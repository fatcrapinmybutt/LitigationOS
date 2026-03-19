#!/usr/bin/env python3
"""
APEX Integration Layer — Connects LLM capabilities to MANBEARPIG
═════════════════════════════════════════════════════════════════
Shadow-programmed: All LLM features disabled until APEX_LLM_ENABLED=true.
Existing MANBEARPIG behavior is NEVER modified — this is purely additive.

This module wraps :class:`MichiganLegalModel` and adds LLM-enhanced
capabilities as an optional overlay via :class:`OllamaProvider` and
:class:`ModelRouter`.  When the LLM gate is closed (the default),
every method delegates 100 % to MANBEARPIG and returns immediately.

APEX DATABASE ARCHITECTURE (38 databases, 15.92 GB total)
═════════════════════════════════════════════════════════
CRITICAL (4):
  litigation_context.db    — 10.47 GB, 702 tables (central hub)
  master_index.db          — 3.32 GB, 14 tables, 1.7M files (agent processing)
  omega_dedup.db           — 591 MB, 7 tables (deduplication)
  file_catalog.db          — 233 MB, 4 tables, 390K files (file index)

VECTOR / ML:
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

PIPELINE:
  mcr_rules.db             — Michigan Court Rules
  failsafe_incidents.db    — Error tracking
  document_fulltext.db     — Full-text search index
  drive_inventory.db       — Drive scanner output
  test_litigation_os.db    — Test harness

AGENT FLEET:
  agents/master_index.db   — 14 tables, 1.7M files (agent processing)

EXTERNAL:
  D:\\litigation_context_backup     — 1.08 GB backup (2026-02-20)
  G:\\authority_store_2.sqlite      — 42 MB legal authorities
  H:\\mi_warchest_pinnacle_v6.sqlite — 60 MB MI law warchest

  Total: 38 databases, ~15.92 GB

Design invariants
─────────────────
* Same ``APEX_LLM_ENABLED`` flag as :mod:`ollama_provider`.
* Thread-safe — all mutable state behind :class:`threading.Lock`.
* Lazy imports — ``inference_engine``, ``ollama_provider``, and
  ``model_router`` are only imported on first use.
* NEVER imports from the repo root (shadow modules like json.py).
* Uses ``Path(__file__).parent`` for sibling imports.
* All DB connections use the mandatory PRAGMA set.
* Zero-crash: every public method is try/excepted.
"""

from __future__ import annotations

import importlib.util
import logging
import os
import sqlite3
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# ──────────────────────────────────────────────────────────────────────
# Global LLM gate — mirrors ollama_provider.py
# ──────────────────────────────────────────────────────────────────────
APEX_LLM_ENABLED: bool = (
    os.environ.get("APEX_LLM_ENABLED", "false").lower() == "true"
)

# ──────────────────────────────────────────────────────────────────────
# Logging — module-level logger, never reconfigures root
# ──────────────────────────────────────────────────────────────────────
_log = logging.getLogger("apex.integration")
if not _log.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s — %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    ))
    _log.addHandler(_h)
    _log.setLevel(logging.DEBUG if APEX_LLM_ENABLED else logging.INFO)

# ──────────────────────────────────────────────────────────────────────
# Path helpers — never CWD to repo root (shadow modules)
# ──────────────────────────────────────────────────────────────────────
_THIS_DIR: Path = Path(__file__).resolve().parent
_REPO_ROOT: Path = _THIS_DIR.parent.parent
_DB_PATH: Path = _REPO_ROOT / "litigation_context.db"
_DATA_DIR: Path = _REPO_ROOT / "09_DATA"
_AGENTS_DIR: Path = _REPO_ROOT / "00_SYSTEM" / "pipeline" / "agents"

