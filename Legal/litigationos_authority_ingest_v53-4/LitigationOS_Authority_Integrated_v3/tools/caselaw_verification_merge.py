#!/usr/bin/env python3
"""
caselaw_verification_merge.py (v41) — OFFLINE MERGE

Merges:
- governance output (v40): caselaw_governance_out.json
- verification list (operator-supplied): caselaw_verification_in.json

Purpose:
- Preserve separation: heuristics vs verified metadata
- Downstream gates can require verified==true before permitting case cite usage

No network calls; verification must be supplied (e.g., via separate web-verified workflow).
"""
import argparse, json

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--governance-json", required=True)
    ap.add_argument("--verification-json", required=True)
    ap.add_argument("--out-json", required=True)
    args=ap.parse_args()

    gov=json.load(open(args.governance_json,"r",encoding="utf-8"))
    ver=json.load(open(args.verification_json,"r",encoding="utf-8"))

    ver_map={}
    for it in (ver.get("items") or []):
        ct=(it.get("citation_text") or "").strip()
        if ct:
            ver_map[ct]=it

    out={"items":[],"meta":{"confidence":"CANDIDATE_ONLY","notes":"MERGED_GOVERNANCE_WITH_OPERATOR_VERIFICATION"}}
    for it in (gov.get("items") or []):
        ct=(it.get("citation_text") or "").strip()
        merged=dict(it)
        v=ver_map.get(ct)
        if v:
            merged["verification"]=v
        else:
            merged["verification"]={"verified":False,"notes":"MISSING_VERIFICATION"}
        out["items"].append(merged)

    json.dump(out, open(args.out_json,"w",encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"OK items={len(out['items'])}")

if __name__=="__main__":
    main()
