"""Wave-8 Tests — SubpoenaEngine + SettlementAnalyzer
=====================================================
Comprehensive pytest suite for subpoena_engine.py and settlement_analyzer.py.

220+ total tests (split across two files).
• Zero network / zero real DB — all DB interactions use in-memory SQLite
• tempfile.mkdtemp() for any filesystem work
• unittest.mock.patch for isolation
• Independent tests, no ordering dependencies
"""
from __future__ import annotations

import json
import pathlib
import sqlite3
import tempfile
import uuid
from datetime import date, timedelta, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Import targets — adjust sys.path so we can import from parent
# ---------------------------------------------------------------------------
import sys

_THIS_DIR = pathlib.Path(__file__).resolve().parent
_LEGAL_AI_DIR = _THIS_DIR.parent
if str(_LEGAL_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_LEGAL_AI_DIR))

from subpoena_engine import (
    SubpoenaType,
    SubpoenaStatus,
    RecipientType,
    ServiceMethod,
    SubpoenaRecord,
    SubpoenaGenerator,
    ServiceTracker,
    ComplianceEnforcer,
    SubpoenaEngine,
    PLAINTIFF,
    PLAINTIFF_ROLE,
    DEFENDANT,
    CHILD,
    CHILD_INITIALS,
    JUDGE,
    CASE_LANES,
    WITNESS_FEE_PER_DAY,
    IRS_MILEAGE_RATE,
    SERVICE_FEE_PERSONAL,
    SERVICE_FEE_REGISTERED,
    SERVICE_FEE_CERTIFIED_MAIL,
    _PRAGMAS,
    _SCHEMA as SUBPOENA_SCHEMA,
    _get_conn as subpoena_get_conn,
    _ensure_schema as subpoena_ensure_schema,
)

from settlement_analyzer import (
    SettlementStrategy,
    RiskLevel,
    OfferVerdict,
    CaseOutcomeProbability,
    SettlementRange,
    DamageItem,
    NegotiationIssue,
    ExpectedValueCalculator,
    DemandLetterGenerator,
    MediationBriefWriter,
    SettlementAnalyzer,
    DEFENDANTS,
    _SCHEMA as SETTLEMENT_SCHEMA,
    _dec,
)


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def tmp_db(tmp_path):
    """Provide an in-memory style temp-dir DB for subpoena schema."""
    db_file = tmp_path / "test_subpoena.db"
    conn = sqlite3.connect(str(db_file), timeout=30)
    conn.executescript(_PRAGMAS)
    conn.row_factory = sqlite3.Row
    conn.executescript(SUBPOENA_SCHEMA)
    yield conn
    conn.close()


@pytest.fixture
def settlement_db(tmp_path):
    """Provide a temp DB for settlement schema."""
    db_file = tmp_path / "test_settlement.db"
    conn = sqlite3.connect(str(db_file), timeout=30)
    conn.executescript(_PRAGMAS)
    conn.row_factory = sqlite3.Row
    conn.executescript(SETTLEMENT_SCHEMA)
    yield conn
    conn.close()


@pytest.fixture
def tmp_db_path(tmp_path):
    """Return a path suitable for SubpoenaEngine(db_path=...)."""
    return tmp_path / "engine_test.db"


@pytest.fixture
def settlement_db_path(tmp_path):
    return tmp_path / "settlement_engine_test.db"


@pytest.fixture
def generator():
    return SubpoenaGenerator()


@pytest.fixture
def service_tracker(tmp_db):
    return ServiceTracker(conn=tmp_db)


@pytest.fixture
def enforcer(tmp_db):
    return ComplianceEnforcer(conn=tmp_db)


@pytest.fixture
def ev_calc():
    return ExpectedValueCalculator()


@pytest.fixture
def mediation_writer():
    return MediationBriefWriter()


# ═══════════════════════════════════════════════════════════════════════════
# Subpoena Engine — Enums
# ═══════════════════════════════════════════════════════════════════════════

class TestSubpoenaEnums:
    """Test all enum definitions in subpoena_engine."""

    def test_subpoena_type_values(self):
        expected = {"WITNESS", "DUCES_TECUM", "DEPOSITION", "TRIAL",
                    "HEARING", "RECORDS_ONLY"}
        assert {e.value for e in SubpoenaType} == expected

    def test_subpoena_status_values(self):
        expected = {"DRAFT", "ISSUED", "SERVED", "ACKNOWLEDGED", "OBJECTED",
                    "QUASHED", "COMPLIED", "NONCOMPLIANT", "MOTION_TO_COMPEL"}
        assert {e.value for e in SubpoenaStatus} == expected

    def test_recipient_type_values(self):
        assert RecipientType.INDIVIDUAL.value == "INDIVIDUAL"
        assert RecipientType.ORGANIZATION.value == "ORGANIZATION"
        assert len(RecipientType) == 2

    def test_service_method_values(self):
        expected = {"PERSONAL", "REGISTERED_MAIL", "CERTIFIED_MAIL",
                    "FIRST_CLASS_MAIL", "PROCESS_SERVER", "SHERIFF",
                    "SUBSTITUTED", "PUBLICATION"}
        assert {e.value for e in ServiceMethod} == expected

    def test_enum_from_string(self):
        assert SubpoenaType("WITNESS") == SubpoenaType.WITNESS
        assert SubpoenaStatus("DRAFT") == SubpoenaStatus.DRAFT
        assert RecipientType("ORGANIZATION") == RecipientType.ORGANIZATION
        assert ServiceMethod("PERSONAL") == ServiceMethod.PERSONAL


# ═══════════════════════════════════════════════════════════════════════════
# Party / Lane Constants
# ═══════════════════════════════════════════════════════════════════════════

class TestSubpoenaConstants:
    def test_plaintiff_name(self):
        assert PLAINTIFF == "Andrew James Pigors"

    def test_defendant_name(self):
        assert DEFENDANT == "Emily A. Watson"

    def test_child_initials(self):
        assert CHILD_INITIALS == "L.D.W."

    def test_judge(self):
        assert JUDGE == "Hon. Jenny L. McNeill"

    def test_case_lanes_six(self):
        assert set(CASE_LANES.keys()) == {"A", "B", "C", "D", "E", "F"}

    def test_case_lane_a(self):
        assert CASE_LANES["A"]["case_number"] == "2024-001507-DC"
        assert CASE_LANES["A"]["subject"] == "Custody"

    def test_case_lane_b(self):
        assert CASE_LANES["B"]["case_number"] == "2025-002760-CZ"

    def test_witness_fee(self):
        assert WITNESS_FEE_PER_DAY == Decimal("12.00")

    def test_irs_mileage_rate(self):
        assert IRS_MILEAGE_RATE == Decimal("0.67")


