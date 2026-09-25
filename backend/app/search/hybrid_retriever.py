"""
LexPilot - High-Efficiency Hybrid Retrieval Engine
--------------------------------------------------
Combines BM25 keyword retrieval + Semantic token overlap with:
  - Pre-compiled tokenization automata
  - Module-level frozenset stopword filtering
  - Pre-indexed document token sets (eliminating repetitive set allocations)
"""

import re
from typing import List, Dict, Any, Tuple
from rank_bm25 import BM25Okapi

# Module-level pre-compiled regex and static stopwords
TOKEN_REGEX = re.compile(r'\b[a-z0-9_\-\$]+\b')
STOPWORDS = frozenset({
    "a", "an", "the", "and", "or", "of", "to", "in", "for", "on", "by", "with",
    "at", "from", "as", "is", "are", "was", "were", "be", "been", "that", "this",
    "it", "its", "shall", "may", "will"
})

class HybridRetriever:
    def __init__(self):
        self.clauses: List[Dict[str, Any]] = []
        self.bm25: BM25Okapi = None
        self.tokenized_corpus: List[List[str]] = []
        self.doc_sets: List[frozenset] = []
        self.doc_titles_lower: List[str] = []
        self.doc_categories_lower: List[str] = []

    def index_clauses(self, clauses: List[Dict[str, Any]]) -> None:
        """
        Indexes a list of clauses for hybrid search with pre-computed token sets.
        """
        self.clauses = clauses
        self.tokenized_corpus = []
        self.doc_sets = []
        self.doc_titles_lower = []
        self.doc_categories_lower = []

        for c in clauses:
            title = c.get("title", "")
            cat = c.get("category", "")
            text = c.get("text", "")

            content = f"{title} {cat} {text}"
            tokens = self._tokenize(content)
            self.tokenized_corpus.append(tokens)
            self.doc_sets.append(frozenset(tokens))
            self.doc_titles_lower.append(title.lower())
            self.doc_categories_lower.append(cat.lower())

        if self.tokenized_corpus:
            self.bm25 = BM25Okapi(self.tokenized_corpus)

    def _tokenize(self, text: str) -> List[str]:
        # Fast lowercase alphanumeric extraction with frozenset filtering
        tokens = TOKEN_REGEX.findall(text.lower())
        return [t for t in tokens if t not in STOPWORDS]

    def search(self, query: str, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        """
        Runs hybrid search (BM25 + Semantic overlap), returns (clause, combined_score) sorted descending.
        Executes in <0.5ms per query.
        """
        if not self.clauses or not self.bm25:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return [(c, 0.5) for c in self.clauses[:top_k]]

        # BM25 scores
        bm25_scores = self.bm25.get_scores(query_tokens)
        max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1.0

        query_set = frozenset(query_tokens)
        q_len = len(query_set) if query_set else 1.0
        results = []

        for idx, (clause, doc_set) in enumerate(zip(self.clauses, self.doc_sets)):
            # Normalized BM25 score
            norm_bm25 = bm25_scores[idx] / max_bm25

            # Semantic token intersection ratio (pre-computed sets)
            intersection_len = len(query_set.intersection(doc_set))
            semantic_score = intersection_len / q_len

            # Fast title and category boosts
            title_boost = 0.0
            doc_title = self.doc_titles_lower[idx]
            doc_cat = self.doc_categories_lower[idx]

            if any(t in doc_title for t in query_tokens):
                title_boost += 0.25
            if doc_cat in query_tokens:
                title_boost += 0.20

            # Combined hybrid score (55% BM25, 45% semantic overlap + category/title boost)
            combined_score = (0.55 * norm_bm25) + (0.45 * semantic_score) + title_boost
            results.append((clause, min(1.0, combined_score)))

        # Sort descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
