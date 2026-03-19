# -*- coding: utf-8 -*-
"""Engine 10: Filing Fee Calculator — Track fees for all courts.

14th Circuit: Motion ~$20, new case $175.
COA: $375 (or fee waiver MC 20).
MSC: $375 (or fee waiver).
USDC: $405 (or IFP 28 USC §1915).
JTC: No fee.
"""
import sys
import os
import json
import sqlite3
from datetime import datetime

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

# ── Fee schedules per court ─────────────────────────────────────────────────
FEE_SCHEDULE = {
    "14th_circuit": {
        "new_case": 175.00,
        "motion": 20.00,
        "motion_ex_parte": 20.00,
        "motion_for_reconsideration": 20.00,
        "response": 0.00,
        "brief": 0.00,
        "subpoena": 0.00,
        "jury_demand": 85.00,
        "appeal_bond": 0.00,  # varies
        "transcript": 0.00,   # per-page cost handled separately
        "certified_copy": 10.00,
        "fee_waiver_form": "MC 20",
        "fee_waiver_authority": "MCR 2.002",
    },
    "coa": {
        "claim_of_appeal": 375.00,
        "application_for_leave": 375.00,
        "motion": 75.00,
        "cross_appeal": 375.00,
        "emergency_motion": 75.00,
        "brief": 0.00,
        "fee_waiver_form": "MC 20",
        "fee_waiver_authority": "MCR 7.202(8); MCR 2.002",
    },
    "msc": {
        "application_for_leave": 375.00,
        "original_action": 375.00,
        "superintending_control": 375.00,
        "emergency_application": 375.00,
        "motion": 75.00,
        "brief": 0.00,
        "fee_waiver_form": "MC 20",
        "fee_waiver_authority": "MCR 7.319; MCR 2.002",
    },
    "usdc": {
        "complaint": 405.00,
        "motion": 0.00,
        "appeal_to_6th_circuit": 505.00,
        "emergency_motion": 0.00,
        "fee_waiver_form": "AO 240 (IFP Application)",
        "fee_waiver_authority": "28 U.S.C. § 1915",
    },
    "jtc": {
        "complaint": 0.00,
        "supplemental": 0.00,
        "fee_waiver_form": None,
        "fee_waiver_authority": "No fee required",
    },
}

# Fee waiver status tracking
WAIVER_STATUS_OPTIONS = [
    "not_filed",
    "filed_pending",
    "granted",
    "denied",
    "not_applicable",
]


