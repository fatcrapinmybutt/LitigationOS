#!/usr/bin/env python3
"""
Tool #169 — Discovery Request Templates
=================================================
🆕 NOVEL TOOL — Pre-drafted discovery requests
(interrogatories, document requests, admissions)
to serve on Emily Watson.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

DISCOVERY = {
    'interrogatories': {
        'title': 'Interrogatories to Defendant Emily A. Watson',
        'rule': 'MCR 2.309(A) — Max 20 interrogatories (including subparts)',
        'questions': [
            'State your full legal name, date of birth, and current address.',
            'Identify all persons living in your household, including their relationship to you and L.D.W.',
            'Describe in detail the incident you alleged in your PPO petition (Case No. 2023-5907-PP), including date, time, location, and all witnesses.',
            'Identify all communications you have had with Ronald T. Berry regarding Andrew Pigors, L.D.W., or this custody matter.',
            'State whether Ronald T. Berry has drafted, edited, or assisted with any court filings in this case.',
            'Identify all instances where you denied or interfered with Andrew Pigors\' parenting time with L.D.W. since 2023.',
            'Describe all contact attempts made by Andrew Pigors that you are aware of since the entry of the PPO.',
            'State your current employment, employer name, and gross monthly income.',
            'Identify all bank accounts, savings accounts, and investment accounts in your name or jointly held.',
            'Describe L.D.W.\'s current daycare/school arrangements, including provider name and schedule.',
            'Identify all medical providers who have treated L.D.W. in the past 24 months.',
            'State whether you have ever been investigated by CPS/DHHS regarding L.D.W., and if so, describe the outcome.',
            'Identify all witnesses you intend to call at any hearing in this matter.',
            'Describe any substance use (alcohol, marijuana, prescription medications) in the past 24 months.',
            'State whether you have ever made a false statement in any court filing in this case.',
        ],
    },
    'document_requests': {
        'title': 'Request for Production of Documents',
        'rule': 'MCR 2.310 — Reasonable scope, 28 days to respond',
        'requests': [
            'All text messages between you and Andrew Pigors from January 2023 to present.',
            'All text messages between you and Ronald T. Berry from January 2023 to present.',
            'All text messages between you and Jennifer Barnes from January 2023 to present.',
            'All social media posts, messages, or stories referencing Andrew Pigors or L.D.W.',
            'Complete phone records (call logs and text logs) for your primary phone number.',
            'All photographs of L.D.W. taken in the past 12 months.',
            'All financial records (pay stubs, tax returns, bank statements) for the past 24 months.',
            'L.D.W.\'s medical records for the past 24 months.',
            'L.D.W.\'s daycare/school records.',
            'All documents related to the PPO petition (2023-5907-PP).',
            'All communications with Judge McNeill\'s office or staff outside of filed documents.',
            'All drafts of court filings, whether filed or not.',
        ],
    },
    'admissions': {
        'title': 'Requests for Admissions',
        'rule': 'MCR 2.312 — Must respond within 28 days or deemed admitted',
        'requests': [
            'Admit that Andrew Pigors has never been convicted of domestic violence.',
            'Admit that Andrew Pigors has made multiple attempts to contact L.D.W. since 2023.',
            'Admit that Ronald T. Berry currently resides at 2160 Garland Drive with you.',
            'Admit that Ronald T. Berry has assisted you in preparing court filings.',
            'Admit that you did not witness Andrew Pigors engage in any act of violence on the date alleged in the PPO petition.',
            'Admit that you have denied Andrew Pigors parenting time on at least one occasion without court authorization.',
            'Admit that Jennifer Barnes withdrew as your attorney in this case.',
            'Admit that you have not facilitated any phone or video contact between Andrew Pigors and L.D.W. in the past 6 months.',
        ],
    },
}

def main():
    print("=" * 70)
    print("DISCOVERY REQUEST TEMPLATES — Tool #169")
    print("=" * 70)

    lines = [
        "# 📑 DISCOVERY REQUEST TEMPLATES",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #169*",
        f"*Pre-drafted discovery to serve on Emily Watson*\n",
        "---\n",
        "> **Serve these AFTER filing your motions.**",
        "> **Emily has 28 days to respond (MCR 2.309/2.310/2.312).**",
        "> **If she doesn't respond, you can move to compel (MCR 2.313).**\n",
    ]

    total_items = 0
    for key, section in DISCOVERY.items():
        lines.append(f"## {section['title']}")
        lines.append(f"**Rule:** {section['rule']}\n")
        field = 'questions' if 'questions' in section else 'requests'
        for i, item in enumerate(section[field], 1):
            lines.append(f"{i}. {item}")
        lines.append("")
        count = len(section[field])
        total_items += count
        print(f"  📑 {key}: {count} items")

    lines.extend([
        "---\n",
        "## 🎯 DISCOVERY STRATEGY\n",
        "1. **Serve with your motions** — creates pressure on Emily to respond",
        "2. **28-day deadline** — if no response, move to compel (MCR 2.313)",
        "3. **Admissions are POWERFUL** — unrebutted admissions are deemed admitted",
        "4. **Document requests expose lies** — her texts/messages will contradict her filings",
        "5. **Interrogatories pin her down** — answers under oath = perjury risk\n",
        f"*{total_items} total discovery items · Serve via certified mail or email (if permitted)*",
    ])

    md_path = REPORTS_DIR / "DISCOVERY_TEMPLATES.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')

    json_path = REPORTS_DIR / "discovery_templates.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Discovery Request Templates (#169)',
        'interrogatories': len(DISCOVERY['interrogatories']['questions']),
        'document_requests': len(DISCOVERY['document_requests']['requests']),
        'admissions': len(DISCOVERY['admissions']['requests']),
        'total': total_items,
    }, indent=2), encoding='utf-8')

    print(f"\n✅ {total_items} discovery items: interrogatories + doc requests + admissions")
    print(f"   Reports: DISCOVERY_TEMPLATES.md + discovery_templates.json")

if __name__ == '__main__':
    main()
