#!/usr/bin/env python3
"""
Tool #165 — Motion Response Deadlines Calculator
=================================================
🆕 NOVEL TOOL — Calculates exact deadlines for
responding to ANY motion type under Michigan Court Rules,
including service method adjustments.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

DEADLINE_RULES = [
    {
        'motion_type': 'Motion (General)',
        'rule': 'MCR 2.119(C)(1)',
        'response_time': '21 days after service',
        'reply_time': '7 days before hearing',
        'service_adjustments': {
            'personal': '0 extra days',
            'mail': '+3 days (MCR 2.107(C)(3))',
            'email/efiling': '+3 days (MCR 2.107(C)(4))',
        },
        'notes': 'Must be filed and served. Judge may shorten or extend.',
    },
    {
        'motion_type': 'Motion for Summary Disposition',
        'rule': 'MCR 2.116(B)',
        'response_time': '21 days after service',
        'reply_time': '7 days before hearing',
        'service_adjustments': {
            'personal': '0 extra days',
            'mail': '+3 days',
            'email/efiling': '+3 days',
        },
        'notes': 'Supporting brief required. Affidavits may be attached.',
    },
    {
        'motion_type': 'Ex Parte Motion',
        'rule': 'MCR 2.119(B)',
        'response_time': 'NONE — decided without hearing (but can move to set aside)',
        'reply_time': 'N/A',
        'service_adjustments': {},
        'notes': 'MCR 3.207(B) — family cases require 2-business-day notice UNLESS immediate danger.',
    },
    {
        'motion_type': 'Motion for Reconsideration',
        'rule': 'MCR 2.119(F)(1)',
        'response_time': '21 days from entry of order',
        'reply_time': 'N/A',
        'service_adjustments': {},
        'notes': 'MUST file within 21 days of order. Must show palpable error.',
    },
    {
        'motion_type': 'Motion to Disqualify Judge',
        'rule': 'MCR 2.003(D)',
        'response_time': 'Within 14 days of discovering grounds',
        'reply_time': 'Chief Judge decides within 14 days',
        'service_adjustments': {},
        'notes': 'File with Chief Judge. Must include affidavit of facts.',
    },
    {
        'motion_type': 'MCR 2.612 — Relief from Judgment',
        'rule': 'MCR 2.612(C)',
        'response_time': '1 year for (C)(1)(a-c), NO limit for (C)(1)(d) void judgment',
        'reply_time': 'As set by court',
        'service_adjustments': {},
        'notes': '(C)(3) — Independent action for fraud = NO time limit. Must show fraud on the court.',
    },
    {
        'motion_type': 'COA Application for Leave',
        'rule': 'MCR 7.205(F)',
        'response_time': '21 days after service',
        'reply_time': 'N/A',
        'service_adjustments': {},
        'notes': 'Application must be filed within 6 months of final order.',
    },
    {
        'motion_type': 'COA Claim of Appeal',
        'rule': 'MCR 7.204(A)',
        'response_time': '21 days from entry of final order',
        'reply_time': 'Per briefing schedule',
        'service_adjustments': {},
        'notes': 'Appeal of right — 21 days is JURISDICTIONAL. Miss it = dismissed.',
    },
    {
        'motion_type': 'Emergency Motion / TRO',
        'rule': 'MCR 3.310',
        'response_time': 'Usually 14 days for preliminary hearing',
        'reply_time': 'At hearing',
        'service_adjustments': {},
        'notes': 'TRO can be entered ex parte. Preliminary injunction hearing within 14 days.',
    },
    {
        'motion_type': 'Discovery Motion (Compel)',
        'rule': 'MCR 2.313',
        'response_time': '21 days after service',
        'reply_time': '7 days before hearing',
        'service_adjustments': {
            'personal': '0 extra days',
            'mail': '+3 days',
        },
        'notes': 'Must attempt resolution before filing. Include good-faith certification.',
    },
]

def main():
    print("=" * 70)
    print("MOTION RESPONSE DEADLINES — Tool #165")
    print("=" * 70)

    lines = [
        "# ⏰ MOTION RESPONSE DEADLINES CALCULATOR",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #165*",
        f"*{len(DEADLINE_RULES)} motion types with exact deadline calculations*\n",
        "---\n",
        "> **CRITICAL: Missing a deadline can be FATAL to your case.**",
        "> **Calendar every deadline the day you receive the motion.**\n",
    ]

    for rule in DEADLINE_RULES:
        lines.append(f"## {rule['motion_type']}")
        lines.append(f"**Rule:** {rule['rule']}")
        lines.append(f"**Response Time:** {rule['response_time']}")
        lines.append(f"**Reply Time:** {rule['reply_time']}")
        if rule['service_adjustments']:
            lines.append("**Service Adjustments:**")
            for method, adj in rule['service_adjustments'].items():
                lines.append(f"  - {method}: {adj}")
        lines.append(f"**Notes:** {rule['notes']}\n")
        lines.append("---\n")
        print(f"  ⏰ {rule['motion_type']}: {rule['response_time']}")

    lines.extend([
        "## 🎯 GOLDEN DEADLINE RULES\n",
        "1. **Calendar IMMEDIATELY** — the day you receive a motion, calendar the deadline",
        "2. **Count from SERVICE date** — not filing date (service = when YOU received it)",
        "3. **Add +3 for mail** — MCR 2.107(C)(3) adds 3 days for mail service",
        "4. **Weekends/holidays** — if deadline falls on weekend/holiday, next business day",
        "5. **When in doubt, file EARLY** — you can always file before the deadline\n",
        f"*{len(DEADLINE_RULES)} motion types · Print and keep at your desk*",
    ])

    md_path = REPORTS_DIR / "MOTION_DEADLINES.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')

    json_path = REPORTS_DIR / "motion_deadlines.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Motion Response Deadlines Calculator (#165)',
        'motion_types': len(DEADLINE_RULES),
    }, indent=2), encoding='utf-8')

    print(f"\n✅ {len(DEADLINE_RULES)} motion types with deadline calculations")
    print(f"   Reports: MOTION_DEADLINES.md + motion_deadlines.json")

if __name__ == '__main__':
    main()
