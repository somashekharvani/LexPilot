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
"""

import os
import re
import uuid
from typing import Dict, Any, List, Optional, Tuple
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
from .clause_engine.legal_ir import LegalIRBuilder
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

import hashlib
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

app = FastAPI(
    title="LexPilot API",
    description="Evidence-Grounded Legal Reasoning System",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security Headers & Rate Limiting Configuration
RATE_LIMIT_MAX_REQUESTS = 180   # Max requests per window per IP
RATE_LIMIT_WINDOW_SECONDS = 60  # 60s sliding window
request_history: Dict[str, List[float]] = defaultdict(list)

@app.middleware("http")
async def security_and_rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "127.0.0.1"
    now = time.time()

    # Rate limiting (exempt static assets, docs, and health checks)
    path = request.url.path
    if not path.startswith("/assets") and path not in ["/docs", "/openapi.json", "/api/health", "/health"]:
        # Prune requests outside sliding window
        request_history[client_ip] = [t for t in request_history[client_ip] if now - t < RATE_LIMIT_WINDOW_SECONDS]
        if len(request_history[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please wait before making additional requests."},
                headers={"Retry-After": "60"}
            )
        request_history[client_ip].append(now)

    response = await call_next(request)

    # Inject HTTP Security Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob: https:;"

    return response

# Pipeline Singletons
parser = DocumentParser()
segmenter = ClauseSegmenter()
classifier = ClauseClassifier()
field_extractor = FieldExtractor()
legal_ir_builder = LegalIRBuilder()
gemini_client = GeminiClient()
gemini_analyzer = GeminiAnalyzer(gemini_client)
verifier = VerificationAgent(gemini_client)
deviation_detector = DeviationDetector()
comparator = ContractComparator(verifier)

# In-memory document session cache
sessions: Dict[str, Dict[str, Any]] = {}

# In-memory Content-Hash Cache: sha256 -> (doc_id, DocumentAnalysisResponse)
content_cache: Dict[str, Tuple[str, DocumentAnalysisResponse]] = {}

def process_document_pipeline(file_bytes: bytes, filename: str, doc_type_hint: str = "auto") -> DocumentAnalysisResponse:
    """
    Executes the single coherent pipeline from raw bytes to verified legal analysis report.
    Utilizes SHA-256 in-memory content caching and parallel thread pool execution for high efficiency.
    """
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    if file_hash in content_cache:
        cached_doc_id, cached_resp = content_cache[file_hash]
        if cached_doc_id in sessions:
            return cached_resp

    doc_id = str(uuid.uuid4())[:8]

    # Stage 1: Document Parsing
    parsed_doc = parser.parse_file(file_bytes, filename)
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

    # Stage 2b: Clause Classification & Structured Field Extraction -> Legal-IR
    processed_clauses = []
    for rc in raw_clauses:
        category, cls_conf = classifier.classify(rc.title, rc.text)
        fields = field_extractor.extract_fields(rc.text)
        legal_ir_obj = legal_ir_builder.build_legal_ir(
            clause_id=rc.clause_id,
            number=rc.number,
            title=rc.title,
            text=rc.text,
            category=category,
            page_number=rc.page_number,
            line_start=rc.line_start,
            line_end=rc.line_end,
            fields=fields,
            full_doc_text=raw_text
        )

        processed_clauses.append({
            "id": rc.clause_id,
            "number": rc.number,
            "title": rc.title,
            "text": rc.text,
            "category": category,
            "page_number": rc.page_number,
            "line_start": rc.line_start,
            "line_end": rc.line_end,
            "fields": fields,
            "legal_ir": legal_ir_obj
        })

    # Stage 3: Graph Construction
    clause_graph = ClauseGraph()
    clause_graph.build_graph(processed_clauses)

    # Stage 4: Hybrid Search Indexing
    retriever = HybridRetriever()
    retriever.index_clauses(processed_clauses)

    # Stage 5: Gemini Analysis & Reference Corpus Deviation Check (Parallelized for Efficiency)
    def _analyze_single_clause(c: Dict[str, Any]) -> Tuple[ClauseNode, Optional[str]]:
        att_level, reasons, plain_lang = gemini_analyzer.analyze_clause(c)
        deviation = deviation_detector.detect_deviation(doc_type, c["category"], c["text"])
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
            legal_ir=c.get("legal_ir"),
            attention_level=att_level,
            attention_reasons=reasons,
            plain_language=plain_lang,
            deviation_check=deviation,
            confidence=conf_level,
            verification_reasoning=verif_reason,
            disclaimer="This is an informational flag, not a legal determination."
        )
        lawyer_q = None
        if att_level == AttentionLevel.HIGH:
            lawyer_q = f"Regarding {c['title']} ({c['id']}): What are the jurisdictional implications of the restrictive covenants or risk allocation terms stated here?"
        return c_node, lawyer_q

    with ThreadPoolExecutor(max_workers=min(8, len(processed_clauses) or 1)) as executor:
        analysis_results = list(executor.map(_analyze_single_clause, processed_clauses))

    clause_nodes: List[ClauseNode] = [r[0] for r in analysis_results]
    questions_for_lawyer: List[str] = [r[1] for r in analysis_results if r[1] is not None]

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
        document_name=filename,
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

    # Cache session
    sessions[doc_id] = {
        "response": response,
        "processed_clauses": processed_clauses,
        "clause_graph": clause_graph,
        "retriever": retriever,
        "qa_engine": qa_engine
    }

    # Store in Content Cache
    content_cache[file_hash] = (doc_id, response)

    return response

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
        "active_sessions": len(sessions)
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
def load_sample_document(sample_id: str):
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

MAX_UPLOAD_SIZE = 15 * 1024 * 1024  # 15 MB limit
ALLOWED_UPLOAD_EXTENSIONS = {".pdf", ".txt", ".docx", ".doc"}

@app.post("/api/upload")
@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Accepts PDF, text, or scan document and runs full parsing and analysis pipeline.
    Hardened with filename path sanitization, format whitelisting, and a 15MB size limit.
    """
    raw_filename = file.filename or "contract.txt"
    safe_filename = os.path.basename(raw_filename)
    safe_filename = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', safe_filename)

    _, ext = os.path.splitext(safe_filename.lower())
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Allowed formats: {', '.join(sorted(ALLOWED_UPLOAD_EXTENSIONS))}"
        )

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum allowed upload limit of {MAX_UPLOAD_SIZE // (1024 * 1024)}MB."
        )

    return process_document_pipeline(contents, safe_filename)

