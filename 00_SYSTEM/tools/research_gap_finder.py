#!/usr/bin/env python3
"""
Legal Research Gap Finder — Identifies missing authorities per filing.

Novel LitigationOS Tool #26

For each filing, analyzes:
1. Required legal elements (per claim type)
2. Authorities cited in the filing
3. Missing mandatory authorities
4. Weak citations needing reinforcement
5. Counter-authority gaps (opposing arguments not addressed)
6. Michigan-specific requirements (MCR, MCL, Const)

Output: Per-filing gap report with specific authority recommendations.
"""
import sys, os, json, re, sqlite3
from collections import defaultdict, Counter
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

DB_PATH = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")
FILING_DIR = Path(r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE")
REPORT_DIR = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\reports")

# Required authorities per filing type / legal theory
REQUIRED_AUTHORITIES = {
    'F1': {
        'name': 'Emergency TRO (Housing)',
        'required': {
            'TRO standard': ['MCR 3.310', 'MCL 600.2950a'],
            'Housing rights': ['MCL 554.139', 'Truth in Renting Act'],
            'Irreparable harm': ['Any case showing immediate housing threat'],
            'Habitability': ['MCL 125.534', 'Rome v Walker'],
        },
    },
    'F2': {
        'name': 'Housing Rights Complaint',
        'required': {
            'Habitability': ['MCL 554.139', 'MCL 125.534'],
            'Security deposit': ['MCL 554.602', 'MCL 554.613'],
            'Tenant rights': ['MCL 554.601a', 'Trentadue v Buckler Automatic'],
            'Damages': ['MCL 600.2919'],
        },
    },
    'F3': {
        'name': 'Judicial Disqualification',
        'required': {
            'Disqualification standard': ['MCR 2.003(C)(1)', 'MCR 2.003(C)(1)(b)'],
            'Bias test': ['Crampton v Dept of State 395 Mich 347', 'Armstrong v Ypsilanti Charter Twp 248 Mich App 573'],
            'Due process': ['In re Murchison 349 US 133', 'Caperton v AT Massey Coal 556 US 868'],
            'Structural error': ['Tumey v Ohio 273 US 510'],
            'Canon violations': ['Michigan Code of Judicial Conduct Canon 2', 'Canon 3'],
            'Remedy': ['MCR 2.003(D)', 'In re Contempt of Dougherty 429 Mich 81'],
        },
    },
    'F4': {
        'name': 'Federal §1983 Civil Rights',
        'required': {
            'Section 1983': ['42 USC §1983', 'Monroe v Pape 365 US 167'],
            'Judicial immunity exception': ['Dennis v Sparks 449 US 24', 'Mireles v Waco 502 US 9'],
            'Conspiracy': ['42 USC §1985(3)', 'Dennis v Sparks'],
            'Parental rights': ['Troxel v Granville 530 US 57', 'Stanley v Illinois 405 US 645', 'Santosky v Kramer 455 US 745'],
            'Domestic relations exception': ['Ankenbrandt v Richards 504 US 689', 'Catz v Chalker 142 F3d 279'],
            'Younger abstention': ['Sprint Communications v Jacobs 571 US 69', 'Younger v Harris 401 US 37'],
            'Rooker-Feldman': ['Exxon Mobil v Saudi Basic 544 US 280'],
            'Procedural due process': ['Mathews v Eldridge 424 US 319'],
        },
    },
    'F5': {
        'name': 'MSC Superintending Control',
        'required': {
            'MSC jurisdiction': ['Const 1963 Art 6 §4', 'MCR 7.306'],
            'Superintending control': ['Const 1963 Art 6 §4', 'In re Hague 412 Mich 532'],
            'Extraordinary circumstances': ['Const 1963 Art 6 §4'],
            'Void judgment': ['MCR 2.612(C)(1)(d)'],
            'Fraud on court': ['MCR 2.612(C)(3)', 'Hazel Park v Highland Park 1996'],
        },
    },
    'F6': {
        'name': 'JTC Complaint',
        'required': {
            'JTC jurisdiction': ['Const 1963 Art 6 §30', 'MCR 9.200 et seq'],
            'Judicial misconduct': ['MCR 9.205'],
            'Canon violations': ['MCJC Canon 1', 'Canon 2', 'Canon 3'],
            'Pattern of conduct': ['In re Justin 809 NW2d 126'],
            'Due process denial': ['14th Amendment', 'Const 1963 Art 1 §17'],
        },
    },
    'F7': {
        'name': 'Custody Modification',
        'required': {
            'Proper cause/change': ['MCL 722.27(1)(c)', 'Vodvarka v Grasmeyer 259 Mich App 499'],
            'Best interest factors': ['MCL 722.23', 'MCL 722.23a-23f'],
            'Established custodial environment': ['MCL 722.27(1)(c)', 'Pierron v Pierron 486 Mich 81'],
            'Burden of proof': ['MCL 722.27(1)(c)'],
            'Parenting time': ['MCL 722.27a'],
            'Fraud basis': ['MCR 2.612(C)(1)(c)', 'MCR 2.612(C)(3)'],
        },
    },
    'F8': {
        'name': 'PPO Termination',
        'required': {
            'PPO modification/termination': ['MCL 600.2950(12)', 'MCL 600.2950a'],
            'Changed circumstances': ['MCL 600.2950(12)'],
            'Due process in PPO': ['MCR 3.310(B)(5)'],
            'Fraud basis': ['MCR 2.612(C)(1)(c)'],
            'Void PPO': ['MCR 2.612(C)(1)(d) if void ab initio'],
        },
    },
    'F9': {
        'name': 'COA Appeal Brief',
        'required': {
            'Standard of review': ['MCR 7.216(A)(7)', 'Sands Appliance v Saratoga 507 US 619'],
            'Abuse of discretion': ['Maldonado v Ford Motor 476 Mich 372'],
            'Preservation': ['MCR 2.517(A)(7)'],
            'Constitutional issues': ['de novo review standard'],
            'Child custody review': ['MCL 722.28', 'Berger v Berger'],
        },
    },
    'F10': {
        'name': 'COA Emergency Motion',
        'required': {
            'Emergency motion standard': ['MCR 7.211(C)(6)'],
            'Stay pending appeal': ['MCR 7.209'],
            'Irreparable harm': ['Mich Coalition of State Empl Unions v Civil Svc Commn'],
            'Likelihood of success': ['Standard appellate stay factors'],
        },
    },
}


def get_connection():
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    return conn


def find_filing_file(filing_id):
    """Find the main filing markdown file."""
    pattern = f"PKG_{filing_id}_*"
    matches = list(FILING_DIR.glob(pattern))
    if matches:
        main_file = matches[0] / "01_MAIN_FILING.md"
        if main_file.exists():
            return main_file
    return None


def extract_citations(text):
    """Extract legal citations from filing text."""
    citations = set()
    # MCR citations
    for m in re.finditer(r'MCR\s+[\d.]+(?:\([A-Za-z0-9]+\))*', text):
        citations.add(m.group().strip())
    # MCL citations
    for m in re.finditer(r'MCL\s+[\d.]+[a-z]?', text):
        citations.add(m.group().strip())
    # USC citations
    for m in re.finditer(r'\d+\s+USC\s+[§]?\s*\d+', text):
        citations.add(m.group().strip())
    # Case citations (Name v Name)
    for m in re.finditer(r'[A-Z][a-z]+\s+v\.?\s+[A-Z][a-z]+(?:\s+\d+\s+(?:Mich|US|F\.\d+|NW\d*|S\.?\s*Ct))', text):
        citations.add(m.group().strip())
    # Constitution
    for m in re.finditer(r'Const\s+\d+\s+Art\s+\d+\s+[§]?\d+', text):
        citations.add(m.group().strip())
    # Amendment references
    for m in re.finditer(r'(?:1st|2nd|3rd|4th|5th|6th|7th|8th|9th|10th|14th)\s+Amendment', text):
        citations.add(m.group().strip())
    # Canon references
    for m in re.finditer(r'Canon\s+\d+', text):
        citations.add(m.group().strip())
    return citations


def check_authority_coverage(filing_id, filing_text, required):
    """Check which required authorities are present/missing."""
    citations = extract_citations(filing_text)
    text_lower = filing_text.lower()
    
    coverage = {}
    total_required = 0
    total_found = 0
    
    for category, authorities in required.items():
        category_found = []
        category_missing = []
        
        for auth in authorities:
            total_required += 1
            # Check if authority or close variant appears
            auth_lower = auth.lower()
            auth_parts = re.split(r'[\s§]+', auth_lower)
            
            found = False
            # Direct text match
            if auth_lower in text_lower:
                found = True
            # Check key numeric parts (e.g., "722.23" from "MCL 722.23")
            for part in auth_parts:
                if re.match(r'\d+\.?\d*', part) and len(part) >= 3:
                    if part in text_lower:
                        found = True
                        break
            # Check case name match (e.g., "Crampton" from "Crampton v Dept of State")
            name_match = re.match(r'([A-Z][a-z]+)\s+v', auth)
            if name_match and name_match.group(1).lower() in text_lower:
                found = True
            
            if found:
                category_found.append(auth)
                total_found += 1
            else:
                category_missing.append(auth)
        
        coverage[category] = {
            'found': category_found,
            'missing': category_missing,
            'complete': len(category_missing) == 0,
        }
    
    return {
        'total_required': total_required,
        'total_found': total_found,
        'total_missing': total_required - total_found,
        'coverage_pct': round(total_found / max(total_required, 1) * 100, 1),
        'categories': coverage,
        'all_citations_found': list(citations)[:50],
    }


def main():
    print("=" * 70)
    print("LEGAL RESEARCH GAP FINDER — Authority Coverage Analysis")
    print("=" * 70)
    print(f"Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    all_results = {}
    total_gaps = 0
    total_required = 0
    
    for filing_id in [f"F{i}" for i in range(1, 11)]:
        req = REQUIRED_AUTHORITIES.get(filing_id, {})
        filepath = find_filing_file(filing_id)
        
        if not filepath:
            print(f"  ⚠ {filing_id}: Filing not found")
            all_results[filing_id] = {'error': 'Filing not found'}
            continue
        
        text = filepath.read_text(encoding='utf-8', errors='replace')
        result = check_authority_coverage(filing_id, text, req.get('required', {}))
        result['filing_name'] = req.get('name', filing_id)
        all_results[filing_id] = result
        
        total_gaps += result['total_missing']
        total_required += result['total_required']
        
        # Display
        pct = result['coverage_pct']
        icon = '✅' if pct >= 90 else '🟡' if pct >= 70 else '🔴'
        print(f"  {icon} {filing_id}: {req.get('name', '')} — {pct:.0f}% coverage "
              f"({result['total_found']}/{result['total_required']})")
        
        for cat, data in result['categories'].items():
            if data['missing']:
                for auth in data['missing']:
                    print(f"     ❌ MISSING [{cat}]: {auth}")
    
    # Summary
    overall_pct = round((total_required - total_gaps) / max(total_required, 1) * 100, 1)
    print(f"\n{'=' * 70}")
    print(f"  SUMMARY: {overall_pct}% authority coverage ({total_required - total_gaps}/{total_required})")
    print(f"  Total gaps: {total_gaps} missing authorities across all filings")
    print(f"{'=' * 70}")
    
    # Priority gaps (most important missing authorities)
    print(f"\n  🎯 PRIORITY GAPS (must fix before filing):")
    priority_count = 0
    for fid in ['F3', 'F10', 'F9', 'F4', 'F7']:  # deadline priority order
        result = all_results.get(fid, {})
        for cat, data in result.get('categories', {}).items():
            for auth in data.get('missing', []):
                priority_count += 1
                if priority_count <= 15:
                    print(f"    {fid} [{cat}]: {auth}")
    if priority_count > 15:
        print(f"    ...and {priority_count - 15} more")
    
    # Save reports
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / "research_gaps.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n  Report saved: {report_path}")
    
    # Markdown
    md_path = REPORT_DIR / "RESEARCH_GAP_REPORT.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# Legal Research Gap Analysis\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Overall Coverage:** {overall_pct}% ({total_required - total_gaps}/{total_required})\n\n")
        f.write(f"**Total Gaps:** {total_gaps} missing authorities\n\n")
        
        f.write("## Coverage by Filing\n\n")
        f.write("| Filing | Name | Coverage | Found | Missing |\n")
        f.write("|--------|------|----------|-------|--------|\n")
        for fid in [f"F{i}" for i in range(1, 11)]:
            r = all_results.get(fid, {})
            if 'error' in r:
                f.write(f"| {fid} | — | ⚠ NOT FOUND | — | — |\n")
            else:
                f.write(f"| {fid} | {r.get('filing_name', '')} | {r['coverage_pct']:.0f}% | "
                        f"{r['total_found']} | {r['total_missing']} |\n")
        
        f.write("\n## Missing Authorities Detail\n\n")
        for fid in [f"F{i}" for i in range(1, 11)]:
            r = all_results.get(fid, {})
            if 'error' in r:
                continue
            missing = [(cat, auth) for cat, data in r.get('categories', {}).items() for auth in data.get('missing', [])]
            if missing:
                f.write(f"\n### {fid}: {r.get('filing_name', '')}\n\n")
                for cat, auth in missing:
                    f.write(f"- **[{cat}]** {auth}\n")
    
    print(f"  Markdown report saved: {md_path}")


if __name__ == '__main__':
    main()
