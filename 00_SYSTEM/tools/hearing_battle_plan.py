#!/usr/bin/env python3
"""
Tool #159 — Hearing Day Battle Plan
=================================================
🆕 NOVEL TOOL — A complete minute-by-minute plan for
Andrew's first hearing day. What to do from waking up
to walking out of the courthouse.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

BATTLE_PLAN = [
    {
        'time': 'Night Before',
        'phase': 'PREPARATION',
        'actions': [
            'Review Pro Se Survival Kit (#154) — pack everything',
            'Print 4 copies of your motion + proposed order',
            'Print Exhibit Index + tab all exhibits',
            'Review Cross-Exam Scripts (#145) for opposing witnesses',
            'Review Objections Card (#102) — memorize top 5',
            'Set 2 alarms — arrive 45 minutes early minimum',
            'Lay out professional clothes (suit, tie, dress shoes)',
            'Charge phone to 100% — bring charger',
            'Eat a good meal. Hydrate. Sleep.',
        ],
    },
    {
        'time': '6:00 AM',
        'phase': 'MORNING',
        'actions': [
            'Shower, dress professionally (suit/tie)',
            'Eat breakfast (protein — you need sustained energy)',
            'Review 1-page filing summary — refresh key points',
            'Check weather (dress in layers, courthouse can be cold)',
            'NO social media. NO texts to Emily. Radio silence.',
        ],
    },
    {
        'time': '7:30 AM',
        'phase': 'TRAVEL',
        'actions': [
            'Leave early — plan for 30 min buffer',
            '14th Circuit Court: 990 Terrace Street, Muskegon, MI 49442',
            'Park in courthouse lot or nearby street (bring quarters)',
            'Bring snacks + water — hearings can last hours',
        ],
    },
    {
        'time': '8:00 AM',
        'phase': 'ARRIVAL',
        'actions': [
            'Go through security — be polite, empty pockets',
            'Find your courtroom — check docket board',
            'Check in with the clerk (announce yourself as pro se)',
            'Sit in gallery, review notes quietly',
            'DO NOT speak to Emily, Berry, or Barnes in the hallway',
            'If they approach: "I have nothing to discuss outside the record"',
        ],
    },
    {
        'time': 'Hearing Start',
        'phase': 'IN COURT',
        'actions': [
            'Stand when judge enters. "Good morning, Your Honor"',
            'When called: "Andrew Pigors, pro se, Your Honor"',
            'Speak clearly, slowly, and to the judge (not opposing)',
            'USE YOUR PREPARED REMARKS — do NOT wing it',
            'Object when necessary: state basis clearly (hearsay, relevance, etc.)',
            'Take notes on everything the judge says',
            'If confused: "Your Honor, may I have a moment to review my notes?"',
            'NEVER argue with the judge — note objection for record',
            'If ruling goes against you: "Respectfully, I object for the record"',
        ],
    },
    {
        'time': 'After Hearing',
        'phase': 'POST-HEARING',
        'actions': [
            'Get a copy of any orders signed that day',
            'Note the next hearing date — write it down immediately',
            'Leave the courthouse without engaging Emily/Berry',
            'In the car: voice-record everything you remember (while fresh)',
            'Drive to Muskegon County Clerk — file any follow-up motions',
            'Update your Hearing Log (#123 report)',
            'Email yourself a summary of what happened',
        ],
    },
]

def main():
    print("=" * 70)
    print("HEARING DAY BATTLE PLAN — Tool #159")
    print("=" * 70)

    lines = [
        "# ⚔️ HEARING DAY BATTLE PLAN",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #159*",
        f"*Minute-by-minute plan for Andrew's hearing day*\n",
        "---\n",
    ]

    total_actions = 0
    for phase in BATTLE_PLAN:
        lines.append(f"## {phase['time']} — {phase['phase']}\n")
        for a in phase['actions']:
            lines.append(f"- [ ] {a}")
        lines.append("")
        total_actions += len(phase['actions'])
        print(f"  ⚔️ {phase['phase']}: {len(phase['actions'])} actions")

    lines.extend([
        "---\n",
        "## 🎯 GOLDEN RULES\n",
        "1. **Be early.** Judges notice who respects their time.",
        "2. **Be prepared.** You have 155+ tools of intelligence — USE them.",
        "3. **Be professional.** Suit, tie, \"Your Honor.\" Every time.",
        "4. **Be brief.** Say what you need to say. Then stop.",
        "5. **Be calm.** They WANT you to lose your temper. Don't give them that.",
        "6. **Be documented.** If it's not in writing, it didn't happen.\n",
        f"*{len(BATTLE_PLAN)} phases · {total_actions} actions · You've got this.*",
    ])

    md_path = REPORTS_DIR / "HEARING_BATTLE_PLAN.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')

    json_path = REPORTS_DIR / "hearing_battle_plan.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Hearing Day Battle Plan (#159)',
        'phases': len(BATTLE_PLAN),
        'total_actions': total_actions,
    }, indent=2), encoding='utf-8')

    print(f"\n✅ {len(BATTLE_PLAN)} phases, {total_actions} actions — complete hearing day plan")
    print(f"   Reports: HEARING_BATTLE_PLAN.md + hearing_battle_plan.json")

if __name__ == '__main__':
    main()
