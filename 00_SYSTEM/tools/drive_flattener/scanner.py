"""OMEGA-FLATTEN scanner — walks an entire drive tree, inventories every file.

LitigationOS Event Horizon Δ∞
"""
from __future__ import annotations

import hashlib
import os
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .config import (
    BATCH_SIZE,
    CHECKPOINT_INTERVAL,
    PROGRESS_INTERVAL,
    SKIP_DIRS,
    SKIP_FILES,
)
from .classifier import classify_file


def _sha256_file(filepath: str, chunk_size: int = 65536) -> Optional[str]:
    """Return SHA-256 hex digest for *filepath*, or ``None`` on error."""
    h = hashlib.sha256()
    try:
        with open(filepath, "rb") as fh:
            while True:
                chunk = fh.read(chunk_size)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except (PermissionError, OSError):
        return None


def _should_skip_dir(dirname: str) -> bool:
    """Return ``True`` if *dirname* (bare name, not full path) should be skipped."""
    if dirname in SKIP_DIRS:
        return True
    # Skip hidden dirs on Windows (start with .)
    if dirname.startswith(".") and dirname not in {".", ".."}:
        return True
    return False


def scan_drive(
    conn: sqlite3.Connection,
    drive: str,
    session_id: int,
    *,
    limit: Optional[int] = None,
    compute_hash: bool = True,
) -> Dict[str, Any]:
    """Walk *drive* and insert every discovered file into ``flat_files``.

    Parameters
    ----------
    conn:
        Open SQLite connection to ``flatten.db`` (WAL mode assumed).
    drive:
        Drive letter without colon, e.g. ``"F"``.
    session_id:
        Active ``scan_sessions.id``.
    limit:
        Stop after discovering this many files (useful for testing).
    compute_hash:
        Whether to compute SHA-256 for every file (slower but enables
        exact-duplicate detection later).

    Returns
    -------
    dict with keys: total_files, total_size_bytes, folders_seen, errors.
    """
    root = f"{drive}:\\"
    if not os.path.isdir(root):
        raise FileNotFoundError(f"Drive root does not exist: {root}")

    total_files = 0
    total_size: int = 0
    errors = 0
    folders_seen: Dict[str, int] = {}
    batch: List[Tuple[str, str, str, str, str, int, Optional[str], str]] = []

    t0 = time.perf_counter()
    last_progress = 0

    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        # Prune skip dirs in-place so os.walk doesn't descend
        dirnames[:] = [d for d in dirnames if not _should_skip_dir(d)]

        for fname in filenames:
            if fname in SKIP_FILES:
                continue

            filepath = os.path.join(dirpath, fname)

            # Stat the file
            try:
                st = os.stat(filepath)
                size = st.st_size
            except (PermissionError, OSError):
                errors += 1
                continue

            ext = Path(fname).suffix.lower() or ""
            folder = classify_file(filepath, ext)

            sha: Optional[str] = None
            if compute_hash and size < 500 * 1024 * 1024:  # skip hash for > 500 MB
                sha = _sha256_file(filepath)

            batch.append((filepath, drive, folder, fname, ext, size, sha, "scanned"))
            folders_seen[folder] = folders_seen.get(folder, 0) + 1
            total_files += 1
            total_size += size

            # Batch insert
            if len(batch) >= BATCH_SIZE:
                _flush_batch(conn, batch)
                batch.clear()

            # Checkpoint
            if total_files % CHECKPOINT_INTERVAL == 0:
                if batch:
                    _flush_batch(conn, batch)
                    batch.clear()
                conn.execute(
                    "UPDATE scan_sessions SET total_files = ?, total_size_bytes = ? WHERE id = ?",
                    (total_files, total_size, session_id),
                )
                conn.commit()

            # Progress
            if total_files - last_progress >= PROGRESS_INTERVAL:
                elapsed = time.perf_counter() - t0
                rate = total_files / elapsed if elapsed > 0 else 0
                print(
                    f"  [SCAN] {total_files:,} files discovered "
                    f"({total_size / (1024**3):.2f} GB) "
                    f"— {rate:,.0f} files/sec — {errors} errors",
                )
                last_progress = total_files

            if limit is not None and total_files >= limit:
                break

        if limit is not None and total_files >= limit:
            break

    # Final flush
    if batch:
        _flush_batch(conn, batch)

    # Update session
    conn.execute(
        """UPDATE scan_sessions
              SET total_files = ?, total_size_bytes = ?, status = 'scanned'
            WHERE id = ?""",
        (total_files, total_size, session_id),
    )
    conn.commit()

    elapsed = time.perf_counter() - t0
    print(
        f"  [SCAN] COMPLETE — {total_files:,} files, "
        f"{total_size / (1024**3):.2f} GB, "
        f"{errors} errors in {elapsed:.1f}s",
    )

    return {
        "total_files": total_files,
        "total_size_bytes": total_size,
        "folders_seen": folders_seen,
        "errors": errors,
        "elapsed_seconds": round(elapsed, 2),
    }


def _flush_batch(
    conn: sqlite3.Connection,
    batch: List[Tuple[str, str, str, str, str, int, Optional[str], str]],
) -> None:
    """Insert a batch of file records using ``executemany``."""
    conn.executemany(
        """INSERT INTO flat_files
               (original_path, drive, folder, filename, extension, size_bytes, sha256, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        batch,
    )
    conn.commit()
