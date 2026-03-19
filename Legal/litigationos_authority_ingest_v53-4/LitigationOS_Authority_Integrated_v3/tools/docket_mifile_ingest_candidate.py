#!/usr/bin/env python3
import argparse, json, re

RE_SERVICE = re.compile(r'\b(service|served|proof of service)\b', re.I)
RE_ORDER = re.compile(r'\b(order|judgment)\b', re.I)
RE_NOTICE = re.compile(r'\b(notice|hearing)\b', re.I)
RE_APPEAL = re.compile(r'\b(appeal|leave to appeal)\b', re.I)
RE_MOTION = re.compile(r'\b(motion)\b', re.I)

def tag(text):
    t=text.lower()
    tags=[]
    if RE_SERVICE.search(t): tags.append("SERVICE")
    if RE_ORDER.search(t): tags.append("ORDER")
    if RE_NOTICE.search(t): tags.append("NOTICE")
    if RE_APPEAL.search(t): tags.append("APPEAL")
    if RE_MOTION.search(t): tags.append("MOTION")
    return tags or ["UNCLASSIFIED"]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--in-json", required=True)
    ap.add_argument("--events-out-json", required=True)
    ap.add_argument("--deadlines-events-out-json", required=True)
    args=ap.parse_args()

    payload=json.load(open(args.in_json,"r",encoding="utf-8"))
    entries=payload.get("entries") or []
    events=[]
    dl_events=[]
    for i,e in enumerate(entries, start=1):
        date=e.get("entry_date")
        text=e.get("text") or ""
        sp=e.get("source_path") or ""
        eid=f"ROA_{i:04d}"
        tags=tag(text)
        events.append({"event_id":eid,"event_date":date,"text":text,"tags":tags,"source_path":sp,"confidence":"CANDIDATE_ONLY"})
        dl_events.append({"id":eid,"event_date":date,"add_days":0,"rule_basis":"","notes":"PINPOINT_MISSING_FILL_ADD_DAYS_AND_RULE_BASIS","confidence":"CANDIDATE_ONLY"})
    json.dump({"events":events,"meta":{"confidence":"CANDIDATE_ONLY"}}, open(args.events_out_json,"w",encoding="utf-8"), indent=2, ensure_ascii=False)
    json.dump({"events":dl_events,"weekend_adjust":"next_business_day","meta":{"confidence":"CANDIDATE_ONLY"}}, open(args.deadlines_events_out_json,"w",encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"OK events={len(events)}")

if __name__=="__main__":
    main()
