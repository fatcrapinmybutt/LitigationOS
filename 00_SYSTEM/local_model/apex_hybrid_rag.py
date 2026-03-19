"""
APEX Hybrid RAG — Enhanced Retrieval for Legal Documents
=========================================================

Combines four retrieval sources with Reciprocal Rank Fusion (RRF):
  1. BM25  — sparse ranked retrieval  (existing BM25Engine)
  2. TF-IDF — cosine similarity       (existing MANBEARPIG vectors)
  3. Dense — MiniLM / nomic-embed-text (shadow-programmed: OFF without LLM)
  4. FTS5  — SQLite full-text search   (litigation_context.db)

ARCHITECTURE:
  - Shadow-programmed: Dense embeddings disabled without APEX_LLM_ENABLED=true
  - When dense disabled, weights automatically redistribute to BM25/TF-IDF/FTS5
  - Thread-safe, never crashes, lazy-loads everything
  - Never sets CWD to repo root (shadow modules)

DATABASE CONNECTIONS (all use mandatory PRAGMA set):
  litigation_context.db       — 702 tables, primary search target
  master_index.db             — 1.7M files for file-level search
  chroma.sqlite3              — 2K vector embeddings (when available)
  MEEK234_HIGHSIGNAL_DB.sqlite — 13.4K high-signal quotes

Author: APEX_MANBEARPIG_LITIGATIONOS
"""

from __future__ import annotations

import io
import json
import logging
import math
import os
import re
import sqlite3
import sys
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# Shadow-program gate
# ---------------------------------------------------------------------------
APEX_LLM_ENABLED: bool = (
    os.environ.get("APEX_LLM_ENABLED", "false").lower() == "true"
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("apex.hybrid_rag")

# ---------------------------------------------------------------------------
# Path anchors
# ---------------------------------------------------------------------------
_HERE: Path = Path(__file__).parent
_REPO: Path = _HERE.parent.parent
_DEFAULT_DB: Path = _REPO / "litigation_context.db"
_MASTER_INDEX: Path = _REPO / "agents" / "master_index.db"
_HIGHSIGNAL_DB: Path = _REPO / "MEEK234_HIGHSIGNAL_DB.sqlite"
_CHROMA_DB: Path = _REPO / "chroma.sqlite3"

# ---------------------------------------------------------------------------
# Mandatory DB PRAGMAs
# ---------------------------------------------------------------------------
_DB_PRAGMAS: str = """
PRAGMA busy_timeout  = 60000;
PRAGMA journal_mode  = WAL;
PRAGMA cache_size    = -32000;
PRAGMA temp_store    = MEMORY;
PRAGMA synchronous   = NORMAL;
"""


def _safe_connect(db_path: str | Path) -> Optional[sqlite3.Connection]:
    """Open a SQLite connection with mandatory PRAGMAs."""
    try:
        p = str(db_path)
        if not Path(p).exists():
            logger.debug("DB not found: %s", p)
            return None
        conn = sqlite3.connect(p, timeout=60, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.executescript(_DB_PRAGMAS)
        return conn
    except Exception as exc:  # noqa: BLE001
        logger.error("DB connect failed (%s): %s", db_path, exc)
        return None


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    """Check whether *table* exists in the connected database."""
    try:
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
        return row is not None
    except Exception:  # noqa: BLE001
        return False


def _has_fts(conn: sqlite3.Connection, table: str) -> bool:
    """Check whether *table* is an FTS5 virtual table."""
    try:
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? AND sql LIKE '%fts5%'",
            (table,),
        ).fetchone()
        return row is not None
    except Exception:  # noqa: BLE001
        return False


# ═══════════════════════════════════════════════════════════════════════════
# Data classes
# ═══════════════════════════════════════════════════════════════════════════
@dataclass
class RAGResult:
    """Single retrieval result."""

    text: str = ""
    source: str = ""
    score: float = 0.0
    method: str = ""         # bm25 | tfidf | dense | fts5 | rrf
    lane: str = ""
    evidence_posture: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "text": self.text,
            "source": self.source,
            "score": round(self.score, 4),
            "method": self.method,
        }
        if self.lane:
            d["lane"] = self.lane
        if self.evidence_posture:
            d["evidence_posture"] = self.evidence_posture
        if self.metadata:
            d["metadata"] = self.metadata
        return d


