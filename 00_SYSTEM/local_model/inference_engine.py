#!/usr/bin/env python3
"""
THE MANBEARPIG — Michigan Legal Language Model (MANBEARPIG) Inference — EPOCH v9.0 — OMEGA-INFINITY EDITION
=================================================================================
100% local, 100% offline, 100% crashproof inference engine.
30 skills, 140+ JSON-RPC methods, 5 jurisdictions (MI Circuit, COA, MSC, Federal, JTC).
Loads trained model, processes queries, returns structured legal answers.

Usage:
    # Python API
    from inference_engine import MichiganLegalModel
    model = MichiganLegalModel()
    result = model.query("What does MCR 2.003 say about disqualification?")

    # CLI
    python inference_engine.py "your question here"

    # JSON-RPC via stdin/stdout pipe (for JS integration)
    python inference_engine.py --pipe
"""

from __future__ import annotations

# Network Safety Net — must be after __future__ but before other imports
try:
    import network_safety_net  # noqa: F401
except ImportError:
    pass  # Safety net not available — continue without it

import hashlib
import json
import logging
import os
import pickle
import re
import sqlite3
import sys
import time

logger = logging.getLogger(__name__)
from pathlib import Path
from functools import lru_cache
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent if 'local_model' in str(Path(__file__)) else Path(__file__).resolve().parent))
try:
    from cycle_method import cycle_json, cycle_print
except ImportError:
    cycle_json = lambda obj, **kw: print(json.dumps(obj, default=str))
    cycle_print = print

import numpy as np
from scipy.sparse import load_npz
from sklearn.metrics.pairwise import cosine_similarity

# ── Paths ──────────────────────────────────────────────────────────
MODEL_DIR = Path(__file__).parent / "model_data"
DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)


def _safe(fn, default=None):
    """Run fn, return default on ANY error."""
    try:
        return fn()
    except Exception as e:
        logger.debug(f"_safe() caught error in {fn.__name__ if hasattr(fn, '__name__') else 'lambda'}: {e}")
        return default


