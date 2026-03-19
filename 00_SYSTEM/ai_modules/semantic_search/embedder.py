"""Evidence embedding — sentence-transformers (preferred) with TF-IDF fallback.

Provides a unified interface for encoding document chunks into dense vectors.
All operations are local-only; no network calls are ever made.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np

from .config import EMBEDDING_DIM_ST, EMBEDDER_STATE_PATH, MODEL_NAME, TFIDF_PATH

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional dependency probing
# ---------------------------------------------------------------------------
_HAS_SENTENCE_TRANSFORMERS = False
_SentenceTransformer: Any = None

try:
    from sentence_transformers import SentenceTransformer as _ST  # type: ignore[import-untyped]
    _SentenceTransformer = _ST
    _HAS_SENTENCE_TRANSFORMERS = True
    log.debug("sentence-transformers available — will use dense embeddings")
except ImportError:
    log.debug("sentence-transformers not installed — falling back to TF-IDF")

try:
    import joblib  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover — joblib ships with sklearn
    joblib = None  # type: ignore[assignment]

from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402


class EvidenceEmbedder:
    """Unified embedding interface with automatic backend selection.

    Priority order:
    1. ``sentence-transformers`` (``all-MiniLM-L6-v2``, dim 384)
    2. ``TfidfVectorizer`` from scikit-learn (always available)
    """

    def __init__(self, model_name: str = MODEL_NAME, force_tfidf: bool = False) -> None:
        self._backend: str = "tfidf"
        self._st_model: Any = None
        self._tfidf: TfidfVectorizer | None = None
        self._fitted: bool = False

        if _HAS_SENTENCE_TRANSFORMERS and not force_tfidf:
            try:
                self._st_model = _SentenceTransformer(model_name)
                self._backend = "sentence-transformers"
                self._fitted = True
                log.info("Embedder backend: sentence-transformers (%s)", model_name)
            except Exception:
                log.warning(
                    "Failed to load sentence-transformers model '%s'; "
                    "falling back to TF-IDF",
                    model_name,
                    exc_info=True,
                )

        if self._backend == "tfidf":
            self._tfidf = TfidfVectorizer(
                max_features=10_000,
                sublinear_tf=True,
                dtype=np.float32,
            )
            self._try_load_tfidf()
            log.info("Embedder backend: TF-IDF (max_features=10000)")

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def backend(self) -> str:
        """Return active backend name."""
        return self._backend

    @property
    def embedding_dim(self) -> int:
        """Dimensionality of the produced embeddings."""
        if self._backend == "sentence-transformers":
            return EMBEDDING_DIM_ST
        if self._tfidf is not None and hasattr(self._tfidf, "vocabulary_"):
            return len(self._tfidf.vocabulary_)
        return 0  # not yet fitted

    @property
    def is_fitted(self) -> bool:
        return self._fitted

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def fit(self, corpus: list[str]) -> None:
        """Fit the embedder on a corpus.

        No-op for sentence-transformers (pre-trained).
        For TF-IDF, fits the vectoriser and persists it.
        """
        if self._backend == "sentence-transformers":
            return  # pre-trained — nothing to fit

        if not corpus:
            raise ValueError("Cannot fit TF-IDF on an empty corpus")

        assert self._tfidf is not None
        self._tfidf.fit(corpus)
        self._fitted = True
        self._save_tfidf()
        log.info("TF-IDF fitted on %d documents (vocab=%d)", len(corpus), self.embedding_dim)

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        """Batch-embed a list of texts.

        Returns
        -------
        np.ndarray
            Shape ``(len(texts), embedding_dim)`` of type float32.
        """
        if not texts:
            return np.empty((0, self.embedding_dim or 1), dtype=np.float32)

        if self._backend == "sentence-transformers":
            vecs = self._st_model.encode(
                texts, show_progress_bar=False, convert_to_numpy=True,
            )
            return vecs.astype(np.float32)

        # TF-IDF path
        self._ensure_fitted(texts)
        assert self._tfidf is not None
        sparse = self._tfidf.transform(texts)
        return np.asarray(sparse.toarray(), dtype=np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        """Embed a single query string.

        Returns
        -------
        np.ndarray
            Shape ``(embedding_dim,)`` — a 1-D vector.
        """
        vecs = self.embed_texts([query])
        return vecs[0]

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _save_tfidf(self) -> None:
        if joblib is None or self._tfidf is None:
            return
        try:
            joblib.dump(self._tfidf, TFIDF_PATH)
            log.debug("TF-IDF vectorizer saved to %s", TFIDF_PATH)
        except Exception:
            log.warning("Failed to persist TF-IDF vectorizer", exc_info=True)

    def _try_load_tfidf(self) -> None:
        if joblib is None or not Path(TFIDF_PATH).exists():
            return
        try:
            self._tfidf = joblib.load(TFIDF_PATH)
            self._fitted = True
            log.debug("TF-IDF vectorizer loaded from %s", TFIDF_PATH)
        except Exception:
            log.warning("Failed to load persisted TF-IDF; will refit", exc_info=True)

    def _ensure_fitted(self, texts: list[str]) -> None:
        """Auto-fit TF-IDF if not already fitted (convenience for ad-hoc use)."""
        if self._fitted:
            return
        log.info("TF-IDF not yet fitted — auto-fitting on %d provided texts", len(texts))
        self.fit(texts)

    def save_state(self) -> None:
        """Persist full embedder state for later reload."""
        self._save_tfidf()
        if joblib is not None:
            state = {"backend": self._backend, "fitted": self._fitted}
            try:
                joblib.dump(state, EMBEDDER_STATE_PATH)
            except Exception:
                log.warning("Failed to save embedder state", exc_info=True)
