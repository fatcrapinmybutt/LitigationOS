# -*- coding: utf-8 -*-
"""
Service Calculator Engine — LitigationOS MANBEARPIG v8.0
=========================================================
Calculate service and filing deadlines per Michigan Court Rules.

Authority:
    MCR 2.107      — Service of process
    MCR 2.119(C)(1)— Motion hearing notice (9 days + 3 if mailed)
    MCR 2.107(C)(3)— Additional 3 days for mail service
    MCR 7.204(A)(1)— 21-day claim of appeal (jurisdictional)
    MCR 7.305(C)(2)— 56-day MSC application window
    MCR 3.207(A)   — Ex parte custody orders (14-day hearing)
    MCR 3.208      — FOC 21-day objection period

Usage:
    python service_calculator.py
    python service_calculator.py --hearing-date 2026-03-15 --method mail
"""

import sys
import os
import io
import sqlite3
import json
from datetime import datetime, timedelta, date
from typing import Optional, Dict, List, Tuple

# UTF-8 fix for Windows console
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
elif sys.stdout is None or not hasattr(sys.stdout, "encoding") or sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer if sys.stdout else open(os.devnull, "w"), encoding="utf-8")

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

# ---------------------------------------------------------------------------
# Michigan Court Rule deadline definitions
# ---------------------------------------------------------------------------

SERVICE_RULES: Dict[str, Dict] = {
    "personal": {
        "rule": "MCR 2.107(C)(1)",
        "description": "Personal service — no additional days",
        "extra_days": 0,
    },
    "mail": {
        "rule": "MCR 2.107(C)(3)",
        "description": "Service by first-class mail — add 3 days",
        "extra_days": 3,
    },
    "email": {
        "rule": "MCR 2.107(C)(4)",
        "description": "Electronic service (where permitted) — add 1 day",
        "extra_days": 1,
    },
    "mifile": {
        "rule": "MCR 1.109(G)(6)(a)",
        "description": "MiFile e-service — add 1 day",
        "extra_days": 1,
    },
}

DEADLINE_RULES: Dict[str, Dict] = {
    "motion_hearing_notice": {
        "rule": "MCR 2.119(C)(1)",
        "base_days": 9,
        "description": "Motion must be served at least 9 days before hearing",
        "mail_total": 12,
    },
    "response_to_motion": {
        "rule": "MCR 2.119(C)(2)",
        "base_days": 7,
        "description": "Response to motion — 7 days before hearing (5 + answer time)",
    },
    "reply_brief": {
        "rule": "MCR 2.119(C)(2)",
        "base_days": 4,
        "description": "Reply brief — 4 days before hearing",
    },
    "claim_of_appeal": {
        "rule": "MCR 7.204(A)(1)",
        "base_days": 21,
        "description": "Claim of appeal — 21 days from order (JURISDICTIONAL)",
        "jurisdictional": True,
    },
    "msc_application": {
        "rule": "MCR 7.305(C)(2)",
        "base_days": 56,
        "description": "MSC application for leave — 56 days from COA decision",
    },
    "msc_cross_application": {
        "rule": "MCR 7.305(C)(3)",
        "base_days": 21,
        "description": "MSC cross-application — 21 days after application served",
    },
    "ex_parte_hearing": {
        "rule": "MCR 3.207(A)",
        "base_days": 14,
        "description": "Hearing after ex parte custody order — within 14 days",
    },
    "foc_objection": {
        "rule": "MCR 3.208",
        "base_days": 21,
        "description": "Objection to FOC recommendation — 21 days from service",
    },
    "discovery_response": {
        "rule": "MCR 2.309(B)(2)",
        "base_days": 28,
        "description": "Response to interrogatories — 28 days",
    },
    "ppo_appeal": {
        "rule": "MCL 600.2950(12)",
        "base_days": 14,
        "description": "Motion to modify/terminate PPO — no fixed deadline but prompt",
    },
    "reconsideration": {
        "rule": "MCR 2.119(F)(1)",
        "base_days": 21,
        "description": "Motion for reconsideration — 21 days from order",
    },
    "coa_brief": {
        "rule": "MCR 7.212(A)(1)",
        "base_days": 56,
        "description": "Appellant brief — 56 days after claim of appeal",
    },
    "coa_appellee_brief": {
        "rule": "MCR 7.212(A)(2)",
        "base_days": 35,
        "description": "Appellee brief — 35 days after appellant brief served",
    },
    "coa_reply_brief": {
        "rule": "MCR 7.212(A)(3)",
        "base_days": 21,
        "description": "Reply brief — 21 days after appellee brief served",
    },
}

