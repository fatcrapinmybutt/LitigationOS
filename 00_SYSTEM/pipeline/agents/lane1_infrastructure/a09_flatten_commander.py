"""
A09 — FLATTEN COMMANDER
DELTA9 Fleet · Tier 3 · Lane 1 Infrastructure

Computes dest_path for canonical files to flatten directory depth to ≤3 levels.
READ-ONLY planning pass — does NOT move files. Moving is a separate verified pass.
"""
import os
from pathlib import Path

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LEGAL_EXTENSIONS, DATA_EXTENSIONS,
    LANE_A_SIGNALS, LANE_B_SIGNALS, LANE_C_SIGNALS
)

EVIDENCE_BASE = Path(r"C:\Users\andre\LitigationOS\02_EVIDENCE")

# Category → subdirectory mapping
CATEGORY_DIR_MAP = {
    "LEGAL_DOC": "legal_docs",
    "COURT_ORDER": "legal_docs",
    "MOTION": "legal_docs",
    "BRIEF": "legal_docs",
    "AFFIDAVIT": "legal_docs",
    "COMPLAINT": "legal_docs",
    "TRANSCRIPT": "legal_docs",
    "STATUTE": "legal_docs",
    "CASE_LAW": "legal_docs",
    "STRUCTURED_DATA": "data",
    "DATA": "data",
    "EVIDENCE_LOG": "data",
    "CODE": "code",
    "ARCHIVE": "archives",
    "IMAGE": "images",
    "CORRESPONDENCE": "correspondence",
    "ANALYSIS": "analysis",
    "OTHER": "misc",
}

MAX_DEPTH = 3


class FlattenCommander(Agent9999):
    """Computes flattened dest_path for canonical files (depth > 3)."""

    def __init__(self):
        super().__init__(agent_id="A09-FLATTEN-CMD")
        self._move_count = 0
        self._total_depth_reduction = 0

    def _validate_preconditions(self):
        cursor = self._db_execute(
            "SELECT COUNT(*) FROM files WHERE is_canonical = 1"
        )
        count = cursor.fetchone()[0]
        if count == 0:
            raise FatalAgentError("No canonical files found in DB — run dedup first")

    def _get_work_items(self) -> list:
        cursor = self._db_execute(
            "SELECT * FROM files WHERE is_canonical = 1 AND depth > 3 AND dest_path IS NULL"
        )
        return cursor.fetchall()

    def _process_item(self, row) -> None:
        file_id = row["id"]
        src_path = row["full_path"]
        category = row["category"] or "OTHER"

        subdir = CATEGORY_DIR_MAP.get(category, "misc")
        dest_dir = EVIDENCE_BASE / subdir
        filename = Path(src_path).name

        # Resolve collisions: append _2, _3, etc.
        dest_path = dest_dir / filename
        if self._dest_path_exists(str(dest_path), file_id):
            stem = Path(filename).stem
            suffix = Path(filename).suffix
            counter = 2
            while True:
                candidate = dest_dir / f"{stem}_{counter}{suffix}"
                if not self._dest_path_exists(str(candidate), file_id):
                    dest_path = candidate
                    break
                counter += 1

        # Compute depth reduction
        src_depth = str(src_path).count(os.sep)
        dest_depth = str(dest_path).count(os.sep)
        reduction = max(0, src_depth - dest_depth)
        self._total_depth_reduction += reduction

        # Verify dest depth ≤ MAX_DEPTH from EVIDENCE_BASE
        relative = dest_path.relative_to(EVIDENCE_BASE)
        if len(relative.parts) > MAX_DEPTH:
            raise SkipItemError(f"Computed path still too deep: {dest_path}")

        self._db_execute(
            "UPDATE files SET dest_path = ? WHERE id = ?",
            (str(dest_path), file_id)
        )
        self.db.commit()
        self._move_count += 1

    def _dest_path_exists(self, dest_path_str: str, exclude_id: int) -> bool:
        """Check if dest_path already assigned to another file in DB."""
        cursor = self._db_execute(
            "SELECT COUNT(*) FROM files WHERE dest_path = ? AND id != ?",
            (dest_path_str, exclude_id)
        )
        return cursor.fetchone()[0] > 0

    def _finalize(self):
        self._log("SUMMARY", f"Files needing move: {self._move_count}")
        avg_reduction = (
            self._total_depth_reduction / max(self._move_count, 1)
        )
        self._log("SUMMARY", f"Total depth reduction: {self._total_depth_reduction} "
                              f"(avg {avg_reduction:.1f} levels per file)")
        self._log("NOTE", "dest_path computed only — no files moved. "
                          "Run verified move pass separately.")
