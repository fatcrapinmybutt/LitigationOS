from __future__ import annotations
from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, Field

TruthTag = Literal["PROVEN","RECORD_RECITED","USER_ASSERTED","INFERRED","UNVERIFIED","DISPUTED"]

class FileAtom(BaseModel):
    atom_id: str
    source_path_norm: str
    bytes_size: int
    mtime_utc: str
    ctime_utc: Optional[str] = None
    file_id: Optional[str] = None
    ext: Optional[str] = None
    kind: Optional[str] = None
    lane: str = "UNKNOWN"
    case_id: Optional[str] = None
    identity_key: str
    truth_tag: TruthTag = "UNVERIFIED"

class QuoteAtom(BaseModel):
    quote_id: str
    atom_id: str
    text: str
    start_pos: int
    end_pos: int
    pinpoint_scheme: str
    pinpoint_value: str
    page_hint: Optional[int] = None
    lane: str = "UNKNOWN"
    case_id: Optional[str] = None
    truth_tag: TruthTag = "UNVERIFIED"

class EventAtom(BaseModel):
    event_id: str
    atom_id: str
    action: str
    when_event_raw: Optional[str] = None
    when_event_utc: Optional[str] = None
    when_recorded_utc: str
    support_quote_ids_json: str = "[]"
    lane: str = "UNKNOWN"
    case_id: Optional[str] = None
    truth_tag: TruthTag = "UNVERIFIED"

class AuthorityTriple(BaseModel):
    issue: str
    authority: str
    pinpoint: str = "VERIFY_PINPOINT"
    status: str = "ACQUIRE"

class Pack(BaseModel):
    pack_id: str
    purpose: str
    created_at_utc: str
    scope: Dict[str, str]
    query: str
    quotes: List[QuoteAtom] = Field(default_factory=list)
    events: List[Dict] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)

class CourtPackManifest(BaseModel):
    courtpack_id: str
    lane: str
    case_id: Optional[str] = None
    forum: str
    vehicle: str
    pack_source: str
    generated_at_utc: str
    files: List[str]
