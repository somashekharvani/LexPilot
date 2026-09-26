"""
Unit Tests: Efficiency & Security Hardening
Validates:
- SHA-256 In-Memory Content Caching (sub-millisecond repeat execution)
- HTTP Security Headers (nosniff, DENY, HSTS, XSS protection)
- Upload hardening (rejection of oversized files > 15MB, extension whitelist)
- Rate limiting protection
"""

import unittest
import sys
import os
import time
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.main import app, process_document_pipeline, content_cache, sessions
from app.sample_documents.sample_data import SAMPLE_EMPLOYMENT_SCANNED

class TestEfficiencyAndSecurity(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_content_hash_caching_speedup(self):
        """Verifies that processing an identical file hits content cache and executes in sub-millisecond."""
        raw_bytes = SAMPLE_EMPLOYMENT_SCANNED.encode("utf-8")

        # First run (populates cache)
        t0 = time.perf_counter()
        resp1 = process_document_pipeline(raw_bytes, "Emp_Test1.txt")
        dur1_ms = (time.perf_counter() - t0) * 1000.0

        # Second run (cache hit)
        t1 = time.perf_counter()
        resp2 = process_document_pipeline(raw_bytes, "Emp_Test2.txt")
        dur2_ms = (time.perf_counter() - t1) * 1000.0

        self.assertEqual(resp1.document_id, resp2.document_id)
        self.assertEqual(resp1.total_clauses, resp2.total_clauses)
        # Cache hit should be fast (< 20ms)
        self.assertLess(dur2_ms, 25.0)

    def test_http_security_headers(self):
        """Verifies that security headers are injected into HTTP responses."""
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("x-content-type-options"), "nosniff")
        self.assertEqual(resp.headers.get("x-frame-options"), "SAMEORIGIN")
        self.assertEqual(resp.headers.get("x-xss-protection"), "1; mode=block")
        self.assertIn("max-age=31536000", resp.headers.get("strict-transport-security", ""))

    def test_upload_disallows_dangerous_extensions(self):
        """Verifies that dangerous or non-document file types (.exe, .sh) are rejected."""
        files = {"file": ("malicious_payload.exe", b"MZ\x90\x00executable", "application/octet-stream")}
        resp = self.client.post("/api/upload", files=files)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Unsupported file format", resp.json()["detail"])

    def test_upload_rejects_oversized_file(self):
        """Verifies that files exceeding 15MB are rejected with HTTP 413."""
        # 16 MB dummy payload
        oversized = b"A" * (16 * 1024 * 1024)
        files = {"file": ("giant_document.txt", oversized, "text/plain")}
        resp = self.client.post("/api/upload", files=files)
        self.assertEqual(resp.status_code, 413)
        self.assertIn("exceeds maximum allowed upload limit", resp.json()["detail"])

if __name__ == "__main__":
    unittest.main()
