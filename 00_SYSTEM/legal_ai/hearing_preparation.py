# -*- coding: utf-8 -*-
"""
Hearing Preparation — LitigationOS Legal AI Subsystem
======================================================
Hearing and trial preparation engine for Michigan family-law
litigation.  Plans hearings, organises exhibits by issue, builds
legal arguments, prepares witness lists, generates proposed orders,
and produces court-ready hearing checklists.

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
    MCR 2.119(E)  — Oral Argument on Motions
    MCR 2.401     — Pretrial Conference
    MCR 2.501     — Trial Procedure
    MCR 2.507     — Findings by the Court
    MCR 2.517     — Proposed Findings and Conclusions
    MCR 3.210     — Domestic Relations — Hearing Procedures

Usage::

    from legal_ai.hearing_preparation import HearingPreparation

    hp = HearingPreparation()
    hp.prepare_full_hearing(...)

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
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger("legal_ai.hearing_preparation")

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
_CHILD_NAME_INITIALS = "L.D.W."
_JUDGE = "Hon. Jenny L. McNeill"
_COURT = "14th Circuit Court"
_COURT_ADDRESS = "Muskegon County Courthouse, 990 Terrace St, Muskegon, MI 49442"

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


class HearingType(str, Enum):
    """Types of hearings/proceedings."""

    MOTION = "motion"
    EVIDENTIARY = "evidentiary"
    STATUS = "status"
    PRETRIAL = "pretrial"
    TRIAL = "trial"
    SHOW_CAUSE = "show_cause"
    EMERGENCY = "emergency"
    SETTLEMENT = "settlement"

    @property
    def mcr_reference(self) -> str:
        _refs = {
            "motion": "MCR 2.119(E)",
            "evidentiary": "MCR 2.501",
            "status": "MCR 2.401",
            "pretrial": "MCR 2.401",
            "trial": "MCR 2.501",
            "show_cause": "MCR 3.606",
            "emergency": "MCR 2.119(F)",
            "settlement": "MCR 2.401(D)",
        }
        return _refs.get(self.value, "MCR 2.501")

    @property
    def typical_duration_minutes(self) -> int:
        _durations = {
            "motion": 30,
            "evidentiary": 120,
            "status": 15,
            "pretrial": 60,
            "trial": 480,
            "show_cause": 30,
            "emergency": 30,
            "settlement": 120,
        }
        return _durations.get(self.value, 60)


class HearingStatus(str, Enum):
    """Lifecycle statuses for a hearing."""

    SCHEDULED = "scheduled"
    PREPARED = "prepared"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CONTINUED = "continued"
    ADJOURNED = "adjourned"


class ArgumentStrength(str, Enum):
    """Strength assessment for a legal argument."""

    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    SPECULATIVE = "speculative"


class ExhibitStatus(str, Enum):
    """Admission status for an exhibit."""

    PROPOSED = "proposed"
    MARKED = "marked"
    ADMITTED = "admitted"
    OBJECTED = "objected"
    EXCLUDED = "excluded"
    WITHDRAWN = "withdrawn"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class WitnessEntry:
    """A witness expected to testify."""

    witness_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    name: str = ""
    role: str = ""
    testimony_topics: List[str] = field(default_factory=list)
    estimated_duration_minutes: int = 15
    subpoena_needed: bool = False
    subpoena_served: bool = False
    is_hostile: bool = False
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HearingExhibit:
    """An exhibit prepared for a hearing."""

    exhibit_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    exhibit_number: str = ""
    title: str = ""
    description: str = ""
    related_issues: List[str] = field(default_factory=list)
    status: ExhibitStatus = ExhibitStatus.PROPOSED
    copies_prepared: int = 3
    foundation_ready: bool = False
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d


@dataclass
class LegalArgument:
    """A legal argument for a hearing issue."""

    argument_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    issue: str = ""
    position: str = ""
    legal_basis: List[str] = field(default_factory=list)
    supporting_facts: List[str] = field(default_factory=list)
    supporting_exhibits: List[str] = field(default_factory=list)
    anticipated_opposition: str = ""
    rebuttal: str = ""
    strength: ArgumentStrength = ArgumentStrength.MODERATE
    case_law: List[str] = field(default_factory=list)
    statutory_authority: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["strength"] = self.strength.value
        return d


@dataclass
class HearingRecord:
    """A complete hearing record."""

    hearing_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    hearing_type: HearingType = HearingType.MOTION
    case_number: str = ""
    lane: str = ""
    court: str = _COURT
    judge: str = _JUDGE
    hearing_date: str = ""
    hearing_time: str = ""
    location: str = _COURT_ADDRESS
    issues: List[str] = field(default_factory=list)
    witnesses: List[WitnessEntry] = field(default_factory=list)
    exhibits: List[HearingExhibit] = field(default_factory=list)
    arguments: List[LegalArgument] = field(default_factory=list)
    status: HearingStatus = HearingStatus.SCHEDULED
    outcome: str = ""
    notes: str = ""
    proposed_order: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hearing_id": self.hearing_id,
            "hearing_type": self.hearing_type.value,
            "case_number": self.case_number,
            "lane": self.lane,
            "court": self.court,
            "judge": self.judge,
            "hearing_date": self.hearing_date,
            "hearing_time": self.hearing_time,
            "location": self.location,
            "issues": self.issues,
            "witnesses": [w.to_dict() for w in self.witnesses],
            "exhibits": [e.to_dict() for e in self.exhibits],
            "arguments": [a.to_dict() for a in self.arguments],
            "status": self.status.value,
            "outcome": self.outcome,
            "notes": self.notes,
            "proposed_order": self.proposed_order,
            "created_at": self.created_at,
        }


@dataclass
class HearingChecklist:
    """Pre-hearing preparation checklist."""

    checklist_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    hearing_id: str = ""
    items: List[Dict[str, Any]] = field(default_factory=list)
    completion_pct: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# HearingPlanner
# ---------------------------------------------------------------------------


class HearingPlanner:
    """Plans hearing outlines, witness lists, and exhibit requirements."""

    _STANDARD_CHECKLIST = [
        {"item": "File motion/brief at least 9 days before hearing (MCR 2.119(C)(1))",
         "category": "filing", "required": True},
        {"item": "Serve opposing party with all filed documents",
         "category": "service", "required": True},
        {"item": "Prepare 3 copies of all exhibits (court, witness, self)",
         "category": "exhibits", "required": True},
        {"item": "Confirm hearing date and time with court clerk",
         "category": "logistics", "required": True},
        {"item": "Prepare opening statement",
         "category": "argument", "required": False},
        {"item": "Prepare direct examination outlines for each witness",
         "category": "witness", "required": False},
        {"item": "Prepare cross-examination outlines for opposing witnesses",
         "category": "witness", "required": False},
        {"item": "Prepare proposed order",
         "category": "filing", "required": True},
        {"item": "Bring identification and case file",
         "category": "logistics", "required": True},
        {"item": "Review all exhibits for authentication readiness",
         "category": "exhibits", "required": True},
        {"item": f"Ensure child references use {_CHILD_INITIALS} per MCR 8.119(H)",
         "category": "compliance", "required": True},
        {"item": "Prepare timeline of relevant events",
         "category": "argument", "required": False},
    ]

    def prepare_hearing_outline(
        self, hearing: HearingRecord
    ) -> Dict[str, Any]:
        """Create a structured hearing outline."""
        outline: Dict[str, Any] = {
            "hearing_id": hearing.hearing_id,
            "type": hearing.hearing_type.value,
            "date": hearing.hearing_date,
            "case": hearing.case_number,
            "judge": hearing.judge,
            "estimated_duration": hearing.hearing_type.typical_duration_minutes,
            "mcr_reference": hearing.hearing_type.mcr_reference,
            "sections": [],
        }

        # Opening section
        if hearing.hearing_type in (HearingType.TRIAL, HearingType.EVIDENTIARY):
            outline["sections"].append({
                "title": "Opening Statement",
                "duration_minutes": 10,
                "notes": "Brief overview of positions and evidence to be presented",
            })

        # Issue sections
        for issue in hearing.issues:
            section = {
                "title": f"Issue: {issue}",
                "duration_minutes": 15,
                "exhibits": [
                    e.exhibit_number for e in hearing.exhibits
                    if issue in e.related_issues
                ],
                "witnesses": [
                    w.name for w in hearing.witnesses
                    if issue in w.testimony_topics
                ],
            }
            outline["sections"].append(section)

        # Closing
        if hearing.hearing_type in (HearingType.TRIAL, HearingType.EVIDENTIARY):
            outline["sections"].append({
                "title": "Closing Argument",
                "duration_minutes": 10,
                "notes": "Summarize evidence and legal basis for requested relief",
            })

        return outline

    def identify_required_exhibits(
        self, hearing: HearingRecord
    ) -> List[str]:
        """Identify exhibits needed for each hearing issue."""
        required: List[str] = []
        for issue in hearing.issues:
            relevant = [
                e.exhibit_number for e in hearing.exhibits
                if issue in e.related_issues
            ]
            if not relevant:
                required.append(f"MISSING EXHIBIT: No exhibit for issue '{issue}'")
            else:
                required.extend(relevant)
        return sorted(set(required))

    def prepare_witness_list(
        self, hearing: HearingRecord
    ) -> str:
        """Generate a formatted witness list."""
        lines = [
            "WITNESS LIST",
            f"Case No. {hearing.case_number}",
            f"Hearing Date: {hearing.hearing_date}",
            "",
            "| # | Name | Role | Topics | Est. Duration | Subpoena |",
            "|---|------|------|--------|---------------|----------|",
        ]
        for i, w in enumerate(hearing.witnesses, 1):
            topics = "; ".join(w.testimony_topics) if w.testimony_topics else "TBD"
            subpoena = "Yes" if w.subpoena_needed else "No"
            lines.append(
                f"| {i} | {w.name} | {w.role} | {topics} | "
                f"{w.estimated_duration_minutes} min | {subpoena} |"
            )
        return "\n".join(lines)

    def estimate_duration(self, hearing: HearingRecord) -> int:
        """Estimate total hearing duration in minutes."""
        base = hearing.hearing_type.typical_duration_minutes
        witness_time = sum(w.estimated_duration_minutes for w in hearing.witnesses)
        issue_time = len(hearing.issues) * 15
        return max(base, witness_time + issue_time + 20)

    def prepare_proposed_order(self, hearing: HearingRecord) -> str:
        """Generate a proposed order template."""
        lines = [
            "STATE OF MICHIGAN",
            f"IN THE {_COURT.upper()}",
            "COUNTY OF MUSKEGON",
            "",
            f"{_PLAINTIFF},".ljust(40) + f"Case No. {hearing.case_number}",
            "    Plaintiff,".ljust(40) + f"{hearing.judge}",
            "v.",
            f"{_DEFENDANT},",
            "    Defendant.",
            "_" * 60,
            "",
            "ORDER",
            "",
            f"At a session of said Court held on {hearing.hearing_date or '[DATE]'},",
            f"in Muskegon, Muskegon County, Michigan.",
            "",
            f"PRESENT: {hearing.judge}",
            "",
            "The Court, having considered the pleadings, evidence, and "
            "arguments of the parties, hereby ORDERS:",
            "",
        ]

        for i, issue in enumerate(hearing.issues, 1):
            lines.append(f"    {i}. [RULING on: {issue}]")
            lines.append("")

        lines.extend([
            "IT IS SO ORDERED.",
            "",
            f"Date: {'_' * 20}",
            "",
            f"{'_' * 40}",
            f"{hearing.judge}",
            f"{hearing.court}",
        ])
        return "\n".join(lines)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "HearingPlanner",
            "checklist_items": len(self._STANDARD_CHECKLIST),
            "hearing_types": len(HearingType),
        }


# ---------------------------------------------------------------------------
# ArgumentBuilder
# ---------------------------------------------------------------------------


class ArgumentBuilder:
    """Builds legal arguments for hearing issues."""

    _BEST_INTEREST_FACTORS = {
        "a": "Love, affection, and emotional ties — MCL 722.23(a)",
        "b": "Capacity to provide love, affection, guidance — MCL 722.23(b)",
        "c": "Capacity to provide food, clothing, medical care — MCL 722.23(c)",
        "d": "Length of time in stable environment — MCL 722.23(d)",
        "e": "Permanence of family unit — MCL 722.23(e)",
        "f": "Moral fitness of the parties — MCL 722.23(f)",
        "g": "Mental and physical health — MCL 722.23(g)",
        "h": "Home, school, and community record — MCL 722.23(h)",
        "i": "Reasonable preference of the child — MCL 722.23(i)",
        "j": "Willingness to facilitate relationship — MCL 722.23(j)",
        "k": "Domestic violence — MCL 722.23(k)",
        "l": "Any other relevant factor — MCL 722.23(l)",
    }

    def build_legal_argument(
        self,
        issue: str,
        position: str,
        legal_basis: Optional[List[str]] = None,
        supporting_facts: Optional[List[str]] = None,
        case_law: Optional[List[str]] = None,
    ) -> LegalArgument:
        """Build a structured legal argument for an issue."""
        return LegalArgument(
            issue=issue,
            position=position,
            legal_basis=legal_basis or [],
            supporting_facts=supporting_facts or [],
            case_law=case_law or [],
            strength=self._assess_strength(legal_basis, supporting_facts, case_law),
        )

    def prepare_opening_statement(
        self,
        hearing: HearingRecord,
        key_points: Optional[List[str]] = None,
    ) -> str:
        """Draft an opening statement for a hearing."""
        lines = [
            f"May it please the Court,",
            "",
            f"My name is {_PLAINTIFF}, and I appear pro se in this matter.",
            "",
            f"This hearing concerns {', '.join(hearing.issues) if hearing.issues else '[issues]'}.",
            "",
        ]

        if key_points:
            lines.append("The evidence will show:")
            for i, point in enumerate(key_points, 1):
                lines.append(f"    {i}. {point}")
            lines.append("")

        lines.extend([
            f"I respectfully ask the Court to consider the evidence and "
            f"grant the relief requested.",
            "",
        ])
        return "\n".join(lines)

    def prepare_closing_argument(
        self,
        hearing: HearingRecord,
        arguments: Sequence[LegalArgument],
    ) -> str:
        """Draft a closing argument summarizing key points."""
        lines = [
            "May it please the Court,",
            "",
            "The evidence presented today demonstrates the following:",
            "",
        ]

        for i, arg in enumerate(arguments, 1):
            lines.append(f"{i}. Regarding {arg.issue}:")
            lines.append(f"   {arg.position}")
            if arg.legal_basis:
                lines.append(f"   Legal basis: {', '.join(arg.legal_basis)}")
            lines.append("")

        lines.extend([
            f"For all of the foregoing reasons, {_PLAINTIFF} respectfully "
            f"requests the relief set forth in the motion.",
            "",
            "Thank you, Your Honor.",
        ])
        return "\n".join(lines)

    def anticipate_opposing_arguments(
        self,
        issue: str,
        our_position: str,
    ) -> List[Dict[str, str]]:
        """Generate potential opposing arguments and rebuttals."""
        anticipated: List[Dict[str, str]] = []

        # Standard opposition patterns
        patterns = [
            {
                "opposition": f"Defendant will argue that {_PLAINTIFF}'s claims "
                              f"regarding {issue} are unsupported by evidence.",
                "rebuttal": f"The evidence, including exhibits admitted today, "
                            f"directly supports {_PLAINTIFF}'s position on {issue}.",
            },
            {
                "opposition": f"Defendant may argue that the status quo should "
                              f"be maintained regarding {issue}.",
                "rebuttal": f"The best-interest factors, particularly MCL 722.23(j), "
                            f"support modification based on changed circumstances.",
            },
            {
                "opposition": f"Defendant may challenge the credibility of "
                              f"{_PLAINTIFF}'s evidence on {issue}.",
                "rebuttal": f"The evidence has been properly authenticated under "
                            f"MRE 901/902 and is corroborated by multiple sources.",
            },
        ]
        anticipated.extend(patterns)
        return anticipated

    def prepare_rebuttal(
        self, opposition_point: str, evidence_refs: Optional[List[str]] = None
    ) -> str:
        """Prepare a rebuttal to a specific opposition argument."""
        lines = [
            f"In response to opposing counsel's argument that {opposition_point}, "
            f"{_PLAINTIFF} submits:",
            "",
        ]
        if evidence_refs:
            lines.append("The following evidence directly contradicts this position:")
            for ref in evidence_refs:
                lines.append(f"    - {ref}")
        return "\n".join(lines)

    @staticmethod
    def _assess_strength(
        legal_basis: Optional[List[str]],
        facts: Optional[List[str]],
        case_law: Optional[List[str]],
    ) -> ArgumentStrength:
        score = 0
        if legal_basis:
            score += min(len(legal_basis), 3)
        if facts:
            score += min(len(facts), 3)
        if case_law:
            score += min(len(case_law), 2)

        if score >= 6:
            return ArgumentStrength.STRONG
        if score >= 3:
            return ArgumentStrength.MODERATE
        if score >= 1:
            return ArgumentStrength.WEAK
        return ArgumentStrength.SPECULATIVE

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "ArgumentBuilder",
            "best_interest_factors": len(self._BEST_INTEREST_FACTORS),
            "argument_strengths": len(ArgumentStrength),
        }


# ---------------------------------------------------------------------------
# ExhibitOrganizer
# ---------------------------------------------------------------------------


class ExhibitOrganizer:
    """Organizes exhibits by issue for hearing presentation."""

    def organize_by_issue(
        self, exhibits: Sequence[HearingExhibit]
    ) -> Dict[str, List[HearingExhibit]]:
        """Group exhibits by related issue."""
        by_issue: Dict[str, List[HearingExhibit]] = defaultdict(list)
        for ex in exhibits:
            if ex.related_issues:
                for issue in ex.related_issues:
                    by_issue[issue].append(ex)
            else:
                by_issue["unassigned"].append(ex)
        return dict(by_issue)

    def create_exhibit_list(
        self,
        exhibits: Sequence[HearingExhibit],
        case_number: str = "",
    ) -> str:
        """Generate a formatted exhibit list for the court."""
        lines = [
            "EXHIBIT LIST",
            f"Case No. {case_number}",
            "",
            "| # | Exhibit No. | Title | Status | Foundation |",
            "|---|-------------|-------|--------|------------|",
        ]
        for i, ex in enumerate(exhibits, 1):
            foundation = "Ready" if ex.foundation_ready else "Needed"
            lines.append(
                f"| {i} | {ex.exhibit_number} | {ex.title} | "
                f"{ex.status.value} | {foundation} |"
            )
        return "\n".join(lines)

    def prepare_exhibit_binder(
        self, exhibits: Sequence[HearingExhibit]
    ) -> Dict[str, Any]:
        """Create an exhibit binder structure with tabs."""
        binder: Dict[str, Any] = {
            "total_exhibits": len(exhibits),
            "tabs": [],
        }
        for i, ex in enumerate(exhibits, 1):
            binder["tabs"].append({
                "tab_number": i,
                "exhibit_number": ex.exhibit_number,
                "title": ex.title,
                "copies": ex.copies_prepared,
                "foundation_ready": ex.foundation_ready,
            })
        return binder

    def mark_for_admission(
        self,
        exhibit: HearingExhibit,
        status: ExhibitStatus = ExhibitStatus.MARKED,
    ) -> HearingExhibit:
        """Update exhibit admission status."""
        exhibit.status = status
        return exhibit

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "ExhibitOrganizer",
            "exhibit_statuses": len(ExhibitStatus),
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

_CREATE_HEARINGS_SQL = textwrap.dedent("""\
    CREATE TABLE IF NOT EXISTS hearings (
        hearing_id     TEXT PRIMARY KEY,
        hearing_type   TEXT NOT NULL,
        case_number    TEXT,
        lane           TEXT,
        court          TEXT,
        judge          TEXT,
        hearing_date   TEXT,
        hearing_time   TEXT,
        location       TEXT,
        issues_json    TEXT,
        status         TEXT DEFAULT 'scheduled',
        outcome        TEXT,
        notes          TEXT,
        proposed_order TEXT,
        created_at     TEXT DEFAULT (datetime('now')),
        updated_at     TEXT DEFAULT (datetime('now'))
    )
