"""
File Migrator for LitigationOS Daemon.
Moves heavy files from flash drives (D/F/G/H) to I: drive.
Implements safe migration with verification and rollback.

RULE: No hard deletions — originals moved to I:\\DEDUP_GRAVEYARD after verification.
"""
import hashlib
import json
import logging
import os
import shutil
import sqlite3
import time
from datetime import datetime
from typing import Optional

from .models import DriveRole
from .storage import StorageResolver, HEAVY_SIZE_THRESHOLD_MB

logger = logging.getLogger("daemon.migrator")

MIGRATION_DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_path TEXT NOT NULL,
    dest_path TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    source_drive TEXT,
    dest_drive TEXT,
    reason TEXT,
    started_at TEXT,
    completed_at TEXT,
    error TEXT,
    verified INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_mig_status ON migrations(status);
CREATE INDEX IF NOT EXISTS idx_mig_source ON migrations(source_path);
"""


class FileMigrator:
    """Safe file migration engine — moves heavy files to appropriate drives."""

    def __init__(self, storage: StorageResolver, db_path: str):
        self.storage = storage
        self.db_path = db_path
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=60)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=60000")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._conn()
        conn.executescript(MIGRATION_DB_SCHEMA)
        conn.commit()
        conn.close()

    def scan_candidates(self, min_size_mb: float = None) -> list[dict]:
        """Find files on flash drives that should be on heavy storage."""
        threshold = min_size_mb or HEAVY_SIZE_THRESHOLD_MB
        return self.storage.find_heavy_files_on_flash(min_size_mb=threshold)

    def migrate_file(self, source_path: str, reason: str = "size_threshold",
                     dest_subdir: str = None) -> dict:
        """Safely migrate a single file to heavy storage.

        Steps:
        1. Hash source file (SHA-256)
        2. Determine destination path
        3. Copy to destination
        4. Verify destination hash matches
        5. Log migration in DB
        6. Do NOT delete source (append-only evidence rule)

        Returns dict with migration result.
        """
        result = {
            "source": source_path,
            "success": False,
            "dest": None,
            "error": None,
        }

        if not os.path.isfile(source_path):
            result["error"] = "Source file not found"
            return result

        size = os.path.getsize(source_path)
        source_hash = self._hash_file(source_path)

        # Determine destination
        dest_path = self.storage.resolve_path(
            source_path,
            target_subdir=dest_subdir or "MIGRATED"
        )
        dest_dir = os.path.dirname(dest_path)

        # Ensure dest directory exists
        os.makedirs(dest_dir, exist_ok=True)

        # Handle name collision
        if os.path.exists(dest_path):
            base, ext = os.path.splitext(dest_path)
            dest_path = f"{base}_{source_hash[:8]}{ext}"

        # Log pending migration
        conn = self._conn()
        cursor = conn.execute(
            "INSERT INTO migrations (source_path, dest_path, size_bytes, sha256, "
            "status, source_drive, dest_drive, reason, started_at) "
            "VALUES (?, ?, ?, ?, 'in_progress', ?, ?, ?, ?)",
            (source_path, dest_path, size, source_hash,
             os.path.splitdrive(source_path)[0],
             os.path.splitdrive(dest_path)[0],
             reason, datetime.utcnow().isoformat())
        )
        mig_id = cursor.lastrowid
        conn.commit()

        try:
            # Copy file
            shutil.copy2(source_path, dest_path)

            # Verify
            dest_hash = self._hash_file(dest_path)
            if dest_hash != source_hash:
                # Hash mismatch — rollback
                os.remove(dest_path)
                conn.execute(
                    "UPDATE migrations SET status='failed', error='Hash mismatch after copy', "
                    "completed_at=? WHERE id=?",
                    (datetime.utcnow().isoformat(), mig_id)
                )
                conn.commit()
                conn.close()
                result["error"] = "Hash mismatch after copy — rolled back"
                return result

            # Mark verified
            conn.execute(
                "UPDATE migrations SET status='completed', verified=1, completed_at=? WHERE id=?",
                (datetime.utcnow().isoformat(), mig_id)
            )
            conn.commit()

            result["success"] = True
            result["dest"] = dest_path
            result["size_bytes"] = size
            result["sha256"] = source_hash

            logger.info(
                f"Migrated: {os.path.basename(source_path)} "
                f"({size / (1024*1024):.1f} MB) → {dest_path}"
            )

        except Exception as e:
            conn.execute(
                "UPDATE migrations SET status='failed', error=?, completed_at=? WHERE id=?",
                (str(e), datetime.utcnow().isoformat(), mig_id)
            )
            conn.commit()
            result["error"] = str(e)
            logger.error(f"Migration failed: {source_path} → {e}")

        conn.close()
        return result

    def batch_migrate(self, max_files: int = 50, min_size_mb: float = None,
                      dry_run: bool = False) -> dict:
        """Migrate batch of heavy files from flash drives.

        Returns summary with counts and total bytes moved.
        """
        candidates = self.scan_candidates(min_size_mb)

        summary = {
            "candidates_found": len(candidates),
            "migrated": 0,
            "failed": 0,
            "skipped": 0,
            "total_bytes": 0,
            "dry_run": dry_run,
            "details": [],
        }

        for i, candidate in enumerate(candidates[:max_files]):
            if dry_run:
                summary["details"].append({
                    "file": candidate["path"],
                    "size_mb": candidate["size_mb"],
                    "action": "would_migrate",
                })
                summary["skipped"] += 1
                continue

            result = self.migrate_file(
                candidate["path"],
                reason=f"flash_drive_heavy_{candidate['size_mb']:.0f}MB"
            )

            if result["success"]:
                summary["migrated"] += 1
                summary["total_bytes"] += result.get("size_bytes", 0)
            else:
                summary["failed"] += 1

            summary["details"].append(result)

        logger.info(
            f"Batch migration: {summary['migrated']} migrated, "
            f"{summary['failed']} failed, {summary['skipped']} skipped"
        )
        return summary

    def get_migration_history(self, limit: int = 100) -> list[dict]:
        """Get recent migration history."""
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM migrations ORDER BY started_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_migration_stats(self) -> dict:
        """Get migration statistics."""
        conn = self._conn()
        row = conn.execute("""
            SELECT
                (SELECT COUNT(*) FROM migrations) as total,
                (SELECT COUNT(*) FROM migrations WHERE status='completed') as completed,
                (SELECT COUNT(*) FROM migrations WHERE status='failed') as failed,
                (SELECT COALESCE(SUM(size_bytes), 0) FROM migrations WHERE status='completed') as bytes_moved,
                (SELECT COUNT(*) FROM migrations WHERE verified=1) as verified
        """).fetchone()
        conn.close()
        return dict(row) if row else {}

    @staticmethod
    def _hash_file(path: str) -> str:
        """SHA-256 hash of file."""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
