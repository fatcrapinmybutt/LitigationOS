"""
APEX Skill Router — Routes tasks to optimal skill chains.

Uses intent classification + skill matching to find the best workflow.
Shadow-programmed: LLM-enhanced routing when APEX_LLM_ENABLED=true,
keyword/heuristic routing when disabled.
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("apex.skill_router")

APEX_LLM_ENABLED: bool = os.environ.get("APEX_LLM_ENABLED", "false").lower() == "true"

_MODULE_DIR = Path(__file__).parent
_DB_DIR = _MODULE_DIR / "model_data"

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
        CREATE TABLE IF NOT EXISTS route_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            task        TEXT NOT NULL,
            matched     TEXT,
            chain       TEXT,
            confidence  REAL,
            method      TEXT,
            created_at  TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS route_feedback (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            task        TEXT NOT NULL,
            chain       TEXT,
            success     INTEGER,
            notes       TEXT,
            created_at  TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()


# ---------------------------------------------------------------------------
# Intent keywords for heuristic routing
# ---------------------------------------------------------------------------

_INTENT_KEYWORDS: Dict[str, List[str]] = {
    "draft_brief": ["brief", "draft brief", "write brief", "appellate brief", "legal brief"],
    "draft_complaint": ["complaint", "draft complaint", "file complaint", "new complaint"],
    "validate_filing": ["validate", "check filing", "filing review", "compliance check"],
    "appellate_strategy": ["appeal", "appellate", "coa", "leave to appeal", "msc"],
    "discovery_prep": ["discovery", "interrogatories", "requests for production", "deposition"],
    "impeachment": ["impeach", "credibility", "inconsistency", "prior statement"],
    "damage_calc": ["damages", "harm", "quantify", "compensation", "loss"],
    "federal_rights": ["1983", "civil rights", "federal", "constitutional", "due process"],
    "custody_analysis": ["custody", "parenting time", "best interest", "child"],
    "ppo_analysis": ["ppo", "protection order", "stalking", "harassment"],
    "convergence": ["convergence", "cross-lane", "multi-case", "pattern"],
}


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class SkillRouter:
    """Routes tasks to optimal skill chains."""

    CHAINS: Dict[str, List[str]] = {
        "draft_brief": [
            "litigation-claim-researcher",
            "litigation-cause-of-action-library",
            "litigation-brief-writer",
            "litigation-red-team",
        ],
        "draft_complaint": [
            "litigation-claim-researcher",
            "litigation-cause-of-action-library",
            "litigation-lawsuit-forge",
            "litigation-complaint-drafter",
        ],
        "validate_filing": [
            "litigation-authority-validator",
            "litigation-filing-architect",
            "litigation-pro-se-guardian",
        ],
        "appellate_strategy": [
            "litigation-appellate-strategist",
            "litigation-supreme-court-architect",
            "litigation-record-builder",
        ],
        "discovery_prep": [
            "litigation-evidence-harvester",
            "litigation-discovery-warfare",
            "litigation-analysis-engine",
        ],
        "impeachment": [
            "litigation-impeachment-engine",
            "litigation-evidence-harvester",
            "litigation-analysis-engine",
        ],
        "damage_calc": [
            "litigation-harm-quantifier",
            "litigation-analysis-engine",
        ],
        "federal_rights": [
            "litigation-federal-civil-rights",
            "litigation-claim-researcher",
        ],
        "custody_analysis": [
            "litigation-custody-specialist",
            "litigation-analysis-engine",
            "michigan-litigation-writer",
        ],
        "ppo_analysis": [
            "litigation-ppo-specialist",
            "litigation-analysis-engine",
        ],
        "convergence": [
            "litigation-convergence-orchestrator",
            "litigation-analysis-engine",
        ],
    }

    def __init__(self, db_path: Optional[str | Path] = None) -> None:
        self._lock = threading.Lock()
        self._db_path = Path(db_path) if db_path else _DB_DIR / "skill_router.db"
        self._skill_loader: Any = None
        self._init_db()

    def _init_db(self) -> None:
        try:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = _open_db(self._db_path)
            _ensure_tables(conn)
            conn.close()
        except Exception as exc:
            logger.warning("Router DB init failed: %s", exc)

    def _get_skill_loader(self) -> Any:
        """Lazily load SkillLoader to avoid circular imports."""
        if self._skill_loader is not None:
            return self._skill_loader
        try:
            from .skill_loader import SkillLoader
            self._skill_loader = SkillLoader()
            return self._skill_loader
        except Exception:
            try:
                import importlib
                mod = importlib.import_module("skill_loader")
                self._skill_loader = mod.SkillLoader()
                return self._skill_loader
            except Exception:
                return None

    # ------------------------------------------------------------------
    # Intent classification
    # ------------------------------------------------------------------

    def _classify_intent(self, task: str) -> tuple[str, float]:
        """Classify task intent. Returns ``(intent_key, confidence)``."""
        task_lower = task.lower()

        # LLM classification
        if APEX_LLM_ENABLED:
            try:
                from .model_router import ModelRouter  # type: ignore[import-untyped]
                router = ModelRouter()
                intents = list(self.CHAINS.keys())
                prompt = (
                    f"Classify this litigation task into one of these categories: "
                    f"{', '.join(intents)}.\n\nTask: {task[:500]}\n\n"
                    "Return JSON: {intent: str, confidence: float}"
                )
                result = router.route(prompt, task_type="classification")
                if isinstance(result, dict):
                    intent = result.get("intent", "")
                    conf = float(result.get("confidence", 0.0))
                    if intent in self.CHAINS and conf >= 0.3:
                        return intent, conf
            except Exception as exc:
                logger.debug("LLM intent classification failed: %s", exc)

        # Keyword heuristic (always available)
        best_intent = ""
        best_score = 0.0

        for intent, keywords in _INTENT_KEYWORDS.items():
            score = 0.0
            for kw in keywords:
                if kw in task_lower:
                    # Longer keyword matches are more specific → higher weight
                    score += len(kw.split()) * 2.0
            if score > best_score:
                best_score = score
                best_intent = intent

        if best_intent:
            confidence = min(best_score / 10.0, 1.0)
            return best_intent, round(confidence, 4)

        return "", 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def route(self, task: str, context: Optional[dict] = None) -> dict:
        """Route task to best skill chain.

        Returns ``{chain: list, intent: str, confidence: float, method: str}``.
        """
        try:
            intent, confidence = self._classify_intent(task)

            if intent and intent in self.CHAINS:
                chain = self.CHAINS[intent]
                method = "intent_match"
            else:
                # Fallback: use SkillLoader to match
                loader = self._get_skill_loader()
                if loader:
                    matches = loader.match_skills(task, top_k=3)
                    chain = [m["name"] for m in matches if "name" in m]
                    intent = "skill_match"
                    confidence = matches[0].get("match_score", 0.0) / 10.0 if matches else 0.0
                    method = "skill_loader"
                else:
                    chain = []
                    method = "none"

            result = {
                "chain": chain,
                "intent": intent,
                "confidence": round(confidence, 4),
                "method": method,
            }

            # Log the routing decision
            self._log_route(task, result)
            return result

        except Exception as exc:
            logger.error("Route failed: %s", exc)
            return {"chain": [], "intent": "", "confidence": 0.0, "method": "error"}

    def execute_chain(self, chain: List[str], context: dict) -> dict:
        """Execute a skill chain sequentially, passing context between steps.

        Returns ``{results: list, final_context: dict, status: str}``.
        """
        results: List[Dict[str, Any]] = []
        current_context = dict(context)

        for i, skill_name in enumerate(chain):
            step_result: Dict[str, Any] = {"skill": skill_name, "step": i}
            try:
                loader = self._get_skill_loader()
                skill_meta = loader.get_skill(skill_name) if loader else {}
                if skill_meta.get("error"):
                    step_result["status"] = "skipped"
                    step_result["reason"] = f"Skill not found: {skill_name}"
                    results.append(step_result)
                    continue

                # Execute the skill (placeholder — actual skill execution is
                # handled by the agent framework / skill_chaining module)
                step_result["status"] = "routed"
                step_result["skill_meta"] = {
                    "name": skill_meta.get("name", skill_name),
                    "description": skill_meta.get("description", "")[:200],
                    "path": skill_meta.get("path", ""),
                }
                current_context[f"step_{i}_skill"] = skill_name
                current_context[f"step_{i}_status"] = "routed"
                results.append(step_result)

            except Exception as exc:
                step_result["status"] = "error"
                step_result["error"] = str(exc)
                results.append(step_result)
                logger.warning("Chain step %d (%s) failed: %s", i, skill_name, exc)

        status = "complete"
        if any(r.get("status") == "error" for r in results):
            status = "partial"
        if all(r.get("status") == "error" for r in results):
            status = "failed"

        return {
            "results": results,
            "final_context": current_context,
            "status": status,
            "chain_length": len(chain),
        }

    def record_feedback(self, task: str, chain: List[str], success: bool,
                        notes: str = "") -> None:
        """Record feedback on a routing decision for future improvement."""
        with self._lock:
            try:
                conn = _open_db(self._db_path)
                conn.execute("""
                    INSERT INTO route_feedback (task, chain, success, notes)
                    VALUES (?, ?, ?, ?)
                """, (task, json.dumps(chain), int(success), notes))
                conn.commit()
                conn.close()
            except Exception as exc:
                logger.warning("Feedback recording failed: %s", exc)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _log_route(self, task: str, result: dict) -> None:
        try:
            conn = _open_db(self._db_path)
            conn.execute("""
                INSERT INTO route_log (task, matched, chain, confidence, method)
                VALUES (?, ?, ?, ?, ?)
            """, (
                task[:500],
                result.get("intent", ""),
                json.dumps(result.get("chain", [])),
                result.get("confidence", 0.0),
                result.get("method", ""),
            ))
            conn.commit()
            conn.close()
        except Exception:
            pass

    def stats(self) -> Dict[str, Any]:
        """Return routing statistics."""
        try:
            conn = _open_db(self._db_path)
            row = conn.execute("""
                SELECT
                    (SELECT COUNT(*) FROM route_log) AS total_routes,
                    (SELECT COUNT(*) FROM route_feedback) AS total_feedback,
                    (SELECT COUNT(*) FROM route_feedback WHERE success = 1) AS successes
            """).fetchone()
            conn.close()
            return {
                "total_routes": row[0] if row else 0,
                "total_feedback": row[1] if row else 0,
                "successes": row[2] if row else 0,
                "chains_defined": len(self.CHAINS),
            }
        except Exception:
            return {"total_routes": 0, "chains_defined": len(self.CHAINS)}
