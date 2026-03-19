#!/usr/bin/env python3
"""
Draft Validator (FAIL-CLOSED v17)
- Fact lines require [FACT:<pinpoint>]
- Authority excerpt lines require [AUTH:<authority_ref>|<anchor_token>]
- "Naked" MCR/MCL/MRE citations are disallowed unless:
  - the line has [AUTH:...] OR
  - the line contains [TOKEN_ONLY] marker (catalog token, not an asserted citation)
Outputs validation_report.json and validation_issues.csv.
"""
import argparse, os, re, json, csv, sys

FACT_TAG=re.compile(r'\[FACT:([^\]]+)\]')
AUTH_TAG=re.compile(r'\[AUTH:([^\]|]+)\|([^\]]+)\]')
NAKED_CIT=re.compile(r'\b(MCR|MCL|MRE)\s+\d+(\.\d+)?(\([A-Za-z0-9]+\))*\b')

def main():
    ap=argparse.ArgumentParser(description="Validate locked draft backlink discipline.")
    ap.add_argument("--draft-txt", required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-csv", required=True)
    args=ap.parse_args()

    if not os.path.exists(args.draft_txt) or os.path.getsize(args.draft_txt)==0:
        print("draft missing/empty", file=sys.stderr); raise SystemExit(2)

    issues=[]
    with open(args.draft_txt,"r",encoding="utf-8") as f:
        lines=f.read().splitlines()

    in_facts=False
    in_auth=False
    for idx,line in enumerate(lines,1):
        s=line.strip()
        if s.startswith("II. Facts"):
            in_facts=True; in_auth=False; continue
        if s.startswith("III. Authority"):
            in_auth=True; in_facts=False; continue
        if s.startswith("IV."):
            in_facts=False; in_auth=False

        if in_facts:
            if not s: continue
            if not FACT_TAG.search(s):
                issues.append({"line":idx,"type":"MISSING_FACT_PINPOINT","detail":"Fact line missing [FACT:<pinpoint>] backlink.","text":s})
        if in_auth:
            if not s: continue
            if s[0].isdigit() and ". " in s:
                if not AUTH_TAG.search(s):
                    issues.append({"line":idx,"type":"MISSING_AUTH_BACKLINK","detail":"Authority excerpt line missing [AUTH:<authority_ref>|<anchor_token>].","text":s})

        # naked citation check
        if NAKED_CIT.search(s) and (not AUTH_TAG.search(s)) and ("[TOKEN_ONLY]" not in s):
            issues.append({"line":idx,"type":"NAKED_CITATION","detail":"Line contains MCR/MCL/MRE citation without [AUTH:...] backlink and not marked [TOKEN_ONLY].","text":s})

    status="PASS" if len(issues)==0 else "FAIL"
    rep={"status":status,"issues":issues,"issue_count":len(issues)}
    with open(args.out_json,"w",encoding="utf-8") as f:
        json.dump(rep,f,indent=2,ensure_ascii=False)

    with open(args.out_csv,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=["line","type","detail","text"]); w.writeheader()
        for it in issues: w.writerow(it)

    print(f"OK {status} issues={len(issues)}")

if __name__=="__main__":
    main()
