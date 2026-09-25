"""
Unit Tests: Cross-Clause Conflict Detection
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.analysis.conflict_detector import ConflictDetector
from app.graph.clause_graph import ClauseGraph

class TestConflictDetection(unittest.TestCase):
    def setUp(self):
        self.graph = ClauseGraph()
        self.detector = ConflictDetector(self.graph)

    def test_contradictory_notice_detection(self):
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
        self.assertEqual(conflicts[0].clause_a_id, "SEC-4")
        self.assertEqual(conflicts[0].clause_b_id, "SEC-14")

if __name__ == "__main__":
    unittest.main()
