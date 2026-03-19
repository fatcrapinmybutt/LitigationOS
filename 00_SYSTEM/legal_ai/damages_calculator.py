# -*- coding: utf-8 -*-
"""
Damages Calculator — LitigationOS Legal AI Subsystem
=====================================================
Comprehensive financial damages computation engine for all six case
lanes of the Pigors v. Watson litigation (19 defendants, 8 jurisdictions).

Computes per-category damages with low / mid / high ranges, applies
statutory multipliers (treble, punitive, fee-shifting), calculates
prejudgment interest under MCL 600.6013, and allocates damages across
defendants with joint-and-several liability analysis.

Case Lanes:
    Lane A — Custody (2024-001507-DC) . . . $200K–$500K
    Lane B — Housing (2025-002760-CZ) . . . $150K–$3.4M (treble)
    Lane C — Convergence (cross-lane) . . . supports other lanes
    Lane D — PPO (2023-5907-PP) . . . . . . $50K–$200K
    Lane E — Misconduct / JTC . . . . . . . §1983 / injunctive
    Lane F — Appellate (COA 366810) . . . . costs + preserved damages

Statutory Authority:
    MCL 600.6013  — Prejudgment interest (T-bill + 1%, simple)
    MCL 37.2801   — Housing discrimination treble damages
    42 USC §1983  — Civil rights damages
    42 USC §1988  — Attorney fee shifting
    MCL 445.911   — MCPA treble damages
    MCL 722.28    — Custody attorney fees

Case Context:
    Plaintiff:  Andrew James Pigors (Pro Se)
    Defendant:  Emily A. Watson
    Child:      L.D.W. (per MCR 8.119(H)) — Male
    Judge:      Hon. Jenny L. McNeill — 14th Circuit Court

Usage:
    from legal_ai.damages_calculator import DamagesCalculator

    calc = DamagesCalculator()
    report = calc.generate_damages_report()
    print(f"Total: ${report['total_mid']:,.0f}")

    # Per lane
    lane_a = calc.calculate_lane_damages("A")

    # Per defendant
    allocs = calc.calculate_per_defendant()

Zero external dependencies.  CPU-first.  Local-only.
"""
from __future__ import annotations

import json
import logging
import math
import sqlite3
import textwrap
import uuid
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("legal_ai.damages_calculator")

# ---------------------------------------------------------------------------
# Path resolution — legal_ai → 00_SYSTEM → LitigationOS root
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
_DB_PATH = _HERE.parents[1] / "litigation_context.db"

# ---------------------------------------------------------------------------
# Case Constants
# ---------------------------------------------------------------------------
_PLAINTIFF = "Andrew James Pigors"
_DEFENDANT = "Emily A. Watson"
_CHILD_INITIALS = "L.D.W."
_CHILD_NAME = "Lincoln David Watson"
_JUDGE = "Hon. Jenny L. McNeill"

LANE_LABELS: Dict[str, str] = {
    "A": "Custody (2024-001507-DC)",
    "B": "Housing (2025-002760-CZ)",
    "C": "Convergence (cross-lane)",
    "D": "PPO (2023-5907-PP)",
    "E": "Misconduct / JTC",
    "F": "Appellate (COA 366810)",
}

LANE_CASE_NUMBERS: Dict[str, str] = {
    "A": "2024-001507-DC",
    "B": "2025-002760-CZ",
    "C": "Multi-lane",
    "D": "2023-5907-PP",
    "E": "Judge McNeill",
    "F": "COA 366810",
}

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class DamageCategory(str, Enum):
    """High-level damage categories."""
    ECONOMIC = "economic"
    NON_ECONOMIC = "non_economic"
    STATUTORY = "statutory"
    PUNITIVE = "punitive"
    ATTORNEY_FEES = "attorney_fees"
    PREJUDGMENT_INTEREST = "prejudgment_interest"


class LiabilityType(str, Enum):
    """Liability classification."""
    JOINT = "joint"
    SEVERAL = "several"
    JOINT_AND_SEVERAL = "joint_and_several"


class CalculationMethod(str, Enum):
    """How a damage figure was computed."""
    ACTUAL = "actual"
    ESTIMATED = "estimated"
    STATUTORY_FORMULA = "statutory_formula"
    MULTIPLIER = "multiplier"
    PER_DIEM = "per_diem"
    COMPARABLE_CASE = "comparable_case"
    EXPERT_ESTIMATE = "expert_estimate"


class MultiplierStatute(str, Enum):
    """Statutes authorising damage multipliers."""
    MCL_37_2801 = "MCL 37.2801"           # Housing discrimination — treble
    MCL_445_911 = "MCL 445.911"           # MCPA — treble
    USC_42_1983 = "42 USC §1983"          # Civil rights
    USC_42_1988 = "42 USC §1988"          # Attorney fee shifting
    MCL_600_6013 = "MCL 600.6013"         # Prejudgment interest
    MCL_722_28 = "MCL 722.28"             # Custody attorney fees


# ---------------------------------------------------------------------------
# Michigan Statutory Interest Rates (MCL 600.6013)
# One-year US Treasury bill rate + 1%, simple interest
# ---------------------------------------------------------------------------
_MI_INTEREST_RATES: Dict[int, float] = {
    2019: 0.0359,  # T-bill ~2.59% + 1%
    2020: 0.0259,  # T-bill ~1.59% + 1%
    2021: 0.0109,  # T-bill ~0.09% + 1%
    2022: 0.0209,  # T-bill ~1.09% + 1%
    2023: 0.0509,  # T-bill ~4.09% + 1%
    2024: 0.0534,  # T-bill ~4.34% + 1%
    2025: 0.0509,  # T-bill ~4.09% + 1%
    2026: 0.0500,  # Estimated
}

# Default rate when year is unknown
_DEFAULT_INTEREST_RATE: float = 0.0509


# ---------------------------------------------------------------------------
# 19 Named Defendants
# ---------------------------------------------------------------------------

