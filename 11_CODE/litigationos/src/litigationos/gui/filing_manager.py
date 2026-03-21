"""Filing manager screen — build, validate, export court-ready packages.

Provides a split-pane interface with a filterable filing list on the left,
filing detail / checklist on the right, and build → validate → export workflow.
Uses LitigationBridge to discover real filing packages on disk when available.
"""

from __future__ import annotations

import logging
import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import TYPE_CHECKING, Optional

import customtkinter as ctk

from litigationos.gui.widgets import ContextMenu, Tooltip

if TYPE_CHECKING:
    from litigationos.app import App

from litigationos.engines.filing import (
    VALID_FILING_TYPES,
    VALID_STATUSES,
    FilingEngine,
    FilingStack,
    ValidationResult,
)

try:
    from litigationos.db.litigation_bridge import LitigationBridge
    _HAS_BRIDGE = True
except ImportError:
    _HAS_BRIDGE = False

logger = logging.getLogger(__name__)

# Status workflow display order
_STATUS_LABELS = ("draft", "review", "ready", "filed", "served")
_STATUS_COLORS = {
    "draft": "#6B7280",
    "review": "#F59E0B",
    "ready": "#3B82F6",
    "filed": "#10B981",
    "served": "#8B5CF6",
    "incomplete": "#EF4444",
}


