"""
Omega Event Bus — The Nervous System of LitigationOS.
=====================================================

CQRS Event Store + Pub/Sub + Circuit Breaker + Dead Letter Queue + Backpressure.

Architecture:
  - Events are APPENDED to omega_event_store (immutable event log — CQRS)
  - Subscribers register patterns (glob-style: "file.*", "evidence.quote_added", "*")
  - EventBus dispatches events to matching subscribers by priority
  - CircuitBreaker protects individual engines from cascading failures
  - DeadLetterQueue catches events that exceed max_retries
  - BackpressureManager defers low-priority events when queue exceeds threshold

Tables used (in litigation_context.db):
  - omega_event_store: Immutable event log
  - omega_event_subscriptions: Registered subscribers
  - omega_circuit_breaker_state: Per-engine circuit state
  - omega_engine_health: Engine health records
  - omega_saga_instances: Multi-step transaction tracking
  - omega_event_projections: Materialized view state
  - omega_event_snapshots: Projection snapshots for recovery
"""

import fnmatch
import importlib
import json
import logging
import os
import sqlite3
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Callable, Optional

logger = logging.getLogger("daemon.event_bus")


def _get_db_path() -> str:
    """Resolve litigation_context.db path."""
    # Walk up from this file to find repo root
    current = os.path.dirname(os.path.abspath(__file__))
    for _ in range(6):
        candidate = os.path.join(current, "litigation_context.db")
        if os.path.exists(candidate):
            return candidate
        current = os.path.dirname(current)
    return os.path.normpath(os.path.join(
        os.path.dirname(__file__), "..", "..", "litigation_context.db"
    ))


def _connect(db_path: str = None) -> sqlite3.Connection:
    """Open connection with mandatory PRAGMAs (Rule 18)."""
    path = db_path or _get_db_path()
    conn = sqlite3.connect(path, timeout=60)
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.row_factory = sqlite3.Row
    return conn


# ═══════════════════════════════════════════════════════════════════════════════
# Class 1: CircuitBreaker
# ═══════════════════════════════════════════════════════════════════════════════

