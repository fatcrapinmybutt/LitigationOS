"""EventBus — Thread-safe pub/sub with self-healing retry.

Architecture:
    - Topic-based routing: handlers subscribe to dot-separated topics
    - Wildcard support: "evidence.*" matches "evidence.new", "evidence.updated"
    - Thread-safe: threading.Lock guards all mutable state
    - Self-healing: failed handlers retried with exponential backoff
    - Event history: collections.deque(maxlen=1000) for audit trail
    - Stats tracking: per-topic publish/handler counts and error counts
"""

import sys
import os
import re
import time
import uuid
import logging
import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

sys.path.insert(0, r"C:\Users\andre\LitigationOS")

logger = logging.getLogger(__name__)

# ── Data Types ────────────────────────────────────────────────────────────

@dataclass
class Event:
    """Immutable event record."""
    event_id: str
    topic: str
    payload: Dict[str, Any]
    timestamp: str
    source: str = "unknown"


@dataclass
class Subscription:
    """Handler subscription record."""
    sub_id: str
    topic_pattern: str
    handler: Callable
    handler_name: str
    priority: int = 0  # lower = higher priority


@dataclass
class BusStats:
    """Runtime statistics."""
    total_published: int = 0
    total_handled: int = 0
    total_errors: int = 0
    topic_counts: Dict[str, int] = field(default_factory=dict)
    error_counts: Dict[str, int] = field(default_factory=dict)
    last_event_time: Optional[str] = None


# ── Core EventBus ─────────────────────────────────────────────────────────

