"""
BM25S Sparse Retrieval Engine — MBP LitigationOS 2026
=====================================================
BM25-based document retrieval over litigation_context.db tables.
Supports hybrid search via Reciprocal Rank Fusion (RRF) with TF-IDF results.
"""

import bm25s
import numpy as np
import sqlite3
import json
import os
import pickle
import time

DEFAULT_DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
DEFAULT_CACHE = r"C:\Users\andre\LitigationOS\00_SYSTEM\local_model\model_data\bm25"

# Table definitions: (table_name, text_column, row_limit)
SOURCE_TABLES = [
    ("evidence_quotes", "quote_text", None),
    ("auth_rules", "full_text", None),
    ("pages", "text_content", 50000),
    ("md_sections", "content", None),
    ("rules_text", "context", None),
]


class BM25Engine:
    """BM25S sparse retrieval over the litigation knowledge base."""

    def __init__(self, db_path=DEFAULT_DB, cache_dir=None):
        self.db_path = db_path
        self.cache_dir = cache_dir or DEFAULT_CACHE
        self.retriever = None
        self.doc_texts = []
        self.doc_meta = []  # list of {"table": ..., "rowid": ...}
        self._index_loaded = False

    # ------------------------------------------------------------------
    # Index building
    # ------------------------------------------------------------------

    def build_index(self):
        """Pull text from 5 DB tables, tokenize, build BM25 index, save."""
        print("[BM25] Building index from litigation_context.db ...")
        t0 = time.time()
        self.doc_texts = []
        self.doc_meta = []

        try:
            conn = sqlite3.connect(self.db_path)
            for table, col, limit in SOURCE_TABLES:
                # Use id if present, fall back to rowid
                sql = f"SELECT rowid AS _rid, {col} FROM {table}"
                if limit:
                    sql += f" LIMIT {limit}"
                try:
                    cur = conn.execute(sql)
                    count = 0
                    for row in cur:
                        text = row[1] or ""
                        if not text.strip():
                            continue
                        self.doc_texts.append(text)
                        self.doc_meta.append({"table": table, "rowid": row[0]})
                        count += 1
                    print(f"  [{table}] loaded {count} docs")
                except Exception as e:
                    print(f"  [{table}] ERROR: {e}")
            conn.close()
        except Exception as e:
            print(f"[BM25] DB connection error: {e}")
            return

        if not self.doc_texts:
            print("[BM25] No documents found — aborting index build.")
            return

        print(f"[BM25] Tokenizing {len(self.doc_texts)} documents ...")
        try:
            corpus_tokens = bm25s.tokenize(self.doc_texts, show_progress=False)
        except Exception as e:
            print(f"[BM25] Tokenization error: {e}")
            return

        print("[BM25] Building BM25 index ...")
        try:
            self.retriever = bm25s.BM25()
            self.retriever.index(corpus_tokens, show_progress=False)
        except Exception as e:
            print(f"[BM25] Index build error: {e}")
            return

        self._save_index()
        self._index_loaded = True
        elapsed = time.time() - t0
        print(f"[BM25] Index built — {len(self.doc_texts)} docs in {elapsed:.1f}s")

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _save_index(self):
        """Save BM25 index and metadata to cache directory."""
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            self.retriever.save(self.cache_dir)

            meta_path = os.path.join(self.cache_dir, "doc_meta.json")
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(self.doc_meta, f)

            texts_path = os.path.join(self.cache_dir, "doc_texts.pkl")
            with open(texts_path, "wb") as f:
                pickle.dump(self.doc_texts, f, protocol=pickle.HIGHEST_PROTOCOL)

            print(f"[BM25] Index saved to {self.cache_dir}")
        except Exception as e:
            print(f"[BM25] Save error: {e}")

    def load_index(self):
        """Load cached BM25 index from disk if available."""
        meta_path = os.path.join(self.cache_dir, "doc_meta.json")
        texts_path = os.path.join(self.cache_dir, "doc_texts.pkl")
        params_path = os.path.join(self.cache_dir, "params.index.json")

        if not all(os.path.exists(p) for p in [meta_path, texts_path, params_path]):
            print("[BM25] No cached index found.")
            return False

        try:
            print("[BM25] Loading cached index ...")
            t0 = time.time()
            self.retriever = bm25s.BM25.load(self.cache_dir, load_corpus=False)

            with open(meta_path, "r", encoding="utf-8") as f:
                self.doc_meta = json.load(f)

            with open(texts_path, "rb") as f:
                self.doc_texts = pickle.load(f)

            self._index_loaded = True
            elapsed = time.time() - t0
            print(f"[BM25] Index loaded — {len(self.doc_texts)} docs in {elapsed:.1f}s")
            return True
        except Exception as e:
            print(f"[BM25] Load error: {e}")
            return False

    def _ensure_index(self):
        """Lazy-load or build the index on first use."""
        if self._index_loaded:
            return True
        if self.load_index():
            return True
        self.build_index()
        return self._index_loaded

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, query: str, top_k: int = 10, table_filter: str = None):
        """
        Search the BM25 index.

        Returns list of dicts: {text, score, table, rowid}
        """
        if not self._ensure_index():
            print("[BM25] No index available.")
            return []

        try:
            query_tokens = bm25s.tokenize([query], show_progress=False)
            # Clamp k to corpus size
            effective_k = min(top_k if table_filter is None else top_k * 5, len(self.doc_texts))
            if effective_k < 1:
                return []

            doc_ids, scores = self.retriever.retrieve(
                query_tokens, k=effective_k, show_progress=False
            )
        except Exception as e:
            print(f"[BM25] Search error: {e}")
            return []

        results = []
        # doc_ids and scores are 2-D arrays (one row per query)
        ids_row = doc_ids[0]
        scores_row = scores[0]

        for idx, (doc_id, score) in enumerate(zip(ids_row, scores_row)):
            doc_id = int(doc_id)
            if doc_id < 0 or doc_id >= len(self.doc_texts):
                continue
            meta = self.doc_meta[doc_id]
            if table_filter and meta["table"] != table_filter:
                continue
            results.append({
                "text": self.doc_texts[doc_id],
                "score": float(score),
                "table": meta["table"],
                "rowid": meta["rowid"],
            })
            if len(results) >= top_k:
                break

        return results

    # ------------------------------------------------------------------
    # Hybrid search (RRF)
    # ------------------------------------------------------------------

    def hybrid_search(self, query: str, tfidf_results: list = None, top_k: int = 10):
        """
        Reciprocal Rank Fusion of BM25 + optional TF-IDF results.

        RRF score = sum(1 / (k + rank_i)) with k=60.
        """
        RRF_K = 60
        bm25_results = self.search(query, top_k=top_k * 3)

        # Build a unified score map keyed by (table, rowid)
        score_map = {}

        for rank, r in enumerate(bm25_results):
            key = (r["table"], r["rowid"])
            rrf_score = 1.0 / (RRF_K + rank + 1)
            entry = score_map.setdefault(key, {
                "text": r["text"],
                "table": r["table"],
                "rowid": r["rowid"],
                "rrf_score": 0.0,
            })
            entry["rrf_score"] += rrf_score

        if tfidf_results:
            for rank, r in enumerate(tfidf_results):
                key = (r.get("table", ""), r.get("rowid", rank))
                rrf_score = 1.0 / (RRF_K + rank + 1)
                entry = score_map.setdefault(key, {
                    "text": r.get("text", ""),
                    "table": r.get("table", ""),
                    "rowid": r.get("rowid", 0),
                    "rrf_score": 0.0,
                })
                entry["rrf_score"] += rrf_score

        merged = sorted(score_map.values(), key=lambda x: x["rrf_score"], reverse=True)
        return merged[:top_k]

    # ------------------------------------------------------------------
    # Self-test
    # ------------------------------------------------------------------

    def self_test(self):
        """Run 3 diagnostic queries and print results."""
        print("\n" + "=" * 60)
        print("BM25 Engine — Self-Test")
        print("=" * 60)

        if not self._ensure_index():
            print("[FAIL] Could not load or build index.")
            return

        test_queries = [
            "best interest of the child custody factors",
            "personal protection order violation",
            "parenting time schedule modification",
        ]

        for q in test_queries:
            print(f"\n--- Query: {q!r} ---")
            try:
                results = self.search(q, top_k=3)
                if not results:
                    print("  (no results)")
                    continue
                for i, r in enumerate(results, 1):
                    snippet = r["text"][:120].replace("\n", " ")
                    print(f"  {i}. [{r['table']}:{r['rowid']}] score={r['score']:.4f}")
                    print(f"     {snippet}...")
            except Exception as e:
                print(f"  ERROR: {e}")

        # Quick hybrid test
        print(f"\n--- Hybrid RRF test: {test_queries[0]!r} ---")
        try:
            hybrid = self.hybrid_search(test_queries[0], top_k=3)
            for i, r in enumerate(hybrid, 1):
                snippet = r["text"][:120].replace("\n", " ")
                print(f"  {i}. [{r['table']}:{r['rowid']}] rrf={r['rrf_score']:.6f}")
                print(f"     {snippet}...")
        except Exception as e:
            print(f"  ERROR: {e}")

        print(f"\n[OK] Self-test complete — index has {len(self.doc_texts)} documents.")


if __name__ == "__main__":
    engine = BM25Engine()
    if not engine.load_index():
        engine.build_index()
    engine.self_test()
