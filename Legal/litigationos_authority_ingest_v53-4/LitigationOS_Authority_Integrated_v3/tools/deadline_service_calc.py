#!/usr/bin/env python3
"""
Deadline & Service Calculator (candidate-only, non-interpretive)

Goal:
- Produce CALCULATED_CANDIDATE fields (deadline, service_due) based on simple date arithmetic
  and operator-supplied parameters.
- Does NOT determine which rules apply. Operator must supply:
    - trigger_date (YYYY-MM-DD)
    - days_offset (int)
    - optional business_days (bool) and holiday list file (optional)

Inputs:
- candidates CSV (vehicle map scaffold or authority triples or any CSV with at least authority_ref)
- one or more calc specs (--spec JSON)
Outputs:
- enriched.csv with added fields:
    trigger_date, days_offset, computed_deadline, computed_service_due, calc_basis, status_calc

Status:
- status_calc is always CALCULATED_CANDIDATE
"""

import argparse, csv, json, os, sys
from datetime import datetime, timedelta, date

def die(msg, code=2):
    print(msg, file=sys.stderr); raise SystemExit(code)

def parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()

def is_weekend(d: date) -> bool:
    return d.weekday() >= 5

def load_holidays(path: str):
    if not path: return set()
    hs=set()
    with open(path,"r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if not line or line.startswith("#"): continue
            hs.add(parse_date(line))
    return hs

def add_days(d: date, n: int, business_days: bool, holidays:set) -> date:
    if not business_days:
        return d + timedelta(days=n)
    step = 1 if n>=0 else -1
    remaining = abs(n)
    cur=d
    while remaining>0:
        cur = cur + timedelta(days=step)
        if is_weekend(cur): 
            continue
        if cur in holidays:
            continue
        remaining -= 1
    return cur

def load_csv(path):
    with open(path,"r",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_csv(path, rows, fieldnames):
    with open(path,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows: w.writerow(r)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--candidates", required=True, help="Input CSV")
    p.add_argument("--spec", required=True, help="JSON calc spec string or @path.json")
    p.add_argument("--out", required=True, help="Output CSV")
    p.add_argument("--holidays", help="Optional holidays file (one YYYY-MM-DD per line)")
    args=p.parse_args()

    if not os.path.exists(args.candidates): die("Candidates CSV not found")
    spec_str=args.spec
    if spec_str.startswith("@"):
        spec_path=spec_str[1:]
        spec=json.load(open(spec_path,"r",encoding="utf-8"))
    else:
        spec=json.loads(spec_str)

    trigger=spec.get("trigger_date")
    days=int(spec.get("days_offset",0))
    business=bool(spec.get("business_days",False))
    svc_days=int(spec.get("service_days_offset",0))

    if not trigger:
        die("spec.trigger_date required (YYYY-MM-DD)")
    td=parse_date(trigger)
    holidays=load_holidays(args.holidays)

    rows=load_csv(args.candidates)
    for r in rows:
        deadline=add_days(td, days, business, holidays)
        service_due=add_days(td, svc_days, business, holidays) if svc_days!=0 else None
        r["trigger_date"]=trigger
        r["days_offset"]=str(days)
        r["business_days"]=str(business)
        r["computed_deadline"]=deadline.isoformat()
        r["computed_service_due"]=service_due.isoformat() if service_due else ""
        r["calc_basis"]=spec.get("calc_basis","operator-supplied; non-interpretive")
        r["status_calc"]="CALCULATED_CANDIDATE"

    fieldnames=list(rows[0].keys()) if rows else []
    write_csv(args.out, rows, fieldnames)

if __name__=="__main__":
    main()
