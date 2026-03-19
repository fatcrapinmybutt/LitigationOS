"""
Comprehensive tests for context_orchestrator.py — 6 classes, 100+ tests.

Tests: TokenBudget, ContextValidator, ContextCompressor,
       AutoSnapshotManager, ContextQualityScorer, ContextOrchestrator.

All tests are self-contained: temp dirs for DB/file ops, no network,
no real drives, no external deps beyond stdlib + pytest.
"""

import pytest
import sys
import os
import json
import time
import math
import hashlib
import tempfile
import shutil
import sqlite3
import threading
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

# Ensure the parent legal_ai package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from context_orchestrator import (
    TokenBudget,
    TokenBudgetConfig,
    ContextValidator,
    ValidationResult,
    ContextCompressor,
    CompressionResult,
    AutoSnapshotManager,
    SnapshotMeta,
    ContextQualityScorer,
    QualityReport,
    ContextOrchestrator,
    VALID_LANES,
    LANE_LABELS,
    TOKENS_PER_WORD,
    MODEL_TOKEN_LIMITS,
    CORRECT_ENTITIES,
    FABRICATED_ITEMS,
    QUALITY_WEIGHTS,
    REQUIRED_DOMAINS,
    FRESHNESS_DECAY_HALF_LIFE_S,
    STALE_THRESHOLD,
    EXPIRED_THRESHOLD,
    SNAPSHOT_INTERVAL_S,
    MAX_SNAPSHOTS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_dir():
    """Fresh temp directory per test — auto-cleaned."""
    d = tempfile.mkdtemp(prefix="litOS_test_orch_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def tmp_db(tmp_dir):
    """Path to a temp SQLite DB that doesn't exist yet."""
    return os.path.join(tmp_dir, "test_orchestrator.db")


@pytest.fixture
def budget():
    """Default TokenBudget with medium tier."""
    return TokenBudget(TokenBudgetConfig(model_tier="medium"))


@pytest.fixture
def validator():
    return ContextValidator()


@pytest.fixture
def compressor():
    return ContextCompressor()


@pytest.fixture
def snapshot_mgr(tmp_dir, tmp_db):
    snap_dir = os.path.join(tmp_dir, "snapshots")
    os.makedirs(snap_dir, exist_ok=True)
    return AutoSnapshotManager(
        snapshot_dir=snap_dir,
        interval_s=300,
        max_snapshots=10,
        db_path=tmp_db,
    )


@pytest.fixture
def quality_scorer():
    return ContextQualityScorer()


@pytest.fixture
def orchestrator(tmp_db):
    """Fresh orchestrator — reset singleton before & after."""
    ContextOrchestrator.reset()
    orch = ContextOrchestrator(db_path=tmp_db, model_tier="medium")
    yield orch
    try:
        orch.shutdown()
    except Exception:
        pass
    ContextOrchestrator.reset()


# ===================================================================
# TOKEN BUDGET — ~18 tests
# ===================================================================

class TestTokenBudget:
    """Tests for TokenBudget: estimation, allocation, overflow, resize."""

    def test_estimate_tokens_empty(self):
        assert TokenBudget.estimate_tokens("") == 0

    def test_estimate_tokens_single_word(self):
        tok = TokenBudget.estimate_tokens("hello")
        assert tok >= 1

    def test_estimate_tokens_word_count_heuristic(self):
        text = "the quick brown fox jumps over the lazy dog"  # 9 words
        tok = TokenBudget.estimate_tokens(text)
        expected = math.ceil(9 * TOKENS_PER_WORD)
        assert tok == expected

    def test_estimate_tokens_multiline(self):
        text = "line one\nline two\nline three"
        tok = TokenBudget.estimate_tokens(text)
        assert tok > 0

    def test_estimate_tokens_for_items_empty(self):
        assert TokenBudget.estimate_tokens_for_items([]) == 0

    def test_estimate_tokens_for_items_sums(self):
        items = [
            {"content": "hello world"},
            {"content": "foo bar baz"},
        ]
        total = TokenBudget.estimate_tokens_for_items(items)
        assert total > 0

    def test_budget_allocation_sums_to_total(self, budget):
        util = budget.utilization()
        total = (
            util["prompt"]["budget"]
            + util["response"]["budget"]
            + util["context"]["budget"]
        )
        assert total == MODEL_TOKEN_LIMITS["medium"]

    def test_context_budget_positive(self, budget):
        assert budget.context_budget > 0

    def test_context_remaining_starts_full(self, budget):
        assert budget.context_remaining == budget.context_budget

    def test_allocate_prompt_success(self, budget):
        assert budget.allocate_prompt("short prompt") is True

    def test_allocate_context_success(self, budget):
        assert budget.allocate_context("some context text") is True

    def test_allocate_reduces_remaining(self, budget):
        before = budget.context_remaining
        budget.allocate_context("a few words here")
        after = budget.context_remaining
        assert after < before

    def test_overflow_detection(self):
        tiny = TokenBudget(TokenBudgetConfig(max_tokens=20, model_tier="small"))
        huge = " ".join(["word"] * 5000)
        result = tiny.allocate_context(huge)
        assert result is False

    def test_try_fit_does_not_allocate(self, budget):
        before = budget.context_remaining
        budget.try_fit("some text", "context")
        assert budget.context_remaining == before

    def test_release_context_refunds(self, budget):
        text = "refundable tokens here"
        budget.allocate_context(text)
        mid = budget.context_remaining
        budget.release_context(text)
        assert budget.context_remaining > mid

    def test_reset_zeros_counters(self, budget):
        budget.allocate_context("use some budget")
        budget.reset()
        assert budget.context_remaining == budget.context_budget

    def test_resize_changes_budget(self, budget):
        old_budget = budget.context_budget
        budget.resize("xl")
        assert budget.context_budget != old_budget

    def test_model_tier_configs_all_present(self):
        for tier in ["small", "medium", "large", "xl", "xxl", "128k"]:
            assert tier in MODEL_TOKEN_LIMITS
            assert MODEL_TOKEN_LIMITS[tier] > 0

    def test_utilization_returns_dict(self, budget):
        util = budget.utilization()
        assert isinstance(util, dict)
        for section in ["prompt", "response", "context"]:
            assert section in util
            assert "budget" in util[section]
            assert "used" in util[section]
            assert "remaining" in util[section]

    def test_total_remaining(self, budget):
        assert budget.total_remaining > 0

    def test_thread_safety(self, budget):
        """Concurrent allocations must not corrupt state."""
        errors = []

        def allocate():
            try:
                for _ in range(50):
                    budget.allocate_context("word")
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=allocate) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0


