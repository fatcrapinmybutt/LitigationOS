"""
quick_query.py — Quick Legal Research Query Tool
=================================================
LitigationOS 2026 v1.0 — Pigors v. Watson

Fast topic search across authority, evidence, and citations.
Returns top 5 results from auth_rules_fts, evidence_quotes_fts,
and master_citations.

Usage:
    python quick_query.py "parental alienation"
    python quick_query.py "MCR 2.003"
    python quick_query.py "custody best interest"
    python quick_query.py --all "due process"     (show more results)

No network calls. Pure SQLite FTS5.
"""

import sqlite3
import sys
import os
import textwrap
from typing import List, Dict, Any, Optional

DB_PATH = r"C:\Users\andre\litigation_context.db"
DEFAULT_LIMIT = 5


def get_connection() -> sqlite3.Connection:
    """Open DB with WAL mode and timeout protection."""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
    except Exception:
        pass
    return conn


def _truncate(text: str, max_len: int = 200) -> str:
    """Truncate text to max_len with ellipsis."""
    if not text:
        return "(empty)"
    text = " ".join(text.split())  # collapse whitespace
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    """Check if a table exists in the DB."""
    cur = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    )
    return cur.fetchone() is not None


def search_auth_rules(conn: sqlite3.Connection, topic: str, limit: int) -> List[Dict]:
    """Search auth_rules via FTS5 index."""
    results = []
    try:
        if not _table_exists(conn, "auth_rules_fts"):
            return [{"error": "auth_rules_fts table not found"}]
        # FTS5 MATCH query — escape double quotes in topic
        safe_topic = topic.replace('"', '""')
        cur = conn.execute(
            """SELECT rule_number, title, substr(full_text, 1, 300) as excerpt
               FROM auth_rules
               WHERE rowid IN (
                   SELECT rowid FROM auth_rules_fts WHERE auth_rules_fts MATCH ?
               )
               LIMIT ?""",
            (safe_topic, limit),
        )
        for row in cur.fetchall():
            results.append({
                "rule": row["rule_number"],
                "title": row["title"],
                "excerpt": _truncate(row["excerpt"], 250),
            })
    except Exception as e:
        results.append({"error": f"auth_rules search failed: {e}"})
    return results


def search_evidence_quotes(conn: sqlite3.Connection, topic: str, limit: int) -> List[Dict]:
    """Search evidence_quotes via FTS5 index."""
    results = []
    try:
        if not _table_exists(conn, "evidence_quotes_fts"):
            return [{"error": "evidence_quotes_fts table not found"}]
        safe_topic = topic.replace('"', '""')
        cur = conn.execute(
            """SELECT quote_text, speaker, evidence_category, legal_significance
               FROM evidence_quotes
               WHERE rowid IN (
                   SELECT rowid FROM evidence_quotes_fts WHERE evidence_quotes_fts MATCH ?
               )
               LIMIT ?""",
            (safe_topic, limit),
        )
        for row in cur.fetchall():
            results.append({
                "quote": _truncate(row["quote_text"], 200),
                "speaker": row["speaker"],
                "category": row["evidence_category"],
                "significance": _truncate(str(row["legal_significance"] or ""), 120),
            })
    except Exception as e:
        results.append({"error": f"evidence_quotes search failed: {e}"})
    return results


def search_master_citations(conn: sqlite3.Connection, topic: str, limit: int) -> List[Dict]:
    """Search master_citations with LIKE fallback (no dedicated FTS)."""
    results = []
    try:
        if not _table_exists(conn, "master_citations"):
            return [{"error": "master_citations table not found"}]
        # Try LIKE search on citation and context columns
        like_pattern = f"%{topic}%"
        cur = conn.execute(
            """SELECT citation, cite_type, substr(context, 1, 250) as context,
                      source_file
               FROM master_citations
               WHERE citation LIKE ? OR context LIKE ?
               LIMIT ?""",
            (like_pattern, like_pattern, limit),
        )
        for row in cur.fetchall():
            results.append({
                "citation": row["citation"],
                "type": row["cite_type"],
                "context": _truncate(row["context"], 200),
                "source": os.path.basename(str(row["source_file"] or "")),
            })
    except Exception as e:
        results.append({"error": f"master_citations search failed: {e}"})
    return results


def print_section(title: str, results: List[Dict], fields: List[str]) -> None:
    """Print a formatted results section."""
    print(f"\n{'─' * 60}")
    print(f"  {title}  ({len(results)} result{'s' if len(results) != 1 else ''})")
    print(f"{'─' * 60}")
    if not results:
        print("  (no results)")
        return
    for i, row in enumerate(results, 1):
        if "error" in row:
            print(f"  ERROR: {row['error']}")
            continue
        print(f"  [{i}]")
        for field in fields:
            if field in row and row[field]:
                label = field.upper().replace("_", " ")
                # Indent wrapped text
                value = str(row[field])
                wrapped = textwrap.fill(value, width=70, subsequent_indent="        ")
                print(f"      {label}: {wrapped}")
        print()


def run_query(topic: str, limit: int = DEFAULT_LIMIT) -> None:
    """Run topic search across all three tables."""
    print("=" * 60)
    print(f"  LitigationOS Quick Query")
    print(f"  Topic: \"{topic}\"")
    print(f"  Limit: {limit} per source")
    print("=" * 60)

    try:
        conn = get_connection()
    except Exception as e:
        print(f"\n  FATAL: Cannot connect to database: {e}")
        sys.exit(1)

    try:
        # Search all three sources
        auth_results = search_auth_rules(conn, topic, limit)
        evidence_results = search_evidence_quotes(conn, topic, limit)
        citation_results = search_master_citations(conn, topic, limit)

        # Print results
        print_section(
            "AUTHORITY RULES (auth_rules_fts)",
            auth_results,
            ["rule", "title", "excerpt"],
        )
        print_section(
            "EVIDENCE QUOTES (evidence_quotes_fts)",
            evidence_results,
            ["speaker", "category", "quote", "significance"],
        )
        print_section(
            "MASTER CITATIONS (master_citations)",
            citation_results,
            ["citation", "type", "context", "source"],
        )

        # Summary
        total = len(auth_results) + len(evidence_results) + len(citation_results)
        errors = sum(
            1 for r in auth_results + evidence_results + citation_results
            if "error" in r
        )
        print(f"\n{'─' * 60}")
        print(f"  TOTAL: {total} results across 3 sources", end="")
        if errors:
            print(f" ({errors} errors)")
        else:
            print()
        print()
    except Exception as e:
        print(f"\n  ERROR during search: {e}")
    finally:
        try:
            conn.close()
        except Exception:
            pass


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    # Parse args
    limit = DEFAULT_LIMIT
    args = sys.argv[1:]
    if args[0] == "--all":
        limit = 20
        args = args[1:]

    if not args:
        print("Error: No topic provided.")
        print("Usage: python quick_query.py \"search topic\"")
        sys.exit(1)

    topic = " ".join(args)
    run_query(topic, limit)


if __name__ == "__main__":
    main()
