#!/usr/bin/env python3
"""
docket_text_to_entries_candidate.py (v41) — CANDIDATE ONLY

Parses plain text ROA/Register of Actions or MiFile receipt text into docket entries JSON
(consumable by docket_mifile_ingest_candidate.py).

NON-INTERPRETIVE:
- Extracts date patterns + remainder line as text
- Does not infer document types beyond shallow keyword tags
- Caller should provide source_path and ensure the text is accurate

Input:
  --in-txt <file>  (text already extracted; use pdftotext externally if needed)
  --source-path <path> (provenance for pinpointing)

Output:
  docket_entries_in.json => {"entries":[{"entry_date":"YYYY-MM-DD","text":"...","source_path":"..."}]}
"""
import argparse, json, re, datetime

# Accept YYYY-MM-DD, MM/DD/YYYY, MM/DD/YY
RE_YMD = re.compile(r'\b(20\d{2}|19\d{2})-(\d{2})-(\d{2})\b')
RE_MDY = re.compile(r'\b(\d{1,2})/(\d{1,2})/((?:20)?\d{2}|19\d{2})\b')

def norm_year(y):
    y=int(y)
    if y < 100:
        y += 2000 if y < 70 else 1900
    return y

def parse_date(s):
    m=RE_YMD.search(s)
    if m:
        y,mn,d=map(int,m.groups())
        return datetime.date(y,mn,d).isoformat()
    m=RE_MDY.search(s)
    if m:
        mn, d, y = m.groups()
        y=norm_year(y)
        return datetime.date(int(y), int(mn), int(d)).isoformat()
    return None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--in-txt", required=True)
    ap.add_argument("--source-path", required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--max", type=int, default=2000)
    args=ap.parse_args()

    lines=[ln.rstrip("\n") for ln in open(args.in_txt,"r",encoding="utf-8",errors="replace")]
    entries=[]
    for ln in lines:
        if not ln.strip():
            continue
        d=parse_date(ln)
        if not d:
            continue
        # Keep full line for non-interpretive retention
        entries.append({
            "entry_date": d,
            "text": ln.strip(),
            "source_path": args.source_path,
            "notes": "CANDIDATE_ONLY_EXTRACTED_FROM_TEXT"
        })
        if len(entries)>=args.max:
            break

    json.dump({"entries":entries,"meta":{"confidence":"CANDIDATE_ONLY","notes":"DATE_LINE_EXTRACTION_ONLY"}}, open(args.out_json,"w",encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"OK entries={len(entries)}")

if __name__=="__main__":
    main()
