#!/usr/bin/env python3
"""
DuckDB Analytical Sidecar for LitigationOS
===========================================
Routes heavy analytical queries (COUNT, GROUP BY, aggregates) through
DuckDB's columnar engine while falling back to SQLite for FTS5 and
unsupported features.

Usage:
    from duckdb_sidecar import sidecar   # lazy singleton
    n = sidecar.count("master_citations")
    rows = sidecar.group_count("evidence_quotes", "evidence_category")

CLI:
    python duckdb_sidecar.py benchmark
"""
from __future__ import annotations

import os
import re
import sys
import time
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, List, Optional, Tuple

# ── UTF-8 stdout (non-negotiable LitigationOS rule) ────────────────────────
sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")
sys.stderr = open(sys.stderr.fileno(), mode="w", encoding="utf-8", errors="replace")

# ── Constants ───────────────────────────────────────────────────────────────
_DB_PATH = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")
# DuckDB ATTACH requires forward slashes
_DB_PATH_FWD = str(_DB_PATH).replace("\\", "/")

# Patterns that benefit from DuckDB's columnar engine
_ANALYTICAL_PATTERNS = re.compile(
    r"""
    \bCOUNT\s*\(               |
    \bSUM\s*\(                  |
    \bAVG\s*\(                  |
    \bMIN\s*\(                  |
    \bMAX\s*\(                  |
    \bGROUP\s+BY\b             |
    \bHAVING\b                  |
    \bORDER\s+BY\b.*\bLIMIT\b
    """,
    re.IGNORECASE | re.VERBOSE | re.DOTALL,
)

# Patterns that MUST stay on SQLite (DuckDB lacks FTS5)
_FTS5_PATTERN = re.compile(r"\bMATCH\b|\bsearch_index\b|\bfts\b", re.IGNORECASE)


