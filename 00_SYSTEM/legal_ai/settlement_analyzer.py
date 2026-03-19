"""LitigationOS Settlement Analyzer v1.0
========================================
Settlement valuation, negotiation strategy, demand-letter generation,
and mediation preparation for Michigan family-law litigation.

Covers MCR 3.216 (mediation), MCR 2.403 (case evaluation), MCR 2.405
(costs after rejected offers), MCL 552.13 (child support), MCL 37.2801
(housing treble damages), and 42 U.S.C. § 1983 (federal civil rights).

Case: Pigors v. Watson (19 defendants, 8 jurisdictions)
Plaintiff: Andrew James Pigors (Pro Se)
Defendant: Emily A. Watson
Child: Lincoln David Watson (L.D.W.) — MALE
Judge: Hon. Jenny L. McNeill

100 % local · zero-API · stdlib-only · Python 3.12+
"""
from __future__ import annotations

import json
import logging
import math
import pathlib
import sqlite3
import sys
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_REPO = pathlib.Path(__file__).resolve().parent.parent.parent
_DB_PATH = _REPO / "litigation_context.db"

# ---------------------------------------------------------------------------
# Party constants
# ---------------------------------------------------------------------------
PLAINTIFF = "Andrew James Pigors"
PLAINTIFF_ROLE = "Pro Se Litigant"
DEFENDANT = "Emily A. Watson"
CHILD = "Lincoln David Watson"
CHILD_INITIALS = "L.D.W."
JUDGE = "Hon. Jenny L. McNeill"

CASE_LANES: Dict[str, Dict[str, str]] = {
    "A": {"subject": "Custody", "case_number": "2024-001507-DC"},
    "B": {"subject": "Housing", "case_number": "2025-002760-CZ"},
    "C": {"subject": "Convergence", "case_number": "Multi-lane"},
    "D": {"subject": "PPO", "case_number": "2023-5907-PP"},
    "E": {"subject": "Misconduct/JTC", "case_number": "Judge McNeill"},
    "F": {"subject": "Appellate", "case_number": "COA 366810"},
}

# ---------------------------------------------------------------------------
# Defendant registry (19 defendants)
# ---------------------------------------------------------------------------
DEFENDANTS: List[Dict[str, str]] = [
    {"name": "Emily A. Watson", "role": "Primary Defendant / Mother", "lane": "A,D"},
    {"name": "Hon. Jenny L. McNeill", "role": "Presiding Judge — §1983", "lane": "E"},
    {"name": "Pamela Rusco", "role": "Mediator", "lane": "A"},
    {"name": "Muskegon County FOC", "role": "Friend of the Court", "lane": "A"},
    {"name": "FOC Officer Doe", "role": "FOC Investigator", "lane": "A"},
    {"name": "FOC Officer Smith", "role": "FOC Caseworker", "lane": "A"},
    {"name": "Shady Oaks HOA", "role": "Housing Association", "lane": "B"},
    {"name": "HOA Board Member 1", "role": "Board Officer", "lane": "B"},
    {"name": "HOA Board Member 2", "role": "Board Officer", "lane": "B"},
    {"name": "HOA Property Manager", "role": "Property Management", "lane": "B"},
    {"name": "DHHS Caseworker", "role": "CPS/DHHS", "lane": "A,D"},
    {"name": "Police Officer Alpha", "role": "Law Enforcement", "lane": "D"},
    {"name": "Police Officer Beta", "role": "Law Enforcement", "lane": "D"},
    {"name": "Guardian ad Litem", "role": "Child Advocate", "lane": "A"},
    {"name": "Custody Evaluator", "role": "Evaluator", "lane": "A"},
    {"name": "Opposing Counsel (Watson)", "role": "Attorney for Defendant", "lane": "A,D"},
    {"name": "HOA Attorney", "role": "Attorney for HOA", "lane": "B"},
    {"name": "County Prosecutor", "role": "Prosecutor Office", "lane": "D"},
    {"name": "Court Administrator", "role": "Court Staff", "lane": "E"},
]

# ---------------------------------------------------------------------------
# DB
# ---------------------------------------------------------------------------
_PRAGMAS = """\
PRAGMA busy_timeout = 60000;
PRAGMA journal_mode = WAL;
PRAGMA cache_size  = -32000;
PRAGMA synchronous = NORMAL;
PRAGMA temp_store  = MEMORY;
"""

_SCHEMA = """\
CREATE TABLE IF NOT EXISTS settlement_analysis (
    analysis_id       TEXT PRIMARY KEY,
    lane              TEXT NOT NULL,
    defendant_name    TEXT NOT NULL DEFAULT '',
    claim_type        TEXT NOT NULL DEFAULT '',
    win_probability   INTEGER NOT NULL DEFAULT 50,
    damages_low       TEXT NOT NULL DEFAULT '0',
    damages_mid       TEXT NOT NULL DEFAULT '0',
    damages_high      TEXT NOT NULL DEFAULT '0',
    expected_value    TEXT NOT NULL DEFAULT '0',
    settlement_floor  TEXT NOT NULL DEFAULT '0',
    settlement_target TEXT NOT NULL DEFAULT '0',
    settlement_ceiling TEXT NOT NULL DEFAULT '0',
    walkaway          TEXT NOT NULL DEFAULT '0',
    risk_factors      TEXT NOT NULL DEFAULT '[]',
    key_factors       TEXT NOT NULL DEFAULT '[]',
    strategy          TEXT NOT NULL DEFAULT 'MODERATE',
    rationale         TEXT NOT NULL DEFAULT '',
    created_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS demand_letters (
    letter_id     TEXT PRIMARY KEY,
    defendant_name TEXT NOT NULL,
    lane          TEXT NOT NULL DEFAULT '',
    amount        TEXT NOT NULL DEFAULT '0',
    deadline_date TEXT NOT NULL DEFAULT '',
    letter_text   TEXT NOT NULL DEFAULT '',
    status        TEXT NOT NULL DEFAULT 'DRAFT',
    sent_date     TEXT,
    response_date TEXT,
    response_type TEXT NOT NULL DEFAULT '',
    created_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE INDEX IF NOT EXISTS idx_settlement_lane
    ON settlement_analysis(lane);
CREATE INDEX IF NOT EXISTS idx_settlement_defendant
    ON settlement_analysis(defendant_name);
CREATE INDEX IF NOT EXISTS idx_demand_defendant
    ON demand_letters(defendant_name);
CREATE INDEX IF NOT EXISTS idx_demand_lane
    ON demand_letters(lane);
"""


