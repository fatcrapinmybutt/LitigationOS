"""LitigationOS Structured Output Contracts — Pydantic v2 Models.

Purpose:  Typed, validated schemas for all filing assembly outputs.
          Ensures court documents are structurally correct before filing.
Inputs:   Raw dicts from filing modules (motion_generator, brief_builder, etc.)
Outputs:  Validated Pydantic models with JSON Schema export.
Failure:  ValidationError with field-level details; never silently drops data.
Paths:    Imported by pipeline modules, skills, and filing assemblers.

Usage::

    from litigation_contracts import (
        FilingCaption, MotionOutput, AppellateBrief,
        CitationAudit, ComplianceResult, FilingPackage,
    )

    # Validate a motion output
    motion = MotionOutput.model_validate(raw_dict)

    # Export JSON Schema for desktop app
    schema = FilingPackage.model_json_schema()
"""
from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════════

class CaseLane(str, Enum):
    """Six case lanes — IRON LAW: never cross-contaminate."""
    A = "A"  # Watson custody
    B = "B"  # Shady Oaks housing
    C = "C"  # Convergence (cross-lane)
    D = "D"  # PPO / Protection Orders
    E = "E"  # Judicial Misconduct / JTC
    F = "F"  # Appellate (COA/MSC)


class Court(str, Enum):
    """Michigan courts and federal."""
    CIRCUIT_14TH = "14TH"
    COA = "COA"
    MSC = "MSC"
    JTC = "JTC"
    USDC_WD_MI = "USDC"
    FOC = "FOC"


class Severity(str, Enum):
    CRITICAL = "critical"
    URGENT = "urgent"
    HIGH = "high"
    WARNING = "warning"
    INFO = "info"


class FilingStatus(str, Enum):
    DRAFTING = "drafting"
    REVIEW = "review"
    FINAL = "final"
    FILED = "filed"
    SERVED = "served"


class ActionTier(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    STANDARD = "STANDARD"


class PostureTag(str, Enum):
    """Evidence atom posture — every quote gets one."""
    RECORD_FACT = "RECORD_FACT"
    EVIDENCE_FACT = "EVIDENCE_FACT"
    SWORN_FACT = "SWORN_FACT"
    ALLEGATION = "ALLEGATION"
    INFERENCE = "INFERENCE"


class TruthTag(str, Enum):
    PROVEN = "PROVEN"
    UNVERIFIED = "UNVERIFIED"
    CONTESTED = "CONTESTED"
    DISPROVEN = "DISPROVEN"


class IracSection(str, Enum):
    ISSUE = "ISSUE"
    RULE = "RULE"
    APPLICATION = "APPLICATION"
    CONCLUSION = "CONCLUSION"


# ═══════════════════════════════════════════════════════════════════════════════
# PROVENANCE & EVIDENCE
# ═══════════════════════════════════════════════════════════════════════════════

class ProvenanceRef(BaseModel):
    """Formal pointer tying a fact to its DB source — QuoteLock compliant."""
    model_config = ConfigDict(extra="forbid")

    atom_id: str
    source_table: str
    source_id: str
    match_type: str = "EXACT"
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    run_id: Optional[str] = None


class EvidenceQuote(BaseModel):
    """A single evidence quote with provenance."""
    model_config = ConfigDict(extra="forbid")

    quote_text: str = Field(min_length=1)
    speaker: Optional[str] = None
    legal_significance: Optional[str] = None
    evidence_category: Optional[str] = None
    posture: PostureTag = PostureTag.EVIDENCE_FACT
    source: Optional[str] = None  # e.g. "evidence_quotes_fts"


class AuthorityRef(BaseModel):
    """A legal authority citation with text excerpt."""
    model_config = ConfigDict(extra="forbid")

    authority: str = Field(min_length=1, description="Rule number (MCR/MCL/MRE)")
    title: Optional[str] = None
    text: Optional[str] = Field(None, max_length=1000, description="First ~800 chars")
    source: Optional[str] = None  # "auth_rules" | "rules_text"


class AuthorityTriple(BaseModel):
    """Citation triple: rule + pinpoint + proposition."""
    model_config = ConfigDict(extra="forbid")

    rule: str = Field(description="MCR X.XXX(X)(x) or MCL XXX.XX(x)")
    pinpoint: Optional[str] = Field(None, description="Specific subsection")
    proposition: str = Field(description="What the rule says/requires")


# ═══════════════════════════════════════════════════════════════════════════════
# CITATION AUDIT
# ═══════════════════════════════════════════════════════════════════════════════

class CitationAudit(BaseModel):
    """Result of citation verification against auth_rules + rules_text."""
    model_config = ConfigDict(extra="forbid")

    verified: list[str] = Field(default_factory=list)
    unverified: list[str] = Field(default_factory=list)
    total: int = 0

    @property
    def verification_rate(self) -> float:
        return len(self.verified) / self.total if self.total > 0 else 0.0


class IracCheck(BaseModel):
    """IRAC completeness check — mandatory for every legal document."""
    model_config = ConfigDict(extra="forbid")

    complete: bool = False
    present: list[IracSection] = Field(default_factory=list)
    missing: list[IracSection] = Field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# FILING CAPTION (MCR 2.113)
# ═══════════════════════════════════════════════════════════════════════════════

class FilingCaption(BaseModel):
    """Court filing caption per MCR 2.113 formatting requirements."""
    model_config = ConfigDict(extra="forbid")

    state: str = "STATE OF MICHIGAN"
    court: str = Field(description="Full court name")
    county: str = "MUSKEGON"
    plaintiff: str = "ANDREW J. PIGORS"
    plaintiff_label: str = "Plaintiff"
    defendant: str = "EMILY A. WATSON"
    defendant_label: str = "Defendant"
    case_number: str
    judge: Optional[str] = None
    document_title: str = Field(min_length=1)
    forum: Court = Court.CIRCUIT_14TH


# ═══════════════════════════════════════════════════════════════════════════════
# CERTIFICATE OF SERVICE (MCR 2.107)
# ═══════════════════════════════════════════════════════════════════════════════

class ServiceEntry(BaseModel):
    """One person/entity served."""
    model_config = ConfigDict(extra="forbid")

    name: str
    address: Optional[str] = None
    method: str = Field(description="first-class mail | personal | e-filing | email")
    date_served: Optional[str] = None


class CertificateOfService(BaseModel):
    """MCR 2.107 compliant Certificate of Service."""
    model_config = ConfigDict(extra="forbid")

    document_title: str
    case_number: str
    served_parties: list[ServiceEntry] = Field(min_length=1)
    server_name: str = "Andrew J. Pigors"
    server_address: Optional[str] = None
    date: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# MOTION OUTPUT (MCR 2.119)
# ═══════════════════════════════════════════════════════════════════════════════

class MotionOutput(BaseModel):
    """Structured output from motion generation."""
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=50, description="Full court-ready motion text")
    motion_type: str
    title: str
    authority_count: int = Field(ge=0)
    evidence_count: int = Field(ge=0)
    word_count: int = Field(ge=0)
    citation_validation: CitationAudit
    irac_check: IracCheck

    @field_validator("text")
    @classmethod
    def must_have_caption(cls, v: str) -> str:
        if "STATE OF MICHIGAN" not in v and "UNITED STATES" not in v:
            raise ValueError("Motion text must include court caption")
        return v


