#!/usr/bin/env python3
"""
Vehicle Map Scaffolder (non-interpretive, candidate-only)

Purpose:
- Emit a Vehicle Map SCAFFOLD from authority hits without asserting law.
- Produces CANDIDATE rows only; FILING mode must validate independently.

Inputs:
- authority_store.sqlite
- query terms (anchors or FTS queries)

Outputs:
- vehicle_map_scaffold.csv with columns:
  relief, vehicle_form, rule_candidate, authority_ref, notes, status

Rules:
- No synthesis or conclusions.
- status is always CANDIDATE.
"""

import argparse, csv, sqlite3, os, sys

def die(msg, code=2):
    print(msg, file=sys.stderr); raise SystemExit(code)

def connect(db):
    if not os.path.exists(db): die(f"DB not found: {db}")
    con=sqlite3.connect(db); con.row_factory=sqlite3.Row; return con

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--db", required=True)
    p.add_argument("--q", required=True, help="FTS query or anchor token")
    p.add_argument("--k", type=int, default=50)
    p.add_argument("--out", required=True)
    args=p.parse_args()

    con=connect(args.db)
    cur=con.cursor()
    cur.execute("""
      SELECT s.authority_ref, s.lexical_anchors, s.header_lines
      FROM shards_fts JOIN shards s ON s.authority_ref=shards_fts.authority_ref
      WHERE shards_fts MATCH ?
      LIMIT ?;
    """,(args.q, args.k))

    rows=[]
    for r in cur.fetchall():
        rows.append({
            "relief":"",
            "vehicle_form":"",
            "rule_candidate":"",
            "authority_ref": r["authority_ref"],
            "notes":"extracted hit; candidate only",
            "status":"CANDIDATE"
        })

    with open(args.out,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=rows[0].keys() if rows else ["relief","vehicle_form","rule_candidate","authority_ref","notes","status"])
        w.writeheader()
        for row in rows: w.writerow(row)

if __name__=="__main__":
    main()
