"""
Unit Tests: Structured Claim Validation against parsed Legal-IR Clause IDs
Validates:
- Validation of cited clause IDs against Legal-IR clause registry
- Immediate rejection of hallucinated/fabricated clause IDs
- Rejection of claims lacking clause citations
- Two-stage verification: structural validation followed by entailment checking
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.verification.verifier import VerificationAgent
from app.models.schemas import ConfidenceLevel
from app.models.legal_ir import LegalIRClause, ClauseIdentity, ClauseSemantic, EvidenceSpan

class TestStructuredClaimValidation(unittest.TestCase):
    def setUp(self):
        self.verifier = VerificationAgent()
        
        # Build mock Legal-IR clause map
        ir_sec4 = LegalIRClause(
            identity=ClauseIdentity(clause_id="SEC-4", section="4", page=1),
            semantic=ClauseSemantic(category="termination"),
            evidence_span=EvidenceSpan(page=1, char_start=0, char_end=100)
        )
        ir_sec12 = LegalIRClause(
            identity=ClauseIdentity(clause_id="SEC-12", section="12", page=1),
            semantic=ClauseSemantic(category="non_compete"),
            evidence_span=EvidenceSpan(page=1, char_start=0, char_end=150)
        )
        
        self.legal_ir_map = {
            "SEC-4": ir_sec4,
            "SEC-12": ir_sec12
        }
        
        self.clause_texts = {
            "SEC-4": "Either party may terminate upon thirty (30) days prior written notice.",
            "SEC-12": "Employee agrees not to compete for a period of thirty-six (36) months post-termination."
        }

    def test_valid_legal_ir_clause_ids_pass_structural_check(self):
        """Verifies that legitimate Legal-IR IDs pass structural validation."""
        claim = "Either party may terminate upon 30 days notice."
        is_valid, reason = self.verifier.validate_claim_structure(
            claim_text=claim,
            cited_clause_ids=["SEC-4"],
            legal_ir_map=self.legal_ir_map
        )
        self.assertTrue(is_valid)
        self.assertIn("Valid Legal-IR clause citations confirmed", reason)

    def test_fabricated_clause_id_rejected(self):
        """Verifies that hallucinated/fabricated clause IDs are immediately rejected."""
        claim = "The landlord must pay $1,000,000 according to Section 99."
        is_valid, reason = self.verifier.validate_claim_structure(
            claim_text=claim,
            cited_clause_ids=["SEC-99"],
            legal_ir_map=self.legal_ir_map
        )
        self.assertFalse(is_valid)
        self.assertIn("Structural rejection", reason)
        self.assertIn("SEC-99", reason)

        # Check full two-stage verification
        result, confidence, details = self.verifier.verify_structured_claim(
            claim_text=claim,
            cited_clause_ids=["SEC-99"],
            legal_ir_map=self.legal_ir_map,
            clause_texts=self.clause_texts
        )
        self.assertEqual(result, "FAIL")
        self.assertEqual(confidence, ConfidenceLevel.LOW)
        self.assertIn("SEC-99", details)

    def test_empty_citations_rejected(self):
        """Verifies claims without citations fail structural validation."""
        claim = "General legal principle without source clause."
        is_valid, reason = self.verifier.validate_claim_structure(
            claim_text=claim,
            cited_clause_ids=[],
            legal_ir_map=self.legal_ir_map
        )
        self.assertFalse(is_valid)
        self.assertIn("does not cite any evidence clause IDs", reason)

    def test_multi_clause_structural_and_entailment_pass(self):
        """Verifies that multi-clause claims citing valid IDs pass both stages."""
        claim = "Notice of 30 days is required under Section 4 and non-compete extends 36 months under Section 12."
        result, confidence, details = self.verifier.verify_structured_claim(
            claim_text=claim,
            cited_clause_ids=["SEC-4", "SEC-12"],
            legal_ir_map=self.legal_ir_map,
            clause_texts=self.clause_texts
        )
        self.assertEqual(result, "PASS")
        self.assertEqual(confidence, ConfidenceLevel.HIGH)
        self.assertIn("Valid Legal-IR clause citations confirmed", details)

if __name__ == "__main__":
    unittest.main()
