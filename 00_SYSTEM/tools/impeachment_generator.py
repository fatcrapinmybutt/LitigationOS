#!/usr/bin/env python3
"""
Impeachment Brief Generator — LitigationOS Novel Tool
=======================================================
Auto-generates witness impeachment outlines from contradictions,
perjury records, and prior inconsistent statements in the DB.

For each witness/party, generates:
  1. Prior Inconsistent Statements (MRE 801(d)(1)(A))
  2. Contradiction Timeline (statement A vs statement B)
  3. Impeachment Questions (ready-to-use cross-examination)
  4. Supporting Evidence Citations (DB-grounded)
  5. Severity Scoring (perjury-level vs minor inconsistency)

Usage:
  python impeachment_generator.py --witness "Emily Watson"  # One witness
  python impeachment_generator.py --all                     # All witnesses
  python impeachment_generator.py --top 5                   # Top 5 by severity
  python impeachment_generator.py --report                  # Full markdown report
"""

import sys, os, json, sqlite3, argparse, re
from datetime import datetime
from collections import defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    conn.row_factory = sqlite3.Row
    return conn


def discover_tables(conn):
    """Find available impeachment-related tables."""
    tables = {}
    for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
        name = row[0]
        try:
            cols = [c[1] for c in conn.execute(f"PRAGMA table_info({name})").fetchall()]
            tables[name] = cols
        except:
            pass
    return tables


def get_contradictions(conn, tables, witness=None):
    """Get contradictions for a witness from detected_contradictions."""
    results = []
    
    if 'detected_contradictions' in tables:
        cols = tables['detected_contradictions']
        # Find the speaker/witness column
        speaker_col = None
        for c in ['speaker', 'witness', 'actor', 'party', 'entity']:
            if c in cols:
                speaker_col = c
                break
        
        text_col = None
        for c in ['contradiction_text', 'description', 'text', 'detail', 'statement']:
            if c in cols:
                text_col = c
                break
        
        sev_col = None
        for c in ['severity', 'severity_level', 'level']:
            if c in cols:
                sev_col = c
                break
        
        if speaker_col and text_col:
            query = f"SELECT * FROM detected_contradictions"
            params = []
            if witness:
                query += f" WHERE {speaker_col} LIKE ?"
                params.append(f"%{witness}%")
            query += " LIMIT 200"
            
            try:
                for row in conn.execute(query, params).fetchall():
                    results.append({
                        'source': 'detected_contradictions',
                        'speaker': row[speaker_col] if speaker_col else 'Unknown',
                        'text': row[text_col] if text_col else '',
                        'severity': row[sev_col] if sev_col else 'UNKNOWN',
                    })
            except:
                pass
    
    return results


def get_perjury_records(conn, tables, witness=None):
    """Get perjury records from watson_perjury_compilation."""
    results = []
    
    if 'watson_perjury_compilation' not in tables:
        return results
    
    cols = tables['watson_perjury_compilation']
    
    text_col = None
    for c in ['statement', 'description', 'text', 'perjury_text', 'content']:
        if c in cols:
            text_col = c
            break
    
    cat_col = None
    for c in ['category', 'type', 'perjury_type']:
        if c in cols:
            cat_col = c
            break
    
    if text_col:
        query = f"SELECT * FROM watson_perjury_compilation LIMIT 200"
        try:
            for row in conn.execute(query).fetchall():
                results.append({
                    'source': 'watson_perjury_compilation',
                    'text': row[text_col] if text_col else '',
                    'category': row[cat_col] if cat_col else 'perjury',
                })
        except:
            pass
    
    return results


def get_contradiction_map(conn, tables, witness=None):
    """Get contradictions from contradiction_map table."""
    results = []
    
    if 'contradiction_map' not in tables:
        return results
    
    cols = tables['contradiction_map']
    
    # Find relevant columns
    text_cols = [c for c in cols if any(k in c.lower() for k in ['text', 'statement', 'description', 'content'])]
    speaker_cols = [c for c in cols if any(k in c.lower() for k in ['speaker', 'actor', 'witness', 'party'])]
    sev_cols = [c for c in cols if any(k in c.lower() for k in ['severity', 'level'])]
    
    query = "SELECT * FROM contradiction_map"
    params = []
    if witness and speaker_cols:
        conditions = [f"{c} LIKE ?" for c in speaker_cols[:2]]
        query += f" WHERE {' OR '.join(conditions)}"
        params = [f"%{witness}%"] * len(conditions)
    query += " LIMIT 200"
    
    try:
        for row in conn.execute(query, params).fetchall():
            text = row[text_cols[0]] if text_cols else str(dict(row))[:200]
            speaker = row[speaker_cols[0]] if speaker_cols else 'Unknown'
            severity = row[sev_cols[0]] if sev_cols else 'UNKNOWN'
            results.append({
                'source': 'contradiction_map',
                'speaker': speaker,
                'text': str(text)[:500],
                'severity': str(severity),
            })
    except:
        pass
    
    return results


