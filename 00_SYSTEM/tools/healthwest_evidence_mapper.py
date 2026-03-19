#!/usr/bin/env python3
"""
Tool #220 — HealthWest Evidence Mapper
========================================
Maps HealthWest evaluation evidence to filing arguments.

Key facts mapped:
  - 1st eval (9/4/2025): CLEAN — no safety issues, ADHD noted but controlled
  - 2nd eval (9/11/2025): Rule-out delusional disorder — only 7 days later
  - Judge accepted 1st eval, rejected 2nd = selective evidence use = bias
  - Pamela Rusco called clinician directly + emailed subpoena = ex parte
  - "Delusional" basis: Andrew saying "this whole thing is illegal" = pathologizing legal criticism

Output: HEALTHWEST_EVIDENCE_MAP.md + healthwest_evidence_map.json
"""
import sys
import os
import json
import sqlite3
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(SCRIPT_DIR, '..', '..'))
DB_PATH = os.path.join(REPO, 'litigation_context.db')
REPORTS_DIR = os.path.join(REPO, '00_SYSTEM', 'reports')


def get_connection():
    """Open DB with required PRAGMAs."""
    conn = sqlite3.connect(DB_PATH, timeout=120)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def safe_query(conn, sql, params=()):
    """Execute query, return list of dicts. Returns [] on error."""
    try:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"  [WARN] Query failed: {e}")
        return []


