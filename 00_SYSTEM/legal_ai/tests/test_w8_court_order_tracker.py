"""Wave-8 Tests — CourtOrderTracker
====================================
Comprehensive pytest suite for court_order_tracker.py.

80+ tests covering enums, dataclasses, ComplianceMonitor,
OrderConflictDetector, ContemptEngine, and the CourtOrderTracker
orchestrator.

• Zero network / zero real DB — all DB interactions use temp SQLite
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
# Import targets
# ---------------------------------------------------------------------------
import sys

_THIS_DIR = pathlib.Path(__file__).resolve().parent
_LEGAL_AI_DIR = _THIS_DIR.parent
if str(_LEGAL_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_LEGAL_AI_DIR))

from court_order_tracker import (
    OrderType,
    ComplianceStatus,
    ViolationSeverity,
    OrderStatus,
    OrderProvision,
    CourtOrder,
    ViolationRecord,
    ConflictRecord,
    ComplianceMonitor,
    OrderConflictDetector,
    ContemptEngine,
    CourtOrderTracker,
    PLAINTIFF,
    PLAINTIFF_ROLE,
    DEFENDANT,
    CHILD,
    CHILD_INITIALS,
    JUDGE,
    CASE_LANES,
    _PRAGMAS,
    _SCHEMA as ORDER_SCHEMA,
)


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def tmp_db(tmp_path):
    """In-memory style temp DB with court order schema."""
    db_file = tmp_path / "test_court_orders.db"
    conn = sqlite3.connect(str(db_file), timeout=30)
    conn.executescript(_PRAGMAS)
    conn.row_factory = sqlite3.Row
    conn.executescript(ORDER_SCHEMA)
    yield conn
    conn.close()


@pytest.fixture
def tracker_db_path(tmp_path):
    """Path for CourtOrderTracker(db_path=...)."""
    return tmp_path / "tracker_test.db"


@pytest.fixture
def compliance_monitor(tmp_db):
    return ComplianceMonitor(conn=tmp_db)


@pytest.fixture
def conflict_detector():
    return OrderConflictDetector()


@pytest.fixture
def contempt_engine(tmp_db):
    return ContemptEngine(conn=tmp_db)


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _insert_order(conn, order_id="ord-001", case_number="2024-001507-DC",
                  case_lane="A", order_type="TEMPORARY", status="ACTIVE",
                  date_entered="2024-06-15", date_expires=None,
                  judge="Hon. Jenny L. McNeill"):
    conn.execute(
        "INSERT INTO court_orders "
        "(order_id, case_number, case_lane, court, judge, order_type, "
        "date_entered, date_effective, date_expires, status, "
        "related_orders, filing_ref, notes) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (order_id, case_number, case_lane,
         "14th Circuit Court", judge, order_type,
         date_entered, date_entered, date_expires,
         status, "[]", "", ""),
    )
    conn.commit()


def _insert_provision(conn, provision_id=None, order_id="ord-001",
                      description="Test provision",
                      compliance_status="UNKNOWN",
                      responsible_party="Emily A. Watson",
                      deadline=None):
    pid = provision_id or str(uuid.uuid4())
    conn.execute(
        "INSERT INTO order_provisions "
        "(provision_id, order_id, description, compliance_status, "
        "responsible_party, deadline, evidence_of_compliance, "
        "evidence_of_violation, last_checked) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (pid, order_id, description, compliance_status,
         responsible_party, deadline, "[]", "[]", None),
    )
    conn.commit()
    return pid


# ═══════════════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════════════

class TestOrderEnums:

    def test_order_type_values(self):
        expected = {"CUSTODY", "PARENTING_TIME", "CHILD_SUPPORT", "PPO",
                    "TEMPORARY", "FINAL", "CONSENT", "EX_PARTE",
                    "SHOW_CAUSE", "STIPULATED"}
        assert {e.value for e in OrderType} == expected

    def test_compliance_status_values(self):
        expected = {"COMPLIANT", "PARTIAL", "NONCOMPLIANT", "DISPUTED",
                    "UNKNOWN", "EXPIRED", "SUPERSEDED"}
        assert {e.value for e in ComplianceStatus} == expected

    def test_violation_severity_values(self):
        expected = {"MINOR", "MODERATE", "SEVERE", "WILLFUL"}
        assert {e.value for e in ViolationSeverity} == expected

    def test_order_status_values(self):
        expected = {"ACTIVE", "EXPIRED", "SUPERSEDED", "VACATED",
                    "MODIFIED", "APPEALED"}
        assert {e.value for e in OrderStatus} == expected

    def test_enum_from_string(self):
        assert OrderType("CUSTODY") == OrderType.CUSTODY
        assert ComplianceStatus("COMPLIANT") == ComplianceStatus.COMPLIANT
        assert ViolationSeverity("WILLFUL") == ViolationSeverity.WILLFUL
        assert OrderStatus("ACTIVE") == OrderStatus.ACTIVE

    def test_enum_count_order_type(self):
        assert len(OrderType) == 10

    def test_enum_count_compliance_status(self):
        assert len(ComplianceStatus) == 7

    def test_enum_count_violation_severity(self):
        assert len(ViolationSeverity) == 4

    def test_enum_count_order_status(self):
        assert len(OrderStatus) == 6


# ═══════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════

class TestOrderConstants:

    def test_plaintiff(self):
        assert PLAINTIFF == "Andrew James Pigors"

    def test_defendant(self):
        assert DEFENDANT == "Emily A. Watson"

    def test_judge(self):
        assert JUDGE == "Hon. Jenny L. McNeill"

    def test_child_initials(self):
        assert CHILD_INITIALS == "L.D.W."

    def test_six_lanes(self):
        assert set(CASE_LANES.keys()) == {"A", "B", "C", "D", "E", "F"}


# ═══════════════════════════════════════════════════════════════════════════
# OrderProvision Dataclass
# ═══════════════════════════════════════════════════════════════════════════

class TestOrderProvision:

    def test_default_creation(self):
        prov = OrderProvision()
        assert prov.compliance_status == ComplianceStatus.UNKNOWN
        assert prov.provision_id  # UUID generated

    def test_uuid_uniqueness(self):
        provs = [OrderProvision() for _ in range(50)]
        ids = {p.provision_id for p in provs}
        assert len(ids) == 50

    def test_to_dict_keys(self):
        prov = OrderProvision(
            order_id="ord-1", description="Pay child support",
            responsible_party="Watson",
        )
        d = prov.to_dict()
        assert d["order_id"] == "ord-1"
        assert d["description"] == "Pay child support"
        assert d["compliance_status"] == "UNKNOWN"

    def test_to_dict_serialisable(self):
        prov = OrderProvision()
        json_str = json.dumps(prov.to_dict())
        assert isinstance(json_str, str)

    def test_is_violated_noncompliant(self):
        prov = OrderProvision(compliance_status=ComplianceStatus.NONCOMPLIANT)
        assert prov.is_violated() is True

    def test_is_violated_partial(self):
        prov = OrderProvision(compliance_status=ComplianceStatus.PARTIAL)
        assert prov.is_violated() is True

    def test_is_violated_compliant(self):
        prov = OrderProvision(compliance_status=ComplianceStatus.COMPLIANT)
        assert prov.is_violated() is False

    def test_is_violated_unknown(self):
        prov = OrderProvision(compliance_status=ComplianceStatus.UNKNOWN)
        assert prov.is_violated() is False

    def test_is_violated_disputed(self):
        prov = OrderProvision(compliance_status=ComplianceStatus.DISPUTED)
        assert prov.is_violated() is False


# ═══════════════════════════════════════════════════════════════════════════
# CourtOrder Dataclass
# ═══════════════════════════════════════════════════════════════════════════

class TestCourtOrder:

    def test_default_creation(self):
        order = CourtOrder()
        assert order.order_type == OrderType.TEMPORARY
        assert order.status == OrderStatus.ACTIVE
        assert order.order_id  # UUID

    def test_uuid_uniqueness(self):
        orders = [CourtOrder() for _ in range(50)]
        ids = {o.order_id for o in orders}
        assert len(ids) == 50

    def test_to_dict_keys(self):
        order = CourtOrder(
            case_number="2024-001507-DC", case_lane="A",
            judge=JUDGE, date_entered="2024-06-15",
        )
        d = order.to_dict()
        assert d["case_number"] == "2024-001507-DC"
        assert d["order_type"] == "TEMPORARY"
        assert d["status"] == "ACTIVE"

    def test_to_dict_with_provisions(self):
        prov = OrderProvision(description="Test provision")
        order = CourtOrder(provisions=[prov])
        d = order.to_dict()
        assert len(d["provisions"]) == 1
        assert d["provisions"][0]["description"] == "Test provision"

    def test_to_dict_serialisable(self):
        order = CourtOrder()
        json_str = json.dumps(order.to_dict())
        assert isinstance(json_str, str)

    def test_is_active_active_no_expiry(self):
        order = CourtOrder(status=OrderStatus.ACTIVE)
        assert order.is_active() is True

    def test_is_active_expired_status(self):
        order = CourtOrder(status=OrderStatus.EXPIRED)
        assert order.is_active() is False

    def test_is_active_superseded(self):
        order = CourtOrder(status=OrderStatus.SUPERSEDED)
        assert order.is_active() is False

    def test_is_active_future_expiry(self):
        future = (date.today() + timedelta(days=365)).isoformat()
        order = CourtOrder(status=OrderStatus.ACTIVE, date_expires=future)
        assert order.is_active() is True

    def test_is_active_past_expiry(self):
        past = (date.today() - timedelta(days=1)).isoformat()
        order = CourtOrder(status=OrderStatus.ACTIVE, date_expires=past)
        assert order.is_active() is False

    def test_is_active_invalid_expiry(self):
        order = CourtOrder(status=OrderStatus.ACTIVE, date_expires="bad-date")
        assert order.is_active() is True  # fallback to True

    def test_is_expired_no_date(self):
        order = CourtOrder()
        assert order.is_expired() is False

    def test_is_expired_past(self):
        past = (date.today() - timedelta(days=10)).isoformat()
        order = CourtOrder(date_expires=past)
        assert order.is_expired() is True

    def test_is_expired_future(self):
        future = (date.today() + timedelta(days=10)).isoformat()
        order = CourtOrder(date_expires=future)
        assert order.is_expired() is False

    def test_is_expired_invalid(self):
        order = CourtOrder(date_expires="not-a-date")
        assert order.is_expired() is False

    def test_days_since_entry(self):
        past = (date.today() - timedelta(days=100)).isoformat()
        order = CourtOrder(date_entered=past)
        assert order.days_since_entry() == 100

    def test_days_since_entry_none(self):
        order = CourtOrder(date_entered="")
        assert order.days_since_entry() is None

    def test_days_since_entry_invalid(self):
        order = CourtOrder(date_entered="bad")
        assert order.days_since_entry() is None

    def test_days_since_entry_today(self):
        order = CourtOrder(date_entered=date.today().isoformat())
        assert order.days_since_entry() == 0


# ═══════════════════════════════════════════════════════════════════════════
# ViolationRecord Dataclass
# ═══════════════════════════════════════════════════════════════════════════

class TestViolationRecord:

    def test_default_creation(self):
        vr = ViolationRecord()
        assert vr.severity == ViolationSeverity.MODERATE

    def test_to_dict(self):
        vr = ViolationRecord(
            order_id="ord-1", provision_id="prov-1",
            provision_description="Custody violation",
            responsible_party="Watson",
            severity=ViolationSeverity.SEVERE,
            evidence=["Exhibit A"],
        )
        d = vr.to_dict()
        assert d["severity"] == "SEVERE"
        assert d["evidence"] == ["Exhibit A"]

    def test_to_dict_serialisable(self):
        vr = ViolationRecord()
        json_str = json.dumps(vr.to_dict())
        assert isinstance(json_str, str)


# ═══════════════════════════════════════════════════════════════════════════
# ConflictRecord Dataclass
# ═══════════════════════════════════════════════════════════════════════════

class TestConflictRecord:

    def test_default_creation(self):
        cr = ConflictRecord()
        assert cr.conflict_type == ""

    def test_to_dict(self):
        cr = ConflictRecord(
            order_a_id="ord-1", order_b_id="ord-2",
            provision_a="Joint custody", provision_b="Sole custody",
            conflict_type="custody",
            description="Contradictory custody provisions",
        )
        d = cr.to_dict()
        assert d["conflict_type"] == "custody"
        assert d["order_a_id"] == "ord-1"

    def test_to_dict_serialisable(self):
        cr = ConflictRecord()
        json_str = json.dumps(cr.to_dict())
        assert isinstance(json_str, str)


# ═══════════════════════════════════════════════════════════════════════════
# ComplianceMonitor
# ═══════════════════════════════════════════════════════════════════════════

class TestComplianceMonitor:

    def test_check_compliance_no_provisions(self, compliance_monitor, tmp_db):
        _insert_order(tmp_db, "ord-100")
        results = compliance_monitor.check_compliance("ord-100")
        assert results == []

    def test_check_compliance_with_provisions(self, compliance_monitor, tmp_db):
        _insert_order(tmp_db, "ord-101")
        _insert_provision(tmp_db, order_id="ord-101",
                          description="Pay support",
                          compliance_status="UNKNOWN")
        results = compliance_monitor.check_compliance("ord-101")
        assert len(results) == 1
        assert results[0]["description"] == "Pay support"

    def test_check_compliance_detects_overdue(self, compliance_monitor, tmp_db):
        _insert_order(tmp_db, "ord-102")
        past = (date.today() - timedelta(days=5)).isoformat()
        _insert_provision(tmp_db, order_id="ord-102",
                          compliance_status="UNKNOWN",
                          deadline=past)
        results = compliance_monitor.check_compliance("ord-102")
        assert len(results) == 1
        assert results[0]["status_after"] == "NONCOMPLIANT"
        assert results[0]["is_violated"] is True

    def test_check_compliance_compliant_not_overdue(self, compliance_monitor, tmp_db):
        _insert_order(tmp_db, "ord-103")
        past = (date.today() - timedelta(days=5)).isoformat()
        _insert_provision(tmp_db, order_id="ord-103",
                          compliance_status="COMPLIANT",
                          deadline=past)
        results = compliance_monitor.check_compliance("ord-103")
        assert results[0]["status_after"] == "COMPLIANT"

    def test_detect_violations_no_order(self, compliance_monitor, tmp_db):
        violations = compliance_monitor.detect_violations("nonexistent")
        assert violations == []

    def test_detect_violations_with_noncompliant(self, compliance_monitor, tmp_db):
        _insert_order(tmp_db, "ord-104")
        _insert_provision(tmp_db, order_id="ord-104",
                          compliance_status="NONCOMPLIANT",
                          description="Failed to appear")
        violations = compliance_monitor.detect_violations("ord-104")
        assert len(violations) == 1
        assert violations[0].responsible_party == "Emily A. Watson"

    def test_generate_violation_report_no_order(self, compliance_monitor, tmp_db):
        report = compliance_monitor.generate_violation_report("nonexistent")
        assert "not found" in report

    def test_generate_violation_report_with_violations(self, compliance_monitor, tmp_db):
        _insert_order(tmp_db, "ord-105")
        _insert_provision(tmp_db, order_id="ord-105",
                          compliance_status="NONCOMPLIANT",
                          description="Denied parenting time")
        report = compliance_monitor.generate_violation_report("ord-105")
        assert "VIOLATION REPORT" in report
        assert "Denied parenting time" in report

    def test_generate_violation_report_no_violations(self, compliance_monitor, tmp_db):
        _insert_order(tmp_db, "ord-106")
        _insert_provision(tmp_db, order_id="ord-106",
                          compliance_status="COMPLIANT")
        report = compliance_monitor.generate_violation_report("ord-106")
        assert "No violations detected" in report

    def test_track_compliance_over_time(self, compliance_monitor, tmp_db):
        _insert_order(tmp_db, "ord-107")
        _insert_provision(tmp_db, order_id="ord-107")
        compliance_monitor.check_compliance("ord-107")
        history = compliance_monitor.track_compliance_over_time("ord-107")
        assert len(history) == 1

    def test_calculate_violation_severity_minor(self, compliance_monitor):
        prov = OrderProvision(
            compliance_status=ComplianceStatus.PARTIAL,
            description="General provision",
        )
        severity = compliance_monitor.calculate_violation_severity(prov)
        assert severity == ViolationSeverity.MINOR

    def test_calculate_violation_severity_moderate(self, compliance_monitor):
        past = (date.today() - timedelta(days=20)).isoformat()
        prov = OrderProvision(
            compliance_status=ComplianceStatus.NONCOMPLIANT,
            deadline=past,
            description="General obligation",
        )
        severity = compliance_monitor.calculate_violation_severity(prov)
        assert severity in (ViolationSeverity.MODERATE, ViolationSeverity.SEVERE)

    def test_calculate_violation_severity_severe_child_keyword(self, compliance_monitor):
        past = (date.today() - timedelta(days=35)).isoformat()
        prov = OrderProvision(
            compliance_status=ComplianceStatus.NONCOMPLIANT,
            deadline=past,
            description="Child custody transfer",
            evidence_of_violation=["Exhibit A", "Exhibit B", "Exhibit C"],
        )
        severity = compliance_monitor.calculate_violation_severity(prov)
        assert severity in (ViolationSeverity.SEVERE, ViolationSeverity.WILLFUL)

    def test_calculate_violation_severity_willful(self, compliance_monitor):
        past = (date.today() - timedelta(days=60)).isoformat()
        prov = OrderProvision(
            compliance_status=ComplianceStatus.NONCOMPLIANT,
            deadline=past,
            description="Emergency child protection order",
            evidence_of_violation=["E1", "E2", "E3", "E4"],
        )
        severity = compliance_monitor.calculate_violation_severity(prov)
        assert severity == ViolationSeverity.WILLFUL

    def test_compliance_monitor_stats(self, compliance_monitor, tmp_db):
        _insert_order(tmp_db, "ord-110")
        _insert_provision(tmp_db, order_id="ord-110")
        compliance_monitor.check_compliance("ord-110")
        stats = compliance_monitor.get_stats()
        assert stats["compliance_checks_performed"] == 1


# ═══════════════════════════════════════════════════════════════════════════
# OrderConflictDetector
# ═══════════════════════════════════════════════════════════════════════════

class TestOrderConflictDetector:

    def _make_order(self, order_id, provisions_desc, **kwargs):
        provs = [
            OrderProvision(order_id=order_id, description=d)
            for d in provisions_desc
        ]
        defaults = dict(
            order_id=order_id, case_number="2024-001507-DC",
            case_lane="A", status=OrderStatus.ACTIVE,
            date_entered="2024-06-15",
        )
        defaults.update(kwargs)
        return CourtOrder(provisions=provs, **defaults)

    def test_no_conflicts_empty(self, conflict_detector):
        conflicts = conflict_detector.detect_conflicts([])
        assert conflicts == []

    def test_no_conflicts_single_order(self, conflict_detector):
        order = self._make_order("o1", ["Custody schedule"])
        conflicts = conflict_detector.detect_conflicts([order])
        assert conflicts == []

    def test_detects_custody_conflict(self, conflict_detector):
        o1 = self._make_order("o1", ["Joint legal custody to both parents"])
        o2 = self._make_order("o2", ["Sole legal custody to mother"])
        conflicts = conflict_detector.detect_conflicts([o1, o2])
        assert len(conflicts) >= 1
        assert any(c.conflict_type == "custody" for c in conflicts)

    def test_detects_parenting_time_conflict(self, conflict_detector):
        o1 = self._make_order("o1", ["Father gets parenting time weekends"])
        o2 = self._make_order("o2", ["Revised parenting time schedule for father"])
        conflicts = conflict_detector.detect_conflicts([o1, o2])
        assert len(conflicts) >= 1

    def test_no_conflict_different_topics(self, conflict_detector):
        o1 = self._make_order("o1", ["Pay child support $500/month"])
        o2 = self._make_order("o2", ["No contact with minor child"])
        conflicts = conflict_detector.detect_conflicts([o1, o2])
        assert len(conflicts) == 0

    def test_inactive_orders_excluded(self, conflict_detector):
        o1 = self._make_order("o1", ["Custody arrangement"],
                              status=OrderStatus.ACTIVE)
        o2 = self._make_order("o2", ["Custody arrangement"],
                              status=OrderStatus.EXPIRED)
        conflicts = conflict_detector.detect_conflicts([o1, o2])
        assert conflicts == []

    def test_detect_superseded_same_type(self, conflict_detector):
        o_old = self._make_order(
            "o-old", ["Old provision"],
            date_entered="2024-01-01",
            order_type=OrderType.TEMPORARY,
        )
        o_new = self._make_order(
            "o-new", ["New provision"],
            date_entered="2024-06-01",
            order_type=OrderType.TEMPORARY,
        )
        issues = conflict_detector.detect_superseded_orders([o_old, o_new])
        assert len(issues) >= 1
        assert issues[0]["issue"] == "POSSIBLE_SUPERSESSION"

    def test_detect_superseded_temp_by_final(self, conflict_detector):
        o_temp = self._make_order(
            "o-temp", ["Temp provision"],
            date_entered="2024-01-01",
            order_type=OrderType.TEMPORARY,
        )
        o_final = self._make_order(
            "o-final", ["Final provision"],
            date_entered="2024-06-01",
            order_type=OrderType.FINAL,
        )
        issues = conflict_detector.detect_superseded_orders([o_temp, o_final])
        temp_issues = [i for i in issues if i["issue"] == "TEMP_NOT_SUPERSEDED"]
        assert len(temp_issues) >= 1

    def test_detect_ex_parte_orders(self, conflict_detector):
        order = self._make_order(
            "o-ex", ["Emergency provision"],
            order_type=OrderType.EX_PARTE,
            judge="Hon. Jenny L. McNeill",
        )
        results = conflict_detector.detect_ex_parte_orders([order])
        assert len(results) == 1
        assert any("MCR 3.207" in basis for basis in results[0]["challenge_basis"])

    def test_detect_ex_parte_mcneill_flag(self, conflict_detector):
        order = self._make_order(
            "o-ex2", ["Ex parte"],
            order_type=OrderType.EX_PARTE,
            judge="Hon. Jenny L. McNeill",
        )
        results = conflict_detector.detect_ex_parte_orders([order])
        assert any("mcneill" in b.lower() for b in results[0]["challenge_basis"])

    def test_detect_ex_parte_non_ex_parte_excluded(self, conflict_detector):
        order = self._make_order(
            "o-normal", ["Normal provision"],
            order_type=OrderType.CUSTODY,
        )
        results = conflict_detector.detect_ex_parte_orders([order])
        assert results == []

    def test_generate_conflict_matrix_no_conflicts(self, conflict_detector):
        o1 = self._make_order("o1", ["Support payment"])
        matrix = conflict_detector.generate_conflict_matrix([o1])
        assert "No conflicts detected" in matrix

    def test_generate_conflict_matrix_with_conflicts(self, conflict_detector):
        o1 = self._make_order("o1", ["Joint custody"])
        o2 = self._make_order("o2", ["Sole custody to mother"])
        matrix = conflict_detector.generate_conflict_matrix([o1, o2])
        assert "Conflict #1" in matrix

    def test_conflict_detector_stats(self, conflict_detector):
        stats = conflict_detector.get_stats()
        assert stats["module"] == "OrderConflictDetector"


# ═══════════════════════════════════════════════════════════════════════════
# ContemptEngine
# ═══════════════════════════════════════════════════════════════════════════

class TestContemptEngine:

    def test_evaluate_contempt_basis_no_violations(self, contempt_engine):
        result = contempt_engine.evaluate_contempt_basis("ord-1", [])
        assert result["supportable"] is False

    def test_evaluate_contempt_basis_severe_violation(self, contempt_engine):
        violations = [
            ViolationRecord(
                severity=ViolationSeverity.SEVERE,
                provision_description="Denied custody exchange",
            ),
        ]
        result = contempt_engine.evaluate_contempt_basis("ord-1", violations)
        assert result["supportable"] is True
        assert result["severe_count"] == 1

    def test_evaluate_contempt_basis_two_moderate(self, contempt_engine):
        violations = [
            ViolationRecord(severity=ViolationSeverity.MODERATE),
            ViolationRecord(severity=ViolationSeverity.MODERATE),
        ]
        result = contempt_engine.evaluate_contempt_basis("ord-1", violations)
        assert result["supportable"] is True

    def test_evaluate_contempt_basis_one_moderate_not_enough(self, contempt_engine):
        violations = [
            ViolationRecord(severity=ViolationSeverity.MODERATE),
        ]
        result = contempt_engine.evaluate_contempt_basis("ord-1", violations)
        assert result["supportable"] is False

    def test_evaluate_contempt_basis_minor_not_enough(self, contempt_engine):
        violations = [
            ViolationRecord(severity=ViolationSeverity.MINOR),
            ViolationRecord(severity=ViolationSeverity.MINOR),
        ]
        result = contempt_engine.evaluate_contempt_basis("ord-1", violations)
        assert result["supportable"] is False

    def test_evaluate_contempt_willful_is_supportable(self, contempt_engine):
        violations = [
            ViolationRecord(severity=ViolationSeverity.WILLFUL),
        ]
        result = contempt_engine.evaluate_contempt_basis("ord-1", violations)
        assert result["supportable"] is True

    def test_evaluate_contempt_elements_structure(self, contempt_engine):
        violations = [ViolationRecord(severity=ViolationSeverity.SEVERE)]
        result = contempt_engine.evaluate_contempt_basis("ord-1", violations)
        assert len(result["elements"]) == 3
        assert result["authority"] == ["MCR 3.606", "MCL 600.1701"]

    def test_prepare_contempt_motion(self, contempt_engine, tmp_db):
        _insert_order(tmp_db, "ord-200")
        violations = [
            ViolationRecord(
                provision_description="Denied parenting time",
                responsible_party="Watson",
                severity=ViolationSeverity.SEVERE,
                evidence=["Exhibit A"],
            ),
        ]
        result = contempt_engine.prepare_contempt_motion("ord-200", violations)
        assert "action_id" in result
        assert "MCR 3.606" in result["motion_text"]
        assert "Denied parenting time" in result["motion_text"]

    def test_prepare_contempt_motion_not_found(self, contempt_engine):
        result = contempt_engine.prepare_contempt_motion("nonexistent", [])
        assert "error" in result

    def test_calculate_purge_conditions(self, contempt_engine, tmp_db):
        _insert_order(tmp_db, "ord-201")
        past = (date.today() - timedelta(days=10)).isoformat()
        _insert_provision(tmp_db, order_id="ord-201",
                          compliance_status="NONCOMPLIANT",
                          description="Transfer records",
                          deadline=past)
        conditions = contempt_engine.calculate_purge_conditions("ord-201")
        assert len(conditions) == 1
        assert conditions[0]["days_overdue"] == 10

    def test_calculate_purge_conditions_no_violations(self, contempt_engine, tmp_db):
        _insert_order(tmp_db, "ord-202")
        _insert_provision(tmp_db, order_id="ord-202",
                          compliance_status="COMPLIANT")
        conditions = contempt_engine.calculate_purge_conditions("ord-202")
        assert conditions == []

    def test_prepare_show_cause(self, contempt_engine, tmp_db):
        _insert_order(tmp_db, "ord-203", date_entered="2024-06-15")
        result = contempt_engine.prepare_show_cause("ord-203")
        assert "action_id" in result
        assert "ORDER TO SHOW CAUSE" in result["text"]

    def test_prepare_show_cause_not_found(self, contempt_engine):
        result = contempt_engine.prepare_show_cause("nonexistent")
        assert "error" in result

    def test_track_contempt_proceedings(self, contempt_engine, tmp_db):
        _insert_order(tmp_db, "ord-204")
        contempt_engine.prepare_show_cause("ord-204")
        history = contempt_engine.track_contempt_proceedings("ord-204")
        assert len(history) == 1
        assert history[0]["action_type"] == "SHOW_CAUSE"

    def test_contempt_engine_stats(self, contempt_engine, tmp_db):
        _insert_order(tmp_db, "ord-210")
        contempt_engine.prepare_show_cause("ord-210")
        stats = contempt_engine.get_stats()
        assert stats["contempt_actions_created"] == 1


# ═══════════════════════════════════════════════════════════════════════════
# CourtOrderTracker (Orchestrator)
# ═══════════════════════════════════════════════════════════════════════════

class TestCourtOrderTracker:

    def test_catalog_order(self, tracker_db_path):
        tracker = CourtOrderTracker(db_path=tracker_db_path)
        try:
            order = tracker.catalog_order({
                "case_number": "2024-001507-DC",
                "case_lane": "A",
                "order_type": "TEMPORARY",
                "date_entered": "2024-06-15",
                "provisions": [
                    {
                        "description": "Parenting time every other weekend",
                        "responsible_party": DEFENDANT,
                    },
                ],
            })
            assert order.case_number == "2024-001507-DC"
            assert len(order.provisions) == 1
        finally:
            tracker.close()

    def test_catalog_order_defaults(self, tracker_db_path):
        tracker = CourtOrderTracker(db_path=tracker_db_path)
        try:
            order = tracker.catalog_order({
                "case_number": "123",
                "order_type": "CUSTODY",
                "date_entered": "2024-01-01",
            })
            assert order.judge == JUDGE
            assert order.court == "14th Circuit Court, Muskegon County"
        finally:
            tracker.close()

    def test_get_all_orders(self, tracker_db_path):
        tracker = CourtOrderTracker(db_path=tracker_db_path)
        try:
            tracker.catalog_order({"case_number": "1", "case_lane": "A",
                                    "order_type": "TEMPORARY",
                                    "date_entered": "2024-01-01"})
            tracker.catalog_order({"case_number": "2", "case_lane": "B",
                                    "order_type": "TEMPORARY",
                                    "date_entered": "2024-02-01"})
            all_orders = tracker.get_all_orders()
            assert len(all_orders) == 2
        finally:
            tracker.close()

    def test_get_all_orders_filter_by_lane(self, tracker_db_path):
        tracker = CourtOrderTracker(db_path=tracker_db_path)
        try:
            tracker.catalog_order({"case_number": "1", "case_lane": "A",
                                    "order_type": "TEMPORARY",
                                    "date_entered": "2024-01-01"})
            tracker.catalog_order({"case_number": "2", "case_lane": "B",
                                    "order_type": "TEMPORARY",
                                    "date_entered": "2024-02-01"})
            lane_a = tracker.get_all_orders(lane="A")
            assert len(lane_a) == 1
            assert lane_a[0].case_lane == "A"
        finally:
            tracker.close()

    def test_get_active_orders(self, tracker_db_path):
        tracker = CourtOrderTracker(db_path=tracker_db_path)
        try:
            tracker.catalog_order({"case_number": "1", "case_lane": "A",
                                    "order_type": "TEMPORARY",
                                    "date_entered": "2024-01-01",
                                    "status": "ACTIVE"})
            tracker.catalog_order({"case_number": "2", "case_lane": "A",
                                    "order_type": "TEMPORARY",
                                    "date_entered": "2024-02-01",
                                    "status": "EXPIRED"})
            active = tracker.get_active_orders()
            assert len(active) == 1
        finally:
            tracker.close()

    def test_get_order_by_id(self, tracker_db_path):
        tracker = CourtOrderTracker(db_path=tracker_db_path)
        try:
            created = tracker.catalog_order({
                "case_number": "1", "order_type": "CUSTODY",
                "date_entered": "2024-01-01",
            })
            fetched = tracker.get_order(created.order_id)
            assert fetched is not None
            assert fetched.order_id == created.order_id
        finally:
            tracker.close()

    def test_get_order_not_found(self, tracker_db_path):
        tracker = CourtOrderTracker(db_path=tracker_db_path)
        try:
            fetched = tracker.get_order("nonexistent-id")
            assert fetched is None
        finally:
            tracker.close()

    def test_update_provision_compliance(self, tracker_db_path):
        tracker = CourtOrderTracker(db_path=tracker_db_path)
        try:
            order = tracker.catalog_order({
                "case_number": "1", "order_type": "TEMPORARY",
                "date_entered": "2024-01-01",
                "provisions": [{"description": "Pay support",
                                "compliance_status": "UNKNOWN"}],
            })
            prov_id = order.provisions[0].provision_id
            tracker.update_provision_compliance(
                prov_id, ComplianceStatus.COMPLIANT,
                evidence=["Payment receipt 2024-07"],
            )
            refreshed = tracker.get_order(order.order_id)
            prov = refreshed.provisions[0]
            assert prov.compliance_status == ComplianceStatus.COMPLIANT
        finally:
            tracker.close()

    def test_monitor_compliance(self, tracker_db_path):
        tracker = CourtOrderTracker(db_path=tracker_db_path)
        try:
            tracker.catalog_order({
                "case_number": "1", "case_lane": "A",
                "order_type": "TEMPORARY",
                "date_entered": "2024-01-01",
                "provisions": [
                    {"description": "Provision 1",
                     "compliance_status": "UNKNOWN"},
                ],
            })
            result = tracker.monitor_compliance()
            assert result["active_orders_scanned"] == 1
            assert result["total_provisions_checked"] == 1
        finally:
            tracker.close()

    def test_detect_all_conflicts_empty(self, tracker_db_path):
        tracker = CourtOrderTracker(db_path=tracker_db_path)
        try:
            result = tracker.detect_all_conflicts()
            assert result["active_orders"] == 0
            assert result["conflicts"] == []
        finally:
            tracker.close()

    def test_detect_all_conflicts_with_data(self, tracker_db_path):
        tracker = CourtOrderTracker(db_path=tracker_db_path)
        try:
            tracker.catalog_order({
                "case_number": "1", "case_lane": "A",
                "order_type": "TEMPORARY",
                "date_entered": "2024-01-01",
                "provisions": [{"description": "Joint legal custody"}],
            })
            tracker.catalog_order({
                "case_number": "1", "case_lane": "A",
                "order_type": "TEMPORARY",
                "date_entered": "2024-06-01",
                "provisions": [{"description": "Sole legal custody to mother"}],
            })
            result = tracker.detect_all_conflicts()
            assert result["active_orders"] == 2
        finally:
            tracker.close()

    def test_generate_order_report(self, tracker_db_path):
        tracker = CourtOrderTracker(db_path=tracker_db_path)
        try:
            tracker.catalog_order({
                "case_number": "2024-001507-DC", "case_lane": "A",
                "order_type": "TEMPORARY",
                "date_entered": "2024-06-15",
            })
            report = tracker.generate_order_report()
            assert "COURT ORDER STATUS REPORT" in report
            assert "Lane A" in report
        finally:
            tracker.close()

    def test_get_stats(self, tracker_db_path):
        tracker = CourtOrderTracker(db_path=tracker_db_path)
        try:
            stats = tracker.get_stats()
            assert "engine_version" in stats
            assert stats["engine_version"] == "1.0.0"
            assert "total_orders" in stats
        finally:
            tracker.close()

    def test_close_idempotent(self, tracker_db_path):
        tracker = CourtOrderTracker(db_path=tracker_db_path)
        tracker._init_db()
        tracker.close()
        tracker.close()  # should not raise

    def test_lane_routing_all_lanes(self, tracker_db_path):
        tracker = CourtOrderTracker(db_path=tracker_db_path)
        try:
            for lane in ["A", "B", "C", "D", "E", "F"]:
                tracker.catalog_order({
                    "case_number": CASE_LANES[lane]["case_number"],
                    "case_lane": lane,
                    "order_type": "TEMPORARY",
                    "date_entered": "2024-01-01",
                })
            all_orders = tracker.get_all_orders()
            assert len(all_orders) == 6
            lanes = {o.case_lane for o in all_orders}
            assert lanes == {"A", "B", "C", "D", "E", "F"}
        finally:
            tracker.close()


# ═══════════════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════════════

class TestEdgeCases:

    def test_empty_orders_list_conflicts(self):
        detector = OrderConflictDetector()
        assert detector.detect_conflicts([]) == []

    def test_empty_orders_supersession(self):
        detector = OrderConflictDetector()
        assert detector.detect_superseded_orders([]) == []

    def test_empty_orders_ex_parte(self):
        detector = OrderConflictDetector()
        assert detector.detect_ex_parte_orders([]) == []

    def test_single_order_no_conflicts(self):
        detector = OrderConflictDetector()
        order = CourtOrder(
            status=OrderStatus.ACTIVE,
            provisions=[OrderProvision(description="Custody provision")],
        )
        assert detector.detect_conflicts([order]) == []

    def test_order_with_many_provisions(self, tracker_db_path):
        tracker = CourtOrderTracker(db_path=tracker_db_path)
        try:
            provisions = [
                {"description": f"Provision {i}",
                 "compliance_status": "UNKNOWN"}
                for i in range(20)
            ]
            order = tracker.catalog_order({
                "case_number": "1", "order_type": "CUSTODY",
                "date_entered": "2024-01-01",
                "provisions": provisions,
            })
            assert len(order.provisions) == 20
        finally:
            tracker.close()

    def test_conflicting_provisions_same_party(self):
        detector = OrderConflictDetector()
        o1 = CourtOrder(
            order_id="o1", status=OrderStatus.ACTIVE,
            provisions=[OrderProvision(
                description="Mother has sole custody",
                responsible_party="Watson",
            )],
        )
        o2 = CourtOrder(
            order_id="o2", status=OrderStatus.ACTIVE,
            provisions=[OrderProvision(
                description="Joint custody arrangement",
                responsible_party="Watson",
            )],
        )
        conflicts = detector.detect_conflicts([o1, o2])
        assert len(conflicts) >= 1

    def test_superseded_chain(self, tracker_db_path):
        tracker = CourtOrderTracker(db_path=tracker_db_path)
        try:
            for i in range(5):
                tracker.catalog_order({
                    "case_number": "1",
                    "case_lane": "A",
                    "order_type": "TEMPORARY",
                    "date_entered": f"2024-0{i+1}-01",
                })
            all_orders = tracker.get_all_orders()
            assert len(all_orders) == 5
            detector = OrderConflictDetector()
            issues = detector.detect_superseded_orders(all_orders)
            assert len(issues) >= 4  # 4 older orders could be superseded
        finally:
            tracker.close()

    def test_order_expiry_date_calculations(self):
        expires_yesterday = (date.today() - timedelta(days=1)).isoformat()
        expires_tomorrow = (date.today() + timedelta(days=1)).isoformat()

        o_past = CourtOrder(
            status=OrderStatus.ACTIVE, date_expires=expires_yesterday,
        )
        o_future = CourtOrder(
            status=OrderStatus.ACTIVE, date_expires=expires_tomorrow,
        )
        assert o_past.is_active() is False
        assert o_past.is_expired() is True
        assert o_future.is_active() is True
        assert o_future.is_expired() is False
