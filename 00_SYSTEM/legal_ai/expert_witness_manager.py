# -*- coding: utf-8 -*-
"""
Expert Witness Manager — LitigationOS Legal AI Subsystem
=========================================================
Expert witness identification, qualification analysis, and
management engine for Michigan family-law litigation.  Implements
MRE 702 (Daubert) four-factor qualification testing, expert report
review, deposition coordination, and cost tracking.

Case Context
------------
    Plaintiff:  Andrew James Pigors (Pro Se)
    Defendant:  Emily A. Watson
    Child:      L.D.W. (per MCR 8.119(H)) — Male
    Judge:      Hon. Jenny L. McNeill — 14th Circuit Court
    Cases:      2024-001507-DC, 2025-002760-CZ, 2023-5907-PP, COA 366810
    Lanes:      ALL (A through F)

Michigan Rules
--------------
    MRE 702 – Testimony by Experts (Daubert standard in Michigan)
    MRE 703 – Bases of Opinion Testimony by Experts
    MRE 704 – Opinion on Ultimate Issue
    MRE 705 – Disclosure of Facts or Data Underlying Expert Opinion
    MRE 706 – Court-Appointed Experts
    MCR 2.302(B)(4) – Discovery of Expert Opinions
    MCL 600.2955 – Daubert Standard (as adopted in Michigan)

Usage::

    from legal_ai.expert_witness_manager import ExpertWitnessManager

    ewm = ExpertWitnessManager()
    experts = ewm.identify_experts(field=ExpertField.CUSTODY_EVALUATION)
    report = ewm.get_stats()

Zero external dependencies.  CPU-first.  Local-only.
"""
from __future__ import annotations

import json
import logging
import sqlite3
import sys
import textwrap
import uuid
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger("legal_ai.expert_witness_manager")

# ---------------------------------------------------------------------------
# Path resolution  (never set CWD to repo root — shadow-module risk)
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[1]
_DB_PATH = _REPO / "litigation_context.db"

# ---------------------------------------------------------------------------
# Case constants
# ---------------------------------------------------------------------------
_PLAINTIFF = "Andrew James Pigors"
_DEFENDANT = "Emily A. Watson"
_CHILD_INITIALS = "L.D.W."
_JUDGE = "Hon. Jenny L. McNeill"
_COURT = "14th Circuit Court"

LANE_CASES: Dict[str, str] = {
    "A": "2024-001507-DC",
    "B": "2025-002760-CZ",
    "C": "Convergence",
    "D": "2023-5907-PP",
    "E": "JTC / Misconduct",
    "F": "COA 366810",
}


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class ExpertField(str, Enum):
    """Domains of expert testimony relevant to the litigation."""

    PSYCHOLOGY = "psychology"
    CHILD_DEVELOPMENT = "child_development"
    FORENSIC_ACCOUNTING = "forensic_accounting"
    REAL_ESTATE = "real_estate"
    DOMESTIC_VIOLENCE = "domestic_violence"
    CUSTODY_EVALUATION = "custody_evaluation"
    JUDICIAL_CONDUCT = "judicial_conduct"
    LAW_ENFORCEMENT = "law_enforcement"

    @property
    def relevant_lanes(self) -> List[str]:
        _lanes: Dict[str, List[str]] = {
            "psychology": ["A", "D"],
            "child_development": ["A"],
            "forensic_accounting": ["A", "B"],
            "real_estate": ["B"],
            "domestic_violence": ["A", "D"],
            "custody_evaluation": ["A"],
            "judicial_conduct": ["E", "F"],
            "law_enforcement": ["D"],
        }
        return _lanes.get(self.value, [])


class RetentionStatus(str, Enum):
    """Lifecycle status of an expert witness."""

    IDENTIFIED = "identified"
    CONTACTED = "contacted"
    RETAINED = "retained"
    REPORT_PENDING = "report_pending"
    REPORT_SUBMITTED = "report_submitted"
    DEPOSED = "deposed"
    TESTIFIED = "testified"
    WITHDRAWN = "withdrawn"

    @property
    def is_active(self) -> bool:
        return self.value not in ("withdrawn", "testified")


class ReportStatus(str, Enum):
    """Status of an expert report."""

    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    FINALIZED = "finalized"
    SUBMITTED = "submitted"
    SUPPLEMENTED = "supplemented"


class ChallengeType(str, Enum):
    """Types of Daubert / MRE 702 challenges."""

    QUALIFICATION = "qualification"
    METHODOLOGY = "methodology"
    RELIABILITY = "reliability"
    FIT = "fit"
    INSUFFICIENT_FACTS = "insufficient_facts"
    SPECULATION = "speculation"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class ExpertWitness:
    """An expert witness record."""

    expert_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str = ""
    field: ExpertField = ExpertField.PSYCHOLOGY
    qualifications: List[str] = field(default_factory=list)
    publications: List[str] = field(default_factory=list)
    testimony_history: List[str] = field(default_factory=list)
    hourly_rate: Decimal = Decimal("0.00")
    retention_status: RetentionStatus = RetentionStatus.IDENTIFIED
    availability: str = ""
    cv_path: str = ""
    notes: str = ""
    retained_for_lane: str = ""
    case_number: str = ""
    retained_date: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "expert_id": self.expert_id,
            "name": self.name,
            "field": self.field.value,
            "qualifications": self.qualifications,
            "publications": self.publications,
            "testimony_history": self.testimony_history,
            "hourly_rate": str(self.hourly_rate),
            "retention_status": self.retention_status.value,
            "availability": self.availability,
            "cv_path": self.cv_path,
            "notes": self.notes,
            "retained_for_lane": self.retained_for_lane,
            "case_number": self.case_number,
            "retained_date": self.retained_date,
            "created_at": self.created_at,
        }


