"""Three-stage hybrid search: FTS5/BM25 recall → vector similarity → cross-encoder rerank.

State-of-the-art retrieval pipeline, all local, zero API cost.

Architecture:
    Stage 1 — FTS5 keyword recall with BM25 ranking (fast, broad coverage)
    Stage 2 — LanceDB vector similarity via all-MiniLM-L6-v2 (semantic understanding)
    Stage 3 — Cross-encoder reranking via ms-marco-MiniLM-L6-v2 (precision)

v2.1 — Singleton caching for SemanticSearchEngine + reranker, ``fast`` mode,
        per-stage timing instrumentation.
"""
from __future__ import annotations

import logging
import re
import sqlite3
import time
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

DB_PATH = Path(__file__).resolve().parents[3] / "litigation_context.db"

CHILD_NAME_RE = re.compile(
    r"\b(?:Lincoln\s+(?:Dean\s+)?(?:Watson|Pigors|Watson[- ]Pigors))\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Singleton caches (loaded once per process)
# ---------------------------------------------------------------------------
_SEMANTIC_ENGINE = None
_LEGALBERT_ENGINE = None


def get_semantic_engine():
    """Return the process-wide SemanticSearchEngine (lazy-loaded, cached)."""
    global _SEMANTIC_ENGINE
    if _SEMANTIC_ENGINE is None:
        import sys

        semantic_dir = str(Path(__file__).resolve().parents[1] / "semantic")
        if semantic_dir not in sys.path:
            sys.path.insert(0, semantic_dir)
        from engine import SemanticSearchEngine

        _SEMANTIC_ENGINE = SemanticSearchEngine()
        log.info("SemanticSearchEngine singleton loaded")
    return _SEMANTIC_ENGINE


def _get_legalbert():
    """Return the process-wide Legal-BERT engine (lazy-loaded, cached)."""
    global _LEGALBERT_ENGINE
    if _LEGALBERT_ENGINE is None:
        import sys

        perception_dir = str(Path(__file__).resolve().parents[1] / "perception")
        if perception_dir not in sys.path:
            sys.path.insert(0, perception_dir)
        from engine import get_engine as _get_lb

        eng = _get_lb()
        if not eng.is_ready:
            eng._load_model()
        _LEGALBERT_ENGINE = eng
        log.info("Legal-BERT singleton loaded for hybrid pipeline")
    return _LEGALBERT_ENGINE


def warm_up():
    """Pre-load all heavy models.  Call once at startup for instant queries."""
    from .reranker import get_reranker

    get_reranker()
    try:
        get_semantic_engine()
    except Exception as e:
        log.warning("Semantic engine warm-up failed (non-fatal): %s", e)
    try:
        _get_legalbert()
    except Exception as e:
        log.warning("Legal-BERT warm-up failed (non-fatal): %s", e)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sanitize_fts5(query: str) -> str:
    """Remove FTS5-unsafe characters, keeping words, spaces, wildcards, and phrases."""
    return re.sub(r'[^\w\s*"]', " ", query).strip()


def _get_conn(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Open a WAL-mode SQLite connection with required PRAGMAs."""
    conn = sqlite3.connect(db_path or str(DB_PATH), timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# Stage 1 — FTS5 / BM25
# ---------------------------------------------------------------------------


def fts5_bm25_search(
    query: str,
    fts_table: str = "evidence_fts",
    text_col: str = "quote_text",
    limit: int = 100,
    db_path: Optional[str] = None,
) -> list[dict]:
    """Stage 1: Fast keyword recall via FTS5 with BM25 ranking.

    BM25 is a probabilistic relevance function built into SQLite FTS5.
    Lower bm25() values = better match (it returns negative scores).

    Falls back to parameterized LIKE on any FTS5 error (Rule 15).
    """
    safe_q = _sanitize_fts5(query)
    if not safe_q:
        return []

    conn = _get_conn(db_path)
    try:
        try:
            rows = conn.execute(
                f"SELECT *, bm25({fts_table}) AS bm25_score "
                f"FROM {fts_table} "
                f"WHERE {fts_table} MATCH ? "
                f"ORDER BY bm25({fts_table}) "
                f"LIMIT ?",
                (safe_q, limit),
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            log.warning("FTS5 MATCH failed (%s), falling back to LIKE", e)
            base_table = fts_table.replace("_fts", "")
            if base_table == "evidence":
                base_table = "evidence_quotes"
            elif base_table == "timeline":
                base_table = "timeline_events"
            elif base_table == "md_sections":
                base_table = "md_sections"

            conn2 = _get_conn(db_path)
            conn2.row_factory = sqlite3.Row
            try:
                like_q = f"%{safe_q}%"
                rows = conn2.execute(
                    f"SELECT * FROM {base_table} WHERE {text_col} LIKE ? LIMIT ?",
                    (like_q, limit),
                ).fetchall()
                return [dict(r) for r in rows]
            finally:
                conn2.close()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Stage 2 — Vector search (cached engine)
# ---------------------------------------------------------------------------


def _vector_search(
    query: str,
    table_name: str = "evidence_quotes",
    top_k: int = 100,
) -> list[dict]:
    """Stage 2: Semantic similarity via LanceDB sentence-transformer vectors.

    Uses the module-level singleton so the model is loaded only once.
    Returns dicts with keys: row_id, text, _distance.
    """
    try:
        engine = get_semantic_engine()
        results = engine.search(query, table_name, top_k=top_k)
        return results
    except Exception as e:
        log.warning("Vector search unavailable: %s", e)
        return []


# ---------------------------------------------------------------------------
# Stage 3 — Hybrid pipeline
# ---------------------------------------------------------------------------

# Candidate pool sizes — fast mode reduces reranker input for interactive use.
_CANDIDATES_FAST = 15
_CANDIDATES_FULL = 30


def hybrid_search(
    query: str,
    fts_table: str = "evidence_fts",
    text_key: str = "quote_text",
    vector_table: str = "evidence_quotes",
    fts_limit: int = 100,
    vector_limit: int = 100,
    rerank_top_k: int = 20,
    use_reranker: bool = True,
    db_path: Optional[str] = None,
    fast: bool = False,
) -> dict:
    """Full 3-stage hybrid search pipeline.

    Stage 1: FTS5 BM25 keyword recall (fast, broad coverage)
    Stage 2: LanceDB vector semantic similarity (meaning-aware)
    Stage 3: Cross-encoder reranking (precision scoring)

    Results are fused, deduplicated by text prefix, and ranked by
    cross-encoder score when the reranker is enabled.

    Args:
        query: Natural language search query.
        fts_table: FTS5 virtual table name for keyword search.
        text_key: Column/key holding the main text content.
        vector_table: Source table name for LanceDB vector search.
        fts_limit: Max candidates from FTS5 stage.
        vector_limit: Max candidates from vector stage.
        rerank_top_k: Final number of results after reranking.
        use_reranker: If False, skip cross-encoder (faster but less precise).
        db_path: Override path to litigation_context.db.
        fast: If True, reduce candidate pool sent to reranker (15 vs 30)
              for interactive / typeahead use.  Batch pipelines should
              leave this False.

    Returns:
        Dict with ``results`` (list[dict]), ``stages`` (per-stage timing in
        seconds), and ``total_s`` (wall-clock total).
    """
    stages: dict[str, float] = {}
    t_start = time.perf_counter()

    # --- Stage 1: FTS5 BM25 keyword recall ---
    t0 = time.perf_counter()
    fts_results = fts5_bm25_search(
        query, fts_table=fts_table, text_col=text_key, limit=fts_limit, db_path=db_path
    )
    stages["fts5"] = time.perf_counter() - t0

    # --- Stage 2: Vector semantic similarity ---
    t0 = time.perf_counter()
    vector_results = _vector_search(query, table_name=vector_table, top_k=vector_limit)
    stages["vector"] = time.perf_counter() - t0

    # Normalize vector results to have the same text_key
    for vr in vector_results:
        if text_key not in vr and "text" in vr:
            vr[text_key] = vr["text"]

    # --- Fusion & dedup ---
    t0 = time.perf_counter()
    seen: set[str] = set()
    fused: list[dict] = []

    for doc in fts_results + vector_results:
        text = doc.get(text_key, doc.get("text", "")) or ""
        text = CHILD_NAME_RE.sub("L.D.W.", text)
        prefix = text[:200]
        if prefix and prefix not in seen:
            seen.add(prefix)
            doc[text_key] = text
            fused.append(doc)
    stages["fusion"] = time.perf_counter() - t0

    if not fused:
        stages["total"] = time.perf_counter() - t_start
        return {"results": [], "stages": stages, "total_s": stages["total"]}

    # --- Legal-BERT domain scoring (skip in fast mode) ---
    max_candidates = _CANDIDATES_FAST if fast else _CANDIDATES_FULL
    candidates = fused[:max_candidates]
    has_legalbert = False

    if not fast and len(candidates) > 1:
        try:
            legalbert = _get_legalbert()
            if legalbert is not None and legalbert.is_ready:
                t0 = time.perf_counter()
                doc_texts = [(d.get(text_key, d.get("text", "")) or "")[:2000]
                             for d in candidates]
                lb_scores = legalbert.score_batch(query, doc_texts)
                for d, score in zip(candidates, lb_scores):
                    d["legalbert_score"] = score
                has_legalbert = True
                stages["legalbert"] = time.perf_counter() - t0
        except Exception as e:
            log.warning("Legal-BERT scoring failed (non-fatal): %s", e)

    # --- Stage 3: Cross-encoder reranking + Legal-BERT blend ---
    if use_reranker and len(candidates) > 1:
        try:
            t0 = time.perf_counter()
            from .reranker import rerank

            results = rerank(query, candidates, text_key=text_key, top_k=rerank_top_k)
            stages["rerank"] = time.perf_counter() - t0

            # Blend cross-encoder + Legal-BERT for domain-aware precision
            if has_legalbert and results:
                ce_vals = [d.get("rerank_score", 0) for d in results]
                ce_min, ce_max = min(ce_vals), max(ce_vals)
                ce_range = ce_max - ce_min if ce_max > ce_min else 1.0
                for d in results:
                    norm_ce = (d.get("rerank_score", 0) - ce_min) / ce_range
                    norm_lb = (d.get("legalbert_score", 0) + 1) / 2
                    d["rerank_score"] = 0.7 * norm_ce + 0.3 * norm_lb
                results.sort(key=lambda d: d.get("rerank_score", 0), reverse=True)

            stages["total"] = time.perf_counter() - t_start
            return {"results": results, "stages": stages, "total_s": stages["total"]}
        except Exception as e:
            log.warning("Reranker unavailable, returning BM25-ranked results: %s", e)
            stages["rerank"] = 0.0

    stages["total"] = time.perf_counter() - t_start
    return {
        "results": fused[:rerank_top_k],
        "stages": stages,
        "total_s": stages["total"],
    }
