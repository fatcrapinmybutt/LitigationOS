"""
Comprehensive test suite for the LitigationOS agent evaluation framework.

Tests shared.internal.eval — SafetyChecker, FormatChecker, CitationVerifier,
MetricsRecorder, AgentEvalSuite, and convenience functions.

50+ test functions covering safety, format, citations, metrics, integration,
and edge cases. Follows existing test conventions from test_fts5.py / test_db.py.
"""

import json
import sqlite3
import sys
import time
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Path setup — mirror pattern from test_fts5.py / test_db.py
# ---------------------------------------------------------------------------
_system_dir = str(Path(__file__).resolve().parent.parent.parent)
if _system_dir not in sys.path:
    sys.path.insert(0, _system_dir)

from shared.internal.eval import (
    QualityDimension,
    EvalResult,
    AgentEvalSuite,
    SafetyChecker,
    CitationVerifier,
    FormatChecker,
    MetricsRecorder,
    evaluate_text,
    quick_safety_check,
)


# ===========================================================================
# 1. SAFETY CHECKER TESTS (MOST CRITICAL — 18 tests)
# ===========================================================================


# --- Child name protection (MCR 8.119(H)) ---

def test_safety_child_name_detected():
    """Full child name must be flagged."""
    safe, violations = SafetyChecker.check_child_name(
        "The court granted custody of Lincoln David Watson to the mother."
    )
    assert not safe
    assert len(violations) >= 1  # may find full name + context match
    assert any("MCR 8.119(H)" in v for v in violations)


def test_safety_child_initials_allowed():
    """L.D.W. and 'the minor child' must pass."""
    safe_ldw, v1 = SafetyChecker.check_child_name(
        "The court granted custody of L.D.W. to the mother."
    )
    assert safe_ldw
    assert v1 == []

    safe_minor, v2 = SafetyChecker.check_child_name(
        "The best interests of the minor child require immediate action."
    )
    assert safe_minor
    assert v2 == []


def test_safety_child_name_case_insensitive():
    """Detection must be case insensitive."""
    safe_upper, violations = SafetyChecker.check_child_name(
        "LINCOLN DAVID WATSON was removed from the home."
    )
    assert not safe_upper
    assert len(violations) >= 1

    safe_mixed, v2 = SafetyChecker.check_child_name(
        "lincoln david watson is only two years old."
    )
    assert not safe_mixed
    assert len(v2) >= 1


def test_safety_child_name_partial_no_flag():
    """Partial name (first only) without custody context should NOT trigger flag."""
    safe, violations = SafetyChecker.check_child_name(
        "Lincoln is a common name. David appeared in court."
    )
    assert safe
    assert violations == []


# --- AI reference detection ---

def test_safety_ai_refs_litigationos():
    """LitigationOS must be caught."""
    safe, violations = SafetyChecker.check_ai_references(
        "The LitigationOS database shows a score of 85"
    )
    assert not safe
    assert any("LitigationOS" in v for v in violations)


def test_safety_ai_refs_egcp():
    """EGCP scoring reference must be caught."""
    safe, violations = SafetyChecker.check_ai_references(
        "According to the EGCP analysis, filing readiness is 72%."
    )
    assert not safe
    assert any("EGCP" in v for v in violations)


def test_safety_ai_refs_multiple():
    """Multiple AI refs in one text all detected."""
    text = "The OMEGA engine and SINGULARITY framework scored this via database scoring."
    safe, violations = SafetyChecker.check_ai_references(text)
    assert not safe
    assert len(violations) >= 3


def test_safety_ai_refs_clean_text_passes():
    """Normal legal text with no AI refs passes."""
    safe, violations = SafetyChecker.check_ai_references(
        "Plaintiff respectfully moves this Honorable Court for an order "
        "modifying custody pursuant to MCL 722.27(1)(c)."
    )
    assert safe
    assert violations == []


# --- Hallucination detection ---

def test_safety_hallucination_jane_berry():
    """Jane Berry is a known hallucination — must be caught."""
    safe, violations = SafetyChecker.check_hallucinations(
        "Attorney Jane Berry represented the defendant at the hearing."
    )
    assert not safe
    assert any("Jane Berry" in v for v in violations)


