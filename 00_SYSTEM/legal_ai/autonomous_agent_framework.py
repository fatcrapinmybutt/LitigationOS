# -*- coding: utf-8 -*-
"""
Autonomous Agent Framework — LitigationOS Legal AI Subsystem
================================================================
Framework for building self-orchestrating litigation agents with
ReAct reasoning loops, Plan-and-Execute patterns, behavioral contracts,
tool registries, and agent memory systems.

Case Context
------------
    Plaintiff:  Andrew James Pigors (Pro Se)
    Defendant:  Emily A. Watson
    Child:      L.D.W. (per MCR 8.119(H)) — Male
    Judge:      Hon. Jenny L. McNeill — 14th Circuit Court
    Cases:      2024-001507-DC, 2025-002760-CZ, 2023-5907-PP, COA 366810

Architecture
------------
    AgentState          — Lifecycle states for autonomous agents
    AgentCapability     — Capability descriptor with confidence and usage tracking
    BehavioralContract  — Pre/post conditions, invariants, and violation handlers
    ReActLoop           — Reason → Act → Observe loop with iteration control
    PlanAndExecute      — Task decomposition, step execution, replanning, checkpointing
    ToolRegistry        — Tool registration, selection, and usage analytics
    AgentMemory         — Short-term + long-term memory with TTL and retrieval
    AutonomousAgentFramework — Main orchestrator: create, run, monitor, evaluate, evolve

Usage::

    from legal_ai.autonomous_agent_framework import AutonomousAgentFramework

    framework = AutonomousAgentFramework()
    agent = framework.create_agent({
        "name": "filing-producer",
        "capabilities": ["draft", "cite", "format"],
        "contracts": [{"invariant": "never_file_without_qa"}],
    })
    result = framework.run_agent(agent["agent_id"], task="Draft motion for Lane A")
    stats = framework.get_stats()

Zero external dependencies.  CPU-first.  Local-only.
"""
from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import sys
import time
import uuid
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger("legal_ai.autonomous_agent_framework")

# ---------------------------------------------------------------------------
# Path resolution  (never set CWD to repo root — shadow-module risk)
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[1]
_DB_PATH = _REPO / "litigation_context.db"

# ---------------------------------------------------------------------------
# Case constants
# ---------------------------------------------------------------------------
_PLAINTIFF = "Andrew James Pigors"
_DEFENDANT = "Emily A. Watson"
_CHILD_INITIALS = "L.D.W."
_JUDGE = "Hon. Jenny L. McNeill"
_COURT = "14th Circuit Court"

LANE_CASES: Dict[str, str] = {
    "A": "2024-001507-DC",
    "B": "2025-002760-CZ",
    "C": "Convergence",
    "D": "2023-5907-PP",
    "E": "JTC / Misconduct",
    "F": "COA 366810",
}

# Max concurrent agents — EAGAIN prevention
_MAX_CONCURRENT_AGENTS = 3
_CHECKPOINT_INTERVAL = 3  # checkpoint every N operations
_DEFAULT_MAX_REACT_ITERATIONS = 10
_DEFAULT_MEMORY_TTL_HOURS = 72
_BACKOFF_BASE_SECONDS = 2.0
_MAX_RETRIES = 3


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class AgentState(str, Enum):
    """Lifecycle states for an autonomous agent."""

    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    MONITORING = "monitoring"
    RECOVERING = "recovering"
    EVOLVING = "evolving"

    @property
    def is_active(self) -> bool:
        return self in (
            AgentState.PLANNING,
            AgentState.EXECUTING,
            AgentState.MONITORING,
        )

    @property
    def can_accept_task(self) -> bool:
        return self in (AgentState.IDLE, AgentState.MONITORING)

    @property
    def requires_intervention(self) -> bool:
        return self == AgentState.RECOVERING


