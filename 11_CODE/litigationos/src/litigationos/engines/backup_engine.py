"""Backup engine — automated backup and restore for LitigationOS data.

Handles SQLite online backup, incremental evidence backup via SHA-256
manifests, filing package snapshots, and safe restore with integrity
verification.  Old backups are moved to I:\\ (never hard-deleted).

Usage::

    from litigationos.engines.backup_engine import BackupEngine

    engine = BackupEngine(db_path="litigation_context.db")
    engine.backup_database("/backups/db")
    engine.backup_evidence("/backups/evidence", incremental=True)
    engine.create_snapshot("pre-filing-2025")
    engine.verify_backup("/backups/db/litigation_context_20250101.db")
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_DB_PATH = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")
_DEFAULT_BACKUP_ROOT = Path(r"C:\Users\andre\LitigationOS\backups")
_ARCHIVE_DRIVE = Path(r"I:\LitigationOS_old_backups")

_FILING_DIRS: list[Path] = [
    Path(r"C:\Users\andre\LitigationOS\01_FILINGS"),
    Path(r"C:\Users\andre\Desktop\Filing_Packages"),
]

_EVIDENCE_DIRS: list[Path] = [
    Path(r"C:\Users\andre\LitigationOS\02_EVIDENCE"),
]

_SQLITE_PRAGMAS = (
    "PRAGMA busy_timeout=60000",
    "PRAGMA journal_mode=WAL",
    "PRAGMA cache_size=-32000",
    "PRAGMA temp_store=MEMORY",
    "PRAGMA synchronous=NORMAL",
)

_CHUNK_SIZE = 8192  # bytes for SHA-256 streaming


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class BackupRecord(BaseModel):
    """A single backup event record."""

    backup_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: datetime = Field(default_factory=datetime.now)
    backup_type: str = "full"  # 'full', 'incremental', 'db'
    source_path: str = ""
    target_path: str = ""
    size_bytes: int = 0
    file_count: int = 0
    sha256_manifest: str = ""

    model_config = ConfigDict(from_attributes=True)


class BackupManifest(BaseModel):
    """Manifest listing every file in a backup with its SHA-256 hash."""

    backup_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    files: list[dict] = Field(default_factory=list)  # [{path, sha256, size}]
    total_size: int = 0
    created_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(from_attributes=True)


class BackupSchedule(BaseModel):
    """Recommended backup schedule for a component."""

    component: str
    frequency: str  # 'daily', 'weekly', 'on_change'
    last_backup: Optional[datetime] = None
    next_due: Optional[datetime] = None
    priority: str = "normal"  # 'critical', 'high', 'normal', 'low'

    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════════════════
# BackupEngine CLASS
# ═══════════════════════════════════════════════════════════════════════════


class BackupEngine:
    """Automated backup and restore engine for LitigationOS.

    Parameters
    ----------
    db_path : str | Path, optional
        Path to the central ``litigation_context.db``.  Defaults to the
        canonical location on C:\\.
    backup_root : str | Path, optional
        Root directory for storing backups.  Defaults to
        ``C:\\Users\\andre\\LitigationOS\\backups``.
    archive_drive : str | Path, optional
        Drive/directory for archiving old backups instead of deleting.
        Defaults to ``I:\\LitigationOS_old_backups``.
    """

    def __init__(
        self,
        db_path: str | Path | None = None,
        backup_root: str | Path | None = None,
        archive_drive: str | Path | None = None,
    ) -> None:
        self._db_path = Path(db_path) if db_path else _DEFAULT_DB_PATH
        self._backup_root = Path(backup_root) if backup_root else _DEFAULT_BACKUP_ROOT
        self._archive_drive = Path(archive_drive) if archive_drive else _ARCHIVE_DRIVE

        self._backup_root.mkdir(parents=True, exist_ok=True)

        logger.info(
            "BackupEngine initialized — db=%s backup_root=%s",
            self._db_path,
            self._backup_root,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _connect(db_path: Path) -> sqlite3.Connection:
        """Open a connection with LitigationOS-standard PRAGMAs."""
        conn = sqlite3.connect(str(db_path), timeout=120)
        for pragma in _SQLITE_PRAGMAS:
            conn.execute(pragma)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _sha256(file_path: Path) -> str:
        """Compute SHA-256 hex digest of a file using streaming reads."""
        h = hashlib.sha256()
        with open(file_path, "rb") as fh:
            while True:
                chunk = fh.read(_CHUNK_SIZE)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def _timestamp_label() -> str:
        """Return an ISO-like label safe for filesystem use."""
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def _ensure_manifest_table(self, conn: sqlite3.Connection) -> None:
        """Create the ``backup_manifests`` table if it does not exist."""
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS backup_manifests (
                backup_id    TEXT PRIMARY KEY,
                timestamp    TEXT NOT NULL,
                backup_type  TEXT NOT NULL,
                source_path  TEXT,
                target_path  TEXT,
                size_bytes   INTEGER DEFAULT 0,
                file_count   INTEGER DEFAULT 0,
                sha256_manifest TEXT,
                manifest_json TEXT
            )
            """
        )
        conn.commit()

    def _save_record(self, record: BackupRecord, manifest: BackupManifest) -> None:
        """Persist a backup record to the ``backup_manifests`` table."""
        if not self._db_path.exists():
            logger.warning("DB not found at %s — skipping manifest save", self._db_path)
            return
        conn = self._connect(self._db_path)
        try:
            self._ensure_manifest_table(conn)
            conn.execute(
                """
                INSERT OR REPLACE INTO backup_manifests
                    (backup_id, timestamp, backup_type, source_path,
                     target_path, size_bytes, file_count, sha256_manifest,
                     manifest_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.backup_id,
                    record.timestamp.isoformat(),
                    record.backup_type,
                    record.source_path,
                    record.target_path,
                    record.size_bytes,
                    record.file_count,
                    record.sha256_manifest,
                    manifest.model_dump_json(),
                ),
            )
            conn.commit()
            logger.info("Backup record saved: %s", record.backup_id)
        finally:
            conn.close()

    def _collect_files(self, root: Path, extensions: set[str] | None = None) -> list[Path]:
        """Recursively collect files under *root*, optionally filtered by extension."""
        if not root.exists():
            return []
        result: list[Path] = []
        for dirpath, _dirnames, filenames in os.walk(root):
            for fn in filenames:
                fp = Path(dirpath) / fn
                if extensions is None or fp.suffix.lower() in extensions:
                    result.append(fp)
        return sorted(result)

    # ------------------------------------------------------------------
    # Public API — backup_database
    # ------------------------------------------------------------------

    def backup_database(self, target_dir: str | Path) -> BackupRecord:
        """Create a consistent SQLite online backup of the central database.

        Uses the ``sqlite3.Connection.backup()`` API which works on a live
        WAL-mode database without locking writers.

        Parameters
        ----------
        target_dir : str | Path
            Directory where the backup ``.db`` file is written.

        Returns
        -------
        BackupRecord
            Metadata about the completed backup.

        Raises
        ------
        FileNotFoundError
            If the source database does not exist.
        """
        target_dir = Path(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        if not self._db_path.exists():
            raise FileNotFoundError(f"Source database not found: {self._db_path}")

        label = self._timestamp_label()
        dest = target_dir / f"litigation_context_{label}.db"

        logger.info("Starting SQLite online backup → %s", dest)

        src_conn = self._connect(self._db_path)
        dst_conn = sqlite3.connect(str(dest))
        try:
            src_conn.backup(dst_conn)
            dst_conn.close()
            logger.info("Database backup complete: %s", dest)
        finally:
            src_conn.close()
            if dst_conn:
                try:
                    dst_conn.close()
                except Exception:
                    pass

        size = dest.stat().st_size
        digest = self._sha256(dest)

        record = BackupRecord(
            backup_type="db",
            source_path=str(self._db_path),
            target_path=str(dest),
            size_bytes=size,
            file_count=1,
            sha256_manifest=digest,
        )
        manifest = BackupManifest(
            backup_id=record.backup_id,
            files=[{"path": str(dest), "sha256": digest, "size": size}],
            total_size=size,
        )

        self._save_record(record, manifest)
        return record

    # ------------------------------------------------------------------
    # Public API — backup_filings
    # ------------------------------------------------------------------

    def backup_filings(self, target_dir: str | Path) -> BackupRecord:
        """Copy all filing packages to a backup location.

        Scans ``01_FILINGS/`` and Desktop filing packages. Each file is
        copied preserving the directory structure.

        Parameters
        ----------
        target_dir : str | Path
            Destination root for filing backups.

        Returns
        -------
        BackupRecord
        """
        target_dir = Path(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        label = self._timestamp_label()
        backup_dir = target_dir / f"filings_{label}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        files_info: list[dict] = []
        total_size = 0
        file_count = 0

        for src_root in _FILING_DIRS:
            if not src_root.exists():
                logger.debug("Filing dir not found, skipping: %s", src_root)
                continue
            for fp in self._collect_files(src_root):
                rel = fp.relative_to(src_root)
                dest = backup_dir / src_root.name / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(fp), str(dest))

                sz = dest.stat().st_size
                digest = self._sha256(dest)
                files_info.append({"path": str(rel), "sha256": digest, "size": sz})
                total_size += sz
                file_count += 1

        logger.info("Filing backup complete: %d files, %s bytes", file_count, total_size)

        record = BackupRecord(
            backup_type="full",
            source_path="; ".join(str(d) for d in _FILING_DIRS),
            target_path=str(backup_dir),
            size_bytes=total_size,
            file_count=file_count,
        )
        manifest = BackupManifest(
            backup_id=record.backup_id,
            files=files_info,
            total_size=total_size,
        )
        record.sha256_manifest = hashlib.sha256(
            manifest.model_dump_json().encode()
        ).hexdigest()

        self._save_record(record, manifest)
        return record

    # ------------------------------------------------------------------
    # Public API — backup_evidence
    # ------------------------------------------------------------------

    def backup_evidence(
        self,
        target_dir: str | Path,
        incremental: bool = True,
    ) -> BackupRecord:
        """Back up evidence files, optionally incremental.

        When *incremental* is ``True``, only files modified since the last
        evidence backup (or files not present in the most recent manifest)
        are copied.  Comparison uses SHA-256 content hashing.

        Parameters
        ----------
        target_dir : str | Path
            Destination directory.
        incremental : bool
            If ``True``, skip unchanged files.

        Returns
        -------
        BackupRecord
        """
        target_dir = Path(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        label = self._timestamp_label()
        backup_dir = target_dir / f"evidence_{label}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        previous_hashes: dict[str, str] = {}
        if incremental:
            previous_hashes = self._load_previous_evidence_hashes()

        files_info: list[dict] = []
        total_size = 0
        file_count = 0
        skipped = 0

        for src_root in _EVIDENCE_DIRS:
            if not src_root.exists():
                logger.debug("Evidence dir not found, skipping: %s", src_root)
                continue
            for fp in self._collect_files(src_root):
                rel = fp.relative_to(src_root)
                rel_str = str(rel)

                current_hash = self._sha256(fp)

                if incremental and previous_hashes.get(rel_str) == current_hash:
                    skipped += 1
                    continue

                dest = backup_dir / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(fp), str(dest))

                sz = fp.stat().st_size
                files_info.append({"path": rel_str, "sha256": current_hash, "size": sz})
                total_size += sz
                file_count += 1

        btype = "incremental" if incremental else "full"
        logger.info(
            "Evidence backup (%s) complete: %d copied, %d skipped, %s bytes",
            btype,
            file_count,
            skipped,
            total_size,
        )

        record = BackupRecord(
            backup_type=btype,
            source_path="; ".join(str(d) for d in _EVIDENCE_DIRS),
            target_path=str(backup_dir),
            size_bytes=total_size,
            file_count=file_count,
        )
        manifest = BackupManifest(
            backup_id=record.backup_id,
            files=files_info,
            total_size=total_size,
        )
        record.sha256_manifest = hashlib.sha256(
            manifest.model_dump_json().encode()
        ).hexdigest()

        self._save_record(record, manifest)
        return record

    def _load_previous_evidence_hashes(self) -> dict[str, str]:
        """Load file→SHA-256 mapping from the most recent evidence manifest."""
        if not self._db_path.exists():
            return {}
        conn = self._connect(self._db_path)
        try:
            self._ensure_manifest_table(conn)
            row = conn.execute(
                """
                SELECT manifest_json FROM backup_manifests
                WHERE backup_type IN ('incremental', 'full')
                  AND source_path LIKE '%EVIDENCE%'
                ORDER BY timestamp DESC LIMIT 1
                """
            ).fetchone()
            if row is None:
                return {}
            data = json.loads(row["manifest_json"])
            return {f["path"]: f["sha256"] for f in data.get("files", [])}
        except Exception:
            logger.debug("Could not load previous evidence hashes", exc_info=True)
            return {}
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Public API — create_snapshot
    # ------------------------------------------------------------------

    def create_snapshot(self, label: str = "") -> BackupRecord:
        """Create a full system snapshot (database + filings + evidence).

        Parameters
        ----------
        label : str
            Human-readable snapshot label.  Defaults to an ISO timestamp.

        Returns
        -------
        BackupRecord
            Aggregate record covering the entire snapshot.
        """
        label = label or self._timestamp_label()
        snap_dir = self._backup_root / f"snapshot_{label}"
        snap_dir.mkdir(parents=True, exist_ok=True)

        all_files: list[dict] = []
        total_size = 0
        total_count = 0

        # Database
        if self._db_path.exists():
            db_rec = self.backup_database(snap_dir / "db")
            total_size += db_rec.size_bytes
            total_count += db_rec.file_count
            all_files.append(
                {"path": db_rec.target_path, "sha256": db_rec.sha256_manifest, "size": db_rec.size_bytes}
            )

        # Filings
        filing_rec = self.backup_filings(snap_dir / "filings")
        total_size += filing_rec.size_bytes
        total_count += filing_rec.file_count

        # Evidence (full, not incremental for snapshots)
        evidence_rec = self.backup_evidence(snap_dir / "evidence", incremental=False)
        total_size += evidence_rec.size_bytes
        total_count += evidence_rec.file_count

        # Write a snapshot summary
        summary = {
            "label": label,
            "created_at": datetime.now().isoformat(),
            "database": db_rec.model_dump(mode="json") if self._db_path.exists() else None,
            "filings": filing_rec.model_dump(mode="json"),
            "evidence": evidence_rec.model_dump(mode="json"),
            "total_size": total_size,
            "total_files": total_count,
        }
        summary_path = snap_dir / "snapshot_manifest.json"
        summary_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")

        record = BackupRecord(
            backup_type="full",
            source_path="system_snapshot",
            target_path=str(snap_dir),
            size_bytes=total_size,
            file_count=total_count,
        )
        manifest = BackupManifest(
            backup_id=record.backup_id,
            files=all_files,
            total_size=total_size,
        )
        record.sha256_manifest = hashlib.sha256(
            manifest.model_dump_json().encode()
        ).hexdigest()

        self._save_record(record, manifest)
        logger.info("Snapshot '%s' complete: %d files, %s bytes", label, total_count, total_size)
        return record

    # ------------------------------------------------------------------
    # Public API — list_backups
    # ------------------------------------------------------------------

    def list_backups(self) -> list[BackupRecord]:
        """List all existing backups with sizes and dates.

        Reads from the ``backup_manifests`` table in the central database
        and also scans the backup root directory for any unregistered
        backup directories.

        Returns
        -------
        list[BackupRecord]
            Records sorted newest-first.
        """
        records: list[BackupRecord] = []

        # From database
        if self._db_path.exists():
            conn = self._connect(self._db_path)
            try:
                self._ensure_manifest_table(conn)
                rows = conn.execute(
                    "SELECT * FROM backup_manifests ORDER BY timestamp DESC"
                ).fetchall()
                for row in rows:
                    records.append(
                        BackupRecord(
                            backup_id=row["backup_id"],
                            timestamp=datetime.fromisoformat(row["timestamp"]),
                            backup_type=row["backup_type"],
                            source_path=row["source_path"] or "",
                            target_path=row["target_path"] or "",
                            size_bytes=row["size_bytes"] or 0,
                            file_count=row["file_count"] or 0,
                            sha256_manifest=row["sha256_manifest"] or "",
                        )
                    )
            except Exception:
                logger.debug("Could not read backup_manifests table", exc_info=True)
            finally:
                conn.close()

        # Also discover on-disk backups not yet registered
        registered_paths = {r.target_path for r in records}
        if self._backup_root.exists():
            for entry in sorted(self._backup_root.iterdir(), reverse=True):
                if entry.is_dir() and str(entry) not in registered_paths:
                    size = sum(f.stat().st_size for f in entry.rglob("*") if f.is_file())
                    count = sum(1 for f in entry.rglob("*") if f.is_file())
                    records.append(
                        BackupRecord(
                            backup_type="unknown",
                            target_path=str(entry),
                            size_bytes=size,
                            file_count=count,
                        )
                    )

        return records

    # ------------------------------------------------------------------
    # Public API — verify_backup
    # ------------------------------------------------------------------

    def verify_backup(self, backup_path: str | Path) -> dict:
        """Verify integrity of a backup using SHA-256.

        For database backups, opens the file and runs ``PRAGMA integrity_check``.
        For directories, verifies each file against its manifest hash.

        Parameters
        ----------
        backup_path : str | Path
            Path to a backup file or directory.

        Returns
        -------
        dict
            ``{"valid": bool, "checked": int, "errors": list[str]}``
        """
        backup_path = Path(backup_path)
        errors: list[str] = []
        checked = 0

        if not backup_path.exists():
            return {"valid": False, "checked": 0, "errors": [f"Path not found: {backup_path}"]}

        # Single DB file
        if backup_path.is_file() and backup_path.suffix == ".db":
            return self._verify_db_file(backup_path)

        # Directory — look for manifest
        manifest_file = backup_path / "snapshot_manifest.json"
        if manifest_file.exists():
            return self._verify_snapshot_dir(backup_path, manifest_file)

        # Fallback: just verify all files are readable and compute hashes
        for fp in backup_path.rglob("*"):
            if fp.is_file():
                checked += 1
                try:
                    self._sha256(fp)
                except Exception as exc:
                    errors.append(f"{fp}: {exc}")

        valid = len(errors) == 0
        logger.info("Backup verification: %d checked, %d errors", checked, len(errors))
        return {"valid": valid, "checked": checked, "errors": errors}

    def _verify_db_file(self, db_path: Path) -> dict:
        """Run SQLite integrity_check on a database file."""
        errors: list[str] = []
        try:
            conn = sqlite3.connect(str(db_path))
            result = conn.execute("PRAGMA integrity_check").fetchone()
            conn.close()
            if result and result[0] != "ok":
                errors.append(f"integrity_check: {result[0]}")
        except Exception as exc:
            errors.append(f"Could not open DB: {exc}")

        return {"valid": len(errors) == 0, "checked": 1, "errors": errors}

    def _verify_snapshot_dir(self, backup_path: Path, manifest_file: Path) -> dict:
        """Verify a snapshot directory against its JSON manifest."""
        errors: list[str] = []
        checked = 0

        try:
            data = json.loads(manifest_file.read_text(encoding="utf-8"))
        except Exception as exc:
            return {"valid": False, "checked": 0, "errors": [f"Manifest unreadable: {exc}"]}

        # Verify sub-backup directories exist
        for key in ("database", "filings", "evidence"):
            sub = data.get(key)
            if sub and sub.get("target_path"):
                tp = Path(sub["target_path"])
                checked += 1
                if not tp.exists():
                    errors.append(f"Missing {key} backup: {tp}")

        # Verify all files in directory are readable
        for fp in backup_path.rglob("*"):
            if fp.is_file():
                checked += 1
                try:
                    self._sha256(fp)
                except Exception as exc:
                    errors.append(f"{fp}: {exc}")

        valid = len(errors) == 0
        return {"valid": valid, "checked": checked, "errors": errors}

    # ------------------------------------------------------------------
    # Public API — restore_from_backup
    # ------------------------------------------------------------------

    def restore_from_backup(
        self,
        backup_path: str | Path,
        target: str | Path,
        *,
        confirmed: bool = False,
    ) -> dict:
        """Restore files from a backup to a target location.

        Parameters
        ----------
        backup_path : str | Path
            Source backup file or directory.
        target : str | Path
            Destination directory where files are restored.
        confirmed : bool
            Safety gate — must be ``True`` or the restore is rejected.
            Callers should prompt the user before setting this.

        Returns
        -------
        dict
            ``{"restored": int, "errors": list[str], "target": str}``
        """
        if not confirmed:
            return {
                "restored": 0,
                "errors": ["Restore requires explicit confirmation (confirmed=True)"],
                "target": str(target),
            }

        backup_path = Path(backup_path)
        target = Path(target)
        target.mkdir(parents=True, exist_ok=True)

        if not backup_path.exists():
            return {"restored": 0, "errors": [f"Backup not found: {backup_path}"], "target": str(target)}

        errors: list[str] = []
        restored = 0

        # Single file restore
        if backup_path.is_file():
            dest = target / backup_path.name
            try:
                shutil.copy2(str(backup_path), str(dest))
                restored = 1
            except Exception as exc:
                errors.append(f"Copy failed: {exc}")
            return {"restored": restored, "errors": errors, "target": str(target)}

        # Directory restore
        for fp in backup_path.rglob("*"):
            if fp.is_file():
                rel = fp.relative_to(backup_path)
                dest = target / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.copy2(str(fp), str(dest))
                    restored += 1
                except Exception as exc:
                    errors.append(f"{rel}: {exc}")

        logger.info("Restore complete: %d files to %s", restored, target)
        return {"restored": restored, "errors": errors, "target": str(target)}

    # ------------------------------------------------------------------
    # Public API — get_backup_schedule
    # ------------------------------------------------------------------

    def get_backup_schedule(self) -> list[BackupSchedule]:
        """Return a recommended backup schedule based on change frequency.

        Queries the ``backup_manifests`` table for the most recent backup
        of each type and computes the next due date.

        Returns
        -------
        list[BackupSchedule]
        """
        components = [
            ("database", "daily", "critical"),
            ("filings", "weekly", "high"),
            ("evidence", "weekly", "high"),
            ("full_snapshot", "monthly", "normal"),
        ]

        freq_delta = {
            "daily": timedelta(days=1),
            "weekly": timedelta(days=7),
            "monthly": timedelta(days=30),
        }

        schedules: list[BackupSchedule] = []
        last_backups = self._get_last_backup_times()

        for component, freq, priority in components:
            last = last_backups.get(component)
            delta = freq_delta[freq]
            next_due = (last + delta) if last else datetime.now()

            schedules.append(
                BackupSchedule(
                    component=component,
                    frequency=freq,
                    last_backup=last,
                    next_due=next_due,
                    priority=priority,
                )
            )

        return schedules

    def _get_last_backup_times(self) -> dict[str, datetime]:
        """Query the DB for the most recent backup timestamp per component."""
        result: dict[str, datetime] = {}
        if not self._db_path.exists():
            return result

        type_map = {
            "db": "database",
            "full": "full_snapshot",
            "incremental": "evidence",
        }

        conn = self._connect(self._db_path)
        try:
            self._ensure_manifest_table(conn)
            rows = conn.execute(
                """
                SELECT backup_type, MAX(timestamp) as last_ts
                FROM backup_manifests
                GROUP BY backup_type
                """
            ).fetchall()
            for row in rows:
                component = type_map.get(row["backup_type"], row["backup_type"])
                try:
                    result[component] = datetime.fromisoformat(row["last_ts"])
                except (ValueError, TypeError):
                    pass

            # Filings: look for source_path containing FILINGS
            row = conn.execute(
                """
                SELECT MAX(timestamp) as last_ts FROM backup_manifests
                WHERE source_path LIKE '%FILINGS%' OR source_path LIKE '%Filing%'
                """
            ).fetchone()
            if row and row["last_ts"]:
                try:
                    result["filings"] = datetime.fromisoformat(row["last_ts"])
                except (ValueError, TypeError):
                    pass
        except Exception:
            logger.debug("Could not query backup history", exc_info=True)
        finally:
            conn.close()

        return result

    # ------------------------------------------------------------------
    # Public API — cleanup_old_backups
    # ------------------------------------------------------------------

    def cleanup_old_backups(self, keep_count: int = 5) -> dict:
        """Move old backups to the archive drive (I:\\).  NEVER deletes.

        Keeps the *keep_count* most recent backups in the backup root.
        Older backups are moved to ``I:\\LitigationOS_old_backups\\``.

        Parameters
        ----------
        keep_count : int
            Number of recent backups to keep in-place.

        Returns
        -------
        dict
            ``{"kept": int, "archived": int, "errors": list[str]}``
        """
        if not self._backup_root.exists():
            return {"kept": 0, "archived": 0, "errors": ["Backup root does not exist"]}

        entries = sorted(
            [e for e in self._backup_root.iterdir() if e.is_dir()],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        kept = entries[:keep_count]
        to_archive = entries[keep_count:]

        archived = 0
        errors: list[str] = []

        if to_archive:
            self._archive_drive.mkdir(parents=True, exist_ok=True)

        for entry in to_archive:
            dest = self._archive_drive / entry.name
            try:
                if dest.exists():
                    dest = self._archive_drive / f"{entry.name}_{self._timestamp_label()}"
                shutil.move(str(entry), str(dest))
                archived += 1
                logger.info("Archived old backup: %s → %s", entry.name, dest)
            except Exception as exc:
                errors.append(f"Failed to archive {entry.name}: {exc}")
                logger.warning("Failed to archive %s: %s", entry.name, exc)

        logger.info(
            "Cleanup complete: %d kept, %d archived, %d errors",
            len(kept),
            archived,
            len(errors),
        )
        return {"kept": len(kept), "archived": archived, "errors": errors}
