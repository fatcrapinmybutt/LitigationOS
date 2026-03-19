"""
SENTINEL File System Monitor
==============================
Monitors all configured drives for new/changed files using Python's watchdog library.
Debounces rapid events, filters excluded patterns, queues files for classification.

Story 1.1: File System Monitor Service
"""
import sys
import os
import time
import sqlite3
import hashlib
import threading
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Optional

# Add shared to path
_shared = Path(__file__).parent.parent / "shared"
if str(_shared) not in sys.path:
    sys.path.insert(0, str(_shared))

from autonomos_config import (
    SENTINEL_QUEUE_DB, DRIVE_SCAN_ROOTS, detect_drives,
    SENTINEL_SKIP_NAMES, SENTINEL_SKIP_EXTENSIONS, SENTINEL_SKIP_PREFIXES,
    SENTINEL_SKIP_DIRS, DEBOUNCE_SECONDS, MAX_FILE_SIZE_MB,
    sha256_file, long_path,
)

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent, FileMovedEvent
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False
    # Provide stub base class so module loads even without watchdog
    class FileSystemEventHandler:
        """Stub when watchdog not installed."""
        pass
    class FileCreatedEvent:
        pass
    class FileModifiedEvent:
        pass
    class FileMovedEvent:
        pass
    class Observer:
        def schedule(self, *a, **kw): pass
        def start(self): pass
        def stop(self): pass
        def join(self): pass
    print("[WARN] watchdog not installed. Run: pip install watchdog", file=sys.stderr)


def _init_queue_db(db_path: Path = SENTINEL_QUEUE_DB) -> sqlite3.Connection:
    """Initialize the SENTINEL file queue database."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=120000")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS file_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            drive TEXT NOT NULL,
            sha256 TEXT DEFAULT '',
            file_size INTEGER DEFAULT 0,
            detected_at TEXT NOT NULL,
            event_type TEXT DEFAULT 'created',
            status TEXT DEFAULT 'pending',
            classification TEXT DEFAULT '',
            lane TEXT DEFAULT '',
            confidence REAL DEFAULT 0.0,
            dest_path TEXT DEFAULT '',
            error TEXT DEFAULT '',
            processed_at TEXT DEFAULT '',
            UNIQUE(file_path, sha256)
        );

        CREATE INDEX IF NOT EXISTS idx_fq_status ON file_queue(status);
        CREATE INDEX IF NOT EXISTS idx_fq_drive ON file_queue(drive);
        CREATE INDEX IF NOT EXISTS idx_fq_detected ON file_queue(detected_at);
        CREATE INDEX IF NOT EXISTS idx_fq_sha256 ON file_queue(sha256);

        CREATE TABLE IF NOT EXISTS monitor_state (
            drive TEXT PRIMARY KEY,
            is_active INTEGER DEFAULT 1,
            last_event_at TEXT DEFAULT '',
            events_today INTEGER DEFAULT 0,
            errors_today INTEGER DEFAULT 0,
            last_error TEXT DEFAULT ''
        );
    """)
    conn.commit()
    return conn


def _should_skip(path: Path) -> bool:
    """Check if a file/directory should be ignored."""
    name = path.name
    # Skip by name
    if name in SENTINEL_SKIP_NAMES:
        return True
    # Skip by prefix
    for prefix in SENTINEL_SKIP_PREFIXES:
        if name.startswith(prefix):
            return True
    # Skip by extension
    if path.suffix.lower() in SENTINEL_SKIP_EXTENSIONS:
        return True
    # Skip if any parent is in skip dirs
    for parent in path.parents:
        if parent.name in SENTINEL_SKIP_DIRS:
            return True
    return False


def _get_drive_letter(path: str) -> str:
    """Extract drive letter from a path."""
    if len(path) >= 2 and path[1] == ":":
        return path[0].upper()
    return "?"


