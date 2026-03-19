# -*- coding: utf-8 -*-
"""
Test Suite — Wave 7: TimelineForensics
=======================================
80+ tests covering timeline_forensics.py: event management,
contradiction detection, gap analysis, visualisations, custody
tracking, and the orchestrator.

Rules:
  - Zero network.  100 % local.
  - tempfile.mkdtemp() for isolation.
  - Mock all DB operations — never touch real litigation_context.db.
  - Every test is independent.
  - NO imports from repo root (shadow modules).
"""
from __future__ import annotations

import csv
import io
import os
import sqlite3
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Ensure the legal_ai package is importable from the tests directory
# ---------------------------------------------------------------------------
_TESTS_DIR = Path(__file__).resolve().parent
_LEGAL_AI_DIR = _TESTS_DIR.parent
if str(_LEGAL_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_LEGAL_AI_DIR))
if str(_LEGAL_AI_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_LEGAL_AI_DIR.parent))

# ---------------------------------------------------------------------------
# Import modules under test
# ---------------------------------------------------------------------------
from timeline_forensics import (
    BEST_INTEREST_FACTORS,
    LANE_CASE_NUMBERS,
    LANE_LABELS,
    Contradiction,
    ContradictionDetector,
    ContradictionSeverity,
    CustodyTimelineTracker,
    EventSource,
    EventTag,
    ForensicReport,
    GapAnalyzer,
    GapCategory,
    SourceType,
    TimelineEvent,
    TimelineForensics,
    TimelineGap,
    TimelineVisualizer,
    _PLAINTIFF,
    _DEFENDANT,
    _CHILD_INITIALS,
    _JUDGE,
)


# ═══════════════════════════════════════════════════════════════════════════
# Helpers / Fixtures
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def tmp_db() -> Path:
    """Create a temporary SQLite database for testing."""
    d = tempfile.mkdtemp(prefix="litostest_tl_")
    db_path = Path(d) / "test_timeline.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.close()
    return db_path


def _make_event(
    date_str: str = "2024-06-15",
    description: str = "Test event",
    lane: str = "A",
    actors: List[str] | None = None,
    tags: List[str] | None = None,
    source_type: str = "record",
    confidence: float = 75.0,
    **kwargs: Any,
) -> TimelineEvent:
    return TimelineEvent(
        date=date_str,
        description=description,
        lane=lane,
        actors=actors or [_PLAINTIFF],
        tags=tags or [],
        source_type=source_type,
        confidence=confidence,
        **kwargs,
    )


def _make_events_sequence(
    count: int = 5,
    start_date: str = "2024-01-01",
    gap_days: int = 10,
    lane: str = "A",
) -> List[TimelineEvent]:
    """Create a sequence of events with fixed gaps."""
    events: List[TimelineEvent] = []
    base = datetime.strptime(start_date, "%Y-%m-%d").date()
    for i in range(count):
        d = base + timedelta(days=i * gap_days)
        events.append(_make_event(
            date_str=d.isoformat(),
            description=f"Event #{i+1}",
            lane=lane,
        ))
    return events


# ═══════════════════════════════════════════════════════════════════════════
# 1 — Enumerations
# ═══════════════════════════════════════════════════════════════════════════

class TestTimelineEnums:

    def test_source_type_values(self) -> None:
        expected = {
            "transcript", "filing", "exhibit", "record", "police_report",
            "social_media", "affidavit", "court_order", "communication", "medical",
        }
        assert {s.value for s in SourceType} == expected

    def test_source_type_count(self) -> None:
        assert len(SourceType) == 10

    def test_event_tag_values(self) -> None:
        tags = {t.value for t in EventTag}
        assert "custody_exchange" in tags
        assert "custody_denial" in tags
        assert "court_hearing" in tags
        assert "judicial_conduct" in tags
        assert "ex_parte" in tags

    def test_event_tag_count(self) -> None:
        assert len(EventTag) == 16

    def test_contradiction_severity_values(self) -> None:
        expected = {"minor", "moderate", "severe", "critical"}
        assert {s.value for s in ContradictionSeverity} == expected

    def test_gap_category_values(self) -> None:
        expected = {"temporal", "evidence", "suppressed", "coverage"}
        assert {g.value for g in GapCategory} == expected


# ═══════════════════════════════════════════════════════════════════════════
# 2 — Data Models
# ═══════════════════════════════════════════════════════════════════════════

