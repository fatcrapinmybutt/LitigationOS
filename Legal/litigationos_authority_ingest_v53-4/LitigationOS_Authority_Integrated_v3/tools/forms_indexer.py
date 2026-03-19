#!/usr/bin/env python3
"""
Forms Indexer v28 (NON-INTERPRETIVE)
Scans a directory tree for likely SCAO/MC/FOC forms and extracts minimal metadata from filenames
and the first lines of extracted text files if present (no rewriting).
Outputs JSONL with: form_id, file_path, filename, extracted_tokens, title_line (direct extraction only)
"""
import argparse, json, os, re, sys

FORM_RX=re.compile(r'\b(MC|FOC)\s*[-_ ]?\s*(\d{2,4}[A-Z]?)\b', re.IGNORECASE)

def tokenize(s):
    s=(s or "").strip()
    toks=re.findall(r"[A-Za-z0-9/.-]{2,}", s)
    return toks[:60]

def read_first_lines_text(path, max_lines=5, max_chars=500):
    try:
        with open(path,"r",encoding="utf-8",errors="ignore") as f:
            lines=[]
            for _ in range(max_lines):
                ln=f.readline()
                if not ln: break
                ln=ln.rstrip("\n")
                if ln.strip():
                    lines.append(ln.strip())
            blob=" | ".join(lines)[:max_chars]
            return blob
    except Exception:
        return ""

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="directory to scan")
    ap.add_argument("--out-jsonl", required=True)
    args=ap.parse_args()

    if not os.path.isdir(args.root):
        print("root not a directory", file=sys.stderr); raise SystemExit(2)

    rows=[]
    for r,ds,fs in os.walk(args.root):
        for fn in fs:
            if fn.startswith("."): 
                continue
            lp=fn.lower()
            if not (lp.endswith(".pdf") or lp.endswith(".docx") or lp.endswith(".txt") or lp.endswith(".rtf")):
                continue
            rel=os.path.relpath(os.path.join(r,fn), args.root).replace("\\","/")
            m=FORM_RX.search(fn)
            form_id=""
            if m:
                form_id=f"{m.group(1).upper()}-{m.group(2).upper()}"
            title_line=""
            if lp.endswith(".txt"):
                title_line=read_first_lines_text(os.path.join(r,fn))
            toks=tokenize(fn + " " + title_line)
            rows.append({
                "form_id": form_id,
                "file_path": rel,
                "filename": fn,
                "extracted_tokens": toks,
                "title_line": title_line
            })

    with open(args.out_jsonl,"w",encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"OK forms_indexed={len(rows)}")

if __name__=="__main__":
    main()
