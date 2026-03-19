# -*- coding: utf-8 -*-
"""
Fee Petition Engine — LitigationOS Legal AI Subsystem
======================================================
Attorney fee petition and cost recovery engine for Michigan
family-law litigation.  Implements lodestar calculation with
Johnson v. Georgia Highway Express factors, fee-shifting analysis
under multiple Michigan and federal statutes, cost bill
preparation, and pro se litigant fee recovery assessment.

Critical for pro se litigant cost recovery where statutes
authorize fee shifting.

Case Context
------------
    Plaintiff:  Andrew James Pigors (Pro Se)
    Defendant:  Emily A. Watson
    Child:      L.D.W. (per MCR 8.119(H)) — Male
    Judge:      Hon. Jenny L. McNeill — 14th Circuit Court
    Cases:      2024-001507-DC, 2025-002760-CZ, 2023-5907-PP, COA 366810
    Lanes:      ALL (A through F)

Michigan Rules & Statutes
--------------------------
    MCR 2.403(O) – Case Evaluation Sanctions (fee shifting on rejection)
    MCR 2.114(E) – Sanctions for frivolous filings
    MCR 2.625 – Taxable Costs
    MCL 600.2405 – Costs in civil actions
    MCL 600.2441 – Attorney fees in certain actions
    MCL 600.2591 – Frivolous claims and defenses
    42 USC §1988 – Attorney fees in civil rights actions

Federal Authority
-----------------
    Johnson v. Georgia Highway Express, 488 F.2d 714 (5th Cir. 1974)
        — 12-factor lodestar reasonableness test
    Kay v. Ehrler, 499 U.S. 432 (1991)
        — Pro se attorney fee recovery limitations
    Hensley v. Eckerhart, 461 U.S. 424 (1983)
        — Lodestar calculation framework

Usage::

    from legal_ai.fee_petition_engine import FeePetitionEngine

    fpe = FeePetitionEngine()
    fpe.add_time_entry(date="2026-01-15", description="Draft motion",
                       hours=Decimal("3.5"), rate=Decimal("150.00"))
    petition = fpe.create_petition(case_number="2024-001507-DC")

Zero external dependencies.  CPU-first.  Local-only.
"""
from __future__ import annotations

import json
import logging
import sqlite3
import sys
import textwrap
import uuid
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger("legal_ai.fee_petition_engine")

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
_JUDGE = "Hon. Jenny L. McNeill"
_COURT = "14th Circuit Court"

LANE_CASES: Dict[str, str] = {
    "A": "2024-001507-DC",
    "B": "2025-002760-CZ",
    "C": "Convergence",
    "D": "2023-5907-PP",
    "E": "JTC / Misconduct",
    "F": "COA 366810",
}

# Reasonable hourly rates for the Muskegon, Michigan market
_MARKET_RATES: Dict[str, Dict[str, Decimal]] = {
    "attorney_senior": {"low": Decimal("200.00"), "mid": Decimal("300.00"), "high": Decimal("400.00")},
    "attorney_junior": {"low": Decimal("150.00"), "mid": Decimal("200.00"), "high": Decimal("275.00")},
    "paralegal": {"low": Decimal("75.00"), "mid": Decimal("100.00"), "high": Decimal("150.00")},
    "pro_se_litigant": {"low": Decimal("50.00"), "mid": Decimal("100.00"), "high": Decimal("150.00")},
}


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class FeeCategory(str, Enum):
    """Categories for time entries and cost items."""

    RESEARCH = "research"
    DRAFTING = "drafting"
    FILING = "filing"
    COURT_APPEARANCE = "court_appearance"
    DISCOVERY = "discovery"
    DEPOSITION = "deposition"
    EXPERT_FEES = "expert_fees"
    TRAVEL = "travel"
    COPYING = "copying"
    POSTAGE = "postage"

    @property
    def is_reimbursable(self) -> bool:
        """Whether this category is typically reimbursable as costs."""
        reimbursable = {
            "filing", "copying", "postage", "travel",
            "deposition", "expert_fees",
        }
        return self.value in reimbursable


class FeeShiftingBasis(str, Enum):
    """Legal bases for fee shifting."""

    MCR_2_403_O = "mcr_2_403_o"
    MCR_2_114_E = "mcr_2_114_e"
    MCL_600_2591 = "mcl_600_2591"
    MCL_600_2405 = "mcl_600_2405"
    USC_42_1988 = "42_usc_1988"
    OFFER_OF_JUDGMENT = "offer_of_judgment"
    INHERENT_AUTHORITY = "inherent_authority"

    @property
    def description(self) -> str:
        _descs: Dict[str, str] = {
            "mcr_2_403_o": "Case evaluation sanctions — party rejecting "
                           "case evaluation bears costs/fees if verdict "
                           "not more favorable",
            "mcr_2_114_e": "Sanctions for frivolous filings signed in "
                           "violation of MCR 2.114",
            "mcl_600_2591": "Frivolous civil actions or defenses — "
                            "prevailing party may recover fees",
            "mcl_600_2405": "General costs in civil actions",
            "42_usc_1988": "Attorney fees for prevailing party in civil "
                           "rights actions under 42 USC §1983",
            "offer_of_judgment": "MCR 2.405 — costs after rejected offer",
            "inherent_authority": "Court's inherent authority to award "
                                  "fees for bad-faith litigation conduct",
        }
        return _descs.get(self.value, "")

    @property
    def authority_citation(self) -> str:
        _cites: Dict[str, str] = {
            "mcr_2_403_o": "MCR 2.403(O)",
            "mcr_2_114_e": "MCR 2.114(E)",
            "mcl_600_2591": "MCL 600.2591",
            "mcl_600_2405": "MCL 600.2405",
            "42_usc_1988": "42 USC §1988",
            "offer_of_judgment": "MCR 2.405",
            "inherent_authority": "Inherent judicial authority",
        }
        return _cites.get(self.value, "")