class TestEventSource:

    def test_creation_auto_id(self) -> None:
        s = EventSource()
        assert s.source_id
        assert len(s.source_id) == 12

    def test_to_dict(self) -> None:
        s = EventSource(source_type="filing", file_path="/some/path.pdf")
        d = s.to_dict()
        assert d["source_type"] == "filing"
        assert d["file_path"] == "/some/path.pdf"
        assert "date_range" in d

    def test_custom_id(self) -> None:
        s = EventSource(source_id="custom_src")
        assert s.source_id == "custom_src"

    def test_default_reliability(self) -> None:
        s = EventSource()
        assert s.reliability_score == 75.0


class TestTimelineEvent:

    def test_creation_auto_id(self) -> None:
        e = TimelineEvent()
        assert e.event_id
        assert len(e.event_id) == 12

    def test_creation_custom_id(self) -> None:
        e = TimelineEvent(event_id="abc123def456")
        assert e.event_id == "abc123def456"

    def test_to_dict(self) -> None:
        e = _make_event(description="Hello world")
        d = e.to_dict()
        assert d["description"] == "Hello world"
        assert "event_id" in d
        assert "actors" in d

    def test_uuid_format(self) -> None:
        e = TimelineEvent()
        assert len(e.event_id) == 12

    def test_overlaps_same_date(self) -> None:
        e1 = _make_event(date_str="2024-06-15")
        e2 = _make_event(date_str="2024-06-15")
        assert e1.overlaps(e2) is True

    def test_overlaps_range(self) -> None:
        e1 = _make_event(date_str="2024-06-01", end_date="2024-06-30")
        e2 = _make_event(date_str="2024-06-15")
        assert e1.overlaps(e2) is True

    def test_no_overlap(self) -> None:
        e1 = _make_event(date_str="2024-01-01", end_date="2024-01-31")
        e2 = _make_event(date_str="2024-06-01")
        assert e1.overlaps(e2) is False

    def test_overlaps_empty_date(self) -> None:
        e1 = _make_event(date_str="")
        e2 = _make_event(date_str="2024-06-15")
        assert e1.overlaps(e2) is False

    def test_contradicts_event_same_actors_same_time(self) -> None:
        e1 = _make_event(
            date_str="2024-06-15",
            description="Child was at school",
            actors=[_DEFENDANT],
        )
        e2 = _make_event(
            date_str="2024-06-15",
            description="Child was at home",
            actors=[_DEFENDANT],
        )
        assert e1.contradicts_event(e2) is True

    def test_contradicts_event_different_actors(self) -> None:
        e1 = _make_event(date_str="2024-06-15", actors=["Person A"])
        e2 = _make_event(date_str="2024-06-15", actors=["Person B"])
        assert e1.contradicts_event(e2) is False

    def test_contradicts_event_different_dates(self) -> None:
        e1 = _make_event(date_str="2024-01-01", actors=[_PLAINTIFF])
        e2 = _make_event(date_str="2024-12-31", actors=[_PLAINTIFF])
        assert e1.contradicts_event(e2) is False

    def test_parse_date_valid(self) -> None:
        e = _make_event(date_str="2024-06-15")
        assert e._parse_date() == date(2024, 6, 15)

    def test_parse_date_invalid(self) -> None:
        e = _make_event(date_str="not-a-date")
        assert e._parse_date() is None

    def test_parse_date_empty(self) -> None:
        e = _make_event(date_str="")
        assert e._parse_date() is None

    def test_default_lane(self) -> None:
        e = TimelineEvent()
        assert e.lane == "A"

    def test_default_confidence(self) -> None:
        e = TimelineEvent()
        assert e.confidence == 75.0


class TestContradiction:

    def test_creation_auto_id(self) -> None:
        c = Contradiction()
        assert c.contradiction_id
        assert len(c.contradiction_id) == 12

    def test_to_dict(self) -> None:
        c = Contradiction(
            event_a_id="aaa",
            event_b_id="bbb",
            contradiction_type="temporal",
            severity="severe",
        )
        d = c.to_dict()
        assert d["event_a_id"] == "aaa"
        assert d["severity"] == "severe"


class TestTimelineGap:

    def test_creation_auto_id(self) -> None:
        g = TimelineGap()
        assert g.gap_id
        assert len(g.gap_id) == 12

    def test_to_dict(self) -> None:
        g = TimelineGap(
            gap_category="temporal",
            start_date="2024-01-01",
            end_date="2024-06-01",
            description="Missing period",
        )
        d = g.to_dict()
        assert d["gap_category"] == "temporal"
        assert d["start_date"] == "2024-01-01"