@dataclass
class ExpertReport:
    """An expert witness report."""

    report_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    expert_id: str = ""
    expert_name: str = ""
    title: str = ""
    field: ExpertField = ExpertField.PSYCHOLOGY
    status: ReportStatus = ReportStatus.DRAFT
    methodology: str = ""
    findings: List[str] = field(default_factory=list)
    opinions: List[str] = field(default_factory=list)
    supporting_data: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    date_submitted: str = ""
    is_opposing: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "expert_id": self.expert_id,
            "expert_name": self.expert_name,
            "title": self.title,
            "field": self.field.value,
            "status": self.status.value,
            "methodology": self.methodology,
            "findings": self.findings,
            "opinions": self.opinions,
            "supporting_data": self.supporting_data,
            "weaknesses": self.weaknesses,
            "date_submitted": self.date_submitted,
            "is_opposing": self.is_opposing,
        }


@dataclass
class DaubertFactor:
    """One factor from the MRE 702 / MCL 600.2955 analysis."""

    factor_name: str = ""
    satisfied: bool = False
    analysis: str = ""
    score: int = 0  # 0-100
    authority: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DaubertAnalysisResult:
    """Complete Daubert / MRE 702 qualification analysis."""

    analysis_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    expert_name: str = ""
    expert_field: str = ""
    factors: List[DaubertFactor] = field(default_factory=list)
    overall_score: int = 0
    admissible: bool = False
    recommendation: str = ""
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "expert_name": self.expert_name,
            "expert_field": self.expert_field,
            "factors": [f.to_dict() for f in self.factors],
            "overall_score": self.overall_score,
            "admissible": self.admissible,
            "recommendation": self.recommendation,
            "generated_at": self.generated_at,
        }


@dataclass
class DepositionRecord:
    """Record of an expert deposition."""

    deposition_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    expert_id: str = ""
    expert_name: str = ""
    scheduled_date: str = ""
    location: str = ""
    duration_hours: Decimal = Decimal("0.0")
    cost: Decimal = Decimal("0.00")
    status: str = "scheduled"
    topics: List[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "deposition_id": self.deposition_id,
            "expert_id": self.expert_id,
            "expert_name": self.expert_name,
            "scheduled_date": self.scheduled_date,
            "location": self.location,
            "duration_hours": str(self.duration_hours),
            "cost": str(self.cost),
            "status": self.status,
            "topics": self.topics,
            "notes": self.notes,
        }


@dataclass
class ExpertCostSummary:
    """Cost tracking summary for expert witnesses."""

    total_retained: int = 0
    total_cost: Decimal = Decimal("0.00")
    by_expert: Dict[str, Decimal] = field(default_factory=dict)
    by_category: Dict[str, Decimal] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_retained": self.total_retained,
            "total_cost": str(self.total_cost),
            "by_expert": {k: str(v) for k, v in self.by_expert.items()},
            "by_category": {k: str(v) for k, v in self.by_category.items()},
        }


# ---------------------------------------------------------------------------
# DaubertAnalyzer
# ---------------------------------------------------------------------------


