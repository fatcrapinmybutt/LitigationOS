"""Tests for vector_search_bridge.py and vector_monitor.py.

Comprehensive unit tests covering enums, dataclasses, metadata index,
VectorSearchBridge, QueryLatencyTracker, EmbeddingDriftDetector,
ReindexScheduler, VectorMonitor health checks, HTML dashboard, and
metrics export.

100 % self-contained: no database, no file I/O, no network.
"""
from __future__ import annotations

import collections
import json
import math
import pathlib
import time
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, mock_open

# ── Modules under test ────────────────────────────────────────────
from .. import vector_search_bridge as vsb
from .. import vector_monitor as vm


# ===================================================================
# vector_search_bridge.py — Enums
# ===================================================================

class TestSearchBackendEnum(unittest.TestCase):
    """SearchBackend enum values."""

    def test_brute_force(self):
        self.assertEqual(vsb.SearchBackend.BRUTE_FORCE.value, "brute_force")

    def test_hnsw(self):
        self.assertEqual(vsb.SearchBackend.HNSW.value, "hnsw")

    def test_hnsw_quantized(self):
        self.assertEqual(vsb.SearchBackend.HNSW_QUANTIZED.value, "hnsw_int8")

    def test_auto(self):
        self.assertEqual(vsb.SearchBackend.AUTO.value, "auto")

    def test_enum_count(self):
        self.assertEqual(len(vsb.SearchBackend), 4)


# ===================================================================
# vector_search_bridge.py — VectorSearchConfig
# ===================================================================

class TestVectorSearchConfig(unittest.TestCase):
    """VectorSearchConfig dataclass defaults and to_dict."""

    def test_defaults(self):
        cfg = vsb.VectorSearchConfig()
        self.assertEqual(cfg.backend, vsb.SearchBackend.AUTO)
        self.assertEqual(cfg.hnsw_ef_search, 64)
        self.assertEqual(cfg.top_k, 10)
        self.assertTrue(cfg.rerank)
        self.assertEqual(cfg.rerank_top_n, 50)
        self.assertIsNone(cfg.metadata_filter)
        self.assertTrue(cfg.fallback_to_brute_force)
        self.assertAlmostEqual(cfg.min_score, 0.1)

    def test_custom_values(self):
        cfg = vsb.VectorSearchConfig(
            backend=vsb.SearchBackend.HNSW,
            top_k=20,
            rerank=False,
        )
        self.assertEqual(cfg.backend, vsb.SearchBackend.HNSW)
        self.assertEqual(cfg.top_k, 20)
        self.assertFalse(cfg.rerank)

    def test_to_dict_keys(self):
        d = vsb.VectorSearchConfig().to_dict()
        expected = {
            "backend", "hnsw_ef_search", "top_k", "rerank",
            "rerank_top_n", "metadata_filter", "fallback_to_brute_force",
            "min_score",
        }
        self.assertEqual(set(d.keys()), expected)

    def test_to_dict_backend_is_string(self):
        d = vsb.VectorSearchConfig().to_dict()
        self.assertEqual(d["backend"], "auto")


# ===================================================================
# vector_search_bridge.py — VectorSearchResult
# ===================================================================

class TestVectorSearchResult(unittest.TestCase):
    """VectorSearchResult dataclass creation and to_dict."""

    def test_creation(self):
        r = vsb.VectorSearchResult(
            doc_id=42, score=0.95, text="Sample text",
            source_table="evidence_quotes",
        )
        self.assertEqual(r.doc_id, 42)
        self.assertAlmostEqual(r.score, 0.95)
        self.assertEqual(r.text, "Sample text")

    def test_default_fields(self):
        r = vsb.VectorSearchResult(
            doc_id=1, score=0.5, text="t", source_table="s",
        )
        self.assertIsNone(r.lane)
        self.assertIsNone(r.doc_type)
        self.assertEqual(r.metadata, {})
        self.assertEqual(r.search_method, "unknown")
        self.assertAlmostEqual(r.latency_ms, 0.0)

    def test_to_dict_keys(self):
        r = vsb.VectorSearchResult(
            doc_id=1, score=0.8, text="t", source_table="s",
        )
        d = r.to_dict()
        expected = {
            "doc_id", "score", "text", "source_table", "lane",
            "doc_type", "metadata", "search_method", "latency_ms",
        }
        self.assertEqual(set(d.keys()), expected)

    def test_to_dict_score_rounded(self):
        r = vsb.VectorSearchResult(
            doc_id=1, score=0.123456789, text="t", source_table="s",
        )
        d = r.to_dict()
        self.assertEqual(d["score"], round(0.123456789, 6))