class MichiganLegalModel:
    """
    Purpose-built Michigan litigation language model.
    TF-IDF retrieval + Naive Bayes classification + entity extraction +
    legal concept KB + template response generation + lawyer mode +
    pattern detection + self-healing error recovery.
    """

    def __init__(self):
        self.loaded = False
        self.vectorizer = None
        self.tfidf_matrix = None
        self.corpus_labels = []
        self.corpus_meta = []
        self.corpus_texts = []
        self.intent_clf = None
        self.intent_le = None
        self.doctype_clf = None
        self.doctype_le = None
        self.legal_concepts = {}
        self.entity_patterns = {}
        self.manifest = {}
        self._db = None
        self._cache = {}  # query result cache
        self._error_log = []  # self-healing error tracking
        self._pattern_cache = {}  # pattern detection cache
        self._heal_attempts = {}  # track auto-heal attempts per component
        self._brain_db = None  # writable connection for brain tables
        self._context_window: list[dict] = []  # sliding window of last 10 queries
        self._inverted_index = None  # fast-path inverted index
        self._hot_cache = {}  # preloaded data for sub-millisecond lookups
        self._engine_cache = {}  # lazy-loading engine registry
        self._query_rewriter = None  # AdaptiveRewriter for LIKE→FTS5 rewrites
        self._load()
        self._preload_hot_data()

    def _preload_hot_data(self):
        """Preload frequently-accessed data into memory for sub-ms lookups."""
        if not self.loaded:
            return
        try:
            # Cache legal concept keywords for fast matching
            self._hot_cache["concept_count"] = len(self.legal_concepts)
            self._hot_cache["corpus_size"] = len(self.corpus_texts)
            self._hot_cache["has_inverted_index"] = self._inverted_index is not None
        except Exception as e:
            logger.warning(f"Hot data preload (initial) failed: {e}")


    def _get_engine(self, name, cls, *args):
        """Lazy-load and cache engine instances to avoid re-instantiation."""
        if name not in self._engine_cache:
            self._engine_cache[name] = cls(*args)
        return self._engine_cache[name]

    def _load(self):
        """Load trained model from disk. Fails gracefully."""
        if not (MODEL_DIR / "manifest.json").exists():
            return

        try:
            with open(MODEL_DIR / "manifest.json") as f:
                self.manifest = json.load(f)

            with open(MODEL_DIR / "vectorizer.pkl", "rb") as f:
                self.vectorizer = pickle.load(f)

            self.tfidf_matrix = load_npz(MODEL_DIR / "tfidf_matrix.npz")

            with open(MODEL_DIR / "intent_clf.pkl", "rb") as f:
                self.intent_clf, self.intent_le = pickle.load(f)

            with open(MODEL_DIR / "doctype_clf.pkl", "rb") as f:
                self.doctype_clf, self.doctype_le = pickle.load(f)

            with open(MODEL_DIR / "corpus_labels.json") as f:
                self.corpus_labels = json.load(f)

            with open(MODEL_DIR / "corpus_meta.json") as f:
                self.corpus_meta = json.load(f)

            with open(MODEL_DIR / "corpus_texts.json") as f:
                self.corpus_texts = json.load(f)

            with open(MODEL_DIR / "legal_concepts.json") as f:
                self.legal_concepts = json.load(f)

            with open(MODEL_DIR / "entity_patterns.json") as f:
                raw = json.load(f)
                self.entity_patterns = {k: re.compile(v, re.I) for k, v in raw.items()}

            self.loaded = True

            # Load inverted index (optional fast path)
            try:
                from inverted_index import InvertedIndex
                if InvertedIndex.exists():
                    self._inverted_index = InvertedIndex.load()
            except Exception as e:
                logger.info(f"Inverted index not available, using cosine similarity: {e}")

        except Exception as e:
            print(f"[MANBEARPIG] Load warning: {e}", file=sys.stderr)

    def _preload_hot_data(self):
        """Cache frequently-queried data in memory for sub-millisecond lookups.

        Loads auth_rules, research_summaries, evidence_quotes, and legal
        concepts so repeat queries skip SQLite entirely (~200ms -> <5ms).
        Also applies LRU caching to _db_lookup, match_concepts, find_authority.
        """
        self._hot_cache = {
            "auth_rules": {},
            "research_summaries": [],
            "evidence_quotes": [],
            "legal_concepts": dict(self.legal_concepts),
        }
        conn = self._get_db()
        if not conn:
            return

        # 1. Auth rules keyed by rule_number (prefer clean view)
        try:
            try:
                rows = conn.execute(
                    "SELECT rule_number, title, full_text FROM v_clean_auth_rules"
                ).fetchall()
            except Exception:
                rows = conn.execute(
                    "SELECT rule_number, title, full_text FROM auth_rules"
                ).fetchall()
            for row in rows:
                self._hot_cache["auth_rules"][row["rule_number"]] = {
                    "title": row["title"],
                    "full_text": row["full_text"],
                }
        except Exception as e:
            self._log_error("preload_auth_rules", str(e))

        # 2. Research summaries
        try:
            rows = conn.execute("SELECT * FROM research_summaries").fetchall()
            self._hot_cache["research_summaries"] = [
                {k: row[k] for k in row.keys()} for row in rows
            ]
        except Exception as e:
            self._log_error("preload_research_summaries", str(e))

        # 3. Evidence quotes
        try:
            rows = conn.execute("SELECT * FROM evidence_quotes").fetchall()
            self._hot_cache["evidence_quotes"] = [
                {k: row[k] for k in row.keys()} for row in rows
            ]
        except Exception as e:
            self._log_error("preload_evidence_quotes", str(e))

        # 4. Concepts already loaded from legal_concepts.json in _load()

        # 5. LRU caching on key lookup methods
        self.match_concepts = lru_cache(maxsize=128)(self.match_concepts)
        self.find_authority = lru_cache(maxsize=128)(self.find_authority)

        # _db_lookup takes unhashable args; wrap with frozen-key adapter
        _orig_db_lookup = self._db_lookup
        @lru_cache(maxsize=256)
        def _cached_db_lookup(intent, ent_frozen, kw_frozen):
            entities = {k: list(v) for k, v in ent_frozen}
            keywords = list(kw_frozen)
            return _orig_db_lookup(intent, entities, keywords)

        def _db_lookup_wrapper(intent, entities, keywords):
            ent_frozen = tuple(sorted((k, tuple(v)) for k, v in entities.items()))
            kw_frozen = tuple(keywords)
            return _cached_db_lookup(intent, ent_frozen, kw_frozen)
        self._db_lookup = _db_lookup_wrapper

    def _get_db(self):
        """Get DB connection with self-healing. Auto-reconnects on failure."""
        if self._db:
            try:
                self._db.execute("SELECT 1")
                return self._db
            except Exception:
                self._log_error("db_connection", "Stale connection detected, reconnecting")
                self._db = None

        for attempt in range(3):
            try:
                self._db = sqlite3.connect(DB_PATH, timeout=60)
                self._db.execute("PRAGMA journal_mode=WAL")
                self._db.execute("PRAGMA cache_size=-131072")  # 128MB cache
                self._db.execute("PRAGMA query_only=ON")
                self._db.execute("PRAGMA mmap_size=12884901888")  # 12GB mmap (Δ∞)
                self._db.execute("PRAGMA temp_store=MEMORY")
                self._db.execute("PRAGMA synchronous=NORMAL")
                self._db.execute("PRAGMA busy_timeout=180000")
                self._db.row_factory = sqlite3.Row
                # Wire AdaptiveRewriter for automatic LIKE→FTS5 optimization
                if self._query_rewriter is None:
                    self._query_rewriter = self._init_query_rewriter()
                return self._db
            except Exception as e:
                self._log_error("db_connection", f"Attempt {attempt+1}: {e}")
                time.sleep(0.5 * (attempt + 1))
                self._db = None
        return None

    def _init_query_rewriter(self):
        """Lazy-load AdaptiveRewriter for transparent LIKE→FTS5 rewrites."""
        try:
            pipeline_dir = Path(__file__).resolve().parent.parent / "pipeline"
            rewriter_path = pipeline_dir / "adaptive_query_rewriter.py"
            if rewriter_path.exists():
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "adaptive_query_rewriter", str(rewriter_path))
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    return mod.AdaptiveRewriter(DB_PATH)
        except Exception as e:
            logger.debug(f"AdaptiveRewriter init failed (non-fatal): {e}")
        return None

    def _rewrite_sql(self, sql: str, params: tuple | None = None):
        """Rewrite SQL through AdaptiveRewriter if available."""
        if self._query_rewriter:
            try:
                return self._query_rewriter.rewrite(sql, params)
            except Exception:
                pass
        return sql, params

    @staticmethod
    def _stem_word(word: str) -> str:
        """Lightweight Porter-style suffix stripping (zero dependencies).

        Handles the most impactful legal suffixes so "disqualification"
        matches "disqualify", "violation" matches "violat", etc.
        """
        if len(word) < 5:
            return word
        # Order matters — try longest suffixes first
        for suffix, replacement in [
            ("ication", ""),   # disqualification → disqualif
            ("ation", ""),     # violation → viol, modification → modif
            ("ment", ""),      # judgment → judg, enforcement → enforc
            ("ness", ""),      # willingness → willing
            ("ible", ""),      # admissible → admiss
            ("able", ""),      # reasonable → reason
            ("ious", ""),      # egregious → egreg
            ("eous", ""),      # erroneous → erron
            ("ing", ""),       # filing → fil
            ("tion", ""),      # objection → objec
            ("sion", ""),      # decision → deci
            ("ity", ""),       # custody → custod
            ("ies", "y"),      # parties → party
            ("ive", ""),       # protective → protect
            ("ful", ""),       # unlawful → unlaw
            ("ous", ""),       # frivolous → frivol
            ("ed", ""),        # dismissed → dismiss
            ("ly", ""),        # properly → proper
            ("er", ""),        # order → ord
            ("es", ""),        # causes → caus
            ("al", ""),        # procedural → procedur
        ]:
            if word.endswith(suffix) and len(word) - len(suffix) + len(replacement) >= 3:
                return word[: -len(suffix)] + replacement
        return word

    def _log_error(self, component: str, msg: str):
        """Log error for self-healing analysis."""
        entry = {"ts": time.time(), "component": component, "msg": str(msg)[:200]}
        self._error_log.append(entry)
        if len(self._error_log) > 500:
            self._error_log = self._error_log[-250:]

    def _self_heal(self, component: str):
        """Attempt to self-heal a failed component."""
        attempts = self._heal_attempts.get(component, 0)
        if attempts >= 3:
            return False  # give up after 3 attempts

        self._heal_attempts[component] = attempts + 1

        if component == "db_connection":
            self._db = None
            return self._get_db() is not None
        elif component == "vectorizer":
            try:
                with open(MODEL_DIR / "vectorizer.pkl", "rb") as f:
                    self.vectorizer = pickle.load(f)
                return True
            except Exception as e:
                logger.error(f"Self-heal failed for vectorizer: {e}")
                return False
        elif component == "tfidf_matrix":
            try:
                self.tfidf_matrix = load_npz(MODEL_DIR / "tfidf_matrix.npz")
                return True
            except Exception as e:
                logger.error(f"Self-heal failed for tfidf_matrix: {e}")
                return False
        elif component == "intent_clf":
            try:
                with open(MODEL_DIR / "intent_clf.pkl", "rb") as f:
                    self.intent_clf, self.intent_le = pickle.load(f)
                return True
            except Exception as e:
                logger.error(f"Self-heal failed for intent_clf: {e}")
                return False
        return False

    def get_error_report(self) -> dict:
        """Return self-healing diagnostic report."""
        recent = self._error_log[-20:] if self._error_log else []
        by_component = {}
        for e in self._error_log:
            c = e["component"]
            by_component[c] = by_component.get(c, 0) + 1
        return {
            "total_errors": len(self._error_log),
            "by_component": by_component,
            "heal_attempts": dict(self._heal_attempts),
            "recent": recent,
            "cache_size": len(self._cache),
        }

    # ── Brain / Persistent Memory ────────────────────────────────

    def _get_brain_db(self):
        """Get a *writable* DB connection for brain tables (query_history, etc.)."""
        if self._brain_db:
            try:
                self._brain_db.execute("SELECT 1")
                return self._brain_db
            except Exception as e:
                logger.warning(f"Brain DB stale connection, reconnecting: {e}")
                self._brain_db = None

        try:
            self._brain_db = sqlite3.connect(DB_PATH, timeout=60)
            self._brain_db.execute("PRAGMA journal_mode=WAL")
            self._brain_db.execute("PRAGMA busy_timeout=60000")
            self._brain_db.execute("PRAGMA mmap_size=12884901888")  # 12GB mmap (Δ∞)
            self._brain_db.execute("PRAGMA cache_size=-131072")
            self._brain_db.execute("PRAGMA temp_store=MEMORY")
            self._brain_db.execute("PRAGMA synchronous=NORMAL")
            self._brain_db.row_factory = sqlite3.Row
            return self._brain_db
        except Exception as e:
            self._log_error("brain_db", str(e))
            return None

    def _log_to_brain(self, query_text: str, result: dict):
        """Non-blocking: log query to brain tables. Never raises."""
        try:
            conn = self._get_brain_db()
            if not conn:
                return

            intent = result.get("intent", "unknown")
            confidence = result.get("confidence", 0.0)
            response_len = len(result.get("response", ""))
            cache_hit = 1 if result.get("cached", False) else 0
            latency = result.get("elapsed_ms", 0.0)
            patterns_found = len(result.get("patterns", []))

            # 1. Log to query_history
            cur = conn.execute(
                "INSERT INTO query_history "
                "(query_text, intent_predicted, confidence, response_length, "
                "cache_hit, latency_ms, patterns_found) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (query_text, intent, confidence, response_len,
                 cache_hit, latency, patterns_found),
            )
            query_id = cur.lastrowid
            conn.commit()

            # 2. Track knowledge gaps
            retrieval_count = result.get("retrieval_count", 0)
            db_match_count = result.get("db_match_count", 0)

            if confidence < 0.3:
                conn.execute(
                    "INSERT INTO knowledge_gaps (query_text, gap_type) VALUES (?, ?)",
                    (query_text, "low_confidence"),
                )
                conn.commit()
            elif retrieval_count == 0 and db_match_count == 0:
                conn.execute(
                    "INSERT INTO knowledge_gaps (query_text, gap_type) VALUES (?, ?)",
                    (query_text, "no_results"),
                )
                conn.commit()

            # 3. Update confidence_calibration
            row = conn.execute(
                "SELECT id, total_queries, avg_confidence FROM confidence_calibration "
                "WHERE intent_class = ?",
                (intent,),
            ).fetchone()

            if row:
                new_total = row["total_queries"] + 1
                new_avg = (row["avg_confidence"] * row["total_queries"] + confidence) / new_total
                conn.execute(
                    "UPDATE confidence_calibration SET "
                    "total_queries = ?, avg_confidence = ?, last_updated = datetime('now') "
                    "WHERE id = ?",
                    (new_total, round(new_avg, 4), row["id"]),
                )
            else:
                conn.execute(
                    "INSERT INTO confidence_calibration "
                    "(intent_class, total_queries, avg_confidence) VALUES (?, 1, ?)",
                    (intent, confidence),
                )
            conn.commit()

        except Exception as e:
            self._log_error("brain_log", str(e))

    def get_brain_stats(self) -> dict:
        """Return brain statistics: query count, gap count, avg confidence, top intents."""
        stats = {
            "query_count": 0,
            "gap_count": 0,
            "avg_confidence": 0.0,
            "top_intents": [],
            "status": "ok",
        }
        try:
            conn = self._get_brain_db()
            if not conn:
                stats["status"] = "no_db"
                return stats

            row = conn.execute("SELECT COUNT(*) as cnt FROM query_history").fetchone()
            stats["query_count"] = row["cnt"] if row else 0

            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM knowledge_gaps WHERE resolution_status = 'open'"
            ).fetchone()
            stats["gap_count"] = row["cnt"] if row else 0

            row = conn.execute(
                "SELECT AVG(confidence) as avg_c FROM query_history"
            ).fetchone()
            stats["avg_confidence"] = round(row["avg_c"], 4) if row and row["avg_c"] else 0.0

            rows = conn.execute(
                "SELECT intent_predicted, COUNT(*) as cnt "
                "FROM query_history GROUP BY intent_predicted "
                "ORDER BY cnt DESC LIMIT 10"
            ).fetchall()
            stats["top_intents"] = [
                {"intent": r["intent_predicted"], "count": r["cnt"]} for r in rows
            ]

        except Exception as e:
            self._log_error("brain_stats", str(e))
            stats["status"] = "error"
        return stats

    def get_knowledge_gaps(self, limit: int = 20) -> dict:
        """Return unresolved knowledge gaps."""
        gaps = []
        try:
            conn = self._get_brain_db()
            if not conn:
                return {"gaps": gaps, "status": "no_db"}

            rows = conn.execute(
                "SELECT id, query_text, gap_type, resolution_status, created_at "
                "FROM knowledge_gaps WHERE resolution_status = 'open' "
                "ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            gaps = [
                {
                    "id": r["id"],
                    "query_text": r["query_text"],
                    "gap_type": r["gap_type"],
                    "created_at": r["created_at"],
                }
                for r in rows
            ]
        except Exception as e:
            self._log_error("brain_gaps", str(e))
        return {"gaps": gaps, "count": len(gaps), "status": "ok"}

    def resolve_gap(self, gap_id: int, note: str) -> dict:
        """Mark a knowledge gap as resolved."""
        try:
            conn = self._get_brain_db()
            if not conn:
                return {"resolved": False, "reason": "no_db"}

            conn.execute(
                "UPDATE knowledge_gaps SET resolution_status = 'resolved', "
                "resolution_note = ? WHERE id = ?",
                (note, gap_id),
            )
            conn.commit()
            return {"resolved": True, "gap_id": gap_id}
        except Exception as e:
            self._log_error("resolve_gap", str(e))
            return {"resolved": False, "reason": str(e)[:200]}

    # ── Context Window (Conversation Memory) ──────────────────────

    _FOLLOWUP_PREFIXES = (
        "what about", "and ", "also ", "how about", "tell me more",
    )
    _PRONOUN_PATTERN = re.compile(
        r"(?<!\w)(it|that|this|these|those|its|them)(?!\w)", re.IGNORECASE,
    )

    def _is_followup(self, text: str) -> bool:
        """Heuristic: does *text* look like a conversational follow-up?"""
        lower = text.lower().strip()
        if any(lower.startswith(p) for p in self._FOLLOWUP_PREFIXES):
            return True
        # Pronoun without a clear subject (very short query with pronoun)
        words = lower.split()
        if len(words) <= 8 and self._PRONOUN_PATTERN.search(lower):
            return True
        return False

    def _enrich_with_context(self, text: str) -> str:
        """Prepend context from the last query when a follow-up is detected."""
        if not self._context_window:
            return text
        last = self._context_window[-1]
        ctx_parts: list[str] = []
        if last.get("entities"):
            for _etype, vals in last["entities"].items():
                if vals:
                    ctx_parts.extend(vals if isinstance(vals, list) else [vals])
        if last.get("top_concept"):
            ctx_parts.append(last["top_concept"])
        if not ctx_parts and last.get("query"):
            ctx_parts.append(last["query"])
        if ctx_parts:
            prefix = " ".join(dict.fromkeys(ctx_parts))  # unique, ordered
            return f"[context: {prefix}] {text}"
        return text

    def _track_context(self, query: str, result: dict):
        """Append query metadata to the sliding context window (max 10)."""
        entry = {
            "query": query,
            "intent": result.get("intent", "unknown"),
            "entities": result.get("entities", {}),
            "top_concept": result["concepts"][0] if result.get("concepts") else None,
            "timestamp": time.time(),
        }
        self._context_window.append(entry)
        if len(self._context_window) > 10:
            self._context_window = self._context_window[-10:]

    def get_context(self) -> list[dict]:
        """Return the current conversation context window."""
        return list(self._context_window)

    def clear_context(self):
        """Reset the conversation context window."""
        self._context_window.clear()

    # ── Quality Feedback Loop ─────────────────────────────────────

    def _ensure_rating_column(self):
        """Add user_rating column to query_history if it doesn't exist yet."""
        try:
            conn = self._get_brain_db()
            if not conn:
                return
            # Safe ALTER — silently ignored if column already exists
            conn.execute(
                "ALTER TABLE query_history ADD COLUMN user_rating INTEGER DEFAULT NULL"
            )
            conn.commit()
        except Exception as e:
            logger.debug(f"Rating column check: {e}")  # column likely already exists

    def feedback(self, query_id: int, rating: int, comment: Optional[str] = None) -> dict:
        """Record user quality feedback for a prior query.

        Args:
            query_id: Row id in query_history.
            rating: 1 (useless) – 5 (perfect).
            comment: Optional free-text note.
        """
        rating = max(1, min(5, int(rating)))
        try:
            conn = self._get_brain_db()
            if not conn:
                return {"ok": False, "reason": "no_db"}

            self._ensure_rating_column()

            conn.execute(
                "UPDATE query_history SET user_rating = ? WHERE id = ?",
                (rating, query_id),
            )
            conn.commit()

            # Auto-add to knowledge_gaps when rating is poor
            if rating <= 2:
                row = conn.execute(
                    "SELECT query_text FROM query_history WHERE id = ?",
                    (query_id,),
                ).fetchone()
                if row:
                    gap_type = "low_user_rating"
                    if comment:
                        gap_type = f"low_user_rating: {comment[:120]}"
                    conn.execute(
                        "INSERT INTO knowledge_gaps (query_text, gap_type) VALUES (?, ?)",
                        (row["query_text"], gap_type),
                    )
                    conn.commit()

            return {"ok": True, "query_id": query_id, "rating": rating}
        except Exception as e:
            self._log_error("feedback", str(e))
            return {"ok": False, "reason": str(e)[:200]}

    def get_weak_areas(self) -> dict:
        """Identify intents with low confidence and/or low user ratings."""
        try:
            conn = self._get_brain_db()
            if not conn:
                return {"weak_areas": [], "status": "no_db"}

            self._ensure_rating_column()

            rows = conn.execute(
                "SELECT intent_predicted, "
                "  COUNT(*) AS total, "
                "  ROUND(AVG(confidence), 4) AS avg_confidence, "
                "  SUM(CASE WHEN user_rating IS NOT NULL AND user_rating <= 2 THEN 1 ELSE 0 END) AS low_ratings, "
                "  SUM(CASE WHEN user_rating IS NOT NULL THEN 1 ELSE 0 END) AS rated_count, "
                "  ROUND(AVG(CASE WHEN user_rating IS NOT NULL THEN user_rating END), 2) AS avg_rating "
                "FROM query_history "
                "GROUP BY intent_predicted "
                "HAVING total >= 1 "
                "ORDER BY avg_confidence ASC, low_ratings DESC"
            ).fetchall()

            areas = []
            for r in rows:
                weakness = (1.0 - (r["avg_confidence"] or 0.0))
                if r["rated_count"] and r["rated_count"] > 0:
                    weakness += (r["low_ratings"] or 0) / r["rated_count"]
                areas.append({
                    "intent": r["intent_predicted"],
                    "total_queries": r["total"],
                    "avg_confidence": r["avg_confidence"],
                    "low_ratings": r["low_ratings"] or 0,
                    "rated_count": r["rated_count"] or 0,
                    "avg_rating": r["avg_rating"],
                    "weakness_score": round(weakness, 4),
                })
            areas.sort(key=lambda x: x["weakness_score"], reverse=True)
            return {"weak_areas": areas, "status": "ok"}
        except Exception as e:
            self._log_error("get_weak_areas", str(e))
            return {"weak_areas": [], "status": "error", "detail": str(e)[:200]}

    def auto_diagnose(self) -> dict:
        """Analyse low-confidence queries against knowledge gaps and suggest improvements."""
        suggestions: list[dict] = []
        try:
            conn = self._get_brain_db()
            if not conn:
                return {"suggestions": suggestions, "status": "no_db"}

            self._ensure_rating_column()

            # 1. Patterns in low-confidence queries
            low_conf = conn.execute(
                "SELECT intent_predicted, COUNT(*) AS cnt, "
                "  ROUND(AVG(confidence), 4) AS avg_c "
                "FROM query_history WHERE confidence < 0.4 "
                "GROUP BY intent_predicted ORDER BY cnt DESC LIMIT 10"
            ).fetchall()

            for r in low_conf:
                suggestions.append({
                    "type": "low_confidence_intent",
                    "intent": r["intent_predicted"],
                    "occurrences": r["cnt"],
                    "avg_confidence": r["avg_c"],
                    "suggestion": (
                        f"Add more training data for intent='{r['intent_predicted']}' "
                        f"({r['cnt']} queries averaged {r['avg_c']:.1%} confidence)"
                    ),
                })

            # 2. Intents with poor user ratings
            poor_rated = conn.execute(
                "SELECT intent_predicted, COUNT(*) AS cnt, "
                "  ROUND(AVG(user_rating), 2) AS avg_r "
                "FROM query_history "
                "WHERE user_rating IS NOT NULL AND user_rating <= 2 "
                "GROUP BY intent_predicted ORDER BY cnt DESC LIMIT 10"
            ).fetchall()

            for r in poor_rated:
                suggestions.append({
                    "type": "poor_user_rating",
                    "intent": r["intent_predicted"],
                    "low_rated_count": r["cnt"],
                    "avg_rating": r["avg_r"],
                    "suggestion": (
                        f"Improve response quality for intent='{r['intent_predicted']}' "
                        f"({r['cnt']} queries rated avg {r['avg_r']}/5)"
                    ),
                })

            # 3. Cross-reference with open knowledge gaps
            gap_types = conn.execute(
                "SELECT gap_type, COUNT(*) AS cnt "
                "FROM knowledge_gaps WHERE resolution_status = 'open' "
                "GROUP BY gap_type ORDER BY cnt DESC LIMIT 10"
            ).fetchall()

            for r in gap_types:
                suggestions.append({
                    "type": "knowledge_gap_pattern",
                    "gap_type": r["gap_type"],
                    "occurrences": r["cnt"],
                    "suggestion": (
                        f"Resolve {r['cnt']} open '{r['gap_type']}' knowledge gaps "
                        "to improve coverage"
                    ),
                })

            return {"suggestions": suggestions, "count": len(suggestions), "status": "ok"}
        except Exception as e:
            self._log_error("auto_diagnose", str(e))
            return {"suggestions": [], "status": "error", "detail": str(e)[:200]}

    # ── Core Capabilities ─────────────────────────────────────────

    def classify_intent(self, text: str) -> tuple[str, float]:
        """Classify user intent. Returns (intent, confidence)."""
        if not self.vectorizer or not self.intent_clf:
            return "general", 0.0
        try:
            X = self.vectorizer.transform([text])
            probs = self.intent_clf.predict_proba(X)[0]
            idx = probs.argmax()
            return self.intent_le.inverse_transform([idx])[0], float(probs[idx])
        except Exception as e:
            logger.warning(f"Intent classification failed: {e}")
            return "general", 0.0

    def extract_entities(self, text: str) -> dict[str, list[str]]:
        """Extract legal entities from text."""
        entities = {}
        for name, pattern in self.entity_patterns.items():
            try:
                matches = pattern.findall(text)
                if matches:
                    if isinstance(matches[0], tuple):
                        entities[name] = [" ".join(m).strip() for m in matches]
                    else:
                        entities[name] = list(set(matches))
            except Exception as e:
                logger.debug(f"Entity extraction failed for pattern '{name}': {e}")
        return entities

    def retrieve(self, text: str, top_k: int = 10, label_filter: str = None) -> list[dict]:
        """Retrieve top-K most relevant documents.

        Fast path: uses inverted index when available and no label filter.
        Full path: cosine similarity against full TF-IDF matrix.
        """
        # Fast path via inverted index (no label filter)
        if self._inverted_index and not label_filter:
            try:
                fast_hits = self._inverted_index.fast_search(text, top_k=top_k * 2)
                if fast_hits:
                    results = []
                    for hit in fast_hits[:top_k]:
                        did = hit["doc_id"]
                        if did < len(self.corpus_labels):
                            results.append({
                                "score": round(hit["score"], 4),
                                "label": self.corpus_labels[did],
                                "text": self.corpus_texts[did] if did < len(self.corpus_texts) else "",
                                "meta": self.corpus_meta[did] if did < len(self.corpus_meta) else {},
                            })
                    if results:
                        return results
            except Exception as e:
                logger.debug(f"Inverted index fast path failed, falling back to cosine: {e}")

        if not self.vectorizer or self.tfidf_matrix is None:
            return []
        try:
            query_vec = self.vectorizer.transform([text])
            sims = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

            if label_filter:
                mask = np.array([l == label_filter for l in self.corpus_labels])
                sims = sims * mask

            top_idx = sims.argsort()[-top_k:][::-1]
            results = []
            # Dynamic threshold: use max(0.01, mean of top-k scores - 1 std)
            top_scores = sims[top_idx]
            if len(top_scores) > 1:
                score_threshold = max(0.005, float(np.mean(top_scores) - np.std(top_scores)))
            else:
                score_threshold = 0.005
            for idx in top_idx:
                if sims[idx] < score_threshold:
                    continue
                results.append({
                    "score": round(float(sims[idx]), 4),
                    "label": self.corpus_labels[idx] if idx < len(self.corpus_labels) else "unknown",
                    "text": self.corpus_texts[idx] if idx < len(self.corpus_texts) else "",
                    "meta": self.corpus_meta[idx] if idx < len(self.corpus_meta) else {},
                })
            return results
        except Exception as e:
            logger.warning(f"TF-IDF retrieval failed: {e}")
            return []

    def match_concepts(self, text: str) -> list[dict]:
        """Find matching legal concepts."""
        lower = text.lower()
        matches = []
        keywords_map = {
            "best_interest_factors": ["best interest", "722.23", "custody factor"],
            "established_custodial_environment": ["custodial environment", "722.27", "established"],
            "parental_alienation": ["alienation", "alienat", "722.23(j)", "factor j"],
            "change_of_circumstances": ["change of circumstances", "proper cause", "vodvarka"],
            "friend_of_court": ["friend of court", "foc", "552.501"],
            "summary_disposition": ["summary disposition", "2.116", "dismiss"],
            "disqualification": ["disqualif", "2.003", "bias", "recusal", "impartial"],
            "ppo": ["ppo", "protection order", "2950", "stalking"],
            "appeal_of_right": ["appeal", "7.204", "7.205", "claim of appeal"],
            "superintending_control": ["superintending", "3.302", "1701"],
            "motion_to_compel": ["compel", "discovery dispute", "2.313", "interrogator", "deposition"],
            "service_of_process": ["service of process", "2.105", "serve", "summons"],
            "parenting_time": ["parenting time", "722.27a", "visitation"],
            "contempt_of_court": ["contempt", "3.606", "violation of order", "custody order violation"],
            "due_process_custody": ["due process", "fundamental right", "liberty interest", "14th amendment", "troxel"],
            "guardian_ad_litem": ["guardian ad litem", "gal", "3.915", "722.24", "guardian appointment"],
            "hearsay_exceptions": ["hearsay", "hearsay exception", "803", "804", "mre 803", "mre 804", "excited utterance", "present sense", "business record"],
            "interrogatories_discovery": ["interrogatories", "interrogatory", "discovery request", "written discovery", "2.309"],
            "foc_objections": ["foc objection", "friend of court objection", "foc recommendation", "552.507", "de novo hearing"],
            "appeal_deadline": ["deadline filing appeal", "21 days", "claim of appeal deadline", "appeal time limit", "7.204(a)"],
            # ── MSC Original Actions & Multi-Jurisdiction ─────────
            "msc_superintending_control": ["superintending control", "7.306", "7.304", "writ of superintending", "supervisory authority", "excess of jurisdiction"],
            "msc_mandamus": ["mandamus", "writ of mandamus", "compel performance", "clear legal duty", "ministerial duty"],
            "msc_habeas_corpus": ["habeas corpus", "habeas", "unlawful restraint", "custody deprivation", "unlawful detention"],
            "msc_prohibition": ["writ of prohibition", "prohibition", "excess jurisdiction", "prevent lower court"],
            "msc_quo_warranto": ["quo warranto", "authority to hold office", "challenge authority"],
            "msc_declaratory_judgment": ["declaratory judgment", "declare rights", "actual controversy", "600.605"],
            "msc_emergency_application": ["emergency application", "immediate consideration", "7.315", "7.305(F)", "emergency relief"],
            "msc_original_action": ["original action", "original jurisdiction", "supreme court complaint", "msc complaint"],
            "federal_1983": ["1983", "section 1983", "42 usc", "civil rights", "under color of law", "deprivation of rights"],
            "federal_habeas": ["federal habeas", "28 usc 2254", "2241", "federal custody challenge"],
            "jtc_complaint": ["judicial tenure", "jtc", "9.200", "judicial misconduct", "judicial discipline"],
            "ex_parte_violation": ["ex parte", "without notice", "ex parte order", "3.207", "one-sided"],
            "parental_rights_fundamental": ["fundamental right", "parental rights", "troxel", "liberty interest", "strict scrutiny"],
            "mcneill_pattern": ["mcneill", "judge mcneill", "jenny mcneill", "biased judge"],
            "emily_watson_pattern": ["emily watson", "watson", "tiffany watson", "defendant watson", "opposing party"],
        }
        # Dynamically add concepts from JSON if they exist
        for concept_id in self.legal_concepts:
            if concept_id not in keywords_map:
                # Auto-generate keywords from the concept title
                title = self.legal_concepts[concept_id].get("title", "").lower()
                keywords_map[concept_id] = [w for w in title.split() if len(w) > 3]

        for concept_id, keywords in keywords_map.items():
            for kw in keywords:
                if kw in lower:
                    if concept_id in self.legal_concepts:
                        matches.append({
                            "id": concept_id,
                            **self.legal_concepts[concept_id],
                        })
                    break
        return matches

    def _db_lookup(self, intent: str, entities: dict, keywords: list[str]) -> list[dict]:
        """Direct DB lookups for precise answers."""
        results = []

        # ── Hot cache: auth_rules (sub-millisecond) ──────────
        hot_rules = self._hot_cache.get("auth_rules", {})
        if hot_rules and "mcr" in entities:
            for rule_ref in entities["mcr"][:3]:
                ref_lower = rule_ref.lower()
                for rn, data in hot_rules.items():
                    if ref_lower in rn.lower():
                        results.append({
                            "type": "court_rule",
                            "rule_number": rn,
                            "title": data.get("title", ""),
                            "text": (data.get("full_text") or "")[:1000],
                        })
                        break

        conn = self._get_db()
        if not conn:
            return results

        try:
            # MCR lookups (auth_rules table) — skip if hot cache already found them
            if "mcr" in entities and not any(r["type"] == "court_rule" for r in results):
                for rule_ref in entities["mcr"][:3]:
                    try:
                        row = conn.execute(
                            "SELECT rule_number, title, full_text FROM auth_rules "
                            "WHERE rule_number LIKE ? LIMIT 1",
                            (f"%{rule_ref}%",),
                        ).fetchone()
                        if row:
                            results.append({
                                "type": "court_rule",
                                "rule_number": row["rule_number"],
                                "title": row["title"],
                                "text": row["full_text"][:1000],
                            })
                    except Exception as e:
                        logger.debug(f"MCR lookup failed: {e}")

            # MCL lookups (rules_text table)
            if "mcl" in entities:
                for mcl_ref in entities["mcl"][:3]:
                    try:
                        rows = conn.execute(
                            "SELECT id, rule, context FROM rules_text "
                            "WHERE rule LIKE ? OR context LIKE ? LIMIT 3",
                            (f"%{mcl_ref}%", f"%{mcl_ref}%"),
                        ).fetchall()
                        for row in rows:
                            results.append({
                                "type": "statute",
                                "statute_id": row["rule"] or str(row["id"]),
                                "text": (row["context"] or "")[:1000],
                            })
                    except Exception as e:
                        logger.debug(f"MCL lookup failed: {e}")

            # Case citation lookups (master_citations table)
            if "case_name" in entities or "case_cite" in entities:
                search_terms = []
                if "case_name" in entities:
                    search_terms.extend(entities["case_name"][:3])
                if "case_cite" in entities:
                    search_terms.extend(entities["case_cite"][:3])
                for term in search_terms[:3]:
                    try:
                        first_word = term.split()[0] if term else ""
                        rows = conn.execute(
                            "SELECT citation, cite_type, context, source_file "
                            "FROM master_citations "
                            "WHERE citation LIKE ? OR context LIKE ? LIMIT 3",
                            (f"%{first_word}%", f"%{first_word}%"),
                        ).fetchall()
                        for row in rows:
                            results.append({
                                "type": "case_law",
                                "citation": row["citation"],
                                "case_name": "",
                                "court": row["cite_type"] or "",
                                "year": "",
                                "holding": (row["context"] or "")[:500],
                            })
                    except Exception as e:
                        logger.debug(f"Case citation lookup failed: {e}")

            # Keyword search in authority passages (auth_authority_passages)
            if keywords and not results:
                try:
                    kw = keywords[0].replace("'", "''")
                    raw_sql = (
                        f"SELECT passage_text, section, source_file "
                        f"FROM auth_authority_passages "
                        f"WHERE passage_text LIKE '%{kw}%' LIMIT 5"
                    )
                    opt_sql, opt_params = self._rewrite_sql(raw_sql)
                    rows = conn.execute(opt_sql, opt_params or ()).fetchall()
                    for row in rows:
                        results.append({
                            "type": "authority_passage",
                            "citation": row["section"] or "",
                            "text": row["passage_text"][:500],
                            "holding_type": "",
                        })
                except Exception as e:
                    logger.debug(f"Authority passage search failed: {e}")

            # Keyword search in auth_rules FTS
            if keywords and len(results) < 3:
                try:
                    fts_q = " OR ".join(keywords[:3])
                    rows = conn.execute(
                        "SELECT rule_number, title, substr(full_text, 1, 500) as excerpt "
                        "FROM auth_rules WHERE rowid IN "
                        "(SELECT rowid FROM auth_rules_fts WHERE auth_rules_fts MATCH ?) "
                        "LIMIT 5",
                        (fts_q,),
                    ).fetchall()
                    for row in rows:
                        results.append({
                            "type": "court_rule",
                            "rule_number": row["rule_number"],
                            "title": row["title"],
                            "text": row["excerpt"],
                        })
                except Exception as e:
                    logger.debug(f"Auth rules FTS search failed: {e}")

            # Filing/motion keyword search in md_sections and documents
            if intent in ("filings", "strategy") or any(
                kw in " ".join(keywords).lower()
                for kw in ["motion", "compel", "dismiss", "suppress", "brief", "petition", "complaint", "filing"]
            ):
                for kw in keywords[:3]:
                    try:
                        kw_safe = kw.replace("'", "''")
                        rows = conn.execute(
                            "SELECT section_title, substr(content, 1, 600) as excerpt, source_file "
                            "FROM md_sections "
                            "WHERE section_title LIKE ? OR content LIKE ? LIMIT 5",
                            (f"%{kw_safe}%", f"%{kw_safe}%"),
                        ).fetchall()
                        for row in rows:
                            results.append({
                                "type": "filing_section",
                                "title": row["section_title"] or "Filing",
                                "text": row["excerpt"],
                                "source": row["source_file"] or "",
                            })
                    except Exception as e:
                        logger.debug(f"Filing search failed: {e}")

            # Broad keyword search across all tables when results still sparse
            if len(results) < 2 and keywords:
                for kw in keywords[:2]:
                    try:
                        kw_safe = kw.replace("'", "''")
                        # Search legal_reference_docs
                        rows = conn.execute(
                            "SELECT heading, substr(body, 1, 500) as excerpt, source_file "
                            "FROM legal_reference_docs "
                            "WHERE heading LIKE ? OR body LIKE ? LIMIT 3",
                            (f"%{kw_safe}%", f"%{kw_safe}%"),
                        ).fetchall()
                        for row in rows:
                            results.append({
                                "type": "legal_reference",
                                "title": row["heading"] or "Reference",
                                "text": row["excerpt"],
                                "source": row["source_file"] or "",
                            })
                    except Exception as e:
                        logger.debug(f"Broad keyword search failed: {e}")

        except Exception as e:
            logger.error(f"DB lookup failed for intent='{intent}': {e}")

        return results

    # ── Response Generation ───────────────────────────────────────

    def _build_response(
        self,
        query: str,
        intent: str,
        confidence: float,
        entities: dict,
        concepts: list,
        retrieved: list,
        db_results: list,
        patterns: list = None,
        lawyer_analysis: dict = None,
    ) -> str:
        """Assemble a comprehensive response from all components with lawyer mode."""
        parts = []

        # Header with case context
        parts.append(f"**[MANBEARPIG -- {intent.upper()} | confidence {confidence:.0%}]**")
        parts.append(f"*Pigors v. Watson | Michigan-First Jurisdiction*\n")

        # Direct DB results (highest priority -- most accurate)
        if db_results:
            parts.append("## Governing Authority\n")
            for r in db_results[:7]:
                if r["type"] == "court_rule":
                    parts.append(f"### {r['rule_number']} -- {r['title']}")
                    parts.append(f"{r['text']}")
                    parts.append(f"*Source: Michigan Court Rules*\n")
                elif r["type"] == "statute":
                    parts.append(f"### {r['statute_id']}")
                    parts.append(f"{r['text']}")
                    parts.append(f"*Source: Michigan Compiled Laws*\n")
                elif r["type"] == "case_law":
                    parts.append(f"### *{r['case_name']}* -- {r['citation']}")
                    if r.get("court"):
                        parts.append(f"*{r['court']}*" + (f" ({r['year']})" if r.get("year") else ""))
                    if r.get("holding"):
                        parts.append(f"\n**Holding:** {r['holding']}\n")
                elif r["type"] == "authority_passage":
                    parts.append(f"### {r.get('citation', 'Authority')}")
                    parts.append(f"{r['text']}\n")
                elif r["type"] in ("filing_section", "legal_reference"):
                    parts.append(f"### {r.get('title', 'Document')}")
                    if r.get("source"):
                        parts.append(f"*Source: {r['source']}*")
                    parts.append(f"{r['text']}\n")

        # Legal concepts (if matched)
        if concepts:
            parts.append("## Legal Framework\n")
            for c in concepts[:4]:
                parts.append(f"### {c.get('title', c['id'])}")
                parts.append(f"**Governing Authority:** {c.get('authority', 'N/A')}")
                if "factors" in c:
                    parts.append("**Factors:**")
                    for factor in c["factors"]:
                        parts.append(f"  - {factor}")
                elif "description" in c:
                    parts.append(c["description"])
                parts.append("")

        # Lawyer Mode Analysis
        if lawyer_analysis:
            la = lawyer_analysis
            has_content = any([la.get("issues_spotted"), la.get("recommended_actions"),
                              la.get("standard_of_review"), la.get("risk_assessment")])
            if has_content:
                parts.append("## Legal Analysis\n")
                if la.get("standard_of_review"):
                    parts.append(f"**Standard of Review:** {la['standard_of_review']}\n")
                if la.get("issues_spotted"):
                    parts.append("**Issues Identified:**")
                    for issue in la["issues_spotted"][:8]:
                        parts.append(f"  - {issue}")
                    parts.append("")
                if la.get("risk_assessment"):
                    parts.append(f"**Risk Assessment:** {la['risk_assessment']}\n")
                if la.get("applicable_authority"):
                    parts.append("**Applicable Authority:**")
                    for auth in la["applicable_authority"][:6]:
                        parts.append(f"  - {auth}")
                    parts.append("")
                if la.get("recommended_actions"):
                    parts.append("**Recommended Next Steps:**")
                    for i, action in enumerate(la["recommended_actions"], 1):
                        parts.append(f"  {i}. {action}")
                parts.append("")

        # Pattern Detection
        if patterns:
            parts.append("## Procedural Patterns Detected\n")
            for p in patterns[:7]:
                parts.append(f"  - {p}")
            parts.append("")

        # Retrieved corpus passages (TF-IDF similarity)
        if retrieved:
            shown = 5 if not db_results else 3
            parts.append("## Supporting Passages\n")
            for r in retrieved[:shown]:
                score = r["score"]
                label = r["label"]
                meta = r.get("meta", {})
                header = meta.get("rule", meta.get("citation", meta.get("title", label)))
                parts.append(f"**[{header}]** (relevance: {score:.2f})")
                text = r["text"][:500]
                parts.append(f"{text}{'...' if len(r['text']) > 500 else ''}\n")

        # Entity summary
        if entities:
            entity_strs = []
            for etype, vals in entities.items():
                entity_strs.append(f"  {etype}: {', '.join(vals[:3])}")
            parts.append("## Entities Detected")
            parts.extend(entity_strs)
            parts.append("")

        # If absolutely nothing found
        if not db_results and not concepts and not retrieved:
            parts.append("No direct matches found in the legal database.\n")
            parts.append("**Try:**")
            parts.append("- Specific MCR references: *\"MCR 2.003 disqualification\"*")
            parts.append("- Statute lookups: *\"MCL 722.27 custody modification\"*")
            parts.append("- Case law: *\"Vodvarka parenting time\"*")
            parts.append("- Legal concepts: *\"best interest factors\"*")
            parts.append(f"\n*Model: {self.manifest.get('model_name', 'MLLM')} | "
                         f"Corpus: {self.manifest.get('corpus_size', 0):,} docs | "
                         f"Vocab: {self.manifest.get('vocab_size', 0):,} terms*")

        return "\n".join(parts)

    # ── Main Query Interface ──────────────────────────────────────

    def query(self, text: str) -> dict:
        """
        Process a natural language query. Returns structured response.
        CANNOT fail — always returns a valid response dict.
        Self-healing: auto-reconnects DB, reloads model components on failure.
        Caching: repeated queries return instantly.
        """
        t0 = time.time()

        # Cache check (hash-based for efficiency)
        cache_key = hashlib.md5(text.strip().lower().encode("utf-8", errors="replace")).hexdigest()
        if cache_key in self._cache:
            cached = self._cache[cache_key].copy()
            cached["elapsed_ms"] = 0.1
            cached["cached"] = True
            self._log_to_brain(text, cached)
            return cached

        # Context window: enrich follow-up queries with prior context
        if self._is_followup(text) and self._context_window:
            text = self._enrich_with_context(text)

        try:
            # 1. Classify intent (with self-heal)
            intent, confidence = self.classify_intent(text)
            if intent == "general" and confidence == 0.0 and self.intent_clf is None:
                if self._self_heal("intent_clf"):
                    intent, confidence = self.classify_intent(text)

            # 2. Extract entities
            entities = self.extract_entities(text)

            # 3. Match legal concepts
            concepts = self.match_concepts(text)

            # 4. Extract keywords for fallback search (with stemming)
            stop = {
                "the", "a", "an", "is", "are", "was", "were", "be", "been",
                "have", "has", "had", "do", "does", "did", "will", "would",
                "could", "should", "may", "might", "shall", "can", "to", "of",
                "in", "for", "on", "with", "at", "by", "from", "as", "what",
                "how", "when", "where", "why", "which", "who", "about", "this",
                "that", "and", "or", "but", "not", "if", "my", "me", "i",
            }
            raw_keywords = [
                w for w in re.sub(r"[^a-z0-9\s.]", " ", text.lower()).split()
                if len(w) > 2 and w not in stop
            ]
            # Expand keywords with stems so "disqualification" also matches "disqualify"
            keywords = list(raw_keywords)
            for w in raw_keywords:
                stem = self._stem_word(w)
                if stem and stem != w and stem not in keywords:
                    keywords.append(stem)

            # 5. Retrieve from TF-IDF corpus (with self-heal)
            label_filter = None
            if confidence > 0.6 and intent in (
                "court_rules", "case_law", "filings", "evidence", "statutes"
            ):
                intent_to_label = {
                    "court_rules": "court_rule",
                    "case_law": "case_law",
                    "filings": "filing",
                    "evidence": "evidence",
                    "statutes": "court_rule",
                }
                label_filter = intent_to_label.get(intent)

            # 5a. EPOCH v5.0: Query expansion for better recall
            expanded_text = text
            try:
                from query_expander import QueryExpander
                _qe = QueryExpander()
                expanded_text = _qe.expand(text)
            except Exception:
                pass  # Query expander unavailable

            retrieved = self.retrieve(expanded_text, top_k=10, label_filter=label_filter)
            if not retrieved and self.tfidf_matrix is None:
                if self._self_heal("tfidf_matrix"):
                    retrieved = self.retrieve(expanded_text, top_k=10, label_filter=label_filter)

            # 5b. EPOCH v5.0: Hybrid retrieval (BM25S + Semantic + FTS5 via RRF)
            try:
                from hybrid_retriever import HybridRetriever
                _hybrid = HybridRetriever()
                hybrid_hits = _hybrid.search(text, top_k=8)
                if hybrid_hits:
                    seen = {r.get("text", "")[:100] for r in retrieved}
                    for h in hybrid_hits:
                        snippet = h.get("text", "")[:100]
                        if snippet not in seen:
                            retrieved.append({
                                "text": h.get("text", ""),
                                "score": h.get("score", 0.0),
                                "source": h.get("source", "hybrid"),
                                "label": h.get("table", "hybrid"),
                            })
                            seen.add(snippet)
            except Exception:
                pass  # Hybrid retriever unavailable — TF-IDF only

            # 6. Direct DB lookups (with self-heal)
            db_results = self._db_lookup(intent, entities, keywords)
            if not db_results and not self._get_db():
                if self._self_heal("db_connection"):
                    db_results = self._db_lookup(intent, entities, keywords)

            # 7. Detect patterns in the query
            patterns = self._detect_patterns(text, intent, entities)

            # 8. Lawyer mode analysis
            lawyer_analysis = self._lawyer_mode(text, intent, entities, concepts, db_results)

            # 8b. Boost confidence using evidence-quality signals
            confidence = self._boost_confidence(
                confidence, entities, db_results, retrieved,
                concepts, patterns, lawyer_analysis,
            )

            # 9. EPOCH: Rerank retrieved results for quality
            try:
                from reranker import Reranker
                _rr = Reranker()
                if len(retrieved) > 3:
                    reranked = _rr.rerank(text, [r.get("text", "") for r in retrieved], top_k=10)
                    if reranked:
                        score_map = {r.get("text", "")[:80]: r.get("score", 0) for r in reranked}
                        retrieved.sort(key=lambda r: score_map.get(r.get("text", "")[:80], 0), reverse=True)
            except Exception:
                pass  # Reranker unavailable — use original order

            # 10. Build response (enriched with patterns + lawyer analysis)
            response_text = self._build_response(
                text, intent, confidence, entities, concepts, retrieved, db_results,
                patterns=patterns, lawyer_analysis=lawyer_analysis
            )

            elapsed = time.time() - t0
            result = {
                "response": response_text,
                "intent": intent,
                "confidence": round(confidence, 3),
                "entities": entities,
                "concepts": [c.get("id", "") for c in concepts],
                "patterns": patterns,
                "retrieval_count": len(retrieved),
                "db_match_count": len(db_results),
                "elapsed_ms": round(elapsed * 1000, 1),
                "model": self.manifest.get("model_name", "THE-MANBEARPIG-v3.0"),
                "status": "ok",
                "cached": False,
            }

            # Cache the result
            self._cache[cache_key] = result
            if len(self._cache) > 1000:
                oldest = list(self._cache.keys())[:500]
                for k in oldest:
                    del self._cache[k]

            # Log to persistent brain (non-blocking)
            self._log_to_brain(text, result)

            # Track in conversation context window
            self._track_context(text, result)

            return result

        except Exception as e:
            self._log_error("query", str(e))
            # Attempt full self-heal cycle
            for comp in ["db_connection", "vectorizer", "tfidf_matrix", "intent_clf"]:
                self._self_heal(comp)

            elapsed = time.time() - t0
            return {
                "response": (
                    f"**[MANBEARPIG — SELF-HEALING MODE]**\n\n"
                    f"Encountered issue: {str(e)[:100]}\n"
                    f"Auto-heal attempted for: db_connection, vectorizer, tfidf_matrix, intent_clf\n\n"
                    "The model is recovering. Please retry your query. If the issue persists, "
                    "run `python train_model.py` to rebuild the model.\n\n"
                    "**Try:** Specific MCR/MCL references, case names, or legal concepts."
                ),
                "intent": "error_recovery",
                "confidence": 0.0,
                "entities": {},
                "concepts": [],
                "patterns": [],
                "retrieval_count": 0,
                "db_match_count": 0,
                "elapsed_ms": round((time.time() - t0) * 1000, 1),
                "model": "MANBEARPIG-self-healing",
                "status": "healing",
                "cached": False,
                "error_report": self.get_error_report(),
            }

    def _detect_patterns(self, text: str, intent: str, entities: dict) -> list[str]:
        """Detect legal patterns, procedural issues, and strategic opportunities."""
        patterns = []
        lower = text.lower()
        try:
            # Procedural violation patterns
            violation_signals = {
                "no hearing": "PATTERN: Potential due process violation — action taken without hearing",
                "without notice": "PATTERN: Notice violation — MCR 2.107 requires proper notice",
                "ex parte": "PATTERN: Ex parte communication concern — MCR 2.119(H)",
                "no findings": "PATTERN: Court failed to make required findings of fact — MCR 2.517",
                "no evidence": "PATTERN: Decision without evidentiary support — clear error standard",
                "denied access": "PATTERN: Possible denial of access to courts — Const Art I, §13",
                "separated from child": "PATTERN: Parental separation — fundamental liberty interest (Troxel)",
                "refused parenting time": "PATTERN: Parenting time denial — MCL 722.27a violation",
                "changed custody without": "PATTERN: Custody modification without proper cause — Vodvarka",
                "bias": "PATTERN: Judicial bias indicator — MCR 2.003(C)(1) disqualification",
                "predetermined": "PATTERN: Predetermined outcome — due process violation",
                "ignored evidence": "PATTERN: Court failed to consider evidence — abuse of discretion",
                "false allegation": "PATTERN: False allegations — relevant to MCL 722.23(j) and credibility",
                "perjur": "PATTERN: Possible perjury — MCL 750.423",
                "fraud": "PATTERN: Fraud on the court — MCR 2.612(C)(1)(c)",
                "conflict of interest": "PATTERN: Conflict of interest — Canon 2, MCJC",
                "retaliat": "PATTERN: Retaliatory action — constitutional violation",
                "violated order": "PATTERN: Contempt — MCR 3.606",
                "alienat": "PATTERN: Parental alienation — MCL 722.23(j) factor",
                "coached": "PATTERN: Child coaching — credibility issue, MCL 722.23(j)",
                "gatekeeper": "PATTERN: Gatekeeping behavior — relevant to custody factors",
                "no investigation": "PATTERN: FOC failed to investigate — MCL 552.505 duty",
            }

            for signal, pattern_desc in violation_signals.items():
                if signal in lower:
                    patterns.append(pattern_desc)

            # Multi-signal pattern detection (compound issues)
            if "custody" in lower and ("no hearing" in lower or "without hearing" in lower):
                patterns.append("CRITICAL: Custody change without hearing — Stanley v. Illinois, Mathews v. Eldridge")
            if "appeal" in lower and "deadline" in lower:
                patterns.append("DEADLINE: Appeal must be filed within 21 days — MCR 7.204(A)(1)")
            if "contempt" in lower and "parenting" in lower:
                patterns.append("ENFORCEMENT: Parenting time contempt — MCR 3.606, show cause hearing required")
            if ("motion" in lower and "denied" in lower) or "overruled" in lower:
                patterns.append("STRATEGY: Consider interlocutory appeal under MCR 7.205 or motion for reconsideration under MCR 2.119(F)")

            # Entity-based pattern detection
            if entities.get("mcr"):
                for rule in entities["mcr"]:
                    if "2.003" in rule:
                        patterns.append("FLAG: Disqualification motion — must file timely, specific factual basis required")
                    if "2.116" in rule:
                        patterns.append("FLAG: Summary disposition — verify all evidence viewed in light most favorable to nonmovant")
                    if "7.204" in rule or "7.205" in rule:
                        patterns.append("FLAG: Appellate action — check preservation of issues, standard of review")
                    if "7.306" in rule or "7.304" in rule:
                        patterns.append("MSC: Original action — superintending control/mandamus via MCR 7.306")
                    if "7.305" in rule:
                        patterns.append("MSC: Application for leave to appeal — bypass COA via MCR 7.305")
                    if "3.207" in rule:
                        patterns.append("CRITICAL: Ex parte procedure — MCR 3.207(C)(2) requires immediate danger showing")
                    if "9.200" in rule or "9.202" in rule:
                        patterns.append("JTC: Judicial discipline — formal complaint under MCR 9.200")

            # MSC Original Action patterns
            msc_signals = {
                "original jurisdiction": "MSC: Original jurisdiction invoked — Const 1963 art 6 § 4",
                "superintending control": "MSC: Superintending control — MCR 7.306; no adequate remedy + systemic error",
                "mandamus": "MSC: Mandamus — clear legal duty + clear legal right + no adequate remedy",
                "habeas corpus": "MSC: Habeas corpus — challenge unlawful custody deprivation (Const art 1 § 12)",
                "writ of prohibition": "MSC: Prohibition — prevent lower court from exceeding jurisdiction",
                "quo warranto": "MSC: Quo warranto — challenge officer authority (MCL 600.4501)",
                "declaratory judgment": "MSC: Declaratory judgment — actual controversy re rights (MCL 600.605)",
                "42 usc 1983": "FEDERAL: § 1983 civil rights action — deprivation under color of law",
                "section 1983": "FEDERAL: § 1983 civil rights action — deprivation under color of law",
                "civil rights": "FEDERAL: Constitutional rights violation — 14th Amendment due process/equal protection",
            }
            for signal, desc in msc_signals.items():
                if signal in lower:
                    patterns.append(desc)

            # McNeill/Emily specific patterns
            if "mcneill" in lower or "judge mcneill" in lower:
                patterns.append("TARGET: Judge McNeill — 1,127 documented violations (377 critical)")
                patterns.append("STRATEGY: MSC superintending control + mandamus + JTC complaint + COA appeal")
            if "emily" in lower or "watson" in lower:
                patterns.append("TARGET: Emily Watson — PPO weaponization, false allegations, parenting time obstruction")
                patterns.append("STRATEGY: Contempt (MCR 3.606) + § 1983 conspiracy + MCL 722.23(j) factor")

            # Multi-jurisdiction escalation patterns
            if ("federal" in lower or "1983" in lower) and ("state" in lower or "michigan" in lower):
                patterns.append("MULTI-JURISDICTION: State + federal parallel filing strategy detected")
            if "appeal" in lower and "supreme court" in lower:
                patterns.append("ESCALATION: Direct MSC review — MCR 7.305 or 7.306 original action")

        except Exception as e:
            self._log_error("pattern_detection", str(e))

        return patterns[:10]  # cap at 10 patterns

    def _lawyer_mode(self, text: str, intent: str, entities: dict,
                     concepts: list, db_results: list) -> dict:
        """
        Lawyer Mode: Analyze query from a practicing attorney's perspective.
        Returns strategic analysis with issue-spotting, authority mapping,
        and recommended next steps.
        """
        analysis = {
            "issues_spotted": [],
            "applicable_authority": [],
            "recommended_actions": [],
            "risk_assessment": "",
            "procedural_posture": "",
            "standard_of_review": "",
        }
        lower = text.lower()

        try:
            # Issue spotting
            issue_map = {
                "custody": ["Best interest factors (MCL 722.23)", "Established custodial environment (MCL 722.27(1)(c))", "Change of circumstances (Vodvarka)"],
                "parenting time": ["MCL 722.27a parenting time rights", "Presumption of relationship with both parents", "Endangerment standard for restriction"],
                "contempt": ["MCR 3.606 contempt proceedings", "Clear and unambiguous order requirement", "Ability to comply defense"],
                "appeal": ["Preservation of issues", "Standard of review applicable", "Timeliness under MCR 7.204"],
                "disqualif": ["MCR 2.003(C) grounds", "Timeliness of motion", "Factual basis specificity"],
                "ppo": ["MCL 600.2950 requirements", "Due process rights of respondent", "Modification/termination hearing"],
                "discovery": ["MCR 2.302-2.316 scope", "Motion to compel under MCR 2.313(A)", "Sanctions for non-compliance"],
                "motion": ["MCR 2.119 motion practice", "Brief and notice requirements", "Response timeline"],
                "evidence": ["MRE relevance (401-403)", "Hearsay exceptions (803-804)", "Authentication (901-903)"],
                "due process": ["14th Amendment liberty interest", "Mathews v. Eldridge balancing", "Notice and opportunity to be heard"],
                "bias": ["MCR 2.003(C)(1) bias/prejudice", "Appearance of impropriety (Canon 2)", "JTC complaint if warranted"],
                "alienat": ["MCL 722.23(j) factor analysis", "Lombardo v. Lombardo", "Evidence gathering strategies"],
            }

            for keyword, issues in issue_map.items():
                if keyword in lower:
                    analysis["issues_spotted"].extend(issues)

            # Authority mapping from DB results
            for r in db_results[:5]:
                if r["type"] == "court_rule":
                    analysis["applicable_authority"].append(f"{r['rule_number']} - {r.get('title', '')}")
                elif r["type"] == "statute":
                    analysis["applicable_authority"].append(r.get("statute_id", ""))
                elif r["type"] == "case_law":
                    analysis["applicable_authority"].append(r.get("citation", ""))

            # Standard of review
            review_map = {
                "custody": "Abuse of discretion (findings of fact reviewed for clear error)",
                "parenting time": "Abuse of discretion",
                "contempt": "Clear error for findings; abuse of discretion for sanctions",
                "evidence": "Abuse of discretion for evidentiary rulings",
                "summary disposition": "De novo review",
                "constitutional": "De novo review",
                "due process": "De novo review of constitutional questions",
                "statutory interpretation": "De novo review",
                "discovery": "Abuse of discretion",
            }
            for key, review in review_map.items():
                if key in lower:
                    analysis["standard_of_review"] = review
                    break

            # Recommended actions based on intent
            action_map = {
                "court_rules": ["Research rule text thoroughly", "Check for recent amendments", "Review case law interpreting this rule"],
                "filings": ["Draft with IRAC structure", "Verify all citations", "Include certificate of service", "File proof of service"],
                "case_law": ["Shepardize/update citation", "Check for distinguishing facts", "Review concurrences and dissents"],
                "evidence": ["Authenticate under MRE 901-903", "Prepare foundation questions", "Anticipate hearsay objections"],
                "strategy": ["Evaluate all available vehicles", "Assess deadline pressure", "Consider parallel filings"],
                "deadlines": ["Calendar all deadlines", "Set reminder 7 days before", "Identify tolling/extension options"],
                "judicial": ["Document specific instances", "File motion to disqualify (MCR 2.003)", "Consider JTC complaint",
                             "File MSC superintending control (MCR 7.306)", "File 42 USC § 1983 federal action"],
            }
            # MSC-specific action recommendations
            if "superintending" in lower or "mandamus" in lower or "original action" in lower:
                analysis["recommended_actions"] = [
                    "File MCR 7.306 complaint in Michigan Supreme Court",
                    "Include emergency application (MCR 7.315(C))",
                    "Pair superintending control + mandamus + declaratory judgment",
                    "Prepare supporting brief (MCR 7.312)",
                    "Document systemic pattern (not isolated error)",
                    "Demonstrate no adequate remedy at law",
                ]
            elif "1983" in lower or "federal" in lower:
                analysis["recommended_actions"] = [
                    "File 42 USC § 1983 complaint in USDC W.D. Michigan",
                    "Seek prospective injunctive relief (Pulliam v Allen)",
                    "Document constitutional violations with specificity",
                    "Consider IFP motion (28 USC § 1915)",
                    "Parallel state MSC action for comprehensive coverage",
                ]
            elif intent in action_map:
                analysis["recommended_actions"] = action_map[intent]

            # Risk assessment
            if "deadline" in lower or "time limit" in lower or "overdue" in lower:
                analysis["risk_assessment"] = "HIGH — Deadline-sensitive. Missing deadlines can result in waiver of rights."
            elif "appeal" in lower:
                analysis["risk_assessment"] = "HIGH — Appellate deadlines are jurisdictional and cannot be extended."
            elif "contempt" in lower:
                analysis["risk_assessment"] = "MEDIUM — Contempt can result in sanctions including jail. Ensure due process."
            elif "custody" in lower:
                analysis["risk_assessment"] = "HIGH — Custody matters affect fundamental parental rights."
            else:
                analysis["risk_assessment"] = "MODERATE — Standard litigation risk. Follow procedural requirements carefully."

            # ── Procedural posture ──────────────────────────────
            posture = "General"
            basis = "Default — no specific procedural indicators detected"
            next_step = "Identify the procedural stage and applicable rules"

            entity_strs = " ".join(str(v) for v in entities.values() if v)
            concept_strs = " ".join(str(c) for c in concepts) if concepts else ""
            combined = lower + " " + entity_strs.lower() + " " + concept_strs.lower()

            if any(kw in combined for kw in ("emergency", "immediate", "irreparable harm",
                                              "ex parte emergency", "tro")):
                posture = "Emergency"
                basis = "Emergency/irreparable-harm language detected"
                next_step = "File emergency motion with MCR 2.119(F) affidavit; request ex parte relief if notice impracticable"
            elif any(kw in combined for kw in ("jtc", "judicial tenure", "misconduct complaint",
                                                "judicial misconduct")):
                posture = "JTC"
                basis = "Judicial Tenure Commission complaint language detected"
                next_step = "Prepare JTC complaint per MCR 9.200 series; document specific conduct violations with dates"
            elif any(kw in combined for kw in ("msc", "supreme court", "superintending",
                                                "mandamus", "original action")):
                posture = "MSC Original Action"
                basis = "Michigan Supreme Court / superintending control language detected"
                next_step = "Draft MCR 7.306 complaint for superintending control; pair with emergency application MCR 7.315(C)"
            elif any(kw in combined for kw in ("federal", "1983", "usdc", "section 1983",
                                                "42 usc")):
                posture = "Federal"
                basis = "Federal court / § 1983 language detected"
                next_step = "Draft 42 USC § 1983 complaint for USDC W.D. Michigan; consider IFP motion (28 USC § 1915)"
            elif ("appeal_of_right" in concept_strs.lower()
                  or any(kw in combined for kw in ("mcr 7.2", "claim of appeal",
                                                    "court of appeals", "coa"))):
                posture = "Appellate"
                basis = "Appeal-of-right / COA indicators detected"
                next_step = "Verify claim of appeal filed per MCR 7.204; prepare appellant brief per MCR 7.212"
            elif any(kw in combined for kw in ("appeal", "reconsideration", "judgment",
                                                "post-judgment", "post judgment")):
                posture = "Post-trial"
                basis = "Post-trial/post-judgment language detected"
                next_step = "Evaluate MCR 2.119(F) reconsideration or MCR 7.204 appeal; check 21-day and 42-day deadlines"
            elif any(kw in combined for kw in ("hearing", "testimony", "witness", "trial",
                                                "examination", "exhibit")):
                posture = "Trial"
                basis = "Trial/hearing-phase language detected"
                next_step = "Prepare witness list, exhibit list, and trial brief per MCR 2.501; file pretrial statement"
            elif any(kw in combined for kw in ("discovery", "interrogator", "deposition",
                                                "request for production", "subpoena",
                                                "rfp", "rog")):
                posture = "Pre-trial"
                basis = "Discovery/pre-trial language detected"
                next_step = "Serve discovery per MCR 2.302-2.316; calendar response deadlines (28 days for interrogatories)"

            analysis["procedural_posture"] = {
                "posture": posture,
                "basis": basis,
                "recommended_next_step": next_step,
            }

            # Deduplicate
            analysis["issues_spotted"] = list(dict.fromkeys(analysis["issues_spotted"]))[:8]
            analysis["applicable_authority"] = list(dict.fromkeys(analysis["applicable_authority"]))[:8]

        except Exception as e:
            self._log_error("lawyer_mode", str(e))

        return analysis

    # ── Confidence Boosting ───────────────────────────────────────

    def _boost_confidence(
        self,
        raw_confidence: float,
        entities: dict,
        db_results: list,
        retrieved: list,
        concepts: list,
        patterns: list,
        lawyer_analysis: dict,
    ) -> float:
        """
        Recalibrate confidence using evidence-quality signals.

        Raw NB/TF-IDF scores are systematically low (rarely > 0.3).
        This boosts confidence based on what the pipeline *actually found*.
        """
        conf = raw_confidence

        # Signal 1: Exact rule/statute match in DB → 0.95
        if any(r.get("type") in ("court_rule", "statute") for r in db_results):
            conf = max(conf, 0.95)

        # Signal 2: Entity has MCR/MCL/MRE AND DB returned results → 0.90
        elif any(k in entities for k in ("mcr", "mcl", "mre")) and db_results:
            conf = max(conf, 0.90)

        # Signal 2b: Substantial DB coverage (3+ results of any type) → 0.70
        elif len(db_results) >= 3:
            conf = max(conf, 0.70)

        # Signal 3: Top TF-IDF similarity > 0.3 → scale into 0.70-0.85
        if retrieved:
            top_score = max(r["score"] for r in retrieved)
            if top_score > 0.3:
                scaled = 0.70 + (top_score - 0.3) / 0.70 * 0.15
                conf = max(conf, min(scaled, 0.85))

        # Signal 4: Concept match → +0.10
        if concepts:
            conf = min(conf + 0.10, 0.99)

        # Signal 5: Lawyer-mode produced substantive analysis → +0.05
        if patterns or (
            lawyer_analysis
            and (
                lawyer_analysis.get("issues_spotted")
                or lawyer_analysis.get("recommended_actions")
            )
        ):
            conf = min(conf + 0.05, 0.99)

        # Floor / cap
        conf = max(conf, 0.15)
        conf = min(conf, 0.99)

        return round(conf, 3)

    # ── Advanced Capabilities ─────────────────────────────────────

    def generate_document(self, doc_type: str, params: dict = None) -> dict:
        """
        Generate court-ready documents using templates + DB content + authority injection.
        doc_type: motion, brief, affidavit, response, objection, complaint, petition, notice, order
        params: dict of template parameters (title, lane, arguments, etc.)
        Returns: {document: str, doc_type: str, authorities_used: list, status: str}
        """
        try:
            # Import templates
            sys.path.insert(0, str(Path(__file__).parent))
            from doc_templates import get_template, TEMPLATES

            if doc_type.lower() not in TEMPLATES:
                return {
                    "document": "",
                    "doc_type": doc_type,
                    "authorities_used": [],
                    "status": "error",
                    "error": f"Unknown doc type: {doc_type}. Available: {', '.join(TEMPLATES.keys())}",
                }

            if params is None:
                params = {}

            # Auto-inject authorities if topic provided
            authorities_used = []
            if params.get("topic") and not params.get("authorities_cited"):
                auth_results = self.find_authority(params["topic"], limit=5)
                auto_authorities = []
                for a in auth_results:
                    cite = a.get("rule_number") or a.get("rule") or a.get("citation") or a.get("heading") or ""
                    title = a.get("title", "")
                    if cite:
                        auto_authorities.append(f"{cite} -- {title}" if title else cite)
                        authorities_used.append(cite)
                if auto_authorities:
                    params["authorities_cited"] = auto_authorities

            # Remove non-template keys
            clean_params = {k: v for k, v in params.items() if k != "topic"}

            # Generate document
            document = get_template(doc_type, **clean_params)

            return {
                "document": document,
                "doc_type": doc_type,
                "authorities_used": authorities_used,
                "word_count": len(document.split()),
                "status": "ok",
            }
        except Exception as e:
            self._log_error("generate_document", str(e))
            return {
                "document": "",
                "doc_type": doc_type,
                "authorities_used": [],
                "status": "error",
                "error": str(e)[:200],
            }

    def build_timeline(self, case_id: str = None) -> list[dict]:
        """
        Construct chronological timeline from all evidence in DB.
        Merges docket_events, deadlines, evidence_quotes, documents.
        """
        try:
            sys.path.insert(0, str(Path(__file__).parent / "skills"))
            from timeline_builder import build_timeline as _build_tl
            return _build_tl(case_id)
        except ImportError:
            # Fallback: direct DB query
            events = []
            conn = self._get_db()
            if not conn:
                return events
            try:
                rows = conn.execute(
                    "SELECT event_date_iso as date, title, event_type as type, "
                    "summary, case_id FROM docket_events ORDER BY event_date_iso"
                ).fetchall()
                for r in rows:
                    events.append({
                        "date": r["date"] or "",
                        "title": r["title"] or "",
                        "type": r["type"] or "",
                        "summary": r["summary"] or "",
                        "source_table": "docket_events",
                    })
            except Exception as e:
                logger.warning(f"Timeline docket_events query failed: {e}")
            try:
                rows = conn.execute(
                    "SELECT due_date_iso as date, title, basis as type, "
                    "risk_if_missed as summary, case_id "
                    "FROM deadlines ORDER BY due_date_iso"
                ).fetchall()
                for r in rows:
                    events.append({
                        "date": r["date"] or "",
                        "title": f"DEADLINE: {r['title'] or ''}",
                        "type": "deadline",
                        "summary": r["summary"] or "",
                        "source_table": "deadlines",
                    })
            except Exception as e:
                logger.warning(f"Timeline deadlines query failed: {e}")
            events.sort(key=lambda e: e.get("date", ""))
            return events
        except Exception as e:
            self._log_error("build_timeline", str(e))
            return []

    def find_authority(self, topic: str, limit: int = 10) -> list[dict]:
        """Comprehensive authority search across all DB tables."""
        results = []
        conn = self._get_db()
        if not conn:
            return results

        topic_safe = topic.replace("'", "''")
        tables_queries = [
            ("auth_rules", f"SELECT rule_number, title, substr(full_text,1,500) as text FROM auth_rules WHERE full_text LIKE '%{topic_safe}%' OR title LIKE '%{topic_safe}%' LIMIT {limit}"),
            ("rules_text", f"SELECT rule, substr(context,1,500) as text FROM rules_text WHERE context LIKE '%{topic_safe}%' OR rule LIKE '%{topic_safe}%' LIMIT {limit}"),
            ("master_citations", f"SELECT citation, cite_type, substr(context,1,500) as text FROM master_citations WHERE citation LIKE '%{topic_safe}%' OR context LIKE '%{topic_safe}%' LIMIT {limit}"),
            ("legal_reference_docs", f"SELECT heading, substr(body,1,500) as text, source_file FROM legal_reference_docs WHERE heading LIKE '%{topic_safe}%' OR body LIKE '%{topic_safe}%' LIMIT {limit}"),
            ("md_sections", f"SELECT section_title, substr(content,1,500) as text, source_file FROM md_sections WHERE section_title LIKE '%{topic_safe}%' OR content LIKE '%{topic_safe}%' LIMIT {limit}"),
        ]

        # Also try FTS if available
        try:
            fts_words = " OR ".join(topic.split()[:5])
            rows = conn.execute(
                "SELECT rule_number, title, substr(full_text,1,500) as text FROM auth_rules "
                "WHERE rowid IN (SELECT rowid FROM auth_rules_fts WHERE auth_rules_fts MATCH ?) LIMIT ?",
                (fts_words, limit)
            ).fetchall()
            for r in rows:
                results.append({"source": "auth_rules_fts", "rule": r["rule_number"], "title": r["title"], "text": r["text"]})
        except Exception as e:
            logger.warning(f"FTS authority search failed for topic '{topic}': {e}")

        for table, sql in tables_queries:
            try:
                opt_sql, opt_params = self._rewrite_sql(sql)
                rows = conn.execute(opt_sql, opt_params or ()).fetchall()
                for r in rows:
                    results.append({"source": table, **{k: r[k] for k in r.keys()}})
            except Exception as e:
                logger.warning(f"Authority search failed on table '{table}': {e}")

        # Deduplicate by text similarity
        seen_texts = set()
        unique = []
        for r in results:
            key = (r.get("text", "")[:100]).lower()
            if key not in seen_texts:
                seen_texts.add(key)
                unique.append(r)
        return unique[:limit]

    def check_citations(self, text: str) -> list[dict]:
        """Verify every legal citation in a document against the DB."""
        results = []
        conn = self._get_db()
        entities = self.extract_entities(text)

        for rule_ref in entities.get("mcr", []):
            found = False
            if conn:
                try:
                    row = conn.execute(
                        "SELECT rule_number, title FROM auth_rules WHERE rule_number LIKE ?",
                        (f"%{rule_ref}%",)
                    ).fetchone()
                    if row:
                        found = True
                        results.append({"citation": f"MCR {rule_ref}", "valid": True, "found_in": "auth_rules", "title": row["title"]})
                except Exception as e:
                    logger.debug(f"Citation check failed for MCR: {e}")
            if not found:
                results.append({"citation": f"MCR {rule_ref}", "valid": False, "found_in": None, "title": "NOT FOUND"})

        for mcl_ref in entities.get("mcl", []):
            found = False
            if conn:
                try:
                    row = conn.execute(
                        "SELECT rule, context FROM rules_text WHERE rule LIKE ?",
                        (f"%{mcl_ref}%",)
                    ).fetchone()
                    if row:
                        found = True
                        results.append({"citation": f"MCL {mcl_ref}", "valid": True, "found_in": "rules_text", "title": (row["context"] or "")[:100]})
                except Exception as e:
                    logger.debug(f"Citation check failed for MCL: {e}")
            if not found:
                results.append({"citation": f"MCL {mcl_ref}", "valid": False, "found_in": None, "title": "NOT FOUND"})

        for mre_ref in entities.get("mre", []):
            found = False
            if conn:
                try:
                    row = conn.execute(
                        "SELECT rule_number, title FROM auth_rules WHERE rule_number LIKE ? AND rule_type='MRE'",
                        (f"%{mre_ref}%",)
                    ).fetchone()
                    if row:
                        found = True
                        results.append({"citation": f"MRE {mre_ref}", "valid": True, "found_in": "auth_rules", "title": row["title"]})
                except Exception as e:
                    logger.debug(f"Citation check failed for MRE: {e}")
            if not found:
                results.append({"citation": f"MRE {mre_ref}", "valid": False, "found_in": None, "title": "NOT FOUND"})

        return results

    def analyze_document(self, text: str) -> dict:
        """Analyze a document: extract citations, claims, issues, strengths/weaknesses."""
        entities = self.extract_entities(text)
        citations = self.check_citations(text)
        intent, confidence = self.classify_intent(text)
        concepts = self.match_concepts(text)
        patterns = self._detect_patterns(text, intent, entities)

        # Extract claims (sentences with legal assertions)
        sentences = re.split(r'[.!?]+', text)
        claims = []
        claim_signals = ["must", "shall", "required", "violated", "failed to", "denied", "refused",
                         "constitutional", "unlawful", "improper", "prejudice", "entitle", "right to"]
        for s in sentences:
            s = s.strip()
            if len(s) > 20 and any(sig in s.lower() for sig in claim_signals):
                claims.append(s[:200])

        # Strengths and weaknesses
        strengths = []
        weaknesses = []
        valid_cites = [c for c in citations if c["valid"]]
        invalid_cites = [c for c in citations if not c["valid"]]

        if valid_cites:
            strengths.append(f"{len(valid_cites)} verified citations found in DB")
        if invalid_cites:
            weaknesses.append(f"{len(invalid_cites)} citations NOT found in DB — verify manually")
        if claims:
            strengths.append(f"{len(claims)} legal claims identified")
        if not claims:
            weaknesses.append("No clear legal claims detected — strengthen argument structure")
        if concepts:
            strengths.append(f"Matches {len(concepts)} legal concepts in KB")
        if patterns:
            strengths.append(f"{len(patterns)} legal patterns detected")
        if not entities.get("mcr") and not entities.get("mcl"):
            weaknesses.append("No MCR/MCL citations — add specific rule references")

        return {
            "intent": intent,
            "confidence": round(confidence, 3),
            "entities": entities,
            "citations": citations,
            "claims": claims[:20],
            "concepts": [c.get("id", "") for c in concepts],
            "patterns": patterns,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "word_count": len(text.split()),
            "sentence_count": len(sentences),
        }

    # ── MSC Original Action Engine ──────────────────────────────

    # All Michigan Supreme Court original actions with standards and authority
    _MSC_ORIGINAL_ACTIONS = {
        "superintending_control": {
            "title": "Complaint for Superintending Control",
            "authority": "MCR 7.306; Const 1963 art 6 § 4",
            "standard": [
                "No adequate remedy available (appeal inadequate)",
                "Lower court acted without or in excess of jurisdiction",
                "Systemic error requiring supervisory intervention",
                "Important question of law affecting state jurisprudence",
            ],
            "case_law": [
                "Genesee Prosecutor v Genesee Circuit Judge, 386 Mich 672, 691 (1972)",
                "In re Disqualification of Gorcyca, 500 Mich 588, 593 (2017)",
            ],
            "filing_requirements": [
                "Complaint filed per MCR 7.306(A)",
                "Service on all parties",
                "Supporting brief per MCR 7.312",
                "Appendix with relevant lower court record",
                "Filing fee (or fee waiver motion)",
            ],
        },
        "mandamus": {
            "title": "Writ of Mandamus",
            "authority": "MCR 7.306; Const 1963 art 6 § 4",
            "standard": [
                "Clear legal duty to act",
                "Clear legal right in the plaintiff",
                "No adequate remedy at law",
                "Duty is ministerial, not discretionary",
            ],
            "case_law": [
                "Ayotte v Dep't of Community Health, 254 Mich App 67, 73 (2002)",
                "Taxpayers Allied for Constitutional Taxation v Wayne County, 450 Mich 119 (1995)",
            ],
            "filing_requirements": [
                "Complaint for mandamus per MCR 7.306",
                "Proof of clear legal duty",
                "Proof of clear legal right",
                "Proof no adequate remedy exists",
            ],
        },
        "habeas_corpus": {
            "title": "Writ of Habeas Corpus",
            "authority": "Const 1963 art 1 § 12; MCL 600.4301-4365",
            "standard": [
                "Person unlawfully restrained of liberty",
                "No other adequate remedy available",
                "Restraint without lawful authority or due process",
            ],
            "case_law": [
                "In re Brock, 442 Mich 101 (1993)",
                "Triplett v Deputy Warden, 371 Mich 663 (1964)",
            ],
            "filing_requirements": [
                "Verified petition",
                "Statement of facts showing unlawful restraint",
                "Proof that other remedies exhausted or inadequate",
            ],
        },
        "prohibition": {
            "title": "Writ of Prohibition",
            "authority": "MCR 7.306; common law",
            "standard": [
                "Lower court proceeding without jurisdiction",
                "Lower court exceeding jurisdictional limits",
                "No adequate remedy by appeal",
            ],
            "case_law": [
                "Genesee Prosecutor v Genesee Circuit Judge, 386 Mich 672 (1972)",
                "Pub Co v Judges of the 74th Judicial Dist, 154 Mich App 552 (1986)",
            ],
            "filing_requirements": [
                "Complaint per MCR 7.306",
                "Proof lower court lacks or exceeds jurisdiction",
            ],
        },
        "quo_warranto": {
            "title": "Quo Warranto",
            "authority": "MCL 600.4501-4521",
            "standard": [
                "Public officer exercising authority not lawfully held",
                "Challenge to right to hold or exercise public office",
            ],
            "case_law": [
                "Attorney General v Bd of State Canvassers, 318 Mich App 242 (2016)",
            ],
            "filing_requirements": [
                "Complaint filed by AG or with AG consent",
                "Statement of grounds for challenge",
            ],
        },
        "declaratory_judgment": {
            "title": "Declaratory Judgment",
            "authority": "MCL 600.605; MCR 2.605",
            "standard": [
                "Actual controversy between parties",
                "Declaration of rights will resolve the controversy",
                "Adverse interests present",
            ],
            "case_law": [
                "Lansing Sch Ed Ass'n v Lansing Bd of Ed, 487 Mich 349 (2010)",
            ],
            "filing_requirements": [
                "Complaint stating actual controversy",
                "Brief in support",
                "Proof of service",
            ],
        },
        "emergency_application": {
            "title": "Emergency Application for Leave to Appeal",
            "authority": "MCR 7.305(F); MCR 7.315(C)",
            "standard": [
                "Immediate and irreparable harm without relief",
                "Issue of major significance",
                "Likelihood of success on the merits",
            ],
            "case_law": [],
            "filing_requirements": [
                "Application per MCR 7.305(A)",
                "Motion for immediate consideration per MCR 7.315(C)(1)",
                "Statement of emergency circumstances",
                "Brief in support",
            ],
        },
        "federal_1983": {
            "title": "42 USC § 1983 Federal Civil Rights Action",
            "authority": "42 USC § 1983; 28 USC § 1343",
            "standard": [
                "Deprivation of constitutional rights",
                "Action under color of state law",
                "No judicial immunity for prospective injunctive relief (Pulliam v Allen)",
            ],
            "case_law": [
                "Monroe v Pape, 365 US 167 (1961)",
                "Pulliam v Allen, 466 US 522, 541-42 (1984)",
                "Hafer v Melo, 502 US 21 (1991)",
            ],
            "filing_requirements": [
                "Complaint in USDC",
                "Statement of constitutional violations",
                "Prayer for prospective injunctive relief",
                "Filing fee or IFP motion (28 USC § 1915)",
            ],
        },
        "jtc_complaint": {
            "title": "JTC Formal Complaint",
            "authority": "MCR 9.200-9.252; Const 1963 art 6 § 30",
            "standard": [
                "Misconduct in office",
                "Conduct prejudicial to administration of justice",
                "Failure to perform judicial duties",
                "Habitual intemperance or persistent disability",
            ],
            "case_law": [
                "In re Haley, 476 Mich 180 (2006)",
                "In re Justin, 490 Mich 394 (2012)",
            ],
            "filing_requirements": [
                "Written complaint to JTC",
                "Specific allegations with dates and details",
                "Supporting documentation",
            ],
        },
    }

    # Jurisdiction compass — authority hierarchy per jurisdiction
    _JURISDICTION_COMPASS = {
        "michigan_circuit": {
            "name": "14th Circuit Court, Muskegon County",
            "court": "14th Circuit Court, Muskegon County",
            "authority_hierarchy": ["MCR", "MCL", "MRE", "Michigan Case Law", "SCAO Forms"],
            "filing_rules": "MCR 2.113; MCR 2.107 (service); local administrative orders",
            "judge": "Hon. Jenny L. McNeill",
            "primary_vehicle": "Emergency Motion to Restore Parenting Time",
        },
        "michigan_coa": {
            "name": "Michigan Court of Appeals",
            "court": "Michigan Court of Appeals",
            "authority_hierarchy": ["MCR Ch 7", "MCL", "MRE", "Published MI COA", "MI Supreme Court"],
            "filing_rules": "MCR 7.204-7.215; MCR 7.212 (briefs)",
            "case_number": "COA 366810",
            "primary_vehicle": "Appellant Brief",
        },
        "michigan_msc": {
            "name": "Michigan Supreme Court",
            "court": "Michigan Supreme Court",
            "authority_hierarchy": ["Const 1963", "MCR Ch 7.3xx", "MCL", "MSC precedent"],
            "filing_rules": "MCR 7.305-7.306; MCR 7.312 (briefs); MCR 7.315 (motions)",
            "original_actions": list(_MSC_ORIGINAL_ACTIONS.keys()),
            "primary_vehicle": "MSC Complaint for Superintending Control (MCR 7.306)",
        },
        "federal_usdc": {
            "name": "USDC Western District of Michigan",
            "court": "U.S. District Court, Western District of Michigan",
            "authority_hierarchy": ["US Constitution", "42 USC § 1983", "28 USC", "Federal Rules Civ Pro", "6th Circuit precedent"],
            "filing_rules": "FRCP; Local Rules W.D. Mich.",
            "primary_vehicle": "42 USC § 1983 Complaint",
        },
        "michigan_jtc": {
            "name": "Judicial Tenure Commission",
            "court": "Michigan Judicial Tenure Commission",
            "authority_hierarchy": ["Const 1963 art 6 § 30", "MCR 9.200-9.252", "Code of Judicial Conduct"],
            "filing_rules": "MCR 9.211 (complaint procedure)",
            "primary_vehicle": "JTC Formal Complaint",
        },
    }

    def msc_original_action_scan(self, action_type: str = "all") -> dict:
        """
        Deep scan for MSC original action viability.
        Queries the database for evidence supporting each action type.
        Returns viability assessment with evidence counts and authority.
        """
        results = {"actions": {}, "total_evidence": 0, "recommendation": ""}
        conn = self._get_db()
        if not conn:
            return {**results, "status": "no_db"}

        actions_to_scan = (
            self._MSC_ORIGINAL_ACTIONS
            if action_type == "all"
            else {action_type: self._MSC_ORIGINAL_ACTIONS.get(action_type, {})}
        )

        evidence_queries = {
            "superintending_control": [
                ("judicial_violations", "SELECT COUNT(*) FROM judicial_violations WHERE judge_name LIKE '%McNeill%'"),
                ("critical_violations", "SELECT COUNT(*) FROM judicial_violations WHERE judge_name LIKE '%McNeill%' AND severity='critical'"),
                ("ex_parte_evidence", "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%ex parte%'"),
                ("benchbook_violations", "SELECT COUNT(*) FROM auth_benchbook_violations WHERE judge LIKE '%McNeill%'"),
            ],
            "mandamus": [
                ("endangerment_evidence", "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%endanger%' OR quote_text LIKE '%MCL 722.27a%'"),
                ("parenting_suspension", "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%suspend%parenting%'"),
                ("no_hearing_evidence", "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%no hearing%' OR quote_text LIKE '%without hearing%'"),
            ],
            "habeas_corpus": [
                ("separation_evidence", "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%separated%' OR quote_text LIKE '%separation%'"),
                ("custody_deprivation", "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%depriv%' AND quote_text LIKE '%parent%'"),
            ],
            "prohibition": [
                ("excess_jurisdiction", "SELECT COUNT(*) FROM judicial_violations WHERE violation_description LIKE '%jurisdiction%' OR violation_description LIKE '%ex parte%'"),
            ],
            "declaratory_judgment": [
                ("controversy_evidence", "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%ex parte%' AND quote_text LIKE '%MCR 3.207%'"),
            ],
            "federal_1983": [
                ("due_process_violations", "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%due process%'"),
                ("equal_protection", "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%disparate%' OR quote_text LIKE '%unequal%'"),
                ("disqualification", "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%disqualif%'"),
            ],
            "jtc_complaint": [
                ("canon_violations", "SELECT COUNT(*) FROM judicial_violations WHERE judge_name LIKE '%McNeill%'"),
                ("impeachment_items", "SELECT COUNT(*) FROM impeachment_items"),
                ("contradictions", "SELECT COUNT(*) FROM contradiction_map"),
            ],
        }

        total = 0
        for action_id, action_info in actions_to_scan.items():
            queries = evidence_queries.get(action_id, [])
            evidence_counts = {}
            action_total = 0
            for label, sql in queries:
                try:
                    row = conn.execute(sql).fetchone()
                    count = row[0] if row else 0
                    evidence_counts[label] = count
                    action_total += count
                except Exception as e:
                    evidence_counts[label] = f"error: {e}"

            # Viability scoring
            viability = min(5, max(1, action_total // 100 + 1))

            results["actions"][action_id] = {
                **action_info,
                "evidence_counts": evidence_counts,
                "evidence_total": action_total,
                "viability_score": viability,
                "viability_stars": "★" * viability + "☆" * (5 - viability),
            }
            total += action_total

        results["total_evidence"] = total

        # Build recommendation
        ranked = sorted(
            results["actions"].items(),
            key=lambda x: x[1].get("evidence_total", 0),
            reverse=True,
        )
        if ranked:
            top = ranked[0]
            results["recommendation"] = (
                f"STRONGEST: {top[1].get('title', top[0])} "
                f"({top[1].get('evidence_total', 0)} evidence items, "
                f"{top[1].get('viability_stars', '')})"
            )

        results["status"] = "ok"
        return results

    def map_evidence_to_grounds(self, grounds: Optional[List[str]] = None) -> dict:
        """
        Map evidence from the database to specific legal grounds.
        3-pass deep scan: (1) direct match, (2) FTS match, (3) pattern match.
        """
        if grounds is None:
            grounds = [
                "ex_parte_violations",
                "due_process",
                "endangerment_finding",
                "disparate_treatment",
                "disqualification",
                "ppo_weaponization",
                "bond_barrier",
                "muting_silencing",
                "exculpatory_evidence_ignored",
                "contempt_abuse",
                "parental_alienation",
                "off_record_evidence",
            ]

        ground_queries = {
            "ex_parte_violations": {
                "pass1": "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%ex parte%'",
                "pass2": "SELECT COUNT(*) FROM evidence_quotes WHERE rowid IN (SELECT rowid FROM evidence_quotes_fts WHERE evidence_quotes_fts MATCH 'ex AND parte')",
                "pass3": "SELECT COUNT(*) FROM judicial_violations WHERE canon_number LIKE '%EX_PARTE%'",
                "authority": "MCR 3.207(C)(2); MCR 2.119(B)(1); Canon 3(A)(5)",
            },
            "due_process": {
                "pass1": "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%due process%' OR quote_text LIKE '%without hearing%' OR quote_text LIKE '%no notice%'",
                "pass2": "SELECT COUNT(*) FROM evidence_quotes WHERE rowid IN (SELECT rowid FROM evidence_quotes_fts WHERE evidence_quotes_fts MATCH 'due AND process')",
                "pass3": "SELECT COUNT(*) FROM judicial_violations WHERE canon_number LIKE '%DUE_PROCESS%'",
                "authority": "US Const Amend XIV; Mathews v Eldridge, 424 US 319 (1976)",
            },
            "endangerment_finding": {
                "pass1": "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%endanger%' OR quote_text LIKE '%MCL 722.27a%'",
                "pass2": "SELECT COUNT(*) FROM evidence_quotes WHERE rowid IN (SELECT rowid FROM evidence_quotes_fts WHERE evidence_quotes_fts MATCH 'endanger OR harm OR danger')",
                "pass3": "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%HealthWest%' OR quote_text LIKE '%CPS%' OR quote_text LIKE '%no abuse%'",
                "authority": "MCL 722.27a(3); Eldred v Ziny, 246 Mich App 142, 148 (2001)",
            },
            "disparate_treatment": {
                "pass1": "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%disparate%' OR quote_text LIKE '%unequal%'",
                "pass2": "SELECT COUNT(*) FROM evidence_quotes WHERE rowid IN (SELECT rowid FROM evidence_quotes_fts WHERE evidence_quotes_fts MATCH 'disparate OR unequal OR discriminat')",
                "pass3": "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%no sanction%' OR quote_text LIKE '%zero sanction%'",
                "authority": "US Const Amend XIV Equal Protection; Reed v Reed, 404 US 71, 76 (1971)",
            },
            "disqualification": {
                "pass1": "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%disqualif%' OR quote_text LIKE '%MCR 2.003%'",
                "pass2": "SELECT COUNT(*) FROM evidence_quotes WHERE rowid IN (SELECT rowid FROM evidence_quotes_fts WHERE evidence_quotes_fts MATCH 'disqualif OR recusal OR bias')",
                "pass3": "SELECT COUNT(*) FROM judicial_violations WHERE canon_number LIKE '%2.003%'",
                "authority": "MCR 2.003(C)(1); MCR 2.003(D); Cain v Dep't of Corrections, 451 Mich 470 (1996)",
            },
            "ppo_weaponization": {
                "pass1": "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%PPO%' AND (quote_text LIKE '%false%' OR quote_text LIKE '%weapon%')",
                "pass2": "SELECT COUNT(*) FROM evidence_quotes WHERE rowid IN (SELECT rowid FROM evidence_quotes_fts WHERE evidence_quotes_fts MATCH 'PPO AND (false OR weapon OR fabricat)')",
                "pass3": "SELECT COUNT(*) FROM judicial_violations WHERE canon_number LIKE '%PPO%'",
                "authority": "MCL 600.2950; MCR 3.707; MRE 602 (personal knowledge)",
            },
            "bond_barrier": {
                "pass1": "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%bond%' OR quote_text LIKE '%250%'",
                "pass2": "SELECT COUNT(*) FROM evidence_quotes WHERE rowid IN (SELECT rowid FROM evidence_quotes_fts WHERE evidence_quotes_fts MATCH 'bond OR filing fee')",
                "pass3": "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%access to court%' OR quote_text LIKE '%Boddie%'",
                "authority": "Boddie v Connecticut, 401 US 371 (1971); Const art 1 § 13",
            },
            "muting_silencing": {
                "pass1": "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%muted%' OR quote_text LIKE '%cut off%' OR quote_text LIKE '%silenc%'",
                "pass2": "SELECT COUNT(*) FROM evidence_quotes WHERE rowid IN (SELECT rowid FROM evidence_quotes_fts WHERE evidence_quotes_fts MATCH 'muted OR silenced OR cut off')",
                "pass3": "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%not to file%' OR quote_text LIKE '%would not look%'",
                "authority": "Due Process Clause; Canon 3(A)(4); right to be heard",
            },
            "exculpatory_evidence_ignored": {
                "pass1": "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%HealthWest%' OR quote_text LIKE '%CPS%' OR quote_text LIKE '%no charge%'",
                "pass2": "SELECT COUNT(*) FROM evidence_quotes WHERE rowid IN (SELECT rowid FROM evidence_quotes_fts WHERE evidence_quotes_fts MATCH 'HealthWest OR CPS OR exculpatory')",
                "pass3": "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%refused to view%' OR quote_text LIKE '%ignored evidence%'",
                "authority": "MRE 401-403; Due Process; Brady v Maryland, 373 US 83 (1963)",
            },
            "contempt_abuse": {
                "pass1": "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%contempt%'",
                "pass2": "SELECT COUNT(*) FROM evidence_quotes WHERE rowid IN (SELECT rowid FROM evidence_quotes_fts WHERE evidence_quotes_fts MATCH 'contempt')",
                "pass3": "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%jail%' AND quote_text LIKE '%hearing%'",
                "authority": "MCR 3.606; MCL 600.1701; due process in contempt proceedings",
            },
            "parental_alienation": {
                "pass1": "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%alienat%'",
                "pass2": "SELECT COUNT(*) FROM evidence_quotes WHERE rowid IN (SELECT rowid FROM evidence_quotes_fts WHERE evidence_quotes_fts MATCH 'alienat OR gatekeep')",
                "pass3": "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%doesn''t want to see%' OR quote_text LIKE '%refuses to facilitate%'",
                "authority": "MCL 722.23(j); Lombardo v Lombardo, 202 Mich App 151 (1993)",
            },
            "off_record_evidence": {
                "pass1": "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%off record%' OR quote_text LIKE '%off the record%' OR quote_text LIKE '%USB%'",
                "pass2": "SELECT COUNT(*) FROM evidence_quotes WHERE rowid IN (SELECT rowid FROM evidence_quotes_fts WHERE evidence_quotes_fts MATCH 'off record OR USB OR chambers')",
                "pass3": "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%ex parte communication%' OR quote_text LIKE '%not on record%'",
                "authority": "Canon 3(A)(5); MCR 2.107; transparency in judicial proceedings",
            },
        }

        conn = self._get_db()
        if not conn:
            return {"grounds": {}, "status": "no_db"}

        mapped = {}
        for ground in grounds:
            if ground not in ground_queries:
                continue
            gq = ground_queries[ground]
            counts = {}
            for pass_name in ["pass1", "pass2", "pass3"]:
                sql = gq.get(pass_name)
                if sql:
                    try:
                        row = conn.execute(sql).fetchone()
                        counts[pass_name] = row[0] if row else 0
                    except Exception:
                        counts[pass_name] = 0

            total = sum(counts.values())
            mapped[ground] = {
                "evidence_counts": counts,
                "total_evidence": total,
                "authority": gq.get("authority", ""),
                "strength": "STRONG" if total > 100 else "MODERATE" if total > 20 else "DEVELOPING",
            }

        return {"grounds": mapped, "total_grounds": len(mapped), "status": "ok"}

    def multi_jurisdiction_query(self, topic: str, jurisdictions: Optional[List[str]] = None) -> dict:
        """
        Query across multiple jurisdictions simultaneously.
        Returns authority, filing requirements, evidence counts, and strategy for each jurisdiction.
        """
        if jurisdictions is None:
            jurisdictions = list(self._JURISDICTION_COMPASS.keys())

        # Map shorthand names to compass keys
        _alias = {
            "circuit": "michigan_circuit", "coa": "michigan_coa",
            "msc": "michigan_msc", "federal": "federal_usdc", "jtc": "michigan_jtc",
        }

        results = {}
        best_jx, best_count = None, 0
        total_evidence = 0

        for jx in jurisdictions:
            key = _alias.get(jx, jx)
            compass = self._JURISDICTION_COMPASS.get(key, {})
            # Get authority for this jurisdiction
            authority_hits = self.find_authority(topic, limit=5)

            # Count evidence relevant to this jurisdiction
            ev_count = 0
            conn = self._get_db()
            if conn:
                try:
                    # Search evidence quotes for topic terms
                    search_terms = " OR ".join(topic.split()[:4])
                    row = conn.execute(
                        "SELECT COUNT(*) FROM evidence_quotes_fts WHERE evidence_quotes_fts MATCH ?",
                        (search_terms,)
                    ).fetchone()
                    ev_count = row[0] if row else 0
                except Exception:
                    ev_count = 0

            total_evidence += ev_count

            results[jx] = {
                "jurisdiction": compass.get("name", jx),
                "court": compass.get("court", compass.get("name", jx)),
                "authority_hierarchy": compass.get("authority_hierarchy", []),
                "governing_authority": compass.get("authority_hierarchy", []),
                "filing_rules": compass.get("filing_rules", ""),
                "authority_found": len(authority_hits),
                "evidence_count": ev_count,
                "top_authorities": [
                    {"source": a.get("source", ""), "text": a.get("text", "")[:200]}
                    for a in authority_hits[:3]
                ],
                "recommended_filing": compass.get("primary_vehicle", ""),
            }
            if key == "michigan_msc":
                results[jx]["original_actions_available"] = list(self._MSC_ORIGINAL_ACTIONS.keys())
                results[jx]["recommended_filing"] = "MSC Complaint for Superintending Control (MCR 7.306)"
            if key == "federal_usdc":
                results[jx]["claims_available"] = [
                    "42 USC § 1983 (civil rights)",
                    "42 USC § 1985 (conspiracy)",
                    "28 USC § 2201 (declaratory judgment)",
                ]
                results[jx]["recommended_filing"] = "42 USC § 1983 Complaint"
            if key == "michigan_circuit":
                results[jx]["recommended_filing"] = "Emergency Motion to Restore Parenting Time"
            if key == "michigan_coa":
                results[jx]["recommended_filing"] = "Appellant Brief (COA 366810)"
            if key == "michigan_jtc":
                results[jx]["recommended_filing"] = "JTC Formal Complaint (already filed)"

            if ev_count > best_count:
                best_count = ev_count
                best_jx = jx

        return {
            "jurisdictions": results,
            "topic": topic,
            "primary_jurisdiction": best_jx or jurisdictions[0] if jurisdictions else "msc",
            "total_evidence": total_evidence,
            "status": "ok",
        }

    def mcneill_pattern_analysis(self) -> dict:
        """
        Deep analysis of Judge McNeill's pattern of conduct.
        Aggregates all violations, impeachment items, and contradictions.
        """
        conn = self._get_db()
        if not conn:
            return {"status": "no_db"}

        analysis = {
            "total_violations": 0,
            "by_severity": {},
            "by_category": {},
            "ex_parte_count": 0,
            "disqualification_grounds": 0,
            "due_process_violations": 0,
            "ppo_weaponization": 0,
            "impeachment_items": 0,
            "contradictions": 0,
            "orders_to_vacate": [],
            "recommendation": "",
        }

        try:
            # Total violations
            row = conn.execute("SELECT COUNT(*) FROM judicial_violations WHERE judge_name LIKE '%McNeill%'").fetchone()
            analysis["total_violations"] = row[0] if row else 0

            # By severity
            rows = conn.execute("SELECT severity, COUNT(*) FROM judicial_violations WHERE judge_name LIKE '%McNeill%' GROUP BY severity").fetchall()
            analysis["by_severity"] = {r[0]: r[1] for r in rows}

            # By category
            rows = conn.execute(
                "SELECT canon_number, COUNT(*) FROM judicial_violations "
                "WHERE judge_name LIKE '%McNeill%' GROUP BY canon_number ORDER BY COUNT(*) DESC LIMIT 10"
            ).fetchall()
            analysis["by_category"] = {r[0]: r[1] for r in rows}

            # Ex parte
            row = conn.execute("SELECT COUNT(*) FROM judicial_violations WHERE judge_name LIKE '%McNeill%' AND canon_number LIKE '%EX_PARTE%'").fetchone()
            analysis["ex_parte_count"] = row[0] if row else 0

            # Disqualification
            row = conn.execute("SELECT COUNT(*) FROM judicial_violations WHERE judge_name LIKE '%McNeill%' AND canon_number LIKE '%2.003%'").fetchone()
            analysis["disqualification_grounds"] = row[0] if row else 0

            # Impeachment
            row = conn.execute("SELECT COUNT(*) FROM impeachment_items").fetchone()
            analysis["impeachment_items"] = row[0] if row else 0

            # Contradictions
            row = conn.execute("SELECT COUNT(*) FROM contradiction_map").fetchone()
            analysis["contradictions"] = row[0] if row else 0

            # Build recommendation
            total = analysis["total_violations"]
            critical = analysis["by_severity"].get("critical", 0)
            analysis["recommendation"] = (
                f"Judge McNeill: {total} total violations ({critical} CRITICAL). "
                f"Ex parte: {analysis['ex_parte_count']}. "
                f"Disqualification: {analysis['disqualification_grounds']}. "
                f"RECOMMEND: MSC Superintending Control + Mandamus + JTC Complaint + COA Appeal. "
                f"NUCLEAR: 42 USC § 1983 federal action."
            )

        except Exception as e:
            self._log_error("mcneill_analysis", str(e))

        analysis["status"] = "ok"
        return analysis

    # MCL 722.23 best-interest factors (a)–(l) for custody IRAC
    _BIF_FACTORS = [
        "(a) love, affection, emotional ties",
        "(b) capacity to give love, affection, guidance",
        "(c) capacity to provide food, clothing, medical care",
        "(d) length of time in stable environment",
        "(e) permanence of existing or proposed custodial home",
        "(f) moral fitness of the parties",
        "(g) mental and physical health of the parties",
        "(h) home, school, and community record of the child",
        "(i) reasonable preference of the child",
        "(j) willingness to facilitate close relationship with other parent",
        "(k) domestic violence",
        "(l) any other factor considered relevant",
    ]

    def irac_analysis(self, issue: str, facts: Optional[List[str]] = None) -> dict:
        """
        Perform structured IRAC (Issue-Rule-Application-Conclusion) legal
        reasoning for a given legal question.

        Args:
            issue: The legal question / issue to analyse.
            facts: Optional list of factual assertions to map against rule elements.

        Returns a dict with keys: issue, rules, application, conclusion,
        confidence, authority_chain.
        """
        t0 = time.time()
        facts = facts or []

        # ── I — ISSUE ────────────────────────────────────────────
        concepts = self.match_concepts(issue)
        entities = self.extract_entities(issue)
        issue_parsed = issue.strip()
        core_issues: list[str] = []
        if concepts:
            core_issues = [c.get("title", c.get("id", "")) for c in concepts[:3]]
        if not core_issues:
            core_issues = [issue_parsed]

        # ── R — RULE ─────────────────────────────────────────────
        stop = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "shall", "can", "to", "of",
            "in", "for", "on", "with", "at", "by", "from", "as", "what",
            "how", "when", "where", "why", "which", "who", "about", "this",
            "that", "and", "or", "but", "not", "if", "my", "me", "i",
        }
        keywords = [
            w for w in re.sub(r"[^a-z0-9\s.]", " ", issue.lower()).split()
            if len(w) > 2 and w not in stop
        ]

        rules: list[dict] = []
        authority_chain: list[str] = []
        conn = self._get_db()

        # (a) auth_rules lookup
        if conn:
            for ent_key in ("mcr", "mcl", "mre"):
                for ref in entities.get(ent_key, [])[:3]:
                    try:
                        row = conn.execute(
                            "SELECT rule_number, title, full_text FROM auth_rules "
                            "WHERE rule_number LIKE ? LIMIT 1",
                            (f"%{ref}%",),
                        ).fetchone()
                        if row:
                            elements = self._extract_rule_elements(row["full_text"] or "")
                            rules.append({
                                "rule": row["rule_number"],
                                "text": (row["full_text"] or "")[:800],
                                "elements": elements,
                            })
                            authority_chain.append(row["rule_number"])
                    except Exception:
                        pass

            # (b) FTS keyword search in auth_rules
            if keywords and len(rules) < 3:
                try:
                    fts_q = " OR ".join(keywords[:4])
                    rows = conn.execute(
                        "SELECT rule_number, title, substr(full_text, 1, 800) as txt "
                        "FROM auth_rules WHERE rowid IN "
                        "(SELECT rowid FROM auth_rules_fts WHERE auth_rules_fts MATCH ?) "
                        "LIMIT 5",
                        (fts_q,),
                    ).fetchall()
                    seen = {r["rule"] for r in rules}
                    for row in rows:
                        if row["rule_number"] not in seen:
                            elements = self._extract_rule_elements(row["txt"] or "")
                            rules.append({
                                "rule": row["rule_number"],
                                "text": row["txt"] or "",
                                "elements": elements,
                            })
                            authority_chain.append(row["rule_number"])
                            seen.add(row["rule_number"])
                except Exception:
                    pass

            # (c) research_summaries
            if keywords:
                try:
                    kw_safe = keywords[0].replace("'", "''")
                    rows = conn.execute(
                        "SELECT topic, rule_refs, key_points FROM research_summaries "
                        "WHERE topic LIKE ? OR rule_refs LIKE ? LIMIT 3",
                        (f"%{kw_safe}%", f"%{kw_safe}%"),
                    ).fetchall()
                    for row in rows:
                        refs = row["rule_refs"] or ""
                        if refs and refs not in authority_chain:
                            authority_chain.append(refs)
                        rules.append({
                            "rule": refs or row["topic"],
                            "text": (row["key_points"] or "")[:600],
                            "elements": [],
                        })
                except Exception:
                    pass

        # ── A — APPLICATION ──────────────────────────────────────
        application: list[dict] = []
        is_custody = any(
            kw in issue.lower()
            for kw in ("custody", "best interest", "722.23", "parenting")
        )

        if is_custody:
            # Map facts against MCL 722.23 factors
            for factor_label in self._BIF_FACTORS:
                factor_kws = factor_label.lower().split()
                ev_for: list[str] = []
                ev_against: list[str] = []
                for f in facts:
                    fl = f.lower()
                    if any(kw in fl for kw in factor_kws if len(kw) > 3):
                        if any(neg in fl for neg in ("denied", "refused", "failed", "against", "lack")):
                            ev_against.append(f)
                        else:
                            ev_for.append(f)
                application.append({
                    "element": factor_label,
                    "evidence_for": ev_for,
                    "evidence_against": ev_against,
                })
        else:
            # Generic: map facts to rule elements
            for rule in rules[:3]:
                for elem in rule.get("elements", [])[:8]:
                    ev_for: list[str] = []
                    ev_against: list[str] = []
                    elem_kws = [w for w in elem.lower().split() if len(w) > 3]
                    for f in facts:
                        fl = f.lower()
                        if any(kw in fl for kw in elem_kws):
                            if any(neg in fl for neg in ("denied", "refused", "failed", "against", "lack")):
                                ev_against.append(f)
                            else:
                                ev_for.append(f)
                    application.append({
                        "element": elem,
                        "evidence_for": ev_for,
                        "evidence_against": ev_against,
                    })

        # Enrich with evidence_quotes and forensic_judicial_analysis from DB
        if conn:
            try:
                kw_safe = keywords[0].replace("'", "''") if keywords else ""
                if kw_safe:
                    rows = conn.execute(
                        "SELECT quote_text, evidence_category, legal_significance "
                        "FROM evidence_quotes WHERE quote_text LIKE ? "
                        "OR legal_significance LIKE ? LIMIT 10",
                        (f"%{kw_safe}%", f"%{kw_safe}%"),
                    ).fetchall()
                    for row in rows:
                        qt = (row["quote_text"] or "")[:200]
                        sig = row["legal_significance"] or ""
                        matched = False
                        for app_entry in application:
                            app_kws = [w for w in app_entry["element"].lower().split() if len(w) > 3]
                            if any(kw in qt.lower() or kw in sig.lower() for kw in app_kws):
                                app_entry["evidence_for"].append(f"[DB] {qt}")
                                matched = True
                                break
                        if not matched and application:
                            application[-1]["evidence_for"].append(f"[DB] {qt}")
            except Exception:
                pass

            try:
                if kw_safe:
                    rows = conn.execute(
                        "SELECT category, severity, description, mcr_violations "
                        "FROM forensic_judicial_analysis "
                        "WHERE description LIKE ? OR mcr_violations LIKE ? LIMIT 5",
                        (f"%{kw_safe}%", f"%{kw_safe}%"),
                    ).fetchall()
                    for row in rows:
                        desc = (row["description"] or "")[:200]
                        viol = row["mcr_violations"] or ""
                        if viol and viol not in authority_chain:
                            authority_chain.append(viol)
                        for app_entry in application:
                            app_kws = [w for w in app_entry["element"].lower().split() if len(w) > 3]
                            if any(kw in desc.lower() for kw in app_kws):
                                app_entry["evidence_against"].append(
                                    f"[Forensic] {row['severity']}: {desc}"
                                )
                                break
            except Exception:
                pass

        # ── C — CONCLUSION ───────────────────────────────────────
        total_for = sum(len(a["evidence_for"]) for a in application)
        total_against = sum(len(a["evidence_against"]) for a in application)
        total_elements = max(len(application), 1)

        # Confidence heuristic
        rule_score = min(len(rules) / 3.0, 1.0) * 0.35
        evidence_score = min((total_for + total_against) / max(total_elements, 1) / 2.0, 1.0) * 0.35
        concept_score = min(len(concepts) / 2.0, 1.0) * 0.15
        chain_score = min(len(authority_chain) / 3.0, 1.0) * 0.15
        confidence = round(min(rule_score + evidence_score + concept_score + chain_score, 0.99), 3)

        if total_for > total_against:
            conclusion = (
                f"Based on {len(rules)} applicable rule(s) and {total_for} supporting "
                f"evidence items vs {total_against} contrary, the analysis supports "
                f"a favourable determination on: {'; '.join(core_issues)}."
            )
        elif total_against > total_for:
            conclusion = (
                f"Based on {len(rules)} applicable rule(s), {total_against} contrary "
                f"evidence items outweigh {total_for} supporting. The issue "
                f"({'; '.join(core_issues)}) faces significant headwinds."
            )
        else:
            conclusion = (
                f"Based on {len(rules)} applicable rule(s), the evidence is evenly "
                f"balanced on: {'; '.join(core_issues)}. Additional fact development "
                f"is recommended."
            )

        elapsed = round((time.time() - t0) * 1000, 1)
        return {
            "issue": issue_parsed,
            "core_issues": core_issues,
            "rules": rules,
            "application": application,
            "conclusion": conclusion,
            "confidence": confidence,
            "authority_chain": list(dict.fromkeys(authority_chain)),
            "elapsed_ms": elapsed,
            "status": "ok",
        }

    @staticmethod
    def _extract_rule_elements(text: str) -> list[str]:
        """Extract numbered or lettered sub-elements from rule text."""
        elements: list[str] = []
        # Match patterns like (1), (a), (A), (i) at start of line or after newline
        for m in re.finditer(r'(?:^|\n)\s*\(([a-zA-Z0-9]{1,3})\)\s*(.+?)(?=\n\s*\(|$)', text, re.S):
            elem_text = m.group(2).strip()[:200]
            if len(elem_text) > 10:
                elements.append(f"({m.group(1)}) {elem_text}")
        # Fallback: numbered list items
        if not elements:
            for m in re.finditer(r'(?:^|\n)\s*(\d{1,2})[.)]\s*(.+?)(?=\n\s*\d|$)', text, re.S):
                elem_text = m.group(2).strip()[:200]
                if len(elem_text) > 10:
                    elements.append(f"{m.group(1)}. {elem_text}")
        return elements[:20]

    # ── Document Q&A delegation ──────────────────────────────────
    def document_qa(
        self, question: str, doc_id=None, file_path=None, top_k: int = 5
    ) -> dict:
        """Delegate to DocumentQA for passage-level document search."""
        from document_qa import DocumentQA
        qa = DocumentQA(db_path=DB_PATH)
        try:
            return qa.ask(question, doc_id=doc_id, file_path=file_path, top_k=top_k)
        finally:
            qa.close()

    # ── EPOCH v9.0: OMEGA-INFINITY METHODS ─────────────────────────
    def startup_diagnostics(self) -> dict:
        """Auto-diagnostic report for Copilot startup integration."""
        t0 = time.time()
        report = {
            "engine_version": "v9.0-OMEGA-INFINITY",
            "model_loaded": self.loaded,
            "model_name": self.manifest.get("model_name", "unknown"),
            "db_connected": False,
            "db_tables": 0,
            "separation_days": 0,
            "deadlines": [],
            "filing_readiness": [],
            "system_health": "UNKNOWN",
            "evidence_counts": {},
            "critical_alerts": [],
        }
        conn = self._get_db()
        if conn:
            report["db_connected"] = True
            try:
                tables = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
                report["db_tables"] = tables
            except Exception:
                pass
            # Separation day count from Aug 8, 2025
            try:
                from datetime import datetime, date
                sep_start = date(2025, 8, 8)
                today = date.today()
                report["separation_days"] = (today - sep_start).days
            except Exception:
                pass
            # Upcoming deadlines
            try:
                rows = conn.execute(
                    "SELECT deadline_name, due_date_iso, case_id, status FROM deadlines "
                    "WHERE due_date_iso >= date('now') ORDER BY due_date_iso LIMIT 10"
                ).fetchall()
                report["deadlines"] = [
                    {"name": r[0], "due": r[1], "case": r[2], "status": r[3],
                     "days_remaining": (datetime.strptime(r[1], "%Y-%m-%d").date() - date.today()).days if r[1] else None}
                    for r in rows
                ]
                # Critical alerts for anything due within 14 days
                for d in report["deadlines"]:
                    if d.get("days_remaining") is not None and d["days_remaining"] <= 14:
                        report["critical_alerts"].append(
                            f"⚠️ URGENT: {d['name']} due in {d['days_remaining']} days ({d['due']})"
                        )
            except Exception as e:
                logger.debug(f"Deadline query failed: {e}")
            # Filing readiness
            try:
                rows = conn.execute(
                    "SELECT vehicle_name, status, readiness_score FROM filing_readiness "
                    "ORDER BY readiness_score DESC LIMIT 15"
                ).fetchall()
                report["filing_readiness"] = [
                    {"vehicle": r[0], "status": r[1], "score": r[2]} for r in rows
                ]
            except Exception:
                pass
            # Evidence counts
            try:
                for tbl, key in [("extracted_harms", "harms"), ("evidence_quotes", "evidence_quotes"),
                                 ("impeachment_items", "impeachment"), ("judicial_violations", "judicial_violations"),
                                 ("contradiction_map", "contradictions")]:
                    try:
                        cnt = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
                        report["evidence_counts"][key] = cnt
                    except Exception:
                        pass
            except Exception:
                pass
            # System health
            try:
                row = conn.execute(
                    "SELECT status FROM system_health_log ORDER BY rowid DESC LIMIT 1"
                ).fetchone()
                report["system_health"] = row[0] if row else "NO_DATA"
            except Exception:
                pass
        report["elapsed_ms"] = round((time.time() - t0) * 1000, 1)
        report["status"] = "ok"
        return report

    def deadline_urgency_score(self, days_threshold: int = 30) -> dict:
        """Score all deadlines by urgency with color-coded alerts."""
        conn = self._get_db()
        if not conn:
            return {"error": "No DB connection", "status": "error"}
        from datetime import datetime, date
        try:
            rows = conn.execute(
                "SELECT deadline_name, due_date_iso, case_id, status, notes FROM deadlines "
                "WHERE due_date_iso >= date('now') ORDER BY due_date_iso"
            ).fetchall()
        except Exception as e:
            return {"error": str(e), "status": "error"}
        scored = []
        for r in rows:
            try:
                due = datetime.strptime(r[1], "%Y-%m-%d").date()
                days_left = (due - date.today()).days
                if days_left <= 7:
                    urgency = "🔴 CRITICAL"
                    score = 100
                elif days_left <= 14:
                    urgency = "🟠 URGENT"
                    score = 80
                elif days_left <= 30:
                    urgency = "🟡 APPROACHING"
                    score = 60
                else:
                    urgency = "🟢 SCHEDULED"
                    score = max(10, 50 - days_left)
                scored.append({
                    "name": r[0], "due": r[1], "case": r[2], "status": r[3],
                    "days_left": days_left, "urgency": urgency, "score": score,
                    "notes": r[4] if len(r) > 4 else None
                })
            except Exception:
                pass
        scored.sort(key=lambda x: -x["score"])
        return {"deadlines": scored, "count": len(scored),
                "critical_count": sum(1 for s in scored if s["score"] >= 80),
                "status": "ok"}

    def filing_readiness_optimizer(self) -> dict:
        """Analyze all filing vehicles and recommend next actions to maximize readiness."""
        conn = self._get_db()
        if not conn:
            return {"error": "No DB connection", "status": "error"}
        try:
            vehicles = conn.execute(
                "SELECT vehicle_name, status, readiness_score, blockers, next_steps "
                "FROM filing_readiness ORDER BY readiness_score DESC"
            ).fetchall()
        except Exception as e:
            return {"error": str(e), "status": "error"}
        optimized = []
        ready_count = 0
        blocked_count = 0
        for v in vehicles:
            entry = {
                "vehicle": v[0], "status": v[1], "score": v[2],
                "blockers": v[3] if len(v) > 3 else None,
                "next_steps": v[4] if len(v) > 4 else None,
            }
            if v[2] and v[2] >= 80:
                ready_count += 1
                entry["recommendation"] = "READY — finalize signatures and file"
            elif v[2] and v[2] >= 60:
                entry["recommendation"] = "NEAR-READY — resolve blockers listed"
            else:
                blocked_count += 1
                entry["recommendation"] = "NEEDS WORK — see next_steps"
            optimized.append(entry)
        return {
            "vehicles": optimized, "total": len(optimized),
            "ready": ready_count, "blocked": blocked_count,
            "top_recommendation": f"File {ready_count} ready vehicles immediately. Resolve {blocked_count} blocked.",
            "status": "ok"
        }

    def evidence_gap_detector(self, vehicle_name: str = None) -> dict:
        """Detect evidence gaps for filing vehicles by cross-referencing claims vs evidence."""
        conn = self._get_db()
        if not conn:
            return {"error": "No DB connection", "status": "error"}
        try:
            if vehicle_name:
                gaps = conn.execute(
                    "SELECT gap_id, vehicle, description, severity, resolution "
                    "FROM gap_tickets WHERE vehicle LIKE ? ORDER BY severity DESC",
                    (f"%{vehicle_name}%",)
                ).fetchall()
            else:
                gaps = conn.execute(
                    "SELECT gap_id, vehicle, description, severity, resolution "
                    "FROM gap_tickets ORDER BY severity DESC LIMIT 50"
                ).fetchall()
        except Exception as e:
            return {"error": str(e), "status": "error"}
        return {
            "gaps": [{"id": g[0], "vehicle": g[1], "description": g[2],
                      "severity": g[3], "resolution": g[4]} for g in gaps],
            "count": len(gaps),
            "critical_gaps": sum(1 for g in gaps if g[3] and str(g[3]).upper() in ("CRITICAL", "HIGH")),
            "status": "ok"
        }

    def status(self) -> dict:
        """Get model status with self-healing diagnostics."""
        return {
            "loaded": self.loaded,
            "model_name": self.manifest.get("model_name", "not trained"),
            "corpus_size": self.manifest.get("corpus_size", 0),
            "vocab_size": self.manifest.get("vocab_size", 0),
            "intent_classes": self.manifest.get("intent_classes", []),
            "doctype_classes": self.manifest.get("doctype_classes", []),
            "concept_count": len(self.legal_concepts),
            "db_connected": self._get_db() is not None,
            "db_path": DB_PATH,
            "cache_size": len(self._cache),
            "error_count": len(self._error_log),
            "heal_attempts": dict(self._heal_attempts),
        }


# ──────────────────────────────────────────────────────────────────
# Backpressure-safe pipe writer (prevents EAGAIN permanently)
# ──────────────────────────────────────────────────────────────────
def _safe_pipe_write(data: str, max_retries: int = 10) -> bool:
    """Write to stdout with EAGAIN/backpressure retry. Never crashes."""
    payload = (data if data.endswith("\n") else data + "\n").encode("utf-8", errors="replace")
    written = 0
    retries = 0
    while written < len(payload):
        try:
            chunk = payload[written:written + 8192]  # 8KB chunks max
            n = sys.stdout.buffer.write(chunk)
            if n is None:
                n = len(chunk)  # some implementations return None on success
            written += n
            retries = 0  # reset on success
        except BlockingIOError:
            retries += 1
            if retries > max_retries:
                print(f"[MANBEARPIG] EAGAIN: gave up after {max_retries} retries", file=sys.stderr, flush=True)
                return False
            time.sleep(0.01 * (2 ** min(retries, 6)))  # exp backoff: 10ms → 640ms
        except (BrokenPipeError, OSError) as e:
            print(f"[MANBEARPIG] Pipe broken: {e}", file=sys.stderr, flush=True)
            return False
        except Exception as e:
            print(f"[MANBEARPIG] Write error: {e}", file=sys.stderr, flush=True)
            return False
    try:
        sys.stdout.buffer.flush()
    except Exception:
        pass
    return True


# ──────────────────────────────────────────────────────────────────
# JSON-RPC Pipe (stdin/stdout — for JS integration, NOT a server)
# ──────────────────────────────────────────────────────────────────
def run_pipe():
    """Read JSON from stdin, write JSON to stdout. Never crashes."""
    # Force binary-safe buffered stdout on Windows
    if sys.platform == "win32":
        import msvcrt
        try:
            msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
        except Exception:
            pass
        # Reopen stdout with a large buffer to prevent EAGAIN
        try:
            sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8",
                              errors="replace", buffering=65536, closefd=False)
        except Exception:
            pass

    print("[MANBEARPIG] Loading model...", file=sys.stderr, flush=True)
    model = MichiganLegalModel()
    if model.loaded:
        print(f"[MANBEARPIG] Model loaded: {model.manifest.get('model_name')}", file=sys.stderr, flush=True)
    else:
        print("[MANBEARPIG] WARNING: Model not trained — run train_model.py first", file=sys.stderr, flush=True)

    # Signal ready
    _safe_pipe_write(json.dumps({"ready": True, "status": model.status()}))

    for line in sys.stdin:
        try:
            line = line.strip()
            if not line:
                continue
            request = json.loads(line)
            method = request.get("method", "query")

            if method == "query":
                result = model.query(request.get("text", ""))
            elif method == "status":
                result = model.status()
            elif method == "retrieve":
                docs = model.retrieve(
                    request.get("text", ""),
                    top_k=request.get("top_k", 10),
                )
                result = {"documents": docs, "status": "ok"}
            elif method == "classify":
                intent, conf = model.classify_intent(request.get("text", ""))
                result = {"intent": intent, "confidence": conf}
            elif method == "entities":
                ents = model.extract_entities(request.get("text", ""))
                result = {"entities": ents}
            elif method == "concepts":
                concepts = model.match_concepts(request.get("text", ""))
                result = {"concepts": concepts}
            elif method == "find_authority":
                result = {"authorities": model.find_authority(
                    request.get("topic", request.get("text", "")),
                    limit=request.get("limit", 10)
                ), "status": "ok"}
            elif method == "check_citations":
                result = {"citations": model.check_citations(request.get("text", "")), "status": "ok"}
            elif method == "analyze_document":
                result = model.analyze_document(request.get("text", ""))
                result["status"] = "ok"
            elif method == "generate_document":
                result = model.generate_document(
                    request.get("doc_type", "motion"),
                    request.get("params", {})
                )
            elif method == "build_timeline":
                events = model.build_timeline(request.get("case_id"))
                result = {"timeline": events, "count": len(events), "status": "ok"}
            elif method == "detect_patterns":
                entities = model.extract_entities(request.get("text", ""))
                intent, _ = model.classify_intent(request.get("text", ""))
                result = {"patterns": model._detect_patterns(request.get("text", ""), intent, entities), "status": "ok"}
            elif method == "error_report":
                result = model.get_error_report()
            elif method == "clear_cache":
                model._cache.clear()
                result = {"cleared": True, "status": "ok"}
            elif method == "brain_stats":
                result = model.get_brain_stats()
            elif method == "knowledge_gaps":
                result = model.get_knowledge_gaps(
                    limit=request.get("limit", 20)
                )
            elif method == "resolve_gap":
                result = model.resolve_gap(
                    request.get("gap_id", 0),
                    request.get("note", ""),
                )
            elif method == "document_qa":
                result = model.document_qa(
                    request.get("text", ""),
                    doc_id=request.get("doc_id"),
                    file_path=request.get("file_path"),
                    top_k=request.get("top_k", 5),
                )
            elif method in ("document_qa_evidence", "document_qa_filings", "document_qa_summarize"):
                from document_qa import DocumentQA
                _qa = DocumentQA(db_path=DB_PATH)
                try:
                    if method == "document_qa_evidence":
                        result = _qa.ask_evidence(request.get("text", ""), top_k=request.get("top_k", 10))
                    elif method == "document_qa_filings":
                        result = _qa.ask_filings(request.get("text", ""), top_k=request.get("top_k", 10))
                    else:
                        result = _qa.summarize_document(request.get("doc_id", 0))
                finally:
                    _qa.close()
            elif method == "feedback":
                result = model.feedback(
                    request.get("query_id", 0),
                    request.get("rating", 3),
                    comment=request.get("comment"),
                )
            elif method == "get_weak_areas":
                result = model.get_weak_areas()
            elif method == "auto_diagnose":
                result = model.auto_diagnose()
            elif method == "irac_analysis":
                result = model.irac_analysis(
                    request.get("issue", request.get("text", "")),
                    facts=request.get("facts"),
                )
            elif method == "get_context":
                result = {"context_window": model.get_context(), "status": "ok"}
            elif method == "clear_context":
                model.clear_context()
                result = {"cleared": True, "status": "ok"}
            # ── MSC Original Action & Multi-Jurisdiction Methods ──
            elif method == "msc_scan":
                result = model.msc_original_action_scan(
                    action_type=request.get("action_type", "all")
                )
            elif method == "map_evidence":
                result = model.map_evidence_to_grounds(
                    grounds=request.get("grounds")
                )
            elif method == "multi_jurisdiction":
                result = model.multi_jurisdiction_query(
                    request.get("topic", request.get("text", "")),
                    jurisdictions=request.get("jurisdictions"),
                )
            elif method == "mcneill_analysis":
                result = model.mcneill_pattern_analysis()
            # ── MANBEARPIG Skill Methods (lazy-imported) ─────────────
            elif method == "jtc_complaint":
                from skills.jtc_complaint_generator import JTCComplaintGenerator
                _skill = JTCComplaintGenerator()
                result = _skill.generate_complaint_narrative()
            elif method == "jtc_complaint_text":
                from skills.jtc_complaint_generator import JTCComplaintGenerator
                _skill = JTCComplaintGenerator()
                result = _skill.generate_complaint_text()
            elif method == "adversary_predict":
                from skills.adversary_war_room import AdversaryWarRoom
                _skill = AdversaryWarRoom()
                result = _skill.predict_attacks(request.get("filing_type"))
            elif method == "adversary_wargame":
                from skills.adversary_war_room import AdversaryWarRoom
                _skill = AdversaryWarRoom()
                result = _skill.war_game_scenario(request.get("filing"))
            elif method == "filing_package":
                from skills.filing_package_generator import FilingPackageGenerator
                _skill = FilingPackageGenerator()
                result = _skill.generate_package(request.get("package_type"))
            elif method == "generate_motion":
                from skills.motion_generator import MotionGenerator
                _skill = MotionGenerator()
                result = _skill.generate_motion(request.get("motion_type"))
            elif method == "analyze_order":
                from skills.order_analyzer import OrderAnalyzer
                _skill = OrderAnalyzer()
                result = _skill.analyze_order(request.get("order_text"))
            elif method == "score_case":
                from skills.case_strength_scorer import CaseStrengthScorer
                _skill = CaseStrengthScorer()
                result = _skill.generate_scorecard()
            elif method == "cluster_evidence":
                from skills.evidence_clusterer import EvidenceClusterer
                _skill = EvidenceClusterer()
                result = _skill.cluster_by_theme()
            elif method == "build_narrative":
                from skills.narrative_builder import NarrativeBuilder
                _skill = NarrativeBuilder()
                result = _skill.build_statement_of_facts()
            elif method == "build_brief":
                from skills.appellate_brief_builder import AppellateBriefBuilder
                _skill = AppellateBriefBuilder()
                result = _skill.generate_full_brief()
            elif method == "find_authority_graph":
                from skills.authority_graph_navigator import AuthorityGraphNavigator
                _skill = AuthorityGraphNavigator()
                result = _skill.find_supporting_authority(request.get("topic"))
            elif method == "search_citations":
                from skills.citation_network import CitationNetwork
                _skill = CitationNetwork()
                result = _skill.search_citations(request.get("query"))
            elif method == "build_complete_timeline":
                from skills.chronology_engine import ChronologyEngine
                _skill = ChronologyEngine()
                result = _skill.build_complete_timeline()
            elif method == "alienation_analysis":
                from skills.alienation_analyzer import AlienationAnalyzer
                _skill = AlienationAnalyzer()
                result = _skill.analyze_factor_j()
            elif method == "forensic_report":
                from skills.forensic_analyzer import ForensicAnalyzer
                _skill = ForensicAnalyzer()
                result = _skill.generate_forensic_report()
            elif method == "weaponization_report":
                from skills.weaponization_tracker import WeaponizationTracker
                _skill = WeaponizationTracker()
                result = _skill.generate_weaponization_report()
            elif method == "witness_prep":
                from witness_prep import WitnessPrep
                _skill = WitnessPrep()
                result = _skill.build_impeachment_packet(request.get("witness"))
            elif method == "risk_dashboard":
                from risk_assessor import RiskAssessor
                _skill = RiskAssessor()
                result = _skill.generate_risk_dashboard()

            # ── EPOCH v4.0 Engines ────────────────────────────
            elif method == "semantic_search":
                from semantic_engine import SemanticEngine
                _eng = SemanticEngine()
                _q = request.get("query", request.get("text", ""))
                _k = request.get("top_k", 10)
                hits = _eng.search(_q, top_k=_k)
                result = {"hits": hits, "count": len(hits), "engine": "LSI-300d", "status": "ok"}

            elif method == "pagerank_score":
                from authority_pagerank import AuthorityPageRank
                _eng = AuthorityPageRank()
                _node = request.get("node", request.get("authority", ""))
                if _node:
                    score = _eng.get_score(_node)
                    top_n = _eng.get_top_authorities(request.get("top_k", 20))
                    path = _eng.shortest_path(_node, request.get("target", "")) if request.get("target") else None
                    result = {"node": _node, "score": score, "top_authorities": top_n, "path": path, "status": "ok"}
                else:
                    top_n = _eng.get_top_authorities(request.get("top_k", 20))
                    result = {"top_authorities": top_n, "status": "ok"}

            elif method == "contradiction_scan":
                from contradiction_discovery import ContradictionDiscovery
                _eng = ContradictionDiscovery()
                _speaker = request.get("speaker", "watson")
                _limit = request.get("limit", 50)
                found = _eng.discover(speaker=_speaker, limit=_limit)
                result = {"contradictions": found, "count": len(found), "status": "ok"}

            elif method == "chain_evidence":
                from evidence_chains import EvidenceChainBuilder
                _eng = EvidenceChainBuilder()
                _q = request.get("query", request.get("text", ""))
                _hops = request.get("max_hops", 4)
                chains = _eng.build_chains(_q, max_hops=_hops)
                result = {"chains": chains, "count": len(chains), "status": "ok"}

            elif method == "temporal_anomaly":
                from temporal_analyzer import TemporalAnalyzer
                _eng = TemporalAnalyzer()
                analysis = _eng.analyze()
                result = {"clusters": analysis.get("clusters", []), "suspicious": analysis.get("suspicious_count", 0),
                          "separation_days": analysis.get("separation_days", 0), "status": "ok"}

            elif method == "filing_optimize":
                from filing_optimizer import FilingOptimizer
                _eng = FilingOptimizer()
                _lanes = request.get("lanes", None)
                sims = _eng.simulate(lanes=_lanes, n_runs=request.get("n_runs", 1000))
                result = {"simulations": sims, "count": len(sims), "status": "ok"}

            elif method == "rerank":
                from reranker import Reranker
                _eng = Reranker()
                _q = request.get("query", request.get("text", ""))
                _docs = request.get("documents", [])
                ranked = _eng.rerank(_q, _docs, top_k=request.get("top_k", 10))
                result = {"ranked": ranked, "count": len(ranked), "status": "ok"}

            # ── EPOCH v5.0 Engines ────────────────────────────
            elif method == "hybrid_search":
                from hybrid_retriever import HybridRetriever
                _eng = HybridRetriever()
                _q = request.get("query", request.get("text", ""))
                hits = _eng.search(_q, top_k=request.get("top_k", 10),
                                   methods=request.get("methods"))
                result = {"hits": hits, "count": len(hits), "engine": "hybrid-rrf", "status": "ok"}

            elif method == "bm25_search":
                from bm25_engine import BM25Engine
                _eng = BM25Engine()
                _q = request.get("query", request.get("text", ""))
                hits = _eng.search(_q, top_k=request.get("top_k", 10),
                                   table_filter=request.get("table_filter"))
                result = {"hits": hits, "count": len(hits), "engine": "bm25s", "status": "ok"}

            elif method == "graph_rag":
                from graph_rag import GraphRAG
                _eng = GraphRAG()
                _q = request.get("query", request.get("text", ""))
                answer = _eng.query(_q, max_hops=request.get("max_hops", 3))
                result = {**answer, "status": "ok"}

            elif method == "knowledge_graph":
                from knowledge_graph import KnowledgeGraphEngine
                _eng = KnowledgeGraphEngine()
                _action = request.get("action", "stats")
                if _action == "stats":
                    result = {**_eng.get_stats(), "status": "ok"}
                elif _action == "centrality":
                    result = {"centrality": _eng.centrality_analysis(request.get("top_k", 20)), "status": "ok"}
                elif _action == "communities":
                    result = {"communities": _eng.community_detection(), "status": "ok"}
                elif _action == "path":
                    result = {"path": _eng.find_path(request.get("source", ""), request.get("target", "")), "status": "ok"}
                elif _action == "subgraph":
                    result = {"subgraph": _eng.subgraph_around(request.get("node", ""), request.get("depth", 2)), "status": "ok"}
                else:
                    result = {"error": f"Unknown KG action: {_action}"}

            elif method == "corrective_query":
                from corrective_rag import CorrectiveRAG
                _eng = CorrectiveRAG()
                _q = request.get("query", request.get("text", ""))
                answer = _eng.corrective_query(_q)
                result = {**answer, "status": "ok"}

            elif method == "litigation_state":
                from litigation_fsm import LitigationFSM
                _eng = LitigationFSM()
                _action = request.get("action", "all_states")
                if _action == "all_states":
                    result = {"states": _eng.get_all_states(), "status": "ok"}
                elif _action == "get_state":
                    result = {"state": _eng.get_state(request.get("lane", "A")), "status": "ok"}
                elif _action == "transition":
                    result = {"result": _eng.transition(request.get("lane", "A"), request.get("transition_action", "")), "status": "ok"}
                elif _action == "next_actions":
                    result = {"actions": _eng.get_next_actions(), "status": "ok"}
                elif _action == "deadlines":
                    result = {"deadlines": _eng.get_deadlines(request.get("lane")), "status": "ok"}
                else:
                    result = {"error": f"Unknown FSM action: {_action}"}

            elif method == "resolve_entity":
                from entity_resolver import EntityResolver
                _eng = EntityResolver()
                _text = request.get("text", request.get("query", ""))
                if request.get("profile"):
                    result = {"profile": _eng.get_entity_profile(request.get("profile")), "status": "ok"}
                else:
                    result = {"entities": _eng.resolve(_text), "status": "ok"}

            elif method == "expand_query":
                from query_expander import QueryExpander
                _eng = QueryExpander()
                _q = request.get("query", request.get("text", ""))
                expanded = _eng.expand(_q)
                result = {"original": _q, "expanded": expanded, "status": "ok"}

            elif method == "dashboard":
                # Text-mode dashboard data
                from tui_dashboard import get_dashboard_data
                result = {**get_dashboard_data(), "status": "ok"}

            # ── EPOCH v6.0: Litigation Intelligence Engines ──────────
            elif method == "impeachment_outline":
                from impeachment_generator import ImpeachmentGenerator
                ig = model._get_engine('impeachment', ImpeachmentGenerator, DB_PATH)
                speaker = params.get("speaker", "Tiffany Watson")
                result = ig.generate_cross_exam_outline(speaker)
            elif method == "impeachment_strongest":
                from impeachment_generator import ImpeachmentGenerator
                ig = model._get_engine('impeachment', ImpeachmentGenerator, DB_PATH)
                speaker = params.get("speaker", "Tiffany Watson")
                top_n = params.get("top_n", 10)
                result = ig.find_strongest_impeachment(speaker, top_n)
            elif method == "impeachment_brief":
                from impeachment_generator import ImpeachmentGenerator
                ig = model._get_engine('impeachment', ImpeachmentGenerator, DB_PATH)
                speaker = params.get("speaker", "Tiffany Watson")
                result = ig.generate_impeachment_brief_section(speaker)
            elif method == "judicial_violations":
                from judicial_violation_analyzer import JudicialViolationAnalyzer
                jva = model._get_engine('judicial_violations', JudicialViolationAnalyzer, DB_PATH)
                judge = params.get("judge", "Jenny L. McNeill")
                result = jva.analyze_violation_patterns(judge)
            elif method == "jtc_complaint":
                from judicial_violation_analyzer import JudicialViolationAnalyzer
                jva = model._get_engine('judicial_violations', JudicialViolationAnalyzer, DB_PATH)
                judge = params.get("judge", "Jenny L. McNeill")
                result = jva.generate_jtc_complaint_sections(judge)
            elif method == "disqualification_grounds":
                from judicial_violation_analyzer import JudicialViolationAnalyzer
                jva = model._get_engine('judicial_violations', JudicialViolationAnalyzer, DB_PATH)
                judge = params.get("judge", "Jenny L. McNeill")
                result = jva.find_disqualification_grounds(judge)
            elif method == "timeline_build":
                from timeline_engine import TimelineEngine
                te = model._get_engine('timeline', TimelineEngine, DB_PATH)
                result = te.build_unified_timeline(
                    start_date=params.get("start_date"),
                    end_date=params.get("end_date"),
                    lanes=params.get("lanes"))
            elif method == "timeline_anomalies":
                from timeline_engine import TimelineEngine
                te = model._get_engine('timeline', TimelineEngine, DB_PATH)
                result = te.find_temporal_anomalies()
            elif method == "timeline_separation":
                from timeline_engine import TimelineEngine
                te = model._get_engine('timeline', TimelineEngine, DB_PATH)
                result = te.build_separation_timeline()
            elif method == "timeline_chronology":
                from timeline_engine import TimelineEngine
                te = model._get_engine('timeline', TimelineEngine, DB_PATH)
                result = te.generate_chronology_section(
                    start_date=params.get("start_date"),
                    end_date=params.get("end_date"))
            elif method == "filing_assemble":
                from filing_assembler import FilingAssembler
                fa = model._get_engine('filing_assembler', FilingAssembler, DB_PATH)
                result = fa.assemble_filing_package(
                    filing_type=params.get("filing_type", "motion"),
                    title=params.get("title", ""),
                    issues=params.get("issues", []),
                    evidence_ids=params.get("evidence_ids"))
            elif method == "filing_validate":
                from filing_assembler import FilingAssembler
                fa = model._get_engine('filing_assembler', FilingAssembler, DB_PATH)
                result = fa.validate_filing(params.get("document_text", ""))
            elif method == "filing_caption":
                from filing_assembler import FilingAssembler
                fa = model._get_engine('filing_assembler', FilingAssembler, DB_PATH)
                result = {"caption": fa.generate_caption(
                    case_number=params.get("case_number", "2024-001507-DC"),
                    case_type=params.get("case_type", "custody"),
                    document_title=params.get("title", "MOTION"))}
            elif method == "adversarial_predict":
                from adversarial_engine import AdversarialEngine
                ae = model._get_engine('adversarial', AdversarialEngine, DB_PATH)
                result = ae.predict_attacks(
                    filing_type=params.get("filing_type", "motion"),
                    claims_list=params.get("claims"))
            elif method == "adversarial_risk":
                from adversarial_engine import AdversarialEngine
                ae = model._get_engine('adversarial', AdversarialEngine, DB_PATH)
                result = ae.assess_litigation_risk(lane=params.get("lane"))
            elif method == "citation_gaps":
                from citation_gap_finder import CitationGapFinder
                cgf = model._get_engine('citation_gaps', CitationGapFinder, DB_PATH)
                result = cgf.generate_gap_report(lane=params.get("lane"))
            elif method == "citation_validate":
                from citation_gap_finder import CitationGapFinder
                cgf = model._get_engine('citation_gaps', CitationGapFinder, DB_PATH)
                result = cgf.validate_citations(params.get("text", ""))
            elif method == "compliance_check":
                from compliance_engine import ComplianceEngine
                ce = model._get_engine('compliance', ComplianceEngine, DB_PATH)
                result = ce.check_filing_compliance(
                    document_text=params.get("document_text", ""),
                    filing_type=params.get("filing_type", "motion"))
            elif method == "compliance_checklist":
                from compliance_engine import ComplianceEngine
                ce = model._get_engine('compliance', ComplianceEngine, DB_PATH)
                result = ce.generate_compliance_checklist(
                    filing_type=params.get("filing_type", "motion"))
            elif method == "compliance_traps":
                from compliance_engine import ComplianceEngine
                ce = model._get_engine('compliance', ComplianceEngine, DB_PATH)
                result = ce.detect_procedural_traps()
            elif method == "admissibility_score":
                from admissibility_scorer import AdmissibilityScorer
                asc = model._get_engine('admissibility', AdmissibilityScorer, DB_PATH)
                result = asc.score_admissibility(
                    evidence_text=params.get("text", ""),
                    evidence_type=params.get("type"),
                    speaker=params.get("speaker"))
            elif method == "admissibility_objections":
                from admissibility_scorer import AdmissibilityScorer
                asc = model._get_engine('admissibility', AdmissibilityScorer, DB_PATH)
                result = asc.predict_objections(
                    evidence_text=params.get("text", ""),
                    evidence_type=params.get("type"))

            # ── EPOCH v7.0: Autonomous Intelligence Layer ────────────
            elif method == "memory_store":
                from persistent_memory import PersistentMemory
                pm = model._get_engine('memory', PersistentMemory, DB_PATH)
                result = {"id": pm.store(
                    memory_type=params.get("type", "insight"),
                    key=params.get("key", ""),
                    value=params.get("value", ""),
                    confidence=params.get("confidence", 0.5),
                    source=params.get("source"))}
            elif method == "memory_recall":
                from persistent_memory import PersistentMemory
                pm = model._get_engine('memory', PersistentMemory, DB_PATH)
                result = pm.recall(
                    memory_type=params.get("type"),
                    key=params.get("key"),
                    min_confidence=params.get("min_confidence", 0.0),
                    limit=params.get("limit", 50))
            elif method == "memory_stats":
                from persistent_memory import PersistentMemory
                pm = model._get_engine('memory', PersistentMemory, DB_PATH)
                result = pm.get_memory_stats()
            elif method == "engine_health":
                from persistent_memory import PersistentMemory
                pm = model._get_engine('memory', PersistentMemory, DB_PATH)
                result = pm.get_engine_health()
            elif method == "self_evolve":
                from self_evolve_v2 import SelfEvolver
                se = model._get_engine('self_evolve', SelfEvolver, DB_PATH, os.path.join(os.path.dirname(__file__), 'model_data'))
                result = se.auto_improve_cycle()
            elif method == "evolve_report":
                from self_evolve_v2 import SelfEvolver
                se = model._get_engine('self_evolve', SelfEvolver, DB_PATH, os.path.join(os.path.dirname(__file__), 'model_data'))
                result = {"report": se.generate_improvement_report()}
            elif method == "orchestrate":
                from orchestrator import Orchestrator
                orch = model._get_engine('orchestrator', Orchestrator, DB_PATH)
                result = orch.route_query(
                    query_text=params.get("query", ""),
                    context=params.get("context"))
            elif method == "orchestrate_full":
                from orchestrator import Orchestrator
                orch = model._get_engine('orchestrator', Orchestrator, DB_PATH)
                result = orch.run_full_analysis(
                    topic=params.get("topic", ""),
                    lane=params.get("lane"))
            elif method == "system_status":
                from orchestrator import Orchestrator
                orch = model._get_engine('orchestrator', Orchestrator, DB_PATH)
                result = orch.get_system_status()
            elif method == "health_sweep":
                from self_heal_monitor import SelfHealMonitor
                shm = model._get_engine('self_heal', SelfHealMonitor, DB_PATH, os.path.dirname(__file__))
                result = shm.run_health_sweep()
            elif method == "health_dashboard":
                from self_heal_monitor import SelfHealMonitor
                shm = model._get_engine('self_heal', SelfHealMonitor, DB_PATH, os.path.dirname(__file__))
                result = shm.get_health_dashboard()
            elif method == "validate_engines":
                from self_heal_monitor import SelfHealMonitor
                shm = model._get_engine('self_heal', SelfHealMonitor, DB_PATH, os.path.dirname(__file__))
                result = shm.validate_all_python_files()
            elif method == "scan_catalog":
                from scan_ingester import ScanIngester
                si = model._get_engine('scan_ingester', ScanIngester, DB_PATH, params.get('scan_root', r'C:\Users\andre\scans'))
                result = si.catalog_directory()
            elif method == "scan_ingest":
                from scan_ingester import ScanIngester
                si = model._get_engine('scan_ingester', ScanIngester, DB_PATH, params.get('scan_root', r'C:\Users\andre\scans'))
                result = si.ingest_batch(
                    batch_size=params.get("batch_size", 100),
                    file_types=params.get("file_types"),
                    doc_types=params.get("doc_types"))
            elif method == "scan_stats":
                from scan_ingester import ScanIngester
                si = model._get_engine('scan_ingester', ScanIngester, DB_PATH, params.get('scan_root', r'C:\Users\andre\scans'))
                result = si.get_ingestion_stats()
            elif method == "classify_doc":
                from doc_classifier import DocumentClassifier
                dc = model._get_engine('doc_classifier', DocumentClassifier, DB_PATH, os.path.join(os.path.dirname(__file__), 'model_data'))
                result = dc.classify(params.get("text", ""), return_proba=params.get("proba", False))
            elif method == "classify_file":
                from doc_classifier import DocumentClassifier
                dc = model._get_engine('doc_classifier', DocumentClassifier, DB_PATH, os.path.join(os.path.dirname(__file__), 'model_data'))
                result = dc.classify_file(params.get("file_path", ""))
            elif method == "mine_patterns":
                from pattern_miner import PatternMiner
                pm = model._get_engine('pattern_miner', PatternMiner, DB_PATH)
                result = pm.generate_pattern_report()
            elif method == "mine_judicial":
                from pattern_miner import PatternMiner
                pm = model._get_engine('pattern_miner', PatternMiner, DB_PATH)
                result = pm.mine_judicial_patterns()
            elif method == "mine_contradictions":
                from pattern_miner import PatternMiner
                pm = model._get_engine('pattern_miner', PatternMiner, DB_PATH)
                result = pm.mine_contradiction_patterns()
            elif method == "cluster_evidence":
                from pattern_miner import PatternMiner
                pm = model._get_engine('pattern_miner', PatternMiner, DB_PATH)
                result = pm.cluster_evidence(n_clusters=params.get("n_clusters", 10))

            elif method == "convert_filing":
                from filing_converter import convert_filing as _convert_filing
                _md_path = request.get("md_path", request.get("file_path", ""))
                _out_path = request.get("output_path")
                _out = _convert_filing(_md_path, _out_path)
                result = {"output_path": _out, "status": "ok"}
            elif method == "convert_all_filings":
                from filing_converter import convert_all_filings as _convert_batch
                _dir = request.get("filing_dir", request.get("directory", ""))
                _results = _convert_batch(_dir)
                result = {"files": _results, "count": len(_results), "status": "ok"}

            elif method == "error_log":
                from error_logger import get_recent_errors
                result = get_recent_errors(
                    limit=params.get("limit", 50),
                    severity=params.get("severity"),
                    engine=params.get("engine"),
                )

            elif method == "citation_validate_file":
                from citation_validator import rpc_validate_file
                result = rpc_validate_file(params, DB_PATH)
            elif method == "citation_validate_text":
                from citation_validator import rpc_validate_text
                result = rpc_validate_text(params, DB_PATH)

            # ── EPOCH v8.0: Federal Jurisdiction Engine ──────────────
            elif method == "section_1983_analysis":
                from skills.federal_jurisdiction import FederalJurisdictionEngine
                result = FederalJurisdictionEngine().section_1983_analysis(params)
            elif method == "judicial_immunity_analysis":
                from skills.federal_jurisdiction import FederalJurisdictionEngine
                result = FederalJurisdictionEngine().judicial_immunity_analysis(params)
            elif method == "frcp_compliance_check":
                from skills.federal_jurisdiction import FederalJurisdictionEngine
                result = FederalJurisdictionEngine().frcp_compliance_check(params)
            elif method == "abstention_defense":
                from skills.federal_jurisdiction import FederalJurisdictionEngine
                result = FederalJurisdictionEngine().abstention_defense_analysis(params)
            elif method == "federal_deadlines":
                from skills.federal_jurisdiction import FederalJurisdictionEngine
                result = FederalJurisdictionEngine().federal_deadlines(params)
            elif method == "federal_filing_template":
                from skills.federal_jurisdiction import FederalJurisdictionEngine
                result = FederalJurisdictionEngine().federal_filing_template(params)
            elif method == "sixth_circuit_standards":
                from skills.federal_jurisdiction import FederalJurisdictionEngine
                result = FederalJurisdictionEngine().sixth_circuit_standards(params)

            # ── EPOCH v8.0: Response Drafter ─────────────────────────
            elif method == "draft_response":
                from skills.response_drafter import ResponseDrafter
                result = ResponseDrafter().draft_response(params)
            elif method == "counter_arguments":
                from skills.response_drafter import ResponseDrafter
                result = ResponseDrafter().counter_arguments(params)
            elif method == "response_deadline":
                from skills.response_drafter import ResponseDrafter
                result = ResponseDrafter().calculate_deadline(params)

            # ── EPOCH v8.0: Hearing Preparation ──────────────────────
            elif method == "prep_motion_hearing":
                from skills.hearing_prep import HearingPrepEngine
                result = HearingPrepEngine().prep_motion_hearing(params)
            elif method == "prep_evidentiary_hearing":
                from skills.hearing_prep import HearingPrepEngine
                result = HearingPrepEngine().prep_evidentiary_hearing(params)
            elif method == "prep_oral_argument":
                from skills.hearing_prep import HearingPrepEngine
                result = HearingPrepEngine().prep_oral_argument(params)
            elif method == "prep_emergency_hearing":
                from skills.hearing_prep import HearingPrepEngine
                result = HearingPrepEngine().prep_emergency_hearing(params)
            elif method == "objection_card":
                from skills.hearing_prep import HearingPrepEngine
                result = HearingPrepEngine().generate_objection_card(params)
            elif method == "mcneill_tactical":
                from skills.hearing_prep import HearingPrepEngine
                result = HearingPrepEngine().mcneill_tactical_brief(params)
            elif method == "preservation_script":
                from skills.hearing_prep import HearingPrepEngine
                result = HearingPrepEngine().preservation_script(params)
            elif method == "courtroom_checklist":
                from skills.hearing_prep import HearingPrepEngine
                result = HearingPrepEngine().pro_se_courtroom_checklist(params)

            # ── EPOCH v8.0: Service Tracker ──────────────────────────
            elif method == "track_service":
                from skills.service_tracker import ServiceTracker
                result = ServiceTracker().track_service(params)
            elif method == "service_compliance":
                from skills.service_tracker import ServiceTracker
                result = ServiceTracker().check_compliance(params)
            elif method == "generate_cos":
                from skills.service_tracker import ServiceTracker
                result = ServiceTracker().generate_cos(params)
            elif method == "service_matrix":
                from skills.service_tracker import ServiceTracker
                result = ServiceTracker().service_matrix(params)

            # ── EPOCH v8.0: Multi-Forum Compliance ───────────────────
            elif method == "validate_forum_filing":
                from skills.multi_forum_compliance import MultiForumCompliance
                result = MultiForumCompliance().validate_filing(params)
            elif method == "cross_forum_matrix":
                from skills.multi_forum_compliance import MultiForumCompliance
                result = MultiForumCompliance().cross_forum_matrix(params)
            elif method == "forum_requirements":
                from skills.multi_forum_compliance import MultiForumCompliance
                result = MultiForumCompliance().format_requirements(params)
            elif method == "forum_checklist":
                from skills.multi_forum_compliance import MultiForumCompliance
                result = MultiForumCompliance().filing_checklist(params)

            # ── EPOCH v8.5: Shell Watchdog & Process Management ──────
            elif method in ("watchdog_check", "watchdog_status", "watchdog_register_shell",
                           "watchdog_register_agent", "watchdog_complete_agent",
                           "watchdog_shells", "watchdog_agents", "watchdog_events",
                           "watchdog_guard_start"):
                from skills.shell_management import handle as _wd_handle
                result = _wd_handle(method, params)

            # ── EPOCH v9.0: OMEGA-INFINITY Methods ─────────────
            elif method == "startup_diagnostics":
                result = model.startup_diagnostics()
            elif method == "deadline_urgency":
                result = model.deadline_urgency_score(
                    days_threshold=request.get("days_threshold", 30)
                )
            elif method == "filing_optimizer":
                result = model.filing_readiness_optimizer()
            elif method == "evidence_gaps":
                result = model.evidence_gap_detector(
                    vehicle_name=request.get("vehicle")
                )
            elif method == "session_recall":
                # Delegated to session_recall module
                try:
                    from session_recall import SessionRecall
                    sr = SessionRecall()
                    action = request.get("action", "recent")
                    if action == "recent":
                        result = sr.get_recent_sessions(limit=request.get("limit", 10))
                    elif action == "search":
                        result = sr.search_sessions(request.get("query", ""))
                    elif action == "summary":
                        result = sr.get_session_summary(request.get("session_id", ""))
                    else:
                        result = {"error": f"Unknown session_recall action: {action}"}
                except ImportError:
                    result = {"error": "session_recall module not available", "status": "error"}
                except Exception as e:
                    result = {"error": str(e), "status": "error"}

            # ═══ THE NEXUS v1.0 — Unified Intelligence Routes ═══
            elif method.startswith("nexus_"):
                try:
                    from nexus_engine import NexusEngine
                    if not hasattr(run_pipe, '_nexus'):
                        run_pipe._nexus = NexusEngine()
                    nx = run_pipe._nexus
                    sub = method[6:]  # strip "nexus_"
                    if sub == "query":
                        result = nx.query(request.get("text", ""))
                    elif sub == "search":
                        result = nx.search(request.get("text", ""), top_k=request.get("top_k", 20))
                    elif sub == "classify":
                        result = nx.classify(request.get("text", ""))
                    elif sub == "entities":
                        result = nx.extract_entities(request.get("text", ""))
                    elif sub == "citations":
                        result = nx.extract_citations(request.get("text", ""))
                    elif sub == "generate":
                        result = nx.generate(request.get("text", ""))
                    elif sub == "analyze":
                        result = nx.analyze_document(request.get("filepath", request.get("text", "")))
                    elif sub == "judicial":
                        result = nx.analyze_judicial()
                    elif sub == "risk":
                        result = nx.assess_risk()
                    elif sub == "evidence_chain":
                        result = nx.build_evidence_chain(request.get("topic", request.get("text", "")))
                    elif sub == "validate":
                        result = nx.validate_filing(request.get("filepath", ""), request.get("filing_type", "motion"))
                    elif sub == "generate_filing":
                        result = nx.generate_filing(request.get("filing_type", "motion"), request.get("params", {}))
                    elif sub == "graph":
                        result = nx.graph_query(request.get("text", ""))
                    elif sub == "status":
                        result = nx.status()
                    elif sub == "warmup":
                        result = nx.warmup(phase=request.get("phase"))
                    elif sub == "benchmark":
                        result = nx.benchmark()
                    # ═══ Extended NEXUS Routes (FRED + ARG + ALE + Skills) ═══
                    elif sub == "skill":
                        result = nx.dispatch_skill(request.get("skill_name", ""), **request.get("params", {}))
                    elif sub == "skills":
                        result = nx.list_skills()
                    elif sub == "agents":
                        result = nx.list_agents()
                    elif sub == "fred_compliance":
                        result = nx.fred_compliance_check(request.get("text", ""))
                    elif sub == "fred_pipeline":
                        result = nx.fred_document_pipeline(request.get("text", ""))
                    elif sub == "argumentation":
                        result = nx.analyze_argumentation(request.get("text", ""))
                    elif sub == "autonomous":
                        result = nx.autonomous_analyze(request.get("text", ""))
                    elif sub == "evolve":
                        result = nx.evolve()
                    elif sub == "heal":
                        result = nx.heal()
                    elif sub == "remember":
                        result = nx.remember(query=request.get("query"), insight=request.get("insight"))
                    elif sub == "messages":
                        result = nx.analyze_messages(limit=request.get("limit", 100))
                    elif sub == "patterns":
                        result = nx.mine_patterns(topic=request.get("topic"))
                    elif sub == "crossref":
                        result = nx.cross_reference(request.get("text", ""))
                    elif sub == "docket":
                        result = nx.analyze_docket()
                    elif sub == "compliance":
                        result = nx.check_compliance(request.get("filing_type", "motion"))
                    elif sub == "harms":
                        result = nx.calculate_harms()
                    elif sub == "mega_status":
                        result = nx.mega_status()
                    else:
                        result = {"error": f"Unknown nexus method: nexus_{sub}"}
                except ImportError:
                    result = {"error": "nexus_engine module not available", "status": "error"}
                except Exception as e:
                    result = {"error": f"NEXUS error: {str(e)[:200]}", "status": "error"}

            # ═══ HF Legal AI Engine Routes ═══
            elif method.startswith("hf_"):
                try:
                    import hf_legal_engine as hf_mod
                    sub = method[3:]
                    if sub == "classify":
                        result = hf_mod.classify_legal_document(request.get("text", ""))
                    elif sub == "embeddings":
                        emb = hf_mod.embed_text(request.get("text", ""))
                        result = {"embeddings": emb.tolist() if hasattr(emb, 'tolist') else list(emb), "dim": len(emb)}
                    elif sub == "ner":
                        result = hf_mod.extract_entities(request.get("text", ""))
                    elif sub == "citations":
                        result = hf_mod.extract_citations(request.get("text", ""))
                    elif sub == "similarity":
                        e1 = hf_mod.embed_text(request.get("text1", ""))
                        e2 = hf_mod.embed_text(request.get("text2", ""))
                        import numpy as np
                        sim = float(np.dot(e1, e2) / (np.linalg.norm(e1) * np.linalg.norm(e2) + 1e-9))
                        result = {"similarity": round(sim, 6)}
                    elif sub == "analyze":
                        result = hf_mod.analyze_document(request.get("filepath", request.get("text", "")))
                    elif sub == "benchmark":
                        result = hf_mod.benchmark()
                    else:
                        result = {"error": f"Unknown hf method: hf_{sub}"}
                except ImportError:
                    result = {"error": "hf_legal_engine module not available", "status": "error"}
                except Exception as e:
                    result = {"error": f"HF error: {str(e)[:200]}", "status": "error"}

            else:
                result = {"error": f"Unknown method: {method}"}

            _safe_pipe_write(json.dumps(result))

        except json.JSONDecodeError:
            _safe_pipe_write(json.dumps({"error": "Invalid JSON"}))
        except Exception as e:
            _safe_pipe_write(json.dumps({"error": str(e)[:200]}))


