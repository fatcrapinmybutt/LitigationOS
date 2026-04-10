"""
APEX File Organizer v3.0 — CANON-Aware Multi-Phase Organization for LitigationOS
==================================================================================

Capabilities:
  - Phase 1: Root cleanup (C:\\Users\\andre\\LitigationOS root violations → canonical folders)
  - Phase 2: Intra-repo SHA-256 deduplication across all 13 canonical folders
  - Phase 3: Other drives scan (D:\\, F:\\, G:\\, J:\\) — flag LitigationOS-relevant content
  - Plan-first (default) — prints a full report of what WOULD be moved
  - Apply mode (--apply) — executes all planned moves with ledger tracking
  - NO deletions EVER — everything moves to canonical folder OR I:\\LITIGOS_ARCHIVE\\

Usage:
    python -I D:\\LitigationOS_tmp\\apex_organizer_v3.py --scan
    python -I D:\\LitigationOS_tmp\\apex_organizer_v3.py --scan --apply
    python -I D:\\LitigationOS_tmp\\apex_organizer_v3.py --phase 1          # root only
    python -I D:\\LitigationOS_tmp\\apex_organizer_v3.py --phase 2          # dedup only
    python -I D:\\LitigationOS_tmp\\apex_organizer_v3.py --phase 3          # other drives
    python -I D:\\LitigationOS_tmp\\apex_organizer_v3.py --scan --apply --phase 1

Author: LitigationOS SINGULARITY APEX v3.0 — 2026
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import shutil
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

__version__ = "3.0.0"

LITIGOS_ROOT = Path(r"C:\Users\andre\LitigationOS")
ARCHIVE_STAGING = Path(r"I:\LITIGOS_ARCHIVE")
DEDUP_STAGING = Path(r"I:\LITIGOS_DEDUP")
LEDGER_PATH = Path(r"D:\LitigationOS_tmp\organizer_ledger.db")

# Large builds/dist go to J:\ (zipped) — too many small files for I:\
ARCHIVE_USB = Path(r"J:\LitigationOS_CENTRAL\ARCHIVE")

# ─────────────────────────────────────────────────────────────────────────────
# CANON-protected files that must NEVER be auto-moved
# ─────────────────────────────────────────────────────────────────────────────

# Files that must stay at root per _CANON.md + DB_REGISTRY requirements
PROTECTED_AT_ROOT: frozenset[str] = frozenset({
    "_CANON.md", "README.md", "pyproject.toml", "requirements.txt",
    "mcp.json", ".gitignore", "litigationos.config.jsonc", "master.code-workspace",
    "AGENTS.md", "justfile",
    # litigation_context.db stays at root — DB_REGISTRY["litigation"] = "litigation_context.db"
    "litigation_context.db", "litigation_context.db-shm", "litigation_context.db-wal",
    # mbp_brain.db — THEMANBEARPIG hardcoded path
    "mbp_brain.db", "mbp_brain.db-shm", "mbp_brain.db-wal",
})

# Root-level config/hidden files — keep as-is (dotfiles)
TOLERATED_DOTFILES: frozenset[str] = frozenset({
    ".gitattributes", ".editorconfig", ".shellcheckrc", ".codex_config.yaml",
    ".node_repl_history", ".lesshst",
})

# Protected directories — never touch internals
PROTECTED_DIRS: frozenset[str] = frozenset({
    "00_SYSTEM", "01_EVIDENCE", "02_AUTHORITY", "03_COURT", "04_ANALYSIS",
    "05_FILINGS", "06_DATA", "07_CODE", "08_MEDIA", "09_REFERENCE",
    "10_EXTERNAL", "11_ARCHIVES", "12_WORKSPACE",
    ".git", ".github", ".agents", ".claude", ".venv", ".vscode", ".eide",
    ".learnings", ".superpower-copilot", ".pytest_cache",
    "pytools_venv",  # Virtual env — keep at root (gitignored, needed by tools)
})

# ─────────────────────────────────────────────────────────────────────────────
# Root Violation → Canonical Target Mapping
# ─────────────────────────────────────────────────────────────────────────────

# Maps root-level items to their canonical destination within LitigationOS
ROOT_MOVE_MAP: dict[str, Path] = {
    # Directories
    "build":             LITIGOS_ROOT / "11_ARCHIVES" / "BUILD_ARTIFACTS",
    "dist":              LITIGOS_ROOT / "11_ARCHIVES" / "DIST_ARTIFACTS",
    "docs":              LITIGOS_ROOT / "09_REFERENCE",
    "logs":              LITIGOS_ROOT / "12_WORKSPACE" / "LOGS",
    "scripts":           LITIGOS_ROOT / "00_SYSTEM" / "tools" / "scripts",
    "cortex-osint-test": LITIGOS_ROOT / "10_EXTERNAL" / "cortex-osint-test",
    "D_tmp":             LITIGOS_ROOT / "12_WORKSPACE" / "TEMP" / "D_tmp",
    "-p":                LITIGOS_ROOT / "12_WORKSPACE" / "TEMP" / "_p_stray",

    # Small databases (not critical, not in DB_REGISTRY as root-relative)
    "claim_evidence_links.db":     LITIGOS_ROOT / "06_DATA",
    "claim_evidence_links.db-shm": LITIGOS_ROOT / "06_DATA",
    "claim_evidence_links.db-wal": LITIGOS_ROOT / "06_DATA",
    "db.sqlite":                   LITIGOS_ROOT / "06_DATA",
    "lit_ctx_snapshot.db":         LITIGOS_ROOT / "06_DATA",

    # Data files
    "visualization_data.json":         LITIGOS_ROOT / "06_DATA",
    "WizTree_FT_20260403104219.csv":    LITIGOS_ROOT / "06_DATA",

    # Build spec
    "THEMANBEARPIG.spec": LITIGOS_ROOT / "07_CODE" / "BUILD",

    # Reports
    "AUTHORITY_SEARCH_REPORT.txt":     LITIGOS_ROOT / "04_ANALYSIS" / "REPORTS",
    "IMPORT_AUDIT_REPORT.txt":         LITIGOS_ROOT / "04_ANALYSIS" / "REPORTS",
    "YELLOW_DOMAINS_AUDIT_REPORT.txt": LITIGOS_ROOT / "04_ANALYSIS" / "REPORTS",
    "import_audit.txt":                LITIGOS_ROOT / "04_ANALYSIS" / "REPORTS",
    "import_test_output.txt":          LITIGOS_ROOT / "12_WORKSPACE" / "TEMP",
    "module_analysis.txt":             LITIGOS_ROOT / "04_ANALYSIS" / "REPORTS",
    "query_results.txt":               LITIGOS_ROOT / "12_WORKSPACE" / "TEMP",
}

# Pattern-based moves for loose root files (applied if not in ROOT_MOVE_MAP)
ROOT_PATTERN_MOVES: list[tuple[re.Pattern, Path]] = [
    # copilot session files
    (re.compile(r"^copilot-session-.*\.md$"), LITIGOS_ROOT / "12_WORKSPACE" / "SESSIONS"),
    # Analysis/query scripts
    (re.compile(r"^(analyze_|check_|query_|explore_|search_|sample_|verify_|final_|weak_|detailed_|merge_|comprehensive_|build_|rule_|evidence_|archive_|list_|export_|syntax_|test_|filing_).*\.py$"),
     LITIGOS_ROOT / "12_WORKSPACE" / "TEMP"),
]

# ─────────────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s", stream=sys.stderr)
log = logging.getLogger("apex_organizer_v3")

# ─────────────────────────────────────────────────────────────────────────────
# Ledger (SQLite — persistent move log)
# ─────────────────────────────────────────────────────────────────────────────

def get_ledger(path: Path = LEDGER_PATH) -> sqlite3.Connection:
    """Return an open ledger connection with WAL mode."""
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS moves (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            phase     INTEGER NOT NULL,
            src       TEXT NOT NULL,
            dst       TEXT NOT NULL,
            size_mb   REAL,
            sha256    TEXT,
            action    TEXT NOT NULL,  -- 'plan' | 'move' | 'dedup_move' | 'skip' | 'error'
            reason    TEXT,
            ts        TEXT DEFAULT (datetime('now')),
            run_id    TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            run_id    TEXT PRIMARY KEY,
            started   TEXT,
            finished  TEXT,
            phase     TEXT,
            applied   INTEGER,
            total     INTEGER,
            errors    INTEGER
        )
    """)
    conn.commit()
    return conn


