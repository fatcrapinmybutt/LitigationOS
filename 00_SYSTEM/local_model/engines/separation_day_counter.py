# -*- coding: utf-8 -*-
"""
Separation Day Counter Engine — LitigationOS MANBEARPIG v8.0
==============================================================
Track parent-child separation with legal significance milestones.

Separation Start: August 8, 2025
    — 5 ex parte orders entered by Judge McNeill on a single day
    — ALL parenting time suspended without notice or hearing
    — MCR 3.207(C)(2), MCL 722.27a(3) violated

Authority:
    Troxel v Granville, 530 US 57 (2000) — fundamental parental right
    MCL 722.27a — Parenting time presumption
    MCL 722.23(j) — Factor J: willingness to facilitate relationship
    Stanley v Illinois, 405 US 645 (1972) — fitness presumption
    Santosky v Kramer, 455 US 745 (1982) — clear and convincing standard

Usage:
    python separation_day_counter.py
"""

import sys
import os
import io
import sqlite3
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
elif sys.stdout is None or not hasattr(sys.stdout, "encoding") or sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer if sys.stdout else open(os.devnull, "w"), encoding="utf-8")

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

# ---------------------------------------------------------------------------
# Core separation data
# ---------------------------------------------------------------------------

SEPARATION_START = date(2025, 8, 8)

# Periods of restored contact (date_start, date_end, description)
# Currently NONE — total deprivation since Aug 8, 2025
RESTORED_CONTACT_PERIODS: List[Tuple[date, date, str]] = []

# Legal significance milestones
MILESTONES = [
    (30, "30 days",
     "Exceeds MCR 3.207(A) 14-day hearing requirement by 2x. "
     "Any reasonable court would have held a hearing."),
    (90, "90 days (3 months)",
     "Quarter-year deprivation. Attachment disruption per developmental psychology. "
     "Troxel fundamental right violated for a full season."),
    (180, "180 days (6 months)",
     "Half-year separation. Rebuttable presumption of established custodial "
     "environment change under MCL 722.27(1)(c). Severe bonding damage."),
    (365, "1 year",
     "Full year of parent-child separation without a best-interest hearing. "
     "Constitutionally intolerable under Troxel and Stanley v Illinois. "
     "Federal §1983 damages accrue substantially."),
    (500, "500 days",
     "Exceeds most civil contempt sanctions. Approaches conditions found in "
     "wrongful termination of parental rights cases. Compelling MSC/federal relief."),
    (730, "2 years",
     "Two full years. Permanent psychological damage documented in literature. "
     "Constitutes de facto termination of parental rights without due process."),
]

# Cause of separation — for filings
CAUSE_DESCRIPTION = (
    "On August 8, 2025, Judge Jenny L. McNeill entered five (5) ex parte orders "
    "simultaneously suspending all parenting time between Father and child, "
    "without prior notice to Father, without a hearing, and without any finding "
    "of imminent danger to the child as required by MCR 3.207(C)(2). "
    "No parenting time has been restored since that date."
)


def get_separation_days() -> Dict:
    """
    Calculate current separation in days, weeks, months, and years.

    Returns:
        Dict with separation metrics and milestone analysis.
    """
    today = date.today()
    total_days = (today - SEPARATION_START).days

    # Subtract any restored contact periods
    restored_days = 0
    for start, end, _desc in RESTORED_CONTACT_PERIODS:
        if start <= today:
            period_end = min(end, today)
            restored_days += (period_end - start).days

    net_separation_days = total_days - restored_days

    # Calculate human-readable duration
    years = net_separation_days // 365
    remaining = net_separation_days % 365
    months = remaining // 30
    days = remaining % 30
    weeks = net_separation_days // 7

    # Determine passed milestones
    passed = []
    next_milestone = None
    for threshold, label, significance in MILESTONES:
        if net_separation_days >= threshold:
            passed.append({
                "threshold": threshold,
                "label": label,
                "significance": significance,
                "passed_on": (SEPARATION_START + timedelta(days=threshold)).isoformat(),
            })
        elif next_milestone is None:
            next_milestone = {
                "threshold": threshold,
                "label": label,
                "days_until": threshold - net_separation_days,
                "expected_date": (SEPARATION_START + timedelta(days=threshold)).isoformat(),
            }

    return {
        "separation_start": SEPARATION_START.isoformat(),
        "current_date": today.isoformat(),
        "total_calendar_days": total_days,
        "restored_contact_days": restored_days,
        "net_separation_days": net_separation_days,
        "weeks": weeks,
        "duration_readable": f"{years}y {months}m {days}d" if years else f"{months}m {days}d",
        "duration_long": (
            f"{years} year(s), {months} month(s), and {days} day(s)"
            if years else f"{months} month(s) and {days} day(s)"
        ),
        "restored_contact_periods": len(RESTORED_CONTACT_PERIODS),
        "milestones_passed": len(passed),
        "milestone_details": passed,
        "next_milestone": next_milestone,
        "cause": CAUSE_DESCRIPTION,
    }


def get_separation_narrative() -> str:
    """
    Generate a narrative paragraph suitable for legal filings.
    """
    data = get_separation_days()
    days = data["net_separation_days"]
    duration = data["duration_long"]

    narrative = (
        f"As of {data['current_date']}, Father and child have been separated for "
        f"{days} consecutive days ({duration}) — since August 8, 2025, when "
        f"Judge McNeill entered five ex parte orders simultaneously stripping "
        f"all parenting time without notice, hearing, or a finding of imminent "
        f"danger. MCR 3.207(C)(2) required a hearing within 14 days; none was held. "
        f"This {days}-day deprivation constitutes a continuing violation of Father's "
        f"fundamental constitutional right to parent under Troxel v Granville, "
        f"530 US 57 (2000), and Stanley v Illinois, 405 US 645 (1972)."
    )

    if days >= 365:
        narrative += (
            f" The separation now exceeds one full year — a duration that is "
            f"constitutionally intolerable and approaches de facto termination "
            f"of parental rights without due process. Santosky v Kramer, "
            f"455 US 745 (1982)."
        )

    return narrative


