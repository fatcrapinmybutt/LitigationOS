# -*- coding: utf-8 -*-
"""
Workflow Automation Engine — LitigationOS Legal AI Subsystem
================================================================
Automated litigation workflow engine with batch processing, scheduling,
conditional routing, retry logic, and pipeline orchestration for
end-to-end filing and evidence workflows.

Case Context
------------
    Plaintiff:  Andrew James Pigors (Pro Se)
    Defendant:  Emily A. Watson
    Child:      L.D.W. (per MCR 8.119(H)) — Male
    Judge:      Hon. Jenny L. McNeill — 14th Circuit Court
    Cases:      2024-001507-DC, 2025-002760-CZ, 2023-5907-PP, COA 366810

Architecture
------------
    WorkflowStatus      — Lifecycle states for workflows (queued → running → completed)
    PipelineStage       — Stage descriptor with handler, inputs, outputs, timeouts
    WorkflowDefinition  — Named workflow with ordered stages, triggers, schedules
    BatchProcessor      — Bulk item processing with progress tracking and retry
    ConditionalRouter   — Route items to handlers based on condition evaluation
    ScheduleManager     — Cron-like scheduling with execution history
    RetryEngine         — Retry with exponential backoff and failure analytics
    WorkflowAutomationEngine — Main orchestrator: define, execute, monitor, batch

Usage::

    from legal_ai.workflow_automation_engine import WorkflowAutomationEngine

    engine = WorkflowAutomationEngine()
    engine.define_workflow({
        "name": "filing_pipeline",
        "stages": [
            {"name": "gather_evidence", "handler": "evidence_harvester"},
            {"name": "draft_motion", "handler": "brief_writer"},
            {"name": "qa_check", "handler": "quality_gate"},
        ],
    })
    result = engine.execute_workflow("filing_pipeline", context={"lane": "A"})
    stats = engine.get_stats()

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

logger = logging.getLogger("legal_ai.workflow_automation_engine")

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

# Defaults
_DEFAULT_STAGE_TIMEOUT = 300  # seconds
_DEFAULT_MAX_RETRIES = 3
_DEFAULT_BACKOFF_BASE = 2.0
_DEFAULT_BATCH_SIZE = 50
_CHECKPOINT_INTERVAL = 3


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class WorkflowStatus(str, Enum):
    """Lifecycle states for a workflow execution."""

    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"

    @property
    def is_terminal(self) -> bool:
        return self in (WorkflowStatus.COMPLETED, WorkflowStatus.FAILED)

    @property
    def is_active(self) -> bool:
        return self in (WorkflowStatus.RUNNING, WorkflowStatus.RETRY)


class StageStatus(str, Enum):
    """Status of a pipeline stage execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"


