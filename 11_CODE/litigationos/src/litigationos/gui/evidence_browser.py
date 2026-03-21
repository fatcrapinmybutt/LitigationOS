"""Evidence browser screen — search, browse, tag, and authenticate.

Provides FTS5 search, a results table, filter panel, detail view with
authentication status, Bates assignment, and exhibit list export.
Uses the real litigation_context.db via LitigationBridge when available,
falling back to the app-schema EvidenceEngine otherwise.
"""

from __future__ import annotations

import csv
import io
import logging
import sqlite3
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import TYPE_CHECKING, Optional

import customtkinter as ctk

from litigationos.gui.widgets import COLORS, ContextMenu, StatusBadge, Tooltip
if TYPE_CHECKING:
    from litigationos.app import App

from litigationos.engines.evidence import VALID_EVIDENCE_TYPES, EvidenceEngine

try:
    from litigationos.db.litigation_bridge import LitigationBridge
    _HAS_BRIDGE = True
except ImportError:
    _HAS_BRIDGE = False

logger = logging.getLogger(__name__)

_TYPE_COLORS = {
    "document": "#3B82F6",
    "photo": "#8B5CF6",
    "screenshot": "#EC4899",
    "recording": "#F97316",
    "email": "#06B6D4",
    "text_message": "#14B8A6",
    "court_order": "#6366F1",
    "financial": "#EAB308",
    "declaration": "#10B981",
}


