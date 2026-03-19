#!/usr/bin/env python3
"""
Authority Query CLI v23 (NON-INTERPRETIVE, schema-robust)
- Detects available columns in shards table.
- Always emits: authority_ref, page (if available), doc_id (if available), hit_text_snippet (direct extraction).
- Prefers shards_fts if present; else LIKE.
No rewriting/summarization.
"""
import argparse, os, sqlite3, json, re, sys

def die(msg, code=2):
    print(msg, file=sys.stderr); raise SystemExit(code)

def has_table(con, name):
    cur=con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (name,))
    return cur.fetchone() is not None

def table_cols(con, table):
    cur=con.cursor()
    cur.execute(f"PRAGMA table_info({table});")
    return [r[1] for r in cur.fetchall()]

def main():
    ap=argparse.ArgumentParser(description="Authority retrieval (local).")
    ap.add_argument("--db", required=True)
    ap.add_argument("--q", default="", help="keyword query")
    ap.add_argument("--authority-ref", default="", help="restrict to authority_ref")
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--out-jsonl", required=True)
    args=ap.parse_args()

    if not os.path.exists(args.db) or os.path.getsize(args.db)==0:
        die("db missing/empty")
    con=sqlite3.connect(args.db)
    con.row_factory=sqlite3.Row
    if not has_table(con,"shards"):
        die("missing shards table")

    cols=table_cols(con,"shards")
    has_doc="doc_id" in cols
    has_page="page" in cols
    text_col="text" if "text" in cols else ("page_text" if "page_text" in cols else None)
    if not text_col:
        die("no text column in shards")

    # build select list
    select=["authority_ref"]
    if has_doc: select.append("doc_id")
    if has_page: select.append("page")
    select.append(text_col + " AS txt")

    q=(args.q or "").strip()
    aref=(args.authority_ref or "").strip()

    def snippet(txt, q):
        if not q:
            return ([], (txt or "")[:240].replace("\n"," "))
        m=re.search(re.escape(q), txt or "", flags=re.IGNORECASE)
        if not m:
            return ([], (txt or "")[:240].replace("\n"," "))
        a=max(0, m.start()-180); b=min(len(txt), m.end()+180)
        return ([{"start":m.start(),"end":m.end()}], (txt or "")[a:b].replace("\n"," "))

    cur=con.cursor()
    rows=[]
    if q and has_table(con,"shards_fts"):
        # Try fts: assume it has authority_ref and text
        sql=f"SELECT {', '.join(select)} FROM shards_fts WHERE shards_fts MATCH ?"
        params=[q]
        if aref:
            sql += " AND authority_ref=?"
            params.append(aref)
        sql += " LIMIT ?"
        params.append(args.limit)
        try:
            cur.execute(sql, params)
            rows=cur.fetchall()
        except Exception:
            rows=[]

    if not rows:
        sql=f"SELECT {', '.join(select)} FROM shards"
        params=[]
        if q:
            sql += f" WHERE {text_col} LIKE ?"
            params.append(f"%{q}%")
            if aref:
                sql += " AND authority_ref=?"
                params.append(aref)
        else:
            if aref:
                sql += " WHERE authority_ref=?"
                params.append(aref)
        sql += " LIMIT ?"
        params.append(args.limit)
        cur.execute(sql, params)
        rows=cur.fetchall()

    with open(args.out_jsonl,"w",encoding="utf-8") as f:
        for r in rows:
            spans,snip=snippet(r["txt"], q)
            out={
                "authority_ref": r["authority_ref"],
                "doc_id": r["doc_id"] if "doc_id" in r.keys() else "",
                "page": r["page"] if "page" in r.keys() else "",
                "hit_spans": spans,
                "hit_text_snippet": snip
            }
            f.write(json.dumps(out, ensure_ascii=False) + "\n")

    con.close()
    print(f"OK hits={len(rows)} cols={cols}")

if __name__=="__main__":
    main()
