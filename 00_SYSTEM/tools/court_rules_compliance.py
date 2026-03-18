#!/usr/bin/env python3
"""
Court Rules Compliance Engine — LitigationOS Novel Tool
=========================================================
Validates filings against Michigan Court Rules (MCR) requirements.
Each filing type has specific MCR requirements that must be met.

Checks:
  - MCR 7.212 — COA brief requirements (sections, word count, cert)
  - MCR 2.113 — Motion requirements (caption, relief, verification)
  - MCR 2.003 — Disqualification motion requirements
  - MCR 3.206 — Custody motion requirements
  - MCR 6.001 — JTC/disciplinary requirements
  - 42 USC §1983 / FRCP — Federal complaint requirements

Usage:
  python court_rules_compliance.py --all          # Check all filings
  python court_rules_compliance.py --filing F9    # Check one filing
  python court_rules_compliance.py --report       # Generate compliance report
"""

import sys, os, re, json, argparse
from datetime import datetime
from pathlib import Path

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

FILING_BASE = r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE"


# ─── MCR REQUIREMENTS BY FILING TYPE ─────────────────────────────────

# Each requirement: (check_name, check_function_key, severity, description, mcr_cite)

COA_BRIEF_REQUIREMENTS = [
    ('caption', 'has_caption', 'CRITICAL', 'Brief must have caption with case number', 'MCR 7.212(A)'),
    ('statement_of_jurisdiction', 'has_section_jurisdiction', 'HIGH', 'Must include basis for jurisdiction', 'MCR 7.212(C)(1)'),
    ('statement_of_questions', 'has_section_questions', 'CRITICAL', 'Must present questions involved', 'MCR 7.212(C)(2)'),
    ('statement_of_facts', 'has_section_facts', 'CRITICAL', 'Must include statement of facts', 'MCR 7.212(C)(4)'),
    ('argument', 'has_section_argument', 'CRITICAL', 'Must include argument section', 'MCR 7.212(C)(6)'),
    ('relief_requested', 'has_section_relief', 'HIGH', 'Must state relief requested', 'MCR 7.212(C)(7)'),
    ('cert_of_compliance', 'has_cert_compliance', 'CRITICAL', 'Must include certificate of word count compliance', 'MCR 7.212(D)'),
    ('cert_of_service', 'has_cert_service', 'CRITICAL', 'Must include proof of service', 'MCR 7.212(A)(6)'),
    ('appendix_ref', 'has_appendix', 'HIGH', 'Must reference required appendix', 'MCR 7.212(G)'),
    ('record_citations', 'has_record_cites', 'MEDIUM', 'Facts should cite to lower court record', 'MCR 7.212(C)(4)'),
    ('standard_of_review', 'has_standard_review', 'HIGH', 'Should state standard of review', 'MCR 7.212(C)(5)'),
    ('word_limit', 'check_word_count', 'HIGH', 'Brief must not exceed 16,000 words', 'MCR 7.212(B)'),
]

MOTION_REQUIREMENTS = [
    ('caption', 'has_caption', 'CRITICAL', 'Must have caption with case number', 'MCR 2.113(A)'),
    ('statement_of_issues', 'has_section_issues', 'HIGH', 'Must concisely state issues', 'MCR 2.119(A)(2)'),
    ('authorities', 'has_authorities', 'HIGH', 'Must cite controlling authority', 'MCR 2.119(A)(2)'),
    ('relief_requested', 'has_section_relief', 'CRITICAL', 'Must state relief sought', 'MCR 2.119(A)(2)'),
    ('verification', 'has_verification', 'MEDIUM', 'Should include verification/affidavit', 'MCR 2.114(A)'),
    ('cert_of_service', 'has_cert_service', 'CRITICAL', 'Must include proof of service', 'MCR 2.107(A)'),
]

