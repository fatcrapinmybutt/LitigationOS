#!/usr/bin/env python3
"""
Tool #84 — Perjury Evidence Linker
=======================================
Links items from watson_perjury_compilation (5,821 items) to
specific filings where they're most useful.

Maps perjury evidence → filing exhibits → legal arguments.
Marks which items are most powerful for each filing.
"""
import sys, json, sqlite3
from pathlib import Path
from datetime import datetime
from collections import defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

# Filing topics — keywords to match perjury items to filings
FILING_KEYWORDS = {
    'F1': ['parenting', 'visitation', 'child', 'contact', 'custody', 'access', 'time', 'birthday'],
    'F2': ['fraud', 'perjury', 'false', 'fabricat', 'lie', 'sworn', 'deceiv', 'misrepresent'],
    'F3': ['judge', 'mcneill', 'bias', 'impartial', 'recus', 'disqualif', 'ex parte'],
    'F4': ['rights', 'constitutional', 'due process', 'liberty', 'civil', 'federal', 'section 1983'],
    'F5': ['supreme', 'superintend', 'void', 'jurisdiction', 'extraordinary'],
    'F6': ['judicial', 'tenure', 'canon', 'misconduct', 'ethics', 'complaint'],
    'F7': ['custody', 'modify', 'best interest', 'change', 'circumstance', 'child welfare'],
    'F8': ['appeal', 'leave', 'error', 'abuse of discretion', 'reversible'],
    'F9': ['appeal', 'brief', 'standard of review', 'error', 'record'],
    'F10': ['attorney', 'grievance', 'barnes', 'professional', 'misconduct', 'ethics'],
}

def main():
    print("=" * 70)
    print("PERJURY EVIDENCE LINKER — Tool #84")
    print("=" * 70)
    
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    
    # Check table schema
    cols = [r[1] for r in conn.execute("PRAGMA table_info(watson_perjury_compilation)").fetchall()]
    print(f"  Columns: {', '.join(cols[:8])}")
    
    total = conn.execute("SELECT COUNT(*) FROM watson_perjury_compilation").fetchone()[0]
    print(f"  Total perjury items: {total}")
    
    # Find text columns to search
    text_cols = []
    for c in cols:
        if any(kw in c.lower() for kw in ['text', 'content', 'description', 'statement', 'quote', 'detail', 'summary', 'allegation']):
            text_cols.append(c)
    
    if not text_cols:
        # Use first few string-looking columns
        text_cols = [c for c in cols if c not in ('id', 'rowid', 'created_at', 'updated_at')][:3]
    
    print(f"  Search columns: {', '.join(text_cols)}")
    
    # Link perjury items to filings
    filing_matches = defaultdict(int)
    filing_samples = defaultdict(list)
    
    for filing_id, keywords in FILING_KEYWORDS.items():
        for kw in keywords:
            for col in text_cols:
                try:
                    count = conn.execute(
                        f"SELECT COUNT(*) FROM watson_perjury_compilation WHERE LOWER(CAST({col} AS TEXT)) LIKE ?",
                        (f'%{kw.lower()}%',)
                    ).fetchone()[0]
                    filing_matches[filing_id] += count
                    
                    if count > 0 and len(filing_samples[filing_id]) < 3:
                        samples = conn.execute(
                            f"SELECT SUBSTR(CAST({col} AS TEXT), 1, 100) FROM watson_perjury_compilation WHERE LOWER(CAST({col} AS TEXT)) LIKE ? LIMIT 2",
                            (f'%{kw.lower()}%',)
                        ).fetchall()
                        for s in samples:
                            if s[0] and len(filing_samples[filing_id]) < 3:
                                filing_samples[filing_id].append(str(s[0])[:80])
                except Exception:
                    pass
    
    # Check admissibility status
    admissible_col = None
    for c in cols:
        if 'admiss' in c.lower() or 'status' in c.lower() or 'marked' in c.lower():
            admissible_col = c
            break
    
    admissible_count = 0
    if admissible_col:
        try:
            admissible_count = conn.execute(
                f"SELECT COUNT(*) FROM watson_perjury_compilation WHERE {admissible_col} = 'admissible' OR {admissible_col} = 1 OR {admissible_col} = 'yes'"
            ).fetchone()[0]
        except:
            pass
    
    conn.close()
    
    print(f"\n  Filing matches:")
    lines = [
        "# 🔗 PERJURY EVIDENCE LINKER",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        f"*Total perjury items: {total} | Admissibility marked: {admissible_count}*\n",
        "---\n",
        "## Evidence Distribution by Filing\n",
        "| Filing | Matched Items | Usefulness | Priority |",
        "|--------|--------------|------------|----------|",
    ]
    
    # Sort by match count
    sorted_filings = sorted(filing_matches.items(), key=lambda x: -x[1])
    
    for filing_id, count in sorted_filings:
        if count > 500:
            usefulness = "🔴 HIGH"
            priority = "⭐⭐⭐"
        elif count > 100:
            usefulness = "🟡 MEDIUM"
            priority = "⭐⭐"
        elif count > 0:
            usefulness = "🟢 LOW"
            priority = "⭐"
        else:
            usefulness = "⚪ NONE"
            priority = ""
        
        lines.append(f"| {filing_id} | {count:,} | {usefulness} | {priority} |")
        print(f"    {filing_id}: {count:>6,} matched items {usefulness}")
    
    # Add samples
    lines.append("\n## Sample Evidence per Filing\n")
    for filing_id, samples in filing_samples.items():
        if samples:
            lines.append(f"### {filing_id}")
            for i, s in enumerate(samples, 1):
                lines.append(f"{i}. _{s}_")
            lines.append("")
    
    lines.extend([
        "---",
        "## Action Items",
        f"- **{total} perjury items** available — {admissible_count} marked admissible",
        "- Top priority filings for perjury evidence: " + ', '.join(f[0] for f in sorted_filings[:3]),
        "- Run admissibility marker tool to classify all 5,821 items",
        "- Cross-reference with detected_contradictions (1,061 items) for strongest evidence",
        "",
        f"*Perjury Evidence Linker — Tool #84*",
    ])
    
    md_path = REPORTS_DIR / "PERJURY_LINKS.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "perjury_links.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Perjury Evidence Linker (#84)',
        'total_perjury_items': total,
        'admissible_count': admissible_count,
        'filing_matches': dict(sorted_filings),
    }, indent=2), encoding='utf-8')
    
    print(f"\n✅ {total} perjury items linked to filings")
    print(f"   Reports: PERJURY_LINKS.md + perjury_links.json")

if __name__ == '__main__':
    main()
