#!/usr/bin/env python3
import argparse, csv, datetime, os, sys

def die(msg, code=2):
    print(msg, file=sys.stderr); raise SystemExit(code)

def load_csv(path):
    with open(path,"r",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_csv(path, rows, fields):
    with open(path,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for r in rows: w.writerow(r)

def parse_date(s):
    try:
        return datetime.date.fromisoformat(s)
    except Exception:
        return None

def load_holidays(path):
    if not path:
        return set()
    if not os.path.exists(path):
        die(f"Holidays file missing: {path}")
    out=set()
    with open(path,"r",encoding="utf-8") as f:
        for ln in f:
            ln=ln.strip()
            if not ln: continue
            d=parse_date(ln)
            if d: out.add(d)
    return out

def next_business_day(d, holidays):
    while d.weekday()>=5 or d in holidays:
        d = d + datetime.timedelta(days=1)
    return d

def main():
    ap=argparse.ArgumentParser(description="Deadline Computer (candidate-only arithmetic)")
    ap.add_argument("--in-csv", required=True)
    ap.add_argument("--out-csv", required=True)
    ap.add_argument("--skip-weekends", action="store_true")
    ap.add_argument("--holidays-txt")
    args=ap.parse_args()

    rows=load_csv(args.in_csv)
    holidays=load_holidays(args.holidays_txt)

    out=[]
    for r in rows:
        rr=dict(r)
        dt=parse_date((r.get("trigger_event_date") or "").strip())
        try:
            off=int((r.get("days_offset") or "").strip())
        except Exception:
            off=None
        if not dt or off is None:
            rr["computed_deadline"]=""
            rr["status_calc"]="FAIL"
            out.append(rr)
            continue

        d=dt + datetime.timedelta(days=off)
        if args.skip_weekends:
            d=next_business_day(d, holidays)
        rr["computed_deadline"]=d.isoformat()
        rr["status_calc"]="CALCULATED_CANDIDATE"
        out.append(rr)

    if out:
        fields=sorted({k for r in out for k in r.keys()})
    else:
        fields=["trigger_event_date","rule_label","days_offset","computed_deadline","basis","source_kind","source_text","status_calc","status"]
    write_csv(args.out_csv, out, fields)

if __name__=="__main__":
    main()
