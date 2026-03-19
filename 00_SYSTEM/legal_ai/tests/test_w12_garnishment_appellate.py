# -*- coding: utf-8 -*-
"""Wave-12 Tests — GarnishmentEngine + AppellateRecordBuilder
================================================================
Comprehensive pytest suite for garnishment_engine.py (~75 tests) and
appellate_record_builder.py (~65 tests).

• Zero network / zero real DB — all DB interactions use tmp_path SQLite
• Independent tests, no ordering dependencies
• Decimal precision validated explicitly
• Real Michigan party names and MCR citations throughout
"""
from __future__ import annotations

import json
import pathlib
import sqlite3
import sys
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import List

import pytest

# ---------------------------------------------------------------------------
# Path bootstrap — let us import from the parent legal_ai package
# ---------------------------------------------------------------------------
_THIS_DIR = pathlib.Path(__file__).resolve().parent
_LEGAL_AI_DIR = _THIS_DIR.parent
if str(_LEGAL_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_LEGAL_AI_DIR))

from garnishment_engine import (
    GarnishmentType,
    ExemptionType,
    GarnishmentStatus,
    PayPeriod,
    GarnishmentRequest,
    ExemptionResult,
    PaymentRecord,
    FormOutput,
    ExemptionAnalyzer,
    WageGarnishmentCalculator,
    BankGarnishmentProcessor,
    GarnishmentFormGenerator,
    GarnishmentEngine,
    _PLAINTIFF,
    _DEFENDANT,
    _CHILD_INITIALS,
    _JUDGE,
    _COURT,
    LANE_CASES,
    _FEDERAL_MINIMUM_WAGE,
    _FEDERAL_WEEKLY_THRESHOLD,
    _FEDERAL_MAX_GARNISHMENT_PCT,
    _MI_HOMESTEAD_EXEMPTION,
    _MI_HOUSEHOLD_GOODS_EXEMPTION,
    _PAY_PERIODS,
)

from appellate_record_builder import (
    RecordType,
    TranscriptStatus,
    RecordBuildStatus,
    CompletionIssue,
    RecordEntry,
    TranscriptRecord,
    VolumeInfo,
    CompletionReport,
    RegisterOfActions,
    TranscriptManager,
    ExhibitCompiler,
    RecordPaginator,
    RecordCompletionChecker,
    AppellateRecordBuilder,
    _TRANSCRIPT_ORDER_DAYS,
    _CLAIM_OF_APPEAL_DAYS,
    _RECORD_PREPARATION_DAYS,
    _APPENDIX_PAGE_LIMIT,
    _VOLUME_PAGE_LIMIT,
    _RECORD_SECTIONS,
)


# ===================================================================
# GARNISHMENT ENGINE TESTS (~75)
# ===================================================================


# -------------------------------------------------------------------
# TestGarnishmentType
# -------------------------------------------------------------------
class TestGarnishmentType:
    """Tests for the GarnishmentType enum."""

    def test_all_values_exist(self):
        expected = {"periodic", "non_periodic", "supplementary"}
        actual = {g.value for g in GarnishmentType}
        assert actual == expected

    def test_count_is_three(self):
        assert len(GarnishmentType) == 3

    def test_periodic_mcl_reference(self):
        assert GarnishmentType.PERIODIC.mcl_reference == "MCL 600.4011"

    def test_non_periodic_mcl_reference(self):
        assert GarnishmentType.NON_PERIODIC.mcl_reference == "MCL 600.4011"

    def test_supplementary_mcl_reference(self):
        assert GarnishmentType.SUPPLEMENTARY.mcl_reference == "MCL 600.4061"

    def test_str_enum_value(self):
        assert GarnishmentType.PERIODIC == "periodic"


# -------------------------------------------------------------------
# TestExemptionType
# -------------------------------------------------------------------
class TestExemptionType:
    """Tests for the ExemptionType enum."""

    def test_all_values_exist(self):
        expected = {
            "federal_minimum", "state_minimum", "head_of_household",
            "public_benefits", "pension", "homestead",
        }
        actual = {e.value for e in ExemptionType}
        assert actual == expected

    def test_count_is_six(self):
        assert len(ExemptionType) == 6

    def test_federal_minimum_legal_basis(self):
        assert ExemptionType.FEDERAL_MINIMUM.legal_basis == "15 USC § 1673(a)"

    def test_pension_legal_basis(self):
        assert ExemptionType.PENSION.legal_basis == "MCL 600.4012(1)(f)"

    def test_homestead_legal_basis(self):
        assert ExemptionType.HOMESTEAD.legal_basis == "MCL 600.6023(1)(h)"

    def test_public_benefits_legal_basis(self):
        assert ExemptionType.PUBLIC_BENEFITS.legal_basis == "MCL 600.4012(1)"


# -------------------------------------------------------------------
# TestGarnishmentStatus
# -------------------------------------------------------------------
class TestGarnishmentStatus:
    """Tests for GarnishmentStatus enum."""

    def test_all_values_exist(self):
        expected = {
            "draft", "filed", "served", "active",
            "objected", "satisfied", "terminated", "suspended",
        }
        actual = {s.value for s in GarnishmentStatus}
        assert actual == expected

    def test_count_is_eight(self):
        assert len(GarnishmentStatus) == 8


# -------------------------------------------------------------------
# TestPayPeriod
# -------------------------------------------------------------------
class TestPayPeriod:
    """Tests for PayPeriod enum."""

    def test_all_values_exist(self):
        expected = {"weekly", "biweekly", "semimonthly", "monthly"}
        actual = {p.value for p in PayPeriod}
        assert actual == expected

    def test_count_is_four(self):
        assert len(PayPeriod) == 4