# ═══════════════════════════════════════════════════════════════════════════════
# APPELLATE BRIEF (MCR 7.212)
# ═══════════════════════════════════════════════════════════════════════════════

class BriefCaption(BaseModel):
    model_config = ConfigDict(extra="forbid")

    court: str = "STATE OF MICHIGAN COURT OF APPEALS"
    docket: str
    lower_court: Optional[str] = None
    lower_case: Optional[str] = None
    appellant: str = "ANDREW J. PIGORS"
    appellee: str = "EMILY A. WATSON"


class IssuePresented(BaseModel):
    model_config = ConfigDict(extra="forbid")

    number: int = Field(ge=1)
    issue: str = Field(min_length=10)
    answer_below: Optional[str] = None
    appellant_answer: Optional[str] = None


class StandardOfReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    issue: str
    standard_of_review: str = Field(
        description="Abuse of Discretion | De Novo | Clear Error"
    )
    explanation: str


class IracBlock(BaseModel):
    """IRAC-structured argument block."""
    model_config = ConfigDict(extra="forbid")

    issue: str
    rule: list[AuthorityRef] = Field(min_length=1)
    application: list[EvidenceQuote] = Field(min_length=1)
    conclusion: str


class BriefArgument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    standard_of_review: StandardOfReview
    section: Optional[str] = None
    mcr_ref: Optional[str] = None
    issue: str
    irac: IracBlock
    supporting_citations: list[AuthorityRef] = Field(default_factory=list)


class WordCountCheck(BaseModel):
    """MCR 7.212(B) word limit compliance."""
    model_config = ConfigDict(extra="forbid")

    word_count: int
    limit: int = 16000
    within_limit: bool
    remaining: int = Field(ge=0)
    over_by: int = Field(ge=0, default=0)


class StatementOfFacts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    section: Optional[str] = None
    mcr_ref: str = "MCR 7.212(C)(6)"
    timeline_events: int = Field(ge=0, default=0)
    evidence_items: int = Field(ge=0, default=0)
    docket_events: int = Field(ge=0, default=0)


class ReliefItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    number: int = Field(ge=1)
    request: str = Field(min_length=5)


class AppellateBrief(BaseModel):
    """MCR 7.212-compliant appellate brief structure."""
    model_config = ConfigDict(extra="forbid")

    caption: BriefCaption
    issues_presented: list[IssuePresented] = Field(min_length=1)
    statement_of_facts: StatementOfFacts
    arguments: list[BriefArgument] = Field(min_length=1)
    relief_requested: list[ReliefItem] = Field(min_length=1)
    mcr_compliance: Optional[WordCountCheck] = None


# ═══════════════════════════════════════════════════════════════════════════════
# FILING STRATEGY (OMEGA)
# ═══════════════════════════════════════════════════════════════════════════════

class ScoredAction(BaseModel):
    """A scored legal action from OMEGA."""
    model_config = ConfigDict(extra="forbid")

    action_id: str
    name: str
    forum: Court
    lane: CaseLane
    score: float = Field(ge=0, le=100)
    tier: ActionTier
    tier_action: str = Field(description="FILE IMMEDIATELY | SCHEDULE | HOLD")
    notes: Optional[str] = None
    readiness_pct: Optional[int] = Field(None, ge=0, le=100)
    risk_score: Optional[float] = None


class RuleCompliance(BaseModel):
    """Procedural compliance checklist for a filing."""
    model_config = ConfigDict(extra="forbid")

    action_name: str
    rule_citation: str
    procedures: list[str] = Field(default_factory=list)
    service: Optional[str] = None
    timing: Optional[str] = None
    fees: Optional[str] = None


class FilingStrategy(BaseModel):
    """OMEGA filing strategy output — tiered action plan."""
    model_config = ConfigDict(extra="forbid")

    critical_actions: list[ScoredAction] = Field(default_factory=list)
    high_actions: list[ScoredAction] = Field(default_factory=list)
    standard_actions: list[ScoredAction] = Field(default_factory=list)
    rule_map: dict[str, RuleCompliance] = Field(default_factory=dict)

    @property
    def total_actions(self) -> int:
        return len(self.critical_actions) + len(self.high_actions) + len(self.standard_actions)


# ═══════════════════════════════════════════════════════════════════════════════
# FILING READINESS
# ═══════════════════════════════════════════════════════════════════════════════

class FilingReadiness(BaseModel):
    """Vehicle readiness evaluation — 5-factor scoring model."""
    model_config = ConfigDict(extra="forbid")

    vehicle_name: str
    authority_score: float = Field(ge=0, le=100, default=0)
    evidence_score: float = Field(ge=0, le=100, default=0)
    compliance_score: float = Field(ge=0, le=100, default=0)
    impeachment_score: float = Field(ge=0, le=100, default=0)
    total_score: float = Field(ge=0, le=100, default=0)
    gaps: Optional[str] = None
    strengths: Optional[str] = None

    @property
    def ready_to_file(self) -> bool:
        return self.total_score >= 70


# ═══════════════════════════════════════════════════════════════════════════════
# COMPLIANCE VALIDATION (MCR 2.113)
# ═══════════════════════════════════════════════════════════════════════════════

class ComplianceResult(BaseModel):
    """Court filing compliance check result."""
    model_config = ConfigDict(extra="forbid")

    score: int = Field(ge=0, le=100)
    court: str
    word_count: int = Field(ge=0)
    citation_count: int = Field(ge=0)
    issues: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    compliant: bool = False


# ═══════════════════════════════════════════════════════════════════════════════
# FILING PACKAGE (complete stack)
# ═══════════════════════════════════════════════════════════════════════════════

class FilingDocument(BaseModel):
    """A single document within a filing package."""
    model_config = ConfigDict(extra="forbid")

    doc_type: str = Field(description="motion | brief | proposed_order | cos | exhibit_index")
    title: str
    content: Optional[str] = None
    file_path: Optional[str] = None
    word_count: int = Field(ge=0, default=0)


class FilingPackage(BaseModel):
    """Complete filing stack — motion + brief + order + CoS + exhibits."""
    model_config = ConfigDict(extra="forbid")

    package_type: str
    court: str
    case_number: str
    lane: CaseLane
    generated: str = Field(description="ISO 8601 timestamp")
    documents: dict[str, FilingDocument] = Field(min_length=1)
    authority_cited: list[AuthorityRef] = Field(default_factory=list)
    supporting_evidence: list[EvidenceQuote] = Field(default_factory=list)
    document_count: int = Field(ge=1)
    validation: Optional[ComplianceResult] = None
    caption: Optional[FilingCaption] = None
    certificate_of_service: Optional[CertificateOfService] = None

    @field_validator("generated")
    @classmethod
    def must_be_iso(cls, v: str) -> str:
        datetime.fromisoformat(v)
        return v


