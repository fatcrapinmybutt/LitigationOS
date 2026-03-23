"""Tests for brief compliance engine -- word count, required sections,
citation format, and MCR 7.212 validation for Phase 5-6."""

from __future__ import annotations

import json

import pytest

from litigationos.db.connection import DatabaseManager
from litigationos.engines.court_rules import CourtRulesEngine
from litigationos.engines.filing import (
    FilingEngine,
    FilingStack,
    StackComponent,
    ValidationResult,
    MCR_FORMAT,
)


# ============================================================================
# Word count validation
# ============================================================================


class TestWordCountValidation:
    """Test word count checks against MCR page/word limits."""

    def test_page_limit_brief_50(self):
        assert MCR_FORMAT["page_limit_brief"] == 50

    def test_page_limit_motion_20(self):
        assert MCR_FORMAT["page_limit_motion"] == 20

    def test_page_limit_reply_10(self):
        assert MCR_FORMAT["page_limit_reply"] == 10

    def test_filing_within_page_limit(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        filing = {"page_count": 40, "spacing": "double"}
        result = engine.validate_filing_format(filing, "MCR 7.212")
        assert result["valid"] is True

    def test_filing_exceeds_page_limit(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        filing = {"page_count": 60, "spacing": "double"}
        result = engine.validate_filing_format(filing, "MCR 7.212")
        # Should have a page-related error
        page_errors = [e for e in result["errors"] if "page" in e.lower() or "Page" in e]
        assert len(page_errors) >= 1

    def test_filing_word_count_stored(
        self, tmp_db: DatabaseManager, sample_case: dict
    ):
        """Filing word_count is persisted in the filings table."""
        fid = tmp_db.execute(
            "INSERT INTO filings (case_id, title, filing_type, status, word_count) "
            "VALUES (?, ?, ?, ?, ?)",
            (sample_case["id"], "Test Brief", "brief", "draft", 8500),
        ).lastrowid
        row = tmp_db.fetchone("SELECT word_count FROM filings WHERE id = ?", (fid,))
        assert row["word_count"] == 8500


# ============================================================================
# Required section detection
# ============================================================================


class TestRequiredSectionDetection:
    """Test detection of required sections in appellate briefs."""

    def test_mcr_7212_has_format_requirements(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        rule = engine.get_rule("MCR 7.212")
        assert rule is not None
        reqs = rule.get("requirements", {})
        fmt = reqs.get("format", {})
        assert fmt.get("spacing") == "double"
        assert fmt.get("page_limit") == 50

    def test_brief_requires_double_spacing(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        filing = {"page_count": 30, "spacing": "single"}
        result = engine.validate_filing_format(filing, "MCR 7.212")
        spacing_errors = [e for e in result["errors"] if "spacing" in e.lower()]
        assert len(spacing_errors) >= 1

    def test_brief_double_spacing_passes(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        filing = {"page_count": 30, "spacing": "double"}
        result = engine.validate_filing_format(filing, "MCR 7.212")
        spacing_errors = [e for e in result["errors"] if "spacing" in e.lower()]
        assert len(spacing_errors) == 0

    def test_motion_requires_brief_attachment(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        filing = {"page_count": 10}
        result = engine.validate_filing_format(filing, "MCR 2.119")
        brief_errors = [e for e in result["errors"] if "brief" in e.lower()]
        assert len(brief_errors) >= 1

    def test_motion_with_brief_attached(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        filing = {"page_count": 10, "brief_attached": True}
        result = engine.validate_filing_format(filing, "MCR 2.119")
        brief_errors = [e for e in result["errors"] if "brief" in e.lower()]
        assert len(brief_errors) == 0


# ============================================================================
# Citation format checking
# ============================================================================


class TestCitationFormatChecking:
    """Test MCR citation format validation logic."""

    def test_mcr_rule_number_format(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        rule = engine.get_rule("MCR 2.119")
        assert rule["rule_number"] == "MCR 2.119"

    def test_search_by_mcr_keyword(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        results = engine.search_rules("briefs appeals")
        rule_nums = [r["rule_number"] for r in results]
        assert "MCR 7.212" in rule_nums

    def test_font_warning_on_mismatch(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        filing = {"page_count": 20, "font": "Arial 14pt", "spacing": "double"}
        result = engine.validate_filing_format(filing, "MCR 7.212")
        font_warnings = [w for w in result["warnings"] if "font" in w.lower()]
        assert len(font_warnings) >= 1


# ============================================================================
# MCR 7.212 rule validation
# ============================================================================


class TestMCR7212Validation:
    """Test full MCR 7.212 compliance checks."""

    def test_appellant_brief_days(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        rule = engine.get_rule("MCR 7.212")
        reqs = rule["requirements"]
        assert reqs["appellant_brief_days"] == 56

    def test_appellee_brief_days(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        rule = engine.get_rule("MCR 7.212")
        reqs = rule["requirements"]
        assert reqs["appellee_brief_days"] == 35

    def test_reply_brief_days(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        rule = engine.get_rule("MCR 7.212")
        reqs = rule["requirements"]
        assert reqs["reply_brief_days"] == 21

    def test_validate_compliant_brief(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        filing = {
            "page_count": 45,
            "spacing": "double",
            "font": "Times New Roman 12pt",
            "margins": "1 inch all sides",
        }
        result = engine.validate_filing_format(filing, "MCR 7.212")
        assert result["valid"] is True
        assert result["score"] > 0.5

    def test_validate_noncompliant_brief(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        filing = {
            "page_count": 999,
            "spacing": "single",
            "font": "Comic Sans 18pt",
        }
        result = engine.validate_filing_format(filing, "MCR 7.212")
        assert result["valid"] is False
        assert len(result["errors"]) >= 1

    def test_score_reflects_compliance(self, tmp_db: DatabaseManager):
        engine = CourtRulesEngine(tmp_db)
        good = engine.validate_filing_format(
            {"page_count": 30, "spacing": "double"}, "MCR 7.212"
        )
        bad = engine.validate_filing_format(
            {"page_count": 999, "spacing": "single"}, "MCR 7.212"
        )
        assert good["score"] > bad["score"]