def test_safety_hallucination_patricia_berry():
    """Patricia Berry is also a hallucination — must be caught."""
    safe, violations = SafetyChecker.check_hallucinations(
        "Patricia Berry filed a response on behalf of the defendant."
    )
    assert not safe
    assert any("Patricia Berry" in v for v in violations)


def test_safety_hallucination_mcl_722_27c():
    """MCL 722.27c does not exist — must be caught."""
    safe, violations = SafetyChecker.check_hallucinations(
        "Under MCL 722.27c, the court is required to consider the factors."
    )
    assert not safe
    assert any("722.27c" in v for v in violations)
    assert any("722.23(j)" in v for v in violations)


def test_safety_hallucination_brady_family():
    """Brady v Maryland in family law context — wrong citation."""
    safe, violations = SafetyChecker.check_hallucinations(
        "Under Brady v Maryland, custody disclosure obligations require "
        "the court to consider the best interest factors in family law."
    )
    assert not safe
    assert any("Brady" in v for v in violations)
    assert any("Mathews" in v for v in violations)


def test_safety_hallucination_brady_criminal_ok():
    """Brady v Maryland in criminal context is valid — should pass."""
    safe, violations = SafetyChecker.check_hallucinations(
        "Under Brady v Maryland, the prosecution must disclose exculpatory evidence."
    )
    assert safe
    assert violations == []


# --- Party name compliance ---

def test_safety_party_name_mcneill_one_l():
    """McNeil (one L) must be caught."""
    safe, violations = SafetyChecker.check_party_names(
        "Judge McNeil entered the order on October 5."
    )
    assert not safe
    assert any("McNeill" in v or "TWO L" in v for v in violations)


def test_safety_party_name_mcneill_correct():
    """McNeill (two L's) should pass."""
    safe, violations = SafetyChecker.check_party_names(
        "The Honorable Jenny L. McNeill presided over the hearing."
    )
    assert safe
    assert violations == []


def test_safety_party_name_emily_wrong():
    """Emily Ann and Watson-Pigors must be caught."""
    safe1, v1 = SafetyChecker.check_party_names(
        "Emily Ann Watson filed a response."
    )
    assert not safe1
    assert any("Emily A. Watson" in v for v in v1)

    safe2, v2 = SafetyChecker.check_party_names(
        "Defendant Watson-Pigors appeared pro se."
    )
    assert not safe2
    assert any("Emily A. Watson" in v for v in v2)


# --- Pro se language ---

def test_safety_pro_se_language():
    """'undersigned counsel' must be caught — pro se case."""
    safe, violations = SafetyChecker.check_party_names(
        "The undersigned counsel respectfully submits this brief."
    )
    assert not safe
    assert any("undersigned counsel" in v for v in violations)


def test_safety_pro_se_attorney_for_plaintiff():
    """'attorney for plaintiff' must be caught."""
    safe, violations = SafetyChecker.check_party_names(
        "Signed by attorney for Plaintiff on this date."
    )
    assert not safe
    assert any("attorney for" in v.lower() for v in violations)


def test_safety_pro_se_correct_language():
    """Proper pro se language passes."""
    safe, violations = SafetyChecker.check_party_names(
        "Plaintiff, appearing pro se, respectfully requests this Court grant relief."
    )
    assert safe
    assert violations == []


# --- Comprehensive safety check ---

def test_safety_clean_filing_passes():
    """A properly formatted filing passes all safety checks."""
    text = (
        "IN THE 14TH CIRCUIT COURT FOR THE COUNTY OF MUSKEGON\n"
        "Case No. 2024-001507-DC\n"
        "ANDREW JAMES PIGORS, Plaintiff (pro se)\n"
        "v.\n"
        "EMILY A. WATSON, Defendant\n\n"
        "Plaintiff, appearing pro se, respectfully moves this Honorable Court "
        "presided over by the Hon. Jenny L. McNeill for an order restoring "
        "parenting time with the minor child pursuant to MCL 722.27(1)(c).\n"
    )
    result = SafetyChecker.check_all(text)
    assert result.passed, f"Clean filing should pass. Details: {result.details}"
    assert result.score == 1.0


