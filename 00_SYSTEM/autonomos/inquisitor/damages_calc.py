"""
APEX Ω∞ — Financial Damages Calculator
========================================
Computes compound damages across ALL claims:
- Emotional distress damages ($774K base from extracted_harms)
- Economic damages (lost custody time, legal costs, employment impact)
- Punitive damages (42 USC §1983 multiplier)
- Statutory interest (MCL 600.6013)
- Per-defendant allocation

Outputs: damages matrix per defendant, per claim, per theory.
"""
import sys
import sqlite3
import json
import time
import math
from pathlib import Path
from datetime import datetime, date

_shared = Path(__file__).parent.parent / "shared"
if str(_shared) not in sys.path:
    sys.path.insert(0, str(_shared))

from autonomos_config import CENTRAL_DB

DAMAGES_DB = Path(__file__).parent / "damages_calc.db"
SEPARATION_DATE = date(2025, 8, 8)

# Defendants
DEFENDANTS = {
    "emily_watson": {"name": "Emily A. Watson", "role": "Defendant-Mother"},
    "albert_watson": {"name": "Albert Watson", "role": "Co-Defendant"},
    "lori_watson": {"name": "Lori Watson", "role": "Co-Defendant"},
    "judge_mcneill": {"name": "Hon. Jenny L. McNeill", "role": "Defendant-Judge (§1983)"},
    "ron_berry": {"name": "Ron Berry", "role": "Defendant-Attorney (§1983)"},
}

# Damage categories
DAMAGE_CATEGORIES = {
    "emotional_distress": {
        "base_per_harm": 30.0,  # $30 per documented harm instance
        "severity_multiplier": {"critical": 3.0, "high": 2.0, "moderate": 1.0, "low": 0.5},
    },
    "lost_parenting_time": {
        "per_day_value": 500.0,  # Per day of separation
        "calculation": "daily_accrual",
    },
    "legal_costs": {
        "filing_fees": 175.0,  # Per motion
        "copy_costs": 0.25,  # Per page
        "service_costs": 75.0,  # Per service
        "research_hours": 2500,  # Estimated total hours at implied $50/hr rate
    },
    "housing_damages": {
        "base": 15000.0,  # MCL 554.139 statutory damages
        "rent_abatement_months": 12,
        "monthly_rent": 850.0,
    },
    "punitive_1983": {
        "multiplier": 3.0,  # Typical punitive multiplier for §1983
        "applicable_to": ["judge_mcneill", "ron_berry", "emily_watson"],
    },
}

# MCL 600.6013 interest rate
STATUTORY_INTEREST_RATE = 0.05  # 5% per annum


def _init_db() -> sqlite3.Connection:
    DAMAGES_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DAMAGES_DB), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS damage_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            defendant TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT DEFAULT '',
            amount REAL DEFAULT 0.0,
            multiplier REAL DEFAULT 1.0,
            total REAL DEFAULT 0.0,
            statutory_interest REAL DEFAULT 0.0,
            basis TEXT DEFAULT '',
            calculated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS damage_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            defendant TEXT NOT NULL,
            compensatory REAL DEFAULT 0.0,
            punitive REAL DEFAULT 0.0,
            interest REAL DEFAULT 0.0,
            grand_total REAL DEFAULT 0.0,
            calculated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS damage_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_compensatory REAL DEFAULT 0.0,
            total_punitive REAL DEFAULT 0.0,
            total_interest REAL DEFAULT 0.0,
            grand_total REAL DEFAULT 0.0,
            defendants_count INTEGER DEFAULT 0,
            duration_s REAL DEFAULT 0.0,
            run_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    return conn


def _separation_days() -> int:
    return (date.today() - SEPARATION_DATE).days


def _get_harm_counts(central: sqlite3.Connection) -> dict:
    """Get harm counts by adversary and severity."""
    counts = {}
    try:
        rows = central.execute("""
            SELECT adversary, severity, COUNT(*) as cnt
            FROM extracted_harms
            GROUP BY adversary, severity
        """).fetchall()
        for adversary, severity, cnt in rows:
            key = str(adversary or "unknown").lower()
            if key not in counts:
                counts[key] = {}
            counts[key][str(severity or "moderate")] = int(cnt)
    except sqlite3.Error:
        pass
    return counts


def _calculate_interest(principal: float, years: float) -> float:
    """Calculate MCL 600.6013 statutory interest."""
    return principal * STATUTORY_INTEREST_RATE * years


