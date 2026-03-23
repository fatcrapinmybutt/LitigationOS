#!/usr/bin/env python3
"""
LitigationOS Hybrid Search Engine — FTS5 + sqlite-vec Vector Search
====================================================================
Combines keyword-based FTS5 search with semantic vector search using
Reciprocal Rank Fusion (RRF) for superior litigation document retrieval.

Usage:
    python hybrid_search_engine.py                    # Build index + run demo queries
    python hybrid_search_engine.py --build-only       # Build/rebuild vector index only
    python hybrid_search_engine.py --search "query"   # Run a single hybrid search
    python hybrid_search_engine.py --status           # Show index statistics

Requirements:
    - sqlite-vec (pip install sqlite-vec)
    - sentence-transformers (pip install sentence-transformers)
    - Model: all-MiniLM-L6-v2 (384-dim, auto-downloaded on first run)

Author: LitigationOS Pipeline
"""

import sys
import os

# UTF-8 stdout (mandatory for LitigationOS)
sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")

import argparse
import json
import sqlite3
import struct
import time
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DB_PATH = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")
MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
MAX_RECORDS = 10_000  # cap for initial index build
BATCH_SIZE = 256

# Tables to vectorize, ordered by priority. Each entry:
#   (table_name, text_column, id_column_or_rowid, max_rows_from_this_table)
SOURCE_TABLES = [
    ("evidence_quotes", "quote_text", "rowid", 4000),
    ("master_evidence_timeline", "description", "rowid", 3000),
    ("narrative_context", "content", "rowid", 1500),
    ("judicial_violations", "description", "rowid", 1000),
    ("critical_facts", "fact_text", "rowid", 500),
    ("police_reports", "full_text", "rowid", 356),
]

# FTS tables available for keyword search (table_name, match_column)
FTS_SOURCES = [
    ("evidence_fts", "evidence_fts"),
    ("timeline_fts", "timeline_fts"),
]

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------


def open_db(readonly: bool = False) -> sqlite3.Connection:
    """Open litigation_context.db with LitigationOS-standard PRAGMAs."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")
    uri = f"file:{DB_PATH}?mode=ro" if readonly else str(DB_PATH)
    if readonly:
        db = sqlite3.connect(uri, uri=True)
    else:
        db = sqlite3.connect(str(DB_PATH))
    db.execute("PRAGMA busy_timeout = 60000")
    db.execute("PRAGMA journal_mode = WAL")
    db.execute("PRAGMA cache_size = -32000")
    db.execute("PRAGMA temp_store = MEMORY")
    db.execute("PRAGMA synchronous = NORMAL")
    return db


def table_exists(db: sqlite3.Connection, name: str) -> bool:
    row = db.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row[0] > 0


def column_exists(db: sqlite3.Connection, table: str, column: str) -> bool:
    cols = db.execute(f"PRAGMA table_info({table})").fetchall()
    return any(c[1] == column for c in cols)


def load_sqlite_vec(db: sqlite3.Connection) -> None:
    """Load the sqlite-vec extension into the connection."""
    import sqlite_vec

    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.enable_load_extension(False)


# ---------------------------------------------------------------------------
# Embedding helpers
# ---------------------------------------------------------------------------

_model = None


def get_model():
    """Lazy-load sentence-transformers model."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        print(f"[model] Loading {MODEL_NAME} ...")
        _model = SentenceTransformer(MODEL_NAME)
        print(f"[model] Loaded. Embedding dim = {_model.get_sentence_embedding_dimension()}")
    return _model


def encode_texts(texts: list[str], batch_size: int = BATCH_SIZE):
    """Encode a list of texts into float32 numpy arrays."""
    model = get_model()
    import numpy as np

    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=True,
    )
    return embeddings.astype(np.float32)


def serialize_f32(vector) -> bytes:
    """Serialize a float32 numpy array to bytes for sqlite-vec."""
    import numpy as np

    return vector.astype(np.float32).tobytes()


# ---------------------------------------------------------------------------
# Index building
# ---------------------------------------------------------------------------


def create_vec_table(db: sqlite3.Connection) -> None:
    """Create the vec_evidence virtual table if it doesn't exist."""
    db.execute("DROP TABLE IF EXISTS vec_evidence")
    db.execute(
        """
        CREATE VIRTUAL TABLE vec_evidence USING vec0(
            embedding float[384],
            +source_table TEXT,
            +source_id TEXT,
            +content_preview TEXT
        )
        """
    )
    print("[index] Created vec_evidence virtual table (384-dim float vectors)")