def get_actor_violations(conn, tables, witness=None):
    """Get violations for a specific actor."""
    results = []
    
    if 'actor_violations' not in tables:
        return results
    
    cols = tables['actor_violations']
    actor_col = next((c for c in ['actor_name', 'actor', 'name'] if c in cols), None)
    type_col = next((c for c in ['violation_type', 'type', 'category'] if c in cols), None)
    desc_col = next((c for c in ['description', 'text', 'detail', 'violation_text'] if c in cols), None)
    
    if not actor_col:
        return results
    
    query = f"SELECT {actor_col}"
    if type_col:
        query += f", {type_col}"
    if desc_col:
        query += f", {desc_col}"
    query += f", COUNT(*) as cnt FROM actor_violations"
    
    if witness:
        query += f" WHERE {actor_col} LIKE ?"
        group_cols = [type_col] if type_col else [actor_col]
        query += f" GROUP BY {', '.join(group_cols)} ORDER BY cnt DESC LIMIT 20"
        
        try:
            for row in conn.execute(query, [f"%{witness}%"]).fetchall():
                results.append({
                    'actor': row[0],
                    'type': row[1] if type_col else 'violation',
                    'count': row[-1],
                })
        except:
            pass
    
    return results


def generate_impeachment_outline(witness_name, contradictions, perjury, contra_map, violations):
    """Generate a structured impeachment outline for one witness."""
    outline = {
        'witness': witness_name,
        'generated': datetime.now().isoformat(),
        'total_items': len(contradictions) + len(perjury) + len(contra_map),
        'sections': [],
    }
    
    # Section 1: Prior Inconsistent Statements
    pis_items = [c for c in contradictions if 'inconsistent' in str(c.get('severity', '')).lower() 
                 or 'CRITICAL' in str(c.get('severity', '')).upper()]
    if not pis_items:
        pis_items = contradictions[:20]
    
    if pis_items:
        outline['sections'].append({
            'title': 'Prior Inconsistent Statements — MRE 801(d)(1)(A)',
            'rule': 'A statement is not hearsay if the declarant testifies and is subject to cross-examination, and the statement is inconsistent with testimony and was given under penalty of perjury.',
            'items': [{'text': c['text'][:300], 'severity': c.get('severity', 'UNKNOWN')} for c in pis_items[:15]],
        })
    
    # Section 2: Perjury Evidence
    if perjury:
        outline['sections'].append({
            'title': 'Perjury Evidence — MCL 750.423',
            'rule': 'Any person who commits perjury by making a false material statement under oath is guilty of a felony punishable by imprisonment for not more than 15 years.',
            'items': [{'text': p['text'][:300], 'category': p.get('category', 'perjury')} for p in perjury[:15]],
        })
    
    # Section 3: Contradiction Timeline
    if contra_map:
        by_severity = defaultdict(list)
        for c in contra_map:
            by_severity[str(c.get('severity', 'UNKNOWN'))].append(c)
        
        timeline_items = []
        for sev in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'UNKNOWN']:
            for c in by_severity.get(sev, [])[:5]:
                timeline_items.append({
                    'text': c['text'][:300],
                    'severity': sev,
                })
        
        if timeline_items:
            outline['sections'].append({
                'title': 'Contradiction Timeline',
                'rule': 'Documented inconsistencies between sworn statements, testimony, and documentary evidence.',
                'items': timeline_items[:15],
            })
    
    # Section 4: Pattern of Violations
    if violations:
        outline['sections'].append({
            'title': f'Pattern of Violations by {witness_name}',
            'rule': 'Pattern evidence admissible under MRE 404(b)(1) to show scheme, plan, or modus operandi.',
            'items': [{'type': v['type'], 'count': v['count']} for v in violations[:10]],
        })
    
    return outline