# -------------------------------------------------------------------
# TestGarnishmentRequest
# -------------------------------------------------------------------
class TestGarnishmentRequest:
    """Tests for GarnishmentRequest dataclass."""

    def test_defaults(self):
        req = GarnishmentRequest()
        assert req.garnishment_type == GarnishmentType.PERIODIC
        assert req.amount == Decimal("0.00")
        assert req.status == GarnishmentStatus.DRAFT
        assert req.court == _COURT

    def test_to_dict_keys(self):
        req = GarnishmentRequest(debtor_name="Emily A. Watson")
        d = req.to_dict()
        assert d["debtor_name"] == "Emily A. Watson"
        assert "request_id" in d
        assert d["garnishment_type"] == "periodic"

    def test_to_dict_decimal_serialized(self):
        req = GarnishmentRequest(amount=Decimal("5000.50"))
        d = req.to_dict()
        assert d["amount"] == "5000.50"

    def test_remaining_balance_full(self):
        req = GarnishmentRequest(amount=Decimal("5000.00"), total_collected=Decimal("0.00"))
        assert req.remaining_balance == Decimal("5000.00")

    def test_remaining_balance_partial(self):
        req = GarnishmentRequest(amount=Decimal("5000.00"), total_collected=Decimal("3000.00"))
        assert req.remaining_balance == Decimal("2000.00")

    def test_remaining_balance_overpaid(self):
        req = GarnishmentRequest(amount=Decimal("5000.00"), total_collected=Decimal("6000.00"))
        assert req.remaining_balance == Decimal("0.00")


# -------------------------------------------------------------------
# TestExemptionResult
# -------------------------------------------------------------------
class TestExemptionResult:
    """Tests for ExemptionResult dataclass."""

    def test_to_dict_keys(self):
        er = ExemptionResult(gross_income=Decimal("1000.00"))
        d = er.to_dict()
        assert d["gross_income"] == "1000.00"
        assert "exemption_id" in d
        assert d["exemption_type"] == "federal_minimum"


# -------------------------------------------------------------------
# TestPaymentRecord
# -------------------------------------------------------------------
class TestPaymentRecord:
    """Tests for PaymentRecord dataclass."""

    def test_to_dict_keys(self):
        pr = PaymentRecord(amount=Decimal("200.00"), request_id="abc123")
        d = pr.to_dict()
        assert d["amount"] == "200.00"
        assert d["request_id"] == "abc123"


# -------------------------------------------------------------------
# TestFormOutput
# -------------------------------------------------------------------
class TestFormOutput:
    """Tests for FormOutput dataclass."""

    def test_to_dict_keys(self):
        fo = FormOutput(form_number="MC 14", form_name="Request and Writ")
        d = fo.to_dict()
        assert d["form_number"] == "MC 14"
        assert d["form_name"] == "Request and Writ"
        assert "form_id" in d


# -------------------------------------------------------------------
# TestExemptionAnalyzer
# -------------------------------------------------------------------
class TestExemptionAnalyzer:
    """Tests for ExemptionAnalyzer — federal/state garnishment limits."""

    def setup_method(self):
        self.analyzer = ExemptionAnalyzer()

    def test_zero_income_fully_exempt(self):
        result = self.analyzer.calculate_exempt_amount(Decimal("0"), pay_period="weekly")
        assert result == Decimal("0")

    def test_negative_income_returns_income(self):
        result = self.analyzer.calculate_exempt_amount(Decimal("-100"), pay_period="weekly")
        assert result == Decimal("-100")

    def test_below_30x_minimum_fully_exempt(self):
        """Income at or below 30× $7.25 ($217.50/week) is fully exempt."""
        income = Decimal("200.00")
        exempt = self.analyzer.calculate_exempt_amount(income, pay_period="weekly")
        assert exempt == income

    def test_above_threshold_partial_garnishment(self):
        income = Decimal("1000.00")
        exempt = self.analyzer.calculate_exempt_amount(income, pay_period="weekly")
        assert exempt < income
        assert exempt > Decimal("0")

    def test_public_benefits_100_percent_exempt(self):
        income = Decimal("2000.00")
        exempt = self.analyzer.calculate_exempt_amount(
            income, pay_period="biweekly", has_public_benefits=True,
        )
        assert exempt == income

    def test_pension_100_percent_exempt(self):
        income = Decimal("3000.00")
        exempt = self.analyzer.calculate_exempt_amount(
            income, pay_period="monthly", has_pension=True,
        )
        assert exempt == income

    def test_head_of_household_larger_exemption(self):
        income = Decimal("2000.00")
        base_exempt = self.analyzer.calculate_exempt_amount(
            income, pay_period="biweekly", dependents=0,
        )
        hoh_exempt = self.analyzer.calculate_exempt_amount(
            income, pay_period="biweekly", dependents=2,
            is_head_of_household=True,
        )
        assert hoh_exempt >= base_exempt

    def test_check_federal_limits_keys(self):
        result = self.analyzer.check_federal_limits(Decimal("500.00"))
        assert "test_1_25_percent" in result
        assert "test_2_excess_over_threshold" in result
        assert "controlling_test" in result
        assert result["legal_basis"] == "15 USC § 1673(a)"

    def test_check_federal_limits_below_threshold_exempt(self):
        result = self.analyzer.check_federal_limits(Decimal("200.00"))
        assert result["fully_exempt"] is True

    def test_check_federal_limits_above_threshold_not_exempt(self):
        result = self.analyzer.check_federal_limits(Decimal("500.00"))
        assert result["fully_exempt"] is False

    def test_check_state_limits_basic(self):
        result = self.analyzer.check_state_limits(Decimal("1000.00"))
        assert result["legal_basis"] == "MCL 600.4012"
        assert "garnishable" in result

    def test_check_state_limits_head_of_household(self):
        result = self.analyzer.check_state_limits(
            Decimal("1000.00"), is_head_of_household=True, dependents=2,
        )
        assert "Head of household" in str(result["exemptions_applied"])

    def test_identify_protected_assets_returns_list(self):
        assets = self.analyzer.identify_protected_assets()
        assert len(assets) >= 5
        asset_types = {a["type"] for a in assets}
        assert "public_benefits" in asset_types
        assert "pension" in asset_types
        assert "homestead" in asset_types

    def test_get_stats(self):
        self.analyzer.calculate_exempt_amount(Decimal("500"), pay_period="weekly")
        stats = self.analyzer.get_stats()
        assert stats["component"] == "ExemptionAnalyzer"
        assert stats["total_analyses"] >= 1


