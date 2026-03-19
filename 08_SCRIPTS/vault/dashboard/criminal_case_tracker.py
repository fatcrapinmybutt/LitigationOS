"""
CRIMINAL CASE TRACKER — LitigationOS
======================================
Tracks deadlines, action items, and countdown for the criminal case:
People v. Pigors, Case No. 2025-25245676SM-SM
60th District Court, Muskegon County

Usage:
    python criminal_case_tracker.py              # Full dashboard
    python criminal_case_tracker.py --countdown  # Days until trial only
    python criminal_case_tracker.py --actions    # Pending actions only
    python criminal_case_tracker.py --json       # JSON output

ScriptVault: dashboard/criminal_case_tracker.py | Version 1.0
"""
import sys
import json
from datetime import datetime, date, timedelta

sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")

# --- Case Constants ---
CASE_NUMBER = "2025-25245676SM-SM"
COURT = "60th Judicial District Court, Muskegon County"
JUDGE = "Hon. Raymond J. Kostrzewa, Jr."
CHARGE = "Assault & Battery (Misdemeanor)"
DEFENSE_THEORY = "Self-Defense (MCL 780.972)"
APPOINTED_COUNSEL = "Amy P. Campanelli, Public Defender"
INVESTIGATING_OFFICER = "Baker/Shawn — Michigan State Police"

# Key dates
INCIDENT_DATE = date(2025, 12, 7)
ARREST_DATE = date(2025, 12, 22)
BOND_RELEASE_DATE = date(2025, 12, 25)
PRETRIAL_DATE = date(2026, 1, 21)
TRIAL_DATE = date(2026, 4, 7)
ARREST_DELAY_DAYS = (ARREST_DATE - INCIDENT_DATE).days

# Action items with deadlines
ACTIONS = [
    {
        "id": "A1",
        "action": "Mail FOIA Request for body camera footage",
        "deadline": date(2026, 3, 19),
        "priority": "CRITICAL",
        "document": "01_FOIA_REQUEST_BODY_CAMERA.md",
        "cost": "$8 (certified mail)",
        "location": "Post Office → Sheriff's Office",
        "status": "pending",
    },
    {
        "id": "A2",
        "action": "Send demand letter to Campanelli",
        "deadline": date(2026, 3, 19),
        "priority": "CRITICAL",
        "document": "03_DEMAND_LETTER_CAMPANELLI.md",
        "cost": "$8 (certified mail) + email",
        "location": "Post Office → Public Defender",
        "status": "pending",
    },
    {
        "id": "A3",
        "action": "Call jail for corrections officer name and attacker names",
        "deadline": date(2026, 3, 19),
        "priority": "CRITICAL",
        "document": None,
        "cost": "Free",
        "location": "Phone: (231) 724-6243",
        "status": "pending",
    },
    {
        "id": "A4",
        "action": "File Motion to Compel Discovery at 60th District Court",
        "deadline": date(2026, 3, 20),
        "priority": "HIGH",
        "document": "02_MOTION_COMPEL_DISCOVERY.md",
        "cost": "~$20 or fee waiver",
        "location": "60th District Court, 990 Terrace St",
        "status": "pending",
    },
    {
        "id": "A5",
        "action": "Get criminal trial subpoena forms from clerk",
        "deadline": date(2026, 3, 20),
        "priority": "HIGH",
        "document": None,
        "cost": "~$20-30 per subpoena",
        "location": "60th District Court, 990 Terrace St",
        "status": "pending",
    },
    {
        "id": "A6",
        "action": "Request in-person meeting with Campanelli",
        "deadline": date(2026, 3, 20),
        "priority": "HIGH",
        "document": None,
        "cost": "Free",
        "location": "Phone: (231) 724-6289",
        "status": "pending",
    },
    {
        "id": "A7",
        "action": "Campanelli response deadline (48 hours from demand letter)",
        "deadline": date(2026, 3, 21),
        "priority": "CRITICAL",
        "document": "03_DEMAND_LETTER_CAMPANELLI.md",
        "cost": None,
        "location": "Wait for response",
        "status": "pending",
    },
    {
        "id": "A8",
        "action": "File Motion to Substitute Counsel (if no response from Campanelli)",
        "deadline": date(2026, 3, 21),
        "priority": "CONDITIONAL",
        "document": "04_MOTION_SUBSTITUTE_COUNSEL.md",
        "cost": "~$20 or fee waiver",
        "location": "60th District Court, 990 Terrace St",
        "status": "pending",
    },
    {
        "id": "A9",
        "action": "FOIA response deadline (5 business days)",
        "deadline": date(2026, 3, 26),
        "priority": "HIGH",
        "document": "01_FOIA_REQUEST_BODY_CAMERA.md",
        "cost": None,
        "location": "Wait for response from Sheriff's Office",
        "status": "pending",
    },
    {
        "id": "A10",
        "action": "Body camera footage must be produced (7 days before trial)",
        "deadline": date(2026, 3, 31),
        "priority": "CRITICAL",
        "document": "02_MOTION_COMPEL_DISCOVERY.md",
        "cost": None,
        "location": "Court-ordered deadline (if motion granted)",
        "status": "pending",
    },
    {
        "id": "A11",
        "action": "Final trial preparation complete",
        "deadline": date(2026, 4, 4),
        "priority": "HIGH",
        "document": "05_SELF_DEFENSE_STRATEGY.md",
        "cost": None,
        "location": "Home",
        "status": "pending",
    },
    {
        "id": "A12",
        "action": "JURY TRIAL — 9:00 AM",
        "deadline": TRIAL_DATE,
        "priority": "CRITICAL",
        "document": "05_SELF_DEFENSE_STRATEGY.md",
        "cost": None,
        "location": "60th District Court, 990 Terrace St, Muskegon MI 49442",
        "status": "pending",
    },
]


