#!/usr/bin/env python3
"""
Brief Word & Page Counter — LitigationOS Novel Tool
=====================================================
Enforces Michigan and Federal court page/word limits.

Rules enforced:
  MCR 7.212(B): COA briefs ≤ 50 pages (exclusive of tables/appendices)
  MCR 7.306(D): MSC applications ≤ 50 pages
  MCR 7.211(C)(2): Motions ≤ 20 pages
  FRCP 7(a): Federal complaints — no page limit but Rule 8 brevity
  MCR 2.119(A)(2): Circuit court briefs ≤ 20 pages
  MCR 7.212(B): 12pt font minimum, double-spaced body

The tool:
  1. Counts words (excluding headers, captions, certs)
  2. Estimates pages (250 words/page double-spaced, 12pt)
  3. Flags over-limit filings
  4. Checks font/spacing references in the document
  5. Reports compliance status

Usage:
  python brief_counter.py --all            # Check all filings
  python brief_counter.py --filing F9      # Check one filing
  python brief_counter.py --verbose        # Detailed word counts
  python brief_counter.py --json           # JSON output
"""

import sys, os, re, json, argparse, glob
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')
FILING_BASE = r'C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE'

# ─── COURT LIMITS ─────────────────────────────────────────────────────

COURT_LIMITS = {
    'F1':  {'type': 'motion',      'rule': 'MCR 2.119(A)(2)',   'max_pages': 20,  'max_words': 5000,  'court': '14th Circuit'},
    'F2':  {'type': 'complaint',   'rule': 'MCR 2.111',         'max_pages': None, 'max_words': None,  'court': '14th Circuit'},
    'F3':  {'type': 'motion',      'rule': 'MCR 2.003 / 2.119', 'max_pages': 20,  'max_words': 5000,  'court': '14th Circuit'},
    'F4':  {'type': 'complaint',   'rule': 'FRCP 8',            'max_pages': None, 'max_words': None,  'court': 'USDC WDMI'},
    'F5':  {'type': 'application', 'rule': 'MCR 7.306(D)',      'max_pages': 50,  'max_words': 12500, 'court': 'MSC'},
    'F6':  {'type': 'complaint',   'rule': 'MCR 9.116',         'max_pages': None, 'max_words': None,  'court': 'JTC'},
    'F7':  {'type': 'motion',      'rule': 'MCR 2.119(A)(2)',   'max_pages': 20,  'max_words': 5000,  'court': '14th Circuit'},
    'F8':  {'type': 'motion',      'rule': 'MCR 2.119(A)(2)',   'max_pages': 20,  'max_words': 5000,  'court': '14th Circuit'},
    'F9':  {'type': 'coa_brief',   'rule': 'MCR 7.212(B)',      'max_pages': 50,  'max_words': 12500, 'court': 'COA'},
    'F10': {'type': 'coa_motion',  'rule': 'MCR 7.211(C)(2)',   'max_pages': 20,  'max_words': 5000,  'court': 'COA'},
}

# Sections to EXCLUDE from word count (per MCR 7.212(B))
EXCLUDED_SECTION_PATTERNS = [
    r'(?i)^#+ .*TABLE OF CONTENTS',
    r'(?i)^#+ .*TABLE OF AUTHORITIES',
    r'(?i)^#+ .*CERTIFICATE OF SERVICE',
    r'(?i)^#+ .*CERTIFICATE OF COMPLIANCE',
    r'(?i)^#+ .*PROOF OF SERVICE',
    r'(?i)^#+ .*APPENDIX',
    r'(?i)^#+ .*EXHIBIT',
    r'(?i)^#+ .*CAPTION',
    r'(?i)^#+ .*VERIFICATION',
]


def find_filing_file(filing_id):
    """Find the main filing document for a filing ID."""
    # Directories are named PKG_F3_DISQUALIFICATION_MCR_2003 etc.
    matches = glob.glob(os.path.join(FILING_BASE, f'PKG_{filing_id}_*'))
    if not matches:
        # Fallback: try exact match
        matches = glob.glob(os.path.join(FILING_BASE, f'PKG_{filing_id}'))
    for pkg_dir in matches:
        if os.path.isdir(pkg_dir):
            main = os.path.join(pkg_dir, '01_MAIN_FILING.md')
            if os.path.isfile(main):
                return main
            mds = glob.glob(os.path.join(pkg_dir, '*.md'))
            if mds:
                return mds[0]
    return None


