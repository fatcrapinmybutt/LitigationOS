from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Mapping, TypeAlias


# -----------------------------------------------------------------------------
# Logging configuration
# -----------------------------------------------------------------------------

logger = logging.getLogger("litigation_os")
if not logger.handlers:
    # Basic, quiet-by-default logger; callers can reconfigure if desired.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )


# -----------------------------------------------------------------------------
# Core Enums
# -----------------------------------------------------------------------------

class FileRole(Enum):
    UNKNOWN = auto()
    PLEADING = auto()
    ORDER = auto()
    TRANSCRIPT = auto()
    POLICE_REPORT = auto()
    APP_LOG = auto()
    MEDICAL = auto()
    HOUSING = auto()
    FINANCIAL = auto()
    CORRESPONDENCE = auto()
    EVIDENCE_MEDIA = auto()
    MEMO_OR_NOTE = auto()


class CitationType(Enum):
    MCR = auto()
    MCL = auto()
    CASE_LAW = auto()
    BENCHBOOK = auto()
    SCAO_FORM = auto()
    OTHER = auto()


class EventDomain(Enum):
    GENERIC = auto()
    CUSTODY = auto()
    PPO = auto()
    HOUSING = auto()
    FOIA = auto()
    MENTAL_HEALTH = auto()
    APPEAL = auto()
    CONTEMPT = auto()
    CHILD_SUPPORT = auto()
    CIVIL_RIGHTS = auto()


class MotionType(Enum):
    GENERIC = auto()
    CUSTODY_MODIFICATION = auto()
    PARENTING_TIME_ENFORCEMENT = auto()
    PPO_DISMISSAL_OR_DEFENSE = auto()
    CONTEMPT_DEFENSE = auto()
    JUDICIAL_DISQUALIFICATION = auto()
    COA_APPLICATION = auto()
    EMERGENCY_STAY = auto()
    HOUSING_REMEDY = auto()
    FOIA_ENFORCEMENT = auto()


class HealthStatus(Enum):
    OK = auto()
    WARNING = auto()
    ERROR = auto()
    UNKNOWN = auto()


class StrategyImpactLevel(Enum):
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    EXTREME = auto()


class ModuleStatus(Enum):
    REGISTERED = auto()
    ACTIVE = auto()
    DISABLED = auto()
    ERROR = auto()


# -----------------------------------------------------------------------------
# Core data structures
# -----------------------------------------------------------------------------

@dataclass
class FileRecord:
    """Physical file on disk or remote storage."""
    path: Path
    size_bytes: int
    modified_at: datetime
    file_type: str
    case_hint: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocRecord:
    """Logical document, possibly backed by one or more files."""
    doc_id: str
    file: FileRecord
    text: str
    page_count: int
    created_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocSection:
    """Labeled section of a structured legal document."""
    section_type: str  # e.g. CAPTION, HISTORY, FINDINGS, ORDERS, EXHIBITS
    heading: Optional[str]
    text: str
    page_start: int
    page_end: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StructuredDoc:
    """Document split into typed sections."""
    doc: DocRecord
    sections: List[DocSection]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LegalEntitySet:
    """Entities extracted from text."""
    parties: List[str] = field(default_factory=list)
    judges: List[str] = field(default_factory=list)
    courts: List[str] = field(default_factory=list)
    addresses: List[str] = field(default_factory=list)
    statutes: List[str] = field(default_factory=list)
    rules: List[str] = field(default_factory=list)
    dates: List[datetime] = field(default_factory=list)
    other_entities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Citation:
    raw_text: str
    normalized: str
    citation_type: CitationType
    source_doc_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


CitationSet: TypeAlias = List[Citation]


@dataclass
class Event:
    event_id: str
    occurred_at: Optional[datetime]
    case_id: Optional[str]
    description: str
    parties: List[str]
    domain: EventDomain = EventDomain.GENERIC
    source_doc_id: Optional[str] = None
    source_section_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FindingOrOrder:
    item_id: str
    doc_id: str
    kind: str  # FINDING or ORDER, or more granular string
    index: int
    text: str
    citations: CitationSet = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FactRuleLink:
    event_id: str
    rule_id: str  # e.g. "MCR 2.003(C)(1)"
    strength: float  # 0–1 confidence
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FactStatuteLink:
    event_id: str
    statute_id: str  # e.g. "MCL 722.27a"
    strength: float
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchbookFactorEvaluation:
    factor_id: str  # e.g. "BestInterest(a)"
    label: str
    support_events: List[str] = field(default_factory=list)
    oppose_events: List[str] = field(default_factory=list)
    net_assessment: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