@dataclass
class Defendant:
    """A named defendant in the litigation."""

    name: str
    role: str = ""
    lanes: List[str] = field(default_factory=list)
    joint_several: bool = True
    percentage_liability: float = 0.0
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to dictionary."""
        return asdict(self)


# The 19 defendants tracked in this litigation
DEFENDANTS: List[Defendant] = [
    Defendant(
        name="Emily A. Watson",
        role="Defendant — opposing party / mother",
        lanes=["A", "D"],
        joint_several=True,
        percentage_liability=35.0,
    ),
    Defendant(
        name="Pamela Rusco",
        role="Court-appointed mediator",
        lanes=["A"],
        joint_several=False,
        percentage_liability=5.0,
    ),
    Defendant(
        name="Hon. Jenny L. McNeill",
        role="Presiding judge — 14th Circuit Court",
        lanes=["E"],
        joint_several=False,
        percentage_liability=15.0,
        notes="Judicial immunity may apply — §1983 exception for "
              "actions in clear absence of jurisdiction",
    ),
    Defendant(
        name="Friend of Court — Muskegon County",
        role="FOC office / officers",
        lanes=["A"],
        joint_several=True,
        percentage_liability=8.0,
    ),
    Defendant(
        name="CPS Investigator",
        role="Child Protective Services case worker",
        lanes=["A"],
        joint_several=True,
        percentage_liability=5.0,
    ),
    Defendant(
        name="Shady Oaks HOA",
        role="Homeowners association — housing defendant",
        lanes=["B"],
        joint_several=True,
        percentage_liability=10.0,
    ),
    Defendant(
        name="Shady Oaks Management Company",
        role="Property management company",
        lanes=["B"],
        joint_several=True,
        percentage_liability=8.0,
    ),
    Defendant(
        name="Shady Oaks HOA Board Member 1",
        role="Individual board member",
        lanes=["B"],
        joint_several=True,
        percentage_liability=2.0,
    ),
    Defendant(
        name="Shady Oaks HOA Board Member 2",
        role="Individual board member",
        lanes=["B"],
        joint_several=True,
        percentage_liability=2.0,
    ),
    Defendant(
        name="Shady Oaks HOA Board Member 3",
        role="Individual board member",
        lanes=["B"],
        joint_several=True,
        percentage_liability=2.0,
    ),
    Defendant(
        name="Muskegon County",
        role="County government — §1983 respondeat superior",
        lanes=["A", "E"],
        joint_several=True,
        percentage_liability=5.0,
    ),
    Defendant(
        name="14th Circuit Court",
        role="Court entity",
        lanes=["E"],
        joint_several=False,
        percentage_liability=3.0,
    ),
    Defendant(
        name="GAL / Guardian ad Litem",
        role="Appointed guardian for L.D.W.",
        lanes=["A"],
        joint_several=False,
        percentage_liability=3.0,
    ),
    Defendant(
        name="Custody Evaluator",
        role="Court-ordered custody evaluator",
        lanes=["A"],
        joint_several=False,
        percentage_liability=3.0,
    ),
    Defendant(
        name="FOC Referee",
        role="Friend of Court referee",
        lanes=["A"],
        joint_several=False,
        percentage_liability=3.0,
    ),
    Defendant(
        name="Law Enforcement — Responding Officer 1",
        role="Officer involved in custody enforcement",
        lanes=["A", "D"],
        joint_several=True,
        percentage_liability=2.0,
    ),
    Defendant(
        name="Law Enforcement — Responding Officer 2",
        role="Officer involved in PPO enforcement",
        lanes=["D"],
        joint_several=True,
        percentage_liability=2.0,
    ),
    Defendant(
        name="Opposing Counsel (if applicable)",
        role="Attorney for Emily A. Watson",
        lanes=["A", "D"],
        joint_several=False,
        percentage_liability=2.0,
    ),
    Defendant(
        name="Insurance Carrier (if applicable)",
        role="Liability insurer for housing defendants",
        lanes=["B"],
        joint_several=True,
        percentage_liability=5.0,
    ),
]


# ---------------------------------------------------------------------------
# Database Helpers
# ---------------------------------------------------------------------------

def _connect(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Open a WAL-mode connection with safe PRAGMAs."""
    path = db_path or _DB_PATH
    conn = sqlite3.connect(str(path), timeout=60)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    """Check if a table exists in the database."""
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row is not None


_DAMAGES_ITEMS_DDL = """\
CREATE TABLE IF NOT EXISTS damages_items (
    id                  TEXT PRIMARY KEY,
    category            TEXT NOT NULL,
    subcategory         TEXT,
    description         TEXT,
    amount_low          REAL DEFAULT 0.0,
    amount_mid          REAL DEFAULT 0.0,
    amount_high         REAL DEFAULT 0.0,
    defendants_json     TEXT,
    evidence_refs_json  TEXT,
    statute_basis       TEXT,
    lane                TEXT NOT NULL,
    calculation_method  TEXT DEFAULT 'estimated',
    confidence          REAL DEFAULT 50.0,
    multiplier_applied  REAL DEFAULT 1.0,
    interest_amount     REAL DEFAULT 0.0,
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL
)
"""

_DEFENDANT_ALLOCATIONS_DDL = """\
CREATE TABLE IF NOT EXISTS defendant_allocations (
    id                  TEXT PRIMARY KEY,
    defendant_name      TEXT NOT NULL,
    defendant_role      TEXT,
    joint_several       INTEGER DEFAULT 1,
    percentage_liability REAL DEFAULT 0.0,
    total_low           REAL DEFAULT 0.0,
    total_mid           REAL DEFAULT 0.0,
    total_high          REAL DEFAULT 0.0,
    lanes_json          TEXT,
    items_json          TEXT,
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL
)
"""


