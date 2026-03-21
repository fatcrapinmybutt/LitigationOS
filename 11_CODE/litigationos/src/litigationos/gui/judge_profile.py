"""Judge and court profile viewer for LitigationOS.

Displays judicial tendencies, ruling patterns, and court intelligence
sourced from jurisdiction databases and the central litigation DB.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any, Callable, Optional

import customtkinter as ctk

from litigationos.gui.widgets import COLORS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths to jurisdiction databases
# ---------------------------------------------------------------------------

_DATABASES_DIR = Path(r"C:\Users\andre\LitigationOS\databases")
_FAMILY_DB = _DATABASES_DIR / "jurisdiction_14th_circuit_family.db"
_JTC_DB = _DATABASES_DIR / "jurisdiction_jtc.db"
_COA_DB = _DATABASES_DIR / "jurisdiction_coa.db"
_MAIN_DB = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")

# ---------------------------------------------------------------------------
# Star rendering
# ---------------------------------------------------------------------------

_STAR_FULL = "★"
_STAR_EMPTY = "☆"


def _stars(rating: int, out_of: int = 5) -> str:
    rating = max(0, min(rating, out_of))
    return _STAR_FULL * rating + _STAR_EMPTY * (out_of - rating)


# ---------------------------------------------------------------------------
# Data access helpers
# ---------------------------------------------------------------------------


def _safe_query(
    db_path: Path, sql: str, params: tuple = ()
) -> list[dict[str, Any]]:
    """Run *sql* against *db_path*; return list-of-dicts or []."""
    if not db_path.exists():
        return []
    try:
        conn = sqlite3.connect(str(db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        logger.debug("Query against %s failed", db_path, exc_info=True)
        return []


def _table_exists(db_path: Path, table: str) -> bool:
    if not db_path.exists():
        return False
    try:
        conn = sqlite3.connect(str(db_path), timeout=5)
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        )
        found = cur.fetchone() is not None
        conn.close()
        return found
    except Exception:
        return False


def _load_judge_names() -> list[str]:
    """Collect judge names from all jurisdiction databases."""
    names: set[str] = set()

    if _table_exists(_FAMILY_DB, "judges"):
        for row in _safe_query(_FAMILY_DB, "SELECT DISTINCT name FROM judges"):
            if row.get("name"):
                names.add(row["name"])

    if _table_exists(_COA_DB, "judges_panels"):
        for col in ("judge_name", "name"):
            try:
                for row in _safe_query(
                    _COA_DB, f"SELECT DISTINCT {col} FROM judges_panels"
                ):
                    if row.get(col):
                        names.add(row[col])
                break
            except Exception:
                continue

    # Central DB
    if _table_exists(_MAIN_DB, "judicial_violations"):
        for row in _safe_query(
            _MAIN_DB,
            "SELECT DISTINCT judge_name FROM judicial_violations",
        ):
            if row.get("judge_name"):
                names.add(row["judge_name"])

    if not names:
        names.add("Hon. Jenny L. McNeill")

    return sorted(names)


def _load_profile(name: str) -> dict[str, Any]:
    """Build a profile dict for a judge by name."""
    profile: dict[str, Any] = {
        "name": name,
        "court": "",
        "division": "",
        "years_on_bench": "",
        "avg_processing_days": "",
        "ruling_patterns": "",
        "custody_bias": "Unknown",
        "prose_friendliness": 0,
        "motion_grant_rate": "",
        "continuance_policy": "Unknown",
        "exparte_policy": "Unknown",
        "case_types": "",
        "key_opinions": "",
        "recusal_history": "",
        "violation_count": 0,
        "source_db": "",
    }

    # 14th Circuit Family DB
    if _table_exists(_FAMILY_DB, "judges"):
        rows = _safe_query(
            _FAMILY_DB,
            "SELECT * FROM judges WHERE name = ? LIMIT 1",
            (name,),
        )
        if rows:
            row = rows[0]
            profile["court"] = row.get("court", profile["court"])
            profile["division"] = row.get("division", profile["division"])
            profile["years_on_bench"] = row.get("years_on_bench", "")
            profile["source_db"] = "jurisdiction_14th_circuit_family.db"

    # JTC violations specific to McNeill
    if _table_exists(_JTC_DB, "mcneill_violations"):
        vrows = _safe_query(
            _JTC_DB, "SELECT COUNT(*) AS cnt FROM mcneill_violations"
        )
        if vrows:
            profile["violation_count"] = vrows[0].get("cnt", 0)
            if not profile["source_db"]:
                profile["source_db"] = "jurisdiction_jtc.db"

    # COA panels
    if _table_exists(_COA_DB, "judges_panels"):
        for col in ("judge_name", "name"):
            prows = _safe_query(
                _COA_DB,
                f"SELECT * FROM judges_panels WHERE {col} = ? LIMIT 5",
                (name,),
            )
            if prows:
                profile["key_opinions"] = "; ".join(
                    str(r.get("case_number", r.get("case_id", "")))
                    for r in prows
                    if r.get("case_number") or r.get("case_id")
                )
                if not profile["source_db"]:
                    profile["source_db"] = "jurisdiction_coa.db"
                break

    # Central DB — judicial_violations
    if _table_exists(_MAIN_DB, "judicial_violations"):
        vrows = _safe_query(
            _MAIN_DB,
            "SELECT COUNT(*) AS cnt FROM judicial_violations WHERE judge_name = ?",
            (name,),
        )
        if vrows and vrows[0].get("cnt", 0) > 0:
            profile["violation_count"] += vrows[0]["cnt"]
            if not profile["source_db"]:
                profile["source_db"] = "litigation_context.db"

    return profile


# =========================================================================
# GUI Frame
# =========================================================================


class JudgeProfileFrame(ctk.CTkFrame):
    """Judge and court personality / tendencies profile viewer."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        db=None,
        navigate_cb: Optional[Callable[[str], None]] = None,
    ):
        super().__init__(parent, fg_color="transparent")
        self._db = db
        self._navigate_cb = navigate_cb
        self._judges: list[str] = []
        self._profile: dict[str, Any] = {}

        self._build_ui()
        self.refresh()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        # Header row
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 8))

        ctk.CTkLabel(
            header, text="👨‍⚖️  Judge & Court Profiles",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS["text"],
        ).pack(side="left")

        # Selector
        sel_frame = ctk.CTkFrame(self, fg_color="transparent")
        sel_frame.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(
            sel_frame, text="Select Judge:",
            font=ctk.CTkFont(size=14), text_color=COLORS["text_dim"],
        ).pack(side="left", padx=(0, 8))

        self._judge_var = ctk.StringVar()
        self._judge_menu = ctk.CTkOptionMenu(
            sel_frame, variable=self._judge_var,
            values=["(loading…)"],
            fg_color=COLORS["bg_card"], button_color=COLORS["accent"],
            button_hover_color="#c93a52", text_color=COLORS["text"],
            width=320,
            command=lambda _: self._on_judge_selected(),
        )
        self._judge_menu.pack(side="left")

        ctk.CTkButton(
            sel_frame, text="⟳ Refresh", width=90, height=32,
            fg_color=COLORS["bg_card"], hover_color=COLORS["accent"],
            text_color=COLORS["text"], corner_radius=8,
            command=self.refresh,
        ).pack(side="left", padx=(12, 0))

        # Scrollable body
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color=COLORS["bg_dark"], corner_radius=0,
        )
        self._scroll.pack(fill="both", expand=True, padx=0, pady=0)

        self._cards_frame = ctk.CTkFrame(self._scroll, fg_color="transparent")
        self._cards_frame.pack(fill="both", expand=True, padx=16, pady=10)

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def refresh(self):
        self._judges = _load_judge_names()
        if self._judges:
            self._judge_menu.configure(values=self._judges)
            if not self._judge_var.get() or self._judge_var.get() not in self._judges:
                self._judge_var.set(self._judges[0])
            self._on_judge_selected()
        else:
            self._judge_menu.configure(values=["(no judges found)"])
            self._show_empty()

    def _on_judge_selected(self):
        name = self._judge_var.get()
        if not name or name.startswith("("):
            self._show_empty()
            return
        self._profile = _load_profile(name)
        self._render_profile()

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _show_empty(self):
        for child in self._cards_frame.winfo_children():
            child.destroy()
        ctk.CTkLabel(
            self._cards_frame,
            text="Profile not yet populated — import jurisdiction data to see insights.",
            font=ctk.CTkFont(size=14), text_color=COLORS["text_dim"],
        ).pack(expand=True, pady=40)

    def _render_profile(self):
        for child in self._cards_frame.winfo_children():
            child.destroy()

        p = self._profile

        # --- Profile Card ---
        self._section(self._cards_frame, "Profile")
        card = self._card(self._cards_frame)
        self._kv(card, "Judge", p["name"])
        self._kv(card, "Court", p.get("court") or "—")
        self._kv(card, "Division", p.get("division") or "—")
        self._kv(card, "Years on Bench", p.get("years_on_bench") or "—")
        self._kv(card, "Avg Case Processing", p.get("avg_processing_days") or "—")
        self._kv(card, "Ruling Patterns", p.get("ruling_patterns") or "—")

        # --- Tendencies Panel ---
        self._section(self._cards_frame, "Tendencies")
        tend = self._card(self._cards_frame)

        bias = p.get("custody_bias", "Unknown")
        bias_color = {
            "evidence-based": COLORS["green"],
            "neutral": COLORS["blue"],
        }.get(bias.lower(), COLORS["text_dim"])
        self._kv(tend, "Custody Bias", bias, value_color=bias_color)

        prose_score = p.get("prose_friendliness", 0) or 0
        self._kv(tend, "Pro Se Friendliness", _stars(prose_score))

        grant = p.get("motion_grant_rate", "")
        self._kv(tend, "Motion Grant Rate", grant if grant else "—")

        cont = p.get("continuance_policy", "Unknown")
        self._kv(tend, "Continuance Policy", cont)

        exparte = p.get("exparte_policy", "Unknown")
        self._kv(tend, "Ex Parte Policy", exparte)

        # --- Demographics Panel ---
        self._section(self._cards_frame, "Demographics & History")
        demo = self._card(self._cards_frame)
        self._kv(demo, "Case Types Handled", p.get("case_types") or "—")
        self._kv(demo, "Key Opinions / Orders", p.get("key_opinions") or "—")
        self._kv(demo, "Recusal History", p.get("recusal_history") or "None on record")

        # --- Violations ---
        vcount = p.get("violation_count", 0) or 0
        if vcount > 0:
            self._section(self._cards_frame, "Judicial Violations")
            vcard = self._card(self._cards_frame)
            v_color = COLORS["red"] if vcount >= 5 else COLORS["orange"]
            self._kv(vcard, "Documented Violations", str(vcount), value_color=v_color)

        # --- Source ---
        src = p.get("source_db", "")
        if src:
            ctk.CTkLabel(
                self._cards_frame,
                text=f"Data from: {src}",
                font=ctk.CTkFont(size=11, slant="italic"),
                text_color=COLORS["text_dim"],
            ).pack(anchor="w", pady=(12, 4))
        else:
            ctk.CTkLabel(
                self._cards_frame,
                text="Profile not yet populated — import jurisdiction data to see insights.",
                font=ctk.CTkFont(size=12),
                text_color=COLORS["text_dim"],
            ).pack(anchor="w", pady=(12, 4))

    # ------------------------------------------------------------------
    # Widget helpers
    # ------------------------------------------------------------------

    def _section(self, parent: ctk.CTkFrame, title: str):
        ctk.CTkLabel(
            parent, text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(anchor="w", pady=(14, 4))

    def _card(self, parent: ctk.CTkFrame) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            parent, fg_color=COLORS["bg_card"], corner_radius=10,
        )
        card.pack(fill="x", pady=(0, 4))
        return card

    def _kv(
        self,
        parent: ctk.CTkFrame,
        key: str,
        value: str,
        *,
        value_color: str | None = None,
    ):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=3)
        ctk.CTkLabel(
            row, text=key, width=200, anchor="w",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_dim"],
        ).pack(side="left")
        ctk.CTkLabel(
            row, text=value, anchor="w",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=value_color or COLORS["text"],
        ).pack(side="left", fill="x", expand=True)
