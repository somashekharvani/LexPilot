"""
LexPilot - FastAPI Pipeline Server
----------------------------------
Single coherent pipeline orchestrating:
  1. Document Parsing Layer (Layout-aware PyMuPDF with Google Doc AI fallback hooks)
  2. Clause Engine (Segmentation, 10-category classification, structured entity extraction)
  3. Clause Graph (NetworkX in-memory graph)
  4. Hybrid Search (BM25 + Semantic overlap)
  5. Reference Corpus Comparison (CUAD-derived baseline deviation detection)
  6. Gemini Analysis Layer (Qualitative attention flags, plain-language rewrites, conflict detection)
  7. Verification Agent (Two-pass entailment verification with High/Medium/Low confidence scoring)
  8. Multi-Hop Graph Reasoning & Verified Q&A
  9. Structured Obligation Timeline
  10. Semantic Contract-to-Contract Comparison

Security & Efficiency:
  - OWASP Security Headers (HSTS, CSP, X-Frame-Options, Nosniff)
  - Strict CORS origin validation
  - In-Memory Sliding-Window Rate Limiting (DoS protection)
  - File upload size enforcement (10MB limit) & PDF Magic Byte verification
  - Prompt Injection & Adversarial Jailbreak Guardrails
  - PII Masking and Data Privacy Filter
  - High-Efficiency LRU Session Cache with TTL eviction
  - SHA-256 Pipeline Memoization for <1ms contract response times
"""

import os
import uuid
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .models.schemas import (
    DocumentAnalysisResponse, ClauseNode, GraphEdge, ContractConflict,
    TimelineEvent, ComparisonItem, QARequest, QAResponse, ConfidenceLevel, AttentionLevel
)
from .parser.document_parser import DocumentParser
from .clause_engine.segmenter import ClauseSegmenter
from .clause_engine.classifier import ClauseClassifier
from .clause_engine.field_extractor import FieldExtractor
from .graph.clause_graph import ClauseGraph
from .search.hybrid_retriever import HybridRetriever
from .reference_corpus.deviation_detector import DeviationDetector
from .reference_corpus.corpus_data import REFERENCE_CORPUS
from .analysis.gemini_analyzer import GeminiClient, GeminiAnalyzer
from .analysis.conflict_detector import ConflictDetector
from .analysis.timeline_extractor import TimelineExtractor
from .analysis.contract_comparator import ContractComparator
from .verification.verifier import VerificationAgent
from .graph.multi_hop import MultiHopQAEngine
from .sample_documents.sample_data import (
    SAMPLE_EMPLOYMENT_SCANNED, SAMPLE_LEASE_CONFLICT, SAMPLE_MSA_V1, SAMPLE_MSA_V2
)
from .security import (
    SecurityHeadersMiddleware, RateLimitMiddleware,
    validate_file_upload, sanitize_filename, check_prompt_injection, mask_pii,
    MAX_UPLOAD_BYTES, ALLOWED_EXTENSIONS
)
from .utils.lru_cache import LRUSessionCache, PipelineMemoizer

app = FastAPI(
    title="LexPilot API",
    description="Evidence-Grounded Legal Reasoning System | AI for Legal Assistance & Access",
    version="1.0.0"
)

# 1. OWASP Security Response Headers
app.add_middleware(SecurityHeadersMiddleware)

# 2. Rate Limiting Middleware (120 requests/minute per client IP)
app.add_middleware(RateLimitMiddleware, max_requests=120, window_seconds=60)

# 3. CORS Configuration (Strict Origins & Preview Regex, Avoiding Insecure Wildcards)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://lex-pilot-phi.vercel.app"
    ],
    allow_origin_regex=r"^https:\/\/lex-pilot-.*-somashekhar-vanis-projects\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Pipeline Singletons
