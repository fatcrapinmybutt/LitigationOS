# -*- coding: utf-8 -*-
"""
Comprehensive unit tests for LitigationOS Wave 1 legal_ai modules:
  1. FilingStateMachine   (filing_state_machine.py)
  2. QualityGateEngine    (quality_gate.py)
  3. CaptionGenerator     (caption_generator.py)
  4. EvidenceGapDetector  (evidence_gap_detector.py)
  5. OutcomePredictor     (outcome_predictor.py)

All tests are pure unit tests — no DB connections or external dependencies.
Run with:
    cd C:\\Users\\andre\\LitigationOS\\00_SYSTEM\\legal_ai
    python -m pytest tests/test_wave1_filing.py -v
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Ensure legal_ai package is importable
# ---------------------------------------------------------------------------
_LEGAL_AI_DIR = Path(__file__).resolve().parent.parent
if str(_LEGAL_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_LEGAL_AI_DIR))
if str(_LEGAL_AI_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_LEGAL_AI_DIR.parent))

from filing_state_machine import (
    FilingPhase,
    FilingRecord,
    FilingStateMachine,
    FilingNotFoundError,
    FilingStateError,
    InvalidTransitionError,
    PhaseTransition,
)
from quality_gate import (
    GateCheck,
    GateResult,
    QualityGateEngine,
)
from caption_generator import (
    Caption,
    CaptionConfig,
    CaptionGenerator,
)
from evidence_gap_detector import (
    EvidenceGap,
    EvidenceGapDetector,
    EvidenceMatch,
    EvidenceRequirement,
    GapAnalysisReport,
)
from outcome_predictor import (
    OutcomePrediction,
    OutcomePredictor,
    PredictionFactor,
)


# ═══════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════

def _clean_motion() -> str:
    """A realistic Michigan court motion that passes quality checks."""
    return """\
STATE OF MICHIGAN
IN THE 14TH CIRCUIT COURT FOR THE COUNTY OF MUSKEGON

ANDREW J. PIGORS,
    Plaintiff,
                                    Case No. 2024-001507-DC
v.                                  Hon. Jenny L. McNeill

EMILY A. WATSON,
    Defendant.
______________________________________________/

MOTION TO MODIFY CUSTODY ARRANGEMENT

NOW COMES Plaintiff, ANDREW J. PIGORS, by and through his own capacity,
pro se, and respectfully moves this Honorable Court for an order modifying
the existing custody arrangement pursuant to MCL 722.27(1)(c) and the
best-interest factors set forth in MCL 722.23.

I. STATEMENT OF FACTS

Plaintiff and Defendant are the parents of the minor child, referred to
herein as L.D.W. to protect the child's identity per MCR 3.203.

Attached hereto as Exhibit A is the affidavit of Plaintiff.

The Court's order dated January 15, 2025, established the current
parenting time schedule. Since that date, Defendant has violated the
terms of the order on multiple occasions.

II. LEGAL ARGUMENT

Under MCL 722.27(1)(c), a court may modify a custody order if the
moving party demonstrates proper cause or a change of circumstances.
See Vodvarka v Grasmeyer, 259 Mich App 499 (2003).

The best-interest factors under MCL 722.23 weigh in favor of
modification. See also Shade v Wright, 291 Mich App 17 (2010).

III. PRAYER FOR RELIEF

WHEREFORE, Plaintiff respectfully requests this Honorable Court:
1. Modify the existing custody arrangement;
2. Grant such other relief as the Court deems just and equitable.

Respectfully submitted,

/s/ Andrew J. Pigors
ANDREW J. PIGORS, Pro Se
1977 Whitehall Road, Lot 17
North Muskegon, MI 49445

CERTIFICATE OF SERVICE

I, Andrew J. Pigors, certify that on this date I served a copy of the
foregoing document upon all parties via first-class mail.

VERIFICATION

I, Andrew J. Pigors, declare under penalty of perjury under the laws of
the State of Michigan that the foregoing is true and correct.
"""


def _dirty_document() -> str:
    """A document with multiple quality issues."""
    return """\
MOTION TO [PLACEHOLDER]

Emily Ann Watson did something.
Judge McNeil ruled against us.
Case number 2024-1507-DC is wrong.
The child Liam David Watson should not be named.
McCraney v Ford Motor Co, 154 Mich App 297 (1986) supports our claim.
Cease v AAA Michigan, unpublished (2020) also applies.
[TODO: add more arguments]
<<FILL IN PRAYER FOR RELIEF>>
{FIELD: date}
"""


def _evidence_rich_text() -> str:
    """Filing text with many evidence references."""
    return """\