# ===================================================================
# vector_search_bridge.py — Pure-python math helpers
# ===================================================================

class TestPurePythonMath(unittest.TestCase):
    """Test _dot_py, _norm_py, _cosine_py, _normalise_py."""

    def test_dot_py(self):
        self.assertAlmostEqual(vsb._dot_py([1, 2, 3], [4, 5, 6]), 32.0)

    def test_norm_py(self):
        self.assertAlmostEqual(vsb._norm_py([3, 4]), 5.0)

    def test_norm_py_zero(self):
        self.assertAlmostEqual(vsb._norm_py([0, 0]), 0.0)

    def test_cosine_py_identical(self):
        v = [0.5, 0.3, 0.8]
        self.assertAlmostEqual(vsb._cosine_py(v, v), 1.0, places=5)

    def test_cosine_py_orthogonal(self):
        self.assertAlmostEqual(vsb._cosine_py([1, 0], [0, 1]), 0.0, places=5)

    def test_cosine_py_zero_vec(self):
        self.assertAlmostEqual(vsb._cosine_py([0, 0], [1, 1]), 0.0)

    def test_normalise_py(self):
        v = vsb._normalise_py([3, 4])
        magnitude = math.sqrt(sum(x * x for x in v))
        self.assertAlmostEqual(magnitude, 1.0, places=5)

    def test_normalise_py_zero_vec(self):
        v = vsb._normalise_py([0.0, 0.0])
        self.assertEqual(v, [0.0, 0.0])

    def test_brute_cosine_topk(self):
        query = [1.0, 0.0, 0.0]
        matrix = [
            [1.0, 0.0, 0.0],  # cos = 1.0
            [0.0, 1.0, 0.0],  # cos = 0.0
            [0.5, 0.5, 0.0],  # cos ≈ 0.707
        ]
        results = vsb._brute_cosine_topk(query, matrix, k=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0][1], 0)  # highest score idx
        self.assertAlmostEqual(results[0][0], 1.0, places=3)


# ===================================================================
# vector_search_bridge.py — MetadataIndex
# ===================================================================

class TestMetadataIndex(unittest.TestCase):
    """MetadataIndex in-memory operations."""

    def setUp(self):
        self.idx = vsb.MetadataIndex(db_path=pathlib.Path("/fake/db.db"))

    def test_add_and_filter_by_lane(self):
        self.idx.add(1, {"lane": "A", "doc_type": "evidence"})
        self.idx.add(2, {"lane": "B", "doc_type": "evidence"})
        self.idx.add(3, {"lane": "A", "doc_type": "rule"})
        result = self.idx.filter_ids({"lane": "A"})
        self.assertEqual(result, {1, 3})

    def test_filter_by_doc_type(self):
        self.idx.add(10, {"doc_type": "evidence"})
        self.idx.add(11, {"doc_type": "rule"})
        self.idx.add(12, {"doc_type": "evidence"})
        result = self.idx.filter_ids({"doc_type": "evidence"})
        self.assertEqual(result, {10, 12})

    def test_filter_multiple_criteria(self):
        self.idx.add(1, {"lane": "A", "doc_type": "evidence", "source_table": "evidence_quotes"})
        self.idx.add(2, {"lane": "A", "doc_type": "rule", "source_table": "auth_rules"})
        self.idx.add(3, {"lane": "B", "doc_type": "evidence", "source_table": "evidence_quotes"})
        result = self.idx.filter_ids({"lane": "A", "doc_type": "evidence"})
        self.assertEqual(result, {1})

    def test_filter_no_criteria_returns_all(self):
        self.idx.add(1, {"lane": "A"})
        self.idx.add(2, {"lane": "B"})
        result = self.idx.filter_ids({})
        self.assertEqual(result, {1, 2})

    def test_filter_nonexistent_lane(self):
        self.idx.add(1, {"lane": "A"})
        result = self.idx.filter_ids({"lane": "Z"})
        self.assertEqual(result, set())

    def test_get_stats(self):
        self.idx.add(1, {"lane": "A", "doc_type": "evidence", "source_table": "t1"})
        stats = self.idx.get_stats()
        self.assertEqual(stats["total_docs"], 1)
        self.assertIn("A", stats["lanes"])
        self.assertIn("evidence", stats["doc_types"])

    def test_filter_by_source_table(self):
        self.idx.add(1, {"source_table": "evidence_quotes"})
        self.idx.add(2, {"source_table": "auth_rules"})
        result = self.idx.filter_ids({"source_table": "evidence_quotes"})
        self.assertEqual(result, {1})


