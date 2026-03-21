"""First-run setup wizard for LitigationOS.

A multi-step modal dialog that collects user preferences, case info, and
data-directory configuration on the very first launch.  Uses the MBP LLC
pink/black brand palette.
"""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import Optional

import customtkinter as ctk

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# MBP LLC brand palette
# ---------------------------------------------------------------------------

BRAND_PINK = "#FF1493"
BRAND_BLACK = "#0D0D0D"
BRAND_DARK = "#1A1A1A"
BRAND_TEXT = "#F5F5F5"
BRAND_DIM = "#9E9E9E"

_US_STATES = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
    "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
    "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
    "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
    "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
    "New Hampshire", "New Jersey", "New Mexico", "New York",
    "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
    "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
    "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
    "West Virginia", "Wisconsin", "Wyoming",
]

_CASE_TYPES = [
    "Family Law", "Civil", "Criminal", "Appellate",
    "Federal", "Housing", "Other",
]

_ROLES = [
    "Pro Se Litigant", "Attorney", "Paralegal", "Student", "Other",
]

_EXPERIENCE = [
    "Beginner", "Some Experience", "Experienced", "Expert",
]

_AUTOSAVE_OPTIONS = ["1", "5", "10", "15"]

STEP_COUNT = 6


class FirstRunWizard(ctk.CTkToplevel):
    """Modal 6-step setup wizard shown on first launch."""

    def __init__(self, parent: ctk.CTk, settings_engine=None):
        super().__init__(parent)
        self.title("LitigationOS — First-Run Setup")
        self.geometry("720x620")
        self.resizable(False, False)
        self.configure(fg_color=BRAND_BLACK)

        self._parent = parent
        self._settings_engine = settings_engine
        self._step = 0
        self._completed = False

        # Collected data ------------------------------------------------
        self._disclaimer_var = ctk.BooleanVar(value=False)

        self._name_var = ctk.StringVar()
        self._email_var = ctk.StringVar()
        self._phone_var = ctk.StringVar()
        self._address_var = ctk.StringVar()
        self._role_var = ctk.StringVar(value=_ROLES[0])
        self._experience_var = ctk.StringVar(value=_EXPERIENCE[0])

        self._state_var = ctk.StringVar(value="Michigan")
        self._county_var = ctk.StringVar()
        self._court_var = ctk.StringVar()
        self._case_type_var = ctk.StringVar(value=_CASE_TYPES[0])
        self._case_number_var = ctk.StringVar()
        self._opposing_var = ctk.StringVar()

        default_dir = str(Path.home() / "LitigationOS")
        self._data_dir_var = ctk.StringVar(value=default_dir)
        self._import_db_var = ctk.BooleanVar(value=False)
        self._import_path_var = ctk.StringVar()

        self._theme_var = ctk.StringVar(value="Dark")
        self._font_size_var = ctk.IntVar(value=13)
        self._autosave_var = ctk.StringVar(value="5")
        self._analytics_var = ctk.BooleanVar(value=False)
        self._update_check_var = ctk.BooleanVar(value=True)
        self._ai_var = ctk.BooleanVar(value=True)

        # Layout --------------------------------------------------------
        self._build_progress_bar()
        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.pack(fill="both", expand=True, padx=30, pady=(0, 10))
        self._build_nav_buttons()
        self._show_step()

        # Modal behaviour -----------------------------------------------
        self.transient(parent)
        self.grab_set()
        self.focus_force()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def completed(self) -> bool:
        return self._completed

    # ------------------------------------------------------------------
    # Progress indicator
    # ------------------------------------------------------------------

    def _build_progress_bar(self):
        top = ctk.CTkFrame(self, fg_color="transparent", height=48)
        top.pack(fill="x", padx=30, pady=(18, 8))
        top.pack_propagate(False)

        self._step_label = ctk.CTkLabel(
            top, text="", font=ctk.CTkFont(size=12),
            text_color=BRAND_DIM,
        )
        self._step_label.pack(side="left")

        self._dots_frame = ctk.CTkFrame(top, fg_color="transparent")
        self._dots_frame.pack(side="right")
        self._dots: list[ctk.CTkFrame] = []
        for _ in range(STEP_COUNT):
            dot = ctk.CTkFrame(
                self._dots_frame, width=12, height=12,
                corner_radius=6, fg_color=BRAND_DIM,
            )
            dot.pack(side="left", padx=3)
            self._dots.append(dot)

    def _update_progress(self):
        self._step_label.configure(
            text=f"Step {self._step + 1} of {STEP_COUNT}",
        )
        for i, dot in enumerate(self._dots):
            dot.configure(fg_color=BRAND_PINK if i <= self._step else BRAND_DIM)

    # ------------------------------------------------------------------
    # Navigation buttons
    # ------------------------------------------------------------------

    def _build_nav_buttons(self):
        nav = ctk.CTkFrame(self, fg_color="transparent", height=50)
        nav.pack(fill="x", padx=30, pady=(0, 18))
        nav.pack_propagate(False)

        self._back_btn = ctk.CTkButton(
            nav, text="← Back", width=100, height=36,
            fg_color=BRAND_DARK, hover_color="#333333",
            text_color=BRAND_TEXT, corner_radius=8,
            command=self._prev_step,
        )
        self._back_btn.pack(side="left")

        self._next_btn = ctk.CTkButton(
            nav, text="Next →", width=100, height=36,
            fg_color=BRAND_PINK, hover_color="#CC1177",
            text_color="#FFFFFF", corner_radius=8,
            command=self._next_step,
        )
        self._next_btn.pack(side="right")

    # ------------------------------------------------------------------
    # Step rendering
    # ------------------------------------------------------------------

    def _show_step(self):
        for child in self._body.winfo_children():
            child.destroy()

        self._update_progress()

        frame = ctk.CTkFrame(self._body, fg_color="transparent")
        frame.pack(fill="both", expand=True)

        builders = [
            self._build_step_welcome,
            self._build_step_profile,
            self._build_step_case,
            self._build_step_data_dir,
            self._build_step_preferences,
            self._build_step_complete,
        ]
        builders[self._step](frame)

        # Button visibility
        self._back_btn.configure(state="normal" if self._step > 0 else "disabled")

        if self._step == STEP_COUNT - 1:
            self._next_btn.configure(text="Launch Dashboard 🚀")
        else:
            self._next_btn.configure(text="Next →")

        if self._step == 0:
            self._update_next_state()

    # ------------------------------------------------------------------
    # Step 1 — Welcome + Legal Disclaimer
    # ------------------------------------------------------------------

    def _build_step_welcome(self, frame: ctk.CTkFrame):
        ctk.CTkLabel(
            frame, text="⚖  MBP LLC",
            font=ctk.CTkFont(size=40, weight="bold"),
            text_color=BRAND_PINK,
        ).pack(pady=(18, 4))

        ctk.CTkLabel(
            frame, text="Welcome to LitigationOS™ by MBP LLC",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=BRAND_TEXT,
        ).pack(pady=(0, 18))

        disclaimer = (
            "This software is a litigation management tool designed to assist "
            "pro se litigants in organizing their legal materials. It is NOT a "
            "substitute for legal advice from a licensed attorney.\n\n"
            "By using this software, you acknowledge that MBP LLC and its "
            "developers are not providing legal counsel. All court filings "
            "should be reviewed by a qualified attorney before submission.\n\n"
            "Use at your own risk."
        )
        txt = ctk.CTkTextbox(
            frame, height=180, fg_color=BRAND_DARK,
            text_color=BRAND_TEXT, font=ctk.CTkFont(size=13),
            corner_radius=8, wrap="word", activate_scrollbars=True,
        )
        txt.pack(fill="x", pady=(0, 14))
        txt.insert("1.0", disclaimer)
        txt.configure(state="disabled")

        cb = ctk.CTkCheckBox(
            frame,
            text="I understand and agree to the above disclaimer",
            variable=self._disclaimer_var,
            font=ctk.CTkFont(size=13),
            text_color=BRAND_TEXT,
            fg_color=BRAND_PINK,
            hover_color="#CC1177",
            command=self._update_next_state,
        )
        cb.pack(anchor="w", pady=(4, 0))

    def _update_next_state(self):
        """Enable / disable Next based on step-specific validation."""
        if self._step == 0:
            state = "normal" if self._disclaimer_var.get() else "disabled"
            self._next_btn.configure(state=state)
        else:
            self._next_btn.configure(state="normal")

    # ------------------------------------------------------------------
    # Step 2 — User Profile
    # ------------------------------------------------------------------

    def _build_step_profile(self, frame: ctk.CTkFrame):
        ctk.CTkLabel(
            frame, text="Your Profile",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=BRAND_PINK,
        ).pack(anchor="w", pady=(6, 14))

        self._field(frame, "Full Name *", self._name_var)
        self._field(frame, "Email (optional)", self._email_var)
        self._field(frame, "Phone (optional)", self._phone_var)
        self._field(frame, "Address (optional)", self._address_var)

        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x", pady=4)
        self._dropdown(row, "Role", self._role_var, _ROLES, side="left")
        self._dropdown(row, "Experience", self._experience_var, _EXPERIENCE, side="right")

    # ------------------------------------------------------------------
    # Step 3 — Case Setup
    # ------------------------------------------------------------------

    def _build_step_case(self, frame: ctk.CTkFrame):
        ctk.CTkLabel(
            frame, text="Case Setup",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=BRAND_PINK,
        ).pack(anchor="w", pady=(6, 14))

        row1 = ctk.CTkFrame(frame, fg_color="transparent")
        row1.pack(fill="x", pady=4)
        self._dropdown(row1, "State", self._state_var, _US_STATES, side="left", width=200)
        self._dropdown(row1, "Case Type", self._case_type_var, _CASE_TYPES, side="right", width=200)

        self._field(frame, "County", self._county_var)
        self._field(frame, "Court", self._court_var)
        self._field(frame, "Case Number (optional)", self._case_number_var)
        self._field(frame, "Opposing Party Name (optional)", self._opposing_var)

    # ------------------------------------------------------------------
    # Step 4 — Data Directory
    # ------------------------------------------------------------------

    def _build_step_data_dir(self, frame: ctk.CTkFrame):
        ctk.CTkLabel(
            frame, text="Data Directory",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=BRAND_PINK,
        ).pack(anchor="w", pady=(6, 10))

        ctk.CTkLabel(
            frame,
            text="Where should MBP LLC store your case data?",
            font=ctk.CTkFont(size=14), text_color=BRAND_TEXT,
        ).pack(anchor="w", pady=(0, 8))

        dir_row = ctk.CTkFrame(frame, fg_color="transparent")
        dir_row.pack(fill="x", pady=4)

        dir_entry = ctk.CTkEntry(
            dir_row, textvariable=self._data_dir_var,
            fg_color=BRAND_DARK, text_color=BRAND_TEXT,
            border_color=BRAND_PINK, height=36,
        )
        dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            dir_row, text="Browse…", width=90, height=36,
            fg_color=BRAND_PINK, hover_color="#CC1177",
            text_color="#FFFFFF", corner_radius=8,
            command=self._browse_data_dir,
        ).pack(side="right")

        # Disk space
        self._disk_label = ctk.CTkLabel(
            frame, text="", font=ctk.CTkFont(size=12),
            text_color=BRAND_DIM,
        )
        self._disk_label.pack(anchor="w", pady=(4, 8))
        self._update_disk_space()
        self._data_dir_var.trace_add("write", lambda *_: self._update_disk_space())

        # Import existing DB
        ctk.CTkCheckBox(
            frame, text="Import existing database",
            variable=self._import_db_var,
            font=ctk.CTkFont(size=13), text_color=BRAND_TEXT,
            fg_color=BRAND_PINK, hover_color="#CC1177",
            command=self._toggle_import,
        ).pack(anchor="w", pady=(6, 4))

        self._import_row = ctk.CTkFrame(frame, fg_color="transparent")
        self._import_row.pack(fill="x", pady=2)

        self._import_entry = ctk.CTkEntry(
            self._import_row, textvariable=self._import_path_var,
            fg_color=BRAND_DARK, text_color=BRAND_TEXT,
            border_color=BRAND_DIM, height=32, state="disabled",
        )
        self._import_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self._import_browse = ctk.CTkButton(
            self._import_row, text="Browse…", width=80, height=32,
            fg_color=BRAND_DARK, hover_color="#333333",
            text_color=BRAND_TEXT, corner_radius=8, state="disabled",
            command=self._browse_import_db,
        )
        self._import_browse.pack(side="right")

        ctk.CTkLabel(
            frame,
            text="🔒  All data stays 100% local on your computer. Nothing is uploaded.",
            font=ctk.CTkFont(size=12), text_color=BRAND_DIM,
        ).pack(anchor="w", pady=(14, 0))

    def _browse_data_dir(self):
        path = ctk.filedialog.askdirectory(
            title="Select data directory",
            initialdir=self._data_dir_var.get(),
        )
        if path:
            self._data_dir_var.set(path)

    def _browse_import_db(self):
        path = ctk.filedialog.askopenfilename(
            title="Select database file",
            filetypes=[("SQLite databases", "*.db"), ("All files", "*.*")],
        )
        if path:
            self._import_path_var.set(path)

    def _toggle_import(self):
        state = "normal" if self._import_db_var.get() else "disabled"
        self._import_entry.configure(state=state)
        self._import_browse.configure(state=state)

    def _update_disk_space(self):
        try:
            target = self._data_dir_var.get()
            # Walk up to find an existing mount point
            check = Path(target)
            while not check.exists() and check.parent != check:
                check = check.parent
            usage = shutil.disk_usage(str(check))
            free_gb = usage.free / (1024 ** 3)
            total_gb = usage.total / (1024 ** 3)
            self._disk_label.configure(
                text=f"Disk space: {free_gb:.1f} GB free of {total_gb:.1f} GB",
            )
        except Exception:
            self._disk_label.configure(text="Disk space: unknown")

    # ------------------------------------------------------------------
    # Step 5 — Preferences
    # ------------------------------------------------------------------

    def _build_step_preferences(self, frame: ctk.CTkFrame):
        ctk.CTkLabel(
            frame, text="Preferences",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=BRAND_PINK,
        ).pack(anchor="w", pady=(6, 14))

        # Theme
        theme_row = ctk.CTkFrame(frame, fg_color="transparent")
        theme_row.pack(fill="x", pady=4)
        ctk.CTkLabel(
            theme_row, text="Theme", font=ctk.CTkFont(size=13),
            text_color=BRAND_TEXT, width=120,
        ).pack(side="left")
        ctk.CTkRadioButton(
            theme_row, text="Dark", variable=self._theme_var, value="Dark",
            text_color=BRAND_TEXT, fg_color=BRAND_PINK, hover_color="#CC1177",
        ).pack(side="left", padx=(0, 16))
        ctk.CTkRadioButton(
            theme_row, text="Light", variable=self._theme_var, value="Light",
            text_color=BRAND_TEXT, fg_color=BRAND_PINK, hover_color="#CC1177",
        ).pack(side="left")

        # Font size
        font_row = ctk.CTkFrame(frame, fg_color="transparent")
        font_row.pack(fill="x", pady=8)
        ctk.CTkLabel(
            font_row, text="Font size", font=ctk.CTkFont(size=13),
            text_color=BRAND_TEXT, width=120,
        ).pack(side="left")
        self._font_val_label = ctk.CTkLabel(
            font_row, text=str(self._font_size_var.get()),
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=BRAND_PINK, width=30,
        )
        self._font_val_label.pack(side="right", padx=(8, 0))
        slider = ctk.CTkSlider(
            font_row, from_=10, to=18, number_of_steps=8,
            variable=self._font_size_var,
            fg_color=BRAND_DARK, progress_color=BRAND_PINK,
            button_color=BRAND_PINK, button_hover_color="#CC1177",
            command=lambda v: self._font_val_label.configure(text=str(int(v))),
        )
        slider.pack(side="left", fill="x", expand=True, padx=(0, 4))

        # Auto-save
        save_row = ctk.CTkFrame(frame, fg_color="transparent")
        save_row.pack(fill="x", pady=4)
        ctk.CTkLabel(
            save_row, text="Auto-save", font=ctk.CTkFont(size=13),
            text_color=BRAND_TEXT, width=120,
        ).pack(side="left")
        ctk.CTkOptionMenu(
            save_row, variable=self._autosave_var,
            values=[f"{m} min" for m in _AUTOSAVE_OPTIONS],
            fg_color=BRAND_DARK, button_color=BRAND_PINK,
            button_hover_color="#CC1177", text_color=BRAND_TEXT,
            width=120,
        ).pack(side="left")

        # Checkboxes
        for var, text, sub in [
            (
                self._analytics_var,
                "Send anonymous usage analytics to help improve MBP LLC products",
                "Analytics include feature usage counts only. No case data, no personal info.",
            ),
            (self._update_check_var, "Check for updates on launch", ""),
            (self._ai_var, "Enable AI assistant (requires local model)", ""),
        ]:
            ctk.CTkCheckBox(
                frame, text=text, variable=var,
                font=ctk.CTkFont(size=13), text_color=BRAND_TEXT,
                fg_color=BRAND_PINK, hover_color="#CC1177",
            ).pack(anchor="w", pady=(10, 0))
            if sub:
                ctk.CTkLabel(
                    frame, text=sub,
                    font=ctk.CTkFont(size=11), text_color=BRAND_DIM,
                ).pack(anchor="w", padx=(28, 0))

    # ------------------------------------------------------------------
    # Step 6 — Completion
    # ------------------------------------------------------------------

    def _build_step_complete(self, frame: ctk.CTkFrame):
        ctk.CTkLabel(
            frame, text="✅  Setup Complete!",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=BRAND_PINK,
        ).pack(pady=(18, 10))

        summary_lines = [
            f"Name:       {self._name_var.get() or '(not set)'}",
            f"Role:       {self._role_var.get()}",
            f"Experience: {self._experience_var.get()}",
            "",
            f"State:      {self._state_var.get()}",
            f"Case Type:  {self._case_type_var.get()}",
            f"County:     {self._county_var.get() or '—'}",
            f"Court:      {self._court_var.get() or '—'}",
            f"Case #:     {self._case_number_var.get() or '—'}",
            "",
            f"Data Dir:   {self._data_dir_var.get()}",
            f"Theme:      {self._theme_var.get()}",
            f"Font Size:  {self._font_size_var.get()}",
            f"AI:         {'Enabled' if self._ai_var.get() else 'Disabled'}",
        ]

        txt = ctk.CTkTextbox(
            frame, height=220, fg_color=BRAND_DARK,
            text_color=BRAND_TEXT, font=ctk.CTkFont(family="Consolas", size=12),
            corner_radius=8, wrap="word",
        )
        txt.pack(fill="x", pady=(0, 14))
        txt.insert("1.0", "\n".join(summary_lines))
        txt.configure(state="disabled")

        ctk.CTkLabel(
            frame,
            text="Your MBP LLC LitigationOS is ready.",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=BRAND_TEXT,
        ).pack(pady=(4, 0))

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _next_step(self):
        if self._step == 0 and not self._disclaimer_var.get():
            return
        if self._step < STEP_COUNT - 1:
            self._step += 1
            self._show_step()
        else:
            self._finish()

    def _prev_step(self):
        if self._step > 0:
            self._step -= 1
            self._show_step()

    def _finish(self):
        self._save_settings()
        self._completed = True
        self.grab_release()
        self.destroy()

    def _on_close(self):
        self.grab_release()
        self.destroy()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _save_settings(self):
        """Persist wizard choices into the settings database."""
        pairs = {
            "first_run_complete": "1",
            "user_name": self._name_var.get(),
            "user_email": self._email_var.get(),
            "user_phone": self._phone_var.get(),
            "user_address": self._address_var.get(),
            "user_role": self._role_var.get(),
            "user_experience": self._experience_var.get(),
            "case_state": self._state_var.get(),
            "case_county": self._county_var.get(),
            "case_court": self._court_var.get(),
            "case_type": self._case_type_var.get(),
            "case_number": self._case_number_var.get(),
            "opposing_party": self._opposing_var.get(),
            "data_directory": self._data_dir_var.get(),
            "theme": self._theme_var.get(),
            "font_size": str(self._font_size_var.get()),
            "autosave_minutes": self._autosave_var.get().replace(" min", ""),
            "analytics_enabled": "1" if self._analytics_var.get() else "0",
            "update_check": "1" if self._update_check_var.get() else "0",
            "ai_enabled": "1" if self._ai_var.get() else "0",
        }

        if self._settings_engine is not None:
            try:
                for k, v in pairs.items():
                    self._settings_engine.set(k, v)
                logger.info("Wizard settings saved via SettingsEngine")
                return
            except Exception:
                logger.debug("SettingsEngine.set() failed, falling back to raw DB")

        # Fallback: write directly to a ``settings`` table
        db = getattr(self._parent, "db", None) or getattr(self._parent, "_db", None)
        if db is None:
            logger.warning("No database available — wizard settings not saved")
            return

        try:
            conn = db.connect()
            conn.execute(
                "CREATE TABLE IF NOT EXISTS settings "
                "(key TEXT PRIMARY KEY, value TEXT)"
            )
            for k, v in pairs.items():
                conn.execute(
                    "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                    (k, v),
                )
            conn.commit()
            conn.close()
            logger.info("Wizard settings saved to settings table")
        except Exception:
            logger.exception("Failed to save wizard settings")

    # ------------------------------------------------------------------
    # Widget helpers
    # ------------------------------------------------------------------

    def _field(self, parent: ctk.CTkFrame, label: str, var: ctk.StringVar):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=4)
        ctk.CTkLabel(
            row, text=label, font=ctk.CTkFont(size=13),
            text_color=BRAND_DIM, width=200, anchor="w",
        ).pack(side="left")
        ctk.CTkEntry(
            row, textvariable=var, fg_color=BRAND_DARK,
            text_color=BRAND_TEXT, border_color=BRAND_PINK,
            height=32,
        ).pack(side="left", fill="x", expand=True)

    def _dropdown(
        self,
        parent: ctk.CTkFrame,
        label: str,
        var: ctk.StringVar,
        values: list[str],
        *,
        side: str = "left",
        width: int = 180,
    ):
        grp = ctk.CTkFrame(parent, fg_color="transparent")
        grp.pack(side=side, padx=(0, 16))
        ctk.CTkLabel(
            grp, text=label, font=ctk.CTkFont(size=12),
            text_color=BRAND_DIM,
        ).pack(anchor="w")
        ctk.CTkOptionMenu(
            grp, variable=var, values=values, width=width,
            fg_color=BRAND_DARK, button_color=BRAND_PINK,
            button_hover_color="#CC1177", text_color=BRAND_TEXT,
        ).pack(anchor="w")