class EventBus:
    """Thread-safe event bus with topic routing and self-healing retry.

    Supports synchronous publishing. Handlers are called in priority
    order (lowest number first). Failed handlers are retried up to
    max_retries times with exponential backoff.

    Topics use dot notation: "evidence.new", "contradiction.found".
    Wildcard patterns: "evidence.*" matches any topic starting with "evidence.".
    """

    MAX_HISTORY = 1000
    DEFAULT_MAX_RETRIES = 3
    BASE_BACKOFF = 0.1  # seconds

    def __init__(self, max_retries: int = DEFAULT_MAX_RETRIES):
        self._subscriptions: List[Subscription] = []
        self._history: deque = deque(maxlen=self.MAX_HISTORY)
        self._stats = BusStats()
        self._lock = threading.Lock()
        self._max_retries = max_retries
        self._paused_topics: Set[str] = set()

    # ── Subscription Management ───────────────────────────────────────

    def subscribe(
        self,
        topic_pattern: str,
        handler: Callable,
        priority: int = 0,
        name: Optional[str] = None,
    ) -> str:
        """Subscribe a handler to a topic pattern. Returns subscription ID."""
        sub_id = str(uuid.uuid4())[:8]
        handler_name = name or getattr(handler, "__name__", str(handler))
        sub = Subscription(
            sub_id=sub_id,
            topic_pattern=topic_pattern,
            handler=handler,
            handler_name=handler_name,
            priority=priority,
        )
        with self._lock:
            self._subscriptions.append(sub)
            self._subscriptions.sort(key=lambda s: s.priority)
        logger.debug("Subscribed %s to '%s' (id=%s, pri=%d)",
                      handler_name, topic_pattern, sub_id, priority)
        return sub_id

    def unsubscribe(self, sub_id: str) -> bool:
        """Remove a subscription by ID. Returns True if found."""
        with self._lock:
            before = len(self._subscriptions)
            self._subscriptions = [
                s for s in self._subscriptions if s.sub_id != sub_id
            ]
            removed = len(self._subscriptions) < before
        if removed:
            logger.debug("Unsubscribed id=%s", sub_id)
        return removed

    def unsubscribe_all(self) -> int:
        """Remove all subscriptions. Returns count removed."""
        with self._lock:
            count = len(self._subscriptions)
            self._subscriptions.clear()
        return count

    # ── Publishing ────────────────────────────────────────────────────

    def publish_sync(
        self,
        topic: str,
        payload: Optional[Dict[str, Any]] = None,
        source: str = "unknown",
    ) -> Event:
        """Publish an event synchronously. Handlers execute in-thread.

        Failed handlers are retried with exponential backoff.
        Returns the Event record.
        """
        event = Event(
            event_id=str(uuid.uuid4())[:12],
            topic=topic,
            payload=payload or {},
            timestamp=datetime.utcnow().isoformat(),
            source=source,
        )

        # Record to history
        with self._lock:
            self._history.append(event)
            self._stats.total_published += 1
            self._stats.topic_counts[topic] = (
                self._stats.topic_counts.get(topic, 0) + 1
            )
            self._stats.last_event_time = event.timestamp

            if topic in self._paused_topics:
                logger.debug("Topic '%s' is paused — skipping handlers", topic)
                return event

            # Snapshot matching handlers under lock
            matching = [
                s for s in self._subscriptions
                if self._topic_matches(s.topic_pattern, topic)
            ]

        # Execute handlers outside lock to avoid deadlock
        for sub in matching:
            self._execute_with_retry(sub, event)

        return event

    # Alias for convenience
    publish = publish_sync

    def _execute_with_retry(self, sub: Subscription, event: Event) -> None:
        """Execute a handler with exponential backoff retry."""
        last_error = None
        for attempt in range(self._max_retries):
            try:
                sub.handler(event)
                with self._lock:
                    self._stats.total_handled += 1
                return
            except Exception as exc:
                last_error = exc
                backoff = self.BASE_BACKOFF * (2 ** attempt)
                logger.warning(
                    "Handler '%s' failed on '%s' (attempt %d/%d): %s — retrying in %.2fs",
                    sub.handler_name, event.topic,
                    attempt + 1, self._max_retries,
                    exc, backoff,
                )
                if attempt < self._max_retries - 1:
                    time.sleep(backoff)

        # All retries exhausted
        with self._lock:
            self._stats.total_errors += 1
            key = f"{sub.handler_name}:{event.topic}"
            self._stats.error_counts[key] = (
                self._stats.error_counts.get(key, 0) + 1
            )
        logger.error(
            "Handler '%s' permanently failed on '%s' after %d retries: %s",
            sub.handler_name, event.topic, self._max_retries, last_error,
        )

    # ── Topic Matching ────────────────────────────────────────────────

    @staticmethod
    def _topic_matches(pattern: str, topic: str) -> bool:
        """Match a topic against a subscription pattern.

        Supports:
            - Exact match: "evidence.new" matches "evidence.new"
            - Wildcard suffix: "evidence.*" matches "evidence.new", "evidence.updated"
            - Global wildcard: "*" matches everything
        """
        if pattern == "*":
            return True
        if pattern == topic:
            return True
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            return topic.startswith(prefix + ".")
        return False

    # ── Topic Control ─────────────────────────────────────────────────

    def pause_topic(self, topic: str) -> None:
        """Pause delivery for a topic. Events are still recorded in history."""
        with self._lock:
            self._paused_topics.add(topic)
        logger.info("Paused topic: %s", topic)

    def resume_topic(self, topic: str) -> None:
        """Resume delivery for a paused topic."""
        with self._lock:
            self._paused_topics.discard(topic)
        logger.info("Resumed topic: %s", topic)

    # ── Query ─────────────────────────────────────────────────────────

    def get_history(
        self,
        topic_filter: Optional[str] = None,
        limit: int = 50,
    ) -> List[Event]:
        """Retrieve recent events, optionally filtered by topic prefix."""
        with self._lock:
            events = list(self._history)
        if topic_filter:
            events = [
                e for e in events
                if e.topic.startswith(topic_filter)
            ]
        return events[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """Return a snapshot of bus statistics."""
        with self._lock:
            return {
                "total_published": self._stats.total_published,
                "total_handled": self._stats.total_handled,
                "total_errors": self._stats.total_errors,
                "topic_counts": dict(self._stats.topic_counts),
                "error_counts": dict(self._stats.error_counts),
                "last_event_time": self._stats.last_event_time,
                "subscriptions": len(self._subscriptions),
                "history_size": len(self._history),
                "paused_topics": list(self._paused_topics),
            }

    def list_subscriptions(self) -> List[Dict[str, Any]]:
        """Return metadata about all active subscriptions."""
        with self._lock:
            return [
                {
                    "sub_id": s.sub_id,
                    "topic_pattern": s.topic_pattern,
                    "handler_name": s.handler_name,
                    "priority": s.priority,
                }
                for s in self._subscriptions
            ]

    def clear_history(self) -> int:
        """Clear event history. Returns count cleared."""
        with self._lock:
            count = len(self._history)
            self._history.clear()
        return count

    def reset_stats(self) -> None:
        """Reset all statistics to zero."""
        with self._lock:
            self._stats = BusStats()


# ── Module-level singleton (lazy) ─────────────────────────────────────────

_default_bus: Optional[EventBus] = None
_bus_lock = threading.Lock()


def get_default_bus() -> EventBus:
    """Get or create the module-level default EventBus singleton."""
    global _default_bus
    with _bus_lock:
        if _default_bus is None:
            _default_bus = EventBus()
        return _default_bus
