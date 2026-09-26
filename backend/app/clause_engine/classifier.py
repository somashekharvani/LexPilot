"""
LexPilot - Clause Engine: Classifier
------------------------------------
Classifies legal clauses into standard legal categories:
  1. termination
  2. payment
  3. liability
  4. confidentiality
  5. indemnification
  6. renewal
  7. governing_law
  8. non_compete
  9. notice
  10. other

Drawing directly on the CUAD (Contract Understanding Atticus Dataset) taxonomy patterns.
"""

import re
from typing import Dict, Any, Tuple

class ClauseClassifier:
    def __init__(self):
        # Lexical pattern banks for standard categories
        self.category_patterns = {
            "termination": [
                r'\b(terminat\w*|cancel\w*|expir\w*|convenience|for cause|breach of this agreement|cure period|without cause)\b',
                r'\b(right to terminate|effect of termination|immediate termination)\b'
            ],
            "payment": [
                r'\b(fee|fees|payment\w*|invoice\w*|invoicing|remit\w*|compensation|salary|reimburse\w*|due date|net \d+|late payment|interest on late|billing)\b',
                r'(\$\s*\d+|\b\d+\s*dollars\b|\beuro\b)'
            ],
            "liability": [
                r'\b(limitation of liability|aggregate liability|direct damages|consequential damages|indirect damages|incidental damages|punitive damages|waiver of damages|liability cap|in no event shall)\b',
                r'\b(exceed the total amount|disclaimer of warranties|as is|sole remedy)\b'
            ],
            "confidentiality": [
                r'\b(confidential\w*|proprietary information|trade secret|non-disclosure|keep confidential|disclosure of confidential|return of materials|standard of care)\b',
                r'\b(confidentiality obligations|compelled disclosure|exceptions to confidential)\b'
            ],
            "indemnification": [
                r'\b(indemnif\w*|indemnitee|indemnitor|hold harmless|defend|defense of claim|losses,\s*damages,\s*liabilities|third[- ]party claim)\b'
            ],
            "renewal": [
                r'\b(renew\w*|extension|extend\w*|automatic renewal|evergreen|successive period|renewal term|opt-out of renewal)\b'
            ],
            "governing_law": [
                r'\b(governing law|applicable law|jurisdiction|venue|courts of|laws of the state of|dispute resolution|arbitration|forum non conveniens)\b'
            ],
            "non_compete": [
                r'\b(non-compete|non-competition|non competition|restrictive covenant\w*|solicit\w*|non-solicitation|not to compete|compete\w*|competitive business|geographical scope|restricted territory|during employment and for a period)\b'
            ],
            "notice": [
                r'\b(notice\w*|written notice|registered mail|certified mail|overnight courier|email notice|days\' written notice|address for notices|deemed received)\b'
            ]
        }

    def classify(self, title: str, text: str) -> Tuple[str, float]:
        """
        Returns (category, confidence_score)
        """
        combined = f"{title}\n{text}".lower()

        scores: Dict[str, float] = {cat: 0.0 for cat in self.category_patterns.keys()}
        title_lower = title.lower()

        # Title priority weighting
        for cat, patterns in self.category_patterns.items():
            for pat in patterns:
                # Strong match in title
                if re.search(pat, title_lower):
                    scores[cat] += 4.0
                # Matches in body
                matches = re.findall(pat, combined)
                scores[cat] += len(matches) * 1.0

        best_cat = "other"
        best_score = 0.0

        for cat, score in scores.items():
            if score > best_score:
                best_score = score
                best_cat = cat

        if best_score < 1.5:
            return "other", 0.65

        confidence = min(0.98, 0.70 + (best_score * 0.04))
        return best_cat, round(confidence, 2)
