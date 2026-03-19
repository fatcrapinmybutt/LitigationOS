#!/usr/bin/env python3
"""
MBP LitigationOS -- Deadline Calculator Skill
===============================================
Calculate procedural deadlines from Michigan court rules.
Includes common MCR time periods and calendar computation.
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent if 'skills' in str(Path(__file__)) else Path(__file__).resolve().parent))
try:
    from cycle_method import cycle_json, cycle_print
except ImportError:
    cycle_json = lambda obj, **kw: print(json.dumps(obj, default=str))
    cycle_print = print

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)

# ── Michigan Court Rule Deadline References ───────────────────────────
# Standard time periods from MCR and MCL

DEADLINE_RULES = {
    "appeal_of_right": {
        "days": 21,
        "rule": "MCR 7.204(A)(1)",
        "description": "Claim of appeal must be filed within 21 days of entry of the order being appealed.",
        "calendar_type": "calendar",
    },
    "appeal_late_application": {
        "days": 182,
        "rule": "MCR 7.205(F)(3)",
        "description": "Application for late appeal within 6 months of entry of judgment or order.",
        "calendar_type": "calendar",
    },
    "motion_response": {
        "days": 14,
        "rule": "MCR 2.119(C)(1)",
        "description": "Response to motion must be filed within 14 days after service.",
        "calendar_type": "calendar",
    },
    "motion_reply": {
        "days": 7,
        "rule": "MCR 2.119(C)(2)",
        "description": "Reply brief may be filed within 7 days after service of response.",
        "calendar_type": "calendar",
    },
    "motion_hearing_notice": {
        "days": 9,
        "rule": "MCR 2.119(C)(1)",
        "description": "Motion must be served at least 9 days before hearing date.",
        "calendar_type": "calendar",
    },
    "answer_complaint": {
        "days": 21,
        "rule": "MCR 2.108(A)(1)",
        "description": "Answer to complaint within 21 days after service.",
        "calendar_type": "calendar",
    },
    "answer_complaint_mail": {
        "days": 28,
        "rule": "MCR 2.108(A)(2)",
        "description": "Answer to complaint if served by mail (21 + 7 days).",
        "calendar_type": "calendar",
    },
    "discovery_response": {
        "days": 28,
        "rule": "MCR 2.309(B)(2)",
        "description": "Response to interrogatories within 28 days after service.",
        "calendar_type": "calendar",
    },
    "discovery_request_to_produce": {
        "days": 28,
        "rule": "MCR 2.310(B)(2)",
        "description": "Response to request for production within 28 days.",
        "calendar_type": "calendar",
    },
    "discovery_admissions": {
        "days": 28,
        "rule": "MCR 2.312(B)(1)",
        "description": "Response to request for admissions within 28 days (deemed admitted if no response).",
        "calendar_type": "calendar",
    },
    "disqualification_motion": {
        "days": 14,
        "rule": "MCR 2.003(D)(1)",
        "description": "Motion for disqualification within 14 days of discovering grounds.",
        "calendar_type": "calendar",
    },
    "foc_objection": {
        "days": 21,
        "rule": "MCR 3.218(D)",
        "description": "Objection to FOC recommendation within 21 days of service.",
        "calendar_type": "calendar",
    },
    "ppo_hearing_request": {
        "days": 14,
        "rule": "MCL 600.2950(12)",
        "description": "Request for hearing to terminate/modify PPO within 14 days.",
        "calendar_type": "calendar",
    },
    "coa_brief_appellant": {
        "days": 56,
        "rule": "MCR 7.212(A)(1)",
        "description": "Appellant's brief due within 56 days after claim of appeal filed.",
        "calendar_type": "calendar",
    },
    "coa_brief_appellee": {
        "days": 35,
        "rule": "MCR 7.212(A)(2)",
        "description": "Appellee's brief due within 35 days after appellant's brief is served.",
        "calendar_type": "calendar",
    },
    "coa_reply_brief": {
        "days": 21,
        "rule": "MCR 7.212(A)(3)",
        "description": "Appellant's reply brief due within 21 days after appellee's brief.",
        "calendar_type": "calendar",
    },
    "reconsideration": {
        "days": 21,
        "rule": "MCR 2.119(F)(1)",
        "description": "Motion for reconsideration within 21 days after entry of order.",
        "calendar_type": "calendar",
    },
    "new_trial": {
        "days": 21,
        "rule": "MCR 2.611(B)",
        "description": "Motion for new trial within 21 days after entry of judgment.",
        "calendar_type": "calendar",
    },
    "relief_from_judgment": {
        "days": 365,
        "rule": "MCR 2.612(C)(1)",
        "description": "Motion for relief from judgment within 1 year (for subrules a-c).",
        "calendar_type": "calendar",
    },
    "service_by_mail_extension": {
        "days": 7,
        "rule": "MCR 2.107(C)(3)",
        "description": "Additional 7 days when service is by mail.",
        "calendar_type": "calendar",
    },
    "contempt_show_cause": {
        "days": 14,
        "rule": "MCR 3.606(A)",
        "description": "Show cause order returnable not less than 14 days after service.",
        "calendar_type": "calendar",
    },
}


def _get_db() -> Optional[sqlite3.Connection]:
    """Get read-only DB connection."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA query_only=ON")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        return None


