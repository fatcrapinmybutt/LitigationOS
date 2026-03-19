"""
LitigationOS Emergency Response Protocol
Handles time-sensitive litigation events: ex parte motions, child safety filings,
surprise motions, and judge reassignment reanalysis.
"""

import sys
import json
import sqlite3
import os
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB_PATH = os.path.join(os.path.dirname(__file__), "emergency_templates.db")


# ---------------------------------------------------------------------------
# Template definitions
# ---------------------------------------------------------------------------

EMERGENCY_TEMPLATES = [
    {
        "template_id": "ex_parte_001",
        "name": "Emergency Ex Parte Application",
        "category": "ex_parte",
        "priority": "critical",
        "response_window_hours": 24,
        "sections": [
            {
                "title": "Caption and Case Information",
                "content": (
                    "SUPERIOR COURT OF THE STATE OF [STATE]\n"
                    "COUNTY OF [COUNTY]\n\n"
                    "Case No.: [CASE_NUMBER]\n"
                    "Petitioner: [PETITIONER_NAME]\n"
                    "Respondent: [RESPONDENT_NAME]\n\n"
                    "EX PARTE APPLICATION FOR [RELIEF_REQUESTED]"
                ),
            },
            {
                "title": "Declaration of Emergency",
                "content": (
                    "I, [DECLARANT_NAME], declare under penalty of perjury:\n\n"
                    "1. Irreparable harm will occur if relief is not granted immediately because:\n"
                    "   [DESCRIBE_IRREPARABLE_HARM]\n\n"
                    "2. The following exigent circumstances exist:\n"
                    "   [DESCRIBE_EXIGENT_CIRCUMSTANCES]\n\n"
                    "3. Notice was provided to opposing counsel on [DATE] via [METHOD],\n"
                    "   or notice was not possible because: [REASON_NO_NOTICE]"
                ),
            },
            {
                "title": "Points and Authorities",
                "content": (
                    "A. Legal Standard for Ex Parte Relief\n"
                    "   - Irreparable harm absent immediate relief\n"
                    "   - Likelihood of success on the merits\n"
                    "   - Balance of equities favors movant\n\n"
                    "B. Application of Facts to Law\n"
                    "   [LEGAL_ARGUMENT]\n\n"
                    "C. Supporting Case Authority\n"
                    "   [CITE_CASES]"
                ),
            },
            {
                "title": "Proposed Order",
                "content": (
                    "IT IS HEREBY ORDERED that:\n"
                    "1. [SPECIFIC_RELIEF_1]\n"
                    "2. [SPECIFIC_RELIEF_2]\n"
                    "3. A hearing on this matter is set for [DATE] at [TIME].\n\n"
                    "Dated: _______________\n"
                    "Judge: _______________"
                ),
            },
        ],
        "checklist": [
            "Verify court's ex parte procedures and filing requirements",
            "Confirm notice requirements met or document why not possible",
            "Prepare declaration(s) with specific facts showing irreparable harm",
            "Draft proposed order for judge signature",
            "Arrange for personal service if required",
            "Calendar the return hearing date",
        ],
    },
    {
        "template_id": "child_safety_001",
        "name": "Emergency Child Safety Filing",
        "category": "child_safety",
        "priority": "critical",
        "response_window_hours": 4,
        "sections": [
            {
                "title": "Emergency Petition Header",
                "content": (
                    "EMERGENCY PETITION FOR TEMPORARY RESTRAINING ORDER\n"
                    "AND ORDER TO SHOW CAUSE RE: CHILD CUSTODY/SAFETY\n\n"
                    "Case No.: [CASE_NUMBER]\n"
                    "Minor Child(ren): [CHILD_INITIALS], Age [AGE]\n\n"
                    "IMMEDIATE RELIEF REQUESTED: [TYPE_OF_RELIEF]"
                ),
            },
            {
                "title": "Factual Basis for Emergency",
                "content": (
                    "1. IMMEDIATE THREAT TO CHILD SAFETY:\n"
                    "   [DESCRIBE_THREAT]\n\n"
                    "2. SPECIFIC INCIDENTS:\n"
                    "   a. On [DATE], [DESCRIBE_INCIDENT]\n"
                    "   b. [ADDITIONAL_INCIDENTS]\n\n"
                    "3. CURRENT LOCATION AND STATUS OF CHILD(REN):\n"
                    "   [CURRENT_STATUS]\n\n"
                    "4. PRIOR REPORTS TO AUTHORITIES:\n"
                    "   [CPS_REPORTS_POLICE_REPORTS]"
                ),
            },
            {
                "title": "Mandatory Reporting Compliance",
                "content": (
                    "☐ CPS report filed — Report #: [REPORT_NUMBER], Date: [DATE]\n"
                    "☐ Law enforcement contacted — Agency: [AGENCY], Report #: [NUMBER]\n"
                    "☐ Medical evaluation obtained/scheduled\n"
                    "☐ Forensic interview arranged if applicable\n"
                    "☐ School/daycare notified of custody restrictions"
                ),
            },
            {
                "title": "Requested Emergency Orders",
                "content": (
                    "Petitioner requests the Court issue the following emergency orders:\n"
                    "1. Temporary sole legal and physical custody to [PARTY]\n"
                    "2. Supervised visitation only for [PARTY] through [PROVIDER]\n"
                    "3. Stay-away order: [PARTY] to remain [DISTANCE] from child(ren)\n"
                    "4. No removal of child(ren) from [JURISDICTION]\n"
                    "5. [ADDITIONAL_RELIEF]\n\n"
                    "OSC Hearing requested within [DAYS] days."
                ),
            },
        ],
        "checklist": [
            "IMMEDIATE: Ensure child is currently safe",
            "File CPS report if not already filed (mandatory reporter obligation)",
            "Contact law enforcement if child is in immediate danger",
            "Gather all evidence of threat (photos, messages, medical records)",
            "Prepare declarations from witnesses with first-hand knowledge",
            "File emergency petition with court clerk — request same-day hearing",
            "Arrange for service on opposing party",
            "Notify child's school/daycare of any custody restrictions",
            "Schedule follow-up hearing within statutory timeframe",
        ],
    },
    {
        "template_id": "surprise_motion_001",
        "name": "24-Hour Surprise Motion Response",
        "category": "surprise_motion",
        "priority": "critical",
        "response_window_hours": 24,
        "sections": [
            {
                "title": "Initial Assessment",
                "content": (
                    "SURPRISE MOTION RESPONSE FRAMEWORK\n\n"
                    "Motion Type: [MOTION_TYPE]\n"
                    "Filed By: [OPPOSING_PARTY]\n"
                    "Filed Date: [DATE]\n"
                    "Hearing Date: [HEARING_DATE]\n"
                    "Response Deadline: [DEADLINE]\n\n"
                    "IMMEDIATE ACTIONS REQUIRED — SEE CHECKLIST"
                ),
            },
            {
                "title": "Opposition Framework",
                "content": (
                    "I. PROCEDURAL OBJECTIONS\n"
                    "   - Insufficient notice: [ANALYZE]\n"
                    "   - Improper service: [ANALYZE]\n"
                    "   - Failure to meet and confer: [ANALYZE]\n\n"
                    "II. SUBSTANTIVE OPPOSITION\n"
                    "   - Legal standard not met because: [ARGUMENT]\n"
                    "   - Facts do not support relief because: [ARGUMENT]\n"
                    "   - Movant's evidence is insufficient because: [ARGUMENT]\n\n"
                    "III. PREJUDICE TO CLIENT\n"
                    "   - Granting the motion would cause: [DESCRIBE_HARM]\n\n"
                    "IV. ALTERNATIVE RELIEF\n"
                    "   - If any relief is granted, request: [LESSER_ALTERNATIVE]"
                ),
            },
        ],
        "checklist": [
            "HOUR 0–1: Read the motion completely and identify the core relief sought",
            "HOUR 0–1: Calendar the response deadline and hearing date immediately",
            "HOUR 1–2: Check for procedural defects (notice, service, meet-and-confer)",
            "HOUR 2–4: Research the legal standard for the motion type",
            "HOUR 2–4: Pull relevant case facts and evidence that oppose the motion",
            "HOUR 4–8: Draft the opposition brief",
            "HOUR 8–12: Research and insert case law citations",
            "HOUR 12–16: Prepare supporting declarations if needed",
            "HOUR 16–20: Review, revise, and finalize the opposition",
            "HOUR 20–22: Prepare for oral argument — outline key points",
            "HOUR 22–24: File and serve the opposition",
            "HOUR 22–24: Confirm hearing logistics (courtroom, remote link, time)",
        ],
    },
    {
        "template_id": "judge_change_001",
        "name": "Judge Change Reanalysis Trigger",
        "category": "judge_change",
        "priority": "high",
        "response_window_hours": 48,
        "sections": [
            {
                "title": "Reassignment Notice",
                "content": (
                    "JUDGE REASSIGNMENT REANALYSIS\n\n"
                    "Case: [CASE_NAME] — [CASE_NUMBER]\n"
                    "Previous Judge: [OLD_JUDGE]\n"
                    "New Judge: [NEW_JUDGE]\n"
                    "Effective Date: [DATE]\n"
                    "Reason: [REASSIGNMENT_REASON]"
                ),
            },
            {
                "title": "Reanalysis Checklist",
                "content": (
                    "1. NEW JUDGE PROFILE ANALYSIS\n"
                    "   - Ruling history in similar case types\n"
                    "   - Known preferences (briefing style, oral argument, discovery scope)\n"
                    "   - Typical motion disposition patterns\n"
                    "   - Sentencing/award tendencies\n\n"
                    "2. OMEGA SCORE RECALCULATION\n"
                    "   - Opposition dimension: Update with new judge's track record vs. opposing counsel\n"
                    "   - Advocacy dimension: Recalibrate for new judge's preferences\n"
                    "   - All dimensions: Full recalculation triggered\n\n"
                    "3. STRATEGY ADJUSTMENT\n"
                    "   - Pending motions: Review for new judge's likely reception\n"
                    "   - Trial strategy: Adjust presentation style\n"
                    "   - Settlement posture: Reassess based on new judge's history\n\n"
                    "4. NOTIFICATIONS\n"
                    "   - Alert assigned attorney of reassignment\n"
                    "   - Flag any OMEGA score change > 5 points\n"
                    "   - Schedule strategy review meeting if score change > 10 points"
                ),
            },
        ],
        "checklist": [
            "Confirm reassignment details from court notice",
            "Run judge-profiler agent on new judge",
            "Trigger OMEGA full recalculation for the case",
            "Compare old vs. new OMEGA scores across all dimensions",
            "Review all pending motions for new judge compatibility",
            "Adjust trial strategy memo if applicable",
            "Notify lead attorney of score changes",
            "Update case timeline with reassignment event",
            "Schedule strategy review if OMEGA delta > 10 points",
        ],
    },
]


