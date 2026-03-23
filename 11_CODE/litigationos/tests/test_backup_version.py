"""Tests for backup and versioning engine -- snapshot creation, hash
verification, manifest tracking, and restore logic for Phase 5-6."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

import pytest

from litigationos.db.connection import DatabaseManager
from litigationos.engines.filing import FilingEngine, FilingStack, StackComponent


# ============================================================================
# Snapshot creation
# ============================================================================


class TestSnapshotCreation:
    """Test filing stack export as a versioned snapshot."""

    def _make_stack(self, tmp_path: Path) -> FilingStack:
        doc = tmp_path / "main.docx"
        doc.write_text("Main document content", encoding="utf-8")
        return FilingStack(
            filing_id=1,
            case_id=1,
            filing_type="motion",
            title="Snapshot Test Motion",
            components=[
                StackComponent(name="main_document", present=True, file_path=str(doc)),
                StackComponent(name="exhibits", present=True),
            ],
            checklist={"main_document_present": True},
            assembled_at=datetime.now().isoformat(),
        )

    def test_export_creates_directory(self, tmp_db: DatabaseManager, tmp_path: Path):
        engine = FilingEngine(tmp_db)
        stack = self._make_stack(tmp_path)
        out_dir = tmp_path / "snapshot_v1"
        result = engine.export_stack(stack, out_dir)
        assert result.exists()
        assert result.is_dir()

    def test_export_creates_manifest(self, tmp_db: DatabaseManager, tmp_path: Path):
        engine = FilingEngine(tmp_db)
        stack = self._make_stack(tmp_path)
        out_dir = tmp_path / "snapshot_v2"
        engine.export_stack(stack, out_dir)
        manifest = out_dir / "manifest.json"
        assert manifest.exists()

    def test_export_manifest_contains_metadata(
        self, tmp_db: DatabaseManager, tmp_path: Path
    ):
        engine = FilingEngine(tmp_db)
        stack = self._make_stack(tmp_path)
        out_dir = tmp_path / "snapshot_v3"
        engine.export_stack(stack, out_dir)
        manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["filing_type"] == "motion"
        assert manifest["title"] == "Snapshot Test Motion"
        assert "assembled_at" in manifest

    def test_export_copies_main_document(
        self, tmp_db: DatabaseManager, tmp_path: Path
    ):
        engine = FilingEngine(tmp_db)
        stack = self._make_stack(tmp_path)
        out_dir = tmp_path / "snapshot_v4"
        engine.export_stack(stack, out_dir)
        exported_doc = out_dir / "main_document.docx"
        assert exported_doc.exists()

    def test_multiple_snapshots_independent(
        self, tmp_db: DatabaseManager, tmp_path: Path
    ):
        engine = FilingEngine(tmp_db)
        stack = self._make_stack(tmp_path)
        v1 = tmp_path / "v1"
        v2 = tmp_path / "v2"
        engine.export_stack(stack, v1)
        engine.export_stack(stack, v2)
        assert (v1 / "manifest.json").exists()
        assert (v2 / "manifest.json").exists()


# ============================================================================
# Hash verification
# ============================================================================


class TestHashVerification:
    """Test file integrity verification via SHA-256."""

    def test_file_hash_consistent(self, tmp_path: Path):
        content = b"consistent hash content"
        f = tmp_path / "hashtest.bin"
        f.write_bytes(content)
        h1 = hashlib.sha256(f.read_bytes()).hexdigest()
        h2 = hashlib.sha256(f.read_bytes()).hexdigest()
        assert h1 == h2

    def test_different_content_different_hash(self, tmp_path: Path):
        f1 = tmp_path / "file1.bin"
        f2 = tmp_path / "file2.bin"
        f1.write_bytes(b"content A")
        f2.write_bytes(b"content B")
        h1 = hashlib.sha256(f1.read_bytes()).hexdigest()
        h2 = hashlib.sha256(f2.read_bytes()).hexdigest()
        assert h1 != h2

    def test_exported_file_matches_source_hash(
        self, tmp_db: DatabaseManager, tmp_path: Path
    ):
        engine = FilingEngine(tmp_db)
        src = tmp_path / "source.docx"
        src.write_bytes(b"source document bytes")
        stack = FilingStack(
            filing_id=1, case_id=1, filing_type="brief", title="Hash Test",
            components=[StackComponent(name="main_document", present=True, file_path=str(src))],
            checklist={"main_document_present": True},
        )
        out_dir = tmp_path / "hash_export"
        engine.export_stack(stack, out_dir)
        exported = out_dir / "main_document.docx"
        assert hashlib.sha256(src.read_bytes()).hexdigest() == \
               hashlib.sha256(exported.read_bytes()).hexdigest()


# ============================================================================
# Manifest tracking
# ============================================================================


class TestManifestTracking:
    """Test manifest JSON completeness."""

    def test_manifest_has_exported_files_list(
        self, tmp_db: DatabaseManager, tmp_path: Path
    ):
        engine = FilingEngine(tmp_db)
        doc = tmp_path / "doc.txt"
        doc.write_text("content", encoding="utf-8")
        stack = FilingStack(
            filing_id=1, case_id=1, filing_type="motion", title="Manifest Test",
            components=[StackComponent(name="main_document", present=True, file_path=str(doc))],
            checklist={"main_document_present": True},
        )
        out_dir = tmp_path / "manifest_out"
        engine.export_stack(stack, out_dir)
        manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
        assert "exported_files" in manifest
        assert len(manifest["exported_files"]) >= 1

    def test_manifest_has_checklist(
        self, tmp_db: DatabaseManager, tmp_path: Path
    ):
        engine = FilingEngine(tmp_db)
        stack = FilingStack(
            filing_id=1, case_id=1, filing_type="motion", title="CL Test",
            components=[],
            checklist={"main_document_present": True, "proof_of_service_present": False},
        )
        out_dir = tmp_path / "cl_out"
        engine.export_stack(stack, out_dir)
        manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["checklist"]["main_document_present"] is True
        assert manifest["checklist"]["proof_of_service_present"] is False

    def test_manifest_is_complete_field(
        self, tmp_db: DatabaseManager, tmp_path: Path
    ):
        engine = FilingEngine(tmp_db)
        stack = FilingStack(
            filing_id=1, case_id=1, filing_type="motion", title="Complete Test",
            components=[],
            checklist={"a": True, "b": True},
        )
        out_dir = tmp_path / "complete_out"
        engine.export_stack(stack, out_dir)
        manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["is_complete"] is True


# ============================================================================
# Restore logic
# ============================================================================


class TestRestoreLogic:
    """Test restoring a filing stack from an exported manifest."""

    def test_manifest_roundtrip(self, tmp_db: DatabaseManager, tmp_path: Path):
        engine = FilingEngine(tmp_db)
        doc = tmp_path / "restore.docx"
        doc.write_text("restorable content", encoding="utf-8")
        stack = FilingStack(
            filing_id=42, case_id=7, filing_type="brief", title="Restore Test",
            components=[StackComponent(name="main_document", present=True, file_path=str(doc))],
            checklist={"main_document_present": True},
        )
        out_dir = tmp_path / "restore_out"
        engine.export_stack(stack, out_dir)
        manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["filing_id"] == 42
        assert manifest["case_id"] == 7
        assert manifest["filing_type"] == "brief"

    def test_exported_file_restorable(self, tmp_db: DatabaseManager, tmp_path: Path):
        engine = FilingEngine(tmp_db)
        doc = tmp_path / "data.docx"
        doc.write_text("precious data", encoding="utf-8")
        stack = FilingStack(
            filing_id=1, case_id=1, filing_type="motion", title="Restore File",
            components=[StackComponent(name="main_document", present=True, file_path=str(doc))],
            checklist={"main_document_present": True},
        )
        out_dir = tmp_path / "restore_file_out"
        engine.export_stack(stack, out_dir)
        restored = (out_dir / "main_document.docx").read_text(encoding="utf-8")
        assert restored == "precious data"
