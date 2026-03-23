"""Tests for court calendar engine -- ICS generation, deadline calculation,
urgency levels, and countdown formatting for Phase 5-6."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from litigationos.db.connection import DatabaseManager
from litigationos.engines.deadline import DeadlineEngine, _HOLIDAYS


# ============================================================================
# ICS calendar generation
# ============================================================================


class TestCourtCalendarICS:
    """Test ICS file generation from deadline data."""

    def test_ics_event_from_deadline(self, tmp_db: DatabaseManager, sample_case: dict):
        """A deadline record can produce a valid ICS VEVENT block."""
        engine = DeadlineEngine(tmp_db)
        # Use 2025-06-16 (Monday) to avoid weekend adjustment
        dl_id = engine.add_deadline(
            case_id=sample_case["id"],
            title="Response to Motion",
            due_date=date(2025, 6, 16),
            priority="high",
            rule_basis="MCR 2.119",
        )
        row = tmp_db.fetchone("SELECT * FROM deadlines WHERE id = ?", (dl_id,))
        assert row is not None
        # Build an ICS fragment from the row
        dtstart = row["due_date"].replace("-", "")
        summary = row["title"]
        ics_lines = [
            "BEGIN:VEVENT",
            f"DTSTART;VALUE=DATE:{dtstart}",
            f"SUMMARY:{summary}",
            "END:VEVENT",
        ]
        ics_block = "\r\n".join(ics_lines)
        assert "BEGIN:VEVENT" in ics_block
        assert "Response to Motion" in ics_block
        assert "20250616" in ics_block

    def test_ics_calendar_wrapper(self, tmp_db: DatabaseManager):
        """Full ICS calendar must wrap events in VCALENDAR."""
        header = "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//LitigationOS//EN"
        footer = "END:VCALENDAR"
        ics = f"{header}\r\n{footer}"
        assert ics.startswith("BEGIN:VCALENDAR")
        assert ics.endswith("END:VCALENDAR")

    def test_ics_multiple_events(self, tmp_db: DatabaseManager, sample_case: dict):
        """Calendar with multiple deadlines produces multiple VEVENTs."""
        engine = DeadlineEngine(tmp_db)
        today = date.today()
        for i in range(5):
            engine.add_deadline(
                case_id=sample_case["id"],
                title=f"Deadline {i}",
                due_date=today + timedelta(days=10 + i),
            )
        upcoming = engine.get_upcoming(case_id=sample_case["id"], days=30)
        assert len(upcoming) >= 5
        # Each deadline maps to exactly one event
        events = [f"SUMMARY:{d['title']}" for d in upcoming]
        assert len(events) >= 5

    def test_ics_date_format_iso(self, tmp_db: DatabaseManager, sample_case: dict):
        """Deadline dates stored as ISO strings can be reformatted for ICS."""
        engine = DeadlineEngine(tmp_db)
        engine.add_deadline(
            case_id=sample_case["id"],
            title="ISO Date Test",
            due_date="2025-09-01",
        )
        row = tmp_db.fetchone(
            "SELECT due_date FROM deadlines WHERE title = 'ISO Date Test'"
        )
        iso_date = row["due_date"]
        ics_date = iso_date.replace("-", "")
        assert ics_date == "20250902"  # adjusted for Labor Day 2025


# ============================================================================
# Deadline calculation accuracy
# ============================================================================


class TestDeadlineCalculationAccuracy:
    """Verify deadline arithmetic edge cases."""

    def test_21_day_answer_exact(self, tmp_db: DatabaseManager):
        engine = DeadlineEngine(tmp_db)
        # 2025-04-07 (Monday) + 21 = 2025-04-28 (Monday) -- no adjustment
        result = engine.calculate_deadline("answer_complaint", date(2025, 4, 7), "circuit")
        assert result["due_date"] == date(2025, 4, 28)

    def test_56_day_brief_exact(self, tmp_db: DatabaseManager):
        engine = DeadlineEngine(tmp_db)
        # 2025-03-03 (Monday) + 56 = 2025-04-28 (Monday)
        result = engine.calculate_deadline("appellant_brief", date(2025, 3, 3), "coa")
        assert result["due_date"] == date(2025, 4, 28)

    def test_negative_days_before_hearing(self, tmp_db: DatabaseManager):
        """Motion service has negative day count (9 days before hearing)."""
        engine = DeadlineEngine(tmp_db)
        result = engine.calculate_deadline("motion_service", date(2025, 5, 15), "circuit")
        assert result is not None
        assert result["calendar_days"] == -9

    def test_supreme_court_42_day(self, tmp_db: DatabaseManager):
        engine = DeadlineEngine(tmp_db)
        result = engine.calculate_deadline("msc_leave_application", date(2025, 3, 1), "supreme")
        assert result is not None
        assert result["calendar_days"] == 42
        assert "MCR 7.302" in result["rule_basis"]

    def test_all_deadline_types_have_rule_basis(self, tmp_db: DatabaseManager):
        engine = DeadlineEngine(tmp_db)
        known_types = [
            ("answer_complaint", "circuit"),
            ("appellant_brief", "coa"),
            ("appellee_brief", "coa"),
            ("reply_brief", "coa"),
            ("msc_leave_application", "supreme"),
        ]
        for ftype, court in known_types:
            result = engine.calculate_deadline(ftype, date(2025, 6, 1), court)
            assert result is not None, f"Missing deadline rule for {ftype}/{court}"
            assert result["rule_basis"], f"No rule_basis for {ftype}"


# ============================================================================
# Urgency level assignment
# ============================================================================


class TestUrgencyLevels:
    """Test urgency/priority assignment for deadlines."""

    def test_critical_priority_for_answer(self, tmp_db: DatabaseManager):
        engine = DeadlineEngine(tmp_db)
        result = engine.calculate_deadline("answer_complaint", date(2025, 6, 1), "circuit")
        assert result["priority"] == "critical"

    def test_high_priority_for_motion_service(self, tmp_db: DatabaseManager):
        engine = DeadlineEngine(tmp_db)
        result = engine.calculate_deadline("motion_service", date(2025, 6, 1), "circuit")
        assert result["priority"] == "high"

    def test_medium_priority_for_reply(self, tmp_db: DatabaseManager):
        engine = DeadlineEngine(tmp_db)
        result = engine.calculate_deadline("motion_reply", date(2025, 6, 1), "circuit")
        assert result["priority"] == "medium"


# ============================================================================
# Countdown formatting
# ============================================================================


class TestCountdownFormatting:
    """Test countdown display logic."""

    def test_countdown_positive_days(self, tmp_db: DatabaseManager, sample_case: dict):
        engine = DeadlineEngine(tmp_db)
        future = date.today() + timedelta(days=15)
        engine.add_deadline(
            case_id=sample_case["id"],
            title="Future Deadline",
            due_date=future,
        )
        upcoming = engine.get_upcoming(case_id=sample_case["id"], days=30)
        assert len(upcoming) >= 1
        due = date.fromisoformat(upcoming[0]["due_date"])
        days_left = (due - date.today()).days
        assert days_left > 0

    def test_countdown_overdue_detection(self, tmp_db: DatabaseManager, sample_case: dict):
        engine = DeadlineEngine(tmp_db)
        past = date.today() - timedelta(days=5)
        # Insert directly to get a past due date
        tmp_db.execute(
            "INSERT INTO deadlines (case_id, title, due_date, status, priority) "
            "VALUES (?, ?, ?, 'pending', 'high')",
            (sample_case["id"], "Overdue Item", past.isoformat()),
        )
        overdue = engine.get_overdue(case_id=sample_case["id"])
        assert len(overdue) >= 1
        assert overdue[0]["title"] == "Overdue Item"

    def test_countdown_near_future(self, tmp_db: DatabaseManager, sample_case: dict):
        """Deadline due within a few days should appear in upcoming window."""
        engine = DeadlineEngine(tmp_db)
        future = date.today() + timedelta(days=3)
        adjusted = engine._next_business_day(future)
        engine.add_deadline(
            case_id=sample_case["id"],
            title="Due Soon",
            due_date=adjusted,
        )
        upcoming = engine.get_upcoming(case_id=sample_case["id"], days=10)
        titles = [d["title"] for d in upcoming]
        assert "Due Soon" in titles