class DuckDBSidecar:
    """Thread-safe singleton that routes analytical queries through DuckDB.

    Two execution tiers:
      1. **Cached (native columnar)** — hot tables materialized into DuckDB's
         native format via CREATE TABLE AS SELECT. This is where the real
         speedup lives (10-100× over SQLite for aggregates).
      2. **Bridge (SQLite attach)** — for ad-hoc queries on any table. Slower
         than native SQLite on simple COUNT(*) due to scanner overhead, but
         useful for complex analytics.

    Tables are cached lazily on first query against them.
    """

    _instance: Optional["DuckDBSidecar"] = None
    _init_lock = threading.Lock()

    # Tables to auto-cache when first queried (high-value analytical targets)
    HOT_TABLES = frozenset({
        "master_citations",
        "evidence_quotes",
        "omega_filesystem_map",
        "pages",
    })

    def __new__(cls) -> "DuckDBSidecar":
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    obj = super().__new__(cls)
                    obj._initialized = False
                    cls._instance = obj
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._lock = threading.Lock()
        self._duck_conn = None  # lazy — created on first use
        self._attached = False
        self._cached_tables: set[str] = set()  # tables in native DuckDB format
        self._initialized = True

    # ── Lazy attach ─────────────────────────────────────────────────────

    def _ensure_attached(self) -> None:
        """Attach SQLite DB to DuckDB on first use (lazy init)."""
        if self._attached and self._duck_conn is not None:
            return
        with self._lock:
            if self._attached and self._duck_conn is not None:
                return
            import duckdb

            if not _DB_PATH.exists():
                raise FileNotFoundError(f"Database not found: {_DB_PATH}")

            conn = duckdb.connect(database=":memory:")
            conn.execute("INSTALL sqlite; LOAD sqlite;")
            conn.execute(
                f"ATTACH '{_DB_PATH_FWD}' AS lit (TYPE sqlite, READ_ONLY)"
            )
            self._duck_conn = conn
            self._attached = True

    # ── Columnar cache ──────────────────────────────────────────────────

    def cache_table(self, table: str) -> None:
        """Materialize a SQLite table into DuckDB's native columnar format.

        Copies the full table into an in-memory DuckDB table named
        `cached_{table}`. Subsequent queries against this table are rewritten
        to hit the cached version.
        """
        self._ensure_attached()
        if table in self._cached_tables:
            return
        with self._lock:
            if table in self._cached_tables:
                return
            cached_name = f"cached_{table}"
            self._duck_conn.execute(
                f"CREATE OR REPLACE TABLE {cached_name} AS "
                f"SELECT * FROM lit.{table}"
            )
            self._cached_tables.add(table)

    def _maybe_cache_hot_table(self, sql: str) -> None:
        """Auto-cache hot tables on first query against them."""
        sql_lower = sql.lower()
        for tbl in self.HOT_TABLES:
            if tbl in sql_lower and tbl not in self._cached_tables:
                try:
                    self.cache_table(tbl)
                except Exception:
                    pass  # fallback to bridge if caching fails

    def _rewrite_to_cached(self, sql: str) -> str:
        """Rewrite table references to use cached_ variants where available."""
        result = sql
        for tbl in self._cached_tables:
            # Replace lit.<table> with cached_<table>
            result = re.sub(
                rf"\blit\.{re.escape(tbl)}\b",
                f"cached_{tbl}",
                result,
                flags=re.IGNORECASE,
            )
            # Replace bare <table> references (after FROM/JOIN)
            result = re.sub(
                rf"(?<=FROM\s){re.escape(tbl)}\b",
                f"cached_{tbl}",
                result,
                flags=re.IGNORECASE,
            )
            result = re.sub(
                rf"(?<=JOIN\s){re.escape(tbl)}\b",
                f"cached_{tbl}",
                result,
                flags=re.IGNORECASE,
            )
        return result

    # ── Core execution ──────────────────────────────────────────────────

    def execute_analytical(
        self, sql: str, params: Optional[tuple] = None
    ) -> List[Any]:
        """Execute an analytical query through DuckDB with SQLite fallback.

        Execution order:
          1. FTS5 detected → SQLite immediately
          2. Hot table in cache → DuckDB native columnar (fastest)
          3. Any other table → DuckDB SQLite bridge
          4. DuckDB error → SQLite fallback
        """
        if _FTS5_PATTERN.search(sql):
            return self._fallback_sqlite(sql, params)

        try:
            self._ensure_attached()
            # Auto-cache hot tables on first access
            self._maybe_cache_hot_table(sql)
            # Qualify bare table refs to lit.*, then rewrite to cached_ if available
            rewritten = self._qualify_tables(sql)
            rewritten = self._rewrite_to_cached(rewritten)
            with self._lock:
                if params:
                    result = self._duck_conn.execute(rewritten, params)
                else:
                    result = self._duck_conn.execute(rewritten)
                return result.fetchall()
        except Exception:
            return self._fallback_sqlite(sql, params)

    def _qualify_tables(self, sql: str) -> str:
        """If the SQL doesn't already reference lit.*, prepend lit. to FROM/JOIN tables.

        Simple heuristic: if 'lit.' is already present, assume user qualified it.
        Otherwise, add 'lit.main.' prefix so DuckDB finds the SQLite tables.
        """
        if "lit." in sql.lower():
            return sql
        # Prefix FROM <table> and JOIN <table> with lit.main.
        sql = re.sub(
            r"(?i)\bFROM\s+([A-Za-z_][A-Za-z0-9_]*)",
            r"FROM lit.\1",
            sql,
        )
        sql = re.sub(
            r"(?i)\bJOIN\s+([A-Za-z_][A-Za-z0-9_]*)",
            r"JOIN lit.\1",
            sql,
        )
        return sql

    def _fallback_sqlite(
        self, sql: str, params: Optional[tuple] = None
    ) -> List[Any]:
        """Execute via a plain SQLite readonly connection."""
        uri = _DB_PATH.as_uri() + "?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=180)
        try:
            conn.execute("PRAGMA busy_timeout=60000")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA query_only=ON")
            conn.execute("PRAGMA mmap_size=12884901888")  # 12 GB
            conn.execute("PRAGMA cache_size=-131072")     # 128 MB
            cur = conn.execute(sql, params or ())
            return cur.fetchall()
        finally:
            conn.close()

    # ── Convenience methods ─────────────────────────────────────────────

    def count(self, table: str) -> int:
        """Fast COUNT(*) on a table."""
        rows = self.execute_analytical(f"SELECT COUNT(*) FROM {table}")
        return rows[0][0] if rows else 0

    def count_where(
        self, table: str, where_clause: str, params: Optional[tuple] = None
    ) -> int:
        """COUNT(*) with a WHERE filter."""
        sql = f"SELECT COUNT(*) FROM {table} WHERE {where_clause}"
        rows = self.execute_analytical(sql, params)
        return rows[0][0] if rows else 0

    def group_count(self, table: str, column: str) -> List[Tuple[Any, int]]:
        """GROUP BY column with counts, ordered descending."""
        sql = (
            f"SELECT {column}, COUNT(*) AS cnt "
            f"FROM {table} GROUP BY {column} ORDER BY cnt DESC"
        )
        return self.execute_analytical(sql)

    def aggregate(self, sql: str, params: Optional[tuple] = None) -> List[Any]:
        """Run any analytical query — alias for execute_analytical."""
        return self.execute_analytical(sql, params)

    # ── Diagnostics ─────────────────────────────────────────────────────

    def list_tables(self) -> List[str]:
        """List all tables visible through the DuckDB→SQLite bridge."""
        self._ensure_attached()
        with self._lock:
            rows = self._duck_conn.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'main' AND table_catalog = 'lit'"
            ).fetchall()
        return [r[0] for r in rows]

    def is_analytical(self, sql: str) -> bool:
        """Check whether a query would be routed through DuckDB."""
        if _FTS5_PATTERN.search(sql):
            return False
        return bool(_ANALYTICAL_PATTERNS.search(sql))

    def close(self) -> None:
        """Shut down the DuckDB connection."""
        with self._lock:
            if self._duck_conn is not None:
                self._duck_conn.close()
                self._duck_conn = None
                self._attached = False


