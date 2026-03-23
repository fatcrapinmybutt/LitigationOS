"""Tests for complaint filing stacks -- template validation, required
fields, agency format compliance, and cross-reference verification
for Phase 5-6."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from litigationos.db.connection import DatabaseManager
from litigationos.engines.court_rules import CourtRulesEngine
from litigationos.engines.evidence import EvidenceEngine
from litigationos.engines.filing import (
    FilingEngine,
    FilingStack,
    StackComponent,
    ValidationResult,
    VALID_FILING_TYPES,
    STACK_COMPONENTS,
)


# ============================================================================
# Template validation
# ============================================================================


class TestComplaintTemplateValidation:
    """Test complaint template structures."""

    def test_complaint_is_valid_filing_type(self):
        assert "complaint" in VALID_FILING_TYPES

    def test_response_is_valid_filing_type(self):
        assert "response" in VALID_FILING_TYPES

    def test_affidavit_is_valid_filing_type(self):
        assert "affidavit" in VALID_FILING_TYPES

    def test_stack_components_defined(self):
        assert "main_document" in STACK_COMPONENTS
        assert "exhibits" in STACK_COMPONENTS
        assert "proof_of_service" in STACK_COMPONENTS

    def test_create_complaint_filing(
        self, tmp_db: DatabaseManager, sample_case: dict
    ):
        engine = FilingEngine(tmp_db)
        fid = engine.create_filing(
            case_id=sample_case["id"],
            filing_type="complaint",
            court="Muskegon County Circuit Court",
            title="Complaint for Custody Modification",
        )
        row = tmp_db.fetchone("SELECT * FROM filings WHERE id = ?", (fid,))
        assert row["filing_type"] == "complaint"
        assert row["status"] == "draft"


# ============================================================================
# Required fields present
# ============================================================================


class TestRequiredFields:
    """Test that complaint stacks have all required fields."""

    def test_complaint_stack_requires_exhibits(
        self, tmp_db: DatabaseManager, sample_case: dict
    ):
        engine = FilingEngine(tmp_db)
        engine.create_filing(
            case_id=sample_case["id"],
            filing_type="complaint",
            court="Test Court",
            title="Complaint Fields Test",
        )
        stack = engine.build_stack(sample_case["id"], "complaint")
        assert "exhibits_present" in stack.checklist

    def test_complaint_stack_requires_proposed_order(
        self, tmp_db: DatabaseManager, sample_case: dict
    ):
        engine = FilingEngine(tmp_db)
        engine.create_filing(
            case_id=sample_case["id"],
            filing_type="complaint",
            court="Test Court",
            title="Order Fields Test",
        )
        stack = engine.build_stack(sample_case["id"], "complaint")
        assert "proposed_order_present" in stack.checklist

    def test_complaint_stack_requires_main_document(
        self, tmp_db: DatabaseManager, sample_case: dict
    ):
        engine = FilingEngine(tmp_db)
        engine.create_filing(
            case_id=sample_case["id"],
            filing_type="complaint",
            court="Test Court",
            title="Main Doc Test",
        )
        stack = engine.build_stack(sample_case["id"], "complaint")
        assert "main_document_present" in stack.checklist

    def test_case_has_required_title(self, tmp_db: DatabaseManager, sample_case: dict):
        assert sample_case["title"] is not None
        assert len(sample_case["title"]) > 0

    def test_case_has_required_status(self, tmp_db: DatabaseManager, sample_case: dict):
        assert sample_case["status"] in ("active", "closed", "appealed", "settled")


# ============================================================================
# Agency format compliance
# ============================================================================


class TestAgencyFormatCompliance:
    """Test Michigan agency/court format requirements for complaints."""

    def test_mcr_3206_domestic_relations(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        rule = engine.get_rule("MCR 3.206")
        assert rule is not None
        assert rule["category"] == "family"

    def test_domestic_requires_waiting_period(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        rule = engine.get_rule("MCR 3.206")
        reqs = rule.get("requirements", {})
        assert reqs["waiting_period_no_children_days"] == 60
        assert reqs["waiting_period_with_children_days"] == 180

    def test_parenting_time_requires_conciliation(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        rule = engine.get_rule("MCR 3.310")
        assert rule is not None
        reqs = rule.get("requirements", {})
        assert reqs["conciliation_required"] is True

    def test_summons_expires_91_days(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        rule = engine.get_rule("MCR 2.105")
        reqs = rule.get("requirements", {})
        assert reqs["service_within_days"] == 91


# ============================================================================
# Cross-reference verification
# ============================================================================


class TestCrossReferenceVerification:
    """Test cross-references between complaints and evidence."""

    def test_evidence_linked_to_case(
        self, tmp_db: DatabaseManager, sample_case: dict, sample_evidence: list
    ):
        engine = EvidenceEngine(tmp_db)
        items = engine.get_evidence(case_id=sample_case["id"])
        assert len(items) == len(sample_evidence)

    def test_filing_linked_to_case(
        self, tmp_db: DatabaseManager, sample_case: dict, sample_filing: dict
    ):
        engine = FilingEngine(tmp_db)
        filings = engine.get_filings(case_id=sample_case["id"])
        assert len(filings) >= 1
        assert any(f["id"] == sample_filing["id"] for f in filings)

    def test_deadline_linked_to_case(
        self, tmp_db: DatabaseManager, sample_case: dict
    ):
        from litigationos.engines.deadline import DeadlineEngine
        from datetime import date, timedelta
        engine = DeadlineEngine(tmp_db)
        dl_id = engine.add_deadline(
            case_id=sample_case["id"],
            title="Complaint Deadline",
            due_date=date.today() + timedelta(days=21),
            rule_basis="MCR 2.108",
        )
        row = tmp_db.fetchone("SELECT case_id FROM deadlines WHERE id = ?", (dl_id,))
        assert row["case_id"] == sample_case["id"]

    def test_parties_linked_to_case(
        self, tmp_db: DatabaseManager, sample_case: dict, sample_party: list
    ):
        rows = tmp_db.fetchall(
            "SELECT * FROM parties WHERE case_id = ?", (sample_case["id"],)
        )
        assert len(rows) == 2

    def test_filing_status_transitions(
        self, tmp_db: DatabaseManager, sample_filing: dict
    ):
        engine = FilingEngine(tmp_db)
        engine.update_status(sample_filing["id"], "review")
        row = tmp_db.fetchone("SELECT status FROM filings WHERE id = ?", (sample_filing["id"],))
        assert row["status"] == "review"
        engine.update_status(sample_filing["id"], "ready")
        row = tmp_db.fetchone("SELECT status FROM filings WHERE id = ?", (sample_filing["id"],))
        assert row["status"] == "ready"
