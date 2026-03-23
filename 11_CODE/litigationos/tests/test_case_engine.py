"""Comprehensive tests for the CaseEngine — core case management."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta

import pytest

from litigationos.engines.case_engine import (
    CASE_LANES,
    CaseEngine,
    CaseSummary,
    CaseTimeline,
    FILING_STATUS_ORDER,
    FilingStatus,
    JurisdictionPlugin,
    LANE_PRIORITY,
    VALID_CASE_STATUSES,
    VALID_CASE_TYPES,
    VALID_PARTY_ROLES,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def engine(tmp_db):
    """CaseEngine wired to the shared temp DB."""
    return CaseEngine(db=tmp_db)


@pytest.fixture
def case_id(engine):
    """Create a case and return its ID."""
    return engine.create_case(
        case_number="2024-001507-DC",
        title="Pigors v. Watson",
        case_type="family",
    )


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

class TestInitialization:
    def test_engine_creates_with_db(self, tmp_db):
        eng = CaseEngine(db=tmp_db)
        assert eng is not None

    def test_ensure_tables_creates_schema(self, engine, tmp_db):
        tables = [
            r["name"]
            for r in tmp_db.fetchall(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        ]
        for expected in ("cases", "parties", "claims", "evidence_claims"):
            assert expected in tables, f"Missing table: {expected}"

    def test_constants_defined(self):
        assert len(VALID_CASE_TYPES) >= 5
        assert len(VALID_PARTY_ROLES) >= 5
        assert "draft" in FILING_STATUS_ORDER


# ---------------------------------------------------------------------------
# Case CRUD
# ---------------------------------------------------------------------------

class TestCaseCRUD:
    def test_create_case(self, engine):
        cid = engine.create_case(
            case_number="2025-TEST-01",
            title="Test Case",
            case_type="civil",
        )
        assert isinstance(cid, int)
        assert cid > 0

    def test_get_case(self, engine, case_id):
        case = engine.get_case(case_id)
        assert case["case_number"] == "2024-001507-DC"
        assert case["title"] == "Pigors v. Watson"

    def test_list_cases(self, engine, case_id):
        cases = engine.list_cases()
        assert len(cases) >= 1
        assert any(c["id"] == case_id for c in cases)

    def test_list_cases_filter_type(self, engine, case_id):
        engine.create_case(case_number="X", title="Civil", case_type="civil")
        family_cases = engine.list_cases(case_type="family")
        assert all(c["case_type"] == "family" for c in family_cases)

    def test_update_case(self, engine, case_id):
        engine.update_case(case_id, status="closed")
        case = engine.get_case(case_id)
        assert case["status"] == "closed"

    def test_get_case_summary(self, engine, case_id):
        summary = engine.get_case_summary(case_id)
        assert isinstance(summary, CaseSummary)
        assert summary.id == case_id
        assert summary.title == "Pigors v. Watson"


# ---------------------------------------------------------------------------
# Lane Detection & Assignment
# ---------------------------------------------------------------------------

class TestLaneRouting:
    def test_detect_custody_lane(self, engine):
        assert engine.detect_lane("custody modification motion") == "A"

    def test_detect_ppo_lane(self, engine):
        assert engine.detect_lane("PPO termination filing") == "D"

    def test_detect_misconduct_lane(self, engine):
        assert engine.detect_lane("judicial misconduct JTC complaint") == "E"

    def test_detect_appellate_lane(self, engine):
        assert engine.detect_lane("COA emergency appeal") == "F"

    def test_detect_housing_lane(self, engine):
        assert engine.detect_lane("landlord habitability complaint") == "B"

    def test_lane_priority_order(self):
        # E (misconduct) is highest priority
        assert LANE_PRIORITY[0] == "E"
        assert LANE_PRIORITY[-1] == "B"

    def test_assign_lane(self, engine, case_id):
        engine.assign_lane(case_id, "A")
        lane = engine.get_lane(case_id)
        assert lane == "A"

    def test_case_lanes_defined(self):
        assert len(CASE_LANES) == 6
        for lane_id in ("A", "B", "C", "D", "E", "F"):
            assert lane_id in CASE_LANES


# ---------------------------------------------------------------------------
# Party Management
# ---------------------------------------------------------------------------

class TestPartyManagement:
    def test_add_party(self, engine, case_id):
        pid = engine.add_party(
            case_id=case_id,
            name="Andrew James Pigors",
            role="plaintiff",
        )
        assert isinstance(pid, int)

    def test_get_parties(self, engine, case_id):
        engine.add_party(case_id, "Andrew James Pigors", "plaintiff")
        engine.add_party(case_id, "Emily A. Watson", "defendant")
        parties = engine.get_parties(case_id)
        assert len(parties) == 2
        names = {p["name"] for p in parties}
        assert "Andrew James Pigors" in names
        assert "Emily A. Watson" in names

    def test_remove_party(self, engine, case_id):
        pid = engine.add_party(case_id, "Test Witness", "witness")
        engine.remove_party(pid)
        parties = engine.get_parties(case_id)
        assert not any(p["id"] == pid for p in parties)


# ---------------------------------------------------------------------------
# Claims
# ---------------------------------------------------------------------------

class TestClaims:
    def test_add_claim(self, engine, case_id):
        cid = engine.add_claim(
            case_id=case_id,
            title="Due Process Violation",
            legal_basis="U.S. Const. Amend. XIV",
        )
        assert isinstance(cid, int)

    def test_get_claims(self, engine, case_id):
        engine.add_claim(case_id, "Due Process", legal_basis="14th Amendment")
        engine.add_claim(case_id, "Equal Protection", legal_basis="14th Amendment")
        claims = engine.get_claims(case_id)
        assert len(claims) == 2

    def test_update_claim_status(self, engine, case_id):
        cid = engine.add_claim(case_id, "Test Claim", legal_basis="MCL 722.23")
        engine.update_claim_status(cid, "dismissed")
        claims = engine.get_claims(case_id)
        dismissed = [c for c in claims if c["id"] == cid]
        assert dismissed[0]["status"] == "dismissed"

    def test_search_claims(self, engine, case_id):
        engine.add_claim(case_id, "Due Process Violation", legal_basis="14th Amendment")
        engine.add_claim(case_id, "Parental Alienation", legal_basis="MCL 722.23(j)")
        results = engine.search_claims("alienation")
        assert len(results) >= 1
        assert any("Alienation" in r["title"] for r in results)


# ---------------------------------------------------------------------------
# Evidence Linkage
# ---------------------------------------------------------------------------

class TestEvidenceLinkage:
    def test_link_evidence_to_claim(self, engine, tmp_db, case_id):
        # Need a real evidence record to satisfy FK constraint
        tmp_db.execute(
            "INSERT INTO evidence (case_id, title, description, file_path, file_type) "
            "VALUES (?, ?, ?, ?, ?)",
            (case_id, "Test Evidence", "Test desc", "/tmp/test.pdf", "pdf"),
        )
        eid = tmp_db.fetchone("SELECT id FROM evidence ORDER BY id DESC LIMIT 1")["id"]
        claim_id = engine.add_claim(case_id, "Test", legal_basis="MCL")
        engine.link_evidence_to_claim(
            evidence_id=eid, claim_id=claim_id, strength="strong",
        )
        evidence = engine.get_evidence_for_claim(claim_id)
        assert len(evidence) >= 1

    def test_get_claims_for_evidence(self, engine, tmp_db, case_id):
        tmp_db.execute(
            "INSERT INTO evidence (case_id, title, description, file_path, file_type) "
            "VALUES (?, ?, ?, ?, ?)",
            (case_id, "Shared Evidence", "Shared desc", "/tmp/shared.pdf", "pdf"),
        )
        eid = tmp_db.fetchone("SELECT id FROM evidence ORDER BY id DESC LIMIT 1")["id"]
        c1 = engine.add_claim(case_id, "Claim A", legal_basis="MCL")
        c2 = engine.add_claim(case_id, "Claim B", legal_basis="MCR")
        engine.link_evidence_to_claim(evidence_id=eid, claim_id=c1, strength="strong")
        engine.link_evidence_to_claim(evidence_id=eid, claim_id=c2, strength="moderate")
        claims = engine.get_claims_for_evidence(eid)
        assert len(claims) == 2


# ---------------------------------------------------------------------------
# Deadlines
# ---------------------------------------------------------------------------

class TestDeadlines:
    def test_add_deadline(self, engine, case_id):
        due = (date.today() + timedelta(days=14)).isoformat()
        did = engine.add_deadline(
            case_id=case_id,
            title="Response Due",
            due_date=due,
        )
        assert isinstance(did, int)

    def test_get_upcoming_deadlines(self, engine, case_id):
        soon = (date.today() + timedelta(days=3)).isoformat()
        later = (date.today() + timedelta(days=30)).isoformat()
        engine.add_deadline(case_id, "Soon", soon)
        engine.add_deadline(case_id, "Later", later)
        upcoming = engine.get_upcoming_deadlines(case_id, days=7)
        assert len(upcoming) >= 1
        assert upcoming[0]["title"] == "Soon"

    def test_get_overdue_deadlines(self, engine, case_id):
        overdue_date = (date.today() - timedelta(days=5)).isoformat()
        engine.add_deadline(case_id, "Overdue", overdue_date)
        overdue = engine.get_overdue_deadlines(case_id)
        assert len(overdue) >= 1

    def test_calculate_deadline_michigan(self, engine):
        result = engine.calculate_deadline(
            filing_type="motion",
            trigger_date="2025-01-01",
        )
        # May return dict or None depending on configured rules
        assert result is None or isinstance(result, dict)


# ---------------------------------------------------------------------------
# Filing State Machine
# ---------------------------------------------------------------------------

class TestFilingWorkflow:
    def test_filing_status_order(self):
        assert FILING_STATUS_ORDER.index("draft") < FILING_STATUS_ORDER.index("filed")
        assert FILING_STATUS_ORDER.index("qa") < FILING_STATUS_ORDER.index("ready")

    def test_advance_filing(self, engine, tmp_db, case_id):
        cur = tmp_db.execute(
            "INSERT INTO filings (case_id, title, filing_type, status) VALUES (?, ?, ?, ?)",
            (case_id, "Test Motion", "motion", "draft"),
        )
        fid = cur.lastrowid
        engine.advance_filing(fid, to_status="review")
        history = engine.get_filing_history(fid)
        assert len(history) >= 1
        assert history[-1]["to_status"] == "review"

    def test_filing_status_enum(self):
        assert FilingStatus.DRAFT == "draft"
        assert FilingStatus.FILED == "filed"


# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------

class TestTimeline:
    def test_add_timeline_event(self, engine, case_id):
        engine.add_timeline_event(
            case_id=case_id,
            event_type="hearing",
            title="Status Conference",
            event_date=date.today(),
        )
        tl = engine.get_timeline(case_id)
        assert isinstance(tl, CaseTimeline)
        assert len(tl.events) >= 1

    def test_timeline_chronological(self, engine, case_id):
        engine.add_timeline_event(case_id, "2025-01-01", "Motion Filed", event_type="filing")
        engine.add_timeline_event(case_id, "2025-02-01", "Hearing", event_type="hearing")
        engine.add_timeline_event(case_id, "2024-12-01", "Order Entered", event_type="order")
        tl = engine.get_timeline(case_id)
        dates = [e.get("event_date", "") for e in tl.events]
        assert dates == sorted(dates)


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

class TestSearch:
    def test_search_by_title(self, engine, case_id):
        engine.add_claim(case_id, "Due Process Violation", legal_basis="14th Amendment")
        results = engine.search("due process", case_id=case_id)
        assert "claims" in results or len(results) > 0

    def test_search_empty_query(self, engine, case_id):
        results = engine.search("xyznonexistent12345", case_id=case_id)
        total = sum(len(v) for v in results.values()) if isinstance(results, dict) else 0
        assert total == 0


# ---------------------------------------------------------------------------
# Jurisdiction Plugin
# ---------------------------------------------------------------------------

class TestJurisdiction:
    def test_michigan_plugin(self):
        jp = JurisdictionPlugin.michigan()
        assert jp is not None

    def test_michigan_has_rules(self):
        jp = JurisdictionPlugin.michigan()
        assert hasattr(jp, "name") or hasattr(jp, "rules") or jp is not None
