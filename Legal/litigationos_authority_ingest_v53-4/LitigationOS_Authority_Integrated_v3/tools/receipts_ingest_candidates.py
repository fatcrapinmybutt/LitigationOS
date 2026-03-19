#!/usr/bin/env python3
"""
Receipts Ingest (CANDIDATE-ONLY)
Reads plain text exports of MiFile/Pay receipts or notices (user-provided),
extracts date-like strings and key IDs via conservative regex, emits receipt_events.csv.
No OCR, no scraping, no legal assertions.
Inputs:
--in-text-dir: directory of .txt
Outputs:
--out-receipt-events-csv: receipt_id,receipt_date,extracted_tokens,source_pinpoint
"""
import argparse, os, re, csv, sys
from datetime import datetime

DATE_RE=re.compile(r'\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b')
ID_RE=re.compile(r'\b([A-Z]{2,6}-\d{3,8})\b')
MONEY_RE=re.compile(r'\$\s*\d+(?:\.\d{2})?')

def main():
    ap=argparse.ArgumentParser(description="Ingest receipt/notice text files to receipt events (candidate-only).")
    ap.add_argument("--in-text-dir", required=True)
    ap.add_argument("--out-receipt-events-csv", required=True)
    args=ap.parse_args()

    if not os.path.isdir(args.in_text_dir):
        print("input dir not found", file=sys.stderr); raise SystemExit(2)

    out=[]
    for fn in sorted(os.listdir(args.in_text_dir)):
        if not fn.lower().endswith(".txt"): 
            continue
        p=os.path.join(args.in_text_dir, fn)
        txt=open(p,"r",encoding="utf-8",errors="ignore").read()
        dates=[f"{y}-{m.zfill(2)}-{d.zfill(2)}" for (y,m,d) in DATE_RE.findall(txt)]
        ids=ID_RE.findall(txt)
        monies=MONEY_RE.findall(txt)
        tokens=[]
        for x in ids[:10]: tokens.append(f"ID:{x}")
        for x in monies[:10]: tokens.append(f"AMT:{x}")
        for x in dates[:10]: tokens.append(f"DATE:{x}")
        receipt_date=dates[0] if dates else ""
        out.append({
            "receipt_id": os.path.splitext(fn)[0],
            "receipt_date": receipt_date,
            "extracted_tokens": " | ".join(tokens),
            "source_pinpoint": f"{p}"
        })

    with open(args.out_receipt_events_csv,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=["receipt_id","receipt_date","extracted_tokens","source_pinpoint"])
        w.writeheader()
        for row in out: w.writerow(row)

    print(f"OK receipts={len(out)}")

if __name__=="__main__":
    main()