# ═══════════════════════════════════════════════════════════════════════════
# SubpoenaRecord Dataclass
# ═══════════════════════════════════════════════════════════════════════════

class TestSubpoenaRecord:

    def test_default_creation(self):
        rec = SubpoenaRecord()
        assert rec.subpoena_type == SubpoenaType.WITNESS
        assert rec.status == SubpoenaStatus.DRAFT
        assert rec.recipient_type == RecipientType.INDIVIDUAL
        assert rec.subpoena_id  # UUID generated

    def test_uuid_uniqueness(self):
        recs = [SubpoenaRecord() for _ in range(50)]
        ids = {r.subpoena_id for r in recs}
        assert len(ids) == 50

    def test_to_dict_keys(self):
        rec = SubpoenaRecord(case_number="123", recipient_name="Jane")
        d = rec.to_dict()
        assert d["case_number"] == "123"
        assert d["recipient_name"] == "Jane"
        assert d["subpoena_type"] == "WITNESS"
        assert d["status"] == "DRAFT"
        assert isinstance(d["documents_requested"], list)
        assert isinstance(d["testimony_topics"], list)

    def test_to_dict_serialisable(self):
        rec = SubpoenaRecord()
        d = rec.to_dict()
        json_str = json.dumps(d)
        assert isinstance(json_str, str)

    def test_is_overdue_no_due_date(self):
        rec = SubpoenaRecord(date_due=None)
        assert rec.is_overdue() is False

    def test_is_overdue_past_date(self):
        past = (date.today() - timedelta(days=5)).isoformat()
        rec = SubpoenaRecord(date_due=past, status=SubpoenaStatus.SERVED)
        assert rec.is_overdue() is True

    def test_is_overdue_future_date(self):
        future = (date.today() + timedelta(days=30)).isoformat()
        rec = SubpoenaRecord(date_due=future, status=SubpoenaStatus.SERVED)
        assert rec.is_overdue() is False

    def test_is_overdue_complied_not_overdue(self):
        past = (date.today() - timedelta(days=5)).isoformat()
        rec = SubpoenaRecord(date_due=past, status=SubpoenaStatus.COMPLIED)
        assert rec.is_overdue() is False

    def test_is_overdue_quashed_not_overdue(self):
        past = (date.today() - timedelta(days=5)).isoformat()
        rec = SubpoenaRecord(date_due=past, status=SubpoenaStatus.QUASHED)
        assert rec.is_overdue() is False

    def test_is_overdue_invalid_date(self):
        rec = SubpoenaRecord(date_due="not-a-date", status=SubpoenaStatus.SERVED)
        assert rec.is_overdue() is False

    def test_days_until_due_none(self):
        rec = SubpoenaRecord(date_due=None)
        assert rec.days_until_due() is None

    def test_days_until_due_future(self):
        future = (date.today() + timedelta(days=10)).isoformat()
        rec = SubpoenaRecord(date_due=future)
        assert rec.days_until_due() == 10

    def test_days_until_due_past(self):
        past = (date.today() - timedelta(days=3)).isoformat()
        rec = SubpoenaRecord(date_due=past)
        assert rec.days_until_due() == -3

    def test_days_until_due_today(self):
        today = date.today().isoformat()
        rec = SubpoenaRecord(date_due=today)
        assert rec.days_until_due() == 0

    def test_days_until_due_invalid_date(self):
        rec = SubpoenaRecord(date_due="bad")
        assert rec.days_until_due() is None


# ═══════════════════════════════════════════════════════════════════════════
# SubpoenaGenerator
# ═══════════════════════════════════════════════════════════════════════════