class TestForensicReport:

    def test_creation_auto_id(self) -> None:
        r = ForensicReport()
        assert r.report_id
        assert r.generated_at

    def test_to_dict(self) -> None:
        r = ForensicReport(event_count=10, contradiction_count=2)
        d = r.to_dict()
        assert d["event_count"] == 10
        assert "contradictions" in d
        assert "gaps" in d


# ═══════════════════════════════════════════════════════════════════════════
# 3 — ContradictionDetector
# ═══════════════════════════════════════════════════════════════════════════

class TestContradictionDetector:

    def test_detect_temporal_no_events(self) -> None:
        cd = ContradictionDetector()
        result = cd.detect_temporal_contradictions([])
        assert result == []

    def test_detect_temporal_no_overlap(self) -> None:
        cd = ContradictionDetector()
        events = [
            _make_event(date_str="2024-01-01", actors=["A"]),
            _make_event(date_str="2024-06-01", actors=["A"]),
        ]
        result = cd.detect_temporal_contradictions(events)
        assert result == []

    def test_detect_temporal_contradiction(self) -> None:
        cd = ContradictionDetector()
        e1 = _make_event(
            date_str="2024-06-15",
            description="Person was at location X",
            actors=["PersonA"],
        )
        e2 = _make_event(
            date_str="2024-06-15",
            description="Person was at location Y",
            actors=["PersonA"],
        )
        result = cd.detect_temporal_contradictions([e1, e2])
        assert len(result) == 1
        assert result[0].contradiction_type == "temporal"

    def test_detect_factual_no_events(self) -> None:
        cd = ContradictionDetector()
        result = cd.detect_factual_contradictions([])
        assert result == []

    def test_detect_factual_contradiction(self) -> None:
        cd = ContradictionDetector()
        e1 = _make_event(
            description="Child was present at school",
            tags=["education"],
            source_type="record",
        )
        e2 = _make_event(
            description="Child was absent from school",
            tags=["education"],
            source_type="affidavit",
        )
        result = cd.detect_factual_contradictions([e1, e2])
        assert len(result) == 1
        assert result[0].contradiction_type == "factual"

    def test_detect_record_contradictions(self) -> None:
        cd = ContradictionDetector()
        testimony = _make_event(
            date_str="2024-06-15",
            description="Witness was present at the hearing",
            source_type="transcript",
            actors=[_DEFENDANT],
        )
        official = _make_event(
            date_str="2024-06-15",
            description="Witness was absent from the hearing",
            source_type="record",
            actors=[_DEFENDANT],
        )
        result = cd.detect_record_contradictions([testimony], [official])
        assert len(result) == 1
        assert result[0].contradiction_type == "record"
        assert result[0].severity == "severe"

    def test_detect_record_no_overlap(self) -> None:
        cd = ContradictionDetector()
        testimony = _make_event(date_str="2024-01-01", actors=["A"])
        official = _make_event(date_str="2024-12-31", actors=["A"])
        result = cd.detect_record_contradictions([testimony], [official])
        assert result == []

    def test_score_contradiction_severity_record(self) -> None:
        cd = ContradictionDetector()
        c = Contradiction(contradiction_type="record")
        result = cd.score_contradiction_severity(c)
        assert result == "severe"

    def test_score_contradiction_severity_temporal(self) -> None:
        cd = ContradictionDetector()
        c = Contradiction(contradiction_type="temporal")
        result = cd.score_contradiction_severity(c)
        assert result == "critical"

    def test_score_contradiction_severity_default(self) -> None:
        cd = ContradictionDetector()
        c = Contradiction(contradiction_type="factual")
        result = cd.score_contradiction_severity(c)
        assert result == "moderate"

    def test_generate_impeachment_brief(self) -> None:
        cd = ContradictionDetector()
        contradictions = [
            Contradiction(
                event_a_id="a1", event_b_id="b1",
                contradiction_type="temporal", severity="critical",
                description="Same person two places",
                impeachment_use="MRE 613",
            ),
            Contradiction(
                event_a_id="a2", event_b_id="b2",
                contradiction_type="factual", severity="moderate",
                description="Conflicting accounts",
                impeachment_use="MRE 613",
            ),
        ]
        brief = cd.generate_impeachment_brief(contradictions)
        assert "IMPEACHMENT BRIEF" in brief
        assert "CRITICAL" in brief
        assert "Contradiction #1" in brief
        assert "Contradiction #2" in brief

    def test_generate_impeachment_brief_empty(self) -> None:
        cd = ContradictionDetector()
        brief = cd.generate_impeachment_brief([])
        assert "Contradictions Identified: 0" in brief

    def test_total_detected_property(self) -> None:
        cd = ContradictionDetector()
        e1 = _make_event(date_str="2024-06-15", actors=["X"], description="Claim A")
        e2 = _make_event(date_str="2024-06-15", actors=["X"], description="Claim B")
        cd.detect_temporal_contradictions([e1, e2])
        assert cd.total_detected >= 1

    def test_descriptions_conflict_positive(self) -> None:
        result = ContradictionDetector._descriptions_conflict(
            "She was present at the meeting",
            "She was absent from the meeting",
        )
        assert result is True

    def test_descriptions_conflict_negative(self) -> None:
        result = ContradictionDetector._descriptions_conflict(
            "She went to the store",
            "She bought groceries",
        )
        assert result is False