def test_safety_check_all_aggregates():
    """check_all catches violations from multiple categories at once."""
    text = (
        "The LitigationOS system shows Lincoln David Watson was scored via EGCP. "
        "Under MCL 722.27c and Brady v Maryland, the custody hearing requires "
        "Jane Berry and the undersigned counsel to appear before Judge McNeil."
    )
    result = SafetyChecker.check_all(text)
    assert not result.passed
    assert result.score < 1.0


# ===========================================================================
# 2. FORMAT CHECKER TESTS (12 tests)
# ===========================================================================


def test_format_irac_full_detected():
    """Text with all four IRAC sections detected."""
    text = (
        "## ISSUE\nWhether the court erred in its custody determination.\n"
        "## RULE\nUnder MCL 722.23, the court must consider 12 factors.\n"
        "## APPLICATION\nHere, the evidence demonstrates factor (j) failure.\n"
        "## CONCLUSION\nTherefore, this Court should modify custody.\n"
    )
    has_structure, sections = FormatChecker.check_irac(text)
    assert has_structure is True
    assert sum(sections.values()) == 4


def test_format_irac_partial():
    """Text with only 2 of 4 IRAC sections."""
    text = (
        "## ISSUE\nWhether parenting time should be restored.\n"
        "## CONCLUSION\nYes, for the reasons stated above.\n"
    )
    has_structure, sections = FormatChecker.check_irac(text)
    assert sections.get("issue") is True
    assert sections.get("conclusion") is True
    # Only 2 of 4 sections — needs >= 3 for has_structure
    assert has_structure is False


def test_format_irac_variations():
    """Alternative section names: ARGUMENT, APPLICABLE LAW, RELIEF REQUESTED."""
    text = (
        "## STATEMENT OF ISSUE\nWhether...\n"
        "## APPLICABLE LAW\nUnder MCR 2.003...\n"
        "## ARGUMENT\nPlaintiff argues...\n"
        "## RELIEF REQUESTED\nPlaintiff requests...\n"
    )
    has_structure, sections = FormatChecker.check_irac(text)
    # "applicable law" → rule, "argument" → application, "relief requested" → conclusion
    assert sum(sections.values()) >= 3
    assert has_structure is True


def test_format_irac_with_extras():
    """IRAC sections + extra filing sections all detected."""
    text = (
        "## ISSUE\nWhether...\n"
        "## RULE\nUnder MCL...\n"
        "## APPLICATION\nHere...\n"
        "## CONCLUSION\nTherefore...\n"
        "## STATEMENT OF FACTS\nOn July 29, 2025...\n"
        "## PROCEDURAL HISTORY\nThis case was filed...\n"
    )
    has_structure, sections = FormatChecker.check_irac(text)
    assert has_structure is True
    assert all(sections.values())  # all 4 IRAC components found


def test_format_caption_full():
    """Text with court name, case number, parties detected."""
    text = (
        "IN THE CIRCUIT COURT FOR THE COUNTY OF MUSKEGON\n"
        "Case No. 2024-001507-DC\n"
        "ANDREW JAMES PIGORS, Plaintiff\n"
        "v.\n"
        "EMILY A. WATSON, Defendant\n"
    )
    has_caption, detail = FormatChecker.check_caption(text)
    assert has_caption is True
    assert "complete" in detail.lower() or "3/3" in detail


def test_format_caption_partial():
    """Only case number present — caption incomplete."""
    text = "Filed in Case No. 2024-001507-DC on this date."
    has_caption, detail = FormatChecker.check_caption(text)
    # Only 1 of 3 elements — needs >= 2 for has_caption
    assert has_caption is False
    assert "partial" in detail.lower() or "missing" in detail.lower()


def test_format_cos_detected():
    """Certificate of Service section detected."""
    text = (
        "CERTIFICATE OF SERVICE\n"
        "I certify that on this date I served the foregoing upon all parties."
    )
    has_cos, detail = FormatChecker.check_certificate_of_service(text)
    assert has_cos is True
    assert "found" in detail.lower()


def test_format_cos_missing():
    """No COS returns False."""
    text = "This is a brief with no service certificate."
    has_cos, detail = FormatChecker.check_certificate_of_service(text)
    assert has_cos is False
    assert "not found" in detail.lower()


