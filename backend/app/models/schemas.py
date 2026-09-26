from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class ConfidenceLevel(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class AttentionLevel(str, Enum):
    HIGH = "🔴 High"
    REVIEW = "🟠 Review"
    NORMAL = "🟢 Normal"

class ReadingLevel(str, Enum):
    GENERAL = "general"     # 8th grade / accessible plain English
    EXECUTIVE = "executive" # C-Suite / commercial impact summary
    TECHNICAL = "technical" # Paralegal / contract specialist

class ConflictType(str, Enum):
    TEMPORAL = "TEMPORAL"       # Notice period, cure period, milestone timeline clashes
    AMOUNT = "AMOUNT"           # Monetary fee, deposit, or penalty calculation contradictions
    OBLIGATION = "OBLIGATION"   # Direct duties contradiction, capped liability vs uncapped indemnity
    SCOPE = "SCOPE"             # Geographic, subject matter, or exclusivity scope contradictions
    DEFINITION = "DEFINITION"   # Conflicting defined terms across document
    SURVIVAL = "SURVIVAL"       # Termination vs survival mandate contradiction
    CONDITIONAL = "CONDITIONAL" # Conflicting conditional priority or "notwithstanding" clauses

from .legal_ir import LegalIRClause

class StructuredFields(BaseModel):
    parties_involved: List[str] = Field(default_factory=list)
    dates: List[str] = Field(default_factory=list)
    monetary_amounts: List[str] = Field(default_factory=list)
    obligations: List[str] = Field(default_factory=list)
    defined_terms: List[str] = Field(default_factory=list)

class ClauseNode(BaseModel):
    id: str
    number: str
    title: str
    text: str
    category: str
    page_number: int = 1
    line_start: int = 0
    line_end: int = 0
    fields: StructuredFields = Field(default_factory=StructuredFields)
    legal_ir: Optional[LegalIRClause] = None
    attention_level: AttentionLevel = AttentionLevel.NORMAL
    attention_reasons: List[str] = Field(default_factory=list)
    plain_language: Dict[str, str] = Field(default_factory=dict)
    deviation_check: Optional[str] = None
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    verification_reasoning: str = ""
    disclaimer: str = "This is an informational flag, not a legal determination."

class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str  # REFERENCES, DEPENDS_ON, SURVIVES, CONFLICTS_WITH, SUPERSEDES
    description: str
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH

class ContractConflict(BaseModel):
    id: str
    clause_a_id: str
    clause_a_title: str
    clause_a_excerpt: str
    clause_b_id: str
    clause_b_title: str
    clause_b_excerpt: str
    conflict_type: str
    typed_category: ConflictType = ConflictType.TEMPORAL
    explanation: str
    attention_level: AttentionLevel = AttentionLevel.HIGH
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    suggested_question: str
    disclaimer: str = "This is an informational flag, not a legal determination."

class TimelineEvent(BaseModel):
    id: str
    clause_id: str
    clause_title: str
    party: str
    timeframe_or_date: str
    obligation: str
    category: str
    relative_order: int = 0
    attention_level: AttentionLevel = AttentionLevel.NORMAL
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    citation: str

class ComparisonItem(BaseModel):
    category: str
    title: str
    version_a_clause_id: Optional[str] = None
    version_a_text: Optional[str] = None
    version_b_clause_id: Optional[str] = None
    version_b_text: Optional[str] = None
    change_flag: str  # "Unchanged", "Modified - Material", "Modified - Minor", "Added in Revision", "Removed in Revision"
    semantic_delta: str
    attention_level: AttentionLevel = AttentionLevel.NORMAL
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    disclaimer: str = "This is an informational flag, not a legal determination."

class Citation(BaseModel):
    clause_id: str
    title: str
    quote: str
    page_number: int = 1

class SupportingClauseSpan(BaseModel):
    clause_id: str
    title: str = ""
    page: int = 1
    char_start: int = 0
    char_end: int = 0
    quote: str = ""

class ProvenanceRecord(BaseModel):
    claim_id: str
    claim_text: str
    reasoning_step: str = ""
    supporting_clauses: List[SupportingClauseSpan] = Field(default_factory=list)
    entailment_result: str = "PASS"  # PASS, PARTIAL, INCONCLUSIVE
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    verification_details: str = ""

class QARequest(BaseModel):
    question: str
    document_id: Optional[str] = None
    jurisdiction: Optional[str] = "General / Unspecified"

class QAResponse(BaseModel):
    question: str
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    provenance: List[ProvenanceRecord] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    multi_hop: bool = False
    graph_path: List[str] = Field(default_factory=list)
    reasoning_steps: List[str] = Field(default_factory=list)
    jurisdiction_note: str = "This analysis may depend on applicable jurisdiction; consider discussing with a qualified legal professional."
    disclaimer: str = "This is an informational analysis, not a legal determination."

class DocumentAnalysisResponse(BaseModel):
    document_id: str
    document_name: str
    document_type: str
    total_clauses: int
    clauses: List[ClauseNode]
    graph_edges: List[GraphEdge]
    conflicts: List[ContractConflict]
    timeline: List[TimelineEvent]
    questions_for_lawyer: List[str]
    overall_summary: str
    raw_text: str
    jurisdiction_note: str = "LexPilot produces informational flags, not legal determinations. Always consult a qualified attorney for legal advice."

class MultiHopQueryRequest(BaseModel):
    document_id: str
    start_clause_id: str
    target_clause_id: Optional[str] = None
    query: str
