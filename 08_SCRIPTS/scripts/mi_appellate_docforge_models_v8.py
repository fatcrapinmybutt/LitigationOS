from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal, Optional, List, Dict
from datetime import datetime

TruthTag = Literal["PROVEN","RECORD-RECITED","USER_ASSERTED","INFERRED","UNVERIFIED","DISPUTED"]

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
    kind: Literal["pdf","docx","txt","email","image","audio","video","other"]
    lane: Literal["MEEK1","MEEK2","MEEK3","MEEK4","UNKNOWN"] = "UNKNOWN"
    case_id: Optional[str] = None
    discovered_at_utc: datetime
    labels: List[str] = Field(default_factory=list)
    truth_tag: TruthTag = "UNVERIFIED"

class Pinpoint(BaseModel):
    scheme: Literal["pdf_page","docx_para","text_line","text_span","timecode","unknown"] = "unknown"
    value: str
    confidence: float = 0.0

class QuoteAtom(BaseModel):
    quote_id: str
    atom_id: str
    text: str
    truth_tag: TruthTag = "UNVERIFIED"
    pinpoint: Optional[Pinpoint] = None
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    actors: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)

class EventAtom(BaseModel):
    event_id: str
    when_event_utc: Optional[datetime] = None
    when_recorded_utc: Optional[datetime] = None
    lane: Literal["MEEK1","MEEK2","MEEK3","MEEK4","UNKNOWN"] = "UNKNOWN"
    case_id: Optional[str] = None
    actor: Optional[str] = None
    action: str
    object: Optional[str] = None
    support_quote_ids: List[str] = Field(default_factory=list)
    truth_tag: TruthTag = "UNVERIFIED"

class AuthorityTriple(BaseModel):
    proposition_id: str
    proposition_text: str
    authority_family: Literal["MCR","MCL","MRE","MJI_BENCHBOOK","SCAO_FORM","LOCAL_RULE","CASELAW","OTHER"]
    citation_stub: str
    pinpoint: Optional[str] = None
    status: Literal["VERIFY_PINPOINT","VERIFIED","DRAFT"] = "VERIFY_PINPOINT"

class AcquisitionTask(BaseModel):
    task_id: str
    purpose: str
    requested_item: str
    source_hint: str
    blocking: bool = False

class Pack(BaseModel):
    pack_id: str
    purpose: Literal[
        "timeline","rebuttal_map","contradiction_map","vehicle_selection","trial_set",
        "coa_set","msc_set","jtc_set","motion_draft","affidavit_draft","exhibit_matrix"
    ]
    lane: Literal["MEEK1","MEEK2","MEEK3","MEEK4"]
    case_id: Optional[str] = None
    created_at_utc: datetime
    scope: Dict[str, str] = Field(default_factory=dict)
    quote_ids: List[str] = Field(default_factory=list)
    event_ids: List[str] = Field(default_factory=list)
    authority_triples: List[AuthorityTriple] = Field(default_factory=list)
    acquisition_tasks: List[AcquisitionTask] = Field(default_factory=list)
    synthesis_instructions: str

class CourtPackManifest(BaseModel):
    pack_id: str
    lane: str
    vehicle: str
    created_at_utc: datetime
    files: List[str]
    readiness: Literal["DRAFT_DROPIN_READY","FACT_COMPLETE_READY","FILE_READY"] = "DRAFT_DROPIN_READY"
    warnings: List[str] = Field(default_factory=list)
