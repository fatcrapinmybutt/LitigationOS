#!/usr/bin/env python3
"""
Preflight Gate v22 (FAIL-CLOSED; completeness only)
Vehicle acceptance:
- Accepts either legacy {"status":"PASS"} OR router schema with:
  routing_status == "CANDIDATE_ONLY_MATCHED" AND len(vehicle_candidates) >= 1
Claim packet acceptance:
- >=1 evidence fact with pinpoint
- >=1 authority prop with authority_ref + anchor_token
Deadlines (if provided):
- each row must include deadline_date and source_pinpoint
"""
import argparse, json, os, sys, csv
from datetime import datetime, date

def parse_date(s):
    s=(s or "").strip()
    if not s: return None
    for fmt in ("%Y-%m-%d","%m/%d/%Y","%Y/%m/%d"):
        try: return datetime.strptime(s, fmt).date()
        except: pass
    return None

def load_first_jsonl(path):
    with open(path,"r",encoding="utf-8") as f:
        for ln in f:
            ln=ln.strip()
            if not ln: continue
            return json.loads(ln)
    return None

def vehicle_is_pass(v):
    if not isinstance(v, dict):
        return (False, "vehicle json not dict")
    if v.get("status") == "PASS":
        return (True, "legacy_status_PASS")
    if v.get("routing_status") == "CANDIDATE_ONLY_MATCHED":
        vc=v.get("vehicle_candidates") or []
        if isinstance(vc, list) and len(vc) >= 1:
            return (True, "routing_status_MATCHED_candidates_present")
        return (False, "routing_status_MATCHED_but_no_candidates")
    return (False, f"unrecognized vehicle status fields (status={v.get('status')}, routing_status={v.get('routing_status')})")

def main():
    ap=argparse.ArgumentParser(description="Preflight gate v22.")
    ap.add_argument("--vehicle-map-json", required=True)
    ap.add_argument("--claim-packets-jsonl", required=True)
    ap.add_argument("--deadlines-csv", default="")
    ap.add_argument("--today", default="")
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-csv", required=True)
    args=ap.parse_args()

    fix=[]
    warn=[]
    today=parse_date(args.today) if args.today else date.today()

    # vehicle map
    v=None
    if not os.path.exists(args.vehicle_map_json) or os.path.getsize(args.vehicle_map_json)==0:
        fix.append({"blocker":"MISSING_VEHICLE_MAP","detail":"vehicle-map-json missing/empty"})
    else:
        v=json.load(open(args.vehicle_map_json,"r",encoding="utf-8"))
        ok,reason=vehicle_is_pass(v)
        if not ok:
            fix.append({"blocker":"VEHICLE_NOT_PASS","detail":reason})

    # claim packet
    pkt=None
    if not os.path.exists(args.claim_packets_jsonl) or os.path.getsize(args.claim_packets_jsonl)==0:
        fix.append({"blocker":"MISSING_CLAIM_PACKETS","detail":"claim-packets-jsonl missing/empty"})
    else:
        pkt=load_first_jsonl(args.claim_packets_jsonl)
        if not pkt:
            fix.append({"blocker":"NO_PACKET","detail":"claim-packets-jsonl has no rows"})
        else:
            facts=pkt.get("evidence_facts") or []
            props=pkt.get("authority_propositions") or []
            if len(facts)<1:
                fix.append({"blocker":"NO_EVIDENCE_FACTS","detail":"packet has no evidence_facts"})
            else:
                for i,fc in enumerate(facts,1):
                    if not (fc.get("pinpoint") or "").strip():
                        fix.append({"blocker":"MISSING_FACT_PINPOINT","detail":f"fact[{i}] missing pinpoint"})
            if len(props)<1:
                fix.append({"blocker":"NO_AUTH_PROPS","detail":"packet has no authority_propositions"})
            else:
                for i,pr in enumerate(props,1):
                    if not (pr.get("authority_ref") or "").strip() or not (pr.get("anchor_token") or "").strip():
                        fix.append({"blocker":"MISSING_AUTH_BACKLINK_FIELDS","detail":f"prop[{i}] missing authority_ref or anchor_token"})

    # deadlines
    dl_rows=[]
    if args.deadlines_csv and os.path.exists(args.deadlines_csv) and os.path.getsize(args.deadlines_csv)>0:
        dl_rows=list(csv.DictReader(open(args.deadlines_csv,"r",encoding="utf-8")))
        if len(dl_rows)==0:
            fix.append({"blocker":"EMPTY_DEADLINES","detail":"deadlines-csv has header but no rows"})
        for i,r in enumerate(dl_rows,1):
            dd=(r.get("deadline_date") or "").strip()
            sp=(r.get("source_pinpoint") or "").strip()
            if not dd:
                fix.append({"blocker":"MISSING_DEADLINE_DATE","detail":f"deadlines row {i} missing deadline_date"})
            if not sp:
                fix.append({"blocker":"MISSING_DEADLINE_SOURCE","detail":f"deadlines row {i} missing source_pinpoint"})
            d=parse_date(dd)
            if d and d < today:
                warn.append({"warning":"CANDIDATE_DEADLINE_IN_PAST","detail":f"row {i} deadline_date={dd} < today={today.isoformat()}"})
    else:
        warn.append({"warning":"NO_DEADLINES_PROVIDED","detail":"deadlines-csv not provided or empty"})

    status="PASS" if len(fix)==0 else "FAIL"
    rep={
        "status": status,
        "today": today.isoformat(),
        "blockers": fix,
        "warnings": warn,
        "deadline_rows": len(dl_rows),
    }
    json.dump(rep, open(args.out_json,"w",encoding="utf-8"), indent=2, ensure_ascii=False)
    with open(args.out_csv,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=["blocker","detail"])
        w.writeheader()
        for b in fix: w.writerow({"blocker":b["blocker"],"detail":b["detail"]})

    print(f"OK {status} blockers={len(fix)} warnings={len(warn)} deadlines={len(dl_rows)}")

if __name__=="__main__":
    main()