class CircuitBreaker:
    """Per-engine circuit breaker to prevent cascading failures.

    States:
      CLOSED   -> Normal. Calls pass through. Track failures.
      OPEN     -> Blocked. Failures exceeded threshold within window.
                  After cooldown_sec, transitions to HALF_OPEN.
      HALF_OPEN -> Testing. Allow half_open_max_calls probe calls.
                   If probe succeeds -> CLOSED. If fails -> OPEN again.

    Default: 3 failures in 60s -> OPEN for 300s (5 min).
    """

    def __init__(self, engine_name: str, db_path: str = None,
                 failure_threshold: int = 3, failure_window_sec: int = 60,
                 cooldown_sec: int = 300, half_open_max_calls: int = 1):
        self.engine_name = engine_name
        self._db_path = db_path
        self.failure_threshold = failure_threshold
        self.failure_window_sec = failure_window_sec
        self.cooldown_sec = cooldown_sec
        self.half_open_max_calls = half_open_max_calls
        # In-memory state (synced to DB periodically)
        self._state = "closed"
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_at: Optional[datetime] = None
        self._last_success_at: Optional[datetime] = None
        self._cooldown_until: Optional[datetime] = None
        self._half_open_calls = 0
        self._failure_timestamps: list[datetime] = []
        # Load persisted state
        self._load_state()

    def _load_state(self):
        """Load circuit breaker state from DB."""
        try:
            conn = _connect(self._db_path)
            row = conn.execute(
                "SELECT * FROM omega_circuit_breaker_state WHERE engine_name = ?",
                (self.engine_name,)
            ).fetchone()
            if row:
                self._state = row["state"]
                self._failure_count = row["failure_count"]
                self._success_count = row["success_count"]
                if row["last_failure_at"]:
                    self._last_failure_at = datetime.fromisoformat(row["last_failure_at"])
                if row["last_success_at"]:
                    self._last_success_at = datetime.fromisoformat(row["last_success_at"])
                if row["cooldown_until"]:
                    self._cooldown_until = datetime.fromisoformat(row["cooldown_until"])
            conn.close()
        except Exception as e:
            logger.warning("CircuitBreaker._load_state(%s): %s", self.engine_name, e)

    def _persist_state(self):
        """Save circuit breaker state to DB."""
        try:
            conn = _connect(self._db_path)
            conn.execute("""
                INSERT INTO omega_circuit_breaker_state
                    (engine_name, state, failure_count, success_count,
                     last_failure_at, last_success_at, cooldown_until,
                     failure_threshold, failure_window_sec, cooldown_sec, half_open_max_calls)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(engine_name) DO UPDATE SET
                    state=excluded.state, failure_count=excluded.failure_count,
                    success_count=excluded.success_count,
                    last_failure_at=excluded.last_failure_at,
                    last_success_at=excluded.last_success_at,
                    cooldown_until=excluded.cooldown_until
            """, (
                self.engine_name, self._state, self._failure_count, self._success_count,
                self._last_failure_at.isoformat() if self._last_failure_at else None,
                self._last_success_at.isoformat() if self._last_success_at else None,
                self._cooldown_until.isoformat() if self._cooldown_until else None,
                self.failure_threshold, self.failure_window_sec,
                self.cooldown_sec, self.half_open_max_calls,
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error("CircuitBreaker._persist_state(%s): %s", self.engine_name, e)

    @property
    def state(self) -> str:
        """Current state, with automatic OPEN -> HALF_OPEN transition."""
        if self._state == "open" and self._cooldown_until:
            if datetime.utcnow() >= self._cooldown_until:
                self._state = "half_open"
                self._half_open_calls = 0
                self._persist_state()
                logger.info("CircuitBreaker(%s): OPEN -> HALF_OPEN", self.engine_name)
        return self._state

    def allow_request(self) -> bool:
        """Check if a request should be allowed through."""
        current = self.state  # triggers auto-transition
        if current == "closed":
            return True
        elif current == "half_open":
            return self._half_open_calls < self.half_open_max_calls
        else:  # open
            return False

    def record_success(self):
        """Record a successful call."""
        self._success_count += 1
        self._last_success_at = datetime.utcnow()
        if self._state == "half_open":
            self._state = "closed"
            self._failure_count = 0
            self._failure_timestamps.clear()
            logger.info("CircuitBreaker(%s): HALF_OPEN -> CLOSED (recovered)", self.engine_name)
        self._persist_state()

    def record_failure(self):
        """Record a failed call. May trip the breaker."""
        now = datetime.utcnow()
        self._failure_count += 1
        self._last_failure_at = now
        self._failure_timestamps.append(now)

        # Prune old failures outside the window
        cutoff = now - timedelta(seconds=self.failure_window_sec)
        self._failure_timestamps = [t for t in self._failure_timestamps if t >= cutoff]

        if self._state == "half_open":
            # Probe failed — back to OPEN
            self._state = "open"
            self._cooldown_until = now + timedelta(seconds=self.cooldown_sec)
            logger.warning("CircuitBreaker(%s): HALF_OPEN -> OPEN (probe failed)", self.engine_name)
        elif self._state == "closed":
            # Check if failures in window exceed threshold
            if len(self._failure_timestamps) >= self.failure_threshold:
                self._state = "open"
                self._cooldown_until = now + timedelta(seconds=self.cooldown_sec)
                logger.warning(
                    "CircuitBreaker(%s): CLOSED -> OPEN (%d failures in %ds)",
                    self.engine_name, len(self._failure_timestamps), self.failure_window_sec
                )
        self._persist_state()

    def reset(self):
        """Manually reset to CLOSED state."""
        self._state = "closed"
        self._failure_count = 0
        self._success_count = 0
        self._failure_timestamps.clear()
        self._cooldown_until = None
        self._half_open_calls = 0
        self._persist_state()
        logger.info("CircuitBreaker(%s): Manually RESET to CLOSED", self.engine_name)

    def to_dict(self) -> dict:
        """Serialize circuit breaker state to dict."""
        return {
            "engine_name": self.engine_name,
            "state": self.state,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure_at": self._last_failure_at.isoformat() if self._last_failure_at else None,
            "cooldown_until": self._cooldown_until.isoformat() if self._cooldown_until else None,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Class 2: DeadLetterQueue
# ═══════════════════════════════════════════════════════════════════════════════

class DeadLetterQueue:
    """Captures events that have exhausted all retry attempts.

    Dead-lettered events are moved to status='dead_letter' in omega_event_store
    and can be reviewed, retried manually, or purged.
    """

    def __init__(self, db_path: str = None):
        self._db_path = db_path

    def send_to_dead_letter(self, event_id: str, error_msg: str):
        """Move an event to dead letter status."""
        conn = _connect(self._db_path)
        conn.execute(
            "UPDATE omega_event_store SET status = 'dead_letter', error_msg = ?, "
            "processed_at = datetime('now') WHERE event_id = ?",
            (error_msg, event_id)
        )
        conn.commit()
        conn.close()
        logger.warning("DeadLetterQueue: event %s dead-lettered: %s", event_id, error_msg)

    def get_dead_letters(self, limit: int = 50) -> list[dict]:
        """Retrieve dead-lettered events for review."""
        conn = _connect(self._db_path)
        rows = conn.execute(
            "SELECT * FROM omega_event_store WHERE status = 'dead_letter' "
            "ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def retry_event(self, event_id: str) -> bool:
        """Re-queue a dead-lettered event for processing."""
        conn = _connect(self._db_path)
        cursor = conn.execute(
            "UPDATE omega_event_store SET status = 'pending', error_msg = NULL, "
            "retry_count = 0, processed_at = NULL WHERE event_id = ? AND status = 'dead_letter'",
            (event_id,)
        )
        conn.commit()
        changed = cursor.rowcount > 0
        conn.close()
        if changed:
            logger.info("DeadLetterQueue: event %s re-queued for retry", event_id)
        return changed

    def purge(self, older_than_hours: int = 168) -> int:
        """Purge dead letters older than N hours (default 7 days)."""
        conn = _connect(self._db_path)
        cursor = conn.execute(
            "DELETE FROM omega_event_store WHERE status = 'dead_letter' "
            "AND created_at < datetime('now', ?)",
            (f"-{older_than_hours} hours",)
        )
        conn.commit()
        count = cursor.rowcount
        conn.close()
        if count > 0:
            logger.info("DeadLetterQueue: purged %d dead letters older than %dh", count, older_than_hours)
        return count

    def count(self) -> int:
        """Count dead-lettered events."""
        conn = _connect(self._db_path)
        row = conn.execute(
            "SELECT COUNT(*) FROM omega_event_store WHERE status = 'dead_letter'"
        ).fetchone()
        conn.close()
        return row[0] if row else 0


# ═══════════════════════════════════════════════════════════════════════════════
# Class 3: BackpressureManager
# ═══════════════════════════════════════════════════════════════════════════════

class BackpressureManager:
    """Controls event flow when the system is overloaded.

    Strategy:
      - Under threshold (default 1000): all events processed normally
      - Over threshold: defer events with priority < defer_below (default 5)
      - Over critical threshold (default 5000): defer everything except CRITICAL (9)
    """

    def __init__(self, db_path: str = None,
                 threshold: int = 1000,
                 critical_threshold: int = 5000,
                 defer_below_priority: int = 5):
        self._db_path = db_path
        self.threshold = threshold
        self.critical_threshold = critical_threshold
        self.defer_below_priority = defer_below_priority

    def check_pressure(self) -> dict:
        """Check current backpressure status."""
        conn = _connect(self._db_path)
        row = conn.execute(
            "SELECT COUNT(*) FROM omega_event_store WHERE status = 'pending'"
        ).fetchone()
        pending = row[0] if row else 0
        conn.close()

        if pending >= self.critical_threshold:
            level = "critical"
        elif pending >= self.threshold:
            level = "elevated"
        else:
            level = "normal"

        return {
            "pending_count": pending,
            "level": level,
            "threshold": self.threshold,
            "critical_threshold": self.critical_threshold,
        }

    def should_defer(self, priority: int) -> bool:
        """Check if an event with given priority should be deferred."""
        pressure = self.check_pressure()
        if pressure["level"] == "critical":
            return priority < 9  # Only CRITICAL (9) gets through
        elif pressure["level"] == "elevated":
            return priority < self.defer_below_priority
        return False

    def defer_event(self, event_id: str):
        """Mark an event as deferred due to backpressure."""
        conn = _connect(self._db_path)
        conn.execute(
            "UPDATE omega_event_store SET status = 'deferred' WHERE event_id = ?",
            (event_id,)
        )
        conn.commit()
        conn.close()

    def resume_deferred(self, batch_size: int = 100) -> int:
        """Re-queue deferred events (highest priority first)."""
        conn = _connect(self._db_path)
        cursor = conn.execute(
            "UPDATE omega_event_store SET status = 'pending' "
            "WHERE event_id IN ("
            "  SELECT event_id FROM omega_event_store "
            "  WHERE status = 'deferred' "
            "  ORDER BY priority ASC, created_at ASC "
            "  LIMIT ?"
            ")",
            (batch_size,)
        )
        conn.commit()
        count = cursor.rowcount
        conn.close()
        if count > 0:
            logger.info("BackpressureManager: resumed %d deferred events", count)
        return count


# ═══════════════════════════════════════════════════════════════════════════════
# Class 4: EventBus — The Central Nervous System
# ═══════════════════════════════════════════════════════════════════════════════

class EventBus:
    """The Omega Event Bus — central nervous system of LitigationOS.

    Responsibilities:
      1. Publish events (append to immutable event store)
      2. Subscribe handlers to event patterns (glob matching)
      3. Dispatch pending events to matching subscribers
      4. Circuit breaker protection per subscriber
      5. Dead letter queue for exhausted retries
      6. Backpressure management under load
      7. Saga orchestration for multi-step workflows

    Usage:
        bus = EventBus()

        # Register a subscriber
        bus.subscribe("filing_engine", "evidence.*", handle_evidence)

        # Publish an event
        bus.publish("evidence.quote_added", source="intake", payload={...})

        # Dispatch pending (called from daemon main loop)
        bus.dispatch(max_events=10)
    """

    def __init__(self, db_path: str = None):
        self._db_path = db_path
        self._subscribers: dict[str, list[dict]] = defaultdict(list)  # pattern -> handlers
        self._circuit_breakers: dict[str, CircuitBreaker] = {}
        # Ensure all omega_ tables exist BEFORE any component queries them
        self._ensure_tables()
        self._dead_letter = DeadLetterQueue(db_path)
        self._backpressure = BackpressureManager(db_path)
        self._event_count = 0
        self._dispatch_count = 0
        # Load persisted subscriptions
        self._load_subscriptions()

    def _ensure_tables(self):
        """Create all omega_ tables if they don't exist.

        Called at the very start of __init__ so that DeadLetterQueue,
        BackpressureManager, CircuitBreaker, and _load_subscriptions all
        find their tables ready.  Idempotent — safe to call repeatedly.
        """
        conn = _connect(self._db_path)
        conn.executescript("""
            -- 1. Core event store (CQRS append-only log)
            CREATE TABLE IF NOT EXISTS omega_event_store (
                event_id       TEXT    PRIMARY KEY,
                event_type     TEXT    NOT NULL,
                source         TEXT,
                payload        TEXT,
                priority       INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 9),
                status         TEXT    DEFAULT 'pending',
                retry_count    INTEGER DEFAULT 0,
                max_retries    INTEGER DEFAULT 3,
                processor      TEXT,
                error_msg      TEXT,
                parent_event_id TEXT,
                correlation_id  TEXT,
                created_at     TEXT    DEFAULT (datetime('now')),
                processed_at   TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_omega_event_store_status_priority
                ON omega_event_store (status, priority);
            CREATE INDEX IF NOT EXISTS idx_omega_event_store_type
                ON omega_event_store (event_type);

            -- 2. Pub/sub subscriptions
            CREATE TABLE IF NOT EXISTS omega_event_subscriptions (
                subscriber_name TEXT NOT NULL,
                event_pattern   TEXT NOT NULL,
                handler_ref     TEXT,
                priority        INTEGER DEFAULT 5,
                enabled         INTEGER DEFAULT 1,
                created_at      TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (subscriber_name, event_pattern)
            );

            -- 3. Materialized projections (read-side of CQRS)
            CREATE TABLE IF NOT EXISTS omega_event_projections (
                projection_name TEXT PRIMARY KEY,
                last_event_id   TEXT    DEFAULT '',
                projection_state TEXT DEFAULT '{}',
                updated_at      TEXT DEFAULT (datetime('now'))
            );

            -- 4. Aggregate snapshots (optimise replays)
            CREATE TABLE IF NOT EXISTS omega_event_snapshots (
                snapshot_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                aggregate_type   TEXT NOT NULL,
                aggregate_id     TEXT NOT NULL,
                snapshot_data    TEXT NOT NULL,
                snapshot_version INTEGER DEFAULT 1,
                created_at       TEXT DEFAULT (datetime('now'))
            );

            -- 5. Saga / process-manager instances
            CREATE TABLE IF NOT EXISTS omega_saga_instances (
                saga_id       TEXT PRIMARY KEY,
                saga_type     TEXT NOT NULL,
                status        TEXT DEFAULT 'running',
                current_step  INTEGER DEFAULT 0,
                total_steps   INTEGER DEFAULT 1,
                context_data  TEXT DEFAULT '{}',
                event_ids     TEXT DEFAULT '[]',
                error         TEXT,
                created_at    TEXT DEFAULT (datetime('now')),
                updated_at    TEXT DEFAULT (datetime('now')),
                completed_at  TEXT
            );

            -- 6. Engine health telemetry
            CREATE TABLE IF NOT EXISTS omega_engine_health (
                engine_name         TEXT PRIMARY KEY,
                status              TEXT    DEFAULT 'unknown',
                last_heartbeat      TEXT    DEFAULT (datetime('now')),
                error_count_1h      INTEGER DEFAULT 0,
                avg_latency_ms      REAL    DEFAULT 0.0,
                events_processed_1h INTEGER DEFAULT 0,
                circuit_state       TEXT    DEFAULT 'closed',
                metadata            TEXT    DEFAULT '{}',
                updated_at          TEXT    DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_omega_engine_health_status
                ON omega_engine_health (status, updated_at);

            -- 7. Circuit-breaker persistent state (all columns used by
            --    CircuitBreaker._persist_state / _load_state)
            CREATE TABLE IF NOT EXISTS omega_circuit_breaker_state (
                engine_name         TEXT PRIMARY KEY,
                state               TEXT    DEFAULT 'closed',
                failure_count       INTEGER DEFAULT 0,
                success_count       INTEGER DEFAULT 0,
                last_failure_at     TEXT,
                last_success_at     TEXT,
                cooldown_until      TEXT,
                failure_threshold   INTEGER DEFAULT 3,
                failure_window_sec  INTEGER DEFAULT 60,
                cooldown_sec        INTEGER DEFAULT 300,
                half_open_max_calls INTEGER DEFAULT 1,
                updated_at          TEXT    DEFAULT (datetime('now'))
            );
        """)
        conn.close()
        logger.debug("EventBus._ensure_tables: all 7 omega_ tables verified")

    def _load_subscriptions(self):
        """Load subscriptions from DB."""
        try:
            conn = _connect(self._db_path)
            rows = conn.execute(
                "SELECT subscriber_name, event_pattern, handler_ref, priority "
                "FROM omega_event_subscriptions WHERE enabled = 1 "
                "ORDER BY priority ASC"
            ).fetchall()
            for row in rows:
                self._subscribers[row["event_pattern"]].append({
                    "subscriber": row["subscriber_name"],
                    "handler_ref": row["handler_ref"],
                    "priority": row["priority"],
                })
            conn.close()
            if rows:
                logger.info("EventBus: loaded %d subscriptions", len(rows))
        except Exception as e:
            logger.warning("EventBus._load_subscriptions: %s", e)

    def _get_circuit_breaker(self, engine_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for an engine."""
        if engine_name not in self._circuit_breakers:
            self._circuit_breakers[engine_name] = CircuitBreaker(
                engine_name, db_path=self._db_path
            )
        return self._circuit_breakers[engine_name]

    def subscribe(self, subscriber_name: str, event_pattern: str,
                  handler: Callable = None, handler_ref: str = None,
                  priority: int = 5) -> bool:
        """Register a subscriber for events matching a pattern.

        Args:
            subscriber_name: Unique name (e.g. "filing_engine")
            event_pattern: Glob pattern (e.g. "file.*", "evidence.quote_added", "*")
            handler: Callable to invoke (in-process only)
            handler_ref: Dotted path for lazy import (e.g. "engines.filing.on_event")
            priority: Higher executes first (1-9)

        Returns:
            True if subscription registered successfully.
        """
        ref = handler_ref or (f"{handler.__module__}.{handler.__qualname__}" if handler else "")

        # Register in memory
        sub_entry = {
            "subscriber": subscriber_name,
            "handler_ref": ref,
            "handler": handler,  # Keep callable reference for in-process dispatch
            "priority": priority,
        }

        # Avoid duplicate subscriptions
        existing = [s for s in self._subscribers[event_pattern]
                    if s["subscriber"] == subscriber_name]
        if not existing:
            self._subscribers[event_pattern].append(sub_entry)
            # Sort by priority (highest first)
            self._subscribers[event_pattern].sort(
                key=lambda s: s["priority"], reverse=True
            )

        # Persist to DB
        try:
            conn = _connect(self._db_path)
            conn.execute("""
                INSERT INTO omega_event_subscriptions
                    (subscriber_name, event_pattern, handler_ref, priority)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(subscriber_name, event_pattern) DO UPDATE SET
                    handler_ref=excluded.handler_ref, priority=excluded.priority
            """, (subscriber_name, event_pattern, ref, priority))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning("EventBus.subscribe persist failed: %s", e)

        logger.info("EventBus: %s subscribed to '%s' (priority=%d)",
                     subscriber_name, event_pattern, priority)
        return True

    def unsubscribe(self, subscriber_name: str, event_pattern: str = None):
        """Remove a subscriber from one or all patterns."""
        if event_pattern:
            self._subscribers[event_pattern] = [
                s for s in self._subscribers[event_pattern]
                if s["subscriber"] != subscriber_name
            ]
        else:
            for pattern in list(self._subscribers.keys()):
                self._subscribers[pattern] = [
                    s for s in self._subscribers[pattern]
                    if s["subscriber"] != subscriber_name
                ]

        try:
            conn = _connect(self._db_path)
            if event_pattern:
                conn.execute(
                    "DELETE FROM omega_event_subscriptions "
                    "WHERE subscriber_name = ? AND event_pattern = ?",
                    (subscriber_name, event_pattern)
                )
            else:
                conn.execute(
                    "DELETE FROM omega_event_subscriptions WHERE subscriber_name = ?",
                    (subscriber_name,)
                )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning("EventBus.unsubscribe persist failed: %s", e)

    def publish(self, event_type: str, source: str, payload: dict = None,
                priority: int = 5, parent_event_id: str = None,
                correlation_id: str = None) -> str:
        """Publish an event to the bus (append to event store).

        Args:
            event_type: Event type string (e.g. "file.discovered")
            source: Emitting engine/module name
            payload: Event data dict
            priority: 1 (background) to 9 (critical)
            parent_event_id: For event chaining
            correlation_id: For grouping related events

        Returns:
            event_id of the published event.
        """
        event_id = f"evt-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}-{os.urandom(3).hex()}"
        payload_json = json.dumps(payload or {}, default=str)

        # Check backpressure
        if self._backpressure.should_defer(priority):
            status = "deferred"
            logger.debug("EventBus: deferring low-priority event %s (backpressure)", event_type)
        else:
            status = "pending"

        conn = _connect(self._db_path)
        conn.execute("""
            INSERT INTO omega_event_store
                (event_id, event_type, source, payload, priority, status,
                 parent_event_id, correlation_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (event_id, event_type, source, payload_json, priority, status,
              parent_event_id, correlation_id))
        conn.commit()
        conn.close()

        self._event_count += 1
        logger.debug("EventBus: published %s from %s (id=%s, pri=%d)",
                      event_type, source, event_id, priority)
        return event_id

    def dispatch(self, max_events: int = 10) -> int:
        """Dispatch pending events to matching subscribers.

        Called from the daemon main loop each tick.
        Returns number of events processed.
        """
        conn = _connect(self._db_path)

        # Fetch highest-priority pending events (priority 1 = critical, dispatches first)
        events = conn.execute(
            "SELECT * FROM omega_event_store WHERE status = 'pending' "
            "ORDER BY priority ASC, created_at ASC LIMIT ?",
            (max_events,)
        ).fetchall()

        processed = 0
        for event_row in events:
            event = dict(event_row)
            event_id = event["event_id"]
            event_type = event["event_type"]

            # Mark as processing
            conn.execute(
                "UPDATE omega_event_store SET status = 'processing' WHERE event_id = ?",
                (event_id,)
            )
            conn.commit()

            # Find matching subscribers
            matched_handlers = self._match_subscribers(event_type)

            if not matched_handlers:
                # No subscribers — mark completed (event is logged but unhandled)
                conn.execute(
                    "UPDATE omega_event_store SET status = 'completed', "
                    "processed_at = datetime('now') WHERE event_id = ?",
                    (event_id,)
                )
                conn.commit()
                processed += 1
                continue

            # Dispatch to each matching subscriber
            all_succeeded = True
            for handler_info in matched_handlers:
                subscriber = handler_info["subscriber"]
                cb = self._get_circuit_breaker(subscriber)

                if not cb.allow_request():
                    logger.warning(
                        "EventBus: circuit OPEN for %s, skipping event %s",
                        subscriber, event_id
                    )
                    continue

                try:
                    handler_fn = handler_info.get("handler")
                    if handler_fn and callable(handler_fn):
                        # Parse payload JSON
                        payload = json.loads(event["payload"]) if isinstance(event["payload"], str) else event["payload"]
                        handler_fn(event_type, payload, event)
                        cb.record_success()
                    else:
                        # Lazy import handler via handler_ref
                        ref = handler_info.get("handler_ref", "")
                        if ref:
                            fn = self._resolve_handler(ref)
                            if fn:
                                payload = json.loads(event["payload"]) if isinstance(event["payload"], str) else event["payload"]
                                fn(event_type, payload, event)
                                cb.record_success()
                            else:
                                logger.warning("EventBus: could not resolve handler %s", ref)
                except Exception as e:
                    cb.record_failure()
                    all_succeeded = False
                    logger.error(
                        "EventBus: handler %s failed for event %s: %s",
                        subscriber, event_id, e
                    )

            if all_succeeded:
                conn.execute(
                    "UPDATE omega_event_store SET status = 'completed', "
                    "processed_at = datetime('now') WHERE event_id = ?",
                    (event_id,)
                )
            else:
                # Increment retry count
                retry = (event.get("retry_count") or 0) + 1
                max_retries = event.get("max_retries") or 3
                if retry >= max_retries:
                    self._dead_letter.send_to_dead_letter(
                        event_id, f"Exhausted {max_retries} retries"
                    )
                else:
                    conn.execute(
                        "UPDATE omega_event_store SET status = 'pending', "
                        "retry_count = ? WHERE event_id = ?",
                        (retry, event_id)
                    )
            conn.commit()
            processed += 1

        conn.close()
        self._dispatch_count += processed

        # Periodically resume deferred events if pressure has eased
        if self._dispatch_count % 50 == 0 and self._dispatch_count > 0:
            pressure = self._backpressure.check_pressure()
            if pressure["level"] == "normal":
                self._backpressure.resume_deferred(batch_size=20)

        return processed

    def _match_subscribers(self, event_type: str) -> list[dict]:
        """Find all subscribers matching an event type using glob patterns."""
        matched = []
        for pattern, handlers in self._subscribers.items():
            if fnmatch.fnmatch(event_type, pattern):
                matched.extend(handlers)
        # Sort by priority (highest first), deduplicate by subscriber name
        seen: set[str] = set()
        result = []
        for h in sorted(matched, key=lambda x: x["priority"], reverse=True):
            if h["subscriber"] not in seen:
                seen.add(h["subscriber"])
                result.append(h)
        return result

    def _resolve_handler(self, handler_ref: str) -> Optional[Callable]:
        """Lazy-import a handler from a dotted reference path."""
        try:
            parts = handler_ref.rsplit(".", 1)
            if len(parts) != 2:
                return None
            module_path, func_name = parts
            module = importlib.import_module(module_path)
            return getattr(module, func_name, None)
        except (ImportError, AttributeError) as e:
            logger.debug("EventBus: cannot resolve %s: %s", handler_ref, e)
            return None

    def emit_heartbeat(self, source: str = "daemon", metadata: dict = None) -> str:
        """Emit a system heartbeat event with health metadata."""
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_count": self._event_count,
            "dispatch_count": self._dispatch_count,
            "dead_letters": self._dead_letter.count(),
            "backpressure": self._backpressure.check_pressure(),
            "circuit_breakers": {
                name: cb.to_dict() for name, cb in self._circuit_breakers.items()
            },
        }
        if metadata:
            payload.update(metadata)
        return self.publish("system.heartbeat", source=source, payload=payload, priority=1)

    def update_engine_health(self, engine_name: str, status: str = "healthy",
                             latency_ms: float = 0.0, error_count: int = 0,
                             events_processed: int = 0, metadata: dict = None):
        """Update engine health record in omega_engine_health."""
        cb = self._get_circuit_breaker(engine_name)
        conn = _connect(self._db_path)
        conn.execute("""
            INSERT INTO omega_engine_health
                (engine_name, status, last_heartbeat, error_count_1h,
                 avg_latency_ms, events_processed_1h, circuit_state, metadata, updated_at)
            VALUES (?, ?, datetime('now'), ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(engine_name) DO UPDATE SET
                status=excluded.status, last_heartbeat=excluded.last_heartbeat,
                error_count_1h=excluded.error_count_1h, avg_latency_ms=excluded.avg_latency_ms,
                events_processed_1h=excluded.events_processed_1h,
                circuit_state=excluded.circuit_state, metadata=excluded.metadata,
                updated_at=excluded.updated_at
        """, (engine_name, status, error_count, latency_ms, events_processed,
              cb.state, json.dumps(metadata or {}, default=str)))
        conn.commit()
        conn.close()

    # ── Saga Methods ──────────────────────────────────────────────────────────

    def start_saga(self, saga_type: str, total_steps: int,
                   context: dict = None) -> str:
        """Start a new saga (multi-step distributed transaction)."""
        saga_id = f"saga-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}-{os.urandom(3).hex()}"
        conn = _connect(self._db_path)
        conn.execute("""
            INSERT INTO omega_saga_instances
                (saga_id, saga_type, status, current_step, total_steps,
                 context_data, event_ids, created_at, updated_at)
            VALUES (?, ?, 'running', 0, ?, ?, '[]', datetime('now'), datetime('now'))
        """, (saga_id, saga_type, total_steps, json.dumps(context or {}, default=str)))
        conn.commit()
        conn.close()
        logger.info("Saga started: %s (%s, %d steps)", saga_id, saga_type, total_steps)
        return saga_id

    def advance_saga(self, saga_id: str, event_id: str = None) -> dict:
        """Advance a saga to the next step."""
        conn = _connect(self._db_path)
        row = conn.execute(
            "SELECT * FROM omega_saga_instances WHERE saga_id = ?", (saga_id,)
        ).fetchone()
        if not row:
            conn.close()
            return {"error": f"Saga not found: {saga_id}"}

        saga = dict(row)
        current = saga["current_step"] + 1
        event_ids = json.loads(saga["event_ids"] or "[]")
        if event_id:
            event_ids.append(event_id)

        if current >= saga["total_steps"]:
            status = "completed"
            conn.execute("""
                UPDATE omega_saga_instances SET
                    current_step = ?, status = ?, event_ids = ?,
                    updated_at = datetime('now'), completed_at = datetime('now')
                WHERE saga_id = ?
            """, (current, status, json.dumps(event_ids), saga_id))
        else:
            status = "running"
            conn.execute("""
                UPDATE omega_saga_instances SET
                    current_step = ?, status = ?, event_ids = ?,
                    updated_at = datetime('now')
                WHERE saga_id = ?
            """, (current, status, json.dumps(event_ids), saga_id))
        conn.commit()
        conn.close()

        return {"saga_id": saga_id, "step": current, "status": status}

    def fail_saga(self, saga_id: str, error: str):
        """Mark a saga as failed."""
        conn = _connect(self._db_path)
        conn.execute(
            "UPDATE omega_saga_instances SET status = 'failed', error = ?, "
            "updated_at = datetime('now') WHERE saga_id = ?",
            (error, saga_id)
        )
        conn.commit()
        conn.close()
        logger.error("Saga failed: %s — %s", saga_id, error)

    # ── Stats & Diagnostics ──────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Get event bus statistics."""
        conn = _connect(self._db_path)
        row = conn.execute("""
            SELECT
                (SELECT COUNT(*) FROM omega_event_store) AS total_events,
                (SELECT COUNT(*) FROM omega_event_store WHERE status='pending') AS pending,
                (SELECT COUNT(*) FROM omega_event_store WHERE status='completed') AS completed,
                (SELECT COUNT(*) FROM omega_event_store WHERE status='failed') AS failed,
                (SELECT COUNT(*) FROM omega_event_store WHERE status='dead_letter') AS dead_letters,
                (SELECT COUNT(*) FROM omega_event_store WHERE status='deferred') AS deferred,
                (SELECT COUNT(*) FROM omega_event_subscriptions WHERE enabled=1) AS subscriptions,
                (SELECT COUNT(*) FROM omega_saga_instances WHERE status='running') AS active_sagas,
                (SELECT COUNT(*) FROM omega_engine_health) AS engines_tracked
        """).fetchone()
        conn.close()

        return {
            "total_events": row[0],
            "pending": row[1],
            "completed": row[2],
            "failed": row[3],
            "dead_letters": row[4],
            "deferred": row[5],
            "subscriptions": row[6],
            "active_sagas": row[7],
            "engines_tracked": row[8],
            "in_memory_event_count": self._event_count,
            "in_memory_dispatch_count": self._dispatch_count,
            "circuit_breakers": {
                name: cb.to_dict() for name, cb in self._circuit_breakers.items()
            },
        }
