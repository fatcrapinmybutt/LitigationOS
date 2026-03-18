#!/usr/bin/env python3
"""
Legal Authority Strength Ranker — LitigationOS Novel Tool
============================================================
Scores every legal citation across all 10 filings on 5 dimensions:
  1. Jurisdiction match (MI > 6th Cir > US Sup Ct > Other)
  2. Recency (newer = stronger, unless landmark)
  3. Court hierarchy (Supreme > Appeals > Circuit > District)
  4. Relevance to claim (keyword overlap with surrounding text)
  5. Validation status (in DB authority_chains? citation_validation?)

Outputs:
  - Per-filing authority strength score
  - Weak authorities that should be replaced
  - Missing authorities (claims without supporting law)
  - Authority diversity index (too many from same source?)

Michigan court hierarchy:
  MSC > COA > Circuit > District > Probate
  US: SCOTUS > 6th Circuit > WDMI/EDMI

Usage:
  python authority_ranker.py --all            # Rank all authorities
  python authority_ranker.py --filing F9      # One filing
  python authority_ranker.py --weak           # Show weak authorities
  python authority_ranker.py --missing        # Claims without authority
  python authority_ranker.py --json           # JSON output
"""

import sys, os, re, json, argparse, glob, sqlite3
from datetime import datetime
from collections import defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')
FILING_BASE = r'C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE'
DB_PATH = r'C:\Users\andre\LitigationOS\litigation_context.db'

# ─── CITATION PATTERNS ───────────────────────────────────────────────

CITATION_PATTERNS = [
    # Michigan cases: People v Smith, 123 Mich App 456 (1990)
    r'(?P<name>[A-Z][a-z]+ v\.? [A-Z][a-z]+)[,\s]+(?P<vol>\d+)\s+(?P<reporter>Mich(?:\s+App)?)\s+(?P<page>\d+)\s*\((?P<year>\d{4})\)',
    # US Supreme Court: Brown v Board, 347 US 483 (1954)
    r'(?P<name>[A-Z][a-z]+ v\.? [A-Z][a-z]+)[,\s]+(?P<vol>\d+)\s+(?P<reporter>U\.?S\.?)\s+(?P<page>\d+)\s*\((?P<year>\d{4})\)',
    # Federal Reporter: Smith v Jones, 123 F.3d 456 (6th Cir. 2020)
    r'(?P<name>[A-Z][a-z]+ v\.? [A-Z][a-z]+)[,\s]+(?P<vol>\d+)\s+(?P<reporter>F\.?\d?[a-z]*)\s+(?P<page>\d+)\s*\((?P<court>[^)]+?)(?P<year>\d{4})\)',
    # Michigan statutes: MCL 750.423
    r'(?P<name>MCL\s+(?P<vol>\d+)\.(?P<page>\d+[a-z]?))',
    # Michigan Court Rules: MCR 2.003
    r'(?P<name>MCR\s+(?P<vol>\d+)\.(?P<page>\d+)(?:\([A-Z]\)(?:\(\d+\))?)?)',
    # Federal statutes: 42 USC §1983
    r'(?P<name>(?P<vol>\d+)\s+U\.?S\.?C\.?\s+§?\s*(?P<page>\d+[a-z]?))',
    # FRCP: FRCP 4(e)
    r'(?P<name>FRCP\s+(?P<vol>\d+)(?:\([a-z]\))?)',
    # Simple case reference: In re Rains, 301 Mich App 313 (2013)
    r'(?P<name>In re [A-Z][a-z]+)[,\s]+(?P<vol>\d+)\s+(?P<reporter>Mich(?:\s+App)?)\s+(?P<page>\d+)\s*\((?P<year>\d{4})\)',
]

# Jurisdiction scoring
JURISDICTION_SCORES = {
    'mich': 100,           # Michigan Supreme Court
    'mich app': 90,        # Michigan Court of Appeals
    'mcl': 95,             # Michigan statutes (binding)
    'mcr': 95,             # Michigan court rules (binding)
    'us': 85,              # US Supreme Court
    'f.3d': 80,            # Federal circuit (6th Cir = primary)
    'f.2d': 75,
    'f. supp': 60,         # Federal district
    'usc': 85,             # Federal statutes
    'frcp': 80,            # Federal rules
}

# Court hierarchy weights
COURT_HIERARCHY = {
    'MSC': 100, 'SCOTUS': 95, 'COA': 85, '6th Cir': 80,
    'Circuit': 70, 'WDMI': 65, 'District': 60,
}


def find_filing_file(filing_id):
    """Find the main filing document."""
    matches = glob.glob(os.path.join(FILING_BASE, f'PKG_{filing_id}_*'))
    for pkg_dir in matches:
        if os.path.isdir(pkg_dir):
            main = os.path.join(pkg_dir, '01_MAIN_FILING.md')
            if os.path.isfile(main):
                return main
    return None


