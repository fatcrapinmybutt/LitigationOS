#!/usr/bin/env python3
"""
Authority Anchor FTS Search v30 (NON-INTERPRETIVE)
Searches authority_anchor_fts.sqlite via FTS5 MATCH.
Sanitizes obvious unsupported operators (e.g., "NEAR/2" -> "NEAR").
"""
import argparse, json, os, sqlite3, sys, re

def sanitize(q):
    q=(q or "").strip()
    q=re.sub(r"NEAR/\d+", "NEAR", q, flags=re.IGNORECASE)
    q=q.replace("/", " ")
    return q

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--q", required=True)
    ap.add_argument("--topk", type=int, default=25)
    ap.add_argument("--out-json", required=True)
    args=ap.parse_args()

    if not os.path.exists(args.db) or os.path.getsize(args.db)==0:
        print("missing db", file=sys.stderr); raise SystemExit(2)

    q=sanitize(args.q)

    con=sqlite3.connect(args.db)
    cur=con.cursor()
    sql="""
    SELECT bm25(fts_pages) as score, pages.authority_ref, pages.doc_id, pages.page, pages.header_lines
    FROM fts_pages JOIN pages ON fts_pages.rowid = pages.rowid
    WHERE fts_pages MATCH ?
    ORDER BY score
    LIMIT ?
    """
    try:
        cur.execute(sql, (q, args.topk))
        rows=cur.fetchall()
    except sqlite3.OperationalError as e:
        # fail closed but return empty results with error field
        rows=[]
        err=str(e)
        con.close()
        json.dump({"q":args.q,"q_sanitized":q,"topk":args.topk,"error":err,"results":[]},
                  open(args.out_json,"w",encoding="utf-8"), indent=2)
        print("OK results=0 (error captured)")
        return
    con.close()

    out=[{"bm25":float(s),"authority_ref":ref,"doc_id":doc,"page":int(page),"header_lines":hdr} for s,ref,doc,page,hdr in rows]
    json.dump({"q":args.q,"q_sanitized":q,"topk":args.topk,"results":out}, open(args.out_json,"w",encoding="utf-8"), indent=2)
    print(f"OK results={len(out)}")

if __name__=="__main__":
    main()
