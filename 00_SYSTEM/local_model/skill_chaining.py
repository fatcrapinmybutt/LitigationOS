"""
APEX Skill Chaining — Executes multi-step skill workflows.

Each skill in chain receives output of previous as input.
Supports: sequential, parallel-then-merge, conditional branching.
"""
from __future__ import annotations

import json
import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("apex.skill_chaining")

APEX_LLM_ENABLED: bool = os.environ.get("APEX_LLM_ENABLED", "false").lower() == "true"

_MODULE_DIR = Path(__file__).parent

# ---------------------------------------------------------------------------
# Step definitions
# ---------------------------------------------------------------------------

STEP_TYPE_SEQUENTIAL = "sequential"
STEP_TYPE_PARALLEL = "parallel"
STEP_TYPE_CONDITIONAL = "conditional"


class _StepDef:
    """Internal representation of a chain step."""
    __slots__ = ("step_type", "skill", "config", "skills", "condition",
                 "if_true", "if_false")

    def __init__(self, step_type: str, **kwargs: Any) -> None:
        self.step_type = step_type
        self.skill: str = kwargs.get("skill", "")
        self.config: Dict[str, Any] = kwargs.get("config", {})
        self.skills: List[str] = kwargs.get("skills", [])
        self.condition: Optional[Callable[..., bool]] = kwargs.get("condition")
        self.if_true: str = kwargs.get("if_true", "")
        self.if_false: str = kwargs.get("if_false", "")


# ---------------------------------------------------------------------------
# Skill execution adapter
# ---------------------------------------------------------------------------

def _load_skill_loader() -> Any:
    """Lazy-load SkillLoader to avoid import cycles."""
    try:
        from .skill_loader import SkillLoader
        return SkillLoader()
    except Exception:
        try:
            import importlib
            return importlib.import_module("skill_loader").SkillLoader()
        except Exception:
            return None


def _execute_skill(skill_name: str, context: dict, config: dict) -> Dict[str, Any]:
    """Execute a single skill and return its result.

    This is a routing stub — actual skill execution is delegated to the
    SkillLoader / agent framework. The stub captures metadata and passes
    through context enrichment.
    """
    result: Dict[str, Any] = {
        "skill": skill_name,
        "status": "executed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:
        loader = _load_skill_loader()
        if loader is None:
            result["status"] = "loader_unavailable"
            return result

        meta = loader.get_skill(skill_name)
        if meta.get("error"):
            result["status"] = "not_found"
            result["error"] = meta["error"]
            return result

        result["skill_meta"] = {
            "name": meta.get("name", skill_name),
            "description": meta.get("description", "")[:200],
            "path": meta.get("path", ""),
        }
        # Pass context and config into the result for downstream consumption
        result["input_context_keys"] = list(context.keys())
        result["config"] = config
        result["status"] = "routed"
        return result

    except Exception as exc:
        logger.warning("Skill execution failed for '%s': %s", skill_name, exc)
        result["status"] = "error"
        result["error"] = str(exc)
        return result


# ---------------------------------------------------------------------------
# SkillChain
# ---------------------------------------------------------------------------

class SkillChain:
    """Executes a defined chain of skills sequentially, in parallel, or
    conditionally.
    """

    def __init__(self, chain_def: List[Dict[str, Any]]) -> None:
        """Define a chain from a list of step dicts.

        Each dict: ``{"skill": "name", "config": {...}}``
        or ``{"parallel": ["skill1", "skill2"]}``
        or ``{"condition": <callable>, "if_true": "skill_a", "if_false": "skill_b"}``.
        """
        self._steps: List[_StepDef] = []
        self._trace: List[Dict[str, Any]] = []
        for step in chain_def:
            self._steps.append(self._parse_step(step))

    @staticmethod
    def _parse_step(step: dict) -> _StepDef:
        if "parallel" in step:
            return _StepDef(STEP_TYPE_PARALLEL, skills=step["parallel"],
                            config=step.get("config", {}))
        if "condition" in step:
            return _StepDef(STEP_TYPE_CONDITIONAL,
                            condition=step.get("condition"),
                            if_true=step.get("if_true", ""),
                            if_false=step.get("if_false", ""),
                            config=step.get("config", {}))
        return _StepDef(STEP_TYPE_SEQUENTIAL,
                        skill=step.get("skill", ""),
                        config=step.get("config", {}))

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def execute(self, initial_context: dict) -> dict:
        """Execute chain. Returns ``{result: dict, trace: list, status: str}``."""
        context = dict(initial_context)
        self._trace = []
        status = "complete"

        for i, step in enumerate(self._steps):
            try:
                step_result = self._execute_step(step, context)
                self._trace.append({
                    "step": i,
                    "type": step.step_type,
                    "result": step_result,
                })
                # Merge step result into context for next step
                if isinstance(step_result, dict):
                    context[f"step_{i}"] = step_result
                    if step_result.get("status") == "error":
                        status = "partial"
            except Exception as exc:
                logger.warning("Chain step %d failed: %s", i, exc)
                self._trace.append({
                    "step": i, "type": step.step_type,
                    "result": {"status": "error", "error": str(exc)},
                })
                status = "partial"

        if all(
            t.get("result", {}).get("status") == "error"
            for t in self._trace
        ) and self._trace:
            status = "failed"

        return {
            "result": context,
            "trace": self._trace,
            "status": status,
            "steps_executed": len(self._trace),
        }

    def _execute_step(self, step: _StepDef, context: dict) -> dict:
        """Execute one step, return enriched context."""
        if step.step_type == STEP_TYPE_SEQUENTIAL:
            return _execute_skill(step.skill, context, step.config)

        if step.step_type == STEP_TYPE_PARALLEL:
            return self._execute_parallel(step.skills, context, step.config)

        if step.step_type == STEP_TYPE_CONDITIONAL:
            return self._execute_conditional(step, context)

        return {"status": "unknown_step_type", "type": step.step_type}

    def _execute_parallel(self, skills: List[str], context: dict,
                          config: dict) -> dict:
        """Execute skills in parallel and merge results."""
        results: Dict[str, Any] = {}
        max_workers = min(len(skills), 3)  # Respect concurrency limits

        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(_execute_skill, s, context, config): s
                    for s in skills
                }
                for future in as_completed(futures, timeout=120):
                    skill_name = futures[future]
                    try:
                        results[skill_name] = future.result()
                    except Exception as exc:
                        results[skill_name] = {"status": "error", "error": str(exc)}
        except Exception as exc:
            logger.warning("Parallel execution failed: %s", exc)
            return {"status": "error", "error": str(exc), "partial": results}

        return {"status": "complete", "parallel_results": results}

    def _execute_conditional(self, step: _StepDef, context: dict) -> dict:
        """Evaluate condition and execute the appropriate branch."""
        try:
            if step.condition is not None and callable(step.condition):
                branch = step.condition(context)
            else:
                branch = True  # default to if_true

            skill = step.if_true if branch else step.if_false
            if not skill:
                return {"status": "skipped", "branch": branch, "reason": "no skill for branch"}

            result = _execute_skill(skill, context, step.config)
            result["branch_taken"] = "if_true" if branch else "if_false"
            return result
        except Exception as exc:
            logger.warning("Conditional execution failed: %s", exc)
            return {"status": "error", "error": str(exc)}


