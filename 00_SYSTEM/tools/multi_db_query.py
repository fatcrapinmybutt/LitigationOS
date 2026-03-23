"""
Multi-database query tool for LitigationOS.
Query, search, and inspect all SQLite databases from a single interface.

Usage:
    python multi_db_query.py list                       # List all registered databases
    python multi_db_query.py stats                      # Size + row counts for all DBs
    python multi_db_query.py schema --db litigation_context  # Tables in a DB
    python multi_db_query.py query --db court_forms --sql "SELECT * FROM forms LIMIT 5"
    python multi_db_query.py search --term "disqualification" --limit 20
"""
import sqlite3
import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

ROOT = Path(r"C:\Users\andre\LitigationOS")
DEFAULT_REGISTRY = ROOT / "config" / "db_registry.json"

# Standard PRAGMAs for all connections
PRAGMAS = [
    "PRAGMA busy_timeout=60000",
    "PRAGMA journal_mode=WAL",
    "PRAGMA cache_size=-32000",
    "PRAGMA temp_store=MEMORY",
    "PRAGMA synchronous=NORMAL",
]


class MultiDBQuery:
    """Query across all LitigationOS databases."""

    def __init__(self, registry_path=None):
        self.registry_path = Path(registry_path) if registry_path else DEFAULT_REGISTRY
        self.databases = self._load_registry()

    def _load_registry(self) -> dict:
        """Load DB registry, or auto-discover if registry doesn't exist."""
        if self.registry_path.exists():
            with open(self.registry_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("databases", {})

        # Auto-discover fallback
        print("[WARN] Registry not found, auto-discovering databases...", file=sys.stderr)
        return self._auto_discover()

    def _auto_discover(self) -> dict:
        """Discover databases without a registry file."""
        found = {}

        # Root-level .db files
        for f in ROOT.glob("*.db"):
            if f.is_file() and f.stat().st_size > 0:
                found[f.stem] = {"path": str(f), "role": "unknown"}

        # databases/ directory
        db_dir = ROOT / "databases"
        if db_dir.exists():
            for f in db_dir.rglob("*.db"):
                if f.is_file():
                    key = f.stem if f.stem not in found else f"databases_{f.stem}"
                    found[key] = {"path": str(f), "role": "jurisdiction"}

        # 00_SYSTEM/brains/
        brains_dir = ROOT / "00_SYSTEM" / "brains"
        if brains_dir.exists():
            for f in brains_dir.rglob("*.db"):
                if f.is_file():
                    found[f"brain_{f.stem}"] = {"path": str(f), "role": "brain"}

        return found

    def _connect(self, db_path: str) -> sqlite3.Connection:
        """Open a read-only connection with standard PRAGMAs."""
        path = Path(db_path)
        if not path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
        if path.stat().st_size == 0:
            raise ValueError(f"Database is empty (0 bytes): {db_path}")

        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=10)
        conn.row_factory = sqlite3.Row
        for pragma in PRAGMAS:
            try:
                conn.execute(pragma)
            except sqlite3.OperationalError:
                pass  # read-only mode may reject some PRAGMAs
        return conn

    def _resolve_db(self, db_name: str) -> dict:
        """Resolve a database name to its registry entry."""
        if db_name in self.databases:
            return self.databases[db_name]

        # Fuzzy match — check if name is a substring
        matches = [k for k in self.databases if db_name.lower() in k.lower()]
        if len(matches) == 1:
            return self.databases[matches[0]]
        if len(matches) > 1:
            raise ValueError(f"Ambiguous db name '{db_name}'. Matches: {matches}")
        raise KeyError(f"Database '{db_name}' not found. Use 'list' to see available databases.")

    def list_databases(self) -> list:
        """List all registered databases with basic info."""
        results = []
        for name, info in sorted(self.databases.items()):
            path = Path(info["path"])
            try:
                size = path.stat().st_size
                exists = True
            except OSError:
                size = 0
                exists = False
            results.append({
                "name": name,
                "path": info["path"],
                "role": info.get("role", "unknown"),
                "size_mb": round(size / (1024 * 1024), 2),
                "exists": exists,
            })
        return results

    def query(self, db_name: str, sql: str, params=None) -> list:
        """Query a specific database by name."""
        info = self._resolve_db(db_name)
        conn = self._connect(info["path"])
        try:
            cur = conn.execute(sql, params or ())
            if cur.description:
                cols = [d[0] for d in cur.description]
                return [dict(zip(cols, row)) for row in cur.fetchall()]
            return []
        finally:
            conn.close()

    def search_all(self, term: str, limit: int = 50) -> dict:
        """Search across all databases for a term using FTS5 where available, fallback to LIKE."""
        results = {}
        for name, info in self.databases.items():
            path = Path(info["path"])
            if not path.exists() or path.stat().st_size == 0:
                continue

            db_results = []
            try:
                conn = self._connect(info["path"])

                # Find FTS5 tables
                fts_tables = []
                try:
                    cur = conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND sql LIKE '%fts5%'"
                    )
                    fts_tables = [r[0] for r in cur.fetchall()]
                except sqlite3.OperationalError:
                    pass

                # Search FTS5 tables first
                for tbl in fts_tables[:3]:  # limit to 3 FTS tables per DB
                    try:
                        cur = conn.execute(
                            f"SELECT * FROM [{tbl}] WHERE [{tbl}] MATCH ? LIMIT ?",
                            (term, limit),
                        )
                        if cur.description:
                            cols = [d[0] for d in cur.description]
                            for row in cur.fetchall():
                                db_results.append({
                                    "table": tbl,
                                    "type": "FTS5",
                                    "data": dict(zip(cols, row)),
                                })
                    except sqlite3.OperationalError:
                        pass

                # Fallback: search text columns in regular tables (limit scope)
                if not db_results:
                    tables = conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' "
                        "AND name NOT LIKE 'sqlite_%' LIMIT 20"
                    ).fetchall()

                    for (tbl,) in tables:
                        try:
                            cols_info = conn.execute(f"PRAGMA table_info([{tbl}])").fetchall()
                            text_cols = [c[1] for c in cols_info if c[2].upper() in ("TEXT", "VARCHAR", "")]
                            if not text_cols:
                                continue

                            where_parts = [f"[{c}] LIKE ?" for c in text_cols[:4]]
                            where_sql = " OR ".join(where_parts)
                            params = [f"%{term}%" for _ in where_parts]

                            cur = conn.execute(
                                f"SELECT * FROM [{tbl}] WHERE {where_sql} LIMIT ?",
                                params + [min(limit, 10)],
                            )
                            if cur.description:
                                cols = [d[0] for d in cur.description]
                                for row in cur.fetchall():
                                    db_results.append({
                                        "table": tbl,
                                        "type": "LIKE",
                                        "data": dict(zip(cols, row)),
                                    })
                        except sqlite3.OperationalError:
                            continue

                conn.close()
            except Exception as e:
                db_results.append({"error": str(e)})

            if db_results:
                results[name] = db_results

        return results

    def schema(self, db_name: str) -> list:
        """Get table list for a database with row counts."""
        info = self._resolve_db(db_name)
        conn = self._connect(info["path"])
        try:
            tables = conn.execute(
                "SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view') "
                "ORDER BY type, name"
            ).fetchall()

            result = []
            for tbl_name, tbl_type in tables:
                row_count = -1
                if tbl_type == "table":
                    try:
                        row_count = conn.execute(f"SELECT COUNT(*) FROM [{tbl_name}]").fetchone()[0]
                    except sqlite3.OperationalError:
                        pass
                result.append({
                    "name": tbl_name,
                    "type": tbl_type,
                    "rows": row_count,
                })
            return result
        finally:
            conn.close()

    def stats(self) -> dict:
        """Get summary stats for all databases."""
        results = {}
        total_size = 0
        total_tables = 0

        for name, info in sorted(self.databases.items()):
            path = Path(info["path"])
            if not path.exists():
                results[name] = {"status": "MISSING", "path": info["path"]}
                continue

            size = path.stat().st_size
            if size == 0:
                results[name] = {"status": "EMPTY", "path": info["path"], "size_bytes": 0}
                continue

            total_size += size
            table_count = 0
            total_rows = 0

            try:
                conn = self._connect(info["path"])
                tables = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                ).fetchall()
                table_count = len(tables)

                # Count rows in up to 50 tables for speed
                for (tbl,) in tables[:50]:
                    try:
                        total_rows += conn.execute(f"SELECT COUNT(*) FROM [{tbl}]").fetchone()[0]
                    except sqlite3.OperationalError:
                        pass
                conn.close()
            except Exception as e:
                results[name] = {
                    "status": "ERROR",
                    "error": str(e),
                    "path": info["path"],
                    "size_mb": round(size / (1024 * 1024), 2),
                }
                continue

            total_tables += table_count
            results[name] = {
                "status": "OK",
                "role": info.get("role", "unknown"),
                "size_mb": round(size / (1024 * 1024), 2),
                "tables": table_count,
                "rows": total_rows,
            }

        return {
            "summary": {
                "total_databases": len(results),
                "total_size_gb": round(total_size / (1024 ** 3), 2),
                "total_tables": total_tables,
            },
            "databases": results,
        }


