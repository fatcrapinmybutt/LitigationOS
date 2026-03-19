"""
persistent_memory.py — Persistent Memory Manager for MANBEARPIG LitigationOS

Cross-session persistent memory system backed by SQLite.
Stores learned patterns, query history, case insights, user preferences,
and engine performance metrics. Auto-loads on startup.

Critical infrastructure: the BRAIN of persistent state.
"""

import sqlite3
import json
import os
import time
from datetime import datetime, timedelta, timezone
from collections import defaultdict

DEFAULT_DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"


class PersistentMemory:
    """Cross-session persistent memory backed by litigation_context.db."""

    VALID_MEMORY_TYPES = (
        "insight", "pattern", "preference", "query_log",
        "performance", "learned_rule", "error_pattern",
    )

    def __init__(self, db_path=None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self._fast_cache = {}  # preferences and learned_rules loaded here
        self._init_tables()
        self.auto_load()

    # ------------------------------------------------------------------
    # Connection helper — one connection per operation, WAL mode
    # ------------------------------------------------------------------

    def _connect(self):
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        return conn

    # ------------------------------------------------------------------
    # Schema bootstrap
    # ------------------------------------------------------------------

    def _init_tables(self):
        try:
            conn = self._connect()
            cur = conn.cursor()
            cur.executescript("""
                CREATE TABLE IF NOT EXISTS memory_store (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    memory_type TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    confidence REAL DEFAULT 0.5,
                    access_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now')),
                    expires_at TEXT,
                    source TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_memory_type ON memory_store(memory_type);
                CREATE INDEX IF NOT EXISTS idx_memory_key ON memory_store(key);

                CREATE TABLE IF NOT EXISTS memory_associations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    memory_id_a INTEGER REFERENCES memory_store(id),
                    memory_id_b INTEGER REFERENCES memory_store(id),
                    association_type TEXT,
                    strength REAL DEFAULT 0.5,
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS engine_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    engine_name TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    recorded_at TEXT DEFAULT (datetime('now'))
                );
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[PersistentMemory] WARN: table init failed: {e}")

    # ------------------------------------------------------------------
    # store
    # ------------------------------------------------------------------

    def store(self, memory_type, key, value, confidence=0.5, source=None, expires_at=None):
        """Store a memory. Upserts if key already exists for the given type."""
        try:
            serialized = json.dumps(value) if not isinstance(value, str) else value
            # Validate JSON round-trip
            json.loads(serialized)
        except (TypeError, ValueError) as e:
            print(f"[PersistentMemory] WARN: value not JSON-serializable: {e}")
            serialized = json.dumps(str(value))

        try:
            conn = self._connect()
            cur = conn.cursor()
            # Check for existing entry
            cur.execute(
                "SELECT id, access_count FROM memory_store "
                "WHERE memory_type = ? AND key = ?",
                (memory_type, key),
            )
            row = cur.fetchone()
            now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

            if row:
                cur.execute(
                    "UPDATE memory_store SET value = ?, confidence = ?, "
                    "access_count = access_count + 1, updated_at = ?, "
                    "source = COALESCE(?, source), expires_at = COALESCE(?, expires_at) "
                    "WHERE id = ?",
                    (serialized, confidence, now, source, expires_at, row["id"]),
                )
                mem_id = row["id"]
            else:
                cur.execute(
                    "INSERT INTO memory_store "
                    "(memory_type, key, value, confidence, access_count, "
                    "created_at, updated_at, expires_at, source) "
                    "VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?)",
                    (memory_type, key, serialized, confidence, now, now,
                     expires_at, source),
                )
                mem_id = cur.lastrowid

            conn.commit()
            conn.close()

            # Update fast cache for critical types
            if memory_type in ("preference", "learned_rule"):
                self._fast_cache[f"{memory_type}:{key}"] = value

            return mem_id
        except Exception as e:
            print(f"[PersistentMemory] ERROR storing memory: {e}")
            return None

    # ------------------------------------------------------------------
    # recall
    # ------------------------------------------------------------------

    def recall(self, memory_type=None, key=None, min_confidence=0.0, limit=50):
        """Retrieve memories with optional filters. Bumps access_count."""
        try:
            conn = self._connect()
            cur = conn.cursor()

            clauses = ["confidence >= ?"]
            params = [min_confidence]

            if memory_type:
                clauses.append("memory_type = ?")
                params.append(memory_type)
            if key:
                clauses.append("key = ?")
                params.append(key)

            # Exclude expired
            clauses.append("(expires_at IS NULL OR expires_at > datetime('now'))")

            where = " AND ".join(clauses)
            query = (
                f"SELECT * FROM memory_store WHERE {where} "
                f"ORDER BY updated_at DESC LIMIT ?"
            )
            params.append(limit)
            cur.execute(query, params)
            rows = cur.fetchall()

            results = []
            ids = []
            for row in rows:
                d = dict(row)
                try:
                    d["value"] = json.loads(d["value"])
                except (json.JSONDecodeError, TypeError):
                    pass
                results.append(d)
                ids.append(d["id"])

            # Bump access counts
            if ids:
                placeholders = ",".join("?" * len(ids))
                cur.execute(
                    f"UPDATE memory_store SET access_count = access_count + 1 "
                    f"WHERE id IN ({placeholders})",
                    ids,
                )
                conn.commit()

            conn.close()
            return results
        except Exception as e:
            print(f"[PersistentMemory] ERROR recalling: {e}")
            return []

    # ------------------------------------------------------------------
    # forget
    # ------------------------------------------------------------------

    def forget(self, memory_id=None, memory_type=None, expired_only=False):
        """Remove memories by ID, type, or expiration."""
        try:
            conn = self._connect()
            cur = conn.cursor()
            deleted = 0

            if memory_id is not None:
                # Also clean up associations
                cur.execute(
                    "DELETE FROM memory_associations "
                    "WHERE memory_id_a = ? OR memory_id_b = ?",
                    (memory_id, memory_id),
                )
                cur.execute("DELETE FROM memory_store WHERE id = ?", (memory_id,))
                deleted = cur.rowcount
            elif expired_only:
                # Get ids first for association cleanup
                cur.execute(
                    "SELECT id FROM memory_store "
                    "WHERE expires_at IS NOT NULL AND expires_at <= datetime('now')"
                )
                expired_ids = [r["id"] for r in cur.fetchall()]
                if expired_ids:
                    ph = ",".join("?" * len(expired_ids))
                    cur.execute(
                        f"DELETE FROM memory_associations "
                        f"WHERE memory_id_a IN ({ph}) OR memory_id_b IN ({ph})",
                        expired_ids + expired_ids,
                    )
                    cur.execute(
                        f"DELETE FROM memory_store WHERE id IN ({ph})",
                        expired_ids,
                    )
                    deleted = cur.rowcount
            elif memory_type is not None:
                cur.execute(
                    "DELETE FROM memory_associations WHERE memory_id_a IN "
                    "(SELECT id FROM memory_store WHERE memory_type = ?) "
                    "OR memory_id_b IN "
                    "(SELECT id FROM memory_store WHERE memory_type = ?)",
                    (memory_type, memory_type),
                )
                cur.execute(
                    "DELETE FROM memory_store WHERE memory_type = ?",
                    (memory_type,),
                )
                deleted = cur.rowcount

            conn.commit()
            conn.close()
            return deleted
        except Exception as e:
            print(f"[PersistentMemory] ERROR forgetting: {e}")
            return 0

    # ------------------------------------------------------------------
    # associations
    # ------------------------------------------------------------------

    def associate(self, memory_id_a, memory_id_b, association_type, strength=0.5):
        """Create an association between two memories."""
        try:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO memory_associations "
                "(memory_id_a, memory_id_b, association_type, strength) "
                "VALUES (?, ?, ?, ?)",
                (memory_id_a, memory_id_b, association_type, strength),
            )
            assoc_id = cur.lastrowid
            conn.commit()
            conn.close()
            return assoc_id
        except Exception as e:
            print(f"[PersistentMemory] ERROR creating association: {e}")
            return None

    def get_associations(self, memory_id):
        """Get all memories associated with a given memory."""
        try:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute(
                "SELECT m.*, a.association_type, a.strength "
                "FROM memory_associations a "
                "JOIN memory_store m ON "
                "  (a.memory_id_b = m.id AND a.memory_id_a = ?) OR "
                "  (a.memory_id_a = m.id AND a.memory_id_b = ?) "
                "ORDER BY a.strength DESC",
                (memory_id, memory_id),
            )
            rows = cur.fetchall()
            results = []
            for row in rows:
                d = dict(row)
                try:
                    d["value"] = json.loads(d["value"])
                except (json.JSONDecodeError, TypeError):
                    pass
                results.append(d)
            conn.close()
            return results
        except Exception as e:
            print(f"[PersistentMemory] ERROR getting associations: {e}")
            return []

    # ------------------------------------------------------------------
    # query logging
    # ------------------------------------------------------------------

    def log_query(self, query_text, engine_used, response_quality=None, latency_ms=None):
        """Log a query for performance tracking."""
        payload = {
            "query": query_text,
            "engine": engine_used,
            "quality": response_quality,
            "latency_ms": latency_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        mem_id = self.store(
            memory_type="query_log",
            key=f"query_{int(time.time() * 1000)}",
            value=payload,
            confidence=response_quality if response_quality is not None else 0.5,
            source=engine_used,
        )
        # Also log latency metric if provided
        if latency_ms is not None:
            self.log_metric(engine_used, "latency_ms", latency_ms)
        return mem_id

    # ------------------------------------------------------------------
    # engine metrics
    # ------------------------------------------------------------------

    def log_metric(self, engine_name, metric_name, metric_value):
        """Log an engine performance metric."""
        try:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO engine_metrics (engine_name, metric_name, metric_value) "
                "VALUES (?, ?, ?)",
                (engine_name, metric_name, float(metric_value)),
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[PersistentMemory] ERROR logging metric: {e}")
            return False

    def get_engine_health(self):
        """Return health summary for all engines based on metrics."""
        try:
            conn = self._connect()
            cur = conn.cursor()

            # Aggregate metrics per engine
            cur.execute(
                "SELECT engine_name, metric_name, "
                "AVG(metric_value) as avg_val, "
                "COUNT(*) as cnt, "
                "MAX(recorded_at) as last_active "
                "FROM engine_metrics "
                "GROUP BY engine_name, metric_name"
            )
            rows = cur.fetchall()
            conn.close()

            engines = defaultdict(lambda: {
                "avg_latency_ms": None,
                "error_rate": None,
                "query_count": 0,
                "last_active": None,
                "metrics": {},
            })

            for row in rows:
                eng = engines[row["engine_name"]]
                eng["metrics"][row["metric_name"]] = {
                    "avg": row["avg_val"],
                    "count": row["cnt"],
                }
                if row["metric_name"] == "latency_ms":
                    eng["avg_latency_ms"] = round(row["avg_val"], 2)
                if row["metric_name"] == "error":
                    eng["error_rate"] = round(row["avg_val"], 4)
                eng["query_count"] += row["cnt"]
                if eng["last_active"] is None or row["last_active"] > eng["last_active"]:
                    eng["last_active"] = row["last_active"]

            return dict(engines)
        except Exception as e:
            print(f"[PersistentMemory] ERROR getting engine health: {e}")
            return {}

    # ------------------------------------------------------------------
    # insights
    # ------------------------------------------------------------------

    def get_insights(self, topic=None, min_confidence=0.5):
        """Get learned insights, optionally filtered by topic keyword."""
        try:
            conn = self._connect()
            cur = conn.cursor()

            if topic:
                cur.execute(
                    "SELECT * FROM memory_store "
                    "WHERE memory_type = 'insight' AND confidence >= ? "
                    "AND (key LIKE ? OR value LIKE ?) "
                    "ORDER BY confidence DESC, updated_at DESC",
                    (min_confidence, f"%{topic}%", f"%{topic}%"),
                )
            else:
                cur.execute(
                    "SELECT * FROM memory_store "
                    "WHERE memory_type = 'insight' AND confidence >= ? "
                    "ORDER BY confidence DESC, updated_at DESC",
                    (min_confidence,),
                )

            rows = cur.fetchall()
            results = []
            for row in rows:
                d = dict(row)
                try:
                    d["value"] = json.loads(d["value"])
                except (json.JSONDecodeError, TypeError):
                    pass
                results.append(d)
            conn.close()
            return results
        except Exception as e:
            print(f"[PersistentMemory] ERROR getting insights: {e}")
            return []

    # ------------------------------------------------------------------
    # pattern learning
    # ------------------------------------------------------------------

    def learn_pattern(self, pattern_key, pattern_data, confidence, source):
        """Store a learned pattern (e.g., 'judge always rules X on Y motions')."""
        return self.store(
            memory_type="pattern",
            key=pattern_key,
            value=pattern_data,
            confidence=confidence,
            source=source,
        )

    def get_learned_patterns(self, min_confidence=0.5):
        """Retrieve all learned patterns above confidence threshold."""
        return self.recall(memory_type="pattern", min_confidence=min_confidence)

    # ------------------------------------------------------------------
    # maintenance
    # ------------------------------------------------------------------

    def prune(self, max_age_days=90, min_access_count=0):
        """Remove old, rarely-accessed memories. Keep high-confidence ones (>=0.9)."""
        try:
            conn = self._connect()
            cur = conn.cursor()
            cutoff = (datetime.now(timezone.utc) - timedelta(days=max_age_days)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            # Find candidates: old + rarely accessed + not high confidence
            cur.execute(
                "SELECT id FROM memory_store "
                "WHERE updated_at < ? AND access_count <= ? AND confidence < 0.9",
                (cutoff, min_access_count),
            )
            ids = [r["id"] for r in cur.fetchall()]

            if ids:
                ph = ",".join("?" * len(ids))
                cur.execute(
                    f"DELETE FROM memory_associations "
                    f"WHERE memory_id_a IN ({ph}) OR memory_id_b IN ({ph})",
                    ids + ids,
                )
                cur.execute(
                    f"DELETE FROM memory_store WHERE id IN ({ph})", ids
                )

            pruned = len(ids)
            conn.commit()
            conn.close()
            return pruned
        except Exception as e:
            print(f"[PersistentMemory] ERROR pruning: {e}")
            return 0

    # ------------------------------------------------------------------
    # stats
    # ------------------------------------------------------------------

    def get_memory_stats(self):
        """Return summary statistics about the memory store."""
        try:
            conn = self._connect()
            cur = conn.cursor()

            cur.execute("SELECT COUNT(*) as total FROM memory_store")
            total = cur.fetchone()["total"]

            cur.execute(
                "SELECT memory_type, COUNT(*) as cnt "
                "FROM memory_store GROUP BY memory_type"
            )
            by_type = {r["memory_type"]: r["cnt"] for r in cur.fetchall()}

            cur.execute("SELECT AVG(confidence) as avg_conf FROM memory_store")
            avg_conf_row = cur.fetchone()
            avg_confidence = round(avg_conf_row["avg_conf"], 4) if avg_conf_row["avg_conf"] else 0.0

            cur.execute(
                "SELECT MIN(created_at) as oldest, MAX(created_at) as newest "
                "FROM memory_store"
            )
            dates = cur.fetchone()

            cur.execute(
                "SELECT key, access_count FROM memory_store "
                "ORDER BY access_count DESC LIMIT 1"
            )
            most = cur.fetchone()
            most_accessed = (
                {"key": most["key"], "access_count": most["access_count"]}
                if most else None
            )

            conn.close()
            return {
                "total_memories": total,
                "by_type": by_type,
                "avg_confidence": avg_confidence,
                "oldest": dates["oldest"] if dates else None,
                "newest": dates["newest"] if dates else None,
                "most_accessed": most_accessed,
            }
        except Exception as e:
            print(f"[PersistentMemory] ERROR getting stats: {e}")
            return {
                "total_memories": 0, "by_type": {}, "avg_confidence": 0.0,
                "oldest": None, "newest": None, "most_accessed": None,
            }

    # ------------------------------------------------------------------
    # export / import
    # ------------------------------------------------------------------

    def export_memory(self, filepath=None):
        """Export all memories as a JSON dict. Optionally write to file."""
        try:
            conn = self._connect()
            cur = conn.cursor()

            cur.execute("SELECT * FROM memory_store ORDER BY id")
            memories = []
            for row in cur.fetchall():
                d = dict(row)
                try:
                    d["value"] = json.loads(d["value"])
                except (json.JSONDecodeError, TypeError):
                    pass
                memories.append(d)

            cur.execute("SELECT * FROM memory_associations ORDER BY id")
            associations = [dict(r) for r in cur.fetchall()]

            cur.execute("SELECT * FROM engine_metrics ORDER BY id")
            metrics = [dict(r) for r in cur.fetchall()]

            conn.close()

            data = {
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "memories": memories,
                "associations": associations,
                "engine_metrics": metrics,
            }

            if filepath:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, default=str)

            return data
        except Exception as e:
            print(f"[PersistentMemory] ERROR exporting: {e}")
            return {}

    def import_memory(self, filepath_or_data):
        """Import memories from JSON file path or dict."""
        try:
            if isinstance(filepath_or_data, str):
                with open(filepath_or_data, "r", encoding="utf-8") as f:
                    data = json.load(f)
            elif isinstance(filepath_or_data, dict):
                data = filepath_or_data
            else:
                print("[PersistentMemory] WARN: invalid import source")
                return 0

            imported = 0
            for mem in data.get("memories", []):
                val = mem.get("value", "")
                if not isinstance(val, str):
                    val = json.dumps(val)
                self.store(
                    memory_type=mem.get("memory_type", "insight"),
                    key=mem.get("key", "imported"),
                    value=val,
                    confidence=mem.get("confidence", 0.5),
                    source=mem.get("source"),
                    expires_at=mem.get("expires_at"),
                )
                imported += 1

            # Import associations (best-effort, IDs may differ)
            conn = self._connect()
            cur = conn.cursor()
            for assoc in data.get("associations", []):
                try:
                    cur.execute(
                        "INSERT INTO memory_associations "
                        "(memory_id_a, memory_id_b, association_type, strength) "
                        "VALUES (?, ?, ?, ?)",
                        (assoc["memory_id_a"], assoc["memory_id_b"],
                         assoc.get("association_type"), assoc.get("strength", 0.5)),
                    )
                except Exception:
                    pass  # Skip broken refs silently

            for met in data.get("engine_metrics", []):
                try:
                    cur.execute(
                        "INSERT INTO engine_metrics "
                        "(engine_name, metric_name, metric_value) "
                        "VALUES (?, ?, ?)",
                        (met["engine_name"], met["metric_name"], met["metric_value"]),
                    )
                except Exception:
                    pass

            conn.commit()
            conn.close()
            return imported
        except Exception as e:
            print(f"[PersistentMemory] ERROR importing: {e}")
            return 0

    # ------------------------------------------------------------------
    # auto_load — fast cache for critical memories
    # ------------------------------------------------------------------

    def auto_load(self):
        """Load preferences and learned rules into fast-access cache."""
        try:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute(
                "SELECT memory_type, key, value FROM memory_store "
                "WHERE memory_type IN ('preference', 'learned_rule') "
                "AND (expires_at IS NULL OR expires_at > datetime('now'))"
            )
            for row in cur.fetchall():
                cache_key = f"{row['memory_type']}:{row['key']}"
                try:
                    self._fast_cache[cache_key] = json.loads(row["value"])
                except (json.JSONDecodeError, TypeError):
                    self._fast_cache[cache_key] = row["value"]
            conn.close()
        except Exception as e:
            print(f"[PersistentMemory] WARN: auto_load failed: {e}")

    def get_cached(self, memory_type, key):
        """Quick lookup from the in-memory fast cache."""
        return self._fast_cache.get(f"{memory_type}:{key}")

    # ------------------------------------------------------------------
    # repr
    # ------------------------------------------------------------------

    def __repr__(self):
        stats = self.get_memory_stats()
        return (
            f"<PersistentMemory db={self.db_path} "
            f"memories={stats['total_memories']} "
            f"cached={len(self._fast_cache)}>"
        )


# ======================================================================
# __main__ — smoke test
# ======================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  MANBEARPIG Persistent Memory — Smoke Test")
    print("=" * 60)

    pm = PersistentMemory()
    print(f"\nInitialized: {pm}")

    # Store test memories
    id1 = pm.store("insight", "custody_pattern",
                    {"finding": "MCL 722.23(j) violations detected in 3 hearings",
                     "lane": "A"},
                    confidence=0.85, source="contradiction_discovery")
    print(f"\n[+] Stored insight (id={id1})")

    id2 = pm.store("preference", "output_format",
                    {"style": "court_ready", "citations": True},
                    confidence=1.0, source="user")
    print(f"[+] Stored preference (id={id2})")

    id3 = pm.learn_pattern(
        "mcneill_motion_denial",
        {"pattern": "Judge McNeill denies motions re: parenting time modification",
         "sample_size": 5, "consistency": 0.8},
        confidence=0.75, source="docket_analyzer",
    )
    print(f"[+] Learned pattern (id={id3})")

    id4 = pm.store("learned_rule", "appeal_deadline",
                    {"rule": "MCR 7.204(A)(1)", "days": 21,
                     "note": "Claim of appeal within 21 days of entry"},
                    confidence=1.0, source="authority_pagerank")
    print(f"[+] Stored learned rule (id={id4})")

    # Associate insight with pattern
    if id1 and id3:
        assoc = pm.associate(id1, id3, "supports", strength=0.7)
        print(f"[+] Associated insight <-> pattern (assoc_id={assoc})")

    # Log query
    qid = pm.log_query(
        "What are the best interest factors?",
        engine_used="bm25_engine",
        response_quality=0.9,
        latency_ms=42.5,
    )
    print(f"[+] Logged query (id={qid})")

    # Log metrics
    pm.log_metric("bm25_engine", "latency_ms", 42.5)
    pm.log_metric("bm25_engine", "latency_ms", 38.1)
    pm.log_metric("semantic_engine", "latency_ms", 120.3)
    pm.log_metric("semantic_engine", "error", 0.02)
    print("[+] Logged engine metrics")

    # Recall
    print("\n--- Recall insights ---")
    insights = pm.get_insights(min_confidence=0.5)
    for ins in insights:
        print(f"  [{ins['confidence']:.2f}] {ins['key']}: {ins['value']}")

    print("\n--- Learned patterns ---")
    patterns = pm.get_learned_patterns(min_confidence=0.5)
    for p in patterns:
        print(f"  [{p['confidence']:.2f}] {p['key']}: {p['value']}")

    print("\n--- Associations for insight ---")
    if id1:
        assocs = pm.get_associations(id1)
        for a in assocs:
            print(f"  [{a['association_type']}|{a['strength']:.1f}] {a['key']}")

    print("\n--- Engine health ---")
    health = pm.get_engine_health()
    for eng, info in health.items():
        print(f"  {eng}: latency={info['avg_latency_ms']}ms, "
              f"queries={info['query_count']}, last={info['last_active']}")

    print("\n--- Fast cache ---")
    for k, v in pm._fast_cache.items():
        print(f"  {k} = {v}")

    print("\n--- Memory stats ---")
    stats = pm.get_memory_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")

    print(f"\n{pm}")
    print("\n[OK] Smoke test complete.")