class EvidenceBrowserFrame(ctk.CTkFrame):
    """Evidence search, browse, tag, and authenticate."""

    def __init__(self, parent: ctk.CTkFrame, app: "App"):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        try:
            self.engine = EvidenceEngine(app.db)
        except Exception:
            self.engine = None
        self._evidence: list[dict] = []
        self._selected: Optional[dict] = None
        self._bates_map: dict[int, str] = {}
        self._exhibit_map: dict[int, str] = {}
        self._filing_map: dict[int, str] = {}

        # Bridge to real litigation_context.db
        self._bridge: Optional[LitigationBridge] = None  # type: ignore[assignment]
        if _HAS_BRIDGE:
            try:
                db_path = getattr(app, '_db_path', None) or getattr(app.db, 'db_path', None)
                self._bridge = LitigationBridge(str(db_path) if db_path else None)
                if not self._bridge.is_real_db:
                    self._bridge = None
            except Exception:
                self._bridge = None

        # Load enrichment data (Bates, exhibits, filing links) in background
        threading.Thread(target=self._load_enrichment_data, daemon=True).start()

        self._build_ui()
        self.refresh()

    # -- Layout ---------------------------------------------------------------

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ── Title ──
        ctk.CTkLabel(self, text="🔍 MBP LLC — Evidence Browser", font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=16, pady=(12, 4)
        )

        # ── Search bar ──
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.grid(row=1, column=0, sticky="ew", padx=16, pady=4)
        search_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(search_frame, text="🔍").grid(row=0, column=0, padx=(0, 4))
        self._search_entry = ctk.CTkEntry(search_frame, placeholder_text="FTS5 search evidence…")
        self._search_entry.grid(row=0, column=1, sticky="ew")
        self._search_entry.bind("<Return>", lambda _: self._do_search())
        search_btn = ctk.CTkButton(search_frame, text="Search", width=80, command=self._do_search)
        search_btn.grid(row=0, column=2, padx=(8, 0))
        Tooltip(search_btn, "Search across evidence items using FTS5 full-text search")
        clear_btn = ctk.CTkButton(search_frame, text="Clear", width=60, fg_color="#6B7280",
                       command=self._clear_search)
        clear_btn.grid(row=0, column=3, padx=(4, 0))
        Tooltip(clear_btn, "Clear search and show all evidence")

        # ── Main body: filters + table + detail ──
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=2, column=0, sticky="nsew", padx=12, pady=(4, 8))
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        self._build_filter_panel(body)
        self._build_results_table(body)
        self._build_detail_panel(body)

    # -- Filter panel ---------------------------------------------------------

    def _build_filter_panel(self, parent: ctk.CTkFrame) -> None:
        panel = ctk.CTkFrame(parent, width=180)
        panel.grid(row=0, column=0, sticky="ns", padx=(0, 4))
        panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(panel, text="Filters", font=ctk.CTkFont(weight="bold")).pack(
            padx=8, pady=(8, 4), anchor="w"
        )

        # Category filter (populated from bridge or fallback to evidence types)
        ctk.CTkLabel(panel, text="Category", font=ctk.CTkFont(size=11)).pack(
            padx=8, anchor="w"
        )
        cat_values = ["All"]
        if self._bridge:
            cats = self._bridge.get_evidence_categories()
            if cats:
                cat_values += cats
        if len(cat_values) == 1:
            cat_values += [t.replace("_", " ").title() for t in VALID_EVIDENCE_TYPES]
        self._category_combo = ctk.CTkComboBox(
            panel, values=cat_values, command=lambda _: self._apply_filters()
        )
        self._category_combo.set("All")
        self._category_combo.pack(padx=8, fill="x", pady=(0, 4))

        # Lane filter (populated from bridge)
        ctk.CTkLabel(panel, text="Lane", font=ctk.CTkFont(size=11)).pack(
            padx=8, anchor="w"
        )
        lane_values = ["All"]
        if self._bridge:
            lanes = self._bridge.get_evidence_lanes()
            if lanes:
                lane_values += lanes
        self._lane_combo = ctk.CTkComboBox(
            panel, values=lane_values, command=lambda _: self._apply_filters()
        )
        self._lane_combo.set("All")
        self._lane_combo.pack(padx=8, fill="x", pady=(0, 4))

        # Filing filter (F1–F10)
        ctk.CTkLabel(panel, text="Filing", font=ctk.CTkFont(size=11)).pack(
            padx=8, anchor="w"
        )
        filing_values = ["All"] + [f"F{i}" for i in range(1, 11)]
        self._filing_combo = ctk.CTkComboBox(
            panel, values=filing_values, command=lambda _: self._apply_filters()
        )
        self._filing_combo.set("All")
        self._filing_combo.pack(padx=8, fill="x", pady=(0, 4))

        # Evidence type checkboxes (kept for legacy engine fallback)
        ctk.CTkLabel(panel, text="Evidence Type", font=ctk.CTkFont(size=11)).pack(
            padx=8, pady=(8, 0), anchor="w"
        )
        self._type_vars: dict[str, tk.BooleanVar] = {}
        for etype in VALID_EVIDENCE_TYPES:
            var = tk.BooleanVar(value=True)
            self._type_vars[etype] = var
            ctk.CTkCheckBox(
                panel, text=etype.replace("_", " ").title(), variable=var,
                font=ctk.CTkFont(size=11), height=22,
                command=self._apply_filters,
            ).pack(padx=12, anchor="w")

        # Case filter
        ctk.CTkLabel(panel, text="Case", font=ctk.CTkFont(size=11)).pack(padx=8, pady=(8, 2), anchor="w")
        self._case_combo = ctk.CTkComboBox(panel, values=["All"], command=lambda _: self._apply_filters())
        self._case_combo.set("All")
        self._case_combo.pack(padx=8, fill="x")

        # Show evidence count
        if self._bridge:
            count = self._bridge.get_evidence_count()
            if count:
                ctk.CTkLabel(
                    panel, text=f"📊 {count:,} evidence items",
                    font=ctk.CTkFont(size=10), text_color="#10B981",
                ).pack(padx=8, pady=(8, 4), anchor="w")

        self._refresh_case_combo()

    def _refresh_case_combo(self) -> None:
        try:
            rows = self.app.db.fetchall("SELECT id, title FROM cases ORDER BY title")
            values = ["All"] + [f"{dict(r)['id']}: {dict(r)['title']}" for r in rows]
            self._case_combo.configure(values=values)
        except Exception:
            pass

    # -- Results table --------------------------------------------------------

    def _build_results_table(self, parent: ctk.CTkFrame) -> None:
        table_frame = ctk.CTkFrame(parent)
        table_frame.grid(row=0, column=1, sticky="nsew", padx=4)
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(1, weight=1)

        # Header — adapt columns based on bridge availability
        hdr = ctk.CTkFrame(table_frame, fg_color="#1E293B", height=30)
        hdr.grid(row=0, column=0, sticky="ew")
        if self._bridge:
            cols = [("Bates #", 75), ("Source", 110), ("Quote", 150), ("Exhibit", 50),
                    ("Filing", 50), ("Strength", 55), ("Category", 70), ("Lane", 40)]
        else:
            cols = [("Bates #", 80), ("Description", 170), ("Exhibit", 50), ("Filing", 50),
                    ("Strength", 55), ("Type", 70), ("Case", 45), ("Date", 80)]
        for i, (text, w) in enumerate(cols):
            ctk.CTkLabel(hdr, text=text, font=ctk.CTkFont(size=11, weight="bold"), width=w, anchor="w").grid(
                row=0, column=i, padx=4, pady=4
            )

        self._table_scroll = ctk.CTkScrollableFrame(table_frame)
        self._table_scroll.grid(row=1, column=0, sticky="nsew")
        self._table_scroll.grid_columnconfigure(1, weight=1)

        # Action buttons
        btn_row = ctk.CTkFrame(table_frame, fg_color="transparent")
        btn_row.grid(row=2, column=0, sticky="ew", pady=4, padx=4)
        add_btn = ctk.CTkButton(btn_row, text="＋ Add Evidence", width=130, command=self._on_add)
        add_btn.pack(side="left", padx=(0, 6))
        Tooltip(add_btn, "Upload a new evidence document, photo, or recording")
        bates_btn = ctk.CTkButton(btn_row, text="Assign Bates", width=110, fg_color="#8B5CF6",
                       hover_color="#7C3AED", command=self._on_assign_bates)
        bates_btn.pack(side="left", padx=6)
        Tooltip(bates_btn, "Auto-assign Bates numbers (PIGORS-XXXX) to unnumbered evidence")
        auth_btn = ctk.CTkButton(btn_row, text="Authenticate", width=110, fg_color="#F59E0B",
                       hover_color="#D97706", command=self._on_authenticate)
        auth_btn.pack(side="left", padx=6)
        Tooltip(auth_btn, "Generate MRE 901 authentication declaration for selected evidence")
        export_btn = ctk.CTkButton(btn_row, text="Export Exhibit List", width=140, fg_color="#10B981",
                       hover_color="#059669", command=self._on_export_list)
        export_btn.pack(side="left", padx=6)
        Tooltip(export_btn, "Export formatted exhibit list for court submission")
        csv_btn = ctk.CTkButton(btn_row, text="📊 Export CSV", width=120, fg_color="#3B82F6",
                       hover_color="#2563EB", command=self._on_export_csv)
        csv_btn.pack(side="left", padx=6)
        Tooltip(csv_btn, "Export all visible evidence to CSV with all columns")
        bulk_bates_btn = ctk.CTkButton(btn_row, text="🔢 Bulk Bates", width=120,
                       fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                       command=self._on_bulk_bates)
        bulk_bates_btn.pack(side="left", padx=6)
        Tooltip(bulk_bates_btn, "Assign sequential Bates numbers to all visible evidence items")

    # -- Detail panel ---------------------------------------------------------

    def _build_detail_panel(self, parent: ctk.CTkFrame) -> None:
        panel = ctk.CTkFrame(parent, width=260)
        panel.grid(row=0, column=2, sticky="ns", padx=(4, 0))
        panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(panel, text="Detail", font=ctk.CTkFont(weight="bold")).pack(
            padx=8, pady=(8, 4), anchor="w"
        )

        self._detail_labels: dict[str, ctk.CTkLabel] = {}
        for field in ("Bates #", "Title", "File Path", "File Type", "Hash", "Source",
                       "Date Created", "Date Imported", "Authentication", "Tags"):
            ctk.CTkLabel(panel, text=field, font=ctk.CTkFont(size=11), text_color="#9CA3AF").pack(
                padx=8, anchor="w", pady=(4, 0)
            )
            lbl = ctk.CTkLabel(panel, text="—", font=ctk.CTkFont(size=12), anchor="w", wraplength=230)
            lbl.pack(padx=12, anchor="w")
            self._detail_labels[field] = lbl

        # Quick Preview
        ctk.CTkLabel(panel, text="Quick Preview", font=ctk.CTkFont(weight="bold")).pack(
            padx=8, pady=(12, 4), anchor="w"
        )
        self._preview_text = ctk.CTkTextbox(
            panel, font=ctk.CTkFont(family="Consolas", size=11),
            height=160, fg_color=COLORS["bg_dark"], text_color=COLORS["text"],
        )
        self._preview_text.pack(padx=8, fill="both", expand=True, pady=(0, 8))
        self._preview_text.insert("1.0", "Select an evidence item to preview…")
        self._preview_text.configure(state="disabled")

    # -- Data -----------------------------------------------------------------

    def refresh(self) -> None:
        """Reload evidence list from bridge or DB."""
        if self._bridge:
            lane = self._lane_combo.get() if hasattr(self, '_lane_combo') else None
            cat = self._category_combo.get() if hasattr(self, '_category_combo') else None
            self._evidence = self._bridge.search_evidence(lane=lane, category=cat)
            self._populate_bridge_table(self._evidence)
        elif self.engine:
            self._evidence = self.engine.get_evidence()
            self._refresh_case_combo()
            self._apply_filters()

    def _do_search(self) -> None:
        query = self._search_entry.get().strip()
        if not query:
            self.refresh()
            return
        if self._bridge:
            lane = self._lane_combo.get() if hasattr(self, '_lane_combo') else None
            cat = self._category_combo.get() if hasattr(self, '_category_combo') else None
            self._evidence = self._bridge.search_evidence(query, lane=lane, category=cat)
            self._populate_bridge_table(self._evidence)
            return
        # Fallback to EvidenceEngine
        if self.engine:
            case_id = self._get_case_filter()
            try:
                self._evidence = self.engine.search_evidence(query, case_id=case_id)
            except Exception:
                self._evidence = []
            self._populate_table(self._evidence)

    def _clear_search(self) -> None:
        self._search_entry.delete(0, "end")
        self.refresh()

    def _get_case_filter(self) -> Optional[int]:
        val = self._case_combo.get()
        if val == "All":
            return None
        try:
            return int(val.split(":")[0])
        except (ValueError, IndexError):
            return None

    def _apply_filters(self) -> None:
        filing_filter = self._filing_combo.get() if hasattr(self, '_filing_combo') else "All"
        if self._bridge:
            # Re-query bridge with selected filters
            lane = self._lane_combo.get() if hasattr(self, '_lane_combo') else None
            cat = self._category_combo.get() if hasattr(self, '_category_combo') else None
            query = self._search_entry.get().strip() if hasattr(self, '_search_entry') else ""
            self._evidence = self._bridge.search_evidence(query, lane=lane, category=cat)
            if filing_filter != "All":
                self._evidence = [
                    e for e in self._evidence
                    if filing_filter in str(self._filing_map.get(
                        e.get("id") or e.get("rowid"), ""))
                ]
            self._populate_bridge_table(self._evidence)
            return
        # Legacy: filter in-memory evidence list
        active_types = {t for t, v in self._type_vars.items() if v.get()}
        case_id = self._get_case_filter()
        filtered = self._evidence
        if case_id is not None:
            filtered = [e for e in filtered if e.get("case_id") == case_id]
        filtered = [e for e in filtered if e.get("file_type", "document") in active_types]
        if filing_filter != "All":
            filtered = [
                e for e in filtered
                if filing_filter in str(self._filing_map.get(
                    e.get("id") or e.get("evidence_id"), ""))
            ]
        self._populate_table(filtered)

    def _populate_table(self, items: list[dict]) -> None:
        for w in self._table_scroll.winfo_children():
            w.destroy()

        if not items:
            ctk.CTkLabel(self._table_scroll, text="No evidence found.", text_color="#6B7280").grid(
                row=0, column=0, columnspan=8, pady=20
            )
            return

        for idx, ev in enumerate(items):
            row_frame = ctk.CTkFrame(
                self._table_scroll, fg_color="#1F2937" if idx % 2 == 0 else "transparent",
                cursor="hand2",
            )
            row_frame.grid(row=idx, column=0, sticky="ew", pady=1)
            row_frame.grid_columnconfigure(1, weight=1)

            ev_id = ev.get("id") or ev.get("evidence_id") or idx
            bates = self._bates_map.get(ev_id) or ev.get("bates_number") or "—"
            exhibit = self._exhibit_map.get(ev_id) or f"Ex. {idx + 1}"
            filing = self._filing_map.get(ev_id) or "—"
            score = ev.get("relevance_score")
            strength = self._strength_indicator(score)
            vals = [
                (bates, 80),
                ((ev.get("description") or ev.get("title", ""))[:45], 170),
                (exhibit, 50),
                (filing, 50),
                (strength, 55),
                (ev.get("file_type") or "—", 70),
                (str(ev.get("case_id", "")), 45),
                ((ev.get("date_created") or "")[:10], 80),
            ]
            for ci, (text, w) in enumerate(vals):
                lbl = ctk.CTkLabel(row_frame, text=text, width=w, anchor="w", font=ctk.CTkFont(size=12))
                lbl.grid(row=0, column=ci, padx=4, pady=3)
                lbl.bind("<Button-1>", lambda e, item=ev: self._on_select(item))
            row_frame.bind("<Button-1>", lambda e, item=ev: self._on_select(item))

            ContextMenu(row_frame, items=[
                ("📋 Copy Citation", lambda item=ev: self._ctx_copy_citation(item)),
                ("📄 View Full Text", lambda item=ev: self._ctx_view_full_text(item)),
                ("📎 Link to Filing", lambda item=ev: self._ctx_link_to_filing(item)),
                ("🔢 Assign Bates", lambda item=ev: self._ctx_assign_bates_single(item)),
                ("⭐ Mark as Key Evidence", lambda item=ev: self._ctx_mark_key_evidence(item)),
                ("---", None),
                ("Copy Description", lambda item=ev: self._ctx_copy_text(
                    item.get("description") or item.get("title", ""))),
                ("View Source File", lambda item=ev: self._ctx_view_source(item)),
                ("---", None),
                ("Change Category", lambda item=ev: self._ctx_change_category(item)),
                ("Change Lane", lambda item=ev: self._ctx_change_lane(item)),
            ])

    def _populate_bridge_table(self, items: list[dict]) -> None:
        """Populate the results table with evidence_quotes data from bridge."""
        for w in self._table_scroll.winfo_children():
            w.destroy()

        if not items:
            ctk.CTkLabel(self._table_scroll, text="No evidence found.", text_color="#6B7280").grid(
                row=0, column=0, columnspan=8, pady=20
            )
            return

        for idx, ev in enumerate(items):
            row_frame = ctk.CTkFrame(
                self._table_scroll, fg_color="#1F2937" if idx % 2 == 0 else "transparent",
                cursor="hand2",
            )
            row_frame.grid(row=idx, column=0, sticky="ew", pady=1)
            row_frame.grid_columnconfigure(2, weight=1)

            ev_id = ev.get("id") or ev.get("rowid") or idx
            bates = self._bates_map.get(ev_id) or "—"
            source = Path(ev.get("source_file", "")).name if ev.get("source_file") else "—"
            quote = (ev.get("quote_text") or "")[:55]
            exhibit = self._exhibit_map.get(ev_id) or f"Ex. {idx + 1}"
            filing = self._filing_map.get(ev_id) or "—"
            category = ev.get("category") or "—"
            lane = ev.get("lane") or "—"
            score = ev.get("relevance_score")
            strength = self._strength_indicator(score)

            vals = [
                (bates, 75),
                (source[:25], 110),
                (quote, 150),
                (exhibit, 50),
                (filing, 50),
                (strength, 55),
                (category, 70),
                (lane, 40),
            ]
            for ci, (text, w) in enumerate(vals):
                lbl = ctk.CTkLabel(row_frame, text=text, width=w, anchor="w", font=ctk.CTkFont(size=12))
                lbl.grid(row=0, column=ci, padx=4, pady=3)
                lbl.bind("<Button-1>", lambda e, item=ev: self._on_select(item))
            row_frame.bind("<Button-1>", lambda e, item=ev: self._on_select(item))

            ContextMenu(row_frame, items=[
                ("📋 Copy Citation", lambda item=ev: self._ctx_copy_citation(item)),
                ("📄 View Full Text", lambda item=ev: self._ctx_view_full_text(item)),
                ("📎 Link to Filing", lambda item=ev: self._ctx_link_to_filing(item)),
                ("🔢 Assign Bates", lambda item=ev: self._ctx_assign_bates_single(item)),
                ("⭐ Mark as Key Evidence", lambda item=ev: self._ctx_mark_key_evidence(item)),
                ("---", None),
                ("Copy Quote Text", lambda item=ev: self._ctx_copy_text(
                    item.get("quote_text", ""))),
                ("View Source File", lambda item=ev: self._ctx_view_source(item)),
                ("---", None),
                ("Change Category", lambda item=ev: self._ctx_change_category(item)),
                ("Change Lane", lambda item=ev: self._ctx_change_lane(item)),
            ])

    def _on_select(self, ev: dict) -> None:
        self._selected = ev
        # Bridge evidence_quotes have different fields than app-schema evidence
        if "quote_text" in ev:
            mapping = {
                "Bates #": str(ev.get("id", "—")),
                "Title": (ev.get("quote_text") or "—")[:200],
                "File Path": ev.get("source_file") or "—",
                "File Type": ev.get("category") or "—",
                "Hash": "—",
                "Source": ev.get("source_file") or "—",
                "Date Created": ev.get("created_at") or "—",
                "Date Imported": "—",
                "Authentication": f"Lane: {ev.get('lane', '—')} | Score: {ev.get('relevance_score', '—')}",
                "Tags": ev.get("tags") or ev.get("filing_refs") or "—",
            }
        else:
            mapping = {
                "Bates #": ev.get("bates_number") or "—",
                "Title": ev.get("title") or "—",
                "File Path": ev.get("file_path") or "—",
                "File Type": ev.get("file_type") or "—",
                "Hash": (ev.get("notes") or "—")[:64],
                "Source": ev.get("source") or "—",
                "Date Created": ev.get("date_created") or "—",
                "Date Imported": ev.get("date_imported") or "—",
                "Authentication": ev.get("authentication_method") or "Not authenticated",
                "Tags": ev.get("tags") or "—",
            }
        for field, value in mapping.items():
            self._detail_labels[field].configure(text=str(value))

        # Update quick preview
        preview = ev.get("quote_text") or ev.get("description") or ev.get("title") or "No preview available."
        preview = str(preview)[:500]
        if hasattr(self, '_preview_text'):
            self._preview_text.configure(state="normal")
            self._preview_text.delete("1.0", "end")
            self._preview_text.insert("1.0", preview)
            self._preview_text.configure(state="disabled")

    # -- Actions --------------------------------------------------------------

    def _ctx_copy_text(self, text: str) -> None:
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
        except Exception:
            pass

    def _ctx_view_source(self, ev: dict) -> None:
        path = ev.get("source_file") or ev.get("file_path")
        if path:
            import os
            os.startfile(Path(path).parent if Path(path).is_file() else path)

    def _ctx_change_category(self, ev: dict) -> None:
        from tkinter import simpledialog
        new_cat = simpledialog.askstring("Change Category", "New category:", parent=self)
        if new_cat and self._bridge and ev.get("id"):
            try:
                conn = self._bridge._conn
                conn.execute("UPDATE evidence_quotes SET category=? WHERE rowid=?", (new_cat, ev["id"]))
                conn.commit()
            except Exception:
                pass
            self.refresh()

    def _ctx_change_lane(self, ev: dict) -> None:
        from tkinter import simpledialog
        new_lane = simpledialog.askstring("Change Lane", "New lane (A-F):", parent=self)
        if new_lane and self._bridge and ev.get("id"):
            try:
                conn = self._bridge._conn
                conn.execute("UPDATE evidence_quotes SET lane=? WHERE rowid=?", (new_lane.upper(), ev["id"]))
                conn.commit()
            except Exception:
                pass
            self.refresh()

            self.refresh()

    # -- Enrichment & helpers -------------------------------------------------

    @staticmethod
    def _strength_indicator(score) -> str:
        """Return colored emoji indicator for evidence strength."""
        if score is None:
            return "—"
        try:
            s = float(score)
        except (TypeError, ValueError):
            return "—"
        if s >= 0.7:
            return f"🟢 {s:.1f}"
        elif s >= 0.4:
            return f"🟡 {s:.1f}"
        else:
            return f"🔴 {s:.1f}"

    def _get_litigation_db_path(self) -> Optional[str]:
        """Resolve litigation_context.db path."""
        candidates = [
            Path(r"C:\Users\andre\LitigationOS\litigation_context.db"),
            Path(r"C:\Users\andre\LitigationOS\databases\litigation_context.db"),
        ]
        if self._bridge:
            bp = getattr(self._bridge, '_db_path', None) or getattr(self._bridge, 'db_path', None)
            if bp:
                candidates.insert(0, Path(str(bp)))
        for p in candidates:
            if p.exists():
                return str(p)
        return None

    def _load_enrichment_data(self) -> None:
        """Background: load Bates assignments, exhibit labels, filing links."""
        db_path = self._get_litigation_db_path()
        if not db_path:
            return
        try:
            conn = sqlite3.connect(db_path, timeout=60)
            conn.execute("PRAGMA busy_timeout=60000")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA cache_size=-32000")

            tables = {r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()}

            # Bates assignments
            if "bates_assignments" in tables:
                cols = [r[1] for r in conn.execute(
                    "PRAGMA table_info(bates_assignments)").fetchall()]
                id_col = "evidence_id" if "evidence_id" in cols else "id"
                bates_col = next(
                    (c for c in ("bates_number", "bates_stamp") if c in cols), None)
                if bates_col:
                    for row in conn.execute(
                        f"SELECT {id_col}, {bates_col} FROM bates_assignments"
                    ).fetchall():
                        if row[0] is not None and row[1]:
                            self._bates_map[row[0]] = str(row[1])

            # Exhibit assignments
            if "exhibit_assignments" in tables:
                cols = [r[1] for r in conn.execute(
                    "PRAGMA table_info(exhibit_assignments)").fetchall()]
                id_col = "evidence_id" if "evidence_id" in cols else "id"
                label_col = next(
                    (c for c in ("exhibit_label", "label", "exhibit_number")
                     if c in cols), None)
                if label_col:
                    for row in conn.execute(
                        f"SELECT {id_col}, {label_col} FROM exhibit_assignments"
                    ).fetchall():
                        if row[0] is not None and row[1]:
                            self._exhibit_map[row[0]] = str(row[1])

            # Filing links
            if "evidence_filing_map" in tables:
                cols = [r[1] for r in conn.execute(
                    "PRAGMA table_info(evidence_filing_map)").fetchall()]
                id_col = "evidence_id" if "evidence_id" in cols else "id"
                filing_col = next(
                    (c for c in ("filing_id", "vehicle_name", "filing")
                     if c in cols), None)
                if filing_col:
                    filing_groups: dict[int, list[str]] = {}
                    for row in conn.execute(
                        f"SELECT {id_col}, {filing_col} FROM evidence_filing_map"
                    ).fetchall():
                        if row[0] is not None and row[1]:
                            filing_groups.setdefault(row[0], []).append(str(row[1]))
                    for eid, filings in filing_groups.items():
                        self._filing_map[eid] = ", ".join(filings[:3])
            elif "claims" in tables:
                cols = [r[1] for r in conn.execute(
                    "PRAGMA table_info(claims)").fetchall()]
                if "vehicle_name" in cols:
                    id_col = "claim_id" if "claim_id" in cols else "id"
                    for row in conn.execute(
                        f"SELECT {id_col}, vehicle_name FROM claims "
                        "WHERE vehicle_name IS NOT NULL LIMIT 5000"
                    ).fetchall():
                        if row[0] is not None and row[1]:
                            self._filing_map[row[0]] = str(row[1])

            conn.close()
        except Exception as exc:
            logger.warning("Failed to load enrichment data: %s", exc)

    # -- New actions ----------------------------------------------------------

    def _on_export_csv(self) -> None:
        """Export visible evidence to CSV with all columns."""
        if not self._evidence:
            messagebox.showinfo("Export CSV", "No evidence to export.")
            return
        path = filedialog.asksaveasfilename(
            title="Export Evidence CSV",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            initialfile="evidence_export.csv",
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Bates #", "Source", "Description/Quote", "Exhibit",
                    "Filing", "Strength", "Category/Type", "Lane", "Date",
                ])
                for idx, ev in enumerate(self._evidence):
                    ev_id = ev.get("id") or ev.get("evidence_id") or idx
                    bates = self._bates_map.get(ev_id) or ev.get("bates_number") or ""
                    source = ev.get("source_file") or ev.get("source") or ""
                    text = ev.get("quote_text") or ev.get("description") or ev.get("title") or ""
                    exhibit = self._exhibit_map.get(ev_id) or f"Ex. {idx + 1}"
                    filing = self._filing_map.get(ev_id) or ""
                    score = ev.get("relevance_score")
                    strength = f"{float(score):.2f}" if score is not None else ""
                    cat = ev.get("category") or ev.get("file_type") or ""
                    lane = ev.get("lane") or ""
                    date = ev.get("date_created") or ev.get("created_at") or ""
                    writer.writerow([bates, source, text, exhibit, filing,
                                     strength, cat, lane, date])
            messagebox.showinfo(
                "Export CSV", f"Exported {len(self._evidence)} items to:\n{path}")
        except Exception as exc:
            messagebox.showerror("Export CSV", str(exc))

    def _on_bulk_bates(self) -> None:
        """Assign sequential Bates numbers to all visible evidence items."""
        if not self._evidence:
            messagebox.showinfo("Bulk Bates", "No evidence items to assign.")
            return
        from tkinter import simpledialog
        prefix = simpledialog.askstring(
            "Bulk Bates Assign", "Bates prefix (e.g., PIGORS):",
            initialvalue="PIGORS", parent=self,
        )
        if not prefix:
            return
        start_num = simpledialog.askinteger(
            "Bulk Bates Assign", "Starting number:",
            initialvalue=1, minvalue=1, parent=self,
        )
        if start_num is None:
            return

        db_path = self._get_litigation_db_path()
        assigned = 0
        try:
            if db_path:
                conn = sqlite3.connect(db_path, timeout=60)
                conn.execute("PRAGMA busy_timeout=60000")
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA cache_size=-32000")
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS bates_assignments (
                        evidence_id INTEGER PRIMARY KEY,
                        bates_number TEXT NOT NULL,
                        assigned_at TEXT DEFAULT (datetime('now'))
                    )
                """)
                for idx, ev in enumerate(self._evidence):
                    ev_id = ev.get("id") or ev.get("evidence_id") or ev.get("rowid")
                    if ev_id is None:
                        continue
                    bates_num = f"{prefix}-{start_num + idx:04d}"
                    conn.execute(
                        "INSERT OR REPLACE INTO bates_assignments "
                        "(evidence_id, bates_number) VALUES (?, ?)",
                        (ev_id, bates_num),
                    )
                    self._bates_map[ev_id] = bates_num
                    assigned += 1
                conn.commit()
                conn.close()
            else:
                for idx, ev in enumerate(self._evidence):
                    ev_id = ev.get("id") or ev.get("evidence_id") or idx
                    bates_num = f"{prefix}-{start_num + idx:04d}"
                    self._bates_map[ev_id] = bates_num
                    assigned += 1

            end_num = start_num + assigned - 1
            messagebox.showinfo(
                "Bulk Bates",
                f"Assigned {assigned} Bates numbers "
                f"({prefix}-{start_num:04d} through {prefix}-{end_num:04d}).",
            )
            self.refresh()
        except Exception as exc:
            messagebox.showerror("Bulk Bates", str(exc))

    def _ctx_copy_citation(self, ev: dict) -> None:
        """Copy formatted citation to clipboard."""
        ev_id = ev.get("id") or ev.get("evidence_id") or 0
        bates = self._bates_map.get(ev_id) or ev.get("bates_number") or "UNASSIGNED"
        exhibit = self._exhibit_map.get(ev_id) or "Ex. ?"
        source = ev.get("source_file") or ev.get("source") or "Unknown source"
        name = Path(source).name if source != "Unknown source" else source
        citation = f"{exhibit} ({bates}) — {name}"
        try:
            self.clipboard_clear()
            self.clipboard_append(citation)
        except Exception:
            pass

    def _ctx_link_to_filing(self, ev: dict) -> None:
        """Link evidence to a filing (F1-F10)."""
        from tkinter import simpledialog
        filing = simpledialog.askstring(
            "Link to Filing", "Filing ID (e.g., F1, F2, … F10):", parent=self,
        )
        if not filing:
            return
        ev_id = ev.get("id") or ev.get("evidence_id") or ev.get("rowid")
        if ev_id is None:
            return
        db_path = self._get_litigation_db_path()
        if db_path:
            try:
                conn = sqlite3.connect(db_path, timeout=60)
                conn.execute("PRAGMA busy_timeout=60000")
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS evidence_filing_map (
                        evidence_id INTEGER,
                        filing_id TEXT,
                        linked_at TEXT DEFAULT (datetime('now')),
                        PRIMARY KEY (evidence_id, filing_id)
                    )
                """)
                conn.execute(
                    "INSERT OR IGNORE INTO evidence_filing_map "
                    "(evidence_id, filing_id) VALUES (?, ?)",
                    (ev_id, filing.upper()),
                )
                conn.commit()
                conn.close()
            except Exception:
                pass
        self._filing_map[ev_id] = filing.upper()
        self.refresh()

    def _ctx_view_full_text(self, ev: dict) -> None:
        """Show full evidence text in a dialog."""
        text = (ev.get("quote_text") or ev.get("description")
                or ev.get("title") or "No text available.")
        _TextViewDialog(self, "Full Evidence Text", str(text))

    def _ctx_assign_bates_single(self, ev: dict) -> None:
        """Assign a Bates number to a single evidence item."""
        from tkinter import simpledialog
        current = self._bates_map.get(ev.get("id")) or ev.get("bates_number") or ""
        bates = simpledialog.askstring(
            "Assign Bates", "Bates number:", initialvalue=current, parent=self,
        )
        if not bates:
            return
        ev_id = ev.get("id") or ev.get("evidence_id") or ev.get("rowid")
        if ev_id is None:
            return
        db_path = self._get_litigation_db_path()
        if db_path:
            try:
                conn = sqlite3.connect(db_path, timeout=60)
                conn.execute("PRAGMA busy_timeout=60000")
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS bates_assignments (
                        evidence_id INTEGER PRIMARY KEY,
                        bates_number TEXT NOT NULL,
                        assigned_at TEXT DEFAULT (datetime('now'))
                    )
                """)
                conn.execute(
                    "INSERT OR REPLACE INTO bates_assignments "
                    "(evidence_id, bates_number) VALUES (?, ?)",
                    (ev_id, bates),
                )
                conn.commit()
                conn.close()
            except Exception:
                pass
        self._bates_map[ev_id] = bates
        self.refresh()

    def _ctx_mark_key_evidence(self, ev: dict) -> None:
        """Mark evidence item as key evidence."""
        ev_id = ev.get("id") or ev.get("evidence_id") or ev.get("rowid")
        if ev_id is None:
            return
        db_path = self._get_litigation_db_path()
        if db_path:
            try:
                conn = sqlite3.connect(db_path, timeout=60)
                conn.execute("PRAGMA busy_timeout=60000")
                conn.execute("PRAGMA journal_mode=WAL")
                tables = {r[0] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()}
                if "evidence_quotes" in tables:
                    cols = [r[1] for r in conn.execute(
                        "PRAGMA table_info(evidence_quotes)").fetchall()]
                    if "tags" in cols:
                        row = conn.execute(
                            "SELECT tags FROM evidence_quotes WHERE rowid=?",
                            (ev_id,),
                        ).fetchone()
                        new_tags = "KEY_EVIDENCE"
                        if row and row[0]:
                            if "KEY_EVIDENCE" in row[0]:
                                conn.close()
                                messagebox.showinfo(
                                    "Key Evidence", "Already marked as key evidence.")
                                return
                            new_tags = f"{row[0]}, KEY_EVIDENCE"
                        conn.execute(
                            "UPDATE evidence_quotes SET tags=? WHERE rowid=?",
                            (new_tags, ev_id),
                        )
                        conn.commit()
                conn.close()
                messagebox.showinfo(
                    "Key Evidence", f"Marked evidence #{ev_id} as KEY EVIDENCE.")
            except Exception as exc:
                messagebox.showerror("Key Evidence", str(exc))
        self.refresh()

    def _on_add(self) -> None:
        if not self.engine:
            messagebox.showinfo("Add Evidence", "Evidence engine not available — use the bridge.")
            return
        _AddEvidenceDialog(self, self.app, self.engine, on_done=self.refresh)

    def _on_assign_bates(self) -> None:
        if not self.engine:
            messagebox.showinfo("Assign Bates", "Evidence engine not available.")
            return
        case_id = self._get_case_filter()
        if case_id is None:
            messagebox.showinfo("Assign Bates", "Select a case filter to assign Bates numbers.")
            return
        try:
            assignments = self.engine.assign_bates(case_id)
            messagebox.showinfo(
                "Assign Bates",
                f"Assigned {len(assignments)} Bates number(s)." if assignments else "No un-numbered evidence found.",
            )
            self.refresh()
        except Exception as exc:
            messagebox.showerror("Assign Bates", str(exc))

    def _on_authenticate(self) -> None:
        if not self._selected:
            messagebox.showinfo("Authenticate", "Select an evidence item first.")
            return
        if not self.engine:
            messagebox.showinfo("Authenticate", "Evidence engine not available.")
            return
        try:
            declaration = self.engine.authenticate(self._selected["id"])
            _TextViewDialog(self, "MRE 901 Declaration", declaration)
            self.refresh()
        except Exception as exc:
            messagebox.showerror("Authenticate", str(exc))

    def _on_export_list(self) -> None:
        if not self.engine:
            messagebox.showinfo("Export", "Evidence engine not available.")
            return
        case_id = self._get_case_filter()
        if case_id is None:
            messagebox.showinfo("Export", "Select a case filter to generate an exhibit list.")
            return
        try:
            exhibit_text = self.engine.get_exhibit_list(case_id)
            _TextViewDialog(self, "Exhibit List", exhibit_text)
        except Exception as exc:
            messagebox.showerror("Export", str(exc))


# -- Dialogs -----------------------------------------------------------------


class _AddEvidenceDialog(ctk.CTkToplevel):
    """Dialog for adding a new evidence item."""

    def __init__(self, parent, app: "App", engine: EvidenceEngine, *, on_done):
        super().__init__(parent)
        self.title("Add Evidence")
        self.geometry("460x420")
        self.resizable(False, False)
        self.grab_set()
        self._engine = engine
        self._app = app
        self._on_done = on_done
        self._file_path = ""

        pad = dict(padx=16, pady=3, sticky="ew")
        r = 0

        ctk.CTkLabel(self, text="File").grid(row=r, column=0, **pad); r += 1
        file_row = ctk.CTkFrame(self, fg_color="transparent")
        file_row.grid(row=r, column=0, **pad); r += 1
        file_row.grid_columnconfigure(0, weight=1)
        self._lbl_file = ctk.CTkLabel(file_row, text="No file selected", anchor="w")
        self._lbl_file.grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(file_row, text="Browse…", width=80, command=self._pick_file).grid(row=0, column=1)

        ctk.CTkLabel(self, text="Case ID").grid(row=r, column=0, **pad); r += 1
        self._entry_case = ctk.CTkEntry(self, placeholder_text="Numeric case ID")
        self._entry_case.grid(row=r, column=0, **pad); r += 1

        ctk.CTkLabel(self, text="Evidence Type").grid(row=r, column=0, **pad); r += 1
        self._combo_type = ctk.CTkComboBox(self, values=list(VALID_EVIDENCE_TYPES))
        self._combo_type.grid(row=r, column=0, **pad); r += 1

        ctk.CTkLabel(self, text="Description").grid(row=r, column=0, **pad); r += 1
        self._entry_desc = ctk.CTkEntry(self, placeholder_text="Describe the evidence")
        self._entry_desc.grid(row=r, column=0, **pad); r += 1

        ctk.CTkLabel(self, text="Source").grid(row=r, column=0, **pad); r += 1
        self._entry_source = ctk.CTkEntry(self, placeholder_text="Where it came from")
        self._entry_source.grid(row=r, column=0, **pad); r += 1

        ctk.CTkButton(self, text="Add", command=self._add).grid(row=r, column=0, **pad)
        self.grid_columnconfigure(0, weight=1)

    def _pick_file(self) -> None:
        path = filedialog.askopenfilename(title="Select evidence file")
        if path:
            self._file_path = path
            self._lbl_file.configure(text=Path(path).name)

    def _add(self) -> None:
        if not self._file_path:
            messagebox.showwarning("Add Evidence", "Select a file.")
            return
        case_raw = self._entry_case.get().strip()
        desc = self._entry_desc.get().strip()
        if not case_raw or not desc:
            messagebox.showwarning("Add Evidence", "Case ID and description are required.")
            return
        try:
            case_id = int(case_raw)
        except ValueError:
            messagebox.showwarning("Add Evidence", "Case ID must be a number.")
            return
        try:
            self._engine.add_evidence(
                case_id, self._file_path, self._combo_type.get(), desc,
                source=self._entry_source.get().strip() or None,
            )
            self.destroy()
            self._on_done()
        except Exception as exc:
            messagebox.showerror("Add Evidence", str(exc))


class _TextViewDialog(ctk.CTkToplevel):
    """Read-only text viewer dialog."""

    def __init__(self, parent, title: str, text: str):
        super().__init__(parent)
        self.title(title)
        self.geometry("640x480")
        self.grab_set()
        tb = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=12))
        tb.pack(fill="both", expand=True, padx=8, pady=8)
        tb.insert("1.0", text)
        tb.configure(state="disabled")
        ctk.CTkButton(self, text="Close", command=self.destroy).pack(pady=(0, 8))