# ===================================================================
# vector_search_bridge.py — _vehicle_to_lane helper
# ===================================================================

class TestVehicleToLane(unittest.TestCase):
    """_vehicle_to_lane mapping tests."""

    def test_custody_lane_a(self):
        self.assertEqual(vsb._vehicle_to_lane("Watson Custody"), "A")

    def test_housing_lane_b(self):
        self.assertEqual(vsb._vehicle_to_lane("Shady Oaks Housing"), "B")

    def test_ppo_lane_d(self):
        self.assertEqual(vsb._vehicle_to_lane("PPO 2023-5907"), "D")

    def test_misconduct_lane_e(self):
        self.assertEqual(vsb._vehicle_to_lane("McNeill Misconduct"), "E")

    def test_appellate_lane_f(self):
        self.assertEqual(vsb._vehicle_to_lane("COA 366810"), "F")

    def test_convergence_lane_c(self):
        self.assertEqual(vsb._vehicle_to_lane("convergence multi-lane"), "C")

    def test_empty_returns_none(self):
        self.assertIsNone(vsb._vehicle_to_lane(""))

    def test_unrecognized_returns_none(self):
        self.assertIsNone(vsb._vehicle_to_lane("completely unknown vehicle"))


# ===================================================================
# vector_search_bridge.py — VectorSearchBridge
# ===================================================================

class TestVectorSearchBridge(unittest.TestCase):
    """VectorSearchBridge with mocked internals."""

    def test_init_default_config(self):
        bridge = vsb.VectorSearchBridge()
        self.assertIsInstance(bridge._config, vsb.VectorSearchConfig)
        self.assertFalse(bridge._hnsw_active)
        self.assertEqual(bridge._query_count, 0)

    def test_init_custom_config(self):
        cfg = vsb.VectorSearchConfig(top_k=20, rerank=False)
        bridge = vsb.VectorSearchBridge(config=cfg)
        self.assertEqual(bridge._config.top_k, 20)
        self.assertFalse(bridge._config.rerank)

    def test_search_without_initialisation_returns_empty(self):
        bridge = vsb.VectorSearchBridge()
        # _vectors is None → search_by_vector returns []
        results = bridge.search_by_vector([0.1] * 300)
        self.assertEqual(results, [])

    def test_search_with_no_transform_returns_empty(self):
        bridge = vsb.VectorSearchBridge()
        # No vectoriser loaded → _transform_query returns None → search returns []
        results = bridge.search("test query")
        self.assertEqual(results, [])

    def test_search_with_lane_creates_filter(self):
        bridge = vsb.VectorSearchBridge()
        with patch.object(bridge, "search", return_value=[]) as mock_search:
            bridge.search_with_lane("test query", "A", top_k=5)
            mock_search.assert_called_once()
            call_args = mock_search.call_args
            cfg = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("config")
            if cfg is None:
                cfg = call_args[0][1]
            self.assertEqual(cfg.metadata_filter, {"lane": "A"})

    def test_get_index_health_no_files(self):
        bridge = vsb.VectorSearchBridge()
        with patch.object(pathlib.Path, "exists", return_value=False):
            health = bridge.get_index_health()
        self.assertFalse(health["hnsw_active"])
        self.assertEqual(health["index_doc_count"], 0)

    def test_get_stats_returns_dict(self):
        bridge = vsb.VectorSearchBridge()
        stats = bridge.get_stats()
        self.assertIn("bridge_version", stats)
        self.assertIn("hnsw_active", stats)
        self.assertIn("query_count", stats)
        self.assertIn("config", stats)
        self.assertIn("metadata_stats", stats)

    def test_get_stats_avg_latency_zero_queries(self):
        bridge = vsb.VectorSearchBridge()
        stats = bridge.get_stats()
        self.assertAlmostEqual(stats["avg_latency_ms"], 0.0)

    def test_batch_search_returns_list_of_lists(self):
        bridge = vsb.VectorSearchBridge()
        results = bridge.batch_search(["q1", "q2"])
        self.assertEqual(len(results), 2)
        for r in results:
            self.assertIsInstance(r, list)

    def test_is_index_stale_no_files(self):
        bridge = vsb.VectorSearchBridge()
        with patch.object(pathlib.Path, "exists", return_value=False):
            self.assertTrue(bridge._is_index_stale())

    @patch.object(vsb.VectorSearchBridge, "_transform_query")
    @patch.object(vsb.VectorSearchBridge, "search_by_vector")
    def test_search_records_latency(self, mock_sbv, mock_tq):
        bridge = vsb.VectorSearchBridge()
        mock_tq.return_value = [0.1] * 300
        mock_sbv.return_value = [
            vsb.VectorSearchResult(doc_id=1, score=0.9, text="t", source_table="s")
        ]
        results = bridge.search("test query")
        self.assertEqual(len(results), 1)
        self.assertGreater(bridge._query_count, 0)


