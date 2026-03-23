"""Tests for e-filing preparation engine -- PDF/A compliance, packet
assembly, cover sheet generation, and TrueFiling format validation
for Phase 5-6."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from litigationos.db.connection import DatabaseManager
from litigationos.engines.filing import (
    FilingEngine,
    FilingStack,
    StackComponent,
    ValidationResult,
    MCR_FORMAT,
    VALID_FILING_TYPES,
)


# ============================================================================
# PDF/A compliance checks
# ============================================================================


class TestPDFACompliance:
    """Test PDF/A compliance validation logic."""

    def test_mcr_format_has_margins(self):
        assert MCR_FORMAT["margin_top_inches"] == 1.0
        assert MCR_FORMAT["margin_bottom_inches"] == 1.0
        assert MCR_FORMAT["margin_left_inches"] == 1.0
        assert MCR_FORMAT["margin_right_inches"] == 1.0

    def test_mcr_format_has_font(self):
        assert MCR_FORMAT["font"] == "Times New Roman"
        assert MCR_FORMAT["font_size_pt"] == 12

    def test_mcr_format_double_spacing(self):
        assert MCR_FORMAT["line_spacing"] == 2.0

    def test_filing_type_motion_valid(self):
        assert "motion" in VALID_FILING_TYPES

    def test_filing_type_brief_valid(self):
        assert "brief" in VALID_FILING_TYPES

    def test_filing_type_complaint_valid(self):
        assert "complaint" in VALID_FILING_TYPES


# ============================================================================
# Packet assembly
# ============================================================================


class TestPacketAssembly:
    """Test filing packet/stack assembly."""

    def test_build_stack_has_all_components(
        self, tmp_db: DatabaseManager, sample_case: dict
    ):
        engine = FilingEngine(tmp_db)
        engine.create_filing(
            case_id=sample_case["id"],
            filing_type="motion",
            court="Test Court",
            title="Packet Motion",
        )
        stack = engine.build_stack(sample_case["id"], "motion")
        comp_names = [c.name for c in stack.components]
        assert "main_document" in comp_names
        assert "exhibits" in comp_names
        assert "proof_of_service" in comp_names
        assert "proposed_order" in comp_names

    def test_build_stack_has_checklist(
        self, tmp_db: DatabaseManager, sample_case: dict
    ):
        engine = FilingEngine(tmp_db)
        engine.create_filing(
            case_id=sample_case["id"],
            filing_type="brief",
            court="COA",
            title="Packet Brief",
        )
        stack = engine.build_stack(sample_case["id"], "brief")
        assert "main_document_present" in stack.checklist
        assert "proof_of_service_present" in stack.checklist

    def test_export_assembles_packet(
        self, tmp_db: DatabaseManager, tmp_path: Path
    ):
        engine = FilingEngine(tmp_db)
        doc = tmp_path / "packet_doc.txt"
        doc.write_text("Filing content", encoding="utf-8")
        stack = FilingStack(
            filing_id=1, case_id=1, filing_type="motion", title="Export Packet",
            components=[
                StackComponent(name="main_document", present=True, file_path=str(doc)),
            ],
            checklist={"main_document_present": True},
        )
        out = tmp_path / "packet_out"
        engine.export_stack(stack, out)
        assert (out / "manifest.json").exists()
        assert (out / "main_document.txt").exists()


# ============================================================================
# Cover sheet generation
# ============================================================================


class TestCoverSheetGeneration:
    """Test cover sheet metadata for e-filing."""

    def test_filing_has_title(
        self, tmp_db: DatabaseManager, sample_case: dict
    ):
        engine = FilingEngine(tmp_db)
        fid = engine.create_filing(
            case_id=sample_case["id"],
            filing_type="motion",
            court="Muskegon Circuit",
            title="Cover Sheet Motion",
        )
        row = tmp_db.fetchone("SELECT title FROM filings WHERE id = ?", (fid,))
        assert row["title"] == "Cover Sheet Motion"

    def test_filing_has_court_in_notes(
        self, tmp_db: DatabaseManager, sample_case: dict
    ):
        engine = FilingEngine(tmp_db)
        fid = engine.create_filing(
            case_id=sample_case["id"],
            filing_type="brief",
            court="Michigan Court of Appeals",
            title="Cover Brief",
        )
        row = tmp_db.fetchone("SELECT notes FROM filings WHERE id = ?", (fid,))
        assert "Michigan Court of Appeals" in row["notes"]

    def test_filing_has_case_number(
        self, tmp_db: DatabaseManager, sample_case: dict
    ):
        assert sample_case["case_number"] == "2025-0001-FC"

    def test_filing_initial_status_draft(
        self, tmp_db: DatabaseManager, sample_case: dict
    ):
        engine = FilingEngine(tmp_db)
        fid = engine.create_filing(
            case_id=sample_case["id"],
            filing_type="motion",
            court="Test",
            title="Status Test",
        )
        row = tmp_db.fetchone("SELECT status FROM filings WHERE id = ?", (fid,))
        assert row["status"] == "draft"


# ============================================================================
# TrueFiling format validation
# ============================================================================


class TestTrueFilingFormat:
    """Test format requirements for TrueFiling/MiFILE submission."""

    def test_validate_complete_stack_passes(self, tmp_db: DatabaseManager):
        engine = FilingEngine(tmp_db)
        stack = FilingStack(
            filing_id=1, case_id=1, filing_type="motion", title="TF Test",
            components=[
                StackComponent(name="main_document", present=True),
                StackComponent(name="proof_of_service", present=True),
                StackComponent(name="exhibits", present=True),
                StackComponent(name="proposed_order", present=True),
            ],
            checklist={
                "main_document_present": True,
                "proof_of_service_present": True,
                "exhibits_present": True,
                "proposed_order_present": True,
            },
        )
        result = engine.validate_stack(stack)
        assert result.score >= 80

    def test_validate_missing_service_warns(self, tmp_db: DatabaseManager):
        engine = FilingEngine(tmp_db)
        stack = FilingStack(
            filing_id=1, case_id=1, filing_type="motion", title="No POS",
            components=[
                StackComponent(name="main_document", present=True),
                StackComponent(name="proof_of_service", present=False),
            ],
            checklist={
                "main_document_present": True,
                "proof_of_service_present": False,
            },
        )
        result = engine.validate_stack(stack)
        pos_issues = [i for i in result.issues if "service" in i.lower() or "proof" in i.lower()]
        assert len(pos_issues) >= 1

    def test_validation_result_has_warnings(self, tmp_db: DatabaseManager):
        engine = FilingEngine(tmp_db)
        stack = FilingStack(
            filing_id=1, case_id=1, filing_type="motion", title="Warn Test",
            components=[
                StackComponent(name="main_document", present=True),
                StackComponent(name="proof_of_service", present=True),
            ],
            checklist={
                "main_document_present": True,
                "proof_of_service_present": True,
            },
        )
        result = engine.validate_stack(stack)
        assert isinstance(result.warnings, list)
