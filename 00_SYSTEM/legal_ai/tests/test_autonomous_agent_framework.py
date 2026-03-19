# -*- coding: utf-8 -*-
"""Tests for autonomous_agent_framework.py — Wave 14 Omega Evolution.
=====================================================================
Comprehensive pytest suite (~85 tests) covering:
  • AgentState, TaskStatus, ContractSeverity enumerations
  • AgentCapability, BehavioralContract, ContractViolation, AgentTask, AgentProfile dataclasses
  • ReActLoop — observe → think → act → evaluate
  • PlanAndExecute — task decomposition, step execution, replanning, checkpointing
  • ToolRegistry — register, select, execute, usage analytics
  • AgentMemory — short-term, long-term, retrieval, TTL, forget_stale
  • ContractValidator — pre/post conditions, invariants, violation tracking
  • AutonomousAgentFramework — full orchestrator lifecycle

Zero network / zero real DB — all DB interactions use tmp_path SQLite.
"""
from __future__ import annotations

import json
import pathlib
import sqlite3
import sys
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

from autonomous_agent_framework import (
    AgentState,
    TaskStatus,
    ContractSeverity,
    AgentCapability,
    BehavioralContract,
    ContractViolation,
    AgentTask,
    AgentProfile,
    ReActLoop,
    PlanAndExecute,
    ToolRegistry,
    AgentMemory,
    ContractValidator,
    AutonomousAgentFramework,
    LANE_CASES,
    _PLAINTIFF,
    _DEFENDANT,
    _CHILD_INITIALS,
    _JUDGE,
    _COURT,
    _MAX_CONCURRENT_AGENTS,
    _DEFAULT_MAX_REACT_ITERATIONS,
    _DEFAULT_MEMORY_TTL_HOURS,
    _MAX_RETRIES,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_db(tmp_path):
    """Create a temporary SQLite database for testing."""
    return tmp_path / "test_agent_framework.db"


@pytest.fixture
def framework(tmp_db):
    """Create an initialized AutonomousAgentFramework with tmp DB."""
    fw = AutonomousAgentFramework(db_path=tmp_db)
    fw.initialize()
    return fw


@pytest.fixture
def sample_agent_config():
    """Standard agent configuration for testing."""
    return {
        "name": "test-filing-agent",
        "description": "Test filing agent for Lane A",
        "capabilities": [
            "draft",
            "cite",
            {"name": "format", "description": "Format filings", "confidence": 0.9, "domains": ["filing"]},
        ],
        "contracts": [
            {
                "name": "qa_contract",
                "invariants": ["never_file_without_qa"],
                "pre_conditions": ["task_assigned"],
                "post_conditions": ["output_validated"],
                "violation_handler": "log_and_halt",
            }
        ],
        "assigned_lanes": ["A"],
    }


# ===================================================================
# Enumeration Tests
# ===================================================================


class TestAgentState:
    def test_all_values_present(self):
        assert set(AgentState) == {
            AgentState.IDLE, AgentState.PLANNING, AgentState.EXECUTING,
            AgentState.MONITORING, AgentState.RECOVERING, AgentState.EVOLVING,
        }

    def test_is_active_planning(self):
        assert AgentState.PLANNING.is_active is True

    def test_is_active_executing(self):
        assert AgentState.EXECUTING.is_active is True

    def test_is_active_monitoring(self):
        assert AgentState.MONITORING.is_active is True

    def test_is_active_idle(self):
        assert AgentState.IDLE.is_active is False

    def test_can_accept_task_idle(self):
        assert AgentState.IDLE.can_accept_task is True

    def test_can_accept_task_monitoring(self):
        assert AgentState.MONITORING.can_accept_task is True

    def test_can_accept_task_executing(self):
        assert AgentState.EXECUTING.can_accept_task is False

    def test_requires_intervention_recovering(self):
        assert AgentState.RECOVERING.requires_intervention is True

    def test_requires_intervention_idle(self):
        assert AgentState.IDLE.requires_intervention is False

    def test_string_value(self):
        assert AgentState.IDLE.value == "idle"


class TestTaskStatus:
    def test_is_terminal_completed(self):
        assert TaskStatus.COMPLETED.is_terminal is True

    def test_is_terminal_failed(self):
        assert TaskStatus.FAILED.is_terminal is True

    def test_is_terminal_blocked(self):
        assert TaskStatus.BLOCKED.is_terminal is True

    def test_is_terminal_pending(self):
        assert TaskStatus.PENDING.is_terminal is False

    def test_is_terminal_in_progress(self):
        assert TaskStatus.IN_PROGRESS.is_terminal is False


class TestContractSeverity:
    def test_all_levels(self):
        assert set(ContractSeverity) == {
            ContractSeverity.WARNING, ContractSeverity.ERROR,
            ContractSeverity.CRITICAL, ContractSeverity.FATAL,
        }

    def test_string_values(self):
        assert ContractSeverity.CRITICAL.value == "critical"


# ===================================================================
# Dataclass Tests
# ===================================================================


class TestAgentCapability:
    def test_default_values(self):
        cap = AgentCapability()
        assert cap.name == ""
        assert cap.confidence == 0.0
        assert cap.usage_count == 0
        assert cap.success_rate == 1.0

    def test_to_dict(self):
        cap = AgentCapability(name="draft", confidence=0.85, domains=["filing"])
        d = cap.to_dict()
        assert d["name"] == "draft"
        assert d["confidence"] == 0.85
        assert "filing" in d["domains"]

    def test_record_usage_success(self):
        cap = AgentCapability(name="cite", confidence=0.9)
        cap.record_usage(True)
        assert cap.usage_count == 1
        assert cap.success_rate == 1.0
        assert cap.last_used != ""

    def test_record_usage_failure(self):
        cap = AgentCapability(name="cite", confidence=0.9)
        cap.record_usage(True)
        cap.record_usage(False)
        assert cap.usage_count == 2
        assert cap.success_rate == 0.5

    def test_record_usage_multiple(self):
        cap = AgentCapability(name="cite")
        for _ in range(8):
            cap.record_usage(True)
        cap.record_usage(False)
        cap.record_usage(False)
        assert cap.usage_count == 10
        assert 0.79 < cap.success_rate < 0.81


class TestBehavioralContract:
    def test_default_severity(self):
        bc = BehavioralContract()
        assert bc.severity == ContractSeverity.ERROR

    def test_to_dict_includes_all_fields(self):
        bc = BehavioralContract(
            name="qa_check",
            invariants=["no_hallucination"],
            pre_conditions=["evidence_loaded"],
            post_conditions=["output_valid"],
        )
        d = bc.to_dict()
        assert d["name"] == "qa_check"
        assert "no_hallucination" in d["invariants"]
        assert d["enabled"] is True

    def test_contract_id_auto_generated(self):
        bc1 = BehavioralContract()
        bc2 = BehavioralContract()
        assert bc1.contract_id != bc2.contract_id


class TestContractViolation:
    def test_to_dict(self):
        v = ContractViolation(
            contract_id="c1", agent_id="a1",
            condition_type="invariant", condition_text="must_not_hallucinate",
            severity=ContractSeverity.CRITICAL,
        )
        d = v.to_dict()
        assert d["severity"] == "critical"
        assert d["condition_type"] == "invariant"


class TestAgentTask:
    def test_can_retry_when_failed(self):
        task = AgentTask(status=TaskStatus.FAILED, retries=0, max_retries=3)
        assert task.can_retry is True

    def test_can_retry_max_reached(self):
        task = AgentTask(status=TaskStatus.FAILED, retries=3, max_retries=3)
        assert task.can_retry is False

    def test_can_retry_not_failed(self):
        task = AgentTask(status=TaskStatus.PENDING, retries=0)
        assert task.can_retry is False

    def test_to_dict_fields(self):
        task = AgentTask(agent_id="ag1", description="Draft motion", lane="A", priority=1)
        d = task.to_dict()
        assert d["lane"] == "A"
        assert d["priority"] == 1


class TestAgentProfile:
    def test_success_rate_no_tasks(self):
        agent = AgentProfile()
        assert agent.success_rate == 0.0

    def test_success_rate_with_tasks(self):
        agent = AgentProfile(total_tasks=10, successful_tasks=8, failed_tasks=2)
        assert agent.success_rate == 0.8

    def test_to_dict_includes_success_rate(self):
        agent = AgentProfile(total_tasks=4, successful_tasks=3, failed_tasks=1)
        d = agent.to_dict()
        assert d["success_rate"] == 0.75


# ===================================================================
# ReActLoop Tests
# ===================================================================


class TestReActLoop:
    def test_init_defaults(self):
        loop = ReActLoop()
        assert loop.iteration == 0
        assert loop.max_iterations == _DEFAULT_MAX_REACT_ITERATIONS
        assert loop.should_continue() is True

    def test_reason_increments_iteration(self):
        loop = ReActLoop(max_iterations=5, name="test")
        thought = loop.reason("initial observation")
        assert loop.iteration == 1
        assert "Iteration 1" in thought

    def test_act_without_handler(self):
        loop = ReActLoop()
        result = loop.act("some plan")
        assert result["action"] == "noop"

    def test_act_with_handler(self):
        loop = ReActLoop()
        loop.set_handlers(
            reason_fn=lambda obs: f"thinking about {obs}",
            act_fn=lambda plan: {"status": "completed", "output": plan},
        )
        result = loop.act("execute motion draft")
        assert result["status"] == "completed"

    def test_observe_produces_summary(self):
        loop = ReActLoop()
        loop.reason("start")
        obs = loop.observe({"status": "success", "summary": "Filed motion"})
        assert "success" in obs

    def test_should_continue_max_iterations(self):
        loop = ReActLoop(max_iterations=2)
        loop.reason("obs1")
        loop.reason("obs2")
        assert loop.should_continue() is False

    def test_mark_complete_stops_loop(self):
        loop = ReActLoop(max_iterations=100)
        loop.mark_complete()
        assert loop.should_continue() is False

    def test_get_history(self):
        loop = ReActLoop()
        loop.reason("test")
        loop.act("plan")
        history = loop.get_history()
        assert len(history) == 2

    def test_get_stats(self):
        loop = ReActLoop(name="test_loop", max_iterations=5)
        loop.reason("obs")
        stats = loop.get_stats()
        assert stats["name"] == "test_loop"
        assert stats["iterations"] == 1
        assert stats["complete"] is False

    def test_full_react_cycle(self):
        loop = ReActLoop(max_iterations=3, name="cycle_test")
        loop.set_handlers(
            reason_fn=lambda obs: "plan step",
            act_fn=lambda plan: {"status": "completed"},
        )
        while loop.should_continue():
            thought = loop.reason("observe")
            result = loop.act(thought)
            loop.observe(result)
            if result.get("status") == "completed":
                loop.mark_complete()
        assert loop.iteration == 1


# ===================================================================
# PlanAndExecute Tests
# ===================================================================


class TestPlanAndExecute:
    def test_decompose_simple_task(self):
        pe = PlanAndExecute(name="test")
        steps = pe.decompose_task("gather evidence")
        assert len(steps) == 1
        assert steps[0]["description"] == "gather evidence"

    def test_decompose_multi_part_task(self):
        pe = PlanAndExecute(name="multi")
        steps = pe.decompose_task("gather evidence; draft motion; file")
        assert len(steps) == 3

    def test_decompose_with_context(self):
        pe = PlanAndExecute(name="ctx")
        steps = pe.decompose_task("draft", context={"lane": "A"})
        assert steps[0]["inputs"]["lane"] == "A"

    def test_execute_step_default(self):
        pe = PlanAndExecute(name="exec")
        steps = pe.decompose_task("single step")
        result = pe.execute_step(steps[0])
        assert result["status"] == "completed"

    def test_execute_step_with_handler(self):
        pe = PlanAndExecute(name="handler")
        steps = pe.decompose_task("custom step")
        result = pe.execute_step(
            steps[0], handler=lambda s: {"status": "completed", "custom": True}
        )
        assert result["custom"] is True

    def test_execute_step_failure(self):
        pe = PlanAndExecute(name="fail")
        steps = pe.decompose_task("will fail")

        def failing_handler(s):
            raise ValueError("intentional failure")

        result = pe.execute_step(steps[0], handler=failing_handler)
        assert result["status"] == "failed"
        assert "intentional failure" in result["error"]

    def test_replan_after_failure(self):
        pe = PlanAndExecute(name="replan")
        pe.decompose_task("step1; step2; step3")
        results = [{"status": "failed", "step_id": "replan-step-0", "summary": "failed step"}]
        new_steps = pe.replan(results)
        assert any("Retry" in s["description"] for s in new_steps)

    def test_checkpoint(self):
        pe = PlanAndExecute(name="cp")
        pe.checkpoint({"step": 1})
        progress = pe.get_progress()
        assert progress["checkpoints"] == 1

    def test_get_progress(self):
        pe = PlanAndExecute(name="progress")
        pe.decompose_task("a; b; c")
        pe.execute_step(pe._steps[0])
        progress = pe.get_progress()
        assert progress["completed"] == 1
        assert progress["total_steps"] == 3

    def test_get_stats_includes_results(self):
        pe = PlanAndExecute(name="stats")
        pe.decompose_task("step")
        pe.execute_step(pe._steps[0])
        stats = pe.get_stats()
        assert "results" in stats
        assert len(stats["results"]) == 1


# ===================================================================
# ToolRegistry Tests
# ===================================================================


class TestToolRegistry:
    def test_register_tool(self):
        reg = ToolRegistry()
        reg.register("search", {"type": "object"}, description="Search evidence")
        assert "search" in reg.get_stats()["tool_names"]

    def test_register_with_handler(self):
        reg = ToolRegistry()
        reg.register("calc", {"type": "object"}, handler=lambda **kw: 42)
        stats = reg.get_stats()
        assert stats["tools_with_handlers"] == 1

    def test_select_tools_keyword_match(self):
        reg = ToolRegistry()
        reg.register("evidence_search", {"type": "object"}, description="Search evidence database")
        reg.register("filing_format", {"type": "object"}, description="Format court filings")
        results = reg.select_tools("search evidence")
        assert len(results) >= 1
        assert results[0]["name"] == "evidence_search"

    def test_select_tools_domain_bonus(self):
        reg = ToolRegistry()
        reg.register("tool_a", {"type": "object"}, description="generic", domains=["custody"])
        reg.register("tool_b", {"type": "object"}, description="generic", domains=["housing"])
        results = reg.select_tools("custody dispute")
        assert results[0]["name"] == "tool_a"

    def test_select_tools_limit(self):
        reg = ToolRegistry()
        for i in range(10):
            reg.register(f"tool_{i}", {"type": "object"}, description=f"tool {i}")
        results = reg.select_tools("tool", limit=3)
        assert len(results) <= 3

    def test_execute_tool_success(self):
        reg = ToolRegistry()
        reg.register("add", {"type": "object"}, handler=lambda x=0, y=0: x + y)
        result = reg.execute_tool("add", x=3, y=4)
        assert result["status"] == "success"
        assert result["result"] == 7

    def test_execute_tool_no_handler(self):
        reg = ToolRegistry()
        reg.register("no_handler", {"type": "object"})
        result = reg.execute_tool("no_handler")
        assert result["status"] == "error"

    def test_execute_tool_handler_exception(self):
        reg = ToolRegistry()
        def bad_handler(**kw):
            raise RuntimeError("tool broke")
        reg.register("bad", {"type": "object"}, handler=bad_handler)
        result = reg.execute_tool("bad")
        assert result["status"] == "error"

    def test_track_usage(self):
        reg = ToolRegistry()
        reg.track_usage("my_tool", {"success": True})
        stats = reg.get_stats()
        assert "my_tool" in stats["usage"]
        assert stats["usage"]["my_tool"]["total_uses"] == 1

    def test_get_stats_comprehensive(self):
        reg = ToolRegistry()
        reg.register("t1", {"type": "object"}, handler=lambda: None)
        reg.register("t2", {"type": "object"})
        stats = reg.get_stats()
        assert stats["total_tools"] == 2
        assert stats["tools_with_handlers"] == 1


# ===================================================================
# AgentMemory Tests
# ===================================================================


class TestAgentMemory:
    def test_short_term_store_and_get(self):
        mem = AgentMemory()
        mem.store_short_term("key1", "value1")
        assert mem.get_short_term("key1") == "value1"

    def test_short_term_missing_key(self):
        mem = AgentMemory()
        assert mem.get_short_term("nonexistent") is None

    def test_clear_short_term(self):
        mem = AgentMemory()
        mem.store_short_term("k", "v")
        mem.clear_short_term()
        assert mem.get_short_term("k") is None

    def test_long_term_store_and_get(self):
        mem = AgentMemory(ttl_hours=24)
        mem.store_long_term("evidence_list", ["doc1", "doc2"])
        assert mem.get_long_term("evidence_list") == ["doc1", "doc2"]

    def test_long_term_custom_ttl(self):
        mem = AgentMemory(ttl_hours=1)
        mem.store_long_term("key", "val", ttl_hours=100)
        assert mem.get_long_term("key") == "val"

    def test_long_term_missing_key(self):
        mem = AgentMemory()
        assert mem.get_long_term("missing") is None

    def test_long_term_access_count(self):
        mem = AgentMemory()
        mem.store_long_term("counter_test", 42)
        mem.get_long_term("counter_test")
        mem.get_long_term("counter_test")
        assert mem._long_term["counter_test"]["access_count"] == 2

    def test_retrieve_by_keyword(self):
        mem = AgentMemory()
        mem.store_long_term("custody_evidence", "Documents about custody")
        mem.store_long_term("housing_docs", "Lease agreements")
        results = mem.retrieve("custody")
        assert len(results) >= 1
        assert results[0]["key"] == "custody_evidence"

    def test_retrieve_limit(self):
        mem = AgentMemory()
        for i in range(20):
            mem.store_long_term(f"item_{i}", f"data about evidence {i}")
        results = mem.retrieve("evidence", limit=5)
        assert len(results) <= 5

    def test_retrieve_empty_query(self):
        mem = AgentMemory()
        mem.store_long_term("something", "data")
        results = mem.retrieve("")
        assert isinstance(results, list)

    def test_forget_stale_removes_expired(self):
        mem = AgentMemory(ttl_hours=0)
        mem.store_long_term("old_data", "expired", ttl_hours=0)
        # Manually set expired timestamp
        key = "old_data"
        mem._long_term[key]["expires_at"] = (
            datetime.now(timezone.utc) - timedelta(hours=1)
        ).isoformat()
        removed = mem.forget_stale()
        assert removed == 1
        assert mem.get_long_term("old_data") is None

    def test_forget_stale_keeps_valid(self):
        mem = AgentMemory(ttl_hours=100)
        mem.store_long_term("fresh", "still valid")
        removed = mem.forget_stale()
        assert removed == 0
        assert mem.get_long_term("fresh") == "still valid"

    def test_get_stats(self):
        mem = AgentMemory(ttl_hours=48)
        mem.store_short_term("s1", "v1")
        mem.store_long_term("l1", "v2")
        stats = mem.get_stats()
        assert stats["short_term_count"] == 1
        assert stats["long_term_count"] == 1
        assert stats["ttl_hours"] == 48


# ===================================================================
# ContractValidator Tests
# ===================================================================


class TestContractValidator:
    def test_check_pre_conditions_pass(self):
        cv = ContractValidator()
        contract = BehavioralContract(pre_conditions=["task_assigned"])
        violations = cv.check_pre_conditions(
            contract, {"task_assigned": True}, agent_id="a1"
        )
        assert len(violations) == 0

    def test_check_pre_conditions_fail(self):
        cv = ContractValidator()
        contract = BehavioralContract(pre_conditions=["task_assigned"])
        violations = cv.check_pre_conditions(
            contract, {"task_assigned": False}, agent_id="a1"
        )
        assert len(violations) == 1

    def test_check_pre_conditions_disabled_contract(self):
        cv = ContractValidator()
        contract = BehavioralContract(pre_conditions=["x"], enabled=False)
        violations = cv.check_pre_conditions(contract, {"x": False})
        assert len(violations) == 0

    def test_check_post_conditions_pass(self):
        cv = ContractValidator()
        contract = BehavioralContract(post_conditions=["output_valid"])
        violations = cv.check_post_conditions(
            contract, {"output_valid": True}
        )
        assert len(violations) == 0

    def test_check_post_conditions_fail(self):
        cv = ContractValidator()
        contract = BehavioralContract(post_conditions=["output_valid"])
        violations = cv.check_post_conditions(
            contract, {"output_valid": False}, agent_id="a2"
        )
        assert len(violations) == 1
        assert violations[0].condition_type == "post_condition"

    def test_check_invariants_pass(self):
        cv = ContractValidator()
        contract = BehavioralContract(invariants=["no_hallucination"])
        violations = cv.check_invariants(
            contract, {"no_hallucination": True}
        )
        assert len(violations) == 0

    def test_check_invariants_fail(self):
        cv = ContractValidator()
        contract = BehavioralContract(invariants=["no_hallucination"])
        violations = cv.check_invariants(
            contract, {"no_hallucination": False}, agent_id="a3"
        )
        assert len(violations) == 1
        assert violations[0].severity == ContractSeverity.CRITICAL

    def test_evaluate_condition_key_with_spaces(self):
        result = ContractValidator._evaluate_condition("task assigned", {"task_assigned": True})
        assert result is True

    def test_evaluate_condition_unresolvable_passes(self):
        result = ContractValidator._evaluate_condition("unknown_condition", {})
        assert result is True

    def test_get_violations_filtered(self):
        cv = ContractValidator()
        contract = BehavioralContract(pre_conditions=["check"])
        cv.check_pre_conditions(contract, {"check": False}, agent_id="agent_x")
        cv.check_pre_conditions(contract, {"check": False}, agent_id="agent_y")
        viol_x = cv.get_violations(agent_id="agent_x")
        assert len(viol_x) == 1

    def test_get_stats(self):
        cv = ContractValidator()
        contract = BehavioralContract(pre_conditions=["c"], severity=ContractSeverity.WARNING)
        cv.check_pre_conditions(contract, {"c": False})
        stats = cv.get_stats()
        assert stats["total_violations"] == 1
        assert "warning" in stats["by_severity"]


# ===================================================================
# AutonomousAgentFramework Tests
# ===================================================================


class TestFrameworkInit:
    def test_initialize(self, tmp_db):
        fw = AutonomousAgentFramework(db_path=tmp_db)
        result = fw.initialize()
        assert result["status"] == "initialized"

    def test_double_initialize(self, framework):
        result = framework.initialize()
        assert result["status"] == "already_initialized"


class TestFrameworkAgentCRUD:
    def test_create_agent(self, framework, sample_agent_config):
        agent = framework.create_agent(sample_agent_config)
        assert agent["name"] == "test-filing-agent"
        assert len(agent["capabilities"]) == 3
        assert len(agent["contracts"]) == 1

    def test_create_agent_with_string_capabilities(self, framework):
        agent = framework.create_agent({
            "name": "simple", "capabilities": ["draft", "format"]
        })
        assert len(agent["capabilities"]) == 2

    def test_get_agent(self, framework, sample_agent_config):
        created = framework.create_agent(sample_agent_config)
        retrieved = framework.get_agent(created["agent_id"])
        assert retrieved is not None
        assert retrieved["name"] == "test-filing-agent"

    def test_get_agent_not_found(self, framework):
        assert framework.get_agent("nonexistent") is None

    def test_list_agents_empty(self, framework):
        assert framework.list_agents() == []

    def test_list_agents_after_creation(self, framework, sample_agent_config):
        framework.create_agent(sample_agent_config)
        agents = framework.list_agents()
        assert len(agents) == 1


class TestFrameworkTaskExecution:
    def test_run_simple_task(self, framework, sample_agent_config):
        agent = framework.create_agent(sample_agent_config)
        result = framework.run_agent(agent["agent_id"], task="Draft motion for Lane A")
        assert result["status"] in ("completed", "failed")

    def test_run_complex_task_semicolons(self, framework, sample_agent_config):
        agent = framework.create_agent(sample_agent_config)
        result = framework.run_agent(
            agent["agent_id"],
            task="Gather evidence; Draft motion; File with court",
            lane="A",
        )
        assert result["status"] in ("completed", "failed")

    def test_run_agent_not_found(self, framework):
        result = framework.run_agent("fake_id", task="test")
        assert result["status"] == "error"

    def test_run_agent_max_concurrent(self, framework):
        agents = []
        for i in range(_MAX_CONCURRENT_AGENTS + 1):
            a = framework.create_agent({"name": f"agent_{i}", "capabilities": ["work"]})
            agents.append(a)
        # Force agents into active state
        for i in range(_MAX_CONCURRENT_AGENTS):
            aid = agents[i]["agent_id"]
            framework._agents[aid].state = AgentState.EXECUTING
        result = framework.run_agent(
            agents[_MAX_CONCURRENT_AGENTS]["agent_id"], task="blocked task"
        )
        assert result["status"] == "blocked"

    def test_run_agent_updates_task_history(self, framework, sample_agent_config):
        agent = framework.create_agent(sample_agent_config)
        framework.run_agent(agent["agent_id"], task="Task 1")
        updated = framework.get_agent(agent["agent_id"])
        assert updated["total_tasks"] == 1


class TestFrameworkMonitoring:
    def test_monitor_agents_empty(self, framework):
        status = framework.monitor_agents()
        assert status["total_agents"] == 0

    def test_monitor_agents_with_agents(self, framework, sample_agent_config):
        framework.create_agent(sample_agent_config)
        status = framework.monitor_agents()
        assert status["total_agents"] == 1
        assert len(status["idle"]) == 1


class TestFrameworkEvaluation:
    def test_evaluate_performance_empty(self, framework):
        result = framework.evaluate_performance()
        assert result["evaluations"] == []

    def test_evaluate_performance_single(self, framework, sample_agent_config):
        agent = framework.create_agent(sample_agent_config)
        framework.run_agent(agent["agent_id"], task="task1")
        result = framework.evaluate_performance(agent["agent_id"])
        assert len(result["evaluations"]) == 1

    def test_grade_agent_na(self):
        agent = AgentProfile(total_tasks=1, successful_tasks=1)
        assert AutonomousAgentFramework._grade_agent(agent) == "N/A"

    def test_grade_agent_a(self):
        agent = AgentProfile(total_tasks=20, successful_tasks=19, failed_tasks=1)
        assert AutonomousAgentFramework._grade_agent(agent) == "A"

    def test_grade_agent_f(self):
        agent = AgentProfile(total_tasks=10, successful_tasks=2, failed_tasks=8)
        assert AutonomousAgentFramework._grade_agent(agent) == "F"


class TestFrameworkEvolution:
    def test_evolve_capabilities_empty(self, framework):
        result = framework.evolve_capabilities()
        assert result["agents_analyzed"] == 0

    def test_evolve_capabilities_suggestions(self, framework):
        agent = framework.create_agent({
            "name": "underperformer",
            "capabilities": [{"name": "bad_cap", "confidence": 0.5}],
        })
        aid = agent["agent_id"]
        # Simulate usage
        cap = framework._agents[aid].capabilities[0]
        for _ in range(10):
            cap.record_usage(False)
        framework._agents[aid].total_tasks = 15
        framework._agents[aid].successful_tasks = 5
        framework._agents[aid].failed_tasks = 10
        result = framework.evolve_capabilities()
        assert result["total_suggestions"] > 0


class TestFrameworkStats:
    def test_get_stats_initialized(self, framework):
        stats = framework.get_stats()
        assert stats["initialized"] is True
        assert stats["agents"]["total"] == 0
        assert "tools" in stats
        assert "memory" in stats
        assert "contracts" in stats


# ===================================================================
# Constants & Case Data Tests
# ===================================================================


class TestCaseConstants:
    def test_plaintiff(self):
        assert _PLAINTIFF == "Andrew James Pigors"

    def test_defendant(self):
        assert _DEFENDANT == "Emily A. Watson"

    def test_child_initials(self):
        assert _CHILD_INITIALS == "L.D.W."

    def test_lane_cases_keys(self):
        assert set(LANE_CASES.keys()) == {"A", "B", "C", "D", "E", "F"}

    def test_lane_a_case_number(self):
        assert LANE_CASES["A"] == "2024-001507-DC"
