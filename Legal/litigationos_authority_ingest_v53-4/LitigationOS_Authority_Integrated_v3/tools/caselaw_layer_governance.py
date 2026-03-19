#!/usr/bin/env python3
"""
Caselaw Layer Governance (CANDIDATE-ONLY)
Goal: classify caselaw citations by court + publication status + precedential weight flags,
BUT ONLY from user-provided metadata (no web lookups).
Input:
- caselaw_citations.csv: citation, court (MSC/COA/Other), published (yes/no/unknown), status (good/overruled/unknown), holding_pinpoint (required to assert later)
Output:
- caselaw_governance.csv with computed flags.
"""
import argparse, csv, os, sys

def main():
    ap=argparse.ArgumentParser(description="Caselaw governance from user-provided metadata (candidate-only).")
    ap.add_argument("--in-csv", required=True)
    ap.add_argument("--out-csv", required=True)
    args=ap.parse_args()

    if not os.path.exists(args.in_csv) or os.path.getsize(args.in_csv)==0:
        print("input csv missing/empty", file=sys.stderr); raise SystemExit(2)

    rows=list(csv.DictReader(open(args.in_csv,"r",encoding="utf-8")))
    out=[]
    for r in rows:
        court=(r.get("court") or "unknown").strip().upper()
        published=(r.get("published") or "unknown").strip().lower()
        status=(r.get("status") or "unknown").strip().lower()
        holding=(r.get("holding_pinpoint") or "").strip()

        precedential="unknown"
        if court=="MSC":
            precedential="binding" if status!="overruled" else "not_binding"
        elif court=="COA":
            if published=="yes" and status!="overruled":
                precedential="binding"
            elif published=="no" and status!="overruled":
                precedential="persuasive_only"
            else:
                precedential="not_binding"

        assertable = "yes" if (holding and precedential in ("binding","persuasive_only")) else "no"

        out.append({
            "citation": (r.get("citation") or "").strip(),
            "court": court,
            "published": published,
            "status": status,
            "precedential_weight": precedential,
            "holding_pinpoint": holding,
            "assertable_holding_ready": assertable,
            "notes": (r.get("notes") or "").strip()
        })

    with open(args.out_csv,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=["citation","court","published","status","precedential_weight","holding_pinpoint","assertable_holding_ready","notes"])
        w.writeheader()
        for row in out: w.writerow(row)

    print(f"OK rows={len(out)}")

if __name__=="__main__":
    main()
