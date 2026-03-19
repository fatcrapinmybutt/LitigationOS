#!/usr/bin/env python3
"""
Deadline Compute Engine v26 (GATED; FAIL-CLOSED by default)

Purpose:
- Compute candidate deadlines from trigger events ONLY when a rule config is provided.
- If config is missing or incomplete, output FIXLIST and compute nothing.

This file does NOT embed or assert legal rules. It requires the user to provide a
rule-set JSON that defines offsets and weekend/holiday handling.

Inputs:
--triggers-csv   required columns: trigger_id, trigger_date, trigger_type, source_pinpoint
--rules-json     required; if missing => FAIL (no computation)
--holidays-csv   optional; ISO dates column 'date' (YYYY-MM-DD)
Outputs:
--out-deadlines-csv  columns: deadline_id, deadline_date, deadline_type, trigger_id, source_pinpoint, notes
--out-fixlist-csv    blockers

Rules JSON (minimal):
{
  "engine_status": "ENABLED",
  "weekend_policy": "NEXT_BUSINESS_DAY" | "NONE",
  "holiday_policy": "NEXT_BUSINESS_DAY" | "NONE",
  "rules": [
    {"trigger_type":"SERVICE_MAIL", "deadline_type":"RESPONSE_DUE", "days_offset":21},
    {"trigger_type":"ORDER_ENTERED", "deadline_type":"MOTION_RECONSIDER_DUE", "days_offset":14}
  ]
}

Computation:
deadline_date = trigger_date + days_offset, then apply weekend/holiday roll-forward per policies.
"""
import argparse, csv, json, os, sys
from datetime import datetime, timedelta

def die(msg, code=2):
    print(msg, file=sys.stderr); raise SystemExit(code)

def read_csv(path):
    with open(path,"r",encoding="utf-8",errors="ignore") as f:
        rdr=csv.DictReader(f)
        return list(rdr)

def load_rules(path):
    obj=json.load(open(path,"r",encoding="utf-8"))
    if obj.get("engine_status") != "ENABLED":
        return None, [("ENGINE_DISABLED","rules-json engine_status must be ENABLED")]
    if "rules" not in obj or not isinstance(obj["rules"], list) or len(obj["rules"])==0:
        return None, [("MISSING_RULES","rules list missing/empty")]
    return obj, []

def load_holidays(path):
    hs=set()
    if not path or not os.path.exists(path) or os.path.getsize(path)==0:
        return hs
    with open(path,"r",encoding="utf-8",errors="ignore") as f:
        rdr=csv.DictReader(f)
        for r in rdr:
            d=(r.get("date") or "").strip()
            if d:
                hs.add(d)
    return hs

def is_weekend(d):
    # d is datetime.date
    return d.weekday()>=5

def roll_forward(d, weekend_policy, holiday_policy, holidays):
    # d is date
    while True:
        if weekend_policy=="NEXT_BUSINESS_DAY" and is_weekend(d):
            d = d + timedelta(days=1); continue
        if holiday_policy=="NEXT_BUSINESS_DAY" and d.isoformat() in holidays:
            d = d + timedelta(days=1); continue
        return d

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--triggers-csv", required=True)
    ap.add_argument("--rules-json", required=True)
    ap.add_argument("--holidays-csv", default="")
    ap.add_argument("--out-deadlines-csv", required=True)
    ap.add_argument("--out-fixlist-csv", required=True)
    args=ap.parse_args()

    fix=[]
    if not os.path.exists(args.triggers_csv) or os.path.getsize(args.triggers_csv)==0:
        die("missing/empty triggers-csv")

    if not os.path.exists(args.rules_json) or os.path.getsize(args.rules_json)==0:
        fix.append(("MISSING_RULES_JSON","rules-json missing/empty"))
        ruleset=None
    else:
        ruleset, more = load_rules(args.rules_json)
        fix.extend(more)

    if fix:
        with open(args.out_fixlist_csv,"w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f, fieldnames=["blocker","detail"]); w.writeheader()
            for b,d in fix: w.writerow({"blocker":b,"detail":d})
        # write empty deadlines
        with open(args.out_deadlines_csv,"w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f, fieldnames=["deadline_id","deadline_date","deadline_type","trigger_id","source_pinpoint","notes"])
            w.writeheader()
        print(f"FAIL blockers={len(fix)}")
        raise SystemExit(2)

    weekend_policy = ruleset.get("weekend_policy","NONE")
    holiday_policy = ruleset.get("holiday_policy","NONE")
    holidays = load_holidays(args.holidays_csv)

    triggers=read_csv(args.triggers_csv)
    computed=[]
    ridx=0
    for t in triggers:
        ttype=(t.get("trigger_type") or "").strip()
        tdate=(t.get("trigger_date") or "").strip()
        if not ttype or not tdate:
            continue
        try:
            td=datetime.strptime(tdate, "%Y-%m-%d").date()
        except Exception:
            continue
        for rule in ruleset["rules"]:
            if (rule.get("trigger_type") or "").strip() != ttype:
                continue
            days=int(rule.get("days_offset") or 0)
            dd = td + timedelta(days=days)
            dd = roll_forward(dd, weekend_policy, holiday_policy, holidays)
            ridx += 1
            computed.append({
                "deadline_id": f"DL-{ridx:05d}",
                "deadline_date": dd.isoformat(),
                "deadline_type": (rule.get("deadline_type") or "DEADLINE"),
                "trigger_id": (t.get("trigger_id") or ""),
                "source_pinpoint": (t.get("source_pinpoint") or ""),
                "notes": f"offset_days={days} trigger_type={ttype}"
            })

    with open(args.out_deadlines_csv,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=["deadline_id","deadline_date","deadline_type","trigger_id","source_pinpoint","notes"])
        w.writeheader()
        for r in computed:
            w.writerow(r)

    with open(args.out_fixlist_csv,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=["blocker","detail"]); w.writeheader()

    print(f"OK computed={len(computed)}")

if __name__=="__main__":
    main()