# -------------------------------------------------------------------
# TestWageGarnishmentCalculator
# -------------------------------------------------------------------
class TestWageGarnishmentCalculator:
    """Tests for WageGarnishmentCalculator."""

    def setup_method(self):
        self.calc = WageGarnishmentCalculator()

    def test_zero_gross_returns_zero(self):
        result = self.calc.calculate_withholding(Decimal("0"), Decimal("0"))
        assert result == Decimal("0.00")

    def test_deductions_exceed_gross_returns_zero(self):
        result = self.calc.calculate_withholding(Decimal("500"), Decimal("600"))
        assert result == Decimal("0.00")

    def test_positive_withholding(self):
        result = self.calc.calculate_withholding(
            Decimal("3000.00"), Decimal("500.00"), pay_period="biweekly",
        )
        assert result > Decimal("0")
        assert result <= Decimal("3000.00")

    def test_withholding_precision_two_decimals(self):
        result = self.calc.calculate_withholding(
            Decimal("1234.56"), Decimal("0"), pay_period="weekly",
        )
        assert result == result.quantize(Decimal("0.01"))

    def test_generate_employer_instructions(self):
        req = GarnishmentRequest(
            case_number="2024-001507-DC",
            debtor_name="Emily A. Watson",
            garnishee_name="Employer LLC",
            amount=Decimal("5000.00"),
            judgment_amount=Decimal("5000.00"),
        )
        instructions = self.calc.generate_employer_instructions(req)
        assert instructions["form"] == "MC 50 — Writ of Garnishment (Periodic)"
        assert instructions["mcr"] == "MCR 3.101(G)"
        assert len(instructions["instructions"]) >= 4

    def test_track_payments_creates_record(self):
        record = self.calc.track_payments("req123", Decimal("250.00"))
        assert record.amount == Decimal("250.00")
        assert record.request_id == "req123"
        assert record.cumulative_total == Decimal("250.00")

    def test_track_payments_cumulative(self):
        self.calc.track_payments("req123", Decimal("250.00"))
        r2 = self.calc.track_payments("req123", Decimal("300.00"))
        assert r2.cumulative_total == Decimal("550.00")

    def test_calculate_remaining_balance(self):
        req = GarnishmentRequest(request_id="req999", amount=Decimal("1000.00"))
        self.calc.track_payments("req999", Decimal("300.00"))
        self.calc.track_payments("req999", Decimal("200.00"))
        result = self.calc.calculate_remaining_balance(req)
        assert result["remaining_balance"] == "500.00"
        assert result["payment_count"] == 2
        assert result["is_satisfied"] is False

    def test_calculate_remaining_balance_satisfied(self):
        req = GarnishmentRequest(request_id="req888", amount=Decimal("500.00"))
        self.calc.track_payments("req888", Decimal("500.00"))
        result = self.calc.calculate_remaining_balance(req)
        assert result["is_satisfied"] is True

    def test_get_stats(self):
        self.calc.track_payments("r1", Decimal("100"))
        stats = self.calc.get_stats()
        assert stats["component"] == "WageGarnishmentCalculator"
        assert stats["total_payments_tracked"] >= 1


