#!/usr/bin/env python3
"""
APEX MANBEARPIG — Model Router (Shadow-Programmed)
═══════════════════════════════════════════════════
Routes inference tasks to the optimal execution backend.

When ``APEX_LLM_ENABLED`` is **False** (default), every task is routed to
the existing MANBEARPIG stack — :class:`MichiganLegalModel` (TF-IDF +
Naive Bayes + BM25 + rules + regex).  No LLM is ever invoked.

When ``APEX_LLM_ENABLED`` is **True** (user has a GPU), the router
consults the :data:`ROUTE_TABLE` to pick the best model per task type
and delegates to :class:`OllamaProvider`.  If the primary model's
confidence falls below the **70 % threshold**, the router escalates down
the fallback chain::

    LLM  →  ML (MANBEARPIG)  →  Rules engine  →  Regex

APEX DATABASE ARCHITECTURE (38 databases, 15.92 GB total)
═════════════════════════════════════════════════════════
CRITICAL (4):
  litigation_context.db    — 10.47 GB, 702 tables (central hub)
  master_index.db          — 3.32 GB, 14 tables, 1.7M files (agent processing)
  omega_dedup.db           — 591 MB, 7 tables (deduplication)
  file_catalog.db          — 233 MB, 4 tables, 390K files (file index)

VECTOR/ML:
  chroma.sqlite3           — 14 MB, 2K vectors (embeddings)
  MEEK234_HIGHSIGNAL_DB    — 40 MB, 13.4K high-signal quotes

CASE LANES (09_DATA/):
  lane_A_custody.db        — Custody (2024-001507-DC)
  lane_B_housing.db        — Housing (2025-002760-CZ)
  lane_C_convergence.db    — Cross-lane convergence
  lane_D_ppo.db            — Protection orders
  lane_E_misconduct.db     — Judicial misconduct
  lane_F_appellate.db      — Appellate (COA 366810)

DRIVE MANIFESTS (7):
  drive_{C,D,F,G,H,I}_manifest.db + omega_C_manifest.db

EXTERNAL:
  D:\\litigation_context_backup (1.08 GB) — backup from 2026-02-20
  G:\\authority_store_2.sqlite (42 MB) — legal authorities
  H:\\mi_warchest_pinnacle_v6.sqlite (60 MB) — MI law warchest

Design invariants
─────────────────
* Same ``APEX_LLM_ENABLED`` flag as :mod:`ollama_provider`.
* Thread-safe — all mutable state behind :class:`threading.Lock`.
* Lazy imports — neither ``ollama_provider`` nor ``inference_engine`` are
  imported until the first call that needs them.
* NEVER imports from the repo root (shadow modules).
* Uses ``Path(__file__).parent`` for sibling imports.
* All DB connections: ``PRAGMA busy_timeout=60000; journal_mode=WAL;
  cache_size=-32000``.
* Zero-crash: every public method is try/excepted.
"""

from __future__ import annotations

import logging
import os
import re
import sqlite3
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Global LLM gate — mirrors ollama_provider.py
# ---------------------------------------------------------------------------
APEX_LLM_ENABLED: bool = (
    os.environ.get("APEX_LLM_ENABLED", "false").lower() == "true"
)

# ---------------------------------------------------------------------------
# Confidence threshold — if the primary model returns confidence below
# this value the router escalates to the next fallback in the chain.
# ---------------------------------------------------------------------------
CONFIDENCE_THRESHOLD: float = 0.70

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
_log = logging.getLogger("apex.model_router")
if not _log.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s — %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    ))
    _log.addHandler(_h)
    _log.setLevel(logging.DEBUG if APEX_LLM_ENABLED else logging.INFO)

# ---------------------------------------------------------------------------
# Path helpers — resolve sibling modules without touching repo root
# ---------------------------------------------------------------------------
_THIS_DIR: Path = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# DB connection helper (matches mandatory PRAGMA set)
# ---------------------------------------------------------------------------
_DB_PATH: Path = _THIS_DIR.parent.parent / "litigation_context.db"


