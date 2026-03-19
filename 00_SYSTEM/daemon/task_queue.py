"""
SQLite WAL Task Queue for LitigationOS Daemon.
High-performance, crash-safe, concurrent producer/consumer queue.

Features:
- WAL mode for concurrent reads + single writer
- Priority levels: CRITICAL > HIGH > NORMAL > LOW
- Dead letter queue after max_retries failures
- Metrics tracking (enqueue rate, process rate, error rate)
- Crash recovery: in-progress tasks reset to queued on startup
"""
import json
import sqlite3
import sys
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Optional

from .models import TaskItem, TaskPriority, TaskResult, TaskStatus

PRIORITY_ORDER = {
    TaskPriority.CRITICAL: 0,
    TaskPriority.HIGH: 1,
    TaskPriority.NORMAL: 2,
    TaskPriority.LOW: 3,
}

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS task_queue (
    id TEXT PRIMARY KEY,
    task_type TEXT NOT NULL,
    payload TEXT NOT NULL DEFAULT '{}',
    priority INTEGER NOT NULL DEFAULT 2,
    status TEXT NOT NULL DEFAULT 'queued',
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    error TEXT,
    retries INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 3,
    source TEXT NOT NULL DEFAULT 'daemon',
    worker_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_tq_status_priority ON task_queue(status, priority, created_at);
CREATE INDEX IF NOT EXISTS idx_tq_type ON task_queue(task_type);

CREATE TABLE IF NOT EXISTS task_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_type TEXT NOT NULL,
    task_type TEXT,
    value REAL NOT NULL,
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_tm_type_ts ON task_metrics(metric_type, timestamp);

CREATE TABLE IF NOT EXISTS daemon_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL,
    logger TEXT NOT NULL DEFAULT 'daemon',
    message TEXT NOT NULL,
    context TEXT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_dl_level_ts ON daemon_logs(level, timestamp);
"""


class TaskQueue:
    """SQLite WAL-backed task queue with priority and dead letter support."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=60)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("PRAGMA cache_size=-32000")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def _conn(self):
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        """Initialize schema and recover crashed tasks."""
        with self._conn() as conn:
            conn.executescript(SCHEMA_SQL)
            recovered = conn.execute(
                "UPDATE task_queue SET status = 'queued', worker_id = NULL "
                "WHERE status = 'running'"
            ).rowcount
            if recovered > 0:
                conn.execute(
                    "INSERT INTO daemon_logs (level, message, context) VALUES (?, ?, ?)",
                    ("WARNING", f"Recovered {recovered} crashed tasks",
                     json.dumps({"recovered_count": recovered}))
                )

    def enqueue(self, task_type: str, payload: dict = None,
                priority: TaskPriority = TaskPriority.NORMAL,
                source: str = "daemon", max_retries: int = 3) -> str:
        """Add a task to the queue. Returns task ID."""
        task_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        pri_num = PRIORITY_ORDER.get(priority, 2)

        with self._conn() as conn:
            conn.execute(
                "INSERT INTO task_queue (id, task_type, payload, priority, status, "
                "created_at, retries, max_retries, source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (task_id, task_type, json.dumps(payload or {}), pri_num,
                 TaskStatus.QUEUED.value, now, 0, max_retries, source)
            )
            conn.execute(
                "INSERT INTO task_metrics (metric_type, task_type, value) VALUES (?, ?, ?)",
                ("enqueue", task_type, 1.0)
            )
        return task_id

    def dequeue(self, worker_id: str = "default") -> Optional[TaskItem]:
        """Dequeue the highest-priority oldest task. Returns None if empty."""
        with self._lock:
            with self._conn() as conn:
                row = conn.execute(
                    "SELECT * FROM task_queue WHERE status = 'queued' "
                    "ORDER BY priority ASC, created_at ASC LIMIT 1"
                ).fetchone()

                if row is None:
                    return None

                now = datetime.utcnow().isoformat()
                conn.execute(
                    "UPDATE task_queue SET status = 'running', started_at = ?, "
                    "worker_id = ? WHERE id = ?",
                    (now, worker_id, row["id"])
                )

                return TaskItem(
                    id=row["id"],
                    task_type=row["task_type"],
                    payload=json.loads(row["payload"]),
                    priority=list(PRIORITY_ORDER.keys())[row["priority"]],
                    status=TaskStatus.RUNNING,
                    created_at=datetime.fromisoformat(row["created_at"]),
                    started_at=datetime.fromisoformat(now),
                    retries=row["retries"],
                    max_retries=row["max_retries"],
                    source=row["source"],
                )

    def complete(self, task_id: str, result: TaskResult):
        """Mark a task as completed or move to retry/dead letter."""
        now = datetime.utcnow().isoformat()

        with self._conn() as conn:
            if result.success:
                conn.execute(
                    "UPDATE task_queue SET status = 'completed', completed_at = ? WHERE id = ?",
                    (now, task_id)
                )
                conn.execute(
                    "INSERT INTO task_metrics (metric_type, task_type, value) VALUES (?, ?, ?)",
                    ("complete", result.output.get("task_type", ""), result.duration_sec)
                )
            else:
                row = conn.execute(
                    "SELECT retries, max_retries, task_type FROM task_queue WHERE id = ?",
                    (task_id,)
                ).fetchone()

                if row and row["retries"] + 1 >= row["max_retries"]:
                    conn.execute(
                        "UPDATE task_queue SET status = 'dead_letter', completed_at = ?, "
                        "error = ?, retries = retries + 1 WHERE id = ?",
                        (now, result.error, task_id)
                    )
                    conn.execute(
                        "INSERT INTO task_metrics (metric_type, task_type, value) VALUES (?, ?, ?)",
                        ("dead_letter", row["task_type"], 1.0)
                    )
                else:
                    conn.execute(
                        "UPDATE task_queue SET status = 'queued', error = ?, "
                        "retries = retries + 1, started_at = NULL, worker_id = NULL WHERE id = ?",
                        (result.error, task_id)
                    )
                    conn.execute(
                        "INSERT INTO task_metrics (metric_type, task_type, value) VALUES (?, ?, ?)",
                        ("retry", row["task_type"] if row else "", 1.0)
                    )

    def depth(self) -> dict[str, int]:
        """Get queue depth by status."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) as cnt FROM task_queue GROUP BY status"
            ).fetchall()
            return {row["status"]: row["cnt"] for row in rows}

    def purge_completed(self, older_than_hours: int = 24) -> int:
        """Remove completed tasks older than N hours."""
        with self._conn() as conn:
            return conn.execute(
                "DELETE FROM task_queue WHERE status = 'completed' "
                "AND completed_at < datetime('now', ?)",
                (f"-{older_than_hours} hours",)
            ).rowcount

    def get_metrics(self, hours: int = 24) -> dict:
        """Get task metrics for the last N hours."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT metric_type, COUNT(*) as cnt, AVG(value) as avg_val "
                "FROM task_metrics WHERE timestamp > datetime('now', ?) "
                "GROUP BY metric_type",
                (f"-{hours} hours",)
            ).fetchall()
            return {row["metric_type"]: {"count": row["cnt"], "avg": row["avg_val"]}
                    for row in rows}
