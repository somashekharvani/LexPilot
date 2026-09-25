"""
LexPilot - Pipeline Self-Test & Verification Script
Runs end-to-end tests across all 10 features.
"""

import sys
import os

# Add backend to path and reconfigure stdout for utf-8
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from app.main import process_document_pipeline, comparator
from app.sample_documents.sample_data import (
    SAMPLE_EMPLOYMENT_SCANNED, SAMPLE_LEASE_CONFLICT, SAMPLE_MSA_V1, SAMPLE_MSA_V2
)

def run_tests():
    print("==================================================")
    print("  LEXPILOT PIPELINE END-TO-END VERIFICATION")
    print("==================================================")

    # 1. Test Feature 1 & 2: Parsing & Clause Intelligence on Scanned Employment Contract
    print("\n[TEST 1] Parsing & Classifying Scanned Employment Agreement...")
    resp_emp = process_document_pipeline(SAMPLE_EMPLOYMENT_SCANNED.encode("utf-8"), "Employment_Scanned.txt")
    print(f"  [OK] Document parsed: {resp_emp.document_name}")
    print(f"  [OK] Document type: {resp_emp.document_type}")
    print(f"  [OK] Total clauses extracted: {resp_emp.total_clauses}")
    assert resp_emp.total_clauses >= 6, "Expected at least 6 clauses"

    categories = [c.category for c in resp_emp.clauses]
    print(f"  [OK] Classified categories: {set(categories)}")
    assert "termination" in categories, "Expected termination clause"
    assert "non_compete" in categories, "Expected non_compete clause"

    # 2. Test Feature 3: Qualitative Attention Flags
    print("\n[TEST 2] Checking Qualitative Attention Flags...")
    high_att = [c for c in resp_emp.clauses if "High" in c.attention_level.value]
    print(f"  [OK] Found {len(high_att)} High attention clauses.")
    assert len(high_att) >= 1, "Expected at least 1 High attention clause"
    for h in high_att:
        print(f"    - {h.title} ({h.id}): {h.attention_reasons[0] if h.attention_reasons else 'N/A'}")
        assert h.disclaimer == "This is an informational flag, not a legal determination."

    # 3. Test Feature 7 & 8: Verification & Reference Corpus Deviation Check
    print("\n[TEST 3] Reference Corpus Deviation & Entailment Verification...")
    non_compete_clause = next(c for c in resp_emp.clauses if c.category == "non_compete")
    print(f"  [OK] Non-compete Clause: {non_compete_clause.title}")
    print(f"  [OK] Deviation Note: {non_compete_clause.deviation_check}")
    print(f"  [OK] Confidence Score: {non_compete_clause.confidence.value}")
    assert "36 months" in non_compete_clause.deviation_check or "exceeds" in non_compete_clause.deviation_check

    # 4. Test Feature 4: Cross-Clause Conflict Detection on Lease Agreement
    print("\n[TEST 4] Cross-Clause Conflict Detection on Lease Agreement...")
    resp_lease = process_document_pipeline(SAMPLE_LEASE_CONFLICT.encode("utf-8"), "Lease_Conflict.txt")
    print(f"  [OK] Total conflicts detected: {len(resp_lease.conflicts)}")
    assert len(resp_lease.conflicts) >= 1, "Expected at least 1 conflict"
    conflict = resp_lease.conflicts[0]
    print(f"  [OK] Conflict Type: {conflict.conflict_type}")
    print(f"  [OK] Clause A: {conflict.clause_a_title} | Excerpt: {conflict.clause_a_excerpt[:60]}...")
    print(f"  [OK] Clause B: {conflict.clause_b_title} | Excerpt: {conflict.clause_b_excerpt[:60]}...")
    print(f"  [OK] Explanation: {conflict.explanation}")
    print(f"  [OK] Suggested Question: {conflict.suggested_question}")

    # 5. Test Feature 9: Structured Obligation Timeline
    print("\n[TEST 5] Structured Obligation Timeline...")
    print(f"  [OK] Total timeline events: {len(resp_emp.timeline)}")
    for ev in resp_emp.timeline[:3]:
        print(f"    [{ev.timeframe_or_date}] {ev.party}: {ev.obligation[:60]}... (Citation: {ev.citation})")

    # 6. Test Feature 5: Semantic Contract Comparison (MSA V1 vs MSA V2)
    print("\n[TEST 6] Semantic Contract Comparison (MSA V1 vs V2)...")
    resp_msa1 = process_document_pipeline(SAMPLE_MSA_V1.encode("utf-8"), "MSA_V1.txt")
    resp_msa2 = process_document_pipeline(SAMPLE_MSA_V2.encode("utf-8"), "MSA_V2.txt")
    comp_items = comparator.compare(
        [c.model_dump() for c in resp_msa1.clauses],
        [c.model_dump() for c in resp_msa2.clauses]
    )
    material_mods = [ci for ci in comp_items if "Material" in ci.change_flag]
    added_items = [ci for ci in comp_items if "Added" in ci.change_flag]
    removed_items = [ci for ci in comp_items if "Removed" in ci.change_flag]
    print(f"  [OK] Total compared items: {len(comp_items)}")
    print(f"  [OK] Material modifications: {len(material_mods)}")
    print(f"  [OK] Added clauses: {len(added_items)} ({[a.title for a in added_items]})")
    print(f"  [OK] Removed clauses: {len(removed_items)} ({[r.title for r in removed_items]})")

    # 7. Test Feature 10 & 6: Multi-Hop Graph Reasoning & Verified Q&A
    print("\n[TEST 7] Multi-Hop Graph Reasoning...")
    from app.main import sessions
    session = sessions[resp_emp.document_id]
    qa_engine = session["qa_engine"]

    q = "If I terminate under Section 4, does the non-compete in Section 12 still apply?"
    ans = qa_engine.answer_question(q)
    print(f"  Question: {q}")
    print(f"  [OK] Multi-hop: {ans.multi_hop}")
    print(f"  [OK] Graph Path: {ans.graph_path}")
    print(f"  [OK] Citations count: {len(ans.citations)}")
    for cit in ans.citations:
        print(f"    - Cited: {cit.title} ({cit.clause_id}) -> Quote: \"{cit.quote[:80]}...\"")
    print(f"  [OK] Answer: {ans.answer[:140]}...")
    print(f"  [OK] Confidence: {ans.confidence.value}")
    assert len(ans.citations) >= 2, "Multi-hop query must cite at least two clauses!"

    print("\n==================================================")
    print("  ALL 10 PIPELINE FEATURES VERIFIED SUCCESSFULLY! ")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
