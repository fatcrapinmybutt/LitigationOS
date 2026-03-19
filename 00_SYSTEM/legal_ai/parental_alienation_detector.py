# -*- coding: utf-8 -*-
"""
Parental Alienation Detector — LitigationOS Legal AI Subsystem
================================================================
Detects, catalogs, and documents parental alienation patterns using
the Gardner 8-manifestation framework.  Links each behaviour to
supporting evidence, scores severity, and produces court-ready reports
tied to Michigan's best-interest factors — particularly MCL 722.23(j)
(willingness to facilitate a close and continuing parent-child
relationship).

Case Context
------------
    Plaintiff:  Andrew James Pigors (Pro Se)
    Defendant:  Emily A. Watson
    Child:      L.D.W. (per MCR 8.119(H)) — Male
    Judge:      Hon. Jenny L. McNeill — 14th Circuit Court
    Case No.:   2024-001507-DC
    Lane:       A (Custody)

Usage::

    from legal_ai.parental_alienation_detector import ParentalAlienationDetector

    pad = ParentalAlienationDetector()
    report = pad.generate_report()

Zero external dependencies.  CPU-first.  Local-only.
"""
from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import sys
import textwrap
import uuid
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from enum import Enum, IntEnum
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

logger = logging.getLogger("legal_ai.parental_alienation_detector")

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
_CHILD_NAME = "Lincoln David Watson"
_JUDGE = "Hon. Jenny L. McNeill"
_COURT = "14th Circuit Court"
_CASE_NUMBER = "2024-001507-DC"
_LANE = "A"

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class AlienationIndicator(IntEnum):
    """Gardner's eight manifestations of Parental Alienation Syndrome."""

    CAMPAIGN_OF_DENIGRATION = 1
    WEAK_RATIONALIZATIONS = 2
    LACK_OF_AMBIVALENCE = 3
    INDEPENDENT_THINKER_PHENOMENON = 4
    REFLEXIVE_SUPPORT = 5
    ABSENCE_OF_GUILT = 6
    BORROWED_SCENARIOS = 7
    SPREAD_TO_EXTENDED_FAMILY = 8

    @property
    def label(self) -> str:
        _labels: Dict[int, str] = {
            1: "Campaign of denigration",
            2: "Weak or frivolous rationalizations",
            3: "Lack of ambivalence",
            4: "Independent-thinker phenomenon",
            5: "Reflexive support of alienating parent",
            6: "Absence of guilt",
            7: "Borrowed scenarios",
            8: "Spread to extended family",
        }
        return _labels.get(self.value, "Unknown")

    @property
    def description(self) -> str:
        _descriptions: Dict[int, str] = {
            1: "Child participates in campaign of denigrating the targeted parent",
            2: "Child gives absurd, weak, or frivolous reasons for hostility",
            3: "Child expresses only negative feelings; no positive memories",
            4: "Child claims alienation is entirely their own independent idea",
            5: "Child automatically sides with alienating parent in all disputes",
            6: "Child shows no guilt for exploitation or cruelty toward targeted parent",
            7: "Child uses phrases or describes events clearly coached by alienating parent",
            8: "Hostility extends to targeted parent's family and social circle",
        }
        return _descriptions.get(self.value, "")


class Severity(str, Enum):
    """Severity levels for alienation events."""

    NONE = "none"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"

    @property
    def score(self) -> int:
        return {"none": 0, "mild": 1, "moderate": 2, "severe": 3}[self.value]


class FactorJImpact(str, Enum):
    """Impact classifications for MCL 722.23(j) scoring."""

    STRONGLY_FAVORS = "strongly_favors"
    FAVORS = "favors"
    NEUTRAL = "neutral"
    AGAINST = "against"
    STRONGLY_AGAINST = "strongly_against"


class EscalationTrend(str, Enum):
    """Trend classification for temporal analysis."""

    ESCALATING = "escalating"
    STABLE = "stable"
    DE_ESCALATING = "de_escalating"
    INSUFFICIENT_DATA = "insufficient_data"