def _ensure_tables(conn: sqlite3.Connection) -> None:
    """Create required tables if they don't exist."""
    conn.execute(_DAMAGES_ITEMS_DDL)
    conn.execute(_DEFENDANT_ALLOCATIONS_DDL)
    conn.commit()


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class DamageItem:
    """A single damage item with range estimates."""

    item_id: str = ""
    category: str = DamageCategory.ECONOMIC.value
    subcategory: str = ""
    description: str = ""
    amount_low: float = 0.0
    amount_mid: float = 0.0
    amount_high: float = 0.0
    defendants: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    statute_basis: str = ""
    lane: str = "A"
    calculation_method: str = CalculationMethod.ESTIMATED.value
    confidence: float = 50.0
    multiplier_applied: float = 1.0
    interest_amount: float = 0.0

    def __post_init__(self) -> None:
        if not self.item_id:
            self.item_id = str(uuid.uuid4())[:12]

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to dictionary."""
        return asdict(self)

    def total_range(self) -> Tuple[float, float, float]:
        """Return (low, mid, high) totals including interest."""
        return (
            self.amount_low + self.interest_amount,
            self.amount_mid + self.interest_amount,
            self.amount_high + self.interest_amount,
        )


@dataclass
class DefendantAllocation:
    """Damage allocation for a single defendant."""

    allocation_id: str = ""
    defendant_name: str = ""
    defendant_role: str = ""
    joint_several: bool = True
    percentage_liability: float = 0.0
    allocated_items: List[DamageItem] = field(default_factory=list)
    total_low: float = 0.0
    total_mid: float = 0.0
    total_high: float = 0.0

    def __post_init__(self) -> None:
        if not self.allocation_id:
            self.allocation_id = str(uuid.uuid4())[:12]

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to dictionary."""
        d = asdict(self)
        d["allocated_items"] = [item.to_dict() for item in self.allocated_items]
        return d

    def calculate_totals(self) -> Tuple[float, float, float]:
        """Calculate total allocated damages."""
        self.total_low = sum(i.amount_low for i in self.allocated_items) * (
            self.percentage_liability / 100.0
        )
        self.total_mid = sum(i.amount_mid for i in self.allocated_items) * (
            self.percentage_liability / 100.0
        )
        self.total_high = sum(i.amount_high for i in self.allocated_items) * (
            self.percentage_liability / 100.0
        )
        return (self.total_low, self.total_mid, self.total_high)


