#!/usr/bin/env python3
"""
Claim Compiler Gate (PASS/FAIL)
- Produces court-assertable claim packets ONLY when gates pass:
  AUTH_PASS: propositions have authority_ref + anchor_token + non-empty excerpt_window
  VEHICLE_PASS: vehicle routing produced at least 1 candidate and catalog present (or explicit vehicle chosen)
  FACT_PASS: evidence facts exist and each asserted fact has a pinpoint
- If any gate fails: emits fixlist and claim packets remain empty.
Non-interpretive: the tool does not "decide" law; it only verifies required fields exist.
"""
import argparse, csv, json, os, sys

def die(msg, code=2):
    print(msg, file=sys.stderr); raise SystemExit(code)

def load_jsonl(path):
    out=[]
    with open(path,"r",encoding="utf-8") as f:
        for ln in f:
            ln=ln.strip()
            if not ln: continue
            out.append(json.loads(ln))
    return out

def write_csv(path, rows, fields):
    with open(path,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for r in rows: w.writerow(r)

def main():
    ap=argparse.ArgumentParser(description="Claim Compiler Gate (PASS/FAIL).")
    ap.add_argument("--vehicle-map-json", required=True)
    ap.add_argument("--propositions-jsonl", required=True)
    ap.add_argument("--evidence-facts-jsonl", default="", help="optional; required for FACT_PASS")
    ap.add_argument("--out-claim-packets-jsonl", required=True)
    ap.add_argument("--out-fixlist-csv", required=True)
    args=ap.parse_args()

    if not os.path.exists(args.vehicle_map_json): die("vehicle_map json missing")
    if not os.path.exists(args.propositions_jsonl): die("propositions jsonl missing")

    vehicle=json.load(open(args.vehicle_map_json,"r",encoding="utf-8"))
    props=load_jsonl(args.propositions_jsonl)

    fix=[]

    # AUTH_PASS: require some non-empty excerpt_window
    auth_pass=any((p.get("authority_ref") and p.get("anchor_token") and (p.get("excerpt_window") or "").strip()) for p in props)
    if not auth_pass:
        fix.append({"gate":"AUTH_PASS","status":"FAIL","detail":"No propositions with non-empty excerpt_window; ensure anchors match shard text or widen builder window."})

    # VEHICLE_PASS
    vstatus=vehicle.get("routing_status","")
    vcands=vehicle.get("vehicle_candidates",[]) or []
    vehicle_pass = (len(vcands) > 0) and ("MATCHED" in vstatus)
    if not vehicle_pass:
        fix.append({"gate":"VEHICLE_PASS","status":"FAIL","detail":"No vehicle candidates matched (or no catalog). Provide vehicle_catalog.csv and match relief_keywords to relief text."})

    # FACT_PASS
    facts_pass=False
    if args.evidence_facts_jsonl and os.path.exists(args.evidence_facts_jsonl) and os.path.getsize(args.evidence_facts_jsonl)>0:
        facts=load_jsonl(args.evidence_facts_jsonl)
        facts_pass=all((f.get("fact_text") and f.get("pinpoint")) for f in facts) and (len(facts)>0)
    if not facts_pass:
        fix.append({"gate":"FACT_PASS","status":"FAIL","detail":"Evidence facts missing or missing pinpoints. Produce evidence_facts_candidates.jsonl from Harvester with (fact_text,pinpoint)."})
    
    all_pass = auth_pass and vehicle_pass and facts_pass

    # Output claim packets only if PASS
    with open(args.out_claim_packets_jsonl,"w",encoding="utf-8") as f:
        if all_pass:
            # Minimal claim packet: includes refs only (no assertions)
            packet={
                "status":"ASSERTABLE_CLAIM_PACKET_PASS",
                "vehicle": vehicle.get("vehicle_candidates",[None])[0],
                "authority_propositions": [p for p in props[:25] if (p.get("excerpt_window") or "").strip()],
                "evidence_facts": load_jsonl(args.evidence_facts_jsonl)[:50],
                "notes":"PASS gates satisfied. Drafting layer may now generate court-facing text strictly from these inputs."
            }
            f.write(json.dumps(packet, ensure_ascii=False)+"\n")

    write_csv(args.out_fixlist_csv, fix, ["gate","status","detail"])
    print(f"OK pass={all_pass} fixlist={len(fix)}")

if __name__=="__main__":
    main()
