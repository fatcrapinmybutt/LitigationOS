"""Windows toast notification engine — deadline alerts, filing updates, pipeline progress.

Provides Windows toast notifications with graceful degradation:
  1. win10toast (preferred — rich toast notifications)
  2. plyer (cross-platform fallback)
  3. ctypes MessageBox (ultimate fallback — always available on Windows)

Thread-safe notification queue with dedup logic prevents notification spam.
Stores last 100 notifications in memory for history retrieval.
"""

from __future__ import annotations

import ctypes
import logging
import os
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from litigationos.db.connection import DatabaseManager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional dependency probing — never crash on missing packages
# ---------------------------------------------------------------------------

_HAS_WIN10TOAST: bool = False
_HAS_PLYER: bool = False

try:
    from win10toast import ToastNotifier  # type: ignore[import-untyped]

    _HAS_WIN10TOAST = True
    logger.debug("win10toast available — using native Windows toasts")
except ImportError:
    ToastNotifier = None  # type: ignore[assignment,misc]

if not _HAS_WIN10TOAST:
    try:
        from plyer import notification as plyer_notification  # type: ignore[import-untyped]

        _HAS_PLYER = True
        logger.debug("plyer available — using cross-platform notifications")
    except ImportError:
        plyer_notification = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_ICON = r"C:\Users\andre\Pictures\LitigationOS-Pig-Icon.ico"
_MAX_HISTORY = 100
_DEDUP_WINDOW_SECONDS = 300  # 5 minutes
_URGENCY_LEVELS = ("low", "normal", "warning", "critical")

