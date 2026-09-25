"""
LexPilot - Reference Corpus Deviation Detector
----------------------------------------------
Compares extracted clauses against preloaded standard baseline contract templates.
Flags material deviations from commercial norms as a distinct "Deviation Check" note.
"""

import re
from typing import Optional, Dict, Any
from .corpus_data import REFERENCE_CORPUS

class DeviationDetector:
    def __init__(self):
        self.corpus = REFERENCE_CORPUS

    def detect_deviation(self, doc_type: str, category: str, text: str) -> Optional[str]:
        """
        Returns a specific 'Deviation Check' note if text materially deviates from the template baseline.
        """
        # Normalize doc_type key
        dt_key = self._resolve_doc_type_key(doc_type)
        if not dt_key or dt_key not in self.corpus:
            dt_key = "employment" if "employ" in doc_type.lower() else "msa"

        template_cat = self.corpus.get(dt_key, {}).get(category)
        if not template_cat:
            # Fallback to checking msa or employment for standard categories
            template_cat = self.corpus.get("msa", {}).get(category) or self.corpus.get("employment", {}).get(category)

        if not template_cat:
            return None

        text_lower = text.lower()

        # Category specific checks
        if category == "termination":
            # Check notice days (supporting parenthesized formats like "thirty (30) days")
            m = re.search(r'(?:\((\d+)\)|\b(\d+)\b)\s*(?:days?|calendar days?|business days?)', text_lower)
            if m:
                actual_days = int(m.group(1) or m.group(2))
                std_days = template_cat.get("standard_notice_days", 30)
                if actual_days > std_days * 1.8:
                    return f"Deviation Check: Required notice period ({actual_days} days) is substantially longer than the standard baseline ({std_days} days) for this agreement type."
                elif actual_days < 10 and "without cause" in text_lower:
                    return f"Deviation Check: Short notice window ({actual_days} days) for termination without cause deviates from the standard {std_days}-day baseline."

        elif category == "non_compete":
            # Check duration in months / years (supporting parenthesized formats like "thirty-six (36) months")
            m_years = re.search(r'(?:\((\d+)\)|\b(\d+)\b)\s*years?', text_lower)
            m_months = re.search(r'(?:\((\d+)\)|\b(\d+)\b)\s*months?', text_lower)
            months = 0
            if m_years:
                months = int(m_years.group(1) or m_years.group(2)) * 12
            elif m_months:
                months = int(m_months.group(1) or m_months.group(2))

            if months > 18:
                return f"Deviation Check: Non-compete duration ({months} months) significantly exceeds standard commercial benchmark (12 months), creating heightened risk of unenforceability under many jurisdictions."
            if "worldwide" in text_lower or "any country" in text_lower:
                return "Deviation Check: Geographic scope ('worldwide') is significantly broader than standard bounded radius benchmarks (25-50 miles)."

        elif category == "payment":
            m_pct = re.search(r'(\d+(?:\.\d+)?)\s*%\s*(?:interest|penalty|late fee)?', text_lower)
            if m_pct:
                pct = float(m_pct.group(1))
                if pct > 5.0:
                    return f"Deviation Check: Late payment rate ({pct}%) exceeds typical market baseline (1.0% - 1.5% per month or 5% flat fee)."

        elif category == "liability":
            if "unlimited" in text_lower and "indemnif" not in text_lower:
                return "Deviation Check: Absence of reciprocal liability cap deviates from market standard 12-month fees paid limit."

        return "Deviation Check: Language aligns reasonably with standard commercial template benchmarks."

    def _resolve_doc_type_key(self, doc_type: str) -> str:
        dt = doc_type.lower()
        if "employ" in dt or "job" in dt or "offer" in dt:
            return "employment"
        if "nda" in dt or "confidential" in dt or "non-disclosure" in dt:
            return "nda"
        if "lease" in dt or "rent" in dt or "tenant" in dt:
            return "residential_lease"
        if "msa" in dt or "service" in dt or "vendor" in dt or "saas" in dt:
            return "msa"
        return "msa"
