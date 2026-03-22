#!/usr/bin/env python3
"""
unified_hub.py — Unified multi-database access layer for LitigationOS.

Provides a single interface to query, search, and inspect all 20+ SQLite
databases across the repository. Read-only by default.

Usage:
    python unified_hub.py list
    python unified_hub.py schema litigation
    python unified_hub.py schema litigation evidence_quotes
    python unified_hub.py query litigation "SELECT COUNT(*) FROM evidence_quotes"
    python unified_hub.py search "Sullivan v Gray"
    python unified_hub.py stats
    python unified_hub.py health
"""

import argparse
import json
import os
import sqlite3
import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path

# UTF-8 stdout — mandatory for LitigationOS
sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace", closefd=False)
sys.stderr = open(sys.stderr.fileno(), mode="w", encoding="utf-8", errors="replace", closefd=False)

# ---------------------------------------------------------------------------
# Static registry — known databases with friendly names
# ---------------------------------------------------------------------------
_STATIC_REGISTRY = {
    # Core
    "litigation": "litigation_context.db",
    "court_forms": "court_forms.db",
    "mcr_rules": "mcr_rules.db",
    "litigationos": "litigationos.db",
    # Brains
    "authority_brain": "00_SYSTEM/brains/authority_brain.db",
    "chat_brain": "00_SYSTEM/brains/chat_intelligence_brain.db",
    "claims_brain": "00_SYSTEM/brains/claims_brain.db",
    "contradictions": "00_SYSTEM/brains/contradictions.db",
    "entity_brain": "00_SYSTEM/brains/entity_brain.db",
    "interpretation_brain": "00_SYSTEM/brains/interpretation_brain.db",
    "narrative_brain": "00_SYSTEM/brains/narrative_brain.db",
    # Scripts
    "script_forge": "script_forge.db",
    "script_vault": "script_vault.db",
    # Pipeline / system (registered only if present on disk)
    # "pipeline": "pipeline.db",
    # "watchdog": "watchdog.db",
}

# Directories to scan for additional .db files
_SCAN_DIRS = [
    "databases",
    "00_SYSTEM/brains",
]

# Connection PRAGMAs applied to every connection
_PRAGMAS = [
    "PRAGMA busy_timeout = 60000;",
    "PRAGMA journal_mode = WAL;",
    "PRAGMA cache_size = -32000;",
    "PRAGMA temp_store = MEMORY;",
    "PRAGMA synchronous = NORMAL;",
]

# Concurrency guard — max 3 open connections at a time
_MAX_CONNECTIONS = 3