# ═══════════════════════════════════════════════════════════════════════════
# 4 — GapAnalyzer
# ═══════════════════════════════════════════════════════════════════════════

class TestGapAnalyzer:

    def test_find_temporal_gaps_empty(self) -> None:
        ga = GapAnalyzer()
        result = ga.find_temporal_gaps(
            [],
            expected_coverage=("2024-01-01", "2024-12-31"),
        )
        assert len(result) == 1
        assert result[0].severity == "critical"

    def test_find_temporal_gaps_no_gap(self) -> None:
        ga = GapAnalyzer()
        events = _make_events_sequence(count=10, gap_days=5)
        result = ga.find_temporal_gaps(
            events,
            expected_coverage=(events[0].date, events[-1].date),
            max_gap_days=30,
        )
        assert len(result) == 0

    def test_find_temporal_gaps_large_gap(self) -> None:
        ga = GapAnalyzer()
        events = [
            _make_event(date_str="2024-01-01"),
            _make_event(date_str="2024-06-01"),
        ]
        result = ga.find_temporal_gaps(
            events,
            expected_coverage=("2024-01-01", "2024-12-31"),
            max_gap_days=30,
        )
        assert len(result) >= 1

    def test_find_evidence_gaps_default(self) -> None:
        ga = GapAnalyzer()
        events = [
            _make_event(tags=[EventTag.CUSTODY_DENIAL.value]),
        ]
        result = ga.find_evidence_gaps(events)
        assert len(result) >= 1  # missing some required elements

    def test_find_evidence_gaps_all_covered(self) -> None:
        ga = GapAnalyzer()
        events = [
            _make_event(tags=[
                EventTag.CUSTODY_DENIAL.value,
                EventTag.POLICE_CONTACT.value,
                EventTag.COMMUNICATION.value,
                EventTag.PPO_EVENT.value,
                EventTag.COURT_HEARING.value,
                EventTag.HOUSING_ISSUE.value,
                EventTag.JUDICIAL_CONDUCT.value,
                EventTag.EX_PARTE.value,
            ]),
        ]
        result = ga.find_evidence_gaps(events)
        assert len(result) == 0

    def test_find_evidence_gaps_custom_requirements(self) -> None:
        ga = GapAnalyzer()
        events = [_make_event(tags=["tag_a"])]
        result = ga.find_evidence_gaps(events, {"claim1": ["tag_a", "tag_b"]})
        assert len(result) == 1
        assert "tag_b" in result[0].description

    def test_identify_suppressed_periods_none(self) -> None:
        ga = GapAnalyzer()
        events = _make_events_sequence(count=5, gap_days=10)
        result = ga.identify_suppressed_periods(events)
        assert len(result) == 0

    def test_identify_suppressed_periods_large_gap(self) -> None:
        ga = GapAnalyzer()
        e1 = _make_event(date_str="2024-01-01", actors=["PersonX"])
        e2 = _make_event(date_str="2024-06-01", actors=["PersonX"])
        result = ga.identify_suppressed_periods([e1, e2])
        assert len(result) >= 1
        assert result[0].gap_category == "suppressed"

    def test_recommend_discovery(self) -> None:
        ga = GapAnalyzer()
        gaps = [
            TimelineGap(
                gap_category="temporal",
                start_date="2024-01-01",
                end_date="2024-03-01",
                description="Gap in records",
                severity="high",
                discovery_recommendation="Get records",
            ),
        ]
        recs = ga.recommend_discovery(gaps)
        assert len(recs) == 1
        assert "discovery_type" in recs[0]

    def test_recommend_discovery_evidence_gap(self) -> None:
        ga = GapAnalyzer()
        gaps = [
            TimelineGap(
                gap_category="evidence",
                description="Missing proof",
                severity="moderate",
                discovery_recommendation="Obtain evidence",
            ),
        ]
        recs = ga.recommend_discovery(gaps)
        assert "Interrogatories" in recs[0]["discovery_type"]

    def test_recommend_discovery_suppressed(self) -> None:
        ga = GapAnalyzer()
        gaps = [
            TimelineGap(
                gap_category="suppressed",
                start_date="2024-01-01",
                end_date="2024-06-01",
                description="Suspicious gap",
                severity="high",
                discovery_recommendation="Subpoena",
            ),
        ]
        recs = ga.recommend_discovery(gaps)
        assert "Subpoena" in recs[0]["discovery_type"]

    def test_days_between_valid(self) -> None:
        result = GapAnalyzer._days_between("2024-01-01", "2024-01-31")
        assert result == 30

    def test_days_between_invalid(self) -> None:
        result = GapAnalyzer._days_between("not-a-date", "2024-01-31")
        assert result == 0

    def test_total_gaps_property(self) -> None:
        ga = GapAnalyzer()
        ga.find_temporal_gaps([], expected_coverage=("2024-01-01", "2024-06-01"))
        assert ga.total_gaps >= 1


