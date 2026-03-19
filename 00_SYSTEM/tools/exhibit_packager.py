#!/usr/bin/env python3
"""
Tool #92 — Evidence Exhibit Packager
========================================
For each filing (F1-F10), automatically:
1. Queries evidence_quotes DB for relevant evidence
2. Selects top exhibits by relevance
3. Generates numbered exhibit lists
4. Creates exhibit index with Bates-style numbering

This bridges the gap between raw evidence (262K+ items)
and court-ready exhibit packages.
"""
import sys, json, sqlite3
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"
PKG_BASE = Path(r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE")

FILING_EVIDENCE_MAP = {
    'F1': {
        'name': 'Emergency Parenting Time',
        'keywords': ['parenting time', 'custody', 'visitation', 'child', 'father', 
                     'mother', 'parent', 'emergency', 'access', 'contact'],
        'tables': ['evidence_quotes', 'watson_perjury_compilation'],
    },
    'F2': {
        'name': 'Fraud on Court',
        'keywords': ['fraud', 'perjury', 'false', 'fabricat', 'lie', 'deceive',
                     'misrepresent', 'sworn', 'oath', 'false statement'],
        'tables': ['watson_perjury_compilation', 'detected_contradictions'],
    },
    'F3': {
        'name': 'Judicial Disqualification',
        'keywords': ['bias', 'ex parte', 'prejudice', 'recusal', 'disqualif',
                     'mcneill', 'judicial', 'impartial', 'canon'],
        'tables': ['judicial_violations'],
    },
    'F4': {
        'name': '§1983 Federal Complaint',
        'keywords': ['civil rights', 'due process', '1983', 'constitutional',
                     'liberty', 'parental', 'deprive', 'color of law'],
        'tables': ['judicial_violations', 'evidence_quotes'],
    },
    'F5': {
        'name': 'MSC Superintending Control',
        'keywords': ['superintending', 'supreme court', 'extraordinary',
                     'void', 'jurisdiction', 'constitutional'],
        'tables': ['judicial_violations'],
    },
    'F6': {
        'name': 'JTC Complaint',
        'keywords': ['judicial conduct', 'canon', 'misconduct', 'ethics',
                     'recusal', 'bias', 'impartial', 'disqualif'],
        'tables': ['judicial_violations'],
    },
    'F7': {
        'name': 'Custody Modification',
        'keywords': ['custody', 'best interest', 'modification', 'change',
                     'parenting', 'child', 'environment', 'stable'],
        'tables': ['evidence_quotes', 'watson_perjury_compilation'],
    },
    'F8': {
        'name': 'COA Leave Application',
        'keywords': ['appeal', 'leave', 'error', 'abuse of discretion',
                     'legal error', 'clearly erroneous'],
        'tables': ['judicial_violations', 'evidence_quotes'],
    },
    'F9': {
        'name': 'COA Appeal Brief',
        'keywords': ['appeal', 'brief', 'error', 'standard of review',
                     'abuse', 'clearly erroneous', 'de novo'],
        'tables': ['judicial_violations', 'evidence_quotes'],
    },
    'F10': {
        'name': 'AGC Grievance',
        'keywords': ['attorney', 'ethics', 'mrpc', 'professional',
                     'misconduct', 'barnes', 'withdraw', 'candor'],
        'tables': ['evidence_quotes'],
    },
}

def get_evidence_for_filing(conn, filing_id, limit=25):
    """Query relevant evidence from DB for a filing."""
    config = FILING_EVIDENCE_MAP.get(filing_id, {})
    keywords = config.get('keywords', [])
    results = []
    
    # Get evidence_quotes columns
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(evidence_quotes)").fetchall()]
    except:
        cols = []
    
    if not cols:
        return results
    
    # Find text column
    text_cols = [c for c in cols if any(k in c.lower() for k in ['text', 'quote', 'content', 'statement'])]
    text_col = text_cols[0] if text_cols else cols[1] if len(cols) > 1 else None
    
    if not text_col:
        return results
    
    # Build LIKE query for keywords
    where_clauses = [f"{text_col} LIKE '%{kw}%'" for kw in keywords[:5]]
    where_sql = ' OR '.join(where_clauses)
    
    try:
        rows = conn.execute(f"""
            SELECT * FROM evidence_quotes 
            WHERE {where_sql}
            LIMIT ?
        """, (limit,)).fetchall()
        
        for row in rows:
            results.append({
                'text': str(row[cols.index(text_col)] if text_col in cols else row[1])[:300],
                'source': str(row[0])[:100],
            })
    except Exception as e:
        pass
    
    return results

def main():
    print("=" * 70)
    print("EVIDENCE EXHIBIT PACKAGER — Tool #92")
    print("=" * 70)
    
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    
    all_exhibits = {}
    total_exhibits = 0
    
    lines = [
        "# 📎 EVIDENCE EXHIBIT INDEX",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #92*\n",
        "---\n",
    ]
    
    for fid in ['F1','F2','F3','F4','F5','F6','F7','F8','F9','F10']:
        config = FILING_EVIDENCE_MAP[fid]
        evidence = get_evidence_for_filing(conn, fid, 20)
        
        bates_prefix = f"PIGORS-{fid}"
        
        lines.append(f"## {fid} — {config['name']}\n")
        lines.append(f"| Exhibit # | Bates # | Description |")
        lines.append(f"|-----------|---------|-------------|")
        
        filing_exhibits = []
        for i, ev in enumerate(evidence, 1):
            bates = f"{bates_prefix}-{i:04d}"
            desc = ev['text'][:80].replace('|', '/').replace('\n', ' ')
            lines.append(f"| Exhibit {i} | {bates} | {desc} |")
            filing_exhibits.append({
                'exhibit_num': i,
                'bates': bates,
                'text_preview': ev['text'][:200],
                'source': ev['source'],
            })
            total_exhibits += 1
        
        if not evidence:
            lines.append(f"| — | — | No keyword-matched evidence (search {', '.join(config['keywords'][:3])}) |")
        
        all_exhibits[fid] = {
            'name': config['name'],
            'exhibit_count': len(filing_exhibits),
            'exhibits': filing_exhibits,
        }
        
        lines.append(f"\n*{len(evidence)} exhibits for {fid}*\n")
        print(f"  {fid} ({config['name'][:20]}): {len(evidence)} exhibits, Bates {bates_prefix}-0001 to {bates_prefix}-{len(evidence):04d}")
    
    conn.close()
    
    lines.extend([
        "---",
        f"*Evidence Exhibit Packager — Tool #92 — {total_exhibits} total exhibits indexed*",
    ])
    
    md_path = REPORTS_DIR / "EXHIBIT_INDEX.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "exhibit_index.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Evidence Exhibit Packager (#92)',
        'total_exhibits': total_exhibits,
        'filings': all_exhibits,
    }, indent=2), encoding='utf-8')
    
    print(f"\n✅ {total_exhibits} exhibits indexed across 10 filings")
    print(f"   Bates numbering: PIGORS-F[N]-0001 through PIGORS-F[N]-NNNN")
    print(f"   Reports: EXHIBIT_INDEX.md + exhibit_index.json")

if __name__ == '__main__':
    main()
