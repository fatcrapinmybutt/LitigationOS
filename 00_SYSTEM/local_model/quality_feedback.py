#!/usr/bin/env python3
"""
APEX Quality Feedback — Continuous quality monitoring and alerting.

Tracks quality scores by task type, model, and time period.
Alerts when quality drops below threshold (70/100 or 3.5/5).
Integrates with ``learning_loop.py`` for persistence and with
``apex_quality_gate.py`` for validation data.

Thread-safe, UTF-8 safe, never crashes.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import sys
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Shadow LLM gate
# ---------------------------------------------------------------------------
APEX_LLM_ENABLED: bool = (
    os.environ.get("APEX_LLM_ENABLED", "false").lower() == "true"
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("apex.quality_feedback")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_HERE = Path(__file__).parent

# ---------------------------------------------------------------------------
# Mandatory DB PRAGMAs
# ---------------------------------------------------------------------------
_DB_PRAGMAS: str = """
PRAGMA busy_timeout  = 60000;
PRAGMA journal_mode  = WAL;
PRAGMA cache_size    = -32000;
PRAGMA temp_store    = MEMORY;
PRAGMA synchronous   = NORMAL;
"""

# ---------------------------------------------------------------------------
# Schema (stored in learning_metrics.db alongside LearningLoop tables)
# ---------------------------------------------------------------------------
_SCHEMA: str = """
CREATE TABLE IF NOT EXISTS quality_scores (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TEXT    DEFAULT (datetime('now')),
    task_type       TEXT    NOT NULL,
    model           TEXT,
    score           REAL    NOT NULL,
    details_json    TEXT,
    alert_fired     INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS quality_alerts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TEXT    DEFAULT (datetime('now')),
    task_type       TEXT,
    model           TEXT,
    score           REAL,
    threshold       REAL,
    message         TEXT,
    acknowledged    INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_qs_task    ON quality_scores(task_type);
CREATE INDEX IF NOT EXISTS idx_qs_ts      ON quality_scores(timestamp);
CREATE INDEX IF NOT EXISTS idx_qs_model   ON quality_scores(model);
CREATE INDEX IF NOT EXISTS idx_qa_ack     ON quality_alerts(acknowledged);
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _safe_connect(db_path: Path) -> Optional[sqlite3.Connection]:
    """Open SQLite with mandatory PRAGMAs.  Returns None on failure."""
    try:
        conn = sqlite3.connect(str(db_path), timeout=60, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.executescript(_DB_PRAGMAS)
        return conn
    except Exception as exc:  # noqa: BLE001
        logger.warning("DB open failed %s: %s", db_path, exc)
        return None


def _ensure_schema(conn: sqlite3.Connection) -> None:
    try:
        conn.executescript(_SCHEMA)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Schema init: %s", exc)


# ---------------------------------------------------------------------------
# QualityFeedback
# ---------------------------------------------------------------------------
class QualityFeedback:
    """Continuous quality monitoring with alerting.

    Stores data in the same ``learning_metrics.db`` used by ``LearningLoop``
    so both systems share a single WAL-mode file.
    """

    ALERT_THRESHOLD: float = 70.0  # score out of 100
    DB_PATH: Path = _HERE / "learning_metrics.db"

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or self.DB_PATH
        self._lock = threading.Lock()
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    # ------------------------------------------------------------------
    # DB lifecycle
    # ------------------------------------------------------------------
    def _init_db(self) -> None:
        try:
            self._conn = _safe_connect(self._db_path)
            if self._conn:
                _ensure_schema(self._conn)
        except Exception as exc:  # noqa: BLE001
            logger.warning("QualityFeedback init: %s", exc)

    def _get_conn(self) -> Optional[sqlite3.Connection]:
        if self._conn is None:
            self._init_db()
        return self._conn

    # ------------------------------------------------------------------
    # Record a quality score
    # ------------------------------------------------------------------
    def record_score(
        self,
        task_type: str,
        model: str,
        score: float,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Record a quality score.  Auto-fires alert if below threshold."""
        try:
            conn = self._get_conn()
            if conn is None:
                return {"status": "error", "error": "no database connection"}

            details_json = json.dumps(details or {}, ensure_ascii=False)
            alert_fired = 1 if score < self.ALERT_THRESHOLD else 0

            with self._lock:
                conn.execute(
                    "INSERT INTO quality_scores (task_type, model, score, details_json, alert_fired) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (task_type, model, score, details_json, alert_fired),
                )

                if alert_fired:
                    msg = (
                        f"Quality alert: {task_type}/{model} scored {score:.1f} "
                        f"(threshold {self.ALERT_THRESHOLD})"
                    )
                    conn.execute(
                        "INSERT INTO quality_alerts (task_type, model, score, threshold, message) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (task_type, model, score, self.ALERT_THRESHOLD, msg),
                    )
                    logger.warning(msg)

                conn.commit()

            return {
                "status": "ok",
                "score": score,
                "alert_fired": bool(alert_fired),
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning("record_score: %s", exc)
            return {"status": "error", "error": str(exc)}

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------
    def get_dashboard(self) -> Dict[str, Any]:
        """Quality dashboard: averages by type/model/period, trends, alerts."""
        try:
            conn = self._get_conn()
            if conn is None:
                return {"status": "error", "error": "no database connection"}

            # Aggregate stats in one query
            overall = conn.execute(
                """
                SELECT
                    (SELECT COUNT(*)           FROM quality_scores) AS total,
                    (SELECT AVG(score)         FROM quality_scores) AS avg_score,
                    (SELECT MIN(score)         FROM quality_scores) AS min_score,
                    (SELECT MAX(score)         FROM quality_scores) AS max_score,
                    (SELECT COUNT(*)           FROM quality_alerts WHERE acknowledged = 0) AS open_alerts
                """
            ).fetchone()

            # By task type
            by_type = conn.execute(
                "SELECT task_type, AVG(score) AS avg, COUNT(*) AS n, MIN(score) AS low "
                "FROM quality_scores GROUP BY task_type ORDER BY avg DESC"
            ).fetchall()

            # By model
            by_model = conn.execute(
                "SELECT model, AVG(score) AS avg, COUNT(*) AS n "
                "FROM quality_scores WHERE model IS NOT NULL "
                "GROUP BY model ORDER BY avg DESC"
            ).fetchall()

            # Recent 7 days trend
            trend = conn.execute(
                "SELECT date(timestamp) AS day, AVG(score) AS avg, COUNT(*) AS n "
                "FROM quality_scores WHERE timestamp >= datetime('now', '-7 days') "
                "GROUP BY day ORDER BY day"
            ).fetchall()

            # Open alerts
            alerts = self.check_alerts()

            return {
                "status": "ok",
                "total_scores": overall["total"] or 0,
                "avg_score": round(overall["avg_score"] or 0, 2),
                "min_score": round(overall["min_score"] or 0, 2),
                "max_score": round(overall["max_score"] or 0, 2),
                "open_alerts": overall["open_alerts"] or 0,
                "by_task_type": [
                    {"task_type": r["task_type"], "avg": round(r["avg"], 2), "count": r["n"], "lowest": round(r["low"], 2)}
                    for r in by_type
                ],
                "by_model": [
                    {"model": r["model"], "avg": round(r["avg"], 2), "count": r["n"]}
                    for r in by_model
                ],
                "trend_7d": [
                    {"date": r["day"], "avg": round(r["avg"], 2), "count": r["n"]}
                    for r in trend
                ],
                "alerts": alerts,
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning("get_dashboard: %s", exc)
            return {"status": "error", "error": str(exc)}

    # ------------------------------------------------------------------
    # Alerts
    # ------------------------------------------------------------------
    def check_alerts(self) -> List[Dict[str, Any]]:
        """Return un-acknowledged quality alerts."""
        alerts: list[dict[str, Any]] = []
        try:
            conn = self._get_conn()
            if conn is None:
                return alerts

            rows = conn.execute(
                "SELECT id, timestamp, task_type, model, score, threshold, message "
                "FROM quality_alerts WHERE acknowledged = 0 "
                "ORDER BY timestamp DESC LIMIT 50"
            ).fetchall()

            alerts = [dict(r) for r in rows]

            # Also check for trend-based alerts: avg of last 5 scores
            recent_avgs = conn.execute(
                """
                SELECT task_type, model, AVG(score) AS recent_avg, COUNT(*) AS n
                FROM (
                    SELECT task_type, model, score
                    FROM quality_scores
                    ORDER BY timestamp DESC
                    LIMIT 10
                )
                GROUP BY task_type, model
                HAVING recent_avg < ?
                """,
                (self.ALERT_THRESHOLD,),
            ).fetchall()

            for r in recent_avgs:
                alerts.append({
                    "type": "trend_alert",
                    "task_type": r["task_type"],
                    "model": r["model"],
                    "recent_avg": round(r["recent_avg"], 2),
                    "message": (
                        f"Recent avg for {r['task_type']}/{r['model']} is "
                        f"{r['recent_avg']:.1f} (below {self.ALERT_THRESHOLD})"
                    ),
                })
        except Exception as exc:  # noqa: BLE001
            logger.debug("check_alerts: %s", exc)
        return alerts

    def acknowledge_alert(self, alert_id: int) -> Dict[str, Any]:
        """Mark an alert as acknowledged."""
        try:
            conn = self._get_conn()
            if conn is None:
                return {"status": "error", "error": "no database connection"}
            with self._lock:
                conn.execute(
                    "UPDATE quality_alerts SET acknowledged = 1 WHERE id = ?",
                    (alert_id,),
                )
                conn.commit()
            return {"status": "ok", "alert_id": alert_id}
        except Exception as exc:  # noqa: BLE001
            return {"status": "error", "error": str(exc)}

    def acknowledge_all(self) -> Dict[str, Any]:
        """Acknowledge all open alerts."""
        try:
            conn = self._get_conn()
            if conn is None:
                return {"status": "error", "error": "no database connection"}
            with self._lock:
                cur = conn.execute(
                    "UPDATE quality_alerts SET acknowledged = 1 WHERE acknowledged = 0"
                )
                conn.commit()
            return {"status": "ok", "acknowledged": cur.rowcount}
        except Exception as exc:  # noqa: BLE001
            return {"status": "error", "error": str(exc)}

    # ------------------------------------------------------------------
    # Model rankings
    # ------------------------------------------------------------------
    def get_model_rankings(self) -> List[Dict[str, Any]]:
        """Rank models by average quality score across all task types."""
        rankings: list[dict[str, Any]] = []
        try:
            conn = self._get_conn()
            if conn is None:
                return rankings

            rows = conn.execute(
                """
                SELECT model,
                       AVG(score) AS avg_score,
                       COUNT(*) AS total,
                       SUM(CASE WHEN score >= ? THEN 1 ELSE 0 END) AS passing,
                       MIN(score) AS worst,
                       MAX(score) AS best
                FROM quality_scores
                WHERE model IS NOT NULL
                GROUP BY model
                ORDER BY avg_score DESC
                """,
                (self.ALERT_THRESHOLD,),
            ).fetchall()

            for rank, r in enumerate(rows, 1):
                total = r["total"] or 1
                rankings.append({
                    "rank": rank,
                    "model": r["model"],
                    "avg_score": round(r["avg_score"], 2),
                    "total_tasks": total,
                    "pass_rate": round((r["passing"] or 0) / total * 100, 1),
                    "worst_score": round(r["worst"] or 0, 2),
                    "best_score": round(r["best"] or 0, 2),
                })
        except Exception as exc:  # noqa: BLE001
            logger.debug("get_model_rankings: %s", exc)
        return rankings

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    def close(self) -> None:
        try:
            if self._conn:
                self._conn.close()
                self._conn = None
        except Exception:  # noqa: BLE001
            pass


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_instance_lock = threading.Lock()
_instance: Optional[QualityFeedback] = None


def get_quality_feedback() -> QualityFeedback:
    """Thread-safe lazy singleton."""
    global _instance  # noqa: PLW0603
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = QualityFeedback()
    return _instance


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _cli_main() -> None:
    """``python quality_feedback.py [dashboard|alerts|rankings|ack-all]``"""
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    qf = get_quality_feedback()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "dashboard"

    if cmd == "dashboard":
        print(json.dumps(qf.get_dashboard(), indent=2, ensure_ascii=False))
    elif cmd == "alerts":
        alerts = qf.check_alerts()
        if alerts:
            for a in alerts:
                print(f"  ⚠ {a.get('message', json.dumps(a))}")
        else:
            print("  No open alerts.")
    elif cmd == "rankings":
        for r in qf.get_model_rankings():
            print(f"  #{r['rank']} {r['model']:<20s}  avg={r['avg_score']:.1f}  pass={r['pass_rate']:.0f}%")
    elif cmd == "ack-all":
        result = qf.acknowledge_all()
        print(f"  Acknowledged {result.get('acknowledged', 0)} alerts.")
    else:
        print("Usage: python quality_feedback.py [dashboard|alerts|rankings|ack-all]")


if __name__ == "__main__":
    _cli_main()
