# -*- coding: utf-8 -*-
"""
Garnishment Engine — LitigationOS Legal AI Subsystem
=====================================================
Michigan garnishment and asset recovery engine.  Handles periodic
(wage) and non-periodic (bank) garnishments, exemption analysis,
withholding calculations, and SCAO form generation per Michigan
Court Rules and the Revised Judicature Act.

Case Context
------------
    Plaintiff:  Andrew James Pigors (Pro Se)
    Defendant:  Emily A. Watson
    Child:      L.D.W. (per MCR 8.119(H)) — Male
    Judge:      Hon. Jenny L. McNeill — 14th Circuit Court
    Cases:      2024-001507-DC, 2025-002760-CZ, 2023-5907-PP, COA 366810

Michigan Rules & Statutes
-------------------------
    MCL 600.4001 – Garnishment; definitions
    MCL 600.4011 – Garnishment; periodic
    MCL 600.4012 – Exemptions from garnishment
    MCL 600.4061 – Garnishment; supplementary proceedings
    MCL 600.4065 – Installment payments
    MCR 3.101  – Garnishment after judgment
    15 USC § 1673 – Federal wage garnishment restrictions
    SCAO Forms: MC 14 (Request and Writ), MC 15 (Disclosure),
                MC 16 (Objection), MC 50 (Periodic Garnishment)

Usage::

    from legal_ai.garnishment_engine import GarnishmentEngine

    engine = GarnishmentEngine()
    req = engine.create_garnishment(
        garnishment_type=GarnishmentType.PERIODIC,
        debtor_name="Emily A. Watson",
        garnishee_name="Employer LLC",
        amount=Decimal("5000.00"),
    )
    calc = engine.calculate_amounts(req.request_id)

Zero external dependencies.  CPU-first.  Local-only.
"""
from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import sys
import uuid
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger("legal_ai.garnishment_engine")

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

# ---------------------------------------------------------------------------
# Federal / state garnishment constants
# ---------------------------------------------------------------------------
# 15 USC § 1673(a) — federal minimum hourly wage ($7.25 as of 2024)
_FEDERAL_MINIMUM_WAGE = Decimal("7.25")
# 30 × federal minimum wage per week
_FEDERAL_WEEKLY_THRESHOLD = _FEDERAL_MINIMUM_WAGE * 30
# Maximum percentage of disposable earnings (25%)
_FEDERAL_MAX_GARNISHMENT_PCT = Decimal("0.25")

# Michigan MCL 600.4012 — state exemptions
_MI_HOUSEHOLD_GOODS_EXEMPTION = Decimal("1000.00")
_MI_HOMESTEAD_EXEMPTION = Decimal("40475.00")  # MCL 600.6023(1)(h)

# Pay periods
_PAY_PERIODS = {
    "weekly": Decimal("1"),
    "biweekly": Decimal("2"),
    "semimonthly": Decimal("2.166667"),
    "monthly": Decimal("4.333333"),
}

# ---------------------------------------------------------------------------
# SCAO form references
# ---------------------------------------------------------------------------
_SCAO_FORMS: Dict[str, Dict[str, str]] = {
    "MC14": {
        "name": "Request and Writ of Garnishment (Periodic)",
        "number": "MC 14",
        "mcr": "MCR 3.101(G)",
        "description": "Initiates periodic garnishment against wages.",
    },
    "MC15": {
        "name": "Garnishee Disclosure",
        "number": "MC 15",
        "mcr": "MCR 3.101(H)",
        "description": "Garnishee discloses property/funds held.",
    },
    "MC16": {
        "name": "Objection to Garnishment / Claim of Exemption",
        "number": "MC 16",
        "mcr": "MCR 3.101(M)",
        "description": "Debtor objects or claims exemption.",
    },
    "MC50": {
        "name": "Writ of Garnishment (Periodic)",
        "number": "MC 50",
        "mcr": "MCR 3.101(G)",
        "description": "Periodic wage garnishment writ.",
    },
}


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class GarnishmentType(str, Enum):
    """Types of garnishment under Michigan law."""

    PERIODIC = "periodic"           # MCL 600.4011 — wages
    NON_PERIODIC = "non_periodic"   # MCL 600.4011 — bank accounts
    SUPPLEMENTARY = "supplementary" # MCL 600.4061 — supplementary proceedings

    @property
    def mcl_reference(self) -> str:
        _refs = {
            "periodic": "MCL 600.4011",
            "non_periodic": "MCL 600.4011",
            "supplementary": "MCL 600.4061",
        }
        return _refs.get(self.value, "MCL 600.4001")


class ExemptionType(str, Enum):
    """Exemption categories under federal and Michigan law."""

    FEDERAL_MINIMUM = "federal_minimum"       # 15 USC § 1673
    STATE_MINIMUM = "state_minimum"           # MCL 600.4012
    HEAD_OF_HOUSEHOLD = "head_of_household"   # MCL 600.4012
    PUBLIC_BENEFITS = "public_benefits"       # MCL 600.4012(1)
    PENSION = "pension"                       # MCL 600.4012(1)(f)
    HOMESTEAD = "homestead"                   # MCL 600.6023(1)(h)

    @property
    def legal_basis(self) -> str:
        _refs = {
            "federal_minimum": "15 USC § 1673(a)",
            "state_minimum": "MCL 600.4012",
            "head_of_household": "MCL 600.4012",
            "public_benefits": "MCL 600.4012(1)",
            "pension": "MCL 600.4012(1)(f)",
            "homestead": "MCL 600.6023(1)(h)",
        }
        return _refs.get(self.value, "MCL 600.4012")