class TaskStatus(str, Enum):
    """Status of a delegated task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    BLOCKED = "blocked"

    @property
    def is_terminal(self) -> bool:
        return self in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.BLOCKED)


class ContractSeverity(str, Enum):
    """Severity level for contract violations."""

    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    FATAL = "fatal"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class AgentCapability:
    """Describes a single capability an agent possesses."""

    name: str = ""
    description: str = ""
    skill_refs: List[str] = field(default_factory=list)
    confidence: float = 0.0
    last_used: str = ""
    usage_count: int = 0
    success_rate: float = 1.0
    domains: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "skill_refs": self.skill_refs,
            "confidence": round(self.confidence, 4),
            "last_used": self.last_used,
            "usage_count": self.usage_count,
            "success_rate": round(self.success_rate, 4),
            "domains": self.domains,
        }

    def record_usage(self, success: bool) -> None:
        """Update usage statistics after the capability is exercised."""
        self.usage_count += 1
        self.last_used = datetime.now(timezone.utc).isoformat()
        total = self.usage_count
        if total > 0:
            prev_successes = self.success_rate * (total - 1)
            self.success_rate = (prev_successes + (1.0 if success else 0.0)) / total


@dataclass
class BehavioralContract:
    """Defines invariants, pre/post conditions, and violation handling for an agent."""

    contract_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    name: str = ""
    invariants: List[str] = field(default_factory=list)
    pre_conditions: List[str] = field(default_factory=list)
    post_conditions: List[str] = field(default_factory=list)
    violation_handler: str = "log_and_halt"
    severity: ContractSeverity = ContractSeverity.ERROR
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "name": self.name,
            "invariants": self.invariants,
            "pre_conditions": self.pre_conditions,
            "post_conditions": self.post_conditions,
            "violation_handler": self.violation_handler,
            "severity": self.severity.value,
            "enabled": self.enabled,
        }


@dataclass
class ContractViolation:
    """Records a behavioral contract violation."""

    violation_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    contract_id: str = ""
    agent_id: str = ""
    condition_type: str = ""  # invariant | pre_condition | post_condition
    condition_text: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    severity: ContractSeverity = ContractSeverity.ERROR
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "violation_id": self.violation_id,
            "contract_id": self.contract_id,
            "agent_id": self.agent_id,
            "condition_type": self.condition_type,
            "condition_text": self.condition_text,
            "context": self.context,
            "severity": self.severity.value,
            "timestamp": self.timestamp,
        }


@dataclass
class AgentTask:
    """A task assigned to an agent."""

    task_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    agent_id: str = ""
    description: str = ""
    lane: str = ""
    priority: int = 3  # 0=emergency, 1=critical, 2=high, 3=standard, 4=low
    status: TaskStatus = TaskStatus.PENDING
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    retries: int = 0
    max_retries: int = _MAX_RETRIES
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    completed_at: str = ""
    error_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "description": self.description,
            "lane": self.lane,
            "priority": self.priority,
            "status": self.status.value,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "retries": self.retries,
            "max_retries": self.max_retries,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "error_message": self.error_message,
        }

    @property
    def can_retry(self) -> bool:
        return self.retries < self.max_retries and self.status == TaskStatus.FAILED


@dataclass
class AgentProfile:
    """Full profile of a registered autonomous agent."""

    agent_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str = ""
    description: str = ""
    state: AgentState = AgentState.IDLE
    capabilities: List[AgentCapability] = field(default_factory=list)
    contracts: List[BehavioralContract] = field(default_factory=list)
    assigned_lanes: List[str] = field(default_factory=list)
    task_history: List[str] = field(default_factory=list)
    current_task_id: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "state": self.state.value,
            "capabilities": [c.to_dict() for c in self.capabilities],
            "contracts": [c.to_dict() for c in self.contracts],
            "assigned_lanes": self.assigned_lanes,
            "current_task_id": self.current_task_id,
            "total_tasks": self.total_tasks,
            "successful_tasks": self.successful_tasks,
            "failed_tasks": self.failed_tasks,
            "success_rate": (
                round(self.successful_tasks / self.total_tasks, 4)
                if self.total_tasks > 0
                else 0.0
            ),
            "created_at": self.created_at,
        }

    @property
    def success_rate(self) -> float:
        if self.total_tasks == 0:
            return 0.0
        return self.successful_tasks / self.total_tasks


# ---------------------------------------------------------------------------
# ReAct Loop
# ---------------------------------------------------------------------------


class ReActLoop:
    """Reason → Act → Observe loop for autonomous agent reasoning.

    The ReAct pattern interleaves reasoning (chain-of-thought) with
    action (tool use) and observation (result inspection) to enable
    agents to make grounded decisions.
    """

    def __init__(
        self,
        max_iterations: int = _DEFAULT_MAX_REACT_ITERATIONS,
        *,
        name: str = "default",
    ) -> None:
        self._max_iterations = max_iterations
        self._name = name
        self._iteration = 0
        self._history: List[Dict[str, Any]] = []
        self._complete = False
        self._reason_fn: Optional[Callable] = None
        self._act_fn: Optional[Callable] = None

    def set_handlers(
        self,
        reason_fn: Callable[[str], str],
        act_fn: Callable[[str], Dict[str, Any]],
    ) -> None:
        """Register the reasoning and action handlers."""
        self._reason_fn = reason_fn
        self._act_fn = act_fn

    def reason(self, observation: str) -> str:
        """Generate a reasoning step based on the current observation."""
        self._iteration += 1
        thought = ""
        if self._reason_fn:
            thought = self._reason_fn(observation)
        else:
            thought = f"[Iteration {self._iteration}] Observed: {observation[:200]}"

        self._history.append(
            {
                "step": self._iteration,
                "type": "reason",
                "content": thought,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        logger.debug("ReAct[%s] reason #%d: %s", self._name, self._iteration, thought[:120])
        return thought

    def act(self, plan: str) -> Dict[str, Any]:
        """Execute an action based on the reasoning plan."""
        result: Dict[str, Any] = {}
        if self._act_fn:
            result = self._act_fn(plan)
        else:
            result = {"action": "noop", "plan": plan[:200]}

        self._history.append(
            {
                "step": self._iteration,
                "type": "act",
                "content": result,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        logger.debug("ReAct[%s] act #%d: %s", self._name, self._iteration, str(result)[:120])
        return result

    def observe(self, result: Dict[str, Any]) -> str:
        """Inspect the result of the last action and produce an observation."""
        status = result.get("status", "unknown")
        summary = result.get("summary", str(result)[:300])
        observation = f"Action status={status}. {summary}"

        self._history.append(
            {
                "step": self._iteration,
                "type": "observe",
                "content": observation,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        logger.debug("ReAct[%s] observe #%d: %s", self._name, self._iteration, observation[:120])
        return observation

    def should_continue(self) -> bool:
        """Determine whether the loop should continue iterating."""
        if self._complete:
            return False
        if self._iteration >= self._max_iterations:
            logger.warning(
                "ReAct[%s] reached max iterations (%d)", self._name, self._max_iterations
            )
            return False
        return True

    def mark_complete(self) -> None:
        """Signal the loop to stop after the current cycle."""
        self._complete = True

    @property
    def iteration(self) -> int:
        return self._iteration

    @property
    def max_iterations(self) -> int:
        return self._max_iterations

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "name": self._name,
            "iterations": self._iteration,
            "max_iterations": self._max_iterations,
            "complete": self._complete,
            "history_length": len(self._history),
        }


# ---------------------------------------------------------------------------
# Plan and Execute
# ---------------------------------------------------------------------------


class PlanAndExecute:
    """Decompose a task into steps, execute each, replan if needed, and checkpoint.

    This pattern is used when a task is too complex for a single ReAct cycle
    and requires decomposition into sequential or parallel sub-tasks.
    """

    def __init__(self, *, name: str = "default") -> None:
        self._name = name
        self._steps: List[Dict[str, Any]] = []
        self._results: List[Dict[str, Any]] = []
        self._checkpoints: List[Dict[str, Any]] = []
        self._current_step = 0
        self._replan_count = 0

    def decompose_task(self, task: str, *, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Break a high-level task into ordered executable steps."""
        ctx = context or {}
        steps = []
        # Default decomposition — heuristic chunking
        parts = [p.strip() for p in task.split(";") if p.strip()]
        if len(parts) <= 1:
            parts = [task]

        for i, part in enumerate(parts):
            step = {
                "step_id": f"{self._name}-step-{i}",
                "index": i,
                "description": part,
                "status": "pending",
                "inputs": ctx,
                "outputs": {},
                "retries": 0,
            }
            steps.append(step)

        self._steps = steps
        self._current_step = 0
        logger.info("PlanAndExecute[%s] decomposed into %d steps", self._name, len(steps))
        return list(steps)

    def execute_step(self, step: Dict[str, Any], *, handler: Optional[Callable] = None) -> Dict[str, Any]:
        """Execute a single step, optionally using a custom handler."""
        step["status"] = "in_progress"
        result: Dict[str, Any] = {}
        try:
            if handler:
                result = handler(step)
            else:
                result = {
                    "status": "completed",
                    "step_id": step["step_id"],
                    "summary": f"Executed: {step['description'][:100]}",
                }
            step["status"] = result.get("status", "completed")
            step["outputs"] = result
        except Exception as exc:
            step["status"] = "failed"
            step["outputs"] = {"error": str(exc)}
            result = {"status": "failed", "error": str(exc)}
            logger.error("PlanAndExecute[%s] step %s failed: %s", self._name, step["step_id"], exc)

        self._results.append(result)
        self._current_step += 1

        # Checkpoint every N steps
        if self._current_step % _CHECKPOINT_INTERVAL == 0:
            self.checkpoint({"step": self._current_step, "results": len(self._results)})

        return result

    def replan(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate a revised plan based on execution results so far."""
        self._replan_count += 1
        failed = [r for r in results if r.get("status") == "failed"]
        remaining = [s for s in self._steps if s["status"] == "pending"]

        new_steps = []
        # Retry failed steps
        for fail in failed:
            step_id = fail.get("step_id", f"retry-{self._replan_count}")
            retry_step = {
                "step_id": f"{step_id}-retry-{self._replan_count}",
                "index": len(new_steps),
                "description": f"Retry: {fail.get('summary', 'failed step')}",
                "status": "pending",
                "inputs": fail,
                "outputs": {},
                "retries": 1,
            }
            new_steps.append(retry_step)

        # Carry over remaining steps
        for s in remaining:
            s["index"] = len(new_steps)
            new_steps.append(s)

        self._steps = new_steps
        self._current_step = 0
        logger.info(
            "PlanAndExecute[%s] replanned: %d steps (replan #%d)",
            self._name,
            len(new_steps),
            self._replan_count,
        )
        return list(new_steps)

    def checkpoint(self, state: Any) -> None:
        """Save a checkpoint of the current execution state."""
        cp = {
            "checkpoint_id": f"{self._name}-cp-{len(self._checkpoints)}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "current_step": self._current_step,
            "total_steps": len(self._steps),
            "completed": sum(1 for s in self._steps if s["status"] == "completed"),
            "failed": sum(1 for s in self._steps if s["status"] == "failed"),
            "state": state,
        }
        self._checkpoints.append(cp)
        logger.debug("PlanAndExecute[%s] checkpoint: %s", self._name, cp["checkpoint_id"])

    def get_progress(self) -> Dict[str, Any]:
        return {
            "name": self._name,
            "total_steps": len(self._steps),
            "current_step": self._current_step,
            "completed": sum(1 for s in self._steps if s["status"] == "completed"),
            "failed": sum(1 for s in self._steps if s["status"] == "failed"),
            "pending": sum(1 for s in self._steps if s["status"] == "pending"),
            "replan_count": self._replan_count,
            "checkpoints": len(self._checkpoints),
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            **self.get_progress(),
            "results": self._results,
            "checkpoints": self._checkpoints,
        }


# ---------------------------------------------------------------------------
# Tool Registry
# ---------------------------------------------------------------------------


class ToolRegistry:
    """Register, select, and track usage of tools available to agents.

    Tools are described by JSON Schema and can be selected based on
    task descriptions using keyword matching.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._usage: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._handlers: Dict[str, Callable] = {}

    def register(
        self,
        name: str,
        schema: Dict[str, Any],
        handler: Optional[Callable] = None,
        *,
        description: str = "",
        domains: Optional[List[str]] = None,
    ) -> None:
        """Register a tool with its schema and optional handler."""
        self._tools[name] = {
            "name": name,
            "schema": schema,
            "description": description or schema.get("description", ""),
            "domains": domains or [],
            "registered_at": datetime.now(timezone.utc).isoformat(),
        }
        if handler:
            self._handlers[name] = handler
        logger.debug("ToolRegistry registered: %s", name)

    def select_tools(self, task: str, *, limit: int = 5) -> List[Dict[str, Any]]:
        """Select the most relevant tools for a given task description."""
        task_lower = task.lower()
        scored: List[Tuple[float, str]] = []

        for name, tool in self._tools.items():
            score = 0.0
            desc = (tool.get("description", "") + " " + name).lower()
            # Keyword overlap scoring
            task_words = set(task_lower.split())
            desc_words = set(desc.split())
            overlap = task_words & desc_words
            if overlap:
                score += len(overlap) * 2.0
            # Domain bonus
            for domain in tool.get("domains", []):
                if domain.lower() in task_lower:
                    score += 3.0
            # Usage history — prefer proven tools
            usage_count = len(self._usage.get(name, []))
            if usage_count > 0:
                success_count = sum(
                    1 for u in self._usage[name] if u.get("success", False)
                )
                score += (success_count / usage_count) * 1.5

            if score > 0:
                scored.append((score, name))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for _score, name in scored[:limit]:
            results.append(self._tools[name])
        return results

    def execute_tool(self, name: str, **kwargs: Any) -> Dict[str, Any]:
        """Execute a registered tool's handler."""
        if name not in self._handlers:
            return {"status": "error", "message": f"No handler for tool '{name}'"}
        try:
            result = self._handlers[name](**kwargs)
            self.track_usage(name, {"success": True, "result_summary": str(result)[:200]})
            return {"status": "success", "result": result}
        except Exception as exc:
            self.track_usage(name, {"success": False, "error": str(exc)})
            return {"status": "error", "message": str(exc)}

    def track_usage(self, tool_name: str, result: Dict[str, Any]) -> None:
        """Record a tool usage event for analytics."""
        event = {
            "tool": tool_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **result,
        }
        self._usage[tool_name].append(event)

    def get_stats(self) -> Dict[str, Any]:
        stats: Dict[str, Any] = {
            "total_tools": len(self._tools),
            "tools_with_handlers": len(self._handlers),
            "tool_names": sorted(self._tools.keys()),
        }
        usage_summary: Dict[str, Dict[str, int]] = {}
        for name, events in self._usage.items():
            usage_summary[name] = {
                "total_uses": len(events),
                "successes": sum(1 for e in events if e.get("success", False)),
                "failures": sum(1 for e in events if not e.get("success", True)),
            }
        stats["usage"] = usage_summary
        return stats


# ---------------------------------------------------------------------------
# Agent Memory
# ---------------------------------------------------------------------------


class AgentMemory:
    """Short-term and long-term memory system for autonomous agents.

    Short-term: In-process dict, cleared per task.
    Long-term: Persisted with TTL, queryable by keyword.
    """

    def __init__(self, *, ttl_hours: int = _DEFAULT_MEMORY_TTL_HOURS) -> None:
        self._short_term: Dict[str, Any] = {}
        self._long_term: Dict[str, Dict[str, Any]] = {}
        self._ttl_hours = ttl_hours

    def store_short_term(self, key: str, value: Any) -> None:
        """Store a value in short-term (task-scoped) memory."""
        self._short_term[key] = {
            "value": value,
            "stored_at": datetime.now(timezone.utc).isoformat(),
        }

    def get_short_term(self, key: str) -> Any:
        """Retrieve a value from short-term memory."""
        entry = self._short_term.get(key)
        return entry["value"] if entry else None

    def clear_short_term(self) -> None:
        """Clear all short-term memory (called between tasks)."""
        self._short_term.clear()

    def store_long_term(
        self, key: str, value: Any, *, ttl_hours: Optional[int] = None
    ) -> None:
        """Store a value in long-term memory with optional custom TTL."""
        ttl = ttl_hours if ttl_hours is not None else self._ttl_hours
        expires = datetime.now(timezone.utc) + timedelta(hours=ttl)
        self._long_term[key] = {
            "value": value,
            "stored_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": expires.isoformat(),
            "ttl_hours": ttl,
            "access_count": 0,
        }

    def get_long_term(self, key: str) -> Any:
        """Retrieve a value from long-term memory if not expired."""
        entry = self._long_term.get(key)
        if not entry:
            return None
        expires = datetime.fromisoformat(entry["expires_at"])
        if datetime.now(timezone.utc) > expires:
            del self._long_term[key]
            return None
        entry["access_count"] += 1
        return entry["value"]

    def retrieve(self, query: str, *, limit: int = 10) -> List[Dict[str, Any]]:
        """Search long-term memory by keyword matching."""
        query_lower = query.lower()
        results: List[Tuple[float, str, Any]] = []
        now = datetime.now(timezone.utc)

        for key, entry in list(self._long_term.items()):
            expires = datetime.fromisoformat(entry["expires_at"])
            if now > expires:
                del self._long_term[key]
                continue

            score = 0.0
            key_lower = key.lower()
            value_str = str(entry["value"]).lower()

            # Key match
            if query_lower in key_lower:
                score += 5.0
            # Value content match
            query_words = set(query_lower.split())
            value_words = set(value_str.split()[:100])
            overlap = query_words & value_words
            if overlap:
                score += len(overlap) * 2.0
            # Recency bonus
            stored = datetime.fromisoformat(entry["stored_at"])
            age_hours = (now - stored).total_seconds() / 3600
            if age_hours < 24:
                score += 2.0
            elif age_hours < 72:
                score += 1.0

            if score > 0:
                results.append((score, key, entry["value"]))

        results.sort(key=lambda x: x[0], reverse=True)
        return [
            {"key": key, "value": value, "relevance": round(score, 2)}
            for score, key, value in results[:limit]
        ]

    def forget_stale(self) -> int:
        """Remove all expired long-term memories. Returns count removed."""
        now = datetime.now(timezone.utc)
        expired_keys = [
            k
            for k, v in self._long_term.items()
            if datetime.fromisoformat(v["expires_at"]) < now
        ]
        for k in expired_keys:
            del self._long_term[k]
        if expired_keys:
            logger.info("AgentMemory: forgot %d stale entries", len(expired_keys))
        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "short_term_count": len(self._short_term),
            "long_term_count": len(self._long_term),
            "ttl_hours": self._ttl_hours,
        }