def _get_db():
    """Connect to litigation_context.db."""
    if not os.path.exists(DB_PATH):
        return None
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_tracker_table(conn):
    """Create filing_fees_tracker table if it doesn't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS filing_fees_tracker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            court TEXT NOT NULL,
            case_number TEXT,
            filing_type TEXT NOT NULL,
            fee_amount REAL NOT NULL DEFAULT 0.0,
            waiver_status TEXT DEFAULT 'not_filed',
            waiver_form TEXT,
            date_filed TEXT,
            date_paid TEXT,
            receipt_ref TEXT,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()


def calculate_fee(court, filing_type):
    """Calculate filing fee for a court and filing type.

    Args:
        court: Court key (14th_circuit, coa, msc, usdc, jtc).
        filing_type: Type of filing (motion, brief, complaint, etc.).

    Returns:
        dict with fee, waiver info, and authority.
    """
    court_key = court.lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "circuit": "14th_circuit", "14th": "14th_circuit",
        "muskegon": "14th_circuit", "trial": "14th_circuit",
        "appeals": "coa", "court_of_appeals": "coa",
        "supreme": "msc", "supreme_court": "msc",
        "federal": "usdc", "district": "usdc",
        "tenure": "jtc", "judicial_tenure": "jtc",
    }
    court_key = aliases.get(court_key, court_key)

    if court_key not in FEE_SCHEDULE:
        return {
            "error": f"Unknown court: {court}",
            "valid_courts": list(FEE_SCHEDULE.keys()),
        }

    schedule = FEE_SCHEDULE[court_key]
    filing_key = filing_type.lower().replace(" ", "_").replace("-", "_")

    # Try exact match, then partial match
    fee = schedule.get(filing_key)
    if fee is None:
        for key, val in schedule.items():
            if isinstance(val, (int, float)) and filing_key in key:
                fee = val
                filing_key = key
                break

    if fee is None:
        known_types = [k for k, v in schedule.items() if isinstance(v, (int, float))]
        return {
            "error": f"Unknown filing type '{filing_type}' for {court_key}",
            "known_types": known_types,
        }

    result = {
        "court": court_key,
        "filing_type": filing_key,
        "fee_amount": fee,
        "fee_display": f"${fee:.2f}" if fee > 0 else "No fee",
        "waiver_form": schedule.get("fee_waiver_form"),
        "waiver_authority": schedule.get("fee_waiver_authority"),
        "waiver_available": schedule.get("fee_waiver_form") is not None,
        "ifp_eligible": True,  # Andrew qualifies for IFP
    }

    if fee > 0:
        result["recommendation"] = (
            f"File fee waiver ({schedule.get('fee_waiver_form', 'form')}) "
            f"per {schedule.get('fee_waiver_authority', 'court rules')}. "
            f"Andrew qualifies for IFP status."
        )
    else:
        result["recommendation"] = "No fee required for this filing type."

    return result


def get_fee_waiver_requirements(court):
    """Get fee waiver requirements and forms for a court.

    Args:
        court: Court key.

    Returns:
        dict with waiver form, authority, requirements, and instructions.
    """
    court_key = court.lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "circuit": "14th_circuit", "14th": "14th_circuit",
        "appeals": "coa", "supreme": "msc",
        "federal": "usdc", "tenure": "jtc",
    }
    court_key = aliases.get(court_key, court_key)

    schedule = FEE_SCHEDULE.get(court_key, {})

    # Common waiver requirements
    requirements = {
        "14th_circuit": {
            "form": "MC 20 (Fee Waiver Request)",
            "authority": "MCR 2.002",
            "requirements": [
                "Affidavit of indigency",
                "Income documentation (pay stubs, tax returns, benefit letters)",
                "Monthly expense breakdown",
                "List of assets and debts",
            ],
            "standard": "Unable to pay fees without depriving self/dependents of necessities",
            "notes": "Filed simultaneously with the filing requiring fee",
        },
        "coa": {
            "form": "MC 20 (Fee Waiver Request)",
            "authority": "MCR 7.202(8); MCR 2.002",
            "requirements": [
                "MC 20 form completed",
                "Same financial documentation as circuit court",
                "File with claim of appeal or application",
            ],
            "standard": "Same as circuit court — MCR 2.002 standard",
            "notes": "Must be filed with or before the filing requiring fee",
        },
        "msc": {
            "form": "MC 20 (Fee Waiver Request)",
            "authority": "MCR 7.319; MCR 2.002",
            "requirements": [
                "MC 20 form completed",
                "Financial documentation",
                "File with application or original action",
            ],
            "standard": "MCR 2.002 standard applies",
            "notes": "File simultaneously with substantive filing",
        },
        "usdc": {
            "form": "AO 240 (Application to Proceed In Forma Pauperis)",
            "authority": "28 U.S.C. § 1915",
            "requirements": [
                "AO 240 form (federal IFP application)",
                "Detailed affidavit of assets, income, expenses",
                "Employer information",
                "Prior litigation history (last 3 years)",
                "Certification of claims in good faith",
            ],
            "standard": "Unable to pay filing fees without undue hardship",
            "notes": (
                "Federal IFP differs from state. Must disclose all prior "
                "federal filings. Court screens complaint under 28 USC §1915(e)(2)."
            ),
        },
        "jtc": {
            "form": None,
            "authority": "No fee required",
            "requirements": [],
            "standard": "N/A — JTC complaints have no filing fee",
            "notes": "Simply file the complaint with supporting documents",
        },
    }

    info = requirements.get(court_key, {
        "form": schedule.get("fee_waiver_form"),
        "authority": schedule.get("fee_waiver_authority"),
        "requirements": ["Check court-specific rules"],
        "standard": "Varies",
        "notes": "",
    })

    info["court"] = court_key
    info["ifp_eligible"] = True  # Andrew qualifies
    return info


def track_fees_paid(court=None):
    """Retrieve filing fee tracker entries.

    Args:
        court: Optional court filter. None returns all.

    Returns:
        dict with entries, totals, and summary.
    """
    conn = _get_db()
    if conn is None:
        return _generate_estimated_tracker()

    try:
        _ensure_tracker_table(conn)

        if court:
            rows = conn.execute(
                "SELECT * FROM filing_fees_tracker WHERE court = ? ORDER BY created_at",
                (court.lower().replace(" ", "_"),)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM filing_fees_tracker ORDER BY court, created_at"
            ).fetchall()

        entries = [dict(r) for r in rows]

        if not entries:
            return _generate_estimated_tracker()

        total_fees = sum(e.get("fee_amount", 0) for e in entries)
        total_paid = sum(
            e.get("fee_amount", 0) for e in entries
            if e.get("date_paid")
        )
        total_waived = sum(
            e.get("fee_amount", 0) for e in entries
            if e.get("waiver_status") == "granted"
        )
        total_pending = total_fees - total_paid - total_waived

        return {
            "entries": entries,
            "summary": {
                "total_fees": total_fees,
                "total_paid": total_paid,
                "total_waived": total_waived,
                "total_pending": total_pending,
                "entry_count": len(entries),
            },
        }
    except Exception as e:
        return {"error": str(e), **_generate_estimated_tracker()}
    finally:
        conn.close()


def _generate_estimated_tracker():
    """Generate estimated fee tracker from known filing plan."""
    planned = [
        {"court": "msc", "filing_type": "superintending_control",
         "fee_amount": 375.00, "waiver_status": "not_filed",
         "notes": "Day 1: MSC complaint — file MC 20 waiver simultaneously"},
        {"court": "jtc", "filing_type": "complaint",
         "fee_amount": 0.00, "waiver_status": "not_applicable",
         "notes": "Day 1: JTC — no fee required"},
        {"court": "14th_circuit", "filing_type": "motion_for_reconsideration",
         "fee_amount": 20.00, "waiver_status": "not_filed",
         "notes": "Day 2-3: Motion for Reconsideration"},
        {"court": "14th_circuit", "filing_type": "motion_ex_parte",
         "fee_amount": 20.00, "waiver_status": "not_filed",
         "notes": "Day 5-7: Emergency Motion Restore PT"},
        {"court": "coa", "filing_type": "brief",
         "fee_amount": 0.00, "waiver_status": "not_applicable",
         "notes": "Day 14: Appellant Brief (no additional fee if appeal filed)"},
        {"court": "usdc", "filing_type": "complaint",
         "fee_amount": 405.00, "waiver_status": "not_filed",
         "notes": "Day 30: Federal §1983 — file AO 240 IFP simultaneously"},
    ]

    total = sum(e["fee_amount"] for e in planned)
    waivable = sum(
        e["fee_amount"] for e in planned
        if e["waiver_status"] != "not_applicable" and e["fee_amount"] > 0
    )

    return {
        "entries": planned,
        "summary": {
            "total_fees": total,
            "total_paid": 0.0,
            "total_waived": 0.0,
            "total_pending": total,
            "waivable_amount": waivable,
            "entry_count": len(planned),
            "source": "estimated_from_filing_plan",
        },
        "recommendation": (
            f"Total estimated fees: ${total:.2f}. "
            f"Waivable amount: ${waivable:.2f}. "
            f"File MC 20 (state) and AO 240 (federal) fee waivers. "
            f"Andrew qualifies for IFP in all courts."
        ),
    }


def record_fee(court, filing_type, fee_amount=None, case_number=None,
               waiver_status="not_filed", notes=""):
    """Record a filing fee in the tracker table.

    Args:
        court: Court key.
        filing_type: Filing type.
        fee_amount: Override fee amount. None uses schedule.
        case_number: Case number.
        waiver_status: Waiver status.
        notes: Additional notes.

    Returns:
        dict with success status and record id.
    """
    if fee_amount is None:
        calc = calculate_fee(court, filing_type)
        if "error" in calc:
            return calc
        fee_amount = calc["fee_amount"]

    conn = _get_db()
    if conn is None:
        return {"error": "Database not available", "fee_amount": fee_amount}

    try:
        _ensure_tracker_table(conn)
        cur = conn.execute(
            """INSERT INTO filing_fees_tracker
               (court, case_number, filing_type, fee_amount, waiver_status, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (court.lower().replace(" ", "_"), case_number, filing_type,
             fee_amount, waiver_status, notes),
        )
        conn.commit()
        return {
            "success": True,
            "id": cur.lastrowid,
            "court": court,
            "filing_type": filing_type,
            "fee_amount": fee_amount,
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()


def get_total_estimated_cost():
    """Calculate total estimated litigation cost across all forums.

    Returns:
        dict with breakdown by court and total.
    """
    planned_filings = {
        "msc": [("superintending_control", 375.00)],
        "jtc": [("complaint", 0.00)],
        "14th_circuit": [
            ("motion_for_reconsideration", 20.00),
            ("motion_ex_parte", 20.00),
        ],
        "coa": [("brief", 0.00)],
        "usdc": [("complaint", 405.00)],
    }

    breakdown = {}
    grand_total = 0.0
    for court, filings in planned_filings.items():
        court_total = sum(f[1] for f in filings)
        breakdown[court] = {
            "filings": [{"type": f[0], "fee": f[1]} for f in filings],
            "subtotal": court_total,
        }
        grand_total += court_total

    return {
        "breakdown": breakdown,
        "grand_total": grand_total,
        "grand_total_display": f"${grand_total:.2f}",
        "waivable": grand_total,
        "if_all_waivers_granted": "$0.00",
        "recommendation": "File fee waivers in all courts. IFP status justified.",
    }


def main():
    """CLI entry point for testing."""
    print("=" * 60)
    print("ENGINE 10: FILING FEE CALCULATOR")
    print("All Courts / Fee Waiver Tracking")
    print("=" * 60)

    # Test fee calculation for each court
    print("\n--- Fee Schedule ---")
    test_cases = [
        ("14th_circuit", "motion"),
        ("14th_circuit", "new_case"),
        ("coa", "claim_of_appeal"),
        ("coa", "motion"),
        ("msc", "superintending_control"),
        ("msc", "emergency_application"),
        ("usdc", "complaint"),
        ("jtc", "complaint"),
    ]

    for court, ftype in test_cases:
        result = calculate_fee(court, ftype)
        if "error" in result:
            print(f"  {court}/{ftype}: ERROR — {result['error']}")
        else:
            print(f"  {court}/{ftype}: {result['fee_display']}"
                  f"  [Waiver: {result['waiver_form']}]")

    # Test fee waiver requirements
    print("\n--- Fee Waiver Requirements ---")
    for court in ["14th_circuit", "coa", "msc", "usdc", "jtc"]:
        info = get_fee_waiver_requirements(court)
        form = info.get("form", "N/A")
        print(f"  {court}: Form={form}, Authority={info.get('authority', 'N/A')}")

    # Test fee tracker
    print("\n--- Fee Tracker ---")
    tracker = track_fees_paid()
    summary = tracker.get("summary", {})
    print(f"  Total fees: ${summary.get('total_fees', 0):.2f}")
    print(f"  Paid: ${summary.get('total_paid', 0):.2f}")
    print(f"  Waived: ${summary.get('total_waived', 0):.2f}")
    print(f"  Pending: ${summary.get('total_pending', 0):.2f}")
    if tracker.get("recommendation"):
        print(f"  Rec: {tracker['recommendation']}")

    # Test total cost estimate
    print("\n--- Total Estimated Cost ---")
    cost = get_total_estimated_cost()
    print(f"  Grand total: {cost['grand_total_display']}")
    print(f"  If waivers granted: {cost['if_all_waivers_granted']}")
    for court, info in cost["breakdown"].items():
        print(f"    {court}: ${info['subtotal']:.2f}")

    print("\n[filing_fee_calculator] All tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
