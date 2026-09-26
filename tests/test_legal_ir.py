import unittest
from backend.app.parser.document_parser import DocumentParser
from backend.app.clause_engine.segmenter import ClauseSegmenter
from backend.app.clause_engine.classifier import ClauseClassifier
from backend.app.clause_engine.field_extractor import FieldExtractor
from backend.app.clause_engine.legal_ir import LegalIRBuilder
from backend.app.sample_documents.sample_data import (
    SAMPLE_EMPLOYMENT_SCANNED, SAMPLE_LEASE_CONFLICT, SAMPLE_MSA_V1, SAMPLE_MSA_V2
)

class TestLegalIR(unittest.TestCase):
    def setUp(self):
        self.parser = DocumentParser()
        self.segmenter = ClauseSegmenter()
        self.classifier = ClauseClassifier()
        self.field_extractor = FieldExtractor()
        self.legal_ir_builder = LegalIRBuilder()

    def test_legal_ir_conversion_coverage(self):
        samples = [
            ("employment.txt", SAMPLE_EMPLOYMENT_SCANNED),
            ("lease.txt", SAMPLE_LEASE_CONFLICT),
            ("msa_v1.txt", SAMPLE_MSA_V1),
            ("msa_v2.txt", SAMPLE_MSA_V2),
        ]
        
        total_clauses = 0
        converted_clauses = 0

        for name, text in samples:
            parsed = self.parser.parse_file(text.encode("utf-8"), name)
            clauses = self.segmenter.segment(parsed)
            for c in clauses:
                total_clauses += 1
                cat, _ = self.classifier.classify(c.title, c.text)
                fields = self.field_extractor.extract_fields(c.text)
                
                ir = self.legal_ir_builder.build_legal_ir(
                    clause_id=c.clause_id,
                    number=c.number,
                    title=c.title,
                    text=c.text,
                    category=cat,
                    page_number=c.page_number,
                    line_start=c.line_start,
                    line_end=c.line_end,
                    fields=fields,
                    full_doc_text=parsed["raw_text"]
                )

                self.assertIsNotNone(ir)
                self.assertEqual(ir.identity.clause_id, c.clause_id)
                self.assertEqual(ir.semantic.category, cat)
                self.assertIsNotNone(ir.evidence_span)
                self.assertGreaterEqual(ir.evidence_span.char_end, ir.evidence_span.char_start)
                converted_clauses += 1

        coverage = (converted_clauses / total_clauses) * 100
        print(f"\n[LEGAL-IR COVERAGE] Converted {converted_clauses}/{total_clauses} clauses ({coverage:.1f}% coverage)")
        self.assertEqual(coverage, 100.0)

    def test_legal_ir_survival_and_references(self):
        # Test Section 4 of employment agreement specifically
        parsed = self.parser.parse_file(SAMPLE_EMPLOYMENT_SCANNED.encode("utf-8"), "emp.txt")
        clauses = self.segmenter.segment(parsed)
        sec4 = next((c for c in clauses if "4" in c.number or "TERM AND TERMINATION" in c.title), None)
        self.assertIsNotNone(sec4)

        cat, _ = self.classifier.classify(sec4.title, sec4.text)
        fields = self.field_extractor.extract_fields(sec4.text)
        ir = self.legal_ir_builder.build_legal_ir(
            clause_id=sec4.clause_id,
            number=sec4.number,
            title=sec4.title,
            text=sec4.text,
            category=cat,
            page_number=sec4.page_number,
            line_start=sec4.line_start,
            line_end=sec4.line_end,
            fields=fields,
            full_doc_text=parsed["raw_text"]
        )

        self.assertTrue(ir.survival.survives)
        self.assertIn("SEC-12", ir.references)
        self.assertIn("SEC-12", ir.survival.surviving_clauses)

if __name__ == '__main__':
    unittest.main()
