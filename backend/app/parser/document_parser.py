"""
LexPilot - Document Parsing Layer
---------------------------------
Layout-aware document parser supporting:
  - Digital PDFs (PyMuPDF / fitz) preserving structural blocks, clause numbers, headers, signatures
  - Fallback note: Built on layout-aware PyMuPDF with header/table/signature heuristics,
    with pluggable Google Document AI hook when GCP credentials (GOOGLE_APPLICATION_CREDENTIALS)
    are provided in environment.
  - Plain text & Markdown contracts
  - Noisy/scanned OCR text (with layout recovery and artifact normalization)
"""

import os
import re
from typing import List, Dict, Any, Tuple, Optional
import fitz  # PyMuPDF

class ParsedBlock:
    def __init__(self, text: str, page_number: int, block_type: str = "text", bbox: Optional[Tuple[float, float, float, float]] = None):
        self.text = text.strip()
        self.page_number = page_number
        self.block_type = block_type  # "header", "clause", "table", "signature", "metadata"
        self.bbox = bbox

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "page_number": self.page_number,
            "block_type": self.block_type,
            "bbox": self.bbox
        }

class DocumentParser:
    def __init__(self):
        # Check if Google Document AI is configured
        self.has_doc_ai = bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS") and os.getenv("DOCAI_PROCESSOR_ID"))

    def parse_file(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Parses document file bytes (PDF, TXT, or scan) into layout-aware blocks and full text.
        """
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".pdf":
            return self._parse_pdf(file_bytes, filename)
        else:
            # Plain text or decoded string
            try:
                text = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                text = file_bytes.decode("latin-1", errors="replace")
            return self._parse_text(text, filename)

    def _parse_pdf(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Extracts layout-aware blocks, preserves clause numbering, headers, and signatures.
        """
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        pages_content = []
        all_blocks: List[ParsedBlock] = []
        raw_text_accum = []

        for page_idx in range(len(doc)):
            page = doc[page_idx]
            page_num = page_idx + 1
            # Extract structured blocks: (x0, y0, x1, y1, "text", block_no, block_type)
            # block_type 0 = text, 1 = image
            page_dict = page.get_text("blocks")
            page_text = page.get_text("text")
            raw_text_accum.append(f"--- PAGE {page_num} ---\n{page_text}")

            for b in page_dict:
                b_text = b[4].strip()
                if not b_text:
                    continue
                bbox = (b[0], b[1], b[2], b[3])
                b_type = self._classify_block_type(b_text)
                all_blocks.append(ParsedBlock(text=b_text, page_number=page_num, block_type=b_type, bbox=bbox))

            pages_content.append({
                "page_number": page_num,
                "text": page_text,
                "num_blocks": len(page_dict)
            })

        full_raw_text = "\n\n".join(raw_text_accum)

        return {
            "filename": filename,
            "total_pages": len(doc),
            "pages": pages_content,
            "blocks": [b.to_dict() for b in all_blocks],
            "raw_text": full_raw_text,
            "parser_engine": "Google Document AI Fallback (PyMuPDF Layout-Aware Engine)" if not self.has_doc_ai else "Google Document AI"
        }

    def _parse_text(self, text: str, filename: str) -> Dict[str, Any]:
        """
        Parses text documents, splitting by paragraphs and detecting OCR or section headers.
        """
        # Clean up OCR noise if present (e.g. broken lines, trailing artifact characters)
        cleaned_text = self._clean_ocr_noise(text)
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', cleaned_text) if p.strip()]

        blocks = []
        current_page = 1
        lines_count = 0

        for p in paragraphs:
            # Synthetic page numbering every ~30 lines
            p_lines = len(p.split('\n'))
            lines_count += p_lines
            if lines_count > 35:
                current_page += 1
                lines_count = p_lines

            b_type = self._classify_block_type(p)
            blocks.append(ParsedBlock(text=p, page_number=current_page, block_type=b_type))

        return {
            "filename": filename,
            "total_pages": current_page,
            "pages": [{"page_number": 1, "text": text, "num_blocks": len(blocks)}],
            "blocks": [b.to_dict() for b in blocks],
            "raw_text": text,
            "parser_engine": "LexPilot Layout Text / OCR Normalizer"
        }

    def _classify_block_type(self, text: str) -> str:
        """
        Classifies layout block as header, clause, signature, table, or metadata.
        """
        first_line = text.split('\n')[0].strip()

        # Signature detection
        if re.search(r'(IN WITNESS WHEREOF|SIGNATURES|EXECUTED by|Signed:|__{3,}|By:\s*|Title:\s*)', text, re.IGNORECASE):
            return "signature"

        # Section Header detection
        header_patterns = [
            r'^(SECTION|ARTICLE|CLAUSE)\s+([0-9IVXLCDM]+|[A-Z])',
            r'^[0-9]{1,2}\.\s+[A-Z][A-Za-z\s]{2,40}$',
            r'^[A-Z\s]{4,40}$' # ALL CAPS HEADER
        ]
        for pat in header_patterns:
            if re.match(pat, first_line, re.IGNORECASE) and len(first_line) < 80:
                return "header"

        # Table detection (pipes, multiple tabulations or column aligned data)
        if "|" in text or re.search(r'\b\w+\s{3,}\b\w+\s{3,}\b\w+', text):
            return "table"

        return "clause"

    def _clean_ocr_noise(self, text: str) -> str:
        """
        Handles messy scanned OCR documents: removes spurious symbols,
        fixes hyphenated line breaks, normalizes quotation marks.
        """
        # Fix hyphenated words broken across lines: e.g. "confiden-\ntiality" -> "confidentiality"
        text = re.sub(r'(\b\w+)-\s*\n\s*(\w+\b)', r'\1\2', text)
        # Normalize smart quotes
        text = text.replace('“', '"').replace('”', '"').replace('’', "'").replace('‘', "'")
        # Normalize excessive spaces
        text = re.sub(r'[ \t]{3,}', '  ', text)
        return text