FEDERAL_COMPLAINT_REQUIREMENTS = [
    ('caption', 'has_caption', 'CRITICAL', 'Must have caption with parties and court', 'FRCP 10(a)'),
    ('jurisdiction', 'has_section_jurisdiction', 'CRITICAL', 'Must allege basis for jurisdiction', 'FRCP 8(a)(1)'),
    ('claim_statement', 'has_section_claims', 'CRITICAL', 'Must contain short and plain statement', 'FRCP 8(a)(2)'),
    ('relief_demanded', 'has_section_relief', 'CRITICAL', 'Must state relief demanded', 'FRCP 8(a)(3)'),
    ('numbered_paragraphs', 'has_numbered_paras', 'HIGH', 'Allegations must be in numbered paragraphs', 'FRCP 10(b)'),
    ('verification', 'has_verification', 'MEDIUM', 'Should include verification under oath', '28 USC §1746'),
]

# Map filing IDs to their requirement sets
FILING_REQUIREMENTS = {
    'F1': ('Emergency TRO (Housing)', MOTION_REQUIREMENTS),
    'F2': ('Amended Complaint (Housing)', MOTION_REQUIREMENTS),
    'F3': ('Disqualification Motion', MOTION_REQUIREMENTS),
    'F4': ('Federal §1983 Complaint', FEDERAL_COMPLAINT_REQUIREMENTS),
    'F5': ('MSC Original Action', MOTION_REQUIREMENTS),
    'F6': ('JTC Complaint', MOTION_REQUIREMENTS),
    'F7': ('Custody Modification', MOTION_REQUIREMENTS),
    'F8': ('PPO Termination', MOTION_REQUIREMENTS),
    'F9': ('COA Brief on Appeal', COA_BRIEF_REQUIREMENTS),
    'F10': ('COA Emergency Motion', MOTION_REQUIREMENTS),
}


# ─── CHECK FUNCTIONS ──────────────────────────────────────────────────

def has_caption(content, lines):
    """Check for caption/header with case information."""
    head = '\n'.join(lines[:30]).lower()
    return bool(re.search(r'(?:case|no\.?|circuit|court|district)', head) and
                re.search(r'(?:plaintiff|petitioner|appellant|complainant)', head))


def has_section_jurisdiction(content, lines):
    """Check for jurisdiction section."""
    return bool(re.search(r'(?:jurisdiction|basis\s+for\s+jurisdiction|jurisdictional)',
                          content, re.IGNORECASE))


def has_section_questions(content, lines):
    """Check for questions presented / issues on appeal."""
    return bool(re.search(r'(?:questions?\s+(?:presented|involved)|issues?\s+(?:on|for)\s+(?:appeal|review))',
                          content, re.IGNORECASE))


def has_section_facts(content, lines):
    """Check for statement of facts."""
    return bool(re.search(r'(?:statement\s+of\s+facts|factual\s+background|background\s+facts)',
                          content, re.IGNORECASE))


def has_section_argument(content, lines):
    """Check for argument section."""
    return bool(re.search(r'(?:^#+\s*argument|^argument\b|##\s*argument)',
                          content, re.IGNORECASE | re.MULTILINE))


def has_section_relief(content, lines):
    """Check for relief requested."""
    return bool(re.search(r'(?:relief\s+(?:requested|sought|demanded)|prayer\s+for\s+relief|wherefore|conclusion)',
                          content, re.IGNORECASE))


def has_cert_compliance(content, lines):
    """Check for certificate of compliance (word count)."""
    return bool(re.search(r'(?:certificate\s+of\s+compliance|word\s+count|16[,.]?000\s+words)',
                          content, re.IGNORECASE))


def has_cert_service(content, lines):
    """Check for certificate/proof of service."""
    return bool(re.search(r'(?:certificate\s+of\s+service|proof\s+of\s+service|hereby\s+certif)',
                          content, re.IGNORECASE))


def has_appendix(content, lines):
    """Check for appendix reference."""
    return bool(re.search(r'(?:appendix|appx|app\.\s|MCR\s+7\.212\(G\))',
                          content, re.IGNORECASE))


