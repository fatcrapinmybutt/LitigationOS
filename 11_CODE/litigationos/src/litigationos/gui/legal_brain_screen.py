"""Legal Brain — Full-text search interface for Michigan law.

Search across MCR (Court Rules), MCL (Statutes), MRE (Evidence Rules),
and Case Law with cross-reference discovery and filing integration.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Callable, Optional

import customtkinter as ctk

from litigationos.gui.widgets import COLORS, ContextMenu, DataCard, Tooltip

if TYPE_CHECKING:
    from litigationos.db.connection import DatabaseManager

try:
    from litigationos.engines.legal_knowledge import LegalKnowledgeEngine

    _HAS_ENGINE = True
except ImportError:
    _HAS_ENGINE = False

logger = logging.getLogger(__name__)

# Source-type badge colours
_SOURCE_COLORS: dict[str, str] = {
    "MCR": COLORS["blue"],
    "MCL": COLORS["green"],
    "MRE": COLORS["orange"],
    "CASE": COLORS["purple"],
    "CANON": COLORS["yellow"],
}

_FILTER_MAP: dict[str, str | None] = {
    "All Sources": None,
    "Court Rules (MCR)": "MCR",
    "Statutes (MCL)": "MCL",
    "Evidence Rules (MRE)": "MRE",
    "Case Law": "CASE",
}


class LegalBrainFrame(ctk.CTkFrame):
    """Full-text search interface for Michigan legal knowledge."""

    def __init__(
        self,
        parent: Any,
        db: DatabaseManager | None = None,
        navigate_cb: Optional[Callable[[str], None]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._db = db
        self._navigate_cb = navigate_cb

        # Engine (optional — degrades gracefully)
        self._engine: LegalKnowledgeEngine | None = None
        if _HAS_ENGINE:
            try:
                self._engine = LegalKnowledgeEngine()
            except Exception:
                logger.exception("Failed to initialise LegalKnowledgeEngine")

        # State
        self._results: list[dict[str, Any]] = []
        self._selected: dict[str, Any] | None = None
        self._recent: list[dict[str, Any]] = []
        self._result_widgets: list[ctk.CTkBaseClass] = []
        self._side_widgets: list[ctk.CTkBaseClass] = []

        # Build UI
        self._build_header()
        self._build_search_bar()
        self._build_body()

        # Initial stats
        self._refresh_stats()

    # ------------------------------------------------------------------
    # Layout builders
    # ------------------------------------------------------------------

    def _build_header(self) -> None:
        """Top bar with title and subtitle."""
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=10)
        header.pack(fill="x", padx=16, pady=(16, 4))

        ctk.CTkLabel(
            header,
            text="⚖ Legal Brain",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(side="left", padx=16, pady=10)

        ctk.CTkLabel(
            header,
            text="Search Michigan Law — MCR • MCL • MRE • Case Law",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_dim"],
        ).pack(side="left", padx=8, pady=10)

    def _build_search_bar(self) -> None:
        """Search entry, button, filter dropdown, and result count."""
        bar = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=10)
        bar.pack(fill="x", padx=16, pady=(4, 8))

        # Search entry
        self._search_var = ctk.StringVar()
        self._search_entry = ctk.CTkEntry(
            bar,
            textvariable=self._search_var,
            placeholder_text="Search rules, statutes, case law…",
            width=400,
            height=38,
            border_color=COLORS["accent"],
            border_width=2,
            corner_radius=8,
            font=ctk.CTkFont(size=13),
        )
        self._search_entry.pack(side="left", padx=(16, 6), pady=10)
        self._search_entry.bind("<Return>", lambda _e: self._search())
        Tooltip(self._search_entry, "FTS5 syntax: AND, OR, NOT, \"phrases\"")

        # Search button
        search_btn = ctk.CTkButton(
            bar,
            text="🔍 Search",
            width=100,
            height=38,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            corner_radius=8,
            command=self._search,
        )
        search_btn.pack(side="left", padx=(0, 10), pady=10)
        Tooltip(search_btn, "Execute search (Enter)")

        # Filter dropdown
        self._filter_var = ctk.StringVar(value="All Sources")
        self._filter_menu = ctk.CTkOptionMenu(
            bar,
            values=list(_FILTER_MAP.keys()),
            variable=self._filter_var,
            width=180,
            height=34,
            fg_color=COLORS["border"],
            button_color=COLORS["accent_dim"],
            button_hover_color=COLORS["accent"],
            corner_radius=8,
            command=self._filter_changed,
        )
        self._filter_menu.pack(side="left", padx=(0, 10), pady=10)
        Tooltip(self._filter_menu, "Filter results by source type")

        # Result count
        self._count_label = ctk.CTkLabel(
            bar,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_dim"],
        )
        self._count_label.pack(side="right", padx=16, pady=10)

    def _build_body(self) -> None:
        """Two-column layout: results (left 70 %) + side panel (right 30 %)."""
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        body.columnconfigure(0, weight=7)
        body.columnconfigure(1, weight=3)
        body.rowconfigure(0, weight=1)

        # --- Results panel (scrollable) ---
        self._results_scroll = ctk.CTkScrollableFrame(
            body,
            fg_color=COLORS["bg_dark"],
            corner_radius=10,
            scrollbar_button_color=COLORS["accent_dim"],
        )
        self._results_scroll.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        self._empty_label = ctk.CTkLabel(
            self._results_scroll,
            text="Enter a query above to search Michigan law",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_dim"],
        )
        self._empty_label.pack(pady=40)

        # --- Side panel ---
        self._side_panel = ctk.CTkScrollableFrame(
            body,
            fg_color=COLORS["bg_card"],
            corner_radius=10,
            scrollbar_button_color=COLORS["accent_dim"],
        )
        self._side_panel.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        self._build_side_stats()
        self._build_side_recent()
        self._build_side_xrefs()
        self._build_side_filings()

    # -- Side panel sections --------------------------------------------------

    def _build_side_stats(self) -> None:
        """Quick Stats section with DataCards."""
        ctk.CTkLabel(
            self._side_panel,
            text="📊 Quick Stats",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w", padx=12, pady=(12, 4))

        grid = ctk.CTkFrame(self._side_panel, fg_color="transparent")
        grid.pack(fill="x", padx=8, pady=(0, 8))
        grid.columnconfigure((0, 1), weight=1)

        self._stat_mcr = DataCard(grid, title="MCR Rules", value="—", color=COLORS["blue"])
        self._stat_mcr.grid(row=0, column=0, sticky="ew", padx=4, pady=4)

        self._stat_mcl = DataCard(grid, title="MCL Statutes", value="—", color=COLORS["green"])
        self._stat_mcl.grid(row=0, column=1, sticky="ew", padx=4, pady=4)

        self._stat_mre = DataCard(grid, title="MRE Rules", value="—", color=COLORS["orange"])
        self._stat_mre.grid(row=1, column=0, sticky="ew", padx=4, pady=4)

        self._stat_cases = DataCard(grid, title="Case Law", value="—", color=COLORS["purple"])
        self._stat_cases.grid(row=1, column=1, sticky="ew", padx=4, pady=4)

    def _build_side_recent(self) -> None:
        """Recently Viewed list."""
        ctk.CTkLabel(
            self._side_panel,
            text="🕑 Recently Viewed",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w", padx=12, pady=(12, 4))

        self._recent_frame = ctk.CTkFrame(self._side_panel, fg_color="transparent")
        self._recent_frame.pack(fill="x", padx=8, pady=(0, 8))

        self._recent_empty = ctk.CTkLabel(
            self._recent_frame,
            text="No rules viewed yet",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_dim"],
        )
        self._recent_empty.pack(anchor="w", padx=4, pady=4)

    def _build_side_xrefs(self) -> None:
        """Cross-References section (populated on result selection)."""
        ctk.CTkLabel(
            self._side_panel,
            text="🔗 Cross-References",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w", padx=12, pady=(12, 4))

        self._xref_frame = ctk.CTkFrame(self._side_panel, fg_color="transparent")
        self._xref_frame.pack(fill="x", padx=8, pady=(0, 8))

        self._xref_empty = ctk.CTkLabel(
            self._xref_frame,
            text="Select a result to view cross-references",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_dim"],
        )
        self._xref_empty.pack(anchor="w", padx=4, pady=4)

    def _build_side_filings(self) -> None:
        """Filing Authorities section."""
        ctk.CTkLabel(
            self._side_panel,
            text="📁 Filing Authorities",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w", padx=12, pady=(12, 4))

        self._filing_frame = ctk.CTkFrame(self._side_panel, fg_color="transparent")
        self._filing_frame.pack(fill="x", padx=8, pady=(0, 12))

        self._filing_empty = ctk.CTkLabel(
            self._filing_frame,
            text="Select a result to view filing usage",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_dim"],
        )
        self._filing_empty.pack(anchor="w", padx=4, pady=4)

    # ------------------------------------------------------------------
    # Search / filter
    # ------------------------------------------------------------------

    def _search(self, query: str | None = None) -> None:
        """Execute full-text search via LegalKnowledgeEngine."""
        if query is None:
            query = self._search_var.get().strip()
        if not query:
            return

        source_type = _FILTER_MAP.get(self._filter_var.get())

        if self._engine is None:
            self._results = []
            self._count_label.configure(text="Engine unavailable")
            self._display_results([])
            return

        try:
            self._results = self._engine.search(
                query, source_type=source_type, limit=50
            )
        except Exception:
            logger.exception("Search failed for query=%s", query)
            self._results = []

        count = len(self._results)
        self._count_label.configure(
            text=f"{count} result{'s' if count != 1 else ''} found"
        )
        self._display_results(self._results)

    def _filter_changed(self, source_type: str) -> None:
        """Re-run the current search with the new filter."""
        if self._search_var.get().strip():
            self._search()

    # ------------------------------------------------------------------
    # Display results
    # ------------------------------------------------------------------

    def _display_results(self, results: list[dict[str, Any]]) -> None:
        """Render result cards inside the scrollable panel."""
        for w in self._result_widgets:
            w.destroy()
        self._result_widgets.clear()

        if self._empty_label.winfo_exists():
            self._empty_label.pack_forget()

        if not results:
            lbl = ctk.CTkLabel(
                self._results_scroll,
                text="No results — try a different query or filter",
                font=ctk.CTkFont(size=13),
                text_color=COLORS["text_dim"],
            )
            lbl.pack(pady=40)
            self._result_widgets.append(lbl)
            return

        for result in results:
            card = self._build_result_card(result)
            self._result_widgets.append(card)

    def _build_result_card(self, result: dict[str, Any]) -> ctk.CTkFrame:
        """Build a single result card with badge, text, and context menu."""
        card = ctk.CTkFrame(
            self._results_scroll,
            fg_color=COLORS["bg_card"],
            corner_radius=8,
            border_width=0,
        )
        card.pack(fill="x", padx=4, pady=4)

        # Pink left accent via inner wrapper
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=(3, 0))

        accent_bar = ctk.CTkFrame(card, fg_color=COLORS["accent"], width=4, corner_radius=2)
        accent_bar.place(relx=0, rely=0.1, relheight=0.8, width=4)

        # Top row: source badge + title
        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(10, 2))

        src = result.get("source_type", "")
        badge_colour = _SOURCE_COLORS.get(src, COLORS["gray"])
        badge = ctk.CTkLabel(
            top,
            text=f" {src} ",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=badge_colour,
            corner_radius=4,
            text_color="#000000",
            width=50,
        )
        badge.pack(side="left", padx=(0, 8))

        rule_num = result.get("rule_number", "")
        title_text = result.get("title", rule_num)
        if rule_num and title_text and rule_num not in title_text:
            title_text = f"{rule_num} — {title_text}"

        title_lbl = ctk.CTkLabel(
            top,
            text=title_text,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text"],
            anchor="w",
        )
        title_lbl.pack(side="left", fill="x", expand=True)

        # Relevance score
        rank = result.get("rank")
        if rank is not None:
            try:
                score_text = f"{float(rank):.1f}"
            except (TypeError, ValueError):
                score_text = str(rank)
            ctk.CTkLabel(
                top,
                text=f"⚡ {score_text}",
                font=ctk.CTkFont(size=11),
                text_color=COLORS["accent"],
            ).pack(side="right", padx=(8, 0))

        # Snippet
        snippet = result.get("snippet", "")
        if snippet:
            ctk.CTkLabel(
                inner,
                text=snippet,
                font=ctk.CTkFont(size=12),
                text_color=COLORS["text_dim"],
                anchor="w",
                wraplength=600,
                justify="left",
            ).pack(fill="x", padx=16, pady=(0, 10))

        # Click to select
        for widget in (card, inner, title_lbl):
            widget.bind("<Button-1>", lambda _e, r=result: self._select_result(r))

        # Tooltip with extra detail
        tip_text = f"{src} {rule_num}"
        if snippet:
            tip_text += f"\n{snippet[:120]}…" if len(snippet) > 120 else f"\n{snippet}"
        Tooltip(card, tip_text)

        # Right-click context menu
        ContextMenu(
            card,
            items=[
                ("Copy Citation", lambda r=result: self._copy_citation(r)),
                ("Add to Filing", lambda r=result: self._add_to_filing(r)),
                ("---", None),
                ("View Full Text", lambda r=result: self._view_full_text(r)),
            ],
        )

        return card

    # ------------------------------------------------------------------
    # Selection & side panel updates
    # ------------------------------------------------------------------

    def _select_result(self, result: dict[str, Any]) -> None:
        """Show details and cross-references in the side panel."""
        self._selected = result

        # Track in recently viewed (max 5, no dupes)
        rule_num = result.get("rule_number", "")
        self._recent = [r for r in self._recent if r.get("rule_number") != rule_num]
        self._recent.insert(0, result)
        self._recent = self._recent[:5]
        self._refresh_recent()

        # Cross-references
        self._refresh_xrefs(result)

        # Filing authorities
        self._refresh_filings(result)

    def _refresh_recent(self) -> None:
        """Rebuild the Recently Viewed section."""
        for w in list(self._recent_frame.winfo_children()):
            w.destroy()

        if not self._recent:
            ctk.CTkLabel(
                self._recent_frame,
                text="No rules viewed yet",
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text_dim"],
            ).pack(anchor="w", padx=4, pady=4)
            return

        for item in self._recent:
            src = item.get("source_type", "")
            rule = item.get("rule_number", "")
            colour = _SOURCE_COLORS.get(src, COLORS["text_dim"])
            row = ctk.CTkFrame(self._recent_frame, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(
                row,
                text=f"  {src}",
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=colour,
                width=40,
            ).pack(side="left")
            lbl = ctk.CTkLabel(
                row,
                text=rule or item.get("title", "—"),
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text"],
                anchor="w",
            )
            lbl.pack(side="left", fill="x", expand=True, padx=4)
            lbl.bind("<Button-1>", lambda _e, r=item: self._select_result(r))
            Tooltip(lbl, f"Click to re-select {rule}")

    def _refresh_xrefs(self, result: dict[str, Any]) -> None:
        """Load cross-references for the selected result."""
        for w in list(self._xref_frame.winfo_children()):
            w.destroy()

        if self._engine is None:
            ctk.CTkLabel(
                self._xref_frame,
                text="Engine unavailable",
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text_dim"],
            ).pack(anchor="w", padx=4, pady=4)
            return

        src = result.get("source_type", "")
        rule = result.get("rule_number", "")
        try:
            xrefs = self._engine.get_cross_references(src, rule)
        except Exception:
            logger.exception("Failed to load cross-references")
            xrefs = []

        if not xrefs:
            ctk.CTkLabel(
                self._xref_frame,
                text="No cross-references found",
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text_dim"],
            ).pack(anchor="w", padx=4, pady=4)
            return

        for xref in xrefs[:10]:
            t_type = xref.get("target_type", "")
            t_num = xref.get("target_number", "")
            rel = xref.get("relationship", "related")
            colour = _SOURCE_COLORS.get(t_type, COLORS["text_dim"])
            row = ctk.CTkFrame(self._xref_frame, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(
                row,
                text=f"  {t_type}",
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=colour,
                width=40,
            ).pack(side="left")
            ctk.CTkLabel(
                row,
                text=f"{t_num} ({rel})",
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text"],
                anchor="w",
            ).pack(side="left", fill="x", expand=True, padx=4)

    def _refresh_filings(self, result: dict[str, Any]) -> None:
        """Show filings that reference the selected authority."""
        for w in list(self._filing_frame.winfo_children()):
            w.destroy()

        if self._db is None:
            ctk.CTkLabel(
                self._filing_frame,
                text="No database connection",
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text_dim"],
            ).pack(anchor="w", padx=4, pady=4)
            return

        rule = result.get("rule_number", "")
        if not rule:
            return

        try:
            rows = self._db.fetchall(
                "SELECT DISTINCT vehicle_name FROM filing_readiness "
                "WHERE authority_list LIKE ? ORDER BY vehicle_name LIMIT 10",
                (f"%{rule}%",),
            )
            filings = [dict(r) for r in rows] if rows else []
        except Exception:
            logger.debug("filing_readiness query failed — table may not exist")
            filings = []

        if not filings:
            ctk.CTkLabel(
                self._filing_frame,
                text="No filings reference this authority",
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text_dim"],
            ).pack(anchor="w", padx=4, pady=4)
            return

        for f in filings:
            name = f.get("vehicle_name", "")
            ctk.CTkLabel(
                self._filing_frame,
                text=f"📄 {name}",
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text"],
                anchor="w",
            ).pack(fill="x", padx=4, pady=1)

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def _refresh_stats(self) -> None:
        """Update stat cards with current DB counts."""
        stats: dict[str, int] = {}
        if self._engine is not None:
            try:
                stats = self._engine.get_stats()
            except Exception:
                logger.exception("Failed to load legal knowledge stats")

        self._stat_mcr.set(stats.get("mcr_rules", 0))
        self._stat_mcl.set(stats.get("mcl_statutes", 0))
        self._stat_mre.set(stats.get("mre_rules", 0))
        self._stat_cases.set(stats.get("case_law", 0))

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _copy_citation(self, result: dict[str, Any]) -> None:
        """Copy a formatted citation to the system clipboard."""
        src = result.get("source_type", "")
        rule = result.get("rule_number", "")
        title = result.get("title", "")
        citation = f"{rule}" if rule else title
        if src and not citation.upper().startswith(src):
            citation = f"{src} {citation}"
        try:
            self.clipboard_clear()
            self.clipboard_append(citation)
            self._count_label.configure(text=f"Copied: {citation}")
        except Exception:
            logger.exception("Clipboard copy failed")

    def _add_to_filing(self, result: dict[str, Any]) -> None:
        """Placeholder — navigate to filing wizard with pre-filled authority."""
        if self._navigate_cb:
            self._navigate_cb("filing_wizard")

    def _view_full_text(self, result: dict[str, Any]) -> None:
        """Show full text in a pop-up window."""
        if self._engine is None:
            return

        src = result.get("source_type", "")
        rule = result.get("rule_number", "")
        full: dict[str, Any] | None = None

        try:
            if src == "MCR":
                full = self._engine.get_rule(rule)
            elif src == "MCL":
                full = self._engine.get_statute(rule)
            elif src == "MRE":
                full = self._engine.get_evidence_rule(rule)
            elif src == "CASE":
                full = self._engine.get_case(rule)
        except Exception:
            logger.exception("Failed to retrieve full text for %s", rule)

        text = (full or {}).get("full_text", result.get("snippet", "No text available"))

        win = ctk.CTkToplevel(self)
        win.title(f"{src} {rule}")
        win.geometry("700x500")
        win.configure(fg_color=COLORS["bg_dark"])

        ctk.CTkLabel(
            win,
            text=f"{src} {rule}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(padx=16, pady=(16, 8))

        tb = ctk.CTkTextbox(
            win,
            font=ctk.CTkFont(size=12),
            fg_color=COLORS["bg_card"],
            text_color=COLORS["text"],
            wrap="word",
            corner_radius=8,
        )
        tb.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        tb.insert("1.0", text)
        tb.configure(state="disabled")

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Full refresh: stats + re-run search if query exists."""
        self._refresh_stats()
        if self._search_var.get().strip():
            self._search()
