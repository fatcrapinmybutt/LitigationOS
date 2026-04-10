"""
Omega Genetic Memory — Cross-Session Evolutionary Intelligence.
================================================================

Phase 1 of the OMEGA SINGULARITY.  Every session writes discoveries,
every session reads what previous sessions learned.  Memories evolve:
high-fitness memories persist and reproduce; low-fitness memories decay
and are eventually archived (never deleted — Rule 1).

Memory lifecycle:
  WRITE  → new memory created with initial fitness 1.0
  USE    → fitness boosted (+0.1 per successful use)
  EVOLVE → child memory created from parent (generation + 1)
  DECAY  → periodic fitness reduction (unused memories fade)
  PRUNE  → low-fitness, old memories archived to omega_genetic_memory_archive

Integration points:
  - Event Bus: subscribes to evidence.*, filing.*, self.improved, adversary.*
  - Startup Hook: get_session_context() injects top memories into session
  - Session Recall: record discoveries at session end
  - All Engines: retrieve() before acting, write() after discovering

Tables:
  - omega_genetic_memory: Active memory pool (evolutionary, fitness-scored)
  - omega_genetic_memory_archive: Archived low-fitness memories (preserved, never deleted)
"""

import hashlib
import json
import logging
import os
import re
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Any, Optional

logger = logging.getLogger("daemon.genetic_memory")


# ═══════════════════════════════════════════════════════════════════════════════
# Database helpers — same pattern as event_bus.py
# ═══════════════════════════════════════════════════════════════════════════════

def _get_db_path() -> str:
    """Resolve litigation_context.db path."""
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


def _generate_memory_id(memory_type: str, topic: str) -> str:
    """Generate a unique memory ID."""
    ts = datetime.now().strftime("%Y%m%d%H%M%S%f")
    h = hashlib.md5(f"{memory_type}:{topic}:{ts}".encode()).hexdigest()[:8]
    return f"mem-{ts[:14]}-{h}"


def _content_hash(content: str) -> str:
    """SHA-256 hash for deduplication."""
    return hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()


# ═══════════════════════════════════════════════════════════════════════════════
# Memory type constants
# ═══════════════════════════════════════════════════════════════════════════════

MEMORY_TYPES = frozenset({
    "search_success",       # Queries that returned high-quality results
    "filing_outcome",       # What scored well in filed documents
    "strategy_result",      # Which legal strategies were effective
    "error_pattern",        # Recurring failures and their fixes
    "user_preference",      # Andrew's explicit preferences and feedback
    "authority_discovery",  # New legal authorities found and validated
    "adversary_behavior",   # Observed patterns in Emily/McNeill/FOC behavior
    "judicial_prediction",  # Predictions about judicial actions and accuracy
    "evidence_insight",     # Cross-lane evidence connections discovered
    "procedural_learning",  # MCR/MCL procedural insights
    "session_intelligence", # Session-level strategic insights
    "critical_fact",        # Verified immutable facts about the case
})

VALID_LANES = frozenset({"A", "B", "C", "D", "E", "F", "CRIMINAL", None})


# ═══════════════════════════════════════════════════════════════════════════════
# GeneticMemory — The Evolutionary Memory Engine
# ═══════════════════════════════════════════════════════════════════════════════