# ===================================================================
# vector_monitor.py — Enums
# ===================================================================

class TestHealthStatusEnum(unittest.TestCase):
    """HealthStatus enum values."""

    def test_healthy(self):
        self.assertEqual(vm.HealthStatus.HEALTHY.value, "healthy")

    def test_degraded(self):
        self.assertEqual(vm.HealthStatus.DEGRADED.value, "degraded")

    def test_critical(self):
        self.assertEqual(vm.HealthStatus.CRITICAL.value, "critical")

    def test_offline(self):
        self.assertEqual(vm.HealthStatus.OFFLINE.value, "offline")

    def test_enum_count(self):
        self.assertEqual(len(vm.HealthStatus), 4)


# ===================================================================
# vector_monitor.py — LatencyStats
# ===================================================================

class TestLatencyStats(unittest.TestCase):
    """LatencyStats dataclass."""

    def test_defaults(self):
        s = vm.LatencyStats()
        self.assertAlmostEqual(s.p50_ms, 0.0)
        self.assertAlmostEqual(s.p95_ms, 0.0)
        self.assertEqual(s.sample_count, 0)

    def test_custom_values(self):
        s = vm.LatencyStats(p50_ms=10.5, p95_ms=50.2, p99_ms=100.8,
                            avg_ms=30.1, min_ms=2.0, max_ms=200.0,
                            sample_count=1000)
        self.assertAlmostEqual(s.p50_ms, 10.5)
        self.assertEqual(s.sample_count, 1000)

    def test_to_dict_keys(self):
        d = vm.LatencyStats().to_dict()
        expected = {"p50_ms", "p95_ms", "p99_ms", "avg_ms", "min_ms", "max_ms", "sample_count"}
        self.assertEqual(set(d.keys()), expected)

    def test_to_dict_rounds_values(self):
        s = vm.LatencyStats(p50_ms=10.123456789)
        d = s.to_dict()
        self.assertEqual(d["p50_ms"], round(10.123456789, 3))


# ===================================================================
# vector_monitor.py — IndexHealth
# ===================================================================

class TestIndexHealth(unittest.TestCase):
    """IndexHealth dataclass."""

    def test_defaults(self):
        h = vm.IndexHealth()
        self.assertEqual(h.name, "")
        self.assertEqual(h.status, vm.HealthStatus.OFFLINE)
        self.assertEqual(h.doc_count, 0)
        self.assertFalse(h.needs_rebuild)

    def test_to_dict_status_as_string(self):
        h = vm.IndexHealth(name="lsi", status=vm.HealthStatus.HEALTHY)
        d = h.to_dict()
        self.assertEqual(d["status"], "healthy")
        self.assertEqual(d["name"], "lsi")

    def test_to_dict_last_query_ms_none(self):
        d = vm.IndexHealth().to_dict()
        self.assertIsNone(d["last_query_ms"])

    def test_to_dict_last_query_ms_present(self):
        h = vm.IndexHealth(last_query_ms=42.567)
        d = h.to_dict()
        self.assertEqual(d["last_query_ms"], round(42.567, 3))


# ===================================================================
# vector_monitor.py — SearchQualityMetric
# ===================================================================

class TestSearchQualityMetric(unittest.TestCase):
    """SearchQualityMetric dataclass."""

    def test_creation(self):
        m = vm.SearchQualityMetric(
            query="test", backend="hnsw", latency_ms=12.5,
            result_count=10, top_score=0.95,
        )
        self.assertEqual(m.query, "test")
        self.assertEqual(m.result_count, 10)

    def test_to_dict_keys(self):
        d = vm.SearchQualityMetric().to_dict()
        expected = {"query", "backend", "latency_ms", "result_count",
                    "top_score", "avg_score", "timestamp"}
        self.assertEqual(set(d.keys()), expected)

    def test_to_dict_rounds(self):
        m = vm.SearchQualityMetric(top_score=0.123456789)
        d = m.to_dict()
        self.assertEqual(d["top_score"], round(0.123456789, 6))