def log_move(conn: sqlite3.Connection, run_id: str, phase: int, src: Path,
             dst: Path, action: str, size_mb: float = 0.0,
             sha256: str = "", reason: str = "") -> None:
    conn.execute(
        "INSERT INTO moves(phase,src,dst,size_mb,sha256,action,reason,run_id) VALUES(?,?,?,?,?,?,?,?)",
        (phase, str(src), str(dst), size_mb, sha256, action, reason, run_id)
    )
    conn.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Utility
# ─────────────────────────────────────────────────────────────────────────────

def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    """Compute SHA-256 of a file using 1 MB chunks."""
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while data := f.read(chunk):
                h.update(data)
        return h.hexdigest()
    except OSError:
        return ""


def size_mb(path: Path) -> float:
    try:
        return path.stat().st_size / (1024 * 1024)
    except OSError:
        return 0.0


def safe_move(src: Path, dst_dir: Path, apply: bool, conn: sqlite3.Connection,
              run_id: str, phase: int, reason: str = "") -> bool:
    """Move src into dst_dir. Creates dst_dir if needed. Returns True on success."""
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name

    # Handle collision — append timestamp
    if dst.exists() and dst != src:
        stem = src.stem
        suffix = src.suffix
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = dst_dir / f"{stem}_{ts}{suffix}"

    mb = size_mb(src)
    sha = sha256_file(src) if (not src.is_dir() and mb < 500) else ""

    action = "move" if apply else "plan"
    log.info(f"[Phase {phase}] {'MOVE' if apply else 'PLAN'}: {src} → {dst} ({mb:.1f} MB)")

    if apply:
        try:
            shutil.move(str(src), str(dst))
            log_move(conn, run_id, phase, src, dst, action, mb, sha, reason)
            return True
        except Exception as e:
            log.error(f"  ERROR moving {src}: {e}")
            log_move(conn, run_id, phase, src, dst, "error", mb, sha, str(e))
            return False
    else:
        log_move(conn, run_id, phase, src, dst, action, mb, sha, reason)
        return True


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1: Root Cleanup
# ─────────────────────────────────────────────────────────────────────────────

