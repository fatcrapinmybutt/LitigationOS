"""
SENTINEL Safe File Mover with Rollback
========================================
Atomic file moves: copy → verify SHA-256 → delete source (never delete-then-copy).
Full rollback DB for undoing any move within 30 days.

Story 1.3: Safe File Mover with Rollback
"""
import sys
import os
import shutil
import sqlite3
import hashlib
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional

_shared = Path(__file__).parent.parent / "shared"
if str(_shared) not in sys.path:
    sys.path.insert(0, str(_shared))

from autonomos_config import (
    SENTINEL_OPS_DB, ROLLBACK_DAYS, sha256_file, long_path,
    DIRECTORY_STANDARD, LITIGOS_ROOT, DIR_SORT_LOGS, DIR_UNSORTED,
    DIR_EVIDENCE, DIR_AUTHORITY, DIR_FILINGS, DIR_ANALYSIS,
    DIR_EXTRACTS, DIR_EXHIBITS, DIR_DOCS, DIR_APPS,
)


@dataclass
class MoveResult:
    """Result of a file move operation."""
    success: bool
    move_id: str = ""
    source: str = ""
    destination: str = ""
    sha256: str = ""
    error: str = ""
    collision_resolved: bool = False


def _init_ops_db(db_path: Path = SENTINEL_OPS_DB) -> sqlite3.Connection:
    """Initialize SENTINEL operations database."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=120000")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS moves (
            move_id TEXT PRIMARY KEY,
            source_path TEXT NOT NULL,
            dest_path TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            file_size INTEGER DEFAULT 0,
            moved_at TEXT NOT NULL,
            can_undo_until TEXT NOT NULL,
            lane TEXT DEFAULT '',
            classification TEXT DEFAULT '',
            is_undone INTEGER DEFAULT 0,
            undone_at TEXT DEFAULT ''
        );

        CREATE INDEX IF NOT EXISTS idx_moves_sha256 ON moves(sha256);
        CREATE INDEX IF NOT EXISTS idx_moves_lane ON moves(lane);
        CREATE INDEX IF NOT EXISTS idx_moves_date ON moves(moved_at);
        CREATE INDEX IF NOT EXISTS idx_moves_undo ON moves(can_undo_until);

        CREATE TABLE IF NOT EXISTS move_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            move_id TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT DEFAULT '',
            timestamp TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS collision_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_dest TEXT NOT NULL,
            resolved_dest TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            timestamp TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    return conn


# ── Lane → Directory Mapping ────────────────────────────────────────
LANE_TO_DIR = {
    "A": DIR_EVIDENCE / "Lane_A_Custody",
    "B": DIR_EVIDENCE / "Lane_B_Housing",
    "C": DIR_EVIDENCE / "Lane_C_Convergence",
    "D": DIR_EVIDENCE / "Lane_D_PPO",
    "E": DIR_EVIDENCE / "Lane_E_Misconduct",
    "F": DIR_EVIDENCE / "Lane_F_Appellate",
}

# Document type → subdirectory
DOC_TYPE_TO_SUBDIR = {
    "motion": "motions",
    "order": "orders",
    "affidavit": "affidavits",
    "brief": "briefs",
    "exhibit": "exhibits",
    "transcript": "transcripts",
    "correspondence": "correspondence",
    "financial": "financial",
    "photo": "photos",
    "form": "forms",
    "code": "_code",
    "data": "_data",
    "unknown": "_unsorted",
}


def _resolve_destination(lane: str, doc_type: str, filename: str, confidence: float) -> Path:
    """Determine the destination path for a classified file."""
    if confidence < 0.3:
        return DIR_SORT_LOGS / filename

    if lane and lane in LANE_TO_DIR:
        base = LANE_TO_DIR[lane]
    else:
        base = DIR_UNSORTED

    subdir = DOC_TYPE_TO_SUBDIR.get(doc_type, "_unsorted")
    return base / subdir / filename


def _resolve_collision(dest: Path) -> tuple[Path, bool]:
    """Handle destination collision by appending version suffix."""
    if not dest.exists():
        return dest, False

    stem = dest.stem
    ext = dest.suffix
    parent = dest.parent

    for version in range(2, 100):
        candidate = parent / f"{stem}_v{version}{ext}"
        if not candidate.exists():
            return candidate, True

    # Extreme edge case
    unique = parent / f"{stem}_{uuid.uuid4().hex[:8]}{ext}"
    return unique, True


class SentinelMover:
    """Manages atomic file moves with rollback capability."""

    def __init__(self, db_path: Path = SENTINEL_OPS_DB):
        self._db = _init_ops_db(db_path)

    def close(self):
        self._db.close()

    def safe_move(self, src: str | Path, lane: str = "", doc_type: str = "unknown",
                  confidence: float = 0.5, dest_override: str | Path | None = None) -> MoveResult:
        """
        Atomically move a file: copy → verify → delete source.
        Never deletes source without verifying destination integrity.
        """
        src_path = Path(src)
        if not src_path.exists():
            return MoveResult(success=False, source=str(src), error="Source file not found")

        # Compute source hash
        try:
            src_hash = sha256_file(src_path)
        except (OSError, PermissionError) as e:
            return MoveResult(success=False, source=str(src), error=f"Cannot hash source: {e}")

        # Determine destination
        if dest_override:
            dest_path = Path(dest_override)
        else:
            dest_path = _resolve_destination(lane, doc_type, src_path.name, confidence)

        # Resolve collisions
        dest_path, collision = _resolve_collision(dest_path)

        # Ensure destination directory exists
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        move_id = str(uuid.uuid4())
        result = MoveResult(
            success=False, move_id=move_id,
            source=str(src_path), destination=str(dest_path),
            sha256=src_hash, collision_resolved=collision
        )

        try:
            # Step 1: Copy (preserve metadata)
            dest_str = long_path(dest_path)
            src_str = long_path(src_path)
            shutil.copy2(src_str, dest_str)

            # Step 2: Verify destination hash matches
            dest_hash = sha256_file(dest_path)
            if dest_hash != src_hash:
                # Hash mismatch — delete corrupt copy and abort
                os.remove(str(dest_path))
                result.error = f"Hash mismatch: src={src_hash[:16]}... dest={dest_hash[:16]}..."
                return result

            # Step 3: Delete source (safe — destination verified)
            try:
                os.remove(str(src_path))
            except PermissionError:
                # Can't delete source — still a successful copy, just warn
                result.error = "WARN: Source not deleted (permission denied) — file copied successfully"

            # Record in rollback DB
            now = datetime.now()
            undo_until = (now + timedelta(days=ROLLBACK_DAYS)).isoformat()
            file_size = dest_path.stat().st_size

            self._db.execute("""
                INSERT INTO moves (move_id, source_path, dest_path, sha256, file_size,
                moved_at, can_undo_until, lane, classification)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (move_id, str(src_path), str(dest_path), src_hash, file_size,
                  now.isoformat(), undo_until, lane, doc_type))

            if collision:
                self._db.execute("""
                    INSERT INTO collision_log (original_dest, resolved_dest, sha256)
                    VALUES (?, ?, ?)
                """, (str(_resolve_destination(lane, doc_type, src_path.name, confidence)),
                      str(dest_path), src_hash))

            self._log(move_id, "MOVED", f"{src_path} → {dest_path}")
            self._db.commit()

            result.success = True

        except Exception as e:
            result.error = str(e)
            self._log(move_id, "FAILED", str(e))
            self._db.commit()

        return result

    def undo(self, move_id: str) -> MoveResult:
        """Undo a previous move by reversing source and destination."""
        row = self._db.execute("""
            SELECT source_path, dest_path, sha256, can_undo_until, is_undone
            FROM moves WHERE move_id=?
        """, (move_id,)).fetchone()

        if not row:
            return MoveResult(success=False, error=f"Move {move_id} not found")

        src, dest, sha256, undo_until, is_undone = row

        if is_undone:
            return MoveResult(success=False, error="Already undone")

        if datetime.now() > datetime.fromisoformat(undo_until):
            return MoveResult(success=False, error="Undo window expired")

        dest_path = Path(dest)
        src_path = Path(src)

        if not dest_path.exists():
            return MoveResult(success=False, error="Destination file no longer exists")

        # Reverse the move
        src_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(str(dest_path), str(src_path))
            dest_hash = sha256_file(src_path)
            if dest_hash != sha256:
                os.remove(str(src_path))
                return MoveResult(success=False, error="Hash mismatch during undo")
            os.remove(str(dest_path))
        except Exception as e:
            return MoveResult(success=False, error=f"Undo failed: {e}")

        self._db.execute("""
            UPDATE moves SET is_undone=1, undone_at=datetime('now') WHERE move_id=?
        """, (move_id,))
        self._log(move_id, "UNDONE", f"{dest} → {src}")
        self._db.commit()

        return MoveResult(success=True, move_id=move_id, source=dest, destination=src, sha256=sha256)

    def recent_moves(self, limit: int = 20) -> list[dict]:
        """Get recent move operations."""
        rows = self._db.execute("""
            SELECT move_id, source_path, dest_path, sha256, lane, classification, moved_at, is_undone
            FROM moves ORDER BY moved_at DESC LIMIT ?
        """, (limit,)).fetchall()
        return [
            {"id": r[0], "source": r[1], "dest": r[2], "sha256": r[3][:16] + "...",
             "lane": r[4], "type": r[5], "moved_at": r[6], "undone": bool(r[7])}
            for r in rows
        ]

    def stats(self) -> dict:
        """Get mover statistics."""
        total = self._db.execute("SELECT COUNT(*) FROM moves").fetchone()[0]
        undone = self._db.execute("SELECT COUNT(*) FROM moves WHERE is_undone=1").fetchone()[0]
        collisions = self._db.execute("SELECT COUNT(*) FROM collision_log").fetchone()[0]
        return {"total_moves": total, "undone": undone, "collisions": collisions, "active": total - undone}

    def _log(self, move_id: str, action: str, details: str = ""):
        self._db.execute(
            "INSERT INTO move_log (move_id, action, details) VALUES (?, ?, ?)",
            (move_id, action, details)
        )


# ── CLI Entry Point ─────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SENTINEL File Mover")
    sub = parser.add_subparsers(dest="action")

    undo_p = sub.add_parser("undo", help="Undo a move")
    undo_p.add_argument("move_id", help="Move ID to undo")

    hist_p = sub.add_parser("history", help="Show recent moves")
    hist_p.add_argument("--limit", type=int, default=20)

    stats_p = sub.add_parser("stats", help="Show mover statistics")

    args = parser.parse_args()
    mover = SentinelMover()

    if args.action == "undo":
        result = mover.undo(args.move_id)
        print(f"Undo {'succeeded' if result.success else 'failed'}: {result.error or 'OK'}")
    elif args.action == "history":
        for m in mover.recent_moves(args.limit):
            status = "↩" if m["undone"] else "→"
            print(f"  [{m['lane']}] {m['source']} {status} {m['dest']}")
    elif args.action == "stats":
        s = mover.stats()
        print(f"Moves: {s['total_moves']} total, {s['active']} active, "
              f"{s['undone']} undone, {s['collisions']} collisions")
    else:
        parser.print_help()
