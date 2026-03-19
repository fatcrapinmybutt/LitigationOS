#!/usr/bin/env python3
"""
Authority Triples Emitter (candidate-only)

Emits (proposition?, authority_ref, pinpoint?) as CANDIDATE triples.
No propositions are asserted; proposition field left blank unless user supplies text.
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
    p.add_argument("--q", required=True)
    p.add_argument("--k", type=int, default=50)
    p.add_argument("--out", required=True)
    args=p.parse_args()

    con=connect(args.db)
    cur=con.cursor()
    cur.execute("""
      SELECT authority_ref, page FROM shards_fts
      JOIN shards USING(authority_ref)
      WHERE shards_fts MATCH ?
      LIMIT ?;
    """,(args.q, args.k))

    with open(args.out,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=["proposition","authority_ref","pinpoint","status"])
        w.writeheader()
        for r in cur.fetchall():
            w.writerow({
                "proposition":"",
                "authority_ref": r["authority_ref"],
                "pinpoint": f"page {r['page']}",
                "status":"CANDIDATE"
            })

if __name__=="__main__":
    main()
