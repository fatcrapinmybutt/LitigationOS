#!/usr/bin/env python3
"""
LitigationOS DB-RAG Bridge — SQL + FTS5 routing engine.

Routes natural language queries to the appropriate FTS5 indexes and SQL tables
in litigation_context.db, with optional LLM-powered NL→SQL translation.

Usage:
    python db_rag_bridge.py --search "ex parte order timeline"
    python db_rag_bridge.py --sql "How many filings were made in 2024?"
    python db_rag_bridge.py --hybrid "parental alienation evidence"
    python db_rag_bridge.py --tables
    python db_rag_bridge.py --schema apex_master_timeline
"""

import argparse
import json
import re
import sqlite3
import sys
import textwrap
import time
from pathlib import Path
from typing import Optional

import requests

# ── paths ────────────────────────────────────────────────────────────────────
DB_PATH = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")
OLLAMA_BASE = "http://localhost:11434"
LLM_MODEL = "qwen2.5:7b"
MAX_RESULTS = 25

# Topic → FTS index routing map
TOPIC_ROUTES: dict[str, list[str]] = {
    "timeline": ["master_timeline_fts", "condensed_timeline_fts", "prosecution_timeline_fts"],
    "evidence": ["evidence_quotes_fts", "canonical_facts_fts", "exhibit_registry_fts"],
    "alienation": ["psych_analysis_fts", "extracted_harms_fts", "adversary_assertions_fts"],
    "court": ["master_timeline_fts", "rules_text_fts", "auth_rules_fts"],
    "filing": ["master_csv_fts", "exhibit_registry_fts"],
    "violation": ["appclose_violations_fts", "constitutional_violations_fts", "auth_rules_fts"],
    "rebuttal": ["rebuttal_matrix_fts", "adversary_assertions_fts", "impeachment_index_fts"],
    "order": ["master_timeline_fts", "condensed_timeline_fts", "rules_text_fts"],
    "custody": ["psych_analysis_fts", "extracted_harms_fts", "master_timeline_fts"],
    "message": ["andrew_messages_fts", "appclose_messages_fts"],
    "authority": ["auth_passages_fts", "auth_rules_fts", "caselaw_unified_fts"],
    "caselaw": ["caselaw_unified_fts", "auth_passages_fts"],
    "harm": ["extracted_harms_fts", "psych_analysis_fts", "adversary_assertions_fts"],
    "impeach": ["impeachment_index_fts", "adversary_assertions_fts", "rebuttal_matrix_fts"],
    "document": ["md_sections_fts", "pages_fts", "ocr_text_fts"],
    "transcript": ["pages_fts", "md_sections_fts"],
    "contradiction": ["rebuttal_matrix_fts", "adversary_assertions_fts"],
    "ex parte": ["master_timeline_fts", "condensed_timeline_fts", "constitutional_violations_fts"],
}

# All available FTS5 indexes
ALL_FTS = [
    "adversary_assertions_fts", "andrew_messages_fts", "appclose_messages_fts",
    "appclose_violations_fts", "auth_passages_fts", "auth_rules_fts",
    "canonical_facts_fts", "case_intelligence_hub_fts", "caselaw_unified_fts",
    "condensed_timeline_fts", "constitutional_violations_fts",
    "evidence_quotes_fts", "exhibit_registry_fts", "extracted_harms_fts",
    "master_csv_fts", "master_timeline_fts", "md_sections_fts",
    "ocr_text_fts", "pages_fts", "prosecution_timeline_fts",
    "psych_analysis_fts", "rebuttal_matrix_fts", "rules_text_fts",
]


# ── database ─────────────────────────────────────────────────────────────────

