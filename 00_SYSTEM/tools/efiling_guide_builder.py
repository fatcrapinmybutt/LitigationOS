#!/usr/bin/env python3
"""
Tool #45 — E-Filing Guide Builder
====================================
Generates a complete e-filing guide for each court where Andrew needs to file.
Includes: registration URLs, filing procedures, fee schedules, format requirements,
and step-by-step instructions for pro se filers.

Courts covered:
- 14th Circuit Court (MiFILE) — F1, F2, F3, F7
- Michigan Court of Appeals (MiFILE/TrueFiling) — F8, F9
- Michigan Supreme Court (MiFILE/TrueFiling) — F5
- U.S. District Court, WDMI (CM/ECF via PACER) — F4
- Judicial Tenure Commission (mail/email) — F6
- Attorney Grievance Commission (mail/email) — F10
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

COURTS = {
    'circuit_14th': {
        'name': '14th Judicial Circuit Court, Family Division',
        'filings': ['F1', 'F2', 'F3', 'F7'],
        'system': 'MiFILE',
        'url': 'https://mifile.courts.michigan.gov',
        'registration': 'https://mifile.courts.michigan.gov/register',
        'pro_se': True,
        'fees': {
            'motion': '$20.00 (MCL 600.2529)',
            'complaint': '$175.00 (civil)',
            'response': '$0 (responses are free)',
            'ifp': 'Fee waiver via MC 20 (Affidavit & Order to Waive Fees)',
        },
        'format': {
            'file_type': 'PDF (searchable text, not scanned images)',
            'page_size': '8.5" x 11" (Letter)',
            'margins': '1" all sides',
            'font': '12-point proportional (Times New Roman, Arial)',
            'line_spacing': 'Double-spaced (briefs), Single-spaced (block quotes)',
            'page_limit': '20 pages for briefs (MCR 2.119(A)(2))',
            'file_size': '25 MB per document',
            'naming': 'Descriptive (e.g., "Motion_for_Disqualification.pdf")',
        },
        'steps': [
            'Register at mifile.courts.michigan.gov/register (select "Self-Represented Litigant")',
            'Verify email and complete profile',
            'Select "14th Circuit Court" → "Muskegon County"',
            'Select existing case number (2024-001507-DC or 2023-5907-PP)',
            'Upload PDF filing as "Lead Document"',
            'Upload exhibits as "Attachments" (separate PDFs)',
            'Pay filing fee or upload MC 20 fee waiver',
            'Submit — system generates timestamp and confirmation',
            'Download confirmation receipt for your records',
            'System auto-serves all registered parties electronically',
        ],
        'service': 'MiFILE handles electronic service to all registered parties. For unregistered parties (Emily Watson, if not on MiFILE), you must serve separately by mail per MCR 2.107.',
        'notes': [
            'MiFILE is MANDATORY for circuit courts as of 2024',
            'Pro se filers get full access — same as attorneys',
            'Emergency motions: File normally, then call clerk at (231) 724-6241',
            'Ex parte motions: Must include "EX PARTE" in document title',
            'Fee waiver: File MC 20 first, then file motions at $0',
        ],
    },
    'coa': {
        'name': 'Michigan Court of Appeals',
        'filings': ['F8', 'F9'],
        'system': 'MiFILE / TrueFiling',
        'url': 'https://mifile.courts.michigan.gov',
        'registration': 'https://mifile.courts.michigan.gov/register',
        'pro_se': True,
        'fees': {
            'application_leave': '$375.00',
            'claim_of_appeal': '$375.00',
            'motion': '$75.00',
            'ifp': 'Fee waiver via MC 20',
        },
        'format': {
            'file_type': 'PDF (searchable)',
            'page_size': '8.5" x 11"',
            'margins': '1" all sides',
            'font': '12-point proportional',
            'line_spacing': 'Double-spaced',
            'page_limit': '50 pages for briefs (MCR 7.212(B))',
            'word_limit': '16,000 words (alternative to page limit)',
            'file_size': '25 MB per document',
            'cover_color': 'Appellant = Blue (MCR 7.212(A)(1))',
        },
        'steps': [
            'Register at mifile.courts.michigan.gov (COA portal)',
            'For Case 366810: Select "Existing Case" → enter 366810',
            'Upload application/brief as Lead Document',
            'Upload appendix (MCR 7.212(G)) as separate attachment',
            'Include Certificate of Compliance (word count)',
            'Pay fee or upload MC 20 fee waiver',
            'Submit and save confirmation',
            'Serve lower court clerk by mail within 7 days',
        ],
        'service': 'E-filing serves all registered COA parties. Must also serve lower court clerk (14th Circuit) by mail. MCR 7.212(E).',
        'notes': [
            'COA Case 366810 already exists — file INTO this case',
            'Appendix REQUIRED (MCR 7.212(G)) — include key lower court orders',
            'Certificate of Compliance REQUIRED (MCR 7.212(D))',
            'Oral argument request: Include in brief caption',
            'Emergency relief: File motion separately with "EMERGENCY" label',
        ],
    },
    'msc': {
        'name': 'Michigan Supreme Court',
        'filings': ['F5'],
        'system': 'MiFILE / TrueFiling',
        'url': 'https://mifile.courts.michigan.gov',
        'registration': 'Same as COA registration',
        'pro_se': True,
        'fees': {
            'application_leave': '$375.00',
            'original_action': '$375.00',
            'motion': '$75.00',
            'ifp': 'Fee waiver via MC 20',
        },
        'format': {
            'file_type': 'PDF (searchable)',
            'page_size': '8.5" x 11"',
            'margins': '1" all sides',
            'font': '12-point proportional',
            'line_spacing': 'Double-spaced',
            'page_limit': '50 pages (MCR 7.306(D))',
            'cover_color': 'RED (Petitioner per MCR 7.312(A))',
        },
        'steps': [
            'Register at mifile.courts.michigan.gov (MSC portal)',
            'Select "New Case" for original action OR existing case for leave',
            'Upload petition as Lead Document',
            'Upload appendix as attachment',
            'RED cover page required for petitioner',
            'Pay fee or upload MC 20',
            'Submit',
            'Serve all respondents by mail within 7 days',
        ],
        'service': 'Must serve all named respondents (14th Circuit Court, Judge McNeill, Emily Watson) by certified mail. MCR 7.306(B)(5).',
        'notes': [
            'Original action petition (Const 1963, art 6, § 4)',
            'Must demonstrate COA inadequacy or futility',
            'Superintending control = extraordinary remedy',
            'Include COA case number (366810) for context',
        ],
    },
    'federal_wdmi': {
        'name': 'U.S. District Court, Western District of Michigan',
        'filings': ['F4'],
        'system': 'CM/ECF (via PACER)',
        'url': 'https://ecf.miwd.uscourts.gov',
        'registration': 'https://pacer.uscourts.gov/register',
        'pro_se': True,
        'fees': {
            'complaint': '$405.00',
            'ifp': 'Fee waiver via 28 U.S.C. § 1915 (in forma pauperis)',
        },
        'format': {
            'file_type': 'PDF (searchable)',
            'page_size': '8.5" x 11"',
            'margins': '1" all sides',
            'font': '12-point, double-spaced',
            'page_limit': 'No strict limit for complaints',
            'file_size': '35 MB per document',
        },
        'steps': [
            'Register at pacer.uscourts.gov (create PACER account)',
            'Request CM/ECF filing credentials from WDMI clerk',
            'Pro se: May need to file initial complaint by MAIL then get e-filing access',
            'Mail to: U.S. District Court, 399 Federal Building, 110 Michigan St NW, Grand Rapids, MI 49503',
            'Or call clerk: (616) 456-2381 for pro se e-filing procedures',
            'Include civil cover sheet (JS-44)',
            'Include summons for each defendant',
            'Pay $405 fee or file IFP affidavit (28 U.S.C. § 1915)',
            'After filing, court issues case number and summons',
            'Serve defendants within 90 days (Fed. R. Civ. P. 4(m))',
        ],
        'service': 'Must serve each defendant per Fed. R. Civ. P. 4. For Judge McNeill (in official capacity): serve Michigan Attorney General. For Emily Watson: personal service or certified mail.',
        'notes': [
            '42 U.S.C. § 1983 complaint — federal question jurisdiction',
            'No page limit but keep complaint focused (30-40 pages)',
            'Pro se filers may mail initial complaint if CM/ECF access not yet granted',
            'IFP: Must complete financial affidavit showing inability to pay',
            'Service on state officials: serve MI Attorney General per Fed. R. Civ. P. 4(j)(2)',
        ],
    },
    'jtc': {
        'name': 'Judicial Tenure Commission',
        'filings': ['F6'],
        'system': 'Mail / Email',
        'url': 'https://jtc.courts.mi.gov',
        'registration': 'No registration needed',
        'pro_se': True,
        'fees': {'complaint': '$0 (no filing fee)'},
        'format': {
            'file_type': 'Paper (mail) or PDF (email)',
            'page_limit': 'No limit',
        },
        'steps': [
            'Prepare written complaint describing judicial misconduct',
            'Include specific dates, case numbers, and descriptions',
            'Attach supporting documents (court records, transcripts)',
            'Mail to: Judicial Tenure Commission, 3034 W. Grand Blvd., Suite 8-450, Detroit, MI 48202',
            'Or email to: jtc@courts.mi.gov',
            'JTC will acknowledge receipt within 30 days',
            'Investigation is confidential until formal proceedings',
        ],
        'service': 'No service requirement — JTC handles notice to judge.',
        'notes': [
            'JTC complaints are CONFIDENTIAL — not public record',
            'JTC investigates independently — do not expect updates',
            'Include all documentary evidence with initial complaint',
            'No filing fee — free to file',
        ],
    },
    'agc': {
        'name': 'Attorney Grievance Commission',
        'filings': ['F10'],
        'system': 'Online Form / Mail',
        'url': 'https://www.agcmi.com',
        'registration': 'No registration needed',
        'pro_se': True,
        'fees': {'complaint': '$0 (no filing fee)'},
        'format': {
            'file_type': 'Online form or paper',
            'page_limit': 'No limit',
        },
        'steps': [
            'Visit agcmi.com → "File a Complaint"',
            'Complete online request for investigation form',
            'Or mail to: AGC, 535 Griswold St., Suite 1700, Detroit, MI 48226',
            'Include attorney name, bar number (P55406 for Barnes)',
            'Describe specific misconduct with dates',
            'Attach supporting documents',
            'AGC will acknowledge within 21 days',
        ],
        'service': 'No service requirement.',
        'notes': [
            'File against Jennifer Barnes (P55406)',
            'Include specific rule violations (MRPC)',
            'AGC investigation is confidential',
        ],
    },
}

def main():
    print("=" * 70)
    print("E-FILING GUIDE BUILDER — Tool #45")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)
    
    # Build comprehensive markdown guide
    md = [
        "# COMPLETE E-FILING GUIDE — Pigors v. Watson",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n",
        "## Filing Overview\n",
        "| Filing | Court | System | Fee | Status |",
        "|--------|-------|--------|-----|--------|",
    ]
    
    for court_key, court in COURTS.items():
        for fid in court['filings']:
            fee = list(court['fees'].values())[0]
            md.append(f"| {fid} | {court['name'][:40]} | {court['system']} | {fee} | Ready to file |")
    
    md.append("")
    
    # Registration checklist
    md.extend([
        "## 🔑 Registration Checklist (Do These FIRST)\n",
        "- [ ] **MiFILE** — mifile.courts.michigan.gov/register (covers Circuit, COA, MSC)",
        "- [ ] **PACER/CM-ECF** — pacer.uscourts.gov/register (for federal court F4)",
        "- [ ] **AGC online** — agcmi.com (for F10, optional — can mail instead)",
        "",
        "**Note:** MiFILE registration covers 3 courts with one account.\n",
    ])
    
    # Detailed guide per court
    for court_key, court in COURTS.items():
        md.extend([
            f"---\n",
            f"## {court['name']}",
            f"**Filings:** {', '.join(court['filings'])}",
            f"**System:** {court['system']}",
            f"**URL:** {court['url']}",
            f"**Pro Se Access:** {'✅ Yes' if court['pro_se'] else '❌ No'}\n",
        ])
        
        md.append("### Fees")
        for fee_type, amount in court['fees'].items():
            md.append(f"- **{fee_type.replace('_', ' ').title()}**: {amount}")
        
        if 'format' in court and len(court['format']) > 2:
            md.append("\n### Format Requirements")
            for key, val in court['format'].items():
                md.append(f"- **{key.replace('_', ' ').title()}**: {val}")
        
        md.append(f"\n### Filing Steps")
        for i, step in enumerate(court['steps'], 1):
            md.append(f"{i}. {step}")
        
        md.append(f"\n### Service of Process")
        md.append(court['service'])
        
        if court.get('notes'):
            md.append(f"\n### ⚠️ Important Notes")
            for note in court['notes']:
                md.append(f"- {note}")
        
        md.append("")
    
    # Filing sequence recommendation
    md.extend([
        "---\n",
        "## 📋 Recommended Filing Sequence\n",
        "Based on strategic analysis (Tool #29 Priority Optimizer):\n",
        "1. **F3** (Disqualification) — Must go first, enables downstream filings",
        "2. **F4** (§1983 Federal) — Highest expected value ($317K), independent court",
        "3. **F6** (JTC Complaint) — Free, no deadline, builds pressure",
        "4. **F5** (MSC Petition) — Extraordinary remedy, strengthened by F3 denial",
        "5. **F9** (COA Appeal) — Already docketed as 366810",
        "6. **F8** (COA Superintending Control) — Alternative to F5",
        "7. **F7** (Custody Modification) — Requires new judge (after F3)",
        "8. **F1** (Emergency TRO) — File when custody is in immediate danger",
        "9. **F2** (PPO Termination) — Lower priority but needed",
        "10. **F10** (AGC Complaint) — Free, no deadline, independent process",
        "",
        "---\n",
        "## 💰 Fee Summary\n",
        "| Route | Total Fees | With IFP Waiver |",
        "|-------|-----------|----------------|",
        "| All Filings | ~$1,500+ | $0 (if all waivers granted) |",
        "| Circuit Only (F1-F3, F7) | ~$80 | $0 |",
        "| Federal (F4) | $405 | $0 |",
        "| COA (F8-F9) | $450-750 | $0 |",
        "| MSC (F5) | $375 | $0 |",
        "| JTC + AGC (F6, F10) | $0 | $0 |",
        "",
        "**Recommendation:** File MC 20 fee waiver with first circuit court filing. ",
        "File IFP affidavit (28 U.S.C. § 1915) with federal complaint.\n",
    ])
    
    guide_path = REPORTS_DIR / "E_FILING_GUIDE.md"
    guide_path.write_text('\n'.join(md), encoding='utf-8')
    
    json_path = REPORTS_DIR / "efiling_guide.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'E-Filing Guide Builder (#45)',
        'courts': {k: {
            'name': v['name'],
            'filings': v['filings'],
            'system': v['system'],
            'url': v['url'],
            'registration': v.get('registration', ''),
            'pro_se': v['pro_se'],
        } for k, v in COURTS.items()},
    }, indent=2), encoding='utf-8')
    
    print(f"\n✅ E-Filing Guide generated: {guide_path.name}")
    print(f"✅ JSON data: {json_path.name}")
    print(f"\n📊 Summary:")
    print(f"  Courts covered: {len(COURTS)}")
    print(f"  Filings mapped: {sum(len(c['filings']) for c in COURTS.values())}")
    print(f"  Registration portals: MiFILE, PACER, AGC online")
    print(f"  Fee waiver forms: MC 20 (state), IFP affidavit (federal)")

if __name__ == '__main__':
    main()