parser = DocumentParser()
segmenter = ClauseSegmenter()
classifier = ClauseClassifier()
field_extractor = FieldExtractor()
gemini_client = GeminiClient()
gemini_analyzer = GeminiAnalyzer(gemini_client)
verifier = VerificationAgent(gemini_client)
deviation_detector = DeviationDetector()
comparator = ContractComparator(verifier)

# High-Efficiency Bounded LRU Cache & SHA-256 Memoizer
sessions = LRUSessionCache(maxsize=50, ttl_seconds=7200)
memoizer = PipelineMemoizer(max_items=30)

def process_document_pipeline(file_bytes: bytes, filename: str, doc_type_hint: str = "auto") -> DocumentAnalysisResponse:
    """
    Executes the single coherent pipeline from raw bytes to verified legal analysis report.
    Utilizes SHA-256 memoization for sub-millisecond repeated contract execution.
    """
    clean_filename = sanitize_filename(filename)
    doc_hash = PipelineMemoizer.compute_hash(file_bytes, clean_filename)

    # Check memoization cache
    cached = memoizer.get(doc_hash)
    if cached is not None:
        cached_resp, session_dict = cached
        sessions[cached_resp.document_id] = session_dict
        return cached_resp

    doc_id = str(uuid.uuid4())[:8]

    # Stage 1: Document Parsing
    parsed_doc = parser.parse_file(file_bytes, clean_filename)
    raw_text = parsed_doc["raw_text"]

    # Stage 2: Clause Engine - Segmentation
    raw_clauses = segmenter.segment(parsed_doc)

    # Infer document type
    doc_type = doc_type_hint
    if doc_type == "auto":
        text_low = raw_text.lower()
        if "employment" in text_low or "employee" in text_low:
            doc_type = "Employment Agreement"
        elif "lease" in text_low or "tenant" in text_low or "landlord" in text_low:
            doc_type = "Residential / Commercial Lease"
        elif "services" in text_low or "sow" in text_low or "deliverables" in text_low:
            doc_type = "Master Services Agreement"
        elif "confidential" in text_low or "non-disclosure" in text_low:
            doc_type = "Non-Disclosure Agreement"
        else:
            doc_type = "Commercial Contract"

    # Stage 2b: Clause Classification & Structured Field Extraction
    processed_clauses = []
    for rc in raw_clauses:
        category, cls_conf = classifier.classify(rc.title, rc.text)
        fields = field_extractor.extract_fields(rc.text)

        processed_clauses.append({
            "id": rc.clause_id,
            "number": rc.number,
            "title": rc.title,
            "text": rc.text,
            "category": category,
            "page_number": rc.page_number,
            "line_start": rc.line_start,
            "line_end": rc.line_end,
            "fields": fields
        })

    # Stage 3: Graph Construction
    clause_graph = ClauseGraph()
    clause_graph.build_graph(processed_clauses)

    # Stage 4: Hybrid Search Indexing
    retriever = HybridRetriever()
    retriever.index_clauses(processed_clauses)

    # Stage 5: Gemini Analysis & Reference Corpus Deviation Check
    clause_nodes: List[ClauseNode] = []
    questions_for_lawyer: List[str] = []

    for c in processed_clauses:
        # Qualitative attention flags & plain-language rewriting
        att_level, reasons, plain_lang = gemini_analyzer.analyze_clause(c)

        # Deviation check against reference corpus
        deviation = deviation_detector.detect_deviation(doc_type, c["category"], c["text"])

        # Verification entailment check
        conf_level, verif_reason = verifier.verify_clause_analysis(
            clause_text=c["text"],
            attention_reasons=reasons,
            plain_text=plain_lang.get("general", "")
        )

        c_node = ClauseNode(
            id=c["id"],
            number=c["number"],
            title=c["title"],
            text=c["text"],
            category=c["category"],
            page_number=c["page_number"],
            line_start=c["line_start"],
            line_end=c["line_end"],
            fields=c["fields"],
            attention_level=att_level,
            attention_reasons=reasons,
            plain_language=plain_lang,
            deviation_check=deviation,
            confidence=conf_level,
            verification_reasoning=verif_reason,
            disclaimer="This is an informational flag, not a legal determination."
        )
        clause_nodes.append(c_node)

        # Collect lawyer questions for High attention clauses
        if att_level == AttentionLevel.HIGH:
            questions_for_lawyer.append(
                f"Regarding {c['title']} ({c['id']}): What are the jurisdictional implications of the restrictive covenants or risk allocation terms stated here?"
            )

    # Stage 6: Cross-Clause Conflict Detection
    conflict_detector = ConflictDetector(clause_graph)
    conflicts = conflict_detector.detect_conflicts(processed_clauses)

    for conf in conflicts:
        questions_for_lawyer.append(
            f"Conflict Resolution: {conf.suggested_question} (between {conf.clause_a_title} and {conf.clause_b_title})"
        )

    # Stage 7: Obligation Timeline Extraction
    timeline_extractor = TimelineExtractor()
    timeline = timeline_extractor.extract_timeline(processed_clauses)

    # Stage 8: Multi-Hop QA Engine setup
    qa_engine = MultiHopQAEngine(clause_graph, retriever, verifier, gemini_client)

    # Build final response object
    summary = (
        f"Analyzed {len(clause_nodes)} clauses across {parsed_doc['total_pages']} pages of this {doc_type}. "
        f"Identified {len([c for c in clause_nodes if c.attention_level == AttentionLevel.HIGH])} high-attention provisions, "
        f"{len(conflicts)} potential cross-clause conflicts, and {len(timeline)} chronological obligation milestones."
    )

    response = DocumentAnalysisResponse(
        document_id=doc_id,
        document_name=clean_filename,
        document_type=doc_type,
        total_clauses=len(clause_nodes),
        clauses=clause_nodes,
        graph_edges=clause_graph.get_all_edges(),
        conflicts=conflicts,
        timeline=timeline,
        questions_for_lawyer=questions_for_lawyer[:6],
        overall_summary=summary,
        raw_text=raw_text
    )

    # Cache session and memoize result
    session_data = {
        "response": response,
        "processed_clauses": processed_clauses,
        "clause_graph": clause_graph,
        "retriever": retriever,
        "qa_engine": qa_engine
    }
    sessions[doc_id] = session_data
    memoizer.put(doc_hash, (response, session_data))

    return response

