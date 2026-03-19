# -*- coding: utf-8 -*-
"""
Evidence Gap Detector — LitigationOS Legal AI Subsystem
========================================================
Maps required evidence to available evidence per filing type per lane.
Identifies gaps and generates acquisition tasks with priority scoring.

This module supports the six case lanes of Pigors v. Watson:
  Lane A — Custody (2024-001507-DC)
  Lane B — Housing (2025-002760-CZ)
  Lane C — Convergence (cross-lane)
  Lane D — PPO (2023-5907-PP)
  Lane E — Misconduct / JTC
  Lane F — Appellate (COA 366810)

Evidence Categories:
  documentary  — Documents, records, official filings
  testimonial  — Witness statements, depositions, affidavits
  physical     — Photos, tangible items, inspection results
  digital      — Electronic communications, metadata, social media
  expert       — Expert reports, professional evaluations

Usage:
    from legal_ai.evidence_gap_detector import EvidenceGapDetector

    detector = EvidenceGapDetector()
    report = detector.analyze_filing(text, "motion_disqualification", "A")
    print(report.coverage_pct, report.grade, report.readiness_score)

    # Get all requirements for a filing type
    reqs = detector.get_requirements("custody_modification")

    # Generate an acquisition plan for gaps
    plan = detector.generate_acquisition_plan(report.gaps)
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import sqlite3
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("legal_ai.evidence_gap_detector")

# ---------------------------------------------------------------------------
# Path resolution — legal_ai → 00_SYSTEM → LitigationOS root
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
_DB_PATH = _HERE.parents[1] / "litigation_context.db"

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class EvidenceCategory(str, Enum):
    """Categories of evidence recognised by the system."""
    DOCUMENTARY = "documentary"
    TESTIMONIAL = "testimonial"
    PHYSICAL = "physical"
    DIGITAL = "digital"
    EXPERT = "expert"


class Importance(str, Enum):
    """Importance levels for evidence requirements."""
    CRITICAL = "critical"
    STRONG = "strong"
    SUPPORTING = "supporting"
    OPTIONAL = "optional"


class GapType(str, Enum):
    """Classification of evidence gaps."""
    MISSING = "missing"
    WEAK = "weak"
    INCOMPLETE = "incomplete"
    UNAUTHENTICATED = "unauthenticated"


class Severity(str, Enum):
    """Severity levels for evidence gaps."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EffortEstimate(str, Enum):
    """Estimated effort to acquire missing evidence."""
    IMMEDIATE = "immediate"
    DAYS = "days"
    WEEKS = "weeks"
    EXPERT_NEEDED = "expert_needed"


# Numeric weights for prioritisation
_IMPORTANCE_WEIGHT: Dict[str, float] = {
    "critical": 1.0,
    "strong": 0.75,
    "supporting": 0.5,
    "optional": 0.25,
}

_SEVERITY_WEIGHT: Dict[str, float] = {
    "critical": 1.0,
    "high": 0.75,
    "medium": 0.5,
    "low": 0.25,
}


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class EvidenceRequirement:
    """A single evidence requirement for a filing type."""

    req_id: str
    filing_type: str
    description: str
    category: str          # documentary, testimonial, physical, digital, expert
    importance: str        # critical, strong, supporting, optional
    mcr_basis: str         # Which MCR/MCL requires this evidence
    keywords: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to dictionary."""
        return asdict(self)


@dataclass
class EvidenceMatch:
    """A match between a requirement and available evidence."""

    req_id: str
    evidence_id: str
    source_file: str
    match_quality: float   # 0-1
    match_reason: str

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to dictionary."""
        return asdict(self)


@dataclass
class EvidenceGap:
    """An identified gap in the evidence chain."""

    req_id: str
    requirement: EvidenceRequirement
    gap_type: str          # missing, weak, incomplete, unauthenticated
    severity: str          # critical, high, medium, low
    acquisition_task: str  # What to do to fill the gap
    estimated_effort: str  # immediate, days, weeks, expert_needed
    alternative_sources: List[str] = field(default_factory=list)
    priority_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to dictionary."""
        d = asdict(self)
        d["requirement"] = self.requirement.to_dict()
        return d


@dataclass
class GapAnalysisReport:
    """Complete gap analysis report for a single filing."""

    filing_id: str
    filing_type: str
    lane: str
    total_requirements: int
    satisfied: int
    gaps: List[EvidenceGap]
    coverage_pct: float
    readiness_score: float   # 0-100
    grade: str               # A-F
    recommendations: List[str] = field(default_factory=list)
    analysis_timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.analysis_timestamp:
            self.analysis_timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to dictionary."""
        d = asdict(self)
        d["gaps"] = [g.to_dict() for g in self.gaps]
        return d


# ---------------------------------------------------------------------------
# Evidence Requirement Maps (embedded — no external data files)
# ---------------------------------------------------------------------------

