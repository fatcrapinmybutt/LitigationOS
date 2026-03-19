#!/usr/bin/env python3
"""
MBP LitigationOS — Inverted Index for Instant TF-IDF Lookups
=============================================================
Pre-computes a term → [(doc_id, tfidf_score)] mapping from the TF-IDF matrix.
Enables sub-20ms query-time retrieval without full cosine similarity computation.

Usage:
    # Build after training
    from inverted_index import InvertedIndex
    idx = InvertedIndex.build(vectorizer, tfidf_matrix)
    idx.save()

    # Load and search
    idx = InvertedIndex.load()
    results = idx.fast_search("MCR 2.003 disqualification", top_k=10)
"""

from __future__ import annotations

import os
import pickle
import re
import time
from pathlib import Path
from typing import Optional

import numpy as np
from scipy.sparse import csr_matrix

MODEL_DIR = Path(__file__).parent / "model_data"
INDEX_PATH = MODEL_DIR / "inverted_index.pkl"

# Minimal stop words for query tokenization
_STOP = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "what", "how", "when", "where",
    "why", "which", "who", "about", "this", "that", "and", "or", "but",
    "not", "if", "my", "me", "i", "it", "its", "their", "there",
})

_TOKEN_RE = re.compile(r"(?u)\b[a-zA-Z0-9._]{2,}\b")


class InvertedIndex:
    """Pre-computed inverted index from a TF-IDF matrix for fast retrieval."""

    def __init__(self):
        self.index: dict[str, list[tuple[int, float]]] = {}
        self.vocab: dict[str, int] = {}  # term -> term_index (for reference)
        self.num_docs: int = 0
        self.build_time: float = 0.0

    @classmethod
    def build(cls, vectorizer, tfidf_matrix: csr_matrix) -> "InvertedIndex":
        """Build inverted index from a fitted vectorizer and TF-IDF matrix.

        For each term in the vocabulary, stores a posting list of
        (doc_id, tfidf_score) pairs sorted by score descending.
        """
        t0 = time.time()
        idx = cls()
        idx.num_docs = tfidf_matrix.shape[0]

        # Invert: vocabulary maps term -> column index
        vocab = vectorizer.vocabulary_
        idx.vocab = vocab

        # Convert to CSC for efficient column slicing
        csc = tfidf_matrix.tocsc()

        # Build term -> feature_index reverse map
        inv_vocab = {col_idx: term for term, col_idx in vocab.items()}

        for col_idx in range(csc.shape[1]):
            col = csc.getcol(col_idx)
            if col.nnz == 0:
                continue

            term = inv_vocab.get(col_idx)
            if not term:
                continue

            # Extract (row_index, score) pairs
            rows = col.indices
            scores = col.data

            # Sort by score descending — store as list of (doc_id, score)
            order = np.argsort(-scores)
            posting = [(int(rows[i]), round(float(scores[i]), 5)) for i in order]

            idx.index[term] = posting

        idx.build_time = time.time() - t0
        return idx

    def save(self, path: Optional[Path] = None):
        """Persist index to disk."""
        path = path or INDEX_PATH
        path.parent.mkdir(exist_ok=True)
        data = {
            "index": self.index,
            "vocab": self.vocab,
            "num_docs": self.num_docs,
            "build_time": self.build_time,
        }
        with open(path, "wb") as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
        size_mb = os.path.getsize(path) / (1024 * 1024)
        print(f"[InvertedIndex] Saved {len(self.index)} terms, "
              f"{self.num_docs} docs → {path} ({size_mb:.1f} MB)")

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "InvertedIndex":
        """Load pre-built index from disk."""
        path = path or INDEX_PATH
        idx = cls()
        with open(path, "rb") as f:
            data = pickle.load(f)
        idx.index = data["index"]
        idx.vocab = data["vocab"]
        idx.num_docs = data["num_docs"]
        idx.build_time = data.get("build_time", 0.0)
        return idx

    @staticmethod
    def exists(path: Optional[Path] = None) -> bool:
        return (path or INDEX_PATH).exists()

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize query text matching the TF-IDF vectorizer's token pattern."""
        tokens = _TOKEN_RE.findall(text.lower())
        return [t for t in tokens if t not in _STOP and len(t) >= 2]

    def fast_search(self, query: str, top_k: int = 10) -> list[dict]:
        """Fast retrieval using inverted index posting lists.

        Tokenizes the query, looks up each term's posting list,
        and merges scores by summing TF-IDF weights per document.
        Returns top_k results sorted by aggregate score.
        Target: <20ms for typical queries.
        """
        t0 = time.time()
        tokens = self._tokenize(query)
        if not tokens:
            return []

        # Accumulate scores per doc_id
        doc_scores: dict[int, float] = {}
        matched_terms = 0

        for token in tokens:
            posting = self.index.get(token)
            if not posting:
                continue
            matched_terms += 1
            for doc_id, score in posting:
                doc_scores[doc_id] = doc_scores.get(doc_id, 0.0) + score

        if not doc_scores:
            # Try bigrams: adjacent token pairs
            for i in range(len(tokens) - 1):
                bigram = f"{tokens[i]} {tokens[i+1]}"
                posting = self.index.get(bigram)
                if posting:
                    matched_terms += 1
                    for doc_id, score in posting:
                        doc_scores[doc_id] = doc_scores.get(doc_id, 0.0) + score

        if not doc_scores:
            return []

        # Sort by score descending, take top_k
        top_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        elapsed_ms = (time.time() - t0) * 1000
        results = [
            {"doc_id": doc_id, "score": round(score, 4), "matched_terms": matched_terms}
            for doc_id, score in top_docs
        ]

        if results:
            results[0]["elapsed_ms"] = round(elapsed_ms, 2)

        return results


def build_from_model():
    """Convenience: load trained model files and build the inverted index."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from scipy.sparse import load_npz

    print("[InvertedIndex] Loading vectorizer and TF-IDF matrix...")
    with open(MODEL_DIR / "vectorizer.pkl", "rb") as f:
        vectorizer = pickle.load(f)
    tfidf_matrix = load_npz(MODEL_DIR / "tfidf_matrix.npz")

    print(f"[InvertedIndex] Matrix: {tfidf_matrix.shape[0]} docs × {tfidf_matrix.shape[1]} features")
    idx = InvertedIndex.build(vectorizer, tfidf_matrix)
    print(f"[InvertedIndex] Built in {idx.build_time:.2f}s — {len(idx.index)} terms indexed")
    idx.save()
    return idx


if __name__ == "__main__":
    build_from_model()