class DaubertAnalyzer:
    """MRE 702 / MCL 600.2955 four-factor Daubert analysis.

    Michigan adopted the Daubert standard through MCL 600.2955
    (effective 2004).  The four factors are:

    1. **Qualification** — Is the expert qualified by knowledge,
       skill, experience, training, or education?
    2. **Reliable principles** — Is the testimony based on
       sufficient facts or data and reliable principles/methods?
    3. **Reliable application** — Has the expert reliably applied
       the principles and methods to the facts of the case?
    4. **Fit** — Will the testimony help the trier of fact understand
       the evidence or determine a fact in issue?
    """

    _QUALIFICATION_INDICATORS = [
        "PhD", "PsyD", "MD", "JD", "MSW", "LCSW", "LPC",
        "board certified", "licensed", "published", "professor",
        "fellow", "diplomate", "certified",
    ]

    def check_qualification(self, witness: ExpertWitness) -> DaubertFactor:
        """Assess Factor 1: Expert qualification under MRE 702."""
        score = 0
        analysis_parts: List[str] = []

        # Check formal qualifications
        qual_text = " ".join(witness.qualifications).lower()
        indicators_found = sum(
            1 for ind in self._QUALIFICATION_INDICATORS
            if ind.lower() in qual_text
        )
        score += min(40, indicators_found * 10)
        analysis_parts.append(
            f"{indicators_found} qualification indicators found"
        )

        # Check publications
        if witness.publications:
            pub_score = min(30, len(witness.publications) * 5)
            score += pub_score
            analysis_parts.append(
                f"{len(witness.publications)} publications ({pub_score} pts)"
            )

        # Check testimony history
        if witness.testimony_history:
            test_score = min(30, len(witness.testimony_history) * 5)
            score += test_score
            analysis_parts.append(
                f"{len(witness.testimony_history)} prior testimony appearances "
                f"({test_score} pts)"
            )

        satisfied = score >= 50

        return DaubertFactor(
            factor_name="Qualification (MRE 702(a))",
            satisfied=satisfied,
            analysis="; ".join(analysis_parts),
            score=min(100, score),
            authority="MRE 702(a); MCL 600.2955(1)",
        )

    def analyze_methodology(
        self, witness: ExpertWitness, methodology_description: str = "",
    ) -> DaubertFactor:
        """Assess Factor 2: Reliable principles and methods."""
        score = 0
        analysis_parts: List[str] = []

        # Peer review / publication indicators
        if witness.publications:
            score += 25
            analysis_parts.append("Expert has peer-reviewed publications")

        # Methodology description assessment
        if methodology_description:
            method_lower = methodology_description.lower()
            method_indicators = [
                "peer-reviewed", "standardized", "validated",
                "generally accepted", "empirical", "replicable",
                "controlled study", "meta-analysis",
            ]
            found = sum(1 for ind in method_indicators if ind in method_lower)
            method_score = min(50, found * 10)
            score += method_score
            analysis_parts.append(
                f"{found} methodology reliability indicators ({method_score} pts)"
            )
        else:
            analysis_parts.append(
                "No methodology description provided — cannot fully assess"
            )

        # Field-specific reliability baseline
        reliable_fields = {
            ExpertField.FORENSIC_ACCOUNTING, ExpertField.REAL_ESTATE,
        }
        if witness.field in reliable_fields:
            score += 25
            analysis_parts.append(
                f"{witness.field.value} generally uses well-established methods"
            )

        return DaubertFactor(
            factor_name="Reliable Principles (MRE 702(b))",
            satisfied=score >= 50,
            analysis="; ".join(analysis_parts),
            score=min(100, score),
            authority="MRE 702(b); MCL 600.2955(1)",
        )

    def assess_reliability(
        self, witness: ExpertWitness, case_facts: str = "",
    ) -> DaubertFactor:
        """Assess Factor 3: Reliable application to case facts."""
        score = 0
        analysis_parts: List[str] = []

        # Prior testimony = established track record of application
        if witness.testimony_history:
            track_score = min(40, len(witness.testimony_history) * 8)
            score += track_score
            analysis_parts.append(
                f"Track record of {len(witness.testimony_history)} "
                f"prior applications"
            )

        # Case facts connection
        if case_facts:
            score += 30
            analysis_parts.append(
                "Case facts provided for application assessment"
            )
        else:
            analysis_parts.append(
                "No case facts provided — application assessment limited"
            )

        # Field relevance to case lanes
        relevant_lanes = witness.field.relevant_lanes
        if witness.retained_for_lane in relevant_lanes:
            score += 30
            analysis_parts.append(
                f"Field {witness.field.value} directly relevant to "
                f"Lane {witness.retained_for_lane}"
            )

        return DaubertFactor(
            factor_name="Reliable Application (MRE 702(c))",
            satisfied=score >= 50,
            analysis="; ".join(analysis_parts),
            score=min(100, score),
            authority="MRE 702(c); MCL 600.2955(1)",
        )

    def check_fit(
        self, witness: ExpertWitness, issues_in_case: Optional[List[str]] = None,
    ) -> DaubertFactor:
        """Assess Factor 4: Fit — helpfulness to trier of fact."""
        score = 0
        analysis_parts: List[str] = []

        # Field relevance mapping
        field_issues: Dict[str, List[str]] = {
            "psychology": ["mental health", "parenting capacity", "child impact"],
            "child_development": ["child welfare", "developmental needs", "attachment"],
            "forensic_accounting": ["financial disputes", "hidden assets", "damages"],
            "real_estate": ["property valuation", "housing conditions"],
            "domestic_violence": ["safety concerns", "protective orders", "abuse patterns"],
            "custody_evaluation": ["best interests", "parenting skills", "custodial environment"],
            "judicial_conduct": ["judicial bias", "procedural violations", "misconduct"],
            "law_enforcement": ["investigation procedures", "evidence handling"],
        }

        expert_issues = field_issues.get(witness.field.value, [])
        if issues_in_case:
            overlap = sum(
                1 for issue in issues_in_case
                if any(ei in issue.lower() for ei in expert_issues)
            )
            fit_score = min(60, overlap * 20)
            score += fit_score
            analysis_parts.append(
                f"{overlap} case issues overlap with expert's domain"
            )
        else:
            # Default fit based on field relevance to assigned lane
            if witness.retained_for_lane:
                lane_case = LANE_CASES.get(witness.retained_for_lane, "")
                if lane_case:
                    score += 40
                    analysis_parts.append(
                        f"Expert retained for Lane {witness.retained_for_lane} "
                        f"({lane_case})"
                    )

        # MRE 704 — opinion on ultimate issue is permitted in Michigan
        score += 20
        analysis_parts.append(
            "MRE 704 permits opinion on ultimate issue in Michigan"
        )

        return DaubertFactor(
            factor_name="Fit (MRE 702(d))",
            satisfied=score >= 50,
            analysis="; ".join(analysis_parts),
            score=min(100, score),
            authority="MRE 702(d); MRE 704; MCL 600.2955(1)",
        )

    def full_daubert_analysis(
        self,
        witness: ExpertWitness,
        methodology: str = "",
        case_facts: str = "",
        issues: Optional[List[str]] = None,
    ) -> DaubertAnalysisResult:
        """Run the complete four-factor Daubert analysis."""
        factors = [
            self.check_qualification(witness),
            self.analyze_methodology(witness, methodology),
            self.assess_reliability(witness, case_facts),
            self.check_fit(witness, issues),
        ]

        total_score = sum(f.score for f in factors)
        overall = total_score // len(factors) if factors else 0
        all_satisfied = all(f.satisfied for f in factors)

        if all_satisfied and overall >= 60:
            recommendation = "ADMISSIBLE — all four Daubert factors satisfied"
        elif overall >= 40:
            unsatisfied = [f.factor_name for f in factors if not f.satisfied]
            recommendation = (
                f"CONDITIONALLY ADMISSIBLE — factors not satisfied: "
                f"{', '.join(unsatisfied)}"
            )
        else:
            recommendation = (
                "LIKELY INADMISSIBLE — insufficient qualification under "
                "MRE 702 / MCL 600.2955"
            )

        return DaubertAnalysisResult(
            expert_name=witness.name,
            expert_field=witness.field.value,
            factors=factors,
            overall_score=overall,
            admissible=all_satisfied and overall >= 60,
            recommendation=recommendation,
        )

    def generate_qualification_memo(
        self, result: DaubertAnalysisResult,
    ) -> str:
        """Generate a qualification memorandum from Daubert analysis."""
        lines = [
            "MEMORANDUM RE: EXPERT WITNESS QUALIFICATION",
            f"Expert: {result.expert_name}",
            f"Field:  {result.expert_field}",
            f"Date:   {result.generated_at[:10]}",
            "=" * 60,
            "",
            "ANALYSIS UNDER MRE 702 / MCL 600.2955",
            "",
        ]
        for factor in result.factors:
            status = "SATISFIED" if factor.satisfied else "NOT SATISFIED"
            lines.append(f"Factor: {factor.factor_name}")
            lines.append(f"  Status: {status} (Score: {factor.score}/100)")
            lines.append(f"  Authority: {factor.authority}")
            lines.append(f"  Analysis: {factor.analysis}")
            lines.append("")

        lines.append(f"OVERALL SCORE: {result.overall_score}/100")
        lines.append(f"RECOMMENDATION: {result.recommendation}")
        return "\n".join(lines)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "DaubertAnalyzer",
            "qualification_indicators": len(self._QUALIFICATION_INDICATORS),
            "daubert_factors": 4,
            "authority": "MRE 702; MCL 600.2955",
        }


