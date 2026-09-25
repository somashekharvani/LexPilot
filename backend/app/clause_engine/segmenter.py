"""
LexPilot - Clause Engine: Segmenter
-----------------------------------
Segments layout blocks or raw text into distinct, identifiable legal clauses.
Preserves clause numbering, titles, page coordinates, and original text.
"""

import re
from typing import List, Dict, Any

class RawClause:
    def __init__(self, clause_id: str, number: str, title: str, text: str, page_number: int = 1, line_start: int = 0, line_end: int = 0):
        self.clause_id = clause_id
        self.number = number
        self.title = title
        self.text = text.strip()
        self.page_number = page_number
        self.line_start = line_start
        self.line_end = line_end

    def to_dict(self) -> Dict[str, Any]:
        return {
            "clause_id": self.clause_id,
            "number": self.number,
            "title": self.title,
            "text": self.text,
            "page_number": self.page_number,
            "line_start": self.line_start,
            "line_end": self.line_end
        }

class ClauseSegmenter:
    def __init__(self):
        # Patterns for section headers / clause numbering
        # e.g.:
        # "1. Term and Termination"
        # "Section 4.2. Notice Requirements"
        # "ARTICLE III - INDEMNIFICATION"
        # "4. PAYMENT TERMS"
        # "(a) Non-Compete Covenant"
        self.section_header_regex = re.compile(
            r'^(?:'
            r'(?:SECTION|ARTICLE|CLAUSE)\s+([0-9IVXLCDM]+(?:\.[0-9]+)*)[:\.\-\s]+([^\n\r]+)|'
            r'([0-9]{1,2}(?:\.[0-9]+)*)[\.\)]\s+([A-Z][^\n\r]+)|'
            r'([0-9]{1,2}(?:\.[0-9]+)*)\.\s*$'
            r')',
            re.IGNORECASE | re.MULTILINE
        )

    def segment(self, parsed_doc: Dict[str, Any]) -> List[RawClause]:
        """
        Segments parsed document into discrete clauses.
        Uses layout blocks if available, else falls back to line-by-line regex parsing.
        """
        raw_text = parsed_doc.get("raw_text", "")
        blocks = parsed_doc.get("blocks", [])

        clauses = self._segment_from_blocks(blocks)
        if len(clauses) >= 3:
            return clauses

        # Fallback to segmenting raw text
        return self._segment_from_raw_text(raw_text)

    def _segment_from_blocks(self, blocks: List[Dict[str, Any]]) -> List[RawClause]:
        clauses: List[RawClause] = []
        current_num = ""
        current_title = ""
        current_text_parts = []
        current_page = 1
        clause_counter = 1
        line_cursor = 0

        for b in blocks:
            text = b["text"]
            b_type = b.get("block_type", "clause")
            page_num = b.get("page_number", 1)

            # Check if this block starts a new clause
            first_line = text.split('\n')[0].strip()
            match = self.section_header_regex.search(first_line)

            is_header = b_type == "header" or (match is not None and len(first_line) < 90)

            if is_header:
                # Flush existing clause
                if current_text_parts:
                    full_text = "\n\n".join(current_text_parts).strip()
                    cid = f"SEC-{current_num if current_num else clause_counter}"
                    clauses.append(RawClause(
                        clause_id=cid,
                        number=current_num or f"{clause_counter}",
                        title=current_title or f"Section {clause_counter}",
                        text=full_text,
                        page_number=current_page,
                        line_start=line_cursor - len(current_text_parts),
                        line_end=line_cursor
                    ))
                    clause_counter += 1
                    current_text_parts = []

                # Extract number and title from header
                num, title = self._extract_header_info(first_line)
                current_num = num
                current_title = title
                current_page = page_num

                # If block has body text following the header line
                body_lines = text.split('\n')[1:]
                if body_lines:
                    current_text_parts.append("\n".join(body_lines).strip())
            else:
                if not current_title and clause_counter == 1:
                    # Preamble / recitals
                    current_title = "Preamble & Recitals"
                    current_num = "0"
                current_text_parts.append(text)

            line_cursor += len(text.split('\n'))

        # Flush final clause
        if current_text_parts:
            full_text = "\n\n".join(current_text_parts).strip()
            cid = f"SEC-{current_num if current_num else clause_counter}"
            clauses.append(RawClause(
                clause_id=cid,
                number=current_num or f"{clause_counter}",
                title=current_title or f"Section {clause_counter}",
                text=full_text,
                page_number=current_page,
                line_start=line_cursor - len(current_text_parts),
                line_end=line_cursor
            ))

        return clauses

    def _segment_from_raw_text(self, raw_text: str) -> List[RawClause]:
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', raw_text) if p.strip()]
        clauses: List[RawClause] = []
        clause_counter = 1

        for p in paragraphs:
            first_line = p.split('\n')[0].strip()
            num, title = self._extract_header_info(first_line)
            cid = f"SEC-{num if num else clause_counter}"
            clauses.append(RawClause(
                clause_id=cid,
                number=num or f"{clause_counter}",
                title=title or f"Section {clause_counter}",
                text=p,
                page_number=1,
                line_start=0,
                line_end=len(p.split('\n'))
            ))
            clause_counter += 1

        return clauses

    def _extract_header_info(self, line: str) -> tuple[str, str]:
        # Try Section X. Title
        m = re.match(r'^(?:SECTION|ARTICLE|CLAUSE)\s+([0-9IVXLCDM]+(?:\.[0-9]+)*)[:\.\-\s]+([^\n\r]+)', line, re.IGNORECASE)
        if m:
            return m.group(1).strip(), m.group(2).strip()

        # Try "1.2 Title" or "1. Title"
        m = re.match(r'^([0-9]{1,2}(?:\.[0-9]+)*)[\.\)]\s+([^\n\r]+)', line)
        if m:
            return m.group(1).strip(), m.group(2).strip()

        # Try ALL CAPS Title
        if line.isupper() and len(line) < 60:
            return "", line.title()

        return "", line[:40]
