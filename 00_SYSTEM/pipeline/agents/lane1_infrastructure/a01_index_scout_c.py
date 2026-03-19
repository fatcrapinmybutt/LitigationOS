"""
DELTA9 — A01 Index Scout C
Tier 1 · Lane 1 Infrastructure · MAX LEVEL 9999++

Crawls C:\\Users\\andre\\scans AND C:\\Users\\andre\\LitigationOS.
Catalogs every file into master_index.db with batch inserts.
"""
import fnmatch
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LEGAL_EXTENSIONS, DATA_EXTENSIONS, CODE_EXTENSIONS, ARCHIVE_EXTENSIONS,
    IMAGE_EXTENSIONS, SKIP_DIRS, SKIP_EXTENSIONS,
)

# Priority map for ready_queue
_LEGAL_PRIORITY = {
    '.pdf': 10,
    '.docx': 9,
    '.md': 8,
    '.doc': 7,
    '.rtf': 6,
    '.txt': 5,
}

_ROOT_DIRS = [
    r"C:\Users\andre\scans",
    r"C:\Users\andre\LitigationOS",
]


class IndexScoutC(Agent9999):
    """Index Scout for C: drive targets (scans + LitigationOS)."""

    def __init__(self):
        super().__init__(agent_id="A01-INDEX-SCOUT-C")
        self.checkpoint_interval = 5000

    # ------------------------------------------------------------------
    # Abstract implementations
    # ------------------------------------------------------------------
    def _validate_preconditions(self) -> None:
        for d in _ROOT_DIRS:
            if not os.path.isdir(d):
                raise FatalAgentError(f"Required directory missing: {d}")

    def _ensure_tables(self) -> None:
        """Verify expected tables exist (created by orchestrator)."""
        cursor = self._db_execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('files','ready_queue')"
        )
        found = {row[0] for row in cursor.fetchall()}
        for tbl in ("files", "ready_queue"):
            if tbl not in found:
                raise FatalAgentError(f"Required table '{tbl}' missing — run orchestrator first")

    def _get_work_items(self) -> list:
        return list(_ROOT_DIRS)

    def _process_item(self, root_dir: Any) -> None:
        """Walk *root_dir*, batch-insert files into the index."""
        drive = os.path.splitdrive(root_dir)[0].rstrip(":") or "C"
        lp_root = self.long_path(root_dir)
        file_batch: list = []
        queue_batch: list = []
        batch_size = 1000
        files_in_root = 0

        for dirpath, dirnames, filenames in os.walk(lp_root, topdown=True):
            # Prune skipped directories in-place
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

            # Calculate depth relative to root
            rel = os.path.relpath(dirpath, lp_root)
            depth = 0 if rel == "." else rel.count(os.sep) + 1

            for fname in filenames:
                ext = os.path.splitext(fname)[1].lower()
                if ext in SKIP_EXTENSIONS:
                    continue

                full_path = os.path.join(dirpath, fname)

                # Safe stat
                st = self.safe_stat(full_path)
                if st is None:
                    self.stats.skipped += 1
                    continue

                size_bytes = st.st_size
                try:
                    modified = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat()
                except (OSError, ValueError, OverflowError):
                    modified = None

                # Normalise the stored path (strip \\?\ prefix)
                stored_path = full_path
                if stored_path.startswith("\\\\?\\"):
                    stored_path = stored_path[4:]

                file_batch.append((
                    drive, stored_path, fname, ext, size_bytes,
                    depth, modified, 0,  # potential_dupe=0
                ))

                # Legal extension → ready_queue
                if ext in LEGAL_EXTENSIONS:
                    priority = _LEGAL_PRIORITY.get(ext, 5)
                    queue_batch.append((stored_path, "judicial", priority))

                files_in_root += 1

                # Flush batch
                if len(file_batch) >= batch_size:
                    self._flush_batch(file_batch, queue_batch)
                    file_batch.clear()
                    queue_batch.clear()
                    self._last_progress = time.time()

        # Final flush
        if file_batch:
            self._flush_batch(file_batch, queue_batch)

        self._log("INDEX", f"{root_dir}: {files_in_root} files indexed")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _flush_batch(self, file_batch: list, queue_batch: list) -> None:
        try:
            self._db_executemany(
                """INSERT OR IGNORE INTO files
                   (drive, full_path, file_name, extension, size_bytes, depth, modified, potential_dupe)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                file_batch,
            )
            if queue_batch:
                # Need file_id from files table — use full_path lookup
                for stored_path, queue_type, priority in queue_batch:
                    try:
                        self._db_execute(
                            """INSERT OR IGNORE INTO ready_queue (file_id, queue_type, priority)
                               SELECT id, ?, ? FROM files WHERE full_path = ?""",
                            (queue_type, priority, stored_path),
                        )
                    except Exception:
                        pass  # non-critical
            self.db.commit()
        except Exception as e:
            self._log("BATCH_ERR", f"Batch insert failed: {e}")
            try:
                self.db.rollback()
            except Exception:
                pass