class ReportFormat(str, Enum):
    """Output formats for generated reports."""

    MARKDOWN = "markdown"
    JSON = "json"
    TEXT = "text"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class AlienationEvent:
    """A single alienation event linked to evidence."""

    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    event_date: str = ""
    indicator: AlienationIndicator = AlienationIndicator.CAMPAIGN_OF_DENIGRATION
    severity: Severity = Severity.NONE
    description: str = ""
    evidence_refs: List[str] = field(default_factory=list)
    accused_party: str = _DEFENDANT
    child_initials: str = _CHILD_INITIALS
    witnesses: List[str] = field(default_factory=list)
    source_document: str = ""
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["indicator"] = self.indicator.value
        d["severity"] = self.severity.value
        return d


@dataclass
class AlienationPattern:
    """Aggregation of events for a single Gardner manifestation."""

    indicator: AlienationIndicator = AlienationIndicator.CAMPAIGN_OF_DENIGRATION
    events: List[AlienationEvent] = field(default_factory=list)
    frequency_per_month: float = 0.0
    peak_severity: Severity = Severity.NONE
    first_occurrence: str = ""
    last_occurrence: str = ""
    trend: EscalationTrend = EscalationTrend.INSUFFICIENT_DATA

    @property
    def score(self) -> int:
        if not self.events:
            return 0
        return self.peak_severity.score

    @property
    def event_count(self) -> int:
        return len(self.events)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "indicator": self.indicator.value,
            "indicator_label": self.indicator.label,
            "event_count": self.event_count,
            "score": self.score,
            "frequency_per_month": round(self.frequency_per_month, 2),
            "peak_severity": self.peak_severity.value,
            "first_occurrence": self.first_occurrence,
            "last_occurrence": self.last_occurrence,
            "trend": self.trend.value,
            "events": [e.to_dict() for e in self.events],
        }


@dataclass
class FactorJAssessment:
    """MCL 722.23(j) best-interest factor assessment per party."""

    party_name: str = ""
    impact: FactorJImpact = FactorJImpact.NEUTRAL
    facilitation_examples: List[str] = field(default_factory=list)
    obstruction_examples: List[str] = field(default_factory=list)
    score_adjustment: int = 0
    narrative: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["impact"] = self.impact.value
        return d


@dataclass
class TemporalAnalysis:
    """Temporal pattern analysis for alienation events."""

    total_events: int = 0
    date_range_start: str = ""
    date_range_end: str = ""
    months_covered: int = 0
    monthly_counts: Dict[str, int] = field(default_factory=dict)
    overall_trend: EscalationTrend = EscalationTrend.INSUFFICIENT_DATA
    peak_month: str = ""
    peak_count: int = 0
    average_per_month: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["overall_trend"] = self.overall_trend.value
        return d


@dataclass
class AlienationReport:
    """Complete court-ready alienation analysis report."""

    report_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    case_number: str = _CASE_NUMBER
    lane: str = _LANE
    total_score: int = 0
    max_possible: int = 24
    severity_level: str = ""
    patterns: List[AlienationPattern] = field(default_factory=list)
    factor_j_plaintiff: Optional[FactorJAssessment] = None
    factor_j_defendant: Optional[FactorJAssessment] = None
    temporal: Optional[TemporalAnalysis] = None
    recommended_actions: List[str] = field(default_factory=list)
    evidence_index: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at,
            "case_number": self.case_number,
            "lane": self.lane,
            "total_score": self.total_score,
            "max_possible": self.max_possible,
            "severity_level": self.severity_level,
            "patterns": [p.to_dict() for p in self.patterns],
            "factor_j_plaintiff": (
                self.factor_j_plaintiff.to_dict()
                if self.factor_j_plaintiff
                else None
            ),
            "factor_j_defendant": (
                self.factor_j_defendant.to_dict()
                if self.factor_j_defendant
                else None
            ),
            "temporal": self.temporal.to_dict() if self.temporal else None,
            "recommended_actions": self.recommended_actions,
            "evidence_index": self.evidence_index,
        }


# ---------------------------------------------------------------------------
# Severity thresholds
# ---------------------------------------------------------------------------
_SEVERITY_THRESHOLDS: Dict[str, Tuple[int, int]] = {
    "no_significant_alienation": (0, 4),
    "mild_alienation": (5, 10),
    "moderate_alienation": (11, 16),
    "severe_alienation": (17, 24),
}


def _classify_severity(total_score: int) -> str:
    """Return human-readable severity classification."""
    for label, (lo, hi) in _SEVERITY_THRESHOLDS.items():
        if lo <= total_score <= hi:
            return label.replace("_", " ").title()
    return "Unknown"


