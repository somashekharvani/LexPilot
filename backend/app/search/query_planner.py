"""
LexPilot - Advanced Query Planner & Graph-Expanded Retrieval Engine
-------------------------------------------------------------------
Implements an explicit multi-stage reasoning pipeline:
  Question
    → Intent Detection
    → Category Identification & Query Biasing
    → Hybrid Retrieval (BM25 + Semantic overlap)
    → Graph Expansion (1-hop traversal via NetworkX edges)
    → Validated Evidence Set
"""

import re
from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field

class QueryPlan(BaseModel):
    original_query: str
    intent_type: str  # "MULTI_HOP_SURVIVAL", "CROSS_CLAUSE_CONFLICT", "OBLIGATION_LOOKUP", "STANDARD_QA"
    target_categories: List[str] = Field(default_factory=list)
    explicit_sections: List[str] = Field(default_factory=list)
    requires_graph_expansion: bool = True
    suggested_relations: List[str] = Field(default_factory=list)

class QueryPlanner:
    def __init__(self):
        # Category intent keyword maps
        self.category_keywords = {
            "termination": ["terminate", "termination", "cancel", "cancellation", "end", "exit", "fired", "discharge", "severance", "cause"],
            "non_compete": ["non-compete", "noncompete", "compete", "solicit", "solicitation", "restrictive covenant", "worldwide", "customer list"],
            "payment": ["pay", "payment", "salary", "bonus", "fee", "late fee", "compensation", "installments", "rent", "interest"],
            "confidentiality": ["confidential", "confidentiality", "secret", "proprietary", "disclose", "disclosure", "nda"],
            "liability": ["liability", "limitation of liability", "cap", "damage", "consequential", "aggregate"],
            "indemnification": ["indemnify", "indemnification", "hold harmless", "defend", "losses"],
            "governing_law": ["governing law", "jurisdiction", "venue", "delaware", "courts", "dispute resolution"],
            "notice": ["notice", "written notice", "certified mail", "days prior", "notwithstanding"]
        }

    def plan_query(self, question: str) -> QueryPlan:
        q_low = question.lower()

        # 1. Identify explicit section references
        explicit_secs = re.findall(r'\b(?:section|sec\.?|clause|article)\s+([0-9IVXLCDM]+(?:\.[0-9]+)*)', q_low)

        # 2. Detect target categories to bias retrieval
        matched_categories = []
        for cat, kws in self.category_keywords.items():
            if any(kw in q_low for kw in kws):
                matched_categories.append(cat)

        # 3. Detect intent type
        is_survival = any(k in q_low for k in ["survive", "still apply", "post-termination", "after termination", "following termination"])
        is_conflict = any(k in q_low for k in ["conflict", "contradict", "discrepancy", "override", "which notice", "differing"])
        has_two_sections = len(explicit_secs) >= 2

        if is_survival or (has_two_sections and "termination" in matched_categories and "non_compete" in matched_categories):
            intent_type = "MULTI_HOP_SURVIVAL"
            suggested_relations = ["SURVIVES", "REFERENCES"]
            requires_graph_expansion = True
        elif is_conflict or (has_two_sections and "notice" in matched_categories):
            intent_type = "CROSS_CLAUSE_CONFLICT"
            suggested_relations = ["CONFLICTS_WITH", "SUPERSEDES"]
            requires_graph_expansion = True
        elif len(matched_categories) >= 2 or has_two_sections:
            intent_type = "MULTI_HOP_RELATIONSHIP"
            suggested_relations = ["DEPENDS_ON", "REFERENCES"]
            requires_graph_expansion = True
        else:
            intent_type = "STANDARD_QA"
            suggested_relations = ["REFERENCES"]
            requires_graph_expansion = False

        return QueryPlan(
            original_query=question,
            intent_type=intent_type,
            target_categories=matched_categories,
            explicit_sections=explicit_secs,
            requires_graph_expansion=requires_graph_expansion,
            suggested_relations=suggested_relations
        )

    def execute_planned_retrieval(
        self,
        question: str,
        retriever: Any,
        clause_graph: Any,
        top_k: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Executes retrieval guided by the QueryPlan:
          1. Hybrid search with category score biasing
          2. 1-Hop Graph expansion from top hits
          3. Returns ordered, enriched evidence clause set
        """
        plan = self.plan_query(question)

        # 1. Base Hybrid Retrieval
        base_results = retriever.search(question, top_k=top_k * 2)

        # 2. Category Biasing & Re-ranking
        scored_clauses = []
        for clause, score in base_results:
            boosted_score = score
            # Boost if category matches intent
            if clause.get("category") in plan.target_categories:
                boosted_score *= 1.35
            # Boost if explicit section mentioned
            num = str(clause.get("number", "")).strip()
            cid = str(clause.get("id", ""))
            if any(sec == num or cid.endswith(f"-{sec}") for sec in plan.explicit_sections):
                boosted_score *= 1.80

            scored_clauses.append((clause, boosted_score))

        scored_clauses.sort(key=lambda x: x[1], reverse=True)
        seed_clauses = [c for c, _ in scored_clauses[:top_k]]

        if not plan.requires_graph_expansion or not seed_clauses:
            return seed_clauses

        # 3. Graph Expansion (1-hop traversal)
        evidence_dict: Dict[str, Dict[str, Any]] = {c["id"]: c for c in seed_clauses}

        for seed in seed_clauses:
            seed_id = seed["id"]
            # Look up neighbors in in-memory clause graph
            if hasattr(clause_graph, "nx_graph") and clause_graph.nx_graph.has_node(seed_id):
                # Outgoing neighbors (clauses this seed points to or survives into)
                for neighbor_id in clause_graph.nx_graph.successors(seed_id):
                    edge_data = clause_graph.nx_graph.get_edge_data(seed_id, neighbor_id, {})
                    edge_rel = edge_data.get("relation", "")
                    if not plan.suggested_relations or edge_rel in plan.suggested_relations or edge_rel == "SURVIVES":
                        if neighbor_id in clause_graph.clause_nodes and neighbor_id not in evidence_dict:
                            evidence_dict[neighbor_id] = clause_graph.clause_nodes[neighbor_id]

                # Incoming neighbors (clauses that reference or survive into this seed)
                for predecessor_id in clause_graph.nx_graph.predecessors(seed_id):
                    edge_data = clause_graph.nx_graph.get_edge_data(predecessor_id, seed_id, {})
                    edge_rel = edge_data.get("relation", "")
                    if not plan.suggested_relations or edge_rel in plan.suggested_relations or edge_rel == "SURVIVES":
                        if predecessor_id in clause_graph.clause_nodes and predecessor_id not in evidence_dict:
                            evidence_dict[predecessor_id] = clause_graph.clause_nodes[predecessor_id]

        return list(evidence_dict.values())
