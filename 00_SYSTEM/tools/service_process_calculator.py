#!/usr/bin/env python3
"""
Tool #65 — Service of Process Calculator
============================================
For each filing, determines:
1. WHO must be served (all parties + court)
2. HOW they must be served (personal, mail, e-service)
3. WHEN service must be completed (MCR deadlines)
4. WHAT proof of service is needed

Uses verified party addresses from the master identity table.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

PARTIES = {
    'Emily A. Watson': {
        'role': 'Defendant',
        'address': '2160 Garland Drive, Norton Shores, MI 49441',
        'service_method': 'Personal service (MCR 2.105) or certified mail',
        'notes': 'Primary opposing party. Serve ALL filings.',
    },
    'Jennifer Barnes P55406': {
        'role': 'Former Attorney (Withdrew)',
        'address': '880 Jefferson St Ste B, Muskegon, MI 49440',
        'service_method': 'First class mail or personal delivery to office',
        'notes': 'Serve F2 (fraud), F4 (§1983 if named defendant), F10 (AGC). Withdrew but may still accept service for Barnes Law Firm PLLC.',
    },
    'Ronald T. Berry': {
        'role': 'Co-conspirator',
        'address': '[ANDREW MUST PROVIDE — possibly same as Emily Watson]',
        'service_method': 'Personal service or certified mail',
        'notes': 'Serve F4 (§1983 if named defendant). Need confirmed address.',
    },
    'Hon. Jenny L. McNeill': {
        'role': 'Judge / Respondent',
        'address': '990 Terrace St, Muskegon, MI 49442 (via court clerk)',
        'service_method': 'Service via court clerk (MCR 2.107(C)(1)) — NOT personal',
        'notes': 'Serve F3 (disqualification — via clerk), F4 (§1983 — via MI AG for state officials), F5 (MSC — via clerk).',
    },
    'Muskegon County Clerk': {
        'role': 'Court Clerk',
        'address': '990 Terrace St, Muskegon, MI 49442',
        'service_method': 'File with clerk directly',
        'notes': 'All 14th Circuit filings go through clerk. E-file via MiFILE.',
    },
    'Michigan Attorney General': {
        'role': 'Required party for §1983 against state official',
        'address': 'PO Box 30212, Lansing, MI 48909',
        'service_method': 'Certified mail',
        'notes': 'Must be served for F4 (§1983) per 28 USC §1983 and MCR 2.209.',
    },
}

SERVICE_MATRIX = {
    'F1': {
        'title': 'Emergency Parenting Time Motion',
        'court': '14th Circuit Court',
        'serve': [
            {'party': 'Emily A. Watson', 'method': 'Personal or certified mail', 'deadline': 'Before hearing (MCR 2.119(C) — 9 days before hearing, or court may shorten for emergency)', 'documents': 'Motion + Affidavit + Notice of Hearing'},
            {'party': 'Muskegon County Clerk', 'method': 'E-file via MiFILE', 'deadline': 'Day of filing', 'documents': 'All documents + proof of service'},
        ],
    },
    'F2': {
        'title': 'Fraud Upon the Court',
        'court': '14th Circuit Court',
        'serve': [
            {'party': 'Emily A. Watson', 'method': 'Personal service (MCR 2.105) — summons required', 'deadline': '91 days from filing (MCR 2.102(D))', 'documents': 'Complaint + Summons'},
            {'party': 'Jennifer Barnes P55406', 'method': 'Certified mail to office', 'deadline': '91 days', 'documents': 'Complaint + Summons (if named)'},
            {'party': 'Muskegon County Clerk', 'method': 'E-file via MiFILE', 'deadline': 'Day of filing', 'documents': 'All documents'},
        ],
    },
    'F3': {
        'title': 'Judicial Disqualification',
        'court': '14th Circuit Court',
        'serve': [
            {'party': 'Emily A. Watson', 'method': 'First class mail or e-service', 'deadline': '7 days (MCR 2.107)', 'documents': 'Motion + Brief + Affidavit'},
            {'party': 'Hon. Jenny L. McNeill', 'method': 'Via court clerk (file copy for judge)', 'deadline': 'Day of filing', 'documents': 'Motion + Brief'},
            {'party': 'Chief Judge (14th Circuit)', 'method': 'Via court clerk', 'deadline': 'Day of filing', 'documents': 'Copy of motion (MCR 2.003 — chief judge reviews if recusal denied)'},
        ],
    },
    'F4': {
        'title': '42 USC §1983 Federal',
        'court': 'USDC Western District MI',
        'serve': [
            {'party': 'Emily A. Watson', 'method': 'Personal service (FRCP 4(e))', 'deadline': '90 days from filing (FRCP 4(m))', 'documents': 'Complaint + Summons (issued by federal clerk)'},
            {'party': 'Hon. Jenny L. McNeill', 'method': 'Via Michigan Attorney General (FRCP 4(j))', 'deadline': '90 days', 'documents': 'Complaint + Summons'},
            {'party': 'Michigan Attorney General', 'method': 'Certified mail to Lansing', 'deadline': '90 days', 'documents': 'Complaint + Summons + Notice'},
            {'party': 'Ronald T. Berry', 'method': 'Personal service', 'deadline': '90 days', 'documents': 'Complaint + Summons (if named)'},
            {'party': 'Jennifer Barnes P55406', 'method': 'Personal service or certified mail', 'deadline': '90 days', 'documents': 'Complaint + Summons (if named)'},
        ],
    },
    'F5': {
        'title': 'MSC Superintending Control',
        'court': 'Michigan Supreme Court',
        'serve': [
            {'party': 'Emily A. Watson', 'method': 'Certified mail', 'deadline': 'Per MSC order', 'documents': 'Complaint + all supporting documents'},
            {'party': 'Hon. Jenny L. McNeill', 'method': 'Via court clerk', 'deadline': 'Per MSC order', 'documents': 'Complaint'},
            {'party': 'MSC Clerk', 'method': 'TrueFiling or mail to Lansing', 'deadline': 'Day of filing', 'documents': 'All documents'},
        ],
    },
    'F6': {
        'title': 'JTC Complaint',
        'court': 'Judicial Tenure Commission',
        'serve': [
            {'party': 'JTC', 'method': 'Mail or email (jtc@jtc.courts.mi.gov)', 'deadline': 'No statutory deadline', 'documents': 'Complaint + supporting evidence'},
        ],
    },
    'F7': {
        'title': 'Custody Modification',
        'court': '14th Circuit Court',
        'serve': [
            {'party': 'Emily A. Watson', 'method': 'Personal or certified mail', 'deadline': '9 days before hearing (MCR 2.119(C))', 'documents': 'Motion + Brief + Affidavit + Notice of Hearing'},
            {'party': 'Muskegon County Clerk', 'method': 'E-file via MiFILE', 'deadline': 'Day of filing', 'documents': 'All documents'},
        ],
    },
    'F8': {
        'title': 'COA Application for Leave',
        'court': 'Michigan Court of Appeals',
        'serve': [
            {'party': 'Emily A. Watson', 'method': 'First class mail', 'deadline': 'Same day as filing (MCR 7.205(D))', 'documents': 'Application + supporting brief'},
            {'party': 'COA Clerk', 'method': 'TrueFiling', 'deadline': 'Day of filing', 'documents': 'All documents'},
        ],
    },
    'F9': {
        'title': 'COA Appeal Brief (366810)',
        'court': 'Michigan Court of Appeals',
        'serve': [
            {'party': 'Emily A. Watson', 'method': 'First class mail', 'deadline': 'Same day as filing', 'documents': 'Brief + appendix'},
            {'party': 'COA Clerk', 'method': 'TrueFiling', 'deadline': 'Per briefing schedule', 'documents': 'Brief + appendix + proof of service'},
        ],
    },
    'F10': {
        'title': 'AGC Grievance',
        'court': 'Attorney Grievance Commission',
        'serve': [
            {'party': 'AGC', 'method': 'Online (agcmi.com) or mail to Detroit', 'deadline': 'No statutory deadline', 'documents': 'Request for Investigation form + supporting docs'},
        ],
    },
}

def main():
    print("=" * 70)
    print("SERVICE OF PROCESS CALCULATOR — Tool #65")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)
    
    lines = [
        "# SERVICE OF PROCESS GUIDE",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "*Complete service requirements for all 10 filings*\n",
        "---\n",
        "## Party Directory",
        "| Party | Role | Address | Service Method |",
        "|-------|------|---------|---------------|",
    ]
    
    for name, info in PARTIES.items():
        lines.append(f"| {name} | {info['role']} | {info['address'][:40]} | {info['service_method'][:30]} |")
    
    total_service_items = 0
    
    for fid, fdata in SERVICE_MATRIX.items():
        print(f"\n📋 {fid}: {fdata['title']} — {len(fdata['serve'])} parties to serve")
        total_service_items += len(fdata['serve'])
        
        lines.extend([
            f"\n---\n## {fid} — {fdata['title']}",
            f"**Court:** {fdata['court']}\n",
            "| Party | Method | Deadline | Documents |",
            "|-------|--------|----------|-----------|",
        ])
        
        for svc in fdata['serve']:
            lines.append(f"| {svc['party']} | {svc['method'][:30]} | {svc['deadline'][:30]} | {svc['documents'][:40]} |")
            print(f"   → {svc['party']}: {svc['method'][:40]}")
    
    lines.extend([
        "\n---",
        "## Service Tips for Pro Se Litigant",
        "1. **You CANNOT serve papers yourself** (MCR 2.103(A)) — use any person 18+ who is NOT a party",
        "2. **Certified mail = built-in proof** — keep the green return receipt card",
        "3. **E-service via MiFILE** counts as service for registered parties",
        "4. **Personal service** = hand-deliver to the person (strongest method)",
        "5. **Always file proof of service** with the court (04_CERTIFICATE_OF_SERVICE.md template in each package)",
        "6. **Federal service (F4)** requires a summons ISSUED BY THE CLERK — cannot self-issue",
        "7. **Keep copies of everything** — certified mail receipts, process server affidavits",
        "",
        f"*Total: {total_service_items} service items across 10 filings*",
    ])
    
    md_path = REPORTS_DIR / "SERVICE_OF_PROCESS_GUIDE.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "service_process.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Service of Process Calculator (#65)',
        'total_service_items': total_service_items,
        'parties': PARTIES,
        'service_matrix': SERVICE_MATRIX,
    }, indent=2, default=str), encoding='utf-8')
    
    print(f"\n✅ {total_service_items} service items mapped across 10 filings")
    print(f"   Reports: {md_path.name}, {json_path.name}")

if __name__ == '__main__':
    main()
