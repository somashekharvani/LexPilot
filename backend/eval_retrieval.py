"""
LexPilot - Retrieval Evaluation Harness
---------------------------------------
Evaluates Hybrid Retriever and QueryPlanner performance against a benchmark of
standard legal queries and ground-truth relevant clauses.

Metrics reported:
  - Recall@1, Recall@3, Recall@5
  - Mean Reciprocal Rank (MRR)
  - Precision@5
  - Citation Coverage (%)
  - Average Latency (ms)
"""

import sys
import os
import time
from typing import List, Dict, Any, Set

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.main import process_document_pipeline, sessions
from app.search.query_planner import QueryPlanner
from app.sample_documents.sample_data import (
    SAMPLE_EMPLOYMENT_SCANNED, SAMPLE_LEASE_CONFLICT, SAMPLE_MSA_V2
)

# Define benchmark query suites with target ground-truth clause numbers
BENCHMARK_CASES = [
    # Document 1: Scanned Employment Agreement
    {
        "doc_name": "Employment Agreement",
        "doc_text": SAMPLE_EMPLOYMENT_SCANNED,
        "filename": "Employment_Scanned.txt",
        "queries": [
            {
                "query": "How many days notice are required for termination without cause?",
                "target_sections": {"4"},
                "description": "Termination notice period (Section 4)"
            },
            {
                "query": "What are the post-employment non-compete restrictions?",
                "target_sections": {"12"},
                "description": "Non-compete covenants (Section 12)"
            },
            {
                "query": "What is the annual base salary and executive compensation?",
                "target_sections": {"2"},
                "description": "Compensation & Benefits (Section 2)"
            },
            {
                "query": "What are the obligations regarding confidential company trade secrets?",
                "target_sections": {"3"},
                "description": "Confidentiality obligations (Section 3)"
            },
            {
                "query": "Which state jurisdiction governs dispute resolution and venue?",
                "target_sections": {"14"},
                "description": "Governing Law & Venue (Section 14)"
            },
            {
                "query": "If I terminate under Section 4, does the non-compete in Section 12 still apply?",
                "target_sections": {"4", "12"},
                "description": "Multi-hop survival query (Sections 4 & 12)"
            }
        ]
    },
    # Document 2: Commercial Lease
    {
        "doc_name": "Commercial Lease",
        "doc_text": SAMPLE_LEASE_CONFLICT,
        "filename": "Commercial_Lease.txt",
        "queries": [
            {
                "query": "What is the required notice period for termination of the lease?",
                "target_sections": {"4", "14"},
                "description": "Conflicting termination notices (Sections 4 & 14)"
            },
            {
                "query": "What late fees or penalties apply if rent is not received by the fifth?",
                "target_sections": {"6"},
                "description": "Rent & late fee penalty (Section 6)"
            },
            {
                "query": "Who is responsible for HVAC, roof, and structural maintenance?",
                "target_sections": {"8"},
                "description": "Maintenance duties (Section 8)"
            },
            {
                "query": "How many hours notice must the landlord provide before entering for inspection?",
                "target_sections": {"10"},
                "description": "Landlord entry notice (Section 10)"
            },
            {
                "query": "Which state laws govern the lease agreement?",
                "target_sections": {"16"},
                "description": "Governing law (Section 16)"
            }
        ]
    },
    # Document 3: Master Services Agreement V2
    {
        "doc_name": "Master Services Agreement",
        "doc_text": SAMPLE_MSA_V2,
        "filename": "MSA_V2.txt",
        "queries": [
            {
                "query": "What is the aggregate monetary ceiling on liability damages?",
                "target_sections": {"6"},
                "description": "Limitation of liability cap (Section 6)"
            },
            {
                "query": "Who defends and indemnifies against third-party intellectual property claims?",
                "target_sections": {"7"},
                "description": "IP indemnification (Section 7)"
            },
            {
                "query": "What security compliance and privacy regulations must the vendor follow?",
                "target_sections": {"10"},
                "description": "Data privacy & security (Section 10)"
            },
            {
                "query": "How many days does a party have to cure a material breach before termination?",
                "target_sections": {"3"},
                "description": "Termination cure window (Section 3)"
            },
            {
                "query": "What are the payment terms and invoicing schedule?",
                "target_sections": {"2"},
                "description": "Payment terms & invoicing (Section 2)"
            }
        ]
    }
]

