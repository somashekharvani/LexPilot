"""
LexPilot - Verification Agent Manager
-------------------------------------
Coordinates entailment verification across the entire analysis pipeline.
Ensures no unverified statement or ungrounded claim reaches the frontend.
"""

from typing import List, Dict, Any, Tuple
from ..models.schemas import ConfidenceLevel, ClauseNode, ContractConflict, TimelineEvent, Citation, QAResponse
from .entailment import EntailmentVerifier

class VerificationAgent:
    def __init__(self, gemini_client=None):
        self.verifier = EntailmentVerifier(gemini_client=gemini_client)

    def verify_clause_analysis(self, clause_text: str, attention_reasons: List[str], plain_text: str) -> Tuple[ConfidenceLevel, str]:
        """
        Verifies attention reasons and plain language synthesis against clause text.
        """
        # Test the most prominent attention reason or plain text
        target_claim = " ".join(attention_reasons) if attention_reasons else plain_text
        if not target_claim:
            return ConfidenceLevel.HIGH, "Standard clause with baseline wording."

        return self.verifier.verify(premise=clause_text, hypothesis=target_claim)

    def verify_conflict(self, clause_a_text: str, clause_b_text: str, explanation: str) -> Tuple[ConfidenceLevel, str]:
        """
        Verifies that a detected conflict is grounded in both cited clauses.
        """
        combined_premise = f"Clause A:\n{clause_a_text}\n\nClause B:\n{clause_b_text}"
        return self.verifier.verify(premise=combined_premise, hypothesis=explanation)

    def verify_qa_answer(self, cited_texts: List[str], answer: str) -> Tuple[ConfidenceLevel, str]:
        """
        Verifies that a Q&A answer is entailed by its cited source clauses.
        """
        combined_premise = "\n\n".join(cited_texts)
        return self.verifier.verify(premise=combined_premise, hypothesis=answer)

    def verify_comparison_delta(self, text_a: str, text_b: str, semantic_delta: str) -> Tuple[ConfidenceLevel, str]:
        """
        Verifies that a comparison delta accurately describes the difference between version A and B.
        """
        premise = f"Original Version:\n{text_a}\n\nRevised Version:\n{text_b}"
        return self.verifier.verify(premise=premise, hypothesis=semantic_delta)

    def validate_claim_structure(
        self,
        claim_text: str,
        cited_clause_ids: List[str],
        legal_ir_map: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Validates that all evidence_ids cited by a claim exist in the parsed Legal-IR registry.
        Rejects fabricated/hallucinated clause IDs before entailment check.
        """
        if not cited_clause_ids:
            return False, "Structural rejection: Claim does not cite any evidence clause IDs."

        invalid_ids = [cid for cid in cited_clause_ids if cid not in legal_ir_map]
        if invalid_ids:
            return False, f"Structural rejection: Cited clause IDs {invalid_ids} do not exist in parsed Legal-IR."

        return True, "Valid Legal-IR clause citations confirmed."

    def verify_structured_claim(
        self,
        claim_text: str,
        cited_clause_ids: List[str],
        legal_ir_map: Dict[str, Any],
        clause_texts: Dict[str, str]
    ) -> Tuple[str, ConfidenceLevel, str]:
        """
        Two-stage claim verification:
          Stage 1: Structured Claim Validation against parsed Legal-IR clause IDs
          Stage 2: Premise entailment verification against source text
        Returns (entailment_result: PASS/FAIL/PARTIAL, confidence: High/Medium/Low, details: str)
        """
        is_valid, struct_reason = self.validate_claim_structure(claim_text, cited_clause_ids, legal_ir_map)
        if not is_valid:
            return "FAIL", ConfidenceLevel.LOW, struct_reason

        premises = [clause_texts.get(cid, "") for cid in cited_clause_ids]
        combined_premise = "\n\n".join(filter(None, premises))
        conf, verif_detail = self.verifier.verify(premise=combined_premise, hypothesis=claim_text)

        entailment_res = "PASS" if conf == ConfidenceLevel.HIGH else ("PARTIAL" if conf == ConfidenceLevel.MEDIUM else "FAIL")
        return entailment_res, conf, f"{struct_reason} {verif_detail}"
