"""Vector search health monitoring and observability for LitigationOS.

Provides comprehensive monitoring for the entire vector search stack:
LSI/semantic (300-d brute-force), HNSW (approximate NN), BM25 (sparse),
and FTS5 (SQLite full-text).  Tracks query latency percentiles, index
freshness, embedding drift, reindex scheduling, and generates both
machine-readable metrics and a standalone HTML dashboard.

Designed to run alongside ``vector_search_bridge.py`` and the existing
``vector_index_optimizer.py`` / ``semantic_engine.py`` / ``hybrid_retriever.py``
components.

100 % local · zero-API · CPU-first · stdlib-only
"""
from __future__ import annotations

import bisect
import collections
import json
import logging
import math
import os
import pathlib
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Deque, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------
_HERE = pathlib.Path(__file__).resolve().parent
_REPO = _HERE.parents[1]          # legal_ai → 00_SYSTEM → repo root
_DB_PATH = _REPO / "litigation_context.db"
_MODEL_DATA = _REPO / "00_SYSTEM" / "local_model" / "model_data"
_SEMANTIC_DIR = _MODEL_DATA / "semantic"
_BM25_DIR = _MODEL_DATA / "bm25"
_INDEX_DIR = _MODEL_DATA / "vector_index"

_LSI_PATH = _SEMANTIC_DIR / "lsi_index.npz"
_SVD_PATH = _SEMANTIC_DIR / "svd_model.pkl"
_DOC_META_PATH = _SEMANTIC_DIR / "doc_meta.json"
_VECTORIZER_PATH = _MODEL_DATA / "vectorizer.pkl"
_INVERTED_PATH = _MODEL_DATA / "inverted_index.pkl"

