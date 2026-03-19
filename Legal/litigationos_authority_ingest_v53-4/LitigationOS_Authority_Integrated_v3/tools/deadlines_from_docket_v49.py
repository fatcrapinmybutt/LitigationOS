#!/usr/bin/env python3
"""
deadlines_from_docket_v49.py — CANDIDATE DEADLINES FROM DOCKET EVENTS (v49)

INPUT: outputs/docket_events.json (from v48)
OPTIONAL: outputs/deadline_trigger_map.json (or docs/examples/deadline_trigger_map.example.json)

OUTPUT: outputs/deadlines.json (candidate items) + outputs/deadlines_report.json

NON-INTERPRETIVE RULE:
- This tool never claims legal correctness.
- Every produced deadline MUST carry a 'basis' string and a 'requires_validation' note.
- Date math is purely mechanical: event_date + N days, no court-day adjustments.
"""
import argparse, json, os, re, datetime

DATE_RX=re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")

def parse_mmddyyyy(s):
    m=DATE_RX.search(s or "")
    if not m: return None
    mm,dd,yy=map(int,m.groups())
    try:
        return datetime.date(yy,mm,dd)
    except Exception:
        return None

def load_json(p):
    if not (os.path.exists(p) and os.path.getsize(p)>0): return None
    return json.load(open(p,"r",encoding="utf-8"))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--docket-json", required=True)
    ap.add_argument("--trigger-map", default="outputs/deadline_trigger_map.json")
    ap.add_argument("--out-deadlines", required=True)
    ap.add_argument("--out-report", default="outputs/deadlines_report.json")
    ap.add_argument("--max", type=int, default=500)
    args=ap.parse_args()

    docket=load_json(args.docket_json)
    if docket is None:
        raise SystemExit("docket_events.json missing/unreadable")

    trig=load_json(args.trigger_map)
    if trig is None:
        ex=os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","docs","examples","deadline_trigger_map.example.json"))
        trig=load_json(ex) if os.path.exists(ex) else {"triggers":[]}

    triggers=[]
    for t in (trig.get("triggers") or []):
        try:
            rx=re.compile(t.get("match_regex",""), re.IGNORECASE)
            triggers.append((t,rx))
        except Exception:
            continue

    out_items=[]
    used=0
    for block in (docket.get("events") or []):
        sp=block.get("source_path") or ""
        cands=block.get("event_candidates") or []
        for ev in cands:
            if used>=args.max: break
            line=ev.get("anchor_line") or ""
            dt=parse_mmddyyyy(ev.get("date") or line)
            if not dt:
                continue
            for t,rx in triggers:
                if rx.search(line):
                    days=int(t.get("deadline_days") or 0)
                    if days<=0:
                        continue
                    due=dt + datetime.timedelta(days=days)
                    used+=1
                    out_items.append({
                        "deadline_id": f"DOC{used:04d}",
                        "due_date": due.isoformat(),
                        "label": t.get("label","Candidate deadline"),
                        "basis": f"MECHANICAL: {dt.isoformat()} + {days} days from docket anchor; source={sp}; line_no={ev.get('anchor_line_no')}; requires_validation",
                        "source": {"source_path": sp, "anchor_line_no": ev.get("anchor_line_no"), "anchor_line": line},
                        "rule_candidate": t.get("rule_candidate",""),
                        "notes": "CANDIDATE_ONLY_REQUIRES_VALIDATION"
                    })
                    break
        if used>=args.max: break

    out={"items": out_items, "meta": {"generated_utc": datetime.datetime.utcnow().isoformat()+"Z",
                                       "count": len(out_items),
                                       "non_interpretive": True,
                                       "requires_validation": True}}
    os.makedirs(os.path.dirname(args.out_deadlines) or ".", exist_ok=True)
    json.dump(out, open(args.out_deadlines,"w",encoding="utf-8"), indent=2, ensure_ascii=False)

    report={"status":"PASS" if len(out_items)>0 else "FAIL",
            "reason":"No triggers matched docket anchor lines" if len(out_items)==0 else "Candidate deadlines generated (requires validation)",
            "count": len(out_items),
            "next":"Validate triggers against authority shards and replace candidate rule refs with pinpointed authority_ref"}
    json.dump(report, open(args.out_report,"w",encoding="utf-8"), indent=2, ensure_ascii=False)
    print("OK deadlines=", len(out_items), "->", args.out_deadlines)

if __name__=="__main__":
    main()