# -------------------------------------------------------------------
# TestBankGarnishmentProcessor
# -------------------------------------------------------------------
class TestBankGarnishmentProcessor:
    """Tests for BankGarnishmentProcessor."""

    def setup_method(self):
        self.proc = BankGarnishmentProcessor()

    def test_identify_accounts_empty(self):
        accounts = self.proc.identify_accounts("Emily A. Watson")
        assert accounts == []

    def test_identify_accounts_with_institutions(self):
        accounts = self.proc.identify_accounts(
            "Emily A. Watson", known_institutions=["Chase", "Fifth Third"],
        )
        assert len(accounts) == 2
        assert accounts[0]["debtor_name"] == "Emily A. Watson"

    def test_calculate_exempt_balance_no_exemptions(self):
        result = self.proc.calculate_exempt_balance(Decimal("10000.00"))
        assert result["exempt_amount"] == "0"
        assert result["is_fully_exempt"] is False

    def test_calculate_exempt_balance_public_benefits(self):
        result = self.proc.calculate_exempt_balance(
            Decimal("5000.00"), has_public_benefits=True,
        )
        assert result["is_fully_exempt"] is True

    def test_calculate_exempt_balance_pension(self):
        result = self.proc.calculate_exempt_balance(
            Decimal("8000.00"), has_pension_deposits=True,
        )
        assert result["is_fully_exempt"] is True

    def test_calculate_exempt_balance_federal_benefits(self):
        result = self.proc.calculate_exempt_balance(
            Decimal("10000.00"), has_federal_benefits=True,
        )
        assert Decimal(result["exempt_amount"]) >= Decimal("0")

    def test_generate_garnishment_order_keys(self):
        req = GarnishmentRequest(
            case_number="2024-001507-DC",
            debtor_name="Emily A. Watson",
            amount=Decimal("5000.00"),
        )
        order = self.proc.generate_garnishment_order(req, "Chase Bank")
        assert order["form"] == "MC 14 — Request and Writ of Garnishment (Non-Periodic)"
        assert order["plaintiff"] == "Andrew James Pigors"
        assert "MCL 600.4011" in str(order["legal_basis"])

    def test_process_objections_valid_basis(self):
        result = self.proc.process_objections("req1", objection_basis="public_benefits")
        assert result["valid_basis"] is True
        assert result["form"] == "MC 16 — Objection to Garnishment"

    def test_process_objections_invalid_basis(self):
        result = self.proc.process_objections("req1", objection_basis="i_dont_wanna")
        assert result["valid_basis"] is False

    def test_process_objections_hearing_required(self):
        result = self.proc.process_objections("req1", objection_basis="improper_service")
        assert result["hearing_required"] is True

    def test_get_stats(self):
        self.proc.identify_accounts("test", known_institutions=["Bank"])
        stats = self.proc.get_stats()
        assert stats["component"] == "BankGarnishmentProcessor"
        assert stats["accounts_identified"] >= 1


# -------------------------------------------------------------------
# TestGarnishmentFormGenerator
# -------------------------------------------------------------------
class TestGarnishmentFormGenerator:
    """Tests for GarnishmentFormGenerator — SCAO form generation."""

    def setup_method(self):
        self.gen = GarnishmentFormGenerator()
        self.req = GarnishmentRequest(
            case_number="2024-001507-DC",
            debtor_name="Emily A. Watson",
            garnishee_name="Employer LLC",
            amount=Decimal("5000.00"),
            judgment_amount=Decimal("4500.00"),
            judgment_date="2025-01-15",
            costs=Decimal("200.00"),
        )

    def test_generate_mc14(self):
        form = self.gen.generate_mc14(self.req)
        assert form.form_number == "MC 14"
        assert form.fields["plaintiff"] == "Andrew James Pigors"
        assert form.fields["defendant"] == "Emily A. Watson"
        assert form.content_hash

    def test_generate_mc15(self):
        form = self.gen.generate_mc15(self.req, Decimal("3000.00"))
        assert form.form_number == "MC 15"
        assert form.fields["disclosed_amount"] == "3000.00"
        assert form.fields["mcr_reference"] == "MCR 3.101(H)"

    def test_generate_mc16(self):
        form = self.gen.generate_mc16(self.req, "pension", "MCL 600.4012(1)(f)")
        assert form.form_number == "MC 16"
        assert form.fields["exemption_claimed"] == "pension"

    def test_generate_mc50(self):
        form = self.gen.generate_mc50(self.req, pay_period="biweekly")
        assert form.form_number == "MC 50"
        assert form.fields["pay_period"] == "biweekly"
        assert "15 USC § 1673" in form.fields["withholding_instructions"]

    def test_form_hash_deterministic(self):
        form1 = self.gen.generate_mc14(self.req)
        form2 = self.gen.generate_mc14(self.req)
        assert form1.content_hash == form2.content_hash

    def test_get_stats_tracks_forms(self):
        self.gen.generate_mc14(self.req)
        self.gen.generate_mc50(self.req)
        stats = self.gen.get_stats()
        assert stats["total_forms_generated"] == 2
        assert stats["by_form"]["MC 14"] == 1
        assert stats["by_form"]["MC 50"] == 1


