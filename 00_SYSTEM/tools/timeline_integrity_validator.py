#!/usr/bin/env python3
"""
Timeline Integrity Validator — LitigationOS Novel Tool
======================================================
Detects impossible date sequences, cross-filing date conflicts, and
temporal anomalies across all 10 filings (F1-F10).

Key capabilities:
  1. Extract ALL dates from filings and normalize them
  2. Build a master timeline of events
  3. Detect impossible sequences (e.g., event B before event A when B depends on A)
  4. Cross-check dates across filings for conflicts (e.g., SC#5 in 2024 vs 2025)
  5. Validate against known verified timeline
  6. Generate repair recommendations

Usage:
  python timeline_integrity_validator.py [--filing F9] [--all] [--json] [--verbose]
"""

import sys, os, re, json, glob, argparse
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path

# UTF-8 stdout on Windows
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

FILING_BASE = r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE"

# ══════════════════════════════════════════════════════════════
# VERIFIED TIMELINE — Source of truth (from user + court records)
# ══════════════════════════════════════════════════════════════
VERIFIED_TIMELINE = [
    {"date": "2022-11-09", "event": "L.D.W. born", "verified": True, "source": "birth certificate"},
    {"date": "2023-12-03", "event": "PPO filed AND granted same day", "verified": True, "source": "court records"},
    {"date": "2024-04-01", "event": "Andrew filed custody case (plaintiff)", "verified": True, "source": "court filing"},
    {"date": "2024-03-26", "event": "1st withholding by Emily begins", "verified": True, "source": "court records"},
    {"date": "2024-05-05", "event": "1st withholding ends — 50/50 custody begins", "verified": True, "source": "court order"},
    {"date": "2025-02-28", "event": "Martini 'Don't Speak' email", "verified": True, "source": "email exhibit"},
    {"date": "2025-03-03", "event": "Rusco ex parte warrant email to prosecutor Hooker", "verified": True, "source": "email exhibit"},
    {"date": "2025-07-17", "event": "Trial — Mother 100% custody, Father 79 overnights", "verified": True, "source": "court order"},
    {"date": "2025-07-29", "event": "PT FULLY SUSPENDED — 2nd withholding begins", "verified": True, "source": "court order"},
    {"date": "2025-08-06", "event": "Ex parte order suspending ALL parenting time (start)", "verified": True, "source": "court order"},
    {"date": "2025-08-08", "event": "Ex parte order suspending ALL parenting time (entered)", "verified": True, "source": "court order"},
    {"date": "2025-09-04", "event": "1st HealthWest eval — CLEAN BASELINE", "verified": True, "source": "eval report"},
    {"date": "2025-09-11", "event": "2nd HealthWest eval — Rule-out Delusional Disorder (7-day flip)", "verified": True, "source": "eval report"},
    {"date": "2025-10-18", "event": "PPO guilty plea (CC 382a)", "verified": True, "source": "court records"},
    {"date": "2025-10-29", "event": "Evidentiary hearing (90 days after ex parte)", "verified": True, "source": "court records"},
    {"date": "2025-11-15", "event": "SC#5 — 14 days jail (muted 3x, Martini silent)", "verified": True, "source": "user verified 2025"},
    {"date": "2025-11-26", "event": "SC#6+7 — 45 days jail (AppClose birthday messages)", "verified": True, "source": "user verified 2025"},
]

# Known causal dependencies (event B cannot happen before event A)
CAUSAL_CHAINS = [
    ("L.D.W. born", "PPO filed"),
    ("PPO filed", "Andrew filed custody"),
    ("Andrew filed custody", "Trial"),
    ("Trial", "PT FULLY SUSPENDED"),
    ("PT FULLY SUSPENDED", "Ex parte order suspending"),
    ("Ex parte order suspending", "1st HealthWest"),
    ("1st HealthWest", "2nd HealthWest"),
    ("2nd HealthWest", "PPO guilty plea"),
    ("PPO guilty plea", "Evidentiary hearing"),
    ("SC#5", "SC#6"),
    ("Martini", "Rusco ex parte"),
    ("50/50 custody begins", "Trial"),
]