class UnifiedHub:
    """Unified access layer for all LitigationOS databases."""

    def __init__(self, base_path: str = r"C:\Users\andre\LitigationOS"):
        self.base_path = Path(base_path)
        self.registry: dict[str, Path] = {}
        self._connections: dict[str, sqlite3.Connection] = {}
        self._lock = threading.Lock()
        self._conn_semaphore = threading.Semaphore(_MAX_CONNECTIONS)
        self._discover_databases()

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def _discover_databases(self) -> None:
        """Auto-discover all .db files and register them with friendly names."""
        # 1. Load static registry
        for name, rel_path in _STATIC_REGISTRY.items():
            full = self.base_path / rel_path.replace("/", os.sep)
            self.registry[name] = full

        # 2. Scan additional directories for .db files not already registered
        registered_paths = {p.resolve() for p in self.registry.values() if p.exists()}
        for scan_dir in _SCAN_DIRS:
            d = self.base_path / scan_dir.replace("/", os.sep)
            if not d.is_dir():
                continue
            for db_file in sorted(d.glob("*.db")):
                if db_file.resolve() in registered_paths:
                    continue
                friendly = db_file.stem.replace("-", "_").replace(" ", "_")
                # Avoid name collisions
                if friendly in self.registry:
                    friendly = f"{scan_dir.replace('/', '_').replace(os.sep, '_')}_{friendly}"
                self.registry[friendly] = db_file
                registered_paths.add(db_file.resolve())

        # 3. Scan repo root for any .db files not yet registered
        for db_file in sorted(self.base_path.glob("*.db")):
            if db_file.resolve() in registered_paths:
                continue
            friendly = db_file.stem.replace("-", "_").replace(" ", "_")
            if friendly in self.registry:
                friendly = f"root_{friendly}"
            self.registry[friendly] = db_file
            registered_paths.add(db_file.resolve())

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def connect(self, db_name: str, *, write: bool = False) -> sqlite3.Connection:
        """Get a connection to the named database with proper PRAGMAs.

        Connections are cached. The semaphore limits total open connections
        to _MAX_CONNECTIONS.
        """
        if db_name not in self.registry:
            raise KeyError(f"Unknown database '{db_name}'. Use list() to see available databases.")

        with self._lock:
            if db_name in self._connections:
                return self._connections[db_name]

        db_path = self.registry[db_name]
        if not db_path.exists():
            raise FileNotFoundError(f"Database file not found: {db_path}")

        if not self._conn_semaphore.acquire(timeout=30):
            raise RuntimeError(
                f"Connection limit reached ({_MAX_CONNECTIONS}). "
                "Close unused connections with close() or close_all()."
            )

        try:
            uri = db_path.as_uri()
            if not write:
                uri += "?mode=ro"
            conn = sqlite3.connect(uri, uri=True, timeout=60)
            conn.row_factory = sqlite3.Row

            for pragma in _PRAGMAS:
                try:
                    conn.execute(pragma)
                except sqlite3.OperationalError:
                    pass  # read-only may reject journal_mode change

            with self._lock:
                self._connections[db_name] = conn
            return conn
        except Exception:
            self._conn_semaphore.release()
            raise

    def close(self, db_name: str) -> None:
        """Close a specific connection and release its semaphore slot."""
        with self._lock:
            conn = self._connections.pop(db_name, None)
        if conn:
            try:
                conn.close()
            except Exception:
                pass
            self._conn_semaphore.release()

    def close_all(self) -> None:
        """Close all open connections."""
        with self._lock:
            names = list(self._connections.keys())
        for name in names:
            self.close(name)

    @contextmanager
    def open(self, db_name: str, *, write: bool = False):
        """Context manager that opens a connection and closes it on exit."""
        conn = self.connect(db_name, write=write)
        try:
            yield conn
        finally:
            self.close(db_name)

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def query(self, db_name: str, sql: str, params: tuple | list | None = None) -> list[dict]:
        """Execute a query and return rows as list of dicts."""
        conn = self.connect(db_name)
        try:
            cursor = conn.execute(sql, params or ())
            cols = [d[0] for d in cursor.description] if cursor.description else []
            return [dict(zip(cols, row)) for row in cursor.fetchall()]
        except sqlite3.OperationalError as e:
            raise sqlite3.OperationalError(f"[{db_name}] {e}") from e

    def query_one(self, db_name: str, sql: str, params: tuple | list | None = None) -> dict | None:
        """Execute a query and return the first row as a dict, or None."""
        rows = self.query(db_name, sql, params)
        return rows[0] if rows else None

    def execute(self, db_name: str, sql: str, params: tuple | list | None = None) -> int:
        """Execute a write statement. Returns rows affected. Requires write=True on connect."""
        conn = self.connect(db_name, write=True)
        cursor = conn.execute(sql, params or ())
        conn.commit()
        return cursor.rowcount

    def cross_query(self, queries: dict[str, str | tuple]) -> dict[str, list[dict]]:
        """Execute queries across multiple databases.

        queries: {db_name: sql_string} or {db_name: (sql_string, params)}
        Returns: {db_name: [rows]}
        """
        results = {}
        for db_name, q in queries.items():
            if isinstance(q, tuple):
                sql, params = q
            else:
                sql, params = q, None
            try:
                results[db_name] = self.query(db_name, sql, params)
            except (FileNotFoundError, sqlite3.OperationalError, KeyError) as e:
                results[db_name] = [{"error": str(e)}]
        return results

    # ------------------------------------------------------------------
    # Search across all databases
    # ------------------------------------------------------------------

    def _find_fts_tables(self, db_name: str) -> list[str]:
        """Find FTS5 virtual tables in a database."""
        try:
            rows = self.query(
                db_name,
                "SELECT name FROM sqlite_master WHERE type='table' AND sql LIKE '%fts5%'",
            )
            return [r["name"] for r in rows]
        except Exception:
            return []

    def search_all(self, term: str, limit: int = 20) -> dict[str, list[dict]]:
        """Search across ALL databases using FTS5 where available.

        Falls back to LIKE on key text columns for databases without FTS.
        """
        results: dict[str, list[dict]] = {}
        safe_term = term.replace("'", "''")

        for db_name in sorted(self.registry):
            if not self.registry[db_name].exists():
                continue

            hits: list[dict] = []

            # Try FTS5 tables first
            fts_tables = self._find_fts_tables(db_name)
            for fts_table in fts_tables:
                try:
                    rows = self.query(
                        db_name,
                        f"SELECT *, rank FROM {fts_table} WHERE {fts_table} MATCH ? "
                        f"ORDER BY rank LIMIT ?",
                        (term, limit),
                    )
                    for r in rows:
                        r["_source_table"] = fts_table
                        r["_source_db"] = db_name
                    hits.extend(rows)
                except Exception:
                    pass

            # Fallback: LIKE search on tables with text-like column names
            if not hits:
                try:
                    tables = self.query(
                        db_name,
                        "SELECT name FROM sqlite_master WHERE type='table' "
                        "AND name NOT LIKE 'sqlite_%' LIMIT 50",
                    )
                    for t in tables[:10]:  # cap to avoid slow scans
                        tname = t["name"]
                        try:
                            cols = self.query(db_name, f"PRAGMA table_info({tname})")
                        except Exception:
                            continue
                        text_cols = [
                            c["name"]
                            for c in cols
                            if c.get("type", "").upper() in ("TEXT", "VARCHAR", "")
                        ]
                        if not text_cols:
                            continue
                        where = " OR ".join(
                            f'"{c}" LIKE ?' for c in text_cols[:5]
                        )
                        params = [f"%{term}%"] * min(len(text_cols), 5)
                        try:
                            rows = self.query(
                                db_name,
                                f'SELECT * FROM "{tname}" WHERE {where} LIMIT ?',
                                (*params, limit),
                            )
                            for r in rows:
                                r["_source_table"] = tname
                                r["_source_db"] = db_name
                            hits.extend(rows)
                        except Exception:
                            continue
                except Exception:
                    pass

            if hits:
                results[db_name] = hits[:limit]

            # Release connection after each DB to stay within limits
            self.close(db_name)

        return results

    # ------------------------------------------------------------------
    # Schema inspection
    # ------------------------------------------------------------------

    def schema(self, db_name: str, table: str | None = None) -> dict:
        """Get schema for a database or a specific table.

        Without table: returns {table_name: [{name, type, notnull, pk, dflt_value}, ...]}
        With table:    returns {columns: [...], row_count: int, indexes: [...]}
        """
        if table:
            cols = self.query(db_name, f"PRAGMA table_info({table})")
            try:
                count_row = self.query_one(db_name, f'SELECT COUNT(*) AS cnt FROM "{table}"')
                row_count = count_row["cnt"] if count_row else "?"
            except Exception:
                row_count = "?"
            try:
                indexes = self.query(db_name, f"PRAGMA index_list({table})")
            except Exception:
                indexes = []
            self.close(db_name)
            return {"table": table, "columns": cols, "row_count": row_count, "indexes": indexes}

        # Full database schema
        tables = self.query(
            db_name,
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name",
        )
        result = {}
        for t in tables:
            tname = t["name"]
            try:
                cols = self.query(db_name, f"PRAGMA table_info({tname})")
                result[tname] = cols
            except Exception:
                result[tname] = [{"error": "could not read schema"}]
        self.close(db_name)
        return result

    def list_tables(self, db_name: str) -> list[str]:
        """List all table names in a database."""
        rows = self.query(
            db_name,
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name",
        )
        self.close(db_name)
        return [r["name"] for r in rows]

    # ------------------------------------------------------------------
    # Stats & health
    # ------------------------------------------------------------------

    def _db_size(self, db_name: str) -> int:
        """Return file size in bytes, or 0 if missing."""
        p = self.registry.get(db_name)
        if p and p.exists():
            size = p.stat().st_size
            # Include -wal and -shm if present
            for suffix in ("-wal", "-shm"):
                extra = p.with_name(p.name + suffix)
                if extra.exists():
                    size += extra.stat().st_size
            return size
        return 0

    def _format_size(self, size_bytes: int) -> str:
        """Human-readable file size."""
        if size_bytes == 0:
            return "0 B"
        for unit in ("B", "KB", "MB", "GB"):
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}" if unit != "B" else f"{size_bytes} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    def stats(self) -> dict:
        """Get stats for all registered databases."""
        all_stats = {}
        total_size = 0
        total_tables = 0

        for db_name in sorted(self.registry):
            info: dict = {"path": str(self.registry[db_name])}
            size = self._db_size(db_name)
            info["size_bytes"] = size
            info["size_human"] = self._format_size(size)
            total_size += size

            if not self.registry[db_name].exists():
                info["status"] = "missing"
                info["tables"] = 0
                all_stats[db_name] = info
                continue

            try:
                tables = self.query(
                    db_name,
                    "SELECT COUNT(*) AS cnt FROM sqlite_master WHERE type='table' "
                    "AND name NOT LIKE 'sqlite_%'",
                )
                tcount = tables[0]["cnt"] if tables else 0
                info["tables"] = tcount
                info["status"] = "healthy"
                total_tables += tcount
            except Exception as e:
                info["tables"] = "?"
                info["status"] = f"error: {e}"
            finally:
                self.close(db_name)

            all_stats[db_name] = info

        return {
            "databases": all_stats,
            "total_databases": len(self.registry),
            "total_size_bytes": total_size,
            "total_size_human": self._format_size(total_size),
            "total_tables": total_tables,
        }

    def health(self) -> dict:
        """Health check all databases — verify accessible, detect corruption."""
        report = {}
        ok_count = 0
        fail_count = 0

        for db_name in sorted(self.registry):
            entry: dict = {"path": str(self.registry[db_name])}
            path = self.registry[db_name]

            if not path.exists():
                entry["status"] = "missing"
                entry["detail"] = "File does not exist"
                fail_count += 1
                report[db_name] = entry
                continue

            entry["size"] = self._format_size(self._db_size(db_name))

            try:
                # Integrity quick-check (fast — checks freelist only)
                rows = self.query(db_name, "PRAGMA quick_check(1)")
                qc = rows[0] if rows else {}
                check_val = qc.get("quick_check", qc.get("ok", "unknown"))
                if check_val == "ok":
                    entry["status"] = "healthy"
                    ok_count += 1
                else:
                    entry["status"] = "warning"
                    entry["detail"] = f"quick_check returned: {check_val}"
                    fail_count += 1
            except Exception as e:
                entry["status"] = "error"
                entry["detail"] = str(e)
                fail_count += 1
            finally:
                self.close(db_name)

            report[db_name] = entry

        return {
            "databases": report,
            "healthy": ok_count,
            "unhealthy": fail_count,
            "total": ok_count + fail_count,
        }

    def list_databases(self) -> list[dict]:
        """Return a list of registered databases with path and existence status."""
        result = []
        for name in sorted(self.registry):
            p = self.registry[name]
            result.append({
                "name": name,
                "path": str(p),
                "exists": p.exists(),
                "size": self._format_size(self._db_size(name)) if p.exists() else "—",
            })
        return result

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close_all()

    def __del__(self):
        try:
            self.close_all()
        except Exception:
            pass


