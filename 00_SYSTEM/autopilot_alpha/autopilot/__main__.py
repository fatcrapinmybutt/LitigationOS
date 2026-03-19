"""
LitigationOS Autopilot (Alpha)
- local-first drive discovery
- recursive scan + manifest emission
- append-only run folders
No external deps (stdlib-only).

Design goals:
- Deterministic-ish outputs
- Fail-soft for missing permissions / weird paths
- Explicit logs + acquire plans for optional external tools
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import re
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Set, Tuple

# -------------------------
# Constants / Defaults
# -------------------------

DEFAULT_EXTS = {
    ".pdf", ".doc", ".docx", ".rtf", ".txt", ".md",
    ".png", ".jpg", ".jpeg", ".tiff", ".tif",
    ".zip", ".7z", ".rar",
    ".eml", ".msg",
    ".wav", ".mp3", ".m4a", ".mp4",
    ".html", ".htm",
    ".csv", ".json", ".jsonl",
}

HIGH_SIGNAL_DIR_MARKERS = {
    "scanned", "scan", "litigation", "litigation_os", "litigationos",
    "evidence", "exhibits", "orders", "transcripts", "pleadings",
    "motions", "briefs", "foia", "subpoena", "discovery",
    "custody", "ppo", "contempt", "jtc", "coa", "msc", "supreme",
}

DEFAULT_EXCLUDE_DIR_NAMES = {
    # Windows
    "windows", "program files", "program files (x86)", "programdata",
    "$recycle.bin", "system volume information",
    # Common caches
    ".git", ".svn", ".hg", "node_modules", "__pycache__", ".pytest_cache",
    ".cache", "cache", "temp", "tmp",
    # Browsers
    "chrome user data", "edge user data", "firefox", "brave-browser",
}

DEFAULT_MAX_FILES = 2_500_000  # safety stop
DEFAULT_MAX_BYTES_HASH = 250 * 1024 * 1024  # 250MB cap for hashing if enabled

# -------------------------
# Data Models
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
    # deterministic-ish, collision-resistant enough
    t = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    pid = os.getpid()
    rnd = hashlib.sha1(f"{t}:{pid}:{time.time_ns()}".encode("utf-8")).hexdigest()[:10]
    return f"RUN_{t}_{pid}_{rnd}"

def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")

def append_jsonl(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def is_probably_system_dir(name: str) -> bool:
    return name.strip().lower() in DEFAULT_EXCLUDE_DIR_NAMES

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

def host_facts() -> Dict[str, str]:
    return {
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "cwd": str(Path.cwd()),
    }

def windows_logical_drives() -> List[str]:
    # Windows-only, stdlib-only.
    import string
    import ctypes
    drives = []
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    for i, letter in enumerate(string.ascii_uppercase):
        if bitmask & (1 << i):
            drives.append(f"{letter}:\\")
    return drives

def default_roots_auto() -> List[str]:
    if os.name == "nt":
        return windows_logical_drives()
    # POSIX: prefer HOME plus /mnt and /media, but also allow /
    roots = []
    home = os.environ.get("HOME")
    if home:
        roots.append(home)
    for p in ("/mnt", "/media"):
        if os.path.isdir(p):
            roots.append(p)
    # Last resort
    roots.append("/")
    # De-dupe
    seen = set()
    out = []
    for r in roots:
        rr = str(Path(r).resolve())
        if rr not in seen:
            out.append(rr)
            seen.add(rr)
    return out

def detect_high_signal_dir(path: Path) -> bool:
    name = path.name.lower()
    if name in HIGH_SIGNAL_DIR_MARKERS:
        return True
    # substring markers
    for m in HIGH_SIGNAL_DIR_MARKERS:
        if m in name:
            return True
    return False

def file_kind_from_ext(ext: str) -> str:
    e = ext.lower()
    if e in (".zip", ".7z", ".rar"):
        return "archive"
    if e in (".pdf",):
        return "pdf"
    if e in (".doc", ".docx", ".rtf"):
        return "word"
    if e in (".png", ".jpg", ".jpeg", ".tif", ".tiff"):
        return "image"
    if e in (".wav", ".mp3", ".m4a"):
        return "audio"
    if e in (".mp4",):
        return "video"
    if e in (".txt", ".md", ".html", ".htm"):
        return "text"
    if e in (".csv", ".json", ".jsonl"):
        return "data"
    return "other"

def sha256_file(path: Path, max_bytes: int) -> str:
    h = hashlib.sha256()
    size = path.stat().st_size
    if size > max_bytes:
        return f"SKIPPED(size>{max_bytes})"
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

# -------------------------
# Scanner
# -------------------------

def walk_files(
    roots: List[Path],
    exts: Set[str],
    include_system: bool,
    max_files: int,
    ledger_path: Path,
) -> Iterator[Tuple[Path, Path]]:
    """
    Yield (root, file_path) for matching extensions.
    Logs events to ledger_path.
    """
    yielded = 0
    for root in roots:
        if not root.exists():
            append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "root_missing", "root": str(root)})
            continue

        append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "root_start", "root": str(root)})

        # Use os.walk for speed, but prune directories.
        for dirpath, dirnames, filenames in os.walk(root, topdown=True):
            dpath = Path(dirpath)

            # prune
            pruned = []
            kept = []
            for dn in list(dirnames):
                if (not include_system) and is_probably_system_dir(dn):
                    pruned.append(dn)
                else:
                    kept.append(dn)
            if pruned:
                append_jsonl(ledger_path, {
                    "ts": utc_now_iso(), "event": "prune_dirs",
                    "dir": str(dpath), "pruned": pruned
                })
            dirnames[:] = kept

            for fn in filenames:
                p = dpath / fn
                ext = p.suffix.lower()
                if ext and (ext in exts):
                    yielded += 1
                    yield (root, p)
                    if yielded >= max_files:
                        append_jsonl(ledger_path, {
                            "ts": utc_now_iso(), "event": "max_files_reached",
                            "max_files": max_files
                        })
                        return

        append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "root_done", "root": str(root)})

# -------------------------
# Dependency Planner (optional tools)
# -------------------------

OPTIONAL_TOOLS = {
    "7z": {
        "purpose": "Unpack SCANNED archives (.zip/.7z/.rar)",
        "windows": {"winget": "7zip.7zip"},
        "notes": "If missing, archives will be inventoried but not unpacked."
    },
    "ocrmypdf": {
        "purpose": "OCR scanned PDFs to add searchable text layer",
        "windows": {"pip": "ocrmypdf"},
        "notes": "Requires external OCR engine; install via pip and follow its docs."
    },
    "pandoc": {
        "purpose": "Compile Markdown into court-styled DOCX/PDF",
        "windows": {"winget": "JohnMacFarlane.Pandoc"},
        "notes": "Used in later pipeline stages (compile)."
    },
    "java": {
        "purpose": "Run Apache Tika (broad file text extraction)",
        "windows": {"winget": "Oracle.JavaRuntimeEnvironment"},
        "notes": "Any OpenJDK runtime is fine; winget ID varies by distro."
    },
}

def tool_on_path(exe: str) -> bool:
    from shutil import which
    return which(exe) is not None

def build_missing_deps_report() -> Dict:
    missing = {}
    for exe, meta in OPTIONAL_TOOLS.items():
        if not tool_on_path(exe):
            missing[exe] = meta
    return missing

# -------------------------
# Main command
# -------------------------

def cmd_scan(args: argparse.Namespace) -> int:
    run_id = make_run_id()
    out_root = Path(args.out_dir).expanduser().resolve()
    run_dir = out_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    ledger_path = run_dir / "RUN_LEDGER.jsonl"
    manifest_csv = run_dir / "manifest_files.csv"
    manifest_jsonl = run_dir / "manifest_files.jsonl"

    roots: List[str]
    if args.auto:
        roots = default_roots_auto()
    else:
        roots = args.roots or default_roots_auto()

    # Normalize and resolve roots
    root_paths: List[Path] = []
    for r in roots:
        try:
            rp = Path(r).expanduser().resolve()
            root_paths.append(rp)
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

    config = RunConfig(
        mode="scan",
        roots=[str(r) for r in uniq_roots],
        include_system=bool(args.include_system),
        exts=sorted(list(exts)),
        max_files=int(args.max_files),
        do_hash=bool(args.hash),
        hash_max_bytes=int(args.hash_max_bytes),
        out_dir=str(out_root),
    )

    summary = RunSummary(
        run_id=run_id,
        started_utc=utc_now_iso(),
        finished_utc=None,
        host=host_facts(),
        config=asdict(config),
        counts={"files_total": 0, "high_signal_dirs": 0, "archives": 0, "pdfs": 0, "errors": 0},
        notes=[],
    )

    write_json(run_dir / "RUN.json", asdict(summary))
    append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "run_start", "run_id": run_id})

    # Prepare CSV writer
    with manifest_csv.open("w", newline="", encoding="utf-8") as fcsv:
        writer = csv.DictWriter(fcsv, fieldnames=[
            "file_id", "root", "relpath", "abspath",
            "ext", "kind", "size_bytes", "mtime_utc",
            "sha256"
        ])
        writer.writeheader()

        # scan
        high_signal_dirs: Set[str] = set()

        for root, fp in walk_files(
            roots=uniq_roots,
            exts=exts,
            include_system=bool(args.include_system),
            max_files=int(args.max_files),
            ledger_path=ledger_path,
        ):
            try:
                st = fp.stat()
                ext = fp.suffix.lower()
                kind = file_kind_from_ext(ext)
                rel = safe_relpath(fp, root)
                file_id_seed = f"{root}|{rel}|{st.st_size}|{int(st.st_mtime)}"
                file_id = hashlib.sha1(file_id_seed.encode("utf-8")).hexdigest()

                # High-signal dir detection: check parents up to root
                cur = fp.parent
                while True:
                    if detect_high_signal_dir(cur):
                        high_signal_dirs.add(str(cur))
                    if cur == root or cur.parent == cur:
                        break
                    cur = cur.parent

                sha = ""
                if bool(args.hash):
                    sha = sha256_file(fp, int(args.hash_max_bytes))

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

                summary.counts["files_total"] += 1
                if kind == "archive":
                    summary.counts["archives"] += 1
                if kind == "pdf":
                    summary.counts["pdfs"] += 1

                if summary.counts["files_total"] % 2500 == 0:
                    append_jsonl(ledger_path, {
                        "ts": utc_now_iso(), "event": "progress",
                        "files_total": summary.counts["files_total"],
                        "archives": summary.counts["archives"],
                        "pdfs": summary.counts["pdfs"],
                    })

            except PermissionError:
                summary.counts["errors"] += 1
                append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "permission_error", "path": str(fp)})
            except FileNotFoundError:
                summary.counts["errors"] += 1
                append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "file_gone", "path": str(fp)})
            except Exception as e:
                summary.counts["errors"] += 1
                append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "error", "path": str(fp), "err": repr(e)})

        summary.counts["high_signal_dirs"] = len(high_signal_dirs)

    # Missing deps plan
    missing = build_missing_deps_report()
    write_json(run_dir / "missing_deps.json", missing)

    summary.finished_utc = utc_now_iso()
    if missing:
        summary.notes.append("Optional tool deps missing; see missing_deps.json")
    write_json(run_dir / "RUN.json", asdict(summary))
    append_jsonl(ledger_path, {"ts": utc_now_iso(), "event": "run_done", "run_id": run_id, "counts": summary.counts})

    # Human-friendly quick report
    report_lines = []
    report_lines.append(f"RUN_ID: {run_id}")
    report_lines.append(f"Started: {summary.started_utc}")
    report_lines.append(f"Finished: {summary.finished_utc}")
    report_lines.append("")
    for k, v in summary.counts.items():
        report_lines.append(f"{k}: {v}")
    report_lines.append("")
    report_lines.append("Outputs:")
    report_lines.append(f"- {run_dir / 'RUN.json'}")
    report_lines.append(f"- {run_dir / 'RUN_LEDGER.jsonl'}")
    report_lines.append(f"- {run_dir / 'manifest_files.csv'}")
    report_lines.append(f"- {run_dir / 'manifest_files.jsonl'}")
    report_lines.append(f"- {run_dir / 'missing_deps.json'}")
    (run_dir / "REPORT.txt").write_text("\n".join(report_lines), encoding="utf-8")

    print("\n".join(report_lines))
    return 0

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="autopilot", description="LitigationOS Autopilot (Alpha)")
    sub = p.add_subparsers(dest="cmd", required=True)

    ps = sub.add_parser("scan", help="Scan drives/roots recursively and emit a manifest")
    ps.add_argument("--auto", action="store_true", help="Auto-discover roots (recommended on Windows)")
    ps.add_argument("--roots", nargs="*", default=None, help="Explicit roots to scan (space-separated)")
    ps.add_argument("--include-system", action="store_true", help="Include OS/system/cache directories (slow)")
    ps.add_argument("--exts", default=",".join(sorted(DEFAULT_EXTS)), help="Comma-separated extension allowlist")
    ps.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES, help="Safety stop after N matched files")
    ps.add_argument("--hash", action="store_true", help="Compute SHA-256 for files (can be slow)")
    ps.add_argument("--hash-max-bytes", type=int, default=DEFAULT_MAX_BYTES_HASH, help="Skip hashing above N bytes")
    ps.add_argument("--out-dir", default="out", help="Output directory root for run folders")

    return p

def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cmd == "scan":
        return cmd_scan(args)
    parser.print_help()
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
