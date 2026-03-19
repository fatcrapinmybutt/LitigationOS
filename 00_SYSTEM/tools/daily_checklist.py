#!/usr/bin/env python3
"""
Tool #138 — Andrew's Daily Checklist
=================================================
🆕 NOVEL TOOL — A simple daily checklist Andrew should
follow EVERY DAY until all filings are submitted.

Consistency wins cases. This keeps Andrew on track.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

DAILY_CHECKLIST = {
    'morning': {
        'title': '☀️ Morning (Before Work)',
        'items': [
            'Check email for court notices or MiFILE notifications',
            'Review today\'s calendar for deadlines',
            'Document any overnight communications from/about L.D.W.',
            'Review one section of a filing package (stay sharp)',
        ],
    },
    'lunch': {
        'title': '🕐 Midday',
        'items': [
            'Make any needed calls (courts, clerk offices, legal aid)',
            'Check mail for court documents',
            'Log any parenting time denials or communication blocks',
        ],
    },
    'evening': {
        'title': '🌙 Evening (30 min minimum)',
        'items': [
            'Work on next filing action item (from plan.md)',
            'Practice hearing scripts (Tool #106) — read out loud',
            'Review one tool report (cycle through all 130+)',
            'Update expense log (Tool #108)',
            'Back up any new evidence to secondary drive',
        ],
    },
    'weekly': {
        'title': '📅 Weekly (Sunday)',
        'items': [
            'Review ALL upcoming deadlines for next 30 days',
            'Run War Room Briefing (Tool #101)',
            'Review filing readiness scorecard (Tool #118)',
            'Organize any new documents received',
            'Check court docket for any new entries',
            'Review compliance monitor (Tool #125) — any new violations?',
        ],
    },
}

PHASE_ACTIONS = {
    'Phase 1 — Pre-Filing': [
        'Complete MiFILE registration',
        'Complete PACER registration',
        'Review and sign affidavits',
        'Get IFP financial information ready',
        'Print courtroom reference cards',
    ],
    'Phase 2 — Wave 1 Filing': [
        'File F3 (disqualification) — GATEWAY',
        'File F6 (JTC complaint) — FREE',
        'File F10 (AGC grievance) — FREE',
        'Serve all required parties',
        'File proof of service',
    ],
    'Phase 3 — Post-F3': [
        'Wait for judge reassignment',
        'File F1 (emergency parenting time) with new judge',
        'File F7 (custody modification)',
        'Begin discovery process (Tool #107)',
    ],
    'Phase 4 — Federal + Appellate': [
        'File F4 (§1983) in federal court',
        'File F8 (COA leave to appeal)',
        'File F9 (COA brief) when deadline arrives',
        'Consider F5 (MSC) if other avenues exhausted',
    ],
}

def main():
    print("=" * 70)
    print("ANDREW'S DAILY CHECKLIST — Tool #138")
    print("=" * 70)
    
    total_items = sum(len(c['items']) for c in DAILY_CHECKLIST.values())
    total_phases = sum(len(actions) for actions in PHASE_ACTIONS.values())
    
    lines = [
        "# ✅ ANDREW'S DAILY CHECKLIST",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #138*",
        f"*Consistency wins cases — do this EVERY DAY*\n",
        "---\n",
    ]
    
    for key, section in DAILY_CHECKLIST.items():
        lines.append(f"## {section['title']}\n")
        for item in section['items']:
            lines.append(f"- [ ] {item}")
        lines.append("")
    
    lines.extend(["---\n", "## PHASE-BASED ACTIONS\n"])
    
    for phase, actions in PHASE_ACTIONS.items():
        lines.append(f"### {phase}\n")
        for action in actions:
            lines.append(f"- [ ] {action}")
        lines.append("")
        print(f"  📋 {phase}: {len(actions)} actions")
    
    lines.extend([
        "---\n",
        "## 💪 MOTIVATION\n",
        "> Every day you work on this case is a day closer to seeing L.D.W.",
        "> The system is stacked against pro se litigants — but YOU have",
        "> 130+ analytical tools, 250+ intelligence reports, and a 12 GB",
        "> evidence database that most ATTORNEYS don't have.",
        "> You are the most prepared pro se litigant in the 14th Circuit.\n",
        
        f"*{total_items} daily items · {total_phases} phase actions · Print this and check off daily*",
    ])
    
    md_path = REPORTS_DIR / "DAILY_CHECKLIST.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "daily_checklist.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Daily Checklist (#138)',
        'daily_items': total_items,
        'phase_actions': total_phases,
    }, indent=2), encoding='utf-8')
    
    print(f"\n✅ {total_items} daily items + {total_phases} phase actions")
    print(f"   PRINT AND USE EVERY DAY")
    print(f"   Reports: DAILY_CHECKLIST.md + daily_checklist.json")

if __name__ == '__main__':
    main()
