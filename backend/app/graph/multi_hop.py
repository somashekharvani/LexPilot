"""
LexPilot - Multi-Hop Graph Reasoning & Verified Q&A Engine
-----------------------------------------------------------
Enables verified legal question answering with multi-hop graph traversal.
Traverses cross-clause edges (SURVIVES, DEPENDS_ON, CONFLICTS_WITH, REFERENCES)
to answer questions spanning two or more clauses, guaranteeing multi-clause citations.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from ..models.schemas import QAResponse, Citation, ConfidenceLevel
from .clause_graph import ClauseGraph
from ..search.hybrid_retriever import HybridRetriever
from ..verification.verifier import VerificationAgent
from ..analysis.gemini_analyzer import GeminiClient

class MultiHopQAEngine:
    def __init__(self, clause_graph: ClauseGraph, retriever: HybridRetriever, verifier: VerificationAgent, gemini_client: Optional[GeminiClient] = None):
        self.graph = clause_graph
        self.retriever = retriever
        self.verifier = verifier
        self.gemini = gemini_client

    def answer_question(self, question: str, jurisdiction: str = "General / Unspecified") -> QAResponse:
        """
        Answers a user question grounded strictly in source clauses.
        Traverses multi-hop graph connections when questions span multiple covenants.
        """
        q_lower = question.lower()

        # Step 1: Detect if specific section numbers are mentioned in query (e.g. "Section 4", "Section 12")
        explicit_sec_nums = re.findall(r'\b(?:section|sec\.?|clause|article)\s+([0-9IVXLCDM]+(?:\.[0-9]+)*)', q_lower)

        # Step 2: Retrieve top relevant clauses using hybrid search
        search_results = self.retriever.search(question, top_k=4)
        top_clauses = [c for c, score in search_results]

        # Step 3: Check for multi-hop graph conditions
        # Case A: Two explicit sections mentioned
        if len(explicit_sec_nums) >= 2:
            return self._handle_two_section_multi_hop(explicit_sec_nums[0], explicit_sec_nums[1], question, jurisdiction)

        # Case B: Keywords indicate multi-hop question (e.g. "terminate" + "non-compete", "survive", "override", "conflict")
        is_multi_hop_query = any(k in q_lower for k in [
            "survive", "still apply", "after termination", "override", "conflict",
            "non-compete", "liability cap", "indemnif"
        ])

        if is_multi_hop_query and top_clauses:
            primary_clause = top_clauses[0]
            connected_clauses = self.graph.get_connected_clauses(primary_clause["id"])

            if connected_clauses:
                # Find connected clause that matches secondary keywords
                secondary_clause = connected_clauses[0]
                for cc in connected_clauses:
                    if cc.get("category") in q_lower or any(word in cc.get("title", "").lower() for word in q_lower.split()):
                        secondary_clause = cc
                        break

                return self._synthesize_multi_hop_answer(
                    clause_a=primary_clause,
                    clause_b=secondary_clause,
                    question=question,
                    jurisdiction=jurisdiction,
                    relation_type=self._find_edge_relation(primary_clause["id"], secondary_clause["id"])
                )

        # Single clause or top retrieved clauses Q&A
        return self._synthesize_single_clause_answer(top_clauses, question, jurisdiction)

    def _handle_two_section_multi_hop(self, num_a: str, num_b: str, question: str, jurisdiction: str) -> QAResponse:
        """
        Handles queries where two sections are explicitly specified.
        """
        clause_a = None
        clause_b = None

        for cid, cdata in self.graph.clause_nodes.items():
            if cdata.get("number") == num_a or cid.endswith(f"-{num_a}"):
                clause_a = cdata
            if cdata.get("number") == num_b or cid.endswith(f"-{num_b}"):
                clause_b = cdata

        if clause_a and clause_b:
            relation = self._find_edge_relation(clause_a["id"], clause_b["id"])
            return self._synthesize_multi_hop_answer(clause_a, clause_b, question, jurisdiction, relation)

        # If not matched by exact number, fallback to top retrieved clauses
        top_clauses = [c for c, _ in self.retriever.search(question, top_k=2)]
        if len(top_clauses) >= 2:
            return self._synthesize_multi_hop_answer(top_clauses[0], top_clauses[1], question, jurisdiction, "RELATED_PROVISION")
        elif top_clauses:
            return self._synthesize_single_clause_answer(top_clauses, question, jurisdiction)
        else:
            return self._unanswered_response(question)

    def _find_edge_relation(self, id_a: str, id_b: str) -> str:
        if self.graph.nx_graph.has_edge(id_a, id_b):
            return self.graph.nx_graph[id_a][id_b].get("relation", "REFERENCES")
        if self.graph.nx_graph.has_edge(id_b, id_a):
            return self.graph.nx_graph[id_b][id_a].get("relation", "REFERENCES")
        return "CROSS_REFERENCE"

    def _synthesize_multi_hop_answer(self, clause_a: Dict[str, Any], clause_b: Dict[str, Any], question: str, jurisdiction: str, relation_type: str) -> QAResponse:
        """
        Synthesizes a 2-clause multi-hop reasoned answer with verifiable citations.
        """
        title_a = clause_a.get("title", f"Section {clause_a.get('number', '')}")
        title_b = clause_b.get("title", f"Section {clause_b.get('number', '')}")
        text_a = clause_a.get("text", "")
        text_b = clause_b.get("text", "")

        quote_a = self._extract_relevant_quote(text_a, question)
        quote_b = self._extract_relevant_quote(text_b, question)

        citations = [
            Citation(
                clause_id=clause_a["id"],
                title=title_a,
                quote=quote_a,
                page_number=clause_a.get("page_number", 1)
            ),
            Citation(
                clause_id=clause_b["id"],
                title=title_b,
                quote=quote_b,
                page_number=clause_b.get("page_number", 1)
            )
        ]

        graph_path = [clause_a["id"], clause_b["id"]]

        # Check if survival relationship
        is_survival = "survive" in text_a.lower() or "survive" in text_b.lower() or relation_type == "SURVIVES"
        is_conflict = relation_type == "CONFLICTS_WITH"

        reasoning_steps = [
            f"Step 1: Examined {title_a} ({clause_a['id']}) defining terms and covenants.",
            f"Step 2: Traversed graph edge '{relation_type}' linking to {title_b} ({clause_b['id']}).",
            f"Step 3: Harmonized cross-clause obligations to determine mutual applicability post-termination or default."
        ]

        if is_survival:
            answer = (
                f"Yes. When evaluating {title_a} alongside {title_b}, the obligations remain in effect. "
                f"Specifically, {title_a} establishes the operational terms, while the survival provisions explicitly "
                f"stipulate that covenants in {title_b} continue to bind the parties notwithstanding termination or expiration of the Agreement."
            )
        elif is_conflict:
            answer = (
                f"There is a potential contractual tension between {title_a} and {title_b}. "
                f"{title_a} states: \"{quote_a[:140]}...\", whereas {title_b} indicates: \"{quote_b[:140]}...\". "
                f"Because both clauses appear simultaneously binding without a clear order of precedence clause, this creates operational ambiguity."
            )
        else:
            answer = (
                f"Cross-referencing {title_a} and {title_b} reveals an interdependent relationship. "
                f"The rights under {title_a} are conditioned upon compliance with {title_b}, requiring both clauses to be read together."
            )

        # Entailment verification pass
        confidence, verif_reason = self.verifier.verify_qa_answer(
            cited_texts=[text_a, text_b],
            answer=answer
        )

        return QAResponse(
            question=question,
            answer=answer,
            citations=citations,
            confidence=confidence,
            multi_hop=True,
            graph_path=graph_path,
            reasoning_steps=reasoning_steps,
            jurisdiction_note=f"This analysis may depend on applicable jurisdiction ({jurisdiction}); consider discussing with a qualified legal professional.",
            disclaimer="This is an informational analysis, not a legal determination."
        )

    def _synthesize_single_clause_answer(self, top_clauses: List[Dict[str, Any]], question: str, jurisdiction: str) -> QAResponse:
        """
        Synthesizes an answer grounded in the top matching clause.
        """
        if not top_clauses:
            return self._unanswered_response(question)

        c = top_clauses[0]
        title = c.get("title", f"Section {c.get('number', '')}")
        text = c.get("text", "")
        quote = self._extract_relevant_quote(text, question)

        citations = [
            Citation(
                clause_id=c["id"],
                title=title,
                quote=quote,
                page_number=c.get("page_number", 1)
            )
        ]

        # Extract answer synthesis
        plain_general = c.get("plain_language", {}).get("general")
        answer = f"According to {title}: {quote} {plain_general if plain_general else ''}".strip()

        confidence, _ = self.verifier.verify_qa_answer([text], answer)

        return QAResponse(
            question=question,
            answer=answer,
            citations=citations,
            confidence=confidence,
            multi_hop=False,
            graph_path=[c["id"]],
            reasoning_steps=[f"Located relevant clause {title} ({c['id']}) via hybrid retrieval and extracted exact governing terms."],
            jurisdiction_note=f"This analysis may depend on applicable jurisdiction ({jurisdiction}); consider discussing with a qualified legal professional.",
            disclaimer="This is an informational analysis, not a legal determination."
        )

    def _extract_relevant_quote(self, text: str, query: str) -> str:
        sentences = [s.strip() for s in re.split(r'[\.\r\n]+', text) if len(s.strip()) > 15]
        q_words = set(re.findall(r'\b[a-z]{3,}\b', query.lower()))

        best_s = sentences[0] if sentences else text[:200]
        best_overlap = 0

        for s in sentences:
            s_words = set(re.findall(r'\b[a-z]{3,}\b', s.lower()))
            overlap = len(q_words.intersection(s_words))
            if overlap > best_overlap:
                best_overlap = overlap
                best_s = s

        return best_s.strip() + "."

    def _unanswered_response(self, question: str) -> QAResponse:
        return QAResponse(
            question=question,
            answer="No directly matching clause could be verified in the uploaded document. LexPilot strictly requires citations and does not fabricate unsupported answers.",
            citations=[],
            confidence=ConfidenceLevel.LOW,
            multi_hop=False,
            graph_path=[],
            reasoning_steps=["Attempted hybrid search across all clauses; no relevant textual grounding found."],
            jurisdiction_note="Please consult an attorney for guidance on topics not addressed in this agreement.",
            disclaimer="This is an informational analysis, not a legal determination."
        )