class BatchItemStatus(str, Enum):
    """Status of an individual batch item."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"


class TriggerType(str, Enum):
    """Types of workflow triggers."""

    MANUAL = "manual"
    SCHEDULE = "schedule"
    EVENT = "event"
    CONDITION = "condition"
    DEADLINE = "deadline"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class PipelineStage:
    """A single stage in a workflow pipeline."""

    stage_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    name: str = ""
    handler: str = ""
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    timeout: int = _DEFAULT_STAGE_TIMEOUT
    retry_count: int = 0
    max_retries: int = _DEFAULT_MAX_RETRIES
    depends_on: List[str] = field(default_factory=list)
    condition: str = ""  # Optional condition for conditional execution
    status: StageStatus = StageStatus.PENDING
    result: Dict[str, Any] = field(default_factory=dict)
    started_at: str = ""
    completed_at: str = ""
    error_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage_id": self.stage_id,
            "name": self.name,
            "handler": self.handler,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "depends_on": self.depends_on,
            "condition": self.condition,
            "status": self.status.value,
            "result": self.result,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error_message": self.error_message,
        }

    @property
    def can_retry(self) -> bool:
        return self.retry_count < self.max_retries and self.status == StageStatus.FAILED


@dataclass
class WorkflowDefinition:
    """Defines a reusable workflow with stages, triggers, and scheduling."""

    workflow_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    name: str = ""
    description: str = ""
    stages: List[PipelineStage] = field(default_factory=list)
    triggers: List[Dict[str, Any]] = field(default_factory=list)
    schedule: str = ""  # cron-like expression
    lane: str = ""
    version: str = "1.0"
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "stages": [s.to_dict() for s in self.stages],
            "triggers": self.triggers,
            "schedule": self.schedule,
            "lane": self.lane,
            "version": self.version,
            "stage_count": len(self.stages),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class WorkflowExecution:
    """Tracks a single execution of a workflow."""

    execution_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    workflow_id: str = ""
    workflow_name: str = ""
    status: WorkflowStatus = WorkflowStatus.QUEUED
    context: Dict[str, Any] = field(default_factory=dict)
    stages_completed: int = 0
    stages_total: int = 0
    stages_failed: int = 0
    started_at: str = ""
    completed_at: str = ""
    error_message: str = ""
    stage_results: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "status": self.status.value,
            "context": self.context,
            "stages_completed": self.stages_completed,
            "stages_total": self.stages_total,
            "stages_failed": self.stages_failed,
            "progress_pct": (
                round(self.stages_completed / self.stages_total * 100, 1)
                if self.stages_total > 0
                else 0.0
            ),
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error_message": self.error_message,
            "stage_results": self.stage_results,
        }


@dataclass
class BatchItem:
    """An individual item in a batch processing run."""

    item_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    data: Dict[str, Any] = field(default_factory=dict)
    status: BatchItemStatus = BatchItemStatus.PENDING
    result: Dict[str, Any] = field(default_factory=dict)
    retries: int = 0
    error_message: str = ""
    processed_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "data": self.data,
            "status": self.status.value,
            "result": self.result,
            "retries": self.retries,
            "error_message": self.error_message,
            "processed_at": self.processed_at,
        }


@dataclass
class ScheduleEntry:
    """A scheduled workflow execution."""

    schedule_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    workflow_id: str = ""
    workflow_name: str = ""
    cron_expr: str = ""
    next_run: str = ""
    last_run: str = ""
    run_count: int = 0
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schedule_id": self.schedule_id,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "cron_expr": self.cron_expr,
            "next_run": self.next_run,
            "last_run": self.last_run,
            "run_count": self.run_count,
            "enabled": self.enabled,
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


def _ensure_workflow_tables(conn: sqlite3.Connection) -> None:
    """Create workflow engine tables if they do not exist."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS workflow_definitions (
            workflow_id TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            description TEXT,
            config      TEXT,
            lane        TEXT,
            version     TEXT DEFAULT '1.0',
            created_at  TEXT,
            updated_at  TEXT
        );
        CREATE TABLE IF NOT EXISTS workflow_executions (
            execution_id  TEXT PRIMARY KEY,
            workflow_id   TEXT,
            workflow_name TEXT,
            status        TEXT DEFAULT 'queued',
            context       TEXT,
            stages_completed INTEGER DEFAULT 0,
            stages_total    INTEGER DEFAULT 0,
            stages_failed   INTEGER DEFAULT 0,
            started_at    TEXT,
            completed_at  TEXT,
            error_message TEXT,
            stage_results TEXT
        );
        CREATE TABLE IF NOT EXISTS workflow_schedules (
            schedule_id   TEXT PRIMARY KEY,
            workflow_id   TEXT,
            workflow_name TEXT,
            cron_expr     TEXT,
            next_run      TEXT,
            last_run      TEXT,
            run_count     INTEGER DEFAULT 0,
            enabled       INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS workflow_batch_items (
            item_id       TEXT PRIMARY KEY,
            batch_id      TEXT,
            data          TEXT,
            status        TEXT DEFAULT 'pending',
            result        TEXT,
            retries       INTEGER DEFAULT 0,
            error_message TEXT,
            processed_at  TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_workflow_exec_status
            ON workflow_executions(status, workflow_id);
        CREATE INDEX IF NOT EXISTS idx_workflow_batch_status
            ON workflow_batch_items(batch_id, status);
        """
    )
    conn.commit()


# ---------------------------------------------------------------------------
# BatchProcessor
# ---------------------------------------------------------------------------


class BatchProcessor:
    """Process items in bulk with progress tracking, error handling, and retry.

    Designed for batch operations like processing all evidence in a lane,
    validating all citations, or formatting all exhibits.
    """

    def __init__(
        self,
        *,
        batch_id: str = "",
        batch_size: int = _DEFAULT_BATCH_SIZE,
        db_path: Optional[Path] = None,
    ) -> None:
        self._batch_id = batch_id or uuid.uuid4().hex[:10]
        self._batch_size = batch_size
        self._db_path = db_path or _DB_PATH
        self._items: List[BatchItem] = []
        self._results: List[Dict[str, Any]] = []

    def add_items(self, items: List[Dict[str, Any]]) -> int:
        """Add items to the batch queue. Returns count added."""
        added = 0
        for item_data in items:
            bi = BatchItem(data=item_data)
            self._items.append(bi)
            added += 1
        logger.info("BatchProcessor[%s] added %d items", self._batch_id, added)
        return added

    def process_batch(
        self,
        handler: Callable[[Dict[str, Any]], Dict[str, Any]],
        *,
        max_errors: int = 10,
    ) -> List[Dict[str, Any]]:
        """Process all pending items using the provided handler.

        Parameters
        ----------
        handler : callable
            Function that takes item data dict and returns result dict.
        max_errors : int
            Stop processing after this many consecutive errors.
        """
        consecutive_errors = 0
        results: List[Dict[str, Any]] = []

        for item in self._items:
            if item.status not in (BatchItemStatus.PENDING, BatchItemStatus.RETRYING):
                continue

            item.status = BatchItemStatus.PROCESSING
            try:
                result = handler(item.data)
                item.result = result
                item.status = BatchItemStatus.COMPLETED
                item.processed_at = datetime.now(timezone.utc).isoformat()
                consecutive_errors = 0
                results.append(item.to_dict())

            except Exception as exc:
                item.status = BatchItemStatus.FAILED
                item.error_message = str(exc)
                item.retries += 1
                consecutive_errors += 1
                results.append(item.to_dict())
                logger.warning(
                    "BatchProcessor[%s] item %s failed: %s",
                    self._batch_id,
                    item.item_id,
                    exc,
                )

                if consecutive_errors >= max_errors:
                    logger.error(
                        "BatchProcessor[%s] aborting after %d consecutive errors",
                        self._batch_id,
                        max_errors,
                    )
                    break

        self._results = results
        return results

    def get_progress(self) -> Dict[str, Any]:
        """Get current batch processing progress."""
        total = len(self._items)
        completed = sum(1 for i in self._items if i.status == BatchItemStatus.COMPLETED)
        failed = sum(1 for i in self._items if i.status == BatchItemStatus.FAILED)
        pending = sum(
            1 for i in self._items if i.status in (BatchItemStatus.PENDING, BatchItemStatus.RETRYING)
        )

        return {
            "batch_id": self._batch_id,
            "total": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "progress_pct": round(completed / total * 100, 1) if total > 0 else 0.0,
            "success_rate": round(completed / (completed + failed), 4) if (completed + failed) > 0 else 0.0,
        }

    def retry_failed(self, *, handler: Optional[Callable] = None) -> int:
        """Retry all failed items. Returns count retried."""
        retried = 0
        for item in self._items:
            if item.status == BatchItemStatus.FAILED and item.retries < _DEFAULT_MAX_RETRIES:
                item.status = BatchItemStatus.RETRYING
                retried += 1

        if handler and retried > 0:
            self.process_batch(handler)

        return retried


# ---------------------------------------------------------------------------
# ConditionalRouter
# ---------------------------------------------------------------------------


class ConditionalRouter:
    """Route items to different handlers based on conditions.

    Used for lane routing, filing type selection, and conditional
    pipeline branching.
    """

    def __init__(self) -> None:
        self._routes: List[Dict[str, Any]] = []
        self._default_handler: Optional[str] = None
        self._handlers: Dict[str, Callable] = {}
        self._routing_log: List[Dict[str, Any]] = []

    def add_route(
        self,
        condition: str,
        handler: str,
        *,
        priority: int = 0,
        description: str = "",
    ) -> None:
        """Add a routing rule.

        Parameters
        ----------
        condition : str
            Condition expression — evaluated against item context.
            Supports: key=value, key in [values], key>value, key<value.
        handler : str
            Name of the handler to route to.
        priority : int
            Higher priority routes are evaluated first.
        """
        self._routes.append(
            {
                "condition": condition,
                "handler": handler,
                "priority": priority,
                "description": description,
            }
        )
        self._routes.sort(key=lambda r: r["priority"], reverse=True)

    def set_default(self, handler: str) -> None:
        """Set the default handler when no conditions match."""
        self._default_handler = handler

    def register_handler(self, name: str, handler: Callable) -> None:
        """Register a callable handler by name."""
        self._handlers[name] = handler

    def evaluate(self, context: Dict[str, Any]) -> str:
        """Evaluate conditions and return the matching handler name."""
        for route in self._routes:
            if self._check_condition(route["condition"], context):
                handler_name = route["handler"]
                self._routing_log.append(
                    {
                        "condition": route["condition"],
                        "handler": handler_name,
                        "context_summary": str(context)[:200],
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )
                return handler_name

        return self._default_handler or "unrouted"

    def route(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Route an item to the appropriate handler and execute it."""
        handler_name = self.evaluate(item)
        handler_fn = self._handlers.get(handler_name)

        if not handler_fn:
            return {
                "status": "error",
                "message": f"Handler '{handler_name}' not registered",
                "handler": handler_name,
            }

        try:
            result = handler_fn(item)
            return {"status": "success", "handler": handler_name, "result": result}
        except Exception as exc:
            return {"status": "error", "handler": handler_name, "message": str(exc)}

    @staticmethod
    def _check_condition(condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate a condition string against context.

        Supports:
            key=value        — equality check
            key!=value       — inequality check
            key>value        — greater than (numeric)
            key<value        — less than (numeric)
            key in [a,b,c]   — membership check
            key exists       — key presence check
        """
        condition = condition.strip()

        # key exists
        if condition.endswith(" exists"):
            key = condition[:-7].strip()
            return key in context

        # key in [values]
        if " in " in condition and "[" in condition:
            parts = condition.split(" in ", 1)
            key = parts[0].strip()
            values_str = parts[1].strip().strip("[]")
            values = [v.strip().strip("'\"") for v in values_str.split(",")]
            return str(context.get(key, "")) in values

        # key!=value
        if "!=" in condition:
            key, value = condition.split("!=", 1)
            return str(context.get(key.strip(), "")) != value.strip()

        # key>=value
        if ">=" in condition:
            key, value = condition.split(">=", 1)
            try:
                return float(context.get(key.strip(), 0)) >= float(value.strip())
            except (ValueError, TypeError):
                return False

        # key<=value
        if "<=" in condition:
            key, value = condition.split("<=", 1)
            try:
                return float(context.get(key.strip(), 0)) <= float(value.strip())
            except (ValueError, TypeError):
                return False

        # key>value
        if ">" in condition:
            key, value = condition.split(">", 1)
            try:
                return float(context.get(key.strip(), 0)) > float(value.strip())
            except (ValueError, TypeError):
                return False

        # key<value
        if "<" in condition:
            key, value = condition.split("<", 1)
            try:
                return float(context.get(key.strip(), 0)) < float(value.strip())
            except (ValueError, TypeError):
                return False

        # key=value
        if "=" in condition:
            key, value = condition.split("=", 1)
            return str(context.get(key.strip(), "")) == value.strip()

        # Direct truthy check
        return bool(context.get(condition, False))

    def get_routing_log(self) -> List[Dict[str, Any]]:
        return list(self._routing_log)


# ---------------------------------------------------------------------------
# ScheduleManager
# ---------------------------------------------------------------------------


class ScheduleManager:
    """Manage scheduled workflow executions with cron-like expressions.

    Supports simple interval-based scheduling. For full cron syntax,
    integrate with an external scheduler.
    """

    def __init__(self, *, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or _DB_PATH
        self._schedules: Dict[str, ScheduleEntry] = {}
        self._history: List[Dict[str, Any]] = []

    def add_schedule(
        self,
        workflow_id: str,
        workflow_name: str,
        cron_expr: str,
    ) -> ScheduleEntry:
        """Add a workflow schedule.

        Parameters
        ----------
        workflow_id : str
            ID of the workflow to schedule.
        workflow_name : str
            Human-readable name.
        cron_expr : str
            Simple interval expression: "every Xh", "every Xm", "daily", "weekly".
        """
        entry = ScheduleEntry(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            cron_expr=cron_expr,
            next_run=self._compute_next_run(cron_expr),
        )
        self._schedules[entry.schedule_id] = entry
        logger.info("Scheduled workflow '%s' with '%s'", workflow_name, cron_expr)
        return entry

    def get_due(self) -> List[ScheduleEntry]:
        """Get all schedules that are due for execution."""
        now = datetime.now(timezone.utc).isoformat()
        due = []
        for entry in self._schedules.values():
            if entry.enabled and entry.next_run and entry.next_run <= now:
                due.append(entry)
        return due

    def execute_due(
        self, *, executor: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """Execute all due schedules and return results."""
        due = self.get_due()
        results = []

        for entry in due:
            result = {
                "schedule_id": entry.schedule_id,
                "workflow_id": entry.workflow_id,
                "workflow_name": entry.workflow_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            if executor:
                try:
                    exec_result = executor(entry.workflow_id)
                    result["status"] = "executed"
                    result["result"] = exec_result
                except Exception as exc:
                    result["status"] = "failed"
                    result["error"] = str(exc)
            else:
                result["status"] = "skipped"
                result["reason"] = "no executor provided"

            entry.last_run = datetime.now(timezone.utc).isoformat()
            entry.next_run = self._compute_next_run(entry.cron_expr)
            entry.run_count += 1
            results.append(result)
            self._history.append(result)

        return results

    def track_history(self) -> Dict[str, Any]:
        """Get schedule execution history."""
        return {
            "total_schedules": len(self._schedules),
            "active_schedules": sum(1 for s in self._schedules.values() if s.enabled),
            "total_executions": len(self._history),
            "recent_executions": self._history[-10:],
        }

    @staticmethod
    def _compute_next_run(cron_expr: str) -> str:
        """Compute the next run time from a simple cron expression."""
        now = datetime.now(timezone.utc)
        expr = cron_expr.lower().strip()

        if expr == "daily":
            next_run = now + timedelta(days=1)
        elif expr == "weekly":
            next_run = now + timedelta(weeks=1)
        elif expr == "hourly":
            next_run = now + timedelta(hours=1)
        elif expr.startswith("every ") and expr.endswith("h"):
            hours = int(expr[6:-1])
            next_run = now + timedelta(hours=hours)
        elif expr.startswith("every ") and expr.endswith("m"):
            minutes = int(expr[6:-1])
            next_run = now + timedelta(minutes=minutes)
        elif expr.startswith("every ") and expr.endswith("d"):
            days = int(expr[6:-1])
            next_run = now + timedelta(days=days)
        else:
            next_run = now + timedelta(hours=24)

        return next_run.isoformat()


# ---------------------------------------------------------------------------
# RetryEngine
# ---------------------------------------------------------------------------


class RetryEngine:
    """Execute functions with exponential backoff retry logic.

    Tracks failure statistics for monitoring and tuning.
    """

    def __init__(
        self,
        *,
        max_retries: int = _DEFAULT_MAX_RETRIES,
        backoff_base: float = _DEFAULT_BACKOFF_BASE,
    ) -> None:
        self._max_retries = max_retries
        self._backoff_base = backoff_base
        self._stats: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"attempts": 0, "successes": 0, "failures": 0, "retries": 0}
        )

    def execute_with_retry(
        self,
        fn: Callable[..., Any],
        *args: Any,
        max_retries: Optional[int] = None,
        backoff: Optional[float] = None,
        operation_name: str = "unnamed",
        **kwargs: Any,
    ) -> Any:
        """Execute a function with exponential backoff on failure.

        Parameters
        ----------
        fn : callable
            Function to execute.
        max_retries : int, optional
            Override default max retries.
        backoff : float, optional
            Override default backoff base.
        operation_name : str
            Name for statistics tracking.
        """
        retries = max_retries if max_retries is not None else self._max_retries
        base = backoff if backoff is not None else self._backoff_base
        last_error: Optional[Exception] = None

        for attempt in range(retries + 1):
            self._stats[operation_name]["attempts"] += 1
            try:
                result = fn(*args, **kwargs)
                self._stats[operation_name]["successes"] += 1
                return result
            except Exception as exc:
                last_error = exc
                self._stats[operation_name]["failures"] += 1

                if attempt < retries:
                    wait = base ** attempt
                    self._stats[operation_name]["retries"] += 1
                    logger.warning(
                        "RetryEngine[%s] attempt %d failed: %s. Retrying in %.1fs",
                        operation_name,
                        attempt + 1,
                        exc,
                        wait,
                    )
                    time.sleep(wait)
                else:
                    logger.error(
                        "RetryEngine[%s] all %d attempts failed. Last error: %s",
                        operation_name,
                        retries + 1,
                        exc,
                    )

        raise last_error  # type: ignore[misc]

    def get_failure_stats(self) -> Dict[str, Any]:
        """Get failure statistics for all tracked operations."""
        return {
            name: {
                **stats,
                "success_rate": (
                    round(stats["successes"] / stats["attempts"], 4)
                    if stats["attempts"] > 0
                    else 0.0
                ),
            }
            for name, stats in self._stats.items()
        }


# ---------------------------------------------------------------------------
# WorkflowAutomationEngine (Main)
# ---------------------------------------------------------------------------


class WorkflowAutomationEngine:
    """Main orchestrator for defining, executing, monitoring, and scheduling
    automated litigation workflows.

    Manages the full workflow lifecycle from definition through execution
    with batch processing, conditional routing, scheduling, and retry logic.
    """

    def __init__(self, *, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or _DB_PATH
        self._workflows: Dict[str, WorkflowDefinition] = {}
        self._executions: Dict[str, WorkflowExecution] = {}
        self._batch_processors: Dict[str, BatchProcessor] = {}
        self._router = ConditionalRouter()
        self._scheduler = ScheduleManager(db_path=self._db_path)
        self._retry_engine = RetryEngine()
        self._stage_handlers: Dict[str, Callable] = {}
        self._initialized = False

    # -- Initialization --

    def initialize(self) -> Dict[str, Any]:
        """Initialize the engine and create database tables."""
        if self._initialized:
            return {"status": "already_initialized"}
        try:
            conn = _get_db(self._db_path)
            _ensure_workflow_tables(conn)
            conn.close()
            self._initialized = True
            logger.info("WorkflowAutomationEngine initialized")
            return {"status": "initialized", "db_path": str(self._db_path)}
        except Exception as exc:
            logger.error("Workflow engine init failed: %s", exc)
            return {"status": "error", "message": str(exc)}

    # -- Handler Registration --

    def register_handler(self, name: str, handler: Callable) -> None:
        """Register a stage handler by name."""
        self._stage_handlers[name] = handler
        logger.debug("Registered stage handler: %s", name)

    # -- Workflow Definition --

    def define_workflow(self, config: Dict[str, Any]) -> WorkflowDefinition:
        """Define a new workflow from configuration.

        Parameters
        ----------
        config : dict
            Must include: name, stages (list of stage configs).
            Optional: description, triggers, schedule, lane, version.
        """
        wf = WorkflowDefinition(
            name=config.get("name", "unnamed"),
            description=config.get("description", ""),
            lane=config.get("lane", ""),
            version=config.get("version", "1.0"),
            schedule=config.get("schedule", ""),
        )

        for stage_cfg in config.get("stages", []):
            stage = PipelineStage(
                name=stage_cfg.get("name", ""),
                handler=stage_cfg.get("handler", ""),
                inputs=stage_cfg.get("inputs", []),
                outputs=stage_cfg.get("outputs", []),
                timeout=stage_cfg.get("timeout", _DEFAULT_STAGE_TIMEOUT),
                max_retries=stage_cfg.get("max_retries", _DEFAULT_MAX_RETRIES),
                depends_on=stage_cfg.get("depends_on", []),
                condition=stage_cfg.get("condition", ""),
            )
            wf.stages.append(stage)

        for trigger_cfg in config.get("triggers", []):
            wf.triggers.append(trigger_cfg)

        self._workflows[wf.workflow_id] = wf
        self._persist_workflow(wf)

        # Set up schedule if provided
        if wf.schedule:
            self._scheduler.add_schedule(wf.workflow_id, wf.name, wf.schedule)

        logger.info("Defined workflow: %s (%d stages)", wf.name, len(wf.stages))
        return wf

    # -- Workflow Execution --

    def execute_workflow(
        self,
        workflow_id: str,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a workflow by ID.

        Parameters
        ----------
        workflow_id : str
            The workflow to execute.
        context : dict, optional
            Execution context (lane, case number, etc.).
        """
        # Find workflow by ID or name
        wf = self._workflows.get(workflow_id)
        if not wf:
            for w in self._workflows.values():
                if w.name == workflow_id:
                    wf = w
                    break
        if not wf:
            return {"status": "error", "message": f"Workflow '{workflow_id}' not found"}

        execution = WorkflowExecution(
            workflow_id=wf.workflow_id,
            workflow_name=wf.name,
            context=context or {},
            stages_total=len(wf.stages),
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        execution.status = WorkflowStatus.RUNNING

        stage_context = dict(context or {})

        for stage in wf.stages:
            # Check condition
            if stage.condition and not ConditionalRouter._check_condition(
                stage.condition, stage_context
            ):
                stage.status = StageStatus.SKIPPED
                execution.stage_results.append(
                    {
                        "stage": stage.name,
                        "status": "skipped",
                        "reason": f"Condition not met: {stage.condition}",
                    }
                )
                continue

            # Check dependencies
            deps_met = all(
                any(
                    sr.get("stage") == dep and sr.get("status") == "completed"
                    for sr in execution.stage_results
                )
                for dep in stage.depends_on
            )
            if not deps_met:
                stage.status = StageStatus.SKIPPED
                execution.stage_results.append(
                    {
                        "stage": stage.name,
                        "status": "skipped",
                        "reason": "Dependencies not met",
                    }
                )
                continue

            # Execute stage
            stage.started_at = datetime.now(timezone.utc).isoformat()
            stage.status = StageStatus.RUNNING

            handler = self._stage_handlers.get(stage.handler)
            if handler:
                try:
                    result = self._retry_engine.execute_with_retry(
                        handler,
                        stage_context,
                        max_retries=stage.max_retries,
                        operation_name=f"{wf.name}/{stage.name}",
                    )
                    stage.status = StageStatus.COMPLETED
                    stage.result = result if isinstance(result, dict) else {"output": result}
                    stage_context.update(stage.result)
                    execution.stages_completed += 1

                except Exception as exc:
                    stage.status = StageStatus.FAILED
                    stage.error_message = str(exc)
                    execution.stages_failed += 1
                    logger.error("Stage %s failed: %s", stage.name, exc)
            else:
                # No handler registered — mark as completed (pass-through)
                stage.status = StageStatus.COMPLETED
                stage.result = {"note": f"No handler registered for '{stage.handler}'"}
                execution.stages_completed += 1

            stage.completed_at = datetime.now(timezone.utc).isoformat()
            execution.stage_results.append(
                {
                    "stage": stage.name,
                    "handler": stage.handler,
                    "status": stage.status.value,
                    "result": stage.result,
                    "error": stage.error_message,
                }
            )

        # Determine final status
        if execution.stages_failed > 0:
            execution.status = WorkflowStatus.FAILED
            execution.error_message = (
                f"{execution.stages_failed} of {execution.stages_total} stages failed"
            )
        else:
            execution.status = WorkflowStatus.COMPLETED

        execution.completed_at = datetime.now(timezone.utc).isoformat()
        self._executions[execution.execution_id] = execution
        self._persist_execution(execution)

        return execution.to_dict()

    # -- Batch Processing --

    def batch_process(
        self,
        items: List[Dict[str, Any]],
        handler: Callable[[Dict[str, Any]], Dict[str, Any]],
        *,
        batch_id: str = "",
    ) -> Dict[str, Any]:
        """Process a batch of items with a handler.

        Parameters
        ----------
        items : list
            Items to process.
        handler : callable
            Processing function for each item.
        batch_id : str
            Optional batch identifier.
        """
        processor = BatchProcessor(batch_id=batch_id, db_path=self._db_path)
        processor.add_items(items)
        processor.process_batch(handler)

        self._batch_processors[processor._batch_id] = processor
        return processor.get_progress()

    # -- Monitoring --

    def monitor_workflows(self) -> Dict[str, Any]:
        """Get current status of all workflow executions."""
        active = []
        completed = []
        failed = []

        for exec_ in self._executions.values():
            summary = {
                "execution_id": exec_.execution_id,
                "workflow": exec_.workflow_name,
                "status": exec_.status.value,
                "progress": (
                    f"{exec_.stages_completed}/{exec_.stages_total}"
                ),
            }
            if exec_.status.is_active:
                active.append(summary)
            elif exec_.status == WorkflowStatus.COMPLETED:
                completed.append(summary)
            else:
                failed.append(summary)

        return {
            "active": active,
            "completed": completed[-10:],
            "failed": failed[-10:],
            "total_workflows_defined": len(self._workflows),
            "total_executions": len(self._executions),
            "schedules": self._scheduler.track_history(),
        }

    # -- Stats --

    def get_stats(self) -> Dict[str, Any]:
        """Comprehensive workflow engine statistics."""
        return {
            "initialized": self._initialized,
            "workflows_defined": len(self._workflows),
            "workflow_names": [w.name for w in self._workflows.values()],
            "total_executions": len(self._executions),
            "active_executions": sum(
                1 for e in self._executions.values() if e.status.is_active
            ),
            "completed_executions": sum(
                1 for e in self._executions.values() if e.status == WorkflowStatus.COMPLETED
            ),
            "failed_executions": sum(
                1 for e in self._executions.values() if e.status == WorkflowStatus.FAILED
            ),
            "batch_processors": len(self._batch_processors),
            "schedules": self._scheduler.track_history(),
            "retry_stats": self._retry_engine.get_failure_stats(),
            "stage_handlers_registered": len(self._stage_handlers),
        }

    # -- Persistence --

    def _persist_workflow(self, wf: WorkflowDefinition) -> None:
        """Save workflow definition to database."""
        try:
            conn = _get_db(self._db_path)
            _ensure_workflow_tables(conn)
            conn.execute(
                """
                INSERT OR REPLACE INTO workflow_definitions
                    (workflow_id, name, description, config, lane, version, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    wf.workflow_id,
                    wf.name,
                    wf.description,
                    json.dumps(wf.to_dict()),
                    wf.lane,
                    wf.version,
                    wf.created_at,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            conn.commit()
            conn.close()
        except Exception as exc:
            logger.warning("Failed to persist workflow %s: %s", wf.name, exc)

    def _persist_execution(self, execution: WorkflowExecution) -> None:
        """Save workflow execution to database."""
        try:
            conn = _get_db(self._db_path)
            _ensure_workflow_tables(conn)
            conn.execute(
                """
                INSERT OR REPLACE INTO workflow_executions
                    (execution_id, workflow_id, workflow_name, status,
                     context, stages_completed, stages_total, stages_failed,
                     started_at, completed_at, error_message, stage_results)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    execution.execution_id,
                    execution.workflow_id,
                    execution.workflow_name,
                    execution.status.value,
                    json.dumps(execution.context),
                    execution.stages_completed,
                    execution.stages_total,
                    execution.stages_failed,
                    execution.started_at,
                    execution.completed_at,
                    execution.error_message,
                    json.dumps(execution.stage_results),
                ),
            )
            conn.commit()
            conn.close()
        except Exception as exc:
            logger.warning("Failed to persist execution %s: %s", execution.execution_id, exc)


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------


def create_engine(*, db_path: Optional[Path] = None) -> WorkflowAutomationEngine:
    """Create and initialize a WorkflowAutomationEngine instance."""
    engine = WorkflowAutomationEngine(db_path=db_path)
    engine.initialize()
    return engine
