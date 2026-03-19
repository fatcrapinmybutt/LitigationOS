#!/usr/bin/env python3
import argparse, csv, os, re, sqlite3, sys, json
def die(msg, code=2):
    print(msg, file=sys.stderr); raise SystemExit(code)
PATTERNS=[
    ("MCR", re.compile(r'\bMCR\s+(\d+(?:\.\d+)?(?:\([A-Za-z0-9]+\))*)\b')),
    ("MCL", re.compile(r'\bMCL\s+(\d+(?:\.\d+)?[A-Za-z0-9\.\-]*)\b')),
    ("MRE", re.compile(r'\bMRE\s+(\d{3})\b')),
    ("MJI", re.compile(r'\bMJI\s+(\d+(?:\.\d+)*)\b')),
    ("SCAO_FORM", re.compile(r'\b(MC|FOC|CC|DC)\s*\d+[A-Za-z]?\b')),
    ("USC", re.compile(r'\b\d+\s+USC\s+\d+[A-Za-z0-9\-]*\b')),
]
def snippet_window(txt, start, end, radius=70):
    a=max(0,start-radius); b=min(len(txt), end+radius)
    return txt[a:b].replace("\n"," ")
def main():
    ap=argparse.ArgumentParser(description="Authority Anchor Extractor (non-interpretive)")
    ap.add_argument("--db", required=True)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out-csv", required=True)
    ap.add_argument("--out-jsonl", required=True)
    args=ap.parse_args()
    if not os.path.exists(args.db) or os.path.getsize(args.db)==0: die("DB missing/empty")
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row
    cur=con.cursor()
    q="SELECT authority_ref, text FROM shards"
    if args.limit and args.limit>0:
        q += " LIMIT ?"; cur.execute(q,(args.limit,))
    else:
        cur.execute(q)
    seen=set(); rows=[]
    for r in cur.fetchall():
        ref=r["authority_ref"]; txt=(r["text"] or "")
        for kind, rx in PATTERNS:
            for m in rx.finditer(txt):
                token=(m.group(0) or "").strip()
                if not token: continue
                key=(ref, kind, token)
                if key in seen: continue
                seen.add(key)
                rows.append({
                    "authority_ref":ref,
                    "anchor_kind":kind,
                    "anchor_token":token,
                    "context_snippet":snippet_window(txt, m.start(), m.end()),
                    "status":"EXTRACTED_NO_INTERPRETATION"
                })
    fields=["authority_ref","anchor_kind","anchor_token","context_snippet","status"]
    with open(args.out_csv,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for rr in rows: w.writerow(rr)
    with open(args.out_jsonl,"w",encoding="utf-8") as f:
        for rr in rows:
            f.write(json.dumps(rr, ensure_ascii=False)+"\n")
    con.close()
if __name__=="__main__":
    main()