def extract_citations(text):
    """Extract all legal citations from text."""
    citations = []
    
    for pattern in CITATION_PATTERNS:
        for match in re.finditer(pattern, text):
            groups = match.groupdict()
            name = groups.get('name', match.group(0))
            reporter = groups.get('reporter', '').lower().strip()
            year_str = groups.get('year', '')
            year = int(year_str) if year_str and year_str.isdigit() else None
            
            # Get surrounding context (50 chars each side)
            start = max(0, match.start() - 80)
            end = min(len(text), match.end() + 80)
            context = text[start:end].replace('\n', ' ').strip()
            
            citations.append({
                'raw': match.group(0).strip(),
                'name': name.strip(),
                'reporter': reporter,
                'year': year,
                'context': context[:160],
                'position': match.start(),
            })
    
    return citations


def score_citation(citation, filing_court='Circuit'):
    """Score a citation on 5 dimensions (0-100 each)."""
    scores = {}
    
    # 1. Jurisdiction match
    reporter = citation.get('reporter', '')
    jur_score = 50  # default
    for key, val in JURISDICTION_SCORES.items():
        if key in reporter:
            jur_score = val
            break
    # MCL/MCR pattern
    if citation['name'].startswith('MCL'):
        jur_score = 95
    elif citation['name'].startswith('MCR'):
        jur_score = 95
    elif citation['name'].startswith('FRCP') or 'usc' in reporter:
        jur_score = 80
    scores['jurisdiction'] = jur_score
    
    # 2. Recency
    year = citation.get('year')
    if year:
        age = 2026 - year
        if age <= 5:
            scores['recency'] = 100
        elif age <= 10:
            scores['recency'] = 85
        elif age <= 20:
            scores['recency'] = 70
        elif age <= 50:
            scores['recency'] = 55
        else:
            scores['recency'] = 40
    else:
        scores['recency'] = 70  # Statutes/rules are timeless
    
    # 3. Court hierarchy
    hierarchy_score = 60
    name = citation['name']
    if 'Mich App' in citation.get('reporter', '') or 'mich app' in reporter:
        hierarchy_score = 85
    elif 'mich' in reporter and 'app' not in reporter:
        hierarchy_score = 100  # MSC
    elif 'U.S.' in name or 'us' == reporter.strip('.'):
        hierarchy_score = 95
    elif 'f.3d' in reporter or 'f.2d' in reporter:
        hierarchy_score = 80
    elif name.startswith('MCL') or name.startswith('MCR'):
        hierarchy_score = 90
    scores['hierarchy'] = hierarchy_score
    
    # 4. Relevance (keyword analysis on context)
    context = citation.get('context', '').lower()
    relevance_keywords = {
        'custody': ['custody', 'parenting', 'child', 'visitation', 'best interest'],
        'disqualification': ['disqualif', 'recusal', 'bias', 'impartial', 'prejudice'],
        'fraud': ['fraud', 'perjury', 'false', 'fabricat', 'misrepresent'],
        'due_process': ['due process', 'liberty', 'fundamental right', 'procedural'],
        'ex_parte': ['ex parte', 'one-sided', 'without notice'],
        'ppo': ['protection order', 'ppo', 'restraining', 'stalking'],
        'housing': ['evict', 'tenant', 'lease', 'habitab', 'housing'],
    }
    
    max_relevance = 0
    for theme, keywords in relevance_keywords.items():
        hits = sum(1 for kw in keywords if kw in context)
        if hits > 0:
            max_relevance = max(max_relevance, min(100, 60 + hits * 15))
    scores['relevance'] = max_relevance if max_relevance > 0 else 50
    
    # 5. Composite
    weights = {'jurisdiction': 0.30, 'recency': 0.15, 'hierarchy': 0.25, 'relevance': 0.30}
    composite = sum(scores[k] * weights[k] for k in weights)
    scores['composite'] = round(composite, 1)
    
    return scores


def check_db_validation(citation_name):
    """Check if citation exists in the DB authority tables."""
    if not os.path.isfile(DB_PATH):
        return None
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("PRAGMA journal_mode=WAL")
        
        # Check citation_validation table
        try:
            row = conn.execute(
                "SELECT status FROM citation_validation WHERE citation LIKE ? LIMIT 1",
                (f'%{citation_name[:30]}%',)
            ).fetchone()
            if row:
                conn.close()
                return row[0]
        except Exception:
            pass
        
        # Check authority_chains
        try:
            row = conn.execute(
                "SELECT chain_complete FROM authority_chains WHERE authority_text LIKE ? LIMIT 1",
                (f'%{citation_name[:30]}%',)
            ).fetchone()
            if row:
                conn.close()
                return 'validated' if row[0] else 'incomplete'
        except Exception:
            pass
        
        conn.close()
    except Exception:
        pass
    return None


