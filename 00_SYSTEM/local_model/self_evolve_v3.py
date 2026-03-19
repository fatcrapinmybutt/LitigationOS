"""
APEX Self-Evolve v3 — Wraps self_evolve_v2 + adds APEX capabilities.

When APEX_LLM_ENABLED=true: uses LLM for pattern analysis, strategy optimisation.
When false: delegates entirely to v2's existing TF-IDF/NB approach.

Does NOT modify self_evolve_v2.py. Imports and wraps it.
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("apex.self_evolve_v3")

APEX_LLM_ENABLED: bool = os.environ.get("APEX_LLM_ENABLED", "false").lower() == "true"

_MODULE_DIR = Path(__file__).parent
_DB_DIR = _MODULE_DIR / "model_data"

# ---------------------------------------------------------------------------
# Safe import of v2
# ---------------------------------------------------------------------------

_v2_module: Any = None

try:
    from . import self_evolve_v2 as _v2_module  # type: ignore[assignment]
except Exception:
    try:
        import importlib
        _v2_module = importlib.import_module("self_evolve_v2")
    except Exception:
        logger.info("self_evolve_v2 not importable; v3 will operate standalone.")

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

_PRAGMA_INIT = (
    "PRAGMA busy_timeout=60000",
    "PRAGMA journal_mode=WAL",
    "PRAGMA cache_size=-32000",
    "PRAGMA synchronous=NORMAL",
    "PRAGMA temp_store=MEMORY",
)


def _open_db(path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path), check_same_thread=False)
    for p in _PRAGMA_INIT:
        conn.execute(p)
    return conn


def _ensure_tables(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS evolve_v3_cycles (
            cycle_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at  TEXT NOT NULL,
            finished_at TEXT,
            phase       TEXT,
            v2_result   TEXT,
            apex_result TEXT,
            delta       TEXT,
            status      TEXT DEFAULT 'running'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS evolve_v3_training (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            cycle_id    INTEGER,
            input_text  TEXT,
            expected    TEXT,
            predicted   TEXT,
            correct     INTEGER,
            source      TEXT,
            created_at  TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()


# ---------------------------------------------------------------------------
# LLM-enhanced helpers (only active when APEX_LLM_ENABLED)
# ---------------------------------------------------------------------------


def _llm_analyze_patterns(corrections: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Use LLM to analyze error patterns in recent corrections."""
    if not APEX_LLM_ENABLED or not corrections:
        return {"patterns": [], "suggestions": [], "method": "disabled"}
    try:
        from .model_router import ModelRouter  # type: ignore[import-untyped]
        router = ModelRouter()
        summary = json.dumps(corrections[:20], default=str, ensure_ascii=False)
        prompt = (
            "Analyze these prediction corrections and identify error patterns. "
            "Return JSON with 'patterns' (list of error categories) and "
            "'suggestions' (list of improvement strategies):\n" + summary
        )
        result = router.route(prompt, task_type="analysis")
        if isinstance(result, dict):
            return {
                "patterns": result.get("patterns", []),
                "suggestions": result.get("suggestions", []),
                "method": "llm",
            }
        return {"patterns": [], "suggestions": [], "method": "llm_parse_fail"}
    except Exception as exc:
        logger.debug("LLM pattern analysis failed: %s", exc)
        return {"patterns": [], "suggestions": [], "method": "error"}