class GarnishmentStatus(str, Enum):
    """Status of a garnishment proceeding."""

    DRAFT = "draft"
    FILED = "filed"
    SERVED = "served"
    ACTIVE = "active"
    OBJECTED = "objected"
    SATISFIED = "satisfied"
    TERMINATED = "terminated"
    SUSPENDED = "suspended"


class PayPeriod(str, Enum):
    """Standard pay period frequencies."""

    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    SEMIMONTHLY = "semimonthly"
    MONTHLY = "monthly"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class GarnishmentRequest:
    """A single garnishment request with tracking metadata."""

    request_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    garnishment_type: GarnishmentType = GarnishmentType.PERIODIC
    debtor_name: str = ""
    garnishee_name: str = ""
    amount: Decimal = Decimal("0.00")
    exempt_amount: Decimal = Decimal("0.00")
    status: GarnishmentStatus = GarnishmentStatus.DRAFT
    filed_date: str = ""
    case_number: str = ""
    court: str = _COURT
    judgment_date: str = ""
    judgment_amount: Decimal = Decimal("0.00")
    costs: Decimal = Decimal("0.00")
    interest_rate: Decimal = Decimal("0.00")
    total_collected: Decimal = Decimal("0.00")
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "garnishment_type": self.garnishment_type.value,
            "debtor_name": self.debtor_name,
            "garnishee_name": self.garnishee_name,
            "amount": str(self.amount),
            "exempt_amount": str(self.exempt_amount),
            "status": self.status.value,
            "filed_date": self.filed_date,
            "case_number": self.case_number,
            "court": self.court,
            "judgment_date": self.judgment_date,
            "judgment_amount": str(self.judgment_amount),
            "costs": str(self.costs),
            "interest_rate": str(self.interest_rate),
            "total_collected": str(self.total_collected),
            "created_at": self.created_at,
        }

    @property
    def remaining_balance(self) -> Decimal:
        return max(Decimal("0.00"), self.amount - self.total_collected)


@dataclass
class ExemptionResult:
    """Result of an exemption analysis."""

    exemption_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    exemption_type: ExemptionType = ExemptionType.FEDERAL_MINIMUM
    gross_income: Decimal = Decimal("0.00")
    disposable_income: Decimal = Decimal("0.00")
    exempt_amount: Decimal = Decimal("0.00")
    garnishable_amount: Decimal = Decimal("0.00")
    pay_period: str = "weekly"
    dependents: int = 0
    legal_basis: str = ""
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "exemption_id": self.exemption_id,
            "exemption_type": self.exemption_type.value,
            "gross_income": str(self.gross_income),
            "disposable_income": str(self.disposable_income),
            "exempt_amount": str(self.exempt_amount),
            "garnishable_amount": str(self.garnishable_amount),
            "pay_period": self.pay_period,
            "dependents": self.dependents,
            "legal_basis": self.legal_basis,
            "notes": self.notes,
        }


@dataclass
class PaymentRecord:
    """Record of a garnishment payment received."""

    payment_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    request_id: str = ""
    amount: Decimal = Decimal("0.00")
    payment_date: str = ""
    garnishee_name: str = ""
    pay_period_end: str = ""
    cumulative_total: Decimal = Decimal("0.00")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "payment_id": self.payment_id,
            "request_id": self.request_id,
            "amount": str(self.amount),
            "payment_date": self.payment_date,
            "garnishee_name": self.garnishee_name,
            "pay_period_end": self.pay_period_end,
            "cumulative_total": str(self.cumulative_total),
        }


@dataclass
class FormOutput:
    """Generated form metadata."""

    form_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    form_number: str = ""
    form_name: str = ""
    request_id: str = ""
    content_hash: str = ""
    fields: Dict[str, str] = field(default_factory=dict)
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "form_id": self.form_id,
            "form_number": self.form_number,
            "form_name": self.form_name,
            "request_id": self.request_id,
            "content_hash": self.content_hash,
            "fields": self.fields,
            "generated_at": self.generated_at,
        }


# ---------------------------------------------------------------------------
# ExemptionAnalyzer
# ---------------------------------------------------------------------------