BenchbookMatrix: TypeAlias = List[BenchbookFactorEvaluation]


@dataclass
class RuleCheckResult:
    rule_id: str
    passed: bool
    severity: Optional[str] = None  # e.g. "INFO", "WARNING", "CRITICAL"
    details: str = ""
    related_events: List[str] = field(default_factory=list)
    related_orders: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ViolationIndex:
    rule_results: List[RuleCheckResult]
    overall_risk_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


VectorIndexId: TypeAlias = str


@dataclass
class QuerySpec:
    text: str
    case_filter: Optional[List[str]] = None
    domain_filter: Optional[List[EventDomain]] = None
    date_range: Optional[Sequence[datetime]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvidenceItem:
    item_id: str
    description: str
    source_doc_id: Optional[str]
    path: Optional[Path]
    page_range: Optional[Sequence[int]] = None
    score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvidenceBundle:
    query: QuerySpec
    items: List[EvidenceItem]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DraftDoc:
    doc_id: str
    title: str
    case_id: Optional[str]
    text: str
    motion_type: Optional[MotionType] = None
    created_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExhibitEntry:
    exhibit_id: str
    title: str
    date: Optional[datetime]
    path: Path
    description: str = ""
    page_count: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExhibitIndex:
    case_id: Optional[str]
    entries: List[ExhibitEntry]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FilledForm:
    form_id: str
    case_id: Optional[str]
    output_path: Path
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BundleArtifact:
    bundle_id: str
    case_id: Optional[str]
    root_path: Path
    files: List[Path]
    manifest: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DraftIssue:
    issue_id: str
    description: str
    severity: str  # e.g. "MINOR", "MAJOR", "BLOCKER"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DraftWithIssues:
    draft: DraftDoc
    issues: List[DraftIssue]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CaseState:
    case_id: str
    caption: str
    judge_name: Optional[str]
    domain: EventDomain
    last_updated: datetime
    key_orders: List[str] = field(default_factory=list)
    key_events: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyOption:
    option_id: str
    label: str
    description: str
    impact: StrategyImpactLevel
    estimated_effort: str  # e.g. "LOW", "MEDIUM", "HIGH"
    risk_notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class JudgeProfile:
    judge_name: str
    court: Optional[str]
    patterns: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResponseForecast:
    likelihood_grant: float
    likelihood_deny: float
    likelihood_no_action: float
    reasoning_summary: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HarmItem:
    harm_id: str
    description: str
    domain: EventDomain
    severity: StrategyImpactLevel
    related_events: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HarmReport:
    case_id: Optional[str]
    harms: List[HarmItem]
    total_weighted_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RemoteSpec:
    name: str
    root: Path
    kind: str  # e.g. "LOCAL", "RCLONE", "NETWORK"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SyncItem:
    path: Path
    action: str  # e.g. "COPIED", "SKIPPED", "UPDATED"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SyncReport:
    remotes: List[RemoteSpec]
    items: List[SyncItem]
    started_at: datetime
    finished_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ActionRecord:
    timestamp: datetime
    case_id: Optional[str]
    actor: str  # e.g. "SYSTEM", "USER"
    action_type: str  # e.g. "GENERATE_MOTION", "EXPORT_BUNDLE"
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthSnapshot:
    status: HealthStatus
    timestamp: datetime
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgePack:
    case_id: Optional[str]
    export_path: Path
    manifest: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModuleSpec:
    module_id: str
    name: str
    version: str
    status: ModuleStatus
    description: str = ""
    inputs: Mapping[str, str] = field(default_factory=dict)
    outputs: Mapping[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


# Type aliases for backing stores; concrete implementations live elsewhere.
TimelineStore: TypeAlias = Any
GraphStore: TypeAlias = Any
RulesStore: TypeAlias = Any
CanonStore: TypeAlias = Any


# -----------------------------------------------------------------------------
# API function signatures
# -----------------------------------------------------------------------------

def discover_evidence_sources(root_paths: List[Path]) -> List[FileRecord]:
    """
    Recursively discover files under the given root paths and return FileRecord
    entries suitable for downstream ingestion.
    """
    raise NotImplementedError


def classify_file_role(file: FileRecord) -> FileRole:
    """
    Infer the high-level legal role for a file (pleading, order, transcript, etc.).
    """
    raise NotImplementedError


def ocr_and_ingest_pdf(file: FileRecord) -> DocRecord:
    """
    OCR (if needed) and ingest a PDF, returning a DocRecord with normalized text.
    """
    raise NotImplementedError


def extract_text_and_metadata(file: FileRecord) -> DocRecord:
    """
    Extract text and metadata from PDF/DOCX/TXT/HTML into a DocRecord.
    """
    raise NotImplementedError


def normalize_document_structure(doc: DocRecord) -> StructuredDoc:
    """
    Split a document into caption, history, findings, orders, and other sections.
    """
    raise NotImplementedError


def segment_legal_sentences(text: str) -> List[str]:
    """
    Split legal text into sentences, respecting citations and abbreviations.
    """
    raise NotImplementedError


def extract_legal_entities(text: str) -> LegalEntitySet:
    """
    Extract parties, judges, courts, addresses, statutes, rules, dates, and
    other entities from raw text.
    """
    raise NotImplementedError


def detect_michigan_citations(text: str) -> CitationSet:
    """
    Detect and normalize Michigan citations (MCR, MCL, case law, Benchbooks,
    SCAO forms) in the given text.
    """
    raise NotImplementedError


def extract_events_from_document(doc: StructuredDoc) -> List[Event]:
    """
    Convert a StructuredDoc into a sequence of fact events with dates and parties.
    """
    raise NotImplementedError


def tag_event_domains(events: List[Event]) -> List[Event]:
    """
    Label each event with its primary domain (custody, PPO, housing, etc.).
    """
    raise NotImplementedError


def extract_ordered_findings_and_orders(doc: StructuredDoc) -> List[FindingOrOrder]:
    """
    Extract numbered findings of fact and orders from a StructuredDoc.
    """
    raise NotImplementedError


def upsert_timeline_events(events: List[Event], timeline_db: TimelineStore) -> None:
    """
    Insert or update events in the global litigation timeline store.
    """
    raise NotImplementedError


def upsert_case_graph_nodes_edges(
    events: List[Event],
    citations: CitationSet,
    graph_db: GraphStore,
) -> None:
    """
    Create/merge graph nodes and edges for events, parties, cases, orders,
    and citations in the case knowledge graph.
    """
    raise NotImplementedError


def compute_violation_edges(graph_db: GraphStore) -> None:
    """
    Analyze the graph and add edges representing potential violations
    (rule breaches, due-process issues, canon concerns).
    """
    raise NotImplementedError


def build_vector_index_for_docs(docs: List[DocRecord]) -> VectorIndexId:
    """
    Build a semantic vector index for the given documents and return its ID.
    """
    raise NotImplementedError


def retrieve_relevant_evidence(
    query: QuerySpec,
    graph_db: GraphStore,
    vector_index: VectorIndexId,
) -> EvidenceBundle:
    """
    Perform hybrid retrieval (graph + keyword + vector) to assemble a targeted
    bundle of evidence answering the query.
    """
    raise NotImplementedError


def map_facts_to_mcr_rules(events: List[Event]) -> List[FactRuleLink]:
    """
    Link fact events to implicated Michigan Court Rules (MCR).
    """
    raise NotImplementedError


def map_facts_to_mcl_statutes(events: List[Event]) -> List[FactStatuteLink]:
    """
    Link fact events to implicated Michigan Compiled Laws (MCL) statutes.
    """
    raise NotImplementedError


def map_facts_to_benchbook_factors(events: List[Event]) -> BenchbookMatrix:
    """
    Evaluate fact events against relevant Michigan Benchbook factors.
    """
    raise NotImplementedError


def evaluate_mcr_compliance(
    timeline: TimelineStore,
    orders: Sequence[FindingOrOrder],
    rules_db: RulesStore,
) -> List[RuleCheckResult]:
    """
    Evaluate the timeline and orders for procedural compliance with MCR.
    """
    raise NotImplementedError


def score_canon_and_due_process_risks(
    timeline: TimelineStore,
    orders: Sequence[FindingOrOrder],
    canon_db: CanonStore,
) -> ViolationIndex:
    """
    Score potential canon and due-process issues, returning a violation index.
    """
    raise NotImplementedError


def generate_motion_from_graph(
    graph_slice: GraphStore,
    motion_type: MotionType,
) -> DraftDoc:
    """
    Generate a draft motion or response grounded in a selected portion of the
    knowledge graph.
    """
    raise NotImplementedError


def generate_affidavit_from_events(
    events: List[Event],
    perspective_party: str,
) -> DraftDoc:
    """
    Turn selected events into a numbered affidavit for the given party.
    """
    raise NotImplementedError


def generate_exhibit_index(evidence_bundle: EvidenceBundle) -> ExhibitIndex:
    """
    Generate an exhibit index from a bundle of evidence items.
    """
    raise NotImplementedError


def autofill_scao_form(form_id: str, data: Dict[str, Any]) -> FilledForm:
    """
    Populate a Michigan SCAO/MC/FOC form overlay from structured data.
    """
    raise NotImplementedError


def generate_mifile_ready_bundle(
    filings: List[DraftDoc],
    exhibits: ExhibitIndex,
) -> BundleArtifact:
    """
    Assemble filings and exhibits into a deterministic, MiFile-ready bundle.
    """
    raise NotImplementedError


def run_michigan_compliance_checks_on_draft(draft: DraftDoc) -> DraftWithIssues:
    """
    Run Michigan-specific compliance checks on a draft document and annotate
    any issues that must be fixed before filing.
    """
    raise NotImplementedError


def rank_legal_strategies(
    current_state: CaseState,
    violation_index: ViolationIndex,
) -> List[StrategyOption]:
    """
    Rank candidate legal strategies for the current case, based on violations,
    harms, and posture.
    """
    raise NotImplementedError


def simulate_judicial_response(
    draft: DraftDoc,
    judge_profile: JudgeProfile,
) -> ResponseForecast:
    """
    Forecast likely judicial responses to a given draft filing.
    """
    raise NotImplementedError


def compute_actionable_harm_index(
    timeline: TimelineStore,
    violation_index: ViolationIndex,
) -> HarmReport:
    """
    Compute an actionable harm report from timeline events and violations.
    """
    raise NotImplementedError


def sync_remote_and_local_evidence(remotes: List[RemoteSpec]) -> SyncReport:
    """
    Synchronize evidence between local drives and remote stores, returning
    a detailed sync report.
    """
    raise NotImplementedError


def log_litigation_action(action: ActionRecord) -> None:
    """
    Append a litigation action to the audit trail.
    """
    raise NotImplementedError


def monitor_litigation_os_health() -> HealthSnapshot:
    """
    Capture a snapshot of system health for dashboards and alerts.
    """
    raise NotImplementedError


def export_case_knowledge_pack(case_id: str) -> KnowledgePack:
    """
    Export a structured knowledge pack for a given case (JSON/CSV/manifest).
    """
    raise NotImplementedError


def register_new_module_capability(module_spec: ModuleSpec) -> None:
    """
    Register a new module's capabilities and IO contract with the Litigation OS.
    """
    raise NotImplementedError


# -----------------------------------------------------------------------------
# Introspection helpers
# -----------------------------------------------------------------------------

def list_public_api_functions() -> List[str]:
    """
    Return a list of public API function names exposed by this module.
    """
    return [
        "discover_evidence_sources",
        "classify_file_role",
        "ocr_and_ingest_pdf",
        "extract_text_and_metadata",
        "normalize_document_structure",
        "segment_legal_sentences",
        "extract_legal_entities",
        "detect_michigan_citations",
        "extract_events_from_document",
        "tag_event_domains",
        "extract_ordered_findings_and_orders",
        "upsert_timeline_events",
        "upsert_case_graph_nodes_edges",
        "compute_violation_edges",
        "build_vector_index_for_docs",
        "retrieve_relevant_evidence",
        "map_facts_to_mcr_rules",
        "map_facts_to_mcl_statutes",
        "map_facts_to_benchbook_factors",
        "evaluate_mcr_compliance",
        "score_canon_and_due_process_risks",
        "generate_motion_from_graph",
        "generate_affidavit_from_events",
        "generate_exhibit_index",
        "autofill_scao_form",
        "generate_mifile_ready_bundle",
        "run_michigan_compliance_checks_on_draft",
        "rank_legal_strategies",
        "simulate_judicial_response",
        "compute_actionable_harm_index",
        "sync_remote_and_local_evidence",
        "log_litigation_action",
        "monitor_litigation_os_health",
        "export_case_knowledge_pack",
        "register_new_module_capability",
    ]


__all__ = [
    # Enums
    "FileRole",
    "CitationType",
    "EventDomain",
    "MotionType",
    "HealthStatus",
    "StrategyImpactLevel",
    "ModuleStatus",
    # Data classes
    "FileRecord",
    "DocRecord",
    "DocSection",
    "StructuredDoc",
    "LegalEntitySet",
    "Citation",
    "Event",
    "FindingOrOrder",
    "FactRuleLink",
    "FactStatuteLink",
    "BenchbookFactorEvaluation",
    "RuleCheckResult",
    "ViolationIndex",
    "QuerySpec",
    "EvidenceItem",
    "EvidenceBundle",
    "DraftDoc",
    "ExhibitEntry",
    "ExhibitIndex",
    "FilledForm",
    "BundleArtifact",
    "DraftIssue",
    "DraftWithIssues",
    "CaseState",
    "StrategyOption",
    "JudgeProfile",
    "ResponseForecast",
    "HarmItem",
    "HarmReport",
    "RemoteSpec",
    "SyncItem",
    "SyncReport",
    "ActionRecord",
    "HealthSnapshot",
    "KnowledgePack",
    "ModuleSpec",
    # Type aliases
    "CitationSet",
    "BenchbookMatrix",
    "VectorIndexId",
    "TimelineStore",
    "GraphStore",
    "RulesStore",
    "CanonStore",
    # Functions
    "discover_evidence_sources",
    "classify_file_role",
    "ocr_and_ingest_pdf",
    "extract_text_and_metadata",
    "normalize_document_structure",
    "segment_legal_sentences",
    "extract_legal_entities",
    "detect_michigan_citations",
    "extract_events_from_document",
    "tag_event_domains",
    "extract_ordered_findings_and_orders",
    "upsert_timeline_events",
    "upsert_case_graph_nodes_edges",
    "compute_violation_edges",
    "build_vector_index_for_docs",
    "retrieve_relevant_evidence",
    "map_facts_to_mcr_rules",
    "map_facts_to_mcl_statutes",
    "map_facts_to_benchbook_factors",
    "evaluate_mcr_compliance",
    "score_canon_and_due_process_risks",
    "generate_motion_from_graph",
    "generate_affidavit_from_events",
    "generate_exhibit_index",
    "autofill_scao_form",
    "generate_mifile_ready_bundle",
    "run_michigan_compliance_checks_on_draft",
    "rank_legal_strategies",
    "simulate_judicial_response",
    "compute_actionable_harm_index",
    "sync_remote_and_local_evidence",
    "log_litigation_action",
    "monitor_litigation_os_health",
    "export_case_knowledge_pack",
    "register_new_module_capability",
    "list_public_api_functions",
]


# -----------------------------------------------------------------------------
# Setup & usage (for humans)
# -----------------------------------------------------------------------------
# Save this file as `litigation_os_api.py`.
# Requirements: Python 3.10+; only standard library is used.
# Example:
#   from pathlib import Path
#   from litigation_os_api import discover_evidence_sources
#
#   roots = [Path("F:/"), Path("D:/")]
#   # Implement discover_evidence_sources in your engine and call it here.
#
if __name__ == "__main__":
    logger.info("litigation_os_api interface loaded.")
    logger.info("Public API functions: %s", ", ".join(list_public_api_functions()))
