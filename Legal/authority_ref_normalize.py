#!/usr/bin/env python3
"""
Authority Ref Normalizer v30 (NON-INTERPRETIVE)
Normalizes authority_ref variants to canonical "DOCID::pNNN".
"""
import argparse, json, re, sys
RX=re.compile(r'^(?P<doc>.+?)(::|:)\s*p?(?P<page>\d+)\s*$', re.IGNORECASE)

def norm_ref(x):
    if isinstance(x, dict):
        d=(x.get("doc_id") or "").strip()
        p=x.get("page")
        if d and isinstance(p,int): return f"{d}::p{p}"
        return ""
    s=(x or "").strip()
    if not s: return ""
    m=RX.match(s)
    if not m: return ""
    d=m.group("doc").strip()
    p=int(m.group("page"))
    return f"{d}::p{p}" if d else ""

def read_jsonl(path):
    with open(path,"r",encoding="utf-8") as f:
        for ln in f:
            ln=ln.strip()
            if ln: yield json.loads(ln)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--in-jsonl", required=True)
    ap.add_argument("--field", required=True)
    ap.add_argument("--out-jsonl", required=True)
    args=ap.parse_args()

    n=0
    with open(args.out_jsonl,"w",encoding="utf-8") as out:
        for row in read_jsonl(args.in_jsonl):
            orig=row.get(args.field)
            nref=norm_ref(orig)
            row["_authority_ref_original"]=orig
            row[args.field]=nref or (orig if isinstance(orig,str) else "")
            out.write(json.dumps(row, ensure_ascii=False)+"\n")
            n+=1
    print(f"OK rows={n}")

if __name__=="__main__":
    main()