def format_table(rows: list, columns: list = None) -> str:
    """Simple ASCII table formatter."""
    if not rows:
        return "(no results)"
    if columns is None:
        columns = list(rows[0].keys()) if isinstance(rows[0], dict) else [f"col{i}" for i in range(len(rows[0]))]

    # Compute widths
    widths = {c: len(str(c)) for c in columns}
    for row in rows:
        for c in columns:
            val = row.get(c, "") if isinstance(row, dict) else row[columns.index(c)]
            widths[c] = max(widths[c], len(str(val)))

    # Cap column widths
    for c in widths:
        widths[c] = min(widths[c], 80)

    header = " | ".join(str(c).ljust(widths[c]) for c in columns)
    sep = "-+-".join("-" * widths[c] for c in columns)
    lines = [header, sep]
    for row in rows:
        vals = []
        for c in columns:
            v = row.get(c, "") if isinstance(row, dict) else row[columns.index(c)]
            vals.append(str(v)[:widths[c]].ljust(widths[c]))
        lines.append(" | ".join(vals))
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="LitigationOS Multi-DB Query Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python multi_db_query.py list
  python multi_db_query.py stats
  python multi_db_query.py schema --db court_forms
  python multi_db_query.py query --db litigation_context --sql "SELECT name FROM sqlite_master LIMIT 10"
  python multi_db_query.py search --term "disqualification" --limit 10
