from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal, Optional, List, Dict
from datetime import datetime

TruthTag = Literal["PROVEN","RECORD-RECITED","USER-ASSERTED","INFERRED","UNVERIFIED","DISPUTED"]

class IdentityKeyV1(BaseModel):
    source_path_norm: str
    bytes_size: int
    mtime_utc: datetime
    ctime_utc: Optional[datetime] = None
    file_id: Optional[str] = None
    volume_serial: Optional[str] = None

class FileAtom(BaseModel):
    atom_id: str
    identity: IdentityKeyV1
    ext: str
    kind: str
    lane: str = "UNKNOWN"
    case_id: Optional[str] = None
    discovered_at_utc: datetime
    truth_tag: TruthTag = "UNVERIFIED"
    labels: List[str] = Field(default_factory=list)

class Pinpoint(BaseModel):
    scheme: str = "unknown"
    value: str = ""
    confidence: float = 0.0

class QuoteAtom(BaseModel):
    quote_id: str
    atom_id: str
    text: str
    start: int
    end: int
    truth_tag: TruthTag = "UNVERIFIED"
    pinpoint: Optional[Pinpoint] = None
    lane: str = "UNKNOWN"
    case_id: Optional[str] = None

class EventAtom(BaseModel):
    event_id: str
    atom_id: str
    action: str
    actor: Optional[str] = None
    object: Optional[str] = None
    when_event_utc: Optional[datetime] = None
    when_recorded_utc: Optional[datetime] = None
    truth_tag: TruthTag = "UNVERIFIED"
    support_quote_ids: List[str] = Field(default_factory=list)
    lane: str = "UNKNOWN"
    case_id: Optional[str] = None

class AuthorityTriple(BaseModel):
    proposition: str
    authority_type: Literal["MCR","MCL","MRE","MJI","MI_CONST","CASELAW","SCAO","LOCAL_RULE","UNKNOWN"] = "UNKNOWN"
    citation: str
    source_url: Optional[str] = None
    status: Literal["RESOLVED_VERIFIED","RESOLVED_UNVERIFIED","UNRESOLVED"] = "UNRESOLVED"

class Pack(BaseModel):
    pack_id: str
    purpose: str
    created_at_utc: datetime
    scope: Dict[str, str]
    query: str
    quote_ids: List[str]
    event_ids: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)

class CourtPackManifest(BaseModel):
    courtpack_id: str
    lane: str
    case_id: Optional[str] = None
    forum: Literal["TRIAL","COA","MSC","JTC"] = "TRIAL"
    generated_at_utc: datetime
    pack_id: Optional[str] = None
    files: List[str] = Field(default_factory=list)