def phase1_root_cleanup(apply: bool, conn: sqlite3.Connection, run_id: str) -> dict:
    """Scan LitigationOS root and move CANON violations to canonical destinations."""
    log.info("=" * 70)
    log.info("PHASE 1: Root CANON cleanup")
    log.info("=" * 70)

    root = LITIGOS_ROOT
    stats = {"planned": 0, "moved": 0, "skipped": 0, "errors": 0, "size_mb": 0.0}

    for item in sorted(root.iterdir()):
        name = item.name

        # Skip protected items and hidden dirs
        if name in PROTECTED_AT_ROOT:
            log.debug(f"  PROTECTED (root): {name}")
            continue
        if name in TOLERATED_DOTFILES:
            log.debug(f"  TOLERATED dotfile: {name}")
            continue
        if name in PROTECTED_DIRS:
            log.debug(f"  PROTECTED dir: {name}")
            continue
        if name.startswith("."):
            log.debug(f"  Hidden (skip): {name}")
            continue

        # Direct match in ROOT_MOVE_MAP
        if name in ROOT_MOVE_MAP:
            dst_dir = ROOT_MOVE_MAP[name]
            mb = size_mb(item)
            stats["planned"] += 1
            stats["size_mb"] += mb
            ok = safe_move(item, dst_dir, apply, conn, run_id, 1,
                           reason=f"ROOT_MOVE_MAP → {dst_dir.relative_to(root)}")
            if apply:
                if ok:
                    stats["moved"] += 1
                else:
                    stats["errors"] += 1
            continue

        # Pattern-based match
        matched = False
        for pattern, dst_dir in ROOT_PATTERN_MOVES:
            if pattern.match(name):
                mb = size_mb(item)
                stats["planned"] += 1
                stats["size_mb"] += mb
                ok = safe_move(item, dst_dir, apply, conn, run_id, 1,
                               reason=f"PATTERN_MATCH {pattern.pattern} → {dst_dir.relative_to(root)}")
                if apply:
                    if ok:
                        stats["moved"] += 1
                    else:
                        stats["errors"] += 1
                matched = True
                break

        if not matched:
            log.warning(f"  UNMATCHED at root: {name} — add to ROOT_MOVE_MAP or PROTECTED_AT_ROOT")
            log_move(conn, run_id, 1, item, item, "skip", size_mb(item), "",
                     "No rule matched — manual review needed")
            stats["skipped"] += 1

    log.info(f"Phase 1 complete — planned={stats['planned']}, moved={stats['moved']}, "
             f"skipped={stats['skipped']}, errors={stats['errors']}, "
             f"total_size={stats['size_mb']:.1f} MB")
    return stats


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2: Intra-Repo Deduplication
# ─────────────────────────────────────────────────────────────────────────────