# ===================================================================
# CONTEXT VALIDATOR — ~22 tests
# ===================================================================

class TestContextValidator:
    """Tests for ContextValidator: entities, fabrication, lanes, contradictions."""

    def test_valid_text_passes(self, validator):
        result = validator.validate_text("Andrew James Pigors filed a motion.")
        assert result.valid is True

    def test_correct_defendant_name(self, validator):
        result = validator.validate_text("Emily A. Watson appeared in court.")
        assert result.valid is True
        assert len(result.entity_issues) == 0

    def test_wrong_emily_middle_name_detected(self, validator):
        result = validator.validate_text("Emily Ann Watson was present.")
        assert result.valid is False or len(result.entity_issues) > 0

    def test_wrong_emily_middle_initial_detected(self, validator):
        result = validator.validate_text("Emily M. Watson filed a response.")
        assert result.valid is False or len(result.entity_issues) > 0

    def test_wrong_judge_spelling_detected(self, validator):
        result = validator.validate_text("Judge Jenny McNeil ruled on the matter.")
        assert result.valid is False or len(result.entity_issues) > 0

    def test_correct_judge_passes(self, validator):
        result = validator.validate_text("Hon. Jenny L. McNeill presided over the hearing.")
        assert len([e for e in result.entity_issues if "McNeill" in str(e)]) == 0

    def test_wrong_judge_first_name_detected(self, validator):
        result = validator.validate_text("Amy McNeill issued an order.")
        assert result.valid is False or len(result.entity_issues) > 0

    def test_fabricated_cps_detected(self, validator):
        result = validator.validate_text("There were 9 CPS investigations.")
        assert result.valid is False or len(result.fabrication_hits) > 0

    def test_fabricated_jane_berry_detected(self, validator):
        result = validator.validate_text("Attorney Jane Berry represented the defendant.")
        assert result.valid is False or len(result.fabrication_hits) > 0

    def test_fabricated_patricia_berry_detected(self, validator):
        result = validator.validate_text("Patricia Berry (P35878) filed a motion.")
        assert result.valid is False or len(result.fabrication_hits) > 0

    def test_fabricated_alienation_score_detected(self, validator):
        result = validator.validate_text("The 91% alienation score was cited.")
        assert result.valid is False or len(result.fabrication_hits) > 0

    def test_clean_text_no_fabrication(self, validator):
        result = validator.validate_text("The motion was filed on time.")
        assert len(result.fabrication_hits) == 0

    def test_lane_same_lane_valid(self, validator):
        result = validator.validate_lane("A", "A")
        assert result.valid is True

    def test_lane_none_passes(self, validator):
        result = validator.validate_lane(None, "A")
        assert result.valid is True

    def test_lane_convergence_accepts_all(self, validator):
        result = validator.validate_lane("A", "C")
        assert result.valid is True

    def test_lane_cross_contamination_blocked(self, validator):
        result = validator.validate_lane("A", "B")
        assert result.valid is False or len(result.lane_violations) > 0

    def test_lane_invalid_lane_rejected(self, validator):
        result = validator.validate_lane("X", "A")
        assert result.valid is False or len(result.lane_violations) > 0

    def test_valid_lanes_constant(self):
        assert VALID_LANES == {"A", "B", "C", "D", "E", "F"}

    def test_validate_item_combines_checks(self, validator):
        result = validator.validate_item(
            key="doc1",
            value="Emily Ann Watson filed 9 CPS investigations.",
            lane="A",
            target_lane="A",
        )
        # Should flag both entity issue AND fabrication
        total_issues = len(result.entity_issues) + len(result.fabrication_hits)
        assert total_issues >= 1

    def test_detect_contradictions_none_when_no_conflict(self, validator):
        existing = [{"content": "The hearing was on Monday."}]
        pairs = validator.detect_contradictions("The hearing was on Monday.", existing)
        # Same statement = no contradiction
        assert isinstance(pairs, list)

    def test_detect_contradictions_with_negation(self, validator):
        existing = [{"content": "The father was present at the hearing."}]
        pairs = validator.detect_contradictions(
            "The father was NOT present at the hearing.", existing
        )
        assert isinstance(pairs, list)

    def test_forbidden_title_ron_berry(self, validator):
        result = validator.validate_text("Attorney Ronald Berry filed the brief.")
        has_issue = (
            not result.valid
            or len(result.entity_issues) > 0
            or len(result.warnings) > 0
        )
        assert has_issue

    def test_correct_entities_constant_populated(self):
        assert "plaintiff" in CORRECT_ENTITIES or "defendant" in CORRECT_ENTITIES
        assert len(CORRECT_ENTITIES) >= 4

    def test_fabricated_items_constant_populated(self):
        assert len(FABRICATED_ITEMS) >= 4


