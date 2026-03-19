#!/usr/bin/env python3
"""
Tool #167 — Filing Cost & Fee Calculator
=================================================
🆕 NOVEL TOOL — Calculates exact filing fees for every
court and motion type, plus IFP savings.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

FEE_SCHEDULE = [
    {
        'filing': 'F1 — Emergency Parenting Time',
        'court': '14th Circuit Court',
        'fee': 20,
        'fee_type': 'Motion filing fee',
        'ifp_waivable': True,
        'notes': 'MCL 600.880 — motion fee. IFP waiver via MC 20.',
    },
    {
        'filing': 'F2 — Fraud Upon the Court',
        'court': '14th Circuit Court',
        'fee': 20,
        'fee_type': 'Motion filing fee',
        'ifp_waivable': True,
        'notes': 'MCR 2.612 motion. Same case, motion fee only.',
    },
    {
        'filing': 'F3 — Disqualification Motion',
        'court': '14th Circuit Court (Chief Judge)',
        'fee': 0,
        'fee_type': 'No fee for disqualification motions',
        'ifp_waivable': False,
        'notes': 'MCR 2.003 — no separate fee. Filed in existing case.',
    },
    {
        'filing': 'F4 — Federal §1983',
        'court': 'USDC Western District MI',
        'fee': 405,
        'fee_type': 'Federal civil filing fee',
        'ifp_waivable': True,
        'notes': '28 USC 1914. IFP via 28 USC 1915. Need financial affidavit.',
    },
    {
        'filing': 'F5 — MSC Application',
        'court': 'Michigan Supreme Court',
        'fee': 375,
        'fee_type': 'Application for leave filing fee',
        'ifp_waivable': True,
        'notes': 'MCR 7.305(C). IFP via MC 20 or MSC specific form.',
    },
    {
        'filing': 'F6 — JTC Complaint',
        'court': 'Judicial Tenure Commission',
        'fee': 0,
        'fee_type': 'No fee for JTC complaints',
        'ifp_waivable': False,
        'notes': 'JTC complaints are free. Administrative process.',
    },
    {
        'filing': 'F7 — Custody Modification',
        'court': '14th Circuit Court',
        'fee': 20,
        'fee_type': 'Motion filing fee',
        'ifp_waivable': True,
        'notes': 'Motion to change custody within existing case.',
    },
    {
        'filing': 'F8 — COA Leave to Appeal',
        'court': 'Court of Appeals',
        'fee': 375,
        'fee_type': 'Application for leave to appeal',
        'ifp_waivable': True,
        'notes': 'MCR 7.205(C). IFP via MC 20.',
    },
    {
        'filing': 'F9 — COA Brief',
        'court': 'Court of Appeals',
        'fee': 0,
        'fee_type': 'No additional fee (part of appeal)',
        'ifp_waivable': False,
        'notes': 'Brief filing is part of the appeal — no separate fee.',
    },
    {
        'filing': 'F10 — AG Complaint',
        'court': 'Attorney General',
        'fee': 0,
        'fee_type': 'No fee for AG complaints',
        'ifp_waivable': False,
        'notes': 'Administrative complaint — free.',
    },
]

ADDITIONAL_COSTS = [
    {'item': 'Certified copies (per page)', 'cost': 1.00, 'source': 'Court clerk'},
    {'item': 'Certified copy of order', 'cost': 10.00, 'source': 'Court clerk'},
    {'item': 'Personal service (process server)', 'cost': 50.00, 'source': 'Private process server'},
    {'item': 'Certified mail with return receipt', 'cost': 8.00, 'source': 'USPS'},
    {'item': 'Notarization per signature', 'cost': 10.00, 'source': 'UPS Store / bank (free at some banks)'},
    {'item': 'Mileage to courthouse (round trip)', 'cost': 25.00, 'source': 'IRS rate × ~35 miles RT'},
    {'item': 'Parking at courthouse', 'cost': 5.00, 'source': 'Metered/lot'},
    {'item': 'Printing costs (per filing ~50 pages × 4 copies)', 'cost': 20.00, 'source': 'Library / home printer'},
]

def main():
    print("=" * 70)
    print("FILING COST & FEE CALCULATOR — Tool #167")
    print("=" * 70)

    total_fees = sum(f['fee'] for f in FEE_SCHEDULE)
    waivable = sum(f['fee'] for f in FEE_SCHEDULE if f['ifp_waivable'])
    out_of_pocket = total_fees - waivable

    lines = [
        "# 💰 FILING COST & FEE CALCULATOR",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #167*\n",
        "---\n",
        "## FILING FEES\n",
        "| Filing | Court | Fee | IFP Waivable |",
        "|--------|-------|-----|-------------|",
    ]

    for f in FEE_SCHEDULE:
        waiver = "✅ Yes" if f['ifp_waivable'] else "—"
        lines.append(f"| {f['filing']} | {f['court']} | ${f['fee']:,.0f} | {waiver} |")
        status = "IFP WAIVED" if f['ifp_waivable'] and f['fee'] > 0 else ("FREE" if f['fee'] == 0 else "")
        print(f"  💰 {f['filing']}: ${f['fee']:,.0f} {status}")

    lines.extend([
        "",
        f"**Total Filing Fees:** ${total_fees:,.0f}",
        f"**IFP Waivable:** ${waivable:,.0f}",
        f"**Out of Pocket (with IFP):** ${out_of_pocket:,.0f}",
        f"**IFP SAVINGS: ${waivable:,.0f}**\n",
        "---\n",
        "## ADDITIONAL COSTS (Estimated)\n",
        "| Item | Est. Cost | Source |",
        "|------|-----------|--------|",
    ])

    additional_total = 0
    for cost in ADDITIONAL_COSTS:
        lines.append(f"| {cost['item']} | ${cost['cost']:.2f} | {cost['source']} |")
        additional_total += cost['cost']

    lines.extend([
        "",
        f"**Estimated Additional Costs:** ${additional_total:.2f} per filing trip\n",
        "---\n",
        "## 🎯 COST REDUCTION STRATEGIES\n",
        "1. **File IFP FIRST** — MC 20 form waives most fees",
        "2. **Use email service** where permitted — saves postage + process server",
        "3. **Print at library** — cheaper than home printing",
        "4. **Batch filings** — one trip, multiple filings",
        "5. **Free notarization** — check your bank (many offer free notary)\n",
        f"*${total_fees:,.0f} total fees · ${waivable:,.0f} waivable via IFP · File IFP form FIRST*",
    ])

    md_path = REPORTS_DIR / "FILING_COSTS.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')

    json_path = REPORTS_DIR / "filing_costs.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Filing Cost & Fee Calculator (#167)',
        'total_fees': total_fees,
        'ifp_waivable': waivable,
        'out_of_pocket': out_of_pocket,
        'additional_per_trip': additional_total,
    }, indent=2), encoding='utf-8')

    print(f"\n✅ ${total_fees:,.0f} total fees | ${waivable:,.0f} IFP savings | ${out_of_pocket:,.0f} out of pocket")
    print(f"   Reports: FILING_COSTS.md + filing_costs.json")

if __name__ == '__main__':
    main()
