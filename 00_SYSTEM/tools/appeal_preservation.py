#!/usr/bin/env python3
"""
Tool #172 — Appeal Preservation Checklist
=================================================
🆕 NOVEL TOOL — Ensures every issue is properly
preserved for appeal at EVERY hearing.
If you don't preserve it, you can't appeal it.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

PRESERVATION_ITEMS = [
    {
        'category': 'Before Every Hearing',
        'items': [
            {'action': 'File written motion/brief', 'why': 'Creates paper trail for appellate record', 'rule': 'MCR 2.119'},
            {'action': 'Request court reporter/transcript', 'why': 'Without transcript, no appellate review', 'rule': 'MCR 7.210(B)'},
            {'action': 'Prepare written proposed order', 'why': 'Shows exactly what you asked for', 'rule': 'MCR 2.602'},
        ],
    },
    {
        'category': 'During Hearing — Objections',
        'items': [
            {'action': 'Object to EVERY improper ruling ON THE RECORD', 'why': 'Unpreserved errors are reviewed for plain error only', 'rule': 'MRE 103(a)'},
            {'action': 'State specific legal basis for objection', 'why': '"Objection" alone is insufficient', 'rule': 'MRE 103(a)(1)'},
            {'action': 'Request a continuing objection if issue recurs', 'why': 'Avoids repeated objections on same issue', 'rule': 'MRE 103(b)'},
            {'action': 'Make offer of proof for excluded evidence', 'why': 'COA can\'t review without knowing what was excluded', 'rule': 'MRE 103(a)(2)'},
        ],
    },
    {
        'category': 'During Hearing — Constitutional Issues',
        'items': [
            {'action': 'Raise due process objection specifically', 'why': 'Constitutional errors require specific objection', 'rule': '14th Amend / Const 1963 art 1 §17'},
            {'action': 'Cite Troxel v Granville for parental rights', 'why': 'Fundamental right — strict scrutiny applies', 'rule': '530 US 57 (2000)'},
            {'action': 'Object to lack of evidentiary hearing', 'why': 'Mathews v Eldridge due process requires hearing', 'rule': '424 US 319 (1976)'},
            {'action': 'Note for record: no counsel provided despite complexity', 'why': 'Preserves potential ineffective assistance claim if relevant', 'rule': 'Turner v Rogers 564 US 431'},
        ],
    },
    {
        'category': 'After Adverse Ruling',
        'items': [
            {'action': 'State for the record: "I object to this ruling"', 'why': 'Preserves the issue', 'rule': 'MCR 2.517'},
            {'action': 'Request specific findings of fact', 'why': 'COA reviews findings for clear error', 'rule': 'MCR 2.517(A)'},
            {'action': 'File motion for reconsideration within 21 days', 'why': 'Some issues require reconsideration before appeal', 'rule': 'MCR 2.119(F)'},
            {'action': 'Order transcript within 14 days', 'why': 'Transcript deadline is jurisdictional for appeal', 'rule': 'MCR 7.210(B)(3)'},
            {'action': 'File claim of appeal within 21 days (if final order)', 'why': '21-day deadline is JURISDICTIONAL', 'rule': 'MCR 7.204(A)'},
        ],
    },
    {
        'category': 'Magic Words for the Record',
        'items': [
            {'action': '"For the record, I preserve this issue for appeal"', 'why': 'Explicit preservation statement', 'rule': 'Best practice'},
            {'action': '"I object on due process grounds under the 14th Amendment"', 'why': 'Constitutional preservation', 'rule': 'US Const Amend XIV'},
            {'action': '"I request findings of fact and conclusions of law"', 'why': 'Required for meaningful appellate review', 'rule': 'MCR 2.517(A)'},
            {'action': '"I note my objection to proceeding without [X]"', 'why': 'Preserves procedural objection', 'rule': 'Various'},
        ],
    },
]

def main():
    print("=" * 70)
    print("APPEAL PRESERVATION CHECKLIST — Tool #172")
    print("=" * 70)

    lines = [
        "# 🛡️ APPEAL PRESERVATION CHECKLIST",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #172*",
        f"*If you don\'t preserve it, you CAN\'T appeal it*\n",
        "---\n",
        "> **THE #1 MISTAKE pro se litigants make on appeal:**",
        "> **Failing to object at the trial level.**",
        "> **An unpreserved error is reviewed ONLY for plain error — nearly impossible to win.**\n",
    ]

    total_items = 0
    for cat in PRESERVATION_ITEMS:
        lines.append(f"## {cat['category']}\n")
        lines.append("| Action | Why | Rule |")
        lines.append("|--------|-----|------|")
        for item in cat['items']:
            lines.append(f"| {item['action']} | {item['why']} | {item['rule']} |")
        lines.append("")
        total_items += len(cat['items'])
        print(f"  🛡️ {cat['category']}: {len(cat['items'])} items")

    lines.extend([
        "---\n",
        f"*{len(PRESERVATION_ITEMS)} categories · {total_items} preservation items*",
        f"*Print this. Bring it to EVERY hearing. Check off as you go.*",
    ])

    md_path = REPORTS_DIR / "APPEAL_PRESERVATION.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')

    json_path = REPORTS_DIR / "appeal_preservation.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Appeal Preservation Checklist (#172)',
        'categories': len(PRESERVATION_ITEMS),
        'total_items': total_items,
    }, indent=2), encoding='utf-8')

    print(f"\n✅ {len(PRESERVATION_ITEMS)} categories, {total_items} preservation items")
    print(f"   Reports: APPEAL_PRESERVATION.md + appeal_preservation.json")

if __name__ == '__main__':
    main()
