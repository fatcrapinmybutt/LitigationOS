"""
LitigationOS Autopilot — PEAK
Stdlib-first scanner + optional stages (unpack/OCR/convert/chunk) with best-effort tool routing.

No invented facts:
- Conversion/OCR stages only run if their deps are detected at runtime.
- Outputs are logged with provenance and stable-ish IDs.

This is designed to be extended into:
GraphRAG → Neo4j import → court-doc compiler.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Set, Tuple

# -------------------------
# Config load
# -------------------------

PKG_DIR = Path(__file__).resolve().parent
ROOT_DIR = PKG_DIR.parent
DEFAULT_CFG_PATH = ROOT_DIR / "config" / "default.json"

def load_cfg() -> Dict:
    try:
        return json.loads(DEFAULT_CFG_PATH.read_text(encoding="utf-8"))
    except Exception:
        # fail-soft
        return {}

CFG = load_cfg()

DEFAULT_EXTS = set(CFG.get("ext_allowlist", [])) or {
    ".pdf",".doc",".docx",".rtf",".txt",".md",".png",".jpg",".jpeg",".tif",".tiff",
    ".zip",".7z",".rar",".eml",".msg",".wav",".mp3",".m4a",".mp4",".html",".htm",".csv",".json",".jsonl"
}
EXCLUDE_DIRS = set([d.lower() for d in CFG.get("exclude_dir_names", [])]) or set()
HIGH_SIGNAL_MARKERS = set([m.lower() for m in CFG.get("high_signal_markers", [])]) or set()

PROFILES = CFG.get("profiles", {}) or {
    "fast": {"max_files": 250000, "hash": False, "hash_max_bytes": 50_000_000, "workers": 4},
    "peak": {"max_files": 2500000, "hash": False, "hash_max_bytes": 250_000_000, "workers": 16},
    "forensic": {"max_files": 2500000, "hash": True, "hash_max_bytes": 250_000_000, "workers": 8},
}

# -------------------------
# Models
# -------------------------

@dataclass(frozen=True)
class RunConfig:
    mode: str
    roots: List[str]
    include_system: bool
    exts: List[str]
    max_files: int
    do_hash: bool
    hash_max_bytes: int
    out_dir: str
    profile: str
    stages: List[str]
    workers: int

@dataclass
class RunSummary:
    run_id: str
    started_utc: str
    finished_utc: Optional[str]
    host: Dict[str, str]
    config: Dict
    counts: Dict[str, int]
    notes: List[str]

# -------------------------
# Utilities
# -------------------------

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def safe_relpath(p: Path, root: Path) -> str:
    try:
        return str(p.relative_to(root))
    except Exception:
        return str(p)

def make_run_id() -> str:
    t = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    pid = os.getpid()
    rnd = hashlib.sha1(f"{t}:{pid}:{time.time_ns()}".encode("utf-8")).hexdigest()[:10]
    return f"RUN_{t}_{pid}_{rnd}"

def host_facts() -> Dict[str, str]:
    return {
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "cwd": str(Path.cwd()),
    }

def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")

def append_jsonl(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def normalize_exts(exts: Iterable[str]) -> Set[str]:
    out = set()
    for e in exts:
        e = e.strip().lower()
        if not e:
            continue
        if not e.startswith("."):
            e = "." + e
        out.add(e)
    return out

def is_probably_system_dir(name: str) -> bool:
    return name.strip().lower() in EXCLUDE_DIRS

def detect_high_signal_dir(path: Path) -> bool:
    name = path.name.lower()
    if name in HIGH_SIGNAL_MARKERS:
        return True
    for m in HIGH_SIGNAL_MARKERS:
        if m and (m in name):
            return True
    return False

def file_kind_from_ext(ext: str) -> str:
    e = ext.lower()
    if e in (".zip", ".7z", ".rar"):
        return "archive"
    if e == ".pdf":
        return "pdf"
    if e in (".doc", ".docx", ".rtf"):
        return "word"
    if e in (".png", ".jpg", ".jpeg", ".tif", ".tiff"):
        return "image"
    if e in (".wav", ".mp3", ".m4a"):
        return "audio"
    if e == ".mp4":
        return "video"
    if e in (".txt", ".md", ".html", ".htm"):
        return "text"
    if e in (".csv", ".json", ".jsonl"):
        return "data"
    return "other"

def tool_on_path(exe: str) -> bool:
    return shutil.which(exe) is not None

def sha256_file(path: Path, max_bytes: int) -> str:
    size = path.stat().st_size
    if size > max_bytes:
        return f"SKIPPED(size>{max_bytes})"
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

# Windows drive discovery (stdlib)
def windows_logical_drives() -> List[str]:
    import ctypes
    import string
    drives = []
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    for i, letter in enumerate(string.ascii_uppercase):
        if bitmask & (1 << i):
            drives.append(f"{letter}:\\")
    return drives

def default_roots_auto() -> List[str]:
    if os.name == "nt":
        return windows_logical_drives()
    roots = []
    home = os.environ.get("HOME")
    if home:
        roots.append(home)
    for p in ("/mnt", "/media"):
        if os.path.isdir(p):
            roots.append(p)
    roots.append("/")
    # de-dupe
    seen = set()
    out = []
    for r in roots:
        try:
            rr = str(Path(r).resolve())
        except Exception:
            rr = str(r)
        if rr not in seen:
            out.append(rr)
            seen.add(rr)
    return out

# -------------------------
# Acquire plan (optional tools)
# -------------------------

OPTIONAL_TOOLS = {
    "7z": {
        "purpose": "Unpack SCANNED archives (.zip/.7z/.rar)",
        "windows": {"winget": "7zip.7zip"},
        "notes": "ZIP is supported via python; 7z/rar require 7z."
    },
    "ocrmypdf": {
        "purpose": "OCR scanned PDFs (adds searchable text layer)",
        "windows": {"pip": "ocrmypdf"},
        "notes": "Runs only if present; recommend installing for scan-heavy evidence."
    },
    "pandoc": {
        "purpose": "Compile Markdown into DOCX/PDF (later stage)",
        "windows": {"winget": "JohnMacFarlane.Pandoc"},
        "notes": "Not required for inventory/extraction."
    },
    "java": {
        "purpose": "Run Apache Tika (broad file text extraction; optional)",
        "windows": {"winget": "EclipseAdoptium.Temurin.21.JRE"},
        "notes": "Any OpenJDK runtime works."
    },
}

def build_missing_deps_report() -> Dict:
    missing = {}
    for exe, meta in OPTIONAL_TOOLS.items():
        if not tool_on_path(exe):
            missing[exe] = meta
    # python deps for convert/chunk
    py_missing = {}
    try:
        import pypdf  # noqa
    except Exception:
        py_missing["pypdf"] = "pip install -r requirements_peak.txt"
    try:
        import docx  # noqa
    except Exception:
        py_missing["python-docx"] = "pip install -r requirements_peak.txt"
    if py_missing:
        missing["_python"] = py_missing
    return missing

# -------------------------
# Scanner (os.scandir recursion for speed)
# -------------------------

def iter_files_scandir(
    root: Path,
    include_system: bool,
    exts: Set[str],
    ledger_path: Path,
) -> Iterator[Path]:
    stack = [root]
    while stack:
        d = stack.pop()
        try:
            with os.scandir(d) as it:
                for entry in it:
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            dn = entry.name
                            if (not include_system) and is_probably_system_dir(dn):
                                append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "prune_dir", "dir": str(entry.path)})
                                continue
                            stack.append(Path(entry.path))
                        elif entry.is_file(follow_symlinks=False):
                            p = Path(entry.path)
                            ext = p.suffix.lower()
                            if ext in exts:
                                yield p
                    except PermissionError:
                        append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "permission_error", "path": str(entry.path)})
                    except FileNotFoundError:
                        append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "file_gone", "path": str(entry.path)})
                    except OSError as e:
                        append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "os_error", "path": str(entry.path), "err": repr(e)})
        except PermissionError:
            append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "permission_error", "path": str(d)})
        except FileNotFoundError:
            append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "dir_gone", "path": str(d)})
        except OSError as e:
            append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "os_error", "path": str(d), "err": repr(e)})

# -------------------------
# Stages
# -------------------------

def stage_inventory(
    run_dir: Path,
    roots: List[Path],
    include_system: bool,
    exts: Set[str],
    max_files: int,
    do_hash: bool,
    hash_max_bytes: int,
    ledger_path: Path,
) -> Tuple[Dict, Set[str]]:
    manifest_csv = run_dir / "manifest_files.csv"
    manifest_jsonl = run_dir / "manifest_files.jsonl"

    counts = {"files_total": 0, "archives": 0, "pdfs": 0, "errors": 0, "high_signal_dirs": 0}
    high_signal_dirs: Set[str] = set()

    with manifest_csv.open("w", newline="", encoding="utf-8") as fcsv:
        writer = csv.DictWriter(fcsv, fieldnames=[
            "file_id","root","relpath","abspath","ext","kind","size_bytes","mtime_utc","sha256"
        ])
        writer.writeheader()

        for root in roots:
            append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "root_start", "root": str(root)})
            if not root.exists():
                append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "root_missing", "root": str(root)})
                continue

            for fp in iter_files_scandir(root, include_system, exts, ledger_path):
                try:
                    st = fp.stat()
                    ext = fp.suffix.lower()
                    kind = file_kind_from_ext(ext)
                    rel = safe_relpath(fp, root)
                    file_id_seed = f"{root}|{rel}|{st.st_size}|{int(st.st_mtime)}"
                    file_id = hashlib.sha1(file_id_seed.encode("utf-8")).hexdigest()

                    # High signal dir detection up the tree
                    cur = fp.parent
                    while True:
                        if detect_high_signal_dir(cur):
                            high_signal_dirs.add(str(cur))
                        if cur == root or cur.parent == cur:
                            break
                        cur = cur.parent

                    sha = ""
                    if do_hash:
                        sha = sha256_file(fp, hash_max_bytes)

                    row = {
                        "file_id": file_id,
                        "root": str(root),
                        "relpath": rel,
                        "abspath": str(fp),
                        "ext": ext,
                        "kind": kind,
                        "size_bytes": st.st_size,
                        "mtime_utc": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).replace(microsecond=0).isoformat(),
                        "sha256": sha,
                    }
                    writer.writerow(row)
                    append_jsonl(manifest_jsonl, row)

                    counts["files_total"] += 1
                    if kind == "archive":
                        counts["archives"] += 1
                    if kind == "pdf":
                        counts["pdfs"] += 1

                    if counts["files_total"] % 5000 == 0:
                        append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "progress", **counts})

                    if counts["files_total"] >= max_files:
                        append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "max_files_reached", "max_files": max_files})
                        break

                except PermissionError:
                    counts["errors"] += 1
                    append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "permission_error", "path": str(fp)})
                except FileNotFoundError:
                    counts["errors"] += 1
                    append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "file_gone", "path": str(fp)})
                except Exception as e:
                    counts["errors"] += 1
                    append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "error", "path": str(fp), "err": repr(e)})

            append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "root_done", "root": str(root)})

    counts["high_signal_dirs"] = len(high_signal_dirs)
    return counts, high_signal_dirs

def _iter_manifest_jsonl(path: Path) -> Iterator[Dict]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue

def _output_id(seed: str) -> str:
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()

def stage_unpack(run_dir: Path, ledger_path: Path) -> int:
    """
    Unpack .zip via stdlib; .7z/.rar via 7z if available.
    Only unpack "high-signal" archives: path contains 'scanned' or parent dir is high-signal.
    """
    manifest = run_dir / "manifest_files.jsonl"
    out_manifest = run_dir / "manifest_outputs.jsonl"
    unpack_dir = run_dir / "unpacked"
    unpack_dir.mkdir(parents=True, exist_ok=True)

    has_7z = tool_on_path("7z")
    produced = 0

    for rec in _iter_manifest_jsonl(manifest):
        if rec.get("kind") != "archive":
            continue
        abspath = Path(rec["abspath"])
        path_lc = str(abspath).lower()
        # heuristic: only unpack scanned/high-signal
        if ("scanned" not in path_lc) and ("scan" not in path_lc) and ("litigation" not in path_lc):
            continue

        file_id = rec["file_id"]
        ext = rec.get("ext","").lower()
        target = unpack_dir / file_id
        target.mkdir(parents=True, exist_ok=True)

        try:
            if ext == ".zip":
                import zipfile
                with zipfile.ZipFile(abspath, "r") as z:
                    z.extractall(target)
                meta = {"archive": str(abspath), "method": "zipfile"}
            elif ext in (".7z", ".rar"):
                if not has_7z:
                    append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "unpack_skip_no_7z", "path": str(abspath)})
                    continue
                # 7z x -y -o<out> <archive>
                cmd = ["7z", "x", "-y", f"-o{str(target)}", str(abspath)]
                rc = subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if rc != 0:
                    append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "unpack_failed", "path": str(abspath), "rc": rc})
                    continue
                meta = {"archive": str(abspath), "method": "7z"}
            else:
                continue

            produced += 1
            out_rec = {
                "output_id": _output_id(f"unpack|{file_id}|{str(target)}"),
                "source_file_id": file_id,
                "stage": "unpack",
                "abspath": str(target),
                "kind": "dir",
                "meta": meta,
                "size_bytes": 0,
                "mtime_utc": utc_now_iso(),
            }
            append_jsonl(out_manifest, out_rec)
            append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "unpack_ok", "path": str(abspath), "out": str(target)})

        except Exception as e:
            append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "unpack_error", "path": str(abspath), "err": repr(e)})

    return produced

def stage_ocr(run_dir: Path, ledger_path: Path) -> int:
    """
    OCR PDFs using ocrmypdf if available.
    Runs: ocrmypdf --skip-text --force-ocr <in> <out>
    (best-effort; does not overwrite originals)
    """
    if not tool_on_path("ocrmypdf"):
        append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "ocr_skip_no_ocrmypdf"})
        return 0

    manifest = run_dir / "manifest_files.jsonl"
    out_manifest = run_dir / "manifest_outputs.jsonl"
    ocr_dir = run_dir / "ocr"
    ocr_dir.mkdir(parents=True, exist_ok=True)

    produced = 0
    for rec in _iter_manifest_jsonl(manifest):
        if rec.get("kind") != "pdf":
            continue
        abspath = Path(rec["abspath"])
        path_lc = str(abspath).lower()
        # prioritize scanned-like
        if ("scanned" not in path_lc) and ("scan" not in path_lc):
            continue

        file_id = rec["file_id"]
        out_pdf = ocr_dir / f"{file_id}.pdf"
        if out_pdf.exists():
            continue

        cmd = ["ocrmypdf", "--skip-text", "--force-ocr", "--quiet", str(abspath), str(out_pdf)]
        rc = subprocess.call(cmd)
        if rc != 0:
            append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "ocr_failed", "path": str(abspath), "rc": rc})
            continue

        produced += 1
        try:
            st = out_pdf.stat()
            out_rec = {
                "output_id": _output_id(f"ocr|{file_id}|{str(out_pdf)}|{st.st_size}|{int(st.st_mtime)}"),
                "source_file_id": file_id,
                "stage": "ocr",
                "abspath": str(out_pdf),
                "kind": "pdf",
                "meta": {"method": "ocrmypdf", "src": str(abspath)},
                "size_bytes": st.st_size,
                "mtime_utc": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).replace(microsecond=0).isoformat(),
            }
            append_jsonl(out_manifest, out_rec)
            append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "ocr_ok", "path": str(abspath), "out": str(out_pdf)})
        except Exception as e:
            append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "ocr_ok_meta_error", "path": str(out_pdf), "err": repr(e)})

    return produced

def _extract_pdf_to_md(pdf_path: Path) -> Tuple[str, Dict]:
    """
    Extracts text from PDF with pypdf if available.
    Returns (md_text, meta).
    """
    try:
        from pypdf import PdfReader
    except Exception as e:
        raise RuntimeError("pypdf_not_installed") from e

    reader = PdfReader(str(pdf_path))
    pages = []
    for i, page in enumerate(reader.pages):
        try:
            txt = page.extract_text() or ""
        except Exception:
            txt = ""
        pages.append((i+1, txt))
    # simple md: headings per page
    md_parts = []
    for pno, txt in pages:
        md_parts.append(f"## Page {pno}\n")
        md_parts.append(txt.strip() + "\n")
    meta = {"pages": len(pages)}
    return "\n".join(md_parts), meta

def _extract_docx_to_md(docx_path: Path) -> Tuple[str, Dict]:
    try:
        import docx
    except Exception as e:
        raise RuntimeError("python_docx_not_installed") from e

    d = docx.Document(str(docx_path))
    lines = []
    for p in d.paragraphs:
        t = (p.text or "").rstrip()
        if t:
            lines.append(t)
    meta = {"paragraphs": len(lines)}
    return "\n\n".join(lines) + "\n", meta

def stage_convert(run_dir: Path, ledger_path: Path) -> int:
    """
    Convert source files to Markdown (best-effort).
    Priority sources:
      - OCRed PDFs (run_dir/ocr) if present
      - Original PDFs/DOCX/TXT/MD
    Outputs:
      run_dir/md/<source_file_id>.md
    """
    manifest = run_dir / "manifest_files.jsonl"
    out_manifest = run_dir / "manifest_outputs.jsonl"
    md_dir = run_dir / "md"
    md_dir.mkdir(parents=True, exist_ok=True)

    # map OCR outputs: source_file_id -> ocr_pdf_path
    ocr_map: Dict[str, Path] = {}
    for rec in _iter_manifest_jsonl(out_manifest):
        if rec.get("stage") == "ocr" and rec.get("kind") == "pdf":
            ocr_map[rec["source_file_id"]] = Path(rec["abspath"])

    produced = 0
    for rec in _iter_manifest_jsonl(manifest):
        kind = rec.get("kind")
        if kind not in ("pdf", "word", "text"):
            continue

        file_id = rec["file_id"]
        out_md = md_dir / f"{file_id}.md"
        if out_md.exists():
            continue

        src_path = Path(rec["abspath"])
        use_path = ocr_map.get(file_id, src_path) if kind == "pdf" else src_path

        try:
            if kind == "pdf":
                md_text, meta = _extract_pdf_to_md(use_path)
            elif kind == "word":
                ext = rec.get("ext","").lower()
                if ext == ".docx":
                    md_text, meta = _extract_docx_to_md(use_path)
                else:
                    # .doc/.rtf are not handled without external tools; skip with ledger note
                    append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "convert_skip_word_unsupported", "path": str(use_path), "ext": ext})
                    continue
            elif kind == "text":
                try:
                    md_text = use_path.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    md_text = use_path.read_text(errors="replace")
                meta = {"method": "raw_text"}
            else:
                continue

            out_md.write_text(md_text, encoding="utf-8")
            st = out_md.stat()
            produced += 1

            out_rec = {
                "output_id": _output_id(f"convert|{file_id}|{str(out_md)}|{st.st_size}|{int(st.st_mtime)}"),
                "source_file_id": file_id,
                "stage": "convert",
                "abspath": str(out_md),
                "kind": "md",
                "meta": {"src": str(use_path), **meta},
                "size_bytes": st.st_size,
                "mtime_utc": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).replace(microsecond=0).isoformat(),
            }
            append_jsonl(out_manifest, out_rec)
            append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "convert_ok", "src": str(use_path), "out": str(out_md)})

        except RuntimeError as e:
            append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "convert_missing_pydep", "path": str(use_path), "err": str(e)})
        except Exception as e:
            append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "convert_error", "path": str(use_path), "err": repr(e)})

    return produced

def stage_chunk(run_dir: Path, ledger_path: Path) -> int:
    """
    Chunk MD outputs line-by-line into shard JSONL for retrieval/citation.
    Outputs:
      run_dir/shards/shards.jsonl
      run_dir/shards/<source_file_id>.lines.txt (line-numbered view)
    """
    out_manifest = run_dir / "manifest_outputs.jsonl"
    shards_dir = run_dir / "shards"
    shards_dir.mkdir(parents=True, exist_ok=True)
    shards_path = shards_dir / "shards.jsonl"

    produced = 0
    for rec in _iter_manifest_jsonl(out_manifest):
        if rec.get("stage") != "convert" or rec.get("kind") != "md":
            continue
        src_file_id = rec["source_file_id"]
        md_path = Path(rec["abspath"])
        try:
            text = md_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            text = md_path.read_text(errors="replace")

        lines = text.splitlines()
        # write a line-numbered view for human auditing
        lines_txt = shards_dir / f"{src_file_id}.lines.txt"
        with lines_txt.open("w", encoding="utf-8") as f:
            for i, ln in enumerate(lines, start=1):
                f.write(f"{i:06d}  {ln}\n")

        # emit shards: 1 line per shard (simple; later can merge)
        for i, ln in enumerate(lines, start=1):
            ln = ln.rstrip()
            if not ln:
                continue
            shard_id = _output_id(f"shard|{src_file_id}|L{i}|{ln[:80]}")
            shard = {
                "shard_id": shard_id,
                "source_file_id": src_file_id,
                "kind": "line",
                "line_no": i,
                "text": ln,
                "provenance": {"md": str(md_path), "method": "line_split"},
            }
            append_jsonl(shards_path, shard)

        produced += 1
        append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "chunk_ok", "md": str(md_path), "lines": len(lines)})

    return produced

# -------------------------
# Orchestrator
# -------------------------

def cmd_doctor(args: argparse.Namespace) -> int:
    missing = build_missing_deps_report()
    print(json.dumps(missing, indent=2))
    return 0

def cmd_scan(args: argparse.Namespace) -> int:
    # inventory-only wrapper
    return cmd_run(argparse.Namespace(
        auto=args.auto,
        roots=args.roots,
        include_system=args.include_system,
        exts=args.exts,
        out_dir=args.out_dir,
        profile=args.profile,
        stages="inventory",
        hash=args.hash,
        hash_max_bytes=args.hash_max_bytes,
        max_files=args.max_files,
        workers=args.workers,
    ))

def cmd_run(args: argparse.Namespace) -> int:
    run_id = make_run_id()
    out_root = Path(args.out_dir).expanduser().resolve()
    run_dir = out_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = run_dir / "RUN_LEDGER.jsonl"

    # roots
    if args.auto:
        roots = default_roots_auto()
    else:
        roots = args.roots or default_roots_auto()
    root_paths: List[Path] = []
    for r in roots:
        try:
            root_paths.append(Path(r).expanduser().resolve())
        except Exception:
            append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "root_bad", "root": r})
    # de-dupe
    seen = set()
    uniq_roots = []
    for rp in root_paths:
        s = str(rp)
        if s not in seen:
            uniq_roots.append(rp)
            seen.add(s)

    exts = normalize_exts(args.exts.split(",") if args.exts else DEFAULT_EXTS)

    # profile merges
    prof = PROFILES.get(args.profile, PROFILES.get("peak", {}))
    max_files = int(args.max_files if args.max_files is not None else prof.get("max_files", 2500000))
    do_hash = bool(args.hash if args.hash is not None else prof.get("hash", False))
    hash_max = int(args.hash_max_bytes if args.hash_max_bytes is not None else prof.get("hash_max_bytes", 250_000_000))
    workers = int(args.workers if args.workers is not None else prof.get("workers", 8))

    stages = [s.strip().lower() for s in (args.stages.split(",") if args.stages else ["inventory"]) if s.strip()]
    # normalize stage order
    stage_order = ["inventory", "unpack", "ocr", "convert", "chunk"]
    stages = [s for s in stage_order if s in stages]  # keep known order

    config = RunConfig(
        mode="run",
        roots=[str(r) for r in uniq_roots],
        include_system=bool(args.include_system),
        exts=sorted(list(exts)),
        max_files=max_files,
        do_hash=do_hash,
        hash_max_bytes=hash_max,
        out_dir=str(out_root),
        profile=str(args.profile),
        stages=stages,
        workers=workers,
    )

    summary = RunSummary(
        run_id=run_id,
        started_utc=utc_now_iso(),
        finished_utc=None,
        host=host_facts(),
        config=asdict(config),
        counts={"files_total": 0, "archives": 0, "pdfs": 0, "errors": 0,
                "high_signal_dirs": 0, "unpacked": 0, "ocred": 0, "converted": 0, "chunked": 0},
        notes=[],
    )

    write_json(run_dir / "RUN.json", asdict(summary))
    append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "run_start", "run_id": run_id, "stages": stages})

    # Always write missing deps plan
    missing = build_missing_deps_report()
    write_json(run_dir / "missing_deps.json", missing)
    if missing:
        summary.notes.append("Missing optional deps; see missing_deps.json")

    high_signal_dirs: Set[str] = set()
    if "inventory" in stages:
        counts, high_signal_dirs = stage_inventory(
            run_dir=run_dir,
            roots=uniq_roots,
            include_system=bool(args.include_system),
            exts=exts,
            max_files=max_files,
            do_hash=do_hash,
            hash_max_bytes=hash_max,
            ledger_path=ledger_path,
        )
        for k in ("files_total","archives","pdfs","errors","high_signal_dirs"):
            summary.counts[k] = counts.get(k, summary.counts.get(k, 0))

    if "unpack" in stages:
        summary.counts["unpacked"] = stage_unpack(run_dir, ledger_path)

    if "ocr" in stages:
        summary.counts["ocred"] = stage_ocr(run_dir, ledger_path)

    if "convert" in stages:
        summary.counts["converted"] = stage_convert(run_dir, ledger_path)

    if "chunk" in stages:
        summary.counts["chunked"] = stage_chunk(run_dir, ledger_path)

    summary.finished_utc = utc_now_iso()
    write_json(run_dir / "RUN.json", asdict(summary))
    append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "run_done", "run_id": run_id, "counts": summary.counts})

    # REPORT
    report = []
    report.append(f"RUN_ID: {run_id}")
    report.append(f"Started: {summary.started_utc}")
    report.append(f"Finished: {summary.finished_utc}")
    report.append("")
    report.append("Counts:")
    for k, v in summary.counts.items():
        report.append(f"- {k}: {v}")
    report.append("")
    report.append("Outputs:")
    for name in ["RUN.json","RUN_LEDGER.jsonl","manifest_files.csv","manifest_files.jsonl","manifest_outputs.jsonl","missing_deps.json","REPORT.txt"]:
        p = run_dir / name
        if p.exists():
            report.append(f"- {p}")
    (run_dir / "REPORT.txt").write_text("\n".join(report), encoding="utf-8")

    print("\n".join(report))
    return 0

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="autopilot", description="LitigationOS Autopilot — PEAK")
    sub = p.add_subparsers(dest="cmd", required=True)

    # doctor
    pd = sub.add_parser("doctor", help="Print missing deps and acquire-plan")
    pd.set_defaults(func=cmd_doctor)

    # scan (inventory only)
    ps = sub.add_parser("scan", help="Inventory-only scan (fast)")
    ps.add_argument("--auto", action="store_true", help="Auto-discover roots (recommended on Windows)")
    ps.add_argument("--roots", nargs="*", default=None, help="Explicit roots to scan (space-separated)")
    ps.add_argument("--include-system", action="store_true", help="Include OS/system/cache directories (slow)")
    ps.add_argument("--exts", default=",".join(sorted(DEFAULT_EXTS)), help="Comma-separated extension allowlist")
    ps.add_argument("--max-files", type=int, default=None, help="Safety stop after N matched files")
    ps.add_argument("--hash", action="store_true", help="Compute SHA-256 for files (slow)")
    ps.add_argument("--hash-max-bytes", type=int, default=None, help="Skip hashing above N bytes")
    ps.add_argument("--out-dir", default="out", help="Output directory root for run folders")
    ps.add_argument("--profile", default="peak", choices=sorted(PROFILES.keys()), help="Tuning profile")
    ps.add_argument("--workers", type=int, default=None, help="Worker hint (reserved)")
    ps.set_defaults(func=cmd_scan)

    # run (pipeline)
    pr = sub.add_parser("run", help="Run pipeline stages (best-effort)")
    pr.add_argument("--auto", action="store_true", help="Auto-discover roots (recommended on Windows)")
    pr.add_argument("--roots", nargs="*", default=None, help="Explicit roots to scan (space-separated)")
    pr.add_argument("--include-system", action="store_true", help="Include OS/system/cache directories (slow)")
    pr.add_argument("--exts", default=",".join(sorted(DEFAULT_EXTS)), help="Comma-separated extension allowlist")
    pr.add_argument("--max-files", type=int, default=None, help="Safety stop after N matched files")
    pr.add_argument("--hash", type=lambda x: x.lower() in ("1","true","yes","y"), default=None, help="Override hash on/off (true/false)")
    pr.add_argument("--hash-max-bytes", type=int, default=None, help="Skip hashing above N bytes")
    pr.add_argument("--out-dir", default="out", help="Output directory root for run folders")
    pr.add_argument("--profile", default="peak", choices=sorted(PROFILES.keys()), help="Tuning profile")
    pr.add_argument("--stages", default="inventory,unpack,ocr,convert,chunk", help="Comma-separated stages")
    pr.add_argument("--workers", type=int, default=None, help="Worker hint (reserved)")
    pr.set_defaults(func=cmd_run)

    return p

def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))

if __name__ == "__main__":
    raise SystemExit(main())
