"""
DELTA9 — A03 Index Scout F
Tier 1 · Lane 1 Infrastructure · MAX LEVEL 9999++

Crawls F:\\ drive in its entirety.
Flags KNOWLEDGE_ALL.jsonl / COPILOT_SUPERPIN files as KNOWLEDGE.
Flags CANONICAL_ROOT_H directory contents with subcategory.
"""
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

_LEGAL_PRIORITY = {
    '.pdf': 10,
    '.docx': 9,
    '.md': 8,
    '.doc': 7,
    '.rtf': 6,
    '.txt': 5,
}

_KNOWLEDGE_FILENAMES = {"KNOWLEDGE_ALL.jsonl"}
_KNOWLEDGE_PREFIXES = ("COPILOT_SUPERPIN",)

_ROOT_DIRS = [r"F:\\"]


class IndexScoutF(Agent9999):
    """Index Scout for F: drive."""

    def __init__(self):
        super().__init__(agent_id="A03-INDEX-SCOUT-F")
        self.checkpoint_interval = 5000

    # ------------------------------------------------------------------
    # Abstract implementations
    # ------------------------------------------------------------------
    def _validate_preconditions(self) -> None:
        if not os.path.isdir(r"F:\\"):
            raise FatalAgentError("F:\\ drive not accessible")

    def _ensure_tables(self) -> None:
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
        drive = "F"
        lp_root = self.long_path(root_dir)
        file_batch: list = []
        queue_batch: list = []
        batch_size = 1000
        files_in_root = 0

        for dirpath, dirnames, filenames in os.walk(lp_root, topdown=True):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

            rel = os.path.relpath(dirpath, lp_root)
            depth = 0 if rel == "." else rel.count(os.sep) + 1

            # Detect CANONICAL_ROOT_H directory
            path_parts = dirpath.replace("/", os.sep).split(os.sep)
            in_canonical_root_h = "CANONICAL_ROOT_H" in path_parts

            for fname in filenames:
                ext = os.path.splitext(fname)[1].lower()
                if ext in SKIP_EXTENSIONS:
                    continue

                full_path = os.path.join(dirpath, fname)
                st = self.safe_stat(full_path)
                if st is None:
                    self.stats.skipped += 1
                    continue

                size_bytes = st.st_size
                try:
                    modified = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat()
                except (OSError, ValueError, OverflowError):
                    modified = None

                stored_path = full_path
                if stored_path.startswith("\\\\?\\"):
                    stored_path = stored_path[4:]

                # Determine category / subcategory
                category = None
                subcategory = None

                if fname in _KNOWLEDGE_FILENAMES or any(fname.startswith(p) for p in _KNOWLEDGE_PREFIXES):
                    category = "KNOWLEDGE"

                if in_canonical_root_h:
                    subcategory = "CANONICAL_ROOT_H"

                file_batch.append((
                    drive, stored_path, fname, ext, size_bytes,
                    depth, modified, 0, category, subcategory,
                ))

                # Legal extension → ready_queue
                if ext in LEGAL_EXTENSIONS:
                    priority = _LEGAL_PRIORITY.get(ext, 5)
                    queue_batch.append((stored_path, "judicial", priority))

                files_in_root += 1

                if len(file_batch) >= batch_size:
                    self._flush_batch(file_batch, queue_batch)
                    file_batch.clear()
                    queue_batch.clear()
                    self._last_progress = time.time()

        if file_batch:
            self._flush_batch(file_batch, queue_batch)

        self._log("INDEX", f"F:\\: {files_in_root} files indexed")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _flush_batch(self, file_batch: list, queue_batch: list) -> None:
        try:
            self._db_executemany(
                """INSERT OR IGNORE INTO files
                   (drive, full_path, file_name, extension, size_bytes, depth, modified,
                    potential_dupe, category, subcategory)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                file_batch,
            )
            if queue_batch:
                for stored_path, queue_type, priority in queue_batch:
                    try:
                        self._db_execute(
                            """INSERT OR IGNORE INTO ready_queue (file_id, queue_type, priority)
                               SELECT id, ?, ? FROM files WHERE full_path = ?""",
                            (queue_type, priority, stored_path),
                        )
                    except Exception:
                        pass
            self.db.commit()
        except Exception as e:
            self._log("BATCH_ERR", f"Batch insert failed: {e}")
            try:
                self.db.rollback()
            except Exception:
                pass
