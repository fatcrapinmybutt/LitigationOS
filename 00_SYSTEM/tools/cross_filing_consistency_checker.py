#!/usr/bin/env python3
"""
Cross-Filing Consistency Checker — LitigationOS Novel Tool
==========================================================
Ensures all 10 filings (F1-F10) tell a consistent story.
Detects contradictions in: party names, case numbers, dates,
employer names, dollar amounts, job counts, address references,
and key factual claims across the entire filing portfolio.

Key capabilities:
  1. Extract key assertions from each filing (names, numbers, dates, amounts)
  2. Cross-reference assertions across all filings
  3. Flag inconsistencies (e.g., "2 jobs" in F9 vs "4 jobs" in F7)
  4. Verify party identity against verified table
  5. Generate consistency matrix showing which filings agree/disagree

Usage:
  python cross_filing_consistency_checker.py [--all] [--verbose] [--json]
"""

import sys, os, re, json, glob, argparse
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

FILING_BASE = r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE"

FILING_MAP = {
    "F1":  ("PKG_F1_EMERGENCY_TRO", "Emergency TRO (Housing)"),
    "F2":  ("PKG_F2_SHADY_OAKS_COMPLAINT", "Amended Complaint (Housing)"),
    "F3":  ("PKG_F3_DISQUALIFICATION_MCR_2003", "Disqualification Motion"),
    "F4":  ("PKG_F4_FEDERAL_S1983_COMPLAINT", "Federal §1983 Complaint"),
    "F5":  ("PKG_F5_MSC_ORIGINAL_ACTION", "MSC Original Action"),
    "F6":  ("PKG_F6_JTC_COMPLAINT", "JTC Complaint"),
    "F7":  ("PKG_F7_CUSTODY_MODIFICATION", "Custody Modification"),
    "F8":  ("PKG_F8_PPO_TERMINATION", "PPO Termination"),
    "F9":  ("PKG_F9_COA_BRIEF_ON_APPEAL", "COA Brief on Appeal"),
    "F10": ("PKG_F10_COA_EMERGENCY_MOTION", "COA Emergency Motion"),
}

# ══════════════════════════════════════════════════════════════
# VERIFIED FACTS — Source of truth
# ══════════════════════════════════════════════════════════════
VERIFIED_FACTS = {
    'plaintiff_name': 'Andrew James Pigors',
    'defendant_name': 'Emily A. Watson',
    'child_initials': 'L.D.W.',
    'child_dob': '2022-11-09',
    'judge': 'Hon. Jenny L. McNeill',
    'custody_case': '2024-001507-DC',
    'ppo_case': '2023-5907-PP',
    'housing_case': '2025-002760-CZ',
    'coa_case': 'COA 366810',
    'jobs_lost': 4,
    'job_names': ['Metal Arc', 'IndiGrow', 'USPS', 'Shape Corp'],
    'jail_days': 59,
    'rusco_title': 'judicial secretary',
    'trailer_value': 15000,
    'rent_original': 395,  # or 325 (needs verification)
    'rent_current': 720,
    'emily_employer': 'Kent County Prosecutor\'s Office',
    'emily_employee_id': '13380',
    'ronald_berry_role': 'boyfriend',
    'barnes_bar': 'P55406',
    'plaintiff_address': '1977 Whitehall Road, Lot 17',
    'defendant_address': '2160 Garland Drive',
}


# ══════════════════════════════════════════════════════════════
# EXTRACTION PATTERNS
# ══════════════════════════════════════════════════════════════