class ExemptionAnalyzer:
    """Analyze garnishment exemptions under federal and Michigan law.

    Implements the dual-test from 15 USC § 1673 and the Michigan
    exemptions under MCL 600.4012.  The lesser of the two limits
    controls the maximum withholding.
    """

    def __init__(self) -> None:
        self._analyses: List[ExemptionResult] = []

    def calculate_exempt_amount(
        self,
        income: Decimal,
        dependents: int = 0,
        pay_period: str = "weekly",
        is_head_of_household: bool = False,
        has_public_benefits: bool = False,
        has_pension: bool = False,
    ) -> Decimal:
        """Calculate total exempt amount using the more protective limit.

        Under 15 USC § 1673(a), garnishment is limited to the lesser of:
          (1) 25% of disposable earnings, OR
          (2) the amount by which disposable earnings exceed 30× the
              federal minimum wage ($7.25/hr).

        Michigan MCL 600.4012 may provide additional protection for
        head-of-household, public-benefit recipients, and pension income.
        """
        if income <= Decimal("0"):
            return income

        period_multiplier = _PAY_PERIODS.get(pay_period, Decimal("1"))
        weekly_threshold = _FEDERAL_WEEKLY_THRESHOLD  # 30 × $7.25 = $217.50

        # Normalize to weekly for federal calculation
        weekly_income = income / period_multiplier

        # Federal test 1: 25% of disposable earnings
        test1 = weekly_income * _FEDERAL_MAX_GARNISHMENT_PCT

        # Federal test 2: amount exceeding 30× minimum wage
        test2 = max(Decimal("0"), weekly_income - weekly_threshold)

        # Lesser of the two is the max garnishable (federal)
        federal_garnishable = min(test1, test2)
        federal_exempt = weekly_income - federal_garnishable

        # Convert back to pay period
        exempt = (federal_exempt * period_multiplier).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # Michigan add-ons
        if has_public_benefits:
            exempt = income  # 100% exempt — MCL 600.4012(1)
        elif has_pension:
            exempt = income  # pension exempt — MCL 600.4012(1)(f)
        elif is_head_of_household and dependents > 0:
            # head-of-household gets larger exemption
            hoh_exempt = income * Decimal("0.60")
            exempt = max(exempt, hoh_exempt)

        exempt = min(exempt, income)

        result = ExemptionResult(
            exemption_type=ExemptionType.FEDERAL_MINIMUM,
            gross_income=income,
            disposable_income=income,
            exempt_amount=exempt,
            garnishable_amount=max(Decimal("0"), income - exempt),
            pay_period=pay_period,
            dependents=dependents,
            legal_basis="15 USC § 1673(a); MCL 600.4012",
        )
        self._analyses.append(result)
        return exempt

    def check_federal_limits(
        self, weekly_disposable: Decimal,
    ) -> Dict[str, Any]:
        """Apply the 15 USC § 1673 two-part federal test.

        Returns both test results and the controlling limit.
        """
        test1 = weekly_disposable * _FEDERAL_MAX_GARNISHMENT_PCT
        test2 = max(Decimal("0"), weekly_disposable - _FEDERAL_WEEKLY_THRESHOLD)
        garnishable = min(test1, test2)

        return {
            "weekly_disposable": str(weekly_disposable),
            "test_1_25_percent": str(test1.quantize(Decimal("0.01"))),
            "test_2_excess_over_threshold": str(test2.quantize(Decimal("0.01"))),
            "threshold_30x_minimum": str(_FEDERAL_WEEKLY_THRESHOLD),
            "max_garnishable": str(garnishable.quantize(Decimal("0.01"))),
            "controlling_test": "25% rule" if test1 < test2 else "30× rule",
            "legal_basis": "15 USC § 1673(a)",
            "fully_exempt": weekly_disposable <= _FEDERAL_WEEKLY_THRESHOLD,
        }

    def check_state_limits(
        self,
        income: Decimal,
        is_head_of_household: bool = False,
        dependents: int = 0,
    ) -> Dict[str, Any]:
        """Apply Michigan MCL 600.4012 state exemption limits."""
        state_exempt = Decimal("0")
        exemptions_applied: List[str] = []

        # Base: Michigan follows federal limits as floor
        federal_garnishable = income * _FEDERAL_MAX_GARNISHMENT_PCT
        state_exempt = income - federal_garnishable

        if is_head_of_household and dependents > 0:
            hoh_exempt = income * Decimal("0.60")
            if hoh_exempt > state_exempt:
                state_exempt = hoh_exempt
                exemptions_applied.append("Head of household — MCL 600.4012")

        state_exempt = min(state_exempt, income)

        return {
            "income": str(income),
            "state_exempt": str(state_exempt.quantize(Decimal("0.01"))),
            "garnishable": str(max(Decimal("0"), income - state_exempt).quantize(Decimal("0.01"))),
            "is_head_of_household": is_head_of_household,
            "dependents": dependents,
            "exemptions_applied": exemptions_applied,
            "legal_basis": "MCL 600.4012",
        }

    def identify_protected_assets(self) -> List[Dict[str, Any]]:
        """List asset categories protected from garnishment in Michigan."""
        return [
            {
                "asset": "Public assistance / benefits",
                "exemption": "100% exempt",
                "legal_basis": "MCL 600.4012(1)",
                "type": ExemptionType.PUBLIC_BENEFITS.value,
            },
            {
                "asset": "Pension / retirement benefits",
                "exemption": "100% exempt",
                "legal_basis": "MCL 600.4012(1)(f)",
                "type": ExemptionType.PENSION.value,
            },
            {
                "asset": "Homestead",
                "exemption": f"Up to ${_MI_HOMESTEAD_EXEMPTION}",
                "legal_basis": "MCL 600.6023(1)(h)",
                "type": ExemptionType.HOMESTEAD.value,
            },
            {
                "asset": "Household goods / provisions",
                "exemption": f"Up to ${_MI_HOUSEHOLD_GOODS_EXEMPTION}",
                "legal_basis": "MCL 600.6023(1)(a)",
                "type": ExemptionType.STATE_MINIMUM.value,
            },
            {
                "asset": "Wages below 30× federal minimum",
                "exemption": "100% exempt (federal floor)",
                "legal_basis": "15 USC § 1673(a)",
                "type": ExemptionType.FEDERAL_MINIMUM.value,
            },
            {
                "asset": "Head of household earnings (60%)",
                "exemption": "60% of earnings if head of household with dependents",
                "legal_basis": "MCL 600.4012",
                "type": ExemptionType.HEAD_OF_HOUSEHOLD.value,
            },
        ]

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "ExemptionAnalyzer",
            "total_analyses": len(self._analyses),
            "federal_minimum_wage": str(_FEDERAL_MINIMUM_WAGE),
            "weekly_threshold": str(_FEDERAL_WEEKLY_THRESHOLD),
        }