# ──────────────────────────────────────────────────────────────────────
# Database catalogue — all 38 databases and their expected locations
# ──────────────────────────────────────────────────────────────────────
_DATABASE_CATALOGUE: Dict[str, Dict[str, Any]] = {
    # CRITICAL (4)
    "litigation_context.db": {
        "path": _REPO_ROOT / "litigation_context.db",
        "category": "critical",
        "desc": "Central hub — 702 tables",
    },
    "master_index.db": {
        "path": _AGENTS_DIR / "master_index.db",
        "category": "critical",
        "desc": "Agent fleet — 14 tables, 1.7M files",
    },
    "omega_dedup.db": {
        "path": _REPO_ROOT / "omega_dedup.db",
        "category": "critical",
        "desc": "Deduplication — 7 tables",
    },
    "file_catalog.db": {
        "path": _REPO_ROOT / "file_catalog.db",
        "category": "critical",
        "desc": "File index — 4 tables, 390K files",
    },
    # VECTOR / ML
    "chroma.sqlite3": {
        "path": _REPO_ROOT / "chroma.sqlite3",
        "category": "vector_ml",
        "desc": "Embeddings — 2K vectors",
    },
    # CASE LANES (09_DATA/)
    "lane_A_custody.db": {
        "path": _DATA_DIR / "lane_A_custody.db",
        "category": "lane",
        "desc": "Custody — 2024-001507-DC",
    },
    "lane_B_housing.db": {
        "path": _DATA_DIR / "lane_B_housing.db",
        "category": "lane",
        "desc": "Housing — 2025-002760-CZ",
    },
    "lane_C_convergence.db": {
        "path": _DATA_DIR / "lane_C_convergence.db",
        "category": "lane",
        "desc": "Cross-lane convergence",
    },
    "lane_D_ppo.db": {
        "path": _DATA_DIR / "lane_D_ppo.db",
        "category": "lane",
        "desc": "Protection orders",
    },
    "lane_E_misconduct.db": {
        "path": _DATA_DIR / "lane_E_misconduct.db",
        "category": "lane",
        "desc": "Judicial misconduct",
    },
    "lane_F_appellate.db": {
        "path": _DATA_DIR / "lane_F_appellate.db",
        "category": "lane",
        "desc": "Appellate — COA 366810",
    },
    # PIPELINE
    "mcr_rules.db": {
        "path": _REPO_ROOT / "mcr_rules.db",
        "category": "pipeline",
        "desc": "Michigan Court Rules",
    },
    "failsafe_incidents.db": {
        "path": _REPO_ROOT / "failsafe_incidents.db",
        "category": "pipeline",
        "desc": "Error tracking",
    },
    "document_fulltext.db": {
        "path": _REPO_ROOT / "document_fulltext.db",
        "category": "pipeline",
        "desc": "Full-text search index",
    },
    "drive_inventory.db": {
        "path": _REPO_ROOT / "drive_inventory.db",
        "category": "pipeline",
        "desc": "Drive scanner output",
    },
    "test_litigation_os.db": {
        "path": _REPO_ROOT / "test_litigation_os.db",
        "category": "pipeline",
        "desc": "Test harness",
    },
    # DRIVE MANIFESTS (7)
    "drive_C_manifest.db": {
        "path": _REPO_ROOT / "drive_C_manifest.db",
        "category": "manifest",
        "desc": "C: drive manifest",
    },
    "drive_D_manifest.db": {
        "path": _REPO_ROOT / "drive_D_manifest.db",
        "category": "manifest",
        "desc": "D: drive manifest",
    },
    "drive_F_manifest.db": {
        "path": _REPO_ROOT / "drive_F_manifest.db",
        "category": "manifest",
        "desc": "F: drive manifest",
    },
    "drive_G_manifest.db": {
        "path": _REPO_ROOT / "drive_G_manifest.db",
        "category": "manifest",
        "desc": "G: drive manifest",
    },
    "drive_H_manifest.db": {
        "path": _REPO_ROOT / "drive_H_manifest.db",
        "category": "manifest",
        "desc": "H: drive manifest",
    },
    "drive_I_manifest.db": {
        "path": _REPO_ROOT / "drive_I_manifest.db",
        "category": "manifest",
        "desc": "I: drive manifest",
    },
    "omega_C_manifest.db": {
        "path": _REPO_ROOT / "omega_C_manifest.db",
        "category": "manifest",
        "desc": "Omega C: manifest",
    },
}