class FilingManagerFrame(ctk.CTkFrame):
    """Filing management — build, validate, export court-ready packages."""

    def __init__(self, parent: ctk.CTkFrame, app: "App"):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.engine = FilingEngine(app.db)
        self._filings: list[dict] = []
        self._packages: list[dict] = []
        self._selected_filing: Optional[dict] = None
        self._selected_package: Optional[dict] = None
        self._current_stack: Optional[FilingStack] = None
        self._current_validation: Optional[ValidationResult] = None

        # Bridge to real litigation_context.db + disk packages
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
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── Title bar ──
        title = ctk.CTkLabel(self, text="📄 MBP LLC — Filing Manager", font=ctk.CTkFont(size=20, weight="bold"))
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(12, 4))

        # ── Left panel: filter + list ──
        left = ctk.CTkFrame(self, width=360)
        left.grid(row=1, column=0, sticky="nsew", padx=(12, 4), pady=8)
        left.grid_rowconfigure(3, weight=1)
        left.grid_columnconfigure(0, weight=1)

        self._build_filters(left)
        self._build_filing_list(left)

        # ── Right panel: detail ──
        right = ctk.CTkFrame(self)
        right.grid(row=1, column=1, sticky="nsew", padx=(4, 12), pady=8)
        right.grid_rowconfigure(5, weight=1)
        right.grid_columnconfigure(0, weight=1)

        self._build_detail_panel(right)

    # -- Filters --------------------------------------------------------------

    def _build_filters(self, parent: ctk.CTkFrame) -> None:
        filt = ctk.CTkFrame(parent, fg_color="transparent")
        filt.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        filt.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(filt, text="Status").grid(row=0, column=0, sticky="w")
        status_values = list(VALID_STATUSES)
        if self._bridge:
            # Add package-specific statuses
            for s in ("ready", "draft", "incomplete"):
                if s not in status_values:
                    status_values.append(s)
        self._filter_status = ctk.CTkComboBox(
            filt, values=["All"] + status_values, command=lambda _: self.refresh()
        )
        self._filter_status.set("All")
        self._filter_status.grid(row=1, column=0, sticky="ew", padx=(0, 4))

        ctk.CTkLabel(filt, text="Type").grid(row=0, column=1, sticky="w")
        self._filter_type = ctk.CTkComboBox(
            filt, values=["All"] + list(VALID_FILING_TYPES), command=lambda _: self.refresh()
        )
        self._filter_type.set("All")
        self._filter_type.grid(row=1, column=1, sticky="ew", padx=4)

        ctk.CTkLabel(filt, text="Court").grid(row=0, column=2, sticky="w")
        self._filter_court = ctk.CTkEntry(filt, placeholder_text="Court filter…")
        self._filter_court.grid(row=1, column=2, sticky="ew", padx=(4, 0))
        self._filter_court.bind("<Return>", lambda _: self.refresh())

    # -- Filing list ----------------------------------------------------------

    def _build_filing_list(self, parent: ctk.CTkFrame) -> None:
        ctk.CTkLabel(parent, text="Filings", font=ctk.CTkFont(weight="bold")).grid(
            row=1, column=0, sticky="w", padx=8, pady=(8, 2)
        )

        btn_row = ctk.CTkFrame(parent, fg_color="transparent")
        btn_row.grid(row=2, column=0, sticky="ew", padx=8)
        new_filing_btn = ctk.CTkButton(btn_row, text="＋ New Filing", width=120, command=self._on_new_filing)
        new_filing_btn.pack(side="left", pady=4)
        Tooltip(new_filing_btn, "Create a new court filing from scratch")

        scroll = ctk.CTkScrollableFrame(parent)
        scroll.grid(row=3, column=0, sticky="nsew", padx=8, pady=(4, 8))
        scroll.grid_columnconfigure(0, weight=1)
        self._list_frame = scroll

    # -- Detail panel ---------------------------------------------------------

    def _build_detail_panel(self, parent: ctk.CTkFrame) -> None:
        # Header
        self._detail_title = ctk.CTkLabel(
            parent, text="Select a filing", font=ctk.CTkFont(size=18, weight="bold")
        )
        self._detail_title.grid(row=0, column=0, sticky="w", padx=16, pady=(12, 4))

        # Info frame
        info = ctk.CTkFrame(parent, fg_color="transparent")
        info.grid(row=1, column=0, sticky="ew", padx=16, pady=4)
        info.grid_columnconfigure((1, 3, 5), weight=1)

        ctk.CTkLabel(info, text="Type:").grid(row=0, column=0, sticky="w")
        self._lbl_type = ctk.CTkLabel(info, text="—")
        self._lbl_type.grid(row=0, column=1, sticky="w", padx=(4, 16))

        ctk.CTkLabel(info, text="Court:").grid(row=0, column=2, sticky="w")
        self._lbl_court = ctk.CTkLabel(info, text="—")
        self._lbl_court.grid(row=0, column=3, sticky="w", padx=(4, 16))

        ctk.CTkLabel(info, text="Status:").grid(row=0, column=4, sticky="w")
        self._lbl_status = ctk.CTkLabel(info, text="—")
        self._lbl_status.grid(row=0, column=5, sticky="w", padx=(4, 0))

        # Status workflow
        self._build_status_workflow(parent)

        # Score bar
        score_frame = ctk.CTkFrame(parent, fg_color="transparent")
        score_frame.grid(row=3, column=0, sticky="ew", padx=16, pady=4)
        score_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(score_frame, text="Score:").grid(row=0, column=0, sticky="w")
        self._score_bar = ctk.CTkProgressBar(score_frame)
        self._score_bar.grid(row=0, column=1, sticky="ew", padx=8)
        self._score_bar.set(0)
        self._score_label = ctk.CTkLabel(score_frame, text="—")
        self._score_label.grid(row=0, column=2, sticky="e")

        # Checklist / issues
        self._issues_text = ctk.CTkTextbox(parent, height=120)
        self._issues_text.grid(row=4, column=0, sticky="ew", padx=16, pady=4)

        # Documents attached
        ctk.CTkLabel(parent, text="Attached Documents", font=ctk.CTkFont(weight="bold")).grid(
            row=5, column=0, sticky="nw", padx=16, pady=(8, 2)
        )
        self._doc_list = ctk.CTkScrollableFrame(parent, height=120)
        self._doc_list.grid(row=6, column=0, sticky="nsew", padx=16, pady=(0, 4))
        self._doc_list.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(6, weight=1)

        # Action buttons
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.grid(row=7, column=0, sticky="ew", padx=16, pady=(4, 12))

        self._btn_build = ctk.CTkButton(btn_frame, text="Build Stack", command=self._on_build_stack)
        self._btn_build.pack(side="left", padx=(0, 8))
        Tooltip(self._btn_build, "Assemble filing components (main doc, exhibits, proof of service)")
        self._btn_validate = ctk.CTkButton(
            btn_frame, text="Validate", fg_color="#F59E0B", hover_color="#D97706",
            command=self._on_validate,
        )
        self._btn_validate.pack(side="left", padx=8)
        Tooltip(self._btn_validate, "Run compliance checks against Michigan Court Rules")
        self._btn_export = ctk.CTkButton(
            btn_frame, text="Export", fg_color="#10B981", hover_color="#059669",
            command=self._on_export,
        )
        self._btn_export.pack(side="left", padx=8)
        Tooltip(self._btn_export, "Export filing package to DOCX/PDF for court submission")

        self._btn_open_folder = ctk.CTkButton(
            btn_frame, text="📂 Open Folder", fg_color="#6366F1", hover_color="#4F46E5",
            command=self._on_open_folder,
        )
        Tooltip(self._btn_open_folder, "Open the filing folder in Windows Explorer")
        self._btn_open_main = ctk.CTkButton(
            btn_frame, text="📄 Open Filing", fg_color="#8B5CF6", hover_color="#7C3AED",
            command=self._on_open_main_filing,
        )
        Tooltip(self._btn_open_main, "Open the main filing document")

    def _build_status_workflow(self, parent: ctk.CTkFrame) -> None:
        wf = ctk.CTkFrame(parent, fg_color="transparent")
        wf.grid(row=2, column=0, sticky="ew", padx=16, pady=4)
        _status_tips = {
            "draft": "Initial draft — still being written",
            "review": "Under review — checking for errors and compliance",
            "ready": "Ready to file — all checks passed",
            "filed": "Filed with the court — awaiting confirmation",
            "served": "Served on opposing party — proof of service attached",
        }
        self._status_btns: dict[str, ctk.CTkButton] = {}
        for i, status in enumerate(_STATUS_LABELS):
            btn = ctk.CTkButton(
                wf, text=status.capitalize(), width=80, height=26,
                fg_color=_STATUS_COLORS[status],
                command=lambda s=status: self._on_set_status(s),
            )
            btn.grid(row=0, column=i * 2, padx=2)
            self._status_btns[status] = btn
            Tooltip(btn, _status_tips.get(status, status.capitalize()))
            if i < len(_STATUS_LABELS) - 1:
                ctk.CTkLabel(wf, text="→").grid(row=0, column=i * 2 + 1)

    # -- Data -----------------------------------------------------------------

    def refresh(self) -> None:
        """Reload filing list from DB + disk packages via bridge."""
        status_val = self._filter_status.get()
        type_val = self._filter_type.get()
        court_val = self._filter_court.get().strip()

        # Try loading disk-based filing packages via bridge
        if self._bridge:
            self._packages = self._bridge.get_filing_packages()
            if self._packages:
                # Apply status filter to packages
                if status_val != "All":
                    self._packages = [p for p in self._packages if p.get("status") == status_val]
                if court_val:
                    court_lower = court_val.lower()
                    self._packages = [
                        p for p in self._packages
                        if court_lower in p.get("title", "").lower()
                    ]
                self._populate_package_list()
                return

        # Fallback to engine-based filings
        status_filter = None if status_val == "All" else status_val
        self._filings = self.engine.get_filings(status=status_filter)

        if type_val != "All":
            self._filings = [f for f in self._filings if f.get("filing_type") == type_val]
        if court_val:
            court_lower = court_val.lower()
            self._filings = [
                f for f in self._filings
                if court_lower in (f.get("notes") or "").lower()
            ]

        self._populate_list()

    def _populate_list(self) -> None:
        for w in self._list_frame.winfo_children():
            w.destroy()

        if not self._filings:
            ctk.CTkLabel(self._list_frame, text="No filings found.", text_color="#6B7280").pack(
                pady=20
            )
            return

        for filing in self._filings:
            row = ctk.CTkFrame(self._list_frame, cursor="hand2")
            row.pack(fill="x", pady=2)
            row.grid_columnconfigure(1, weight=1)

            status_color = _STATUS_COLORS.get(filing.get("status", ""), "#6B7280")
            dot = ctk.CTkLabel(row, text="●", text_color=status_color, width=20)
            dot.grid(row=0, column=0, padx=(8, 4), pady=6)

            lbl = ctk.CTkLabel(
                row, text=filing.get("title", "Untitled"), anchor="w",
                font=ctk.CTkFont(size=13),
            )
            lbl.grid(row=0, column=1, sticky="ew", pady=6)

            tag = ctk.CTkLabel(
                row, text=filing.get("filing_type", ""), text_color="#9CA3AF",
                font=ctk.CTkFont(size=11),
            )
            tag.grid(row=0, column=2, padx=8, pady=6)

            for widget in (row, dot, lbl, tag):
                widget.bind("<Button-1>", lambda e, f=filing: self._on_select(f))

            ContextMenu(row, items=[
                ("Open in Explorer", lambda f=filing: self._ctx_open_filing(f)),
                ("View Main Filing", lambda f=filing: self._ctx_view_main(f)),
                ("---", None),
                ("Copy Filing Title", lambda f=filing: self._ctx_copy_title(f)),
                ("Duplicate Filing", lambda f=filing: self._ctx_duplicate(f)),
            ])

    def _populate_package_list(self) -> None:
        """Populate left panel with disk-based filing packages."""
        for w in self._list_frame.winfo_children():
            w.destroy()

        if not self._packages:
            ctk.CTkLabel(self._list_frame, text="No filing packages found.", text_color="#6B7280").pack(
                pady=20
            )
            return

        for pkg in self._packages:
            row = ctk.CTkFrame(self._list_frame, cursor="hand2")
            row.pack(fill="x", pady=2)
            row.grid_columnconfigure(1, weight=1)

            status = pkg.get("status", "incomplete")
            status_color = _STATUS_COLORS.get(status, "#6B7280")
            dot = ctk.CTkLabel(row, text="●", text_color=status_color, width=20)
            dot.grid(row=0, column=0, padx=(8, 4), pady=6)

            lbl = ctk.CTkLabel(
                row, text=pkg.get("title", pkg.get("id", "Untitled")), anchor="w",
                font=ctk.CTkFont(size=13),
            )
            lbl.grid(row=0, column=1, sticky="ew", pady=6)

            info_text = f"{pkg.get('file_count', 0)} files · {pkg.get('total_size_str', '')}"
            tag = ctk.CTkLabel(
                row, text=info_text, text_color="#9CA3AF",
                font=ctk.CTkFont(size=11),
            )
            tag.grid(row=0, column=2, padx=8, pady=6)

            for widget in (row, dot, lbl, tag):
                widget.bind("<Button-1>", lambda e, p=pkg: self._on_select_package(p))

    def _on_select_package(self, pkg: dict) -> None:
        """Handle selection of a disk-based filing package."""
        self._selected_package = pkg
        self._selected_filing = None
        self._current_stack = None
        self._current_validation = None
        self._show_package_detail(pkg)

    def _show_package_detail(self, pkg: dict) -> None:
        """Show filing package detail in the right panel."""
        self._detail_title.configure(text=pkg.get("title", pkg.get("id", "Untitled")))

        status = pkg.get("status", "incomplete")
        self._lbl_type.configure(text="Filing Package")
        self._lbl_court.configure(text=pkg.get("total_size_str", "—"))
        self._lbl_status.configure(
            text=status.capitalize(),
            text_color=_STATUS_COLORS.get(status, "#FFFFFF"),
        )

        # Score based on completeness
        completeness = 0
        if pkg.get("has_main_filing"):
            completeness += 40
        if pkg.get("has_affidavit"):
            completeness += 20
        if pkg.get("has_exhibits"):
            completeness += 20
        if pkg.get("has_assembled"):
            completeness += 20
        self._set_score(completeness)

        # Checklist
        self._issues_text.delete("1.0", "end")
        self._issues_text.insert("end", "PACKAGE CHECKLIST\n" + "─" * 40 + "\n")
        checks = [
            ("Main Filing (01_MAIN_FILING.md)", pkg.get("has_main_filing", False)),
            ("Affidavit (02_AFFIDAVIT)", pkg.get("has_affidavit", False)),
            ("Exhibit Index", pkg.get("has_exhibits", False)),
            ("Assembled Filing", pkg.get("has_assembled", False)),
        ]
        for label, ok in checks:
            icon = "✅" if ok else "❌"
            self._issues_text.insert("end", f"  {icon}  {label}\n")
        self._issues_text.insert("end", f"\nFiles: {pkg.get('file_count', 0)}\n")
        self._issues_text.insert("end", f"Size: {pkg.get('total_size_str', '—')}\n")

        # Populate document list with files from the package
        for w in self._doc_list.winfo_children():
            w.destroy()
        for fname in pkg.get("files", []):
            icon = "📄"
            if fname.startswith("01_MAIN"):
                icon = "📋"
            elif fname.startswith("02_AFFIDAVIT"):
                icon = "✍️"
            elif "EXHIBIT" in fname.upper():
                icon = "📎"
            elif fname.startswith("ASSEMBLED_"):
                icon = "📦"
            lbl = ctk.CTkLabel(
                self._doc_list,
                text=f"  {icon} {fname}",
                anchor="w",
            )
            lbl.pack(fill="x", padx=4, pady=1)

        # Show/hide package-specific buttons
        self._btn_open_folder.pack(side="left", padx=8)
        self._btn_open_main.pack(side="left", padx=8)

    def _on_open_folder(self) -> None:
        """Open the selected package directory in Windows Explorer."""
        pkg = self._selected_package
        if not pkg or not pkg.get("dir_path"):
            return
        try:
            os.startfile(pkg["dir_path"])  # type: ignore[attr-defined]
        except Exception as exc:
            messagebox.showerror("Open Folder", str(exc))

    def _on_open_main_filing(self) -> None:
        """Open the main filing markdown in the default editor."""
        pkg = self._selected_package
        if not pkg or not pkg.get("dir_path"):
            return
        main = Path(pkg["dir_path"]) / "01_MAIN_FILING.md"
        if not main.exists():
            messagebox.showwarning("Open Filing", "01_MAIN_FILING.md not found in this package.")
            return
        try:
            os.startfile(str(main))  # type: ignore[attr-defined]
        except Exception as exc:
            messagebox.showerror("Open Filing", str(exc))

    def _on_select(self, filing: dict) -> None:
        self._selected_filing = filing
        self._selected_package = None
        self._current_stack = None
        self._current_validation = None
        # Hide package-specific buttons
        self._btn_open_folder.pack_forget()
        self._btn_open_main.pack_forget()
        self._show_detail(filing)

    # -- Context menu handlers ------------------------------------------------

    def _ctx_open_filing(self, filing: dict) -> None:
        notes = filing.get("notes") or ""
        for line in notes.splitlines():
            if line.startswith("Path:"):
                path = line.replace("Path:", "").strip()
                if os.path.exists(path):
                    os.startfile(os.path.dirname(path))
                    return
        from tkinter import messagebox
        messagebox.showinfo("Info", "No file path associated with this filing.")

    def _ctx_view_main(self, filing: dict) -> None:
        notes = filing.get("notes") or ""
        for line in notes.splitlines():
            if line.startswith("Path:"):
                path = line.replace("Path:", "").strip()
                if os.path.exists(path):
                    os.startfile(path)
                    return
        from tkinter import messagebox
        messagebox.showinfo("Info", "No main filing document found.")

    def _ctx_copy_title(self, filing: dict) -> None:
        try:
            self.clipboard_clear()
            self.clipboard_append(filing.get("title", ""))
        except Exception:
            pass

    def _ctx_duplicate(self, filing: dict) -> None:
        if not self.engine:
            return
        try:
            self.engine.create_filing(
                title=f"Copy of {filing.get('title', 'Untitled')}",
                filing_type=filing.get("filing_type", "motion"),
                case_id=filing.get("case_id"),
                notes=filing.get("notes"),
            )
            self.refresh()
        except Exception:
            logger.exception("Failed to duplicate filing")

    def _show_detail(self, filing: dict) -> None:
        self._detail_title.configure(text=filing.get("title", "Untitled"))
        self._lbl_type.configure(text=filing.get("filing_type", "—"))

        notes = filing.get("notes") or ""
        court_line = ""
        for line in notes.splitlines():
            if line.startswith("Court:"):
                court_line = line.replace("Court:", "").strip()
                break
        self._lbl_court.configure(text=court_line or "—")

        status = filing.get("status", "draft")
        self._lbl_status.configure(text=status.capitalize(), text_color=_STATUS_COLORS.get(status, "#FFFFFF"))

        # Score
        score = filing.get("compliance_score")
        if score is not None:
            self._set_score(int(score))
        else:
            self._score_bar.set(0)
            self._score_label.configure(text="—")

        self._issues_text.delete("1.0", "end")

        # Load attached documents
        self._load_documents(filing.get("id"))

    def _load_documents(self, filing_id: Optional[int]) -> None:
        for w in self._doc_list.winfo_children():
            w.destroy()
        if filing_id is None:
            return
        try:
            rows = self.app.db.fetchall(
                "SELECT id, title, format, output_path FROM documents WHERE filing_id = ? ORDER BY id",
                (filing_id,),
            )
            if not rows:
                ctk.CTkLabel(self._doc_list, text="No documents attached.", text_color="#6B7280").pack(pady=8)
                return
            for row in rows:
                d = dict(row)
                lbl = ctk.CTkLabel(
                    self._doc_list,
                    text=f"  📄 {d.get('title', 'Untitled')}  [{d.get('format', '')}]",
                    anchor="w",
                )
                lbl.pack(fill="x", padx=4, pady=1)
        except Exception as exc:
            logger.warning("Failed to load documents for filing %s: %s", filing_id, exc)

    # -- Score display --------------------------------------------------------

    def _set_score(self, score: int) -> None:
        frac = max(0.0, min(score / 100.0, 1.0))
        self._score_bar.set(frac)
        if score >= 80:
            color = "#10B981"
        elif score >= 50:
            color = "#F59E0B"
        else:
            color = "#EF4444"
        self._score_bar.configure(progress_color=color)
        self._score_label.configure(text=f"{score}%", text_color=color)

    # -- Actions --------------------------------------------------------------

    def _on_build_stack(self) -> None:
        if not self._selected_filing:
            messagebox.showinfo("Filing Manager", "Select a filing first.")
            return
        try:
            stack = self.engine.build_stack(
                self._selected_filing["case_id"],
                self._selected_filing["filing_type"],
            )
            self._current_stack = stack
            # Show checklist in issues box
            self._issues_text.delete("1.0", "end")
            self._issues_text.insert("end", "BUILD STACK CHECKLIST\n" + "─" * 40 + "\n")
            for item, ok in stack.checklist.items():
                icon = "✅" if ok else "❌"
                self._issues_text.insert("end", f"  {icon}  {item}\n")
            complete_pct = (
                sum(stack.checklist.values()) / max(len(stack.checklist), 1) * 100
            )
            self._issues_text.insert("end", f"\nComponents: {len(stack.components)}\n")
            self._issues_text.insert("end", f"Complete: {complete_pct:.0f}%\n")
        except Exception as exc:
            messagebox.showerror("Build Stack", str(exc))

    def _on_validate(self) -> None:
        if self._current_stack is None:
            if self._selected_filing:
                self._on_build_stack()
            if self._current_stack is None:
                messagebox.showinfo("Filing Manager", "Build a stack first.")
                return
        try:
            result = self.engine.validate_stack(self._current_stack)
            self._current_validation = result
            self._set_score(result.score)

            self._issues_text.delete("1.0", "end")
            self._issues_text.insert("end", f"VALIDATION — Score: {result.score}%\n")
            self._issues_text.insert("end", "─" * 40 + "\n")
            if result.issues:
                self._issues_text.insert("end", "Issues:\n")
                for issue in result.issues:
                    self._issues_text.insert("end", f"  ⚠  {issue}\n")
            if result.warnings:
                self._issues_text.insert("end", "\nWarnings:\n")
                for w in result.warnings:
                    self._issues_text.insert("end", f"  ℹ  {w}\n")
            if result.valid:
                self._issues_text.insert("end", "\n✅ Filing is VALID and ready for submission.\n")
            else:
                self._issues_text.insert("end", "\n❌ Filing has issues that must be resolved.\n")

            # Persist score
            if self._selected_filing:
                self.app.db.execute(
                    "UPDATE filings SET compliance_score = ? WHERE id = ?",
                    (result.score, self._selected_filing["id"]),
                )
        except Exception as exc:
            messagebox.showerror("Validate", str(exc))

    def _on_export(self) -> None:
        if self._current_stack is None:
            messagebox.showinfo("Filing Manager", "Build a stack first.")
            return
        out_dir = filedialog.askdirectory(title="Select export directory")
        if not out_dir:
            return
        try:
            export_path = self.engine.export_stack(self._current_stack, out_dir)
            messagebox.showinfo("Export", f"Filing exported to:\n{export_path}")
        except Exception as exc:
            messagebox.showerror("Export", str(exc))

    def _on_set_status(self, new_status: str) -> None:
        if not self._selected_filing:
            return
        try:
            self.engine.update_status(self._selected_filing["id"], new_status)
            self._selected_filing["status"] = new_status
            self._lbl_status.configure(
                text=new_status.capitalize(),
                text_color=_STATUS_COLORS.get(new_status, "#FFFFFF"),
            )
            self.refresh()
        except Exception as exc:
            messagebox.showerror("Status", str(exc))

    def _on_new_filing(self) -> None:
        _NewFilingDialog(self, self.app, self.engine, on_done=self.refresh)