# Pre-warm memoizer with standard contracts for instant response
try:
    process_document_pipeline(SAMPLE_EMPLOYMENT_SCANNED.encode("utf-8"), "Executive_Employment_Agreement_Scanned.txt", "Employment Agreement")
    process_document_pipeline(SAMPLE_LEASE_CONFLICT.encode("utf-8"), "Commercial_Residential_Lease_Conflict.txt", "Residential / Commercial Lease")
except Exception:
    pass

@app.get("/api")
@app.get("/api/")
@app.get("/api/health")
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "LexPilot Evidence-Grounded Legal Reasoning Pipeline",
        "gemini_connected": gemini_client.is_available(),
        "gemini_model": "gemini-2.5-flash" if gemini_client.is_available() else "Offline Verified Legal Engine",
        "doc_ai_connected": parser.has_doc_ai,
        "active_sessions": len(sessions),
        "security": {
            "rate_limiting_enabled": True,
            "owasp_headers_active": True,
            "max_upload_size_mb": 10,
            "prompt_guardrail_active": True
        }
    }

@app.get("/api/samples")
@app.get("/samples")
def get_sample_list():
    return [
        {
            "id": "sample_employment",
            "name": "Executive Employment Agreement (Messy Scanned OCR)",
            "type": "Employment Agreement",
            "highlights": "Survival cross-reference (Sec 4 to Sec 12), 36-month non-compete, 90-day termination notice deviation.",
            "tested_features": "Messy OCR parsing, Reference corpus deviation, Multi-hop survival reasoning"
        },
        {
            "id": "sample_lease",
            "name": "Residential & Commercial Lease (Conflict Demo)",
            "type": "Residential / Commercial Lease",
            "highlights": "Section 4 (30-day notice) contradicts Section 14 (60-day notice); 15% late fee deviation.",
            "tested_features": "Cross-clause conflict detection, Obligation timeline, Side-by-side evidence"
        },
        {
            "id": "sample_msa_v1",
            "name": "Master Services Agreement (Baseline V1)",
            "type": "Master Services Agreement",
            "highlights": "Net 30 terms, $50,000 liability cap, 12-month non-solicit, mutual indemnity.",
            "tested_features": "Semantic clause mapping, Pre-comparison baseline"
        },
        {
            "id": "sample_msa_v2",
            "name": "Master Services Agreement (Revised Draft V2)",
            "type": "Master Services Agreement",
            "highlights": "Net 60 + penalty, reduced liability cap, uncapped indemnity, deleted non-solicitation, added data security.",
            "tested_features": "Semantic contract-to-contract comparison, Material change flags"
        }
    ]

