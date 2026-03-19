from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal

TruthTag = Literal["PROVEN","RECORD_RECITED","USER_ASSERTED","INFERRED","UNVERIFIED","DISPUTED"]

class ProvenanceRef(BaseModel):
    source_kind: str
    locator: str
    excerpt: Optional[str] = None

class DiscoveryTarget(BaseModel):
    title: str
    lane: str
    priority: Literal["critical","high","medium","low"] = "medium"
    rationale: str
    fulfillment_signal: Optional[str] = None

class ResolutionTarget(BaseModel):
    title: str
    lane: str
    priority: Literal["critical","high","medium","low"] = "high"
    completion_signal: str
    supporting_discovery_targets: List[str] = Field(default_factory=list)

class EvidenceAtom(BaseModel):
    atom_id: str
    lane: str
    truth_tag: TruthTag
    summary: str
    provenance: List[ProvenanceRef] = Field(default_factory=list)
    linked_order_ids: List[str] = Field(default_factory=list)
    linked_event_ids: List[str] = Field(default_factory=list)

class AuthorityTriple(BaseModel):
    proposition: str
    authority_cite: str
    pinpoint: Optional[str] = None
    lane: Optional[str] = None
    confidence_note: Optional[str] = None

class VehicleReadinessRow(BaseModel):
    vehicle_id: str
    title: str
    lane: str
    ccs_score: float = Field(ge=0, le=1)
    sbna_score: float = Field(ge=0, le=100)
    readiness_band: Literal["A","B","C","D","E"]
    component_scores: Dict[str, float] = Field(default_factory=dict)
    top_resolution_targets: List[str] = Field(default_factory=list)
    top_discovery_targets: List[str] = Field(default_factory=list)
    status: str

class WidgetState(BaseModel):
    widget_id: str
    visible: bool = True
    lane_filter: List[str] = Field(default_factory=list)
    truth_filter: List[TruthTag] = Field(default_factory=list)

class CommandCenterState(BaseModel):
    directive_name: str
    cycle_index: int
    delta_level: int
    convergence_score: float = Field(ge=0, le=1)
    emergence_score: float = Field(ge=0, le=1)
    discovery_targets: List[DiscoveryTarget] = Field(default_factory=list)
    resolution_targets: List[ResolutionTarget] = Field(default_factory=list)
    evidence_atoms: List[EvidenceAtom] = Field(default_factory=list)
    authority_triples: List[AuthorityTriple] = Field(default_factory=list)
    vehicle_readiness: List[VehicleReadinessRow] = Field(default_factory=list)
    widgets: List[WidgetState] = Field(default_factory=list)
