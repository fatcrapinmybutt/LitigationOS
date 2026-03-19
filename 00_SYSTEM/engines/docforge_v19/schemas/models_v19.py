from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, Literal

TruthTag = Literal["PROVEN","RECORD_RECITED","USER_ASSERTED","INFERRED","UNKNOWN","DISPUTED"]
GraftStatus = Literal["UNRESOLVED","PARTIAL","RESOLVED_VERIFIED"]
LockStatus = Literal["LOCKED","MISSING_ANCHOR","RULE_MISSING","PENDING_VERIFY"]

class AuthorityTriple(BaseModel):
    authority_id: str
    lane: Optional[str] = None
    citation: str
    normalized_citation: str
    proposition: Optional[str] = None
    source_url: Optional[str] = None
    source_url_status: str = "UNRESOLVED"
    official_text_exact: Optional[str] = None
    pinpoint: Optional[str] = None
    pinpoint_status: str = "UNRESOLVED"
    graft_status: GraftStatus = "UNRESOLVED"

class TranscriptRow(BaseModel):
    transcript_row_id: str
    transcript_id: str
    page: Optional[int] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    speaker: Optional[str] = None
    text: str
    issue_tag: Optional[str] = None

class DeadlineRule(BaseModel):
    rule_id: str
    lane: Optional[str] = None
    vehicle_code: str
    forum: str
    anchor_type: Literal["entered","signed","served","recorded"]
    trigger_event: str
    due_days: Optional[int] = None
    business_days_only: bool = False
    tolling_notes: Optional[str] = None
    authority_citation: Optional[str] = None
    rule_status: str = "UNVERIFIED_TEMPLATE"

class DeadlineLock(BaseModel):
    lock_id: str
    event_id: str
    rule_id: str
    anchor_type: str
    anchor_date: Optional[str] = None
    due_date: Optional[str] = None
    lock_status: LockStatus
    tolling_notes: Optional[str] = None
