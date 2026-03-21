"""Pipeline Runner — Run and monitor the LitigationOS 16-phase data pipeline.

Provides a GUI for launching, pausing, and stopping the pipeline,
viewing real-time console output, tracking phase completion, and
reviewing run history.  Subprocess output is streamed to a terminal-
style text area via a dedicated reader thread.

CRITICAL: The pipeline subprocess CWD is set to ``00_SYSTEM/pipeline/``
(never the repo root) to avoid shadow-module collisions with the 22+
stdlib-shadowing files in the repo root.
"""

from __future__ import annotations

import datetime
import logging
import os
import re
import subprocess
import sys
import threading
import time
from typing import TYPE_CHECKING, Any, Callable, Optional

import customtkinter as ctk

from litigationos.gui.widgets import (
    COLORS,
    ContextMenu,
    DataCard,
    ProgressScore,
    StatusBadge,
    Tooltip,
)

if TYPE_CHECKING:
    from litigationos.db.connection import DatabaseManager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_REPO_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "..")
)
_PIPELINE_DIR = os.path.join(_REPO_ROOT, "00_SYSTEM", "pipeline")
_PIPELINE_SCRIPT = os.path.join(_PIPELINE_DIR, "run_omega_pipeline.py")

# Phase definitions: (id, label, description)
PHASES: list[tuple[str, str, str]] = [
    ("0", "Safety Snapshot", "SHA-256 manifest & backup of all evidence files"),
    ("1", "Drive Inventory", "Scan all 6+ drives and catalogue every file"),
    ("2", "Deduplication", "Content-based dedup across all drives"),
    ("3", "Classification", "MEEK signal detection & lane assignment"),
    ("4a", "PDF Extraction", "Extract text, metadata & images from PDFs"),
    ("4b", "DOCX Extraction", "Extract text & structure from Word documents"),
    ("4c", "Structured Data", "Parse CSVs, Excel, JSON & other structured files"),
    ("4d", "Atomization", "Split documents into atomic evidence units"),
    ("4e", "Archive Processing", "Unpack and index ZIP/RAR/7z archives"),
    ("5", "Brain Feed", "Feed 50 LEXOS micro-brains across 8 categories"),
    ("6", "Gap Analysis", "EGCP scoring per legal action & evidence gaps"),
    ("7a", "Graph Delta", "Build incremental knowledge-graph changes"),
    ("7b", "Synthesis Merge", "Merge overlapping evidence threads"),
    ("7c", "Knowledge Merge", "Consolidate knowledge graph into unified view"),
    ("8", "Litigation Refresh", "Refresh litigation context from merged data"),
    ("9", "MCP Ingest", "Feed data into MCP server for tool access"),
    ("10", "Judicial Analysis", "Analyse judicial patterns & bias indicators"),
    ("11", "Legal Action Discovery", "Discover actionable legal claims"),
    ("12", "Rule Audit", "Audit compliance with MCR / court rules"),
    ("13", "Refinement", "Refine evidence scoring & cross-references"),
    ("14", "Finalization", "Finalize filings, exhibits & indexes"),
    ("15", "Validation", "End-to-end validation & PASS-gate checks"),
    ("16", "Desktop Offload", "Package outputs for the desktop app"),
]

# Phase-status palette
_STATUS_CFG: dict[str, tuple[str, str]] = {
    "NOT_RUN": (COLORS["gray"], "NOT RUN"),
    "RUNNING": (COLORS["blue"], "RUNNING"),
    "COMPLETE": (COLORS["green"], "COMPLETE"),
    "FAILED": (COLORS["red"], "FAILED"),
    "SKIPPED": (COLORS["yellow"], "SKIPPED"),
}

# Regex to detect phase-start / phase-end markers in pipeline stdout.
# The pipeline emits lines like:
#   [PHASE 4a] Starting PDF Extraction ...
#   [PHASE 4a] COMPLETE  (312 items, 14.2s)
#   [PHASE 6] FAILED  RuntimeError: ...
_RE_PHASE_START = re.compile(
    r"\[PHASE\s+([0-9]+[a-e]?)\]\s+(Starting|RUNNING)", re.IGNORECASE,
)
_RE_PHASE_END = re.compile(
    r"\[PHASE\s+([0-9]+[a-e]?)\]\s+(COMPLETE|FAILED|SKIPPED)"
    r"(?:\s+\((\d+)\s+items?,\s*([\d.]+)s\))?",
    re.IGNORECASE,
)