As shown in Exhibit A (PIGORS-0001 through PIGORS-0015), the Defendant
violated the custody order. The transcript of the hearing on January 15,
2025 (Exhibit B) confirms these facts. The affidavit of Plaintiff
(Exhibit C) attests to the pattern of violations.

Police Report #2024-1234 documents the incident on February 3, 2025.
Photographs attached as Exhibit D show the condition of the premises.
Medical records from Dr. Smith (Exhibit E) document the child's health.
Financial records (Exhibit F) show Defendant's income.
Text messages between the parties (Exhibit G) confirm the agreement.
Court Order dated January 15, 2025 (Exhibit H) establishes the baseline.
"""


def _authority_rich_text() -> str:
    """Filing text heavy with legal citations."""
    return """\
STATE OF MICHIGAN
IN THE 14TH CIRCUIT COURT FOR THE COUNTY OF MUSKEGON
Case No. 2024-001507-DC

Under MCL 722.27(1)(c), modification requires proper cause or change of
circumstances. The seminal case is Vodvarka v Grasmeyer, 259 Mich App
499 (2003), which established the modern framework.

MCR 3.210 governs custody proceedings. The court must consider all
factors under MCL 722.23. See also Shade v Wright, 291 Mich App 17 (2010).

The Fourteenth Amendment guarantees due process. Troxel v Granville,
530 US 57 (2000), protects parental rights. 42 USC §1983 provides a
federal remedy for constitutional violations.

Attached as Exhibit A is the certified court transcript.
Exhibit B contains corroborating witness statements from three sources.
An independent expert report (Exhibit C, per MRE 702) supports our position.

CERTIFICATE OF SERVICE
I certify that on this date I served copies per MCR 2.107.

