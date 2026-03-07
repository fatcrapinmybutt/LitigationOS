#!/usr/bin/env python3
"""
semantic_search.py — Vector Semantic Search for LitigationOS Evidence
=====================================================================

Hybrid search engine combining BM25 (FTS5) keyword search with cosine
similarity (sqlite-vec) for the evidence_quotes table (~308K rows).

Usage:
    python semantic_search.py build                          # Build/resume index
    python semantic_search.py search "query text"            # Hybrid search (default)
    python semantic_search.py search --method bm25 "query"   # BM25-only
    python semantic_search.py search --method semantic "q"    # Semantic-only
    python semantic_search.py search --top-k 50 "query"      # Top 50 results
    python semantic_search.py stats                          # Index statistics

Architecture:
    evidence_quotes (308K rows)
        ├── evidence_quotes_fts  (FTS5 — BM25 keyword search)
        └── evidence_embeddings  (vec0 — 384-dim cosine similarity)

    Hybrid = Reciprocal Rank Fusion(BM25, Semantic)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sqlite3
import struct
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Optional

# UTF-8 stdout (Windows safety — prevents UnicodeEncodeError)
if sys.stdout and hasattr(sys.stdout, 'fileno'):
    try:
        sys.stdout = open(
            sys.stdout.fileno(), mode='w', encoding='utf-8',
            errors='replace', closefd=False,
        )
    except (OSError, ValueError):
        pass

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_DB_PATH = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")
DEFAULT_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
BATCH_SIZE = 1000
ENCODE_BATCH_SIZE = 256
MAX_RETRIES = 5
RETRY_BASE_DELAY = 2.0  # seconds, exponential backoff

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)
log = logging.getLogger("semantic_search")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def serialize_f32(vec: list[float]) -> bytes:
    """Pack a float32 vector into little-endian bytes for sqlite-vec."""
    return struct.pack(f"<{len(vec)}f", *vec)


def _apply_pragmas(conn: sqlite3.Connection) -> None:
    """Apply performance PRAGMAs required by LitigationOS."""
    conn.execute("PRAGMA busy_timeout = 180000;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA mmap_size = 12884901888;")   # 12 GB
    conn.execute("PRAGMA cache_size = -131072;")       # 128 MB
    conn.execute("PRAGMA temp_store = MEMORY;")
    conn.execute("PRAGMA synchronous = NORMAL;")


def _retry_on_busy(fn: Callable, *args, max_retries: int = MAX_RETRIES, **kwargs) -> Any:
    """Retry a callable on SQLITE_BUSY / SQLITE_LOCKED with exponential backoff."""
    for attempt in range(1, max_retries + 1):
        try:
            return fn(*args, **kwargs)
        except sqlite3.OperationalError as exc:
            msg = str(exc).lower()
            if ("busy" in msg or "locked" in msg) and attempt < max_retries:
                delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                log.warning("DB busy (attempt %d/%d) — retrying in %.1fs", attempt, max_retries, delay)
                time.sleep(delay)
            else:
                raise


@contextmanager
def _connect(db_path: Path):
    """Open a connection with LitigationOS PRAGMAs and sqlite-vec loaded."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    _apply_pragmas(conn)
    try:
        conn.enable_load_extension(True)
        import sqlite_vec
        sqlite_vec.load(conn)
    except Exception as exc:
        conn.close()
        raise RuntimeError(
            f"Failed to load sqlite-vec extension: {exc}\n"
            "Install with:  pip install sqlite-vec"
        ) from exc
    try:
        yield conn
    finally:
        try:
            conn.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# SemanticSearchEngine
# ---------------------------------------------------------------------------

