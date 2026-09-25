"""
Utility to generate authentic sample PDF contracts with proper multi-page layout.
"""

import os
import pymupdf as fitz
from sample_data import SAMPLE_EMPLOYMENT_SCANNED, SAMPLE_LEASE_CONFLICT, SAMPLE_MSA_V1, SAMPLE_MSA_V2

def make_pdf(text: str, output_path: str, title: str):
    doc = fitz.open()
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

    margin_x = 50
    margin_y = 60
    page_width = 595
    page_height = 842
    max_y = page_height - 60

    page = doc.new_page(width=page_width, height=page_height)
    current_y = margin_y

    for p in paragraphs:
        # Measure height needed for this paragraph
        rect = fitz.Rect(margin_x, current_y, page_width - margin_x, max_y)
        # Check if we need a new page
        test_rc = page.insert_textbox(rect, p, fontsize=10, fontname="helv", align=fitz.TEXT_ALIGN_LEFT)
        if test_rc < 0:
            # New page needed
            page = doc.new_page(width=page_width, height=page_height)
            current_y = margin_y
            rect = fitz.Rect(margin_x, current_y, page_width - margin_x, max_y)
            # Insert on new page
            page.insert_textbox(rect, p, fontsize=10, fontname="helv", align=fitz.TEXT_ALIGN_LEFT)
        
        # Approximate line count and move y
        num_lines = max(1, len(p) // 75 + p.count('\n') + 1)
        current_y += (num_lines * 14) + 12
        if current_y > max_y - 40:
            page = doc.new_page(width=page_width, height=page_height)
            current_y = margin_y

    page_count = len(doc)
    doc.save(output_path)
    doc.close()
    print(f"Generated PDF with {page_count} pages: {output_path}")

if __name__ == "__main__":
    dir_path = os.path.dirname(os.path.abspath(__file__))
    make_pdf(SAMPLE_EMPLOYMENT_SCANNED, os.path.join(dir_path, "sample_employment_scanned.pdf"), "Employment Agreement")
    make_pdf(SAMPLE_LEASE_CONFLICT, os.path.join(dir_path, "sample_lease_conflict.pdf"), "Lease Agreement")
    make_pdf(SAMPLE_MSA_V1, os.path.join(dir_path, "sample_msa_v1.pdf"), "MSA Version 1")
    make_pdf(SAMPLE_MSA_V2, os.path.join(dir_path, "sample_msa_v2.pdf"), "MSA Version 2")
