"""Ingestion pipeline — load evidence from DB or filesystem into the search index.

Reads from ``litigation_context.db`` (documents + pages tables) or from
a list of file paths.  Tracks which documents have already been indexed
via the ``evidence_embeddings`` table to support incremental runs.
"""
from __future__ import annotations

import logging
import sqlite3
import struct
from pathlib import Path
from typing import Any

import numpy as np

from .chunker import Chunk, DocumentChunker
from .config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DB_PATH,
    DB_PRAGMAS,
    INGEST_BATCH_SIZE,
    SUPPORTED_EXTENSIONS,
)
from .embedder import EvidenceEmbedder
from .search_engine import SemanticSearchEngine

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SQL
# ---------------------------------------------------------------------------
_CREATE_EMBEDDINGS_TABLE = """
CREATE TABLE IF NOT EXISTS evidence_embeddings (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id   INTEGER,
    chunk_index   INTEGER,
    chunk_text    TEXT,
    embedding     BLOB,
    file_path     TEXT,
    page_number   INTEGER,
    lane          TEXT,
    case_number   TEXT,
    sha256_hash   TEXT,
    created_at    TEXT DEFAULT (datetime('now')),
    UNIQUE(document_id, chunk_index)
);
"""

_INDEXED_HASHES_SQL = "SELECT DISTINCT sha256_hash FROM evidence_embeddings"

_DOCUMENTS_SQL = """
SELECT d.id, d.file_path, d.file_name, d.sha256_hash, d.evidence_category
FROM documents d
WHERE d.sha256_hash IS NOT NULL
ORDER BY d.id
LIMIT ? OFFSET ?
"""

_PAGES_SQL = """
SELECT page_number, text_content
FROM pages
WHERE document_id = ?
ORDER BY page_number
"""

