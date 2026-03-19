"""
Cross-Brain Query Optimizer — LitigationOS Legal AI
=====================================================
Plans, routes, and fuses queries across the LitigationOS multi-brain
architecture (6 SQLite brain databases) for optimal retrieval.

Features:
  - Query classification (legal_authority / factual_narrative / entity / claim / strategic)
  - Brain-aware routing (only search relevant brains and FTS tables)
  - Reciprocal Rank Fusion (RRF) across brain result sets
  - In-memory LRU cache with TTL expiry
  - Latency tracking with percentile reporting

Usage:
    from legal_ai.cross_brain_optimizer import CrossBrainOptimizer
    opt = CrossBrainOptimizer()
    result = opt.search("MCR 2.003 disqualification for bias", top_k=10)
    # → CrossBrainSearchResult with fused, ranked results from authority + interpretation brains
"""

from __future__ import annotations

import logging
import re
import sqlite3
import sys
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

logger = logging.getLogger("legal_ai.cross_brain_optimizer")

_HERE = Path(__file__).parent
_REPO = _HERE.parent.parent

# ── Lazy BrainManager import ────────────────────────────────────
# BrainManager is imported lazily in __init__ to avoid blocking module loads


# ── Data Models ──────────────────────────────────────────────────

@dataclass
class QueryPlan:
    """Plan describing how a query should be executed across brains."""
    original_query: str
    query_type: str             # legal_authority / factual_narrative / entity_lookup / claim_analysis / strategic / universal
    target_brains: List[str] = field(default_factory=list)
    target_tables: List[str] = field(default_factory=list)
    fts_queries: Dict[str, str] = field(default_factory=dict)
    estimated_cost_ms: float = 0.0
    plan_reason: str = ""


@dataclass
class CrossBrainResult:
    """A single result from a brain search."""
    text: str
    brain_name: str
    table_name: str
    record_id: Optional[str] = None
    score: float = 0.0
    method: str = "fts5"        # fts5 / like / direct
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CrossBrainSearchResult:
    """Aggregated search results across multiple brains."""
    results: List[CrossBrainResult] = field(default_factory=list)
    total_found: int = 0
    brains_searched: List[str] = field(default_factory=list)
    tables_searched: int = 0
    query_plan: Optional[QueryPlan] = None
    search_time_ms: float = 0.0
    cache_hit: bool = False
    warnings: List[str] = field(default_factory=list)


@dataclass
class QueryLatencyReport:
    """Timing statistics for query execution."""
    total_queries: int = 0
    avg_latency_ms: float = 0.0
    p50_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    slowest_brain: str = ""
    slowest_table: str = ""
    cache_hit_rate: float = 0.0
    per_brain_avg_ms: Dict[str, float] = field(default_factory=dict)


# ── Constants ────────────────────────────────────────────────────

QUERY_BRAIN_MAP: Dict[str, List[str]] = {
    "legal_authority": ["authority_brain", "interpretation_brain"],
    "factual_narrative": ["narrative_brain", "entity_brain"],
    "entity_lookup": ["entity_brain", "narrative_brain"],
    "claim_analysis": ["claims_brain", "authority_brain", "interpretation_brain"],
    "strategic": ["interpretation_brain", "claims_brain"],
    "universal": [
        "authority_brain", "narrative_brain", "entity_brain",
        "claims_brain", "interpretation_brain", "cross_brain_index",
    ],
}

QUERY_CLASSIFIERS: Dict[str, "re.Pattern[str]"] = {
    "legal_authority": re.compile(
        r"MCR|MCL|MRE|USC|statute|rule|law|precedent|case\s+law", re.I
    ),
    "factual_narrative": re.compile(
        r"when|timeline|order|hearing|event|what\s+happened", re.I
    ),
    "entity_lookup": re.compile(
        r"who|judge|party|witness|attorney|defendant|plaintiff", re.I
    ),
    "claim_analysis": re.compile(
        r"claim|cause|element|damages|breach|violation", re.I
    ),
    "strategic": re.compile(
        r"strategy|risk|strength|weakness|argument|brief", re.I
    ),
}

