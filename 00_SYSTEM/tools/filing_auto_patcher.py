#!/usr/bin/env python3
"""
Filing Auto-Patcher — LitigationOS Novel Tool
===============================================
Programmatically applies known correction rules across all 10 filings.
Runs the correction rules without needing manual editing.

Correction categories:
  1. FABRICATION_REMOVAL — Remove fabricated citations (Canon 4, Wong Sun, etc.)
  2. FACT_CORRECTION — Fix incorrect facts (birth year, job count, trailer value)
  3. PARTY_IDENTITY — Fix party names/titles (Rusco→secretary, Berry→boyfriend)
  4. DATE_CORRECTION — Fix incorrect dates (SC#5/6/7 all 2025, etc.)
  5. CITATION_FIX — Replace bad citations with correct ones
  6. STAT_REMOVAL — Remove inflated/fabricated statistics

Usage:
  python filing_auto_patcher.py --scan          # Scan only (show what would change)
  python filing_auto_patcher.py --apply         # Apply all patches
  python filing_auto_patcher.py --apply --filing F9  # Apply to one filing
  python filing_auto_patcher.py --report        # Generate patch report
"""

import sys, os, re, json, argparse, shutil
from datetime import datetime
from pathlib import Path

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

FILING_BASE = r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE"


# ─── CORRECTION RULES ────────────────────────────────────────────────
# Each rule: (pattern_regex, replacement, category, description, filing_filter)

GLOBAL_RULES = [
    # FABRICATION: Canon 4 does not exist
    (r'Canon\s+4\b', None, 'FABRICATION_REMOVAL',
     'Canon 4 does not exist in MI Code of Judicial Conduct',
     None),  # Context-dependent replacement

    # FABRICATION: Wong Sun is criminal, not civil
    (r'Wong\s+Sun\s+v\.?\s+United\s+States', None, 'FABRICATION_REMOVAL',
     'Wong Sun is a criminal exclusionary rule case — not applicable to civil §1983',
     ['F4']),

    # FACT: L.D.W. birth year
    (r'\b2021\b(?=.*(?:born|birth|child|L\.?D\.?W))', '2022', 'FACT_CORRECTION',
     'L.D.W. born November 9, 2022 (NOT 2021)',
     None),

    # FACT: Job count
    (r'(?:two|2)\s+jobs?\b(?!\s+(?:at|with|for)\s+(?:Metal|IndiGrow|USPS|Shape))',
     'four jobs (Metal Arc Welding, IndiGrow Inc., USPS, Shape Corp.)',
     'FACT_CORRECTION',
     'Andrew lost 4 jobs, not 2',
     None),

    # FACT: Trailer value
    (r'\$4[,.]?200\b', '$15,000', 'FACT_CORRECTION',
     'Mobile home value is $15,000 (not $4,200)',
     ['F1']),

    # PARTY: Rusco is judicial secretary
    (r'(?:FOC|Friend\s+of\s+(?:the\s+)?Court|clerk)\s+(?:Pamela\s+)?Rusco',
     'judicial secretary Pamela Rusco', 'PARTY_IDENTITY',
     'Pamela Rusco is judicial secretary (NOT FOC, NOT clerk)',
     None),

    # PARTY: Ronald Berry is NOT an attorney
    (r'(?:Attorney|counsel|Esq\.?)\s+(?:Ronald\s+)?(?:T\.?\s+)?Berry',
     'Ronald T. Berry (Emily Watson\'s boyfriend)', 'PARTY_IDENTITY',
     'Ronald Berry is Emily\'s boyfriend, not an attorney',
     None),

    # FACT: Ex-parte count
    (r'\b(?:24|seventeen|17|15|twelve|12)\s+ex[\s-]?parte\s+(?:orders?|motions?)',
     '2 ex parte orders', 'FACT_CORRECTION',
     'Exactly 2 ex-parte orders (Andrew May 2024, Emily Aug 2025)',
     None),

    # STAT: Remove "documented pattern of parental alienation"
    (r'91%?\s+alienation\s+(?:score|index|rating)', '[parental alienation pattern documented]',
     'STAT_REMOVAL',
     'documented pattern of parental alienation was fabricated pseudo-science',
     None),

    # DATE: Show cause hearings are 2025
    (r'(?:SC\s*#?\s*[567]|show\s+cause\s+#?\s*[567]).*?2024',
     None, 'DATE_CORRECTION',
     'SC#5, SC#6, SC#7 are ALL in 2025 (not 2024)',
     None),
]


def find_filing_dirs():
    """Find all F1-F10 filing directories."""
    filings = {}
    if not os.path.isdir(FILING_BASE):
        return filings

    for d in os.listdir(FILING_BASE):
        match = re.match(r'PKG_(F\d+)', d)
        if match:
            fid = match.group(1)
            main_file = os.path.join(FILING_BASE, d, '01_MAIN_FILING.md')
            if os.path.isfile(main_file):
                filings[fid] = {
                    'dir': os.path.join(FILING_BASE, d),
                    'main': main_file,
                    'name': d,
                }
                # Also find affidavit
                aff = os.path.join(FILING_BASE, d, '02_AFFIDAVIT.md')
                if os.path.isfile(aff):
                    filings[fid]['affidavit'] = aff

    return filings


