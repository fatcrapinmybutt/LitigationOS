"""
DELTA99 Ω∞ — Self-Healing Daemon Engine
=========================================
Watchdog-watches-the-watchdog. Monitors SENTINEL + INQUISITOR heartbeats,
auto-restarts crashed components, circuit-breaks on cascading failures,
snapshots DBs on critical errors.

Architecture:
  heartbeat_table (10s interval) → missed_check (3 consecutive) → auto_restart
  → restart_failed (3x) → emergency_snapshot → Windows Event Log escalation
"""
import sys
import os
import time
import sqlite3
import threading
import traceback
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional, Callable

_shared = Path(__file__).parent.parent / "shared"
if str(_shared) not in sys.path:
    sys.path.insert(0, str(_shared))

from autonomos_config import (
    AUTONOMOS_ROOT, SENTINEL_DIR, INQUISITOR_DIR,
    CENTRAL_DB, PROVENANCE_DB, EVENT_BRIDGE_DB,
    SENTINEL_QUEUE_DB, SENTINEL_OPS_DB, INQUISITOR_RESULTS_DB,
    LITIGOS_ROOT,
)

SELF_HEAL_DB = AUTONOMOS_ROOT / "self_heal.db"
EMERGENCY_BACKUP_DIR = LITIGOS_ROOT / "00_SYSTEM" / "backups" / "emergency"
HEARTBEAT_INTERVAL = 10  # seconds
MISS_THRESHOLD = 3       # consecutive misses before restart
MAX_RESTARTS = 3         # max restarts before escalation
CIRCUIT_BREAKER_COOLDOWN = 300  # 5 min cooldown after max restarts


