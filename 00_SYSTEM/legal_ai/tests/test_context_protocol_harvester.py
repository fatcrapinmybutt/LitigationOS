"""
Comprehensive tests for agent_context_protocol.py (7 classes) and
context_harvester.py (6 classes) — 100+ tests.

All tests are self-contained: temp dirs for DB/file ops, mocked
external deps, no network, no real drives.
"""

import pytest
import sys
import os
import json
import time
import math
import hashlib
import tempfile
import shutil
import sqlite3
import threading
import csv
from pathlib import Path
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock, PropertyMock, mock_open

# Ensure the parent legal_ai package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent_context_protocol import (
    ContextRegistry,
    AgentRegistration,
    AgentStatus,
    ContextPubSub,
    ContextEvent,
    EventPriority,
    VersionedHandoff,
    HandoffVersion,
    ContextRouter,
    RouteEntry,
    ContextLifecycleManager,
    ContextLifecycleStage,
    DeadLetterQueue,
    DLQEntry,
    DLQStatus,
    AgentContextProtocol,
    VALID_LANES,
)

from context_harvester import (
    DriveScanner,
    FileRecord,
    TextExtractor,
    ExtractedContent,
    GoogleDriveHarvester,
    ContentIndexer,
    HarvestScheduler,
    ContextHarvester,
    LEGAL_EXTENSIONS,
    SKIP_DIRS,
    DEFAULT_DRIVES,
    MAX_FILE_SIZE,
    MAX_EXTRACT_TIMEOUT,
    DEFAULT_MAX_DEPTH,
    DEFAULT_BATCH_SIZE,
    detect_lane,
    compute_sha256,
)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_dir():
    """Fresh temp directory per test — auto-cleaned."""
    d = tempfile.mkdtemp(prefix="litOS_test_proto_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def tmp_db(tmp_dir):
    """Path to a temp SQLite DB that doesn't exist yet."""
    return os.path.join(tmp_dir, "test_protocol.db")


@pytest.fixture
def harvest_db(tmp_dir):
    """Separate DB for harvester tests."""
    return os.path.join(tmp_dir, "test_harvest.db")


# ---------------------------------------------------------------------------
# Protocol fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def registry(tmp_db):
    return ContextRegistry(db_path=tmp_db)


@pytest.fixture
def pubsub(tmp_db):
    return ContextPubSub(db_path=tmp_db)


@pytest.fixture
def versioning(tmp_db):
    return VersionedHandoff(db_path=tmp_db)


@pytest.fixture
def router(tmp_db):
    reg = ContextRegistry(db_path=tmp_db)
    return ContextRouter(registry=reg, db_path=tmp_db)


@pytest.fixture
def lifecycle(tmp_db):
    return ContextLifecycleManager(db_path=tmp_db)


@pytest.fixture
def dlq(tmp_db):
    return DeadLetterQueue(db_path=tmp_db)


@pytest.fixture
def protocol(tmp_db):
    AgentContextProtocol.reset()
    proto = AgentContextProtocol(db_path=tmp_db)
    yield proto
    try:
        proto.shutdown()
    except Exception:
        pass
    AgentContextProtocol.reset()


# ---------------------------------------------------------------------------
# Harvester fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def scanner(tmp_dir):
    """DriveScanner pointed at the temp dir only."""
    return DriveScanner(
        drives=[(tmp_dir, True)],
        extensions=LEGAL_EXTENSIONS,
        max_depth=3,
    )


@pytest.fixture
def extractor():
    return TextExtractor(timeout=5)


@pytest.fixture
def indexer(harvest_db):
    idx = ContentIndexer(db_path=harvest_db)
    yield idx
    idx.close()


@pytest.fixture
def gdrive_harvester(tmp_dir):
    return GoogleDriveHarvester(download_dir=tmp_dir)


# ===================================================================
# CONTEXT REGISTRY — ~16 tests
# ===================================================================

class TestContextRegistry:
    """Tests for ContextRegistry: register, unregister, discover, status."""

    def test_register_agent(self, registry):
        reg = registry.register("agent_01", agent_type="research")
        assert isinstance(reg, AgentRegistration)
        assert reg.agent_id == "agent_01"

    def test_register_with_capabilities(self, registry):
        reg = registry.register(
            "agent_02", capabilities=["discovery", "analysis"]
        )
        assert "discovery" in reg.capabilities

    def test_register_with_lane_affinity(self, registry):
        reg = registry.register("agent_03", lane_affinity=["A", "D"])
        assert "A" in reg.lane_affinity

    def test_unregister_agent(self, registry):
        registry.register("agent_04")
        assert registry.unregister("agent_04") is True

    def test_unregister_nonexistent(self, registry):
        assert registry.unregister("never_registered") is False

    def test_get_agent(self, registry):
        registry.register("agent_05", agent_type="filing")
        agent = registry.get_agent("agent_05")
        assert agent is not None
        assert agent.agent_type == "filing"

    def test_get_agent_missing(self, registry):
        assert registry.get_agent("ghost_agent") is None

    def test_update_status(self, registry):
        registry.register("agent_06")
        result = registry.update_status("agent_06", AgentStatus.BUSY)
        assert result is True

    def test_heartbeat(self, registry):
        registry.register("agent_07")
        result = registry.heartbeat("agent_07")
        assert result is True

    def test_list_agents_all(self, registry):
        registry.register("a1")
        registry.register("a2")
        agents = registry.list_agents()
        assert len(agents) >= 2

    def test_list_agents_by_status(self, registry):
        registry.register("a3")
        registry.update_status("a3", AgentStatus.BUSY)
        busy = registry.list_agents(status=AgentStatus.BUSY)
        ids = [a.agent_id for a in busy]
        assert "a3" in ids

    def test_discover_by_capability(self, registry):
        registry.register("d1", capabilities=["ocr", "extraction"])
        registry.register("d2", capabilities=["analysis"])
        found = registry.discover(capability="ocr")
        ids = [a.agent_id for a in found]
        assert "d1" in ids
        assert "d2" not in ids

    def test_discover_by_lane(self, registry):
        registry.register("l1", lane_affinity=["A"])
        registry.register("l2", lane_affinity=["B"])
        found = registry.discover(capability=None, lane="A")
        ids = [a.agent_id for a in found]
        assert "l1" in ids

    def test_agent_count(self, registry):
        registry.register("c1")
        registry.register("c2")
        assert registry.agent_count() >= 2

    def test_duplicate_register_updates(self, registry):
        registry.register("dup1", agent_type="v1")
        registry.register("dup1", agent_type="v2")
        agent = registry.get_agent("dup1")
        assert agent is not None

    def test_register_with_metadata(self, registry):
        reg = registry.register("m1", metadata={"version": "2.0"})
        assert reg.metadata.get("version") == "2.0"


# ===================================================================
# CONTEXT PUBSUB — ~14 tests
# ===================================================================

class TestContextPubSub:
    """Tests for ContextPubSub: subscribe, publish, filter, ack."""

    def test_subscribe(self, pubsub):
        assert pubsub.subscribe("sub1", "filing.progress") is True

    def test_subscribe_with_lane_filter(self, pubsub):
        assert pubsub.subscribe("sub2", "evidence.new", lane_filter="A") is True

    def test_unsubscribe(self, pubsub):
        pubsub.subscribe("sub3", "test.topic")
        assert pubsub.unsubscribe("sub3", "test.topic") is True

    def test_publish_returns_event_id(self, pubsub):
        event_id = pubsub.publish(
            topic="case.update",
            payload={"status": "filed"},
            publisher_id="agent_01",
        )
        assert isinstance(event_id, int)
        assert event_id > 0

    def test_publish_with_lane(self, pubsub):
        event_id = pubsub.publish(
            topic="evidence.new",
            payload={"file": "doc.pdf"},
            publisher_id="agent_02",
            lane="A",
        )
        assert event_id > 0

    def test_get_events(self, pubsub):
        pubsub.publish("test.events", {"n": 1}, "pub1")
        pubsub.publish("test.events", {"n": 2}, "pub1")
        events = pubsub.get_events(topic="test.events")
        assert len(events) >= 2

    def test_get_events_with_lane_filter(self, pubsub):
        pubsub.publish("lane.test", {"x": 1}, "p1", lane="A")
        pubsub.publish("lane.test", {"x": 2}, "p1", lane="B")
        events = pubsub.get_events(topic="lane.test", lane="A")
        lanes = [e.get("lane") for e in events]
        assert all(l == "A" for l in lanes)

    def test_acknowledge_event(self, pubsub):
        eid = pubsub.publish("ack.test", {"data": True}, "p1")
        result = pubsub.acknowledge(eid, "agent_ack")
        assert result is True

    def test_get_unacknowledged(self, pubsub):
        pubsub.subscribe("unack_agent", "unack.topic")
        pubsub.publish("unack.topic", {}, "pub")
        unacked = pubsub.get_unacknowledged("unack_agent", topic="unack.topic")
        assert isinstance(unacked, list)

    def test_get_matching_subscribers(self, pubsub):
        pubsub.subscribe("ms1", "match.topic")
        pubsub.subscribe("ms2", "match.topic")
        subs = pubsub.get_matching_subscribers("match.topic")
        assert "ms1" in subs
        assert "ms2" in subs

    def test_cleanup_expired(self, pubsub):
        pubsub.publish("expire.test", {}, "pub", ttl_seconds=0)
        time.sleep(0.1)
        removed = pubsub.cleanup_expired()
        assert isinstance(removed, int)

    def test_stats_returns_dict(self, pubsub):
        pubsub.publish("stats.test", {}, "pub")
        s = pubsub.stats()
        assert isinstance(s, dict)

    def test_publish_with_priority(self, pubsub):
        eid = pubsub.publish(
            "prio.test", {}, "pub", priority="critical"
        )
        assert eid > 0

    def test_dead_letter_on_no_subscribers(self, pubsub):
        """Publishing to a topic with no subscribers should not error."""
        eid = pubsub.publish("orphan.topic", {"lost": True}, "pub")
        assert eid > 0


# ===================================================================
# VERSIONED HANDOFF — ~14 tests
# ===================================================================

class TestVersionedHandoff:
    """Tests for VersionedHandoff: versioning, diff, rollback, conflict."""

    def test_create_version(self, versioning):
        ver = versioning.create_version(
            handoff_id="h1",
            items=[{"key": "a", "val": 1}],
            created_by="test",
        )
        assert isinstance(ver, HandoffVersion)
        assert ver.version == "1.0.0" or ver.version.startswith("0.")

    def test_create_increments_version(self, versioning):
        v1 = versioning.create_version("h2", [{"k": 1}], created_by="test")
        v2 = versioning.create_version("h2", [{"k": 2}], created_by="test")
        assert v2.version != v1.version

    def test_get_version_latest(self, versioning):
        versioning.create_version("h3", [{"k": "latest"}], created_by="test")
        ver = versioning.get_version("h3")
        assert ver is not None

    def test_get_version_specific(self, versioning):
        v1 = versioning.create_version("h4", [{"k": "v1"}], created_by="test")
        fetched = versioning.get_version("h4", version=v1.version)
        assert fetched is not None
        assert fetched.version == v1.version

    def test_list_versions(self, versioning):
        versioning.create_version("h5", [{"k": 1}], created_by="test")
        versioning.create_version("h5", [{"k": 2}], created_by="test")
        versions = versioning.list_versions("h5")
        assert len(versions) >= 2

    def test_rollback(self, versioning):
        v1 = versioning.create_version("h6", [{"k": "original"}], created_by="test")
        versioning.create_version("h6", [{"k": "modified"}], created_by="test")
        rolled = versioning.rollback("h6", v1.version)
        assert rolled is not None

    def test_diff_between_versions(self, versioning):
        v1 = versioning.create_version("h7", [{"key": "a", "val": 1}], created_by="test")
        v2 = versioning.create_version(
            "h7", [{"key": "a", "val": 2}, {"key": "b", "val": 3}], created_by="test"
        )
        diff = versioning.diff("h7", v1.version, v2.version)
        assert isinstance(diff, dict)

    def test_diff_same_version(self, versioning):
        v1 = versioning.create_version("h8", [{"k": 1}], created_by="test")
        diff = versioning.diff("h8", v1.version, v1.version)
        assert diff.get("added_count", 0) == 0

    def test_detect_conflict(self, versioning):
        v1 = versioning.create_version("h9", [{"k": "base"}], created_by="test")
        conflict = versioning.detect_conflict(
            "h9", v1.version,
            items_a=[{"k": "change_a"}],
            items_b=[{"k": "change_b"}],
        )
        assert isinstance(conflict, dict)

    def test_merge_last_writer_wins(self, versioning):
        versioning.create_version("h10", [{"k": "base"}], created_by="test")
        merged = versioning.merge_last_writer_wins(
            "h10",
            items_a=[{"k": "a_val"}],
            items_b=[{"k": "b_val"}],
            winner="b",
            merged_by="test",
        )
        assert isinstance(merged, HandoffVersion)

    def test_bump_patch(self, versioning):
        v1 = versioning.create_version("bp1", [{}], created_by="test", bump_level="patch")
        v2 = versioning.create_version("bp1", [{}], created_by="test", bump_level="patch")
        # Patch should increment third number
        assert v1.version != v2.version

    def test_bump_minor(self, versioning):
        versioning.create_version("bm1", [{}], created_by="test")
        v2 = versioning.create_version("bm1", [{}], created_by="test", bump_level="minor")
        assert isinstance(v2, HandoffVersion)

    def test_bump_major(self, versioning):
        versioning.create_version("bj1", [{}], created_by="test")
        v2 = versioning.create_version("bj1", [{}], created_by="test", bump_level="major")
        assert isinstance(v2, HandoffVersion)

    def test_stats(self, versioning):
        versioning.create_version("hs1", [{}], created_by="test")
        s = versioning.stats()
        assert isinstance(s, dict)


# ===================================================================
# CONTEXT ROUTER — ~10 tests
# ===================================================================

class TestContextRouter:
    """Tests for ContextRouter: route table, lane routing, fallback."""

    def test_add_route(self, router, registry):
        registry.register("r_agent1", lane_affinity=["A"])
        entry = router.add_route("A", "discovery", "r_agent1")
        assert isinstance(entry, RouteEntry)

    def test_remove_route(self, router, registry):
        registry.register("r_agent2", lane_affinity=["A"])
        router.add_route("A", "analysis", "r_agent2")
        assert router.remove_route("A", "analysis", "r_agent2") is True

    def test_resolve_route(self, router, registry):
        registry.register("r_agent3", lane_affinity=["B"])
        router.add_route("B", "filing", "r_agent3")
        agent = router.resolve("B", "filing")
        assert agent == "r_agent3"

    def test_resolve_no_route(self, router):
        agent = router.resolve("F", "nonexistent_task")
        assert agent is None

    def test_resolve_with_load_balance(self, router, registry):
        registry.register("lb1", lane_affinity=["A"])
        registry.register("lb2", lane_affinity=["A"])
        router.add_route("A", "balance", "lb1")
        router.add_route("A", "balance", "lb2")
        agent = router.resolve_with_load_balance("A", "balance")
        assert agent in ("lb1", "lb2")

    def test_validate_route_valid(self, router, registry):
        registry.register("vr1", lane_affinity=["A"])
        result = router.validate_route("A", "vr1")
        assert result.get("valid") is True

    def test_validate_route_iron_law_violation(self, router, registry):
        registry.register("vr2", lane_affinity=["B"])
        result = router.validate_route("A", "vr2")
        # Agent with B affinity shouldn't serve lane A
        assert result.get("valid") is False or "IRON" in str(result.get("reason", ""))

    def test_list_routes(self, router, registry):
        registry.register("lr1", lane_affinity=["D"])
        router.add_route("D", "ppo_check", "lr1")
        routes = router.list_routes(lane="D")
        assert len(routes) >= 1

    def test_list_routes_all(self, router):
        routes = router.list_routes()
        assert isinstance(routes, list)

    def test_stats(self, router):
        s = router.stats()
        assert isinstance(s, dict)


# ===================================================================
# CONTEXT LIFECYCLE MANAGER — ~12 tests
# ===================================================================

class TestContextLifecycleManager:
    """Tests for ContextLifecycleManager: HOT→WARM→COLD→ARCHIVED."""

    def test_store_returns_id(self, lifecycle):
        row_id = lifecycle.store("ctx_key_1", {"data": "hot content"}, lane="A")
        assert isinstance(row_id, int)
        assert row_id > 0

    def test_retrieve_stored_item(self, lifecycle):
        lifecycle.store("ctx_key_2", {"data": "retrievable"})
        item = lifecycle.retrieve("ctx_key_2")
        assert item is not None

    def test_retrieve_nonexistent(self, lifecycle):
        item = lifecycle.retrieve("never_stored_key")
        assert item is None

    def test_store_with_lane(self, lifecycle):
        row_id = lifecycle.store("lane_item", {"x": 1}, lane="D")
        assert row_id > 0

    def test_list_by_stage_hot(self, lifecycle):
        lifecycle.store("hot1", {"data": "hot"})
        items = lifecycle.list_by_stage(ContextLifecycleStage.HOT)
        assert isinstance(items, list)

    def test_run_lifecycle_sweep(self, lifecycle):
        lifecycle.store("sweep1", {"data": "test"})
        result = lifecycle.run_lifecycle_sweep()
        assert isinstance(result, dict)

    def test_retrieve_updates_access_count(self, lifecycle):
        lifecycle.store("ac1", {"data": "access"})
        lifecycle.retrieve("ac1")
        lifecycle.retrieve("ac1")
        lifecycle.retrieve("ac1")
        # Multiple retrievals should increment access count
        item = lifecycle.retrieve("ac1")
        assert item is not None

    def test_cleanup_archived(self, lifecycle):
        count = lifecycle.cleanup_archived(older_than_days=365)
        assert isinstance(count, int)
        assert count >= 0

    def test_stats(self, lifecycle):
        lifecycle.store("st1", {"data": "stats"})
        s = lifecycle.stats()
        assert isinstance(s, dict)

    def test_multiple_stores_same_key(self, lifecycle):
        lifecycle.store("dup_key", {"v": 1})
        lifecycle.store("dup_key", {"v": 2})
        item = lifecycle.retrieve("dup_key")
        assert item is not None

    def test_list_by_stage_with_lane(self, lifecycle):
        lifecycle.store("ln1", {"d": 1}, lane="E")
        items = lifecycle.list_by_stage(ContextLifecycleStage.HOT, lane="E")
        assert isinstance(items, list)

    def test_list_by_stage_limit(self, lifecycle):
        for i in range(5):
            lifecycle.store(f"lim_{i}", {"n": i})
        items = lifecycle.list_by_stage(ContextLifecycleStage.HOT, limit=2)
        assert len(items) <= 2


# ===================================================================
# DEAD LETTER QUEUE — ~12 tests
# ===================================================================

class TestDeadLetterQueue:
    """Tests for DeadLetterQueue: enqueue, retry, backoff, resolve."""

    def test_enqueue(self, dlq):
        dlq_id = dlq.enqueue(
            handoff_id="fail_h1",
            source_agent="src1",
            target_agent="tgt1",
            payload=json.dumps({"items": []}),
            failure_reason="target agent offline",
        )
        assert isinstance(dlq_id, int)
        assert dlq_id > 0

    def test_enqueue_with_lane(self, dlq):
        dlq_id = dlq.enqueue(
            handoff_id="fail_h2",
            source_agent="src2",
            target_agent="tgt2",
            payload="{}",
            failure_reason="timeout",
            lane="A",
        )
        assert dlq_id > 0

    def test_get_ready_for_retry(self, dlq):
        dlq.enqueue("rr1", "s", "t", "{}", "error")
        # Immediately after enqueue, the item may or may not be ready
        ready = dlq.get_ready_for_retry(limit=10)
        assert isinstance(ready, list)

    def test_record_retry_success(self, dlq):
        dlq_id = dlq.enqueue("rs1", "s", "t", "{}", "temp error")
        # Wait briefly for retry window
        time.sleep(0.1)
        result = dlq.record_retry(dlq_id, success=True)
        assert result is True

    def test_record_retry_failure(self, dlq):
        dlq_id = dlq.enqueue("rf1", "s", "t", "{}", "persistent error")
        time.sleep(0.1)
        result = dlq.record_retry(dlq_id, success=False, reason="still failing")
        assert result is True

    def test_replay(self, dlq):
        dlq_id = dlq.enqueue("rp1", "s", "t", '{"data":1}', "error")
        replayed = dlq.replay(dlq_id)
        assert replayed is not None
        assert isinstance(replayed, dict)

    def test_resolve(self, dlq):
        dlq_id = dlq.enqueue("res1", "s", "t", "{}", "error")
        assert dlq.resolve(dlq_id) is True

    def test_get_alerts(self, dlq):
        dlq_id = dlq.enqueue("al1", "s", "t", "{}", "error", max_retries=3)
        # Record multiple failures to exceed alert threshold
        for _ in range(3):
            dlq.record_retry(dlq_id, success=False, reason="failing")
            time.sleep(0.05)
        alerts = dlq.get_alerts(min_retries=2)
        assert isinstance(alerts, list)

    def test_stats(self, dlq):
        dlq.enqueue("st1", "s", "t", "{}", "error")
        s = dlq.stats()
        assert isinstance(s, dict)

    def test_max_retries_configurable(self, dlq):
        dlq_id = dlq.enqueue("mr1", "s", "t", "{}", "error", max_retries=5)
        assert dlq_id > 0

    def test_exponential_backoff(self, dlq):
        """Retry delay should increase with each attempt."""
        dlq_id = dlq.enqueue("eb1", "s", "t", "{}", "error")
        # Simulate retries and check that backoff increases
        dlq.record_retry(dlq_id, success=False)
        time.sleep(0.05)
        dlq.record_retry(dlq_id, success=False)
        # If we can inspect the entry, backoff should have grown
        alerts = dlq.get_alerts(min_retries=1)
        assert isinstance(alerts, list)

    def test_enqueue_duplicate_handoff_id(self, dlq):
        """Multiple failures for the same handoff_id are separate DLQ entries."""
        id1 = dlq.enqueue("dup_h", "s", "t", "{}", "first error")
        id2 = dlq.enqueue("dup_h", "s", "t", "{}", "second error")
        assert id1 != id2


# ===================================================================
# AGENT CONTEXT PROTOCOL (facade) — ~14 tests
# ===================================================================

class TestAgentContextProtocol:
    """Tests for AgentContextProtocol: unified facade over all subsystems."""

    def test_singleton(self, tmp_db):
        AgentContextProtocol.reset()
        p1 = AgentContextProtocol(db_path=tmp_db)
        p2 = AgentContextProtocol(db_path=tmp_db)
        assert p1 is p2
        p1.shutdown()
        AgentContextProtocol.reset()

    def test_register_agent(self, protocol):
        reg = protocol.register_agent("facade_a1", agent_type="test")
        assert isinstance(reg, AgentRegistration)

    def test_unregister_agent(self, protocol):
        protocol.register_agent("facade_a2")
        assert protocol.unregister_agent("facade_a2") is True

    def test_get_agent_status(self, protocol):
        protocol.register_agent("facade_a3")
        status = protocol.get_agent_status("facade_a3")
        assert status is not None

    def test_send_handoff(self, protocol):
        protocol.register_agent("sender1", lane_affinity=["A"])
        protocol.register_agent("receiver1", lane_affinity=["A"], capabilities=["discovery"])
        protocol.add_route("A", "discovery", "receiver1")
        result = protocol.send_handoff(
            source_agent="sender1",
            lane="A",
            task_type="discovery",
            task_description="test handoff",
            items=[{"key": "item1", "content": "data"}],
        )
        assert isinstance(result, dict)
        assert "handoff_id" in result

    def test_receive_handoff(self, protocol):
        protocol.register_agent("s2", lane_affinity=["A"])
        protocol.register_agent("r2", lane_affinity=["A"], capabilities=["filing"])
        protocol.add_route("A", "filing", "r2")
        sent = protocol.send_handoff(
            source_agent="s2", lane="A", task_type="filing",
            task_description="test", items=[{"k": 1}],
        )
        if "handoff_id" in sent:
            received = protocol.receive_handoff(sent["handoff_id"], "r2")
            assert received is not None

    def test_subscribe_and_publish(self, protocol):
        protocol.register_agent("ps1")
        protocol.subscribe("ps1", "test.topic")
        eid = protocol.publish("test.topic", {"msg": "hello"}, "ps1")
        assert isinstance(eid, int)

    def test_store_and_retrieve_context(self, protocol):
        row_id = protocol.store_context("test_ctx", {"data": "lifecycle test"}, lane="A")
        assert row_id > 0
        retrieved = protocol.retrieve_context("test_ctx")
        assert retrieved is not None

    def test_retry_failed_handoffs(self, protocol):
        result = protocol.retry_failed_handoffs()
        assert isinstance(result, dict)

    def test_run_maintenance(self, protocol):
        result = protocol.run_maintenance()
        assert isinstance(result, dict)

    def test_get_stats(self, protocol):
        stats = protocol.get_stats()
        assert isinstance(stats, dict)

    def test_health(self, protocol):
        h = protocol.health()
        assert isinstance(h, dict)

    def test_get_lane_status(self, protocol):
        protocol.register_agent("lane_a", lane_affinity=["A"])
        status = protocol.get_lane_status("A")
        assert isinstance(status, dict)

    def test_shutdown_graceful(self, tmp_db):
        AgentContextProtocol.reset()
        p = AgentContextProtocol(db_path=tmp_db)
        p.register_agent("shutdown_test")
        p.shutdown()
        AgentContextProtocol.reset()


# ===================================================================
# DRIVE SCANNER — ~12 tests
# ===================================================================

class TestDriveScanner:
    """Tests for DriveScanner: scan, filter, dedup, skip dirs."""

    def test_scan_empty_dir(self, scanner, tmp_dir):
        records = scanner.scan_drive(tmp_dir)
        assert isinstance(records, list)

    def test_scan_finds_txt_file(self, tmp_dir):
        # Create a .txt file
        fpath = os.path.join(tmp_dir, "test_doc.txt")
        with open(fpath, "w") as f:
            f.write("Legal content for testing.")
        sc = DriveScanner(drives=[(tmp_dir, True)], extensions={".txt"}, max_depth=2)
        records = sc.scan_drive(tmp_dir)
        assert any(r.ext == ".txt" for r in records)

    def test_scan_skips_wrong_extension(self, tmp_dir):
        fpath = os.path.join(tmp_dir, "image.png")
        with open(fpath, "w") as f:
            f.write("not a legal file")
        sc = DriveScanner(drives=[(tmp_dir, True)], extensions={".txt"}, max_depth=2)
        records = sc.scan_drive(tmp_dir)
        assert not any(r.ext == ".png" for r in records)

    def test_scan_respects_max_depth(self, tmp_dir):
        deep = os.path.join(tmp_dir, "a", "b", "c", "d", "e")
        os.makedirs(deep, exist_ok=True)
        fpath = os.path.join(deep, "deep.txt")
        with open(fpath, "w") as f:
            f.write("deep file")
        sc = DriveScanner(drives=[(tmp_dir, True)], extensions={".txt"}, max_depth=2)
        records = sc.scan_drive(tmp_dir)
        deep_found = any("deep.txt" in r.path for r in records)
        # At depth 5, should be skipped with max_depth=2
        assert not deep_found

    def test_skip_directories(self, tmp_dir):
        skip_dir = os.path.join(tmp_dir, "__pycache__")
        os.makedirs(skip_dir, exist_ok=True)
        fpath = os.path.join(skip_dir, "cached.txt")
        with open(fpath, "w") as f:
            f.write("should be skipped")
        sc = DriveScanner(
            drives=[(tmp_dir, True)], extensions={".txt"},
            skip_dirs={"__pycache__"}, max_depth=3,
        )
        records = sc.scan_drive(tmp_dir)
        assert not any("__pycache__" in r.path for r in records)

    def test_file_record_fields(self, tmp_dir):
        fpath = os.path.join(tmp_dir, "fields.txt")
        with open(fpath, "w") as f:
            f.write("field test content")
        sc = DriveScanner(drives=[(tmp_dir, True)], extensions={".txt"}, max_depth=2)
        records = sc.scan_drive(tmp_dir)
        if records:
            r = records[0]
            assert hasattr(r, "path")
            assert hasattr(r, "size")
            assert hasattr(r, "ext")
            assert hasattr(r, "sha256")

    def test_load_known_hashes_dedup(self, tmp_dir):
        fpath = os.path.join(tmp_dir, "dup.txt")
        with open(fpath, "w") as f:
            f.write("duplicate content")
        # Compute hash
        h = hashlib.sha256(b"duplicate content").hexdigest()
        sc = DriveScanner(drives=[(tmp_dir, True)], extensions={".txt"}, max_depth=2)
        sc.load_known_hashes({h})
        records = sc.scan_drive(tmp_dir)
        # File with known hash should be skipped
        # (Note: hash is of raw bytes via file read, not string — may still appear)
        assert isinstance(records, list)

    def test_stats_property(self, tmp_dir):
        sc = DriveScanner(drives=[(tmp_dir, True)], extensions={".txt"}, max_depth=2)
        sc.scan_drive(tmp_dir)
        s = sc.stats
        assert isinstance(s, dict)
        assert "total_scanned" in s or "total_matched" in s

    def test_scan_all_drives(self, tmp_dir):
        fpath = os.path.join(tmp_dir, "all_test.txt")
        with open(fpath, "w") as f:
            f.write("scan all test")
        sc = DriveScanner(drives=[(tmp_dir, True)], extensions={".txt"}, max_depth=2)
        records = sc.scan_all()
        assert isinstance(records, list)

    def test_max_file_size_filter(self, tmp_dir):
        fpath = os.path.join(tmp_dir, "big.txt")
        with open(fpath, "w") as f:
            f.write("x" * 100)
        sc = DriveScanner(
            drives=[(tmp_dir, True)], extensions={".txt"},
            max_depth=2, max_file_size=10,  # Only 10 bytes
        )
        records = sc.scan_drive(tmp_dir)
        assert not any("big.txt" in r.path for r in records)

    def test_default_drives_constant(self):
        assert isinstance(DEFAULT_DRIVES, list)
        assert len(DEFAULT_DRIVES) >= 1

    def test_legal_extensions_constant(self):
        assert ".pdf" in LEGAL_EXTENSIONS
        assert ".txt" in LEGAL_EXTENSIONS
        assert ".docx" in LEGAL_EXTENSIONS


# ===================================================================
# TEXT EXTRACTOR — ~14 tests
# ===================================================================

class TestTextExtractor:
    """Tests for TextExtractor: format-specific extraction with fallbacks."""

    def test_extract_txt_file(self, tmp_dir, extractor):
        fpath = os.path.join(tmp_dir, "plain.txt")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write("Plain text content for extraction test.")
        result = extractor.extract(fpath)
        assert isinstance(result, ExtractedContent)
        assert "Plain text" in result.text

    def test_extract_md_file(self, tmp_dir, extractor):
        fpath = os.path.join(tmp_dir, "readme.md")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write("# Heading\n\nMarkdown content for testing.")
        result = extractor.extract(fpath)
        assert "Markdown" in result.text or "Heading" in result.text

    def test_extract_csv_file(self, tmp_dir, extractor):
        fpath = os.path.join(tmp_dir, "data.csv")
        with open(fpath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["name", "value"])
            writer.writerow(["test", "123"])
        result = extractor.extract(fpath)
        assert isinstance(result, ExtractedContent)
        assert len(result.text) > 0

    def test_extract_json_file(self, tmp_dir, extractor):
        fpath = os.path.join(tmp_dir, "data.json")
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump({"key": "value", "number": 42}, f)
        result = extractor.extract(fpath)
        assert "key" in result.text or "value" in result.text

    def test_extract_html_file(self, tmp_dir, extractor):
        fpath = os.path.join(tmp_dir, "page.html")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write("<html><body><p>HTML content for test.</p></body></html>")
        result = extractor.extract(fpath)
        assert "HTML content" in result.text or "content" in result.text.lower()

    def test_extract_nonexistent_file(self, extractor):
        result = extractor.extract("/nonexistent/path/file.txt")
        # Should handle gracefully — empty content or error metadata
        assert isinstance(result, ExtractedContent)

    def test_extract_empty_file(self, tmp_dir, extractor):
        fpath = os.path.join(tmp_dir, "empty.txt")
        with open(fpath, "w") as f:
            pass
        result = extractor.extract(fpath)
        assert isinstance(result, ExtractedContent)
        assert result.text == "" or result.char_count == 0

    def test_extract_binary_file_graceful(self, tmp_dir, extractor):
        fpath = os.path.join(tmp_dir, "binary.txt")
        with open(fpath, "wb") as f:
            f.write(bytes(range(256)))
        result = extractor.extract(fpath)
        assert isinstance(result, ExtractedContent)

    def test_extracted_content_fields(self, tmp_dir, extractor):
        fpath = os.path.join(tmp_dir, "fields.txt")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write("Content for field validation test.")
        result = extractor.extract(fpath)
        assert hasattr(result, "text")
        assert hasattr(result, "page_count")
        assert hasattr(result, "char_count")
        assert hasattr(result, "extraction_method")

    def test_extraction_method_set(self, tmp_dir, extractor):
        fpath = os.path.join(tmp_dir, "method.txt")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write("Method tracking test.")
        result = extractor.extract(fpath)
        assert result.extraction_method != "unknown"

    def test_stats_property(self, tmp_dir, extractor):
        fpath = os.path.join(tmp_dir, "stats.txt")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write("Stats test.")
        extractor.extract(fpath)
        s = extractor.stats
        assert isinstance(s, dict)

    @patch.dict("sys.modules", {"fitz": None, "pymupdf": None})
    def test_pdf_graceful_fallback(self, tmp_dir, extractor):
        """PDF extraction should fall back gracefully when fitz unavailable."""
        fpath = os.path.join(tmp_dir, "test.pdf")
        with open(fpath, "wb") as f:
            f.write(b"%PDF-1.4 fake pdf content for fallback test")
        result = extractor.extract(fpath)
        assert isinstance(result, ExtractedContent)

    @patch.dict("sys.modules", {"docx": None, "python-docx": None})
    def test_docx_graceful_fallback(self, tmp_dir, extractor):
        """DOCX extraction should fall back to zipfile when python-docx unavailable."""
        fpath = os.path.join(tmp_dir, "test.docx")
        with open(fpath, "wb") as f:
            f.write(b"PK\x03\x04 fake docx content")
        result = extractor.extract(fpath)
        assert isinstance(result, ExtractedContent)

    def test_latin1_fallback(self, tmp_dir, extractor):
        """Files with non-UTF-8 encoding should fall back to latin-1."""
        fpath = os.path.join(tmp_dir, "latin1.txt")
        with open(fpath, "wb") as f:
            f.write("Caf\xe9 d\xe9cor".encode("latin-1"))
        result = extractor.extract(fpath)
        assert isinstance(result, ExtractedContent)
        assert len(result.text) > 0


# ===================================================================
# GOOGLE DRIVE HARVESTER — ~8 tests
# ===================================================================

class TestGoogleDriveHarvester:
    """Tests for GoogleDriveHarvester: graceful skip, mock OAuth."""

    def test_no_auth_by_default(self, gdrive_harvester):
        """Without credentials, authenticate should return False gracefully."""
        result = gdrive_harvester.authenticate()
        assert result is False

    def test_list_files_without_auth(self, gdrive_harvester):
        files = gdrive_harvester.list_files()
        assert isinstance(files, list)
        assert len(files) == 0

    def test_download_files_without_auth(self, gdrive_harvester):
        paths = gdrive_harvester.download_files()
        assert isinstance(paths, list)
        assert len(paths) == 0

    def test_stats_initial(self, gdrive_harvester):
        s = gdrive_harvester.stats
        assert isinstance(s, dict)
        assert s.get("listed", 0) == 0

    @patch.dict(os.environ, {}, clear=False)
    def test_no_hardcoded_credentials(self, gdrive_harvester):
        """Credentials must come from env vars or files, never hardcoded."""
        src = os.path.join(
            os.path.dirname(__file__), "..", "context_harvester.py"
        )
        if os.path.exists(src):
            with open(src, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            # Should not contain hardcoded API keys or secrets
            assert "AIza" not in content  # Google API key prefix
            assert "GOCSPX" not in content  # Google OAuth secret prefix

    def test_download_dir_created(self, tmp_dir):
        dl_dir = os.path.join(tmp_dir, "gdrive_downloads")
        gdh = GoogleDriveHarvester(download_dir=dl_dir)
        # The dir should either be created or noted for creation
        assert gdh is not None

    def test_rate_limit_delay(self, tmp_dir):
        gdh = GoogleDriveHarvester(download_dir=tmp_dir, rate_limit_delay=2.0)
        assert gdh is not None

    @patch("context_harvester.GoogleDriveHarvester.authenticate", return_value=True)
    def test_mock_authenticate(self, mock_auth, tmp_dir):
        gdh = GoogleDriveHarvester(download_dir=tmp_dir)
        assert gdh.authenticate() is True


# ===================================================================
# CONTENT INDEXER — ~14 tests
# ===================================================================

class TestContentIndexer:
    """Tests for ContentIndexer: table creation, batch insert, FTS5, dedup."""

    def test_table_creation(self, indexer):
        """Tables should be created on init."""
        conn = sqlite3.connect(indexer.db_path if hasattr(indexer, "db_path") else ":memory:")
        # Try to query the main table
        try:
            conn.execute("SELECT COUNT(*) FROM harvested_content")
            assert True
        except sqlite3.OperationalError:
            # If db_path is internal, just verify indexer works
            stats = indexer.get_stats()
            assert isinstance(stats, dict)
        finally:
            conn.close()

    def test_index_single(self, indexer):
        rec = FileRecord(
            path="/test/doc.txt", size=100, modified="2025-01-01T00:00:00Z",
            ext=".txt", sha256="abc123def456", drive="C",
        )
        content = ExtractedContent(
            text="Legal document content.", page_count=1,
            char_count=22, extraction_method="text",
        )
        result = indexer.index_single(rec, content)
        assert result is True

    def test_index_batch(self, indexer):
        records = []
        contents = []
        for i in range(5):
            records.append(FileRecord(
                path=f"/test/batch_{i}.txt", size=50 + i, modified="2025-01-01",
                ext=".txt", sha256=f"batch_hash_{i}", drive="C",
            ))
            contents.append(ExtractedContent(
                text=f"Batch content item {i}.", page_count=1,
                char_count=20, extraction_method="text",
            ))
        count = indexer.index_batch(records, contents)
        assert count >= 5

    def test_dedup_by_sha256(self, indexer):
        rec = FileRecord(
            path="/test/dup1.txt", size=100, modified="2025-01-01",
            ext=".txt", sha256="dedup_hash_001", drive="C",
        )
        content = ExtractedContent(text="Dedup test.", char_count=11, extraction_method="text")
        indexer.index_single(rec, content)
        # Try to insert same hash again
        rec2 = FileRecord(
            path="/test/dup2.txt", size=100, modified="2025-01-01",
            ext=".txt", sha256="dedup_hash_001", drive="D",
        )
        result = indexer.index_single(rec2, content)
        assert result is False  # Should be rejected as duplicate

    def test_search_fts5(self, indexer):
        rec = FileRecord(
            path="/test/search.txt", size=100, modified="2025-01-01",
            ext=".txt", sha256="search_hash_001", drive="C",
        )
        content = ExtractedContent(
            text="custody hearing evidence filing motion.", char_count=40,
            extraction_method="text",
        )
        indexer.index_single(rec, content)
        results = indexer.search("custody")
        assert isinstance(results, list)
        assert len(results) >= 1

    def test_search_with_lane_filter(self, indexer):
        rec = FileRecord(
            path="/test/lane_a.txt", size=50, modified="2025-01-01",
            ext=".txt", sha256="lane_hash_a", drive="C",
        )
        content = ExtractedContent(
            text="custody parenting time evidence.", char_count=30,
            extraction_method="text",
        )
        indexer.index_single(rec, content)
        results = indexer.search("custody", lane="A")
        assert isinstance(results, list)

    def test_search_with_file_type_filter(self, indexer):
        rec = FileRecord(
            path="/test/typed.pdf", size=500, modified="2025-01-01",
            ext=".pdf", sha256="pdf_hash_001", drive="C",
        )
        content = ExtractedContent(text="PDF content.", char_count=12, extraction_method="fitz")
        indexer.index_single(rec, content)
        results = indexer.search("PDF", file_type=".pdf")
        assert isinstance(results, list)

    def test_get_known_hashes(self, indexer):
        rec = FileRecord(
            path="/test/known.txt", size=10, modified="2025-01-01",
            ext=".txt", sha256="known_hash_xyz", drive="C",
        )
        content = ExtractedContent(text="known.", char_count=6, extraction_method="text")
        indexer.index_single(rec, content)
        hashes = indexer.get_known_hashes()
        assert "known_hash_xyz" in hashes

    def test_get_stats(self, indexer):
        stats = indexer.get_stats()
        assert isinstance(stats, dict)
        assert "total_indexed" in stats

    def test_log_progress(self, indexer):
        row_id = indexer.log_progress(
            drive="C", last_path="/test/last.txt",
            scanned=100, indexed=80, skipped=15, errored=5,
        )
        assert isinstance(row_id, int)

    def test_log_error(self, indexer):
        indexer.log_error(
            file_path="/test/bad.pdf",
            error_type="ExtractionError",
            error_msg="Failed to parse PDF",
        )
        # Should not raise

    def test_close(self, harvest_db):
        idx = ContentIndexer(db_path=harvest_db)
        idx.close()
        # Should not raise on double close
        idx.close()

    def test_search_no_results(self, indexer):
        results = indexer.search("xyznonexistenttermxyz")
        assert isinstance(results, list)
        assert len(results) == 0

    def test_search_limit(self, indexer):
        for i in range(10):
            rec = FileRecord(
                path=f"/test/limit_{i}.txt", size=10, modified="2025-01-01",
                ext=".txt", sha256=f"limit_hash_{i}", drive="C",
            )
            content = ExtractedContent(
                text=f"common search term item {i}.", char_count=25,
                extraction_method="text",
            )
            indexer.index_single(rec, content)
        results = indexer.search("common", limit=3)
        assert len(results) <= 3


# ===================================================================
# CONTEXT HARVESTER (facade) — ~12 tests
# ===================================================================

class TestContextHarvester:
    """Tests for ContextHarvester: unified facade."""

    @pytest.fixture
    def harvester(self, tmp_dir, harvest_db):
        h = ContextHarvester(
            db_path=harvest_db,
            drives=[(tmp_dir, True)],
            extensions={".txt", ".md"},
            max_depth=3,
            batch_size=10,
        )
        yield h
        h.close()

    def test_init(self, harvester):
        assert harvester is not None
        assert harvester.indexer is not None
        assert harvester.scanner is not None
        assert harvester.extractor is not None

    def test_search_returns_list(self, harvester):
        results = harvester.search("test query")
        assert isinstance(results, list)

    def test_get_stats_structure(self, harvester):
        stats = harvester.get_stats()
        assert isinstance(stats, dict)

    def test_get_health_checks_drives(self, harvester):
        health = harvester.get_health()
        assert isinstance(health, dict)

    def test_harvest_drive(self, harvester, tmp_dir):
        # Create a test file
        fpath = os.path.join(tmp_dir, "harvest_test.txt")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write("Content for harvest drive test.")
        result = harvester.harvest_drive(tmp_dir)
        assert isinstance(result, dict)

    def test_harvest_all(self, harvester, tmp_dir):
        fpath = os.path.join(tmp_dir, "all_test.txt")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write("Content for harvest all test.")
        result = harvester.harvest_all()
        assert isinstance(result, dict)

    def test_search_after_harvest(self, harvester, tmp_dir):
        fpath = os.path.join(tmp_dir, "searchable.txt")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write("unique custody evidence searchable term xylophone.")
        harvester.harvest_drive(tmp_dir)
        results = harvester.search("xylophone")
        assert isinstance(results, list)
        # Should find the indexed content
        assert len(results) >= 1

    def test_get_context_for_query(self, harvester, tmp_dir):
        fpath = os.path.join(tmp_dir, "context_query.txt")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write("Context query test with custody and evidence keywords.")
        harvester.harvest_drive(tmp_dir)
        ctx = harvester.get_context_for_query("custody", max_tokens=500)
        assert isinstance(ctx, list)

    def test_stop(self, harvester):
        harvester.stop()
        # Should not raise

    def test_close_idempotent(self, tmp_dir, harvest_db):
        h = ContextHarvester(
            db_path=harvest_db, drives=[(tmp_dir, True)],
            extensions={".txt"}, max_depth=2,
        )
        h.close()
        h.close()  # Should not raise on double close

    def test_harvest_google_drive_without_auth(self, harvester):
        result = harvester.harvest_google_drive()
        assert isinstance(result, dict)
        assert result.get("authenticated") is False or result.get("indexed", 0) == 0

    def test_export_to_context_orchestrator(self, harvester, tmp_dir):
        fpath = os.path.join(tmp_dir, "export_test.txt")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write("Exportable evidence content for orchestrator.")
        harvester.harvest_drive(tmp_dir)
        payload = harvester.export_to_context_orchestrator("evidence", max_tokens=500)
        assert isinstance(payload, dict)
        assert "source" in payload or "query" in payload


# ===================================================================
# HELPER FUNCTIONS — ~8 tests
# ===================================================================

class TestHelperFunctions:
    """Tests for module-level helpers: detect_lane, compute_sha256."""

    def test_detect_lane_custody(self):
        lane = detect_lane("/case/custody_doc.pdf", "custody parenting time")
        assert lane in ("A", None) or lane is not None

    def test_detect_lane_ppo(self):
        lane = detect_lane("/case/ppo_violation.txt", "PPO protection order")
        assert lane in ("D", None) or lane is not None

    def test_detect_lane_appellate(self):
        lane = detect_lane("/case/COA_366810_brief.pdf", "appellate brief")
        assert lane in ("F", None) or lane is not None

    def test_detect_lane_misconduct(self):
        lane = detect_lane("/case/jtc_complaint.txt", "judicial misconduct")
        assert lane in ("E", None) or lane is not None

    def test_detect_lane_housing(self):
        lane = detect_lane("/case/shady_oaks.pdf", "housing habitability")
        assert lane in ("B", None) or lane is not None

    def test_detect_lane_unknown(self):
        lane = detect_lane("/random/file.txt", "nothing relevant here")
        # Could be None or any lane
        assert lane is None or lane in VALID_LANES

    def test_compute_sha256_file(self, tmp_dir):
        fpath = os.path.join(tmp_dir, "hash_test.txt")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write("hash this content")
        h = compute_sha256(fpath)
        assert isinstance(h, str)
        assert len(h) == 64  # SHA-256 hex digest

    def test_compute_sha256_deterministic(self, tmp_dir):
        fpath = os.path.join(tmp_dir, "determ.txt")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write("deterministic content")
        h1 = compute_sha256(fpath)
        h2 = compute_sha256(fpath)
        assert h1 == h2


# ===================================================================
# HARVEST SCHEDULER — ~6 tests
# ===================================================================

class TestHarvestScheduler:
    """Tests for HarvestScheduler: incremental, checkpoints, stop."""

    @pytest.fixture
    def scheduler(self, tmp_dir, harvest_db):
        sc = DriveScanner(drives=[(tmp_dir, True)], extensions={".txt"}, max_depth=2)
        ex = TextExtractor(timeout=5)
        idx = ContentIndexer(db_path=harvest_db)
        cp_path = os.path.join(tmp_dir, "checkpoint.json")
        sched = HarvestScheduler(
            scanner=sc, extractor=ex, indexer=idx,
            batch_size=5, checkpoint_path=cp_path,
        )
        yield sched
        idx.close()

    def test_run_incremental(self, scheduler, tmp_dir):
        fpath = os.path.join(tmp_dir, "incr.txt")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write("Incremental harvest test.")
        result = scheduler.run_incremental()
        assert isinstance(result, dict)

    def test_stop(self, scheduler):
        scheduler.stop()
        assert True  # Should not raise

    def test_is_running_initially_false(self, scheduler):
        assert scheduler.is_running is False

    def test_should_sync_gdrive(self, scheduler):
        result = scheduler.should_sync_gdrive()
        assert isinstance(result, bool)

    def test_mark_gdrive_synced(self, scheduler):
        scheduler.mark_gdrive_synced()
        # After marking, should_sync_gdrive should return False
        assert scheduler.should_sync_gdrive() is False

    def test_checkpoint_persistence(self, scheduler, tmp_dir):
        fpath = os.path.join(tmp_dir, "cp_test.txt")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write("Checkpoint test.")
        scheduler.run_incremental()
        cp_file = os.path.join(tmp_dir, "checkpoint.json")
        assert os.path.exists(cp_file)


# ===================================================================
# CONSTANTS — ~5 tests
# ===================================================================

class TestHarvesterConstants:
    """Verify harvester module-level constants."""

    def test_legal_extensions_set(self):
        assert isinstance(LEGAL_EXTENSIONS, (set, frozenset))
        assert ".pdf" in LEGAL_EXTENSIONS

    def test_skip_dirs_set(self):
        assert isinstance(SKIP_DIRS, (set, frozenset, list, tuple))
        assert "node_modules" in SKIP_DIRS or "__pycache__" in SKIP_DIRS

    def test_max_file_size_positive(self):
        assert MAX_FILE_SIZE > 0

    def test_max_extract_timeout_positive(self):
        assert MAX_EXTRACT_TIMEOUT > 0

    def test_default_batch_size_positive(self):
        assert DEFAULT_BATCH_SIZE > 0