# ═══════════════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════════════

class SettlementStrategy(Enum):
    """Negotiation posture."""
    AGGRESSIVE = "AGGRESSIVE"
    MODERATE = "MODERATE"
    CONSERVATIVE = "CONSERVATIVE"
    WALKAWAY = "WALKAWAY"


class RiskLevel(Enum):
    """Severity of a litigation risk factor."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class OfferVerdict(Enum):
    """Recommendation after evaluating a settlement offer."""
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    COUNTER = "COUNTER"
    DEFER = "DEFER"


# ═══════════════════════════════════════════════════════════════════════════
# Dataclasses
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class CaseOutcomeProbability:
    """Probability-weighted outcome model for a single claim."""

    lane: str = ""
    claim_type: str = ""
    win_probability: int = 50
    damages_if_win_low: Decimal = Decimal("0")
    damages_if_win_mid: Decimal = Decimal("0")
    damages_if_win_high: Decimal = Decimal("0")
    expected_value: Decimal = Decimal("0")
    confidence: int = 50
    key_factors: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "lane": self.lane,
            "claim_type": self.claim_type,
            "win_probability": self.win_probability,
            "damages_if_win_low": str(self.damages_if_win_low),
            "damages_if_win_mid": str(self.damages_if_win_mid),
            "damages_if_win_high": str(self.damages_if_win_high),
            "expected_value": str(self.expected_value),
            "confidence": self.confidence,
            "key_factors": list(self.key_factors),
            "risks": list(self.risks),
        }

    # ------------------------------------------------------------------
    def calculate_expected_value(self) -> Decimal:
        """Probability × midpoint damages.  Updates *expected_value* in-place."""
        prob = Decimal(str(self.win_probability)) / Decimal("100")
        self.expected_value = (
            prob * self.damages_if_win_mid
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return self.expected_value


@dataclass
class SettlementRange:
    """Acceptable settlement window for a given defendant/lane."""

    lane: str = ""
    defendant_name: str = ""
    floor: Decimal = Decimal("0")
    target: Decimal = Decimal("0")
    ceiling: Decimal = Decimal("0")
    walkaway: Decimal = Decimal("0")
    rationale: str = ""

    def to_dict(self) -> dict:
        return {
            "lane": self.lane,
            "defendant_name": self.defendant_name,
            "floor": str(self.floor),
            "target": str(self.target),
            "ceiling": str(self.ceiling),
            "walkaway": str(self.walkaway),
            "rationale": self.rationale,
        }


@dataclass
class DamageItem:
    """Single line item in a damages schedule."""

    category: str = ""
    description: str = ""
    amount: Decimal = Decimal("0")
    multiplier: Decimal = Decimal("1")
    authority: str = ""

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "description": self.description,
            "amount": str(self.amount),
            "multiplier": str(self.multiplier),
            "total": str(self.amount * self.multiplier),
            "authority": self.authority,
        }


@dataclass
class NegotiationIssue:
    """Single issue in a mediation/negotiation matrix."""

    issue: str = ""
    our_position: str = ""
    their_likely_position: str = ""
    priority: int = 5
    tradeoff_value: str = ""
    zone_of_agreement: str = ""

    def to_dict(self) -> dict:
        return {
            "issue": self.issue,
            "our_position": self.our_position,
            "their_likely_position": self.their_likely_position,
            "priority": self.priority,
            "tradeoff_value": self.tradeoff_value,
            "zone_of_agreement": self.zone_of_agreement,
        }


# ═══════════════════════════════════════════════════════════════════════════
# Database helpers
# ═══════════════════════════════════════════════════════════════════════════

def _get_conn(db_path: Optional[pathlib.Path] = None) -> sqlite3.Connection:
    p = db_path or _DB_PATH
    conn = sqlite3.connect(str(p), timeout=120)
    conn.executescript(_PRAGMAS)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(_SCHEMA)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today_iso() -> str:
    return date.today().isoformat()


def _dec(val: Any) -> Decimal:
    """Coerce to Decimal, handling strings, ints, floats."""
    if isinstance(val, Decimal):
        return val
    try:
        return Decimal(str(val))
    except Exception:
        return Decimal("0")


# ═══════════════════════════════════════════════════════════════════════════
# ExpectedValueCalculator
# ═══════════════════════════════════════════════════════════════════════════

class ExpectedValueCalculator:
    """Probability-weighted case valuation engine.

    All monetary calculations use ``Decimal`` for precision.
    """

    # ------------------------------------------------------------------
    # Baseline claim templates (lane → claim → params)
    # ------------------------------------------------------------------
    _CLAIM_TEMPLATES: Dict[str, Dict[str, Dict[str, Any]]] = {
        "A": {
            "custody_interference": {
                "win_prob": 65, "low": 5000, "mid": 25000, "high": 75000,
                "factors": [
                    "Documented denial of parenting time",
                    "Pattern of ex parte manipulation",
                ],
                "risks": ["Judicial bias toward status quo", "He-said/she-said dynamics"],
            },
            "child_support_modification": {
                "win_prob": 55, "low": 2000, "mid": 10000, "high": 30000,
                "factors": ["Income disparity evidence", "Child needs documentation"],
                "risks": ["FOC recommendation weight", "Income verification gaps"],
            },
            "parental_alienation": {
                "win_prob": 40, "low": 10000, "mid": 50000, "high": 150000,
                "factors": ["L.D.W. behavioral changes", "Expert testimony potential"],
                "risks": ["High burden of proof", "Court skepticism of alienation claims"],
            },
        },
        "B": {
            "fair_housing_violation": {
                "win_prob": 60, "low": 15000, "mid": 50000, "high": 150000,
                "factors": [
                    "Documented discriminatory conduct",
                    "MCL 37.2801 treble damages available",
                ],
                "risks": ["HOA claims business judgment rule", "Statute of limitations"],
            },
            "breach_of_fiduciary_duty": {
                "win_prob": 50, "low": 5000, "mid": 20000, "high": 60000,
                "factors": ["Board meeting records", "Financial mismanagement"],
                "risks": ["Business judgment rule defense", "Standing questions"],
            },
        },
        "D": {
            "wrongful_ppo": {
                "win_prob": 55, "low": 5000, "mid": 20000, "high": 50000,
                "factors": ["Lack of statutory basis", "Retaliatory timing"],
                "risks": ["Judicial deference to PPO issuance", "Safety concerns override"],
            },
        },
        "E": {
            "judicial_misconduct_1983": {
                "win_prob": 25, "low": 25000, "mid": 100000, "high": 500000,
                "factors": [
                    "Pattern of ex parte communications",
                    "Due process violations documented",
                ],
                "risks": [
                    "Judicial immunity (absolute in most acts)",
                    "Qualified immunity analysis required",
                    "High bar for §1983 against judge",
                ],
            },
        },
        "F": {
            "appellate_reversal": {
                "win_prob": 35, "low": 0, "mid": 0, "high": 0,
                "factors": ["Clear legal error on record", "Preserved objections"],
                "risks": ["Abuse of discretion standard", "Harmless error doctrine"],
            },
        },
    }

    # ------------------------------------------------------------------
    def calculate_case_value(
        self,
        lane: str,
        claims: Optional[List[str]] = None,
    ) -> List[CaseOutcomeProbability]:
        """Compute expected values for each claim in a lane.

        If *claims* is ``None``, all known claims for the lane are used.
        """
        templates = self._CLAIM_TEMPLATES.get(lane.upper(), {})
        if claims:
            templates = {k: v for k, v in templates.items() if k in claims}

        results: List[CaseOutcomeProbability] = []
        for claim, params in templates.items():
            cop = CaseOutcomeProbability(
                lane=lane,
                claim_type=claim,
                win_probability=params["win_prob"],
                damages_if_win_low=Decimal(str(params["low"])),
                damages_if_win_mid=Decimal(str(params["mid"])),
                damages_if_win_high=Decimal(str(params["high"])),
                confidence=60,
                key_factors=list(params.get("factors", [])),
                risks=list(params.get("risks", [])),
            )
            cop.calculate_expected_value()
            results.append(cop)
        return results

    # ------------------------------------------------------------------
    def discount_for_risk(
        self,
        value: Decimal,
        risk_factors: List[str],
    ) -> Decimal:
        """Apply a cumulative risk discount to an expected value.

        Each risk factor reduces the value by a fixed percentage.
        """
        discount_per_factor = Decimal("0.05")
        total_discount = min(
            discount_per_factor * Decimal(str(len(risk_factors))),
            Decimal("0.50"),
        )
        return (value * (Decimal("1") - total_discount)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP,
        )

    # ------------------------------------------------------------------
    def calculate_litigation_costs(
        self,
        remaining_steps: List[str],
    ) -> Decimal:
        """Estimate remaining litigation costs based on pending steps.

        Costs are pro-se estimates (filing fees, copies, mileage).
        """
        step_costs: Dict[str, Decimal] = {
            "discovery": Decimal("500.00"),
            "depositions": Decimal("1500.00"),
            "mediation": Decimal("750.00"),
            "trial_prep": Decimal("1000.00"),
            "trial": Decimal("2000.00"),
            "post_trial_motions": Decimal("300.00"),
            "appeal_filing": Decimal("375.00"),
            "appeal_brief": Decimal("500.00"),
            "appeal_oral_argument": Decimal("250.00"),
            "expert_witness": Decimal("3000.00"),
            "service_of_process": Decimal("200.00"),
            "copies_and_postage": Decimal("150.00"),
        }
        total = Decimal("0")
        for step in remaining_steps:
            key = step.lower().replace(" ", "_").replace("-", "_")
            total += step_costs.get(key, Decimal("250.00"))
        return total

    # ------------------------------------------------------------------
    def net_expected_value(
        self,
        case_value: Decimal,
        litigation_costs: Decimal,
    ) -> Decimal:
        """Expected value minus remaining litigation costs."""
        return (case_value - litigation_costs).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP,
        )

    # ------------------------------------------------------------------
    def compare_settlement_to_trial(
        self,
        offer: Decimal,
        expected_value: Decimal,
        risk_tolerance: str = "MODERATE",
    ) -> Dict[str, Any]:
        """Recommend whether to accept, reject, or counter an offer.

        Parameters
        ----------
        risk_tolerance : str
            AGGRESSIVE, MODERATE, CONSERVATIVE.

        Returns
        -------
        dict
            verdict, reasoning, counter_suggestion (if COUNTER).
        """
        multiplier_map = {
            "AGGRESSIVE": Decimal("1.20"),
            "MODERATE": Decimal("0.90"),
            "CONSERVATIVE": Decimal("0.70"),
        }
        threshold = expected_value * multiplier_map.get(
            risk_tolerance.upper(), Decimal("0.90"),
        )

        if offer >= expected_value:
            verdict = OfferVerdict.ACCEPT
            reasoning = (
                f"Offer (${offer}) meets or exceeds expected trial value "
                f"(${expected_value}). Accepting eliminates litigation risk."
            )
            counter = None
        elif offer >= threshold:
            verdict = OfferVerdict.COUNTER
            midpoint = ((offer + expected_value) / Decimal("2")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP,
            )
            reasoning = (
                f"Offer (${offer}) is within negotiable range but below "
                f"expected value (${expected_value}). Counter at ${midpoint}."
            )
            counter = midpoint
        else:
            verdict = OfferVerdict.REJECT
            reasoning = (
                f"Offer (${offer}) is significantly below expected value "
                f"(${expected_value}) and threshold (${threshold}). Reject."
            )
            counter = expected_value

        return {
            "verdict": verdict.value,
            "offer": str(offer),
            "expected_value": str(expected_value),
            "threshold": str(threshold),
            "reasoning": reasoning,
            "counter_suggestion": str(counter) if counter else None,
        }

    # ------------------------------------------------------------------
    def get_stats(self) -> dict:
        return {
            "claim_template_lanes": list(self._CLAIM_TEMPLATES.keys()),
            "total_claim_templates": sum(
                len(v) for v in self._CLAIM_TEMPLATES.values()
            ),
        }


# ═══════════════════════════════════════════════════════════════════════════
# DemandLetterGenerator
# ═══════════════════════════════════════════════════════════════════════════

class DemandLetterGenerator:
    """Generate formal demand letters with itemised damages and citations."""

    def __init__(self, conn: Optional[sqlite3.Connection] = None) -> None:
        self._conn = conn
        self._letters_count: int = 0

    def _db(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = _get_conn()
            _ensure_schema(self._conn)
        return self._conn

    # ------------------------------------------------------------------
    def generate_demand(
        self,
        defendant: str,
        lane: str,
        amount: Decimal,
        deadline_days: int = 30,
        *,
        damage_items: Optional[List[DamageItem]] = None,
        claims: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generate a formal demand letter for one defendant.

        Returns a dict containing the letter_id, text, and metadata.
        """
        deadline = (date.today() + timedelta(days=deadline_days)).isoformat()
        letter_id = str(uuid.uuid4())
        lane_info = CASE_LANES.get(lane.upper(), {})
        case_number = lane_info.get("case_number", "")

        lines: List[str] = []
        lines.append(f"Date: {_today_iso()}")
        lines.append("")
        lines.append("VIA CERTIFIED MAIL — RETURN RECEIPT REQUESTED")
        lines.append("")
        lines.append(f"To: {defendant}")
        lines.append("")
        lines.append(f"Re: Pigors v. Watson, et al.")
        lines.append(f"    Case No.: {case_number}")
        lines.append(f"    Lane: {lane.upper()} — {lane_info.get('subject', '')}")
        lines.append("")
        lines.append("DEMAND FOR SETTLEMENT")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"Dear {defendant},")
        lines.append("")
        lines.append(
            f"This letter constitutes a formal demand on behalf of "
            f"{PLAINTIFF} for the total sum of ${amount} arising from "
            f"your actions and/or omissions in connection with the "
            f"above-referenced matter."
        )
        lines.append("")

        if damage_items:
            lines.append("ITEMISED DAMAGES:")
            lines.append("-" * 40)
            running = Decimal("0")
            for item in damage_items:
                total = item.amount * item.multiplier
                running += total
                lines.append(
                    f"  {item.category}: {item.description}"
                )
                lines.append(
                    f"    Amount: ${item.amount} × {item.multiplier} = ${total}"
                )
                if item.authority:
                    lines.append(f"    Authority: {item.authority}")
            lines.append("-" * 40)
            lines.append(f"  SUBTOTAL: ${running}")
            lines.append("")

        lines.append(self._include_authority_citations(lane, claims))
        lines.append("")
        lines.append(
            f"You have until {deadline} ({deadline_days} days) to respond "
            f"to this demand. Failure to respond will result in the "
            f"commencement or continuation of litigation seeking the full "
            f"amount of damages plus costs and fees."
        )
        lines.append("")
        lines.append(
            "Under MCR 2.405, if you reject this demand and the eventual "
            "judgment exceeds this offer, you may be liable for actual costs "
            "incurred from the date of rejection."
        )
        lines.append("")
        lines.append("This demand is made without prejudice to any claim for")
        lines.append("additional damages that may be discovered.")
        lines.append("")
        lines.append(f"Sincerely,")
        lines.append(f"{PLAINTIFF}")
        lines.append(f"{PLAINTIFF_ROLE}")
        lines.append(f"Phone: [PHONE]")
        lines.append(f"Email: [EMAIL]")

        text = "\n".join(lines)

        db = self._db()
        db.execute(
            "INSERT INTO demand_letters "
            "(letter_id, defendant_name, lane, amount, deadline_date, letter_text, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (letter_id, defendant, lane, str(amount), deadline, text, "DRAFT"),
        )
        db.commit()
        self._letters_count += 1

        return {
            "letter_id": letter_id,
            "defendant": defendant,
            "lane": lane,
            "amount": str(amount),
            "deadline": deadline,
            "text": text,
            "status": "DRAFT",
        }

    # ------------------------------------------------------------------
    def generate_global_demand(
        self,
        defendants_amounts: List[Tuple[str, str, Decimal]],
        total_amount: Decimal,
        deadline_days: int = 30,
    ) -> Dict[str, Any]:
        """Generate a combined multi-defendant demand letter.

        Parameters
        ----------
        defendants_amounts : list of (name, lane, amount)
        total_amount : Decimal
            Grand total across all defendants.
        """
        deadline = (date.today() + timedelta(days=deadline_days)).isoformat()
        lines: List[str] = []
        lines.append(f"Date: {_today_iso()}")
        lines.append("")
        lines.append("VIA CERTIFIED MAIL — RETURN RECEIPT REQUESTED")
        lines.append("")
        lines.append("To: All Named Defendants (see schedule below)")
        lines.append("")
        lines.append(f"Re: Pigors v. Watson, et al.")
        lines.append("    Multi-Lane Global Settlement Demand")
        lines.append("")
        lines.append("GLOBAL DEMAND FOR SETTLEMENT")
        lines.append("=" * 60)
        lines.append("")
        lines.append(
            f"This letter constitutes a formal demand by {PLAINTIFF} "
            f"for a global settlement in the amount of ${total_amount}, "
            f"allocated among defendants as follows:"
        )
        lines.append("")
        lines.append("DEFENDANT ALLOCATION SCHEDULE:")
        lines.append("-" * 60)
        for name, lane, amt in defendants_amounts:
            lane_info = CASE_LANES.get(lane.upper(), {})
            lines.append(
                f"  {name:<35} Lane {lane} | ${amt}"
            )
        lines.append("-" * 60)
        lines.append(f"  {'TOTAL':<35}         | ${total_amount}")
        lines.append("")
        lines.append(
            f"Response deadline: {deadline} ({deadline_days} days)."
        )
        lines.append("")
        lines.append(
            "Failure to respond may result in the filing of additional "
            "motions, sanctions requests, and full prosecution of all claims."
        )
        lines.append("")
        lines.append(f"Sincerely,")
        lines.append(f"{PLAINTIFF}")
        lines.append(f"{PLAINTIFF_ROLE}")

        text = "\n".join(lines)
        letter_id = str(uuid.uuid4())

        db = self._db()
        db.execute(
            "INSERT INTO demand_letters "
            "(letter_id, defendant_name, lane, amount, deadline_date, letter_text, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (letter_id, "ALL DEFENDANTS", "C", str(total_amount),
             deadline, text, "DRAFT"),
        )
        db.commit()
        self._letters_count += 1

        return {
            "letter_id": letter_id,
            "total_amount": str(total_amount),
            "defendant_count": len(defendants_amounts),
            "deadline": deadline,
            "text": text,
        }

    # ------------------------------------------------------------------
    def format_damages_summary(
        self, damage_items: List[DamageItem],
    ) -> str:
        """Return a formatted damages summary table."""
        lines: List[str] = []
        lines.append("ITEMISED DAMAGES SUMMARY")
        lines.append("=" * 60)
        total = Decimal("0")
        for item in damage_items:
            line_total = item.amount * item.multiplier
            total += line_total
            lines.append(
                f"  {item.category:<25} ${line_total:>12}"
            )
            if item.description:
                lines.append(f"    {item.description}")
            if item.authority:
                lines.append(f"    Authority: {item.authority}")
        lines.append("-" * 60)
        lines.append(f"  {'TOTAL':<25} ${total:>12}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    def _include_authority_citations(
        self,
        lane: str,
        claims: Optional[List[str]] = None,
    ) -> str:
        """Generate legal-basis paragraphs for the demand."""
        lane_upper = lane.upper()
        paras: List[str] = []
        paras.append("LEGAL BASIS:")

        if lane_upper == "A":
            paras.append(
                "  — MCL 722.23: Best interest of the child factors."
            )
            paras.append(
                "  — MCL 722.27: Modification of custody orders."
            )
            paras.append(
                "  — MCL 552.13: Child support obligations."
            )
        elif lane_upper == "B":
            paras.append(
                "  — MCL 37.2501 et seq.: Elliott-Larsen Civil Rights Act."
            )
            paras.append(
                "  — MCL 37.2801: Treble damages for housing discrimination."
            )
            paras.append(
                "  — MCL 559.206: Condominium Act duties."
            )
        elif lane_upper == "D":
            paras.append(
                "  — MCL 600.2950: Personal Protection Orders."
            )
            paras.append(
                "  — MCR 3.706: PPO proceedings."
            )
        elif lane_upper == "E":
            paras.append(
                "  — 42 U.S.C. § 1983: Deprivation of rights under color of law."
            )
            paras.append(
                "  — 42 U.S.C. § 1988: Attorney/litigation costs in civil rights cases."
            )
            paras.append(
                "  — Stump v. Sparkman, 435 U.S. 349 (1978): Judicial immunity limits."
            )
        elif lane_upper == "F":
            paras.append(
                "  — MCR 7.205: Application for leave to appeal."
            )
            paras.append(
                "  — MCR 7.212: Briefs in the Court of Appeals."
            )

        if claims:
            paras.append("")
            paras.append("  Additional claims asserted:")
            for c in claims:
                paras.append(f"    • {c}")

        return "\n".join(paras)

    # ------------------------------------------------------------------
    def set_deadline(
        self, letter_id: str, days: int,
    ) -> str:
        """Update the compliance deadline on an existing demand letter."""
        deadline = (date.today() + timedelta(days=days)).isoformat()
        db = self._db()
        db.execute(
            "UPDATE demand_letters SET deadline_date = ? WHERE letter_id = ?",
            (deadline, letter_id),
        )
        db.commit()
        return deadline

    # ------------------------------------------------------------------
    def get_stats(self) -> dict:
        return {"letters_generated": self._letters_count}