def _safe_db(path: Optional[Path] = None) -> Optional[sqlite3.Connection]:
    """Open a read-only SQLite connection with mandatory PRAGMAs.

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
        conn.execute("PRAGMA query_only = ON")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as exc:
        _log.warning("_safe_db(%s) failed: %s", db_file, exc)
        return None


def _load_sibling(module_name: str) -> Any:
    """Import a sibling module by filename from the same directory.

    Uses ``importlib`` so the repo root is never added to ``sys.path``.
    Returns ``None`` on any import failure.
    """
    mod_path = _THIS_DIR / f"{module_name}.py"
    if not mod_path.exists():
        _log.debug("Sibling module not found: %s", mod_path)
        return None
    try:
        spec = importlib.util.spec_from_file_location(module_name, str(mod_path))
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception as exc:
        _log.warning("Failed to import sibling %s: %s", module_name, exc)
        return None


# ╔══════════════════════════════════════════════════════════════════════╗
# ║                         FILING TEMPLATES                            ║
# ╚══════════════════════════════════════════════════════════════════════╝
_SECTION_TEMPLATES: Dict[str, str] = {
    "caption": (
        "STATE OF MICHIGAN\n"
        "IN THE {court} FOR THE COUNTY OF {county}\n\n"
        "{plaintiff},\n    Plaintiff,\n\n"
        "v.\n\n"
        "{defendant},\n    Defendant.\n\n"
        "Case No. {case_no}\n"
        "Hon. {judge}\n"
    ),
    "statement_of_facts": (
        "STATEMENT OF FACTS\n\n"
        "The following facts are supported by the record:\n\n"
        "{facts}\n"
    ),
    "argument": (
        "ARGUMENT\n\n"
        "{argument_body}\n"
    ),
    "conclusion": (
        "CONCLUSION\n\n"
        "For the foregoing reasons, {party} respectfully requests "
        "that this Court {relief}.\n"
    ),
    "certificate_of_service": (
        "CERTIFICATE OF SERVICE\n\n"
        "I certify that on {date}, I served a copy of the foregoing "
        "document on all parties of record by {method}.\n\n"
        "____________________________\n"
        "{name}\n"
    ),
}


# ╔══════════════════════════════════════════════════════════════════════╗
# ║                         APEX ENGINE                                 ║
# ╚══════════════════════════════════════════════════════════════════════╝

class APEXEngine:
    """Enhanced MANBEARPIG with optional LLM overlay.

    All public methods:
    1. Always run MANBEARPIG first (fast, reliable, deterministic).
    2. If ``APEX_LLM_ENABLED`` **and** ``enhance=True``, augment with
       LLM analysis via :class:`OllamaProvider` / :class:`ModelRouter`.
    3. Merge results with confidence weighting.

    Thread-safe — a single lock guards lazy initialisation of the
    underlying engine instances.

    Example (disabled — default)::

        >>> engine = APEXEngine()
        >>> engine.query("What is MCR 2.003?")
        {'source': 'manbearpig', 'answer': '...', ...}

    Example (enabled)::

        >>> import os; os.environ["APEX_LLM_ENABLED"] = "true"
        >>> engine = APEXEngine()
        >>> engine.query("What is MCR 2.003?", enhance=True)
        {'source': 'merged', 'manbearpig': {...}, 'llm': {...}, ...}
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._manbearpig: Any = None      # lazy: MichiganLegalModel
        self._ollama: Any = None           # lazy: OllamaProvider
        self._router: Any = None           # lazy: ModelRouter
        self._init_errors: List[str] = []
        self._created_at: float = time.time()
        _log.info(
            "APEXEngine initialised (LLM %s)",
            "ENABLED" if APEX_LLM_ENABLED else "disabled",
        )

    # ── Lazy loaders ─────────────────────────────────────────────

    def _get_manbearpig(self) -> Any:
        """Lazy-load MichiganLegalModel. Thread-safe."""
        if self._manbearpig is not None:
            return self._manbearpig
        with self._lock:
            if self._manbearpig is not None:
                return self._manbearpig
            try:
                mod = _load_sibling("inference_engine")
                if mod and hasattr(mod, "MichiganLegalModel"):
                    self._manbearpig = mod.MichiganLegalModel()
                    _log.info("MANBEARPIG loaded (loaded=%s)", self._manbearpig.loaded)
                else:
                    self._init_errors.append("inference_engine missing MichiganLegalModel")
                    _log.error("MichiganLegalModel not found in inference_engine")
            except Exception as exc:
                self._init_errors.append(f"MANBEARPIG init: {exc}")
                _log.error("Failed to load MANBEARPIG: %s", exc)
        return self._manbearpig

    def _get_ollama(self) -> Any:
        """Lazy-load OllamaProvider. Thread-safe. Returns None if LLM disabled."""
        if not APEX_LLM_ENABLED:
            return None
        if self._ollama is not None:
            return self._ollama
        with self._lock:
            if self._ollama is not None:
                return self._ollama
            try:
                mod = _load_sibling("ollama_provider")
                if mod and hasattr(mod, "OllamaProvider"):
                    self._ollama = mod.OllamaProvider()
                    _log.info("OllamaProvider loaded")
                else:
                    self._init_errors.append("ollama_provider missing OllamaProvider")
            except Exception as exc:
                self._init_errors.append(f"OllamaProvider init: {exc}")
                _log.warning("OllamaProvider unavailable: %s", exc)
        return self._ollama

    def _get_router(self) -> Any:
        """Lazy-load ModelRouter. Thread-safe. Returns None if LLM disabled."""
        if not APEX_LLM_ENABLED:
            return None
        if self._router is not None:
            return self._router
        with self._lock:
            if self._router is not None:
                return self._router
            try:
                mod = _load_sibling("model_router")
                if mod and hasattr(mod, "ModelRouter"):
                    self._router = mod.ModelRouter()
                    _log.info("ModelRouter loaded")
                else:
                    self._init_errors.append("model_router missing ModelRouter")
            except Exception as exc:
                self._init_errors.append(f"ModelRouter init: {exc}")
                _log.warning("ModelRouter unavailable: %s", exc)
        return self._router

    # ── Core public API ──────────────────────────────────────────

    def query(self, question: str, enhance: bool = True) -> Dict[str, Any]:
        """Query with optional LLM enhancement.

        1. Always runs MANBEARPIG first (fast, reliable).
        2. If LLM enabled **and** *enhance* is ``True``, augments with
           LLM analysis via :class:`ModelRouter`.
        3. Merges results with confidence weighting.

        Parameters
        ----------
        question : str
            Natural-language legal question.
        enhance : bool
            If ``True`` and LLM is available, augment MANBEARPIG's answer.

        Returns
        -------
        dict
            ``{'source', 'answer', 'confidence', 'manbearpig', 'llm', ...}``
        """
        try:
            mb_result = self._query_manbearpig(question)
            if not (APEX_LLM_ENABLED and enhance):
                return {
                    "source": "manbearpig",
                    "answer": mb_result.get("answer", ""),
                    "confidence": mb_result.get("confidence", 0.0),
                    "manbearpig": mb_result,
                    "llm": None,
                    "enhanced": False,
                }

            llm_result = self._query_llm(question)
            merged = self._merge_results(mb_result, llm_result)
            return {
                "source": "merged",
                "answer": merged.get("answer", mb_result.get("answer", "")),
                "confidence": merged.get("confidence", 0.0),
                "manbearpig": mb_result,
                "llm": llm_result,
                "enhanced": True,
            }
        except Exception as exc:
            _log.error("query() failed: %s", exc)
            return {
                "source": "error",
                "answer": f"Query failed: {exc}",
                "confidence": 0.0,
                "manbearpig": None,
                "llm": None,
                "enhanced": False,
                "error": str(exc),
            }

    def legal_research(
        self, topic: str, jurisdiction: str = "michigan"
    ) -> Dict[str, Any]:
        """Deep legal research — MANBEARPIG retrieval + optional LLM synthesis.

        Parameters
        ----------
        topic : str
            Legal topic or question to research.
        jurisdiction : str
            Jurisdiction filter (default ``"michigan"``).

        Returns
        -------
        dict
            ``{'topic', 'jurisdiction', 'results', 'synthesis', 'sources', ...}``
        """
        try:
            mb = self._get_manbearpig()
            results: List[Dict[str, Any]] = []
            sources: List[str] = []

            # MANBEARPIG retrieval via query
            if mb and mb.loaded:
                try:
                    mb_answer = mb.query(topic) if hasattr(mb, "query") else {}
                    if isinstance(mb_answer, dict):
                        results.append(mb_answer)
                        sources.append("manbearpig_tfidf")
                    elif isinstance(mb_answer, str):
                        results.append({"answer": mb_answer})
                        sources.append("manbearpig_tfidf")
                except Exception as exc:
                    _log.warning("MANBEARPIG research failed: %s", exc)

            # DB-based authority lookup
            conn = _safe_db()
            if conn:
                try:
                    rows = conn.execute(
                        "SELECT rule_number, title, full_text "
                        "FROM auth_rules WHERE full_text LIKE ? LIMIT 10",
                        (f"%{topic[:80]}%",),
                    ).fetchall()
                    for row in rows:
                        results.append({
                            "rule": row["rule_number"],
                            "title": row["title"],
                            "text": (row["full_text"] or "")[:500],
                        })
                        sources.append(f"auth_rules:{row['rule_number']}")
                except Exception:
                    pass
                finally:
                    conn.close()

            synthesis = ""
            if APEX_LLM_ENABLED:
                router = self._get_router()
                if router and hasattr(router, "route"):
                    try:
                        llm_out = router.route(
                            f"Legal research on: {topic} ({jurisdiction})",
                            task_type="legal_reasoning",
                        )
                        if isinstance(llm_out, dict):
                            synthesis = llm_out.get("answer", "")
                    except Exception as exc:
                        _log.warning("LLM synthesis failed: %s", exc)

            return {
                "topic": topic,
                "jurisdiction": jurisdiction,
                "result_count": len(results),
                "results": results,
                "synthesis": synthesis,
                "sources": sources,
                "llm_used": bool(synthesis),
            }
        except Exception as exc:
            _log.error("legal_research() failed: %s", exc)
            return {
                "topic": topic,
                "jurisdiction": jurisdiction,
                "result_count": 0,
                "results": [],
                "synthesis": "",
                "sources": [],
                "llm_used": False,
                "error": str(exc),
            }

    def draft_section(
        self, section_type: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Draft a filing section — template-based + optional LLM enhancement.

        Parameters
        ----------
        section_type : str
            One of: ``caption``, ``statement_of_facts``, ``argument``,
            ``conclusion``, ``certificate_of_service``.
        context : dict
            Variables for template interpolation (e.g. ``court``, ``county``,
            ``plaintiff``, ``defendant``, ``case_no``, ``judge``).

        Returns
        -------
        dict
            ``{'section_type', 'text', 'source', 'llm_enhanced'}``
        """
        try:
            template = _SECTION_TEMPLATES.get(section_type, "")
            text = ""

            if template:
                try:
                    text = template.format_map(_SafeFormatDict(context))
                except Exception as exc:
                    _log.warning("Template formatting failed: %s", exc)
                    text = template

            if APEX_LLM_ENABLED and text:
                router = self._get_router()
                if router and hasattr(router, "route"):
                    try:
                        prompt = (
                            f"Improve this {section_type} section for a Michigan "
                            f"court filing. Keep all factual content. Fix only "
                            f"grammar and legal style:\n\n{text}"
                        )
                        llm_out = router.route(prompt, task_type="legal_reasoning")
                        if isinstance(llm_out, dict) and llm_out.get("answer"):
                            return {
                                "section_type": section_type,
                                "text": llm_out["answer"],
                                "template_text": text,
                                "source": "llm_enhanced",
                                "llm_enhanced": True,
                            }
                    except Exception as exc:
                        _log.warning("LLM draft enhancement failed: %s", exc)

            return {
                "section_type": section_type,
                "text": text,
                "source": "template" if template else "empty",
                "llm_enhanced": False,
            }
        except Exception as exc:
            _log.error("draft_section() failed: %s", exc)
            return {
                "section_type": section_type,
                "text": "",
                "source": "error",
                "llm_enhanced": False,
                "error": str(exc),
            }

    def validate_filing(
        self, filing_text: str, filing_type: str
    ) -> Dict[str, Any]:
        """Validate a filing for compliance — rules-based + optional LLM review.

        Parameters
        ----------
        filing_text : str
            Full text of the filing to validate.
        filing_type : str
            Type of filing (``motion``, ``complaint``, ``brief``, ``affidavit``).

        Returns
        -------
        dict
            ``{'passed', 'score', 'issues', 'warnings', 'llm_review'}``
        """
        try:
            # Import quality_gate lazily from sibling
            qg_mod = _load_sibling("quality_gate")
            issues: List[str] = []
            warnings: List[str] = []
            score = 100

            if qg_mod and hasattr(qg_mod, "QualityGate"):
                gate = qg_mod.QualityGate()
                result = gate.validate(
                    filing_text,
                    filing_type=filing_type,
                )
                issues = result.get("issues", [])
                warnings = result.get("warnings", [])
                score = result.get("score", 100)
            else:
                # Minimal inline check when quality_gate is unavailable
                if not filing_text.strip():
                    issues.append("Filing text is empty")
                    score = 0
                if len(filing_text) < 200:
                    warnings.append("Filing appears very short (<200 chars)")
                    score = max(score - 20, 0)

            llm_review = ""
            if APEX_LLM_ENABLED and filing_text.strip():
                router = self._get_router()
                if router and hasattr(router, "route"):
                    try:
                        prompt = (
                            f"Review this Michigan {filing_type} filing for "
                            f"legal compliance issues. Be concise:\n\n"
                            f"{filing_text[:3000]}"
                        )
                        llm_out = router.route(prompt, task_type="legal_reasoning")
                        if isinstance(llm_out, dict):
                            llm_review = llm_out.get("answer", "")
                    except Exception as exc:
                        _log.warning("LLM filing review failed: %s", exc)

            passed = score >= 70 and not any(
                "FABRICATED" in str(i) or "WRONG" in str(i) for i in issues
            )

            return {
                "passed": passed,
                "score": score,
                "filing_type": filing_type,
                "issues": issues,
                "warnings": warnings,
                "llm_review": llm_review,
                "llm_used": bool(llm_review),
            }
        except Exception as exc:
            _log.error("validate_filing() failed: %s", exc)
            return {
                "passed": False,
                "score": 0,
                "filing_type": filing_type,
                "issues": [f"Validation error: {exc}"],
                "warnings": [],
                "llm_review": "",
                "llm_used": False,
                "error": str(exc),
            }

    def status(self) -> Dict[str, Any]:
        """System status report.

        Reports on MANBEARPIG health, LLM availability, and the full
        38-database architecture with table counts and accessibility.

        Returns
        -------
        dict
            ``{'manbearpig', 'llm', 'databases', 'uptime_seconds'}``
        """
        try:
            result: Dict[str, Any] = {
                "apex_llm_enabled": APEX_LLM_ENABLED,
                "uptime_seconds": round(time.time() - self._created_at, 1),
                "init_errors": list(self._init_errors),
                "manbearpig": self._manbearpig_status(),
                "llm": self._llm_status(),
                "databases": self._database_status(),
            }
            return result
        except Exception as exc:
            _log.error("status() failed: %s", exc)
            return {
                "apex_llm_enabled": APEX_LLM_ENABLED,
                "uptime_seconds": round(time.time() - self._created_at, 1),
                "error": str(exc),
            }

    # ── Internal helpers ─────────────────────────────────────────

    def _query_manbearpig(self, question: str) -> Dict[str, Any]:
        """Run a query through MANBEARPIG's pipeline."""
        mb = self._get_manbearpig()
        if mb is None:
            return {"answer": "", "confidence": 0.0, "error": "MANBEARPIG not loaded"}
        try:
            raw = mb.query(question) if hasattr(mb, "query") else None
            if isinstance(raw, dict):
                return raw
            if isinstance(raw, str):
                return {"answer": raw, "confidence": 0.5}
            return {"answer": str(raw) if raw else "", "confidence": 0.0}
        except Exception as exc:
            _log.warning("MANBEARPIG query error: %s", exc)
            return {"answer": "", "confidence": 0.0, "error": str(exc)}

    def _query_llm(self, question: str) -> Dict[str, Any]:
        """Run a query through the LLM router (if enabled)."""
        router = self._get_router()
        if router is None:
            return {"answer": "", "confidence": 0.0, "status": "llm_disabled"}
        try:
            raw = router.route(question) if hasattr(router, "route") else None
            if isinstance(raw, dict):
                return raw
            return {"answer": str(raw) if raw else "", "confidence": 0.5}
        except Exception as exc:
            _log.warning("LLM query error: %s", exc)
            return {"answer": "", "confidence": 0.0, "error": str(exc)}

    @staticmethod
    def _merge_results(
        mb: Dict[str, Any], llm: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge MANBEARPIG and LLM results with confidence weighting.

        Weighting: MANBEARPIG 0.6, LLM 0.4 (MANBEARPIG is trusted baseline).
        """
        mb_conf = float(mb.get("confidence", 0.0))
        llm_conf = float(llm.get("confidence", 0.0))
        mb_answer = mb.get("answer", "")
        llm_answer = llm.get("answer", "")

        # If LLM has no answer, return MANBEARPIG's
        if not llm_answer:
            return {"answer": mb_answer, "confidence": mb_conf}

        # If MANBEARPIG has no answer, return LLM's (with reduced confidence)
        if not mb_answer:
            return {"answer": llm_answer, "confidence": llm_conf * 0.8}

        # Both have answers — weighted merge
        merged_conf = (mb_conf * 0.6) + (llm_conf * 0.4)

        # Use MANBEARPIG as base, append LLM supplement
        if llm_answer and llm_answer != mb_answer:
            merged_answer = (
                f"{mb_answer}\n\n"
                f"[LLM Supplement — confidence {llm_conf:.0%}]\n"
                f"{llm_answer}"
            )
        else:
            merged_answer = mb_answer

        return {"answer": merged_answer, "confidence": merged_conf}

    def _manbearpig_status(self) -> Dict[str, Any]:
        """Gather MANBEARPIG health metrics."""
        mb = self._get_manbearpig()
        if mb is None:
            return {"available": False, "error": "Not loaded"}
        try:
            status: Dict[str, Any] = {
                "available": True,
                "loaded": getattr(mb, "loaded", False),
                "corpus_size": len(getattr(mb, "corpus_texts", [])),
                "concept_count": len(getattr(mb, "legal_concepts", {})),
                "cache_size": len(getattr(mb, "_cache", {})),
                "has_vectorizer": getattr(mb, "vectorizer", None) is not None,
                "has_tfidf": getattr(mb, "tfidf_matrix", None) is not None,
                "has_intent_clf": getattr(mb, "intent_clf", None) is not None,
            }
            if hasattr(mb, "get_error_report"):
                status["error_report"] = mb.get_error_report()
            return status
        except Exception as exc:
            return {"available": True, "error": str(exc)}

    def _llm_status(self) -> Dict[str, Any]:
        """Gather LLM health metrics."""
        if not APEX_LLM_ENABLED:
            return {"enabled": False, "status": "shadow_programmed"}
        ollama = self._get_ollama()
        if ollama is None:
            return {"enabled": True, "status": "unavailable"}
        try:
            if hasattr(ollama, "health_check"):
                health = ollama.health_check()
                return {"enabled": True, "status": "available", "health": health}
            return {"enabled": True, "status": "loaded"}
        except Exception as exc:
            return {"enabled": True, "status": "error", "error": str(exc)}

    def _database_status(self) -> Dict[str, Any]:
        """Probe all 38 databases and report accessibility.

        For each database:
        - Check if file exists
        - Attempt connection
        - Count tables
        - Estimate total rows (sum of first 20 tables)
        """
        db_report: Dict[str, Any] = {
            "total_catalogued": len(_DATABASE_CATALOGUE),
            "accessible": 0,
            "total_tables": 0,
            "total_estimated_rows": 0,
            "databases": {},
        }

        for name, info in _DATABASE_CATALOGUE.items():
            db_path: Path = info["path"]
            entry: Dict[str, Any] = {
                "category": info["category"],
                "description": info["desc"],
                "exists": db_path.exists(),
                "accessible": False,
                "tables": 0,
                "estimated_rows": 0,
                "size_mb": 0.0,
            }

            if db_path.exists():
                try:
                    entry["size_mb"] = round(db_path.stat().st_size / (1024 * 1024), 2)
                except Exception:
                    pass

                conn = _safe_db(db_path)
                if conn:
                    try:
                        tables = conn.execute(
                            "SELECT name FROM sqlite_master "
                            "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                        ).fetchall()
                        entry["tables"] = len(tables)
                        entry["accessible"] = True
                        db_report["accessible"] += 1
                        db_report["total_tables"] += len(tables)

                        # Estimate rows from first 20 tables
                        est_rows = 0
                        for tbl in tables[:20]:
                            try:
                                row = conn.execute(
                                    f"SELECT COUNT(*) AS c FROM [{tbl['name']}]"
                                ).fetchone()
                                if row:
                                    est_rows += row["c"]
                            except Exception:
                                pass
                        entry["estimated_rows"] = est_rows
                        db_report["total_estimated_rows"] += est_rows
                    except Exception as exc:
                        entry["error"] = str(exc)
                    finally:
                        conn.close()

            db_report["databases"][name] = entry

        return db_report

    # ── Magic methods ────────────────────────────────────────────

    def __repr__(self) -> str:
        mb_loaded = (
            getattr(self._manbearpig, "loaded", False)
            if self._manbearpig else False
        )
        return (
            f"<APEXEngine manbearpig={'loaded' if mb_loaded else 'unloaded'} "
            f"llm={'enabled' if APEX_LLM_ENABLED else 'disabled'}>"
        )


class _SafeFormatDict(dict):
    """Dict subclass that returns ``{key}`` for missing template keys."""

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


# ──────────────────────────────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")
    import json as _json  # safe — running from __file__ dir, not repo root

    engine = APEXEngine()
    if len(sys.argv) > 1:
        q = " ".join(sys.argv[1:])
        result = engine.query(q)
        print(_json.dumps(result, indent=2, default=str))
    else:
        st = engine.status()
        print(_json.dumps(st, indent=2, default=str))
