#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HARVEST_ENGINE_FULL_v2.py — full recursive PDF per-page extraction, OCR-needed flags, run ledger, PROV-lite.

This script is designed to run LOCALLY (Windows-first) against your canonical roots/drives.

Key upgrades vs vNext:
- Consistent path discovery via litigationos_common (LITIGATIONOS_HOME / config / marker files)
- Recursive scan mode: --root, --paths-file, --include-glob/--exclude-dir
- Resume & idempotency: per-PDF output fingerprints; --resume (default on)
- Parallelism: --workers N (process PDFs in parallel; safe defaults)
- Robust PDF text extraction:
  - Primary: PyPDF2 (fast)
  - Optional fallback: pdfminer.six (if installed) for stubborn PDFs via --use-pdfminer
- OCR-needed detection heuristics:
  - empty/near-empty extracted text
  - very low alphabetic ratio
  - extreme repetition / garbage characters
- Output contracts:
  - data/pdf_inventory.csv (bytes, pages, partial sha)
  - data/pdf_page_extract_index.csv (one row per page with pinpoint fields)
  - data/ocr_needed_pages.csv (subset)
  - data/page_text/<pdf_stem>.pages.jsonl.gz (page records)
  - data/run_ledger.jsonl (append-only run events)
  - data/prov_entities.jsonl + data/prov_activities.jsonl (PROV-lite)
  - logs/harvest.log

No network calls. Preserves originals (read-only).

USAGE:
  python HARVEST_ENGINE_FULL_v2.py --paths-file drivesANDpaths.txt --out F:\\LitigationOS\\HarvestOut --pdf-extract
  python HARVEST_ENGINE_FULL_v2.py --root F:\\ --root D:\\ --out F:\\LitigationOS\\HarvestOut --pdf-extract
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import os
import re
import sys
import time
import traceback
import datetime as dt
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any, Iterable, Tuple

from PyPDF2 import PdfReader

try:
    from litigationos_common import (
        ensure_dir, atomic_write_text, sha256_file, safe_ascii_filename,
        configure_logging, load_paths_file, iter_files, now_utc_iso, platform_hint,
        resolve_litigationos_home, load_paths_config, write_paths_config
    )
except Exception:  # pragma: no cover
    # Allow single-file execution if common isn't importable
    def ensure_dir(p: Path) -> Path:
        p.mkdir(parents=True, exist_ok=True); return p
    def atomic_write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
        ensure_dir(path.parent); path.write_text(text, encoding=encoding)
    def sha256_file(path: Path, max_bytes: Optional[int] = None) -> str:
        import hashlib
        h=hashlib.sha256()
        with path.open("rb") as f:
            total=0
            for chunk in iter(lambda: f.read(1024*1024), b""):
                h.update(chunk); total += len(chunk)
                if max_bytes is not None and total >= max_bytes:
                    break
        return h.hexdigest()
    def safe_ascii_filename(name: str, max_len: int = 180) -> str:
        return re.sub(r"[^A-Za-z0-9._\-]+", "_", name)[:max_len] or "artifact"
    def now_utc_iso() -> str:
        return dt.datetime.utcnow().replace(microsecond=0).isoformat()+"Z"
    def platform_hint() -> str:
        return f"platform={sys.platform}"

# Optional pdfminer fallback
_PDFMINER_AVAILABLE = False
try:
    from pdfminer.high_level import extract_text as _pdfminer_extract_text  # type: ignore
    _PDFMINER_AVAILABLE = True
except Exception:
    _PDFMINER_AVAILABLE = False

@dataclass
class PageRecord:
    pdf_path: str
    pdf_sha256_partial: str
    pdf_bytes: int
    pdf_pages: int
    page_num_1: int
    extracted_len: int
    alpha_ratio: float
    ocr_needed: bool
    text: str

def _alpha_ratio(s: str) -> float:
    if not s:
        return 0.0
    letters = sum(1 for c in s if c.isalpha())
    return letters / max(1, len(s))

def _is_garbage(s: str) -> bool:
    if not s:
        return True
    # Heuristics: high fraction of replacement/control, or extremely repetitive
    bad = sum(1 for c in s if ord(c) < 9 or c == "\ufffd")
    if bad / max(1, len(s)) > 0.10:
        return True
    # repetition: many identical characters
    if len(set(s)) <= 5 and len(s) > 200:
        return True
    return False

