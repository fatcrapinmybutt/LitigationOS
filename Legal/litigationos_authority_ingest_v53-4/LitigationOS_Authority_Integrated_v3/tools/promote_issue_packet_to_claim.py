#!/usr/bin/env python3
"""
Promotion Gate v24 (FAIL-CLOSED; HUMAN-APPROVAL REQUIRED)
Requires explicit allowlists of vehicle_id, fact_id, prop_id.
Use tools/ensure_atom_ids.py if upstream packets lacked ids.
"""
import argparse, json, csv, os, sys

def load_first_jsonl(path):
    for ln in open(path,"r",encoding="utf-8"):
        ln=ln.strip()
        if ln: return json.loads(ln)
    return None

def main():
    ap=argparse.ArgumentParser(description="Promote issue packet to claim packet with explicit approvals.")
    ap.add_argument("--issue-packets-jsonl", required=True)
    ap.add_argument("--approvals-json", required=True)
    ap.add_argument("--out-claim-packets-jsonl", required=True)
    ap.add_argument("--out-fixlist-csv", required=True)
    args=ap.parse_args()

    fix=[]

    if not os.path.exists(args.issue_packets_jsonl) or os.path.getsize(args.issue_packets_jsonl)==0:
        print("missing/empty issue packets", file=sys.stderr); raise SystemExit(2)
    if not os.path.exists(args.approvals_json) or os.path.getsize(args.approvals_json)==0:
        fix.append(("MISSING_APPROVALS","approvals-json missing/empty"))

    pkt=load_first_jsonl(args.issue_packets_jsonl)
    if not pkt:
        print("no issue packet row", file=sys.stderr); raise SystemExit(2)

    approvals={}
    if not fix:
        approvals=json.load(open(args.approvals_json,"r",encoding="utf-8"))

    ipid=pkt.get("issue_packet_id","")
    if approvals.get("approved_issue_packet_id","") != ipid:
        fix.append(("ISSUE_PACKET_ID_MISMATCH", f"approvals approved_issue_packet_id != issue_packet_id ({ipid})"))

    vehicles=pkt.get("vehicle_candidates") or []
    facts=pkt.get("evidence_facts") or []
    props=pkt.get("authority_propositions") or []

    v_by={ (v.get("vehicle_id") or ""): v for v in vehicles if (v.get("vehicle_id") or "").strip() }
    f_by={ (x.get("fact_id") or ""): x for x in facts if (x.get("fact_id") or "").strip() }
    p_by={ (x.get("prop_id") or ""): x for x in props if (x.get("prop_id") or "").strip() }

    av=approvals.get("approve_vehicle_ids") or []
    af=approvals.get("approve_fact_ids") or []
    apx=approvals.get("approve_prop_ids") or []

    if len(av)==0 and len(af)==0 and len(apx)==0:
        fix.append(("EMPTY_APPROVAL_SETS","no approved ids provided; must intentionally select"))

    for vid in av:
        if vid not in v_by: fix.append(("MISSING_VEHICLE_ID", vid))
    for fid in af:
        if fid not in f_by: fix.append(("MISSING_FACT_ID", fid))
    for pid in apx:
        if pid not in p_by: fix.append(("MISSING_PROP_ID", pid))

    sel_veh=[v_by[v] for v in av if v in v_by]
    sel_facts=[f_by[x] for x in af if x in f_by]
    sel_props=[p_by[x] for x in apx if x in p_by]

    for i,fc in enumerate(sel_facts,1):
        if not (fc.get("pinpoint") or "").strip():
            fix.append(("MISSING_FACT_PINPOINT", f"approved fact[{i}] missing pinpoint"))
    for i,pr in enumerate(sel_props,1):
        if not (pr.get("authority_ref") or "").strip() or not (pr.get("anchor_token") or "").strip():
            fix.append(("MISSING_PROP_FIELDS", f"approved prop[{i}] missing authority_ref or anchor_token"))

    status="PASS" if len(fix)==0 else "FAIL"
    claim={
        "claim_packet_id": f"CLAIMPACKET::{ipid}",
        "source_issue_packet_id": ipid,
        "status": "APPROVED_FOR_DRAFTING" if status=="PASS" else "BLOCKED_NOT_APPROVED",
        "approvals_meta": {
            "approver": approvals.get("approver",""),
            "approved_at": approvals.get("approved_at",""),
            "approved_issue_packet_id": approvals.get("approved_issue_packet_id","")
        },
        "vehicle_candidates": sel_veh,
        "evidence_facts": sel_facts,
        "authority_propositions": sel_props,
        "no_legal_inference": True
    }

    # outputs
    with open(args.out_claim_packets_jsonl,"w",encoding="utf-8") as f:
        if status=="PASS":
            f.write(json.dumps(claim, ensure_ascii=False) + "\n")

    with open(args.out_fixlist_csv,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=["blocker","detail"])
        w.writeheader()
        for b,d in fix: w.writerow({"blocker":b,"detail":d})

    print(f"OK {status} blockers={len(fix)}")

if __name__=="__main__":
    main()