def _build_custody_requirements() -> List[EvidenceRequirement]:
    """Evidence requirements for custody motions (Lane A — MCL 722.23)."""
    reqs = [
        EvidenceRequirement(
            req_id="CUST-001", filing_type="custody_modification",
            description="Evidence of love, affection, and emotional ties (Factor A)",
            category="testimonial", importance="critical",
            mcr_basis="MCL 722.23(a)",
            keywords=["love", "affection", "emotional", "bond", "attachment",
                      "relationship", "parent-child"],
        ),
        EvidenceRequirement(
            req_id="CUST-002", filing_type="custody_modification",
            description="Evidence of capacity to provide food, clothing, medical care (Factor B)",
            category="documentary", importance="strong",
            mcr_basis="MCL 722.23(b)",
            keywords=["income", "employment", "insurance", "medical", "housing",
                      "food", "clothing", "financial"],
        ),
        EvidenceRequirement(
            req_id="CUST-003", filing_type="custody_modification",
            description="Length of time child lived in stable custodial environment (Factor C)",
            category="documentary", importance="strong",
            mcr_basis="MCL 722.23(c)",
            keywords=["residence", "stability", "custodial", "living arrangement",
                      "home", "established"],
        ),
        EvidenceRequirement(
            req_id="CUST-004", filing_type="custody_modification",
            description="Moral fitness of parties involved (Factor E)",
            category="testimonial", importance="strong",
            mcr_basis="MCL 722.23(e)",
            keywords=["moral", "fitness", "character", "conduct", "behavior",
                      "criminal", "substance"],
        ),
        EvidenceRequirement(
            req_id="CUST-005", filing_type="custody_modification",
            description="Mental and physical health of parties (Factor F)",
            category="expert", importance="strong",
            mcr_basis="MCL 722.23(f)",
            keywords=["mental health", "physical health", "psychological",
                      "evaluation", "diagnosis", "treatment"],
        ),
        EvidenceRequirement(
            req_id="CUST-006", filing_type="custody_modification",
            description="School and community records of L.D.W. (Factor G)",
            category="documentary", importance="strong",
            mcr_basis="MCL 722.23(g)",
            keywords=["school", "grades", "attendance", "community", "activities",
                      "education", "records"],
        ),
        EvidenceRequirement(
            req_id="CUST-007", filing_type="custody_modification",
            description="Home, school, and community stability (Factor D)",
            category="documentary", importance="critical",
            mcr_basis="MCL 722.23(d)",
            keywords=["permanence", "family unit", "stability", "established",
                      "routine", "continuity"],
        ),
        EvidenceRequirement(
            req_id="CUST-008", filing_type="custody_modification",
            description="Domestic violence history (Factor J)",
            category="documentary", importance="critical",
            mcr_basis="MCL 722.23(j)",
            keywords=["domestic violence", "PPO", "protection order", "assault",
                      "abuse", "police report", "incident"],
        ),
        EvidenceRequirement(
            req_id="CUST-009", filing_type="custody_modification",
            description="Reasonable preference of child if court deems sufficient age (Factor H)",
            category="testimonial", importance="supporting",
            mcr_basis="MCL 722.23(h)",
            keywords=["preference", "child", "wishes", "age", "maturity",
                      "interview"],
        ),
        EvidenceRequirement(
            req_id="CUST-010", filing_type="custody_modification",
            description="Willingness to facilitate close relationship with other parent (Factor I)",
            category="documentary", importance="critical",
            mcr_basis="MCL 722.23(i)",
            keywords=["facilitate", "relationship", "cooperation", "parenting time",
                      "communication", "interference", "denial"],
        ),
        EvidenceRequirement(
            req_id="CUST-011", filing_type="custody_modification",
            description="Evidence of parenting time compliance or denial",
            category="documentary", importance="critical",
            mcr_basis="MCR 3.206",
            keywords=["parenting time", "visitation", "denial", "interference",
                      "schedule", "compliance", "log"],
        ),
        EvidenceRequirement(
            req_id="CUST-012", filing_type="custody_modification",
            description="Affidavit supporting custody modification per MCR 3.206",
            category="documentary", importance="critical",
            mcr_basis="MCR 3.206(C)",
            keywords=["affidavit", "sworn", "verified", "notarized",
                      "declaration", "custody modification"],
        ),
        EvidenceRequirement(
            req_id="CUST-013", filing_type="custody_modification",
            description="Evidence of ex parte communications by judge",
            category="digital", importance="critical",
            mcr_basis="MCR 2.003(C)(1)",
            keywords=["ex parte", "communication", "unilateral", "one-sided",
                      "contact", "off-record"],
        ),
        EvidenceRequirement(
            req_id="CUST-014", filing_type="custody_modification",
            description="Any other factor considered by court (Factor L)",
            category="documentary", importance="optional",
            mcr_basis="MCL 722.23(l)",
            keywords=["additional", "other factor", "relevant", "consideration"],
        ),
    ]
    return reqs


def _build_disqualification_requirements() -> List[EvidenceRequirement]:
    """Evidence requirements for judicial disqualification (Lane A/E)."""
    return [
        EvidenceRequirement(
            req_id="DISQ-001", filing_type="motion_disqualification",
            description="Evidence of personal bias or prejudice (MCR 2.003(C)(1)(a))",
            category="documentary", importance="critical",
            mcr_basis="MCR 2.003(C)(1)(a)",
            keywords=["bias", "prejudice", "partiality", "impartial",
                      "unfair", "one-sided"],
        ),
        EvidenceRequirement(
            req_id="DISQ-002", filing_type="motion_disqualification",
            description="Evidence of ex parte orders issued without notice",
            category="documentary", importance="critical",
            mcr_basis="MCR 2.003(C)(1)",
            keywords=["ex parte", "without notice", "unilateral order",
                      "emergency order", "no hearing"],
        ),
        EvidenceRequirement(
            req_id="DISQ-003", filing_type="motion_disqualification",
            description="Hearing transcripts showing biased conduct",
            category="documentary", importance="critical",
            mcr_basis="MCR 2.003(C)(1)(a)",
            keywords=["transcript", "hearing", "proceeding", "record",
                      "statement", "bench", "on the record"],
        ),
        EvidenceRequirement(
            req_id="DISQ-004", filing_type="motion_disqualification",
            description="Pattern evidence — multiple instances of bias",
            category="documentary", importance="strong",
            mcr_basis="MCR 2.003(C)(1)",
            keywords=["pattern", "repeated", "multiple", "instances",
                      "systematic", "recurring", "history"],
        ),
        EvidenceRequirement(
            req_id="DISQ-005", filing_type="motion_disqualification",
            description="Evidence of prejudgment of issues",
            category="documentary", importance="strong",
            mcr_basis="MCR 2.003(C)(1)(b)",
            keywords=["prejudgment", "predetermined", "mind made up",
                      "already decided", "pre-decided"],
        ),
        EvidenceRequirement(
            req_id="DISQ-006", filing_type="motion_disqualification",
            description="Evidence of financial or personal interest in outcome",
            category="documentary", importance="strong",
            mcr_basis="MCR 2.003(C)(1)(c)",
            keywords=["financial interest", "personal interest", "conflict",
                      "recusal", "pecuniary"],
        ),
        EvidenceRequirement(
            req_id="DISQ-007", filing_type="motion_disqualification",
            description="Comparison of treatment — plaintiff vs. defendant",
            category="documentary", importance="strong",
            mcr_basis="MCR 2.003(C)(1)",
            keywords=["differential treatment", "comparison", "disparate",
                      "unequal", "favorable", "unfavorable"],
        ),
        EvidenceRequirement(
            req_id="DISQ-008", filing_type="motion_disqualification",
            description="Affidavit of bias per MCR 2.003(D)",
            category="documentary", importance="critical",
            mcr_basis="MCR 2.003(D)",
            keywords=["affidavit", "bias", "sworn statement", "facts",
                      "specific instances"],
        ),
        EvidenceRequirement(
            req_id="DISQ-009", filing_type="motion_disqualification",
            description="Timeline of procedural irregularities",
            category="documentary", importance="supporting",
            mcr_basis="MCR 2.003(C)(1)",
            keywords=["timeline", "chronology", "procedural", "irregularity",
                      "sequence", "dates"],
        ),
        EvidenceRequirement(
            req_id="DISQ-010", filing_type="motion_disqualification",
            description="Expert opinion on judicial conduct standards (if available)",
            category="expert", importance="optional",
            mcr_basis="MCR 2.003",
            keywords=["expert", "judicial conduct", "ethics", "standard",
                      "canon", "code of conduct"],
        ),
    ]