# ===================================================================
# vector_monitor.py — QueryLatencyTracker
# ===================================================================

class TestQueryLatencyTracker(unittest.TestCase):
    """QueryLatencyTracker percentile computation."""

    def test_empty_tracker(self):
        t = vm.QueryLatencyTracker()
        stats = t.get_stats()
        self.assertAlmostEqual(stats.p50_ms, 0.0)
        self.assertEqual(stats.sample_count, 0)

    def test_record_and_get_stats(self):
        t = vm.QueryLatencyTracker()
        for i in range(100):
            t.record("hnsw", float(i))
        stats = t.get_stats("hnsw")
        self.assertEqual(stats.sample_count, 100)
        self.assertAlmostEqual(stats.min_ms, 0.0)
        self.assertAlmostEqual(stats.max_ms, 99.0)
        # P50 should be around 49-50
        self.assertGreater(stats.p50_ms, 40)
        self.assertLess(stats.p50_ms, 60)

    def test_p95_and_p99(self):
        t = vm.QueryLatencyTracker()
        for i in range(1000):
            t.record("brute", float(i))
        stats = t.get_stats("brute")
        # P95 ≈ 949-950, P99 ≈ 989-990
        self.assertGreater(stats.p95_ms, 900)
        self.assertGreater(stats.p99_ms, 980)

    def test_aggregate_across_backends(self):
        t = vm.QueryLatencyTracker()
        for i in range(50):
            t.record("hnsw", float(i))
            t.record("brute", float(i + 50))
        stats = t.get_stats()  # aggregate
        self.assertEqual(stats.sample_count, 100)

    def test_get_slow_queries_below_threshold(self):
        t = vm.QueryLatencyTracker()
        for i in range(10):
            t.record("fast_backend", float(i))  # max 9ms
        slow = t.get_slow_queries(threshold_ms=100.0)
        self.assertEqual(slow, [])

    def test_get_slow_queries_above_threshold(self):
        t = vm.QueryLatencyTracker()
        for i in range(100):
            t.record("slow_backend", float(i * 10))  # up to 990ms
        slow = t.get_slow_queries(threshold_ms=100.0)
        self.assertGreater(len(slow), 0)
        self.assertEqual(slow[0]["backend"], "slow_backend")

    def test_reset(self):
        t = vm.QueryLatencyTracker()
        t.record("hnsw", 10.0)
        t.reset()
        stats = t.get_stats()
        self.assertEqual(stats.sample_count, 0)

    def test_get_stats_all_backends(self):
        t = vm.QueryLatencyTracker()
        t.record("hnsw", 5.0)
        t.record("brute", 50.0)
        all_stats = t.get_stats_all_backends()
        self.assertIn("hnsw", all_stats)
        self.assertIn("brute", all_stats)

    def test_single_sample_percentile(self):
        t = vm.QueryLatencyTracker()
        t.record("test", 42.0)
        stats = t.get_stats("test")
        self.assertAlmostEqual(stats.p50_ms, 42.0)
        self.assertAlmostEqual(stats.p99_ms, 42.0)

    def test_circular_buffer_max_samples(self):
        t = vm.QueryLatencyTracker(max_samples=10)
        for i in range(100):
            t.record("test", float(i))
        stats = t.get_stats("test")
        # Only last 10 should remain (90-99)
        self.assertEqual(stats.sample_count, 10)
        self.assertAlmostEqual(stats.min_ms, 90.0)


# ===================================================================
# vector_monitor.py — EmbeddingDriftDetector
# ===================================================================

