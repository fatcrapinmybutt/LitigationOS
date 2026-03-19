#!/usr/bin/env python3
"""
pdf_locator_helper_v47.py — NON-INTERPRETIVE PDF LOCATOR HELPER (v47)

Purpose: given a PDF + a literal search string (or regex), produce *candidate* locator hints:
- page number(s)
- character offsets in that page's pdftotext -layout output
- a minimal direct excerpt window (no rewriting)

This helps the operator fill pinpoint locators for facts (page/line).
It does not OCR; it relies on `pdftotext` being available in PATH.

Usage:
  python tools/pdf_locator_helper_v47.py --pdf <file.pdf> --query "exact phrase" --out-json outputs/locator_hits.json
  python tools/pdf_locator_helper_v47.py --pdf <file.pdf> --regex "MCR\s+3\.207" --out-json outputs/locator_hits.json

Notes:
- Extracts one .txt per page in a temp dir (deterministic naming).
- Does not modify your PDF.
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile

def require_pdftotext():
    from shutil import which
    if which("pdftotext") is None:
        print("ERROR: pdftotext not found in PATH. Install poppler and ensure pdftotext is available.", file=sys.stderr)
        raise SystemExit(2)

def run_pdftotext_pages(pdf_path, out_dir):
    # pdftotext supports -f/-l for page range; we first determine page count using pdfinfo if available; else brute 1..5000 until fail is avoided by try/except? 
    # Here: prefer pdfinfo when present; else run pdftotext once for whole and split by formfeed is unreliable with -layout. We choose pdfinfo optional.
    from shutil import which
    page_count=None
    if which("pdfinfo"):
        p=subprocess.run(["pdfinfo", pdf_path], capture_output=True, text=True)
        if p.returncode==0:
            m=re.search(r"Pages:\s+(\d+)", p.stdout)
            if m:
                page_count=int(m.group(1))
    if page_count is None:
        # fallback: try pages incrementally until pdftotext fails; cap 5000
        page_count=0
        for i in range(1,5001):
            tmp=os.path.join(out_dir, f"page_{i:05d}.txt")
            pr=subprocess.run(["pdftotext","-layout","-f",str(i),"-l",str(i),pdf_path,tmp], capture_output=True, text=True)
            if pr.returncode!=0 or (not os.path.exists(tmp)) or os.path.getsize(tmp)==0:
                # stop after first failure once we've seen at least one page
                if page_count>0:
                    break
            else:
                page_count=i
        if page_count==0:
            raise SystemExit("Could not extract any page text via pdftotext.")
        return page_count

    for i in range(1,page_count+1):
        out_txt=os.path.join(out_dir, f"page_{i:05d}.txt")
        subprocess.run(["pdftotext","-layout","-f",str(i),"-l",str(i),pdf_path,out_txt], check=False)
    return page_count

def find_hits(text, q=None, rx=None):
    hits=[]
    if q is not None:
        start=0
        while True:
            idx=text.lower().find(q.lower(), start)
            if idx==-1: break
            hits.append({"start":idx,"end":idx+len(q)})
            start=idx+max(1,len(q))
    else:
        for m in rx.finditer(text):
            hits.append({"start":m.start(),"end":m.end()})
    return hits

def excerpt(text, start, end, window=200):
    a=max(0,start-window)
    b=min(len(text),end+window)
    return text[a:b]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--query", default=None, help="literal phrase")
    ap.add_argument("--regex", default=None, help="regex pattern")
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--max-hits", type=int, default=50)
    ap.add_argument("--window", type=int, default=200)
    args=ap.parse_args()

    if (args.query is None) == (args.regex is None):
        print("ERROR: provide exactly one of --query or --regex", file=sys.stderr)
        raise SystemExit(2)

    require_pdftotext()
    pdf_path=os.path.abspath(args.pdf)
    tmpdir=tempfile.mkdtemp(prefix="pdf_loc_v47_")
    try:
        pages=run_pdftotext_pages(pdf_path, tmpdir)
        rx=re.compile(args.regex, re.IGNORECASE) if args.regex else None
        results=[]
        total=0
        for i in range(1,pages+1):
            pth=os.path.join(tmpdir, f"page_{i:05d}.txt")
            if not os.path.exists(pth): 
                continue
            txt=open(pth,"r",encoding="utf-8",errors="replace").read()
            hs=find_hits(txt, q=args.query, rx=rx)
            if not hs: 
                continue
            for h in hs[: max(0,args.max_hits-total)]:
                total+=1
                results.append({
                    "page": i,
                    "start": h["start"],
                    "end": h["end"],
                    "excerpt": excerpt(txt, h["start"], h["end"], window=args.window)
                })
                if total>=args.max_hits:
                    break
            if total>=args.max_hits:
                break

        out={
          "pdf": pdf_path,
          "mode": "query" if args.query else "regex",
          "query": args.query if args.query else args.regex,
          "hits": results
        }
        os.makedirs(os.path.dirname(args.out_json) or ".", exist_ok=True)
        json.dump(out, open(args.out_json,"w",encoding="utf-8"), indent=2, ensure_ascii=False)
        print("OK hits=", len(results), "->", args.out_json)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

if __name__=="__main__":
    main()