class DBBridge:
    """SQL + FTS5 routing bridge for litigation_context.db."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path), timeout=30)
        self.conn.row_factory = sqlite3.Row
        self._table_cache: Optional[list[dict]] = None

    def close(self):
        self.conn.close()

    # ── table discovery ──────────────────────────────────────────────────

    def get_all_tables(self) -> list[dict]:
        """Return metadata for all tables in the database."""
        if self._table_cache is not None:
            return self._table_cache

        cur = self.conn.cursor()
        cur.execute(
            "SELECT name, type FROM sqlite_master "
            "WHERE type IN ('table', 'view') ORDER BY name"
        )
        tables = []
        for row in cur.fetchall():
            name = row[0]
            is_fts_shadow = any(
                name.endswith(s) for s in ("_fts_config", "_fts_data", "_fts_docsize", "_fts_idx")
            )
            if is_fts_shadow:
                continue

            is_fts = name.endswith("_fts")
            try:
                cur.execute(f"SELECT COUNT(*) FROM [{name}]")
                count = cur.fetchone()[0]
            except Exception:
                count = -1

            # Get columns
            try:
                cur.execute(f"PRAGMA table_info([{name}])")
                columns = [r[1] for r in cur.fetchall()]
            except Exception:
                columns = []

            tables.append({
                "name": name,
                "type": "fts5" if is_fts else row[1],
                "rows": count,
                "columns": columns,
            })

        self._table_cache = tables
        return tables

    def get_schema(self, table_name: str) -> dict:
        """Get detailed schema for a single table."""
        cur = self.conn.cursor()
        cur.execute(f"PRAGMA table_info([{table_name}])")
        columns = []
        for r in cur.fetchall():
            columns.append({
                "cid": r[0], "name": r[1], "type": r[2],
                "notnull": bool(r[3]), "pk": bool(r[5]),
            })

        try:
            cur.execute(f"SELECT COUNT(*) FROM [{table_name}]")
            row_count = cur.fetchone()[0]
        except Exception:
            row_count = -1

        # Sample rows
        sample = []
        try:
            cur.execute(f"SELECT * FROM [{table_name}] LIMIT 3")
            for row in cur.fetchall():
                sample.append(dict(row))
        except Exception:
            pass

        return {
            "name": table_name,
            "columns": columns,
            "row_count": row_count,
            "sample_rows": sample,
        }

    # ── FTS5 search ──────────────────────────────────────────────────────

    def _route_to_indexes(self, query: str) -> list[str]:
        """Determine which FTS indexes to search based on query topics."""
        query_lower = query.lower()
        targeted = set()

        for topic, indexes in TOPIC_ROUTES.items():
            if topic in query_lower:
                targeted.update(indexes)

        # If no topic match, search the most comprehensive indexes
        if not targeted:
            targeted = {
                "master_timeline_fts", "evidence_quotes_fts", "canonical_facts_fts",
                "case_intelligence_hub_fts", "md_sections_fts", "condensed_timeline_fts",
            }

        return list(targeted)

    def search(self, query: str, max_results: int = MAX_RESULTS) -> list[dict]:
        """Search relevant FTS5 indexes for the query."""
        indexes = self._route_to_indexes(query)

        # Build FTS5 query
        clean = re.sub(r'[^\w\s]', ' ', query)
        terms = clean.split()
        if not terms:
            return []
        fts_query = " OR ".join(terms)

        results = []
        for idx in indexes:
            try:
                cur = self.conn.cursor()
                cur.execute(
                    f"SELECT rowid, rank, * FROM [{idx}] "
                    f"WHERE [{idx}] MATCH ? ORDER BY rank LIMIT ?",
                    (fts_query, max_results),
                )
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]

                for row in rows:
                    row_dict = dict(zip(columns, row))
                    text_parts = []
                    for k, v in row_dict.items():
                        if k not in ("rowid", "rank") and v is not None and str(v).strip():
                            text_parts.append(f"{k}: {v}")

                    rank_val = row_dict.get("rank", 0)
                    score = 1.0 / (1.0 + abs(rank_val)) if rank_val else 0.5
                    base_table = idx.replace("_fts", "")

                    results.append({
                        "source": f"[SOURCE: {base_table}, row={row_dict.get('rowid', '?')}]",
                        "fts_index": idx,
                        "score": score,
                        "text": "\n".join(text_parts)[:3000],
                        "rowid": row_dict.get("rowid"),
                    })
            except Exception:
                continue

        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:max_results]

    # ── NL → SQL ─────────────────────────────────────────────────────────

    def sql_query(self, question: str) -> list[dict]:
        """Convert natural language to SQL via LLM, execute, return results."""
        # Gather schema context for the LLM
        tables = self.get_all_tables()
        # Pick top tables by relevance (largest data tables)
        data_tables = [t for t in tables if t["type"] == "table" and t["rows"] > 0]
        data_tables.sort(key=lambda t: t["rows"], reverse=True)
        schema_ctx = []
        for t in data_tables[:40]:
            cols = ", ".join(t["columns"][:15])
            schema_ctx.append(f"  {t['name']} ({t['rows']:,} rows): {cols}")

        schema_text = "\n".join(schema_ctx)

        prompt = textwrap.dedent(f"""\
            You are a SQL expert for a SQLite litigation database.
            Generate a single SELECT query to answer the user's question.
            Return ONLY the SQL query, no explanation.
            Use standard SQLite syntax. Limit results to 50 rows max.
            Do NOT modify data (no INSERT/UPDATE/DELETE/DROP).

            Available tables (name, row count, columns):
            {schema_text}

            Question: {question}

            SQL:
        """)

        try:
            resp = requests.post(
                f"{OLLAMA_BASE}/api/generate",
                json={
                    "model": LLM_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1, "num_ctx": 8192},
                },
                timeout=120,
            )
            resp.raise_for_status()
            raw = resp.json()["response"].strip()
        except Exception as e:
            return [{"error": f"LLM error: {e}"}]

        # Extract SQL from response
        sql = raw
        if "```" in sql:
            match = re.search(r"```(?:sql)?\s*(.*?)```", sql, re.DOTALL)
            if match:
                sql = match.group(1).strip()

        # Safety: only allow SELECT
        sql_upper = sql.upper().strip()
        if not sql_upper.startswith("SELECT"):
            return [{"error": f"Refused non-SELECT query: {sql[:100]}"}]

        # Execute
        try:
            cur = self.conn.cursor()
            cur.execute(sql)
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            results = [dict(zip(columns, row)) for row in rows]
            return [{"sql": sql, "columns": columns, "row_count": len(results), "rows": results}]
        except Exception as e:
            return [{"sql": sql, "error": f"SQL error: {e}"}]

    # ── hybrid ───────────────────────────────────────────────────────────

    def hybrid(self, query: str) -> dict:
        """Combine FTS5 search + NL→SQL for comprehensive results."""
        print("🔍 FTS5 search...")
        t0 = time.time()
        fts_results = self.search(query)
        fts_time = time.time() - t0

        print("🧠 NL→SQL translation...")
        t0 = time.time()
        sql_results = self.sql_query(query)
        sql_time = time.time() - t0

        return {
            "query": query,
            "fts_results": fts_results,
            "fts_count": len(fts_results),
            "fts_time": f"{fts_time:.2f}s",
            "sql_results": sql_results,
            "sql_time": f"{sql_time:.2f}s",
        }


# ── CLI ──────────────────────────────────────────────────────────────────────

def format_search_results(results: list[dict]):
    """Pretty-print search results."""
    if not results:
        print("  No results found.")
        return

    for i, r in enumerate(results, 1):
        print(f"\n{'─' * 50}")
        print(f"  #{i}  {r['source']}  (score: {r['score']:.4f})")
        print(f"  Index: {r['fts_index']}")
        # Truncate text for display
        text = r["text"][:500]
        for line in text.split("\n")[:6]:
            print(f"    {line}")
        if len(r["text"]) > 500:
            print("    ...")


def format_sql_results(results: list[dict]):
    """Pretty-print SQL results."""
    for block in results:
        if "error" in block:
            print(f"  ⚠ {block['error']}")
            if "sql" in block:
                print(f"  SQL: {block['sql']}")
            continue

        print(f"  SQL: {block['sql']}")
        print(f"  Rows returned: {block['row_count']}")
        if block["row_count"] > 0:
            # Column headers
            cols = block["columns"]
            print(f"  {'  '.join(c[:20].ljust(20) for c in cols[:8])}")
            print(f"  {'─' * min(len(cols) * 22, 160)}")
            for row in block["rows"][:20]:
                vals = [str(row.get(c, ""))[:20].ljust(20) for c in cols[:8]]
                print(f"  {'  '.join(vals)}")
            if block["row_count"] > 20:
                print(f"  ... ({block['row_count'] - 20} more rows)")


def cmd_tables(bridge: DBBridge):
    """List all searchable tables."""
    tables = bridge.get_all_tables()
    data_tables = [t for t in tables if t["type"] == "table"]
    fts_tables = [t for t in tables if t["type"] == "fts5"]

    print("=" * 70)
    print("LitigationOS DB-RAG Bridge — Table Inventory")
    print("=" * 70)
    print(f"\n  Total tables: {len(data_tables)}  |  FTS5 indexes: {len(fts_tables)}")
    print(f"  Database: {bridge.db_path}\n")

    # Data tables sorted by row count
    print("─" * 70)
    print(f"  {'TABLE NAME':<45} {'ROWS':>10}  {'COLUMNS':>7}")
    print("─" * 70)
    data_tables.sort(key=lambda t: t["rows"], reverse=True)
    for t in data_tables:
        rows_str = f"{t['rows']:,}" if t["rows"] >= 0 else "error"
        print(f"  {t['name']:<45} {rows_str:>10}  {len(t['columns']):>7}")

    print(f"\n{'─' * 70}")
    print("FTS5 INDEXES:")
    print("─" * 70)
    for t in fts_tables:
        rows_str = f"{t['rows']:,}" if t["rows"] >= 0 else "error"
        base = t["name"].replace("_fts", "")
        print(f"  {t['name']:<45} {rows_str:>10}  (base: {base})")


def cmd_search(bridge: DBBridge, query: str):
    """Run FTS5 search."""
    print(f"\n{'=' * 60}")
    print(f"FTS5 Search: {query}")
    print("=" * 60)

    routed = bridge._route_to_indexes(query)
    print(f"  Routed to indexes: {', '.join(routed)}")

    t0 = time.time()
    results = bridge.search(query)
    elapsed = time.time() - t0

    print(f"  Found {len(results)} results in {elapsed:.2f}s")
    format_search_results(results)


def cmd_sql(bridge: DBBridge, question: str):
    """Run NL→SQL query."""
    print(f"\n{'=' * 60}")
    print(f"NL→SQL: {question}")
    print("=" * 60)

    t0 = time.time()
    results = bridge.sql_query(question)
    elapsed = time.time() - t0

    print(f"  Completed in {elapsed:.2f}s\n")
    format_sql_results(results)


def cmd_hybrid(bridge: DBBridge, query: str):
    """Run hybrid FTS5 + SQL query."""
    print(f"\n{'=' * 60}")
    print(f"Hybrid Query: {query}")
    print("=" * 60)

    result = bridge.hybrid(query)

    print(f"\n── FTS5 Results ({result['fts_count']}) [{result['fts_time']}] ──")
    format_search_results(result["fts_results"])

    print(f"\n── SQL Results [{result['sql_time']}] ──")
    format_sql_results(result["sql_results"])


def cmd_schema(bridge: DBBridge, table_name: str):
    """Show detailed schema for a table."""
    schema = bridge.get_schema(table_name)
    print(f"\n{'=' * 60}")
    print(f"Schema: {schema['name']}  ({schema['row_count']:,} rows)")
    print("=" * 60)

    print(f"\n  {'COLUMN':<30} {'TYPE':<15} {'PK':>3}  {'NOT NULL':>8}")
    print(f"  {'─' * 60}")
    for col in schema["columns"]:
        print(
            f"  {col['name']:<30} {col['type'] or 'ANY':<15} "
            f"{'✓' if col['pk'] else '':>3}  {'✓' if col['notnull'] else '':>8}"
        )

    if schema["sample_rows"]:
        print(f"\n  Sample rows:")
        for row in schema["sample_rows"]:
            truncated = {k: str(v)[:60] for k, v in row.items()}
            print(f"    {json.dumps(truncated, ensure_ascii=False)}")


def main():
    parser = argparse.ArgumentParser(
        description="LitigationOS DB-RAG Bridge — SQL + FTS5 routing engine"
    )
    parser.add_argument("--search", type=str, help="FTS5 search across relevant indexes")
    parser.add_argument("--sql", type=str, help="Natural language → SQL query")
    parser.add_argument("--hybrid", type=str, help="Combined FTS5 + SQL search")
    parser.add_argument("--tables", action="store_true", help="List all searchable tables")
    parser.add_argument("--schema", type=str, help="Show schema for a specific table")

    args = parser.parse_args()
    bridge = DBBridge()

    try:
        if args.search:
            cmd_search(bridge, args.search)
        elif args.sql:
            cmd_sql(bridge, args.sql)
        elif args.hybrid:
            cmd_hybrid(bridge, args.hybrid)
        elif args.tables:
            cmd_tables(bridge)
        elif args.schema:
            cmd_schema(bridge, args.schema)
        else:
            parser.print_help()
    finally:
        bridge.close()


if __name__ == "__main__":
    main()
