#!/usr/bin/env python3
"""
Tool #154 — Pro Se Survival Kit
=================================================
🆕 NOVEL TOOL — Everything Andrew needs to physically
bring to the courthouse. The ultimate "go bag" checklist.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

CATEGORIES = [
    {
        'name': '📁 FILING DOCUMENTS',
        'items': [
            'Original motion/filing (signed)',
            '3 copies of everything (court + opposing + your working copy)',
            'IFP application (MC 20) if needed',
            'Proof of service (with certificate)',
            'Proposed order (courts love when you draft one)',
        ],
    },
    {
        'name': '📋 REFERENCE MATERIALS',
        'items': [
            'Objection Reference Card (Tool #102) — LAMINATED',
            'Pro Se Rights Card (Tool #128) — LAMINATED',
            'Emergency Contacts Card (Tool #119)',
            'Legal Standards Cheat Sheet (Tool #147)',
            'Cross-Exam Scripts (Tool #145) — tabbed',
            'Hearing Simulator notes (Tool #143)',
        ],
    },
    {
        'name': '📦 EXHIBIT BOOK',
        'items': [
            'Exhibit Book (Tool #122) with tabs A-H',
            'Extra copies of each exhibit for judge and opposing',
            'Index page listing all exhibits',
            'Exhibit stickers/labels (A, B, C...)',
        ],
    },
    {
        'name': '✏️ SUPPLIES',
        'items': [
            'Legal pad (yellow) + 2 pens (blue or black ink)',
            'Highlighters (3 colors)',
            'Sticky tabs/flags for quick reference',
            'Paper clips (no staples — courts prefer unstapled copies)',
            'Folder or binder for organization',
        ],
    },
    {
        'name': '👔 PERSONAL',
        'items': [
            'Business casual or suit (NO jeans, NO t-shirts)',
            'Watch (phones must be OFF in courtroom)',
            'Water bottle (small, closed — some courts allow)',
            'Breath mints (not gum)',
            'Valid ID (driver\'s license)',
        ],
    },
    {
        'name': '📱 TECHNOLOGY',
        'items': [
            'Phone charged to 100% (turn OFF before entering courtroom)',
            'PDF copies of all filings on phone (backup)',
            'Voice recorder app ready (check if recording allowed — MCR varies)',
            'Calendar app with all deadlines',
        ],
    },
    {
        'name': '⚠️ DO NOT BRING',
        'items': [
            'Weapons of any kind (courthouse security)',
            'Emotional support people who might cause drama',
            'Young children (find childcare)',
            'Food or drinks beyond water',
            'Electronic devices that make noise',
        ],
    },
]

def main():
    print("=" * 70)
    print("PRO SE SURVIVAL KIT — Tool #154")
    print("=" * 70)

    total_items = sum(len(c['items']) for c in CATEGORIES)

    lines = [
        "# 🎒 PRO SE SURVIVAL KIT",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #154*",
        f"*{total_items} items — pack this bag the NIGHT BEFORE every court appearance*\n",
        "---\n",
    ]

    for cat in CATEGORIES:
        lines.append(f"## {cat['name']}\n")
        for item in cat['items']:
            lines.append(f"- [ ] {item}")
        lines.append("")
        print(f"  {cat['name']}: {len(cat['items'])} items")

    lines.extend([
        "---\n",
        "## ⏰ COURTHOUSE TIMELINE\n",
        "| Time | Action |",
        "|------|--------|",
        "| Night Before | Pack bag, lay out clothes, review hearing scripts |",
        "| Morning | Eat breakfast, review key points, check calendar |",
        "| 1 Hour Before | Arrive at courthouse, find parking, go through security |",
        "| 30 Min Before | Find courtroom, sit in gallery, observe proceedings |",
        "| 15 Min Before | Check in with clerk, organize papers on table |",
        "| Hearing Time | Stand when judge enters, wait to be called |",
        "| After Hearing | Get copies of any orders, note next dates, leave quietly |\n",
        f"*{total_items} items · PRINT AND USE AS CHECKLIST*",
    ])

    md_path = REPORTS_DIR / "PRO_SE_SURVIVAL_KIT.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')

    json_path = REPORTS_DIR / "pro_se_survival_kit.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Pro Se Survival Kit (#154)',
        'categories': len(CATEGORIES),
        'total_items': total_items,
    }, indent=2), encoding='utf-8')

    print(f"\n✅ {total_items} items across {len(CATEGORIES)} categories")
    print(f"   Reports: PRO_SE_SURVIVAL_KIT.md + pro_se_survival_kit.json")

if __name__ == '__main__':
    main()