# ---------------------------------------------------------------------------
# Database operations
# ---------------------------------------------------------------------------

def init_db(db_path: str) -> sqlite3.Connection:
    """Create the emergency templates table and return a connection."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS omega_emergency_templates (
            template_id   TEXT PRIMARY KEY,
            name          TEXT NOT NULL,
            category      TEXT NOT NULL,
            priority      TEXT NOT NULL,
            response_window_hours INTEGER NOT NULL,
            sections      TEXT NOT NULL,
            checklist     TEXT NOT NULL,
            created_at    TEXT NOT NULL,
            updated_at    TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def save_templates(conn: sqlite3.Connection, templates: list) -> int:
    """Insert or replace all emergency templates. Returns count saved."""
    now = datetime.utcnow().isoformat() + "Z"
    rows = []
    for t in templates:
        rows.append((
            t["template_id"],
            t["name"],
            t["category"],
            t["priority"],
            t["response_window_hours"],
            json.dumps(t["sections"], indent=2),
            json.dumps(t["checklist"], indent=2),
            now,
            now,
        ))
    conn.executemany(
        """
        INSERT OR REPLACE INTO omega_emergency_templates
            (template_id, name, category, priority, response_window_hours,
             sections, checklist, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    return len(rows)


def print_summary(conn: sqlite3.Connection) -> None:
    """Print a summary of all stored templates."""
    cursor = conn.execute(
        "SELECT template_id, name, category, priority, response_window_hours FROM omega_emergency_templates ORDER BY template_id"
    )
    rows = cursor.fetchall()

    print("=" * 72)
    print("  LITIGATIONOS EMERGENCY PROTOCOL — TEMPLATE REGISTRY")
    print("=" * 72)
    print(f"\n  Templates saved: {len(rows)}")
    print(f"  Database: {DB_PATH}")
    print(f"  Timestamp: {datetime.utcnow().isoformat()}Z\n")

    for template_id, name, category, priority, window in rows:
        icon = {"critical": "🔴", "high": "🟠", "medium": "🟡"}.get(priority, "⚪")
        print(f"  {icon} [{template_id}] {name}")
        print(f"     Category: {category} | Priority: {priority} | Response Window: {window}h")
        print()

    print("-" * 72)
    print("  ✅ All emergency templates loaded and ready.")
    print("  ⚡ Emergency protocols can be triggered via API or agent fleet.")
    print("-" * 72)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("\n🚨 LitigationOS Emergency Protocol Initializing...\n")

    conn = init_db(DB_PATH)
    count = save_templates(conn, EMERGENCY_TEMPLATES)

    print(f"  → Created/updated {count} emergency templates in database.\n")

    print_summary(conn)
    conn.close()


if __name__ == "__main__":
    main()
