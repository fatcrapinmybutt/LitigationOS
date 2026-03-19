#!/usr/bin/env python3
import argparse, json, os, sys, re
REF1=re.compile(r'^(?P<doc>.+?)(::|:)\s*p?(?P<page>\d+)\s*$', re.IGNORECASE)

def parse_ref(s):
    s=(s or "").strip()
    if not s: return "", None
    m=REF1.match(s)
    if m:
        return m.group("doc").strip(), int(m.group("page"))
    return "", None

def read_first_jsonl(path):
    for ln in open(path,"r",encoding="utf-8"):
        ln=ln.strip()
        if ln: return json.loads(ln)
    return None

def main():
    ap=argparse.ArgumentParser(description="Reopen Recipe Builder v27")
    ap.add_argument("--claim-packets-jsonl", required=True)
    ap.add_argument("--authority-store", required=True)
    ap.add_argument("--authority-cli", default="tools/authority_query_cli.py")
    ap.add_argument("--out-json", required=True)
    args=ap.parse_args()

    if not os.path.exists(args.claim_packets_jsonl) or os.path.getsize(args.claim_packets_jsonl)==0:
        print("missing claim packet", file=sys.stderr); raise SystemExit(2)

    pkt=read_first_jsonl(args.claim_packets_jsonl)
    if not pkt:
        print("no claim packet row", file=sys.stderr); raise SystemExit(2)

    auth_cmds=[]
    seen=set()
    for pr in (pkt.get("authority_propositions") or []):
        ref=pr.get("authority_ref") or ""
        doc,page=parse_ref(ref)
        if doc and page is not None:
            key=(doc,page)
            if key in seen: 
                continue
            seen.add(key)
            auth_cmds.append({
                "authority_ref": f"{doc}::p{page}",
                "cmd": f'python "{args.authority_cli}" --db "{args.authority_store}" --q "{doc}" --page {page} --max-results 1'
            })

    facts=[]
    for fc in (pkt.get("evidence_facts") or []):
        facts.append({"fact_id": fc.get("fact_id") or fc.get("id") or "", "pinpoint": fc.get("pinpoint") or ""})

    recipe={
        "recipe_type":"REOPEN_RECIPE_V27",
        "source_claim_packet_id": pkt.get("claim_packet_id") or "",
        "authority_reopen": auth_cmds,
        "fact_pinpoints": facts
    }
    json.dump(recipe, open(args.out_json,"w",encoding="utf-8"), indent=2)
    print(f"OK authority_cmds={len(auth_cmds)} facts={len(facts)}")

if __name__=="__main__":
    main()
