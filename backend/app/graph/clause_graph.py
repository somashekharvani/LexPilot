"""
LexPilot - Clause Graph Engine
------------------------------
Constructs an in-memory clause graph (using NetworkX and dict adjacency):
  - Nodes: Legal clauses with classification, structured entities, attention levels
  - Edges:
      * REFERENCES (explicit cross-references: "as defined in Section 2")
      * SURVIVES ("Sections 6 and 10 shall survive termination")
      * DEPENDS_ON ("subject to the provisions of Section 4")
      * SUPERSEDES ("Notwithstanding anything to the contrary in Section 5")
      * CONFLICTS_WITH (contradictory operational terms)
  - Multi-hop traversal: Shortest paths, survival chains, cross-clause reasoning paths
"""

import re
import networkx as nx
from typing import List, Dict, Any, Tuple, Optional
from ..models.schemas import GraphEdge, ConfidenceLevel

class ClauseGraph:
    def __init__(self):
        self.nx_graph = nx.DiGraph()
        self.clause_nodes: Dict[str, Dict[str, Any]] = {}
        self.edge_records: List[GraphEdge] = []

    def build_graph(self, clauses: List[Dict[str, Any]]) -> None:
        """
        Builds the in-memory graph from a list of segmented, classified clauses.
        """
        self.nx_graph.clear()
        self.clause_nodes.clear()
        self.edge_records.clear()

        # Add all nodes
        for c in clauses:
            cid = c["id"]
            self.clause_nodes[cid] = c
            self.nx_graph.add_node(
                cid,
                number=c.get("number", ""),
                title=c.get("title", ""),
                category=c.get("category", "other"),
                text=c.get("text", "")
            )

        # Detect edges between nodes
        self._detect_cross_references(clauses)
        self._detect_survival_edges(clauses)
        self._detect_dependency_edges(clauses)
        self._detect_superseding_edges(clauses)

    def add_conflict_edge(self, source_id: str, target_id: str, explanation: str, confidence: ConfidenceLevel = ConfidenceLevel.HIGH):
        """
        Adds a CONFLICTS_WITH bidirectional edge.
        """
        edge = GraphEdge(
            source=source_id,
            target=target_id,
            relation="CONFLICTS_WITH",
            description=explanation,
            confidence=confidence
        )
        self.edge_records.append(edge)
        self.nx_graph.add_edge(source_id, target_id, relation="CONFLICTS_WITH", description=explanation)
        self.nx_graph.add_edge(target_id, source_id, relation="CONFLICTS_WITH", description=explanation)

    def _detect_cross_references(self, clauses: List[Dict[str, Any]]):
        """
        Finds explicit mentions of "Section X", "Clause Y", "Article Z" in clause text.
        """
        # Map numbers / IDs to clause IDs
        num_to_id = {}
        for c in clauses:
            num = c.get("number", "").strip()
            if num:
                num_to_id[num] = c["id"]
                # Also handle dotted numbers like "4.1" -> "4" if main
                main_part = num.split('.')[0]
                if main_part not in num_to_id:
                    num_to_id[main_part] = c["id"]

        ref_pattern = re.compile(r'\b(?:Section|Article|Clause)\s+([0-9IVXLCDM]+(?:\.[0-9]+)*)', re.IGNORECASE)

        for c in clauses:
            src_id = c["id"]
            text = c.get("text", "")
            matches = ref_pattern.findall(text)

            for ref_num in matches:
                target_id = num_to_id.get(ref_num)
                if not target_id:
                    # Try finding by section number in IDs
                    for cid in self.clause_nodes.keys():
                        if cid.endswith(f"-{ref_num}"):
                            target_id = cid
                            break

                if target_id and target_id != src_id:
                    desc = f"{c.get('title', 'Clause')} references Section {ref_num}"
                    edge = GraphEdge(
                        source=src_id,
                        target=target_id,
                        relation="REFERENCES",
                        description=desc,
                        confidence=ConfidenceLevel.HIGH
                    )
                    self.edge_records.append(edge)
                    self.nx_graph.add_edge(src_id, target_id, relation="REFERENCES", description=desc)

    def _detect_survival_edges(self, clauses: List[Dict[str, Any]]):
        """
        Detects survival clauses: "Sections X, Y, and Z shall survive termination of this Agreement".
        Connects Termination clause -> Survived clauses with relation 'SURVIVES'.
        """
        survival_pattern = re.compile(
            r'(?:Sections?|Articles?|Clauses?)\s+([0-9,\s&andor\.]+)\s+shall\s+survive',
            re.IGNORECASE
        )

        for c in clauses:
            text = c.get("text", "")
            m = survival_pattern.search(text)
            if m:
                raw_nums = m.group(1)
                nums = re.findall(r'[0-9]+(?:\.[0-9]+)*', raw_nums)
                for num in nums:
                    # Find matching target clause
                    for target_id, target_data in self.clause_nodes.items():
                        if target_data.get("number") == num or target_id.endswith(f"-{num}"):
                            desc = f"Section {num} explicitly survives contract termination pursuant to {c.get('number', c['id'])}"
                            edge = GraphEdge(
                                source=c["id"],
                                target=target_id,
                                relation="SURVIVES",
                                description=desc,
                                confidence=ConfidenceLevel.HIGH
                            )
                            self.edge_records.append(edge)
                            self.nx_graph.add_edge(c["id"], target_id, relation="SURVIVES", description=desc)

    def _detect_dependency_edges(self, clauses: List[Dict[str, Any]]):
        """
        Detects conditional clauses: "Subject to Section X", "conditioned upon compliance with Section Y".
        """
        dep_pattern = re.compile(
            r'(?:subject to|conditioned upon|pursuant to|in accordance with)\s+(?:Section|Article|Clause)\s+([0-9IVXLCDM]+(?:\.[0-9]+)*)',
            re.IGNORECASE
        )

        for c in clauses:
            text = c.get("text", "")
            matches = dep_pattern.findall(text)
            for num in matches:
                for target_id, target_data in self.clause_nodes.items():
                    if target_data.get("number") == num or target_id.endswith(f"-{num}"):
                        desc = f"Obligations in {c.get('number', c['id'])} are conditioned upon {target_data.get('number', target_id)}"
                        edge = GraphEdge(
                            source=c["id"],
                            target=target_id,
                            relation="DEPENDS_ON",
                            description=desc,
                            confidence=ConfidenceLevel.HIGH
                        )
                        self.edge_records.append(edge)
                        self.nx_graph.add_edge(c["id"], target_id, relation="DEPENDS_ON", description=desc)

    def _detect_superseding_edges(self, clauses: List[Dict[str, Any]]):
        """
        Detects override clauses: "Notwithstanding anything to the contrary in Section X".
        """
        super_pattern = re.compile(
            r'notwithstanding (?:anything to the contrary in )?(?:Section|Article|Clause)\s+([0-9IVXLCDM]+(?:\.[0-9]+)*)',
            re.IGNORECASE
        )

        for c in clauses:
            text = c.get("text", "")
            matches = super_pattern.findall(text)
            for num in matches:
                for target_id, target_data in self.clause_nodes.items():
                    if target_data.get("number") == num or target_id.endswith(f"-{num}"):
                        desc = f"{c.get('number', c['id'])} supersedes/overrides Section {num}"
                        edge = GraphEdge(
                            source=c["id"],
                            target=target_id,
                            relation="SUPERSEDES",
                            description=desc,
                            confidence=ConfidenceLevel.HIGH
                        )
                        self.edge_records.append(edge)
                        self.nx_graph.add_edge(c["id"], target_id, relation="SUPERSEDES", description=desc)

    def find_multi_hop_path(self, start_id: str, end_id: str) -> Optional[List[str]]:
        """
        Finds shortest directed or undirected path in the clause graph between two clauses.
        """
        if start_id not in self.nx_graph or end_id not in self.nx_graph:
            return None

        # Check directed path first
        try:
            return nx.shortest_path(self.nx_graph, source=start_id, target=end_id)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            pass

        # Try reverse directed path
        try:
            return nx.shortest_path(self.nx_graph, source=end_id, target=start_id)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            pass

        # Try undirected graph
        undirected = self.nx_graph.to_undirected()
        try:
            return nx.shortest_path(undirected, source=start_id, target=end_id)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def get_connected_clauses(self, clause_id: str) -> List[Dict[str, Any]]:
        """
        Returns all clauses connected directly to this clause node in the graph.
        """
        if clause_id not in self.nx_graph:
            return []

        neighbors = set(self.nx_graph.neighbors(clause_id))
        undirected = self.nx_graph.to_undirected()
        all_connected = set(undirected.neighbors(clause_id))

        results = []
        for nid in all_connected:
            if nid in self.clause_nodes:
                results.append(self.clause_nodes[nid])
        return results

    def get_all_edges(self) -> List[GraphEdge]:
        return self.edge_records