class TestEmbeddingDriftDetector(unittest.TestCase):
    """EmbeddingDriftDetector drift computation."""

    def test_drift_score_no_data(self):
        d = vm.EmbeddingDriftDetector()
        self.assertAlmostEqual(d.compute_drift_score(), 0.0)

    def test_drift_score_insufficient_queries(self):
        d = vm.EmbeddingDriftDetector()
        d.record_index_sample([[1.0, 0.0], [0.0, 1.0]])
        for _ in range(5):  # need >=10
            d.record_query_vector([0.5, 0.5])
        self.assertAlmostEqual(d.compute_drift_score(), 0.0)

    def test_should_reindex_low_drift(self):
        d = vm.EmbeddingDriftDetector(threshold=0.5)
        # Without data, drift = 0 → should not reindex
        self.assertFalse(d.should_reindex())

    def test_record_query_vector_updates_count(self):
        d = vm.EmbeddingDriftDetector()
        d.record_query_vector([0.1, 0.2, 0.3])
        self.assertEqual(d._query_count, 1)
        d.record_query_vector([0.4, 0.5, 0.6])
        self.assertEqual(d._query_count, 2)

    def test_record_index_sample(self):
        d = vm.EmbeddingDriftDetector()
        sample = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        d.record_index_sample(sample)
        self.assertEqual(d._index_sample_count, 3)
        self.assertIsNotNone(d._index_centroid)

    def test_record_index_sample_empty(self):
        d = vm.EmbeddingDriftDetector()
        d.record_index_sample([])
        self.assertEqual(d._index_sample_count, 0)

    def test_drift_score_with_similar_data(self):
        d = vm.EmbeddingDriftDetector()
        # Index and query vectors are from the same distribution
        index_vecs = [[1.0, 0.0, 0.0]] * 50
        d.record_index_sample(index_vecs)
        for _ in range(20):
            d.record_query_vector([1.0, 0.0, 0.0])
        score = d.compute_drift_score()
        # Similar distribution → low drift
        self.assertLess(score, 0.3)

    def test_drift_score_with_dissimilar_data(self):
        d = vm.EmbeddingDriftDetector()
        index_vecs = [[1.0, 0.0, 0.0]] * 50
        d.record_index_sample(index_vecs)
        # Query vectors pointing in completely different direction
        for _ in range(20):
            d.record_query_vector([0.0, 0.0, 100.0])
        score = d.compute_drift_score()
        # Dissimilar → higher drift
        self.assertGreater(score, 0.1)

    def test_get_stats(self):
        d = vm.EmbeddingDriftDetector()
        stats = d.get_stats()
        self.assertIn("drift_score", stats)
        self.assertIn("threshold", stats)
        self.assertIn("should_reindex", stats)
        self.assertIn("index_sample_count", stats)
        self.assertIn("query_count", stats)


# ===================================================================
# vector_monitor.py — ReindexScheduler
# ===================================================================

class TestReindexScheduler(unittest.TestCase):
    """ReindexScheduler scheduling and trigger tests."""

    def test_schedule_rebuild_returns_job_id(self):
        s = vm.ReindexScheduler()
        job_id = s.schedule_rebuild("stale index")
        self.assertIsInstance(job_id, str)
        self.assertGreater(len(job_id), 0)

    def test_get_pending_rebuilds(self):
        s = vm.ReindexScheduler()
        s.schedule_rebuild("reason 1")
        s.schedule_rebuild("reason 2")
        pending = s.get_pending_rebuilds()
        self.assertEqual(len(pending), 2)

    def test_mark_complete(self):
        s = vm.ReindexScheduler()
        job_id = s.schedule_rebuild("test rebuild")
        s.mark_complete(job_id)
        pending = s.get_pending_rebuilds()
        self.assertEqual(len(pending), 0)
        self.assertEqual(len(s._completed), 1)

    def test_mark_complete_nonexistent_job(self):
        s = vm.ReindexScheduler()
        # Should not raise
        s.mark_complete("nonexistent_id")

    def test_check_triggers_never_built(self):
        s = vm.ReindexScheduler()
        triggers = s.check_triggers()
        self.assertTrue(triggers["time_based"])

    def test_check_triggers_recently_built(self):
        s = vm.ReindexScheduler()
        s.set_last_index_info(time.time(), 1000)
        triggers = s.check_triggers(current_doc_count=1000)
        self.assertFalse(triggers["time_based"])
        self.assertFalse(triggers["count_based"])

    def test_check_triggers_stale_time(self):
        s = vm.ReindexScheduler(max_age_hours=1)
        # Set last index to 2 hours ago
        s.set_last_index_info(time.time() - 7200, 1000)
        triggers = s.check_triggers(current_doc_count=1000)
        self.assertTrue(triggers["time_based"])

    def test_check_triggers_doc_count_drift(self):
        s = vm.ReindexScheduler(doc_delta_threshold=100)
        s.set_last_index_info(time.time(), 1000)
        triggers = s.check_triggers(current_doc_count=1200)
        self.assertTrue(triggers["count_based"])

    def test_check_triggers_drift_based(self):
        mock_drift = MagicMock()
        mock_drift.should_reindex.return_value = True
        s = vm.ReindexScheduler(drift_detector=mock_drift)
        triggers = s.check_triggers()
        self.assertTrue(triggers["drift_based"])

    def test_check_triggers_no_drift(self):
        mock_drift = MagicMock()
        mock_drift.should_reindex.return_value = False
        s = vm.ReindexScheduler(drift_detector=mock_drift)
        s.set_last_index_info(time.time(), 1000)
        triggers = s.check_triggers(current_doc_count=1000)
        self.assertFalse(triggers["drift_based"])

    def test_get_stats(self):
        s = vm.ReindexScheduler()
        s.schedule_rebuild("test")
        stats = s.get_stats()
        self.assertIn("pending_count", stats)
        self.assertIn("completed_count", stats)
        self.assertEqual(stats["pending_count"], 1)