""")

_CREATE_HEARING_EXHIBITS_SQL = textwrap.dedent("""\
    CREATE TABLE IF NOT EXISTS hearing_exhibits (
        exhibit_id       TEXT PRIMARY KEY,
        hearing_id       TEXT NOT NULL,
        exhibit_number   TEXT,
        title            TEXT,
        related_issues   TEXT,
        status           TEXT DEFAULT 'proposed',
        foundation_ready INTEGER DEFAULT 0,
        created_at       TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (hearing_id) REFERENCES hearings(hearing_id)
    )
""")

_CREATE_ARGUMENTS_SQL = textwrap.dedent("""\
    CREATE TABLE IF NOT EXISTS hearing_arguments (
        argument_id   TEXT PRIMARY KEY,
        hearing_id    TEXT NOT NULL,
        issue         TEXT,
        position      TEXT,
        legal_basis   TEXT,
        strength      TEXT DEFAULT 'moderate',
        created_at    TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (hearing_id) REFERENCES hearings(hearing_id)
    )
""")

_CREATE_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_hearings_date "
    "ON hearings(hearing_date, status)",
    "CREATE INDEX IF NOT EXISTS idx_hearing_exhibits "
    "ON hearing_exhibits(hearing_id, status)",
    "CREATE INDEX IF NOT EXISTS idx_hearing_args "
    "ON hearing_arguments(hearing_id)",
]


def _ensure_tables(conn: sqlite3.Connection) -> None:
    conn.execute(_CREATE_HEARINGS_SQL)
    conn.execute(_CREATE_HEARING_EXHIBITS_SQL)
    conn.execute(_CREATE_ARGUMENTS_SQL)
    for idx in _CREATE_INDEXES_SQL:
        conn.execute(idx)
    conn.commit()


# ---------------------------------------------------------------------------
# HearingPreparation — orchestrator
# ---------------------------------------------------------------------------


class HearingPreparation:
    """Top-level orchestrator for hearing preparation.

    Combines :class:`HearingPlanner`, :class:`ArgumentBuilder`, and
    :class:`ExhibitOrganizer` into a unified workflow.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or _DB_PATH
        self._planner = HearingPlanner()
        self._arg_builder = ArgumentBuilder()
        self._exhibit_organizer = ExhibitOrganizer()
        self._hearings: List[HearingRecord] = []

    # -- hearing management --

    def create_hearing(
        self,
        hearing_type: HearingType,
        case_number: str,
        lane: str,
        hearing_date: str = "",
        hearing_time: str = "",
        issues: Optional[List[str]] = None,
    ) -> HearingRecord:
        """Create and register a new hearing."""
        hearing = HearingRecord(
            hearing_type=hearing_type,
            case_number=case_number,
            lane=lane,
            hearing_date=hearing_date,
            hearing_time=hearing_time,
            issues=issues or [],
        )
        self._hearings.append(hearing)
        return hearing

    def add_hearing(self, hearing: HearingRecord) -> None:
        """Add an existing hearing record."""
        self._hearings.append(hearing)

    def get_hearing(self, hearing_id: str) -> Optional[HearingRecord]:
        """Retrieve a hearing by ID."""
        for h in self._hearings:
            if h.hearing_id == hearing_id:
                return h
        return None

    # -- full preparation --

    def prepare_full_hearing(
        self,
        hearing: HearingRecord,
        key_points: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Run full hearing preparation pipeline."""
        result: Dict[str, Any] = {
            "hearing_id": hearing.hearing_id,
            "outline": self._planner.prepare_hearing_outline(hearing),
            "duration_estimate": self._planner.estimate_duration(hearing),
            "witness_list": self._planner.prepare_witness_list(hearing),
            "required_exhibits": self._planner.identify_required_exhibits(hearing),
        }

        if hearing.exhibits:
            result["exhibit_list"] = self._exhibit_organizer.create_exhibit_list(
                hearing.exhibits, hearing.case_number
            )
            result["exhibit_binder"] = self._exhibit_organizer.prepare_exhibit_binder(
                hearing.exhibits
            )

        if hearing.hearing_type in (HearingType.TRIAL, HearingType.EVIDENTIARY):
            result["opening_statement"] = self._arg_builder.prepare_opening_statement(
                hearing, key_points
            )

        result["proposed_order"] = self._planner.prepare_proposed_order(hearing)
        hearing.status = HearingStatus.PREPARED
        return result

    # -- checklist --

    def generate_hearing_checklist(
        self, hearing: HearingRecord
    ) -> HearingChecklist:
        """Generate a pre-hearing preparation checklist."""
        items: List[Dict[str, Any]] = []
        for item in self._planner._STANDARD_CHECKLIST:
            items.append({
                **item,
                "completed": False,
            })

        # Add witness-specific items
        for w in hearing.witnesses:
            if w.subpoena_needed:
                items.append({
                    "item": f"Serve subpoena on {w.name}",
                    "category": "witness",
                    "required": True,
                    "completed": w.subpoena_served,
                })

        # Add exhibit-specific items
        for ex in hearing.exhibits:
            if not ex.foundation_ready:
                items.append({
                    "item": f"Prepare foundation for Exhibit {ex.exhibit_number}",
                    "category": "exhibits",
                    "required": True,
                    "completed": False,
                })

        completed = sum(1 for i in items if i.get("completed"))
        checklist = HearingChecklist(
            hearing_id=hearing.hearing_id,
            items=items,
            completion_pct=round((completed / len(items) * 100) if items else 0, 1),
        )
        return checklist

    # -- persistence --

    def persist(self) -> int:
        """Write hearings to the database."""
        if not self._db_path.exists():
            logger.warning("Database not found — cannot persist")
            return 0

        try:
            conn = sqlite3.connect(str(self._db_path), timeout=60)
            conn.executescript(_PRAGMAS)
        except sqlite3.Error as exc:
            logger.error("DB connection failed: %s", exc)
            return 0

        written = 0
        try:
            _ensure_tables(conn)
            for hearing in self._hearings:
                conn.execute(
                    "INSERT OR REPLACE INTO hearings "
                    "(hearing_id, hearing_type, case_number, lane, court, "
                    "judge, hearing_date, hearing_time, location, "
                    "issues_json, status, outcome, notes, proposed_order) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        hearing.hearing_id,
                        hearing.hearing_type.value,
                        hearing.case_number,
                        hearing.lane,
                        hearing.court,
                        hearing.judge,
                        hearing.hearing_date,
                        hearing.hearing_time,
                        hearing.location,
                        json.dumps(hearing.issues),
                        hearing.status.value,
                        hearing.outcome,
                        hearing.notes,
                        hearing.proposed_order,
                    ),
                )

                for ex in hearing.exhibits:
                    conn.execute(
                        "INSERT OR REPLACE INTO hearing_exhibits "
                        "(exhibit_id, hearing_id, exhibit_number, title, "
                        "related_issues, status, foundation_ready) "
                        "VALUES (?,?,?,?,?,?,?)",
                        (
                            ex.exhibit_id,
                            hearing.hearing_id,
                            ex.exhibit_number,
                            ex.title,
                            json.dumps(ex.related_issues),
                            ex.status.value,
                            1 if ex.foundation_ready else 0,
                        ),
                    )

                for arg in hearing.arguments:
                    conn.execute(
                        "INSERT OR REPLACE INTO hearing_arguments "
                        "(argument_id, hearing_id, issue, position, "
                        "legal_basis, strength) VALUES (?,?,?,?,?,?)",
                        (
                            arg.argument_id,
                            hearing.hearing_id,
                            arg.issue,
                            arg.position,
                            json.dumps(arg.legal_basis),
                            arg.strength.value,
                        ),
                    )

                written += 1
            conn.commit()
        except sqlite3.Error as exc:
            logger.error("Persist failed: %s", exc)
        finally:
            conn.close()

        return written

    # -- stats --

    def get_stats(self) -> Dict[str, Any]:
        return {
            "module": "hearing_preparation",
            "hearings_loaded": len(self._hearings),
            "total_witnesses": sum(
                len(h.witnesses) for h in self._hearings
            ),
            "total_exhibits": sum(
                len(h.exhibits) for h in self._hearings
            ),
            "db_path": str(self._db_path),
            "planner": self._planner.get_stats(),
            "argument_builder": self._arg_builder.get_stats(),
            "exhibit_organizer": self._exhibit_organizer.get_stats(),
        }

    def reset(self) -> None:
        self._hearings.clear()


# ---------------------------------------------------------------------------
# CLI demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sys.stdout = open(  # noqa: SIM115
        sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace"
    )
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print("=" * 60)
    print("  Hearing Preparation — LitigationOS")
    print("=" * 60)
    print()

    hp = HearingPreparation()
    hearing = hp.create_hearing(
        hearing_type=HearingType.EVIDENTIARY,
        case_number="2024-001507-DC",
        lane="A",
        hearing_date="2025-03-15",
        hearing_time="9:00 AM",
        issues=["Custody modification", "Parenting time"],
    )

    hearing.witnesses.append(WitnessEntry(
        name=_PLAINTIFF,
        role="Plaintiff / Father",
        testimony_topics=["Custody modification", "Parenting time"],
        estimated_duration_minutes=30,
    ))
    hearing.exhibits.append(HearingExhibit(
        exhibit_number="A-001",
        title="Text messages re: parenting time",
        related_issues=["Parenting time"],
        foundation_ready=True,
    ))

    prep = hp.prepare_full_hearing(hearing, key_points=[
        f"{_DEFENDANT} has systematically interfered with parenting time",
        f"Best-interest factors, especially MCL 722.23(j), favor modification",
    ])

    print(f"Hearing prepared: {hearing.hearing_id}")
    print(f"Estimated duration: {prep['duration_estimate']} minutes")
    print()
    print(prep["witness_list"])
    print()
    print("--- Stats ---")
    import pprint

    pprint.pprint(hp.get_stats())
