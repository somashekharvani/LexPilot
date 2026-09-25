"""
LexPilot - Obligation Timeline Extractor
----------------------------------------
Extracts chronological milestones, deadlines, and operational obligations
into a structured timeline visualization model.
"""

import re
from typing import List, Dict, Any
from ..models.schemas import TimelineEvent, AttentionLevel, ConfidenceLevel

class TimelineExtractor:
    def __init__(self):
        # Timeframe priority order mapping for relative chronological ordering
        self.timeframe_weights = [
            (r'effective date|commencement|upon signing|day 1|immediately', 10),
            (r'within\s+5\s+days|5\s+days', 20),
            (r'within\s+10\s+days|10\s+days', 30),
            (r'within\s+15\s+days|15\s+days', 40),
            (r'within\s+30\s+days|30\s+days|monthly|net\s+30', 50),
            (r'within\s+45\s+days|45\s+days|net\s+45', 60),
            (r'within\s+60\s+days|60\s+days', 70),
            (r'quarterly|90\s+days', 80),
            (r'annually|1\s+year|end of term|prior to expiration', 90),
            (r'upon termination|on termination|survive', 100),
            (r'6\s+months?\s+(?:following|post|after)', 110),
            (r'1\s+year\s+(?:following|post|after)|12\s+months', 120),
            (r'2\s+years?\s+(?:following|post|after)|24\s+months', 130),
            (r'indefinitely|perpetual', 140)
        ]

    def extract_timeline(self, clauses: List[Dict[str, Any]]) -> List[TimelineEvent]:
        """
        Builds a chronological list of timeline events across all clauses.
        """
        events: List[TimelineEvent] = []
        counter = 1

        for c in clauses:
            cid = c["id"]
            title = c.get("title", f"Section {c.get('number', '')}")
            text = c.get("text", "")
            category = c.get("category", "other")
            att_level = c.get("attention_level", AttentionLevel.NORMAL)
            fields = c.get("fields", {})

            dates = fields.get("dates", [])
            obligations = fields.get("obligations", [])
            parties = fields.get("parties_involved", [])
            default_party = parties[0] if parties else "Relevant Party"

            # If obligations and dates exist, map them
            if dates:
                for d in dates[:3]:
                    # Find closest obligation sentence
                    ob_sentence = self._find_matching_obligation(text, d, obligations)
                    rel_order = self._calculate_relative_order(d)

                    events.append(TimelineEvent(
                        id=f"TL-{counter}",
                        clause_id=cid,
                        clause_title=title,
                        party=default_party,
                        timeframe_or_date=d.title(),
                        obligation=ob_sentence or f"Contractual duty governed by {title}.",
                        category=category,
                        relative_order=rel_order,
                        attention_level=att_level,
                        confidence=ConfidenceLevel.HIGH,
                        citation=f"{title} ({cid})"
                    ))
                    counter += 1

            elif obligations and category in ["termination", "confidentiality", "payment", "non_compete"]:
                # Obligation without explicit date
                for ob in obligations[:2]:
                    events.append(TimelineEvent(
                        id=f"TL-{counter}",
                        clause_id=cid,
                        clause_title=title,
                        party=default_party,
                        timeframe_or_date="Ongoing Obligation",
                        obligation=ob,
                        category=category,
                        relative_order=75,
                        attention_level=att_level,
                        confidence=ConfidenceLevel.HIGH,
                        citation=f"{title} ({cid})"
                    ))
                    counter += 1

        # Sort chronologically by relative_order
        events.sort(key=lambda x: x.relative_order)
        return events

    def _calculate_relative_order(self, timeframe_text: str) -> int:
        tf_lower = timeframe_text.lower()
        for pat, weight in self.timeframe_weights:
            if re.search(pat, tf_lower):
                return weight
        return 65

    def _find_matching_obligation(self, text: str, date_str: str, obligations: List[str]) -> str:
        # First try finding sentence in text containing date_str
        for sentence in re.split(r'[\.\r\n]+', text):
            if date_str.lower() in sentence.lower() and len(sentence.strip()) > 20:
                return sentence.strip() + "."

        if obligations:
            return obligations[0]
        return ""
