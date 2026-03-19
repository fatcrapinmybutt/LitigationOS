#!/usr/bin/env python3
"""
MBP LitigationOS — Enhanced Query Engine
=========================================
Multi-table FTS5 search across the litigation database with relevance scoring,
source attribution, and query expansion.

Searches across:
  - auth_rules_fts     (weight: 1.5) — Michigan court rules
  - evidence_quotes_fts (weight: 2.0) — Evidence quotes
  - pages_fts          (weight: 0.8) — Raw page text
  - md_sections_fts    (weight: 1.0) — Markdown sections
  - master_csv_fts     (weight: 0.7) — CSV data
  - rules_text_fts     (weight: 1.2) — Rules text

Usage:
    python enhanced_query.py "parental alienation"
    python enhanced_query.py "MCR 2.003 disqualification" --tables auth,rules --limit 10
    python enhanced_query.py "custody best interest" --expand --format json

Example:
    python enhanced_query.py "what evidence shows alienation?" --expand --limit 20
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from cycle_method import cycle_json, cycle_print
except ImportError:
    cycle_json = lambda obj, **kw: print(json.dumps(obj, default=str))
    cycle_print = print

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\litigation_context.db",
)

# ── Table configurations ────────────────────────────────────────────
TABLE_CONFIGS = {
    "auth": {
        "fts_table": "auth_rules_fts",
        "base_table": "auth_rules",
        "weight": 1.5,
        "display_cols": ["rule_number", "title", "full_text"],
        "id_col": "rowid",
        "label": "Michigan Court Rules",
    },
    "evidence": {
        "fts_table": "evidence_quotes_fts",
        "base_table": "evidence_quotes",
        "weight": 2.0,
        "display_cols": ["quote_text", "speaker", "evidence_category", "legal_significance"],
        "id_col": "rowid",
        "label": "Evidence Quotes",
    },
    "pages": {
        "fts_table": "pages_fts",
        "base_table": "pages",
        "weight": 0.8,
        "display_cols": ["text_content"],
        "id_col": "rowid",
        "label": "Document Pages",
    },
    "sections": {
        "fts_table": "md_sections_fts",
        "base_table": "md_sections",
        "weight": 1.0,
        "display_cols": ["section_title", "content", "source_file"],
        "id_col": "rowid",
        "label": "Document Sections",
    },
    "csv": {
        "fts_table": "master_csv_fts",
        "base_table": "master_csv_data",
        "weight": 0.7,
        "display_cols": ["*"],
        "id_col": "rowid",
        "label": "CSV Data",
    },
    "rules": {
        "fts_table": "rules_text_fts",
        "base_table": "rules_text",
        "weight": 1.2,
        "display_cols": ["rule", "chapter", "context"],
        "id_col": "rowid",
        "label": "Rules Text",
    },
}

# ── Query expansion synonyms (Michigan legal domain) ────────────────
QUERY_EXPANSIONS = {
    "custody": ["custody", "parenting", "child", "best interest", "custodial environment"],
    "alienation": ["alienation", "parental alienation", "factor j", "mcl 722.23", "facilitate relationship"],
    "disqualification": ["disqualification", "recusal", "bias", "prejudice", "mcr 2.003"],
    "contempt": ["contempt", "violation", "non-compliance", "disobey", "sanctions"],
    "discovery": ["discovery", "interrogatories", "deposition", "subpoena", "production", "compel"],
    "ppo": ["ppo", "personal protection", "protective order", "restraining", "mcl 600.2950"],
    "appeal": ["appeal", "appellate", "claim of appeal", "mcr 7.204", "court of appeals"],
    "motion": ["motion", "relief", "requested", "pursuant", "mcr 2.119"],
    "evidence": ["evidence", "exhibit", "testimony", "admissible", "mre"],
    "hearing": ["hearing", "evidentiary", "oral argument", "conference"],
    "service": ["service", "served", "process", "mcr 2.105", "proof of service"],
    "due process": ["due process", "fourteenth amendment", "fundamental right", "constitutional"],
    "best interest": ["best interest", "mcl 722.23", "factor", "child welfare"],
    "parenting time": ["parenting time", "visitation", "mcl 722.27a", "schedule"],
    "foc": ["friend of court", "foc", "recommendation", "mcl 552.501"],
    "fraud": ["fraud", "misrepresentation", "perjury", "false statement"],
}


def expand_query(query: str) -> str:
    """Expand query with domain-specific synonyms for better FTS recall."""
    words = query.lower().split()
    expanded_terms = set(words)

    for word in words:
        if word in QUERY_EXPANSIONS:
            expanded_terms.update(QUERY_EXPANSIONS[word])
        # Also check two-word phrases
        for i, w in enumerate(words[:-1]):
            phrase = f"{w} {words[i+1]}"
            if phrase in QUERY_EXPANSIONS:
                expanded_terms.update(QUERY_EXPANSIONS[phrase])

    return " OR ".join(f'"{t}"' if " " in t else t for t in expanded_terms)


def _safe_text(val: Any, max_len: int = 500) -> str:
    """Safely convert DB value to truncated string."""
    if val is None:
        return ""
    try:
        s = str(val).strip()
    except Exception:
        s = str(val).encode("utf-8", errors="replace").decode("utf-8", errors="replace").strip()
    return s[:max_len] if len(s) > max_len else s


# ── Enhanced Query Engine ───────────────────────────────────────────
class EnhancedQueryEngine:
    """Multi-table FTS5 search with relevance scoring and source attribution."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def _get_db(self) -> sqlite3.Connection:
        if self._conn is not None:
            try:
                self._conn.execute("SELECT 1")
                return self._conn
            except Exception:
                self._conn = None

        self._conn = sqlite3.connect(self.db_path, timeout=30)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA cache_size=-65536")
        self._conn.execute("PRAGMA query_only=ON")
        return self._conn

    def _sanitize_fts_query(self, query: str) -> str:
        """Sanitize query for FTS5 MATCH syntax."""
        # Remove characters that break FTS5
        sanitized = re.sub(r'[^\w\s".|*OR AND NOT]', ' ', query)
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        return sanitized if sanitized else query

    def _search_table(
        self,
        table_key: str,
        fts_query: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Search a single FTS5 table and return scored results."""
        config = TABLE_CONFIGS.get(table_key)
        if not config:
            return []

        conn = self._get_db()
        results = []
        fts_table = config["fts_table"]
        weight = config["weight"]

        try:
            # FTS5 MATCH query with rank
            sql = f"""
                SELECT rowid, rank, *
                FROM [{fts_table}]
                WHERE [{fts_table}] MATCH ?
                ORDER BY rank
                LIMIT ?
            """
            rows = conn.execute(sql, (fts_query, limit)).fetchall()

            col_names = [desc[0] for desc in conn.execute(f"PRAGMA table_info([{fts_table}])").fetchall()]
            fts_col_names = ["rowid", "rank"] + [c[1] for c in conn.execute(f"PRAGMA table_info([{fts_table}])").fetchall()]

            for row in rows:
                # rank is negative in FTS5 (more negative = better match)
                raw_rank = abs(row[1]) if row[1] else 1.0
                score = (1.0 / (raw_rank + 0.001)) * weight

                # Build result dict from available columns
                row_data = {}
                for i, val in enumerate(row):
                    if i == 0:
                        row_data["rowid"] = val
                    elif i == 1:
                        row_data["raw_rank"] = val
                    else:
                        row_data[f"col_{i-2}"] = _safe_text(val)

                results.append({
                    "source_table": table_key,
                    "source_label": config["label"],
                    "rowid": row[0],
                    "score": round(score, 4),
                    "weight": weight,
                    "data": row_data,
                    "snippet": _safe_text(str(row[2]) if len(row) > 2 else "", max_len=300),
                })

        except Exception as e:
            # Table might not exist or query syntax issue — graceful fallback
            if "no such table" not in str(e).lower():
                print(f"  [WARN] Search failed on {fts_table}: {e}")

        return results

    def search(
        self,
        query: str,
        tables: Optional[List[str]] = None,
        limit: int = 20,
        expand: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute multi-table search with relevance scoring.

        Args:
            query: Search query text
            tables: List of table keys to search (default: all)
            limit: Max results per table
            expand: Whether to expand query with synonyms

        Returns:
            {query, expanded_query, results, sources, total_results}
        """
        start_time = time.time()

        # Query expansion
        if expand:
            fts_query = expand_query(query)
        else:
            fts_query = query

        fts_query = self._sanitize_fts_query(fts_query)

        # Determine tables to search
        active_tables = tables if tables else list(TABLE_CONFIGS.keys())

        # Search each table
        all_results = []
        source_counts = {}

        for table_key in active_tables:
            if table_key not in TABLE_CONFIGS:
                print(f"  [WARN] Unknown table key: {table_key}")
                continue

            results = self._search_table(table_key, fts_query, limit=limit)
            source_counts[table_key] = len(results)
            all_results.extend(results)

        # Sort by score (descending)
        all_results.sort(key=lambda x: x["score"], reverse=True)

        # Trim to overall limit
        all_results = all_results[:limit]

        elapsed = time.time() - start_time

        return {
            "query": query,
            "expanded_query": fts_query if expand else None,
            "total_results": len(all_results),
            "source_counts": source_counts,
            "elapsed_seconds": round(elapsed, 3),
            "results": all_results,
        }

    def close(self) -> None:
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None


def _print_results(report: Dict[str, Any], format_type: str = "text") -> None:
    """Print search results in requested format."""
    if format_type == "json":
        cycle_json(report)
        return

    print(f"\n{'='*60}")
    print(f"ENHANCED QUERY RESULTS")
    print(f"{'='*60}")
    print(f"  Query:    {report['query']}")
    if report.get("expanded_query"):
        print(f"  Expanded: {report['expanded_query'][:100]}...")
    print(f"  Results:  {report['total_results']}")
    print(f"  Time:     {report['elapsed_seconds']}s")
    print(f"  Sources:  {report['source_counts']}")
    print(f"{'─'*60}")

    for i, r in enumerate(report.get("results", []), 1):
        print(f"\n  [{i}] Score: {r['score']:.4f}  Source: {r['source_label']}")
        snippet = r.get("snippet", "")
        if snippet:
            # Clean and truncate
            snippet = snippet.replace("\n", " ")[:200]
            print(f"      {snippet}")

    print(f"\n{'='*60}")


# ── CLI ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Enhanced multi-table FTS5 query engine for LitigationOS"
    )
    parser.add_argument("query", type=str, help="Search query")
    parser.add_argument("--tables", type=str, default="",
                        help="Comma-separated table keys: auth,evidence,pages,sections,csv,rules")
    parser.add_argument("--limit", type=int, default=20, help="Max results (default: 20)")
    parser.add_argument("--expand", action="store_true", help="Enable query expansion")
    parser.add_argument("--format", type=str, default="text",
                        choices=["text", "json"], help="Output format")

    args = parser.parse_args()
    tables = [t.strip() for t in args.tables.split(",") if t.strip()] or None

    engine = EnhancedQueryEngine()
    try:
        report = engine.search(
            query=args.query,
            tables=tables,
            limit=args.limit,
            expand=args.expand,
        )
        _print_results(report, format_type=args.format)
    finally:
        engine.close()