def _recommended_actions(severity: str) -> List[str]:
    """Return recommended actions based on severity."""
    actions: Dict[str, List[str]] = {
        "No Significant Alienation": [
            "Continue monitoring and documenting interactions",
            "Maintain a log of all parenting-time exchanges",
        ],
        "Mild Alienation": [
            "Recommend co-parenting therapy (MCL 722.27a)",
            "Document all instances for future reference",
            "Request FOC investigation noting alienation concerns",
        ],
        "Moderate Alienation": [
            "File motion citing MCL 722.23(j) impact on best-interest factors",
            "Request court-ordered reunification therapy (Brown v Loveman)",
            "Move for custody evaluation by independent professional",
            "Preserve all evidence with chain of custody documentation",
        ],
        "Severe Alienation": [
            "File emergency motion for change of custody (Berger v Berger)",
            "Request immediate therapeutic intervention for L.D.W.",
            "File motion for contempt if alienation violates existing orders",
            "Consider JTC complaint if court fails to act (Lane E coordination)",
            "Preserve evidence and prepare for appellate review (Lane F)",
        ],
    }
    return actions.get(severity, ["Consult legal research for guidance"])


# ---------------------------------------------------------------------------
# BehaviorCataloger
# ---------------------------------------------------------------------------


class BehaviorCataloger:
    """Scans evidence and catalogs alienation behaviours.

    Provides keyword-based detection against evidence content previews
    stored in *litigation_context.db*.  No network access.
    """

    _INDICATOR_KEYWORDS: Dict[int, List[str]] = {
        1: ["denigrat", "bad-mouth", "trash talk", "horrible parent", "hates you",
            "doesn't love", "doesn't care about you", "terrible father",
            "terrible mother", "worthless parent"],
        2: ["stupid reason", "because I just don't", "no reason", "I don't know why",
            "can't explain", "just because", "doesn't matter why"],
        3: ["nothing good", "never liked", "all bad", "always hated",
            "can't think of anything", "no good memories", "never fun"],
        4: ["my own decision", "nobody told me", "I decided myself",
            "my own idea", "nobody influenced", "thought of it myself"],
        5: ["mom is always right", "dad is always right", "always agree with",
            "always on their side", "never wrong"],
        6: ["don't care", "so what", "doesn't bother me", "deserve it",
            "not my problem", "who cares", "good riddance"],
        7: ["mom said you", "dad said you", "told me that you", "heard that you",
            "said you were", "they told me", "I was told"],
        8: ["hate grandpa", "hate grandma", "don't want to see uncle",
            "entire family", "all of them", "your whole family",
            "don't like your friends"],
    }

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or _DB_PATH

    def scan_text(self, text: str) -> List[Tuple[AlienationIndicator, str]]:
        """Scan *text* for alienation-indicator keywords.

        Returns a list of ``(indicator, matched_keyword)`` tuples.
        """
        hits: List[Tuple[AlienationIndicator, str]] = []
        lower = text.lower()
        for ind_val, keywords in self._INDICATOR_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in lower:
                    hits.append((AlienationIndicator(ind_val), kw))
        return hits

    def scan_evidence(
        self,
        lane: str = _LANE,
        limit: int = 500,
    ) -> List[AlienationEvent]:
        """Scan evidence in the database for alienation indicators."""
        events: List[AlienationEvent] = []
        if not self._db_path.exists():
            logger.warning("Database not found at %s", self._db_path)
            return events

        try:
            conn = sqlite3.connect(str(self._db_path), timeout=60)
            conn.execute("PRAGMA busy_timeout=60000")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA cache_size=-32000")
            conn.row_factory = sqlite3.Row
        except sqlite3.Error as exc:
            logger.error("Failed to open database: %s", exc)
            return events

        try:
            tables = {
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            if "documents" not in tables:
                logger.info("documents table not found — skipping evidence scan")
                return events

            cols = [
                r[1]
                for r in conn.execute("PRAGMA table_info(documents)").fetchall()
            ]
            has_preview = "content_preview" in cols
            has_lane = "lane" in cols

            query_parts = ["SELECT * FROM documents"]
            params: List[Any] = []
            if has_lane:
                query_parts.append("WHERE lane = ?")
                params.append(lane)
            query_parts.append(f"LIMIT {int(limit)}")
            query = " ".join(query_parts)

            rows = conn.execute(query, params).fetchall()
            for row in rows:
                text = ""
                if has_preview:
                    text = row["content_preview"] or ""
                hits = self.scan_text(text)
                for indicator, kw in hits:
                    ev = AlienationEvent(
                        event_date=str(row.get("created_at", "") or ""),
                        indicator=indicator,
                        severity=Severity.MILD,
                        description=f"Keyword '{kw}' found in document",
                        evidence_refs=[str(row.get("doc_id", "") or row.get("id", ""))],
                        source_document=str(row.get("title", "") or ""),
                    )
                    events.append(ev)
        except sqlite3.Error as exc:
            logger.error("Evidence scan query failed: %s", exc)
        finally:
            conn.close()

        return events

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "BehaviorCataloger",
            "keyword_categories": len(self._INDICATOR_KEYWORDS),
            "total_keywords": sum(
                len(v) for v in self._INDICATOR_KEYWORDS.values()
            ),
        }


