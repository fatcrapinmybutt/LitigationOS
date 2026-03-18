#!/usr/bin/env python3
"""
Exhibit Cross-Reference Engine — LitigationOS Novel Tool
==========================================================
Maps exhibit references across all 10 filings to find:
  1. Which exhibits are cited in which filings
  2. Orphan exhibits (referenced but not in exhibit index)
  3. Unused exhibits (in index but never cited in body)
  4. Cross-filing opportunities (exhibit used in F3 could strengthen F9)
  5. Citation format consistency

Exhibit conventions:
  - "Exhibit A", "Ex. A", "Exhibit 1", "Ex. 1"
  - "Attachment 1", "Att. 1"
  - Appendix references: "App. A", "Appendix A"

Usage:
  python exhibit_xref.py --all            # Full cross-reference matrix
  python exhibit_xref.py --filing F9      # Exhibits for one filing
  python exhibit_xref.py --orphans        # Find orphan/unused exhibits
  python exhibit_xref.py --opportunities  # Cross-filing opportunities
  python exhibit_xref.py --json           # JSON output
"""

import sys, os, re, json, argparse, glob
from datetime import datetime
from collections import defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')
FILING_BASE = r'C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE'

# Regex patterns for exhibit references
EXHIBIT_PATTERNS = [
    r'(?i)\b(?:Exhibit|Ex\.?)\s+([A-Z](?:\-\d+)?)',     # Exhibit A, Ex. A, Ex A-1
    r'(?i)\b(?:Exhibit|Ex\.?)\s+(\d+(?:\-[A-Z])?)',      # Exhibit 1, Ex. 1-A
    r'(?i)\b(?:Attachment|Att\.?)\s+([A-Z0-9]+)',         # Attachment 1, Att. A
    r'(?i)\b(?:Appendix|App\.?)\s+([A-Z0-9]+)',           # Appendix A, App. 1
    r'(?i)\b(?:Tab)\s+([A-Z0-9]+)',                        # Tab A, Tab 1
]


def find_all_filing_files(filing_id):
    """Find all documents in a filing package."""
    # Directories are named PKG_F3_DISQUALIFICATION_MCR_2003 etc.
    matches = glob.glob(os.path.join(FILING_BASE, f'PKG_{filing_id}_*'))
    if not matches:
        matches = glob.glob(os.path.join(FILING_BASE, f'PKG_{filing_id}'))
    files = {}
    for pkg_dir in matches:
        if os.path.isdir(pkg_dir):
            for md in glob.glob(os.path.join(pkg_dir, '*.md')):
                name = os.path.basename(md)
                files[name] = md
    return files


def extract_exhibits_from_text(text, filename=''):
    """Extract all exhibit references from text."""
    exhibits = []
    lines = text.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        for pattern in EXHIBIT_PATTERNS:
            for match in re.finditer(pattern, line):
                ref = match.group(0).strip()
                exhibit_id = match.group(1).strip().upper()
                exhibits.append({
                    'ref': ref,
                    'exhibit_id': exhibit_id,
                    'line': line_num,
                    'context': line.strip()[:120],
                    'file': filename,
                })
    
    return exhibits


def parse_exhibit_index(filepath):
    """Parse an exhibit index file to get declared exhibits."""
    declared = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        # Match patterns like "Exhibit A — Description" or "| Exhibit A | Description |"
        for match in re.finditer(r'(?i)(?:Exhibit|Ex\.?)\s+([A-Z0-9]+(?:\-\d+)?)\s*[—\-:|]+\s*(.+?)(?:\n|\|)', content):
            declared.append({
                'exhibit_id': match.group(1).strip().upper(),
                'description': match.group(2).strip()[:100],
            })
        
        # Also match numbered list items
        for match in re.finditer(r'(?i)^\s*\d+\.\s*(?:Exhibit|Ex\.?)\s+([A-Z0-9]+)\s*[—\-:]+\s*(.+)', content, re.MULTILINE):
            eid = match.group(1).strip().upper()
            if not any(d['exhibit_id'] == eid for d in declared):
                declared.append({
                    'exhibit_id': eid,
                    'description': match.group(2).strip()[:100],
                })
    except Exception:
        pass
    
    return declared


