#!/usr/bin/env python3
"""
Docket/MiFile Ingest Candidates v25 (NON-INTERPRETIVE)
Converts ROA CSV + receipt JSONL into a candidate deadlines CSV.
Explicit dates only; no computed offsets.
"""
import argparse, csv, json, os, re, sys
from datetime import datetime

DATE_PATTERNS=[
    ("%Y-%m-%d", re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")),
    ("%m/%d/%Y", re.compile(r"\b(\d{1,2}/\d{1,2}/\d{4})\b")),
    ("%m/%d/%y", re.compile(r"\b(\d{1,2}/\d{1,2}/\d{2})\b"))
]
KEYWORDS=re.compile(r"(response\s+due|due\s+date|deadline|hearing\s+date|trial\s+date)", re.IGNORECASE)

def parse_first_date(s):
    s=(s or "")
    for fmt,rx in DATE_PATTERNS:
        m=rx.search(s)
        if m:
            try:
                dt=datetime.strptime(m.group(1), fmt)
                return dt.date().isoformat()
            except Exception:
                pass
    return ""

def read_jsonl(path):
    with open(path,"r",encoding="utf-8") as f:
        for i,ln in enumerate(f,1):
            ln=ln.strip()
            if not ln: 
                continue
            yield i, json.loads(ln)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--roa-csv", default="")
    ap.add_argument("--receipts-jsonl", default="")
    ap.add_argument("--case-id", required=True)
    ap.add_argument("--out-deadlines-csv", required=True)
    args=ap.parse_args()

    rows=[]

    if args.roa_csv and os.path.exists(args.roa_csv) and os.path.getsize(args.roa_csv)>0:
        with open(args.roa_csv,"r",encoding="utf-8",errors="ignore") as f:
            rdr=csv.DictReader(f)
            for idx,r in enumerate(rdr,1):
                blob=" | ".join([str(v or "") for v in r.values()])
                if not KEYWORDS.search(blob):
                    continue
                dd=parse_first_date(blob)
                if not dd:
                    continue
                rows.append({
                    "case_id": args.case_id,
                    "deadline_date": dd,
                    "deadline_type": "CANDIDATE_FROM_ROA_EXPLICIT_DATE",
                    "source_pinpoint": f"ROA:{idx}",
                    "notes": blob[:400]
                })

    if args.receipts_jsonl and os.path.exists(args.receipts_jsonl) and os.path.getsize(args.receipts_jsonl)>0:
        for ln_idx,obj in read_jsonl(args.receipts_jsonl):
            blob=json.dumps(obj, ensure_ascii=False)
            if not KEYWORDS.search(blob):
                continue
            dd=parse_first_date(blob)
            if not dd:
                continue
            rows.append({
                "case_id": args.case_id,
                "deadline_date": dd,
                "deadline_type": "CANDIDATE_FROM_RECEIPT_EXPLICIT_DATE",
                "source_pinpoint": f"RECEIPT:{ln_idx}",
                "notes": blob[:400]
            })

    with open(args.out_deadlines_csv,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=["case_id","deadline_date","deadline_type","source_pinpoint","notes"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"OK candidates={len(rows)}")

if __name__=="__main__":
    main()