# Urgency → MB_ICON flag for ctypes fallback
_MB_ICON_MAP = {
    "low": 0x00000040,        # MB_ICONINFORMATION
    "normal": 0x00000040,     # MB_ICONINFORMATION
    "warning": 0x00000030,    # MB_ICONWARNING
    "critical": 0x00000010,   # MB_ICONERROR
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class _NotificationRecord:
    """Internal record for a sent notification."""

    timestamp: datetime
    title: str
    message: str
    urgency: str
    backend: str
    success: bool


@dataclass
class _Preferences:
    """User notification preferences."""

    enabled: bool = True
    sound: bool = True
    urgency_threshold: str = "normal"


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class NotificationEngine:
    """Windows toast notification engine with dedup, history, and deadline scheduling.

    Parameters
    ----------
    db : DatabaseManager, optional
        Database connection for querying upcoming deadlines.  When *None*,
        deadline-scheduled checks are disabled but manual notifications still work.
    """

    def __init__(self, db: Optional["DatabaseManager"] = None) -> None:
        self._db = db

        # Backend setup
        self._toaster: Optional[ToastNotifier] = None  # type: ignore[type-arg]
        if _HAS_WIN10TOAST and ToastNotifier is not None:
            try:
                self._toaster = ToastNotifier()
            except Exception:
                logger.warning("win10toast found but ToastNotifier() init failed")

        # Icon resolution
        self._icon_path = _DEFAULT_ICON if os.path.isfile(_DEFAULT_ICON) else ""

        # Thread-safe history & dedup
        self._lock = threading.Lock()
        self._history: deque[_NotificationRecord] = deque(maxlen=_MAX_HISTORY)
        self._recent_keys: dict[tuple[str, str], datetime] = {}

        # Preferences
        self._prefs = _Preferences()

        # Scheduler state
        self._scheduler_thread: Optional[threading.Thread] = None
        self._scheduler_stop = threading.Event()

        backend = self._describe_backend()
        logger.info("NotificationEngine initialised — backend=%s", backend)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def notify(
        self,
        title: str,
        message: str,
        icon_path: str = "",
        duration: int = 5,
        urgency: str = "normal",
    ) -> bool:
        """Send a toast notification.

        Parameters
        ----------
        title : str
            Notification title / headline.
        message : str
            Body text (kept short for toast readability).
        icon_path : str
            Path to a ``.ico`` file.  Falls back to the default pig icon.
        duration : int
            Seconds the toast stays visible (win10toast / plyer only).
        urgency : str
            One of ``"low"``, ``"normal"``, ``"warning"``, ``"critical"``.

        Returns
        -------
        bool
            *True* if the notification was delivered (or at least attempted).
        """
        if urgency not in _URGENCY_LEVELS:
            urgency = "normal"

        # Preferences gate
        if not self._prefs.enabled:
            logger.debug("Notifications disabled — suppressing: %s", title)
            return False

        if not self._passes_threshold(urgency):
            logger.debug(
                "Urgency %s below threshold %s — suppressing: %s",
                urgency,
                self._prefs.urgency_threshold,
                title,
            )
            return False

        # Dedup gate
        if self._is_duplicate(title, message):
            logger.debug("Duplicate suppressed (within 5 min): %s", title)
            return False

        icon = icon_path or self._icon_path
        success = self._dispatch(title, message, icon, duration, urgency)

        # Record history
        backend = self._describe_backend()
        record = _NotificationRecord(
            timestamp=datetime.now(),
            title=title,
            message=message,
            urgency=urgency,
            backend=backend,
            success=success,
        )
        with self._lock:
            self._history.append(record)

        if success:
            logger.info("Toast sent [%s]: %s", urgency, title)
        else:
            logger.warning("Toast delivery failed: %s", title)

        return success

    def notify_deadline(self, deadline: dict) -> bool:
        """Format and send a deadline alert notification.

        Parameters
        ----------
        deadline : dict
            Must contain ``"title"`` and ``"due_date"`` keys.
            Optional: ``"days_remaining"``, ``"case_number"``.

        Returns
        -------
        bool
            Delivery result.
        """
        title_text = deadline.get("title", "Upcoming Deadline")
        due_date = deadline.get("due_date", "unknown")
        days = deadline.get("days_remaining")
        case_num = deadline.get("case_number", "")

        # Determine urgency from days remaining
        if days is not None:
            if days <= 1:
                urgency = "critical"
                prefix = "🔴 URGENT"
            elif days <= 7:
                urgency = "warning"
                prefix = "🟡 WARNING"
            elif days <= 14:
                urgency = "normal"
                prefix = "📅 Reminder"
            else:
                urgency = "low"
                prefix = "📋 Upcoming"
        else:
            urgency = "normal"
            prefix = "📅 Deadline"

        title = f"{prefix}: {title_text}"
        parts = [f"Due: {due_date}"]
        if days is not None:
            parts.append(f"{days} day{'s' if days != 1 else ''} remaining")
        if case_num:
            parts.append(f"Case {case_num}")
        message = " | ".join(parts)

        return self.notify(title, message, urgency=urgency)

    def notify_filing_ready(self, filing_id: str, filing_title: str) -> bool:
        """Notify the user that a filing package is ready for review.

        Parameters
        ----------
        filing_id : str
            Internal filing identifier.
        filing_title : str
            Human-readable filing name (e.g. ``"Motion to Disqualify"``).

        Returns
        -------
        bool
            Delivery result.
        """
        title = f"📄 Filing Ready: {filing_title}"
        message = f"Filing {filing_id} is assembled and ready for review."
        return self.notify(title, message, urgency="normal")

    def notify_pipeline_complete(self, phase: str, stats: dict) -> bool:
        """Notify the user that a pipeline phase has completed.

        Parameters
        ----------
        phase : str
            Phase identifier (e.g. ``"phase_4a"``).
        stats : dict
            Phase statistics — common keys: ``"processed"``, ``"errors"``,
            ``"duration_sec"``.

        Returns
        -------
        bool
            Delivery result.
        """
        processed = stats.get("processed", 0)
        errors = stats.get("errors", 0)
        duration = stats.get("duration_sec", 0)

        urgency = "warning" if errors > 0 else "normal"
        title = f"⚙️ Pipeline {phase} complete"
        parts = [f"{processed} processed"]
        if errors:
            parts.append(f"{errors} errors")
        if duration:
            parts.append(f"{duration:.0f}s")
        message = " | ".join(parts)

        return self.notify(title, message, urgency=urgency)

    def notify_evidence_found(self, count: int, source: str) -> bool:
        """Notify the user that new evidence has been discovered.

        Parameters
        ----------
        count : int
            Number of new evidence items.
        source : str
            Where the evidence was found (e.g. drive letter, folder name).

        Returns
        -------
        bool
            Delivery result.
        """
        title = f"🔍 {count} new evidence item{'s' if count != 1 else ''}"
        message = f"Source: {source}"
        return self.notify(title, message, urgency="normal")

    def notify_error(self, error_msg: str, context: str = "") -> bool:
        """Send an error notification.

        Parameters
        ----------
        error_msg : str
            Short error description.
        context : str
            Optional additional context (module, phase, etc.).

        Returns
        -------
        bool
            Delivery result.
        """
        title = "❌ LitigationOS Error"
        parts = [error_msg]
        if context:
            parts.append(f"Context: {context}")
        message = " | ".join(parts)
        return self.notify(title, message, urgency="critical")

    # ------------------------------------------------------------------
    # Scheduler
    # ------------------------------------------------------------------

    def schedule_deadline_checks(self, interval_minutes: int = 60) -> None:
        """Start a background thread that periodically checks for upcoming deadlines.

        Queries the database for deadlines due within 7 days and sends toast
        notifications for each one.  No-ops gracefully if no database is
        configured.

        Parameters
        ----------
        interval_minutes : int
            Minutes between each check cycle.
        """
        if self._scheduler_thread is not None and self._scheduler_thread.is_alive():
            logger.warning("Deadline scheduler already running — ignoring duplicate start")
            return

        if self._db is None:
            logger.warning("No database configured — deadline scheduler disabled")
            return

        self._scheduler_stop.clear()
        self._scheduler_thread = threading.Thread(
            target=self._deadline_check_loop,
            args=(interval_minutes,),
            daemon=True,
            name="notification-deadline-scheduler",
        )
        self._scheduler_thread.start()
        logger.info(
            "Deadline scheduler started — checking every %d min", interval_minutes
        )

    def stop_scheduler(self) -> None:
        """Stop the background deadline-check thread (if running)."""
        if self._scheduler_thread is None or not self._scheduler_thread.is_alive():
            logger.debug("No scheduler running — nothing to stop")
            return

        self._scheduler_stop.set()
        self._scheduler_thread.join(timeout=10)
        logger.info("Deadline scheduler stopped")

    # ------------------------------------------------------------------
    # History & Preferences
    # ------------------------------------------------------------------

    def get_notification_history(self) -> list[dict]:
        """Return the most recent notifications (up to 100).

        Returns
        -------
        list[dict]
            Each dict contains ``timestamp``, ``title``, ``message``,
            ``urgency``, ``backend``, ``success``.
        """
        with self._lock:
            return [
                {
                    "timestamp": r.timestamp.isoformat(),
                    "title": r.title,
                    "message": r.message,
                    "urgency": r.urgency,
                    "backend": r.backend,
                    "success": r.success,
                }
                for r in reversed(self._history)  # newest first
            ]

    def set_preferences(
        self,
        enabled: bool = True,
        sound: bool = True,
        urgency_threshold: str = "normal",
    ) -> None:
        """Update notification preferences.

        Parameters
        ----------
        enabled : bool
            Master switch — *False* suppresses all notifications.
        sound : bool
            Play a sound with the notification (win10toast only).
        urgency_threshold : str
            Minimum urgency to actually show (``"low"`` shows everything).
        """
        if urgency_threshold not in _URGENCY_LEVELS:
            urgency_threshold = "normal"

        self._prefs = _Preferences(
            enabled=enabled,
            sound=sound,
            urgency_threshold=urgency_threshold,
        )
        logger.info(
            "Notification preferences updated: enabled=%s sound=%s threshold=%s",
            enabled,
            sound,
            urgency_threshold,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _describe_backend(self) -> str:
        """Return a human-readable name for the active notification backend."""
        if self._toaster is not None:
            return "win10toast"
        if _HAS_PLYER:
            return "plyer"
        return "ctypes_messagebox"

    def _passes_threshold(self, urgency: str) -> bool:
        """Check whether *urgency* meets or exceeds the configured threshold."""
        try:
            return _URGENCY_LEVELS.index(urgency) >= _URGENCY_LEVELS.index(
                self._prefs.urgency_threshold
            )
        except ValueError:
            return True

    def _is_duplicate(self, title: str, message: str) -> bool:
        """Return *True* if the same (title, message) was sent within the dedup window."""
        key = (title, message)
        now = datetime.now()
        with self._lock:
            # Prune stale entries while we're here
            cutoff = now - timedelta(seconds=_DEDUP_WINDOW_SECONDS)
            stale = [k for k, ts in self._recent_keys.items() if ts < cutoff]
            for k in stale:
                del self._recent_keys[k]

            if key in self._recent_keys:
                return True

            self._recent_keys[key] = now
        return False

    def _dispatch(
        self,
        title: str,
        message: str,
        icon: str,
        duration: int,
        urgency: str,
    ) -> bool:
        """Send via the best available backend.  Returns success flag."""
        # Attempt 1: win10toast
        if self._toaster is not None:
            return self._send_win10toast(title, message, icon, duration)

        # Attempt 2: plyer
        if _HAS_PLYER:
            return self._send_plyer(title, message, icon, duration)

        # Attempt 3: ctypes MessageBox (always available on Windows)
        return self._send_messagebox(title, message, urgency)

    def _send_win10toast(
        self, title: str, message: str, icon: str, duration: int
    ) -> bool:
        """Dispatch via win10toast.  Non-blocking (threaded=True)."""
        try:
            icon_arg = icon if icon and os.path.isfile(icon) else None
            self._toaster.show_toast(  # type: ignore[union-attr]
                title,
                message,
                icon_path=icon_arg,
                duration=duration,
                threaded=True,
            )
            return True
        except Exception:
            logger.exception("win10toast delivery failed")
            return False

    def _send_plyer(
        self, title: str, message: str, icon: str, duration: int
    ) -> bool:
        """Dispatch via plyer.notification."""
        try:
            kwargs: dict = {
                "title": title,
                "message": message,
                "timeout": duration,
            }
            if icon and os.path.isfile(icon):
                kwargs["app_icon"] = icon
            plyer_notification.notify(**kwargs)  # type: ignore[union-attr]
            return True
        except Exception:
            logger.exception("plyer delivery failed")
            return False

    @staticmethod
    def _send_messagebox(title: str, message: str, urgency: str) -> bool:
        """Dispatch via ctypes MessageBox — always available on Windows."""
        try:
            icon_flag = _MB_ICON_MAP.get(urgency, 0x00000040)
            # MB_OK | MB_SYSTEMMODAL | icon
            flags = 0x00000000 | 0x00001000 | icon_flag
            ctypes.windll.user32.MessageBoxW(0, message, title, flags)  # type: ignore[attr-defined]
            return True
        except Exception:
            logger.exception("ctypes MessageBox delivery failed")
            return False

    # ------------------------------------------------------------------
    # Deadline scheduler loop
    # ------------------------------------------------------------------

    def _deadline_check_loop(self, interval_minutes: int) -> None:
        """Background loop that queries for upcoming deadlines and notifies."""
        logger.debug("Deadline check loop entered (interval=%d min)", interval_minutes)
        while not self._scheduler_stop.is_set():
            try:
                self._check_deadlines()
            except Exception:
                logger.exception("Error during scheduled deadline check")

            # Sleep in small increments so stop_scheduler responds quickly
            for _ in range(interval_minutes * 6):
                if self._scheduler_stop.is_set():
                    return
                time.sleep(10)

    def _check_deadlines(self) -> None:
        """Query the database for deadlines due within 7 days and notify."""
        if self._db is None:
            return

        try:
            rows = self._db.fetchall(
                """
                SELECT title, due_date, days_remaining, case_number
                FROM deadlines
                WHERE days_remaining IS NOT NULL
                  AND days_remaining <= 7
                  AND status != 'completed'
                ORDER BY days_remaining ASC
                LIMIT 10
                """,
            )
        except Exception:
            # Table may not exist or schema mismatch — degrade gracefully
            logger.debug("Could not query deadlines table — skipping check")
            return

        if not rows:
            logger.debug("No upcoming deadlines within 7 days")
            return

        for row in rows:
            deadline = {
                "title": row.get("title", row.get(0, "Deadline")),
                "due_date": row.get("due_date", row.get(1, "")),
                "days_remaining": row.get("days_remaining", row.get(2)),
                "case_number": row.get("case_number", row.get(3, "")),
            }
            self.notify_deadline(deadline)
