#!/usr/bin/env python3
"""HARVEST_ENGINE_FULL_vNext — Removes page-cap; full per-page extraction + OCR-needed flags.

Run locally:
  python HARVEST_ENGINE_FULL_vNext.py --paths-file drivesANDpaths.txt --out F:\\LitigationOS\\HarvestOut --pdf-extract

Outputs:
- data/sor_manifest.json
- data/pdf_page_extract_index.csv
- data/ocr_needed_pages.csv
- data/page_text/*.jsonl.gz (one per PDF)

"""
from __future__ import annotations
import argparse, json, re, hashlib, datetime, gzip, csv
from pathlib import Path
from PyPDF2 import PdfReader

def sha256_file(p: Path, max_bytes: int|None=None) -> str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        total=0
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk); total += len(chunk)
            if max_bytes is not None and total >= max_bytes:
                return ""
    return h.hexdigest()

def safe_ascii(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", s)[:200]

def load_roots(paths_file: Path):
    roots=[]
    for line in paths_file.read_text(encoding="utf-8", errors="replace").splitlines():
        line=line.strip()
        if line and not line.startswith("#"):
            roots.append(line)
    return sorted(set(roots))

def iter_files(root: Path):
    if root.is_file():
        yield root
    else:
        for p in root.rglob("*"):
            if p.is_file():
                yield p

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--paths-file", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--pdf-extract", action="store_true")
    ap.add_argument("--ocr-empty-threshold", type=int, default=30)
    ap.add_argument("--max-hash-bytes", type=int, default=250*1024*1024)
    args=ap.parse_args()

    out=Path(args.out); out.mkdir(parents=True, exist_ok=True)
    data=out/"data"; data.mkdir(parents=True, exist_ok=True)

    roots=load_roots(Path(args.paths_file))
    sor=[]
    for r in roots:
        rp=Path(r)
        if not rp.exists():
            sor.append({"path": r, "missing": True}); continue
        for p in iter_files(rp):
            try:
                st=p.stat()
                rec={"path": str(p), "bytes": st.st_size,
                     "mtime": datetime.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")}
                rec["sha256"]=sha256_file(p, max_bytes=args.max_hash_bytes)
                sor.append(rec)
            except Exception as e:
                sor.append({"path": str(p), "error": str(e)})
    (data/"sor_manifest.json").write_text(json.dumps({"generated_at":datetime.datetime.now().isoformat(), "roots":roots, "files":sor}, indent=2), encoding="utf-8")

    if args.pdf_extract:
        page_text_dir=data/"page_text"; page_text_dir.mkdir(parents=True, exist_ok=True)
        idx=[]
        for rec in sor:
            pth=rec.get("path","")
            if not pth.lower().endswith(".pdf"):
                continue
            pdf=Path(pth)
            if not pdf.exists():
                continue
            doc_sha=rec.get("sha256") or sha256_file(pdf)
            doc_id=f"PDF::{doc_sha[:16]}" if doc_sha else f"PDF::{safe_ascii(pdf.name)}"
            out_gz=page_text_dir/(safe_ascii(pdf.stem)+"__pages.jsonl.gz")
            try:
                reader=PdfReader(str(pdf))
                with gzip.open(out_gz, "wt", encoding="utf-8") as g:
                    for i,pg in enumerate(reader.pages, start=1):
                        try:
                            txt=pg.extract_text() or ""
                        except Exception:
                            txt=""
                        txt_norm=re.sub(r"\s+"," ", txt.replace("\x00"," ")).strip()
                        needs_ocr=(len(txt_norm)<args.ocr_empty_threshold)
                        g.write(json.dumps({
                            "doc_name": pdf.name,
                            "doc_path": str(pdf),
                            "doc_sha256": doc_sha,
                            "doc_id": doc_id,
                            "page": i,
                            "char_count": len(txt_norm),
                            "needs_ocr": needs_ocr
                        })+"\n")
                        idx.append({
                            "doc_name": pdf.name,
                            "doc_path": str(pdf),
                            "doc_sha256": doc_sha,
                            "doc_id": doc_id,
                            "page": i,
                            "char_count": len(txt_norm),
                            "needs_ocr": "Y" if needs_ocr else "N",
                            "extract_file": str(out_gz)
                        })
            except Exception as e:
                idx.append({"doc_name": pdf.name, "doc_path": str(pdf), "error": str(e)})

        if idx:
            fields=sorted({k for r in idx for k in r.keys()})
            with (data/"pdf_page_extract_index.csv").open("w", newline="", encoding="utf-8") as f:
                w=csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(idx)
            ocr=[r for r in idx if r.get("needs_ocr")=="Y" and r.get("page")]
            fields2=sorted({k for r in ocr for k in r.keys()}) if ocr else fields
            with (data/"ocr_needed_pages.csv").open("w", newline="", encoding="utf-8") as f:
                w=csv.DictWriter(f, fieldnames=fields2); w.writeheader(); w.writerows(ocr)

if __name__=="__main__":
    main()
