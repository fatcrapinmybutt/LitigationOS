"""Tests for the Dashboard home screen engine."""

from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from pathlib import Path

import pytest

from litigationos.engines.dashboard import (
    DashboardEngine,
    FILING_NAMES,
    LANE_REGISTRY,
    SEPARATION_DATE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_db(tmp_path: Path) -> Path:
    """Create a minimal DB with tables the dashboard queries."""
    db_path = tmp_path / "test_dash.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode = WAL")

    # evidence_quotes
    conn.execute(
        "CREATE TABLE evidence_quotes (id INTEGER PRIMARY KEY, quote TEXT, lane TEXT)"
    )
    for i in range(25):
        lane = "A" if i < 10 else ("E" if i < 20 else "F")
        conn.execute(
            "INSERT INTO evidence_quotes (quote, lane) VALUES (?, ?)",
            (f"quote {i}", lane),
        )

    # citation_audit
    conn.execute("CREATE TABLE citation_audit (id INTEGER PRIMARY KEY, citation TEXT)")
    for i in range(12):
        conn.execute("INSERT INTO citation_audit (citation) VALUES (?)", (f"cite {i}",))

    # impeachment_matrix
    conn.execute("CREATE TABLE impeachment_matrix (id INTEGER PRIMARY KEY, item TEXT)")
    conn.executemany(
        "INSERT INTO impeachment_matrix (item) VALUES (?)",
        [(f"imp {i}",) for i in range(8)],
    )

    # judicial_bias_chronology
    conn.execute(
        "CREATE TABLE judicial_bias_chronology (id INTEGER PRIMARY KEY, event TEXT)"
    )
    conn.executemany(
        "INSERT INTO judicial_bias_chronology (event) VALUES (?)",
        [(f"bias {i}",) for i in range(5)],
    )

    # alienation_timeline
    conn.execute(
        "CREATE TABLE alienation_timeline (id INTEGER PRIMARY KEY, event TEXT, days INTEGER)"
    )
    conn.executemany(
        "INSERT INTO alienation_timeline (event, days) VALUES (?, ?)",
        [(f"alien {i}", 10 + i) for i in range(4)],
    )

    # authority_chain_audit
    conn.execute(
        "CREATE TABLE authority_chain_audit (id INTEGER PRIMARY KEY, filing_id TEXT, chain_complete INTEGER)"
    )
    conn.executemany(
        "INSERT INTO authority_chain_audit (filing_id, chain_complete) VALUES (?, ?)",
        [("F3", 1), ("F3", 1), ("F3", 0), ("F7", 1), ("F7", 0)],
    )

    # exhibit_binders
    conn.execute(
        "CREATE TABLE exhibit_binders (id INTEGER PRIMARY KEY, filing_id TEXT, title TEXT)"
    )
    conn.executemany(
        "INSERT INTO exhibit_binders (filing_id, title) VALUES (?, ?)",
        [("F3", "Ex A"), ("F3", "Ex B"), ("F7", "Ex A")],
    )

    # irac_analysis
    conn.execute(
        "CREATE TABLE irac_analysis (id INTEGER PRIMARY KEY, filing_id TEXT, score REAL)"
    )
    conn.executemany(
        "INSERT INTO irac_analysis (filing_id, score) VALUES (?, ?)",
        [("F3", 8.5), ("F7", 7.0), ("F9", 6.5)],
    )

    # authority_chain_summary
    conn.execute(
        "CREATE TABLE authority_chain_summary (id INTEGER PRIMARY KEY, filing_id TEXT, score REAL)"
    )
    conn.executemany(
        "INSERT INTO authority_chain_summary (filing_id, score) VALUES (?, ?)",
        [("F3", 9.0), ("F7", 6.0)],
    )

    # filing_vulnerability_scores
    conn.execute(
        "CREATE TABLE filing_vulnerability_scores "
        "(id INTEGER PRIMARY KEY, filing_id TEXT, overall_vulnerability REAL)"
    )
    conn.executemany(
        "INSERT INTO filing_vulnerability_scores (filing_id, overall_vulnerability) VALUES (?, ?)",
        [("F3", 2.0), ("F7", 5.0), ("F9", 3.0)],
    )

    # deadlines
    today = date.today()
    conn.execute(
        "CREATE TABLE deadlines (id INTEGER PRIMARY KEY, due_date_iso TEXT, "
        "description TEXT, filing_id TEXT)"
    )
    conn.executemany(
        "INSERT INTO deadlines (due_date_iso, description, filing_id) VALUES (?, ?, ?)",
        [
            ((today + timedelta(days=3)).isoformat(), "COA brief due", "F9"),
            ((today + timedelta(days=15)).isoformat(), "Response deadline", "F3"),
            ((today + timedelta(days=60)).isoformat(), "MSC application window", "F5"),
        ],
    )

    # damages_calculation
    conn.execute(
        "CREATE TABLE damages_calculation "
        "(id INTEGER PRIMARY KEY, category TEXT, amount_low REAL, amount_high REAL)"
    )
    conn.executemany(
        "INSERT INTO damages_calculation (category, amount_low, amount_high) VALUES (?, ?, ?)",
        [("emotional", 25000, 75000), ("economic", 10000, 30000)],
    )

    # filing_fees
    conn.execute(
        "CREATE TABLE filing_fees "
        "(id INTEGER PRIMARY KEY, court TEXT, fee REAL, waived INTEGER)"
    )
    conn.executemany(
        "INSERT INTO filing_fees (court, fee, waived) VALUES (?, ?, ?)",
        [("14th Circuit", 175.0, 0), ("COA", 375.0, 1), ("Federal", 402.0, 0)],
    )

    # pipeline_runs
    conn.execute(
        "CREATE TABLE pipeline_runs (id INTEGER PRIMARY KEY, completed_at TEXT)"
    )
    conn.execute(
        "INSERT INTO pipeline_runs (completed_at) VALUES (?)",
        ("2025-07-10 14:30:00",),
    )

    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def dash_db(tmp_path: Path) -> Path:
    return _make_db(tmp_path)