def _init_db() -> sqlite3.Connection:
    SELF_HEAL_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(SELF_HEAL_DB), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS heartbeats (
            component TEXT NOT NULL,
            beat_at TEXT NOT NULL,
            status TEXT DEFAULT 'alive',
            details TEXT DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_hb_comp ON heartbeats(component);
        CREATE INDEX IF NOT EXISTS idx_hb_time ON heartbeats(beat_at);

        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            component TEXT NOT NULL,
            incident_type TEXT NOT NULL,
            details TEXT DEFAULT '',
            action_taken TEXT DEFAULT '',
            resolved INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS circuit_breakers (
            component TEXT PRIMARY KEY,
            state TEXT DEFAULT 'closed',
            failure_count INTEGER DEFAULT 0,
            last_failure_at TEXT DEFAULT '',
            cooldown_until TEXT DEFAULT '',
            total_trips INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS emergency_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trigger_reason TEXT NOT NULL,
            snapshot_dir TEXT NOT NULL,
            dbs_backed_up INTEGER DEFAULT 0,
            total_size_mb REAL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    return conn


@dataclass
class ComponentStatus:
    name: str
    is_alive: bool = False
    last_beat: str = ""
    missed_beats: int = 0
    restart_count: int = 0
    circuit_state: str = "closed"  # closed, open, half-open


class CircuitBreaker:
    """Per-component circuit breaker."""

    def __init__(self, db: sqlite3.Connection, component: str):
        self._db = db
        self._component = component
        self._ensure_row()

    def _ensure_row(self):
        self._db.execute("""
            INSERT OR IGNORE INTO circuit_breakers (component) VALUES (?)
        """, (self._component,))
        self._db.commit()

    @property
    def state(self) -> str:
        row = self._db.execute(
            "SELECT state, cooldown_until FROM circuit_breakers WHERE component=?",
            (self._component,)
        ).fetchone()
        if not row:
            return "closed"
        if row[0] == "open" and row[1]:
            if datetime.now() > datetime.fromisoformat(row[1]):
                self._db.execute(
                    "UPDATE circuit_breakers SET state='half-open' WHERE component=?",
                    (self._component,)
                )
                self._db.commit()
                return "half-open"
        return row[0]

    def record_failure(self):
        now = datetime.now().isoformat()
        self._db.execute("""
            UPDATE circuit_breakers SET failure_count = failure_count + 1,
            last_failure_at = ? WHERE component = ?
        """, (now, self._component))
        row = self._db.execute(
            "SELECT failure_count FROM circuit_breakers WHERE component=?",
            (self._component,)
        ).fetchone()
        if row and row[0] >= MAX_RESTARTS:
            cooldown = (datetime.now() + timedelta(seconds=CIRCUIT_BREAKER_COOLDOWN)).isoformat()
            self._db.execute("""
                UPDATE circuit_breakers SET state='open', cooldown_until=?,
                total_trips = total_trips + 1 WHERE component=?
            """, (cooldown, self._component))
        self._db.commit()

    def record_success(self):
        self._db.execute("""
            UPDATE circuit_breakers SET state='closed', failure_count=0
            WHERE component=?
        """, (self._component,))
        self._db.commit()

    @property
    def is_open(self) -> bool:
        return self.state == "open"


class SelfHealDaemon:
    """Monitors and auto-restarts AUTONOMOS components."""

    def __init__(self):
        self._db = _init_db()
        self._components: dict[str, dict] = {}
        self._breakers: dict[str, CircuitBreaker] = {}
        self._running = False
        self._threads: dict[str, threading.Thread] = {}

    def register_component(self, name: str, start_fn: Callable, health_fn: Callable[[], bool]):
        """Register a component for monitoring."""
        self._components[name] = {
            "start_fn": start_fn,
            "health_fn": health_fn,
            "missed_beats": 0,
            "restart_count": 0,
            "thread": None,
        }
        self._breakers[name] = CircuitBreaker(self._db, name)

    def heartbeat(self, component: str, status: str = "alive", details: str = ""):
        """Record a heartbeat from a component."""
        now = datetime.now().isoformat()
        self._db.execute("""
            INSERT INTO heartbeats (component, beat_at, status, details)
            VALUES (?, ?, ?, ?)
        """, (component, now, status, details))
        # Keep only last 1000 heartbeats per component
        self._db.execute("""
            DELETE FROM heartbeats WHERE component=? AND rowid NOT IN (
                SELECT rowid FROM heartbeats WHERE component=? ORDER BY beat_at DESC LIMIT 1000
            )
        """, (component, component))
        self._db.commit()
        # Reset missed beats
        if component in self._components:
            self._components[component]["missed_beats"] = 0

    def _check_component(self, name: str) -> ComponentStatus:
        """Check health of a single component."""
        comp = self._components.get(name, {})
        breaker = self._breakers.get(name)

        # Get last heartbeat
        row = self._db.execute("""
            SELECT beat_at FROM heartbeats WHERE component=?
            ORDER BY beat_at DESC LIMIT 1
        """, (name,)).fetchone()

        status = ComponentStatus(name=name)
        if row:
            status.last_beat = row[0]
            last_beat_time = datetime.fromisoformat(row[0])
            elapsed = (datetime.now() - last_beat_time).total_seconds()
            status.is_alive = elapsed < HEARTBEAT_INTERVAL * 3
        else:
            status.is_alive = False

        # Check via health function
        try:
            health_fn = comp.get("health_fn")
            if health_fn and not health_fn():
                status.is_alive = False
        except Exception:
            status.is_alive = False

        status.missed_beats = comp.get("missed_beats", 0)
        status.restart_count = comp.get("restart_count", 0)
        status.circuit_state = breaker.state if breaker else "unknown"

        return status

    def _attempt_restart(self, name: str) -> bool:
        """Attempt to restart a crashed component."""
        comp = self._components.get(name)
        breaker = self._breakers.get(name)

        if not comp or not breaker:
            return False

        if breaker.is_open:
            self._log_incident(name, "CIRCUIT_OPEN",
                               "Circuit breaker open — not restarting",
                               "Waiting for cooldown")
            return False

        comp["restart_count"] += 1
        self._log_incident(name, "RESTART_ATTEMPT",
                           f"Restart #{comp['restart_count']}",
                           "Starting component in new thread")

        try:
            # Kill existing thread if any
            old_thread = comp.get("thread")
            if old_thread and old_thread.is_alive():
                pass  # Can't kill thread — daemon flag will handle it

            # Start in new daemon thread
            start_fn = comp["start_fn"]
            t = threading.Thread(target=start_fn, name=f"{name}_worker", daemon=True)
            t.start()
            comp["thread"] = t

            # Wait briefly and check
            time.sleep(3)
            if t.is_alive():
                breaker.record_success()
                comp["missed_beats"] = 0
                self._log_incident(name, "RESTART_SUCCESS",
                                   f"Restart #{comp['restart_count']} succeeded", "")
                return True
            else:
                breaker.record_failure()
                self._log_incident(name, "RESTART_FAILED",
                                   f"Thread died immediately", "Recording failure")
                return False

        except Exception as e:
            breaker.record_failure()
            self._log_incident(name, "RESTART_ERROR", str(e), "")
            return False

    def emergency_snapshot(self, reason: str) -> str:
        """Emergency backup of all critical databases."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        snap_dir = EMERGENCY_BACKUP_DIR / f"EMERGENCY_{ts}"
        snap_dir.mkdir(parents=True, exist_ok=True)

        dbs = [CENTRAL_DB, PROVENANCE_DB, EVENT_BRIDGE_DB,
               SENTINEL_QUEUE_DB, SENTINEL_OPS_DB, INQUISITOR_RESULTS_DB, SELF_HEAL_DB]

        backed_up = 0
        total_size = 0
        for db_path in dbs:
            if db_path.exists():
                try:
                    dest = snap_dir / db_path.name
                    shutil.copy2(str(db_path), str(dest))
                    total_size += dest.stat().st_size
                    backed_up += 1
                except Exception:
                    pass

        size_mb = round(total_size / (1024 * 1024), 2)
        self._db.execute("""
            INSERT INTO emergency_snapshots (trigger_reason, snapshot_dir, dbs_backed_up, total_size_mb)
            VALUES (?, ?, ?, ?)
        """, (reason, str(snap_dir), backed_up, size_mb))
        self._db.commit()

        self._log_incident("SYSTEM", "EMERGENCY_SNAPSHOT",
                           f"Reason: {reason}", f"Backed up {backed_up} DBs ({size_mb}MB)")
        return str(snap_dir)

    def _log_incident(self, component: str, incident_type: str,
                      details: str = "", action: str = ""):
        self._db.execute("""
            INSERT INTO incidents (component, incident_type, details, action_taken)
            VALUES (?, ?, ?, ?)
        """, (component, incident_type, details, action))
        self._db.commit()
        print(f"[SELF-HEAL] [{component}] {incident_type}: {details}", file=sys.stderr)

    def monitor_loop(self, poll_interval: float = HEARTBEAT_INTERVAL):
        """Main monitoring loop."""
        self._running = True
        print("[SELF-HEAL] Daemon started — monitoring components...", file=sys.stderr)

        while self._running:
            for name in list(self._components.keys()):
                status = self._check_component(name)

                if not status.is_alive:
                    self._components[name]["missed_beats"] += 1
                    missed = self._components[name]["missed_beats"]

                    if missed >= MISS_THRESHOLD:
                        print(f"[SELF-HEAL] {name}: {missed} missed beats — restarting",
                              file=sys.stderr)
                        success = self._attempt_restart(name)

                        if not success and self._components[name]["restart_count"] >= MAX_RESTARTS:
                            self.emergency_snapshot(
                                f"{name} failed {MAX_RESTARTS} restarts"
                            )

            time.sleep(poll_interval)

    def stop(self):
        self._running = False

    def get_status(self) -> dict:
        """Get full system health status."""
        statuses = {}
        for name in self._components:
            s = self._check_component(name)
            statuses[name] = {
                "alive": s.is_alive, "last_beat": s.last_beat,
                "missed": s.missed_beats, "restarts": s.restart_count,
                "circuit": s.circuit_state,
            }
        incidents = self._db.execute("""
            SELECT component, incident_type, details, created_at
            FROM incidents ORDER BY created_at DESC LIMIT 20
        """).fetchall()
        return {
            "components": statuses,
            "recent_incidents": [
                {"component": r[0], "type": r[1], "details": r[2], "at": r[3]}
                for r in incidents
            ],
        }


# ── Singleton for import by SENTINEL/INQUISITOR ────────────────────
_daemon_instance: Optional[SelfHealDaemon] = None


def get_daemon() -> SelfHealDaemon:
    global _daemon_instance
    if _daemon_instance is None:
        _daemon_instance = SelfHealDaemon()
    return _daemon_instance


def heartbeat(component: str, status: str = "alive", details: str = ""):
    """Convenience function for components to send heartbeats."""
    get_daemon().heartbeat(component, status, details)


if __name__ == "__main__":
    import json
    daemon = get_daemon()
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        print(json.dumps(daemon.get_status(), indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "snapshot":
        path = daemon.emergency_snapshot("Manual trigger")
        print(f"Snapshot saved to: {path}")
    else:
        print("Usage: python self_heal.py [status|snapshot]")
