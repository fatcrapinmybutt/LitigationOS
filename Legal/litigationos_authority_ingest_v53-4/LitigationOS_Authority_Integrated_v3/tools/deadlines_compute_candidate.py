#!/usr/bin/env python3
import argparse, json, datetime

def parse_date(s): return datetime.date.fromisoformat(s)

def adjust_weekend(d, mode):
    if mode=="none": return d
    if mode=="next_business_day":
        while d.weekday()>=5: d = d + datetime.timedelta(days=1)
        return d
    if mode=="previous_business_day":
        while d.weekday()>=5: d = d - datetime.timedelta(days=1)
        return d
    return d

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--in-json", required=True)
    ap.add_argument("--out-json", required=True)
    args=ap.parse_args()

    payload=json.load(open(args.in_json,"r",encoding="utf-8"))
    events=payload.get("events") or []
    mode=payload.get("weekend_adjust") or "next_business_day"

    out={"items":[],"meta":{"confidence":"CANDIDATE_ONLY","notes":"DATE_ARITHMETIC_ONLY_WEEKEND_ADJUST_ONLY"}}
    for ev in events:
        eid=ev.get("id") or f"E{len(out['items'])+1}"
        ed=parse_date(ev["event_date"])
        add=int(ev.get("add_days") or 0)
        d=adjust_weekend(ed + datetime.timedelta(days=add), mode)
        out["items"].append({
            "deadline_id": f"D_{eid}",
            "event_id": eid,
            "event_date": ed.isoformat(),
            "add_days": add,
            "rule_basis": ev.get("rule_basis") or "",
            "computed_deadline_date": d.isoformat(),
            "confidence": "CANDIDATE_ONLY",
            "notes": ev.get("notes") or ""
        })

    json.dump(out, open(args.out_json,"w",encoding="utf-8"), indent=2)
    print(f"OK deadlines={len(out['items'])}")

if __name__=="__main__":
    main()
