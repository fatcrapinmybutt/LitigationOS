#!/usr/bin/env python3
"""
Authority Anchor FTS Builder v30 (NON-INTERPRETIVE)
Builds SQLite DB with FTS5 table for fast lexical search.
"""
import argparse, json, os, sqlite3, sys

def read_jsonl(path):
    with open(path,"r",encoding="utf-8") as f:
        for ln in f:
            ln=ln.strip()
            if ln: yield json.loads(ln)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--index-jsonl", required=True)
    ap.add_argument("--out-sqlite", required=True)
    args=ap.parse_args()

    if not os.path.exists(args.index_jsonl) or os.path.getsize(args.index_jsonl)==0:
        print("missing index jsonl", file=sys.stderr); raise SystemExit(2)

    if os.path.exists(args.out_sqlite):
        os.remove(args.out_sqlite)

    con=sqlite3.connect(args.out_sqlite)
    cur=con.cursor()
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute("CREATE TABLE pages(authority_ref TEXT PRIMARY KEY, doc_id TEXT, page INTEGER, header_lines TEXT, anchors_text TEXT);")
    cur.execute("CREATE VIRTUAL TABLE fts_pages USING fts5(header_lines, anchors_text, content='pages', content_rowid='rowid');")

    n=0
    for row in read_jsonl(args.index_jsonl):
        ref=row.get("authority_ref") or ""
        doc=row.get("doc_id") or ""
        page=int(row.get("page") or 0)
        hdr=row.get("header_lines") or ""
        anchors=row.get("anchors") or []
        anchors_text=" ".join([(a.get("token") or "") for a in anchors if (a.get("token") or "").strip()])[:5000]
        cur.execute("INSERT INTO pages(authority_ref, doc_id, page, header_lines, anchors_text) VALUES (?,?,?,?,?)", (ref,doc,page,hdr,anchors_text))
        cur.execute("INSERT INTO fts_pages(rowid, header_lines, anchors_text) VALUES (last_insert_rowid(), ?, ?)", (hdr,anchors_text))
        n+=1
        if n % 5000 == 0:
            con.commit()

    con.commit()
    cur.execute("INSERT INTO fts_pages(fts_pages) VALUES('optimize');")
    con.commit()
    con.close()
    print(f"OK pages_indexed={n}")

if __name__=="__main__":
    main()