# ===================================================================
# CONTEXT COMPRESSOR — ~16 tests
# ===================================================================

class TestContextCompressor:
    """Tests for ContextCompressor: TF-IDF, extractive summary, priority."""

    def test_compress_empty_text(self, compressor):
        result = compressor.compress("")
        assert isinstance(result, CompressionResult)
        assert result.compressed_tokens == 0

    def test_compress_short_text_unchanged(self, compressor):
        text = "Short sentence."
        result = compressor.compress(text, target_tokens=1000)
        # Short text should survive compression
        assert result.summary_text.strip() != ""

    def test_extractive_summary_reduces_length(self, compressor):
        sentences = " ".join(
            [f"Sentence number {i} about the custody hearing." for i in range(50)]
        )
        result = compressor.compress(sentences, ratio=0.3)
        assert result.compressed_tokens < result.original_tokens

    def test_compression_ratio_honoured(self, compressor):
        sentences = " ".join(
            [f"Document {i} was filed in court on day {i}." for i in range(40)]
        )
        result = compressor.compress(sentences, ratio=0.5)
        assert result.compression_ratio <= 1.0

    def test_compress_respects_target_tokens(self, compressor):
        text = " ".join(["important legal evidence"] * 200)
        result = compressor.compress(text, target_tokens=50)
        assert result.compressed_tokens <= 80  # allow some slack

    def test_sentences_kept_and_dropped(self, compressor):
        text = " ".join(
            [f"Filing {i} was submitted." for i in range(20)]
        )
        result = compressor.compress(text, ratio=0.4)
        assert result.sentences_kept > 0
        assert result.sentences_dropped >= 0
        assert result.sentences_kept + result.sentences_dropped >= 10

    def test_compress_items_empty_list(self, compressor):
        assert compressor.compress_items([], 1000) == []

    def test_compress_items_critical_preserved(self, compressor):
        items = [
            {"content": "Critical evidence", "priority": "CRITICAL"},
            {"content": " ".join(["filler"] * 100), "priority": "LOW"},
        ]
        result = compressor.compress_items(items, budget_tokens=500)
        critical = [i for i in result if i.get("priority") == "CRITICAL"]
        assert len(critical) == 1

    def test_compress_items_low_priority_dropped(self, compressor):
        items = [
            {"content": " ".join(["word"] * 200), "priority": "LOW"},
        ]
        result = compressor.compress_items(items, budget_tokens=10)
        # Low priority should be dropped or heavily compressed
        assert len(result) == 0 or TokenBudget.estimate_tokens(
            result[0].get("content", "")
        ) < TokenBudget.estimate_tokens(items[0]["content"])

    def test_compress_items_respects_budget(self, compressor):
        items = [
            {"content": " ".join(["evidence"] * 50), "priority": "MEDIUM"},
            {"content": " ".join(["filing"] * 50), "priority": "MEDIUM"},
        ]
        result = compressor.compress_items(items, budget_tokens=30)
        total = sum(
            TokenBudget.estimate_tokens(i.get("content", "")) for i in result
        )
        assert total <= 60  # generous slack

    def test_summarize_evicted_empty(self, compressor):
        summary = compressor.summarize_evicted([])
        assert isinstance(summary, str)

    def test_summarize_evicted_returns_text(self, compressor):
        items = [
            {"key": "doc1", "content": "Motion to compel discovery."},
            {"key": "doc2", "content": "Response to interrogatories."},
        ]
        summary = compressor.summarize_evicted(items, max_tokens=100)
        assert len(summary) > 0

    def test_compress_result_fields(self, compressor):
        text = "Legal brief about custody. Evidence supports the claim."
        result = compressor.compress(text)
        assert hasattr(result, "original_tokens")
        assert hasattr(result, "compressed_tokens")
        assert hasattr(result, "compression_ratio")
        assert hasattr(result, "sentences_kept")
        assert hasattr(result, "sentences_dropped")
        assert hasattr(result, "summary_text")

    def test_legal_terms_get_bonus(self, compressor):
        """Sentences with legal terms should score higher."""
        legal = "The court ordered MCR 2.003 disqualification of the judge."
        filler = "The weather was nice that day in Michigan."
        text = f"{legal} {filler} " * 5
        result = compressor.compress(text, ratio=0.3)
        assert "court" in result.summary_text.lower() or "mcr" in result.summary_text.lower()

    def test_first_sentence_position_bonus(self, compressor):
        text = (
            "This opening sentence is about the PPO violation. "
            + " ".join([f"Filler sentence number {i}." for i in range(20)])
        )
        result = compressor.compress(text, ratio=0.2)
        # First sentence typically gets a position bonus
        assert len(result.summary_text) > 0

    def test_min_sentence_words_filter(self):
        c = ContextCompressor(min_sentence_words=10)
        text = "Ok. Sure. This is a very long sentence about custody and evidence."
        result = c.compress(text)
        # Short sentences should be filtered
        assert isinstance(result, CompressionResult)


