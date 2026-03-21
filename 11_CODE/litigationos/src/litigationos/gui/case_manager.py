"""Case manager screen — CRUD operations for litigation cases.

Provides a list view of all cases with filters, and detail forms
for creating/editing cases, parties, and claims.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

import customtkinter as ctk

from litigationos.gui.widgets import COLORS, STATUS_COLORS, StatusBadge, Tooltip

if TYPE_CHECKING:
    from litigationos.db.connection import DatabaseManager

logger = logging.getLogger(__name__)

CASE_STATUSES = ("active", "closed", "appealed", "settled")
CASE_TYPES = ("civil", "family", "criminal", "appellate", "federal")


class CaseManagerFrame(ctk.CTkFrame):
    """Case CRUD screen with list and detail views."""

    def __init__(self, parent, db: "DatabaseManager", **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._db = db
        self._selected_id: Optional[int] = None

        self._build_toolbar()
        self._build_panels()
        self.load_cases()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_toolbar(self):
        toolbar = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=10)
        toolbar.pack(fill="x", padx=16, pady=(16, 8))

        ctk.CTkLabel(
            toolbar,
            text="📁 MBP LLC — Case Manager",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["text"],
        ).pack(side="left", padx=12, pady=8)

        add_btn = ctk.CTkButton(
            toolbar,
            text="＋ Add Case",
            width=110,
            fg_color=COLORS["green"],
            hover_color="#00a381",
            corner_radius=8,
            command=self._new_case,
        )
        add_btn.pack(side="left", padx=8, pady=8)
        Tooltip(add_btn, "Create a new case with auto-generated case number")

        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self.load_cases())
        ctk.CTkEntry(
            toolbar,
            textvariable=self._search_var,
            placeholder_text="Search cases…",
            width=220,
            corner_radius=8,
        ).pack(side="right", padx=12, pady=8)

    def _build_panels(self):
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=4)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=2)

        # --- Left: case list ---
        self._list_frame = ctk.CTkScrollableFrame(
            body, fg_color=COLORS["bg_card"], corner_radius=10,
        )
        self._list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=0)

        # --- Right: detail form ---
        self._detail_frame = ctk.CTkFrame(
            body, fg_color=COLORS["bg_card"], corner_radius=10,
        )
        self._detail_frame.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=0)

        self._build_detail_form()

    def _build_detail_form(self):
        """Build the detail/edit form on the right side."""
        self._form_vars: dict[str, ctk.StringVar] = {}

        ctk.CTkLabel(
            self._detail_frame,
            text="Case Details",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w", padx=16, pady=(16, 8))

        form = ctk.CTkFrame(self._detail_frame, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        fields = [
            ("case_number", "Case Number"),
            ("title", "Title"),
            ("court", "Court"),
        ]

        for key, label in fields:
            var = ctk.StringVar()
            self._form_vars[key] = var
            ctk.CTkLabel(
                form, text=label, font=ctk.CTkFont(size=12),
                text_color=COLORS["text_dim"],
            ).pack(anchor="w", pady=(8, 0))
            ctk.CTkEntry(form, textvariable=var, corner_radius=6).pack(
                fill="x", pady=(2, 0),
            )

        # Case type dropdown
        ctk.CTkLabel(
            form, text="Case Type", font=ctk.CTkFont(size=12),
            text_color=COLORS["text_dim"],
        ).pack(anchor="w", pady=(8, 0))
        self._type_var = ctk.StringVar(value="civil")
        ctk.CTkOptionMenu(
            form,
            variable=self._type_var,
            values=list(CASE_TYPES),
            corner_radius=6,
            fg_color=COLORS["border"],
        ).pack(fill="x", pady=(2, 0))

        # Status dropdown
        ctk.CTkLabel(
            form, text="Status", font=ctk.CTkFont(size=12),
            text_color=COLORS["text_dim"],
        ).pack(anchor="w", pady=(8, 0))
        self._status_var = ctk.StringVar(value="active")
        ctk.CTkOptionMenu(
            form,
            variable=self._status_var,
            values=list(CASE_STATUSES),
            corner_radius=6,
            fg_color=COLORS["border"],
        ).pack(fill="x", pady=(2, 0))

        # Filed date
        var_filed = ctk.StringVar()
        self._form_vars["filed_date"] = var_filed
        ctk.CTkLabel(
            form, text="Filed Date (YYYY-MM-DD)", font=ctk.CTkFont(size=12),
            text_color=COLORS["text_dim"],
        ).pack(anchor="w", pady=(8, 0))
        ctk.CTkEntry(form, textvariable=var_filed, corner_radius=6).pack(
            fill="x", pady=(2, 0),
        )

        # Notes
        ctk.CTkLabel(
            form, text="Notes", font=ctk.CTkFont(size=12),
            text_color=COLORS["text_dim"],
        ).pack(anchor="w", pady=(8, 0))
        self._notes_box = ctk.CTkTextbox(
            form, height=80, corner_radius=6,
            fg_color=COLORS["border"],
        )
        self._notes_box.pack(fill="x", pady=(2, 0))

        # Buttons
        btn_row = ctk.CTkFrame(form, fg_color="transparent")
        btn_row.pack(fill="x", pady=(16, 8))

        save_btn = ctk.CTkButton(
            btn_row, text="💾  Save", width=100,
            fg_color=COLORS["green"], hover_color="#00a381",
            corner_radius=8, command=self._save_case,
        )
        save_btn.pack(side="left", padx=(0, 8))
        Tooltip(save_btn, "Save case details to database")

        cancel_btn = ctk.CTkButton(
            btn_row, text="Cancel", width=80,
            fg_color=COLORS["gray"], hover_color=COLORS["border"],
            corner_radius=8, command=self._clear_form,
        )
        cancel_btn.pack(side="left")
        Tooltip(cancel_btn, "Discard changes and reset form")

    # ------------------------------------------------------------------
    # Data operations
    # ------------------------------------------------------------------

    def load_cases(self):
        """Query cases and populate the list."""
        for w in self._list_frame.winfo_children():
            w.destroy()

        search = self._search_var.get().strip() if hasattr(self, "_search_var") else ""
        try:
            if search:
                rows = self._db.fetchall(
                    "SELECT * FROM cases WHERE title LIKE ? OR case_number LIKE ? "
                    "ORDER BY updated_at DESC",
                    (f"%{search}%", f"%{search}%"),
                )
            else:
                rows = self._db.fetchall(
                    "SELECT * FROM cases ORDER BY updated_at DESC",
                )
        except Exception:
            logger.exception("Failed to load cases")
            rows = []

        if not rows:
            ctk.CTkLabel(
                self._list_frame,
                text="No cases found" if search else "No cases yet — click Add Case",
                text_color=COLORS["text_dim"],
                font=ctk.CTkFont(size=12),
            ).pack(pady=20)
            return

        for row in rows:
            c = dict(row)
            cid = c["id"]
            frame = ctk.CTkFrame(self._list_frame, fg_color="transparent")
            frame.pack(fill="x", pady=2, padx=4)

            btn = ctk.CTkButton(
                frame,
                text=f"{c.get('case_number') or '—'}  {c['title']}",
                anchor="w",
                fg_color="transparent",
                hover_color=COLORS["bg_sidebar"],
                text_color=COLORS["text"],
                font=ctk.CTkFont(size=13),
                command=lambda case_id=cid: self._select_case(case_id),
            )
            btn.pack(side="left", fill="x", expand=True)

            StatusBadge(frame, text=c.get("status", "active")).pack(
                side="right", padx=4,
            )

    def _select_case(self, case_id: int):
        """Populate the detail form with the selected case."""
        try:
            row = self._db.fetchone("SELECT * FROM cases WHERE id = ?", (case_id,))
        except Exception:
            logger.exception("Failed to load case %d", case_id)
            return
        if row is None:
            return

        c = dict(row)
        self._selected_id = case_id
        self._form_vars["case_number"].set(c.get("case_number") or "")
        self._form_vars["title"].set(c.get("title") or "")
        self._form_vars["filed_date"].set(c.get("filed_date") or "")

        # Court: resolve court name from court_id
        court_name = ""
        if c.get("court_id"):
            try:
                court_row = self._db.fetchone(
                    "SELECT name FROM courts WHERE id = ?", (c["court_id"],),
                )
                if court_row:
                    court_name = dict(court_row).get("name", "")
            except Exception:
                pass
        self._form_vars["court"].set(court_name)

        self._type_var.set(c.get("case_type") or "civil")
        self._status_var.set(c.get("status") or "active")

        self._notes_box.delete("1.0", "end")
        if c.get("notes"):
            self._notes_box.insert("1.0", c["notes"])

    def _new_case(self):
        self._clear_form()
        self._selected_id = None
        self._form_vars["title"].set("")

    def _clear_form(self):
        self._selected_id = None
        for var in self._form_vars.values():
            var.set("")
        self._type_var.set("civil")
        self._status_var.set("active")
        self._notes_box.delete("1.0", "end")

    def _save_case(self):
        """Insert or update a case in the database."""
        title = self._form_vars["title"].get().strip()
        if not title:
            return  # title is required

        case_number = self._form_vars["case_number"].get().strip() or None
        filed_date = self._form_vars["filed_date"].get().strip() or None
        case_type = self._type_var.get()
        status = self._status_var.get()
        notes = self._notes_box.get("1.0", "end").strip() or None

        try:
            if self._selected_id is not None:
                self._db.execute(
                    "UPDATE cases SET case_number=?, title=?, case_type=?, "
                    "status=?, filed_date=?, notes=?, updated_at=datetime('now') "
                    "WHERE id=?",
                    (case_number, title, case_type, status, filed_date,
                     notes, self._selected_id),
                )
                logger.info("Updated case %d", self._selected_id)
            else:
                self._db.execute(
                    "INSERT INTO cases (case_number, title, case_type, status, "
                    "filed_date, notes) VALUES (?, ?, ?, ?, ?, ?)",
                    (case_number, title, case_type, status, filed_date, notes),
                )
                logger.info("Created new case: %s", title)
        except Exception:
            logger.exception("Failed to save case")
            return

        self.load_cases()
        self._clear_form()
