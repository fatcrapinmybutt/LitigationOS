#!/usr/bin/env python3
"""
Claim Draft Candidates Assembler v28 (GATED; NON-INTERPRETIVE)

Purpose:
- Convert a claim_packet (already built) into 'claim_draft_candidates' rows.
- Does NOT create legal claims or elements. It only packages:
  - cited authority_refs
  - evidence_fact ids + pinpoints
  - explicit missing pinpoints (PINPOINT_MISSING)
Gate:
- Requires a PASS authority_ref_validation report or runs validator if requested.

Inputs:
--claim-packets-jsonl (first row)
--authority-ref-validation-json (required; must be PASS)
Output:
--out-jsonl claim_draft_candidates
"""
import argparse, json, os, sys

def read_first_jsonl(path):
    for ln in open(path,"r",encoding="utf-8"):
        ln=ln.strip()
        if ln: return json.loads(ln)
    return None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--claim-packets-jsonl", required=True)
    ap.add_argument("--authority-ref-validation-json", required=True)
    ap.add_argument("--out-jsonl", required=True)
    args=ap.parse_args()

    if not os.path.exists(args.claim_packets_jsonl) or os.path.getsize(args.claim_packets_jsonl)==0:
        print("missing claim packets", file=sys.stderr); raise SystemExit(2)
    if not os.path.exists(args.authority_ref_validation_json) or os.path.getsize(args.authority_ref_validation_json)==0:
        print("missing validation json", file=sys.stderr); raise SystemExit(2)

    rep=json.load(open(args.authority_ref_validation_json,"r",encoding="utf-8"))
    if rep.get("status")!="PASS":
        print("validation not PASS; refusing to assemble", file=sys.stderr)
        raise SystemExit(2)

    pkt=read_first_jsonl(args.claim_packets_jsonl)
    if not pkt:
        print("no claim packet row", file=sys.stderr); raise SystemExit(2)

    auth_refs=[(p.get("authority_ref") or "") for p in (pkt.get("authority_propositions") or []) if (p.get("authority_ref") or "").strip()]
    facts=[]
    missing=[]
    for fc in (pkt.get("evidence_facts") or []):
        fid=fc.get("fact_id") or fc.get("id") or ""
        pin=fc.get("pinpoint") or ""
        if not pin:
            missing.append({"fact_id":fid,"missing":"PINPOINT_MISSING"})
        facts.append({"fact_id":fid,"pinpoint":pin})

    row={
        "claim_draft_candidate_id": f"CDC-{pkt.get('claim_packet_id') or 'UNKNOWN'}",
        "source_claim_packet_id": pkt.get("claim_packet_id") or "",
        "authority_refs": auth_refs,
        "evidence_facts": facts,
        "pinpoint_missing": missing,
        "status":"CANDIDATE_ONLY_NO_ELEMENTS_NO_HOLDINGS"
    }

    with open(args.out_jsonl,"w",encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"OK auth_refs={len(auth_refs)} facts={len(facts)} missing_pinpoints={len(missing)}")

if __name__=="__main__":
    main()