def calculate_deadline(deadline_type: str,
                       trigger_date: str,
                       mail_service: bool = False) -> Dict:
    """
    Calculate a specific deadline.

    deadline_type: key from DEADLINE_RULES
    trigger_date: ISO format date string (YYYY-MM-DD)
    mail_service: if True, adds 7 days per MCR 2.107(C)(3)

    Returns: {deadline_type, trigger_date, due_date, days, rule, description, mail_extension}
    """
    result = {
        "deadline_type": deadline_type,
        "trigger_date": trigger_date,
        "due_date": "",
        "days": 0,
        "rule": "",
        "description": "",
        "mail_extension": mail_service,
        "warning": "",
    }

    try:
        rule_info = DEADLINE_RULES.get(deadline_type)
        if not rule_info:
            result["warning"] = f"Unknown deadline type: {deadline_type}. Available: {', '.join(DEADLINE_RULES.keys())}"
            return result

        result["days"] = rule_info["days"]
        result["rule"] = rule_info["rule"]
        result["description"] = rule_info["description"]

        trigger = datetime.strptime(trigger_date, "%Y-%m-%d")
        days = rule_info["days"]

        if mail_service:
            days += 7
            result["days"] = days
            result["description"] += " (+ 7 days for mail service per MCR 2.107(C)(3))"

        due = trigger + timedelta(days=days)

        # Check if due date falls on weekend
        if due.weekday() == 5:  # Saturday
            due += timedelta(days=2)
            result["warning"] = "Due date fell on Saturday; extended to Monday per MCR 1.108(1)."
        elif due.weekday() == 6:  # Sunday
            due += timedelta(days=1)
            result["warning"] = "Due date fell on Sunday; extended to Monday per MCR 1.108(1)."

        result["due_date"] = due.strftime("%Y-%m-%d")

        # Check if past due
        if due.date() < datetime.now().date():
            days_overdue = (datetime.now().date() - due.date()).days
            result["warning"] = (result.get("warning", "") +
                                 f" WARNING: This deadline is {days_overdue} days OVERDUE.").strip()

    except ValueError:
        result["warning"] = f"Invalid date format: {trigger_date}. Use YYYY-MM-DD."
    except Exception as e:
        result["warning"] = f"Calculation error: {str(e)[:100]}"

    return result


def get_all_deadlines_from_db() -> List[Dict]:
    """Get all tracked deadlines from the database."""
    results = []
    try:
        conn = _get_db()
        if not conn:
            return results

        rows = conn.execute(
            "SELECT deadline_id, case_id, title, due_date_iso, basis, "
            "basis_authority, risk_if_missed, status "
            "FROM deadlines "
            "ORDER BY due_date_iso ASC"
        ).fetchall()

        for row in rows:
            entry = {
                "deadline_id": row["deadline_id"] or "",
                "case_id": row["case_id"] or "",
                "title": row["title"] or "",
                "due_date": row["due_date_iso"] or "",
                "basis": row["basis"] or "",
                "authority": row["basis_authority"] or "",
                "risk": row["risk_if_missed"] or "",
                "status": row["status"] or "",
            }

            # Check if overdue
            try:
                if entry["due_date"] and entry["status"] not in ("satisfied",):
                    due = datetime.strptime(entry["due_date"][:10], "%Y-%m-%d")
                    if due.date() < datetime.now().date():
                        entry["overdue"] = True
                        entry["days_overdue"] = (datetime.now().date() - due.date()).days
                    else:
                        entry["overdue"] = False
                        entry["days_until"] = (due.date() - datetime.now().date()).days
            except Exception:
                pass

            results.append(entry)

        conn.close()
    except Exception:
        pass

    return results


def get_upcoming_deadlines(days_ahead: int = 30) -> List[Dict]:
    """Get deadlines within N days from now."""
    try:
        all_deadlines = get_all_deadlines_from_db()
        cutoff = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        today = datetime.now().strftime("%Y-%m-%d")

        upcoming = [
            d for d in all_deadlines
            if d.get("due_date", "") >= today and d.get("due_date", "") <= cutoff
            and d.get("status") not in ("satisfied",)
        ]
        return upcoming
    except Exception:
        return []


def get_overdue_deadlines() -> List[Dict]:
    """Get all overdue, unsatisfied deadlines."""
    try:
        all_deadlines = get_all_deadlines_from_db()
        return [d for d in all_deadlines if d.get("overdue")]
    except Exception:
        return []


def list_deadline_types() -> List[Dict]:
    """List all known deadline types and their rules."""
    return [
        {
            "type": k,
            "days": v["days"],
            "rule": v["rule"],
            "description": v["description"],
        }
        for k, v in DEADLINE_RULES.items()
    ]


# ── CLI ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--types":
            result = list_deadline_types()
        elif sys.argv[1] == "--db":
            result = get_all_deadlines_from_db()
        elif sys.argv[1] == "--upcoming":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            result = get_upcoming_deadlines(days)
        elif sys.argv[1] == "--overdue":
            result = get_overdue_deadlines()
        elif sys.argv[1] == "--calc" and len(sys.argv) >= 4:
            dtype = sys.argv[2]
            trigger = sys.argv[3]
            mail = "--mail" in sys.argv
            result = calculate_deadline(dtype, trigger, mail)
        else:
            result = {"error": "Unknown command",
                      "usage": "python deadline_calculator.py --types | --db | --upcoming [days] | --overdue | --calc <type> <YYYY-MM-DD> [--mail]"}
    else:
        result = {
            "overdue": get_overdue_deadlines(),
            "upcoming_30": get_upcoming_deadlines(30),
        }

    cycle_json(result)