def format_for_filing(court_type: str = "trial") -> str:
    """
    Format separation data for specific court filing types.

    Args:
        court_type: trial | coa | msc | federal

    Returns:
        Formatted text block for inclusion in the filing.
    """
    data = get_separation_days()
    days = data["net_separation_days"]
    duration = data["duration_long"]
    start = "August 8, 2025"

    if court_type == "trial":
        return (
            f"SEPARATION STATEMENT\n"
            f"{'='*40}\n"
            f"Father and child have been separated for {days} consecutive days "
            f"({duration}) since {start}, when this Court entered five ex parte "
            f"orders suspending all parenting time without notice or hearing, in "
            f"violation of MCR 3.207(C)(2) and MCL 722.27a(3). No parenting time "
            f"has been restored. Father requests immediate restoration of parenting "
            f"time pending a proper best-interest hearing under MCL 722.23.\n"
        )

    elif court_type == "coa":
        return (
            f"SEPARATION TIMELINE — APPEAL OF RIGHT\n"
            f"{'='*40}\n"
            f"The trial court's ex parte orders of {start} have now resulted in "
            f"{days} consecutive days ({duration}) of complete parent-child "
            f"separation. This Court should note that MCR 3.207(A) required a "
            f"hearing within 14 days — a requirement the trial court ignored. "
            f"The ongoing deprivation constitutes plain error affecting substantial "
            f"rights under People v Carines, 460 Mich 750 (1999), and demands "
            f"immediate relief under MCR 7.211(C)(6).\n"
        )

    elif court_type == "msc":
        return (
            f"SEPARATION STATEMENT — SUPERINTENDING CONTROL\n"
            f"{'='*40}\n"
            f"This case presents an extraordinary circumstance warranting this "
            f"Court's exercise of superintending control under Const 1963, art 6, "
            f"§ 4 and MCR 7.306. A father has been completely separated from his "
            f"child for {days} consecutive days ({duration}) based solely on "
            f"ex parte orders entered on {start} — five orders in a single day, "
            f"without notice, without hearing, and without any finding of imminent "
            f"danger. The trial court has refused to restore parenting time or hold "
            f"a best-interest hearing as required by MCL 722.23 and MCL 722.27a. "
            f"Every day of continued separation causes irreparable harm to the "
            f"parent-child bond. Troxel v Granville, 530 US 57 (2000).\n"
        )

    elif court_type == "federal":
        return (
            f"DEPRIVATION OF CONSTITUTIONAL RIGHTS — 42 USC § 1983\n"
            f"{'='*40}\n"
            f"Plaintiff has been deprived of all contact with his child for {days} "
            f"consecutive days ({duration}) since {start}, pursuant to ex parte "
            f"state court orders entered without the procedural due process "
            f"required by the Fourteenth Amendment. The deprivation of a parent's "
            f"fundamental liberty interest in the care, custody, and companionship "
            f"of his child — Troxel v Granville, 530 US 57 (2000) — by state "
            f"actors acting under color of law constitutes a continuing "
            f"constitutional violation actionable under 42 USC § 1983. Damages "
            f"accrue for each day of deprivation. See Duchesne v Sugarman, "
            f"566 F.2d 817 (2d Cir. 1977).\n"
        )

    else:
        return get_separation_narrative()


def get_separation_db_log() -> List[Dict]:
    """Query the DB for any documented separation events."""
    if not os.path.exists(DB_PATH):
        return [{"error": f"Database not found: {DB_PATH}"}]
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT * FROM docket_events WHERE event_date = '2025-08-08' "
            "ORDER BY event_date"
        )
        rows = [dict(r) for r in cur.fetchall()]
        if not rows:
            cur.execute(
                "SELECT * FROM docket_events WHERE event_date LIKE '2025-08%' "
                "ORDER BY event_date LIMIT 10"
            )
            rows = [dict(r) for r in cur.fetchall()]
    except sqlite3.OperationalError as e:
        rows = [{"error": f"Query failed: {e}"}]
    finally:
        conn.close()
    return rows


def main():
    """CLI test harness."""
    print("=" * 70)
    print("SEPARATION DAY COUNTER ENGINE — LitigationOS MANBEARPIG v8.0")
    print("=" * 70)

    # Test 1: Core separation data
    print("\n[TEST 1] Separation metrics:")
    data = get_separation_days()
    for k, v in data.items():
        if k == "milestone_details":
            print(f"  {k}: [{len(v)} milestones passed]")
            for m in v:
                print(f"    ✓ {m['label']} — passed {m['passed_on']}")
        elif k == "next_milestone" and v:
            print(f"  {k}: {v['label']} in {v['days_until']} days ({v['expected_date']})")
        else:
            print(f"  {k}: {v}")

    # Test 2: Narrative
    print("\n[TEST 2] Filing narrative:")
    print(get_separation_narrative())

    # Test 3: Court-specific formats
    for court in ["trial", "coa", "msc", "federal"]:
        print(f"\n[TEST 3-{court}] Format for {court.upper()}:")
        print(format_for_filing(court))

    # Test 4: DB events
    print("\n[TEST 4] DB separation events:")
    events = get_separation_db_log()
    for e in events[:3]:
        print(f"  {e}")

    print("\n✓ Separation Day Counter Engine — all tests complete.")


if __name__ == "__main__":
    main()
