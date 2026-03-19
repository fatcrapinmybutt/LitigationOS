"""Tests for ContradictionReport generation."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)),
)

from contradiction_detect.statement_extractor import Statement
from contradiction_detect.normalizer import NormalizedStatement, StatementNormalizer
from contradiction_detect.scorer import ScoredContradiction
from contradiction_detect.report_generator import ContradictionReport


def _make_scored(
    text_a: str = "I was at home",
    text_b: str = "I was at work",
    speaker: str = "Andrew Pigors",
    ctype: str = "DIRECT",
    severity: str = "CRITICAL",
    score: float = 75.0,
    impeachment: str = "HIGH",
    date_a: str | None = "2024-03-15",
    date_b: str | None = "2024-09-22",
    source_a: str = "filing_X.pdf",
    source_b: str = "transcript_Y.pdf",
) -> ScoredContradiction:
    """Build a ScoredContradiction for testing."""
    normalizer = StatementNormalizer()

    stmt_a = Statement(text=text_a, speaker=speaker, date=date_a,
                       source_file=source_a, page_number=3)
    stmt_b = Statement(text=text_b, speaker=speaker, date=date_b,
                       source_file=source_b, page_number=12)

    norm_a = normalizer.normalize(stmt_a)
    norm_b = normalizer.normalize(stmt_b)

    return ScoredContradiction(
        statement_a=norm_a,
        statement_b=norm_b,
        contradiction_type=ctype,
        severity=severity,
        explanation=f"{ctype} contradiction detected. Same speaker ({speaker}).",
        evidence_citations=[
            f"[A] {source_a}, p.3",
            f"[B] {source_b}, p.12",
        ],
        severity_score=score,
        impeachment_value=impeachment,
        legal_significance="HIGH",
    )


class TestMarkdownReport(unittest.TestCase):
    """Test markdown rendering."""

    def setUp(self) -> None:
        self.reporter = ContradictionReport()
        self.contradictions = [
            _make_scored(),
            _make_scored(
                text_a="The payment was $500",
                text_b="The payment was $1500",
                ctype="MAGNITUDE",
                severity="MAJOR",
                score=45.0,
                impeachment="MEDIUM",
            ),
        ]

    def test_markdown_has_header(self) -> None:
        md = self.reporter.generate(self.contradictions, fmt="markdown")
        self.assertIn("# Contradiction Analysis Report", md)

    def test_markdown_has_contradictions(self) -> None:
        md = self.reporter.generate(self.contradictions, fmt="markdown")
        self.assertIn("Contradiction #1", md)
        self.assertIn("Contradiction #2", md)

    def test_markdown_has_severity(self) -> None:
        md = self.reporter.generate(self.contradictions, fmt="markdown")
        self.assertIn("CRITICAL", md)
        self.assertIn("MAJOR", md)

    def test_markdown_side_by_side_box(self) -> None:
        md = self.reporter.generate(self.contradictions, fmt="markdown")
        self.assertIn("Statement A", md)
        self.assertIn("Statement B", md)
        self.assertIn("┌", md)
        self.assertIn("┘", md)

    def test_markdown_has_summary(self) -> None:
        md = self.reporter.generate(self.contradictions, fmt="markdown")
        self.assertIn("Summary", md)
        self.assertIn("Total contradictions", md)


class TestJsonReport(unittest.TestCase):
    """Test JSON rendering."""

    def setUp(self) -> None:
        self.reporter = ContradictionReport()
        self.contradictions = [_make_scored()]

    def test_valid_json(self) -> None:
        raw = self.reporter.generate(self.contradictions, fmt="json")
        data = json.loads(raw)
        self.assertIn("report", data)
        self.assertIn("stats", data)

    def test_json_report_entry(self) -> None:
        raw = self.reporter.generate(self.contradictions, fmt="json")
        data = json.loads(raw)
        entry = data["report"][0]
        self.assertEqual(entry["contradiction_type"], "DIRECT")
        self.assertIn("statement_a", entry)
        self.assertIn("statement_b", entry)

    def test_json_stats(self) -> None:
        raw = self.reporter.generate(self.contradictions, fmt="json")
        data = json.loads(raw)
        stats = data["stats"]
        self.assertEqual(stats["total"], 1)
        self.assertIn("by_type", stats)
        self.assertIn("by_severity", stats)
        self.assertIn("by_speaker", stats)


class TestHtmlReport(unittest.TestCase):
    """Test HTML rendering."""

    def setUp(self) -> None:
        self.reporter = ContradictionReport()
        self.contradictions = [_make_scored()]

    def test_html_structure(self) -> None:
        html = self.reporter.generate(self.contradictions, fmt="html")
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("<table>", html)
        self.assertIn("Contradiction Report", html)

    def test_html_has_severity_color(self) -> None:
        html = self.reporter.generate(self.contradictions, fmt="html")
        self.assertIn("#ff4444", html)  # CRITICAL color


class TestExhibitGeneration(unittest.TestCase):
    """Test court exhibit dict generation."""

    def setUp(self) -> None:
        self.reporter = ContradictionReport()

    def test_exhibit_keys(self) -> None:
        sc = _make_scored()
        exhibit = self.reporter.generate_exhibit(sc)
        expected_keys = {
            "exhibit_type", "contradiction_type", "severity",
            "severity_score", "impeachment_value",
            "statement_a", "statement_b",
            "explanation", "citations", "generated_at",
        }
        self.assertTrue(expected_keys.issubset(exhibit.keys()))
        self.assertEqual(exhibit["exhibit_type"], "CONTRADICTION")


class TestSummaryStats(unittest.TestCase):
    """Test summary statistics calculation."""

    def setUp(self) -> None:
        self.reporter = ContradictionReport()
        self.contradictions = [
            _make_scored(severity="CRITICAL", score=80.0),
            _make_scored(severity="MAJOR", score=40.0, ctype="TEMPORAL"),
            _make_scored(severity="MINOR", score=15.0, ctype="MAGNITUDE"),
        ]

    def test_total_count(self) -> None:
        stats = self.reporter.summary_stats(self.contradictions)
        self.assertEqual(stats["total"], 3)

    def test_by_type_breakdown(self) -> None:
        stats = self.reporter.summary_stats(self.contradictions)
        self.assertEqual(stats["by_type"]["DIRECT"], 1)
        self.assertEqual(stats["by_type"]["TEMPORAL"], 1)
        self.assertEqual(stats["by_type"]["MAGNITUDE"], 1)

    def test_by_severity_breakdown(self) -> None:
        stats = self.reporter.summary_stats(self.contradictions)
        self.assertEqual(stats["by_severity"]["CRITICAL"], 1)
        self.assertEqual(stats["by_severity"]["MAJOR"], 1)
        self.assertEqual(stats["by_severity"]["MINOR"], 1)

    def test_avg_score(self) -> None:
        stats = self.reporter.summary_stats(self.contradictions)
        self.assertAlmostEqual(stats["avg_severity_score"], 45.0, places=1)

    def test_empty_stats(self) -> None:
        stats = self.reporter.summary_stats([])
        self.assertEqual(stats["total"], 0)
        self.assertEqual(stats["avg_severity_score"], 0.0)


class TestDbStorage(unittest.TestCase):
    """Test persisting reports to SQLite."""

    def test_store_and_read_back(self) -> None:
        import sqlite3
        reporter = ContradictionReport()
        sc = _make_scored()

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            count = reporter.store_to_db([sc], lane="A", db_path=db_path)
            self.assertEqual(count, 1)

            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM contradiction_reports").fetchall()
            conn.close()

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["contradiction_type"], "DIRECT")
            self.assertEqual(rows[0]["severity"], "CRITICAL")
            self.assertEqual(rows[0]["lane"], "A")
        finally:
            os.unlink(db_path)


if __name__ == "__main__":
    unittest.main()