def test_format_empty_text():
    """Empty text returns negative results, doesn't crash."""
    has_irac, sections = FormatChecker.check_irac("")
    assert has_irac is False
    assert not any(sections.values())

    has_caption, _ = FormatChecker.check_caption("")
    assert has_caption is False

    has_cos, _ = FormatChecker.check_certificate_of_service("")
    assert has_cos is False


def test_format_plain_text():
    """Plain text without structure returns negative results."""
    text = (
        "The weather today is sunny and there are no clouds in the sky. "
        "This paragraph has absolutely no legal structure whatsoever."
    )
    has_irac, sections = FormatChecker.check_irac(text)
    assert has_irac is False


def test_format_check_all_composite():
    """AgentEvalSuite.evaluate_format returns weighted composite."""
    text = (
        "IN THE CIRCUIT COURT FOR THE COUNTY OF MUSKEGON\n"
        "Case No. 2024-001507-DC\n"
        "ANDREW JAMES PIGORS, Plaintiff\n"
        "v.\n"
        "EMILY A. WATSON, Defendant\n\n"
        "## ISSUE\nWhether...\n"
        "## RULE\nUnder MCL...\n"
        "## APPLICATION\nHere...\n"
        "## CONCLUSION\nTherefore...\n\n"
        "CERTIFICATE OF SERVICE\n"
        "I certify service on all parties.\n"
    )
    suite = AgentEvalSuite()
    result = suite.evaluate_format(text)
    assert result.score >= 0.8
    assert result.passed is True
    assert isinstance(result, EvalResult)


def test_format_irac_result_type():
    """check_irac returns a tuple of (bool, dict)."""
    result = FormatChecker.check_irac("## ISSUE\nSample text.")
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], bool)
    assert isinstance(result[1], dict)


# ===========================================================================
# 3. CITATION VERIFIER TESTS (10 tests)
# ===========================================================================


def test_citation_extraction_mcl():
    """MCL citations extracted correctly."""
    text = "Under MCL 722.23(j), the court must consider willingness to facilitate."
    citations = CitationVerifier().extract_citations(text)
    assert len(citations) >= 1
    assert any("MCL 722.23" in c for c in citations)


def test_citation_extraction_mcr():
    """MCR citations extracted."""
    text = "Plaintiff moves pursuant to MCR 2.119(F) for reconsideration."
    citations = CitationVerifier().extract_citations(text)
    assert len(citations) >= 1
    assert any("MCR 2.119" in c for c in citations)


def test_citation_extraction_mre():
    """MRE citations extracted."""
    text = "This testimony is admissible under MRE 803.1 as a present sense impression."
    citations = CitationVerifier().extract_citations(text)
    assert len(citations) >= 1
    assert any("MRE 803" in c for c in citations)


def test_citation_extraction_usc():
    """USC citations are NOT extracted — extractor covers MCL/MCR/MRE only."""
    text = "Plaintiff brings this action under 42 USC § 1983 for civil rights violations."
    citations = CitationVerifier().extract_citations(text)
    # Implementation only extracts MCL/MCR/MRE patterns
    assert citations == []


def test_citation_extraction_case_law():
    """Case law citations are NOT extracted — extractor covers MCL/MCR/MRE only."""
    text = "As held in Vodvarka v Grasher, 259 Mich App 499 (2003)."
    citations = CitationVerifier().extract_citations(text)
    # Implementation only extracts MCL/MCR/MRE patterns
    assert citations == []


def test_citation_extraction_multiple():
    """Multiple MCL/MCR/MRE citations in one text all extracted."""
    text = (
        "Under MCL 722.23 and MCR 2.003(C)(1), "
        "the court must consider "
        "MRE 801 before admitting the statement."
    )
    citations = CitationVerifier().extract_citations(text)
    assert len(citations) >= 3
    mcl_found = any("MCL" in c for c in citations)
    mcr_found = any("MCR" in c for c in citations)
    mre_found = any("MRE" in c for c in citations)
    assert mcl_found and mcr_found and mre_found


def test_citation_extraction_none():
    """Text with no citations returns empty list."""
    text = "This is a plain text paragraph with no legal citations at all."
    citations = CitationVerifier().extract_citations(text)
    assert citations == []


def test_citation_extraction_empty():
    """Empty text returns empty list."""
    citations = CitationVerifier().extract_citations("")
    assert citations == []