def _safe_hash(path: Path, max_mb: int = MAX_FILE_SIZE_MB) -> str:
    """Compute SHA-256, skipping files larger than max_mb."""
    try:
        size = path.stat().st_size
        if size > max_mb * 1024 * 1024:
            return f"TOO_LARGE_{size}"
        return sha256_file(path)
    except (OSError, PermissionError):
        return "UNREADABLE"


class SentinelEventHandler(FileSystemEventHandler):
    """Handles filesystem events with debouncing and filtering."""

    def __init__(self, queue_db: sqlite3.Connection, drive: str, debounce_s: float = DEBOUNCE_SECONDS):
        super().__init__()
        self._db = queue_db
        self._drive = drive
        self._debounce_s = debounce_s
        self._pending: dict[str, float] = {}  # path → last_event_time
        self._lock = threading.Lock()
        self._stats = {"created": 0, "modified": 0, "moved": 0, "skipped": 0}

    def _debounced_enqueue(self, path: str, event_type: str):
        """Debounce rapid events for the same file."""
        now = time.time()
        with self._lock:
            last = self._pending.get(path, 0)
            if now - last < self._debounce_s:
                return  # Still debouncing
            self._pending[path] = now

        p = Path(path)
        if _should_skip(p):
            self._stats["skipped"] += 1
            return
        if not p.is_file():
            return

        # Enqueue
        try:
            file_size = p.stat().st_size
            sha = _safe_hash(p)
            ts = datetime.now().isoformat()
            self._db.execute("""
                INSERT OR IGNORE INTO file_queue (file_path, drive, sha256, file_size, detected_at, event_type)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (str(p), self._drive, sha, file_size, ts, event_type))
            self._db.commit()
            self._stats[event_type] = self._stats.get(event_type, 0) + 1
        except (OSError, PermissionError, sqlite3.Error) as e:
            self._stats["skipped"] += 1

    def on_created(self, event):
        if not event.is_directory:
            self._debounced_enqueue(event.src_path, "created")

    def on_modified(self, event):
        if not event.is_directory:
            self._debounced_enqueue(event.src_path, "modified")

    def on_moved(self, event):
        if not event.is_directory:
            self._debounced_enqueue(event.dest_path, "moved")

    @property
    def stats(self) -> dict:
        return dict(self._stats)


class SentinelMonitor:
    """Main SENTINEL monitor — watches all drives for new files."""

    def __init__(self, db_path: Path = SENTINEL_QUEUE_DB):
        self._db = _init_queue_db(db_path)
        self._observers: dict[str, Observer] = {}
        self._handlers: dict[str, SentinelEventHandler] = {}
        self._running = False

    def start(self, drives: dict | None = None):
        """Start monitoring configured drives."""
        if not HAS_WATCHDOG:
            raise RuntimeError("watchdog library not installed. Run: pip install watchdog")

        scan_roots = drives or DRIVE_SCAN_ROOTS
        available = detect_drives()

        for drive_letter, paths in scan_roots.items():
            if drive_letter not in available:
                print(f"[SENTINEL] Drive {drive_letter}: not available, skipping", file=sys.stderr)
                continue

            observer = Observer()
            handler = SentinelEventHandler(self._db, drive_letter)

            for watch_path in paths:
                if watch_path.exists():
                    try:
                        observer.schedule(handler, str(watch_path), recursive=True)
                        print(f"[SENTINEL] Watching: {watch_path}", file=sys.stderr)
                    except Exception as e:
                        print(f"[SENTINEL] Failed to watch {watch_path}: {e}", file=sys.stderr)

            try:
                observer.start()
                self._observers[drive_letter] = observer
                self._handlers[drive_letter] = handler
                self._db.execute("""
                    INSERT OR REPLACE INTO monitor_state (drive, is_active, last_event_at)
                    VALUES (?, 1, datetime('now'))
                """, (drive_letter,))
            except Exception as e:
                print(f"[SENTINEL] Failed to start observer for {drive_letter}: {e}", file=sys.stderr)

        self._db.commit()
        self._running = True
        print(f"[SENTINEL] Monitoring {len(self._observers)} drives", file=sys.stderr)

    def stop(self):
        """Stop all monitors."""
        for drive, observer in self._observers.items():
            observer.stop()
            observer.join(timeout=5)
            self._db.execute(
                "UPDATE monitor_state SET is_active=0 WHERE drive=?", (drive,)
            )
        self._db.commit()
        self._observers.clear()
        self._handlers.clear()
        self._running = False

    def get_pending(self, limit: int = 100) -> list[dict]:
        """Get pending files from the queue."""
        rows = self._db.execute("""
            SELECT id, file_path, drive, sha256, file_size, detected_at, event_type
            FROM file_queue WHERE status='pending'
            ORDER BY detected_at LIMIT ?
        """, (limit,)).fetchall()
        return [
            {"id": r[0], "path": r[1], "drive": r[2], "sha256": r[3],
             "size": r[4], "detected_at": r[5], "event_type": r[6]}
            for r in rows
        ]

    def mark_processed(self, queue_id: int, classification: str = "", lane: str = "",
                       confidence: float = 0.0, dest_path: str = ""):
        """Mark a queue item as processed."""
        now = datetime.now().isoformat()
        self._db.execute("""
            UPDATE file_queue SET status='processed', classification=?, lane=?,
            confidence=?, dest_path=?, processed_at=?
            WHERE id=?
        """, (classification, lane, confidence, dest_path, now, queue_id))
        self._db.commit()

    def mark_failed(self, queue_id: int, error: str):
        """Mark a queue item as failed."""
        self._db.execute("""
            UPDATE file_queue SET status='failed', error=?, processed_at=datetime('now')
            WHERE id=?
        """, (error, queue_id))
        self._db.commit()

    def queue_stats(self) -> dict:
        """Get queue statistics."""
        result = {}
        for status in ("pending", "processed", "failed"):
            cnt = self._db.execute(
                "SELECT COUNT(*) FROM file_queue WHERE status=?", (status,)
            ).fetchone()[0]
            result[status] = cnt
        result["total"] = sum(result.values())
        return result

    def drive_stats(self) -> list[dict]:
        """Get per-drive monitoring stats."""
        rows = self._db.execute("SELECT * FROM monitor_state").fetchall()
        cols = [d[0] for d in self._db.execute("SELECT * FROM monitor_state LIMIT 0").description]
        return [dict(zip(cols, r)) for r in rows]

    @property
    def is_running(self) -> bool:
        return self._running

    def run_forever(self):
        """Run the monitor until interrupted."""
        if not self._running:
            self.start()
        try:
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[SENTINEL] Shutting down...", file=sys.stderr)
        finally:
            self.stop()


# ── CLI Entry Point ─────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SENTINEL File System Monitor")
    parser.add_argument("action", choices=["start", "status", "pending", "stats"],
                        help="Action to perform")
    parser.add_argument("--limit", type=int, default=20, help="Max items for pending/stats")
    args = parser.parse_args()

    monitor = SentinelMonitor()

    if args.action == "start":
        print("[SENTINEL] Starting file system monitor... (Ctrl+C to stop)")
        monitor.run_forever()

    elif args.action == "status":
        stats = monitor.drive_stats()
        print(f"Drive monitoring status:")
        for s in stats:
            print(f"  {s['drive']}: active={s['is_active']} last_event={s['last_event_at']}")

    elif args.action == "pending":
        items = monitor.get_pending(args.limit)
        print(f"Pending items: {len(items)}")
        for item in items:
            print(f"  [{item['drive']}] {item['path']} ({item['event_type']})")

    elif args.action == "stats":
        qs = monitor.queue_stats()
        print(f"Queue: pending={qs['pending']} processed={qs['processed']} "
              f"failed={qs['failed']} total={qs['total']}")
