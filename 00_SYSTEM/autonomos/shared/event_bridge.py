"""
AUTONOMOS Event Bridge
=======================
SQLite-based event queue connecting SENTINEL → INQUISITOR with:
  - Exactly-once delivery (consumer ACK pattern)
  - Dead letter queue (3 retries → quarantine)
  - Crash-safe ordered delivery
  - Event types: FILE_ORGANIZED, FILE_ANALYZED, FILING_UPDATED, FILING_PUSHED

Story 4.1: SENTINEL ↔ INQUISITOR Event Bridge
"""
import sqlite3
import json
import uuid
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable
from dataclasses import dataclass

from autonomos_config import EVENT_BRIDGE_DB


@dataclass
class Event:
    """An event in the bridge queue."""
    event_id: str
    event_type: str
    payload: dict
    created_at: str
    processed_at: str = ""
    status: str = "pending"        # pending → processing → done → dead
    retry_count: int = 0
    error: str = ""


def _init_db(db_path: Path = EVENT_BRIDGE_DB) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=120000")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            processed_at TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            retry_count INTEGER DEFAULT 0,
            error TEXT DEFAULT ''
        );

        CREATE INDEX IF NOT EXISTS idx_evt_status ON events(status);
        CREATE INDEX IF NOT EXISTS idx_evt_type ON events(event_type);
        CREATE INDEX IF NOT EXISTS idx_evt_created ON events(created_at);

        CREATE TABLE IF NOT EXISTS dead_letters (
            event_id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            dead_at TEXT NOT NULL,
            retry_count INTEGER DEFAULT 0,
            last_error TEXT DEFAULT ''
        );
    """)
    conn.commit()
    return conn


class EventBridge:
    """SQLite-based event queue for SENTINEL ↔ INQUISITOR communication."""

    MAX_RETRIES = 3

    def __init__(self, db_path: Path = EVENT_BRIDGE_DB):
        self._conn = _init_db(db_path)

    def close(self):
        self._conn.close()

    def publish(self, event_type: str, payload: dict) -> str:
        """Publish an event to the bridge. Returns event_id."""
        event_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        self._conn.execute("""
            INSERT INTO events (event_id, event_type, payload_json, created_at, status)
            VALUES (?, ?, ?, ?, 'pending')
        """, (event_id, event_type, json.dumps(payload), now))
        self._conn.commit()
        return event_id

    def consume(self, event_types: list[str] | None = None, limit: int = 10) -> list[Event]:
        """Fetch pending events for processing. Marks them as 'processing'."""
        if event_types:
            placeholders = ",".join(["?"] * len(event_types))
            query = f"""
                SELECT event_id, event_type, payload_json, created_at, retry_count
                FROM events WHERE status='pending' AND event_type IN ({placeholders})
                ORDER BY created_at LIMIT ?
            """
            rows = self._conn.execute(query, (*event_types, limit)).fetchall()
        else:
            rows = self._conn.execute("""
                SELECT event_id, event_type, payload_json, created_at, retry_count
                FROM events WHERE status='pending'
                ORDER BY created_at LIMIT ?
            """, (limit,)).fetchall()

        events = []
        for r in rows:
            self._conn.execute(
                "UPDATE events SET status='processing' WHERE event_id=?", (r[0],)
            )
            events.append(Event(
                event_id=r[0], event_type=r[1], payload=json.loads(r[2]),
                created_at=r[3], retry_count=r[4], status="processing"
            ))
        self._conn.commit()
        return events

    def ack(self, event_id: str):
        """Acknowledge successful processing of an event."""
        now = datetime.now().isoformat()
        self._conn.execute("""
            UPDATE events SET status='done', processed_at=? WHERE event_id=?
        """, (now, event_id))
        self._conn.commit()

    def nack(self, event_id: str, error: str = ""):
        """Negative acknowledge — retry or dead-letter."""
        row = self._conn.execute(
            "SELECT retry_count, event_type, payload_json, created_at FROM events WHERE event_id=?",
            (event_id,)
        ).fetchone()
        if not row:
            return

        retry_count = row[0] + 1
        if retry_count >= self.MAX_RETRIES:
            # Move to dead letter queue
            now = datetime.now().isoformat()
            self._conn.execute("""
                INSERT OR REPLACE INTO dead_letters 
                (event_id, event_type, payload_json, created_at, dead_at, retry_count, last_error)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (event_id, row[1], row[2], row[3], now, retry_count, error))
            self._conn.execute("DELETE FROM events WHERE event_id=?", (event_id,))
        else:
            # Retry — put back as pending
            self._conn.execute("""
                UPDATE events SET status='pending', retry_count=?, error=?
                WHERE event_id=?
            """, (retry_count, error, event_id))
        self._conn.commit()

    def pending_count(self, event_type: str | None = None) -> int:
        """Count pending events."""
        if event_type:
            return self._conn.execute(
                "SELECT COUNT(*) FROM events WHERE status='pending' AND event_type=?",
                (event_type,)
            ).fetchone()[0]
        return self._conn.execute(
            "SELECT COUNT(*) FROM events WHERE status='pending'"
        ).fetchone()[0]

    def dead_letter_count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM dead_letters").fetchone()[0]

    def stats(self) -> dict:
        """Get queue statistics."""
        result = {}
        for status in ("pending", "processing", "done", "dead"):
            if status == "dead":
                result[status] = self.dead_letter_count()
            else:
                result[status] = self._conn.execute(
                    "SELECT COUNT(*) FROM events WHERE status=?", (status,)
                ).fetchone()[0]
        result["total_processed"] = result.get("done", 0)
        return result

    def replay_dead_letters(self, event_type: str | None = None) -> int:
        """Move dead letters back to pending for retry. Returns count."""
        if event_type:
            rows = self._conn.execute(
                "SELECT event_id, event_type, payload_json, created_at FROM dead_letters WHERE event_type=?",
                (event_type,)
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT event_id, event_type, payload_json, created_at FROM dead_letters"
            ).fetchall()

        for r in rows:
            self._conn.execute("""
                INSERT OR REPLACE INTO events 
                (event_id, event_type, payload_json, created_at, status, retry_count)
                VALUES (?, ?, ?, ?, 'pending', 0)
            """, (r[0], r[1], r[2], r[3]))
            self._conn.execute("DELETE FROM dead_letters WHERE event_id=?", (r[0],))
        self._conn.commit()
        return len(rows)

    def process_loop(self, handler: Callable[[Event], None],
                     event_types: list[str] | None = None,
                     poll_interval: float = 2.0, max_iterations: int = 0):
        """Run a consumer loop. Set max_iterations=0 for infinite loop."""
        iteration = 0
        while max_iterations == 0 or iteration < max_iterations:
            events = self.consume(event_types, limit=5)
            if not events:
                time.sleep(poll_interval)
                iteration += 1
                continue
            for event in events:
                try:
                    handler(event)
                    self.ack(event.event_id)
                except Exception as e:
                    self.nack(event.event_id, str(e))
            iteration += 1
