#!/usr/bin/env python3
"""
Ensure Atom IDs v24
Adds stable-ish ids to issue/claim packets when missing:
- vehicle_id for vehicle candidates
- fact_id for evidence facts
- prop_id for authority propositions
Does not modify text/pinpoints.
"""
import argparse, json, os, sys, hashlib

def load_all_jsonl(path):
    out=[]
    with open(path,"r",encoding="utf-8") as f:
        for ln in f:
            ln=ln.strip()
            if ln: out.append(json.loads(ln))
    return out

def dump_jsonl(rows, path):
    with open(path,"w",encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def sid(prefix, s):
    h=hashlib.sha256((s or "").encode("utf-8")).hexdigest()[:16]
    return f"{prefix}-{h}"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--in-jsonl", required=True)
    ap.add_argument("--out-jsonl", required=True)
    args=ap.parse_args()
    if not os.path.exists(args.in_jsonl) or os.path.getsize(args.in_jsonl)==0:
        print("missing/empty input", file=sys.stderr); raise SystemExit(2)
    rows=load_all_jsonl(args.in_jsonl)
    for pkt in rows:
        for v in (pkt.get("vehicle_candidates") or []):
            if not (v.get("vehicle_id") or "").strip():
                key=json.dumps(v, sort_keys=True, ensure_ascii=False)
                v["vehicle_id"]=sid("VEH", key)
        for fct in (pkt.get("evidence_facts") or []):
            if not (fct.get("fact_id") or "").strip():
                key=(fct.get("pinpoint") or "") + "|" + (fct.get("text") or fct.get("fact_text") or "")
                fct["fact_id"]=sid("FACT", key)
        for pr in (pkt.get("authority_propositions") or []):
            if not (pr.get("prop_id") or "").strip():
                key=(pr.get("authority_ref") or "") + "|" + (pr.get("anchor_token") or "") + "|" + (pr.get("proposition_text") or pr.get("text") or "")
                pr["prop_id"]=sid("PROP", key)
    dump_jsonl(rows, args.out_jsonl)
    print(f"OK packets={len(rows)}")
if __name__=="__main__":
    main()
