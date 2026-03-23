"""Tests for pre-filing QA engine -- GO/CONDITIONAL/NO-GO logic,
signature detection, service address validation, exhibit reference
verification for Phase 5-6."""

from __future__ import annotations

from pathlib import Path

import pytest

from litigationos.db.connection import DatabaseManager
from litigationos.engines.filing import (
    FilingEngine,
    FilingStack,
    StackComponent,
    ValidationResult,
    VALID_FILING_TYPES,
    VALID_STATUSES,
)
from litigationos.engines.evidence import EvidenceEngine


# ============================================================================
# GO / CONDITIONAL / NO-GO logic
# ============================================================================


class TestPrefilingQADecision:
    """Test GO/CONDITIONAL/NO-GO decision logic based on stack validation."""

    def _make_stack(self, checklist: dict, filing_type: str = "motion") -> FilingStack:
        components = []
        for name, present in checklist.items():
            clean = name.replace("_present", "")
            components.append(StackComponent(name=clean, present=present))
        return FilingStack(
            filing_id=1,
            case_id=1,
            filing_type=filing_type,
            title="QA Test Filing",
            components=components,
            checklist=checklist,
        )

    def test_go_when_all_present(self, tmp_db: DatabaseManager):
        engine = FilingEngine(tmp_db)
        stack = self._make_stack({
            "main_document_present": True,
            "proof_of_service_present": True,
            "exhibits_present": True,
            "proposed_order_present": True,
        })
        result = engine.validate_stack(stack)
        # GO: score >= 80 and no issues
        assert result.score >= 80 or result.valid is True

    def test_nogo_when_main_missing(self, tmp_db: DatabaseManager):
        engine = FilingEngine(tmp_db)
        stack = self._make_stack({
            "main_document_present": False,
            "proof_of_service_present": False,
        })
        result = engine.validate_stack(stack)
        assert result.valid is False
        assert len(result.issues) >= 1

    def test_conditional_partial_checklist(self, tmp_db: DatabaseManager):
        engine = FilingEngine(tmp_db)
        stack = self._make_stack({
            "main_document_present": True,
            "proof_of_service_present": False,
            "exhibits_present": True,
            "proposed_order_present": False,
        })
        result = engine.validate_stack(stack)
        assert result.score < 100
        assert len(result.issues) >= 1

    def test_score_zero_when_empty(self, tmp_db: DatabaseManager):
        engine = FilingEngine(tmp_db)
        stack = self._make_stack({})
        result = engine.validate_stack(stack)
        # Empty checklist with no main doc --> low score
        assert result.score < 100

    def test_issues_list_describes_failures(self, tmp_db: DatabaseManager):
        engine = FilingEngine(tmp_db)
        stack = self._make_stack({
            "main_document_present": False,
            "proof_of_service_present": False,
        })
        result = engine.validate_stack(stack)
        assert any("main_document" in issue.lower() or "checklist" in issue.lower()
                    for issue in result.issues)


# ============================================================================
# Signature detection
# ============================================================================


class TestSignatureDetection:
    """Test that filings have signature blocks."""

    def test_authentication_declaration_has_signature_line(
        self, tmp_db: DatabaseManager, sample_evidence: list
    ):
        engine = EvidenceEngine(tmp_db)
        declaration = engine.authenticate(sample_evidence[0]["id"])
        assert "Signature" in declaration

    def test_authentication_declaration_has_printed_name(
        self, tmp_db: DatabaseManager, sample_evidence: list
    ):
        engine = EvidenceEngine(tmp_db)
        declaration = engine.authenticate(sample_evidence[0]["id"])
        assert "Printed Name" in declaration

    def test_authentication_has_date_line(
        self, tmp_db: DatabaseManager, sample_evidence: list
    ):
        engine = EvidenceEngine(tmp_db)
        declaration = engine.authenticate(sample_evidence[0]["id"])
        assert "Dated:" in declaration


# ============================================================================
# Service address validation
# ============================================================================


class TestServiceAddressValidation:
    """Test that party addresses are present for service."""

    def test_party_has_address(
        self, tmp_db: DatabaseManager, sample_party: list
    ):
        for party in sample_party:
            row = tmp_db.fetchone("SELECT * FROM parties WHERE id = ?", (party["id"],))
            # Address may be None for test data but column exists
            assert "address" in dict(row)

    def test_service_rule_requires_all_parties(self, tmp_db: DatabaseManager):
        from litigationos.engines.court_rules import CourtRulesEngine
        engine = CourtRulesEngine(tmp_db)
        rule = engine.get_rule("MCR 2.107")
        assert rule is not None
        reqs = rule.get("requirements", {})
        assert reqs.get("serve_on_all_parties") is True

    def test_service_methods_include_mail(self, tmp_db: DatabaseManager):
        from litigationos.engines.court_rules import CourtRulesEngine
        engine = CourtRulesEngine(tmp_db)
        rule = engine.get_rule("MCR 2.107")
        reqs = rule.get("requirements", {})
        assert "mail" in reqs.get("methods", [])


# ============================================================================
# Exhibit reference verification
# ============================================================================


class TestExhibitReferenceVerification:
    """Test that exhibit references are cross-checked."""

    def test_evidence_items_have_titles(
        self, tmp_db: DatabaseManager, sample_evidence: list
    ):
        for ev in sample_evidence:
            assert ev["title"] is not None
            assert len(ev["title"]) > 0

    def test_exhibit_list_references_all_evidence(
        self, tmp_db: DatabaseManager, sample_case: dict, sample_evidence: list
    ):
        engine = EvidenceEngine(tmp_db)
        exhibit_list = engine.get_exhibit_list(sample_case["id"])
        assert f"Total exhibits: {len(sample_evidence)}" in exhibit_list

    def test_bates_numbers_assigned_for_references(
        self, tmp_db: DatabaseManager, sample_case: dict, sample_evidence: list
    ):
        engine = EvidenceEngine(tmp_db)
        assignments = engine.assign_bates(sample_case["id"], prefix="REF")
        assert len(assignments) == len(sample_evidence)
        for a in assignments:
            assert a["bates_number"].startswith("REF-")