BRAIN_FTS_TABLES: Dict[str, List[str]] = {
    "authority_brain": [
        "court_rules_fts", "statutes_fts", "case_law_fts",
        "evidence_rules_fts", "benchbook_fts",
    ],
    "narrative_brain": [
        "timeline_fts", "extractions_fts", "orders_fts",
        "police_fts", "testimony_fts", "communications_fts",
    ],
    "entity_brain": [],
    "claims_brain": [],
    "interpretation_brain": [
        "arguments_fts", "impeachment_fts", "drafts_fts", "applications_fts",
    ],
    "cross_brain_index": ["universal_search"],
}

# Rough per-table latency estimates (ms) for query planning
_TABLE_COST_MS: Dict[str, float] = {
    "court_rules_fts": 5.0, "statutes_fts": 8.0, "case_law_fts": 12.0,
    "evidence_rules_fts": 4.0, "benchbook_fts": 6.0,
    "timeline_fts": 10.0, "extractions_fts": 15.0, "orders_fts": 8.0,
    "police_fts": 7.0, "testimony_fts": 12.0, "communications_fts": 10.0,
    "arguments_fts": 6.0, "impeachment_fts": 5.0, "drafts_fts": 8.0,
    "applications_fts": 5.0, "universal_search": 20.0,
}


# ── Cache Entry ──────────────────────────────────────────────────

@dataclass
class _CacheEntry:
    """Internal cache entry with timestamp for TTL eviction."""
    result: CrossBrainSearchResult
    timestamp: float


# ── Main Class ───────────────────────────────────────────────────

