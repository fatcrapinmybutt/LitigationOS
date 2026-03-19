#!/usr/bin/env python3
"""
Tool #71 — E-Filing Package Assembler
=========================================
Creates court-specific e-filing bundles per each court's requirements:
- MiFILE (Michigan state courts) — PDF format, size limits
- CM/ECF (Federal USDC WDMI) — PDF format, naming conventions
- TrueFiling (COA/MSC) — PDF format, page limits
- JTC / AGC — Letter format, no specific e-filing system

Generates a submission checklist for each filing.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"
PKG_BASE = Path(r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE")
PDF_DIR = PKG_BASE / "PDF_OUTPUT"

FILINGS = {
    'F1': {
        'name': 'Emergency Parenting Time Motion',
        'court': '14th Circuit Court, Family Division',
        'system': 'MiFILE',
        'case_no': '2024-001507-DC',
        'documents': [
            ('01_MAIN_FILING.md', 'Motion for Emergency Parenting Time', True),
            ('02_AFFIDAVIT.md', 'Supporting Affidavit', True),
            ('03_EXHIBIT_INDEX.md', 'Exhibit Index', True),
            ('04_CERTIFICATE_OF_SERVICE.md', 'Certificate of Service', True),
            ('05_COURT_FORMS_CHECKLIST.md', 'Court Forms Reference', False),
            ('06_CAPTION.md', 'Caption Page', True),
            ('09_IFP_APPLICATION.md', 'IFP Application (MC 20)', True),
        ],
        'filing_fee': '$175 (waived with IFP)',
        'instructions': [
            'Log into MiFILE (mifile.courts.michigan.gov)',
            'Select "14th Circuit Court"',
            'Select existing case: 2024-001507-DC',
            'Filing type: "Motion"',
            'Upload: Motion PDF, Affidavit PDF, Exhibits PDF, Certificate of Service PDF',
            'Upload MC 20 (Fee Waiver) as separate filing if not already on file',
            'Mark as EMERGENCY to request expedited hearing',
            'Pay fee or submit IFP simultaneously',
        ],
    },
    'F2': {
        'name': 'Fraud Upon the Court',
        'court': '14th Circuit Court, Civil Division',
        'system': 'MiFILE',
        'case_no': 'NEW CASE',
        'documents': [
            ('01_MAIN_FILING.md', 'Complaint for Fraud Upon the Court', True),
            ('02_AFFIDAVIT.md', 'Supporting Affidavit', True),
            ('03_EXHIBIT_INDEX.md', 'Exhibit Index', True),
            ('04_CERTIFICATE_OF_SERVICE.md', 'Certificate of Service', True),
            ('06_CAPTION.md', 'Caption Page', True),
        ],
        'filing_fee': '$175 (waived with IFP)',
        'instructions': [
            'Log into MiFILE',
            'Select "14th Circuit Court"',
            'Select "New Case Filing"',
            'Case type: "Civil — General Civil"',
            'Upload: Complaint PDF, Affidavit PDF, Exhibits PDF',
            'Request summons issuance',
            'Arrange personal service via process server (not yourself)',
        ],
    },
    'F3': {
        'name': 'Judicial Disqualification',
        'court': '14th Circuit Court, Family Division',
        'system': 'MiFILE',
        'case_no': '2024-001507-DC',
        'documents': [
            ('01_MAIN_FILING.md', 'Motion for Disqualification', True),
            ('01B_BRIEF.md', 'Supporting Brief', True),
            ('02_AFFIDAVIT.md', 'Supporting Affidavit', True),
            ('03_EXHIBIT_INDEX.md', 'Exhibit Index', True),
            ('04_CERTIFICATE_OF_SERVICE.md', 'Certificate of Service', True),
            ('06_CAPTION.md', 'Caption Page', True),
        ],
        'filing_fee': '$0 (motion in existing case)',
        'instructions': [
            'Log into MiFILE',
            'Select existing case: 2024-001507-DC',
            'Filing type: "Motion — Disqualification of Judge"',
            'Upload: Motion PDF, Brief PDF, Affidavit PDF, Exhibits PDF, Cert of Service',
            'Judge has 14 days to respond (MCR 2.003(D)(3))',
            'If no recusal, automatically referred to chief judge',
        ],
    },
    'F4': {
        'name': '42 USC §1983 Federal Civil Rights',
        'court': 'USDC Western District of Michigan',
        'system': 'CM/ECF (PACER)',
        'case_no': 'NEW CASE',
        'documents': [
            ('01_MAIN_FILING.md', 'Complaint under 42 USC §1983', True),
            ('01B_BRIEF.md', 'Memorandum of Law', True),
            ('02_AFFIDAVIT.md', 'Declaration under 28 USC §1746', True),
            ('03_EXHIBIT_INDEX.md', 'Exhibit Index', True),
            ('04_CERTIFICATE_OF_SERVICE.md', 'Certificate of Service', True),
            ('06_CAPTION.md', 'Civil Cover Sheet (JS 44)', True),
            ('09_IFP_APPLICATION.md', 'IFP Application (AO 240)', True),
        ],
        'filing_fee': '$405 (waived with IFP)',
        'instructions': [
            'Log into CM/ECF (ecf.miwd.uscourts.gov)',
            'Select "Civil" → "Open a New Civil Case"',
            'Nature of Suit: 440 (Other Civil Rights)',
            'Cause of Action: 42 USC §1983',
            'Upload: Complaint, Memorandum, Declaration, Exhibits',
            'File AO 240 (IFP) simultaneously',
            'File Civil Cover Sheet (JS 44)',
            'If IFP granted, request US Marshals service (FRCP 4(c)(3))',
            'Serve Michigan AG: certified mail to Capitol, Lansing MI',
        ],
    },
    'F5': {
        'name': 'MSC Superintending Control',
        'court': 'Michigan Supreme Court',
        'system': 'TrueFiling',
        'case_no': 'NEW CASE',
        'documents': [
            ('01_MAIN_FILING.md', 'Complaint for Superintending Control', True),
            ('01B_BRIEF.md', 'Supporting Brief', True),
            ('02_AFFIDAVIT.md', 'Supporting Affidavit', True),
            ('03_EXHIBIT_INDEX.md', 'Exhibit Index', True),
            ('04_CERTIFICATE_OF_SERVICE.md', 'Certificate of Service', True),
            ('06_CAPTION.md', 'Caption Page', True),
            ('09_IFP_APPLICATION.md', 'IFP Application (MC 20)', True),
        ],
        'filing_fee': '$375 (waived with IFP)',
        'instructions': [
            'Log into TrueFiling (truefiling.com)',
            'Select "Michigan Supreme Court"',
            'Filing type: "Original Action — Superintending Control"',
            'Upload all documents as single combined PDF or separate PDFs',
            'File MC 20 for fee waiver',
            'Serve all parties via first-class mail',
        ],
    },
    'F6': {
        'name': 'JTC Complaint',
        'court': 'Judicial Tenure Commission',
        'system': 'Mail/Email',
        'case_no': 'N/A',
        'documents': [
            ('01_MAIN_FILING.md', 'JTC Complaint', True),
            ('02_AFFIDAVIT.md', 'Supporting Declaration', False),
            ('03_EXHIBIT_INDEX.md', 'Evidence Summary', False),
        ],
        'filing_fee': 'FREE',
        'instructions': [
            'Print complaint and attachments',
            'Mail to: JTC, 3034 W Grand Blvd Ste 8-450, Detroit MI 48202',
            'OR email to: jtc@jtc.courts.mi.gov',
            'No specific format required — letter format acceptable',
            'Include all supporting evidence as attachments',
            'JTC will investigate and respond (timeline varies)',
        ],
    },
    'F7': {
        'name': 'Custody Modification',
        'court': '14th Circuit Court, Family Division',
        'system': 'MiFILE',
        'case_no': '2024-001507-DC',
        'documents': [
            ('01_MAIN_FILING.md', 'Motion for Custody Modification', True),
            ('01B_BRIEF.md', 'Supporting Brief', True),
            ('02_AFFIDAVIT.md', 'Supporting Affidavit', True),
            ('03_EXHIBIT_INDEX.md', 'Exhibit Index', True),
            ('04_CERTIFICATE_OF_SERVICE.md', 'Certificate of Service', True),
            ('06_CAPTION.md', 'Caption Page', True),
        ],
        'filing_fee': '$0 (motion in existing case)',
        'instructions': [
            'Log into MiFILE',
            'Select existing case: 2024-001507-DC',
            'Filing type: "Motion — Modification of Custody"',
            'Upload all documents',
            'Serve Emily Watson — certified mail',
            'Request hearing date',
        ],
    },
    'F8': {
        'name': 'COA Application for Leave',
        'court': 'Michigan Court of Appeals',
        'system': 'TrueFiling',
        'case_no': 'NEW APPLICATION',
        'documents': [
            ('01_MAIN_FILING.md', 'Application for Leave to Appeal', True),
            ('02_AFFIDAVIT.md', 'Supporting Affidavit', True),
            ('03_EXHIBIT_INDEX.md', 'Exhibit Index', True),
            ('04_CERTIFICATE_OF_SERVICE.md', 'Certificate of Service', True),
            ('06_CAPTION.md', 'Caption Page', True),
            ('09_IFP_APPLICATION.md', 'IFP Application (MC 20)', True),
        ],
        'filing_fee': '$375 (waived with IFP)',
        'instructions': [
            'Log into TrueFiling',
            'Select "Michigan Court of Appeals"',
            'Filing type: "Application for Leave to Appeal"',
            'Upload all documents',
            'File MC 20 for fee waiver',
            'Must be filed within 21 days of order (MCR 7.205(A))',
        ],
    },
    'F9': {
        'name': 'COA 366810 Appeal Brief',
        'court': 'Michigan Court of Appeals',
        'system': 'TrueFiling',
        'case_no': 'COA 366810',
        'documents': [
            ('01_MAIN_FILING.md', 'Appellant Brief', True),
            ('01B_BRIEF.md', 'Full Appellate Brief', True),
            ('02_AFFIDAVIT.md', 'Supporting Declaration', True),
            ('03_EXHIBIT_INDEX.md', 'Appendix / Exhibit Index', True),
            ('04_CERTIFICATE_OF_SERVICE.md', 'Certificate of Service', True),
            ('06_CAPTION.md', 'Caption Page', True),
        ],
        'filing_fee': '$0 (already docketed)',
        'instructions': [
            'Log into TrueFiling',
            'Select existing case: COA 366810',
            'Filing type: "Appellant Brief"',
            'Upload brief + appendix as separate PDFs',
            'Brief must comply with MCR 7.212 (format, length, margins)',
            'Serve Emily Watson — first-class mail',
            'CALL COA CLERK FIRST: (517) 373-0786 to confirm deadline',
        ],
    },
    'F10': {
        'name': 'AGC Attorney Grievance',
        'court': 'Attorney Grievance Commission',
        'system': 'Online/Mail',
        'case_no': 'N/A',
        'documents': [
            ('01_MAIN_FILING.md', 'AGC Grievance Complaint', True),
            ('02_AFFIDAVIT.md', 'Supporting Declaration', False),
            ('03_EXHIBIT_INDEX.md', 'Evidence Summary', False),
        ],
        'filing_fee': 'FREE',
        'instructions': [
            'File online at: agcmi.com',
            'OR mail to: 535 Griswold Ste 1700, Detroit MI 48226',
            'No specific format required',
            'Include: complaint, supporting evidence, relevant filings',
            'AGC will investigate — response timeline varies',
        ],
    },
}

def check_pdfs():
    """Check which PDFs exist."""
    pdf_status = {}
    for filing_id, filing in FILINGS.items():
        pkg_dir = PKG_BASE / f"PKG_{filing_id}"
        pdf_subdir = PDF_DIR / filing_id if PDF_DIR.exists() else None
        
        pdfs_found = 0
        if pdf_subdir and pdf_subdir.exists():
            pdfs_found = len(list(pdf_subdir.glob("*.pdf")))
        
        md_found = 0
        if pkg_dir.exists():
            md_found = len([f for f in pkg_dir.glob("*.md") if '.bak.' not in f.name])
        
        pdf_status[filing_id] = {
            'pdfs': pdfs_found,
            'markdown': md_found,
            'required_docs': len([d for d in filing['documents'] if d[2]]),
        }
    
    return pdf_status

def main():
    print("=" * 70)
    print("E-FILING PACKAGE ASSEMBLER — Tool #71")
    print("=" * 70)
    
    pdf_status = check_pdfs()
    
    lines = [
        "# 📦 E-FILING PACKAGE ASSEMBLY GUIDE",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        f"*10 filings across 5 courts/systems*\n",
        "---\n",
    ]
    
    for filing_id in sorted(FILINGS.keys(), key=lambda x: int(x[1:])):
        filing = FILINGS[filing_id]
        status = pdf_status.get(filing_id, {})
        
        print(f"\n  {filing_id}: {filing['name']}")
        print(f"    Court: {filing['court']}")
        print(f"    System: {filing['system']}")
        print(f"    Fee: {filing['filing_fee']}")
        print(f"    Docs: {status.get('markdown', 0)} MD, {status.get('pdfs', 0)} PDF")
        
        lines.append(f"## {filing_id}: {filing['name']}")
        lines.append(f"- **Court:** {filing['court']}")
        lines.append(f"- **E-Filing System:** {filing['system']}")
        lines.append(f"- **Case No:** {filing['case_no']}")
        lines.append(f"- **Filing Fee:** {filing['filing_fee']}")
        lines.append(f"- **Status:** {status.get('markdown', 0)} docs ready, {status.get('pdfs', 0)} PDFs\n")
        
        lines.append("### Documents to Upload")
        lines.append("| Doc | Description | Required |")
        lines.append("|-----|-------------|----------|")
        for doc_file, doc_name, required in filing['documents']:
            req = "✅ YES" if required else "Optional"
            lines.append(f"| {doc_file} | {doc_name} | {req} |")
        
        lines.append("\n### Step-by-Step Instructions")
        for i, step in enumerate(filing['instructions'], 1):
            lines.append(f"{i}. {step}")
        
        lines.append("\n---\n")
    
    # Summary table
    lines.extend([
        "## E-Filing System Summary",
        "| System | Filings | URL |",
        "|--------|---------|-----|",
        "| MiFILE | F1, F2, F3, F7 | mifile.courts.michigan.gov |",
        "| CM/ECF (PACER) | F4 | ecf.miwd.uscourts.gov |",
        "| TrueFiling | F5, F8, F9 | truefiling.com |",
        "| Mail/Email | F6, F10 | See instructions above |",
        "",
        f"*E-Filing Package Assembler — Tool #71*",
    ])
    
    md_path = REPORTS_DIR / "EFILING_ASSEMBLY_GUIDE.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "efiling_assembly.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'E-Filing Package Assembler (#71)',
        'filings': {k: {**v, 'pdf_status': pdf_status.get(k, {})} for k, v in FILINGS.items()},
    }, indent=2, default=str), encoding='utf-8')
    
    print(f"\n✅ E-filing guides generated for all 10 filings")
    print(f"   Reports: EFILING_ASSEMBLY_GUIDE.md + efiling_assembly.json")

if __name__ == '__main__':
    main()