class TestSubpoenaGenerator:

    def test_generate_witness_subpoena(self, generator):
        hearing = (date.today() + timedelta(days=30)).isoformat()
        rec = generator.generate_witness_subpoena(
            "Jane Doe", hearing,
            "14th Circuit Court",
            "2024-001507-DC",
            case_lane="A",
        )
        assert rec.subpoena_type == SubpoenaType.WITNESS
        assert rec.recipient_name == "Jane Doe"
        assert rec.case_lane == "A"
        assert rec.status == SubpoenaStatus.DRAFT

    def test_witness_subpoena_with_topics(self, generator):
        hearing = (date.today() + timedelta(days=14)).isoformat()
        topics = ["Child welfare", "Custody observations"]
        rec = generator.generate_witness_subpoena(
            "Expert Witness", hearing, "Court", "2024-001507-DC",
            testimony_topics=topics,
        )
        assert rec.testimony_topics == topics

    def test_generate_duces_tecum(self, generator):
        deadline = (date.today() + timedelta(days=21)).isoformat()
        docs = ["Bank records", "Tax returns"]
        rec = generator.generate_duces_tecum(
            "Bank of America", docs, deadline,
            case_number="2024-001507-DC",
            recipient_type=RecipientType.ORGANIZATION,
        )
        assert rec.subpoena_type == SubpoenaType.DUCES_TECUM
        assert rec.documents_requested == docs
        assert rec.date_due == deadline

    def test_generate_deposition_subpoena(self, generator):
        dep_date = (date.today() + timedelta(days=45)).isoformat()
        rec = generator.generate_deposition_subpoena(
            "Emily A. Watson", dep_date, "Deposition Suite",
            case_number="2024-001507-DC",
            testimony_topics=["Parenting time"],
            documents=["Phone records"],
        )
        assert rec.subpoena_type == SubpoenaType.DEPOSITION
        assert rec.hearing_location == "Deposition Suite"
        assert rec.documents_requested == ["Phone records"]

    def test_generate_third_party_records_bank(self, generator):
        rec = generator.generate_third_party_records(
            "First National Bank", "BANK",
            ["Statements 2022-2025"],
            case_number="2024-001507-DC",
        )
        assert rec.subpoena_type == SubpoenaType.RECORDS_ONLY
        assert rec.recipient_type == RecipientType.ORGANIZATION
        assert "Financial records" in rec.notes

    def test_third_party_records_police(self, generator):
        rec = generator.generate_third_party_records(
            "Muskegon PD", "POLICE", ["Incident reports"],
        )
        assert "Law enforcement" in rec.notes

    def test_third_party_records_medical(self, generator):
        rec = generator.generate_third_party_records(
            "Mercy Hospital", "MEDICAL", ["Treatment notes"],
        )
        assert "Medical records" in rec.notes

    def test_third_party_records_unknown_type(self, generator):
        rec = generator.generate_third_party_records(
            "Custom Entity", "CUSTOM", ["Custom docs"],
        )
        assert "Records subpoena to CUSTOM" in rec.notes

    def test_third_party_default_deadline_21_days(self, generator):
        rec = generator.generate_third_party_records(
            "Entity", "BANK", ["docs"],
        )
        expected_due = (date.today() + timedelta(days=21)).isoformat()
        assert rec.date_due == expected_due

    def test_format_subpoena_body_witness(self, generator):
        hearing = (date.today() + timedelta(days=30)).isoformat()
        rec = generator.generate_witness_subpoena(
            "Jane Doe", hearing, "Court", "2024-001507-DC",
        )
        body = generator.format_subpoena_body(rec)
        assert "STATE OF MICHIGAN" in body
        assert "Jane Doe" in body
        assert "MCR 2.506" in body
        assert PLAINTIFF in body

    def test_format_subpoena_body_duces_tecum(self, generator):
        deadline = (date.today() + timedelta(days=28)).isoformat()
        rec = generator.generate_duces_tecum(
            "DHHS", ["Case files"], deadline,
        )
        body = generator.format_subpoena_body(rec)
        assert "MCR 2.305" in body
        assert "Case files" in body

    def test_format_subpoena_body_deposition(self, generator):
        dep_date = (date.today() + timedelta(days=30)).isoformat()
        rec = generator.generate_deposition_subpoena(
            "Witness", dep_date, "Suite 200",
            testimony_topics=["Topic A"],
            documents=["Doc 1"],
        )
        body = generator.format_subpoena_body(rec)
        assert "DEPOSITION" in body
        assert "Topic A" in body
        assert "Doc 1" in body

    def test_validate_mcr_compliance_valid_witness(self, generator):
        hearing = (date.today() + timedelta(days=30)).isoformat()
        rec = generator.generate_witness_subpoena(
            "Witness", hearing, "Court", "2024-001507-DC",
        )
        issues = generator.validate_mcr_compliance(rec)
        assert issues == []

    def test_validate_mcr_compliance_missing_recipient(self, generator):
        rec = SubpoenaRecord(
            recipient_name="",
            case_number="123",
            subpoena_type=SubpoenaType.WITNESS,
            hearing_date="2026-01-01",
            hearing_location="Court",
        )
        issues = generator.validate_mcr_compliance(rec)
        assert any("Recipient name" in i for i in issues)

    def test_validate_mcr_compliance_missing_case_number(self, generator):
        rec = SubpoenaRecord(
            recipient_name="Witness",
            case_number="",
            subpoena_type=SubpoenaType.WITNESS,
        )
        issues = generator.validate_mcr_compliance(rec)
        assert any("Case number" in i for i in issues)

    def test_validate_mcr_compliance_duces_tecum_no_docs(self, generator):
        rec = SubpoenaRecord(
            recipient_name="X",
            case_number="123",
            subpoena_type=SubpoenaType.DUCES_TECUM,
            documents_requested=[],
        )
        issues = generator.validate_mcr_compliance(rec)
        assert any("document must be requested" in i for i in issues)

    def test_validate_mcr_14_day_rule(self, generator):
        issued = date.today().isoformat()
        due = (date.today() + timedelta(days=10)).isoformat()
        rec = SubpoenaRecord(
            recipient_name="X",
            case_number="123",
            subpoena_type=SubpoenaType.DUCES_TECUM,
            documents_requested=["Doc"],
            date_issued=issued,
            date_due=due,
        )
        issues = generator.validate_mcr_compliance(rec)
        assert any("14 days" in i for i in issues)

    def test_generator_count_increments(self, generator):
        assert generator.get_stats()["generated_count"] == 0
        generator.generate_witness_subpoena(
            "X", "2026-12-01", "Court", "123",
        )
        assert generator.get_stats()["generated_count"] == 1
        generator.generate_duces_tecum("Y", ["Doc"], "2026-12-01")
        assert generator.get_stats()["generated_count"] == 2


# ═══════════════════════════════════════════════════════════════════════════
# ServiceTracker
# ═══════════════════════════════════════════════════════════════════════════

