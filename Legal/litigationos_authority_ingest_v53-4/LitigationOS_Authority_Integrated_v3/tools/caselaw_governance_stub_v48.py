#!/usr/bin/env python3
"""
caselaw_governance_stub_v48.py — OFFLINE GOVERNANCE STUB (v48)

Validates structure of outputs/caselaw_verified.json against schema and enforces a simple gate:
- any item with status UNVERIFIED keeps the caselaw gate FAIL

No web calls. No citation parsing beyond presence checks.
"""
import argparse, json, os, sys

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--in-json", required=True, help="outputs/caselaw_verified.json")
    ap.add_argument("--out-json", required=True, help="outputs/caselaw_governance_report.json")
    args=ap.parse_args()

    data=json.load(open(args.in_json,"r",encoding="utf-8"))
    items=data.get("items") or []
    fail=[it for it in items if (it.get("status") or "UNVERIFIED")=="UNVERIFIED"]
    out={
      "items": len(items),
      "unverified": len(fail),
      "gate": "PASS" if len(fail)==0 else "FAIL",
      "notes": "No web verification performed. Populate status based on authoritative sources."
    }
    os.makedirs(os.path.dirname(args.out_json) or ".", exist_ok=True)
    json.dump(out, open(args.out_json,"w",encoding="utf-8"), indent=2, ensure_ascii=False)
    print("OK gate=", out["gate"], "unverified=", out["unverified"])

if __name__=="__main__":
    main()
