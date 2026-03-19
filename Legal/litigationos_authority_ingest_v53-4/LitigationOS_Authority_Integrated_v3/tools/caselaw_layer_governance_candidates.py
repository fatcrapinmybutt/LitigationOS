#!/usr/bin/env python3
"""
Caselaw Layer Governance v25 (CANDIDATE-ONLY)
Adds governance fields based on user-supplied metadata (no web lookups).
"""
import argparse, json, os, sys

def read_jsonl(path):
    with open(path,"r",encoding="utf-8") as f:
        for ln in f:
            ln=ln.strip()
            if ln:
                yield json.loads(ln)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--cases-jsonl", required=True)
    ap.add_argument("--out-jsonl", required=True)
    args=ap.parse_args()

    if not os.path.exists(args.cases_jsonl) or os.path.getsize(args.cases_jsonl)==0:
        print("missing/empty cases-jsonl", file=sys.stderr)
        raise SystemExit(2)

    out=[]
    for row in read_jsonl(args.cases_jsonl):
        court=(row.get("court") or "").strip().upper()
        pub=row.get("published")
        weight="UNKNOWN"
        if court=="MSC":
            weight="MSC_CONTROLLING"
        elif court=="COA":
            if pub is True:
                weight="COA_PUBLISHED"
            elif pub is False:
                weight="COA_UNPUBLISHED_PERSUASIVE"
        row2=dict(row)
        row2["authority_weight"]=weight
        row2["required_pinpoint"]=True
        row2["holding_only_gate"]=True
        row2["status_flag"]= (row.get("status") or "UNKNOWN")
        out.append(row2)

    with open(args.out_jsonl,"w",encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"OK rows={len(out)}")

if __name__=="__main__":
    main()
