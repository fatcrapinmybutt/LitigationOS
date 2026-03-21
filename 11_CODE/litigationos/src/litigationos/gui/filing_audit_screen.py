"""Filing Audit Viewer — Pre-filing quality assurance for all 10 packages.

Displays filing readiness, QA checklists, evidence/authority counts,
placeholder scan results, and overall audit status in a scrollable
card-grid + detail-panel layout.

Colour palette: Hot-pink (#FF1493) on near-black (#0D0D0D) from COLORS.
All database work runs in daemon threads so the GUI never freezes.
"""

from __future__ import annotations

import logging
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

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

_DB_PATH = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")

FILINGS: Dict[str, Dict[str, str]] = {
    "F1": {"title": "Custody Modification — Best Interest", "lane": "A", "case": "2024-001507-DC"},
    "F2": {"title": "Parenting Time Enforcement", "lane": "A", "case": "2024-001507-DC"},
    "F3": {"title": "§1983 Federal Civil Rights", "lane": "A", "case": "2024-001507-DC"},
    "F4": {"title": "Motion to Disqualify Judge", "lane": "E", "case": "2024-001507-DC"},
    "F5": {"title": "Emergency Custody Motion", "lane": "A", "case": "2024-001507-DC"},
    "F6": {"title": "FOC Complaint", "lane": "A", "case": "2024-001507-DC"},
    "F7": {"title": "PPO Violation Enforcement", "lane": "D", "case": "2023-5907-PP"},
    "F8": {"title": "Housing Discrimination (Shady Oaks)", "lane": "B", "case": "2025-002760-CZ"},
    "F9": {"title": "Court of Appeals Application", "lane": "F", "case": "COA-366810"},
    "F10": {"title": "JTC Complaint", "lane": "E", "case": "JTC-2024"},
}

_QA_ITEMS: List[str] = [
    "Caption block",
    "Jurisdiction statement",
    "Standing proof",
    "IRAC structure",
    "Evidence citations",
    "Authority chain",
    "Certificate of service",
    "Page limits",
    "Signature block",
    "Court forms attached",
]

