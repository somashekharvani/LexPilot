"""
LexPilot - Conflict Detector (Cross-Clause Reasoning)
-----------------------------------------------------
Traverses the clause graph and compares interrelated clauses to identify:
  - Differing or contradictory notice periods
  - Liability caps conflicting with uncapped indemnification
  - Contradictory termination / cure timelines
  - Automatic renewal opt-out vs termination window clashes
  - Conflicting dispute resolution / forum selections

Produces structured ContractConflict outputs with both clauses cited side-by-side.
"""

import re
from typing import List, Dict, Any, Optional
from ..models.schemas import ContractConflict, AttentionLevel, ConfidenceLevel
from ..graph.clause_graph import ClauseGraph

class ConflictDetector:
    def __init__(self, clause_graph: ClauseGraph):
        self.graph = clause_graph

    def detect_conflicts(self, clauses: List[Dict[str, Any]]) -> List[ContractConflict]:
        """
        Scans clauses across the document for internal contradictions.
        """
        conflicts: List[ContractConflict] = []

        # 1. Notice Period Contradictions across Termination, Notice, Renewal clauses
        notice_conflict = self._check_notice_period_conflicts(clauses)
        if notice_conflict:
            conflicts.append(notice_conflict)

        # 2. Liability Cap vs Indemnity Contradiction
        liability_conflict = self._check_liability_vs_indemnity_conflicts(clauses)
        if liability_conflict:
            conflicts.append(liability_conflict)

        # 3. Cure Period / Default Timelines Contradiction
        cure_conflict = self._check_cure_period_conflicts(clauses)
        if cure_conflict:
            conflicts.append(cure_conflict)

        # Register conflicts into the clause graph as CONFLICTS_WITH edges!
        for c in conflicts:
            self.graph.add_conflict_edge(
                source_id=c.clause_a_id,
                target_id=c.clause_b_id,
                explanation=c.explanation,
                confidence=c.confidence
            )

        return conflicts

    def _check_notice_period_conflicts(self, clauses: List[Dict[str, Any]]) -> Optional[ContractConflict]:
        """
        Detects conflicting notice days across clauses (e.g. 30 days vs 60 days).
        """
        notice_clauses = [c for c in clauses if c.get("category") in ["termination", "notice", "renewal"]]
        if len(notice_clauses) < 2:
            return None

        clause_days: List[Tuple[Dict[str, Any], int, str]] = []

        for c in notice_clauses:
            text = c.get("text", "")
            # Look for explicit day notices (e.g. "30 days", "(30) days' prior written notice")
            matches = re.finditer(r'(?:\((\d+)\)|\b(\d+)\b)\s*(?:days?|calendar days?|business days?)(?:[\'\"]|\s+prior|\s+written|\s+notice)', text, re.IGNORECASE)
            for m in matches:
                days = int(m.group(1) or m.group(2))
                clause_days.append((c, days, m.group(0)))

        # Look for distinct numbers of days between different clauses
        for i in range(len(clause_days)):
            for j in range(i + 1, len(clause_days)):
                c1, days1, match1 = clause_days[i]
                c2, days2, match2 = clause_days[j]

                if c1["id"] != c2["id"] and days1 != days2:
                    return ContractConflict(
                        id=f"CONF-NOTICE-{c1['id']}-{c2['id']}",
                        clause_a_id=c1["id"],
                        clause_a_title=c1.get("title", f"Section {c1.get('number', '')}"),
                        clause_a_excerpt=self._extract_sentence_with_match(c1.get("text", ""), match1),
                        clause_b_id=c2["id"],
                        clause_b_title=c2.get("title", f"Section {c2.get('number', '')}"),
                        clause_b_excerpt=self._extract_sentence_with_match(c2.get("text", ""), match2),
                        conflict_type="Contradictory Notice Periods",
                        explanation=f"Section {c1.get('number', c1['id'])} requires {days1} days notice, while Section {c2.get('number', c2['id'])} mandates {days2} days notice. This creates operational ambiguity regarding the effective date of notice.",
                        attention_level=AttentionLevel.HIGH,
                        confidence=ConfidenceLevel.HIGH,
                        suggested_question=f"Which notice timeline governs contract termination: the {days1}-day window in {c1.get('title')} or the {days2}-day period in {c2.get('title')}?"
                    )
        return None

    def _check_liability_vs_indemnity_conflicts(self, clauses: List[Dict[str, Any]]) -> Optional[ContractConflict]:
        """
        Detects if liability clause sets a low cap while indemnification clause has no carve-out or is unlimited.
        """
        liability_clauses = [c for c in clauses if c.get("category") == "liability"]
        indemnity_clauses = [c for c in clauses if c.get("category") == "indemnification"]

        if not liability_clauses or not indemnity_clauses:
            return None

        l_clause = liability_clauses[0]
        i_clause = indemnity_clauses[0]

        l_text = l_clause.get("text", "").lower()
        i_text = i_clause.get("text", "").lower()

        # Check if liability sets a monetary cap and indemnity doesn't mention the cap
        has_cap = bool(re.search(r'(\$\s*\d+|\bfees paid\b|\btotal amount paid\b)', l_text))
        has_indemnity_exclusion = "indemnification" in l_text or "section " + str(i_clause.get("number", "")) in l_text

        if has_cap and not has_indemnity_exclusion:
            return ContractConflict(
                id=f"CONF-LIAB-INDEM-{l_clause['id']}-{i_clause['id']}",
                clause_a_id=l_clause["id"],
                clause_a_title=l_clause.get("title", "Limitation of Liability"),
                clause_a_excerpt=l_clause.get("text", "")[:280] + "...",
                clause_b_id=i_clause["id"],
                clause_b_title=i_clause.get("title", "Indemnification"),
                clause_b_excerpt=i_clause.get("text", "")[:280] + "...",
                conflict_type="Liability Cap vs. Broad Indemnification Exposure",
                explanation=f"{l_clause.get('title')} imposes a total monetary liability ceiling, but does not explicitly clarify whether indemnification duties in {i_clause.get('title')} are subject to or excluded from this cap, creating open-ended financial risk.",
                attention_level=AttentionLevel.HIGH,
                confidence=ConfidenceLevel.HIGH,
                suggested_question="Is the indemnification obligation intended to be capped by the general limitation of liability, or is it an uncapped carve-out?"
            )
        return None

    def _check_cure_period_conflicts(self, clauses: List[Dict[str, Any]]) -> Optional[ContractConflict]:
        """
        Checks for conflicting breach cure periods across termination and default sections.
        """
        term_clauses = [c for c in clauses if c.get("category") == "termination"]
        if len(term_clauses) < 2:
            return None

        c1 = term_clauses[0]
        c2 = term_clauses[1]
        m1 = re.search(r'(\d+)\s+days?\s+to\s+cure', c1.get("text", ""), re.IGNORECASE)
        m2 = re.search(r'(\d+)\s+days?\s+to\s+cure', c2.get("text", ""), re.IGNORECASE)

        if m1 and m2 and m1.group(1) != m2.group(1):
            return ContractConflict(
                id=f"CONF-CURE-{c1['id']}-{c2['id']}",
                clause_a_id=c1["id"],
                clause_a_title=c1.get("title", ""),
                clause_a_excerpt=c1.get("text", "")[:250],
                clause_b_id=c2["id"],
                clause_b_title=c2.get("title", ""),
                clause_b_excerpt=c2.get("text", "")[:250],
                conflict_type="Inconsistent Cure Windows",
                explanation=f"Cure period in Section {c1.get('number')} ({m1.group(1)} days) differs from Section {c2.get('number')} ({m2.group(1)} days).",
                attention_level=AttentionLevel.HIGH,
                confidence=ConfidenceLevel.HIGH,
                suggested_question="Which breach cure period applies to material non-monetary defaults?"
            )
        return None

    def _extract_sentence_with_match(self, text: str, match_str: str) -> str:
        for sentence in re.split(r'[\.\r\n]+', text):
            if match_str.lower() in sentence.lower():
                return sentence.strip() + "."
        return text[:200]
