"""OMEGA-FLATTEN organizer — creates taxonomy folders and moves files.

LitigationOS Event Horizon Δ∞

CRITICAL: No hard deletions.  Files are *moved*, never deleted.
"""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .config import (
    BATCH_SIZE,
    CHECKPOINT_INTERVAL,
    PROGRESS_INTERVAL,
    TAXONOMY,
)

# Folders that must not have their contents moved out
_SYSTEM_FOLDERS = {"_INDEX", "_DEDUP", "_UNKNOWN"}


def _ensure_taxonomy_dirs(drive: str) -> None:
    """Create all 30 taxonomy folders on the drive root."""
    root = Path(f"{drive}:\\")
    for folder_name in TAXONOMY:
        folder = root / folder_name
        folder.mkdir(parents=True, exist_ok=True)


def _safe_dest_path(dest_dir: Path, filename: str) -> Path:
    """Return a collision-free destination path.

    If ``dest_dir / filename`` already exists, append ``_1``, ``_2``, … until
    a free name is found.
    """
    candidate = dest_dir / filename
    if not candidate.exists():
        return candidate

    stem = Path(filename).stem
    suffix = Path(filename).suffix
    counter = 1
    while True:
        candidate = dest_dir / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1
        if counter > 10000:
            # Safety valve
            raise RuntimeError(f"Too many collisions for {filename} in {dest_dir}")


def _file_already_in_correct_folder(original_path: str, folder: str, drive: str) -> bool:
    """Return ``True`` if the file is already inside its target taxonomy folder."""
    expected_root = os.path.normpath(f"{drive}:\\{folder}")
    norm_original = os.path.normpath(original_path)
    return norm_original.startswith(expected_root + os.sep) or norm_original == expected_root


def _file_in_system_folder(original_path: str, drive: str) -> bool:
    """Return ``True`` if the file lives inside _INDEX, _DEDUP, or _UNKNOWN."""
    norm = os.path.normpath(original_path)
    for sys_folder in _SYSTEM_FOLDERS:
        sys_root = os.path.normpath(f"{drive}:\\{sys_folder}")
        if norm.startswith(sys_root + os.sep) or norm == sys_root:
            return True
    return False


def organize_drive(
    conn: sqlite3.Connection,
    drive: str,
    session_id: int,
    *,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Move scanned files into their taxonomy folders.

    Parameters
    ----------
    conn:
        Connection to ``flatten.db``.
    drive:
        Drive letter (no colon).
    session_id:
        Active ``scan_sessions.id``.
    dry_run:
        If ``True``, compute moves but don't touch the filesystem.

    Returns
    -------
    dict with keys: files_moved, files_skipped, errors, manifest_path.
    """
    _ensure_taxonomy_dirs(drive)

    cursor = conn.execute(
        """SELECT id, original_path, folder, filename
             FROM flat_files
            WHERE drive = ? AND status = 'scanned'
            ORDER BY id""",
        (drive,),
    )

    files_moved = 0
    files_skipped = 0
    errors = 0
    manifest: List[Dict[str, str]] = []
    update_batch: List[Tuple[str, int]] = []

    t0 = time.perf_counter()
    last_progress = 0

    while True:
        rows = cursor.fetchmany(BATCH_SIZE)
        if not rows:
            break

        for file_id, original_path, folder, filename in rows:
            # Skip files already in system folders
            if _file_in_system_folder(original_path, drive):
                files_skipped += 1
                continue

            # Skip files already in correct folder
            if _file_already_in_correct_folder(original_path, folder, drive):
                # Just mark as organized without moving
                update_batch.append((original_path, file_id))
                files_skipped += 1
                continue

            # Verify source exists
            if not os.path.isfile(original_path):
                files_skipped += 1
                continue

            dest_dir = Path(f"{drive}:\\{folder}")
            try:
                dest_path = _safe_dest_path(dest_dir, filename)
            except RuntimeError:
                errors += 1
                continue

            if not dry_run:
                try:
                    shutil.move(original_path, str(dest_path))
                except (PermissionError, OSError, shutil.Error) as exc:
                    errors += 1
                    continue

            manifest.append({
                "old": original_path,
                "new": str(dest_path),
                "folder": folder,
            })
            update_batch.append((str(dest_path), file_id))
            files_moved += 1

            # Progress
            processed = files_moved + files_skipped + errors
            if processed - last_progress >= PROGRESS_INTERVAL:
                elapsed = time.perf_counter() - t0
                print(
                    f"  [ORGANIZE] {files_moved:,} moved, "
                    f"{files_skipped:,} skipped, {errors} errors "
                    f"— {elapsed:.1f}s",
                )
                last_progress = processed

        # Batch update DB
        if update_batch:
            conn.executemany(
                """UPDATE flat_files
                      SET new_path = ?, status = 'organized'
                    WHERE id = ?""",
                update_batch,
            )
            conn.commit()
            update_batch.clear()

    # Flush remaining updates
    if update_batch:
        conn.executemany(
            """UPDATE flat_files
                  SET new_path = ?, status = 'organized'
                WHERE id = ?""",
            update_batch,
        )
        conn.commit()

    # Write manifest
    manifest_path = os.path.join(f"{drive}:\\_INDEX", "MOVE_MANIFEST.json")
    label = "DRY RUN" if dry_run else "EXECUTED"
    manifest_doc = {
        "label": f"OMEGA-FLATTEN organize — {label}",
        "drive": drive,
        "session_id": session_id,
        "files_moved": files_moved,
        "files_skipped": files_skipped,
        "errors": errors,
        "moves": manifest,
    }
    try:
        os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
        with open(manifest_path, "w", encoding="utf-8") as fh:
            json.dump(manifest_doc, fh, indent=2, ensure_ascii=False)
    except (PermissionError, OSError) as exc:
        print(f"  [ORGANIZE] WARNING: Could not write manifest: {exc}")
        manifest_path = ""

    # Update session
    conn.execute(
        "UPDATE scan_sessions SET files_moved = ? WHERE id = ?",
        (files_moved, session_id),
    )
    conn.commit()

    elapsed = time.perf_counter() - t0
    print(
        f"  [ORGANIZE] COMPLETE — {files_moved:,} moved, "
        f"{files_skipped:,} skipped, {errors} errors in {elapsed:.1f}s",
    )

    return {
        "files_moved": files_moved,
        "files_skipped": files_skipped,
        "errors": errors,
        "manifest_path": manifest_path,
        "elapsed_seconds": round(elapsed, 2),
    }