def create_metadata_table(db: sqlite3.Connection) -> None:
    """Create a metadata table to track what's been indexed."""
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS vec_evidence_meta (
            source_table TEXT,
            source_id TEXT,
            indexed_at TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (source_table, source_id)
        )
        """
    )


def gather_texts(db: sqlite3.Connection) -> list[dict]:
    """Gather text records from all source tables, respecting per-table caps."""
    records = []
    for tbl, col, id_col, max_rows in SOURCE_TABLES:
        if not table_exists(db, tbl):
            print(f"[gather] SKIP {tbl} — table not found")
            continue
        if not column_exists(db, tbl, col):
            print(f"[gather] SKIP {tbl}.{col} — column not found")
            continue

        # Build query — prefer non-null, non-empty text, ordered by rowid
        query = f"""
            SELECT {id_col}, {col}
            FROM {tbl}
            WHERE {col} IS NOT NULL AND TRIM({col}) != ''
            ORDER BY {id_col}
            LIMIT ?
        """
        try:
            rows = db.execute(query, (max_rows,)).fetchall()
        except Exception as e:
            print(f"[gather] ERROR reading {tbl}: {e}")
            continue

        for row_id, text in rows:
            text_str = str(text).strip()
            if len(text_str) < 10:
                continue
            records.append(
                {
                    "source_table": tbl,
                    "source_id": str(row_id),
                    "text": text_str[:2000],  # cap at 2000 chars for embedding
                    "preview": text_str[:200],
                }
            )
        print(f"[gather] {tbl}.{col}: {len(rows)} rows read, {sum(1 for r in records if r['source_table'] == tbl)} usable")

    # Enforce global cap
    if len(records) > MAX_RECORDS:
        print(f"[gather] Capping from {len(records)} to {MAX_RECORDS} records")
        records = records[:MAX_RECORDS]

    print(f"[gather] Total records to embed: {len(records)}")
    return records


def build_index(db: sqlite3.Connection) -> int:
    """Build the vector index from scratch. Returns count of indexed records."""
    load_sqlite_vec(db)
    create_vec_table(db)
    create_metadata_table(db)

    records = gather_texts(db)
    if not records:
        print("[index] No records to index!")
        return 0

    texts = [r["text"] for r in records]
    print(f"[index] Generating embeddings for {len(texts)} texts ...")
    t0 = time.time()
    embeddings = encode_texts(texts)
    elapsed = time.time() - t0
    print(f"[index] Embeddings generated in {elapsed:.1f}s ({len(texts)/elapsed:.0f} texts/sec)")

    # Insert into vec_evidence in batches
    print("[index] Inserting into vec_evidence ...")
    batch = []
    meta_batch = []
    for i, (rec, emb) in enumerate(zip(records, embeddings)):
        batch.append((serialize_f32(emb), rec["source_table"], rec["source_id"], rec["preview"]))
        meta_batch.append((rec["source_table"], rec["source_id"]))
        if len(batch) >= 500:
            db.executemany(
                "INSERT INTO vec_evidence (embedding, source_table, source_id, content_preview) VALUES (?, ?, ?, ?)",
                batch,
            )
            db.executemany(
                "INSERT OR IGNORE INTO vec_evidence_meta (source_table, source_id) VALUES (?, ?)",
                meta_batch,
            )
            db.commit()
            batch.clear()
            meta_batch.clear()
            print(f"  ... {i + 1}/{len(records)} inserted")

    if batch:
        db.executemany(
            "INSERT INTO vec_evidence (embedding, source_table, source_id, content_preview) VALUES (?, ?, ?, ?)",
            batch,
        )
        db.executemany(
            "INSERT OR IGNORE INTO vec_evidence_meta (source_table, source_id) VALUES (?, ?)",
            meta_batch,
        )
        db.commit()

    count = db.execute("SELECT COUNT(*) FROM vec_evidence").fetchone()[0]
    print(f"[index] ✅ Index built: {count} vectors in vec_evidence")
    return count


# ---------------------------------------------------------------------------
# Search functions
# ---------------------------------------------------------------------------


def fts_search(db: sqlite3.Connection, query: str, k: int = 20) -> list[dict]:
    """Run FTS5 keyword search across available FTS tables."""
    results = []
    for fts_table, match_col in FTS_SOURCES:
        if not table_exists(db, fts_table):
            continue
        try:
            # Get column names to find the best text column
            cols = db.execute(f"PRAGMA table_info({fts_table})").fetchall()
            col_names = [c[1] for c in cols]

            # Pick the best content column
            text_col = None
            for candidate in ["quote_text", "content", "description", "text", "full_text"]:
                if candidate in col_names:
                    text_col = candidate
                    break
            if text_col is None and col_names:
                text_col = col_names[0]

            # Sanitize query for FTS5 — wrap each word in quotes for safety
            safe_tokens = []
            for word in query.split():
                clean = "".join(c for c in word if c.isalnum() or c in "-_'")
                if clean:
                    safe_tokens.append(f'"{clean}"')
            if not safe_tokens:
                continue
            # Use OR to be inclusive
            fts_query = " OR ".join(safe_tokens)

            rows = db.execute(
                f"""
                SELECT rowid, {text_col}, rank
                FROM {fts_table}
                WHERE {match_col} MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (fts_query, k),
            ).fetchall()

            for rowid, text, rank in rows:
                results.append(
                    {
                        "rowid": rowid,
                        "source": fts_table,
                        "text": str(text)[:200] if text else "",
                        "score": -rank if rank else 0,
                        "method": "fts5",
                    }
                )
        except Exception as e:
            print(f"[fts] Warning: {fts_table} search failed: {e}")
            continue

    # Sort by score descending, take top k
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:k]