def phase2_dedup(apply: bool, conn: sqlite3.Connection, run_id: str) -> dict:
    """SHA-256 dedup across all 13 canonical folders. Move dupes to I:\\LITIGOS_DEDUP\\."""
    log.info("=" * 70)
    log.info("PHASE 2: Intra-repo SHA-256 deduplication")
    log.info("=" * 70)

    stats = {"scanned": 0, "dupes": 0, "moved": 0, "errors": 0, "freed_mb": 0.0}
    seen: dict[str, Path] = {}  # sha256 → first path seen

    # Skip very large files (DBs) — too slow and risky
    MAX_HASH_MB = 200

    # Scan all 13 canonical folders
    for canon_dir_name in [
        "01_EVIDENCE", "02_AUTHORITY", "03_COURT", "04_ANALYSIS", "05_FILINGS",
        "06_DATA", "07_CODE", "08_MEDIA", "09_REFERENCE", "10_EXTERNAL",
        "11_ARCHIVES", "12_WORKSPACE"
        # Exclude 00_SYSTEM — protected
    ]:
        canon_dir = LITIGOS_ROOT / canon_dir_name
        if not canon_dir.exists():
            continue

        for fpath in canon_dir.rglob("*"):
            if not fpath.is_file():
                continue
            if fpath.suffix.lower() in {".shm", ".wal"}:
                continue  # Skip WAL files

            mb = size_mb(fpath)
            if mb > MAX_HASH_MB:
                log.debug(f"  SKIP large file: {fpath} ({mb:.0f} MB)")
                continue

            stats["scanned"] += 1
            sha = sha256_file(fpath)
            if not sha:
                continue

            if sha in seen:
                # Duplicate found
                original = seen[sha]
                stats["dupes"] += 1
                stats["freed_mb"] += mb
                log.info(f"  DUPE: {fpath} == {original} ({mb:.1f} MB)")

                # Move to I:\LITIGOS_DEDUP\{date}\{sha8}_{name}
                date_dir = DEDUP_STAGING / datetime.now().strftime("%Y-%m-%d")
                dst_dir = date_dir / f"{sha[:8]}_{fpath.stem}"[:60]
                ok = safe_move(fpath, dst_dir, apply, conn, run_id, 2,
                               reason=f"DUPE of {original}")
                if apply:
                    if ok:
                        stats["moved"] += 1
                    else:
                        stats["errors"] += 1
            else:
                seen[sha] = fpath

    log.info(f"Phase 2 complete — scanned={stats['scanned']}, dupes={stats['dupes']}, "
             f"moved={stats['moved']}, freed={stats['freed_mb']:.1f} MB")
    return stats


# ─────────────────────────────────────────────────────────────────────────────
# Phase 3: Other Drives Scan
# ─────────────────────────────────────────────────────────────────────────────

# MEEK keywords for routing files from other drives into canonical folders
MEEK_ROUTING: list[tuple[re.Pattern, Path]] = [
    (re.compile(r"(mcneill|mcr|mcl|mre|benchbook|statute|court.rule)", re.I),
     LITIGOS_ROOT / "02_AUTHORITY"),
    (re.compile(r"(police.report|nspd|incident|witness|appclose|exhibit|evidence)", re.I),
     LITIGOS_ROOT / "01_EVIDENCE"),
    (re.compile(r"(court.order|judgment|docket|transcript|ruling)", re.I),
     LITIGOS_ROOT / "03_COURT"),
    (re.compile(r"(analysis|timeline|impeachment|contradiction|intelligence)", re.I),
     LITIGOS_ROOT / "04_ANALYSIS"),
    (re.compile(r"(filing|motion|brief|complaint|petition|affidavit)", re.I),
     LITIGOS_ROOT / "05_FILINGS"),
    (re.compile(r"(litigationos|litigation_context|mbp_brain|nexus)", re.I),
     LITIGOS_ROOT / "06_DATA"),
]

