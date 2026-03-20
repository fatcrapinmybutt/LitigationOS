"""Calendar View — Monthly deadline calendar visualization.

Renders a month-grid calendar highlighting dates that carry court
deadlines, with previous/next navigation.  Uses DeadlineEngine for
real deadline data from the database.
"""

from __future__ import annotations

import calendar
import logging
from datetime import date, datetime
from typing import TYPE_CHECKING

import customtkinter as ctk

from litigationos.gui.widgets import COLORS

if TYPE_CHECKING:
    from litigationos.db.connection import DatabaseManager

logger = logging.getLogger(__name__)

# Engine import -- graceful fallback
try:
    from litigationos.engines.deadline import DeadlineEngine
    _HAS_DEADLINE_ENGINE = True
except ImportError:
    _HAS_DEADLINE_ENGINE = False

_DEFAULT_DEADLINES = {
    "2026-03-15": "McNeill Disqualification",
    "2026-04-01": "MSC Original Action",
    "2026-04-15": "COA Brief 366810",
    "2026-04-30": "Watson/Shady Oaks",
    "2026-07-17": "HUD/LARA",
}


class CalendarViewFrame(ctk.CTkFrame):
    """Monthly calendar view showing deadlines and court dates."""

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
        self._current = datetime.now()
        self._deadlines: dict[str, str] = dict(_DEFAULT_DEADLINES)
        self._deadline_details: dict[str, dict] = {}
        self._build_ui()
        self._load_deadlines()
        self._render_month()

        # Detail panel frame (for click-to-view)
        self._detail_frame: ctk.CTkFrame | None = None

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_ui(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=12)
        hdr.pack(fill="x", padx=16, pady=(16, 8))

        ctk.CTkLabel(
            hdr,
            text="📅  COURT CALENDAR",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS["text"],
        ).pack(side="left", padx=16, pady=12)

        # Month navigation
        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.pack(fill="x", padx=16, pady=4)

        ctk.CTkButton(
            nav, text="◀", width=40, command=self._prev_month,
            fg_color=COLORS["bg_card"], hover_color=COLORS["accent"], corner_radius=8,
        ).pack(side="left", padx=4)

        self._month_label = ctk.CTkLabel(
            nav, text="",
            font=ctk.CTkFont(size=18, weight="bold"), text_color=COLORS["text"],
        )
        self._month_label.pack(side="left", padx=16)

        ctk.CTkButton(
            nav, text="▶", width=40, command=self._next_month,
            fg_color=COLORS["bg_card"], hover_color=COLORS["accent"], corner_radius=8,
        ).pack(side="left", padx=4)

        # Calendar grid
        self._cal_frame = ctk.CTkFrame(
            self, fg_color=COLORS["bg_card"], corner_radius=10,
        )
        self._cal_frame.pack(fill="both", expand=True, padx=16, pady=8)

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------

    def _load_deadlines(self):
        """Load deadlines from DeadlineEngine or raw DB."""
        # Try engine-backed data first
        if _HAS_DEADLINE_ENGINE and self._db:
            try:
                engine = DeadlineEngine(self._db)
                overdue = engine.get_overdue()
                upcoming = engine.get_upcoming(days=365)
                for d in overdue + upcoming:
                    due = d.get("due_date", "")
                    title = d.get("title", "Deadline")
                    priority = d.get("priority", "medium")
                    if due:
                        self._deadlines[due] = title
                        self._deadline_details[due] = {
                            "title": title,
                            "priority": priority,
                            "rule_basis": d.get("rule_basis", ""),
                            "status": d.get("status", "pending"),
                        }
                return
            except Exception:
                logger.debug("DeadlineEngine calendar load failed")

        # Fallback: raw DB query
        if not self._db:
            return
        try:
            rows = self._db.fetchall(
                "SELECT due_date, title, priority, rule_basis, status "
                "FROM deadlines WHERE status = 'pending'",
            )
            for row in rows:
                r = dict(row)
                if r.get("due_date") and r.get("title"):
                    self._deadlines[r["due_date"]] = r["title"]
                    self._deadline_details[r["due_date"]] = {
                        "title": r["title"],
                        "priority": r.get("priority", "medium"),
                        "rule_basis": r.get("rule_basis", ""),
                        "status": r.get("status", "pending"),
                    }
        except Exception:
            logger.debug("Could not load deadlines from DB")

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _render_month(self):
        for w in self._cal_frame.winfo_children():
            w.destroy()

        year = self._current.year
        month = self._current.month
        self._month_label.configure(text=f"{calendar.month_name[month]} {year}")

        for i in range(7):
            self._cal_frame.grid_columnconfigure(i, weight=1)

        # Day-of-week headers
        for i, name in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
            ctk.CTkLabel(
                self._cal_frame, text=name,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=COLORS["text_dim"],
            ).grid(row=0, column=i, padx=2, pady=4)

        # Day cells
        weeks = calendar.monthcalendar(year, month)
        for wi, week in enumerate(weeks):
            self._cal_frame.grid_rowconfigure(wi + 1, weight=1)
            for di, day in enumerate(week):
                if day == 0:
                    continue

                date_str = f"{year}-{month:02d}-{day:02d}"
                has_dl = date_str in self._deadlines

                text = str(day)
                if has_dl:
                    text = f"{day}\n{self._deadlines[date_str][:15]}"

                ctk.CTkButton(
                    self._cal_frame,
                    text=text,
                    width=60, height=60,
                    fg_color=self._date_color(date_str) if has_dl else "transparent",
                    hover_color="#AA0000" if has_dl else COLORS["accent"],
                    text_color="white" if has_dl else COLORS["text"],
                    font=ctk.CTkFont(size=10),
                    corner_radius=6,
                    command=lambda ds=date_str: self._on_date_click(ds) if ds in self._deadlines else None,
                ).grid(row=wi + 1, column=di, padx=2, pady=2, sticky="nsew")

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _prev_month(self):
        if self._current.month == 1:
            self._current = self._current.replace(year=self._current.year - 1, month=12)
        else:
            self._current = self._current.replace(month=self._current.month - 1)
        self._render_month()

    def _next_month(self):
        if self._current.month == 12:
            self._current = self._current.replace(year=self._current.year + 1, month=1)
        else:
            self._current = self._current.replace(month=self._current.month + 1)
        self._render_month()

    def _date_color(self, date_str: str) -> str:
        """Return urgency-based color for a deadline date."""
        try:
            target = date.fromisoformat(date_str)
            days = (target - date.today()).days
        except (ValueError, TypeError):
            return COLORS["red"]

        detail = self._deadline_details.get(date_str, {})
        priority = detail.get("priority", "medium")

        if days < 0:
            return "#FF0000"  # overdue
        if days <= 3 or priority == "critical":
            return "#FF3333"  # emergency
        if days <= 7 or priority == "high":
            return "#FF6600"  # critical
        if days <= 14:
            return COLORS["orange"]
        return COLORS["yellow"]

    def _on_date_click(self, date_str: str):
        """Show filing details for a clicked deadline date."""
        if self._detail_frame:
            self._detail_frame.destroy()

        detail = self._deadline_details.get(date_str, {})
        title = self._deadlines.get(date_str, "Unknown")

        self._detail_frame = ctk.CTkFrame(
            self, fg_color=COLORS["bg_card"], corner_radius=10,
        )
        self._detail_frame.pack(fill="x", padx=16, pady=4)

        ctk.CTkLabel(
            self._detail_frame, text=f"Deadline: {title}",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["text"],
        ).pack(anchor="w", padx=12, pady=(8, 2))

        ctk.CTkLabel(
            self._detail_frame, text=f"Date: {date_str}",
            font=ctk.CTkFont(size=12), text_color=COLORS["text_dim"],
        ).pack(anchor="w", padx=12, pady=1)

        if detail.get("rule_basis"):
            ctk.CTkLabel(
                self._detail_frame, text=f"Rule: {detail['rule_basis']}",
                font=ctk.CTkFont(size=12), text_color=COLORS["blue"],
            ).pack(anchor="w", padx=12, pady=1)

        if detail.get("priority"):
            p_color = {"critical": COLORS["red"], "high": COLORS["orange"],
                       "medium": COLORS["yellow"], "low": COLORS["text_dim"]}.get(
                detail["priority"], COLORS["text_dim"])
            ctk.CTkLabel(
                self._detail_frame,
                text=f"Priority: {detail['priority'].upper()}",
                font=ctk.CTkFont(size=12, weight="bold"), text_color=p_color,
            ).pack(anchor="w", padx=12, pady=(1, 8))
