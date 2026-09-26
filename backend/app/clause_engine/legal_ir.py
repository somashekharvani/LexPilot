"""
LexPilot - Clause Engine: Legal-IR Builder & Parser
---------------------------------------------------
Transforms raw clause text, classification, and extracted entities into the
canonical Legal Intermediate Representation (Legal-IR).
"""

import re
from typing import Dict, Any, List, Optional
from ..models.legal_ir import (
    LegalIRClause, ClauseIdentity, ClauseSemantic,
    ObligationItem, ConditionItem, ExceptionItem,
    SurvivalInfo, EvidenceSpan
)

class LegalIRBuilder:
    def __init__(self):
        # Section reference pattern: "Section 4", "Sections 3, 12, and 14"
        self.ref_regex = re.compile(r'\b(?:Sections?|Articles?|Clauses?)\s+([0-9IVXLCDM]+(?:,\s*(?:and\s*)?[0-9IVXLCDM]+)*)', re.IGNORECASE)
        
        # Condition patterns
        self.cond_regex = re.compile(
            r'(?:In the event of|Subject to|Contingent upon|Provided that|If)\s+([^,\.\n;]+)(?:,\s*([^\.\n;]+))?',
            re.IGNORECASE
        )
        
        # Exception patterns
        self.exc_regex = re.compile(
            r'(?:except\s+as|notwithstanding\s+any|unless\s+otherwise|without\s+giving\s+effect\s+to)\s+([^;\.\n]+)',
            re.IGNORECASE
        )

        # Modal action verbs
        self.action_split = re.compile(r'\b(shall\s+not|may\s+not|shall|must|agrees\s+to|will|is\s+required\s+to|hereby\s+employs|leases\s+to)\b', re.IGNORECASE)

    def build_legal_ir(
        self,
        clause_id: str,
        number: str,
        title: str,
        text: str,
        category: str,
        page_number: int = 1,
        line_start: int = 0,
        line_end: int = 0,
        fields: Optional[Dict[str, Any]] = None,
        full_doc_text: Optional[str] = None
    ) -> LegalIRClause:
        fields = fields or {}
        parties = fields.get("parties_involved", [])
        defined_terms = fields.get("defined_terms", [])
        monetary_amounts = fields.get("monetary_amounts", [])
        dates = fields.get("dates", [])
        raw_obligations = fields.get("obligations", [])

        # 1. Identity
        identity = ClauseIdentity(
            clause_id=clause_id,
            section=number or title or clause_id,
            page=page_number,
            line_start=line_start,
            line_end=line_end
        )

        # 2. Semantic
        semantic = ClauseSemantic(
            category=category,
            parties=parties,
            defined_terms=defined_terms,
            monetary_amounts=monetary_amounts,
            dates=dates
        )

        # 3. Obligations
        obligations = self._parse_obligations(raw_obligations, parties, dates, text)

        # 4. Conditions
        conditions = self._parse_conditions(text)

        # 5. Exceptions
        exceptions = self._parse_exceptions(text)

        # 6. References
        references = self._parse_references(text)

        # 7. Survival Info
        survival = self._parse_survival(text, references)

        # 8. Evidence Span
        evidence_span = self._parse_evidence_span(text, page_number, full_doc_text)

        return LegalIRClause(
            identity=identity,
            semantic=semantic,
            obligations=obligations,
            conditions=conditions,
            exceptions=exceptions,
            references=references,
            survival=survival,
            evidence_span=evidence_span,
            raw_text=text
        )

    def _parse_obligations(
        self,
        raw_obligations: List[str],
        parties: List[str],
        dates: List[str],
        text: str
    ) -> List[ObligationItem]:
        items: List[ObligationItem] = []
        source_texts = raw_obligations if raw_obligations else [s.strip() for s in text.splitlines() if len(s.strip()) > 20]

        for ob in source_texts:
            actor = "Party"
            for p in parties:
                if p.lower() in ob.lower():
                    actor = p
                    break

            match = self.action_split.search(ob)
            if match:
                action = match.group(1).strip()
                actor_part = ob[:match.start()].strip()
                object_part = ob[match.end():].strip()
                if actor_part and actor == "Party":
                    actor_candidate = actor_part.split()[-1]
                    if len(actor_candidate) > 2:
                        actor = actor_candidate
            else:
                action = "binding covenant"
                object_part = ob

            # Detect deadline
            deadline = None
            for d in dates:
                if d.lower() in ob.lower():
                    deadline = d
                    break

            items.append(ObligationItem(
                actor=actor,
                action=action,
                object=object_part[:180],
                deadline=deadline,
                original_text=ob[:250]
            ))

        return items[:6]

    def _parse_conditions(self, text: str) -> List[ConditionItem]:
        conditions = []
        for m in self.cond_regex.finditer(text):
            trigger = m.group(1).strip()
            consequence = m.group(2).strip() if m.group(2) else ""
            if len(trigger) > 5:
                conditions.append(ConditionItem(trigger=trigger[:120], consequence=consequence[:120]))
        return conditions[:4]

    def _parse_exceptions(self, text: str) -> List[ExceptionItem]:
        exceptions = []
        for m in self.exc_regex.finditer(text):
            desc = m.group(0).strip()
            if len(desc) > 8:
                exceptions.append(ExceptionItem(description=desc[:150]))
        return exceptions[:4]

    def _parse_references(self, text: str) -> List[str]:
        refs = []
        # Pattern 1: Lists of sections like "Sections 3 (Confidentiality), 12 (Non-Competition...), and 14 (...)"
        sec_block_match = re.search(r'\b(?:Sections?|Articles?|Clauses?)\s+([^;\.\n]+?)(?:shall|\.|\n|;)', text, re.IGNORECASE)
        if sec_block_match:
            block = sec_block_match.group(1)
            for num in re.findall(r'\b([0-9IVXLCDM]+(?:\.[0-9]+)*)\b', block):
                cid = f"SEC-{num}"
                if cid not in refs:
                    refs.append(cid)

        # Pattern 2: Individual "Section X" mentions throughout text
        for m in re.finditer(r'\b(?:Sections?|Articles?|Clauses?)\s+([0-9IVXLCDM]+(?:\.[0-9]+)*)', text, re.IGNORECASE):
            cid = f"SEC-{m.group(1)}"
            if cid not in refs:
                refs.append(cid)

        return refs

    def _parse_survival(self, text: str, references: List[str]) -> SurvivalInfo:
        text_low = text.lower()
        survives = False
        trigger = None
        surviving_clauses: List[str] = []
        duration = None

        if "survive" in text_low or "survival" in text_low:
            survives = True
            trigger = "termination or expiration"
            # If this clause specifies which provisions survive (like Sec 4(d))
            surviving_clauses = references

        if "following the termination" in text_low or "post-termination" in text_low:
            survives = True
            dur_match = re.search(r'(\d{1,2}\s+(?:months?|years?))\s+(?:post-termination|following\s+the\s+termination)', text, re.IGNORECASE)
            if dur_match:
                duration = dur_match.group(1)

        return SurvivalInfo(
            survives=survives,
            trigger=trigger,
            surviving_clauses=surviving_clauses,
            duration=duration
        )

    def _parse_evidence_span(self, text: str, page_number: int, full_doc_text: Optional[str]) -> EvidenceSpan:
        char_start = 0
        char_end = len(text)
        if full_doc_text and text:
            # Try to locate exact span
            idx = full_doc_text.find(text[:60])
            if idx != -1:
                char_start = idx
                char_end = idx + len(text)

        snippet = text[:100].replace('\n', ' ').strip()
        return EvidenceSpan(
            page=page_number,
            char_start=char_start,
            char_end=char_end,
            text_snippet=snippet
        )
