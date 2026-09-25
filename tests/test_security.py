"""
Unit Tests: Security, Input Validation & Sanitization
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.parser.document_parser import DocumentParser

class TestSecurityAndSanitization(unittest.TestCase):
    def setUp(self):
        self.parser = DocumentParser()

    def test_safe_text_parsing_against_injection(self):
        malicious_input = "<script>alert('xss')</script>\n\n{{7*7}}\n\n__import__('os').system('dir')"
        parsed = self.parser.parse_file(malicious_input.encode("utf-8"), "safe.txt")
        self.assertIn("blocks", parsed)
        self.assertIsInstance(parsed["raw_text"], str)

    def test_filename_handling(self):
        traversal_filename = "../../../../etc/passwd"
        parsed = self.parser.parse_file(b"1. Section One\nStandard terms.", traversal_filename)
        self.assertEqual(parsed["filename"], traversal_filename)

if __name__ == "__main__":
    unittest.main()
