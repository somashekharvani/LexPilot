"""
Unit Tests: Clause Classification into 10 Legal Categories
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.clause_engine.classifier import ClauseClassifier
from app.clause_engine.field_extractor import FieldExtractor

class TestClauseClassification(unittest.TestCase):
    def setUp(self):
        self.classifier = ClauseClassifier()
        self.field_extractor = FieldExtractor()

    def test_classification_categories(self):
        test_cases = [
            ("Termination of Agreement", "Either party may terminate for material breach with 30 days cure.", "termination"),
            ("Compensation and Invoicing", "Client shall pay invoices Net 30 with 1.5% late interest.", "payment"),
            ("Limitation of Liability", "In no event shall aggregate liability exceed fees paid in prior 12 months.", "liability"),
            ("Non-Disclosure Obligations", "Recipient shall hold Confidential Information in strict confidence.", "confidentiality"),
            ("Defense and Indemnification", "Vendor shall defend and indemnify Customer against third-party patent claims.", "indemnification"),
            ("Restrictive Covenants", "Employee agrees not to compete with the business for 12 months post-employment.", "non_compete"),
            ("Governing Law and Jurisdiction", "This agreement is governed by the laws of the State of Delaware.", "governing_law"),
            ("Written Notices", "All formal notices must be delivered via certified mail or courier.", "notice")
        ]

        for title, text, expected_cat in test_cases:
            cat, conf = self.classifier.classify(title, text)
            self.assertEqual(cat, expected_cat, f"Failed for title '{title}': got '{cat}', expected '{expected_cat}'")
            self.assertGreaterEqual(conf, 0.70)

    def test_field_extraction(self):
        text = "Company shall pay Contractor $120,000 on December 31, 2026. Contractor shall maintain confidentiality."
        fields = self.field_extractor.extract_fields(text)
        self.assertIn("Contractor", fields["parties_involved"])
        self.assertTrue(any("$120,000" in m for m in fields["monetary_amounts"]))
        self.assertGreaterEqual(len(fields["obligations"]), 1)

if __name__ == "__main__":
    unittest.main()
