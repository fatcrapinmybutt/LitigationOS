"""
Auto-Ingest Trigger for LitigationOS Daemon.
Connects the File Watchdog to the Task Queue for automatic document processing.

When watchdog detects a new/changed file:
1. Classify document type and case lane
2. Hash the file for provenance
3. Enqueue appropriate processing tasks (extract, OCR, brain feed, etc.)
4. Log to litigation_context.db
"""
import hashlib
import logging
import os
import sqlite3
from datetime import datetime
from typing import Optional

from .models import TaskPriority
from .task_queue import TaskQueue
from .watchdog_engine import FileEvent

logger = logging.getLogger("daemon.auto_ingest")

# Extensions that trigger full processing
PROCESSABLE_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".txt", ".md",
    ".csv", ".xlsx", ".xls",
    ".jpg", ".jpeg", ".png", ".tiff", ".bmp",
    ".html", ".htm", ".xml",
    ".rtf", ".odt",
}

# Extensions that need OCR
OCR_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".bmp"}

# Priority boost for certain doc types
PRIORITY_MAP = {
    "motion": TaskPriority.HIGH,
    "complaint": TaskPriority.HIGH,
    "order": TaskPriority.CRITICAL,
    "evidence": TaskPriority.HIGH,
    "affidavit": TaskPriority.HIGH,
    "brief": TaskPriority.NORMAL,
    "transcript": TaskPriority.NORMAL,
    "correspondence": TaskPriority.LOW,
    "form": TaskPriority.NORMAL,
}


class AutoIngestEngine:
    """Orchestrates automatic file ingestion when watchdog detects changes."""

    def __init__(self, task_queue: TaskQueue, litigation_db_path: str = None):
        self.task_queue = task_queue
        self.litigation_db = litigation_db_path or (
            r"C:\Users\andre\LitigationOS\litigation_context.db"
        )
        self._processed_hashes: set[str] = set()
        self._load_known_hashes()

    def _load_known_hashes(self):
        """Load already-processed file hashes to avoid re-processing."""
        try:
            conn = sqlite3.connect(self.litigation_db, timeout=30)
            conn.execute("PRAGMA busy_timeout=30000")
            rows = conn.execute(
                "SELECT sha256 FROM documents WHERE sha256 IS NOT NULL"
            ).fetchall()
            self._processed_hashes = {r[0] for r in rows}
            conn.close()
            logger.info(f"Loaded {len(self._processed_hashes)} known document hashes")
        except Exception as e:
            logger.warning(f"Could not load known hashes: {e}")

    def handle_event(self, event: FileEvent):
        """Handle a watchdog file event — the main entry point.

        This method is passed as on_event callback to WatchdogEngine.
        """
        # Only process created/modified events
        if event.event_type not in ("created", "modified"):
            return

        path = event.path
        ext = os.path.splitext(path)[1].lower()

        # Skip non-processable files
        if ext not in PROCESSABLE_EXTENSIONS:
            return

        # Skip tiny files (likely incomplete or temp)
        try:
            size = os.path.getsize(path)
            if size < 100:  # Skip files under 100 bytes
                return
        except OSError:
            return

        # Compute hash for dedup
        file_hash = self._quick_hash(path)
        if file_hash in self._processed_hashes:
            logger.debug(f"Already processed (hash match): {os.path.basename(path)}")
            return

        # Determine priority based on doc type
        priority = PRIORITY_MAP.get(event.doc_type, TaskPriority.NORMAL)

        # Build task payload
        payload = {
            "file_path": os.path.abspath(path),
            "file_name": os.path.basename(path),
            "extension": ext,
            "size_bytes": size,
            "sha256": file_hash,
            "lane": event.lane,
            "doc_type": event.doc_type,
            "detected_at": datetime.utcnow().isoformat(),
        }

        # Enqueue classification task
        task_id = self.task_queue.enqueue(
            task_type="auto_classify",
            payload=payload,
            priority=priority,
            source="watchdog",
        )
        logger.info(
            f"Auto-ingest: {os.path.basename(path)} → task {task_id[:8]} "
            f"[Lane {event.lane or '?'}, {event.doc_type or 'unknown'}]"
        )

        # Enqueue OCR if needed
        if ext in OCR_EXTENSIONS:
            self.task_queue.enqueue(
                task_type="ocr_extract",
                payload=payload,
                priority=TaskPriority.NORMAL,
                source="watchdog",
            )

        # Enqueue brain feed
        self.task_queue.enqueue(
            task_type="brain_feed",
            payload=payload,
            priority=TaskPriority.LOW,
            source="watchdog",
        )

        # Track hash
        self._processed_hashes.add(file_hash)
        event.processed = True

    def get_stats(self) -> dict:
        """Get auto-ingest statistics."""
        depth = self.task_queue.depth()
        return {
            "known_hashes": len(self._processed_hashes),
            "queue_depth": depth,
        }

    @staticmethod
    def _quick_hash(path: str, max_bytes: int = 1048576) -> str:
        """Quick SHA-256 of first 1MB for dedup. Full hash done during processing."""
        h = hashlib.sha256()
        try:
            with open(path, "rb") as f:
                data = f.read(max_bytes)
                h.update(data)
                # Include file size for extra discrimination
                h.update(str(os.path.getsize(path)).encode())
        except Exception:
            h.update(path.encode())
        return h.hexdigest()
