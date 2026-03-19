#!/usr/bin/env python3
"""
Tool #142 — Court Clerk Intelligence
=================================================
🆕 NOVEL TOOL — Contact info, procedures, and tips
for every clerk's office Andrew needs to interact with.

Pro se litigants live and die by their relationship
with court clerks. This tool makes every interaction smooth.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

CLERK_OFFICES = [
    {
        'court': '14th Circuit Court — Family Division',
        'address': '990 Terrace St, Muskegon, MI 49442',
        'phone': '(231) 724-6241',
        'hours': 'Mon-Fri 8:00 AM - 5:00 PM',
        'efiling': 'MiFILE (mifile.courts.michigan.gov)',
        'key_contacts': ['Family Division Clerk', 'Pamela Rusco (judicial secretary — NOTE: works for McNeill)'],
        'filing_tips': [
            'E-file through MiFILE preferred — paper accepted at counter',
            'Bring 3 copies: original + 2 (court + your copy)',
            'Filing fees: $175 per motion (waived with MC 20 IFP)',
            'Ask for certified copies at time of filing ($1/page + $10 cert)',
            'Clerk CANNOT give legal advice but CAN tell you if paperwork is complete',
        ],
        'case_numbers': ['2024-001507-DC', '2023-5907-PP'],
    },
    {
        'court': 'US District Court — Western District of Michigan',
        'address': '399 Federal Building, 110 Michigan St NW, Grand Rapids, MI 49503',
        'phone': '(616) 456-2381',
        'hours': 'Mon-Fri 8:30 AM - 4:30 PM',
        'efiling': 'CM/ECF (ecf.miwd.uscourts.gov) — PACER account required',
        'key_contacts': ['Clerk of Court', 'Pro Se Intake Clerk'],
        'filing_tips': [
            'Federal court requires CM/ECF for all filings',
            'Pro se litigants get PACER fee exemption (ask for it)',
            'US Marshals serve defendants for free with IFP',
            'Filing fee: $405 (waived with IFP application)',
            'Call Pro Se Intake Clerk for filing questions',
        ],
        'case_numbers': ['New — to be assigned with F4'],
    },
    {
        'court': 'Michigan Court of Appeals',
        'address': '925 W. Ottawa St, Lansing, MI 48915',
        'phone': '(517) 373-0786',
        'hours': 'Mon-Fri 8:00 AM - 5:00 PM',
        'efiling': 'MiFILE (same system as circuit court)',
        'key_contacts': ['COA Clerk', 'Case Manager for 366810'],
        'filing_tips': [
            'Call (517) 373-0786 to confirm deadline for 366810',
            'Application fee: $375 (waived with MC 20 IFP)',
            'COA is STRICT about page limits — 50 pages for application',
            'Use 13pt Times New Roman, double-spaced',
            'Include lower court register of actions',
        ],
        'case_numbers': ['COA 366810 (existing)', 'New for F8'],
    },
    {
        'court': 'Michigan Supreme Court',
        'address': '925 W. Ottawa St, Lansing, MI 48915',
        'phone': '(517) 373-0120',
        'hours': 'Mon-Fri 8:00 AM - 5:00 PM',
        'efiling': 'MiFILE',
        'key_contacts': ['MSC Clerk', 'Original Actions Desk'],
        'filing_tips': [
            'Superintending control = original action (rare)',
            'Call Original Actions Desk to confirm procedure',
            'Filing fee: $375 (waived with MC 20 IFP)',
            'MSC accepts only extraordinary cases — be compelling',
        ],
        'case_numbers': ['New — for F5 if filed'],
    },
    {
        'court': 'Judicial Tenure Commission (JTC)',
        'address': '3034 W. Grand Blvd Ste 8-450, Detroit, MI 48202',
        'phone': '(313) 875-5110',
        'hours': 'Mon-Fri 8:30 AM - 5:00 PM',
        'efiling': 'Mail or online (jtc.courts.mi.gov)',
        'key_contacts': ['JTC Intake Officer'],
        'filing_tips': [
            'Filing is FREE — no fees',
            'Complaint form available online at jtc.courts.mi.gov',
            'Be factual, specific, cite dates and evidence',
            'JTC investigates confidentially — you may not hear back',
            'File even if you think nothing will happen — creates paper trail',
        ],
        'case_numbers': ['New — for F6'],
    },
    {
        'court': 'Attorney Grievance Commission (AGC)',
        'address': '535 Griswold St Ste 1700, Detroit, MI 48226',
        'phone': '(313) 961-6585',
        'hours': 'Mon-Fri 8:30 AM - 5:00 PM',
        'efiling': 'Online (agcmi.com) or mail',
        'key_contacts': ['AGC Intake Coordinator'],
        'filing_tips': [
            'Filing is FREE — no fees',
            'Online filing preferred (agcmi.com/file-a-grievance)',
            'Include specific MRPC rule violations',
            'Attach documentary evidence',
            'Grievance is confidential until formal charges',
        ],
        'case_numbers': ['New — for F10 against Barnes P55406'],
    },
]

def main():
    print("=" * 70)
    print("COURT CLERK INTELLIGENCE — Tool #142")
    print("=" * 70)
    
    lines = [
        "# 🏛️ COURT CLERK INTELLIGENCE",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #142*",
        f"*{len(CLERK_OFFICES)} courts — every clerk office Andrew needs*\n",
        "---\n",
        "## QUICK REFERENCE\n",
        "| Court | Phone | E-Filing |",
        "|-------|-------|----------|",
    ]
    
    for c in CLERK_OFFICES:
        lines.append(f"| {c['court'][:40]} | {c['phone']} | {c['efiling'][:30]} |")
        print(f"  🏛️ {c['court'][:40]}: {c['phone']}")
    
    lines.extend(["", "---\n"])
    
    for c in CLERK_OFFICES:
        lines.append(f"## {c['court']}")
        lines.append(f"📍 **Address:** {c['address']}")
        lines.append(f"📞 **Phone:** {c['phone']}")
        lines.append(f"🕐 **Hours:** {c['hours']}")
        lines.append(f"💻 **E-Filing:** {c['efiling']}")
        lines.append(f"📋 **Case Numbers:** {', '.join(c['case_numbers'])}\n")
        
        lines.append("### Key Contacts:")
        for kc in c['key_contacts']:
            lines.append(f"- {kc}")
        
        lines.append("\n### Filing Tips:")
        for tip in c['filing_tips']:
            lines.append(f"- 💡 {tip}")
        
        lines.append("\n---\n")
    
    total_tips = sum(len(c['filing_tips']) for c in CLERK_OFFICES)
    lines.append(f"*{len(CLERK_OFFICES)} courts · {total_tips} tips · Print and keep at desk*")
    
    md_path = REPORTS_DIR / "COURT_CLERK_INTEL.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "court_clerk_intel.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Court Clerk Intelligence (#142)',
        'courts': len(CLERK_OFFICES),
        'tips': total_tips,
    }, indent=2), encoding='utf-8')
    
    print(f"\n✅ {len(CLERK_OFFICES)} clerk offices with {total_tips} tips")
    print(f"   Reports: COURT_CLERK_INTEL.md + court_clerk_intel.json")

if __name__ == '__main__':
    main()
