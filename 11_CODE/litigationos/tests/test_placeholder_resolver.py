"""Tests for placeholder resolver engine -- pattern detection, DB
cross-reference, auto-resolution, and ANDREW_REQUIRED tagging
for Phase 5-6."""

from __future__ import annotations

import re

import pytest

from litigationos.db.connection import DatabaseManager
from litigationos.engines.settings import SettingsEngine


# ============================================================================
# Pattern detection
# ============================================================================


class TestPlaceholderPatternDetection:
    """Test detection of placeholder patterns in text."""

    _PLACEHOLDER_RE = re.compile(r"\{\{\s*(\w+)\s*\}\}")
    _BRACKET_RE = re.compile(r"\[([A-Z_]+)\]")

    def test_detect_jinja_placeholders(self):
        text = "IN THE {{ court_name }} COUNTY OF {{ county }}"
        matches = self._PLACEHOLDER_RE.findall(text)
        assert "court_name" in matches
        assert "county" in matches

    def test_detect_bracket_placeholders(self):
        text = "Case No. [CASE_NUMBER] filed by [PARTY_NAME]"
        matches = self._BRACKET_RE.findall(text)
        assert "CASE_NUMBER" in matches
        assert "PARTY_NAME" in matches

    def test_no_placeholders_in_clean_text(self):
        text = "This is a clean sentence with no placeholders."
        jinja = self._PLACEHOLDER_RE.findall(text)
        bracket = self._BRACKET_RE.findall(text)
        assert jinja == []
        assert bracket == []

    def test_mixed_placeholders(self):
        text = "{{ judge_name }} presiding over [CASE_NUMBER]"
        jinja = self._PLACEHOLDER_RE.findall(text)
        bracket = self._BRACKET_RE.findall(text)
        assert "judge_name" in jinja
        assert "CASE_NUMBER" in bracket

    def test_nested_braces_ignored(self):
        text = "Value is {not_a_placeholder} but {{ real_one }} is."
        matches = self._PLACEHOLDER_RE.findall(text)
        assert matches == ["real_one"]


# ============================================================================
# DB cross-reference
# ============================================================================


class TestDBCrossReference:
    """Test resolving placeholders from database values."""

    def test_resolve_jurisdiction_state(self, tmp_db: DatabaseManager):
        engine = SettingsEngine(tmp_db)
        val = engine.get("jurisdiction.state")
        assert val == "MI"

    def test_resolve_jurisdiction_county(self, tmp_db: DatabaseManager):
        engine = SettingsEngine(tmp_db)
        val = engine.get("jurisdiction.county")
        assert val == "Muskegon"

    def test_resolve_jurisdiction_court(self, tmp_db: DatabaseManager):
        engine = SettingsEngine(tmp_db)
        val = engine.get("jurisdiction.court")
        assert val == "14th Circuit"

    def test_resolve_case_title(
        self, tmp_db: DatabaseManager, sample_case: dict
    ):
        row = tmp_db.fetchone("SELECT title FROM cases WHERE id = ?", (sample_case["id"],))
        assert row["title"] == "Pigors v. Watson"

    def test_resolve_party_name(
        self, tmp_db: DatabaseManager, sample_party: list
    ):
        names = [p["name"] for p in sample_party]
        assert "Andre Pigors" in names
        assert "Jane Watson" in names


# ============================================================================
# Auto-resolution
# ============================================================================


class TestAutoResolution:
    """Test automatic placeholder resolution using settings/case data."""

    def test_auto_resolve_state(self, tmp_db: DatabaseManager):
        engine = SettingsEngine(tmp_db)
        template = "State of {{ state }}"
        state = engine.get("jurisdiction.state")
        resolved = template.replace("{{ state }}", state or "")
        assert resolved == "State of MI"

    def test_auto_resolve_county(self, tmp_db: DatabaseManager):
        engine = SettingsEngine(tmp_db)
        template = "County of {{ county }}"
        county = engine.get("jurisdiction.county")
        resolved = template.replace("{{ county }}", county or "")
        assert resolved == "County of Muskegon"

    def test_auto_resolve_court(self, tmp_db: DatabaseManager):
        engine = SettingsEngine(tmp_db)
        template = "{{ court }} Court"
        court = engine.get("jurisdiction.court")
        resolved = template.replace("{{ court }}", court or "")
        assert resolved == "14th Circuit Court"

    def test_unresolved_placeholder_remains(self, tmp_db: DatabaseManager):
        engine = SettingsEngine(tmp_db)
        template = "Filed by {{ unknown_party }}"
        val = engine.get("unknown_party")
        if val is None:
            # Placeholder not resolved
            assert "{{ unknown_party }}" in template


# ============================================================================
# ANDREW_REQUIRED tagging
# ============================================================================


class TestAndrewRequiredTagging:
    """Test tagging unresolved placeholders as ANDREW_REQUIRED."""

    _PLACEHOLDER_RE = re.compile(r"\{\{\s*(\w+)\s*\}\}")

    def _tag_unresolved(self, text: str, resolved: dict) -> str:
        """Replace unresolved placeholders with ANDREW_REQUIRED tags."""
        def replacer(match):
            key = match.group(1)
            if key in resolved and resolved[key]:
                return str(resolved[key])
            return f"[ANDREW_REQUIRED: {key}]"
        return self._PLACEHOLDER_RE.sub(replacer, text)

    def test_tag_resolved_values(self):
        text = "State: {{ state }}, County: {{ county }}"
        result = self._tag_unresolved(text, {"state": "MI", "county": "Muskegon"})
        assert result == "State: MI, County: Muskegon"

    def test_tag_unresolved_values(self):
        text = "Judge: {{ judge_name }}"
        result = self._tag_unresolved(text, {})
        assert result == "Judge: [ANDREW_REQUIRED: judge_name]"

    def test_tag_mixed_resolved_unresolved(self):
        text = "{{ state }} court, Judge {{ judge }}"
        result = self._tag_unresolved(text, {"state": "MI"})
        assert "MI" in result
        assert "[ANDREW_REQUIRED: judge]" in result

    def test_no_tags_when_all_resolved(self):
        text = "Case: {{ case_title }}"
        result = self._tag_unresolved(text, {"case_title": "Pigors v. Watson"})
        assert "ANDREW_REQUIRED" not in result

    def test_multiple_unresolved_tags(self):
        text = "{{ a }} and {{ b }} and {{ c }}"
        result = self._tag_unresolved(text, {})
        assert result.count("ANDREW_REQUIRED") == 3
