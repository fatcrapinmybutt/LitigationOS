"""Search index — FAISS (preferred) with brute-force numpy fallback.

Maintains a vector index alongside a parallel metadata list so that
search results can be traced back to their source documents, pages,
and case lanes.
"""
from __future__ import annotations

import logging
import pickle
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from .config import FAISS_INDEX_PATH, METADATA_PATH, SIMILARITY_THRESHOLD, TOP_K_DEFAULT

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional FAISS probing
# ---------------------------------------------------------------------------
_HAS_FAISS = False
_faiss: Any = None

try:
    import faiss as _faiss_mod  # type: ignore[import-untyped]
    _faiss = _faiss_mod
    _HAS_FAISS = True
    log.debug("FAISS available — using optimised index")
except ImportError:
    log.debug("FAISS not installed — falling back to brute-force numpy search")


@dataclass(frozen=True, slots=True)
class SearchResult:
    """A single search hit."""

    chunk_id: int
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


class SearchIndex:
    """Vector similarity index with FAISS / numpy backend."""

    def __init__(self, dim: int = 0) -> None:
        self._dim: int = dim
        self._lock = threading.Lock()

        # FAISS index (set in build_index / load)
        self._faiss_index: Any = None
        # Numpy fallback storage
        self._vectors: np.ndarray | None = None

        # Parallel metadata list — metadata[i] corresponds to vector i
        self._metadata: list[dict[str, Any]] = []

        self._backend: str = "faiss" if _HAS_FAISS else "numpy"

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def size(self) -> int:
        """Number of indexed vectors."""
        if self._faiss_index is not None:
            return int(self._faiss_index.ntotal)
        if self._vectors is not None:
            return self._vectors.shape[0]
        return 0

    @property
    def dim(self) -> int:
        return self._dim

    @property
    def backend(self) -> str:
        return self._backend

    # ------------------------------------------------------------------
    # Build / Add
    # ------------------------------------------------------------------

    def build_index(
        self,
        embeddings: np.ndarray,
        metadata: list[dict[str, Any]],
    ) -> None:
        """Create a new index from *embeddings* and *metadata*.

        Replaces any existing index.
        """
        if embeddings.ndim != 2:
            raise ValueError("embeddings must be 2-D (n_vectors, dim)")
        if len(metadata) != embeddings.shape[0]:
            raise ValueError("metadata length must match number of embeddings")

        with self._lock:
            self._dim = embeddings.shape[1]
            self._metadata = list(metadata)
            self._build_backend(embeddings)

        log.info(
            "Index built: %d vectors, dim=%d, backend=%s",
            embeddings.shape[0], self._dim, self._backend,
        )

    def add_to_index(
        self,
        embeddings: np.ndarray,
        metadata: list[dict[str, Any]],
    ) -> None:
        """Incrementally add vectors to the existing index."""
        if embeddings.ndim != 2:
            raise ValueError("embeddings must be 2-D")
        if len(metadata) != embeddings.shape[0]:
            raise ValueError("metadata length must match embedding count")
        if self._dim and embeddings.shape[1] != self._dim:
            raise ValueError(
                f"Dimension mismatch: index has {self._dim}, "
                f"got {embeddings.shape[1]}"
            )

        with self._lock:
            if self.size == 0:
                self._dim = embeddings.shape[1]
                self._metadata = list(metadata)
                self._build_backend(embeddings)
                return

            self._metadata.extend(metadata)
            vecs = np.ascontiguousarray(embeddings, dtype=np.float32)

            if self._faiss_index is not None:
                self._faiss_index.add(vecs)
            elif self._vectors is not None:
                self._vectors = np.vstack([self._vectors, vecs])

        log.debug("Added %d vectors to index (total=%d)", embeddings.shape[0], self.size)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = TOP_K_DEFAULT,
        min_score: float = SIMILARITY_THRESHOLD,
    ) -> list[SearchResult]:
        """Return the *top_k* nearest neighbours above *min_score*."""
        if self.size == 0:
            return []

        query = np.ascontiguousarray(
            query_embedding.reshape(1, -1), dtype=np.float32,
        )

        with self._lock:
            if self._faiss_index is not None:
                scores, indices = self._faiss_index.search(query, min(top_k, self.size))
                scores = scores[0]
                indices = indices[0]
            else:
                scores, indices = self._numpy_search(query[0], top_k)

        results: list[SearchResult] = []
        for score, idx in zip(scores, indices):
            idx = int(idx)
            score = float(score)
            if idx < 0 or score < min_score:
                continue
            results.append(SearchResult(
                chunk_id=idx,
                score=score,
                metadata=self._metadata[idx] if idx < len(self._metadata) else {},
            ))

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: str | None = None) -> None:
        """Persist the index and metadata to disk."""
        idx_path = path or FAISS_INDEX_PATH
        meta_path = str(Path(idx_path).with_suffix(".meta.pkl")) if path else METADATA_PATH

        with self._lock:
            if self._faiss_index is not None:
                _faiss.write_index(self._faiss_index, idx_path)
            elif self._vectors is not None:
                np.save(idx_path + ".npy", self._vectors)

            with open(meta_path, "wb") as fh:
                pickle.dump({"metadata": self._metadata, "dim": self._dim}, fh)

        log.info("Index saved to %s (%d vectors)", idx_path, self.size)

    def load(self, path: str | None = None) -> None:
        """Load a previously saved index."""
        idx_path = path or FAISS_INDEX_PATH
        meta_path = str(Path(idx_path).with_suffix(".meta.pkl")) if path else METADATA_PATH

        if not Path(meta_path).exists():
            log.warning("No metadata file at %s — cannot load index", meta_path)
            return

        with open(meta_path, "rb") as fh:
            state = pickle.load(fh)  # noqa: S301

        with self._lock:
            self._metadata = state["metadata"]
            self._dim = state.get("dim", 0)

            if _HAS_FAISS and Path(idx_path).exists():
                self._faiss_index = _faiss.read_index(idx_path)
                self._backend = "faiss"
                log.info("FAISS index loaded from %s (%d vectors)", idx_path, self.size)
            elif Path(idx_path + ".npy").exists():
                self._vectors = np.load(idx_path + ".npy")
                self._backend = "numpy"
                log.info("Numpy index loaded from %s (%d vectors)", idx_path + ".npy", self.size)
            else:
                log.warning("No index file found at %s", idx_path)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_backend(self, embeddings: np.ndarray) -> None:
        vecs = np.ascontiguousarray(embeddings, dtype=np.float32)

        if _HAS_FAISS:
            # Normalise for cosine similarity via inner-product index
            _faiss.normalize_L2(vecs)
            index = _faiss.IndexFlatIP(self._dim)
            index.add(vecs)
            self._faiss_index = index
            self._vectors = None
            self._backend = "faiss"
        else:
            # Normalise rows for cosine similarity
            norms = np.linalg.norm(vecs, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1.0, norms)
            self._vectors = vecs / norms
            self._faiss_index = None
            self._backend = "numpy"

    def _numpy_search(
        self, query: np.ndarray, top_k: int,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Brute-force cosine similarity search."""
        assert self._vectors is not None
        q = query / (np.linalg.norm(query) or 1.0)
        scores = self._vectors @ q  # cosine similarities
        top_indices = np.argsort(scores)[::-1][:top_k]
        return scores[top_indices], top_indices