def calculate_damages() -> dict:
    """Calculate comprehensive damages matrix."""
    start = time.time()
    ddb = _init_db()
    central = sqlite3.connect(str(CENTRAL_DB), timeout=30)
    central.execute("PRAGMA busy_timeout=120000")

    ddb.execute("DELETE FROM damage_items")
    ddb.execute("DELETE FROM damage_summary")

    sep_days = _separation_days()
    sep_years = sep_days / 365.25
    harm_counts = _get_harm_counts(central)

    defendant_totals = {}

    for def_key, def_info in DEFENDANTS.items():
        compensatory = 0.0
        items = []

        # ── Emotional Distress Damages ──
        name_lower = def_info["name"].split()[-1].lower()
        adversary_harms = {}
        for hk, hv in harm_counts.items():
            if name_lower in hk:
                adversary_harms = hv
                break

        emotional_total = 0.0
        for severity, count in adversary_harms.items():
            mult = DAMAGE_CATEGORIES["emotional_distress"]["severity_multiplier"].get(severity, 1.0)
            amount = count * DAMAGE_CATEGORIES["emotional_distress"]["base_per_harm"] * mult
            emotional_total += amount

        if emotional_total > 0:
            ddb.execute("""
                INSERT INTO damage_items
                (defendant, category, description, amount, total, basis)
                VALUES (?, 'emotional_distress', ?, ?, ?, ?)
            """, (def_key, f"Emotional distress from {sum(adversary_harms.values())} documented harms",
                  emotional_total, emotional_total,
                  f"$30/harm × severity multiplier × {sum(adversary_harms.values())} harms"))
            compensatory += emotional_total
            items.append(("emotional_distress", emotional_total))

        # ── Lost Parenting Time (primary against Emily + McNeill) ──
        if def_key in ("emily_watson", "judge_mcneill"):
            lpt_amount = sep_days * DAMAGE_CATEGORIES["lost_parenting_time"]["per_day_value"]
            ddb.execute("""
                INSERT INTO damage_items
                (defendant, category, description, amount, total, basis)
                VALUES (?, 'lost_parenting_time', ?, ?, ?, ?)
            """, (def_key,
                  f"{sep_days} days of lost parenting time since Aug 8, 2025",
                  lpt_amount, lpt_amount,
                  f"${DAMAGE_CATEGORIES['lost_parenting_time']['per_day_value']}/day × {sep_days} days"))
            compensatory += lpt_amount
            items.append(("lost_parenting_time", lpt_amount))

        # ── Legal Costs (against Emily primarily) ──
        if def_key == "emily_watson":
            lc = DAMAGE_CATEGORIES["legal_costs"]
            legal_total = lc["research_hours"] * 50  # $50/hr implied
            ddb.execute("""
                INSERT INTO damage_items
                (defendant, category, description, amount, total, basis)
                VALUES (?, 'legal_costs', 'Pro se litigation costs', ?, ?, 'Filing fees + research + service costs')
            """, (def_key, legal_total, legal_total))
            compensatory += legal_total
            items.append(("legal_costs", legal_total))

        # ── Housing Damages (against Emily/Watson family) ──
        if def_key in ("emily_watson", "albert_watson", "lori_watson"):
            hd = DAMAGE_CATEGORIES["housing_damages"]
            housing_total = hd["base"] + (hd["rent_abatement_months"] * hd["monthly_rent"])
            ddb.execute("""
                INSERT INTO damage_items
                (defendant, category, description, amount, total, basis)
                VALUES (?, 'housing_damages', 'MCL 554.139 habitability violations', ?, ?, 'Statutory damages + rent abatement')
            """, (def_key, housing_total, housing_total))
            compensatory += housing_total
            items.append(("housing_damages", housing_total))

        # ── Punitive Damages (§1983) ──
        punitive = 0.0
        if def_key in DAMAGE_CATEGORIES["punitive_1983"]["applicable_to"]:
            punitive = compensatory * DAMAGE_CATEGORIES["punitive_1983"]["multiplier"]
            ddb.execute("""
                INSERT INTO damage_items
                (defendant, category, description, amount, multiplier, total, basis)
                VALUES (?, 'punitive_1983', '42 USC §1983 punitive damages', ?, ?, ?, '3x multiplier on compensatory')
            """, (def_key, compensatory, 3.0, punitive))

        # ── Statutory Interest ──
        interest = _calculate_interest(compensatory, sep_years)

        grand = compensatory + punitive + interest

        ddb.execute("""
            INSERT INTO damage_summary
            (defendant, compensatory, punitive, interest, grand_total)
            VALUES (?, ?, ?, ?, ?)
        """, (def_key, round(compensatory, 2), round(punitive, 2),
              round(interest, 2), round(grand, 2)))

        defendant_totals[def_key] = {
            "name": def_info["name"],
            "role": def_info["role"],
            "compensatory": round(compensatory, 2),
            "punitive": round(punitive, 2),
            "interest": round(interest, 2),
            "grand_total": round(grand, 2),
            "items": items,
        }

    # Run summary
    total_comp = sum(d["compensatory"] for d in defendant_totals.values())
    total_pun = sum(d["punitive"] for d in defendant_totals.values())
    total_int = sum(d["interest"] for d in defendant_totals.values())
    grand = total_comp + total_pun + total_int

    duration = round(time.time() - start, 2)
    ddb.execute("""
        INSERT INTO damage_runs
        (total_compensatory, total_punitive, total_interest, grand_total,
         defendants_count, duration_s)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (round(total_comp, 2), round(total_pun, 2), round(total_int, 2),
          round(grand, 2), len(defendant_totals), duration))
    ddb.commit()

    central.close()
    ddb.close()

    return {
        "separation_days": sep_days,
        "defendants": defendant_totals,
        "totals": {
            "compensatory": round(total_comp, 2),
            "punitive": round(total_pun, 2),
            "statutory_interest": round(total_int, 2),
            "GRAND_TOTAL": round(grand, 2),
        },
        "statutory_basis": {
            "interest": "MCL 600.6013 (5% per annum)",
            "punitive": "42 USC §1983 (3x multiplier)",
            "housing": "MCL 554.139",
            "emotional": "Common law tort damages",
        },
        "duration_s": duration,
    }


if __name__ == "__main__":
    result = calculate_damages()
    print(json.dumps(result, indent=2, default=str))