@pytest.fixture
def engine(dash_db: Path) -> DashboardEngine:
    return DashboardEngine(db_path=dash_db)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSeparationDays:
    def test_returns_non_negative(self, engine: DashboardEngine):
        assert engine.get_separation_days() >= 0

    def test_correct_calculation(self):
        expected = (date.today() - SEPARATION_DATE).days
        eng = DashboardEngine.__new__(DashboardEngine)
        assert eng.get_separation_days() == max(expected, 0)


class TestEvidenceStats:
    def test_evidence_counts(self, engine: DashboardEngine):
        stats = engine.get_evidence_stats()
        assert stats["evidence_quotes"] == 25
        assert stats["citations"] == 12
        assert stats["impeachment_items"] == 8
        assert stats["bias_events"] == 5
        assert stats["alienation_events"] == 4

    def test_authority_chains(self, engine: DashboardEngine):
        stats = engine.get_evidence_stats()
        assert stats["total_chains"] == 5
        assert stats["complete_chains"] == 3

    def test_alienation_cumulative_days(self, engine: DashboardEngine):
        stats = engine.get_evidence_stats()
        # 10 + 11 + 12 + 13 = 46
        assert stats["alienation_cumulative_days"] == 46

    def test_exhibits(self, engine: DashboardEngine):
        stats = engine.get_evidence_stats()
        assert stats["exhibits"] == 3

    def test_irac_claims(self, engine: DashboardEngine):
        stats = engine.get_evidence_stats()
        assert stats["irac_claims"] == 3

    def test_missing_tables_return_zero(self, tmp_path: Path):
        db_path = tmp_path / "empty.db"
        sqlite3.connect(str(db_path)).close()
        eng = DashboardEngine(db_path=db_path)
        stats = eng.get_evidence_stats()
        assert stats["evidence_quotes"] == 0
        assert stats["complete_chains"] == 0


class TestFilingStatus:
    def test_returns_all_filings(self, engine: DashboardEngine):
        filings = engine.get_filing_status()
        ids = {f["filing_id"] for f in filings}
        assert ids == set(FILING_NAMES.keys())

    def test_f3_has_high_completeness(self, engine: DashboardEngine):
        filings = engine.get_filing_status()
        f3 = next(f for f in filings if f["filing_id"] == "F3")
        # vulnerability 2.0 → completeness (10-2)*10 = 80%
        assert f3["completeness_pct"] == 80.0
        assert f3["status"] == "REVIEW"

    def test_f3_authority_and_irac(self, engine: DashboardEngine):
        filings = engine.get_filing_status()
        f3 = next(f for f in filings if f["filing_id"] == "F3")
        assert f3["authority_strength"] == 9.0
        assert f3["irac_score"] == 8.5
        assert f3["exhibit_count"] == 2

    def test_unknown_filing_gets_defaults(self, engine: DashboardEngine):
        filings = engine.get_filing_status()
        f2 = next(f for f in filings if f["filing_id"] == "F2")
        assert f2["status"] == "DRAFT"
        assert f2["completeness_pct"] == 0.0

    def test_empty_db_returns_drafts(self, tmp_path: Path):
        db_path = tmp_path / "empty.db"
        sqlite3.connect(str(db_path)).close()
        eng = DashboardEngine(db_path=db_path)
        filings = eng.get_filing_status()
        assert all(f["status"] == "DRAFT" for f in filings)


