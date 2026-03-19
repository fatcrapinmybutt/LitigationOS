#!/usr/bin/env python3
import argparse, os, sqlite3, sys, csv
def die(msg, code=2):
    print(msg, file=sys.stderr); raise SystemExit(code)
def main():
    ap=argparse.ArgumentParser(description="Authority Search CLI (FTS5) - non-interpretive retrieval")
    ap.add_argument("--db", required=True)
    ap.add_argument("--q", required=True)
    ap.add_argument("--limit", type=int, default=25)
    ap.add_argument("--authority-ref-prefix", default="")
    ap.add_argument("--out-csv", default="")
    args=ap.parse_args()
    if not os.path.exists(args.db) or os.path.getsize(args.db)==0: die(f"DB not found/empty: {args.db}")
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='shards_fts';")
    if not cur.fetchone(): die("FTS table shards_fts not found. Run build_fts_index.py first.")
    where=""; params=[]
    if args.authority_ref_prefix:
        where=" AND authority_ref LIKE ?"; params.append(args.authority_ref_prefix + "%")
    sql=f"""
    SELECT authority_ref, snippet(shards_fts, 1, '[', ']', ' … ', 20) AS snippet, bm25(shards_fts) AS score
    FROM shards_fts
    WHERE shards_fts MATCH ? {where}
    ORDER BY score
    LIMIT ?;
    """
    params=[args.q] + params + [args.limit]
    cur.execute(sql, params)
    rows=cur.fetchall()
    out=[{"authority_ref":r["authority_ref"],"score":r["score"],"snippet":r["snippet"]} for r in rows]
    if args.out_csv:
        with open(args.out_csv,"w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f, fieldnames=["authority_ref","score","snippet"]); w.writeheader()
            for rr in out: w.writerow(rr)
    for rr in out[: min(len(out), 25)]:
        print(f'{rr["authority_ref"]}\t{rr["score"]}\t{rr["snippet"]}')
    con.close()
if __name__=="__main__":
    main()
