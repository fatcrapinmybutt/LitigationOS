#!/usr/bin/env python3
"""
Tool #129 — Service of Process Matrix
==========================================
🆕 NOVEL TOOL — Comprehensive service matrix for ALL 10 
filings across all courts and parties. Distinct from the 
existing service_tracker.py which tracks active service.
This generates a reference matrix with methods and deadlines.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

FILINGS = [
    {'id': 'F1', 'name': 'Emergency Parenting Time', 'court': '14th Circuit', 'serve': ['Emily Watson'], 'method': 'MCR 2.107 (mail/personal)', 'fee': '$175', 'notes': 'Emergency = shortened notice OK'},
    {'id': 'F2', 'name': 'Fraud on Court', 'court': '14th Circuit', 'serve': ['Emily Watson'], 'method': 'MCR 2.107 (mail/personal)', 'fee': '$175', 'notes': '9-day notice per MCR 2.119'},
    {'id': 'F3', 'name': 'Judicial Disqualification', 'court': '14th Circuit', 'serve': ['Emily Watson', 'Judge McNeill (via clerk)'], 'method': 'MCR 2.003', 'fee': '$0', 'notes': 'GATEWAY filing — everything depends on this'},
    {'id': 'F4', 'name': '§1983 Federal', 'court': 'USDC WDMI', 'serve': ['Emily Watson', 'Judge McNeill', 'Ronald Berry'], 'method': 'FRCP 4 (US Marshal FREE w/IFP)', 'fee': '$405', 'notes': '90 days to serve'},
    {'id': 'F5', 'name': 'MSC Superintending', 'court': 'Mich Supreme Court', 'serve': ['Emily Watson', '14th Circuit Court'], 'method': 'MCR 7.306 (mail)', 'fee': '$375', 'notes': 'Highest risk filing'},
    {'id': 'F6', 'name': 'JTC Complaint', 'court': 'JTC Detroit', 'serve': [], 'method': 'JTC handles all notice', 'fee': '$0', 'notes': 'FREE — just mail complaint'},
    {'id': 'F7', 'name': 'Custody Modification', 'court': '14th Circuit', 'serve': ['Emily Watson'], 'method': 'MCR 2.107 (personal preferred)', 'fee': '$175', 'notes': 'Major mod — personal service recommended'},
    {'id': 'F8', 'name': 'COA Leave to Appeal', 'court': 'Court of Appeals', 'serve': ['Emily Watson'], 'method': 'MCR 7.205 (mail)', 'fee': '$375', 'notes': 'Certificate of service in application'},
    {'id': 'F9', 'name': 'COA Brief', 'court': 'Court of Appeals', 'serve': ['Emily Watson'], 'method': 'MCR 7.212 (mail)', 'fee': '$0', 'notes': 'Cert of service as last page of brief'},
    {'id': 'F10', 'name': 'AGC Grievance', 'court': 'AGC Detroit', 'serve': [], 'method': 'AGC handles all notice', 'fee': '$0', 'notes': 'FREE — file online or mail'},
]

def main():
    print("=" * 70)
    print("SERVICE OF PROCESS MATRIX — Tool #129")
    print("=" * 70)
    
    total_fees = 0
    total_parties = 0
    
    lines = [
        "# 📬 SERVICE OF PROCESS MATRIX",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #129*\n",
        "---\n",
        "| Filing | Court | Serve On | Method | Fee |",
        "|--------|-------|----------|--------|-----|",
    ]
    
    for f in FILINGS:
        parties = ', '.join(f['serve']) if f['serve'] else 'None'
        total_parties += len(f['serve'])
        fee_num = int(f['fee'].replace('$', '').replace(',', '')) if f['fee'] != '$0' else 0
        total_fees += fee_num
        lines.append(f"| **{f['id']}** {f['name']} | {f['court']} | {parties} | {f['method']} | {f['fee']} |")
        print(f"  📬 {f['id']}: {f['name'][:30]} → {len(f['serve'])} parties, {f['fee']}")
    
    lines.extend([
        "",
        f"\n**Total Filing Fees:** ${total_fees:,} (IFP waives ALL → **$0**)",
        f"**Total Service Actions:** {total_parties} parties across {len(FILINGS)} filings",
        f"**No-Service Filings:** F6 (JTC) + F10 (AGC) — oversight bodies handle notice\n",
        "---",
        f"\n*{len(FILINGS)} filings · {total_parties} service actions · ${total_fees:,} fees (waived by IFP)*",
    ])
    
    md_path = REPORTS_DIR / "SERVICE_MATRIX.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "service_matrix.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Service Matrix (#129)',
        'filings': len(FILINGS),
        'total_parties': total_parties,
        'total_fees': total_fees,
        'ifp_savings': total_fees,
    }, indent=2), encoding='utf-8')
    
    print(f"\n✅ {len(FILINGS)} filings | {total_parties} service actions | ${total_fees:,} fees (IFP waives)")
    print(f"   Reports: SERVICE_MATRIX.md + service_matrix.json")

if __name__ == '__main__':
    main()
