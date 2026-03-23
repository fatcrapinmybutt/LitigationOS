"""Tests for the BackupEngine — automated backup and restore system.

Covers: database backup, filing backup, evidence backup (full + incremental),
snapshot creation, backup listing, integrity verification, restore with
confirmation gate, schedule generation, cleanup/archival, Pydantic models,
SHA-256 hashing, manifest persistence, and edge cases.

All tests use temporary directories — never touches production data.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from litigationos.engines.backup_engine import (
    BackupEngine,
    BackupManifest,
    BackupRecord,
    BackupSchedule,
    _SQLITE_PRAGMAS,
)


# ===================================================================
# Fixtures
# ===================================================================


@pytest.fixture
def fake_db(tmp_path: Path) -> Path:
    """Create a small SQLite database mimicking litigation_context.db."""
    db_path = tmp_path / "litigation_context.db"
    conn = sqlite3.connect(str(db_path))
    for pragma in _SQLITE_PRAGMAS:
        conn.execute(pragma)
    conn.execute("CREATE TABLE cases (id INTEGER PRIMARY KEY, title TEXT)")
    conn.execute("INSERT INTO cases (title) VALUES ('Pigors v. Watson')")
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def filing_dir(tmp_path: Path) -> Path:
    """Create a fake filing directory with sample files."""
    fdir = tmp_path / "01_FILINGS"
    fdir.mkdir()
    (fdir / "motion_to_compel.pdf").write_bytes(b"PDF-motion-content-12345")
    (fdir / "brief.docx").write_bytes(b"DOCX-brief-content-67890")
    sub = fdir / "exhibits"
    sub.mkdir()
    (sub / "exhibit_A.pdf").write_bytes(b"exhibit-A-data")
    return fdir


@pytest.fixture
def evidence_dir(tmp_path: Path) -> Path:
    """Create a fake evidence directory with sample files."""
    edir = tmp_path / "02_EVIDENCE"
    edir.mkdir()
    (edir / "screenshot_01.png").write_bytes(b"PNG-evidence-screenshot")
    (edir / "bank_statement.pdf").write_bytes(b"PDF-bank-statement-data")
    sub = edir / "texts"
    sub.mkdir()
    (sub / "messages.txt").write_text("Text message export 2024", encoding="utf-8")
    return edir


@pytest.fixture
def engine(tmp_path: Path, fake_db: Path, monkeypatch: pytest.MonkeyPatch) -> BackupEngine:
    """Create a BackupEngine wired to temp paths."""
    backup_root = tmp_path / "backups"
    archive = tmp_path / "I_drive_archive"

    import litigationos.engines.backup_engine as mod

    monkeypatch.setattr(mod, "_FILING_DIRS", [tmp_path / "01_FILINGS"])
    monkeypatch.setattr(mod, "_EVIDENCE_DIRS", [tmp_path / "02_EVIDENCE"])

    return BackupEngine(
        db_path=fake_db,
        backup_root=backup_root,
        archive_drive=archive,
    )


# ===================================================================
# Pydantic Model Tests
# ===================================================================


class TestPydanticModels:
    """Validate Pydantic model creation and serialization."""

    def test_backup_record_defaults(self) -> None:
        rec = BackupRecord()
        assert rec.backup_id  # auto-generated
        assert rec.backup_type == "full"
        assert rec.size_bytes == 0
        assert isinstance(rec.timestamp, datetime)

    def test_backup_record_custom(self) -> None:
        rec = BackupRecord(
            backup_id="abc123",
            backup_type="db",
            source_path="/src",
            target_path="/dst",
            size_bytes=1024,
            file_count=3,
            sha256_manifest="deadbeef",
        )
        assert rec.backup_id == "abc123"
        assert rec.backup_type == "db"
        assert rec.file_count == 3
        dumped = rec.model_dump()
        assert dumped["size_bytes"] == 1024

    def test_backup_manifest_files(self) -> None:
        manifest = BackupManifest(
            files=[
                {"path": "a.txt", "sha256": "aaa", "size": 100},
                {"path": "b.txt", "sha256": "bbb", "size": 200},
            ],
            total_size=300,
        )
        assert len(manifest.files) == 2
        assert manifest.total_size == 300
        jstr = manifest.model_dump_json()
        assert "aaa" in jstr

    def test_backup_schedule_creation(self) -> None:
        sched = BackupSchedule(
            component="database",
            frequency="daily",
            priority="critical",
        )
        assert sched.component == "database"
        assert sched.last_backup is None
        assert sched.next_due is None


# ===================================================================
# Database Backup Tests
# ===================================================================


class TestBackupDatabase:
    """Test SQLite online backup functionality."""

    def test_backup_database_creates_file(self, engine: BackupEngine, tmp_path: Path) -> None:
        target = tmp_path / "db_backup"
        rec = engine.backup_database(target)

        assert rec.backup_type == "db"
        assert rec.file_count == 1
        assert rec.size_bytes > 0
        assert rec.sha256_manifest
        assert Path(rec.target_path).exists()

    def test_backup_database_is_valid_sqlite(self, engine: BackupEngine, tmp_path: Path) -> None:
        target = tmp_path / "db_backup"
        rec = engine.backup_database(target)

        conn = sqlite3.connect(rec.target_path)
        row = conn.execute("SELECT title FROM cases").fetchone()
        conn.close()
        assert row[0] == "Pigors v. Watson"

    def test_backup_database_missing_source_raises(self, tmp_path: Path) -> None:
        eng = BackupEngine(
            db_path=tmp_path / "nonexistent.db",
            backup_root=tmp_path / "backups",
        )
        with pytest.raises(FileNotFoundError):
            eng.backup_database(tmp_path / "out")


# ===================================================================
# Filing Backup Tests
# ===================================================================


class TestBackupFilings:
    """Test filing package backup."""

    def test_backup_filings_copies_all(
        self, engine: BackupEngine, filing_dir: Path, tmp_path: Path
    ) -> None:
        target = tmp_path / "filing_backup"
        rec = engine.backup_filings(target)

        assert rec.file_count == 3  # motion, brief, exhibit_A
        assert rec.size_bytes > 0
        assert rec.backup_type == "full"

    def test_backup_filings_preserves_content(
        self, engine: BackupEngine, filing_dir: Path, tmp_path: Path
    ) -> None:
        target = tmp_path / "filing_backup"
        rec = engine.backup_filings(target)

        backup_dir = Path(rec.target_path)
        found_files = list(backup_dir.rglob("*.pdf"))
        assert len(found_files) >= 1

        # Verify a file's content survived the copy
        motion_files = [f for f in found_files if "motion" in f.name]
        assert len(motion_files) == 1
        assert motion_files[0].read_bytes() == b"PDF-motion-content-12345"

    def test_backup_filings_empty_dir(self, tmp_path: Path) -> None:
        """Engine handles missing filing directories gracefully."""
        eng = BackupEngine(
            db_path=tmp_path / "test.db",
            backup_root=tmp_path / "backups",
        )
        import litigationos.engines.backup_engine as mod

        original = mod._FILING_DIRS
        mod._FILING_DIRS = [tmp_path / "nonexistent_filings"]
        try:
            rec = eng.backup_filings(tmp_path / "out")
            assert rec.file_count == 0
        finally:
            mod._FILING_DIRS = original


# ===================================================================
# Evidence Backup Tests
# ===================================================================


class TestBackupEvidence:
    """Test incremental and full evidence backup."""

    def test_full_evidence_backup(
        self, engine: BackupEngine, evidence_dir: Path, tmp_path: Path
    ) -> None:
        target = tmp_path / "evidence_backup"
        rec = engine.backup_evidence(target, incremental=False)

        assert rec.file_count == 3  # screenshot, bank_statement, messages
        assert rec.backup_type == "full"
        assert rec.size_bytes > 0

    def test_incremental_skips_unchanged(
        self, engine: BackupEngine, evidence_dir: Path, tmp_path: Path
    ) -> None:
        target = tmp_path / "evidence_backup"

        # First backup — all files copied
        rec1 = engine.backup_evidence(target, incremental=False)
        assert rec1.file_count == 3

        # Second backup (incremental) — nothing changed, so 0 copied
        rec2 = engine.backup_evidence(target, incremental=True)
        assert rec2.file_count == 0

    def test_incremental_detects_new_file(
        self, engine: BackupEngine, evidence_dir: Path, tmp_path: Path
    ) -> None:
        target = tmp_path / "evidence_backup"

        rec1 = engine.backup_evidence(target, incremental=False)
        assert rec1.file_count == 3

        # Add a new file
        (evidence_dir / "new_doc.pdf").write_bytes(b"new-evidence-data")

        rec2 = engine.backup_evidence(target, incremental=True)
        assert rec2.file_count == 1  # only the new file


# ===================================================================
# Snapshot Tests
# ===================================================================


class TestCreateSnapshot:
    """Test full system snapshot creation."""

    def test_snapshot_creates_manifest(
        self,
        engine: BackupEngine,
        filing_dir: Path,
        evidence_dir: Path,
        tmp_path: Path,
    ) -> None:
        rec = engine.create_snapshot("test_snap")
        snap_dir = Path(rec.target_path)

        assert snap_dir.exists()
        manifest = snap_dir / "snapshot_manifest.json"
        assert manifest.exists()

        data = json.loads(manifest.read_text(encoding="utf-8"))
        assert data["label"] == "test_snap"
        assert data["total_files"] > 0

    def test_snapshot_includes_all_components(
        self,
        engine: BackupEngine,
        filing_dir: Path,
        evidence_dir: Path,
        tmp_path: Path,
    ) -> None:
        rec = engine.create_snapshot("full")
        snap_dir = Path(rec.target_path)

        assert (snap_dir / "db").exists()
        assert (snap_dir / "filings").exists()
        assert (snap_dir / "evidence").exists()


# ===================================================================
# Verify Backup Tests
# ===================================================================


class TestVerifyBackup:
    """Test backup integrity verification."""

    def test_verify_valid_db(self, engine: BackupEngine, tmp_path: Path) -> None:
        target = tmp_path / "db_backup"
        rec = engine.backup_database(target)

        result = engine.verify_backup(rec.target_path)
        assert result["valid"] is True
        assert result["checked"] == 1
        assert result["errors"] == []

    def test_verify_nonexistent_path(self, engine: BackupEngine) -> None:
        result = engine.verify_backup("/nonexistent/path")
        assert result["valid"] is False
        assert len(result["errors"]) == 1

    def test_verify_directory_backup(
        self,
        engine: BackupEngine,
        filing_dir: Path,
        evidence_dir: Path,
        tmp_path: Path,
    ) -> None:
        rec = engine.create_snapshot("verify_test")
        result = engine.verify_backup(rec.target_path)
        assert result["valid"] is True
        assert result["checked"] > 0


# ===================================================================
# Restore Tests
# ===================================================================


class TestRestoreFromBackup:
    """Test restore with confirmation gate."""

    def test_restore_requires_confirmation(self, engine: BackupEngine, tmp_path: Path) -> None:
        target = tmp_path / "db_backup"
        rec = engine.backup_database(target)

        result = engine.restore_from_backup(rec.target_path, tmp_path / "restore_out")
        assert result["restored"] == 0
        assert "confirmation" in result["errors"][0].lower()

    def test_restore_single_file(self, engine: BackupEngine, tmp_path: Path) -> None:
        target = tmp_path / "db_backup"
        rec = engine.backup_database(target)

        restore_dir = tmp_path / "restore_out"
        result = engine.restore_from_backup(
            rec.target_path, restore_dir, confirmed=True
        )
        assert result["restored"] == 1
        assert (restore_dir / Path(rec.target_path).name).exists()

    def test_restore_directory(
        self,
        engine: BackupEngine,
        filing_dir: Path,
        tmp_path: Path,
    ) -> None:
        target = tmp_path / "filing_backup"
        rec = engine.backup_filings(target)

        restore_dir = tmp_path / "restore_filings"
        result = engine.restore_from_backup(
            rec.target_path, restore_dir, confirmed=True
        )
        assert result["restored"] == rec.file_count
        assert result["errors"] == []


# ===================================================================
# List and Schedule Tests
# ===================================================================


class TestListAndSchedule:
    """Test backup listing and schedule generation."""

    def test_list_backups_returns_records(self, engine: BackupEngine, tmp_path: Path) -> None:
        engine.backup_database(tmp_path / "db1")
        engine.backup_database(tmp_path / "db2")

        backups = engine.list_backups()
        assert len(backups) >= 2

    def test_get_backup_schedule_returns_all_components(self, engine: BackupEngine) -> None:
        schedules = engine.get_backup_schedule()
        components = {s.component for s in schedules}
        assert "database" in components
        assert "filings" in components
        assert "evidence" in components
        assert "full_snapshot" in components

    def test_schedule_priorities(self, engine: BackupEngine) -> None:
        schedules = engine.get_backup_schedule()
        db_sched = next(s for s in schedules if s.component == "database")
        assert db_sched.priority == "critical"
        assert db_sched.frequency == "daily"


# ===================================================================
# Cleanup Tests
# ===================================================================


class TestCleanupOldBackups:
    """Test old backup archival (move to I:\\, never delete)."""

    def test_cleanup_moves_old_backups(self, engine: BackupEngine, tmp_path: Path) -> None:
        # Create 7 backup directories
        for i in range(7):
            d = engine._backup_root / f"backup_{i:03d}"
            d.mkdir(parents=True)
            (d / "data.txt").write_text(f"backup {i}", encoding="utf-8")
            # Stagger modification times
            import time

            time.sleep(0.05)

        result = engine.cleanup_old_backups(keep_count=3)
        assert result["kept"] == 3
        assert result["archived"] == 4
        assert result["errors"] == []

        # Verify old backups moved to archive, not deleted
        remaining = list(engine._backup_root.iterdir())
        assert len(remaining) == 3

        archived = list(engine._archive_drive.iterdir())
        assert len(archived) == 4

    def test_cleanup_with_fewer_than_keep(self, engine: BackupEngine) -> None:
        # Only 2 backups exist, keep_count=5
        for i in range(2):
            d = engine._backup_root / f"small_backup_{i}"
            d.mkdir()
            (d / "f.txt").write_text("x", encoding="utf-8")

        result = engine.cleanup_old_backups(keep_count=5)
        assert result["kept"] == 2
        assert result["archived"] == 0


# ===================================================================
# SHA-256 Hashing Tests
# ===================================================================


class TestSHA256:
    """Test the internal SHA-256 utility."""

    def test_sha256_deterministic(self, tmp_path: Path) -> None:
        f = tmp_path / "test.bin"
        f.write_bytes(b"hello world")
        h1 = BackupEngine._sha256(f)
        h2 = BackupEngine._sha256(f)
        assert h1 == h2
        assert len(h1) == 64  # hex digest length

    def test_sha256_different_content(self, tmp_path: Path) -> None:
        f1 = tmp_path / "a.bin"
        f2 = tmp_path / "b.bin"
        f1.write_bytes(b"content A")
        f2.write_bytes(b"content B")
        assert BackupEngine._sha256(f1) != BackupEngine._sha256(f2)


# ===================================================================
# Manifest Persistence Tests
# ===================================================================


class TestManifestPersistence:
    """Test that backup records are saved to the database."""

    def test_record_persisted_in_db(
        self, engine: BackupEngine, fake_db: Path, tmp_path: Path
    ) -> None:
        engine.backup_database(tmp_path / "db_out")

        conn = sqlite3.connect(str(fake_db))
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM backup_manifests").fetchall()
        conn.close()

        assert len(rows) >= 1
        row = rows[0]
        assert row["backup_type"] == "db"
        assert row["size_bytes"] > 0
        assert row["manifest_json"]

        # Verify manifest JSON is valid
        data = json.loads(row["manifest_json"])
        assert "files" in data
        assert "total_size" in data
