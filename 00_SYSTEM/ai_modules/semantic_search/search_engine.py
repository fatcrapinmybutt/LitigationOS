"""Semantic search engine — the main orchestrator.

Combines the chunker, embedder, and index into a single ``search()`` call.
Supports lane-based filtering, score thresholds, and incremental ingestion.
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np

from .chunker import Chunk, DocumentChunker
from .config import SIMILARITY_THRESHOLD, TOP_K_DEFAULT, VALID_LANES
from .embedder import EvidenceEmbedder
from .index_builder import SearchIndex, SearchResult

log = logging.getLogger(__name__)


class SemanticSearchEngine:
    """High-level semantic evidence search.

    Usage::

        engine = SemanticSearchEngine()
        engine.ingest_document("path/to/file.pdf", text, {"lane": "A"})
        results = engine.search("motion to disqualify", lane="E")
    """

    def __init__(
        self,
        force_tfidf: bool = False,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> None:
        self._chunker = DocumentChunker(
            **({"chunk_size": chunk_size} if chunk_size else {}),
            **({"chunk_overlap": chunk_overlap} if chunk_overlap else {}),
        )
        self._embedder = EvidenceEmbedder(force_tfidf=force_tfidf)
        self._index = SearchIndex()

        # Corpus texts needed for TF-IDF fitting
        self._corpus_texts: list[str] = []
        # Map from index position → Chunk for text retrieval
        self._chunk_store: list[Chunk] = []
        self._needs_refit: bool = self._embedder.backend == "tfidf"

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        top_k: int = TOP_K_DEFAULT,
        lane: str | None = None,
        min_score: float = SIMILARITY_THRESHOLD,
    ) -> list[dict[str, Any]]:
        """Search the index for *query*.

        Parameters
        ----------
        query : str
            Natural-language search query.
        top_k : int
            Maximum number of results.
        lane : str | None
            Filter results to a specific case lane (A–F).
        min_score : float
            Minimum cosine similarity to include in results.

        Returns
        -------
        list[dict]
            Each dict contains: ``score``, ``chunk_text``, ``file_path``,
            ``page_number``, ``lane``, plus any extra metadata.
        """
        if self._index.size == 0:
            return []

        if lane and lane.upper() not in VALID_LANES:
            log.warning("Invalid lane '%s' — ignoring filter", lane)
            lane = None

        query_vec = self._embedder.embed_query(query)
        # Fetch extra results so lane filter doesn't starve output
        fetch_k = top_k * 3 if lane else top_k
        raw: list[SearchResult] = self._index.search(
            query_vec, top_k=fetch_k, min_score=min_score,
        )

        results: list[dict[str, Any]] = []
        for hit in raw:
            meta = dict(hit.metadata)
            if lane and meta.get("lane", "").upper() != lane.upper():
                continue

            # Attach chunk text from store
            chunk_text = ""
            if 0 <= hit.chunk_id < len(self._chunk_store):
                chunk_text = self._chunk_store[hit.chunk_id].text

            results.append({
                "score": round(hit.score, 4),
                "chunk_text": chunk_text,
                "file_path": meta.get("file_path", ""),
                "page_number": meta.get("page_number"),
                "lane": meta.get("lane", ""),
                "case_number": meta.get("case_number", ""),
                **{k: v for k, v in meta.items()
                   if k not in ("file_path", "page_number", "lane", "case_number")},
            })

            if len(results) >= top_k:
                break

        log.debug("Search '%s' → %d results (lane=%s)", query[:60], len(results), lane)
        return results

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    def ingest_document(
        self,
        file_path: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """Chunk, embed, and index a single document.

        Returns the number of chunks ingested.
        """
        meta = metadata or {}
        meta.setdefault("file_path", file_path)

        chunks = self._chunker.chunk_text(text, metadata=meta)
        if not chunks:
            return 0

        return self._index_chunks(chunks)

    def bulk_ingest(self, documents: list[dict[str, Any]]) -> int:
        """Ingest many documents at once.

        Each dict must have ``file_path`` and ``text`` keys.  Optional
        keys: ``lane``, ``case_number``, ``page_number``, and any other
        metadata.

        Returns total number of chunks ingested.
        """
        all_chunks: list[Chunk] = []
        for doc in documents:
            text = doc.get("text", "")
            meta = {k: v for k, v in doc.items() if k != "text"}
            meta.setdefault("file_path", doc.get("file_path", ""))
            chunks = self._chunker.chunk_text(text, metadata=meta)
            all_chunks.extend(chunks)

        if not all_chunks:
            return 0

        return self._index_chunks(all_chunks)

    # ------------------------------------------------------------------
    # Stats & persistence
    # ------------------------------------------------------------------

    def get_stats(self) -> dict[str, Any]:
        """Return index and embedder statistics."""
        return {
            "index_size": self._index.size,
            "index_dim": self._index.dim,
            "index_backend": self._index.backend,
            "embedder_backend": self._embedder.backend,
            "embedder_dim": self._embedder.embedding_dim,
            "chunk_count": len(self._chunk_store),
            "corpus_size": len(self._corpus_texts),
        }

    def save(self) -> None:
        """Persist index and embedder state to disk."""
        self._index.save()
        self._embedder.save_state()
        log.info("Search engine state saved")

    def load(self) -> None:
        """Load previously saved state."""
        self._index.load()
        log.info("Search engine state loaded (index size=%d)", self._index.size)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _index_chunks(self, chunks: list[Chunk]) -> int:
        """Embed and index a batch of chunks."""
        texts = [c.text for c in chunks]
        metas = [c.metadata for c in chunks]

        # Always add chunks to the store for text retrieval
        self._chunk_store.extend(chunks)

        # For TF-IDF: accumulate corpus and refit
        if self._embedder.backend == "tfidf":
            self._corpus_texts.extend(texts)
            if self._needs_refit or not self._embedder.is_fitted:
                self._embedder.fit(self._corpus_texts)
                self._needs_refit = False
                # Rebuild entire index with new vocabulary
                return self._rebuild_index()

        embeddings = self._embedder.embed_texts(texts)

        if self._index.size == 0:
            self._index.build_index(embeddings, metas)
        else:
            self._index.add_to_index(embeddings, metas)

        log.info("Indexed %d chunks (total=%d)", len(chunks), self._index.size)
        return len(chunks)

    def _rebuild_index(self) -> int:
        """Rebuild the full index after TF-IDF vocabulary change."""
        if not self._corpus_texts:
            return 0

        all_texts = self._corpus_texts
        embeddings = self._embedder.embed_texts(all_texts)

        # Reconstruct metadata from chunk store
        # (chunk_store may not cover corpus_texts 1:1 after refits, so we
        # rebuild from scratch)
        metas = [c.metadata for c in self._chunk_store]
        # Pad if corpus grew beyond chunk_store (shouldn't normally happen)
        while len(metas) < len(all_texts):
            metas.append({})

        self._index.build_index(embeddings[:len(metas)], metas[:embeddings.shape[0]])
        log.info("Index rebuilt after TF-IDF refit (%d vectors)", self._index.size)
        return self._index.size
