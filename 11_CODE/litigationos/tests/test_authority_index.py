"""Tests for authority index engine -- citation search (FTS5), citation
graph traversal, authority verification, and Michigan format validation
for Phase 5-6."""

from __future__ import annotations

import json

import pytest

from litigationos.db.connection import DatabaseManager
from litigationos.engines.court_rules import CourtRulesEngine, _MCR_SEED


# ============================================================================
# Citation search (FTS5)
# ============================================================================


class TestCitationSearch:
    """Test FTS5 search across court rules."""

    def test_search_motion_returns_results(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        results = engine.search_rules("motion")
        assert len(results) >= 1

    def test_search_appeal_returns_results(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        results = engine.search_rules("appeal")
        assert len(results) >= 1

    def test_search_brief_returns_results(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        results = engine.search_rules("brief")
        assert len(results) >= 1

    def test_search_returns_rule_number(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        results = engine.search_rules("summons expiration")
        assert any(r["rule_number"] == "MCR 2.105" for r in results)

    def test_search_no_results_for_gibberish(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        results = engine.search_rules("zzxqwvnm99999")
        assert results == []

    def test_search_category_filter(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        results = engine.search_rules("appeal brief", category="appeal")
        for r in results:
            assert r["category"] == "appeal"


# ============================================================================
# Citation graph traversal
# ============================================================================


class TestCitationGraph:
    """Test cross-references between court rules."""

    def test_mcr_7306_references_7212(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        rule = engine.get_rule("MCR 7.306")
        assert rule is not None
        reqs = rule.get("requirements", {})
        assert reqs.get("format_rule") == "MCR 7.212(B)"

    def test_cross_application_references_7302(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        rule = engine.get_rule("MCR 7.303")
        assert rule is not None
        full_text = rule.get("full_text", "")
        assert "MCR 7.302" in full_text

    def test_service_rules_linked(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        rule = engine.get_rule("MCR 3.206")
        assert rule is not None
        full_text = rule.get("full_text", "")
        assert "MCR 2.105" in full_text

    def test_applicable_rules_returns_related(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        rules = engine.get_applicable_rules("complaint", court_type="circuit")
        rule_nums = [r["rule_number"] for r in rules]
        # Complaint should pull service and response rules
        assert any("2.10" in rn for rn in rule_nums)


# ============================================================================
# Authority verification
# ============================================================================


class TestAuthorityVerification:
    """Test rule lookup and verification."""

    def test_verify_existing_rule(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        rule = engine.get_rule("MCR 2.119")
        assert rule is not None
        assert rule["title"] == "Motion Practice"

    def test_verify_nonexistent_rule(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        rule = engine.get_rule("MCR 99.999")
        assert rule is None

    def test_all_seed_rules_verifiable(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        for seed in _MCR_SEED:
            rule = engine.get_rule(seed["rule_number"])
            assert rule is not None, f"Seed rule {seed['rule_number']} not found"

    def test_rule_has_full_text(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        rule = engine.get_rule("MCR 2.108")
        assert rule is not None
        assert len(rule.get("full_text", "")) > 50


# ============================================================================
# Michigan format validation
# ============================================================================


class TestMichiganFormatValidation:
    """Test Michigan-specific formatting validation."""

    def test_validate_margins_warning(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        filing = {"page_count": 30, "margins": "0.5 inch", "spacing": "double"}
        result = engine.validate_filing_format(filing, "MCR 7.212")
        margin_warnings = [w for w in result["warnings"] if "margin" in w.lower()]
        assert len(margin_warnings) >= 1

    def test_validate_correct_margins_no_warning(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        filing = {
            "page_count": 30,
            "margins": "1 inch all sides",
            "spacing": "double",
        }
        result = engine.validate_filing_format(filing, "MCR 7.212")
        margin_warnings = [w for w in result["warnings"] if "margin" in w.lower()]
        assert len(margin_warnings) == 0

    def test_family_rule_requires_verified_statement(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        filing = {"page_count": 10}
        result = engine.validate_filing_format(filing, "MCR 3.206")
        vs_errors = [e for e in result["errors"] if "verified statement" in e.lower()]
        assert len(vs_errors) >= 1

    def test_family_rule_with_verified_statement(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        filing = {"page_count": 10, "verified_statement": True}
        result = engine.validate_filing_format(filing, "MCR 3.206")
        vs_errors = [e for e in result["errors"] if "verified statement" in e.lower()]
        assert len(vs_errors) == 0
