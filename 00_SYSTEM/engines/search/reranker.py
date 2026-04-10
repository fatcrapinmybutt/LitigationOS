"""Cross-encoder reranker for LitigationOS search results.

Uses cross-encoder/ms-marco-MiniLM-L6-v2 (~22M params, ~80MB) to rerank
candidate documents by query-document relevance. Runs on CPU with sub-second
latency for typical result sets (<200 docs).

Cross-encoders jointly encode (query, document) pairs through a single
transformer pass, producing far more accurate relevance scores than
bi-encoder cosine similarity alone. Expected MRR@10 lift: 25-35%.

v2.1 — Singleton pattern: model loads once, cached for process lifetime.
"""
from __future__ import annotations

import logging
import re
import time
from typing import Sequence

log = logging.getLogger(__name__)

CHILD_NAME_RE = re.compile(
    r"\b(?:Lincoln\s+(?:Dean\s+)?(?:Watson|Pigors|Watson[- ]Pigors))\b",
    re.IGNORECASE,
)


class CrossEncoderReranker:
    """Singleton-friendly cross-encoder wrapper.  Loads model once on first use."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L6-v2"):
        t0 = time.perf_counter()
        from sentence_transformers import CrossEncoder

        self._model = CrossEncoder(model_name)
        self._load_time = time.perf_counter() - t0
        log.info(
            "CrossEncoderReranker loaded %s in %.2fs",
            model_name,
            self._load_time,
        )

    def rerank(
        self,
        query: str,
        documents: Sequence[dict],
        text_key: str = "text",
        top_k: int = 10,
    ) -> list[dict]:
        """Rerank *documents* by cross-encoder relevance to *query*.

        Returns top-k dicts sorted descending by ``rerank_score``.
        """
        if not documents:
            return []

        pairs = []
        for doc in documents:
            text = doc.get(text_key, "") or ""
            text = CHILD_NAME_RE.sub("L.D.W.", text)
            pairs.append((query, text))

        t0 = time.perf_counter()
        scores = self._model.predict(pairs, show_progress_bar=False)
        predict_ms = (time.perf_counter() - t0) * 1000

        for doc, score in zip(documents, scores):
            doc["rerank_score"] = float(score)

        ranked = sorted(documents, key=lambda d: d["rerank_score"], reverse=True)
        log.debug(
            "Reranked %d docs in %.1fms (top score %.3f)",
            len(documents),
            predict_ms,
            ranked[0]["rerank_score"] if ranked else 0,
        )
        return ranked[:top_k]


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_RERANKER_INSTANCE: CrossEncoderReranker | None = None


def get_reranker() -> CrossEncoderReranker:
    """Return the process-wide CrossEncoderReranker (lazy-loaded, cached)."""
    global _RERANKER_INSTANCE
    if _RERANKER_INSTANCE is None:
        _RERANKER_INSTANCE = CrossEncoderReranker()
    return _RERANKER_INSTANCE


# ---------------------------------------------------------------------------
# Convenience function (backward-compatible public API)
# ---------------------------------------------------------------------------
def rerank(
    query: str,
    documents: Sequence[dict],
    text_key: str = "text",
    top_k: int = 10,
) -> list[dict]:
    """Rerank documents by cross-encoder relevance score.

    Delegates to the module-level singleton so the model is loaded only once.

    Args:
        query: Search query string.
        documents: List of dicts, each containing a text field.
        text_key: Key in each dict holding the text to rank against.
        top_k: Number of top results to return.

    Returns:
        Top-k documents sorted by cross-encoder score descending,
        with ``rerank_score`` added to each dict.
    """
    return get_reranker().rerank(query, documents, text_key=text_key, top_k=top_k)