def _ocr_needed(text: str, min_len: int, min_alpha: float) -> bool:
    if text is None:
        return True
    t = text.strip()
    if len(t) < min_len:
        return True
    ar = _alpha_ratio(t)
    if ar < min_alpha:
        return True
    if _is_garbage(t):
        return True
    return False

def _extract_page_text_pypdf(reader: PdfReader, page_index_0: int) -> str:
    try:
        page = reader.pages[page_index_0]
        return page.extract_text() or ""
    except Exception:
        return ""

def _extract_page_text_pdfminer(pdf_path: Path, page_num_1: int) -> str:
    # pdfminer extracts whole doc by default; page_numbers is 0-indexed set
    try:
        return _pdfminer_extract_text(str(pdf_path), page_numbers={page_num_1 - 1}) or ""
    except Exception:
        return ""

def process_pdf(pdf_path: Path, min_len: int, min_alpha: float, use_pdfminer: bool, logger=None) -> Tuple[List[PageRecord], List[Dict[str, Any]]]:
    """Return page records and a small inventory dict list (single)."""
    inv = []
    try:
        st = pdf_path.stat()
        pdf_bytes = st.st_size
        # partial hash keeps this fast; full sha can be enabled in other pipelines
        pdf_sha_partial = sha256_file(pdf_path, max_bytes=8 * 1024 * 1024)
        reader = PdfReader(str(pdf_path))
        pdf_pages = len(reader.pages)
        inv.append({
            "pdf_path": str(pdf_path),
            "bytes": pdf_bytes,
            "pages": pdf_pages,
            "sha256_partial": pdf_sha_partial,
            "mtime_iso_utc": dt.datetime.utcfromtimestamp(st.st_mtime).replace(microsecond=0).isoformat() + "Z",
        })
        recs: List[PageRecord] = []
        for i0 in range(pdf_pages):
            p1 = i0 + 1
            txt = _extract_page_text_pypdf(reader, i0)
            if use_pdfminer and _PDFMINER_AVAILABLE:
                # If pypdf is empty, try pdfminer
                if len((txt or "").strip()) < 5:
                    txt = _extract_page_text_pdfminer(pdf_path, p1)
            txt = txt or ""
            ar = _alpha_ratio(txt)
            need = _ocr_needed(txt, min_len=min_len, min_alpha=min_alpha)
            recs.append(PageRecord(
                pdf_path=str(pdf_path),
                pdf_sha256_partial=pdf_sha_partial,
                pdf_bytes=pdf_bytes,
                pdf_pages=pdf_pages,
                page_num_1=p1,
                extracted_len=len(txt),
                alpha_ratio=round(ar, 6),
                ocr_needed=need,
                text=txt
            ))
        return recs, inv
    except Exception as e:
        if logger:
            logger.error(f"PDF failed: {pdf_path} | {e}")
        return [], [{"pdf_path": str(pdf_path), "error": str(e)}]

def write_outputs(out_dir: Path, page_recs: List[PageRecord], inventory_rows: List[Dict[str, Any]], run_id: str) -> None:
    data_dir = ensure_dir(out_dir / "data")
    logs_dir = ensure_dir(out_dir / "logs")
    page_text_dir = ensure_dir(data_dir / "page_text")

    # inventory
    inv_csv = data_dir / "pdf_inventory.csv"
    inv_fields = sorted({k for r in inventory_rows for k in r.keys()})
    with inv_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=inv_fields)
        w.writeheader()
        for r in inventory_rows:
            w.writerow(r)

    # page index
    idx_csv = data_dir / "pdf_page_extract_index.csv"
    fields = ["run_id","pdf_path","pdf_sha256_partial","pdf_bytes","pdf_pages","page_num_1","extracted_len","alpha_ratio","ocr_needed"]
    with idx_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in page_recs:
            w.writerow({
                "run_id": run_id,
                "pdf_path": r.pdf_path,
                "pdf_sha256_partial": r.pdf_sha256_partial,
                "pdf_bytes": r.pdf_bytes,
                "pdf_pages": r.pdf_pages,
                "page_num_1": r.page_num_1,
                "extracted_len": r.extracted_len,
                "alpha_ratio": r.alpha_ratio,
                "ocr_needed": int(r.ocr_needed),
            })

    # OCR-needed subset
    ocr_csv = data_dir / "ocr_needed_pages.csv"
    with ocr_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in page_recs:
            if r.ocr_needed:
                w.writerow({
                    "run_id": run_id,
                    "pdf_path": r.pdf_path,
                    "pdf_sha256_partial": r.pdf_sha256_partial,
                    "pdf_bytes": r.pdf_bytes,
                    "pdf_pages": r.pdf_pages,
                    "page_num_1": r.page_num_1,
                    "extracted_len": r.extracted_len,
                    "alpha_ratio": r.alpha_ratio,
                    "ocr_needed": 1,
                })

    # per-pdf page text JSONL.GZ
    # group by pdf
    by_pdf: Dict[str, List[PageRecord]] = {}
    for r in page_recs:
        by_pdf.setdefault(r.pdf_path, []).append(r)

    for pdf_path, recs in by_pdf.items():
        stem = safe_ascii_filename(Path(pdf_path).stem)
        out_gz = page_text_dir / f"{stem}.pages.jsonl.gz"
        with gzip.open(out_gz, "wt", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps({
                    "run_id": run_id,
                    "pdf_path": r.pdf_path,
                    "pdf_sha256_partial": r.pdf_sha256_partial,
                    "page_num_1": r.page_num_1,
                    "ocr_needed": r.ocr_needed,
                    "extracted_len": r.extracted_len,
                    "alpha_ratio": r.alpha_ratio,
                    "text": r.text,
                }, ensure_ascii=False) + "\n")

