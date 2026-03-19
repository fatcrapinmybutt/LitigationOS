"""
A08-ARCHIVE-CRACKER — Catalog archive contents, flag critical archives.
DELTA9 Fleet · Tier 2 · Lane 1 Infrastructure

.zip  → zipfile.namelist() to catalog inner files
.rar/.7z → log for manual extraction
SCANNED*.zip → CRITICAL category
"""
import os
import re
import zipfile

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LEGAL_EXTENSIONS, DATA_EXTENSIONS, CODE_EXTENSIONS,
    ARCHIVE_EXTENSIONS, SKIP_EXTENSIONS, CANONICAL_PRIORITY
)

CRITICAL_ZIP_PATTERN = re.compile(r"^SCANNED", re.IGNORECASE)
# Extensions considered legal for inner-file tagging
INNER_LEGAL_EXTENSIONS = LEGAL_EXTENSIONS


class ArchiveCracker(Agent9999):
    """Catalog archive contents into zip_contents, flag CRITICAL archives."""

    def __init__(self):
        super().__init__(agent_id="A08-ARCHIVE-CRACKER")
        self._zips_cataloged = 0
        self._manual_needed = 0
        self._critical_count = 0
        self._inner_files_total = 0

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------
    def _ensure_tables(self):
        self._db_execute("""
            CREATE TABLE IF NOT EXISTS zip_contents (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                zip_id     INTEGER NOT NULL,
                inner_path TEXT NOT NULL,
                inner_size INTEGER,
                inner_ext  TEXT,
                is_legal   INTEGER DEFAULT 0,
                created_by TEXT DEFAULT 'A08-ARCHIVE-CRACKER'
            )
        """)
        self.db.commit()

    # ------------------------------------------------------------------
    # Preconditions
    # ------------------------------------------------------------------
    def _validate_preconditions(self):
        placeholders = ",".join("?" for _ in ARCHIVE_EXTENSIONS)
        row = self._db_execute(
            f"SELECT COUNT(*) AS cnt FROM files WHERE extension IN ({placeholders})",
            tuple(ARCHIVE_EXTENSIONS)
        ).fetchone()
        if not row or row["cnt"] == 0:
            raise FatalAgentError("No archive files in files table")

    # ------------------------------------------------------------------
    # Work items
    # ------------------------------------------------------------------
    def _get_work_items(self) -> list:
        placeholders = ",".join("?" for _ in ARCHIVE_EXTENSIONS)
        rows = self._db_execute(
            f"""SELECT id, full_path, file_name, extension, size_bytes
                FROM files
                WHERE extension IN ({placeholders})
                ORDER BY size_bytes ASC""",
            tuple(ARCHIVE_EXTENSIONS)
        ).fetchall()
        return rows

    # ------------------------------------------------------------------
    # Process: catalog archive contents
    # ------------------------------------------------------------------
    def _process_item(self, row) -> None:
        file_id = row["id"]
        raw_path = row["full_path"]
        ext = (row["extension"] or "").lower()
        filename = row["file_name"] or os.path.basename(raw_path)
        path = self.long_path(raw_path)

        if not os.path.exists(path):
            raise SkipItemError(f"File gone: {raw_path}")

        # Flag SCANNED*.zip as CRITICAL
        category = None
        if CRITICAL_ZIP_PATTERN.match(filename):
            category = "CRITICAL"
            self._critical_count += 1

        if ext == ".zip":
            self._catalog_zip(file_id, path, raw_path)
            if category:
                self._db_execute(
                    "UPDATE files SET category = ? WHERE id = ?",
                    (category, file_id)
                )
            self.db.commit()
            self._zips_cataloged += 1
        elif ext in (".rar", ".7z"):
            self._log("MANUAL", f"Needs manual extraction: {raw_path}")
            self._db_execute(
                "UPDATE files SET category = ? WHERE id = ?",
                (category or "MANUAL_EXTRACT", file_id)
            )
            self.db.commit()
            self._manual_needed += 1
        else:
            # .tar, .gz, .bz2 — log but don't crash
            self._log("INFO", f"Unsupported archive type {ext}: {raw_path}")

    def _catalog_zip(self, zip_id: int, path: str, raw_path: str) -> None:
        """Read zip namelist and insert inner files into zip_contents."""
        try:
            with zipfile.ZipFile(path, "r") as zf:
                inserts = []
                for info in zf.infolist():
                    if info.is_dir():
                        continue
                    inner_path = info.filename
                    inner_ext = os.path.splitext(inner_path)[1].lower()
                    is_legal = 1 if inner_ext in INNER_LEGAL_EXTENSIONS else 0
                    inserts.append((
                        zip_id, inner_path, info.file_size, inner_ext, is_legal
                    ))
                    self._inner_files_total += 1

                if inserts:
                    self._db_executemany(
                        """INSERT INTO zip_contents
                           (zip_id, inner_path, inner_size, inner_ext, is_legal)
                           VALUES (?, ?, ?, ?, ?)""",
                        inserts
                    )
        except zipfile.BadZipFile:
            raise SkipItemError(f"Corrupt zip: {raw_path}")
        except PermissionError:
            raise SkipItemError(f"Permission denied: {raw_path}")
        except FileNotFoundError:
            raise SkipItemError(f"File not found during read: {raw_path}")
        except OSError as e:
            raise SkipItemError(f"OS error reading zip {raw_path}: {e}")

    # ------------------------------------------------------------------
    # Finalize
    # ------------------------------------------------------------------
    def _finalize(self):
        self._log("SUMMARY",
                  f"ZIPs cataloged: {self._zips_cataloged} | "
                  f"Manual needed: {self._manual_needed} | "
                  f"CRITICAL archives: {self._critical_count} | "
                  f"Inner files indexed: {self._inner_files_total}")