def test_citation_extraction_deduplication():
    """Duplicate citations are deduplicated."""
    text = "MCL 722.23 requires consideration. Under MCL 722.23, factors include..."
    citations = CitationVerifier().extract_citations(text)
    mcl_citations = [c for c in citations if "MCL 722.23" in c]
    assert len(mcl_citations) == 1


def test_citation_verify_against_db(tmp_path):
    """Create a mock DB with known rules, verify citations match."""
    db_path = tmp_path / "test_citations.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "CREATE TABLE michigan_rules_extracted "
        "(id INTEGER PRIMARY KEY, rule_number TEXT, full_text TEXT)"
    )
    conn.execute(
        "INSERT INTO michigan_rules_extracted (rule_number, full_text) "
        "VALUES ('MCL 722.23', 'Best interest of the child factors MCL 722 23')"
    )
    conn.execute(
        "INSERT INTO michigan_rules_extracted (rule_number, full_text) "
        "VALUES ('MCR 2.003', 'Disqualification of judge MCR 2 003')"
    )
    conn.commit()
    conn.close()

    verifier = CitationVerifier(str(db_path))

    # verify_citations takes text string and returns EvalResult
    result = verifier.verify_citations(
        "Under MCL 722.23 and MCR 2.003 and MCR 9.999, the court must act."
    )
    assert isinstance(result, EvalResult)
    assert result.dimension == QualityDimension.CORRECTNESS
    # MCL 722.23 and MCR 2.003 should be verified, MCR 9.999 should not
    assert "MCR 9.999" in result.checks or "MCR 9.999" in str(result.details)
    assert result.score > 0.0  # at least some verified


# ===========================================================================
# 4. METRICS RECORDER TESTS (9 tests)
# ===========================================================================


def test_metrics_table_creation(tmp_path):
    """Tables created on init."""
    db_path = tmp_path / "metrics.db"
    recorder = MetricsRecorder(db_path)

    conn = sqlite3.connect(str(db_path))
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    conn.close()

    assert "eval_metrics" in tables


def test_metrics_record_result(tmp_path):
    """Single result persisted correctly."""
    db_path = tmp_path / "metrics.db"
    recorder = MetricsRecorder(str(db_path))

    result = EvalResult(
        dimension=QualityDimension.SAFETY,
        score=0.85,
        passed=True,
        checks={"all_passed": True},
        details="All safety checks passed",
    )
    count = recorder.record([result], eval_type="filing")
    assert isinstance(count, int)
    assert count >= 1

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM eval_metrics WHERE eval_type = 'filing' LIMIT 1"
    ).fetchone()
    conn.close()

    assert row["dimension"] == "safety"
    assert abs(row["score"] - 0.85) < 0.001
    assert row["passed"] == 1


def test_metrics_record_batch(tmp_path):
    """Batch recording persists all results."""
    db_path = tmp_path / "metrics.db"
    recorder = MetricsRecorder(str(db_path))

    results = [
        EvalResult(QualityDimension.SAFETY, 1.0, True, {"ok": True}),
        EvalResult(QualityDimension.FORMAT, 0.8, True, {"good": True}),
        EvalResult(QualityDimension.GROUNDEDNESS, 0.6, True, {"partial": True}),
    ]
    count = recorder.record(results, eval_type="batch_test")
    assert count == 3

    conn = sqlite3.connect(str(db_path))
    total = conn.execute("SELECT COUNT(*) FROM eval_metrics").fetchone()[0]
    conn.close()
    assert total == 3


def test_metrics_get_trend(tmp_path):
    """Trend data returned grouped by date."""
    db_path = tmp_path / "metrics.db"
    recorder = MetricsRecorder(str(db_path))

    for score in [0.5, 0.6, 0.7, 0.8, 0.9]:
        recorder.record(
            [EvalResult(QualityDimension.SAFETY, score, True, {"ok": True})],
            eval_type="filing",
        )
        time.sleep(0.01)  # ensure distinct timestamps

    trend = recorder.get_trend("filing", "safety")
    assert isinstance(trend, list)
    # All records are same date → 1 grouped entry
    assert len(trend) >= 1


