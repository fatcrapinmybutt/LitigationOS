"""
LitigationOS Unified Context Manager — Δ99 Ω∞
===============================================
Central nervous system for context orchestration across the entire
LitigationOS stack. Integrates all four context engineering disciplines:

1. Context Manager — Dynamic assembly, agent handoff, lifecycle
2. Context Window Management — Serial position, trimming, summarization
3. Conversation Memory — Tiered memory (short/long/entity), persistence
4. Auto-Research — Local documentation and authority retrieval

Architecture:
    AgentContext ← serializable handoff payload between agents
    MemoryTier  ← short-term (session), long-term (persistent), entity
    FreshnessScorer ← staleness detection, recency weighting
    ContextWindow ← optimized window with serial position effect
    ContextManager ← central orchestrator managing all subsystems

Integration Points:
    - PersistentMemory (persistent_memory.py) — long-term store
    - SessionRecall (session_recall.py) — cross-session patterns
    - InferenceEngine (inference_engine.py) — hot cache, context window
    - Agent9999 (agent_base.py) — agent handoff protocol
    - QualityGate (quality_gate.py) — output validation

Zero network. Zero APIs. 100% local.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
import threading
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# UTF-8 safety
if hasattr(sys.stdout, "fileno"):
    try:
        sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")
    except Exception:
        pass

# ─────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────

_DB_PATH = Path(os.environ.get(
    "LITIGOS_DB",
    Path(__file__).resolve().parent.parent.parent / "litigation_context.db"
))

# Memory lifecycle
SHORT_TERM_TTL_S = 600          # 10 minutes
LONG_TERM_TTL_S = 86400 * 30   # 30 days
ENTITY_TTL_S = 86400 * 365     # 1 year (party data rarely changes)
MAX_SHORT_TERM_ITEMS = 50
MAX_LONG_TERM_ITEMS = 10000
MAX_ENTITY_ITEMS = 500

# Context window optimization
CONTEXT_WINDOW_MAX = 20         # max items in sliding window
SERIAL_POSITION_HEAD = 3        # items at start (primacy effect)
SERIAL_POSITION_TAIL = 5        # items at end (recency effect)

# Freshness scoring
FRESHNESS_DECAY_HALF_LIFE_S = 86400 * 7  # 7-day half-life
STALE_THRESHOLD = 0.3           # below this = stale warning
EXPIRED_THRESHOLD = 0.1         # below this = expired

# Auto-cleanup
CLEANUP_INTERVAL_S = 300        # 5 minutes
CLEANUP_BATCH_SIZE = 100        # max items per cleanup cycle

# Lane boundaries (IRON LAW — never cross)
VALID_LANES = {"A", "B", "C", "D", "E", "F"}


# ─────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────

class MemoryTier(str, Enum):
    """Three-tier memory system per conversation-memory skill."""
    SHORT_TERM = "short_term"   # Current session, fast, volatile
    LONG_TERM = "long_term"     # Persistent across sessions, searchable
    ENTITY = "entity"           # Party/judge/case facts, rarely change


class ContextPriority(str, Enum):
    """Priority levels for context items."""
    CRITICAL = "critical"       # Always in window (party names, case numbers)
    HIGH = "high"               # Important (current filing, active lane)
    MEDIUM = "medium"           # Relevant (related authorities, evidence)
    LOW = "low"                 # Background (historical, pattern data)


class HandoffStatus(str, Enum):
    """Agent handoff status tracking."""
    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    COMPLETED = "completed"
    FAILED = "failed"


# ─────────────────────────────────────────────────────────────
# Dataclasses
# ─────────────────────────────────────────────────────────────

@dataclass
class ContextItem:
    """Single item in the context window."""
    key: str
    value: Any
    priority: ContextPriority = ContextPriority.MEDIUM
    lane: Optional[str] = None
    source: str = "unknown"
    created_at: float = field(default_factory=time.time)
    accessed_at: float = field(default_factory=time.time)
    access_count: int = 0
    ttl_seconds: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def age_seconds(self) -> float:
        return time.time() - self.created_at

    @property
    def freshness_score(self) -> float:
        """Exponential decay freshness: 1.0 (fresh) → 0.0 (stale)."""
        import math
        age = self.age_seconds
        return math.exp(-0.693 * age / FRESHNESS_DECAY_HALF_LIFE_S)

    @property
    def is_expired(self) -> bool:
        if self.ttl_seconds is not None:
            return self.age_seconds > self.ttl_seconds
        return self.freshness_score < EXPIRED_THRESHOLD

    @property
    def is_stale(self) -> bool:
        return self.freshness_score < STALE_THRESHOLD

    def touch(self) -> None:
        """Update access timestamp and count."""
        self.accessed_at = time.time()
        self.access_count += 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value if isinstance(self.value, (str, int, float, bool, type(None))) else str(self.value),
            "priority": self.priority.value,
            "lane": self.lane,
            "source": self.source,
            "created_at": self.created_at,
            "accessed_at": self.accessed_at,
            "access_count": self.access_count,
            "freshness": round(self.freshness_score, 3),
            "is_stale": self.is_stale,
        }


@dataclass
class AgentContext:
    """
    Serializable context payload for agent-to-agent handoff.
    
    Per context-manager skill: explicit handoff protocol with
    verification and audit trail.
    """
    source_agent: str
    target_agent: str
    lane: str
    task_description: str
    items: List[ContextItem] = field(default_factory=list)
    handoff_id: str = ""
    status: HandoffStatus = HandoffStatus.PENDING
    created_at: float = field(default_factory=time.time)
    acknowledged_at: Optional[float] = None
    completed_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.handoff_id:
            payload = f"{self.source_agent}:{self.target_agent}:{time.time()}"
            self.handoff_id = hashlib.sha256(payload.encode()).hexdigest()[:16]
        if self.lane and self.lane not in VALID_LANES:
            raise ValueError(f"Invalid lane '{self.lane}'. Must be one of {VALID_LANES}")

    def acknowledge(self) -> None:
        self.status = HandoffStatus.ACKNOWLEDGED
        self.acknowledged_at = time.time()

    def complete(self) -> None:
        self.status = HandoffStatus.COMPLETED
        self.completed_at = time.time()

    def fail(self, reason: str = "") -> None:
        self.status = HandoffStatus.FAILED
        self.metadata["failure_reason"] = reason

    def serialize(self) -> str:
        """JSON-safe serialization for DB storage or IPC."""
        data = {
            "source_agent": self.source_agent,
            "target_agent": self.target_agent,
            "lane": self.lane,
            "task_description": self.task_description,
            "handoff_id": self.handoff_id,
            "status": self.status.value,
            "created_at": self.created_at,
            "acknowledged_at": self.acknowledged_at,
            "completed_at": self.completed_at,
            "metadata": self.metadata,
            "items": [item.to_dict() for item in self.items],
        }
        return json.dumps(data, default=str)

    @classmethod
    def deserialize(cls, json_str: str) -> "AgentContext":
        """Reconstruct from serialized JSON."""
        data = json.loads(json_str)
        items = []
        for item_data in data.get("items", []):
            items.append(ContextItem(
                key=item_data["key"],
                value=item_data["value"],
                priority=ContextPriority(item_data.get("priority", "medium")),
                lane=item_data.get("lane"),
                source=item_data.get("source", "deserialized"),
                created_at=item_data.get("created_at", time.time()),
                accessed_at=item_data.get("accessed_at", time.time()),
                access_count=item_data.get("access_count", 0),
            ))
        ctx = cls(
            source_agent=data["source_agent"],
            target_agent=data["target_agent"],
            lane=data["lane"],
            task_description=data["task_description"],
            items=items,
            handoff_id=data["handoff_id"],
            status=HandoffStatus(data["status"]),
            created_at=data["created_at"],
            acknowledged_at=data.get("acknowledged_at"),
            completed_at=data.get("completed_at"),
            metadata=data.get("metadata", {}),
        )
        return ctx


@dataclass
class FreshnessReport:
    """Report from a freshness audit."""
    total_items: int = 0
    fresh_items: int = 0
    stale_items: int = 0
    expired_items: int = 0
    avg_freshness: float = 0.0
    oldest_item_age_hours: float = 0.0
    warnings: List[str] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────
# Context Window (per context-window-management skill)
# ─────────────────────────────────────────────────────────────

class ContextWindow:
    """
    Optimized context window with serial position effect.
    
    Per context-window-management skill:
    - Items at START and END of window get more attention (primacy/recency)
    - Middle items are candidates for summarization/eviction
    - Critical items are pinned and never evicted
    - Token budget awareness (approximate)
    """

    def __init__(self, max_size: int = CONTEXT_WINDOW_MAX):
        self._items: List[ContextItem] = []
        self._pinned: List[ContextItem] = []  # CRITICAL items never evicted
        self._max_size = max_size
        self._lock = threading.Lock()

    @property
    def size(self) -> int:
        return len(self._pinned) + len(self._items)

    @property
    def items(self) -> List[ContextItem]:
        """Return items in serial-position-optimized order."""
        with self._lock:
            return list(self._pinned) + list(self._items)

    def add(self, item: ContextItem) -> Optional[ContextItem]:
        """
        Add item to window. Returns evicted item if window was full.
        Critical items are pinned. Others go into the sliding window.
        """
        with self._lock:
            if item.priority == ContextPriority.CRITICAL:
                # Deduplicate pinned items by key
                self._pinned = [p for p in self._pinned if p.key != item.key]
                self._pinned.append(item)
                return None

            # Deduplicate by key
            self._items = [i for i in self._items if i.key != item.key]
            self._items.append(item)

            evicted = None
            if len(self._items) > self._max_size - len(self._pinned):
                evicted = self._evict_one()
            return evicted

    def _evict_one(self) -> Optional[ContextItem]:
        """
        Evict the least valuable item from the middle of the window.
        Serial position: protect head (primacy) and tail (recency).
        """
        if len(self._items) <= SERIAL_POSITION_HEAD + SERIAL_POSITION_TAIL:
            # Too few items — evict lowest priority
            scored = sorted(self._items, key=lambda i: (
                i.priority.value, i.freshness_score
            ))
            if scored:
                victim = scored[0]
                self._items.remove(victim)
                return victim
            return None

        # Middle zone: candidates for eviction
        middle_start = SERIAL_POSITION_HEAD
        middle_end = len(self._items) - SERIAL_POSITION_TAIL
        middle = self._items[middle_start:middle_end]

        if not middle:
            return None

        # Score: lower = more evictable
        def eviction_score(item: ContextItem) -> float:
            priority_weight = {"critical": 4, "high": 3, "medium": 2, "low": 1}
            return (
                priority_weight.get(item.priority.value, 1) * 0.4
                + item.freshness_score * 0.3
                + min(item.access_count / 10, 1.0) * 0.3
            )

        victim = min(middle, key=eviction_score)
        self._items.remove(victim)
        return victim

    def get_optimized(self) -> List[ContextItem]:
        """
        Return items in optimal order for LLM consumption.
        Serial position effect: important items at start and end.
        """
        with self._lock:
            all_items = list(self._pinned) + list(self._items)
            if len(all_items) <= 6:
                return all_items

            # Sort by relevance for middle section
            head = all_items[:SERIAL_POSITION_HEAD]
            tail = all_items[-SERIAL_POSITION_TAIL:]
            middle = all_items[SERIAL_POSITION_HEAD:-SERIAL_POSITION_TAIL] if len(all_items) > SERIAL_POSITION_HEAD + SERIAL_POSITION_TAIL else []

            # Middle sorted by freshness (least fresh in the middle-of-middle)
            middle.sort(key=lambda i: i.freshness_score, reverse=True)

            return head + middle + tail

    def clear(self, keep_pinned: bool = True) -> int:
        """Clear window. Returns count of items removed."""
        with self._lock:
            count = len(self._items)
            self._items.clear()
            if not keep_pinned:
                count += len(self._pinned)
                self._pinned.clear()
            return count

    def find(self, key: str) -> Optional[ContextItem]:
        """Find item by key."""
        with self._lock:
            for item in self._pinned + self._items:
                if item.key == key:
                    item.touch()
                    return item
            return None

    def summary(self) -> Dict[str, Any]:
        """Window health summary."""
        with self._lock:
            all_items = self._pinned + self._items
            if not all_items:
                return {"size": 0, "pinned": 0, "avg_freshness": 0}
            scores = [i.freshness_score for i in all_items]
            return {
                "size": len(all_items),
                "pinned": len(self._pinned),
                "sliding": len(self._items),
                "max_size": self._max_size,
                "avg_freshness": round(sum(scores) / len(scores), 3),
                "stale_count": sum(1 for i in all_items if i.is_stale),
                "expired_count": sum(1 for i in all_items if i.is_expired),
                "priorities": {
                    p.value: sum(1 for i in all_items if i.priority == p)
                    for p in ContextPriority
                },
            }


# ─────────────────────────────────────────────────────────────
# Freshness Scorer
# ─────────────────────────────────────────────────────────────

class FreshnessScorer:
    """
    Staleness detection and recency weighting for all retrievals.
    
    Per context-manager skill: context quality assessment.
    """

    @staticmethod
    def score(item: ContextItem) -> float:
        """Composite freshness score: 0.0 (dead) to 1.0 (fresh)."""
        import math

        age_score = math.exp(-0.693 * item.age_seconds / FRESHNESS_DECAY_HALF_LIFE_S)
        access_score = min(item.access_count / 20, 1.0)  # diminishing returns
        priority_bonus = {"critical": 0.3, "high": 0.2, "medium": 0.1, "low": 0.0}

        base = age_score * 0.5 + access_score * 0.2
        bonus = priority_bonus.get(item.priority.value, 0.0)
        return min(base + bonus, 1.0)

    @staticmethod
    def audit(items: List[ContextItem]) -> FreshnessReport:
        """Audit a collection of context items for freshness."""
        report = FreshnessReport(total_items=len(items))
        if not items:
            return report

        scores = []
        max_age = 0.0

        for item in items:
            score = item.freshness_score
            scores.append(score)
            age_h = item.age_seconds / 3600

            if age_h > max_age:
                max_age = age_h

            if item.is_expired:
                report.expired_items += 1
                report.warnings.append(
                    f"EXPIRED: '{item.key}' (age={age_h:.1f}h, freshness={score:.3f})"
                )
            elif item.is_stale:
                report.stale_items += 1
                report.warnings.append(
                    f"STALE: '{item.key}' (age={age_h:.1f}h, freshness={score:.3f})"
                )
            else:
                report.fresh_items += 1

        report.avg_freshness = round(sum(scores) / len(scores), 3)
        report.oldest_item_age_hours = round(max_age, 1)
        return report

    @staticmethod
    def weight_results(results: List[Dict], age_key: str = "created_at") -> List[Dict]:
        """
        Apply recency weighting to search results.
        Results with 'created_at' timestamp get freshness-adjusted scores.
        """
        import math
        now = time.time()
        for r in results:
            ts = r.get(age_key, now)
            if isinstance(ts, str):
                try:
                    import datetime
                    dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    ts = dt.timestamp()
                except (ValueError, TypeError):
                    ts = now
            age = now - ts
            freshness = math.exp(-0.693 * age / FRESHNESS_DECAY_HALF_LIFE_S)
            original_score = r.get("score", 0.5)
            r["freshness"] = round(freshness, 3)
            r["weighted_score"] = round(original_score * 0.7 + freshness * 0.3, 3)
        results.sort(key=lambda r: r.get("weighted_score", 0), reverse=True)
        return results


# ─────────────────────────────────────────────────────────────
# Tiered Memory Store (per conversation-memory skill)
# ─────────────────────────────────────────────────────────────

class TieredMemory:
    """
    Three-tier memory system:
      SHORT_TERM — in-memory dict, fast, session-scoped, auto-evicts
      LONG_TERM  — SQLite-backed via PersistentMemory, searchable
      ENTITY     — Dedicated entity facts store (party names, case numbers)
    
    Per conversation-memory skill:
    - Different tiers for different purposes
    - Entity memory for facts about entities
    - Memory-aware prompting with relevant memories
    """

    def __init__(self, db_path: Optional[Path] = None):
        self._db_path = db_path or _DB_PATH
        self._short_term: Dict[str, ContextItem] = {}
        self._entity_cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._persistent = None  # Lazy-loaded PersistentMemory

        # Pre-load critical entity facts
        self._load_entity_cache()

    def _get_persistent(self):
        """Lazy-load PersistentMemory to avoid circular imports."""
        if self._persistent is None:
            try:
                from persistent_memory import PersistentMemory
                self._persistent = PersistentMemory(db_path=str(self._db_path))
            except ImportError:
                try:
                    parent = Path(__file__).resolve().parent
                    sys.path.insert(0, str(parent))
                    from persistent_memory import PersistentMemory
                    self._persistent = PersistentMemory(db_path=str(self._db_path))
                except Exception:
                    self._persistent = None
        return self._persistent

    def _load_entity_cache(self) -> None:
        """Pre-load known entities (party names, case numbers, judges)."""
        self._entity_cache = {
            "plaintiff": {
                "name": "Andrew James Pigors",
                "address": "1977 Whitehall Road, Lot 17, North Muskegon, MI 49445",
                "phone": "(231) 903-5690",
                "role": "Plaintiff / Petitioner (Pro Se)",
            },
            "defendant": {
                "name": "Emily A. Watson",
                "address": "2160 Garland Drive, Norton Shores, MI 49441",
                "role": "Defendant / Respondent",
                "attorney_status": "Unrepresented (Barnes withdrew)",
                "WRONG_NAMES": ["Emily Ann Watson", "Emily M. Watson", "Tiffany Watson"],
            },
            "child": {
                "name": "Lincoln David Watson",
                "initials": "L.D.W.",
                "rule": "MCR 8.119(H) — use initials only",
            },
            "judge": {
                "name": "Hon. Jenny L. McNeill",
                "court": "14th Circuit Court, Family Division",
                "WRONG_NAMES": ["Amy McNeill", "Jenny McNeill"],
            },
            "ron_berry": {
                "name": "Ronald Berry",
                "role": "Emily's boyfriend — NOT an attorney",
                "bar_number": None,
                "CRITICAL": "NO 'Esq.', NO bar number, NON-ATTORNEY",
            },
            "emily_attorney": {
                "name": "Jennifer Barnes (P55406)",
                "firm": "Barnes Law Firm PLLC",
                "status": "WITHDREW — Emily currently unrepresented",
                "WRONG_NAMES": ["Jane Berry", "Patricia Berry (P35878)"],
            },
            "foc": {
                "name": "Pamela Rusco",
                "address": "990 Terrace St, Muskegon MI 49442",
                "role": "FOC Referee",
            },
            "case_custody": {"number": "2024-001507-DC", "lane": "A"},
            "case_ppo": {"number": "2023-5907-PP", "lane": "D"},
            "case_housing": {"number": "2025-002760-CZ", "lane": "B"},
            "case_appellate": {"number": "COA 366810", "lane": "F"},
            "fabricated_PURGED": {
                "items": [
                    "Jane Berry",
                    "Patricia Berry (P35878)",
                    "9 CPS investigations",
                    "91% alienation score (use '305 documented interference incidents')",
                ],
                "rule": "NEVER reference these — they are fabrications",
            },
        }

    # ── Short-Term Memory ──

    def store_short(self, key: str, value: Any, priority: ContextPriority = ContextPriority.MEDIUM,
                    lane: Optional[str] = None, source: str = "session") -> None:
        """Store in short-term memory (in-memory, fast, session-scoped)."""
        with self._lock:
            item = ContextItem(
                key=key, value=value, priority=priority,
                lane=lane, source=source, ttl_seconds=SHORT_TERM_TTL_S,
            )
            self._short_term[key] = item

            # Evict oldest LOW items if over limit
            if len(self._short_term) > MAX_SHORT_TERM_ITEMS:
                candidates = [
                    (k, v) for k, v in self._short_term.items()
                    if v.priority == ContextPriority.LOW
                ]
                candidates.sort(key=lambda kv: kv[1].accessed_at)
                for k, _ in candidates[:10]:
                    del self._short_term[k]

    def recall_short(self, key: Optional[str] = None, lane: Optional[str] = None) -> List[ContextItem]:
        """Recall from short-term memory."""
        with self._lock:
            # Clean expired
            now = time.time()
            expired = [k for k, v in self._short_term.items() if v.is_expired]
            for k in expired:
                del self._short_term[k]

            if key:
                item = self._short_term.get(key)
                if item:
                    item.touch()
                    return [item]
                return []

            items = list(self._short_term.values())
            if lane:
                items = [i for i in items if i.lane == lane]
            for i in items:
                i.touch()
            return sorted(items, key=lambda i: i.freshness_score, reverse=True)

    # ── Long-Term Memory ──

    def store_long(self, key: str, value: str, memory_type: str = "insight",
                   confidence: float = 0.7, source: str = "session",
                   ttl_days: int = 30) -> Optional[int]:
        """Store in long-term persistent memory (SQLite-backed)."""
        pm = self._get_persistent()
        if pm is None:
            return None
        import datetime
        expires = (datetime.datetime.now() + datetime.timedelta(days=ttl_days)).isoformat()
        return pm.store(
            memory_type=memory_type,
            key=key,
            value=value,
            confidence=confidence,
            source=source,
            expires_at=expires,
        )

    def recall_long(self, memory_type: Optional[str] = None, key: Optional[str] = None,
                    min_confidence: float = 0.0, limit: int = 20) -> List[Dict]:
        """Recall from long-term persistent memory."""
        pm = self._get_persistent()
        if pm is None:
            return []
        results = pm.recall(
            memory_type=memory_type,
            key=key,
            min_confidence=min_confidence,
            limit=limit,
        )
        return FreshnessScorer.weight_results(results) if results else []

    # ── Entity Memory ──

    def get_entity(self, entity_key: str) -> Optional[Dict[str, Any]]:
        """Get entity facts (party names, case numbers, etc.)."""
        return self._entity_cache.get(entity_key)

    def set_entity(self, entity_key: str, facts: Dict[str, Any]) -> None:
        """Update entity facts."""
        with self._lock:
            self._entity_cache[entity_key] = facts

    def get_all_entities(self) -> Dict[str, Dict[str, Any]]:
        """Get all entity facts."""
        return dict(self._entity_cache)

    def validate_entity_reference(self, text: str) -> List[str]:
        """
        Check text for wrong entity references.
        Returns list of warnings.
        """
        warnings = []
        # Check wrong names
        for entity_key, facts in self._entity_cache.items():
            wrong_names = facts.get("WRONG_NAMES", [])
            for wrong in wrong_names:
                if wrong.lower() in text.lower():
                    correct = facts.get("name", entity_key)
                    warnings.append(
                        f"WRONG NAME: '{wrong}' found — correct name is '{correct}'"
                    )

        # Check fabricated items
        purged = self._entity_cache.get("fabricated_PURGED", {})
        for item in purged.get("items", []):
            check = item.split(" (")[0]  # strip parenthetical
            if check.lower() in text.lower():
                warnings.append(f"FABRICATED CONTENT: '{item}' — PURGE IMMEDIATELY")

        return warnings

    # ── Cleanup ──

    def cleanup_expired(self) -> Dict[str, int]:
        """Clean expired items from all tiers."""
        counts = {"short_term": 0, "long_term": 0}

        # Short-term
        with self._lock:
            expired_keys = [k for k, v in self._short_term.items() if v.is_expired]
            for k in expired_keys:
                del self._short_term[k]
            counts["short_term"] = len(expired_keys)

        # Long-term
        pm = self._get_persistent()
        if pm:
            try:
                counts["long_term"] = pm.forget(expired_only=True)
            except Exception:
                pass

        return counts

    def stats(self) -> Dict[str, Any]:
        """Memory tier statistics."""
        with self._lock:
            short_items = list(self._short_term.values())
        return {
            "short_term": {
                "count": len(short_items),
                "max": MAX_SHORT_TERM_ITEMS,
                "stale": sum(1 for i in short_items if i.is_stale),
                "expired": sum(1 for i in short_items if i.is_expired),
            },
            "long_term": {
                "available": self._get_persistent() is not None,
            },
            "entity": {
                "count": len(self._entity_cache),
                "keys": list(self._entity_cache.keys()),
            },
        }


# ─────────────────────────────────────────────────────────────
# Context Manager (central orchestrator)
# ─────────────────────────────────────────────────────────────

class ContextManager:
    """
    Central context orchestrator for LitigationOS.
    
    Manages:
    - Context window (serial position optimized)
    - Tiered memory (short/long/entity)
    - Agent handoff protocol
    - Freshness scoring and auto-cleanup
    - Lane boundary enforcement
    
    Thread-safe. Singleton per process.
    """

    _instance: Optional["ContextManager"] = None
    _init_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._init_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, db_path: Optional[Path] = None):
        if self._initialized:
            return
        self._initialized = True

        self._db_path = db_path or _DB_PATH
        self.window = ContextWindow(max_size=CONTEXT_WINDOW_MAX)
        self.memory = TieredMemory(db_path=self._db_path)
        self.scorer = FreshnessScorer()

        self._handoff_log: List[Dict] = []
        self._cleanup_thread: Optional[threading.Thread] = None
        self._shutdown = threading.Event()
        self._lock = threading.Lock()

        # Initialize handoff audit table in DB
        self._init_handoff_table()

        # Start background cleanup
        self._start_cleanup_daemon()

    def _init_handoff_table(self) -> None:
        """Create agent_context_handoffs table for audit trail."""
        try:
            conn = sqlite3.connect(str(self._db_path), timeout=30)
            conn.execute("PRAGMA busy_timeout = 60000")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_context_handoffs (
                    handoff_id TEXT PRIMARY KEY,
                    source_agent TEXT NOT NULL,
                    target_agent TEXT NOT NULL,
                    lane TEXT,
                    task_description TEXT,
                    status TEXT DEFAULT 'pending',
                    items_count INTEGER DEFAULT 0,
                    payload TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    acknowledged_at TEXT,
                    completed_at TEXT,
                    metadata TEXT
                )
            """)
            conn.commit()
            conn.close()
        except Exception:
            pass  # Non-fatal — handoff works without audit table

    def _start_cleanup_daemon(self) -> None:
        """Background thread for automatic memory cleanup."""
        def cleanup_loop():
            while not self._shutdown.is_set():
                try:
                    self.memory.cleanup_expired()
                except Exception:
                    pass
                self._shutdown.wait(timeout=CLEANUP_INTERVAL_S)

        self._cleanup_thread = threading.Thread(
            target=cleanup_loop, daemon=True, name="context-cleanup"
        )
        self._cleanup_thread.start()

    # ── Context Window Operations ──

    def add_context(self, key: str, value: Any,
                    priority: ContextPriority = ContextPriority.MEDIUM,
                    lane: Optional[str] = None,
                    source: str = "session") -> None:
        """Add item to the active context window and short-term memory."""
        item = ContextItem(
            key=key, value=value, priority=priority,
            lane=lane, source=source,
        )
        evicted = self.window.add(item)
        self.memory.store_short(key, value, priority, lane, source)

        if evicted and evicted.priority in (ContextPriority.HIGH, ContextPriority.MEDIUM):
            # Promote evicted important items to long-term memory
            self.memory.store_long(
                key=evicted.key,
                value=str(evicted.value),
                memory_type="evicted_context",
                confidence=evicted.freshness_score,
                source=f"evicted_from_window:{evicted.source}",
            )

    def get_context(self, lane: Optional[str] = None,
                    min_priority: ContextPriority = ContextPriority.LOW) -> List[ContextItem]:
        """
        Get optimized context window items.
        Applies serial position optimization.
        Filters by lane and minimum priority.
        """
        items = self.window.get_optimized()
        if lane:
            items = [i for i in items if i.lane is None or i.lane == lane]
        priority_order = [ContextPriority.CRITICAL, ContextPriority.HIGH,
                          ContextPriority.MEDIUM, ContextPriority.LOW]
        min_idx = priority_order.index(min_priority)
        allowed = set(priority_order[:min_idx + 1])
        items = [i for i in items if i.priority in allowed]
        return items

    def find_context(self, key: str) -> Optional[ContextItem]:
        """Find a specific context item by key."""
        return self.window.find(key)

    # ── Agent Handoff Protocol ──

    def create_handoff(self, source_agent: str, target_agent: str,
                       lane: str, task: str,
                       include_window: bool = True,
                       include_entities: bool = True) -> AgentContext:
        """
        Create a context handoff payload for agent-to-agent transfer.
        
        Per context-manager skill: explicit handoff with verification.
        """
        ctx = AgentContext(
            source_agent=source_agent,
            target_agent=target_agent,
            lane=lane,
            task_description=task,
        )

        # Include current window items for this lane
        if include_window:
            for item in self.get_context(lane=lane):
                ctx.items.append(item)

        # Include entity facts
        if include_entities:
            for entity_key, facts in self.memory.get_all_entities().items():
                ctx.items.append(ContextItem(
                    key=f"entity:{entity_key}",
                    value=json.dumps(facts, default=str),
                    priority=ContextPriority.CRITICAL,
                    source="entity_memory",
                ))

        # Log handoff
        self._log_handoff(ctx)
        return ctx

    def receive_handoff(self, ctx: AgentContext) -> bool:
        """
        Receive and acknowledge a handoff from another agent.
        Loads items into the active context window.
        Returns True if successful.
        """
        try:
            ctx.acknowledge()

            # Load handoff items into window
            for item in ctx.items:
                if item.key.startswith("entity:"):
                    # Entity items go to entity memory
                    entity_key = item.key.replace("entity:", "")
                    try:
                        facts = json.loads(item.value)
                        self.memory.set_entity(entity_key, facts)
                    except (json.JSONDecodeError, TypeError):
                        pass
                else:
                    self.window.add(item)

            # Update audit log
            self._update_handoff_status(ctx.handoff_id, "acknowledged")
            return True
        except Exception:
            ctx.fail("Failed to receive handoff")
            self._update_handoff_status(ctx.handoff_id, "failed")
            return False

    def complete_handoff(self, handoff_id: str) -> None:
        """Mark a handoff as completed."""
        self._update_handoff_status(handoff_id, "completed")

    def _log_handoff(self, ctx: AgentContext) -> None:
        """Log handoff to DB audit trail."""
        try:
            conn = sqlite3.connect(str(self._db_path), timeout=30)
            conn.execute("PRAGMA busy_timeout = 60000")
            conn.execute("""
                INSERT OR REPLACE INTO agent_context_handoffs
                (handoff_id, source_agent, target_agent, lane, task_description,
                 status, items_count, payload, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ctx.handoff_id, ctx.source_agent, ctx.target_agent,
                ctx.lane, ctx.task_description, ctx.status.value,
                len(ctx.items), ctx.serialize(),
                json.dumps(ctx.metadata, default=str),
            ))
            conn.commit()
            conn.close()
        except Exception:
            pass  # Non-fatal

    def _update_handoff_status(self, handoff_id: str, status: str) -> None:
        """Update handoff status in DB."""
        try:
            ts_col = {"acknowledged": "acknowledged_at", "completed": "completed_at"}.get(status)
            conn = sqlite3.connect(str(self._db_path), timeout=30)
            conn.execute("PRAGMA busy_timeout = 60000")
            sql = f"UPDATE agent_context_handoffs SET status = ?"
            params: list = [status]
            if ts_col:
                sql += f", {ts_col} = datetime('now')"
            sql += " WHERE handoff_id = ?"
            params.append(handoff_id)
            conn.execute(sql, params)
            conn.commit()
            conn.close()
        except Exception:
            pass

    # ── Freshness & Quality ──

    def audit_freshness(self) -> FreshnessReport:
        """Audit freshness of all active context items."""
        all_items = self.window.items + self.memory.recall_short()
        items_to_audit = []
        for item in all_items:
            if isinstance(item, ContextItem):
                items_to_audit.append(item)
        return FreshnessScorer.audit(items_to_audit)

    def validate_output(self, text: str) -> List[str]:
        """
        Validate output text against entity memory.
        Returns list of warnings about wrong names, fabrications, etc.
        """
        return self.memory.validate_entity_reference(text)

    # ── Lane Management ──

    def set_active_lane(self, lane: str) -> None:
        """Set the active case lane (filters context retrieval)."""
        if lane not in VALID_LANES:
            raise ValueError(f"Invalid lane '{lane}'. Must be one of {VALID_LANES}")
        self.add_context(
            key="active_lane",
            value=lane,
            priority=ContextPriority.CRITICAL,
            source="lane_manager",
        )

    def get_active_lane(self) -> Optional[str]:
        """Get the current active lane."""
        item = self.find_context("active_lane")
        return item.value if item else None

    # ── Convenience Methods ──

    def remember(self, key: str, value: str, tier: MemoryTier = MemoryTier.SHORT_TERM,
                 **kwargs) -> None:
        """Universal remember method — routes to appropriate tier."""
        if tier == MemoryTier.SHORT_TERM:
            self.memory.store_short(key, value, **kwargs)
        elif tier == MemoryTier.LONG_TERM:
            self.memory.store_long(key, value, **kwargs)
        elif tier == MemoryTier.ENTITY:
            self.memory.set_entity(key, {"value": value, **kwargs})

    def recall(self, key: Optional[str] = None, tier: Optional[MemoryTier] = None,
               **kwargs) -> List[Any]:
        """Universal recall method — searches across tiers."""
        results = []

        if tier is None or tier == MemoryTier.SHORT_TERM:
            results.extend(self.memory.recall_short(key=key))

        if tier is None or tier == MemoryTier.ENTITY:
            if key:
                entity = self.memory.get_entity(key)
                if entity:
                    results.append(ContextItem(
                        key=key, value=entity,
                        priority=ContextPriority.CRITICAL,
                        source="entity_memory",
                    ))
            else:
                for ek, ev in self.memory.get_all_entities().items():
                    results.append(ContextItem(
                        key=ek, value=ev,
                        priority=ContextPriority.CRITICAL,
                        source="entity_memory",
                    ))

        if tier is None or tier == MemoryTier.LONG_TERM:
            long_results = self.memory.recall_long(key=key, **kwargs)
            for lr in long_results:
                results.append(ContextItem(
                    key=lr.get("key", "unknown"),
                    value=lr.get("value", ""),
                    priority=ContextPriority.MEDIUM,
                    source="long_term_memory",
                    created_at=lr.get("created_at", time.time()),
                ))

        return results

    # ── Health & Status ──

    def health(self) -> Dict[str, Any]:
        """Full context system health report."""
        freshness = self.audit_freshness()
        return {
            "window": self.window.summary(),
            "memory": self.memory.stats(),
            "freshness": {
                "total": freshness.total_items,
                "fresh": freshness.fresh_items,
                "stale": freshness.stale_items,
                "expired": freshness.expired_items,
                "avg_score": freshness.avg_freshness,
                "warnings": freshness.warnings[:5],
            },
            "cleanup_daemon": self._cleanup_thread is not None and self._cleanup_thread.is_alive(),
            "active_lane": self.get_active_lane(),
        }

    def shutdown(self) -> None:
        """Graceful shutdown — stop cleanup daemon."""
        self._shutdown.set()
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=5)


# ─────────────────────────────────────────────────────────────
# Module-level convenience
# ─────────────────────────────────────────────────────────────

def get_context_manager(db_path: Optional[Path] = None) -> ContextManager:
    """Get the singleton ContextManager instance."""
    return ContextManager(db_path=db_path)


# ─────────────────────────────────────────────────────────────
# CLI interface
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import pprint

    cm = get_context_manager()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "health":
            pprint.pprint(cm.health())

        elif cmd == "entities":
            for key, facts in cm.memory.get_all_entities().items():
                print(f"\n[{key}]")
                for k, v in facts.items():
                    print(f"  {k}: {v}")

        elif cmd == "validate":
            text = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
            warnings = cm.validate_output(text)
            if warnings:
                for w in warnings:
                    print(f"  ⚠️  {w}")
            else:
                print("  ✅ No issues found")

        elif cmd == "freshness":
            report = cm.audit_freshness()
            pprint.pprint(asdict(report))

        else:
            print(f"Unknown command: {cmd}")
            print("Usage: context_manager.py [health|entities|validate <text>|freshness]")
    else:
        print("LitigationOS Context Manager — Δ99 Ω∞")
        print("========================================")
        health = cm.health()
        print(f"Window: {health['window']['size']}/{health['window']['max_size']} items")
        print(f"Entities: {health['memory']['entity']['count']} loaded")
        print(f"Cleanup daemon: {'✅ running' if health['cleanup_daemon'] else '❌ stopped'}")
        print(f"Active lane: {health['active_lane'] or 'none'}")
        print()
        print("Commands: health, entities, validate <text>, freshness")

    cm.shutdown()