def _build_housing_requirements() -> List[EvidenceRequirement]:
    """Evidence requirements for housing complaint (Lane B)."""
    return [
        EvidenceRequirement(
            req_id="HOUS-001", filing_type="complaint_housing",
            description="Lease agreements and rental contracts",
            category="documentary", importance="critical",
            mcr_basis="MCL 554.601 et seq.",
            keywords=["lease", "rental agreement", "contract", "tenancy",
                      "term", "occupancy"],
        ),
        EvidenceRequirement(
            req_id="HOUS-002", filing_type="complaint_housing",
            description="Payment records — rent, deposits, fees",
            category="documentary", importance="critical",
            mcr_basis="MCL 554.602",
            keywords=["rent", "payment", "receipt", "deposit", "security",
                      "check", "money order", "transaction"],
        ),
        EvidenceRequirement(
            req_id="HOUS-003", filing_type="complaint_housing",
            description="Utility bills and service records",
            category="documentary", importance="strong",
            mcr_basis="MCL 554.139",
            keywords=["utility", "electric", "water", "gas", "sewer",
                      "billing", "service"],
        ),
        EvidenceRequirement(
            req_id="HOUS-004", filing_type="complaint_housing",
            description="Photos of housing conditions (sewage, structural issues)",
            category="physical", importance="critical",
            mcr_basis="MCL 125.534",
            keywords=["photo", "image", "condition", "sewage", "damage",
                      "mold", "structural", "repair"],
        ),
        EvidenceRequirement(
            req_id="HOUS-005", filing_type="complaint_housing",
            description="Communication records with property management",
            category="digital", importance="strong",
            mcr_basis="MCL 554.139",
            keywords=["email", "text", "letter", "notice", "complaint",
                      "request", "maintenance", "management"],
        ),
        EvidenceRequirement(
            req_id="HOUS-006", filing_type="complaint_housing",
            description="Code violation reports and inspection records",
            category="documentary", importance="critical",
            mcr_basis="MCL 125.534",
            keywords=["code violation", "inspection", "building inspector",
                      "citation", "violation", "condemned"],
        ),
        EvidenceRequirement(
            req_id="HOUS-007", filing_type="complaint_housing",
            description="EGLE environmental records (if applicable)",
            category="documentary", importance="strong",
            mcr_basis="MCL 324.20101 et seq.",
            keywords=["EGLE", "environmental", "contamination", "hazard",
                      "lead", "asbestos", "testing"],
        ),
        EvidenceRequirement(
            req_id="HOUS-008", filing_type="complaint_housing",
            description="Medical records documenting health effects from conditions",
            category="expert", importance="strong",
            mcr_basis="MCL 554.139(1)",
            keywords=["medical", "health", "doctor", "diagnosis", "treatment",
                      "illness", "respiratory"],
        ),
        EvidenceRequirement(
            req_id="HOUS-009", filing_type="complaint_housing",
            description="Comparable rental pricing evidence",
            category="documentary", importance="supporting",
            mcr_basis="MCL 554.601",
            keywords=["comparable", "market rate", "rental price", "similar",
                      "area", "fair market"],
        ),
        EvidenceRequirement(
            req_id="HOUS-010", filing_type="complaint_housing",
            description="Witness statements from other tenants",
            category="testimonial", importance="supporting",
            mcr_basis="MRE 602",
            keywords=["witness", "tenant", "neighbor", "statement",
                      "testimony", "observed", "experienced"],
        ),
    ]


def _build_federal_1983_requirements() -> List[EvidenceRequirement]:
    """Evidence requirements for federal §1983 action (Lane A)."""
    return [
        EvidenceRequirement(
            req_id="FED-001", filing_type="federal_1983",
            description="State action under color of law — judge acting in official capacity",
            category="documentary", importance="critical",
            mcr_basis="42 USC §1983",
            keywords=["color of law", "state action", "official capacity",
                      "government", "authority", "judicial"],
        ),
        EvidenceRequirement(
            req_id="FED-002", filing_type="federal_1983",
            description="Constitutional violation evidence — due process denial",
            category="documentary", importance="critical",
            mcr_basis="14th Amendment; 42 USC §1983",
            keywords=["due process", "constitutional", "violation", "rights",
                      "fourteenth amendment", "liberty", "equal protection"],
        ),
        EvidenceRequirement(
            req_id="FED-003", filing_type="federal_1983",
            description="Pattern of similar constitutional violations",
            category="documentary", importance="strong",
            mcr_basis="42 USC §1983",
            keywords=["pattern", "practice", "systematic", "repeated",
                      "other cases", "similar", "history"],
        ),
        EvidenceRequirement(
            req_id="FED-004", filing_type="federal_1983",
            description="Evidence overcoming qualified immunity defense",
            category="documentary", importance="critical",
            mcr_basis="Harlow v. Fitzgerald, 457 US 800 (1982)",
            keywords=["qualified immunity", "clearly established", "reasonable",
                      "objective", "override", "exception"],
        ),
        EvidenceRequirement(
            req_id="FED-005", filing_type="federal_1983",
            description="Evidence of actual damages — emotional distress, economic harm",
            category="documentary", importance="strong",
            mcr_basis="42 USC §1983",
            keywords=["damages", "harm", "injury", "emotional distress",
                      "economic", "loss", "quantifiable"],
        ),
        EvidenceRequirement(
            req_id="FED-006", filing_type="federal_1983",
            description="Expert report on judicial conduct standards violation",
            category="expert", importance="supporting",
            mcr_basis="FRE 702; 42 USC §1983",
            keywords=["expert", "report", "judicial conduct", "standard",
                      "violation", "opinion"],
        ),
        EvidenceRequirement(
            req_id="FED-007", filing_type="federal_1983",
            description="Exhaustion of state remedies documentation",
            category="documentary", importance="strong",
            mcr_basis="Rooker-Feldman doctrine",
            keywords=["exhaustion", "state remedies", "appeal", "denied",
                      "state court", "remedied"],
        ),
        EvidenceRequirement(
            req_id="FED-008", filing_type="federal_1983",
            description="Declaratory and injunctive relief basis evidence",
            category="documentary", importance="supporting",
            mcr_basis="42 USC §1983; 28 USC §2201",
            keywords=["declaratory", "injunctive", "relief", "ongoing",
                      "irreparable", "remedy"],
        ),
    ]


