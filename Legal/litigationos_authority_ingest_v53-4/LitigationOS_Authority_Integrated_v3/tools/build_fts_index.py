#!/usr/bin/env python3
import argparse, os, sqlite3, sys
def die(msg, code=2):
    print(msg, file=sys.stderr); raise SystemExit(code)
def main():
    ap=argparse.ArgumentParser(description="Build/refresh FTS5 index over shards (non-interpretive)")
    ap.add_argument("--db", required=True)
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args=ap.parse_args()
    if not os.path.exists(args.db) or os.path.getsize(args.db)==0: die(f"DB not found/empty: {args.db}")
    con=sqlite3.connect(args.db); cur=con.cursor()
    cur.execute("PRAGMA journal_mode=WAL;"); cur.execute("PRAGMA synchronous=NORMAL;")
    if args.rebuild:
        cur.execute("DROP TABLE IF EXISTS shards_fts;")
        cur.execute("DROP TABLE IF EXISTS shards_fts_vocab;")
        con.commit()
    cur.execute("CREATE VIRTUAL TABLE IF NOT EXISTS shards_fts USING fts5(authority_ref UNINDEXED, text, tokenize='unicode61');")
    con.commit()
    cur.execute("SELECT COUNT(1) FROM shards_fts;"); fts_count=cur.fetchone()[0]
    if fts_count==0 or args.rebuild:
        cur.execute("DELETE FROM shards_fts;"); con.commit()
        q="SELECT authority_ref, text FROM shards"
        if args.limit and args.limit>0:
            q += " LIMIT ?"; cur.execute(q,(args.limit,))
        else:
            cur.execute(q)
        rows=cur.fetchall()
        cur.executemany("INSERT INTO shards_fts(authority_ref, text) VALUES (?, ?);", [(r[0], r[1] or "") for r in rows])
        con.commit()
    cur.execute("CREATE VIRTUAL TABLE IF NOT EXISTS shards_fts_vocab USING fts5vocab(shards_fts, 'row');")
    con.commit()
    cur.execute("SELECT COUNT(1) FROM shards;"); shard_count=cur.fetchone()[0]
    cur.execute("SELECT COUNT(1) FROM shards_fts;"); fts_count2=cur.fetchone()[0]
    print(f"OK shards={shard_count} fts={fts_count2}")
    con.close()
if __name__=="__main__":
    main()