# ═══════════════════════════════════════════════════════════════════════════════
# DEADLINE & DOCKET
# ═══════════════════════════════════════════════════════════════════════════════

class DeadlineItem(BaseModel):
    """A litigation deadline with urgency."""
    model_config = ConfigDict(extra="forbid")

    id: Optional[str] = None
    title: str
    due_date_iso: str
    days_remaining: Optional[int] = None
    severity: Severity = Severity.INFO
    lane: Optional[CaseLane] = None
    filing_vehicle: Optional[str] = None
    notes: Optional[str] = None


class DocketEvent(BaseModel):
    """A docket entry from case records."""
    model_config = ConfigDict(extra="forbid")

    date: Optional[str] = None
    description: str
    filed_by: Optional[str] = None
    case_number: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# GAP TICKET
# ═══════════════════════════════════════════════════════════════════════════════

class GapTicket(BaseModel):
    """Missing element tracked during pipeline processing."""
    model_config = ConfigDict(extra="forbid")

    ticket_id: str
    filing_name: str
    gap_type: str
    description: Optional[str] = None
    severity: Severity = Severity.WARNING
    resolution_status: str = "open"
    resolution_notes: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE RUN MANIFEST
# ═══════════════════════════════════════════════════════════════════════════════

class ManifestInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_path: str
    sha256: Optional[str] = None
    lane: Optional[CaseLane] = None
    source: str = "local"


class ManifestOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    vehicle: Optional[str] = None
    file_path: Optional[str] = None


class RunManifest(BaseModel):
    """Pipeline run manifest — full audit trail."""
    model_config = ConfigDict(extra="forbid")

    run_id: str
    timestamp: str
    inputs: list[ManifestInput] = Field(default_factory=list)
    outputs: list[ManifestOutput] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    gaps_opened: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════════
# JSON SCHEMA EXPORT — for desktop app consumption
# ═══════════════════════════════════════════════════════════════════════════════

def export_all_schemas(output_dir: str | Path = ".") -> dict[str, str]:
    """Export JSON Schema for all models. Desktop app can import these.

    Returns dict of {model_name: filepath}.
    """
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    models = [
        FilingCaption, CertificateOfService, MotionOutput,
        AppellateBrief, FilingStrategy, FilingReadiness,
        ComplianceResult, FilingPackage, CitationAudit,
        DeadlineItem, GapTicket, RunManifest, EvidenceQuote,
        AuthorityRef, ProvenanceRef,
    ]

    exported = {}
    for model in models:
        name = model.__name__
        schema = model.model_json_schema()
        filepath = output / f"{name}.schema.json"
        filepath.write_text(json.dumps(schema, indent=2), encoding="utf-8")
        exported[name] = str(filepath)

    return exported


# ═══════════════════════════════════════════════════════════════════════════════
# CLI — export schemas
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

    import argparse
    parser = argparse.ArgumentParser(description="LitigationOS Filing Contracts")
    parser.add_argument("command", choices=["export", "list", "validate"],
                        help="export = JSON schemas; list = model names; validate = test parse")
    parser.add_argument("--output", "-o", default=".", help="Output directory for schemas")
    parser.add_argument("--model", "-m", help="Model name for validate command")
    parser.add_argument("--input", "-i", help="JSON file to validate against model")
    args = parser.parse_args()

    if args.command == "list":
        models = [
            "FilingCaption", "CertificateOfService", "MotionOutput",
            "AppellateBrief", "FilingStrategy", "FilingReadiness",
            "ComplianceResult", "FilingPackage", "CitationAudit",
            "DeadlineItem", "GapTicket", "RunManifest", "EvidenceQuote",
            "AuthorityRef", "ProvenanceRef",
        ]
        for m in models:
            print(f"  {m}")
        print(f"\n{len(models)} models defined")

    elif args.command == "export":
        exported = export_all_schemas(args.output)
        for name, path in exported.items():
            print(f"  ✅ {name:30s} → {path}")
        print(f"\n{len(exported)} schemas exported to {args.output}")

    elif args.command == "validate":
        if not args.model or not args.input:
            print("Usage: --model ModelName --input file.json")
            sys.exit(1)
        model_cls = globals().get(args.model)
        if not model_cls:
            print(f"Unknown model: {args.model}")
            sys.exit(1)
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))
        try:
            obj = model_cls.model_validate(data)
            print(f"✅ Valid {args.model}")
            print(json.dumps(obj.model_dump(), indent=2, default=str))
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            sys.exit(1)