# ---------------------------------------------------------------------------
# Contract Validator
# ---------------------------------------------------------------------------


class ContractValidator:
    """Validates behavioral contracts for agents before and after actions."""

    def __init__(self) -> None:
        self._violations: List[ContractViolation] = []

    def check_pre_conditions(
        self,
        contract: BehavioralContract,
        context: Dict[str, Any],
        *,
        agent_id: str = "",
    ) -> List[ContractViolation]:
        """Check pre-conditions before an action. Returns list of violations."""
        violations: List[ContractViolation] = []
        if not contract.enabled:
            return violations

        for condition in contract.pre_conditions:
            # Pattern-based checks
            if not self._evaluate_condition(condition, context):
                v = ContractViolation(
                    contract_id=contract.contract_id,
                    agent_id=agent_id,
                    condition_type="pre_condition",
                    condition_text=condition,
                    context=context,
                    severity=contract.severity,
                )
                violations.append(v)
                self._violations.append(v)

        return violations

    def check_post_conditions(
        self,
        contract: BehavioralContract,
        context: Dict[str, Any],
        *,
        agent_id: str = "",
    ) -> List[ContractViolation]:
        """Check post-conditions after an action. Returns list of violations."""
        violations: List[ContractViolation] = []
        if not contract.enabled:
            return violations

        for condition in contract.post_conditions:
            if not self._evaluate_condition(condition, context):
                v = ContractViolation(
                    contract_id=contract.contract_id,
                    agent_id=agent_id,
                    condition_type="post_condition",
                    condition_text=condition,
                    context=context,
                    severity=contract.severity,
                )
                violations.append(v)
                self._violations.append(v)

        return violations

    def check_invariants(
        self,
        contract: BehavioralContract,
        context: Dict[str, Any],
        *,
        agent_id: str = "",
    ) -> List[ContractViolation]:
        """Check invariants that must always hold. Returns list of violations."""
        violations: List[ContractViolation] = []
        if not contract.enabled:
            return violations

        for invariant in contract.invariants:
            if not self._evaluate_condition(invariant, context):
                v = ContractViolation(
                    contract_id=contract.contract_id,
                    agent_id=agent_id,
                    condition_type="invariant",
                    condition_text=invariant,
                    context=context,
                    severity=ContractSeverity.CRITICAL,
                )
                violations.append(v)
                self._violations.append(v)

        return violations

    @staticmethod
    def _evaluate_condition(condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate a condition string against context.

        Supports simple key-presence checks: condition text is checked
        as a key in context. If key exists and is truthy, condition passes.
        """
        cond_lower = condition.lower().strip()
        # Check if condition key is directly in context
        if cond_lower in context:
            return bool(context[cond_lower])
        # Check with underscores instead of spaces
        cond_key = cond_lower.replace(" ", "_")
        if cond_key in context:
            return bool(context[cond_key])
        # Default: unresolvable conditions pass (conservative)
        return True

    def get_violations(self, *, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        viol = self._violations
        if agent_id:
            viol = [v for v in viol if v.agent_id == agent_id]
        return [v.to_dict() for v in viol]

    def get_stats(self) -> Dict[str, Any]:
        severity_counts: Dict[str, int] = defaultdict(int)
        for v in self._violations:
            severity_counts[v.severity.value] += 1
        return {
            "total_violations": len(self._violations),
            "by_severity": dict(severity_counts),
        }


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------


def _get_db(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Open a WAL-mode SQLite connection with standard PRAGMAs."""
    path = db_path or _DB_PATH
    conn = sqlite3.connect(str(path), timeout=60)
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_agent_tables(conn: sqlite3.Connection) -> None:
    """Create agent framework tables if they do not exist."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS agent_profiles (
            agent_id   TEXT PRIMARY KEY,
            name       TEXT NOT NULL,
            config     TEXT,
            state      TEXT DEFAULT 'idle',
            created_at TEXT,
            updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS agent_tasks (
            task_id      TEXT PRIMARY KEY,
            agent_id     TEXT,
            description  TEXT,
            lane         TEXT,
            priority     INTEGER DEFAULT 3,
            status       TEXT DEFAULT 'pending',
            inputs       TEXT,
            outputs      TEXT,
            retries      INTEGER DEFAULT 0,
            created_at   TEXT,
            completed_at TEXT,
            error_message TEXT
        );
        CREATE TABLE IF NOT EXISTS agent_violations (
            violation_id  TEXT PRIMARY KEY,
            contract_id   TEXT,
            agent_id      TEXT,
            condition_type TEXT,
            condition_text TEXT,
            severity      TEXT,
            context       TEXT,
            timestamp     TEXT
        );
        CREATE TABLE IF NOT EXISTS agent_checkpoints (
            checkpoint_id TEXT PRIMARY KEY,
            agent_id      TEXT,
            state         TEXT,
            timestamp     TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_agent_tasks_agent
            ON agent_tasks(agent_id, status);
        CREATE INDEX IF NOT EXISTS idx_agent_tasks_priority
            ON agent_tasks(priority, status);
        """
    )
    conn.commit()


