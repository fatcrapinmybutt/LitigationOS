# -*- coding: utf-8 -*-
"""
Timeline Forensics — LitigationOS Legal AI Subsystem
=====================================================
Chronological event reconstruction, contradiction detection, gap analysis,
and forensic timeline reporting across all six case lanes of the Pigors v.
Watson litigation.

Builds master timelines from multiple source types (transcripts, filings,
exhibits, records, police reports, social media), detects temporal and
factual contradictions, identifies evidence gaps, and generates
court-ready visualisations (Mermaid, HTML, CSV).

Case Lanes:
    Lane A — Custody (2024-001507-DC)
    Lane B — Housing (2025-002760-CZ)
    Lane C — Convergence (cross-lane)
    Lane D — PPO (2023-5907-PP)
    Lane E — Misconduct / JTC (Judge McNeill)
    Lane F — Appellate (COA 366810)

Key Timelines:
    1. Custody Timeline:    Sept 2023 → present
    2. PPO Timeline:        2023-5907-PP filing through modifications
    3. Housing Timeline:    Shady Oaks residency, habitability, eviction
    4. Judicial Conduct:    McNeill ex parte contacts, bias, recusal refusals
    5. Court Filing:        All filings across all courts

Michigan-Specific:
    MCL 722.23 — Best interest factors (tracked over time)
    MCR 2.308  — Deposition use at trial (timeline evidence)
    MCL 600.2950 — PPO timeline requirements

Case Context:
    Plaintiff:  Andrew James Pigors (Pro Se)
    Defendant:  Emily A. Watson
    Child:      L.D.W. (per MCR 8.119(H)) — Male
    Judge:      Hon. Jenny L. McNeill — 14th Circuit Court

Usage:
    from legal_ai.timeline_forensics import TimelineForensics

    engine = TimelineForensics()
    engine.build_master_timeline()
    contradictions = engine.analyze_contradictions()
    report = engine.generate_forensic_report()
    stats = engine.get_stats()

Zero external dependencies.  CPU-first.  Local-only.
"""
from __future__ import annotations

import csv
import hashlib
import html as html_mod
import io
import json
import logging
import re
import sqlite3
import textwrap
import uuid
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("legal_ai.timeline_forensics")

# ---------------------------------------------------------------------------
# Path resolution — legal_ai → 00_SYSTEM → LitigationOS root
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
_DB_PATH = _HERE.parents[1] / "litigation_context.db"

# ---------------------------------------------------------------------------
# Case Constants
# ---------------------------------------------------------------------------
_PLAINTIFF = "Andrew James Pigors"
_DEFENDANT = "Emily A. Watson"
_CHILD_INITIALS = "L.D.W."
_CHILD_NAME = "Lincoln David Watson"
_JUDGE = "Hon. Jenny L. McNeill"

LANE_LABELS: Dict[str, str] = {
    "A": "Custody (2024-001507-DC)",
    "B": "Housing (2025-002760-CZ)",
    "C": "Convergence (cross-lane)",
    "D": "PPO (2023-5907-PP)",
    "E": "Misconduct / JTC",
    "F": "Appellate (COA 366810)",
}

LANE_CASE_NUMBERS: Dict[str, str] = {
    "A": "2024-001507-DC",
    "B": "2025-002760-CZ",
    "C": "Multi-lane",
    "D": "2023-5907-PP",
    "E": "Judge McNeill",
    "F": "COA 366810",
}

_LANE_COLORS: Dict[str, str] = {
    "A": "#3b82f6",
    "B": "#22c55e",
    "C": "#a855f7",
    "D": "#f97316",
    "E": "#ef4444",
    "F": "#06b6d4",
}


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class SourceType(str, Enum):
    """Types of evidence sources."""
    TRANSCRIPT = "transcript"
    FILING = "filing"
    EXHIBIT = "exhibit"
    RECORD = "record"
    POLICE_REPORT = "police_report"
    SOCIAL_MEDIA = "social_media"
    AFFIDAVIT = "affidavit"
    COURT_ORDER = "court_order"
    COMMUNICATION = "communication"
    MEDICAL = "medical"


class EventTag(str, Enum):
    """Event classification tags."""
    CUSTODY_EXCHANGE = "custody_exchange"
    CUSTODY_DENIAL = "custody_denial"
    COURT_HEARING = "court_hearing"
    FILING = "filing"
    ORDER_ENTERED = "order_entered"
    PPO_EVENT = "ppo_event"
    HOUSING_ISSUE = "housing_issue"
    JUDICIAL_CONDUCT = "judicial_conduct"
    EX_PARTE = "ex_parte"
    EVIDENCE_DISCOVERY = "evidence_discovery"
    SERVICE_OF_PROCESS = "service_of_process"
    DEADLINE = "deadline"
    POLICE_CONTACT = "police_contact"
    MEDICAL_EVENT = "medical_event"
    SCHOOL_EVENT = "school_event"
    COMMUNICATION = "communication"


class ContradictionSeverity(str, Enum):
    """Severity of detected contradictions."""
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


class GapCategory(str, Enum):
    """Categories of timeline / evidence gaps."""
    TEMPORAL = "temporal"
    EVIDENCE = "evidence"
    SUPPRESSED = "suppressed"
    COVERAGE = "coverage"


# ---------------------------------------------------------------------------
# Best Interest Factors (MCL 722.23)
# ---------------------------------------------------------------------------

BEST_INTEREST_FACTORS: Dict[str, str] = {
    "a": "Love, affection, and emotional ties",
    "b": "Capacity to give love, affection, and guidance",
    "c": "Capacity to provide food, clothing, medical care",
    "d": "Length of time in stable, satisfactory environment",
    "e": "Permanence of existing or proposed custodial home",
    "f": "Moral fitness of parties",
    "g": "Mental and physical health of parties",
    "h": "Home, school, and community record of child",
    "i": "Reasonable preference of child (if of sufficient age)",
    "j": "Willingness to facilitate parent-child relationship",
    "k": "Domestic violence",
    "l": "Any other relevant factor",
}


# ---------------------------------------------------------------------------
# Database Helpers
# ---------------------------------------------------------------------------

