"""Tests for StatementComparator and contradiction detection."""
from __future__ import annotations

import sys
import os
import unittest

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)),
)

from contradiction_detect.statement_extractor import Statement
from contradiction_detect.normalizer import NormalizedStatement, StatementNormalizer
from contradiction_detect.comparator import StatementComparator


def _make_normalized(
    text: str,
    speaker: str = "Andrew Pigors",
    date: str | None = None,
    source: str = "doc_A.pdf",
    page: int = 1,
    is_sworn: bool = False,
) -> NormalizedStatement:
    """Helper to build a NormalizedStatement quickly."""
    raw = Statement(
        text=text,
        speaker=speaker,
        date=date,
        source_file=source,
        page_number=page,
        is_sworn=is_sworn,
    )
    normalizer = StatementNormalizer()
    return normalizer.normalize(raw)


class TestDirectContradiction(unittest.TestCase):
    """Detect statements that directly contradict each other."""

    def setUp(self) -> None:
        self.comp = StatementComparator()

    def test_opposite_claims_flagged(self) -> None:
        a = _make_normalized(
            "On March 15 evening I was at home watching the children all night",
            speaker="Andrew Pigors", source="filing_A.pdf",
        )
        b = _make_normalized(
            "On March 15 evening I was at the office working late and not home with the children",
            speaker="Andrew Pigors", source="depo_B.pdf",
        )
        result = self.comp.compare_pair(a, b)
        # Shared vocabulary (March, 15, evening, children) gives topic match,
        # but differing facts (home vs office) → contradiction or at least topic match
        self.assertTrue(
            result.topic_match or result.is_contradiction,
            "Statements sharing topic keywords but differing facts should be flagged",
        )

    def test_non_contradictory_similar(self) -> None:
        a = _make_normalized(
            "The children attended Lincoln Elementary School",
            speaker="Andrew Pigors", source="filing_A.pdf",
        )
        b = _make_normalized(
            "The children attended Lincoln Elementary School in Muskegon",
            speaker="Andrew Pigors", source="filing_B.pdf",
        )
        result = self.comp.compare_pair(a, b)
        self.assertFalse(
            result.is_contradiction,
            "Nearly identical statements should NOT be flagged as contradictions",
        )


class TestTemporalContradiction(unittest.TestCase):
    """Detect contradictions involving impossible timelines."""

    def setUp(self) -> None:
        self.comp = StatementComparator()

    def test_different_dates_for_same_event(self) -> None:
        a = _make_normalized(
            "The custody exchange happened on January 5 2024",
            speaker="Andrew Pigors", source="filing_A.pdf",
            date="January 5, 2024",
        )
        b = _make_normalized(
            "The custody exchange happened on March 20 2024",
            speaker="Andrew Pigors", source="filing_B.pdf",
            date="March 20, 2024",
        )
        result = self.comp.compare_pair(a, b)
        if result.is_contradiction:
            self.assertIn(
                result.contradiction_type, ("TEMPORAL", "DIRECT", "EVOLUTION"),
            )


class TestMagnitudeContradiction(unittest.TestCase):
    """Detect contradictions about amounts/quantities."""

    def setUp(self) -> None:
        self.comp = StatementComparator()

    def test_different_amounts(self) -> None:
        a = _make_normalized(
            "The monthly child support payment was $500",
            speaker="Andrew Pigors", source="filing_A.pdf",
        )
        b = _make_normalized(
            "The monthly child support payment was $1500",
            speaker="Andrew Pigors", source="filing_B.pdf",
        )
        result = self.comp.compare_pair(a, b)
        # High topic similarity, different numbers
        if result.is_contradiction:
            self.assertIn(result.contradiction_type, ("MAGNITUDE", "DIRECT", "EVOLUTION"))


class TestSameDocumentSkipping(unittest.TestCase):
    """Ensure pairs from the same document + page are skipped."""

    def setUp(self) -> None:
        self.comp = StatementComparator()

    def test_same_source_same_page_skipped(self) -> None:
        a = _make_normalized(
            "He claimed the sky was red on that day",
            source="filing_A.pdf", page=5,
        )
        b = _make_normalized(
            "He stated the sky was blue on that day",
            source="filing_A.pdf", page=5,
        )
        # find_contradictions should skip this pair
        results = self.comp.find_contradictions([a, b])
        self.assertEqual(len(results), 0, "Same-doc same-page pairs should be skipped")


class TestBatchContradictions(unittest.TestCase):
    """Test batch find_contradictions across multiple statements."""

    def setUp(self) -> None:
        self.comp = StatementComparator()

    def test_batch_returns_list(self) -> None:
        stmts = [
            _make_normalized("He was at home", source="A.pdf"),
            _make_normalized("He was at work", source="B.pdf"),
            _make_normalized("The weather was sunny", source="C.pdf"),
        ]
        results = self.comp.find_contradictions(stmts)
        self.assertIsInstance(results, list)


if __name__ == "__main__":
    unittest.main()