# ===================================================================
# vector_monitor.py — VectorMonitor
# ===================================================================

class TestVectorMonitor(unittest.TestCase):
    """VectorMonitor health checks and dashboard."""

    def _make_monitor(self):
        return vm.VectorMonitor()

    @patch.object(pathlib.Path, "exists", return_value=False)
    def test_check_all_health_no_files(self, mock_exists):
        m = self._make_monitor()
        health = m.check_all_health()
        self.assertIn("lsi", health)
        self.assertIn("hnsw", health)
        self.assertIn("bm25", health)
        self.assertIn("fts5", health)
        self.assertIn("vectorizer", health)
        self.assertIn("svd_model", health)
        # All offline when no files exist
        for name, h in health.items():
            self.assertEqual(h.status, vm.HealthStatus.OFFLINE, f"{name} should be OFFLINE")

    def test_record_search(self):
        m = self._make_monitor()
        m.record_search("hnsw", "test query", 15.0, 10, 0.95)
        self.assertEqual(len(m._search_log), 1)
        metric = m._search_log[0]
        self.assertEqual(metric.backend, "hnsw")
        self.assertEqual(metric.result_count, 10)

    def test_record_search_updates_latency(self):
        m = self._make_monitor()
        m.record_search("brute", "query", 50.0, 5, 0.8)
        stats = m.latency_tracker.get_stats("brute")
        self.assertEqual(stats.sample_count, 1)
        self.assertAlmostEqual(stats.p50_ms, 50.0)

    @patch.object(vm.VectorMonitor, "check_all_health")
    def test_get_dashboard_data(self, mock_health):
        m = self._make_monitor()
        mock_health.return_value = {
            "lsi": vm.IndexHealth(name="lsi", status=vm.HealthStatus.HEALTHY),
        }
        data = m.get_dashboard_data()
        self.assertIn("generated_at", data)
        self.assertIn("uptime_minutes", data)
        self.assertIn("health", data)
        self.assertIn("latency", data)
        self.assertIn("drift", data)
        self.assertIn("reindex", data)
        self.assertIn("recommendations", data)

    @patch.object(vm.VectorMonitor, "check_all_health")
    def test_generate_html_dashboard(self, mock_health):
        m = self._make_monitor()
        mock_health.return_value = {
            "lsi": vm.IndexHealth(name="lsi", status=vm.HealthStatus.HEALTHY),
            "hnsw": vm.IndexHealth(name="hnsw", status=vm.HealthStatus.OFFLINE),
        }
        html = m.generate_html_dashboard()
        self.assertIsInstance(html, str)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("Vector Search Monitor", html)
        self.assertIn("Component Health", html)
        self.assertIn("Query Latency", html)
        self.assertIn("Embedding Drift", html)
        self.assertIn("Recommendations", html)
        self.assertIn("</html>", html)

    @patch.object(vm.VectorMonitor, "check_all_health")
    def test_generate_html_dashboard_has_inline_css(self, mock_health):
        m = self._make_monitor()
        mock_health.return_value = {}
        html = m.generate_html_dashboard()
        self.assertIn("<style>", html)
        self.assertIn("background:#0d1117", html)

    @patch.object(pathlib.Path, "exists", return_value=False)
    def test_get_recommendations_no_data(self, mock_exists):
        m = self._make_monitor()
        recs = m.get_recommendations()
        self.assertIsInstance(recs, list)

    def test_get_recommendations_slow_latency(self):
        m = self._make_monitor()
        # Record very slow queries
        for _ in range(20):
            m.latency_tracker.record("slow_backend", 600.0)
        recs = m.get_recommendations()
        has_latency_rec = any("latency" in r.lower() or "P99" in r or "P95" in r for r in recs)
        self.assertTrue(has_latency_rec, f"Expected latency recommendation, got: {recs}")

    @patch.object(vm.VectorMonitor, "get_dashboard_data")
    def test_export_metrics(self, mock_data):
        m = self._make_monitor()
        mock_data.return_value = {"test": "data", "generated_at": "now"}
        # Use mock_open to avoid real file I/O
        with patch("builtins.open", mock_open()) as mf:
            with patch.object(pathlib.Path, "mkdir"):
                path = m.export_metrics("/fake/output.json")
        self.assertEqual(path, "/fake/output.json")

    @patch.object(pathlib.Path, "exists", return_value=False)
    def test_get_stats(self, mock_exists):
        m = self._make_monitor()
        stats = m.get_stats()
        self.assertIn("monitor_version", stats)
        self.assertIn("uptime_minutes", stats)
        self.assertIn("total_searches_recorded", stats)
        self.assertIn("latency_aggregate", stats)
        self.assertIn("drift", stats)
        self.assertIn("reindex_scheduler", stats)

    def test_health_history_accumulates(self):
        m = self._make_monitor()
        with patch.object(pathlib.Path, "exists", return_value=False):
            m.check_all_health()
            m.check_all_health()
        self.assertEqual(len(m._health_history), 2)

    def test_search_log_bounded(self):
        m = self._make_monitor()
        for i in range(3000):
            m.record_search("test", f"q{i}", 1.0, 1, 0.5)
        # Bounded by maxlen=2000
        self.assertLessEqual(len(m._search_log), 2000)


