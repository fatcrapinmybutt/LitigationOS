#!/usr/bin/env python3
"""
Deadline Validator (FAIL-CLOSED on completeness, not law)
- Flags rows missing authority_anchor_token AND missing service_method_anchor_token.
- Flags rows missing source_pinpoint.
Outputs: deadline_validation_report.json + issues.csv
"""
import argparse, csv, json, os, sys

def main():
    ap=argparse.ArgumentParser(description="Validate deadline candidates for completeness.")
    ap.add_argument("--deadlines-csv", required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-csv", required=True)
    args=ap.parse_args()

    if not os.path.exists(args.deadlines_csv) or os.path.getsize(args.deadlines_csv)==0:
        print("deadlines missing/empty", file=sys.stderr); raise SystemExit(2)

    issues=[]
    rows=list(csv.DictReader(open(args.deadlines_csv,"r",encoding="utf-8")))
    for i,r in enumerate(rows,1):
        if not (r.get("authority_anchor_token") or "").strip() and not (r.get("service_method_anchor_token") or "").strip():
            issues.append({"row":i,"type":"MISSING_AUTH_ANCHOR","detail":"No anchor token provided for base or service method."})
        if not (r.get("source_pinpoint") or "").strip():
            issues.append({"row":i,"type":"MISSING_SOURCE_PINPOINT","detail":"No source pinpoint for triggering event."})

    status="PASS" if not issues else "FAIL"
    rep={"status":status,"issue_count":len(issues),"issues":issues}
    json.dump(rep, open(args.out_json,"w",encoding="utf-8"), indent=2)

    with open(args.out_csv,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=["row","type","detail"]); w.writeheader()
        for it in issues: w.writerow(it)

    print(f"OK {status} issues={len(issues)} rows={len(rows)}")

if __name__=="__main__":
    main()
