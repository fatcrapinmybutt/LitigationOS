#!/usr/bin/env python3
"""
Proposition Builder (authority-only, bounded, non-interpretive) v18
- Sanitizes anchor tokens to ensure no embedded newlines break [AUTH:ref|token] tags downstream.
"""
import argparse, os, re, sqlite3, sys, json, hashlib, csv

def die(msg, code=2):
    print(msg, file=sys.stderr); raise SystemExit(code)

def norm_ws(s: str) -> str:
    return re.sub(r'\s+', ' ', (s or '').strip())

def clean_token(s: str) -> str:
    # collapse any newlines/tabs into spaces, then normalize spaces
    return norm_ws((s or "").replace("\r"," ").replace("\n"," ").replace("\t"," "))

def window(txt, start, end, radius=220):
    a=max(0, start-radius); b=min(len(txt), end+radius)
    return norm_ws(txt[a:b])

def main():
    ap=argparse.ArgumentParser(description="Build authority proposition candidates from anchors + shard text (non-interpretive).")
    ap.add_argument("--db", required=True)
    ap.add_argument("--anchors-csv", required=True)
    ap.add_argument("--out-jsonl", required=True)
    ap.add_argument("--limit-anchors", type=int, default=0)
    args=ap.parse_args()

    if not os.path.exists(args.db) or os.path.getsize(args.db)==0:
        die("DB missing/empty")
    if not os.path.exists(args.anchors_csv) or os.path.getsize(args.anchors_csv)==0:
        die("anchors csv missing/empty")

    anchors=[]
    with open(args.anchors_csv,"r",encoding="utf-8") as f:
        for row in csv.DictReader(f):
            anchors.append(row)
    if args.limit_anchors and args.limit_anchors>0:
        anchors=anchors[:args.limit_anchors]

    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row
    cur=con.cursor()

    refs=sorted(set(a.get("authority_ref","") for a in anchors if a.get("authority_ref")))
    text_map={}
    for ref in refs:
        cur.execute("SELECT text FROM shards WHERE authority_ref=? LIMIT 1;", (ref,))
        r=cur.fetchone()
        text_map[ref]=(r["text"] if r else "") or ""

    out=[]
    seen=set()
    for a in anchors:
        ref=clean_token(a.get("authority_ref",""))
        kind=clean_token(a.get("anchor_kind",""))
        token=clean_token(a.get("anchor_token",""))
        if not ref or not token:
            continue
        txt=text_map.get(ref,"")
        idx=txt.find(token)
        if idx==-1:
            excerpt=""; start=0; end=0
        else:
            start=idx; end=idx+len(token)
            excerpt=window(txt, start, end, radius=260)

        prop_id=hashlib.sha256(f"{ref}|{kind}|{token}|{start}|{end}".encode("utf-8")).hexdigest()[:24]
        key=(ref, kind, token, start, end)
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "proposition_id": prop_id,
            "authority_ref": ref,
            "anchor_kind": kind,
            "anchor_token": token,
            "excerpt_window": excerpt,
            "excerpt_loc": {"start": start, "end": end},
            "status": "CANDIDATE_ONLY_NO_LEGAL_INFERENCE"
        })

    with open(args.out_jsonl,"w",encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    con.close()
    print(f"OK propositions={len(out)} refs={len(refs)}")

if __name__=="__main__":
    main()
