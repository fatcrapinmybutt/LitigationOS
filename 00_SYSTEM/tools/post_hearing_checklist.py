#!/usr/bin/env python3
"""
Tool #168 — Post-Hearing Action Checklist
=================================================
🆕 NOVEL TOOL — After EVERY hearing, these are the
exact steps Andrew must take within specific timeframes.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

POST_HEARING = {
    'immediately': {
        'timeframe': 'IMMEDIATELY (In the Courthouse)',
        'actions': [
            'Get a copy of any order signed today — ask the clerk',
            'Write down the next hearing date — DO NOT rely on memory',
            'Note who was present (judge, opposing party, attorneys, witnesses)',
            'Leave without engaging Emily, Berry, or Barnes',
        ],
    },
    'within_1_hour': {
        'timeframe': 'Within 1 Hour (In Your Car)',
        'actions': [
            'Voice-record a summary of everything that happened while fresh',
            'Note any objections you made and the judge\'s rulings',
            'Note any objections you SHOULD have made (for next time)',
            'Note the judge\'s demeanor and any concerning statements',
            'Note any ex parte observations (judge talking to Emily/Barnes privately)',
        ],
    },
    'within_24_hours': {
        'timeframe': 'Within 24 Hours',
        'actions': [
            'Type up your notes into a formal hearing summary',
            'Update your LitigationOS hearing log',
            'Calendar ALL new deadlines from the hearing',
            'Review any orders entered — check for errors',
            'If order has errors: prepare motion to correct under MCR 2.612(A)',
            'Email yourself a copy of all notes and observations',
        ],
    },
    'within_7_days': {
        'timeframe': 'Within 7 Days',
        'actions': [
            'If you lost a motion: decide whether to file reconsideration (MCR 2.119(F) — 21 days)',
            'If you won: prepare proposed order if judge asked you to draft it',
            'Order transcript of hearing if needed for appeal (within 14 days per MCR 7.210)',
            'Update filing strategy based on hearing outcome',
            'Review cross-exam performance — what worked, what didn\'t',
        ],
    },
    'within_21_days': {
        'timeframe': 'Within 21 Days (CRITICAL)',
        'actions': [
            'Motion for reconsideration deadline (MCR 2.119(F)(1)) — USE IT OR LOSE IT',
            'If appeal needed: file claim of appeal (MCR 7.204 — 21 days from final order)',
            'Respond to any motions filed by opposing party at the hearing',
            'Update master filing strategy',
        ],
    },
}

def main():
    print("=" * 70)
    print("POST-HEARING ACTION CHECKLIST — Tool #168")
    print("=" * 70)

    lines = [
        "# 📋 POST-HEARING ACTION CHECKLIST",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #168*",
        f"*Do these after EVERY hearing — missing a step can cost you the case*\n",
        "---\n",
        "> **The hearing isn't over when you leave the courtroom.**",
        "> **What you do in the next 21 days determines whether you preserve your rights.**\n",
    ]

    total_actions = 0
    for key, phase in POST_HEARING.items():
        lines.append(f"## ⏰ {phase['timeframe']}\n")
        for action in phase['actions']:
            lines.append(f"- [ ] {action}")
        lines.append("")
        total_actions += len(phase['actions'])
        print(f"  ⏰ {phase['timeframe']}: {len(phase['actions'])} actions")

    lines.extend([
        "---\n",
        "## 🚨 CRITICAL DEADLINES AFTER HEARING\n",
        "| Deadline | Timeframe | Rule | Consequence |",
        "|----------|-----------|------|-------------|",
        "| Motion for reconsideration | 21 days | MCR 2.119(F)(1) | Waived forever |",
        "| Claim of appeal | 21 days from final order | MCR 7.204(A) | JURISDICTIONAL — dismissed |",
        "| Transcript order | 14 days | MCR 7.210(B)(3) | Can't appeal without it |",
        "| Proposed order submission | As ordered by judge | MCR 2.602 | Judge enters their own version |\n",
        f"*{len(POST_HEARING)} phases · {total_actions} actions · Print and use after EVERY hearing*",
    ])

    md_path = REPORTS_DIR / "POST_HEARING_CHECKLIST.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')

    json_path = REPORTS_DIR / "post_hearing_checklist.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Post-Hearing Action Checklist (#168)',
        'phases': len(POST_HEARING),
        'total_actions': total_actions,
    }, indent=2), encoding='utf-8')

    print(f"\n✅ {len(POST_HEARING)} phases, {total_actions} actions — complete post-hearing guide")
    print(f"   Reports: POST_HEARING_CHECKLIST.md + post_hearing_checklist.json")

if __name__ == '__main__':
    main()
