#!/usr/bin/env python3
"""
Claim Router Candidates v23 (CANDIDATE-ONLY, NON-INTERPRETIVE)
Purpose:
- Given (1) evidence facts JSONL, (2) authority propositions JSONL, and (3) vehicle candidates JSON,
  emit a candidate "issue packet" that can be manually approved into a claim packet.
Key property:
- Does NOT create legal claims. It only pairs artifacts into a structured packet with provenance pointers.
Inputs:
--vehicle-map-json
--evidence-facts-jsonl
--propositions-jsonl
Outputs:
--out-issue-packets-jsonl
--out-fixlist-csv
Selection logic (conservative defaults):
- Take top N facts (default 10)
- Take top M propositions (default 15)
- Take first K vehicle candidates (default 3) (or legacy vehicle object)
"""
import argparse, json, os, sys, csv

def die(msg, code=2):
    print(msg, file=sys.stderr); raise SystemExit(code)

def load_json(path):
    return json.load(open(path,"r",encoding="utf-8"))

def load_jsonl(path, limit=0):
    out=[]
    with open(path,"r",encoding="utf-8") as f:
        for ln in f:
            ln=ln.strip()
            if not ln: continue
            out.append(json.loads(ln))
            if limit and len(out)>=limit: break
    return out

def main():
    ap=argparse.ArgumentParser(description="Candidate issue packet builder.")
    ap.add_argument("--vehicle-map-json", required=True)
    ap.add_argument("--evidence-facts-jsonl", required=True)
    ap.add_argument("--propositions-jsonl", required=True)
    ap.add_argument("--out-issue-packets-jsonl", required=True)
    ap.add_argument("--out-fixlist-csv", required=True)
    ap.add_argument("--facts-limit", type=int, default=10)
    ap.add_argument("--props-limit", type=int, default=15)
    ap.add_argument("--vehicles-limit", type=int, default=3)
    args=ap.parse_args()

    fix=[]
    if not os.path.exists(args.vehicle_map_json) or os.path.getsize(args.vehicle_map_json)==0:
        fix.append(("MISSING_VEHICLE_MAP","vehicle map missing/empty"))
        vehicle=None
    else:
        vehicle=load_json(args.vehicle_map_json)

    if not os.path.exists(args.evidence_facts_jsonl) or os.path.getsize(args.evidence_facts_jsonl)==0:
        fix.append(("MISSING_EVIDENCE_FACTS","evidence facts missing/empty"))
        facts=[]
    else:
        facts=load_jsonl(args.evidence_facts_jsonl, limit=max(0,args.facts_limit))

    if not os.path.exists(args.propositions_jsonl) or os.path.getsize(args.propositions_jsonl)==0:
        fix.append(("MISSING_PROPOSITIONS","propositions missing/empty"))
        props=[]
    else:
        props=load_jsonl(args.propositions_jsonl, limit=max(0,args.props_limit))

    if fix:
        with open(args.out_fixlist_csv,"w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f, fieldnames=["blocker","detail"])
            w.writeheader()
            for b,d in fix: w.writerow({"blocker":b,"detail":d})
        # still write empty packets file
        open(args.out_issue_packets_jsonl,"w",encoding="utf-8").close()
        print(f"FAIL blockers={len(fix)}")
        raise SystemExit(2)

    vehicles=[]
    if isinstance(vehicle, dict) and vehicle.get("routing_status")=="CANDIDATE_ONLY_MATCHED":
        vc=vehicle.get("vehicle_candidates") or []
        vehicles=vc[:max(0,args.vehicles_limit)]
    elif isinstance(vehicle, dict) and vehicle.get("status")=="PASS":
        vehicles=[vehicle]
    else:
        vehicles=[]

    packet={
        "issue_packet_id": "ISSUEPACKET-DEMO",
        "status": "CANDIDATE_ONLY_NO_LEGAL_INFERENCE",
        "vehicle_candidates": vehicles,
        "evidence_facts": facts,
        "authority_propositions": props
    }

    with open(args.out_issue_packets_jsonl,"w",encoding="utf-8") as f:
        f.write(json.dumps(packet, ensure_ascii=False) + "\n")

    with open(args.out_fixlist_csv,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=["blocker","detail"])
        w.writeheader()

    print("OK packets=1")

if __name__=="__main__":
    main()