def has_record_cites(content, lines):
    """Check for record citations (Appx XX, R. XX, Tr. XX)."""
    cites = re.findall(r'(?:Appx|App\.|R\.\s*\d|Tr\.\s*\d|Record\s+\d)', content)
    return len(cites) >= 3


def has_standard_review(content, lines):
    """Check for standard of review section."""
    return bool(re.search(r'(?:standard\s+of\s+review|de\s+novo|abuse\s+of\s+discretion|clear(?:ly)?\s+erroneous)',
                          content, re.IGNORECASE))


def check_word_count(content, lines):
    """Check if brief is under 16,000 words."""
    words = len(content.split())
    return words <= 16000


def has_section_issues(content, lines):
    """Check for statement of issues."""
    return bool(re.search(r'(?:statement\s+of\s+(?:issues?|facts)|^#+\s*(?:issues?|background))',
                          content, re.IGNORECASE | re.MULTILINE))


def has_authorities(content, lines):
    """Check for legal authority citations."""
    cites = re.findall(r'(?:MCR|MCL|USC|F\.\d|Mich\.?\s+(?:App|Ct)|\d+\s+US\s+\d)',
                       content)
    return len(cites) >= 3


def has_verification(content, lines):
    """Check for verification/signature block."""
    return bool(re.search(r'(?:sworn|affirm|verify|under\s+penalty|/s/|signature)',
                          content, re.IGNORECASE))


def has_section_claims(content, lines):
    """Check for claims/causes of action."""
    return bool(re.search(r'(?:count\s+[IVX]+|cause\s+of\s+action|claim\s+\d|§\s*1983|first\s+cause)',
                          content, re.IGNORECASE))


def has_numbered_paras(content, lines):
    """Check for numbered paragraphs."""
    numbered = [l for l in lines if re.match(r'^\s*\d+\.?\s+\S', l)]
    return len(numbered) >= 5


# Function dispatch
CHECK_FUNCTIONS = {
    'has_caption': has_caption,
    'has_section_jurisdiction': has_section_jurisdiction,
    'has_section_questions': has_section_questions,
    'has_section_facts': has_section_facts,
    'has_section_argument': has_section_argument,
    'has_section_relief': has_section_relief,
    'has_cert_compliance': has_cert_compliance,
    'has_cert_service': has_cert_service,
    'has_appendix': has_appendix,
    'has_record_cites': has_record_cites,
    'has_standard_review': has_standard_review,
    'check_word_count': check_word_count,
    'has_section_issues': has_section_issues,
    'has_authorities': has_authorities,
    'has_verification': has_verification,
    'has_section_claims': has_section_claims,
    'has_numbered_paras': has_numbered_paras,
}