def test_metrics_get_trend_filtered(tmp_path):
    """Trend filtered by dimension returns only that dimension."""
    db_path = tmp_path / "metrics.db"
    recorder = MetricsRecorder(str(db_path))

    recorder.record(
        [EvalResult(QualityDimension.SAFETY, 1.0, True, {"ok": True})],
        eval_type="filing",
    )
    recorder.record(
        [EvalResult(QualityDimension.FORMAT, 0.5, True, {"ok": True})],
        eval_type="filing",
    )
    recorder.record(
        [EvalResult(QualityDimension.SAFETY, 0.9, True, {"ok": True})],
        eval_type="filing",
    )

    safety_trend = recorder.get_trend("filing", "safety")
    assert isinstance(safety_trend, list)
    assert len(safety_trend) >= 1


def test_metrics_detect_regression_stable(tmp_path):
    """Stable scores return STABLE status."""
    db_path = tmp_path / "metrics.db"
    recorder = MetricsRecorder(str(db_path))

    for _ in range(20):
        recorder.record(
            [EvalResult(QualityDimension.SAFETY, 0.85, True, {"ok": True})],
            eval_type="filing",
        )
        time.sleep(0.001)

    result = recorder.detect_regression("filing", "safety", window=10)
    assert result["status"] == "STABLE"
    assert result["delta"] is not None
    assert abs(result["delta"]) < 0.1


def test_metrics_detect_regression_dropping(tmp_path):
    """Dropping scores return REGRESSION status."""
    db_path = tmp_path / "metrics.db"
    recorder = MetricsRecorder(str(db_path))

    # Older scores: high
    for _ in range(10):
        recorder.record(
            [EvalResult(QualityDimension.FORMAT, 0.95, True, {"ok": True})],
            eval_type="filing",
        )
        time.sleep(0.001)

    # Recent scores: low
    for _ in range(10):
        recorder.record(
            [EvalResult(QualityDimension.FORMAT, 0.50, True, {"ok": True})],
            eval_type="filing",
        )
        time.sleep(0.001)

    result = recorder.detect_regression("filing", "format", window=10)
    assert result["status"] == "REGRESSION"
    assert result["delta"] < -0.1
    assert result["current_mean"] < result["baseline_mean"]


def test_metrics_detect_regression_insufficient(tmp_path):
    """Too few data points returns INSUFFICIENT_DATA."""
    db_path = tmp_path / "metrics.db"
    recorder = MetricsRecorder(str(db_path))

    recorder.record(
        [EvalResult(QualityDimension.SAFETY, 0.9, True, {"ok": True})],
        eval_type="filing",
    )

    result = recorder.detect_regression("filing", "safety", window=10)
    assert result["status"] == "INSUFFICIENT_DATA"


def test_metrics_dashboard(tmp_path):
    """Dashboard returns summary stats."""
    db_path = tmp_path / "metrics.db"
    recorder = MetricsRecorder(str(db_path))

    recorder.record(
        [EvalResult(QualityDimension.SAFETY, 1.0, True, {"ok": True})],
        eval_type="filing",
    )
    recorder.record(
        [EvalResult(QualityDimension.SAFETY, 0.8, True, {"ok": True})],
        eval_type="filing",
    )
    recorder.record(
        [EvalResult(QualityDimension.FORMAT, 0.5, False, {"poor": True})],
        eval_type="filing",
    )

    dash = recorder.get_dashboard("filing")
    assert dash["total_evaluations"] == 3
    assert "safety" in dash["dimensions"]
    assert "format" in dash["dimensions"]
    assert dash["dimensions"]["safety"]["count"] == 2
    assert dash["dimensions"]["safety"]["avg_score"] > 0.8
    assert 0.0 < dash["overall_pass_rate"] <= 1.0


def test_metrics_empty_db(tmp_path):
    """Empty DB returns safe defaults, doesn't crash."""
    db_path = tmp_path / "metrics.db"
    recorder = MetricsRecorder(str(db_path))

    dash = recorder.get_dashboard()
    assert dash["total_evaluations"] == 0
    assert dash["dimensions"] == {}
    assert dash["overall_pass_rate"] == 0.0

    trend = recorder.get_trend("filing")
    assert trend == []


# ===========================================================================
# 5. INTEGRATION TESTS (7 tests)
# ===========================================================================


