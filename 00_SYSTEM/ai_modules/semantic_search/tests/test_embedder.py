"""Tests for EvidenceEmbedder (TF-IDF fallback path)."""
from __future__ import annotations

import numpy as np
import pytest

from semantic_search.embedder import EvidenceEmbedder


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

CORPUS = [
    "The court orders the defendant to appear on March first.",
    "Evidence of financial fraud was presented to the jury.",
    "Plaintiff filed a motion for summary judgement.",
    "Witness testimony corroborates the claims of misconduct.",
    "The judge denied the motion to dismiss the case.",
    "Custody agreement modifications require court approval.",
    "Property records show transfer of ownership in January.",
    "Deposition transcripts reveal inconsistent statements.",
]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestEvidenceEmbedder:
    """Tests for the TF-IDF fallback embedder."""

    @pytest.fixture()
    def embedder(self) -> EvidenceEmbedder:
        """Force TF-IDF backend regardless of installed packages."""
        return EvidenceEmbedder(force_tfidf=True)

    def test_backend_is_tfidf(self, embedder: EvidenceEmbedder) -> None:
        assert embedder.backend == "tfidf"

    def test_fit_sets_vocabulary(self, embedder: EvidenceEmbedder) -> None:
        embedder.fit(CORPUS)
        assert embedder.is_fitted
        assert embedder.embedding_dim > 0

    def test_embed_texts_shape(self, embedder: EvidenceEmbedder) -> None:
        embedder.fit(CORPUS)
        vecs = embedder.embed_texts(CORPUS)
        assert isinstance(vecs, np.ndarray)
        assert vecs.shape == (len(CORPUS), embedder.embedding_dim)
        assert vecs.dtype == np.float32

    def test_embed_query_shape(self, embedder: EvidenceEmbedder) -> None:
        embedder.fit(CORPUS)
        vec = embedder.embed_query("court order")
        assert isinstance(vec, np.ndarray)
        assert vec.ndim == 1
        assert vec.shape[0] == embedder.embedding_dim

    def test_embed_empty_list(self, embedder: EvidenceEmbedder) -> None:
        embedder.fit(CORPUS)
        vecs = embedder.embed_texts([])
        assert vecs.shape[0] == 0

    def test_fit_empty_corpus_raises(self, embedder: EvidenceEmbedder) -> None:
        with pytest.raises(ValueError, match="empty corpus"):
            embedder.fit([])

    def test_auto_fit_on_embed(self, embedder: EvidenceEmbedder) -> None:
        """Embedding without explicit fit should auto-fit on provided texts."""
        vecs = embedder.embed_texts(CORPUS)
        assert embedder.is_fitted
        assert vecs.shape[0] == len(CORPUS)

    def test_different_texts_different_vectors(self, embedder: EvidenceEmbedder) -> None:
        embedder.fit(CORPUS)
        v1 = embedder.embed_query("financial fraud evidence")
        v2 = embedder.embed_query("custody agreement children")
        # Vectors should not be identical
        assert not np.allclose(v1, v2)