# ===================================================================
# vector_monitor.py — helper functions
# ===================================================================

class TestMonitorHelpers(unittest.TestCase):
    """Test vector_monitor utility functions."""

    def test_file_size_mb_missing(self):
        with patch.object(pathlib.Path, "exists", return_value=False):
            result = vm._file_size_mb(pathlib.Path("/fake/file.txt"))
        self.assertAlmostEqual(result, 0.0)

    def test_file_age_hours_missing(self):
        with patch.object(pathlib.Path, "exists", return_value=False):
            result = vm._file_age_hours(pathlib.Path("/fake/file.txt"))
        self.assertAlmostEqual(result, 0.0)

    def test_esc_html(self):
        result = vm._esc('<script>alert("xss")</script>')
        self.assertNotIn("<script>", result)
        self.assertIn("&lt;script&gt;", result)

    def test_esc_ampersand(self):
        result = vm._esc("A & B")
        self.assertIn("&amp;", result)


# ===================================================================
# Integration-level: cross-module consistency
# ===================================================================

class TestCrossModuleConsistency(unittest.TestCase):
    """Verify that bridge and monitor interact correctly."""

    def test_bridge_stats_and_monitor_stats_independent(self):
        bridge = vsb.VectorSearchBridge()
        monitor = vm.VectorMonitor()
        b_stats = bridge.get_stats()
        m_stats = monitor.get_stats()
        # Both should be valid dicts with no shared state issues
        self.assertIsInstance(b_stats, dict)
        self.assertIsInstance(m_stats, dict)
        self.assertIn("bridge_version", b_stats)
        self.assertIn("monitor_version", m_stats)

    def test_monitor_records_bridge_style_search(self):
        monitor = vm.VectorMonitor()
        # Simulate what VectorSearchBridge would call
        monitor.record_search("hnsw", "MCR 2.003 disqualification", 15.5, 8, 0.92)
        monitor.record_search("brute_force", "MCL 722.23", 120.0, 5, 0.78)
        stats = monitor.latency_tracker.get_stats()
        self.assertEqual(stats.sample_count, 2)

    def test_metadata_index_works_standalone(self):
        idx = vsb.MetadataIndex(db_path=pathlib.Path("/fake/db.db"))
        idx.add(1, {"lane": "A", "doc_type": "evidence"})
        idx.add(2, {"lane": "E", "doc_type": "violation"})
        # Filter should work without any DB
        self.assertEqual(idx.filter_ids({"lane": "E"}), {2})


if __name__ == "__main__":
    unittest.main()