# ---------------------------------------------------------------------------
# WageGarnishmentCalculator
# ---------------------------------------------------------------------------


class WageGarnishmentCalculator:
    """Calculate wage withholding amounts per MCR 3.101 / MCL 600.4011.

    Generates employer instructions and tracks payments against
    the total judgment balance.
    """

    def __init__(self) -> None:
        self._exemption_analyzer = ExemptionAnalyzer()
        self._payments: List[PaymentRecord] = []

    def calculate_withholding(
        self,
        gross: Decimal,
        deductions: Decimal = Decimal("0.00"),
        pay_period: str = "biweekly",
        dependents: int = 0,
        is_head_of_household: bool = False,
    ) -> Decimal:
        """Calculate the garnishment withholding for one pay period.

        Parameters
        ----------
        gross : Decimal
            Gross earnings for the pay period.
        deductions : Decimal
            Mandatory deductions (taxes, FICA, health ins).
        pay_period : str
            One of weekly, biweekly, semimonthly, monthly.
        dependents : int
            Number of dependents.
        is_head_of_household : bool
            Whether debtor is head of household.

        Returns
        -------
        Decimal
            Amount to withhold for garnishment this period.
        """
        disposable = gross - deductions
        if disposable <= Decimal("0"):
            return Decimal("0.00")

        exempt = self._exemption_analyzer.calculate_exempt_amount(
            income=disposable,
            dependents=dependents,
            pay_period=pay_period,
            is_head_of_household=is_head_of_household,
        )

        withholding = max(Decimal("0"), disposable - exempt)
        return withholding.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def generate_employer_instructions(
        self,
        request: GarnishmentRequest,
        pay_period: str = "biweekly",
    ) -> Dict[str, Any]:
        """Generate employer instructions for wage garnishment.

        These instructions accompany MC 50 (Periodic Garnishment).
        The employer must withhold per-period and remit to the court.
        """
        instructions: Dict[str, Any] = {
            "form": "MC 50 — Writ of Garnishment (Periodic)",
            "mcr": "MCR 3.101(G)",
            "case_number": request.case_number,
            "court": request.court,
            "debtor": request.debtor_name,
            "garnishee_employer": request.garnishee_name,
            "judgment_amount": str(request.judgment_amount),
            "total_owed": str(request.amount),
            "pay_period": pay_period,
            "instructions": [
                "Withhold the lesser of (a) 25% of disposable earnings or "
                "(b) the amount exceeding 30× $7.25/hr for the pay period.",
                "Disposable earnings = gross wages minus legally required deductions "
                "(federal/state tax, FICA, mandatory retirement).",
                "Do NOT deduct voluntary deductions (401k, union dues, insurance) "
                "before calculating disposable earnings.",
                f"Continue withholding each {pay_period} pay period until the "
                f"total of ${request.amount} is satisfied or court orders otherwise.",
                "Remit withheld amounts to the court within the time specified in the writ.",
                "If the employee separates, notify the court and provide last-known address.",
            ],
            "legal_basis": [
                "15 USC § 1673(a) — federal wage garnishment limits",
                "MCL 600.4011 — Michigan garnishment of periodic earnings",
                "MCL 600.4012 — exemptions from garnishment",
                "MCR 3.101 — garnishment after judgment",
            ],
        }
        return instructions

    def track_payments(
        self,
        request_id: str,
        amount: Decimal,
        payment_date: str = "",
        garnishee_name: str = "",
    ) -> PaymentRecord:
        """Record a garnishment payment."""
        cumulative = sum(
            (p.amount for p in self._payments if p.request_id == request_id),
            Decimal("0"),
        ) + amount

        record = PaymentRecord(
            request_id=request_id,
            amount=amount,
            payment_date=payment_date or date.today().isoformat(),
            garnishee_name=garnishee_name,
            cumulative_total=cumulative,
        )
        self._payments.append(record)
        return record

    def calculate_remaining_balance(
        self,
        request: GarnishmentRequest,
    ) -> Dict[str, Any]:
        """Calculate remaining balance on a garnishment."""
        payments = [p for p in self._payments if p.request_id == request.request_id]
        total_paid = sum((p.amount for p in payments), Decimal("0"))
        remaining = max(Decimal("0"), request.amount - total_paid)

        return {
            "request_id": request.request_id,
            "judgment_amount": str(request.amount),
            "total_paid": str(total_paid),
            "remaining_balance": str(remaining),
            "payment_count": len(payments),
            "is_satisfied": remaining <= Decimal("0"),
            "last_payment": payments[-1].to_dict() if payments else None,
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "WageGarnishmentCalculator",
            "total_payments_tracked": len(self._payments),
            "unique_requests": len({p.request_id for p in self._payments}),
        }


