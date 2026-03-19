#!/usr/bin/env python3
import argparse, csv, os, re, sys, datetime

DATE_ISO=re.compile(r'\b(\d{4}-\d{2}-\d{2})\b')
DATE_US =re.compile(r'\b(\d{1,2}/\d{1,2}/\d{2,4})\b')

def die(msg, code=2):
    print(msg, file=sys.stderr); raise SystemExit(code)

def parse_date_token(s):
    m=DATE_ISO.search(s)
    if m:
        return m.group(1)
    m=DATE_US.search(s)
    if m:
        token=m.group(1)
        parts=token.split("/")
        if len(parts)==3:
            mm=int(parts[0]); dd=int(parts[1]); yy=int(parts[2])
            if yy<100: yy += 2000
            try:
                return datetime.date(yy,mm,dd).isoformat()
            except Exception:
                return ""
    return ""

def main():
    ap=argparse.ArgumentParser(description="ROA/Receipt Text Parser (candidate-only)")
    ap.add_argument("--text", required=True)
    ap.add_argument("--kind", choices=["ROA_TEXT","RECEIPT_TEXT"], required=True)
    ap.add_argument("--case-number", default="")
    ap.add_argument("--court-name", default="")
    ap.add_argument("--out-csv", required=True)
    args=ap.parse_args()

    if not os.path.exists(args.text):
        die("Text file missing")

    rows=[]
    with open(args.text,"r",encoding="utf-8",errors="replace") as f:
        for ln in f:
            ln=ln.strip()
            if not ln:
                continue
            dt=parse_date_token(ln)
            rows.append({
                "event_date": dt,
                "kind": args.kind,
                "docket_text": ln,
                "filing_party":"",
                "document_title":"",
                "case_number": args.case_number,
                "court_name": args.court_name,
                "file_path": args.text,
                "integrity_note":"CANDIDATE_ONLY_NO_LEGAL_INFERENCE",
                "status":"CANDIDATE"
            })

    fields=["event_date","kind","docket_text","filing_party","document_title","case_number","court_name","file_path","integrity_note","status"]
    with open(args.out_csv,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for r in rows: w.writerow(r)

if __name__=="__main__":
    main()
