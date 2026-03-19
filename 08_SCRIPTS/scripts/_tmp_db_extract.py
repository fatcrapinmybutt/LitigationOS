import sys
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

import sqlite3
import os

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
OUTPUT_PATH = r"C:\Users\andre\LitigationOS\_tmp_db_evidence_extract.txt"

def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.row_factory = sqlite3.Row
    return conn

def table_exists(conn, name):
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return cur.fetchone() is not None

def get_columns(conn, name):
    cur = conn.execute(f"PRAGMA table_info({name})")
    return [row[1] for row in cur.fetchall()]

def fmt_row(row, cols, max_col_width=120):
    parts = []
    for c in cols:
        val = row[c] if c in row.keys() else ""
        val_str = str(val) if val is not None else ""
        if len(val_str) > max_col_width:
            val_str = val_str[:max_col_width] + "..."
        parts.append(f"  {c}: {val_str}")
    return "\n".join(parts)

def query_table(conn, table, where_clause, params, limit, label):
    if not table_exists(conn, table):
        return None, f"[SKIP] Table '{table}' does not exist.\n"
    cols = get_columns(conn, table)
    col_list = ", ".join(cols)
    sql = f"SELECT {col_list} FROM {table}"
    if where_clause:
        sql += f" WHERE {where_clause}"
    sql += f" LIMIT {limit}"
    try:
        cur = conn.execute(sql, params)
        rows = cur.fetchall()
    except Exception as e:
        return None, f"[ERROR] Table '{table}': {e}\n"
    lines = []
    lines.append(f"{'='*80}")
    lines.append(f"  {label}  (table: {table}, columns: {len(cols)}, rows returned: {len(rows)})")
    lines.append(f"  Columns: {', '.join(cols)}")
    lines.append(f"{'='*80}")
    if not rows:
        lines.append("  (no matching rows)")
    for i, row in enumerate(rows):
        lines.append(f"\n--- [{i+1}] ---")
        lines.append(fmt_row(row, cols))
    lines.append("")
    return len(rows), "\n".join(lines)