def run_retrieval_evaluation():
    planner = QueryPlanner()

    total_queries = 0
    hits_at_1 = 0
    hits_at_3 = 0
    hits_at_5 = 0
    reciprocal_ranks = []
    precision_at_5_list = []
    latencies = []

    print("=" * 72)
    print("        LEXPILOT RETRIEVAL EVALUATION HARNESS (BENCHMARK)       ")
    print("=" * 72)

    for case in BENCHMARK_CASES:
        doc_name = case["doc_name"]
        filename = case["filename"]
        resp = process_document_pipeline(case["doc_text"].encode("utf-8"), filename)
        session = sessions[resp.document_id]
        graph = session["clause_graph"]
        retriever = session["retriever"]

        print(f"\nDocument Corpus: {doc_name} ({resp.total_clauses} clauses)")
        print("-" * 72)

        for q_item in case["queries"]:
            query = q_item["query"]
            targets: Set[str] = set(q_item["target_sections"])
            total_queries += 1

            start_t = time.perf_counter()
            retrieved_clauses = planner.execute_planned_retrieval(query, retriever, graph, top_k=5)
            elapsed_ms = (time.perf_counter() - start_t) * 1000.0
            latencies.append(elapsed_ms)

            retrieved_sections = [str(c.get("number", "")) for c in retrieved_clauses]

            hit_1 = bool(targets.intersection(set(retrieved_sections[:1])))
            hit_3 = bool(targets.intersection(set(retrieved_sections[:3])))
            hit_5 = bool(targets.intersection(set(retrieved_sections[:5])))

            if hit_1:
                hits_at_1 += 1
            if hit_3:
                hits_at_3 += 1
            if hit_5:
                hits_at_5 += 1

            # Reciprocal Rank
            rr = 0.0
            for rank, sec in enumerate(retrieved_sections, start=1):
                if sec in targets:
                    rr = 1.0 / rank
                    break
            reciprocal_ranks.append(rr)

            # Precision@5
            relevant_in_top5 = len(targets.intersection(set(retrieved_sections[:5])))
            precision_at_5 = relevant_in_top5 / 5.0
            precision_at_5_list.append(precision_at_5)

            status_icon = "PASS" if hit_1 else ("HIT3" if hit_3 else "MISS")
            print(f"  [{status_icon:4s}] RR: {rr:.2f} | Latency: {elapsed_ms:4.1f}ms | Target: {targets} -> Top-3: {retrieved_sections[:3]} | \"{query[:44]}...\"")

    # Aggregate Metrics
    recall_1 = (hits_at_1 / total_queries) * 100.0
    recall_3 = (hits_at_3 / total_queries) * 100.0
    recall_5 = (hits_at_5 / total_queries) * 100.0
    mrr = (sum(reciprocal_ranks) / total_queries)
    avg_precision_5 = (sum(precision_at_5_list) / total_queries) * 100.0
    avg_latency_ms = sum(latencies) / len(latencies)

    print("\n" + "=" * 72)
    print("                    EVALUATION SUMMARY RESULTS                  ")
    print("=" * 72)
    print(f"Total Benchmark Queries : {total_queries}")
    print(f"Recall@1                : {recall_1:.1f}%")
    print(f"Recall@3                : {recall_3:.1f}%")
    print(f"Recall@5 (Coverage)     : {recall_5:.1f}%")
    print(f"Mean Reciprocal Rank    : {mrr:.4f}")
    print(f"Avg Precision@5         : {avg_precision_5:.1f}%")
    print(f"Avg Retrieval Latency   : {avg_latency_ms:.2f} ms")
    print("=" * 72)

    return {
        "total_queries": total_queries,
        "recall_1": recall_1,
        "recall_3": recall_3,
        "recall_5": recall_5,
        "mrr": mrr,
        "avg_precision_5": avg_precision_5,
        "avg_latency_ms": avg_latency_ms
    }

if __name__ == "__main__":
    run_retrieval_evaluation()
