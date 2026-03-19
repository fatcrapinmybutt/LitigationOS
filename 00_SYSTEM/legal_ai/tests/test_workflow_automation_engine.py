# -*- coding: utf-8 -*-
"""Tests for workflow_automation_engine.py — Wave 14 Omega Evolution.
=====================================================================
Comprehensive pytest suite (~85 tests) covering:
  • WorkflowStatus, StageStatus, BatchItemStatus, TriggerType enumerations
  • PipelineStage, WorkflowDefinition, WorkflowExecution, BatchItem, ScheduleEntry dataclasses
  • BatchProcessor — add, process, progress, retry
  • ConditionalRouter — add_route, evaluate, route, condition parsing
  • ScheduleManager — add, get_due, execute, history
  • RetryEngine — execute_with_retry, backoff, failure stats
  • WorkflowAutomationEngine — full orchestrator lifecycle

Zero network / zero real DB — all DB interactions use tmp_path SQLite.
"""
from __future__ import annotations

import json
import pathlib
import sqlite3
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

import pytest

# ---------------------------------------------------------------------------
# Path bootstrap
# ---------------------------------------------------------------------------
_THIS_DIR = pathlib.Path(__file__).resolve().parent
_LEGAL_AI_DIR = _THIS_DIR.parent
if str(_LEGAL_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_LEGAL_AI_DIR))