def _build_ppo_requirements() -> List[EvidenceRequirement]:
    """Evidence requirements for PPO matters (Lane D)."""
    return [
        EvidenceRequirement(
            req_id="PPO-001", filing_type="ppo_violation",
            description="PPO order text — certified copy of the protection order",
            category="documentary", importance="critical",
            mcr_basis="MCL 600.2950",
            keywords=["PPO", "protection order", "personal protection",
                      "order text", "terms", "conditions"],
        ),
        EvidenceRequirement(
            req_id="PPO-002", filing_type="ppo_violation",
            description="Evidence of specific PPO violation — dates, acts, communications",
            category="documentary", importance="critical",
            mcr_basis="MCL 600.2950(23)",
            keywords=["violation", "contact", "communication", "proximity",
                      "harass", "stalk", "breach"],
        ),
        EvidenceRequirement(
            req_id="PPO-003", filing_type="ppo_violation",
            description="Police reports documenting PPO violations",
            category="documentary", importance="strong",
            mcr_basis="MCL 764.15b",
            keywords=["police report", "incident report", "arrest",
                      "responding officer", "dispatch", "911"],
        ),
        EvidenceRequirement(
            req_id="PPO-004", filing_type="ppo_violation",
            description="Communication records — texts, emails, voicemails",
            category="digital", importance="critical",
            mcr_basis="MRE 901",
            keywords=["text message", "email", "voicemail", "call log",
                      "social media", "screenshot"],
        ),
        EvidenceRequirement(
            req_id="PPO-005", filing_type="ppo_violation",
            description="Witness statements corroborating violation",
            category="testimonial", importance="strong",
            mcr_basis="MRE 602",
            keywords=["witness", "statement", "observed", "saw", "heard",
                      "present", "corroborate"],
        ),
        EvidenceRequirement(
            req_id="PPO-006", filing_type="ppo_violation",
            description="Service proof that respondent was served with PPO",
            category="documentary", importance="critical",
            mcr_basis="MCR 3.706(H)",
            keywords=["service", "served", "proof of service", "return",
                      "acknowledged"],
        ),
        EvidenceRequirement(
            req_id="PPO-007", filing_type="ppo_violation",
            description="Prior violation history (pattern evidence)",
            category="documentary", importance="strong",
            mcr_basis="MCL 600.2950(23)",
            keywords=["prior", "history", "previous", "repeated",
                      "pattern", "escalation"],
        ),
    ]


def _build_jtc_requirements() -> List[EvidenceRequirement]:
    """Evidence requirements for JTC / misconduct complaints (Lane E)."""
    return [
        EvidenceRequirement(
            req_id="JTC-001", filing_type="jtc_complaint",
            description="Specific instances of judicial misconduct with dates",
            category="documentary", importance="critical",
            mcr_basis="MCR 9.104; Const 1963, Art 6 §30",
            keywords=["misconduct", "incident", "specific", "date",
                      "instance", "judicial", "conduct"],
        ),
        EvidenceRequirement(
            req_id="JTC-002", filing_type="jtc_complaint",
            description="Hearing transcripts evidencing misconduct",
            category="documentary", importance="critical",
            mcr_basis="MCR 9.104",
            keywords=["transcript", "hearing", "record", "proceeding",
                      "court reporter"],
        ),
        EvidenceRequirement(
            req_id="JTC-003", filing_type="jtc_complaint",
            description="Statistical analysis of ex parte communication rate",
            category="expert", importance="strong",
            mcr_basis="MRPC Canon 3(A)(4)",
            keywords=["statistical", "rate", "ex parte", "frequency",
                      "comparison", "average", "normal"],
        ),
        EvidenceRequirement(
            req_id="JTC-004", filing_type="jtc_complaint",
            description="Evidence of pattern across multiple cases (not just complainant)",
            category="documentary", importance="strong",
            mcr_basis="MCR 9.104",
            keywords=["pattern", "multiple cases", "other litigants",
                      "systematic", "widespread"],
        ),
        EvidenceRequirement(
            req_id="JTC-005", filing_type="jtc_complaint",
            description="Documentation of harm caused by misconduct",
            category="documentary", importance="strong",
            mcr_basis="MCR 9.104",
            keywords=["harm", "damage", "consequence", "impact", "result",
                      "injury", "prejudice"],
        ),
        EvidenceRequirement(
            req_id="JTC-006", filing_type="jtc_complaint",
            description="Prior complaints or disciplinary history (if public)",
            category="documentary", importance="supporting",
            mcr_basis="MCR 9.104",
            keywords=["prior complaint", "discipline", "censure", "warning",
                      "history", "record"],
        ),
    ]


def _build_appellate_requirements() -> List[EvidenceRequirement]:
    """Evidence requirements for appellate filings (Lane F — COA 366810)."""
    return [
        EvidenceRequirement(
            req_id="APP-001", filing_type="appellate_brief",
            description="Lower court record — complete certified record",
            category="documentary", importance="critical",
            mcr_basis="MCR 7.210",
            keywords=["record", "lower court", "certified", "register",
                      "transcript", "orders", "pleadings"],
        ),
        EvidenceRequirement(
            req_id="APP-002", filing_type="appellate_brief",
            description="Transcripts of all relevant hearings",
            category="documentary", importance="critical",
            mcr_basis="MCR 7.210(B)(1)",
            keywords=["transcript", "hearing", "proceeding", "testimony",
                      "court reporter", "stenographic"],
        ),
        EvidenceRequirement(
            req_id="APP-003", filing_type="appellate_brief",
            description="Orders being appealed — certified copies",
            category="documentary", importance="critical",
            mcr_basis="MCR 7.204",
            keywords=["order", "appealed", "judgment", "opinion", "ruling",
                      "decision", "certified copy"],
        ),
        EvidenceRequirement(
            req_id="APP-004", filing_type="appellate_brief",
            description="Preservation evidence — objections on the record",
            category="documentary", importance="critical",
            mcr_basis="MCR 2.517; MRE 103",
            keywords=["objection", "preserved", "on record", "timely",
                      "contemporaneous", "motion"],
        ),
        EvidenceRequirement(
            req_id="APP-005", filing_type="appellate_brief",
            description="Binding and persuasive authority supporting each error",
            category="documentary", importance="strong",
            mcr_basis="MCR 7.212(C)(7)",
            keywords=["authority", "precedent", "case law", "binding",
                      "persuasive", "supporting"],
        ),
        EvidenceRequirement(
            req_id="APP-006", filing_type="appellate_brief",
            description="Standard of review identification per issue",
            category="documentary", importance="strong",
            mcr_basis="MCR 7.212(C)(7)",
            keywords=["standard of review", "abuse of discretion",
                      "de novo", "clearly erroneous", "plain error"],
        ),
    ]


# Master registry — filing_type → requirements list
_REQUIREMENT_REGISTRY: Dict[str, List[EvidenceRequirement]] = {}


def _init_registry() -> None:
    """Populate the global requirement registry (lazy, once)."""
    if _REQUIREMENT_REGISTRY:
        return
    for builder in (
        _build_custody_requirements,
        _build_disqualification_requirements,
        _build_housing_requirements,
        _build_federal_1983_requirements,
        _build_ppo_requirements,
        _build_jtc_requirements,
        _build_appellate_requirements,
    ):
        reqs = builder()
        for r in reqs:
            _REQUIREMENT_REGISTRY.setdefault(r.filing_type, []).append(r)


# ---------------------------------------------------------------------------
# Lane → filing type mapping
# ---------------------------------------------------------------------------

_LANE_FILING_TYPES: Dict[str, List[str]] = {
    "A": ["custody_modification", "motion_disqualification", "federal_1983"],
    "B": ["complaint_housing"],
    "C": ["custody_modification", "complaint_housing", "federal_1983",
          "motion_disqualification", "ppo_violation", "jtc_complaint",
          "appellate_brief"],
    "D": ["ppo_violation"],
    "E": ["jtc_complaint", "motion_disqualification"],
    "F": ["appellate_brief"],
}