# ── Module-level lazy singleton ─────────────────────────────────────────────

def get_sidecar() -> DuckDBSidecar:
    """Return the global DuckDBSidecar singleton (lazy-init on first call)."""
    return DuckDBSidecar()


# Convenient alias — import as: from duckdb_sidecar import sidecar
class _LazySidecar:
    """Descriptor that defers singleton creation until attribute access."""

    def __init__(self):
        self._obj: Optional[DuckDBSidecar] = None

    def __getattr__(self, name: str):
        if self._obj is None:
            self._obj = get_sidecar()
        return getattr(self._obj, name)


sidecar = _LazySidecar()


# ═══════════════════════════════════════════════════════════════════════════
# CLI — Benchmark Mode
# ═══════════════════════════════════════════════════════════════════════════

def _bench_sqlite(sql: str, label: str) -> Tuple[float, Any]:
    """Time a query on SQLite with mmap tuning."""
    uri = _DB_PATH.as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=180)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA query_only=ON")
    conn.execute("PRAGMA mmap_size=12884901888")
    conn.execute("PRAGMA cache_size=-131072")
    # warm up
    conn.execute(sql).fetchall()
    t0 = time.perf_counter()
    result = conn.execute(sql).fetchall()
    elapsed = time.perf_counter() - t0
    conn.close()
    return elapsed, result


def _bench_duckdb(sc: DuckDBSidecar, sql: str, label: str) -> Tuple[float, Any]:
    """Time a query on DuckDB bridge (already attached)."""
    rewritten = sc._qualify_tables(sql)
    sc._ensure_attached()
    # warm up
    with sc._lock:
        sc._duck_conn.execute(rewritten).fetchall()
    t0 = time.perf_counter()
    with sc._lock:
        result = sc._duck_conn.execute(rewritten).fetchall()
    elapsed = time.perf_counter() - t0
    return elapsed, result


def _bench_duckdb_cached(
    sc: DuckDBSidecar, sql: str, table: str, label: str
) -> Tuple[float, Any]:
    """Time a query on DuckDB native columnar (cached table)."""
    sc._ensure_attached()
    sc.cache_table(table)
    rewritten = sc._qualify_tables(sql)
    rewritten = sc._rewrite_to_cached(rewritten)
    # warm up
    with sc._lock:
        sc._duck_conn.execute(rewritten).fetchall()
    t0 = time.perf_counter()
    with sc._lock:
        result = sc._duck_conn.execute(rewritten).fetchall()
    elapsed = time.perf_counter() - t0
    return elapsed, result