def test_evaluate_text_full_pipeline(tmp_path):
    """Full evaluation pipeline on sample filing text."""
    db_path = tmp_path / "eval_int.db"

    text = (
        "IN THE CIRCUIT COURT FOR THE COUNTY OF MUSKEGON\n"
        "Case No. 2024-001507-DC\n"
        "ANDREW JAMES PIGORS, Plaintiff\n"
        "v.\n"
        "EMILY A. WATSON, Defendant\n\n"
        "## ISSUE\n"
        "Whether the court erred in suspending all parenting time.\n\n"
        "## RULE\n"
        "Under MCL 722.27(1)(c), the court may modify custody upon showing "
        "proper cause or change of circumstances. MCR 2.119(F)(3) governs "
        "motions for reconsideration.\n\n"
        "## APPLICATION\n"
        "Here, Plaintiff demonstrates that the minor child has been separated "
        "from his father since July 29, 2025. The established custodial environment "
        "was disrupted without adequate due process.\n\n"
        "## CONCLUSION\n"
        "Plaintiff, appearing pro se, respectfully requests this Court restore "
        "parenting time immediately.\n\n"
        "CERTIFICATE OF SERVICE\n"
        "I certify that I served the foregoing on all parties.\n"
    )

    summary = evaluate_text(text, db_path=str(db_path))
    assert isinstance(summary, dict)
    assert "results" in summary
    assert len(summary["results"]) == 5  # correctness, safety, format, groundedness, completeness
    assert "overall_score" in summary
    assert "overall_passed" in summary


def test_evaluate_text_no_db(tmp_path):
    """evaluate_text works with a temp DB."""
    db_path = tmp_path / "nodb.db"
    summary = evaluate_text("Simple text.", db_path=str(db_path))
    assert isinstance(summary, dict)
    assert "results" in summary
    for r in summary["results"]:
        assert "dimension" in r
        assert "score" in r


def test_quick_safety_check_pass():
    """Clean text passes quick check."""
    safe = quick_safety_check(
        "Plaintiff, appearing pro se, moves for an order pursuant to MCL 722.23."
    )
    assert safe is True


def test_quick_safety_check_fail():
    """Unsafe text fails quick check."""
    safe = quick_safety_check(
        "The LitigationOS database scored Lincoln David Watson's case "
        "via the undersigned counsel's EGCP analysis."
    )
    assert safe is False


def test_eval_suite_all_dimensions(tmp_path):
    """All quality dimensions scored by AgentEvalSuite."""
    db_path = tmp_path / "suite.db"
    suite = AgentEvalSuite(db_path=str(db_path))

    results = suite.evaluate_filing_output(
        "## ISSUE\nWhether...\n## RULE\nUnder MCL 722.23...\n"
        "## APPLICATION\nHere the minor child...\n## CONCLUSION\nTherefore...\n",
    )

    returned_dims = {r.dimension for r in results}
    # evaluate_filing_output returns 5 results (correctness, safety, format,
    # groundedness, completeness) — consistency not included
    assert len(returned_dims) == 5


def test_eval_suite_records_to_db(tmp_path):
    """Suite evaluates and results can be recorded to DB."""
    db_path = tmp_path / "record.db"
    suite = AgentEvalSuite(db_path=str(db_path))

    results = suite.evaluate_filing_output(
        "Test text with MCL 722.23 citation."
    )

    recorder = MetricsRecorder(str(db_path))
    recorder.record(results, eval_type="filing")

    conn = sqlite3.connect(str(db_path))
    count = conn.execute("SELECT COUNT(*) FROM eval_metrics").fetchone()[0]
    conn.close()
    assert count >= 5  # one per evaluator


def test_eval_result_serialization():
    """EvalResult can be converted to dict for JSON storage."""
    result = EvalResult(
        dimension=QualityDimension.SAFETY,
        score=0.95,
        passed=True,
        checks={"check1": True, "check2": True},
        details="All checks passed",
    )
    d = result.to_dict()
    assert d["dimension"] == "safety"
    assert d["score"] == 0.95
    assert d["passed"] is True
    assert d["checks"] == {"check1": True, "check2": True}
    assert d["details"] == "All checks passed"

    # Must be JSON-serializable
    json_str = json.dumps(d)
    assert '"safety"' in json_str
    roundtrip = json.loads(json_str)
    assert roundtrip == d