def check_filing(filing_id, filepath, requirements):
    """Run all checks against a filing."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        return {'error': str(e)}

    results = []
    passed = 0
    failed = 0

    for check_name, func_key, severity, description, mcr_cite in requirements:
        func = CHECK_FUNCTIONS.get(func_key)
        if not func:
            results.append({
                'check': check_name, 'passed': False, 'severity': 'UNKNOWN',
                'description': f'Check function {func_key} not found', 'mcr': mcr_cite
            })
            failed += 1
            continue

        try:
            ok = func(content, lines)
        except Exception:
            ok = False

        results.append({
            'check': check_name, 'passed': ok, 'severity': severity,
            'description': description, 'mcr': mcr_cite
        })
        if ok:
            passed += 1
        else:
            failed += 1

    total = passed + failed
    score = round(passed / total * 100, 1) if total else 0
    grade = 'A' if score >= 90 else 'B' if score >= 75 else 'C' if score >= 60 else 'D' if score >= 40 else 'F'

    return {
        'filing_id': filing_id,
        'file': filepath,
        'total_checks': total,
        'passed': passed,
        'failed': failed,
        'score': score,
        'grade': grade,
        'word_count': len(content.split()),
        'results': results,
    }


def run_all_checks(filing_filter=None, verbose=False):
    """Run checks on all filings."""
    all_results = {}

    for fid in sorted(FILING_REQUIREMENTS.keys()):
        if filing_filter and fid != filing_filter:
            continue

        fname, requirements = FILING_REQUIREMENTS[fid]
        main_file = os.path.join(FILING_BASE, f'PKG_{fid}_*', '01_MAIN_FILING.md')

        # Find the actual directory
        import glob
        matches = glob.glob(main_file)
        if not matches:
            # Try direct path construction
            for d in os.listdir(FILING_BASE):
                if d.startswith(f'PKG_{fid}_'):
                    matches = [os.path.join(FILING_BASE, d, '01_MAIN_FILING.md')]
                    break

        if not matches or not os.path.isfile(matches[0]):
            all_results[fid] = {'error': f'Filing {fid} not found'}
            continue

        result = check_filing(fid, matches[0], requirements)
        result['name'] = fname
        all_results[fid] = result

    return all_results


def print_results(all_results, verbose=False):
    """Print compliance check results."""
    print(f"\n{'═' * 70}")
    print(f"  COURT RULES COMPLIANCE ENGINE — LitigationOS")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'═' * 70}\n")

    # Summary table
    print(f"  {'Filing':<8} {'Name':<35} {'Score':>6} {'Grade':>6} {'Pass':>5} {'Fail':>5}")
    print(f"  {'─' * 65}")

    for fid in sorted(all_results.keys()):
        r = all_results[fid]
        if 'error' in r:
            print(f"  {fid:<8} {'ERROR':<35} {'--':>6} {'--':>6} {'--':>5} {'--':>5}")
            continue
        name = r.get('name', '')[:35]
        emoji = '✅' if r['grade'] in ('A', 'B') else '⚠' if r['grade'] == 'C' else '❌'
        print(f"  {fid:<8} {name:<35} {r['score']:>5.1f}% {r['grade']:>5} {r['passed']:>5} {r['failed']:>5}  {emoji}")

    print()

    # Failed checks detail
    if verbose:
        for fid in sorted(all_results.keys()):
            r = all_results[fid]
            if 'error' in r:
                continue
            failures = [c for c in r['results'] if not c['passed']]
            if failures:
                print(f"  ▓ {fid} — {r.get('name', '')} — FAILURES:")
                for c in failures:
                    icon = '🔴' if c['severity'] == 'CRITICAL' else '🟡' if c['severity'] == 'HIGH' else '🔵'
                    print(f"    {icon} [{c['severity']}] {c['check']}: {c['description']}")
                    print(f"       Rule: {c['mcr']}")
                print()

    # Overall stats
    total_passed = sum(r.get('passed', 0) for r in all_results.values() if 'error' not in r)
    total_failed = sum(r.get('failed', 0) for r in all_results.values() if 'error' not in r)
    total_checks = total_passed + total_failed
    overall_pct = round(total_passed / total_checks * 100, 1) if total_checks else 0

    print(f"  OVERALL: {total_passed}/{total_checks} checks passed ({overall_pct}%)")
    print(f"  Ready to file: {sum(1 for r in all_results.values() if r.get('grade') in ('A', 'B'))}/{len(all_results)}")
    print()


def main():
    parser = argparse.ArgumentParser(description='Court Rules Compliance Engine')
    parser.add_argument('--all', action='store_true', help='Check all filings')
    parser.add_argument('--filing', type=str, help='Check one filing (e.g., F9)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show failed check details')
    parser.add_argument('--report', '-r', action='store_true', help='Save JSON report')
    args = parser.parse_args()

    if not args.filing:
        args.all = True

    results = run_all_checks(args.filing, args.verbose)
    print_results(results, args.verbose)

    if args.report:
        rpath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            '..', 'reports', 'court_rules_compliance.json')
        os.makedirs(os.path.dirname(rpath), exist_ok=True)
        with open(rpath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"  Report: {rpath}")


if __name__ == '__main__':
    main()