def days_until(target: date) -> int:
    """Calculate days from today until target date."""
    return (target - date.today()).days


def urgency_label(days: int) -> str:
    """Return urgency label based on days remaining."""
    if days < 0:
        return "⚠️  OVERDUE"
    if days == 0:
        return "🔴 TODAY"
    if days <= 3:
        return "🔴 URGENT"
    if days <= 7:
        return "🟠 SOON"
    if days <= 14:
        return "🟡 APPROACHING"
    return "🔵 SCHEDULED"


def print_header():
    """Print the dashboard header."""
    days = days_until(TRIAL_DATE)
    print("=" * 72)
    print("  CRIMINAL CASE TRACKER — People v. Pigors")
    print(f"  Case No. {CASE_NUMBER}")
    print(f"  {COURT}")
    print("=" * 72)
    print()
    print(f"  Judge:           {JUDGE}")
    print(f"  Charge:          {CHARGE}")
    print(f"  Defense:         {DEFENSE_THEORY}")
    print(f"  Counsel:         {APPOINTED_COUNSEL}")
    print(f"  Officer:         {INVESTIGATING_OFFICER}")
    print()
    print(f"  Trial Date:      {TRIAL_DATE.strftime('%B %d, %Y')} at 9:00 AM")
    print(f"  Days to Trial:   {days} days")
    print(f"  Urgency:         {urgency_label(days)}")
    print()


def print_timeline():
    """Print key dates timeline."""
    print("-" * 72)
    print("  KEY DATES TIMELINE")
    print("-" * 72)
    dates = [
        (INCIDENT_DATE, "Jail incident (5-on-1 attack)"),
        (ARREST_DATE, f"Arrest ({ARREST_DELAY_DAYS}-day delay)"),
        (BOND_RELEASE_DATE, "Released on bond"),
        (PRETRIAL_DATE, "Pre-trial hearing"),
        (TRIAL_DATE, "JURY TRIAL — 9:00 AM"),
    ]
    for d, label in dates:
        marker = " ◄── TODAY" if d == date.today() else ""
        passed = "  ✓" if d < date.today() else "   "
        print(f"  {passed} {d.strftime('%b %d, %Y')}  {label}{marker}")
    print()


def print_actions(filter_status=None):
    """Print action items with deadlines."""
    print("-" * 72)
    print("  ACTION ITEMS")
    print("-" * 72)
    for a in ACTIONS:
        if filter_status and a["status"] != filter_status:
            continue
        days = days_until(a["deadline"])
        urgency = urgency_label(days)
        status_icon = "✅" if a["status"] == "done" else "⬜"
        print(f"  {status_icon} [{a['id']}] {a['action']}")
        print(f"       Deadline: {a['deadline'].strftime('%b %d, %Y')} ({days} days) {urgency}")
        print(f"       Priority: {a['priority']}")
        if a["document"]:
            print(f"       Document: {a['document']}")
        if a["cost"]:
            print(f"       Cost:     {a['cost']}")
        print(f"       Location: {a['location']}")
        print()


def print_countdown():
    """Print trial countdown."""
    days = days_until(TRIAL_DATE)
    print()
    print("=" * 72)
    print(f"  ⏰ TRIAL COUNTDOWN: {days} DAYS REMAINING")
    print(f"     Trial: {TRIAL_DATE.strftime('%A, %B %d, %Y')} at 9:00 AM")
    print(f"     Court: {COURT}")
    print(f"     Judge: {JUDGE}")
    print("=" * 72)
    print()


def to_json():
    """Output case data as JSON."""
    data = {
        "case": {
            "number": CASE_NUMBER,
            "court": COURT,
            "judge": JUDGE,
            "charge": CHARGE,
            "defense_theory": DEFENSE_THEORY,
            "counsel": APPOINTED_COUNSEL,
            "officer": INVESTIGATING_OFFICER,
        },
        "dates": {
            "incident": INCIDENT_DATE.isoformat(),
            "arrest": ARREST_DATE.isoformat(),
            "bond_release": BOND_RELEASE_DATE.isoformat(),
            "pretrial": PRETRIAL_DATE.isoformat(),
            "trial": TRIAL_DATE.isoformat(),
        },
        "countdown": {
            "days_to_trial": days_until(TRIAL_DATE),
            "urgency": urgency_label(days_until(TRIAL_DATE)),
            "today": date.today().isoformat(),
        },
        "actions": [
            {
                "id": a["id"],
                "action": a["action"],
                "deadline": a["deadline"].isoformat(),
                "days_remaining": days_until(a["deadline"]),
                "priority": a["priority"],
                "document": a["document"],
                "status": a["status"],
            }
            for a in ACTIONS
        ],
    }
    print(json.dumps(data, indent=2))


def main():
    """Main entry point."""
    args = sys.argv[1:]

    if "--json" in args:
        to_json()
        return

    if "--countdown" in args:
        print_countdown()
        return

    if "--actions" in args:
        print_actions(filter_status="pending")
        return

    # Full dashboard
    print_header()
    print_timeline()
    print_actions()
    print_countdown()


if __name__ == "__main__":
    main()
