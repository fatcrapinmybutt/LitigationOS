"""Deadline Dashboard — Visual countdown timers for all court deadlines.

Displays each deadline with urgency-colored countdown, court name, and
due date.  Uses DeadlineEngine for real deadline data from the DB and
falls back to built-in data when no engine data is available.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import customtkinter as ctk

from litigationos.gui.widgets import COLORS

if TYPE_CHECKING:
    from litigationos.db.connection import DatabaseManager

logger = logging.getLogger(__name__)

# Engine import -- graceful fallback if unavailable
try:
    from litigationos.engines.deadline import DeadlineEngine
    _HAS_DEADLINE_ENGINE = True
except ImportError:
    _HAS_DEADLINE_ENGINE = False

# Hard-coded fallback deadlines when no external source is available.
_DEFAULT_DEADLINES = [
    {"name": "McNeill Disqualification", "date": "2026-03-15", "court": "14th Circuit"},
    {"name": "MSC Original Action", "date": "2026-04-01", "court": "MI Supreme Court"},
    {"name": "COA Brief 366810", "date": "2026-04-15", "court": "Court of Appeals"},
    {"name": "Watson Tort", "date": "2026-04-30", "court": "14th Circuit"},
    {"name": "Shady Oaks", "date": "2026-04-30", "court": "14th Circuit"},
    {"name": "HUD/LARA Complaint", "date": "2026-07-17", "court": "Federal/Agency"},
]

_URGENCY_COLORS = {
    "OVERDUE": "#FF0000",
    "EMERGENCY": "#FF3333",
    "CRITICAL": "#FF6600",
    "URGENT": "#FFAA00",
    "APPROACHING": "#00AA00",
    "SCHEDULED": "#666666",
}


class DeadlineDashboardFrame(ctk.CTkFrame):
    """Dashboard showing all deadlines with countdown timers and urgency colors."""

    def __init__(
        self,
        parent,
        db: "DatabaseManager",
        navigate_cb=None,
        **kwargs,
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._db = db
        self._navigate_cb = navigate_cb
        self._build_ui()
        self.refresh()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_urgency(date_str: str) -> tuple[str, int]:
        today = date.today()
        try:
            target = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return "SCHEDULED", 999
        days = (target - today).days
        if days < 0:
            return "OVERDUE", days
        if days <= 3:
            return "EMERGENCY", days
        if days <= 7:
            return "CRITICAL", days
        if days <= 14:
            return "URGENT", days
        if days <= 30:
            return "APPROACHING", days
        return "SCHEDULED", days

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_ui(self):
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0,
        )
        self._scroll.pack(fill="both", expand=True)

        # Header
        hdr = ctk.CTkFrame(self._scroll, fg_color=COLORS["bg_card"], corner_radius=12)
        hdr.pack(fill="x", padx=16, pady=(16, 8))

        ctk.CTkLabel(
            hdr,
            text="⏰  DEADLINE DASHBOARD",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS["text"],
        ).pack(side="left", padx=16, pady=12)

        ctk.CTkButton(
            hdr, text="⟳  Refresh", width=100, command=self.refresh,
            fg_color=COLORS["blue"], hover_color=COLORS["accent"], corner_radius=8,
        ).pack(side="right", padx=16, pady=12)

        # Deadline list container
        self._deadline_container = ctk.CTkFrame(self._scroll, fg_color="transparent")
        self._deadline_container.pack(fill="both", expand=True, padx=16, pady=8)

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_deadlines(self) -> list[dict]:
        """Return deadline dicts from DeadlineEngine, DB, or built-in defaults."""
        # Try engine-backed data first
        if _HAS_DEADLINE_ENGINE and self._db:
            try:
                engine = DeadlineEngine(self._db)
                overdue = engine.get_overdue()
                upcoming = engine.get_upcoming(days=90)
                combined = overdue + upcoming
                if combined:
                    results = []
                    for d in combined:
                        results.append({
                            "name": d.get("title", "Deadline"),
                            "date": d.get("due_date", ""),
                            "court": d.get("rule_basis", ""),
                            "priority": d.get("priority", "medium"),
                        })
                    return results
            except Exception:
                logger.debug("DeadlineEngine query failed; trying raw DB")

        # Fallback: raw DB query
        if self._db:
            try:
                rows = self._db.fetchall(
                    "SELECT title AS name, due_date AS date, rule_basis AS court, priority "
                    "FROM deadlines WHERE status = 'pending' ORDER BY due_date",
                )
                if rows:
                    return [dict(r) for r in rows]
            except Exception:
                logger.debug("No deadlines table; using defaults")

        return list(_DEFAULT_DEADLINES)

    def _load_filing_wave(self) -> list[dict]:
        """Return filing wave plan: deadlines grouped by upcoming week."""
        if not (_HAS_DEADLINE_ENGINE and self._db):
            return []
        try:
            engine = DeadlineEngine(self._db)
            upcoming = engine.get_upcoming(days=30)
            wave: list[dict] = []
            for d in upcoming:
                due_str = d.get("due_date", "")
                try:
                    due = date.fromisoformat(due_str)
                    days_out = (due - date.today()).days
                except (ValueError, TypeError):
                    days_out = 999
                if days_out <= 7:
                    phase = "WAVE 1 (This Week)"
                elif days_out <= 14:
                    phase = "WAVE 2 (Next Week)"
                else:
                    phase = "WAVE 3 (2-4 Weeks)"
                wave.append({
                    "name": d.get("title", ""),
                    "date": due_str,
                    "phase": phase,
                    "priority": d.get("priority", "medium"),
                })
            return wave
        except Exception:
            logger.debug("Filing wave plan unavailable")
            return []

    def refresh(self):
        """Reload and re-render all deadline rows and filing wave plan."""
        for w in self._deadline_container.winfo_children():
            w.destroy()

        deadlines = sorted(self._load_deadlines(), key=lambda d: d.get("date", "9999"))

        if not deadlines:
            ctk.CTkLabel(
                self._deadline_container, text="No deadlines found",
                font=ctk.CTkFont(size=14), text_color=COLORS["text_dim"],
            ).pack(pady=16)
            return

        for dl in deadlines:
            urgency, days = self._get_urgency(dl.get("date", "2099-01-01"))
            color = _URGENCY_COLORS.get(urgency, "#666666")

            row = ctk.CTkFrame(
                self._deadline_container, fg_color=COLORS["bg_card"], corner_radius=8,
            )
            row.pack(fill="x", pady=3)
            row.columnconfigure(1, weight=1)

            ctk.CTkLabel(
                row, text=f"[{urgency}]", text_color=color,
                font=ctk.CTkFont(size=12, weight="bold"), width=110,
            ).grid(row=0, column=0, padx=10, pady=8)

            ctk.CTkLabel(
                row, text=dl.get("name", "Unknown"),
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=COLORS["text"], anchor="w",
            ).grid(row=0, column=1, padx=4, pady=8, sticky="w")

            if days < 0:
                countdown = f"OVERDUE by {abs(days)} days"
            elif days == 0:
                countdown = "DUE TODAY"
            else:
                countdown = f"{days} days remaining"

            ctk.CTkLabel(
                row, text=countdown, text_color=color,
                font=ctk.CTkFont(size=12),
            ).grid(row=0, column=2, padx=10, pady=8)

            ctk.CTkLabel(
                row, text=dl.get("court", ""),
                font=ctk.CTkFont(size=11), text_color=COLORS["text_dim"],
            ).grid(row=0, column=3, padx=10, pady=8)

            ctk.CTkLabel(
                row, text=dl.get("date", ""),
                font=ctk.CTkFont(size=11), text_color=COLORS["text_dim"],
            ).grid(row=0, column=4, padx=10, pady=8)

        # Filing wave plan section
        wave = self._load_filing_wave()
        if wave:
            ctk.CTkLabel(
                self._deadline_container,
                text="FILING WAVE PLAN",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=COLORS["text"],
            ).pack(anchor="w", padx=10, pady=(16, 4))

            current_phase = ""
            for item in wave:
                if item["phase"] != current_phase:
                    current_phase = item["phase"]
                    ctk.CTkLabel(
                        self._deadline_container,
                        text=current_phase,
                        font=ctk.CTkFont(size=13, weight="bold"),
                        text_color=COLORS["blue"],
                    ).pack(anchor="w", padx=10, pady=(8, 2))

                priority = item.get("priority", "medium")
                p_color = {
                    "critical": COLORS["red"], "high": COLORS["orange"],
                    "medium": COLORS["yellow"], "low": COLORS["text_dim"],
                }.get(priority, COLORS["text_dim"])
                wrow = ctk.CTkFrame(
                    self._deadline_container, fg_color=COLORS["bg_card"], corner_radius=6,
                )
                wrow.pack(fill="x", padx=20, pady=1)
                ctk.CTkLabel(
                    wrow, text=f"  {item['name']}  --  {item['date']}",
                    font=ctk.CTkFont(size=12), text_color=p_color, anchor="w",
                ).pack(side="left", padx=8, pady=4)