""",
    )
    parser.add_argument("command", choices=["query", "search", "schema", "stats", "list"])
    parser.add_argument("--db", help="Database name (use 'list' to see names)")
    parser.add_argument("--sql", help="SQL query (for 'query' command)")
    parser.add_argument("--term", help="Search term (for 'search' command)")
    parser.add_argument("--limit", type=int, default=50, help="Max results (default: 50)")
    parser.add_argument("--registry", help="Path to db_registry.json")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    mdb = MultiDBQuery(registry_path=args.registry)

    if args.command == "list":
        dbs = mdb.list_databases()
        if args.json:
            print(json.dumps(dbs, indent=2))
        else:
            print(f"\nLitigationOS Database Registry — {len(dbs)} databases\n")
            print(format_table(dbs, ["name", "role", "size_mb", "exists"]))
            print(f"\nTotal: {len(dbs)} databases")

    elif args.command == "stats":
        data = mdb.stats()
        if args.json:
            print(json.dumps(data, indent=2))
        else:
            s = data["summary"]
            print(f"\n{'=' * 60}")
            print(f"LitigationOS Database Stats")
            print(f"{'=' * 60}")
            print(f"  Total databases: {s['total_databases']}")
            print(f"  Total size:      {s['total_size_gb']} GB")
            print(f"  Total tables:    {s['total_tables']}")
            print(f"{'=' * 60}\n")

            rows = []
            for name, info in sorted(data["databases"].items()):
                if info["status"] == "OK":
                    rows.append({
                        "name": name,
                        "role": info.get("role", "?"),
                        "size_mb": info["size_mb"],
                        "tables": info["tables"],
                        "rows": info["rows"],
                    })
                else:
                    rows.append({
                        "name": name,
                        "role": info.get("status", "?"),
                        "size_mb": info.get("size_mb", 0),
                        "tables": "-",
                        "rows": "-",
                    })
            print(format_table(rows, ["name", "role", "size_mb", "tables", "rows"]))

    elif args.command == "schema":
        if not args.db:
            print("ERROR: --db required for schema command", file=sys.stderr)
            sys.exit(1)
        tables = mdb.schema(args.db)
        if args.json:
            print(json.dumps(tables, indent=2))
        else:
            print(f"\nSchema for '{args.db}' — {len(tables)} tables/views\n")
            print(format_table(tables, ["name", "type", "rows"]))

    elif args.command == "query":
        if not args.db or not args.sql:
            print("ERROR: --db and --sql required for query command", file=sys.stderr)
            sys.exit(1)
        rows = mdb.query(args.db, args.sql)
        if args.json:
            print(json.dumps(rows, indent=2, default=str))
        else:
            if rows:
                print(format_table(rows))
            else:
                print("(no results)")
            print(f"\n{len(rows)} rows returned")

    elif args.command == "search":
        if not args.term:
            print("ERROR: --term required for search command", file=sys.stderr)
            sys.exit(1)
        results = mdb.search_all(args.term, limit=args.limit)
        if args.json:
            print(json.dumps(results, indent=2, default=str))
        else:
            if not results:
                print(f"No results for '{args.term}' across any database.")
            else:
                total = sum(len(v) for v in results.values())
                print(f"\nSearch: '{args.term}' — {total} results across {len(results)} databases\n")
                for db_name, hits in results.items():
                    print(f"  [{db_name}] — {len(hits)} hits")
                    for hit in hits[:5]:
                        tbl = hit.get("table", "?")
                        htype = hit.get("type", "?")
                        if "error" in hit:
                            print(f"    ERROR: {hit['error']}")
                        else:
                            preview = str(hit.get("data", {}))[:120]
                            print(f"    {tbl} ({htype}): {preview}")
                    if len(hits) > 5:
                        print(f"    ... and {len(hits) - 5} more")


if __name__ == "__main__":
    main()
