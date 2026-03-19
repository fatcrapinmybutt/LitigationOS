#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_roa_from_pdf.py (ROA column-aware)

Parses ROA PDFs where OCR splits the "Date" and "Code" into separate lines.

Usage:
  python scripts/extract_roa_from_pdf.py --root .
"""
from __future__ import annotations
import argparse, csv, json, re
from pathlib import Path

DATE_ONLY = re.compile(r"^\s*(\d{2})\s*/\s*(\d{2})\s*/\s*(\d{4})\s*$")
CODE_ONLY = re.compile(r"^[A-Z0-9]{2,4}$")
PARTY_ONLY = re.compile(r"^[DP]\s*\d{3}$")
PARTY_CODE = re.compile(r"^([DP])\s*(\d{3})\s+([A-Z0-9]{2,4})$")

def norm_line(s: str) -> str:
    s = s.replace("\x00","").strip()
    return re.sub(r"\s+", " ", s)

def norm_date(s: str) -> str:
    m = DATE_ONLY.match(s)
    if not m: return s.strip()
    return f"{m.group(1)}/{m.group(2)}/{m.group(3)}"

def extract_text(pdf: Path) -> str:
    import fitz
    doc = fitz.open(str(pdf))
    return "\n".join([p.get_text("text") for p in doc])

def parse_roa_lines(lines):
    events=[]
    i=0
    n=len(lines)
    while i<n:
        ln = lines[i]
        if DATE_ONLY.match(ln):
            date = norm_date(ln)
            i += 1
            party = ""
            code = ""
            look = 0
            while i<n and look < 6:
                t = lines[i]
                if DATE_ONLY.match(t): break
                mpc = PARTY_CODE.match(t)
                if mpc and not code:
                    party = f"{mpc.group(1)} {mpc.group(2)}"
                    code = mpc.group(3)
                    i += 1
                    look += 1
                    break
                if PARTY_ONLY.match(t) and not party:
                    party = norm_line(t); i += 1; look += 1; continue
                if CODE_ONLY.match(t) and not code:
                    code = norm_line(t); i += 1; look += 1; break
                break
            desc_lines=[]
            while i<n and not DATE_ONLY.match(lines[i]):
                desc_lines.append(lines[i]); i += 1
            title = desc_lines[0] if desc_lines else ""
            detail = "\n".join(desc_lines[1:]).strip() if len(desc_lines)>1 else ""
            events.append({"date": date, "party": party, "code": code, "title": title, "detail": detail})
        else:
            i += 1
    return events

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    args = ap.parse_args()
    root = Path(args.root).expanduser().resolve()
    orig = root/"intake"/"original"
    norm = root/"intake"/"normalized"
    rep = root/"reports"
    norm.mkdir(parents=True, exist_ok=True)
    rep.mkdir(parents=True, exist_ok=True)

    rows=[]
    for pdf in sorted(orig.glob("ppo docket_*.pdf")):
        raw = extract_text(pdf)
        (norm/(pdf.stem + ".txt")).write_text(raw.replace("\r\n","\n").replace("\r","\n"), encoding="utf-8", errors="replace")
        lines = [norm_line(x) for x in raw.splitlines() if norm_line(x)]
        evs = parse_roa_lines(lines)
        for seq, ev in enumerate(evs, 1):
            rows.append({"source_pdf": pdf.name, "seq": seq, **ev})

    out_csv = rep/"ppo_roa_entries.csv"
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["source_pdf","seq","date","party","code","title","detail"])
        w.writeheader()
        for r in rows: w.writerow(r)

    out_jsonl = rep/"ppo_roa_entries.jsonl"
    with out_jsonl.open("w", encoding="utf-8") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print("Entries:", len(rows))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