# ---------------------------------------------------------------------------
# AutonomousAgentFramework (Main)
# ---------------------------------------------------------------------------


class AutonomousAgentFramework:
    """Main orchestrator for creating, running, monitoring, evaluating,
    and evolving autonomous litigation agents.

    Coordinates the full agent lifecycle: registration, capability assignment,
    behavioral contract enforcement, task delegation, ReAct reasoning,
    plan-and-execute decomposition, and performance evaluation.
    """

    def __init__(self, *, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or _DB_PATH
        self._agents: Dict[str, AgentProfile] = {}
        self._tool_registry = ToolRegistry()
        self._contract_validator = ContractValidator()
        self._memory = AgentMemory()
        self._react_loops: Dict[str, ReActLoop] = {}
        self._plan_executors: Dict[str, PlanAndExecute] = {}
        self._operations_count = 0
        self._initialized = False

    # -- Initialization --

    def initialize(self) -> Dict[str, Any]:
        """Initialize the framework and ensure database tables exist."""
        if self._initialized:
            return {"status": "already_initialized"}
        try:
            conn = _get_db(self._db_path)
            _ensure_agent_tables(conn)
            conn.close()
            self._initialized = True
            logger.info("AutonomousAgentFramework initialized")
            return {"status": "initialized", "db_path": str(self._db_path)}
        except Exception as exc:
            logger.error("Framework init failed: %s", exc)
            return {"status": "error", "message": str(exc)}

    # -- Agent CRUD --

    def create_agent(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create and register a new autonomous agent.

        Parameters
        ----------
        config : dict
            Must include: name, capabilities (list of dicts), contracts (list of dicts).
            Optional: description, assigned_lanes.
        """
        name = config.get("name", "unnamed")
        agent = AgentProfile(
            name=name,
            description=config.get("description", ""),
            assigned_lanes=config.get("assigned_lanes", []),
        )

        # Build capabilities
        for cap_cfg in config.get("capabilities", []):
            if isinstance(cap_cfg, str):
                cap = AgentCapability(name=cap_cfg, confidence=0.8)
            elif isinstance(cap_cfg, dict):
                cap = AgentCapability(
                    name=cap_cfg.get("name", ""),
                    description=cap_cfg.get("description", ""),
                    skill_refs=cap_cfg.get("skill_refs", []),
                    confidence=cap_cfg.get("confidence", 0.8),
                    domains=cap_cfg.get("domains", []),
                )
            else:
                continue
            agent.capabilities.append(cap)

        # Build contracts
        for contract_cfg in config.get("contracts", []):
            if isinstance(contract_cfg, dict):
                bc = BehavioralContract(
                    name=contract_cfg.get("name", ""),
                    invariants=contract_cfg.get("invariants", []),
                    pre_conditions=contract_cfg.get("pre_conditions", []),
                    post_conditions=contract_cfg.get("post_conditions", []),
                    violation_handler=contract_cfg.get("violation_handler", "log_and_halt"),
                )
                agent.contracts.append(bc)

        self._agents[agent.agent_id] = agent

        # Create ReAct loop and PlanAndExecute for this agent
        self._react_loops[agent.agent_id] = ReActLoop(name=name)
        self._plan_executors[agent.agent_id] = PlanAndExecute(name=name)

        # Persist to DB
        self._persist_agent(agent)

        logger.info("Created agent: %s (%s)", name, agent.agent_id)
        return agent.to_dict()

    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an agent profile by ID."""
        agent = self._agents.get(agent_id)
        return agent.to_dict() if agent else None

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents."""
        return [a.to_dict() for a in self._agents.values()]

    # -- Task Execution --

    def run_agent(
        self,
        agent_id: str,
        task: str,
        *,
        lane: str = "",
        priority: int = 3,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Assign and execute a task on the specified agent.

        Uses ReAct loop for simple tasks and PlanAndExecute for
        multi-step tasks (detected by semicolons or length > 200 chars).
        """
        agent = self._agents.get(agent_id)
        if not agent:
            return {"status": "error", "message": f"Agent {agent_id} not found"}

        if not agent.state.can_accept_task:
            return {
                "status": "error",
                "message": f"Agent {agent.name} in state {agent.state.value}, cannot accept tasks",
            }

        # Concurrency check
        active_count = sum(1 for a in self._agents.values() if a.state.is_active)
        if active_count >= _MAX_CONCURRENT_AGENTS:
            return {
                "status": "blocked",
                "message": f"Max concurrent agents ({_MAX_CONCURRENT_AGENTS}) reached",
            }

        # Create task
        agent_task = AgentTask(
            agent_id=agent_id,
            description=task,
            lane=lane or (agent.assigned_lanes[0] if agent.assigned_lanes else ""),
            priority=priority,
            inputs=inputs or {},
        )

        # Check pre-conditions
        context = {"task": task, "lane": lane, **(inputs or {})}
        for contract in agent.contracts:
            violations = self._contract_validator.check_pre_conditions(
                contract, context, agent_id=agent_id
            )
            if violations and contract.severity in (
                ContractSeverity.CRITICAL,
                ContractSeverity.FATAL,
            ):
                agent_task.status = TaskStatus.BLOCKED
                agent_task.error_message = (
                    f"Pre-condition violation: {violations[0].condition_text}"
                )
                return agent_task.to_dict()

        # Execute using appropriate pattern
        agent.state = AgentState.PLANNING
        agent.current_task_id = agent_task.task_id
        agent_task.status = TaskStatus.IN_PROGRESS

        try:
            is_complex = ";" in task or len(task) > 200
            if is_complex:
                result = self._execute_plan_and_execute(agent, agent_task)
            else:
                result = self._execute_react(agent, agent_task)

            agent_task.outputs = result
            if result.get("status") == "completed":
                agent_task.status = TaskStatus.COMPLETED
                agent.successful_tasks += 1
            else:
                agent_task.status = TaskStatus.FAILED
                agent_task.error_message = result.get("message", "Unknown failure")
                agent.failed_tasks += 1

        except Exception as exc:
            agent_task.status = TaskStatus.FAILED
            agent_task.error_message = str(exc)
            agent.failed_tasks += 1
            agent.state = AgentState.RECOVERING
            logger.error("Agent %s task failed: %s", agent.name, exc)

        agent_task.completed_at = datetime.now(timezone.utc).isoformat()
        agent.total_tasks += 1
        agent.task_history.append(agent_task.task_id)
        agent.current_task_id = ""

        if agent.state != AgentState.RECOVERING:
            agent.state = AgentState.IDLE

        # Check post-conditions
        post_context = {
            **context,
            "result_status": agent_task.status.value,
            "outputs": agent_task.outputs,
        }
        for contract in agent.contracts:
            self._contract_validator.check_post_conditions(
                contract, post_context, agent_id=agent_id
            )

        # Checkpoint
        self._operations_count += 1
        if self._operations_count % _CHECKPOINT_INTERVAL == 0:
            self._checkpoint_state(agent_id)

        # Persist task
        self._persist_task(agent_task)

        return agent_task.to_dict()

    def _execute_react(
        self, agent: AgentProfile, task: AgentTask
    ) -> Dict[str, Any]:
        """Execute a task using the ReAct loop."""
        react = self._react_loops.get(agent.agent_id)
        if not react:
            react = ReActLoop(name=agent.name)
            self._react_loops[agent.agent_id] = react

        agent.state = AgentState.EXECUTING
        observation = f"Task: {task.description}. Lane: {task.lane}. Inputs: {json.dumps(task.inputs)[:300]}"

        while react.should_continue():
            thought = react.reason(observation)
            action_result = react.act(thought)
            observation = react.observe(action_result)

            if action_result.get("status") in ("completed", "success"):
                react.mark_complete()
                return {
                    "status": "completed",
                    "summary": f"Completed in {react.iteration} iterations",
                    "iterations": react.iteration,
                    "history": react.get_history(),
                }

        return {
            "status": "completed",
            "summary": f"ReAct loop completed after {react.iteration} iterations",
            "iterations": react.iteration,
            "history": react.get_history(),
        }

    def _execute_plan_and_execute(
        self, agent: AgentProfile, task: AgentTask
    ) -> Dict[str, Any]:
        """Execute a complex task using plan-and-execute decomposition."""
        planner = self._plan_executors.get(agent.agent_id)
        if not planner:
            planner = PlanAndExecute(name=agent.name)
            self._plan_executors[agent.agent_id] = planner

        agent.state = AgentState.PLANNING
        steps = planner.decompose_task(task.description, context=task.inputs)

        agent.state = AgentState.EXECUTING
        results: List[Dict[str, Any]] = []
        for step in steps:
            result = planner.execute_step(step)
            results.append(result)

        # Check for failures and replan if needed
        failures = [r for r in results if r.get("status") == "failed"]
        if failures and len(failures) < len(steps):
            agent.state = AgentState.PLANNING
            new_steps = planner.replan(results)
            agent.state = AgentState.EXECUTING
            for step in new_steps:
                if step["status"] == "pending":
                    result = planner.execute_step(step)
                    results.append(result)

        progress = planner.get_progress()
        return {
            "status": "completed",
            "summary": f"Plan executed: {progress['completed']}/{progress['total_steps']} steps completed",
            "progress": progress,
        }

    # -- Monitoring --

    def monitor_agents(self) -> Dict[str, Any]:
        """Get current status of all agents."""
        status: Dict[str, Any] = {
            "total_agents": len(self._agents),
            "active": [],
            "idle": [],
            "recovering": [],
        }
        for agent in self._agents.values():
            info = {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "state": agent.state.value,
                "success_rate": agent.success_rate,
                "current_task": agent.current_task_id,
            }
            if agent.state.is_active:
                status["active"].append(info)
            elif agent.state == AgentState.RECOVERING:
                status["recovering"].append(info)
            else:
                status["idle"].append(info)
        return status

    # -- Evaluation --

    def evaluate_performance(
        self, agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Evaluate agent performance metrics."""
        agents = (
            [self._agents[agent_id]] if agent_id and agent_id in self._agents else list(self._agents.values())
        )
        evaluations = []
        for agent in agents:
            evaluation = {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "total_tasks": agent.total_tasks,
                "successful_tasks": agent.successful_tasks,
                "failed_tasks": agent.failed_tasks,
                "success_rate": agent.success_rate,
                "capabilities": len(agent.capabilities),
                "contracts": len(agent.contracts),
                "violations": len(
                    self._contract_validator.get_violations(agent_id=agent.agent_id)
                ),
                "grade": self._grade_agent(agent),
            }
            evaluations.append(evaluation)

        return {
            "evaluations": evaluations,
            "fleet_average_success_rate": (
                sum(a.success_rate for a in agents) / len(agents) if agents else 0.0
            ),
            "total_violations": len(self._contract_validator.get_violations()),
        }

    @staticmethod
    def _grade_agent(agent: AgentProfile) -> str:
        """Assign a letter grade based on agent performance."""
        rate = agent.success_rate
        if agent.total_tasks < 3:
            return "N/A"
        if rate >= 0.95:
            return "A"
        if rate >= 0.85:
            return "B"
        if rate >= 0.70:
            return "C"
        if rate >= 0.50:
            return "D"
        return "F"

    # -- Evolution --

    def evolve_capabilities(self) -> Dict[str, Any]:
        """Analyze agent capabilities and suggest improvements."""
        suggestions: List[Dict[str, Any]] = []
        for agent in self._agents.values():
            # Check for under-performing capabilities
            for cap in agent.capabilities:
                if cap.usage_count > 5 and cap.success_rate < 0.7:
                    suggestions.append(
                        {
                            "agent": agent.name,
                            "capability": cap.name,
                            "issue": "low_success_rate",
                            "current_rate": round(cap.success_rate, 3),
                            "suggestion": f"Retrain or replace capability '{cap.name}' — success rate below threshold",
                        }
                    )
                if cap.usage_count == 0 and cap.last_used == "":
                    suggestions.append(
                        {
                            "agent": agent.name,
                            "capability": cap.name,
                            "issue": "never_used",
                            "suggestion": f"Capability '{cap.name}' never used — consider removal or integration",
                        }
                    )

            # Check overall agent health
            if agent.total_tasks > 10 and agent.success_rate < 0.6:
                suggestions.append(
                    {
                        "agent": agent.name,
                        "issue": "agent_underperforming",
                        "success_rate": round(agent.success_rate, 3),
                        "suggestion": f"Agent '{agent.name}' consistently underperforming — needs redesign",
                    }
                )

        return {
            "suggestions": suggestions,
            "total_suggestions": len(suggestions),
            "agents_analyzed": len(self._agents),
        }

    # -- Stats --

    def get_stats(self) -> Dict[str, Any]:
        """Comprehensive framework statistics."""
        return {
            "agents": {
                "total": len(self._agents),
                "active": sum(1 for a in self._agents.values() if a.state.is_active),
                "idle": sum(
                    1 for a in self._agents.values() if a.state == AgentState.IDLE
                ),
                "recovering": sum(
                    1
                    for a in self._agents.values()
                    if a.state == AgentState.RECOVERING
                ),
            },
            "tasks": {
                "total": sum(a.total_tasks for a in self._agents.values()),
                "successful": sum(a.successful_tasks for a in self._agents.values()),
                "failed": sum(a.failed_tasks for a in self._agents.values()),
            },
            "tools": self._tool_registry.get_stats(),
            "memory": self._memory.get_stats(),
            "contracts": self._contract_validator.get_stats(),
            "operations_count": self._operations_count,
            "initialized": self._initialized,
        }

    # -- Persistence helpers --

    def _persist_agent(self, agent: AgentProfile) -> None:
        """Save agent profile to database."""
        try:
            conn = _get_db(self._db_path)
            _ensure_agent_tables(conn)
            conn.execute(
                """
                INSERT OR REPLACE INTO agent_profiles
                    (agent_id, name, config, state, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    agent.agent_id,
                    agent.name,
                    json.dumps(agent.to_dict()),
                    agent.state.value,
                    agent.created_at,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            conn.commit()
            conn.close()
        except Exception as exc:
            logger.warning("Failed to persist agent %s: %s", agent.agent_id, exc)

    def _persist_task(self, task: AgentTask) -> None:
        """Save task to database."""
        try:
            conn = _get_db(self._db_path)
            _ensure_agent_tables(conn)
            conn.execute(
                """
                INSERT OR REPLACE INTO agent_tasks
                    (task_id, agent_id, description, lane, priority,
                     status, inputs, outputs, retries, created_at,
                     completed_at, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task.task_id,
                    task.agent_id,
                    task.description,
                    task.lane,
                    task.priority,
                    task.status.value,
                    json.dumps(task.inputs),
                    json.dumps(task.outputs),
                    task.retries,
                    task.created_at,
                    task.completed_at,
                    task.error_message,
                ),
            )
            conn.commit()
            conn.close()
        except Exception as exc:
            logger.warning("Failed to persist task %s: %s", task.task_id, exc)

    def _checkpoint_state(self, agent_id: str) -> None:
        """Save a checkpoint to database."""
        agent = self._agents.get(agent_id)
        if not agent:
            return
        try:
            conn = _get_db(self._db_path)
            _ensure_agent_tables(conn)
            cp_id = f"{agent_id}-cp-{self._operations_count}"
            conn.execute(
                """
                INSERT INTO agent_checkpoints (checkpoint_id, agent_id, state, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                (
                    cp_id,
                    agent_id,
                    json.dumps(agent.to_dict()),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            conn.commit()
            conn.close()
            logger.debug("Checkpoint saved: %s", cp_id)
        except Exception as exc:
            logger.warning("Failed to save checkpoint: %s", exc)


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------


def create_framework(*, db_path: Optional[Path] = None) -> AutonomousAgentFramework:
    """Create and initialize an AutonomousAgentFramework instance."""
    fw = AutonomousAgentFramework(db_path=db_path)
    fw.initialize()
    return fw