@app.post("/api/qa", response_model=QAResponse)
@app.post("/qa", response_model=QAResponse)
def ask_question(payload: QARequest):
    """
    Verified Q&A with multi-hop graph reasoning and adversarial prompt-injection guardrails.
    """
    from .analysis.gemini_analyzer import check_for_prompt_injection
    is_inj, _ = check_for_prompt_injection(payload.question)
    if is_inj:
        return QAResponse(
            question=payload.question,
            answer="Security Notice: This query contains adversarial instruction overrides or unauthorized system manipulation commands. LexPilot evaluates legal clauses as passive data only and does not execute prompt-injected commands.",
            citations=[],
            provenance=[],
            confidence=ConfidenceLevel.LOW,
            multi_hop=False,
            graph_path=[],
            reasoning_steps=["Prompt Injection & Jailbreak Guardrail: Query intercepted and refused due to adversarial override signature."],
            jurisdiction_note="Adversarial input blocked by security policy.",
            disclaimer="This is an informational flag, not a legal determination."
        )

    doc_id = payload.document_id
    if not doc_id or doc_id not in sessions:
        # Default to the most recent active session
        if sessions:
            doc_id = list(sessions.keys())[-1]
        else:
            # Auto-load sample employment document if no session exists
            sample_resp = process_document_pipeline(SAMPLE_EMPLOYMENT_SCANNED.encode("utf-8"), "Executive_Employment_Agreement_Scanned.txt")
            doc_id = sample_resp.document_id

    session = sessions[doc_id]
    qa_engine: MultiHopQAEngine = session["qa_engine"]
    return qa_engine.answer_question(payload.question, payload.jurisdiction or "General / Unspecified")

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
    """
    # Resolve Document A clauses
    clauses_a = []
    if file_a:
        bytes_a = file_a.file.read()
        resp_a = process_document_pipeline(bytes_a, file_a.filename)
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
        bytes_b = file_b.file.read()
        resp_b = process_document_pipeline(bytes_b, file_b.filename)
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
    gemini_client.set_api_key(api_key)
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
