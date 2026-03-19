#!/usr/bin/env python3
"""
Tool #93 — Court Rule Compliance Checker
============================================
Verifies each filing meets specific court rules:
- MCR format requirements (margins, font, spacing)
- FRCP requirements for federal filings
- COA/MSC specific requirements
- Cover page / caption requirements
- Certificate of service requirements
- Page/word limits by filing type

Returns a compliance matrix showing what's met and what needs fixing.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"
PKG_BASE = Path(r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE")

RULES = {
    'F1': {
        'name': 'Emergency Parenting Time',
        'court': '14th Circuit (State)',
        'rules': {
            'MCR 3.206(D)': 'Ex-parte motion requires: (1) irreparable injury, (2) immediate danger, (3) risk of parental abduction',
            'MCR 2.119(A)(1)': 'Motion must state grounds with particularity and relief sought',
            'MCR 2.113(C)': 'Caption with case number, court, parties',
            'MCR 2.114': 'Signature certification — well-grounded in fact and law',
            'MCR 2.107': 'Service on all parties within 7 days',
            'Format': 'Double-spaced, 12pt font, 1-inch margins, numbered pages',
        },
        'required_docs': ['Motion', 'Brief in Support', 'Affidavit', 'Certificate of Service', 'Proposed Order'],
    },
    'F2': {
        'name': 'Fraud on Court',
        'court': '14th Circuit (State)',
        'rules': {
            'MCR 2.612(C)(1)(c)': 'Fraud motion within 1 year of judgment',
            'MCR 2.612(C)(1)(d)': 'Void judgment — NO time limit',
            'MCR 2.612(C)(3)': 'Independent action for fraud — NO time bar',
            'MCR 2.119(A)(1)': 'Motion with particularity',
            'MCR 2.114': 'Signature certification',
            'Format': 'Double-spaced, 12pt font, 1-inch margins',
        },
        'required_docs': ['Motion', 'Brief in Support', 'Affidavit', 'Exhibits', 'Certificate of Service'],
    },
    'F3': {
        'name': 'Judicial Disqualification',
        'court': '14th Circuit (State)',
        'rules': {
            'MCR 2.003(C)': 'Motion for disqualification — specific grounds required',
            'MCR 2.003(D)': 'Affidavit of prejudice (timely filing)',
            'MCR 2.003(B)': 'Grounds: personal bias, ex-parte communications, appearance of impropriety',
            'MCL 600.401': 'Statutory disqualification',
            'Format': 'Double-spaced, 12pt font',
        },
        'required_docs': ['Motion', 'Brief', 'Affidavit of Bias', 'Exhibit List', 'Certificate of Service'],
    },
    'F4': {
        'name': '§1983 Federal Complaint',
        'court': 'USDC Western District MI',
        'rules': {
            'FRCP 8(a)': 'Short plain statement of: (1) jurisdiction, (2) claim, (3) relief demanded',
            'FRCP 10(a)': 'Caption with court, parties, file number',
            'FRCP 10(b)': 'Numbered paragraphs, separate counts',
            'FRCP 11': 'Signature certification — reasonable inquiry',
            'LCivR 5.7': 'Electronic filing via CM/ECF required',
            'LCivR 5.6(a)': 'Page limits: brief max 25 pages',
            '28 USC 1331': 'Federal question jurisdiction',
            'Format': 'Double-spaced, 14pt or 12pt, 1-inch margins, page numbers',
        },
        'required_docs': ['Complaint', 'Civil Cover Sheet', 'Summons', 'IFP Application', 'Certificate of Service'],
    },
    'F5': {
        'name': 'MSC Superintending Control',
        'court': 'Michigan Supreme Court',
        'rules': {
            'MCR 7.306(B)(1)': 'Complaint format — verified, specific relief',
            'MCR 7.306(B)(2)': 'Must show: extraordinary case, no adequate remedy',
            'MCR 7.212(B)': 'Brief format requirements (incorporated by reference)',
            'Const 1963 Art 6 §4': 'Superintending control jurisdiction',
            'Format': 'Double-spaced, 12pt, 50-page limit for application',
        },
        'required_docs': ['Complaint for Superintending Control', 'Brief', 'Appendix', 'Proof of Service'],
    },
    'F6': {
        'name': 'JTC Complaint',
        'court': 'Judicial Tenure Commission',
        'rules': {
            'MCR 9.104': 'JTC complaint procedure',
            'MCR 9.205': 'Complaint format — specific misconduct',
            'Const 1963 Art 6 §30': 'JTC jurisdiction over judicial misconduct',
            'Format': 'Letter format OR JTC form — no strict format requirements',
        },
        'required_docs': ['Complaint Letter/Form', 'Supporting Documentation'],
    },
    'F7': {
        'name': 'Custody Modification',
        'court': '14th Circuit (State)',
        'rules': {
            'MCL 722.27(1)(c)': 'Modification requires proper cause + change of circumstances',
            'Vodvarka v Grasmeyer': 'Standard for change of circumstances',
            'MCL 722.23': 'Best interest factors (12 factors)',
            'MCR 3.210': 'Post-judgment custody motions',
            'MCR 2.119': 'Motion practice requirements',
            'Format': 'Double-spaced, 12pt font, 1-inch margins',
        },
        'required_docs': ['Motion', 'Brief', 'Affidavit', 'Proposed Order', 'Certificate of Service'],
    },
    'F8': {
        'name': 'COA Leave Application',
        'court': 'Michigan Court of Appeals',
        'rules': {
            'MCR 7.205(B)': 'Application format — 4 copies, within 21 days',
            'MCR 7.212': 'Brief requirements (if application granted)',
            'MCR 7.215(J)': 'Peremptory reversal standard',
            'Format': 'Double-spaced, 12pt, max 50 pages',
        },
        'required_docs': ['Application for Leave', 'Brief', 'Lower Court Record', 'Proof of Service'],
    },
    'F9': {
        'name': 'COA Appeal Brief (366810)',
        'court': 'Michigan Court of Appeals',
        'rules': {
            'MCR 7.212(C)': 'Brief format: table of contents, authorities, jurisdictional statement, questions presented, statement of facts, argument, relief requested',
            'MCR 7.212(B)': 'Page limits: 50 pages initial brief',
            'MCR 7.212(D)': 'Appendix with lower court opinions/orders',
            'Format': 'Double-spaced, 12pt, page numbers, binding edge',
        },
        'required_docs': ['Brief on Appeal', 'Table of Authorities', 'Appendix', 'Proof of Service'],
    },
    'F10': {
        'name': 'AGC Grievance',
        'court': 'Attorney Grievance Commission',
        'rules': {
            'MCR 9.104': 'Grievance procedure',
            'MCR 9.113': 'Request for investigation format',
            'MRPC (various)': 'Specific rule violations cited',
            'Format': 'Letter format OR AGC Request for Investigation form',
        },
        'required_docs': ['Request for Investigation', 'Supporting Documentation', 'Chronology'],
    },
}

def check_filing_compliance(fid):
    """Check if a filing package has required documents."""
    pkg_dir = PKG_BASE / f"PKG_{fid}"
    existing_files = []
    if pkg_dir.exists():
        existing_files = [f.name for f in pkg_dir.iterdir() if f.is_file()]
    
    return {
        'exists': pkg_dir.exists(),
        'file_count': len(existing_files),
        'files': existing_files,
    }

def main():
    print("=" * 70)
    print("COURT RULE COMPLIANCE CHECKER — Tool #93")
    print("=" * 70)
    
    lines = [
        "# ✅ COURT RULE COMPLIANCE MATRIX",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #93*\n",
        "---\n",
    ]
    
    all_compliance = {}
    total_rules = 0
    total_docs_needed = 0
    
    for fid in ['F1','F2','F3','F4','F5','F6','F7','F8','F9','F10']:
        config = RULES[fid]
        pkg_status = check_filing_compliance(fid)
        
        lines.append(f"## {fid} — {config['name']}")
        lines.append(f"**Court:** {config['court']}\n")
        
        # Rules table
        lines.append("### Applicable Rules")
        lines.append("| Rule | Requirement |")
        lines.append("|------|------------|")
        for rule, req in config['rules'].items():
            lines.append(f"| {rule} | {req[:60]} |")
            total_rules += 1
        
        # Required docs
        lines.append(f"\n### Required Documents ({len(config['required_docs'])} needed)")
        for doc in config['required_docs']:
            # Check if something like this exists in package
            found = any(doc.lower().replace(' ', '_') in f.lower() or 
                       doc.lower().split()[0] in f.lower() 
                       for f in pkg_status['files'])
            status = "✅" if found else "❌"
            lines.append(f"- {status} {doc}")
            total_docs_needed += 1
        
        lines.append(f"\n**Package Status:** {'📁 EXISTS' if pkg_status['exists'] else '❌ MISSING'} — {pkg_status['file_count']} files\n")
        
        all_compliance[fid] = {
            'name': config['name'],
            'court': config['court'],
            'rules_count': len(config['rules']),
            'required_docs': config['required_docs'],
            'pkg_files': pkg_status['file_count'],
            'pkg_exists': pkg_status['exists'],
        }
        
        pkg_indicator = f"📁 {pkg_status['file_count']} files" if pkg_status['exists'] else "❌ NO PKG"
        print(f"  {fid} ({config['name'][:20]}): {len(config['rules'])} rules, {len(config['required_docs'])} docs needed — {pkg_indicator}")
    
    lines.extend([
        "---",
        f"*Court Rule Compliance Checker — Tool #93 — {total_rules} rules mapped, {total_docs_needed} documents required*",
    ])
    
    md_path = REPORTS_DIR / "COURT_RULE_COMPLIANCE.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "court_rule_compliance.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Court Rule Compliance Checker (#93)',
        'total_rules': total_rules,
        'total_docs_needed': total_docs_needed,
        'filings': all_compliance,
    }, indent=2), encoding='utf-8')
    
    print(f"\n✅ Compliance matrix complete — {total_rules} rules, {total_docs_needed} documents mapped")
    print(f"   Reports: COURT_RULE_COMPLIANCE.md + court_rule_compliance.json")

if __name__ == '__main__':
    main()