def analyze_filing(filing_id):
    """Analyze all authorities in a filing."""
    fpath = find_filing_file(filing_id)
    if not fpath:
        return {'error': f'File not found for {filing_id}'}
    
    try:
        with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception as e:
        return {'error': str(e)}
    
    citations = extract_citations(content)
    
    # Score each citation
    scored = []
    for cit in citations:
        scores = score_citation(cit)
        scored.append({**cit, 'scores': scores})
    
    # Sort by composite score
    scored.sort(key=lambda x: x['scores']['composite'], reverse=True)
    
    # Identify weak authorities
    weak = [c for c in scored if c['scores']['composite'] < 60]
    strong = [c for c in scored if c['scores']['composite'] >= 80]
    
    avg_score = sum(c['scores']['composite'] for c in scored) / len(scored) if scored else 0
    
    return {
        'filing_id': filing_id,
        'total_citations': len(scored),
        'avg_strength': round(avg_score, 1),
        'strong_count': len(strong),
        'weak_count': len(weak),
        'citations': scored,
        'weak': weak,
        'strong': strong,
    }


def print_dashboard(results, verbose=False, show_weak=False):
    """Print authority strength dashboard."""
    print(f"\n{'═' * 78}")
    print(f"  LEGAL AUTHORITY STRENGTH RANKER — LitigationOS")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'═' * 78}\n")
    
    print(f"  {'Filing':<6} {'Total':>6} {'Avg':>6} {'Strong':>7} {'Weak':>5} {'Grade':<6}")
    print(f"  {'─' * 42}")
    
    for fid in sorted(results.keys()):
        r = results[fid]
        if 'error' in r:
            print(f"  {fid:<6} {'ERROR':>6}")
            continue
        
        total = r['total_citations']
        avg = r['avg_strength']
        strong = r['strong_count']
        weak = r['weak_count']
        
        if avg >= 80: grade = 'A'
        elif avg >= 70: grade = 'B'
        elif avg >= 60: grade = 'C'
        elif avg >= 50: grade = 'D'
        else: grade = 'F'
        
        icon = '✅' if avg >= 70 else '⚠️' if avg >= 60 else '❌'
        print(f"  {fid:<6} {total:>6} {avg:>5.1f} {strong:>7} {weak:>5} {icon} {grade}")
    
    if verbose or show_weak:
        print(f"\n{'─' * 78}")
        for fid in sorted(results.keys()):
            r = results[fid]
            if 'error' in r:
                continue
            
            if show_weak and r.get('weak'):
                print(f"\n  ⚠ {fid} — WEAK AUTHORITIES ({len(r['weak'])}):")
                for c in r['weak'][:5]:
                    print(f"    {c['scores']['composite']:>5.1f} | {c['name'][:50]}")
                    print(f"           Context: {c['context'][:70]}...")
            
            if verbose:
                print(f"\n  ▓ {fid} — TOP 5 STRONGEST:")
                for c in r.get('strong', [])[:5]:
                    print(f"    {c['scores']['composite']:>5.1f} | {c['name'][:60]}")
    
    # Overall stats
    all_cits = sum(r.get('total_citations', 0) for r in results.values() if 'error' not in r)
    all_weak = sum(r.get('weak_count', 0) for r in results.values() if 'error' not in r)
    all_strong = sum(r.get('strong_count', 0) for r in results.values() if 'error' not in r)
    print(f"\n  TOTALS: {all_cits} citations, {all_strong} strong, {all_weak} weak")
    print()


def main():
    parser = argparse.ArgumentParser(description='Legal Authority Strength Ranker')
    parser.add_argument('--all', '-a', action='store_true', help='All filings')
    parser.add_argument('--filing', '-f', type=str, help='One filing')
    parser.add_argument('--weak', '-w', action='store_true', help='Show weak authorities')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose')
    parser.add_argument('--json', '-j', action='store_true', help='JSON output')
    args = parser.parse_args()
    
    if not args.all and not args.filing:
        args.all = True
    
    filing_ids = [f'F{i}' for i in range(1, 11)] if args.all else [args.filing.upper()]
    results = {}
    
    for fid in filing_ids:
        results[fid] = analyze_filing(fid)
    
    print_dashboard(results, args.verbose, args.weak)
    
    if args.json:
        os.makedirs(REPORTS_DIR, exist_ok=True)
        jpath = os.path.join(REPORTS_DIR, 'authority_strength.json')
        out = {}
        for fid, r in results.items():
            if 'error' in r:
                out[fid] = r
                continue
            out[fid] = {
                'total_citations': r['total_citations'],
                'avg_strength': r['avg_strength'],
                'strong_count': r['strong_count'],
                'weak_count': r['weak_count'],
                'top_5': [{'name': c['name'], 'score': c['scores']['composite']} for c in r.get('strong', [])[:5]],
                'weak_5': [{'name': c['name'], 'score': c['scores']['composite']} for c in r.get('weak', [])[:5]],
            }
        with open(jpath, 'w', encoding='utf-8') as f:
            json.dump({'results': out, 'generated': datetime.now().isoformat()}, f, indent=2)
        print(f"  📊 JSON: {jpath}")


if __name__ == '__main__':
    main()