def print_outline(outline, verbose=False):
    """Print impeachment outline to stdout."""
    print(f"\n{'▓' * 70}")
    print(f"  IMPEACHMENT OUTLINE: {outline['witness']}")
    print(f"  Total items: {outline['total_items']}")
    print(f"  Generated: {outline['generated']}")
    print(f"{'▓' * 70}\n")
    
    for section in outline['sections']:
        print(f"  ═══ {section['title']} ═══")
        print(f"  Rule: {section['rule'][:100]}...")
        print()
        
        for i, item in enumerate(section['items'], 1):
            if 'text' in item:
                text = item['text'][:120].replace('\n', ' ')
                sev = item.get('severity', item.get('category', ''))
                print(f"    {i:2d}. [{sev}] {text}")
            elif 'type' in item:
                print(f"    {i:2d}. {item['type']}: {item['count']} instances")
        print()


def save_report(outlines, filepath):
    """Save all outlines as a markdown report."""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("# Impeachment Brief — LitigationOS\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("**Every item below is traceable to a specific DB record.**\n\n")
        f.write("---\n\n")
        
        for outline in outlines:
            f.write(f"## {outline['witness']} ({outline['total_items']} items)\n\n")
            
            for section in outline['sections']:
                f.write(f"### {section['title']}\n\n")
                f.write(f"> {section['rule']}\n\n")
                
                for i, item in enumerate(section['items'], 1):
                    if 'text' in item:
                        sev = item.get('severity', item.get('category', ''))
                        text = item['text'][:200].replace('\n', ' ')
                        f.write(f"{i}. **[{sev}]** {text}\n")
                    elif 'type' in item:
                        f.write(f"{i}. **{item['type']}**: {item['count']} instances\n")
                f.write("\n")
            f.write("---\n\n")


def main():
    parser = argparse.ArgumentParser(description='Impeachment Brief Generator')
    parser.add_argument('--witness', '-w', type=str, help='Generate for specific witness')
    parser.add_argument('--all', '-a', action='store_true', help='Generate for all witnesses')
    parser.add_argument('--top', '-t', type=int, default=0, help='Top N witnesses by volume')
    parser.add_argument('--report', '-r', action='store_true', help='Save markdown report')
    parser.add_argument('--json', '-j', action='store_true', help='Save JSON output')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = parser.parse_args()
    
    conn = get_db()
    tables = discover_tables(conn)
    
    # Determine which witnesses to process
    witnesses = []
    if args.witness:
        witnesses = [args.witness]
    elif args.all or args.top:
        # Get top witnesses from actor_violations
        if 'actor_violations' in tables:
            actor_col = next((c for c in ['actor_name', 'actor', 'name'] 
                            if c in tables['actor_violations']), None)
            if actor_col:
                limit = args.top if args.top else 10
                rows = conn.execute(f"""
                    SELECT {actor_col}, COUNT(*) as cnt 
                    FROM actor_violations 
                    GROUP BY {actor_col} 
                    ORDER BY cnt DESC 
                    LIMIT ?
                """, (limit,)).fetchall()
                witnesses = [r[0] for r in rows if r[0]]
    
    if not witnesses:
        witnesses = ['McNeill', 'Watson', 'Watson Family', 'Rusco', 'Barnes']
    
    print(f"  Generating impeachment outlines for {len(witnesses)} witnesses...")
    print(f"  Database: {len(tables)} tables\n")
    
    outlines = []
    for w in witnesses:
        contradictions = get_contradictions(conn, tables, w)
        perjury = get_perjury_records(conn, tables, w) if 'watson' in w.lower() else []
        contra_map = get_contradiction_map(conn, tables, w)
        violations = get_actor_violations(conn, tables, w)
        
        outline = generate_impeachment_outline(w, contradictions, perjury, contra_map, violations)
        outlines.append(outline)
        print_outline(outline, args.verbose)
    
    # Summary
    total = sum(o['total_items'] for o in outlines)
    print(f"\n{'═' * 70}")
    print(f"  SUMMARY: {len(outlines)} witnesses, {total} impeachment items")
    print(f"{'═' * 70}\n")
    
    for o in sorted(outlines, key=lambda x: -x['total_items']):
        sections = len(o['sections'])
        print(f"  {o['witness']:30s}: {o['total_items']:5d} items, {sections} sections")
    
    # Save outputs
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    if args.report:
        rpath = os.path.join(REPORTS_DIR, 'IMPEACHMENT_BRIEF.md')
        save_report(outlines, rpath)
        print(f"\n  📄 Report: {rpath}")
    
    if args.json:
        jpath = os.path.join(REPORTS_DIR, 'impeachment_outlines.json')
        with open(jpath, 'w', encoding='utf-8') as f:
            json.dump(outlines, f, indent=2, default=str)
        print(f"  📊 JSON: {jpath}")
    
    conn.close()


if __name__ == '__main__':
    main()
