#!/usr/bin/env python3
"""
Tool #155 — Settlement Negotiation Framework
=================================================
🆕 NOVEL TOOL — If Emily or her attorney proposes a 
settlement at any point, Andrew needs to know his
minimum terms, walk-away points, and leverage.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

SETTLEMENT_TERMS = {
    'non_negotiable': [
        {
            'term': 'Regular, unsupervised parenting time with L.D.W.',
            'minimum': 'Every other weekend + one weekday evening (minimum)',
            'reason': 'L.D.W. needs her father. This is the floor, not the ceiling.',
        },
        {
            'term': 'Daily phone/video communication with L.D.W.',
            'minimum': 'At least 3 calls per week at consistent times',
            'reason': 'Communication is essential for maintaining attachment during non-custodial time.',
        },
        {
            'term': 'Joint legal custody (shared major decisions)',
            'minimum': 'Information rights + consultation before major decisions',
            'reason': 'Andrew is a competent, involved parent who should have input on education, health, religion.',
        },
        {
            'term': 'Dismissal of fraudulent PPO',
            'minimum': 'PPO vacated or dismissed with prejudice',
            'reason': 'The PPO was based on fabricated evidence. It must be removed.',
        },
    ],
    'negotiable': [
        {
            'term': 'Specific parenting schedule',
            'ideal': '50/50 week-on/week-off',
            'compromise': 'Every other weekend + Wednesday overnight + one weeknight dinner',
            'reason': 'Flexibility shows reasonableness to the court.',
        },
        {
            'term': 'Exchange location',
            'ideal': 'School/daycare pickup and dropoff',
            'compromise': 'Police station lobby or other neutral public location',
            'reason': 'Safety and neutrality can be achieved multiple ways.',
        },
        {
            'term': 'Communication platform',
            'ideal': 'Direct text/call',
            'compromise': 'OurFamilyWizard (courts favor this in high-conflict cases)',
            'reason': 'The platform matters less than that communication happens.',
        },
        {
            'term': 'Holiday schedule',
            'ideal': 'Alternating all major holidays',
            'compromise': 'Standard Michigan schedule with flexibility',
            'reason': 'Standard schedules are well-tested and fair.',
        },
    ],
    'walk_away': [
        'Any agreement with NO parenting time for Andrew',
        'Any agreement that maintains the fraudulent PPO',
        'Any agreement requiring Andrew to admit wrongdoing he didn\'t commit',
        'Any agreement that gives Emily sole legal custody without cause',
        'Any agreement contingent on Andrew dropping F3 (disqualification)',
        'Any agreement contingent on Andrew dropping F6 (JTC) or F10 (AGC)',
    ],
    'leverage_points': [
        'Andrew has documented evidence of Emily\'s perjury — exposure risk for her',
        'JTC complaint (F6) creates pressure even without formal charges',
        'AGC grievance (F10) impacts Barnes\' license — motivates negotiation',
        'Federal §1983 (F4) carries potential for damages — financial exposure',
        'Andrew\'s evidence arsenal is comprehensive — discovery will be devastating for Emily',
        'New judge after F3 means a fresh start — Emily loses any advantage with McNeill',
    ],
}

def main():
    print("=" * 70)
    print("SETTLEMENT NEGOTIATION FRAMEWORK — Tool #155")
    print("=" * 70)

    lines = [
        "# 🤝 SETTLEMENT NEGOTIATION FRAMEWORK",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #155*",
        f"*Know your leverage, your floor, and when to walk away*\n",
        "---\n",
        "> **\"Never negotiate out of fear, but never fear to negotiate.\"**",
        "> **— John F. Kennedy**\n",
        "---\n",
    ]

    lines.append("## 🔴 NON-NEGOTIABLE TERMS\n")
    for t in SETTLEMENT_TERMS['non_negotiable']:
        lines.append(f"### {t['term']}")
        lines.append(f"**Minimum:** {t['minimum']}")
        lines.append(f"**Why:** {t['reason']}\n")
        print(f"  🔴 Non-negotiable: {t['term'][:50]}")

    lines.extend(["---\n", "## 🟡 NEGOTIABLE TERMS\n"])
    for t in SETTLEMENT_TERMS['negotiable']:
        lines.append(f"### {t['term']}")
        lines.append(f"**Ideal:** {t['ideal']}")
        lines.append(f"**Compromise:** {t['compromise']}")
        lines.append(f"**Why flexible:** {t['reason']}\n")

    lines.extend(["---\n", "## 🚫 WALK-AWAY TRIGGERS\n",
                   "If ANY of these appear in a proposed settlement, **WALK AWAY:**\n"])
    for wa in SETTLEMENT_TERMS['walk_away']:
        lines.append(f"- ❌ {wa}")

    lines.extend(["", "---\n", "## 💪 YOUR LEVERAGE POINTS\n"])
    for lp in SETTLEMENT_TERMS['leverage_points']:
        lines.append(f"- 🎯 {lp}")

    total = (len(SETTLEMENT_TERMS['non_negotiable']) + len(SETTLEMENT_TERMS['negotiable']) +
             len(SETTLEMENT_TERMS['walk_away']) + len(SETTLEMENT_TERMS['leverage_points']))

    lines.extend(["", "---\n",
        f"*{total} total terms/points · Know before any negotiation*"])

    md_path = REPORTS_DIR / "SETTLEMENT_FRAMEWORK.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')

    json_path = REPORTS_DIR / "settlement_framework.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Settlement Negotiation Framework (#155)',
        'non_negotiable': len(SETTLEMENT_TERMS['non_negotiable']),
        'negotiable': len(SETTLEMENT_TERMS['negotiable']),
        'walk_away_triggers': len(SETTLEMENT_TERMS['walk_away']),
        'leverage_points': len(SETTLEMENT_TERMS['leverage_points']),
    }, indent=2), encoding='utf-8')

    print(f"\n✅ {total} settlement terms and leverage points")
    print(f"   Reports: SETTLEMENT_FRAMEWORK.md + settlement_framework.json")

if __name__ == '__main__':
    main()