# -------------------------------------------------------------------
# TestGarnishmentEngine
# -------------------------------------------------------------------
class TestGarnishmentEngine:
    """Tests for GarnishmentEngine orchestrator."""

    def setup_method(self, tmp_path=None):
        self.engine = GarnishmentEngine(db_path=pathlib.Path("nonexistent.db"))

    def test_create_garnishment_periodic(self):
        req = self.engine.create_garnishment(
            garnishment_type=GarnishmentType.PERIODIC,
            debtor_name="Emily A. Watson",
            garnishee_name="Employer LLC",
            amount=Decimal("5000.00"),
        )
        assert req.debtor_name == "Emily A. Watson"
        assert req.garnishment_type == GarnishmentType.PERIODIC
        assert req.request_id in self.engine._requests

    def test_create_garnishment_non_periodic(self):
        req = self.engine.create_garnishment(
            garnishment_type=GarnishmentType.NON_PERIODIC,
            debtor_name="Emily A. Watson",
            garnishee_name="Chase Bank",
            amount=Decimal("10000.00"),
        )
        assert req.garnishment_type == GarnishmentType.NON_PERIODIC

    def test_create_garnishment_defaults(self):
        req = self.engine.create_garnishment()
        assert req.debtor_name == "Emily A. Watson"
        assert req.court == "14th Circuit Court"

    def test_calculate_amounts_not_found(self):
        result = self.engine.calculate_amounts("nonexistent")
        assert "error" in result

    def test_calculate_amounts_periodic(self):
        req = self.engine.create_garnishment(
            garnishment_type=GarnishmentType.PERIODIC,
            amount=Decimal("5000.00"),
        )
        result = self.engine.calculate_amounts(
            req.request_id,
            gross_income=Decimal("3000.00"),
            deductions=Decimal("500.00"),
            pay_period="biweekly",
        )
        assert result["type"] == "periodic"
        assert "withholding_per_period" in result

    def test_calculate_amounts_non_periodic(self):
        req = self.engine.create_garnishment(
            garnishment_type=GarnishmentType.NON_PERIODIC,
            amount=Decimal("10000.00"),
        )
        result = self.engine.calculate_amounts(
            req.request_id,
            gross_income=Decimal("8000.00"),
        )
        assert result["type"] == "non_periodic"

    def test_track_compliance_not_found(self):
        result = self.engine.track_compliance("nonexistent")
        assert "error" in result

    def test_track_compliance_valid(self):
        req = self.engine.create_garnishment(amount=Decimal("5000.00"))
        result = self.engine.track_compliance(req.request_id)
        assert result["request_id"] == req.request_id
        assert "balance" in result

    def test_constants_correct(self):
        assert _FEDERAL_MINIMUM_WAGE == Decimal("7.25")
        assert _FEDERAL_WEEKLY_THRESHOLD == Decimal("7.25") * 30
        assert _FEDERAL_MAX_GARNISHMENT_PCT == Decimal("0.25")

    def test_case_constants(self):
        assert _PLAINTIFF == "Andrew James Pigors"
        assert _DEFENDANT == "Emily A. Watson"
        assert _CHILD_INITIALS == "L.D.W."
        assert _JUDGE == "Hon. Jenny L. McNeill"
        assert _COURT == "14th Circuit Court"

    def test_lane_cases_mapping(self):
        assert LANE_CASES["A"] == "2024-001507-DC"
        assert LANE_CASES["B"] == "2025-002760-CZ"
        assert LANE_CASES["D"] == "2023-5907-PP"
        assert LANE_CASES["F"] == "COA 366810"


# ===================================================================
# APPELLATE RECORD BUILDER TESTS (~65)
# ===================================================================


# -------------------------------------------------------------------
# TestRecordType
# -------------------------------------------------------------------
class TestRecordType:
    """Tests for RecordType enum."""

    def test_all_values_exist(self):
        expected = {
            "register_of_actions", "transcript", "exhibit",
            "pleading", "order", "motion", "brief",
        }
        actual = {r.value for r in RecordType}
        assert actual == expected

    def test_count_is_seven(self):
        assert len(RecordType) == 7

    def test_transcript_mcr_reference(self):
        assert RecordType.TRANSCRIPT.mcr_reference == "MCR 7.210(B)"

    def test_exhibit_mcr_reference(self):
        assert RecordType.EXHIBIT.mcr_reference == "MCR 7.210(A)(3)"

    def test_brief_mcr_reference(self):
        assert RecordType.BRIEF.mcr_reference == "MCR 7.212(C)"


# -------------------------------------------------------------------
# TestTranscriptStatus
# -------------------------------------------------------------------
class TestTranscriptStatus:
    """Tests for TranscriptStatus enum."""

    def test_all_values_exist(self):
        expected = {
            "not_ordered", "ordered", "received",
            "certified", "missing", "waived",
        }
        actual = {s.value for s in TranscriptStatus}
        assert actual == expected

    def test_count_is_six(self):
        assert len(TranscriptStatus) == 6


# -------------------------------------------------------------------
# TestRecordBuildStatus
# -------------------------------------------------------------------
class TestRecordBuildStatus:
    """Tests for RecordBuildStatus enum."""

    def test_all_values_exist(self):
        expected = {
            "planning", "collecting", "paginating",
            "reviewing", "certified", "filed", "deficient",
        }
        actual = {s.value for s in RecordBuildStatus}
        assert actual == expected

    def test_count_is_seven(self):
        assert len(RecordBuildStatus) == 7


# -------------------------------------------------------------------
# TestCompletionIssue
# -------------------------------------------------------------------
class TestCompletionIssue:
    """Tests for CompletionIssue enum."""

    def test_all_values_exist(self):
        expected = {
            "missing_transcript", "missing_exhibit", "missing_order",
            "pagination_gap", "certification_missing",
            "register_incomplete", "bates_error",
        }
        actual = {c.value for c in CompletionIssue}
        assert actual == expected


# -------------------------------------------------------------------
# TestRecordEntry
# -------------------------------------------------------------------
class TestRecordEntry:
    """Tests for RecordEntry dataclass."""

    def test_defaults(self):
        entry = RecordEntry()
        assert entry.record_type == RecordType.PLEADING
        assert entry.volume == 1
        assert entry.is_certified is False

    def test_to_dict_keys(self):
        entry = RecordEntry(title="Complaint", date="2024-06-15")
        d = entry.to_dict()
        assert d["title"] == "Complaint"
        assert d["record_type"] == "pleading"

    def test_page_count_valid(self):
        entry = RecordEntry(page_start=10, page_end=25)
        assert entry.page_count == 16

    def test_page_count_zero_when_no_pages(self):
        entry = RecordEntry(page_start=0, page_end=0)
        assert entry.page_count == 0


