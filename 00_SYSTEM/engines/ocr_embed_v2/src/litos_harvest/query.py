
from __future__ import annotations

import argparse
from pathlib import Path
from .index.fts_sqlite import search

def _args():
    ap = argparse.ArgumentParser(description="Query the FTS index for a harvest run")
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--query", required=True)
    ap.add_argument("--limit", type=int, default=20)
    return ap.parse_args()

def main():
    a = _args()
    run_dir = Path(a.run_dir)
    db = run_dir / "fts.sqlite"
    if not db.exists():
        raise SystemExit(f"FTS db not found: {db}")
    rows = search(db, a.query, limit=a.limit)
    for r in rows:
        print(f"- {r['path']} [{r['chunk_id']}] {r['snip']}")
if __name__ == "__main__":
    main()