# ---------------------------------------------------------------------------
# ExpertReportReviewer
# ---------------------------------------------------------------------------


class ExpertReportReviewer:
    """Reviews expert reports for strengths, weaknesses, and rebuttal points."""

    # Common weakness patterns in expert reports
    _WEAKNESS_PATTERNS: List[Dict[str, str]] = [
        {
            "pattern": "reliance on self-report",
            "issue": "Report relies primarily on one party's self-report without "
                     "independent verification",
            "rebuttal": "Challenge under MRE 703 — insufficient factual basis",
        },
        {
            "pattern": "incomplete record review",
            "issue": "Expert did not review all relevant records or evidence",
            "rebuttal": "Expert failed to consider material evidence per MRE 703",
        },
        {
            "pattern": "outdated methodology",
            "issue": "Methods used are no longer current in the field",
            "rebuttal": "Challenge under MCL 600.2955(1) — methodology not "
                        "reliably applied",
        },
        {
            "pattern": "no standardized testing",
            "issue": "Expert did not use standardized assessment instruments",
            "rebuttal": "Without standardized measures, conclusions lack "
                        "scientific reliability per MRE 702",
        },
        {
            "pattern": "bias indicators",
            "issue": "Report shows potential evaluator bias (disproportionate "
                     "reliance on one party's narrative)",
            "rebuttal": "Demonstrate bias through comparison of time spent with "
                        "each party and selective citation of evidence",
        },
        {
            "pattern": "ultimate issue overreach",
            "issue": "Expert opinion exceeds expertise or speculates beyond data",
            "rebuttal": "While MRE 704 permits ultimate issue testimony, the "
                        "opinion must still be grounded in reliable methodology",
        },
    ]

    def review_report(
        self, report: ExpertReport,
    ) -> Dict[str, Any]:
        """Review an expert report for quality and vulnerabilities."""
        review: Dict[str, Any] = {
            "report_id": report.report_id,
            "expert": report.expert_name,
            "field": report.field.value,
            "is_opposing": report.is_opposing,
            "strengths": [],
            "weaknesses": [],
            "methodology_assessment": "",
            "overall_quality": "unknown",
        }

        # Assess strengths
        if report.supporting_data:
            review["strengths"].append(
                f"Report cites {len(report.supporting_data)} supporting data sources"
            )
        if report.methodology:
            review["strengths"].append("Methodology explicitly described")
            review["methodology_assessment"] = (
                f"Methodology described: {report.methodology[:100]}"
            )

        if report.findings:
            review["strengths"].append(
                f"{len(report.findings)} specific findings documented"
            )

        # Assess weaknesses (from report's own weakness list + pattern matching)
        review["weaknesses"] = list(report.weaknesses)

        if not report.methodology:
            review["weaknesses"].append(
                "No methodology described — vulnerable to Daubert challenge"
            )
        if not report.supporting_data:
            review["weaknesses"].append(
                "No supporting data cited — reliability questionable"
            )
        if len(report.opinions) > len(report.findings):
            review["weaknesses"].append(
                "More opinions than findings — potential speculation"
            )

        # Quality grade
        strength_count = len(review["strengths"])
        weakness_count = len(review["weaknesses"])
        if strength_count >= 3 and weakness_count <= 1:
            review["overall_quality"] = "strong"
        elif strength_count >= 2 and weakness_count <= 2:
            review["overall_quality"] = "adequate"
        else:
            review["overall_quality"] = "weak"

        return review

    def identify_weaknesses(
        self, report: ExpertReport,
    ) -> List[Dict[str, str]]:
        """Identify specific weaknesses using pattern library."""
        found: List[Dict[str, str]] = []
        report_text = " ".join([
            report.methodology,
            " ".join(report.findings),
            " ".join(report.opinions),
        ]).lower()

        for pattern in self._WEAKNESS_PATTERNS:
            if pattern["pattern"] in report_text:
                found.append({
                    "weakness": pattern["issue"],
                    "rebuttal_strategy": pattern["rebuttal"],
                })

        # Generic weaknesses
        if not report.supporting_data:
            found.append({
                "weakness": "No supporting data referenced in report",
                "rebuttal_strategy": "Challenge factual basis under MRE 703",
            })

        return found

    def compare_to_opposing(
        self,
        our_report: ExpertReport,
        opposing_report: ExpertReport,
    ) -> Dict[str, Any]:
        """Compare our expert's report to the opposing expert's."""
        comparison: Dict[str, Any] = {
            "our_expert": our_report.expert_name,
            "opposing_expert": opposing_report.expert_name,
            "our_findings_count": len(our_report.findings),
            "opposing_findings_count": len(opposing_report.findings),
            "conflicting_opinions": [],
            "our_advantages": [],
            "their_advantages": [],
        }

        # Compare data sources
        our_data = len(our_report.supporting_data)
        their_data = len(opposing_report.supporting_data)
        if our_data > their_data:
            comparison["our_advantages"].append(
                f"More supporting data cited ({our_data} vs {their_data})"
            )
        elif their_data > our_data:
            comparison["their_advantages"].append(
                f"More supporting data cited ({their_data} vs {our_data})"
            )

        # Compare methodology presence
        if our_report.methodology and not opposing_report.methodology:
            comparison["our_advantages"].append(
                "Our expert describes methodology; opposing does not"
            )
        elif opposing_report.methodology and not our_report.methodology:
            comparison["their_advantages"].append(
                "Opposing expert describes methodology; ours does not"
            )

        return comparison

    def generate_rebuttal_outline(
        self, opposing_report: ExpertReport,
    ) -> List[Dict[str, str]]:
        """Generate an outline for rebutting an opposing expert's report."""
        outline: List[Dict[str, str]] = []
        weaknesses = self.identify_weaknesses(opposing_report)

        for i, weakness in enumerate(weaknesses, 1):
            outline.append({
                "point": str(i),
                "attack": weakness["weakness"],
                "legal_basis": weakness["rebuttal_strategy"],
                "section": f"Rebuttal Point {i}",
            })

        # Standard rebuttal points
        outline.append({
            "point": str(len(outline) + 1),
            "attack": "Expert's opinions exceed the bounds of reliable methodology",
            "legal_basis": "MCL 600.2955(1) — reliable application requirement",
            "section": "Methodology Challenge",
        })

        return outline

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "ExpertReportReviewer",
            "weakness_patterns": len(self._WEAKNESS_PATTERNS),
        }