class SemanticSearchEngine:
    """Hybrid BM25 + vector semantic search over evidence_quotes."""

    def __init__(
        self,
        db_path: str | Path = DEFAULT_DB_PATH,
        model_name: str = DEFAULT_MODEL,
    ):
        self.db_path = Path(db_path)
        self.model_name = model_name
        self._model = None  # lazy-loaded

        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")

        # Ensure the vec0 virtual table exists
        with _connect(self.db_path) as conn:
            conn.execute(f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS evidence_embeddings USING vec0(
                    quote_id INTEGER PRIMARY KEY,
                    embedding FLOAT[{EMBEDDING_DIM}]
                );
            """)
            conn.commit()
            log.info("evidence_embeddings table ready (vec0, %d dims)", EMBEDDING_DIM)

    # ------------------------------------------------------------------
    # Model loading (lazy)
    # ------------------------------------------------------------------

    @property
    def model(self):
        """Lazy-load the sentence-transformers model on first use."""
        if self._model is None:
            log.info("Loading model '%s' …", self.model_name)
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            log.info("Model loaded — embedding dim = %d", self._model.get_sentence_embedding_dimension())
        return self._model

    # ------------------------------------------------------------------
    # Index building
    # ------------------------------------------------------------------

    def build_index(
        self,
        batch_size: int = BATCH_SIZE,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> dict:
        """
        Generate embeddings for all evidence_quotes and store in vec0.

        Resumes automatically — rows already in evidence_embeddings are skipped.
        Returns a stats dict: {total, indexed, skipped, elapsed_sec}.
        """
        t0 = time.perf_counter()
        stats = {"total": 0, "indexed": 0, "skipped": 0, "errors": 0}

        with _connect(self.db_path) as conn:
            # Total rows in evidence_quotes
            total = conn.execute("SELECT COUNT(*) FROM evidence_quotes").fetchone()[0]
            stats["total"] = total

            # Already-indexed count
            already = conn.execute("SELECT COUNT(*) FROM evidence_embeddings").fetchone()[0]
            stats["skipped"] = already

            if already >= total:
                log.info("Index is complete (%d/%d). Nothing to do.", already, total)
                stats["elapsed_sec"] = round(time.perf_counter() - t0, 2)
                return stats

            log.info(
                "Building index: %d total, %d already indexed, ~%d remaining",
                total, already, total - already,
            )

            # Fetch un-indexed rows in batches via LEFT JOIN
            offset = 0
            while True:
                rows = conn.execute(
                    """
                    SELECT eq.id, eq.quote_text
                    FROM evidence_quotes eq
                    LEFT JOIN evidence_embeddings ee ON ee.quote_id = eq.id
                    WHERE ee.quote_id IS NULL
                    ORDER BY eq.id
                    LIMIT ?
                    """,
                    (batch_size,),
                ).fetchall()

                if not rows:
                    break

                ids = [r["id"] for r in rows]
                texts = [r["quote_text"] or "" for r in rows]

                # Encode
                try:
                    embeddings = self.model.encode(
                        texts,
                        batch_size=ENCODE_BATCH_SIZE,
                        show_progress_bar=False,
                        normalize_embeddings=True,
                    )
                except Exception as exc:
                    log.error("Encoding error on batch starting at id=%d: %s", ids[0], exc)
                    stats["errors"] += len(ids)
                    continue

                # Insert into vec0
                insert_data = [
                    (qid, serialize_f32(emb.tolist()))
                    for qid, emb in zip(ids, embeddings)
                ]

                def _do_insert(data=insert_data):
                    conn.executemany(
                        "INSERT INTO evidence_embeddings (quote_id, embedding) VALUES (?, ?)",
                        data,
                    )
                    conn.commit()

                _retry_on_busy(_do_insert)
                stats["indexed"] += len(ids)

                done = stats["indexed"] + stats["skipped"]
                if progress_callback:
                    progress_callback(done, total)
                else:
                    pct = done / total * 100 if total else 0
                    log.info(
                        "Progress: %d / %d (%.1f%%) — batch of %d encoded",
                        done, total, pct, len(ids),
                    )

                offset += len(ids)

        stats["elapsed_sec"] = round(time.perf_counter() - t0, 2)
        log.info(
            "Build complete: %d indexed, %d skipped, %d errors in %.1fs",
            stats["indexed"], stats["skipped"], stats["errors"], stats["elapsed_sec"],
        )
        return stats

    # ------------------------------------------------------------------
    # Search: unified entry point
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        top_k: int = 20,
        method: str = "hybrid",
        alpha: float = 0.6,
    ) -> list[dict]:
        """
        Search evidence_quotes.

        Args:
            query:  Natural-language search query.
            top_k:  Number of results to return.
            method: 'hybrid' | 'semantic' | 'bm25'.
            alpha:  Weight for semantic score in hybrid (0.0–1.0).

        Returns:
            List of dicts with keys:
              quote_id, quote_text, score, document_id, page_number,
              evidence_category, quote_type, speaker, date_ref,
              legal_significance, source_type
        """
        if method == "bm25":
            return self._search_bm25(query, top_k)
        elif method == "semantic":
            return self._search_semantic(query, top_k)
        elif method == "hybrid":
            return self.hybrid_search(query, top_k, alpha)
        else:
            raise ValueError(f"Unknown search method: {method!r} — use 'hybrid', 'bm25', or 'semantic'")

    # ------------------------------------------------------------------
    # BM25 search (FTS5)
    # ------------------------------------------------------------------

    def _search_bm25(self, query: str, top_k: int = 20) -> list[dict]:
        """Pure BM25 keyword search via evidence_quotes_fts."""
        fts_query = self._sanitize_fts_query(query)
        with _connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT
                    eq.id           AS quote_id,
                    eq.quote_text,
                    eq.document_id,
                    eq.page_number,
                    eq.evidence_category,
                    eq.quote_type,
                    eq.speaker,
                    eq.date_ref,
                    eq.legal_significance,
                    eq.source_type,
                    bm25(evidence_quotes_fts) AS bm25_score
                FROM evidence_quotes_fts fts
                JOIN evidence_quotes eq ON eq.id = fts.rowid
                WHERE evidence_quotes_fts MATCH ?
                ORDER BY bm25(evidence_quotes_fts)
                LIMIT ?
                """,
                (fts_query, top_k),
            ).fetchall()
            return [self._row_to_dict(r, score_key="bm25_score") for r in rows]

    # ------------------------------------------------------------------
    # Semantic search (sqlite-vec KNN)
    # ------------------------------------------------------------------

    def _search_semantic(self, query: str, top_k: int = 20) -> list[dict]:
        """Pure cosine-similarity search via sqlite-vec."""
        query_emb = self.model.encode(
            [query], normalize_embeddings=True,
        )[0]
        query_bytes = serialize_f32(query_emb.tolist())

        with _connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT
                    ee.quote_id,
                    ee.distance,
                    eq.quote_text,
                    eq.document_id,
                    eq.page_number,
                    eq.evidence_category,
                    eq.quote_type,
                    eq.speaker,
                    eq.date_ref,
                    eq.legal_significance,
                    eq.source_type
                FROM evidence_embeddings ee
                JOIN evidence_quotes eq ON eq.id = ee.quote_id
                WHERE ee.embedding MATCH ?
                    AND k = ?
                ORDER BY ee.distance
                """,
                (query_bytes, top_k),
            ).fetchall()

            results = []
            for r in rows:
                d = self._row_to_dict(r)
                # sqlite-vec returns L2 distance; convert to similarity score
                d["score"] = round(1.0 - float(r["distance"]), 6)
                results.append(d)
            return results

    # ------------------------------------------------------------------
    # Hybrid search (Reciprocal Rank Fusion)
    # ------------------------------------------------------------------

    def hybrid_search(
        self,
        query: str,
        top_k: int = 20,
        alpha: float = 0.6,
    ) -> list[dict]:
        """
        Reciprocal Rank Fusion of BM25 + semantic search.

        alpha = weight for semantic component (0.6 = 60% semantic, 40% BM25).
        RRF score = alpha / (k + sem_rank) + (1-alpha) / (k + bm25_rank)
        where k = 60 (standard RRF constant).
        """
        k_rrf = 60  # standard RRF smoothing constant

        # Fetch more candidates than top_k to improve fusion quality
        fetch_k = min(top_k * 3, 200)

        sem_results = self._search_semantic(query, fetch_k)
        bm25_results = self._search_bm25(query, fetch_k)

        # Build rank maps: quote_id → rank (1-based)
        sem_ranks: dict[int, int] = {}
        for rank, r in enumerate(sem_results, 1):
            sem_ranks[r["quote_id"]] = rank

        bm25_ranks: dict[int, int] = {}
        for rank, r in enumerate(bm25_results, 1):
            bm25_ranks[r["quote_id"]] = rank

        # Collect all candidate IDs
        all_ids = set(sem_ranks.keys()) | set(bm25_ranks.keys())

        # Build detail lookup from both result sets
        detail_map: dict[int, dict] = {}
        for r in sem_results:
            detail_map[r["quote_id"]] = r
        for r in bm25_results:
            if r["quote_id"] not in detail_map:
                detail_map[r["quote_id"]] = r

        # Compute RRF scores
        scored: list[tuple[int, float]] = []
        absent_rank = fetch_k + 50  # penalty rank for items missing from one list

        for qid in all_ids:
            sem_r = sem_ranks.get(qid, absent_rank)
            bm25_r = bm25_ranks.get(qid, absent_rank)
            rrf = alpha / (k_rrf + sem_r) + (1 - alpha) / (k_rrf + bm25_r)
            scored.append((qid, rrf))

        scored.sort(key=lambda x: x[1], reverse=True)

        results = []
        for qid, rrf_score in scored[:top_k]:
            entry = detail_map[qid].copy()
            entry["score"] = round(rrf_score, 6)
            entry["_rrf_detail"] = {
                "semantic_rank": sem_ranks.get(qid),
                "bm25_rank": bm25_ranks.get(qid),
            }
            results.append(entry)

        return results

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> dict:
        """Return index statistics."""
        with _connect(self.db_path) as conn:
            total_quotes = conn.execute("SELECT COUNT(*) FROM evidence_quotes").fetchone()[0]
            indexed = conn.execute("SELECT COUNT(*) FROM evidence_embeddings").fetchone()[0]
            return {
                "total_quotes": total_quotes,
                "indexed_embeddings": indexed,
                "coverage_pct": round(indexed / total_quotes * 100, 2) if total_quotes else 0,
                "embedding_dim": EMBEDDING_DIM,
                "model": self.model_name,
                "db_path": str(self.db_path),
                "db_size_gb": round(self.db_path.stat().st_size / (1024**3), 2),
            }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _sanitize_fts_query(query: str) -> str:
        """
        Sanitize a user query for FTS5 MATCH.

        Wraps each token in double-quotes to prevent FTS5 syntax errors from
        special characters, then joins with implicit AND.
        """
        tokens = query.split()
        if not tokens:
            return '""'
        safe_tokens = ['"' + t.replace('"', '""') + '"' for t in tokens]
        return " ".join(safe_tokens)

    @staticmethod
    def _row_to_dict(row: sqlite3.Row, score_key: str | None = None) -> dict:
        """Convert a sqlite3.Row to a result dict."""
        d = {
            "quote_id": row["quote_id"],
            "quote_text": row["quote_text"],
            "document_id": row["document_id"],
            "page_number": row["page_number"],
            "evidence_category": row["evidence_category"],
            "quote_type": row["quote_type"],
            "speaker": row["speaker"],
            "date_ref": row["date_ref"],
            "legal_significance": row["legal_significance"],
            "source_type": row["source_type"],
        }
        if score_key and score_key in row.keys():
            d["score"] = round(float(row[score_key]), 6)
        return d

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def close(self):
        """Release model memory."""
        self._model = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print_results(results: list[dict], method: str) -> None:
    """Pretty-print search results to stdout."""
    if not results:
        print("  (no results)")
        return
    for i, r in enumerate(results, 1):
        text_preview = (r["quote_text"] or "")[:120].replace("\n", " ")
        print(f"  {i:3d}. [score={r.get('score', 0):.4f}] id={r['quote_id']}"
              f"  cat={r.get('evidence_category', '?')}"
              f"  speaker={r.get('speaker', '?')}")
        print(f"       {text_preview}")
        if r.get("_rrf_detail"):
            det = r["_rrf_detail"]
            print(f"       (semantic_rank={det.get('semantic_rank', '-')}"
                  f", bm25_rank={det.get('bm25_rank', '-')})")
        print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="LitigationOS Semantic Search — hybrid BM25 + vector search over evidence_quotes",
    )
    parser.add_argument(
        "--db", type=str, default=str(DEFAULT_DB_PATH),
        help="Path to litigation_context.db",
    )
    parser.add_argument(
        "--model", type=str, default=DEFAULT_MODEL,
        help=f"Sentence-transformers model name (default: {DEFAULT_MODEL})",
    )

    sub = parser.add_subparsers(dest="command")

    # build
    build_p = sub.add_parser("build", help="Build or resume the embedding index")
    build_p.add_argument("--batch-size", type=int, default=BATCH_SIZE)

    # search
    search_p = sub.add_parser("search", help="Search evidence quotes")
    search_p.add_argument("query", type=str, help="Search query text")
    search_p.add_argument("--method", choices=["hybrid", "bm25", "semantic"], default="hybrid")
    search_p.add_argument("--top-k", type=int, default=20)
    search_p.add_argument("--alpha", type=float, default=0.6,
                          help="Semantic weight in hybrid mode (0.0–1.0, default 0.6)")
    search_p.add_argument("--json", action="store_true", help="Output results as JSON")

    # stats
    sub.add_parser("stats", help="Show index statistics")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    engine = SemanticSearchEngine(db_path=args.db, model_name=args.model)

    if args.command == "build":
        stats = engine.build_index(batch_size=args.batch_size)
        print(json.dumps(stats, indent=2))

    elif args.command == "search":
        t0 = time.perf_counter()
        results = engine.search(
            query=args.query,
            top_k=args.top_k,
            method=args.method,
            alpha=args.alpha,
        )
        elapsed = time.perf_counter() - t0

        if args.json:
            for r in results:
                r.pop("_rrf_detail", None)
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            print(f"\n{'='*72}")
            print(f"  Query:   {args.query}")
            print(f"  Method:  {args.method}  |  top_k={args.top_k}  |  alpha={args.alpha}")
            print(f"  Results: {len(results)}  |  {elapsed:.2f}s")
            print(f"{'='*72}\n")
            _print_results(results, args.method)

    elif args.command == "stats":
        stats = engine.get_stats()
        print(json.dumps(stats, indent=2))

    engine.close()


if __name__ == "__main__":
    main()