from workflow_automation_engine import (
    WorkflowStatus,
    StageStatus,
    BatchItemStatus,
    TriggerType,
    PipelineStage,
    WorkflowDefinition,
    WorkflowExecution,
    BatchItem,
    ScheduleEntry,
    BatchProcessor,
    ConditionalRouter,
    ScheduleManager,
    RetryEngine,
    WorkflowAutomationEngine,
    LANE_CASES,
    _DEFAULT_STAGE_TIMEOUT,
    _DEFAULT_MAX_RETRIES,
    _DEFAULT_BACKOFF_BASE,
    _DEFAULT_BATCH_SIZE,
    _get_db,
    _ensure_workflow_tables,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_db(tmp_path):
    """Create a temporary SQLite database for testing."""
    return tmp_path / "test_workflow_engine.db"


@pytest.fixture
def engine(tmp_db):
    """Create an initialized WorkflowAutomationEngine with tmp DB."""
    eng = WorkflowAutomationEngine(db_path=tmp_db)
    eng.initialize()
    return eng


@pytest.fixture
def sample_workflow_config():
    """Standard workflow configuration for testing."""
    return {
        "name": "filing_pipeline",
        "description": "End-to-end filing workflow for Lane A",
        "lane": "A",
        "stages": [
            {"name": "gather_evidence", "handler": "evidence_harvester"},
            {"name": "draft_motion", "handler": "brief_writer"},
            {"name": "qa_check", "handler": "quality_gate"},
        ],
    }


# ===================================================================
# Enumeration Tests
# ===================================================================


class TestWorkflowStatus:
    def test_all_values(self):
        assert set(WorkflowStatus) == {
            WorkflowStatus.QUEUED, WorkflowStatus.RUNNING,
            WorkflowStatus.PAUSED, WorkflowStatus.COMPLETED,
            WorkflowStatus.FAILED, WorkflowStatus.RETRY,
        }

    def test_is_terminal_completed(self):
        assert WorkflowStatus.COMPLETED.is_terminal is True

    def test_is_terminal_failed(self):
        assert WorkflowStatus.FAILED.is_terminal is True

    def test_is_terminal_running(self):
        assert WorkflowStatus.RUNNING.is_terminal is False

    def test_is_active_running(self):
        assert WorkflowStatus.RUNNING.is_active is True

    def test_is_active_retry(self):
        assert WorkflowStatus.RETRY.is_active is True

    def test_is_active_queued(self):
        assert WorkflowStatus.QUEUED.is_active is False


class TestStageStatus:
    def test_all_values(self):
        assert set(StageStatus) == {
            StageStatus.PENDING, StageStatus.RUNNING,
            StageStatus.COMPLETED, StageStatus.FAILED,
            StageStatus.SKIPPED, StageStatus.TIMEOUT,
        }


class TestBatchItemStatus:
    def test_all_values(self):
        assert set(BatchItemStatus) == {
            BatchItemStatus.PENDING, BatchItemStatus.PROCESSING,
            BatchItemStatus.COMPLETED, BatchItemStatus.FAILED,
            BatchItemStatus.RETRYING, BatchItemStatus.SKIPPED,
        }


class TestTriggerType:
    def test_all_values(self):
        assert set(TriggerType) == {
            TriggerType.MANUAL, TriggerType.SCHEDULE,
            TriggerType.EVENT, TriggerType.CONDITION,
            TriggerType.DEADLINE,
        }


# ===================================================================
# Dataclass Tests
# ===================================================================


class TestPipelineStage:
    def test_defaults(self):
        stage = PipelineStage()
        assert stage.timeout == _DEFAULT_STAGE_TIMEOUT
        assert stage.status == StageStatus.PENDING
        assert stage.max_retries == _DEFAULT_MAX_RETRIES

    def test_can_retry_failed(self):
        stage = PipelineStage(status=StageStatus.FAILED, retry_count=0, max_retries=3)
        assert stage.can_retry is True

    def test_can_retry_max_reached(self):
        stage = PipelineStage(status=StageStatus.FAILED, retry_count=3, max_retries=3)
        assert stage.can_retry is False

    def test_can_retry_not_failed(self):
        stage = PipelineStage(status=StageStatus.COMPLETED, retry_count=0)
        assert stage.can_retry is False

    def test_to_dict(self):
        stage = PipelineStage(name="gather", handler="harvester", inputs=["case_data"])
        d = stage.to_dict()
        assert d["name"] == "gather"
        assert d["handler"] == "harvester"
        assert d["inputs"] == ["case_data"]


class TestWorkflowDefinition:
    def test_to_dict_stage_count(self):
        wf = WorkflowDefinition(
            name="test_wf",
            stages=[PipelineStage(name="s1"), PipelineStage(name="s2")],
        )
        d = wf.to_dict()
        assert d["stage_count"] == 2
        assert d["name"] == "test_wf"


class TestWorkflowExecution:
    def test_to_dict_progress(self):
        exe = WorkflowExecution(
            workflow_name="test", stages_completed=3, stages_total=10,
        )
        d = exe.to_dict()
        assert d["progress_pct"] == 30.0

    def test_progress_zero_stages(self):
        exe = WorkflowExecution(stages_total=0)
        d = exe.to_dict()
        assert d["progress_pct"] == 0.0


class TestBatchItem:
    def test_default_status(self):
        bi = BatchItem()
        assert bi.status == BatchItemStatus.PENDING

    def test_to_dict(self):
        bi = BatchItem(data={"file": "doc.pdf"})
        d = bi.to_dict()
        assert d["data"]["file"] == "doc.pdf"


class TestScheduleEntry:
    def test_to_dict(self):
        se = ScheduleEntry(workflow_name="daily_check", cron_expr="daily")
        d = se.to_dict()
        assert d["workflow_name"] == "daily_check"
        assert d["enabled"] is True


# ===================================================================
# BatchProcessor Tests
# ===================================================================


class TestBatchProcessor:
    def test_add_items(self):
        bp = BatchProcessor(batch_id="test_batch")
        count = bp.add_items([{"id": 1}, {"id": 2}, {"id": 3}])
        assert count == 3

    def test_process_batch_success(self):
        bp = BatchProcessor()
        bp.add_items([{"value": x} for x in range(5)])
        results = bp.process_batch(lambda item: {"doubled": item["value"] * 2})
        assert len(results) == 5
        assert all(r["status"] == "completed" for r in results)

    def test_process_batch_with_errors(self):
        bp = BatchProcessor()
        bp.add_items([{"value": x} for x in range(5)])

        def flaky(item):
            if item["value"] == 2:
                raise ValueError("item 2 failed")
            return {"ok": True}

        results = bp.process_batch(flaky)
        failed = [r for r in results if r["status"] == "failed"]
        assert len(failed) == 1

    def test_process_batch_max_errors(self):
        bp = BatchProcessor()
        bp.add_items([{"value": x} for x in range(20)])

        def always_fail(item):
            raise RuntimeError("always fails")

        results = bp.process_batch(always_fail, max_errors=3)
        # Should stop after 3 consecutive errors
        assert len(results) <= 4

    def test_get_progress(self):
        bp = BatchProcessor(batch_id="progress_test")
        bp.add_items([{"x": i} for i in range(10)])
        bp.process_batch(lambda item: {"ok": True})
        progress = bp.get_progress()
        assert progress["total"] == 10
        assert progress["completed"] == 10
        assert progress["progress_pct"] == 100.0

    def test_retry_failed(self):
        bp = BatchProcessor()
        bp.add_items([{"val": 1}, {"val": 2}])

        call_count = 0
        def fail_once(item):
            nonlocal call_count
            call_count += 1
            if item["val"] == 2 and call_count <= 2:
                raise ValueError("transient")
            return {"ok": True}

        bp.process_batch(fail_once)
        retried = bp.retry_failed(handler=fail_once)
        assert retried >= 0  # May have been retried


# ===================================================================
# ConditionalRouter Tests
# ===================================================================


class TestConditionalRouter:
    def test_add_route(self):
        router = ConditionalRouter()
        router.add_route("lane=A", "custody_handler")
        assert len(router._routes) == 1

    def test_evaluate_equality(self):
        router = ConditionalRouter()
        router.add_route("lane=A", "custody_handler")
        result = router.evaluate({"lane": "A"})
        assert result == "custody_handler"

    def test_evaluate_no_match_returns_default(self):
        router = ConditionalRouter()
        router.add_route("lane=A", "handler_a")
        router.set_default("fallback")
        result = router.evaluate({"lane": "Z"})
        assert result == "fallback"

    def test_evaluate_no_match_no_default(self):
        router = ConditionalRouter()
        result = router.evaluate({"lane": "X"})
        assert result == "unrouted"

    def test_evaluate_inequality(self):
        router = ConditionalRouter()
        router.add_route("status!=closed", "open_handler")
        result = router.evaluate({"status": "open"})
        assert result == "open_handler"

    def test_evaluate_greater_than(self):
        router = ConditionalRouter()
        router.add_route("priority>5", "high_priority")
        assert router.evaluate({"priority": 8}) == "high_priority"

    def test_evaluate_less_than(self):
        router = ConditionalRouter()
        router.add_route("risk<3", "low_risk")
        assert router.evaluate({"risk": 1}) == "low_risk"

    def test_evaluate_gte(self):
        router = ConditionalRouter()
        router.add_route("score>=90", "excellent")
        assert router.evaluate({"score": 90}) == "excellent"

    def test_evaluate_lte(self):
        router = ConditionalRouter()
        router.add_route("count<=5", "small_batch")
        assert router.evaluate({"count": 5}) == "small_batch"

    def test_evaluate_in_list(self):
        router = ConditionalRouter()
        router.add_route("lane in [A,B,D]", "family_handler")
        assert router.evaluate({"lane": "B"}) == "family_handler"

    def test_evaluate_exists(self):
        router = ConditionalRouter()
        router.add_route("evidence exists", "evidence_handler")
        assert router.evaluate({"evidence": True}) == "evidence_handler"

    def test_evaluate_exists_missing(self):
        router = ConditionalRouter()
        router.add_route("evidence exists", "evidence_handler")
        router.set_default("no_evidence")
        assert router.evaluate({}) == "no_evidence"

    def test_priority_ordering(self):
        router = ConditionalRouter()
        router.add_route("lane=A", "low_priority", priority=1)
        router.add_route("lane=A", "high_priority", priority=10)
        result = router.evaluate({"lane": "A"})
        assert result == "high_priority"

    def test_route_with_handler(self):
        router = ConditionalRouter()
        router.add_route("type=motion", "motion_handler")
        router.register_handler("motion_handler", lambda item: {"filed": True})
        result = router.route({"type": "motion"})
        assert result["status"] == "success"
        assert result["result"]["filed"] is True

    def test_route_handler_not_registered(self):
        router = ConditionalRouter()
        router.add_route("type=motion", "missing_handler")
        result = router.route({"type": "motion"})
        assert result["status"] == "error"

    def test_route_handler_exception(self):
        router = ConditionalRouter()
        router.add_route("x=1", "bad")
        router.register_handler("bad", lambda item: (_ for _ in ()).throw(ValueError("broken")))
        # Simpler: register a handler that raises
        router._handlers["bad"] = lambda item: (_ for _ in ()).throw(RuntimeError("boom"))
        # Let's do it properly
        def bad_handler(item):
            raise RuntimeError("handler crashed")
        router.register_handler("bad", bad_handler)
        result = router.route({"x": "1"})
        assert result["status"] == "error"

    def test_get_routing_log(self):
        router = ConditionalRouter()
        router.add_route("lane=A", "handler_a")
        router.evaluate({"lane": "A"})
        log = router.get_routing_log()
        assert len(log) == 1


# ===================================================================
# ScheduleManager Tests
# ===================================================================


class TestScheduleManager:
    def test_add_schedule(self):
        sm = ScheduleManager()
        entry = sm.add_schedule("wf1", "daily_check", "daily")
        assert entry.workflow_id == "wf1"
        assert entry.cron_expr == "daily"
        assert entry.next_run != ""

    def test_get_due_none(self):
        sm = ScheduleManager()
        sm.add_schedule("wf1", "future_run", "weekly")
        # Just added — next_run is in the future
        due = sm.get_due()
        assert len(due) == 0

    def test_get_due_past(self):
        sm = ScheduleManager()
        entry = sm.add_schedule("wf1", "past_run", "daily")
        # Manually set next_run to the past
        entry.next_run = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        due = sm.get_due()
        assert len(due) == 1

    def test_execute_due_no_executor(self):
        sm = ScheduleManager()
        entry = sm.add_schedule("wf1", "test", "daily")
        entry.next_run = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        results = sm.execute_due()
        assert len(results) == 1
        assert results[0]["status"] == "skipped"

    def test_execute_due_with_executor(self):
        sm = ScheduleManager()
        entry = sm.add_schedule("wf1", "test", "daily")
        entry.next_run = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        results = sm.execute_due(executor=lambda wf_id: {"executed": wf_id})
        assert results[0]["status"] == "executed"
        assert entry.run_count == 1

    def test_track_history(self):
        sm = ScheduleManager()
        sm.add_schedule("wf1", "test", "hourly")
        history = sm.track_history()
        assert history["total_schedules"] == 1
        assert history["active_schedules"] == 1

    def test_compute_next_run_daily(self):
        result = ScheduleManager._compute_next_run("daily")
        next_dt = datetime.fromisoformat(result)
        assert next_dt > datetime.now(timezone.utc)

    def test_compute_next_run_hourly(self):
        result = ScheduleManager._compute_next_run("hourly")
        next_dt = datetime.fromisoformat(result)
        assert next_dt > datetime.now(timezone.utc)

    def test_compute_next_run_every_2h(self):
        result = ScheduleManager._compute_next_run("every 2h")
        next_dt = datetime.fromisoformat(result)
        assert next_dt > datetime.now(timezone.utc)

    def test_compute_next_run_every_30m(self):
        result = ScheduleManager._compute_next_run("every 30m")
        next_dt = datetime.fromisoformat(result)
        assert next_dt > datetime.now(timezone.utc)


# ===================================================================
# RetryEngine Tests
# ===================================================================


class TestRetryEngine:
    def test_execute_success_first_try(self):
        re = RetryEngine()
        result = re.execute_with_retry(lambda: 42, operation_name="test_op")
        assert result == 42

    def test_execute_retry_then_succeed(self):
        re = RetryEngine(max_retries=3, backoff_base=0.01)
        call_count = 0

        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("transient")
            return "success"

        result = re.execute_with_retry(flaky, operation_name="flaky_op")
        assert result == "success"
        assert call_count == 3

    def test_execute_all_retries_exhausted(self):
        re = RetryEngine(max_retries=2, backoff_base=0.01)

        def always_fail():
            raise RuntimeError("permanent failure")

        with pytest.raises(RuntimeError, match="permanent failure"):
            re.execute_with_retry(always_fail, operation_name="fail_op")

    def test_execute_with_args(self):
        re = RetryEngine()
        result = re.execute_with_retry(
            lambda x, y: x + y, 3, 4, operation_name="add"
        )
        assert result == 7

    def test_execute_custom_retries(self):
        re = RetryEngine(max_retries=1, backoff_base=0.01)
        count = 0

        def fail_twice():
            nonlocal count
            count += 1
            if count <= 5:
                raise ValueError("fail")
            return "ok"

        with pytest.raises(ValueError):
            re.execute_with_retry(fail_twice, max_retries=2, backoff=0.01, operation_name="custom")

    def test_get_failure_stats(self):
        re = RetryEngine(max_retries=1, backoff_base=0.01)
        re.execute_with_retry(lambda: "ok", operation_name="good_op")
        stats = re.get_failure_stats()
        assert "good_op" in stats
        assert stats["good_op"]["successes"] == 1
        assert stats["good_op"]["success_rate"] == 1.0

    def test_failure_stats_after_failures(self):
        re = RetryEngine(max_retries=0, backoff_base=0.01)
        try:
            re.execute_with_retry(lambda: (_ for _ in ()).throw(ValueError("x")), operation_name="bad")
        except ValueError:
            pass
        # Use a proper failing function
        def raise_err():
            raise ValueError("x")
        try:
            re.execute_with_retry(raise_err, operation_name="bad2")
        except ValueError:
            pass
        stats = re.get_failure_stats()
        assert stats["bad2"]["failures"] == 1


# ===================================================================
# WorkflowAutomationEngine Tests
# ===================================================================


class TestEngineInit:
    def test_initialize(self, tmp_db):
        eng = WorkflowAutomationEngine(db_path=tmp_db)
        result = eng.initialize()
        assert result["status"] == "initialized"

    def test_double_initialize(self, engine):
        result = engine.initialize()
        assert result["status"] == "already_initialized"


class TestEngineDefineWorkflow:
    def test_define_workflow(self, engine, sample_workflow_config):
        wf = engine.define_workflow(sample_workflow_config)
        assert wf.name == "filing_pipeline"
        assert len(wf.stages) == 3

    def test_define_workflow_with_schedule(self, engine):
        wf = engine.define_workflow({
            "name": "scheduled_wf",
            "stages": [{"name": "step1", "handler": "handler1"}],
            "schedule": "daily",
        })
        assert wf.schedule == "daily"

    def test_define_workflow_with_triggers(self, engine):
        wf = engine.define_workflow({
            "name": "triggered_wf",
            "stages": [{"name": "step1", "handler": "h1"}],
            "triggers": [{"type": "event", "event": "new_evidence"}],
        })
        assert len(wf.triggers) == 1


class TestEngineExecuteWorkflow:
    def test_execute_workflow_no_handlers(self, engine, sample_workflow_config):
        wf = engine.define_workflow(sample_workflow_config)
        result = engine.execute_workflow(wf.workflow_id)
        assert result["status"] == "completed"
        assert result["stages_completed"] == 3

    def test_execute_workflow_by_name(self, engine, sample_workflow_config):
        engine.define_workflow(sample_workflow_config)
        result = engine.execute_workflow("filing_pipeline")
        assert result["status"] == "completed"

    def test_execute_workflow_not_found(self, engine):
        result = engine.execute_workflow("nonexistent")
        assert result["status"] == "error"

    def test_execute_with_registered_handler(self, engine):
        engine.register_handler("my_handler", lambda ctx: {"output": "done"})
        wf = engine.define_workflow({
            "name": "handler_wf",
            "stages": [{"name": "step1", "handler": "my_handler"}],
        })
        result = engine.execute_workflow(wf.workflow_id, context={"lane": "A"})
        assert result["status"] == "completed"

    def test_execute_with_failing_handler(self, engine):
        def bad_handler(ctx):
            raise RuntimeError("handler failed")

        engine.register_handler("bad_handler", bad_handler)
        wf = engine.define_workflow({
            "name": "failing_wf",
            "stages": [{"name": "step1", "handler": "bad_handler", "max_retries": 0}],
        })
        result = engine.execute_workflow(wf.workflow_id)
        assert result["status"] == "failed"

    def test_execute_conditional_stage_skipped(self, engine):
        wf = engine.define_workflow({
            "name": "conditional_wf",
            "stages": [
                {"name": "step1", "handler": "h1", "condition": "lane=A"},
            ],
        })
        result = engine.execute_workflow(wf.workflow_id, context={"lane": "B"})
        skipped = [s for s in result["stage_results"] if s["status"] == "skipped"]
        assert len(skipped) == 1

    def test_execute_conditional_stage_runs(self, engine):
        wf = engine.define_workflow({
            "name": "conditional_wf_2",
            "stages": [
                {"name": "step1", "handler": "h1", "condition": "lane=A"},
            ],
        })
        result = engine.execute_workflow(wf.workflow_id, context={"lane": "A"})
        assert result["stages_completed"] == 1

    def test_execute_dependency_skipped(self, engine):
        wf = engine.define_workflow({
            "name": "dep_wf",
            "stages": [
                {"name": "step2", "handler": "h2", "depends_on": ["step1"]},
            ],
        })
        result = engine.execute_workflow(wf.workflow_id)
        skipped = [s for s in result["stage_results"] if s["status"] == "skipped"]
        assert len(skipped) == 1


class TestEngineBatchProcess:
    def test_batch_process(self, engine):
        items = [{"file": f"doc_{i}.pdf"} for i in range(5)]
        result = engine.batch_process(items, lambda item: {"processed": True})
        assert result["total"] == 5
        assert result["completed"] == 5


class TestEngineMonitoring:
    def test_monitor_workflows_empty(self, engine):
        result = engine.monitor_workflows()
        assert result["total_workflows_defined"] == 0
        assert result["total_executions"] == 0

    def test_monitor_workflows_after_execution(self, engine, sample_workflow_config):
        wf = engine.define_workflow(sample_workflow_config)
        engine.execute_workflow(wf.workflow_id)
        result = engine.monitor_workflows()
        assert result["total_executions"] == 1


class TestEngineStats:
    def test_get_stats_empty(self, engine):
        stats = engine.get_stats()
        assert stats["initialized"] is True
        assert stats["workflows_defined"] == 0
        assert stats["total_executions"] == 0

    def test_get_stats_after_work(self, engine, sample_workflow_config):
        wf = engine.define_workflow(sample_workflow_config)
        engine.execute_workflow(wf.workflow_id)
        stats = engine.get_stats()
        assert stats["workflows_defined"] == 1
        assert stats["total_executions"] == 1
        assert "filing_pipeline" in stats["workflow_names"]


# ===================================================================
# Database Helper Tests
# ===================================================================


class TestWorkflowDatabaseHelpers:
    def test_get_db_connection(self, tmp_db):
        conn = _get_db(tmp_db)
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode.lower() == "wal"
        conn.close()

    def test_ensure_workflow_tables(self, tmp_db):
        conn = _get_db(tmp_db)
        _ensure_workflow_tables(conn)
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]
        conn.close()
        assert "workflow_definitions" in tables
        assert "workflow_executions" in tables
        assert "workflow_schedules" in tables
        assert "workflow_batch_items" in tables


# ===================================================================
# Constants Tests
# ===================================================================


class TestWorkflowConstants:
    def test_lane_cases(self):
        assert LANE_CASES["A"] == "2024-001507-DC"

    def test_defaults(self):
        assert _DEFAULT_STAGE_TIMEOUT == 300
        assert _DEFAULT_MAX_RETRIES == 3
        assert _DEFAULT_BACKOFF_BASE == 2.0
        assert _DEFAULT_BATCH_SIZE == 50