def scan_file(filepath, rules, filing_id=None):
    """Scan a file for matches against all rules."""
    matches = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        return matches

    for pattern, replacement, category, description, filing_filter in rules:
        # Skip rules that don't apply to this filing
        if filing_filter and filing_id not in filing_filter:
            continue

        for i, line in enumerate(lines, 1):
            found = re.finditer(pattern, line, re.IGNORECASE)
            for m in found:
                matches.append({
                    'file': filepath,
                    'line': i,
                    'line_text': line.strip()[:120],
                    'match': m.group(),
                    'replacement': replacement,
                    'category': category,
                    'description': description,
                    'col_start': m.start(),
                    'col_end': m.end(),
                })

    return matches


def scan_all(filings, rules, filing_filter=None):
    """Scan all filings for issues."""
    all_matches = {}
    for fid, finfo in sorted(filings.items()):
        if filing_filter and fid != filing_filter:
            continue
        matches = scan_file(finfo['main'], rules, fid)
        if finfo.get('affidavit'):
            matches += scan_file(finfo['affidavit'], rules, fid)
        if matches:
            all_matches[fid] = matches
    return all_matches


def apply_patches(filings, all_matches, dry_run=False):
    """Apply all patches to filing files."""
    applied = 0
    skipped = 0

    for fid, matches in sorted(all_matches.items()):
        # Group by file
        by_file = {}
        for m in matches:
            by_file.setdefault(m['file'], []).append(m)

        for filepath, file_matches in by_file.items():
            if not dry_run:
                # Create backup
                backup = filepath + f'.bak.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
                shutil.copy2(filepath, backup)

            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

            for m in file_matches:
                if m['replacement'] is None:
                    skipped += 1
                    continue

                # Apply replacement
                old_text = m['match']
                new_text = m['replacement']

                if old_text in content:
                    if not dry_run:
                        content = content.replace(old_text, new_text, 1)
                    applied += 1
                else:
                    skipped += 1

            if not dry_run:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

    return applied, skipped


def print_scan_results(all_matches):
    """Print scan results in a readable format."""
    total = sum(len(m) for m in all_matches.values())
    by_category = {}

    for fid, matches in sorted(all_matches.items()):
        for m in matches:
            by_category.setdefault(m['category'], []).append((fid, m))

    print(f"\n{'═' * 70}")
    print(f"  FILING AUTO-PATCHER SCAN RESULTS")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Total issues found: {total}")
    print(f"{'═' * 70}\n")

    for cat in ['FABRICATION_REMOVAL', 'FACT_CORRECTION', 'PARTY_IDENTITY',
                'DATE_CORRECTION', 'CITATION_FIX', 'STAT_REMOVAL']:
        items = by_category.get(cat, [])
        if not items:
            continue

        print(f"  ▓ {cat} ({len(items)} issues)")
        print(f"  {'─' * 66}")
        for fid, m in items:
            auto = "✅ AUTO" if m['replacement'] else "⚠ MANUAL"
            print(f"    {fid} L{m['line']:3d}: {m['match'][:50]:50s} [{auto}]")
            print(f"         → {m['description']}")
            if m['replacement']:
                print(f"         → Replace with: {m['replacement'][:60]}")
        print()

    # Summary by filing
    print(f"  {'─' * 66}")
    print(f"  By Filing:")
    for fid, matches in sorted(all_matches.items()):
        auto = sum(1 for m in matches if m['replacement'])
        manual = len(matches) - auto
        print(f"    {fid}: {len(matches)} issues ({auto} auto-fixable, {manual} need manual review)")
    print()

    auto_total = sum(1 for ms in all_matches.values() for m in ms if m['replacement'])
    manual_total = total - auto_total
    print(f"  TOTAL: {total} issues ({auto_total} auto-fixable, {manual_total} need manual review)")
    print()


def main():
    parser = argparse.ArgumentParser(description='Filing Auto-Patcher')
    parser.add_argument('--scan', action='store_true', help='Scan only (show what would change)')
    parser.add_argument('--apply', action='store_true', help='Apply all auto-fixable patches')
    parser.add_argument('--filing', type=str, help='Filter to one filing (e.g., F9)')
    parser.add_argument('--report', action='store_true', help='Generate JSON patch report')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be applied')
    args = parser.parse_args()

    if not args.scan and not args.apply and not args.report:
        args.scan = True  # Default

    filings = find_filing_dirs()
    if not filings:
        print(f"❌ No filings found at {FILING_BASE}")
        sys.exit(1)

    print(f"  Found {len(filings)} filing packages")

    all_matches = scan_all(filings, GLOBAL_RULES, args.filing)
    print_scan_results(all_matches)

    if args.apply and not args.dry_run:
        print("  Applying auto-fixable patches...")
        applied, skipped = apply_patches(filings, all_matches, dry_run=False)
        print(f"  ✅ Applied: {applied} | ⚠ Skipped (manual): {skipped}")
        print(f"  Backup files created (.bak.*)")
    elif args.apply and args.dry_run:
        applied, skipped = apply_patches(filings, all_matches, dry_run=True)
        print(f"  DRY RUN: Would apply {applied} | Would skip {skipped}")

    if args.report:
        report = {
            'generated': datetime.now().isoformat(),
            'total_issues': sum(len(m) for m in all_matches.values()),
            'by_filing': {},
        }
        for fid, matches in all_matches.items():
            report['by_filing'][fid] = [{
                'line': m['line'],
                'match': m['match'],
                'replacement': m['replacement'],
                'category': m['category'],
                'description': m['description'],
            } for m in matches]

        rpath = os.path.join(os.path.dirname(__file__), '..', 'reports', 'auto_patcher_report.json')
        os.makedirs(os.path.dirname(rpath), exist_ok=True)
        with open(rpath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        print(f"  Report: {rpath}")


if __name__ == '__main__':
    main()
