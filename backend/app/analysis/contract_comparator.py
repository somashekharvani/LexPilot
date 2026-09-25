"""
LexPilot - Semantic Contract Comparator
---------------------------------------
Performs semantic clause-to-clause alignment between two uploaded contracts
(e.g., Original vs. Revised Draft, or Client Template vs. Vendor Mark-up).
Handles reordered, renumbered, and reworded clauses.
"""

import re
from typing import List, Dict, Any, Tuple
from ..models.schemas import ComparisonItem, AttentionLevel, ConfidenceLevel
from ..verification.verifier import VerificationAgent

class ContractComparator:
    def __init__(self, verifier: VerificationAgent):
        self.verifier = verifier

    def compare(self, doc_a_clauses: List[Dict[str, Any]], doc_b_clauses: List[Dict[str, Any]]) -> List[ComparisonItem]:
        """
        Semantically aligns clauses between Document A and Document B.
        """
        results: List[ComparisonItem] = []
        matched_b_ids = set()

        # Step 1: Match each clause in A with best counterpart in B
        for ca in doc_a_clauses:
            cat_a = ca.get("category", "other")
            title_a = ca.get("title", "")
            text_a = ca.get("text", "")

            best_b = None
            best_score = 0.0

            for cb in doc_b_clauses:
                if cb["id"] in matched_b_ids:
                    continue

                cat_b = cb.get("category", "other")
                title_b = cb.get("title", "")
                text_b = cb.get("text", "")

                score = self._compute_similarity(cat_a, title_a, text_a, cat_b, title_b, text_b)
                if score > best_score:
                    best_score = score
                    best_b = cb

            if best_b and best_score >= 0.40:
                matched_b_ids.add(best_b["id"])
                # Evaluate delta
                item = self._analyze_pair_delta(ca, best_b)
                results.append(item)
            else:
                # Removed in revision
                results.append(ComparisonItem(
                    category=cat_a,
                    title=title_a,
                    version_a_clause_id=ca["id"],
                    version_a_text=text_a,
                    version_b_clause_id=None,
                    version_b_text=None,
                    change_flag="Removed in Revision",
                    semantic_delta=f"Clause was deleted in revised draft. Previously governed {cat_a} under {title_a}.",
                    attention_level=AttentionLevel.HIGH if cat_a in ["indemnification", "liability", "termination", "non_compete"] else AttentionLevel.REVIEW,
                    confidence=ConfidenceLevel.HIGH
                ))

        # Step 2: Check for clauses added in B that were not matched
        for cb in doc_b_clauses:
            if cb["id"] not in matched_b_ids:
                cat_b = cb.get("category", "other")
                title_b = cb.get("title", "")
                text_b = cb.get("text", "")

                results.append(ComparisonItem(
                    category=cat_b,
                    title=title_b,
                    version_a_clause_id=None,
                    version_a_text=None,
                    version_b_clause_id=cb["id"],
                    version_b_text=text_b,
                    change_flag="Added in Revision",
                    semantic_delta=f"New clause introduced in revised draft ({cat_b}). Requires review for novel obligations.",
                    attention_level=AttentionLevel.HIGH if cat_b in ["indemnification", "liability", "non_compete"] else AttentionLevel.NORMAL,
                    confidence=ConfidenceLevel.HIGH
                ))

        return results

    def _compute_similarity(self, cat_a: str, title_a: str, text_a: str, cat_b: str, title_b: str, text_b: str) -> float:
        score = 0.0
        # Category match
        if cat_a != "other" and cat_a == cat_b:
            score += 0.50

        # Title match
        words_a = set(re.findall(r'\b[a-z]{3,}\b', title_a.lower()))
        words_b = set(re.findall(r'\b[a-z]{3,}\b', title_b.lower()))
        if words_a and words_b:
            title_overlap = len(words_a.intersection(words_b)) / min(len(words_a), len(words_b))
            score += title_overlap * 0.30

        # Text overlap
        text_words_a = set(re.findall(r'\b[a-z]{4,}\b', text_a[:400].lower()))
        text_words_b = set(re.findall(r'\b[a-z]{4,}\b', text_b[:400].lower()))
        if text_words_a and text_words_b:
            text_overlap = len(text_words_a.intersection(text_words_b)) / max(len(text_words_a), len(text_words_b))
            score += text_overlap * 0.25

        return score

    def _analyze_pair_delta(self, ca: Dict[str, Any], cb: Dict[str, Any]) -> ComparisonItem:
        text_a = ca.get("text", "").strip()
        text_b = cb.get("text", "").strip()
        cat = ca.get("category", "other")
        title = ca.get("title", cb.get("title", ""))

        if text_a == text_b:
            return ComparisonItem(
                category=cat,
                title=title,
                version_a_clause_id=ca["id"],
                version_a_text=text_a,
                version_b_clause_id=cb["id"],
                version_b_text=text_b,
                change_flag="Unchanged",
                semantic_delta="Clause text is identical between both versions.",
                attention_level=AttentionLevel.NORMAL,
                confidence=ConfidenceLevel.HIGH
            )

        # Check substantive numbers / monetary / day differences
        nums_a = re.findall(r'\b\d+(?:,\d{3})*(?:\.\d+)?%?|\$\s*\d+(?:,\d{3})*', text_a)
        nums_b = re.findall(r'\b\d+(?:,\d{3})*(?:\.\d+)?%?|\$\s*\d+(?:,\d{3})*', text_b)

        differences = []
        is_material = False

        if set(nums_a) != set(nums_b):
            is_material = True
            differences.append(f"Numerical terms altered: Version A ({', '.join(nums_a) if nums_a else 'none'}) vs Version B ({', '.join(nums_b) if nums_b else 'none'}).")

        # Check key legal phrases changes
        for kw in ["sole remedy", "unlimited", "consequential", "without cause", "immediate", "attorneys' fees"]:
            in_a = kw in text_a.lower()
            in_b = kw in text_b.lower()
            if in_a != in_b:
                is_material = True
                status = f"Added '{kw}'" if in_b else f"Removed '{kw}'"
                differences.append(f"Substantive covenant shift: {status} in revised version.")

        if is_material:
            delta_msg = " ".join(differences) if differences else "Material alterations to contractual terms and risk allocation."
            att = AttentionLevel.HIGH if cat in ["liability", "indemnification", "payment", "termination"] else AttentionLevel.REVIEW
            flag = "Modified - Material"
        else:
            delta_msg = "Minor stylistic or clarificatory wording updates without shifting core legal liabilities."
            att = AttentionLevel.NORMAL
            flag = "Modified - Minor"

        # Entailment verification of delta
        conf, v_reason = self.verifier.verify_comparison_delta(text_a, text_b, delta_msg)

        return ComparisonItem(
            category=cat,
            title=title,
            version_a_clause_id=ca["id"],
            version_a_text=text_a,
            version_b_clause_id=cb["id"],
            version_b_text=text_b,
            change_flag=flag,
            semantic_delta=delta_msg,
            attention_level=att,
            confidence=conf
        )
