#!/usr/bin/env python3
"""
Issue Packet Validator v23 (FAIL-CLOSED completeness)
"""
import argparse, json, csv, os, sys

def load_first_jsonl(path):
    for ln in open(path,"r",encoding="utf-8"):
        ln=ln.strip()
        if not ln: continue
        return json.loads(ln)
    return None

def main():
    ap=argparse.ArgumentParser(description="Validate issue packet completeness.")
    ap.add_argument("--issue-packets-jsonl", required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-csv", required=True)
    args=ap.parse_args()

    if not os.path.exists(args.issue_packets_jsonl) or os.path.getsize(args.issue_packets_jsonl)==0:
        print("missing/empty issue packets", file=sys.stderr); raise SystemExit(2)

    pkt=load_first_jsonl(args.issue_packets_jsonl)
    if not pkt:
        print("no packets", file=sys.stderr); raise SystemExit(2)

    issues=[]
    facts=pkt.get("evidence_facts") or []
    props=pkt.get("authority_propositions") or []
    for i,f in enumerate(facts,1):
        if not (f.get("pinpoint") or "").strip():
            issues.append({"type":"MISSING_FACT_PINPOINT","detail":f"fact[{i}] missing pinpoint"})
    for i,p in enumerate(props,1):
        if not (p.get("authority_ref") or "").strip() or not (p.get("anchor_token") or "").strip():
            issues.append({"type":"MISSING_AUTH_FIELDS","detail":f"prop[{i}] missing authority_ref or anchor_token"})

    status="PASS" if not issues else "FAIL"
    json.dump({"status":status,"issue_count":len(issues),"issues":issues},
              open(args.out_json,"w",encoding="utf-8"), indent=2)
    with open(args.out_csv,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=["type","detail"]); w.writeheader()
        for it in issues: w.writerow(it)

    print(f"OK {status} issues={len(issues)}")

if __name__=="__main__":
    main()
