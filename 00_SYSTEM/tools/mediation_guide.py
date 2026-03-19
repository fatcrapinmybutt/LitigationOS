#!/usr/bin/env python3
"""
Tool #148 — Mediation Preparation Guide
=================================================
🆕 NOVEL TOOL — Prepare Andrew for court-ordered or
voluntary mediation. Courts prefer mediation in
custody cases and may order it before trial.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

MEDIATION_GUIDE = {
    'what_is_mediation': [
        'Confidential process where a neutral mediator helps parties reach agreement',
        'NOT binding unless both parties agree to the result',
        'Michigan courts frequently order mediation in custody cases (MCR 3.216)',
        'Mediator CANNOT force a decision — they only facilitate discussion',
        'If mediation fails, case proceeds to hearing (no penalty for failure)',
    ],
    'preparation_steps': [
        'Review all parenting plan proposals (Tool #139) — know your ideal, compromise, and floor',
        'Prepare a 2-page case summary highlighting key facts only',
        'Practice stating your position in 3 minutes or less',
        'List your top 3 non-negotiable items (seeing L.D.W. regularly is #1)',
        'List 5 things you are willing to compromise on',
        'Bring copies of relevant court orders and your parenting proposals',
        'Dress professionally — first impressions matter even in mediation',
    ],
    'dos': [
        'DO be calm, respectful, and solution-oriented',
        'DO focus on L.D.W.\'s best interests (not your grievances)',
        'DO listen to Emily\'s position without interrupting',
        'DO propose specific, detailed solutions (not vague requests)',
        'DO acknowledge what Emily does well as a parent (if applicable)',
        'DO take notes on everything discussed',
        'DO ask for a written summary of any agreement',
    ],
    'donts': [
        'DON\'T bring up past grievances or argue about who was wrong',
        'DON\'T get emotional or raise your voice',
        'DON\'T agree to anything you can\'t live with long-term',
        'DON\'T discuss the mediation content in court (it\'s confidential)',
        'DON\'T sign anything without reading it carefully',
        'DON\'T badmouth Emily to the mediator',
        'DON\'T bring up the disqualification or fraud cases in mediation',
    ],
    'negotiation_positions': [
        {
            'issue': 'Parenting Time Schedule',
            'ideal': 'Primary custody or 50/50 (Plans A or B)',
            'compromise': 'Expanded parenting time — every other weekend + Wednesday + one weeknight',
            'floor': 'Current schedule PLUS make-up time for denied visits',
        },
        {
            'issue': 'Communication with L.D.W.',
            'ideal': 'Daily phone/video at consistent time',
            'compromise': 'Every other day phone/video',
            'floor': 'Minimum 3x per week phone contact',
        },
        {
            'issue': 'Decision Making',
            'ideal': 'Joint legal custody (shared major decisions)',
            'compromise': 'Joint legal with Emily as tiebreaker for education only',
            'floor': 'Information sharing rights + consultation before major decisions',
        },
        {
            'issue': 'Exchange Protocol',
            'ideal': 'Neutral public location, both parents present',
            'compromise': 'School/daycare as exchange point',
            'floor': 'Third-party exchange if needed',
        },
    ],
}

def main():
    print("=" * 70)
    print("MEDIATION PREPARATION GUIDE — Tool #148")
    print("=" * 70)

    lines = [
        "# 🤝 MEDIATION PREPARATION GUIDE",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #148*",
        f"*Be prepared if the court orders mediation — it often happens first*\n",
        "---\n",
    ]

    lines.append("## What Is Mediation?\n")
    for item in MEDIATION_GUIDE['what_is_mediation']:
        lines.append(f"- {item}")

    lines.extend(["", "---\n", "## Preparation Steps\n"])
    for i, step in enumerate(MEDIATION_GUIDE['preparation_steps'], 1):
        lines.append(f"{i}. {step}")

    lines.extend(["", "---\n", "## ✅ DO:\n"])
    for item in MEDIATION_GUIDE['dos']:
        lines.append(f"- {item}")

    lines.extend(["", "## ❌ DON'T:\n"])
    for item in MEDIATION_GUIDE['donts']:
        lines.append(f"- {item}")

    lines.extend(["", "---\n", "## NEGOTIATION POSITIONS\n",
                   "| Issue | Ideal | Compromise | Floor |",
                   "|-------|-------|-----------|-------|"])

    for pos in MEDIATION_GUIDE['negotiation_positions']:
        lines.append(f"| {pos['issue']} | {pos['ideal'][:30]} | {pos['compromise'][:30]} | {pos['floor'][:30]} |")
        print(f"  🤝 {pos['issue']}: {pos['ideal'][:40]}")

    lines.extend(["", "---\n"])
    for pos in MEDIATION_GUIDE['negotiation_positions']:
        lines.append(f"### {pos['issue']}")
        lines.append(f"- **Ideal:** {pos['ideal']}")
        lines.append(f"- **Compromise:** {pos['compromise']}")
        lines.append(f"- **Floor (minimum acceptable):** {pos['floor']}\n")

    total_items = (len(MEDIATION_GUIDE['dos']) + len(MEDIATION_GUIDE['donts']) +
                   len(MEDIATION_GUIDE['preparation_steps']) + len(MEDIATION_GUIDE['negotiation_positions']))

    lines.append(f"*{total_items} items · 4 negotiation positions · Review before mediation*")

    md_path = REPORTS_DIR / "MEDIATION_GUIDE.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')

    json_path = REPORTS_DIR / "mediation_guide.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Mediation Preparation Guide (#148)',
        'total_items': total_items,
        'positions': len(MEDIATION_GUIDE['negotiation_positions']),
    }, indent=2), encoding='utf-8')

    print(f"\n✅ {total_items} preparation items + {len(MEDIATION_GUIDE['negotiation_positions'])} negotiation positions")
    print(f"   Reports: MEDIATION_GUIDE.md + mediation_guide.json")

if __name__ == '__main__':
    main()
