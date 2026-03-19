#!/usr/bin/env python3
"""
Tool #176 — Contempt Motion Builder
=================================================
🆕 NOVEL TOOL — Templates for filing contempt motions
when Emily violates court orders (parenting time,
contact provisions, discovery obligations).
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

CONTEMPT_TYPES = [
    {
        'type': 'Civil Contempt — Parenting Time Denial',
        'rule': 'MCL 600.1701 / MCR 3.208',
        'elements': [
            'A valid court order existed granting parenting time',
            'The order was clear and unambiguous',
            'Defendant had knowledge of the order',
            'Defendant willfully violated the order',
            'Plaintiff was deprived of parenting time',
        ],
        'remedies': [
            'Make-up parenting time (MCL 722.27a(7)(a))',
            'Modify custody (MCL 722.27a(7)(b))',
            'Hold Emily in contempt with purge conditions',
            'Attorney fees / costs (MCL 722.27a(7)(c))',
            'Community service (MCL 722.27a(7)(d))',
        ],
        'evidence_needed': [
            'Copy of court order granting parenting time',
            'Documentation of each denied visit (dates, communications)',
            'Proof of Andrew\'s attempts to exercise parenting time',
            'Proof Emily received/knows about the order',
        ],
    },
    {
        'type': 'Civil Contempt — Discovery Violations',
        'rule': 'MCR 2.313(B)',
        'elements': [
            'Discovery requests were properly served',
            'Deadline to respond has passed (28 days + service time)',
            'Defendant failed to respond or responded inadequately',
            'Good faith attempt to resolve was made',
        ],
        'remedies': [
            'Order compelling responses (MCR 2.313(A))',
            'Expenses of motion (MCR 2.313(A)(4))',
            'Facts deemed admitted (MCR 2.313(B)(2)(a))',
            'Striking pleadings (MCR 2.313(B)(2)(c))',
            'Default judgment (MCR 2.313(B)(2)(c)) — nuclear option',
        ],
        'evidence_needed': [
            'Copy of discovery requests served',
            'Proof of service (certified mail receipt)',
            'Documentation of non-response or inadequate response',
            'Good faith letter/email requesting compliance',
        ],
    },
    {
        'type': 'Civil Contempt — Violation of PPO Terms',
        'rule': 'MCL 600.2950 / MCR 3.708',
        'elements': [
            'A valid PPO existed',
            'The contemnor violated a specific provision',
            'The violation was willful',
        ],
        'remedies': [
            'Criminal contempt (up to 93 days jail)',
            'Civil sanctions',
            'Modification or termination of PPO',
        ],
        'evidence_needed': [
            'Copy of PPO',
            'Specific provision violated',
            'Evidence of violation (communications, witness testimony)',
        ],
    },
]

def main():
    print("=" * 70)
    print("CONTEMPT MOTION BUILDER — Tool #176")
    print("=" * 70)

    lines = [
        "# ⚖️ CONTEMPT MOTION BUILDER",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #176*",
        f"*{len(CONTEMPT_TYPES)} contempt types with elements, remedies, and evidence*\n",
        "---\n",
        "> **Contempt is your enforcement tool. When Emily violates a court order,**",
        "> **this is how you hold her accountable.**\n",
    ]

    total_elements = 0
    total_remedies = 0
    for ct in CONTEMPT_TYPES:
        lines.append(f"## {ct['type']}")
        lines.append(f"**Rule:** {ct['rule']}\n")

        lines.append("### Elements to Prove")
        for e in ct['elements']:
            lines.append(f"1. {e}")
        
        lines.append("\n### Available Remedies")
        for r in ct['remedies']:
            lines.append(f"- ⚖️ {r}")

        lines.append("\n### Evidence Needed")
        for ev in ct['evidence_needed']:
            lines.append(f"- 📎 {ev}")

        lines.append("\n---\n")
        total_elements += len(ct['elements'])
        total_remedies += len(ct['remedies'])
        print(f"  ⚖️ {ct['type']}: {len(ct['elements'])} elements, {len(ct['remedies'])} remedies")

    lines.append(f"*{len(CONTEMPT_TYPES)} types · {total_elements} elements · {total_remedies} remedies*")

    md_path = REPORTS_DIR / "CONTEMPT_MOTION_BUILDER.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')

    json_path = REPORTS_DIR / "contempt_motion_builder.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Contempt Motion Builder (#176)',
        'types': len(CONTEMPT_TYPES),
        'total_elements': total_elements,
        'total_remedies': total_remedies,
    }, indent=2), encoding='utf-8')

    print(f"\n✅ {len(CONTEMPT_TYPES)} contempt types, {total_elements} elements, {total_remedies} remedies")
    print(f"   Reports: CONTEMPT_MOTION_BUILDER.md + contempt_motion_builder.json")

if __name__ == '__main__':
    main()