# Cross-lane evidence sources
_CROSS_LANE_EVIDENCE: Dict[str, Dict[str, List[str]]] = {
    "A": {
        "motion_disqualification": [
            "Lane E: JTC evidence of judicial misconduct pattern",
            "Lane D: PPO orders showing judicial handling",
            "Lane F: Appellate record of preserved errors",
        ],
        "custody_modification": [
            "Lane B: Housing conditions evidence (best-interest Factor B)",
            "Lane D: PPO history showing domestic violence (Factor J)",
            "Lane E: Evidence of judicial bias affecting custody hearings",
        ],
        "federal_1983": [
            "Lane E: Pattern evidence from JTC complaint",
            "Lane A: Custody orders showing constitutional violations",
            "Lane D: PPO proceedings showing due process denial",
        ],
    },
    "B": {
        "complaint_housing": [
            "Lane A: Financial stress evidence from custody litigation",
        ],
    },
    "D": {
        "ppo_violation": [
            "Lane A: Custody records showing contact patterns",
            "Lane E: Judicial handling of PPO proceedings",
        ],
    },
    "E": {
        "jtc_complaint": [
            "Lane A: Custody hearing transcripts showing bias",
            "Lane D: PPO proceedings showing ex parte conduct",
            "Lane F: Appellate record documenting errors",
        ],
        "motion_disqualification": [
            "Lane A: All custody proceeding evidence",
            "Lane D: PPO handling evidence",
        ],
    },
    "F": {
        "appellate_brief": [
            "Lane A: Full custody case record",
            "Lane E: Misconduct evidence supporting error claims",
        ],
    },
}


# ---------------------------------------------------------------------------
# Evidence text scanning patterns
# ---------------------------------------------------------------------------

_EVIDENCE_PATTERNS: List[Tuple[str, re.Pattern[str]]] = [
    ("exhibit_reference", re.compile(
        r"\bExhibit\s+[A-Z0-9]{1,5}\b", re.IGNORECASE)),
    ("bates_stamp", re.compile(
        r"\b[A-Z]{2,6}[-_]?\d{4,8}\b")),
    ("document_citation", re.compile(
        r"\b(?:attached|enclosed|see)\s+(?:hereto|herewith)?\s*"
        r"(?:as\s+)?(?:Exhibit|Attachment|Appendix)\s+\w+",
        re.IGNORECASE)),
    ("transcript_cite", re.compile(
        r"\b(?:Tr|Transcript)\s*[.,]?\s*(?:at\s+)?(?:p(?:p)?\.?\s*)?\d+",
        re.IGNORECASE)),
    ("affidavit_reference", re.compile(
        r"\b(?:affidavit|declaration|sworn\s+statement)\s+of\s+\w+",
        re.IGNORECASE)),
    ("police_report", re.compile(
        r"\b(?:police|incident|offense)\s+report\s*#?\s*\d*",
        re.IGNORECASE)),
    ("photo_video", re.compile(
        r"\b(?:photograph|photo|video|recording|surveillance)\b",
        re.IGNORECASE)),
    ("medical_record", re.compile(
        r"\b(?:medical\s+record|doctor|physician|treatment\s+record)",
        re.IGNORECASE)),
    ("financial_record", re.compile(
        r"\b(?:bank\s+statement|pay\s+stub|tax\s+return|W-?2|financial)",
        re.IGNORECASE)),
    ("communication_record", re.compile(
        r"\b(?:email|text\s+message|voicemail|letter|correspondence)",
        re.IGNORECASE)),
    ("court_order", re.compile(
        r"\b(?:Court\s+)?Order\s+(?:dated|entered|filed)\s+",
        re.IGNORECASE)),
    ("witness_reference", re.compile(
        r"\b(?:witness|testified|deponent|deposition\s+of)\s+\w+",
        re.IGNORECASE)),
    ("expert_report", re.compile(
        r"\b(?:expert\s+report|evaluation|assessment)\s+(?:of|by|from)\s+\w+",
        re.IGNORECASE)),
    ("statute_reference", re.compile(
        r"\bMCL\s+\d{2,4}\.\d+", re.IGNORECASE)),
    ("court_rule_reference", re.compile(
        r"\bMCR\s+\d+\.\d+", re.IGNORECASE)),
]


# ---------------------------------------------------------------------------
# EvidenceGapDetector
# ---------------------------------------------------------------------------

