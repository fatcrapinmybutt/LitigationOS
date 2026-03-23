"""OMEGA-FLATTEN CLI — entry point for drive flattening, analysis, and dedup.

LitigationOS Event Horizon Δ∞

Usage:
    python -m drive_flattener flatten F --phase all
    python -m drive_flattener flatten G --phase scan --limit 1000
    python -m drive_flattener flatten F --phase dedup --dry-run
    python -m drive_flattener flatten F --resume
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
import time
from typing import Optional

# UTF-8 stdout — required by LitigationOS coding standards
if hasattr(sys.stdout, "fileno"):
    try:
        sys.stdout = open(  # noqa: SIM115
            sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace",
        )
    except (OSError, ValueError):
        pass

from .analyzer import analyze_files
from .config import FLATTEN_DB_SCHEMA
from .deduplicator import dedup_drive
from .forge import forge_drive
from .organizer import organize_drive
from .scanner import scan_drive

VALID_PHASES = {"scan", "organize", "analyze", "dedup", "forge", "all"}


def _open_db(drive: str) -> sqlite3.Connection:
    """Open (or create) the ``flatten.db`` for *drive* with proper PRAGMAs."""
    index_dir = os.path.join(f"{drive}:\\_INDEX")
    os.makedirs(index_dir, exist_ok=True)
    db_path = os.path.join(index_dir, "flatten.db")

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA synchronous = NORMAL")

    # Create schema
    conn.executescript(FLATTEN_DB_SCHEMA)
    conn.commit()
    return conn


def _create_session(conn: sqlite3.Connection, drive: str) -> int:
    """Insert a new ``scan_sessions`` row and return its id."""
    cur = conn.execute(
        "INSERT INTO scan_sessions (drive) VALUES (?)", (drive,),
    )
    conn.commit()
    return cur.lastrowid  # type: ignore[return-value]


def _resume_session(conn: sqlite3.Connection, drive: str) -> Optional[int]:
    """Find the most recent non-completed session for *drive*."""
    row = conn.execute(
        """SELECT id FROM scan_sessions
            WHERE drive = ? AND status != 'completed'
            ORDER BY id DESC LIMIT 1""",
        (drive,),
    ).fetchone()
    return row[0] if row else None


def _complete_session(conn: sqlite3.Connection, session_id: int) -> None:
    """Mark a scan session as completed."""
    conn.execute(
        """UPDATE scan_sessions
              SET completed_at = strftime('%Y-%m-%dT%H:%M:%S','now','localtime'),
                  status = 'completed'
            WHERE id = ?""",
        (session_id,),
    )
    conn.commit()


def run(
    drive: str,
    phase: str = "all",
    dry_run: bool = False,
    limit: Optional[int] = None,
    resume: bool = False,
) -> None:
    """Execute the OMEGA-FLATTEN pipeline for *drive*.

    Parameters
    ----------
    drive:
        Drive letter (e.g. ``"F"``).
    phase:
        Which phase to run: scan, organize, analyze, dedup, forge, all.
    dry_run:
        If ``True``, don't move files (organize + dedup phases).
    limit:
        Max files to process (scan + analyze phases).
    resume:
        If ``True``, resume the last incomplete session instead of starting fresh.
    """
    drive = drive.upper().rstrip(":\\")
    if len(drive) != 1 or not drive.isalpha():
        print(f"ERROR: Invalid drive letter: {drive}")
        sys.exit(1)

    root = f"{drive}:\\"
    if not os.path.isdir(root):
        print(f"ERROR: Drive {root} is not accessible")
        sys.exit(1)

    print(f"{'=' * 60}")
    print(f"  OMEGA-FLATTEN v1.0 — Drive {drive}:")
    print(f"  Phase: {phase}  |  Dry-run: {dry_run}  |  Limit: {limit or 'none'}")
    print(f"{'=' * 60}")
    print()

    conn = _open_db(drive)

    # Session management
    session_id: Optional[int] = None
    if resume:
        session_id = _resume_session(conn, drive)
        if session_id:
            print(f"  Resuming session {session_id}")
        else:
            print("  No incomplete session found — starting fresh")

    if session_id is None:
        session_id = _create_session(conn, drive)
        print(f"  New session {session_id}")

    t0 = time.perf_counter()
    run_all = phase == "all"

    try:
        # Phase: scan
        if run_all or phase == "scan":
            print(f"\n{'─' * 40}")
            print("  PHASE 1: SCAN")
            print(f"{'─' * 40}")
            scan_result = scan_drive(conn, drive, session_id, limit=limit)
            print(f"  → {scan_result['total_files']:,} files, "
                  f"{scan_result['total_size_bytes'] / (1024**3):.2f} GB")

        # Phase: organize
        if run_all or phase == "organize":
            print(f"\n{'─' * 40}")
            print("  PHASE 2: ORGANIZE")
            print(f"{'─' * 40}")
            org_result = organize_drive(conn, drive, session_id, dry_run=dry_run)
            print(f"  → {org_result['files_moved']:,} files moved")

        # Phase: analyze
        if run_all or phase == "analyze":
            print(f"\n{'─' * 40}")
            print("  PHASE 3: ANALYZE")
            print(f"{'─' * 40}")
            ana_result = analyze_files(conn, drive, session_id, limit=limit)
            print(f"  → {ana_result['files_analyzed']:,} files analyzed "
                  f"(H:{ana_result['high_value']} M:{ana_result['medium_value']})")

        # Phase: dedup
        if run_all or phase == "dedup":
            print(f"\n{'─' * 40}")
            print("  PHASE 4: DEDUP")
            print(f"{'─' * 40}")
            dedup_result = dedup_drive(conn, drive, session_id, dry_run=dry_run)
            total_d = dedup_result["phase1_dupes"] + dedup_result["phase2_dupes"] + dedup_result["phase3_dupes"]
            print(f"  → {total_d:,} duplicates, "
                  f"{dedup_result['space_saved_bytes'] / (1024**2):.1f} MB recoverable")

        # Phase: forge
        if run_all or phase == "forge":
            print(f"\n{'─' * 40}")
            print("  PHASE 5: FORGE")
            print(f"{'─' * 40}")
            forge_result = forge_drive(conn, drive, session_id)
            print(f"  → {forge_result['outputs_created']} outputs, "
                  f"{forge_result['timeline_events']:,} timeline events")

        _complete_session(conn, session_id)

    except KeyboardInterrupt:
        print("\n  INTERRUPTED — session checkpointed, use --resume to continue")
        conn.execute(
            "UPDATE scan_sessions SET status = 'interrupted' WHERE id = ?",
            (session_id,),
        )
        conn.commit()
    except Exception as exc:
        print(f"\n  ERROR: {exc}")
        conn.execute(
            "UPDATE scan_sessions SET status = 'error' WHERE id = ?",
            (session_id,),
        )
        conn.commit()
        raise
    finally:
        conn.close()

    elapsed = time.perf_counter() - t0
    print(f"\n{'=' * 60}")
    print(f"  OMEGA-FLATTEN DONE — {elapsed:.1f}s total")
    print(f"  DB: {drive}:\\_INDEX\\flatten.db")
    print(f"{'=' * 60}")


def main() -> None:
    """Argparse entry point."""
    parser = argparse.ArgumentParser(
        prog="omega-flatten",
        description="OMEGA-FLATTEN v1.0 — Drive Organization System (LitigationOS)",
    )
    sub = parser.add_subparsers(dest="command")

    flatten_p = sub.add_parser("flatten", help="Flatten a drive into ≤30 folders")
    flatten_p.add_argument("drive", help="Drive letter (e.g. F)")
    flatten_p.add_argument(
        "--phase", default="all",
        choices=sorted(VALID_PHASES),
        help="Which phase to run (default: all)",
    )
    flatten_p.add_argument("--dry-run", action="store_true", help="Don't move files")
    flatten_p.add_argument("--limit", type=int, default=None, help="Max files to process")
    flatten_p.add_argument("--resume", action="store_true", help="Resume last incomplete session")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "flatten":
        run(
            drive=args.drive,
            phase=args.phase,
            dry_run=args.dry_run,
            limit=args.limit,
            resume=args.resume,
        )


if __name__ == "__main__":
    main()
