"""
File Watchdog Engine for LitigationOS Daemon.
Monitors directories for new/changed files and auto-classifies, routes, ingests.

Uses watchdog library for cross-platform filesystem events.
Falls back to polling if watchdog is not available.
"""
import os
import re
import time
import threading
from datetime import datetime
from typing import Callable, Optional

from .models import WatchdogConfig

# MEEK lane detection patterns (from config.py MEEK_SIGNALS)
MEEK_PATTERNS = {
    "E": [  # Judicial Misconduct — highest priority
        re.compile(r"(?i)(jtc|judicial.?tenure|canon|misconduct|disqualif)"),
        re.compile(r"(?i)(mcneill|bias|ex.?parte|recusal)"),
    ],
    "D": [  # PPO
        re.compile(r"(?i)(ppo|protection.?order|stalking|2023.?5907)"),
        re.compile(r"(?i)(personal.?protection|domestic.?violence)"),
    ],
    "F": [  # Appellate
        re.compile(r"(?i)(coa|appellate|366810|appeal|msc|supreme)"),
        re.compile(r"(?i)(mcr.?7\.\d|appellant|appellee|amicus)"),
    ],
    "C": [  # Convergence (cross-lane)
        re.compile(r"(?i)(convergence|cross.?lane|unified|all.?lanes)"),
    ],
    "A": [  # Custody
        re.compile(r"(?i)(custody|parenting|visitation|best.?interest)"),
        re.compile(r"(?i)(2024.?001507|watson|alienation|bif|foc)"),
    ],
    "B": [  # Housing
        re.compile(r"(?i)(housing|shady.?oaks|landlord|tenant|eviction)"),
        re.compile(r"(?i)(2025.?002760|rico|habitability|mhp|lease)"),
    ],
}

# Document type classification
DOC_PATTERNS = {
    "motion": re.compile(r"(?i)(motion|mtn)"),
    "brief": re.compile(r"(?i)(brief|memorandum)"),
    "complaint": re.compile(r"(?i)(complaint|petition)"),
    "affidavit": re.compile(r"(?i)(affidavit|declaration|sworn)"),
    "order": re.compile(r"(?i)(order|judgment|ruling)"),
    "evidence": re.compile(r"(?i)(exhibit|evidence|proof)"),
    "transcript": re.compile(r"(?i)(transcript|hearing|deposition)"),
    "correspondence": re.compile(r"(?i)(letter|email|notice|corres)"),
    "form": re.compile(r"(?i)(scao|mc.?\d|cc.?\d|foc.?\d|form)"),
}


class FileEvent:
    """Represents a filesystem change event."""
    def __init__(self, path: str, event_type: str, timestamp: datetime = None):
        self.path = path
        self.event_type = event_type  # created, modified, deleted, moved
        self.timestamp = timestamp or datetime.utcnow()
        self.lane: Optional[str] = None
        self.doc_type: Optional[str] = None
        self.processed = False


class WatchdogEngine:
    """Monitors filesystem for changes and classifies new files."""

    def __init__(self, config: WatchdogConfig, logger=None,
                 on_event: Callable[[FileEvent], None] = None):
        self.config = config
        self.logger = logger
        self.on_event = on_event
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._observer = None
        self._event_buffer: list[FileEvent] = []

    def start(self):
        """Start the watchdog engine."""
        self._running = True

        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler

            class _Handler(FileSystemEventHandler):
                def __init__(self, engine: 'WatchdogEngine'):
                    self.engine = engine

                def on_created(self, event):
                    if not event.is_directory:
                        self.engine._handle_event(event.src_path, "created")

                def on_modified(self, event):
                    if not event.is_directory:
                        self.engine._handle_event(event.src_path, "modified")

                def on_moved(self, event):
                    if not event.is_directory:
                        self.engine._handle_event(event.dest_path, "moved")

            self._observer = Observer()
            handler = _Handler(self)

            for watch_dir in self.config.watch_dirs:
                if os.path.isdir(watch_dir):
                    self._observer.schedule(handler, watch_dir, recursive=True)
                    if self.logger:
                        self.logger.info(f"Watching: {watch_dir}")

            self._observer.start()
            if self.logger:
                self.logger.info("Watchdog engine started (native)")

        except ImportError:
            # Fallback: polling mode
            if self.logger:
                self.logger.warning("watchdog package not found, using polling")
            self._thread = threading.Thread(target=self._poll_loop, daemon=True)
            self._thread.start()

    def stop(self):
        """Stop the watchdog engine."""
        self._running = False
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5)
        if self._thread:
            self._thread.join(timeout=5)
        if self.logger:
            self.logger.info("Watchdog engine stopped")

    def _handle_event(self, path: str, event_type: str):
        """Handle a filesystem event."""
        # Check exclusions
        for pattern in self.config.exclude_patterns:
            if pattern in path:
                return

        event = FileEvent(path=path, event_type=event_type)

        # Auto-classify
        if self.config.auto_classify:
            event.doc_type = self._classify_doc(path)

        # Auto-route to lane
        if self.config.auto_lane_route:
            event.lane = self._detect_lane(path)

        if self.logger:
            lane_str = f" [Lane {event.lane}]" if event.lane else ""
            type_str = f" ({event.doc_type})" if event.doc_type else ""
            self.logger.info(
                f"File {event_type}: {os.path.basename(path)}{lane_str}{type_str}"
            )

        # Dispatch to handler
        if self.on_event:
            try:
                self.on_event(event)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Event handler error: {e}")

    def _classify_doc(self, path: str) -> Optional[str]:
        """Classify document type from filename/path."""
        name = os.path.basename(path).lower()
        full = path.lower()
        for doc_type, pattern in DOC_PATTERNS.items():
            if pattern.search(name) or pattern.search(full):
                return doc_type
        return None

    def _detect_lane(self, path: str) -> Optional[str]:
        """Detect case lane from filename/path using MEEK patterns.
        Priority: E → D → F → C → A → B
        """
        text = path.lower()
        for lane in ["E", "D", "F", "C", "A", "B"]:
            for pattern in MEEK_PATTERNS.get(lane, []):
                if pattern.search(text):
                    return lane
        return None

    def _poll_loop(self):
        """Fallback polling mode for when watchdog is not available."""
        seen: dict[str, float] = {}

        while self._running:
            for watch_dir in self.config.watch_dirs:
                if not os.path.isdir(watch_dir):
                    continue
                try:
                    for root, dirs, files in os.walk(watch_dir):
                        # Skip excluded dirs
                        dirs[:] = [
                            d for d in dirs
                            if not any(p in d for p in self.config.exclude_patterns)
                        ]
                        for f in files:
                            full = os.path.join(root, f)
                            if any(p in full for p in self.config.exclude_patterns):
                                continue
                            try:
                                mtime = os.path.getmtime(full)
                            except OSError:
                                continue
                            if full not in seen:
                                seen[full] = mtime
                                self._handle_event(full, "created")
                            elif mtime > seen[full]:
                                seen[full] = mtime
                                self._handle_event(full, "modified")
                except OSError:
                    continue

            time.sleep(self.config.poll_interval_sec)
