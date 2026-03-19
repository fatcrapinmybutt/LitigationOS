#!/usr/bin/env python3
"""
Vehicle Router Candidates v28 (NON-INTERPRETIVE; token-based retrieval)
Inputs:
--intents-jsonl: rows {intent_id, relief_text}
--forms-index-jsonl: output of forms_indexer
Output:
--out-json: vehicle_map_candidates with token overlap matches (NO legal standards)
"""
import argparse, json, os, re, sys

def read_jsonl(path):
    with open(path,"r",encoding="utf-8") as f:
        for ln in f:
            ln=ln.strip()
            if ln: yield json.loads(ln)

def toks(s):
    return set(re.findall(r"[A-Za-z0-9]{3,}", (s or "").lower()))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--intents-jsonl", required=True)
    ap.add_argument("--forms-index-jsonl", required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--topk", type=int, default=8)
    args=ap.parse_args()

    forms=list(read_jsonl(args.forms_index_jsonl))
    f_idx=[]
    for fr in forms:
        blob=" ".join((fr.get("filename") or "", fr.get("title_line") or "", " ".join(fr.get("extracted_tokens") or [])))
        f_idx.append((fr, toks(blob)))

    out=[]
    for ir in read_jsonl(args.intents_jsonl):
        itxt=ir.get("relief_text") or ""
        itoks=toks(itxt)
        scored=[]
        for fr,ft in f_idx:
            inter=len(itoks & ft)
            if inter>0:
                scored.append((inter, fr))
        scored=sorted(scored, key=lambda x:(-x[0], x[1].get("form_id") or x[1].get("filename") or ""))[:args.topk]
        matches=[{"score":s,"form_id":fr.get("form_id") or "","file_path":fr.get("file_path"),"filename":fr.get("filename"),"title_line":fr.get("title_line")} for s,fr in scored]
        out.append({
            "intent_id": ir.get("intent_id") or "",
            "relief_text": itxt,
            "vehicle_candidates": matches
        })

    json.dump({"vehicle_router_version":"v28","candidates":out}, open(args.out_json,"w",encoding="utf-8"), indent=2)
    print(f"OK intents={len(out)}")

if __name__=="__main__":
    main()
