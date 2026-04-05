#!/usr/bin/env python3
"""
LitigationOS RAG Engine — Hybrid ChromaDB + FTS5 retrieval with Ollama synthesis.

Usage:
    python litigation_rag_engine.py --ingest          # Index all documents
    python litigation_rag_engine.py --query "question" # Ask a question
    python litigation_rag_engine.py --status           # Show index stats
"""

import argparse
import json
import os
import re
import sqlite3
import sys
import textwrap
import time
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import chromadb
    HAS_CHROMADB = True
except ImportError:
    chromadb = None
    HAS_CHROMADB = False
import requests

# ── shared module import ─────────────────────────────────────────────────────
try:
    _sys_dir = str(Path(__file__).resolve().parent.parent)
    if _sys_dir not in sys.path:
        sys.path.insert(0, _sys_dir)
    from shared import sanitize_fts5 as _shared_sanitize
    _HAS_SHARED_FTS5 = True
except ImportError:
    _HAS_SHARED_FTS5 = False

# ── paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "litigation_context.db"
CHROMA_DIR = BASE_DIR / "00_SYSTEM" / "chroma_db"
COLLECTION_NAME = "litigation_vectors"

OLLAMA_BASE = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "qwen2.5:7b"

CHUNK_SIZE = 1000   # tokens (approx chars / 4)
CHUNK_OVERLAP = 200
VECTOR_WEIGHT = 0.6
FTS_WEIGHT = 0.4
TOP_K = 15

# Priority tables for ingestion (data tables, not FTS shadow tables)
PRIORITY_TABLES = [
    "apex_master_timeline",
    "apex_filing_stack_index",
    "cyclepack_chronodb",
    "cyclepack_statement_index",
    "permafix_r12_contradiction_map",
    "permafix_r12_doc_records",
    "permafix_r12_operating_orders",
    "permafix_r12_quote_db",
    "permafix_r13_authority_anchors",
    "permafix_r13_case_catalog",
    "permafix_r13_contradiction_grid",
    "permafix_r13_quote_db",
    "permafix_r14_case_chronology",
    "permafix_r14_operating_orders",
    "permafix_r14_quote_db",
    "court_filing_bundles",
    "filing_packages",
    "filing_inventory",
    "filing_analysis",
    "court_filing_content_analysis",
    "adversary_assertions",
    "evidence_quotes",
    "master_timeline",
    "prosecution_timeline",
    "constitutional_violations",
    "impeachment_index",
    "rebuttal_matrix",
    "condensed_timeline",
    "actor_violations",
    "extracted_harms",
]

# FTS5 indexes available for hybrid search
FTS_INDEXES = [
    "adversary_assertions_fts",
    "andrew_messages_fts",
    "appclose_messages_fts",
    "appclose_violations_fts",
    "auth_passages_fts",
    "auth_rules_fts",
    "canonical_facts_fts",
    "case_intelligence_hub_fts",
    "caselaw_unified_fts",
    "condensed_timeline_fts",
    "constitutional_violations_fts",
    "evidence_quotes_fts",
    "exhibit_registry_fts",
    "extracted_harms_fts",
    "master_csv_fts",
    "master_timeline_fts",
    "md_sections_fts",
    "ocr_text_fts",
    "pages_fts",
    "prosecution_timeline_fts",
    "psych_analysis_fts",
    "rebuttal_matrix_fts",
    "rules_text_fts",
]


# ── helpers ──────────────────────────────────────────────────────────────────

def ollama_embed(texts: list[str]) -> list[list[float]]:
    """Get embeddings from Ollama nomic-embed-text."""
    embeddings = []
    for text in texts:
        resp = requests.post(
            f"{OLLAMA_BASE}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text},
            timeout=120,
        )
        resp.raise_for_status()
        embeddings.append(resp.json()["embedding"])
    return embeddings


