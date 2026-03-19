#!/usr/bin/env python3
"""
APEX Task Router v2 — Historically-informed task routing.

Uses ``learning_loop.py`` data to pick the best model + skill chain for
each task.  Falls back to a static routing table when no historical data
is available.

Routing priority
----------------
1. Historical data (learning_loop model_performance)  → confidence > 0.7
2. LLM classification (if APEX_LLM_ENABLED)           → optional boost
3. Static keyword table                                → always works

Thread-safe, UTF-8 safe, never crashes.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Shadow LLM gate
# ---------------------------------------------------------------------------
APEX_LLM_ENABLED: bool = (
    os.environ.get("APEX_LLM_ENABLED", "false").lower() == "true"
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("apex.task_router_v2")

# ---------------------------------------------------------------------------
# Paths (never CWD — always relative to *this* file)
# ---------------------------------------------------------------------------
_HERE = Path(__file__).parent

# ---------------------------------------------------------------------------
# Static routing table (fallback when no historical data)
# ---------------------------------------------------------------------------
_STATIC_ROUTES: Dict[str, Dict[str, Any]] = {
    "legal_reasoning": {
        "primary": "manbearpig",
        "fallback": "rules_engine",
        "chain": ["litigation-analysis-engine"],
        "timeout": 60,
    },
    "legal_search": {
        "primary": "manbearpig",
        "fallback": "rules_engine",
        "chain": ["litigation-claim-researcher", "litigation-authority-validator"],
        "timeout": 45,
    },
    "filing": {
        "primary": "manbearpig",
        "fallback": "rules_engine",
        "chain": ["litigation-filing-architect", "litigation-brief-writer", "litigation-service-engine"],
        "timeout": 120,
    },
    "custody": {
        "primary": "manbearpig",
        "fallback": "rules_engine",
        "chain": ["litigation-custody-specialist", "litigation-evidence-harvester"],
        "timeout": 90,
    },
    "impeachment": {
        "primary": "manbearpig",
        "fallback": "regex",
        "chain": ["litigation-impeachment-engine", "litigation-red-team"],
        "timeout": 60,
    },
    "discovery": {
        "primary": "manbearpig",
        "fallback": "rules_engine",
        "chain": ["litigation-discovery-warfare", "litigation-evidence-harvester"],
        "timeout": 90,
    },
    "sanctions": {
        "primary": "manbearpig",
        "fallback": "rules_engine",
        "chain": ["litigation-sanctions-engine"],
        "timeout": 60,
    },
    "appeal": {
        "primary": "manbearpig",
        "fallback": "rules_engine",
        "chain": ["litigation-record-builder", "litigation-supreme-court-architect"],
        "timeout": 120,
    },
    "classification": {
        "primary": "manbearpig",
        "fallback": "naive_bayes",
        "chain": [],
        "timeout": 15,
    },
    "entity_extraction": {
        "primary": "manbearpig",
        "fallback": "regex",
        "chain": [],
        "timeout": 15,
    },
    "deadline": {
        "primary": "rules_engine",
        "fallback": "rules_engine",
        "chain": ["litigation-pipeline-commander"],
        "timeout": 30,
    },
    "evidence_search": {
        "primary": "manbearpig",
        "fallback": "rules_engine",
        "chain": ["litigation-evidence-harvester"],
        "timeout": 45,
    },
    "judicial_analysis": {
        "primary": "manbearpig",
        "fallback": "rules_engine",
        "chain": ["litigation-judicial-analyst"],
        "timeout": 60,
    },
    "ppo": {
        "primary": "manbearpig",
        "fallback": "rules_engine",
        "chain": ["litigation-ppo-specialist"],
        "timeout": 60,
    },
    "federal_1983": {
        "primary": "manbearpig",
        "fallback": "rules_engine",
        "chain": ["litigation-federal-civil-rights"],
        "timeout": 90,
    },
    "jtc_complaint": {
        "primary": "manbearpig",
        "fallback": "rules_engine",
        "chain": ["litigation-judicial-analyst", "litigation-complaint-drafter"],
        "timeout": 90,
    },
}

# ---------------------------------------------------------------------------
# Task classification keywords (compiled once, immutable)
# ---------------------------------------------------------------------------
_TASK_KEYWORDS: Dict[str, list[re.Pattern]] = {
    "filing": [re.compile(r"(?:file|filing|submit|e-?fil|court\s*packet|service\s*of\s*process)", re.I)],
    "custody": [re.compile(r"(?:custod|parenting|visitation|child\s*support|best\s*interest)", re.I)],
    "impeachment": [re.compile(r"(?:impeach|credibil|contradict|prior.*statement|inconsisten)", re.I)],
    "discovery": [re.compile(r"(?:discover|interrogator|request.*production|deposition|subpoena)", re.I)],
    "sanctions": [re.compile(r"(?:sanction|contempt|vexatious|frivolous|rule\s*11)", re.I)],
    "appeal": [re.compile(r"(?:appeal|appell|COA|MSC|supreme\s*court|circuit\s*court)", re.I)],
    "classification": [re.compile(r"(?:classify|categoriz|sort|label|tag)", re.I)],
    "entity_extraction": [re.compile(r"(?:extract|entit|NER|named?\s*entity|parse\s*name)", re.I)],
    "deadline": [re.compile(r"(?:deadline|due\s*date|calendar|schedul|time\s*limit|statute\s*of\s*limit)", re.I)],
    "evidence_search": [re.compile(r"(?:evidence|exhibit|document.*search|find.*proof)", re.I)],
    "judicial_analysis": [re.compile(r"(?:judge|judicial|bench|disqualif|bias|recus)", re.I)],
    "legal_search": [re.compile(r"(?:search|find|look\s*up|query|research|case\s*law|statute|MCR|MCL)", re.I)],
    "ppo": [re.compile(r"(?:PPO|protect.*order|restraining|no.?contact)", re.I)],
    "federal_1983": [re.compile(r"(?:1983|§\s*1983|civil\s*rights|federal|42\s*U\.?S\.?C)", re.I)],
    "jtc_complaint": [re.compile(r"(?:JTC|judicial\s*tenure|misconduct\s*complaint)", re.I)],
}

# ---------------------------------------------------------------------------
# Lane keywords for auto-detection
# ---------------------------------------------------------------------------
_LANE_KEYWORDS: Dict[str, re.Pattern] = {
    "E": re.compile(r"(?:mcneill|judicial\s*misconduct|JTC|tenure\s*commission)", re.I),
    "D": re.compile(r"(?:PPO|protection\s*order|restraining|no.?contact|2023-5907)", re.I),
    "F": re.compile(r"(?:COA|appell|366810|supreme\s*court|court\s*of\s*appeal)", re.I),
    "C": re.compile(r"(?:cross.?lane|convergence|multi.?lane)", re.I),
    "A": re.compile(r"(?:custody|parenting|watson|pigors|2024-001507|visitation|child\s*support)", re.I),
    "B": re.compile(r"(?:shady\s*oaks|housing|2025-002760|habitab|landlord|tenant)", re.I),
}


# ---------------------------------------------------------------------------
# Lazy loader for LearningLoop (avoids import-time failures)
# ---------------------------------------------------------------------------
_ll_lock = threading.Lock()
_ll_instance = None  # type: Any


def _get_learning_loop():
    """Lazy-load LearningLoop singleton.  Returns None on failure."""
    global _ll_instance  # noqa: PLW0603
    if _ll_instance is None:
        with _ll_lock:
            if _ll_instance is None:
                try:
                    from learning_loop import get_learning_loop
                    _ll_instance = get_learning_loop()
                except Exception as exc:  # noqa: BLE001
                    logger.debug("LearningLoop unavailable: %s", exc)
                    _ll_instance = False  # sentinel: tried and failed
    return _ll_instance if _ll_instance is not False else None


# ---------------------------------------------------------------------------
# TaskRouterV2
# ---------------------------------------------------------------------------
class TaskRouterV2:
    """Historically-informed task router.

    Uses ``LearningLoop`` data when available; falls back to ``_STATIC_ROUTES``.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Primary entry — route()
    # ------------------------------------------------------------------
    def route(
        self, task_description: str, lane: Optional[str] = None
    ) -> Dict[str, Any]:
        """Route *task_description* to the optimal model + skill chain.

        Returns
        -------
        dict
            ``{task_type, lane, model, fallback, chain, timeout, source}``
        """
        try:
            task_type = self.classify_task(task_description)
            detected_lane = lane or self._detect_lane(task_description)

            # 1. Try historical recommendation
            rec = self.recommend_chain(task_type)
            if rec.get("source") == "historical":
                rec["task_type"] = task_type
                rec["lane"] = detected_lane
                return rec

            # 2. Static route
            static = _STATIC_ROUTES.get(task_type, _STATIC_ROUTES["legal_reasoning"])
            return {
                "task_type": task_type,
                "lane": detected_lane,
                "model": static["primary"],
                "fallback": static["fallback"],
                "chain": list(static["chain"]),
                "timeout": static["timeout"],
                "source": "static",
                "estimated_time": self.estimate_time(task_type, static["primary"]),
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning("route() failed: %s", exc)
            return {
                "task_type": "legal_reasoning",
                "lane": lane or "A",
                "model": "manbearpig",
                "fallback": "rules_engine",
                "chain": ["litigation-analysis-engine"],
                "timeout": 60,
                "source": "emergency_fallback",
                "error": str(exc),
            }

    # ------------------------------------------------------------------
    # Task classification
    # ------------------------------------------------------------------
    def classify_task(self, text: str) -> str:
        """Classify task type from text using keyword patterns + optional LLM."""
        try:
            # Keyword-based classification
            scores: Dict[str, int] = {}
            for task_type, patterns in _TASK_KEYWORDS.items():
                for rx in patterns:
                    matches = rx.findall(text)
                    if matches:
                        scores[task_type] = scores.get(task_type, 0) + len(matches)

            if scores:
                best = max(scores, key=scores.get)  # type: ignore[arg-type]
                if scores[best] >= 1:
                    return best

            # LLM classification (optional)
            if APEX_LLM_ENABLED:
                llm_type = self._llm_classify(text)
                if llm_type and llm_type in _STATIC_ROUTES:
                    return llm_type

            return "legal_reasoning"  # safe default
        except Exception as exc:  # noqa: BLE001
            logger.debug("classify_task: %s", exc)
            return "legal_reasoning"

    def _llm_classify(self, text: str) -> Optional[str]:
        """Optional LLM-based task classification.  Shadow-gated."""
        if not APEX_LLM_ENABLED:
            return None
        try:
            # Attempt to use MANBEARPIG inference for classification
            from inference_engine import MichiganLegalModel
            model = MichiganLegalModel()
            result = model.classify(text)
            if isinstance(result, dict):
                return result.get("task_type") or result.get("category")
        except Exception as exc:  # noqa: BLE001
            logger.debug("_llm_classify: %s", exc)
        return None

    # ------------------------------------------------------------------
    # Lane detection
    # ------------------------------------------------------------------
    @staticmethod
    def _detect_lane(text: str) -> str:
        """Auto-detect case lane from text.  Priority: E → D → F → C → A → B."""
        for lane, rx in _LANE_KEYWORDS.items():
            if rx.search(text):
                return lane
        return "A"  # default

    # ------------------------------------------------------------------
    # Historical recommendations
    # ------------------------------------------------------------------
    def recommend_chain(self, task_type: str) -> Dict[str, Any]:
        """Recommend skill chain based on historical performance data."""
        try:
            ll = _get_learning_loop()
            if ll is None:
                return {"source": "none", "reason": "learning_loop unavailable"}

            best_model = ll.get_best_model(task_type)
            if best_model == "manbearpig":
                # Check if we have actual historical data or just the default
                summary = ll.summary()
                if summary.get("total_tasks", 0) < 3:
                    return {"source": "none", "reason": "insufficient historical data"}

            static = _STATIC_ROUTES.get(task_type, _STATIC_ROUTES["legal_reasoning"])
            return {
                "model": best_model,
                "fallback": static["fallback"],
                "chain": list(static["chain"]),
                "timeout": static["timeout"],
                "source": "historical",
                "estimated_time": self.estimate_time(task_type, best_model),
            }
        except Exception as exc:  # noqa: BLE001
            logger.debug("recommend_chain: %s", exc)
            return {"source": "error", "error": str(exc)}

    # ------------------------------------------------------------------
    # Time estimation
    # ------------------------------------------------------------------
    def estimate_time(self, task_type: str, model: str) -> float:
        """Estimate execution time in seconds based on historical data."""
        try:
            ll = _get_learning_loop()
            if ll is None:
                return self._static_estimate(task_type)

            conn = ll._get_conn()
            if conn is None:
                return self._static_estimate(task_type)

            row = conn.execute(
                "SELECT avg_latency, sample_count FROM model_performance "
                "WHERE model_name = ? AND task_type = ?",
                (model, task_type),
            ).fetchone()

            if row and row["sample_count"] >= 2:
                return round(row["avg_latency"], 1)

            return self._static_estimate(task_type)
        except Exception as exc:  # noqa: BLE001
            logger.debug("estimate_time: %s", exc)
            return self._static_estimate(task_type)

    @staticmethod
    def _static_estimate(task_type: str) -> float:
        """Static time estimate for task types."""
        estimates: Dict[str, float] = {
            "classification": 5.0,
            "entity_extraction": 8.0,
            "legal_search": 15.0,
            "deadline": 10.0,
            "evidence_search": 20.0,
            "legal_reasoning": 30.0,
            "judicial_analysis": 30.0,
            "impeachment": 25.0,
            "custody": 45.0,
            "discovery": 45.0,
            "sanctions": 30.0,
            "filing": 60.0,
            "appeal": 60.0,
            "ppo": 30.0,
            "federal_1983": 45.0,
            "jtc_complaint": 45.0,
        }
        return estimates.get(task_type, 30.0)

    # ------------------------------------------------------------------
    # Status / introspection
    # ------------------------------------------------------------------
    def status(self) -> Dict[str, Any]:
        """Router status report."""
        try:
            ll = _get_learning_loop()
            ll_status = "available" if ll else "unavailable"
            ll_summary = ll.summary() if ll else {}

            return {
                "status": "ok",
                "llm_enabled": APEX_LLM_ENABLED,
                "learning_loop": ll_status,
                "total_task_types": len(_STATIC_ROUTES),
                "task_types": list(_STATIC_ROUTES.keys()),
                "historical_tasks": ll_summary.get("total_tasks", 0),
                "top_models": ll_summary.get("top_models", []),
            }
        except Exception as exc:  # noqa: BLE001
            return {"status": "error", "error": str(exc)}


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_instance_lock = threading.Lock()
_instance: Optional[TaskRouterV2] = None


def get_task_router() -> TaskRouterV2:
    """Return module-level singleton.  Thread-safe lazy init."""
    global _instance  # noqa: PLW0603
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = TaskRouterV2()
    return _instance


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _cli_main() -> None:
    """``python task_router_v2.py <task description>``"""
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if len(sys.argv) < 2:
        router = get_task_router()
        print(json.dumps(router.status(), indent=2, ensure_ascii=False))
        return

    text = " ".join(sys.argv[1:])
    router = get_task_router()
    result = router.route(text)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    _cli_main()