def _table_exists_sqlite(table: str) -> bool:
    """Quick check whether a table exists in the SQLite DB."""
    uri = _DB_PATH.as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=30)
    try:
        cur = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        )
        return cur.fetchone() is not None
    finally:
        conn.close()


def run_benchmark() -> None:
    print("=" * 72)
    print("  DuckDB Analytical Sidecar — Benchmark")
    print(f"  DB: {_DB_PATH}  ({_DB_PATH.stat().st_size / (1024**3):.2f} GB)")
    print("=" * 72)
    print()

    sc = DuckDBSidecar.__new__(DuckDBSidecar)
    sc._initialized = False
    sc.__init__()

    # Verify tables exist before benchmarking
    candidate_tables = [
        "master_citations",
        "evidence_quotes",
        "omega_filesystem_map",
        "pages",
    ]
    tables = [t for t in candidate_tables if _table_exists_sqlite(t)]
    if not tables:
        print("ERROR: None of the benchmark tables exist in the database.")
        return

    skipped = set(candidate_tables) - set(tables)
    if skipped:
        print(f"  ⚠  Skipping missing tables: {', '.join(sorted(skipped))}")
        print()

    # ── COUNT(*) benchmarks ─────────────────────────────────────────────
    print("─── COUNT(*) ────────────────────────────────────────────────────")
    print(f"  {'Table':<26} {'SQLite':>10} {'Bridge':>10} {'Columnar':>10} {'Speedup':>10}  {'Rows':>12}")
    print(f"  {'─'*26} {'─'*10} {'─'*10} {'─'*10} {'─'*10}  {'─'*12}")

    for tbl in tables:
        sql = f"SELECT COUNT(*) FROM {tbl}"
        try:
            sq_t, sq_r = _bench_sqlite(sql, tbl)
            dk_t, dk_r = _bench_duckdb(sc, sql, tbl)
            dc_t, dc_r = _bench_duckdb_cached(sc, sql, tbl, tbl)
            speedup = sq_t / dc_t if dc_t > 0 else float("inf")
            count_val = dc_r[0][0] if dc_r else "?"
            print(
                f"  {tbl:<26} {sq_t*1000:>8.1f}ms {dk_t*1000:>8.1f}ms"
                f" {dc_t*1000:>8.1f}ms {speedup:>8.1f}×  {count_val:>12,}"
            )
        except Exception as e:
            print(f"  {tbl:<26}  ERROR: {e}")

    # ── GROUP BY benchmark ──────────────────────────────────────────────
    print()
    print("─── GROUP BY ────────────────────────────────────────────────────")
    group_queries: List[Tuple[str, str, str]] = []
    if "evidence_quotes" in tables:
        # Verify column exists
        uri = _DB_PATH.as_uri() + "?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=30)
        cols = [
            r[1]
            for r in conn.execute("PRAGMA table_info(evidence_quotes)").fetchall()
        ]
        conn.close()
        if "evidence_category" in cols:
            group_queries.append((
                "evidence_quotes BY category",
                "SELECT evidence_category, COUNT(*) AS cnt "
                "FROM evidence_quotes GROUP BY evidence_category ORDER BY cnt DESC",
                "evidence_quotes",
            ))
        else:
            # Use first text-ish column as fallback
            for c in cols:
                if c not in ("rowid", "id"):
                    group_queries.append((
                        f"evidence_quotes BY {c}",
                        f"SELECT {c}, COUNT(*) AS cnt "
                        f"FROM evidence_quotes GROUP BY {c} ORDER BY cnt DESC LIMIT 15",
                        "evidence_quotes",
                    ))
                    break

    if group_queries:
        print(f"  {'Query':<35} {'SQLite':>10} {'Bridge':>10} {'Columnar':>10} {'Speedup':>10}")
        print(f"  {'─'*35} {'─'*10} {'─'*10} {'─'*10} {'─'*10}")
        for label, sql, cache_tbl in group_queries:
            try:
                sq_t, sq_r = _bench_sqlite(sql, label)
                dk_t, dk_r = _bench_duckdb(sc, sql, label)
                dc_t, dc_r = _bench_duckdb_cached(sc, sql, cache_tbl, label)
                speedup = sq_t / dc_t if dc_t > 0 else float("inf")
                print(
                    f"  {label:<35} {sq_t*1000:>8.1f}ms {dk_t*1000:>8.1f}ms"
                    f" {dc_t*1000:>8.1f}ms {speedup:>8.1f}×"
                )
            except Exception as e:
                print(f"  {label:<35}  ERROR: {e}")
    else:
        print("  (no suitable GROUP BY columns found)")

    # ── COUNT(DISTINCT) benchmark ───────────────────────────────────────
    print()
    print("─── COUNT(DISTINCT) ─────────────────────────────────────────────")
    distinct_queries: List[Tuple[str, str, str]] = []
    if "evidence_quotes" in tables:
        uri = _DB_PATH.as_uri() + "?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=30)
        cols = [
            r[1]
            for r in conn.execute("PRAGMA table_info(evidence_quotes)").fetchall()
        ]
        conn.close()
        if "document_id" in cols:
            distinct_queries.append((
                "DISTINCT document_id FROM evidence_quotes",
                "SELECT COUNT(DISTINCT document_id) FROM evidence_quotes",
                "evidence_quotes",
            ))
        elif "source_file" in cols:
            distinct_queries.append((
                "DISTINCT source_file FROM evidence_quotes",
                "SELECT COUNT(DISTINCT source_file) FROM evidence_quotes",
                "evidence_quotes",
            ))

    if distinct_queries:
        print(f"  {'Query':<40} {'SQLite':>10} {'Bridge':>10} {'Columnar':>10} {'Speedup':>10}  {'Value':>10}")
        print(f"  {'─'*40} {'─'*10} {'─'*10} {'─'*10} {'─'*10}  {'─'*10}")
        for label, sql, cache_tbl in distinct_queries:
            try:
                sq_t, sq_r = _bench_sqlite(sql, label)
                dk_t, dk_r = _bench_duckdb(sc, sql, label)
                dc_t, dc_r = _bench_duckdb_cached(sc, sql, cache_tbl, label)
                speedup = sq_t / dc_t if dc_t > 0 else float("inf")
                val = dc_r[0][0] if dc_r else "?"
                print(
                    f"  {label:<40} {sq_t*1000:>8.1f}ms {dk_t*1000:>8.1f}ms"
                    f" {dc_t*1000:>8.1f}ms {speedup:>8.1f}×  {val:>10,}"
                )
            except Exception as e:
                print(f"  {label:<40}  ERROR: {e}")
    else:
        print("  (no suitable DISTINCT columns found)")

    print()
    print("─── Cache Materialization Times ──────────────────────────────────")
    print(f"  {'Table':<30} {'Time':>12}  {'Rows':>12}")
    print(f"  {'─'*30} {'─'*12}  {'─'*12}")

    # Reset cache to measure materialization fresh
    sc2 = DuckDBSidecar.__new__(DuckDBSidecar)
    sc2._initialized = False
    sc2.__init__()
    # Force new instance for clean measurement
    sc2._instance = None
    import duckdb as _ddb
    c2 = _ddb.connect(database=":memory:")
    c2.execute("INSTALL sqlite; LOAD sqlite;")
    c2.execute(f"ATTACH '{_DB_PATH_FWD}' AS lit (TYPE sqlite, READ_ONLY)")

    for tbl in tables:
        try:
            t0 = time.perf_counter()
            c2.execute(f"CREATE TABLE cached_{tbl} AS SELECT * FROM lit.{tbl}")
            elapsed = time.perf_counter() - t0
            row_count = c2.execute(f"SELECT COUNT(*) FROM cached_{tbl}").fetchone()[0]
            print(f"  {tbl:<30} {elapsed:>10.2f}s  {row_count:>12,}")
        except Exception as e:
            print(f"  {tbl:<30}  ERROR: {e}")
    c2.close()

    print()
    print("=" * 72)
    print("  Benchmark complete.")
    print("  Bridge = DuckDB reading through SQLite scanner (slow for simple ops)")
    print("  Columnar = DuckDB native in-memory tables (the real speedup)")
    print("  Speedup = SQLite ÷ Columnar time")
    print()
    print("  Import: from duckdb_sidecar import sidecar")
    print("=" * 72)

    sc.close()


# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "benchmark":
        run_benchmark()
    else:
        print("Usage: python duckdb_sidecar.py benchmark")
        print("  Runs DuckDB vs SQLite analytical benchmark on litigation_context.db")