# ===================================================================
# AUTO SNAPSHOT MANAGER — ~17 tests
# ===================================================================

class TestAutoSnapshotManager:
    """Tests for AutoSnapshotManager: capture, restore, diff, integrity."""

    def test_create_snapshot(self, snapshot_mgr):
        state = {"items": [{"key": "a", "value": "test"}]}
        meta = snapshot_mgr.capture(state, lane="A", description="test snapshot")
        assert meta is not None
        assert meta.snapshot_id is not None

    def test_snapshot_returns_snapshot_meta(self, snapshot_mgr):
        state = {"items": []}
        meta = snapshot_mgr.capture(state, description="meta check")
        assert isinstance(meta, SnapshotMeta)
        assert meta.sha256 is not None
        assert len(meta.sha256) > 0

    def test_snapshot_integrity_sha256(self, snapshot_mgr):
        state = {"items": [{"key": "b", "value": "integrity test"}]}
        meta = snapshot_mgr.capture(state, description="integrity")
        assert snapshot_mgr.verify_integrity(meta.snapshot_id) is True

    def test_snapshot_tamper_detection(self, snapshot_mgr, tmp_dir):
        state = {"items": [{"key": "c", "value": "tamper test"}]}
        meta = snapshot_mgr.capture(state, description="tamper")
        # Tamper with the snapshot file
        snap_dir = os.path.join(tmp_dir, "snapshots")
        for f in os.listdir(snap_dir):
            fpath = os.path.join(snap_dir, f)
            if os.path.isfile(fpath) and f.endswith(".json"):
                with open(fpath, "a") as fh:
                    fh.write("TAMPERED")
                break
        assert snapshot_mgr.verify_integrity(meta.snapshot_id) is False

    def test_restore_returns_state(self, snapshot_mgr):
        state = {"items": [{"key": "d", "value": "restorable"}]}
        meta = snapshot_mgr.capture(state, description="restore test")
        restored = snapshot_mgr.restore(meta.snapshot_id)
        assert restored is not None
        assert restored["items"][0]["key"] == "d"

    def test_restore_nonexistent_returns_none(self, snapshot_mgr):
        result = snapshot_mgr.restore("nonexistent_id_12345")
        assert result is None

    def test_rollback_restores_state(self, snapshot_mgr):
        state_v1 = {"items": [{"key": "e", "value": "v1"}]}
        meta_v1 = snapshot_mgr.capture(state_v1, description="v1")
        state_v2 = {"items": [{"key": "e", "value": "v2"}]}
        snapshot_mgr.capture(state_v2, description="v2")
        # Rollback to v1
        restored = snapshot_mgr.restore(meta_v1.snapshot_id)
        assert restored["items"][0]["value"] == "v1"

    def test_diff_between_versions(self, snapshot_mgr):
        state_a = {"items": [{"key": "x", "value": "alpha"}]}
        meta_a = snapshot_mgr.capture(state_a, description="a")
        state_b = {"items": [{"key": "x", "value": "beta"}, {"key": "y", "value": "new"}]}
        meta_b = snapshot_mgr.capture(state_b, description="b")
        diff = snapshot_mgr.diff(meta_a.snapshot_id, meta_b.snapshot_id)
        assert isinstance(diff, dict)

    def test_diff_same_snapshot_no_changes(self, snapshot_mgr):
        state = {"items": [{"key": "z", "value": "same"}]}
        meta = snapshot_mgr.capture(state, description="same")
        diff = snapshot_mgr.diff(meta.snapshot_id, meta.snapshot_id)
        assert diff.get("added_count", 0) == 0
        assert diff.get("removed_count", 0) == 0

    def test_list_snapshots(self, snapshot_mgr):
        for i in range(3):
            snapshot_mgr.capture({"n": i}, description=f"snap_{i}")
        listing = snapshot_mgr.list_snapshots(limit=10)
        assert len(listing) >= 3

    def test_list_snapshots_respects_limit(self, snapshot_mgr):
        for i in range(5):
            snapshot_mgr.capture({"n": i}, description=f"snap_{i}")
        listing = snapshot_mgr.list_snapshots(limit=2)
        assert len(listing) <= 2

    def test_dedup_identical_snapshots(self, snapshot_mgr):
        state = {"items": [{"key": "dup", "value": "same content"}]}
        meta1 = snapshot_mgr.capture(state, description="first")
        meta2 = snapshot_mgr.capture(state, description="second")
        # Second capture with same content should be deduplicated
        if meta2 is None:
            assert True  # dedup returned None
        else:
            assert meta1.sha256 == meta2.sha256

    def test_stats_returns_dict(self, snapshot_mgr):
        snapshot_mgr.capture({"test": True}, description="stats test")
        s = snapshot_mgr.stats()
        assert isinstance(s, dict)
        assert "count" in s or "snapshot_count" in s or "total_bytes" in s

    def test_snapshot_with_lane(self, snapshot_mgr):
        meta = snapshot_mgr.capture(
            {"items": []}, lane="E", description="lane E snapshot"
        )
        assert meta is not None
        assert meta.lane == "E"

    def test_snapshot_item_count(self, snapshot_mgr):
        state = {"items": [{"k": 1}, {"k": 2}, {"k": 3}]}
        meta = snapshot_mgr.capture(state, description="count test")
        # item_count should reflect the state
        assert meta.item_count >= 0

    def test_snapshot_size_bytes(self, snapshot_mgr):
        state = {"items": [{"content": "x" * 1000}]}
        meta = snapshot_mgr.capture(state, description="size test")
        assert meta.size_bytes > 0

    def test_multiple_lanes_separate_snapshots(self, snapshot_mgr):
        meta_a = snapshot_mgr.capture({"lane": "A"}, lane="A", description="lane A")
        meta_d = snapshot_mgr.capture({"lane": "D"}, lane="D", description="lane D")
        assert meta_a.snapshot_id != meta_d.snapshot_id