# File extensions of interest from other drives
RELEVANT_EXTENSIONS: frozenset[str] = frozenset({
    ".pdf", ".docx", ".doc", ".rtf",
    ".mp3", ".mp4", ".wav", ".m4a",
    ".png", ".jpg", ".jpeg", ".bmp",
    ".txt", ".md", ".csv", ".json",
    ".db", ".sqlite",
    ".eml", ".msg",
})

# Directories on other drives to scan
OTHER_DRIVE_ROOTS: list[tuple[Path, str]] = [
    (Path(r"D:\\"), "D:"),
    (Path(r"F:\\"), "F:"),
    (Path(r"G:\\"), "G:"),
]

# Directories to SKIP on other drives (system, bloat)
SKIP_ON_OTHER_DRIVES: frozenset[str] = frozenset({
    "$RECYCLE.BIN", "System Volume Information", "Windows", "Program Files",
    "Program Files (x86)", "ProgramData", "Users", "AppData", "Temp", "tmp",
    "node_modules", ".git", "__pycache__", ".venv",
})


def route_from_other_drive(fpath: Path) -> Optional[Path]:
    """Determine canonical destination for a file from another drive."""
    stem = fpath.stem.lower()
    for pattern, dest in MEEK_ROUTING:
        if pattern.search(stem) or pattern.search(str(fpath).lower()):
            return dest
    # Fallback by extension
    ext = fpath.suffix.lower()
    if ext in {".db", ".sqlite"}:
        return LITIGOS_ROOT / "06_DATA"
    if ext in {".mp3", ".mp4", ".wav", ".m4a"}:
        return LITIGOS_ROOT / "08_MEDIA" / "AUDIO"
    if ext in {".png", ".jpg", ".jpeg", ".bmp"}:
        return LITIGOS_ROOT / "08_MEDIA" / "PHOTOS"
    return None


def phase3_other_drives(apply: bool, conn: sqlite3.Connection, run_id: str,
                         report_only: bool = True) -> dict:
    """Scan D:\\, F:\\, G:\\ for LitigationOS-relevant files and report/route them."""
    log.info("=" * 70)
    log.info("PHASE 3: Other drives scan (report mode — files stay in place)")
    log.info("=" * 70)

    stats = {"scanned": 0, "relevant": 0, "routed": 0}
    report_lines: list[str] = []

    for drive_root, drive_label in OTHER_DRIVE_ROOTS:
        if not drive_root.exists():
            log.info(f"  {drive_label} not accessible — skip")
            continue

        log.info(f"  Scanning {drive_label}...")
        try:
            for item in drive_root.rglob("*"):
                if not item.is_file():
                    continue

                # Skip excluded dirs
                parts = set(p.upper() for p in item.parts)
                if parts & {d.upper() for d in SKIP_ON_OTHER_DRIVES}:
                    continue

                stats["scanned"] += 1
                ext = item.suffix.lower()
                if ext not in RELEVANT_EXTENSIONS:
                    continue

                stats["relevant"] += 1
                dest = route_from_other_drive(item)
                if dest:
                    stats["routed"] += 1
                    mb = size_mb(item)
                    report_lines.append(
                        f"{drive_label}  {item}  →  {dest.relative_to(LITIGOS_ROOT)}  ({mb:.1f} MB)"
                    )
                    log_move(conn, run_id, 3, item, dest / item.name, "plan", mb, "",
                             f"DRIVE_SCAN {drive_label} — MEEK routing")

        except PermissionError as e:
            log.warning(f"  Permission denied on {drive_root}: {e}")
        except Exception as e:
            log.error(f"  Error scanning {drive_label}: {e}")

    # Write report
    report_path = LITIGOS_ROOT / "04_ANALYSIS" / "REPORTS" / "OTHER_DRIVES_SCAN.txt"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"Other Drives Scan Report — {datetime.now().isoformat()}\n")
        f.write(f"Total scanned: {stats['scanned']} | Relevant: {stats['relevant']} | Routable: {stats['routed']}\n")
        f.write("=" * 80 + "\n")
        for line in report_lines:
            f.write(line + "\n")

    log.info(f"Phase 3 complete — scanned={stats['scanned']}, relevant={stats['relevant']}, "
             f"routable={stats['routed']}")
    log.info(f"  Report written: {report_path}")
    return stats