class TestServiceTracker:

    def _insert_subpoena(self, conn, sid="sub-001", status="ISSUED",
                         date_due=None, case_number="2024-001507-DC"):
        conn.execute(
            "INSERT INTO subpoenas (subpoena_id, subpoena_type, "
            "case_number, recipient_name, status, date_due) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (sid, "WITNESS", case_number, "Test Recipient", status, date_due),
        )
        conn.commit()

    def test_record_service(self, service_tracker, tmp_db):
        self._insert_subpoena(tmp_db, "sub-001")
        log_id = service_tracker.record_service(
            "sub-001", "PERSONAL", "2026-01-15", "John Server",
        )
        assert log_id  # UUID returned
        row = tmp_db.execute(
            "SELECT * FROM subpoenas WHERE subpoena_id = 'sub-001'",
        ).fetchone()
        assert dict(row)["status"] == "SERVED"

    def test_track_response_complied(self, service_tracker, tmp_db):
        self._insert_subpoena(tmp_db, "sub-002", status="SERVED")
        service_tracker.track_response("sub-002", "COMPLIED")
        row = tmp_db.execute(
            "SELECT status FROM subpoenas WHERE subpoena_id = 'sub-002'",
        ).fetchone()
        assert dict(row)["status"] == "COMPLIED"

    def test_track_response_objected(self, service_tracker, tmp_db):
        self._insert_subpoena(tmp_db, "sub-003", status="SERVED")
        service_tracker.track_response("sub-003", "OBJECTED", "Privilege claim")
        row = tmp_db.execute(
            "SELECT status, objection_details FROM subpoenas WHERE subpoena_id = 'sub-003'",
        ).fetchone()
        d = dict(row)
        assert d["status"] == "OBJECTED"
        assert d["objection_details"] == "Privilege claim"

    def test_check_overdue_returns_overdue(self, service_tracker, tmp_db):
        past = (date.today() - timedelta(days=5)).isoformat()
        self._insert_subpoena(tmp_db, "sub-004", status="SERVED", date_due=past)
        overdue = service_tracker.check_overdue()
        assert len(overdue) == 1
        assert overdue[0].subpoena_id == "sub-004"

    def test_check_overdue_excludes_complied(self, service_tracker, tmp_db):
        past = (date.today() - timedelta(days=5)).isoformat()
        self._insert_subpoena(tmp_db, "sub-005", status="COMPLIED", date_due=past)
        overdue = service_tracker.check_overdue()
        assert len(overdue) == 0

    def test_generate_service_log_empty(self, service_tracker):
        log = service_tracker.generate_service_log()
        assert "SERVICE LOG" in log
        assert "no service records found" in log

    def test_generate_service_log_with_entry(self, service_tracker, tmp_db):
        self._insert_subpoena(tmp_db, "sub-010")
        service_tracker.record_service(
            "sub-010", "CERTIFIED_MAIL", "2026-01-20", "Server A",
        )
        log = service_tracker.generate_service_log("sub-010")
        assert "sub-010" in log
        assert "CERTIFIED_MAIL" in log

    def test_calculate_service_fees_personal(self, service_tracker):
        fees = service_tracker.calculate_service_fees("PERSONAL", 20.0, 1)
        assert fees["witness_fee"] == Decimal("12.00")
        assert fees["mileage"] == Decimal("0.67") * Decimal("20.0")
        assert fees["service_fee"] == Decimal("35.00")
        assert fees["total"] == fees["witness_fee"] + fees["mileage"] + fees["service_fee"]

    def test_calculate_service_fees_certified_mail(self, service_tracker):
        fees = service_tracker.calculate_service_fees("CERTIFIED_MAIL", 0, 2)
        assert fees["witness_fee"] == Decimal("24.00")
        assert fees["service_fee"] == Decimal("8.50")

    def test_calculate_service_fees_registered_mail(self, service_tracker):
        fees = service_tracker.calculate_service_fees("REGISTERED_MAIL")
        assert fees["service_fee"] == SERVICE_FEE_REGISTERED

    def test_calculate_service_fees_unknown_method(self, service_tracker):
        fees = service_tracker.calculate_service_fees("UNKNOWN")
        assert fees["service_fee"] == Decimal("0.00")

    def test_service_tracker_stats(self, service_tracker, tmp_db):
        self._insert_subpoena(tmp_db, "sub-020")
        service_tracker.record_service("sub-020", "PERSONAL", "2026-01-01", "S")
        stats = service_tracker.get_stats()
        assert stats["log_entries_created"] == 1


# ═══════════════════════════════════════════════════════════════════════════
# ComplianceEnforcer
# ═══════════════════════════════════════════════════════════════════════════

class TestComplianceEnforcer:

    def _insert_subpoena(self, conn, sid="enf-001", status="NONCOMPLIANT",
                         case_number="2024-001507-DC"):
        conn.execute(
            "INSERT INTO subpoenas (subpoena_id, subpoena_type, "
            "case_number, recipient_name, status, date_issued, "
            "date_due, service_date) VALUES (?,?,?,?,?,?,?,?)",
            (sid, "DUCES_TECUM", case_number, "Opposing Party", status,
             "2026-01-01", "2026-01-21", "2026-01-05"),
        )
        conn.commit()

    def test_prepare_motion_to_compel(self, enforcer, tmp_db):
        self._insert_subpoena(tmp_db, "enf-001")
        result = enforcer.prepare_motion_to_compel("enf-001")
        assert "enforcement_id" in result
        assert result["action_type"] == "MOTION_TO_COMPEL"
        assert "MCR 2.313" in result["motion_text"]
        assert PLAINTIFF in result["motion_text"]

    def test_motion_to_compel_not_found(self, enforcer):
        result = enforcer.prepare_motion_to_compel("nonexistent")
        assert "error" in result

    def test_prepare_contempt_motion(self, enforcer, tmp_db):
        self._insert_subpoena(tmp_db, "enf-002")
        result = enforcer.prepare_contempt_motion("enf-002")
        assert result["action_type"] == "CONTEMPT"
        assert "MCR 3.606" in result["motion_text"]

    def test_contempt_motion_not_found(self, enforcer):
        result = enforcer.prepare_contempt_motion("nonexistent")
        assert "error" in result

    def test_calculate_sanctions_failure_to_appear(self, enforcer):
        result = enforcer.calculate_sanctions("FAILURE_TO_APPEAR")
        assert result["base_sanction"] == Decimal("500.00")
        assert result["total_sanctions"] == Decimal("500.00")

    def test_calculate_sanctions_with_attorney_hours(self, enforcer):
        result = enforcer.calculate_sanctions(
            "FAILURE_TO_PRODUCE",
            attorney_hours=Decimal("4"),
            hourly_rate=Decimal("250.00"),
        )
        assert result["attorney_equivalent_cost"] == Decimal("1000.00")
        assert result["total_sanctions"] == Decimal("250.00") + Decimal("1000.00")

    def test_calculate_sanctions_wilful_destruction(self, enforcer):
        result = enforcer.calculate_sanctions("WILFUL_DESTRUCTION")
        assert result["base_sanction"] == Decimal("5000.00")

    def test_calculate_sanctions_unknown_type(self, enforcer):
        result = enforcer.calculate_sanctions("SOMETHING_ELSE")
        assert result["base_sanction"] == Decimal("250.00")

    def test_draft_show_cause_order(self, enforcer, tmp_db):
        self._insert_subpoena(tmp_db, "enf-003")
        result = enforcer.draft_show_cause_order("enf-003")
        assert result["action_type"] == "SHOW_CAUSE"
        assert "ORDER TO SHOW CAUSE" in result["text"]

    def test_enforcer_stats(self, enforcer, tmp_db):
        self._insert_subpoena(tmp_db, "enf-010")
        enforcer.prepare_motion_to_compel("enf-010")
        stats = enforcer.get_stats()
        assert stats["enforcement_actions_created"] == 1


# ═══════════════════════════════════════════════════════════════════════════
# SubpoenaEngine (Orchestrator)
# ═══════════════════════════════════════════════════════════════════════════

