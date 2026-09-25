"""
LexPilot - Hybrid Retrieval Engine
----------------------------------
Combines BM25 keyword retrieval + Semantic vector/token similarity
to retrieve clauses for Q&A, multi-hop reasoning, and cross-document alignment.
"""

import re
import math
from typing import List, Dict, Any, Tuple
from rank_bm25 import BM25Okapi

class HybridRetriever:
    def __init__(self):
        self.clauses: List[Dict[str, Any]] = []
        self.bm25: BM25Okapi = None
        self.tokenized_corpus: List[List[str]] = []

    def index_clauses(self, clauses: List[Dict[str, Any]]) -> None:
        """
        Indexes a list of clauses for hybrid search.
        """
        self.clauses = clauses
        self.tokenized_corpus = []

        for c in clauses:
            content = f"{c.get('title', '')} {c.get('category', '')} {c.get('text', '')}"
            tokens = self._tokenize(content)
            self.tokenized_corpus.append(tokens)

        if self.tokenized_corpus:
            self.bm25 = BM25Okapi(self.tokenized_corpus)

    def _tokenize(self, text: str) -> List[str]:
        # Lowercase, clean alphanumeric tokens
        tokens = re.findall(r'\b[a-z0-9_\-\$]+\b', text.lower())
        # Filter basic stop words
        stopwords = {
            "a", "an", "the", "and", "or", "of", "to", "in", "for", "on", "by", "with",
            "at", "from", "as", "is", "are", "was", "were", "be", "been", "that", "this"
        }
        return [t for t in tokens if t not in stopwords]

    def search(self, query: str, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        """
        Runs hybrid search (BM25 + Semantic overlap), returns (clause, combined_score) sorted descending.
        """
        if not self.clauses or not self.bm25:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return [(c, 0.5) for c in self.clauses[:top_k]]

        # BM25 scores
        bm25_scores = self.bm25.get_scores(query_tokens)
        max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1.0

        # Semantic/Jaccard overlap scores
        query_set = set(query_tokens)
        results = []

        for idx, (clause, doc_tokens) in enumerate(zip(self.clauses, self.tokenized_corpus)):
            doc_set = set(doc_tokens)
            # Normalized BM25
            norm_bm25 = bm25_scores[idx] / max_bm25

            # Semantic token intersection ratio
            intersection = query_set.intersection(doc_set)
            semantic_score = len(intersection) / len(query_set) if query_set else 0.0

            # Boost if query mentions clause category or title directly
            title_boost = 0.0
            if any(t in clause.get("title", "").lower() for t in query_tokens):
                title_boost = 0.25
            if any(t == clause.get("category", "").lower() for t in query_tokens):
                title_boost += 0.20

            # Combined hybrid score (60% BM25, 40% semantic overlap + title boost)
            combined_score = (0.55 * norm_bm25) + (0.45 * semantic_score) + title_boost
            results.append((clause, min(1.0, combined_score)))

        # Sort descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
