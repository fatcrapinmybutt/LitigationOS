#!/usr/bin/env python3
"""
Claim/Ground Harvester (non-interpretive)
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
    match=fts_match(q)
    cur=con.cursor()
    cur.execute("""
      SELECT s.authority_ref, snippet(shards_fts, 3, '[', ']', '…', 10) AS snippet
      FROM shards_fts
      JOIN shards s ON s.authority_ref = shards_fts.authority_ref
      WHERE shards_fts MATCH ?
      LIMIT ?;
    """,(match,k))
    return [dict(r) for r in cur.fetchall()]

def main():
    p=argparse.ArgumentParser(description="Claim/Ground Harvester (non-interpretive)")
    p.add_argument("--db", required=True)
    p.add_argument("--lens", required=True)
    p.add_argument("--k", type=int, default=10)
    p.add_argument("--out", required=True)
    args=p.parse_args()

    lens=json.load(open(args.lens,"r",encoding="utf-8"))
    tokens=list(lens.get("tokens") or [])
    con=connect(args.db)

    rows=[]
    for t in tokens:
        for h in run_query(con, t, args.k):
            rows.append({
                "claim_label_candidate":"",
                "element_token_candidate": t,
                "authority_ref": h.get("authority_ref",""),
                "snippet": h.get("snippet",""),
                "status":"CANDIDATE"
            })

    cols=["claim_label_candidate","element_token_candidate","authority_ref","snippet","status"]
    with open(args.out,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for r in rows: w.writerow(r)

if __name__=="__main__":
    main()
