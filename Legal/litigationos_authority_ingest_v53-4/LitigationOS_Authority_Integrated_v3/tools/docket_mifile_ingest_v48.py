#!/usr/bin/env python3
"""
docket_mifile_ingest_v48.py — NON-INTERPRETIVE DOCKET/RECEIPT INGEST (v48)

Reads a JSON input listing MiFile receipts / ROA docs (PDF or text) and extracts *candidate* docket events:
- timestamps (as found)
- case number (if found)
- document titles / transaction ids (if found)
- filing/fee snippets (if found)
- provenance (source path)

No legal conclusions. No deadline computation.
PDF text extraction uses `pdftotext -layout` if available; otherwise requires pre-extracted .txt.

Input:
  outputs/docket_ingest_in.json  (see docs/schemas/docket_ingest_in.schema.json)

Output:
  outputs/docket_events.json  (JSON with extracted events + raw anchor lines)

Usage:
  python tools/docket_mifile_ingest_v48.py --in-json outputs/docket_ingest_in.json --out-json outputs/docket_events.json
"""
import argparse, json, os, re, subprocess, sys, tempfile, shutil
from shutil import which

def pdftotext_layout(pdf_path, out_txt):
    if which("pdftotext") is None:
        raise SystemExit("pdftotext not found; provide .txt input instead.")
    subprocess.run(["pdftotext","-layout",pdf_path,out_txt], check=False)

def read_text_from_item(path, typ):
    path=os.path.abspath(path)
    if typ.endswith("_pdf") or path.lower().endswith(".pdf"):
        tmpdir=tempfile.mkdtemp(prefix="mifile_v48_")
        try:
            out_txt=os.path.join(tmpdir,"doc.txt")
            pdftotext_layout(path,out_txt)
            txt=open(out_txt,"r",encoding="utf-8",errors="replace").read()
            return txt
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
    else:
        return open(path,"r",encoding="utf-8",errors="replace").read()

DATE_RX=re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")
TIME_RX=re.compile(r"\b(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(AM|PM)?\b", re.IGNORECASE)
CASE_RX=re.compile(r"\b(\d{4}[- ]?\d{6,})\b")  # rough
DOCWORDS=("Document","Pleading","Motion","Order","Receipt","Payment","Filing","Transaction","Case","Docket","Register of Actions")

def extract_anchor_lines(txt, max_lines=4000):
    lines=[l.rstrip("\n") for l in txt.splitlines()]
    # keep non-empty + short-ish
    out=[]
    for l in lines:
        if not l.strip(): 
            continue
        if any(w.lower() in l.lower() for w in DOCWORDS) or DATE_RX.search(l) or CASE_RX.search(l):
            out.append(l.strip())
        if len(out)>=max_lines:
            break
    return out

def build_events(anchor_lines):
    events=[]
    for idx,l in enumerate(anchor_lines):
        d=DATE_RX.search(l)
        c=CASE_RX.search(l)
        t=TIME_RX.search(l)
        if d or c or t:
            events.append({
                "anchor_line_no": idx+1,
                "anchor_line": l,
                "date": d.group(0) if d else "",
                "time": t.group(0) if t else "",
                "case_no_candidate": c.group(0) if c else "",
            })
    return events

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--in-json", required=True)
    ap.add_argument("--out-json", required=True)
    args=ap.parse_args()

    payload=json.load(open(args.in_json,"r",encoding="utf-8"))
    items=payload.get("items") or []
    out={"inputs":items,"events":[]}
    for it in items:
        p=it.get("path") or ""
        typ=it.get("type") or "other"
        if not p:
            continue
        if not os.path.exists(p):
            out["events"].append({"source_path":p,"type":typ,"error":"FILE_NOT_FOUND"})
            continue
        try:
            txt=read_text_from_item(p, typ)
            anchors=extract_anchor_lines(txt)
            events=build_events(anchors)
            out["events"].append({
                "source_path": os.path.abspath(p),
                "type": typ,
                "anchor_lines": anchors[:500],
                "event_candidates": events[:500]
            })
        except Exception as e:
            out["events"].append({"source_path":os.path.abspath(p),"type":typ,"error":repr(e)})
    os.makedirs(os.path.dirname(args.out_json) or ".", exist_ok=True)
    json.dump(out, open(args.out_json,"w",encoding="utf-8"), indent=2, ensure_ascii=False)
    print("OK wrote", args.out_json)

if __name__=="__main__":
    main()