def _llm_generate_training(corrections: List[Dict[str, Any]], count: int = 10) -> List[Dict[str, Any]]:
    """Use LLM to generate synthetic training examples from corrections."""
    if not APEX_LLM_ENABLED or not corrections:
        return []
    try:
        from .model_router import ModelRouter  # type: ignore[import-untyped]
        router = ModelRouter()
        sample = json.dumps(corrections[:5], default=str, ensure_ascii=False)
        prompt = (
            f"Based on these correction examples, generate {count} new diverse training "
            "examples that would help a classifier avoid these errors. "
            "Return a JSON list of {input, output, type} objects:\n" + sample
        )
        result = router.route(prompt, task_type="generation")
        if isinstance(result, list):
            return result[:count]
        if isinstance(result, dict) and "examples" in result:
            return result["examples"][:count]
        return []
    except Exception as exc:
        logger.debug("LLM training generation failed: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Core class
# ---------------------------------------------------------------------------


class SelfEvolveV3:
    """APEX self-evolution engine wrapping v2 + LLM enhancements."""

    def __init__(self, db_path: Optional[str | Path] = None) -> None:
        self._lock = threading.Lock()
        self._db_path = Path(db_path) if db_path else _DB_DIR / "evolve_v3.db"
        self._v2: Any = None
        self._init_db()
        self._init_v2()

    def _init_db(self) -> None:
        try:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = _open_db(self._db_path)
            _ensure_tables(conn)
            conn.close()
        except Exception as exc:
            logger.warning("Evolve v3 DB init failed: %s", exc)

    def _init_v2(self) -> None:
        """Load v2 engine safely."""
        if _v2_module is None:
            return
        try:
            for cls_name in ("SelfEvolver", "SelfEvolveV2", "Evolver"):
                if hasattr(_v2_module, cls_name):
                    self._v2 = getattr(_v2_module, cls_name)()
                    logger.info("Loaded v2 evolver: %s", cls_name)
                    return
            # If there's an evolve() function at module level
            if hasattr(_v2_module, "evolve"):
                self._v2 = _v2_module
                logger.info("Loaded v2 evolver as module-level functions.")
        except Exception as exc:
            logger.warning("v2 init failed: %s", exc)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evolve_cycle(self) -> dict:
        """Run one evolution cycle: analyse → train → evaluate → promote.

        Returns ``{status, v2_result, apex_result, delta, cycle_id}``.
        """
        cycle_id: Optional[int] = None
        started = datetime.now(timezone.utc).isoformat()
        try:
            conn = _open_db(self._db_path)
            cur = conn.execute(
                "INSERT INTO evolve_v3_cycles (started_at, phase) VALUES (?, 'starting')",
                (started,),
            )
            cycle_id = cur.lastrowid
            conn.commit()
            conn.close()
        except Exception:
            pass

        # Phase 1 — performance analysis
        perf = self._analyze_performance()
        self._update_phase(cycle_id, "analyzed")

        # Phase 2 — v2 evolution (always runs if available)
        v2_result = self._run_v2_cycle()
        self._update_phase(cycle_id, "v2_complete")

        # Phase 3 — APEX enhancements
        apex_result: Dict[str, Any] = {"method": "disabled"}
        if APEX_LLM_ENABLED:
            corrections = perf.get("corrections", [])
            apex_result = _llm_analyze_patterns(corrections)
            candidates = self._generate_training_candidates()
            apex_result["new_candidates"] = len(candidates)
            self._update_phase(cycle_id, "apex_complete")

        # Phase 4 — evaluate improvement
        delta = self._evaluate_improvement(
            before=perf.get("metrics", {}),
            after=v2_result.get("metrics", {}),
        )

        # Persist
        finished = datetime.now(timezone.utc).isoformat()
        try:
            conn = _open_db(self._db_path)
            conn.execute("""
                UPDATE evolve_v3_cycles
                SET finished_at = ?, phase = 'done', status = 'complete',
                    v2_result = ?, apex_result = ?, delta = ?
                WHERE cycle_id = ?
            """, (
                finished,
                json.dumps(v2_result, default=str),
                json.dumps(apex_result, default=str),
                json.dumps(delta, default=str),
                cycle_id,
            ))
            conn.commit()
            conn.close()
        except Exception:
            pass

        return {
            "status": "complete",
            "cycle_id": cycle_id,
            "v2_result": v2_result,
            "apex_result": apex_result,
            "delta": delta,
        }

    def _analyze_performance(self) -> dict:
        """Analyse recent predictions and corrections."""
        corrections: List[Dict[str, Any]] = []
        metrics: Dict[str, Any] = {}
        try:
            conn = _open_db(self._db_path)
            rows = conn.execute("""
                SELECT input_text, expected, predicted, correct, source
                FROM evolve_v3_training
                ORDER BY created_at DESC LIMIT 200
            """).fetchall()
            conn.close()
            total = len(rows)
            correct = sum(1 for r in rows if r[3])
            for r in rows:
                if not r[3]:
                    corrections.append({
                        "input": r[0], "expected": r[1],
                        "predicted": r[2], "source": r[4],
                    })
            metrics = {
                "total": total,
                "correct": correct,
                "accuracy": round(correct / max(total, 1), 4),
                "error_count": len(corrections),
            }
        except Exception as exc:
            logger.debug("Performance analysis DB read failed: %s", exc)
        return {"corrections": corrections, "metrics": metrics}

    def _generate_training_candidates(self) -> List[Dict[str, Any]]:
        """Generate new training examples from corrections + feedback."""
        perf = self._analyze_performance()
        corrections = perf.get("corrections", [])

        # Rule-based candidates (always available)
        candidates: List[Dict[str, Any]] = []
        for c in corrections[:20]:
            candidates.append({
                "input": c.get("input", ""),
                "output": c.get("expected", ""),
                "type": "correction",
                "source": "evolve_v3",
            })

        # LLM-generated candidates
        if APEX_LLM_ENABLED and corrections:
            llm_candidates = _llm_generate_training(corrections)
            candidates.extend(llm_candidates)

        logger.info("Generated %d training candidates", len(candidates))
        return candidates

    def _evaluate_improvement(self, before: dict, after: dict) -> dict:
        """Compare metrics before/after training. Returns delta."""
        delta: Dict[str, Any] = {"improved": False}
        try:
            before_acc = float(before.get("accuracy", 0.0))
            after_acc = float(after.get("accuracy", 0.0))
            delta["accuracy_before"] = before_acc
            delta["accuracy_after"] = after_acc
            delta["accuracy_delta"] = round(after_acc - before_acc, 4)
            delta["improved"] = after_acc > before_acc
        except Exception:
            pass
        return delta

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run_v2_cycle(self) -> dict:
        """Run v2's evolution cycle if available."""
        if self._v2 is None:
            return {"status": "v2_unavailable", "metrics": {}}
        try:
            if hasattr(self._v2, "evolve_cycle"):
                result = self._v2.evolve_cycle()
            elif hasattr(self._v2, "evolve"):
                result = self._v2.evolve()
            elif hasattr(self._v2, "run"):
                result = self._v2.run()
            else:
                return {"status": "v2_no_method", "metrics": {}}
            if isinstance(result, dict):
                return result
            return {"status": "v2_complete", "metrics": {}, "raw": str(result)[:500]}
        except Exception as exc:
            logger.warning("v2 cycle failed: %s", exc)
            return {"status": "v2_error", "error": str(exc), "metrics": {}}

    def _update_phase(self, cycle_id: Optional[int], phase: str) -> None:
        if cycle_id is None:
            return
        try:
            conn = _open_db(self._db_path)
            conn.execute(
                "UPDATE evolve_v3_cycles SET phase = ? WHERE cycle_id = ?",
                (phase, cycle_id),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    def record_correction(self, input_text: str, expected: str, predicted: str,
                          source: str = "manual") -> None:
        """Record a prediction correction for future evolution."""
        with self._lock:
            try:
                conn = _open_db(self._db_path)
                conn.execute("""
                    INSERT INTO evolve_v3_training (input_text, expected, predicted, correct, source)
                    VALUES (?, ?, ?, ?, ?)
                """, (input_text, expected, predicted, 0, source))
                conn.commit()
                conn.close()
            except Exception as exc:
                logger.warning("Correction recording failed: %s", exc)

    def status(self) -> dict:
        """Return current evolution status."""
        info: Dict[str, Any] = {
            "v2_available": self._v2 is not None,
            "apex_enabled": APEX_LLM_ENABLED,
            "db_path": str(self._db_path),
        }
        try:
            conn = _open_db(self._db_path)
            row = conn.execute("""
                SELECT COUNT(*), MAX(finished_at)
                FROM evolve_v3_cycles WHERE status = 'complete'
            """).fetchone()
            info["total_cycles"] = row[0] if row else 0
            info["last_cycle"] = row[1] if row else None
            trow = conn.execute("SELECT COUNT(*) FROM evolve_v3_training").fetchone()
            info["training_samples"] = trow[0] if trow else 0
            conn.close()
        except Exception:
            pass
        return info