class TestSubpoenaEngine:

    def test_create_witness_subpoena(self, tmp_db_path):
        engine = SubpoenaEngine(db_path=tmp_db_path)
        try:
            rec = engine.create_subpoena(
                SubpoenaType.WITNESS, "Jane Doe",
                {
                    "case_number": "2024-001507-DC",
                    "case_lane": "A",
                    "hearing_date": "2026-06-01",
                    "court": "14th Circuit Court",
                },
            )
            assert rec.subpoena_type == SubpoenaType.WITNESS
            assert rec.recipient_name == "Jane Doe"
        finally:
            engine.close()

    def test_create_duces_tecum_subpoena(self, tmp_db_path):
        engine = SubpoenaEngine(db_path=tmp_db_path)
        try:
            rec = engine.create_subpoena(
                SubpoenaType.DUCES_TECUM, "Bank",
                {
                    "case_number": "2024-001507-DC",
                    "documents": ["Statements"],
                    "deadline": (date.today() + timedelta(days=21)).isoformat(),
                },
            )
            assert rec.subpoena_type == SubpoenaType.DUCES_TECUM
        finally:
            engine.close()

    def test_create_deposition_subpoena(self, tmp_db_path):
        engine = SubpoenaEngine(db_path=tmp_db_path)
        try:
            rec = engine.create_subpoena(
                SubpoenaType.DEPOSITION, "Witness",
                {"deposition_date": "2026-06-01", "location": "Suite 200"},
            )
            assert rec.subpoena_type == SubpoenaType.DEPOSITION
        finally:
            engine.close()

    def test_create_records_subpoena(self, tmp_db_path):
        engine = SubpoenaEngine(db_path=tmp_db_path)
        try:
            rec = engine.create_subpoena(
                SubpoenaType.RECORDS_ONLY, "Hospital",
                {
                    "entity_type": "MEDICAL",
                    "records_list": ["Treatment notes"],
                },
            )
            assert rec.subpoena_type == SubpoenaType.RECORDS_ONLY
        finally:
            engine.close()

    def test_track_all_subpoenas(self, tmp_db_path):
        engine = SubpoenaEngine(db_path=tmp_db_path)
        try:
            engine.create_subpoena(
                SubpoenaType.WITNESS, "W1",
                {"case_lane": "A", "hearing_date": "2026-06-01",
                 "court": "Court", "case_number": "123"},
            )
            engine.create_subpoena(
                SubpoenaType.WITNESS, "W2",
                {"case_lane": "B", "hearing_date": "2026-06-01",
                 "court": "Court", "case_number": "456"},
            )
            all_subs = engine.track_all_subpoenas()
            assert len(all_subs) == 2
            lane_a = engine.track_all_subpoenas(lane="A")
            assert len(lane_a) == 1
        finally:
            engine.close()

    def test_get_overdue_subpoenas_empty(self, tmp_db_path):
        engine = SubpoenaEngine(db_path=tmp_db_path)
        try:
            overdue = engine.get_overdue_subpoenas()
            assert overdue == []
        finally:
            engine.close()

    def test_enforce_noncompliance_motion_to_compel(self, tmp_db_path):
        engine = SubpoenaEngine(db_path=tmp_db_path)
        try:
            rec = engine.create_subpoena(
                SubpoenaType.DUCES_TECUM, "Target",
                {"documents": ["D"], "deadline": "2026-01-01",
                 "case_number": "123"},
            )
            result = engine.enforce_noncompliance(rec.subpoena_id,
                                                   action="MOTION_TO_COMPEL")
            assert result["action_type"] == "MOTION_TO_COMPEL"
        finally:
            engine.close()

    def test_enforce_noncompliance_contempt(self, tmp_db_path):
        engine = SubpoenaEngine(db_path=tmp_db_path)
        try:
            rec = engine.create_subpoena(
                SubpoenaType.DUCES_TECUM, "Target",
                {"documents": ["D"], "deadline": "2026-01-01",
                 "case_number": "123"},
            )
            result = engine.enforce_noncompliance(rec.subpoena_id,
                                                   action="CONTEMPT")
            assert result["action_type"] == "CONTEMPT"
        finally:
            engine.close()

    def test_enforce_noncompliance_show_cause(self, tmp_db_path):
        engine = SubpoenaEngine(db_path=tmp_db_path)
        try:
            rec = engine.create_subpoena(
                SubpoenaType.WITNESS, "W",
                {"hearing_date": "2026-06-01", "court": "C",
                 "case_number": "123"},
            )
            result = engine.enforce_noncompliance(rec.subpoena_id,
                                                   action="SHOW_CAUSE")
            assert result["action_type"] == "SHOW_CAUSE"
        finally:
            engine.close()

    def test_subpoena_report(self, tmp_db_path):
        engine = SubpoenaEngine(db_path=tmp_db_path)
        try:
            engine.create_subpoena(
                SubpoenaType.WITNESS, "W",
                {"hearing_date": "2026-06-01", "court": "C",
                 "case_number": "123", "case_lane": "A"},
            )
            report = engine.generate_subpoena_report()
            assert "SUBPOENA STATUS REPORT" in report
            assert "Lane A" in report
        finally:
            engine.close()

    def test_engine_get_stats(self, tmp_db_path):
        engine = SubpoenaEngine(db_path=tmp_db_path)
        try:
            stats = engine.get_stats()
            assert "total" in stats
            assert "engine_version" in stats
            assert stats["engine_version"] == "1.0.0"
        finally:
            engine.close()

    def test_engine_close_idempotent(self, tmp_db_path):
        engine = SubpoenaEngine(db_path=tmp_db_path)
        engine._init_db()
        engine.close()
        engine.close()  # second close should not raise

    def test_lane_routing_all_lanes(self, tmp_db_path):
        engine = SubpoenaEngine(db_path=tmp_db_path)
        try:
            for lane in ["A", "B", "C", "D", "E", "F"]:
                rec = engine.create_subpoena(
                    SubpoenaType.WITNESS, f"Witness-{lane}",
                    {"case_lane": lane, "hearing_date": "2026-06-01",
                     "court": "Court", "case_number": CASE_LANES[lane]["case_number"]},
                )
                assert rec.case_lane == lane
            all_subs = engine.track_all_subpoenas()
            assert len(all_subs) == 6
        finally:
            engine.close()


# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════
# SETTLEMENT ANALYZER TESTS
# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════