# ---------------------------------------------------------------------------
# PatternAnalyzer
# ---------------------------------------------------------------------------


class PatternAnalyzer:
    """Analyses alienation events for temporal patterns and Gardner scoring."""

    def build_patterns(
        self, events: Sequence[AlienationEvent]
    ) -> List[AlienationPattern]:
        """Group events by indicator and compute per-indicator patterns."""
        grouped: Dict[int, List[AlienationEvent]] = defaultdict(list)
        for ev in events:
            grouped[ev.indicator.value].append(ev)

        patterns: List[AlienationPattern] = []
        for ind in AlienationIndicator:
            evts = grouped.get(ind.value, [])
            pat = AlienationPattern(indicator=ind, events=list(evts))
            if evts:
                severities = [e.severity for e in evts]
                pat.peak_severity = max(severities, key=lambda s: s.score)
                dates = sorted(e.event_date for e in evts if e.event_date)
                if dates:
                    pat.first_occurrence = dates[0]
                    pat.last_occurrence = dates[-1]
                    pat.frequency_per_month = self._freq_per_month(dates)
                    pat.trend = self._detect_trend(dates)
            patterns.append(pat)
        return patterns

    @staticmethod
    def _parse_date(d: str) -> Optional[date]:
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(d[:19], fmt).date()
            except (ValueError, IndexError):
                continue
        return None

    def _freq_per_month(self, dates: List[str]) -> float:
        parsed = [self._parse_date(d) for d in dates]
        valid = sorted(d for d in parsed if d is not None)
        if len(valid) < 2:
            return float(len(valid))
        span_days = (valid[-1] - valid[0]).days or 1
        months = max(span_days / 30.44, 1.0)
        return len(valid) / months

    def _detect_trend(self, dates: List[str]) -> EscalationTrend:
        parsed = [self._parse_date(d) for d in dates]
        valid = sorted(d for d in parsed if d is not None)
        if len(valid) < 4:
            return EscalationTrend.INSUFFICIENT_DATA

        mid = len(valid) // 2
        first_half_span = (valid[mid - 1] - valid[0]).days or 1
        second_half_span = (valid[-1] - valid[mid]).days or 1
        first_rate = mid / (first_half_span / 30.44)
        second_rate = (len(valid) - mid) / (second_half_span / 30.44)

        ratio = second_rate / first_rate if first_rate > 0 else 1.0
        if ratio > 1.3:
            return EscalationTrend.ESCALATING
        if ratio < 0.7:
            return EscalationTrend.DE_ESCALATING
        return EscalationTrend.STABLE

    def temporal_analysis(self, events: Sequence[AlienationEvent]) -> TemporalAnalysis:
        """Compute temporal statistics across all events."""
        ta = TemporalAnalysis()
        ta.total_events = len(events)
        if not events:
            return ta

        dates_str = sorted(e.event_date for e in events if e.event_date)
        if dates_str:
            ta.date_range_start = dates_str[0]
            ta.date_range_end = dates_str[-1]

        monthly: Dict[str, int] = defaultdict(int)
        for e in events:
            d = self._parse_date(e.event_date)
            if d:
                key = d.strftime("%Y-%m")
                monthly[key] += 1
        ta.monthly_counts = dict(monthly)

        if monthly:
            ta.peak_month = max(monthly, key=monthly.get)  # type: ignore[arg-type]
            ta.peak_count = monthly[ta.peak_month]
            ta.months_covered = len(monthly)
            ta.average_per_month = round(ta.total_events / max(ta.months_covered, 1), 2)

        all_dates = sorted(
            d
            for d in (self._parse_date(e.event_date) for e in events)
            if d is not None
        )
        if len(all_dates) >= 4:
            mid = len(all_dates) // 2
            first_count = mid
            second_count = len(all_dates) - mid
            if first_count > 0 and second_count > 0:
                ratio = second_count / first_count
                if ratio > 1.3:
                    ta.overall_trend = EscalationTrend.ESCALATING
                elif ratio < 0.7:
                    ta.overall_trend = EscalationTrend.DE_ESCALATING
                else:
                    ta.overall_trend = EscalationTrend.STABLE

        return ta

    def get_stats(self) -> Dict[str, Any]:
        return {"component": "PatternAnalyzer", "manifestations_tracked": 8}


