"""
Quick DB Query Tool for Copilot Shell Sessions
===============================================
Usage: python dbq.py "SELECT * FROM auth_rules LIMIT 5"
       python dbq.py fts evidence_quotes_fts "Watson custody"
       python dbq.py health
       python dbq.py tables
       python dbq.py count tort_claims

Never hangs. WAL mode. Timeout protection. Cycle Method output.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shell_resilience_engine import (
    safe_query, safe_fts, db_health_check, cycle_print, init
)

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print('  python dbq.py "SQL QUERY"')
        print('  python dbq.py fts TABLE_FTS "search terms"')
        print("  python dbq.py health")
        print("  python dbq.py tables")
        print("  python dbq.py count TABLE_NAME")
        return

    cmd = sys.argv[1].lower()

    # Initialize WAL
    init()

    if cmd == "health":
        h = db_health_check()
        for k, v in h.items():
            print(f"  {k}: {v}")

    elif cmd == "tables":
        rows = safe_query(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        for r in rows:
            print(f"  {r['name']}")
        print(f"\n  Total: {len(rows)} tables")

    elif cmd == "count":
        table = sys.argv[2] if len(sys.argv) > 2 else "sqlite_master"
        rows = safe_query(f"SELECT COUNT(*) as cnt FROM [{table}]")
        print(f"  {table}: {rows[0]['cnt']} rows")

    elif cmd == "fts":
        table = sys.argv[2] if len(sys.argv) > 2 else "evidence_quotes_fts"
        terms = sys.argv[3] if len(sys.argv) > 3 else "Watson"
        rows = safe_fts(table, terms, limit=10)
        print(f"  {len(rows)} results from {table} for '{terms}':")
        for r in rows:
            # Print first 200 chars of each row
            text = str(dict(r))[:200]
            print(f"    {text}")

    else:
        # Treat as SQL query
        sql = " ".join(sys.argv[1:])
        rows = safe_query(sql)
        if not rows:
            print("  (no results)")
            return
        # Print header
        cols = list(rows[0].keys())
        print("  | " + " | ".join(cols) + " |")
        print("  |" + "|".join(["---" for _ in cols]) + "|")
        # Print rows (max 50)
        for r in rows[:50]:
            vals = []
            for c in cols:
                v = str(r[c])
                if len(v) > 60:
                    v = v[:57] + "..."
                vals.append(v)
            print("  | " + " | ".join(vals) + " |")
        if len(rows) > 50:
            print(f"  ... ({len(rows)} total rows, showing first 50)")


if __name__ == "__main__":
    main()