# ═══════════════════════════════════════════════════════════════════════════
# Lane patterns (shared with apex_orchestrator, compiled once)
# ═══════════════════════════════════════════════════════════════════════════
_LANE_PATTERNS: Dict[str, List[re.Pattern]] = {
    "A": [re.compile(p, re.IGNORECASE) for p in [
        r"custody", r"parenting", r"Watson", r"L\.D\.W", r"best\s+interest", r"MCL\s*722",
    ]],
    "B": [re.compile(p, re.IGNORECASE) for p in [
        r"housing", r"Shady\s+Oaks", r"habitab", r"tenant", r"MCL\s*125", r"rent",
    ]],
    "D": [re.compile(p, re.IGNORECASE) for p in [
        r"PPO", r"protection\s+order", r"MCL\s*600\.2950", r"stalking",
    ]],
    "E": [re.compile(p, re.IGNORECASE) for p in [
        r"misconduct", r"McNeill", r"JTC", r"MCR\s*9\.2",
    ]],
    "F": [re.compile(p, re.IGNORECASE) for p in [
        r"appellate", r"COA\s*366810", r"MSC", r"MCR\s*7\.[23]", r"appeal",
    ]],
}


# ═══════════════════════════════════════════════════════════════════════════
# FTS5 Searchable Tables Configuration
# ═══════════════════════════════════════════════════════════════════════════
# Tables to query in litigation_context.db via FTS5 or LIKE fallback.
# Columns probed dynamically via PRAGMA table_info to avoid column-name crashes.
_FTS_TARGETS: List[Dict[str, str]] = [
    {"table": "documents",          "text_col_hint": "content",   "source_col_hint": "source"},
    {"table": "evidence_quotes",    "text_col_hint": "quote_text", "source_col_hint": "source"},
    {"table": "authority_chains",   "text_col_hint": "chain_text", "source_col_hint": "authority"},
    {"table": "claims",             "text_col_hint": "claim_text", "source_col_hint": "claim_id"},
    {"table": "research_summaries", "text_col_hint": "summary",   "source_col_hint": "topic"},
]

# Evidence posture hierarchy
POSTURES: List[str] = [
    "RECORD_FACT", "EVIDENCE_FACT", "SWORN_FACT", "ALLEGATION", "INFERENCE",
]


