#!/usr/bin/env python3
"""
Contradiction Scanner (non-interpretive)

Purpose:
- Cross-check timelines / candidate tables for INTERNAL inconsistencies:
    - date_order: end_date < start_date
    - duplicate_key_conflict: same key but different value
    - impossible_deadline: computed_deadline before trigger_date
- Does NOT interpret legal significance. Emits flags only.

Inputs:
- one CSV (timeline/events/deadlines/validated outputs)
- configuration for key columns

Outputs:
- contradictions.csv with: row, type, key, details
"""

import argparse, csv, os, sys
from datetime import datetime

def die(msg, code=2):
    print(msg, file=sys.stderr); raise SystemExit(code)

def parse_date(s):
    s=(s or "").strip()
    if not s: return None
    for fmt in ("%Y-%m-%d","%Y-%m-%dT%H:%M:%S","%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None

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
    p.add_argument("--in", dest="inp", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--key", default="authority_ref", help="Key column for conflict grouping")
    p.add_argument("--start", default="start_date")
    p.add_argument("--end", default="end_date")
    p.add_argument("--trigger", default="trigger_date")
    p.add_argument("--deadline", default="computed_deadline")
    p.add_argument("--conflict-cols", default="status,vehicle_form,rule_candidate", help="Comma cols checked for conflicts")
    args=p.parse_args()

    if not os.path.exists(args.inp): die("Input CSV not found")
    rows=load_csv(args.inp)
    conflicts=[]
    # 1) date_order
    for idx,r in enumerate(rows, start=1):
        sd=parse_date(r.get(args.start))
        ed=parse_date(r.get(args.end))
        if sd and ed and ed < sd:
            conflicts.append({"row":idx,"type":"date_order","key":r.get(args.key,""),"details":f"{args.end}<{args.start}"})
        td=parse_date(r.get(args.trigger))
        dd=parse_date(r.get(args.deadline))
        if td and dd and dd < td:
            conflicts.append({"row":idx,"type":"impossible_deadline","key":r.get(args.key,""),"details":f"{args.deadline}<{args.trigger}"})
    # 2) duplicate_key_conflict
    cols=[c.strip() for c in (args.conflict_cols or "").split(",") if c.strip()]
    seen={}
    for idx,r in enumerate(rows, start=1):
        k=r.get(args.key,"")
        if not k: 
            continue
        snap=tuple((c, (r.get(c) or "").strip()) for c in cols)
        prev=seen.get(k)
        if prev is None:
            seen[k]=snap
        else:
            if snap != prev:
                conflicts.append({"row":idx,"type":"duplicate_key_conflict","key":k,"details":f"{prev} vs {snap}"})
    write_csv(args.out, conflicts, ["row","type","key","details"])

if __name__=="__main__":
    main()
