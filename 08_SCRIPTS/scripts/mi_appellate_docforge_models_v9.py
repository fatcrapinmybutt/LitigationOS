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

class FastSigV1(BaseModel):
    algo: Literal["xxh3_sampled"] = "xxh3_sampled"
    first_kb: int = 64
    last_kb: int = 64
    sig_hex: str

class FileAtom(BaseModel):
    atom_id: str
    identity: IdentityKeyV1
    ext: str
    kind: Literal["pdf","docx","txt","email","image","audio","video","other"]
    lane: Literal["MEEK1","MEEK2","MEEK3","MEEK4","UNKNOWN"] = "UNKNOWN"
    case_id: Optional[str] = None
    labels: List[str] = Field(default_factory=list)
    discovered_at_utc: datetime
    truth_tag: TruthTag = "UNVERIFIED"

class ExtractionAtom(BaseModel):
    atom_id: str
    extractor: Literal["txt","docx","pdf_text","pdf_ocr","email","image_ocr","audio_asr","video_asr","other"]
    extracted_at_utc: datetime
    text_path: str
    char_count: int
    warnings: List[str] = Field(default_factory=list)

class Pinpoint(BaseModel):
    scheme: Literal["pdf_page","docx_para","line_range","char_span","timecode","unknown"] = "unknown"
    value: str
    confidence: float = 0.0

class QuoteAtom(BaseModel):
    quote_id: str
    atom_id: str
    text: str
    start: int
    end: int
    pinpoint: Optional[Pinpoint] = None
    truth_tag: TruthTag = "UNVERIFIED"
    relevance: float = 0.0

class EventAtom(BaseModel):
    event_id: str
    lane: Literal["MEEK1","MEEK2","MEEK3","MEEK4","UNKNOWN"] = "UNKNOWN"
    case_id: Optional[str] = None
    actor: Optional[str] = None
    action: str
    obj: Optional[str] = None
    when_event_utc: Optional[datetime] = None
    when_recorded_utc: Optional[datetime] = None
    support_quotes: List[str] = Field(default_factory=list)
    truth_tag: TruthTag = "UNVERIFIED"

class AuthorityTriple(BaseModel):
    issue_key: str
    authority_family: str
    authority_cite: str
    proposition: str
    source_url: Optional[str] = None
    status: Literal["RESOLVED_VERIFIED","RESOLVED_UNVERIFIED","NEEDS_PINPOINT"] = "NEEDS_PINPOINT"

class Pack(BaseModel):
    pack_id: str
    purpose: Literal[
        "timeline","rebuttal_map","contradiction_map","motion_draft","affidavit_draft","coa_packet","msc_packet","jtc_packet"
    ]
    scope: Dict[str,str]
    created_at_utc: datetime
    query_text: str
    quotes: List[QuoteAtom] = Field(default_factory=list)
    events: List[EventAtom] = Field(default_factory=list)
    authority_triples: List[AuthorityTriple] = Field(default_factory=list)
    synthesis_instructions: str

class CourtPackManifest(BaseModel):
    courtpack_id: str
    lane: str
    vehicle: str
    court_level: Literal["TRIAL","COA","MSC","JTC","OTHER"]
    generated_at_utc: datetime
    source_pack_ids: List[str] = Field(default_factory=list)
    included_files: List[str] = Field(default_factory=list)
    known_gaps: List[str] = Field(default_factory=list)