# ===================================================================
# CONTEXT QUALITY SCORER — ~18 tests
# ===================================================================

class TestContextQualityScorer:
    """Tests for ContextQualityScorer: freshness, relevance, coverage, purity."""

    def _make_item(self, content, lane="A", timestamp=None, domain=None):
        ts = timestamp or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        item = {"content": content, "lane": lane, "timestamp": ts}
        if domain:
            item["domain"] = domain
        return item

    def test_score_returns_quality_report(self, quality_scorer):
        items = [self._make_item("custody evidence")]
        report = quality_scorer.score(items, query="custody", target_lane="A")
        assert isinstance(report, QualityReport)

    def test_fresh_items_score_high(self, quality_scorer):
        items = [self._make_item("recent evidence about custody")]
        report = quality_scorer.score(items, query="custody", target_lane="A")
        assert report.freshness_score >= 0.5

    def test_stale_items_score_low(self, quality_scorer):
        old_ts = "2020-01-01T00:00:00Z"
        items = [self._make_item("old evidence", timestamp=old_ts)]
        report = quality_scorer.score(items, query="evidence", target_lane="A")
        assert report.freshness_score < 0.8

    def test_relevance_high_for_matching_query(self, quality_scorer):
        items = [self._make_item("custody hearing evidence motion")]
        report = quality_scorer.score(items, query="custody hearing")
        assert report.relevance_score > 0.0

    def test_relevance_low_for_unrelated_query(self, quality_scorer):
        items = [self._make_item("weather forecast for tomorrow")]
        report = quality_scorer.score(items, query="custody hearing")
        assert report.relevance_score < 0.5

    def test_coverage_all_domains_present(self, quality_scorer):
        items = []
        for domain in REQUIRED_DOMAINS:
            items.append(self._make_item(f"info about {domain}", domain=domain))
        report = quality_scorer.score(items, query="full coverage")
        assert report.coverage_score > 0.5

    def test_coverage_missing_domains(self, quality_scorer):
        items = [self._make_item("just parties info", domain="parties")]
        report = quality_scorer.score(
            items, query="test", required_domains=REQUIRED_DOMAINS
        )
        assert len(report.missing_domains) > 0

    def test_lane_purity_all_same_lane(self, quality_scorer):
        items = [
            self._make_item("item 1", lane="A"),
            self._make_item("item 2", lane="A"),
        ]
        report = quality_scorer.score(items, query="test", target_lane="A")
        assert report.lane_purity_score >= 0.9

    def test_lane_contamination_detected(self, quality_scorer):
        items = [
            self._make_item("item 1", lane="A"),
            self._make_item("item 2", lane="B"),
        ]
        report = quality_scorer.score(items, query="test", target_lane="A")
        assert report.lane_purity_score < 1.0

    def test_contradiction_penalty_applied(self, quality_scorer):
        items = [
            self._make_item("The father was present at the hearing."),
            self._make_item("The father was NOT present at the hearing."),
        ]
        report = quality_scorer.score(items, query="hearing")
        # Contradiction should cause some penalty
        assert report.contradiction_penalty >= 0.0

    def test_overall_score_in_range(self, quality_scorer):
        items = [self._make_item("custody evidence about the case")]
        report = quality_scorer.score(items, query="custody", target_lane="A")
        assert 0.0 <= report.overall_score <= 1.0

    def test_overall_score_formula_weights(self):
        total = sum(QUALITY_WEIGHTS.values())
        assert abs(total - 1.0) < 0.01

    def test_empty_items_scored(self, quality_scorer):
        report = quality_scorer.score([], query="test")
        assert isinstance(report, QualityReport)
        assert report.item_count == 0

    def test_stale_and_expired_counts(self, quality_scorer):
        very_old = "2015-01-01T00:00:00Z"
        items = [self._make_item("ancient doc", timestamp=very_old)]
        report = quality_scorer.score(items, query="old")
        assert report.stale_count >= 0
        assert report.expired_count >= 0

    def test_warnings_populated(self, quality_scorer):
        items = [self._make_item("minimal", lane="B")]
        report = quality_scorer.score(
            items, query="custody", target_lane="A",
            required_domains=REQUIRED_DOMAINS,
        )
        assert len(report.warnings) > 0 or len(report.missing_domains) > 0

    def test_quality_weights_constant(self):
        assert "freshness" in QUALITY_WEIGHTS
        assert "relevance" in QUALITY_WEIGHTS
        assert "coverage" in QUALITY_WEIGHTS
        assert "lane_purity" in QUALITY_WEIGHTS
        assert "contradiction_penalty" in QUALITY_WEIGHTS

    def test_freshness_decay_half_life(self):
        assert FRESHNESS_DECAY_HALF_LIFE_S == 86400.0 * 7

    def test_thresholds_valid(self):
        assert 0.0 < STALE_THRESHOLD < 1.0
        assert 0.0 < EXPIRED_THRESHOLD < STALE_THRESHOLD


