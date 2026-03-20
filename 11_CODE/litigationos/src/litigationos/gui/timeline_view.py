"""Timeline view screen — interactive case timeline visualization.

Displays case events vertically with colour-coded event types, date-range
filtering, case/type filters, keyword search, and an add-event dialog.
"""

from __future__ import annotations

import logging
import tkinter as tk
from datetime import datetime
from tkinter import messagebox
from typing import TYPE_CHECKING, Optional

import customtkinter as ctk

if TYPE_CHECKING:
    from litigationos.app import App

logger = logging.getLogger(__name__)

# Colour mapping by event type
_TYPE_COLORS: dict[str, str] = {
    "filing": "#3B82F6",
    "hearing": "#3B82F6",
    "order": "#3B82F6",
    "communication": "#F97316",
    "incident": "#EF4444",
    "deadline": "#EF4444",
    # extended aliases
    "court": "#3B82F6",
    "evidence": "#10B981",
    "harm": "#EF4444",
}

_EVENT_TYPES = ("filing", "hearing", "order", "communication", "incident", "deadline")


class TimelineFrame(ctk.CTkFrame):
    """Interactive case timeline visualization."""

    def __init__(self, parent: ctk.CTkFrame, app: "App"):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._events: list[dict] = []

        self._build_ui()
        self.refresh()

    # -- Layout ---------------------------------------------------------------

    def _build_ui(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── Title ──
        ctk.CTkLabel(self, text="Case Timeline", font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(12, 4)
        )

        # ── Left panel: filters ──
        left = ctk.CTkFrame(self, width=220)
        left.grid(row=1, column=0, sticky="ns", padx=(12, 4), pady=8)
        left.grid_columnconfigure(0, weight=1)
        self._build_filter_panel(left)

        # ── Right panel: timeline ──
        right = ctk.CTkFrame(self)
        right.grid(row=1, column=1, sticky="nsew", padx=(4, 12), pady=8)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(0, weight=1)

        self._timeline_scroll = ctk.CTkScrollableFrame(right)
        self._timeline_scroll.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        self._timeline_scroll.grid_columnconfigure(1, weight=1)

    # -- Filters --------------------------------------------------------------

    def _build_filter_panel(self, parent: ctk.CTkFrame) -> None:
        ctk.CTkLabel(parent, text="Filters", font=ctk.CTkFont(weight="bold")).pack(
            padx=8, pady=(8, 4), anchor="w"
        )

        # Search
        ctk.CTkLabel(parent, text="Keyword", font=ctk.CTkFont(size=11)).pack(padx=8, anchor="w")
        self._search_entry = ctk.CTkEntry(parent, placeholder_text="Search events…")
        self._search_entry.pack(padx=8, fill="x")
        self._search_entry.bind("<Return>", lambda _: self._apply_filters())

        # Date range
        ctk.CTkLabel(parent, text="From Date (YYYY-MM-DD)", font=ctk.CTkFont(size=11)).pack(
            padx=8, pady=(8, 0), anchor="w"
        )
        self._date_from = ctk.CTkEntry(parent, placeholder_text="2020-01-01")
        self._date_from.pack(padx=8, fill="x")

        ctk.CTkLabel(parent, text="To Date (YYYY-MM-DD)", font=ctk.CTkFont(size=11)).pack(
            padx=8, pady=(4, 0), anchor="w"
        )
        self._date_to = ctk.CTkEntry(parent, placeholder_text="2030-12-31")
        self._date_to.pack(padx=8, fill="x")

        # Case filter
        ctk.CTkLabel(parent, text="Case", font=ctk.CTkFont(size=11)).pack(padx=8, pady=(8, 0), anchor="w")
        self._case_combo = ctk.CTkComboBox(parent, values=["All"], command=lambda _: self._apply_filters())
        self._case_combo.set("All")
        self._case_combo.pack(padx=8, fill="x")

        # Event type checkboxes
        ctk.CTkLabel(parent, text="Event Type", font=ctk.CTkFont(size=11)).pack(
            padx=8, pady=(8, 0), anchor="w"
        )
        self._type_vars: dict[str, tk.BooleanVar] = {}
        for etype in _EVENT_TYPES:
            var = tk.BooleanVar(value=True)
            self._type_vars[etype] = var
            color = _TYPE_COLORS.get(etype, "#9CA3AF")
            ctk.CTkCheckBox(
                parent, text=etype.capitalize(), variable=var,
                font=ctk.CTkFont(size=11), height=22,
                fg_color=color, hover_color=color,
                command=self._apply_filters,
            ).pack(padx=12, anchor="w")

        # Apply / Add buttons
        ctk.CTkButton(parent, text="Apply Filters", command=self._apply_filters).pack(
            padx=8, pady=(12, 4), fill="x"
        )
        ctk.CTkButton(parent, text="＋ Add Event", fg_color="#10B981", hover_color="#059669",
                       command=self._on_add_event).pack(padx=8, pady=4, fill="x")

    # -- Data -----------------------------------------------------------------

    def refresh(self) -> None:
        """Reload events from master_chronological_timeline / timeline_events."""
        self._refresh_case_combo()
        try:
            rows = self.app.db.fetchall(
                "SELECT * FROM timeline_events ORDER BY event_date ASC"
            )
            self._events = [dict(r) for r in rows]
        except Exception as exc:
            logger.warning("Failed to load timeline events: %s", exc)
            self._events = []
        self._apply_filters()

    def _refresh_case_combo(self) -> None:
        try:
            rows = self.app.db.fetchall("SELECT id, title FROM cases ORDER BY title")
            values = ["All"] + [f"{dict(r)['id']}: {dict(r)['title']}" for r in rows]
            self._case_combo.configure(values=values)
        except Exception:
            pass

    def _get_case_filter(self) -> Optional[int]:
        val = self._case_combo.get()
        if val == "All":
            return None
        try:
            return int(val.split(":")[0])
        except (ValueError, IndexError):
            return None

    def _apply_filters(self) -> None:
        items = list(self._events)

        # Case filter
        case_id = self._get_case_filter()
        if case_id is not None:
            items = [e for e in items if e.get("case_id") == case_id]

        # Type filter
        active_types = {t for t, v in self._type_vars.items() if v.get()}
        items = [e for e in items if e.get("event_type", "filing") in active_types]

        # Date range
        date_from = self._date_from.get().strip()
        date_to = self._date_to.get().strip()
        if date_from:
            items = [e for e in items if (e.get("event_date") or "") >= date_from]
        if date_to:
            items = [e for e in items if (e.get("event_date") or "") <= date_to]

        # Keyword search
        keyword = self._search_entry.get().strip().lower()
        if keyword:
            items = [
                e for e in items
                if keyword in (e.get("title") or "").lower()
                or keyword in (e.get("description") or "").lower()
            ]

        self._render_timeline(items)

    # -- Render ---------------------------------------------------------------

    def _render_timeline(self, events: list[dict]) -> None:
        for w in self._timeline_scroll.winfo_children():
            w.destroy()

        if not events:
            ctk.CTkLabel(
                self._timeline_scroll, text="No events to display.", text_color="#6B7280"
            ).grid(row=0, column=0, columnspan=2, pady=40)
            return

        for idx, ev in enumerate(events):
            etype = ev.get("event_type") or "filing"
            color = _TYPE_COLORS.get(etype, "#6B7280")
            date_str = (ev.get("event_date") or "—")[:10]

            # Date column
            date_lbl = ctk.CTkLabel(
                self._timeline_scroll, text=date_str,
                font=ctk.CTkFont(size=12, weight="bold"), text_color="#9CA3AF",
                width=100, anchor="e",
            )
            date_lbl.grid(row=idx * 2, column=0, sticky="ne", padx=(8, 12), pady=(8, 0))

            # Event card
            card = ctk.CTkFrame(self._timeline_scroll, border_width=2, border_color=color)
            card.grid(row=idx * 2, column=1, sticky="ew", padx=(0, 8), pady=(4, 0))
            card.grid_columnconfigure(0, weight=1)

            # Coloured type badge
            badge = ctk.CTkLabel(
                card, text=etype.upper(), font=ctk.CTkFont(size=10, weight="bold"),
                fg_color=color, corner_radius=4, text_color="#FFFFFF",
                width=80, height=20,
            )
            badge.grid(row=0, column=0, sticky="w", padx=8, pady=(6, 0))

            # Title
            title_lbl = ctk.CTkLabel(
                card, text=ev.get("title") or "Untitled",
                font=ctk.CTkFont(size=14, weight="bold"), anchor="w",
            )
            title_lbl.grid(row=1, column=0, sticky="ew", padx=8, pady=(2, 0))

            # Description
            desc = ev.get("description") or ""
            if desc:
                desc_lbl = ctk.CTkLabel(
                    card, text=desc[:200], anchor="w", wraplength=500,
                    font=ctk.CTkFont(size=12), text_color="#D1D5DB",
                )
                desc_lbl.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 6))

            # Connector line
            if idx < len(events) - 1:
                line = ctk.CTkLabel(
                    self._timeline_scroll, text="│", text_color="#4B5563",
                    font=ctk.CTkFont(size=14),
                )
                line.grid(row=idx * 2 + 1, column=0, sticky="e", padx=(0, 12))

    # -- Add event dialog -----------------------------------------------------

    def _on_add_event(self) -> None:
        _AddEventDialog(self, self.app, on_done=self.refresh)