class PetitionStatus(str, Enum):
    """Status of a fee petition."""

    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    FILED = "filed"
    CONTESTED = "contested"
    AWARDED = "awarded"
    DENIED = "denied"
    PARTIAL_AWARD = "partial_award"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class TimeEntry:
    """A single time entry for fee calculation."""

    entry_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    date: str = ""
    description: str = ""
    hours: Decimal = Decimal("0.0")
    rate: Decimal = Decimal("0.00")
    category: FeeCategory = FeeCategory.RESEARCH
    lane: str = ""
    case_number: str = ""
    billable: bool = True
    notes: str = ""

    @property
    def amount(self) -> Decimal:
        return (self.hours * self.rate).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "date": self.date,
            "description": self.description,
            "hours": str(self.hours),
            "rate": str(self.rate),
            "amount": str(self.amount),
            "category": self.category.value,
            "lane": self.lane,
            "case_number": self.case_number,
            "billable": self.billable,
            "notes": self.notes,
        }


@dataclass
class CostItem:
    """A single cost item for the bill of costs."""

    item_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    date: str = ""
    description: str = ""
    amount: Decimal = Decimal("0.00")
    category: FeeCategory = FeeCategory.FILING
    receipt_path: str = ""
    reimbursable: bool = True
    lane: str = ""
    case_number: str = ""
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "date": self.date,
            "description": self.description,
            "amount": str(self.amount),
            "category": self.category.value,
            "receipt_path": self.receipt_path,
            "reimbursable": self.reimbursable,
            "lane": self.lane,
            "case_number": self.case_number,
            "notes": self.notes,
        }


@dataclass
class JohnsonFactor:
    """One of the 12 Johnson v. Georgia Highway Express factors."""

    factor_number: int = 0
    factor_name: str = ""
    analysis: str = ""
    supports_enhancement: bool = False
    weight: int = 5  # 1-10

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LodestarResult:
    """Result of a lodestar fee calculation."""

    result_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    base_lodestar: Decimal = Decimal("0.00")
    multiplier: Decimal = Decimal("1.0")
    adjusted_amount: Decimal = Decimal("0.00")
    total_hours: Decimal = Decimal("0.0")
    weighted_rate: Decimal = Decimal("0.00")
    johnson_factors: List[JohnsonFactor] = field(default_factory=list)
    enhancement_justified: bool = False
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "base_lodestar": str(self.base_lodestar),
            "multiplier": str(self.multiplier),
            "adjusted_amount": str(self.adjusted_amount),
            "total_hours": str(self.total_hours),
            "weighted_rate": str(self.weighted_rate),
            "johnson_factors": [f.to_dict() for f in self.johnson_factors],
            "enhancement_justified": self.enhancement_justified,
            "generated_at": self.generated_at,
        }


@dataclass
class FeeShiftingAnalysis:
    """Analysis of fee-shifting eligibility under various statutes."""

    analysis_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    case_number: str = ""
    case_type: str = ""
    eligible_bases: List[Dict[str, Any]] = field(default_factory=list)
    recommended_basis: str = ""
    estimated_recovery: Decimal = Decimal("0.00")
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "case_number": self.case_number,
            "case_type": self.case_type,
            "eligible_bases": self.eligible_bases,
            "recommended_basis": self.recommended_basis,
            "estimated_recovery": str(self.estimated_recovery),
            "notes": self.notes,
        }


@dataclass
class FeePetition:
    """A complete fee petition document."""

    petition_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    case_number: str = ""
    lane: str = ""
    status: PetitionStatus = PetitionStatus.DRAFT
    time_entries: List[TimeEntry] = field(default_factory=list)
    cost_items: List[CostItem] = field(default_factory=list)
    lodestar: Optional[LodestarResult] = None
    fee_shifting: Optional[FeeShiftingAnalysis] = None
    total_fees: Decimal = Decimal("0.00")
    total_costs: Decimal = Decimal("0.00")
    total_requested: Decimal = Decimal("0.00")
    legal_basis: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "petition_id": self.petition_id,
            "case_number": self.case_number,
            "lane": self.lane,
            "status": self.status.value,
            "time_entries": [t.to_dict() for t in self.time_entries],
            "cost_items": [c.to_dict() for c in self.cost_items],
            "lodestar": self.lodestar.to_dict() if self.lodestar else None,
            "fee_shifting": self.fee_shifting.to_dict() if self.fee_shifting else None,
            "total_fees": str(self.total_fees),
            "total_costs": str(self.total_costs),
            "total_requested": str(self.total_requested),
            "legal_basis": self.legal_basis,
            "created_at": self.created_at,
        }


# ---------------------------------------------------------------------------
# LodestarCalculator
# ---------------------------------------------------------------------------