def vector_search(db: sqlite3.Connection, query: str, k: int = 20) -> list[dict]:
    """Run semantic vector search against vec_evidence."""
    if not table_exists(db, "vec_evidence"):
        print("[vec] vec_evidence table not found — run --build-only first")
        return []

    model = get_model()
    import numpy as np

    query_emb = model.encode([query], normalize_embeddings=True)[0].astype(np.float32)

    rows = db.execute(
        """
        SELECT rowid, distance, source_table, source_id, content_preview
        FROM vec_evidence
        WHERE embedding MATCH ?
        AND k = ?
        """,
        (serialize_f32(query_emb), k),
    ).fetchall()

    results = []
    for rowid, distance, src_table, src_id, preview in rows:
        results.append(
            {
                "rowid": rowid,
                "source": f"{src_table}:{src_id}",
                "text": str(preview)[:200] if preview else "",
                "score": 1.0 - distance,  # cosine similarity (normalized vectors)
                "distance": distance,
                "method": "vector",
            }
        )
    return results


def hybrid_search(
    db: sqlite3.Connection, query: str, k: int = 20, rrf_k: int = 60
) -> list[dict]:
    """
    Hybrid search using Reciprocal Rank Fusion (RRF).

    Combines FTS5 keyword results and vector semantic results.
    RRF score = sum(1 / (rrf_k + rank)) across both result lists.
    """
    fts_results = fts_search(db, query, k=k * 2)
    vec_results = vector_search(db, query, k=k * 2)

    # Build RRF score map keyed by a unique identifier
    scores: dict[str, dict] = {}

    for rank, result in enumerate(fts_results):
        uid = f"fts:{result['source']}:{result['rowid']}"
        if uid not in scores:
            scores[uid] = {
                "uid": uid,
                "text": result["text"],
                "source": result["source"],
                "rrf_score": 0.0,
                "fts_rank": None,
                "vec_rank": None,
                "methods": [],
            }
        scores[uid]["rrf_score"] += 1.0 / (rrf_k + rank)
        scores[uid]["fts_rank"] = rank + 1
        scores[uid]["methods"].append("fts5")

    for rank, result in enumerate(vec_results):
        uid = f"vec:{result['source']}:{result['rowid']}"
        if uid not in scores:
            scores[uid] = {
                "uid": uid,
                "text": result["text"],
                "source": result["source"],
                "rrf_score": 0.0,
                "fts_rank": None,
                "vec_rank": None,
                "methods": [],
            }
        scores[uid]["rrf_score"] += 1.0 / (rrf_k + rank)
        scores[uid]["vec_rank"] = rank + 1
        scores[uid]["methods"].append("vector")

    # Sort by RRF score descending
    ranked = sorted(scores.values(), key=lambda x: x["rrf_score"], reverse=True)
    return ranked[:k]


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------


def print_results(label: str, results: list[dict], max_show: int = 10) -> None:
    """Pretty-print search results."""
    print(f"\n{'='*70}")
    print(f"  {label} — {len(results)} results")
    print(f"{'='*70}")
    for i, r in enumerate(results[:max_show]):
        text_preview = r.get("text", "")[:100].replace("\n", " ")
        methods = ", ".join(r.get("methods", [r.get("method", "?")]))
        score_str = ""
        if "rrf_score" in r:
            score_str = f"RRF={r['rrf_score']:.4f}"
            if r.get("fts_rank"):
                score_str += f" fts#{r['fts_rank']}"
            if r.get("vec_rank"):
                score_str += f" vec#{r['vec_rank']}"
        elif "score" in r:
            score_str = f"score={r['score']:.4f}"
        if "distance" in r:
            score_str += f" dist={r['distance']:.4f}"

        source = r.get("source", "?")
        print(f"  [{i+1:2d}] [{methods:>7s}] {score_str}")
        print(f"       src={source}")
        print(f"       {text_preview}")
    if len(results) > max_show:
        print(f"  ... and {len(results) - max_show} more")