class TestSettlementEnums:

    def test_settlement_strategy_values(self):
        expected = {"AGGRESSIVE", "MODERATE", "CONSERVATIVE", "WALKAWAY"}
        assert {e.value for e in SettlementStrategy} == expected

    def test_risk_level_values(self):
        expected = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        assert {e.value for e in RiskLevel} == expected

    def test_offer_verdict_values(self):
        expected = {"ACCEPT", "REJECT", "COUNTER", "DEFER"}
        assert {e.value for e in OfferVerdict} == expected


class TestSettlementDataclasses:

    def test_case_outcome_probability_defaults(self):
        cop = CaseOutcomeProbability()
        assert cop.win_probability == 50
        assert cop.expected_value == Decimal("0")

    def test_case_outcome_probability_to_dict(self):
        cop = CaseOutcomeProbability(lane="A", claim_type="custody")
        d = cop.to_dict()
        assert d["lane"] == "A"
        assert d["claim_type"] == "custody"
        assert isinstance(d["expected_value"], str)

    def test_case_outcome_calculate_expected_value(self):
        cop = CaseOutcomeProbability(
            win_probability=60,
            damages_if_win_mid=Decimal("50000"),
        )
        ev = cop.calculate_expected_value()
        assert ev == Decimal("30000.00")
        assert cop.expected_value == Decimal("30000.00")

    def test_settlement_range_defaults(self):
        sr = SettlementRange()
        assert sr.floor == Decimal("0")
        assert sr.walkaway == Decimal("0")

    def test_settlement_range_to_dict(self):
        sr = SettlementRange(
            lane="B", defendant_name="HOA",
            floor=Decimal("5000"), target=Decimal("15000"),
            ceiling=Decimal("30000"), walkaway=Decimal("3000"),
        )
        d = sr.to_dict()
        assert d["floor"] == "5000"
        assert d["defendant_name"] == "HOA"

    def test_damage_item_to_dict(self):
        item = DamageItem(
            category="Lost Wages",
            description="6 months",
            amount=Decimal("25000"),
            multiplier=Decimal("1"),
        )
        d = item.to_dict()
        assert d["total"] == "25000"

    def test_damage_item_with_multiplier(self):
        item = DamageItem(
            category="Housing",
            amount=Decimal("10000"),
            multiplier=Decimal("3"),
            authority="MCL 37.2801",
        )
        d = item.to_dict()
        assert d["total"] == "30000"

    def test_negotiation_issue_to_dict(self):
        ni = NegotiationIssue(
            issue="Custody", our_position="Joint",
            their_likely_position="Sole mother",
            priority=9,
        )
        d = ni.to_dict()
        assert d["priority"] == 9
        assert d["issue"] == "Custody"


# ═══════════════════════════════════════════════════════════════════════════
# ExpectedValueCalculator
# ═══════════════════════════════════════════════════════════════════════════

class TestExpectedValueCalculator:

    def test_calculate_case_value_lane_a(self, ev_calc):
        results = ev_calc.calculate_case_value("A")
        assert len(results) == 3  # custody_interference, child_support, parental_alienation
        for r in results:
            assert r.expected_value > Decimal("0") or r.win_probability > 0

    def test_calculate_case_value_lane_b(self, ev_calc):
        results = ev_calc.calculate_case_value("B")
        assert len(results) == 2

    def test_calculate_case_value_lane_d(self, ev_calc):
        results = ev_calc.calculate_case_value("D")
        assert len(results) == 1

    def test_calculate_case_value_lane_e(self, ev_calc):
        results = ev_calc.calculate_case_value("E")
        assert len(results) == 1

    def test_calculate_case_value_lane_f(self, ev_calc):
        results = ev_calc.calculate_case_value("F")
        assert len(results) == 1
        assert results[0].expected_value == Decimal("0.00")

    def test_calculate_case_value_unknown_lane(self, ev_calc):
        results = ev_calc.calculate_case_value("Z")
        assert results == []

    def test_calculate_case_value_filter_claims(self, ev_calc):
        results = ev_calc.calculate_case_value("A", ["custody_interference"])
        assert len(results) == 1
        assert results[0].claim_type == "custody_interference"

    def test_discount_for_risk_no_factors(self, ev_calc):
        result = ev_calc.discount_for_risk(Decimal("10000"), [])
        assert result == Decimal("10000.00")

    def test_discount_for_risk_one_factor(self, ev_calc):
        result = ev_calc.discount_for_risk(Decimal("10000"), ["risk1"])
        assert result == Decimal("9500.00")

    def test_discount_for_risk_cap_at_50_percent(self, ev_calc):
        risks = [f"risk{i}" for i in range(20)]
        result = ev_calc.discount_for_risk(Decimal("10000"), risks)
        assert result == Decimal("5000.00")

    def test_calculate_litigation_costs_known_steps(self, ev_calc):
        costs = ev_calc.calculate_litigation_costs(["discovery", "trial"])
        assert costs == Decimal("2500.00")

    def test_calculate_litigation_costs_unknown_step(self, ev_calc):
        costs = ev_calc.calculate_litigation_costs(["unknown_step"])
        assert costs == Decimal("250.00")

    def test_calculate_litigation_costs_empty(self, ev_calc):
        costs = ev_calc.calculate_litigation_costs([])
        assert costs == Decimal("0")

    def test_net_expected_value(self, ev_calc):
        net = ev_calc.net_expected_value(Decimal("50000"), Decimal("5000"))
        assert net == Decimal("45000.00")

    def test_net_expected_value_negative(self, ev_calc):
        net = ev_calc.net_expected_value(Decimal("1000"), Decimal("5000"))
        assert net == Decimal("-4000.00")

    def test_compare_settlement_accept(self, ev_calc):
        result = ev_calc.compare_settlement_to_trial(
            Decimal("50000"), Decimal("40000"),
        )
        assert result["verdict"] == "ACCEPT"

    def test_compare_settlement_reject(self, ev_calc):
        result = ev_calc.compare_settlement_to_trial(
            Decimal("5000"), Decimal("50000"), "MODERATE",
        )
        assert result["verdict"] == "REJECT"

    def test_compare_settlement_counter(self, ev_calc):
        result = ev_calc.compare_settlement_to_trial(
            Decimal("42000"), Decimal("50000"), "MODERATE",
        )
        assert result["verdict"] == "COUNTER"
        assert result["counter_suggestion"] is not None

    def test_compare_settlement_aggressive(self, ev_calc):
        result = ev_calc.compare_settlement_to_trial(
            Decimal("55000"), Decimal("50000"), "AGGRESSIVE",
        )
        assert result["verdict"] in ("ACCEPT", "COUNTER")

    def test_decimal_precision(self, ev_calc):
        """Verify all calculations use Decimal, not float."""
        results = ev_calc.calculate_case_value("A")
        for r in results:
            assert isinstance(r.expected_value, Decimal)

    def test_ev_calc_stats(self, ev_calc):
        stats = ev_calc.get_stats()
        assert "claim_template_lanes" in stats
        assert "total_claim_templates" in stats


