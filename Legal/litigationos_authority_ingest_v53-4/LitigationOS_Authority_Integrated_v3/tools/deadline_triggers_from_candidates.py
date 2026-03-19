#!/usr/bin/env python3
"""
Triggers Builder v26 (NON-INTERPRETIVE)
Converts deadlines_candidates.csv into triggers.csv for the compute engine when the
candidate row represents a trigger event (e.g., service date, order date).

This is intentionally conservative: it just copies explicit dates into trigger rows.
User should edit trigger_type as needed.

Input columns expected:
case_id, deadline_date, deadline_type, source_pinpoint, notes

Outputs:
trigger_id, trigger_date, trigger_type, source_pinpoint, notes
"""
import argparse, csv, os, sys

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--deadlines-candidates-csv", required=True)
    ap.add_argument("--trigger-type", required=True, help="literal trigger_type to assign to all rows")
    ap.add_argument("--out-triggers-csv", required=True)
    args=ap.parse_args()

    if not os.path.exists(args.deadlines_candidates_csv) or os.path.getsize(args.deadlines_candidates_csv)==0:
        print("missing/empty deadlines_candidates", file=sys.stderr); raise SystemExit(2)

    rows=[]
    with open(args.deadlines_candidates_csv,"r",encoding="utf-8",errors="ignore") as f:
        rdr=csv.DictReader(f)
        for idx,r in enumerate(rdr,1):
            dd=(r.get("deadline_date") or "").strip()
            if not dd: 
                continue
            rows.append({
                "trigger_id": f"TR-{idx:05d}",
                "trigger_date": dd,
                "trigger_type": args.trigger_type,
                "source_pinpoint": (r.get("source_pinpoint") or ""),
                "notes": (r.get("notes") or "")[:400]
            })

    with open(args.out_triggers_csv,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=["trigger_id","trigger_date","trigger_type","source_pinpoint","notes"])
        w.writeheader()
        for r in rows: w.writerow(r)

    print(f"OK triggers={len(rows)}")

if __name__=="__main__":
    main()
