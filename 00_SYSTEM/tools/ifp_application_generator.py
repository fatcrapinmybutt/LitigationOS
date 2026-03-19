#!/usr/bin/env python3
"""
Tool #60 — IFP Application Generator
========================================
Generates In Forma Pauperis (fee waiver) applications for:
1. Federal court (28 USC §1915) — USDC Western District MI
2. Michigan courts — MC 20 (Application to Waive Fees)
3. Michigan Supreme Court — separate application
4. Court of Appeals — separate application

Populates known fields from verified party data.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"
PKG_BASE = Path(r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE")

# Verified party data
PLAINTIFF = {
    'name': 'Andrew James Pigors',
    'address': '1977 Whitehall Road, Lot 17',
    'city_state_zip': 'North Muskegon, MI 49445',
    'phone': '(231) 903-5690',
    'email': 'andrewjpigors@gmail.com',
    'status': 'Pro Se Plaintiff',
}

IFP_APPLICATIONS = {
    'federal': {
        'title': 'Application to Proceed In Forma Pauperis (28 USC §1915)',
        'court': 'United States District Court, Western District of Michigan',
        'case': 'Pigors v. Watson et al.',
        'form': 'AO 240 (Application to Proceed in District Court Without Prepaying Fees)',
        'filing': 'F4 — 42 USC §1983 Civil Rights Complaint',
        'fee': '$405.00 (filing fee)',
        'sections': [
            {
                'heading': 'INSTRUCTIONS',
                'content': [
                    'Complete AO 240 form from uscourts.gov',
                    'Attach to F4 §1983 complaint',
                    'File via CM/ECF (PACER) or in person at USDC Grand Rapids',
                    'Court address: 399 Federal Building, 110 Michigan St NW, Grand Rapids, MI 49503',
                ],
            },
            {
                'heading': 'REQUIRED INFORMATION (Andrew to Complete)',
                'content': [
                    '[  ] Current monthly income from all sources',
                    '[  ] Current monthly expenses (rent, utilities, food, medical, transportation)',
                    '[  ] List of dependents (including L.D.W.)',
                    '[  ] Bank account balances',
                    '[  ] Vehicle value and loan balance',
                    '[  ] Any other assets or debts',
                    '[  ] Employment status and employer information',
                    '[  ] Any government assistance received (SNAP, Medicaid, SSI, etc.)',
                ],
            },
            {
                'heading': 'LEGAL STANDARD',
                'content': [
                    '28 USC §1915(a)(1): Court may authorize proceeding without prepayment "if the person is unable to pay such fees or give security therefor."',
                    'Standard: Not destitution, but inability to pay fees without depriving self or dependents of necessities.',
                    'Adkins v E.I. DuPont de Nemours & Co., 335 US 331 (1948)',
                ],
            },
        ],
    },
    'michigan_circuit': {
        'title': 'Application to Waive Fees — MC 20',
        'court': '14th Circuit Court, Muskegon County',
        'case': 'Pigors v. Watson, 2024-001507-DC',
        'form': 'MC 20 (Fee Waiver Application)',
        'filing': 'F1, F2, F3, F7 — Circuit Court filings',
        'fee': '$175.00 per filing (circuit court)',
        'sections': [
            {
                'heading': 'INSTRUCTIONS',
                'content': [
                    'Download MC 20 from courts.michigan.gov/scao-forms',
                    'One MC 20 covers ALL filings in same case number',
                    'File with first circuit court filing (F1 recommended)',
                    'If approved, covers F2, F3, F7 in same case',
                ],
            },
            {
                'heading': 'AUTO-FILLED FIELDS',
                'content': [
                    f'Plaintiff: {PLAINTIFF["name"]}',
                    f'Address: {PLAINTIFF["address"]}, {PLAINTIFF["city_state_zip"]}',
                    f'Phone: {PLAINTIFF["phone"]}',
                    'Case No: 2024-001507-DC',
                    'Court: 14th Circuit Court, Muskegon County',
                    'Judge: Hon. Jenny L. McNeill',
                ],
            },
            {
                'heading': 'REQUIRED INFORMATION (Andrew to Complete)',
                'content': [
                    '[  ] Monthly income',
                    '[  ] Monthly expenses',
                    '[  ] Dependents',
                    '[  ] Whether receiving public assistance (MCL 600.2963)',
                    '[  ] Bank balances',
                    '[  ] Sign and date under oath',
                ],
            },
        ],
    },
    'michigan_coa': {
        'title': 'Application to Waive Fees — Court of Appeals',
        'court': 'Michigan Court of Appeals',
        'case': 'COA 366810',
        'form': 'MC 20 (same form, filed with COA)',
        'filing': 'F8, F9 — COA filings',
        'fee': '$375.00 (COA filing fee)',
        'sections': [
            {
                'heading': 'INSTRUCTIONS',
                'content': [
                    'Use MC 20 form, mark Court of Appeals',
                    'File with application for leave (F8) or opening brief (F9)',
                    'COA 366810 already filed — check if fee was paid or waived',
                    'If fee already paid for 366810, may need separate MC 20 for F8 (new application)',
                ],
            },
        ],
    },
    'michigan_msc': {
        'title': 'Application to Waive Fees — Michigan Supreme Court',
        'court': 'Michigan Supreme Court',
        'case': 'New case number assigned on filing',
        'form': 'MC 20 (same form, filed with MSC)',
        'filing': 'F5 — MSC Complaint for Superintending Control',
        'fee': '$375.00 (MSC filing fee)',
        'sections': [
            {
                'heading': 'INSTRUCTIONS',
                'content': [
                    'Use MC 20 form, mark Supreme Court',
                    'File with F5 complaint for superintending control',
                    'MSC Clerk: PO Box 30052, Lansing, MI 48909',
                    'E-file via TrueFiling (trufiling.com/michigan-supreme-court)',
                ],
            },
        ],
    },
    'jtc': {
        'title': 'JTC Complaint — No Filing Fee',
        'court': 'Judicial Tenure Commission',
        'case': 'New complaint',
        'form': 'JTC Complaint Form (free)',
        'filing': 'F6 — JTC Misconduct Complaint',
        'fee': '$0 (no fee for JTC complaints)',
        'sections': [
            {
                'heading': 'NOTE',
                'content': [
                    'JTC complaints are FREE — no filing fee required',
                    'Mail to: 3034 W Grand Blvd, Ste 8-450, Detroit, MI 48202',
                    'Or email: jtc@jtc.courts.mi.gov',
                ],
            },
        ],
    },
    'agc': {
        'title': 'AGC Grievance — No Filing Fee',
        'court': 'Attorney Grievance Commission',
        'case': 'New grievance against Jennifer Barnes P55406',
        'form': 'AGC Request for Investigation Form (free)',
        'filing': 'F10 — AGC Attorney Misconduct Complaint',
        'fee': '$0 (no fee for AGC grievances)',
        'sections': [
            {
                'heading': 'NOTE',
                'content': [
                    'AGC grievances are FREE — no filing fee required',
                    'File online: agcmi.com',
                    'Or mail: 535 Griswold, Ste 1700, Detroit, MI 48226',
                ],
            },
        ],
    },
}

def main():
    print("=" * 70)
    print("IFP APPLICATION GENERATOR — Tool #60")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)
    
    lines = [
        "# IN FORMA PAUPERIS (FEE WAIVER) APPLICATIONS",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n",
        "## Fee Summary",
        "| Court | Filing | Fee | IFP Form |",
        "|-------|--------|-----|----------|",
    ]
    
    total_fees = 0
    for key, app in IFP_APPLICATIONS.items():
        fee_num = float(app['fee'].replace('$','').replace(',','').split()[0])
        total_fees += fee_num
        lines.append(f"| {app['court'][:30]} | {app['filing'][:25]} | {app['fee']} | {app['form'][:30]} |")
        print(f"  {app['court'][:40]}: {app['fee']}")
    
    lines.append(f"| **TOTAL** | | **${total_fees:,.2f}** | |")
    lines.append(f"\n> **If all IFP applications are approved, Andrew saves ${total_fees:,.2f} in filing fees.**")
    lines.append(f"> **Free filings (JTC + AGC): $0 — no IFP needed.**\n")
    
    for key, app in IFP_APPLICATIONS.items():
        lines.extend([
            f"\n---\n## {app['title']}",
            f"**Court:** {app['court']}",
            f"**Case:** {app['case']}",
            f"**Form:** {app['form']}",
            f"**Filing:** {app['filing']}",
            f"**Fee if not waived:** {app['fee']}\n",
        ])
        
        for section in app['sections']:
            lines.append(f"### {section['heading']}")
            for item in section['content']:
                lines.append(f"- {item}")
            lines.append("")
    
    lines.extend([
        "\n---",
        "## Andrew's Action Items",
        "1. **Gather financial information** — income, expenses, bank balances, assets, debts",
        "2. **Download MC 20** from courts.michigan.gov/scao-forms",
        "3. **Download AO 240** from uscourts.gov (for federal court)",
        "4. **Complete both forms** with actual financial data",
        "5. **Sign under oath** (MC 20 requires notarization or signing under penalty of perjury)",
        "6. **File MC 20 with first circuit court filing** (covers F1, F2, F3, F7)",
        "7. **File separate MC 20 with COA** (covers F8, F9)",
        "8. **File separate MC 20 with MSC** (covers F5)",
        "9. **File AO 240 with federal complaint** (covers F4)",
        "10. **JTC and AGC are free** — no fee waiver needed",
        "",
        f"*Total potential savings: ${total_fees:,.2f}*",
    ])
    
    md_path = REPORTS_DIR / "IFP_APPLICATIONS.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "ifp_applications.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'IFP Application Generator (#60)',
        'total_fees': total_fees,
        'applications': IFP_APPLICATIONS,
        'plaintiff': PLAINTIFF,
    }, indent=2, default=str), encoding='utf-8')
    
    # Also save IFP guide to each relevant package
    for fid, pkg_info in [
        ('F1', 'michigan_circuit'), ('F4', 'federal'), 
        ('F5', 'michigan_msc'), ('F8', 'michigan_coa'), ('F9', 'michigan_coa'),
    ]:
        pkg_dirs = list(PKG_BASE.glob(f"PKG_{fid}_*"))
        if pkg_dirs:
            ifp_path = pkg_dirs[0] / "09_IFP_APPLICATION.md"
            app = IFP_APPLICATIONS[pkg_info]
            ifp_lines = [
                f"# {app['title']}",
                f"**Court:** {app['court']}",
                f"**Form:** {app['form']}",
                f"**Fee:** {app['fee']}\n",
            ]
            for section in app['sections']:
                ifp_lines.append(f"## {section['heading']}")
                for item in section['content']:
                    ifp_lines.append(f"- {item}")
                ifp_lines.append("")
            ifp_path.write_text('\n'.join(ifp_lines), encoding='utf-8')
            print(f"  ✅ {fid}: 09_IFP_APPLICATION.md saved")
    
    print(f"\n✅ Total fees: ${total_fees:,.2f}")
    print(f"   Reports: {md_path.name}, {json_path.name}")
    print(f"   IFP guides saved to F1, F4, F5, F8, F9 packages")

if __name__ == '__main__':
    main()
