#!/usr/bin/env python3
"""
form_os_orchestrator.py

Baseline “FormOS” orchestrator:
- Recursively scans root folders (local corpus).
- Explodes ZIPs into a staging area (bounded depth).
- Deduplicates all files into a content-addressed store (CAS) by SHA-256.
- Extracts text from PDF/DOCX/TXT (best-effort), page-marked for PDFs.
- Detects "court forms" heuristically (filename + content signals).
- Extracts "instructions" blocks (best-effort) and stores them as fulltext with page markers.
- Writes all metadata into a SQLite DB.

This script is meant as a starting point for Copilot to expand into a full agent swarm pipeline.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import mimetypes
import os
import re
import shutil
import sqlite3
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

PDF_TEXT_AVAILABLE = True
try:
    from pypdf import PdfReader
except Exception:
    PDF_TEXT_AVAILABLE = False

DOCX_AVAILABLE = True
try:
    import docx  # python-docx
except Exception:
    DOCX_AVAILABLE = False

def now_iso() -> str:
    return _dt.datetime.now().isoformat(timespec="seconds")

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def safe_mkdir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def is_zip(path: Path) -> bool:
    return path.suffix.lower() == ".zip" and zipfile.is_zipfile(path)

def guess_mime(path: Path) -> str:
    mt, _ = mimetypes.guess_type(str(path))
    return mt or "application/octet-stream"

@dataclass
class Config:
    roots: List[str]
    vault_root: str
    sqlite_db: str
    explode_zips: bool = True
    max_zip_depth: int = 6
    extract_pdf_text: bool = True
    pdf_text_min_chars_per_page: int = 50
    enable_ocr: bool = False
    ocr_tool: str = "ocrmypdf"

def load_config(path: Path) -> Config:
    data = json.loads(path.read_text(encoding="utf-8"))
    return Config(**data)

def connect_db(db_path: Path) -> sqlite3.Connection:
    safe_mkdir(db_path.parent)
    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA journal_mode=WAL;")
    return con

def run_schema(con: sqlite3.Connection, schema_path: Path) -> None:
    con.executescript(schema_path.read_text(encoding="utf-8"))
    con.commit()

def cas_store(vault_root: Path, src_path: Path, sha: str) -> Path:
    ext = src_path.suffix.lower().lstrip(".") or "bin"
    obj_dir = vault_root / "00_OBJECTS" / sha[:2]
    safe_mkdir(obj_dir)
    dest = obj_dir / f"{sha}.{ext}"
    if not dest.exists():
        shutil.copy2(src_path, dest)
    return dest

def iter_files(root: Path) -> Iterable[Path]:
    skip = {".git", "__pycache__", "node_modules"}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip]
        for fn in filenames:
            yield Path(dirpath) / fn

def explode_zip(zip_path: Path, out_dir: Path, depth: int, max_depth: int) -> None:
    if depth > max_depth:
        return
    safe_mkdir(out_dir)
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(out_dir)
    except Exception as ex:
        print(f"[WARN] Failed to unzip {zip_path}: {ex}", file=sys.stderr)
        return
    for p in out_dir.rglob("*.zip"):
        if zipfile.is_zipfile(p):
            explode_zip(p, p.with_suffix(""), depth + 1, max_depth)

def pdf_extract_text_pages(pdf_path: Path, min_chars_per_page: int) -> Tuple[List[Dict], str, float, bool]:
    if not PDF_TEXT_AVAILABLE:
        return [], "", 0.0, True
    try:
        reader = PdfReader(str(pdf_path))
        pages: List[Dict] = []
        total_chars = 0
        low_pages = 0
        for i, pg in enumerate(reader.pages):
            try:
                txt = pg.extract_text() or ""
            except Exception:
                txt = ""
            cc = len(txt.strip())
            total_chars += cc
            if cc < min_chars_per_page:
                low_pages += 1
            pages.append({"page": i + 1, "text": txt, "char_count": cc})
        n = max(len(pages), 1)
        avg = total_chars / n
        quality = min(avg / 1500.0, 1.0)
        needs_ocr = (low_pages / n) > 0.5
        fulltext = "\n\n".join([f"---PAGE {p['page']:04d}---\n{p['text']}" for p in pages])
        return pages, fulltext, float(quality), bool(needs_ocr)
    except Exception as ex:
        print(f"[WARN] PDF text extract failed: {pdf_path}: {ex}", file=sys.stderr)
        return [], "", 0.0, True

def docx_extract_text(docx_path: Path) -> str:
    if not DOCX_AVAILABLE:
        return ""
    try:
        d = docx.Document(str(docx_path))
        return "\n".join([p.text for p in d.paragraphs if p.text]).strip()
    except Exception as ex:
        print(f"[WARN] DOCX extract failed: {docx_path}: {ex}", file=sys.stderr)
        return ""

FORM_FILENAME_HINTS = [
    r"\bfoc\s*\d+\b", r"\bmc\s*\d+\b", r"\bdc\s*\d+\b", r"\bcc\s*\d+\b", r"\bpc\s*\d+\b", r"\bjc\s*\d+\b",
    r"\bform\b", r"\binstructions?\b", r"\bpetition\b", r"\bmotion\b", r"\bsummons\b", r"\bnotice\b"
]
FORM_TEXT_HINTS = [
    "approved", "instructions", "for office use only", "case no.", "court address",
    "plaintiff", "defendant", "petitioner", "respondent"
]

def looks_like_form(path: Path, extracted_text: str) -> bool:
    name = path.name.lower()
    if any(re.search(p, name) for p in FORM_FILENAME_HINTS):
        return True
    lt = extracted_text.lower()
    hits = sum(1 for s in FORM_TEXT_HINTS if s in lt)
    return hits >= 3

def deterministic_id(*parts: str, n: int = 24) -> str:
    h = hashlib.sha256("|".join(parts).encode("utf-8", errors="ignore")).hexdigest()
    return h[:n]

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, help="Path to config JSON")
    ap.add_argument("--schema", required=True, help="Path to schema.sql")
    ap.add_argument("--run", action="store_true", help="Execute ingestion pipeline")
    args = ap.parse_args()

    cfg = load_config(Path(args.config))
    vault_root = Path(cfg.vault_root)
    db_path = Path(cfg.sqlite_db)
    schema_path = Path(args.schema)

    safe_mkdir(vault_root)
    con = connect_db(db_path)
    run_schema(con, schema_path)

    run_id = deterministic_id(now_iso(), json.dumps(cfg.roots), n=26)
    con.execute(
        "INSERT OR REPLACE INTO ingest_runs(run_id, started_at, roots_json) VALUES(?,?,?)",
        (run_id, now_iso(), json.dumps(cfg.roots))
    )
    con.commit()

    staging = vault_root / "_STAGING_ZIPS"
    if staging.exists():
        shutil.rmtree(staging, ignore_errors=True)
    safe_mkdir(staging)

    expanded_roots: List[Path] = [Path(r) for r in cfg.roots]
    if cfg.explode_zips:
        for r in list(expanded_roots):
            if not r.exists():
                continue
            for f in iter_files(r):
                if is_zip(f):
                    sha = sha256_file(f)
                    out_dir = staging / deterministic_id(str(f), sha, n=32)
                    explode_zip(f, out_dir, 1, cfg.max_zip_depth)
                    expanded_roots.append(out_dir)

    doc_count = 0
    form_count = 0

    for root in expanded_roots:
        if not root.exists():
            continue
        for f in iter_files(root):
            if not f.is_file():
                continue
            try:
                size = f.stat().st_size
            except Exception:
                continue
            if size <= 0:
                continue

            sha = sha256_file(f)
            stored = cas_store(vault_root, f, sha)
            doc_id = deterministic_id(sha, str(stored), n=24)
            ext = f.suffix.lower()
            mime = guess_mime(f)

            con.execute(
                "INSERT OR IGNORE INTO documents(doc_id, sha256, size_bytes, ext, mime, original_path, stored_object_path, created_at) VALUES(?,?,?,?,?,?,?,?)",
                (doc_id, sha, size, ext, mime, str(f), str(stored), now_iso())
            )
            doc_count += 1

            extraction_id = None
            extracted_text = ""

            if ext == ".pdf" and cfg.extract_pdf_text:
                pages, fulltext, quality, needs_ocr = pdf_extract_text_pages(f, cfg.pdf_text_min_chars_per_page)
                if fulltext:
                    out_dir = vault_root / "90_REPORTS" / "extractions" / sha[:2] / sha
                    safe_mkdir(out_dir / "pages")
                    pages_meta = []
                    for p in pages:
                        tp = out_dir / "pages" / f"p{p['page']:04d}.txt"
                        tp.write_text(p["text"] or "", encoding="utf-8")
                        pages_meta.append({"page": p["page"], "text_path": str(tp), "char_count": p["char_count"]})
                    full_path = out_dir / "fulltext.txt"
                    full_path.write_text(fulltext, encoding="utf-8")
                    ex_sha = hashlib.sha256(fulltext.encode("utf-8", errors="ignore")).hexdigest()
                    extraction_id = deterministic_id(doc_id, "pdf_text", ex_sha, n=24)
                    con.execute(
                        "INSERT OR IGNORE INTO extractions(extraction_id, doc_id, method, quality_score, needs_ocr, pages_json, fulltext_path, sha256, created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                        (extraction_id, doc_id, "pdf_text", quality, int(needs_ocr), json.dumps(pages_meta), str(full_path), ex_sha, now_iso())
                    )
                    con.commit()
                    extracted_text = fulltext

            elif ext == ".docx" and DOCX_AVAILABLE:
                txt = docx_extract_text(f)
                if txt:
                    out_dir = vault_root / "90_REPORTS" / "extractions" / sha[:2] / sha
                    safe_mkdir(out_dir)
                    full_path = out_dir / "fulltext.txt"
                    full_path.write_text(txt, encoding="utf-8")
                    ex_sha = hashlib.sha256(txt.encode("utf-8", errors="ignore")).hexdigest()
                    extraction_id = deterministic_id(doc_id, "docx", ex_sha, n=24)
                    con.execute(
                        "INSERT OR IGNORE INTO extractions(extraction_id, doc_id, method, quality_score, needs_ocr, pages_json, fulltext_path, sha256, created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                        (extraction_id, doc_id, "docx", 1.0, 0, None, str(full_path), ex_sha, now_iso())
                    )
                    con.commit()
                    extracted_text = txt

            elif ext in (".txt", ".md"):
                try:
                    txt = f.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    txt = ""
                if txt:
                    out_dir = vault_root / "90_REPORTS" / "extractions" / sha[:2] / sha
                    safe_mkdir(out_dir)
                    full_path = out_dir / "fulltext.txt"
                    full_path.write_text(txt, encoding="utf-8")
                    ex_sha = hashlib.sha256(txt.encode("utf-8", errors="ignore")).hexdigest()
                    extraction_id = deterministic_id(doc_id, "txt", ex_sha, n=24)
                    con.execute(
                        "INSERT OR IGNORE INTO extractions(extraction_id, doc_id, method, quality_score, needs_ocr, pages_json, fulltext_path, sha256, created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                        (extraction_id, doc_id, "txt", 1.0, 0, None, str(full_path), ex_sha, now_iso())
                    )
                    con.commit()
                    extracted_text = txt

            if extraction_id and looks_like_form(f, extracted_text):
                form_id = deterministic_id(doc_id, "FORM", n=24)
                con.execute(
                    "INSERT OR IGNORE INTO forms(form_id, doc_id, detected_by, created_at) VALUES(?,?,?,?)",
                    (form_id, doc_id, "heuristic", now_iso())
                )
                instr_dir = vault_root / "10_FORMS" / "UNCLASSIFIED" / "UNKNOWN" / "UNKNOWN" / form_id / "extracted"
                safe_mkdir(instr_dir)
                instr_path = instr_dir / "instructions_fulltext.txt"
                instr_path.write_text(extracted_text.strip(), encoding="utf-8")
                instr_sha = hashlib.sha256(extracted_text.encode("utf-8", errors="ignore")).hexdigest()
                instr_id = deterministic_id(form_id, "INSTR", instr_sha, n=24)
                con.execute(
                    "INSERT OR IGNORE INTO form_instructions(instr_id, form_id, extraction_id, instruction_fulltext_path, instruction_sha256, created_at) VALUES(?,?,?,?,?,?)",
                    (instr_id, form_id, extraction_id, str(instr_path), instr_sha, now_iso())
                )
                con.commit()
                form_count += 1

    stats = {"documents_seen": doc_count, "forms_detected": form_count}
    con.execute("UPDATE ingest_runs SET ended_at=?, stats_json=? WHERE run_id=?",
                (now_iso(), json.dumps(stats), run_id))
    con.commit()
    con.close()
    print(f"OK: run_id={run_id} documents={doc_count} forms={form_count}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
