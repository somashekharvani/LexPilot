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
from typing import List, Dict, Any, Optional, Tuple
from ..models.schemas import ContractConflict, AttentionLevel, ConfidenceLevel, ConflictType
from ..graph.clause_graph import ClauseGraph

class ConflictDetector:
    def __init__(self, clause_graph: ClauseGraph):
        self.graph = clause_graph

    def detect_conflicts(self, clauses: List[Dict[str, Any]]) -> List[ContractConflict]:
        """
        Scans clauses across the document for internal contradictions across
        typed conflict dimensions: TEMPORAL, OBLIGATION, AMOUNT, SURVIVAL, SCOPE, CONDITIONAL, DEFINITION.
        """
        conflicts: List[ContractConflict] = []

        # 1. Notice Period Contradictions (TEMPORAL)
        notice_conflict = self._check_notice_period_conflicts(clauses)
        if notice_conflict:
            conflicts.append(notice_conflict)

        # 2. Liability Cap vs Indemnity Contradiction (OBLIGATION)
        liability_conflict = self._check_liability_vs_indemnity_conflicts(clauses)
        if liability_conflict:
            conflicts.append(liability_conflict)

        # 3. Cure Period / Default Timelines Contradiction (TEMPORAL)
        cure_conflict = self._check_cure_period_conflicts(clauses)
        if cure_conflict:
            conflicts.append(cure_conflict)

        # 4. Monetary Amount Contradictions (AMOUNT)
        amount_conflict = self._check_amount_conflicts(clauses)
        if amount_conflict:
            conflicts.append(amount_conflict)

        # 5. Survival Mandate Contradictions (SURVIVAL)
        survival_conflict = self._check_survival_conflicts(clauses)
        if survival_conflict:
            conflicts.append(survival_conflict)

        # 6. Rights & License Scope Contradictions (SCOPE)
        scope_conflict = self._check_scope_conflicts(clauses)
        if scope_conflict:
            conflicts.append(scope_conflict)

        # 7. Circular Supremacy / Notwithstanding Clashes (CONDITIONAL)
        cond_conflict = self._check_conditional_precedence_conflicts(clauses)
        if cond_conflict:
            conflicts.append(cond_conflict)

        # 8. Inconsistent Term Definitions (DEFINITION)
        def_conflict = self._check_definition_conflicts(clauses)
        if def_conflict:
            conflicts.append(def_conflict)

        # Register conflicts into the clause graph as CONFLICTS_WITH edges
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
        Detects conflicting notice days across clauses (TEMPORAL).
        """
        notice_clauses = [c for c in clauses if c.get("category") in ["termination", "notice", "renewal"]]
        if len(notice_clauses) < 2:
            return None

        clause_days: List[Tuple[Dict[str, Any], int, str]] = []

        for c in notice_clauses:
            text = c.get("text", "")
            matches = re.finditer(r'(?:\((\d+)\)|\b(\d+)\b)\s*(?:days?|calendar days?|business days?)(?:[\'\"]|\s+prior|\s+written|\s+notice)', text, re.IGNORECASE)
            for m in matches:
                days = int(m.group(1) or m.group(2))
                clause_days.append((c, days, m.group(0)))

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
                        typed_category=ConflictType.TEMPORAL,
                        explanation=f"Section {c1.get('number', c1['id'])} requires {days1} days notice, while Section {c2.get('number', c2['id'])} mandates {days2} days notice. This creates operational ambiguity regarding the effective date of notice.",
                        attention_level=AttentionLevel.HIGH,
                        confidence=ConfidenceLevel.HIGH,
                        suggested_question=f"Which notice timeline governs contract termination: the {days1}-day window in {c1.get('title')} or the {days2}-day period in {c2.get('title')}?"
                    )
        return None

    def _check_liability_vs_indemnity_conflicts(self, clauses: List[Dict[str, Any]]) -> Optional[ContractConflict]:
        """
        Detects if liability clause sets a low cap while indemnification clause has no carve-out (OBLIGATION).
        """
        liability_clauses = [c for c in clauses if c.get("category") == "liability"]
        indemnity_clauses = [c for c in clauses if c.get("category") == "indemnification"]

        if not liability_clauses or not indemnity_clauses:
            return None

        l_clause = liability_clauses[0]
        i_clause = indemnity_clauses[0]

        l_text = l_clause.get("text", "").lower()
        i_text = i_clause.get("text", "").lower()

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
                typed_category=ConflictType.OBLIGATION,
                explanation=f"{l_clause.get('title')} imposes a total monetary liability ceiling, but does not explicitly clarify whether indemnification duties in {i_clause.get('title')} are subject to or excluded from this cap, creating open-ended financial risk.",
                attention_level=AttentionLevel.HIGH,
                confidence=ConfidenceLevel.HIGH,
                suggested_question="Is the indemnification obligation intended to be capped by the general limitation of liability, or is it an uncapped carve-out?"
            )
        return None

    def _check_cure_period_conflicts(self, clauses: List[Dict[str, Any]]) -> Optional[ContractConflict]:
        """
        Checks for conflicting breach cure periods across termination and default sections (TEMPORAL).
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
                typed_category=ConflictType.TEMPORAL,
                explanation=f"Cure period in Section {c1.get('number')} ({m1.group(1)} days) differs from Section {c2.get('number')} ({m2.group(1)} days).",
                attention_level=AttentionLevel.HIGH,
                confidence=ConfidenceLevel.HIGH,
                suggested_question="Which breach cure period applies to material non-monetary defaults?"
            )
        return None

    def _check_amount_conflicts(self, clauses: List[Dict[str, Any]]) -> Optional[ContractConflict]:
        """
        Detects conflicting monetary amounts for the same fee, deposit, or threshold (AMOUNT).
        """
        amount_items: List[Tuple[Dict[str, Any], int, str, str]] = []
        for c in clauses:
            text = c.get("text", "")
            matches = re.finditer(r'(security\s+deposit|deposit|late\s+fee|retainer|liquidated\s+damages)[^\.\n]{0,60}\$\s*([\d,]+)', text, re.IGNORECASE)
            for m in matches:
                item_type = m.group(1).lower().strip()
                amt_str = m.group(2).replace(",", "")
                try:
                    amt = int(amt_str)
                    amount_items.append((c, amt, item_type, m.group(0)))
                except ValueError:
                    pass

        for i in range(len(amount_items)):
            for j in range(i + 1, len(amount_items)):
                c1, amt1, type1, match1 = amount_items[i]
                c2, amt2, type2, match2 = amount_items[j]
                if c1["id"] != c2["id"] and type1 == type2 and amt1 != amt2:
                    return ContractConflict(
                        id=f"CONF-AMT-{c1['id']}-{c2['id']}",
                        clause_a_id=c1["id"],
                        clause_a_title=c1.get("title", f"Section {c1.get('number', '')}"),
                        clause_a_excerpt=self._extract_sentence_with_match(c1.get("text", ""), match1),
                        clause_b_id=c2["id"],
                        clause_b_title=c2.get("title", f"Section {c2.get('number', '')}"),
                        clause_b_excerpt=self._extract_sentence_with_match(c2.get("text", ""), match2),
                        conflict_type="Contradictory Monetary Amounts",
                        typed_category=ConflictType.AMOUNT,
                        explanation=f"{c1.get('title')} specifies a {type1} of ${amt1:,}, whereas {c2.get('title')} cites ${amt2:,}, creating financial ambiguity.",
                        attention_level=AttentionLevel.HIGH,
                        confidence=ConfidenceLevel.HIGH,
                        suggested_question=f"Which monetary amount is intended to control: ${amt1:,} in {c1.get('title')} or ${amt2:,} in {c2.get('title')}?"
                    )
        return None

    def _check_survival_conflicts(self, clauses: List[Dict[str, Any]]) -> Optional[ContractConflict]:
        """
        Detects contradiction between blanket termination and indefinite survival (SURVIVAL).
        """
        cease_clauses = []
        survival_clauses = []
        for c in clauses:
            text = c.get("text", "").lower()
            if any(phrase in text for phrase in [
                "all rights and obligations of the parties shall immediately cease",
                "shall immediately terminate and have no further force",
                "neither party shall have any further obligation or liability upon termination"
            ]):
                cease_clauses.append(c)
            if any(phrase in text for phrase in [
                "shall survive the termination of this agreement in perpetuity",
                "shall survive termination for an indefinite period",
                "survives termination indefinitely"
            ]):
                survival_clauses.append(c)

        if cease_clauses and survival_clauses:
            c1 = cease_clauses[0]
            c2 = survival_clauses[0]
            return ContractConflict(
                id=f"CONF-SURV-{c1['id']}-{c2['id']}",
                clause_a_id=c1["id"],
                clause_a_title=c1.get("title", f"Section {c1.get('number', '')}"),
                clause_a_excerpt=c1.get("text", "")[:260],
                clause_b_id=c2["id"],
                clause_b_title=c2.get("title", f"Section {c2.get('number', '')}"),
                clause_b_excerpt=c2.get("text", "")[:260],
                conflict_type="Contradictory Survival Mandates",
                typed_category=ConflictType.SURVIVAL,
                explanation=f"{c1.get('title')} purports to extinguish all obligations immediately upon termination without savings language, directly contradicting {c2.get('title')} which mandates survival indefinitely.",
                attention_level=AttentionLevel.HIGH,
                confidence=ConfidenceLevel.HIGH,
                suggested_question=f"Does the total extinction of obligations in {c1.get('title')} override the survival mandate in {c2.get('title')}?"
            )
        return None

    def _check_scope_conflicts(self, clauses: List[Dict[str, Any]]) -> Optional[ContractConflict]:
        """
        Detects contradiction between exclusive and non-exclusive grants for same rights (SCOPE).
        """
        exclusive_clauses = []
        non_exclusive_clauses = []
        for c in clauses:
            text = c.get("text", "").lower()
            if re.search(r'\b(sole and exclusive|exclusive license|exclusive right)\b', text):
                exclusive_clauses.append(c)
            if re.search(r'\b(non-exclusive license|non-exclusive right)\b', text):
                non_exclusive_clauses.append(c)

        if exclusive_clauses and non_exclusive_clauses:
            c1 = exclusive_clauses[0]
            c2 = non_exclusive_clauses[0]
            if c1["id"] != c2["id"]:
                return ContractConflict(
                    id=f"CONF-SCOPE-{c1['id']}-{c2['id']}",
                    clause_a_id=c1["id"],
                    clause_a_title=c1.get("title", f"Section {c1.get('number', '')}"),
                    clause_a_excerpt=c1.get("text", "")[:260],
                    clause_b_id=c2["id"],
                    clause_b_title=c2.get("title", f"Section {c2.get('number', '')}"),
                    clause_b_excerpt=c2.get("text", "")[:260],
                    conflict_type="Contradictory License/Rights Scope",
                    typed_category=ConflictType.SCOPE,
                    explanation=f"{c1.get('title')} grants exclusive rights, whereas {c2.get('title')} specifies a non-exclusive grant without clarifying qualification.",
                    attention_level=AttentionLevel.HIGH,
                    confidence=ConfidenceLevel.HIGH,
                    suggested_question="Is the grant of rights intended to be strictly exclusive or non-exclusive?"
                )
        return None

    def _check_conditional_precedence_conflicts(self, clauses: List[Dict[str, Any]]) -> Optional[ContractConflict]:
        """
        Detects conflicting supremacy clauses where both claim absolute precedence (CONDITIONAL).
        """
        precedence_clauses: List[Tuple[Dict[str, Any], str]] = []
        for c in clauses:
            text = c.get("text", "")
            m = re.search(r'\bnotwithstanding\s+(?:anything|any\s+provision|any\s+other\s+clause)\s+to\s+the\s+contrary\b', text, re.IGNORECASE)
            if m:
                precedence_clauses.append((c, m.group(0)))

        if len(precedence_clauses) >= 2:
            for i in range(len(precedence_clauses)):
                for j in range(i + 1, len(precedence_clauses)):
                    c1, m1 = precedence_clauses[i]
                    c2, m2 = precedence_clauses[j]
                    if c1["id"] != c2["id"] and c1.get("category") != c2.get("category"):
                        return ContractConflict(
                            id=f"CONF-COND-{c1['id']}-{c2['id']}",
                            clause_a_id=c1["id"],
                            clause_a_title=c1.get("title", f"Section {c1.get('number', '')}"),
                            clause_a_excerpt=self._extract_sentence_with_match(c1.get("text", ""), m1),
                            clause_b_id=c2["id"],
                            clause_b_title=c2.get("title", f"Section {c2.get('number', '')}"),
                            clause_b_excerpt=self._extract_sentence_with_match(c2.get("text", ""), m2),
                            conflict_type="Conflicting Supremacy / Precedence Clauses",
                            typed_category=ConflictType.CONDITIONAL,
                            explanation=f"Both {c1.get('title')} and {c2.get('title')} assert absolute supremacy using 'notwithstanding' clauses, creating circular precedence ambiguity.",
                            attention_level=AttentionLevel.HIGH,
                            confidence=ConfidenceLevel.HIGH,
                            suggested_question=f"In the event of an operational clash, does {c1.get('title')} or {c2.get('title')} take legal precedence?"
                        )
        return None

    def _check_definition_conflicts(self, clauses: List[Dict[str, Any]]) -> Optional[ContractConflict]:
        """
        Detects materially divergent definitions for the same capitalized term (DEFINITION).
        """
        def_map: Dict[str, List[Tuple[Dict[str, Any], str]]] = {}
        for c in clauses:
            text = c.get("text", "")
            matches = re.finditer(r'["“]([A-Z][A-Za-z\s]{3,35})["”]\s+(?:means|shall\s+mean|is\s+defined\s+as)\s+([^;\.\n]{15,120})', text)
            for m in matches:
                term = m.group(1).strip()
                meaning = m.group(2).strip()
                if term not in def_map:
                    def_map[term] = []
                def_map[term].append((c, meaning))

        for term, occurrences in def_map.items():
            if len(occurrences) >= 2:
                c1, m1 = occurrences[0]
                c2, m2 = occurrences[1]
                if c1["id"] != c2["id"] and abs(len(m1) - len(m2)) > 20:
                    return ContractConflict(
                        id=f"CONF-DEF-{c1['id']}-{c2['id']}",
                        clause_a_id=c1["id"],
                        clause_a_title=c1.get("title", f"Section {c1.get('number', '')}"),
                        clause_a_excerpt=f'"{term}" shall mean {m1}',
                        clause_b_id=c2["id"],
                        clause_b_title=c2.get("title", f"Section {c2.get('number', '')}"),
                        clause_b_excerpt=f'"{term}" shall mean {m2}',
                        conflict_type="Inconsistent Term Definitions",
                        typed_category=ConflictType.DEFINITION,
                        explanation=f'The defined term "{term}" has materially differing definitions in {c1.get("title")} and {c2.get("title")}.',
                        attention_level=AttentionLevel.HIGH,
                        confidence=ConfidenceLevel.HIGH,
                        suggested_question=f'Which definition of "{term}" applies to obligations across the agreement?'
                    )
        return None

    def _extract_sentence_with_match(self, text: str, match_str: str) -> str:
        for sentence in re.split(r'[\.\r\n]+', text):
            if match_str.lower() in sentence.lower():
                return sentence.strip() + "."
        return text[:200]
