"""Evidence browser screen — search, browse, tag, and authenticate.

Provides FTS5 search, a results table, filter panel, detail view with
authentication status, Bates assignment, and exhibit list export.
Uses the real litigation_context.db via LitigationBridge when available,
falling back to the app-schema EvidenceEngine otherwise.
"""

from __future__ import annotations

import logging
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import TYPE_CHECKING, Optional

import customtkinter as ctk

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
        self.engine = EvidenceEngine(app.db)
        self._evidence: list[dict] = []
        self._selected: Optional[dict] = None

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

        self._build_ui()
        self.refresh()

    # -- Layout ---------------------------------------------------------------

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ── Title ──
        ctk.CTkLabel(self, text="Evidence Browser", font=ctk.CTkFont(size=20, weight="bold")).grid(
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
        ctk.CTkButton(search_frame, text="Search", width=80, command=self._do_search).grid(
            row=0, column=2, padx=(8, 0)
        )
        ctk.CTkButton(search_frame, text="Clear", width=60, fg_color="#6B7280",
                       command=self._clear_search).grid(row=0, column=3, padx=(4, 0))

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
            cols = [("Source", 150), ("Quote", 220), ("Category", 80), ("Lane", 40), ("Score", 50)]
        else:
            cols = [("Bates #", 100), ("Description", 260), ("Type", 90), ("Case", 50), ("Date", 90)]
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
        ctk.CTkButton(btn_row, text="＋ Add Evidence", width=130, command=self._on_add).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btn_row, text="Assign Bates", width=110, fg_color="#8B5CF6",
                       hover_color="#7C3AED", command=self._on_assign_bates).pack(side="left", padx=6)
        ctk.CTkButton(btn_row, text="Authenticate", width=110, fg_color="#F59E0B",
                       hover_color="#D97706", command=self._on_authenticate).pack(side="left", padx=6)
        ctk.CTkButton(btn_row, text="Export Exhibit List", width=140, fg_color="#10B981",
                       hover_color="#059669", command=self._on_export_list).pack(side="left", padx=6)

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

    # -- Data -----------------------------------------------------------------

    def refresh(self) -> None:
        """Reload evidence list from bridge or DB."""
        if self._bridge:
            lane = self._lane_combo.get() if hasattr(self, '_lane_combo') else None
            cat = self._category_combo.get() if hasattr(self, '_category_combo') else None
            self._evidence = self._bridge.search_evidence(lane=lane, category=cat)
            self._populate_bridge_table(self._evidence)
        else:
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
        if self._bridge:
            # Re-query bridge with selected filters
            lane = self._lane_combo.get() if hasattr(self, '_lane_combo') else None
            cat = self._category_combo.get() if hasattr(self, '_category_combo') else None
            query = self._search_entry.get().strip() if hasattr(self, '_search_entry') else ""
            self._evidence = self._bridge.search_evidence(query, lane=lane, category=cat)
            self._populate_bridge_table(self._evidence)
            return
        # Legacy: filter in-memory evidence list
        active_types = {t for t, v in self._type_vars.items() if v.get()}
        case_id = self._get_case_filter()
        filtered = self._evidence
        if case_id is not None:
            filtered = [e for e in filtered if e.get("case_id") == case_id]
        filtered = [e for e in filtered if e.get("file_type", "document") in active_types]
        self._populate_table(filtered)

    def _populate_table(self, items: list[dict]) -> None:
        for w in self._table_scroll.winfo_children():
            w.destroy()

        if not items:
            ctk.CTkLabel(self._table_scroll, text="No evidence found.", text_color="#6B7280").grid(
                row=0, column=0, columnspan=5, pady=20
            )
            return

        for idx, ev in enumerate(items):
            row_frame = ctk.CTkFrame(
                self._table_scroll, fg_color="#1F2937" if idx % 2 == 0 else "transparent",
                cursor="hand2",
            )
            row_frame.grid(row=idx, column=0, sticky="ew", pady=1)
            row_frame.grid_columnconfigure(1, weight=1)

            vals = [
                (ev.get("bates_number") or "—", 100),
                ((ev.get("description") or ev.get("title", ""))[:60], 260),
                (ev.get("file_type") or "—", 90),
                (str(ev.get("case_id", "")), 50),
                ((ev.get("date_created") or "")[:10], 90),
            ]
            for ci, (text, w) in enumerate(vals):
                lbl = ctk.CTkLabel(row_frame, text=text, width=w, anchor="w", font=ctk.CTkFont(size=12))
                lbl.grid(row=0, column=ci, padx=4, pady=3)
                lbl.bind("<Button-1>", lambda e, item=ev: self._on_select(item))
            row_frame.bind("<Button-1>", lambda e, item=ev: self._on_select(item))

    def _populate_bridge_table(self, items: list[dict]) -> None:
        """Populate the results table with evidence_quotes data from bridge."""
        for w in self._table_scroll.winfo_children():
            w.destroy()

        if not items:
            ctk.CTkLabel(self._table_scroll, text="No evidence found.", text_color="#6B7280").grid(
                row=0, column=0, columnspan=5, pady=20
            )
            return

        for idx, ev in enumerate(items):
            row_frame = ctk.CTkFrame(
                self._table_scroll, fg_color="#1F2937" if idx % 2 == 0 else "transparent",
                cursor="hand2",
            )
            row_frame.grid(row=idx, column=0, sticky="ew", pady=1)
            row_frame.grid_columnconfigure(1, weight=1)

            source = Path(ev.get("source_file", "")).name if ev.get("source_file") else "—"
            quote = (ev.get("quote_text") or "")[:80]
            category = ev.get("category") or "—"
            lane = ev.get("lane") or "—"
            score = ev.get("relevance_score")
            score_str = f"{score:.1f}" if score is not None else "—"

            vals = [
                (source[:30], 150),
                (quote, 220),
                (category, 80),
                (lane, 40),
                (score_str, 50),
            ]
            for ci, (text, w) in enumerate(vals):
                lbl = ctk.CTkLabel(row_frame, text=text, width=w, anchor="w", font=ctk.CTkFont(size=12))
                lbl.grid(row=0, column=ci, padx=4, pady=3)
                lbl.bind("<Button-1>", lambda e, item=ev: self._on_select(item))
            row_frame.bind("<Button-1>", lambda e, item=ev: self._on_select(item))

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

    # -- Actions --------------------------------------------------------------

    def _on_add(self) -> None:
        _AddEvidenceDialog(self, self.app, self.engine, on_done=self.refresh)

    def _on_assign_bates(self) -> None:
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
        try:
            declaration = self.engine.authenticate(self._selected["id"])
            _TextViewDialog(self, "MRE 901 Declaration", declaration)
            self.refresh()
        except Exception as exc:
            messagebox.showerror("Authenticate", str(exc))

    def _on_export_list(self) -> None:
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