def ollama_generate(prompt: str, system: str = "") -> str:
    """Generate text with Ollama qwen2.5:7b."""
    resp = requests.post(
        f"{OLLAMA_BASE}/api/generate",
        json={
            "model": LLM_MODEL,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {"temperature": 0.3, "num_ctx": 8192},
        },
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()["response"]


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks by approximate token count."""
    # Approximate: 1 token ≈ 4 chars
    char_size = chunk_size * 4
    char_overlap = overlap * 4
    if len(text) <= char_size:
        return [text] if text.strip() else []
    chunks = []
    start = 0
    while start < len(text):
        end = start + char_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start += char_size - char_overlap
    return chunks


def get_chroma_client():
    if not HAS_CHROMADB:
        raise ImportError("chromadb not installed. Run: pip install chromadb")
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def get_collection(client):
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.row_factory = sqlite3.Row
    return conn


# ── ingestion ────────────────────────────────────────────────────────────────

def row_to_text(table: str, row: sqlite3.Row) -> str:
    """Convert a DB row into a searchable text block."""
    keys = row.keys()
    parts = [f"[TABLE: {table}]"]
    for k in keys:
        val = row[k]
        if val is not None and str(val).strip():
            parts.append(f"{k}: {val}")
    return "\n".join(parts)


def ingest_table(collection: chromadb.Collection, conn: sqlite3.Connection, table: str) -> int:
    """Ingest all rows from a table into ChromaDB."""
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT * FROM [{table}]")
    except Exception as e:
        print(f"  ⚠ Skip {table}: {e}")
        return 0

    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    if not rows:
        print(f"  ⏭ {table}: 0 rows")
        return 0

    total_chunks = 0
    batch_ids, batch_docs, batch_metas = [], [], []

    for i, row in enumerate(rows):
        text = row_to_text(table, row)
        chunks = chunk_text(text)

        # Determine row_id from first column or index
        row_id = row[0] if row[0] is not None else i

        for ci, chunk in enumerate(chunks):
            doc_id = f"{table}__r{row_id}__c{ci}"
            batch_ids.append(doc_id)
            batch_docs.append(chunk)
            batch_metas.append({
                "source_table": table,
                "row_id": str(row_id),
                "chunk_index": ci,
                "total_chunks": len(chunks),
            })
            total_chunks += 1

            # Batch embed every 50 chunks
            if len(batch_ids) >= 50:
                _flush_batch(collection, batch_ids, batch_docs, batch_metas)
                batch_ids, batch_docs, batch_metas = [], [], []

    if batch_ids:
        _flush_batch(collection, batch_ids, batch_docs, batch_metas)

    print(f"  ✓ {table}: {len(rows)} rows → {total_chunks} chunks")
    return total_chunks


def _flush_batch(collection, ids, docs, metas):
    """Embed and upsert a batch into ChromaDB."""
    try:
        embeddings = ollama_embed(docs)
        collection.upsert(ids=ids, documents=docs, metadatas=metas, embeddings=embeddings)
    except Exception as e:
        print(f"    ⚠ Batch embed error ({len(ids)} docs): {e}")


def run_ingest():
    """Full ingestion pipeline."""
    print("=" * 60)
    print("LitigationOS RAG Engine — Ingestion")
    print("=" * 60)

    client = get_chroma_client()
    collection = get_collection(client)
    conn = get_db()

    existing = collection.count()
    print(f"\nExisting vectors in collection: {existing}")
    print(f"Tables to index: {len(PRIORITY_TABLES)}\n")

    grand_total = 0
    t0 = time.time()

    for table in PRIORITY_TABLES:
        n = ingest_table(collection, conn, table)
        grand_total += n

    elapsed = time.time() - t0
    conn.close()

    print(f"\n{'=' * 60}")
    print(f"Ingestion complete: {grand_total} chunks indexed in {elapsed:.1f}s")
    print(f"Total vectors now: {collection.count()}")
    print(f"ChromaDB path: {CHROMA_DIR}")


# ── query ────────────────────────────────────────────────────────────────────

def vector_search(collection: chromadb.Collection, query: str, top_k: int = TOP_K) -> list[dict]:
    """Search ChromaDB for relevant chunks."""
    try:
        emb = ollama_embed([query])[0]
    except Exception as e:
        print(f"  ⚠ Embedding error: {e}")
        return []

    results = collection.query(
        query_embeddings=[emb],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    hits = []
    for i in range(len(results["ids"][0])):
        score = 1.0 - results["distances"][0][i]  # cosine similarity
        hits.append({
            "id": results["ids"][0][i],
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "score": score,
            "source": "vector",
        })
    return hits


def fts_search(conn: sqlite3.Connection, query: str, top_k: int = TOP_K) -> list[dict]:
    """Search all FTS5 indexes for the query, with LIKE fallback on failure."""
    # Use shared sanitizer if available (handles legal citations properly)
    if _HAS_SHARED_FTS5:
        clean = _shared_sanitize(query)
    else:
        clean = re.sub(r'[^\w\s*"]', ' ', query)
    terms = [t for t in clean.split() if len(t) >= 2 and t.upper() not in {"AND", "OR", "NOT"}]
    if not terms:
        return []
    fts_query = " OR ".join(terms)

    hits = []
    for fts_table in FTS_INDEXES:
        try:
            cur = conn.cursor()
            cur.execute(
                f"SELECT rowid, rank, * FROM [{fts_table}] "
                f"WHERE [{fts_table}] MATCH ? ORDER BY rank LIMIT ?",
                (fts_query, top_k),
            )
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]

            for row in rows:
                row_dict = dict(zip(columns, row))
                # Build text from all non-system columns
                text_parts = []
                for k, v in row_dict.items():
                    if k not in ("rowid", "rank") and v is not None and str(v).strip():
                        text_parts.append(f"{k}: {v}")
                text = "\n".join(text_parts)

                base_table = fts_table.replace("_fts", "")
                rank_val = row_dict.get("rank", 0)
                # FTS5 rank is negative (lower = better match); normalize
                score = 1.0 / (1.0 + abs(rank_val)) if rank_val else 0.5

                hits.append({
                    "id": f"{fts_table}__row{row_dict.get('rowid', '?')}",
                    "text": text[:4000],
                    "metadata": {"source_table": base_table, "fts_index": fts_table},
                    "score": score,
                    "source": "fts5",
                })
        except Exception:
            # LIKE fallback — query the base table directly
            base_table = fts_table.replace("_fts", "")
            try:
                # Get text columns from base table
                cols_info = conn.execute(f"PRAGMA table_info([{base_table}])").fetchall()
                text_cols = [c[1] for c in cols_info if c[2].upper() in ("TEXT", "")]
                if text_cols:
                    text_col = text_cols[0]
                    like_clauses = " AND ".join([f"[{text_col}] LIKE ?" for _ in terms])
                    like_params = [f"%{t}%" for t in terms]
                    rows = conn.execute(
                        f"SELECT rowid, * FROM [{base_table}] WHERE {like_clauses} LIMIT ?",
                        like_params + [top_k]
                    ).fetchall()
                    columns = [desc[0] for desc in conn.execute(f"SELECT * FROM [{base_table}] LIMIT 0").description]
                    for row in rows:
                        row_dict = dict(zip(["rowid"] + columns, row))
                        text_parts = [f"{k}: {v}" for k, v in row_dict.items()
                                      if k != "rowid" and v is not None and str(v).strip()]
                        hits.append({
                            "id": f"{base_table}__row{row_dict.get('rowid', '?')}",
                            "text": "\n".join(text_parts)[:4000],
                            "metadata": {"source_table": base_table, "fts_index": fts_table},
                            "score": 0.3,  # Lower score for LIKE results
                            "source": "like_fallback",
                        })
            except Exception:
                continue

    # Sort by score descending, take top_k
    hits.sort(key=lambda h: h["score"], reverse=True)
    return hits[:top_k]


def hybrid_merge(vector_hits: list[dict], fts_hits: list[dict]) -> list[dict]:
    """Merge vector and FTS results with weighted scoring."""
    merged = {}

    for hit in vector_hits:
        key = hit["id"]
        merged[key] = {
            **hit,
            "hybrid_score": hit["score"] * VECTOR_WEIGHT,
        }

    for hit in fts_hits:
        key = hit["id"]
        if key in merged:
            merged[key]["hybrid_score"] += hit["score"] * FTS_WEIGHT
        else:
            merged[key] = {
                **hit,
                "hybrid_score": hit["score"] * FTS_WEIGHT,
            }

    results = sorted(merged.values(), key=lambda h: h["hybrid_score"], reverse=True)
    return results


def build_context(results: list[dict], max_ctx: int = 6000) -> tuple[str, list[str]]:
    """Build LLM context from search results. Returns (context_text, source_citations)."""
    context_parts = []
    sources = []
    char_count = 0

    for r in results:
        meta = r.get("metadata", {})
        table = meta.get("source_table", meta.get("fts_index", "unknown"))
        row_id = meta.get("row_id", meta.get("rowid", "?"))
        chunk_id = meta.get("chunk_index", "")
        source_tag = f"[SOURCE: {table}, row={row_id}"
        if chunk_id != "":
            source_tag += f", chunk={chunk_id}"
        source_tag += f", score={r.get('hybrid_score', r.get('score', 0)):.3f}]"

        text = r["text"][:2000]
        block = f"---\n{source_tag}\n{text}\n"

        if char_count + len(block) > max_ctx * 4:
            break
        context_parts.append(block)
        sources.append(source_tag)
        char_count += len(block)

    return "\n".join(context_parts), sources


def run_query(question: str):
    """Full hybrid RAG query pipeline."""
    print(f"\n{'=' * 60}")
    print(f"Query: {question}")
    print("=" * 60)

    client = get_chroma_client()
    collection = get_collection(client)
    conn = get_db()

    # Step 1: Vector search
    print("\n🔍 Vector search (ChromaDB)...")
    t0 = time.time()
    vec_hits = vector_search(collection, question)
    print(f"   Found {len(vec_hits)} results ({time.time() - t0:.2f}s)")

    # Step 2: FTS5 search
    print("🔍 FTS5 search (SQLite)...")
    t0 = time.time()
    fts_hits = fts_search(conn, question)
    print(f"   Found {len(fts_hits)} results ({time.time() - t0:.2f}s)")

    # Step 3: Hybrid merge
    merged = hybrid_merge(vec_hits, fts_hits)
    print(f"📊 Merged: {len(merged)} unique results")

    if not merged:
        print("\n⚠ No results found. Try different search terms.")
        conn.close()
        return

    # Step 4: Build context and generate answer
    context, sources = build_context(merged)

    system_prompt = textwrap.dedent("""\
        You are a litigation research assistant for Pigors v. Watson (Michigan 14th Circuit Court).

        RULES:
        1. Answer using ONLY the provided evidence context — never add outside knowledge
        2. Cite every factual claim as [SOURCE: table_name, row=X]
        3. If the evidence is insufficient, state what is missing — do not guess
        4. Note contradictions between sources explicitly
        5. Never fabricate party names, dates, or statistics not in the context

        FORMAT:
        - Answer the question directly first
        - Follow with SOURCES: list all [SOURCE: ...] citations used
        - End with CONFIDENCE: HIGH / MEDIUM / LOW
    """)

    user_prompt = f"EVIDENCE CONTEXT:\n{context}\n\nQUESTION: {question}\n\nProvide a detailed answer with source citations:"

    print("\n🤖 Generating answer with qwen2.5:7b...")
    t0 = time.time()
    answer = ollama_generate(user_prompt, system=system_prompt)
    gen_time = time.time() - t0

    conn.close()

    # Display results
    print(f"\n{'─' * 60}")
    print("ANSWER:")
    print("─" * 60)
    print(answer)
    print(f"\n{'─' * 60}")
    print(f"SOURCES ({len(sources)}):")
    for s in sources[:10]:
        print(f"  {s}")
    if len(sources) > 10:
        print(f"  ... and {len(sources) - 10} more")
    print(f"\n⏱ Generation: {gen_time:.1f}s")


# ── status ───────────────────────────────────────────────────────────────────

def run_status():
    """Show index statistics."""
    print("=" * 60)
    print("LitigationOS RAG Engine — Status")
    print("=" * 60)

    # ChromaDB stats
    client = get_chroma_client()
    try:
        collection = client.get_collection(COLLECTION_NAME)
        vec_count = collection.count()
    except Exception:
        vec_count = 0

    print(f"\n📦 ChromaDB Collection: {COLLECTION_NAME}")
    print(f"   Vectors stored: {vec_count:,}")
    print(f"   Persist path:   {CHROMA_DIR}")

    # DB stats
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '%_fts%'")
    data_tables = [r[0] for r in cur.fetchall()]

    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name LIKE '%_fts' "
        "AND name NOT LIKE '%_fts_config' "
        "AND name NOT LIKE '%_fts_data' "
        "AND name NOT LIKE '%_fts_docsize' "
        "AND name NOT LIKE '%_fts_idx'"
    )
    fts_tables = [r[0] for r in cur.fetchall()]

    total_fts_rows = 0
    fts_failures = []
    for ft in fts_tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM [{ft}]")
            total_fts_rows += cur.fetchone()[0]
        except Exception as e:
            fts_failures.append((ft, str(e)))

    print(f"\n📊 SQLite Database: {DB_PATH.name}")
    print(f"   Data tables:    {len(data_tables)}")
    print(f"   FTS5 indexes:   {len(fts_tables)}")
    print(f"   FTS5 total rows:{total_fts_rows:,}")
    if fts_failures:
        print(f"   ⚠️  FTS5 query failures ({len(fts_failures)}):")
        for ft_name, err in fts_failures:
            print(f"      - {ft_name}: {err}")

    # Priority table status
    print(f"\n📋 Priority Tables ({len(PRIORITY_TABLES)}):")
    for table in PRIORITY_TABLES:
        try:
            cur.execute(f"SELECT COUNT(*) FROM [{table}]")
            cnt = cur.fetchone()[0]
            # Check if indexed in ChromaDB
            if vec_count > 0:
                try:
                    sample = collection.get(
                        where={"source_table": table},
                        limit=1,
                    )
                    indexed = "✓ indexed" if sample["ids"] else "○ not indexed"
                except Exception:
                    indexed = "? unknown"
            else:
                indexed = "○ not indexed"
            print(f"   {table:45s} {cnt:>8,} rows  {indexed}")
        except Exception:
            print(f"   {table:45s}   ⚠ error")

    # Ollama models
    print(f"\n🤖 Ollama Models:")
    try:
        resp = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=10)
        models = resp.json().get("models", [])
        for m in models:
            name = m.get("name", "?")
            size_gb = m.get("size", 0) / (1024**3)
            print(f"   {name:30s} {size_gb:.1f} GB")
    except Exception as e:
        print(f"   ⚠ Cannot reach Ollama: {e}")

    conn.close()
    print(f"\n{'=' * 60}")


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="LitigationOS RAG Engine — Hybrid ChromaDB + FTS5 retrieval"
    )
    parser.add_argument("--ingest", action="store_true", help="Index all priority tables")
    parser.add_argument("--query", type=str, help="Ask a question")
    parser.add_argument("--status", action="store_true", help="Show index statistics")

    args = parser.parse_args()

    if args.ingest:
        run_ingest()
    elif args.query:
        run_query(args.query)
    elif args.status:
        run_status()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
