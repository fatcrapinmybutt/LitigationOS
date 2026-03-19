#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bridge_drive_meek_intake_optimized.py
=====================================
Purpose
  High-performance, duplicate-safe, resumable bridge that ingests evidence from your local
  Google Drive sync and BOTH local drives (Z:\ and F:\) into Litigation OS intake folders:
    • F:\MEEK1  (housing / Shady Oaks)
    • F:\MEEK2  (custody / PPO)

Highlights
  • Fast recursive scan (os.scandir), large I/O buffers
  • Excludes system/trash and destination folders (prevents loops)
  • Keyword router (filename + path) -> MEEK1 vs MEEK2
  • Safe ZIP extraction (ZipSlip-proof), preserves metadata
  • Duplicate detection (size+mtime quick path; optional SHA-256)
  • Thread-safe manifest writes and per-target copy locks
  • Atomic copy to temp then replace
  • Threaded copy (configurable workers) + optional tqdm live progress
  • Resumable CSV+JSONL manifest with short stats
  • Dry-run mode
  • Windows-friendly; Python 3.9+

New switches
  • --audit               (route forecast by bucket, then exit)
  • --default-bucket      (fallback bucket for unmatched: M1|M2|none)
  • --min-bytes N         (skip tiny files below N bytes)
"""

from __future__ import annotations
import argparse
import concurrent.futures as futures
import csv
import hashlib
import json
import os
import shutil
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

# =========================
# ===== CONFIG DEFAULTS ===
# =========================
DEFAULT_SOURCES = [
    r"Z:\LAWFORGE_SERVER",
    r"F:\LAWFORGE_SERVER",
    r"Z:\\",
    r"F:\\",
]

DEFAULT_DEST_M1 = r"F:\MEEK1"   # Housing / Shady Oaks
DEFAULT_DEST_M2 = r"F:\MEEK2"   # Custody / PPO

ALLOWED_EXT = [
    ".pdf", ".zip", ".docx", ".doc", ".rtf", ".txt",
    ".jpg", ".jpeg", ".png", ".tif", ".tiff",
    ".csv", ".csv.bz2", ".json", ".jsonl",
    ".xlsx", ".xls", ".eml", ".msg"
]
ALLOWED_EXT_TUPLE = tuple(ALLOWED_EXT)

EXCLUDE_DIR_NAMES = {
    "system volume information", "$recycle.bin", "recycler", "windows", "program files",
    "program files (x86)", "programdata", "appdata", "node_modules", "__pycache__",
    "_unzipped_tmp", "_unzipped", "_extracted", ".git", ".svn", ".cache",
    "miek1", "meek1", "miek2", "meek2", "auto_ingested", "organized_litigation_supreme"
}

EXCLUDE_ABS_PREFIXES: List[str] = [
    str(Path(DEFAULT_DEST_M1)).lower(),
    str(Path(DEFAULT_DEST_M2)).lower(),
]

KEYWORDS_M1 = [
    "shady oaks", "homes of america", "partridge", "alden", "rent", "ledger",
    "sewer", "sewage", "egle", "eviction", "writ", "lock", "drill", "damage",
    "mhp", "mhp llc", "zeg o", "zego",
    "shady oaks park mhp llc", "partridge equity", "alden global capital",
    "lease", "notice to quit", "summary proceedings", "mcl 600.5714"
]
KEYWORDS_M2 = [
    "ppo", "custody", "parenting time", "watson", "emily watson", "lori watson",
    "show cause", "contempt", "mcneill", "jenny l. mcneill", "bench trial (custody)",
    "best interests", "parenting schedule", "supervised exchange",
    "friend of the court", "mcr 3.207", "mcl 722.27a", "ex parte"
]

MANIFEST_CSV = "ingest_manifest.csv"
MANIFEST_JSONL = "ingest_manifest.jsonl"
LOG_NAME = "ingest_bridge.log"

COPY_CHUNK = 8 * 1024 * 1024  # 8 MiB

# =========================
# ====== UTILITIES ========
# =========================
def ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(COPY_CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def samefile_quick(src: Path, dst: Path) -> bool:
    try:
        s, d = src.stat(), dst.stat()
        return (s.st_size == d.st_size) and (int(s.st_mtime) == int(d.st_mtime))
    except Exception:
        return False

def safe_zip_extract(zip_path: Path, dest_dir: Path) -> int:
    import zipfile
    count = 0
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for member in zf.infolist():
                target = (dest_dir / member.filename).resolve()
                # ZipSlip guard
                if not str(target).lower().startswith(str(dest_dir.resolve()).lower()):
                    continue
                if member.is_dir():
                    ensure_dir(target)
                    continue
                ensure_dir(target.parent)
                with zf.open(member, 'r') as src, target.open('wb') as out:
                    shutil.copyfileobj(src, out, length=COPY_CHUNK)
                count += 1
    except Exception:
        return count
    return count

# Manifest writer with thread lock
class ManifestWriter:
    def __init__(self, csv_writer, jsonl_file):
        self._csv_writer = csv_writer
        self._jsonl = jsonl_file
        self._lock = threading.Lock()
    def write(self, row: Dict[str, str]) -> None:
        with self._lock:
            self._csv_writer.writerow(row)
            self._jsonl.write(json.dumps(row, ensure_ascii=False) + "\n")
            try:
                self._jsonl.flush()
            except Exception:
                pass

# Per-target path locks
_TARGET_LOCKS: Dict[str, threading.Lock] = {}
_TARGET_LOCKS_GUARD = threading.Lock()
def _path_lock_for(p: Path) -> threading.Lock:
    key = str(p).lower()
    with _TARGET_LOCKS_GUARD:
        lk = _TARGET_LOCKS.get(key)
        if lk is None:
            lk = threading.Lock()
            _TARGET_LOCKS[key] = lk
        return lk

def copy_stream_atomic(src: Path, dst: Path) -> None:
    tmp = dst.with_name(f"{dst.name}.tmp_{os.getpid()}_{threading.get_ident()}")
    with src.open("rb") as fsrc, tmp.open("wb") as fdst:
        shutil.copyfileobj(fsrc, fdst, length=COPY_CHUNK)
    shutil.copystat(src, tmp, follow_symlinks=True)
    os.replace(tmp, dst)  # atomic on Windows
    try:
        shutil.copystat(src, dst, follow_symlinks=True)
    except Exception:
        pass

# =========================
# ====== ROUTING ==========
# =========================
def choose_destination(path_lc: str, *, default_bucket: Optional[str] = "none") -> Tuple[Optional[str], Optional[str]]:
    for kw in KEYWORDS_M1:
        if kw in path_lc:
            return ("M1", kw)
    for kw in KEYWORDS_M2:
        if kw in path_lc:
            return ("M2", kw)
    if default_bucket in ("M1", "M2"):
        return (default_bucket, "*default*")
    return (None, None)

def allowed_file(name_lc: str) -> bool:
    return name_lc.endswith(ALLOWED_EXT_TUPLE)

# =========================
# === SCAN & PIPELINE ====
# =========================
def iter_files(root: Path, exclude_prefixes: List[str]) -> Iterator[Path]:
    try:
        stack = [root]
        while stack:
            d = stack.pop()
            try:
                for entry in os.scandir(d):
                    try:
                        if entry.is_symlink():
                            continue
                        name_lc = entry.name.lower()
                        if entry.is_dir(follow_symlinks=False):
                            if name_lc in EXCLUDE_DIR_NAMES:
                                continue
                            full_lc = str(Path(entry.path)).lower()
                            if any(full_lc.startswith(pfx) for pfx in exclude_prefixes):
                                continue
                            stack.append(entry.path)
                            continue
                        if entry.is_file(follow_symlinks=False):
                            yield Path(entry.path)
                    except PermissionError:
                        continue
            except PermissionError:
                continue
    except FileNotFoundError:
        return

def process_one(
    src_file: Path,
    dest_m1: Path,
    dest_m2: Path,
    dry_run: bool,
    strategy: str,  # 'size' or 'hash'
    prior_hashes: Dict[str, str],
    writer: ManifestWriter,
    default_bucket: str
) -> Tuple[int, int, int, int]:
    copied = skipped = extracted = errors = 0
    try:
        name_lc = src_file.name.lower()
        parent_lc = str(src_file.parent).lower()

        if not allowed_file(name_lc):
            return (0, 0, 0, 0)

        dest_key, matched_kw = choose_destination(name_lc, default_bucket=default_bucket)
        if dest_key is None:
            dest_key, matched_kw = choose_destination(parent_lc, default_bucket=default_bucket)
        if dest_key is None:
            return (0, 0, 0, 0)

        dest_root = dest_m1 if dest_key == "M1" else dest_m2
        target = (dest_root / src_file.name)

        # serialize per-target operations to avoid races
        with _path_lock_for(target):
            if target.exists():
                if strategy == "size":
                    if samefile_quick(src_file, target):
                        skipped += 1
                        writer.write({
                            "timestamp": ts(), "action": "skip_duplicate_quick",
                            "src_path": str(src_file), "dest_path": str(target),
                            "size_bytes": str(target.stat().st_size), "sha256": "", "note": "size+mtime"
                        })
                        return (0, skipped, 0, 0)
                else:
                    src_hash = sha256_file(src_file)
                    prev_hash = prior_hashes.get(str(target), "")
                    if prev_hash and prev_hash == src_hash:
                        skipped += 1
                        writer.write({
                            "timestamp": ts(), "action": "skip_duplicate_manifest",
                            "src_path": str(src_file), "dest_path": str(target),
                            "size_bytes": str(src_file.stat().st_size), "sha256": src_hash, "note": ""
                        })
                        return (0, skipped, 0, 0)
                    if target.exists():
                        dst_hash = sha256_file(target)
                        if dst_hash == src_hash:
                            skipped += 1
                            writer.write({
                                "timestamp": ts(), "action": "skip_duplicate_current",
                                "src_path": str(src_file), "dest_path": str(target),
                                "size_bytes": str(src_file.stat().st_size), "sha256": src_hash, "note": ""
                            })
                            return (0, skipped, 0, 0)
                        else:
                            short = src_hash[:8]
                            target = target.with_name(f"{target.stem}__{short}{target.suffix}")

            if dry_run:
                writer.write({
                    "timestamp": ts(), "action": "dryrun_copy",
                    "src_path": str(src_file), "dest_path": str(target),
                    "size_bytes": str(src_file.stat().st_size), "sha256": "", "note": ""
                })
                return (0, 0, 0, 0)

            ensure_dir(target.parent)
            copy_stream_atomic(src_file, target)
            copied += 1

        # outside the per-target lock

        if target.suffix.lower() == ".zip":
            unzip_dir = target.parent / f"_unzipped_{target.stem}"
            ensure_dir(unzip_dir)
            extracted += safe_zip_extract(target, unzip_dir)

        out_hash = sha256_file(target) if strategy == "hash" else ""
        writer.write({
            "timestamp": ts(), "action": "copied",
            "src_path": str(src_file), "dest_path": str(target),
            "size_bytes": str(target.stat().st_size), "sha256": out_hash,
            "note": f"kw={matched_kw}"
        })
        return (copied, skipped, extracted, 0)

    except Exception as e:
        errors += 1
        try:
            writer.write({
                "timestamp": ts(), "action": "error",
                "src_path": str(src_file), "dest_path": "",
                "size_bytes": "", "sha256": "", "note": f"{type(e).__name__}: {e}"
            })
        except Exception:
            pass
        return (0, 0, 0, errors)

def load_prior_hashes(manifest_csv: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not manifest_csv.exists():
        return out
    try:
        with manifest_csv.open("r", encoding="utf-8", newline="") as f:
            rdr = csv.DictReader(f)
            for row in rdr:
                dp = row.get("dest_path", "")
                h = row.get("sha256", "")
                if dp and h:
                    out[dp] = h
    except Exception:
        pass
    return out

def compile_excludes(exclude_prefixes: List[str], dest_m1: Path, dest_m2: Path) -> List[str]:
    out = [x.lower() for x in exclude_prefixes]
    out.append(str(dest_m1).lower())
    out.append(str(dest_m2).lower())
    return list(dict.fromkeys(out))

def main() -> int:
    ap = argparse.ArgumentParser(description="Optimized local-drive -> MEEK intake bridge (Z:/, F:/, Drive sync).")
    ap.add_argument("--sources", nargs="*", default=DEFAULT_SOURCES, help="One or more source roots (files or directories).")
    ap.add_argument("--dest-m1", default=DEFAULT_DEST_M1, help="Destination for MEEK1.")
    ap.add_argument("--dest-m2", default=DEFAULT_DEST_M2, help="Destination for MEEK2.")
    ap.add_argument("--workers", type=int, default=4, help="Thread pool workers for copy/hash.")
    ap.add_argument("--strategy", choices=["size", "hash"], default="hash", help="Duplicate strategy: size (fast) or hash (accurate).")
    ap.add_argument("--dry-run", action="store_true", help="Report only; do not copy or extract.")
    ap.add_argument("--audit", action="store_true", help="Print routing counts by bucket then exit (no copy).")
    ap.add_argument("--default-bucket", choices=["M1","M2","none"], default="none",
                    help="Route unmatched files to this bucket. 'none' keeps strict matching.")
    ap.add_argument("--min-bytes", type=int, default=1024, help="Skip files smaller than this many bytes.")
    args = ap.parse_args()

    # optional tqdm
    try:
        from tqdm import tqdm  # type: ignore
    except Exception:
        tqdm = None  # type: ignore

    sources: List[Path] = [Path(s) for s in args.sources]
    dest_m1 = Path(args.dest_m1).resolve()
    dest_m2 = Path(args.dest_m2).resolve()
    ensure_dir(dest_m1)
    ensure_dir(dest_m2)

    # Centralize manifest/logs in M1 root
    manifest_csv = (dest_m1 / MANIFEST_CSV).resolve()
    manifest_jsonl = (dest_m1 / MANIFEST_JSONL).resolve()
    log_path = (dest_m1 / LOG_NAME).resolve()

    # Exclude prefixes include dest dirs to avoid loops
    exclude_prefixes = compile_excludes(EXCLUDE_ABS_PREFIXES, dest_m1, dest_m2)

    # Open logs
    log_f = log_path.open("a", encoding="utf-8")
    def log(msg: str) -> None:
        line = f"[{ts()}] {msg}"
        print(line)
        try:
            log_f.write(line + "\n")
            log_f.flush()
        except Exception:
            pass

    # Manifest setup
    manifest_exists = manifest_csv.exists()
    csv_f = manifest_csv.open("a", newline="", encoding="utf-8")
    csv_writer = csv.DictWriter(csv_f, fieldnames=[
        "timestamp","action","src_path","dest_path","size_bytes","sha256","note"
    ])
    if not manifest_exists:
        csv_writer.writeheader()
    jsonl_f = manifest_jsonl.open("a", encoding="utf-8")
    writer = ManifestWriter(csv_writer, jsonl_f)

    prior_hashes = load_prior_hashes(manifest_csv)

    # Gather candidate files
    candidates: List[Path] = []
    for s in sources:
        if not s.exists():
            log(f"SKIP (missing source): {s}")
            continue
        if s.is_file():
            try:
                if s.stat().st_size >= args.min_bytes and allowed_file(s.name.lower()):
                    candidates.append(s)
            except Exception:
                pass
        else:
            log(f"Scanning: {s}")
            for p in iter_files(s, exclude_prefixes):
                if allowed_file(p.name.lower()):
                    try:
                        if p.stat().st_size >= args.min_bytes:
                            candidates.append(p)
                    except Exception:
                        pass

    if not candidates:
        log("No candidate files found. Exiting.")
        for f in (log_f, csv_f, jsonl_f):
            try: f.close()
            except Exception: pass
        return 0

    log(f"Candidates collected: {len(candidates):,}")

    # Audit-only mode
    if args.audit:
        counts = {"M1": 0, "M2": 0, "none": 0}
        for pth in candidates:
            nm = pth.name.lower()
            par = str(pth.parent).lower()
            dest, _ = choose_destination(nm, default_bucket=args.default_bucket)
            if dest is None:
                dest, _ = choose_destination(par, default_bucket=args.default_bucket)
            counts[dest or "none"] += 1
        log("AUDIT: route forecast (no copy): M1={:,}  M2={:,}  unmatched={:,}".format(
            counts["M1"], counts["M2"], counts["none"]))
        for f in (log_f, csv_f, jsonl_f):
            try: f.close()
            except Exception: pass
        return 0

    copied = skipped = extracted = errors = 0

    # Progress bar
    pbar = None
    if tqdm is not None:
        pbar = tqdm(total=len(candidates), unit="file", desc="Processing", smoothing=0, ascii=True)

    # Threaded processing
    with futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        future_to_path = {
            ex.submit(process_one, p, dest_m1, dest_m2, args.dry_run, args.strategy,
                      prior_hashes, writer, args.default_bucket): p
            for p in candidates
        }
        for i, future in enumerate(futures.as_completed(future_to_path), 1):
            p = future_to_path[future]
            c, s, e, err = future.result()
            copied += c; skipped += s; extracted += e; errors += err
            if pbar:
                pbar.set_postfix_str(f"copied={copied} skipped={skipped} extracted={extracted} errors={errors} last={p.name[:48]}")
                pbar.update(1)
            elif i % 200 == 0:
                log(f"Progress: {i:,}/{len(candidates):,}  copied={copied:,} skipped={skipped:,} extracted={extracted:,} errors={errors:,}")

    if pbar:
        pbar.close()

    # Summary
    log("====== SUMMARY ======")
    log(f"Processed files     : {len(candidates):,}")
    log(f"Copied              : {copied:,}")
    log(f"Skipped (duplicates): {skipped:,}")
    log(f"ZIP entries extracted: {extracted:,}")
    log(f"Errors              : {errors:,}")
    log("=====================")

    for f in (log_f, csv_f, jsonl_f):
        try: f.close()
        except Exception: pass

    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user.")
        sys.exit(130)
