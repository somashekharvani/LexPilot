"""
LexPilot - Legal Intermediate Representation (Legal-IR) Models
--------------------------------------------------------------
Canonical structured representation for legal clauses:
  Clause
  ├── identity: clause_id, section, page
  ├── semantic: category, parties, defined_terms
  ├── obligations: actor, action, object, deadline
  ├── conditions
  ├── exceptions
  ├── references (other clause_ids this clause points to)
  ├── survival (does this clause survive termination? which trigger?)
  └── evidence_span (page, char_start, char_end — exact source location)
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ClauseIdentity(BaseModel):
    clause_id: str
    section: str
    page: int = 1
    line_start: int = 0
    line_end: int = 0

class ClauseSemantic(BaseModel):
    category: str
    parties: List[str] = Field(default_factory=list)
    defined_terms: List[str] = Field(default_factory=list)
    monetary_amounts: List[str] = Field(default_factory=list)
    dates: List[str] = Field(default_factory=list)

class ObligationItem(BaseModel):
    actor: str = "Party"
    action: str = ""
    object: str = ""
    deadline: Optional[str] = None
    original_text: str = ""

class ConditionItem(BaseModel):
    trigger: str
    consequence: str = ""

class ExceptionItem(BaseModel):
    description: str

class SurvivalInfo(BaseModel):
    survives: bool = False
    trigger: Optional[str] = None
    surviving_clauses: List[str] = Field(default_factory=list)
    duration: Optional[str] = None

class EvidenceSpan(BaseModel):
    page: int = 1
    char_start: int = 0
    char_end: int = 0
    text_snippet: str = ""

class LegalIRClause(BaseModel):
    identity: ClauseIdentity
    semantic: ClauseSemantic
    obligations: List[ObligationItem] = Field(default_factory=list)
    conditions: List[ConditionItem] = Field(default_factory=list)
    exceptions: List[ExceptionItem] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list)
    survival: SurvivalInfo = Field(default_factory=SurvivalInfo)
    evidence_span: EvidenceSpan = Field(default_factory=EvidenceSpan)
    raw_text: str = ""
