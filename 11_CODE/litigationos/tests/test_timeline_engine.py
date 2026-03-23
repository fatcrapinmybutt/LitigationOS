"""Comprehensive tests for the TimelineEngine — case timeline visualization."""

from __future__ import annotations

import json
import sqlite3
from datetime import date, timedelta

import pytest

from litigationos.engines.timeline_engine import (
    CASE_LANES,
    VALID_EVENT_TYPES,
    VALID_IMPORTANCE,
    EventCluster,
    TimelineEngine,
    TimelineEvent,
    TimelineGap,
    TimelineResult,
    _parse_date,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mem_db(tmp_path):
    """Create a DatabaseManager-like wrapper over an in-memory SQLite DB.

    We use a thin shim so the tests do not require the full
    ``DatabaseManager`` / ``schema.sql`` bootstrap — just the tables
    the TimelineEngine cares about.
    """
    from litigationos.db.connection import DatabaseManager

    db_path = tmp_path / "test_timeline.db"
    db = DatabaseManager(db_path)
    db.initialize()
    return db


@pytest.fixture
def engine(mem_db):
    """TimelineEngine wired to the in-memory test DB."""
    return TimelineEngine(db=mem_db)


@pytest.fixture
def case_id(mem_db):
    """Insert a test case and return its row id."""
    cur = mem_db.execute(
        "INSERT INTO cases (case_number, case_type, title, status) "
        "VALUES (?, ?, ?, ?)",
        ("2024-001507-DC", "family", "Pigors v. Watson", "active"),
    )
    return cur.lastrowid


@pytest.fixture
def populated_timeline(engine, case_id, mem_db):
    """Seed timeline_events with a known set of events."""
    events = [
        (case_id, "2024-01-15", "Complaint Filed", "Initial complaint filed", "filing", "critical"),
        (case_id, "2024-02-10", "Service Completed", "Summons served", "filing", "high"),
        (case_id, "2024-03-01", "Status Conference", "First hearing", "hearing", "normal"),
        (case_id, "2024-06-15", "Discovery Deadline", "All discovery due", "deadline", "high"),
        (case_id, "2024-07-20", "Motion to Compel", "Motion filed", "filing", "normal"),
        (case_id, "2024-09-01", "Settlement Conf", "Mandatory mediation", "hearing", "high"),
        (case_id, "2024-11-05", "Trial Date", "Three-day trial", "hearing", "critical"),
        (case_id, "2025-01-10", "Order Entered", "Final order", "order", "critical"),
    ]
    for cid, dt, title, desc, etype, imp in events:
        mem_db.execute(
            "INSERT INTO timeline_events "
            "(case_id, event_date, title, description, event_type, importance) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (cid, dt, title, desc, etype, imp),
        )
    return case_id


# ---------------------------------------------------------------------------
# Pydantic Model Tests
# ---------------------------------------------------------------------------


class TestModels:
    def test_timeline_event_creation(self):
        evt = TimelineEvent(
            event_date="2024-05-01",
            title="Test Event",
            event_type="filing",
            importance="high",
        )
        assert evt.event_date == "2024-05-01"
        assert evt.importance == "high"

    def test_timeline_event_defaults(self):
        evt = TimelineEvent(event_date="2024-01-01", title="Minimal")
        assert evt.importance == "normal"
        assert evt.lane is None
        assert evt.source_table is None

    def test_timeline_gap_creation(self):
        gap = TimelineGap(
            start_date="2024-01-01",
            end_date="2024-04-01",
            gap_days=91,
            significance="high",
        )
        assert gap.gap_days == 91
        assert gap.significance == "high"

    def test_event_cluster_creation(self):
        cluster = EventCluster(
            cluster_name="filings",
            event_count=5,
            pattern_description="5 filing events",
        )
        assert cluster.cluster_name == "filings"
        assert cluster.event_count == 5
        assert cluster.events == []

    def test_timeline_result_creation(self):
        result = TimelineResult(case_id=1, total_events=0)
        assert result.events == []
        assert result.sources_queried == []


# ---------------------------------------------------------------------------
# Engine Initialization
# ---------------------------------------------------------------------------


class TestInitialization:
    def test_engine_creates(self, mem_db):
        eng = TimelineEngine(db=mem_db)
        assert eng is not None

    def test_engine_with_context_path(self, mem_db):
        eng = TimelineEngine(db=mem_db, context_db_path="/fake/path.db")
        assert eng._context_db_path == "/fake/path.db"


# ---------------------------------------------------------------------------
# build_timeline
# ---------------------------------------------------------------------------


class TestBuildTimeline:
    def test_build_empty_timeline(self, engine, case_id):
        result = engine.build_timeline(case_id=case_id)
        assert isinstance(result, TimelineResult)
        assert result.total_events == 0
        assert result.events == []

    def test_build_populated_timeline(self, engine, populated_timeline):
        result = engine.build_timeline(case_id=populated_timeline)
        assert result.total_events == 8
        assert result.case_id == populated_timeline
        assert "timeline_events" in result.sources_queried

    def test_events_sorted_chronologically(self, engine, populated_timeline):
        result = engine.build_timeline(case_id=populated_timeline)
        dates = [e.event_date for e in result.events]
        assert dates == sorted(dates)

    def test_date_range_filter(self, engine, populated_timeline):
        result = engine.build_timeline(
            case_id=populated_timeline,
            start_date="2024-06-01",
            end_date="2024-12-31",
        )
        for evt in result.events:
            assert evt.event_date >= "2024-06-01"
            assert evt.event_date <= "2024-12-31"

    def test_date_range_in_result(self, engine, populated_timeline):
        result = engine.build_timeline(case_id=populated_timeline)
        assert result.date_range is not None
        assert "2024-01-15" in result.date_range
        assert "2025-01-10" in result.date_range


# ---------------------------------------------------------------------------
# get_key_events
# ---------------------------------------------------------------------------


class TestKeyEvents:
    def test_key_events_ranked(self, engine, populated_timeline):
        key = engine.get_key_events(case_id=populated_timeline, limit=3)
        assert len(key) == 3
        # First events should be critical importance
        assert key[0].importance == "critical"

    def test_key_events_limit(self, engine, populated_timeline):
        key = engine.get_key_events(case_id=populated_timeline, limit=2)
        assert len(key) == 2

    def test_key_events_empty_case(self, engine, case_id):
        key = engine.get_key_events(case_id=case_id, limit=10)
        assert key == []


# ---------------------------------------------------------------------------
# get_lane_timeline
# ---------------------------------------------------------------------------


class TestLaneTimeline:
    def test_invalid_lane_raises(self, engine):
        with pytest.raises(ValueError, match="Invalid lane"):
            engine.get_lane_timeline("Z")

    def test_valid_lane_returns_result(self, engine):
        result = engine.get_lane_timeline("A")
        assert isinstance(result, TimelineResult)


# ---------------------------------------------------------------------------
# find_gaps
# ---------------------------------------------------------------------------


class TestFindGaps:
    def test_find_gaps_in_timeline(self, engine, populated_timeline):
        gaps = engine.find_gaps(case_id=populated_timeline, min_gap_days=20)
        assert isinstance(gaps, list)
        # There is a gap between 2024-03-01 and 2024-06-15 (106 days)
        large_gaps = [g for g in gaps if g.gap_days > 60]
        assert len(large_gaps) >= 1

    def test_gap_significance_levels(self, engine, mem_db, case_id):
        # Create events with a 200-day gap → critical
        mem_db.execute(
            "INSERT INTO timeline_events (case_id, event_date, title) VALUES (?, ?, ?)",
            (case_id, "2024-01-01", "Start"),
        )
        mem_db.execute(
            "INSERT INTO timeline_events (case_id, event_date, title) VALUES (?, ?, ?)",
            (case_id, "2024-08-01", "End"),
        )
        gaps = engine.find_gaps(case_id=case_id, min_gap_days=1)
        assert len(gaps) == 1
        assert gaps[0].significance == "critical"
        assert gaps[0].gap_days >= 180

    def test_no_gaps_when_dense(self, engine, mem_db, case_id):
        # Events every 10 days — no gaps at 30-day threshold
        base = date(2024, 1, 1)
        for i in range(10):
            d = (base + timedelta(days=i * 10)).isoformat()
            mem_db.execute(
                "INSERT INTO timeline_events (case_id, event_date, title) VALUES (?, ?, ?)",
                (case_id, d, f"Event {i}"),
            )
        gaps = engine.find_gaps(case_id=case_id, min_gap_days=30)
        assert gaps == []

    def test_empty_timeline_no_gaps(self, engine, case_id):
        gaps = engine.find_gaps(case_id=case_id)
        assert gaps == []


# ---------------------------------------------------------------------------
# get_event_clusters
# ---------------------------------------------------------------------------


class TestEventClusters:
    def test_clusters_by_type(self, engine, populated_timeline):
        clusters = engine.get_event_clusters(case_id=populated_timeline)
        assert isinstance(clusters, list)
        assert len(clusters) >= 1
        names = {c.cluster_name for c in clusters}
        assert "filing" in names or "hearing" in names

    def test_cluster_event_count(self, engine, populated_timeline):
        clusters = engine.get_event_clusters(case_id=populated_timeline)
        total = sum(c.event_count for c in clusters)
        assert total == 8

    def test_cluster_date_range(self, engine, populated_timeline):
        clusters = engine.get_event_clusters(case_id=populated_timeline)
        for c in clusters:
            if c.events:
                assert c.date_range is not None


# ---------------------------------------------------------------------------
# export_timeline
# ---------------------------------------------------------------------------


class TestExport:
    def test_export_markdown(self, engine, populated_timeline):
        md = engine.export_timeline(case_id=populated_timeline, format="md")
        assert "# Case Timeline" in md
        assert "Complaint Filed" in md
        assert "| Date |" in md

    def test_export_json(self, engine, populated_timeline):
        raw = engine.export_timeline(case_id=populated_timeline, format="json")
        data = json.loads(raw)
        assert data["total_events"] == 8
        assert len(data["events"]) == 8
        assert data["events"][0]["event_date"] == "2024-01-15"

    def test_export_csv(self, engine, populated_timeline):
        csv_out = engine.export_timeline(case_id=populated_timeline, format="csv")
        lines = csv_out.strip().split("\n")
        assert len(lines) == 9  # header + 8 events
        assert "date,event_type,title" in lines[0]

    def test_export_invalid_format(self, engine, populated_timeline):
        with pytest.raises(ValueError, match="Unsupported format"):
            engine.export_timeline(case_id=populated_timeline, format="xml")


# ---------------------------------------------------------------------------
# add_event
# ---------------------------------------------------------------------------


class TestAddEvent:
    def test_add_event(self, engine, case_id):
        eid = engine.add_event(
            case_id=case_id,
            event_date="2025-03-15",
            title="New Motion Filed",
            event_type="filing",
            importance="high",
        )
        assert isinstance(eid, int)
        assert eid > 0

    def test_add_event_appears_in_timeline(self, engine, case_id):
        engine.add_event(
            case_id=case_id,
            event_date="2025-04-01",
            title="Hearing Scheduled",
            event_type="hearing",
        )
        result = engine.build_timeline(case_id=case_id)
        assert result.total_events >= 1
        assert any(e.title == "Hearing Scheduled" for e in result.events)

    def test_add_event_invalid_importance(self, engine, case_id):
        with pytest.raises(ValueError, match="Invalid importance"):
            engine.add_event(
                case_id=case_id,
                event_date="2025-01-01",
                title="Bad",
                importance="super",
            )

    def test_add_event_invalid_type(self, engine, case_id):
        with pytest.raises(ValueError, match="Invalid event_type"):
            engine.add_event(
                case_id=case_id,
                event_date="2025-01-01",
                title="Bad",
                event_type="nonexistent",
            )

    def test_add_event_missing_fields(self, engine, case_id):
        with pytest.raises(ValueError, match="required"):
            engine.add_event(case_id=case_id, event_date="", title="")


# ---------------------------------------------------------------------------
# delete_event
# ---------------------------------------------------------------------------


class TestDeleteEvent:
    def test_delete_event(self, engine, case_id, mem_db):
        eid = engine.add_event(
            case_id=case_id,
            event_date="2025-05-01",
            title="To be deleted",
            event_type="filing",
        )
        engine.delete_event(eid)
        result = engine.build_timeline(case_id=case_id)
        assert not any(e.id == eid for e in result.events)


# ---------------------------------------------------------------------------
# Helper: _parse_date
# ---------------------------------------------------------------------------


class TestParseDate:
    def test_parse_iso_date(self):
        assert _parse_date("2024-06-15") == date(2024, 6, 15)

    def test_parse_datetime(self):
        assert _parse_date("2024-06-15T10:30:00") == date(2024, 6, 15)

    def test_parse_none(self):
        assert _parse_date(None) is None

    def test_parse_invalid(self):
        assert _parse_date("not-a-date") is None

    def test_parse_empty(self):
        assert _parse_date("") is None


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    def test_case_lanes_complete(self):
        assert len(CASE_LANES) == 6
        for lane_id in ("A", "B", "C", "D", "E", "F"):
            assert lane_id in CASE_LANES

    def test_valid_importance_levels(self):
        assert "critical" in VALID_IMPORTANCE
        assert "low" in VALID_IMPORTANCE

    def test_valid_event_types(self):
        assert "filing" in VALID_EVENT_TYPES
        assert "hearing" in VALID_EVENT_TYPES
        assert "violation" in VALID_EVENT_TYPES
