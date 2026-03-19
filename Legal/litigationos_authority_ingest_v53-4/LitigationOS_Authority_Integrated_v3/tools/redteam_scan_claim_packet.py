#!/usr/bin/env python3
"""
Red-Team Scan v24 (COMPLIANCE)
"""
import argparse, json, csv, os, re, sys

PLACEHOLDER=re.compile(r'(TODO|TKTK|\[INSERT[^\]]*\]|<[^>]{1,80}>|\?\?\?)', re.IGNORECASE)
HEDGE=re.compile(r'\b(likely|probably|seems|i think|i believe|maybe|could be)\b', re.IGNORECASE)

def load_first_jsonl(path):
    for ln in open(path,"r",encoding="utf-8"):
        ln=ln.strip()
        if ln: return json.loads(ln)
    return None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--claim-packets-jsonl", required=True)
    ap.add_argument("--draft-txt", default="")
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-csv", required=True)
    args=ap.parse_args()

    if not os.path.exists(args.claim_packets_jsonl) or os.path.getsize(args.claim_packets_jsonl)==0:
        print("missing/empty claim packets", file=sys.stderr); raise SystemExit(2)
    pkt=load_first_jsonl(args.claim_packets_jsonl)
    if not pkt:
        print("no claim packet", file=sys.stderr); raise SystemExit(2)

    issues=[]
    for i,f in enumerate(pkt.get("evidence_facts") or [],1):
        if not (f.get("pinpoint") or "").strip():
            issues.append({"severity":"FAIL","type":"MISSING_FACT_PINPOINT","detail":f"fact[{i}] missing pinpoint"})
    for i,p in enumerate(pkt.get("authority_propositions") or [],1):
        if not (p.get("authority_ref") or "").strip() or not (p.get("anchor_token") or "").strip():
            issues.append({"severity":"FAIL","type":"MISSING_AUTH_FIELDS","detail":f"prop[{i}] missing authority_ref or anchor_token"})

    blob=json.dumps(pkt, ensure_ascii=False)
    m=PLACEHOLDER.search(blob)
    if m: issues.append({"severity":"FAIL","type":"PLACEHOLDER_TOKEN","detail":f"found '{m.group(0)}' in claim packet"})
    mh=HEDGE.search(blob)
    if mh: issues.append({"severity":"WARN","type":"HEDGE_LANGUAGE","detail":f"found '{mh.group(0)}' in claim packet"})

    if args.draft_txt and os.path.exists(args.draft_txt) and os.path.getsize(args.draft_txt)>0:
        txt=open(args.draft_txt,"r",encoding="utf-8",errors="ignore").read()
        md=PLACEHOLDER.search(txt)
        if md: issues.append({"severity":"FAIL","type":"PLACEHOLDER_TOKEN_DRAFT","detail":f"found '{md.group(0)}' in draft"})
        mhd=HEDGE.search(txt)
        if mhd: issues.append({"severity":"WARN","type":"HEDGE_LANGUAGE_DRAFT","detail":f"found '{mhd.group(0)}' in draft"})

    status="FAIL" if any(i["severity"]=="FAIL" for i in issues) else "PASS"
    rep={"status":status,"issue_count":len(issues),"issues":issues}
    json.dump(rep, open(args.out_json,"w",encoding="utf-8"), indent=2)
    with open(args.out_csv,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=["severity","type","detail"]); w.writeheader()
        for it in issues: w.writerow(it)
    print(f"OK {status} issues={len(issues)}")

if __name__=="__main__":
    main()