# ═══════════════════════════════════════════════════════════════════════════
# 5 — TimelineVisualizer
# ═══════════════════════════════════════════════════════════════════════════

class TestTimelineVisualizer:

    def test_mermaid_gantt_empty(self) -> None:
        result = TimelineVisualizer.generate_mermaid_gantt([])
        assert "```mermaid" in result
        assert "gantt" in result
        assert "No events" in result

    def test_mermaid_gantt_with_events(self) -> None:
        events = _make_events_sequence(count=3, lane="A")
        result = TimelineVisualizer.generate_mermaid_gantt(events)
        assert "```mermaid" in result
        assert "gantt" in result
        assert "dateFormat" in result
        assert "section" in result
        assert result.strip().endswith("```")

    def test_mermaid_gantt_multiple_lanes(self) -> None:
        events = [
            _make_event(date_str="2024-01-01", lane="A", description="Lane A event"),
            _make_event(date_str="2024-02-01", lane="B", description="Lane B event"),
        ]
        result = TimelineVisualizer.generate_mermaid_gantt(events)
        assert "section" in result

    def test_mermaid_timeline_empty(self) -> None:
        result = TimelineVisualizer.generate_mermaid_timeline([])
        assert "```mermaid" in result
        assert "timeline" in result
        assert "No Events" in result

    def test_mermaid_timeline_with_events(self) -> None:
        events = _make_events_sequence(count=3)
        result = TimelineVisualizer.generate_mermaid_timeline(events)
        assert "```mermaid" in result
        assert "timeline" in result
        assert "2024-01" in result

    def test_parallel_timelines(self) -> None:
        andrew = [_make_event(date_str="2024-01-01", actors=[_PLAINTIFF])]
        emily = [_make_event(date_str="2024-02-01", actors=[_DEFENDANT])]
        official = [_make_event(date_str="2024-03-01", source_type="court_order")]
        result = TimelineVisualizer.generate_parallel_timelines(
            andrew, emily, official,
        )
        assert "```mermaid" in result
        assert "Parallel Timelines" in result
        assert _PLAINTIFF in result
        assert _DEFENDANT in result

    def test_html_timeline_empty(self) -> None:
        result = TimelineVisualizer.generate_html_timeline([])
        assert "<!DOCTYPE html>" in result
        assert "Interactive Timeline" in result

    def test_html_timeline_with_events(self) -> None:
        events = _make_events_sequence(count=3)
        result = TimelineVisualizer.generate_html_timeline(events)
        assert "<!DOCTYPE html>" in result
        assert "tl-container" in result
        assert "filterLane" in result

    def test_html_timeline_contradiction_badge(self) -> None:
        e = _make_event(date_str="2024-06-15")
        e.contradicts = ["other_id"]
        result = TimelineVisualizer.generate_html_timeline([e])
        assert "contradiction" in result.lower()

    def test_csv_export_empty(self) -> None:
        result = TimelineVisualizer.export_csv([])
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)
        assert len(rows) == 1  # header only
        assert rows[0][0] == "event_id"

    def test_csv_export_with_events(self) -> None:
        events = _make_events_sequence(count=3)
        result = TimelineVisualizer.export_csv(events)
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)
        assert len(rows) == 4  # header + 3 events

    def test_csv_export_to_file(self) -> None:
        d = tempfile.mkdtemp(prefix="litostest_csv_")
        p = Path(d) / "timeline.csv"
        events = [_make_event()]
        TimelineVisualizer.export_csv(events, path=p)
        assert p.exists()
        content = p.read_text(encoding="utf-8")
        assert "event_id" in content

    def test_csv_export_contains_all_columns(self) -> None:
        events = [_make_event()]
        result = TimelineVisualizer.export_csv(events)
        reader = csv.reader(io.StringIO(result))
        header = next(reader)
        expected_cols = [
            "event_id", "date", "end_date", "description",
            "source_type", "source_ref", "page_ref", "actors",
            "lane", "tags", "confidence", "contradicts",
        ]
        assert header == expected_cols


