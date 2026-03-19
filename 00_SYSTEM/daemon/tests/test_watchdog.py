"""
Unit tests for file watchdog engine.
Tests classification, lane detection, and event handling.
"""
import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from daemon.models import WatchdogConfig
from daemon.watchdog_engine import WatchdogEngine, FileEvent


class TestLaneDetection(unittest.TestCase):
    """Test MEEK lane detection patterns."""

    def setUp(self):
        self.engine = WatchdogEngine(WatchdogConfig())

    def test_lane_E_judicial_misconduct(self):
        self.assertEqual(self.engine._detect_lane(r"C:\JTC_complaint.pdf"), "E")
        self.assertEqual(self.engine._detect_lane(r"C:\mcneill_bias_analysis.md"), "E")
        self.assertEqual(self.engine._detect_lane(r"C:\disqualification_motion.docx"), "E")

    def test_lane_D_ppo(self):
        self.assertEqual(self.engine._detect_lane(r"C:\ppo_evidence.pdf"), "D")
        self.assertEqual(self.engine._detect_lane(r"C:\2023-5907-filing.docx"), "D")
        self.assertEqual(self.engine._detect_lane(r"C:\protection_order.pdf"), "D")

    def test_lane_F_appellate(self):
        self.assertEqual(self.engine._detect_lane(r"C:\coa_brief.pdf"), "F")
        self.assertEqual(self.engine._detect_lane(r"C:\366810_docket.md"), "F")
        self.assertEqual(self.engine._detect_lane(r"C:\appellate_record.pdf"), "F")

    def test_lane_A_custody(self):
        self.assertEqual(self.engine._detect_lane(r"C:\custody_agreement.pdf"), "A")
        self.assertEqual(self.engine._detect_lane(r"C:\2024-001507_motion.docx"), "A")
        self.assertEqual(self.engine._detect_lane(r"C:\best_interest_analysis.md"), "A")

    def test_lane_B_housing(self):
        self.assertEqual(self.engine._detect_lane(r"C:\shady_oaks_complaint.pdf"), "B")
        self.assertEqual(self.engine._detect_lane(r"C:\2025-002760-CZ.docx"), "B")
        self.assertEqual(self.engine._detect_lane(r"C:\rico_claim.pdf"), "B")

    def test_lane_C_convergence(self):
        self.assertEqual(self.engine._detect_lane(r"C:\convergence_analysis.md"), "C")

    def test_lane_unknown(self):
        self.assertIsNone(self.engine._detect_lane(r"C:\random_file.txt"))

    def test_priority_E_over_A(self):
        # Judicial misconduct takes priority over custody
        path = r"C:\mcneill_custody_bias.pdf"
        self.assertEqual(self.engine._detect_lane(path), "E")


class TestDocClassification(unittest.TestCase):
    """Test document type classification."""

    def setUp(self):
        self.engine = WatchdogEngine(WatchdogConfig())

    def test_motion(self):
        self.assertEqual(self.engine._classify_doc(r"C:\motion_to_dismiss.pdf"), "motion")

    def test_brief(self):
        self.assertEqual(self.engine._classify_doc(r"C:\reply_brief.docx"), "brief")

    def test_complaint(self):
        self.assertEqual(self.engine._classify_doc(r"C:\verified_complaint.pdf"), "complaint")

    def test_affidavit(self):
        self.assertEqual(self.engine._classify_doc(r"C:\affidavit_of_andrew.pdf"), "affidavit")

    def test_order(self):
        self.assertEqual(self.engine._classify_doc(r"C:\court_order_2024.pdf"), "order")

    def test_evidence(self):
        self.assertEqual(self.engine._classify_doc(r"C:\exhibit_A.pdf"), "evidence")

    def test_transcript(self):
        self.assertEqual(self.engine._classify_doc(r"C:\hearing_transcript.pdf"), "transcript")

    def test_form(self):
        self.assertEqual(self.engine._classify_doc(r"C:\scao_form_mc01.pdf"), "form")

    def test_unknown(self):
        self.assertIsNone(self.engine._classify_doc(r"C:\random_data.csv"))


class TestFileEvent(unittest.TestCase):
    """Test FileEvent model."""

    def test_event_creation(self):
        event = FileEvent(path=r"C:\test.pdf", event_type="created")
        self.assertEqual(event.event_type, "created")
        self.assertFalse(event.processed)
        self.assertIsNone(event.lane)
        self.assertIsNone(event.doc_type)


class TestWatchdogEngine(unittest.TestCase):
    """Test WatchdogEngine event handling."""

    def test_excluded_files_ignored(self):
        handler = MagicMock()
        config = WatchdogConfig(exclude_patterns=["__pycache__", ".git", "temp"])
        engine = WatchdogEngine(config, on_event=handler)

        engine._handle_event(r"C:\project\__pycache__\file.pyc", "created")
        handler.assert_not_called()

        engine._handle_event(r"C:\project\.git\objects\abc", "created")
        handler.assert_not_called()

    def test_event_classified_and_routed(self):
        events_received = []

        def handler(event):
            events_received.append(event)

        config = WatchdogConfig(auto_classify=True, auto_lane_route=True)
        engine = WatchdogEngine(config, on_event=handler)

        engine._handle_event(r"C:\custody_motion.pdf", "created")

        self.assertEqual(len(events_received), 1)
        self.assertEqual(events_received[0].doc_type, "motion")
        self.assertEqual(events_received[0].lane, "A")

    def test_event_handler_exception_caught(self):
        def bad_handler(event):
            raise RuntimeError("Handler crash")

        logger = MagicMock()
        config = WatchdogConfig()
        engine = WatchdogEngine(config, logger=logger, on_event=bad_handler)

        # Should not raise
        engine._handle_event(r"C:\some_file.pdf", "created")
        logger.error.assert_called()


if __name__ == "__main__":
    unittest.main()
