"""
APEX Orchestrator — Central Brain of APEX_MANBEARPIG_LITIGATIONOS
=================================================================

Routes tasks to optimal agent+model combination based on task type,
complexity, and available resources.

DISPATCH MATRIX (from litigation-os SKILL.md):
  New lawsuit:  claim-researcher → cause-of-action-library → lawsuit-forge
                → complaint-drafter → red-team → service-engine
  Appeal:       record-builder → appellate-strategist → brief-writer → red-team
  MSC:          supreme-court-architect → brief-writer → red-team → service-engine
  Discovery:    discovery-warfare → brief-writer
  Convergence:  convergence-orchestrator → evidence-harvester
                → authority-validator → pipeline-commander
  Emergency:    pro-se-guardian → filing-architect → service-engine
  Sanctions:    sanctions-engine → brief-writer → red-team
  Impeachment:  impeachment-engine → evidence-harvester → red-team

ARCHITECTURE:
  - Shadow-programmed: LLM features OFF by default
  - Fallback chain: LLM → MANBEARPIG → Rules → Regex
  - Thread-safe, never crashes, lazy-loads everything
  - Never sets CWD to repo root (shadow modules)

DATABASE CONNECTIONS (all use mandatory PRAGMA set):
  litigation_context.db  — 702 tables, primary search target
  master_index.db        — 1.7M files for file-level search
  lane_*_*.db            — Per-lane case databases

Author: APEX_MANBEARPIG_LITIGATIONOS
"""

from __future__ import annotations

