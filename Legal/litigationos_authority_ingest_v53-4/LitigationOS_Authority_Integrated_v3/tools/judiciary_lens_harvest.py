#!/usr/bin/env python3
"""
Judiciary Lens Harvester (non-interpretive)

FTS-safe: treats each token as a phrase query when it contains whitespace.
"""
import argparse, csv, json, os, sqlite3, sys

def die(msg, code=2):
    print(msg, file=sys.stderr); raise SystemExit(code)

def connect(db):
    if not os.path.exists(db) or os.path.getsize(db)==0:
        die(f"DB not found/empty: {db}")
    con=sqlite3.connect(db); con.row_factory=sqlite3.Row; return con

def fts_match(q: str) -> str:
    q=q.strip()
    q=q.replace('"','""')
    if any(c.isspace() for c in q):
        return f'"{q}"'
    return q

def run_query(con, q, k):
    q2=q.strip()
    if not q2: return []
    match=fts_match(q2)
    cur=con.cursor()
    cur.execute("""
      SELECT s.authority_ref, s.doc_id, s.page, s.header_lines,
             snippet(shards_fts, 3, '[', ']', '…', 10) AS snippet
      FROM shards_fts
      JOIN shards s ON s.authority_ref = shards_fts.authority_ref
      WHERE shards_fts MATCH ?
      LIMIT ?;
    """,(match,k))
    return [dict(r) for r in cur.fetchall()]

def main():
    p=argparse.ArgumentParser(description="Judiciary Lens Harvester (non-interpretive)")
    p.add_argument("--db", required=True)
    p.add_argument("--lens", required=True)
    p.add_argument("--k", type=int, default=10)
    p.add_argument("--out", required=True)
    args=p.parse_args()

    lens=json.load(open(args.lens,"r",encoding="utf-8"))
    tokens=list(lens.get("tokens") or [])
    con=connect(args.db)

    out_rows=[]
    for t in tokens:
        for h in run_query(con, t, args.k):
            out_rows.append({
                "token": t,
                "authority_ref": h.get("authority_ref",""),
                "doc_id": h.get("doc_id",""),
                "page": h.get("page",""),
                "header_lines": h.get("header_lines",""),
                "snippet": h.get("snippet",""),
                "status": "CANDIDATE"
            })

    cols=["token","authority_ref","doc_id","page","header_lines","snippet","status"]
    with open(args.out,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for r in out_rows: w.writerow(r)

if __name__=="__main__":
    main()
