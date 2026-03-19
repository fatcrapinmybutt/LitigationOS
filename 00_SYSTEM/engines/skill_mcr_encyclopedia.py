"""
skill_mcr_encyclopedia.py — Michigan Court Rules Encyclopedia Skill
Provides full-text search, rule lookup, deadline extraction, and compliance checking
for all Michigan Court Rules (MCR) in the LitigationOS database.
"""
import sqlite3, sys, json, re, os
sys.stdout.reconfigure(encoding='utf-8')

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"

def _connect():
    conn = sqlite3.connect(DB, timeout=120)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn

# ─────────────────────────────────────────────
# search_rule(query) — Full-text search across MCR rules
# ─────────────────────────────────────────────
def search_rule(query: str, limit: int = 10) -> list[dict]:
    """Search MCR rules by keyword or phrase. Returns matching rules ranked by relevance."""
    conn = _connect()
    # FTS5 search
    results = []
    try:
        rows = conn.execute("""
            SELECT e.rule_number, e.rule_title, e.chapter, e.summary,
                   e.filing_types, e.cross_refs,
                   length(e.full_text) as text_length
            FROM mcr_encyclopedia_fts f
            JOIN mcr_encyclopedia e ON e.rowid = f.rowid
            WHERE mcr_encyclopedia_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (query, limit)).fetchall()
        for r in rows:
            results.append({
                'rule_number': f"MCR {r['rule_number']}",
                'title': r['rule_title'],
                'chapter': r['chapter'],
                'summary': r['summary'][:300] if r['summary'] else '',
                'filing_types': json.loads(r['filing_types'] or '[]'),
                'cross_refs': json.loads(r['cross_refs'] or '[]'),
                'text_length': r['text_length']
            })
    except Exception as e:
        # Fallback to LIKE search if FTS fails
        rows = conn.execute("""
            SELECT rule_number, rule_title, chapter, summary,
                   filing_types, cross_refs, length(full_text) as text_length
            FROM mcr_encyclopedia
            WHERE full_text LIKE ? OR rule_title LIKE ? OR rule_number LIKE ?
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", f"%{query}%", limit)).fetchall()
        for r in rows:
            results.append({
                'rule_number': f"MCR {r['rule_number']}",
                'title': r['rule_title'],
                'chapter': r['chapter'],
                'summary': (r['summary'] or '')[:300],
                'filing_types': json.loads(r['filing_types'] or '[]'),
                'cross_refs': json.loads(r['cross_refs'] or '[]'),
                'text_length': r['text_length']
            })
    conn.close()
    return results

# ─────────────────────────────────────────────
# get_rule(rule_number) — Full rule text + requirements
# ─────────────────────────────────────────────
def get_rule(rule_number: str) -> dict | None:
    """Get complete rule text, requirements, deadlines, and cross-references.
    Accepts: '7.212', 'MCR 7.212', 'mcr 7.212', '2.119(A)' etc.
    """
    conn = _connect()
    # Normalize input
    rnum = re.sub(r'^MCR\s*', '', rule_number.strip(), flags=re.IGNORECASE)
    # Strip subrule for lookup, but note it
    base_rnum = re.split(r'\(', rnum)[0]
    
    row = conn.execute("""
        SELECT * FROM mcr_encyclopedia WHERE rule_number = ?
    """, (base_rnum,)).fetchone()
    
    if not row:
        # Try partial match
        row = conn.execute("""
            SELECT * FROM mcr_encyclopedia WHERE rule_number LIKE ?
            LIMIT 1
        """, (f"%{base_rnum}%",)).fetchone()
    
    conn.close()
    if not row:
        return None
    
    return {
        'rule_id': row['rule_id'],
        'rule_number': f"MCR {row['rule_number']}",
        'title': row['rule_title'],
        'chapter': row['chapter'],
        'full_text': row['full_text'],
        'requirements': json.loads(row['requirements_json'] or '[]'),
        'deadlines': json.loads(row['deadlines_json'] or '[]'),
        'filing_types': json.loads(row['filing_types'] or '[]'),
        'cross_refs': json.loads(row['cross_refs'] or '[]'),
        'summary': row['summary']
    }

# ─────────────────────────────────────────────
# get_deadlines(rule_number) — All deadlines for a rule
# ─────────────────────────────────────────────
def get_deadlines(rule_number: str) -> list[dict]:
    """Extract all deadline references from a specific MCR rule.
    Returns list of {days, context} dicts sorted by day count.
    """
    rule = get_rule(rule_number)
    if not rule:
        return []
    deadlines = rule.get('deadlines', [])
    # Also do a fresh parse for completeness
    text = rule.get('full_text', '')
    extra = []
    patterns = [
        (r'within (\d+) days?', 'within'),
        (r'(\d+) days? (?:after|before|of|from)', 'relative'),
        (r'not (?:later|less) than (\d+) days?', 'not later than'),
        (r'at least (\d+) days?', 'at least'),
        (r'no (?:later|more) than (\d+) days?', 'no later than'),
        (r'(\d+)-day', 'N-day'),
    ]
    seen_contexts = {d.get('context', '')[:40] for d in deadlines}
    for pat, dtype in patterns:
        for m in re.finditer(pat, text, re.IGNORECASE):
            start = max(0, m.start() - 80)
            end = min(len(text), m.end() + 80)
            ctx = text[start:end].replace('\n', ' ').strip()
            if ctx[:40] not in seen_contexts:
                extra.append({
                    'days': int(m.group(1)),
                    'type': dtype,
                    'context': ctx
                })
                seen_contexts.add(ctx[:40])
    all_deadlines = deadlines + extra
    all_deadlines.sort(key=lambda x: x.get('days', 999))
    return all_deadlines

# ─────────────────────────────────────────────
# check_compliance(filing_type, document_text) — Compliance issues
# ─────────────────────────────────────────────
def check_compliance(filing_type: str, document_text: str = "") -> list[dict]:
    """Check compliance with MCR rules for a given filing type.
    Returns list of potential compliance issues with rule references.
    
    filing_type: 'motion', 'brief', 'complaint', 'answer', 'appeal', 
                 'application', 'affidavit', 'response', etc.
    document_text: optional text of the document to check against rules.
    """
    conn = _connect()
    issues = []
    filing_lower = filing_type.lower().strip()
    
    # Map filing types to key rules
    FILING_RULE_MAP = {
        'motion': ['2.119', '2.113', '2.107'],
        'brief': ['7.212', '2.119', '7.215'],
        'complaint': ['2.101', '2.111', '2.113', '2.112'],
        'answer': ['2.110', '2.111', '2.108'],
        'appeal': ['7.204', '7.205', '7.203'],
        'claim of appeal': ['7.204', '7.203', '7.210'],
        'leave to appeal': ['7.205', '7.203'],
        'application': ['7.205', '7.305'],
        'affidavit': ['2.119', '1.109'],
        'response': ['2.119', '2.108'],
        'reply': ['2.119'],
        'appendix': ['7.212', '7.210'],
        'petition': ['3.206', '3.207'],
        'ex parte': ['3.207', '2.119'],
        'summary disposition': ['2.116'],
        'discovery': ['2.302', '2.306', '2.307', '2.309', '2.310'],
        'domestic relations': ['3.206', '3.207', '3.210'],
    }
    
    # Find applicable rules
    applicable_rules = FILING_RULE_MAP.get(filing_lower, [])
    if not applicable_rules:
        # Try partial match
        for key, rules in FILING_RULE_MAP.items():
            if key in filing_lower or filing_lower in key:
                applicable_rules.extend(rules)
    
    if not applicable_rules:
        # Fallback: search for filing type in FTS
        try:
            rows = conn.execute("""
                SELECT e.rule_number, e.rule_title, e.requirements_json, e.deadlines_json
                FROM mcr_encyclopedia_fts f
                JOIN mcr_encyclopedia e ON e.rowid = f.rowid
                WHERE mcr_encyclopedia_fts MATCH ?
                LIMIT 5
            """, (filing_lower,)).fetchall()
            for r in rows:
                applicable_rules.append(r['rule_number'])
        except:
            pass
    
    # Check each applicable rule
    for rnum in applicable_rules:
        row = conn.execute("""
            SELECT rule_number, rule_title, requirements_json, deadlines_json, full_text
            FROM mcr_encyclopedia WHERE rule_number = ?
        """, (rnum,)).fetchone()
        if not row:
            continue
        
        reqs = json.loads(row['requirements_json'] or '[]')
        dls = json.loads(row['deadlines_json'] or '[]')
        
        # Check requirements
        for req in reqs[:10]:
            issue = {
                'rule': f"MCR {row['rule_number']}",
                'title': row['rule_title'],
                'type': 'requirement',
                'description': req,
                'status': 'check'
            }
            # If document text provided, try to verify compliance
            if document_text:
                # Simple heuristic checks
                req_lower = req.lower()
                doc_lower = document_text.lower()
                if 'caption' in req_lower and ('caption' not in doc_lower and 'case no' not in doc_lower):
                    issue['status'] = 'MISSING'
                elif 'proof of service' in req_lower and 'proof of service' not in doc_lower:
                    issue['status'] = 'MISSING'
                elif 'verification' in req_lower and 'verif' not in doc_lower:
                    issue['status'] = 'MISSING'
                elif 'signature' in req_lower and ('signature' not in doc_lower and '/s/' not in doc_lower):
                    issue['status'] = 'MISSING'
            issues.append(issue)
        
        # Check deadlines
        for dl in dls[:5]:
            issues.append({
                'rule': f"MCR {row['rule_number']}",
                'title': row['rule_title'],
                'type': 'deadline',
                'description': f"{dl.get('days', '?')} days — {dl.get('context', '')}",
                'status': 'verify_timing'
            })
    
    conn.close()
    return issues


# ─────────────────────────────────────────────
# CLI Interface
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="MCR Encyclopedia Skill")
    sub = parser.add_subparsers(dest='command')
    
    p_search = sub.add_parser('search', help='Search MCR rules')
    p_search.add_argument('query', help='Search query')
    p_search.add_argument('--limit', type=int, default=10)
    
    p_get = sub.add_parser('get', help='Get specific MCR rule')
    p_get.add_argument('rule', help='Rule number (e.g., 7.212)')
    
    p_dl = sub.add_parser('deadlines', help='Get deadlines for a rule')
    p_dl.add_argument('rule', help='Rule number')
    
    p_comply = sub.add_parser('compliance', help='Check compliance')
    p_comply.add_argument('filing_type', help='Filing type (motion, brief, etc.)')
    p_comply.add_argument('--text', default='', help='Document text to check')
    
    args = parser.parse_args()
    
    if args.command == 'search':
        results = search_rule(args.query, args.limit)
        print(f"\n{'='*70}")
        print(f"  MCR ENCYCLOPEDIA — Search: '{args.query}'")
        print(f"  Found {len(results)} matching rules")
        print(f"{'='*70}\n")
        for i, r in enumerate(results, 1):
            print(f"  {i}. {r['rule_number']} — {r['title']}")
            if r['summary']:
                print(f"     {r['summary'][:120]}...")
            if r['filing_types']:
                print(f"     Filing types: {', '.join(r['filing_types'][:5])}")
            print()
    
    elif args.command == 'get':
        rule = get_rule(args.rule)
        if rule:
            print(f"\n{'='*70}")
            print(f"  {rule['rule_number']} — {rule['title']}")
            print(f"  Chapter: {rule['chapter']}")
            print(f"{'='*70}\n")
            # Print full text (truncated for CLI)
            text = rule['full_text'] or ''
            if len(text) > 3000:
                print(text[:3000])
                print(f"\n  ... [{len(text) - 3000} more characters] ...")
            else:
                print(text)
            print(f"\n{'─'*70}")
            print(f"  Requirements ({len(rule['requirements'])}):")
            for req in rule['requirements'][:10]:
                print(f"    • {req[:120]}")
            print(f"\n  Deadlines ({len(rule['deadlines'])}):")
            for dl in rule['deadlines'][:10]:
                print(f"    ⏰ {dl.get('days','?')} days — {dl.get('context','')[:100]}")
            print(f"\n  Cross-References ({len(rule['cross_refs'])}):")
            for ref in rule['cross_refs'][:15]:
                print(f"    → {ref}")
            print(f"\n  Filing Types: {', '.join(rule['filing_types'])}")
        else:
            print(f"  [NOT FOUND] Rule '{args.rule}' not in encyclopedia")
    
    elif args.command == 'deadlines':
        dls = get_deadlines(args.rule)
        rnum = re.sub(r'^MCR\s*', '', args.rule.strip(), flags=re.IGNORECASE)
        print(f"\n{'='*70}")
        print(f"  MCR {rnum} — Deadline Analysis")
        print(f"  Found {len(dls)} deadline references")
        print(f"{'='*70}\n")
        for dl in dls:
            print(f"  ⏰ {dl.get('days','?'):>4} days — {dl.get('context','')[:100]}")
    
    elif args.command == 'compliance':
        issues = check_compliance(args.filing_type, args.text)
        print(f"\n{'='*70}")
        print(f"  COMPLIANCE CHECK — Filing Type: '{args.filing_type}'")
        print(f"  Found {len(issues)} items to verify")
        print(f"{'='*70}\n")
        for iss in issues:
            status_icon = '❌' if iss['status'] == 'MISSING' else '⚠️' if iss['status'] == 'verify_timing' else '🔍'
            print(f"  {status_icon} [{iss['rule']}] ({iss['type']}) {iss['description'][:100]}")
    
    else:
        parser.print_help()
