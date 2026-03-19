#!/usr/bin/env python3
"""
APEX Learning Loop — Autonomous improvement from every interaction.

Stores patterns in SQLite learning_metrics.db.  Zero LLM dependency for core
learning.  When LLM is available, adds neural quality assessment on top.

Learning cycle
--------------
1. Task completes → extract patterns (what worked, what failed)
2. Store in learning_metrics.db
3. Update model_performance weights (which model/skill worked best)
4. Track quality scores by task type, model, time
5. Detect quality drift → trigger alerts
6. Feed back into model selection for next task

Thread-safe, UTF-8 safe, never crashes.
"""

from __future__ import annotations

import json
import logging
import os
import re
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
logger = logging.getLogger("apex.learning_loop")

# ---------------------------------------------------------------------------
# Paths (never use CWD — always relative to *this* file)
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
# Schema
# ---------------------------------------------------------------------------
_SCHEMA: str = """
CREATE TABLE IF NOT EXISTS task_outcomes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TEXT    DEFAULT (datetime('now')),
    task_type       TEXT    NOT NULL,
    lane            TEXT,
    model_used      TEXT,
    skill_chain     TEXT,
    quality_score   REAL,
    latency_s       REAL,
    success         INTEGER DEFAULT 1,
    error_type      TEXT,
    patterns_json   TEXT,
    feedback        TEXT
);

CREATE TABLE IF NOT EXISTS model_performance (
    model_name      TEXT NOT NULL,
    task_type       TEXT NOT NULL,
    avg_quality     REAL    DEFAULT 0,
    avg_latency     REAL    DEFAULT 0,
    success_rate    REAL    DEFAULT 1.0,
    sample_count    INTEGER DEFAULT 0,
    last_updated    TEXT    DEFAULT (datetime('now')),
    PRIMARY KEY (model_name, task_type)
);

CREATE TABLE IF NOT EXISTS patterns (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TEXT    DEFAULT (datetime('now')),
    pattern_type    TEXT,
    description     TEXT,
    frequency       INTEGER DEFAULT 1,
    impact          TEXT,
    resolution      TEXT
);

CREATE TABLE IF NOT EXISTS quality_trends (
    date            TEXT NOT NULL,
    task_type       TEXT NOT NULL,
    avg_score       REAL,
    sample_count    INTEGER,
    PRIMARY KEY (date, task_type)
);

CREATE INDEX IF NOT EXISTS idx_outcomes_task   ON task_outcomes(task_type);
CREATE INDEX IF NOT EXISTS idx_outcomes_ts     ON task_outcomes(timestamp);
CREATE INDEX IF NOT EXISTS idx_patterns_type   ON patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_trends_date     ON quality_trends(date);
"""

# ---------------------------------------------------------------------------
# Pattern extraction rules (compiled once, immutable, thread-safe)
# ---------------------------------------------------------------------------
_ERROR_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"timeout|timed?\s*out", re.I), "timeout"),
    (re.compile(r"SQLITE_BUSY|database is locked", re.I), "db_contention"),
    (re.compile(r"EAGAIN|pipe.?overflow", re.I), "eagain"),
    (re.compile(r"lane.*contaminat", re.I), "lane_contamination"),
    (re.compile(r"hallucin|fabricat", re.I), "hallucination"),
    (re.compile(r"missing.*citation|no.*authority", re.I), "missing_citation"),
    (re.compile(r"placeholder|TODO|TBD|\[REQUIRED\]", re.I), "placeholder_left"),
]