# ---------------------------------------------------------------------------
# DepositionCoordinator
# ---------------------------------------------------------------------------


class DepositionCoordinator:
    """Coordinates expert witness depositions."""

    _NOTICE_TEMPLATE = textwrap.dedent("""\
        STATE OF MICHIGAN
        IN THE {court}
        COUNTY OF MUSKEGON

        {plaintiff},                        Case No. {case_number}
            Plaintiff,                      Hon. {judge}
        v.
        {defendant},
            Defendant.
        ____________________________________________________________

        NOTICE OF DEPOSITION OF EXPERT WITNESS
        PURSUANT TO MCR 2.306 AND MCR 2.302(B)(4)

        TO: {opposing_party} and/or counsel of record

        PLEASE TAKE NOTICE that {deposing_party} will take the
        deposition upon oral examination of {expert_name},
        {expert_field} expert, at the following time and place:

            Date:     {depo_date}
            Time:     {depo_time}
            Location: {location}

        The deposition will be recorded by stenographic means.
        The deposition is being taken for purposes of discovery
        and/or for use at trial pursuant to MCR 2.308.

        Respectfully submitted,

        ________________________________________
        {deposing_party}
        Pro Se
    """)

    def __init__(self) -> None:
        self._depositions: List[DepositionRecord] = []

    def schedule_deposition(
        self,
        expert: ExpertWitness,
        scheduled_date: str,
        location: str = "",
        topics: Optional[List[str]] = None,
        estimated_hours: Decimal = Decimal("4.0"),
    ) -> DepositionRecord:
        """Schedule an expert deposition."""
        cost = expert.hourly_rate * estimated_hours
        record = DepositionRecord(
            expert_id=expert.expert_id,
            expert_name=expert.name,
            scheduled_date=scheduled_date,
            location=location or f"{_COURT} — Muskegon County, Michigan",
            duration_hours=estimated_hours,
            cost=cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            topics=topics or [],
        )
        self._depositions.append(record)
        return record

    def prepare_expert(
        self, expert: ExpertWitness, case_issues: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generate preparation materials for our expert's deposition."""
        prep: Dict[str, Any] = {
            "expert": expert.name,
            "field": expert.field.value,
            "preparation_checklist": [
                "Review all documents provided to expert",
                "Review expert's report and methodology",
                "Prepare for cross-examination on qualifications",
                "Review prior testimony transcripts for consistency",
                "Confirm opinions are within scope of expertise",
                "Prepare demonstrative exhibits if applicable",
            ],
            "anticipated_cross_topics": [],
            "documents_to_bring": [
                "Expert's complete file for this case",
                "CV / resume (current)",
                "List of cases testified in (last 4 years) per MCR 2.302(B)(4)(a)",
                "All documents relied upon in forming opinions",
                "Fee agreement and billing records",
            ],
        }

        # Field-specific cross-examination topics
        field_topics: Dict[str, List[str]] = {
            "psychology": [
                "Testing instruments used and their validity",
                "Hours spent with each party",
                "Peer-review status of methodology",
            ],
            "custody_evaluation": [
                "MCL 722.23 factors addressed",
                "Time spent with child vs each parent",
                "Collateral contacts made",
                "Standardized instruments administered",
            ],
            "forensic_accounting": [
                "Documents reviewed vs total available",
                "Assumptions underlying calculations",
                "Industry standards applied",
            ],
        }
        prep["anticipated_cross_topics"] = field_topics.get(
            expert.field.value, ["Qualifications", "Methodology", "Conclusions"]
        )

        return prep

    def generate_expert_notice(
        self,
        expert: ExpertWitness,
        deposition_date: str,
        deposition_time: str = "10:00 a.m.",
        location: str = "",
        case_number: str = "",
    ) -> str:
        """Generate a Notice of Expert Deposition."""
        return self._NOTICE_TEMPLATE.format(
            court=_COURT.upper(),
            plaintiff=_PLAINTIFF,
            defendant=_DEFENDANT,
            judge=_JUDGE,
            case_number=case_number or LANE_CASES.get(expert.retained_for_lane, ""),
            opposing_party=_DEFENDANT,
            deposing_party=_PLAINTIFF,
            expert_name=expert.name,
            expert_field=expert.field.value,
            depo_date=deposition_date,
            depo_time=deposition_time,
            location=location or f"{_COURT} — Muskegon County, Michigan",
        )

    def track_costs(self) -> ExpertCostSummary:
        """Track all deposition costs."""
        summary = ExpertCostSummary()
        for depo in self._depositions:
            summary.total_cost += depo.cost
            name = depo.expert_name or depo.expert_id
            summary.by_expert[name] = (
                summary.by_expert.get(name, Decimal("0.00")) + depo.cost
            )
        summary.total_retained = len(set(d.expert_id for d in self._depositions))
        return summary

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "DepositionCoordinator",
            "depositions_scheduled": len(self._depositions),
        }