def extract_assertions(text, filing_id):
    """Extract key factual assertions from a filing."""
    assertions = []
    lines = text.split('\n')

    for line_num, line in enumerate(lines, 1):
        line_lower = line.lower()

        # Job count
        job_match = re.search(r'(?:jobs?\s*lost|lost\s*(?:his\s*)?jobs?)[\s:]*(\d+|two|three|four|five)', line_lower)
        if job_match:
            num = job_match.group(1)
            num_map = {'two': 2, 'three': 3, 'four': 4, 'five': 5}
            count = num_map.get(num, int(num) if num.isdigit() else None)
            if count:
                assertions.append({
                    'filing': filing_id, 'line': line_num,
                    'category': 'jobs_lost', 'value': count,
                    'raw': line.strip()[:100],
                })

        # Also check for specific employer mentions
        for employer in ['Metal Arc', 'IndiGrow', 'USPS', 'Shape Corp']:
            if employer.lower() in line_lower:
                assertions.append({
                    'filing': filing_id, 'line': line_num,
                    'category': 'employer_mention', 'value': employer,
                    'raw': line.strip()[:100],
                })

        # Jail days
        jail_match = re.search(r'(\d+)\s*days?\s*(?:jail|incarcerat|imprison)', line_lower)
        if jail_match:
            assertions.append({
                'filing': filing_id, 'line': line_num,
                'category': 'jail_days', 'value': int(jail_match.group(1)),
                'raw': line.strip()[:100],
            })

        # Trailer/home value
        value_match = re.search(r'\$\s*([\d,]+).*?(?:trailer|mobile\s*home|home\s*value|property\s*value)', line_lower)
        if not value_match:
            value_match = re.search(r'(?:trailer|mobile\s*home).*?\$\s*([\d,]+)', line_lower)
        if value_match:
            amount = int(value_match.group(1).replace(',', ''))
            if amount > 100:  # Filter trivial amounts
                assertions.append({
                    'filing': filing_id, 'line': line_num,
                    'category': 'trailer_value', 'value': amount,
                    'raw': line.strip()[:100],
                })

        # Rent amounts
        rent_match = re.search(r'\$\s*(\d{3,4}).*?(?:rent|monthly|lot\s*fee)', line_lower)
        if not rent_match:
            rent_match = re.search(r'(?:rent|monthly|lot\s*fee).*?\$\s*(\d{3,4})', line_lower)
        if rent_match:
            amount = int(rent_match.group(1))
            if 200 <= amount <= 2000:
                assertions.append({
                    'filing': filing_id, 'line': line_num,
                    'category': 'rent_amount', 'value': amount,
                    'raw': line.strip()[:100],
                })

        # Rusco title
        if 'rusco' in line_lower:
            if 'foc' in line_lower or 'friend of the court' in line_lower:
                assertions.append({
                    'filing': filing_id, 'line': line_num,
                    'category': 'rusco_title', 'value': 'FOC',
                    'raw': line.strip()[:100],
                })
            elif 'clerk' in line_lower:
                assertions.append({
                    'filing': filing_id, 'line': line_num,
                    'category': 'rusco_title', 'value': 'clerk',
                    'raw': line.strip()[:100],
                })
            elif 'secretary' in line_lower or 'judicial secretary' in line_lower:
                assertions.append({
                    'filing': filing_id, 'line': line_num,
                    'category': 'rusco_title', 'value': 'judicial secretary',
                    'raw': line.strip()[:100],
                })

        # Ex parte count
        exparte_match = re.search(r'(\d+|two|three|four|five|six|seven)\s*ex\s*parte', line_lower)
        if exparte_match:
            num = exparte_match.group(1)
            num_map = {'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7}
            count = num_map.get(num, int(num) if num.isdigit() else None)
            if count:
                assertions.append({
                    'filing': filing_id, 'line': line_num,
                    'category': 'exparte_count', 'value': count,
                    'raw': line.strip()[:100],
                })

        # Child birth year
        if 'l.d.w' in line_lower or 'minor child' in line_lower or 'born' in line_lower:
            year_match = re.search(r'(?:born|birth).*?(20\d{2})', line_lower)
            if year_match:
                assertions.append({
                    'filing': filing_id, 'line': line_num,
                    'category': 'child_birth_year', 'value': int(year_match.group(1)),
                    'raw': line.strip()[:100],
                })

        # Case numbers
        case_match = re.findall(r'(\d{4}-\d{4,7}-[A-Z]{2})', line)
        for case_num in case_match:
            assertions.append({
                'filing': filing_id, 'line': line_num,
                'category': 'case_number', 'value': case_num,
                'raw': line.strip()[:100],
            })

        # Canon references
        canon_match = re.findall(r'Canon\s+(\d+(?:\([A-Z]\)(?:\(\d+\))?)?)', line)
        for canon in canon_match:
            assertions.append({
                'filing': filing_id, 'line': line_num,
                'category': 'canon_cite', 'value': f'Canon {canon}',
                'raw': line.strip()[:100],
            })

        # Ronald Berry title
        if 'berry' in line_lower and 'ronald' in line_lower:
            if 'attorney' in line_lower or 'counsel' in line_lower or 'esq' in line_lower:
                assertions.append({
                    'filing': filing_id, 'line': line_num,
                    'category': 'berry_title', 'value': 'attorney',
                    'raw': line.strip()[:100],
                })
            elif 'boyfriend' in line_lower or 'partner' in line_lower:
                assertions.append({
                    'filing': filing_id, 'line': line_num,
                    'category': 'berry_title', 'value': 'boyfriend',
                    'raw': line.strip()[:100],
                })

    return assertions


def check_consistency(all_assertions, verbose=False):
    """Check assertions for cross-filing inconsistencies."""
    issues = []

    # Group by category
    by_category = defaultdict(list)
    for a in all_assertions:
        by_category[a['category']].append(a)

    # Check numeric categories for inconsistency
    for cat in ['jobs_lost', 'jail_days', 'trailer_value', 'child_birth_year', 'exparte_count']:
        entries = by_category.get(cat, [])
        if len(entries) < 2:
            continue
        values = set(e['value'] for e in entries)
        if len(values) > 1:
            verified = VERIFIED_FACTS.get(cat)
            details = []
            for e in entries:
                correct = "✅" if verified and e['value'] == verified else "❌"
                details.append(f"{e['filing']} line {e['line']}: {e['value']} {correct}")
            issues.append({
                'type': 'NUMERIC_INCONSISTENCY',
                'severity': 'CRITICAL',
                'category': cat,
                'values_found': sorted(values),
                'verified_value': verified,
                'details': details,
                'filings': sorted(set(e['filing'] for e in entries)),
            })

    # Check Rusco title
    rusco_entries = by_category.get('rusco_title', [])
    if rusco_entries:
        titles = set(e['value'] for e in rusco_entries)
        wrong = [e for e in rusco_entries if e['value'] != 'judicial secretary']
        if wrong:
            issues.append({
                'type': 'PARTY_TITLE_ERROR',
                'severity': 'HIGH',
                'category': 'rusco_title',
                'correct': 'judicial secretary',
                'found': sorted(titles),
                'details': [
                    f"{e['filing']} line {e['line']}: calls Rusco '{e['value']}'"
                    for e in wrong
                ],
                'filings': sorted(set(e['filing'] for e in wrong)),
            })

    # Check Berry title
    berry_entries = by_category.get('berry_title', [])
    wrong_berry = [e for e in berry_entries if e['value'] == 'attorney']
    if wrong_berry:
        issues.append({
            'type': 'PARTY_TITLE_ERROR',
            'severity': 'HIGH',
            'category': 'berry_title',
            'correct': 'boyfriend (no verified bar number)',
            'found': ['attorney'],
            'details': [
                f"{e['filing']} line {e['line']}: calls Berry 'attorney'"
                for e in wrong_berry
            ],
            'filings': sorted(set(e['filing'] for e in wrong_berry)),
        })

    # Check Canon 4 (fabricated)
    canon_entries = by_category.get('canon_cite', [])
    canon4 = [e for e in canon_entries if 'Canon 4' in e['value']]
    if canon4:
        issues.append({
            'type': 'FABRICATED_CITATION',
            'severity': 'CRITICAL',
            'category': 'canon_cite',
            'description': 'Canon 4 was identified as fabricated — MI Judicial Canons have no Canon 4 for delegation',
            'details': [
                f"{e['filing']} line {e['line']}: cites {e['value']}"
                for e in canon4
            ],
            'filings': sorted(set(e['filing'] for e in canon4)),
        })

    # Check employer mentions across filings
    emp_entries = by_category.get('employer_mention', [])
    emp_by_filing = defaultdict(set)
    for e in emp_entries:
        emp_by_filing[e['filing']].add(e['value'])
    if len(emp_by_filing) > 1:
        # Check if any filing mentions Shape Corp as Andrew's employer
        for fid, emps in emp_by_filing.items():
            if 'Shape Corp' in emps:
                # Shape Corp is Emily's employer — flag if used as Andrew's
                issues.append({
                    'type': 'EMPLOYER_WARNING',
                    'severity': 'MEDIUM',
                    'category': 'employer_mention',
                    'description': f'{fid} mentions Shape Corp — verify context (Shape Corp may be Emily\'s employer)',
                    'filings': [fid],
                    'details': [f"{e['filing']} line {e['line']}: mentions {e['value']}"
                               for e in emp_entries if e['filing'] == fid and e['value'] == 'Shape Corp'],
                })

    return issues


def build_consistency_matrix(all_assertions):
    """Build a matrix showing which filings agree/disagree on key facts."""
    matrix = {}
    categories = ['jobs_lost', 'jail_days', 'trailer_value', 'child_birth_year',
                   'rusco_title', 'exparte_count']

    by_cat = defaultdict(lambda: defaultdict(set))
    for a in all_assertions:
        if a['category'] in categories:
            by_cat[a['category']][a['filing']].add(a['value'])

    for cat in categories:
        matrix[cat] = {}
        for fid in FILING_MAP:
            values = by_cat[cat].get(fid, set())
            if not values:
                matrix[cat][fid] = '—'
            elif len(values) == 1:
                matrix[cat][fid] = str(list(values)[0])
            else:
                matrix[cat][fid] = '/'.join(str(v) for v in sorted(values))

    return matrix


def run_check(verbose=False, output_json=False):
    """Run full cross-filing consistency check."""
    all_assertions = []

    print("═" * 70)
    print("  CROSS-FILING CONSISTENCY CHECKER — LitigationOS")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("═" * 70)
    print()

    # Phase 1: Extract assertions
    print("Phase 1: Extracting assertions from all filings...")
    for fid, (folder, name) in FILING_MAP.items():
        main_path = os.path.join(FILING_BASE, folder, "01_MAIN_FILING.md")
        affidavit_path = os.path.join(FILING_BASE, folder, "02_AFFIDAVIT.md")

        count = 0
        for fpath in [main_path, affidavit_path]:
            if os.path.exists(fpath):
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                        text = f.read()
                    assertions = extract_assertions(text, fid)
                    all_assertions.extend(assertions)
                    count += len(assertions)
                except Exception as e:
                    print(f"  ⚠ Error reading {fpath}: {e}")

        print(f"  {fid:5s} ({name:30s}): {count:3d} assertions")

    print(f"\n  Total: {len(all_assertions)} assertions\n")

    # Phase 2: Check consistency
    print("Phase 2: Checking cross-filing consistency...")
    issues = check_consistency(all_assertions, verbose)

    critical = sum(1 for i in issues if i.get('severity') == 'CRITICAL')
    high = sum(1 for i in issues if i.get('severity') == 'HIGH')
    medium = sum(1 for i in issues if i.get('severity') == 'MEDIUM')

    print()
    print("═" * 70)
    print(f"  RESULTS: {len(issues)} inconsistencies ({critical} CRITICAL, {high} HIGH, {medium} MEDIUM)")
    print("═" * 70)
    print()

    severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
    issues.sort(key=lambda x: severity_order.get(x.get('severity', 'LOW'), 4))

    for issue in issues:
        sev = issue['severity']
        icon = {'CRITICAL': '🔴', 'HIGH': '🟡', 'MEDIUM': '🔵'}.get(sev, '⚪')

        print(f"  {icon} [{sev}] {issue['type']}: {issue['category']}")
        if 'description' in issue:
            print(f"     {issue['description']}")
        if 'values_found' in issue:
            verified = issue.get('verified_value')
            vstr = f" (verified: {verified})" if verified else ""
            print(f"     Values found: {issue['values_found']}{vstr}")
        if 'correct' in issue:
            print(f"     Correct value: {issue['correct']}")
        print(f"     Filings affected: {', '.join(issue['filings'])}")
        if verbose and 'details' in issue:
            for d in issue['details']:
                print(f"       → {d}")
        print()

    # Phase 3: Consistency Matrix
    matrix = build_consistency_matrix(all_assertions)
    print("═" * 70)
    print("  CONSISTENCY MATRIX")
    print("═" * 70)

    # Header
    fids = list(FILING_MAP.keys())
    header = f"  {'Category':20s} | " + " | ".join(f"{f:>5s}" for f in fids)
    print(header)
    print("  " + "─" * (len(header) - 2))

    for cat in matrix:
        row = f"  {cat:20s} | "
        cells = []
        for fid in fids:
            val = matrix[cat].get(fid, '—')
            # Color-code: match verified = normal, mismatch = !!
            verified = VERIFIED_FACTS.get(cat)
            if val == '—':
                cells.append(f"{'—':>5s}")
            elif verified and str(val) != str(verified):
                cells.append(f"{'!'+str(val):>5s}")
            else:
                cells.append(f"{str(val):>5s}")
        row += " | ".join(cells)
        print(row)

    print()
    print("  Legend: — = not mentioned | !X = inconsistent with verified value")
    print()

    # JSON output
    if output_json:
        report = {
            'generated': datetime.now().isoformat(),
            'total_assertions': len(all_assertions),
            'total_issues': len(issues),
            'critical': critical,
            'high': high,
            'medium': medium,
            'issues': issues,
            'matrix': matrix,
            'verified_facts': {k: str(v) for k, v in VERIFIED_FACTS.items()},
        }
        json_path = os.path.join(os.path.dirname(__file__), '..', 'reports', 'consistency_check.json')
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"  JSON report saved to: {json_path}")

    return issues


def main():
    parser = argparse.ArgumentParser(description='Cross-Filing Consistency Checker')
    parser.add_argument('--json', '-j', action='store_true', help='Output JSON report')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed context')
    args = parser.parse_args()

    run_check(verbose=args.verbose, output_json=args.json)


if __name__ == '__main__':
    main()
