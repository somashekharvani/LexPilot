"""
Unit Tests: Document Parsing & Layout Engine
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.parser.document_parser import DocumentParser
from app.clause_engine.segmenter import ClauseSegmenter

class TestDocumentParsing(unittest.TestCase):
    def setUp(self):
        self.parser = DocumentParser()
        self.segmenter = ClauseSegmenter()

    def test_plain_text_parsing(self):
        sample_contract = (
            "1. TERM AND TERMINATION\n"
            "Either party may terminate this agreement upon 30 days notice.\n\n"
            "2. PAYMENT TERMS\n"
            "Client shall pay Provider $5,000 monthly within 15 days of invoice."
        )
        parsed = self.parser.parse_file(sample_contract.encode("utf-8"), "test.txt")
        self.assertIn("blocks", parsed)
        self.assertGreaterEqual(len(parsed["blocks"]), 2)

        clauses = self.segmenter.segment(parsed)
        self.assertGreaterEqual(len(clauses), 2)
        titles = [c.title for c in clauses]
        self.assertTrue(any("TERMINATION" in t for t in titles))
        self.assertTrue(any("PAYMENT" in t for t in titles))

    def test_ocr_noise_normalization(self):
        noisy_text = "This agree-\nment is entered into on Jan  15,  2026."
        cleaned = self.parser._clean_ocr_noise(noisy_text)
        self.assertNotIn("agree-\nment", cleaned)
        self.assertIn("agreement", cleaned)

if __name__ == "__main__":
    unittest.main()