def discover_health_tables(conn):
    """Find all tables that might contain HealthWest / medical data."""
    patterns = ['%health%', '%eval%', '%medical%', '%west%', '%clinical%', '%psych%']
    tables = set()
    for pat in patterns:
        rows = safe_query(conn,
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?", (pat,))
        for r in rows:
            tables.add(r['name'])
    return sorted(tables)


def get_table_columns(conn, table):
    """Return list of column names for a table."""
    rows = safe_query(conn, f"PRAGMA table_info({table})")
    return [r['name'] for r in rows]


def search_evidence_quotes(conn):
    """Search evidence_quotes for HealthWest-related content."""
    keywords = [
        '%HealthWest%', '%health%west%', '%delusional%', '%ADHD%',
        '%psychological%eval%', '%clinical%', '%mental%health%',
        '%Rusco%', '%subpoena%clinician%', '%rule-out%', '%rule out%',
        '%safety%issue%', '%parenting%eval%',
    ]
    where_clauses = ' OR '.join(['quote_text LIKE ?' for _ in keywords])
    sql = f"""
        SELECT id, quote_text, speaker, date_ref, legal_significance,
               evidence_category, source_type, document_id
        FROM evidence_quotes
        WHERE {where_clauses}
        ORDER BY date_ref, id
    """
    return safe_query(conn, sql, tuple(keywords))


def search_additional_tables(conn, tables):
    """Search discovered tables for HealthWest content."""
    results = {}
    for table in tables:
        cols = get_table_columns(conn, table)
        if not cols:
            continue
        text_cols = []
        for c in cols:
            # Try to find text-like columns
            if any(kw in c.lower() for kw in ['text', 'name', 'desc', 'note', 'content',
                                                'summary', 'detail', 'finding', 'title',
                                                'quote', 'source', 'path', 'file']):
                text_cols.append(c)
        if not text_cols:
            # Fallback: use first 3 columns
            text_cols = cols[:3]

        keywords = ['%HealthWest%', '%health%west%', '%delusional%', '%ADHD%',
                     '%Rusco%', '%clinical%eval%']
        for col in text_cols:
            for kw in keywords:
                try:
                    rows = conn.execute(
                        f"SELECT * FROM [{table}] WHERE [{col}] LIKE ? LIMIT 20",
                        (kw,)
                    ).fetchall()
                    if rows:
                        key = f"{table}.{col}"
                        if key not in results:
                            results[key] = []
                        results[key].extend([dict(r) for r in rows])
                except Exception:
                    pass
    return results


# --- Core Evidence Facts ---
HEALTHWEST_FACTS = [
    {
        "fact_id": "HW-001",
        "date": "2025-09-04",
        "title": "1st HealthWest Evaluation — CLEAN",
        "description": (
            "First HealthWest psychological evaluation found NO safety concerns. "
            "ADHD noted but controlled. No psychiatric diagnoses warranting custody restriction. "
            "Andrew assessed as competent, engaged parent."
        ),
        "significance": "CRITICAL — Establishes baseline: Andrew is fit parent per clinical eval.",
        "filings": ["F3-disqualification", "F6-JTC", "F7-custody"],
        "arguments": {
            "F3-disqualification": (
                "Judge McNeill accepted this eval but later relied on contradictory 2nd eval "
                "only 7 days later — selective evidence use violating MCR 2.003(C)(1)(b)."
            ),
            "F6-JTC": (
                "Judicial misconduct: accepting 1st eval as valid then ignoring it in favor of "
                "2nd eval obtained through ex parte contact = outcome-driven decision-making."
            ),
            "F7-custody": (
                "1st eval supports Andrew's fitness. No safety concerns identified. "
                "Any custody restriction based on 'mental health' is contradicted by this eval."
            ),
        },
    },
    {
        "fact_id": "HW-002",
        "date": "2025-09-11",
        "title": "2nd HealthWest Evaluation — Rule-Out Delusional Disorder",
        "description": (
            "Only 7 days after clean eval, second evaluation diagnosed 'rule-out delusional "
            "disorder.' The basis: Andrew stating 'this whole thing is illegal.' "
            "No new clinical evidence between evals. Same patient, radically different conclusion."
        ),
        "significance": (
            "CRITICAL — 7-day reversal with no new clinical data is medically unprecedented. "
            "Pathologizes protected legal speech (1st Amendment)."
        ),
        "filings": ["F3-disqualification", "F6-JTC", "F7-custody", "F10-1983"],
        "arguments": {
            "F3-disqualification": (
                "Judge relied on 2nd eval to justify custody restriction despite 1st eval clearing "
                "Andrew — demonstrates predetermined outcome, not evidence-based ruling."
            ),
            "F6-JTC": (
                "JTC complaint: judge facilitated procurement of contradictory eval through "
                "court staff (Rusco) to manufacture justification for custody denial."
            ),
            "F7-custody": (
                "Rebuttal: 'Rule-out' is NOT a diagnosis — it means 'consider and exclude.' "
                "Using it as basis for custody denial is clinical misapplication."
            ),
            "F10-1983": (
                "§1983 due process: Pathologizing statement 'this is illegal' as evidence of "
                "delusion = punishing protected speech. Chilling effect on litigant advocacy."
            ),
        },
    },
    {
        "fact_id": "HW-003",
        "date": "2025-09-04",
        "title": "7-Day Contradiction — No New Clinical Data",
        "description": (
            "Between 9/4 (clean) and 9/11 (delusional disorder), zero new clinical events, "
            "zero new evidence, zero new incidents. The ONLY intervening event was Pamela Rusco's "
            "direct contact with the clinician."
        ),
        "significance": (
            "The 7-day gap with no new data proves external influence on the 2nd eval. "
            "Temporal proximity to Rusco contact is devastating."
        ),
        "filings": ["F3-disqualification", "F6-JTC"],
        "arguments": {
            "F3-disqualification": (
                "Timeline: 9/4 clean → Rusco contacts clinician → 9/11 delusional disorder. "
                "No clinical basis for reversal = court-influenced outcome."
            ),
            "F6-JTC": (
                "Rusco is judge's secretary acting as agent of the court. Her direct clinician "
                "contact + subpoena email constitutes ex parte communication under MCR 2.003."
            ),
        },
    },
    {
        "fact_id": "HW-004",
        "date": "2025-09-11",
        "title": "Pamela Rusco Ex Parte Contact",
        "description": (
            "Pamela Rusco (FOC / judge's secretary) called the HealthWest clinician directly "
            "AND emailed a subpoena — both without notice to Andrew. This is textbook ex parte "
            "communication between court staff and a treating/evaluating clinician."
        ),
        "significance": (
            "CRITICAL — Ex parte contact with evaluator is grounds for disqualification. "
            "Rusco acted as agent of Judge McNeill."
        ),
        "filings": ["F3-disqualification", "F6-JTC", "F10-1983"],
        "arguments": {
            "F3-disqualification": (
                "MCR 2.003(C)(1)(b): ex parte communication through court staff. "
                "Rusco's contact with clinician was not disclosed to Andrew. "
                "Judge has duty to ensure staff compliance — failure = imputed bias."
            ),
            "F6-JTC": (
                "MCR 9.104, 9.202: Judicial staff acting as agent conducting ex parte contact "
                "with evaluation provider. JTC jurisdiction covers court staff acting under "
                "judge's authority."
            ),
            "F10-1983": (
                "Due process violation: secret contact with evaluator to influence clinical "
                "outcome without notice or opportunity to respond = § 1983 liability."
            ),
        },
    },
    {
        "fact_id": "HW-005",
        "date": "2025-09-11",
        "title": "Pathologizing Legal Criticism as 'Delusional'",
        "description": (
            "The basis for 'delusional disorder' diagnosis was Andrew's statement "
            "'this whole thing is illegal.' Criticizing court proceedings is protected speech, "
            "not a psychiatric symptom. This weaponizes mental health against a litigant."
        ),
        "significance": (
            "CRITICAL — Using protected legal speech as evidence of mental illness is a "
            "constitutional violation and clinical ethics breach."
        ),
        "filings": ["F3-disqualification", "F6-JTC", "F7-custody", "F10-1983"],
        "arguments": {
            "F3-disqualification": (
                "Judge accepted a diagnosis predicated on protected speech — demonstrates "
                "willingness to weaponize clinical authority against disfavored litigant."
            ),
            "F6-JTC": (
                "Judicial misconduct: facilitating psychiatric labeling of a litigant for "
                "exercising right to criticize court proceedings."
            ),
            "F7-custody": (
                "Rebuttal argument: 'This is illegal' is a legal conclusion, not a delusion. "
                "Courts have found ex parte contact illegal — Andrew's statement may be correct."
            ),
            "F10-1983": (
                "1st Amendment: chilling effect. If criticizing court = 'delusional,' no "
                "litigant can safely advocate without risking psychiatric retaliation. "
                "Garcetti v. Ceballos distinguishes — private litigants retain full 1A rights."
            ),
        },
    },
]

FILING_MAP = {
    "F3-disqualification": {
        "name": "Motion to Disqualify Judge McNeill",
        "authority": "MCR 2.003(C)(1)(b)",
        "hw_relevance": "Selective evidence use + ex parte contact through Rusco",
    },
    "F6-JTC": {
        "name": "Judicial Tenure Commission Complaint",
        "authority": "MCR 9.104, 9.202; Const 1963 Art 6 §30",
        "hw_relevance": "Court staff ex parte contact + outcome-driven eval procurement",
    },
    "F7-custody": {
        "name": "Motion to Restore Parenting Time / Custody Modification",
        "authority": "MCL 722.27; Child Custody Act",
        "hw_relevance": "1st eval clears Andrew; 2nd eval clinically invalid; best interest factors",
    },
    "F10-1983": {
        "name": "42 USC §1983 Federal Civil Rights Action",
        "authority": "42 USC §1983; 14th Amendment Due Process",
        "hw_relevance": "Pathologizing speech + secret eval manipulation = constitutional violation",
    },
}


def build_report(conn):
    """Build the full HealthWest evidence map."""
    print("=" * 70)
    print("  Tool #220 — HealthWest Evidence Mapper")
    print("=" * 70)

    # 1. Discover related tables
    print("\n[1/5] Discovering HealthWest-related tables...")
    health_tables = discover_health_tables(conn)
    print(f"  Found {len(health_tables)} related tables: {health_tables}")

    # 2. Search evidence_quotes
    print("\n[2/5] Searching evidence_quotes for HealthWest content...")
    hw_quotes = search_evidence_quotes(conn)
    print(f"  Found {len(hw_quotes)} matching quotes")

    # 3. Search additional tables
    print("\n[3/5] Searching additional tables for HealthWest references...")
    additional = search_additional_tables(conn, health_tables)
    total_additional = sum(len(v) for v in additional.values())
    print(f"  Found {total_additional} additional records across {len(additional)} table.column combos")

    # 4. Search drive_evidence and evidence_file_index for HealthWest files
    print("\n[4/5] Searching evidence indexes for HealthWest files...")
    hw_files = []
    for table in ['drive_evidence', 'evidence_file_index', 'scanned_evidence_catalog',
                   'evidence_extract_inventory', 'desktop_evidence_index']:
        cols = get_table_columns(conn, table)
        if not cols:
            continue
        for col in cols:
            if any(kw in col.lower() for kw in ['path', 'file', 'name', 'source']):
                rows = safe_query(conn,
                    f"SELECT * FROM [{table}] WHERE [{col}] LIKE '%HealthWest%' "
                    f"OR [{col}] LIKE '%health%west%' LIMIT 50", ())
                hw_files.extend([dict(r) for r in rows])
    print(f"  Found {len(hw_files)} HealthWest file references in evidence indexes")

    # 5. Build filing argument map
    print("\n[5/5] Building filing argument map...")
    filing_argument_map = {}
    for filing_id, filing_info in FILING_MAP.items():
        facts_for_filing = []
        for fact in HEALTHWEST_FACTS:
            if filing_id in fact['filings']:
                facts_for_filing.append({
                    "fact_id": fact['fact_id'],
                    "title": fact['title'],
                    "date": fact['date'],
                    "argument": fact['arguments'].get(filing_id, ''),
                })
        filing_argument_map[filing_id] = {
            **filing_info,
            "facts_count": len(facts_for_filing),
            "facts": facts_for_filing,
        }

    # Assemble full report
    report = {
        "tool": "Tool #220 — HealthWest Evidence Mapper",
        "generated": datetime.now().isoformat(),
        "summary": {
            "total_facts": len(HEALTHWEST_FACTS),
            "total_db_quotes": len(hw_quotes),
            "additional_table_hits": total_additional,
            "hw_file_references": len(hw_files),
            "filings_mapped": len(FILING_MAP),
            "health_tables_discovered": len(health_tables),
        },
        "healthwest_facts": HEALTHWEST_FACTS,
        "filing_argument_map": filing_argument_map,
        "db_evidence_quotes": hw_quotes,
        "discovered_tables": health_tables,
        "additional_table_results": {k: v[:5] for k, v in additional.items()},
        "hw_file_references": hw_files[:30],
    }

    return report


def write_markdown(report, path):
    """Write the markdown report."""
    r = report
    s = r['summary']
    lines = [
        "# HealthWest Evidence Map",
        f"*Generated: {r['generated']}*\n",
        "## Executive Summary\n",
        f"| Metric | Count |",
        f"|--------|-------|",
        f"| Core HealthWest Facts | {s['total_facts']} |",
        f"| DB Evidence Quotes | {s['total_db_quotes']} |",
        f"| Additional Table Hits | {s['additional_table_hits']} |",
        f"| File References | {s['hw_file_references']} |",
        f"| Filings Mapped | {s['filings_mapped']} |",
        f"| Health Tables Discovered | {s['health_tables_discovered']} |",
        "",
        "## Critical Timeline\n",
        "| Date | Event | Significance |",
        "|------|-------|-------------|",
        "| 9/4/2025 | 1st HealthWest Eval — **CLEAN** | No safety issues, ADHD controlled |",
        "| 9/4-9/11 | Pamela Rusco contacts clinician + emails subpoena | **EX PARTE** |",
        "| 9/11/2025 | 2nd HealthWest Eval — Rule-out delusional disorder | 7-day reversal, NO new data |",
        "",
        "## HealthWest Facts → Filing Arguments\n",
    ]

    for fact in HEALTHWEST_FACTS:
        lines.append(f"### {fact['fact_id']}: {fact['title']}")
        lines.append(f"**Date:** {fact['date']}\n")
        lines.append(f"{fact['description']}\n")
        lines.append(f"**Significance:** {fact['significance']}\n")
        lines.append("| Filing | Argument |")
        lines.append("|--------|----------|")
        for fid, arg in fact['arguments'].items():
            lines.append(f"| {fid} | {arg} |")
        lines.append("")

    lines.append("## Filing Readiness by HealthWest Evidence\n")
    for fid, fdata in r['filing_argument_map'].items():
        lines.append(f"### {fid}: {fdata['name']}")
        lines.append(f"- **Authority:** {fdata['authority']}")
        lines.append(f"- **HW Relevance:** {fdata['hw_relevance']}")
        lines.append(f"- **Supporting Facts:** {fdata['facts_count']}")
        for f in fdata['facts']:
            lines.append(f"  - [{f['fact_id']}] {f['title']}")
        lines.append("")

    if r['db_evidence_quotes']:
        lines.append("## DB Evidence Quotes (HealthWest-Related)\n")
        for q in r['db_evidence_quotes'][:20]:
            text = (q.get('quote_text') or '')[:200]
            lines.append(f"- **[ID {q.get('id')}]** ({q.get('date_ref', 'N/A')}): {text}...")
            if q.get('legal_significance'):
                lines.append(f"  - *Legal significance:* {q['legal_significance']}")
        lines.append("")

    if r['discovered_tables']:
        lines.append(f"## Discovered Health-Related Tables ({len(r['discovered_tables'])})\n")
        for t in r['discovered_tables']:
            lines.append(f"- `{t}`")
        lines.append("")

    lines.append("---")
    lines.append("*Tool #220 — HealthWest Evidence Mapper — LitigationOS*")

    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def main():
    os.makedirs(REPORTS_DIR, exist_ok=True)

    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database not found: {DB_PATH}")
        sys.exit(1)

    conn = get_connection()
    try:
        report = build_report(conn)

        # Write JSON
        json_path = os.path.join(REPORTS_DIR, 'healthwest_evidence_map.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str, ensure_ascii=False)
        print(f"\n[OK] JSON → {json_path}")

        # Write MD
        md_path = os.path.join(REPORTS_DIR, 'HEALTHWEST_EVIDENCE_MAP.md')
        write_markdown(report, md_path)
        print(f"[OK] MD   → {md_path}")

        # Summary
        s = report['summary']
        print(f"\n{'=' * 70}")
        print(f"  HEALTHWEST EVIDENCE MAP COMPLETE")
        print(f"  Facts: {s['total_facts']} | DB Quotes: {s['total_db_quotes']} | "
              f"Files: {s['hw_file_references']} | Filings: {s['filings_mapped']}")
        print(f"{'=' * 70}")
    finally:
        conn.close()


if __name__ == '__main__':
    main()
