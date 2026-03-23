"""Tests for evidence chain of custody -- tracking, gap detection,
authentication metadata, and Bates numbering for Phase 5-6."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from litigationos.db.connection import DatabaseManager
from litigationos.engines.evidence import EvidenceEngine, VALID_EVIDENCE_TYPES


# ============================================================================
# Chain of custody tracking
# ============================================================================


class TestChainOfCustody:
    """Test evidence chain of custody via SHA-256 hashing and metadata."""

    def test_sha256_stored_on_add(
        self, tmp_db: DatabaseManager, sample_case: dict, tmp_path: Path
    ):
        engine = EvidenceEngine(tmp_db)
        dummy = tmp_path / "chain_test.pdf"
        dummy.write_bytes(b"chain of custody test content")
        eid = engine.add_evidence(
            case_id=sample_case["id"],
            file_path=str(dummy),
            evidence_type="document",
            description="Chain test doc",
        )
        row = tmp_db.fetchone("SELECT notes FROM evidence WHERE id = ?", (eid,))
        assert row["notes"].startswith("sha256:")

    def test_sha256_matches_file(
        self, tmp_db: DatabaseManager, sample_case: dict, tmp_path: Path
    ):
        engine = EvidenceEngine(tmp_db)
        content = b"verify hash consistency"
        dummy = tmp_path / "hash_test.pdf"
        dummy.write_bytes(content)
        eid = engine.add_evidence(
            case_id=sample_case["id"],
            file_path=str(dummy),
            evidence_type="document",
            description="Hash verification",
        )
        row = tmp_db.fetchone("SELECT notes FROM evidence WHERE id = ?", (eid,))
        stored_hash = row["notes"].split("sha256:")[1]
        expected = hashlib.sha256(content).hexdigest()
        assert stored_hash == expected

    def test_date_imported_set_automatically(
        self, tmp_db: DatabaseManager, sample_case: dict, tmp_path: Path
    ):
        engine = EvidenceEngine(tmp_db)
        dummy = tmp_path / "import_test.pdf"
        dummy.write_bytes(b"auto import date")
        eid = engine.add_evidence(
            case_id=sample_case["id"],
            file_path=str(dummy),
            evidence_type="document",
            description="Import date test",
        )
        row = tmp_db.fetchone("SELECT date_imported FROM evidence WHERE id = ?", (eid,))
        assert row["date_imported"] is not None

    def test_source_tracked(
        self, tmp_db: DatabaseManager, sample_case: dict, tmp_path: Path
    ):
        engine = EvidenceEngine(tmp_db)
        dummy = tmp_path / "source_test.pdf"
        dummy.write_bytes(b"source tracking")
        eid = engine.add_evidence(
            case_id=sample_case["id"],
            file_path=str(dummy),
            evidence_type="document",
            description="Source tracking",
            source="Petitioner's personal records",
        )
        row = tmp_db.fetchone("SELECT source FROM evidence WHERE id = ?", (eid,))
        assert row["source"] == "Petitioner's personal records"


# ============================================================================
# Gap detection
# ============================================================================


class TestEvidenceGapDetection:
    """Test evidence gap analysis for claims."""

    def test_gap_found_for_unsupported_claim(
        self, tmp_db: DatabaseManager, sample_case: dict
    ):
        engine = EvidenceEngine(tmp_db)
        # Add a claim with no matching evidence
        tmp_db.execute(
            "INSERT INTO claims (case_id, title, status) VALUES (?, ?, ?)",
            (sample_case["id"], "Count I: Obscure Xylophone Tort", "active"),
        )
        gaps = engine.check_gaps(sample_case["id"])
        assert len(gaps) >= 1
        assert any("Xylophone" in g["claim_title"] for g in gaps)

    def test_no_gap_when_evidence_matches(
        self, tmp_db: DatabaseManager, sample_case: dict, sample_evidence: list
    ):
        engine = EvidenceEngine(tmp_db)
        # Add a claim whose keywords match evidence descriptions
        tmp_db.execute(
            "INSERT INTO claims (case_id, title, status) VALUES (?, ?, ?)",
            (sample_case["id"], "Count I: Custody Agreement Dispute", "active"),
        )
        gaps = engine.check_gaps(sample_case["id"])
        custody_gaps = [g for g in gaps if "Custody" in g.get("claim_title", "")]
        assert len(custody_gaps) == 0

    def test_gap_returns_claim_info(
        self, tmp_db: DatabaseManager, sample_case: dict
    ):
        engine = EvidenceEngine(tmp_db)
        tmp_db.execute(
            "INSERT INTO claims (case_id, title, status) VALUES (?, ?, ?)",
            (sample_case["id"], "Count II: Invisible Widget Claim", "active"),
        )
        gaps = engine.check_gaps(sample_case["id"])
        for gap in gaps:
            assert "claim_id" in gap
            assert "claim_title" in gap
            assert "issue" in gap


# ============================================================================
# Authentication metadata
# ============================================================================


class TestAuthenticationMetadata:
    """Test MRE 901 authentication workflow."""

    def test_authenticate_sets_method(
        self, tmp_db: DatabaseManager, sample_evidence: list
    ):
        engine = EvidenceEngine(tmp_db)
        engine.authenticate(sample_evidence[0]["id"])
        row = tmp_db.fetchone(
            "SELECT authentication_method FROM evidence WHERE id = ?",
            (sample_evidence[0]["id"],),
        )
        assert row["authentication_method"] == "witness_901"

    def test_authenticate_declaration_mentions_mre(
        self, tmp_db: DatabaseManager, sample_evidence: list
    ):
        engine = EvidenceEngine(tmp_db)
        decl = engine.authenticate(sample_evidence[0]["id"])
        assert "MRE 901" in decl

    def test_authenticate_includes_perjury_clause(
        self, tmp_db: DatabaseManager, sample_evidence: list
    ):
        engine = EvidenceEngine(tmp_db)
        decl = engine.authenticate(sample_evidence[1]["id"])
        assert "penalty of perjury" in decl

    def test_authenticate_nonexistent_raises(self, tmp_db: DatabaseManager):
        engine = EvidenceEngine(tmp_db)
        with pytest.raises(LookupError):
            engine.authenticate(99999)


# ============================================================================
# Bates numbering
# ============================================================================


class TestBatesNumbering:
    """Test sequential Bates number assignment."""

    def test_bates_format_prefix_six_digits(
        self, tmp_db: DatabaseManager, sample_case: dict, sample_evidence: list
    ):
        engine = EvidenceEngine(tmp_db)
        assignments = engine.assign_bates(sample_case["id"], prefix="CHAIN")
        for a in assignments:
            parts = a["bates_number"].split("-")
            assert parts[0] == "CHAIN"
            assert len(parts[1]) == 6

    def test_bates_sequential_order(
        self, tmp_db: DatabaseManager, sample_case: dict, sample_evidence: list
    ):
        engine = EvidenceEngine(tmp_db)
        assignments = engine.assign_bates(sample_case["id"], prefix="SEQ")
        nums = [int(a["bates_number"].split("-")[1]) for a in assignments]
        assert nums == sorted(nums)
        assert nums == [1, 2, 3]

    def test_bates_idempotent(
        self, tmp_db: DatabaseManager, sample_case: dict, sample_evidence: list
    ):
        engine = EvidenceEngine(tmp_db)
        first = engine.assign_bates(sample_case["id"], prefix="IDEM")
        second = engine.assign_bates(sample_case["id"], prefix="IDEM")
        assert len(first) == 3
        assert len(second) == 0  # already assigned

    def test_bates_empty_case(self, tmp_db: DatabaseManager):
        engine = EvidenceEngine(tmp_db)
        tmp_db.execute("INSERT INTO cases (title) VALUES (?)", ("Empty",))
        row = tmp_db.fetchone("SELECT id FROM cases WHERE title = 'Empty'")
        assignments = engine.assign_bates(row["id"])
        assert assignments == []
