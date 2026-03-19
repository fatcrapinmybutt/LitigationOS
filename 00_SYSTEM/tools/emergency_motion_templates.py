#!/usr/bin/env python3
"""
Tool #173 — Emergency Motion Templates
=================================================
🆕 NOVEL TOOL — Pre-drafted emergency motion shells
for time-sensitive situations. Fill in the blanks
and file within hours, not days.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

EMERGENCY_TEMPLATES = [
    {
        'title': 'Emergency Motion to Restore Parenting Time',
        'trigger': 'Emily unilaterally suspends/blocks contact with L.D.W.',
        'urgency': 'CRITICAL — file same day',
        'rule': 'MCR 3.207(B) — 2 business day notice unless immediate danger',
        'sections': [
            'Caption + Case No. 2024-001507-DC',
            'Statement of Emergency: "On [DATE], Defendant [specific action blocking contact]"',
            'Statutory basis: MCL 722.27a — parenting time shall be granted',
            'No finding of endangerment exists to justify suspension',
            'Request: Immediate order restoring parenting time on [specific schedule]',
            'Proposed order attached',
        ],
    },
    {
        'title': 'Emergency Motion for Protective Order (Evidence Destruction)',
        'trigger': 'Evidence that Emily is destroying/deleting relevant records',
        'urgency': 'HIGH — file within 24 hours',
        'rule': 'MCR 2.313(B) — spoliation sanctions',
        'sections': [
            'Caption + Case No.',
            'Statement: "Plaintiff has reason to believe Defendant is destroying [specific evidence]"',
            'Preservation demand was sent on [DATE] via certified mail',
            'Court has inherent authority to prevent spoliation',
            'Request: Order prohibiting destruction + forensic examination if needed',
        ],
    },
    {
        'title': 'Emergency Motion to Stay Enforcement of Order',
        'trigger': 'Adverse order entered that must be challenged immediately',
        'urgency': 'HIGH — file within 48 hours',
        'rule': 'MCR 7.209 — stay pending appeal',
        'sections': [
            'Caption + Case No.',
            'Identify specific order to be stayed',
            'Likelihood of success on appeal (cite strongest argument)',
            'Irreparable harm if not stayed (loss of parental bond)',
            'Balance of equities (child needs both parents)',
            'Public interest (children benefit from both parents)',
        ],
    },
    {
        'title': 'Emergency Ex Parte Motion (Child Safety)',
        'trigger': 'Genuine safety concern for L.D.W.',
        'urgency': 'CRITICAL — file immediately',
        'rule': 'MCR 3.207(B)(3) — ex parte if irreparable injury',
        'sections': [
            'Caption + Case No.',
            'Affidavit of facts supporting emergency (SWORN)',
            'Specific, articulable safety concern',
            'Why notice to opposing party is impractical',
            'Temporary relief requested (specific, narrow)',
            'Request for full hearing within 14 days',
        ],
    },
]

def main():
    print("=" * 70)
    print("EMERGENCY MOTION TEMPLATES — Tool #173")
    print("=" * 70)

    lines = [
        "# 🚨 EMERGENCY MOTION TEMPLATES",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #173*",
        f"*{len(EMERGENCY_TEMPLATES)} emergency templates — fill in blanks and file FAST*\n",
        "---\n",
        "> **These are pre-built shells. When an emergency hits:**",
        "> **1. Choose the right template**",
        "> **2. Fill in the [BRACKETS]**",
        "> **3. File within hours**\n",
    ]

    total_sections = 0
    for tmpl in EMERGENCY_TEMPLATES:
        lines.append(f"## 🚨 {tmpl['title']}")
        lines.append(f"**Trigger:** {tmpl['trigger']}")
        lines.append(f"**Urgency:** {tmpl['urgency']}")
        lines.append(f"**Rule:** {tmpl['rule']}\n")
        lines.append("**Sections to Include:**")
        for i, sec in enumerate(tmpl['sections'], 1):
            lines.append(f"{i}. {sec}")
        lines.append("")
        lines.append("---\n")
        total_sections += len(tmpl['sections'])
        print(f"  🚨 {tmpl['title']}: {tmpl['urgency']}")

    lines.append(f"*{len(EMERGENCY_TEMPLATES)} templates · {total_sections} sections · Ready to deploy in hours*")

    md_path = REPORTS_DIR / "EMERGENCY_MOTION_TEMPLATES.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')

    json_path = REPORTS_DIR / "emergency_motion_templates.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Emergency Motion Templates (#173)',
        'templates': len(EMERGENCY_TEMPLATES),
        'total_sections': total_sections,
    }, indent=2), encoding='utf-8')

    print(f"\n✅ {len(EMERGENCY_TEMPLATES)} emergency templates with {total_sections} sections")
    print(f"   Reports: EMERGENCY_MOTION_TEMPLATES.md + emergency_motion_templates.json")

if __name__ == '__main__':
    main()