# ---------------------------------------------------------------------------
# AlienationReporter
# ---------------------------------------------------------------------------


class AlienationReporter:
    """Generates court-ready alienation analysis reports."""

    def build_report(
        self,
        patterns: List[AlienationPattern],
        temporal: Optional[TemporalAnalysis] = None,
    ) -> AlienationReport:
        """Compile patterns and temporal data into a full report."""
        total = sum(p.score for p in patterns)
        severity = _classify_severity(total)

        plaintiff_assessment = FactorJAssessment(
            party_name=_PLAINTIFF,
            impact=FactorJImpact.FAVORS,
            narrative=(
                f"{_PLAINTIFF} demonstrates willingness to facilitate "
                f"the parent-child relationship between {_CHILD_INITIALS} "
                f"and {_DEFENDANT}."
            ),
        )
        defendant_assessment = FactorJAssessment(
            party_name=_DEFENDANT,
            impact=self._defendant_impact(total),
            narrative=self._defendant_narrative(total),
        )

        evidence_refs: List[str] = []
        for p in patterns:
            for ev in p.events:
                evidence_refs.extend(ev.evidence_refs)
        evidence_index = sorted(set(evidence_refs))

        report = AlienationReport(
            total_score=total,
            severity_level=severity,
            patterns=patterns,
            factor_j_plaintiff=plaintiff_assessment,
            factor_j_defendant=defendant_assessment,
            temporal=temporal,
            recommended_actions=_recommended_actions(severity),
            evidence_index=evidence_index,
        )
        return report

    @staticmethod
    def _defendant_impact(total: int) -> FactorJImpact:
        if total >= 17:
            return FactorJImpact.STRONGLY_AGAINST
        if total >= 11:
            return FactorJImpact.AGAINST
        if total >= 5:
            return FactorJImpact.NEUTRAL
        return FactorJImpact.FAVORS

    @staticmethod
    def _defendant_narrative(total: int) -> str:
        if total >= 17:
            return (
                f"Severe alienation pattern documented — {_DEFENDANT} "
                f"demonstrates a pervasive unwillingness to facilitate "
                f"the relationship between {_CHILD_INITIALS} and {_PLAINTIFF}."
            )
        if total >= 11:
            return (
                f"Moderate alienation indicators present — {_DEFENDANT}'s "
                f"conduct raises concerns under MCL 722.23(j)."
            )
        if total >= 5:
            return (
                f"Mild alienation indicators observed — continued "
                f"monitoring recommended."
            )
        return (
            f"No significant alienation indicators documented at this time "
            f"regarding {_DEFENDANT}."
        )

    def to_markdown(self, report: AlienationReport) -> str:
        """Render the report as Markdown text."""
        lines: List[str] = []
        lines.append(f"## Parental Alienation Analysis Report")
        lines.append(
            f"### Case: {report.case_number} | "
            f"Lane: {report.lane} | "
            f"Generated: {report.generated_at[:10]}"
        )
        lines.append("")
        lines.append(
            f"#### Overall Score: {report.total_score}/{report.max_possible} "
            f"— {report.severity_level}"
        )
        lines.append("")
        lines.append("| # | Manifestation | Score | Events | Trend |")
        lines.append("|---|---------------|-------|--------|-------|")
        for p in report.patterns:
            lines.append(
                f"| {p.indicator.value} | {p.indicator.label} | "
                f"{p.score} | {p.event_count} | {p.trend.value} |"
            )
        lines.append("")

        if report.factor_j_plaintiff:
            lines.append("#### Factor (j) — MCL 722.23(j)")
            lines.append(
                f"- **{_PLAINTIFF}:** {report.factor_j_plaintiff.impact.value} "
                f"— {report.factor_j_plaintiff.narrative}"
            )
        if report.factor_j_defendant:
            lines.append(
                f"- **{_DEFENDANT}:** {report.factor_j_defendant.impact.value} "
                f"— {report.factor_j_defendant.narrative}"
            )
        lines.append("")

        if report.temporal and report.temporal.total_events > 0:
            t = report.temporal
            lines.append("#### Temporal Analysis")
            lines.append(f"- Date range: {t.date_range_start} — {t.date_range_end}")
            lines.append(f"- Total events: {t.total_events}")
            lines.append(f"- Average per month: {t.average_per_month}")
            lines.append(f"- Peak month: {t.peak_month} ({t.peak_count} events)")
            lines.append(f"- Overall trend: {t.overall_trend.value}")
            lines.append("")

        if report.recommended_actions:
            lines.append("#### Recommended Actions")
            for i, action in enumerate(report.recommended_actions, 1):
                lines.append(f"{i}. {action}")
            lines.append("")

        if report.evidence_index:
            lines.append("#### Evidence Index")
            for ref in report.evidence_index:
                lines.append(f"- {ref}")
        return "\n".join(lines)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "AlienationReporter",
            "severity_levels": list(_SEVERITY_THRESHOLDS.keys()),
        }