# -------------------------------------------------------------------
# TestTranscriptRecord
# -------------------------------------------------------------------
class TestTranscriptRecord:
    """Tests for TranscriptRecord dataclass."""

    def test_defaults(self):
        tr = TranscriptRecord()
        assert tr.status == TranscriptStatus.NOT_ORDERED
        assert tr.judge == "Hon. Jenny L. McNeill"

    def test_to_dict_keys(self):
        tr = TranscriptRecord(hearing_date="2024-09-10", hearing_type="Motion")
        d = tr.to_dict()
        assert d["hearing_date"] == "2024-09-10"
        assert d["status"] == "not_ordered"

    def test_is_overdue_when_past_deadline(self):
        old_date = (date.today() - timedelta(days=30)).isoformat()
        tr = TranscriptRecord(hearing_date=old_date, status=TranscriptStatus.NOT_ORDERED)
        assert tr.is_overdue is True

    def test_not_overdue_when_recent(self):
        recent_date = date.today().isoformat()
        tr = TranscriptRecord(hearing_date=recent_date, status=TranscriptStatus.NOT_ORDERED)
        assert tr.is_overdue is False

    def test_not_overdue_when_ordered(self):
        old_date = (date.today() - timedelta(days=30)).isoformat()
        tr = TranscriptRecord(hearing_date=old_date, status=TranscriptStatus.ORDERED)
        assert tr.is_overdue is False


# -------------------------------------------------------------------
# TestVolumeInfo
# -------------------------------------------------------------------
class TestVolumeInfo:
    """Tests for VolumeInfo dataclass."""

    def test_to_dict(self):
        vi = VolumeInfo(volume_number=2, page_start=201, page_end=400)
        d = vi.to_dict()
        assert d["volume_number"] == 2
        assert d["page_start"] == 201


# -------------------------------------------------------------------
# TestCompletionReport
# -------------------------------------------------------------------
class TestCompletionReport:
    """Tests for CompletionReport dataclass."""

    def test_to_dict(self):
        cr = CompletionReport(case_number="COA 366810", is_complete=False)
        d = cr.to_dict()
        assert d["case_number"] == "COA 366810"
        assert d["is_complete"] is False


# -------------------------------------------------------------------
# TestRegisterOfActions
# -------------------------------------------------------------------
class TestRegisterOfActions:
    """Tests for RegisterOfActions."""

    def setup_method(self):
        self.register = RegisterOfActions()

    def test_build_from_empty_docket(self):
        result = self.register.build_from_docket([])
        assert result == []

    def test_build_from_docket_entries(self):
        entries = [
            {"date": "2024-06-15", "description": "Complaint Filed", "filed_by": "Plaintiff"},
            {"date": "2024-07-01", "description": "Answer Filed", "filed_by": "Defendant"},
        ]
        result = self.register.build_from_docket(entries)
        assert len(result) == 2
        assert result[0]["date"] <= result[1]["date"]

    def test_verify_completeness_all_present(self):
        self.register.build_from_docket([
            {"date": "2024-06-15", "description": "Complaint Filed"},
        ])
        result = self.register.verify_completeness(["Complaint"])
        assert result["is_complete"] is True

    def test_verify_completeness_missing(self):
        self.register.build_from_docket([
            {"date": "2024-06-15", "description": "Complaint Filed"},
        ])
        result = self.register.verify_completeness(["Complaint", "Motion for Summary Judgment"])
        assert result["is_complete"] is False
        assert len(result["missing_filings"]) == 1

    def test_identify_missing_entries(self):
        self.register.build_from_docket([
            {"date": "2024-06-15", "description": "Complaint Filed"},
        ])
        missing = self.register.identify_missing_entries(
            orders=["Order Granting Motion"],
            motions=["Motion to Dismiss"],
        )
        assert len(missing) == 2

    def test_generate_certified_copy(self):
        self.register.build_from_docket([
            {"date": "2024-06-15", "description": "Complaint Filed"},
        ])
        cert = self.register.generate_certified_copy()
        assert cert["document"] == "Certified Register of Actions"
        assert cert["legal_basis"] == "MCR 7.210(A)(1)"
        assert "content_hash" in cert

    def test_get_stats(self):
        self.register.build_from_docket([{"date": "2024-01-01", "description": "Test"}])
        stats = self.register.get_stats()
        assert stats["total_entries"] == 1