@dataclass
class LaneDamagesSummary:
    """Summary of damages for a single case lane."""

    lane: str = ""
    lane_label: str = ""
    items: List[DamageItem] = field(default_factory=list)
    total_low: float = 0.0
    total_mid: float = 0.0
    total_high: float = 0.0
    item_count: int = 0
    categories: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to dictionary."""
        d = {
            "lane": self.lane,
            "lane_label": self.lane_label,
            "total_low": self.total_low,
            "total_mid": self.total_mid,
            "total_high": self.total_high,
            "item_count": self.item_count,
            "categories": self.categories,
            "items": [i.to_dict() for i in self.items],
        }
        return d


# ---------------------------------------------------------------------------
# Per-Lane Damage Templates
# ---------------------------------------------------------------------------

_LANE_A_DAMAGES: List[Dict[str, Any]] = [
    {
        "category": DamageCategory.ECONOMIC.value,
        "subcategory": "lost_parenting_time",
        "description": "Lost parenting time — 305+ documented interference incidents "
                       "× per-diem value ($328–$656)",
        "amount_low": 100_000.0,
        "amount_mid": 152_500.0,
        "amount_high": 200_000.0,
        "statute_basis": "MCL 722.27a",
        "calculation_method": CalculationMethod.PER_DIEM.value,
        "evidence_refs": [
            "Parenting time interference log (305 incidents)",
            "Court-ordered parenting time schedule",
            "Communication records showing denial",
        ],
        "confidence": 70.0,
    },
    {
        "category": DamageCategory.NON_ECONOMIC.value,
        "subcategory": "emotional_distress",
        "description": "Emotional distress from denial of parental rights and "
                       "parent-child relationship harm",
        "amount_low": 50_000.0,
        "amount_mid": 100_000.0,
        "amount_high": 150_000.0,
        "statute_basis": "MCL 600.2911",
        "calculation_method": CalculationMethod.COMPARABLE_CASE.value,
        "evidence_refs": [
            "Declaration of emotional impact",
            "Counseling records",
            "Pattern of sustained interference",
        ],
        "confidence": 75.0,
    },
    {
        "category": DamageCategory.ECONOMIC.value,
        "subcategory": "therapy_costs",
        "description": "Therapy and counseling costs for L.D.W. and plaintiff",
        "amount_low": 5_000.0,
        "amount_mid": 15_000.0,
        "amount_high": 30_000.0,
        "statute_basis": "MCL 722.23(c)",
        "calculation_method": CalculationMethod.ACTUAL.value,
        "evidence_refs": [
            "Therapy session records",
            "Counselor recommendations",
        ],
        "confidence": 85.0,
    },
    {
        "category": DamageCategory.ATTORNEY_FEES.value,
        "subcategory": "pro_se_litigation_costs",
        "description": "Filing fees, copies, travel, lost work time for pro se litigation",
        "amount_low": 15_000.0,
        "amount_mid": 25_000.0,
        "amount_high": 40_000.0,
        "statute_basis": "MCL 722.28",
        "calculation_method": CalculationMethod.ACTUAL.value,
        "evidence_refs": [
            "Filing fee receipts",
            "Copy/printing costs",
            "Travel costs to court",
            "Lost work time documentation",
        ],
        "confidence": 85.0,
    },
    {
        "category": DamageCategory.NON_ECONOMIC.value,
        "subcategory": "loss_of_consortium",
        "description": "Loss of parent-child relationship and companionship",
        "amount_low": 25_000.0,
        "amount_mid": 50_000.0,
        "amount_high": 100_000.0,
        "statute_basis": "MCL 600.2922",
        "calculation_method": CalculationMethod.COMPARABLE_CASE.value,
        "evidence_refs": [
            "Testimony regarding father-son bond",
            "Evidence of relationship quality before interference",
        ],
        "confidence": 60.0,
    },
]

_LANE_B_DAMAGES: List[Dict[str, Any]] = [
    {
        "category": DamageCategory.ECONOMIC.value,
        "subcategory": "security_deposit",
        "description": "Wrongfully withheld security deposit",
        "amount_low": 1_500.0,
        "amount_mid": 2_500.0,
        "amount_high": 3_500.0,
        "statute_basis": "MCL 554.613",
        "calculation_method": CalculationMethod.ACTUAL.value,
        "evidence_refs": ["Lease agreement", "Security deposit receipt"],
        "confidence": 90.0,
    },
    {
        "category": DamageCategory.ECONOMIC.value,
        "subcategory": "moving_costs",
        "description": "Forced relocation costs due to habitability failure / eviction",
        "amount_low": 3_000.0,
        "amount_mid": 6_000.0,
        "amount_high": 10_000.0,
        "statute_basis": "MCL 554.139",
        "calculation_method": CalculationMethod.ACTUAL.value,
        "evidence_refs": ["Moving receipts", "New housing costs"],
        "confidence": 80.0,
    },
    {
        "category": DamageCategory.ECONOMIC.value,
        "subcategory": "habitability_damages",
        "description": "Rent abatement and repair costs for uninhabitable conditions",
        "amount_low": 10_000.0,
        "amount_mid": 25_000.0,
        "amount_high": 50_000.0,
        "statute_basis": "MCL 554.139",
        "calculation_method": CalculationMethod.ESTIMATED.value,
        "evidence_refs": [
            "Photos of conditions",
            "Inspection reports",
            "Complaint history to management",
        ],
        "confidence": 70.0,
    },
    {
        "category": DamageCategory.STATUTORY.value,
        "subcategory": "housing_discrimination_treble",
        "description": "Housing discrimination treble damages — familial status "
                       "discrimination (MCL 37.2801: 3× actual damages)",
        "amount_low": 150_000.0,
        "amount_mid": 500_000.0,
        "amount_high": 1_000_000.0,
        "statute_basis": "MCL 37.2801",
        "calculation_method": CalculationMethod.MULTIPLIER.value,
        "evidence_refs": [
            "Evidence of discriminatory treatment",
            "Comparator tenant data",
            "Communications showing bias",
        ],
        "confidence": 55.0,
    },
    {
        "category": DamageCategory.NON_ECONOMIC.value,
        "subcategory": "emotional_distress_housing",
        "description": "Emotional distress from housing discrimination and "
                       "unsafe living conditions",
        "amount_low": 25_000.0,
        "amount_mid": 75_000.0,
        "amount_high": 150_000.0,
        "statute_basis": "MCL 37.2801",
        "calculation_method": CalculationMethod.COMPARABLE_CASE.value,
        "evidence_refs": [
            "Impact statement",
            "Mental health records",
        ],
        "confidence": 60.0,
    },
    {
        "category": DamageCategory.PUNITIVE.value,
        "subcategory": "housing_punitive",
        "description": "Punitive damages for willful housing discrimination",
        "amount_low": 50_000.0,
        "amount_mid": 250_000.0,
        "amount_high": 500_000.0,
        "statute_basis": "MCL 37.2801",
        "calculation_method": CalculationMethod.COMPARABLE_CASE.value,
        "evidence_refs": ["Pattern of discriminatory conduct"],
        "confidence": 40.0,
    },
    {
        "category": DamageCategory.ATTORNEY_FEES.value,
        "subcategory": "housing_attorney_fees",
        "description": "Attorney fees and litigation costs for housing case",
        "amount_low": 10_000.0,
        "amount_mid": 25_000.0,
        "amount_high": 50_000.0,
        "statute_basis": "MCL 37.2802",
        "calculation_method": CalculationMethod.ESTIMATED.value,
        "evidence_refs": ["Fee petition", "Time records"],
        "confidence": 75.0,
    },
]

_LANE_D_DAMAGES: List[Dict[str, Any]] = [
    {
        "category": DamageCategory.NON_ECONOMIC.value,
        "subcategory": "false_ppo_harm",
        "description": "Harm from wrongfully issued PPO — stigma, "
                       "restriction of liberty, employment impact",
        "amount_low": 15_000.0,
        "amount_mid": 50_000.0,
        "amount_high": 100_000.0,
        "statute_basis": "MCL 600.2950",
        "calculation_method": CalculationMethod.COMPARABLE_CASE.value,
        "evidence_refs": [
            "PPO documentation",
            "Impact on employment",
            "Stigma evidence",
        ],
        "confidence": 55.0,
    },
    {
        "category": DamageCategory.ECONOMIC.value,
        "subcategory": "lost_custody_access",
        "description": "Lost custody access due to false PPO — per-diem "
                       "parenting time value",
        "amount_low": 20_000.0,
        "amount_mid": 40_000.0,
        "amount_high": 75_000.0,
        "statute_basis": "MCL 722.27a",
        "calculation_method": CalculationMethod.PER_DIEM.value,
        "evidence_refs": [
            "PPO duration records",
            "Parenting time schedule",
            "Custody order",
        ],
        "confidence": 65.0,
    },
    {
        "category": DamageCategory.NON_ECONOMIC.value,
        "subcategory": "reputation_damage",
        "description": "Reputation damage from false allegations in PPO petition",
        "amount_low": 10_000.0,
        "amount_mid": 30_000.0,
        "amount_high": 50_000.0,
        "statute_basis": "MCL 600.2911",
        "calculation_method": CalculationMethod.COMPARABLE_CASE.value,
        "evidence_refs": ["Third-party impact statements"],
        "confidence": 45.0,
    },
    {
        "category": DamageCategory.NON_ECONOMIC.value,
        "subcategory": "emotional_distress_ppo",
        "description": "Emotional distress from false PPO and separation from child",
        "amount_low": 15_000.0,
        "amount_mid": 35_000.0,
        "amount_high": 75_000.0,
        "statute_basis": "MCL 600.2911",
        "calculation_method": CalculationMethod.COMPARABLE_CASE.value,
        "evidence_refs": ["Mental health records", "Impact declaration"],
        "confidence": 60.0,
    },
]

_LANE_E_DAMAGES: List[Dict[str, Any]] = [
    {
        "category": DamageCategory.STATUTORY.value,
        "subcategory": "section_1983_damages",
        "description": "42 USC §1983 — deprivation of due process rights "
                       "by judicial officer acting in clear absence of jurisdiction",
        "amount_low": 50_000.0,
        "amount_mid": 200_000.0,
        "amount_high": 500_000.0,
        "statute_basis": "42 USC §1983",
        "calculation_method": CalculationMethod.COMPARABLE_CASE.value,
        "evidence_refs": [
            "Ex parte communication evidence",
            "Bias indicators",
            "Due process violation record",
        ],
        "confidence": 40.0,
    },
    {
        "category": DamageCategory.PUNITIVE.value,
        "subcategory": "section_1983_punitive",
        "description": "Punitive damages for willful constitutional violations — "
                       "up to 10× compensatory",
        "amount_low": 100_000.0,
        "amount_mid": 500_000.0,
        "amount_high": 2_000_000.0,
        "statute_basis": "42 USC §1983",
        "calculation_method": CalculationMethod.MULTIPLIER.value,
        "evidence_refs": ["Pattern of willful misconduct"],
        "confidence": 30.0,
    },
    {
        "category": DamageCategory.ATTORNEY_FEES.value,
        "subcategory": "section_1988_fees",
        "description": "42 USC §1988 attorney fee shifting for prevailing "
                       "party in §1983 action",
        "amount_low": 25_000.0,
        "amount_mid": 75_000.0,
        "amount_high": 150_000.0,
        "statute_basis": "42 USC §1988",
        "calculation_method": CalculationMethod.STATUTORY_FORMULA.value,
        "evidence_refs": ["Fee petition", "Time records"],
        "confidence": 65.0,
    },
]

_LANE_F_DAMAGES: List[Dict[str, Any]] = [
    {
        "category": DamageCategory.ECONOMIC.value,
        "subcategory": "costs_of_appeal",
        "description": "Costs of appeal — filing fees, transcript costs, "
                       "printing, service",
        "amount_low": 2_000.0,
        "amount_mid": 5_000.0,
        "amount_high": 10_000.0,
        "statute_basis": "MCR 7.219",
        "calculation_method": CalculationMethod.ACTUAL.value,
        "evidence_refs": ["Filing receipts", "Transcript invoices"],
        "confidence": 90.0,
    },
    {
        "category": DamageCategory.ECONOMIC.value,
        "subcategory": "lost_custody_during_appeal",
        "description": "Lost parenting time during pendency of appeal",
        "amount_low": 10_000.0,
        "amount_mid": 30_000.0,
        "amount_high": 60_000.0,
        "statute_basis": "MCL 722.27a",
        "calculation_method": CalculationMethod.PER_DIEM.value,
        "evidence_refs": ["Appeal timeline", "Custody schedule"],
        "confidence": 60.0,
    },
]

_ALL_LANE_DAMAGES: Dict[str, List[Dict[str, Any]]] = {
    "A": _LANE_A_DAMAGES,
    "B": _LANE_B_DAMAGES,
    "C": [],  # Convergence — no direct damages
    "D": _LANE_D_DAMAGES,
    "E": _LANE_E_DAMAGES,
    "F": _LANE_F_DAMAGES,
}


# ---------------------------------------------------------------------------
# PrejudgmentInterestCalculator
# ---------------------------------------------------------------------------

class PrejudgmentInterestCalculator:
    """Calculate prejudgment interest under MCL 600.6013."""

    @staticmethod
    def get_michigan_rate(year: int) -> float:
        """Look up Michigan statutory interest rate for a given year."""
        return _MI_INTEREST_RATES.get(year, _DEFAULT_INTEREST_RATE)

    @staticmethod
    def compound_or_simple() -> str:
        """Michigan uses simple interest for prejudgment interest."""
        return "simple"

    def calculate(
        self,
        principal: float,
        start_date: date,
        end_date: date,
        rate: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Calculate prejudgment interest on a principal amount.

        MCL 600.6013: Interest accrues from the date of filing the complaint.
        Michigan uses simple interest at the statutory rate.
        """
        if rate is None:
            rate = self.get_michigan_rate(start_date.year)

        days = (end_date - start_date).days
        if days <= 0:
            return {
                "principal": principal,
                "interest": 0.0,
                "total": principal,
                "rate": rate,
                "days": 0,
                "method": "simple",
            }

        years = days / 365.25
        interest = principal * rate * years

        return {
            "principal": round(principal, 2),
            "interest": round(interest, 2),
            "total": round(principal + interest, 2),
            "rate": rate,
            "days": days,
            "years": round(years, 2),
            "method": "simple",
            "statute": "MCL 600.6013",
        }

    def apply_to_damages(
        self,
        damage_items: List[DamageItem],
        judgment_date: date,
        filing_date: Optional[date] = None,
    ) -> List[DamageItem]:
        """Apply prejudgment interest to each damage item."""
        if filing_date is None:
            filing_date = date(2024, 3, 15)  # Approximate filing date

        for item in damage_items:
            result = self.calculate(item.amount_mid, filing_date, judgment_date)
            item.interest_amount = result["interest"]

        return damage_items


