#!/usr/bin/env python3
"""
Tool #156 — Record Preservation Demand Letter
=================================================
🆕 NOVEL TOOL — Generates litigation hold / preservation
demand letters to send to Emily, Berry, Barnes, and
any third parties holding relevant evidence.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

PRESERVATION_DEMANDS = [
    {
        'recipient': 'Emily A. Watson',
        'address': '2160 Garland Drive, Norton Shores, MI 49441',
        'preserve': [
            'All text messages, emails, and social media messages to/from/about Andrew Pigors or L.D.W.',
            'All photographs and videos of L.D.W.',
            'All communications with Jennifer Barnes (P55406)',
            'All communications with Ronald T. Berry regarding custody or Andrew',
            'All financial records related to child support or household expenses',
            'All medical records for L.D.W.',
            'All school/daycare records for L.D.W.',
            'All records related to the PPO (2023-5907-PP)',
            'Phone records showing call/text history',
        ],
    },
    {
        'recipient': 'Jennifer Barnes (P55406)',
        'address': '880 Jefferson St Ste B, Muskegon, MI 49440',
        'preserve': [
            'Complete client file for Emily Watson / Pigors v. Watson',
            'All billing records',
            'All internal notes and memoranda',
            'All communications with Emily Watson',
            'All communications with the court or Judge McNeill\'s office',
            'All draft filings and discovery materials',
            'MRPC requires retention of client file for 5 years after withdrawal',
        ],
    },
    {
        'recipient': 'Ronald T. Berry',
        'address': '[ADDRESS NEEDED — Andrew to provide]',
        'preserve': [
            'All communications with Emily Watson about Andrew or L.D.W.',
            'All communications with any court, attorney, or legal entity about this case',
            'All recordings, photographs, or surveillance of Andrew',
            'All financial records showing shared expenses with Emily',
        ],
    },
]

def main():
    print("=" * 70)
    print("RECORD PRESERVATION DEMAND LETTERS — Tool #156")
    print("=" * 70)

    lines = [
        "# 📋 RECORD PRESERVATION DEMAND LETTERS",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #156*",
        f"*{len(PRESERVATION_DEMANDS)} letters — send BEFORE filing to prevent spoliation*\n",
        "---\n",
        "> **Send these letters BEFORE filing your motions.**",
        "> **They create a legal duty to preserve evidence.**",
        "> **Destruction after receiving this letter = spoliation = sanctions.**\n",
        "---\n",
    ]

    for demand in PRESERVATION_DEMANDS:
        total_items = len(demand['preserve'])
        lines.append(f"## PRESERVATION DEMAND — {demand['recipient']}")
        lines.append(f"**Address:** {demand['address']}\n")
        lines.append("---")
        lines.append(f"**Date:** {datetime.now().strftime('%B %d, %Y')}\n")
        lines.append(f"**RE: Litigation Hold and Preservation Demand**")
        lines.append(f"**Case: Pigors v. Watson, Case No. 2024-001507-DC**\n")
        lines.append(f"Dear {demand['recipient'].split('(')[0].strip()},\n")
        lines.append("You are hereby notified that litigation is pending or reasonably anticipated")
        lines.append("in the above-captioned matter. This letter constitutes a formal demand that")
        lines.append("you immediately preserve and refrain from destroying, altering, or disposing")
        lines.append("of the following documents and materials:\n")

        for i, item in enumerate(demand['preserve'], 1):
            lines.append(f"{i}. {item}")

        lines.extend([
            "",
            "**Failure to preserve these records may constitute spoliation of evidence,**",
            "**which may result in adverse inference instructions, sanctions, or separate**",
            "**legal action under Michigan law.**\n",
            "Sincerely,",
            "Andrew James Pigors",
            "1977 Whitehall Road, Lot 17",
            "North Muskegon, MI 49445",
            "(231) 903-5690\n",
            "---\n",
        ])
        print(f"  📋 {demand['recipient']}: {total_items} items to preserve")

    total_items = sum(len(d['preserve']) for d in PRESERVATION_DEMANDS)
    lines.append(f"*{len(PRESERVATION_DEMANDS)} letters · {total_items} items · Send via certified mail with return receipt*")

    md_path = REPORTS_DIR / "PRESERVATION_DEMANDS.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')

    json_path = REPORTS_DIR / "preservation_demands.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Record Preservation Demand Letters (#156)',
        'recipients': len(PRESERVATION_DEMANDS),
        'total_items': total_items,
    }, indent=2), encoding='utf-8')

    print(f"\n✅ {len(PRESERVATION_DEMANDS)} preservation demand letters with {total_items} items")
    print(f"   SEND VIA CERTIFIED MAIL WITH RETURN RECEIPT")
    print(f"   Reports: PRESERVATION_DEMANDS.md + preservation_demands.json")

if __name__ == '__main__':
    main()