# ═══════════════════════════════════════════════════════════════════════════
# MediationBriefWriter
# ═══════════════════════════════════════════════════════════════════════════

class MediationBriefWriter:
    """Prepare mediation briefs and negotiation materials per MCR 3.216."""

    # ------------------------------------------------------------------
    def generate_mediation_brief(
        self,
        lane: str,
        issues: List[str],
        positions: Dict[str, str],
    ) -> str:
        """Generate a mediation brief for MCR 3.216 facilitative mediation.

        Parameters
        ----------
        issues : list[str]
            Key issues to address.
        positions : dict
            Mapping of issue → plaintiff's position.
        """
        lane_info = CASE_LANES.get(lane.upper(), {})
        lines: List[str] = []
        lines.append("CONFIDENTIAL MEDIATION BRIEF")
        lines.append("(MCR 3.216 — Facilitative Mediation)")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"Case: Pigors v. Watson, et al.")
        lines.append(f"Case No.: {lane_info.get('case_number', '')}")
        lines.append(f"Lane: {lane.upper()} — {lane_info.get('subject', '')}")
        lines.append(f"Date: {_today_iso()}")
        lines.append(f"Prepared by: {PLAINTIFF} ({PLAINTIFF_ROLE})")
        lines.append("")

        lines.append("I. CASE SUMMARY")
        lines.append("-" * 40)
        lines.append(
            f"This is a {lane_info.get('subject', 'family law').lower()} "
            f"matter involving {PLAINTIFF} (father) and {DEFENDANT} (mother) "
            f"regarding their minor child, {CHILD_INITIALS}."
        )
        lines.append("")

        lines.append("II. KEY ISSUES")
        lines.append("-" * 40)
        for i, issue in enumerate(issues, 1):
            lines.append(f"  {i}. {issue}")
            pos = positions.get(issue, "")
            if pos:
                lines.append(f"     Plaintiff's Position: {pos}")
        lines.append("")

        lines.append("III. DESIRED OUTCOMES")
        lines.append("-" * 40)
        lines.append(
            "  Plaintiff seeks a resolution that prioritises the best "
            "interests of L.D.W. and provides meaningful, enforceable "
            "parenting time and decision-making authority."
        )
        lines.append("")

        lines.append("IV. SETTLEMENT AUTHORITY")
        lines.append("-" * 40)
        lines.append(
            "  Plaintiff has authority to negotiate in good faith on all "
            "issues identified above. Specific monetary authority is "
            "reserved and will be discussed in session."
        )
        lines.append("")

        lines.append("V. BARRIERS TO SETTLEMENT")
        lines.append("-" * 40)
        lines.append("  1. History of broken agreements by opposing party.")
        lines.append("  2. Ongoing ex parte communications with the court.")
        lines.append("  3. Trust deficit requiring enforceable provisions.")
        lines.append("")

        lines.append(f"Respectfully submitted,")
        lines.append(f"{PLAINTIFF}")
        lines.append(f"{PLAINTIFF_ROLE}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    def prepare_opening_statement(
        self, key_points: List[str],
    ) -> str:
        """Draft a mediation opening statement."""
        lines: List[str] = []
        lines.append("MEDIATION OPENING STATEMENT — Plaintiff")
        lines.append("=" * 60)
        lines.append("")
        lines.append(
            f"My name is {PLAINTIFF}. I am here to resolve this matter in "
            f"the best interest of my son, {CHILD_INITIALS}."
        )
        lines.append("")
        lines.append("KEY POINTS:")
        for i, pt in enumerate(key_points, 1):
            lines.append(f"  {i}. {pt}")
        lines.append("")
        lines.append(
            "I am prepared to negotiate in good faith and am open to "
            "creative solutions that serve L.D.W.'s best interests."
        )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    def build_issue_matrix(
        self,
        issues: List[NegotiationIssue],
    ) -> str:
        """Build a negotiation-prep issue matrix."""
        lines: List[str] = []
        lines.append("NEGOTIATION ISSUE MATRIX")
        lines.append("=" * 72)
        lines.append(
            f"{'Issue':<20} {'Priority':>8} {'Our Position':<22} "
            f"{'Their Position':<22}"
        )
        lines.append("-" * 72)
        sorted_issues = sorted(issues, key=lambda x: x.priority, reverse=True)
        for iss in sorted_issues:
            lines.append(
                f"{iss.issue[:20]:<20} {iss.priority:>8} "
                f"{iss.our_position[:22]:<22} "
                f"{iss.their_likely_position[:22]:<22}"
            )
            if iss.zone_of_agreement:
                lines.append(f"  → Zone of agreement: {iss.zone_of_agreement}")
            if iss.tradeoff_value:
                lines.append(f"  → Tradeoff value:    {iss.tradeoff_value}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    def calculate_batna(
        self,
        case_value: Decimal,
        litigation_costs: Decimal,
    ) -> Dict[str, Any]:
        """Best Alternative To Negotiated Agreement.

        If mediation fails, the BATNA is proceeding to trial.
        """
        net = (case_value - litigation_costs).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP,
        )
        return {
            "batna": "Proceed to trial",
            "expected_trial_value": str(case_value),
            "estimated_remaining_costs": str(litigation_costs),
            "net_batna_value": str(net),
            "note": (
                "Any settlement offer below the net BATNA value should "
                "be rejected unless non-monetary terms compensate."
            ),
        }

    # ------------------------------------------------------------------
    def calculate_watna(
        self,
        worst_case_scenarios: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Worst Alternative To Negotiated Agreement.

        Assesses the worst realistic outcome if the case goes to trial.
        """
        worst_total = Decimal("0")
        descriptions: List[str] = []
        for sc in worst_case_scenarios:
            amt = _dec(sc.get("amount", 0))
            worst_total += amt
            descriptions.append(
                f"{sc.get('scenario', 'Unknown')}: ${amt}"
            )
        return {
            "watna": "Worst-case trial outcomes",
            "total_worst_exposure": str(worst_total),
            "scenarios": descriptions,
            "note": (
                "This represents the worst realistic outcome, not the "
                "absolute worst case."
            ),
        }

    # ------------------------------------------------------------------
    def get_stats(self) -> dict:
        return {"module": "MediationBriefWriter", "version": "1.0.0"}


# ═══════════════════════════════════════════════════════════════════════════
# SettlementAnalyzer  (main orchestrator)
# ═══════════════════════════════════════════════════════════════════════════

class SettlementAnalyzer:
    """Top-level settlement analysis, valuation, and negotiation engine.

    Provides case valuation, settlement ranges, offer evaluation, demand
    packages, and mediation prep across all case lanes and defendants.
    """

    VERSION = "1.0.0"

    def __init__(
        self,
        db_path: Optional[pathlib.Path] = None,
    ) -> None:
        self._db_path = db_path or _DB_PATH
        self._conn: Optional[sqlite3.Connection] = None
        self.calculator = ExpectedValueCalculator()
        self.demand_generator: Optional[DemandLetterGenerator] = None
        self.mediation_writer = MediationBriefWriter()

    # ------------------------------------------------------------------
    def _init_db(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = _get_conn(self._db_path)
            _ensure_schema(self._conn)
            self.demand_generator = DemandLetterGenerator(self._conn)
        return self._conn

    # ------------------------------------------------------------------
    def close(self) -> None:
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    # ------------------------------------------------------------------
    def analyze_case_value(
        self,
        lane: str,
        claims: Optional[List[str]] = None,
    ) -> List[CaseOutcomeProbability]:
        """Analyse expected case value for a lane.

        Returns a list of ``CaseOutcomeProbability`` — one per claim.
        """
        return self.calculator.calculate_case_value(lane, claims)

    # ------------------------------------------------------------------
    def generate_settlement_range(
        self,
        lane: str,
        defendant: str,
        *,
        strategy: SettlementStrategy = SettlementStrategy.MODERATE,
    ) -> SettlementRange:
        """Compute a settlement range for a specific defendant in a lane.

        The range is derived from expected values and adjusted by strategy.
        """
        outcomes = self.calculator.calculate_case_value(lane)
        total_ev = sum(o.expected_value for o in outcomes)
        total_risks = []
        for o in outcomes:
            total_risks.extend(o.risks)

        discounted = self.calculator.discount_for_risk(total_ev, total_risks)

        strategy_mult: Dict[SettlementStrategy, Tuple[Decimal, Decimal, Decimal, Decimal]] = {
            SettlementStrategy.AGGRESSIVE:   (Decimal("0.80"), Decimal("1.20"), Decimal("1.80"), Decimal("0.60")),
            SettlementStrategy.MODERATE:      (Decimal("0.60"), Decimal("1.00"), Decimal("1.50"), Decimal("0.40")),
            SettlementStrategy.CONSERVATIVE:  (Decimal("0.40"), Decimal("0.75"), Decimal("1.20"), Decimal("0.25")),
            SettlementStrategy.WALKAWAY:      (Decimal("0.20"), Decimal("0.50"), Decimal("0.80"), Decimal("0.10")),
        }
        f, t, c, w = strategy_mult.get(
            strategy, strategy_mult[SettlementStrategy.MODERATE],
        )

        sr = SettlementRange(
            lane=lane,
            defendant_name=defendant,
            floor=(discounted * f).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            target=(discounted * t).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            ceiling=(discounted * c).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            walkaway=(discounted * w).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            rationale=(
                f"Based on {len(outcomes)} claim(s) in Lane {lane} with "
                f"total EV ${total_ev}, risk-discounted to ${discounted}. "
                f"Strategy: {strategy.value}."
            ),
        )

        self._persist_analysis(lane, defendant, outcomes, sr, strategy)
        return sr

    # ------------------------------------------------------------------
    def _persist_analysis(
        self,
        lane: str,
        defendant: str,
        outcomes: List[CaseOutcomeProbability],
        sr: SettlementRange,
        strategy: SettlementStrategy,
    ) -> None:
        db = self._init_db()
        for o in outcomes:
            analysis_id = str(uuid.uuid4())
            db.execute(
                "INSERT OR REPLACE INTO settlement_analysis "
                "(analysis_id, lane, defendant_name, claim_type, "
                "win_probability, damages_low, damages_mid, damages_high, "
                "expected_value, settlement_floor, settlement_target, "
                "settlement_ceiling, walkaway, risk_factors, key_factors, "
                "strategy, rationale, updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    analysis_id, lane, defendant, o.claim_type,
                    o.win_probability,
                    str(o.damages_if_win_low), str(o.damages_if_win_mid),
                    str(o.damages_if_win_high), str(o.expected_value),
                    str(sr.floor), str(sr.target), str(sr.ceiling),
                    str(sr.walkaway),
                    json.dumps(o.risks), json.dumps(o.key_factors),
                    strategy.value, sr.rationale, _now_iso(),
                ),
            )
        db.commit()

    # ------------------------------------------------------------------
    def evaluate_offer(
        self,
        offer_amount: Decimal,
        lane: str,
        *,
        risk_tolerance: str = "MODERATE",
    ) -> Dict[str, Any]:
        """Evaluate a settlement offer for a lane.

        Returns a recommendation: ACCEPT, REJECT, or COUNTER.
        """
        outcomes = self.calculator.calculate_case_value(lane)
        total_ev = sum(o.expected_value for o in outcomes)
        remaining_costs = self.calculator.calculate_litigation_costs(
            ["discovery", "trial_prep", "trial"],
        )
        net_ev = self.calculator.net_expected_value(total_ev, remaining_costs)

        result = self.calculator.compare_settlement_to_trial(
            offer_amount, net_ev, risk_tolerance,
        )
        result["lane"] = lane
        result["total_expected_value"] = str(total_ev)
        result["remaining_costs"] = str(remaining_costs)
        result["net_expected_value"] = str(net_ev)
        return result

    # ------------------------------------------------------------------
    def generate_demand_package(
        self,
        defendants: Optional[List[Tuple[str, str, Decimal]]] = None,
        *,
        deadline_days: int = 30,
    ) -> Dict[str, Any]:
        """Generate demand letters for specified defendants.

        Parameters
        ----------
        defendants : list of (name, lane, amount)
            If ``None``, generates demands for all 19 defendants with
            placeholder amounts.
        """
        self._init_db()
        assert self.demand_generator is not None

        if defendants is None:
            defendants = [
                (d["name"], d["lane"].split(",")[0], Decimal("10000"))
                for d in DEFENDANTS
            ]

        results: List[Dict[str, Any]] = []
        total = Decimal("0")
        for name, lane, amount in defendants:
            result = self.demand_generator.generate_demand(
                defendant=name,
                lane=lane,
                amount=amount,
                deadline_days=deadline_days,
            )
            results.append(result)
            total += amount

        return {
            "letters": results,
            "defendant_count": len(defendants),
            "total_demanded": str(total),
        }

    # ------------------------------------------------------------------
    def prepare_mediation(
        self,
        lane: str,
        *,
        issues: Optional[List[str]] = None,
        positions: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Prepare a complete mediation package for a lane.

        Returns brief text, opening statement, BATNA, and WATNA.
        """
        if issues is None:
            default_issues: Dict[str, List[str]] = {
                "A": ["Custody schedule", "Decision-making authority",
                      "Child support amount", "Communication protocols"],
                "B": ["Lease violations", "Discriminatory enforcement",
                      "Damages amount", "Injunctive relief"],
                "D": ["PPO modification/dismissal", "Contact restrictions",
                      "False allegations remedy"],
            }
            issues = default_issues.get(lane.upper(), ["Settlement terms"])

        if positions is None:
            positions = {iss: "[Position to be stated at mediation]" for iss in issues}

        brief = self.mediation_writer.generate_mediation_brief(lane, issues, positions)
        opening = self.mediation_writer.prepare_opening_statement(
            [f"Issue: {iss}" for iss in issues[:5]],
        )

        outcomes = self.calculator.calculate_case_value(lane)
        total_ev = sum(o.expected_value for o in outcomes)
        costs = self.calculator.calculate_litigation_costs(
            ["mediation", "trial_prep", "trial"],
        )
        batna = self.mediation_writer.calculate_batna(total_ev, costs)
        watna = self.mediation_writer.calculate_watna([
            {"scenario": "Complete loss at trial", "amount": costs},
            {"scenario": "Adverse custody modification", "amount": Decimal("25000")},
        ])

        return {
            "lane": lane,
            "brief": brief,
            "opening_statement": opening,
            "batna": batna,
            "watna": watna,
            "issues_count": len(issues),
        }

    # ------------------------------------------------------------------
    def get_defendant_analysis(self, defendant_name: str) -> Dict[str, Any]:
        """Get analysis for a specific defendant across all lanes."""
        defendant_info = None
        for d in DEFENDANTS:
            if d["name"].lower() == defendant_name.lower():
                defendant_info = d
                break

        if not defendant_info:
            return {"error": f"Defendant '{defendant_name}' not found in registry."}

        lanes = [ln.strip() for ln in defendant_info["lane"].split(",")]
        analyses: List[Dict[str, Any]] = []
        for lane in lanes:
            outcomes = self.calculator.calculate_case_value(lane)
            for o in outcomes:
                analyses.append(o.to_dict())

        immunity_note = ""
        name_lower = defendant_name.lower()
        if "mcneill" in name_lower:
            immunity_note = (
                "IMMUNITY ANALYSIS: Judicial immunity is absolute for judicial "
                "acts within jurisdiction. However, acts that are clearly "
                "non-judicial or taken in complete absence of jurisdiction "
                "are not protected. See Mireles v. Waco, 502 U.S. 9 (1991)."
            )
        elif "foc" in name_lower:
            immunity_note = (
                "IMMUNITY ANALYSIS: Governmental immunity under MCL 691.1407 "
                "protects FOC officers acting within scope of employment "
                "unless gross negligence is shown."
            )
        elif "rusco" in name_lower:
            immunity_note = (
                "IMMUNITY ANALYSIS: Mediator liability is limited under "
                "MCL 691.1558 (mediator immunity) but does not extend to "
                "acts outside the scope of mediation duties."
            )
        elif "hoa" in name_lower or "shady" in name_lower:
            immunity_note = (
                "DAMAGES NOTE: MCL 37.2801 provides for treble damages "
                "in housing discrimination cases. Business judgment rule "
                "may provide partial defense."
            )

        return {
            "defendant": defendant_info,
            "lanes": lanes,
            "analyses": analyses,
            "immunity_note": immunity_note,
        }

    # ------------------------------------------------------------------
    def get_stats(self) -> dict:
        """Return engine-wide statistics."""
        db = self._init_db()
        row = db.execute(
            "SELECT "
            "  (SELECT COUNT(*) FROM settlement_analysis) AS analyses, "
            "  (SELECT COUNT(DISTINCT defendant_name) FROM settlement_analysis) AS defendants_analysed, "
            "  (SELECT COUNT(DISTINCT lane) FROM settlement_analysis) AS lanes_analysed, "
            "  (SELECT COUNT(*) FROM demand_letters) AS demands, "
            "  (SELECT COUNT(*) FROM demand_letters WHERE status = 'DRAFT') AS draft_demands, "
            "  (SELECT COUNT(*) FROM demand_letters WHERE status = 'SENT') AS sent_demands"
        ).fetchone()
        d = dict(row)
        d["engine_version"] = self.VERSION
        d["defendant_registry_count"] = len(DEFENDANTS)
        d["calculator"] = self.calculator.get_stats()
        if self.demand_generator:
            d["demand_generator"] = self.demand_generator.get_stats()
        d["mediation_writer"] = self.mediation_writer.get_stats()
        return d


# ═══════════════════════════════════════════════════════════════════════════
# CLI / Demo
# ═══════════════════════════════════════════════════════════════════════════

def _cli_main() -> int:
    """Minimal CLI for settlement analysis."""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="SettlementAnalyzer — case valuation and negotiation",
    )
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("stats", help="Print engine statistics")
    sp_val = sub.add_parser("value", help="Compute case value for a lane")
    sp_val.add_argument("lane", help="Case lane (A-F)")
    sp_range = sub.add_parser("range", help="Settlement range for defendant")
    sp_range.add_argument("lane", help="Case lane")
    sp_range.add_argument("defendant", help="Defendant name")
    sp_eval = sub.add_parser("evaluate", help="Evaluate a settlement offer")
    sp_eval.add_argument("lane", help="Case lane")
    sp_eval.add_argument("amount", help="Offer amount (dollars)")
    sub.add_parser("demo", help="Run demo")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 0

    engine = SettlementAnalyzer()
    try:
        if args.command == "stats":
            print(json.dumps(engine.get_stats(), indent=2, default=str))

        elif args.command == "value":
            outcomes = engine.analyze_case_value(args.lane)
            for o in outcomes:
                print(json.dumps(o.to_dict(), indent=2))

        elif args.command == "range":
            sr = engine.generate_settlement_range(args.lane, args.defendant)
            print(json.dumps(sr.to_dict(), indent=2))

        elif args.command == "evaluate":
            result = engine.evaluate_offer(Decimal(args.amount), args.lane)
            print(json.dumps(result, indent=2, default=str))

        elif args.command == "demo":
            _run_demo(engine)
    finally:
        engine.close()

    return 0