def count_words(filepath):
    """Count words in a filing, separating countable vs excluded sections."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception as e:
        return {'error': str(e)}
    
    lines = content.split('\n')
    total_words = 0
    countable_words = 0
    excluded_words = 0
    in_excluded_section = False
    section_counts = {}
    current_section = 'PREAMBLE'
    
    for line in lines:
        # Check for section header
        if line.strip().startswith('#'):
            current_section = re.sub(r'^#+\s*', '', line.strip())
            is_excluded = any(re.match(pat, line.strip()) for pat in EXCLUDED_SECTION_PATTERNS)
            in_excluded_section = is_excluded
        
        words = len(line.split())
        total_words += words
        
        if in_excluded_section:
            excluded_words += words
        else:
            countable_words += words
        
        section_counts[current_section] = section_counts.get(current_section, 0) + words
    
    # Estimate pages (250 words per page, double-spaced, 12pt)
    est_pages = round(countable_words / 250, 1)
    
    # Check for formatting indicators
    has_12pt = bool(re.search(r'12[- ]?p(?:oin)?t', content, re.IGNORECASE))
    has_double_space = bool(re.search(r'double[- ]?space', content, re.IGNORECASE))
    has_times_new_roman = bool(re.search(r'times\s*new\s*roman', content, re.IGNORECASE))
    
    return {
        'file': filepath,
        'total_words': total_words,
        'countable_words': countable_words,
        'excluded_words': excluded_words,
        'estimated_pages': est_pages,
        'total_lines': len(lines),
        'sections': section_counts,
        'formatting': {
            '12pt_mentioned': has_12pt,
            'double_space_mentioned': has_double_space,
            'times_new_roman': has_times_new_roman,
        },
    }


def check_compliance(filing_id, word_data):
    """Check if filing meets court limits."""
    limits = COURT_LIMITS.get(filing_id, {})
    issues = []
    status = 'COMPLIANT'
    
    if 'error' in word_data:
        return {'status': 'ERROR', 'issues': [word_data['error']]}
    
    max_pages = limits.get('max_pages')
    max_words = limits.get('max_words')
    est_pages = word_data.get('estimated_pages', 0)
    countable = word_data.get('countable_words', 0)
    
    if max_pages and est_pages > max_pages:
        issues.append(f'OVER PAGE LIMIT: ~{est_pages} pages vs {max_pages} max ({limits["rule"]})')
        status = 'OVER_LIMIT'
    elif max_pages and est_pages > max_pages * 0.9:
        issues.append(f'WARNING: ~{est_pages} pages — approaching {max_pages} limit ({limits["rule"]})')
        status = 'WARNING'
    
    if max_words and countable > max_words:
        issues.append(f'OVER WORD LIMIT: {countable:,} words vs {max_words:,} max')
        status = 'OVER_LIMIT'
    elif max_words and countable > max_words * 0.9:
        issues.append(f'WARNING: {countable:,} words — approaching {max_words:,} limit')
        if status != 'OVER_LIMIT':
            status = 'WARNING'
    
    # COA/MSC briefs need font/spacing compliance
    if limits.get('type') in ('coa_brief', 'coa_motion', 'application'):
        fmt = word_data.get('formatting', {})
        if not fmt.get('12pt_mentioned') and not fmt.get('times_new_roman'):
            issues.append('No font specification found — MCR 7.212(B) requires 12pt minimum')
    
    return {
        'status': status,
        'issues': issues,
        'rule': limits.get('rule', 'Unknown'),
        'max_pages': max_pages,
        'max_words': max_words,
        'pct_of_page_limit': round(est_pages / max_pages * 100, 1) if max_pages else None,
        'pct_of_word_limit': round(countable / max_words * 100, 1) if max_words else None,
    }


def print_results(results, verbose=False):
    """Print compliance results."""
    print(f"\n{'═' * 78}")
    print(f"  BRIEF WORD & PAGE COUNTER — LitigationOS")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'═' * 78}\n")
    
    print(f"  {'Filing':<6} {'Words':>7} {'Pages':>6} {'Limit':>6} {'Usage':>6} {'Status':<14} {'Rule'}")
    print(f"  {'─' * 76}")
    
    over = 0
    warn = 0
    ok = 0
    
    for fid in sorted(results.keys()):
        r = results[fid]
        words = r.get('word_data', {}).get('countable_words', 0)
        pages = r.get('word_data', {}).get('estimated_pages', 0)
        comp = r.get('compliance', {})
        limit = comp.get('max_pages')
        pct = comp.get('pct_of_page_limit')
        status = comp.get('status', 'UNKNOWN')
        rule = comp.get('rule', '')
        
        status_icon = '✅' if status == 'COMPLIANT' else '⚠️' if status == 'WARNING' else '❌' if status == 'OVER_LIMIT' else '—'
        limit_str = str(limit) if limit else 'None'
        pct_str = f'{pct}%' if pct else 'N/A'
        
        if status == 'OVER_LIMIT': over += 1
        elif status == 'WARNING': warn += 1
        else: ok += 1
        
        print(f"  {fid:<6} {words:>7,} {pages:>5.1f}p {limit_str:>6} {pct_str:>6} {status_icon} {status:<10} {rule}")
    
    print(f"\n  Summary: {ok} compliant, {warn} warnings, {over} over-limit")
    
    if verbose:
        print(f"\n{'─' * 78}")
        for fid in sorted(results.keys()):
            r = results[fid]
            wd = r.get('word_data', {})
            comp = r.get('compliance', {})
            
            print(f"\n  ▓ {fid}: {COURT_LIMITS.get(fid, {}).get('court', '')}")
            print(f"    Total words: {wd.get('total_words', 0):,}")
            print(f"    Countable: {wd.get('countable_words', 0):,} | Excluded: {wd.get('excluded_words', 0):,}")
            print(f"    Est. pages: {wd.get('estimated_pages', 0)} | Lines: {wd.get('total_lines', 0)}")
            
            if comp.get('issues'):
                for issue in comp['issues']:
                    print(f"    ⚠ {issue}")
            
            # Top sections by word count
            secs = wd.get('sections', {})
            top = sorted(secs.items(), key=lambda x: x[1], reverse=True)[:5]
            if top and verbose:
                print(f"    Top sections:")
                for sec, wc in top:
                    name = sec[:50]
                    print(f"      {wc:>5} words — {name}")
    print()


def main():
    parser = argparse.ArgumentParser(description='Brief Word & Page Counter')
    parser.add_argument('--all', '-a', action='store_true', help='Check all filings')
    parser.add_argument('--filing', '-f', type=str, help='Check one filing')
    parser.add_argument('--verbose', '-v', action='store_true', help='Detailed output')
    parser.add_argument('--json', '-j', action='store_true', help='JSON output')
    args = parser.parse_args()
    
    if not args.all and not args.filing:
        args.all = True
        args.verbose = True
    
    filings = list(COURT_LIMITS.keys()) if args.all else [args.filing.upper()]
    results = {}
    
    for fid in filings:
        fpath = find_filing_file(fid)
        if fpath:
            wd = count_words(fpath)
            comp = check_compliance(fid, wd)
            results[fid] = {'word_data': wd, 'compliance': comp, 'file': fpath}
        else:
            results[fid] = {'word_data': {'error': 'File not found'}, 'compliance': {'status': 'ERROR'}, 'file': None}
    
    print_results(results, args.verbose)
    
    if args.json:
        os.makedirs(REPORTS_DIR, exist_ok=True)
        jpath = os.path.join(REPORTS_DIR, 'brief_word_counts.json')
        # Remove section detail for cleaner JSON
        out = {}
        for fid, r in results.items():
            out[fid] = {
                'countable_words': r['word_data'].get('countable_words', 0),
                'estimated_pages': r['word_data'].get('estimated_pages', 0),
                'total_lines': r['word_data'].get('total_lines', 0),
                'compliance': r['compliance'],
            }
        with open(jpath, 'w', encoding='utf-8') as f:
            json.dump({'results': out, 'generated': datetime.now().isoformat()}, f, indent=2)
        print(f"  📊 JSON: {jpath}")


if __name__ == '__main__':
    main()