# ═══════════════════════════════════════════════════════════════════════════
# 6 — CustodyTimelineTracker
# ═══════════════════════════════════════════════════════════════════════════

class TestCustodyTimelineTracker:

    def test_track_exchanges_empty(self) -> None:
        ctt = CustodyTimelineTracker()
        result = ctt.track_custody_exchanges([])
        assert result["total_events"] == 0

    def test_track_exchanges_with_denials(self) -> None:
        ctt = CustodyTimelineTracker()
        events = [
            _make_event(
                date_str="2024-06-15",
                tags=[EventTag.CUSTODY_DENIAL.value],
                description="Parenting time denied",
            ),
            _make_event(
                date_str="2024-06-22",
                tags=[EventTag.CUSTODY_EXCHANGE.value],
                description="Successful exchange",
            ),
        ]
        result = ctt.track_custody_exchanges(events)
        assert result["total_events"] == 2
        assert result["denials"] == 1
        assert result["successful_exchanges"] == 1

    def test_calculate_lost_parenting_time_empty(self) -> None:
        ctt = CustodyTimelineTracker()
        result = ctt.calculate_lost_parenting_time([])
        assert result["denial_count"] == 0
        assert result["damages_low"] == 0.0

    def test_calculate_lost_parenting_time_with_denials(self) -> None:
        ctt = CustodyTimelineTracker()
        denials = [
            _make_event(tags=[EventTag.CUSTODY_DENIAL.value])
            for _ in range(10)
        ]
        result = ctt.calculate_lost_parenting_time(denials)
        assert result["denial_count"] == 10
        assert result["damages_low"] == 10 * 328.0
        assert result["damages_high"] == 10 * 656.0
        assert result["statute"] == "MCL 722.27a"

    def test_track_order_compliance_no_violations(self) -> None:
        ctt = CustodyTimelineTracker()
        events = [_make_event(description="Normal activity occurred")]
        result = ctt.track_order_compliance(events)
        assert result == []

    def test_track_order_compliance_violation(self) -> None:
        ctt = CustodyTimelineTracker()
        events = [
            _make_event(
                description="Parenting time exchange was denied by mother",
                actors=[_DEFENDANT],
            ),
        ]
        result = ctt.track_order_compliance(events)
        assert len(result) >= 1

    def test_best_interest_timeline_empty(self) -> None:
        ctt = CustodyTimelineTracker()
        result = ctt.generate_best_interest_timeline([])
        assert len(result) == 12  # 12 factors (a-l)

    def test_best_interest_timeline_matches(self) -> None:
        ctt = CustodyTimelineTracker()
        events = [
            _make_event(description="Showed love and affection to child"),
            _make_event(description="Child attended school regularly"),
            _make_event(description="Domestic violence incident reported"),
        ]
        result = ctt.generate_best_interest_timeline(events)
        assert len(result["a"]) >= 1  # love/affection
        assert len(result["h"]) >= 1  # school
        assert len(result["k"]) >= 1  # violence


# ═══════════════════════════════════════════════════════════════════════════
# 7 — TimelineForensics Orchestrator
# ═══════════════════════════════════════════════════════════════════════════