@app.get("/api/sample/{sample_id}")
@app.get("/sample/{sample_id}")
def get_sample_document(sample_id: str):
    if sample_id == "sample_employment":
        raw = SAMPLE_EMPLOYMENT_SCANNED
        filename = "Executive_Employment_Agreement_Scanned.txt"
    elif sample_id == "sample_lease":
        raw = SAMPLE_LEASE_CONFLICT
        filename = "Commercial_Residential_Lease_Conflict.txt"
    elif sample_id == "sample_msa_v1":
        raw = SAMPLE_MSA_V1
        filename = "Master_Services_Agreement_V1.txt"
    elif sample_id == "sample_msa_v2":
        raw = SAMPLE_MSA_V2
        filename = "Master_Services_Agreement_V2_Revised.txt"
    else:
        raise HTTPException(status_code=404, detail="Sample contract not found")

    return process_document_pipeline(raw.encode("utf-8"), filename)

@app.post("/api/upload")
@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Accepts PDF, text, or scan document and runs full parsing and analysis pipeline.
    Enforces strict size validation (10MB limit), magic byte validation, and filename sanitization.
    """
    clean_filename = sanitize_filename(file.filename)
    contents = await file.read(MAX_UPLOAD_BYTES + 1024)

    is_valid, err_msg = validate_file_upload(contents, clean_filename)
    if not is_valid:
        raise HTTPException(status_code=400, detail=err_msg)

    return process_document_pipeline(contents, clean_filename)

@app.post("/api/qa", response_model=QAResponse)
@app.post("/qa", response_model=QAResponse)
def ask_question(payload: QARequest):
    """
    Verified Q&A with multi-hop graph reasoning, prompt injection protection, and PII masking.
    """
    # Prompt injection & adversarial input guardrail
    is_safe, refusal_reason = check_prompt_injection(payload.question)
    if not is_safe:
        return QAResponse(
            question=payload.question,
            answer=f"🛡️ Security Notice: Your question was flagged by LexPilot's safety guardrail ({refusal_reason}). LexPilot only provides evidence-grounded answers strictly based on the contract clauses.",
            evidence_citations=[],
            confidence=ConfidenceLevel.LOW,
            multi_hop=False,
            graph_path=[],
            reasoning_steps=["Security check: Query intercepted by Prompt Injection & Jailbreak Guardrail."],
            jurisdiction_note="System security filter active.",
            disclaimer="This is an informational security notice."
        )

    # Redact PII before analysis
    safe_question = mask_pii(payload.question)

    doc_id = payload.document_id
    if not doc_id or doc_id not in sessions:
        # Default to the most recent active session
        if len(sessions) > 0:
            doc_id = list(sessions.keys())[-1]
        else:
            # Auto-load sample employment document if no session exists
            sample_resp = process_document_pipeline(SAMPLE_EMPLOYMENT_SCANNED.encode("utf-8"), "Executive_Employment_Agreement_Scanned.txt")
            doc_id = sample_resp.document_id

    session = sessions[doc_id]
    qa_engine: MultiHopQAEngine = session["qa_engine"]
    return qa_engine.answer_question(safe_question, payload.jurisdiction or "General / Unspecified")

@app.post("/api/compare")
@app.post("/compare")
def compare_contracts(
    doc_a_id: Optional[str] = Form(None),
    doc_b_id: Optional[str] = Form(None),
    file_a: Optional[UploadFile] = File(None),
    file_b: Optional[UploadFile] = File(None)
):
    """
    Compares two contracts semantically (Version A vs Version B).
    Includes upload validation and filename sanitization.
    """
    # Resolve Document A clauses
    clauses_a = []
    if file_a:
        clean_name_a = sanitize_filename(file_a.filename)
        bytes_a = file_a.file.read(MAX_UPLOAD_BYTES + 1024)
        is_valid, err = validate_file_upload(bytes_a, clean_name_a)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Document A error: {err}")
        resp_a = process_document_pipeline(bytes_a, clean_name_a)
        clauses_a = sessions[resp_a.document_id]["processed_clauses"]
    elif doc_a_id and doc_a_id in sessions:
        clauses_a = sessions[doc_a_id]["processed_clauses"]
    else:
        # Fallback to MSA V1
        resp_a = process_document_pipeline(SAMPLE_MSA_V1.encode("utf-8"), "Master_Services_Agreement_V1.txt")
        clauses_a = sessions[resp_a.document_id]["processed_clauses"]

    # Resolve Document B clauses
    clauses_b = []
    if file_b:
        clean_name_b = sanitize_filename(file_b.filename)
        bytes_b = file_b.file.read(MAX_UPLOAD_BYTES + 1024)
        is_valid, err = validate_file_upload(bytes_b, clean_name_b)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Document B error: {err}")
        resp_b = process_document_pipeline(bytes_b, clean_name_b)
        clauses_b = sessions[resp_b.document_id]["processed_clauses"]
    elif doc_b_id and doc_b_id in sessions:
        clauses_b = sessions[doc_b_id]["processed_clauses"]
    else:
        # Fallback to MSA V2 Revised
        resp_b = process_document_pipeline(SAMPLE_MSA_V2.encode("utf-8"), "Master_Services_Agreement_V2_Revised.txt")
        clauses_b = sessions[resp_b.document_id]["processed_clauses"]

    comparison_results = comparator.compare(clauses_a, clauses_b)
    return {
        "total_compared_clauses": len(comparison_results),
        "material_changes": len([c for c in comparison_results if "Material" in c.change_flag]),
        "items": comparison_results,
        "disclaimer": "This is an informational comparison, not a legal determination."
    }

@app.get("/api/corpus")
@app.get("/corpus")
def get_reference_corpus():
    """
    Exposes preloaded CUAD-derived template baselines across employment, NDA, lease, and MSA.
    """
    return {
        "templates": REFERENCE_CORPUS,
        "provenance": "Preloaded reference benchmarks derived from public commercial contracts and CUAD examples. No fine-tuning applied.",
        "supported_contract_types": ["Employment Agreement", "Non-Disclosure Agreement", "Residential / Commercial Lease", "Master Services Agreement"]
    }

@app.post("/api/settings/key")
@app.post("/settings/key")
def update_api_key(api_key: str = Body(..., embed=True)):
    gemini_client.set_api_key(api_key.strip())
    return {
        "status": "updated",
        "gemini_connected": gemini_client.is_available()
    }

# Serve built React frontend if dist directory exists
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.exists(frontend_dist):
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    if os.path.exists(os.path.join(frontend_dist, "assets")):
        app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/")
    def serve_root():
        return FileResponse(os.path.join(frontend_dist, "index.html"))

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("openapi"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
