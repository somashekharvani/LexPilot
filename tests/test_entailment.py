"""
Unit Tests: Entailment Verification & Grounding
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.verification.entailment import EntailmentVerifier
from app.models.schemas import ConfidenceLevel

class TestEntailmentVerification(unittest.TestCase):
    def setUp(self):
        self.verifier = EntailmentVerifier(gemini_client=None)

    def test_grounded_claim_high_confidence(self):
        premise = "Either party may terminate this agreement upon thirty (30) days prior written notice."
        claim = "The contract permits termination upon 30 days notice."
        conf, reason = self.verifier.verify(premise, claim)
        self.assertEqual(conf, ConfidenceLevel.HIGH)

    def test_hallucinated_money_low_confidence(self):
        premise = "Contractor will receive standard consulting compensation."
        claim = "Contractor will receive $500,000 in upfront bonus payments."
        conf, reason = self.verifier.verify(premise, claim)
        self.assertEqual(conf, ConfidenceLevel.LOW)
        self.assertIn("not grounded", reason.lower())

    def test_hallucinated_timeframe_low_confidence(self):
        premise = "Notice may be given at any time."
        claim = "Notice requires 90 days advance delivery."
        conf, reason = self.verifier.verify(premise, claim)
        self.assertEqual(conf, ConfidenceLevel.LOW)

if __name__ == "__main__":
    unittest.main()
