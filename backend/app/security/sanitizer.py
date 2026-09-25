"""
LexPilot - Security & Input Sanitization Module
-----------------------------------------------
Provides robust protection against:
  - Path traversal and malicious filenames
  - Oversized payloads and Denial of Service (DoS)
  - Spoofed MIME types & file extension bypasses (Magic Byte validation)
  - LLM Prompt Injection & Jailbreaks
  - Sensitive Data / PII leakage (SSN, credit card, phone redaction)
"""

import re
import os
from typing import Tuple, List

# Allowed upload file extensions
ALLOWED_EXTENSIONS = frozenset({".pdf", ".txt", ".doc", ".docx"})

# Maximum allowed upload size (10 MB in bytes)
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

# PDF Magic Bytes (%PDF-)
PDF_MAGIC_BYTES = b"%PDF-"

# Prompt injection / jailbreak detection patterns
PROMPT_INJECTION_PATTERNS = [
    re.compile(r'\b(ignore\s+(all\s+)?(previous|prior)\s+instructions?)\b', re.IGNORECASE),
    re.compile(r'\b(system\s+override|developer\s+mode|dan\s+mode)\b', re.IGNORECASE),
    re.compile(r'\b(reveal\s+(your\s+)?(system\s+prompt|secret\s+key|api\s+key))\b', re.IGNORECASE),
    re.compile(r'\b(disregard\s+(all\s+)?(safety|rules|constraints))\b', re.IGNORECASE),
    re.compile(r'\b(you\s+are\s+now\s+an\s+unfiltered|jailbreak)\b', re.IGNORECASE),
    re.compile(r'<script\b[^>]*>([\s\S]*?)<\/script>', re.IGNORECASE),
    re.compile(r'javascript:', re.IGNORECASE),
]

# PII Redaction patterns
SSN_REGEX = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
CREDIT_CARD_REGEX = re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b')
EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
PHONE_REGEX = re.compile(r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b')


def sanitize_filename(filename: str) -> str:
    """
    Sanitizes filenames to prevent directory traversal and special character attacks.
    Strips directory separators, null bytes, and non-whitelisted characters.
    """
    if not filename:
        return "unnamed_document.txt"

    # Remove path components (POSIX and Windows)
    basename = os.path.basename(filename.replace("\\", "/"))
    # Remove null bytes
    basename = basename.replace("\x00", "")
    # Remove traversal sequences
    basename = re.sub(r'\.{2,}', '.', basename)
    # Whitelist alphanumeric, underscore, hyphen, space, dot, parentheses
    clean_name = re.sub(r'[^a-zA-Z0-9_\-\.\s\(\)]', '_', basename).strip()

    # Limit filename length
    if len(clean_name) > 120:
        base, ext = os.path.splitext(clean_name)
        clean_name = base[:110] + ext

    return clean_name or "document.txt"


def validate_file_upload(file_bytes: bytes, filename: str) -> Tuple[bool, str]:
    """
    Validates file payload size, extension, and magic bytes.
    Returns (is_valid, error_message).
    """
    if not file_bytes or len(file_bytes) == 0:
        return False, "Uploaded file is empty."

    if len(file_bytes) > MAX_UPLOAD_BYTES:
        return False, f"File size ({len(file_bytes) / (1024*1024):.1f} MB) exceeds maximum allowed limit of 10 MB."

    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"File extension '{ext}' is not supported. Supported extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}."

    # Validate PDF magic bytes
    if ext == ".pdf":
        if not file_bytes.startswith(PDF_MAGIC_BYTES):
            return False, "File possesses a .pdf extension but lacks valid PDF magic byte header (%PDF-)."

    return True, ""


def check_prompt_injection(query: str) -> Tuple[bool, str]:
    """
    Scans queries for known prompt injection, jailbreak attempts, or malicious script tags.
    Returns (is_safe, refusal_reason).
    """
    if not query:
        return True, ""

    for pat in PROMPT_INJECTION_PATTERNS:
        if pat.search(query):
            return False, "Query contains restricted instruction overrides or potential prompt injection patterns."

    return True, ""


def mask_pii(text: str) -> str:
    """
    Redacts personally identifiable information (SSNs, credit cards, emails, phone numbers)
    from legal text before processing or logging.
    """
    if not text:
        return ""

    masked = SSN_REGEX.sub("[REDACTED_SSN]", text)
    masked = CREDIT_CARD_REGEX.sub("[REDACTED_CARD]", masked)
    masked = EMAIL_REGEX.sub("[REDACTED_EMAIL]", masked)
    masked = PHONE_REGEX.sub("[REDACTED_PHONE]", masked)
    return masked