# Michigan holidays (state + federal observed by courts)
MI_COURT_HOLIDAYS_2025_2026 = [
    date(2025, 1, 1), date(2025, 1, 20), date(2025, 2, 17),
    date(2025, 5, 26), date(2025, 6, 19), date(2025, 7, 4),
    date(2025, 9, 1), date(2025, 11, 27), date(2025, 11, 28),
    date(2025, 12, 24), date(2025, 12, 25), date(2025, 12, 31),
    date(2026, 1, 1), date(2026, 1, 19), date(2026, 2, 16),
    date(2026, 5, 25), date(2026, 6, 19), date(2026, 7, 3),
    date(2026, 9, 7), date(2026, 11, 26), date(2026, 11, 27),
    date(2026, 12, 24), date(2026, 12, 25), date(2026, 12, 31),
]


def _is_court_business_day(d: date) -> bool:
    """Return True if the date is a court business day in Michigan."""
    if d.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    if d in MI_COURT_HOLIDAYS_2025_2026:
        return False
    return True


def _next_business_day(d: date) -> date:
    """If d falls on weekend/holiday, advance to the next business day (MCR 1.108(1))."""
    while not _is_court_business_day(d):
        d += timedelta(days=1)
    return d


def _count_back_business_or_calendar(from_date: date, days: int, calendar: bool = True) -> date:
    """
    Count backward from a date.
    calendar=True  → subtract calendar days (MCR default for most deadlines)
    calendar=False → subtract court business days
    """
    if calendar:
        result = from_date - timedelta(days=days)
    else:
        counted = 0
        result = from_date
        while counted < days:
            result -= timedelta(days=1)
            if _is_court_business_day(result):
                counted += 1
    return result


def calculate_service_deadline(
    hearing_date: str,
    service_method: str = "mail",
    deadline_type: str = "motion_hearing_notice",
) -> Dict:
    """
    Calculate the latest date to serve a filing for a given hearing.

    Args:
        hearing_date:   ISO format date string (YYYY-MM-DD)
        service_method: personal | mail | email | mifile
        deadline_type:  Key from DEADLINE_RULES

    Returns:
        Dict with deadline details, authority, and warnings.
    """
    hearing = date.fromisoformat(hearing_date)
    method = service_method.lower()

    rule_info = DEADLINE_RULES.get(deadline_type, DEADLINE_RULES["motion_hearing_notice"])
    service_info = SERVICE_RULES.get(method, SERVICE_RULES["mail"])

    base_days = rule_info["base_days"]
    extra = service_info["extra_days"]
    total_days = base_days + extra

    serve_by = _count_back_business_or_calendar(hearing, total_days, calendar=True)
    # MCR 1.108(1): if deadline falls on non-business day, move to previous business day
    if not _is_court_business_day(serve_by):
        # For service deadlines we must serve BEFORE, so go earlier
        while not _is_court_business_day(serve_by):
            serve_by -= timedelta(days=1)

    today = date.today()
    days_remaining = (serve_by - today).days

    result = {
        "hearing_date": hearing_date,
        "service_method": method,
        "deadline_type": deadline_type,
        "base_days_required": base_days,
        "mail_extra_days": extra,
        "total_days_before_hearing": total_days,
        "serve_by_date": serve_by.isoformat(),
        "days_remaining": days_remaining,
        "authority": rule_info["rule"],
        "service_authority": service_info["rule"],
        "description": rule_info["description"],
        "is_jurisdictional": rule_info.get("jurisdictional", False),
        "warnings": [],
    }

    if days_remaining < 0:
        result["warnings"].append(f"⚠ DEADLINE PASSED {abs(days_remaining)} days ago!")
    elif days_remaining <= 3:
        result["warnings"].append(f"⚠ URGENT: Only {days_remaining} days remaining!")

    if result["is_jurisdictional"]:
        result["warnings"].append("⚠ JURISDICTIONAL DEADLINE — cannot be extended.")

    return result


def calculate_appeal_deadline(order_date: str, appeal_type: str = "claim_of_appeal") -> Dict:
    """
    Calculate appeal deadline from an order date.

    Args:
        order_date:  ISO date of the order being appealed
        appeal_type: claim_of_appeal | coa_brief | msc_application | reconsideration

    Returns:
        Dict with deadline info.
    """
    order = date.fromisoformat(order_date)
    rule_info = DEADLINE_RULES.get(appeal_type, DEADLINE_RULES["claim_of_appeal"])
    base_days = rule_info["base_days"]

    raw_deadline = order + timedelta(days=base_days)
    deadline = _next_business_day(raw_deadline)

    today = date.today()
    days_remaining = (deadline - today).days

    result = {
        "order_date": order_date,
        "appeal_type": appeal_type,
        "days_allowed": base_days,
        "deadline_date": deadline.isoformat(),
        "days_remaining": days_remaining,
        "authority": rule_info["rule"],
        "description": rule_info["description"],
        "is_jurisdictional": rule_info.get("jurisdictional", False),
        "warnings": [],
    }

    if days_remaining < 0:
        result["warnings"].append(f"⚠ DEADLINE EXPIRED {abs(days_remaining)} days ago!")
    elif days_remaining <= 5:
        result["warnings"].append(f"⚠ CRITICAL: Only {days_remaining} days remaining!")

    if result["is_jurisdictional"]:
        result["warnings"].append("⚠ JURISDICTIONAL — no extensions, no excuses. MCR 7.204(A)(1).")

    return result