def analyze_filing(filing_id):
    """Analyze exhibit references in a filing."""
    files = find_all_filing_files(filing_id)
    if not files:
        return {'error': f'No files found for {filing_id}'}
    
    all_refs = []
    declared_exhibits = []
    
    for fname, fpath in files.items():
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception:
            continue
        
        refs = extract_exhibits_from_text(content, fname)
        all_refs.extend(refs)
        
        # Check if this is an exhibit index
        if 'EXHIBIT' in fname.upper() and 'INDEX' in fname.upper():
            declared_exhibits = parse_exhibit_index(fpath)
    
    # Deduplicate by exhibit_id
    ref_ids = set(r['exhibit_id'] for r in all_refs)
    declared_ids = set(d['exhibit_id'] for d in declared_exhibits)
    
    # Find orphans (in body but not in index) and unused (in index but not in body)
    body_refs = {r['exhibit_id'] for r in all_refs if 'EXHIBIT_INDEX' not in r['file'].upper()}
    orphans = body_refs - declared_ids if declared_ids else set()
    unused = declared_ids - body_refs if body_refs else set()
    
    return {
        'filing_id': filing_id,
        'total_references': len(all_refs),
        'unique_exhibits': len(ref_ids),
        'declared_in_index': len(declared_exhibits),
        'references': all_refs,
        'declared': declared_exhibits,
        'orphans': list(orphans),
        'unused': list(unused),
        'files_scanned': len(files),
    }


def find_cross_filing_opportunities(results):
    """Find exhibits that could be shared across filings."""
    exhibit_to_filings = defaultdict(list)
    
    for fid, data in results.items():
        if 'error' in data:
            continue
        for ref in data.get('references', []):
            ctx = ref.get('context', '').lower()
            # Extract key evidence themes
            themes = []
            if any(kw in ctx for kw in ['ex parte', 'exparte']):
                themes.append('ex_parte')
            if any(kw in ctx for kw in ['perjury', 'false', 'fabricat', 'lie']):
                themes.append('perjury')
            if any(kw in ctx for kw in ['canon', 'mcr', 'violat']):
                themes.append('judicial_violation')
            if any(kw in ctx for kw in ['custody', 'parenting', 'child']):
                themes.append('custody')
            if any(kw in ctx for kw in ['conspiracy', 'collu']):
                themes.append('conspiracy')
            
            exhibit_to_filings[ref['exhibit_id']].append({
                'filing': fid,
                'themes': themes,
                'context': ref['context'],
            })
    
    # Find exhibits in only 1 filing that match themes from other filings
    opportunities = []
    for eid, occurrences in exhibit_to_filings.items():
        filing_set = set(o['filing'] for o in occurrences)
        if len(filing_set) == 1:
            themes = set()
            for o in occurrences:
                themes.update(o['themes'])
            
            if themes:
                # Check which other filings share these themes
                for other_fid, other_data in results.items():
                    if other_fid in filing_set or 'error' in other_data:
                        continue
                    for other_ref in other_data.get('references', []):
                        other_themes = set()
                        ctx = other_ref.get('context', '').lower()
                        if any(kw in ctx for kw in ['ex parte']): other_themes.add('ex_parte')
                        if any(kw in ctx for kw in ['perjury', 'false']): other_themes.add('perjury')
                        if any(kw in ctx for kw in ['canon', 'violat']): other_themes.add('judicial_violation')
                        
                        shared = themes & other_themes
                        if shared:
                            opportunities.append({
                                'exhibit': eid,
                                'current_filing': list(filing_set)[0],
                                'could_strengthen': other_fid,
                                'shared_themes': list(shared),
                            })
                            break
    
    return opportunities