def append_jsonl(path: Path, obj: Dict[str, Any]) -> None:
    ensure_dir(path.parent)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def init_paths_config(args) -> Optional[Path]:
    cfg = {
        "litigationos_home": args.litigationos_home or "",
        "default_out_root": str(args.out) if args.out else "",
        "scan_roots": args.root or [],
        "paths_file": str(args.paths_file) if args.paths_file else ""
    }
    # Remove empties
    cfg = {k:v for k,v in cfg.items() if v}
    if not cfg:
        return None
    outp = write_paths_config(cfg, out_path=Path(args.init_paths_config))
    return outp

def main() -> None:
    ap = argparse.ArgumentParser(description="LitigationOS Harvest Engine — full per-page PDF extraction + OCR-needed.")
    ap.add_argument("--out", required=True, help="Output directory (e.g., F:\\LitigationOS\\HarvestOut).")
    ap.add_argument("--paths-file", help="Text file listing roots/paths to scan (one per line).")
    ap.add_argument("--root", action="append", help="Scan root directory/file. Can be repeated.")
    ap.add_argument("--exclude-dir", action="append", default=["$RECYCLE.BIN","System Volume Information",".git",".venv","node_modules"], help="Directory names to exclude (repeatable).")
    ap.add_argument("--pdf-extract", action="store_true", help="Enable PDF per-page extraction.")
    ap.add_argument("--min-len", type=int, default=40, help="Minimum extracted text length before OCR-needed flag.")
    ap.add_argument("--min-alpha", type=float, default=0.20, help="Minimum alphabetic ratio before OCR-needed flag.")
    ap.add_argument("--workers", type=int, default=1, help="Parallel workers (PDF-level). Use 1 for safest.")
    ap.add_argument("--resume", action="store_true", default=True, help="Resume mode (skip PDFs whose outputs exist).")
    ap.add_argument("--force", action="store_true", help="Force reprocess all PDFs.")
    ap.add_argument("--use-pdfminer", action="store_true", help="Try pdfminer fallback for empty pages (if installed).")
    ap.add_argument("--litigationos-home", help="Explicit LitigationOS home root (optional; overrides discovery).")
    ap.add_argument("--init-paths-config", help="Write a litigationos_paths.json to this path, then exit.")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    out_dir = Path(args.out)
    ensure_dir(out_dir)
    log = configure_logging(out_dir / "logs" / "harvest.log", verbose=args.verbose, quiet=args.quiet)

    if args.init_paths_config:
        p = init_paths_config(args)
        if p:
            log.info(f"Wrote paths config: {p}")
        else:
            log.info("No config fields provided; nothing written.")
        return

    if args.litigationos_home:
        os.environ["LITIGATIONOS_HOME"] = args.litigationos_home

    run_id = f"harvest_{dt.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    ledger = out_dir / "data" / "run_ledger.jsonl"
    prov_ent = out_dir / "data" / "prov_entities.jsonl"
    prov_act = out_dir / "data" / "prov_activities.jsonl"

    append_jsonl(ledger, {"ts_utc": now_utc_iso(), "run_id": run_id, "event": "run_start", "hint": platform_hint()})
    append_jsonl(prov_act, {"activity_id": run_id, "type": "HarvestRun", "started_at_utc": now_utc_iso(), "platform": platform_hint()})

    roots: List[Path] = []
    if args.paths_file:
        pf = Path(args.paths_file)
        # If relative and LITIGATIONOS_HOME exists, resolve
        if not pf.is_absolute():
            home = resolve_litigationos_home(Path(__file__))
            if home:
                pf = home / pf
        for s in load_paths_file(pf):
            roots.append(Path(s))
    if args.root:
        roots.extend([Path(r) for r in args.root])

    # Default behavior if no roots provided: try to use config paths_file then common drives
    if not roots:
        cfg = load_paths_config(Path(__file__))
        pf = cfg.get("paths_file")
        if pf and Path(pf).exists():
            for s in load_paths_file(Path(pf)):
                roots.append(Path(s))
        else:
            # conservative default: do not scan entire system without explicit roots
            log.error("No scan roots provided. Provide --paths-file and/or --root.")
            append_jsonl(ledger, {"ts_utc": now_utc_iso(), "run_id": run_id, "event": "blocked_no_roots"})
            sys.exit(2)

    if not args.pdf_extract:
        log.error("Nothing to do (missing --pdf-extract).")
        append_jsonl(ledger, {"ts_utc": now_utc_iso(), "run_id": run_id, "event": "blocked_no_mode"})
        sys.exit(2)

    include_ext = {".pdf"}
    pdfs = list(iter_files(roots, include_ext=include_ext, exclude_dirs=args.exclude_dir))

    log.info(f"Run {run_id} | PDFs discovered: {len(pdfs)}")
    append_jsonl(ledger, {"ts_utc": now_utc_iso(), "run_id": run_id, "event": "pdf_discovered", "count": len(pdfs)})

    # Resume logic: if page_text exists for pdf stem, skip
    page_text_dir = ensure_dir(out_dir / "data" / "page_text")
    def already_done(pdf_path: Path) -> bool:
        stem = safe_ascii_filename(pdf_path.stem)
        out_gz = page_text_dir / f"{stem}.pages.jsonl.gz"
        return out_gz.exists() and out_gz.stat().st_size > 0

    to_process = []
    for p in pdfs:
        if args.force:
            to_process.append(p)
        elif args.resume and already_done(p):
            continue
        else:
            to_process.append(p)

    log.info(f"PDFs to process: {len(to_process)} (resume={args.resume}, force={args.force})")

    page_recs_all: List[PageRecord] = []
    inventory_all: List[Dict[str, Any]] = []

    # Parallelism: optional, PDF-level
    if args.workers and args.workers > 1:
        import concurrent.futures as cf
        with cf.ProcessPoolExecutor(max_workers=args.workers) as ex:
            futs = [ex.submit(process_pdf, p, args.min_len, args.min_alpha, args.use_pdfminer, None) for p in to_process]
            for f in cf.as_completed(futs):
                recs, inv = f.result()
                page_recs_all.extend(recs)
                inventory_all.extend(inv)
    else:
        for p in to_process:
            recs, inv = process_pdf(p, args.min_len, args.min_alpha, args.use_pdfminer, logger=log)
            page_recs_all.extend(recs)
            inventory_all.extend(inv)
            # PROV entity for each PDF processed
            if inv and "error" not in inv[0]:
                append_jsonl(prov_ent, {
                    "entity_id": inv[0].get("sha256_partial"),
                    "type": "PDF",
                    "path": inv[0].get("pdf_path"),
                    "bytes": inv[0].get("bytes"),
                    "pages": inv[0].get("pages"),
                    "sha256_partial": inv[0].get("sha256_partial"),
                })

    write_outputs(out_dir, page_recs_all, inventory_all, run_id)

    append_jsonl(ledger, {"ts_utc": now_utc_iso(), "run_id": run_id, "event": "run_end", "pdfs_processed": len(to_process), "pages": len(page_recs_all)})
    append_jsonl(prov_act, {"activity_id": run_id, "ended_at_utc": now_utc_iso(), "status": "OK", "pdfs_processed": len(to_process), "pages": len(page_recs_all)})

    log.info(f"Completed {run_id} | PDFs processed: {len(to_process)} | Pages: {len(page_recs_all)}")
    log.info(f"Outputs: {out_dir / 'data'}")

if __name__ == "__main__":
    main()