import io
import json
import logging
import os
import re
import sqlite3
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Shadow-program gate — LLM features OFF by default
# ---------------------------------------------------------------------------
APEX_LLM_ENABLED: bool = (
    os.environ.get("APEX_LLM_ENABLED", "false").lower() == "true"
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("apex.orchestrator")

# ---------------------------------------------------------------------------
# Path anchors (never use repo root as CWD)
# ---------------------------------------------------------------------------
_HERE: Path = Path(__file__).parent
_REPO: Path = _HERE.parent.parent  # …/LitigationOS
_DB_PATH: Path = _REPO / "litigation_context.db"

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
    """Open a SQLite connection with mandatory PRAGMAs.  Returns None on error."""
    try:
        p = str(db_path)
        if not Path(p).exists():
            logger.warning("DB not found: %s", p)
            return None
        conn = sqlite3.connect(p, timeout=60, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.executescript(_DB_PRAGMAS)
        return conn
    except Exception as exc:  # noqa: BLE001
        logger.error("DB connect failed (%s): %s", db_path, exc)
        return None


# ═══════════════════════════════════════════════════════════════════════════
# MEEK Signal Patterns — lane routing regexes
# Detection priority: E → D → F → C → A → B
# ═══════════════════════════════════════════════════════════════════════════
MEEK_SIGNALS: Dict[str, List[re.Pattern]] = {
    "E": [re.compile(p, re.IGNORECASE) for p in [
        r"misconduct", r"McNeill", r"JTC", r"MCR\s*9\.2",
        r"judicial\s+bias", r"ex\s*parte.*order",
    ]],
    "D": [re.compile(p, re.IGNORECASE) for p in [
        r"PPO", r"protection\s+order", r"MCL\s*600\.2950",
        r"stalking", r"no.contact",
    ]],
    "F": [re.compile(p, re.IGNORECASE) for p in [
        r"appellate", r"COA\s*366810", r"MSC",
        r"MCR\s*7\.[23]", r"appeal", r"leave\s+to\s+appeal",
    ]],
    "C": [re.compile(p, re.IGNORECASE) for p in [
        r"convergence", r"cross.lane", r"conspiracy",
        r"coordinated", r"pattern.*practice",
    ]],
    "A": [re.compile(p, re.IGNORECASE) for p in [
        r"custody", r"parenting", r"Watson", r"L\.D\.W",
        r"best\s+interest", r"MCL\s*722",
    ]],
    "B": [re.compile(p, re.IGNORECASE) for p in [
        r"housing", r"Shady\s+Oaks", r"habitab", r"tenant",
        r"MCL\s*125", r"Truth\s+in\s+Renting", r"rent",
    ]],
}

# Lane detection priority order (copilot-instructions.md)
_LANE_PRIORITY: List[str] = ["E", "D", "F", "C", "A", "B"]

# ═══════════════════════════════════════════════════════════════════════════
# Task-type keyword patterns (compiled once)
# ═══════════════════════════════════════════════════════════════════════════
_TASK_PATTERNS: Dict[str, List[re.Pattern]] = {
    "new_lawsuit": [re.compile(p, re.IGNORECASE) for p in [
        r"\bnew\s+lawsuit\b", r"\bfile\s+suit\b", r"\bnew\s+complaint\b",
        r"\binitiate\s+action\b", r"\bsummons\b",
    ]],
    "appeal": [re.compile(p, re.IGNORECASE) for p in [
        r"\bappeal\b", r"\bCOA\b", r"\bclaim\s+of\s+appeal\b",
        r"\bappellate\s+brief\b", r"\bleave\s+to\s+appeal\b",
    ]],
    "msc_writ": [re.compile(p, re.IGNORECASE) for p in [
        r"\bMSC\b", r"\bsupreme\s+court\b", r"\bwrit\b",
        r"\bapplication.*leave\b",
    ]],
    "discovery": [re.compile(p, re.IGNORECASE) for p in [
        r"\bdiscovery\b", r"\binterrogator", r"\bdeposition\b",
        r"\brequest.*production\b", r"\bsubpoena\b",
    ]],
    "motion": [re.compile(p, re.IGNORECASE) for p in [
        r"\bmotion\b", r"\bfile\s+motion\b", r"\bmotion\s+to\b",
    ]],
    "convergence": [re.compile(p, re.IGNORECASE) for p in [
        r"\bconvergence\b", r"\bcross.lane\b", r"\bpattern.*practice\b",
    ]],
    "emergency": [re.compile(p, re.IGNORECASE) for p in [
        r"\bemergency\b", r"\bex\s*parte\b", r"\bTRO\b",
        r"\btemporary\s+restraining\b", r"\bimmediate\s+danger\b",
    ]],
    "sanctions": [re.compile(p, re.IGNORECASE) for p in [
        r"\bsanction", r"\bMCR\s*2\.114\b", r"\bfrivolous\b",
        r"\bbad\s+faith\b",
    ]],
    "impeachment": [re.compile(p, re.IGNORECASE) for p in [
        r"\bimpeach", r"\bcredibility\b", r"\bprior.*inconsistent\b",
        r"\bcontradiction\b",
    ]],
    "jtc_complaint": [re.compile(p, re.IGNORECASE) for p in [
        r"\bJTC\b", r"\bjudicial\s+tenure\b", r"\bmisconduct\s+complaint\b",
        r"\bjudicial\s+misconduct\b",
    ]],
    "federal_1983": [re.compile(p, re.IGNORECASE) for p in [
        r"\b1983\b", r"\bcivil\s+rights\b", r"\b42\s+USC\b",
        r"\bfederal\s+complaint\b", r"\bRICO\b",
    ]],
    "custody": [re.compile(p, re.IGNORECASE) for p in [
        r"\bcustody\b", r"\bparenting\s+time\b", r"\bbest\s+interest\b",
        r"\bchild\s+custody\b",
    ]],
    "ppo": [re.compile(p, re.IGNORECASE) for p in [
        r"\bPPO\b", r"\bprotection\s+order\b", r"\bno.contact\b",
        r"\bstalking\b",
    ]],
    "damages": [re.compile(p, re.IGNORECASE) for p in [
        r"\bdamage[s]?\b", r"\bharm\b", r"\bquantif",
        r"\bcompensation\b", r"\btreble\b",
    ]],
    "research": [re.compile(p, re.IGNORECASE) for p in [
        r"\bresearch\b", r"\blook\s+up\b", r"\bfind\s+authority\b",
        r"\bcase\s+law\b", r"\bstatute\b",
    ]],
}


# ═══════════════════════════════════════════════════════════════════════════
# Data classes
# ═══════════════════════════════════════════════════════════════════════════
@dataclass
class ExecutionPlan:
    """Immutable execution plan produced by ``plan()``."""

    task_type: str = "research"
    lane: str = "C"
    skill_chain: List[str] = field(default_factory=list)
    models_needed: List[str] = field(default_factory=list)
    estimated_seconds: float = 0.0
    resource_check: Dict[str, bool] = field(default_factory=dict)
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_type": self.task_type,
            "lane": self.lane,
            "skill_chain": list(self.skill_chain),
            "models_needed": list(self.models_needed),
            "estimated_seconds": self.estimated_seconds,
            "resource_check": dict(self.resource_check),
            "confidence": self.confidence,
        }


@dataclass
class ExecutionResult:
    """Result of executing a task through the orchestrator."""

    status: str = "unknown"          # ok | error | dry_run
    task_type: str = "research"
    lane: str = "C"
    skill_chain: List[str] = field(default_factory=list)
    outputs: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    elapsed_seconds: float = 0.0
    quality_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "task_type": self.task_type,
            "lane": self.lane,
            "skill_chain": list(self.skill_chain),
            "outputs": list(self.outputs),
            "errors": list(self.errors),
            "elapsed_seconds": self.elapsed_seconds,
            "quality_score": self.quality_score,
        }