# ---------------------------------------------------------------------------
# Database layer
# ---------------------------------------------------------------------------

_CREATE_TABLE_SQL = textwrap.dedent("""\
    CREATE TABLE IF NOT EXISTS alienation_indicators (
        indicator_id          TEXT PRIMARY KEY,
        event_date            TEXT NOT NULL,
        gardner_manifestation INTEGER CHECK(gardner_manifestation BETWEEN 1 AND 8),
        severity              TEXT CHECK(severity IN ('none','mild','moderate','severe')),
        description           TEXT NOT NULL,
        evidence_refs         TEXT,
        accused_party         TEXT DEFAULT 'Emily A. Watson',
        child_initials        TEXT DEFAULT 'L.D.W.',
        lane                  TEXT DEFAULT 'A',
        case_number           TEXT DEFAULT '2024-001507-DC',
        created_at            TEXT DEFAULT (datetime('now')),
        updated_at            TEXT DEFAULT (datetime('now'))
    )
""")

_CREATE_INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_alienation_date "
    "ON alienation_indicators(event_date)",
    "CREATE INDEX IF NOT EXISTS idx_alienation_manifestation "
    "ON alienation_indicators(gardner_manifestation, severity)",
]


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(_CREATE_TABLE_SQL)
    for idx in _CREATE_INDEX_SQL:
        conn.execute(idx)
    conn.commit()


# ---------------------------------------------------------------------------
# ParentalAlienationDetector  —  orchestrator
# ---------------------------------------------------------------------------


