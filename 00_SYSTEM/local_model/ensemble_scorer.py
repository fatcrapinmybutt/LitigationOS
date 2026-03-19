"""
APEX Ensemble Scorer — Weighted voting across multiple models.

Aggregates predictions from Naive Bayes + Qwen + legal-BERT + keyword patterns.
Shadow-programmed: only invokes LLM models when APEX_LLM_ENABLED=true.
When disabled: uses TF-IDF/NB + keyword patterns only (still effective).

Voting strategy: majority vote with confidence weighting.
If MANBEARPIG + keyword agree, skip LLM to save compute.
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("apex.ensemble_scorer")

APEX_LLM_ENABLED: bool = os.environ.get("APEX_LLM_ENABLED", "false").lower() == "true"

_MODULE_DIR = Path(__file__).parent
_DB_DIR = _MODULE_DIR / "model_data"

# ---------------------------------------------------------------------------
# Safe imports for optional backends
# ---------------------------------------------------------------------------

_manbearpig = None
_keyword_classifier = None

try:
    from . import inference_engine as _ie_mod
    _manbearpig = _ie_mod
except Exception:
    try:
        import importlib
        _manbearpig = importlib.import_module("inference_engine")
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PRAGMA_INIT = (
    "PRAGMA busy_timeout=60000",
    "PRAGMA journal_mode=WAL",
    "PRAGMA cache_size=-32000",
    "PRAGMA synchronous=NORMAL",
    "PRAGMA temp_store=MEMORY",
)


def _open_db(path: str | Path) -> sqlite3.Connection:
    """Open a SQLite connection with mandatory PRAGMAs."""
    conn = sqlite3.connect(str(path), check_same_thread=False)
    for p in _PRAGMA_INIT:
        conn.execute(p)
    return conn


def _ensure_weight_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ensemble_weights (
            task       TEXT NOT NULL,
            model_name TEXT NOT NULL,
            weight     REAL NOT NULL DEFAULT 1.0,
            wins       INTEGER NOT NULL DEFAULT 0,
            losses     INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (task, model_name)
        )
    """)
    conn.commit()


# ---------------------------------------------------------------------------
# Keyword classifier (always available, zero dependencies)
# ---------------------------------------------------------------------------

_KEYWORD_PATTERNS: Dict[str, List[str]] = {
    "custody": ["custody", "parenting time", "best interest", "child", "minor"],
    "housing": ["housing", "habitability", "landlord", "tenant", "lease", "mold"],
    "ppo": ["protection order", "ppo", "stalking", "harassment", "domestic violence"],
    "misconduct": ["judicial misconduct", "bias", "disqualification", "recusal", "jtc"],
    "appellate": ["appeal", "appellate", "coa", "msc", "leave to appeal"],
    "federal": ["1983", "civil rights", "federal", "constitutional", "due process"],
    "motion": ["motion", "brief", "memorandum", "reply", "response"],
    "evidence": ["exhibit", "evidence", "testimony", "deposition", "affidavit"],
}


def _keyword_vote(text: str, task: str) -> Dict[str, Any]:
    """Simple keyword-based classification — always available."""
    text_lower = text.lower()
    scores: Dict[str, float] = {}
    for label, keywords in _KEYWORD_PATTERNS.items():
        hits = sum(1 for kw in keywords if kw in text_lower)
        if hits > 0:
            scores[label] = hits / len(keywords)
    if not scores:
        return {"model": "keyword", "label": "unknown", "confidence": 0.0}
    best = max(scores, key=scores.get)  # type: ignore[arg-type]
    return {"model": "keyword", "label": best, "confidence": round(scores[best], 4)}


def _manbearpig_vote(text: str, task: str) -> Optional[Dict[str, Any]]:
    """Get prediction from MANBEARPIG inference engine."""
    if _manbearpig is None:
        return None
    try:
        if hasattr(_manbearpig, "MichiganLegalModel"):
            model = _manbearpig.MichiganLegalModel()
            result = model.query(text) if hasattr(model, "query") else None
            if result and isinstance(result, dict):
                label = result.get("intent", result.get("label", result.get("category", "unknown")))
                conf = float(result.get("confidence", result.get("score", 0.5)))
                return {"model": "manbearpig", "label": str(label), "confidence": round(conf, 4)}
        return None
    except Exception as exc:
        logger.debug("MANBEARPIG vote failed: %s", exc)
        return None


