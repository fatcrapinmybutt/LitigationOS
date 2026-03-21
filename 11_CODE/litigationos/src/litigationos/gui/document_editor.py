"""Document Editor — In-app document viewer with compliance highlighting.

Provides a plain-text editor with word count, a compliance checker that
flags unresolved placeholders and word-limit violations, and open/save.

Wired to: DocumentEngine (placeholder resolver), CourtRulesEngine (brief compliance).
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING

import customtkinter as ctk

from litigationos.gui.widgets import COLORS

if TYPE_CHECKING:
    from litigationos.db.connection import DatabaseManager

logger = logging.getLogger(__name__)

_PLACEHOLDER_RE = re.compile(
    r"\[(?:PLACEHOLDER|TODO|INSERT|ANDREW|TBD|FILL)[^\]]*\]",
    re.IGNORECASE,
)

_JINJA_PLACEHOLDER_RE = re.compile(r"\{\{\s*\w+\s*\}\}")

# Engine imports -- graceful fallback
try:
    from litigationos.engines.court_rules import CourtRulesEngine
    _HAS_RULES_ENGINE = True
except ImportError:
    _HAS_RULES_ENGINE = False

try:
    from litigationos.engines.document import DocumentEngine
    _HAS_DOC_ENGINE = True
except ImportError:
    _HAS_DOC_ENGINE = False


class DocumentEditorFrame(ctk.CTkFrame):
    """Document viewer/editor with real-time compliance checking."""

    def __init__(
        self,
        parent,
        db: "DatabaseManager",
        navigate_cb=None,
        **kwargs,
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._db = db
        self._navigate_cb = navigate_cb
        self._current_file: str | None = None
        self._build_ui()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_ui(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=12)
        hdr.pack(fill="x", padx=16, pady=(16, 8))

        ctk.CTkLabel(
            hdr,
            text="📃 MBP LLC — Document Editor",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS["text"],
        ).pack(side="left", padx=16, pady=12)

        # Toolbar
        toolbar = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=8)
        toolbar.pack(fill="x", padx=16, pady=4)

        ctk.CTkButton(
            toolbar, text="Open", width=80, command=self._open_file,
            fg_color=COLORS["blue"], hover_color=COLORS["accent"], corner_radius=8,
        ).pack(side="left", padx=6, pady=6)

        ctk.CTkButton(
            toolbar, text="Save", width=80, command=self._save_file,
            fg_color=COLORS["blue"], hover_color=COLORS["accent"], corner_radius=8,
        ).pack(side="left", padx=6, pady=6)

        ctk.CTkButton(
            toolbar, text="Check Compliance", width=140,
            command=self._check_compliance,
            fg_color=COLORS["orange"], hover_color=COLORS["accent"], corner_radius=8,
        ).pack(side="left", padx=6, pady=6)

        self._placeholder_label = ctk.CTkLabel(
            toolbar, text="Placeholders: 0",
            font=ctk.CTkFont(size=12), text_color=COLORS["text_dim"],
        )
        self._placeholder_label.pack(side="right", padx=12, pady=6)

        self._compliance_label = ctk.CTkLabel(
            toolbar, text="Compliance: --",
            font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["text_dim"],
        )
        self._compliance_label.pack(side="right", padx=12, pady=6)

        self._word_label = ctk.CTkLabel(
            toolbar, text="Words: 0",
            font=ctk.CTkFont(size=12), text_color=COLORS["text_dim"],
        )
        self._word_label.pack(side="right", padx=12, pady=6)

        self._file_label = ctk.CTkLabel(
            toolbar, text="No file open",
            font=ctk.CTkFont(size=11), text_color=COLORS["text_dim"],
        )
        self._file_label.pack(side="right", padx=12, pady=6)

        # Editor
        self._editor = ctk.CTkTextbox(
            self, font=("Courier New", 12), corner_radius=8,
        )
        self._editor.pack(fill="both", expand=True, padx=16, pady=8)

        # Status bar
        self._status = ctk.CTkLabel(
            self, text="Ready", font=ctk.CTkFont(size=11),
            text_color=COLORS["text_dim"], anchor="w",
        )
        self._status.pack(fill="x", padx=16, pady=(0, 8))

    # ------------------------------------------------------------------
    # File operations
    # ------------------------------------------------------------------

    def _open_file(self):
        from tkinter import filedialog

        filepath = filedialog.askopenfilename(
            initialdir=str(Path.home() / "LitigationOS"),
            filetypes=[
                ("Markdown", "*.md"),
                ("Text", "*.txt"),
                ("All files", "*.*"),
            ],
        )
        if not filepath:
            return

        self._current_file = filepath
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
                content = fh.read()
        except Exception:
            logger.exception("Failed to open %s", filepath)
            self._status.configure(text=f"Error opening file", text_color=COLORS["red"])
            return

        self._editor.delete("0.0", "end")
        self._editor.insert("0.0", content)
        self._file_label.configure(text=Path(filepath).name)
        self._update_word_count()
        self._status.configure(text=f"Opened: {filepath}", text_color=COLORS["text_dim"])

    def _save_file(self):
        if not self._current_file:
            self._status.configure(text="No file to save", text_color=COLORS["orange"])
            return

        content = self._editor.get("0.0", "end")
        try:
            with open(self._current_file, "w", encoding="utf-8") as fh:
                fh.write(content)
            self._status.configure(
                text=f"Saved: {self._current_file}", text_color=COLORS["green"],
            )
        except Exception:
            logger.exception("Failed to save %s", self._current_file)
            self._status.configure(text="Save failed", text_color=COLORS["red"])

    # ------------------------------------------------------------------
    # Compliance
    # ------------------------------------------------------------------

    def _check_compliance(self):
        content = self._editor.get("0.0", "end")
        bracket_placeholders = len(_PLACEHOLDER_RE.findall(content))
        jinja_placeholders = len(_JINJA_PLACEHOLDER_RE.findall(content))
        total_placeholders = bracket_placeholders + jinja_placeholders
        words = len(content.split())
        pages_est = max(1, words // 250)

        issues: list[str] = []
        warnings: list[str] = []

        if total_placeholders:
            issues.append(f"{total_placeholders} unresolved placeholder(s)")
        if words > 16_000:
            issues.append(f"Over word limit ({words:,}/16,000)")

        # Engine-backed compliance check
        if _HAS_RULES_ENGINE and self._db:
            try:
                rules_engine = CourtRulesEngine(self._db)
                filing_meta = {
                    "page_count": pages_est,
                    "word_count": words,
                    "spacing": "double",
                }
                result = rules_engine.validate_filing_format(filing_meta, "MCR 7.212")
                if result.get("errors"):
                    issues.extend(result["errors"])
                if result.get("warnings"):
                    warnings.extend(result["warnings"])
                score = result.get("score", 0)
                if isinstance(score, float):
                    score = int(score * 100)
            except Exception:
                logger.debug("CourtRulesEngine compliance check failed")
                score = None
        else:
            score = None

        # Update placeholder count display
        ph_color = COLORS["red"] if total_placeholders else COLORS["green"]
        self._placeholder_label.configure(
            text=f"Placeholders: {total_placeholders}", text_color=ph_color,
        )

        # Update compliance indicator
        if score is not None:
            if score >= 80:
                c_color = COLORS["green"]
                c_text = f"Compliance: PASS ({score}%)"
            elif score >= 50:
                c_color = COLORS["orange"]
                c_text = f"Compliance: WARN ({score}%)"
            else:
                c_color = COLORS["red"]
                c_text = f"Compliance: FAIL ({score}%)"
            self._compliance_label.configure(text=c_text, text_color=c_color)
        elif not issues:
            self._compliance_label.configure(
                text="Compliance: PASS", text_color=COLORS["green"],
            )

        # Status bar
        if issues:
            all_msgs = issues + [f"(warning) {w}" for w in warnings]
            self._status.configure(
                text=f"Issues: {'; '.join(all_msgs)}", text_color=COLORS["orange"],
            )
        elif warnings:
            self._status.configure(
                text=f"Warnings: {'; '.join(warnings)}", text_color=COLORS["orange"],
            )
        else:
            self._status.configure(text="Compliance: PASS", text_color=COLORS["green"])

        self._update_word_count()

    def _update_word_count(self):
        content = self._editor.get("0.0", "end")
        words = len(content.split())
        self._word_label.configure(text=f"Words: {words:,}")