class CrossBrainOptimizer:
    """
    Plans, routes, and fuses queries across the LitigationOS brain fleet.

    Works with or without a live BrainManager — gracefully degrades
    to returning empty result sets when brains are unavailable.
    """

    def __init__(
        self,
        brain_manager: Optional[Any] = None,
        cache_size: int = 256,
        cache_ttl_seconds: int = 300,
    ) -> None:
        """
        Args:
            brain_manager: Optional BrainManager instance.  If *None* and
                           BrainManager is importable, one is created automatically.
            cache_size:    Maximum entries in the in-memory LRU cache.
            cache_ttl_seconds: Time-to-live for cache entries (seconds).
        """
        self._bm = brain_manager
        if self._bm is None:
            try:
                sys.path.insert(0, str(Path(__file__).parent.parent))
                from brains.brain_manager import BrainManager  # type: ignore
                self._bm = BrainManager()
            except Exception as exc:
                logger.debug("Could not initialise BrainManager: %s", exc)

        self._cache_size = max(cache_size, 1)
        self._cache_ttl = cache_ttl_seconds
        self._cache: OrderedDict[Tuple[str, FrozenSet[str]], _CacheEntry] = OrderedDict()

        # Latency tracking
        self._latencies: List[float] = []
        self._brain_latencies: Dict[str, List[float]] = {}
        self._table_latencies: Dict[str, List[float]] = {}
        self._total_queries: int = 0
        self._cache_hits: int = 0

    # ── Query Planning ───────────────────────────────────────────

    def plan_query(
        self, query: str, hint_brains: Optional[List[str]] = None
    ) -> QueryPlan:
        """
        Classify *query* and produce a ``QueryPlan`` selecting brains, FTS tables,
        and estimated cost.

        Args:
            query:       Natural-language or citation query.
            hint_brains: If given, restricts the plan to these brains only.

        Returns:
            QueryPlan describing the optimal execution strategy.
        """
        query_type = self._classify_query(query)
        target_brains = list(hint_brains) if hint_brains else list(QUERY_BRAIN_MAP.get(query_type, QUERY_BRAIN_MAP["universal"]))

        target_tables: List[str] = []
        fts_queries: Dict[str, str] = {}
        estimated_cost_ms: float = 0.0

        fts_term = self._build_fts_term(query)

        for brain in target_brains:
            tables = BRAIN_FTS_TABLES.get(brain, [])
            for table in tables:
                target_tables.append(f"{brain}.{table}")
                fts_queries[f"{brain}.{table}"] = fts_term
                estimated_cost_ms += _TABLE_COST_MS.get(table, 10.0)

        reason = (
            f"Classified as '{query_type}' → targeting {len(target_brains)} brain(s), "
            f"{len(target_tables)} FTS table(s)"
        )

        return QueryPlan(
            original_query=query,
            query_type=query_type,
            target_brains=target_brains,
            target_tables=target_tables,
            fts_queries=fts_queries,
            estimated_cost_ms=estimated_cost_ms,
            plan_reason=reason,
        )

    # ── Search (multi-brain) ─────────────────────────────────────

    def search(
        self,
        query: str,
        top_k: int = 20,
        brains: Optional[List[str]] = None,
    ) -> CrossBrainSearchResult:
        """
        Execute a planned multi-brain search with RRF fusion.

        Args:
            query:  Natural-language or citation query.
            top_k:  Maximum results to return after fusion.
            brains: Optional list of brain names to restrict the search.

        Returns:
            CrossBrainSearchResult with fused, ranked results.
        """
        t0 = time.perf_counter()
        self._total_queries += 1

        # ── Cache lookup ─────────────────────────────────────────
        cache_key = self._cache_key(query, brains)
        cached = self._cache_get(cache_key)
        if cached is not None:
            self._cache_hits += 1
            elapsed = (time.perf_counter() - t0) * 1000
            cached.search_time_ms = elapsed
            cached.cache_hit = True
            self._latencies.append(elapsed)
            return cached

        # ── Plan ─────────────────────────────────────────────────
        plan = self.plan_query(query, hint_brains=brains)
        warnings: List[str] = []

        if self._bm is None:
            warnings.append("BrainManager unavailable — returning empty results")
            return CrossBrainSearchResult(
                query_plan=plan,
                brains_searched=plan.target_brains,
                search_time_ms=(time.perf_counter() - t0) * 1000,
                warnings=warnings,
            )

        # ── Execute per-brain ────────────────────────────────────
        ranked_lists: Dict[str, List[CrossBrainResult]] = {}
        tables_searched = 0

        for brain_name in plan.target_brains:
            bt0 = time.perf_counter()
            try:
                brain_results = self.search_brain(brain_name, query, top_k=top_k)
                ranked_lists[brain_name] = brain_results
                tables_searched += len(BRAIN_FTS_TABLES.get(brain_name, []))
            except Exception as exc:
                warnings.append(f"Brain '{brain_name}' error: {exc}")
                logger.warning("Error searching brain '%s': %s", brain_name, exc)
            finally:
                brain_ms = (time.perf_counter() - bt0) * 1000
                self._brain_latencies.setdefault(brain_name, []).append(brain_ms)

        # ── RRF fusion ───────────────────────────────────────────
        fused = self._rrf_fuse(ranked_lists)[:top_k]

        elapsed_ms = (time.perf_counter() - t0) * 1000
        self._latencies.append(elapsed_ms)

        result = CrossBrainSearchResult(
            results=fused,
            total_found=len(fused),
            brains_searched=plan.target_brains,
            tables_searched=tables_searched,
            query_plan=plan,
            search_time_ms=elapsed_ms,
            cache_hit=False,
            warnings=warnings,
        )
        self._cache_put(cache_key, result)
        return result

    # ── Search (single brain) ────────────────────────────────────

    def search_brain(
        self, brain_name: str, query: str, top_k: int = 10
    ) -> List[CrossBrainResult]:
        """
        Execute FTS5 search on a single brain's tables.

        Args:
            brain_name: Name of the brain database (e.g. 'authority_brain').
            query:      Search query (will be converted to FTS5 syntax).
            top_k:      Maximum results per FTS table.

        Returns:
            List of ``CrossBrainResult`` ordered by relevance.
        """
        if self._bm is None:
            return []

        fts_term = self._build_fts_term(query)
        tables = BRAIN_FTS_TABLES.get(brain_name, [])
        results: List[CrossBrainResult] = []

        for table in tables:
            tt0 = time.perf_counter()
            try:
                rows = self._query_fts_table(brain_name, table, fts_term, top_k)
                for row in rows:
                    text = self._extract_text(row)
                    record_id = self._extract_id(row)
                    results.append(CrossBrainResult(
                        text=text,
                        brain_name=brain_name,
                        table_name=table,
                        record_id=record_id,
                        score=abs(float(row.get("rank", 0.0))) if isinstance(row, dict) else 0.0,
                        method="fts5",
                        metadata={k: v for k, v in (row.items() if isinstance(row, dict) else [])
                                  if k not in ("rank", "rowid")},
                    ))
            except Exception as exc:
                logger.debug("FTS query on %s.%s failed: %s", brain_name, table, exc)
            finally:
                table_ms = (time.perf_counter() - tt0) * 1000
                self._table_latencies.setdefault(table, []).append(table_ms)

        # Sort by descending FTS5 score (higher = better match)
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    # ── Cache Management ─────────────────────────────────────────

    def invalidate_cache(self, brain_name: Optional[str] = None) -> int:
        """
        Clear cached results.

        Args:
            brain_name: If given, only invalidate entries that searched this brain.
                        If *None*, flush the entire cache.

        Returns:
            Number of cache entries removed.
        """
        if brain_name is None:
            count = len(self._cache)
            self._cache.clear()
            return count

        to_remove = [
            key for key, entry in self._cache.items()
            if brain_name in entry.result.brains_searched
        ]
        for key in to_remove:
            del self._cache[key]
        return len(to_remove)

    # ── Latency Report ───────────────────────────────────────────

    def get_latency_report(self) -> QueryLatencyReport:
        """Return percentile latency statistics."""
        lats = sorted(self._latencies) if self._latencies else [0.0]
        n = len(lats)

        def _pctl(p: float) -> float:
            idx = int(p / 100.0 * max(n - 1, 0))
            return lats[min(idx, n - 1)]

        # Per-brain averages
        per_brain: Dict[str, float] = {}
        slowest_brain = ""
        slowest_brain_ms = 0.0
        for brain, times in self._brain_latencies.items():
            avg = sum(times) / len(times) if times else 0.0
            per_brain[brain] = round(avg, 2)
            if avg > slowest_brain_ms:
                slowest_brain_ms = avg
                slowest_brain = brain

        # Slowest table
        slowest_table = ""
        slowest_table_ms = 0.0
        for table, times in self._table_latencies.items():
            avg = sum(times) / len(times) if times else 0.0
            if avg > slowest_table_ms:
                slowest_table_ms = avg
                slowest_table = table

        hit_rate = (self._cache_hits / self._total_queries) if self._total_queries > 0 else 0.0

        return QueryLatencyReport(
            total_queries=self._total_queries,
            avg_latency_ms=round(sum(lats) / n, 2),
            p50_ms=round(_pctl(50), 2),
            p95_ms=round(_pctl(95), 2),
            p99_ms=round(_pctl(99), 2),
            slowest_brain=slowest_brain,
            slowest_table=slowest_table,
            cache_hit_rate=round(hit_rate, 4),
            per_brain_avg_ms=per_brain,
        )

    # ── Statistics ───────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Return engine status and capabilities."""
        return {
            "version": "1.0.0",
            "brain_manager_available": self._bm is not None,
            "brain_manager_class": type(self._bm).__name__ if self._bm else None,
            "known_brains": list(BRAIN_FTS_TABLES.keys()),
            "total_fts_tables": sum(len(v) for v in BRAIN_FTS_TABLES.values()),
            "query_types": list(QUERY_CLASSIFIERS.keys()) + ["universal"],
            "cache_size": self._cache_size,
            "cache_ttl_seconds": self._cache_ttl,
            "cache_entries": len(self._cache),
            "total_queries": self._total_queries,
            "cache_hits": self._cache_hits,
            "cache_hit_rate": round(
                (self._cache_hits / self._total_queries) if self._total_queries > 0 else 0.0, 4
            ),
        }

    # ── Private Helpers ──────────────────────────────────────────

    def _classify_query(self, query: str) -> str:
        """Classify a query into a type using regex classifiers."""
        best_type = "universal"
        best_score = 0
        for qtype, pattern in QUERY_CLASSIFIERS.items():
            matches = pattern.findall(query)
            if len(matches) > best_score:
                best_score = len(matches)
                best_type = qtype
        return best_type

    def _build_fts_term(self, query: str) -> str:
        """
        Convert a natural-language query into an FTS5-safe search term.

        Strips special FTS characters and joins tokens with OR for recall.
        """
        # Remove FTS5 operators and special chars
        cleaned = re.sub(r'["\'\(\)\*\-\+\^]', " ", query)
        tokens = [t.strip() for t in cleaned.split() if len(t.strip()) >= 2]
        if not tokens:
            return query.strip()
        if len(tokens) == 1:
            return tokens[0]
        return " OR ".join(tokens)

    def _query_fts_table(
        self, brain_name: str, table: str, fts_term: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Execute an FTS5 MATCH query against a brain's table."""
        sql = f"SELECT *, rank FROM {table} WHERE {table} MATCH ? ORDER BY rank LIMIT ?"
        rows = self._bm.query_brain(brain_name, sql, (fts_term, limit))  # type: ignore[union-attr]
        return rows if rows else []

    def _extract_text(self, row: Any) -> str:
        """Pull the best text field from a result row."""
        if isinstance(row, dict):
            for col in ("content", "text", "full_text", "body", "rule_text",
                        "summary", "description", "excerpt", "title"):
                val = row.get(col)
                if val and isinstance(val, str):
                    return val[:2000]
        return str(row)[:500]

    def _extract_id(self, row: Any) -> Optional[str]:
        """Pull the best identifier from a result row."""
        if isinstance(row, dict):
            for col in ("id", "rowid", "record_id", "rule_id",
                        "citation", "case_id", "statute_id"):
                val = row.get(col)
                if val is not None:
                    return str(val)
        return None

    def _rrf_fuse(
        self,
        ranked_lists: Dict[str, List[CrossBrainResult]],
        k: int = 60,
    ) -> List[CrossBrainResult]:
        """
        Reciprocal Rank Fusion across per-brain ranked lists.

        Args:
            ranked_lists: Mapping of brain_name → sorted results.
            k:            RRF smoothing constant (default 60).

        Returns:
            Fused list sorted by descending RRF score.
        """
        scores: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
        for brain_name, results in ranked_lists.items():
            for rank, result in enumerate(results):
                key = (
                    result.brain_name,
                    result.table_name,
                    result.record_id or result.text[:100],
                )
                if key not in scores:
                    scores[key] = {"result": result, "score": 0.0}
                scores[key]["score"] += 1.0 / (k + rank + 1)

        fused = sorted(scores.values(), key=lambda x: x["score"], reverse=True)
        for item in fused:
            item["result"].score = item["score"]
        return [item["result"] for item in fused]

    # ── Cache internals ──────────────────────────────────────────

    def _cache_key(
        self, query: str, brains: Optional[List[str]]
    ) -> Tuple[str, FrozenSet[str]]:
        """Build a deterministic cache key."""
        normalised = " ".join(query.lower().split())
        brain_set = frozenset(brains) if brains else frozenset()
        return (normalised, brain_set)

    def _cache_get(
        self, key: Tuple[str, FrozenSet[str]]
    ) -> Optional[CrossBrainSearchResult]:
        """Retrieve a cache entry if present and not expired."""
        entry = self._cache.get(key)
        if entry is None:
            return None
        if (time.time() - entry.timestamp) > self._cache_ttl:
            del self._cache[key]
            return None
        # Move to end (LRU)
        self._cache.move_to_end(key)
        return entry.result

    def _cache_put(
        self, key: Tuple[str, FrozenSet[str]], result: CrossBrainSearchResult
    ) -> None:
        """Insert a result into the LRU cache, evicting oldest if full."""
        if key in self._cache:
            self._cache.move_to_end(key)
            self._cache[key] = _CacheEntry(result=result, timestamp=time.time())
            return
        if len(self._cache) >= self._cache_size:
            self._cache.popitem(last=False)  # evict oldest
        self._cache[key] = _CacheEntry(result=result, timestamp=time.time())
