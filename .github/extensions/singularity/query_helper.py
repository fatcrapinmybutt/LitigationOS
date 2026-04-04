#!/usr/bin/env python3
"""Secure query helper for litigation-db Copilot extension.

Reads a JSON request from stdin, executes parameterized SQLite queries
against litigation_context.db, and writes JSON results to stdout.

Supported actions:
  - query:      Execute parameterized SQL (? placeholders)
  - fts_search: FTS5 search with table allowlist
  - stats:      Row counts for key tables
"""
import sqlite3
import json
import sys

# ── Shared module integration ──────────────────────────────────────────────
try:
    from pathlib import Path as _Path
    sys.path.insert(0, str(_Path(__file__).resolve().parents[2] / "00_SYSTEM"))
    from shared import get_db as _shared_get_db  # noqa: F401
    _HAS_SHARED = True
except ImportError:
    _HAS_SHARED = False

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

# ── FTS5 table configuration ──────────────────────────────────────────────
ALLOWED_FTS = {
    "evidence_fts": {
        "join": "evidence_quotes eq ON eq.id = evidence_fts.rowid",
        "snippet_col": 0,  # quote_text
        "extra_cols": [
            "eq.source_file",
            "eq.category",
            "eq.lane",
            "eq.relevance_score",
        ],
    },
    "timeline_fts": {
        "join": None,
        "snippet_col": 0,  # description
        "extra_cols": ["actors"],
    },
}

# ── LIKE-fallback table configuration ─────────────────────────────────────
ALLOWED_LIKE = {
    "police_reports": {
        "text_col": "full_text",
        "cols": ["filename", "allegations", "exculpatory", "false_reports"],
    },
    "michigan_rules_extracted": {
        "text_col": "full_text",
        "cols": ["rule_number", "rule_type", "title"],
    },
}

# ── Tables included in the stats action ───────────────────────────────────
STATS_TABLES = [
    "evidence_quotes",
    "timeline_events",
    "police_reports",
    "michigan_rules_extracted",
    "impeachment_matrix",
    "authority_chains_v2",
    "contradiction_map",
    "deadlines",
    "filing_packages",
    "master_evidence_timeline",
]


def _rows_to_dicts(cursor, max_rows):
    """Fetch up to *max_rows* rows and return (cols, row_dicts, extra_count)."""
    cols = [d[0] for d in cursor.description] if cursor.description else []
    rows = []
    for r in cursor.fetchmany(max_rows):
        row = dict(r)
        # Truncate individual cell values to prevent massive JSON output
        for k, v in row.items():
            if isinstance(v, str) and len(v) > 5000:
                row[k] = v[:5000] + "...[truncated]"
        rows.append(row)
    count = len(rows)
    extra = 0
    if count == max_rows:
        # Count remaining without loading full rows into memory
        remaining = cursor.fetchmany(10000)
        extra = len(remaining)
        if extra == 10000:
            # More than 10K extra — just report ">10000"
            extra = 10000
    return cols, rows, count, extra


def handle_query(conn, request, max_rows):
    sql = request["sql"]
    params = request.get("params", [])
    cur = conn.execute(sql, params)
    cols, rows, count, extra = _rows_to_dicts(cur, max_rows)
    result = {"columns": cols, "rows": rows, "count": count}
    if extra:
        result["truncated"] = extra
    return result


def handle_fts_search(conn, request, max_rows):
    table = request["table"]
    query_text = request["query"]

    if table in ALLOWED_FTS:
        cfg = ALLOWED_FTS[table]
        extra_cols = ", ".join(cfg["extra_cols"])
        snippet = (
            f"snippet({table}, {cfg['snippet_col']}, "
            "'>>>', '<<<', '...', 64)"
        )
        if cfg["join"]:
            sql = (
                f"SELECT {extra_cols}, {snippet} AS excerpt, {table}.rank "
                f"FROM {table} "
                f"JOIN {cfg['join']} "
                f"WHERE {table} MATCH ? "
                f"ORDER BY {table}.rank LIMIT ?"
            )
        else:
            sql = (
                f"SELECT {extra_cols}, {snippet} AS excerpt, {table}.rank "
                f"FROM {table} "
                f"WHERE {table} MATCH ? "
                f"ORDER BY {table}.rank LIMIT ?"
            )
        cur = conn.execute(sql, [query_text, max_rows])

    elif table in ALLOWED_LIKE:
        cfg = ALLOWED_LIKE[table]
        col_str = ", ".join(cfg["cols"])
        text_col = cfg["text_col"]
        terms = [t for t in query_text.split() if len(t) >= 2]
        if not terms:
            return {"columns": [], "rows": [], "count": 0}
        conditions = " AND ".join(f"{text_col} LIKE ?" for _ in terms)
        params = [f"%{t}%" for t in terms]
        params.append(max_rows)
        sql = (
            f"SELECT {col_str}, substr({text_col}, 1, 300) AS excerpt "
            f"FROM {table} WHERE {conditions} LIMIT ?"
        )
        cur = conn.execute(sql, params)

    else:
        return {"error": f"Table not in allowlist: {table}"}

    cols, rows, count, _ = _rows_to_dicts(cur, max_rows)
    return {"columns": cols, "rows": rows, "count": count}


def handle_stats(conn):
    stats = {}
    for tbl in STATS_TABLES:
        try:
            cnt = conn.execute(f"SELECT COUNT(*) FROM [{tbl}]").fetchone()[0]
            stats[tbl] = cnt
        except Exception:
            stats[tbl] = "N/A"
    return {"stats": stats}


def main():
    raw = sys.stdin.read()
    if not raw.strip():
        print(json.dumps({"error": "Empty request"}))
        return

    try:
        request = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(json.dumps({"error": f"Invalid JSON: {str(exc)[:200]}"}))
        return

    action = request.get("action", "query")
    db_path = request.get("db_path", DB_PATH)
    max_rows = min(request.get("max_rows", 50), 500)

    try:
        if _HAS_SHARED and db_path == DB_PATH:
            conn = _shared_get_db("litigation")
        else:
            conn = sqlite3.connect(db_path, timeout=10)
            conn.row_factory = sqlite3.Row

        if action == "query":
            result = handle_query(conn, request, max_rows)
        elif action == "fts_search":
            result = handle_fts_search(conn, request, max_rows)
        elif action == "stats":
            result = handle_stats(conn)
        else:
            result = {"error": f"Unknown action: {action}"}

        conn.close()
        output = json.dumps(result, default=str)
        # Cap output to 5 MB to prevent Node.js RangeError
        if len(output) > 5 * 1024 * 1024:
            # Re-serialize with truncated rows
            if isinstance(result, dict) and "rows" in result:
                result["rows"] = result["rows"][:50]
                result["truncated_by_size"] = True
                output = json.dumps(result, default=str)
            else:
                output = json.dumps({"error": f"Result too large ({len(output)} bytes). Narrow your query."})
        print(output)

    except Exception as exc:
        print(json.dumps({"error": str(exc)[:300]}))


if __name__ == "__main__":
    main()
