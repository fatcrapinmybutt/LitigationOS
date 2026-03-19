#!/usr/bin/env python3
"""
Tool #105 — IFP (In Forma Pauperis) Application Generator
=============================================================
🆕 NOVEL TOOL — Poverty affidavit assistance

Generates the framework for IFP applications across all courts:
- State court (MCR 2.002)
- Federal court (28 USC 1915)
- COA (MCR 7.002)
- MSC (MCR 7.002)

Includes:
- Required financial disclosures
- Income/expense framework
- Legal standard for IFP
- Filing fee waiver amounts
- Which filings benefit from IFP

This could save Andrew $1,505+ in filing fees.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

IFP_FILINGS = {
    'F1': {'name': 'Emergency Parenting Time', 'court': 'State', 'fee': 175, 'ifp_saves': 175, 'form': 'MC 20'},
    'F2': {'name': 'Fraud on Court', 'court': 'State', 'fee': 175, 'ifp_saves': 175, 'form': 'MC 20'},
    'F3': {'name': 'Judicial Disqualification', 'court': 'State', 'fee': 0, 'ifp_saves': 0, 'form': 'N/A (no fee)'},
    'F4': {'name': '§1983 Federal', 'court': 'Federal', 'fee': 405, 'ifp_saves': 405, 'form': 'AO 240'},
    'F5': {'name': 'MSC Superintending', 'court': 'MSC', 'fee': 375, 'ifp_saves': 375, 'form': 'MC 20'},
    'F6': {'name': 'JTC Complaint', 'court': 'JTC', 'fee': 0, 'ifp_saves': 0, 'form': 'N/A (free)'},
    'F7': {'name': 'Custody Modification', 'court': 'State', 'fee': 175, 'ifp_saves': 175, 'form': 'MC 20'},
    'F8': {'name': 'COA Leave', 'court': 'COA', 'fee': 375, 'ifp_saves': 375, 'form': 'MC 20'},
    'F9': {'name': 'COA Brief', 'court': 'COA', 'fee': 0, 'ifp_saves': 0, 'form': 'N/A (already filed)'},
    'F10': {'name': 'AGC Grievance', 'court': 'AGC', 'fee': 0, 'ifp_saves': 0, 'form': 'N/A (free)'},
}

IFP_STANDARDS = {
    'State (MCR 2.002)': {
        'standard': 'Unable to pay fees/costs without depriving self or family of necessities',
        'factors': [
            'Employment status and income',
            'Assets (real property, vehicles, savings)',
            'Monthly expenses vs income',
            'Number of dependents',
            'Receipt of public assistance (Medicaid, food stamps, SSI)',
            'Nature of the action (custody = favored for IFP)',
        ],
        'form': 'MC 20 — Fee Waiver Request',
        'auto_qualify': 'Receiving public assistance = automatic qualification',
    },
    'Federal (28 USC 1915)': {
        'standard': 'Unable to pay filing fee without undue hardship',
        'factors': [
            'Gross and net monthly income',
            'All sources of income',
            'Monthly expenses (rent, utilities, food, medical)',
            'Debts and obligations',
            'Assets and property',
            'Dependents',
        ],
        'form': 'AO 240 — Application to Proceed In Forma Pauperis',
        'auto_qualify': 'Income below 150% federal poverty line strongly favors IFP',
    },
    'COA/MSC (MCR 7.002)': {
        'standard': 'Same as state court — MCR 2.002 applies to appellate courts',
        'factors': ['Same as State (MCR 2.002)'],
        'form': 'MC 20 — same form for all Michigan courts',
        'auto_qualify': 'Same as state court',
    },
}

def main():
    print("=" * 70)
    print("IFP APPLICATION GENERATOR — Tool #105")
    print("=" * 70)
    
    total_fees = sum(f['fee'] for f in IFP_FILINGS.values())
    total_savings = sum(f['ifp_saves'] for f in IFP_FILINGS.values())
    
    lines = [
        "# 💸 IN FORMA PAUPERIS (IFP) APPLICATION GUIDE",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #105*\n",
        "---\n",
        f"## 💰 POTENTIAL SAVINGS: **${total_savings:,}** out of ${total_fees:,} total fees\n",
        
        "## Fee Waiver Matrix\n",
        "| Filing | Court | Fee | IFP Saves | Form |",
        "|--------|-------|-----|-----------|------|",
    ]
    
    for fid in ['F1','F2','F3','F4','F5','F6','F7','F8','F9','F10']:
        f = IFP_FILINGS[fid]
        saves = f"**${f['ifp_saves']}**" if f['ifp_saves'] > 0 else "—"
        lines.append(f"| {fid} ({f['name'][:20]}) | {f['court']} | ${f['fee']} | {saves} | {f['form']} |")
        
        if f['ifp_saves'] > 0:
            print(f"  {fid}: ${f['fee']} fee → IFP saves ${f['ifp_saves']} ({f['form']})")
        else:
            print(f"  {fid}: ${f['fee']} — {'free filing' if f['fee'] == 0 else 'no IFP needed'}")
    
    lines.append(f"\n**Total without IFP: ${total_fees:,}** | **With IFP: ${total_fees - total_savings:,}** | **Savings: ${total_savings:,}**\n")
    
    # Standards by court
    for court, data in IFP_STANDARDS.items():
        lines.extend([
            f"## {court}\n",
            f"**Standard:** {data['standard']}\n",
            f"**Form:** {data['form']}\n",
            f"**Auto-qualify:** {data['auto_qualify']}\n",
            "**Factors considered:**",
        ])
        for factor in data['factors']:
            lines.append(f"- {factor}")
        lines.append("")
    
    # Financial affidavit template
    lines.extend([
        "---",
        "## 📋 FINANCIAL INFORMATION NEEDED\n",
        "Andrew must gather these for the IFP application:\n",
        "### Income",
        "- [ ] Employment status and employer",
        "- [ ] Monthly gross income",
        "- [ ] Monthly net income (after taxes)",
        "- [ ] Any other income sources (disability, SSI, unemployment)",
        "- [ ] Public assistance received (Medicaid, SNAP, etc.)",
        "",
        "### Expenses",
        "- [ ] Rent/mortgage payment",
        "- [ ] Utilities (electric, gas, water, phone)",
        "- [ ] Food/groceries",
        "- [ ] Transportation (car payment, insurance, gas)",
        "- [ ] Medical expenses",
        "- [ ] Child support payments",
        "- [ ] Insurance (health, car)",
        "- [ ] Debts (credit cards, loans)",
        "",
        "### Assets",
        "- [ ] Bank account balances",
        "- [ ] Vehicle value",
        "- [ ] Real property",
        "- [ ] Other assets (retirement, investments)",
        "",
        "## ⚠️ IMPORTANT NOTES\n",
        "1. IFP applications are sworn under oath — must be truthful",
        "2. Court may verify information",
        "3. IFP can be revoked if financial situation changes",
        "4. Federal IFP (F4) has separate process — AO 240 form",
        "5. File IFP application WITH the first filing in each court",
        "",
        f"*IFP Application Generator — Tool #105 — saves ${total_savings:,}*",
    ])
    
    md_path = REPORTS_DIR / "IFP_GUIDE.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "ifp_guide.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'IFP Application Generator (#105)',
        'total_fees': total_fees,
        'total_savings': total_savings,
        'net_cost_with_ifp': total_fees - total_savings,
        'filings': IFP_FILINGS,
    }, indent=2), encoding='utf-8')
    
    print(f"\n  💸 Total fees: ${total_fees:,}")
    print(f"  💰 IFP saves: ${total_savings:,}")
    print(f"  ✅ Net cost with IFP: ${total_fees - total_savings:,}")
    print(f"   Reports: IFP_GUIDE.md + ifp_guide.json")

if __name__ == '__main__':
    main()