# ---------------------------------------------------------------------------
# StatutoryMultiplierEngine
# ---------------------------------------------------------------------------

class StatutoryMultiplierEngine:
    """Apply statutory damage multipliers."""

    @staticmethod
    def apply_treble_damages(
        base_amount: float, statute: str = "MCL 37.2801"
    ) -> Dict[str, Any]:
        """
        Apply treble (3×) damages.

        MCL 37.2801 — Housing discrimination: actual damages × 3
        MCL 445.911 — MCPA consumer protection: actual damages × 3
        """
        trebled = base_amount * 3.0
        return {
            "base": round(base_amount, 2),
            "multiplier": 3.0,
            "trebled": round(trebled, 2),
            "statute": statute,
            "note": f"Treble damages under {statute}",
        }

    @staticmethod
    def apply_1983_fees(
        damages: float,
        hours_spent: float,
        hourly_rate: float = 350.0,
    ) -> Dict[str, Any]:
        """
        Calculate 42 USC §1988 attorney fee award.

        Pro se litigants may recover fees at a reduced rate.
        Lodestar method: hours × reasonable rate × multiplier.
        """
        lodestar = hours_spent * hourly_rate
        pro_se_adjustment = 0.5  # Pro se typically gets 50% of lodestar
        adjusted = lodestar * pro_se_adjustment

        return {
            "hours": hours_spent,
            "hourly_rate": hourly_rate,
            "lodestar": round(lodestar, 2),
            "pro_se_adjustment": pro_se_adjustment,
            "adjusted_fees": round(adjusted, 2),
            "underlying_damages": round(damages, 2),
            "statute": "42 USC §1988",
        }

    @staticmethod
    def apply_consumer_protection(base_amount: float) -> Dict[str, Any]:
        """Apply MCPA treble damages (MCL 445.911)."""
        trebled = base_amount * 3.0
        min_statutory = 250.0  # Minimum statutory damages
        final = max(trebled, min_statutory)
        return {
            "base": round(base_amount, 2),
            "multiplier": 3.0,
            "trebled": round(final, 2),
            "minimum_statutory": min_statutory,
            "statute": "MCL 445.911",
        }

    @staticmethod
    def calculate_fee_shifting(
        prevailing_party: str = "plaintiff",
        statute: str = "42 USC §1988",
    ) -> Dict[str, Any]:
        """Determine which statutes allow fee shifting."""
        fee_shifting_statutes: Dict[str, Dict[str, Any]] = {
            "42 USC §1988": {
                "allows_fee_shifting": True,
                "prevailing_party_required": True,
                "pro_se_eligible": True,
                "note": "Prevailing §1983 plaintiff entitled to fees; "
                        "pro se at reduced rate",
            },
            "MCL 37.2802": {
                "allows_fee_shifting": True,
                "prevailing_party_required": True,
                "pro_se_eligible": True,
                "note": "Civil rights / housing discrimination — fees to prevailing party",
            },
            "MCL 722.28": {
                "allows_fee_shifting": True,
                "prevailing_party_required": False,
                "pro_se_eligible": True,
                "note": "Custody — court may order fees for enforcement actions",
            },
            "MCL 445.911": {
                "allows_fee_shifting": True,
                "prevailing_party_required": True,
                "pro_se_eligible": True,
                "note": "MCPA — attorney fees to prevailing consumer",
            },
        }

        info = fee_shifting_statutes.get(statute, {
            "allows_fee_shifting": False,
            "note": f"No fee-shifting provision found for {statute}",
        })
        info["statute"] = statute
        info["prevailing_party"] = prevailing_party
        return info