class TestDeadlineUrgency:
    def test_returns_three_deadlines(self, engine: DashboardEngine):
        deadlines = engine.get_deadline_urgency()
        assert len(deadlines) == 3

    def test_urgency_colours(self, engine: DashboardEngine):
        deadlines = engine.get_deadline_urgency()
        urgencies = [d["urgency"] for d in deadlines]
        assert urgencies[0] == "RED"       # 3 days
        assert urgencies[1] == "YELLOW"    # 15 days
        assert urgencies[2] == "GREEN"     # 60 days

    def test_sorted_by_date(self, engine: DashboardEngine):
        deadlines = engine.get_deadline_urgency()
        dates = [d["due_date"] for d in deadlines]
        assert dates == sorted(dates)

    def test_no_deadlines_table(self, tmp_path: Path):
        db_path = tmp_path / "no_dl.db"
        sqlite3.connect(str(db_path)).close()
        eng = DashboardEngine(db_path=db_path)
        assert eng.get_deadline_urgency() == []


class TestFinancialSummary:
    def test_damages_range(self, engine: DashboardEngine):
        fin = engine.get_financial_summary()
        assert fin["damages_low"] == 35000.0
        assert fin["damages_high"] == 105000.0

    def test_filing_fees(self, engine: DashboardEngine):
        fin = engine.get_financial_summary()
        assert fin["filing_fees_total"] == 952.0   # 175 + 375 + 402

    def test_ifp_savings(self, engine: DashboardEngine):
        fin = engine.get_financial_summary()
        assert fin["ifp_savings"] == 375.0  # Only COA waived

    def test_empty_db(self, tmp_path: Path):
        db_path = tmp_path / "empty.db"
        sqlite3.connect(str(db_path)).close()
        eng = DashboardEngine(db_path=db_path)
        fin = eng.get_financial_summary()
        assert fin["damages_low"] == 0.0
        assert fin["filing_fees_total"] == 0.0


class TestLaneHealth:
    def test_all_lanes_present(self, engine: DashboardEngine):
        lanes = engine.get_lane_health()
        assert set(lanes.keys()) == set(LANE_REGISTRY.keys())

    def test_lane_a_has_filings(self, engine: DashboardEngine):
        lanes = engine.get_lane_health()
        assert lanes["A"]["filing_count"] == 3  # F1, F4, F7

    def test_lane_evidence_counts(self, engine: DashboardEngine):
        lanes = engine.get_lane_health()
        assert lanes["A"]["evidence_count"] == 10
        assert lanes["E"]["evidence_count"] == 10
        assert lanes["F"]["evidence_count"] == 5


class TestSystemHealth:
    def test_db_size_positive(self, engine: DashboardEngine):
        health = engine.get_system_health()
        assert health["db_size_mb"] > 0

    def test_table_count(self, engine: DashboardEngine):
        health = engine.get_system_health()
        assert health["table_count"] >= 10  # We created ~12 tables

    def test_last_pipeline_run(self, engine: DashboardEngine):
        health = engine.get_system_health()
        assert "2025-07-10" in health["last_pipeline_run"]


class TestCaseHealth:
    def test_returns_all_keys(self, engine: DashboardEngine):
        health = engine.get_case_health()
        expected_keys = {
            "separation_days", "active_lanes", "phase",
            "filings_total", "filings_ready", "filings_in_review",
            "filings_draft", "red_deadlines", "evidence", "financial", "system",
        }
        assert expected_keys.issubset(health.keys())

    def test_filings_total(self, engine: DashboardEngine):
        health = engine.get_case_health()
        assert health["filings_total"] == 10

    def test_active_lanes(self, engine: DashboardEngine):
        health = engine.get_case_health()
        assert health["active_lanes"] == 6

    def test_phase(self, engine: DashboardEngine):
        assert engine.get_case_health()["phase"] == "Filing Preparation"


class TestGenerateFullDashboard:
    def test_returns_markdown(self, engine: DashboardEngine):
        md = engine.generate_full_dashboard()
        assert md.startswith("# LitigationOS")

    def test_contains_all_sections(self, engine: DashboardEngine):
        md = engine.generate_full_dashboard()
        assert "## Case Header" in md
        assert "## Filing Readiness" in md
        assert "## Evidence Arsenal" in md
        assert "## Deadline Tracker" in md
        assert "## Financial Summary" in md
        assert "## Lane Health" in md
        assert "## System Health" in md

    def test_verified_party_names(self, engine: DashboardEngine):
        md = engine.generate_full_dashboard()
        assert "Andrew James Pigors" in md
        assert "Emily A. Watson" in md
        assert "L.D.W." in md

    def test_no_fabricated_names(self, engine: DashboardEngine):
        md = engine.generate_full_dashboard()
        assert "Jane Berry" not in md
        assert "Patricia Berry" not in md

    def test_filing_table_present(self, engine: DashboardEngine):
        md = engine.generate_full_dashboard()
        for fid in FILING_NAMES:
            assert fid in md

    def test_deadline_section_populated(self, engine: DashboardEngine):
        md = engine.generate_full_dashboard()
        assert "COA brief due" in md

    def test_financial_section(self, engine: DashboardEngine):
        md = engine.generate_full_dashboard()
        assert "$35,000.00" in md
        assert "$105,000.00" in md