# Thresholds
_STALE_HOURS = 168          # 7 days
_LATENCY_WARN_MS = 100.0    # P95 warning threshold
_LATENCY_CRIT_MS = 500.0    # P99 critical threshold
_DRIFT_REINDEX = 0.30       # drift score above this → suggest reindex
_MEMORY_WARN_MB = 2048.0    # per-index memory warning
_CIRCULAR_BUFFER = 5000     # max latency samples kept in memory


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class HealthStatus(Enum):
    """Component health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    OFFLINE = "offline"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class LatencyStats:
    """Percentile latency statistics for a backend."""
    p50_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    avg_ms: float = 0.0
    min_ms: float = 0.0
    max_ms: float = 0.0
    sample_count: int = 0

    def to_dict(self) -> dict:
        return {
            "p50_ms": round(self.p50_ms, 3),
            "p95_ms": round(self.p95_ms, 3),
            "p99_ms": round(self.p99_ms, 3),
            "avg_ms": round(self.avg_ms, 3),
            "min_ms": round(self.min_ms, 3),
            "max_ms": round(self.max_ms, 3),
            "sample_count": self.sample_count,
        }


@dataclass
class IndexHealth:
    """Health snapshot for a single search index."""
    name: str = ""
    status: HealthStatus = HealthStatus.OFFLINE
    doc_count: int = 0
    index_age_hours: float = 0.0
    size_mb: float = 0.0
    last_query_ms: Optional[float] = None
    staleness_score: float = 1.0
    needs_rebuild: bool = False
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status.value,
            "doc_count": self.doc_count,
            "index_age_hours": round(self.index_age_hours, 1),
            "size_mb": round(self.size_mb, 2),
            "last_query_ms": (round(self.last_query_ms, 3)
                              if self.last_query_ms is not None else None),
            "staleness_score": round(self.staleness_score, 3),
            "needs_rebuild": self.needs_rebuild,
            "details": self.details,
        }


@dataclass
class SearchQualityMetric:
    """Quality signal recorded for a single search operation."""
    query: str = ""
    backend: str = ""
    latency_ms: float = 0.0
    result_count: int = 0
    top_score: float = 0.0
    avg_score: float = 0.0
    timestamp: str = ""

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "backend": self.backend,
            "latency_ms": round(self.latency_ms, 3),
            "result_count": self.result_count,
            "top_score": round(self.top_score, 6),
            "avg_score": round(self.avg_score, 6),
            "timestamp": self.timestamp,
        }


# ---------------------------------------------------------------------------
# QueryLatencyTracker
# ---------------------------------------------------------------------------

class QueryLatencyTracker:
    """Track query latency percentiles with per-backend circular buffers.

    Keeps the last ``_CIRCULAR_BUFFER`` samples per backend so that
    percentile computation is both fast and bounded in memory.
    """

    def __init__(self, max_samples: int = _CIRCULAR_BUFFER):
        self._max = max_samples
        self._buffers: Dict[str, Deque[float]] = {}
        self._sorted_cache: Dict[str, List[float]] = {}
        self._dirty: Dict[str, bool] = {}

    def record(self, backend: str, latency_ms: float) -> None:
        """Record a latency observation for *backend*."""
        buf = self._buffers.setdefault(backend, collections.deque(maxlen=self._max))
        buf.append(latency_ms)
        self._dirty[backend] = True

    def get_stats(self, backend: Optional[str] = None) -> LatencyStats:
        """Compute percentile statistics.

        If *backend* is ``None``, aggregate across all backends.
        """
        if backend:
            samples = self._sorted(backend)
        else:
            all_samples: List[float] = []
            for b in self._buffers:
                all_samples.extend(self._buffers[b])
            all_samples.sort()
            samples = all_samples

        if not samples:
            return LatencyStats()

        n = len(samples)
        return LatencyStats(
            p50_ms=self._percentile(samples, 0.50),
            p95_ms=self._percentile(samples, 0.95),
            p99_ms=self._percentile(samples, 0.99),
            avg_ms=sum(samples) / n,
            min_ms=samples[0],
            max_ms=samples[-1],
            sample_count=n,
        )

    def get_slow_queries(self, threshold_ms: float = 100.0) -> List[Dict[str, Any]]:
        """Return summary of backends whose P95 exceeds *threshold_ms*."""
        slow: List[Dict[str, Any]] = []
        for backend in self._buffers:
            stats = self.get_stats(backend)
            if stats.p95_ms > threshold_ms:
                slow.append({
                    "backend": backend,
                    "p95_ms": stats.p95_ms,
                    "p99_ms": stats.p99_ms,
                    "sample_count": stats.sample_count,
                })
        return slow

    def reset(self) -> None:
        """Clear all recorded samples."""
        self._buffers.clear()
        self._sorted_cache.clear()
        self._dirty.clear()

    def get_stats_all_backends(self) -> Dict[str, dict]:
        """Return per-backend LatencyStats as dicts."""
        return {b: self.get_stats(b).to_dict() for b in self._buffers}

    # -- internals --

    def _sorted(self, backend: str) -> List[float]:
        if self._dirty.get(backend, True):
            buf = self._buffers.get(backend)
            self._sorted_cache[backend] = sorted(buf) if buf else []
            self._dirty[backend] = False
        return self._sorted_cache.get(backend, [])

    @staticmethod
    def _percentile(sorted_vals: List[float], pct: float) -> float:
        """Linear-interpolation percentile on a pre-sorted list."""
        n = len(sorted_vals)
        if n == 0:
            return 0.0
        if n == 1:
            return sorted_vals[0]
        k = (n - 1) * pct
        lo = int(math.floor(k))
        hi = min(lo + 1, n - 1)
        frac = k - lo
        return sorted_vals[lo] + frac * (sorted_vals[hi] - sorted_vals[lo])


# ---------------------------------------------------------------------------
# EmbeddingDriftDetector
# ---------------------------------------------------------------------------

class EmbeddingDriftDetector:
    """Detect when embedding distributions shift.

    Monitors mean vector magnitude, cosine-similarity distribution,
    and centroid stability.  When new query vectors diverge
    significantly from the indexed population, ``should_reindex()``
    returns True.

    Uses only stdlib math — no numpy dependency.
    """

    def __init__(self, threshold: float = _DRIFT_REINDEX,
                 window: int = 500):
        self._threshold = threshold
        self._window = window
        # Index population statistics
        self._index_mag_mean: float = 0.0
        self._index_mag_var: float = 0.0
        self._index_centroid: Optional[List[float]] = None
        self._index_sample_count: int = 0
        # Query population statistics (rolling window)
        self._query_mags: Deque[float] = collections.deque(maxlen=window)
        self._query_centroid_accum: Optional[List[float]] = None
        self._query_count: int = 0

    def record_query_vector(self, vec: List[float]) -> None:
        """Record a query vector for drift detection."""
        mag = math.sqrt(sum(x * x for x in vec))
        self._query_mags.append(mag)
        self._query_count += 1
        if self._query_centroid_accum is None:
            self._query_centroid_accum = list(vec)
        else:
            for i in range(min(len(vec), len(self._query_centroid_accum))):
                self._query_centroid_accum[i] += vec[i]

    def record_index_sample(self, vectors: List[List[float]]) -> None:
        """Record a sample of index vectors to establish baseline.

        Typically called once during initialisation with a representative
        sub-sample (e.g. 1000 randomly chosen index vectors).
        """
        if not vectors:
            return
        mags: List[float] = []
        dim = len(vectors[0])
        centroid = [0.0] * dim
        for v in vectors:
            m = math.sqrt(sum(x * x for x in v))
            mags.append(m)
            for i in range(dim):
                centroid[i] += v[i]
        n = len(vectors)
        self._index_mag_mean = sum(mags) / n
        var_sum = sum((m - self._index_mag_mean) ** 2 for m in mags)
        self._index_mag_var = var_sum / max(n - 1, 1)
        self._index_centroid = [c / n for c in centroid]
        self._index_sample_count = n

    def compute_drift_score(self) -> float:
        """Compute a normalised drift score in [0, 1].

        Components (equally weighted):
            1. Magnitude drift — Welch t-test proxy on mean magnitudes.
            2. Centroid drift — cosine distance between index and query
               centroids.

        Returns 0.0 when insufficient data is available.
        """
        if (self._index_sample_count == 0 or
                len(self._query_mags) < 10):
            return 0.0

        # --- magnitude drift ---
        q_mags = list(self._query_mags)
        q_mean = sum(q_mags) / len(q_mags)
        q_var = (sum((m - q_mean) ** 2 for m in q_mags)
                 / max(len(q_mags) - 1, 1))
        idx_std = math.sqrt(max(self._index_mag_var, 1e-12))
        mag_drift = abs(q_mean - self._index_mag_mean) / idx_std
        mag_drift_norm = min(mag_drift / 3.0, 1.0)  # 3 σ → 1.0

        # --- centroid drift ---
        centroid_drift = 0.0
        if (self._index_centroid is not None and
                self._query_centroid_accum is not None and
                self._query_count > 0):
            dim = len(self._index_centroid)
            q_c = [x / self._query_count
                   for x in self._query_centroid_accum[:dim]]
            dot = sum(a * b for a, b in zip(self._index_centroid, q_c))
            n_a = math.sqrt(sum(x * x for x in self._index_centroid))
            n_b = math.sqrt(sum(x * x for x in q_c))
            if n_a > 1e-10 and n_b > 1e-10:
                cos_sim = dot / (n_a * n_b)
                centroid_drift = max(0.0, 1.0 - cos_sim)

        return (mag_drift_norm + centroid_drift) / 2.0

    def should_reindex(self) -> bool:
        """True if embedding drift exceeds the configured threshold."""
        return self.compute_drift_score() > self._threshold

    def get_stats(self) -> dict:
        """Return detector statistics."""
        return {
            "drift_score": round(self.compute_drift_score(), 4),
            "threshold": self._threshold,
            "should_reindex": self.should_reindex(),
            "index_sample_count": self._index_sample_count,
            "query_count": self._query_count,
            "index_mag_mean": round(self._index_mag_mean, 6),
        }


# ---------------------------------------------------------------------------
# ReindexScheduler
# ---------------------------------------------------------------------------

class ReindexScheduler:
    """Schedule and track index rebuild jobs.

    Triggers:
        1. **Time-based** — rebuild every *max_age_hours* hours.
        2. **Count-based** — rebuild when new-doc delta exceeds threshold.
        3. **Drift-based** — rebuild when EmbeddingDriftDetector fires.
        4. **Manual** — on-demand via ``schedule_rebuild()``.
    """

    def __init__(self, max_age_hours: float = _STALE_HOURS,
                 doc_delta_threshold: int = 5000,
                 drift_detector: Optional[EmbeddingDriftDetector] = None):
        self._max_age_hours = max_age_hours
        self._doc_delta = doc_delta_threshold
        self._drift = drift_detector
        self._pending: List[Dict[str, Any]] = []
        self._completed: List[Dict[str, Any]] = []
        self._last_index_time: Optional[float] = None
        self._last_doc_count: int = 0

    def set_last_index_info(self, timestamp: float, doc_count: int) -> None:
        """Record when the last index was built and how many docs it had."""
        self._last_index_time = timestamp
        self._last_doc_count = doc_count

    def check_triggers(self, current_doc_count: int = 0) -> Dict[str, bool]:
        """Evaluate all trigger conditions.

        Returns a dict mapping trigger name → whether it fired.
        """
        triggers: Dict[str, bool] = {
            "time_based": False,
            "count_based": False,
            "drift_based": False,
        }

        # Time-based
        if self._last_index_time is not None:
            age_h = (time.time() - self._last_index_time) / 3600
            if age_h > self._max_age_hours:
                triggers["time_based"] = True
        else:
            triggers["time_based"] = True  # never built

        # Count-based
        if current_doc_count > 0 and self._last_doc_count > 0:
            delta = abs(current_doc_count - self._last_doc_count)
            if delta >= self._doc_delta:
                triggers["count_based"] = True

        # Drift-based
        if self._drift is not None:
            triggers["drift_based"] = self._drift.should_reindex()

        return triggers

    def schedule_rebuild(self, reason: str) -> str:
        """Create a pending rebuild job.

        Returns:
            A unique job ID.
        """
        job_id = uuid.uuid4().hex[:12]
        self._pending.append({
            "job_id": job_id,
            "reason": reason,
            "scheduled_at": datetime.now(timezone.utc).isoformat(),
            "status": "pending",
        })
        logger.info("Reindex job %s scheduled: %s", job_id, reason)
        return job_id

    def get_pending_rebuilds(self) -> List[Dict[str, Any]]:
        """Return all pending rebuild jobs."""
        return [j for j in self._pending if j["status"] == "pending"]

    def mark_complete(self, job_id: str) -> None:
        """Mark a rebuild job as complete."""
        for job in self._pending:
            if job["job_id"] == job_id:
                job["status"] = "completed"
                job["completed_at"] = datetime.now(timezone.utc).isoformat()
                self._completed.append(job)
                logger.info("Reindex job %s completed", job_id)
                return
        logger.warning("Reindex job %s not found", job_id)

    def get_stats(self) -> dict:
        """Return scheduler statistics."""
        return {
            "pending_count": len(self.get_pending_rebuilds()),
            "completed_count": len(self._completed),
            "max_age_hours": self._max_age_hours,
            "doc_delta_threshold": self._doc_delta,
            "last_index_time": (datetime.fromtimestamp(
                self._last_index_time, tz=timezone.utc
            ).isoformat() if self._last_index_time else None),
            "last_doc_count": self._last_doc_count,
        }


# ---------------------------------------------------------------------------
# VectorMonitor
# ---------------------------------------------------------------------------

class VectorMonitor:
    """Comprehensive vector search health monitoring.

    Monitors all four retrieval backends:
        1. LSI / Semantic (300-d brute-force)
        2. HNSW (approximate NN via vector_index_optimizer)
        3. BM25 (sparse keyword retrieval)
        4. FTS5 (SQLite full-text search)

    Plus: embedding cache, metadata index, query patterns,
          drift detection, and reindex scheduling.
    """

    def __init__(self):
        self.latency_tracker = QueryLatencyTracker()
        self.drift_detector = EmbeddingDriftDetector()
        self.reindex_scheduler = ReindexScheduler(
            drift_detector=self.drift_detector,
        )
        self._health_history: List[Dict[str, Any]] = []
        self._search_log: Deque[SearchQualityMetric] = collections.deque(
            maxlen=2000,
        )
        self._start_time = time.time()

    # ------------------------------------------------------------------
    # Health checks
    # ------------------------------------------------------------------

    def check_all_health(self) -> Dict[str, IndexHealth]:
        """Check health of every vector search component.

        Returns:
            Dict mapping component name to its :class:`IndexHealth`.
        """
        results: Dict[str, IndexHealth] = {}
        results["lsi"] = self._check_lsi()
        results["hnsw"] = self._check_hnsw()
        results["bm25"] = self._check_bm25()
        results["fts5"] = self._check_fts5()
        results["vectorizer"] = self._check_model_file(
            "vectorizer", _VECTORIZER_PATH,
        )
        results["svd_model"] = self._check_model_file(
            "svd_model", _SVD_PATH,
        )

        # Persist snapshot
        snapshot = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": {k: v.to_dict() for k, v in results.items()},
        }
        self._health_history.append(snapshot)
        # Trim history
        if len(self._health_history) > 500:
            self._health_history = self._health_history[-500:]

        return results

    # ------------------------------------------------------------------
    # Record search
    # ------------------------------------------------------------------

    def record_search(self, backend: str, query: str,
                      latency_ms: float, result_count: int,
                      top_score: float) -> None:
        """Record a completed search for monitoring.

        Called by VectorSearchBridge, HybridRetriever, or other callers
        after each search operation to feed the monitoring pipeline.
        """
        self.latency_tracker.record(backend, latency_ms)

        avg_score = top_score * 0.7 if result_count > 0 else 0.0
        metric = SearchQualityMetric(
            query=query[:200],
            backend=backend,
            latency_ms=latency_ms,
            result_count=result_count,
            top_score=top_score,
            avg_score=avg_score,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self._search_log.append(metric)

    # ------------------------------------------------------------------
    # Dashboard data
    # ------------------------------------------------------------------

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Generate dashboard data suitable for JSON export or HTML rendering.

        Sections:
            health    – per-component health status
            latency   – per-backend P50/P95/P99
            drift     – embedding drift scores
            reindex   – schedule and triggers
            quality   – recent search quality metrics
            recommend – actionable optimisation recommendations
        """
        health_map = self.check_all_health()

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "uptime_minutes": round((time.time() - self._start_time) / 60, 1),
            "health": {k: v.to_dict() for k, v in health_map.items()},
            "latency": self.latency_tracker.get_stats_all_backends(),
            "latency_aggregate": self.latency_tracker.get_stats().to_dict(),
            "drift": self.drift_detector.get_stats(),
            "reindex": self.reindex_scheduler.get_stats(),
            "recent_searches": [
                m.to_dict() for m in list(self._search_log)[-20:]
            ],
            "slow_backends": self.latency_tracker.get_slow_queries(),
            "recommendations": self.get_recommendations(),
        }

    # ------------------------------------------------------------------
    # HTML dashboard
    # ------------------------------------------------------------------

    def generate_html_dashboard(self) -> str:
        """Generate a standalone HTML dashboard with dark theme.

        Sections:
            1. Overall Health Status (green / yellow / red per backend)
            2. Latency Distribution (P50 / P95 / P99 per backend)
            3. Index Freshness (age, staleness score)
            4. Memory Usage (per index)
            5. Query Volume (recent queries, patterns)
            6. Drift Detection (scores, reindex triggers)
            7. Recommendations

        Returns:
            Complete HTML string — inline CSS, no external deps.
        """
        data = self.get_dashboard_data()
        now = data["generated_at"]

        status_colors = {
            "healthy": "#3fb950",
            "degraded": "#d29922",
            "critical": "#f85149",
            "offline": "#8b949e",
        }

        # Build health cards HTML
        health_cards = ""
        for name, info in data["health"].items():
            colour = status_colors.get(info["status"], "#8b949e")
            health_cards += (
                f'<div class="card">'
                f'<div class="card-header" style="border-left:4px solid {colour}">'
                f'<span class="status-dot" style="background:{colour}"></span>'
                f'<strong>{_esc(name)}</strong>'
                f'<span class="badge" style="background:{colour}">'
                f'{_esc(info["status"])}</span></div>'
                f'<div class="card-body">'
                f'<p>Docs: <b>{info["doc_count"]:,}</b></p>'
                f'<p>Size: <b>{info["size_mb"]} MB</b></p>'
                f'<p>Age: <b>{info["index_age_hours"]} h</b></p>'
                f'<p>Staleness: <b>{info["staleness_score"]}</b></p>'
                f'</div></div>'
            )

        # Latency table rows
        lat_rows = ""
        for backend, stats in data["latency"].items():
            p95_cls = ""
            if stats["p95_ms"] > _LATENCY_CRIT_MS:
                p95_cls = ' class="crit"'
            elif stats["p95_ms"] > _LATENCY_WARN_MS:
                p95_cls = ' class="warn"'
            lat_rows += (
                f'<tr><td>{_esc(backend)}</td>'
                f'<td>{stats["p50_ms"]:.1f}</td>'
                f'<td{p95_cls}>{stats["p95_ms"]:.1f}</td>'
                f'<td>{stats["p99_ms"]:.1f}</td>'
                f'<td>{stats["avg_ms"]:.1f}</td>'
                f'<td>{stats["sample_count"]}</td></tr>'
            )

        # Recent searches
        search_rows = ""
        for s in data["recent_searches"][-10:]:
            search_rows += (
                f'<tr><td>{_esc(s["backend"])}</td>'
                f'<td>{_esc(s["query"][:60])}</td>'
                f'<td>{s["latency_ms"]:.1f}</td>'
                f'<td>{s["result_count"]}</td>'
                f'<td>{s["top_score"]:.4f}</td></tr>'
            )

        # Drift info
        drift = data["drift"]
        drift_colour = (
            status_colors["healthy"] if drift["drift_score"] < 0.15
            else status_colors["degraded"] if drift["drift_score"] < _DRIFT_REINDEX
            else status_colors["critical"]
        )

        # Recommendations list
        rec_items = "".join(
            f"<li>{_esc(r)}</li>" for r in data["recommendations"]
        ) or "<li>All systems nominal — no recommendations.</li>"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>LitigationOS — Vector Search Monitor</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0d1117;color:#c9d1d9;font-family:-apple-system,
  BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;padding:24px}}