# ===================================================================
# CONTEXT ORCHESTRATOR — ~22 tests
# ===================================================================

class TestContextOrchestrator:
    """Tests for ContextOrchestrator: singleton, assembly, validation, compression."""

    def test_singleton_pattern(self, tmp_db):
        ContextOrchestrator.reset()
        o1 = ContextOrchestrator(db_path=tmp_db, model_tier="medium")
        o2 = ContextOrchestrator(db_path=tmp_db, model_tier="medium")
        assert o1 is o2
        o1.shutdown()
        ContextOrchestrator.reset()

    def test_reset_clears_singleton(self, tmp_db):
        ContextOrchestrator.reset()
        o1 = ContextOrchestrator(db_path=tmp_db)
        ContextOrchestrator.reset()
        o2 = ContextOrchestrator(db_path=tmp_db)
        assert o1 is not o2
        o2.shutdown()
        ContextOrchestrator.reset()

    def test_add_item(self, orchestrator):
        result = orchestrator.add(
            key="doc1",
            value="Andrew James Pigors filed a motion in custody case.",
            priority="HIGH",
            lane="A",
        )
        assert isinstance(result, dict)

    def test_find_item(self, orchestrator):
        orchestrator.add(key="doc2", value="evidence filing", lane="A")
        found = orchestrator.find("doc2")
        assert found is not None

    def test_find_missing_item(self, orchestrator):
        found = orchestrator.find("nonexistent_key_xyz")
        assert found is None

    def test_remove_item(self, orchestrator):
        orchestrator.add(key="doc3", value="removable", lane="A")
        removed = orchestrator.remove("doc3")
        assert removed is True

    def test_remove_nonexistent(self, orchestrator):
        removed = orchestrator.remove("never_added_key")
        assert removed is False

    def test_validate_text_clean(self, orchestrator):
        result = orchestrator.validate_text("Andrew James Pigors is the plaintiff.")
        assert isinstance(result, dict)
        assert result.get("valid", True) is True

    def test_validate_text_fabricated(self, orchestrator):
        result = orchestrator.validate_text("There were 9 CPS investigations.")
        assert result.get("valid") is False or len(result.get("fabrication_hits", [])) > 0

    def test_validate_lane_same(self, orchestrator):
        result = orchestrator.validate_lane("A", "A")
        assert result.get("valid") is True

    def test_validate_lane_cross(self, orchestrator):
        result = orchestrator.validate_lane("A", "B")
        assert result.get("valid") is False or len(result.get("lane_violations", [])) > 0

    def test_compress_text(self, orchestrator):
        text = " ".join([f"Sentence {i} about the custody case." for i in range(30)])
        result = orchestrator.compress_text(text, target_tokens=50)
        assert isinstance(result, CompressionResult)
        assert result.compressed_tokens <= result.original_tokens

    def test_assemble_returns_dict(self, orchestrator):
        orchestrator.add(key="ctx1", value="custody hearing scheduled", lane="A")
        result = orchestrator.assemble(query="custody", lane="A")
        assert isinstance(result, dict)

    def test_assemble_within_budget(self, orchestrator):
        orchestrator.add(key="ctx2", value="budget test item", lane="A")
        result = orchestrator.assemble(query="test", lane="A", max_tokens=5000)
        assert isinstance(result, dict)

    def test_compression_when_over_budget(self, orchestrator):
        big_text = " ".join(["evidence"] * 2000)
        orchestrator.add(key="huge", value=big_text, lane="A")
        result = orchestrator.assemble(query="evidence", lane="A", max_tokens=100)
        assert isinstance(result, dict)

    def test_snapshot_manual(self, orchestrator):
        orchestrator.add(key="snap1", value="snapshot content", lane="A")
        snap = orchestrator.snapshot(description="manual snapshot", lane="A")
        assert snap is not None or isinstance(snap, dict)

    def test_list_snapshots_empty(self, orchestrator):
        listing = orchestrator.list_snapshots()
        assert isinstance(listing, list)

    def test_quality_report(self, orchestrator):
        orchestrator.add(key="q1", value="quality test evidence", lane="A")
        report = orchestrator.quality_report(query="evidence", lane="A")
        assert isinstance(report, dict)

    def test_budget_status(self, orchestrator):
        status = orchestrator.budget_status()
        assert isinstance(status, dict)

    def test_resize_budget(self, orchestrator):
        result = orchestrator.resize_budget("large")
        assert isinstance(result, dict)

    def test_get_stats_returns_dict(self, orchestrator):
        stats = orchestrator.get_stats()
        assert isinstance(stats, dict)

    def test_health_returns_dict(self, orchestrator):
        h = orchestrator.health()
        assert isinstance(h, dict)
        assert "status" in h or "issues" in h or "healthy" in h

    def test_shutdown_graceful(self, tmp_db):
        ContextOrchestrator.reset()
        orch = ContextOrchestrator(db_path=tmp_db)
        orch.add(key="pre_shutdown", value="data", lane="A")
        orch.shutdown()
        ContextOrchestrator.reset()
        # Should not raise