# ---------------------------------------------------------------------------
# BankGarnishmentProcessor
# ---------------------------------------------------------------------------


class BankGarnishmentProcessor:
    """Process non-periodic (bank account) garnishments.

    Under MCL 600.4011, non-periodic garnishment freezes funds held
    by a financial institution at the time the writ is served.  The
    debtor may claim exemptions under MCL 600.4012.
    """

    def __init__(self) -> None:
        self._accounts: List[Dict[str, Any]] = []
        self._objections: List[Dict[str, Any]] = []

    def identify_accounts(
        self,
        debtor_name: str,
        known_institutions: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Identify potential accounts for garnishment.

        In practice this would integrate with discovery responses.
        Here we build a structured checklist for the litigant.
        """
        institutions = known_institutions or []
        accounts: List[Dict[str, Any]] = []

        for idx, inst in enumerate(institutions, 1):
            account = {
                "account_id": uuid.uuid4().hex[:10],
                "institution": inst,
                "debtor_name": debtor_name,
                "status": "identified",
                "discovery_source": "interrogatory_responses",
                "notes": "",
            }
            accounts.append(account)

        self._accounts.extend(accounts)
        return accounts

    def calculate_exempt_balance(
        self,
        account_balance: Decimal,
        has_public_benefits: bool = False,
        has_pension_deposits: bool = False,
        has_federal_benefits: bool = False,
    ) -> Dict[str, Any]:
        """Calculate exempt vs. garnishable balance in a bank account.

        Certain deposits are exempt even after deposit into a bank:
        - Public benefits (MCL 600.4012(1))
        - Pension/retirement (MCL 600.4012(1)(f))
        - Federal benefits (31 CFR 212 — automatic protection)
        """
        exempt = Decimal("0")
        exemptions: List[str] = []

        if has_public_benefits:
            exempt = account_balance
            exemptions.append("Public benefits — MCL 600.4012(1)")

        if has_pension_deposits:
            exempt = account_balance
            exemptions.append("Pension deposits — MCL 600.4012(1)(f)")

        if has_federal_benefits:
            # Federal benefits have automatic 2-month look-back
            two_month_amount = min(account_balance, Decimal("5000.00"))
            exempt = max(exempt, two_month_amount)
            exemptions.append("Federal benefits — 31 CFR 212")

        exempt = min(exempt, account_balance)
        garnishable = max(Decimal("0"), account_balance - exempt)

        return {
            "account_balance": str(account_balance),
            "exempt_amount": str(exempt),
            "garnishable_amount": str(garnishable),
            "exemptions_applied": exemptions,
            "is_fully_exempt": garnishable <= Decimal("0"),
            "legal_basis": "MCL 600.4011; MCL 600.4012",
        }

    def generate_garnishment_order(
        self,
        request: GarnishmentRequest,
        institution: str,
    ) -> Dict[str, Any]:
        """Generate a non-periodic garnishment order for a bank.

        The writ orders the institution to hold funds and disclose
        the account balance via MC 15 (Garnishee Disclosure).
        """
        return {
            "form": "MC 14 — Request and Writ of Garnishment (Non-Periodic)",
            "mcr": "MCR 3.101(F)",
            "case_number": request.case_number,
            "court": request.court,
            "plaintiff": _PLAINTIFF,
            "defendant": request.debtor_name,
            "garnishee": institution,
            "amount_claimed": str(request.amount),
            "judgment_date": request.judgment_date,
            "writ_instructions": [
                f"The garnishee ({institution}) shall hold all funds of "
                f"the defendant ({request.debtor_name}) upon service of this writ.",
                "The garnishee must file MC 15 (Garnishee Disclosure) within "
                "14 days of service, disclosing all property held.",
                "The defendant may file MC 16 (Objection/Claim of Exemption) "
                "within 14 days of receiving notice of garnishment.",
                "Funds shall remain frozen until further order of the court.",
            ],
            "legal_basis": [
                "MCL 600.4011 — non-periodic garnishment",
                "MCR 3.101 — garnishment after judgment",
            ],
        }

    def process_objections(
        self,
        request_id: str,
        objection_type: str = "exemption",
        objection_basis: str = "",
    ) -> Dict[str, Any]:
        """Process a debtor's objection to garnishment (MC 16)."""
        valid_bases = [
            "public_benefits",
            "pension",
            "head_of_household",
            "improper_service",
            "satisfied_judgment",
            "wrong_person",
            "excess_amount",
        ]

        objection = {
            "objection_id": uuid.uuid4().hex[:10],
            "request_id": request_id,
            "objection_type": objection_type,
            "objection_basis": objection_basis,
            "valid_basis": objection_basis in valid_bases,
            "form": "MC 16 — Objection to Garnishment",
            "response_deadline_days": 14,
            "hearing_required": objection_basis in ("improper_service", "wrong_person"),
            "legal_basis": "MCR 3.101(M); MCL 600.4012",
            "recommendations": [],
        }

        if objection_basis == "public_benefits":
            objection["recommendations"].append(
                "Request documentation of benefit source — MCL 600.4012(1)"
            )
        elif objection_basis == "pension":
            objection["recommendations"].append(
                "Verify pension/retirement status — MCL 600.4012(1)(f)"
            )
        elif objection_basis == "excess_amount":
            objection["recommendations"].append(
                "Recalculate amounts to ensure compliance with judgment total"
            )

        self._objections.append(objection)
        return objection

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "BankGarnishmentProcessor",
            "accounts_identified": len(self._accounts),
            "objections_processed": len(self._objections),
        }


