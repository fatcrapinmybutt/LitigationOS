#!/usr/bin/env python3
"""
Deadline Engine (CANDIDATE-ONLY) v20
Adds:
- Optional holiday calendar (CSV) for business-day computations.
- Optional service method offsets (CSV) applied AFTER base offsets.
Still:
- No legal assertions. All offsets come from user catalogs.
Inputs:
--events-csv: docket_events.csv
--rules-csv: deadline_rules_catalog.csv (base offsets by event_kind)
Optional:
--holidays-csv: holidays.csv (date,label)
--service-methods-csv: service_methods_catalog.csv (service_method,add_days,add_business_days,notes,authority_anchor_token)
--event-service-map-csv: event_service_map.csv (event_id,service_method)
Outputs:
--out-deadlines-csv
--out-fixlist-csv
"""
import argparse, csv, os, sys
from datetime import datetime, timedelta, date

def parse_date(s):
    s=(s or "").strip()
    if not s: return None
    for fmt in ("%Y-%m-%d","%m/%d/%Y","%Y/%m/%d"):
        try: return datetime.strptime(s, fmt).date()
        except: pass
    return None

def load_holidays(path):
    hol=set()
    if not path: return hol
    if not os.path.exists(path) or os.path.getsize(path)==0:
        return hol
    for r in csv.DictReader(open(path,"r",encoding="utf-8")):
        d=parse_date(r.get("date") or r.get("holiday_date") or "")
        if d: hol.add(d)
    return hol

def is_business_day(d: date, holidays:set):
    return d.weekday()<5 and d not in holidays

def add_business_days(d: date, n: int, holidays:set):
    step=1 if n>=0 else -1
    n=abs(n)
    cur=d
    while n>0:
        cur=cur+timedelta(days=step)
        if is_business_day(cur, holidays):
            n-=1
    return cur

def main():
    ap=argparse.ArgumentParser(description="Compute deadline candidates from events + user catalogs (v20).")
    ap.add_argument("--events-csv", required=True)
    ap.add_argument("--rules-csv", required=True)
    ap.add_argument("--out-deadlines-csv", required=True)
    ap.add_argument("--out-fixlist-csv", required=True)
    ap.add_argument("--holidays-csv", default="")
    ap.add_argument("--service-methods-csv", default="")
    ap.add_argument("--event-service-map-csv", default="")
    args=ap.parse_args()

    if not os.path.exists(args.events_csv) or os.path.getsize(args.events_csv)==0:
        print("events csv missing/empty", file=sys.stderr); raise SystemExit(2)
    if not os.path.exists(args.rules_csv) or os.path.getsize(args.rules_csv)==0:
        print("rules csv missing/empty", file=sys.stderr); raise SystemExit(2)

    holidays=load_holidays(args.holidays_csv)

    events=list(csv.DictReader(open(args.events_csv,"r",encoding="utf-8")))
    rules=list(csv.DictReader(open(args.rules_csv,"r",encoding="utf-8")))

    rules_by_kind={}
    for r in rules:
        k=(r.get("event_kind") or "").strip().lower()
        if not k: continue
        rules_by_kind.setdefault(k, []).append(r)

    svc_by_name={}
    if args.service_methods_csv and os.path.exists(args.service_methods_csv) and os.path.getsize(args.service_methods_csv)>0:
        for r in csv.DictReader(open(args.service_methods_csv,"r",encoding="utf-8")):
            name=(r.get("service_method") or "").strip().lower()
            if name: svc_by_name[name]=r

    svc_map={}
    if args.event_service_map_csv and os.path.exists(args.event_service_map_csv) and os.path.getsize(args.event_service_map_csv)>0:
        for r in csv.DictReader(open(args.event_service_map_csv,"r",encoding="utf-8")):
            eid=(r.get("event_id") or "").strip()
            m=(r.get("service_method") or "").strip().lower()
            if eid and m: svc_map[eid]=m

    deadlines=[]
    fix=[]

    for ev in events:
        ev_id=(ev.get("event_id") or "").strip()
        kind=(ev.get("event_kind") or "").strip().lower()
        ev_date=parse_date(ev.get("event_date"))
        sp=(ev.get("source_pinpoint") or "").strip()
        if not ev_id: 
            continue
        if not ev_date:
            fix.append({"event_id":ev_id,"blocker":"MISSING_EVENT_DATE","detail":"event_date required", "source_pinpoint":sp})
            continue
        if kind not in rules_by_kind:
            fix.append({"event_id":ev_id,"blocker":"NO_RULE_MATCH","detail":f"No rule rows for event_kind='{kind}'", "source_pinpoint":sp})
            continue

        svc_method=svc_map.get(ev_id,"")
        svc_row=svc_by_name.get(svc_method,"") if svc_method else ""

        for r in rules_by_kind[kind]:
            rule_id=(r.get("rule_id") or "").strip()
            od=int((r.get("offset_days") or "0").strip() or "0")
            obd=int((r.get("offset_business_days") or "0").strip() or "0")
            d=ev_date
            if od: d=d+timedelta(days=od)
            if obd: d=add_business_days(d, obd, holidays)

            # apply service method offsets after base
            svc_od=0; svc_obd=0; svc_anchor=""
            if svc_row:
                svc_od=int((svc_row.get("add_days") or "0").strip() or "0")
                svc_obd=int((svc_row.get("add_business_days") or "0").strip() or "0")
                svc_anchor=(svc_row.get("authority_anchor_token") or "").strip()
                if svc_od: d=d+timedelta(days=svc_od)
                if svc_obd: d=add_business_days(d, svc_obd, holidays)

            deadlines.append({
                "event_id": ev_id,
                "rule_id": rule_id,
                "event_kind": kind,
                "event_date": ev_date.isoformat(),
                "deadline_date": d.isoformat(),
                "service_method": svc_method,
                "authority_anchor_token": (r.get("authority_anchor_token") or "").strip(),
                "service_method_anchor_token": svc_anchor,
                "status": "CANDIDATE_DEADLINE_NO_LEGAL_ASSERTION",
                "source_pinpoint": sp,
                "notes": (r.get("notes") or "").strip()
            })

    with open(args.out_deadlines_csv,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=["event_id","rule_id","event_kind","event_date","deadline_date","service_method","authority_anchor_token","service_method_anchor_token","status","source_pinpoint","notes"])
        w.writeheader()
        for row in deadlines: w.writerow(row)

    with open(args.out_fixlist_csv,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=["event_id","blocker","detail","source_pinpoint"])
        w.writeheader()
        for row in fix: w.writerow(row)

    print(f"OK deadlines={len(deadlines)} fixlist={len(fix)} holidays={len(holidays)} svc_methods={len(svc_by_name)}")

if __name__=="__main__":
    main()