# ──────────────────────────────────────────────────────────────────
# Local LLM Layer (GGUF via llama-cpp-python, no server needed)
# RAG: TF-IDF retrieval -> Local LLM reasoning
# ──────────────────────────────────────────────────────────────────

# ── Tier 1 (fast): Qwen 2.5 1.5B ──
GGUF_MODEL_PATH = os.environ.get(
    "GGUF_MODEL_PATH",
    os.path.join(os.path.dirname(__file__), "gguf", "qwen2.5-1.5b-instruct-q4_k_m.gguf")
)
# ── Tier 2 (legal reasoning): SaulLM-7B ──
SAULLM_MODEL_PATH = os.environ.get(
    "SAULLM_MODEL_PATH",
    os.path.join(os.path.dirname(__file__), "gguf", "saul-instruct-v1.Q5_K_M.gguf")
)
SAULLM_CTX = int(os.environ.get("SAULLM_CTX", "4096"))
GGUF_THREADS = int(os.environ.get("GGUF_THREADS", "4"))
GGUF_CTX = int(os.environ.get("GGUF_CTX", "2048"))

# Keywords that trigger SaulLM legal reasoning tier
_LEGAL_REASONING_KEYWORDS = {
    "mcr ", "mcl ", "mre ", "statute", "ruling", "brief", "motion",
    "irac", "custody", "parenting time", "best interest", "due process",
    "disqualification", "contempt", "appeal", "habeas", "mandamus",
    "superintending", "ex parte", "ppo", "protection order", "§1983",
    "jurisdiction", "court rule", "legal standard", "burden of proof",
}