class TestTimelineForensics:

    def test_init(self, tmp_db: Path) -> None:
        engine = TimelineForensics(db_path=tmp_db)
        assert engine.VERSION == "1.0.0"

    def test_add_event(self, tmp_db: Path) -> None:
        engine = TimelineForensics(db_path=tmp_db)
        eid = engine.add_event(_make_event())
        assert eid  # returns event_id

    def test_add_events_batch(self, tmp_db: Path) -> None:
        engine = TimelineForensics(db_path=tmp_db)
        events = _make_events_sequence(count=5)
        count = engine.add_events(events)
        assert count == 5

    def test_build_master_timeline(self, tmp_db: Path) -> None:
        engine = TimelineForensics(db_path=tmp_db)
        result = engine.build_master_timeline()
        assert "total_events" in result
        assert result["total_events"] >= 0

    def test_build_master_timeline_seeds(self, tmp_db: Path) -> None:
        engine = TimelineForensics(db_path=tmp_db)
        result = engine.build_master_timeline()
        assert result["total_events"] >= 6  # seed events

    def test_analyze_contradictions_empty(self, tmp_db: Path) -> None:
        engine = TimelineForensics(db_path=tmp_db)
        engine.add_events(_make_events_sequence(count=3))
        result = engine.analyze_contradictions()
        assert isinstance(result, list)

    def test_analyze_contradictions_detects(self, tmp_db: Path) -> None:
        engine = TimelineForensics(db_path=tmp_db)
        e1 = _make_event(
            date_str="2024-06-15",
            description="Person was at location A",
            actors=["SharedActor"],
        )
        e2 = _make_event(
            date_str="2024-06-15",
            description="Person was at location B",
            actors=["SharedActor"],
        )
        engine.add_events([e1, e2])
        result = engine.analyze_contradictions()
        assert len(result) >= 1

    def test_analyze_gaps(self, tmp_db: Path) -> None:
        engine = TimelineForensics(db_path=tmp_db)
        engine.add_events(_make_events_sequence(count=2, gap_days=100))
        result = engine.analyze_gaps()
        assert isinstance(result, list)

    def test_generate_forensic_report(self, tmp_db: Path) -> None:
        engine = TimelineForensics(db_path=tmp_db)
        engine.add_events(_make_events_sequence(count=5))
        report = engine.generate_forensic_report()
        assert isinstance(report, ForensicReport)
        assert report.event_count >= 5

    def test_forensic_report_to_dict(self, tmp_db: Path) -> None:
        engine = TimelineForensics(db_path=tmp_db)
        engine.add_events([_make_event()])
        report = engine.generate_forensic_report()
        d = report.to_dict()
        assert "event_count" in d
        assert "contradictions" in d

    def test_generate_mermaid(self, tmp_db: Path) -> None:
        engine = TimelineForensics(db_path=tmp_db)
        engine.add_events(_make_events_sequence(count=3))
        result = engine.generate_mermaid()
        assert "```mermaid" in result

    def test_generate_html(self, tmp_db: Path) -> None:
        engine = TimelineForensics(db_path=tmp_db)
        engine.add_events(_make_events_sequence(count=3))
        result = engine.generate_html()
        assert "<!DOCTYPE html>" in result

    def test_export_csv(self, tmp_db: Path) -> None:
        engine = TimelineForensics(db_path=tmp_db)
        engine.add_events(_make_events_sequence(count=3))
        result = engine.export_csv()
        assert "event_id" in result

    def test_track_custody(self, tmp_db: Path) -> None:
        engine = TimelineForensics(db_path=tmp_db)
        denial = _make_event(
            lane="A",
            tags=[EventTag.CUSTODY_DENIAL.value],
            description="Parenting time denied",
        )
        engine.add_event(denial)
        result = engine.track_custody()
        assert "exchanges" in result
        assert "lost_parenting_time" in result

    def test_get_stats(self, tmp_db: Path) -> None:
        engine = TimelineForensics(db_path=tmp_db)
        stats = engine.get_stats()
        assert stats["engine"] == "TimelineForensics"
        assert "event_count" in stats
        assert stats["case_context"]["plaintiff"] == _PLAINTIFF
        assert stats["case_context"]["defendant"] == _DEFENDANT

    def test_get_stats_after_events(self, tmp_db: Path) -> None:
        engine = TimelineForensics(db_path=tmp_db)
        engine.add_events(_make_events_sequence(count=5))
        stats = engine.get_stats()
        assert stats["event_count"] == 5

    def test_generate_text_report(self, tmp_db: Path) -> None:
        engine = TimelineForensics(db_path=tmp_db)
        engine.add_events(_make_events_sequence(count=3))
        text = engine.generate_text_report()
        assert "TIMELINE FORENSICS REPORT" in text
        assert "EVENTS BY LANE" in text