# ---------------------------------------------------------------------------
# Database layer
# ---------------------------------------------------------------------------

_PRAGMAS = textwrap.dedent("""\
    PRAGMA busy_timeout = 60000;
    PRAGMA journal_mode = WAL;
    PRAGMA cache_size = -32000;
    PRAGMA temp_store = MEMORY;
    PRAGMA synchronous = NORMAL;
""")

_CREATE_EXPERTS_SQL = textwrap.dedent("""\
    CREATE TABLE IF NOT EXISTS expert_witnesses (
        expert_id         TEXT PRIMARY KEY,
        name              TEXT NOT NULL,
        field             TEXT NOT NULL,
        qualifications    TEXT,
        publications      TEXT,
        testimony_history TEXT,
        hourly_rate       TEXT DEFAULT '0.00',
        retention_status  TEXT DEFAULT 'identified',
        availability      TEXT,
        cv_path           TEXT,
        notes             TEXT,
        retained_for_lane TEXT,
        case_number       TEXT,
        retained_date     TEXT,
        created_at        TEXT DEFAULT (datetime('now')),
        updated_at        TEXT DEFAULT (datetime('now'))
    )
""")

_CREATE_REPORTS_SQL = textwrap.dedent("""\
    CREATE TABLE IF NOT EXISTS expert_reports (
        report_id       TEXT PRIMARY KEY,
        expert_id       TEXT NOT NULL,
        expert_name     TEXT,
        title           TEXT,
        field           TEXT,
        status          TEXT DEFAULT 'draft',
        methodology     TEXT,
        findings_json   TEXT,
        opinions_json   TEXT,
        data_json       TEXT,
        weaknesses_json TEXT,
        date_submitted  TEXT,
        is_opposing     INTEGER DEFAULT 0,
        created_at      TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (expert_id) REFERENCES expert_witnesses(expert_id)
    )
""")

