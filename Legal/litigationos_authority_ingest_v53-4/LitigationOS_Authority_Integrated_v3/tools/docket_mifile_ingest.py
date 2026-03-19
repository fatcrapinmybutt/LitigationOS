#!/usr/bin/env python3
"""
Docket/MiFile Ingest (candidate-only)

Goal:
- Ingest Register of Actions (ROA) / docket exports and MiFile filing receipts (as text or CSV) into a
  normalized "docket_events_candidates.csv" stream.
- Optionally derive *candidate* deadlines feed using operator-supplied mapping rules (no legal inference).

Inputs:
A) --roa-csv: CSV export with columns like date, entry, description (flexible; use --map-json)
B) --receipts-csv: CSV export of MiFile receipts (flexible; use --map-json)
C) --text: plaintext lines (already extracted externally via pdftotext) (use --text-kind=roa|receipt)

Mapping:
- --map-json: a JSON mapping that identifies which input columns correspond to:
  - event_date, docket_text, filing_party, document_title, case_number, court_name, file_path
If omitted, defaults try common column names.

Output:
- --out-csv: docket_events_candidates.csv
Columns (normalized):
  event_date, kind, docket_text, filing_party, document_title, case_number, court_name, file_path, integrity_note, status

Candidate deadline feed (optional):
- --deadline-spec-json: operator-defined rules that transform certain 'kind' or token matches into day offsets.
  This uses plain arithmetic only and marks deadlines as CALCULATED_CANDIDATE.
"""
import argparse, csv, json, os, sys, datetime

def die(msg, code=2):
    print(msg, file=sys.stderr); raise SystemExit(code)

def load_csv(path):
    with open(path,"r",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def read_lines_txt(path):
    lines=[]
    with open(path,"r",encoding="utf-8") as f:
        for ln in f:
            ln=ln.strip()
            if ln:
                lines.append(ln)
    return lines

def parse_date(s):
    s=(s or "").strip()
    if not s:
        return ""
    # try common formats only; if unknown leave blank (fail-closed)
    fmts=["%Y-%m-%d","%m/%d/%Y","%m/%d/%y"]
    for fmt in fmts:
        try:
            return datetime.datetime.strptime(s,fmt).date().isoformat()
        except Exception:
            pass
    return ""

def normalize_row(r, kind, m):
    def pick(*keys):
        for k in keys:
            if k in r and (r.get(k) or "").strip():
                return (r.get(k) or "").strip()
        return ""
    event_date=parse_date(pick(m.get("event_date","date"),"date","entry_date","filed","timestamp"))
    docket_text=pick(m.get("docket_text","description"),"description","text","entry","docket","roa")
    filing_party=pick(m.get("filing_party","party"),"party","filed_by","submitter")
    document_title=pick(m.get("document_title","title"),"title","document","doc_title")
    case_number=pick(m.get("case_number","case_number"),"case_number","case no","case")
    court_name=pick(m.get("court_name","court_name"),"court","court_name")
    file_path=pick(m.get("file_path","file_path"),"file_path","path","source_path")
    return {
        "event_date": event_date,
        "kind": kind,
        "docket_text": docket_text,
        "filing_party": filing_party,
        "document_title": document_title,
        "case_number": case_number,
        "court_name": court_name,
        "file_path": file_path,
        "integrity_note": "CANDIDATE_ONLY_NO_LEGAL_INFERENCE",
        "status": "CANDIDATE"
    }

def apply_deadline_rules(events, spec):
    # spec: {"rules":[{"match_contains":["token1","token2"],"days_offset":14,"label":"objection_due"}], "business_days":false}
    if not spec:
        return []
    rules=spec.get("rules") or []
    out=[]
    for e in events:
        dt=e.get("event_date","")
        if not dt:
            continue
        text=(e.get("docket_text","") + " " + e.get("document_title","")).lower()
        for rule in rules:
            toks=[t.lower() for t in (rule.get("match_contains") or [])]
            if toks and all(t in text for t in toks):
                out.append({
                    "trigger_event_date": dt,
                    "rule_label": rule.get("label",""),
                    "days_offset": rule.get("days_offset",""),
                    "computed_deadline": "",  # intentionally blank here unless operator chooses to compute in a separate tool
                    "basis": "operator_spec_match_contains",
                    "source_kind": e.get("kind",""),
                    "source_text": (e.get("docket_text","") or "")[:300],
                    "status_calc": "CALCULATED_CANDIDATE",
                    "status": "CANDIDATE"
                })
    return out

def write_csv(path, rows, fields):
    with open(path,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--roa-csv")
    ap.add_argument("--receipts-csv")
    ap.add_argument("--text")
    ap.add_argument("--text-kind", choices=["roa","receipt"])
    ap.add_argument("--map-json")
    ap.add_argument("--deadline-spec-json")
    ap.add_argument("--out-csv", required=True)
    ap.add_argument("--out-deadlines-csv")
    args=ap.parse_args()

    if not (args.roa_csv or args.receipts_csv or args.text):
        die("Provide --roa-csv and/or --receipts-csv and/or --text")

    mapping={}
    if args.map_json:
        mapping=json.load(open(args.map_json,"r",encoding="utf-8"))

    events=[]
    if args.roa_csv:
        for r in load_csv(args.roa_csv):
            events.append(normalize_row(r,"ROA",mapping.get("roa",{})))
    if args.receipts_csv:
        for r in load_csv(args.receipts_csv):
            events.append(normalize_row(r,"MIFILE_RECEIPT",mapping.get("receipt",{})))
    if args.text:
        if not args.text_kind:
            die("--text-kind required when using --text")
        for ln in read_lines_txt(args.text):
            events.append({
                "event_date":"",
                "kind":"ROA_TEXT" if args.text_kind=="roa" else "RECEIPT_TEXT",
                "docket_text": ln,
                "filing_party":"",
                "document_title":"",
                "case_number":"",
                "court_name":"",
                "file_path": args.text,
                "integrity_note":"CANDIDATE_ONLY_NO_LEGAL_INFERENCE",
                "status":"CANDIDATE"
            })

    fields=["event_date","kind","docket_text","filing_party","document_title","case_number","court_name","file_path","integrity_note","status"]
    write_csv(args.out_csv, events, fields)

    if args.deadline_spec_json and args.out_deadlines_csv:
        spec=json.load(open(args.deadline_spec_json,"r",encoding="utf-8"))
        dl=apply_deadline_rules(events, spec)
        dl_fields=["trigger_event_date","rule_label","days_offset","computed_deadline","basis","source_kind","source_text","status_calc","status"]
        write_csv(args.out_deadlines_csv, dl, dl_fields)

if __name__=="__main__":
    main()