# -- New-filing dialog --------------------------------------------------------


class _NewFilingDialog(ctk.CTkToplevel):
    """Modal dialog for creating a new filing."""

    def __init__(self, parent, app: "App", engine: FilingEngine, *, on_done):
        super().__init__(parent)
        self.title("New Filing")
        self.geometry("420x340")
        self.resizable(False, False)
        self.grab_set()
        self._engine = engine
        self._app = app
        self._on_done = on_done

        pad = dict(padx=16, pady=4, sticky="ew")
        r = 0

        ctk.CTkLabel(self, text="Title").grid(row=r, column=0, **pad); r += 1
        self._entry_title = ctk.CTkEntry(self, placeholder_text="e.g. Motion for Summary Judgment")
        self._entry_title.grid(row=r, column=0, **pad); r += 1

        ctk.CTkLabel(self, text="Filing Type").grid(row=r, column=0, **pad); r += 1
        self._combo_type = ctk.CTkComboBox(self, values=list(VALID_FILING_TYPES))
        self._combo_type.grid(row=r, column=0, **pad); r += 1

        ctk.CTkLabel(self, text="Court").grid(row=r, column=0, **pad); r += 1
        self._entry_court = ctk.CTkEntry(self, placeholder_text="e.g. 14th Circuit Court")
        self._entry_court.grid(row=r, column=0, **pad); r += 1

        ctk.CTkLabel(self, text="Case ID").grid(row=r, column=0, **pad); r += 1
        self._entry_case = ctk.CTkEntry(self, placeholder_text="Numeric case ID")
        self._entry_case.grid(row=r, column=0, **pad); r += 1

        ctk.CTkButton(self, text="Create", command=self._create).grid(row=r, column=0, **pad)

        self.grid_columnconfigure(0, weight=1)

    def _create(self) -> None:
        title = self._entry_title.get().strip()
        ftype = self._combo_type.get()
        court = self._entry_court.get().strip()
        case_raw = self._entry_case.get().strip()
        if not title or not case_raw:
            messagebox.showwarning("New Filing", "Title and Case ID are required.")
            return
        try:
            case_id = int(case_raw)
        except ValueError:
            messagebox.showwarning("New Filing", "Case ID must be a number.")
            return
        try:
            self._engine.create_filing(case_id, ftype, court, title)
            self.destroy()
            self._on_done()
        except Exception as exc:
            messagebox.showerror("New Filing", str(exc))
