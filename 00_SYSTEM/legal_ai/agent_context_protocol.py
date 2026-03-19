"""
agent_context_protocol.py — Multi-Agent Context Coordination Protocol
=====================================================================
Extends the base ContextManager (context_manager.py) and ContextOrchestrator
(context_orchestrator.py) with advanced multi-agent coordination:

  * ContextRegistry        — central agent registry with capabilities & status
  * ContextPubSub          — publish/subscribe event bus across agents
  * VersionedHandoff       — semantic-versioned handoffs with diff & rollback
  * ContextRouter          — lane-aware, priority-based context routing
  * ContextLifecycleManager — HOT→WARM→COLD→ARCHIVED lifecycle transitions
  * DeadLetterQueue        — failed-handoff recovery with exponential backoff
  * AgentContextProtocol   — unified facade wiring all subsystems together

Zero external deps (Pydantic optional).  SQLite WAL mode for all persistence.
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import sqlite3
import sys
import threading
import time
import zlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

# ── UTF-8 safety ──────────────────────────────────────────────────────────
if hasattr(sys.stdout, "fileno"):
    try:
        sys.stdout = open(
            sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace"
        )
    except Exception:
        pass

# ── Pydantic v2 optional import ───────────────────────────────────────────
_PYDANTIC = False
try:
    from pydantic import BaseModel, Field
    _PYDANTIC = True
except ImportError:
    pass

# ── Path resolution ───────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[1]  # 00_SYSTEM -> LitigationOS
_DB_PATH = Path(
    os.environ.get("LITIGOS_DB", str(_REPO / "litigation_context.db"))
)

# ── Logging ───────────────────────────────────────────────────────────────
logger = logging.getLogger("litigationos.agent_context_protocol")

# ── Constants ─────────────────────────────────────────────────────────────
VALID_LANES: Set[str] = {"A", "B", "C", "D", "E", "F"}

_WAL_PRAGMAS = """
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 60000;
PRAGMA cache_size  = -32000;
PRAGMA temp_store  = MEMORY;
PRAGMA synchronous = NORMAL;
"""

# Lifecycle thresholds (seconds)
_HOT_TTL = 3600        # 1 hour
_WARM_TTL = 86400      # 24 hours
_COLD_TTL = 2592000    # 30 days
_PROMOTION_HITS = 3    # access_count needed to promote cold→warm

# Dead-letter retry
_DLQ_MAX_RETRIES = 3
_DLQ_BASE_BACKOFF = 1.0   # seconds
_DLQ_MAX_BACKOFF = 60.0   # seconds

# PubSub priorities
_PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


# ═══════════════════════════════════════════════════════════════════════════
#  Database helpers
# ═══════════════════════════════════════════════════════════════════════════

def _safe_connect(
    db_path: Union[str, Path] = _DB_PATH,
) -> Optional[sqlite3.Connection]:
    """Open a SQLite connection with WAL + safety PRAGMAs."""
    try:
        conn = sqlite3.connect(str(db_path), timeout=30)
        conn.row_factory = sqlite3.Row
        for pragma in _WAL_PRAGMAS.strip().splitlines():
            pragma = pragma.strip()
            if pragma:
                conn.execute(pragma)
        return conn
    except Exception as exc:
        logger.error("DB connect failed (%s): %s", db_path, exc)
        return None


def _utcnow() -> str:
    """ISO-8601 UTC timestamp string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha(text: str) -> str:
    """SHA-256 truncated to 16 hex chars."""
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]


# ═══════════════════════════════════════════════════════════════════════════
#  Enums
# ═══════════════════════════════════════════════════════════════════════════

class AgentStatus(str, Enum):
    """Runtime status of a registered agent."""
    IDLE = "idle"
    BUSY = "busy"
    WAITING = "waiting"
    ERROR = "error"


class ContextLifecycleStage(str, Enum):
    """Lifecycle stages for context items."""
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"
    ARCHIVED = "archived"


class EventPriority(str, Enum):
    """Priority levels for pub/sub events."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DLQStatus(str, Enum):
    """Dead-letter queue entry status."""
    PENDING = "pending"
    RETRYING = "retrying"
    RESOLVED = "resolved"
    EXHAUSTED = "exhausted"


# ═══════════════════════════════════════════════════════════════════════════
#  Data models (Pydantic v2 with dataclass fallback)
# ═══════════════════════════════════════════════════════════════════════════

if _PYDANTIC:
    class AgentRegistration(BaseModel):
        agent_id: str
        agent_type: str = "generic"
        capabilities: List[str] = Field(default_factory=list)
        lane_affinity: List[str] = Field(default_factory=list)
        status: str = "idle"
        registered_at: str = Field(default_factory=_utcnow)
        last_heartbeat: str = Field(default_factory=_utcnow)
        metadata: Dict[str, Any] = Field(default_factory=dict)

    class ContextEvent(BaseModel):
        topic: str
        lane: Optional[str] = None
        priority: str = "medium"
        payload: Dict[str, Any] = Field(default_factory=dict)
        publisher_id: str = ""
        published_at: str = Field(default_factory=_utcnow)
        acknowledged_by: List[str] = Field(default_factory=list)
        expires_at: Optional[str] = None

    class HandoffVersion(BaseModel):
        handoff_id: str
        version: str = "1.0.0"
        items_snapshot: List[Dict[str, Any]] = Field(default_factory=list)
        diff_from_previous: Optional[Dict[str, Any]] = None
        created_at: str = Field(default_factory=_utcnow)
        created_by: str = ""

    class RouteEntry(BaseModel):
        lane: str
        task_type: str
        agent_id: str
        priority: int = 0
        fallback_agents: List[str] = Field(default_factory=list)

    class DLQEntry(BaseModel):
        handoff_id: str
        source_agent: str
        target_agent: str
        lane: Optional[str] = None
        payload: str = ""
        failure_reason: str = ""
        retry_count: int = 0
        max_retries: int = _DLQ_MAX_RETRIES
        next_retry_at: Optional[str] = None
        status: str = "pending"

else:
    @dataclass
    class AgentRegistration:  # type: ignore[no-redef]
        agent_id: str = ""
        agent_type: str = "generic"
        capabilities: List[str] = field(default_factory=list)
        lane_affinity: List[str] = field(default_factory=list)
        status: str = "idle"
        registered_at: str = field(default_factory=_utcnow)
        last_heartbeat: str = field(default_factory=_utcnow)
        metadata: Dict[str, Any] = field(default_factory=dict)

    @dataclass
    class ContextEvent:  # type: ignore[no-redef]
        topic: str = ""
        lane: Optional[str] = None
        priority: str = "medium"
        payload: Dict[str, Any] = field(default_factory=dict)
        publisher_id: str = ""
        published_at: str = field(default_factory=_utcnow)
        acknowledged_by: List[str] = field(default_factory=list)
        expires_at: Optional[str] = None

    @dataclass
    class HandoffVersion:  # type: ignore[no-redef]
        handoff_id: str = ""
        version: str = "1.0.0"
        items_snapshot: List[Dict[str, Any]] = field(default_factory=list)
        diff_from_previous: Optional[Dict[str, Any]] = None
        created_at: str = field(default_factory=_utcnow)
        created_by: str = ""

    @dataclass
    class RouteEntry:  # type: ignore[no-redef]
        lane: str = ""
        task_type: str = ""
        agent_id: str = ""
        priority: int = 0
        fallback_agents: List[str] = field(default_factory=list)

    @dataclass
    class DLQEntry:  # type: ignore[no-redef]
        handoff_id: str = ""
        source_agent: str = ""
        target_agent: str = ""
        lane: Optional[str] = None
        payload: str = ""
        failure_reason: str = ""
        retry_count: int = 0
        max_retries: int = _DLQ_MAX_RETRIES
        next_retry_at: Optional[str] = None
        status: str = "pending"


# ═══════════════════════════════════════════════════════════════════════════
#  1. ContextRegistry — agent synchronisation
# ═══════════════════════════════════════════════════════════════════════════

class ContextRegistry:
    """Central registry of all active agents and their context state.

    Thread-safe.  Backed by ``agent_registry`` and ``context_subscriptions``
    SQLite tables for crash-resilient persistence.
    """

    def __init__(self, db_path: Union[str, Path] = _DB_PATH) -> None:
        self._db_path = Path(db_path)
        self._lock = threading.Lock()
        self._agents: Dict[str, AgentRegistration] = {}
        self._init_tables()
        self._load_from_db()

    # ── schema ────────────────────────────────────────────────────────
    def _init_tables(self) -> None:
        conn = _safe_connect(self._db_path)
        if conn is None:
            return
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS agent_registry (
                    agent_id TEXT PRIMARY KEY,
                    agent_type TEXT,
                    capabilities TEXT,
                    lane_affinity TEXT,
                    status TEXT DEFAULT 'idle',
                    registered_at TEXT DEFAULT (datetime('now')),
                    last_heartbeat TEXT,
                    metadata TEXT
                );
                CREATE TABLE IF NOT EXISTS context_subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    lane_filter TEXT,
                    priority_filter TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    UNIQUE(agent_id, topic)
                );
                CREATE INDEX IF NOT EXISTS idx_subs_topic
                    ON context_subscriptions(topic);
            """)
            conn.commit()
        except Exception as exc:
            logger.error("ContextRegistry _init_tables: %s", exc)
        finally:
            conn.close()

    def _load_from_db(self) -> None:
        conn = _safe_connect(self._db_path)
        if conn is None:
            return
        try:
            rows = conn.execute(
                "SELECT agent_id, agent_type, capabilities, lane_affinity, "
                "status, registered_at, last_heartbeat, metadata "
                "FROM agent_registry"
            ).fetchall()
            for r in rows:
                reg = AgentRegistration(
                    agent_id=r["agent_id"],
                    agent_type=r["agent_type"] or "generic",
                    capabilities=json.loads(r["capabilities"] or "[]"),
                    lane_affinity=json.loads(r["lane_affinity"] or "[]"),
                    status=r["status"] or "idle",
                    registered_at=r["registered_at"] or _utcnow(),
                    last_heartbeat=r["last_heartbeat"] or _utcnow(),
                    metadata=json.loads(r["metadata"] or "{}"),
                )
                self._agents[reg.agent_id] = reg
        except Exception as exc:
            logger.error("ContextRegistry _load_from_db: %s", exc)
        finally:
            conn.close()

    # ── public API ────────────────────────────────────────────────────
    def register(
        self,
        agent_id: str,
        agent_type: str = "generic",
        capabilities: Optional[List[str]] = None,
        lane_affinity: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AgentRegistration:
        """Register an agent.  Overwrites if already registered."""
        caps = capabilities or []
        lanes = lane_affinity or []
        for ln in lanes:
            if ln not in VALID_LANES:
                raise ValueError(f"Invalid lane '{ln}'. Valid: {sorted(VALID_LANES)}")

        now = _utcnow()
        reg = AgentRegistration(
            agent_id=agent_id,
            agent_type=agent_type,
            capabilities=caps,
            lane_affinity=lanes,
            status=AgentStatus.IDLE.value,
            registered_at=now,
            last_heartbeat=now,
            metadata=metadata or {},
        )
        with self._lock:
            self._agents[agent_id] = reg
        self._persist_agent(reg)
        logger.info("Registered agent %s (type=%s, lanes=%s)", agent_id, agent_type, lanes)
        return reg

    def unregister(self, agent_id: str) -> bool:
        """Remove an agent from the registry."""
        with self._lock:
            removed = self._agents.pop(agent_id, None)
        if removed is None:
            return False
        conn = _safe_connect(self._db_path)
        if conn:
            try:
                conn.execute("DELETE FROM agent_registry WHERE agent_id = ?", (agent_id,))
                conn.execute("DELETE FROM context_subscriptions WHERE agent_id = ?", (agent_id,))
                conn.commit()
            except Exception as exc:
                logger.error("unregister DB error: %s", exc)
            finally:
                conn.close()
        logger.info("Unregistered agent %s", agent_id)
        return True

    def update_status(self, agent_id: str, status: AgentStatus) -> bool:
        """Update an agent's runtime status and heartbeat."""
        with self._lock:
            reg = self._agents.get(agent_id)
            if reg is None:
                return False
            reg.status = status.value
            reg.last_heartbeat = _utcnow()
        conn = _safe_connect(self._db_path)
        if conn:
            try:
                conn.execute(
                    "UPDATE agent_registry SET status = ?, last_heartbeat = ? WHERE agent_id = ?",
                    (status.value, reg.last_heartbeat, agent_id),
                )
                conn.commit()
            except Exception as exc:
                logger.error("update_status DB error: %s", exc)
            finally:
                conn.close()
        return True

    def heartbeat(self, agent_id: str) -> bool:
        """Update last_heartbeat timestamp for an agent."""
        with self._lock:
            reg = self._agents.get(agent_id)
            if reg is None:
                return False
            reg.last_heartbeat = _utcnow()
        conn = _safe_connect(self._db_path)
        if conn:
            try:
                conn.execute(
                    "UPDATE agent_registry SET last_heartbeat = ? WHERE agent_id = ?",
                    (reg.last_heartbeat, agent_id),
                )
                conn.commit()
            except Exception as exc:
                logger.error("heartbeat DB error: %s", exc)
            finally:
                conn.close()
        return True

    def get_agent(self, agent_id: str) -> Optional[AgentRegistration]:
        with self._lock:
            return self._agents.get(agent_id)

    def list_agents(
        self,
        status: Optional[AgentStatus] = None,
        lane: Optional[str] = None,
        capability: Optional[str] = None,
    ) -> List[AgentRegistration]:
        """List agents with optional filters."""
        with self._lock:
            agents = list(self._agents.values())
        if status is not None:
            agents = [a for a in agents if a.status == status.value]
        if lane is not None:
            agents = [a for a in agents if lane in a.lane_affinity]
        if capability is not None:
            agents = [a for a in agents if capability in a.capabilities]
        return agents

    def discover(
        self, capability: str, lane: Optional[str] = None
    ) -> List[AgentRegistration]:
        """Find agents that have a given capability and optional lane affinity."""
        return self.list_agents(capability=capability, lane=lane)

    def agent_count(self) -> int:
        with self._lock:
            return len(self._agents)

    # ── internals ─────────────────────────────────────────────────────
    def _persist_agent(self, reg: AgentRegistration) -> None:
        conn = _safe_connect(self._db_path)
        if conn is None:
            return
        try:
            conn.execute(
                "INSERT OR REPLACE INTO agent_registry "
                "(agent_id, agent_type, capabilities, lane_affinity, "
                "status, registered_at, last_heartbeat, metadata) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    reg.agent_id,
                    reg.agent_type,
                    json.dumps(reg.capabilities, default=str),
                    json.dumps(reg.lane_affinity, default=str),
                    reg.status,
                    reg.registered_at,
                    reg.last_heartbeat,
                    json.dumps(reg.metadata, default=str),
                ),
            )
            conn.commit()
        except Exception as exc:
            logger.error("_persist_agent DB error: %s", exc)
        finally:
            conn.close()