_SUCCESS_INDICATORS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"score[:\s]*(?:9\d|100)", re.I), "high_quality"),
    (re.compile(r"all.*pass|PASS", re.I), "all_gates_passed"),
    (re.compile(r"filed|submitted|served", re.I), "court_filing"),
    (re.compile(r"chain.*complete|full.*chain", re.I), "complete_chain"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _safe_connect(db_path: Path) -> Optional[sqlite3.Connection]:
    """Open a SQLite connection with mandatory PRAGMAs.  Returns None on failure."""
    try:
        p = str(db_path)
        conn = sqlite3.connect(p, timeout=60, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.executescript(_DB_PRAGMAS)
        return conn
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to open DB %s: %s", db_path, exc)
        return None


def _ensure_schema(conn: sqlite3.Connection) -> None:
    """Idempotent schema creation."""
    try:
        conn.executescript(_SCHEMA)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Schema init warning: %s", exc)


# ---------------------------------------------------------------------------
# LearningLoop
# ---------------------------------------------------------------------------
class LearningLoop:
    """Autonomous learning engine — records outcomes, extracts patterns, detects drift."""

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
            logger.warning("LearningLoop DB init failed: %s", exc)

    def _get_conn(self) -> Optional[sqlite3.Connection]:
        if self._conn is None:
            self._init_db()
        return self._conn

    # ------------------------------------------------------------------
    # Record outcome
    # ------------------------------------------------------------------
    def record_outcome(
        self,
        task_type: str,
        lane: str,
        model: str,
        skill_chain: list[str],
        quality_score: float,
        latency: float,
        success: bool,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record a task outcome for learning.  Returns status dict."""
        try:
            conn = self._get_conn()
            if conn is None:
                return {"status": "error", "error": "no database connection"}

            patterns_json = json.dumps(
                self.extract_patterns(
                    {
                        "task_type": task_type,
                        "error": error,
                        "quality_score": quality_score,
                        "success": success,
                    }
                ),
                ensure_ascii=False,
            )

            with self._lock:
                conn.execute(
                    """
                    INSERT INTO task_outcomes
                        (task_type, lane, model_used, skill_chain,
                         quality_score, latency_s, success, error_type, patterns_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        task_type,
                        lane,
                        model,
                        json.dumps(skill_chain, ensure_ascii=False),
                        quality_score,
                        latency,
                        1 if success else 0,
                        error,
                        patterns_json,
                    ),
                )
                self._update_model_performance(conn, model, task_type, quality_score, latency, success)
                self._update_quality_trend(conn, task_type, quality_score)
                conn.commit()

            return {"status": "ok", "task_type": task_type, "quality_score": quality_score}
        except Exception as exc:  # noqa: BLE001
            logger.warning("record_outcome failed: %s", exc)
            return {"status": "error", "error": str(exc)}

    def _update_model_performance(
        self,
        conn: sqlite3.Connection,
        model: str,
        task_type: str,
        quality: float,
        latency: float,
        success: bool,
    ) -> None:
        """Rolling update of model_performance aggregate row."""
        try:
            row = conn.execute(
                "SELECT avg_quality, avg_latency, success_rate, sample_count "
                "FROM model_performance WHERE model_name = ? AND task_type = ?",
                (model, task_type),
            ).fetchone()

            if row is None:
                conn.execute(
                    """
                    INSERT INTO model_performance
                        (model_name, task_type, avg_quality, avg_latency, success_rate, sample_count)
                    VALUES (?, ?, ?, ?, ?, 1)
                    """,
                    (model, task_type, quality, latency, 1.0 if success else 0.0),
                )
            else:
                n = row["sample_count"]
                new_n = n + 1
                new_q = (row["avg_quality"] * n + quality) / new_n
                new_l = (row["avg_latency"] * n + latency) / new_n
                new_s = (row["success_rate"] * n + (1.0 if success else 0.0)) / new_n
                conn.execute(
                    """
                    UPDATE model_performance
                    SET avg_quality = ?, avg_latency = ?, success_rate = ?,
                        sample_count = ?, last_updated = datetime('now')
                    WHERE model_name = ? AND task_type = ?
                    """,
                    (new_q, new_l, new_s, new_n, model, task_type),
                )
        except Exception as exc:  # noqa: BLE001
            logger.debug("_update_model_performance: %s", exc)

    def _update_quality_trend(
        self, conn: sqlite3.Connection, task_type: str, quality: float
    ) -> None:
        """Upsert today's quality_trends row."""
        try:
            today = datetime.utcnow().strftime("%Y-%m-%d")
            row = conn.execute(
                "SELECT avg_score, sample_count FROM quality_trends "
                "WHERE date = ? AND task_type = ?",
                (today, task_type),
            ).fetchone()

            if row is None:
                conn.execute(
                    "INSERT INTO quality_trends (date, task_type, avg_score, sample_count) "
                    "VALUES (?, ?, ?, 1)",
                    (today, task_type, quality),
                )
            else:
                n = row["sample_count"]
                new_avg = (row["avg_score"] * n + quality) / (n + 1)
                conn.execute(
                    "UPDATE quality_trends SET avg_score = ?, sample_count = ? "
                    "WHERE date = ? AND task_type = ?",
                    (new_avg, n + 1, today, task_type),
                )
        except Exception as exc:  # noqa: BLE001
            logger.debug("_update_quality_trend: %s", exc)

    # ------------------------------------------------------------------
    # Pattern extraction
    # ------------------------------------------------------------------
    def extract_patterns(self, task_results: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract reusable patterns from task results.  Pure function, never crashes."""
        patterns: list[dict[str, str]] = []
        try:
            error_text = str(task_results.get("error") or "")
            quality = task_results.get("quality_score", 0)
            success = task_results.get("success", True)

            # Error pattern matching
            for rx, tag in _ERROR_PATTERNS:
                if rx.search(error_text):
                    patterns.append(
                        {"pattern_type": "error_pattern", "description": tag, "impact": "high"}
                    )

            # Success pattern matching
            result_text = json.dumps(task_results, default=str)
            for rx, tag in _SUCCESS_INDICATORS:
                if rx.search(result_text):
                    patterns.append(
                        {"pattern_type": "success_pattern", "description": tag, "impact": "medium"}
                    )

            # Quality-based patterns
            if isinstance(quality, (int, float)):
                if quality >= 90:
                    patterns.append(
                        {"pattern_type": "success_pattern", "description": "excellent_quality", "impact": "high"}
                    )
                elif quality < 50 and not success:
                    patterns.append(
                        {"pattern_type": "failure_pattern", "description": "low_quality_failure", "impact": "high"}
                    )

            # Store unique patterns to DB
            self._persist_patterns(patterns)
        except Exception as exc:  # noqa: BLE001
            logger.debug("extract_patterns: %s", exc)

        return patterns

    def _persist_patterns(self, patterns: List[Dict[str, str]]) -> None:
        """Upsert patterns — bump frequency if the description already exists."""
        conn = self._get_conn()
        if conn is None or not patterns:
            return
        try:
            with self._lock:
                for p in patterns:
                    existing = conn.execute(
                        "SELECT id, frequency FROM patterns WHERE description = ? AND pattern_type = ?",
                        (p["description"], p["pattern_type"]),
                    ).fetchone()
                    if existing:
                        conn.execute(
                            "UPDATE patterns SET frequency = frequency + 1 WHERE id = ?",
                            (existing["id"],),
                        )
                    else:
                        conn.execute(
                            "INSERT INTO patterns (pattern_type, description, impact) VALUES (?, ?, ?)",
                            (p["pattern_type"], p["description"], p.get("impact", "medium")),
                        )
                conn.commit()
        except Exception as exc:  # noqa: BLE001
            logger.debug("_persist_patterns: %s", exc)

    # ------------------------------------------------------------------
    # Model selection
    # ------------------------------------------------------------------
    def get_best_model(self, task_type: str) -> str:
        """Return historically best-performing model for *task_type*.

        Falls back to ``"manbearpig"`` when no data is available.
        """
        try:
            conn = self._get_conn()
            if conn is None:
                return "manbearpig"

            row = conn.execute(
                """
                SELECT model_name
                FROM model_performance
                WHERE task_type = ? AND sample_count >= 3
                ORDER BY (avg_quality * success_rate) DESC
                LIMIT 1
                """,
                (task_type,),
            ).fetchone()

            if row:
                return row["model_name"]

            # No data for this task type — check overall best
            row = conn.execute(
                """
                SELECT model_name
                FROM model_performance
                WHERE sample_count >= 5
                ORDER BY (avg_quality * success_rate) DESC
                LIMIT 1
                """,
            ).fetchone()
            return row["model_name"] if row else "manbearpig"
        except Exception as exc:  # noqa: BLE001
            logger.debug("get_best_model: %s", exc)
            return "manbearpig"

    # ------------------------------------------------------------------
    # Quality trends
    # ------------------------------------------------------------------
    def get_quality_trend(
        self, task_type: Optional[str] = None, days: int = 30
    ) -> Dict[str, Any]:
        """Quality score trend over time.  Detects drift automatically."""
        try:
            conn = self._get_conn()
            if conn is None:
                return {"status": "error", "error": "no database connection"}

            cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
            if task_type:
                rows = conn.execute(
                    "SELECT date, avg_score, sample_count FROM quality_trends "
                    "WHERE task_type = ? AND date >= ? ORDER BY date",
                    (task_type, cutoff),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT date, task_type, avg_score, sample_count FROM quality_trends "
                    "WHERE date >= ? ORDER BY date",
                    (cutoff,),
                ).fetchall()

            points = [dict(r) for r in rows]
            drift_alerts = self.detect_drift()

            return {
                "status": "ok",
                "days": days,
                "task_type": task_type or "all",
                "data_points": len(points),
                "points": points,
                "drift_alerts": drift_alerts,
            }
        except Exception as exc:  # noqa: BLE001
            logger.debug("get_quality_trend: %s", exc)
            return {"status": "error", "error": str(exc)}

    # ------------------------------------------------------------------
    # Drift detection
    # ------------------------------------------------------------------
    def detect_drift(self, threshold: float = 5.0) -> List[Dict[str, Any]]:
        """Detect quality drift (>*threshold*-point drop).  Returns alert list."""
        alerts: list[dict[str, Any]] = []
        try:
            conn = self._get_conn()
            if conn is None:
                return alerts

            rows = conn.execute(
                """
                SELECT task_type,
                       AVG(CASE WHEN date >= date('now', '-7 days') THEN avg_score END) AS recent,
                       AVG(CASE WHEN date < date('now', '-7 days')
                                 AND date >= date('now', '-30 days') THEN avg_score END) AS baseline
                FROM quality_trends
                WHERE date >= date('now', '-30 days')
                GROUP BY task_type
                HAVING recent IS NOT NULL AND baseline IS NOT NULL
                """,
            ).fetchall()

            for r in rows:
                delta = r["baseline"] - r["recent"]
                if delta > threshold:
                    alerts.append(
                        {
                            "task_type": r["task_type"],
                            "baseline": round(r["baseline"], 2),
                            "recent": round(r["recent"], 2),
                            "drop": round(delta, 2),
                            "severity": "critical" if delta > threshold * 2 else "warning",
                        }
                    )
        except Exception as exc:  # noqa: BLE001
            logger.debug("detect_drift: %s", exc)
        return alerts

    # ------------------------------------------------------------------
    # Recommendations
    # ------------------------------------------------------------------
    def get_recommendations(self) -> List[Dict[str, str]]:
        """Recommendations based on historical data."""
        recs: list[dict[str, str]] = []
        try:
            conn = self._get_conn()
            if conn is None:
                return [{"recommendation": "No DB available — enable learning_metrics.db"}]

            # Low success rate models
            low_success = conn.execute(
                "SELECT model_name, task_type, success_rate, sample_count "
                "FROM model_performance WHERE success_rate < 0.7 AND sample_count >= 3"
            ).fetchall()
            for r in low_success:
                recs.append(
                    {
                        "type": "model_issue",
                        "recommendation": (
                            f"Model '{r['model_name']}' has {r['success_rate']:.0%} success "
                            f"rate on '{r['task_type']}' ({r['sample_count']} samples). "
                            f"Consider switching to a different model."
                        ),
                    }
                )

            # High-frequency error patterns
            freq_errors = conn.execute(
                "SELECT description, frequency FROM patterns "
                "WHERE pattern_type = 'error_pattern' AND frequency >= 3 "
                "ORDER BY frequency DESC LIMIT 5"
            ).fetchall()
            for r in freq_errors:
                recs.append(
                    {
                        "type": "recurring_error",
                        "recommendation": (
                            f"Error '{r['description']}' occurred {r['frequency']} times. "
                            f"Investigate root cause."
                        ),
                    }
                )

            # Drift alerts
            drift = self.detect_drift()
            for alert in drift:
                recs.append(
                    {
                        "type": "quality_drift",
                        "recommendation": (
                            f"Quality dropped {alert['drop']}pts for '{alert['task_type']}' "
                            f"(baseline {alert['baseline']} → recent {alert['recent']}). "
                            f"Review recent changes."
                        ),
                    }
                )

            if not recs:
                recs.append({"type": "info", "recommendation": "No issues detected. System healthy."})
        except Exception as exc:  # noqa: BLE001
            logger.debug("get_recommendations: %s", exc)
            recs.append({"type": "error", "recommendation": f"Analysis failed: {exc}"})
        return recs

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    def summary(self) -> Dict[str, Any]:
        """Learning loop summary: total tasks, avg quality, model rankings, patterns."""
        try:
            conn = self._get_conn()
            if conn is None:
                return {"status": "error", "error": "no database connection"}

            row = conn.execute(
                """
                SELECT
                    (SELECT COUNT(*)       FROM task_outcomes)          AS total_tasks,
                    (SELECT AVG(quality_score) FROM task_outcomes
                     WHERE quality_score IS NOT NULL)                   AS avg_quality,
                    (SELECT COUNT(*)       FROM task_outcomes
                     WHERE success = 1)                                AS successes,
                    (SELECT COUNT(*)       FROM patterns)              AS pattern_count,
                    (SELECT COUNT(DISTINCT model_name)
                     FROM model_performance)                           AS models_tracked
                """
            ).fetchone()

            total = row["total_tasks"] or 0
            successes = row["successes"] or 0
            success_rate = (successes / total * 100) if total > 0 else 0

            # Top models
            top_models = conn.execute(
                "SELECT model_name, AVG(avg_quality * success_rate) AS score, "
                "SUM(sample_count) AS total_samples "
                "FROM model_performance GROUP BY model_name "
                "ORDER BY score DESC LIMIT 5"
            ).fetchall()

            return {
                "status": "ok",
                "total_tasks": total,
                "avg_quality": round(row["avg_quality"] or 0, 2),
                "success_rate": round(success_rate, 1),
                "patterns_found": row["pattern_count"] or 0,
                "models_tracked": row["models_tracked"] or 0,
                "top_models": [
                    {"model": m["model_name"], "score": round(m["score"] or 0, 2), "samples": m["total_samples"]}
                    for m in top_models
                ],
                "drift_alerts": self.detect_drift(),
                "recommendations": self.get_recommendations(),
            }
        except Exception as exc:  # noqa: BLE001
            logger.debug("summary: %s", exc)
            return {"status": "error", "error": str(exc)}

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    def close(self) -> None:
        """Close DB connection."""
        try:
            if self._conn:
                self._conn.close()
                self._conn = None
        except Exception:  # noqa: BLE001
            pass


# ---------------------------------------------------------------------------
# Module-level convenience instance (lazy, thread-safe)
# ---------------------------------------------------------------------------
_instance_lock = threading.Lock()
_instance: Optional[LearningLoop] = None


def get_learning_loop() -> LearningLoop:
    """Return module-level singleton.  Thread-safe lazy init."""
    global _instance  # noqa: PLW0603
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = LearningLoop()
    return _instance


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------
def _cli_main() -> None:
    """Quick CLI: ``python learning_loop.py [summary|recommend|drift]``"""
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    ll = get_learning_loop()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "summary"

    if cmd == "summary":
        print(json.dumps(ll.summary(), indent=2, ensure_ascii=False))
    elif cmd == "recommend":
        for r in ll.get_recommendations():
            print(f"  [{r.get('type', '?')}] {r['recommendation']}")
    elif cmd == "drift":
        alerts = ll.detect_drift()
        if alerts:
            for a in alerts:
                print(f"  ⚠ {a['task_type']}: {a['drop']}pt drop ({a['severity']})")
        else:
            print("  No quality drift detected.")
    else:
        print(f"Usage: python learning_loop.py [summary|recommend|drift]")


if __name__ == "__main__":
    _cli_main()