def show_status(db: sqlite3.Connection) -> None:
    """Show current index statistics."""
    load_sqlite_vec(db)
    print("\n" + "=" * 60)
    print("  HYBRID SEARCH ENGINE — STATUS")
    print("=" * 60)

    if table_exists(db, "vec_evidence"):
        count = db.execute("SELECT COUNT(*) FROM vec_evidence").fetchone()[0]
        print(f"  vec_evidence vectors:  {count:,}")
    else:
        print("  vec_evidence:          NOT BUILT (run --build-only)")

    if table_exists(db, "vec_evidence_meta"):
        meta_count = db.execute("SELECT COUNT(*) FROM vec_evidence_meta").fetchone()[0]
        by_table = db.execute(
            "SELECT source_table, COUNT(*) FROM vec_evidence_meta GROUP BY source_table ORDER BY COUNT(*) DESC"
        ).fetchall()
        print(f"  Indexed records:       {meta_count:,}")
        for tbl, cnt in by_table:
            print(f"    {tbl:35s} {cnt:>6,}")

    for fts_table, _ in FTS_SOURCES:
        if table_exists(db, fts_table):
            cnt = db.execute(f"SELECT COUNT(*) FROM {fts_table}").fetchone()[0]
            print(f"  {fts_table:23s} {cnt:>8,} rows")
        else:
            print(f"  {fts_table:23s} NOT FOUND")

    print("=" * 60)


# ---------------------------------------------------------------------------
# Demo queries
# ---------------------------------------------------------------------------

DEMO_QUERIES = [
    "parenting time interference",
    "ex parte order without notice",
    "Albert Watson false report",
    "PPO investigation zero charges",
    "contempt incarceration without counsel",
]


def run_demo(db: sqlite3.Connection) -> None:
    """Run demo queries showing FTS-only, vector-only, and hybrid results."""
    load_sqlite_vec(db)

    for query in DEMO_QUERIES:
        print(f"\n{'#'*70}")
        print(f"  QUERY: \"{query}\"")
        print(f"{'#'*70}")

        # FTS5-only
        fts_res = fts_search(db, query, k=10)
        print_results("FTS5 Keyword Search", fts_res, max_show=5)

        # Vector-only
        vec_res = vector_search(db, query, k=10)
        print_results("Vector Semantic Search", vec_res, max_show=5)

        # Hybrid RRF
        hybrid_res = hybrid_search(db, query, k=10)
        print_results("HYBRID (RRF Fusion)", hybrid_res, max_show=5)

        # Summary
        fts_only = sum(1 for r in hybrid_res if r.get("fts_rank") and not r.get("vec_rank"))
        vec_only = sum(1 for r in hybrid_res if r.get("vec_rank") and not r.get("fts_rank"))
        both = sum(1 for r in hybrid_res if r.get("fts_rank") and r.get("vec_rank"))
        print(f"\n  FUSION SUMMARY: {both} found by both | {fts_only} FTS-only | {vec_only} vector-only")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="LitigationOS Hybrid Search Engine — FTS5 + Vector (sqlite-vec)"
    )
    parser.add_argument("--build-only", action="store_true", help="Build/rebuild vector index only")
    parser.add_argument("--search", type=str, help="Run a single hybrid search query")
    parser.add_argument("--status", action="store_true", help="Show index statistics")
    parser.add_argument("--k", type=int, default=20, help="Number of results (default: 20)")
    args = parser.parse_args()

    if args.status:
        db = open_db(readonly=True)
        show_status(db)
        db.close()
        return

    if args.build_only:
        db = open_db(readonly=False)
        t0 = time.time()
        count = build_index(db)
        elapsed = time.time() - t0
        print(f"\n✅ Index build complete: {count:,} vectors in {elapsed:.1f}s")
        show_status(db)
        db.close()
        return

    if args.search:
        db = open_db(readonly=True)
        load_sqlite_vec(db)
        # Ensure model is loaded
        get_model()

        print(f"\nQuery: \"{args.search}\"")
        results = hybrid_search(db, args.search, k=args.k)
        print_results("HYBRID SEARCH RESULTS", results, max_show=args.k)
        db.close()
        return

    # Default: build index (if needed) + run demo
    db = open_db(readonly=False)

    # Check if index exists
    load_sqlite_vec(db)
    needs_build = True
    if table_exists(db, "vec_evidence"):
        count = db.execute("SELECT COUNT(*) FROM vec_evidence").fetchone()[0]
        if count > 0:
            print(f"[init] Existing index found with {count:,} vectors — skipping rebuild")
            print(f"[init] Use --build-only to force rebuild")
            needs_build = False

    if needs_build:
        t0 = time.time()
        count = build_index(db)
        elapsed = time.time() - t0
        print(f"\n✅ Index build complete: {count:,} vectors in {elapsed:.1f}s")

    show_status(db)
    run_demo(db)
    db.close()


if __name__ == "__main__":
    main()