class LodestarCalculator:
    """Lodestar fee calculation with Johnson factor analysis.

    The lodestar method (Hensley v. Eckerhart, 461 U.S. 424 (1983))
    multiplies reasonable hours by a reasonable hourly rate.  The
    12 Johnson factors (Johnson v. Georgia Highway Express, 488 F.2d
    714 (5th Cir. 1974)) may justify an upward or downward adjustment.
    """

    # The 12 Johnson factors
    _JOHNSON_FACTORS: List[Dict[str, str]] = [
        {"name": "Time and labor required",
         "description": "The time and labor required, the novelty and "
                        "difficulty of the questions involved, and the "
                        "skill requisite to perform the legal service properly"},
        {"name": "Preclusion of other employment",
         "description": "The likelihood that the acceptance of the particular "
                        "employment will preclude other employment"},
        {"name": "Customary fee",
         "description": "The fee customarily charged in the locality for "
                        "similar legal services"},
        {"name": "Amount involved and results obtained",
         "description": "The amount involved and the results obtained"},
        {"name": "Time limitations imposed",
         "description": "The time limitations imposed by the client or "
                        "the circumstances"},
        {"name": "Nature and length of relationship",
         "description": "The nature and length of the professional "
                        "relationship with the client"},
        {"name": "Experience, reputation, and ability",
         "description": "The experience, reputation, and ability of the "
                        "attorney performing the services"},
        {"name": "Undesirability of the case",
         "description": "The 'undesirability' of the case"},
        {"name": "Nature of the fee arrangement",
         "description": "The nature and length of the professional "
                        "relationship with the client"},
        {"name": "Awards in similar cases",
         "description": "Awards in similar cases"},
        {"name": "Novelty and difficulty",
         "description": "The novelty and difficulty of the questions"},
        {"name": "Skill of the attorney",
         "description": "The skill requisite to perform the legal "
                        "service properly"},
    ]

    def calculate_base(self, entries: Sequence[TimeEntry]) -> LodestarResult:
        """Calculate the base lodestar amount.

        Lodestar = sum(hours × rate) for all billable entries.
        """
        total_hours = Decimal("0.0")
        total_fees = Decimal("0.00")
        rate_weighted_sum = Decimal("0.00")

        for entry in entries:
            if not entry.billable:
                continue
            total_hours += entry.hours
            total_fees += entry.amount
            rate_weighted_sum += entry.rate * entry.hours

        weighted_rate = (
            (rate_weighted_sum / total_hours).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            if total_hours > 0 else Decimal("0.00")
        )

        return LodestarResult(
            base_lodestar=total_fees.quantize(Decimal("0.01")),
            total_hours=total_hours.quantize(Decimal("0.1")),
            weighted_rate=weighted_rate,
            adjusted_amount=total_fees.quantize(Decimal("0.01")),
        )

    def apply_multiplier(
        self, result: LodestarResult, multiplier: Decimal = Decimal("1.0"),
        justification: str = "",
    ) -> LodestarResult:
        """Apply a fee multiplier (enhancement or reduction)."""
        result.multiplier = multiplier
        result.adjusted_amount = (
            result.base_lodestar * multiplier
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        result.enhancement_justified = multiplier > Decimal("1.0")
        return result

    def johnson_factors(
        self, entries: Sequence[TimeEntry],
        case_complexity: str = "moderate",
        results_obtained: str = "",
    ) -> List[JohnsonFactor]:
        """Analyze the 12 Johnson factors for fee reasonableness.

        Produces a factor-by-factor assessment that can support
        or oppose a lodestar enhancement.
        """
        total_hours = sum(e.hours for e in entries if e.billable)
        factors: List[JohnsonFactor] = []

        for i, jf in enumerate(self._JOHNSON_FACTORS, 1):
            analysis = ""
            supports = False
            weight = 5

            if i == 1:  # Time and labor
                if total_hours > Decimal("100"):
                    analysis = (f"Extensive time commitment ({total_hours} hours) "
                                f"supports reasonable fee")
                    supports = True
                    weight = 7
                else:
                    analysis = f"Moderate time commitment ({total_hours} hours)"
                    weight = 5

            elif i == 3:  # Customary fee
                rates = [e.rate for e in entries if e.billable and e.rate > 0]
                if rates:
                    avg_rate = sum(rates) / len(rates)
                    market_mid = _MARKET_RATES["pro_se_litigant"]["mid"]
                    if avg_rate <= market_mid:
                        analysis = (f"Rate (${avg_rate}) at or below market "
                                    f"rate (${market_mid}) for locality")
                        supports = True
                        weight = 8
                    else:
                        analysis = (f"Rate (${avg_rate}) above market "
                                    f"rate (${market_mid})")
                        weight = 4

            elif i == 4:  # Amount involved / results
                if results_obtained:
                    analysis = f"Results: {results_obtained}"
                    supports = True
                    weight = 8
                else:
                    analysis = "Results pending — cannot fully assess"
                    weight = 5

            elif i == 5:  # Time limitations
                analysis = ("Pro se litigant faces strict court deadlines "
                            "without counsel support")
                supports = True
                weight = 6

            elif i == 7:  # Experience
                analysis = ("Pro se litigant — limited legal training but "
                            "demonstrates competent self-representation")
                weight = 4

            elif i == 8:  # Undesirability
                analysis = ("Family law custody disputes are emotionally "
                            "complex and often undesirable for attorneys")
                supports = True
                weight = 6

            elif i == 11:  # Novelty and difficulty
                complexity_map = {
                    "simple": ("Routine legal matter", False, 3),
                    "moderate": ("Moderate complexity — multiple issues", False, 5),
                    "complex": ("Complex multi-lane litigation", True, 7),
                    "exceptional": ("Exceptionally complex — 6 lanes, multiple courts", True, 9),
                }
                c = complexity_map.get(case_complexity, complexity_map["moderate"])
                analysis, supports, weight = c[0], c[1], c[2]

            else:
                analysis = f"Factor {i}: {jf['name']} — neutral assessment"
                weight = 5

            factors.append(JohnsonFactor(
                factor_number=i,
                factor_name=jf["name"],
                analysis=analysis,
                supports_enhancement=supports,
                weight=weight,
            ))

        return factors

    def compare_market_rate(
        self, requested_rate: Decimal, role: str = "pro_se_litigant",
    ) -> Dict[str, Any]:
        """Compare a requested rate to local market rates."""
        market = _MARKET_RATES.get(role, _MARKET_RATES["pro_se_litigant"])
        return {
            "requested_rate": str(requested_rate),
            "market_low": str(market["low"]),
            "market_mid": str(market["mid"]),
            "market_high": str(market["high"]),
            "within_market": market["low"] <= requested_rate <= market["high"],
            "comparison": (
                "below market" if requested_rate < market["low"]
                else "within market" if requested_rate <= market["high"]
                else "above market"
            ),
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "LodestarCalculator",
            "johnson_factors": len(self._JOHNSON_FACTORS),
            "market_rate_roles": len(_MARKET_RATES),
        }


# ---------------------------------------------------------------------------
# FeeShiftingAnalyzer
# ---------------------------------------------------------------------------


class FeeShiftingAnalyzer:
    """Analyzes fee-shifting eligibility under Michigan and federal law."""

    def analyze_statute(self, case_type: str) -> FeeShiftingAnalysis:
        """Analyze all available fee-shifting bases for a case type."""
        analysis = FeeShiftingAnalysis(case_type=case_type)

        # Check each basis
        bases: List[Dict[str, Any]] = []

        # MCR 2.403(O) — Case evaluation
        ce_result = self.check_mcr_2_403_O()
        if ce_result["eligible"]:
            bases.append(ce_result)

        # 42 USC §1988 — Civil rights
        if case_type in ("civil_rights", "federal_1983"):
            cr_result = self.check_42_usc_1988()
            if cr_result["eligible"]:
                bases.append(cr_result)

        # MCL 600.2591 — Frivolous actions
        friv_result = self.check_mcl_600_2591()
        if friv_result["eligible"]:
            bases.append(friv_result)

        # MCR 2.405 — Offer of judgment
        oj_result = self.check_offer_of_judgment()
        if oj_result["eligible"]:
            bases.append(oj_result)

        # MCL 600.2405 — General costs
        gen_result = self.check_mcl_600_2405()
        if gen_result["eligible"]:
            bases.append(gen_result)

        analysis.eligible_bases = bases
        if bases:
            # Recommend the strongest basis
            best = max(bases, key=lambda b: b.get("strength", 0))
            analysis.recommended_basis = best.get("authority", "")

        return analysis

    def check_42_usc_1988(self) -> Dict[str, Any]:
        """Analyze fee eligibility under 42 USC §1988.

        Prevailing party in a 42 USC §1983 civil rights action is
        entitled to reasonable attorney fees.  For pro se litigants,
        Kay v. Ehrler limits recovery — pro se attorneys generally
        cannot recover fees, but pro se non-attorneys in some circuits
        have argued for fees under specific circumstances.
        """
        return {
            "authority": "42 USC §1988",
            "eligible": True,
            "strength": 8,
            "requirements": [
                "Must be prevailing party in §1983 action",
                "Must demonstrate constitutional violation by state actor",
                "Fees must be reasonable under lodestar method",
            ],
            "pro_se_note": (
                "Kay v. Ehrler, 499 U.S. 432 (1991) limits pro se attorney "
                "fee recovery.  However, non-attorney pro se litigants may "
                "recover in limited circumstances where the statute "
                "specifically provides."
            ),
            "lane_applicability": ["A", "D", "E"],
        }

    def check_mcr_2_403_O(self) -> Dict[str, Any]:
        """Analyze fee eligibility under MCR 2.403(O).

        When a party rejects case evaluation and the verdict is not
        more favorable than the evaluation, the rejecting party must
        pay the other side's actual costs (including attorney fees)
        from the date of rejection.
        """
        return {
            "authority": "MCR 2.403(O)",
            "eligible": True,
            "strength": 7,
            "requirements": [
                "Case evaluation must have been conducted",
                "Opposing party must have rejected the evaluation",
                "Verdict must not be more favorable than evaluation to rejector",
                "Costs include reasonable attorney fees from rejection date",
            ],
            "calculation": (
                "Actual costs incurred from the date of case evaluation "
                "rejection, including reasonable attorney fees"
            ),
            "lane_applicability": ["A", "B", "D"],
        }

    def check_mcl_600_2591(self) -> Dict[str, Any]:
        """Analyze fee eligibility under MCL 600.2591.

        Allows recovery of fees when the opposing party's claims or
        defenses are frivolous — i.e., not well-grounded in fact,
        not warranted by existing law, and filed for improper purpose.
        """
        return {
            "authority": "MCL 600.2591",
            "eligible": True,
            "strength": 6,
            "requirements": [
                "Opposing party's claim or defense must be frivolous",
                "Frivolous = not well-grounded in fact or law",
                "Filed for improper purpose (harassment, delay, cost)",
                "Must prevail on the frivolousness claim",
            ],
            "standard": (
                "The court must find the claim or defense was: (1) not "
                "well-grounded in fact, (2) not warranted by existing law "
                "or good-faith argument for extension, and (3) interposed "
                "for improper purpose."
            ),
            "lane_applicability": ["A", "B", "D"],
        }

    def check_mcl_600_2405(self) -> Dict[str, Any]:
        """Analyze taxable costs under MCL 600.2405."""
        return {
            "authority": "MCL 600.2405",
            "eligible": True,
            "strength": 5,
            "requirements": [
                "Must be prevailing party",
                "Costs must be reasonable and actually incurred",
            ],
            "recoverable_items": [
                "Filing fees",
                "Service of process fees",
                "Witness fees and mileage",
                "Deposition costs",
                "Copying costs for exhibits",
            ],
            "lane_applicability": ["A", "B", "D"],
        }

    def check_offer_of_judgment(self) -> Dict[str, Any]:
        """Analyze fee eligibility under MCR 2.405 offer of judgment."""
        return {
            "authority": "MCR 2.405",
            "eligible": True,
            "strength": 6,
            "requirements": [
                "Offer of judgment must have been served",
                "Opposing party must have rejected the offer",
                "Judgment must be more favorable than offer to offeror",
                "Costs from date of rejection are recoverable",
            ],
            "lane_applicability": ["A", "B"],
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "FeeShiftingAnalyzer",
            "fee_shifting_bases": len(FeeShiftingBasis),
            "statutes_analyzed": 5,
        }


# ---------------------------------------------------------------------------
# CostBillPreparer
# ---------------------------------------------------------------------------


class CostBillPreparer:
    """Prepares a formal bill of costs for court filing."""

    def compile_costs(
        self, items: Sequence[CostItem], reimbursable_only: bool = True,
    ) -> List[CostItem]:
        """Compile cost items, optionally filtering to reimbursable only."""
        if reimbursable_only:
            return [i for i in items if i.reimbursable]
        return list(items)

    def verify_receipts(
        self, items: Sequence[CostItem],
    ) -> Dict[str, Any]:
        """Check which cost items have receipt documentation."""
        with_receipt: List[str] = []
        without_receipt: List[str] = []
        for item in items:
            if item.receipt_path:
                with_receipt.append(item.item_id)
            else:
                without_receipt.append(item.item_id)
        return {
            "total_items": len(items),
            "with_receipts": len(with_receipt),
            "without_receipts": len(without_receipt),
            "missing_receipt_ids": without_receipt,
            "documentation_rate": (
                round(len(with_receipt) / max(len(items), 1) * 100, 1)
            ),
        }

    def categorize(
        self, items: Sequence[CostItem],
    ) -> Dict[str, List[CostItem]]:
        """Group cost items by category."""
        grouped: Dict[str, List[CostItem]] = defaultdict(list)
        for item in items:
            grouped[item.category.value].append(item)
        return dict(grouped)

    def generate_bill_of_costs(
        self,
        items: Sequence[CostItem],
        case_number: str = "",
    ) -> str:
        """Generate a formatted Bill of Costs for court filing."""
        reimbursable = [i for i in items if i.reimbursable]
        total = sum(i.amount for i in reimbursable)

        lines = [
            "STATE OF MICHIGAN",
            f"IN THE {_COURT.upper()}",
            "COUNTY OF MUSKEGON",
            "",
            f"{_PLAINTIFF},".ljust(40) + f"Case No. {case_number}",
            "    Plaintiff,".ljust(40) + f"Hon. {_JUDGE}",
            "v.",
            f"{_DEFENDANT},",
            "    Defendant.",
            "_" * 60,
            "",
            "PLAINTIFF'S VERIFIED BILL OF COSTS",
            "PURSUANT TO MCR 2.625 AND MCL 600.2405",
            "=" * 60,
            "",
        ]

        # Group by category
        categorized = self.categorize(reimbursable)
        item_num = 1
        for cat_name, cat_items in sorted(categorized.items()):
            cat_total = sum(i.amount for i in cat_items)
            lines.append(f"  {cat_name.upper().replace('_', ' ')}:")
            for item in cat_items:
                lines.append(
                    f"    {item_num}. {item.date}  {item.description}"
                    f"  ${item.amount}"
                )
                item_num += 1
            lines.append(f"    Subtotal: ${cat_total}")
            lines.append("")

        lines.extend([
            "_" * 60,
            f"TOTAL COSTS REQUESTED: ${total}",
            "",
            "VERIFICATION",
            "",
            f"I, {_PLAINTIFF}, verify under penalty of perjury that the "
            "foregoing costs were actually and necessarily incurred in "
            "connection with this matter.",
            "",
            f"Date: {'_' * 20}",
            "",
            f"{'_' * 40}",
            f"{_PLAINTIFF}",
            "Pro Se",
        ])

        return "\n".join(lines)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "CostBillPreparer",
            "reimbursable_categories": sum(
                1 for c in FeeCategory if c.is_reimbursable
            ),
        }