# Singleton LLM instances (load once, reuse)
_llm_instance = None
_saullm_instance = None

def _get_llm():
    """Load Qwen GGUF model (lazy singleton). ~1s cold start."""
    global _llm_instance
    if _llm_instance is not None:
        return _llm_instance
    try:
        from llama_cpp import Llama
        if not os.path.exists(GGUF_MODEL_PATH):
            print(f"[LLM] Model not found: {GGUF_MODEL_PATH}", file=sys.stderr)
            return None
        _llm_instance = Llama(
            model_path=GGUF_MODEL_PATH,
            n_ctx=GGUF_CTX,
            n_threads=GGUF_THREADS,
            verbose=False
        )
        return _llm_instance
    except ImportError:
        print("[LLM] llama-cpp-python not installed. Run: pip install llama-cpp-python", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[LLM] Load error: {e}", file=sys.stderr)
        return None

def _get_saullm():
    """Load SaulLM-7B GGUF model (lazy singleton). ~3-5s cold start."""
    global _saullm_instance
    if _saullm_instance is not None:
        return _saullm_instance
    try:
        from llama_cpp import Llama
        if not os.path.exists(SAULLM_MODEL_PATH):
            print(f"[SaulLM] Model not found: {SAULLM_MODEL_PATH}", file=sys.stderr)
            return None
        _saullm_instance = Llama(
            model_path=SAULLM_MODEL_PATH,
            n_ctx=SAULLM_CTX,
            n_threads=GGUF_THREADS,
            verbose=False
        )
        print("[SaulLM] SaulLM-7B legal model loaded", file=sys.stderr)
        return _saullm_instance
    except ImportError:
        print("[SaulLM] llama-cpp-python not installed. Run: pip install llama-cpp-python", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[SaulLM] Load error: {e}", file=sys.stderr)
        return None

def _needs_legal_reasoning(text: str) -> bool:
    """Return True if the query should be routed to SaulLM-7B for deeper legal reasoning."""
    lower = text.lower()
    return any(kw in lower for kw in _LEGAL_REASONING_KEYWORDS)

def _llm_generate(system: str, user: str, max_tokens: int = 200, temperature: float = 0.3,
                  tier: str = "auto") -> Optional[str]:
    """Generate with local GGUF model. tier='auto'|'fast'|'legal'. Returns text or None."""
    # Select model based on tier
    if tier == "legal" or (tier == "auto" and _needs_legal_reasoning(user)):
        llm = _get_saullm()
        model_label = "SaulLM-7B"
        if llm is None:
            llm = _get_llm()  # fallback to Qwen
            model_label = "Qwen-1.5B(fallback)"
    else:
        llm = _get_llm()
        model_label = "Qwen-1.5B"
    if not llm:
        return None
    try:
        output = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        return output["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[LLM ERROR] ({model_label}) {e}", file=sys.stderr)
        return None

def _llm_available() -> bool:
    """Check if any GGUF model file exists and llama-cpp-python is installed."""
    try:
        from llama_cpp import Llama  # noqa: F401
        return os.path.exists(GGUF_MODEL_PATH) or os.path.exists(SAULLM_MODEL_PATH)
    except ImportError:
        return False

def _saullm_available() -> bool:
    """Check if SaulLM-7B GGUF model is available."""
    try:
        from llama_cpp import Llama  # noqa: F401
        return os.path.exists(SAULLM_MODEL_PATH)
    except ImportError:
        return False


class LocalLegalRAG:
    """
    RAG layer: TF-IDF/DB retrieval (MichiganLegalModel) + local GGUF LLM.
    3-tier stack: Qwen-1.5B (fast) → SaulLM-7B (legal reasoning) → full pipeline.
    Falls back to pure TF-IDF if model unavailable.
    """

    SYSTEM_PROMPT = (
        "You are a Michigan litigation legal assistant. Case: Pigors v. Watson. "
        "Judge: Hon. Jenny L. McNeill. 14th Circuit Court, Muskegon County. "
        "Cite MCR, MCL, MRE, or case law for every assertion. Use IRAC format. "
        "Be concise. Never fabricate citations."
    )

    def __init__(self, mllm: Optional[MichiganLegalModel] = None):
        self.mllm = mllm or MichiganLegalModel()
        self.llm_ok = _llm_available()
        self.saullm_ok = _saullm_available()
        self.model_name = os.path.basename(GGUF_MODEL_PATH).replace('.gguf', '')
        self.saullm_name = os.path.basename(SAULLM_MODEL_PATH).replace('.gguf', '')

    def query(self, text: str, max_context: int = 600) -> dict:
        """
        Full RAG query: retrieve with MANBEARPIG TF-IDF, reason with local LLM.
        ~15s per response on CPU. Falls back to TF-IDF if LLM unavailable.
        """
        t0 = time.time()

        # Step 1: TF-IDF retrieval
        retrieval = self.mllm.query(text)

        # Step 2: Top 2 authority results (truncated)
        authority = self.mllm.find_authority(text, limit=2)
        auth_text = "\n".join(
            f"- {a.get('source','')}: {str(a.get('text',''))[:150]}"
            for a in authority[:2]
        ) if authority else ""

        # Step 3: Extract concise context from retrieval
        full_resp = retrieval.get("response", "")
        if "## Governing Authority" in full_resp:
            section = full_resp.split("## Governing Authority")[1]
            if "##" in section[10:]:
                section = section[:section.index("##", 10)]
            ctx = section.strip()[:max_context]
        else:
            ctx = full_resp[:max_context]

        # Step 4: Generate with local LLM (auto-routes: SaulLM for legal, Qwen for fast)
        if self.llm_ok:
            use_legal = _needs_legal_reasoning(text)
            tier = "legal" if use_legal and self.saullm_ok else "fast"
            active_model = self.saullm_name if tier == "legal" else self.model_name
            user_prompt = f"CONTEXT:\n{ctx}\n{auth_text}\n\nQUESTION: {text}\n\nAnswer concisely with citations:"
            llm_response = _llm_generate(self.SYSTEM_PROMPT, user_prompt, max_tokens=200, tier=tier)
            if llm_response:
                elapsed = round((time.time() - t0) * 1000, 1)
                return {
                    "response": llm_response,
                    "model": f"RAG({active_model}+MANBEARPIG)",
                    "mode": "llm",
                    "tier": tier,
                    "intent": retrieval.get("intent", "unknown"),
                    "confidence": retrieval.get("confidence", 0),
                    "entities": retrieval.get("entities", {}),
                    "retrieval_count": retrieval.get("retrieval_count", 0),
                    "db_match_count": retrieval.get("db_match_count", 0),
                    "authority_count": len(authority) if authority else 0,
                    "elapsed_ms": elapsed,
                    "cached": False,
                    "llm_model": active_model,
                }

        # Fallback: pure MLLM
        retrieval["model"] = f"MANBEARPIG-fallback (LLM {'not found' if not self.llm_ok else 'failed'})"
        retrieval["mode"] = "tfidf"
        return retrieval

    def status(self) -> dict:
        """System status including local LLM tiers."""
        mllm_status = self.mllm.status()
        mllm_status["llm_available"] = self.llm_ok
        mllm_status["llm_model"] = self.model_name
        mllm_status["llm_path"] = GGUF_MODEL_PATH
        mllm_status["llm_threads"] = GGUF_THREADS
        mllm_status["llm_ctx"] = GGUF_CTX
        mllm_status["saullm_available"] = self.saullm_ok
        mllm_status["saullm_model"] = self.saullm_name
        mllm_status["saullm_path"] = SAULLM_MODEL_PATH
        mllm_status["saullm_ctx"] = SAULLM_CTX
        tiers = []
        if self.llm_ok:
            tiers.append(f"Qwen-1.5B(fast)")
        if self.saullm_ok:
            tiers.append(f"SaulLM-7B(legal)")
        tiers.append("MANBEARPIG(pipeline)")
        mllm_status["model_tiers"] = tiers
        mllm_status["mode"] = f"RAG ({'+'.join(tiers)})" if self.llm_ok else "MANBEARPIG-only (TF-IDF)"
        return mllm_status


# ──────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Encoding safety
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    if "--pipe" in sys.argv:
        run_pipe()
    elif "--status" in sys.argv:
        m = MichiganLegalModel()
        if "--llm" in sys.argv:
            rag = LocalLegalRAG(m)
            cycle_json(rag.status())
        else:
            cycle_json(m.status())
    elif "--llm" in sys.argv:
        # LLM-powered RAG mode (local GGUF, no server needed)
        args = [a for a in sys.argv[1:] if a != "--llm"]
        if not args:
            print("Usage: python inference_engine.py --llm 'your legal question'")
            sys.exit(1)
        query_text = " ".join(args)
        rag = LocalLegalRAG()
        result = rag.query(query_text)
        print(result["response"])
        print(f"\n--- [{result['model']} | {result.get('intent','?')} | "
              f"{result['elapsed_ms']}ms | {result.get('retrieval_count',0)} retrieved | "
              f"{result.get('authority_count',0)} authority] ---")
    elif len(sys.argv) > 1 and sys.argv[1] != "--help":
        query_text = " ".join(sys.argv[1:])
        m = MichiganLegalModel()
        result = m.query(query_text)
        sys.stdout.buffer.write(result["response"].encode("ascii", errors="replace"))
        sys.stdout.buffer.write(b"\n")
        footer = (f"\n--- [{result['model']} | {result['intent']} ({result['confidence']:.0%}) | "
                  f"{result['elapsed_ms']}ms | {result['retrieval_count']} retrieved | "
                  f"{result['db_match_count']} DB matches] ---\n")
        sys.stdout.buffer.write(footer.encode("ascii", errors="replace"))
    else:
        print("MBP LitigationOS -- Michigan Legal Language Model (MLLM)")
        print("Usage:")
        print("  python inference_engine.py 'your legal question'        # TF-IDF retrieval")
        print("  python inference_engine.py --llm 'your legal question'  # RAG (Ollama+TF-IDF)")
        print("  python inference_engine.py --pipe                       # JSON-RPC pipe mode")
        print("  python inference_engine.py --status                     # Model status")
        print("  python inference_engine.py --status --llm               # Status + Ollama")