_CREATE_DEPOSITIONS_SQL = textwrap.dedent("""\
    CREATE TABLE IF NOT EXISTS expert_depositions (
        deposition_id   TEXT PRIMARY KEY,
        expert_id       TEXT NOT NULL,
        expert_name     TEXT,
        scheduled_date  TEXT,
        location        TEXT,
        duration_hours  TEXT DEFAULT '0.0',
        cost            TEXT DEFAULT '0.00',
        status          TEXT DEFAULT 'scheduled',
        topics_json     TEXT,
        notes           TEXT,
        created_at      TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (expert_id) REFERENCES expert_witnesses(expert_id)
    )
""")

_CREATE_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_expert_field "
    "ON expert_witnesses(field, retention_status)",
    "CREATE INDEX IF NOT EXISTS idx_expert_lane "
    "ON expert_witnesses(retained_for_lane)",
    "CREATE INDEX IF NOT EXISTS idx_expert_reports_expert "
    "ON expert_reports(expert_id, status)",
    "CREATE INDEX IF NOT EXISTS idx_expert_depo_date "
    "ON expert_depositions(scheduled_date, status)",
]


def _ensure_tables(conn: sqlite3.Connection) -> None:
    conn.execute(_CREATE_EXPERTS_SQL)
    conn.execute(_CREATE_REPORTS_SQL)
    conn.execute(_CREATE_DEPOSITIONS_SQL)
    for idx in _CREATE_INDEXES_SQL:
        conn.execute(idx)
    conn.commit()


# ---------------------------------------------------------------------------
# ExpertWitnessManager — orchestrator
# ---------------------------------------------------------------------------