# ═══════════════════════════════════════════════════════════════════════════
# Phase Card Widget
# ═══════════════════════════════════════════════════════════════════════════

class _PhaseCard(ctk.CTkFrame):
    """A single pipeline-phase card with checkbox, status badge & stats."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        phase_id: str,
        label: str,
        description: str,
        on_run_single: Callable[[str], None] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(parent, fg_color=COLORS["bg_card"], corner_radius=10, **kwargs)
        self.phase_id = phase_id
        self._on_run_single = on_run_single

        # State
        self._status = "NOT_RUN"
        self._last_run: str = "—"
        self._items_processed: int = 0

        # --- Checkbox (for "Run Selected") ---
        self._selected_var = ctk.BooleanVar(value=True)
        self._chk = ctk.CTkCheckBox(
            self,
            text="",
            variable=self._selected_var,
            width=24,
            checkbox_width=18,
            checkbox_height=18,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            border_color=COLORS["border_light"],
        )
        self._chk.grid(row=0, column=0, rowspan=2, padx=(10, 4), pady=10, sticky="n")

        # --- Phase ID badge ---
        id_frame = ctk.CTkFrame(self, fg_color=COLORS["accent_dim"], corner_radius=6, width=44)
        id_frame.grid(row=0, column=1, rowspan=2, padx=(0, 8), pady=10, sticky="n")
        id_frame.grid_propagate(False)
        id_frame.configure(height=28, width=44)
        ctk.CTkLabel(
            id_frame,
            text=phase_id,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#FFFFFF",
        ).place(relx=0.5, rely=0.5, anchor="center")

        # --- Text info ---
        info = ctk.CTkFrame(self, fg_color="transparent")
        info.grid(row=0, column=2, sticky="ew", padx=(0, 8), pady=(10, 0))

        self._name_label = ctk.CTkLabel(
            info,
            text=label,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text"],
            anchor="w",
        )
        self._name_label.pack(anchor="w")

        self._desc_label = ctk.CTkLabel(
            info,
            text=description,
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_dim"],
            anchor="w",
            wraplength=280,
        )
        self._desc_label.pack(anchor="w")

        # --- Status / stats row ---
        stats_row = ctk.CTkFrame(self, fg_color="transparent")
        stats_row.grid(row=1, column=2, sticky="ew", padx=(0, 8), pady=(2, 10))

        self._badge = StatusBadge(stats_row, text="NOT RUN", color=COLORS["gray"])
        self._badge.pack(side="left", padx=(0, 8))

        self._time_label = ctk.CTkLabel(
            stats_row,
            text="Last: —",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_dim"],
        )
        self._time_label.pack(side="left", padx=(0, 8))

        self._items_label = ctk.CTkLabel(
            stats_row,
            text="",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_dim"],
        )
        self._items_label.pack(side="left")

        # Grid weights
        self.columnconfigure(2, weight=1)

        # --- Tooltip ---
        Tooltip(self, text=f"Phase {phase_id}: {label}\n{description}")

        # --- Context menu ---
        menu_items: list[tuple[str, Any]] = [
            ("▶ Run This Phase", lambda: self._run_single()),
            ("📋 View Last Log", lambda: logger.info("View log for phase %s", phase_id)),
            ("---", None),
            ("🔄 Reset Status", lambda: self.set_status("NOT_RUN")),
        ]
        ContextMenu(self, items=menu_items)

    # --- Public API -------------------------------------------------------

    @property
    def selected(self) -> bool:
        """Return whether this phase is checked for inclusion in a run."""
        return self._selected_var.get()

    @selected.setter
    def selected(self, value: bool) -> None:
        self._selected_var.set(value)

    def set_status(
        self,
        status: str,
        items: int | None = None,
        timestamp: str | None = None,
    ) -> None:
        """Update the visual status of this phase card."""
        self._status = status
        color, display = _STATUS_CFG.get(status, (COLORS["gray"], status))
        self._badge.set(display, color=color)

        if timestamp:
            self._last_run = timestamp
            self._time_label.configure(text=f"Last: {timestamp}")

        if items is not None:
            self._items_processed = items
            self._items_label.configure(text=f"{items:,} items")

        # Highlight border for running phase
        if status == "RUNNING":
            self.configure(border_color=COLORS["accent"], border_width=2)
        else:
            self.configure(border_color=COLORS["border"], border_width=1)

    def get_status(self) -> str:
        """Return the current status string."""
        return self._status

    # --- Internal ---------------------------------------------------------

    def _run_single(self) -> None:
        if self._on_run_single:
            self._on_run_single(self.phase_id)


# ═══════════════════════════════════════════════════════════════════════════
# Main Screen
# ═══════════════════════════════════════════════════════════════════════════

class PipelineRunnerFrame(ctk.CTkFrame):
    """Pipeline Runner screen — launch, monitor & review the 16-phase pipeline.

    Parameters
    ----------
    parent : ctk.CTkFrame
        Parent container (typically ``app._content``).
    db : DatabaseManager, optional
        Shared database handle for reading / writing run history.
    navigate_cb : callable, optional
        ``switch_screen(name)`` callback for cross-screen navigation.
    """

    def __init__(
        self,
        parent: ctk.CTkFrame,
        db: "DatabaseManager" = None,
        navigate_cb: Optional[Callable[[str], None]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._db = db
        self._navigate_cb = navigate_cb

        # Run state
        self._process: subprocess.Popen | None = None
        self._reader_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._is_running = False
        self._run_start: float = 0.0

        # Stats accumulators
        self._total_files: int = 0
        self._total_errors: int = 0
        self._total_evidence: int = 0

        # Phase card registry
        self._phase_cards: dict[str, _PhaseCard] = {}

        self._build_ui()
        self._load_history()

    # ------------------------------------------------------------------
    # Cleanup on destroy
    # ------------------------------------------------------------------

    def destroy(self) -> None:
        """Ensure the subprocess is terminated when the screen is torn down."""
        self._stop_pipeline(quiet=True)
        super().destroy()

    # ==================================================================
    # UI Construction
    # ==================================================================

    def _build_ui(self) -> None:
        """Assemble all sub-layouts."""
        # Top-level: header + body split
        self._build_header()
        self._build_body()
        self._build_stats_bar()

    # --- Header -----------------------------------------------------------

    def _build_header(self) -> None:
        hdr = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=12)
        hdr.pack(fill="x", padx=16, pady=(16, 8))

        title_col = ctk.CTkFrame(hdr, fg_color="transparent")
        title_col.pack(side="left", fill="x", expand=True, padx=16, pady=12)

        ctk.CTkLabel(
            title_col,
            text="🚀 Pipeline Runner",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_col,
            text="Run the LitigationOS 16-phase data pipeline",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_dim"],
        ).pack(anchor="w")

        # --- Control panel (right side of header) ---
        ctrl = ctk.CTkFrame(hdr, fg_color="transparent")
        ctrl.pack(side="right", padx=16, pady=12)

        # Row 1: action buttons
        btn_row = ctk.CTkFrame(ctrl, fg_color="transparent")
        btn_row.pack(anchor="e", pady=(0, 6))

        self._btn_run_full = ctk.CTkButton(
            btn_row,
            text="▶ Run Full Pipeline",
            width=150,
            fg_color=COLORS["green"],
            hover_color="#00C853",
            text_color="#000000",
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=8,
            command=self._on_run_full,
        )
        self._btn_run_full.pack(side="left", padx=(0, 6))
        Tooltip(self._btn_run_full, text="Launch all phases sequentially")

        self._btn_run_selected = ctk.CTkButton(
            btn_row,
            text="▶ Run Selected",
            width=120,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=8,
            command=self._on_run_selected,
        )
        self._btn_run_selected.pack(side="left", padx=(0, 6))
        Tooltip(self._btn_run_selected, text="Run only checked phases")

        self._btn_pause = ctk.CTkButton(
            btn_row,
            text="⏸ Pause",
            width=80,
            fg_color=COLORS["yellow"],
            hover_color="#FFAB00",
            text_color="#000000",
            font=ctk.CTkFont(size=12),
            corner_radius=8,
            state="disabled",
            command=self._on_pause,
        )
        self._btn_pause.pack(side="left", padx=(0, 6))

        self._btn_stop = ctk.CTkButton(
            btn_row,
            text="⏹ Stop",
            width=80,
            fg_color=COLORS["red"],
            hover_color="#D50000",
            font=ctk.CTkFont(size=12),
            corner_radius=8,
            state="disabled",
            command=self._on_stop,
        )
        self._btn_stop.pack(side="left")

        # Row 2: options
        opt_row = ctk.CTkFrame(ctrl, fg_color="transparent")
        opt_row.pack(anchor="e", pady=(0, 4))

        # Phase range selectors
        ctk.CTkLabel(
            opt_row, text="Start:", font=ctk.CTkFont(size=11),
            text_color=COLORS["text_dim"],
        ).pack(side="left", padx=(0, 2))

        phase_ids = [p[0] for p in PHASES]
        self._start_phase_var = ctk.StringVar(value=phase_ids[0])
        self._start_dropdown = ctk.CTkOptionMenu(
            opt_row,
            values=phase_ids,
            variable=self._start_phase_var,
            width=70,
            fg_color=COLORS["bg_card"],
            button_color=COLORS["accent_dim"],
            button_hover_color=COLORS["accent"],
            font=ctk.CTkFont(size=11),
        )
        self._start_dropdown.pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            opt_row, text="End:", font=ctk.CTkFont(size=11),
            text_color=COLORS["text_dim"],
        ).pack(side="left", padx=(0, 2))

        self._end_phase_var = ctk.StringVar(value=phase_ids[-1])
        self._end_dropdown = ctk.CTkOptionMenu(
            opt_row,
            values=phase_ids,
            variable=self._end_phase_var,
            width=70,
            fg_color=COLORS["bg_card"],
            button_color=COLORS["accent_dim"],
            button_hover_color=COLORS["accent"],
            font=ctk.CTkFont(size=11),
        )
        self._end_dropdown.pack(side="left", padx=(0, 12))

        # Checkboxes
        self._dry_run_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            opt_row,
            text="Dry Run",
            variable=self._dry_run_var,
            font=ctk.CTkFont(size=11),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            border_color=COLORS["border_light"],
            checkbox_width=18,
            checkbox_height=18,
        ).pack(side="left", padx=(0, 8))

        self._snapshot_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            opt_row,
            text="Create Snapshot",
            variable=self._snapshot_var,
            font=ctk.CTkFont(size=11),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            border_color=COLORS["border_light"],
            checkbox_width=18,
            checkbox_height=18,
        ).pack(side="left")

    # --- Body (phase grid + console) --------------------------------------

    def _build_body(self) -> None:
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=4)
        body.rowconfigure(0, weight=3)
        body.rowconfigure(1, weight=2)
        body.columnconfigure(0, weight=1)

        # Phase grid (top portion, scrollable)
        self._build_phase_grid(body)

        # Console (bottom portion)
        self._build_console(body)

    def _build_phase_grid(self, parent: ctk.CTkFrame) -> None:
        """Create the scrollable 2-column grid of phase cards."""
        grid_frame = ctk.CTkFrame(parent, fg_color="transparent")
        grid_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 4))

        # Select-all / deselect-all bar
        sel_bar = ctk.CTkFrame(grid_frame, fg_color=COLORS["bg_card"], corner_radius=8)
        sel_bar.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            sel_bar,
            text="Pipeline Phases",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text"],
        ).pack(side="left", padx=12, pady=6)

        ctk.CTkButton(
            sel_bar, text="Select All", width=80,
            fg_color=COLORS["accent_dim"], hover_color=COLORS["accent"],
            font=ctk.CTkFont(size=11), corner_radius=6,
            command=lambda: self._set_all_selected(True),
        ).pack(side="right", padx=(0, 12), pady=6)

        ctk.CTkButton(
            sel_bar, text="Deselect All", width=90,
            fg_color=COLORS["border"], hover_color=COLORS["border_light"],
            font=ctk.CTkFont(size=11), corner_radius=6,
            command=lambda: self._set_all_selected(False),
        ).pack(side="right", padx=(0, 4), pady=6)

        # Scrollable area
        scroll = ctk.CTkScrollableFrame(
            grid_frame,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=COLORS["accent_dim"],
            scrollbar_button_hover_color=COLORS["accent"],
        )
        scroll.pack(fill="both", expand=True)
        scroll.columnconfigure(0, weight=1)
        scroll.columnconfigure(1, weight=1)

        # Create phase cards — 2 columns
        for idx, (pid, label, desc) in enumerate(PHASES):
            card = _PhaseCard(
                scroll,
                phase_id=pid,
                label=label,
                description=desc,
                on_run_single=self._on_run_single_phase,
            )
            row = idx // 2
            col = idx % 2
            card.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
            self._phase_cards[pid] = card

    def _build_console(self, parent: ctk.CTkFrame) -> None:
        """Terminal-style output console at the bottom."""
        console_frame = ctk.CTkFrame(
            parent, fg_color=COLORS["bg_dark"], corner_radius=10,
            border_color=COLORS["border"], border_width=1,
        )
        console_frame.grid(row=1, column=0, sticky="nsew", pady=(4, 0))
        console_frame.rowconfigure(1, weight=1)
        console_frame.columnconfigure(0, weight=1)

        # Console header
        con_hdr = ctk.CTkFrame(console_frame, fg_color=COLORS["bg_card"], corner_radius=0)
        con_hdr.grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(
            con_hdr,
            text="📟 Live Output",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(side="left", padx=12, pady=6)

        self._line_count_label = ctk.CTkLabel(
            con_hdr,
            text="0 lines",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_dim"],
        )
        self._line_count_label.pack(side="right", padx=12, pady=6)

        ctk.CTkButton(
            con_hdr, text="Clear", width=60,
            fg_color=COLORS["border"], hover_color=COLORS["border_light"],
            font=ctk.CTkFont(size=11), corner_radius=6,
            command=self._clear_console,
        ).pack(side="right", padx=(0, 4), pady=6)

        # Textbox (monospace, green-on-black)
        self._console = ctk.CTkTextbox(
            console_frame,
            fg_color="#000000",
            text_color="#00E676",
            font=ctk.CTkFont(family="Consolas", size=12),
            corner_radius=0,
            border_width=0,
            wrap="word",
            state="disabled",
            activate_scrollbars=True,
        )
        self._console.grid(row=1, column=0, sticky="nsew", padx=2, pady=(0, 2))

        self._console_lines = 0

    # --- Stats bar --------------------------------------------------------

    def _build_stats_bar(self) -> None:
        bar = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=10)
        bar.pack(fill="x", padx=16, pady=(4, 16))
        bar.columnconfigure((0, 1, 2, 3), weight=1)

        self._dc_files = DataCard(bar, title="Files Processed", value="0", color=COLORS["blue"])
        self._dc_files.grid(row=0, column=0, padx=8, pady=8, sticky="ew")

        self._dc_errors = DataCard(bar, title="Errors", value="0", color=COLORS["red"])
        self._dc_errors.grid(row=0, column=1, padx=8, pady=8, sticky="ew")

        self._dc_duration = DataCard(bar, title="Duration", value="0:00", color=COLORS["accent"])
        self._dc_duration.grid(row=0, column=2, padx=8, pady=8, sticky="ew")

        self._dc_evidence = DataCard(bar, title="Evidence Found", value="0", color=COLORS["green"])
        self._dc_evidence.grid(row=0, column=3, padx=8, pady=8, sticky="ew")

    # ==================================================================
    # Pipeline Execution
    # ==================================================================

    def _on_run_full(self) -> None:
        """Start the full pipeline from start-phase to end-phase."""
        if self._is_running:
            logger.warning("Pipeline already running")
            return
        self._start_pipeline()

    def _on_run_selected(self) -> None:
        """Run only phases whose checkboxes are checked."""
        if self._is_running:
            logger.warning("Pipeline already running")
            return
        selected = [pid for pid, card in self._phase_cards.items() if card.selected]
        if not selected:
            self._append_console("[WARN] No phases selected.\n")
            return
        # Use skip-phases for everything NOT selected
        all_ids = {p[0] for p in PHASES}
        skip = sorted(all_ids - set(selected))
        self._start_pipeline(skip_phases=skip)

    def _on_run_single_phase(self, phase_id: str) -> None:
        """Run a single phase via context menu."""
        if self._is_running:
            self._append_console(f"[WARN] Pipeline busy — cannot run phase {phase_id}.\n")
            return
        self._start_pipeline(start_phase=phase_id, end_phase=phase_id)

    def _on_pause(self) -> None:
        """Toggle pause (send SIGSTOP / SIGCONT on Unix, not supported on Windows)."""
        if not self._process:
            return
        self._append_console("[INFO] Pause not supported on Windows — use Stop instead.\n")

    def _on_stop(self) -> None:
        """Stop the running pipeline."""
        self._stop_pipeline()

    # --- Launch -----------------------------------------------------------

    def _start_pipeline(
        self,
        start_phase: str | None = None,
        end_phase: str | None = None,
        skip_phases: list[str] | None = None,
    ) -> None:
        """Build the subprocess command and launch the pipeline."""
        # Validate pipeline script exists
        if not os.path.isfile(_PIPELINE_SCRIPT):
            self._append_console(
                f"[ERROR] Pipeline script not found: {_PIPELINE_SCRIPT}\n"
            )
            logger.error("Pipeline script missing: %s", _PIPELINE_SCRIPT)
            return

        # Build command
        cmd: list[str] = [sys.executable, _PIPELINE_SCRIPT]

        sp = start_phase or self._start_phase_var.get()
        ep = end_phase or self._end_phase_var.get()
        cmd.extend(["--start-phase", sp, "--end-phase", ep])

        if skip_phases:
            cmd.extend(["--skip-phases", ",".join(skip_phases)])

        if self._dry_run_var.get():
            cmd.append("--dry-run")

        if self._snapshot_var.get():
            cmd.append("--create-snapshot")

        # Reset UI state
        self._reset_run_state()
        self._set_buttons_running(True)
        self._clear_console()

        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._append_console(f"[{ts}] 🚀 Launching pipeline: {' '.join(cmd)}\n")
        self._append_console(f"[{ts}]    CWD: {_PIPELINE_DIR}\n\n")

        # Mark selected phases as NOT_RUN before start
        for pid, card in self._phase_cards.items():
            if card.selected or (start_phase and pid == start_phase):
                card.set_status("NOT_RUN")

        # Launch subprocess — CWD is the pipeline directory (NEVER repo root)
        try:
            env = os.environ.copy()
            env["PYTHONUTF8"] = "1"
            env["PYTHONIOENCODING"] = "utf-8"

            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=_PIPELINE_DIR,
                env=env,
                bufsize=1,
                text=True,
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
        except Exception as exc:
            self._append_console(f"[ERROR] Failed to launch: {exc}\n")
            logger.exception("Pipeline launch failed")
            self._set_buttons_running(False)
            return

        self._is_running = True
        self._run_start = time.monotonic()
        self._stop_event.clear()

        # Start reader thread
        self._reader_thread = threading.Thread(
            target=self._read_output,
            daemon=True,
            name="pipeline-reader",
        )
        self._reader_thread.start()

        # Start duration ticker
        self._tick_duration()

    # --- Reader thread ----------------------------------------------------

    def _read_output(self) -> None:
        """Background thread: read subprocess stdout line-by-line."""
        proc = self._process
        if not proc or not proc.stdout:
            return

        try:
            for line in proc.stdout:
                if self._stop_event.is_set():
                    break
                self._process_line(line)
        except Exception as exc:
            self._schedule_ui(self._append_console, f"\n[READER ERROR] {exc}\n")
        finally:
            # Wait for process to finish
            if proc.poll() is None:
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()

            rc = proc.returncode
            self._schedule_ui(self._on_pipeline_finished, rc)

    def _process_line(self, line: str) -> None:
        """Parse a single output line for phase markers and update UI."""
        # Always append to console
        self._schedule_ui(self._append_console, line)

        # Detect phase start
        m = _RE_PHASE_START.search(line)
        if m:
            pid = m.group(1).lower()
            self._schedule_ui(self._update_phase_status, pid, "RUNNING")
            return

        # Detect phase end
        m = _RE_PHASE_END.search(line)
        if m:
            pid = m.group(1).lower()
            status = m.group(2).upper()
            items_str = m.group(3)
            items = int(items_str) if items_str else None
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            self._schedule_ui(self._update_phase_status, pid, status, items, ts)

            # Accumulate stats
            if items:
                self._total_files += items
            if status == "FAILED":
                self._total_errors += 1
            return

        # Detect evidence counts (heuristic)
        if "evidence" in line.lower() and re.search(r"(\d+)\s+evidence", line, re.I):
            em = re.search(r"(\d+)\s+evidence", line, re.I)
            if em:
                self._total_evidence += int(em.group(1))

        # Detect error lines
        if line.strip().startswith("ERROR") or "Traceback" in line:
            self._total_errors += 1

    # --- UI updates (must run on main thread) -----------------------------

    def _schedule_ui(self, func: Callable, *args: Any) -> None:
        """Schedule *func* to run on the Tk main-loop thread."""
        try:
            self.after(0, func, *args)
        except RuntimeError:
            pass  # Widget destroyed

    def _update_phase_status(
        self,
        phase_id: str,
        status: str,
        items: int | None = None,
        timestamp: str | None = None,
    ) -> None:
        """Update a phase card from the main thread."""
        card = self._phase_cards.get(phase_id)
        if card:
            card.set_status(status, items=items, timestamp=timestamp)

        # Update stats
        self._dc_files.set(f"{self._total_files:,}")
        self._dc_errors.set(f"{self._total_errors:,}")
        self._dc_evidence.set(f"{self._total_evidence:,}")

    def _on_pipeline_finished(self, return_code: int | None) -> None:
        """Called when the pipeline subprocess exits."""
        self._is_running = False
        self._set_buttons_running(False)

        elapsed = time.monotonic() - self._run_start
        mins, secs = divmod(int(elapsed), 60)
        hrs, mins = divmod(mins, 60)
        duration_str = f"{hrs}:{mins:02d}:{secs:02d}" if hrs else f"{mins}:{secs:02d}"

        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if return_code == 0:
            self._append_console(
                f"\n[{ts}] ✅ Pipeline completed successfully ({duration_str})\n"
            )
        else:
            self._append_console(
                f"\n[{ts}] ❌ Pipeline exited with code {return_code} ({duration_str})\n"
            )

        self._dc_duration.set(duration_str)
        self._save_run_record(return_code, elapsed)
        logger.info("Pipeline finished rc=%s elapsed=%s", return_code, duration_str)

    # --- Stop / cleanup ---------------------------------------------------

    def _stop_pipeline(self, quiet: bool = False) -> None:
        """Terminate the running pipeline process."""
        self._stop_event.set()

        if self._process and self._process.poll() is None:
            try:
                self._process.terminate()
                try:
                    self._process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._process.kill()
            except OSError:
                pass

            if not quiet:
                self._append_console("\n[INFO] Pipeline stopped by user.\n")

        self._is_running = False
        self._process = None
        self._set_buttons_running(False)

    def _reset_run_state(self) -> None:
        """Reset counters for a new run."""
        self._total_files = 0
        self._total_errors = 0
        self._total_evidence = 0
        self._dc_files.set("0")
        self._dc_errors.set("0")
        self._dc_duration.set("0:00")
        self._dc_evidence.set("0")

    # --- Console helpers --------------------------------------------------

    def _append_console(self, text: str) -> None:
        """Append text to the live console widget (must be called from main thread)."""
        try:
            self._console.configure(state="normal")
            self._console.insert("end", text)
            self._console.see("end")
            self._console.configure(state="disabled")
            self._console_lines += text.count("\n")
            self._line_count_label.configure(text=f"{self._console_lines} lines")
        except Exception:
            pass  # Widget may have been destroyed

    def _clear_console(self) -> None:
        """Clear the output console."""
        try:
            self._console.configure(state="normal")
            self._console.delete("1.0", "end")
            self._console.configure(state="disabled")
            self._console_lines = 0
            self._line_count_label.configure(text="0 lines")
        except Exception:
            pass

    # --- Button state toggling --------------------------------------------

    def _set_buttons_running(self, running: bool) -> None:
        """Toggle button enabled/disabled state based on pipeline activity."""
        if running:
            self._btn_run_full.configure(state="disabled")
            self._btn_run_selected.configure(state="disabled")
            self._btn_pause.configure(state="normal")
            self._btn_stop.configure(state="normal")
            self._start_dropdown.configure(state="disabled")
            self._end_dropdown.configure(state="disabled")
        else:
            self._btn_run_full.configure(state="normal")
            self._btn_run_selected.configure(state="normal")
            self._btn_pause.configure(state="disabled")
            self._btn_stop.configure(state="disabled")
            self._start_dropdown.configure(state="normal")
            self._end_dropdown.configure(state="normal")

    # --- Duration ticker --------------------------------------------------

    def _tick_duration(self) -> None:
        """Update the duration DataCard every second while running."""
        if not self._is_running:
            return
        elapsed = time.monotonic() - self._run_start
        mins, secs = divmod(int(elapsed), 60)
        hrs, mins = divmod(mins, 60)
        display = f"{hrs}:{mins:02d}:{secs:02d}" if hrs else f"{mins}:{secs:02d}"
        self._dc_duration.set(display)
        self.after(1000, self._tick_duration)

    # --- Select-all helper ------------------------------------------------

    def _set_all_selected(self, value: bool) -> None:
        """Check or uncheck all phase cards."""
        for card in self._phase_cards.values():
            card.selected = value

    # ==================================================================
    # Run History (persisted in-memory or via DB)
    # ==================================================================

    def _save_run_record(self, return_code: int | None, elapsed: float) -> None:
        """Persist a run record to the database (best-effort)."""
        if not self._db:
            return
        try:
            self._db.execute(
                """
                CREATE TABLE IF NOT EXISTS pipeline_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TEXT NOT NULL,
                    finished_at TEXT NOT NULL,
                    return_code INTEGER,
                    elapsed_seconds REAL,
                    files_processed INTEGER,
                    errors INTEGER,
                    evidence_found INTEGER,
                    phases_run TEXT,
                    dry_run INTEGER DEFAULT 0
                )
                """,
            )
            phases_run = ",".join(
                pid for pid, c in self._phase_cards.items()
                if c.get_status() in ("COMPLETE", "FAILED", "SKIPPED")
            )
            now = datetime.datetime.now().isoformat()
            started = datetime.datetime.fromtimestamp(
                time.time() - elapsed,
            ).isoformat()
            self._db.execute(
                """
                INSERT INTO pipeline_runs
                    (started_at, finished_at, return_code, elapsed_seconds,
                     files_processed, errors, evidence_found, phases_run, dry_run)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    started,
                    now,
                    return_code,
                    round(elapsed, 2),
                    self._total_files,
                    self._total_errors,
                    self._total_evidence,
                    phases_run,
                    1 if self._dry_run_var.get() else 0,
                ),
            )
            logger.info("Saved pipeline run record")
        except Exception:
            logger.debug("Could not save pipeline run record", exc_info=True)

    def _load_history(self) -> None:
        """Load the last run record to pre-populate stats (best-effort)."""
        if not self._db:
            return
        try:
            row = self._db.fetchone(
                """
                SELECT files_processed, errors, evidence_found, elapsed_seconds,
                       phases_run, return_code
                FROM pipeline_runs
                ORDER BY id DESC LIMIT 1
                """,
            )
            if row:
                r = dict(row) if hasattr(row, "keys") else {
                    "files_processed": row[0],
                    "errors": row[1],
                    "evidence_found": row[2],
                    "elapsed_seconds": row[3],
                    "phases_run": row[4],
                    "return_code": row[5],
                }
                self._dc_files.set(f"{r.get('files_processed', 0):,}")
                self._dc_errors.set(f"{r.get('errors', 0):,}")
                self._dc_evidence.set(f"{r.get('evidence_found', 0):,}")

                elapsed = r.get("elapsed_seconds", 0) or 0
                mins, secs = divmod(int(elapsed), 60)
                hrs, mins = divmod(mins, 60)
                dur = f"{hrs}:{mins:02d}:{secs:02d}" if hrs else f"{mins}:{secs:02d}"
                self._dc_duration.set(dur, title="Duration (last)")

                # Restore phase statuses from last run
                phases_csv = r.get("phases_run", "") or ""
                rc = r.get("return_code", None)
                for pid in phases_csv.split(","):
                    pid = pid.strip()
                    card = self._phase_cards.get(pid)
                    if card:
                        card.set_status("COMPLETE" if rc == 0 else "FAILED")

                logger.info("Loaded last pipeline run history")
        except Exception:
            logger.debug("No pipeline run history available", exc_info=True)

    # ==================================================================
    # Public API
    # ==================================================================

    def refresh(self) -> None:
        """Reload any dynamic data — called by the app framework."""
        self._load_history()
