"""
Contract tests for shared.internal.fts5 — FTS5 query sanitization.

These tests lock the behavior that prevents FTS5 crashes from legal citations.
Every legal citation pattern that has crashed a session in the past is tested.
"""

import sys
from pathlib import Path

# Add 00_SYSTEM to path
_system_dir = str(Path(__file__).resolve().parent.parent.parent)
if _system_dir not in sys.path:
    sys.path.insert(0, _system_dir)

from shared import sanitize_fts5


class TestSanitizeBasic:
    """Contract: basic sanitization behavior."""

    def test_empty_returns_empty(self):
        assert sanitize_fts5("") == ""

    def test_none_returns_empty(self):
        assert sanitize_fts5(None) == ""

    def test_simple_word_preserved(self):
        result = sanitize_fts5("custody")
        assert "custody" in result

    def test_two_words_preserved(self):
        result = sanitize_fts5("parental alienation")
        assert "parental" in result
        assert "alienation" in result


class TestSanitizeLegalCitations:
    """Contract: legal citations that crash FTS5 are neutralized."""

    def test_strips_periods(self):
        """MCR 2.003 → no period remains."""
        result = sanitize_fts5("MCR 2.003")
        assert "." not in result
        assert "MCR" in result

    def test_strips_parentheses(self):
        """MCL 722.23(j) → no parens remain."""
        result = sanitize_fts5("MCL 722.23(j)")
        assert "(" not in result
        assert ")" not in result
        assert "MCL" in result

    def test_strips_section_sign(self):
        """42 USC §1983 → no § remains."""
        result = sanitize_fts5("42 USC §1983")
        assert "§" not in result

    def test_complex_citation(self):
        """MCR 2.003(C)(1)(b) → cleaned but tokens preserved."""
        result = sanitize_fts5("MCR 2.003(C)(1)(b)")
        assert "(" not in result
        assert ")" not in result
        assert "." not in result
        assert "MCR" in result

    def test_colons_stripped(self):
        """Colons from time/citation formats stripped."""
        result = sanitize_fts5("filed: 2024-01-15")
        assert ":" not in result


class TestSanitizePreservation:
    """Contract: things that SHOULD be preserved ARE preserved."""

    def test_preserves_quoted_phrases(self):
        """Quoted phrases pass through intact."""
        result = sanitize_fts5('"parental alienation" OR custody')
        assert '"parental alienation"' in result

    def test_preserves_wildcards(self):
        """Prefix wildcards (custod*) pass through."""
        result = sanitize_fts5("custod*")
        assert "custod*" in result

    def test_preserves_and_operator(self):
        result = sanitize_fts5("custody AND alienation")
        assert "AND" in result

    def test_preserves_or_operator(self):
        result = sanitize_fts5("custody OR parenting")
        assert "OR" in result

    def test_preserves_not_operator(self):
        result = sanitize_fts5("custody NOT dismissed")
        assert "NOT" in result


class TestSanitizeEdgeCases:
    """Contract: edge cases don't crash or produce garbage."""

    def test_only_special_chars(self):
        """String of only special chars → empty."""
        result = sanitize_fts5("...()()")
        assert result == ""

    def test_single_char_dropped(self):
        """Single-character tokens are dropped (noise)."""
        result = sanitize_fts5("a b c")
        # Single chars below 2-char threshold are dropped
        assert result.strip() == ""

    def test_multiple_spaces_collapsed(self):
        """Multiple spaces collapse to single spaces."""
        result = sanitize_fts5("custody    alienation")
        assert "  " not in result

    def test_real_world_query(self):
        """A real query from LitigationOS sessions."""
        result = sanitize_fts5('MCL 722.23(j) AND "parental alienation"')
        assert '"parental alienation"' in result
        assert "AND" in result
        assert "(" not in result
        assert "." not in result
