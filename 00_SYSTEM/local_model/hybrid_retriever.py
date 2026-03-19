"""
THE MANBEARPIG — Hybrid Retrieval Orchestrator (EPOCH v4.0)
===========================================================
Unified retrieval combining BM25S sparse, LSI semantic, and FTS5 native
search with Reciprocal Rank Fusion (RRF) score merging.

Each sub-retriever is lazy-loaded and fault-isolated: if one engine is
unavailable the others still contribute results.
"""

import sqlite3
import time
import os
import sys

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

# FTS5 tables and their text columns
FTS5_TARGETS = [
    ("evidence_quotes_fts", "quote_text"),
    ("auth_rules_fts", "full_text"),
    ("rules_text_fts", "context"),
]


class HybridRetriever:
    """Fuses BM25, LSI/Semantic, and FTS5 retrieval via Reciprocal Rank Fusion."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        # Lazy-loaded sub-retrievers
        self._bm25 = None
        self._semantic = None
        self._stats = {
            "bm25": {"available": False, "index_size": 0, "last_query_ms": 0},
            "semantic": {"available": False, "index_size": 0, "last_query_ms": 0},
            "fts5": {"available": False, "tables": 0, "last_query_ms": 0},
        }
        self._init_sub_retrievers()

    # ------------------------------------------------------------------
    # Lazy initialisation
    # ------------------------------------------------------------------

    def _init_sub_retrievers(self):
        """Lazy-load each sub-retriever inside try/except for resilience."""
        # BM25
        try:
            from bm25_engine import BM25Engine
            self._bm25 = BM25Engine(db_path=self.db_path)
            self._stats["bm25"]["available"] = True
            self._stats["bm25"]["index_size"] = len(getattr(self._bm25, "doc_texts", []))
            print("[HybridRetriever] BM25 engine loaded")
        except Exception as exc:
            print(f"[HybridRetriever] BM25 unavailable: {exc}")

        # Semantic / LSI
        try:
            from semantic_engine import SemanticEngine
            self._semantic = SemanticEngine()
            self._stats["semantic"]["available"] = True
            sm = getattr(self._semantic, "semantic_matrix", None)
            self._stats["semantic"]["index_size"] = sm.shape[0] if sm is not None else 0
            print("[HybridRetriever] Semantic/LSI engine loaded")
        except Exception as exc:
            print(f"[HybridRetriever] Semantic engine unavailable: {exc}")

        # FTS5 — verify tables exist
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            count = 0
            for tbl, _ in FTS5_TARGETS:
                try:
                    conn.execute(f"SELECT 1 FROM {tbl} LIMIT 1")
                    count += 1
                except Exception:
                    pass
            conn.close()
            self._stats["fts5"]["available"] = count > 0
            self._stats["fts5"]["tables"] = count
            print(f"[HybridRetriever] FTS5 ready — {count}/{len(FTS5_TARGETS)} tables")
        except Exception as exc:
            print(f"[HybridRetriever] FTS5 unavailable: {exc}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search(self, query: str, top_k: int = 10, methods: list = None) -> list:
        """Run multiple retrieval methods, fuse via RRF, return top_k results.

        Parameters
        ----------
        query   : natural-language search string
        top_k   : how many results to return after fusion
        methods : subset of ['bm25', 'semantic', 'fts5'] — default = all available

        Returns
        -------
        list of dict  {text, score, source, method_scores}
        """
        available = {
            "bm25": self._stats["bm25"]["available"],
            "semantic": self._stats["semantic"]["available"],
            "fts5": self._stats["fts5"]["available"],
        }
        if methods is None:
            methods = [m for m, ok in available.items() if ok]
        else:
            methods = [m for m in methods if available.get(m)]

        if not methods:
            print("[HybridRetriever] WARNING: no retrieval methods available")
            return []

        # Gather ranked lists from each method
        ranked_lists = {}
        fetch_k = top_k * 3  # over-fetch for better fusion

        if "bm25" in methods:
            ranked_lists["bm25"] = self._bm25_search(query, fetch_k)
        if "semantic" in methods:
            ranked_lists["semantic"] = self._semantic_search(query, fetch_k)
        if "fts5" in methods:
            ranked_lists["fts5"] = self._fts5_search(query, fetch_k)

        # Fuse
        fused = self._rrf_fuse(ranked_lists, k=60)

        # Deduplicate by text prefix (first 100 chars)
        seen_prefixes = set()
        deduped = []
        for item in fused:
            prefix = (item.get("text") or "")[:100].strip().lower()
            if prefix and prefix not in seen_prefixes:
                seen_prefixes.add(prefix)
                deduped.append(item)

        return deduped[:top_k]

    def get_retrieval_stats(self) -> dict:
        """Return stats dict for each sub-retriever."""
        return dict(self._stats)

    # ------------------------------------------------------------------
    # Sub-retriever wrappers
    # ------------------------------------------------------------------

    def _bm25_search(self, query: str, top_k: int) -> list:
        """Wrap BM25Engine.search() → list of {text, score, source}."""
        t0 = time.time()
        try:
            raw = self._bm25.search(query, top_k=top_k)
            results = []
            for r in raw:
                results.append({
                    "text": r.get("text", ""),
                    "score": float(r.get("score", 0)),
                    "source": f"bm25:{r.get('table', 'unknown')}:{r.get('rowid', '')}",
                })
            self._stats["bm25"]["last_query_ms"] = round((time.time() - t0) * 1000, 1)
            return results
        except Exception as exc:
            print(f"[HybridRetriever] BM25 search error: {exc}")
            return []

    def _semantic_search(self, query: str, top_k: int) -> list:
        """Wrap SemanticEngine.search() → list of {text, score, source}."""
        t0 = time.time()
        try:
            raw = self._semantic.search(query, top_k=top_k)
            results = []
            for r in raw:
                results.append({
                    "text": r.get("snippet", r.get("text", "")),
                    "score": float(r.get("score", 0)),
                    "source": f"semantic:{r.get('id', r.get('doc_type', 'unknown'))}",
                })
            self._stats["semantic"]["last_query_ms"] = round((time.time() - t0) * 1000, 1)
            return results
        except Exception as exc:
            print(f"[HybridRetriever] Semantic search error: {exc}")
            return []

    def _fts5_search(self, query: str, top_k: int) -> list:
        """Direct SQLite FTS5 MATCH across key tables."""
        t0 = time.time()
        results = []
        # Sanitise query for FTS5 — wrap tokens in double quotes to avoid syntax errors
        safe_tokens = []
        for token in query.split():
            cleaned = "".join(ch for ch in token if ch.isalnum() or ch in "._-")
            if cleaned:
                safe_tokens.append(f'"{cleaned}"')
        if not safe_tokens:
            return []
        fts_query = " OR ".join(safe_tokens)

        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            conn.execute("PRAGMA query_only=ON")
            for tbl, col in FTS5_TARGETS:
                try:
                    sql = (
                        f"SELECT {col}, rank FROM {tbl} "
                        f"WHERE {tbl} MATCH ? ORDER BY rank LIMIT ?"
                    )
                    rows = conn.execute(sql, (fts_query, top_k)).fetchall()
                    for text_val, rank_val in rows:
                        results.append({
                            "text": text_val or "",
                            "score": -float(rank_val) if rank_val else 0.0,
                            "source": f"fts5:{tbl}",
                        })
                except Exception as tbl_exc:
                    # Individual table failure is non-fatal
                    pass
            conn.close()
        except Exception as exc:
            print(f"[HybridRetriever] FTS5 search error: {exc}")

        # Sort by score descending, take top_k
        results.sort(key=lambda x: x["score"], reverse=True)
        self._stats["fts5"]["last_query_ms"] = round((time.time() - t0) * 1000, 1)
        return results[:top_k]

    # ------------------------------------------------------------------
    # Reciprocal Rank Fusion
    # ------------------------------------------------------------------

    def _rrf_fuse(self, ranked_lists: dict, k: int = 60) -> list:
        """Reciprocal Rank Fusion across multiple ranked result lists.

        For each document, fused_score = sum(1 / (k + rank_i)) for every
        list the document appears in.  Documents are keyed by text prefix
        (first 100 chars) to handle cross-method dedup.
        """
        doc_scores = {}   # key -> cumulative RRF score
        doc_records = {}  # key -> best record (highest individual score)
        doc_method_scores = {}  # key -> {method: rrf_contribution}

        for method_name, results in ranked_lists.items():
            for rank_i, item in enumerate(results):
                key = (item.get("text") or "")[:100].strip().lower()
                if not key:
                    continue
                rrf_score = 1.0 / (k + rank_i + 1)  # +1 for 1-based ranking

                doc_scores[key] = doc_scores.get(key, 0.0) + rrf_score

                if key not in doc_method_scores:
                    doc_method_scores[key] = {}
                doc_method_scores[key][method_name] = (
                    doc_method_scores[key].get(method_name, 0.0) + rrf_score
                )

                # Keep record with highest native score
                if key not in doc_records or item.get("score", 0) > doc_records[key].get("score", 0):
                    doc_records[key] = item

        # Build final list
        fused = []
        for key in doc_scores:
            record = dict(doc_records[key])
            record["score"] = round(doc_scores[key], 6)
            record["method_scores"] = doc_method_scores.get(key, {})
            fused.append(record)

        fused.sort(key=lambda x: x["score"], reverse=True)
        return fused

    # ------------------------------------------------------------------
    # Self-test
    # ------------------------------------------------------------------

    def self_test(self):
        """Run 3 test queries, show per-method and fused results."""
        test_queries = [
            "custody best interest factors MCL 722.23",
            "judicial bias disqualification MCR 2.003",
            "parental alienation factor j willingness",
        ]
        stats = self.get_retrieval_stats()
        print("\n" + "=" * 70)
        print("  HYBRID RETRIEVER — SELF TEST")
        print("=" * 70)
        print(f"  BM25 available : {stats['bm25']['available']}  (index: {stats['bm25']['index_size']} docs)")
        print(f"  Semantic avail : {stats['semantic']['available']}  (index: {stats['semantic']['index_size']} docs)")
        print(f"  FTS5 available : {stats['fts5']['available']}  (tables: {stats['fts5']['tables']})")
        print("=" * 70)

        for q in test_queries:
            print(f"\n  QUERY: {q}")
            print("-" * 60)

            # Per-method results
            for method in ["bm25", "semantic", "fts5"]:
                if not stats[method]["available"]:
                    print(f"    [{method.upper()}] — unavailable, skipped")
                    continue
                fn = {"bm25": self._bm25_search, "semantic": self._semantic_search, "fts5": self._fts5_search}[method]
                raw = fn(q, 3)
                print(f"    [{method.upper()}] {len(raw)} results")
                for i, r in enumerate(raw[:3]):
                    snippet = (r.get("text") or "")[:80].replace("\n", " ")
                    print(f"      {i+1}. [{r.get('score',0):.4f}] {snippet}...")

            # Fused results
            fused = self.search(q, top_k=5)
            print(f"    [FUSED] {len(fused)} results (RRF)")
            for i, r in enumerate(fused[:5]):
                snippet = (r.get("text") or "")[:80].replace("\n", " ")
                methods = ", ".join(r.get("method_scores", {}).keys())
                print(f"      {i+1}. [{r['score']:.4f}] ({methods}) {snippet}...")

        updated_stats = self.get_retrieval_stats()
        print(f"\n  Timing — BM25: {updated_stats['bm25']['last_query_ms']}ms | "
              f"Semantic: {updated_stats['semantic']['last_query_ms']}ms | "
              f"FTS5: {updated_stats['fts5']['last_query_ms']}ms")
        print("=" * 70)
        print("  SELF TEST COMPLETE")
        print("=" * 70)


# ------------------------------------------------------------------
# CLI entry point
# ------------------------------------------------------------------
if __name__ == "__main__":
    hr = HybridRetriever()
    if "--test" in sys.argv or len(sys.argv) == 1:
        hr.self_test()
    else:
        query = " ".join(sys.argv[1:])
        results = hr.search(query)
        for i, r in enumerate(results):
            print(f"{i+1}. [{r['score']:.4f}] {r.get('source','')}  {(r.get('text',''))[:120]}")