# ═══════════════════════════════════════════════════════════════════════════
# APEXHybridRAG
# ═══════════════════════════════════════════════════════════════════════════
class APEXHybridRAG:
    """Enhanced hybrid retrieval with 4-source Reciprocal Rank Fusion.

    Works fully offline.  Dense embeddings activate only when
    ``APEX_LLM_ENABLED=true`` and an embedding provider is available.
    """

    # RRF weights (tuned for legal retrieval)
    WEIGHTS: Dict[str, float] = {
        "bm25": 0.30,
        "tfidf": 0.20,
        "dense": 0.30,
        "fts5": 0.20,
    }

    # Fallback weights when dense embeddings unavailable
    WEIGHTS_NO_DENSE: Dict[str, float] = {
        "bm25": 0.40,
        "tfidf": 0.30,
        "fts5": 0.30,
    }

    # RRF constant (standard value from Cormack et al.)
    RRF_K: int = 60

    def __init__(self, db_path: Optional[str] = None) -> None:
        self._lock = threading.Lock()
        self.db_path: Path = Path(db_path) if db_path else _DEFAULT_DB

        # Lazy-loaded backends
        self._bm25: Any = None
        self._inference: Any = None
        self._embedder: Any = None

        # Cache discovered table schemas
        self._schema_cache: Dict[str, Dict[str, str]] = {}

        logger.info(
            "APEXHybridRAG init  LLM=%s  DB=%s", APEX_LLM_ENABLED, self.db_path,
        )

    # ------------------------------------------------------------------
    # Lazy loaders
    # ------------------------------------------------------------------
    def _get_bm25(self) -> Any:
        if self._bm25 is None:
            with self._lock:
                if self._bm25 is None:
                    try:
                        saved = os.getcwd()
                        os.chdir(str(_HERE))
                        from bm25_engine import BM25Engine  # type: ignore[import-untyped]
                        self._bm25 = BM25Engine()
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("BM25Engine unavailable: %s", exc)
                        self._bm25 = _NullBackend("bm25")
                    finally:
                        try:
                            os.chdir(saved)
                        except Exception:  # noqa: BLE001
                            pass
        return self._bm25

    def _get_inference(self) -> Any:
        if self._inference is None:
            with self._lock:
                if self._inference is None:
                    try:
                        saved = os.getcwd()
                        os.chdir(str(_HERE))
                        from inference_engine import MichiganLegalModel  # type: ignore[import-untyped]
                        self._inference = MichiganLegalModel()
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("Inference engine unavailable: %s", exc)
                        self._inference = _NullBackend("tfidf")
                    finally:
                        try:
                            os.chdir(saved)
                        except Exception:  # noqa: BLE001
                            pass
        return self._inference

    def _get_embedder(self) -> Any:
        """Load dense embedding provider. Only when LLM is enabled."""
        if self._embedder is None and APEX_LLM_ENABLED:
            with self._lock:
                if self._embedder is None:
                    try:
                        saved = os.getcwd()
                        os.chdir(str(_HERE))
                        from ollama_provider import OllamaProvider  # type: ignore[import-untyped]
                        self._embedder = OllamaProvider()
                    except Exception as exc:  # noqa: BLE001
                        logger.info("Dense embedder unavailable (expected without LLM): %s", exc)
                        self._embedder = _NullBackend("dense")
                    finally:
                        try:
                            os.chdir(saved)
                        except Exception:  # noqa: BLE001
                            pass
        return self._embedder

    @property
    def _dense_available(self) -> bool:
        if not APEX_LLM_ENABLED:
            return False
        emb = self._get_embedder()
        return emb is not None and not isinstance(emb, _NullBackend)

    @property
    def _active_weights(self) -> Dict[str, float]:
        return dict(self.WEIGHTS) if self._dense_available else dict(self.WEIGHTS_NO_DENSE)

    # ------------------------------------------------------------------
    # Schema discovery
    # ------------------------------------------------------------------
    def _discover_columns(
        self, conn: sqlite3.Connection, table: str, text_hint: str, source_hint: str,
    ) -> Tuple[Optional[str], Optional[str]]:
        """Dynamically discover the text and source columns for *table*.

        Checks PRAGMA table_info to find actual column names matching hints.
        Caches results for the session.
        """
        cache_key = f"{id(conn)}:{table}"
        if cache_key in self._schema_cache:
            cached = self._schema_cache[cache_key]
            return cached.get("text"), cached.get("source")

        text_col: Optional[str] = None
        source_col: Optional[str] = None
        try:
            cols_info = conn.execute(f"PRAGMA table_info({table})").fetchall()
            col_names = [c["name"] for c in cols_info]

            # Find text column: exact hint → partial match → first TEXT column
            if text_hint in col_names:
                text_col = text_hint
            else:
                for cn in col_names:
                    if text_hint.lower() in cn.lower() or "text" in cn.lower() or "content" in cn.lower():
                        text_col = cn
                        break
                if text_col is None and col_names:
                    text_col = col_names[-1]  # last column heuristic

            # Find source column: exact hint → partial match → first column
            if source_hint in col_names:
                source_col = source_hint
            else:
                for cn in col_names:
                    if source_hint.lower() in cn.lower() or "source" in cn.lower() or "id" in cn.lower():
                        source_col = cn
                        break
                if source_col is None and col_names:
                    source_col = col_names[0]

        except Exception as exc:  # noqa: BLE001
            logger.debug("Column discovery for %s failed: %s", table, exc)

        self._schema_cache[cache_key] = {"text": text_col, "source": source_col}
        return text_col, source_col

    # ------------------------------------------------------------------
    # Core search API
    # ------------------------------------------------------------------
    def search(
        self,
        query: str,
        top_k: int = 20,
        lane: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Hybrid search across all sources with RRF fusion.

        Each result dict: {text, source, score, method, lane, evidence_posture}.
        If *lane* is specified, post-filters results to that lane.
        """
        try:
            if not query or not query.strip():
                return []

            fetch_k = max(top_k * 3, 50)

            # Parallel retrieval from all sources
            fts5_results = self._search_fts5(query, top_k=fetch_k)
            bm25_results = self._search_bm25(query, top_k=fetch_k)
            tfidf_results = self._search_tfidf(query, top_k=fetch_k)

            # Dense embeddings (only when enabled)
            dense_results: List[RAGResult] = []
            if self._dense_available:
                dense_results = self._search_dense(query, top_k=fetch_k)

            # RRF fusion
            if dense_results:
                fused = self._rrf_fusion(
                    bm25_results, tfidf_results, dense_results, fts5_results,
                    weights=self.WEIGHTS,
                )
            else:
                fused = self._rrf_fusion(
                    bm25_results, tfidf_results, fts5_results,
                    weights=self.WEIGHTS_NO_DENSE,
                )

            # Post-filter by lane
            if lane:
                fused = [r for r in fused if not r.lane or r.lane == lane]

            # Truncate and convert
            return [r.to_dict() for r in fused[:top_k]]

        except Exception as exc:  # noqa: BLE001
            logger.error("search() failed: %s", exc)
            return []

    def search_evidence(
        self,
        query: str,
        lane: str,
        posture: Optional[str] = None,
        top_k: int = 20,
    ) -> List[Dict[str, Any]]:
        """Evidence-specific search with posture filtering.

        Postures: RECORD_FACT, EVIDENCE_FACT, SWORN_FACT, ALLEGATION, INFERENCE
        """
        try:
            results = self.search(query, top_k=top_k * 2, lane=lane)

            if posture and posture in POSTURES:
                results = [r for r in results if r.get("evidence_posture") == posture]

            # Also query high-signal DB
            hs_results = self._search_highsignal(query, lane=lane, top_k=top_k)
            for hr in hs_results:
                results.append(hr.to_dict())

            # Deduplicate by text content (first 100 chars)
            seen: set = set()
            deduped: List[Dict[str, Any]] = []
            for r in results:
                key = r.get("text", "")[:100].strip().lower()
                if key and key not in seen:
                    seen.add(key)
                    deduped.append(r)

            # Sort by score descending
            deduped.sort(key=lambda x: x.get("score", 0), reverse=True)
            return deduped[:top_k]

        except Exception as exc:  # noqa: BLE001
            logger.error("search_evidence() failed: %s", exc)
            return []

    def search_authorities(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """Search legal authorities (MCR, MCL, case law)."""
        try:
            conn = _safe_connect(self.db_path)
            if conn is None:
                return []

            results: List[Dict[str, Any]] = []
            try:
                # Check which authority tables exist
                for tbl in ["authority_chains", "authorities", "auth_rules", "rules_text"]:
                    if not _table_exists(conn, tbl):
                        continue

                    text_col, source_col = self._discover_columns(
                        conn, tbl, "chain_text", "authority",
                    )
                    if not text_col:
                        continue

                    # Build query terms for LIKE search
                    terms = [t.strip() for t in query.split() if len(t.strip()) >= 2]
                    if not terms:
                        continue

                    conditions = " OR ".join(
                        f"{text_col} LIKE ?" for _ in terms
                    )
                    params = [f"%{t}%" for t in terms]

                    sql = f"SELECT * FROM {tbl} WHERE {conditions} LIMIT ?"  # noqa: S608
                    params.append(str(top_k))
                    rows = conn.execute(sql, params).fetchall()

                    for row in rows:
                        d = dict(row)
                        results.append({
                            "text": str(d.get(text_col, ""))[:2000],
                            "source": f"{tbl}:{d.get(source_col, '')}",
                            "score": 1.0,
                            "method": "authority_search",
                        })
            finally:
                conn.close()

            return results[:top_k]

        except Exception as exc:  # noqa: BLE001
            logger.error("search_authorities() failed: %s", exc)
            return []

    def search_harms(
        self, query: str, category: Optional[str] = None, top_k: int = 20,
    ) -> List[Dict[str, Any]]:
        """Search the harm records in the database."""
        try:
            conn = _safe_connect(self.db_path)
            if conn is None:
                return []

            results: List[Dict[str, Any]] = []
            try:
                for tbl in ["harms", "harm_records", "harm_quantification"]:
                    if not _table_exists(conn, tbl):
                        continue

                    text_col, source_col = self._discover_columns(
                        conn, tbl, "description", "harm_id",
                    )
                    if not text_col:
                        continue

                    terms = [t.strip() for t in query.split() if len(t.strip()) >= 2]
                    if not terms:
                        continue

                    conditions = " OR ".join(f"{text_col} LIKE ?" for _ in terms)
                    params: list = [f"%{t}%" for t in terms]

                    if category:
                        conditions = f"({conditions}) AND category = ?"
                        params.append(category)

                    sql = f"SELECT * FROM {tbl} WHERE {conditions} LIMIT ?"  # noqa: S608
                    params.append(str(top_k))
                    rows = conn.execute(sql, params).fetchall()

                    for row in rows:
                        d = dict(row)
                        results.append({
                            "text": str(d.get(text_col, ""))[:2000],
                            "source": f"{tbl}:{d.get(source_col, '')}",
                            "score": 1.0,
                            "method": "harm_search",
                            "metadata": {"category": d.get("category", "")},
                        })
            finally:
                conn.close()

            return results[:top_k]

        except Exception as exc:  # noqa: BLE001
            logger.error("search_harms() failed: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Backend: FTS5
    # ------------------------------------------------------------------
    def _search_fts5(self, query: str, top_k: int = 50) -> List[RAGResult]:
        """SQLite FTS5 full-text search on litigation_context.db."""
        results: List[RAGResult] = []
        try:
            conn = _safe_connect(self.db_path)
            if conn is None:
                return results

            try:
                # Build FTS5 query: quote terms, join with OR for recall
                terms = [t.strip() for t in re.split(r"\s+", query) if len(t.strip()) >= 2]
                if not terms:
                    return results
                fts_query = " OR ".join(f'"{t}"' for t in terms)

                for target in _FTS_TARGETS:
                    tbl = target["table"]
                    fts_tbl = f"{tbl}_fts"

                    # Try FTS5 virtual table first
                    if _has_fts(conn, fts_tbl):
                        try:
                            rows = conn.execute(
                                f"SELECT *, rank FROM {fts_tbl} WHERE {fts_tbl} MATCH ? "
                                f"ORDER BY rank LIMIT ?",
                                (fts_query, top_k),
                            ).fetchall()
                            for row in rows:
                                d = dict(row)
                                text = str(d.get(target["text_col_hint"], ""))[:2000]
                                source = str(d.get(target["source_col_hint"], tbl))
                                rank_val = abs(float(d.get("rank", 0)))
                                results.append(RAGResult(
                                    text=text, source=f"fts5:{tbl}:{source}",
                                    score=rank_val, method="fts5",
                                ))
                            continue
                        except Exception:  # noqa: BLE001
                            pass

                    # Fallback: LIKE search on the real table
                    if not _table_exists(conn, tbl):
                        continue

                    text_col, source_col = self._discover_columns(
                        conn, tbl, target["text_col_hint"], target["source_col_hint"],
                    )
                    if not text_col:
                        continue

                    conditions = " OR ".join(f"{text_col} LIKE ?" for _ in terms)
                    params: list = [f"%{t}%" for t in terms]
                    sql = f"SELECT * FROM {tbl} WHERE {conditions} LIMIT ?"  # noqa: S608
                    params.append(str(top_k))

                    rows = conn.execute(sql, params).fetchall()
                    for idx, row in enumerate(rows):
                        d = dict(row)
                        text = str(d.get(text_col, ""))[:2000]
                        source = str(d.get(source_col, tbl))
                        # Synthetic score: penalize later results
                        score = 1.0 / (1 + idx)
                        results.append(RAGResult(
                            text=text, source=f"fts5_like:{tbl}:{source}",
                            score=score, method="fts5",
                            lane=self._detect_lane_from_text(text),
                            evidence_posture=d.get("posture", d.get("evidence_posture", "")),
                        ))
            finally:
                conn.close()

        except Exception as exc:  # noqa: BLE001
            logger.error("_search_fts5 failed: %s", exc)

        return results

    # ------------------------------------------------------------------
    # Backend: BM25
    # ------------------------------------------------------------------
    def _search_bm25(self, query: str, top_k: int = 50) -> List[RAGResult]:
        """BM25 ranked retrieval using existing BM25Engine."""
        results: List[RAGResult] = []
        try:
            bm25 = self._get_bm25()
            if isinstance(bm25, _NullBackend):
                return results

            # BM25Engine.search() returns list of (text, score, metadata) or similar
            if hasattr(bm25, "search"):
                raw = bm25.search(query, top_k=top_k)
                if isinstance(raw, list):
                    for idx, item in enumerate(raw):
                        if isinstance(item, dict):
                            results.append(RAGResult(
                                text=str(item.get("text", item.get("content", "")))[:2000],
                                source=str(item.get("source", f"bm25:{idx}")),
                                score=float(item.get("score", 1.0 / (1 + idx))),
                                method="bm25",
                                lane=self._detect_lane_from_text(
                                    str(item.get("text", "")),
                                ),
                            ))
                        elif isinstance(item, (list, tuple)) and len(item) >= 2:
                            results.append(RAGResult(
                                text=str(item[0])[:2000],
                                source=f"bm25:{idx}",
                                score=float(item[1]) if len(item) > 1 else 1.0 / (1 + idx),
                                method="bm25",
                            ))
            elif hasattr(bm25, "query"):
                raw = bm25.query(query)
                if isinstance(raw, list):
                    for idx, item in enumerate(raw):
                        text = str(item) if not isinstance(item, dict) else str(item.get("text", ""))
                        results.append(RAGResult(
                            text=text[:2000], source=f"bm25:{idx}",
                            score=1.0 / (1 + idx), method="bm25",
                        ))

        except Exception as exc:  # noqa: BLE001
            logger.error("_search_bm25 failed: %s", exc)

        return results

    # ------------------------------------------------------------------
    # Backend: TF-IDF
    # ------------------------------------------------------------------
    def _search_tfidf(self, query: str, top_k: int = 50) -> List[RAGResult]:
        """TF-IDF cosine similarity using MANBEARPIG inference engine."""
        results: List[RAGResult] = []
        try:
            inf = self._get_inference()
            if isinstance(inf, _NullBackend):
                return results

            # The inference engine's query() returns search results
            if hasattr(inf, "search") or hasattr(inf, "query"):
                method = getattr(inf, "search", None) or getattr(inf, "query", None)
                if method is None:
                    return results

                raw = method(query)

                # Normalize output format
                if isinstance(raw, str):
                    results.append(RAGResult(
                        text=raw[:2000], source="tfidf:manbearpig",
                        score=0.5, method="tfidf",
                    ))
                elif isinstance(raw, dict):
                    text = raw.get("response", raw.get("text", raw.get("answer", str(raw))))
                    results.append(RAGResult(
                        text=str(text)[:2000], source="tfidf:manbearpig",
                        score=float(raw.get("confidence", raw.get("score", 0.5))),
                        method="tfidf",
                    ))
                elif isinstance(raw, list):
                    for idx, item in enumerate(raw):
                        if isinstance(item, dict):
                            results.append(RAGResult(
                                text=str(item.get("text", item.get("content", "")))[:2000],
                                source=str(item.get("source", f"tfidf:{idx}")),
                                score=float(item.get("score", 1.0 / (1 + idx))),
                                method="tfidf",
                            ))
                        else:
                            results.append(RAGResult(
                                text=str(item)[:2000], source=f"tfidf:{idx}",
                                score=1.0 / (1 + idx), method="tfidf",
                            ))

        except Exception as exc:  # noqa: BLE001
            logger.error("_search_tfidf failed: %s", exc)

        return results[:top_k]

    # ------------------------------------------------------------------
    # Backend: Dense Embeddings
    # ------------------------------------------------------------------
    def _search_dense(self, query: str, top_k: int = 50) -> List[RAGResult]:
        """Dense embedding search. Disabled without APEX_LLM_ENABLED=true."""
        results: List[RAGResult] = []
        if not APEX_LLM_ENABLED:
            return results

        try:
            emb = self._get_embedder()
            if emb is None or isinstance(emb, _NullBackend):
                return results

            # Try embedding-based search if provider supports it
            if hasattr(emb, "search"):
                raw = emb.search(query, top_k=top_k)
                if isinstance(raw, list):
                    for idx, item in enumerate(raw):
                        if isinstance(item, dict):
                            results.append(RAGResult(
                                text=str(item.get("text", item.get("content", "")))[:2000],
                                source=str(item.get("source", f"dense:{idx}")),
                                score=float(item.get("score", item.get("similarity", 1.0 / (1 + idx)))),
                                method="dense",
                            ))
            elif hasattr(emb, "embed"):
                # Raw embedding: would need a vector store to search against
                # Chroma DB integration
                if _CHROMA_DB.exists():
                    logger.debug("Chroma DB found but direct vector search not implemented in fallback")

        except Exception as exc:  # noqa: BLE001
            logger.info("_search_dense failed (expected without LLM): %s", exc)

        return results

    # ------------------------------------------------------------------
    # High-signal DB search
    # ------------------------------------------------------------------
    def _search_highsignal(
        self, query: str, lane: Optional[str] = None, top_k: int = 20,
    ) -> List[RAGResult]:
        """Search MEEK234_HIGHSIGNAL_DB for high-signal evidence quotes."""
        results: List[RAGResult] = []
        try:
            conn = _safe_connect(_HIGHSIGNAL_DB)
            if conn is None:
                return results

            try:
                # Discover tables dynamically
                tables = [
                    r["name"]
                    for r in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall()
                ]

                terms = [t.strip() for t in query.split() if len(t.strip()) >= 2]
                if not terms:
                    return results

                for tbl in tables[:10]:  # limit to first 10 tables
                    text_col, source_col = self._discover_columns(
                        conn, tbl, "quote_text", "source",
                    )
                    if not text_col:
                        continue

                    conditions = " OR ".join(f"{text_col} LIKE ?" for _ in terms)
                    params: list = [f"%{t}%" for t in terms]
                    sql = f"SELECT * FROM {tbl} WHERE {conditions} LIMIT ?"  # noqa: S608
                    params.append(str(top_k))

                    rows = conn.execute(sql, params).fetchall()
                    for idx, row in enumerate(rows):
                        d = dict(row)
                        text = str(d.get(text_col, ""))[:2000]
                        results.append(RAGResult(
                            text=text,
                            source=f"highsignal:{tbl}:{d.get(source_col, idx)}",
                            score=1.5 / (1 + idx),  # boost high-signal results
                            method="fts5",
                            lane=lane or self._detect_lane_from_text(text),
                            evidence_posture=d.get("posture", ""),
                        ))
            finally:
                conn.close()

        except Exception as exc:  # noqa: BLE001
            logger.debug("_search_highsignal failed: %s", exc)

        return results

    # ------------------------------------------------------------------
    # Reciprocal Rank Fusion
    # ------------------------------------------------------------------
    def _rrf_fusion(
        self,
        *result_lists: Sequence[RAGResult],
        weights: Optional[Dict[str, float]] = None,
    ) -> List[RAGResult]:
        """Merge multiple ranked result lists using Reciprocal Rank Fusion.

        RRF score for document d = Σ (weight_i / (k + rank_i(d)))
        where k = 60 (standard constant).
        """
        try:
            w = weights or self._active_weights
            method_order = ["bm25", "tfidf", "dense", "fts5"]

            # Map: text_key → (RAGResult, cumulative_rrf_score)
            scores: Dict[str, Tuple[RAGResult, float]] = {}

            for list_idx, rlist in enumerate(result_lists):
                if not rlist:
                    continue

                # Determine method for this list (from first item)
                method = "unknown"
                if rlist and hasattr(rlist[0], "method"):
                    method = rlist[0].method
                elif list_idx < len(method_order):
                    method = method_order[list_idx]

                method_weight = w.get(method, 0.2)

                for rank, item in enumerate(rlist):
                    # Unique key: first 150 chars of text (dedup-safe)
                    key = item.text[:150].strip().lower() if item.text else f"empty_{id(item)}"
                    rrf_score = method_weight / (self.RRF_K + rank + 1)

                    if key in scores:
                        existing_result, existing_score = scores[key]
                        scores[key] = (existing_result, existing_score + rrf_score)
                    else:
                        scores[key] = (item, rrf_score)

            # Sort by RRF score descending
            sorted_items = sorted(scores.values(), key=lambda x: x[1], reverse=True)

            # Update scores and mark as RRF-fused
            fused: List[RAGResult] = []
            for item, score in sorted_items:
                fused_item = RAGResult(
                    text=item.text,
                    source=item.source,
                    score=score,
                    method="rrf",
                    lane=item.lane,
                    evidence_posture=item.evidence_posture,
                    metadata=item.metadata,
                )
                fused.append(fused_item)

            return fused

        except Exception as exc:  # noqa: BLE001
            logger.error("_rrf_fusion failed: %s", exc)
            # Fallback: just concatenate and deduplicate
            all_results: List[RAGResult] = []
            for rlist in result_lists:
                if rlist:
                    all_results.extend(rlist)
            return all_results

    # ------------------------------------------------------------------
    # Lane detection helper
    # ------------------------------------------------------------------
    @staticmethod
    def _detect_lane_from_text(text: str) -> str:
        """Quick lane detection from text snippet."""
        if not text:
            return ""
        try:
            for lane_id in ["E", "D", "F", "C", "A", "B"]:
                patterns = _LANE_PATTERNS.get(lane_id, [])
                if any(p.search(text) for p in patterns):
                    return lane_id
        except Exception:  # noqa: BLE001
            pass
        return ""

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------
    def status(self) -> Dict[str, Any]:
        """Return status of all retrieval backends."""
        return {
            "db_path": str(self.db_path),
            "db_exists": self.db_path.exists(),
            "llm_enabled": APEX_LLM_ENABLED,
            "dense_available": self._dense_available,
            "active_weights": self._active_weights,
            "highsignal_db": _HIGHSIGNAL_DB.exists(),
            "chroma_db": _CHROMA_DB.exists(),
            "backends": {
                "bm25": not isinstance(self._bm25, _NullBackend) if self._bm25 else "not_loaded",
                "tfidf": not isinstance(self._inference, _NullBackend) if self._inference else "not_loaded",
                "dense": (
                    not isinstance(self._embedder, _NullBackend)
                    if self._embedder else "not_loaded"
                ),
                "fts5": self.db_path.exists(),
            },
        }


# ═══════════════════════════════════════════════════════════════════════════
# Null backend (safe fallback)
# ═══════════════════════════════════════════════════════════════════════════
class _NullBackend:
    """Placeholder when a real backend can't be loaded."""

    def __init__(self, name: str = "null") -> None:
        self._name = name

    def search(self, query: str, **kw: Any) -> List:
        return []

    def query(self, query: str, **kw: Any) -> str:
        return ""

    def embed(self, text: str, **kw: Any) -> List[float]:
        return []


# ═══════════════════════════════════════════════════════════════════════════
# CLI entry point
# ═══════════════════════════════════════════════════════════════════════════
def main() -> None:
    """CLI: ``python apex_hybrid_rag.py "search query"``"""
    if sys.stdout.encoding != "utf-8":
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace",
        )

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    rag = APEXHybridRAG()

    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])

        if "--status" in sys.argv:
            print(json.dumps(rag.status(), indent=2, default=str))
        elif "--authorities" in sys.argv:
            query = query.replace("--authorities", "").strip()
            results = rag.search_authorities(query)
            print(json.dumps(results, indent=2, default=str, ensure_ascii=False))
        elif "--evidence" in sys.argv:
            query = query.replace("--evidence", "").strip()
            results = rag.search_evidence(query, lane="C")
            print(json.dumps(results, indent=2, default=str, ensure_ascii=False))
        elif "--harms" in sys.argv:
            query = query.replace("--harms", "").strip()
            results = rag.search_harms(query)
            print(json.dumps(results, indent=2, default=str, ensure_ascii=False))
        else:
            results = rag.search(query)
            print(json.dumps(results, indent=2, default=str, ensure_ascii=False))
            print(f"\n--- {len(results)} results ---")
    else:
        print("APEX Hybrid RAG — Legal Document Retrieval")
        print(f"  LLM enabled: {APEX_LLM_ENABLED}")
        st = rag.status()
        print(f"  DB exists: {st['db_exists']}")
        print(f"  Dense available: {st['dense_available']}")
        print(f"  Weights: {st['active_weights']}")
        print("\nUsage:")
        print('  python apex_hybrid_rag.py "MCR 2.003 disqualification"')
        print('  python apex_hybrid_rag.py --authorities "best interest factors"')
        print('  python apex_hybrid_rag.py --evidence "parental interference"')
        print('  python apex_hybrid_rag.py --harms "emotional distress"')
        print("  python apex_hybrid_rag.py --status")


if __name__ == "__main__":
    main()