# Date extraction patterns
DATE_PATTERNS = [
    # ISO-like: 2025-11-15
    (r'\b(20[12]\d)[-/](0?[1-9]|1[0-2])[-/](0?[1-9]|[12]\d|3[01])\b', 'ymd'),
    # US format: November 15, 2025 / Nov 15, 2025
    (r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(20[12]\d)\b', 'mdy_long'),
    (r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+(\d{1,2}),?\s+(20[12]\d)\b', 'mdy_short'),
    # MM/DD/YYYY
    (r'\b(0?[1-9]|1[0-2])/(0?[1-9]|[12]\d|3[01])/(20[12]\d)\b', 'mdy_slash'),
]

MONTH_MAP = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
    'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
}

FILING_MAP = {
    "F1":  "PKG_F1_EMERGENCY_TRO",
    "F2":  "PKG_F2_SHADY_OAKS_COMPLAINT",
    "F3":  "PKG_F3_DISQUALIFICATION_MCR_2003",
    "F4":  "PKG_F4_FEDERAL_S1983_COMPLAINT",
    "F5":  "PKG_F5_MSC_ORIGINAL_ACTION",
    "F6":  "PKG_F6_JTC_COMPLAINT",
    "F7":  "PKG_F7_CUSTODY_MODIFICATION",
    "F8":  "PKG_F8_PPO_TERMINATION",
    "F9":  "PKG_F9_COA_BRIEF_ON_APPEAL",
    "F10": "PKG_F10_COA_EMERGENCY_MOTION",
}


def extract_dates(text, filing_id):
    """Extract all dates from filing text with line numbers and context."""
    results = []
    lines = text.split('\n')
    for line_num, line in enumerate(lines, 1):
        for pattern, fmt in DATE_PATTERNS:
            for match in re.finditer(pattern, line, re.IGNORECASE):
                try:
                    if fmt == 'ymd':
                        dt = datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
                    elif fmt == 'mdy_long' or fmt == 'mdy_short':
                        month = MONTH_MAP.get(match.group(1).lower(), 0)
                        if month:
                            dt = datetime(int(match.group(3)), month, int(match.group(2)))
                        else:
                            continue
                    elif fmt == 'mdy_slash':
                        dt = datetime(int(match.group(3)), int(match.group(1)), int(match.group(2)))
                    else:
                        continue

                    # Get surrounding context (30 chars each side)
                    start = max(0, match.start() - 40)
                    end = min(len(line), match.end() + 40)
                    context = line[start:end].strip()

                    results.append({
                        'filing': filing_id,
                        'line': line_num,
                        'date': dt.strftime('%Y-%m-%d'),
                        'date_obj': dt,
                        'raw': match.group(0),
                        'context': context,
                    })
                except (ValueError, IndexError):
                    continue
    return results


def find_event_match(context, date_str):
    """Try to match a date+context to a known verified event."""
    context_lower = context.lower()
    for evt in VERIFIED_TIMELINE:
        # Check if the event keywords appear near this date
        keywords = evt['event'].lower().split()
        # Need at least 2 keyword matches
        matches = sum(1 for kw in keywords if len(kw) > 3 and kw in context_lower)
        if matches >= 2:
            return evt
        # Special cases
        if 'healthwest' in context_lower and 'healthwest' in evt['event'].lower():
            return evt
        if 'show cause' in context_lower and 'SC#' in evt['event']:
            return evt
        if 'sc#5' in context_lower and 'SC#5' in evt['event']:
            return evt
        if 'sc#6' in context_lower and 'SC#6' in evt['event']:
            return evt
    return None


def check_causal_violations(all_dates):
    """Check if any dates violate causal ordering."""
    violations = []
    # Build event-to-date mapping from all filings
    event_dates = defaultdict(list)
    for d in all_dates:
        ctx = d['context'].lower()
        for evt in VERIFIED_TIMELINE:
            keywords = evt['event'].lower().split()
            if sum(1 for kw in keywords if len(kw) > 3 and kw in ctx) >= 2:
                event_dates[evt['event']].append(d)

    for before_key, after_key in CAUSAL_CHAINS:
        before_events = [e for ename, dates in event_dates.items()
                        for e in dates if before_key.lower() in ename.lower()]
        after_events = [e for ename, dates in event_dates.items()
                       for e in dates if after_key.lower() in ename.lower()]

        for be in before_events:
            for ae in after_events:
                if ae['date_obj'] < be['date_obj']:
                    violations.append({
                        'type': 'CAUSAL_VIOLATION',
                        'severity': 'CRITICAL',
                        'description': f"'{after_key}' dated {ae['date']} occurs BEFORE '{before_key}' dated {be['date']}",
                        'filing_a': be['filing'],
                        'line_a': be['line'],
                        'filing_b': ae['filing'],
                        'line_b': ae['line'],
                    })
    return violations


def check_cross_filing_conflicts(all_dates):
    """Find dates that reference the same event but with different dates across filings."""
    conflicts = []
    # Group by approximate event (using context similarity)
    event_groups = defaultdict(list)

    # Key event patterns to match across filings
    event_signatures = [
        ('SC#5', r'(?:sc\s*#?\s*5|show\s*cause\s*#?\s*5|14\s*days?\s*jail)', 'Show Cause #5'),
        ('SC#6', r'(?:sc\s*#?\s*6|show\s*cause\s*#?\s*6|45\s*days?\s*jail)', 'Show Cause #6/7'),
        ('trial', r'(?:trial|bench\s*trial|custody\s*trial)', 'Custody Trial'),
        ('exparte', r'(?:ex\s*parte|suspend.*parenting)', 'Ex Parte Order'),
        ('healthwest1', r'(?:first.*healthwest|healthwest.*first|clean\s*baseline|september\s*4)', 'HealthWest Eval #1'),
        ('healthwest2', r'(?:second.*healthwest|healthwest.*second|delusional|september\s*11|gansen)', 'HealthWest Eval #2'),
        ('ppo_filed', r'(?:ppo\s*filed|ppo\s*granted|protection\s*order\s*filed)', 'PPO Filed'),
        ('guilty_plea', r'(?:guilty\s*plea|cc\s*382|plea\s*hearing)', 'Guilty Plea'),
        ('rusco_email', r'(?:rusco.*email|warrant.*email|march\s*3)', 'Rusco Email'),
        ('martini', r'(?:martini.*don.t\s*speak|don.t\s*speak)', 'Martini Email'),
        ('born', r'(?:l\.?d\.?w\.?\s*born|child.*born|november\s*9.*2022)', 'Child Born'),
        ('jobs_lost', r'(?:jobs?\s*lost|lost.*jobs?|employment.*lost)', 'Jobs Lost'),
    ]

    for d in all_dates:
        ctx = d['context'].lower()
        for sig_id, pattern, sig_name in event_signatures:
            if re.search(pattern, ctx, re.IGNORECASE):
                event_groups[sig_id].append({**d, 'sig_name': sig_name})

    # Check each event group for date conflicts
    for sig_id, entries in event_groups.items():
        if len(entries) < 2:
            continue
        dates_seen = set(e['date'] for e in entries)
        if len(dates_seen) > 1:
            filings_involved = set(e['filing'] for e in entries)
            date_list = sorted(dates_seen)
            conflicts.append({
                'type': 'CROSS_FILING_CONFLICT',
                'severity': 'CRITICAL',
                'event': entries[0].get('sig_name', sig_id),
                'dates_found': date_list,
                'filings': sorted(filings_involved),
                'details': [
                    f"{e['filing']} line {e['line']}: {e['date']} — \"{e['context'][:60]}...\""
                    for e in sorted(entries, key=lambda x: x['filing'])
                ],
            })

    return conflicts


def check_verified_timeline(all_dates):
    """Check filing dates against verified timeline for mismatches."""
    mismatches = []
    for d in all_dates:
        matched_event = find_event_match(d['context'], d['date'])
        if matched_event and matched_event['date'] != d['date']:
            mismatches.append({
                'type': 'VERIFIED_MISMATCH',
                'severity': 'HIGH',
                'filing': d['filing'],
                'line': d['line'],
                'event': matched_event['event'],
                'filing_date': d['date'],
                'verified_date': matched_event['date'],
                'context': d['context'],
            })
    return mismatches


def check_future_dates(all_dates):
    """Flag dates that are in the future (possible typos)."""
    today = datetime.now()
    future = []
    for d in all_dates:
        if d['date_obj'] > today + timedelta(days=365):
            future.append({
                'type': 'FUTURE_DATE',
                'severity': 'MEDIUM',
                'filing': d['filing'],
                'line': d['line'],
                'date': d['date'],
                'context': d['context'],
            })
    return future


def check_suspicious_gaps(all_dates):
    """Detect suspicious timeline gaps (e.g., year off by 1)."""
    suspicious = []
    for d in all_dates:
        for evt in VERIFIED_TIMELINE:
            # Same month/day but different year — likely typo
            try:
                evt_dt = datetime.strptime(evt['date'], '%Y-%m-%d')
                if (d['date_obj'].month == evt_dt.month and
                    d['date_obj'].day == evt_dt.day and
                    abs(d['date_obj'].year - evt_dt.year) == 1):
                    # Check context similarity
                    ctx_lower = d['context'].lower()
                    evt_lower = evt['event'].lower()
                    keywords = [w for w in evt_lower.split() if len(w) > 3]
                    if sum(1 for kw in keywords if kw in ctx_lower) >= 1:
                        suspicious.append({
                            'type': 'YEAR_OFF_BY_ONE',
                            'severity': 'HIGH',
                            'filing': d['filing'],
                            'line': d['line'],
                            'date_in_filing': d['date'],
                            'likely_correct': evt['date'],
                            'event': evt['event'],
                            'context': d['context'],
                        })
            except ValueError:
                continue
    return suspicious


def run_validation(filing_ids=None, verbose=False, output_json=False):
    """Run full timeline validation across specified filings."""
    if filing_ids is None:
        filing_ids = list(FILING_MAP.keys())

    all_dates = []
    filing_stats = {}

    print("═" * 70)
    print("  TIMELINE INTEGRITY VALIDATOR — LitigationOS")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("═" * 70)
    print()

    # Phase 1: Extract dates from all filings
    print("Phase 1: Extracting dates from filings...")
    for fid in filing_ids:
        folder = FILING_MAP.get(fid)
        if not folder:
            print(f"  ⚠ Unknown filing: {fid}")
            continue
        main_path = os.path.join(FILING_BASE, folder, "01_MAIN_FILING.md")
        affidavit_path = os.path.join(FILING_BASE, folder, "02_AFFIDAVIT.md")

        dates = []
        for fpath in [main_path, affidavit_path]:
            if os.path.exists(fpath):
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                        text = f.read()
                    dates.extend(extract_dates(text, fid))
                except Exception as e:
                    print(f"  ⚠ Error reading {fpath}: {e}")

        filing_stats[fid] = len(dates)
        all_dates.extend(dates)
        print(f"  {fid}: {len(dates)} dates extracted")

    print(f"\n  Total: {len(all_dates)} dates across {len(filing_ids)} filings\n")

    # Phase 2: Run all checks
    print("Phase 2: Running integrity checks...")
    all_issues = []

    # Check 1: Cross-filing conflicts
    conflicts = check_cross_filing_conflicts(all_dates)
    all_issues.extend(conflicts)
    print(f"  Cross-filing conflicts: {len(conflicts)}")

    # Check 2: Verified timeline mismatches
    mismatches = check_verified_timeline(all_dates)
    all_issues.extend(mismatches)
    print(f"  Verified timeline mismatches: {len(mismatches)}")

    # Check 3: Causal violations
    causal = check_causal_violations(all_dates)
    all_issues.extend(causal)
    print(f"  Causal ordering violations: {len(causal)}")

    # Check 4: Year-off-by-one
    year_off = check_suspicious_gaps(all_dates)
    all_issues.extend(year_off)
    print(f"  Year-off-by-one suspects: {len(year_off)}")

    # Check 5: Future dates
    future = check_future_dates(all_dates)
    all_issues.extend(future)
    print(f"  Future date anomalies: {len(future)}")

    total_issues = len(all_issues)
    critical = sum(1 for i in all_issues if i.get('severity') == 'CRITICAL')
    high = sum(1 for i in all_issues if i.get('severity') == 'HIGH')

    # Phase 3: Report
    print()
    print("═" * 70)
    print(f"  RESULTS: {total_issues} issues ({critical} CRITICAL, {high} HIGH)")
    print("═" * 70)
    print()

    if not all_issues:
        print("  ✅ No timeline integrity issues detected!")
    else:
        # Sort by severity
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        all_issues.sort(key=lambda x: severity_order.get(x.get('severity', 'LOW'), 4))

        for issue in all_issues:
            sev = issue.get('severity', 'UNKNOWN')
            itype = issue.get('type', 'UNKNOWN')

            if sev == 'CRITICAL':
                icon = "🔴"
            elif sev == 'HIGH':
                icon = "🟡"
            else:
                icon = "🔵"

            print(f"  {icon} [{sev}] {itype}")

            if itype == 'CROSS_FILING_CONFLICT':
                print(f"     Event: {issue['event']}")
                print(f"     Dates found: {', '.join(issue['dates_found'])}")
                print(f"     Filings: {', '.join(issue['filings'])}")
                if verbose:
                    for detail in issue['details']:
                        print(f"       → {detail}")

            elif itype == 'VERIFIED_MISMATCH':
                print(f"     {issue['filing']} line {issue['line']}: {issue['event']}")
                print(f"     Filing says: {issue['filing_date']} | Verified: {issue['verified_date']}")
                if verbose:
                    print(f"     Context: \"{issue['context'][:80]}...\"")

            elif itype == 'CAUSAL_VIOLATION':
                print(f"     {issue['description']}")
                print(f"     {issue['filing_a']} line {issue['line_a']} vs {issue['filing_b']} line {issue['line_b']}")

            elif itype == 'YEAR_OFF_BY_ONE':
                print(f"     {issue['filing']} line {issue['line']}: {issue['date_in_filing']}")
                print(f"     Likely correct: {issue['likely_correct']} ({issue['event']})")
                if verbose:
                    print(f"     Context: \"{issue['context'][:80]}...\"")

            elif itype == 'FUTURE_DATE':
                print(f"     {issue['filing']} line {issue['line']}: {issue['date']}")
                if verbose:
                    print(f"     Context: \"{issue['context'][:80]}...\"")

            print()

    # Summary table
    print("═" * 70)
    print("  DATE EXTRACTION SUMMARY")
    print("═" * 70)
    for fid in filing_ids:
        count = filing_stats.get(fid, 0)
        issues_for = sum(1 for i in all_issues
                        if i.get('filing') == fid or fid in i.get('filings', []))
        status = "✅" if issues_for == 0 else f"⚠ {issues_for} issues"
        print(f"  {fid:5s}: {count:3d} dates | {status}")
    print()

    # JSON output
    if output_json:
        report = {
            'generated': datetime.now().isoformat(),
            'total_dates': len(all_dates),
            'total_issues': total_issues,
            'critical': critical,
            'high': high,
            'filing_stats': filing_stats,
            'issues': [{k: v for k, v in i.items() if k != 'date_obj'} for i in all_issues],
            'verified_timeline': VERIFIED_TIMELINE,
        }
        json_path = os.path.join(os.path.dirname(__file__), '..', 'reports', 'timeline_validation.json')
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"  JSON report saved to: {json_path}")

    return all_issues


def main():
    parser = argparse.ArgumentParser(description='Timeline Integrity Validator')
    parser.add_argument('--filing', '-f', help='Specific filing (e.g., F9)')
    parser.add_argument('--all', '-a', action='store_true', help='Validate all filings')
    parser.add_argument('--json', '-j', action='store_true', help='Output JSON report')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed context')
    args = parser.parse_args()

    if args.filing:
        filings = [args.filing.upper()]
    elif args.all:
        filings = None  # All
    else:
        filings = None  # Default: all

    run_validation(filing_ids=filings, verbose=args.verbose, output_json=args.json)


if __name__ == '__main__':
    main()