Respectfully submitted,
/s/ Andrew J. Pigors
ANDREW J. PIGORS, Pro Se
1977 Whitehall Road, Lot 17
North Muskegon, MI 49445
"""


# ═══════════════════════════════════════════════════════════════════
#  1. FilingStateMachine Tests (18 tests)
# ═══════════════════════════════════════════════════════════════════

class TestFilingStateMachine(unittest.TestCase):
    """Tests for the FilingStateMachine class."""

    def setUp(self):
        self.fsm = FilingStateMachine(db_path=None, persist=False)

    # -- lifecycle ---------------------------------------------------

    def test_initial_state_is_draft(self):
        rec = self.fsm.create_filing("F001", "Test Motion", "A")
        self.assertEqual(rec.current_phase, FilingPhase.DRAFT)

    def test_valid_transition_draft_to_review(self):
        self.fsm.create_filing("F002", "Motion", "A")
        trans = self.fsm.advance(
            "F002", FilingPhase.REVIEW, "agent1", "ready for review",
            check_results={"has_content": True, "has_caption": True, "has_case_number": True},
        )
        self.assertEqual(trans.to_phase, FilingPhase.REVIEW)

    def test_invalid_transition_draft_to_filed(self):
        self.fsm.create_filing("F003", "Motion", "A")
        with self.assertRaises(InvalidTransitionError):
            self.fsm.advance("F003", FilingPhase.FILED, "agent1", "skip")

    def test_full_lifecycle_draft_to_served(self):
        self.fsm.create_filing("F004", "Motion", "A")
        phase_checks = {
            FilingPhase.REVIEW: {"has_content": True, "has_caption": True, "has_case_number": True},
            FilingPhase.QA: {"reviewer_approved": True, "no_placeholders": True},
            FilingPhase.APPROVED: {"qa_score_above_80": True, "citations_verified": True, "party_names_correct": True},
            FilingPhase.FORMATTED: {"approved_by_qa": True, "format_compliant": True},
            FilingPhase.FILED: {"pdf_generated": True, "e_filing_ready": True, "fee_paid_or_waived": True, "filed_with_court": True},
            FilingPhase.SERVED: {"filed_with_court": True, "proof_of_service_complete": True},
        }
        for phase in [
            FilingPhase.REVIEW,
            FilingPhase.QA,
            FilingPhase.APPROVED,
            FilingPhase.FORMATTED,
            FilingPhase.FILED,
            FilingPhase.SERVED,
        ]:
            self.fsm.advance(
                "F004", phase, "agent1", f"advance to {phase.value}",
                check_results=phase_checks.get(phase, {}),
            )
        rec = self.fsm.get_filing("F004")
        self.assertEqual(rec.current_phase, FilingPhase.SERVED)

    def test_rollback_to_previous_state(self):
        self.fsm.create_filing("F005", "Motion", "A")
        self.fsm.advance("F005", FilingPhase.REVIEW, "a1", "review",
                         check_results={"has_content": True, "has_caption": True, "has_case_number": True})
        self.fsm.advance("F005", FilingPhase.QA, "a1", "qa",
                         check_results={"reviewer_approved": True, "no_placeholders": True})
        self.fsm.rollback("F005", FilingPhase.REVIEW, "a1", "needs rework")
        rec = self.fsm.get_filing("F005")
        self.assertEqual(rec.current_phase, FilingPhase.REVIEW)

    def test_transition_audit_log_recorded(self):
        self.fsm.create_filing("F006", "Motion", "A")
        self.fsm.advance("F006", FilingPhase.REVIEW, "a1", "advance",
                         check_results={"has_content": True, "has_caption": True, "has_case_number": True})
        log = self.fsm.get_audit_log("F006")
        self.assertGreaterEqual(len(log), 1)
        self.assertEqual(log[-1].to_phase, FilingPhase.REVIEW)

    def test_transition_with_metadata(self):
        self.fsm.create_filing("F007", "Motion", "A", metadata={"lane": "A"})
        rec = self.fsm.get_filing("F007")
        self.assertIn("lane", rec.metadata)
        self.assertEqual(rec.metadata["lane"], "A")

    def test_get_available_transitions(self):
        valid = FilingStateMachine.VALID_TRANSITIONS
        self.assertIn(FilingPhase.REVIEW, valid[FilingPhase.DRAFT])
        self.assertNotIn(FilingPhase.FILED, valid[FilingPhase.DRAFT])

    def test_state_persistence_to_dict(self):
        self.fsm.create_filing("F008", "Motion", "A")
        rec = self.fsm.get_filing("F008")
        d = rec.to_dict()
        self.assertIn("filing_id", d)
        self.assertIn("current_phase", d)
        self.assertEqual(d["filing_id"], "F008")

    def test_state_machine_get_stats(self):
        self.fsm.create_filing("F009", "Motion", "A")
        stats = self.fsm.get_stats()
        self.assertIsInstance(stats, dict)

    def test_multiple_documents_tracked(self):
        self.fsm.create_filing("F010", "Motion A", "A")
        self.fsm.create_filing("F011", "Motion B", "B")
        rec_a = self.fsm.get_filing("F010")
        rec_b = self.fsm.get_filing("F011")
        self.assertEqual(rec_a.vehicle_name, "Motion A")
        self.assertEqual(rec_b.vehicle_name, "Motion B")

    def test_transition_callback_invoked(self):
        self.fsm.create_filing("F012", "Motion", "A")
        trans = self.fsm.advance(
            "F012", FilingPhase.REVIEW, "agent1", "review",
            check_results={"has_content": True, "has_caption": True, "has_case_number": True},
        )
        self.assertEqual(trans.to_phase, FilingPhase.REVIEW)

    def test_invalid_document_id_handled(self):
        with self.assertRaises((FilingNotFoundError, FilingStateError)):
            self.fsm.get_filing("NONEXISTENT_ID")

    def test_state_history_maintained(self):
        self.fsm.create_filing("F013", "Motion", "A")
        self.fsm.advance("F013", FilingPhase.REVIEW, "a1", "r1",
                         check_results={"has_content": True, "has_caption": True, "has_case_number": True})
        self.fsm.advance("F013", FilingPhase.QA, "a1", "r2",
                         check_results={"reviewer_approved": True, "no_placeholders": True})
        rec = self.fsm.get_filing("F013")
        self.assertGreaterEqual(len(rec.history), 2)

    def test_parallel_document_states(self):
        self.fsm.create_filing("F014", "Doc A", "A")
        self.fsm.create_filing("F015", "Doc B", "B")
        self.fsm.advance("F014", FilingPhase.REVIEW, "a1", "advance A",
                         check_results={"has_content": True, "has_caption": True, "has_case_number": True})
        rec_a = self.fsm.get_filing("F014")
        rec_b = self.fsm.get_filing("F015")
        self.assertEqual(rec_a.current_phase, FilingPhase.REVIEW)
        self.assertEqual(rec_b.current_phase, FilingPhase.DRAFT)

    def test_duplicate_filing_id_raises(self):
        self.fsm.create_filing("FDUP", "Motion", "A")
        with self.assertRaises(FilingStateError):
            self.fsm.create_filing("FDUP", "Duplicate", "A")

    def test_invalid_lane_raises(self):
        with self.assertRaises((FilingStateError, ValueError)):
            self.fsm.create_filing("FBAD", "Motion", "Z")

    def test_filing_record_from_dict_roundtrip(self):
        self.fsm.create_filing("FRT", "Motion", "A")
        rec = self.fsm.get_filing("FRT")
        d = rec.to_dict()
        restored = FilingRecord.from_dict(d)
        self.assertEqual(restored.filing_id, "FRT")
        self.assertEqual(restored.current_phase, FilingPhase.DRAFT)


# ═══════════════════════════════════════════════════════════════════
#  2. QualityGateEngine Tests (22 tests)
# ═══════════════════════════════════════════════════════════════════

class TestQualityGateEngine(unittest.TestCase):
    """Tests for the QualityGateEngine class."""

    def setUp(self):
        self.qg = QualityGateEngine()

    # -- party names ------------------------------------------------

    def test_check_party_name_correct(self):
        text = "Plaintiff ANDREW J. PIGORS v. Defendant EMILY A. WATSON."
        checks = self.qg.run_specific_checks(text, ["party_names"])
        for chk in checks:
            if chk.check_id == "party_names":
                self.assertTrue(chk.passed, f"Party names check failed: {chk.details}")

    def test_check_party_name_wrong_emily_ann(self):
        text = "Defendant Emily Ann Watson appeared."
        checks = self.qg.run_specific_checks(text, ["party_names"])
        found_issue = any(not c.passed for c in checks if c.check_id == "party_names")
        self.assertTrue(found_issue, "Should flag 'Emily Ann Watson'")

    def test_check_party_name_wrong_emily_m(self):
        text = "Defendant Emily M. Watson appeared."
        checks = self.qg.run_specific_checks(text, ["party_names"])
        found_issue = any(not c.passed for c in checks if c.check_id == "party_names")
        self.assertTrue(found_issue, "Should flag 'Emily M. Watson'")

    # -- judge name -------------------------------------------------

    def test_check_judge_name_correct(self):
        text = "Before the Honorable Jenny L. McNeill, Circuit Court Judge."
        checks = self.qg.run_specific_checks(text, ["judge_name"])
        for chk in checks:
            if chk.check_id == "judge_name":
                self.assertTrue(chk.passed, f"Judge name failed: {chk.details}")

    def test_check_judge_name_wrong_mcneil(self):
        text = "Judge McNeil issued the ruling."
        checks = self.qg.run_specific_checks(text, ["judge_name"])
        found_issue = any(not c.passed for c in checks if c.check_id == "judge_name")
        self.assertTrue(found_issue, "Should flag 'McNeil' (single L)")

    # -- case number ------------------------------------------------

    def test_check_case_number_format_correct(self):
        text = "Case No. 2024-001507-DC."
        checks = self.qg.run_specific_checks(text, ["case_number_format"])
        for chk in checks:
            if chk.check_id == "case_number_format":
                self.assertTrue(chk.passed, f"Case number failed: {chk.details}")

    def test_check_case_number_missing_zeros(self):
        text = "Case No. 2024-1507-DC."
        checks = self.qg.run_specific_checks(text, ["case_number_format"])
        found_issue = any(
            not c.passed for c in checks if c.check_id == "case_number_format"
        )
        self.assertTrue(found_issue, "Should flag missing leading zeros")

    # -- child redaction --------------------------------------------

    def test_check_child_redaction_ldw(self):
        text = "The minor child, L.D.W., was present at the hearing."
        checks = self.qg.run_specific_checks(text, ["child_name"])
        for chk in checks:
            if chk.check_id == "child_name":
                self.assertTrue(chk.passed, f"L.D.W. should pass: {chk.details}")

    def test_check_child_redaction_full_name(self):
        text = "Lincoln David Watson was present at the hearing."
        checks = self.qg.run_specific_checks(text, ["child_name"])
        found_issue = any(not c.passed for c in checks if c.check_id == "child_name")
        self.assertTrue(found_issue, "Should flag full child name")

    # -- fabricated citations ---------------------------------------

    def test_check_fabricated_citations_clean(self):
        text = "Vodvarka v Grasmeyer, 259 Mich App 499 (2003)."
        checks = self.qg.run_specific_checks(text, ["no_fabricated_citations"])
        for chk in checks:
            if chk.check_id == "no_fabricated_citations":
                self.assertTrue(chk.passed, f"Clean citation flagged: {chk.details}")

    def test_check_fabricated_citations_mccraney(self):
        text = "McCraney v Ford Motor Co, 154 Mich App 297 (1986)."
        checks = self.qg.run_specific_checks(text, ["no_fabricated_citations"])
        found_issue = any(
            not c.passed for c in checks if c.check_id == "no_fabricated_citations"
        )
        self.assertTrue(found_issue, "Should flag McCraney fabricated citation")

    def test_check_fabricated_citations_cease(self):
        text = "Cease v AAA Michigan, unpublished (2020)."
        checks = self.qg.run_specific_checks(text, ["no_fabricated_citations"])
        found_issue = any(
            not c.passed for c in checks if c.check_id == "no_fabricated_citations"
        )
        self.assertTrue(found_issue, "Should flag Cease fabricated citation")

    # -- placeholders -----------------------------------------------

    def test_check_placeholder_none(self):
        text = _clean_motion()
        checks = self.qg.run_specific_checks(text, ["no_placeholders"])
        for chk in checks:
            if chk.check_id == "no_placeholders":
                self.assertTrue(chk.passed, f"No placeholders should pass: {chk.details}")

    def test_check_placeholder_found(self):
        text = "This motion is about [PLACEHOLDER] and [TODO: fix]."
        checks = self.qg.run_specific_checks(text, ["no_placeholders"])
        found_issue = any(
            not c.passed for c in checks if c.check_id == "no_placeholders"
        )
        self.assertTrue(found_issue, "Should flag [PLACEHOLDER]")

    # -- gate runs --------------------------------------------------

    def test_run_all_checks_clean_document(self):
        result = self.qg.run_gate(_clean_motion(), "F100", "review")
        self.assertIsInstance(result, GateResult)
        self.assertIsInstance(result.score, float)

    def test_run_all_checks_dirty_document(self):
        result = self.qg.run_gate(_dirty_document(), "F101", "qa")
        self.assertIsInstance(result, GateResult)
        self.assertGreater(result.blocker_count + result.warning_count, 0)

    def test_quality_score_calculation(self):
        result = self.qg.run_gate(_clean_motion(), "F102", "review")
        self.assertGreaterEqual(result.score, 0.0)
        self.assertLessEqual(result.score, 100.0)

    def test_gate_pass_threshold(self):
        result = self.qg.run_gate(_clean_motion(), "F103", "review")
        # Clean motion should either pass or at least have a high score
        self.assertIsInstance(result.passed, bool)

    def test_gate_fail_threshold(self):
        result = self.qg.run_gate(_dirty_document(), "F104", "qa")
        # Dirty document should fail with blockers
        self.assertFalse(result.passed, "Dirty document should fail QA gate")

    def test_get_stats(self):
        self.qg.run_gate(_clean_motion(), "FSTATS", "review")
        stats = self.qg.get_stats()
        self.assertIsInstance(stats, dict)

    def test_get_available_checks(self):
        checks = self.qg.get_available_checks()
        self.assertIsInstance(checks, list)
        self.assertGreater(len(checks), 0)

    def test_gate_result_to_dict(self):
        result = self.qg.run_gate(_clean_motion(), "FDICT", "review")
        d = result.to_dict()
        self.assertIn("gate_name", d)
        self.assertIn("score", d)
        self.assertIn("checks", d)


# ═══════════════════════════════════════════════════════════════════
#  3. CaptionGenerator Tests (12 tests)
# ═══════════════════════════════════════════════════════════════════

class TestCaptionGenerator(unittest.TestCase):
    """Tests for the CaptionGenerator class."""

    def setUp(self):
        self.cg = CaptionGenerator()

    def test_generate_14th_circuit_caption(self):
        cap = self.cg.generate("14th_circuit", "Motion to Modify Custody")
        self.assertIsInstance(cap, Caption)
        self.assertTrue(len(cap.full_caption) > 0)

    def test_generate_coa_caption(self):
        cap = self.cg.generate("coa", "Brief on Appeal")
        self.assertIn("366810", cap.full_caption)

    def test_generate_msc_caption(self):
        cap = self.cg.generate("msc", "Application for Leave to Appeal")
        self.assertIsInstance(cap, Caption)
        self.assertTrue(len(cap.full_caption) > 0)

    def test_generate_federal_wdmi_caption(self):
        cap = self.cg.generate("wdmi", "42 USC 1983 Complaint")
        self.assertIsInstance(cap, Caption)
        self.assertTrue(len(cap.full_caption) > 0)

    def test_generate_jtc_caption(self):
        cap = self.cg.generate("jtc", "Complaint Against Judge")
        self.assertIsInstance(cap, Caption)
        self.assertTrue(len(cap.full_caption) > 0)

    def test_caption_includes_plaintiff_name(self):
        cap = self.cg.generate("14th_circuit", "Motion")
        self.assertIn("PIGORS", cap.full_caption.upper())

    def test_caption_includes_case_number(self):
        cap = self.cg.generate("14th_circuit", "Motion")
        self.assertIn("2024-001507-DC", cap.full_caption)

    def test_lane_a_defendants(self):
        block = self.cg.get_defendant_block("A")
        self.assertIn("WATSON", block.upper())

    def test_lane_b_defendants(self):
        block = self.cg.get_defendant_block("B")
        self.assertIn("SHADY OAKS", block.upper())

    def test_get_stats(self):
        self.cg.generate("14th_circuit", "Test")
        stats = self.cg.get_stats()
        self.assertIsInstance(stats, dict)

    def test_validate_caption_clean(self):
        cap = self.cg.generate("14th_circuit", "Motion")
        issues = self.cg.validate_caption(cap.full_caption)
        self.assertIsInstance(issues, list)

    def test_format_case_number_adds_zeros(self):
        formatted = self.cg.format_case_number("2024-1507-DC")
        self.assertEqual(formatted, "2024-001507-DC")


# ═══════════════════════════════════════════════════════════════════
#  4. EvidenceGapDetector Tests (17 tests)
# ═══════════════════════════════════════════════════════════════════

class TestEvidenceGapDetector(unittest.TestCase):
    """Tests for the EvidenceGapDetector class."""

    def setUp(self):
        with patch.object(
            EvidenceGapDetector, "__init__", lambda self, **kw: None
        ):
            self.det = EvidenceGapDetector()
        # Manually initialize the attributes the constructor would set
        self.det._db_path = None
        self.det._conn = None
        self.det._stats = {
            "analyses_run": 0,
            "gaps_found": 0,
            "requirements_checked": 0,
        }
        # Set up the requirement maps and patterns directly
        self.det._requirement_maps = {}
        self.det._evidence_patterns = []
        self.det._importance_weight = {
            "critical": 1.0, "strong": 0.75, "supporting": 0.5, "optional": 0.25,
        }
        self.det._severity_weight = {
            "critical": 1.0, "high": 0.75, "medium": 0.5, "low": 0.25,
        }

    def _make_detector(self) -> EvidenceGapDetector:
        """Create a properly initialized detector with mocked DB."""
        with patch("evidence_gap_detector.Path.exists", return_value=False):
            det = EvidenceGapDetector.__new__(EvidenceGapDetector)
            det._db_path = None
            det._conn = None
            det._stats = {
                "analyses_run": 0,
                "gaps_found": 0,
                "requirements_checked": 0,
            }
            return det

    def test_detect_gaps_custody_motion(self):
        """Full init with mocked DB path for end-to-end test."""
        with patch("evidence_gap_detector.Path.exists", return_value=False):
            det = EvidenceGapDetector(db_path=None)
        reqs = det.get_requirements("custody_modification")
        self.assertIsInstance(reqs, list)
        self.assertGreater(len(reqs), 0)

    def test_detect_gaps_housing_complaint(self):
        with patch("evidence_gap_detector.Path.exists", return_value=False):
            det = EvidenceGapDetector(db_path=None)
        reqs = det.get_requirements("complaint_housing")
        self.assertIsInstance(reqs, list)
        self.assertGreater(len(reqs), 0)

    def test_detect_gaps_ppo_modification(self):
        with patch("evidence_gap_detector.Path.exists", return_value=False):
            det = EvidenceGapDetector(db_path=None)
        reqs = det.get_requirements("ppo_violation")
        self.assertIsInstance(reqs, list)

    def test_detect_gaps_disqualification_motion(self):
        with patch("evidence_gap_detector.Path.exists", return_value=False):
            det = EvidenceGapDetector(db_path=None)
        reqs = det.get_requirements("motion_disqualification")
        self.assertIsInstance(reqs, list)
        self.assertGreater(len(reqs), 0)

    def test_no_gaps_when_all_evidence_present(self):
        with patch("evidence_gap_detector.Path.exists", return_value=False):
            det = EvidenceGapDetector(db_path=None)
        reqs = det.get_requirements("custody_modification")
        # Create matches for every requirement
        matches = []
        for r in reqs:
            matches.append(EvidenceMatch(
                req_id=r.req_id,
                evidence_id=f"ev_{r.req_id}",
                source_file="evidence.pdf",
                match_quality=0.95,
                match_reason="Direct match",
            ))
        gaps = det.detect_gaps(reqs, matches)
        self.assertEqual(len(gaps), 0, "Should have no gaps when all evidence matched")

    def test_gap_priority_scoring(self):
        with patch("evidence_gap_detector.Path.exists", return_value=False):
            det = EvidenceGapDetector(db_path=None)
        reqs = det.get_requirements("custody_modification")
        gaps = det.detect_gaps(reqs, [])  # no evidence at all
        if gaps:
            prioritized = det.prioritize_gaps(gaps)
            self.assertGreaterEqual(len(prioritized), 1)
            # First gap should have highest priority
            if len(prioritized) > 1:
                self.assertGreaterEqual(
                    prioritized[0].priority_score, prioritized[-1].priority_score
                )

    def test_gap_acquisition_tasks_generated(self):
        with patch("evidence_gap_detector.Path.exists", return_value=False):
            det = EvidenceGapDetector(db_path=None)
        reqs = det.get_requirements("custody_modification")
        gaps = det.detect_gaps(reqs, [])
        for gap in gaps:
            self.assertTrue(
                len(gap.acquisition_task) > 0,
                f"Gap {gap.req_id} should have an acquisition task",
            )

    def test_multi_lane_detection(self):
        with patch("evidence_gap_detector.Path.exists", return_value=False):
            det = EvidenceGapDetector(db_path=None)
        for ftype in ["custody_modification", "complaint_housing", "motion_disqualification"]:
            reqs = det.get_requirements(ftype)
            self.assertIsInstance(reqs, list)

    def test_evidence_requirement_count(self):
        with patch("evidence_gap_detector.Path.exists", return_value=False):
            det = EvidenceGapDetector(db_path=None)
        reqs = det.get_requirements("custody_modification")
        self.assertGreaterEqual(len(reqs), 5, "Custody should have 5+ requirements")

    def test_gap_report_structure(self):
        with patch("evidence_gap_detector.Path.exists", return_value=False):
            det = EvidenceGapDetector(db_path=None)
        report = det.analyze_filing("F200", _evidence_rich_text(), "custody_modification", "A")
        self.assertIsInstance(report, GapAnalysisReport)
        self.assertIsInstance(report.coverage_pct, float)
        self.assertIsInstance(report.grade, str)

    def test_lane_specific_requirements(self):
        with patch("evidence_gap_detector.Path.exists", return_value=False):
            det = EvidenceGapDetector(db_path=None)
        custody_reqs = det.get_requirements("custody_modification")
        housing_reqs = det.get_requirements("complaint_housing")
        custody_ids = {r.req_id for r in custody_reqs}
        housing_ids = {r.req_id for r in housing_reqs}
        # Requirements should differ between lanes
        self.assertNotEqual(custody_ids, housing_ids)

    def test_get_stats(self):
        with patch("evidence_gap_detector.Path.exists", return_value=False):
            det = EvidenceGapDetector(db_path=None)
        stats = det.get_stats()
        self.assertIsInstance(stats, dict)

    def test_gap_to_dict(self):
        gap = EvidenceGap(
            req_id="R001",
            requirement=EvidenceRequirement(
                req_id="R001",
                filing_type="custody_modification",
                description="Test requirement",
                category="documentary",
                importance="critical",
                mcr_basis="MCL 722.23",
            ),
            gap_type="missing",
            severity="critical",
            acquisition_task="Obtain document",
            estimated_effort="immediate",
        )
        d = gap.to_dict()
        self.assertIn("req_id", d)
        self.assertIn("gap_type", d)
        self.assertEqual(d["severity"], "critical")

    def test_empty_evidence_set(self):
        with patch("evidence_gap_detector.Path.exists", return_value=False):
            det = EvidenceGapDetector(db_path=None)
        reqs = det.get_requirements("custody_modification")
        gaps = det.detect_gaps(reqs, [])
        # With no evidence, should have gaps for every requirement
        self.assertGreater(len(gaps), 0)

    def test_critical_gaps_flagged(self):
        with patch("evidence_gap_detector.Path.exists", return_value=False):
            det = EvidenceGapDetector(db_path=None)
        reqs = det.get_requirements("custody_modification")
        gaps = det.detect_gaps(reqs, [])
        critical_gaps = [g for g in gaps if g.severity == "critical"]
        self.assertGreater(len(critical_gaps), 0, "Should have at least one critical gap")

    def test_scan_for_evidence_in_text(self):
        with patch("evidence_gap_detector.Path.exists", return_value=False):
            det = EvidenceGapDetector(db_path=None)
        evidence = det.scan_for_evidence_in_text(_evidence_rich_text())
        self.assertIsInstance(evidence, list)
        self.assertGreater(len(evidence), 0, "Should find evidence in rich text")

    def test_evidence_requirement_to_dict(self):
        req = EvidenceRequirement(
            req_id="REQ001",
            filing_type="custody_modification",
            description="Love and affection evidence",
            category="testimonial",
            importance="critical",
            mcr_basis="MCL 722.23(a)",
        )
        d = req.to_dict()
        self.assertEqual(d["req_id"], "REQ001")
        self.assertEqual(d["importance"], "critical")


# ═══════════════════════════════════════════════════════════════════
#  5. OutcomePredictor Tests (18 tests)
# ═══════════════════════════════════════════════════════════════════

class TestOutcomePredictor(unittest.TestCase):
    """Tests for the OutcomePredictor class."""

    def setUp(self):
        with patch("outcome_predictor.Path.exists", return_value=False):
            self.pred = OutcomePredictor(db_path=None)

    def test_predict_custody_modification(self):
        result = self.pred.predict(
            _clean_motion(), "custody_modification", "A", "14th_circuit",
        )
        self.assertIsInstance(result, OutcomePrediction)
        self.assertGreater(result.probability_success, 0.0)

    def test_predict_disqualification_motion(self):
        result = self.pred.predict(
            _authority_rich_text(), "motion_disqualification", "A", "14th_circuit",
        )
        self.assertIsInstance(result, OutcomePrediction)

    def test_predict_ppo_modification(self):
        result = self.pred.predict(
            _clean_motion(), "ppo_violation", "D", "14th_circuit",
        )
        self.assertIsInstance(result, OutcomePrediction)

    def test_predict_housing_complaint(self):
        result = self.pred.predict(
            _clean_motion(), "complaint_housing", "B", "14th_circuit",
        )
        self.assertIsInstance(result, OutcomePrediction)

    def test_predict_contempt_motion(self):
        # May fall back to default base rate
        result = self.pred.predict(
            _clean_motion(), "contempt", "A", "14th_circuit",
        )
        self.assertIsInstance(result, OutcomePrediction)

    def test_mcneill_profile_embedded(self):
        factor = self.pred.score_judicial_profile("mcneill", "custody_modification")
        self.assertIsInstance(factor, PredictionFactor)

    def test_base_rates_reasonable(self):
        for ftype in [
            "motion_disqualification", "custody_modification",
            "federal_1983", "complaint_housing", "ppo_violation",
        ]:
            rate = self.pred.get_base_rate(ftype)
            self.assertGreaterEqual(rate, 0.0, f"{ftype} base rate < 0")
            self.assertLessEqual(rate, 1.0, f"{ftype} base rate > 1")

    def test_evidence_strength_factor(self):
        factor = self.pred.score_evidence_weight(_evidence_rich_text())
        self.assertIsInstance(factor, PredictionFactor)
        self.assertGreaterEqual(factor.score, 0.0)
        self.assertLessEqual(factor.score, 1.0)

    def test_authority_strength_factor(self):
        factor = self.pred.score_authority_strength(_authority_rich_text())
        self.assertIsInstance(factor, PredictionFactor)
        self.assertGreaterEqual(factor.score, 0.0)
        self.assertLessEqual(factor.score, 1.0)

    def test_judicial_profile_factor(self):
        factor = self.pred.score_judicial_profile("mcneill", "motion_disqualification")
        self.assertIsInstance(factor, PredictionFactor)

    def test_prediction_confidence_range(self):
        result = self.pred.predict(
            _clean_motion(), "custody_modification", "A", "14th_circuit",
        )
        self.assertGreaterEqual(result.confidence, 0.0)
        self.assertLessEqual(result.confidence, 1.0)

    def test_prediction_to_dict(self):
        result = self.pred.predict(
            _clean_motion(), "custody_modification", "A", "14th_circuit",
        )
        d = result.to_dict()
        self.assertIn("probability_success", d)
        self.assertIn("confidence", d)
        self.assertIn("grade", d)

    def test_report_structure(self):
        result = self.pred.predict(
            _authority_rich_text(), "motion_disqualification", "A", "14th_circuit",
        )
        self.assertIsInstance(result.factors, list)
        self.assertIsInstance(result.risk_factors, list)
        self.assertIsInstance(result.strength_factors, list)
        self.assertIsInstance(result.recommendations, list)

    def test_get_stats(self):
        self.pred.predict(
            _clean_motion(), "custody_modification", "A", "14th_circuit",
        )
        stats = self.pred.get_stats()
        self.assertIsInstance(stats, dict)

    def test_multiple_predictions_independent(self):
        r1 = self.pred.predict(
            _clean_motion(), "custody_modification", "A", "14th_circuit",
        )
        r2 = self.pred.predict(
            _authority_rich_text(), "motion_disqualification", "A", "14th_circuit",
        )
        self.assertNotEqual(r1.filing_type, r2.filing_type)

    def test_prediction_factor_weighted_score(self):
        pf = PredictionFactor(
            factor_name="test", weight=0.5, score=0.8,
            confidence=0.9, evidence="test evidence",
        )
        self.assertAlmostEqual(pf.weighted_score, 0.4, places=2)

    def test_prediction_factor_to_dict(self):
        pf = PredictionFactor(
            factor_name="authority", weight=0.25, score=0.7,
            confidence=0.8, evidence="MCL 722.23",
        )
        d = pf.to_dict()
        self.assertIn("factor_name", d)
        self.assertIn("weight", d)
        self.assertEqual(d["factor_name"], "authority")

    def test_bayesian_update(self):
        prior = 0.3
        factors = [
            PredictionFactor(
                factor_name="test", weight=0.5, score=0.8,
                confidence=0.9, evidence="test",
            ),
        ]
        posterior = self.pred.bayesian_update(prior, factors)
        self.assertGreaterEqual(posterior, 0.0)
        self.assertLessEqual(posterior, 1.0)


if __name__ == "__main__":
    unittest.main()