def print_dashboard(results, verbose=False):
    """Print cross-reference dashboard."""
    print(f"\n{'═' * 78}")
    print(f"  EXHIBIT CROSS-REFERENCE ENGINE — LitigationOS")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'═' * 78}\n")
    
    print(f"  {'Filing':<6} {'Refs':>5} {'Unique':>7} {'Declared':>9} {'Orphans':>8} {'Unused':>7}")
    print(f"  {'─' * 52}")
    
    total_refs = 0
    total_orphans = 0
    total_unused = 0
    
    for fid in sorted(results.keys()):
        r = results[fid]
        if 'error' in r:
            print(f"  {fid:<6} {'ERROR':>5}")
            continue
        
        refs = r.get('total_references', 0)
        unique = r.get('unique_exhibits', 0)
        decl = r.get('declared_in_index', 0)
        orph = len(r.get('orphans', []))
        unus = len(r.get('unused', []))
        total_refs += refs
        total_orphans += orph
        total_unused += unus
        
        orph_flag = '⚠' if orph > 0 else '✓'
        unus_flag = '⚠' if unus > 0 else '✓'
        
        print(f"  {fid:<6} {refs:>5} {unique:>7} {decl:>9} {orph_flag}{orph:>7} {unus_flag}{unus:>6}")
    
    print(f"  {'─' * 52}")
    print(f"  {'TOTAL':<6} {total_refs:>5} {'':>7} {'':>9} {total_orphans:>8} {total_unused:>7}")
    print(f"\n  {total_orphans} orphan exhibits (cited but not in index)")
    print(f"  {total_unused} unused exhibits (in index but never cited)")
    
    if verbose:
        for fid in sorted(results.keys()):
            r = results[fid]
            if 'error' in r or not r.get('references'):
                continue
            print(f"\n  ▓ {fid}")
            if r.get('orphans'):
                print(f"    Orphans: {', '.join(r['orphans'])}")
            if r.get('unused'):
                print(f"    Unused: {', '.join(r['unused'])}")
            
            # Show unique exhibit list
            seen = set()
            for ref in r.get('references', []):
                eid = ref['exhibit_id']
                if eid not in seen:
                    seen.add(eid)
                    print(f"    Ex {eid}: {ref['context'][:70]}")
    print()


def main():
    parser = argparse.ArgumentParser(description='Exhibit Cross-Reference Engine')
    parser.add_argument('--all', '-a', action='store_true', help='All filings')
    parser.add_argument('--filing', '-f', type=str, help='One filing')
    parser.add_argument('--orphans', '-o', action='store_true', help='Show orphans')
    parser.add_argument('--opportunities', '-p', action='store_true', help='Cross-filing opportunities')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose')
    parser.add_argument('--json', '-j', action='store_true', help='JSON output')
    args = parser.parse_args()
    
    if not args.all and not args.filing:
        args.all = True
    
    filing_ids = [f'F{i}' for i in range(1, 11)] if args.all else [args.filing.upper()]
    results = {}
    
    for fid in filing_ids:
        results[fid] = analyze_filing(fid)
    
    print_dashboard(results, args.verbose or args.orphans)
    
    if args.opportunities:
        opps = find_cross_filing_opportunities(results)
        print(f"  📌 CROSS-FILING OPPORTUNITIES ({len(opps)}):")
        for o in opps[:20]:
            print(f"    Ex {o['exhibit']}: {o['current_filing']} → {o['could_strengthen']} ({', '.join(o['shared_themes'])})")
        print()
    
    if args.json:
        os.makedirs(REPORTS_DIR, exist_ok=True)
        jpath = os.path.join(REPORTS_DIR, 'exhibit_crossref.json')
        out = {}
        for fid, r in results.items():
            out[fid] = {
                'total_references': r.get('total_references', 0),
                'unique_exhibits': r.get('unique_exhibits', 0),
                'declared_in_index': r.get('declared_in_index', 0),
                'orphans': r.get('orphans', []),
                'unused': r.get('unused', []),
            }
        opps = find_cross_filing_opportunities(results)
        with open(jpath, 'w', encoding='utf-8') as f:
            json.dump({
                'results': out,
                'opportunities': opps,
                'generated': datetime.now().isoformat(),
            }, f, indent=2)
        print(f"  📊 JSON: {jpath}")


if __name__ == '__main__':
    main()