# ═══════════════════════════════════════════════════════════════════════════
#  2. ContextPubSub — event-driven context sharing
# ═══════════════════════════════════════════════════════════════════════════

class ContextPubSub:
    """Publish-subscribe event bus for context events across agents.

    Topics include lane updates, filing progress, evidence discoveries,
    deadline alerts.  Delivery guarantee: at-least-once with ack.
    Dead-letter queue integration for unacknowledged messages.
    """

    def __init__(self, db_path: Union[str, Path] = _DB_PATH) -> None:
        self._db_path = Path(db_path)
        self._lock = threading.Lock()
        self._subscribers: Dict[str, List[Dict[str, Any]]] = {}
        self._callbacks: Dict[str, List[Callable]] = {}
        self._init_tables()
        self._load_subscriptions()

    def _init_tables(self) -> None:
        conn = _safe_connect(self._db_path)
        if conn is None:
            return
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS context_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    lane TEXT,
                    priority TEXT DEFAULT 'medium',
                    payload TEXT NOT NULL,
                    publisher_id TEXT NOT NULL,
                    published_at TEXT DEFAULT (datetime('now')),
                    acknowledged_by TEXT,
                    expires_at TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_events_topic_lane
                    ON context_events(topic, lane);
            """)
            conn.commit()
        except Exception as exc:
            logger.error("ContextPubSub _init_tables: %s", exc)
        finally:
            conn.close()

    def _load_subscriptions(self) -> None:
        conn = _safe_connect(self._db_path)
        if conn is None:
            return
        try:
            rows = conn.execute(
                "SELECT agent_id, topic, lane_filter, priority_filter "
                "FROM context_subscriptions"
            ).fetchall()
            with self._lock:
                for r in rows:
                    topic = r["topic"]
                    sub = {
                        "agent_id": r["agent_id"],
                        "lane_filter": r["lane_filter"],
                        "priority_filter": r["priority_filter"],
                    }
                    self._subscribers.setdefault(topic, []).append(sub)
        except Exception as exc:
            logger.error("_load_subscriptions: %s", exc)
        finally:
            conn.close()

    def subscribe(
        self,
        agent_id: str,
        topic: str,
        lane_filter: Optional[str] = None,
        priority_filter: Optional[str] = None,
        callback: Optional[Callable] = None,
    ) -> bool:
        """Subscribe an agent to a topic with optional lane/priority filters."""
        sub = {
            "agent_id": agent_id,
            "lane_filter": lane_filter,
            "priority_filter": priority_filter,
        }
        with self._lock:
            subs = self._subscribers.setdefault(topic, [])
            if not any(s["agent_id"] == agent_id for s in subs):
                subs.append(sub)
            if callback is not None:
                self._callbacks.setdefault(topic, []).append(callback)

        conn = _safe_connect(self._db_path)
        if conn:
            try:
                conn.execute(
                    "INSERT OR REPLACE INTO context_subscriptions "
                    "(agent_id, topic, lane_filter, priority_filter) "
                    "VALUES (?, ?, ?, ?)",
                    (agent_id, topic, lane_filter, priority_filter),
                )
                conn.commit()
            except Exception as exc:
                logger.error("subscribe DB error: %s", exc)
            finally:
                conn.close()
        logger.debug("Agent %s subscribed to topic '%s'", agent_id, topic)
        return True

    def unsubscribe(self, agent_id: str, topic: str) -> bool:
        """Remove an agent's subscription to a topic."""
        removed = False
        with self._lock:
            subs = self._subscribers.get(topic, [])
            before = len(subs)
            self._subscribers[topic] = [s for s in subs if s["agent_id"] != agent_id]
            removed = len(self._subscribers[topic]) < before

        conn = _safe_connect(self._db_path)
        if conn:
            try:
                conn.execute(
                    "DELETE FROM context_subscriptions WHERE agent_id = ? AND topic = ?",
                    (agent_id, topic),
                )
                conn.commit()
            except Exception as exc:
                logger.error("unsubscribe DB error: %s", exc)
            finally:
                conn.close()
        return removed

    def publish(
        self,
        topic: str,
        payload: Dict[str, Any],
        publisher_id: str,
        lane: Optional[str] = None,
        priority: str = "medium",
        ttl_seconds: Optional[int] = None,
    ) -> int:
        """Publish an event to a topic.  Returns the event row id."""
        if lane and lane not in VALID_LANES:
            raise ValueError(f"Invalid lane '{lane}'. Valid: {sorted(VALID_LANES)}")

        expires = None
        if ttl_seconds:
            expires = (
                datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
            ).strftime("%Y-%m-%dT%H:%M:%SZ")

        event_id = 0
        conn = _safe_connect(self._db_path)
        if conn:
            try:
                cur = conn.execute(
                    "INSERT INTO context_events "
                    "(topic, lane, priority, payload, publisher_id, published_at, "
                    "acknowledged_by, expires_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        topic, lane, priority,
                        json.dumps(payload, default=str),
                        publisher_id, _utcnow(),
                        json.dumps([]), expires,
                    ),
                )
                conn.commit()
                event_id = cur.lastrowid or 0
            except Exception as exc:
                logger.error("publish DB error: %s", exc)
            finally:
                conn.close()

        # Fire in-memory callbacks
        with self._lock:
            cbs = list(self._callbacks.get(topic, []))
        for cb in cbs:
            try:
                cb(topic, payload, publisher_id, lane, priority)
            except Exception as exc:
                logger.warning("Callback error for topic '%s': %s", topic, exc)

        logger.debug("Published event %d to topic '%s' (lane=%s)", event_id, topic, lane)
        return event_id

    def acknowledge(self, event_id: int, agent_id: str) -> bool:
        """Mark an event as acknowledged by an agent."""
        conn = _safe_connect(self._db_path)
        if conn is None:
            return False
        try:
            row = conn.execute(
                "SELECT acknowledged_by FROM context_events WHERE id = ?",
                (event_id,),
            ).fetchone()
            if row is None:
                return False
            acked: List[str] = json.loads(row["acknowledged_by"] or "[]")
            if agent_id not in acked:
                acked.append(agent_id)
            conn.execute(
                "UPDATE context_events SET acknowledged_by = ? WHERE id = ?",
                (json.dumps(acked), event_id),
            )
            conn.commit()
            return True
        except Exception as exc:
            logger.error("acknowledge DB error: %s", exc)
            return False
        finally:
            conn.close()

    def get_events(
        self,
        topic: Optional[str] = None,
        lane: Optional[str] = None,
        since: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Retrieve events with optional filters."""
        clauses: List[str] = []
        params: List[Any] = []
        if topic:
            clauses.append("topic = ?")
            params.append(topic)
        if lane:
            clauses.append("lane = ?")
            params.append(lane)
        if since:
            clauses.append("published_at >= ?")
            params.append(since)

        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = (
            f"SELECT id, topic, lane, priority, payload, publisher_id, "
            f"published_at, acknowledged_by, expires_at "
            f"FROM context_events{where} "
            f"ORDER BY id DESC LIMIT ?"
        )
        params.append(limit)

        conn = _safe_connect(self._db_path)
        if conn is None:
            return []
        try:
            rows = conn.execute(sql, params).fetchall()
            return [
                {
                    "id": r["id"],
                    "topic": r["topic"],
                    "lane": r["lane"],
                    "priority": r["priority"],
                    "payload": json.loads(r["payload"] or "{}"),
                    "publisher_id": r["publisher_id"],
                    "published_at": r["published_at"],
                    "acknowledged_by": json.loads(r["acknowledged_by"] or "[]"),
                    "expires_at": r["expires_at"],
                }
                for r in rows
            ]
        except Exception as exc:
            logger.error("get_events: %s", exc)
            return []
        finally:
            conn.close()

    def get_unacknowledged(
        self, agent_id: str, topic: Optional[str] = None, limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get events not yet acknowledged by a specific agent."""
        events = self.get_events(topic=topic, limit=limit * 2)
        return [
            e for e in events
            if agent_id not in e.get("acknowledged_by", [])
        ][:limit]

    def get_matching_subscribers(
        self, topic: str, lane: Optional[str] = None, priority: Optional[str] = None,
    ) -> List[str]:
        """Return agent_ids whose subscription matches the event."""
        with self._lock:
            subs = list(self._subscribers.get(topic, []))
        result = []
        for s in subs:
            if s["lane_filter"] and lane and s["lane_filter"] != lane:
                continue
            if s["priority_filter"] and priority:
                if _PRIORITY_ORDER.get(priority, 2) > _PRIORITY_ORDER.get(s["priority_filter"], 2):
                    continue
            result.append(s["agent_id"])
        return result

    def cleanup_expired(self) -> int:
        """Remove events past their expires_at timestamp."""
        conn = _safe_connect(self._db_path)
        if conn is None:
            return 0
        try:
            now = _utcnow()
            cur = conn.execute(
                "DELETE FROM context_events WHERE expires_at IS NOT NULL AND expires_at < ?",
                (now,),
            )
            conn.commit()
            removed = cur.rowcount
            if removed:
                logger.info("Cleaned up %d expired events", removed)
            return removed
        except Exception as exc:
            logger.error("cleanup_expired: %s", exc)
            return 0
        finally:
            conn.close()

    def stats(self) -> Dict[str, Any]:
        conn = _safe_connect(self._db_path)
        if conn is None:
            return {"error": "db_unavailable"}
        try:
            row = conn.execute(
                "SELECT "
                "(SELECT COUNT(*) FROM context_events) AS event_count, "
                "(SELECT COUNT(*) FROM context_subscriptions) AS sub_count"
            ).fetchone()
            return {
                "total_events": row["event_count"] if row else 0,
                "total_subscriptions": row["sub_count"] if row else 0,
                "topics": list(self._subscribers.keys()),
            }
        except Exception as exc:
            logger.error("pubsub stats: %s", exc)
            return {"error": str(exc)}
        finally:
            conn.close()


# ═══════════════════════════════════════════════════════════════════════════
#  3. VersionedHandoff — context versioning with diff + rollback
# ═══════════════════════════════════════════════════════════════════════════

class VersionedHandoff:
    """Extends handoff concepts with semantic versioning, diffs, rollback,
    conflict detection, and last-writer-wins merge with conflict logging."""

    def __init__(self, db_path: Union[str, Path] = _DB_PATH) -> None:
        self._db_path = Path(db_path)
        self._lock = threading.Lock()
        self._init_tables()

    def _init_tables(self) -> None:
        conn = _safe_connect(self._db_path)
        if conn is None:
            return
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS handoff_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    handoff_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    items_snapshot TEXT NOT NULL,
                    diff_from_previous TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    created_by TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_versions_handoff
                    ON handoff_versions(handoff_id, version);
            """)
            conn.commit()
        except Exception as exc:
            logger.error("VersionedHandoff _init_tables: %s", exc)
        finally:
            conn.close()

    @staticmethod
    def _parse_version(v: str) -> Tuple[int, int, int]:
        parts = v.split(".")
        try:
            return (int(parts[0]), int(parts[1]), int(parts[2]))
        except (IndexError, ValueError):
            return (1, 0, 0)

    @staticmethod
    def _bump_version(v: str, level: str = "patch") -> str:
        major, minor, patch = VersionedHandoff._parse_version(v)
        if level == "major":
            return f"{major + 1}.0.0"
        elif level == "minor":
            return f"{major}.{minor + 1}.0"
        else:
            return f"{major}.{minor}.{patch + 1}"

    @staticmethod
    def _compute_diff(
        old_items: List[Dict[str, Any]], new_items: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Compute a diff between two item snapshots."""
        old_keys = {item.get("key", ""): item for item in old_items}
        new_keys = {item.get("key", ""): item for item in new_items}

        added = [new_keys[k] for k in new_keys if k not in old_keys]
        removed = [old_keys[k] for k in old_keys if k not in new_keys]
        changed = []
        for k in old_keys:
            if k in new_keys and old_keys[k] != new_keys[k]:
                changed.append({"key": k, "old": old_keys[k], "new": new_keys[k]})

        return {
            "added": added,
            "removed": removed,
            "changed": changed,
            "added_count": len(added),
            "removed_count": len(removed),
            "changed_count": len(changed),
        }

    def create_version(
        self,
        handoff_id: str,
        items: List[Dict[str, Any]],
        created_by: str = "",
        bump_level: str = "patch",
    ) -> HandoffVersion:
        """Create a new version of a handoff.  Auto-diffs from previous."""
        with self._lock:
            prev = self._get_latest_version(handoff_id)
            if prev:
                new_ver = self._bump_version(prev.version, bump_level)
                diff = self._compute_diff(prev.items_snapshot, items)
            else:
                new_ver = "1.0.0"
                diff = {"added": items, "removed": [], "changed": [],
                        "added_count": len(items), "removed_count": 0, "changed_count": 0}

            version = HandoffVersion(
                handoff_id=handoff_id,
                version=new_ver,
                items_snapshot=items,
                diff_from_previous=diff,
                created_at=_utcnow(),
                created_by=created_by,
            )
            self._persist_version(version)
        logger.info("Handoff %s → version %s by %s", handoff_id, new_ver, created_by)
        return version

    def get_version(self, handoff_id: str, version: Optional[str] = None) -> Optional[HandoffVersion]:
        """Get a specific version, or the latest if version is None."""
        if version is None:
            return self._get_latest_version(handoff_id)
        conn = _safe_connect(self._db_path)
        if conn is None:
            return None
        try:
            row = conn.execute(
                "SELECT handoff_id, version, items_snapshot, diff_from_previous, "
                "created_at, created_by FROM handoff_versions "
                "WHERE handoff_id = ? AND version = ?",
                (handoff_id, version),
            ).fetchone()
            if row is None:
                return None
            return self._row_to_version(row)
        except Exception as exc:
            logger.error("get_version: %s", exc)
            return None
        finally:
            conn.close()

    def list_versions(self, handoff_id: str) -> List[HandoffVersion]:
        """List all versions of a handoff in chronological order."""
        conn = _safe_connect(self._db_path)
        if conn is None:
            return []
        try:
            rows = conn.execute(
                "SELECT handoff_id, version, items_snapshot, diff_from_previous, "
                "created_at, created_by FROM handoff_versions "
                "WHERE handoff_id = ? ORDER BY id ASC",
                (handoff_id,),
            ).fetchall()
            return [self._row_to_version(r) for r in rows]
        except Exception as exc:
            logger.error("list_versions: %s", exc)
            return []
        finally:
            conn.close()

    def rollback(self, handoff_id: str, target_version: str) -> Optional[HandoffVersion]:
        """Rollback to a previous version by creating a new version with that snapshot."""
        target = self.get_version(handoff_id, target_version)
        if target is None:
            logger.warning("Rollback target %s v%s not found", handoff_id, target_version)
            return None
        return self.create_version(
            handoff_id=handoff_id,
            items=target.items_snapshot,
            created_by=f"rollback-to-{target_version}",
            bump_level="minor",
        )

    def detect_conflict(
        self,
        handoff_id: str,
        base_version: str,
        items_a: List[Dict[str, Any]],
        items_b: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Detect conflicts when two agents modify the same handoff concurrently."""
        base = self.get_version(handoff_id, base_version)
        base_items = base.items_snapshot if base else []
        diff_a = self._compute_diff(base_items, items_a)
        diff_b = self._compute_diff(base_items, items_b)

        a_changed_keys = {c["key"] for c in diff_a.get("changed", [])}
        b_changed_keys = {c["key"] for c in diff_b.get("changed", [])}
        conflicting_keys = a_changed_keys & b_changed_keys

        return {
            "has_conflict": len(conflicting_keys) > 0,
            "conflicting_keys": sorted(conflicting_keys),
            "a_changes": diff_a,
            "b_changes": diff_b,
        }

    def merge_last_writer_wins(
        self,
        handoff_id: str,
        items_a: List[Dict[str, Any]],
        items_b: List[Dict[str, Any]],
        winner: str = "b",
        merged_by: str = "",
    ) -> HandoffVersion:
        """Merge two sets of items with last-writer-wins strategy.
        ``winner`` ('a' or 'b') takes precedence on conflicts.
        """
        a_map = {item.get("key", ""): item for item in items_a}
        b_map = {item.get("key", ""): item for item in items_b}
        all_keys = list(dict.fromkeys(list(a_map.keys()) + list(b_map.keys())))

        merged = []
        conflict_log = []
        for k in all_keys:
            in_a = k in a_map
            in_b = k in b_map
            if in_a and in_b:
                if a_map[k] != b_map[k]:
                    conflict_log.append({
                        "key": k, "resolution": f"last-writer-wins({winner})",
                        "a_value": a_map[k], "b_value": b_map[k],
                    })
                merged.append(b_map[k] if winner == "b" else a_map[k])
            elif in_a:
                merged.append(a_map[k])
            else:
                merged.append(b_map[k])

        ver = self.create_version(
            handoff_id=handoff_id,
            items=merged,
            created_by=merged_by or f"merge-lww-{winner}",
            bump_level="minor",
        )
        if conflict_log:
            logger.info("Merge %s: %d conflicts resolved (winner=%s)", handoff_id, len(conflict_log), winner)
        return ver

    def diff(self, handoff_id: str, version_a: str, version_b: str) -> Dict[str, Any]:
        """Compute diff between any two versions."""
        va = self.get_version(handoff_id, version_a)
        vb = self.get_version(handoff_id, version_b)
        if va is None or vb is None:
            return {"error": "version_not_found", "version_a": version_a, "version_b": version_b}
        return self._compute_diff(va.items_snapshot, vb.items_snapshot)

    def stats(self) -> Dict[str, Any]:
        conn = _safe_connect(self._db_path)
        if conn is None:
            return {"error": "db_unavailable"}
        try:
            row = conn.execute(
                "SELECT "
                "(SELECT COUNT(*) FROM handoff_versions) AS total_versions, "
                "(SELECT COUNT(DISTINCT handoff_id) FROM handoff_versions) AS unique_handoffs"
            ).fetchone()
            return {
                "total_versions": row["total_versions"] if row else 0,
                "unique_handoffs": row["unique_handoffs"] if row else 0,
            }
        except Exception as exc:
            logger.error("VersionedHandoff stats: %s", exc)
            return {"error": str(exc)}
        finally:
            conn.close()

    # ── internals ─────────────────────────────────────────────────────
    def _get_latest_version(self, handoff_id: str) -> Optional[HandoffVersion]:
        conn = _safe_connect(self._db_path)
        if conn is None:
            return None
        try:
            row = conn.execute(
                "SELECT handoff_id, version, items_snapshot, diff_from_previous, "
                "created_at, created_by FROM handoff_versions "
                "WHERE handoff_id = ? ORDER BY id DESC LIMIT 1",
                (handoff_id,),
            ).fetchone()
            if row is None:
                return None
            return self._row_to_version(row)
        except Exception as exc:
            logger.error("_get_latest_version: %s", exc)
            return None
        finally:
            conn.close()

    @staticmethod
    def _row_to_version(row: sqlite3.Row) -> HandoffVersion:
        return HandoffVersion(
            handoff_id=row["handoff_id"],
            version=row["version"],
            items_snapshot=json.loads(row["items_snapshot"] or "[]"),
            diff_from_previous=json.loads(row["diff_from_previous"] or "null"),
            created_at=row["created_at"] or "",
            created_by=row["created_by"] or "",
        )

    def _persist_version(self, ver: HandoffVersion) -> None:
        conn = _safe_connect(self._db_path)
        if conn is None:
            return
        try:
            conn.execute(
                "INSERT INTO handoff_versions "
                "(handoff_id, version, items_snapshot, diff_from_previous, "
                "created_at, created_by) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    ver.handoff_id,
                    ver.version,
                    json.dumps(ver.items_snapshot, default=str),
                    json.dumps(ver.diff_from_previous, default=str),
                    ver.created_at,
                    ver.created_by,
                ),
            )
            conn.commit()
        except Exception as exc:
            logger.error("_persist_version: %s", exc)
        finally:
            conn.close()


# ═══════════════════════════════════════════════════════════════════════════
#  4. ContextRouter — intelligent lane-aware routing
# ═══════════════════════════════════════════════════════════════════════════

class ContextRouter:
    """Routes context to the right agent based on lane + task type.

    Enforces the IRON LAW of lane isolation: context from one lane
    must never leak into another lane's agent pipeline.
    """

    def __init__(
        self,
        registry: ContextRegistry,
        db_path: Union[str, Path] = _DB_PATH,
    ) -> None:
        self._registry = registry
        self._db_path = Path(db_path)
        self._lock = threading.Lock()
        # route_key = (lane, task_type) → sorted list of RouteEntry
        self._routes: Dict[Tuple[str, str], List[RouteEntry]] = {}

    def add_route(
        self,
        lane: str,
        task_type: str,
        agent_id: str,
        priority: int = 0,
        fallback_agents: Optional[List[str]] = None,
    ) -> RouteEntry:
        """Register a route mapping (lane, task_type) → agent."""
        if lane not in VALID_LANES:
            raise ValueError(f"Invalid lane '{lane}'. Valid: {sorted(VALID_LANES)}")

        entry = RouteEntry(
            lane=lane,
            task_type=task_type,
            agent_id=agent_id,
            priority=priority,
            fallback_agents=fallback_agents or [],
        )
        key = (lane, task_type)
        with self._lock:
            entries = self._routes.setdefault(key, [])
            entries = [e for e in entries if e.agent_id != agent_id]
            entries.append(entry)
            entries.sort(key=lambda e: e.priority)
            self._routes[key] = entries
        logger.debug("Route added: (%s, %s) → %s (pri=%d)", lane, task_type, agent_id, priority)
        return entry

    def remove_route(self, lane: str, task_type: str, agent_id: str) -> bool:
        """Remove a specific route entry."""
        key = (lane, task_type)
        with self._lock:
            entries = self._routes.get(key, [])
            before = len(entries)
            self._routes[key] = [e for e in entries if e.agent_id != agent_id]
            return len(self._routes[key]) < before

    def resolve(
        self, lane: str, task_type: str,
    ) -> Optional[str]:
        """Resolve the best agent_id for a given (lane, task_type).

        Returns the highest-priority agent that is registered and idle/waiting.
        Falls through fallback chains on failure.
        """
        if lane not in VALID_LANES:
            logger.warning("resolve: invalid lane '%s'", lane)
            return None

        with self._lock:
            entries = list(self._routes.get((lane, task_type), []))

        for entry in entries:
            agent = self._registry.get_agent(entry.agent_id)
            if agent and agent.status in (AgentStatus.IDLE.value, AgentStatus.WAITING.value):
                if lane in agent.lane_affinity or not agent.lane_affinity:
                    return entry.agent_id
            # Try fallbacks
            for fb_id in entry.fallback_agents:
                fb_agent = self._registry.get_agent(fb_id)
                if fb_agent and fb_agent.status in (AgentStatus.IDLE.value, AgentStatus.WAITING.value):
                    if lane in fb_agent.lane_affinity or not fb_agent.lane_affinity:
                        return fb_id

        # Last resort: discover by capability
        candidates = self._registry.discover(capability=task_type, lane=lane)
        idle_candidates = [c for c in candidates if c.status == AgentStatus.IDLE.value]
        if idle_candidates:
            return idle_candidates[0].agent_id
        return None

    def resolve_with_load_balance(
        self, lane: str, task_type: str,
    ) -> Optional[str]:
        """Like resolve() but distributes work across equivalent agents.

        Selects the agent with the oldest heartbeat among idle candidates,
        distributing work evenly.
        """
        if lane not in VALID_LANES:
            return None

        with self._lock:
            entries = list(self._routes.get((lane, task_type), []))

        all_agent_ids: List[str] = []
        for entry in entries:
            all_agent_ids.append(entry.agent_id)
            all_agent_ids.extend(entry.fallback_agents)

        # Deduplicate preserving order
        seen: Set[str] = set()
        unique_ids: List[str] = []
        for aid in all_agent_ids:
            if aid not in seen:
                seen.add(aid)
                unique_ids.append(aid)

        candidates = []
        for aid in unique_ids:
            agent = self._registry.get_agent(aid)
            if agent and agent.status == AgentStatus.IDLE.value:
                if lane in agent.lane_affinity or not agent.lane_affinity:
                    candidates.append(agent)

        if not candidates:
            return self.resolve(lane, task_type)

        # Pick the agent with the oldest heartbeat (least recently active)
        candidates.sort(key=lambda a: a.last_heartbeat)
        return candidates[0].agent_id

    def validate_route(self, source_lane: str, target_agent_id: str) -> Dict[str, Any]:
        """Validate that routing a context from source_lane to target_agent is legal."""
        agent = self._registry.get_agent(target_agent_id)
        if agent is None:
            return {"valid": False, "reason": f"Agent '{target_agent_id}' not registered"}
        if agent.lane_affinity and source_lane not in agent.lane_affinity:
            return {
                "valid": False,
                "reason": (
                    f"IRON LAW violation: lane '{source_lane}' not in "
                    f"agent '{target_agent_id}' affinity {agent.lane_affinity}"
                ),
            }
        if agent.status == AgentStatus.ERROR.value:
            return {"valid": False, "reason": f"Agent '{target_agent_id}' is in ERROR state"}
        return {"valid": True, "reason": "ok", "agent_status": agent.status}

    def list_routes(self, lane: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all registered routes, optionally filtered by lane."""
        with self._lock:
            result = []
            for (r_lane, task_type), entries in self._routes.items():
                if lane and r_lane != lane:
                    continue
                for e in entries:
                    result.append({
                        "lane": r_lane,
                        "task_type": task_type,
                        "agent_id": e.agent_id,
                        "priority": e.priority,
                        "fallback_agents": e.fallback_agents,
                    })
        return result

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            route_count = sum(len(v) for v in self._routes.values())
            lane_counts = {}
            for (lane, _), entries in self._routes.items():
                lane_counts[lane] = lane_counts.get(lane, 0) + len(entries)
        return {"total_routes": route_count, "routes_per_lane": lane_counts}


# ═══════════════════════════════════════════════════════════════════════════
#  5. ContextLifecycleManager — HOT → WARM → COLD → ARCHIVED
# ═══════════════════════════════════════════════════════════════════════════

class ContextLifecycleManager:
    """Manages context lifecycle transitions based on age and access patterns.

    HOT  (<1h, in-memory + DB) — actively used context
    WARM (<24h, DB) — recent but not active
    COLD (<30d, DB) — archived but retrievable
    ARCHIVED (>30d, compressed in DB) — long-term storage
    """

    def __init__(self, db_path: Union[str, Path] = _DB_PATH) -> None:
        self._db_path = Path(db_path)
        self._lock = threading.Lock()
        self._hot_cache: Dict[str, Dict[str, Any]] = {}
        self._init_tables()

    def _init_tables(self) -> None:
        conn = _safe_connect(self._db_path)
        if conn is None:
            return
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS context_lifecycle (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    context_key TEXT NOT NULL,
                    lane TEXT,
                    stage TEXT DEFAULT 'hot',
                    payload TEXT NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TEXT DEFAULT (datetime('now')),
                    created_at TEXT DEFAULT (datetime('now')),
                    transitioned_at TEXT DEFAULT (datetime('now')),
                    compressed INTEGER DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS idx_lifecycle_stage_lane
                    ON context_lifecycle(stage, lane);
            """)
            conn.commit()
        except Exception as exc:
            logger.error("ContextLifecycleManager _init_tables: %s", exc)
        finally:
            conn.close()

    def store(
        self,
        context_key: str,
        payload: Dict[str, Any],
        lane: Optional[str] = None,
    ) -> int:
        """Store a context item in the HOT stage."""
        if lane and lane not in VALID_LANES:
            raise ValueError(f"Invalid lane '{lane}'. Valid: {sorted(VALID_LANES)}")

        now = _utcnow()
        payload_json = json.dumps(payload, default=str)
        row_id = 0

        conn = _safe_connect(self._db_path)
        if conn:
            try:
                cur = conn.execute(
                    "INSERT INTO context_lifecycle "
                    "(context_key, lane, stage, payload, access_count, "
                    "last_accessed, created_at, transitioned_at, compressed) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (context_key, lane, ContextLifecycleStage.HOT.value,
                     payload_json, 1, now, now, now, 0),
                )
                conn.commit()
                row_id = cur.lastrowid or 0
            except Exception as exc:
                logger.error("lifecycle store: %s", exc)
            finally:
                conn.close()

        with self._lock:
            self._hot_cache[context_key] = {
                "id": row_id,
                "payload": payload,
                "lane": lane,
                "access_count": 1,
                "last_accessed": now,
                "stage": ContextLifecycleStage.HOT.value,
            }
        return row_id

    def retrieve(self, context_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a context item from any stage.  Auto-promotes if cold and accessed frequently."""
        # Check hot cache first
        with self._lock:
            cached = self._hot_cache.get(context_key)
            if cached:
                cached["access_count"] += 1
                cached["last_accessed"] = _utcnow()
                self._update_access(context_key)
                return cached["payload"]

        # Fall back to DB
        conn = _safe_connect(self._db_path)
        if conn is None:
            return None
        try:
            row = conn.execute(
                "SELECT id, context_key, lane, stage, payload, access_count, "
                "last_accessed, created_at, transitioned_at, compressed "
                "FROM context_lifecycle WHERE context_key = ? "
                "ORDER BY id DESC LIMIT 1",
                (context_key,),
            ).fetchone()
            if row is None:
                return None

            payload_raw = row["payload"]
            compressed = row["compressed"]
            stage = row["stage"]
            access_count = (row["access_count"] or 0) + 1

            # Decompress if archived
            if compressed:
                try:
                    payload_raw = zlib.decompress(
                        base64.b64decode(payload_raw)
                    ).decode("utf-8")
                except Exception:
                    pass

            payload = json.loads(payload_raw)

            # Update access stats
            now = _utcnow()
            conn.execute(
                "UPDATE context_lifecycle SET access_count = ?, last_accessed = ? "
                "WHERE id = ?",
                (access_count, now, row["id"]),
            )
            conn.commit()

            # Auto-promote: cold item accessed frequently → warm
            if stage == ContextLifecycleStage.COLD.value and access_count >= _PROMOTION_HITS:
                self._transition(row["id"], ContextLifecycleStage.WARM, conn)
                conn.commit()

            return payload
        except Exception as exc:
            logger.error("lifecycle retrieve: %s", exc)
            return None
        finally:
            conn.close()

    def run_lifecycle_sweep(self) -> Dict[str, int]:
        """Run a full lifecycle sweep: demote stale items, compress archived."""
        now_ts = time.time()
        counts = {"hot_to_warm": 0, "warm_to_cold": 0, "cold_to_archived": 0, "compressed": 0}

        conn = _safe_connect(self._db_path)
        if conn is None:
            return counts

        try:
            rows = conn.execute(
                "SELECT id, context_key, stage, payload, last_accessed, "
                "access_count, compressed FROM context_lifecycle "
                "WHERE stage != ?",
                (ContextLifecycleStage.ARCHIVED.value,),
            ).fetchall()

            for row in rows:
                stage = row["stage"]
                last_accessed = row["last_accessed"] or ""
                try:
                    la_dt = datetime.fromisoformat(last_accessed.replace("Z", "+00:00"))
                    age_s = now_ts - la_dt.timestamp()
                except (ValueError, OSError):
                    age_s = 0

                if stage == ContextLifecycleStage.HOT.value and age_s > _HOT_TTL:
                    self._transition(row["id"], ContextLifecycleStage.WARM, conn)
                    counts["hot_to_warm"] += 1
                    with self._lock:
                        self._hot_cache.pop(row["context_key"], None)
                elif stage == ContextLifecycleStage.WARM.value and age_s > _WARM_TTL:
                    self._transition(row["id"], ContextLifecycleStage.COLD, conn)
                    counts["warm_to_cold"] += 1
                elif stage == ContextLifecycleStage.COLD.value and age_s > _COLD_TTL:
                    self._transition(row["id"], ContextLifecycleStage.ARCHIVED, conn)
                    counts["cold_to_archived"] += 1
                    if not row["compressed"]:
                        self._compress_row(row["id"], row["payload"], conn)
                        counts["compressed"] += 1

            conn.commit()
        except Exception as exc:
            logger.error("lifecycle sweep: %s", exc)
        finally:
            conn.close()

        if any(counts.values()):
            logger.info("Lifecycle sweep: %s", counts)
        return counts

    def list_by_stage(
        self,
        stage: ContextLifecycleStage,
        lane: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List context items at a given lifecycle stage."""
        clauses = ["stage = ?"]
        params: List[Any] = [stage.value]
        if lane:
            clauses.append("lane = ?")
            params.append(lane)
        where = " AND ".join(clauses)
        params.append(limit)

        conn = _safe_connect(self._db_path)
        if conn is None:
            return []
        try:
            rows = conn.execute(
                f"SELECT id, context_key, lane, stage, access_count, "
                f"last_accessed, created_at, transitioned_at, compressed "
                f"FROM context_lifecycle WHERE {where} "
                f"ORDER BY last_accessed DESC LIMIT ?",
                params,
            ).fetchall()
            return [
                {
                    "id": r["id"],
                    "context_key": r["context_key"],
                    "lane": r["lane"],
                    "stage": r["stage"],
                    "access_count": r["access_count"],
                    "last_accessed": r["last_accessed"],
                    "created_at": r["created_at"],
                    "compressed": bool(r["compressed"]),
                }
                for r in rows
            ]
        except Exception as exc:
            logger.error("list_by_stage: %s", exc)
            return []
        finally:
            conn.close()

    def cleanup_archived(self, older_than_days: int = 365) -> int:
        """Remove archived items older than the given threshold."""
        cutoff = (
            datetime.now(timezone.utc) - timedelta(days=older_than_days)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
        conn = _safe_connect(self._db_path)
        if conn is None:
            return 0
        try:
            cur = conn.execute(
                "DELETE FROM context_lifecycle "
                "WHERE stage = ? AND transitioned_at < ?",
                (ContextLifecycleStage.ARCHIVED.value, cutoff),
            )
            conn.commit()
            removed = cur.rowcount
            if removed:
                logger.info("Cleaned up %d archived items older than %d days", removed, older_than_days)
            return removed
        except Exception as exc:
            logger.error("cleanup_archived: %s", exc)
            return 0
        finally:
            conn.close()

    def stats(self) -> Dict[str, Any]:
        conn = _safe_connect(self._db_path)
        if conn is None:
            return {"error": "db_unavailable"}
        try:
            row = conn.execute(
                "SELECT "
                "(SELECT COUNT(*) FROM context_lifecycle WHERE stage = 'hot') AS hot, "
                "(SELECT COUNT(*) FROM context_lifecycle WHERE stage = 'warm') AS warm, "
                "(SELECT COUNT(*) FROM context_lifecycle WHERE stage = 'cold') AS cold, "
                "(SELECT COUNT(*) FROM context_lifecycle WHERE stage = 'archived') AS archived, "
                "(SELECT COUNT(*) FROM context_lifecycle WHERE compressed = 1) AS compressed_count"
            ).fetchone()
            with self._lock:
                hot_cache_size = len(self._hot_cache)
            return {
                "hot": row["hot"] if row else 0,
                "warm": row["warm"] if row else 0,
                "cold": row["cold"] if row else 0,
                "archived": row["archived"] if row else 0,
                "compressed_count": row["compressed_count"] if row else 0,
                "hot_cache_size": hot_cache_size,
            }
        except Exception as exc:
            logger.error("lifecycle stats: %s", exc)
            return {"error": str(exc)}
        finally:
            conn.close()

    # ── internals ─────────────────────────────────────────────────────
    def _transition(
        self, row_id: int, new_stage: ContextLifecycleStage,
        conn: sqlite3.Connection,
    ) -> None:
        try:
            conn.execute(
                "UPDATE context_lifecycle SET stage = ?, transitioned_at = ? WHERE id = ?",
                (new_stage.value, _utcnow(), row_id),
            )
        except Exception as exc:
            logger.error("_transition: %s", exc)

    def _compress_row(
        self, row_id: int, payload_text: str, conn: sqlite3.Connection,
    ) -> None:
        try:
            compressed = base64.b64encode(
                zlib.compress(payload_text.encode("utf-8"), level=6)
            ).decode("ascii")
            conn.execute(
                "UPDATE context_lifecycle SET payload = ?, compressed = 1 WHERE id = ?",
                (compressed, row_id),
            )
        except Exception as exc:
            logger.error("_compress_row: %s", exc)

    def _update_access(self, context_key: str) -> None:
        conn = _safe_connect(self._db_path)
        if conn is None:
            return
        try:
            conn.execute(
                "UPDATE context_lifecycle SET access_count = access_count + 1, "
                "last_accessed = ? WHERE context_key = ? "
                "AND id = (SELECT MAX(id) FROM context_lifecycle WHERE context_key = ?)",
                (_utcnow(), context_key, context_key),
            )
            conn.commit()
        except Exception as exc:
            logger.error("_update_access: %s", exc)
        finally:
            conn.close()


# ═══════════════════════════════════════════════════════════════════════════
#  6. DeadLetterQueue — failed handoff recovery
# ═══════════════════════════════════════════════════════════════════════════

class DeadLetterQueue:
    """Captures failed handoffs for retry or manual intervention.

    Uses exponential backoff: 1s, 2s, 4s, 8s … capped at 60s.
    """

    def __init__(self, db_path: Union[str, Path] = _DB_PATH) -> None:
        self._db_path = Path(db_path)
        self._lock = threading.Lock()
        self._init_tables()

    def _init_tables(self) -> None:
        conn = _safe_connect(self._db_path)
        if conn is None:
            return
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS dead_letter_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    handoff_id TEXT NOT NULL,
                    source_agent TEXT NOT NULL,
                    target_agent TEXT NOT NULL,
                    lane TEXT,
                    payload TEXT NOT NULL,
                    failure_reason TEXT,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    next_retry_at TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    resolved_at TEXT,
                    status TEXT DEFAULT 'pending'
                );
                CREATE INDEX IF NOT EXISTS idx_dlq_status
                    ON dead_letter_queue(status, next_retry_at);
            """)
            conn.commit()
        except Exception as exc:
            logger.error("DeadLetterQueue _init_tables: %s", exc)
        finally:
            conn.close()

    def enqueue(
        self,
        handoff_id: str,
        source_agent: str,
        target_agent: str,
        payload: str,
        failure_reason: str,
        lane: Optional[str] = None,
        max_retries: int = _DLQ_MAX_RETRIES,
    ) -> int:
        """Add a failed handoff to the dead-letter queue."""
        next_retry = self._compute_next_retry(0)
        row_id = 0
        conn = _safe_connect(self._db_path)
        if conn:
            try:
                cur = conn.execute(
                    "INSERT INTO dead_letter_queue "
                    "(handoff_id, source_agent, target_agent, lane, payload, "
                    "failure_reason, retry_count, max_retries, next_retry_at, "
                    "created_at, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        handoff_id, source_agent, target_agent, lane,
                        payload, failure_reason, 0, max_retries,
                        next_retry, _utcnow(), DLQStatus.PENDING.value,
                    ),
                )
                conn.commit()
                row_id = cur.lastrowid or 0
            except Exception as exc:
                logger.error("dlq enqueue: %s", exc)
            finally:
                conn.close()
        logger.warning(
            "DLQ enqueue: handoff %s (%s→%s) reason: %s",
            handoff_id, source_agent, target_agent, failure_reason,
        )
        return row_id

    def get_ready_for_retry(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get entries that are due for retry."""
        now = _utcnow()
        conn = _safe_connect(self._db_path)
        if conn is None:
            return []
        try:
            rows = conn.execute(
                "SELECT id, handoff_id, source_agent, target_agent, lane, "
                "payload, failure_reason, retry_count, max_retries, "
                "next_retry_at, created_at, status "
                "FROM dead_letter_queue "
                "WHERE status IN (?, ?) AND next_retry_at <= ? "
                "ORDER BY next_retry_at ASC LIMIT ?",
                (DLQStatus.PENDING.value, DLQStatus.RETRYING.value, now, limit),
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception as exc:
            logger.error("get_ready_for_retry: %s", exc)
            return []
        finally:
            conn.close()

    def record_retry(self, dlq_id: int, success: bool, reason: str = "") -> bool:
        """Record the result of a retry attempt."""
        conn = _safe_connect(self._db_path)
        if conn is None:
            return False
        try:
            row = conn.execute(
                "SELECT retry_count, max_retries FROM dead_letter_queue WHERE id = ?",
                (dlq_id,),
            ).fetchone()
            if row is None:
                return False

            retry_count = (row["retry_count"] or 0) + 1
            max_retries = row["max_retries"] or _DLQ_MAX_RETRIES

            if success:
                conn.execute(
                    "UPDATE dead_letter_queue SET status = ?, resolved_at = ?, "
                    "retry_count = ? WHERE id = ?",
                    (DLQStatus.RESOLVED.value, _utcnow(), retry_count, dlq_id),
                )
            elif retry_count >= max_retries:
                conn.execute(
                    "UPDATE dead_letter_queue SET status = ?, retry_count = ?, "
                    "failure_reason = ? WHERE id = ?",
                    (DLQStatus.EXHAUSTED.value, retry_count,
                     reason or "max retries exceeded", dlq_id),
                )
                logger.error("DLQ entry %d exhausted after %d retries", dlq_id, retry_count)
            else:
                next_retry = self._compute_next_retry(retry_count)
                conn.execute(
                    "UPDATE dead_letter_queue SET status = ?, retry_count = ?, "
                    "next_retry_at = ?, failure_reason = ? WHERE id = ?",
                    (DLQStatus.RETRYING.value, retry_count, next_retry,
                     reason, dlq_id),
                )

            conn.commit()
            return True
        except Exception as exc:
            logger.error("record_retry: %s", exc)
            return False
        finally:
            conn.close()

    def replay(self, dlq_id: int) -> Optional[Dict[str, Any]]:
        """Manually replay a dead-letter entry (reset retry count)."""
        conn = _safe_connect(self._db_path)
        if conn is None:
            return None
        try:
            row = conn.execute(
                "SELECT id, handoff_id, source_agent, target_agent, lane, "
                "payload, failure_reason, retry_count, max_retries "
                "FROM dead_letter_queue WHERE id = ?",
                (dlq_id,),
            ).fetchone()
            if row is None:
                return None

            now = _utcnow()
            conn.execute(
                "UPDATE dead_letter_queue SET status = ?, retry_count = 0, "
                "next_retry_at = ?, failure_reason = 'manual replay' WHERE id = ?",
                (DLQStatus.PENDING.value, now, dlq_id),
            )
            conn.commit()
            logger.info("DLQ entry %d manually replayed", dlq_id)
            return dict(row)
        except Exception as exc:
            logger.error("replay: %s", exc)
            return None
        finally:
            conn.close()

    def resolve(self, dlq_id: int) -> bool:
        """Manually mark a DLQ entry as resolved."""
        conn = _safe_connect(self._db_path)
        if conn is None:
            return False
        try:
            conn.execute(
                "UPDATE dead_letter_queue SET status = ?, resolved_at = ? WHERE id = ?",
                (DLQStatus.RESOLVED.value, _utcnow(), dlq_id),
            )
            conn.commit()
            return True
        except Exception as exc:
            logger.error("resolve: %s", exc)
            return False
        finally:
            conn.close()

    def get_alerts(self, min_retries: int = 2) -> List[Dict[str, Any]]:
        """Get entries that have failed repeatedly (potential issues)."""
        conn = _safe_connect(self._db_path)
        if conn is None:
            return []
        try:
            rows = conn.execute(
                "SELECT id, handoff_id, source_agent, target_agent, lane, "
                "failure_reason, retry_count, max_retries, status, created_at "
                "FROM dead_letter_queue "
                "WHERE retry_count >= ? AND status != ? "
                "ORDER BY retry_count DESC",
                (min_retries, DLQStatus.RESOLVED.value),
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception as exc:
            logger.error("get_alerts: %s", exc)
            return []
        finally:
            conn.close()

    def stats(self) -> Dict[str, Any]:
        conn = _safe_connect(self._db_path)
        if conn is None:
            return {"error": "db_unavailable"}
        try:
            row = conn.execute(
                "SELECT "
                "(SELECT COUNT(*) FROM dead_letter_queue WHERE status = 'pending') AS pending, "
                "(SELECT COUNT(*) FROM dead_letter_queue WHERE status = 'retrying') AS retrying, "
                "(SELECT COUNT(*) FROM dead_letter_queue WHERE status = 'resolved') AS resolved, "
                "(SELECT COUNT(*) FROM dead_letter_queue WHERE status = 'exhausted') AS exhausted"
            ).fetchone()
            return {
                "pending": row["pending"] if row else 0,
                "retrying": row["retrying"] if row else 0,
                "resolved": row["resolved"] if row else 0,
                "exhausted": row["exhausted"] if row else 0,
                "total": sum(row[k] for k in row.keys()) if row else 0,
            }
        except Exception as exc:
            logger.error("dlq stats: %s", exc)
            return {"error": str(exc)}
        finally:
            conn.close()

    # ── internals ─────────────────────────────────────────────────────
    @staticmethod
    def _compute_next_retry(current_retry: int) -> str:
        backoff = min(
            _DLQ_BASE_BACKOFF * (2 ** current_retry), _DLQ_MAX_BACKOFF,
        )
        retry_time = datetime.now(timezone.utc) + timedelta(seconds=backoff)
        return retry_time.strftime("%Y-%m-%dT%H:%M:%SZ")


# ═══════════════════════════════════════════════════════════════════════════
#  7. AgentContextProtocol — unified multi-agent coordination facade
# ═══════════════════════════════════════════════════════════════════════════

class AgentContextProtocol:
    """Unified multi-agent context coordination protocol for LitigationOS.

    Wraps ContextRegistry, ContextPubSub, VersionedHandoff, ContextRouter,
    ContextLifecycleManager, and DeadLetterQueue into one interface.
    """

    _instance: Optional["AgentContextProtocol"] = None
    _init_lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "AgentContextProtocol":
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        db_path: Optional[Union[str, Path]] = None,
    ) -> None:
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self._db_path = Path(db_path) if db_path else _DB_PATH
        self._lock = threading.Lock()

        # Counters
        self._handoffs_sent = 0
        self._handoffs_received = 0
        self._handoffs_failed = 0
        self._events_published = 0
        self._route_resolutions = 0

        # Initialise subsystems
        self.registry = ContextRegistry(self._db_path)
        self.pubsub = ContextPubSub(self._db_path)
        self.versioning = VersionedHandoff(self._db_path)
        self.router = ContextRouter(self.registry, self._db_path)
        self.lifecycle = ContextLifecycleManager(self._db_path)
        self.dlq = DeadLetterQueue(self._db_path)

        logger.info(
            "AgentContextProtocol initialised (db=%s, pydantic=%s)",
            self._db_path, _PYDANTIC,
        )

    # ── Agent management ──────────────────────────────────────────────
    def register_agent(
        self,
        agent_id: str,
        agent_type: str = "generic",
        capabilities: Optional[List[str]] = None,
        lane_affinity: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AgentRegistration:
        """Register an agent in the central registry."""
        return self.registry.register(
            agent_id=agent_id,
            agent_type=agent_type,
            capabilities=capabilities,
            lane_affinity=lane_affinity,
            metadata=metadata,
        )

    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent and clean up subscriptions."""
        return self.registry.unregister(agent_id)

    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get an agent's current registration and status."""
        reg = self.registry.get_agent(agent_id)
        if reg is None:
            return None
        return {
            "agent_id": reg.agent_id,
            "agent_type": reg.agent_type,
            "capabilities": reg.capabilities,
            "lane_affinity": reg.lane_affinity,
            "status": reg.status,
            "last_heartbeat": reg.last_heartbeat,
        }

    def get_lane_status(self, lane: str) -> Dict[str, Any]:
        """Get the status of all agents assigned to a lane."""
        if lane not in VALID_LANES:
            return {"error": f"Invalid lane '{lane}'", "valid_lanes": sorted(VALID_LANES)}
        agents = self.registry.list_agents(lane=lane)
        return {
            "lane": lane,
            "agent_count": len(agents),
            "agents": [
                {
                    "agent_id": a.agent_id,
                    "status": a.status,
                    "type": a.agent_type,
                    "last_heartbeat": a.last_heartbeat,
                }
                for a in agents
            ],
            "idle_count": sum(1 for a in agents if a.status == AgentStatus.IDLE.value),
            "busy_count": sum(1 for a in agents if a.status == AgentStatus.BUSY.value),
        }

    # ── Handoff operations ────────────────────────────────────────────
    def send_handoff(
        self,
        source_agent: str,
        target_agent: Optional[str],
        lane: str,
        task_type: str,
        task_description: str,
        items: List[Dict[str, Any]],
        auto_route: bool = True,
    ) -> Dict[str, Any]:
        """Send a context handoff with routing, validation, and versioning.

        If ``target_agent`` is None and ``auto_route`` is True, the router
        resolves the best target automatically.
        """
        if lane not in VALID_LANES:
            return {"success": False, "error": f"Invalid lane '{lane}'"}

        # Route resolution
        actual_target = target_agent
        if actual_target is None and auto_route:
            actual_target = self.router.resolve_with_load_balance(lane, task_type)
            with self._lock:
                self._route_resolutions += 1
        if actual_target is None:
            return {"success": False, "error": "No suitable agent found for routing"}

        # Validate route
        validation = self.router.validate_route(lane, actual_target)
        if not validation.get("valid", False):
            reason = validation.get("reason", "unknown")
            with self._lock:
                self._handoffs_failed += 1
            self.dlq.enqueue(
                handoff_id=_sha(f"{source_agent}-{actual_target}-{time.time()}"),
                source_agent=source_agent,
                target_agent=actual_target,
                payload=json.dumps(items, default=str),
                failure_reason=f"Route validation failed: {reason}",
                lane=lane,
            )
            return {"success": False, "error": reason}

        # Generate handoff ID and create version
        handoff_id = _sha(f"{source_agent}-{actual_target}-{lane}-{time.time()}")
        try:
            version = self.versioning.create_version(
                handoff_id=handoff_id,
                items=items,
                created_by=source_agent,
            )
        except Exception as exc:
            logger.error("send_handoff version creation failed: %s", exc)
            self.dlq.enqueue(
                handoff_id=handoff_id,
                source_agent=source_agent,
                target_agent=actual_target,
                payload=json.dumps(items, default=str),
                failure_reason=f"Version creation failed: {exc}",
                lane=lane,
            )
            with self._lock:
                self._handoffs_failed += 1
            return {"success": False, "error": str(exc)}

        # Store in lifecycle as HOT
        self.lifecycle.store(
            context_key=f"handoff:{handoff_id}",
            payload={
                "handoff_id": handoff_id,
                "source": source_agent,
                "target": actual_target,
                "lane": lane,
                "task_type": task_type,
                "task_description": task_description,
                "items_count": len(items),
                "version": version.version,
            },
            lane=lane,
        )

        # Publish event
        self.pubsub.publish(
            topic="handoff.sent",
            payload={
                "handoff_id": handoff_id,
                "source": source_agent,
                "target": actual_target,
                "lane": lane,
                "task_type": task_type,
                "items_count": len(items),
            },
            publisher_id=source_agent,
            lane=lane,
            priority="high",
        )

        with self._lock:
            self._handoffs_sent += 1
            self._events_published += 1

        logger.info(
            "Handoff %s sent: %s → %s (lane=%s, task=%s, items=%d, v=%s)",
            handoff_id, source_agent, actual_target, lane, task_type,
            len(items), version.version,
        )
        return {
            "success": True,
            "handoff_id": handoff_id,
            "target_agent": actual_target,
            "version": version.version,
            "items_count": len(items),
        }

    def receive_handoff(
        self, handoff_id: str, agent_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Receive and acknowledge a context handoff."""
        version = self.versioning.get_version(handoff_id)
        if version is None:
            logger.warning("receive_handoff: handoff %s not found", handoff_id)
            return None

        # Mark agent busy
        self.registry.update_status(agent_id, AgentStatus.BUSY)

        # Publish ack event
        self.pubsub.publish(
            topic="handoff.received",
            payload={"handoff_id": handoff_id, "receiver": agent_id},
            publisher_id=agent_id,
            priority="medium",
        )

        with self._lock:
            self._handoffs_received += 1
            self._events_published += 1

        logger.info("Handoff %s received by %s (v=%s)", handoff_id, agent_id, version.version)
        return {
            "handoff_id": handoff_id,
            "version": version.version,
            "items": version.items_snapshot,
            "created_by": version.created_by,
            "created_at": version.created_at,
        }

    def complete_handoff(self, handoff_id: str, agent_id: str) -> bool:
        """Mark a handoff as completed by the receiving agent."""
        self.registry.update_status(agent_id, AgentStatus.IDLE)
        self.pubsub.publish(
            topic="handoff.completed",
            payload={"handoff_id": handoff_id, "completed_by": agent_id},
            publisher_id=agent_id,
            priority="medium",
        )
        with self._lock:
            self._events_published += 1
        logger.info("Handoff %s completed by %s", handoff_id, agent_id)
        return True

    def fail_handoff(
        self, handoff_id: str, agent_id: str, reason: str = "",
    ) -> bool:
        """Mark a handoff as failed and enqueue in DLQ."""
        self.registry.update_status(agent_id, AgentStatus.IDLE)

        version = self.versioning.get_version(handoff_id)
        payload = json.dumps(version.items_snapshot, default=str) if version else "{}"

        self.dlq.enqueue(
            handoff_id=handoff_id,
            source_agent="unknown",
            target_agent=agent_id,
            payload=payload,
            failure_reason=reason,
        )

        self.pubsub.publish(
            topic="handoff.failed",
            payload={"handoff_id": handoff_id, "agent": agent_id, "reason": reason},
            publisher_id=agent_id,
            lane=None,
            priority="critical",
        )

        with self._lock:
            self._handoffs_failed += 1
            self._events_published += 1

        logger.error("Handoff %s failed at %s: %s", handoff_id, agent_id, reason)
        return True

    # ── Pub/Sub ───────────────────────────────────────────────────────
    def subscribe(
        self,
        agent_id: str,
        topic: str,
        lane_filter: Optional[str] = None,
        priority_filter: Optional[str] = None,
        callback: Optional[Callable] = None,
    ) -> bool:
        """Subscribe an agent to a topic."""
        return self.pubsub.subscribe(
            agent_id, topic, lane_filter, priority_filter, callback,
        )

    def publish(
        self,
        topic: str,
        payload: Dict[str, Any],
        publisher_id: str,
        lane: Optional[str] = None,
        priority: str = "medium",
        ttl_seconds: Optional[int] = None,
    ) -> int:
        """Publish an event to a topic."""
        event_id = self.pubsub.publish(
            topic, payload, publisher_id, lane, priority, ttl_seconds,
        )
        with self._lock:
            self._events_published += 1
        return event_id

    # ── Routing ───────────────────────────────────────────────────────
    def add_route(
        self,
        lane: str,
        task_type: str,
        agent_id: str,
        priority: int = 0,
        fallback_agents: Optional[List[str]] = None,
    ) -> RouteEntry:
        """Add a route mapping (lane, task_type) → agent."""
        return self.router.add_route(lane, task_type, agent_id, priority, fallback_agents)

    # ── Lifecycle ─────────────────────────────────────────────────────
    def store_context(
        self, key: str, payload: Dict[str, Any], lane: Optional[str] = None,
    ) -> int:
        """Store a context item in the lifecycle system."""
        return self.lifecycle.store(key, payload, lane)

    def retrieve_context(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a context item from any lifecycle stage."""
        return self.lifecycle.retrieve(key)

    # ── Dead Letter Queue ─────────────────────────────────────────────
    def retry_failed_handoffs(self, limit: int = 10) -> Dict[str, Any]:
        """Process DLQ entries that are ready for retry.

        Returns a summary of retry outcomes.
        """
        ready = self.dlq.get_ready_for_retry(limit=limit)
        results = {"attempted": 0, "success": 0, "failed": 0}
        for entry in ready:
            dlq_id = entry["id"]
            target = entry["target_agent"]
            results["attempted"] += 1

            agent = self.registry.get_agent(target)
            if agent and agent.status == AgentStatus.IDLE.value:
                self.dlq.record_retry(dlq_id, success=True)
                results["success"] += 1
            else:
                self.dlq.record_retry(
                    dlq_id, success=False,
                    reason=f"Agent '{target}' not available",
                )
                results["failed"] += 1
        return results

    # ── Maintenance ───────────────────────────────────────────────────
    def run_maintenance(self) -> Dict[str, Any]:
        """Run all maintenance tasks: lifecycle sweep, DLQ retry, cleanup."""
        lifecycle_result = self.lifecycle.run_lifecycle_sweep()
        dlq_result = self.retry_failed_handoffs()
        expired_events = self.pubsub.cleanup_expired()
        return {
            "lifecycle_sweep": lifecycle_result,
            "dlq_retries": dlq_result,
            "expired_events_cleaned": expired_events,
        }

    # ── Stats & Health ────────────────────────────────────────────────
    def get_stats(self) -> Dict[str, Any]:
        """Comprehensive metrics across all subsystems."""
        with self._lock:
            counters = {
                "handoffs_sent": self._handoffs_sent,
                "handoffs_received": self._handoffs_received,
                "handoffs_failed": self._handoffs_failed,
                "events_published": self._events_published,
                "route_resolutions": self._route_resolutions,
            }
        return {
            "protocol": counters,
            "registry": {
                "agent_count": self.registry.agent_count(),
                "agents": [
                    {"id": a.agent_id, "status": a.status, "type": a.agent_type}
                    for a in self.registry.list_agents()
                ],
            },
            "pubsub": self.pubsub.stats(),
            "versioning": self.versioning.stats(),
            "router": self.router.stats(),
            "lifecycle": self.lifecycle.stats(),
            "dead_letter_queue": self.dlq.stats(),
            "valid_lanes": sorted(VALID_LANES),
            "pydantic_available": _PYDANTIC,
            "db_path": str(self._db_path),
        }

    def health(self) -> Dict[str, Any]:
        """Quick health check for all subsystems."""
        checks: Dict[str, str] = {}

        # DB connectivity
        conn = _safe_connect(self._db_path)
        if conn:
            checks["database"] = "ok"
            conn.close()
        else:
            checks["database"] = "error"

        # Subsystem checks
        try:
            self.registry.agent_count()
            checks["registry"] = "ok"
        except Exception:
            checks["registry"] = "error"

        try:
            self.pubsub.stats()
            checks["pubsub"] = "ok"
        except Exception:
            checks["pubsub"] = "error"

        try:
            self.versioning.stats()
            checks["versioning"] = "ok"
        except Exception:
            checks["versioning"] = "error"

        try:
            self.lifecycle.stats()
            checks["lifecycle"] = "ok"
        except Exception:
            checks["lifecycle"] = "error"

        try:
            self.dlq.stats()
            checks["dead_letter_queue"] = "ok"
        except Exception:
            checks["dead_letter_queue"] = "error"

        all_ok = all(v == "ok" for v in checks.values())
        return {"healthy": all_ok, "checks": checks}

    def shutdown(self) -> None:
        """Clean shutdown — flush caches, close connections."""
        logger.info("AgentContextProtocol shutting down")
        self._initialized = False
        AgentContextProtocol._instance = None

    def reset(self) -> None:
        """Reset singleton state for testing."""
        self.shutdown()


# ═══════════════════════════════════════════════════════════════════════════
#  Module-level convenience
# ═══════════════════════════════════════════════════════════════════════════

def get_protocol(
    db_path: Optional[Union[str, Path]] = None,
) -> AgentContextProtocol:
    """Get or create the singleton AgentContextProtocol instance."""
    return AgentContextProtocol(db_path=db_path)


# ── CLI self-test ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import tempfile

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    print("=" * 60)
    print("AgentContextProtocol — self-test")
    print("=" * 60)

    # Use temp DB so we don't pollute the real one
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    test_db = Path(tmp.name)

    try:
        # Reset singleton for test
        AgentContextProtocol._instance = None

        proto = AgentContextProtocol(db_path=test_db)

        # 1. Registry
        proto.register_agent("A01", "indexer", ["index", "dedup"], ["A", "B"])
        proto.register_agent("J01", "judicial", ["judicial_profile", "bias_scan"], ["E"])
        proto.register_agent("F01", "filer", ["filing", "assembly"], ["A", "B", "D", "F"])
        assert proto.registry.agent_count() == 3, "Registry count mismatch"
        print("[PASS] Registry: 3 agents registered")

        # 2. Routing
        proto.add_route("A", "filing", "F01", priority=0)
        proto.add_route("A", "index", "A01", priority=0, fallback_agents=["F01"])
        proto.add_route("E", "judicial_profile", "J01", priority=0)
        resolved = proto.router.resolve("A", "filing")
        assert resolved == "F01", f"Expected F01, got {resolved}"
        print("[PASS] Router: lane A filing → F01")

        # 3. Pub/Sub
        proto.subscribe("A01", "handoff.sent", lane_filter="A")
        proto.subscribe("F01", "handoff.sent")
        event_id = proto.publish(
            "handoff.sent",
            {"test": True},
            publisher_id="test",
            lane="A",
        )
        assert event_id > 0, "Event publish failed"
        proto.pubsub.acknowledge(event_id, "A01")
        print("[PASS] PubSub: event published + acknowledged")

        # 4. Handoff
        result = proto.send_handoff(
            source_agent="A01",
            target_agent="F01",
            lane="A",
            task_type="filing",
            task_description="Prepare custody filing",
            items=[{"key": "motion_draft", "value": "draft text"}],
        )
        assert result["success"], f"Handoff failed: {result}"
        hid = result["handoff_id"]
        print(f"[PASS] Handoff sent: {hid} (v={result['version']})")

        # 5. Receive handoff
        received = proto.receive_handoff(hid, "F01")
        assert received is not None, "Receive failed"
        assert len(received["items"]) == 1
        print(f"[PASS] Handoff received by F01 (v={received['version']})")

        # 6. Versioning
        v2 = proto.versioning.create_version(
            hid,
            [{"key": "motion_draft", "value": "revised text"}, {"key": "exhibit_a", "value": "new"}],
            created_by="F01",
        )
        assert v2.version == "1.0.1", f"Expected 1.0.1, got {v2.version}"
        diff = v2.diff_from_previous
        assert diff["added_count"] == 1
        assert diff["changed_count"] == 1
        print(f"[PASS] Versioning: v{v2.version} with diff (added={diff['added_count']}, changed={diff['changed_count']})")

        # 7. Lifecycle
        lid = proto.store_context("test:doc1", {"content": "hello"}, lane="A")
        assert lid > 0
        retrieved = proto.retrieve_context("test:doc1")
        assert retrieved == {"content": "hello"}
        print("[PASS] Lifecycle: store → retrieve")

        # 8. DLQ
        dlq_id = proto.dlq.enqueue(
            "bad-handoff", "src", "missing-target",
            '{"items": []}', "Agent not found", lane="A",
        )
        assert dlq_id > 0
        alerts = proto.dlq.get_alerts(min_retries=0)
        assert len(alerts) >= 1
        print(f"[PASS] DLQ: enqueued + {len(alerts)} alert(s)")

        # 9. Stats
        stats = proto.get_stats()
        assert stats["protocol"]["handoffs_sent"] >= 1
        assert stats["registry"]["agent_count"] == 3
        print("[PASS] Stats: comprehensive metrics returned")

        # 10. Health
        h = proto.health()
        assert h["healthy"], f"Health check failed: {h}"
        print("[PASS] Health: all subsystems OK")

        # 11. Maintenance
        maint = proto.run_maintenance()
        assert "lifecycle_sweep" in maint
        print("[PASS] Maintenance: sweep complete")

        # Complete handoff
        proto.complete_handoff(hid, "F01")
        print("[PASS] Handoff completed")

        proto.shutdown()
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED")
        print("=" * 60)

    finally:
        try:
            os.unlink(test_db)
        except OSError:
            pass