_INSERT_EMBEDDING_SQL = """
INSERT OR IGNORE INTO evidence_embeddings
    (document_id, chunk_index, chunk_text, embedding,
     file_path, page_number, lane, case_number, sha256_hash)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


def _connect(db_path: str | None = None) -> sqlite3.Connection:
    """Open a WAL-mode connection with mandatory PRAGMAs."""
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    for pragma in DB_PRAGMAS:
        conn.execute(pragma)
    return conn


def _embedding_to_blob(vec: np.ndarray) -> bytes:
    """Pack a float32 vector into raw bytes for BLOB storage."""
    return struct.pack(f"{len(vec)}f", *vec.tolist())


def _blob_to_embedding(blob: bytes) -> np.ndarray:
    """Unpack a BLOB back into a float32 numpy array."""
    count = len(blob) // 4
    return np.array(struct.unpack(f"{count}f", blob), dtype=np.float32)


class IngestPipeline:
    """Load evidence into the semantic search index.

    Supports two sources:

    * ``"db"`` — reads from ``litigation_context.db`` (documents + pages).
    * ``"filesystem"`` — reads raw text files from given paths.

    Already-indexed documents (by ``sha256_hash``) are skipped for
    incremental ingestion.
    """

    def __init__(
        self,
        engine: SemanticSearchEngine | None = None,
        db_path: str | None = None,
    ) -> None:
        self._engine = engine or SemanticSearchEngine(force_tfidf=True)
        self._db_path = db_path or DB_PATH
        self._chunker = DocumentChunker(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        self._embedder = EvidenceEmbedder(force_tfidf=True)
        self._stats: dict[str, int] = {
            "documents_processed": 0,
            "documents_skipped": 0,
            "chunks_created": 0,
            "embeddings_stored": 0,
        }

    @property
    def stats(self) -> dict[str, int]:
        return dict(self._stats)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        source: str = "db",
        limit: int | None = None,
        paths: list[str] | None = None,
    ) -> dict[str, int]:
        """Main entry point.

        Parameters
        ----------
        source : str
            ``"db"`` to read from litigation_context.db, ``"filesystem"``
            to read from *paths*.
        limit : int | None
            Max documents to process (useful for testing).
        paths : list[str] | None
            File paths when *source* is ``"filesystem"``.
        """
        self._stats = {k: 0 for k in self._stats}

        if source == "db":
            self.ingest_from_db(limit=limit)
        elif source == "filesystem":
            if not paths:
                raise ValueError("paths required when source='filesystem'")
            self.ingest_from_filesystem(paths, limit=limit)
        else:
            raise ValueError(f"Unknown source: {source!r}")

        log.info("Ingestion complete: %s", self._stats)
        return self.stats

    # ------------------------------------------------------------------
    # DB ingestion
    # ------------------------------------------------------------------

    def ingest_from_db(self, limit: int | None = None) -> None:
        """Read documents + pages from the central DB and index them."""
        conn = _connect(self._db_path)
        try:
            conn.execute(_CREATE_EMBEDDINGS_TABLE)
            conn.commit()

            indexed_hashes = self._get_indexed_hashes(conn)
            log.info("Already indexed: %d unique document hashes", len(indexed_hashes))

            offset = 0
            total = 0
            while True:
                actual_limit = limit - total if limit else INGEST_BATCH_SIZE
                if actual_limit <= 0:
                    break

                rows = conn.execute(
                    _DOCUMENTS_SQL, (min(actual_limit, INGEST_BATCH_SIZE), offset),
                ).fetchall()
                if not rows:
                    break
                offset += len(rows)

                for doc_row in rows:
                    if limit and total >= limit:
                        break

                    sha = doc_row["sha256_hash"]
                    if sha in indexed_hashes:
                        self._stats["documents_skipped"] += 1
                        continue

                    pages = conn.execute(_PAGES_SQL, (doc_row["id"],)).fetchall()
                    if not pages:
                        self._stats["documents_skipped"] += 1
                        continue

                    self._process_document(conn, doc_row, pages)
                    total += 1
                    self._stats["documents_processed"] += 1

                    if total % 100 == 0:
                        log.info("Progress: %d documents processed", total)

                if len(rows) < INGEST_BATCH_SIZE:
                    break

            conn.commit()
        finally:
            conn.close()

    def ingest_from_filesystem(
        self,
        paths: list[str],
        limit: int | None = None,
    ) -> None:
        """Read text files from *paths* and index them."""
        processed = 0
        for p in paths:
            if limit and processed >= limit:
                break

            fp = Path(p)
            if not fp.exists():
                log.warning("File not found: %s", p)
                continue
            if fp.suffix.lower() not in SUPPORTED_EXTENSIONS:
                log.debug("Skipping unsupported extension: %s", fp.suffix)
                continue

            try:
                text = fp.read_text(encoding="utf-8", errors="replace")
            except Exception:
                log.warning("Failed to read %s", p, exc_info=True)
                continue

            if not text.strip():
                continue

            chunks_ingested = self._engine.ingest_document(
                file_path=str(fp),
                text=text,
                metadata={"file_path": str(fp), "file_name": fp.name},
            )
            self._stats["documents_processed"] += 1
            self._stats["chunks_created"] += chunks_ingested
            processed += 1

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_indexed_hashes(self, conn: sqlite3.Connection) -> set[str]:
        """Return sha256 hashes of already-indexed documents."""
        try:
            rows = conn.execute(_INDEXED_HASHES_SQL).fetchall()
            return {r[0] for r in rows if r[0]}
        except sqlite3.OperationalError:
            return set()

    def _process_document(
        self,
        conn: sqlite3.Connection,
        doc_row: sqlite3.Row,
        pages: list[sqlite3.Row],
    ) -> None:
        """Chunk, embed, and store one document's pages."""
        doc_id = doc_row["id"]
        file_path = doc_row["file_path"]
        sha256 = doc_row["sha256_hash"]
        category = doc_row["evidence_category"]

        chunk_idx = 0
        all_chunks: list[Chunk] = []
        all_page_numbers: list[int | None] = []

        for page in pages:
            text = page["text_content"]
            if not text or not text.strip():
                continue

            meta: dict[str, Any] = {
                "file_path": file_path,
                "page_number": page["page_number"],
                "document_id": doc_id,
                "sha256_hash": sha256,
                "evidence_category": category,
            }

            chunks = self._chunker.chunk_text(text, metadata=meta)
            for c in chunks:
                all_chunks.append(c)
                all_page_numbers.append(page["page_number"])

        if not all_chunks:
            return

        # Embed all chunks for this document at once
        texts = [c.text for c in all_chunks]

        # Auto-fit TF-IDF if needed
        if not self._embedder.is_fitted:
            self._embedder.fit(texts)

        embeddings = self._embedder.embed_texts(texts)

        # Ingest into the search engine
        self._engine.ingest_document(
            file_path=file_path,
            text="\n\n".join(texts),
            metadata={
                "file_path": file_path,
                "document_id": doc_id,
                "sha256_hash": sha256,
            },
        )

        # Store in evidence_embeddings table
        rows_to_insert: list[tuple[Any, ...]] = []
        for i, (chunk, page_num) in enumerate(zip(all_chunks, all_page_numbers)):
            emb_blob = _embedding_to_blob(embeddings[i]) if i < len(embeddings) else b""
            rows_to_insert.append((
                doc_id,
                chunk_idx + i,
                chunk.text[:2000],  # truncate very long chunks for DB
                emb_blob,
                file_path,
                page_num,
                chunk.metadata.get("lane"),
                chunk.metadata.get("case_number"),
                sha256,
            ))

        try:
            conn.executemany(_INSERT_EMBEDDING_SQL, rows_to_insert)
            self._stats["chunks_created"] += len(rows_to_insert)
            self._stats["embeddings_stored"] += len(rows_to_insert)
        except sqlite3.Error:
            log.warning("Failed to store embeddings for doc %d", doc_id, exc_info=True)
