#!/usr/bin/env python3
import argparse, csv, os, re, sqlite3, sys

def die(msg, code=2):
    print(msg, file=sys.stderr); raise SystemExit(code)

CIT_RE = re.compile(
    r'(?P<mich>\b\d{1,4}\s+Mich(?:\s+App)?\s+\d{1,5}\b(?:\s*\(\d{4}\))?)'
    r'|(?P<nw>\b\d{1,4}\s+NW2d\s+\d{1,5}\b(?:\s*\(\d{4}\))?)',
    re.IGNORECASE
)

def connect(db):
    if not os.path.exists(db) or os.path.getsize(db)==0:
        die(f"DB not found/empty: {db}")
    con=sqlite3.connect(db); con.row_factory=sqlite3.Row; return con

def fetch_shards(con, limit=None):
    cur=con.cursor()
    q="SELECT authority_ref, text FROM shards"
    if limit:
        q += " LIMIT ?"
        cur.execute(q,(limit,))
    else:
        cur.execute(q)
    for r in cur.fetchall():
        yield r["authority_ref"], (r["text"] or "")

def scan_text_lines(path):
    with open(path,"r",encoding="utf-8",errors="replace") as f:
        for i,ln in enumerate(f, start=1):
            yield i, ln.rstrip("\n")

def snippet_around(s, start, end, radius=60):
    a=max(0,start-radius); b=min(len(s), end+radius)
    return s[a:b].replace("\n"," ")

def main():
    ap=argparse.ArgumentParser(description="Caselaw Citation Extractor (candidate-only)")
    ap.add_argument("--db", help="authority_store.sqlite")
    ap.add_argument("--db-limit", type=int, help="limit shards for testing")
    ap.add_argument("--text", help="text file to scan (pdftotext output, etc.)")
    ap.add_argument("--out-csv", required=True)
    args=ap.parse_args()

    if not args.db and not args.text:
        die("Provide --db and/or --text")

    rows=[]

    if args.db:
        con=connect(args.db)
        for authority_ref, txt in fetch_shards(con, args.db_limit):
            for m in CIT_RE.finditer(txt):
                cit=(m.group("mich") or m.group("nw") or "").strip()
                if not cit: continue
                rows.append({
                    "source_kind":"DB_SHARD",
                    "source_ref":authority_ref,
                    "citation":cit,
                    "context_snippet":snippet_around(txt, m.start(), m.end()),
                    "status":"CANDIDATE"
                })

    if args.text:
        if not os.path.exists(args.text):
            die(f"Text file not found: {args.text}")
        for line_no, ln in scan_text_lines(args.text):
            for m in CIT_RE.finditer(ln):
                cit=(m.group("mich") or m.group("nw") or "").strip()
                if not cit: continue
                src=f"{args.text}:{line_no}"
                rows.append({
                    "source_kind":"TEXT_FILE",
                    "source_ref":src,
                    "citation":cit,
                    "context_snippet":ln[max(0,m.start()-60):m.end()+60],
                    "status":"CANDIDATE"
                })

    seen=set()
    out=[]
    for r in rows:
        k=(r["source_ref"], r["citation"].lower())
        if k in seen: continue
        seen.add(k); out.append(r)

    fields=["source_kind","source_ref","citation","context_snippet","status"]
    with open(args.out_csv,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for r in out: w.writerow(r)

if __name__=="__main__":
    main()