# ─────────────────────────────────────────────────────────────────────────────
# Summary Report
# ─────────────────────────────────────────────────────────────────────────────

def print_summary(conn: sqlite3.Connection, run_id: str) -> None:
    """Print a human-readable summary of all planned/executed moves."""
    print("\n" + "=" * 70)
    print(f"APEX ORGANIZER v{__version__} — RUN SUMMARY")
    print("=" * 70)

    rows = conn.execute(
        "SELECT phase, action, COUNT(*), SUM(size_mb) FROM moves WHERE run_id=? GROUP BY phase, action ORDER BY phase, action",
        (run_id,)
    ).fetchall()

    for phase, action, count, total_mb in rows:
        print(f"  Phase {phase} | {action:12s} | {count:5d} files | {(total_mb or 0):10.1f} MB")

    # Print all planned moves
    print("\n--- PLANNED/EXECUTED MOVES ---")
    moves = conn.execute(
        "SELECT phase, action, src, dst, size_mb, reason FROM moves WHERE run_id=? ORDER BY phase, id",
        (run_id,)
    ).fetchall()

    for phase, action, src, dst, mb, reason in moves:
        src_short = src.replace(str(LITIGOS_ROOT), "<ROOT>")
        dst_short = dst.replace(str(LITIGOS_ROOT), "<ROOT>")
        print(f"  [P{phase}][{action}] {src_short}")
        print(f"        → {dst_short}  ({(mb or 0):.1f} MB)")
        if reason:
            print(f"        reason: {reason}")
    print("=" * 70)


# ─────────────────────────────────────────────────────────────────────────────
# Free Disk Report
# ─────────────────────────────────────────────────────────────────────────────

def check_disk_space() -> None:
    import shutil as _shutil
    for drive, label in [
        (r"C:\\", "C:"), (r"I:\\", "I:"), (r"J:\\", "J:")
    ]:
        try:
            total, used, free = _shutil.disk_usage(drive)
            pct_free = free / total * 100
            log.info(f"  {label} — {free/1e9:.1f} GB free / {total/1e9:.1f} GB total ({pct_free:.1f}% free)")
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description=f"APEX Organizer v{__version__} — CANON-aware LitigationOS file organization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--scan", action="store_true", default=True,
                        help="Run full scan (default)")
    parser.add_argument("--apply", action="store_true",
                        help="Execute moves (default is dry-run plan only)")
    parser.add_argument("--phase", type=int, choices=[1, 2, 3],
                        help="Run only one phase (1=root, 2=dedup, 3=drives)")
    parser.add_argument("--ledger", default=str(LEDGER_PATH),
                        help="Path to SQLite ledger")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable debug logging")
    args = parser.parse_args()

    if args.verbose:
        log.setLevel(logging.DEBUG)

    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    log.info(f"APEX Organizer v{__version__} — run_id={run_id}")
    log.info(f"Mode: {'APPLY (LIVE MOVES)' if args.apply else 'DRY-RUN (plan only)'}")
    log.info(f"Root: {LITIGOS_ROOT}")

    check_disk_space()

    conn = get_ledger(Path(args.ledger))
    conn.execute(
        "INSERT INTO runs(run_id, started, phase, applied) VALUES(?,?,?,?)",
        (run_id, datetime.now().isoformat(),
         str(args.phase or "all"), 1 if args.apply else 0)
    )
    conn.commit()

    all_stats: dict[str, dict] = {}

    try:
        if args.phase is None or args.phase == 1:
            all_stats["phase1"] = phase1_root_cleanup(args.apply, conn, run_id)

        if args.phase is None or args.phase == 2:
            all_stats["phase2"] = phase2_dedup(args.apply, conn, run_id)

        if args.phase is None or args.phase == 3:
            all_stats["phase3"] = phase3_other_drives(args.apply, conn, run_id)

    finally:
        conn.execute(
            "UPDATE runs SET finished=? WHERE run_id=?",
            (datetime.now().isoformat(), run_id)
        )
        conn.commit()

    print_summary(conn, run_id)
    conn.close()

    if not args.apply:
        print("\n⚠️  DRY-RUN mode — no files were moved.")
        print("    Add --apply to execute all moves.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
