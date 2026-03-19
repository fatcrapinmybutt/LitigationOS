"""
Legal Reranker — LitigationOS Legal AI
=======================================
Cross-encoder reranking and Maximal Marginal Relevance (MMR) diversity
for legal evidence retrieval.

Applies RAG best practices from rag-engineer + rag-implementation skills:
  1. Cross-encoder reranking (sentence-transformers)
  2. MMR for diversity-relevance balance
  3. Metadata-aware scoring (evidence strength, lane relevance)
  4. Graceful degradation: cross-encoder → cosine → score passthrough

Pipeline position: after initial retrieval (BM25/FTS5/hybrid), before
generation.  Plugs into LegalRAGEngine and HybridRetriever.

Usage:
    from legal_ai.reranker import LegalReranker
    reranker = LegalReranker()
    reranked = reranker.rerank(query, candidates, top_k=10)
    diverse  = reranker.mmr_select(query, candidates, top_k=5, lambda_mult=0.5)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger("legal_ai.reranker")

# ── Lazy dependency loading ──────────────────────────────────────
# These heavy libraries (sentence-transformers, numpy) are imported on first
# use — not at module scope — so that importing reranker.py is instantaneous
# and never blocks test collection or lightweight consumers.

_cross_encoder_available = False
_CrossEncoder = None

_numpy_available = False
_np = None

_st_available = False
_SentenceTransformer = None

_deps_loaded = False


def _ensure_optional_deps() -> None:
    """Import optional heavy dependencies on first use."""
    global _cross_encoder_available, _CrossEncoder
    global _numpy_available, _np
    global _st_available, _SentenceTransformer
    global _deps_loaded

    if _deps_loaded:
        return
    _deps_loaded = True

    try:
        from sentence_transformers import CrossEncoder as _CE  # type: ignore
        _CrossEncoder = _CE
        _cross_encoder_available = True
    except ImportError:
        logger.debug("sentence-transformers not available — cross-encoder reranking disabled")

    try:
        import numpy as _numpy  # type: ignore
        _np = _numpy
        _numpy_available = True
    except ImportError:
        logger.debug("numpy not available — MMR disabled")

    try:
        from sentence_transformers import SentenceTransformer as _ST  # type: ignore
        _SentenceTransformer = _ST
        _st_available = True
    except ImportError:
        pass


# ── Data Models ──────────────────────────────────────────────────

@dataclass
class RerankResult:
    """A single reranked candidate with scores."""
    text: str
    original_score: float = 0.0
    rerank_score: float = 0.0
    combined_score: float = 0.0
    source: str = ""
    lane: str = ""
    evidence_strength: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)
    rank: int = 0


@dataclass
class RerankReport:
    """Summary metrics from a reranking operation."""
    query: str = ""
    method: str = "passthrough"
    candidates_in: int = 0
    results_out: int = 0
    time_ms: float = 0.0
    top_score: float = 0.0
    avg_score: float = 0.0
    position_changes: int = 0


# ── Evidence strength bonuses ────────────────────────────────────

STRENGTH_BONUS: Dict[str, float] = {
    "strong": 0.10,
    "moderate": 0.05,
    "weak": 0.0,
    "unknown": 0.0,
}

LANE_RELEVANCE_BONUS: float = 0.08


# ── Cross-Encoder Models ────────────────────────────────────────

DEFAULT_CROSS_ENCODER = "cross-encoder/ms-marco-MiniLM-L-6-v2"
LEGAL_CROSS_ENCODER = "cross-encoder/ms-marco-MiniLM-L-12-v2"


# ── Main Class ───────────────────────────────────────────────────

class LegalReranker:
    """
    Cross-encoder reranker with legal-domain enhancements.

    Applies sentence-transformers CrossEncoder for precise relevance
    scoring, then adjusts for evidence strength and lane relevance.
    Falls back to cosine similarity or score passthrough when
    cross-encoder is unavailable.

    Tool Schema (for MCP/agent integration):
        name: legal_rerank
        description: >
            Rerank retrieved legal evidence for a query.
            Use when initial retrieval returns too many results
            or ranking quality is poor.
        parameters:
            query: str — The legal query to rerank against
            candidates: list — Retrieved evidence items (text + score + source)
            top_k: int — Number of results to return (default 10)
            lane: str — Optional case lane filter (A-F)
        returns:
            results: list[RerankResult] — Reranked evidence
            report: RerankReport — Reranking metrics
    """

    def __init__(
        self,
        model_name: str = DEFAULT_CROSS_ENCODER,
        use_cross_encoder: bool = True,
        embedding_model: Optional[str] = None,
    ) -> None:
        _ensure_optional_deps()

        self._model_name = model_name
        self._cross_encoder: Optional[Any] = None
        self._embedder: Optional[Any] = None
        self._method = "passthrough"

        # Try cross-encoder first (highest quality)
        if use_cross_encoder and _cross_encoder_available and _CrossEncoder is not None:
            try:
                self._cross_encoder = _CrossEncoder(model_name)
                self._method = "cross_encoder"
                logger.info("LegalReranker: cross-encoder loaded (%s)", model_name)
            except Exception as exc:
                logger.warning("Cross-encoder load failed: %s — trying embedder", exc)

        # Fallback to embedding cosine similarity
        if self._cross_encoder is None and _st_available and _SentenceTransformer is not None:
            emb_model = embedding_model or "all-MiniLM-L6-v2"
            try:
                self._embedder = _SentenceTransformer(emb_model)
                self._method = "cosine_similarity"
                logger.info("LegalReranker: using cosine similarity fallback (%s)", emb_model)
            except Exception as exc:
                logger.warning("Embedder load failed: %s — score passthrough only", exc)

        if self._cross_encoder is None and self._embedder is None:
            logger.info("LegalReranker: no ML models — using score passthrough")

        # Stats
        self._total_reranks: int = 0
        self._total_time_ms: float = 0.0

    # ── Public API ───────────────────────────────────────────────

    def rerank(
        self,
        query: str,
        candidates: Sequence[Dict[str, Any]],
        top_k: int = 10,
        lane: Optional[str] = None,
        alpha: float = 0.7,
    ) -> Tuple[List[RerankResult], RerankReport]:
        """
        Rerank candidates for the given query.

        Args:
            query:      Natural-language legal query.
            candidates: List of dicts with at least 'text' key.
                        Optional: 'score', 'source', 'lane', 'evidence_strength'.
            top_k:      Number of top results to return.
            lane:       Target case lane for relevance bonus.
            alpha:      Weight for rerank score vs original (0=original, 1=rerank).

        Returns:
            (results, report) — Reranked results and summary metrics.
        """
        t0 = time.perf_counter()
        self._total_reranks += 1

        if not candidates:
            return [], RerankReport(query=query, method=self._method)

        # Extract texts
        texts = [c.get("text", "") for c in candidates]

        # Score based on available method
        if self._method == "cross_encoder":
            rerank_scores = self._cross_encoder_score(query, texts)
        elif self._method == "cosine_similarity":
            rerank_scores = self._cosine_score(query, texts)
        else:
            rerank_scores = [c.get("score", 0.0) for c in candidates]

        # Build results with combined scores
        results: List[RerankResult] = []
        for i, (candidate, rerank_score) in enumerate(zip(candidates, rerank_scores)):
            original_score = float(candidate.get("score", 0.0))

            # Normalize rerank score to [0, 1] if cross-encoder
            if self._method == "cross_encoder":
                norm_rerank = self._sigmoid(rerank_score)
            else:
                norm_rerank = rerank_score

            # Combined score: weighted blend
            combined = alpha * norm_rerank + (1.0 - alpha) * original_score

            # Evidence strength bonus
            strength = candidate.get("evidence_strength", "unknown")
            combined += STRENGTH_BONUS.get(strength, 0.0)

            # Lane relevance bonus
            cand_lane = candidate.get("lane", "")
            if lane and cand_lane and cand_lane.upper() == lane.upper():
                combined += LANE_RELEVANCE_BONUS

            results.append(RerankResult(
                text=candidate.get("text", ""),
                original_score=original_score,
                rerank_score=float(rerank_score),
                combined_score=round(combined, 6),
                source=candidate.get("source", ""),
                lane=cand_lane,
                evidence_strength=strength,
                metadata=candidate.get("metadata", {}),
            ))

        # Sort by combined score descending
        results.sort(key=lambda r: r.combined_score, reverse=True)

        # Assign ranks
        for rank_i, r in enumerate(results):
            r.rank = rank_i + 1

        # Count position changes
        position_changes = self._count_position_changes(candidates, results)

        # Trim to top_k
        results = results[:top_k]

        elapsed_ms = (time.perf_counter() - t0) * 1000
        self._total_time_ms += elapsed_ms

        report = RerankReport(
            query=query,
            method=self._method,
            candidates_in=len(candidates),
            results_out=len(results),
            time_ms=round(elapsed_ms, 2),
            top_score=results[0].combined_score if results else 0.0,
            avg_score=round(
                sum(r.combined_score for r in results) / len(results), 4
            ) if results else 0.0,
            position_changes=position_changes,
        )

        return results, report

    def mmr_select(
        self,
        query: str,
        candidates: Sequence[Dict[str, Any]],
        top_k: int = 5,
        fetch_k: int = 20,
        lambda_mult: float = 0.5,
    ) -> Tuple[List[RerankResult], RerankReport]:
        """
        Maximal Marginal Relevance selection.

        Balances relevance to query with diversity among selected results.
        Prevents redundant evidence from dominating the context window.

        Args:
            query:       Legal query.
            candidates:  Retrieved evidence items.
            top_k:       Number to select.
            fetch_k:     Candidates to consider (pre-filter).
            lambda_mult: 0.0 = max diversity, 1.0 = max relevance.

        Returns:
            (selected, report) — Diverse + relevant subset.
        """
        t0 = time.perf_counter()

        _ensure_optional_deps()
        if not candidates or not _numpy_available or _np is None:
            # Fallback: just take top_k by score
            sorted_cands = sorted(candidates, key=lambda c: c.get("score", 0), reverse=True)
            results = [
                RerankResult(
                    text=c.get("text", ""),
                    original_score=float(c.get("score", 0)),
                    combined_score=float(c.get("score", 0)),
                    source=c.get("source", ""),
                    rank=i + 1,
                )
                for i, c in enumerate(sorted_cands[:top_k])
            ]
            elapsed_ms = (time.perf_counter() - t0) * 1000
            return results, RerankReport(
                query=query, method="score_passthrough",
                candidates_in=len(candidates), results_out=len(results),
                time_ms=round(elapsed_ms, 2),
            )

        if self._embedder is None:
            # No embedder — fall back to rerank then deduplicate
            return self.rerank(query, candidates, top_k=top_k)

        # Encode query and candidates
        texts = [c.get("text", "") for c in candidates[:fetch_k]]
        try:
            query_embedding = self._embedder.encode([query])[0]
            doc_embeddings = self._embedder.encode(texts)
        except Exception as exc:
            logger.warning("MMR encoding failed: %s — falling back to rerank", exc)
            return self.rerank(query, candidates, top_k=top_k)

        # Cosine similarities
        query_sims = self._cosine_sim_matrix(
            query_embedding.reshape(1, -1), doc_embeddings
        ).flatten()

        selected_indices: List[int] = []
        remaining = list(range(len(texts)))

        for _ in range(min(top_k, len(texts))):
            if not remaining:
                break

            if not selected_indices:
                # First: pick most relevant
                best_idx = remaining[int(_np.argmax(query_sims[remaining]))]
            else:
                # MMR formula
                mmr_scores = []
                selected_embs = doc_embeddings[selected_indices]
                for idx in remaining:
                    relevance = query_sims[idx]
                    max_sim = float(_np.max(
                        self._cosine_sim_matrix(
                            doc_embeddings[idx].reshape(1, -1), selected_embs
                        )
                    ))
                    mmr = lambda_mult * relevance - (1.0 - lambda_mult) * max_sim
                    mmr_scores.append(mmr)
                best_idx = remaining[int(_np.argmax(mmr_scores))]

            selected_indices.append(best_idx)
            remaining.remove(best_idx)

        # Build results
        results = []
        for rank_i, idx in enumerate(selected_indices):
            c = candidates[idx]
            results.append(RerankResult(
                text=c.get("text", ""),
                original_score=float(c.get("score", 0)),
                rerank_score=float(query_sims[idx]),
                combined_score=float(query_sims[idx]),
                source=c.get("source", ""),
                lane=c.get("lane", ""),
                evidence_strength=c.get("evidence_strength", "unknown"),
                metadata=c.get("metadata", {}),
                rank=rank_i + 1,
            ))

        elapsed_ms = (time.perf_counter() - t0) * 1000
        return results, RerankReport(
            query=query, method="mmr",
            candidates_in=len(candidates), results_out=len(results),
            time_ms=round(elapsed_ms, 2),
            top_score=results[0].combined_score if results else 0.0,
            avg_score=round(
                sum(r.combined_score for r in results) / len(results), 4
            ) if results else 0.0,
        )

    def get_stats(self) -> Dict[str, Any]:
        """Return reranker statistics."""
        return {
            "method": self._method,
            "model": self._model_name if self._method == "cross_encoder" else "n/a",
            "cross_encoder_available": _cross_encoder_available,
            "embedder_available": _st_available,
            "numpy_available": _numpy_available,
            "total_reranks": self._total_reranks,
            "total_time_ms": round(self._total_time_ms, 2),
            "avg_time_ms": round(
                self._total_time_ms / self._total_reranks, 2
            ) if self._total_reranks > 0 else 0.0,
        }

    # ── Private Methods ──────────────────────────────────────────

    def _cross_encoder_score(self, query: str, texts: List[str]) -> List[float]:
        """Score query-text pairs using cross-encoder."""
        try:
            pairs = [[query, text] for text in texts]
            scores = self._cross_encoder.predict(pairs)
            return [float(s) for s in scores]
        except Exception as exc:
            logger.warning("Cross-encoder scoring failed: %s", exc)
            return [0.0] * len(texts)

    def _cosine_score(self, query: str, texts: List[str]) -> List[float]:
        """Score via cosine similarity of embeddings."""
        try:
            all_texts = [query] + texts
            embeddings = self._embedder.encode(all_texts)
            query_emb = embeddings[0]
            doc_embs = embeddings[1:]
            sims = self._cosine_sim_matrix(
                query_emb.reshape(1, -1), doc_embs
            ).flatten()
            return [float(s) for s in sims]
        except Exception as exc:
            logger.warning("Cosine scoring failed: %s", exc)
            return [0.0] * len(texts)

    @staticmethod
    def _sigmoid(x: float) -> float:
        """Sigmoid normalization to [0, 1]."""
        try:
            return 1.0 / (1.0 + 2.718281828 ** (-x))
        except (OverflowError, ValueError):
            return 1.0 if x > 0 else 0.0

    @staticmethod
    def _cosine_sim_matrix(a, b) -> Any:
        """Cosine similarity between matrix a (n×d) and b (m×d)."""
        _ensure_optional_deps()
        if _np is None:
            return [[0.0]]
        a_norm = a / (_np.linalg.norm(a, axis=1, keepdims=True) + 1e-10)
        b_norm = b / (_np.linalg.norm(b, axis=1, keepdims=True) + 1e-10)
        return a_norm @ b_norm.T

    @staticmethod
    def _count_position_changes(
        original: Sequence[Dict[str, Any]],
        reranked: List[RerankResult],
    ) -> int:
        """Count how many items changed position after reranking."""
        orig_order = {
            (c.get("text", ""))[:80]: i for i, c in enumerate(original)
        }
        changes = 0
        for new_pos, result in enumerate(reranked):
            old_pos = orig_order.get(result.text[:80])
            if old_pos is not None and old_pos != new_pos:
                changes += 1
        return changes
