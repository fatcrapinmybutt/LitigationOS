#!/usr/bin/env python3
import argparse, csv, os, sys

def die(msg, code=2):
    print(msg, file=sys.stderr); raise SystemExit(code)

def load_csv(p):
    with open(p,"r",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_csv(p, rows, fields):
    with open(p,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for r in rows: w.writerow(r)

def main():
    ap=argparse.ArgumentParser(description="Claim→Vehicle Router (candidate-only)")
    ap.add_argument("--claims", required=True)
    ap.add_argument("--vehicles", required=True)
    ap.add_argument("--out", required=True)
    args=ap.parse_args()

    if not os.path.exists(args.claims) or not os.path.exists(args.vehicles):
        die("Input CSV missing")

    claims=load_csv(args.claims)
    vehicles=load_csv(args.vehicles)

    v_by_ref={}
    for v in vehicles:
        ar=(v.get("authority_ref") or "").strip()
        if not ar: continue
        v_by_ref.setdefault(ar,[]).append(v)

    rows=[]
    for c in claims:
        ar=(c.get("authority_ref") or "").strip()
        if not ar or ar not in v_by_ref: continue
        for v in v_by_ref[ar]:
            rows.append({
                "claim_label_candidate": c.get("claim_label_candidate",""),
                "element_token_candidate": c.get("element_token_candidate",""),
                "vehicle_name_candidate": v.get("vehicle_name_candidate",""),
                "form_candidate": v.get("form_candidate",""),
                "rule_candidate_token": v.get("rule_candidate_token",""),
                "authority_ref": ar,
                "status": "CANDIDATE"
            })

    fields=["claim_label_candidate","element_token_candidate","vehicle_name_candidate","form_candidate","rule_candidate_token","authority_ref","status"]
    write_csv(args.out, rows, fields)

if __name__=="__main__":
    main()