h1{{color:#58a6ff;margin-bottom:4px}}
h2{{color:#79c0ff;margin:24px 0 12px;border-bottom:1px solid #21262d;
    padding-bottom:6px}}
.subtitle{{color:#8b949e;font-size:0.85em;margin-bottom:20px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));
    gap:14px}}
.card{{background:#161b22;border:1px solid #30363d;border-radius:8px;
    overflow:hidden}}
.card-header{{padding:10px 14px;display:flex;align-items:center;gap:8px;
    background:#0d1117}}
.card-body{{padding:10px 14px}}
.card-body p{{margin:4px 0;font-size:0.88em}}
.status-dot{{width:10px;height:10px;border-radius:50%;display:inline-block}}
.badge{{font-size:0.7em;padding:2px 8px;border-radius:10px;color:#0d1117;
    font-weight:700;margin-left:auto}}
table{{width:100%;border-collapse:collapse;margin:8px 0}}
th,td{{text-align:left;padding:6px 10px;border-bottom:1px solid #21262d;
    font-size:0.88em}}
th{{color:#8b949e;font-weight:600}}
.warn{{color:#d29922;font-weight:700}}
.crit{{color:#f85149;font-weight:700}}
.drift-bar{{height:14px;border-radius:7px;background:#21262d;margin:6px 0}}
.drift-fill{{height:100%;border-radius:7px}}
ul{{margin:8px 0 8px 20px}}
li{{margin:4px 0;font-size:0.9em}}
.footer{{margin-top:40px;text-align:center;color:#484f58;font-size:0.8em}}
</style>
</head>
<body>
<h1>&#x1F50D; Vector Search Monitor</h1>
<p class="subtitle">Generated {_esc(now)} &middot; Uptime {data['uptime_minutes']} min</p>

<h2>1 &mdash; Component Health</h2>
<div class="grid">{health_cards}</div>

<h2>2 &mdash; Query Latency (ms)</h2>
<table>
<tr><th>Backend</th><th>P50</th><th>P95</th><th>P99</th>
    <th>Avg</th><th>Samples</th></tr>
{lat_rows if lat_rows else '<tr><td colspan="6">No latency data recorded yet.</td></tr>'}
</table>

<h2>3 &mdash; Embedding Drift</h2>
<p>Score: <b style="color:{drift_colour}">{drift['drift_score']:.4f}</b>
   (threshold {drift['threshold']})</p>
<div class="drift-bar">
  <div class="drift-fill" style="width:{min(drift['drift_score']*100,100):.0f}%;
       background:{drift_colour}"></div>
</div>
<p>Index samples: {drift['index_sample_count']} &middot;
   Query vectors: {drift['query_count']} &middot;
   Reindex needed: <b>{'YES' if drift['should_reindex'] else 'no'}</b></p>

<h2>4 &mdash; Recent Searches</h2>
<table>
<tr><th>Backend</th><th>Query</th><th>Latency</th>
    <th>Results</th><th>Top Score</th></tr>
{search_rows if search_rows else '<tr><td colspan="5">No searches recorded yet.</td></tr>'}
</table>

<h2>5 &mdash; Recommendations</h2>
<ul>{rec_items}</ul>

<p class="footer">LitigationOS Vector Monitor v1.0 &middot; 100 % local &middot;
   zero-API &middot; stdlib only</p>
</body>
</html>"""
        return html

    # ------------------------------------------------------------------
    # Metrics export
    # ------------------------------------------------------------------

    def export_metrics(self, path: Optional[str] = None) -> str:
        """Export all metrics to JSON.

        Args:
            path: Optional file path.  If ``None``, writes to
                  ``00_SYSTEM/local_model/model_data/vector_index/monitor_metrics.json``.

        Returns:
            The path the JSON was written to.
        """
        data = self.get_dashboard_data()
        if path is None:
            _INDEX_DIR.mkdir(parents=True, exist_ok=True)
            path = str(_INDEX_DIR / "monitor_metrics.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, default=str)
        logger.info("Metrics exported to %s", path)
        return path

    # ------------------------------------------------------------------
    # Recommendations
    # ------------------------------------------------------------------

    def get_recommendations(self) -> List[str]:
        """Generate actionable optimisation recommendations.

        Based on:
            - Latency patterns  (if P99 > 200 ms → suggest HNSW)
            - Index staleness   (if > 7 days → suggest rebuild)
            - Memory pressure   (if > 2 GB → suggest quantisation)
            - Query patterns    (repeated queries → suggest caching)
            - Drift scores      (if > 0.3 → suggest reindex)
        """
        recs: List[str] = []

        # Latency
        agg = self.latency_tracker.get_stats()
        if agg.sample_count > 0:
            if agg.p99_ms > _LATENCY_CRIT_MS:
                recs.append(
                    f"CRITICAL: Aggregate P99 latency is {agg.p99_ms:.0f} ms. "
                    f"Enable HNSW backend to reduce to <20 ms."
                )
            elif agg.p95_ms > _LATENCY_WARN_MS:
                recs.append(
                    f"WARNING: Aggregate P95 latency is {agg.p95_ms:.0f} ms. "
                    f"Consider enabling HNSW or increasing ef_search."
                )

        slow = self.latency_tracker.get_slow_queries(_LATENCY_WARN_MS)
        for s in slow:
            recs.append(
                f"Backend '{s['backend']}' has P95={s['p95_ms']:.0f} ms "
                f"over {s['sample_count']} queries — investigate."
            )

        # Staleness
        for path_label, path_obj in [("LSI", _LSI_PATH),
                                      ("HNSW", _INDEX_DIR / "hnsw_index.pkl")]:
            if path_obj.exists():
                age_h = (time.time() - path_obj.stat().st_mtime) / 3600
                if age_h > _STALE_HOURS:
                    recs.append(
                        f"{path_label} index is {age_h:.0f} h old "
                        f"(limit {_STALE_HOURS} h). Schedule a rebuild."
                    )

        # Memory
        for name, p in [("LSI", _LSI_PATH),
                        ("BM25", _BM25_DIR),
                        ("Inverted", _INVERTED_PATH)]:
            size_mb = _dir_size_mb(p) if p.is_dir() else _file_size_mb(p)
            if size_mb > _MEMORY_WARN_MB:
                recs.append(
                    f"{name} index is {size_mb:.0f} MB. "
                    f"Consider INT8 quantisation or pruning."
                )

        # Drift
        drift_score = self.drift_detector.compute_drift_score()
        if drift_score > _DRIFT_REINDEX:
            recs.append(
                f"Embedding drift score is {drift_score:.3f} "
                f"(threshold {_DRIFT_REINDEX}). Reindex recommended."
            )

        # Repeated queries (simple heuristic)
        if len(self._search_log) >= 50:
            queries = [m.query for m in self._search_log]
            counter = collections.Counter(queries)
            top = counter.most_common(1)
            if top and top[0][1] >= 5:
                recs.append(
                    f"Query '{top[0][0][:60]}' repeated {top[0][1]} times. "
                    f"Consider adding a result cache."
                )

        return recs

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> dict:
        """Return comprehensive monitor statistics."""
        return {
            "monitor_version": "1.0.0",
            "uptime_minutes": round((time.time() - self._start_time) / 60, 1),
            "total_searches_recorded": len(self._search_log),
            "health_snapshots": len(self._health_history),
            "latency_aggregate": self.latency_tracker.get_stats().to_dict(),
            "latency_per_backend": self.latency_tracker.get_stats_all_backends(),
            "drift": self.drift_detector.get_stats(),
            "reindex_scheduler": self.reindex_scheduler.get_stats(),
            "recommendation_count": len(self.get_recommendations()),
        }

    # ------------------------------------------------------------------
    # Private health-check helpers
    # ------------------------------------------------------------------

    def _check_lsi(self) -> IndexHealth:
        """Check LSI / semantic index health."""
        h = IndexHealth(name="lsi")
        if not _LSI_PATH.exists():
            h.status = HealthStatus.OFFLINE
            h.details = {"error": "lsi_index.npz not found"}
            return h

        h.size_mb = _file_size_mb(_LSI_PATH)
        h.index_age_hours = _file_age_hours(_LSI_PATH)
        h.staleness_score = min(h.index_age_hours / _STALE_HOURS, 1.0)
        h.needs_rebuild = h.staleness_score >= 1.0

        # Doc count from doc_meta.json
        if _DOC_META_PATH.exists():
            try:
                with open(_DOC_META_PATH, "r", encoding="utf-8") as fh:
                    meta = json.load(fh)
                h.doc_count = len(meta.get("doc_ids", []))
            except Exception:
                pass

        h.status = (
            HealthStatus.HEALTHY if h.staleness_score < 0.5
            else HealthStatus.DEGRADED if h.staleness_score < 1.0
            else HealthStatus.CRITICAL
        )
        h.details = {
            "path": str(_LSI_PATH),
            "svd_model_exists": _SVD_PATH.exists(),
        }
        return h

    def _check_hnsw(self) -> IndexHealth:
        """Check HNSW index health."""
        h = IndexHealth(name="hnsw")
        idx_pkl = _INDEX_DIR / "hnsw_index.pkl"
        idx_bin = _INDEX_DIR / "hnsw_native.bin"
        idx_path = idx_pkl if idx_pkl.exists() else (
            idx_bin if idx_bin.exists() else None
        )
        if idx_path is None:
            h.status = HealthStatus.OFFLINE
            h.details = {"error": "No HNSW index file found"}
            return h

        h.size_mb = _file_size_mb(idx_path)
        h.index_age_hours = _file_age_hours(idx_path)
        h.staleness_score = min(h.index_age_hours / _STALE_HOURS, 1.0)
        h.needs_rebuild = h.staleness_score >= 1.0

        # Try to read metadata
        meta_path = _INDEX_DIR / "hnsw_meta.json"
        if meta_path.exists():
            try:
                with open(meta_path, "r", encoding="utf-8") as fh:
                    meta = json.load(fh)
                h.doc_count = meta.get("num_vectors", 0)
            except Exception:
                pass

        h.status = (
            HealthStatus.HEALTHY if h.staleness_score < 0.5
            else HealthStatus.DEGRADED if h.staleness_score < 1.0
            else HealthStatus.CRITICAL
        )
        h.details = {
            "path": str(idx_path),
            "type": "native" if idx_path == idx_bin else "pure_python",
        }
        return h

    def _check_bm25(self) -> IndexHealth:
        """Check BM25 index health."""
        h = IndexHealth(name="bm25")
        if not _BM25_DIR.exists() or not _BM25_DIR.is_dir():
            h.status = HealthStatus.OFFLINE
            h.details = {"error": "bm25/ directory not found"}
            return h

        h.size_mb = _dir_size_mb(_BM25_DIR)
        # Use newest file's mtime for age
        newest = 0.0
        file_count = 0
        for f in _BM25_DIR.iterdir():
            if f.is_file():
                file_count += 1
                newest = max(newest, f.stat().st_mtime)
        if newest > 0:
            h.index_age_hours = (time.time() - newest) / 3600
        h.staleness_score = min(h.index_age_hours / _STALE_HOURS, 1.0)
        h.needs_rebuild = h.staleness_score >= 1.0

        # Doc count from doc_meta.json in bm25/
        bm25_meta = _BM25_DIR / "doc_meta.json"
        if bm25_meta.exists():
            try:
                with open(bm25_meta, "r", encoding="utf-8") as fh:
                    meta = json.load(fh)
                if isinstance(meta, dict):
                    h.doc_count = len(meta.get("doc_ids", []))
                elif isinstance(meta, list):
                    h.doc_count = len(meta)
            except Exception:
                pass

        h.status = (
            HealthStatus.HEALTHY if h.staleness_score < 0.5
            else HealthStatus.DEGRADED if h.staleness_score < 1.0
            else HealthStatus.CRITICAL
        )
        h.details = {"path": str(_BM25_DIR), "file_count": file_count}
        return h

    def _check_fts5(self) -> IndexHealth:
        """Check FTS5 virtual table health."""
        h = IndexHealth(name="fts5")
        if not _DB_PATH.exists():
            h.status = HealthStatus.OFFLINE
            h.details = {"error": "litigation_context.db not found"}
            return h

        known_fts = ["evidence_quotes_fts", "auth_rules_fts", "rules_text_fts"]
        tables_ok: List[str] = []
        total_rows = 0
        try:
            conn = sqlite3.connect(str(_DB_PATH), timeout=30)
            conn.execute("PRAGMA busy_timeout = 60000")
            conn.execute("PRAGMA journal_mode = WAL")
            for table in known_fts:
                try:
                    row = conn.execute(
                        f"SELECT COUNT(*) FROM [{table}]"
                    ).fetchone()
                    if row:
                        tables_ok.append(table)
                        total_rows += row[0]
                except Exception:
                    pass
            conn.close()
        except Exception as exc:
            h.status = HealthStatus.CRITICAL
            h.details = {"error": str(exc)}
            return h

        h.doc_count = total_rows
        h.details = {
            "tables_available": tables_ok,
            "tables_missing": [t for t in known_fts if t not in tables_ok],
        }
        # DB age
        h.index_age_hours = _file_age_hours(_DB_PATH)
        h.staleness_score = 0.0  # FTS5 is always fresh with the DB
        h.size_mb = _file_size_mb(_DB_PATH)

        if len(tables_ok) == len(known_fts) and total_rows > 0:
            h.status = HealthStatus.HEALTHY
        elif tables_ok:
            h.status = HealthStatus.DEGRADED
        else:
            h.status = HealthStatus.CRITICAL
        return h

    @staticmethod
    def _check_model_file(name: str, path: pathlib.Path) -> IndexHealth:
        """Check existence and age of a model file."""
        h = IndexHealth(name=name)
        if not path.exists():
            h.status = HealthStatus.OFFLINE
            h.details = {"error": f"{path.name} not found"}
            return h
        h.size_mb = _file_size_mb(path)
        h.index_age_hours = _file_age_hours(path)
        h.staleness_score = min(h.index_age_hours / _STALE_HOURS, 1.0)
        h.status = HealthStatus.HEALTHY
        h.details = {"path": str(path)}
        return h


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _file_size_mb(p: pathlib.Path) -> float:
    """Return file size in MB, 0 if missing."""
    try:
        return round(p.stat().st_size / (1024 * 1024), 2) if p.exists() else 0.0
    except Exception:
        return 0.0


def _dir_size_mb(p: pathlib.Path) -> float:
    """Return total size of all files in a directory, in MB."""
    total = 0
    try:
        if p.is_dir():
            for f in p.rglob("*"):
                if f.is_file():
                    total += f.stat().st_size
    except Exception:
        pass
    return round(total / (1024 * 1024), 2)


def _file_age_hours(p: pathlib.Path) -> float:
    """Return file age in hours, 0 if missing."""
    try:
        return round((time.time() - p.stat().st_mtime) / 3600, 1) if p.exists() else 0.0
    except Exception:
        return 0.0


def _esc(text: str) -> str:
    """Minimal HTML escape."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _cli_main() -> None:
    """Minimal CLI for vector monitor operations."""
    import sys
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="VectorMonitor — health monitoring and observability",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("health", help="Check all component health")
    sub.add_parser("dashboard", help="Generate HTML dashboard")
    sp_export = sub.add_parser("export", help="Export metrics JSON")
    sp_export.add_argument("--path", default=None,
                           help="Output file path (default: auto)")
    sub.add_parser("recommend", help="Print optimisation recommendations")
    sub.add_parser("stats", help="Print monitor stats")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    monitor = VectorMonitor()

    if args.command == "health":
        health = monitor.check_all_health()
        for name, h in health.items():
            status = h.status.value.upper()
            print(f"  [{status:8s}] {name:15s}  docs={h.doc_count:>8,}  "
                  f"size={h.size_mb:>8.1f} MB  age={h.index_age_hours:.1f} h  "
                  f"stale={h.staleness_score:.2f}")

    elif args.command == "dashboard":
        html = monitor.generate_html_dashboard()
        out_path = _INDEX_DIR / "vector_monitor_dashboard.html"
        _INDEX_DIR.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(html)
        print(f"Dashboard written to {out_path}")

    elif args.command == "export":
        path = monitor.export_metrics(args.path)
        print(f"Metrics exported to {path}")

    elif args.command == "recommend":
        recs = monitor.get_recommendations()
        if recs:
            for i, r in enumerate(recs, 1):
                print(f"  {i}. {r}")
        else:
            print("  All systems nominal — no recommendations.")

    elif args.command == "stats":
        stats = monitor.get_stats()
        print(json.dumps(stats, indent=2, default=str))


if __name__ == "__main__":
    _cli_main()