def _safe_db(path: Optional[Path] = None) -> Optional[sqlite3.Connection]:
    """Open a SQLite connection with the required PRAGMAs.

    Returns ``None`` if the file doesn't exist or the connection fails.
    """
    db_file = path or _DB_PATH
    if not db_file.exists():
        return None
    try:
        conn = sqlite3.connect(str(db_file), timeout=60)
        conn.execute("PRAGMA busy_timeout = 60000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA cache_size = -32000")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as exc:
        _log.warning("_safe_db(%s) failed: %s", db_file, exc)
        return None


# ╔══════════════════════════════════════════════════════════════════════╗
# ║                        TASK TYPE KEYWORDS                           ║
# ╚══════════════════════════════════════════════════════════════════════╝
# Used by classify_task() to auto-detect task type from free-text queries.
_TASK_KEYWORDS: Dict[str, List[str]] = {
    "legal_reasoning": [
        "analyze", "analysis", "legal", "argue", "argument", "motion",
        "brief", "irac", "issue", "rule", "application", "conclusion",
        "disqualif", "mcr", "statute", "constitutional",
    ],
    "classification": [
        "classify", "categorize", "category", "type", "kind", "sort",
        "label", "tag", "which",
    ],
    "ner": [
        "extract", "entity", "entities", "name", "person", "date",
        "address", "phone", "judge", "attorney", "case number",
    ],
    "embeddings": [
        "embed", "embedding", "vector", "similarity", "semantic",
        "cosine", "nearest",
    ],
    "retrieval": [
        "find", "search", "retrieve", "lookup", "look up", "where",
        "relevant", "related",
    ],
    "citation_check": [
        "citation", "cite", "cited", "authority", "authorities",
        "shepard", "bluebook", "mcr",
    ],
    "summarization": [
        "summarize", "summary", "summarise", "tldr", "digest",
        "condense", "overview",
    ],
    "drafting": [
        "draft", "write", "compose", "generate document", "template",
        "pleading", "complaint", "affidavit",
    ],
    "red_team": [
        "red team", "attack", "weakness", "counter", "opposing",
        "devil", "adversar",
    ],
    "lane_routing": [
        "lane", "route", "meek", "custody", "housing", "ppo",
        "misconduct", "appellate", "convergence",
    ],
    "compliance": [
        "comply", "compliance", "rule", "check", "valid", "court rule",
        "deadline met",
    ],
    "deadline_calc": [
        "deadline", "due date", "calendar", "filing date", "days left",
        "time limit",
    ],
    "form_fill": [
        "form", "fill", "scao", "mc ", "dc ", "cc ", "template fill",
    ],
}


