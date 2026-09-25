# LexPilot — Evidence-Grounded Legal Reasoning System

**AI for Legal Assistance & Access**

[![Live Demo](https://img.shields.io/badge/Vercel-Live%20Demo-success?style=for-the-badge&logo=vercel)](https://lex-pilot-phi.vercel.app/)
[![API Docs](https://img.shields.io/badge/FastAPI-Swagger%20UI-009688?style=for-the-badge&logo=fastapi)](https://lex-pilot-phi.vercel.app/docs)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)

* 🌐 **Live Web Application:** [https://lex-pilot-phi.vercel.app/](https://lex-pilot-phi.vercel.app/)
* 📚 **Interactive Swagger API Documentation:** [https://lex-pilot-phi.vercel.app/docs](https://lex-pilot-phi.vercel.app/docs)

LexPilot is a GenAI-powered legal document analysis system that helps users understand contracts by connecting AI-generated insights directly to the source clauses that support them.

Instead of providing an ungrounded summary or generic legal chatbot experience, LexPilot creates a structured, verified representation of a legal document containing:

* **Clauses and their legal categories** (termination, payment, liability, confidentiality, etc.)
* **Extracted structured entities:** Parties, dates/deadlines, monetary amounts, obligations, and defined terms
* **Attention points requiring review** with explicit bullet-point reasons
* **Cross-clause conflicts and dependencies** cited side-by-side
* **Semantic differences between contract versions** (not raw character diffing)
* **Evidence-linked answers to user questions** with exact clause citations
* **Confidence-verified AI claims** scored as High, Medium, or Low
* **Visual obligation timelines** mapping dates and covenants chronologically
* **Multi-hop relationships between clauses** traversing survival and dependency graph edges

---

![LexPilot Dashboard](docs/images/dashboard.png)

---

## 🏛️ Core Pipeline

$$\text{Document (PDF/Scan/Text)} \longrightarrow \text{Parsing} \longrightarrow \text{Clause Segmentation} \longrightarrow \text{Classification} \longrightarrow \text{Clause Graph + Hybrid Retrieval} \longrightarrow \text{Gemini Analysis} \longrightarrow \text{Evidence Verification} \longrightarrow \text{Split-Pane UI}$$

1. **Document Parsing Layer:** Ingests native PDFs, scanned contracts with OCR noise, or plain text, preserving section headers, tables, and signature blocks.
2. **Clause Engine:** Segments text into discrete numbered clauses and classifies them into 10 standard legal categories with structured field extraction.
3. **In-Memory Clause Graph & Hybrid Retrieval:** Constructs a NetworkX graph linking `REFERENCES`, `SURVIVES`, `CONFLICTS_WITH`, and `DEPENDS_ON` edges alongside BM25 and semantic keyword indexing.
4. **Gemini Analysis Layer:** Generates qualitative attention flags, plain-language rewrites calibrated across 3 reading levels, and answers complex multi-hop queries.
5. **Verification Agent:** Performs a secondary entailment check verifying that cited clauses strictly support each generated statement.
6. **Split-Pane UI:** Left pane displays the source document; right pane displays AI legal analysis with clickable citations that smoothly scroll and highlight the source clause.

---

## 📸 Product Screenshots

### 1. Evidence-Grounded Analysis & Attention Flags
> *Section 12 (Non-Competition) flagged as `HIGH ATTENTION` with explicit factual justifications, 36-month non-compete deviation check against CUAD commercial benchmarks, and calibrated plain-language synthesis.*

![Evidence Analysis](docs/images/evidence.png)

### 2. Multi-Hop Legal Q&A (2 Citations)
> *Answering "If I terminate under Section 4, does the non-compete in Section 12 still apply?" by traversing the graph edge `SEC-4` $\rightarrow$ `SURVIVES` $\rightarrow$ `SEC-12` with High Confidence verification.*

![Multi-Hop Q&A](docs/images/multihop.png)

### 3. Contract Conflict Detection
> *Side-by-side evidence analysis identifying contradictory notice windows: Section 4 (30 days' notice) contradicts Section 14 (60 days' notice).*

![Conflict Detection](docs/images/conflict.png)

---

## 🤖 GenAI Usage

Google Gemini is the primary Generative AI service powering LexPilot:

* **Plain-Language Interpretation:** Translates dense legalese into calibrated reading levels (8th Grade Accessible, Executive Commercial Impact, and Technical Paralegal).
* **Attention-Point Generation:** Identifies high-friction covenants (e.g., broad non-competes, asymmetric indemnities) and produces grounded, bullet-pointed explanations.
* **Cross-Clause Multi-Hop Reasoning:** Harmonizes interdependent clauses (e.g., assessing whether a non-compete survives termination under a separate exit clause).
* **Evidence-Grounded Question Answering:** Answers user questions strictly using retrieved clauses, refusing to fabricate answers without citations.
* **Semantic Contract Comparison:** Aligns clauses between two versions of an agreement to identify substantive legal shifts rather than typographical diffs.

A separate verification pass checks AI-generated claims against the original source clauses to assign **High**, **Medium**, or **Low** confidence. If network interruptions occur, the application seamlessly falls back to its deterministic legal reasoning engine.

---

## 🛡️ Important Safety Boundary

* **Informational Assistance Only:** LexPilot provides document analysis and informational assistance. It does **not** provide legal advice or legal determinations and is **not a replacement for a qualified legal professional**.
* **No Numeric "Risk Scores":** The product deliberately avoids misleading numeric risk scores (e.g., "78% risk"). Instead, it produces qualitative attention levels (**High Attention**, **Review Recommended**, **Normal**) with verifiable, bullet-pointed reasons.
* **Visible Disclaimers:** Every generated finding, conflict, and answer displays a clear informational disclaimer.

---

## 🚀 Main Features (All 10 Implemented & Live)

1. **Smart Document Understanding:** Ingests native PDFs, scans, and text; handles OCR noise; extracts section hierarchies and signatures.
2. **Clause Intelligence:** Classifies clauses into 10 categories (`termination`, `payment`, `liability`, `confidentiality`, `indemnification`, `renewal`, `governing_law`, `non_compete`, `notice`, `other`).
3. **Attention Detection:** Qualitative attention levels paired with explicit factual justifications.
4. **Cross-Clause Reasoning:** Graph-based contradiction detection identifying clashing notice windows or uncapped indemnities.
5. **Contract Comparison:** Semantic clause alignment comparing original vs. revised drafts.
6. **Verified Legal Q&A:** Question answering where every response includes exact quotes, clause IDs, and page numbers.
7. **Confidence-Weighted Verification:** Entailment verification assigning High, Medium, or Low confidence to every claim.
8. **Reference Corpus Deviation Detection:** Preloaded CUAD benchmarks flagging deviations from commercial norms as distinct "Deviation Check" notes.
9. **Structured Obligation Timeline:** Chronological visual timeline track of operational deadlines, grace periods, and payment dates.
10. **Multi-Hop Graph Reasoning:** Graph traversal answering multi-clause covenants with multiple source citations.

---

## 🎯 Hackathon Live Demo Story & Walkthrough

LexPilot is organized around a unified, end-to-end user journey:

**Upload PDF → Clause Extraction → Attention Flag → Click Evidence → Active Highlight in Left Pane → Cross-Clause Conflict → Multi-Hop Q&A (2 Citations) → Obligation Timeline → Semantic Contract Comparison**

Follow these 6 steps directly in the running web application ([https://lex-pilot-phi.vercel.app](https://lex-pilot-phi.vercel.app)):

1. **Step 1: Ingest Messy Scanned Contract**
   * Click **`1. Scanned Contract`** on the Live Demo bar (or upload your own PDF).
   * Notice that 9 structured clauses are extracted with preserved numbering and signatures despite scan artifacts.
2. **Step 2: Inspect Attention & Deviation Check**
   * Click **`2. Attention & Deviation`** to select **Section 12 (Non-Competition)**.
   * Observe the **`HIGH ATTENTION`** badge and the **Deviation Check** note (*"Non-compete duration of 36 months significantly exceeds standard commercial benchmark of 12 months"*).
   * Toggle between **8th Grade**, **Executive**, and **Paralegal** reading levels.
3. **Step 3: Multi-Hop Graph Reasoning (The Core Proof)**
   * Click **`3. Multi-Hop Reasoning`** in the demo bar:
     > *"If I terminate under Section 4, does the non-compete in Section 12 still apply?"*
   * Observe the verified answer: LexPilot traverses the in-memory graph edge `SEC-4` $\rightarrow$ `SURVIVES` $\rightarrow$ `SEC-12`.
   * **Click either citation card:** The left document pane automatically scrolls and pulses with an **`ACTIVE EVIDENCE CITATION`** glowing highlight!
4. **Step 4: Cross-Clause Conflict Detection**
   * Click **`4. Cross-Clause Conflict`** to load the Commercial Lease.
   * Review the side-by-side conflict: **Section 4 (30 days' notice)** vs. **Section 14 (60 days' notice)** with an auto-generated *"Question for Your Lawyer"*.
5. **Step 5: Structured Obligation Timeline**
   * Click **`5. Obligation Timeline`** to view all operational deadlines, payment dates (1st of month), and grace periods (5th of month) mapped onto an interactive vertical track.
6. **Step 6: Semantic Contract Comparison**
   * Click **`6. Semantic Comparison`** to run clause-to-clause alignment between **MSA Version 1** and **Revised Draft Version 2**, reviewing material changes and deleted covenants.

---

## 🧪 Testing

The repository includes both an end-to-end pipeline test and modular unit tests:

### 1. End-to-End Pipeline Verification
```powershell
python backend/test_pipeline.py
```
* Verifies document parsing, 10-category classification, qualitative attention flags, CUAD deviation checks, cross-clause conflicts, timeline extraction, semantic comparison, and multi-hop reasoning.

### 2. Modular Unit Test Suite (21 Comprehensive Tests)
```powershell
python -m unittest discover tests
```
* `tests/test_parsing.py`: Layout-aware parsing & OCR noise normalization
* `tests/test_classification.py`: 10-category classification & entity extraction
* `tests/test_entailment.py`: Entailment verification & confidence scoring
* `tests/test_conflict.py`: Cross-clause contradiction detection
* `tests/test_efficiency.py`: Bounded LRU cache eviction, TTL expiration, SHA-256 memoization (<5ms), and pre-compiled regex performance
* `tests/test_security.py`: OWASP security response headers, sliding-window rate limiting, directory traversal sanitization, 10MB payload enforcement, PDF magic bytes (`%PDF-`), LLM prompt injection blocking, and PII masking

### 3. Live System Verification
```powershell
python backend/verify_all_live.py
```
* Runs 11 live checks against the active HTTP server and API endpoints with 100% pass rate.

---

## 🔒 Security & Safety Architecture

* **OWASP Security Response Headers:** Injects `Strict-Transport-Security` (HSTS), `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `X-XSS-Protection: 1; mode=block`, and modern `Content-Security-Policy` (CSP) on all responses.
* **In-Memory Rate Limiting (DoS Defense):** Enforces a sliding-window rate limiter (120 requests/minute per client IP) to protect against API abuse.
* **Strict CORS Policy:** Eliminates insecure `*` wildcard origin policies when credentials are permitted, utilizing explicit origin whitelists and verified preview regexes.
* **Strict Upload Payload Validation:** Enforces a strict 10 MB payload limit, file extension whitelisting (`.pdf`, `.txt`, `.doc`, `.docx`), and verifies `%PDF-` magic bytes.
* **Path Traversal & Filename Sanitization:** Strips directory traversal sequences (`..`, `/`, `\`), null bytes (`\x00`), and non-whitelisted characters.
* **Prompt Injection & Adversarial Jailbreak Guardrails:** Intercepts prompt override attempts (`ignore previous instructions`, `DAN mode`, `developer mode`, `<script>` tags) before reaching the reasoning model.
* **PII Redaction & Privacy by Design:** Automatically redacts sensitive identifiers (SSNs, credit cards, emails, phone numbers) before processing or logging.
* **No Hardcoded Secrets:** All credentials are loaded exclusively through environment variables.

---

## ⚡ Efficiency, Performance & Scalability

* **Bounded LRU Session Cache:** Replaces unbounded session dictionaries with a thread-safe `LRUSessionCache` (max 50 sessions) featuring automatic TTL eviction to guarantee zero memory leaks under sustained operation.
* **SHA-256 Pipeline Memoization:** Hashes document contents with SHA-256 to deliver $<1$ ms responses on repeated contracts without redundant NLP pipeline execution.
* **Pre-Compiled Regex Automata:** All legal classification patterns, entity extractors, and conflict rules are pre-compiled into static `re.Pattern` automata at module load, eliminating dynamic recompilation overhead.
* **Pre-Indexed Frozenset Retrieval:** Hybrid BM25 retriever pre-computes token sets and lowercased titles during indexing, reducing query search latency to $<0.5$ ms.
* **Lightweight Working Tree:** Total repository footprint is only **2.4 MB** including documentation and product screenshots (well below the strict **10 MB** limit).
* **Resilient Offline Fallback:** Google Gemini API calls utilize strict timeouts with instantaneous fallback to the deterministic offline legal engine.

---

## 🚀 Running the Application Locally

### Quick Start (Single Command)
1. Start the FastAPI backend and bundled web application:
   ```powershell
   python backend/run.py
   ```
2. Open your browser:
   * **Web Application:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
   * **API Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