# ======================================================================
# CLI interface
# ======================================================================

def _print_json(obj, pretty: bool = True):
    """Print an object as JSON."""

    def _default(o):
        if isinstance(o, Path):
            return str(o)
        if isinstance(o, sqlite3.Row):
            return dict(o)
        return repr(o)

    indent = 2 if pretty else None
    print(json.dumps(obj, indent=indent, default=_default, ensure_ascii=False))


def _print_table(rows: list[dict], columns: list[str] | None = None):
    """Simple ASCII table printer."""
    if not rows:
        print("(no results)")
        return
    if columns is None:
        columns = list(rows[0].keys())
    # Filter out internal keys
    columns = [c for c in columns if not c.startswith("_")]

    widths = {c: len(c) for c in columns}
    str_rows = []
    for row in rows:
        sr = {}
        for c in columns:
            val = str(row.get(c, ""))
            if len(val) > 80:
                val = val[:77] + "..."
            sr[c] = val
            widths[c] = max(widths[c], len(val))
        str_rows.append(sr)

    header = " | ".join(c.ljust(widths[c]) for c in columns)
    sep = "-+-".join("-" * widths[c] for c in columns)
    print(header)
    print(sep)
    for sr in str_rows:
        print(" | ".join(sr.get(c, "").ljust(widths[c]) for c in columns))