def main():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        return

    conn = get_connection()
    results = []
    summary = {}

    # --- 1. Harms (try extracted_harms first, then harms) ---
    harms_table = None
    for t in ["extracted_harms", "harms"]:
        if table_exists(conn, t):
            harms_table = t
            break

    if harms_table:
        cols = get_columns(conn, harms_table)
        # Build WHERE dynamically based on available text columns
        text_cols = [c for c in cols if any(k in c.lower() for k in ["description", "text", "content", "detail", "harm", "type", "category", "summary", "narrative", "finding"])]
        if not text_cols:
            text_cols = cols[:5]  # fallback: search first 5 cols
        conditions = []
        params = []
        keywords = ["%false report%", "%fabricat%", "%police%", "%alienat%", "%false alleg%"]
        for col in text_cols:
            for kw in keywords:
                conditions.append(f"{col} LIKE ?")
                params.append(kw)
        where = " OR ".join(conditions) if conditions else "1=1"
        count, text = query_table(conn, harms_table, where, params, 100, "HARMS / EXTRACTED HARMS")
        results.append(text)
        summary[harms_table] = count
    else:
        results.append("[SKIP] No harms or extracted_harms table found.\n")
        summary["harms"] = None

    # --- 2. Impeachment Items ---
    if table_exists(conn, "impeachment_items"):
        cols = get_columns(conn, "impeachment_items")
        text_cols = [c for c in cols if any(k in c.lower() for k in ["description", "text", "content", "detail", "type", "category", "summary", "finding", "statement", "source"])]
        if not text_cols:
            text_cols = cols[:5]
        conditions = []
        params = []
        keywords = ["%Watson%", "%police%", "%false%", "%alleg%", "%fabricat%"]
        for col in text_cols:
            for kw in keywords:
                conditions.append(f"{col} LIKE ?")
                params.append(kw)
        where = " OR ".join(conditions) if conditions else "1=1"
        count, text = query_table(conn, "impeachment_items", where, params, 100, "IMPEACHMENT ITEMS")
        results.append(text)
        summary["impeachment_items"] = count
    else:
        results.append("[SKIP] Table 'impeachment_items' not found.\n")
        summary["impeachment_items"] = None

    # --- 3. Contradictions ---
    if table_exists(conn, "contradictions"):
        cols = get_columns(conn, "contradictions")
        text_cols = [c for c in cols if any(k in c.lower() for k in ["description", "text", "content", "detail", "type", "summary", "statement", "finding", "claim"])]
        if not text_cols:
            text_cols = cols[:5]
        conditions = []
        params = []
        keywords = ["%Watson%", "%police%", "%custody%", "%false%", "%contradict%"]
        for col in text_cols:
            for kw in keywords:
                conditions.append(f"{col} LIKE ?")
                params.append(kw)
        where = " OR ".join(conditions) if conditions else "1=1"
        count, text = query_table(conn, "contradictions", where, params, 100, "CONTRADICTIONS")
        results.append(text)
        summary["contradictions"] = count
    else:
        results.append("[SKIP] Table 'contradictions' not found.\n")
        summary["contradictions"] = None

    # --- 4. Claims ---
    if table_exists(conn, "claims"):
        cols = get_columns(conn, "claims")
        # Look for supported/status column
        status_cols = [c for c in cols if any(k in c.lower() for k in ["status", "supported", "evidence", "linked"])]
        if status_cols:
            where = " OR ".join([f"{c} IS NOT NULL AND {c} != ''" for c in status_cols])
            count, text = query_table(conn, "claims", where, [], 50, "CLAIMS (with evidence links)")
        else:
            count, text = query_table(conn, "claims", None, [], 50, "CLAIMS (all)")
        results.append(text)
        summary["claims"] = count
    else:
        results.append("[SKIP] Table 'claims' not found.\n")
        summary["claims"] = None

    # --- 5. Evidence Quotes ---
    if table_exists(conn, "evidence_quotes"):
        cols = get_columns(conn, "evidence_quotes")
        text_cols = [c for c in cols if any(k in c.lower() for k in ["quote", "text", "content", "excerpt", "body", "passage", "description"])]
        if not text_cols:
            text_cols = cols[:5]
        conditions = []
        params = []
        keywords = ["%police%", "%fabricat%", "%suspend%", "%alienat%", "%ex parte%"]
        for col in text_cols:
            for kw in keywords:
                conditions.append(f"{col} LIKE ?")
                params.append(kw)
        where = " OR ".join(conditions) if conditions else "1=1"
        count, text = query_table(conn, "evidence_quotes", where, params, 100, "EVIDENCE QUOTES")
        results.append(text)
        summary["evidence_quotes"] = count
    else:
        results.append("[SKIP] Table 'evidence_quotes' not found.\n")
        summary["evidence_quotes"] = None

    # --- 6. Judicial Violations ---
    if table_exists(conn, "judicial_violations"):
        cols = get_columns(conn, "judicial_violations")
        text_cols = [c for c in cols if any(k in c.lower() for k in ["severity", "level", "priority", "judge", "description", "type", "violation"])]
        conditions = []
        params = []
        # Filter for critical + McNeill
        for col in text_cols:
            if any(k in col.lower() for k in ["severity", "level", "priority"]):
                conditions.append(f"({col} LIKE '%critical%' OR {col} LIKE '%high%')")
            if any(k in col.lower() for k in ["judge", "description", "violation", "type"]):
                conditions.append(f"{col} LIKE '%McNeill%'")
        where = " OR ".join(conditions) if conditions else "1=1"
        count, text = query_table(conn, "judicial_violations", where, [], 50, "JUDICIAL VIOLATIONS (Critical / McNeill)")
        results.append(text)
        summary["judicial_violations"] = count
    else:
        results.append("[SKIP] Table 'judicial_violations' not found.\n")
        summary["judicial_violations"] = None

    # --- TOTAL TABLE COUNTS ---
    results.append("\n" + "="*80)
    results.append("  TOTAL ROW COUNTS (full tables, no filter)")
    results.append("="*80)
    for tbl in ["extracted_harms", "harms", "impeachment_items", "contradictions", "claims", "evidence_quotes", "judicial_violations"]:
        if table_exists(conn, tbl):
            cur = conn.execute(f"SELECT COUNT(*) FROM {tbl}")
            total = cur.fetchone()[0]
            results.append(f"  {tbl}: {total:,} total rows")

    # --- SUMMARY ---
    results.append("\n" + "="*80)
    results.append("  EXTRACTION SUMMARY (filtered results)")
    results.append("="*80)
    for tbl, cnt in summary.items():
        if cnt is None:
            results.append(f"  {tbl}: TABLE NOT FOUND")
        else:
            results.append(f"  {tbl}: {cnt} matching rows extracted")
    results.append("="*80 + "\n")

    output = "\n".join(results)
    print(output)

    with open(OUTPUT_PATH, "w", encoding="utf-8", errors="replace") as f:
        f.write(output)
    print(f"\n[OK] Results written to {OUTPUT_PATH}")

    conn.close()

if __name__ == "__main__":
    main()
