"""Main CustomTkinter application window and navigation.

This is the top-level GUI container that manages screen switching,
the sidebar navigation, and the status bar.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

import customtkinter as ctk

from litigationos.db.connection import DatabaseManager
from litigationos.gui.widgets import COLORS

logger = logging.getLogger(__name__)

# Sidebar navigation items: (icon, label, screen_key)
NAV_ITEMS = [
    ("📊", "Dashboard", "dashboard"),
    ("💬", "AI Chat", "chat"),
    ("⏰", "Deadlines", "deadlines"),
    ("📁", "Cases", "cases"),
    ("📄", "Filings", "filings"),
    ("📝", "Filing Wizard", "filing_wizard"),
    ("🔍", "Evidence", "evidence"),
    ("🗺", "Evidence Map", "evidence_map"),
    ("📃", "Doc Editor", "doc_editor"),
    ("📅", "Calendar", "calendar"),
    ("📅", "Timeline", "timeline"),
    ("⚙️", "Settings", "settings"),
]

# Prefer the real litigation database; fall back to product DB
_LITIGATION_DB = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")
DEFAULT_DB_PATH = (
    _LITIGATION_DB
    if _LITIGATION_DB.exists()
    else Path.home() / "LitigationOS" / "litigationos.db"
)


class LitigationOSApp(ctk.CTk):
    """Main application window with sidebar navigation."""

    def __init__(self, db_path: Optional[str | Path] = None):
        super().__init__()
        self.title("LitigationOS — Pro Se Litigation Command Center")
        self.geometry("1400x900")
        self.minsize(1000, 600)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # --- Database ---
        self._db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self._db: Optional[DatabaseManager] = None
        self._init_db()

        # --- Settings ---
        self._settings = None
        try:
            from litigationos.config import Settings
            self._settings = Settings(self._db) if self._db else None
        except Exception:
            self._settings = None

        # --- Layout ---
        self._active_screen: Optional[str] = None
        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        self._screen_frame: Optional[ctk.CTkFrame] = None

        self._build_sidebar()
        self._build_content_area()
        self._build_status_bar()

        # Start on dashboard
        self.switch_screen("dashboard")

        # Cleanup on close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # Database initialisation
    # ------------------------------------------------------------------

    def _init_db(self):
        """Create / open the SQLite database."""
        try:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            self._db = DatabaseManager(self._db_path)
            self._db.initialize()
            logger.info("Database ready: %s", self._db_path)
        except Exception:
            logger.exception("Failed to initialise database at %s", self._db_path)
            self._db = None

    # --- Public properties so screen frames that expect an ``app`` work ---

    @property
    def db(self) -> Optional[DatabaseManager]:
        return self._db

    @property
    def settings(self):
        return self._settings

    @property
    def data_dir(self) -> Path:
        return self._db_path.parent

    # ------------------------------------------------------------------
    # Sidebar
    # ------------------------------------------------------------------

    def _build_sidebar(self):
        self._sidebar = ctk.CTkFrame(
            self, width=200, fg_color=COLORS["bg_sidebar"], corner_radius=0,
        )
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)

        # Logo / app title
        logo_frame = ctk.CTkFrame(self._sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", pady=(20, 24))

        ctk.CTkLabel(
            logo_frame,
            text="⚖  LitigationOS",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"],
        ).pack(padx=16)

        ctk.CTkLabel(
            logo_frame,
            text="Pro Se Command Center",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_dim"],
        ).pack(padx=16)

        # Navigation buttons
        for icon, label, key in NAV_ITEMS:
            btn = ctk.CTkButton(
                self._sidebar,
                text=f" {icon}  {label}",
                anchor="w",
                fg_color="transparent",
                hover_color=COLORS["accent"],
                text_color=COLORS["text"],
                font=ctk.CTkFont(size=14),
                height=40,
                corner_radius=8,
                command=lambda k=key: self.switch_screen(k),
            )
            btn.pack(fill="x", padx=10, pady=2)
            self._nav_buttons[key] = btn

    # ------------------------------------------------------------------
    # Content area
    # ------------------------------------------------------------------

    def _build_content_area(self):
        self._content = ctk.CTkFrame(self, fg_color=COLORS["bg_dark"], corner_radius=0)
        self._content.pack(side="left", fill="both", expand=True)

    # ------------------------------------------------------------------
    # Status bar
    # ------------------------------------------------------------------

    def _build_status_bar(self):
        self._status_bar = ctk.CTkFrame(
            self, height=28, fg_color=COLORS["border"], corner_radius=0,
        )
        self._status_bar.pack(side="bottom", fill="x")
        self._status_bar.pack_propagate(False)

        self._status_case_label = ctk.CTkLabel(
            self._status_bar, text="Cases: —",
            font=ctk.CTkFont(size=11), text_color=COLORS["text_dim"],
        )
        self._status_case_label.pack(side="left", padx=12)

        self._status_deadline_label = ctk.CTkLabel(
            self._status_bar, text="Deadlines: —",
            font=ctk.CTkFont(size=11), text_color=COLORS["text_dim"],
        )
        self._status_deadline_label.pack(side="left", padx=12)

        # DB file size indicator
        db_size_str = "—"
        if self._db_path.exists():
            db_size = os.path.getsize(self._db_path)
            if db_size > 1024 * 1024 * 1024:
                db_size_str = f"{db_size / (1024**3):.1f} GB"
            elif db_size > 1024 * 1024:
                db_size_str = f"{db_size / (1024**2):.1f} MB"
            else:
                db_size_str = f"{db_size // 1024} KB"
        self._status_dbsize_label = ctk.CTkLabel(
            self._status_bar, text=f"DB: {db_size_str}",
            font=ctk.CTkFont(size=11), text_color=COLORS["text_dim"],
        )
        self._status_dbsize_label.pack(side="left", padx=12)

        db_status = "[OK] Connected" if self._db else "[X] No DB"
        db_color = COLORS["green"] if self._db else COLORS["red"]
        self._status_db_label = ctk.CTkLabel(
            self._status_bar, text=f"DB: {db_status}",
            font=ctk.CTkFont(size=11), text_color=db_color,
        )
        self._status_db_label.pack(side="right", padx=12)

        self._refresh_status_bar()

    def _refresh_status_bar(self):
        if not self._db:
            return
        conn = self._db.connect()
        try:
            tables = [
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            ]

            # Evidence / case count
            if "evidence_quotes" in tables:
                row = conn.execute("SELECT COUNT(*) FROM evidence_quotes").fetchone()
                self._status_case_label.configure(text=f"Evidence: {row[0]:,}")
            elif "evidence" in tables:
                row = conn.execute("SELECT COUNT(*) FROM evidence").fetchone()
                self._status_case_label.configure(text=f"Evidence: {row[0]:,}")
            elif "cases" in tables:
                row = conn.execute("SELECT COUNT(*) FROM cases").fetchone()
                self._status_case_label.configure(text=f"Cases: {row[0]}")

            # Deadline count
            if "deadlines" in tables:
                row = conn.execute(
                    "SELECT COUNT(*) FROM deadlines WHERE status='pending'"
                ).fetchone()
                dl_count = row[0] if row else 0
                color = COLORS["red"] if dl_count > 0 else COLORS["text_dim"]
                self._status_deadline_label.configure(
                    text=f"Deadlines: {dl_count}", text_color=color,
                )
        except Exception:
            pass
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Screen switching
    # ------------------------------------------------------------------

    def switch_screen(self, screen_name: str):
        """Navigate to a different screen."""
        if screen_name == self._active_screen:
            return

        # Destroy current screen
        if self._screen_frame is not None:
            self._screen_frame.destroy()
            self._screen_frame = None

        # Highlight active nav button
        for key, btn in self._nav_buttons.items():
            if key == screen_name:
                btn.configure(fg_color=COLORS["accent"])
            else:
                btn.configure(fg_color="transparent")

        self._active_screen = screen_name
        self._screen_frame = self._create_screen(screen_name)
        if self._screen_frame:
            self._screen_frame.pack(fill="both", expand=True)

        self._refresh_status_bar()

    def _create_screen(self, name: str) -> Optional[ctk.CTkFrame]:
        """Lazily instantiate the screen frame for *name*."""
        if not self._db:
            return self._placeholder("Database not available")

        if name == "dashboard":
            from litigationos.gui.dashboard import DashboardFrame
            return DashboardFrame(
                self._content, db=self._db, navigate_cb=self.switch_screen,
            )

        if name == "chat":
            from litigationos.gui.chat_screen import ChatFrame
            return ChatFrame(
                self._content, db=self._db, navigate_cb=self.switch_screen,
            )

        if name == "cases":
            from litigationos.gui.case_manager import CaseManagerFrame
            return CaseManagerFrame(self._content, db=self._db)

        if name == "deadlines":
            from litigationos.gui.deadline_dashboard import DeadlineDashboardFrame
            return DeadlineDashboardFrame(
                self._content, db=self._db, navigate_cb=self.switch_screen,
            )

        if name == "filings":
            from litigationos.gui.filing_manager import FilingManagerFrame
            return FilingManagerFrame(self._content, app=self)

        if name == "filing_wizard":
            from litigationos.gui.filing_wizard import FilingWizardFrame
            return FilingWizardFrame(
                self._content, db=self._db, navigate_cb=self.switch_screen,
            )

        if name == "evidence":
            from litigationos.gui.evidence_browser import EvidenceBrowserFrame
            return EvidenceBrowserFrame(self._content, app=self)

        if name == "evidence_map":
            from litigationos.gui.evidence_map import EvidenceMapFrame
            return EvidenceMapFrame(
                self._content, db=self._db, navigate_cb=self.switch_screen,
            )

        if name == "doc_editor":
            from litigationos.gui.document_editor import DocumentEditorFrame
            return DocumentEditorFrame(
                self._content, db=self._db, navigate_cb=self.switch_screen,
            )

        if name == "calendar":
            from litigationos.gui.calendar_view import CalendarViewFrame
            return CalendarViewFrame(
                self._content, db=self._db, navigate_cb=self.switch_screen,
            )

        if name == "timeline":
            from litigationos.gui.timeline_view import TimelineFrame
            return TimelineFrame(self._content, app=self)

        if name == "settings":
            from litigationos.gui.settings_screen import SettingsFrame
            return SettingsFrame(self._content, app=self)

        return self._placeholder(f"Unknown screen: {name}")

    def _placeholder(self, text: str) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self._content, fg_color="transparent")
        ctk.CTkLabel(
            frame, text=text,
            font=ctk.CTkFont(size=18), text_color=COLORS["text_dim"],
        ).pack(expand=True)
        return frame

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _on_close(self):
        """Clean up and exit."""
        logger.info("LitigationOS shutting down")
        self.destroy()

    def mainloop(self, *args, **kwargs):
        """Start the GUI event loop."""
        logger.info("LitigationOS GUI starting")
        super().mainloop(*args, **kwargs)