def _run_demo(engine: SettlementAnalyzer) -> None:
    """Demonstrate settlement analysis capabilities."""
    print("=" * 60)
    print("SettlementAnalyzer Demo — Pigors v. Watson")
    print("=" * 60)

    # 1. Case value — Lane A
    print("\n[1] Case Value — Lane A (Custody):")
    outcomes = engine.analyze_case_value("A")
    for o in outcomes:
        print(f"  {o.claim_type}: EV=${o.expected_value} "
              f"(Win: {o.win_probability}%, Range: "
              f"${o.damages_if_win_low}-${o.damages_if_win_high})")

    # 2. Settlement range
    print("\n[2] Settlement Range — Emily A. Watson (Lane A):")
    sr = engine.generate_settlement_range("A", DEFENDANT)
    print(f"  Floor:    ${sr.floor}")
    print(f"  Target:   ${sr.target}")
    print(f"  Ceiling:  ${sr.ceiling}")
    print(f"  Walkaway: ${sr.walkaway}")
    print(f"  Rationale: {sr.rationale[:80]}…")

    # 3. Lane B (Housing)
    print("\n[3] Case Value — Lane B (Housing):")
    outcomes_b = engine.analyze_case_value("B")
    for o in outcomes_b:
        print(f"  {o.claim_type}: EV=${o.expected_value}")

    # 4. Lane E (§1983)
    print("\n[4] Defendant Analysis — Hon. Jenny L. McNeill:")
    analysis = engine.get_defendant_analysis("Hon. Jenny L. McNeill")
    print(f"  Immunity note: {analysis.get('immunity_note', '')[:100]}…")
    for a in analysis.get("analyses", []):
        print(f"  Claim: {a['claim_type']}, EV: ${a['expected_value']}")

    # 5. Offer evaluation
    print("\n[5] Offer Evaluation — $15,000 for Lane A:")
    result = engine.evaluate_offer(Decimal("15000"), "A")
    print(f"  Verdict: {result['verdict']}")
    print(f"  Reasoning: {result['reasoning'][:100]}…")

    # 6. Litigation costs
    print("\n[6] Remaining Litigation Costs:")
    costs = engine.calculator.calculate_litigation_costs(
        ["discovery", "depositions", "trial_prep", "trial"],
    )
    print(f"  Estimated remaining costs: ${costs}")

    # 7. Mediation prep
    print("\n[7] Mediation Prep — Lane A:")
    med = engine.prepare_mediation("A")
    print(f"  Brief length: {len(med['brief'])} chars")
    print(f"  BATNA net value: ${med['batna']['net_batna_value']}")
    print(f"  WATNA exposure: ${med['watna']['total_worst_exposure']}")

    # 8. Demand letter
    print("\n[8] Demand Letter — Emily A. Watson:")
    engine._init_db()
    assert engine.demand_generator is not None
    demand = engine.demand_generator.generate_demand(
        defendant=DEFENDANT,
        lane="A",
        amount=Decimal("75000"),
        deadline_days=30,
        damage_items=[
            DamageItem(
                category="Custody Interference",
                description="Documented denial of parenting time",
                amount=Decimal("25000"),
                authority="MCL 722.23",
            ),
            DamageItem(
                category="Emotional Distress",
                description="Impact on parent-child relationship",
                amount=Decimal("30000"),
                authority="MCL 600.2913",
            ),
            DamageItem(
                category="Litigation Costs",
                description="Filing fees, copies, service",
                amount=Decimal("5000"),
            ),
        ],
    )
    print(f"  Letter ID: {demand['letter_id'][:12]}…")
    print(f"  Amount: ${demand['amount']}")
    print(f"  Deadline: {demand['deadline']}")

    # 9. Stats
    print("\n[9] Engine Stats:")
    stats = engine.get_stats()
    print(json.dumps(stats, indent=2, default=str))

    print("\nDemo complete.")


if __name__ == "__main__":
    sys.exit(_cli_main())
