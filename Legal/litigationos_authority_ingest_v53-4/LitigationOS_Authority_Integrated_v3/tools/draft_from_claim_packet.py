#!/usr/bin/env python3
"""
Draft From Claim Packet (LOCKED v18)
- Sanitizes tokens/refs to prevent tag breakage.
"""
import argparse, json, os, re, sys

def die(msg, code=2):
    print(msg, file=sys.stderr); raise SystemExit(code)

def norm_ws(s: str) -> str:
    return re.sub(r'\s+', ' ', (s or '').strip())

def load_first_jsonl(path):
    with open(path,"r",encoding="utf-8") as f:
        for ln in f:
            ln=ln.strip()
            if not ln: continue
            return json.loads(ln)
    return None

def main():
    ap=argparse.ArgumentParser(description="Generate locked draft from claim packet JSONL.")
    ap.add_argument("--claim-packets-jsonl", required=True)
    ap.add_argument("--out-draft-txt", required=True)
    ap.add_argument("--title", default="DRAFT (LOCKED)")
    args=ap.parse_args()

    if not os.path.exists(args.claim_packets_jsonl) or os.path.getsize(args.claim_packets_jsonl)==0:
        die("claim packets missing/empty")
    pkt=load_first_jsonl(args.claim_packets_jsonl)
    if not pkt:
        die("no packet found")

    vehicle=pkt.get("vehicle") or {}
    props=pkt.get("authority_propositions") or []
    facts=pkt.get("evidence_facts") or []

    lines=[]
    lines.append(args.title)
    lines.append("")
    lines.append("I. Vehicle (candidate selected)")
    lines.append(f"- Vehicle Name: {norm_ws(vehicle.get('vehicle_name',''))}")
    lines.append(f"- Form Token: {norm_ws(vehicle.get('form_token',''))}")
    rat=norm_ws(vehicle.get('rule_anchor_token',''))
    if rat:
        lines.append(f"- Rule Anchor Token (catalog): {rat} [TOKEN_ONLY]")
    else:
        lines.append(f"- Rule Anchor Token (catalog): [NONE]")
    lines.append(f"- Prereqs (catalog): {norm_ws(vehicle.get('prereqs',''))} [TOKEN_ONLY]")
    lines.append("")
    lines.append("II. Facts (each requires pinpoint)")
    for i,fact in enumerate(facts,1):
        lines.append(f"{i}. {norm_ws(fact.get('fact_text',''))} [FACT:{norm_ws(fact.get('pinpoint',''))}]")
    lines.append("")
    lines.append("III. Authority excerpts (direct extraction only)")
    for i,p in enumerate(props,1):
        ref=norm_ws(p.get("authority_ref",""))
        tok=norm_ws(p.get("anchor_token",""))
        excerpt=norm_ws(p.get("excerpt_window",""))
        lines.append(f"{i}. [AUTH:{ref}|{tok}] {excerpt}")
    lines.append("")
    lines.append("IV. Requested Relief (candidate; no additional assertions)")
    lines.append("- The court should grant relief consistent with the selected Vehicle, supported by the cited Facts and Authority excerpts.")
    lines.append("")
    lines.append("END (LOCKED DRAFT)")

    with open(args.out_draft_txt,"w",encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("OK draft_written")

if __name__=="__main__":
    main()