# ---------------------------------------------------------------------------
# ChainBuilder (fluent API)
# ---------------------------------------------------------------------------

class ChainBuilder:
    """Fluent builder for skill chains."""

    def __init__(self) -> None:
        self._steps: List[Dict[str, Any]] = []

    def add_step(self, skill: str, config: Optional[dict] = None) -> "ChainBuilder":
        """Add a sequential skill step."""
        self._steps.append({"skill": skill, "config": config or {}})
        return self

    def add_parallel(self, skills: List[str], config: Optional[dict] = None) -> "ChainBuilder":
        """Add a parallel execution step (skills run concurrently)."""
        self._steps.append({"parallel": skills, "config": config or {}})
        return self

    def add_conditional(self, condition: Callable[..., bool],
                        if_true: str, if_false: str,
                        config: Optional[dict] = None) -> "ChainBuilder":
        """Add a conditional branching step."""
        self._steps.append({
            "condition": condition,
            "if_true": if_true,
            "if_false": if_false,
            "config": config or {},
        })
        return self

    def build(self) -> SkillChain:
        """Build and return the SkillChain."""
        return SkillChain(self._steps)

    def __len__(self) -> int:
        return len(self._steps)

    def __repr__(self) -> str:
        return f"ChainBuilder(steps={len(self._steps)})"


# ---------------------------------------------------------------------------
# Pre-built chains
# ---------------------------------------------------------------------------

def brief_chain() -> SkillChain:
    """Pre-built chain for brief drafting."""
    return (
        ChainBuilder()
        .add_step("litigation-claim-researcher")
        .add_step("litigation-cause-of-action-library")
        .add_step("litigation-brief-writer")
        .add_step("litigation-red-team")
        .build()
    )


def complaint_chain() -> SkillChain:
    """Pre-built chain for complaint drafting."""
    return (
        ChainBuilder()
        .add_step("litigation-claim-researcher")
        .add_step("litigation-cause-of-action-library")
        .add_step("litigation-lawsuit-forge")
        .add_step("litigation-complaint-drafter")
        .build()
    )


def filing_validation_chain() -> SkillChain:
    """Pre-built chain for filing validation."""
    return (
        ChainBuilder()
        .add_step("litigation-authority-validator")
        .add_parallel([
            "litigation-filing-architect",
            "litigation-pro-se-guardian",
        ])
        .build()
    )