class ParentalAlienationDetector:
    """Top-level orchestrator for alienation detection and reporting.

    Combines :class:`BehaviorCataloger`, :class:`PatternAnalyzer`, and
    :class:`AlienationReporter` into a single workflow.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or _DB_PATH
        self._cataloger = BehaviorCataloger(self._db_path)
        self._analyzer = PatternAnalyzer()
        self._reporter = AlienationReporter()
        self._events: List[AlienationEvent] = []
        self._report: Optional[AlienationReport] = None

    # -- public API --

    def add_event(self, event: AlienationEvent) -> None:
        """Manually add an alienation event."""
        self._events.append(event)

    def add_events(self, events: Sequence[AlienationEvent]) -> None:
        self._events.extend(events)

    def scan_database(self, lane: str = _LANE, limit: int = 500) -> int:
        """Scan the evidence database and collect events."""
        found = self._cataloger.scan_evidence(lane=lane, limit=limit)
        self._events.extend(found)
        return len(found)

    def analyse(self) -> AlienationReport:
        """Run full analysis pipeline and return the report."""
        patterns = self._analyzer.build_patterns(self._events)
        temporal = self._analyzer.temporal_analysis(self._events)
        self._report = self._reporter.build_report(patterns, temporal)
        return self._report

    def generate_report(
        self,
        fmt: ReportFormat = ReportFormat.MARKDOWN,
    ) -> str:
        """Convenience: scan, analyse, and render in one call."""
        if not self._report:
            if not self._events:
                self.scan_database()
            self.analyse()
        assert self._report is not None

        if fmt == ReportFormat.JSON:
            return json.dumps(self._report.to_dict(), indent=2, default=str)
        if fmt == ReportFormat.TEXT:
            return self._reporter.to_markdown(self._report)
        return self._reporter.to_markdown(self._report)

    def persist(self) -> int:
        """Write collected events to the database. Returns rows written."""
        if not self._db_path.exists():
            logger.warning("Database not found — cannot persist events")
            return 0

        try:
            conn = sqlite3.connect(str(self._db_path), timeout=60)
            conn.execute("PRAGMA busy_timeout=60000")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA cache_size=-32000")
        except sqlite3.Error as exc:
            logger.error("DB connection failed: %s", exc)
            return 0

        try:
            _ensure_table(conn)
            rows: List[Tuple[Any, ...]] = []
            for ev in self._events:
                rows.append((
                    ev.event_id,
                    ev.event_date,
                    ev.indicator.value,
                    ev.severity.value,
                    ev.description,
                    json.dumps(ev.evidence_refs),
                    ev.accused_party,
                    ev.child_initials,
                    _LANE,
                    _CASE_NUMBER,
                ))
            conn.executemany(
                "INSERT OR IGNORE INTO alienation_indicators "
                "(indicator_id, event_date, gardner_manifestation, severity, "
                "description, evidence_refs, accused_party, child_initials, "
                "lane, case_number) VALUES (?,?,?,?,?,?,?,?,?,?)",
                rows,
            )
            conn.commit()
            return len(rows)
        except sqlite3.Error as exc:
            logger.error("Persist failed: %s", exc)
            return 0
        finally:
            conn.close()

    def get_stats(self) -> Dict[str, Any]:
        """Return runtime statistics."""
        return {
            "module": "parental_alienation_detector",
            "events_loaded": len(self._events),
            "report_generated": self._report is not None,
            "total_score": self._report.total_score if self._report else None,
            "severity": self._report.severity_level if self._report else None,
            "db_path": str(self._db_path),
            "cataloger": self._cataloger.get_stats(),
            "analyzer": self._analyzer.get_stats(),
            "reporter": self._reporter.get_stats(),
        }

    def reset(self) -> None:
        """Clear loaded events and report (for re-analysis)."""
        self._events.clear()
        self._report = None


# ---------------------------------------------------------------------------
# CLI demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sys.stdout = open(  # noqa: SIM115
        sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace"
    )
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print("=" * 60)
    print("  Parental Alienation Detector — LitigationOS")
    print("=" * 60)
    print()

    # Create some demo events
    demo_events = [
        AlienationEvent(
            event_date="2024-06-15",
            indicator=AlienationIndicator.CAMPAIGN_OF_DENIGRATION,
            severity=Severity.MODERATE,
            description="Example: child told targeted parent is 'bad'",
            evidence_refs=["DOC-001"],
        ),
        AlienationEvent(
            event_date="2024-07-20",
            indicator=AlienationIndicator.BORROWED_SCENARIOS,
            severity=Severity.MILD,
            description="Example: child used language matching alienating parent",
            evidence_refs=["DOC-002"],
        ),
        AlienationEvent(
            event_date="2024-08-10",
            indicator=AlienationIndicator.SPREAD_TO_EXTENDED_FAMILY,
            severity=Severity.MODERATE,
            description="Example: child refused to see grandparents",
            evidence_refs=["DOC-003"],
        ),
        AlienationEvent(
            event_date="2024-09-01",
            indicator=AlienationIndicator.CAMPAIGN_OF_DENIGRATION,
            severity=Severity.SEVERE,
            description="Example: escalated campaign",
            evidence_refs=["DOC-004"],
        ),
    ]

    detector = ParentalAlienationDetector()
    detector.add_events(demo_events)
    report = detector.analyse()

    print(detector.generate_report())
    print()
    print("--- Stats ---")
    import pprint

    pprint.pprint(detector.get_stats())
