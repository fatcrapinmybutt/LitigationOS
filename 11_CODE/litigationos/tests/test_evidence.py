"""Comprehensive tests for the EvidenceEngine.

Covers: instantiation, add_evidence validation, FTS5 search, get_evidence
filtering, exhibit list generation, file-type detection, duplicate hash
detection, Michigan-specific concerns (MRE 901, child-initials), and edge
cases (empty DB, unknown claim types, metadata completeness).

NOTE: test_evidence_chain.py already covers chain-of-custody hashing, gap
detection, authentication method storage, and Bates numbering.  This file
focuses on everything else.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from litigationos.db.connection import DatabaseManager
from litigationos.engines.evidence import (
    EvidenceEngine,
    VALID_EVIDENCE_TYPES,
    _detect_file_type,
)


# ============================================================================
# Core Evidence Operations
# ============================================================================


class TestEvidenceEngineCore:
    """Instantiation and basic CRUD operations."""

    def test_evidence_engine_instantiation(self, tmp_db: DatabaseManager):
        """Engine can be created with a DatabaseManager."""
        engine = EvidenceEngine(tmp_db)
        assert engine is not None
        assert engine._db is tmp_db

    def test_add_evidence_returns_id(
        self, tmp_db: DatabaseManager, sample_case: dict, tmp_path: Path
    ):
        """add_evidence returns a positive integer row ID."""
        engine = EvidenceEngine(tmp_db)
        dummy = tmp_path / "test_doc.pdf"
        dummy.write_bytes(b"pdf content")
        eid = engine.add_evidence(
            case_id=sample_case["id"],
            file_path=str(dummy),
            evidence_type="document",
            description="Test document for add_evidence return value",
        )
        assert isinstance(eid, int)
        assert eid > 0

    def test_search_evidence_finds_matching(
        self, tmp_db: DatabaseManager, sample_case: dict, sample_evidence: list
    ):
        """FTS5 search returns evidence whose description matches the query."""
        engine = EvidenceEngine(tmp_db)
        results = engine.search_evidence("custody", case_id=sample_case["id"])
        assert len(results) >= 1
        assert any("Custody" in r.get("title", "") for r in results)

    def test_search_evidence_with_case_filter(
        self, tmp_db: DatabaseManager, sample_case: dict, sample_evidence: list
    ):
        """Passing case_id limits search to that case only."""
        engine = EvidenceEngine(tmp_db)
        # Create a second case with its own evidence
        cursor = tmp_db.execute(
            "INSERT INTO cases (case_number, case_type, title, status) "
            "VALUES (?, ?, ?, ?)",
            ("2025-9999-XX", "civil", "Other Case", "active"),
        )
        other_id = cursor.lastrowid
        dummy = tmp_path_file(tmp_db, "other_case.pdf")
        tmp_db.execute(
            "INSERT INTO evidence (case_id, title, description, file_path, file_type) "
            "VALUES (?, ?, ?, ?, ?)",
            (other_id, "Other Custody", "custody doc for other case", str(dummy), "pdf"),
        )
        # Search scoped to sample_case should NOT include the other case's evidence
        results = engine.search_evidence("custody", case_id=sample_case["id"])
        for r in results:
            assert r["case_id"] == sample_case["id"]

    def test_search_evidence_no_results(
        self, tmp_db: DatabaseManager, sample_case: dict, sample_evidence: list
    ):
        """A query matching nothing returns an empty list, not an error."""
        engine = EvidenceEngine(tmp_db)
        results = engine.search_evidence(
            "xylophone", case_id=sample_case["id"]
        )
        assert results == []


# Helper — creates a tiny file and returns its path (avoids repeating boilerplate)
def tmp_path_file(db: DatabaseManager, name: str = "tmp.txt") -> Path:
    """Resolve a temporary file path next to the DB."""
    p = Path(db.db_path).parent / name
    p.write_bytes(b"placeholder")
    return p


# ============================================================================
# Evidence Quality — metadata, dedup, categorization
# ============================================================================


class TestEvidenceQuality:
    """Metadata completeness, duplicate detection, and categorization."""

    def test_add_evidence_stores_all_optional_fields(
        self, tmp_db: DatabaseManager, sample_case: dict, tmp_path: Path
    ):
        """title, source, date_created, and tags are persisted when provided."""
        engine = EvidenceEngine(tmp_db)
        dummy = tmp_path / "full_meta.pdf"
        dummy.write_bytes(b"full metadata test")
        eid = engine.add_evidence(
            case_id=sample_case["id"],
            file_path=str(dummy),
            evidence_type="document",
            description="Document with all metadata",
            title="Custom Title",
            source="Petitioner's phone records",
            date_created="2024-06-15",
            tags=["custody", "communication"],
        )
        row = tmp_db.fetchone("SELECT * FROM evidence WHERE id = ?", (eid,))
        assert row["title"] == "Custom Title"
        assert row["source"] == "Petitioner's phone records"
        assert row["date_created"] == "2024-06-15"
        tags = json.loads(row["tags"])
        assert "custody" in tags
        assert "communication" in tags

    def test_add_evidence_default_title_is_filename(
        self, tmp_db: DatabaseManager, sample_case: dict, tmp_path: Path
    ):
        """When title is omitted the file name is used as the title."""
        engine = EvidenceEngine(tmp_db)
        dummy = tmp_path / "bank_statement_jan.pdf"
        dummy.write_bytes(b"financial data")
        eid = engine.add_evidence(
            case_id=sample_case["id"],
            file_path=str(dummy),
            evidence_type="financial",
            description="January bank statement",
        )
        row = tmp_db.fetchone("SELECT title FROM evidence WHERE id = ?", (eid,))
        assert row["title"] == "bank_statement_jan.pdf"

    def test_duplicate_file_produces_same_hash(
        self, tmp_db: DatabaseManager, sample_case: dict, tmp_path: Path
    ):
        """Adding the same file content twice yields identical SHA-256 hashes."""
        engine = EvidenceEngine(tmp_db)
        content = b"identical content for dedup test"
        file_a = tmp_path / "dup_a.pdf"
        file_b = tmp_path / "dup_b.pdf"
        file_a.write_bytes(content)
        file_b.write_bytes(content)

        eid_a = engine.add_evidence(
            sample_case["id"], str(file_a), "document", "Copy A"
        )
        eid_b = engine.add_evidence(
            sample_case["id"], str(file_b), "document", "Copy B"
        )
        hash_a = tmp_db.fetchone(
            "SELECT notes FROM evidence WHERE id = ?", (eid_a,)
        )["notes"]
        hash_b = tmp_db.fetchone(
            "SELECT notes FROM evidence WHERE id = ?", (eid_b,)
        )["notes"]
        assert hash_a == hash_b
        expected = "sha256:" + hashlib.sha256(content).hexdigest()
        assert hash_a == expected

    def test_file_type_detection_pdf(self, tmp_path: Path):
        """A .pdf file is detected as 'pdf'."""
        assert _detect_file_type(tmp_path / "report.pdf") == "pdf"

    def test_file_type_detection_image(self, tmp_path: Path):
        """Image extensions map to 'image'."""
        for ext in (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"):
            assert _detect_file_type(tmp_path / f"photo{ext}") == "image"

    def test_file_type_detection_financial(self, tmp_path: Path):
        """.xlsx and .xls map to 'financial'."""
        assert _detect_file_type(tmp_path / "ledger.xlsx") == "financial"
        assert _detect_file_type(tmp_path / "ledger.xls") == "financial"

    def test_file_type_detection_email(self, tmp_path: Path):
        """.eml and .msg map to 'email'."""
        assert _detect_file_type(tmp_path / "message.eml") == "email"
        assert _detect_file_type(tmp_path / "message.msg") == "email"

    def test_file_type_detection_unknown_defaults_to_document(self, tmp_path: Path):
        """An unrecognised extension falls back to 'document'."""
        assert _detect_file_type(tmp_path / "data.xyz") == "document"

    def test_file_type_detection_recording(self, tmp_path: Path):
        """Audio/video extensions map to 'recording'."""
        for ext in (".mp3", ".mp4", ".wav", ".mov"):
            assert _detect_file_type(tmp_path / f"media{ext}") == "recording"


# ============================================================================
# Michigan Legal — MRE compliance
# ============================================================================


class TestMichiganLegal:
    """Michigan Rules of Evidence and child-privacy compliance."""

    def test_authenticate_declaration_structure(
        self, tmp_db: DatabaseManager, sample_evidence: list
    ):
        """The MRE 901 declaration contains all required sections."""
        engine = EvidenceEngine(tmp_db)
        decl = engine.authenticate(sample_evidence[0]["id"])
        # Must contain numbered paragraphs 1-5
        for n in range(1, 6):
            assert f"{n}." in decl
        # Must contain signature and printed name lines
        assert "Signature" in decl
        assert "Printed Name" in decl
        # Must be dated
        assert "Dated:" in decl

    def test_authenticate_includes_evidence_title(
        self, tmp_db: DatabaseManager, sample_evidence: list
    ):
        """Declaration references the evidence title."""
        engine = EvidenceEngine(tmp_db)
        decl = engine.authenticate(sample_evidence[0]["id"])
        assert sample_evidence[0]["title"] in decl

    def test_child_initials_preserved_in_exhibit_list(
        self, tmp_db: DatabaseManager, sample_case: dict, tmp_path: Path
    ):
        """Evidence using child initials (L.D.W.) passes through exhibit list intact."""
        engine = EvidenceEngine(tmp_db)
        dummy = tmp_path / "child_record.pdf"
        dummy.write_bytes(b"child evidence")
        engine.add_evidence(
            case_id=sample_case["id"],
            file_path=str(dummy),
            evidence_type="document",
            description="Parenting time log for L.D.W.",
        )
        exhibit_list = engine.get_exhibit_list(sample_case["id"])
        assert "L.D.W." in exhibit_list

    def test_authenticate_uses_bates_when_assigned(
        self, tmp_db: DatabaseManager, sample_case: dict, sample_evidence: list
    ):
        """If a Bates number is assigned, the declaration references it."""
        engine = EvidenceEngine(tmp_db)
        engine.assign_bates(sample_case["id"], prefix="MRE")
        decl = engine.authenticate(sample_evidence[0]["id"])
        assert "MRE-" in decl


# ============================================================================
# Edge Cases
# ============================================================================


class TestEdgeCases:
    """Boundary conditions, error handling, and graceful degradation."""

    def test_add_evidence_invalid_type_raises(
        self, tmp_db: DatabaseManager, sample_case: dict, tmp_path: Path
    ):
        """A non-existent evidence_type raises ValueError."""
        engine = EvidenceEngine(tmp_db)
        dummy = tmp_path / "bad_type.pdf"
        dummy.write_bytes(b"bad type")
        with pytest.raises(ValueError, match="Invalid evidence_type"):
            engine.add_evidence(
                case_id=sample_case["id"],
                file_path=str(dummy),
                evidence_type="hologram",
                description="Invalid type",
            )

    def test_add_evidence_missing_file_raises(
        self, tmp_db: DatabaseManager, sample_case: dict
    ):
        """A non-existent file path raises FileNotFoundError."""
        engine = EvidenceEngine(tmp_db)
        with pytest.raises(FileNotFoundError):
            engine.add_evidence(
                case_id=sample_case["id"],
                file_path=r"C:\nonexistent\file.pdf",
                evidence_type="document",
                description="Ghost file",
            )

    def test_get_evidence_empty_case_returns_empty_list(
        self, tmp_db: DatabaseManager
    ):
        """Querying evidence for a case with none returns [] not an error."""
        engine = EvidenceEngine(tmp_db)
        cursor = tmp_db.execute(
            "INSERT INTO cases (title) VALUES (?)", ("Empty Case",)
        )
        empty_id = cursor.lastrowid
        result = engine.get_evidence(case_id=empty_id)
        assert result == []

    def test_get_evidence_invalid_type_filter_raises(
        self, tmp_db: DatabaseManager
    ):
        """Filtering by a bad evidence_type raises ValueError."""
        engine = EvidenceEngine(tmp_db)
        with pytest.raises(ValueError, match="Invalid evidence_type"):
            engine.get_evidence(evidence_type="hologram")

    def test_exhibit_list_empty_case(self, tmp_db: DatabaseManager):
        """Exhibit list for a case with no evidence renders without errors."""
        engine = EvidenceEngine(tmp_db)
        cursor = tmp_db.execute(
            "INSERT INTO cases (title) VALUES (?)", ("No Exhibits",)
        )
        cid = cursor.lastrowid
        exhibit_list = engine.get_exhibit_list(cid)
        assert "EXHIBIT LIST" in exhibit_list
        assert "Total exhibits: 0" in exhibit_list

    def test_exhibit_list_counts_all_items(
        self, tmp_db: DatabaseManager, sample_case: dict, sample_evidence: list
    ):
        """Exhibit list total matches the number of evidence rows."""
        engine = EvidenceEngine(tmp_db)
        exhibit_list = engine.get_exhibit_list(sample_case["id"])
        assert f"Total exhibits: {len(sample_evidence)}" in exhibit_list

    def test_get_evidence_filters_by_case_id(
        self, tmp_db: DatabaseManager, sample_case: dict, sample_evidence: list
    ):
        """get_evidence(case_id=X) returns only items for that case."""
        engine = EvidenceEngine(tmp_db)
        results = engine.get_evidence(case_id=sample_case["id"])
        assert len(results) == len(sample_evidence)
        for r in results:
            assert r["case_id"] == sample_case["id"]

    def test_get_evidence_no_filter_returns_all(
        self, tmp_db: DatabaseManager, sample_case: dict, sample_evidence: list
    ):
        """get_evidence() with no filters returns all evidence in the DB."""
        engine = EvidenceEngine(tmp_db)
        results = engine.get_evidence()
        assert len(results) >= len(sample_evidence)

    def test_evidence_metadata_complete(
        self, tmp_db: DatabaseManager, sample_case: dict, tmp_path: Path
    ):
        """Every evidence row has non-null id, case_id, title, file_path, date_imported."""
        engine = EvidenceEngine(tmp_db)
        dummy = tmp_path / "complete_meta.pdf"
        dummy.write_bytes(b"metadata completeness check")
        eid = engine.add_evidence(
            case_id=sample_case["id"],
            file_path=str(dummy),
            evidence_type="document",
            description="Metadata completeness test",
        )
        row = tmp_db.fetchone("SELECT * FROM evidence WHERE id = ?", (eid,))
        ev = dict(row)
        assert ev["id"] is not None
        assert ev["case_id"] == sample_case["id"]
        assert ev["title"] is not None
        assert ev["file_path"] is not None
        assert ev["date_imported"] is not None
        assert ev["file_type"] is not None

    def test_valid_evidence_types_constant(self):
        """VALID_EVIDENCE_TYPES is a non-empty tuple of strings."""
        assert isinstance(VALID_EVIDENCE_TYPES, tuple)
        assert len(VALID_EVIDENCE_TYPES) >= 9
        for t in VALID_EVIDENCE_TYPES:
            assert isinstance(t, str)