class ExpertWitnessManager:
    """Top-level orchestrator for expert witness management.

    Combines :class:`DaubertAnalyzer`, :class:`ExpertReportReviewer`,
    and :class:`DepositionCoordinator` into a unified expert witness
    lifecycle management system.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or _DB_PATH
        self._daubert = DaubertAnalyzer()
        self._reviewer = ExpertReportReviewer()
        self._depo_coordinator = DepositionCoordinator()
        self._experts: List[ExpertWitness] = []
        self._reports: List[ExpertReport] = []

    # -- expert management --

    def identify_experts(
        self, expert_field: Optional[ExpertField] = None,
        lane: Optional[str] = None,
    ) -> List[ExpertWitness]:
        """List experts, optionally filtered by field or lane."""
        results = self._experts
        if expert_field:
            results = [e for e in results if e.field == expert_field]
        if lane:
            results = [e for e in results if e.retained_for_lane == lane]
        return results

    def add_expert(
        self,
        name: str,
        expert_field: ExpertField,
        qualifications: Optional[List[str]] = None,
        publications: Optional[List[str]] = None,
        hourly_rate: Decimal = Decimal("0.00"),
        lane: str = "",
        case_number: str = "",
    ) -> ExpertWitness:
        """Register a new expert witness."""
        expert = ExpertWitness(
            name=name,
            field=expert_field,
            qualifications=qualifications or [],
            publications=publications or [],
            hourly_rate=hourly_rate,
            retained_for_lane=lane,
            case_number=case_number or LANE_CASES.get(lane, ""),
        )
        self._experts.append(expert)
        return expert

    def retain_expert(
        self, expert_id: str, lane: str = "", retained_date: str = "",
    ) -> bool:
        """Mark an expert as retained."""
        for expert in self._experts:
            if expert.expert_id == expert_id:
                expert.retention_status = RetentionStatus.RETAINED
                expert.retained_for_lane = lane or expert.retained_for_lane
                expert.retained_date = retained_date or date.today().isoformat()
                return True
        return False

    def update_status(
        self, expert_id: str, status: RetentionStatus,
    ) -> bool:
        """Update an expert's retention status."""
        for expert in self._experts:
            if expert.expert_id == expert_id:
                expert.retention_status = status
                return True
        return False

    # -- reports --

    def add_report(self, report: ExpertReport) -> None:
        """Register an expert report."""
        self._reports.append(report)

    def manage_reports(
        self, expert_id: Optional[str] = None,
    ) -> List[ExpertReport]:
        """List reports, optionally filtered by expert."""
        if expert_id:
            return [r for r in self._reports if r.expert_id == expert_id]
        return list(self._reports)

    def review_report(self, report: ExpertReport) -> Dict[str, Any]:
        """Delegate to the ExpertReportReviewer."""
        return self._reviewer.review_report(report)

    # -- Daubert challenges --

    def challenge_opposing_expert(
        self,
        witness: ExpertWitness,
        methodology: str = "",
        case_facts: str = "",
        issues: Optional[List[str]] = None,
    ) -> DaubertAnalysisResult:
        """Run a full Daubert challenge analysis on opposing expert."""
        return self._daubert.full_daubert_analysis(
            witness, methodology, case_facts, issues
        )

    def generate_qualification_memo(
        self, analysis: DaubertAnalysisResult,
    ) -> str:
        """Generate a qualification memorandum."""
        return self._daubert.generate_qualification_memo(analysis)

    # -- costs --

    def calculate_costs(self) -> ExpertCostSummary:
        """Calculate total expert witness costs."""
        summary = self._depo_coordinator.track_costs()

        # Add retention costs estimate (initial retainer)
        for expert in self._experts:
            if expert.retention_status.is_active and expert.hourly_rate > 0:
                # Estimate: 10 hours minimum engagement
                estimated = expert.hourly_rate * Decimal("10")
                name = expert.name or expert.expert_id
                summary.by_expert[name] = (
                    summary.by_expert.get(name, Decimal("0.00")) + estimated
                )
                summary.by_category["retention_estimate"] = (
                    summary.by_category.get("retention_estimate", Decimal("0.00"))
                    + estimated
                )
                summary.total_cost += estimated

        summary.total_retained = len([
            e for e in self._experts if e.retention_status.is_active
        ])
        return summary

    # -- persistence --

    def persist(self) -> int:
        """Write expert data to the database."""
        if not self._db_path.exists():
            logger.warning("Database not found — cannot persist")
            return 0

        try:
            conn = sqlite3.connect(str(self._db_path), timeout=60)
            conn.executescript(_PRAGMAS)
        except sqlite3.Error as exc:
            logger.error("DB connection failed: %s", exc)
            return 0

        try:
            _ensure_tables(conn)
            saved = 0

            # Persist experts
            expert_rows: List[Tuple[Any, ...]] = []
            for e in self._experts:
                expert_rows.append((
                    e.expert_id, e.name, e.field.value,
                    json.dumps(e.qualifications),
                    json.dumps(e.publications),
                    json.dumps(e.testimony_history),
                    str(e.hourly_rate),
                    e.retention_status.value,
                    e.availability, e.cv_path, e.notes,
                    e.retained_for_lane, e.case_number, e.retained_date,
                ))
            if expert_rows:
                conn.executemany(
                    "INSERT OR REPLACE INTO expert_witnesses "
                    "(expert_id, name, field, qualifications, publications, "
                    "testimony_history, hourly_rate, retention_status, "
                    "availability, cv_path, notes, retained_for_lane, "
                    "case_number, retained_date) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    expert_rows,
                )
                saved += len(expert_rows)

            # Persist reports
            report_rows: List[Tuple[Any, ...]] = []
            for r in self._reports:
                report_rows.append((
                    r.report_id, r.expert_id, r.expert_name, r.title,
                    r.field.value, r.status.value, r.methodology,
                    json.dumps(r.findings), json.dumps(r.opinions),
                    json.dumps(r.supporting_data),
                    json.dumps(r.weaknesses), r.date_submitted,
                    1 if r.is_opposing else 0,
                ))
            if report_rows:
                conn.executemany(
                    "INSERT OR REPLACE INTO expert_reports "
                    "(report_id, expert_id, expert_name, title, field, "
                    "status, methodology, findings_json, opinions_json, "
                    "data_json, weaknesses_json, date_submitted, is_opposing) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    report_rows,
                )
                saved += len(report_rows)

            conn.commit()
            return saved
        except sqlite3.Error as exc:
            logger.error("Persist failed: %s", exc)
            return 0
        finally:
            conn.close()

    # -- stats --

    def get_stats(self) -> Dict[str, Any]:
        """Return runtime statistics."""
        return {
            "module": "expert_witness_manager",
            "experts_loaded": len(self._experts),
            "reports_loaded": len(self._reports),
            "active_experts": len([
                e for e in self._experts if e.retention_status.is_active
            ]),
            "db_path": str(self._db_path),
            "daubert_analyzer": self._daubert.get_stats(),
            "report_reviewer": self._reviewer.get_stats(),
            "depo_coordinator": self._depo_coordinator.get_stats(),
        }

    def reset(self) -> None:
        """Clear all loaded experts and reports."""
        self._experts.clear()
        self._reports.clear()


# ---------------------------------------------------------------------------
# CLI demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sys.stdout = open(  # noqa: SIM115
        sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace"
    )
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print("=" * 60)
    print("  Expert Witness Manager — LitigationOS")
    print("=" * 60)
    print()

    ewm = ExpertWitnessManager()

    # Register an expert
    expert = ewm.add_expert(
        name="Dr. Jane Smith",
        expert_field=ExpertField.CUSTODY_EVALUATION,
        qualifications=["PhD Clinical Psychology", "Licensed Psychologist",
                        "Board Certified Forensic Examiner"],
        publications=["Journal of Family Psychology 2022",
                       "Child Development Quarterly 2023"],
        hourly_rate=Decimal("350.00"),
        lane="A",
    )
    ewm.retain_expert(expert.expert_id, lane="A")
    print(f"Expert registered: {expert.name} ({expert.field.value})")

    # Run Daubert analysis
    analysis = ewm.challenge_opposing_expert(
        witness=expert,
        methodology="Standardized psychological testing and clinical interview",
        issues=["best interests", "parenting capacity", "child welfare"],
    )
    print(f"Daubert Score: {analysis.overall_score}/100")
    print(f"Admissible: {analysis.admissible}")
    print(f"Recommendation: {analysis.recommendation}")
    print()

    # Cost summary
    costs = ewm.calculate_costs()
    print(f"Total expert costs: ${costs.total_cost}")
    print()

    stats = ewm.get_stats()
    print(f"Stats: {json.dumps(stats, indent=2)}")
