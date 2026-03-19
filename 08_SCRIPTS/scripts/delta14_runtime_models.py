from __future__ import annotations
from typing import List, Optional, Literal, Any, Dict
from pydantic import BaseModel, Field

class ProvenanceJump(BaseModel):
    hints: List[str] = Field(default_factory=list)

class TranscriptQuotePreview(BaseModel):
    preview_id: str
    quote_id: str
    lane: Optional[str] = None
    file_path: str
    page: int
    line: int
    pinpoint: str
    score: float
    candidate_text: str
    reasons: List[str] = Field(default_factory=list)
    truth_tag: str = "UNVERIFIED"
    promotion_stage: Literal["PREVIEW_READY","EXACT_READY"]
    provenance_jump_hints: List[str] = Field(default_factory=list)
    resolution_target: Optional[str] = None

class TranscriptQuotePromotionsPayload(BaseModel):
    generated_at: str
    summary: Dict[str, Any]
    promotions: List[Dict[str, Any]] = Field(default_factory=list)
    resolution_targets: List[str] = Field(default_factory=list)

class ServiceArtifactParseRow(BaseModel):
    artifact_id: str
    file_path: str
    artifact_name: str
    artifact_type: str
    page_count: int = 1
    is_seed_artifact: bool = False
    service_ids_detected: List[str] = Field(default_factory=list)
    order_ids_detected: List[str] = Field(default_factory=list)
    case_ids_detected: List[str] = Field(default_factory=list)
    served_dates_detected: List[str] = Field(default_factory=list)
    channels_detected: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    snippet: Optional[str] = None
    parse_confidence: float = 0.0
    promotion_readiness: Literal["READY","WATCH","SEED_ONLY"]
    provenance_jump_hints: List[str] = Field(default_factory=list)

class ServiceArtifactPromotionsPayload(BaseModel):
    generated_at: str
    summary: Dict[str, Any]
    promotions: List[Dict[str, Any]] = Field(default_factory=list)

class DocketImportedEntry(BaseModel):
    entry_id: str
    kind: str
    case_id: Optional[str] = None
    date: Optional[str] = None
    title: str
    lane: Optional[str] = None
    source_ref: str
    raw_row: Dict[str, Any]
    provenance_jump_hints: List[str] = Field(default_factory=list)

class LiveDocketImportRun(BaseModel):
    run_id: str
    generated_at: str
    files_processed: List[Dict[str, Any]] = Field(default_factory=list)
    imported_entry_count: int = 0
    delta_counts: Dict[str, int] = Field(default_factory=dict)
    deadline_candidate_count: int = 0
    resolution_targets: List[str] = Field(default_factory=list)

class DocketDeadlineCandidate(BaseModel):
    deadline_id: str
    source_entry_id: str
    due_date_iso: str
    title: str
    status: str
    deadline_kind: str
    truth_tag: str = "INFERRED"
    basis: str
    provenance_jump_hints: List[str] = Field(default_factory=list)
