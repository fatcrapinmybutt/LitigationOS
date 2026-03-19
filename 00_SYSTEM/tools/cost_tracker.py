#!/usr/bin/env python3
"""
Tool #108 — Litigation Cost Tracker & Fee Shifting Calculator
================================================================
🆕 NOVEL TOOL — Tracks every dollar spent and calculates
potential fee-shifting recovery

Under MCL 600.2591 (frivolous actions) and 42 USC 1988 (federal
fee shifting), Andrew can potentially recover costs if he prevails.

Tracks:
- Filing fees (actual + projected)
- Service costs
- Copy/printing costs
- Travel/mileage to court
- Postage
- Notarization fees
- Expert fees (if any)
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

COSTS = {
    'filing_fees': {
        'label': 'Filing Fees',
        'items': [
            {'description': 'F1 Emergency Parenting Time (14th Circuit)', 'amount': 175, 'status': 'projected', 'ifp_waivable': True},
            {'description': 'F2 Fraud on Court (14th Circuit)', 'amount': 175, 'status': 'projected', 'ifp_waivable': True},
            {'description': 'F3 Judicial Disqualification (14th Circuit)', 'amount': 0, 'status': 'projected', 'ifp_waivable': False},
            {'description': 'F4 §1983 Federal (USDC WDMI)', 'amount': 405, 'status': 'projected', 'ifp_waivable': True},
            {'description': 'F5 MSC Superintending Control', 'amount': 375, 'status': 'projected', 'ifp_waivable': True},
            {'description': 'F6 JTC Complaint', 'amount': 0, 'status': 'projected', 'ifp_waivable': False},
            {'description': 'F7 Custody Modification (14th Circuit)', 'amount': 175, 'status': 'projected', 'ifp_waivable': True},
            {'description': 'F8 COA Leave to Appeal', 'amount': 375, 'status': 'projected', 'ifp_waivable': True},
            {'description': 'F9 COA Brief (already filed)', 'amount': 0, 'status': 'filed', 'ifp_waivable': False},
            {'description': 'F10 AGC Grievance', 'amount': 0, 'status': 'projected', 'ifp_waivable': False},
        ]
    },
    'service_costs': {
        'label': 'Service of Process',
        'items': [
            {'description': 'Emily Watson (certified mail per filing)', 'amount': 12, 'quantity': 5, 'status': 'projected'},
            {'description': 'Ronald Berry (certified mail)', 'amount': 12, 'quantity': 2, 'status': 'projected'},
            {'description': 'Judge McNeill (via court clerk)', 'amount': 0, 'quantity': 2, 'status': 'projected'},
            {'description': 'Process server (if needed)', 'amount': 75, 'quantity': 1, 'status': 'projected'},
        ]
    },
    'copy_printing': {
        'label': 'Copies & Printing',
        'items': [
            {'description': 'Court copies ($.25/page est 500 pages)', 'amount': 125, 'status': 'projected'},
            {'description': 'Exhibit copies (200 exhibits avg 5 pages)', 'amount': 250, 'status': 'projected'},
            {'description': 'Brief printing (10 briefs avg 30 pages)', 'amount': 75, 'status': 'projected'},
        ]
    },
    'travel': {
        'label': 'Travel & Mileage',
        'items': [
            {'description': 'Muskegon courthouse (RT from N. Muskegon) ~15 mi', 'amount': 10, 'quantity': 10, 'status': 'projected'},
            {'description': 'Grand Rapids federal court (RT ~80 mi)', 'amount': 52, 'quantity': 3, 'status': 'projected'},
            {'description': 'Lansing COA/MSC/JTC (RT ~350 mi)', 'amount': 228, 'quantity': 2, 'status': 'projected'},
        ]
    },
    'other': {
        'label': 'Other Costs',
        'items': [
            {'description': 'Notarization fees (affidavits)', 'amount': 10, 'quantity': 10, 'status': 'projected'},
            {'description': 'Postage (certified mail filings)', 'amount': 8, 'quantity': 15, 'status': 'projected'},
            {'description': 'USB drives for electronic filing', 'amount': 10, 'quantity': 2, 'status': 'projected'},
        ]
    },
}

FEE_SHIFTING = {
    'MCL 600.2591': {
        'title': 'Michigan Frivolous Claims Statute',
        'applies_to': 'State court (F1, F2, F3, F7)',
        'standard': 'Other party\'s claims were frivolous — filed to harass, no factual basis, or no legal basis',
        'recoverable': 'Reasonable attorney fees (or pro se equivalent) + costs',
        'note': 'Pro se litigants can recover costs but NOT attorney fees (no attorney to pay)',
    },
    '42 USC 1988': {
        'title': 'Federal Civil Rights Attorney Fees',
        'applies_to': 'Federal court (F4 — §1983)',
        'standard': 'Prevailing party in §1983 action',
        'recoverable': 'Reasonable attorney fees + expert fees + costs. Pro se can recover costs.',
        'note': 'If Andrew prevails on §1983, defendants pay ALL costs + potentially fees',
    },
    'MCL 600.2405': {
        'title': 'Michigan Cost Recovery',
        'applies_to': 'All state filings',
        'standard': 'Prevailing party',
        'recoverable': 'Taxable costs: filing fees, service, witness fees, copy costs',
        'note': 'Mandatory — prevailing party recovers taxable costs',
    },
}

def main():
    print("=" * 70)
    print("LITIGATION COST TRACKER — Tool #108")
    print("=" * 70)
    
    lines = [
        "# 💰 LITIGATION COST TRACKER & FEE SHIFTING CALCULATOR",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #108*\n",
        "---\n",
    ]
    
    grand_total = 0
    ifp_savings = 0
    
    for cat_key, cat in COSTS.items():
        lines.append(f"## {cat['label']}\n")
        lines.append("| Item | Amount | Status |")
        lines.append("|------|--------|--------|")
        
        cat_total = 0
        for item in cat['items']:
            qty = item.get('quantity', 1)
            total = item['amount'] * qty
            cat_total += total
            
            qty_str = f" × {qty}" if qty > 1 else ""
            ifp = " 🏷️ IFP" if item.get('ifp_waivable') else ""
            lines.append(f"| {item['description']}{qty_str} | ${total:,.0f}{ifp} | {item['status']} |")
            
            if item.get('ifp_waivable') and total > 0:
                ifp_savings += total
        
        lines.append(f"\n**Subtotal: ${cat_total:,.0f}**\n")
        grand_total += cat_total
        print(f"  {cat['label']}: ${cat_total:,.0f}")
    
    lines.extend([
        "---",
        "## 📊 TOTALS\n",
        f"| Metric | Amount |",
        f"|--------|--------|",
        f"| Total projected costs | **${grand_total:,.0f}** |",
        f"| IFP waivable fees | -${ifp_savings:,.0f} |",
        f"| Net cost with IFP | **${grand_total - ifp_savings:,.0f}** |",
        "",
    ])
    
    # Fee shifting
    lines.append("## ⚖️ FEE SHIFTING POTENTIAL\n")
    total_recoverable = 0
    
    for statute, data in FEE_SHIFTING.items():
        lines.extend([
            f"### {statute}: {data['title']}",
            f"**Applies to:** {data['applies_to']}",
            f"**Standard:** {data['standard']}",
            f"**Recoverable:** {data['recoverable']}",
            f"**Note:** {data['note']}\n",
        ])
    
    lines.extend([
        "---",
        "## 🎯 BOTTOM LINE\n",
        f"- **Worst case** (no IFP, no recovery): ${grand_total:,.0f} out of pocket",
        f"- **With IFP** (fees waived): ${grand_total - ifp_savings:,.0f} out of pocket",
        f"- **Best case** (prevail + fee shifting): **$0** — all costs recovered from defendants",
        "",
        "## ⚠️ ANDREW ACTION ITEMS\n",
        "- [ ] Track every expense — keep ALL receipts",
        "- [ ] Log mileage for every court trip",
        "- [ ] Keep copy/printing receipts",
        "- [ ] File IFP application with first filing in each court",
        "- [ ] Request cost recovery in every filing",
        "",
        f"*Cost Tracker — Tool #108 — ${grand_total:,.0f} total / ${grand_total - ifp_savings:,.0f} with IFP*",
    ])
    
    md_path = REPORTS_DIR / "COST_TRACKER.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "cost_tracker.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Cost Tracker (#108)',
        'grand_total': grand_total,
        'ifp_savings': ifp_savings,
        'net_with_ifp': grand_total - ifp_savings,
        'categories': {k: sum(i['amount'] * i.get('quantity', 1) for i in v['items']) for k, v in COSTS.items()},
    }, indent=2), encoding='utf-8')
    
    print(f"\n  💰 Total costs: ${grand_total:,.0f}")
    print(f"  🏷️ IFP savings: ${ifp_savings:,.0f}")
    print(f"  ✅ Net with IFP: ${grand_total - ifp_savings:,.0f}")
    print(f"   Reports: COST_TRACKER.md + cost_tracker.json")

if __name__ == '__main__':
    main()