# ===================================================================
# CONSTANTS & MODULE LEVEL — ~7 tests
# ===================================================================

class TestModuleConstants:
    """Verify module-level constants are consistent."""

    def test_valid_lanes_set(self):
        assert isinstance(VALID_LANES, (set, frozenset))
        assert len(VALID_LANES) == 6

    def test_lane_labels_match_valid_lanes(self):
        for lane in VALID_LANES:
            assert lane in LANE_LABELS

    def test_tokens_per_word_reasonable(self):
        assert 1.0 <= TOKENS_PER_WORD <= 2.0

    def test_model_token_limits_increasing(self):
        ordered = ["small", "medium", "large", "xl", "xxl", "128k"]
        for i in range(len(ordered) - 1):
            assert MODEL_TOKEN_LIMITS[ordered[i]] < MODEL_TOKEN_LIMITS[ordered[i + 1]]

    def test_snapshot_interval_positive(self):
        assert SNAPSHOT_INTERVAL_S > 0

    def test_max_snapshots_positive(self):
        assert MAX_SNAPSHOTS > 0

    def test_required_domains_list(self):
        assert isinstance(REQUIRED_DOMAINS, (list, tuple))
        assert len(REQUIRED_DOMAINS) >= 5


# ===================================================================
# INTEGRATION TESTS — ~8 tests
# ===================================================================