class EvidenceGapDetector:
    """Detect evidence gaps per filing type and generate acquisition tasks.

    Analyses filing text against a built-in requirement map for each filing
    type and lane, identifying missing, weak, incomplete, and
    unauthenticated evidence.  Produces a :class:`GapAnalysisReport` with
    prioritised gaps and acquisition tasks.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        """Initialise the detector.

        Args:
            db_path: Override path to ``litigation_context.db``.
                     Defaults to the standard repo-relative path.
        """
        _init_registry()
        self._db_path = db_path or _DB_PATH
        self._analyses_run: int = 0
        self._total_gaps_found: int = 0
        self._total_requirements_checked: int = 0
        logger.info("EvidenceGapDetector initialised (db=%s)", self._db_path)

    # ------------------------------------------------------------------
    # Database helpers
    # ------------------------------------------------------------------

    def _connect_db(self) -> Optional[sqlite3.Connection]:
        """Open a WAL-mode connection to the central database.

        Returns:
            A :class:`sqlite3.Connection` or ``None`` if the DB is missing.
        """
        if not self._db_path.exists():
            logger.warning("Database not found at %s", self._db_path)
            return None
        try:
            conn = sqlite3.connect(str(self._db_path), timeout=30)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA busy_timeout=60000")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA cache_size=-32000")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA synchronous=NORMAL")
            return conn
        except sqlite3.Error as exc:
            logger.error("DB connection failed: %s", exc)
            return None

    def _query_available_evidence(
        self, filing_type: str, lane: str,
    ) -> List[Dict[str, Any]]:
        """Query the DB for evidence items related to a filing/lane.

        Returns a list of dicts with keys: ``id``, ``source``, ``category``,
        ``description``, ``keywords``.
        """
        conn = self._connect_db()
        if conn is None:
            return []
        try:
            results: List[Dict[str, Any]] = []
            # Try several known evidence-related tables
            for table in ("evidence_items", "evidence_catalog",
                          "evidence_inventory", "evidence"):
                try:
                    cols = [
                        r[1] for r in
                        conn.execute(f"PRAGMA table_info({table})").fetchall()
                    ]
                    if not cols:
                        continue
                    # Build a safe select with available columns
                    select_cols = []
                    if "id" in cols or "evidence_id" in cols:
                        select_cols.append(
                            "id" if "id" in cols else "evidence_id AS id")
                    if "source" in cols or "source_file" in cols:
                        select_cols.append(
                            "source" if "source" in cols
                            else "source_file AS source")
                    if "category" in cols:
                        select_cols.append("category")
                    if "description" in cols:
                        select_cols.append("description")
                    if not select_cols:
                        continue
                    sql = f"SELECT {', '.join(select_cols)} FROM {table} LIMIT 5000"
                    rows = conn.execute(sql).fetchall()
                    for r in rows:
                        results.append(dict(r))
                    if results:
                        break
                except sqlite3.OperationalError:
                    continue
            return results
        except sqlite3.Error as exc:
            logger.error("Evidence query failed: %s", exc)
            return []
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def get_requirements(self, filing_type: str) -> List[EvidenceRequirement]:
        """Return all evidence requirements for *filing_type*.

        Args:
            filing_type: One of the registered filing types
                         (e.g. ``"custody_modification"``).

        Returns:
            Sorted list of :class:`EvidenceRequirement` objects.
        """
        _init_registry()
        reqs = _REQUIREMENT_REGISTRY.get(filing_type, [])
        if not reqs:
            logger.warning("No requirements registered for '%s'", filing_type)
        return sorted(reqs, key=lambda r: (
            _IMPORTANCE_WEIGHT.get(r.importance, 0)), reverse=True)

    def scan_for_evidence_in_text(self, text: str) -> List[str]:
        """Find evidence references present in the filing text.

        Scans *text* with compiled regex patterns to detect exhibit
        references, Bates stamps, affidavit cites, transcripts, etc.

        Args:
            text: Filing or motion text to scan.

        Returns:
            Deduplicated list of evidence reference strings found.
        """
        if not text:
            return []
        found: List[str] = []
        seen: Set[str] = set()
        for label, pattern in _EVIDENCE_PATTERNS:
            for m in pattern.finditer(text):
                ref = m.group().strip()
                key = ref.lower()
                if key not in seen:
                    seen.add(key)
                    found.append(f"[{label}] {ref}")
        return found

    def match_evidence(
        self,
        requirements: List[EvidenceRequirement],
        available_evidence: List[Dict[str, Any]],
        filing_text: str = "",
    ) -> List[EvidenceMatch]:
        """Match available evidence against requirements.

        Uses keyword overlap + text scanning to score each requirement
        against the evidence pool.

        Args:
            requirements: List of requirements to check.
            available_evidence: Evidence items from DB or external source.
            filing_text: Optional filing text to scan for inline evidence.

        Returns:
            List of :class:`EvidenceMatch` objects with quality scores.
        """
        matches: List[EvidenceMatch] = []
        text_lower = filing_text.lower() if filing_text else ""
        text_refs = self.scan_for_evidence_in_text(filing_text)
        text_refs_lower = " ".join(text_refs).lower()

        for req in requirements:
            best_quality = 0.0
            best_reason = ""
            best_evidence_id = ""
            best_source = ""

            # --- check DB evidence ---
            for ev in available_evidence:
                ev_text = " ".join(
                    str(v) for v in ev.values() if v
                ).lower()
                keyword_hits = sum(
                    1 for kw in req.keywords if kw.lower() in ev_text
                )
                if keyword_hits == 0:
                    continue
                quality = min(1.0, keyword_hits / max(len(req.keywords), 1))
                if quality > best_quality:
                    best_quality = quality
                    best_evidence_id = str(ev.get("id", "db_evidence"))
                    best_source = str(ev.get("source", "database"))
                    best_reason = (
                        f"DB evidence matched {keyword_hits}/{len(req.keywords)} "
                        f"keywords for {req.description}"
                    )

            # --- check inline text references ---
            if text_lower:
                keyword_hits_text = sum(
                    1 for kw in req.keywords if kw.lower() in text_lower
                )
                text_quality = min(
                    1.0, keyword_hits_text / max(len(req.keywords), 1))
                # Boost if explicit evidence references found
                ref_boost = 0.0
                for kw in req.keywords:
                    if kw.lower() in text_refs_lower:
                        ref_boost = 0.15
                        break
                text_quality = min(1.0, text_quality + ref_boost)
                if text_quality > best_quality:
                    best_quality = text_quality
                    best_evidence_id = "inline_text"
                    best_source = "filing_text"
                    best_reason = (
                        f"Filing text matched {keyword_hits_text}/"
                        f"{len(req.keywords)} keywords for {req.description}"
                    )

            if best_quality > 0:
                matches.append(EvidenceMatch(
                    req_id=req.req_id,
                    evidence_id=best_evidence_id,
                    source_file=best_source,
                    match_quality=round(best_quality, 3),
                    match_reason=best_reason,
                ))

        return matches

    def detect_gaps(
        self,
        requirements: List[EvidenceRequirement],
        matches: List[EvidenceMatch],
    ) -> List[EvidenceGap]:
        """Identify gaps by comparing requirements against matches.

        Args:
            requirements: Full requirement list.
            matches: Evidence matches produced by :meth:`match_evidence`.

        Returns:
            List of :class:`EvidenceGap` objects for unmet/weak requirements.
        """
        match_map: Dict[str, EvidenceMatch] = {m.req_id: m for m in matches}
        gaps: List[EvidenceGap] = []

        for req in requirements:
            m = match_map.get(req.req_id)

            if m is None:
                # Completely missing
                gap = EvidenceGap(
                    req_id=req.req_id,
                    requirement=req,
                    gap_type=GapType.MISSING.value,
                    severity=self._severity_for_importance(req.importance),
                    acquisition_task=self._generate_task(req, GapType.MISSING),
                    estimated_effort=self._estimate_effort(
                        req, GapType.MISSING),
                    alternative_sources=self._suggest_alternatives(req),
                )
                gaps.append(gap)
            elif m.match_quality < 0.3:
                # Very weak match
                gap = EvidenceGap(
                    req_id=req.req_id,
                    requirement=req,
                    gap_type=GapType.WEAK.value,
                    severity=self._severity_for_importance(req.importance),
                    acquisition_task=self._generate_task(req, GapType.WEAK),
                    estimated_effort=self._estimate_effort(req, GapType.WEAK),
                    alternative_sources=self._suggest_alternatives(req),
                )
                gaps.append(gap)
            elif m.match_quality < 0.6:
                # Incomplete — some evidence, but insufficient
                severity = ("medium" if req.importance in ("critical", "strong")
                            else "low")
                gap = EvidenceGap(
                    req_id=req.req_id,
                    requirement=req,
                    gap_type=GapType.INCOMPLETE.value,
                    severity=severity,
                    acquisition_task=self._generate_task(
                        req, GapType.INCOMPLETE),
                    estimated_effort=self._estimate_effort(
                        req, GapType.INCOMPLETE),
                    alternative_sources=self._suggest_alternatives(req),
                )
                gaps.append(gap)
            elif m.source_file in ("filing_text", "inline_text"):
                # Referenced in text but no authenticated backing document
                if req.category in ("documentary", "physical", "expert"):
                    gap = EvidenceGap(
                        req_id=req.req_id,
                        requirement=req,
                        gap_type=GapType.UNAUTHENTICATED.value,
                        severity="medium",
                        acquisition_task=self._generate_task(
                            req, GapType.UNAUTHENTICATED),
                        estimated_effort=EffortEstimate.IMMEDIATE.value,
                        alternative_sources=self._suggest_alternatives(req),
                    )
                    gaps.append(gap)

        return gaps

    def prioritize_gaps(self, gaps: List[EvidenceGap]) -> List[EvidenceGap]:
        """Sort gaps by severity × importance descending.

        Assigns a numeric ``priority_score`` to each gap and returns the
        list sorted highest-priority first.

        Args:
            gaps: Unsorted list of evidence gaps.

        Returns:
            Gaps sorted by priority descending.
        """
        for gap in gaps:
            sev = _SEVERITY_WEIGHT.get(gap.severity, 0.25)
            imp = _IMPORTANCE_WEIGHT.get(gap.requirement.importance, 0.25)
            # Missing > weak > incomplete > unauthenticated
            type_weight = {
                "missing": 1.0, "weak": 0.8,
                "incomplete": 0.5, "unauthenticated": 0.3,
            }.get(gap.gap_type, 0.5)
            gap.priority_score = round(sev * imp * type_weight, 4)

        return sorted(gaps, key=lambda g: g.priority_score, reverse=True)

    def generate_acquisition_plan(
        self, gaps: List[EvidenceGap],
    ) -> List[Dict[str, Any]]:
        """Convert prioritised gaps into actionable acquisition tasks.

        Args:
            gaps: Prioritised list of evidence gaps.

        Returns:
            List of task dictionaries with keys: ``task_id``, ``priority``,
            ``description``, ``effort``, ``alternatives``, ``filing_type``,
            ``mcr_basis``.
        """
        plan: List[Dict[str, Any]] = []
        for idx, gap in enumerate(gaps, start=1):
            plan.append({
                "task_id": f"ACQ-{idx:03d}",
                "priority": gap.priority_score,
                "severity": gap.severity,
                "gap_type": gap.gap_type,
                "requirement_id": gap.req_id,
                "description": gap.acquisition_task,
                "effort": gap.estimated_effort,
                "alternatives": gap.alternative_sources,
                "filing_type": gap.requirement.filing_type,
                "mcr_basis": gap.requirement.mcr_basis,
                "evidence_category": gap.requirement.category,
            })
        return plan

    def cross_lane_evidence_check(
        self, lane: str, filing_type: str,
    ) -> List[str]:
        """Identify evidence from other lanes that could support a filing.

        Args:
            lane: Current case lane (A-F).
            filing_type: Filing type being prepared.

        Returns:
            List of cross-lane evidence suggestions.
        """
        lane_upper = lane.upper()
        lane_map = _CROSS_LANE_EVIDENCE.get(lane_upper, {})
        suggestions = lane_map.get(filing_type, [])
        if not suggestions:
            logger.debug(
                "No cross-lane evidence mapped for lane=%s type=%s",
                lane_upper, filing_type,
            )
        return list(suggestions)

    def analyze_filing(
        self,
        filing_text: str,
        filing_type: str,
        lane: str,
        filing_id: Optional[str] = None,
    ) -> GapAnalysisReport:
        """Run a full gap analysis on a filing.

        This is the primary entry point.  It:
        1. Loads requirements for *filing_type*.
        2. Queries the DB for available evidence.
        3. Scans *filing_text* for inline evidence references.
        4. Matches evidence against requirements.
        5. Detects and prioritises gaps.
        6. Generates recommendations.

        Args:
            filing_text: Full text of the filing/motion.
            filing_type: E.g. ``"custody_modification"``.
            lane: Case lane (``"A"``–``"F"``).
            filing_id: Optional identifier for the filing.

        Returns:
            A :class:`GapAnalysisReport` with coverage score, gaps, and
            recommendations.
        """
        if filing_id is None:
            filing_id = hashlib.sha256(
                f"{filing_type}:{lane}:{datetime.now(timezone.utc).isoformat()}"
                .encode()
            ).hexdigest()[:12]

        logger.info(
            "Analysing filing: type=%s lane=%s id=%s",
            filing_type, lane, filing_id,
        )

        # 1. Requirements
        requirements = self.get_requirements(filing_type)
        if not requirements:
            logger.warning("No requirements for '%s' — returning empty report",
                           filing_type)
            return GapAnalysisReport(
                filing_id=filing_id, filing_type=filing_type, lane=lane,
                total_requirements=0, satisfied=0, gaps=[],
                coverage_pct=0.0, readiness_score=0.0, grade="F",
                recommendations=[
                    f"No requirement map for '{filing_type}'. "
                    "Define requirements before analysis."
                ],
            )

        # 2. Available evidence (DB)
        available = self._query_available_evidence(filing_type, lane)

        # 3-4. Match
        matches = self.match_evidence(requirements, available, filing_text)

        # 5. Detect and prioritise gaps
        gaps = self.detect_gaps(requirements, matches)
        gaps = self.prioritize_gaps(gaps)

        # 6. Metrics
        satisfied = len(requirements) - len(gaps)
        total = len(requirements)
        coverage = round((satisfied / total) * 100, 1) if total else 0.0

        # Readiness score — weighted by importance
        total_weight = sum(
            _IMPORTANCE_WEIGHT.get(r.importance, 0.25) for r in requirements
        )
        matched_weight = 0.0
        match_map = {m.req_id: m for m in matches}
        for req in requirements:
            m = match_map.get(req.req_id)
            if m and m.match_quality >= 0.6:
                matched_weight += (
                    _IMPORTANCE_WEIGHT.get(req.importance, 0.25)
                    * m.match_quality
                )
            elif m and m.match_quality >= 0.3:
                matched_weight += (
                    _IMPORTANCE_WEIGHT.get(req.importance, 0.25)
                    * m.match_quality * 0.5
                )
        readiness = round(
            (matched_weight / total_weight) * 100, 1
        ) if total_weight > 0 else 0.0

        grade = self._grade_from_score(readiness)

        # 7. Recommendations
        recommendations = self._build_recommendations(
            gaps, coverage, readiness, filing_type, lane,
        )

        report = GapAnalysisReport(
            filing_id=filing_id,
            filing_type=filing_type,
            lane=lane,
            total_requirements=total,
            satisfied=satisfied,
            gaps=gaps,
            coverage_pct=coverage,
            readiness_score=readiness,
            grade=grade,
            recommendations=recommendations,
        )

        # Stats tracking
        self._analyses_run += 1
        self._total_gaps_found += len(gaps)
        self._total_requirements_checked += total

        logger.info(
            "Analysis complete: coverage=%.1f%% readiness=%.1f grade=%s "
            "gaps=%d/%d",
            coverage, readiness, grade, len(gaps), total,
        )
        return report

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Return operational statistics.

        Returns:
            Dictionary of usage and performance metrics.
        """
        total_filing_types = len(_REQUIREMENT_REGISTRY)
        total_requirements = sum(
            len(v) for v in _REQUIREMENT_REGISTRY.values()
        )
        return {
            "analyses_run": self._analyses_run,
            "total_gaps_found": self._total_gaps_found,
            "total_requirements_checked": self._total_requirements_checked,
            "registered_filing_types": total_filing_types,
            "registered_requirements": total_requirements,
            "db_path": str(self._db_path),
            "db_exists": self._db_path.exists(),
            "supported_lanes": list(_LANE_FILING_TYPES.keys()),
            "evidence_categories": [e.value for e in EvidenceCategory],
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _severity_for_importance(importance: str) -> str:
        """Map requirement importance to gap severity."""
        return {
            "critical": "critical",
            "strong": "high",
            "supporting": "medium",
            "optional": "low",
        }.get(importance, "medium")

    @staticmethod
    def _generate_task(
        req: EvidenceRequirement, gap_type: GapType,
    ) -> str:
        """Generate a human-readable acquisition task description."""
        prefix_map = {
            GapType.MISSING: "Obtain",
            GapType.WEAK: "Strengthen",
            GapType.INCOMPLETE: "Complete",
            GapType.UNAUTHENTICATED: "Authenticate",
        }
        prefix = prefix_map.get(gap_type, "Address")
        return f"{prefix}: {req.description} (per {req.mcr_basis})"

    @staticmethod
    def _estimate_effort(
        req: EvidenceRequirement, gap_type: GapType,
    ) -> str:
        """Estimate acquisition effort for a gap."""
        if gap_type == GapType.UNAUTHENTICATED:
            return EffortEstimate.IMMEDIATE.value
        if req.category == "expert":
            return EffortEstimate.EXPERT_NEEDED.value
        if gap_type == GapType.INCOMPLETE:
            return EffortEstimate.DAYS.value
        if req.category in ("documentary", "digital"):
            return EffortEstimate.DAYS.value
        if req.category == "testimonial":
            return EffortEstimate.WEEKS.value
        if req.category == "physical":
            return EffortEstimate.DAYS.value
        return EffortEstimate.DAYS.value

    @staticmethod
    def _suggest_alternatives(req: EvidenceRequirement) -> List[str]:
        """Suggest alternative evidence sources for a requirement."""
        alt_map: Dict[str, List[str]] = {
            "documentary": [
                "Request from opposing party via discovery",
                "Subpoena from court or agency",
                "FOIA request to relevant government agency",
                "Obtain certified copies from court clerk",
            ],
            "testimonial": [
                "Affidavit from fact witness",
                "Deposition of party or witness",
                "Declaration under penalty of perjury",
                "Written interrogatory responses",
            ],
            "physical": [
                "Professional inspection and report",
                "Contemporaneous photographs with metadata",
                "Independent third-party documentation",
                "Video recording with timestamp",
            ],
            "digital": [
                "Forensic extraction from device",
                "Screen captures with authentication metadata",
                "Certified phone/email records from provider",
                "Social media preservation via third-party service",
            ],
            "expert": [
                "Retain qualified expert for evaluation",
                "Academic or professional literature supporting position",
                "Request court-appointed expert per MRE 706",
                "Engage expert from opposing jurisdiction for independence",
            ],
        }
        return alt_map.get(req.category, [
            "Consult with attorney for evidence acquisition strategy",
        ])

    @staticmethod
    def _grade_from_score(score: float) -> str:
        """Convert a 0-100 readiness score to a letter grade."""
        if score >= 90:
            return "A"
        if score >= 80:
            return "B"
        if score >= 70:
            return "C"
        if score >= 60:
            return "D"
        return "F"

    def _build_recommendations(
        self,
        gaps: List[EvidenceGap],
        coverage: float,
        readiness: float,
        filing_type: str,
        lane: str,
    ) -> List[str]:
        """Build prioritised recommendation strings.

        Args:
            gaps: Detected evidence gaps.
            coverage: Percentage of requirements satisfied.
            readiness: Weighted readiness score.
            filing_type: Type of filing being prepared.
            lane: Case lane.

        Returns:
            Ordered list of recommendation strings.
        """
        recs: List[str] = []

        # Critical gap warnings
        critical = [g for g in gaps if g.severity == "critical"]
        if critical:
            recs.append(
                f"CRITICAL: {len(critical)} critical evidence gap(s) must be "
                f"resolved before filing. Filing without these risks immediate "
                f"denial."
            )
            for cg in critical[:3]:
                recs.append(f"  → {cg.acquisition_task}")

        # Readiness assessment
        if readiness < 40:
            recs.append(
                f"Filing NOT READY (readiness {readiness:.0f}%). Significant "
                f"evidence gathering required."
            )
        elif readiness < 70:
            recs.append(
                f"Filing PARTIALLY READY (readiness {readiness:.0f}%). Address "
                f"high-priority gaps before filing."
            )
        elif readiness < 90:
            recs.append(
                f"Filing NEARLY READY (readiness {readiness:.0f}%). "
                f"Strengthen remaining weak points."
            )
        else:
            recs.append(
                f"Filing READY (readiness {readiness:.0f}%). Evidence coverage "
                f"is strong."
            )

        # Cross-lane suggestions
        cross = self.cross_lane_evidence_check(lane, filing_type)
        if cross:
            recs.append("Cross-lane evidence may strengthen this filing:")
            for c in cross:
                recs.append(f"  → {c}")

        # Category-specific advice
        cat_counts: Counter = Counter()
        for g in gaps:
            cat_counts[g.requirement.category] += 1
        if cat_counts.get("expert", 0) > 0:
            recs.append(
                f"Expert evidence needed for {cat_counts['expert']} "
                f"requirement(s). Begin expert retention early."
            )
        if cat_counts.get("testimonial", 0) > 1:
            recs.append(
                f"{cat_counts['testimonial']} testimonial gaps detected. "
                f"Schedule affidavits or depositions."
            )

        # Quick wins
        immediate = [
            g for g in gaps
            if g.estimated_effort == EffortEstimate.IMMEDIATE.value
        ]
        if immediate:
            recs.append(
                f"{len(immediate)} gap(s) can be resolved immediately "
                f"(authentication, formatting)."
            )

        return recs


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

def analyze_filing(
    filing_text: str,
    filing_type: str,
    lane: str,
    filing_id: Optional[str] = None,
) -> GapAnalysisReport:
    """Module-level convenience function.

    Creates a default :class:`EvidenceGapDetector` and runs analysis.
    """
    detector = EvidenceGapDetector()
    return detector.analyze_filing(filing_text, filing_type, lane, filing_id)


def get_supported_filing_types() -> List[str]:
    """Return all filing types with registered evidence requirements."""
    _init_registry()
    return sorted(_REQUIREMENT_REGISTRY.keys())


def get_supported_lanes() -> Dict[str, List[str]]:
    """Return lane → filing type mapping."""
    return dict(_LANE_FILING_TYPES)