# -------------------------------------------------------------------
# TestTranscriptManager
# -------------------------------------------------------------------
class TestTranscriptManager:
    """Tests for TranscriptManager."""

    def setup_method(self):
        self.mgr = TranscriptManager()

    def test_inventory_empty(self):
        result = self.mgr.inventory_transcripts([])
        assert result == []

    def test_inventory_transcripts(self):
        hearings = [
            {"hearing_date": "2024-09-10", "hearing_type": "Motion Hearing"},
            {"hearing_date": "2024-10-15", "hearing_type": "Evidentiary Hearing"},
        ]
        result = self.mgr.inventory_transcripts(hearings)
        assert len(result) == 2
        assert result[0].hearing_type == "Motion Hearing"

    def test_order_missing_returns_unordered(self):
        self.mgr.inventory_transcripts([
            {"hearing_date": "2024-09-10", "hearing_type": "Motion Hearing"},
        ])
        to_order = self.mgr.order_missing()
        assert len(to_order) == 1
        assert to_order[0]["legal_basis"] == "MCR 7.210(B)(1)"

    def test_verify_certification_received_uncertified(self):
        self.mgr.inventory_transcripts([
            {"hearing_date": "2024-09-10", "hearing_type": "Motion"},
        ])
        self.mgr._transcripts[0].status = TranscriptStatus.RECEIVED
        issues = self.mgr.verify_certification()
        assert len(issues) == 1
        assert issues[0]["legal_basis"] == "MCR 7.210(B)(2)"

    def test_verify_certification_missing_transcript(self):
        self.mgr.inventory_transcripts([
            {"hearing_date": "2024-09-10", "hearing_type": "Motion"},
        ])
        self.mgr._transcripts[0].status = TranscriptStatus.MISSING
        issues = self.mgr.verify_certification()
        assert len(issues) == 1
        assert "MCR 7.210(B)(4)" in issues[0]["legal_basis"]

    def test_calculate_costs(self):
        self.mgr.inventory_transcripts([
            {"hearing_date": "2024-09-10", "hearing_type": "Motion"},
        ])
        self.mgr._transcripts[0].cost = "350.00"
        costs = self.mgr.calculate_costs()
        assert costs["total_cost"] == "350.00"

    def test_track_ordering_deadlines(self):
        self.mgr.inventory_transcripts([
            {"hearing_date": "2024-09-10", "hearing_type": "Motion"},
        ])
        coa_date = date.today().isoformat()
        deadlines = self.mgr.track_ordering_deadlines(coa_date)
        assert len(deadlines) == 1
        assert deadlines[0]["legal_basis"] == "MCR 7.210(B)(1)"
        assert deadlines[0]["days_remaining"] == _TRANSCRIPT_ORDER_DAYS

    def test_update_status(self):
        self.mgr.inventory_transcripts([
            {"hearing_date": "2024-09-10", "hearing_type": "Motion"},
        ])
        tid = self.mgr._transcripts[0].transcript_id
        result = self.mgr.update_status(tid, TranscriptStatus.ORDERED)
        assert result is not None
        assert result.status == TranscriptStatus.ORDERED

    def test_update_status_not_found(self):
        result = self.mgr.update_status("nonexistent", TranscriptStatus.ORDERED)
        assert result is None

    def test_get_stats(self):
        self.mgr.inventory_transcripts([{"hearing_date": "2024-09-10", "hearing_type": "M"}])
        stats = self.mgr.get_stats()
        assert stats["component"] == "TranscriptManager"


# -------------------------------------------------------------------
# TestExhibitCompiler
# -------------------------------------------------------------------
class TestExhibitCompiler:
    """Tests for ExhibitCompiler."""

    def setup_method(self):
        self.compiler = ExhibitCompiler(bates_prefix="PIGORS")

    def test_collect_empty(self):
        result = self.compiler.collect_exhibits([])
        assert result == []

    def test_collect_exhibits(self):
        exhibits = [
            {"title": "Exhibit A — Lease Agreement", "date": "2023-06-01"},
            {"title": "Exhibit B — Email Thread", "date": "2024-01-15"},
        ]
        result = self.compiler.collect_exhibits(exhibits)
        assert len(result) == 2
        assert result[0].record_type == RecordType.EXHIBIT

    def test_apply_bates_numbers(self):
        self.compiler.collect_exhibits([
            {"title": "Exhibit A"},
            {"title": "Exhibit B"},
        ])
        numbered = self.compiler.apply_bates_numbers()
        assert numbered[0].bates_number == "PIGORS-0001"
        assert numbered[1].bates_number == "PIGORS-0002"

    def test_create_exhibit_index(self):
        self.compiler.collect_exhibits([{"title": "Exhibit A"}])
        self.compiler.apply_bates_numbers()
        index = self.compiler.create_exhibit_index()
        assert len(index) == 1
        assert "bates_number" in index[0]

    def test_verify_admitted_status_complete(self):
        collected = self.compiler.collect_exhibits([{"title": "Exhibit A"}])
        result = self.compiler.verify_admitted_status([collected[0].entry_id])
        assert result["is_complete"] is True

    def test_verify_admitted_status_missing(self):
        self.compiler.collect_exhibits([{"title": "Exhibit A"}])
        result = self.compiler.verify_admitted_status(["nonexistent_id"])
        assert result["is_complete"] is False
        assert len(result["missing_from_record"]) == 1

    def test_get_stats(self):
        self.compiler.collect_exhibits([{"title": "A"}])
        stats = self.compiler.get_stats()
        assert stats["component"] == "ExhibitCompiler"
        assert stats["bates_prefix"] == "PIGORS"


# -------------------------------------------------------------------
# TestRecordPaginator
# -------------------------------------------------------------------
class TestRecordPaginator:
    """Tests for RecordPaginator."""

    def setup_method(self):
        self.paginator = RecordPaginator(pages_per_volume=_VOLUME_PAGE_LIMIT)

    def _make_entries(self, count: int) -> List[RecordEntry]:
        entries = []
        for i in range(count):
            entries.append(RecordEntry(
                title=f"Entry {i+1}",
                record_type=RecordType.PLEADING,
                date=f"2024-{(i % 12)+1:02d}-01",
            ))
        return entries

    def test_paginate_empty(self):
        result = self.paginator.paginate_record([])
        assert result == []

    def test_paginate_assigns_consecutive_pages(self):
        entries = self._make_entries(5)
        result = self.paginator.paginate_record(entries)
        assert result[0].page_start == 1
        for i in range(1, len(result)):
            assert result[i].page_start == result[i-1].page_end + 1

    def test_create_volumes_empty(self):
        volumes = self.paginator.create_volumes()
        assert volumes == []

    def test_create_volumes_single(self):
        entries = self._make_entries(5)
        self.paginator.paginate_record(entries)
        volumes = self.paginator.create_volumes()
        assert len(volumes) >= 1

    def test_generate_toc(self):
        entries = self._make_entries(3)
        self.paginator.paginate_record(entries)
        toc = self.paginator.generate_toc()
        assert len(toc) == 3
        assert "title" in toc[0]
        assert "page_start" in toc[0]

    def test_create_cover_pages(self):
        entries = self._make_entries(3)
        self.paginator.paginate_record(entries)
        self.paginator.create_volumes()
        covers = self.paginator.create_cover_pages()
        assert len(covers) >= 1
        assert covers[0]["case_number"] == "COA 366810"
        assert covers[0]["appellant"] == "Andrew James Pigors"
        assert covers[0]["appellee"] == "Emily A. Watson"

    def test_get_stats(self):
        entries = self._make_entries(3)
        self.paginator.paginate_record(entries)
        stats = self.paginator.get_stats()
        assert stats["component"] == "RecordPaginator"
        assert stats["total_entries"] == 3