def _connect(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Open a WAL-mode connection with safe PRAGMAs."""
    path = db_path or _DB_PATH
    conn = sqlite3.connect(str(path), timeout=60)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    """Check if a table exists in the database."""
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row is not None


_TIMELINE_EVENTS_DDL = """\
CREATE TABLE IF NOT EXISTS timeline_events (
    id              TEXT PRIMARY KEY,
    event_date      TEXT NOT NULL,
    end_date        TEXT,
    description     TEXT NOT NULL,
    source_type     TEXT NOT NULL DEFAULT 'record',
    source_ref      TEXT,
    page_ref        TEXT,
    actors_json     TEXT,
    lane            TEXT NOT NULL DEFAULT 'A',
    tags_json       TEXT,
    confidence      REAL DEFAULT 75.0,
    contradicts_json TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
)
"""

_TIMELINE_CONTRADICTIONS_DDL = """\
CREATE TABLE IF NOT EXISTS timeline_contradictions (
    id              TEXT PRIMARY KEY,
    event_a_id      TEXT NOT NULL,
    event_b_id      TEXT NOT NULL,
    contradiction_type TEXT NOT NULL,
    severity        TEXT NOT NULL DEFAULT 'moderate',
    description     TEXT,
    impeachment_use TEXT,
    created_at      TEXT NOT NULL,
    FOREIGN KEY (event_a_id) REFERENCES timeline_events(id),
    FOREIGN KEY (event_b_id) REFERENCES timeline_events(id)
)
"""

_TIMELINE_GAPS_DDL = """\
CREATE TABLE IF NOT EXISTS timeline_gaps (
    id              TEXT PRIMARY KEY,
    gap_category    TEXT NOT NULL DEFAULT 'temporal',
    start_date      TEXT,
    end_date        TEXT,
    description     TEXT,
    lane            TEXT,
    severity        TEXT DEFAULT 'moderate',
    discovery_recommendation TEXT,
    created_at      TEXT NOT NULL
)
"""


def _ensure_tables(conn: sqlite3.Connection) -> None:
    """Create required tables if they don't exist."""
    conn.execute(_TIMELINE_EVENTS_DDL)
    conn.execute(_TIMELINE_CONTRADICTIONS_DDL)
    conn.execute(_TIMELINE_GAPS_DDL)
    conn.commit()


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class EventSource:
    """A source of timeline events."""

    source_id: str = ""
    source_type: str = SourceType.RECORD.value
    file_path: str = ""
    date_range: Tuple[str, str] = ("", "")
    event_count: int = 0
    reliability_score: float = 75.0

    def __post_init__(self) -> None:
        if not self.source_id:
            self.source_id = str(uuid.uuid4())[:12]

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to dictionary."""
        return {
            "source_id": self.source_id,
            "source_type": self.source_type,
            "file_path": self.file_path,
            "date_range": list(self.date_range),
            "event_count": self.event_count,
            "reliability_score": self.reliability_score,
        }


@dataclass
class TimelineEvent:
    """A single event on the master timeline."""

    event_id: str = ""
    date: str = ""           # ISO format: YYYY-MM-DD
    end_date: str = ""       # Optional — for span events
    description: str = ""
    source_type: str = SourceType.RECORD.value
    source_ref: str = ""
    page_ref: str = ""
    actors: List[str] = field(default_factory=list)
    lane: str = "A"
    tags: List[str] = field(default_factory=list)
    confidence: float = 75.0
    contradicts: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.event_id:
            self.event_id = str(uuid.uuid4())[:12]

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to dictionary."""
        return asdict(self)

    def overlaps(self, other: TimelineEvent) -> bool:
        """Check if this event's time range overlaps with another."""
        if not self.date or not other.date:
            return False
        s1 = self.date
        e1 = self.end_date or self.date
        s2 = other.date
        e2 = other.end_date or other.date
        return s1 <= e2 and s2 <= e1

    def contradicts_event(self, other: TimelineEvent) -> bool:
        """Check if this event contradicts another (same actors, same time, different claims)."""
        if not self.overlaps(other):
            return False
        shared_actors = set(self.actors) & set(other.actors)
        if not shared_actors:
            return False
        return self.description.lower() != other.description.lower()

    def _parse_date(self) -> Optional[date]:
        """Parse the date string into a date object."""
        try:
            return datetime.strptime(self.date, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None


@dataclass
class Contradiction:
    """A detected contradiction between two events."""

    contradiction_id: str = ""
    event_a_id: str = ""
    event_b_id: str = ""
    contradiction_type: str = "factual"  # temporal, factual, record
    severity: str = ContradictionSeverity.MODERATE.value
    description: str = ""
    impeachment_use: str = ""

    def __post_init__(self) -> None:
        if not self.contradiction_id:
            self.contradiction_id = str(uuid.uuid4())[:12]

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to dictionary."""
        return asdict(self)


@dataclass
class TimelineGap:
    """An identified gap in the timeline or evidence."""

    gap_id: str = ""
    gap_category: str = GapCategory.TEMPORAL.value
    start_date: str = ""
    end_date: str = ""
    description: str = ""
    lane: str = ""
    severity: str = "moderate"
    discovery_recommendation: str = ""

    def __post_init__(self) -> None:
        if not self.gap_id:
            self.gap_id = str(uuid.uuid4())[:12]

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to dictionary."""
        return asdict(self)


@dataclass
class ForensicReport:
    """Complete timeline forensics report."""

    report_id: str = ""
    generated_at: str = ""
    event_count: int = 0
    contradiction_count: int = 0
    gap_count: int = 0
    coverage_percentage: float = 0.0
    events_by_lane: Dict[str, int] = field(default_factory=dict)
    events_by_source: Dict[str, int] = field(default_factory=dict)
    contradictions: List[Contradiction] = field(default_factory=list)
    gaps: List[TimelineGap] = field(default_factory=list)
    key_findings: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.report_id:
            self.report_id = str(uuid.uuid4())[:12]
        if not self.generated_at:
            self.generated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to dictionary."""
        d = asdict(self)
        d["contradictions"] = [c.to_dict() for c in self.contradictions]
        d["gaps"] = [g.to_dict() for g in self.gaps]
        return d


# ---------------------------------------------------------------------------
# ContradictionDetector
# ---------------------------------------------------------------------------

class ContradictionDetector:
    """Detect contradictions between timeline events."""

    def __init__(self) -> None:
        self._detected: List[Contradiction] = []

    def detect_temporal_contradictions(
        self, events: List[TimelineEvent]
    ) -> List[Contradiction]:
        """Detect same person in two places at the same time."""
        contradictions: List[Contradiction] = []

        date_groups: Dict[str, List[TimelineEvent]] = defaultdict(list)
        for event in events:
            if event.date:
                date_groups[event.date].append(event)

        for dt, group in date_groups.items():
            if len(group) < 2:
                continue
            for i, e1 in enumerate(group):
                for e2 in group[i + 1:]:
                    shared_actors = set(e1.actors) & set(e2.actors)
                    if shared_actors and e1.description != e2.description:
                        c = Contradiction(
                            event_a_id=e1.event_id,
                            event_b_id=e2.event_id,
                            contradiction_type="temporal",
                            severity=self._score_severity(e1, e2),
                            description=(
                                f"On {dt}, {', '.join(shared_actors)} reportedly: "
                                f"(1) {e1.description[:100]}; "
                                f"(2) {e2.description[:100]}"
                            ),
                            impeachment_use=(
                                "MRE 613 — prior inconsistent statement / "
                                "temporal impossibility"
                            ),
                        )
                        contradictions.append(c)
                        e1.contradicts.append(e2.event_id)
                        e2.contradicts.append(e1.event_id)

        self._detected.extend(contradictions)
        return contradictions

    def detect_factual_contradictions(
        self, events: List[TimelineEvent]
    ) -> List[Contradiction]:
        """Detect conflicting claims about the same event."""
        contradictions: List[Contradiction] = []

        tag_groups: Dict[str, List[TimelineEvent]] = defaultdict(list)
        for event in events:
            for tag in event.tags:
                tag_groups[tag].append(event)

        for tag, group in tag_groups.items():
            if len(group) < 2:
                continue
            for i, e1 in enumerate(group):
                for e2 in group[i + 1:]:
                    if e1.event_id == e2.event_id:
                        continue
                    if self._descriptions_conflict(e1.description, e2.description):
                        c = Contradiction(
                            event_a_id=e1.event_id,
                            event_b_id=e2.event_id,
                            contradiction_type="factual",
                            severity=self._score_severity(e1, e2),
                            description=(
                                f"Conflicting accounts of '{tag}': "
                                f"Source A ({e1.source_type}): {e1.description[:100]}; "
                                f"Source B ({e2.source_type}): {e2.description[:100]}"
                            ),
                            impeachment_use="MRE 613 — conflicting factual accounts",
                        )
                        contradictions.append(c)

        self._detected.extend(contradictions)
        return contradictions

    def detect_record_contradictions(
        self,
        testimony_events: List[TimelineEvent],
        official_records: List[TimelineEvent],
    ) -> List[Contradiction]:
        """Detect witness testimony vs. official record contradictions."""
        contradictions: List[Contradiction] = []

        for testimony in testimony_events:
            for record in official_records:
                if not testimony.overlaps(record):
                    continue
                shared_actors = set(testimony.actors) & set(record.actors)
                if not shared_actors:
                    continue
                if self._descriptions_conflict(testimony.description, record.description):
                    c = Contradiction(
                        event_a_id=testimony.event_id,
                        event_b_id=record.event_id,
                        contradiction_type="record",
                        severity=ContradictionSeverity.SEVERE.value,
                        description=(
                            f"Testimony contradicts official record: "
                            f"Witness said: {testimony.description[:100]}; "
                            f"Record shows: {record.description[:100]}"
                        ),
                        impeachment_use=(
                            "MRE 613 + documentary impeachment — "
                            "official record contradicts testimony"
                        ),
                    )
                    contradictions.append(c)

        self._detected.extend(contradictions)
        return contradictions

    def score_contradiction_severity(
        self, contradiction: Contradiction
    ) -> str:
        """Score the severity of a contradiction."""
        if contradiction.contradiction_type == "record":
            return ContradictionSeverity.SEVERE.value
        if contradiction.contradiction_type == "temporal":
            return ContradictionSeverity.CRITICAL.value
        return ContradictionSeverity.MODERATE.value

    def generate_impeachment_brief(
        self, contradictions: List[Contradiction]
    ) -> str:
        """Generate formatted impeachment brief from contradictions."""
        lines: List[str] = [
            "IMPEACHMENT BRIEF — TIMELINE CONTRADICTIONS",
            "=" * 50,
            f"Contradictions Identified: {len(contradictions)}",
            f"Generated: {datetime.now(timezone.utc).isoformat()}",
            "",
        ]

        severity_order = ["critical", "severe", "moderate", "minor"]
        sorted_contradictions = sorted(
            contradictions,
            key=lambda c: severity_order.index(c.severity)
            if c.severity in severity_order else 99,
        )

        for i, c in enumerate(sorted_contradictions, 1):
            lines.extend([
                f"{'─' * 50}",
                f"Contradiction #{i} — [{c.severity.upper()}]",
                f"  Type: {c.contradiction_type}",
                f"  Description: {c.description}",
                f"  Impeachment Use: {c.impeachment_use}",
                f"  Events: {c.event_a_id} vs {c.event_b_id}",
                "",
            ])

        return "\n".join(lines)

    @staticmethod
    def _score_severity(e1: TimelineEvent, e2: TimelineEvent) -> str:
        """Score severity based on source reliability."""
        high_reliability = {
            SourceType.COURT_ORDER.value, SourceType.RECORD.value,
            SourceType.POLICE_REPORT.value,
        }
        if e1.source_type in high_reliability or e2.source_type in high_reliability:
            return ContradictionSeverity.SEVERE.value
        if e1.confidence > 80 and e2.confidence > 80:
            return ContradictionSeverity.SEVERE.value
        return ContradictionSeverity.MODERATE.value

    @staticmethod
    def _descriptions_conflict(desc_a: str, desc_b: str) -> bool:
        """Heuristic check for conflicting descriptions."""
        a_lower = desc_a.lower()
        b_lower = desc_b.lower()

        negation_pairs = [
            ("did", "did not"), ("was", "was not"), ("is", "is not"),
            ("present", "absent"), ("allowed", "denied"),
            ("complied", "violated"), ("granted", "denied"),
            ("true", "false"), ("confirmed", "denied"),
            ("attended", "did not attend"), ("filed", "did not file"),
        ]

        for pos, neg in negation_pairs:
            if (pos in a_lower and neg in b_lower) or \
               (neg in a_lower and pos in b_lower):
                return True

        return False

    @property
    def total_detected(self) -> int:
        return len(self._detected)


# ---------------------------------------------------------------------------
# GapAnalyzer
# ---------------------------------------------------------------------------

class GapAnalyzer:
    """Identify gaps in the timeline and evidence chain."""

    def __init__(self) -> None:
        self._gaps: List[TimelineGap] = []

    def find_temporal_gaps(
        self,
        events: List[TimelineEvent],
        expected_coverage: Tuple[str, str] = ("2023-09-01", ""),
        max_gap_days: int = 30,
    ) -> List[TimelineGap]:
        """Find periods with no events exceeding max_gap_days."""
        if not expected_coverage[1]:
            expected_coverage = (expected_coverage[0], date.today().isoformat())

        dated_events = sorted(
            [e for e in events if e.date],
            key=lambda e: e.date,
        )

        if not dated_events:
            gap = TimelineGap(
                gap_category=GapCategory.TEMPORAL.value,
                start_date=expected_coverage[0],
                end_date=expected_coverage[1],
                description="No events found in entire expected coverage period",
                severity="critical",
                discovery_recommendation="Conduct comprehensive document review "
                                         "and witness interviews",
            )
            self._gaps.append(gap)
            return [gap]

        gaps: List[TimelineGap] = []

        if dated_events[0].date > expected_coverage[0]:
            gap_days = self._days_between(expected_coverage[0], dated_events[0].date)
            if gap_days > max_gap_days:
                gap = TimelineGap(
                    gap_category=GapCategory.TEMPORAL.value,
                    start_date=expected_coverage[0],
                    end_date=dated_events[0].date,
                    description=f"No events for {gap_days} days at start of timeline",
                    severity="high" if gap_days > 60 else "moderate",
                    discovery_recommendation="Request records from this period",
                )
                gaps.append(gap)

        for i in range(len(dated_events) - 1):
            gap_days = self._days_between(dated_events[i].date, dated_events[i + 1].date)
            if gap_days > max_gap_days:
                gap = TimelineGap(
                    gap_category=GapCategory.TEMPORAL.value,
                    start_date=dated_events[i].date,
                    end_date=dated_events[i + 1].date,
                    description=f"Gap of {gap_days} days between events",
                    severity="high" if gap_days > 90 else "moderate",
                    discovery_recommendation=(
                        f"Request records from {dated_events[i].date} to "
                        f"{dated_events[i + 1].date}"
                    ),
                )
                gaps.append(gap)

        self._gaps.extend(gaps)
        return gaps

    def find_evidence_gaps(
        self,
        events: List[TimelineEvent],
        required_elements: Optional[Dict[str, List[str]]] = None,
    ) -> List[TimelineGap]:
        """Find missing proof for claims based on required evidence elements."""
        if required_elements is None:
            required_elements = {
                "custody_interference": [
                    EventTag.CUSTODY_DENIAL.value,
                    EventTag.POLICE_CONTACT.value,
                    EventTag.COMMUNICATION.value,
                ],
                "ppo_challenge": [
                    EventTag.PPO_EVENT.value,
                    EventTag.COURT_HEARING.value,
                ],
                "housing_discrimination": [
                    EventTag.HOUSING_ISSUE.value,
                    EventTag.COMMUNICATION.value,
                ],
                "judicial_misconduct": [
                    EventTag.JUDICIAL_CONDUCT.value,
                    EventTag.EX_PARTE.value,
                    EventTag.COURT_HEARING.value,
                ],
            }

        all_tags = {tag for e in events for tag in e.tags}
        gaps: List[TimelineGap] = []

        for claim, required_tags in required_elements.items():
            missing = [t for t in required_tags if t not in all_tags]
            if missing:
                gap = TimelineGap(
                    gap_category=GapCategory.EVIDENCE.value,
                    description=(
                        f"Claim '{claim}' missing evidence types: "
                        f"{', '.join(missing)}"
                    ),
                    severity="high" if len(missing) > 1 else "moderate",
                    discovery_recommendation=(
                        f"Obtain evidence for: {', '.join(missing)}"
                    ),
                )
                gaps.append(gap)

        self._gaps.extend(gaps)
        return gaps

    def identify_suppressed_periods(
        self, events: List[TimelineEvent]
    ) -> List[TimelineGap]:
        """Identify suspicious gaps suggesting hidden or suppressed evidence."""
        gaps: List[TimelineGap] = []

        actor_events: Dict[str, List[TimelineEvent]] = defaultdict(list)
        for event in events:
            for actor in event.actors:
                actor_events[actor].append(event)

        for actor, acts in actor_events.items():
            sorted_acts = sorted(acts, key=lambda e: e.date or "")
            dated_acts = [a for a in sorted_acts if a.date]

            for i in range(len(dated_acts) - 1):
                gap_days = self._days_between(dated_acts[i].date, dated_acts[i + 1].date)
                if gap_days > 60:
                    gap = TimelineGap(
                        gap_category=GapCategory.SUPPRESSED.value,
                        start_date=dated_acts[i].date,
                        end_date=dated_acts[i + 1].date,
                        description=(
                            f"{actor}: {gap_days}-day silence between "
                            f"'{dated_acts[i].description[:50]}' and "
                            f"'{dated_acts[i + 1].description[:50]}'"
                        ),
                        severity="high",
                        discovery_recommendation=(
                            f"Subpoena records for {actor} from "
                            f"{dated_acts[i].date} to {dated_acts[i + 1].date}"
                        ),
                    )
                    gaps.append(gap)

        self._gaps.extend(gaps)
        return gaps

    def recommend_discovery(
        self, gaps: List[TimelineGap]
    ) -> List[Dict[str, str]]:
        """Generate discovery recommendations to fill gaps."""
        recommendations: List[Dict[str, str]] = []

        for gap in gaps:
            rec: Dict[str, str] = {
                "gap_id": gap.gap_id,
                "category": gap.gap_category,
                "description": gap.description,
                "recommendation": gap.discovery_recommendation,
                "priority": gap.severity,
            }

            if gap.gap_category == GapCategory.TEMPORAL.value:
                rec["discovery_type"] = "Request for Production (MCR 2.310)"
                rec["scope"] = f"All documents from {gap.start_date} to {gap.end_date}"
            elif gap.gap_category == GapCategory.EVIDENCE.value:
                rec["discovery_type"] = "Interrogatories (MCR 2.309) + Request for Production"
                rec["scope"] = gap.description
            elif gap.gap_category == GapCategory.SUPPRESSED.value:
                rec["discovery_type"] = "Subpoena Duces Tecum (MCR 2.305)"
                rec["scope"] = f"Records for period {gap.start_date} to {gap.end_date}"

            recommendations.append(rec)

        return recommendations

    @staticmethod
    def _days_between(date_a: str, date_b: str) -> int:
        """Calculate days between two ISO date strings."""
        try:
            d1 = datetime.strptime(date_a[:10], "%Y-%m-%d").date()
            d2 = datetime.strptime(date_b[:10], "%Y-%m-%d").date()
            return abs((d2 - d1).days)
        except (ValueError, TypeError):
            return 0

    @property
    def total_gaps(self) -> int:
        return len(self._gaps)


# ---------------------------------------------------------------------------
# TimelineVisualizer
# ---------------------------------------------------------------------------

class TimelineVisualizer:
    """Generate visualisations of timeline data."""

    @staticmethod
    def generate_mermaid_gantt(
        events: List[TimelineEvent],
        title: str = "Pigors v. Watson — Master Timeline",
    ) -> str:
        """Generate a Mermaid Gantt chart in Markdown."""
        dated = sorted(
            [e for e in events if e.date],
            key=lambda e: e.date,
        )
        if not dated:
            return f"```mermaid\ngantt\n    title {title}\n    (No events)\n```"

        lines = [
            "```mermaid",
            "gantt",
            f"    title {title}",
            "    dateFormat YYYY-MM-DD",
            "    axisFormat %Y-%m",
        ]

        lane_events: Dict[str, List[TimelineEvent]] = defaultdict(list)
        for event in dated:
            lane_events[event.lane].append(event)

        for lane in sorted(lane_events.keys()):
            label = LANE_LABELS.get(lane, f"Lane {lane}")
            lines.append(f"    section {label}")
            for event in lane_events[lane][:20]:
                desc = event.description[:40].replace(":", " -")
                end = event.end_date or event.date
                lines.append(f"    {desc} :{event.date}, {end}")

        lines.append("```")
        return "\n".join(lines)

    @staticmethod
    def generate_mermaid_timeline(
        events: List[TimelineEvent],
    ) -> str:
        """Generate a Mermaid timeline diagram."""
        dated = sorted(
            [e for e in events if e.date],
            key=lambda e: e.date,
        )
        if not dated:
            return "```mermaid\ntimeline\n    title No Events\n```"

        lines = [
            "```mermaid",
            "timeline",
            "    title Pigors v. Watson Timeline",
        ]

        month_groups: Dict[str, List[TimelineEvent]] = defaultdict(list)
        for event in dated:
            month_key = event.date[:7]  # YYYY-MM
            month_groups[month_key].append(event)

        for month in sorted(month_groups.keys()):
            lines.append(f"    {month}")
            for event in month_groups[month][:5]:
                desc = event.description[:60].replace(":", " -")
                lines.append(f"        : {desc}")

        lines.append("```")
        return "\n".join(lines)

    @staticmethod
    def generate_parallel_timelines(
        andrew_events: List[TimelineEvent],
        emily_events: List[TimelineEvent],
        official_events: List[TimelineEvent],
    ) -> str:
        """Generate side-by-side comparison Mermaid chart."""
        lines = [
            "```mermaid",
            "gantt",
            "    title Parallel Timelines — Pigors v. Watson",
            "    dateFormat YYYY-MM-DD",
            "    axisFormat %Y-%m",
            f"    section {_PLAINTIFF}",
        ]

        for event in sorted(andrew_events, key=lambda e: e.date or "")[:15]:
            if event.date:
                desc = event.description[:35].replace(":", " -")
                lines.append(f"    {desc} :{event.date}, 1d")

        lines.append(f"    section {_DEFENDANT}")
        for event in sorted(emily_events, key=lambda e: e.date or "")[:15]:
            if event.date:
                desc = event.description[:35].replace(":", " -")
                lines.append(f"    {desc} :{event.date}, 1d")

        lines.append("    section Official Records")
        for event in sorted(official_events, key=lambda e: e.date or "")[:15]:
            if event.date:
                desc = event.description[:35].replace(":", " -")
                lines.append(f"    {desc} :{event.date}, 1d")

        lines.append("```")
        return "\n".join(lines)

    @staticmethod
    def generate_html_timeline(
        events: List[TimelineEvent],
        title: str = "Pigors v. Watson — Interactive Timeline",
    ) -> str:
        """Generate an interactive HTML timeline."""
        dated = sorted(
            [e for e in events if e.date],
            key=lambda e: e.date,
        )

        event_divs: List[str] = []
        for i, event in enumerate(dated):
            color = _LANE_COLORS.get(event.lane, "#6b7280")
            lane_label = html_mod.escape(LANE_LABELS.get(event.lane, ""))
            desc = html_mod.escape(event.description[:200])
            actors_str = html_mod.escape(", ".join(event.actors))
            side = "left" if i % 2 == 0 else "right"
            contradiction_badge = ""
            if event.contradicts:
                contradiction_badge = (
                    '<span style="background:#ef4444;color:white;'
                    'padding:2px 6px;border-radius:4px;font-size:0.7em;">'
                    f'⚠ {len(event.contradicts)} contradiction(s)</span>'
                )

            event_divs.append(f"""\
<div class="tl-item tl-{side}" style="border-left-color:{color}">
  <div class="tl-date">{html_mod.escape(event.date)}</div>
  <div class="tl-lane" style="color:{color}">{lane_label}</div>
  <div class="tl-desc">{desc}</div>
  <div class="tl-meta">
    <span class="tl-source">{html_mod.escape(event.source_type)}</span>
    {f'<span class="tl-actors">{actors_str}</span>' if actors_str else ''}
    {contradiction_badge}
  </div>
</div>""")

        events_html = "\n".join(event_divs)
        escaped_title = html_mod.escape(title)

        return textwrap.dedent(f"""\
        <!DOCTYPE html>
        <html lang="en">
        <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{escaped_title}</title>
        <style>
          body {{ font-family: system-ui, sans-serif; background: #0f172a;
                 color: #e2e8f0; margin: 0; padding: 20px; }}
          h1 {{ text-align: center; color: #38bdf8; }}
          .tl-container {{ max-width: 900px; margin: 0 auto; }}
          .tl-item {{ padding: 12px 16px; margin: 8px 0; background: #1e293b;
                      border-radius: 8px; border-left: 4px solid #6b7280; }}
          .tl-date {{ font-weight: bold; color: #38bdf8; }}
          .tl-lane {{ font-size: 0.8em; margin-top: 2px; }}
          .tl-desc {{ margin-top: 6px; }}
          .tl-meta {{ font-size: 0.75em; color: #94a3b8; margin-top: 6px; }}
          .tl-source {{ background: #334155; padding: 2px 6px; border-radius: 4px; }}
          .tl-actors {{ margin-left: 8px; }}
          .filter-bar {{ text-align: center; margin: 16px 0; }}
          .filter-btn {{ background: #334155; color: #e2e8f0; border: none;
                         padding: 6px 12px; margin: 2px; border-radius: 4px;
                         cursor: pointer; }}
          .filter-btn:hover {{ background: #475569; }}
          .filter-btn.active {{ background: #3b82f6; }}
        </style>
        </head>
        <body>
        <h1>{escaped_title}</h1>
        <div class="filter-bar">
          <button class="filter-btn active" onclick="filterLane('all')">All</button>
          {"".join(
              f'<button class="filter-btn" onclick="filterLane(\'{lane}\')" '
              f'style="border-bottom:2px solid {_LANE_COLORS.get(lane, "#6b7280")}">'
              f'{html_mod.escape(LANE_LABELS.get(lane, lane))}</button>'
              for lane in sorted(LANE_LABELS.keys())
          )}
        </div>
        <div class="tl-container" id="timeline">
        {events_html}
        </div>
        <script>
        function filterLane(lane) {{
          const items = document.querySelectorAll('.tl-item');
          items.forEach(el => {{
            if (lane === 'all') {{ el.style.display = ''; }}
            else {{
              const laneText = el.querySelector('.tl-lane')?.textContent || '';
              el.style.display = laneText.includes(lane) || laneText.includes('Lane ' + lane) ? '' : 'none';
            }}
          }});
          document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
          event.target.classList.add('active');
        }}
        </script>
        </body>
        </html>
        """)

    @staticmethod
    def export_csv(
        events: List[TimelineEvent],
        path: Optional[Path] = None,
    ) -> str:
        """Export events to CSV. Returns CSV text or writes to path."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "event_id", "date", "end_date", "description", "source_type",
            "source_ref", "page_ref", "actors", "lane", "tags",
            "confidence", "contradicts",
        ])

        for event in sorted(events, key=lambda e: e.date or ""):
            writer.writerow([
                event.event_id,
                event.date,
                event.end_date,
                event.description,
                event.source_type,
                event.source_ref,
                event.page_ref,
                "; ".join(event.actors),
                event.lane,
                "; ".join(event.tags),
                event.confidence,
                "; ".join(event.contradicts),
            ])

        csv_text = output.getvalue()

        if path is not None:
            path.write_text(csv_text, encoding="utf-8")
            logger.info("CSV exported to %s (%d events)", path, len(events))

        return csv_text


# ---------------------------------------------------------------------------
# CustodyTimelineTracker
# ---------------------------------------------------------------------------

class CustodyTimelineTracker:
    """Track custody-specific events and compliance."""

    def __init__(self) -> None:
        self._custody_events: List[TimelineEvent] = []

    def track_custody_exchanges(
        self, events: List[TimelineEvent]
    ) -> Dict[str, Any]:
        """Track who had custody when based on events."""
        custody_events = [
            e for e in events
            if any(t in [EventTag.CUSTODY_EXCHANGE.value, EventTag.CUSTODY_DENIAL.value]
                   for t in e.tags)
        ]
        self._custody_events = sorted(custody_events, key=lambda e: e.date or "")

        exchanges = []
        denials = []
        for event in self._custody_events:
            if EventTag.CUSTODY_DENIAL.value in event.tags:
                denials.append(event.to_dict())
            else:
                exchanges.append(event.to_dict())

        return {
            "total_events": len(self._custody_events),
            "successful_exchanges": len(exchanges),
            "denials": len(denials),
            "denial_details": denials[:20],
            "exchange_details": exchanges[:20],
        }

    def calculate_lost_parenting_time(
        self,
        events: List[TimelineEvent],
        court_orders: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Calculate days of lost parenting time due to violations."""
        denial_events = [
            e for e in events
            if EventTag.CUSTODY_DENIAL.value in e.tags
        ]

        if court_orders is None:
            court_orders = [{
                "order_date": "2024-01-01",
                "schedule": "Standard alternate weekends + Wednesday evening",
                "expected_days_per_month": 8,
            }]

        total_denial_days = len(denial_events)
        per_diem_value_low = 328.0
        per_diem_value_high = 656.0

        return {
            "denial_count": total_denial_days,
            "total_days_lost": total_denial_days,
            "per_diem_low": per_diem_value_low,
            "per_diem_high": per_diem_value_high,
            "damages_low": round(total_denial_days * per_diem_value_low, 2),
            "damages_high": round(total_denial_days * per_diem_value_high, 2),
            "applicable_orders": court_orders,
            "statute": "MCL 722.27a",
        }

    def track_order_compliance(
        self,
        events: List[TimelineEvent],
        orders: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Track which orders were violated, when, and by whom."""
        if orders is None:
            orders = [
                {
                    "order_id": "parenting_time_order",
                    "description": "Standard parenting time schedule",
                    "issued_date": "2024-01-15",
                    "keywords": ["custody", "parenting time", "exchange"],
                },
                {
                    "order_id": "no_contact_provisions",
                    "description": "Communication restrictions",
                    "issued_date": "2024-02-01",
                    "keywords": ["contact", "communication"],
                },
            ]

        violations: List[Dict[str, Any]] = []
        for event in events:
            for order in orders:
                keywords = order.get("keywords", [])
                desc_lower = event.description.lower()
                if any(kw in desc_lower for kw in keywords):
                    if any(neg in desc_lower for neg in
                           ["denied", "violated", "refused", "failed"]):
                        violations.append({
                            "event_id": event.event_id,
                            "event_date": event.date,
                            "event_description": event.description[:200],
                            "order_id": order["order_id"],
                            "order_description": order["description"],
                            "violator": event.actors[0] if event.actors else "Unknown",
                        })

        return violations

    def generate_best_interest_timeline(
        self, events: List[TimelineEvent]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Track MCL 722.23 best interest factors over time."""
        factor_events: Dict[str, List[Dict[str, Any]]] = {
            factor: [] for factor in BEST_INTEREST_FACTORS
        }

        factor_keywords: Dict[str, List[str]] = {
            "a": ["love", "affection", "emotional", "bond"],
            "b": ["guidance", "care", "nurture"],
            "c": ["food", "clothing", "medical", "health care"],
            "d": ["stable", "environment", "home"],
            "e": ["permanent", "housing", "residence"],
            "f": ["moral", "fitness", "character"],
            "g": ["mental health", "physical health"],
            "h": ["school", "community", "grades"],
            "i": ["preference", "child wants"],
            "j": ["facilitate", "cooperation", "willingness", "interfere"],
            "k": ["violence", "abuse", "assault", "PPO"],
            "l": ["other factor"],
        }

        for event in events:
            desc_lower = event.description.lower()
            for factor, keywords in factor_keywords.items():
                if any(kw in desc_lower for kw in keywords):
                    factor_events[factor].append({
                        "event_id": event.event_id,
                        "date": event.date,
                        "description": event.description[:200],
                        "source": event.source_type,
                        "factor_description": BEST_INTEREST_FACTORS[factor],
                    })

        return factor_events


# ---------------------------------------------------------------------------
# TimelineForensics (Main Orchestrator)
# ---------------------------------------------------------------------------

class TimelineForensics:
    """
    Main orchestrator for timeline forensics.

    Integrates TimelineEvent management, ContradictionDetector,
    GapAnalyzer, TimelineVisualizer, and CustodyTimelineTracker.
    """

    VERSION = "1.0.0"

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or _DB_PATH
        self._events: List[TimelineEvent] = []
        self._sources: List[EventSource] = []
        self._contradiction_detector = ContradictionDetector()
        self._gap_analyzer = GapAnalyzer()
        self._visualizer = TimelineVisualizer()
        self._custody_tracker = CustodyTimelineTracker()
        self._contradictions: List[Contradiction] = []
        self._gaps: List[TimelineGap] = []
        self._initialized = False

    def _ensure_db(self) -> None:
        """Initialise database tables on first use."""
        if self._initialized:
            return
        if not self._db_path.exists():
            logger.warning("DB not found at %s — running in memory-only mode", self._db_path)
            self._initialized = True
            return
        try:
            conn = _connect(self._db_path)
            _ensure_tables(conn)
            conn.close()
            self._initialized = True
        except sqlite3.Error as exc:
            logger.error("DB init failed: %s", exc)
            self._initialized = True

    # -- Event Management --------------------------------------------------

    def add_event(self, event: TimelineEvent) -> str:
        """Add a single event to the master timeline."""
        self._events.append(event)
        return event.event_id

    def add_events(self, events: List[TimelineEvent]) -> int:
        """Add multiple events. Returns count added."""
        self._events.extend(events)
        return len(events)

    def build_master_timeline(
        self,
        sources: Optional[List[EventSource]] = None,
    ) -> Dict[str, Any]:
        """
        Compile all events from all sources into the master timeline.

        If no sources are provided, loads from the database and
        generates seed events from known case milestones.
        """
        self._ensure_db()

        if self._db_path.exists():
            self._load_from_db()

        if not self._events:
            self._seed_known_events()

        if sources:
            self._sources = sources

        self._events.sort(key=lambda e: e.date or "9999-12-31")

        return {
            "total_events": len(self._events),
            "sources": len(self._sources),
            "date_range": self._get_date_range(),
            "lanes_covered": list({e.lane for e in self._events}),
            "actors_found": list({a for e in self._events for a in e.actors})[:20],
        }

    def _load_from_db(self) -> None:
        """Load timeline events from the database."""
        try:
            conn = _connect(self._db_path)
            if not _table_exists(conn, "timeline_events"):
                conn.close()
                return

            rows = conn.execute(
                "SELECT * FROM timeline_events ORDER BY event_date"
            ).fetchall()

            for row in rows:
                actors = []
                tags = []
                contradicts = []
                try:
                    actors = json.loads(row["actors_json"] or "[]")
                except (json.JSONDecodeError, KeyError):
                    pass
                try:
                    tags = json.loads(row["tags_json"] or "[]")
                except (json.JSONDecodeError, KeyError):
                    pass
                try:
                    contradicts = json.loads(row["contradicts_json"] or "[]")
                except (json.JSONDecodeError, KeyError):
                    pass

                event = TimelineEvent(
                    event_id=row["id"],
                    date=row["event_date"],
                    end_date=row.get("end_date", "") or "",
                    description=row["description"],
                    source_type=row.get("source_type", SourceType.RECORD.value),
                    source_ref=row.get("source_ref", "") or "",
                    page_ref=row.get("page_ref", "") or "",
                    actors=actors,
                    lane=row.get("lane", "A") or "A",
                    tags=tags,
                    confidence=float(row.get("confidence", 75.0) or 75.0),
                    contradicts=contradicts,
                )
                self._events.append(event)

            conn.close()
            logger.info("Loaded %d events from DB", len(self._events))
        except sqlite3.Error as exc:
            logger.error("Error loading timeline from DB: %s", exc)

    def _seed_known_events(self) -> None:
        """Generate seed events from known case milestones."""
        seed_events = [
            TimelineEvent(
                date="2023-09-01",
                description="PPO petition filed (2023-5907-PP)",
                source_type=SourceType.FILING.value,
                actors=[_DEFENDANT],
                lane="D",
                tags=[EventTag.PPO_EVENT.value, EventTag.FILING.value],
                confidence=95.0,
            ),
            TimelineEvent(
                date="2024-01-15",
                description="Custody action filed (2024-001507-DC)",
                source_type=SourceType.FILING.value,
                actors=[_PLAINTIFF],
                lane="A",
                tags=[EventTag.FILING.value],
                confidence=95.0,
            ),
            TimelineEvent(
                date="2024-03-15",
                description=f"Case assigned to {_JUDGE}",
                source_type=SourceType.RECORD.value,
                actors=[_JUDGE],
                lane="A",
                tags=[EventTag.ORDER_ENTERED.value],
                confidence=90.0,
            ),
            TimelineEvent(
                date="2025-01-10",
                description="Housing complaint filed against Shady Oaks (2025-002760-CZ)",
                source_type=SourceType.FILING.value,
                actors=[_PLAINTIFF],
                lane="B",
                tags=[EventTag.FILING.value, EventTag.HOUSING_ISSUE.value],
                confidence=95.0,
            ),
            TimelineEvent(
                date="2025-02-01",
                description="COA application filed (366810)",
                source_type=SourceType.FILING.value,
                actors=[_PLAINTIFF],
                lane="F",
                tags=[EventTag.FILING.value],
                confidence=90.0,
            ),
            TimelineEvent(
                date="2025-06-15",
                description="JTC complaint filed regarding Judge McNeill conduct",
                source_type=SourceType.FILING.value,
                actors=[_PLAINTIFF],
                lane="E",
                tags=[EventTag.JUDICIAL_CONDUCT.value, EventTag.FILING.value],
                confidence=85.0,
            ),
        ]

        for event in seed_events:
            existing = {e.date + e.description[:30] for e in self._events}
            key = event.date + event.description[:30]
            if key not in existing:
                self._events.append(event)

    # -- Analysis ----------------------------------------------------------

    def analyze_contradictions(self) -> List[Contradiction]:
        """Run full contradiction detection suite."""
        if not self._events:
            self.build_master_timeline()

        self._contradictions = []

        temporal = self._contradiction_detector.detect_temporal_contradictions(
            self._events
        )
        self._contradictions.extend(temporal)

        factual = self._contradiction_detector.detect_factual_contradictions(
            self._events
        )
        self._contradictions.extend(factual)

        testimony_events = [
            e for e in self._events
            if e.source_type in (
                SourceType.TRANSCRIPT.value,
                SourceType.AFFIDAVIT.value,
            )
        ]
        official_events = [
            e for e in self._events
            if e.source_type in (
                SourceType.RECORD.value,
                SourceType.COURT_ORDER.value,
                SourceType.POLICE_REPORT.value,
            )
        ]
        if testimony_events and official_events:
            record_contradictions = (
                self._contradiction_detector.detect_record_contradictions(
                    testimony_events, official_events,
                )
            )
            self._contradictions.extend(record_contradictions)

        self._save_contradictions()
        return self._contradictions

    def analyze_gaps(self) -> List[TimelineGap]:
        """Run full gap analysis suite."""
        if not self._events:
            self.build_master_timeline()

        self._gaps = []

        temporal_gaps = self._gap_analyzer.find_temporal_gaps(self._events)
        self._gaps.extend(temporal_gaps)

        evidence_gaps = self._gap_analyzer.find_evidence_gaps(self._events)
        self._gaps.extend(evidence_gaps)

        suppressed = self._gap_analyzer.identify_suppressed_periods(self._events)
        self._gaps.extend(suppressed)

        self._save_gaps()
        return self._gaps

    # -- Reporting ---------------------------------------------------------

    def generate_forensic_report(self) -> ForensicReport:
        """Generate comprehensive timeline forensics report."""
        if not self._events:
            self.build_master_timeline()
        if not self._contradictions:
            self.analyze_contradictions()
        if not self._gaps:
            self.analyze_gaps()

        events_by_lane: Dict[str, int] = Counter(e.lane for e in self._events)
        events_by_source: Dict[str, int] = Counter(
            e.source_type for e in self._events
        )

        date_range = self._get_date_range()
        total_days = 0
        if date_range[0] and date_range[1]:
            try:
                d1 = datetime.strptime(date_range[0], "%Y-%m-%d").date()
                d2 = datetime.strptime(date_range[1], "%Y-%m-%d").date()
                total_days = (d2 - d1).days
            except ValueError:
                pass

        event_days = len({e.date for e in self._events if e.date})
        coverage = (event_days / max(total_days, 1)) * 100.0

        key_findings: List[str] = []
        if self._contradictions:
            critical = sum(
                1 for c in self._contradictions
                if c.severity in (
                    ContradictionSeverity.CRITICAL.value,
                    ContradictionSeverity.SEVERE.value,
                )
            )
            key_findings.append(
                f"{len(self._contradictions)} contradictions detected "
                f"({critical} critical/severe)"
            )
        if self._gaps:
            key_findings.append(
                f"{len(self._gaps)} evidence/timeline gaps identified"
            )
        if coverage < 50:
            key_findings.append(
                f"Low timeline coverage ({coverage:.1f}%) — "
                f"significant discovery needed"
            )

        report = ForensicReport(
            event_count=len(self._events),
            contradiction_count=len(self._contradictions),
            gap_count=len(self._gaps),
            coverage_percentage=round(coverage, 1),
            events_by_lane=dict(events_by_lane),
            events_by_source=dict(events_by_source),
            contradictions=self._contradictions,
            gaps=self._gaps,
            key_findings=key_findings,
        )

        return report

    def generate_text_report(self) -> str:
        """Generate human-readable forensic report."""
        report = self.generate_forensic_report()

        lines = [
            "TIMELINE FORENSICS REPORT",
            "=" * 50,
            f"Generated: {report.generated_at}",
            f"Events: {report.event_count}",
            f"Contradictions: {report.contradiction_count}",
            f"Gaps: {report.gap_count}",
            f"Coverage: {report.coverage_percentage:.1f}%",
            "",
            "EVENTS BY LANE:",
        ]
        for lane, count in sorted(report.events_by_lane.items()):
            lines.append(
                f"  Lane {lane} ({LANE_LABELS.get(lane, '')}): {count}"
            )

        lines.append("")
        lines.append("EVENTS BY SOURCE:")
        for source, count in sorted(
            report.events_by_source.items(), key=lambda x: -x[1]
        ):
            lines.append(f"  {source}: {count}")

        if report.key_findings:
            lines.append("")
            lines.append("KEY FINDINGS:")
            for finding in report.key_findings:
                lines.append(f"  ⚠ {finding}")

        if report.contradictions:
            lines.append("")
            lines.append("CONTRADICTIONS:")
            for c in report.contradictions[:10]:
                lines.append(
                    f"  [{c.severity.upper()}] {c.description[:120]}"
                )

        if report.gaps:
            lines.append("")
            lines.append("GAPS:")
            for g in report.gaps[:10]:
                lines.append(
                    f"  [{g.severity.upper()}] {g.description[:120]}"
                )

        return "\n".join(lines)

    # -- Visualisation Passthrough -----------------------------------------

    def generate_mermaid(self) -> str:
        """Generate Mermaid Gantt chart of the master timeline."""
        return self._visualizer.generate_mermaid_gantt(self._events)

    def generate_html(self) -> str:
        """Generate interactive HTML timeline."""
        return self._visualizer.generate_html_timeline(self._events)

    def export_csv(self, path: Optional[Path] = None) -> str:
        """Export timeline to CSV."""
        return self._visualizer.export_csv(self._events, path)

    # -- Custody-Specific --------------------------------------------------

    def track_custody(self) -> Dict[str, Any]:
        """Run custody-specific timeline analysis."""
        custody_events = [
            e for e in self._events if e.lane == "A"
        ]
        exchanges = self._custody_tracker.track_custody_exchanges(custody_events)
        lost_time = self._custody_tracker.calculate_lost_parenting_time(custody_events)
        violations = self._custody_tracker.track_order_compliance(custody_events)
        best_interest = self._custody_tracker.generate_best_interest_timeline(
            custody_events
        )

        return {
            "exchanges": exchanges,
            "lost_parenting_time": lost_time,
            "order_violations": violations,
            "best_interest_factors": {
                k: len(v) for k, v in best_interest.items()
            },
        }

    # -- Persistence -------------------------------------------------------

    def save_to_db(self) -> int:
        """Persist all events to the database. Returns count saved."""
        if not self._db_path.exists():
            return 0
        try:
            conn = _connect(self._db_path)
            _ensure_tables(conn)
            now = datetime.now(timezone.utc).isoformat()
            rows = []
            for event in self._events:
                rows.append((
                    event.event_id,
                    event.date,
                    event.end_date or None,
                    event.description,
                    event.source_type,
                    event.source_ref,
                    event.page_ref,
                    json.dumps(event.actors),
                    event.lane,
                    json.dumps(event.tags),
                    event.confidence,
                    json.dumps(event.contradicts),
                    now, now,
                ))
            conn.executemany(
                "INSERT OR REPLACE INTO timeline_events "
                "(id, event_date, end_date, description, source_type, "
                "source_ref, page_ref, actors_json, lane, tags_json, "
                "confidence, contradicts_json, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                rows,
            )
            conn.commit()
            conn.close()
            return len(rows)
        except sqlite3.Error as exc:
            logger.error("Error saving timeline events: %s", exc)
            return 0

    def _save_contradictions(self) -> None:
        """Persist contradictions to the database."""
        if not self._db_path.exists():
            return
        try:
            conn = _connect(self._db_path)
            _ensure_tables(conn)
            now = datetime.now(timezone.utc).isoformat()
            rows = []
            for c in self._contradictions:
                rows.append((
                    c.contradiction_id,
                    c.event_a_id,
                    c.event_b_id,
                    c.contradiction_type,
                    c.severity,
                    c.description,
                    c.impeachment_use,
                    now,
                ))
            conn.executemany(
                "INSERT OR REPLACE INTO timeline_contradictions "
                "(id, event_a_id, event_b_id, contradiction_type, "
                "severity, description, impeachment_use, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                rows,
            )
            conn.commit()
            conn.close()
        except sqlite3.Error as exc:
            logger.error("Error saving contradictions: %s", exc)

    def _save_gaps(self) -> None:
        """Persist gaps to the database."""
        if not self._db_path.exists():
            return
        try:
            conn = _connect(self._db_path)
            _ensure_tables(conn)
            now = datetime.now(timezone.utc).isoformat()
            rows = []
            for g in self._gaps:
                rows.append((
                    g.gap_id,
                    g.gap_category,
                    g.start_date or None,
                    g.end_date or None,
                    g.description,
                    g.lane or None,
                    g.severity,
                    g.discovery_recommendation,
                    now,
                ))
            conn.executemany(
                "INSERT OR REPLACE INTO timeline_gaps "
                "(id, gap_category, start_date, end_date, description, "
                "lane, severity, discovery_recommendation, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                rows,
            )
            conn.commit()
            conn.close()
        except sqlite3.Error as exc:
            logger.error("Error saving gaps: %s", exc)

    # -- Utility -----------------------------------------------------------

    def _get_date_range(self) -> Tuple[str, str]:
        """Get earliest and latest dates from events."""
        dates = [e.date for e in self._events if e.date]
        if not dates:
            return ("", "")
        return (min(dates), max(dates))

    # -- Statistics --------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Return engine statistics."""
        date_range = self._get_date_range()
        event_days = len({e.date for e in self._events if e.date})

        total_days = 0
        if date_range[0] and date_range[1]:
            try:
                d1 = datetime.strptime(date_range[0], "%Y-%m-%d").date()
                d2 = datetime.strptime(date_range[1], "%Y-%m-%d").date()
                total_days = (d2 - d1).days
            except ValueError:
                pass

        coverage = (event_days / max(total_days, 1)) * 100.0 if total_days else 0.0

        return {
            "engine": "TimelineForensics",
            "version": self.VERSION,
            "db_path": str(self._db_path),
            "db_exists": self._db_path.exists(),
            "event_count": len(self._events),
            "source_count": len(self._sources),
            "contradiction_count": len(self._contradictions),
            "gap_count": len(self._gaps),
            "coverage_percentage": round(coverage, 1),
            "date_range": date_range,
            "events_by_lane": dict(Counter(e.lane for e in self._events)),
            "events_by_source": dict(Counter(e.source_type for e in self._events)),
            "actors_tracked": len({a for e in self._events for a in e.actors}),
            "case_context": {
                "plaintiff": _PLAINTIFF,
                "defendant": _DEFENDANT,
                "child": _CHILD_INITIALS,
                "judge": _JUDGE,
            },
        }


# ---------------------------------------------------------------------------
# __main__ demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")

    logging.basicConfig(level=logging.INFO, format="%(name)s %(levelname)s: %(message)s")

    print("=" * 60)
    print("TimelineForensics — Demo")
    print("=" * 60)

    engine = TimelineForensics()

    # Build master timeline (seeds known events)
    result = engine.build_master_timeline()
    print(f"\nTimeline built: {result['total_events']} events")
    print(f"Date range: {result['date_range']}")
    print(f"Lanes: {result['lanes_covered']}")

    # Add some demo events for analysis
    demo_events = [
        TimelineEvent(
            date="2024-04-15",
            description=f"{_DEFENDANT} denied parenting time exchange",
            source_type=SourceType.COMMUNICATION.value,
            actors=[_DEFENDANT, _PLAINTIFF],
            lane="A",
            tags=[EventTag.CUSTODY_DENIAL.value],
            confidence=85.0,
        ),
        TimelineEvent(
            date="2024-04-15",
            description=f"{_DEFENDANT} claimed child was sick and could not travel",
            source_type=SourceType.AFFIDAVIT.value,
            actors=[_DEFENDANT],
            lane="A",
            tags=[EventTag.CUSTODY_DENIAL.value],
            confidence=70.0,
        ),
        TimelineEvent(
            date="2024-04-15",
            description="School attendance record shows child present in class",
            source_type=SourceType.RECORD.value,
            actors=[_CHILD_INITIALS],
            lane="A",
            tags=[EventTag.SCHOOL_EVENT.value],
            confidence=95.0,
        ),
        TimelineEvent(
            date="2024-05-20",
            description="Habitability complaint filed for mold in unit",
            source_type=SourceType.FILING.value,
            actors=[_PLAINTIFF],
            lane="B",
            tags=[EventTag.HOUSING_ISSUE.value],
            confidence=90.0,
        ),
        TimelineEvent(
            date="2024-06-10",
            description=f"Ex parte communication between {_DEFENDANT} and court staff",
            source_type=SourceType.COMMUNICATION.value,
            actors=[_DEFENDANT, _JUDGE],
            lane="E",
            tags=[EventTag.EX_PARTE.value, EventTag.JUDICIAL_CONDUCT.value],
            confidence=60.0,
        ),
    ]
    engine.add_events(demo_events)

    # Analyse contradictions
    contradictions = engine.analyze_contradictions()
    print(f"\nContradictions found: {len(contradictions)}")
    for c in contradictions[:5]:
        print(f"  [{c.severity}] {c.description[:100]}")

    # Analyse gaps
    gaps = engine.analyze_gaps()
    print(f"\nGaps found: {len(gaps)}")
    for g in gaps[:5]:
        print(f"  [{g.severity}] {g.description[:100]}")

    # Custody tracking
    custody = engine.track_custody()
    print(f"\nCustody Analysis:")
    print(f"  Denials: {custody['exchanges']['denials']}")
    print(f"  Lost time damages: ${custody['lost_parenting_time']['damages_low']:,.0f}"
          f" – ${custody['lost_parenting_time']['damages_high']:,.0f}")

    # Generate Mermaid
    mermaid = engine.generate_mermaid()
    print(f"\nMermaid chart: {len(mermaid)} chars")

    # CSV export
    csv_text = engine.export_csv()
    print(f"CSV export: {len(csv_text)} chars, "
          f"{csv_text.count(chr(10))} rows")

    # Report
    report = engine.generate_forensic_report()
    print(f"\nForensic Report:")
    print(f"  Events: {report.event_count}")
    print(f"  Contradictions: {report.contradiction_count}")
    print(f"  Gaps: {report.gap_count}")
    print(f"  Coverage: {report.coverage_percentage}%")
    if report.key_findings:
        print("  Key Findings:")
        for f in report.key_findings:
            print(f"    ⚠ {f}")

    # Stats
    print(f"\n{'─' * 40}")
    stats = engine.get_stats()
    for key, val in stats.items():
        if key != "case_context":
            print(f"  {key}: {val}")

    print(f"\n{engine.generate_text_report()}")
    print("\nDone.")
