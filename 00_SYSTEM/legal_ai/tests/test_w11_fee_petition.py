# -*- coding: utf-8 -*-
"""Wave-11 Tests — FeePetitionEngine
======================================
Comprehensive pytest suite for fee_petition_engine.py (~100 tests).

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

from fee_petition_engine import (
    FeeCategory,
    FeeShiftingBasis,
    PetitionStatus,
    TimeEntry,
    CostItem,
    JohnsonFactor,
    LodestarResult,
    FeeShiftingAnalysis,
    FeePetition,
    LodestarCalculator,
    FeeShiftingAnalyzer,
    CostBillPreparer,
    ProSeLitigantFees,
    FeePetitionEngine,
    _PLAINTIFF,
    _DEFENDANT,
    _CHILD_INITIALS,
    _JUDGE,
    _COURT,
    LANE_CASES,
    _MARKET_RATES,
)


# ===================================================================
# TestFeeCategory
# ===================================================================
class TestFeeCategory:
    """Tests for the FeeCategory enum."""

    def test_all_values_exist(self):
        expected = {
            "research", "drafting", "filing", "court_appearance",
            "discovery", "deposition", "expert_fees", "travel",
            "copying", "postage",
        }
        actual = {c.value for c in FeeCategory}
        assert actual == expected

    def test_count_is_ten(self):
        assert len(FeeCategory) == 10

    def test_is_reimbursable_filing(self):
        assert FeeCategory.FILING.is_reimbursable is True

    def test_is_reimbursable_copying(self):
        assert FeeCategory.COPYING.is_reimbursable is True

    def test_is_reimbursable_travel(self):
        assert FeeCategory.TRAVEL.is_reimbursable is True

    def test_is_reimbursable_postage(self):
        assert FeeCategory.POSTAGE.is_reimbursable is True

    def test_is_reimbursable_deposition(self):
        assert FeeCategory.DEPOSITION.is_reimbursable is True

    def test_not_reimbursable_research(self):
        assert FeeCategory.RESEARCH.is_reimbursable is False

    def test_not_reimbursable_drafting(self):
        assert FeeCategory.DRAFTING.is_reimbursable is False

    def test_not_reimbursable_court_appearance(self):
        assert FeeCategory.COURT_APPEARANCE.is_reimbursable is False


# ===================================================================
# TestFeeShiftingBasis
# ===================================================================
class TestFeeShiftingBasis:
    """Tests for the FeeShiftingBasis enum."""

    def test_all_values_exist(self):
        expected = {
            "mcr_2_403_o", "mcr_2_114_e", "mcl_600_2591",
            "mcl_600_2405", "42_usc_1988", "offer_of_judgment",
            "inherent_authority",
        }
        actual = {b.value for b in FeeShiftingBasis}
        assert actual == expected

    def test_count_is_seven(self):
        assert len(FeeShiftingBasis) == 7

    def test_description_mcr_2_403_o(self):
        desc = FeeShiftingBasis.MCR_2_403_O.description
        assert "case evaluation" in desc.lower()

    def test_description_42_usc_1988(self):
        desc = FeeShiftingBasis.USC_42_1988.description
        assert "civil rights" in desc.lower()

    def test_authority_citation_mcr_2_403_o(self):
        assert FeeShiftingBasis.MCR_2_403_O.authority_citation == "MCR 2.403(O)"

    def test_authority_citation_42_usc(self):
        assert FeeShiftingBasis.USC_42_1988.authority_citation == "42 USC §1988"

    def test_authority_citation_mcl_600_2591(self):
        assert FeeShiftingBasis.MCL_600_2591.authority_citation == "MCL 600.2591"


# ===================================================================
# TestPetitionStatus
# ===================================================================
class TestPetitionStatus:
    """Tests for the PetitionStatus enum."""

    def test_all_values_exist(self):
        expected = {
            "draft", "under_review", "filed", "contested",
            "awarded", "denied", "partial_award",
        }
        actual = {s.value for s in PetitionStatus}
        assert actual == expected

    def test_count_is_seven(self):
        assert len(PetitionStatus) == 7


# ===================================================================
# TestTimeEntry
# ===================================================================
class TestTimeEntry:
    """Tests for the TimeEntry dataclass."""

    def test_default_creation(self):
        te = TimeEntry()
        assert te.hours == Decimal("0.0")
        assert te.rate == Decimal("0.00")
        assert te.billable is True
        assert te.category == FeeCategory.RESEARCH

    def test_amount_property(self):
        te = TimeEntry(hours=Decimal("3.5"), rate=Decimal("100.00"))
        assert te.amount == Decimal("350.00")

    def test_amount_precision(self):
        te = TimeEntry(hours=Decimal("1.3"), rate=Decimal("99.99"))
        expected = (Decimal("1.3") * Decimal("99.99")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        assert te.amount == expected

    def test_amount_zero_hours(self):
        te = TimeEntry(hours=Decimal("0.0"), rate=Decimal("100.00"))
        assert te.amount == Decimal("0.00")

    def test_to_dict_keys(self):
        te = TimeEntry(
            date="2026-01-15",
            description="Research MCR 2.403(O)",
            hours=Decimal("3.5"),
            rate=Decimal("100.00"),
            lane="A",
        )
        d = te.to_dict()
        expected_keys = {
            "entry_id", "date", "description", "hours", "rate",
            "amount", "category", "lane", "case_number", "billable", "notes",
        }
        assert set(d.keys()) == expected_keys

    def test_to_dict_decimal_as_string(self):
        te = TimeEntry(hours=Decimal("3.5"), rate=Decimal("100.00"))
        d = te.to_dict()
        assert d["hours"] == "3.5"
        assert d["rate"] == "100.00"
        assert d["amount"] == "350.00"

    def test_unique_ids(self):
        te1 = TimeEntry()
        te2 = TimeEntry()
        assert te1.entry_id != te2.entry_id

    def test_to_dict_serializable(self):
        te = TimeEntry(hours=Decimal("2.5"), rate=Decimal("150.00"))
        json.dumps(te.to_dict())


# ===================================================================
# TestCostItem
# ===================================================================
class TestCostItem:
    """Tests for the CostItem dataclass."""

    def test_default_creation(self):
        ci = CostItem()
        assert ci.amount == Decimal("0.00")
        assert ci.reimbursable is True
        assert ci.category == FeeCategory.FILING

    def test_to_dict(self):
        ci = CostItem(
            date="2026-01-16",
            description="Filing fee",
            amount=Decimal("20.00"),
            receipt_path="receipts/filing.pdf",
        )
        d = ci.to_dict()
        assert d["amount"] == "20.00"
        assert d["receipt_path"] == "receipts/filing.pdf"
        assert d["reimbursable"] is True

    def test_reimbursable_flag_follows_category(self):
        ci = CostItem(category=FeeCategory.COPYING, reimbursable=True)
        assert ci.reimbursable is True
        ci2 = CostItem(category=FeeCategory.RESEARCH, reimbursable=False)
        assert ci2.reimbursable is False

    def test_to_dict_serializable(self):
        ci = CostItem(amount=Decimal("45.50"))
        json.dumps(ci.to_dict())


# ===================================================================
# TestJohnsonFactor
# ===================================================================
class TestJohnsonFactor:
    """Tests for the JohnsonFactor dataclass."""

    def test_default_creation(self):
        jf = JohnsonFactor()
        assert jf.factor_number == 0
        assert jf.supports_enhancement is False
        assert jf.weight == 5

    def test_to_dict(self):
        jf = JohnsonFactor(
            factor_number=3,
            factor_name="Customary fee",
            analysis="At or below market rate",
            supports_enhancement=True,
            weight=8,
        )
        d = jf.to_dict()
        assert d["factor_number"] == 3
        assert d["supports_enhancement"] is True


# ===================================================================
# TestLodestarResult
# ===================================================================
class TestLodestarResult:
    """Tests for the LodestarResult dataclass."""

    def test_default_creation(self):
        lr = LodestarResult()
        assert lr.base_lodestar == Decimal("0.00")
        assert lr.multiplier == Decimal("1.0")
        assert lr.enhancement_justified is False

    def test_to_dict_decimal_strings(self):
        lr = LodestarResult(
            base_lodestar=Decimal("1050.00"),
            adjusted_amount=Decimal("1050.00"),
            total_hours=Decimal("10.5"),
            weighted_rate=Decimal("100.00"),
        )
        d = lr.to_dict()
        assert d["base_lodestar"] == "1050.00"
        assert d["total_hours"] == "10.5"
        json.dumps(d)


# ===================================================================
# TestFeeShiftingAnalysis
# ===================================================================
class TestFeeShiftingAnalysis:
    """Tests for the FeeShiftingAnalysis dataclass."""

    def test_default_creation(self):
        fsa = FeeShiftingAnalysis()
        assert fsa.eligible_bases == []
        assert fsa.estimated_recovery == Decimal("0.00")

    def test_to_dict(self):
        fsa = FeeShiftingAnalysis(
            case_number="2024-001507-DC",
            recommended_basis="MCR 2.403(O)",
        )
        d = fsa.to_dict()
        assert d["case_number"] == "2024-001507-DC"
        json.dumps(d)


# ===================================================================
# TestFeePetition
# ===================================================================
class TestFeePetition:
    """Tests for the FeePetition dataclass."""

    def test_default_creation(self):
        fp = FeePetition()
        assert fp.status == PetitionStatus.DRAFT
        assert fp.total_fees == Decimal("0.00")
        assert fp.total_costs == Decimal("0.00")
        assert fp.total_requested == Decimal("0.00")

    def test_to_dict_with_lodestar(self):
        lr = LodestarResult(base_lodestar=Decimal("1000.00"))
        fp = FeePetition(lodestar=lr, total_fees=Decimal("1000.00"))
        d = fp.to_dict()
        assert d["lodestar"] is not None
        assert d["lodestar"]["base_lodestar"] == "1000.00"

    def test_to_dict_no_lodestar(self):
        fp = FeePetition()
        d = fp.to_dict()
        assert d["lodestar"] is None
        assert d["fee_shifting"] is None

    def test_to_dict_serializable(self):
        fp = FeePetition(
            case_number="2024-001507-DC",
            total_fees=Decimal("500.00"),
            total_costs=Decimal("50.00"),
            total_requested=Decimal("550.00"),
        )
        json.dumps(fp.to_dict())


# ===================================================================
# TestLodestarCalculator
# ===================================================================
class TestLodestarCalculator:
    """Tests for the LodestarCalculator class."""

    def _make_entries(self, count=3):
        entries = []
        for i in range(count):
            entries.append(TimeEntry(
                date=f"2026-01-{15 + i:02d}",
                description=f"Task {i + 1}",
                hours=Decimal("3.0"),
                rate=Decimal("100.00"),
                category=FeeCategory.RESEARCH,
                lane="A",
                case_number="2024-001507-DC",
            ))
        return entries

    def test_calculate_base_simple(self):
        lc = LodestarCalculator()
        entries = self._make_entries(3)
        result = lc.calculate_base(entries)
        assert result.base_lodestar == Decimal("900.00")
        assert result.total_hours == Decimal("9.0")
        assert result.weighted_rate == Decimal("100.00")

    def test_calculate_base_mixed_rates(self):
        lc = LodestarCalculator()
        entries = [
            TimeEntry(hours=Decimal("5.0"), rate=Decimal("100.00")),
            TimeEntry(hours=Decimal("5.0"), rate=Decimal("200.00")),
        ]
        result = lc.calculate_base(entries)
        assert result.base_lodestar == Decimal("1500.00")
        assert result.total_hours == Decimal("10.0")
        assert result.weighted_rate == Decimal("150.00")

    def test_calculate_base_excludes_non_billable(self):
        lc = LodestarCalculator()
        entries = [
            TimeEntry(hours=Decimal("3.0"), rate=Decimal("100.00"), billable=True),
            TimeEntry(hours=Decimal("2.0"), rate=Decimal("100.00"), billable=False),
        ]
        result = lc.calculate_base(entries)
        assert result.base_lodestar == Decimal("300.00")
        assert result.total_hours == Decimal("3.0")

    def test_calculate_base_empty(self):
        lc = LodestarCalculator()
        result = lc.calculate_base([])
        assert result.base_lodestar == Decimal("0.00")
        assert result.weighted_rate == Decimal("0.00")

    def test_apply_multiplier_enhancement(self):
        lc = LodestarCalculator()
        result = LodestarResult(base_lodestar=Decimal("1000.00"))
        lc.apply_multiplier(result, Decimal("1.5"))
        assert result.adjusted_amount == Decimal("1500.00")
        assert result.enhancement_justified is True

    def test_apply_multiplier_reduction(self):
        lc = LodestarCalculator()
        result = LodestarResult(base_lodestar=Decimal("1000.00"))
        lc.apply_multiplier(result, Decimal("0.8"))
        assert result.adjusted_amount == Decimal("800.00")
        assert result.enhancement_justified is False

    def test_apply_multiplier_default_one(self):
        lc = LodestarCalculator()
        result = LodestarResult(
            base_lodestar=Decimal("1000.00"),
            adjusted_amount=Decimal("1000.00"),
        )
        lc.apply_multiplier(result, Decimal("1.0"))
        assert result.adjusted_amount == Decimal("1000.00")
        assert result.enhancement_justified is False

    def test_johnson_factors_count(self):
        lc = LodestarCalculator()
        entries = self._make_entries(3)
        factors = lc.johnson_factors(entries)
        assert len(factors) == 12

    def test_johnson_factors_high_hours_supports(self):
        lc = LodestarCalculator()
        entries = [
            TimeEntry(hours=Decimal("120.0"), rate=Decimal("100.00")),
        ]
        factors = lc.johnson_factors(entries)
        time_factor = factors[0]  # Factor 1: time and labor
        assert time_factor.supports_enhancement is True

    def test_johnson_factors_customary_fee_at_market(self):
        lc = LodestarCalculator()
        entries = [
            TimeEntry(hours=Decimal("10.0"), rate=Decimal("100.00")),
        ]
        factors = lc.johnson_factors(entries)
        # Factor 3 is customary fee
        fee_factor = factors[2]
        assert fee_factor.supports_enhancement is True
        assert "market" in fee_factor.analysis.lower()

    def test_johnson_factors_complexity_exceptional(self):
        lc = LodestarCalculator()
        entries = self._make_entries(1)
        factors = lc.johnson_factors(entries, case_complexity="exceptional")
        # Factor 11 (index 10) is novelty/difficulty
        novelty = factors[10]
        assert novelty.supports_enhancement is True

    def test_compare_market_rate_within(self):
        lc = LodestarCalculator()
        result = lc.compare_market_rate(Decimal("100.00"))
        assert result["within_market"] is True
        assert result["comparison"] == "within market"

    def test_compare_market_rate_above(self):
        lc = LodestarCalculator()
        result = lc.compare_market_rate(Decimal("999.00"))
        assert result["within_market"] is False
        assert result["comparison"] == "above market"

    def test_compare_market_rate_below(self):
        lc = LodestarCalculator()
        result = lc.compare_market_rate(Decimal("10.00"))
        assert result["within_market"] is False
        assert result["comparison"] == "below market"

    def test_get_stats(self):
        lc = LodestarCalculator()
        stats = lc.get_stats()
        assert stats["component"] == "LodestarCalculator"
        assert stats["johnson_factors"] == 12


# ===================================================================
# TestFeeShiftingAnalyzer
# ===================================================================
class TestFeeShiftingAnalyzer:
    """Tests for the FeeShiftingAnalyzer class."""

    def test_analyze_statute_family_law(self):
        fsa = FeeShiftingAnalyzer()
        analysis = fsa.analyze_statute("family_law")
        assert isinstance(analysis, FeeShiftingAnalysis)
        assert len(analysis.eligible_bases) >= 3

    def test_analyze_statute_civil_rights(self):
        fsa = FeeShiftingAnalyzer()
        analysis = fsa.analyze_statute("civil_rights")
        # Should include 42 USC §1988
        auths = [b.get("authority", "") for b in analysis.eligible_bases]
        assert "42 USC §1988" in auths

    def test_analyze_statute_federal_1983(self):
        fsa = FeeShiftingAnalyzer()
        analysis = fsa.analyze_statute("federal_1983")
        auths = [b.get("authority", "") for b in analysis.eligible_bases]
        assert "42 USC §1988" in auths

    def test_check_42_usc_1988(self):
        fsa = FeeShiftingAnalyzer()
        result = fsa.check_42_usc_1988()
        assert result["eligible"] is True
        assert result["strength"] == 8
        assert "prevailing party" in result["requirements"][0].lower()

    def test_check_mcr_2_403_O(self):
        fsa = FeeShiftingAnalyzer()
        result = fsa.check_mcr_2_403_O()
        assert result["eligible"] is True
        assert result["authority"] == "MCR 2.403(O)"

    def test_check_mcl_600_2591(self):
        fsa = FeeShiftingAnalyzer()
        result = fsa.check_mcl_600_2591()
        assert result["eligible"] is True
        assert result["authority"] == "MCL 600.2591"
        assert "frivolous" in result["standard"].lower()

    def test_check_mcl_600_2405(self):
        fsa = FeeShiftingAnalyzer()
        result = fsa.check_mcl_600_2405()
        assert result["eligible"] is True
        assert "filing fees" in str(result.get("recoverable_items", [])).lower()

    def test_check_offer_of_judgment(self):
        fsa = FeeShiftingAnalyzer()
        result = fsa.check_offer_of_judgment()
        assert result["eligible"] is True
        assert result["authority"] == "MCR 2.405"

    def test_recommended_basis_selected(self):
        fsa = FeeShiftingAnalyzer()
        analysis = fsa.analyze_statute("family_law")
        assert analysis.recommended_basis != ""

    def test_get_stats(self):
        fsa = FeeShiftingAnalyzer()
        stats = fsa.get_stats()
        assert stats["component"] == "FeeShiftingAnalyzer"
        assert stats["statutes_analyzed"] == 5


# ===================================================================
# TestCostBillPreparer
# ===================================================================
class TestCostBillPreparer:
    """Tests for the CostBillPreparer class."""

    def _sample_costs(self):
        return [
            CostItem(
                date="2026-01-16", description="Filing fee",
                amount=Decimal("20.00"), category=FeeCategory.FILING,
                receipt_path="receipts/filing.pdf", reimbursable=True,
            ),
            CostItem(
                date="2026-01-16", description="Copies (25 pages)",
                amount=Decimal("6.25"), category=FeeCategory.COPYING,
                receipt_path="receipts/copies.pdf", reimbursable=True,
            ),
            CostItem(
                date="2026-01-17", description="Research time",
                amount=Decimal("50.00"), category=FeeCategory.RESEARCH,
                reimbursable=False,
            ),
        ]

    def test_compile_costs_reimbursable_only(self):
        cbp = CostBillPreparer()
        items = self._sample_costs()
        result = cbp.compile_costs(items, reimbursable_only=True)
        assert len(result) == 2
        assert all(c.reimbursable for c in result)

    def test_compile_costs_all(self):
        cbp = CostBillPreparer()
        items = self._sample_costs()
        result = cbp.compile_costs(items, reimbursable_only=False)
        assert len(result) == 3

    def test_verify_receipts_all_documented(self):
        cbp = CostBillPreparer()
        items = [
            CostItem(receipt_path="a.pdf"),
            CostItem(receipt_path="b.pdf"),
        ]
        report = cbp.verify_receipts(items)
        assert report["with_receipts"] == 2
        assert report["without_receipts"] == 0
        assert report["documentation_rate"] == 100.0

    def test_verify_receipts_some_missing(self):
        cbp = CostBillPreparer()
        items = [
            CostItem(receipt_path="a.pdf"),
            CostItem(receipt_path=""),
        ]
        report = cbp.verify_receipts(items)
        assert report["with_receipts"] == 1
        assert report["without_receipts"] == 1
        assert report["documentation_rate"] == 50.0

    def test_verify_receipts_empty(self):
        cbp = CostBillPreparer()
        report = cbp.verify_receipts([])
        assert report["total_items"] == 0

    def test_categorize(self):
        cbp = CostBillPreparer()
        items = self._sample_costs()
        grouped = cbp.categorize(items)
        assert "filing" in grouped
        assert "copying" in grouped
        assert len(grouped["filing"]) == 1

    def test_generate_bill_of_costs(self):
        cbp = CostBillPreparer()
        items = self._sample_costs()
        bill = cbp.generate_bill_of_costs(items, "2024-001507-DC")
        assert "STATE OF MICHIGAN" in bill
        assert "Andrew James Pigors" in bill
        assert "Emily A. Watson" in bill
        assert "MCR 2.625" in bill
        assert "MCL 600.2405" in bill
        assert "2024-001507-DC" in bill
        assert "VERIFICATION" in bill

    def test_generate_bill_excludes_non_reimbursable(self):
        cbp = CostBillPreparer()
        items = self._sample_costs()
        bill = cbp.generate_bill_of_costs(items, "2024-001507-DC")
        # Research cost ($50) should be excluded (non-reimbursable)
        # Total should be $26.25
        assert "$26.25" in bill

    def test_get_stats(self):
        cbp = CostBillPreparer()
        stats = cbp.get_stats()
        assert stats["component"] == "CostBillPreparer"
        assert stats["reimbursable_categories"] >= 5


# ===================================================================
# TestProSeLitigantFees
# ===================================================================
class TestProSeLitigantFees:
    """Tests for the ProSeLitigantFees class."""

    def test_eligibility_non_attorney(self):
        pslf = ProSeLitigantFees()
        result = pslf.analyze_fee_recovery_eligibility(
            is_attorney=False,
            case_type="family_law",
            statutes_invoked=["MCR 2.403(O)"],
        )
        assert result["eligible_for_fees"] is True
        assert result["eligible_for_costs"] is True

    def test_eligibility_attorney_barred(self):
        pslf = ProSeLitigantFees()
        result = pslf.analyze_fee_recovery_eligibility(
            is_attorney=True,
            case_type="civil_rights",
            statutes_invoked=["42 USC §1988"],
        )
        # Kay v. Ehrler bars pro se attorneys from §1988 fees
        assert any("Kay v. Ehrler" in a for a in result["analysis"])

    def test_eligibility_1988_non_attorney(self):
        pslf = ProSeLitigantFees()
        result = pslf.analyze_fee_recovery_eligibility(
            is_attorney=False,
            statutes_invoked=["42_usc_1988"],
        )
        assert result["eligible_for_fees"] is True

    def test_eligibility_mcl_600_2591(self):
        pslf = ProSeLitigantFees()
        result = pslf.analyze_fee_recovery_eligibility(
            is_attorney=False,
            statutes_invoked=["mcl_600_2591"],
        )
        assert result["eligible_for_fees"] is True

    def test_recommendations_always_present(self):
        pslf = ProSeLitigantFees()
        result = pslf.analyze_fee_recovery_eligibility()
        assert len(result["recommendations"]) >= 3

    def test_document_hours_excellent(self):
        pslf = ProSeLitigantFees()
        entries = [
            TimeEntry(
                date="2026-01-15",
                description="Researched MCR 2.403(O) case evaluation sanctions in detail",
                hours=Decimal("3.5"),
            ),
        ]
        result = pslf.document_hours(entries)
        assert result["documentation_quality"] == "excellent"
        assert result["issues_found"] == 0

    def test_document_hours_missing_date(self):
        pslf = ProSeLitigantFees()
        entries = [
            TimeEntry(description="Long enough description here", hours=Decimal("3.0")),
        ]
        result = pslf.document_hours(entries)
        assert result["issues_found"] >= 1
        assert any("missing date" in i for i in result["issues"])

    def test_document_hours_brief_description(self):
        pslf = ProSeLitigantFees()
        entries = [
            TimeEntry(date="2026-01-15", description="Work", hours=Decimal("3.0")),
        ]
        result = pslf.document_hours(entries)
        assert any("description too brief" in i for i in result["issues"])

    def test_document_hours_excessive(self):
        pslf = ProSeLitigantFees()
        entries = [
            TimeEntry(
                date="2026-01-15",
                description="Very long work day with extensive activities",
                hours=Decimal("15.0"),
            ),
        ]
        result = pslf.document_hours(entries)
        assert any("excessive" in i for i in result["issues"])

    def test_document_hours_zero_hours(self):
        pslf = ProSeLitigantFees()
        entries = [
            TimeEntry(date="2026-01-15", description="Something described fully",
                      hours=Decimal("0")),
        ]
        result = pslf.document_hours(entries)
        assert any("zero or negative" in i for i in result["issues"])

    def test_calculate_reasonable_rate_moderate(self):
        pslf = ProSeLitigantFees()
        result = pslf.calculate_reasonable_rate(case_complexity="moderate")
        rate = Decimal(result["recommended_rate"])
        low = Decimal(result["market_range"]["low"])
        high = Decimal(result["market_range"]["high"])
        assert low <= rate <= high

    def test_calculate_reasonable_rate_exceptional(self):
        pslf = ProSeLitigantFees()
        result = pslf.calculate_reasonable_rate(case_complexity="exceptional")
        rate = Decimal(result["recommended_rate"])
        assert rate == Decimal("150.00")  # capped at high

    def test_calculate_reasonable_rate_simple(self):
        pslf = ProSeLitigantFees()
        result = pslf.calculate_reasonable_rate(case_complexity="simple")
        rate = Decimal(result["recommended_rate"])
        assert rate >= Decimal("50.00")  # at least the low end

    def test_get_stats(self):
        pslf = ProSeLitigantFees()
        stats = pslf.get_stats()
        assert stats["component"] == "ProSeLitigantFees"
        assert stats["market_rate_tiers"] >= 4


# ===================================================================
# TestFeePetitionEngine
# ===================================================================
class TestFeePetitionEngine:
    """Tests for the FeePetitionEngine orchestrator."""

    def test_add_time_entry(self, tmp_path):
        fpe = FeePetitionEngine(db_path=tmp_path / "test.db")
        entry = fpe.add_time_entry(
            date="2026-01-15",
            description="Research MCR 2.403(O)",
            hours=Decimal("3.5"),
            rate=Decimal("100.00"),
            lane="A",
        )
        assert entry.case_number == "2024-001507-DC"
        assert entry.hours == Decimal("3.5")

    def test_add_cost_item(self, tmp_path):
        fpe = FeePetitionEngine(db_path=tmp_path / "test.db")
        item = fpe.add_cost_item(
            date="2026-01-16",
            description="Filing fee",
            amount=Decimal("20.00"),
            category=FeeCategory.FILING,
            lane="A",
        )
        assert item.reimbursable is True
        assert item.case_number == "2024-001507-DC"

    def test_add_cost_item_non_reimbursable(self, tmp_path):
        fpe = FeePetitionEngine(db_path=tmp_path / "test.db")
        item = fpe.add_cost_item(
            date="2026-01-16",
            description="Research",
            amount=Decimal("50.00"),
            category=FeeCategory.RESEARCH,
            lane="A",
        )
        assert item.reimbursable is False

    def test_create_petition(self, tmp_path):
        fpe = FeePetitionEngine(db_path=tmp_path / "test.db")
        fpe.add_time_entry(
            "2026-01-15", "Research", Decimal("3.5"),
            Decimal("100.00"), lane="A",
        )
        fpe.add_cost_item(
            "2026-01-16", "Filing fee", Decimal("20.00"),
            FeeCategory.FILING, lane="A",
        )
        petition = fpe.create_petition("2024-001507-DC", lane="A")
        assert isinstance(petition, FeePetition)
        assert petition.total_fees == Decimal("350.00")
        assert petition.total_costs == Decimal("20.00")
        assert petition.total_requested == Decimal("370.00")

    def test_create_petition_lodestar(self, tmp_path):
        fpe = FeePetitionEngine(db_path=tmp_path / "test.db")
        fpe.add_time_entry(
            "2026-01-15", "Research", Decimal("5.0"), Decimal("100.00"),
            lane="A",
        )
        petition = fpe.create_petition("2024-001507-DC")
        assert petition.lodestar is not None
        assert petition.lodestar.base_lodestar == Decimal("500.00")

    def test_create_petition_fee_shifting(self, tmp_path):
        fpe = FeePetitionEngine(db_path=tmp_path / "test.db")
        fpe.add_time_entry(
            "2026-01-15", "Research", Decimal("3.0"), Decimal("100.00"),
            lane="A",
        )
        petition = fpe.create_petition("2024-001507-DC")
        assert petition.fee_shifting is not None
        assert petition.legal_basis != ""

    def test_create_petition_empty_entries(self, tmp_path):
        fpe = FeePetitionEngine(db_path=tmp_path / "test.db")
        petition = fpe.create_petition("2024-001507-DC")
        assert petition.total_fees == Decimal("0.00")
        assert petition.total_costs == Decimal("0.00")
        assert petition.lodestar is None

    def test_calculate_total(self, tmp_path):
        fpe = FeePetitionEngine(db_path=tmp_path / "test.db")
        fpe.add_time_entry(
            "2026-01-15", "Research", Decimal("3.5"), Decimal("100.00"),
            lane="A",
        )
        fpe.add_time_entry(
            "2026-01-16", "Drafting", Decimal("5.0"), Decimal("100.00"),
            lane="A",
        )
        fpe.add_cost_item(
            "2026-01-16", "Filing", Decimal("20.00"),
            FeeCategory.FILING, lane="A",
        )
        totals = fpe.calculate_total()
        assert totals["total_fees"] == "850.00"
        assert totals["total_costs"] == "20.00"
        assert totals["total_requested"] == "870.00"
        assert totals["total_hours"] == "8.5"

    def test_calculate_total_by_case(self, tmp_path):
        fpe = FeePetitionEngine(db_path=tmp_path / "test.db")
        fpe.add_time_entry(
            "2026-01-15", "Task A", Decimal("3.0"), Decimal("100.00"),
            lane="A",
        )
        fpe.add_time_entry(
            "2026-01-16", "Task B", Decimal("2.0"), Decimal("100.00"),
            lane="B",
        )
        totals_a = fpe.calculate_total("2024-001507-DC")
        assert totals_a["time_entries"] == 1
        assert totals_a["total_fees"] == "300.00"

    def test_generate_itemization(self, tmp_path):
        fpe = FeePetitionEngine(db_path=tmp_path / "test.db")
        fpe.add_time_entry(
            "2026-01-15", "Research", Decimal("3.0"), Decimal("100.00"),
            FeeCategory.RESEARCH, lane="A",
        )
        fpe.add_cost_item(
            "2026-01-16", "Filing", Decimal("20.00"),
            FeeCategory.FILING, lane="A",
        )
        itemization = fpe.generate_itemization()
        assert "time_entries_by_category" in itemization
        assert "cost_items_by_category" in itemization
        assert "summary" in itemization
        assert "research" in itemization["time_entries_by_category"]

    def test_assess_recoverability(self, tmp_path):
        fpe = FeePetitionEngine(db_path=tmp_path / "test.db")
        fpe.add_time_entry(
            "2026-01-15",
            "Detailed research on MCR 2.403(O) sanctions provisions",
            Decimal("3.0"), Decimal("100.00"), lane="A",
        )
        fpe.add_cost_item(
            "2026-01-16", "Filing fee for motion",
            Decimal("20.00"), FeeCategory.FILING,
            receipt_path="receipts/filing.pdf", lane="A",
        )
        assessment = fpe.assess_recoverability(
            case_number="2024-001507-DC", case_type="family_law",
        )
        assert assessment["overall_assessment"] in ("STRONG", "MODERATE", "WEAK")
        assert assessment["cost_recovery_eligible"] is True
        assert "fee_shifting_bases" in assessment

    def test_assess_recoverability_weak(self, tmp_path):
        fpe = FeePetitionEngine(db_path=tmp_path / "test.db")
        # No entries = weak documentation
        assessment = fpe.assess_recoverability()
        assert assessment["overall_assessment"] in ("MODERATE", "WEAK")

    def test_generate_bill_of_costs(self, tmp_path):
        fpe = FeePetitionEngine(db_path=tmp_path / "test.db")
        fpe.add_cost_item(
            "2026-01-16", "Filing fee", Decimal("20.00"),
            FeeCategory.FILING, lane="A",
        )
        bill = fpe.generate_bill_of_costs("2024-001507-DC")
        assert "STATE OF MICHIGAN" in bill
        assert "Andrew James Pigors" in bill

    def test_persist_with_tmp_db(self, tmp_path):
        db_path = tmp_path / "test_fee.db"
        conn = sqlite3.connect(str(db_path))
        conn.close()
        fpe = FeePetitionEngine(db_path=db_path)
        fpe.add_time_entry(
            "2026-01-15", "Research", Decimal("3.0"), Decimal("100.00"),
        )
        fpe.add_cost_item(
            "2026-01-16", "Filing", Decimal("20.00"),
        )
        saved = fpe.persist()
        assert saved >= 2

    def test_persist_no_db(self, tmp_path):
        fpe = FeePetitionEngine(db_path=tmp_path / "nonexistent.db")
        assert fpe.persist() == 0

    def test_get_stats(self, tmp_path):
        fpe = FeePetitionEngine(db_path=tmp_path / "test.db")
        fpe.add_time_entry("2026-01-15", "Research", Decimal("3.0"))
        stats = fpe.get_stats()
        assert stats["module"] == "fee_petition_engine"
        assert stats["time_entries"] == 1
        assert "lodestar" in stats
        assert "fee_shifting" in stats

    def test_reset(self, tmp_path):
        fpe = FeePetitionEngine(db_path=tmp_path / "test.db")
        fpe.add_time_entry("2026-01-15", "Research", Decimal("3.0"))
        fpe.add_cost_item("2026-01-16", "Filing", Decimal("20.00"))
        fpe.create_petition("2024-001507-DC")
        fpe.reset()
        assert fpe.get_stats()["time_entries"] == 0
        assert fpe.get_stats()["cost_items"] == 0
        assert fpe.get_stats()["petitions"] == 0


# ===================================================================
# TestDecimalPrecision
# ===================================================================
class TestDecimalPrecision:
    """Ensure all financial calculations use Decimal, not float."""

    def test_time_entry_amount_is_decimal(self):
        te = TimeEntry(hours=Decimal("1.1"), rate=Decimal("99.99"))
        assert isinstance(te.amount, Decimal)

    def test_lodestar_base_is_decimal(self):
        lc = LodestarCalculator()
        entries = [TimeEntry(hours=Decimal("2.0"), rate=Decimal("100.00"))]
        result = lc.calculate_base(entries)
        assert isinstance(result.base_lodestar, Decimal)
        assert isinstance(result.weighted_rate, Decimal)

    def test_multiplier_precision(self):
        lc = LodestarCalculator()
        result = LodestarResult(base_lodestar=Decimal("333.33"))
        lc.apply_multiplier(result, Decimal("1.5"))
        assert result.adjusted_amount == Decimal("499.99") or result.adjusted_amount == Decimal("500.00")
        assert isinstance(result.adjusted_amount, Decimal)

    def test_cost_item_amount_decimal(self):
        ci = CostItem(amount=Decimal("19.99"))
        assert isinstance(ci.amount, Decimal)

    def test_no_float_contamination(self):
        te = TimeEntry(hours=Decimal("0.1"), rate=Decimal("0.2"))
        # 0.1 * 0.2 = 0.02 exactly in Decimal, but not in float
        assert te.amount == Decimal("0.02")


# ===================================================================
# TestEdgeCases
# ===================================================================
class TestEdgeCases:
    """Edge cases for fee petition processing."""

    def test_zero_fees_petition(self, tmp_path):
        fpe = FeePetitionEngine(db_path=tmp_path / "test.db")
        petition = fpe.create_petition("2024-001507-DC")
        assert petition.total_requested == Decimal("0.00")

    def test_massive_cost(self, tmp_path):
        fpe = FeePetitionEngine(db_path=tmp_path / "test.db")
        fpe.add_cost_item(
            "2026-01-16", "Expert witness retainer",
            Decimal("999999.99"), FeeCategory.EXPERT_FEES,
        )
        totals = fpe.calculate_total()
        assert Decimal(totals["total_costs"]) == Decimal("999999.99")

    def test_mixed_reimbursable_costs(self, tmp_path):
        fpe = FeePetitionEngine(db_path=tmp_path / "test.db")
        fpe.add_cost_item(
            "2026-01-16", "Filing fee",
            Decimal("20.00"), FeeCategory.FILING,
        )
        fpe.add_cost_item(
            "2026-01-16", "Research books",
            Decimal("50.00"), FeeCategory.RESEARCH,
        )
        totals = fpe.calculate_total()
        # Only filing is reimbursable
        assert totals["total_costs"] == "20.00"

    def test_many_entries(self, tmp_path):
        fpe = FeePetitionEngine(db_path=tmp_path / "test.db")
        for i in range(50):
            fpe.add_time_entry(
                f"2026-01-{(i % 28) + 1:02d}",
                f"Task {i + 1}: detailed description of work performed",
                Decimal("1.0"), Decimal("100.00"),
            )
        totals = fpe.calculate_total()
        assert totals["time_entries"] == 50
        assert Decimal(totals["total_fees"]) == Decimal("5000.00")

    def test_market_rates_exist(self):
        assert "attorney_senior" in _MARKET_RATES
        assert "pro_se_litigant" in _MARKET_RATES
        for role, rates in _MARKET_RATES.items():
            assert rates["low"] <= rates["mid"] <= rates["high"]

    def test_lane_cases_consistency(self):
        assert LANE_CASES["A"] == "2024-001507-DC"
        assert LANE_CASES["B"] == "2025-002760-CZ"
        assert LANE_CASES["D"] == "2023-5907-PP"

    def test_party_names(self):
        assert _PLAINTIFF == "Andrew James Pigors"
        assert _DEFENDANT == "Emily A. Watson"
        assert _CHILD_INITIALS == "L.D.W."
        assert _JUDGE == "Hon. Jenny L. McNeill"
        assert _COURT == "14th Circuit Court"