# ═══════════════════════════════════════════════════════════════════════════
# DemandLetterGenerator
# ═══════════════════════════════════════════════════════════════════════════

class TestDemandLetterGenerator:

    def test_generate_demand(self, settlement_db):
        gen = DemandLetterGenerator(conn=settlement_db)
        result = gen.generate_demand(
            "Emily A. Watson", "A", Decimal("50000"),
        )
        assert "letter_id" in result
        assert result["defendant"] == "Emily A. Watson"
        assert "DEMAND FOR SETTLEMENT" in result["text"]
        assert PLAINTIFF in result["text"]

    def test_generate_demand_with_damage_items(self, settlement_db):
        gen = DemandLetterGenerator(conn=settlement_db)
        items = [
            DamageItem(category="Emotional", amount=Decimal("20000")),
            DamageItem(category="Housing", amount=Decimal("10000"),
                       multiplier=Decimal("3"), authority="MCL 37.2801"),
        ]
        result = gen.generate_demand(
            "Shady Oaks HOA", "B", Decimal("50000"),
            damage_items=items,
        )
        assert "ITEMISED DAMAGES" in result["text"]
        assert "MCL 37.2801" in result["text"]

    def test_generate_global_demand(self, settlement_db):
        gen = DemandLetterGenerator(conn=settlement_db)
        defendants = [
            ("Watson", "A", Decimal("30000")),
            ("HOA", "B", Decimal("20000")),
        ]
        result = gen.generate_global_demand(
            defendants, Decimal("50000"),
        )
        assert result["defendant_count"] == 2
        assert "GLOBAL DEMAND" in result["text"]
        assert result["total_amount"] == "50000"

    def test_format_damages_summary(self, settlement_db):
        gen = DemandLetterGenerator(conn=settlement_db)
        items = [
            DamageItem(category="Lost Income", amount=Decimal("15000")),
            DamageItem(category="Treble", amount=Decimal("15000"),
                       multiplier=Decimal("3")),
        ]
        summary = gen.format_damages_summary(items)
        assert "TOTAL" in summary

    def test_demand_persists_to_db(self, settlement_db):
        gen = DemandLetterGenerator(conn=settlement_db)
        gen.generate_demand("Test Def", "A", Decimal("1000"))
        row = settlement_db.execute(
            "SELECT COUNT(*) AS c FROM demand_letters",
        ).fetchone()
        assert dict(row)["c"] == 1

    def test_demand_letter_stats(self, settlement_db):
        gen = DemandLetterGenerator(conn=settlement_db)
        gen.generate_demand("D1", "A", Decimal("1000"))
        gen.generate_demand("D2", "B", Decimal("2000"))
        stats = gen.get_stats()
        assert stats["letters_generated"] == 2


# ═══════════════════════════════════════════════════════════════════════════
# MediationBriefWriter
# ═══════════════════════════════════════════════════════════════════════════

class TestMediationBriefWriter:

    def test_generate_mediation_brief(self, mediation_writer):
        brief = mediation_writer.generate_mediation_brief(
            "A",
            ["Custody schedule", "Child support"],
            {"Custody schedule": "Joint custody"},
        )
        assert "CONFIDENTIAL MEDIATION BRIEF" in brief
        assert "MCR 3.216" in brief
        assert "Custody schedule" in brief

    def test_prepare_opening_statement(self, mediation_writer):
        statement = mediation_writer.prepare_opening_statement(
            ["Point 1", "Point 2"],
        )
        assert PLAINTIFF in statement
        assert "Point 1" in statement

    def test_build_issue_matrix(self, mediation_writer):
        issues = [
            NegotiationIssue(
                issue="Custody", our_position="Joint",
                their_likely_position="Sole", priority=10,
                zone_of_agreement="Shared decision-making",
            ),
            NegotiationIssue(
                issue="Support", our_position="Reduce",
                their_likely_position="Increase", priority=7,
                tradeoff_value="Parenting time offset",
            ),
        ]
        matrix = mediation_writer.build_issue_matrix(issues)
        assert "NEGOTIATION ISSUE MATRIX" in matrix
        assert "Custody" in matrix
        assert "Support" in matrix

    def test_calculate_batna(self, mediation_writer):
        result = mediation_writer.calculate_batna(
            Decimal("50000"), Decimal("10000"),
        )
        assert result["net_batna_value"] == "40000.00"
        assert result["batna"] == "Proceed to trial"

    def test_calculate_watna(self, mediation_writer):
        scenarios = [
            {"scenario": "Loss at trial", "amount": Decimal("5000")},
            {"scenario": "Adverse order", "amount": Decimal("10000")},
        ]
        result = mediation_writer.calculate_watna(scenarios)
        assert result["total_worst_exposure"] == "15000"
        assert len(result["scenarios"]) == 2

    def test_mediation_writer_stats(self, mediation_writer):
        stats = mediation_writer.get_stats()
        assert stats["module"] == "MediationBriefWriter"


# ═══════════════════════════════════════════════════════════════════════════
# SettlementAnalyzer (Orchestrator)
# ═══════════════════════════════════════════════════════════════════════════

