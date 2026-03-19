#!/usr/bin/env python3
"""
Tool #56 — Perjury Compiler Fix
==================================
Fixes the perjury compilation queries to use correct column names.
Previous versions used wrong column names causing empty results.

Verified schema from PRAGMA table_info(watson_perjury_compilation):
- watson_member (NOT actor)
- statement_text
- contradicting_evidence
- source_doc
- date_of_statement
- perjury_type
- severity_score
- admissible
- mcr_mre_authority
"""
import sys, json, sqlite3
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

def main():
    print("=" * 70)
    print("PERJURY COMPILER FIX — Tool #56")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)
    
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.row_factory = sqlite3.Row
    
    # Verify schema
    print("\n📋 Verifying watson_perjury_compilation schema...")
    cols = [r[1] for r in conn.execute("PRAGMA table_info(watson_perjury_compilation)").fetchall()]
    print(f"  Columns: {', '.join(cols)}")
    
    # Get total count
    total = conn.execute("SELECT COUNT(*) FROM watson_perjury_compilation").fetchone()[0]
    print(f"  Total rows: {total:,}")
    
    # Break down by watson_member
    print("\n👥 Breakdown by watson_member:")
    by_member = conn.execute("""
        SELECT watson_member, COUNT(*) as cnt 
        FROM watson_perjury_compilation 
        GROUP BY watson_member 
        ORDER BY cnt DESC
    """).fetchall()
    for r in by_member:
        print(f"  {r['watson_member']}: {r['cnt']:,}")
    
    # Break down by perjury_type
    print("\n📊 Breakdown by perjury_type:")
    by_type = conn.execute("""
        SELECT perjury_type, COUNT(*) as cnt 
        FROM watson_perjury_compilation 
        GROUP BY perjury_type 
        ORDER BY cnt DESC
        LIMIT 15
    """).fetchall()
    for r in by_type:
        print(f"  {r['perjury_type']}: {r['cnt']:,}")
    
    # Break down by severity
    print("\n⚡ Breakdown by severity_score:")
    by_severity = conn.execute("""
        SELECT severity_score, COUNT(*) as cnt 
        FROM watson_perjury_compilation 
        GROUP BY severity_score 
        ORDER BY severity_score DESC
        LIMIT 10
    """).fetchall()
    for r in by_severity:
        print(f"  Score {r['severity_score']}: {r['cnt']:,}")
    
    # Admissible items (prosecution-ready)
    admissible = conn.execute("""
        SELECT COUNT(*) FROM watson_perjury_compilation 
        WHERE admissible = 1 OR admissible = 'true' OR admissible = 'yes' OR CAST(admissible AS INTEGER) = 1
    """).fetchone()[0]
    print(f"\n✅ Admissible/prosecution-ready: {admissible:,}")
    
    # High severity admissible items
    high_sev = conn.execute("""
        SELECT COUNT(*) FROM watson_perjury_compilation 
        WHERE (admissible = 1 OR admissible = 'true' OR admissible = 'yes' OR CAST(admissible AS INTEGER) = 1)
        AND CAST(severity_score AS REAL) >= 7.0
    """).fetchone()[0]
    print(f"🔴 High severity (≥7.0) + admissible: {high_sev:,}")
    
    # Sample top items
    print("\n📄 Top 5 highest-severity items:")
    top = conn.execute("""
        SELECT watson_member, statement_text, perjury_type, severity_score, source_doc
        FROM watson_perjury_compilation
        ORDER BY CAST(severity_score AS REAL) DESC
        LIMIT 5
    """).fetchall()
    for i, r in enumerate(top, 1):
        print(f"  {i}. [{r['severity_score']}] {r['watson_member']}: {str(r['statement_text'])[:120]}...")
        print(f"     Type: {r['perjury_type']} | Source: {str(r['source_doc'])[:60]}")
    
    # Also check detected_contradictions
    print("\n📋 Checking detected_contradictions...")
    dc_cols = [r[1] for r in conn.execute("PRAGMA table_info(detected_contradictions)").fetchall()]
    print(f"  Columns: {', '.join(dc_cols)}")
    dc_total = conn.execute("SELECT COUNT(*) FROM detected_contradictions").fetchone()[0]
    print(f"  Total: {dc_total:,}")
    
    conn.close()
    
    # Generate report
    report = {
        'generated': datetime.now().isoformat(),
        'tool': 'Perjury Compiler Fix (#56)',
        'watson_perjury_compilation': {
            'total': total,
            'columns': cols,
            'by_member': {r['watson_member']: r['cnt'] for r in by_member},
            'by_type': {r['perjury_type']: r['cnt'] for r in by_type},
            'admissible': admissible,
            'high_severity_admissible': high_sev,
        },
        'detected_contradictions': {
            'total': dc_total,
            'columns': dc_cols,
        },
    }
    
    json_path = REPORTS_DIR / "perjury_compiler_fix.json"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding='utf-8')
    
    md_lines = [
        "# PERJURY COMPILER — FIXED REPORT",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n",
        f"## watson_perjury_compilation",
        f"- **Total items:** {total:,}",
        f"- **Admissible:** {admissible:,}",
        f"- **High severity + admissible:** {high_sev:,}",
        "",
        "### By Watson Member",
        "| Member | Count |",
        "|--------|-------|",
    ]
    for r in by_member:
        md_lines.append(f"| {r['watson_member']} | {r['cnt']:,} |")
    
    md_lines.extend(["", "### By Perjury Type", "| Type | Count |", "|------|-------|"])
    for r in by_type:
        md_lines.append(f"| {r['perjury_type']} | {r['cnt']:,} |")
    
    md_lines.extend([
        "",
        f"## detected_contradictions: {dc_total:,} total",
    ])
    
    md_path = REPORTS_DIR / "PERJURY_COMPILER_REPORT.md"
    md_path.write_text('\n'.join(md_lines), encoding='utf-8')
    
    print(f"\n✅ Reports: {json_path.name}, {md_path.name}")
    print(f"📊 Perjury compilation: {total:,} items, {admissible:,} admissible, {high_sev:,} high-severity")

if __name__ == '__main__':
    main()