# ═══════════════════════════════════════════════════════════════════════════
# 8 — Edge Cases
# ═══════════════════════════════════════════════════════════════════════════

class TestEdgeCases:

    def test_single_event_timeline(self, tmp_db: Path) -> None:
        engine = TimelineForensics(db_path=tmp_db)
        engine.add_event(_make_event())
        report = engine.generate_forensic_report()
        assert report.event_count == 1

    def test_empty_events_timeline(self, tmp_db: Path) -> None:
        engine = TimelineForensics(db_path=tmp_db)
        stats = engine.get_stats()
        assert stats["event_count"] == 0

    def test_same_day_contradictions(self, tmp_db: Path) -> None:
        engine = TimelineForensics(db_path=tmp_db)
        for i in range(5):
            engine.add_event(_make_event(
                date_str="2024-06-15",
                description=f"Different claim #{i}",
                actors=["SharedPerson"],
            ))
        contradictions = engine.analyze_contradictions()
        assert len(contradictions) >= 1

    def test_overlapping_span_events(self) -> None:
        e1 = _make_event(date_str="2024-01-01", end_date="2024-06-30")
        e2 = _make_event(date_str="2024-03-01", end_date="2024-09-30")
        assert e1.overlaps(e2) is True

    def test_adjacent_non_overlapping(self) -> None:
        e1 = _make_event(date_str="2024-01-01", end_date="2024-01-31")
        e2 = _make_event(date_str="2024-02-01")
        assert e1.overlaps(e2) is False

    def test_event_no_actors_no_contradiction(self) -> None:
        e1 = _make_event(date_str="2024-06-15", actors=[])
        e2 = _make_event(date_str="2024-06-15", actors=[])
        assert e1.contradicts_event(e2) is False

    def test_same_description_no_contradiction(self) -> None:
        e1 = _make_event(
            date_str="2024-06-15",
            description="Same exact claim",
            actors=["Person"],
        )
        e2 = _make_event(
            date_str="2024-06-15",
            description="Same exact claim",
            actors=["Person"],
        )
        assert e1.contradicts_event(e2) is False

    def test_event_with_all_tags(self) -> None:
        e = _make_event(tags=[t.value for t in EventTag])
        assert len(e.tags) == len(EventTag)

    def test_large_number_of_events(self, tmp_db: Path) -> None:
        engine = TimelineForensics(db_path=tmp_db)
        events = _make_events_sequence(count=100, gap_days=1)
        engine.add_events(events)
        stats = engine.get_stats()
        assert stats["event_count"] == 100


# ═══════════════════════════════════════════════════════════════════════════
# 9 — Constants & Lane Routing
# ═══════════════════════════════════════════════════════════════════════════

class TestTimelineConstants:

    def test_lane_labels(self) -> None:
        for lane in ("A", "B", "C", "D", "E", "F"):
            assert lane in LANE_LABELS

    def test_lane_case_numbers(self) -> None:
        assert LANE_CASE_NUMBERS["A"] == "2024-001507-DC"
        assert LANE_CASE_NUMBERS["D"] == "2023-5907-PP"

    def test_plaintiff(self) -> None:
        assert _PLAINTIFF == "Andrew James Pigors"

    def test_defendant(self) -> None:
        assert _DEFENDANT == "Emily A. Watson"

    def test_child_initials(self) -> None:
        assert _CHILD_INITIALS == "L.D.W."

    def test_judge(self) -> None:
        assert _JUDGE == "Hon. Jenny L. McNeill"

    def test_best_interest_factors_count(self) -> None:
        assert len(BEST_INTEREST_FACTORS) == 12

    def test_best_interest_factor_a(self) -> None:
        assert "Love" in BEST_INTEREST_FACTORS["a"]

    def test_best_interest_factor_k(self) -> None:
        assert "violence" in BEST_INTEREST_FACTORS["k"].lower()

    def test_lane_routing_event(self) -> None:
        for lane in ("A", "B", "C", "D", "E", "F"):
            e = _make_event(lane=lane)
            assert e.lane == lane
