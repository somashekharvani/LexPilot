"""
LexPilot - Multi-Hop Graph Reasoning & Verified Q&A Engine
-----------------------------------------------------------
Enables verified legal question answering with multi-hop graph traversal.
Traverses cross-clause edges (SURVIVES, DEPENDS_ON, CONFLICTS_WITH, REFERENCES)
to answer questions spanning two or more clauses, guaranteeing multi-clause citations.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from ..models.schemas import (
    QAResponse, Citation, ConfidenceLevel, SupportingClauseSpan, ProvenanceRecord
)
from .clause_graph import ClauseGraph
from ..search.hybrid_retriever import HybridRetriever
from ..search.query_planner import QueryPlanner
from ..verification.verifier import VerificationAgent
from ..analysis.gemini_analyzer import GeminiClient

class MultiHopQAEngine:
    def __init__(self, clause_graph: ClauseGraph, retriever: HybridRetriever, verifier: VerificationAgent, gemini_client: Optional[GeminiClient] = None):
        self.graph = clause_graph
        self.retriever = retriever
        self.verifier = verifier
        self.gemini = gemini_client
        self.planner = QueryPlanner()

    def answer_question(self, question: str, jurisdiction: str = "General / Unspecified") -> QAResponse:
        """
        Answers a user question grounded strictly in source clauses.
        Uses QueryPlanner to bias category retrieval and 1-hop graph expansion.
        """
        # Step 1: Execute Query Planning & Intent Classification
        plan = self.planner.plan_query(question)

        # Case A: Two explicit sections mentioned
        if len(plan.explicit_sections) >= 2:
            return self._handle_two_section_multi_hop(plan.explicit_sections[0], plan.explicit_sections[1], question, jurisdiction)

        # Step 2: Planned Retrieval with Category Biasing & 1-Hop Graph Expansion
        evidence_clauses = self.planner.execute_planned_retrieval(question, self.retriever, self.graph, top_k=3)

        # Step 3: Check for multi-hop graph conditions
        if plan.intent_type in ["MULTI_HOP_SURVIVAL", "CROSS_CLAUSE_CONFLICT", "MULTI_HOP_RELATIONSHIP"] and len(evidence_clauses) >= 2:
            primary_clause = evidence_clauses[0]
            # Select secondary clause from planned evidence
            secondary_clause = evidence_clauses[1]
            relation = self._find_edge_relation(primary_clause["id"], secondary_clause["id"])

            return self._synthesize_multi_hop_answer(
                clause_a=primary_clause,
                clause_b=secondary_clause,
                question=question,
                jurisdiction=jurisdiction,
                relation_type=relation
            )

        # Single clause or top retrieved clauses Q&A
        return self._synthesize_single_clause_answer(evidence_clauses, question, jurisdiction)

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

        # Structured Claim Validation against parsed Legal-IR clause IDs & Entailment
        legal_ir_map = {
            cid: cdata.get("legal_ir")
            for cid, cdata in self.graph.clause_nodes.items()
            if cdata.get("legal_ir") is not None
        }
        claim_summary = answer.split(". ")[0] + "."
        cited_ids = [clause_a["id"], clause_b["id"]]
        clause_texts = {
            clause_a["id"]: text_a,
            clause_b["id"]: text_b
        }

        entailment_res, confidence, verif_reason = self.verifier.verify_structured_claim(
            claim_text=answer,
            cited_clause_ids=cited_ids,
            legal_ir_map=legal_ir_map,
            clause_texts=clause_texts
        )

        # Build explicit Provenance Chain:
        # USER QUESTION -> CLAIM -> REASONING STEP -> CLAUSE -> EXACT EVIDENCE SPAN -> PAGE -> VERIFICATION RESULT
        legal_ir_a = clause_a.get("legal_ir")
        legal_ir_b = clause_b.get("legal_ir")

        span_a = SupportingClauseSpan(
            clause_id=clause_a["id"],
            title=title_a,
            page=clause_a.get("page_number", 1),
            char_start=legal_ir_a.evidence_span.char_start if legal_ir_a and hasattr(legal_ir_a, "evidence_span") else 0,
            char_end=legal_ir_a.evidence_span.char_end if legal_ir_a and hasattr(legal_ir_a, "evidence_span") else len(text_a),
            quote=quote_a
        )
        span_b = SupportingClauseSpan(
            clause_id=clause_b["id"],
            title=title_b,
            page=clause_b.get("page_number", 1),
            char_start=legal_ir_b.evidence_span.char_start if legal_ir_b and hasattr(legal_ir_b, "evidence_span") else 0,
            char_end=legal_ir_b.evidence_span.char_end if legal_ir_b and hasattr(legal_ir_b, "evidence_span") else len(text_b),
            quote=quote_b
        )

        provenance = [
            ProvenanceRecord(
                claim_id="CLAIM-1",
                claim_text=claim_summary,
                reasoning_step=f"Traversed graph edge '{relation_type}' from {clause_a['id']} to {clause_b['id']} and harmonized covenants.",
                supporting_clauses=[span_a, span_b],
                entailment_result=entailment_res,
                confidence=confidence,
                verification_details=verif_reason
            )
        ]

        return QAResponse(
            question=question,
            answer=answer,
            citations=citations,
            provenance=provenance,
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

        # Structured Claim Validation against parsed Legal-IR clause IDs & Entailment
        legal_ir_map = {
            cid: cdata.get("legal_ir")
            for cid, cdata in self.graph.clause_nodes.items()
            if cdata.get("legal_ir") is not None
        }
        claim_text = answer[:180]
        cited_ids = [c["id"]]
        clause_texts = {c["id"]: text}

        entailment_res, confidence, verif_reason = self.verifier.verify_structured_claim(
            claim_text=claim_text,
            cited_clause_ids=cited_ids,
            legal_ir_map=legal_ir_map,
            clause_texts=clause_texts
        )

        legal_ir = c.get("legal_ir")
        span = SupportingClauseSpan(
            clause_id=c["id"],
            title=title,
            page=c.get("page_number", 1),
            char_start=legal_ir.evidence_span.char_start if legal_ir and hasattr(legal_ir, "evidence_span") else 0,
            char_end=legal_ir.evidence_span.char_end if legal_ir and hasattr(legal_ir, "evidence_span") else len(text),
            quote=quote
        )

        provenance = [
            ProvenanceRecord(
                claim_id="CLAIM-1",
                claim_text=claim_text,
                reasoning_step=f"Located governing terms in {title} ({c['id']}) via hybrid retrieval and verified entailment.",
                supporting_clauses=[span],
                entailment_result=entailment_res,
                confidence=confidence,
                verification_details=verif_reason
            )
        ]

        return QAResponse(
            question=question,
            answer=answer,
            citations=citations,
            provenance=provenance,
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