class _AddEventDialog(ctk.CTkToplevel):
    """Dialog for adding a new timeline event."""

    def __init__(self, parent, app: "App", *, on_done):
        super().__init__(parent)
        self.title("Add Timeline Event")
        self.geometry("440x380")
        self.resizable(False, False)
        self.grab_set()
        self._app = app
        self._on_done = on_done

        pad = dict(padx=16, pady=3, sticky="ew")
        r = 0

        ctk.CTkLabel(self, text="Date (YYYY-MM-DD)").grid(row=r, column=0, **pad); r += 1
        self._entry_date = ctk.CTkEntry(self, placeholder_text="2024-01-15")
        self._entry_date.grid(row=r, column=0, **pad); r += 1

        ctk.CTkLabel(self, text="Title").grid(row=r, column=0, **pad); r += 1
        self._entry_title = ctk.CTkEntry(self, placeholder_text="Event title")
        self._entry_title.grid(row=r, column=0, **pad); r += 1

        ctk.CTkLabel(self, text="Description").grid(row=r, column=0, **pad); r += 1
        self._entry_desc = ctk.CTkEntry(self, placeholder_text="Description")
        self._entry_desc.grid(row=r, column=0, **pad); r += 1

        ctk.CTkLabel(self, text="Event Type").grid(row=r, column=0, **pad); r += 1
        self._combo_type = ctk.CTkComboBox(self, values=list(_EVENT_TYPES))
        self._combo_type.grid(row=r, column=0, **pad); r += 1

        ctk.CTkLabel(self, text="Case ID").grid(row=r, column=0, **pad); r += 1
        self._entry_case = ctk.CTkEntry(self, placeholder_text="Numeric case ID")
        self._entry_case.grid(row=r, column=0, **pad); r += 1

        ctk.CTkButton(self, text="Add Event", command=self._add).grid(row=r, column=0, **pad)
        self.grid_columnconfigure(0, weight=1)

    def _add(self) -> None:
        date = self._entry_date.get().strip()
        title = self._entry_title.get().strip()
        etype = self._combo_type.get()
        case_raw = self._entry_case.get().strip()
        if not date or not title or not case_raw:
            messagebox.showwarning("Add Event", "Date, title, and case ID are required.")
            return
        try:
            case_id = int(case_raw)
        except ValueError:
            messagebox.showwarning("Add Event", "Case ID must be a number.")
            return
        # Validate date format
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Add Event", "Date must be YYYY-MM-DD format.")
            return
        try:
            self._app.db.execute(
                "INSERT INTO timeline_events (case_id, event_date, title, description, event_type) "
                "VALUES (?, ?, ?, ?, ?)",
                (case_id, date, title, self._entry_desc.get().strip(), etype),
            )
            self.destroy()
            self._on_done()
        except Exception as exc:
            messagebox.showerror("Add Event", str(exc))