def calculate_msc_deadline(coa_decision_date: str) -> Dict:
    """Calculate MSC application deadline — 56 days from COA decision per MCR 7.305(C)(2)."""
    return calculate_appeal_deadline(coa_decision_date, appeal_type="msc_application")


def days_until_deadline(deadline_date: str) -> Dict:
    """
    Simple utility: how many days until a given deadline?
    Returns dict with days, urgency level, and business days.
    """
    dl = date.fromisoformat(deadline_date)
    today = date.today()
    total = (dl - today).days

    # Count business days
    biz_days = 0
    check = today
    while check < dl:
        check += timedelta(days=1)
        if _is_court_business_day(check):
            biz_days += 1

    if total < 0:
        urgency = "EXPIRED"
    elif total <= 3:
        urgency = "CRITICAL"
    elif total <= 7:
        urgency = "URGENT"
    elif total <= 14:
        urgency = "APPROACHING"
    else:
        urgency = "NORMAL"

    return {
        "deadline_date": deadline_date,
        "calendar_days": total,
        "business_days": biz_days,
        "urgency": urgency,
        "today": today.isoformat(),
    }


def get_all_pending_deadlines() -> List[Dict]:
    """Query the deadlines table in litigation_context.db for active deadlines."""
    if not os.path.exists(DB_PATH):
        return [{"error": f"Database not found: {DB_PATH}"}]
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT * FROM deadlines WHERE date(deadline_date) >= date('now') ORDER BY deadline_date ASC"
        )
        rows = [dict(r) for r in cur.fetchall()]
    except sqlite3.OperationalError:
        rows = [{"error": "deadlines table not found or inaccessible"}]
    finally:
        conn.close()
    return rows


def list_all_rules() -> List[Dict]:
    """Return all known deadline rules for reference."""
    result = []
    for key, info in DEADLINE_RULES.items():
        result.append({
            "type": key,
            "rule": info["rule"],
            "days": info["base_days"],
            "description": info["description"],
            "jurisdictional": info.get("jurisdictional", False),
        })
    return result


def main():
    """CLI test harness."""
    print("=" * 70)
    print("SERVICE CALCULATOR ENGINE — LitigationOS MANBEARPIG v8.0")
    print("=" * 70)

    # Test 1: Motion hearing service deadline
    print("\n[TEST 1] Motion hearing service deadline (mail):")
    future_hearing = (date.today() + timedelta(days=30)).isoformat()
    result = calculate_service_deadline(future_hearing, "mail", "motion_hearing_notice")
    for k, v in result.items():
        print(f"  {k}: {v}")

    # Test 2: Appeal deadline
    print("\n[TEST 2] Claim of appeal deadline:")
    result = calculate_appeal_deadline("2025-08-08", "claim_of_appeal")
    for k, v in result.items():
        print(f"  {k}: {v}")

    # Test 3: MSC deadline
    print("\n[TEST 3] MSC application deadline:")
    result = calculate_msc_deadline("2025-12-01")
    for k, v in result.items():
        print(f"  {k}: {v}")

    # Test 4: Days until a future date
    print("\n[TEST 4] Days until deadline:")
    future = (date.today() + timedelta(days=15)).isoformat()
    result = days_until_deadline(future)
    for k, v in result.items():
        print(f"  {k}: {v}")

    # Test 5: All known rules
    print("\n[TEST 5] All Michigan deadline rules:")
    for rule in list_all_rules():
        flag = " [JURISDICTIONAL]" if rule["jurisdictional"] else ""
        print(f"  {rule['type']:30s} | {rule['rule']:20s} | {rule['days']:3d} days{flag}")

    # Test 6: Pending deadlines from DB
    print("\n[TEST 6] Pending deadlines from DB:")
    deadlines = get_all_pending_deadlines()
    if deadlines and "error" not in deadlines[0]:
        for d in deadlines[:5]:
            print(f"  {d}")
    else:
        print(f"  {deadlines}")

    print("\n✓ Service Calculator Engine — all tests complete.")


if __name__ == "__main__":
    main()