# ---------------------------------------------------------------------------
# ProSeLitigantFees
# ---------------------------------------------------------------------------


class ProSeLitigantFees:
    """Analyzes fee recovery eligibility for pro se litigants.

    Key authority: Kay v. Ehrler, 499 U.S. 432 (1991) — the Supreme
    Court held that a pro se litigant who is also an attorney may NOT
    recover attorney fees under 42 USC §1988.  However, this does NOT
    necessarily bar non-attorney pro se litigants from all fee recovery.

    Michigan-specific considerations apply.
    """

    def analyze_fee_recovery_eligibility(
        self, is_attorney: bool = False, case_type: str = "family_law",
        statutes_invoked: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Analyze whether a pro se litigant can recover fees."""
        analysis: Dict[str, Any] = {
            "is_attorney": is_attorney,
            "case_type": case_type,
            "statutes_invoked": statutes_invoked or [],
            "eligible_for_fees": False,
            "eligible_for_costs": True,  # Costs generally recoverable
            "analysis": [],
            "recommendations": [],
        }

        # Kay v. Ehrler analysis
        if is_attorney:
            analysis["analysis"].append(
                "Kay v. Ehrler, 499 U.S. 432 (1991): Pro se attorneys "
                "CANNOT recover attorney fees under §1988."
            )
            analysis["eligible_for_fees"] = False
        else:
            analysis["analysis"].append(
                "Non-attorney pro se litigant — Kay v. Ehrler does not "
                "directly apply.  Fee recovery depends on specific statute."
            )

        # Statute-specific analysis
        statutes = statutes_invoked or []

        if "42_usc_1988" in statutes or "42 USC §1988" in statutes:
            if not is_attorney:
                analysis["analysis"].append(
                    "42 USC §1988 — some circuits allow non-attorney pro se "
                    "fee recovery; Michigan (6th Circuit) analysis required."
                )
                analysis["eligible_for_fees"] = True
            else:
                analysis["analysis"].append(
                    "42 USC §1988 — barred for pro se attorneys per Kay v. Ehrler."
                )

        if "mcr_2_403_o" in statutes or "MCR 2.403(O)" in statutes:
            analysis["analysis"].append(
                "MCR 2.403(O) — case evaluation sanctions include 'actual costs' "
                "which may include reasonable value of pro se time."
            )
            analysis["eligible_for_fees"] = True

        if "mcl_600_2591" in statutes or "MCL 600.2591" in statutes:
            analysis["analysis"].append(
                "MCL 600.2591 — frivolous action statute may authorize fee "
                "recovery including reasonable value of pro se litigant time."
            )
            analysis["eligible_for_fees"] = True

        # Costs are always recoverable for prevailing party
        analysis["recommendations"].append(
            "Document all time spent with contemporaneous records"
        )
        analysis["recommendations"].append(
            "Use a reasonable hourly rate for the locality "
            f"(${_MARKET_RATES['pro_se_litigant']['mid']}/hour suggested)"
        )
        analysis["recommendations"].append(
            "Maintain receipts for all out-of-pocket costs"
        )

        return analysis

    def document_hours(
        self, entries: Sequence[TimeEntry],
    ) -> Dict[str, Any]:
        """Validate time entry documentation quality."""
        issues: List[str] = []
        for entry in entries:
            if not entry.date:
                issues.append(f"Entry {entry.entry_id}: missing date")
            if not entry.description or len(entry.description) < 10:
                issues.append(
                    f"Entry {entry.entry_id}: description too brief "
                    f"(must describe specific work performed)"
                )
            if entry.hours <= Decimal("0"):
                issues.append(f"Entry {entry.entry_id}: zero or negative hours")
            if entry.hours > Decimal("12"):
                issues.append(
                    f"Entry {entry.entry_id}: {entry.hours} hours may be "
                    f"challenged as excessive for a single day"
                )

        return {
            "total_entries": len(entries),
            "issues_found": len(issues),
            "issues": issues,
            "documentation_quality": (
                "excellent" if not issues
                else "adequate" if len(issues) <= 2
                else "needs_improvement"
            ),
        }

    def calculate_reasonable_rate(
        self, experience_years: int = 0, case_complexity: str = "moderate",
    ) -> Dict[str, Any]:
        """Calculate a defensible hourly rate for pro se work.

        Michigan courts assess pro se rates based on:
        - Local market rates for similar legal work
        - Complexity of the matter
        - Pro se litigant's relevant experience
        """
        base = _MARKET_RATES["pro_se_litigant"]["mid"]

        # Adjust for complexity
        complexity_adj = {
            "simple": Decimal("-25.00"),
            "moderate": Decimal("0.00"),
            "complex": Decimal("25.00"),
            "exceptional": Decimal("50.00"),
        }
        adj = complexity_adj.get(case_complexity, Decimal("0.00"))
        adjusted = base + adj

        # Cap within market range
        market = _MARKET_RATES["pro_se_litigant"]
        capped = max(market["low"], min(market["high"], adjusted))

        return {
            "recommended_rate": str(capped),
            "market_range": {
                "low": str(market["low"]),
                "mid": str(market["mid"]),
                "high": str(market["high"]),
            },
            "complexity_adjustment": str(adj),
            "justification": (
                f"Rate of ${capped}/hour is within the Muskegon, MI market "
                f"range for pro se litigation work at {case_complexity} "
                f"complexity level."
            ),
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "ProSeLitigantFees",
            "market_rate_tiers": len(_MARKET_RATES),
        }


# ---------------------------------------------------------------------------
# Database layer
# ---------------------------------------------------------------------------

_PRAGMAS = textwrap.dedent("""\
    PRAGMA busy_timeout = 60000;
    PRAGMA journal_mode = WAL;
    PRAGMA cache_size = -32000;
    PRAGMA temp_store = MEMORY;
    PRAGMA synchronous = NORMAL;
""")

_CREATE_TIME_ENTRIES_SQL = textwrap.dedent("""\
    CREATE TABLE IF NOT EXISTS fee_time_entries (
        entry_id    TEXT PRIMARY KEY,
        date        TEXT,
        description TEXT,
        hours       TEXT DEFAULT '0.0',
        rate        TEXT DEFAULT '0.00',
        category    TEXT DEFAULT 'research',
        lane        TEXT,
        case_number TEXT,
        billable    INTEGER DEFAULT 1,
        notes       TEXT,
        created_at  TEXT DEFAULT (datetime('now'))
    )
""")

_CREATE_COST_ITEMS_SQL = textwrap.dedent("""\
    CREATE TABLE IF NOT EXISTS fee_cost_items (
        item_id       TEXT PRIMARY KEY,
        date          TEXT,
        description   TEXT,
        amount        TEXT DEFAULT '0.00',
        category      TEXT DEFAULT 'filing',
        receipt_path  TEXT,
        reimbursable  INTEGER DEFAULT 1,
        lane          TEXT,
        case_number   TEXT,
        notes         TEXT,
        created_at    TEXT DEFAULT (datetime('now'))
    )
""")

_CREATE_PETITIONS_SQL = textwrap.dedent("""\
    CREATE TABLE IF NOT EXISTS fee_petitions (
        petition_id     TEXT PRIMARY KEY,
        case_number     TEXT,
        lane            TEXT,
        status          TEXT DEFAULT 'draft',
        total_fees      TEXT DEFAULT '0.00',
        total_costs     TEXT DEFAULT '0.00',
        total_requested TEXT DEFAULT '0.00',
        legal_basis     TEXT,
        lodestar_json   TEXT,
        shifting_json   TEXT,
        created_at      TEXT DEFAULT (datetime('now')),
        updated_at      TEXT DEFAULT (datetime('now'))
    )
""")

_CREATE_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_fee_time_date "
    "ON fee_time_entries(date, category)",
    "CREATE INDEX IF NOT EXISTS idx_fee_time_lane "
    "ON fee_time_entries(lane, case_number)",
    "CREATE INDEX IF NOT EXISTS idx_fee_cost_date "
    "ON fee_cost_items(date, category)",
    "CREATE INDEX IF NOT EXISTS idx_fee_petition_case "
    "ON fee_petitions(case_number, status)",
]


def _ensure_tables(conn: sqlite3.Connection) -> None:
    conn.execute(_CREATE_TIME_ENTRIES_SQL)
    conn.execute(_CREATE_COST_ITEMS_SQL)
    conn.execute(_CREATE_PETITIONS_SQL)
    for idx in _CREATE_INDEXES_SQL:
        conn.execute(idx)
    conn.commit()


# ---------------------------------------------------------------------------
# FeePetitionEngine — orchestrator
# ---------------------------------------------------------------------------


class FeePetitionEngine:
    """Top-level orchestrator for fee petition preparation.

    Combines :class:`LodestarCalculator`, :class:`FeeShiftingAnalyzer`,
    :class:`CostBillPreparer`, and :class:`ProSeLitigantFees` into a
    unified fee petition system.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or _DB_PATH
        self._lodestar = LodestarCalculator()
        self._shifting = FeeShiftingAnalyzer()
        self._cost_preparer = CostBillPreparer()
        self._pro_se = ProSeLitigantFees()
        self._time_entries: List[TimeEntry] = []
        self._cost_items: List[CostItem] = []
        self._petitions: List[FeePetition] = []

    # -- time and cost entry --

    def add_time_entry(
        self,
        date: str,
        description: str,
        hours: Decimal,
        rate: Decimal = Decimal("100.00"),
        category: FeeCategory = FeeCategory.RESEARCH,
        lane: str = "",
        case_number: str = "",
    ) -> TimeEntry:
        """Add a time entry for fee calculation."""
        entry = TimeEntry(
            date=date,
            description=description,
            hours=hours,
            rate=rate,
            category=category,
            lane=lane,
            case_number=case_number or LANE_CASES.get(lane, ""),
        )
        self._time_entries.append(entry)
        return entry

    def add_cost_item(
        self,
        date: str,
        description: str,
        amount: Decimal,
        category: FeeCategory = FeeCategory.FILING,
        receipt_path: str = "",
        lane: str = "",
        case_number: str = "",
    ) -> CostItem:
        """Add a cost item for the bill of costs."""
        item = CostItem(
            date=date,
            description=description,
            amount=amount,
            category=category,
            receipt_path=receipt_path,
            reimbursable=category.is_reimbursable,
            lane=lane,
            case_number=case_number or LANE_CASES.get(lane, ""),
        )
        self._cost_items.append(item)
        return item

    # -- petition creation --

    def create_petition(
        self,
        case_number: str,
        lane: str = "",
        case_type: str = "family_law",
        include_lodestar: bool = True,
        include_shifting: bool = True,
    ) -> FeePetition:
        """Create a complete fee petition."""
        # Filter entries for this case
        case_entries = [
            e for e in self._time_entries
            if not case_number or e.case_number == case_number
        ]
        case_costs = [
            c for c in self._cost_items
            if not case_number or c.case_number == case_number
        ]

        petition = FeePetition(
            case_number=case_number,
            lane=lane,
            time_entries=case_entries,
            cost_items=case_costs,
        )

        # Calculate lodestar
        if include_lodestar and case_entries:
            lodestar = self._lodestar.calculate_base(case_entries)
            lodestar.johnson_factors = self._lodestar.johnson_factors(case_entries)
            petition.lodestar = lodestar
            petition.total_fees = lodestar.adjusted_amount

        # Analyze fee shifting
        if include_shifting:
            shifting = self._shifting.analyze_statute(case_type)
            shifting.case_number = case_number
            petition.fee_shifting = shifting
            petition.legal_basis = shifting.recommended_basis

        # Calculate total costs
        reimbursable = [c for c in case_costs if c.reimbursable]
        petition.total_costs = sum(
            (c.amount for c in reimbursable), Decimal("0.00")
        ).quantize(Decimal("0.01"))

        # Total requested
        petition.total_requested = (
            petition.total_fees + petition.total_costs
        ).quantize(Decimal("0.01"))

        self._petitions.append(petition)
        return petition

    # -- calculation --

    def calculate_total(
        self, case_number: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Calculate total fees and costs."""
        entries = self._time_entries
        costs = self._cost_items
        if case_number:
            entries = [e for e in entries if e.case_number == case_number]
            costs = [c for c in costs if c.case_number == case_number]

        total_fees = sum(
            (e.amount for e in entries if e.billable), Decimal("0.00")
        )
        total_costs = sum(
            (c.amount for c in costs if c.reimbursable), Decimal("0.00")
        )
        total_hours = sum(
            (e.hours for e in entries if e.billable), Decimal("0.0")
        )

        return {
            "total_fees": str(total_fees.quantize(Decimal("0.01"))),
            "total_costs": str(total_costs.quantize(Decimal("0.01"))),
            "total_requested": str(
                (total_fees + total_costs).quantize(Decimal("0.01"))
            ),
            "total_hours": str(total_hours.quantize(Decimal("0.1"))),
            "time_entries": len(entries),
            "cost_items": len(costs),
        }

    def generate_itemization(
        self, case_number: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a detailed itemization of fees and costs."""
        entries = self._time_entries
        costs = self._cost_items
        if case_number:
            entries = [e for e in entries if e.case_number == case_number]
            costs = [c for c in costs if c.case_number == case_number]

        # Group time entries by category
        time_by_cat: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for e in entries:
            time_by_cat[e.category.value].append(e.to_dict())

        # Group costs by category
        cost_by_cat: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for c in costs:
            cost_by_cat[c.category.value].append(c.to_dict())

        return {
            "time_entries_by_category": dict(time_by_cat),
            "cost_items_by_category": dict(cost_by_cat),
            "summary": self.calculate_total(case_number),
        }

    # -- recoverability assessment --

    def assess_recoverability(
        self,
        case_number: str = "",
        case_type: str = "family_law",
        is_attorney: bool = False,
    ) -> Dict[str, Any]:
        """Assess overall fee recoverability."""
        # Fee shifting analysis
        shifting = self._shifting.analyze_statute(case_type)

        # Pro se analysis
        pro_se = self._pro_se.analyze_fee_recovery_eligibility(
            is_attorney=is_attorney,
            case_type=case_type,
        )

        # Documentation quality
        doc_quality = self._pro_se.document_hours(self._time_entries)

        # Receipt verification
        receipt_check = self._cost_preparer.verify_receipts(self._cost_items)

        totals = self.calculate_total(case_number or None)

        return {
            "case_number": case_number,
            "case_type": case_type,
            "total_requested": totals["total_requested"],
            "fee_shifting_bases": len(shifting.eligible_bases),
            "recommended_basis": shifting.recommended_basis,
            "pro_se_eligible": pro_se["eligible_for_fees"],
            "cost_recovery_eligible": pro_se["eligible_for_costs"],
            "documentation_quality": doc_quality["documentation_quality"],
            "receipt_coverage": f"{receipt_check['documentation_rate']}%",
            "overall_assessment": (
                "STRONG" if (
                    pro_se["eligible_for_fees"]
                    and doc_quality["documentation_quality"] == "excellent"
                    and receipt_check["documentation_rate"] >= 80
                )
                else "MODERATE" if (
                    pro_se["eligible_for_costs"]
                    and doc_quality["documentation_quality"] != "needs_improvement"
                )
                else "WEAK"
            ),
        }

    # -- bill of costs --

    def generate_bill_of_costs(
        self, case_number: str = "",
    ) -> str:
        """Generate a formatted bill of costs."""
        costs = self._cost_items
        if case_number:
            costs = [c for c in costs if c.case_number == case_number]
        return self._cost_preparer.generate_bill_of_costs(costs, case_number)

    # -- persistence --

    def persist(self) -> int:
        """Write fee data to the database."""
        if not self._db_path.exists():
            logger.warning("Database not found — cannot persist")
            return 0

        try:
            conn = sqlite3.connect(str(self._db_path), timeout=60)
            conn.executescript(_PRAGMAS)
        except sqlite3.Error as exc:
            logger.error("DB connection failed: %s", exc)
            return 0

        try:
            _ensure_tables(conn)
            saved = 0

            # Persist time entries
            te_rows: List[Tuple[Any, ...]] = []
            for e in self._time_entries:
                te_rows.append((
                    e.entry_id, e.date, e.description,
                    str(e.hours), str(e.rate), e.category.value,
                    e.lane, e.case_number, 1 if e.billable else 0, e.notes,
                ))
            if te_rows:
                conn.executemany(
                    "INSERT OR REPLACE INTO fee_time_entries "
                    "(entry_id, date, description, hours, rate, category, "
                    "lane, case_number, billable, notes) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?)",
                    te_rows,
                )
                saved += len(te_rows)

            # Persist cost items
            ci_rows: List[Tuple[Any, ...]] = []
            for c in self._cost_items:
                ci_rows.append((
                    c.item_id, c.date, c.description,
                    str(c.amount), c.category.value, c.receipt_path,
                    1 if c.reimbursable else 0, c.lane, c.case_number, c.notes,
                ))
            if ci_rows:
                conn.executemany(
                    "INSERT OR REPLACE INTO fee_cost_items "
                    "(item_id, date, description, amount, category, "
                    "receipt_path, reimbursable, lane, case_number, notes) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?)",
                    ci_rows,
                )
                saved += len(ci_rows)

            # Persist petitions
            pet_rows: List[Tuple[Any, ...]] = []
            for p in self._petitions:
                pet_rows.append((
                    p.petition_id, p.case_number, p.lane, p.status.value,
                    str(p.total_fees), str(p.total_costs),
                    str(p.total_requested), p.legal_basis,
                    json.dumps(p.lodestar.to_dict()) if p.lodestar else None,
                    json.dumps(p.fee_shifting.to_dict()) if p.fee_shifting else None,
                ))
            if pet_rows:
                conn.executemany(
                    "INSERT OR REPLACE INTO fee_petitions "
                    "(petition_id, case_number, lane, status, total_fees, "
                    "total_costs, total_requested, legal_basis, "
                    "lodestar_json, shifting_json) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?)",
                    pet_rows,
                )
                saved += len(pet_rows)

            conn.commit()
            return saved
        except sqlite3.Error as exc:
            logger.error("Persist failed: %s", exc)
            return 0
        finally:
            conn.close()

    # -- stats --

    def get_stats(self) -> Dict[str, Any]:
        """Return runtime statistics."""
        return {
            "module": "fee_petition_engine",
            "time_entries": len(self._time_entries),
            "cost_items": len(self._cost_items),
            "petitions": len(self._petitions),
            "db_path": str(self._db_path),
            "lodestar": self._lodestar.get_stats(),
            "fee_shifting": self._shifting.get_stats(),
            "cost_preparer": self._cost_preparer.get_stats(),
            "pro_se_fees": self._pro_se.get_stats(),
        }

    def reset(self) -> None:
        """Clear all loaded data."""
        self._time_entries.clear()
        self._cost_items.clear()
        self._petitions.clear()


# ---------------------------------------------------------------------------
# CLI demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sys.stdout = open(  # noqa: SIM115
        sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace"
    )
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print("=" * 60)
    print("  Fee Petition Engine — LitigationOS")
    print("=" * 60)
    print()

    fpe = FeePetitionEngine()

    # Add time entries
    fpe.add_time_entry(
        date="2026-01-15", description="Research MCR 2.403(O) case evaluation sanctions",
        hours=Decimal("3.5"), rate=Decimal("100.00"),
        category=FeeCategory.RESEARCH, lane="A",
    )
    fpe.add_time_entry(
        date="2026-01-16", description="Draft motion to compel discovery",
        hours=Decimal("5.0"), rate=Decimal("100.00"),
        category=FeeCategory.DRAFTING, lane="A",
    )
    fpe.add_time_entry(
        date="2026-01-20", description="Court appearance — motion hearing",
        hours=Decimal("2.0"), rate=Decimal("100.00"),
        category=FeeCategory.COURT_APPEARANCE, lane="A",
    )

    # Add cost items
    fpe.add_cost_item(
        date="2026-01-16", description="Motion filing fee",
        amount=Decimal("20.00"), category=FeeCategory.FILING, lane="A",
        receipt_path="receipts/filing_20260116.pdf",
    )
    fpe.add_cost_item(
        date="2026-01-16", description="Copies for service (25 pages)",
        amount=Decimal("6.25"), category=FeeCategory.COPYING, lane="A",
        receipt_path="receipts/copies_20260116.pdf",
    )

    # Create petition
    petition = fpe.create_petition(
        case_number="2024-001507-DC", lane="A",
    )
    print(f"Petition: {petition.petition_id}")
    print(f"  Total fees: ${petition.total_fees}")
    print(f"  Total costs: ${petition.total_costs}")
    print(f"  Total requested: ${petition.total_requested}")
    print(f"  Legal basis: {petition.legal_basis}")
    print()

    # Assess recoverability
    assessment = fpe.assess_recoverability(
        case_number="2024-001507-DC", case_type="family_law",
    )
    print(f"Recoverability: {assessment['overall_assessment']}")
    print(f"  Fee shifting bases: {assessment['fee_shifting_bases']}")
    print(f"  Documentation: {assessment['documentation_quality']}")
    print(f"  Receipts: {assessment['receipt_coverage']}")
    print()

    # Bill of costs
    bill = fpe.generate_bill_of_costs("2024-001507-DC")
    print(bill[:500])
    print("...")
    print()

    stats = fpe.get_stats()
    print(f"Stats: {json.dumps(stats, indent=2)}")