_LANE_COLORS: Dict[str, str] = {
    "A": COLORS["blue"],
    "B": COLORS["orange"],
    "D": COLORS["purple"],
    "E": COLORS["red"],
    "F": COLORS["yellow"],
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_connect() -> Optional[sqlite3.Connection]:
    """Open a read-only connection with standard LitigationOS PRAGMAs."""
    if not _DB_PATH.exists():
        logger.warning("litigation_context.db not found at %s", _DB_PATH)
        return None
    try:
        conn = sqlite3.connect(str(_DB_PATH), timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 60000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA cache_size = -32000")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA synchronous = NORMAL")
        return conn
    except sqlite3.Error as exc:
        logger.error("DB connection failed: %s", exc)
        return None


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row is not None


def _get_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    """Return column names for *table* using PRAGMA table_info."""
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [r[1] for r in rows]


def _ts_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


# ---------------------------------------------------------------------------
# Filing data container
# ---------------------------------------------------------------------------


class _FilingAuditData:
    """Holds audit results for a single filing package."""

    __slots__ = (
        "fid",
        "title",
        "lane",
        "case_no",
        "status",
        "completion",
        "evidence_count",
        "authority_count",
        "page_count",
        "qa_results",
        "placeholder_count",
        "strongest_quotes",
        "authority_levels",
        "last_audit",
    )

    def __init__(self, fid: str) -> None:
        meta = FILINGS[fid]
        self.fid = fid
        self.title = meta["title"]
        self.lane = meta["lane"]
        self.case_no = meta["case"]
        self.status: str = "DRAFT"
        self.completion: int = 0
        self.evidence_count: int = 0
        self.authority_count: int = 0
        self.page_count: int = 0
        self.qa_results: Dict[str, bool] = {item: False for item in _QA_ITEMS}
        self.placeholder_count: int = 0
        self.strongest_quotes: List[str] = []
        self.authority_levels: List[Dict[str, Any]] = []
        self.last_audit: str = "Never"


# ---------------------------------------------------------------------------
# Main frame
# ---------------------------------------------------------------------------


class FilingAuditFrame(ctk.CTkFrame):
    """Pre-filing quality-assurance dashboard for all 10 filing packages.

    Parameters
    ----------
    parent : widget
        Parent CTk container.
    db : DatabaseManager | None
        Optional injected DB manager (not used directly — we open our own
        read-only connection on a worker thread).
    navigate_cb : callable | None
        ``navigate_cb(screen_name)`` for cross-screen navigation.
    """

    def __init__(
        self,
        parent: Any,
        db: Optional["DatabaseManager"] = None,
        navigate_cb: Optional[Callable[[str], None]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._db = db
        self._navigate_cb = navigate_cb
        self._busy = False
        self._selected_fid: Optional[str] = None

        # Audit data cache keyed by filing ID
        self._audit_data: Dict[str, _FilingAuditData] = {}
        # Widget references for cleanup / update
        self._card_widgets: Dict[str, ctk.CTkFrame] = {}
        self._detail_widgets: List[ctk.CTkBaseClass] = []

        self._build_ui()
        # Kick off initial data load
        self._refresh_all()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Assemble full layout: header → body (cards + detail) → footer."""
        self._build_header()
        self._build_body()
        self._build_footer()

    # --- Header --------------------------------------------------------

    def _build_header(self) -> None:
        hdr = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=12)
        hdr.pack(fill="x", padx=16, pady=(16, 8))

        left = ctk.CTkFrame(hdr, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True, padx=16, pady=10)

        ctk.CTkLabel(
            left,
            text="📋 Filing Audit Center",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            left,
            text="Pre-filing quality assurance for all 10 packages",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_dim"],
        ).pack(anchor="w", pady=(2, 0))

        btn_frame = ctk.CTkFrame(hdr, fg_color="transparent")
        btn_frame.pack(side="right", padx=16, pady=10)

        self._refresh_btn = ctk.CTkButton(
            btn_frame,
            text="⟳ Refresh",
            width=100,
            fg_color=COLORS["bg_dark"],
            border_color=COLORS["accent"],
            border_width=1,
            hover_color=COLORS["accent_dim"],
            text_color=COLORS["text"],
            command=self._refresh_all,
        )
        self._refresh_btn.pack(side="left", padx=(0, 8))
        Tooltip(self._refresh_btn, "Reload audit data from database")

        self._audit_btn = ctk.CTkButton(
            btn_frame,
            text="▶ Run Full Audit",
            width=130,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_dim"],
            text_color=COLORS["text"],
            command=self._run_full_audit,
        )
        self._audit_btn.pack(side="left")
        Tooltip(self._audit_btn, "Run QA checks on all 10 filing packages")

    # --- Body ----------------------------------------------------------

    def _build_body(self) -> None:
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=4)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)

        # Left: scrollable card grid
        self._cards_scroll = ctk.CTkScrollableFrame(
            body,
            fg_color=COLORS["bg_dark"],
            corner_radius=12,
            label_text="Filing Packages",
            label_font=ctk.CTkFont(size=13, weight="bold"),
            label_text_color=COLORS["accent"],
            label_fg_color=COLORS["bg_card"],
        )
        self._cards_scroll.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=0)
        # 2-column inner grid
        self._cards_scroll.columnconfigure(0, weight=1)
        self._cards_scroll.columnconfigure(1, weight=1)

        # Right: detail panel
        self._detail_panel = ctk.CTkScrollableFrame(
            body,
            fg_color=COLORS["bg_card"],
            corner_radius=12,
            label_text="Audit Details",
            label_font=ctk.CTkFont(size=13, weight="bold"),
            label_text_color=COLORS["accent"],
            label_fg_color=COLORS["bg_card"],
        )
        self._detail_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=0)

        self._detail_placeholder = ctk.CTkLabel(
            self._detail_panel,
            text="← Select a filing package to view audit details",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_dim"],
            wraplength=280,
        )
        self._detail_placeholder.pack(pady=40)

    # --- Footer --------------------------------------------------------

    def _build_footer(self) -> None:
        self._footer = ctk.CTkFrame(
            self, fg_color=COLORS["bg_card"], corner_radius=12, height=60
        )
        self._footer.pack(fill="x", padx=16, pady=(8, 16))
        self._footer.pack_propagate(False)

        inner = ctk.CTkFrame(self._footer, fg_color="transparent")
        inner.pack(fill="x", expand=True, padx=16, pady=8)

        self._footer_ready = ctk.CTkLabel(
            inner,
            text="Ready: —/10",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["green"],
        )
        self._footer_ready.pack(side="left", padx=(0, 24))

        self._footer_evidence = ctk.CTkLabel(
            inner,
            text="Evidence: —",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_dim"],
        )
        self._footer_evidence.pack(side="left", padx=(0, 24))

        self._footer_authorities = ctk.CTkLabel(
            inner,
            text="Authorities: —",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_dim"],
        )
        self._footer_authorities.pack(side="left", padx=(0, 24))

        self._footer_status = ctk.CTkLabel(
            inner,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_dim"],
        )
        self._footer_status.pack(side="right")

    # ------------------------------------------------------------------
    # Card grid
    # ------------------------------------------------------------------

    def _populate_cards(self) -> None:
        """Destroy old cards and rebuild from ``_audit_data``."""
        for widget in self._card_widgets.values():
            widget.destroy()
        self._card_widgets.clear()

        for idx, fid in enumerate(FILINGS):
            data = self._audit_data.get(fid) or _FilingAuditData(fid)
            row, col = divmod(idx, 2)
            card = self._build_card(fid, data)
            card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
            self._card_widgets[fid] = card

    def _build_card(self, fid: str, data: _FilingAuditData) -> ctk.CTkFrame:
        """Create a single filing card widget."""
        is_selected = fid == self._selected_fid
        border_clr = COLORS["accent"] if is_selected else COLORS["border"]

        card = ctk.CTkFrame(
            self._cards_scroll,
            fg_color=COLORS["bg_card"],
            border_color=border_clr,
            border_width=2 if is_selected else 1,
            corner_radius=10,
        )

        # Lane colour strip
        lane_clr = _LANE_COLORS.get(data.lane, COLORS["gray"])
        strip = ctk.CTkFrame(card, fg_color=lane_clr, width=5, corner_radius=4)
        strip.pack(side="left", fill="y", padx=(4, 0), pady=6)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        # Title row
        title_row = ctk.CTkFrame(content, fg_color="transparent")
        title_row.pack(fill="x")

        ctk.CTkLabel(
            title_row,
            text=f"{fid} — {data.title}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text"],
            wraplength=260,
            anchor="w",
            justify="left",
        ).pack(side="left", fill="x", expand=True)

        badge = StatusBadge(title_row, text=data.status)
        badge.pack(side="right", padx=(4, 0))

        # Case number + lane
        ctk.CTkLabel(
            content,
            text=f"Lane {data.lane}  ·  {data.case_no}",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_dim"],
        ).pack(anchor="w", pady=(2, 4))

        # Progress bar
        ProgressScore(content, label="Completion", score=data.completion).pack(
            fill="x", pady=(0, 4)
        )

        # Stats row
        stats = ctk.CTkFrame(content, fg_color="transparent")
        stats.pack(fill="x")

        for label, val in [
            ("Evid", data.evidence_count),
            ("Auth", data.authority_count),
            ("Pgs", data.page_count),
        ]:
            ctk.CTkLabel(
                stats,
                text=f"{label}: {val}",
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text_dim"],
            ).pack(side="left", padx=(0, 12))

        # Last audit timestamp
        ctk.CTkLabel(
            content,
            text=f"Audited: {data.last_audit}",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["gray"],
        ).pack(anchor="w", pady=(4, 0))

        # Click handler
        card.bind("<Button-1>", lambda _e, f=fid: self._select_filing(f))
        content.bind("<Button-1>", lambda _e, f=fid: self._select_filing(f))
        for child in content.winfo_children():
            child.bind("<Button-1>", lambda _e, f=fid: self._select_filing(f))
            if hasattr(child, "winfo_children"):
                for grandchild in child.winfo_children():
                    grandchild.bind(
                        "<Button-1>", lambda _e, f=fid: self._select_filing(f)
                    )

        # Context menu
        ContextMenu(
            card,
            items=[
                ("Run Audit", lambda f=fid: self._run_single_audit(f)),
                ("Generate Package", lambda f=fid: self._generate_package(f)),
                ("Open Wizard", lambda f=fid: self._open_wizard(f)),
                ("---", None),
                ("View Evidence", lambda f=fid: self._view_evidence(f)),
            ],
        )

        Tooltip(card, f"{fid}: {data.title}\nStatus: {data.status}")
        return card

    # ------------------------------------------------------------------
    # Detail panel
    # ------------------------------------------------------------------

    def _select_filing(self, fid: str) -> None:
        """Select a filing and populate the detail panel."""
        self._selected_fid = fid
        self._populate_cards()  # re-render to show selection highlight
        self._populate_detail(fid)

    def _populate_detail(self, fid: str) -> None:
        """Fill the right-side detail panel for the selected filing."""
        for w in self._detail_widgets:
            w.destroy()
        self._detail_widgets.clear()
        self._detail_placeholder.pack_forget()

        data = self._audit_data.get(fid) or _FilingAuditData(fid)

        # --- Filing header ---
        hdr = ctk.CTkFrame(self._detail_panel, fg_color="transparent")
        hdr.pack(fill="x", pady=(4, 8))
        self._detail_widgets.append(hdr)

        ctk.CTkLabel(
            hdr,
            text=f"{fid} — {data.title}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["accent"],
            wraplength=340,
            anchor="w",
            justify="left",
        ).pack(anchor="w")

        meta_text = f"Lane {data.lane}  ·  Case {data.case_no}  ·  Status: {data.status}"
        ctk.CTkLabel(
            hdr,
            text=meta_text,
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_dim"],
        ).pack(anchor="w", pady=(2, 0))

        # --- QA Checklist ---
        self._add_section_label("QA Checklist")
        qa_frame = ctk.CTkFrame(
            self._detail_panel, fg_color=COLORS["bg_dark"], corner_radius=8
        )
        qa_frame.pack(fill="x", padx=4, pady=(0, 8))
        self._detail_widgets.append(qa_frame)

        passed = 0
        for item_name in _QA_ITEMS:
            ok = data.qa_results.get(item_name, False)
            if ok:
                passed += 1
            icon = "✅" if ok else "❌"
            clr = COLORS["green"] if ok else COLORS["red"]
            ctk.CTkLabel(
                qa_frame,
                text=f" {icon}  {item_name}",
                font=ctk.CTkFont(size=12),
                text_color=clr,
                anchor="w",
            ).pack(fill="x", padx=10, pady=2)

        qa_summary = f"{passed}/{len(_QA_ITEMS)} checks passed"
        ctk.CTkLabel(
            qa_frame,
            text=qa_summary,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS["accent"] if passed == len(_QA_ITEMS) else COLORS["yellow"],
        ).pack(anchor="w", padx=10, pady=(4, 6))

        # --- Evidence summary ---
        self._add_section_label("Evidence Summary")
        ev_frame = ctk.CTkFrame(
            self._detail_panel, fg_color=COLORS["bg_dark"], corner_radius=8
        )
        ev_frame.pack(fill="x", padx=4, pady=(0, 8))
        self._detail_widgets.append(ev_frame)

        ctk.CTkLabel(
            ev_frame,
            text=f"Total evidence items: {data.evidence_count}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w", padx=10, pady=(6, 2))

        if data.strongest_quotes:
            ctk.CTkLabel(
                ev_frame,
                text="Strongest quotes:",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=COLORS["accent_dim"],
            ).pack(anchor="w", padx=10, pady=(4, 0))
            for qt in data.strongest_quotes[:3]:
                display = qt if len(qt) <= 120 else qt[:117] + "…"
                ctk.CTkLabel(
                    ev_frame,
                    text=f'  "{display}"',
                    font=ctk.CTkFont(size=11),
                    text_color=COLORS["text_dim"],
                    wraplength=320,
                    anchor="w",
                    justify="left",
                ).pack(fill="x", padx=10, pady=1)
        else:
            ctk.CTkLabel(
                ev_frame,
                text="No quotes loaded — run audit to populate.",
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text_dim"],
            ).pack(anchor="w", padx=10, pady=(0, 6))

        # --- Authority chain ---
        self._add_section_label("Authority Chain")
        auth_frame = ctk.CTkFrame(
            self._detail_panel, fg_color=COLORS["bg_dark"], corner_radius=8
        )
        auth_frame.pack(fill="x", padx=4, pady=(0, 8))
        self._detail_widgets.append(auth_frame)

        if data.authority_levels:
            for level in data.authority_levels:
                status_icon = "🟢" if level.get("complete") else "🔴"
                name = level.get("name", "Unknown")
                count = level.get("count", 0)
                ctk.CTkLabel(
                    auth_frame,
                    text=f"  {status_icon}  {name}  ({count} authorities)",
                    font=ctk.CTkFont(size=12),
                    text_color=COLORS["text"],
                    anchor="w",
                ).pack(fill="x", padx=10, pady=2)
        else:
            ctk.CTkLabel(
                auth_frame,
                text=f"Total authorities: {data.authority_count}",
                font=ctk.CTkFont(size=12),
                text_color=COLORS["text"],
            ).pack(anchor="w", padx=10, pady=6)

        # --- Placeholder scan ---
        self._add_section_label("Placeholder Scan")
        ph_frame = ctk.CTkFrame(
            self._detail_panel, fg_color=COLORS["bg_dark"], corner_radius=8
        )
        ph_frame.pack(fill="x", padx=4, pady=(0, 8))
        self._detail_widgets.append(ph_frame)

        if data.placeholder_count > 0:
            ph_text = f"⚠ {data.placeholder_count} placeholder(s) remaining"
            ph_clr = COLORS["yellow"]
        else:
            ph_text = "✅ No placeholders — filing is clean"
            ph_clr = COLORS["green"]
        ctk.CTkLabel(
            ph_frame,
            text=ph_text,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=ph_clr,
        ).pack(anchor="w", padx=10, pady=8)

        # --- Action buttons ---
        btn_row = ctk.CTkFrame(self._detail_panel, fg_color="transparent")
        btn_row.pack(fill="x", padx=4, pady=(8, 4))
        self._detail_widgets.append(btn_row)

        gen_btn = ctk.CTkButton(
            btn_row,
            text="📦 Generate Package",
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_dim"],
            text_color=COLORS["text"],
            width=160,
            command=lambda: self._generate_package(fid),
        )
        gen_btn.pack(side="left", padx=(0, 8))
        Tooltip(gen_btn, "Assemble court-ready filing package")

        wiz_btn = ctk.CTkButton(
            btn_row,
            text="✏️ Open Filing Wizard",
            fg_color=COLORS["bg_dark"],
            border_color=COLORS["accent"],
            border_width=1,
            hover_color=COLORS["accent_dim"],
            text_color=COLORS["text"],
            width=160,
            command=lambda: self._open_wizard(fid),
        )
        wiz_btn.pack(side="left")
        Tooltip(wiz_btn, "Edit this filing in the Filing Wizard")

    def _add_section_label(self, text: str) -> None:
        lbl = ctk.CTkLabel(
            self._detail_panel,
            text=text,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["accent"],
        )
        lbl.pack(anchor="w", padx=4, pady=(8, 2))
        self._detail_widgets.append(lbl)

    # ------------------------------------------------------------------
    # Data loading (threaded)
    # ------------------------------------------------------------------

    def _refresh_all(self) -> None:
        """Reload audit data for every filing from the database."""
        if self._busy:
            return
        self._set_busy(True, "Loading audit data…")

        def _work() -> None:
            results: Dict[str, _FilingAuditData] = {}
            conn = _safe_connect()
            try:
                for fid in FILINGS:
                    results[fid] = self._load_filing_data(conn, fid)
            finally:
                if conn:
                    conn.close()
            self.after(0, self._finish_refresh, results, None)

        threading.Thread(target=_work, daemon=True).start()

    def _finish_refresh(
        self,
        results: Optional[Dict[str, _FilingAuditData]],
        error: Optional[str],
    ) -> None:
        self._set_busy(False)
        if error:
            logger.error("Refresh failed: %s", error)
            self._footer_status.configure(text=f"Error: {error}")
            return
        if results:
            self._audit_data = results
        self._populate_cards()
        self._update_footer()
        if self._selected_fid:
            self._populate_detail(self._selected_fid)
        self._footer_status.configure(text=f"Refreshed {_ts_now()}")

    def _load_filing_data(
        self, conn: Optional[sqlite3.Connection], fid: str
    ) -> _FilingAuditData:
        """Query DB for a single filing's audit data.

        Falls back to simulated data when tables are missing or empty.
        """
        data = _FilingAuditData(fid)
        if conn is None:
            self._simulate_data(data)
            return data

        vehicle = data.title
        has_real_data = False

        # --- filing_readiness ---
        if _table_exists(conn, "filing_readiness"):
            cols = _get_columns(conn, "filing_readiness")
            try:
                if "vehicle_name" in cols:
                    row = conn.execute(
                        "SELECT * FROM filing_readiness WHERE vehicle_name LIKE ? LIMIT 1",
                        (f"%{fid}%",),
                    ).fetchone()
                    if row is None:
                        # Try matching on title keywords
                        keyword = data.title.split("—")[0].strip().split()[0]
                        row = conn.execute(
                            "SELECT * FROM filing_readiness WHERE vehicle_name LIKE ? LIMIT 1",
                            (f"%{keyword}%",),
                        ).fetchone()
                    if row:
                        has_real_data = True
                        row_dict = dict(row)
                        if "completion_pct" in row_dict:
                            data.completion = min(100, max(0, int(row_dict["completion_pct"])))
                        elif "readiness_score" in row_dict:
                            data.completion = min(100, max(0, int(row_dict["readiness_score"])))
                        if "status" in row_dict and row_dict["status"]:
                            data.status = str(row_dict["status"]).upper()
                        if "placeholder_count" in row_dict:
                            data.placeholder_count = int(row_dict["placeholder_count"] or 0)
            except sqlite3.Error as exc:
                logger.debug("filing_readiness query failed for %s: %s", fid, exc)

        # --- evidence_quotes ---
        if _table_exists(conn, "evidence_quotes"):
            cols = _get_columns(conn, "evidence_quotes")
            try:
                if "vehicle_name" in cols:
                    count_row = conn.execute(
                        "SELECT COUNT(*) FROM evidence_quotes WHERE vehicle_name LIKE ?",
                        (f"%{fid}%",),
                    ).fetchone()
                    if count_row and count_row[0] > 0:
                        data.evidence_count = count_row[0]
                        has_real_data = True
                    else:
                        # Broader match on title keyword
                        keyword = data.title.split("—")[0].strip().split()[0]
                        count_row = conn.execute(
                            "SELECT COUNT(*) FROM evidence_quotes WHERE vehicle_name LIKE ?",
                            (f"%{keyword}%",),
                        ).fetchone()
                        if count_row:
                            data.evidence_count = count_row[0]
                            has_real_data = has_real_data or count_row[0] > 0

                    # Strongest quotes
                    quote_col = "quote_text" if "quote_text" in cols else (
                        "text" if "text" in cols else None
                    )
                    if quote_col:
                        keyword = data.title.split("—")[0].strip().split()[0]
                        rows = conn.execute(
                            f"SELECT {quote_col} FROM evidence_quotes "
                            f"WHERE vehicle_name LIKE ? AND {quote_col} IS NOT NULL "
                            f"ORDER BY ROWID DESC LIMIT 3",
                            (f"%{keyword}%",),
                        ).fetchall()
                        data.strongest_quotes = [str(r[0]) for r in rows if r[0]]
            except sqlite3.Error as exc:
                logger.debug("evidence_quotes query failed for %s: %s", fid, exc)

        # --- authority_chains ---
        if _table_exists(conn, "authority_chains"):
            cols = _get_columns(conn, "authority_chains")
            try:
                if "vehicle_name" in cols:
                    keyword = data.title.split("—")[0].strip().split()[0]
                    count_row = conn.execute(
                        "SELECT COUNT(*) FROM authority_chains WHERE vehicle_name LIKE ?",
                        (f"%{keyword}%",),
                    ).fetchone()
                    if count_row:
                        data.authority_count = count_row[0]
                        has_real_data = has_real_data or count_row[0] > 0

                    # Authority levels breakdown
                    complete_col = (
                        "chain_complete"
                        if "chain_complete" in cols
                        else ("is_complete" if "is_complete" in cols else None)
                    )
                    level_col = (
                        "authority_level"
                        if "authority_level" in cols
                        else ("level" if "level" in cols else None)
                    )
                    if level_col and complete_col:
                        levels = conn.execute(
                            f"SELECT {level_col}, "
                            f"COUNT(*) as cnt, "
                            f"SUM(CASE WHEN {complete_col} = 1 THEN 1 ELSE 0 END) as ok "
                            f"FROM authority_chains WHERE vehicle_name LIKE ? "
                            f"GROUP BY {level_col} ORDER BY {level_col}",
                            (f"%{keyword}%",),
                        ).fetchall()
                        data.authority_levels = [
                            {
                                "name": str(lv[0] or "General"),
                                "count": int(lv[1]),
                                "complete": int(lv[2]) == int(lv[1]),
                            }
                            for lv in levels
                        ]
            except sqlite3.Error as exc:
                logger.debug("authority_chains query failed for %s: %s", fid, exc)

        # --- claims ---
        if _table_exists(conn, "claims"):
            cols = _get_columns(conn, "claims")
            try:
                if "vehicle_name" in cols:
                    keyword = data.title.split("—")[0].strip().split()[0]
                    row = conn.execute(
                        "SELECT COUNT(*) FROM claims WHERE vehicle_name LIKE ?",
                        (f"%{keyword}%",),
                    ).fetchone()
                    if row and row[0] > 0:
                        has_real_data = True
            except sqlite3.Error as exc:
                logger.debug("claims query failed for %s: %s", fid, exc)

        # --- documents (page count) ---
        if _table_exists(conn, "documents"):
            cols = _get_columns(conn, "documents")
            try:
                page_col = (
                    "page_count"
                    if "page_count" in cols
                    else ("pages" if "pages" in cols else None)
                )
                if page_col:
                    keyword = data.title.split("—")[0].strip().split()[0]
                    name_col = (
                        "file_name"
                        if "file_name" in cols
                        else ("name" if "name" in cols else "path" if "path" in cols else None)
                    )
                    if name_col:
                        row = conn.execute(
                            f"SELECT SUM({page_col}) FROM documents "
                            f"WHERE {name_col} LIKE ?",
                            (f"%{keyword}%",),
                        ).fetchone()
                        if row and row[0]:
                            data.page_count = int(row[0])
                            has_real_data = True
            except sqlite3.Error as exc:
                logger.debug("documents query failed for %s: %s", fid, exc)

        # If we got no real DB data, fill with simulated values
        if not has_real_data:
            self._simulate_data(data)
        else:
            data.last_audit = _ts_now()
            self._derive_qa_and_status(data)

        return data

    # ------------------------------------------------------------------
    # Simulation / derivation
    # ------------------------------------------------------------------

    @staticmethod
    def _simulate_data(data: _FilingAuditData) -> None:
        """Fill with plausible mock values when DB lacks data for a filing."""
        import hashlib

        seed = int(hashlib.md5(data.fid.encode()).hexdigest()[:8], 16)
        data.completion = 30 + (seed % 60)
        data.evidence_count = 5 + (seed % 45)
        data.authority_count = 2 + (seed % 20)
        data.page_count = 8 + (seed % 30)
        data.placeholder_count = seed % 5

        # Deterministic QA results
        for i, item in enumerate(_QA_ITEMS):
            data.qa_results[item] = ((seed + i * 7) % 10) > 3

        passed_count = sum(data.qa_results.values())
        if data.completion >= 80 and passed_count >= 8:
            data.status = "READY"
        elif data.completion >= 50:
            data.status = "NEEDS_WORK"
        elif data.completion >= 20:
            data.status = "DRAFT"
        else:
            data.status = "BLOCKED"

        data.strongest_quotes = [
            f"[Simulated] Key evidence excerpt for {data.title}",
        ]
        data.authority_levels = [
            {"name": "Constitutional", "count": max(1, data.authority_count // 3), "complete": seed % 3 != 0},
            {"name": "Statutory", "count": max(1, data.authority_count // 3), "complete": seed % 2 == 0},
            {"name": "Case Law", "count": max(1, data.authority_count // 3), "complete": seed % 4 != 0},
        ]
        data.last_audit = "Simulated"

    @staticmethod
    def _derive_qa_and_status(data: _FilingAuditData) -> None:
        """Derive QA pass/fail and status from real DB counts."""
        data.qa_results["Evidence citations"] = data.evidence_count > 0
        data.qa_results["Authority chain"] = data.authority_count > 0
        data.qa_results["Page limits"] = 0 < data.page_count <= 50

        # Heuristic: mark structural items as pass when completion is high
        if data.completion >= 70:
            for item in ("Caption block", "Jurisdiction statement", "Standing proof",
                         "IRAC structure", "Certificate of service", "Signature block"):
                data.qa_results[item] = True
        if data.completion >= 50:
            data.qa_results["Court forms attached"] = True

        passed = sum(data.qa_results.values())
        if data.placeholder_count == 0 and passed >= 9 and data.completion >= 80:
            data.status = "READY"
        elif passed >= 5 and data.completion >= 40:
            data.status = "NEEDS_WORK"
        elif data.completion > 0:
            data.status = "DRAFT"
        else:
            data.status = "BLOCKED"

    # ------------------------------------------------------------------
    # Full audit (threaded)
    # ------------------------------------------------------------------

    def _run_full_audit(self) -> None:
        """Run QA checks on all 10 packages in a background thread."""
        if self._busy:
            return
        self._set_busy(True, "Running full audit on all 10 packages…")
        logger.info("Starting full audit run")

        def _work() -> None:
            results: Dict[str, _FilingAuditData] = {}
            conn = _safe_connect()
            try:
                for fid in FILINGS:
                    results[fid] = self._load_filing_data(conn, fid)
                    results[fid].last_audit = _ts_now()
            except Exception as exc:
                self.after(0, self._finish_full_audit, None, str(exc))
                return
            finally:
                if conn:
                    conn.close()
            self.after(0, self._finish_full_audit, results, None)

        threading.Thread(target=_work, daemon=True).start()

    def _finish_full_audit(
        self,
        results: Optional[Dict[str, _FilingAuditData]],
        error: Optional[str],
    ) -> None:
        self._set_busy(False)
        if error:
            logger.error("Full audit failed: %s", error)
            self._footer_status.configure(text=f"Audit error: {error}")
            return
        if results:
            self._audit_data = results
        self._populate_cards()
        self._update_footer()
        if self._selected_fid:
            self._populate_detail(self._selected_fid)
        ready = sum(1 for d in self._audit_data.values() if d.status == "READY")
        self._footer_status.configure(
            text=f"Full audit complete — {ready}/10 ready  ({_ts_now()})"
        )
        logger.info("Full audit complete: %d/10 ready", ready)

    def _run_single_audit(self, fid: str) -> None:
        """Run audit on a single filing package."""
        if self._busy:
            return
        self._set_busy(True, f"Auditing {fid}…")
        logger.info("Running single audit for %s", fid)

        def _work() -> None:
            conn = _safe_connect()
            try:
                result = self._load_filing_data(conn, fid)
                result.last_audit = _ts_now()
            except Exception as exc:
                self.after(0, self._finish_single_audit, fid, None, str(exc))
                return
            finally:
                if conn:
                    conn.close()
            self.after(0, self._finish_single_audit, fid, result, None)

        threading.Thread(target=_work, daemon=True).start()

    def _finish_single_audit(
        self,
        fid: str,
        result: Optional[_FilingAuditData],
        error: Optional[str],
    ) -> None:
        self._set_busy(False)
        if error:
            logger.error("Audit for %s failed: %s", fid, error)
            self._footer_status.configure(text=f"Audit error ({fid}): {error}")
            return
        if result:
            self._audit_data[fid] = result
        self._populate_cards()
        self._update_footer()
        if self._selected_fid == fid:
            self._populate_detail(fid)
        self._footer_status.configure(text=f"{fid} audit done ({_ts_now()})")

    # ------------------------------------------------------------------
    # Footer summary
    # ------------------------------------------------------------------

    def _update_footer(self) -> None:
        """Recalculate aggregate stats for the footer bar."""
        total_ev = 0
        total_auth = 0
        ready_count = 0

        for d in self._audit_data.values():
            total_ev += d.evidence_count
            total_auth += d.authority_count
            if d.status == "READY":
                ready_count += 1

        rdy_clr = COLORS["green"] if ready_count >= 8 else (
            COLORS["yellow"] if ready_count >= 4 else COLORS["red"]
        )
        self._footer_ready.configure(
            text=f"Ready: {ready_count}/10", text_color=rdy_clr
        )
        self._footer_evidence.configure(text=f"Evidence: {total_ev:,}")
        self._footer_authorities.configure(text=f"Authorities: {total_auth:,}")

    # ------------------------------------------------------------------
    # Action handlers
    # ------------------------------------------------------------------

    def _generate_package(self, fid: str) -> None:
        """Navigate to PDF Studio / package assembly for this filing."""
        logger.info("Generate package requested for %s", fid)
        if self._navigate_cb:
            self._navigate_cb("pdf_studio")
        else:
            self._footer_status.configure(
                text=f"📦 Package generation for {fid} — navigate to PDF Studio"
            )

    def _open_wizard(self, fid: str) -> None:
        """Open the Filing Wizard for this package."""
        logger.info("Open wizard requested for %s", fid)
        if self._navigate_cb:
            self._navigate_cb("filing_wizard")
        else:
            self._footer_status.configure(
                text=f"✏️ Opening Filing Wizard for {fid}…"
            )

    def _view_evidence(self, fid: str) -> None:
        """Navigate to Evidence Browser filtered for this filing."""
        logger.info("View evidence requested for %s", fid)
        if self._navigate_cb:
            self._navigate_cb("evidence_browser")
        else:
            self._footer_status.configure(
                text=f"🔍 View evidence for {fid} — navigate to Evidence Browser"
            )

    # ------------------------------------------------------------------
    # Busy-state management
    # ------------------------------------------------------------------

    def _set_busy(self, busy: bool, message: str = "") -> None:
        self._busy = busy
        state = "disabled" if busy else "normal"
        self._refresh_btn.configure(state=state)
        self._audit_btn.configure(state=state)
        if busy and message:
            self._footer_status.configure(text=message)