def _llm_vote(text: str, task: str) -> Optional[Dict[str, Any]]:
    """Get prediction from LLM backend (only when APEX_LLM_ENABLED)."""
    if not APEX_LLM_ENABLED:
        return None
    try:
        from .model_router import ModelRouter  # type: ignore[import-untyped]
        router = ModelRouter()
        result = router.route(text, task_type=task)
        if result and isinstance(result, dict):
            label = result.get("label", result.get("intent", "unknown"))
            conf = float(result.get("confidence", 0.5))
            return {"model": "llm", "label": str(label), "confidence": round(conf, 4)}
        return None
    except Exception as exc:
        logger.debug("LLM vote failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------


class EnsembleScorer:
    """Multi-model ensemble scorer with weighted voting."""

    DEFAULT_MODELS = ["keyword", "manbearpig", "llm"]

    def __init__(self, db_path: Optional[str | Path] = None) -> None:
        self._lock = threading.Lock()
        self._db_path = Path(db_path) if db_path else _DB_DIR / "ensemble_weights.db"
        self._weights_cache: Dict[str, Dict[str, float]] = {}
        self._init_db()

    # ------------------------------------------------------------------
    # DB
    # ------------------------------------------------------------------

    def _init_db(self) -> None:
        try:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = _open_db(self._db_path)
            _ensure_weight_table(conn)
            conn.close()
        except Exception as exc:
            logger.warning("Ensemble DB init failed (will use defaults): %s", exc)

    def _load_weights(self, task: str) -> Dict[str, float]:
        if task in self._weights_cache:
            return self._weights_cache[task]
        defaults = {m: 1.0 for m in self.DEFAULT_MODELS}
        try:
            conn = _open_db(self._db_path)
            rows = conn.execute(
                "SELECT model_name, weight FROM ensemble_weights WHERE task = ?", (task,)
            ).fetchall()
            conn.close()
            if rows:
                loaded = {r[0]: r[1] for r in rows}
                defaults.update(loaded)
        except Exception as exc:
            logger.debug("Weight load failed: %s", exc)
        self._weights_cache[task] = defaults
        return defaults

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score(self, text: str, task: str = "classify") -> dict:
        """Ensemble prediction.

        Returns ``{label: str, confidence: float, votes: {...}, method: str}``.
        """
        try:
            votes = self._collect_votes(text, task)
            if not votes:
                return {"label": "unknown", "confidence": 0.0, "votes": {}, "method": "none"}
            return self._weighted_merge(votes, task)
        except Exception as exc:
            logger.error("Ensemble score failed: %s", exc)
            return {"label": "unknown", "confidence": 0.0, "votes": {}, "method": "error"}

    def _collect_votes(self, text: str, task: str) -> List[Dict[str, Any]]:
        """Collect predictions from all available models."""
        votes: List[Dict[str, Any]] = []
        try:
            kw = _keyword_vote(text, task)
            votes.append(kw)
        except Exception:
            pass

        try:
            mb = _manbearpig_vote(text, task)
            if mb is not None:
                votes.append(mb)
        except Exception:
            pass

        # Early-exit optimisation: if keyword + MANBEARPIG agree, skip LLM
        if len(votes) >= 2:
            labels = [v["label"] for v in votes]
            if len(set(labels)) == 1 and all(v["confidence"] >= 0.5 for v in votes):
                logger.debug("Keyword + MANBEARPIG agree on '%s'; skipping LLM", labels[0])
                return votes

        try:
            llm = _llm_vote(text, task)
            if llm is not None:
                votes.append(llm)
        except Exception:
            pass

        return votes

    def _weighted_merge(self, votes: List[Dict[str, Any]], task: str = "classify") -> dict:
        """Merge votes using learned weights (default: equal)."""
        weights = self._load_weights(task)
        weighted_scores: Dict[str, float] = {}
        vote_detail: Dict[str, dict] = {}

        for v in votes:
            model = v.get("model", "unknown")
            label = v.get("label", "unknown")
            conf = v.get("confidence", 0.0)
            w = weights.get(model, 1.0)
            weighted_scores[label] = weighted_scores.get(label, 0.0) + conf * w
            vote_detail[model] = {"label": label, "confidence": conf, "weight": w}

        if not weighted_scores:
            return {"label": "unknown", "confidence": 0.0, "votes": vote_detail, "method": "empty"}

        best_label = max(weighted_scores, key=weighted_scores.get)  # type: ignore[arg-type]
        total_weight = sum(weights.get(v.get("model", ""), 1.0) for v in votes)
        norm_conf = round(weighted_scores[best_label] / max(total_weight, 1e-9), 4)
        norm_conf = min(norm_conf, 1.0)

        method = "ensemble"
        if len(votes) == 1:
            method = f"single:{votes[0].get('model', 'unknown')}"

        return {
            "label": best_label,
            "confidence": norm_conf,
            "votes": vote_detail,
            "method": method,
        }

    def update_weights(self, task: str, results: List[Dict[str, Any]]) -> None:
        """Update model weights based on outcome feedback.

        ``results``: list of ``{model: str, correct: bool}`` dicts.
        """
        with self._lock:
            try:
                conn = _open_db(self._db_path)
                _ensure_weight_table(conn)
                for r in results:
                    model = r.get("model", "")
                    correct = r.get("correct", False)
                    if not model:
                        continue
                    conn.execute("""
                        INSERT INTO ensemble_weights (task, model_name, weight, wins, losses)
                        VALUES (?, ?, 1.0, 0, 0)
                        ON CONFLICT(task, model_name) DO NOTHING
                    """, (task, model))
                    if correct:
                        conn.execute("""
                            UPDATE ensemble_weights
                            SET wins = wins + 1,
                                weight = MIN(weight + 0.05, 3.0),
                                updated_at = datetime('now')
                            WHERE task = ? AND model_name = ?
                        """, (task, model))
                    else:
                        conn.execute("""
                            UPDATE ensemble_weights
                            SET losses = losses + 1,
                                weight = MAX(weight - 0.05, 0.1),
                                updated_at = datetime('now')
                            WHERE task = ? AND model_name = ?
                        """, (task, model))
                conn.commit()
                conn.close()
                self._weights_cache.pop(task, None)
                logger.info("Updated ensemble weights for task '%s' (%d results)", task, len(results))
            except Exception as exc:
                logger.error("Weight update failed: %s", exc)


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------

_default_scorer: Optional[EnsembleScorer] = None
_default_lock = threading.Lock()


def get_scorer() -> EnsembleScorer:
    """Return (and lazily create) the module-level default scorer."""
    global _default_scorer
    if _default_scorer is None:
        with _default_lock:
            if _default_scorer is None:
                _default_scorer = EnsembleScorer()
    return _default_scorer