class GeneticMemory:
    """Cross-session evolutionary intelligence with fitness-scored memories.

    Memories evolve through:
    - **Selection**: High-fitness memories surface first in retrieval
    - **Reproduction**: Successful memories spawn evolved children (evolve())
    - **Mutation**: Content can be refined as new evidence appears
    - **Decay**: Unused memories lose fitness over time
    - **Archival**: Low-fitness memories archived, never deleted (Rule 1)
    """

    # ── DDL ────────────────────────────────────────────────────────────────

    _DDL_ACTIVE = """
    CREATE TABLE IF NOT EXISTS omega_genetic_memory (
        memory_id       TEXT PRIMARY KEY,
        memory_type     TEXT NOT NULL,
        topic           TEXT NOT NULL,
        content         TEXT NOT NULL,
        content_hash    TEXT NOT NULL,
        confidence      REAL NOT NULL DEFAULT 1.0,
        source          TEXT,
        lane            TEXT,
        fitness_score   REAL NOT NULL DEFAULT 1.0,
        times_used      INTEGER NOT NULL DEFAULT 0,
        times_boosted   INTEGER NOT NULL DEFAULT 0,
        last_used       TEXT,
        last_boosted    TEXT,
        generation      INTEGER NOT NULL DEFAULT 0,
        parent_memory_id TEXT,
        is_verified     INTEGER NOT NULL DEFAULT 0,
        tags            TEXT DEFAULT '[]',
        metadata        TEXT DEFAULT '{}',
        created_at      TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """

    _DDL_ARCHIVE = """
    CREATE TABLE IF NOT EXISTS omega_genetic_memory_archive (
        memory_id       TEXT PRIMARY KEY,
        memory_type     TEXT NOT NULL,
        topic           TEXT NOT NULL,
        content         TEXT NOT NULL,
        content_hash    TEXT NOT NULL,
        confidence      REAL NOT NULL DEFAULT 1.0,
        source          TEXT,
        lane            TEXT,
        fitness_score   REAL NOT NULL DEFAULT 0.0,
        times_used      INTEGER NOT NULL DEFAULT 0,
        times_boosted   INTEGER NOT NULL DEFAULT 0,
        last_used       TEXT,
        last_boosted    TEXT,
        generation      INTEGER NOT NULL DEFAULT 0,
        parent_memory_id TEXT,
        is_verified     INTEGER NOT NULL DEFAULT 0,
        tags            TEXT DEFAULT '[]',
        metadata        TEXT DEFAULT '{}',
        created_at      TEXT NOT NULL,
        updated_at      TEXT NOT NULL,
        archived_at     TEXT NOT NULL DEFAULT (datetime('now')),
        archive_reason  TEXT DEFAULT 'fitness_decay'
    );
    """

    _DDL_INDEXES = """
    CREATE INDEX IF NOT EXISTS idx_gm_type_fitness
        ON omega_genetic_memory(memory_type, fitness_score DESC);
    CREATE INDEX IF NOT EXISTS idx_gm_topic
        ON omega_genetic_memory(topic);
    CREATE INDEX IF NOT EXISTS idx_gm_lane_fitness
        ON omega_genetic_memory(lane, fitness_score DESC);
    CREATE INDEX IF NOT EXISTS idx_gm_content_hash
        ON omega_genetic_memory(content_hash);
    CREATE INDEX IF NOT EXISTS idx_gm_generation
        ON omega_genetic_memory(generation);
    CREATE INDEX IF NOT EXISTS idx_gm_verified
        ON omega_genetic_memory(is_verified, fitness_score DESC);
    CREATE INDEX IF NOT EXISTS idx_gm_parent
        ON omega_genetic_memory(parent_memory_id);
    """

    # ── Constructor ────────────────────────────────────────────────────────

    def __init__(self, db_path: str = None):
        self._db_path = db_path
        self._ensure_tables()
        self._stats_cache: dict[str, Any] = {}
        self._stats_cache_time: float = 0.0
        logger.info("GeneticMemory initialized")

    def _ensure_tables(self):
        """Create omega_genetic_memory + archive tables if they don't exist."""
        conn = _connect(self._db_path)
        try:
            conn.executescript(
                self._DDL_ACTIVE + self._DDL_ARCHIVE + self._DDL_INDEXES
            )
            conn.commit()
            logger.info("omega_genetic_memory tables ensured")
        except sqlite3.Error as e:
            logger.error("Failed to ensure genetic memory tables: %s", e)
            raise
        finally:
            conn.close()

    # ── Write ──────────────────────────────────────────────────────────────

    def write_memory(
        self,
        memory_type: str,
        topic: str,
        content: str,
        confidence: float = 1.0,
        source: str = None,
        lane: str = None,
        fitness_score: float = 1.0,
        is_verified: int = 0,
        tags: list[str] = None,
        metadata: dict = None,
        parent_memory_id: str = None,
        generation: int = 0,
    ) -> str:
        """Write a new memory to the genetic pool.

        Returns the memory_id of the newly created memory.
        Deduplicates by content_hash — if identical content exists,
        boosts existing memory fitness instead of creating duplicate.
        """
        if memory_type not in MEMORY_TYPES:
            raise ValueError(
                f"Invalid memory_type '{memory_type}'. "
                f"Valid types: {sorted(MEMORY_TYPES)}"
            )
        if lane is not None and lane not in VALID_LANES:
            raise ValueError(f"Invalid lane '{lane}'. Valid: {sorted(x for x in VALID_LANES if x)}")

        confidence = max(0.0, min(1.0, confidence))
        fitness_score = max(0.0, fitness_score)
        c_hash = _content_hash(content)

        conn = _connect(self._db_path)
        try:
            # Dedup check — if same content exists, boost it instead
            existing = conn.execute(
                "SELECT memory_id, fitness_score FROM omega_genetic_memory "
                "WHERE content_hash = ?",
                (c_hash,)
            ).fetchone()

            if existing:
                new_fitness = existing["fitness_score"] + 0.05
                conn.execute(
                    "UPDATE omega_genetic_memory SET fitness_score = ?, "
                    "times_boosted = times_boosted + 1, "
                    "last_boosted = datetime('now'), "
                    "updated_at = datetime('now') "
                    "WHERE memory_id = ?",
                    (new_fitness, existing["memory_id"])
                )
                conn.commit()
                logger.debug(
                    "Dedup hit for content_hash=%s, boosted %s to fitness=%.2f",
                    c_hash[:12], existing["memory_id"], new_fitness
                )
                return existing["memory_id"]

            # Create new memory
            memory_id = _generate_memory_id(memory_type, topic)
            conn.execute(
                """INSERT INTO omega_genetic_memory
                (memory_id, memory_type, topic, content, content_hash,
                 confidence, source, lane, fitness_score, is_verified,
                 tags, metadata, parent_memory_id, generation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    memory_id, memory_type, topic, content, c_hash,
                    confidence, source, lane, fitness_score, is_verified,
                    json.dumps(tags or []), json.dumps(metadata or {}),
                    parent_memory_id, generation,
                )
            )
            conn.commit()
            logger.info(
                "Memory written: id=%s type=%s topic=%s fitness=%.2f",
                memory_id, memory_type, topic, fitness_score
            )
            return memory_id

        except sqlite3.Error as e:
            logger.error("Failed to write memory: %s", e)
            raise
        finally:
            conn.close()

    # ── Retrieve ───────────────────────────────────────────────────────────

    def retrieve(
        self,
        topic: str = None,
        memory_type: str = None,
        lane: str = None,
        min_fitness: float = 0.0,
        verified_only: bool = False,
        min_generation: int = 0,
        limit: int = 20,
    ) -> list[dict]:
        """Retrieve relevant memories sorted by fitness_score DESC.

        Automatically increments times_used and updates last_used for
        returned memories (retrieval = usage = selection pressure).
        """
        conn = _connect(self._db_path)
        try:
            conditions = ["fitness_score >= ?"]
            params: list[Any] = [min_fitness]

            if topic:
                # FTS5-safe: sanitize then use LIKE for flexible matching
                safe_topic = re.sub(r'[^\w\s]', ' ', topic).strip()
                if safe_topic:
                    conditions.append("topic LIKE ?")
                    params.append(f"%{safe_topic}%")

            if memory_type:
                conditions.append("memory_type = ?")
                params.append(memory_type)

            if lane is not None:
                conditions.append("lane = ?")
                params.append(lane)

            if verified_only:
                conditions.append("is_verified = 1")

            if min_generation > 0:
                conditions.append("generation >= ?")
                params.append(min_generation)

            where_clause = " AND ".join(conditions)
            params.append(limit)

            rows = conn.execute(
                f"""SELECT memory_id, memory_type, topic, content, confidence,
                       source, lane, fitness_score, times_used, times_boosted,
                       last_used, generation, parent_memory_id, is_verified,
                       tags, metadata, created_at, updated_at
                FROM omega_genetic_memory
                WHERE {where_clause}
                ORDER BY fitness_score DESC, times_used DESC, created_at DESC
                LIMIT ?""",
                params
            ).fetchall()

            results = [dict(r) for r in rows]

            # Mark as used — selection pressure
            if results:
                ids = [r["memory_id"] for r in results]
                placeholders = ",".join(["?"] * len(ids))
                conn.execute(
                    f"""UPDATE omega_genetic_memory
                    SET times_used = times_used + 1,
                        last_used = datetime('now'),
                        updated_at = datetime('now')
                    WHERE memory_id IN ({placeholders})""",
                    ids
                )
                conn.commit()

            return results

        except sqlite3.Error as e:
            logger.error("Failed to retrieve memories: %s", e)
            return []
        finally:
            conn.close()

    # ── Boost ──────────────────────────────────────────────────────────────

    def boost_fitness(self, memory_id: str, amount: float = 0.1) -> float:
        """Increase fitness when a memory leads to a successful outcome.

        Returns the new fitness score.
        """
        conn = _connect(self._db_path)
        try:
            row = conn.execute(
                "SELECT fitness_score FROM omega_genetic_memory WHERE memory_id = ?",
                (memory_id,)
            ).fetchone()
            if not row:
                logger.warning("boost_fitness: memory_id=%s not found", memory_id)
                return 0.0

            new_fitness = row["fitness_score"] + abs(amount)
            conn.execute(
                """UPDATE omega_genetic_memory
                SET fitness_score = ?,
                    times_boosted = times_boosted + 1,
                    last_boosted = datetime('now'),
                    updated_at = datetime('now')
                WHERE memory_id = ?""",
                (new_fitness, memory_id)
            )
            conn.commit()
            logger.debug("Boosted %s: %.2f → %.2f", memory_id, row["fitness_score"], new_fitness)
            return new_fitness

        except sqlite3.Error as e:
            logger.error("Failed to boost fitness: %s", e)
            return 0.0
        finally:
            conn.close()

    # ── Decay ──────────────────────────────────────────────────────────────

    def decay_fitness(self, decay_rate: float = 0.01, floor: float = 0.05) -> int:
        """Periodic fitness decay for all memories.

        Verified memories decay at half rate.  Memories below floor are
        candidates for archival via prune().

        Returns the number of memories decayed.
        """
        conn = _connect(self._db_path)
        try:
            # Unverified memories: full decay rate
            result1 = conn.execute(
                """UPDATE omega_genetic_memory
                SET fitness_score = MAX(?, fitness_score - ?),
                    updated_at = datetime('now')
                WHERE is_verified = 0 AND fitness_score > ?""",
                (floor, decay_rate, floor)
            )
            count1 = result1.rowcount

            # Verified memories: half decay rate (more resilient)
            result2 = conn.execute(
                """UPDATE omega_genetic_memory
                SET fitness_score = MAX(?, fitness_score - ?),
                    updated_at = datetime('now')
                WHERE is_verified = 1 AND fitness_score > ?""",
                (floor, decay_rate / 2.0, floor)
            )
            count2 = result2.rowcount

            conn.commit()
            total = count1 + count2
            if total > 0:
                logger.info(
                    "Decayed %d memories (rate=%.3f, floor=%.2f): "
                    "%d unverified, %d verified",
                    total, decay_rate, floor, count1, count2
                )
            return total

        except sqlite3.Error as e:
            logger.error("Failed to decay fitness: %s", e)
            return 0
        finally:
            conn.close()

    # ── Evolve ─────────────────────────────────────────────────────────────

    def evolve(
        self,
        parent_id: str,
        new_content: str,
        new_confidence: float = None,
        new_tags: list[str] = None,
    ) -> str:
        """Create a child memory from a parent (generation + 1).

        The child inherits the parent's type, topic, lane, and source,
        but has updated content and starts with the parent's fitness + 0.1
        (evolved memories are slightly fitter than their parents).

        Returns the child memory_id.
        """
        conn = _connect(self._db_path)
        try:
            parent = conn.execute(
                """SELECT memory_type, topic, confidence, source, lane,
                          fitness_score, generation, is_verified, tags
                FROM omega_genetic_memory WHERE memory_id = ?""",
                (parent_id,)
            ).fetchone()

            if not parent:
                raise ValueError(f"Parent memory '{parent_id}' not found")

            child_confidence = new_confidence if new_confidence is not None else parent["confidence"]
            child_fitness = parent["fitness_score"] + 0.1  # evolution bonus
            child_generation = parent["generation"] + 1

            # Merge tags
            parent_tags = json.loads(parent["tags"]) if parent["tags"] else []
            merged_tags = list(set(parent_tags + (new_tags or [])))

            child_id = self.write_memory(
                memory_type=parent["memory_type"],
                topic=parent["topic"],
                content=new_content,
                confidence=child_confidence,
                source=parent["source"],
                lane=parent["lane"],
                fitness_score=child_fitness,
                is_verified=parent["is_verified"],
                tags=merged_tags,
                metadata={"evolved_from": parent_id, "evolution_reason": "content_update"},
                parent_memory_id=parent_id,
                generation=child_generation,
            )

            logger.info(
                "Evolved: parent=%s → child=%s (gen %d → %d, fitness %.2f → %.2f)",
                parent_id, child_id, parent["generation"], child_generation,
                parent["fitness_score"], child_fitness
            )
            return child_id

        except sqlite3.Error as e:
            logger.error("Failed to evolve memory: %s", e)
            raise
        finally:
            conn.close()

    # ── Prune (Archive) ───────────────────────────────────────────────────

    def prune(
        self,
        min_fitness: float = 0.05,
        max_age_days: int = 90,
        reason: str = "fitness_decay",
    ) -> int:
        """Archive low-fitness, old memories to omega_genetic_memory_archive.

        NEVER deletes — moves to archive table (Rule 1: no deletions).
        Returns the number of memories archived.
        """
        conn = _connect(self._db_path)
        try:
            cutoff_date = (datetime.now() - timedelta(days=max_age_days)).isoformat()

            # Find candidates: low fitness AND old AND not recently used
            candidates = conn.execute(
                """SELECT memory_id FROM omega_genetic_memory
                WHERE fitness_score <= ?
                  AND created_at < ?
                  AND (last_used IS NULL OR last_used < ?)
                  AND is_verified = 0""",
                (min_fitness, cutoff_date, cutoff_date)
            ).fetchall()

            if not candidates:
                return 0

            ids = [r["memory_id"] for r in candidates]
            placeholders = ",".join(["?"] * len(ids))

            # Copy to archive
            conn.execute(
                f"""INSERT OR IGNORE INTO omega_genetic_memory_archive
                (memory_id, memory_type, topic, content, content_hash,
                 confidence, source, lane, fitness_score, times_used,
                 times_boosted, last_used, last_boosted, generation,
                 parent_memory_id, is_verified, tags, metadata,
                 created_at, updated_at, archive_reason)
                SELECT memory_id, memory_type, topic, content, content_hash,
                       confidence, source, lane, fitness_score, times_used,
                       times_boosted, last_used, last_boosted, generation,
                       parent_memory_id, is_verified, tags, metadata,
                       created_at, updated_at, ?
                FROM omega_genetic_memory
                WHERE memory_id IN ({placeholders})""",
                [reason] + ids
            )

            # Remove from active pool
            conn.execute(
                f"DELETE FROM omega_genetic_memory WHERE memory_id IN ({placeholders})",
                ids
            )
            conn.commit()

            logger.info(
                "Pruned %d memories to archive (fitness<=%.2f, age>%d days)",
                len(ids), min_fitness, max_age_days
            )
            return len(ids)

        except sqlite3.Error as e:
            logger.error("Failed to prune memories: %s", e)
            return 0
        finally:
            conn.close()

    # ── Session Context ───────────────────────────────────────────────────

    def get_session_context(self, limit: int = 50) -> list[dict]:
        """Top-fitness memories formatted for session injection.

        Called by startup_hook to pre-load the session with accumulated
        intelligence from all prior sessions.  Returns a diverse mix:
        - Top 10 verified facts
        - Top 10 user preferences
        - Top 10 strategy results
        - Top 10 error patterns (avoid repeating mistakes)
        - Top 10 general (by fitness)
        """
        conn = _connect(self._db_path)
        try:
            results = []
            categories = [
                ("critical_fact", 10),
                ("user_preference", 10),
                ("strategy_result", 10),
                ("error_pattern", 10),
            ]

            collected_ids = set()
            for mem_type, cat_limit in categories:
                rows = conn.execute(
                    """SELECT memory_id, memory_type, topic, content, confidence,
                              lane, fitness_score, generation, is_verified
                    FROM omega_genetic_memory
                    WHERE memory_type = ?
                    ORDER BY fitness_score DESC, times_used DESC
                    LIMIT ?""",
                    (mem_type, cat_limit)
                ).fetchall()
                for r in rows:
                    if r["memory_id"] not in collected_ids:
                        results.append(dict(r))
                        collected_ids.add(r["memory_id"])

            # Fill remaining slots with highest-fitness from any type
            remaining = limit - len(results)
            if remaining > 0:
                placeholders = ",".join(["?"] * len(collected_ids)) if collected_ids else "''"
                exclude_params = list(collected_ids) + [remaining]
                if collected_ids:
                    rows = conn.execute(
                        f"""SELECT memory_id, memory_type, topic, content, confidence,
                                   lane, fitness_score, generation, is_verified
                        FROM omega_genetic_memory
                        WHERE memory_id NOT IN ({placeholders})
                        ORDER BY fitness_score DESC, times_used DESC
                        LIMIT ?""",
                        exclude_params
                    ).fetchall()
                else:
                    rows = conn.execute(
                        """SELECT memory_id, memory_type, topic, content, confidence,
                                  lane, fitness_score, generation, is_verified
                        FROM omega_genetic_memory
                        ORDER BY fitness_score DESC, times_used DESC
                        LIMIT ?""",
                        (remaining,)
                    ).fetchall()
                for r in rows:
                    if r["memory_id"] not in collected_ids:
                        results.append(dict(r))

            return results

        except sqlite3.Error as e:
            logger.error("Failed to get session context: %s", e)
            return []
        finally:
            conn.close()

    # ── User Preference ───────────────────────────────────────────────────

    def record_user_preference(
        self,
        topic: str,
        content: str,
        source: str = "user_feedback",
    ) -> str:
        """Special write for user feedback — high initial fitness (2.0).

        User preferences are the strongest signal and should persist
        across many sessions without decay (verified = 1).
        """
        return self.write_memory(
            memory_type="user_preference",
            topic=topic,
            content=content,
            confidence=1.0,
            source=source,
            fitness_score=2.0,
            is_verified=1,
            tags=["user_preference", "high_priority"],
        )

    # ── Verify ────────────────────────────────────────────────────────────

    def verify_memory(self, memory_id: str, verified_by: str = "system") -> bool:
        """Mark a memory as verified — verified memories resist decay."""
        conn = _connect(self._db_path)
        try:
            result = conn.execute(
                """UPDATE omega_genetic_memory
                SET is_verified = 1,
                    fitness_score = MAX(fitness_score, 1.0),
                    metadata = json_set(COALESCE(metadata, '{}'), '$.verified_by', ?),
                    updated_at = datetime('now')
                WHERE memory_id = ?""",
                (verified_by, memory_id)
            )
            conn.commit()
            return result.rowcount > 0
        except sqlite3.Error as e:
            logger.error("Failed to verify memory: %s", e)
            return False
        finally:
            conn.close()

    # ── Stats ─────────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Memory pool statistics — cached for 30 seconds."""
        now = time.time()
        if now - self._stats_cache_time < 30 and self._stats_cache:
            return self._stats_cache

        conn = _connect(self._db_path)
        try:
            row = conn.execute("""
                SELECT
                    (SELECT COUNT(*) FROM omega_genetic_memory) AS total_active,
                    (SELECT COUNT(*) FROM omega_genetic_memory_archive) AS total_archived,
                    (SELECT ROUND(AVG(fitness_score), 3) FROM omega_genetic_memory) AS avg_fitness,
                    (SELECT MAX(fitness_score) FROM omega_genetic_memory) AS max_fitness,
                    (SELECT MIN(fitness_score) FROM omega_genetic_memory) AS min_fitness,
                    (SELECT COUNT(*) FROM omega_genetic_memory WHERE is_verified = 1) AS verified_count,
                    (SELECT MAX(generation) FROM omega_genetic_memory) AS max_generation,
                    (SELECT SUM(times_used) FROM omega_genetic_memory) AS total_uses,
                    (SELECT COUNT(DISTINCT memory_type) FROM omega_genetic_memory) AS type_diversity,
                    (SELECT COUNT(DISTINCT topic) FROM omega_genetic_memory) AS topic_diversity,
                    (SELECT COUNT(DISTINCT lane) FROM omega_genetic_memory WHERE lane IS NOT NULL) AS lane_coverage
            """).fetchone()

            # Type breakdown
            type_rows = conn.execute(
                """SELECT memory_type, COUNT(*) as cnt,
                          ROUND(AVG(fitness_score), 3) as avg_fit
                FROM omega_genetic_memory
                GROUP BY memory_type
                ORDER BY cnt DESC"""
            ).fetchall()

            stats = dict(row)
            stats["type_breakdown"] = {r["memory_type"]: {"count": r["cnt"], "avg_fitness": r["avg_fit"]} for r in type_rows}
            stats["timestamp"] = datetime.now().isoformat()

            self._stats_cache = stats
            self._stats_cache_time = now
            return stats

        except sqlite3.Error as e:
            logger.error("Failed to get stats: %s", e)
            return {"error": str(e)}
        finally:
            conn.close()

    # ── Seed from Existing ────────────────────────────────────────────────

    def seed_from_existing(self) -> dict:
        """One-time migration from legacy memory tables into omega_genetic_memory.

        Sources:
        - agent_genetic_memory (10 rows) → error_pattern memories
        - hydra_genetic_memory (10 rows) → error_pattern memories
        - session_intelligence (non-duplicate) → session_intelligence memories
        - critical_facts (non-duplicate) → critical_fact memories

        Returns counts of migrated rows per source.
        """
        conn = _connect(self._db_path)
        counts = {
            "agent_genetic_memory": 0,
            "hydra_genetic_memory": 0,
            "session_intelligence": 0,
            "critical_facts": 0,
        }

        try:
            # Helper: check if table exists
            def table_exists(name: str) -> bool:
                r = conn.execute(
                    "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
                    (name,)
                ).fetchone()
                return r[0] > 0

            # ── agent_genetic_memory ──
            if table_exists("agent_genetic_memory"):
                rows = conn.execute(
                    """SELECT failure_pattern, fix_applied, context, success_rate,
                              times_applied, created_at
                    FROM agent_genetic_memory
                    WHERE deprecated = 0"""
                ).fetchall()
                for r in rows:
                    content = f"Pattern: {r['failure_pattern']}\nFix: {r['fix_applied']}"
                    if r["context"]:
                        content += f"\nContext: {r['context']}"
                    c_hash = _content_hash(content)
                    existing = conn.execute(
                        "SELECT 1 FROM omega_genetic_memory WHERE content_hash = ?",
                        (c_hash,)
                    ).fetchone()
                    if not existing:
                        mid = _generate_memory_id("error_pattern", "agent_fix")
                        fitness = 0.5 + (r["success_rate"] or 0.0) * 0.5
                        conn.execute(
                            """INSERT INTO omega_genetic_memory
                            (memory_id, memory_type, topic, content, content_hash,
                             confidence, source, fitness_score, times_used,
                             is_verified, tags)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (mid, "error_pattern", "agent_fix", content, c_hash,
                             r["success_rate"] or 0.5, "agent_genetic_memory",
                             fitness, r["times_applied"] or 0, 0,
                             json.dumps(["seeded", "agent_legacy"]))
                        )
                        counts["agent_genetic_memory"] += 1

            # ── hydra_genetic_memory ──
            if table_exists("hydra_genetic_memory"):
                rows = conn.execute(
                    """SELECT failure_pattern, fix_applied, context, success_rate,
                              times_applied, created_at
                    FROM hydra_genetic_memory
                    WHERE deprecated = 0"""
                ).fetchall()
                for r in rows:
                    content = f"Pattern: {r['failure_pattern']}\nFix: {r['fix_applied']}"
                    if r["context"]:
                        content += f"\nContext: {r['context']}"
                    c_hash = _content_hash(content)
                    existing = conn.execute(
                        "SELECT 1 FROM omega_genetic_memory WHERE content_hash = ?",
                        (c_hash,)
                    ).fetchone()
                    if not existing:
                        mid = _generate_memory_id("error_pattern", "hydra_fix")
                        fitness = 0.5 + (r["success_rate"] or 0.0) * 0.5
                        conn.execute(
                            """INSERT INTO omega_genetic_memory
                            (memory_id, memory_type, topic, content, content_hash,
                             confidence, source, fitness_score, times_used,
                             is_verified, tags)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (mid, "error_pattern", "hydra_fix", content, c_hash,
                             r["success_rate"] or 0.5, "hydra_genetic_memory",
                             fitness, r["times_applied"] or 0, 0,
                             json.dumps(["seeded", "hydra_legacy"]))
                        )
                        counts["hydra_genetic_memory"] += 1

            # ── session_intelligence ──
            if table_exists("session_intelligence"):
                rows = conn.execute(
                    """SELECT category, intelligence, source, actionable, created_at
                    FROM session_intelligence
                    WHERE is_duplicate = 0 AND intelligence IS NOT NULL
                    AND LENGTH(intelligence) > 10"""
                ).fetchall()
                batch = []
                for r in rows:
                    c_hash = _content_hash(r["intelligence"])
                    existing = conn.execute(
                        "SELECT 1 FROM omega_genetic_memory WHERE content_hash = ?",
                        (c_hash,)
                    ).fetchone()
                    if not existing:
                        mid = _generate_memory_id("session_intelligence", r["category"] or "general")
                        fitness = 0.8 if r["actionable"] else 0.4
                        batch.append((
                            mid, "session_intelligence", r["category"] or "general",
                            r["intelligence"], c_hash,
                            0.7, r["source"] or "session_intelligence",
                            fitness, 0, 0, json.dumps(["seeded", "session_intel"])
                        ))
                if batch:
                    conn.executemany(
                        """INSERT OR IGNORE INTO omega_genetic_memory
                        (memory_id, memory_type, topic, content, content_hash,
                         confidence, source, fitness_score, times_used,
                         is_verified, tags)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        batch
                    )
                    counts["session_intelligence"] = len(batch)

            # ── critical_facts ──
            if table_exists("critical_facts"):
                rows = conn.execute(
                    """SELECT fact_type, fact_text, source, verified_by, lane, created_at
                    FROM critical_facts
                    WHERE is_duplicate = 0 AND fact_text IS NOT NULL
                    AND LENGTH(fact_text) > 5"""
                ).fetchall()
                batch = []
                for r in rows:
                    c_hash = _content_hash(r["fact_text"])
                    existing = conn.execute(
                        "SELECT 1 FROM omega_genetic_memory WHERE content_hash = ?",
                        (c_hash,)
                    ).fetchone()
                    if not existing:
                        mid = _generate_memory_id("critical_fact", r["fact_type"] or "general")
                        batch.append((
                            mid, "critical_fact", r["fact_type"] or "general",
                            r["fact_text"], c_hash,
                            0.9, r["source"] or "critical_facts",
                            r["lane"],
                            1.5, 0, 1,  # verified = 1 (these are critical facts)
                            json.dumps(["seeded", "critical_fact", "verified"])
                        ))
                if batch:
                    conn.executemany(
                        """INSERT OR IGNORE INTO omega_genetic_memory
                        (memory_id, memory_type, topic, content, content_hash,
                         confidence, source, lane, fitness_score, times_used,
                         is_verified, tags)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        batch
                    )
                    counts["critical_facts"] = len(batch)

            conn.commit()
            total = sum(counts.values())
            logger.info("Seeded %d memories from legacy tables: %s", total, counts)
            return counts

        except sqlite3.Error as e:
            logger.error("Failed to seed from existing: %s", e)
            conn.rollback()
            return counts
        finally:
            conn.close()

    # ── Event Bus Integration ─────────────────────────────────────────────

    def handle_event(self, event_type: str, payload: dict, event: Any = None) -> None:
        """Event bus handler — processes relevant events and writes memories.

        Subscribes to:
          evidence.*      → evidence_insight memories
          filing.*        → filing_outcome memories
          adversary.*     → adversary_behavior memories
          judicial.*      → judicial_prediction memories
          self.improved   → strategy_result memories
          authority.*     → authority_discovery memories
          knowledge.gap   → error_pattern memories (gaps are failures to find)
        """
        try:
            category = event_type.split(".")[0] if "." in event_type else event_type

            type_map = {
                "evidence": "evidence_insight",
                "filing": "filing_outcome",
                "adversary": "adversary_behavior",
                "judicial": "judicial_prediction",
                "self": "strategy_result",
                "authority": "authority_discovery",
                "knowledge": "error_pattern",
            }

            memory_type = type_map.get(category)
            if not memory_type:
                return

            topic = payload.get("topic", event_type)
            content = payload.get("content") or payload.get("description") or json.dumps(payload)
            confidence = float(payload.get("confidence", 0.7))
            lane = payload.get("lane")
            source = payload.get("source", f"event_bus:{event_type}")

            self.write_memory(
                memory_type=memory_type,
                topic=topic,
                content=content,
                confidence=confidence,
                source=source,
                lane=lane,
                tags=[f"event:{event_type}", "auto_captured"],
            )

        except (KeyError, TypeError, ValueError) as e:
            logger.warning("GeneticMemory event handler error for %s: %s", event_type, e)

    def register_with_event_bus(self, event_bus) -> None:
        """Register this memory engine as a subscriber on the event bus.

        Subscribes to all relevant event patterns for memory capture.
        """
        patterns = [
            "evidence.*",
            "filing.*",
            "adversary.*",
            "judicial.*",
            "self.improved",
            "authority.*",
            "knowledge.gap",
        ]
        for pattern in patterns:
            event_bus.subscribe(
                pattern=pattern,
                handler_fn=self.handle_event,
                subscriber_name="genetic_memory",
                priority=9,  # Low priority — observe, don't block
            )
        logger.info("GeneticMemory registered with EventBus for %d patterns", len(patterns))

    # ── Search ────────────────────────────────────────────────────────────

    def search(self, query: str, limit: int = 20) -> list[dict]:
        """Full-text search across memory content and topics.

        Uses LIKE with sanitized query (FTS5-safe per Rule 15).
        """
        safe_query = re.sub(r'[^\w\s]', ' ', query).strip()
        if not safe_query:
            return []

        conn = _connect(self._db_path)
        try:
            terms = safe_query.split()
            conditions = []
            params = []
            for term in terms[:5]:  # Max 5 terms to prevent explosion
                conditions.append("(content LIKE ? OR topic LIKE ?)")
                params.extend([f"%{term}%", f"%{term}%"])

            if not conditions:
                return []

            where = " AND ".join(conditions)
            params.append(limit)

            rows = conn.execute(
                f"""SELECT memory_id, memory_type, topic, content, confidence,
                           source, lane, fitness_score, times_used, generation,
                           is_verified, created_at
                FROM omega_genetic_memory
                WHERE {where}
                ORDER BY fitness_score DESC, times_used DESC
                LIMIT ?""",
                params
            ).fetchall()
            return [dict(r) for r in rows]

        except sqlite3.Error as e:
            logger.error("Failed to search memories: %s", e)
            return []
        finally:
            conn.close()

    # ── Lineage Trace ─────────────────────────────────────────────────────

    def trace_lineage(self, memory_id: str) -> list[dict]:
        """Trace the evolutionary lineage of a memory back to its root ancestor."""
        conn = _connect(self._db_path)
        try:
            lineage = []
            current_id = memory_id
            visited = set()

            while current_id and current_id not in visited:
                visited.add(current_id)
                row = conn.execute(
                    """SELECT memory_id, memory_type, topic, content, fitness_score,
                              generation, parent_memory_id, created_at
                    FROM omega_genetic_memory
                    WHERE memory_id = ?""",
                    (current_id,)
                ).fetchone()

                if not row:
                    # Check archive
                    row = conn.execute(
                        """SELECT memory_id, memory_type, topic, content, fitness_score,
                                  generation, parent_memory_id, created_at
                        FROM omega_genetic_memory_archive
                        WHERE memory_id = ?""",
                        (current_id,)
                    ).fetchone()

                if row:
                    lineage.append(dict(row))
                    current_id = row["parent_memory_id"]
                else:
                    break

            return lineage

        except sqlite3.Error as e:
            logger.error("Failed to trace lineage: %s", e)
            return []
        finally:
            conn.close()

    # ── Representation ────────────────────────────────────────────────────

    def __repr__(self) -> str:
        stats = self.get_stats()
        return (
            f"GeneticMemory(active={stats.get('total_active', 0)}, "
            f"archived={stats.get('total_archived', 0)}, "
            f"avg_fitness={stats.get('avg_fitness', 0):.3f}, "
            f"types={stats.get('type_diversity', 0)})"
        )
