#!/usr/bin/env python3
"""
Tool #127 — E-Filing Instruction Guide
==========================================
🆕 NOVEL TOOL — Step-by-step instructions for filing
in each court system Andrew needs to use.

Covers: MiFILE (state), PACER/CM-ECF (federal), 
JTC (mail), AGC (online), COA/MSC (MiFILE).
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

FILING_SYSTEMS = {
    'mifile': {
        'name': 'MiFILE (Michigan Courts)',
        'url': 'https://mifile.courts.michigan.gov',
        'used_for': ['F1', 'F2', 'F3', 'F7', 'F8', 'F9'],
        'registration': [
            'Go to mifile.courts.michigan.gov/register',
            'Click "Register" and select "Self-Represented (Pro Se)"',
            'Enter: Andrew James Pigors, andrewjpigors@gmail.com',
            'Create password (save it somewhere secure!)',
            'Verify email address',
            'Add case: 2024-001507-DC (14th Circuit Court)',
            'Add case: 2023-5907-PP (14th Circuit Court)',
        ],
        'filing_steps': [
            'Log in to MiFILE',
            'Click "File Into Existing Case"',
            'Select case number (2024-001507-DC)',
            'Select filing type (e.g., "Motion")',
            'Upload PDF document (main filing)',
            'Upload any attachments (exhibits, affidavits)',
            'Add proposed order if required',
            'Review all uploaded documents',
            'Pay fee or select "Fee Waiver / IFP" if approved',
            'Click "Submit" — SAVE the confirmation number!',
            'File proof of service separately (MC 09)',
        ],
        'tips': [
            'Convert all docs to PDF before uploading',
            'Max file size: 25 MB per document',
            'Name files descriptively (e.g., "Motion_Disqualification_F3.pdf")',
            'Keep confirmation emails as proof of filing',
            'File BEFORE 11:59 PM to count as that day\'s filing',
        ],
        'cost': 'Filing fees vary; IFP waives all (Tool #105)',
    },
    'pacer': {
        'name': 'PACER / CM-ECF (Federal Court)',
        'url': 'https://pacer.uscourts.gov',
        'used_for': ['F4'],
        'registration': [
            'Go to pacer.uscourts.gov',
            'Click "Register for an Account"',
            'Select "Register for a PACER Account" first',
            'Complete registration form',
            'Then register for CM-ECF at USDC Western District of Michigan',
            'Go to ecf.miwd.uscourts.gov',
            'Complete attorney/pro se registration (may require in-person verification)',
            'NOTE: Federal pro se e-filing may require court permission',
        ],
        'filing_steps': [
            'Log in to CM-ECF for USDC WDMI',
            'Click "Civil" → "Complaints/New Cases"',
            'Enter party information (all defendants)',
            'Upload complaint PDF',
            'Upload civil cover sheet (JS 44)',
            'Upload IFP application if applicable',
            'Pay filing fee ($405) or submit IFP',
            'Serve defendants per FRCP 4 (US Marshal for IFP plaintiffs)',
        ],
        'tips': [
            'Federal court is stricter on formatting (see local rules)',
            'Margins: 1 inch all sides; font: 12pt Times New Roman',
            'Page numbers required on every page',
            'Certificate of service must be on separate page',
            'File the IFP application WITH the complaint — not after',
        ],
        'cost': '$405 filing fee (IFP waives)',
    },
    'jtc': {
        'name': 'Judicial Tenure Commission',
        'url': 'https://jtc.courts.michigan.gov',
        'used_for': ['F6'],
        'registration': [
            'NO registration required — anyone can file a complaint',
        ],
        'filing_steps': [
            'Download complaint form from jtc.courts.michigan.gov',
            'OR write a letter-format complaint',
            'Include: Your name, judge name, case number, specific conduct',
            'Attach supporting documentation (keep under 50 pages)',
            'Mail to: Judicial Tenure Commission, 3034 W Grand Blvd Ste 8-450, Detroit, MI 48202',
            'OR email: jtc@courts.mi.gov (confirm current email)',
            'Keep copy of everything you send',
            'JTC will acknowledge receipt within 30 days',
        ],
        'tips': [
            'Be specific and factual — cite dates, case numbers, exact conduct',
            'Do NOT use emotional language — stick to facts',
            'Reference specific Canon violations (see Tool #103)',
            'JTC investigations are confidential — they won\'t tell you the status',
            'Filing is FREE — no cost whatsoever',
        ],
        'cost': 'FREE',
    },
    'agc': {
        'name': 'Attorney Grievance Commission',
        'url': 'https://agc.michbar.org',
        'used_for': ['F10'],
        'registration': [
            'NO registration required — anyone can file a grievance',
        ],
        'filing_steps': [
            'Go to agc.michbar.org',
            'Click "File a Grievance" or "Request for Investigation"',
            'Complete the online form OR download paper form',
            'Identify attorney: Jennifer Barnes, P55406',
            'Describe specific MRPC violations (see Tool #117)',
            'Attach supporting documents',
            'Submit online or mail to: AGC, 535 Griswold St Ste 1700, Detroit, MI 48226',
            'AGC will acknowledge within 21 days',
        ],
        'tips': [
            'Reference specific MRPC rules Barnes violated',
            'Include timeline of representation and withdrawal',
            'AGC handles investigation — you just provide facts',
            'Filing is FREE',
            'You may be contacted for additional information',
        ],
        'cost': 'FREE',
    },
    'coa': {
        'name': 'Court of Appeals (via MiFILE)',
        'url': 'https://mifile.courts.michigan.gov',
        'used_for': ['F8', 'F9'],
        'registration': [
            'Same MiFILE account as circuit court',
            'Add COA case: 366810',
            'Select "Court of Appeals" as the court',
        ],
        'filing_steps': [
            'Log in to MiFILE',
            'Select Court of Appeals case (366810)',
            'For F8 (Leave): Upload application for leave to appeal',
            'For F9 (Brief): Upload appellant brief (50 page limit)',
            'Include: Table of contents, index of authorities, statement of questions',
            'Upload appendix as separate document',
            'File proof of service on opposing party',
            'Pay fee ($375 for leave, $0 for brief if leave granted) or IFP',
        ],
        'tips': [
            'CALL CLERK FIRST: (517) 373-0786 to confirm deadlines for 366810',
            'Brief must cite to lower court record (page numbers)',
            'Follow MCR 7.212 formatting requirements exactly',
            'Binding: left margin stapled, not spiral bound',
            'File 1 original + copies as required by clerk',
        ],
        'cost': '$375 application fee (IFP waives)',
    },
}

def main():
    print("=" * 70)
    print("E-FILING INSTRUCTION GUIDE — Tool #127")
    print("=" * 70)
    
    lines = [
        "# 💻 E-FILING INSTRUCTION GUIDE",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #127*",
        f"*Step-by-step for every court system Andrew needs*\n",
        "---\n",
        "## QUICK REFERENCE\n",
        "| System | Filings | Cost | URL |",
        "|--------|---------|------|-----|",
    ]
    
    for key, sys_info in FILING_SYSTEMS.items():
        filings = ', '.join(sys_info['used_for'])
        lines.append(f"| {sys_info['name']} | {filings} | {sys_info['cost']} | {sys_info['url']} |")
    
    lines.extend(["", "---\n"])
    
    for key, sys_info in FILING_SYSTEMS.items():
        lines.append(f"## {sys_info['name']}")
        lines.append(f"**URL:** {sys_info['url']}")
        lines.append(f"**Used For:** {', '.join(sys_info['used_for'])}")
        lines.append(f"**Cost:** {sys_info['cost']}\n")
        
        lines.append("### Registration:")
        for i, step in enumerate(sys_info['registration'], 1):
            lines.append(f"{i}. {step}")
        
        lines.append("\n### Filing Steps:")
        for i, step in enumerate(sys_info['filing_steps'], 1):
            lines.append(f"{i}. {step}")
        
        lines.append("\n### Tips:")
        for tip in sys_info['tips']:
            lines.append(f"- 💡 {tip}")
        
        lines.append("\n---\n")
        print(f"  💻 {sys_info['name']}: {len(sys_info['filing_steps'])} steps ({', '.join(sys_info['used_for'])})")
    
    lines.extend([
        "## REGISTRATION PRIORITY",
        "1. **MiFILE** — Register FIRST (needed for 6 of 10 filings)",
        "2. **PACER** — Register SECOND (federal §1983 takes longest to set up)",
        "3. **JTC/AGC** — No registration needed (just submit)\n",
        
        f"*{len(FILING_SYSTEMS)} filing systems · {sum(len(s['filing_steps']) for s in FILING_SYSTEMS.values())} total steps*",
    ])
    
    md_path = REPORTS_DIR / "EFILING_GUIDE.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "efiling_guide.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'E-Filing Instruction Guide (#127)',
        'systems': len(FILING_SYSTEMS),
        'total_steps': sum(len(s['filing_steps']) for s in FILING_SYSTEMS.values()),
    }, indent=2), encoding='utf-8')
    
    print(f"\n✅ {len(FILING_SYSTEMS)} filing systems with {sum(len(s['filing_steps']) for s in FILING_SYSTEMS.values())} total steps")
    print(f"   Reports: EFILING_GUIDE.md + efiling_guide.json")

if __name__ == '__main__':
    main()
