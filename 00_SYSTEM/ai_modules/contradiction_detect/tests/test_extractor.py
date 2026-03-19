"""Tests for StatementExtractor."""
from __future__ import annotations

import sys
import os
import unittest

# Ensure the package is importable
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)),
)

from contradiction_detect.statement_extractor import StatementExtractor, Statement


class TestStatementExtraction(unittest.TestCase):
    """Verify that attributed statements are correctly extracted."""

    def setUp(self) -> None:
        self.extractor = StatementExtractor()

    def test_basic_testified(self) -> None:
        text = "Mr. Pigors testified that he was at home on March 15, 2024."
        stmts = self.extractor.extract_statements(text, {"file_path": "depo.txt"})
        self.assertTrue(len(stmts) >= 1)
        self.assertIn("testified", stmts[0].text.lower())

    def test_speaker_identification_pigors(self) -> None:
        text = "Andrew Pigors stated that the children were in his custody during that week."
        stmts = self.extractor.extract_statements(text, {})
        self.assertTrue(len(stmts) >= 1)
        self.assertEqual(stmts[0].speaker, "Andrew Pigors")

    def test_speaker_identification_watson(self) -> None:
        text = "Watson declared under oath that she had primary custody."
        stmts = self.extractor.extract_statements(text, {})
        self.assertTrue(len(stmts) >= 1)
        self.assertEqual(stmts[0].speaker, "Opposing Party")

    def test_speaker_identification_judge(self) -> None:
        text = "Judge McNeill stated that the motion was denied."
        stmts = self.extractor.extract_statements(text, {})
        self.assertTrue(len(stmts) >= 1)
        self.assertEqual(stmts[0].speaker, "Judge McNeill")

    def test_date_extraction_from_text(self) -> None:
        text = "Pigors testified on January 10, 2024 that he filed the paperwork."
        stmts = self.extractor.extract_statements(text, {})
        self.assertTrue(len(stmts) >= 1)
        self.assertIsNotNone(stmts[0].date)
        self.assertIn("2024", stmts[0].date)

    def test_date_from_metadata_fallback(self) -> None:
        text = "Mr. Pigors declared that the agreement was already signed."
        meta = {"date": "2024-06-01", "file_path": "decl.pdf"}
        stmts = self.extractor.extract_statements(text, meta)
        self.assertTrue(len(stmts) >= 1)
        self.assertEqual(stmts[0].date, "2024-06-01")

    def test_multiple_statements_one_paragraph(self) -> None:
        text = (
            "Watson claimed that she was at home. "
            "She also alleged that Pigors was absent. "
            "The witness testified that the door was open."
        )
        stmts = self.extractor.extract_statements(text, {})
        self.assertGreaterEqual(len(stmts), 2, "Should extract multiple statements")

    def test_short_text_ignored(self) -> None:
        text = "He said yes."
        stmts = self.extractor.extract_statements(text, {})
        self.assertEqual(len(stmts), 0, "Very short statements should be skipped")

    def test_empty_text(self) -> None:
        stmts = self.extractor.extract_statements("", {})
        self.assertEqual(stmts, [])

    def test_sworn_detection(self) -> None:
        text = "In his sworn affidavit, Pigors stated that he was employed full-time."
        stmts = self.extractor.extract_statements(text, {})
        self.assertTrue(len(stmts) >= 1)
        self.assertTrue(stmts[0].is_sworn)

    def test_source_file_metadata(self) -> None:
        text = "Watson testified that she received no notice of the hearing date."
        meta = {"file_path": "transcript_2024.pdf", "page_number": 42}
        stmts = self.extractor.extract_statements(text, meta)
        self.assertTrue(len(stmts) >= 1)
        self.assertEqual(stmts[0].source_file, "transcript_2024.pdf")
        self.assertEqual(stmts[0].page_number, 42)


if __name__ == "__main__":
    unittest.main()
