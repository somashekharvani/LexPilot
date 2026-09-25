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