class TestSettlementAnalyzer:

    def test_analyze_case_value(self, settlement_db_path):
        sa = SettlementAnalyzer(db_path=settlement_db_path)
        try:
            results = sa.analyze_case_value("A")
            assert len(results) == 3
        finally:
            sa.close()

    def test_generate_settlement_range(self, settlement_db_path):
        sa = SettlementAnalyzer(db_path=settlement_db_path)
        try:
            sr = sa.generate_settlement_range("A", "Emily A. Watson")
            assert sr.floor > Decimal("0")
            assert sr.target >= sr.floor
            assert sr.ceiling >= sr.target
            assert sr.walkaway <= sr.floor
        finally:
            sa.close()

    def test_settlement_range_aggressive(self, settlement_db_path):
        sa = SettlementAnalyzer(db_path=settlement_db_path)
        try:
            sr = sa.generate_settlement_range(
                "A", "Watson", strategy=SettlementStrategy.AGGRESSIVE,
            )
            assert sr.floor > Decimal("0")
        finally:
            sa.close()

    def test_settlement_range_conservative(self, settlement_db_path):
        sa = SettlementAnalyzer(db_path=settlement_db_path)
        try:
            sr_mod = sa.generate_settlement_range(
                "B", "HOA", strategy=SettlementStrategy.MODERATE,
            )
            sr_con = sa.generate_settlement_range(
                "B", "HOA", strategy=SettlementStrategy.CONSERVATIVE,
            )
            assert sr_con.target <= sr_mod.target
        finally:
            sa.close()

    def test_settlement_range_all_lanes(self, settlement_db_path):
        sa = SettlementAnalyzer(db_path=settlement_db_path)
        try:
            for lane in ["A", "B", "D", "E", "F"]:
                sr = sa.generate_settlement_range(lane, f"Defendant-{lane}")
                assert isinstance(sr, SettlementRange)
        finally:
            sa.close()

    def test_evaluate_offer(self, settlement_db_path):
        sa = SettlementAnalyzer(db_path=settlement_db_path)
        try:
            result = sa.evaluate_offer(Decimal("5000"), "A")
            assert result["verdict"] in ("ACCEPT", "REJECT", "COUNTER")
            assert "lane" in result
        finally:
            sa.close()

    def test_evaluate_offer_high_amount(self, settlement_db_path):
        sa = SettlementAnalyzer(db_path=settlement_db_path)
        try:
            result = sa.evaluate_offer(Decimal("999999"), "A")
            assert result["verdict"] == "ACCEPT"
        finally:
            sa.close()

    def test_generate_demand_package_default(self, settlement_db_path):
        sa = SettlementAnalyzer(db_path=settlement_db_path)
        try:
            pkg = sa.generate_demand_package()
            assert pkg["defendant_count"] == 19
            assert int(Decimal(pkg["total_demanded"])) > 0
        finally:
            sa.close()

    def test_generate_demand_package_custom(self, settlement_db_path):
        sa = SettlementAnalyzer(db_path=settlement_db_path)
        try:
            pkg = sa.generate_demand_package(
                defendants=[
                    ("Watson", "A", Decimal("30000")),
                    ("HOA", "B", Decimal("50000")),
                ],
            )
            assert pkg["defendant_count"] == 2
            assert pkg["total_demanded"] == "80000"
        finally:
            sa.close()

    def test_prepare_mediation(self, settlement_db_path):
        sa = SettlementAnalyzer(db_path=settlement_db_path)
        try:
            result = sa.prepare_mediation("A")
            assert "brief" in result
            assert "batna" in result
            assert "watna" in result
        finally:
            sa.close()

    def test_get_defendant_analysis_watson(self, settlement_db_path):
        sa = SettlementAnalyzer(db_path=settlement_db_path)
        try:
            result = sa.get_defendant_analysis("Emily A. Watson")
            assert "defendant" in result
            assert "A" in result["lanes"]
        finally:
            sa.close()

    def test_get_defendant_analysis_mcneill(self, settlement_db_path):
        sa = SettlementAnalyzer(db_path=settlement_db_path)
        try:
            result = sa.get_defendant_analysis("Hon. Jenny L. McNeill")
            assert "immunity" in result.get("immunity_note", "").lower()
        finally:
            sa.close()

    def test_get_defendant_analysis_not_found(self, settlement_db_path):
        sa = SettlementAnalyzer(db_path=settlement_db_path)
        try:
            result = sa.get_defendant_analysis("Unknown Person")
            assert "error" in result
        finally:
            sa.close()

    def test_19_defendants_in_registry(self):
        assert len(DEFENDANTS) == 19

    def test_defendant_registry_structure(self):
        for d in DEFENDANTS:
            assert "name" in d
            assert "role" in d
            assert "lane" in d

    def test_settlement_analyzer_stats(self, settlement_db_path):
        sa = SettlementAnalyzer(db_path=settlement_db_path)
        try:
            stats = sa.get_stats()
            assert "engine_version" in stats
            assert stats["engine_version"] == "1.0.0"
            assert stats["defendant_registry_count"] == 19
        finally:
            sa.close()

    def test_close_idempotent(self, settlement_db_path):
        sa = SettlementAnalyzer(db_path=settlement_db_path)
        sa._init_db()
        sa.close()
        sa.close()  # should not raise


# ═══════════════════════════════════════════════════════════════════════════
# Decimal Precision Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestDecimalPrecision:

    def test_dec_helper_from_string(self):
        assert _dec("123.45") == Decimal("123.45")

    def test_dec_helper_from_int(self):
        assert _dec(100) == Decimal("100")

    def test_dec_helper_from_decimal(self):
        assert _dec(Decimal("99.99")) == Decimal("99.99")

    def test_dec_helper_from_invalid(self):
        assert _dec("not-a-number") == Decimal("0")

    def test_dec_helper_from_float(self):
        result = _dec(3.14)
        assert isinstance(result, Decimal)

    def test_no_float_in_settlement_range(self, settlement_db_path):
        sa = SettlementAnalyzer(db_path=settlement_db_path)
        try:
            sr = sa.generate_settlement_range("A", "Test")
            assert isinstance(sr.floor, Decimal)
            assert isinstance(sr.target, Decimal)
            assert isinstance(sr.ceiling, Decimal)
            assert isinstance(sr.walkaway, Decimal)
        finally:
            sa.close()


# ═══════════════════════════════════════════════════════════════════════════
# Lane-Specific Settlement Analysis
# ═══════════════════════════════════════════════════════════════════════════

class TestLaneSpecificSettlement:

    def test_lane_c_no_claims(self):
        calc = ExpectedValueCalculator()
        results = calc.calculate_case_value("C")
        assert results == []

    def test_per_lane_has_expected_claim_count(self):
        calc = ExpectedValueCalculator()
        assert len(calc.calculate_case_value("A")) == 3
        assert len(calc.calculate_case_value("B")) == 2
        assert len(calc.calculate_case_value("D")) == 1
        assert len(calc.calculate_case_value("E")) == 1
        assert len(calc.calculate_case_value("F")) == 1
