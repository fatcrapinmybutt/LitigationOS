#!/usr/bin/env python3
"""
Authority Anchor Search v29 (NON-INTERPRETIVE)

Searches authority_anchor_index.jsonl by:
- exact/substring match in anchors.token
- fallback match in header_lines

Inputs:
--index-jsonl (from authority_anchor_index_from_db.py)
--q query string (tokens separated by space)
Outputs:
--out-json results (ranked)
"""
import argparse, json, os, re, sys

def read_jsonl(path):
    with open(path,"r",encoding="utf-8") as f:
        for ln in f:
            ln=ln.strip()
            if ln: yield json.loads(ln)

def score_row(row, q):
    ql=q.lower().strip()
    if not ql:
        return 0
    score=0
    # anchors
    for a in row.get("anchors") or []:
        tok=(a.get("token") or "").lower()
        if not tok:
            continue
        if tok==ql:
            score += 50
        elif ql in tok:
            score += 20
    # header lines
    hdr=(row.get("header_lines") or "").lower()
    if ql and ql in hdr:
        score += 5
    # multi-token bonus
    toks=[t.lower() for t in re.findall(r"[A-Za-z0-9.()]{2,}", q)]
    if len(toks)>1:
        bonus=0
        for t in toks:
            if t in hdr:
                bonus += 1
        score += bonus
    return score

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--index-jsonl", required=True)
    ap.add_argument("--q", required=True)
    ap.add_argument("--topk", type=int, default=25)
    ap.add_argument("--out-json", required=True)
    args=ap.parse_args()

    if not os.path.exists(args.index_jsonl) or os.path.getsize(args.index_jsonl)==0:
        print("missing index", file=sys.stderr); raise SystemExit(2)

    scored=[]
    for row in read_jsonl(args.index_jsonl):
        s=score_row(row, args.q)
        if s>0:
            scored.append((s, row.get("authority_ref"), row.get("header_lines","")))
    scored=sorted(scored, key=lambda x:(-x[0], x[1] or ""))[:args.topk]
    out=[{"score":s,"authority_ref":ref,"header_lines":hdr} for s,ref,hdr in scored]
    json.dump({"q":args.q,"topk":args.topk,"results":out}, open(args.out_json,"w",encoding="utf-8"), indent=2)
    print(f"OK results={len(out)}")

if __name__=="__main__":
    main()