# ---------------------------------------------------------------------------
# DamagesCalculator (Main Orchestrator)
# ---------------------------------------------------------------------------

class DamagesCalculator:
    """
    Main orchestrator for damages calculation across all case lanes.

    Integrates DamageItem computation, DefendantAllocation,
    PrejudgmentInterestCalculator, and StatutoryMultiplierEngine.
    """

    VERSION = "1.0.0"

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or _DB_PATH
        self._interest_calc = PrejudgmentInterestCalculator()
        self._multiplier_engine = StatutoryMultiplierEngine()
        self._items: List[DamageItem] = []
        self._allocations: List[DefendantAllocation] = []
        self._calculation_count: int = 0
        self._initialized = False

    def _ensure_db(self) -> None:
        """Initialise database tables on first use."""
        if self._initialized:
            return
        if not self._db_path.exists():
            logger.warning("DB not found at %s — running in memory-only mode", self._db_path)
            self._initialized = True
            return
        try:
            conn = _connect(self._db_path)
            _ensure_tables(conn)
            conn.close()
            self._initialized = True
        except sqlite3.Error as exc:
            logger.error("DB init failed: %s", exc)
            self._initialized = True

    def _build_items_for_lane(self, lane: str) -> List[DamageItem]:
        """Build DamageItem objects from lane templates."""
        templates = _ALL_LANE_DAMAGES.get(lane, [])
        items: List[DamageItem] = []

        for tmpl in templates:
            item = DamageItem(
                category=tmpl["category"],
                subcategory=tmpl.get("subcategory", ""),
                description=tmpl.get("description", ""),
                amount_low=tmpl.get("amount_low", 0.0),
                amount_mid=tmpl.get("amount_mid", 0.0),
                amount_high=tmpl.get("amount_high", 0.0),
                evidence_refs=tmpl.get("evidence_refs", []),
                statute_basis=tmpl.get("statute_basis", ""),
                lane=lane,
                calculation_method=tmpl.get("calculation_method", CalculationMethod.ESTIMATED.value),
                confidence=tmpl.get("confidence", 50.0),
            )
            relevant_defendants = [
                d.name for d in DEFENDANTS if lane in d.lanes
            ]
            item.defendants = relevant_defendants
            items.append(item)

        return items

    # -- Lane-Level Calculation --------------------------------------------

    def calculate_lane_damages(self, lane: str) -> LaneDamagesSummary:
        """Calculate full damages for a single case lane."""
        self._ensure_db()

        items = self._build_items_for_lane(lane)

        summary = LaneDamagesSummary(
            lane=lane,
            lane_label=LANE_LABELS.get(lane, f"Lane {lane}"),
            items=items,
            total_low=sum(i.amount_low for i in items),
            total_mid=sum(i.amount_mid for i in items),
            total_high=sum(i.amount_high for i in items),
            item_count=len(items),
        )

        cat_totals: Dict[str, float] = defaultdict(float)
        for item in items:
            cat_totals[item.category] += item.amount_mid
        summary.categories = dict(cat_totals)

        self._items.extend(items)
        self._calculation_count += 1

        return summary

    def calculate_all_lanes(self) -> Dict[str, LaneDamagesSummary]:
        """Calculate damages for every lane."""
        results: Dict[str, LaneDamagesSummary] = {}
        for lane in LANE_LABELS:
            results[lane] = self.calculate_lane_damages(lane)
        return results

    # -- Per-Defendant Allocation ------------------------------------------

    def calculate_per_defendant(
        self,
        defendants: Optional[List[Defendant]] = None,
    ) -> List[DefendantAllocation]:
        """Allocate damages across defendants with joint/several analysis."""
        self._ensure_db()

        if defendants is None:
            defendants = DEFENDANTS

        if not self._items:
            self.calculate_all_lanes()

        allocations: List[DefendantAllocation] = []

        for defendant in defendants:
            relevant_items = [
                item for item in self._items
                if item.lane in defendant.lanes
            ]

            alloc = DefendantAllocation(
                defendant_name=defendant.name,
                defendant_role=defendant.role,
                joint_several=defendant.joint_several,
                percentage_liability=defendant.percentage_liability,
                allocated_items=relevant_items,
            )
            alloc.calculate_totals()
            allocations.append(alloc)

        self._allocations = allocations
        self._save_allocations(allocations)
        return allocations

    # -- Prayer for Relief -------------------------------------------------

    def generate_prayer_for_relief(
        self,
        lane: str,
        style: str = "moderate",
    ) -> str:
        """Generate formatted prayer for relief with damage ranges."""
        summary = self.calculate_lane_damages(lane)

        if style == "aggressive":
            amount = summary.total_high
        elif style == "conservative":
            amount = summary.total_low
        else:
            amount = summary.total_mid

        case_number = LANE_CASE_NUMBERS.get(lane, "")
        label = LANE_LABELS.get(lane, "")

        lines = [
            "PRAYER FOR RELIEF",
            "=" * 40,
            "",
            f"Case: {label} — {case_number}",
            "",
            "WHEREFORE, Plaintiff Andrew James Pigors respectfully requests "
            "that this Honorable Court enter judgment in his favor and against "
            "Defendants, jointly and severally, as follows:",
            "",
        ]

        for i, item in enumerate(summary.items, 1):
            if style == "aggressive":
                amt = item.amount_high
            elif style == "conservative":
                amt = item.amount_low
            else:
                amt = item.amount_mid

            lines.append(
                f"  {i}. {item.description}: ${amt:,.2f}"
            )
            if item.statute_basis:
                lines.append(f"     (Pursuant to {item.statute_basis})")
            lines.append("")

        lines.extend([
            f"  TOTAL REQUESTED: ${amount:,.2f}",
            "",
            "  Plus prejudgment interest pursuant to MCL 600.6013 from the "
            "date of filing;",
            "",
            "  Plus costs and attorney fees as allowed by law;",
            "",
            "  Plus such other and further relief as this Court deems just "
            "and equitable.",
            "",
            "Respectfully submitted,",
            "",
            "________________________________",
            f"{_PLAINTIFF}, Pro Se",
        ])

        return "\n".join(lines)

    # -- Comprehensive Report ----------------------------------------------

    def generate_damages_report(self) -> Dict[str, Any]:
        """Generate comprehensive damages report across all lanes."""
        self._ensure_db()

        lane_summaries = self.calculate_all_lanes()
        allocations = self.calculate_per_defendant()

        total_low = sum(s.total_low for s in lane_summaries.values())
        total_mid = sum(s.total_mid for s in lane_summaries.values())
        total_high = sum(s.total_high for s in lane_summaries.values())

        interest_on_mid = self._interest_calc.calculate(
            total_mid,
            date(2024, 3, 15),
            date.today(),
        )

        report: Dict[str, Any] = {
            "report_id": str(uuid.uuid4())[:12],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "case_context": {
                "plaintiff": _PLAINTIFF,
                "defendant": _DEFENDANT,
                "child": _CHILD_INITIALS,
                "judge": _JUDGE,
                "defendant_count": len(DEFENDANTS),
            },
            "total_low": round(total_low, 2),
            "total_mid": round(total_mid, 2),
            "total_high": round(total_high, 2),
            "prejudgment_interest": interest_on_mid,
            "total_with_interest_mid": round(
                total_mid + interest_on_mid["interest"], 2
            ),
            "lane_summaries": {
                lane: summary.to_dict()
                for lane, summary in lane_summaries.items()
            },
            "defendant_allocations": [a.to_dict() for a in allocations],
            "defendant_count": len(DEFENDANTS),
            "item_count": sum(s.item_count for s in lane_summaries.values()),
        }

        self._save_report(report)
        return report

    # -- Persistence -------------------------------------------------------

    def _save_allocations(self, allocations: List[DefendantAllocation]) -> None:
        """Persist defendant allocations to the database."""
        if not self._db_path.exists():
            return
        try:
            conn = _connect(self._db_path)
            _ensure_tables(conn)
            now = datetime.now(timezone.utc).isoformat()
            rows = []
            for alloc in allocations:
                rows.append((
                    alloc.allocation_id,
                    alloc.defendant_name,
                    alloc.defendant_role,
                    1 if alloc.joint_several else 0,
                    alloc.percentage_liability,
                    alloc.total_low,
                    alloc.total_mid,
                    alloc.total_high,
                    json.dumps([i.lane for i in alloc.allocated_items]),
                    json.dumps([i.to_dict() for i in alloc.allocated_items[:5]]),
                    now, now,
                ))
            conn.executemany(
                "INSERT OR REPLACE INTO defendant_allocations "
                "(id, defendant_name, defendant_role, joint_several, "
                "percentage_liability, total_low, total_mid, total_high, "
                "lanes_json, items_json, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                rows,
            )
            conn.commit()
            conn.close()
        except sqlite3.Error as exc:
            logger.error("Error saving allocations: %s", exc)

    def _save_report(self, report: Dict[str, Any]) -> None:
        """Persist individual damage items to the database."""
        if not self._db_path.exists():
            return
        try:
            conn = _connect(self._db_path)
            _ensure_tables(conn)
            now = datetime.now(timezone.utc).isoformat()
            rows = []
            for item in self._items:
                rows.append((
                    item.item_id,
                    item.category,
                    item.subcategory,
                    item.description,
                    item.amount_low,
                    item.amount_mid,
                    item.amount_high,
                    json.dumps(item.defendants),
                    json.dumps(item.evidence_refs),
                    item.statute_basis,
                    item.lane,
                    item.calculation_method,
                    item.confidence,
                    item.multiplier_applied,
                    item.interest_amount,
                    now, now,
                ))
            conn.executemany(
                "INSERT OR REPLACE INTO damages_items "
                "(id, category, subcategory, description, amount_low, "
                "amount_mid, amount_high, defendants_json, evidence_refs_json, "
                "statute_basis, lane, calculation_method, confidence, "
                "multiplier_applied, interest_amount, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                rows,
            )
            conn.commit()
            conn.close()
        except sqlite3.Error as exc:
            logger.error("Error saving damage items: %s", exc)

    # -- Statistics ---------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Return engine statistics."""
        total_low = sum(i.amount_low for i in self._items)
        total_mid = sum(i.amount_mid for i in self._items)
        total_high = sum(i.amount_high for i in self._items)

        lanes_with_damages = {i.lane for i in self._items if i.amount_mid > 0}
        categories_used = {i.category for i in self._items}

        return {
            "engine": "DamagesCalculator",
            "version": self.VERSION,
            "db_path": str(self._db_path),
            "db_exists": self._db_path.exists(),
            "calculation_count": self._calculation_count,
            "total_items": len(self._items),
            "total_low": round(total_low, 2),
            "total_mid": round(total_mid, 2),
            "total_high": round(total_high, 2),
            "lanes_with_damages": sorted(lanes_with_damages),
            "categories_used": sorted(categories_used),
            "defendant_count": len(DEFENDANTS),
            "allocations_computed": len(self._allocations),
            "interest_rate": _DEFAULT_INTEREST_RATE,
            "case_context": {
                "plaintiff": _PLAINTIFF,
                "defendant": _DEFENDANT,
                "child": _CHILD_INITIALS,
                "judge": _JUDGE,
            },
        }

    def generate_text_summary(self) -> str:
        """Generate human-readable damages summary."""
        if not self._items:
            self.calculate_all_lanes()

        stats = self.get_stats()
        lines = [
            "DAMAGES CALCULATOR — SUMMARY REPORT",
            "=" * 50,
            f"Plaintiff: {_PLAINTIFF}",
            f"Defendants: {len(DEFENDANTS)}",
            "",
            f"Total Damages (Low):  ${stats['total_low']:>14,.2f}",
            f"Total Damages (Mid):  ${stats['total_mid']:>14,.2f}",
            f"Total Damages (High): ${stats['total_high']:>14,.2f}",
            "",
            "PER-LANE BREAKDOWN:",
        ]

        for lane in sorted(LANE_LABELS.keys()):
            lane_items = [i for i in self._items if i.lane == lane]
            if lane_items:
                lane_mid = sum(i.amount_mid for i in lane_items)
                lines.append(
                    f"  Lane {lane} ({LANE_LABELS[lane]}): "
                    f"${lane_mid:>12,.2f}"
                )

        lines.append("")
        lines.append("TOP DEFENDANTS BY ALLOCATION:")
        if self._allocations:
            sorted_allocs = sorted(
                self._allocations, key=lambda a: a.total_mid, reverse=True
            )
            for alloc in sorted_allocs[:10]:
                lines.append(
                    f"  {alloc.defendant_name}: "
                    f"${alloc.total_mid:>12,.2f} "
                    f"({alloc.percentage_liability:.0f}%)"
                )

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# __main__ demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")

    logging.basicConfig(level=logging.INFO, format="%(name)s %(levelname)s: %(message)s")

    print("=" * 60)
    print("DamagesCalculator — Demo")
    print("=" * 60)

    calc = DamagesCalculator()

    # Calculate all lanes
    lane_results = calc.calculate_all_lanes()
    for lane, summary in lane_results.items():
        if summary.item_count > 0:
            print(
                f"\nLane {lane} ({summary.lane_label}): "
                f"${summary.total_low:,.0f} – ${summary.total_high:,.0f} "
                f"(mid: ${summary.total_mid:,.0f}, {summary.item_count} items)"
            )

    # Per-defendant allocation
    print(f"\n{'─' * 60}")
    print("DEFENDANT ALLOCATIONS:")
    allocations = calc.calculate_per_defendant()
    for alloc in sorted(allocations, key=lambda a: a.total_mid, reverse=True):
        if alloc.total_mid > 0:
            print(
                f"  {alloc.defendant_name}: "
                f"${alloc.total_mid:,.0f} "
                f"({'J&S' if alloc.joint_several else 'Several'}, "
                f"{alloc.percentage_liability:.0f}%)"
            )

    # Prejudgment interest
    print(f"\n{'─' * 60}")
    pic = PrejudgmentInterestCalculator()
    interest = pic.calculate(500_000.0, date(2024, 3, 15), date.today())
    print(f"Prejudgment Interest on $500K: ${interest['interest']:,.2f}")
    print(f"  Rate: {interest['rate']*100:.2f}%, Days: {interest['days']}, "
          f"Method: {interest['method']}")

    # Treble damages demo
    sme = StatutoryMultiplierEngine()
    treble = sme.apply_treble_damages(100_000.0, "MCL 37.2801")
    print(f"\nTreble Damages: ${treble['base']:,.0f} × 3 = ${treble['trebled']:,.0f}")

    # Fee shifting
    fees = sme.apply_1983_fees(500_000.0, hours_spent=200.0)
    print(f"§1988 Fees: {fees['hours']}h × ${fees['hourly_rate']}/h = "
          f"${fees['adjusted_fees']:,.0f} (pro se adjusted)")

    # Prayer for relief
    print(f"\n{'─' * 60}")
    prayer = calc.generate_prayer_for_relief("A", style="moderate")
    print(prayer[:800])

    # Stats
    print(f"\n{'─' * 60}")
    stats = calc.get_stats()
    for key, val in stats.items():
        if key != "case_context":
            print(f"  {key}: {val}")

    # Full report
    report = calc.generate_damages_report()
    print(f"\nFull Report: {report['item_count']} items, "
          f"${report['total_mid']:,.0f} total (mid)")

    print(f"\n{calc.generate_text_summary()}")
    print("\nDone.")