def main():
    parser = argparse.ArgumentParser(
        description="LitigationOS Unified Database Hub",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list                                        List all databases
  %(prog)s schema litigation                           Show all tables in litigation_context.db
  %(prog)s schema litigation evidence_quotes           Show columns for evidence_quotes
  %(prog)s query litigation "SELECT COUNT(*) FROM evidence_quotes"
  %(prog)s search "Sullivan v Gray"                    Search ALL databases
  %(prog)s stats                                       Full stats report
  %(prog)s health                                      Health check all databases
        """,
    )
    parser.add_argument("command", choices=["list", "schema", "query", "search", "stats", "health"])
    parser.add_argument("args", nargs="*", help="Command-specific arguments")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--write", action="store_true", help="Allow write operations (query command only)")
    parser.add_argument("--limit", type=int, default=50, help="Max rows to return (default: 50)")
    parser.add_argument(
        "--base-path",
        default=r"C:\Users\andre\LitigationOS",
        help="Repository root path",
    )

    args = parser.parse_args()

    with UnifiedHub(base_path=args.base_path) as hub:

        if args.command == "list":
            dbs = hub.list_databases()
            if args.json:
                _print_json(dbs)
            else:
                _print_table(dbs, ["name", "size", "exists", "path"])

        elif args.command == "schema":
            if not args.args:
                parser.error("schema requires a database name, e.g.: schema litigation")
            db_name = args.args[0]
            table = args.args[1] if len(args.args) > 1 else None
            result = hub.schema(db_name, table)
            if args.json:
                _print_json(result)
            elif table:
                print(f"\n  Table: {db_name}.{table}")
                print(f"  Rows:  {result.get('row_count', '?')}\n")
                _print_table(result.get("columns", []), ["name", "type", "notnull", "pk", "dflt_value"])
                if result.get("indexes"):
                    print(f"\n  Indexes:")
                    _print_table(result["indexes"])
            else:
                tables = sorted(result.keys())
                print(f"\n  Database: {db_name}  ({len(tables)} tables)\n")
                for tname in tables:
                    cols = result[tname]
                    col_names = ", ".join(c.get("name", "?") for c in cols if isinstance(c, dict))
                    print(f"  {tname}: {col_names}")

        elif args.command == "query":
            if len(args.args) < 2:
                parser.error('query requires db_name and sql, e.g.: query litigation "SELECT 1"')
            db_name = args.args[0]
            sql = args.args[1]

            # Safety: block writes unless --write flag
            sql_upper = sql.strip().upper()
            if not args.write and any(
                sql_upper.startswith(kw)
                for kw in ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "REPLACE")
            ):
                print("ERROR: Write operations require --write flag.", file=sys.stderr)
                sys.exit(1)

            rows = hub.query(db_name, sql)
            rows = rows[: args.limit]
            if args.json:
                _print_json(rows)
            else:
                _print_table(rows)

        elif args.command == "search":
            if not args.args:
                parser.error("search requires a term, e.g.: search \"Sullivan v Gray\"")
            term = " ".join(args.args)
            results = hub.search_all(term, limit=args.limit)
            if args.json:
                _print_json(results)
            else:
                if not results:
                    print(f"No results found for '{term}' across all databases.")
                else:
                    total_hits = sum(len(v) for v in results.values())
                    print(f"\n  Found {total_hits} result(s) across {len(results)} database(s) for '{term}':\n")
                    for db_name, hits in results.items():
                        print(f"  === {db_name} ({len(hits)} hit{'s' if len(hits) != 1 else ''}) ===")
                        _print_table(hits[:10])
                        if len(hits) > 10:
                            print(f"  ... and {len(hits) - 10} more")
                        print()

        elif args.command == "stats":
            result = hub.stats()
            if args.json:
                _print_json(result)
            else:
                print(f"\n  LitigationOS Database Statistics")
                print(f"  Total: {result['total_databases']} databases, "
                      f"{result['total_size_human']}, "
                      f"{result['total_tables']} tables\n")
                db_rows = []
                for name, info in sorted(result["databases"].items()):
                    db_rows.append({
                        "database": name,
                        "size": info.get("size_human", "?"),
                        "tables": str(info.get("tables", "?")),
                        "status": info.get("status", "?"),
                    })
                _print_table(db_rows, ["database", "size", "tables", "status"])

        elif args.command == "health":
            result = hub.health()
            if args.json:
                _print_json(result)
            else:
                print(f"\n  LitigationOS Database Health Check")
                print(f"  Healthy: {result['healthy']} / {result['total']}\n")
                db_rows = []
                for name, info in sorted(result["databases"].items()):
                    status = info.get("status", "?")
                    icon = {"healthy": "OK", "missing": "MISSING", "warning": "WARN"}.get(
                        status, "ERR"
                    )
                    db_rows.append({
                        "database": name,
                        "size": info.get("size", "—"),
                        "status": icon,
                        "detail": info.get("detail", ""),
                    })
                _print_table(db_rows, ["database", "size", "status", "detail"])


if __name__ == "__main__":
    main()
