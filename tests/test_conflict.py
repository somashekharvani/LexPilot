"""
Unit Tests: Cross-Clause Conflict Detection with Typed Conflict Engine
Validates: TEMPORAL, AMOUNT, OBLIGATION, SCOPE, DEFINITION, SURVIVAL, CONDITIONAL
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.analysis.conflict_detector import ConflictDetector
from app.graph.clause_graph import ClauseGraph
from app.models.schemas import ConflictType

class TestConflictDetection(unittest.TestCase):
    def setUp(self):
        self.graph = ClauseGraph()
        self.detector = ConflictDetector(self.graph)

    def test_contradictory_notice_detection_temporal(self):
        clauses = [
            {
                "id": "SEC-4",
                "number": "4",
                "title": "Early Termination for Convenience",
                "category": "termination",
                "text": "Tenant may terminate upon thirty (30) days' prior written notice."
            },
            {
                "id": "SEC-14",
                "number": "14",
                "title": "Notice for Termination of Tenancy",
                "category": "notice",
                "text": "Any notice of termination requires sixty (60) days' prior written notice."
            }
        ]
        conflicts = self.detector.detect_conflicts(clauses)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].conflict_type, "Contradictory Notice Periods")
        self.assertEqual(conflicts[0].typed_category, ConflictType.TEMPORAL)
        self.assertEqual(conflicts[0].clause_a_id, "SEC-4")
        self.assertEqual(conflicts[0].clause_b_id, "SEC-14")

    def test_liability_vs_indemnity_obligation(self):
        clauses = [
            {
                "id": "SEC-9",
                "number": "9",
                "title": "Limitation of Liability",
                "category": "liability",
                "text": "Total aggregate liability of either party shall not exceed the total amount paid of $50,000."
            },
            {
                "id": "SEC-10",
                "number": "10",
                "title": "Indemnification",
                "category": "indemnification",
                "text": "Vendor agrees to defend, indemnify, and hold harmless Customer from any third-party claims."
            }
        ]
        conflicts = self.detector.detect_conflicts(clauses)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].typed_category, ConflictType.OBLIGATION)

    def test_monetary_amount_conflict(self):
        clauses = [
            {
                "id": "SEC-3",
                "number": "3",
                "title": "Security Deposit",
                "category": "payment",
                "text": "Tenant shall provide a security deposit of $5,000 upon signing."
            },
            {
                "id": "SEC-15",
                "number": "15",
                "title": "Move-In Requirements",
                "category": "payment",
                "text": "Prior to occupancy, Tenant must submit a security deposit of $7,500 to Landlord."
            }
        ]
        conflicts = self.detector.detect_conflicts(clauses)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].typed_category, ConflictType.AMOUNT)
        self.assertIn("5,000", conflicts[0].explanation)
        self.assertIn("7,500", conflicts[0].explanation)

    def test_survival_mandate_conflict(self):
        clauses = [
            {
                "id": "SEC-8",
                "number": "8",
                "title": "Effect of Termination",
                "category": "termination",
                "text": "Upon any termination of this Agreement, all rights and obligations of the parties shall immediately cease."
            },
            {
                "id": "SEC-12",
                "number": "12",
                "title": "Non-Competition",
                "category": "non_compete",
                "text": "Employee agrees that restrictive covenants shall survive the termination of this agreement in perpetuity."
            }
        ]
        conflicts = self.detector.detect_conflicts(clauses)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].typed_category, ConflictType.SURVIVAL)

    def test_scope_conflict(self):
        clauses = [
            {
                "id": "SEC-2",
                "number": "2",
                "title": "License Grant",
                "category": "intellectual_property",
                "text": "Licensor hereby grants Licensee a sole and exclusive license to commercialize the Product."
            },
            {
                "id": "SEC-5",
                "number": "5",
                "title": "Distribution Rights",
                "category": "intellectual_property",
                "text": "Licensor grants a non-exclusive license to market and sell the Product globally."
            }
        ]
        conflicts = self.detector.detect_conflicts(clauses)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].typed_category, ConflictType.SCOPE)

    def test_conditional_supremacy_conflict(self):
        clauses = [
            {
                "id": "SEC-6",
                "number": "6",
                "title": "Fee Adjustments",
                "category": "payment",
                "text": "Notwithstanding anything to the contrary in this Agreement, Vendor may increase fees by 15% annually."
            },
            {
                "id": "SEC-11",
                "number": "11",
                "title": "Price Lock Warranty",
                "category": "warranty",
                "text": "Notwithstanding any provision to the contrary, pricing shall remain fixed for the entire 5-year term."
            }
        ]
        conflicts = self.detector.detect_conflicts(clauses)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].typed_category, ConflictType.CONDITIONAL)

    def test_inconsistent_definitions_conflict(self):
        clauses = [
            {
                "id": "SEC-1",
                "number": "1",
                "title": "Definitions",
                "category": "definitions",
                "text": '“Confidential Information” means any technical data disclosed in writing.'
            },
            {
                "id": "SEC-7",
                "number": "7",
                "title": "Proprietary Data",
                "category": "confidentiality",
                "text": '“Confidential Information” shall mean all business plans, customer lists, software code, financial projections, oral disclosures, and general marketing insights.'
            }
        ]
        conflicts = self.detector.detect_conflicts(clauses)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].typed_category, ConflictType.DEFINITION)

if __name__ == "__main__":
    unittest.main()