# ---------------------------------------------------------------------------
# GarnishmentFormGenerator
# ---------------------------------------------------------------------------


class GarnishmentFormGenerator:
    """Generate SCAO garnishment form field data.

    Produces structured field dictionaries matching SCAO forms MC 14,
    MC 15, MC 16, and MC 50.  Does NOT produce the PDF itself — that
    is handled by the output pipeline's pdf_generator.
    """

    def __init__(self) -> None:
        self._generated_forms: List[FormOutput] = []

    def _hash_fields(self, fields: Dict[str, str]) -> str:
        raw = json.dumps(fields, sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def generate_mc14(
        self, request: GarnishmentRequest,
    ) -> FormOutput:
        """Generate MC 14 — Request and Writ of Garnishment.

        This is the initiating document filed with the court to begin
        garnishment proceedings per MCR 3.101(G).
        """
        fields = {
            "court": request.court,
            "case_number": request.case_number,
            "plaintiff": _PLAINTIFF,
            "defendant": request.debtor_name,
            "garnishee": request.garnishee_name,
            "garnishment_type": request.garnishment_type.value,
            "judgment_date": request.judgment_date,
            "judgment_amount": str(request.judgment_amount),
            "costs_and_interest": str(request.costs + request.amount - request.judgment_amount),
            "total_amount": str(request.amount),
            "filed_date": request.filed_date or date.today().isoformat(),
            "mcr_reference": "MCR 3.101(G)",
        }

        form = FormOutput(
            form_number="MC 14",
            form_name="Request and Writ of Garnishment",
            request_id=request.request_id,
            content_hash=self._hash_fields(fields),
            fields=fields,
        )
        self._generated_forms.append(form)
        return form

    def generate_mc15(
        self, request: GarnishmentRequest, disclosed_amount: Decimal = Decimal("0"),
    ) -> FormOutput:
        """Generate MC 15 — Garnishee Disclosure.

        The garnishee files this form to disclose what property or
        funds they hold belonging to the debtor.  Due within 14 days
        of service per MCR 3.101(H).
        """
        fields = {
            "court": request.court,
            "case_number": request.case_number,
            "plaintiff": _PLAINTIFF,
            "defendant": request.debtor_name,
            "garnishee": request.garnishee_name,
            "disclosed_amount": str(disclosed_amount),
            "disclosure_date": date.today().isoformat(),
            "deadline": (date.today() + timedelta(days=14)).isoformat(),
            "mcr_reference": "MCR 3.101(H)",
            "instructions": "Garnishee must disclose all property held.",
        }

        form = FormOutput(
            form_number="MC 15",
            form_name="Garnishee Disclosure",
            request_id=request.request_id,
            content_hash=self._hash_fields(fields),
            fields=fields,
        )
        self._generated_forms.append(form)
        return form

    def generate_mc16(
        self,
        request: GarnishmentRequest,
        exemption_claimed: str = "",
        exemption_basis: str = "",
    ) -> FormOutput:
        """Generate MC 16 — Objection to Garnishment / Claim of Exemption.

        Filed by the debtor to object to garnishment or claim statutory
        exemption under MCL 600.4012.
        """
        fields = {
            "court": request.court,
            "case_number": request.case_number,
            "plaintiff": _PLAINTIFF,
            "defendant": request.debtor_name,
            "garnishee": request.garnishee_name,
            "exemption_claimed": exemption_claimed,
            "exemption_basis": exemption_basis,
            "filing_date": date.today().isoformat(),
            "mcr_reference": "MCR 3.101(M)",
            "legal_basis": "MCL 600.4012",
        }

        form = FormOutput(
            form_number="MC 16",
            form_name="Objection to Garnishment / Claim of Exemption",
            request_id=request.request_id,
            content_hash=self._hash_fields(fields),
            fields=fields,
        )
        self._generated_forms.append(form)
        return form

    def generate_mc50(
        self, request: GarnishmentRequest, pay_period: str = "biweekly",
    ) -> FormOutput:
        """Generate MC 50 — Writ of Garnishment (Periodic).

        Initiates periodic wage garnishment.  Served on the employer
        to begin regular withholding per MCR 3.101(G).
        """
        fields = {
            "court": request.court,
            "case_number": request.case_number,
            "plaintiff": _PLAINTIFF,
            "defendant": request.debtor_name,
            "employer_garnishee": request.garnishee_name,
            "judgment_amount": str(request.judgment_amount),
            "total_owed": str(request.amount),
            "pay_period": pay_period,
            "filed_date": request.filed_date or date.today().isoformat(),
            "mcr_reference": "MCR 3.101(G)",
            "mcl_reference": "MCL 600.4011",
            "withholding_instructions": (
                "Withhold per 15 USC § 1673: the lesser of 25% of "
                "disposable earnings or the amount exceeding 30× $7.25/hr."
            ),
        }

        form = FormOutput(
            form_number="MC 50",
            form_name="Writ of Garnishment (Periodic)",
            request_id=request.request_id,
            content_hash=self._hash_fields(fields),
            fields=fields,
        )
        self._generated_forms.append(form)
        return form

    def get_stats(self) -> Dict[str, Any]:
        form_counts: Dict[str, int] = {}
        for f in self._generated_forms:
            form_counts[f.form_number] = form_counts.get(f.form_number, 0) + 1
        return {
            "component": "GarnishmentFormGenerator",
            "total_forms_generated": len(self._generated_forms),
            "by_form": form_counts,
        }


# ---------------------------------------------------------------------------
# GarnishmentEngine  (main orchestrator)
# ---------------------------------------------------------------------------


class GarnishmentEngine:
    """Top-level orchestrator for Michigan garnishment proceedings.

    Combines :class:`ExemptionAnalyzer`, :class:`WageGarnishmentCalculator`,
    :class:`BankGarnishmentProcessor`, and :class:`GarnishmentFormGenerator`
    into a unified garnishment management system.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or _DB_PATH
        self._exemption_analyzer = ExemptionAnalyzer()
        self._wage_calculator = WageGarnishmentCalculator()
        self._bank_processor = BankGarnishmentProcessor()
        self._form_generator = GarnishmentFormGenerator()
        self._requests: Dict[str, GarnishmentRequest] = {}

    # -- DB helpers --

    def _get_db(self) -> sqlite3.Connection:
        """Open a WAL-mode connection with safe PRAGMAs."""
        conn = sqlite3.connect(str(self._db_path), timeout=60)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("PRAGMA cache_size=-32000")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.row_factory = sqlite3.Row
        return conn

    # -- garnishment lifecycle --

    def create_garnishment(
        self,
        garnishment_type: GarnishmentType = GarnishmentType.PERIODIC,
        debtor_name: str = "",
        garnishee_name: str = "",
        amount: Decimal = Decimal("0.00"),
        case_number: str = "",
        judgment_date: str = "",
        judgment_amount: Optional[Decimal] = None,
        costs: Decimal = Decimal("0.00"),
    ) -> GarnishmentRequest:
        """Create a new garnishment request.

        Parameters
        ----------
        garnishment_type : GarnishmentType
        debtor_name : str
        garnishee_name : str — employer (periodic) or bank (non-periodic)
        amount : Decimal — total amount sought
        case_number : str
        judgment_date : str — ISO date of underlying judgment
        judgment_amount : Decimal or None
        costs : Decimal — additional costs/interest

        Returns
        -------
        GarnishmentRequest
        """
        request = GarnishmentRequest(
            garnishment_type=garnishment_type,
            debtor_name=debtor_name or _DEFENDANT,
            garnishee_name=garnishee_name,
            amount=amount,
            case_number=case_number or LANE_CASES["A"],
            court=_COURT,
            judgment_date=judgment_date,
            judgment_amount=judgment_amount if judgment_amount is not None else amount,
            costs=costs,
        )
        self._requests[request.request_id] = request
        logger.info(
            "Created %s garnishment %s — %s → %s ($%s)",
            garnishment_type.value,
            request.request_id,
            debtor_name,
            garnishee_name,
            amount,
        )
        return request

    def calculate_amounts(
        self,
        request_id: str,
        gross_income: Decimal = Decimal("0.00"),
        deductions: Decimal = Decimal("0.00"),
        pay_period: str = "biweekly",
        dependents: int = 0,
        is_head_of_household: bool = False,
    ) -> Dict[str, Any]:
        """Calculate garnishment amounts for a request."""
        request = self._requests.get(request_id)
        if not request:
            return {"error": f"Request {request_id} not found"}

        if request.garnishment_type == GarnishmentType.PERIODIC:
            withholding = self._wage_calculator.calculate_withholding(
                gross=gross_income,
                deductions=deductions,
                pay_period=pay_period,
                dependents=dependents,
                is_head_of_household=is_head_of_household,
            )
            exempt = self._exemption_analyzer.calculate_exempt_amount(
                income=gross_income - deductions,
                dependents=dependents,
                pay_period=pay_period,
                is_head_of_household=is_head_of_household,
            )
            return {
                "request_id": request_id,
                "type": "periodic",
                "gross_income": str(gross_income),
                "deductions": str(deductions),
                "disposable_income": str(gross_income - deductions),
                "exempt_amount": str(exempt),
                "withholding_per_period": str(withholding),
                "pay_period": pay_period,
                "judgment_total": str(request.amount),
                "remaining": str(request.remaining_balance),
            }
        else:
            # Non-periodic — bank garnishment
            balance_result = self._bank_processor.calculate_exempt_balance(
                account_balance=gross_income,  # treat as account balance
            )
            return {
                "request_id": request_id,
                "type": "non_periodic",
                "account_balance": str(gross_income),
                **balance_result,
                "judgment_total": str(request.amount),
            }

    def track_compliance(
        self, request_id: str,
    ) -> Dict[str, Any]:
        """Track garnishment compliance status."""
        request = self._requests.get(request_id)
        if not request:
            return {"error": f"Request {request_id} not found"}

        balance = self._wage_calculator.calculate_remaining_balance(request)

        compliance: Dict[str, Any] = {
            "request_id": request_id,
            "status": request.status.value,
            "garnishment_type": request.garnishment_type.value,
            "balance": balance,
            "issues": [],
            "next_steps": [],
        }

        if request.status == GarnishmentStatus.SERVED:
            compliance["next_steps"].append(
                "Await MC 15 (Garnishee Disclosure) — due 14 days from service"
            )
        elif request.status == GarnishmentStatus.ACTIVE:
            if balance.get("is_satisfied"):
                compliance["next_steps"].append(
                    "File satisfaction of judgment — garnishment complete"
                )
                compliance["issues"].append("Judgment satisfied — terminate garnishment")
            else:
                compliance["next_steps"].append(
                    f"Continue monitoring payments — ${balance.get('remaining_balance', '0')} remaining"
                )
        elif request.status == GarnishmentStatus.OBJECTED:
            compliance["next_steps"].append(
                "Respond to MC 16 objection within 7 days"
            )
            compliance["next_steps"].append(
                "Request hearing if exemption claim is disputed"
            )

        return compliance

    def generate_forms(
        self, request_id: str, forms: Optional[List[str]] = None,
    ) -> List[FormOutput]:
        """Generate SCAO forms for a garnishment request.

        Parameters
        ----------
        request_id : str
        forms : list of form codes (MC14, MC15, MC16, MC50) or None for all

        Returns
        -------
        list of FormOutput
        """
        request = self._requests.get(request_id)
        if not request:
            logger.warning("Request %s not found for form generation", request_id)
            return []

        target_forms = forms or ["MC14"]
        if request.garnishment_type == GarnishmentType.PERIODIC and not forms:
            target_forms = ["MC14", "MC50"]

        generated: List[FormOutput] = []
        for code in target_forms:
            code_upper = code.upper().replace(" ", "")
            if code_upper == "MC14":
                generated.append(self._form_generator.generate_mc14(request))
            elif code_upper == "MC15":
                generated.append(self._form_generator.generate_mc15(request))
            elif code_upper == "MC16":
                generated.append(self._form_generator.generate_mc16(request))
            elif code_upper == "MC50":
                generated.append(self._form_generator.generate_mc50(request))
            else:
                logger.warning("Unknown form code: %s", code)

        return generated

    def get_request(self, request_id: str) -> Optional[GarnishmentRequest]:
        """Retrieve a garnishment request by ID."""
        return self._requests.get(request_id)

    def list_requests(
        self, status: Optional[GarnishmentStatus] = None,
    ) -> List[GarnishmentRequest]:
        """List all requests, optionally filtered by status."""
        if status:
            return [r for r in self._requests.values() if r.status == status]
        return list(self._requests.values())

    def update_status(
        self, request_id: str, new_status: GarnishmentStatus,
    ) -> Optional[GarnishmentRequest]:
        """Update the status of a garnishment request."""
        request = self._requests.get(request_id)
        if request:
            old_status = request.status
            request.status = new_status
            logger.info(
                "Garnishment %s: %s → %s",
                request_id, old_status.value, new_status.value,
            )
        return request

    def get_stats(self) -> Dict[str, Any]:
        """Return runtime statistics."""
        by_type: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        for r in self._requests.values():
            by_type[r.garnishment_type.value] = by_type.get(r.garnishment_type.value, 0) + 1
            by_status[r.status.value] = by_status.get(r.status.value, 0) + 1

        return {
            "module": "garnishment_engine",
            "total_requests": len(self._requests),
            "by_type": by_type,
            "by_status": by_status,
            "db_path": str(self._db_path),
            "exemption_analyzer": self._exemption_analyzer.get_stats(),
            "wage_calculator": self._wage_calculator.get_stats(),
            "bank_processor": self._bank_processor.get_stats(),
            "form_generator": self._form_generator.get_stats(),
        }

    def reset(self) -> None:
        """Clear all loaded requests."""
        self._requests.clear()


# ---------------------------------------------------------------------------
# CLI demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sys.stdout = open(  # noqa: SIM115
        sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace"
    )
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print("=" * 60)
    print("  Garnishment Engine — LitigationOS")
    print("=" * 60)
    print()

    engine = GarnishmentEngine()

    # Create a periodic garnishment
    req = engine.create_garnishment(
        garnishment_type=GarnishmentType.PERIODIC,
        debtor_name=_DEFENDANT,
        garnishee_name="Acme Employer LLC",
        amount=Decimal("5000.00"),
        case_number=LANE_CASES["A"],
        judgment_date="2025-06-15",
    )
    print(f"Created: {req.request_id}")
    print(f"  Type: {req.garnishment_type.value}")
    print(f"  Amount: ${req.amount}")
    print()

    # Calculate withholding
    calc = engine.calculate_amounts(
        request_id=req.request_id,
        gross_income=Decimal("2000.00"),
        deductions=Decimal("400.00"),
        pay_period="biweekly",
        dependents=1,
    )
    print("Withholding Calculation:")
    for k, v in calc.items():
        print(f"  {k}: {v}")
    print()

    # Generate forms
    forms = engine.generate_forms(req.request_id)
    print(f"Generated {len(forms)} form(s):")
    for f in forms:
        print(f"  {f.form_number} — {f.form_name}")
    print()

    # Exemption analysis
    analyzer = ExemptionAnalyzer()
    protected = analyzer.identify_protected_assets()
    print(f"Protected assets ({len(protected)}):")
    for asset in protected:
        print(f"  • {asset['asset']} — {asset['exemption']}")
    print()

    # Stats
    stats = engine.get_stats()
    print("Stats:")
    for k, v in stats.items():
        print(f"  {k}: {v}")