# ═══════════════════════════════════════════════════════════════════════════
# APEXOrchestrator
# ═══════════════════════════════════════════════════════════════════════════
class APEXOrchestrator:
    """Central orchestration brain for the APEX system.

    Routes incoming tasks to the optimal agent + model combination based on
    task type, complexity, and available resources.  Works fully offline;
    LLM features activate only when ``APEX_LLM_ENABLED=true``.
    """

    # ------------------------------------------------------------------
    # Skill dispatch chains — ordered sequences of agents per task type
    # ------------------------------------------------------------------
    SKILL_CHAINS: Dict[str, List[str]] = {
        "new_lawsuit": [
            "claim-researcher", "cause-of-action-library", "lawsuit-forge",
            "complaint-drafter", "red-team", "service-engine",
        ],
        "appeal": [
            "record-builder", "appellate-strategist", "brief-writer", "red-team",
        ],
        "msc_writ": [
            "supreme-court-architect", "brief-writer", "red-team", "service-engine",
        ],
        "discovery": ["discovery-warfare", "brief-writer"],
        "motion": [
            "claim-researcher", "brief-writer", "red-team", "filing-architect",
        ],
        "convergence": [
            "convergence-orchestrator", "evidence-harvester",
            "authority-validator", "pipeline-commander",
        ],
        "emergency": ["pro-se-guardian", "filing-architect", "service-engine"],
        "sanctions": ["sanctions-engine", "brief-writer", "red-team"],
        "impeachment": ["impeachment-engine", "evidence-harvester", "red-team"],
        "jtc_complaint": [
            "judicial-analyst", "impeachment-engine", "complaint-drafter",
            "red-team",
        ],
        "federal_1983": [
            "federal-civil-rights", "claim-researcher", "complaint-drafter",
            "red-team",
        ],
        "custody": [
            "custody-specialist", "evidence-harvester", "brief-writer", "red-team",
        ],
        "ppo": ["ppo-specialist", "evidence-harvester", "brief-writer"],
        "damages": ["harm-quantifier", "evidence-harvester", "analysis-engine"],
        "research": ["claim-researcher", "authority-validator", "analysis-engine"],
    }

    # ------------------------------------------------------------------
    # Case lane routing metadata
    # ------------------------------------------------------------------
    LANE_MAP: Dict[str, Dict[str, str]] = {
        "A": {"name": "Custody",      "case": "2024-001507-DC",  "db": "lane_A_custody.db"},
        "B": {"name": "Housing",      "case": "2025-002760-CZ",  "db": "lane_B_housing.db"},
        "C": {"name": "Convergence",  "case": "Multi-lane",      "db": "lane_C_convergence.db"},
        "D": {"name": "PPO",          "case": "2023-5907-PP",    "db": "lane_D_ppo.db"},
        "E": {"name": "Misconduct",   "case": "Judge McNeill",   "db": "lane_E_misconduct.db"},
        "F": {"name": "Appellate",    "case": "COA 366810",      "db": "lane_F_appellate.db"},
    }

    # ------------------------------------------------------------------
    # Model assignments per abstract task category
    # ------------------------------------------------------------------
    MODEL_ASSIGNMENTS: Dict[str, str] = {
        "drafting":       "saul-legal",
        "classification": "qwen-fast",
        "research":       "hybrid",        # BM25 + TF-IDF + semantic
        "validation":     "rules",
        "ner":            "bert-ner",
        "embeddings":     "nomic-embed-text",
        "calculation":    "rules",
    }

    # Skill → model-category mapping for resource estimation
    _SKILL_MODEL_NEEDS: Dict[str, str] = {
        "claim-researcher":         "research",
        "cause-of-action-library":  "research",
        "lawsuit-forge":            "drafting",
        "complaint-drafter":        "drafting",
        "red-team":                 "validation",
        "service-engine":           "calculation",
        "record-builder":           "research",
        "appellate-strategist":     "research",
        "brief-writer":             "drafting",
        "supreme-court-architect":  "research",
        "discovery-warfare":        "research",
        "filing-architect":         "drafting",
        "convergence-orchestrator": "research",
        "evidence-harvester":       "research",
        "authority-validator":      "validation",
        "pipeline-commander":       "calculation",
        "pro-se-guardian":          "validation",
        "sanctions-engine":         "research",
        "impeachment-engine":       "research",
        "judicial-analyst":         "research",
        "federal-civil-rights":     "research",
        "custody-specialist":       "research",
        "ppo-specialist":           "research",
        "harm-quantifier":          "calculation",
        "analysis-engine":          "research",
    }

    # Approximate per-skill execution time (seconds)
    _SKILL_TIME_EST: Dict[str, float] = {
        "claim-researcher": 8.0, "cause-of-action-library": 5.0,
        "lawsuit-forge": 12.0, "complaint-drafter": 15.0,
        "red-team": 10.0, "service-engine": 3.0,
        "record-builder": 10.0, "appellate-strategist": 12.0,
        "brief-writer": 20.0, "supreme-court-architect": 15.0,
        "discovery-warfare": 10.0, "filing-architect": 8.0,
        "convergence-orchestrator": 10.0, "evidence-harvester": 8.0,
        "authority-validator": 6.0, "pipeline-commander": 5.0,
        "pro-se-guardian": 5.0, "sanctions-engine": 8.0,
        "impeachment-engine": 10.0, "judicial-analyst": 12.0,
        "federal-civil-rights": 10.0, "custody-specialist": 10.0,
        "ppo-specialist": 8.0, "harm-quantifier": 6.0,
        "analysis-engine": 8.0,
    }

    # ------------------------------------------------------------------
    # Init
    # ------------------------------------------------------------------
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._router: Any = None          # ModelRouter (lazy)
        self._quality_gate: Any = None    # QualityGate (lazy)
        self._integration: Any = None     # APEXEngine  (lazy)
        self._inference: Any = None       # MichiganLegalModel (lazy)
        logger.info(
            "APEXOrchestrator init  LLM=%s  DB=%s",
            APEX_LLM_ENABLED, _DB_PATH,
        )

    # ------------------------------------------------------------------
    # Lazy loaders (thread-safe, never crash)
    # ------------------------------------------------------------------
    def _get_router(self) -> Any:
        if self._router is None:
            with self._lock:
                if self._router is None:
                    try:
                        saved = os.getcwd()
                        os.chdir(str(_HERE))
                        from model_router import ModelRouter  # type: ignore[import-untyped]
                        self._router = ModelRouter()
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("ModelRouter unavailable: %s", exc)
                        self._router = _StubRouter()
                    finally:
                        try:
                            os.chdir(saved)
                        except Exception:  # noqa: BLE001
                            pass
        return self._router

    def _get_quality_gate(self) -> Any:
        if self._quality_gate is None:
            with self._lock:
                if self._quality_gate is None:
                    try:
                        saved = os.getcwd()
                        os.chdir(str(_HERE))
                        from quality_gate import QualityGate  # type: ignore[import-untyped]
                        self._quality_gate = QualityGate()
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("QualityGate unavailable: %s", exc)
                        self._quality_gate = _StubQualityGate()
                    finally:
                        try:
                            os.chdir(saved)
                        except Exception:  # noqa: BLE001
                            pass
        return self._quality_gate

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
                        self._inference = None
                    finally:
                        try:
                            os.chdir(saved)
                        except Exception:  # noqa: BLE001
                            pass
        return self._inference

    def _get_integration(self) -> Any:
        if self._integration is None:
            with self._lock:
                if self._integration is None:
                    try:
                        saved = os.getcwd()
                        os.chdir(str(_HERE))
                        from apex_integration import APEXEngine  # type: ignore[import-untyped]
                        self._integration = APEXEngine()
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("APEXEngine unavailable: %s", exc)
                        self._integration = None
                    finally:
                        try:
                            os.chdir(saved)
                        except Exception:  # noqa: BLE001
                            pass
        return self._integration

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------
    def detect_task_type(self, text: str) -> str:
        """Classify *text* into one of the SKILL_CHAINS keys.

        Uses compiled regex patterns with a priority-ordered scan.
        Falls back to ``"research"`` if nothing matches.
        """
        try:
            if not text or not text.strip():
                return "research"

            # Priority order mirrors common litigation urgency
            priority = [
                "emergency", "jtc_complaint", "federal_1983", "impeachment",
                "sanctions", "msc_writ", "appeal", "new_lawsuit", "discovery",
                "motion", "convergence", "custody", "ppo", "damages", "research",
            ]

            scores: Dict[str, int] = {}
            for ttype in priority:
                pats = _TASK_PATTERNS.get(ttype, [])
                hits = sum(1 for p in pats if p.search(text))
                if hits:
                    scores[ttype] = hits

            if not scores:
                return "research"

            # Return highest-scoring type; on tie, use priority order
            max_score = max(scores.values())
            for ttype in priority:
                if scores.get(ttype, 0) == max_score:
                    return ttype

            return "research"
        except Exception as exc:  # noqa: BLE001
            logger.error("detect_task_type failed: %s", exc)
            return "research"

    def detect_lane(self, text: str) -> str:
        """Detect case lane (A-F) from *text* using MEEK signal patterns.

        Detection priority: E → D → F → C → A → B (per copilot-instructions).
        Returns ``"C"`` (convergence / default) if no signals match.
        """
        try:
            if not text or not text.strip():
                return "C"

            scores: Dict[str, int] = {}
            for lane_id in _LANE_PRIORITY:
                patterns = MEEK_SIGNALS.get(lane_id, [])
                hits = sum(1 for p in patterns if p.search(text))
                if hits:
                    scores[lane_id] = hits

            if not scores:
                return "C"

            # Return first lane in priority order with max score
            max_score = max(scores.values())
            for lane_id in _LANE_PRIORITY:
                if scores.get(lane_id, 0) == max_score:
                    return lane_id

            return "C"
        except Exception as exc:  # noqa: BLE001
            logger.error("detect_lane failed: %s", exc)
            return "C"

    def get_skill_chain(self, task_type: str) -> List[str]:
        """Return the skill dispatch chain for *task_type*.

        Falls back to the ``"research"`` chain for unknown types.
        """
        return list(self.SKILL_CHAINS.get(task_type, self.SKILL_CHAINS["research"]))

    # ------------------------------------------------------------------
    # Plan (read-only analysis)
    # ------------------------------------------------------------------
    def plan(self, task_description: str) -> Dict[str, Any]:
        """Analyze a task and return an execution plan WITHOUT executing.

        Returns a dict with: task_type, lane, skill_chain, models_needed,
        estimated_time, resource_check, confidence.
        """
        try:
            task_type = self.detect_task_type(task_description)
            lane = self.detect_lane(task_description)
            chain = self.get_skill_chain(task_type)

            # Determine which model categories are required
            model_cats: List[str] = list(dict.fromkeys(
                self._SKILL_MODEL_NEEDS.get(s, "research") for s in chain
            ))
            models_needed = [self.MODEL_ASSIGNMENTS.get(c, "manbearpig") for c in model_cats]

            # Estimate execution time
            est = sum(self._SKILL_TIME_EST.get(s, 8.0) for s in chain)

            # Resource check
            resources = self._check_resources(lane, models_needed)

            # Confidence heuristic: based on signal strength
            confidence = self._compute_confidence(task_description, task_type, lane)

            ep = ExecutionPlan(
                task_type=task_type,
                lane=lane,
                skill_chain=chain,
                models_needed=models_needed,
                estimated_seconds=est,
                resource_check=resources,
                confidence=confidence,
            )
            return ep.to_dict()
        except Exception as exc:  # noqa: BLE001
            logger.error("plan() failed: %s", exc)
            return ExecutionPlan(
                task_type="research", lane="C",
                skill_chain=list(self.SKILL_CHAINS["research"]),
            ).to_dict()

    # ------------------------------------------------------------------
    # Execute
    # ------------------------------------------------------------------
    def execute(
        self,
        task_description: str,
        lane: Optional[str] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Execute a task through the full pipeline.

        Steps:
          1. Classify task type
          2. Detect case lane (or use *lane* override)
          3. Select skill chain
          4. Check resources
          5. Execute each skill in chain (or simulate if *dry_run*)
          6. Quality-gate the output
          7. Return results

        Returns an :class:`ExecutionResult` as a dict.
        """
        t0 = time.monotonic()
        result = ExecutionResult()
        try:
            # 1. Classify
            result.task_type = self.detect_task_type(task_description)

            # 2. Lane
            result.lane = lane if lane and lane in self.LANE_MAP else self.detect_lane(task_description)

            # 3. Skill chain
            result.skill_chain = self.get_skill_chain(result.task_type)

            # 4. Resource check
            resources = self._check_resources(result.lane, [])
            if not resources.get("db_available", False) and not dry_run:
                result.errors.append("Primary database unavailable")

            # 5. Execute or simulate
            if dry_run:
                result.status = "dry_run"
                for skill in result.skill_chain:
                    result.outputs.append({
                        "skill": skill,
                        "status": "simulated",
                        "model": self.MODEL_ASSIGNMENTS.get(
                            self._SKILL_MODEL_NEEDS.get(skill, "research"), "manbearpig",
                        ),
                    })
            else:
                result.status = "ok"
                for skill in result.skill_chain:
                    skill_result = self._execute_skill(
                        skill, task_description, result.lane,
                    )
                    result.outputs.append(skill_result)
                    if skill_result.get("status") == "error":
                        result.errors.append(
                            f"{skill}: {skill_result.get('error', 'unknown')}"
                        )

            # 6. Quality gate (only on real execution with outputs)
            if not dry_run and result.outputs:
                result.quality_score = self._run_quality_gate(result)

            # 7. Finalize
            result.elapsed_seconds = round(time.monotonic() - t0, 3)
            if result.errors and result.status == "ok":
                result.status = "partial"

            return result.to_dict()

        except Exception as exc:  # noqa: BLE001
            logger.error("execute() failed: %s", exc)
            result.status = "error"
            result.errors.append(str(exc))
            result.elapsed_seconds = round(time.monotonic() - t0, 3)
            return result.to_dict()

    # ------------------------------------------------------------------
    # System status
    # ------------------------------------------------------------------
    def system_status(self) -> Dict[str, Any]:
        """Full system health check: models, databases, skills, resources."""
        status: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "llm_enabled": APEX_LLM_ENABLED,
            "databases": {},
            "skill_chains": len(self.SKILL_CHAINS),
            "lanes": {},
            "models": dict(self.MODEL_ASSIGNMENTS),
            "components": {},
        }
        try:
            # Database health
            main_db = _DB_PATH
            status["databases"]["litigation_context"] = {
                "path": str(main_db),
                "exists": main_db.exists(),
                "size_mb": round(main_db.stat().st_size / 1_048_576, 1) if main_db.exists() else 0,
            }

            master_idx = _REPO / "agents" / "master_index.db"
            status["databases"]["master_index"] = {
                "path": str(master_idx),
                "exists": master_idx.exists(),
            }

            # Lane databases
            for lane_id, info in self.LANE_MAP.items():
                db_file = _REPO / info["db"]
                status["lanes"][lane_id] = {
                    "name": info["name"],
                    "case": info["case"],
                    "db_exists": db_file.exists(),
                }

            # Component availability
            status["components"]["model_router"] = not isinstance(self._get_router(), _StubRouter)
            status["components"]["quality_gate"] = not isinstance(self._get_quality_gate(), _StubQualityGate)
            status["components"]["inference_engine"] = self._get_inference() is not None
            status["components"]["apex_engine"] = self._get_integration() is not None

        except Exception as exc:  # noqa: BLE001
            logger.error("system_status() partial failure: %s", exc)
            status["error"] = str(exc)

        return status

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _check_resources(
        self, lane: str, models_needed: List[str],
    ) -> Dict[str, bool]:
        """Check if required resources are available."""
        result: Dict[str, bool] = {
            "db_available": _DB_PATH.exists(),
            "lane_db_available": False,
            "llm_available": APEX_LLM_ENABLED,
        }
        try:
            lane_info = self.LANE_MAP.get(lane, {})
            if lane_info:
                lane_db = _REPO / lane_info.get("db", "")
                result["lane_db_available"] = lane_db.exists()
        except Exception:  # noqa: BLE001
            pass
        return result

    def _compute_confidence(
        self, text: str, task_type: str, lane: str,
    ) -> float:
        """Heuristic confidence score (0.0–1.0) for the classification."""
        try:
            conf = 0.3  # base

            # Task-type signal strength
            pats = _TASK_PATTERNS.get(task_type, [])
            hits = sum(1 for p in pats if p.search(text))
            conf += min(hits * 0.15, 0.35)

            # Lane signal strength
            lane_pats = MEEK_SIGNALS.get(lane, [])
            lane_hits = sum(1 for p in lane_pats if p.search(text))
            conf += min(lane_hits * 0.1, 0.25)

            # Length bonus (more text → more signal)
            if len(text) > 100:
                conf += 0.05
            if len(text) > 500:
                conf += 0.05

            return min(round(conf, 2), 1.0)
        except Exception:  # noqa: BLE001
            return 0.3

    def _execute_skill(
        self, skill_name: str, task_description: str, lane: str,
    ) -> Dict[str, Any]:
        """Execute a single skill in the chain.

        Uses MANBEARPIG inference engine as the primary execution backend.
        LLM-backed execution available when ``APEX_LLM_ENABLED=true``.
        """
        result: Dict[str, Any] = {
            "skill": skill_name,
            "status": "ok",
            "model": "manbearpig",
            "output": None,
        }
        try:
            model_cat = self._SKILL_MODEL_NEEDS.get(skill_name, "research")
            result["model"] = self.MODEL_ASSIGNMENTS.get(model_cat, "manbearpig")

            # Try APEX engine first (when LLM enabled)
            if APEX_LLM_ENABLED:
                engine = self._get_integration()
                if engine is not None and hasattr(engine, "route_query"):
                    try:
                        resp = engine.route_query(
                            f"[{skill_name}] {task_description}",
                            task_type=model_cat,
                        )
                        result["output"] = resp
                        return result
                    except Exception as exc:  # noqa: BLE001
                        logger.debug("APEXEngine route_query failed: %s", exc)

            # Fallback: MANBEARPIG inference
            inf = self._get_inference()
            if inf is not None and hasattr(inf, "query"):
                try:
                    resp = inf.query(
                        f"[{skill_name}] lane={lane} | {task_description}"
                    )
                    result["output"] = resp
                    return result
                except Exception as exc:  # noqa: BLE001
                    logger.debug("Inference query failed: %s", exc)

            # Final fallback: stub response
            result["output"] = {
                "text": f"[{skill_name}] Processed (rule-based fallback)",
                "fallback": True,
            }
            return result

        except Exception as exc:  # noqa: BLE001
            logger.error("_execute_skill(%s) failed: %s", skill_name, exc)
            result["status"] = "error"
            result["error"] = str(exc)
            return result

    def _run_quality_gate(self, result: ExecutionResult) -> float:
        """Run quality gate on execution outputs. Returns score 0–100."""
        try:
            gate = self._get_quality_gate()
            texts: List[str] = []
            for out in result.outputs:
                if isinstance(out, dict):
                    raw = out.get("output")
                    if isinstance(raw, str):
                        texts.append(raw)
                    elif isinstance(raw, dict):
                        texts.append(raw.get("text", raw.get("response", "")))

            if not texts:
                return 50.0  # neutral score when no text to check

            combined = "\n".join(t for t in texts if t)
            if hasattr(gate, "validate"):
                qr = gate.validate(combined)
                if isinstance(qr, dict):
                    return float(qr.get("score", qr.get("quality_score", 50.0)))
                return 50.0

            return 50.0
        except Exception as exc:  # noqa: BLE001
            logger.error("Quality gate failed: %s", exc)
            return 0.0


# ═══════════════════════════════════════════════════════════════════════════
# Stub fallbacks (used when real modules can't load)
# ═══════════════════════════════════════════════════════════════════════════
class _StubRouter:
    """Fallback router when ModelRouter isn't available."""

    def route(self, query: str, task_type: str = "research", **kw: Any) -> Dict[str, Any]:
        return {"text": f"[stub-router] {query[:120]}", "status": "fallback", "fallback": True}


class _StubQualityGate:
    """Fallback quality gate when QualityGate isn't available."""

    def validate(self, text: str, **kw: Any) -> Dict[str, Any]:
        return {"score": 50.0, "passed": True, "issues": [], "fallback": True}


# ═══════════════════════════════════════════════════════════════════════════
# CLI entry point
# ═══════════════════════════════════════════════════════════════════════════
def main() -> None:
    """CLI: ``python apex_orchestrator.py "task description"``"""
    # Force UTF-8 stdout
    if sys.stdout.encoding != "utf-8":
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace",
        )

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    orch = APEXOrchestrator()

    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
        dry = "--dry-run" in sys.argv
        if dry:
            task = task.replace("--dry-run", "").strip()

        if "--status" in sys.argv:
            print(json.dumps(orch.system_status(), indent=2, default=str))
        elif "--plan" in sys.argv:
            task = task.replace("--plan", "").strip()
            print(json.dumps(orch.plan(task), indent=2, default=str))
        else:
            result = orch.execute(task, dry_run=dry)
            print(json.dumps(result, indent=2, default=str))
    else:
        print("APEX Orchestrator — Central Brain")
        print(f"  LLM enabled: {APEX_LLM_ENABLED}")
        print(f"  Skill chains: {len(APEXOrchestrator.SKILL_CHAINS)}")
        print(f"  Case lanes: {len(APEXOrchestrator.LANE_MAP)}")
        print("\nUsage:")
        print('  python apex_orchestrator.py "task description"')
        print('  python apex_orchestrator.py --plan "task description"')
        print('  python apex_orchestrator.py "task description" --dry-run')
        print("  python apex_orchestrator.py --status")


if __name__ == "__main__":
    main()