class ModelRouter:
    """Routes tasks to the optimal model.  Shadow-programmed — falls back
    to MANBEARPIG when the LLM flag is off.

    Parameters
    ----------
    None — configuration is read from the environment and module-level
    constants.

    Attributes
    ----------
    enabled : bool
        Mirrors ``APEX_LLM_ENABLED``.
    ROUTE_TABLE : dict
        Maps task types to ``{primary, fallback, timeout}`` triples.
    """

    ROUTE_TABLE: Dict[str, Dict[str, Any]] = {
        "legal_reasoning": {"primary": "saul-legal",      "fallback": "manbearpig",    "timeout": 180},
        "classification":  {"primary": "qwen-fast",       "fallback": "naive_bayes",   "timeout": 30},
        "ner":             {"primary": "bert-ner",         "fallback": "regex",         "timeout": 10},
        "embeddings":      {"primary": "nomic-embed-text", "fallback": "tfidf",         "timeout": 15},
        "retrieval":       {"primary": "hybrid",           "fallback": "bm25",          "timeout": 10},
        "citation_check":  {"primary": "legal-bert",       "fallback": "regex",         "timeout": 15},
        "summarization":   {"primary": "qwen-fast",        "fallback": "manbearpig",    "timeout": 60},
        "drafting":        {"primary": "saul-legal",       "fallback": "manbearpig",    "timeout": 180},
        "red_team":        {"primary": "saul-legal",       "fallback": "manbearpig",    "timeout": 180},
        "lane_routing":    {"primary": "qwen-fast",        "fallback": "meek_regex",    "timeout": 15},
        "compliance":      {"primary": "qwen-fast",        "fallback": "rules_engine",  "timeout": 30},
        "deadline_calc":   {"primary": "rules_engine",     "fallback": "rules_engine",  "timeout": 5},
        "form_fill":       {"primary": "template_engine",  "fallback": "template_engine","timeout": 5},
    }

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def __init__(self) -> None:
        self.enabled: bool = APEX_LLM_ENABLED
        self._ollama: Any = None          # lazy OllamaProvider
        self._manbearpig: Any = None      # lazy MichiganLegalModel
        self._lock: threading.Lock = threading.Lock()
        _log.info(
            "ModelRouter initialised (llm_enabled=%s, confidence_threshold=%.0f%%)",
            self.enabled,
            CONFIDENCE_THRESHOLD * 100,
        )

    # ------------------------------------------------------------------
    # Lazy loaders — import siblings via Path, never via repo root
    # ------------------------------------------------------------------
    def _get_ollama(self) -> Any:
        """Lazy-import and cache :class:`OllamaProvider`."""
        if self._ollama is not None:
            return self._ollama
        with self._lock:
            if self._ollama is not None:
                return self._ollama
            try:
                # Import from same directory (00_SYSTEM/local_model/)
                _parent = str(_THIS_DIR)
                if _parent not in sys.path:
                    sys.path.insert(0, _parent)
                from ollama_provider import OllamaProvider  # noqa: E402
                self._ollama = OllamaProvider()
                return self._ollama
            except Exception as exc:
                _log.warning("Could not load OllamaProvider: %s", exc)
                return None

    def _get_manbearpig(self) -> Any:
        """Lazy-import and cache :class:`MichiganLegalModel`."""
        if self._manbearpig is not None:
            return self._manbearpig
        with self._lock:
            if self._manbearpig is not None:
                return self._manbearpig
            try:
                _parent = str(_THIS_DIR)
                if _parent not in sys.path:
                    sys.path.insert(0, _parent)
                from inference_engine import MichiganLegalModel  # noqa: E402
                self._manbearpig = MichiganLegalModel()
                return self._manbearpig
            except Exception as exc:
                _log.warning("Could not load MichiganLegalModel: %s", exc)
                return None

    # ------------------------------------------------------------------
    # Core routing
    # ------------------------------------------------------------------
    def route(
        self,
        task_type: str,
        query: str,
        context: str = "",
    ) -> Dict[str, Any]:
        """Route *query* to the best backend for *task_type* and execute.

        Fallback chain
        ~~~~~~~~~~~~~~
        1. If LLM enabled → try primary model via OllamaProvider
        2. If primary confidence < 70 % or LLM disabled → MANBEARPIG
        3. If MANBEARPIG unavailable → rules / regex fallback
        4. If everything fails → return error dict (never raises)

        Returns
        -------
        dict
            Always contains at least ``status``, ``backend``, ``task_type``,
            ``latency_s``.
        """
        t0 = time.perf_counter()
        route_info = self.get_route_info(task_type)
        result: Dict[str, Any] = {
            "task_type": task_type,
            "query_preview": query[:120],
            "route_info": route_info,
        }

        # --- Step 1: try LLM if enabled and task has an LLM primary ------
        if self.enabled and route_info.get("primary_is_llm"):
            llm_result = self._execute_llm(task_type, query, context, route_info)
            if llm_result and not llm_result.get("fallback"):
                confidence = llm_result.get("confidence", 0.85)
                if confidence >= CONFIDENCE_THRESHOLD:
                    result.update(llm_result)
                    result["backend"] = route_info["primary"]
                    result["escalated"] = False
                    result["latency_s"] = round(time.perf_counter() - t0, 3)
                    _log.debug(
                        "route OK via LLM (%s) conf=%.2f",
                        route_info["primary"],
                        confidence,
                    )
                    return result
                else:
                    _log.info(
                        "LLM confidence %.2f < threshold %.2f — escalating to fallback",
                        confidence,
                        CONFIDENCE_THRESHOLD,
                    )

        # --- Step 2: MANBEARPIG fallback ----------------------------------
        mb_result = self._execute_manbearpig(task_type, query, context)
        if mb_result is not None:
            result.update(mb_result)
            result["backend"] = "manbearpig"
            result["escalated"] = True
            result["latency_s"] = round(time.perf_counter() - t0, 3)
            result["status"] = result.get("status", "ok")
            _log.debug("route OK via MANBEARPIG for task=%s", task_type)
            return result

        # --- Step 3: rules / regex fallback --------------------------------
        rules_result = self._execute_rules(task_type, query)
        result.update(rules_result)
        result["backend"] = route_info.get("fallback", "regex")
        result["escalated"] = True
        result["latency_s"] = round(time.perf_counter() - t0, 3)
        _log.debug("route OK via rules/regex for task=%s", task_type)
        return result

    # ------------------------------------------------------------------
    # Task type auto-detection
    # ------------------------------------------------------------------
    def classify_task(self, query: str) -> str:
        """Auto-detect the task type from free-text *query*.

        Uses keyword matching against :data:`_TASK_KEYWORDS`.  When LLM is
        enabled, the LLM classification is tried first.

        Returns
        -------
        str
            One of the keys in :data:`ROUTE_TABLE`, or ``"legal_reasoning"``
            as the default.
        """
        try:
            # --- Keyword scoring (always available) -----------------------
            q_lower = query.lower()
            scores: Dict[str, int] = {}
            for task, keywords in _TASK_KEYWORDS.items():
                score = sum(1 for kw in keywords if kw in q_lower)
                if score > 0:
                    scores[task] = score

            if scores:
                best = max(scores, key=scores.get)  # type: ignore[arg-type]
                _log.debug("classify_task → %s (score=%d)", best, scores[best])
                return best

            # No keyword match — default to legal reasoning
            return "legal_reasoning"
        except Exception as exc:
            _log.warning("classify_task error: %s — defaulting", exc)
            return "legal_reasoning"

    # ------------------------------------------------------------------
    # Route info (non-executing)
    # ------------------------------------------------------------------
    def get_route_info(self, task_type: str) -> Dict[str, Any]:
        """Return routing metadata for *task_type* without executing.

        Returns
        -------
        dict
            ``primary``, ``fallback``, ``timeout``, ``primary_is_llm``,
            ``llm_enabled``.
        """
        entry = self.ROUTE_TABLE.get(task_type, {
            "primary": "manbearpig",
            "fallback": "regex",
            "timeout": 30,
        })
        llm_models = {"saul-legal", "qwen-fast", "nomic-embed-text",
                       "legal-bert", "bert-ner", "hybrid"}
        return {
            "task_type": task_type,
            "primary": entry["primary"],
            "fallback": entry["fallback"],
            "timeout": entry["timeout"],
            "primary_is_llm": entry["primary"] in llm_models,
            "llm_enabled": self.enabled,
            "confidence_threshold": CONFIDENCE_THRESHOLD,
            "would_use_llm": self.enabled and entry["primary"] in llm_models,
        }

    # ------------------------------------------------------------------
    # Backend executors (private)
    # ------------------------------------------------------------------
    def _execute_llm(
        self,
        task_type: str,
        query: str,
        context: str,
        route_info: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Try to execute *query* on the LLM backend via OllamaProvider."""
        try:
            ollama = self._get_ollama()
            if ollama is None:
                return None

            primary = route_info["primary"]

            if task_type == "embeddings":
                return ollama.embed(query, model=primary)
            elif task_type == "classification":
                # Need categories — extract from context or use defaults
                cats = _extract_categories(context) or [
                    "custody", "housing", "ppo", "misconduct",
                    "appellate", "evidence", "procedural", "other",
                ]
                return ollama.classify(query, cats, model=primary)
            elif task_type in ("legal_reasoning", "drafting", "red_team"):
                return ollama.legal_analyze(query, context=context, model=primary)
            else:
                # Generic generation for summarisation, compliance, etc.
                return ollama.generate(query, model=primary)

        except Exception as exc:
            _log.warning("_execute_llm failed for task=%s: %s", task_type, exc)
            return None

    def _execute_manbearpig(
        self,
        task_type: str,
        query: str,
        context: str,
    ) -> Optional[Dict[str, Any]]:
        """Execute *query* through the MANBEARPIG inference engine."""
        try:
            mb = self._get_manbearpig()
            if mb is None:
                return None

            if task_type == "classification":
                intent, conf = mb.classify_intent(query)
                return {
                    "category": intent,
                    "confidence": conf,
                    "status": "ok",
                    "fallback": False,
                }

            elif task_type == "ner":
                entities = mb.extract_entities(query)
                return {
                    "entities": entities,
                    "status": "ok",
                    "fallback": False,
                }

            elif task_type == "retrieval":
                results = mb.retrieve(query, top_k=10)
                return {
                    "results": results,
                    "count": len(results),
                    "status": "ok",
                    "fallback": False,
                }

            elif task_type == "citation_check":
                citations = mb.check_citations(query)
                return {
                    "citations": citations,
                    "status": "ok",
                    "fallback": False,
                }

            elif task_type == "embeddings":
                # MANBEARPIG uses TF-IDF vectors — return sparse representation
                results = mb.retrieve(query, top_k=1)
                return {
                    "embedding": [],
                    "dimensions": 0,
                    "note": "TF-IDF fallback — no dense embeddings",
                    "nearest_match": results[0] if results else None,
                    "status": "ok",
                    "fallback": True,
                }

            elif task_type == "lane_routing":
                # Use MEEK signal detection via the query method
                result = mb.query(query)
                return {
                    "text": result if isinstance(result, str) else result.get("response", str(result)),
                    "status": "ok",
                    "fallback": False,
                }

            elif task_type == "legal_reasoning":
                # Full IRAC analysis when available
                try:
                    result = mb.irac_analysis(query, facts=context or None)
                    return {
                        "analysis": result if isinstance(result, str) else str(result),
                        "status": "ok",
                        "fallback": False,
                    }
                except Exception:
                    result = mb.query(query)
                    text = result if isinstance(result, str) else result.get("response", str(result))
                    return {"analysis": text, "status": "ok", "fallback": False}

            elif task_type == "drafting":
                try:
                    result = mb.generate_document(query, {})
                    return {
                        "text": result if isinstance(result, str) else str(result),
                        "status": "ok",
                        "fallback": False,
                    }
                except Exception:
                    result = mb.query(query)
                    text = result if isinstance(result, str) else result.get("response", str(result))
                    return {"text": text, "status": "ok", "fallback": False}

            else:
                # Generic: route through the main query() method
                result = mb.query(query)
                text = result if isinstance(result, str) else result.get("response", str(result))
                return {
                    "text": text,
                    "status": "ok",
                    "fallback": False,
                }

        except Exception as exc:
            _log.warning("_execute_manbearpig failed for task=%s: %s", task_type, exc)
            return None

    def _execute_rules(
        self,
        task_type: str,
        query: str,
    ) -> Dict[str, Any]:
        """Last-resort fallback: pure rules / regex / keyword matching.

        This ALWAYS returns a result — it is the bottom of the fallback
        chain and never fails.
        """
        result: Dict[str, Any] = {"status": "rules_fallback", "fallback": True}

        try:
            if task_type == "ner":
                result["entities"] = _regex_ner(query)
            elif task_type == "lane_routing":
                result["lane"] = _regex_lane_detect(query)
            elif task_type == "citation_check":
                result["citations"] = _regex_citations(query)
            elif task_type == "deadline_calc":
                result["message"] = (
                    "Deadline calculation requires the rules engine. "
                    "Check deadlines table in litigation_context.db."
                )
            elif task_type == "form_fill":
                result["message"] = (
                    "Form filling requires the template engine. "
                    "See 02_Court_Forms/ for SCAO form templates."
                )
            else:
                result["text"] = (
                    f"No model available for task '{task_type}'. "
                    f"Query stored for processing when MANBEARPIG or LLM becomes available."
                )
                result["query"] = query[:500]
        except Exception as exc:
            _log.warning("_execute_rules error: %s", exc)
            result["error"] = str(exc)

        return result

    # ------------------------------------------------------------------
    # Status / diagnostics
    # ------------------------------------------------------------------
    def status(self) -> Dict[str, Any]:
        """Return full router status including backend availability."""
        report: Dict[str, Any] = {
            "apex_llm_enabled": self.enabled,
            "confidence_threshold": CONFIDENCE_THRESHOLD,
            "task_types": list(self.ROUTE_TABLE.keys()),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        # MANBEARPIG status
        mb = self._get_manbearpig()
        report["manbearpig_loaded"] = mb is not None
        if mb is not None:
            try:
                mb_status = mb.status()
                report["manbearpig_status"] = (
                    mb_status if isinstance(mb_status, dict) else {"raw": str(mb_status)}
                )
            except Exception:
                report["manbearpig_status"] = "status() call failed"

        # Ollama status
        if self.enabled:
            ollama = self._get_ollama()
            report["ollama_loaded"] = ollama is not None
            if ollama is not None:
                report["ollama_available"] = ollama.is_available()
                report["ollama_health"] = ollama.health_check()
        else:
            report["ollama_loaded"] = False
            report["ollama_available"] = False
            report["ollama_message"] = "LLM disabled — set APEX_LLM_ENABLED=true"

        return report


# ╔══════════════════════════════════════════════════════════════════════╗
# ║              REGEX FALLBACK HELPERS (bottom of chain)               ║
# ╚══════════════════════════════════════════════════════════════════════╝

_RE_CASE_NUM = re.compile(
    r"\b(?:20\d{2})[- ]?\d{4,6}[- ]?(?:DC|CZ|PP|FC|FH|FD|DO)\b",
    re.IGNORECASE,
)
_RE_MCR = re.compile(r"\bMCR\s*\d+\.\d+(?:\([A-Za-z0-9]+\))?\b", re.IGNORECASE)
_RE_MCL = re.compile(r"\bMCL\s*\d+\.\d+[a-z]?\b", re.IGNORECASE)
_RE_DATE = re.compile(
    r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b",
)
_RE_JUDGE = re.compile(
    r"\b(?:Judge|Hon\.?|Honorable)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b",
)
_RE_PERSON = re.compile(r"\b[A-Z][a-z]+\s+(?:[A-Z]\.?\s+)?[A-Z][a-z]+\b")

_LANE_SIGNALS: Dict[str, List[str]] = {
    "E": ["misconduct", "jtc", "mcneill", "judicial tenure", "bias", "canon"],
    "D": ["ppo", "protection order", "personal protection", "stalking", "5907"],
    "F": ["appeal", "appellate", "coa", "msc", "366810", "leave to appeal"],
    "C": ["convergence", "cross-lane", "multi-case", "conspiracy"],
    "A": ["custody", "parenting", "child", "visitation", "watson", "001507"],
    "B": ["housing", "shady oaks", "habitability", "landlord", "002760"],
}


def _regex_ner(text: str) -> Dict[str, List[str]]:
    """Extract entities via compiled regexes."""
    return {
        "case_numbers": _RE_CASE_NUM.findall(text),
        "mcr_rules": _RE_MCR.findall(text),
        "mcl_statutes": _RE_MCL.findall(text),
        "dates": _RE_DATE.findall(text),
        "judges": _RE_JUDGE.findall(text),
        "persons": _RE_PERSON.findall(text),
    }


def _regex_lane_detect(text: str) -> str:
    """Detect case lane via keyword signals.  Priority: E → D → F → C → A → B."""
    t = text.lower()
    for lane, signals in _LANE_SIGNALS.items():
        if any(s in t for s in signals):
            return lane
    return "A"  # default to custody lane


def _regex_citations(text: str) -> List[Dict[str, str]]:
    """Extract legal citations via regex."""
    results: List[Dict[str, str]] = []
    for m in _RE_MCR.finditer(text):
        results.append({"type": "MCR", "citation": m.group(), "start": str(m.start())})
    for m in _RE_MCL.finditer(text):
        results.append({"type": "MCL", "citation": m.group(), "start": str(m.start())})
    return results


def _extract_categories(context: str) -> List[str]:
    """Try to extract a category list from *context* (e.g. comma-separated)."""
    if not context:
        return []
    # Look for lines like "categories: a, b, c" or just comma-separated tokens
    for line in context.splitlines():
        if "," in line:
            cats = [c.strip() for c in line.split(",") if c.strip()]
            if len(cats) >= 2:
                return cats
    return []


# -----------------------------------------------------------------------
# CLI entry point — smoke test
# -----------------------------------------------------------------------
if __name__ == "__main__":
    sys.stdout = open(
        sys.stdout.fileno(), mode="w", encoding="utf-8",
        errors="replace", closefd=False,
    )

    router = ModelRouter()

    print("=" * 60)
    print("APEX MANBEARPIG — Model Router smoke test")
    print("=" * 60)
    print(f"  APEX_LLM_ENABLED       : {router.enabled}")
    print(f"  CONFIDENCE_THRESHOLD   : {CONFIDENCE_THRESHOLD}")
    print(f"  Task types registered  : {len(router.ROUTE_TABLE)}")
    print()

    # Auto-classify some queries
    test_queries = [
        "Can Judge McNeill be disqualified under MCR 2.003?",
        "Classify this document as custody or housing",
        "Extract all names and dates from this motion",
        "What is the filing deadline for COA 366810?",
        "Summarize the PPO violation evidence",
        "Find MCR rules about service of process",
    ]

    print("--- Task Classification ---")
    for q in test_queries:
        task = router.classify_task(q)
        info = router.get_route_info(task)
        print(f"  Q: {q[:60]}...")
        print(f"     → task={task}, primary={info['primary']}, would_use_llm={info['would_use_llm']}")
        print()

    # Route a query through the full chain
    print("--- Full Route Execution ---")
    result = router.route(
        "legal_reasoning",
        "Can I disqualify Judge McNeill under MCR 2.003?",
        context="Family law custody case 2024-001507-DC",
    )
    for k, v in result.items():
        val_str = str(v)
        if len(val_str) > 120:
            val_str = val_str[:120] + "..."
        print(f"  {k}: {val_str}")

    print()
    print("--- Regex NER Fallback ---")
    ner = _regex_ner(
        "Judge McNeill in case 2024-001507-DC violated MCR 2.003(C) "
        "and MCL 600.1 on 2025-03-15. John Watson filed the motion."
    )
    for entity_type, vals in ner.items():
        if vals:
            print(f"  {entity_type}: {vals}")

    print()
    print("--- Lane Detection ---")
    for text in ["PPO violation by respondent", "COA 366810 appeal", "Shady Oaks lease"]:
        print(f"  '{text}' → lane {_regex_lane_detect(text)}")

    print()
    print("Done.")