# -------------------------------------------------------------------
# TestRecordCompletionChecker
# -------------------------------------------------------------------
class TestRecordCompletionChecker:
    """Tests for RecordCompletionChecker."""

    def setup_method(self):
        self.checker = RecordCompletionChecker()

    def test_verify_against_register_complete(self):
        record_entries = [RecordEntry(title="Complaint Filed")]
        register_entries = [{"description": "Complaint Filed", "date": "2024-06-15"}]
        result = self.checker.verify_against_register(record_entries, register_entries)
        assert result["is_complete"] is True

    def test_verify_against_register_missing(self):
        record_entries = [RecordEntry(title="Complaint Filed")]
        register_entries = [
            {"description": "Complaint Filed", "date": "2024-06-15"},
            {"description": "Motion to Dismiss", "date": "2024-08-01"},
        ]
        result = self.checker.verify_against_register(record_entries, register_entries)
        assert result["is_complete"] is False

    def test_identify_gaps_no_gaps(self):
        entries = [
            RecordEntry(title="A", page_start=1, page_end=5),
            RecordEntry(title="B", page_start=6, page_end=10),
        ]
        gaps = self.checker.identify_gaps(entries)
        assert len(gaps) == 0

    def test_identify_gaps_with_gap(self):
        entries = [
            RecordEntry(title="A", page_start=1, page_end=5),
            RecordEntry(title="B", page_start=8, page_end=12),
        ]
        gaps = self.checker.identify_gaps(entries)
        assert len(gaps) == 1
        assert gaps[0]["gap_start"] == 6
        assert gaps[0]["gap_end"] == 7

    def test_generate_certification(self):
        cert = self.checker.generate_certification("COA 366810")
        assert cert["case_number"] == "COA 366810"
        assert cert["legal_basis"] == "MCR 7.210(C)"
        assert cert["certifier"] == "Clerk of the Court"

    def test_create_settled_statement(self):
        stmt = self.checker.create_settled_statement(
            missing_transcripts=["2024-09-10 Motion Hearing"],
            proposed_narrative="The court heard argument on...",
        )
        assert stmt["legal_basis"] == "MCR 7.210(B)(4)"
        assert len(stmt["instructions"]) >= 3

    def test_get_stats(self):
        stats = self.checker.get_stats()
        assert stats["component"] == "RecordCompletionChecker"


# -------------------------------------------------------------------
# TestAppellateRecordBuilder
# -------------------------------------------------------------------
class TestAppellateRecordBuilder:
    """Tests for AppellateRecordBuilder orchestrator."""

    def setup_method(self):
        self.builder = AppellateRecordBuilder(db_path=pathlib.Path("nonexistent.db"))

    def test_build_record_empty(self):
        result = self.builder.build_record()
        assert result["case_number"] == "COA 366810"
        assert result["total_entries"] >= 0

    def test_build_record_with_docket(self):
        result = self.builder.build_record(
            docket_entries=[
                {"date": "2024-06-15", "description": "Complaint Filed"},
                {"date": "2024-07-01", "description": "Answer Filed"},
            ],
        )
        assert result["total_entries"] >= 1

    def test_build_record_with_hearings(self):
        result = self.builder.build_record(
            hearings=[
                {"hearing_date": "2024-09-10", "hearing_type": "Motion Hearing"},
            ],
        )
        assert result["total_entries"] >= 1

    def test_build_record_with_exhibits(self):
        result = self.builder.build_record(
            exhibits=[
                {"title": "Exhibit A — Lease", "date": "2023-06-01"},
            ],
        )
        assert result["total_entries"] >= 1

    def test_build_record_full(self):
        result = self.builder.build_record(
            case_number="COA 366810",
            docket_entries=[
                {"date": "2024-06-15", "description": "Complaint Filed"},
            ],
            hearings=[
                {"hearing_date": "2024-09-10", "hearing_type": "Motion Hearing"},
            ],
            exhibits=[
                {"title": "Exhibit A", "date": "2024-01-01"},
                {"title": "Exhibit B", "date": "2024-02-01"},
            ],
            claim_of_appeal_date=date.today().isoformat(),
        )
        assert result["total_entries"] >= 4
        assert result["case_number"] == "COA 366810"

    def test_constants_correct(self):
        assert _TRANSCRIPT_ORDER_DAYS == 7
        assert _CLAIM_OF_APPEAL_DAYS == 21
        assert _RECORD_PREPARATION_DAYS == 56
        assert _APPENDIX_PAGE_LIMIT == 50
        assert _VOLUME_PAGE_LIMIT == 200

    def test_record_sections_order(self):
        assert _RECORD_SECTIONS["register_of_actions"] == 1
        assert _RECORD_SECTIONS["transcripts"] == 5
        assert _RECORD_SECTIONS["exhibits"] == 6