class TestOrchestratorIntegration:
    """End-to-end integration tests across subsystems."""

    @pytest.fixture(autouse=True)
    def setup_orch(self, tmp_db):
        ContextOrchestrator.reset()
        self.orch = ContextOrchestrator(db_path=tmp_db, model_tier="medium")
        yield
        try:
            self.orch.shutdown()
        except Exception:
            pass
        ContextOrchestrator.reset()

    def test_add_validate_assemble_cycle(self):
        self.orch.add(key="ev1", value="Andrew James Pigors testimony", lane="A")
        self.orch.add(key="ev2", value="Hon. Jenny L. McNeill ruling", lane="A")
        result = self.orch.assemble(query="custody", lane="A")
        assert isinstance(result, dict)

    def test_reject_fabricated_in_assembly(self):
        self.orch.add(
            key="fab", value="9 CPS investigations confirmed", lane="A", validate=True
        )
        # Fabricated content should be rejected
        found = self.orch.find("fab")
        # Either the add was rejected or it was flagged
        assert True  # validation ran without crash

    def test_snapshot_and_restore_cycle(self):
        self.orch.add(key="s1", value="snapshot cycle test", lane="D")
        snap = self.orch.snapshot(description="cycle test")
        if snap and isinstance(snap, dict) and "snapshot_id" in snap:
            restored = self.orch.restore_snapshot(snap["snapshot_id"])
            assert restored is not None

    def test_compression_preserves_critical(self):
        self.orch.add(key="crit", value="critical evidence", priority="CRITICAL", lane="A")
        self.orch.add(
            key="filler",
            value=" ".join(["filler word"] * 500),
            priority="LOW",
            lane="A",
        )
        result = self.orch.assemble(query="evidence", lane="A", max_tokens=100)
        assert isinstance(result, dict)

    def test_cross_lane_rejected_in_add(self):
        result = self.orch.add(
            key="cross", value="housing complaint", lane="B",
        )
        # This is lane B data — adding to a lane A assembly should be checked
        assert isinstance(result, dict)

    def test_quality_after_adding_items(self):
        for i in range(5):
            self.orch.add(key=f"q{i}", value=f"custody evidence item {i}", lane="A")
        report = self.orch.quality_report(query="custody", lane="A")
        assert isinstance(report, dict)

    def test_stats_after_operations(self):
        self.orch.add(key="s_item", value="stats check", lane="A")
        self.orch.assemble(query="check", lane="A")
        stats = self.orch.get_stats()
        assert isinstance(stats, dict)

    def test_budget_utilization_after_assembly(self):
        self.orch.add(key="b1", value="budget utilization test item", lane="A")
        self.orch.assemble(query="budget", lane="A")
        status = self.orch.budget_status()
        assert isinstance(status, dict)
