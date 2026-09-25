"""
LexPilot - Clause Engine: Field Extractor
-----------------------------------------
Extracts structured legal entities from clause text:
  - Parties involved
  - Dates and operational timeframes
  - Monetary amounts and fee formulas
  - Specific affirmative & negative obligations (modal extraction)
  - Defined legal terms referenced
"""

import re
from typing import List, Dict, Any

class FieldExtractor:
    def __init__(self):
        # Known common legal roles compiled into a single high-efficiency pass
        self.roles_regex = re.compile(
            r'\b(?:Company|Client|Contractor|Employee|Employer|Consultant|Vendor|Customer|Landlord|Tenant|Lessor|Lessee|Disclosing Party|Receiving Party|Licensor|Licensee|Service Provider|Party|Parties)\b'
        )

        # Regex for dates, timeframes, and deadlines
        self.date_regex = re.compile(
            r'\b(?:'
            r'\d{1,2}\s+(?:days?|business days?|calendar days?|months?|years?)|'
            r'(?:within|after|prior to|no later than)\s+\d{1,2}\s+(?:days?|business days?|months?)|'
            r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s*\d{4}|'
            r'\d{1,2}/\d{1,2}/\d{2,4}|'
            r'net\s+\d{1,2}|'
            r'immediately|at-will|quarterly|annually|per annum'
            r')\b',
            re.IGNORECASE
        )

        # Regex for monetary figures and percentages
        self.money_regex = re.compile(
            r'(?:\$\s*\d+(?:,\d{3})*(?:\.\d{2})?|\b\d+(?:,\d{3})*\s*dollars\b|\b\d+(?:\.\d+)?\s*%\s*(?:interest|penalty|fee)?|\b€\s*\d+(?:,\d{3})*)',
            re.IGNORECASE
        )

        # Modal verbs for obligation extraction
        self.obligation_split_regex = re.compile(r'([A-Z][^\.\?!;]*(?:\bshall\b|\bmust\b|\bagrees to\b|\bis required to\b|\bwill\b|\bshall not\b|\bmay not\b)[^\.\?!;]*)')

        # Defined terms (quoted capitalized words or capitalized title-case sequences)
        self.defined_terms_quoted_regex = re.compile(r'\"([A-Z][A-Za-z0-9\s]{2,35})\"|\“([A-Z][A-Za-z0-9\s]{2,35})\”')

    def extract_fields(self, text: str) -> Dict[str, List[str]]:
        """
        Extracts structured fields from clause text.
        """
        return {
            "parties_involved": self._extract_parties(text),
            "dates": self._extract_dates(text),
            "monetary_amounts": self._extract_money(text),
            "obligations": self._extract_obligations(text),
            "defined_terms": self._extract_defined_terms(text)
        }

    def _extract_parties(self, text: str) -> List[str]:
        matches = self.roles_regex.findall(text)
        return sorted(list(set(matches)))

    def _extract_dates(self, text: str) -> List[str]:
        matches = self.date_regex.findall(text)
        # Deduplicate while preserving order
        seen = set()
        out = []
        for m in matches:
            cleaned = m.strip()
            if cleaned.lower() not in seen:
                seen.add(cleaned.lower())
                out.append(cleaned)
        return out[:6]

    def _extract_money(self, text: str) -> List[str]:
        matches = self.money_regex.findall(text)
        seen = set()
        out = []
        for m in matches:
            cleaned = m.strip()
            if cleaned not in seen:
                seen.add(cleaned)
                out.append(cleaned)
        return out[:5]

    def _extract_obligations(self, text: str) -> List[str]:
        matches = self.obligation_split_regex.findall(text)
        obligations = []
        for m in matches:
            cleaned = " ".join(m.split()).strip()
            if 15 < len(cleaned) < 250:
                obligations.append(cleaned)
        return obligations[:4]

    def _extract_defined_terms(self, text: str) -> List[str]:
        terms = set()
        # From quotes
        for m in self.defined_terms_quoted_regex.finditer(text):
            val = m.group(1) or m.group(2)
            if val and len(val.split()) <= 4:
                terms.add(val.strip())

        # Capitalized multi-word phrases frequently used in legal docs
        caps_phrases = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\b', text)
        for cp in caps_phrases:
            if cp not in ["United States", "New York", "In Witness Whereof"]:
                if len(cp.split()) in [2, 3]:
                    terms.add(cp)

        return sorted(list(terms))[:8]
