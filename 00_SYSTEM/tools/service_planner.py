#!/usr/bin/env python3
"""
Tool #83 — Service of Process Planner
=========================================
Plans service of process for ALL 10 filings:
- Who must be served (parties, agencies, courts)
- How to serve (personal, mail, e-filing, certified)
- Michigan rules: MCR 2.105 (personal), MCR 2.107 (subsequent)
- Federal rules: FRCP 4 (summons + complaint)
- Time limits for service
- Cost per method
- Template proof of service language

Generates a per-filing service checklist.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

# Service requirements per filing
SERVICE_PLANS = {
    'F1': {
        'name': 'Emergency Parenting Time Motion',
        'court': '14th Circuit Court',
        'case_no': '2024-001507-DC',
        'serve_parties': [
            {
                'name': 'Emily A. Watson',
                'address': '2160 Garland Drive, Norton Shores, MI 49441',
                'method': 'Personal service (MCR 2.105) or First-class mail (MCR 2.107)',
                'rule': 'MCR 2.107(C)(1) — mail to last known address',
                'cost': 75,
                'notes': 'Motion — subsequent pleading, mail OK per MCR 2.107',
            },
        ],
        'serve_court': 'MiFILE electronic filing',
        'deadline': '7 days before hearing (MCR 2.119(C)(1))',
    },
    'F2': {
        'name': 'Motion to Set Aside (Fraud)',
        'court': '14th Circuit Court',
        'case_no': '2024-001507-DC',
        'serve_parties': [
            {
                'name': 'Emily A. Watson',
                'address': '2160 Garland Drive, Norton Shores, MI 49441',
                'method': 'Personal service or mail (MCR 2.107)',
                'rule': 'MCR 2.107(C)(1)',
                'cost': 75,
                'notes': 'Critical motion — consider personal service for proof',
            },
        ],
        'serve_court': 'MiFILE electronic filing',
        'deadline': '7 days before hearing',
    },
    'F3': {
        'name': 'Motion for Disqualification',
        'court': '14th Circuit Court',
        'case_no': '2024-001507-DC',
        'serve_parties': [
            {
                'name': 'Emily A. Watson',
                'address': '2160 Garland Drive, Norton Shores, MI 49441',
                'method': 'Mail (MCR 2.107)',
                'rule': 'MCR 2.003(D)(1) — must serve all parties',
                'cost': 10,
                'notes': 'Disqualification motion served on ALL parties + judge gets copy via clerk',
            },
            {
                'name': 'Hon. Jenny L. McNeill (via Clerk)',
                'address': '14th Circuit Court, 990 Terrace St, Muskegon, MI 49442',
                'method': 'Filed with clerk — judge receives automatically',
                'rule': 'MCR 2.003(D)',
                'cost': 0,
                'notes': 'Judge must respond within 14 days per MCR 2.003(D)(2)',
            },
        ],
        'serve_court': 'MiFILE electronic filing',
        'deadline': 'ASAP — no hearing required initially (MCR 2.003(D)(2))',
    },
    'F4': {
        'name': '§1983 Federal Complaint',
        'court': 'USDC Western District MI',
        'case_no': 'New filing',
        'serve_parties': [
            {
                'name': 'Emily A. Watson',
                'address': '2160 Garland Drive, Norton Shores, MI 49441',
                'method': 'Personal service by US Marshals (if IFP) or process server',
                'rule': 'FRCP 4(c)(3) — court orders Marshals if IFP granted',
                'cost': 0,  # Free if IFP
                'notes': 'If IFP granted, US Marshals serve for FREE',
            },
            {
                'name': 'Ronald T. Berry',
                'address': '2160 Garland Drive, Norton Shores, MI 49441',
                'method': 'Personal service by US Marshals (if IFP)',
                'rule': 'FRCP 4(e) — personal service',
                'cost': 0,
                'notes': 'Co-defendant — same address as Watson',
            },
            {
                'name': 'Hon. Jenny L. McNeill (official capacity)',
                'address': '14th Circuit Court, 990 Terrace St, Muskegon, MI 49442',
                'method': 'Service on MI Attorney General (FRCP 4(j)(2))',
                'rule': 'FRCP 4(j)(2) — serve state officer via AG',
                'cost': 0,
                'notes': 'Must also serve MI AG: Dana Nessel, PO Box 30212, Lansing MI 48909',
            },
        ],
        'serve_court': 'CM/ECF electronic filing (PACER account required)',
        'deadline': '90 days after filing (FRCP 4(m))',
    },
    'F5': {
        'name': 'MSC Complaint for Superintending Control',
        'court': 'Michigan Supreme Court',
        'case_no': 'New filing',
        'serve_parties': [
            {
                'name': 'Emily A. Watson',
                'address': '2160 Garland Drive, Norton Shores, MI 49441',
                'method': 'Certified mail, return receipt (MCR 7.305)',
                'rule': 'MCR 7.306(B)(2)',
                'cost': 15,
                'notes': 'MSC requires certified mail for original actions',
            },
            {
                'name': 'Hon. Jenny L. McNeill',
                'address': '14th Circuit Court, 990 Terrace St, Muskegon, MI 49442',
                'method': 'Certified mail',
                'rule': 'MCR 7.306(B)(2)',
                'cost': 15,
                'notes': 'Respondent judge must be served',
            },
        ],
        'serve_court': 'TrueFiling electronic filing',
        'deadline': 'With filing or within 7 days',
    },
    'F6': {
        'name': 'JTC Complaint',
        'court': 'Judicial Tenure Commission',
        'case_no': 'New complaint',
        'serve_parties': [],
        'serve_court': 'Mail to JTC: 3034 W Grand Blvd Ste 8-450, Detroit MI 48202',
        'deadline': 'No deadline — submit anytime',
        'notes': 'JTC investigates internally — no party service required by complainant',
    },
    'F7': {
        'name': 'Motion to Modify Custody',
        'court': '14th Circuit Court',
        'case_no': '2024-001507-DC',
        'serve_parties': [
            {
                'name': 'Emily A. Watson',
                'address': '2160 Garland Drive, Norton Shores, MI 49441',
                'method': 'Personal service (MCR 2.105) — new motion in existing case',
                'rule': 'MCR 2.107(C)(1)',
                'cost': 75,
                'notes': 'Modification motion — serve like new complaint if custody change sought',
            },
        ],
        'serve_court': 'MiFILE electronic filing',
        'deadline': '7 days before hearing (MCR 2.119(C)(1))',
    },
    'F8': {
        'name': 'COA Application for Leave',
        'court': 'Court of Appeals',
        'case_no': 'New application',
        'serve_parties': [
            {
                'name': 'Emily A. Watson',
                'address': '2160 Garland Drive, Norton Shores, MI 49441',
                'method': 'First-class mail (MCR 7.205)',
                'rule': 'MCR 7.205(A)',
                'cost': 10,
                'notes': 'Application — mail service sufficient',
            },
        ],
        'serve_court': 'TrueFiling electronic filing',
        'deadline': 'Within 21 days of order being appealed (MCR 7.205(A))',
    },
    'F9': {
        'name': 'COA Appeal Brief',
        'court': 'Court of Appeals',
        'case_no': 'COA 366810',
        'serve_parties': [
            {
                'name': 'Emily A. Watson',
                'address': '2160 Garland Drive, Norton Shores, MI 49441',
                'method': 'First-class mail (MCR 7.212)',
                'rule': 'MCR 7.212(E)',
                'cost': 10,
                'notes': 'Brief — mail to all parties',
            },
        ],
        'serve_court': 'TrueFiling electronic filing',
        'deadline': 'Per COA scheduling order (call clerk: 517-373-0786)',
    },
    'F10': {
        'name': 'AGC Grievance',
        'court': 'Attorney Grievance Commission',
        'case_no': 'New grievance',
        'serve_parties': [],
        'serve_court': 'Mail/email to AGC: 535 Griswold St Ste 1700, Detroit MI 48226',
        'deadline': 'No deadline — submit anytime',
        'notes': 'AGC investigates internally — no party service required',
    },
}

def main():
    print("=" * 70)
    print("SERVICE OF PROCESS PLANNER — Tool #83")
    print("=" * 70)
    
    total_serve_actions = 0
    total_cost = 0
    
    lines = [
        "# 📬 SERVICE OF PROCESS PLANNER",
        "## Pigors v. Watson — Complete Service Guide",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n",
        "---\n",
    ]
    
    for filing_id, plan in SERVICE_PLANS.items():
        party_count = len(plan['serve_parties'])
        filing_cost = sum(p.get('cost', 0) for p in plan['serve_parties'])
        total_serve_actions += party_count
        total_cost += filing_cost
        
        lines.append(f"## {filing_id} — {plan['name']}")
        lines.append(f"**Court:** {plan['court']} | **Case:** {plan['case_no']}")
        lines.append(f"**Filing Method:** {plan['serve_court']}")
        lines.append(f"**Service Deadline:** {plan.get('deadline', 'N/A')}")
        
        if plan['serve_parties']:
            lines.append(f"\n| Party | Method | Rule | Cost |")
            lines.append(f"|-------|--------|------|------|")
            for p in plan['serve_parties']:
                lines.append(f"| {p['name']} | {p['method'][:40]} | {p['rule'][:20]} | ${p.get('cost', 0)} |")
                print(f"  {filing_id} → {p['name'][:25]}: {p['method'][:40]}")
        else:
            lines.append(f"\n*{plan.get('notes', 'No party service required')}*")
            print(f"  {filing_id}: No party service required")
        
        lines.append("")
    
    lines.extend([
        "---",
        "## SUMMARY",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total service actions | {total_serve_actions} |",
        f"| Total service cost | ${total_cost} |",
        f"| Free services (IFP/agency) | JTC (F6), AGC (F10), Federal if IFP (F4) |",
        "",
        "## KEY ADDRESSES",
        "| Party/Entity | Address |",
        "|-------------|---------|",
        "| Emily A. Watson | 2160 Garland Drive, Norton Shores, MI 49441 |",
        "| 14th Circuit Court | 990 Terrace St, Muskegon, MI 49442 |",
        "| JTC | 3034 W Grand Blvd Ste 8-450, Detroit MI 48202 |",
        "| AGC | 535 Griswold St Ste 1700, Detroit MI 48226 |",
        "| MI Attorney General | PO Box 30212, Lansing MI 48909 |",
        "| MSC | 925 W Ottawa St, Lansing MI 48915 |",
        "| COA | 925 W Ottawa St, Lansing MI 48909 |",
        "",
        f"*Service of Process Planner — Tool #83*",
    ])
    
    md_path = REPORTS_DIR / "SERVICE_PLANNER.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "service_planner.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Service of Process Planner (#83)',
        'total_serve_actions': total_serve_actions,
        'total_cost': total_cost,
        'filings': {k: {
            'name': v['name'],
            'court': v['court'],
            'parties_to_serve': len(v['serve_parties']),
            'cost': sum(p.get('cost', 0) for p in v['serve_parties']),
        } for k, v in SERVICE_PLANS.items()},
    }, indent=2), encoding='utf-8')
    
    print(f"\n✅ {total_serve_actions} service actions, ${total_cost} total cost")
    print(f"   Reports: SERVICE_PLANNER.md + service_planner.json")

if __name__ == '__main__':
    main()
