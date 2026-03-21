"""Splash screen and enhanced onboarding wizard for LitigationOS.

Provides two top-level windows:

* **SplashScreen** — A borderless, animated splash shown on launch with
  MBP LLC branding, a progress bar, and cycling status messages.  Fades in
  via ``wm_attributes('-alpha', …)`` and auto-closes after ~3 s.

* **OnboardingWizard** — An eight-step post-splash setup wizard that
  collects case info, drive selection, download location, notification
  preferences, and analytics opt-in.  Persists results to
  ``~/.litigationos/config.json``.

Both windows use the MBP LLC pink (#FF1493) / black (#0D0D0D) theme and
import shared colour constants from :pymod:`litigationos.gui.widgets`.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional

import customtkinter as ctk

from litigationos.gui.widgets import COLORS, Tooltip

if TYPE_CHECKING:
    from litigationos.db.connection import DatabaseManager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Brand constants (mirrors widgets.COLORS for quick reference)
# ---------------------------------------------------------------------------

BRAND_PINK: str = COLORS["accent"]           # #FF1493
BRAND_PINK_HOVER: str = COLORS["accent_hover"]  # #FF69B4
BRAND_PINK_DIM: str = COLORS["accent_dim"]    # #C71585
BRAND_BLACK: str = COLORS["bg_dark"]          # #0D0D0D
BRAND_CARD: str = COLORS["bg_card"]           # #1A1A1A
BRAND_TEXT: str = COLORS["text"]              # #F5F5F5
BRAND_DIM: str = COLORS["text_dim"]           # #9E9E9E
BRAND_BORDER: str = COLORS["border"]          # #2A2A2A
BRAND_GREEN: str = COLORS["green"]            # #00E676

# Default path for generated filings
_DEFAULT_FILING_DIR: str = str(
    Path.home() / "Desktop" / "LitigationOS_Filings"
)

# Config persistence directory
_CONFIG_DIR: Path = Path.home() / ".litigationos"
_CONFIG_FILE: Path = _CONFIG_DIR / "config.json"

# Icon path (optional — pig emoji used as fallback)
_ICON_PATH: Path = Path(r"C:\Users\andre\Pictures\LitigationOS-Pig-Icon.ico")

# Splash loading messages
_LOADING_MESSAGES: list[str] = [
    "Initializing engines…",
    "Loading legal knowledge…",
    "Connecting to database…",
    "Preparing your arsenal…",
    "Ready to fight.",
]

# Michigan counties for case setup dropdown
_MI_COUNTIES: list[str] = [
    "Alcona", "Alger", "Allegan", "Alpena", "Antrim", "Arenac",
    "Baraga", "Barry", "Bay", "Benzie", "Berrien", "Branch",
    "Calhoun", "Cass", "Charlevoix", "Cheboygan", "Chippewa",
    "Clare", "Clinton", "Crawford", "Delta", "Dickinson", "Eaton",
    "Emmet", "Genesee", "Gladwin", "Gogebic", "Grand Traverse",
    "Gratiot", "Hillsdale", "Houghton", "Huron", "Ingham", "Ionia",
    "Iosco", "Iron", "Isabella", "Jackson", "Kalamazoo", "Kalkaska",
    "Kent", "Keweenaw", "Lake", "Lapeer", "Leelanau", "Lenawee",
    "Livingston", "Luce", "Mackinac", "Macomb", "Manistee",
    "Marquette", "Mason", "Mecosta", "Menominee", "Midland",
    "Missaukee", "Monroe", "Montcalm", "Montmorency", "Muskegon",
    "Newaygo", "Oakland", "Oceana", "Ogemaw", "Ontonagon",
    "Osceola", "Oscoda", "Otsego", "Ottawa", "Presque Isle",
    "Roscommon", "Saginaw", "Sanilac", "Schoolcraft", "Shiawassee",
    "St. Clair", "St. Joseph", "Tuscola", "Van Buren", "Washtenaw",
    "Wayne", "Wexford",
]

# Default drives available for scanning
_SCAN_DRIVES: list[str] = ["C:\\", "D:\\", "F:\\", "G:\\", "H:\\", "I:\\"]

# Urgency threshold options
_URGENCY_OPTIONS: list[str] = [
    "Critical only",
    "High and above",
    "Medium and above",
    "All notifications",
]


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  SplashScreen                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝


class SplashScreen(ctk.CTkToplevel):
    """Borderless, animated splash window with MBP LLC branding.

    Parameters
    ----------
    parent:
        The root ``CTk`` window.
    on_complete:
        Callback invoked when the splash closes (typically launches the
        main application window or the onboarding wizard).
    duration_ms:
        Total display time in milliseconds (default 3 000).
    """

    # -- construction --------------------------------------------------------

    def __init__(
        self,
        parent: ctk.CTk,
        on_complete: Optional[Callable[[], None]] = None,
        duration_ms: int = 3000,
    ) -> None:
        super().__init__(parent)

        self._parent = parent
        self._on_complete = on_complete
        self._duration_ms = duration_ms
        self._current_msg_idx: int = 0
        self._alpha: float = 0.0
        self._progress: float = 0.0
        self._closed: bool = False

        # -- window chrome ---------------------------------------------------
        self.overrideredirect(True)  # borderless
        self.configure(fg_color=BRAND_BLACK)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.0)  # start fully transparent

        # Dimensions & centering
        width, height = 600, 400
        self.geometry(f"{width}x{height}")
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

        # Try to set .ico on the underlying Tk window (non-fatal)
        if _ICON_PATH.exists():
            try:
                self.iconbitmap(str(_ICON_PATH))
            except Exception:
                pass

        # -- layout ----------------------------------------------------------
        self._build_ui()

        # -- animations ------------------------------------------------------
        self._fade_in()

    # -- UI construction -----------------------------------------------------

    def _build_ui(self) -> None:
        """Assemble the splash layout: logo, title, tagline, bar, status."""
        container = ctk.CTkFrame(self, fg_color=BRAND_BLACK)
        container.pack(fill="both", expand=True)

        # Decorative accent line at top
        accent_bar = ctk.CTkFrame(container, fg_color=BRAND_PINK, height=3)
        accent_bar.pack(fill="x", side="top")

        inner = ctk.CTkFrame(container, fg_color=BRAND_BLACK)
        inner.pack(expand=True)

        # Logo — use icon image if available, otherwise pig emoji placeholder
        logo_text = "🐷"
        self._logo_label = ctk.CTkLabel(
            inner,
            text=logo_text,
            font=ctk.CTkFont(size=64),
            text_color=BRAND_PINK,
        )
        self._logo_label.pack(pady=(0, 4))

        # Title
        ctk.CTkLabel(
            inner,
            text="LitigationOS",
            font=ctk.CTkFont(family="Segoe UI", size=40, weight="bold"),
            text_color=BRAND_TEXT,
        ).pack(pady=(0, 2))

        # Subtitle
        ctk.CTkLabel(
            inner,
            text="by MBP LLC",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=BRAND_DIM,
        ).pack(pady=(0, 6))

        # Tagline
        ctk.CTkLabel(
            inner,
            text="Level the Playing Field",
            font=ctk.CTkFont(family="Segoe UI", size=16, slant="italic"),
            text_color=BRAND_PINK,
        ).pack(pady=(0, 24))

        # Progress bar
        self._progress_bar = ctk.CTkProgressBar(
            inner,
            width=400,
            height=6,
            corner_radius=3,
            fg_color=BRAND_BORDER,
            progress_color=BRAND_PINK,
        )
        self._progress_bar.pack(pady=(0, 12))
        self._progress_bar.set(0.0)

        # Status text
        self._status_label = ctk.CTkLabel(
            inner,
            text=_LOADING_MESSAGES[0],
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=BRAND_DIM,
        )
        self._status_label.pack()

        # Bottom accent line
        accent_bar_bottom = ctk.CTkFrame(container, fg_color=BRAND_PINK, height=3)
        accent_bar_bottom.pack(fill="x", side="bottom")

    # -- animations ----------------------------------------------------------

    def _fade_in(self) -> None:
        """Gradually increase window opacity from 0 → 1 then start loading."""
        if self._closed:
            return
        self._alpha += 0.05
        if self._alpha >= 1.0:
            self._alpha = 1.0
            self.attributes("-alpha", 1.0)
            self._start_loading()
            return
        self.attributes("-alpha", self._alpha)
        self.after(20, self._fade_in)

    def _start_loading(self) -> None:
        """Cycle through loading messages and advance the progress bar."""
        msg_count = len(_LOADING_MESSAGES)
        interval = self._duration_ms // msg_count
        self._tick_loading(interval, msg_count)

    def _tick_loading(self, interval_ms: int, total_steps: int) -> None:
        """Advance one loading step."""
        if self._closed:
            return
        idx = self._current_msg_idx
        if idx >= total_steps:
            self._finish()
            return

        self._status_label.configure(text=_LOADING_MESSAGES[idx])
        self._progress = (idx + 1) / total_steps
        self._progress_bar.set(self._progress)
        self._current_msg_idx += 1
        self.after(interval_ms, self._tick_loading, interval_ms, total_steps)

    def _finish(self) -> None:
        """Close splash and invoke the completion callback."""
        if self._closed:
            return
        self._closed = True
        self.after(300, self._destroy_and_callback)

    def _destroy_and_callback(self) -> None:
        """Destroy the window then fire ``on_complete``."""
        try:
            self.destroy()
        except Exception:
            pass
        if self._on_complete:
            self._on_complete()

    # -- public helpers ------------------------------------------------------

    def force_close(self) -> None:
        """Immediately dismiss the splash (e.g. if loading finished early)."""
        self._finish()


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  OnboardingWizard                                                       ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

_ONBOARDING_STEPS: list[str] = [
    "Welcome",
    "Disclaimer",
    "Case Setup",
    "Drives",
    "Downloads",
    "Notifications",
    "Analytics",
    "Ready",
]

STEP_COUNT: int = len(_ONBOARDING_STEPS)


class OnboardingWizard(ctk.CTkToplevel):
    """Eight-step post-splash onboarding wizard.

    Collects case information, drive selection, notification preferences,
    and analytics opt-in.  Results are persisted to
    ``~/.litigationos/config.json``.

    Parameters
    ----------
    parent:
        The root ``CTk`` window.
    on_complete:
        Callback receiving the ``dict`` of wizard results when the user
        clicks *Launch LitigationOS* on the final step.
    db:
        Optional :class:`DatabaseManager` for seeding initial case data.
    """

    def __init__(
        self,
        parent: ctk.CTk,
        on_complete: Optional[Callable[[dict[str, Any]], None]] = None,
        db: Optional["DatabaseManager"] = None,
    ) -> None:
        super().__init__(parent)

        self._parent = parent
        self._on_complete = on_complete
        self._db: Optional["DatabaseManager"] = db
        self._current_step: int = 0

        # Collected data (populated as user progresses)
        self._data: dict[str, Any] = {
            "disclaimer_accepted": False,
            "case_name": "",
            "court": "",
            "county": "",
            "case_number": "",
            "judge_name": "",
            "scan_drives": [],
            "custom_scan_path": "",
            "download_location": _DEFAULT_FILING_DIR,
            "notifications_enabled": True,
            "sound_enabled": True,
            "urgency_threshold": "Medium and above",
            "analytics_usage": False,
            "analytics_court_profiling": False,
        }

        # -- window chrome ---------------------------------------------------
        self.title("LitigationOS — Setup Wizard")
        self.geometry("780x620")
        self.resizable(False, False)
        self.configure(fg_color=BRAND_BLACK)
        self.transient(parent)
        self.grab_set()
        self.focus_force()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Center on screen
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - 780) // 2
        y = (sh - 620) // 2
        self.geometry(f"780x620+{x}+{y}")

        if _ICON_PATH.exists():
            try:
                self.iconbitmap(str(_ICON_PATH))
            except Exception:
                pass

        # -- top-level layout ------------------------------------------------
        self._build_chrome()

        # Step frames (lazy-built on first visit)
        self._step_frames: list[Optional[ctk.CTkFrame]] = [None] * STEP_COUNT
        self._build_step(0)
        self._show_step(0)

    # ── chrome (step indicator + nav buttons) ───────────────────────────────

    def _build_chrome(self) -> None:
        """Build the fixed header (step indicator) and footer (nav buttons)."""
        # Header — step indicator dots
        self._header = ctk.CTkFrame(self, fg_color=BRAND_BLACK, height=50)
        self._header.pack(fill="x", padx=20, pady=(16, 0))

        self._dot_labels: list[ctk.CTkLabel] = []
        dot_container = ctk.CTkFrame(self._header, fg_color="transparent")
        dot_container.pack(expand=True)

        for i, name in enumerate(_ONBOARDING_STEPS):
            dot_frame = ctk.CTkFrame(dot_container, fg_color="transparent")
            dot_frame.pack(side="left", padx=6)

            dot = ctk.CTkLabel(
                dot_frame,
                text=str(i + 1),
                width=28,
                height=28,
                corner_radius=14,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=BRAND_PINK if i == 0 else BRAND_BORDER,
                text_color=BRAND_TEXT,
            )
            dot.pack()

            lbl = ctk.CTkLabel(
                dot_frame,
                text=name,
                font=ctk.CTkFont(size=9),
                text_color=BRAND_PINK if i == 0 else BRAND_DIM,
            )
            lbl.pack(pady=(2, 0))
            self._dot_labels.append((dot, lbl))  # type: ignore[arg-type]

        # Separator
        ctk.CTkFrame(self, fg_color=BRAND_BORDER, height=1).pack(
            fill="x", padx=20, pady=(12, 0),
        )

        # Content area (each step frame packed here)
        self._content = ctk.CTkFrame(self, fg_color=BRAND_BLACK)
        self._content.pack(fill="both", expand=True, padx=20, pady=(8, 0))

        # Footer separator
        ctk.CTkFrame(self, fg_color=BRAND_BORDER, height=1).pack(
            fill="x", padx=20, pady=(0, 0),
        )

        # Footer — nav buttons
        self._footer = ctk.CTkFrame(self, fg_color=BRAND_BLACK, height=56)
        self._footer.pack(fill="x", padx=20, pady=(8, 16))

        self._back_btn = ctk.CTkButton(
            self._footer,
            text="← Back",
            width=100,
            fg_color=BRAND_CARD,
            hover_color=BRAND_BORDER,
            text_color=BRAND_TEXT,
            font=ctk.CTkFont(size=13),
            command=self._go_back,
        )
        self._back_btn.pack(side="left")

        self._next_btn = ctk.CTkButton(
            self._footer,
            text="Next →",
            width=100,
            fg_color=BRAND_PINK,
            hover_color=BRAND_PINK_HOVER,
            text_color=BRAND_TEXT,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._go_next,
        )
        self._next_btn.pack(side="right")

        # Error label (inline validation)
        self._error_label = ctk.CTkLabel(
            self._footer,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["red"],
        )
        self._error_label.pack(side="right", padx=(0, 16))

    # ── step indicator update ───────────────────────────────────────────────

    def _update_dots(self) -> None:
        """Refresh the header dots to highlight the current step."""
        for i, (dot, lbl) in enumerate(self._dot_labels):
            if i < self._current_step:
                dot.configure(fg_color=BRAND_GREEN, text_color=BRAND_TEXT)
                lbl.configure(text_color=BRAND_GREEN)
            elif i == self._current_step:
                dot.configure(fg_color=BRAND_PINK, text_color=BRAND_TEXT)
                lbl.configure(text_color=BRAND_PINK)
            else:
                dot.configure(fg_color=BRAND_BORDER, text_color=BRAND_DIM)
                lbl.configure(text_color=BRAND_DIM)

        # Button visibility
        self._back_btn.pack_forget()
        if self._current_step > 0:
            self._back_btn.pack(side="left")

        # Last step replaces "Next" with "Launch"
        if self._current_step == STEP_COUNT - 1:
            self._next_btn.configure(text="🚀 Launch LitigationOS")
        else:
            self._next_btn.configure(text="Next →")

    # ── navigation ----------------------------------------------------------

    def _go_next(self) -> None:
        """Advance to the next step (validates first)."""
        self._error_label.configure(text="")

        if not self._validate_step(self._current_step):
            return

        self._collect_step_data(self._current_step)

        if self._current_step >= STEP_COUNT - 1:
            self._finish_wizard()
            return

        self._current_step += 1
        self._build_step(self._current_step)
        self._show_step(self._current_step)

    def _go_back(self) -> None:
        """Return to the previous step."""
        self._error_label.configure(text="")
        if self._current_step <= 0:
            return
        self._collect_step_data(self._current_step)
        self._current_step -= 1
        self._show_step(self._current_step)

    def _show_step(self, step: int) -> None:
        """Display the frame for *step*, hiding all others."""
        for child in self._content.winfo_children():
            child.pack_forget()
        frame = self._step_frames[step]
        if frame is not None:
            frame.pack(fill="both", expand=True)
        self._update_dots()

    # ── validation ----------------------------------------------------------

    def _validate_step(self, step: int) -> bool:
        """Return True if the current step passes validation."""
        if step == 1:  # Disclaimer
            if not self._data["disclaimer_accepted"]:
                self._error_label.configure(
                    text="You must accept the disclaimer to continue.",
                )
                return False

        if step == 2:  # Case setup
            if not self._case_name_var.get().strip():
                self._error_label.configure(text="Case name is required.")
                return False

        if step == 3:  # Drives
            has_drive = any(v.get() for v in self._drive_vars.values())
            has_custom = self._custom_path_var.get().strip() != ""
            if not has_drive and not has_custom:
                self._error_label.configure(
                    text="Select at least one drive or enter a custom path.",
                )
                return False

        return True

    # ── step data collection ------------------------------------------------

    def _collect_step_data(self, step: int) -> None:
        """Read widget state into ``self._data`` for the given step."""
        if step == 1:
            self._data["disclaimer_accepted"] = self._disclaimer_var.get()
        elif step == 2:
            self._data["case_name"] = self._case_name_var.get().strip()
            self._data["court"] = self._court_var.get().strip()
            self._data["county"] = self._county_var.get()
            self._data["case_number"] = self._case_number_var.get().strip()
            self._data["judge_name"] = self._judge_var.get().strip()
        elif step == 3:
            selected = [d for d, v in self._drive_vars.items() if v.get()]
            self._data["scan_drives"] = selected
            self._data["custom_scan_path"] = self._custom_path_var.get().strip()
        elif step == 4:
            self._data["download_location"] = self._download_var.get().strip()
        elif step == 5:
            self._data["notifications_enabled"] = self._notif_var.get()
            self._data["sound_enabled"] = self._sound_var.get()
            self._data["urgency_threshold"] = self._urgency_var.get()
        elif step == 6:
            self._data["analytics_usage"] = self._analytics_usage_var.get()
            self._data["analytics_court_profiling"] = (
                self._analytics_court_var.get()
            )

    # ── step builders -------------------------------------------------------

    def _build_step(self, step: int) -> None:
        """Build the frame for *step* if not already created."""
        if self._step_frames[step] is not None:
            return  # already built

        builders = [
            self._build_step_welcome,       # 0
            self._build_step_disclaimer,    # 1
            self._build_step_case_setup,    # 2
            self._build_step_drives,        # 3
            self._build_step_downloads,     # 4
            self._build_step_notifications, # 5
            self._build_step_analytics,     # 6
            self._build_step_ready,         # 7
        ]
        builders[step]()

    # -- Step 0: Welcome -----------------------------------------------------

    def _build_step_welcome(self) -> None:
        """Welcome page with MBP LLC branding."""
        f = ctk.CTkFrame(self._content, fg_color="transparent")
        self._step_frames[0] = f

        spacer = ctk.CTkFrame(f, fg_color="transparent")
        spacer.pack(expand=True)

        ctk.CTkLabel(
            spacer,
            text="🐷",
            font=ctk.CTkFont(size=56),
            text_color=BRAND_PINK,
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            spacer,
            text="Welcome to LitigationOS",
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color=BRAND_TEXT,
        ).pack(pady=(0, 4))

        ctk.CTkLabel(
            spacer,
            text="by MBP LLC",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=BRAND_DIM,
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            spacer,
            text=(
                "Your pro se litigation command center.\n"
                "This wizard will walk you through initial setup."
            ),
            font=ctk.CTkFont(size=13),
            text_color=BRAND_DIM,
            justify="center",
        ).pack(pady=(0, 16))

        ctk.CTkLabel(
            spacer,
            text="Level the Playing Field",
            font=ctk.CTkFont(family="Segoe UI", size=15, slant="italic"),
            text_color=BRAND_PINK,
        ).pack()

        ctk.CTkFrame(f, fg_color="transparent").pack(expand=True)

    # -- Step 1: Legal Disclaimer --------------------------------------------

    def _build_step_disclaimer(self) -> None:
        """Disclaimer that LitigationOS is not legal advice."""
        f = ctk.CTkFrame(self._content, fg_color="transparent")
        self._step_frames[1] = f

        ctk.CTkLabel(
            f,
            text="⚖️  Legal Disclaimer",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=BRAND_TEXT,
        ).pack(anchor="w", pady=(16, 12))

        disclaimer_text = (
            "LitigationOS is a litigation support tool designed to help "
            "pro se litigants organize evidence, track deadlines, and "
            "generate draft court filings.\n\n"
            "THIS SOFTWARE DOES NOT PROVIDE LEGAL ADVICE. Nothing "
            "generated by LitigationOS constitutes legal counsel, and no "
            "attorney-client relationship is created by using this "
            "software.\n\n"
            "You are solely responsible for verifying the accuracy, "
            "completeness, and legal sufficiency of all filings before "
            "submission to any court. Always consult a licensed attorney "
            "for legal matters.\n\n"
            "MBP LLC and the creators of LitigationOS accept no liability "
            "for outcomes resulting from use of this software."
        )

        text_box = ctk.CTkTextbox(
            f,
            width=700,
            height=240,
            fg_color=BRAND_CARD,
            text_color=BRAND_TEXT,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            corner_radius=8,
            border_width=1,
            border_color=BRAND_BORDER,
            wrap="word",
        )
        text_box.pack(fill="x", pady=(0, 16))
        text_box.insert("1.0", disclaimer_text)
        text_box.configure(state="disabled")

        self._disclaimer_var = ctk.BooleanVar(value=self._data["disclaimer_accepted"])
        checkbox = ctk.CTkCheckBox(
            f,
            text="I have read and accept this disclaimer",
            variable=self._disclaimer_var,
            font=ctk.CTkFont(size=13),
            text_color=BRAND_TEXT,
            fg_color=BRAND_PINK,
            hover_color=BRAND_PINK_HOVER,
            border_color=BRAND_DIM,
            checkmark_color=BRAND_TEXT,
        )
        checkbox.pack(anchor="w")

    # -- Step 2: Case Setup --------------------------------------------------

    def _build_step_case_setup(self) -> None:
        """Collect case name, court, county, case number, judge."""
        f = ctk.CTkFrame(self._content, fg_color="transparent")
        self._step_frames[2] = f

        ctk.CTkLabel(
            f,
            text="📋  Case Setup",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=BRAND_TEXT,
        ).pack(anchor="w", pady=(16, 12))

        ctk.CTkLabel(
            f,
            text="Enter your primary case details. You can add more cases later.",
            font=ctk.CTkFont(size=12),
            text_color=BRAND_DIM,
        ).pack(anchor="w", pady=(0, 12))

        form = ctk.CTkFrame(f, fg_color="transparent")
        form.pack(fill="x")

        # -- helpers for form rows --
        def _row(parent: ctk.CTkFrame, label: str, var: ctk.StringVar,
                 placeholder: str = "", tooltip: str = "") -> ctk.CTkEntry:
            row_frame = ctk.CTkFrame(parent, fg_color="transparent")
            row_frame.pack(fill="x", pady=6)

            lbl = ctk.CTkLabel(
                row_frame,
                text=label,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=BRAND_TEXT,
                width=140,
                anchor="w",
            )
            lbl.pack(side="left")

            entry = ctk.CTkEntry(
                row_frame,
                textvariable=var,
                placeholder_text=placeholder,
                fg_color=BRAND_CARD,
                border_color=BRAND_BORDER,
                text_color=BRAND_TEXT,
                font=ctk.CTkFont(size=12),
                height=36,
            )
            entry.pack(side="left", fill="x", expand=True)
            if tooltip:
                Tooltip(entry, tooltip)
            return entry

        self._case_name_var = ctk.StringVar(value=self._data["case_name"])
        _row(form, "Case Name *", self._case_name_var,
             placeholder="e.g. Pigors v. Watson",
             tooltip="A descriptive name for your case.")

        self._court_var = ctk.StringVar(value=self._data["court"])
        _row(form, "Court", self._court_var,
             placeholder="e.g. 14th Circuit Court, Family Division",
             tooltip="Court where the case is filed.")

        # County dropdown
        county_row = ctk.CTkFrame(form, fg_color="transparent")
        county_row.pack(fill="x", pady=6)
        ctk.CTkLabel(
            county_row,
            text="County",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=BRAND_TEXT,
            width=140,
            anchor="w",
        ).pack(side="left")

        self._county_var = ctk.StringVar(
            value=self._data["county"] or "Muskegon",
        )
        county_menu = ctk.CTkOptionMenu(
            county_row,
            variable=self._county_var,
            values=_MI_COUNTIES,
            fg_color=BRAND_CARD,
            button_color=BRAND_PINK,
            button_hover_color=BRAND_PINK_HOVER,
            text_color=BRAND_TEXT,
            font=ctk.CTkFont(size=12),
            dropdown_fg_color=BRAND_CARD,
            dropdown_text_color=BRAND_TEXT,
            dropdown_hover_color=BRAND_PINK_DIM,
            width=240,
        )
        county_menu.pack(side="left")
        Tooltip(county_menu, "Michigan county where the case is filed.")

        self._case_number_var = ctk.StringVar(value=self._data["case_number"])
        _row(form, "Case Number", self._case_number_var,
             placeholder="e.g. 2024-001507-DC",
             tooltip="Docket or case number assigned by the court.")

        self._judge_var = ctk.StringVar(value=self._data["judge_name"])
        _row(form, "Judge Name", self._judge_var,
             placeholder="e.g. Hon. Jenny L. McNeill",
             tooltip="Presiding judge (used for profiling and bias analysis).")

    # -- Step 3: Drive Selection ---------------------------------------------

    def _build_step_drives(self) -> None:
        """Select drives to scan for evidence files."""
        f = ctk.CTkFrame(self._content, fg_color="transparent")
        self._step_frames[3] = f

        ctk.CTkLabel(
            f,
            text="💾  Drive Selection",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=BRAND_TEXT,
        ).pack(anchor="w", pady=(16, 4))

        ctk.CTkLabel(
            f,
            text=(
                "Select which drives LitigationOS should scan for evidence, "
                "documents, and case files."
            ),
            font=ctk.CTkFont(size=12),
            text_color=BRAND_DIM,
        ).pack(anchor="w", pady=(0, 16))

        # Drive checkboxes (2-column grid)
        drive_grid = ctk.CTkFrame(f, fg_color="transparent")
        drive_grid.pack(fill="x", pady=(0, 12))
        drive_grid.columnconfigure((0, 1), weight=1)

        pre_selected = self._data.get("scan_drives", [])
        self._drive_vars: dict[str, ctk.BooleanVar] = {}

        for idx, drive in enumerate(_SCAN_DRIVES):
            var = ctk.BooleanVar(value=(drive in pre_selected))
            self._drive_vars[drive] = var

            exists = os.path.isdir(drive)
            state = "normal" if exists else "disabled"
            suffix = "" if exists else "  (not found)"

            cb = ctk.CTkCheckBox(
                drive_grid,
                text=f"{drive}{suffix}",
                variable=var,
                state=state,
                font=ctk.CTkFont(size=13),
                text_color=BRAND_TEXT if exists else BRAND_DIM,
                fg_color=BRAND_PINK,
                hover_color=BRAND_PINK_HOVER,
                border_color=BRAND_DIM,
                checkmark_color=BRAND_TEXT,
            )
            row, col = divmod(idx, 2)
            cb.grid(row=row, column=col, sticky="w", padx=12, pady=6)

        # Custom path
        ctk.CTkFrame(f, fg_color=BRAND_BORDER, height=1).pack(
            fill="x", pady=(8, 12),
        )

        ctk.CTkLabel(
            f,
            text="Custom scan path (optional):",
            font=ctk.CTkFont(size=12),
            text_color=BRAND_DIM,
        ).pack(anchor="w")

        self._custom_path_var = ctk.StringVar(
            value=self._data.get("custom_scan_path", ""),
        )
        ctk.CTkEntry(
            f,
            textvariable=self._custom_path_var,
            placeholder_text=r"e.g. E:\MyLegalFiles",
            fg_color=BRAND_CARD,
            border_color=BRAND_BORDER,
            text_color=BRAND_TEXT,
            font=ctk.CTkFont(size=12),
            height=36,
            width=500,
        ).pack(anchor="w", pady=(6, 0))

    # -- Step 4: Download Location -------------------------------------------

    def _build_step_downloads(self) -> None:
        """Choose where generated filings are saved."""
        f = ctk.CTkFrame(self._content, fg_color="transparent")
        self._step_frames[4] = f

        ctk.CTkLabel(
            f,
            text="📂  Download Location",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=BRAND_TEXT,
        ).pack(anchor="w", pady=(16, 4))

        ctk.CTkLabel(
            f,
            text=(
                "Choose where LitigationOS saves generated filings, "
                "briefs, and court documents."
            ),
            font=ctk.CTkFont(size=12),
            text_color=BRAND_DIM,
        ).pack(anchor="w", pady=(0, 20))

        path_frame = ctk.CTkFrame(f, fg_color="transparent")
        path_frame.pack(fill="x")

        self._download_var = ctk.StringVar(
            value=self._data.get("download_location", _DEFAULT_FILING_DIR),
        )
        entry = ctk.CTkEntry(
            path_frame,
            textvariable=self._download_var,
            fg_color=BRAND_CARD,
            border_color=BRAND_BORDER,
            text_color=BRAND_TEXT,
            font=ctk.CTkFont(size=12),
            height=36,
        )
        entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        Tooltip(entry, "Directory where generated filings will be saved.")

        browse_btn = ctk.CTkButton(
            path_frame,
            text="Browse…",
            width=90,
            fg_color=BRAND_CARD,
            hover_color=BRAND_BORDER,
            text_color=BRAND_TEXT,
            font=ctk.CTkFont(size=12),
            command=self._browse_download_dir,
        )
        browse_btn.pack(side="left")

        # Info note
        ctk.CTkLabel(
            f,
            text=(
                "ℹ️  The folder will be created automatically if it does "
                "not exist."
            ),
            font=ctk.CTkFont(size=11),
            text_color=BRAND_DIM,
        ).pack(anchor="w", pady=(16, 0))

    def _browse_download_dir(self) -> None:
        """Open a directory chooser dialog for the download location."""
        import tkinter.filedialog as fd

        chosen = fd.askdirectory(
            title="Select Filing Download Location",
            initialdir=str(Path.home() / "Desktop"),
        )
        if chosen:
            self._download_var.set(chosen)

    # -- Step 5: Notification Preferences ------------------------------------

    def _build_step_notifications(self) -> None:
        """Enable/disable notifications, sound, and urgency threshold."""
        f = ctk.CTkFrame(self._content, fg_color="transparent")
        self._step_frames[5] = f

        ctk.CTkLabel(
            f,
            text="🔔  Notification Preferences",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=BRAND_TEXT,
        ).pack(anchor="w", pady=(16, 4))

        ctk.CTkLabel(
            f,
            text="Configure how LitigationOS alerts you about deadlines and events.",
            font=ctk.CTkFont(size=12),
            text_color=BRAND_DIM,
        ).pack(anchor="w", pady=(0, 20))

        # Notifications toggle
        self._notif_var = ctk.BooleanVar(
            value=self._data.get("notifications_enabled", True),
        )
        notif_row = ctk.CTkFrame(f, fg_color=BRAND_CARD, corner_radius=8)
        notif_row.pack(fill="x", pady=6)
        ctk.CTkLabel(
            notif_row,
            text="Enable desktop notifications",
            font=ctk.CTkFont(size=13),
            text_color=BRAND_TEXT,
        ).pack(side="left", padx=16, pady=12)
        ctk.CTkSwitch(
            notif_row,
            text="",
            variable=self._notif_var,
            fg_color=BRAND_BORDER,
            progress_color=BRAND_PINK,
            button_color=BRAND_TEXT,
            button_hover_color=BRAND_PINK_HOVER,
        ).pack(side="right", padx=16, pady=12)

        # Sound toggle
        self._sound_var = ctk.BooleanVar(
            value=self._data.get("sound_enabled", True),
        )
        sound_row = ctk.CTkFrame(f, fg_color=BRAND_CARD, corner_radius=8)
        sound_row.pack(fill="x", pady=6)
        ctk.CTkLabel(
            sound_row,
            text="Enable notification sounds",
            font=ctk.CTkFont(size=13),
            text_color=BRAND_TEXT,
        ).pack(side="left", padx=16, pady=12)
        ctk.CTkSwitch(
            sound_row,
            text="",
            variable=self._sound_var,
            fg_color=BRAND_BORDER,
            progress_color=BRAND_PINK,
            button_color=BRAND_TEXT,
            button_hover_color=BRAND_PINK_HOVER,
        ).pack(side="right", padx=16, pady=12)

        # Urgency threshold
        urgency_row = ctk.CTkFrame(f, fg_color=BRAND_CARD, corner_radius=8)
        urgency_row.pack(fill="x", pady=6)
        ctk.CTkLabel(
            urgency_row,
            text="Urgency threshold",
            font=ctk.CTkFont(size=13),
            text_color=BRAND_TEXT,
        ).pack(side="left", padx=16, pady=12)

        self._urgency_var = ctk.StringVar(
            value=self._data.get("urgency_threshold", "Medium and above"),
        )
        ctk.CTkOptionMenu(
            urgency_row,
            variable=self._urgency_var,
            values=_URGENCY_OPTIONS,
            fg_color=BRAND_BLACK,
            button_color=BRAND_PINK,
            button_hover_color=BRAND_PINK_HOVER,
            text_color=BRAND_TEXT,
            font=ctk.CTkFont(size=12),
            dropdown_fg_color=BRAND_CARD,
            dropdown_text_color=BRAND_TEXT,
            dropdown_hover_color=BRAND_PINK_DIM,
            width=180,
        ).pack(side="right", padx=16, pady=12)

    # -- Step 6: Analytics Opt-in --------------------------------------------

    def _build_step_analytics(self) -> None:
        """Optional usage analytics and court profiling opt-in."""
        f = ctk.CTkFrame(self._content, fg_color="transparent")
        self._step_frames[6] = f

        ctk.CTkLabel(
            f,
            text="📊  Analytics Opt-In",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=BRAND_TEXT,
        ).pack(anchor="w", pady=(16, 4))

        ctk.CTkLabel(
            f,
            text="These options are entirely optional. Your data stays local.",
            font=ctk.CTkFont(size=12),
            text_color=BRAND_DIM,
        ).pack(anchor="w", pady=(0, 20))

        # Usage analytics
        self._analytics_usage_var = ctk.BooleanVar(
            value=self._data.get("analytics_usage", False),
        )
        usage_card = ctk.CTkFrame(f, fg_color=BRAND_CARD, corner_radius=8)
        usage_card.pack(fill="x", pady=6)

        usage_inner = ctk.CTkFrame(usage_card, fg_color="transparent")
        usage_inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(
            usage_inner,
            text="Help improve LitigationOS",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=BRAND_TEXT,
        ).pack(anchor="w")
        ctk.CTkLabel(
            usage_inner,
            text=(
                "Send anonymous usage analytics (feature usage, error "
                "rates) to help us improve the product. No case data is "
                "ever transmitted."
            ),
            font=ctk.CTkFont(size=11),
            text_color=BRAND_DIM,
            wraplength=600,
            justify="left",
        ).pack(anchor="w", pady=(4, 8))
        ctk.CTkSwitch(
            usage_inner,
            text="Enable anonymous usage analytics",
            variable=self._analytics_usage_var,
            font=ctk.CTkFont(size=12),
            text_color=BRAND_TEXT,
            fg_color=BRAND_BORDER,
            progress_color=BRAND_PINK,
            button_color=BRAND_TEXT,
            button_hover_color=BRAND_PINK_HOVER,
        ).pack(anchor="w")

        # Court profiling analytics
        self._analytics_court_var = ctk.BooleanVar(
            value=self._data.get("analytics_court_profiling", False),
        )
        court_card = ctk.CTkFrame(f, fg_color=BRAND_CARD, corner_radius=8)
        court_card.pack(fill="x", pady=6)

        court_inner = ctk.CTkFrame(court_card, fg_color="transparent")
        court_inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(
            court_inner,
            text="Court & judge profiling data",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=BRAND_TEXT,
        ).pack(anchor="w")
        ctk.CTkLabel(
            court_inner,
            text=(
                "Contribute anonymised case analytics (ruling patterns, "
                "motion success rates) to improve judge and court "
                "profiling for all users."
            ),
            font=ctk.CTkFont(size=11),
            text_color=BRAND_DIM,
            wraplength=600,
            justify="left",
        ).pack(anchor="w", pady=(4, 8))
        ctk.CTkSwitch(
            court_inner,
            text="Send case analytics for judge/court profiling",
            variable=self._analytics_court_var,
            font=ctk.CTkFont(size=12),
            text_color=BRAND_TEXT,
            fg_color=BRAND_BORDER,
            progress_color=BRAND_PINK,
            button_color=BRAND_TEXT,
            button_hover_color=BRAND_PINK_HOVER,
        ).pack(anchor="w")

    # -- Step 7: Ready -------------------------------------------------------

    def _build_step_ready(self) -> None:
        """Summary of choices and launch button."""
        # Collect any pending data from previous step
        if self._current_step == 6:
            self._collect_step_data(6)

        f = ctk.CTkFrame(self._content, fg_color="transparent")
        self._step_frames[7] = f

        ctk.CTkLabel(
            f,
            text="🚀  You're All Set!",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=BRAND_TEXT,
        ).pack(anchor="w", pady=(16, 4))

        ctk.CTkLabel(
            f,
            text="Here's a summary of your configuration:",
            font=ctk.CTkFont(size=12),
            text_color=BRAND_DIM,
        ).pack(anchor="w", pady=(0, 16))

        # Summary card
        summary_card = ctk.CTkFrame(f, fg_color=BRAND_CARD, corner_radius=10)
        summary_card.pack(fill="x", pady=(0, 12))

        d = self._data

        rows = [
            ("Case", d.get("case_name", "—") or "—"),
            ("Court", d.get("court", "—") or "—"),
            ("County", d.get("county", "—") or "—"),
            ("Case Number", d.get("case_number", "—") or "—"),
            ("Judge", d.get("judge_name", "—") or "—"),
            ("Scan Drives", ", ".join(d.get("scan_drives", [])) or "None"),
            ("Custom Path", d.get("custom_scan_path", "") or "—"),
            ("Filings Saved To", d.get("download_location", _DEFAULT_FILING_DIR)),
            ("Notifications", "On" if d.get("notifications_enabled") else "Off"),
            ("Sound", "On" if d.get("sound_enabled") else "Off"),
            ("Urgency", d.get("urgency_threshold", "—")),
            ("Usage Analytics", "On" if d.get("analytics_usage") else "Off"),
            ("Court Profiling", "On" if d.get("analytics_court_profiling") else "Off"),
        ]

        for label, value in rows:
            row = ctk.CTkFrame(summary_card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=3)

            ctk.CTkLabel(
                row,
                text=f"{label}:",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=BRAND_DIM,
                width=140,
                anchor="w",
            ).pack(side="left")

            ctk.CTkLabel(
                row,
                text=value,
                font=ctk.CTkFont(size=12),
                text_color=BRAND_TEXT,
                anchor="w",
            ).pack(side="left", fill="x", expand=True)

        # Extra padding at bottom of summary
        ctk.CTkFrame(summary_card, fg_color="transparent", height=8).pack()

        ctk.CTkLabel(
            f,
            text="You can change any of these settings later from the Settings screen.",
            font=ctk.CTkFont(size=11),
            text_color=BRAND_DIM,
        ).pack(anchor="w", pady=(8, 0))

    # ── finish / persist ----------------------------------------------------

    def _finish_wizard(self) -> None:
        """Persist config to disk, invoke callback, and close."""
        self._collect_step_data(self._current_step)
        self._save_config()

        logger.info("Onboarding wizard complete. Config saved to %s", _CONFIG_FILE)

        callback_data = dict(self._data)
        try:
            self.grab_release()
            self.destroy()
        except Exception:
            pass

        if self._on_complete:
            self._on_complete(callback_data)

    def _save_config(self) -> None:
        """Write wizard results to ``~/.litigationos/config.json``."""
        try:
            _CONFIG_DIR.mkdir(parents=True, exist_ok=True)

            # Merge with any existing config
            existing: dict[str, Any] = {}
            if _CONFIG_FILE.exists():
                try:
                    existing = json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    pass

            existing.update(self._data)
            existing["onboarding_complete"] = True

            _CONFIG_FILE.write_text(
                json.dumps(existing, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            logger.info("Config written to %s", _CONFIG_FILE)
        except OSError:
            logger.exception("Failed to save onboarding config")

    def _on_close(self) -> None:
        """Handle the window-manager close button (X)."""
        try:
            self.grab_release()
            self.destroy()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def load_onboarding_config() -> dict[str, Any]:
    """Load persisted onboarding config, returning an empty dict on failure."""
    if _CONFIG_FILE.exists():
        try:
            return json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def is_onboarding_complete() -> bool:
    """Return True if the onboarding wizard has been completed before."""
    cfg = load_onboarding_config()
    return bool(cfg.get("onboarding_complete", False))