# ===========================================================================
# 6. EDGE CASE TESTS (8 tests)
# ===========================================================================


def test_eval_empty_text():
    """Empty string doesn't crash any evaluator."""
    result = SafetyChecker.check_all("")
    assert result.passed is True

    has_irac, sections = FormatChecker.check_irac("")
    assert has_irac is False

    citations = CitationVerifier().extract_citations("")
    assert citations == []

    summary = evaluate_text("", db_path="")
    assert isinstance(summary, dict)
    assert "results" in summary


def test_eval_very_long_text():
    """10,000+ char text handles correctly."""
    paragraph = (
        "Plaintiff respectfully submits that under MCL 722.23, "
        "the best interest factors weigh in favor of modification. "
    )
    text = paragraph * 200  # ~12,000+ chars
    assert len(text) > 10000

    result = SafetyChecker.check_all(text)
    assert result.passed is True

    citations = CitationVerifier().extract_citations(text)
    # Deduplicated to one unique citation
    mcl_cites = [c for c in citations if "MCL 722.23" in c]
    assert len(mcl_cites) == 1

    summary = evaluate_text(text, db_path="")
    assert isinstance(summary, dict)
    assert "results" in summary


def test_eval_unicode_text():
    """Unicode characters (§, ¶, —, etc.) handled."""
    text = (
        "Pursuant to 42 USC § 1983, Plaintiff alleges violations of the "
        "Fourteenth Amendment — specifically, denial of due process.\n"
        "¶ 12. The court's ex parte order violated Plaintiff's rights.\n"
        "See Troxel v Granville, 530 US 57 (2000).\n"
        "† This footnote references MCR 2.003(C)(1)(b).\n"
    )
    result = SafetyChecker.check_all(text)
    assert isinstance(result.passed, bool)

    citations = CitationVerifier().extract_citations(text)
    assert any("MCR" in c for c in citations)


def test_eval_none_handling_safety():
    """None values handled gracefully where possible."""
    # SafetyChecker methods should handle empty strings at minimum
    for checker in [
        SafetyChecker.check_child_name,
        SafetyChecker.check_ai_references,
        SafetyChecker.check_hallucinations,
        SafetyChecker.check_party_names,
    ]:
        safe, violations = checker("")
        assert safe is True
        assert violations == []


def test_eval_special_chars():
    """Legal special chars (§, ¶, †, ‡) don't break regex patterns."""
    text = "§ 1983 ¶ 12 † footnote ‡ cross-ref MCL 722.23(j)"
    citations = CitationVerifier().extract_citations(text)
    assert any("MCL" in c for c in citations)

    # Safety should not crash on special chars
    result = SafetyChecker.check_all(text)
    assert isinstance(result.passed, bool)


def test_eval_newlines_and_whitespace():
    """Various whitespace patterns don't break detection."""
    text = (
        "Lincoln\n  David\n   Watson\nwas present.\n"
        "The\n\tLitigationOS\nsystem was referenced."
    )
    # Child name detection works across simple whitespace in regex
    safe_child, v_child = SafetyChecker.check_child_name(text)
    # Note: the regex uses \s+ which matches newlines, so this should detect
    assert not safe_child

    safe_ai, v_ai = SafetyChecker.check_ai_references(text)
    assert not safe_ai


def test_eval_quality_dimension_enum():
    """QualityDimension enum has all expected members."""
    dims = set(QualityDimension)
    assert len(dims) == 6
    assert QualityDimension.CORRECTNESS in dims
    assert QualityDimension.COMPLETENESS in dims
    assert QualityDimension.GROUNDEDNESS in dims
    assert QualityDimension.SAFETY in dims
    assert QualityDimension.FORMAT in dims
    assert QualityDimension.CONSISTENCY in dims


def test_eval_result_defaults():
    """EvalResult default fields are correct."""
    result = EvalResult(
        dimension=QualityDimension.SAFETY,
        score=0.5,
        passed=True,
    )
    assert result.checks == {}
    assert result.details == ""
    assert result.to_dict()["checks"] == {}
    assert result.to_dict()["details"] == ""
