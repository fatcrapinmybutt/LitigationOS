#!/usr/bin/env python3
"""
Tool #103 — Judicial Canon Violation Cross-Referencer
=========================================================
🆕 NOVEL TOOL — Maps each judicial violation to specific
Michigan Code of Judicial Conduct canons

Takes the 1,127 violations from judicial_violations table
and cross-references against the 7 Canons:
- Canon 1: Integrity and Independence
- Canon 2: Avoiding Impropriety  
- Canon 3: Performing Duties Impartially
- Canon 4: Extra-Judicial Activities
- Canon 5: Quasi-Judicial Activities
- Canon 6: Political Activity
- Canon 7: A Judge Should Not Practice Law

Creates a violation-to-canon matrix for JTC complaint (F6)
and disqualification motion (F3).
"""
import sys, json, sqlite3
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

CANONS = {
    'Canon 1': {
        'title': 'A Judge Should Uphold the Integrity and Independence of the Judiciary',
        'keywords': ['integrity', 'independence', 'trust', 'confidence', 'dignit'],
        'violations_expected': ['Appearance of impropriety', 'Undermining public confidence'],
    },
    'Canon 2': {
        'title': 'A Judge Should Avoid Impropriety and the Appearance of Impropriety',
        'keywords': ['impropriet', 'appearance', 'ex parte', 'ex-parte', 'bias', 'prejudice', 
                     'partial', 'favorit', 'one-sided', 'unfair'],
        'violations_expected': ['Ex-parte communications', 'Appearance of bias', 'Favoritism'],
    },
    'Canon 3': {
        'title': 'A Judge Should Perform the Duties of Office Impartially and Diligently',
        'keywords': ['impartial', 'diligen', 'prompt', 'fair', 'hearing', 'notice', 
                     'opportunity', 'due process', 'procedur'],
        'violations_expected': ['Denial of due process', 'Failure to provide hearing', 'Procedural violations'],
    },
    'Canon 4': {
        'title': 'A Judge May Engage in Extra-Judicial Activities',
        'keywords': ['extra-judicial', 'outside', 'financial', 'business'],
        'violations_expected': [],
    },
    'Canon 5': {
        'title': 'A Judge Should Regulate Quasi-Judicial Activities',
        'keywords': ['quasi-judicial', 'referee', 'mediator', 'arbitrat'],
        'violations_expected': [],
    },
    'Canon 6': {
        'title': 'Political Activity',
        'keywords': ['political', 'campaign', 'election', 'endorse'],
        'violations_expected': [],
    },
    'Canon 7': {
        'title': 'A Judge Should Not Practice Law',
        'keywords': ['practice law', 'legal advice', 'counsel'],
        'violations_expected': [],
    },
}

def classify_violation(text):
    """Classify a violation text to the most relevant canon."""
    text_lower = text.lower() if text else ''
    scores = {}
    
    for canon, data in CANONS.items():
        score = sum(1 for kw in data['keywords'] if kw in text_lower)
        scores[canon] = score
    
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return 'Canon 3'  # Default — most violations are procedural
    return best

def main():
    print("=" * 70)
    print("JUDICIAL CANON VIOLATION CROSS-REFERENCER — Tool #103")
    print("=" * 70)
    
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    
    # Get violations
    violations = []
    canon_counts = {c: 0 for c in CANONS}
    
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(judicial_violations)").fetchall()]
        
        text_cols = [c for c in cols if any(k in c.lower() for k in ['statement', 'text', 'desc', 'violation'])]
        severity_col = next((c for c in cols if 'severity' in c.lower()), None)
        
        text_col = text_cols[0] if text_cols else cols[1] if len(cols) > 1 else None
        
        if text_col:
            rows = conn.execute(f"""
                SELECT {text_col}{', ' + severity_col if severity_col else ''}
                FROM judicial_violations LIMIT 2000
            """).fetchall()
            
            for row in rows:
                text = str(row[0])
                severity = str(row[1]) if len(row) > 1 else 'unknown'
                canon = classify_violation(text)
                canon_counts[canon] += 1
                violations.append({
                    'text': text[:200],
                    'severity': severity,
                    'canon': canon,
                })
    except Exception as e:
        print(f"  ⚠️ Error reading violations: {e}")
    
    conn.close()
    
    total = len(violations)
    
    lines = [
        "# ⚖️ JUDICIAL CANON VIOLATION CROSS-REFERENCE",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #103*\n",
        "---\n",
        "## Canon Violation Distribution\n",
        "| Canon | Title | Violations | % |",
        "|-------|-------|-----------|---|",
    ]
    
    for canon in sorted(CANONS.keys()):
        count = canon_counts[canon]
        pct = (count / total * 100) if total > 0 else 0
        bar = '█' * int(pct / 5) + '░' * (20 - int(pct / 5))
        lines.append(f"| {canon} | {CANONS[canon]['title'][:40]} | {count:,} | {pct:.1f}% {bar} |")
        
        if count > 0:
            print(f"  {canon}: {count:,} violations ({pct:.1f}%)")
    
    lines.append(f"\n**Total: {total:,} violations classified**\n")
    
    # Top violations per canon
    for canon in ['Canon 2', 'Canon 3', 'Canon 1']:
        canon_violations = [v for v in violations if v['canon'] == canon][:5]
        if canon_violations:
            lines.append(f"### {canon} — Top Violations\n")
            for v in canon_violations:
                lines.append(f"- [{v['severity']}] {v['text'][:100]}")
            lines.append("")
    
    lines.extend([
        "---",
        "## Use in Filings\n",
        "- **F3 (Disqualification)**: Cite Canon 2 + Canon 3 violations",
        "- **F6 (JTC Complaint)**: Cite ALL canon violations with specific examples",
        "- **F9 (COA Brief)**: Cite Canon 3 (due process) violations as preserved error",
        "",
        f"*Judicial Canon Cross-Referencer — Tool #103 — {total:,} violations mapped to 7 canons*",
    ])
    
    md_path = REPORTS_DIR / "CANON_VIOLATIONS.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "canon_violations.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Canon Violation Cross-Referencer (#103)',
        'total_violations': total,
        'canon_counts': canon_counts,
    }, indent=2), encoding='utf-8')
    
    print(f"\n✅ {total:,} violations mapped to 7 Canons of Judicial Conduct")
    print(f"   Top canon: {max(canon_counts, key=canon_counts.get)} ({max(canon_counts.values()):,})")
    print(f"   Reports: CANON_VIOLATIONS.md + canon_violations.json")

if __name__ == '__main__':
    main()
