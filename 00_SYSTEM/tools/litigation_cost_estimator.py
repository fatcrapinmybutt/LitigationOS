#!/usr/bin/env python3
"""
Tool #66 — Litigation Cost Estimator
========================================
Estimates all costs associated with filing 10 actions:
- Filing fees (with IFP waiver scenarios)
- Service of process costs
- Copying/printing costs
- Mileage (court appearances)
- Miscellaneous (notarization, certified copies)

Provides: total without IFP, total with IFP, and cost-per-filing breakdown.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

# IRS mileage rate 2025
MILEAGE_RATE = 0.70  # $/mile

COSTS = {
    'F1': {
        'title': 'Emergency Parenting Time',
        'court': '14th Circuit Court',
        'filing_fee': 175.00,
        'ifp_eligible': True,
        'service': [
            {'item': 'Certified mail to Emily Watson', 'cost': 8.50},
        ],
        'copies': {'pages': 50, 'cost_per_page': 0.10},
        'mileage': {'location': 'Muskegon (990 Terrace St)', 'miles_roundtrip': 20, 'trips': 2},
        'other': [
            {'item': 'Notarization of affidavit', 'cost': 10.00},
        ],
    },
    'F2': {
        'title': 'Fraud Upon the Court',
        'court': '14th Circuit Court',
        'filing_fee': 175.00,
        'ifp_eligible': True,
        'service': [
            {'item': 'Personal service on Emily Watson (process server)', 'cost': 75.00},
            {'item': 'Certified mail to Barnes', 'cost': 8.50},
        ],
        'copies': {'pages': 80, 'cost_per_page': 0.10},
        'mileage': {'location': 'Muskegon', 'miles_roundtrip': 20, 'trips': 1},
        'other': [
            {'item': 'Summons issuance', 'cost': 0.00},
            {'item': 'Notarization', 'cost': 10.00},
        ],
    },
    'F3': {
        'title': 'Judicial Disqualification',
        'court': '14th Circuit Court',
        'filing_fee': 0.00,  # Motion in existing case — no separate fee
        'ifp_eligible': False,
        'service': [
            {'item': 'First class mail to Emily Watson', 'cost': 1.50},
        ],
        'copies': {'pages': 40, 'cost_per_page': 0.10},
        'mileage': {'location': 'Muskegon', 'miles_roundtrip': 20, 'trips': 1},
        'other': [],
    },
    'F4': {
        'title': '42 USC §1983 Federal',
        'court': 'USDC Western District MI',
        'filing_fee': 405.00,
        'ifp_eligible': True,
        'service': [
            {'item': 'US Marshals service (IFP = free)', 'cost': 0.00},
            {'item': 'Certified mail to MI AG', 'cost': 8.50},
            {'item': 'Certified mail to Berry (if served)', 'cost': 8.50},
            {'item': 'Certified mail to Barnes (if served)', 'cost': 8.50},
        ],
        'copies': {'pages': 150, 'cost_per_page': 0.10},
        'mileage': {'location': 'Grand Rapids (110 Michigan St NW)', 'miles_roundtrip': 90, 'trips': 3},
        'other': [
            {'item': 'Notarization', 'cost': 10.00},
            {'item': 'PACER fee (if not IFP)', 'cost': 0.10},
        ],
    },
    'F5': {
        'title': 'MSC Superintending Control',
        'court': 'Michigan Supreme Court',
        'filing_fee': 375.00,
        'ifp_eligible': True,
        'service': [
            {'item': 'Certified mail to Emily Watson', 'cost': 8.50},
            {'item': 'Certified mail to MSC Clerk', 'cost': 8.50},
        ],
        'copies': {'pages': 75, 'cost_per_page': 0.10},
        'mileage': {'location': 'Lansing (or TrueFiling)', 'miles_roundtrip': 0, 'trips': 0},
        'other': [],
    },
    'F6': {
        'title': 'JTC Complaint',
        'court': 'Judicial Tenure Commission',
        'filing_fee': 0.00,
        'ifp_eligible': False,
        'service': [
            {'item': 'First class mail or email (free)', 'cost': 1.50},
        ],
        'copies': {'pages': 30, 'cost_per_page': 0.10},
        'mileage': {'location': 'Mail/email (no travel)', 'miles_roundtrip': 0, 'trips': 0},
        'other': [],
    },
    'F7': {
        'title': 'Custody Modification',
        'court': '14th Circuit Court',
        'filing_fee': 0.00,  # Motion in existing case
        'ifp_eligible': False,
        'service': [
            {'item': 'Certified mail to Emily Watson', 'cost': 8.50},
        ],
        'copies': {'pages': 60, 'cost_per_page': 0.10},
        'mileage': {'location': 'Muskegon', 'miles_roundtrip': 20, 'trips': 2},
        'other': [
            {'item': 'Notarization', 'cost': 10.00},
        ],
    },
    'F8': {
        'title': 'COA Application for Leave',
        'court': 'Michigan Court of Appeals',
        'filing_fee': 375.00,
        'ifp_eligible': True,
        'service': [
            {'item': 'First class mail to Emily Watson', 'cost': 1.50},
        ],
        'copies': {'pages': 50, 'cost_per_page': 0.10},
        'mileage': {'location': 'TrueFiling (no travel)', 'miles_roundtrip': 0, 'trips': 0},
        'other': [],
    },
    'F9': {
        'title': 'COA Appeal Brief (366810)',
        'court': 'Michigan Court of Appeals',
        'filing_fee': 0.00,  # Already docketed
        'ifp_eligible': False,
        'service': [
            {'item': 'First class mail to Emily Watson', 'cost': 1.50},
        ],
        'copies': {'pages': 60, 'cost_per_page': 0.10},
        'mileage': {'location': 'TrueFiling (no travel)', 'miles_roundtrip': 0, 'trips': 0},
        'other': [],
    },
    'F10': {
        'title': 'AGC Grievance',
        'court': 'Attorney Grievance Commission',
        'filing_fee': 0.00,
        'ifp_eligible': False,
        'service': [
            {'item': 'Online submission (free) or mail', 'cost': 1.50},
        ],
        'copies': {'pages': 20, 'cost_per_page': 0.10},
        'mileage': {'location': 'Online (no travel)', 'miles_roundtrip': 0, 'trips': 0},
        'other': [],
    },
}

def calc_filing_cost(fdata, with_ifp=False):
    """Calculate total cost for a single filing."""
    fee = 0 if (with_ifp and fdata['ifp_eligible']) else fdata['filing_fee']
    service = sum(s['cost'] for s in fdata['service'])
    copies = fdata['copies']['pages'] * fdata['copies']['cost_per_page']
    mileage = fdata['mileage']['miles_roundtrip'] * fdata['mileage']['trips'] * MILEAGE_RATE
    other = sum(o['cost'] for o in fdata['other'])
    return fee, service, copies, mileage, other

def main():
    print("=" * 70)
    print("LITIGATION COST ESTIMATOR — Tool #66")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)
    
    lines = [
        "# LITIGATION COST ESTIMATE",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n",
        "## Cost Summary (Without IFP)",
        "| Filing | Title | Fee | Service | Copies | Mileage | Other | TOTAL |",
        "|--------|-------|-----|---------|--------|---------|-------|-------|",
    ]
    
    grand_total = 0
    grand_ifp = 0
    
    for fid, fdata in COSTS.items():
        fee, svc, copies, miles, other = calc_filing_cost(fdata, with_ifp=False)
        total = fee + svc + copies + miles + other
        grand_total += total
        
        fee_ifp, svc_ifp, copies_ifp, miles_ifp, other_ifp = calc_filing_cost(fdata, with_ifp=True)
        total_ifp = fee_ifp + svc_ifp + copies_ifp + miles_ifp + other_ifp
        grand_ifp += total_ifp
        
        lines.append(f"| {fid} | {fdata['title'][:25]} | ${fee:.2f} | ${svc:.2f} | ${copies:.2f} | ${miles:.2f} | ${other:.2f} | **${total:.2f}** |")
        
        print(f"  {fid}: ${total:.2f} (IFP: ${total_ifp:.2f})")
    
    lines.extend([
        f"| **TOTAL** | | | | | | | **${grand_total:.2f}** |",
        "",
        "## Cost Summary (With IFP Fee Waivers)",
        "| Filing | Title | Fee | Service | Copies | Mileage | Other | TOTAL |",
        "|--------|-------|-----|---------|--------|---------|-------|-------|",
    ])
    
    for fid, fdata in COSTS.items():
        fee, svc, copies, miles, other = calc_filing_cost(fdata, with_ifp=True)
        total = fee + svc + copies + miles + other
        ifp_note = ' *(waived)*' if fdata['ifp_eligible'] and fdata['filing_fee'] > 0 else ''
        lines.append(f"| {fid} | {fdata['title'][:25]} | ${fee:.2f}{ifp_note} | ${svc:.2f} | ${copies:.2f} | ${miles:.2f} | ${other:.2f} | **${total:.2f}** |")
    
    savings = grand_total - grand_ifp
    
    lines.extend([
        f"| **TOTAL** | | | | | | | **${grand_ifp:.2f}** |",
        "",
        f"## 💰 IFP Savings: ${savings:.2f}",
        f"- Without IFP: **${grand_total:.2f}**",
        f"- With IFP: **${grand_ifp:.2f}**",
        f"- **Savings: ${savings:.2f}** ({savings/grand_total*100:.0f}% reduction)",
        "",
        "## Cost Breakdown by Category",
        f"| Category | Without IFP | With IFP |",
        f"|----------|------------|---------|",
    ])
    
    cats = {'Filing fees': 0, 'Filing fees (IFP)': 0, 'Service': 0, 'Copies': 0, 'Mileage': 0, 'Other': 0}
    for fdata in COSTS.values():
        fee, svc, copies, miles, other = calc_filing_cost(fdata, with_ifp=False)
        fee_ifp, _, _, _, _ = calc_filing_cost(fdata, with_ifp=True)
        cats['Filing fees'] += fee
        cats['Filing fees (IFP)'] += fee_ifp
        cats['Service'] += svc
        cats['Copies'] += copies
        cats['Mileage'] += miles
        cats['Other'] += other
    
    lines.append(f"| Filing fees | ${cats['Filing fees']:.2f} | ${cats['Filing fees (IFP)']:.2f} |")
    lines.append(f"| Service of process | ${cats['Service']:.2f} | ${cats['Service']:.2f} |")
    lines.append(f"| Copies/printing | ${cats['Copies']:.2f} | ${cats['Copies']:.2f} |")
    lines.append(f"| Mileage ({MILEAGE_RATE}/mi) | ${cats['Mileage']:.2f} | ${cats['Mileage']:.2f} |")
    lines.append(f"| Other | ${cats['Other']:.2f} | ${cats['Other']:.2f} |")
    
    lines.extend([
        "",
        "---",
        f"*Mileage rate: ${MILEAGE_RATE}/mile (IRS 2025). All estimates approximate.*",
    ])
    
    md_path = REPORTS_DIR / "LITIGATION_COST_ESTIMATE.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "cost_estimate.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Litigation Cost Estimator (#66)',
        'total_without_ifp': grand_total,
        'total_with_ifp': grand_ifp,
        'savings': savings,
        'mileage_rate': MILEAGE_RATE,
        'costs': {fid: {
            'total': sum(calc_filing_cost(fd, False)),
            'total_ifp': sum(calc_filing_cost(fd, True)),
        } for fid, fd in COSTS.items()},
    }, indent=2, default=str), encoding='utf-8')
    
    print(f"\n✅ Without IFP: ${grand_total:.2f}")
    print(f"   With IFP:    ${grand_ifp:.2f}")
    print(f"   Savings:     ${savings:.2f}")
    print(f"   Reports: {md_path.name}, {json_path.name}")

if __name__ == '__main__':
    main()
