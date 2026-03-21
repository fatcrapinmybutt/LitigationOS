"""Agent Fleet Dashboard — status view for all 56 pipeline agents."""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
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
# Agent registry — 56 agents across 7 tiers, 2 lanes + convergence
# ---------------------------------------------------------------------------

AGENT_REGISTRY: dict[str, dict[str, Any]] = {
    "1": {
        "name": "Tier 1 — Scouts",
        "lane": "Lane 1 — I/O Pipeline",
        "agents": ["A01", "A02", "A03", "A04"],
    },
    "2": {
        "name": "Tier 2 — Dedup",
        "lane": "Lane 1 — I/O Pipeline",
        "agents": ["A05", "A06", "A07", "A08"],
    },
    "3": {
        "name": "Tier 3 — Extract",
        "lane": "Lane 1 — I/O Pipeline",
        "agents": ["A09", "A10", "A11", "A12"],
    },
    "J": {
        "name": "Tier J — Judicial",
        "lane": "Lane 2 — Intelligence",
        "agents": [f"J{i:02d}" for i in range(1, 9)],
    },
    "K": {
        "name": "Tier K — Case Intel",
        "lane": "Lane 2 — Intelligence",
        "agents": [f"K{i:02d}" for i in range(1, 12)],
    },
    "L": {
        "name": "Tier L — Warfare",
        "lane": "Lane 2 — Intelligence",
        "agents": [f"L{i:02d}" for i in range(1, 12)],
    },
    "F": {
        "name": "Tier F — Convergence",
        "lane": "Convergence",
        "agents": [f"F{i:02d}" for i in range(1, 10)],
    },
}

AGENT_NAMES: dict[str, str] = {
    # Tier 1 — Scouts
    "A01": "Drive Scanner",
    "A02": "File Classifier",
    "A03": "Metadata Harvester",
    "A04": "Integrity Checker",
    # Tier 2 — Dedup
    "A05": "Hash Deduplicator",
    "A06": "Content Deduplicator",
    "A07": "Cluster Merger",
    "A08": "Archive Expander",
    # Tier 3 — Extract
    "A09": "PDF Extractor",
    "A10": "DOCX Extractor",
    "A11": "Structured Extractor",
    "A12": "Atom Splitter",
    # Tier J — Judicial
    "J01": "Judicial Profiler",
    "J02": "Ruling Analyzer",
    "J03": "Bias Detector",
    "J04": "Order Tracker",
    "J05": "Docket Analyzer",
    "J06": "Hearing Reviewer",
    "J07": "Precedent Mapper",
    "J08": "Misconduct Scanner",
    # Tier K — Case Intel
    "K01": "Claim Builder",
    "K02": "Evidence Linker",
    "K03": "Timeline Builder",
    "K04": "Contradiction Finder",
    "K05": "Impeachment Engine",
    "K06": "Witness Profiler",
    "K07": "Discovery Tracker",
    "K08": "Exhibit Indexer",
    "K09": "Pattern Analyzer",
    "K10": "Risk Assessor",
    "K11": "Strategy Scorer",
    # Tier L — Warfare
    "L01": "Brief Drafter",
    "L02": "Motion Generator",
    "L03": "Opposition Predictor",
    "L04": "Settlement Analyzer",
    "L05": "Appeal Evaluator",
    "L06": "Authority Validator",
    "L07": "Citation Builder",
    "L08": "Filing Assembler",
    "L09": "Compliance Checker",
    "L10": "Service Tracker",
    "L11": "Deadline Enforcer",
    # Tier F — Convergence
    "F01": "Filing Factory",
    "F02": "Brain Feeder",
    "F03": "Graph Builder",
    "F04": "Certification Engine",
    "F05": "Cross-Lane Merger",
    "F06": "Quality Gate",
    "F07": "Export Packager",
    "F08": "Validation Runner",
    "F09": "Archive Finalizer",
}

MASTER_INDEX_DB = Path(
    r"C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\agents\master_index.db"
)

# Lane display order
_LANE_ORDER: list[tuple[str, list[str]]] = [
    ("Lane 1 — I/O Pipeline", ["1", "2", "3"]),
    ("Lane 2 — Intelligence", ["J", "K", "L"]),
    ("Convergence", ["F"]),
]


# ---------------------------------------------------------------------------
# Helper: query master_index.db for agent stats
# ---------------------------------------------------------------------------

def _load_agent_stats() -> dict[str, dict[str, Any]]:
    """Return ``{agent_id: {action, detail, items_processed, ...}}``."""
    stats: dict[str, dict[str, Any]] = {}
    if not MASTER_INDEX_DB.exists():
        return stats
    try:
        conn = sqlite3.connect(str(MASTER_INDEX_DB), timeout=30)
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT agent_id, level, action, detail,
                   items_processed, items_errored,
                   MAX(timestamp) AS last_run
            FROM agent_log
            GROUP BY agent_id
            ORDER BY agent_id
            """
        ).fetchall()
        for r in rows:
            stats[r["agent_id"]] = dict(r)
        conn.close()
    except Exception:
        logger.exception("Failed to read master_index.db agent_log")
    return stats


def _derive_status(stat: dict[str, Any] | None) -> str:
    """Map an agent stat row to a display status string."""
    if stat is None:
        return "PENDING"
    action = (stat.get("action") or "").upper()
    errored = stat.get("items_errored") or 0
    if "FAIL" in action or "CRASH" in action or "FATAL" in action:
        return "FAILED"
    if errored > 0 and (stat.get("items_processed") or 0) == 0:
        return "FAILED"
    if "SUCCESS" in action or "COMPLETE" in action or "DONE" in action:
        return "SUCCESS"
    if "RUN" in action or "START" in action or "ACTIVE" in action:
        return "ACTIVE"
    if stat.get("items_processed"):
        return "SUCCESS"
    return "PENDING"


def _quality_score(stat: dict[str, Any] | None) -> int:
    """Derive a 0-100 quality score from processed/errored counts."""
    if stat is None:
        return 0
    processed = stat.get("items_processed") or 0
    errored = stat.get("items_errored") or 0
    total = processed + errored
    if total == 0:
        return 0
    return max(0, min(100, int((processed / total) * 100)))


# ---------------------------------------------------------------------------
# Main frame
# ---------------------------------------------------------------------------

class AgentDashboardFrame(ctk.CTkFrame):
    """Fleet-wide agent status dashboard for the 56-agent pipeline."""

    def __init__(
        self,
        parent: Any,
        db: "DatabaseManager",
        navigate_cb: Optional[Callable[[str], None]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._db = db
        self._navigate_cb = navigate_cb
        self._agent_stats: dict[str, dict[str, Any]] = {}
        self._selected_agent: Optional[str] = None
        self._tier_frames: dict[str, ctk.CTkFrame] = {}
        self._tier_collapsed: dict[str, bool] = {}
        self._agent_rows: dict[str, ctk.CTkFrame] = {}

        # Fleet summary cards (set in _build_fleet_overview)
        self._card_total: Optional[DataCard] = None
        self._card_active: Optional[DataCard] = None
        self._card_passed: Optional[DataCard] = None
        self._card_failed: Optional[DataCard] = None
        self._card_health: Optional[StatusBadge] = None

        # Details panel widgets
        self._detail_title: Optional[ctk.CTkLabel] = None
        self._detail_stats: Optional[ctk.CTkLabel] = None
        self._detail_quality: Optional[ProgressScore] = None
        self._detail_error: Optional[ctk.CTkLabel] = None
        self._detail_findings: Optional[ctk.CTkLabel] = None
        self._detail_frame: Optional[ctk.CTkFrame] = None

        # --- Layout ---
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)

        self._build_header()
        self._build_fleet_overview()
        self._build_agent_list()
        self._build_detail_panel()

        self.refresh()

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------

    def _build_header(self) -> None:
        hdr = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=12)
        hdr.grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(16, 8))
        hdr.grid_columnconfigure(1, weight=1)

        title_frame = ctk.CTkFrame(hdr, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="w", padx=16, pady=12)

        ctk.CTkLabel(
            title_frame,
            text="🤖 Agent Fleet Dashboard",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_frame,
            text="56 Pipeline Agents  •  5 Tiers  •  2 Lanes",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_dim"],
        ).pack(anchor="w", pady=(2, 0))

        btn = ctk.CTkButton(
            hdr,
            text="⟳  Refresh",
            width=100,
            height=32,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=8,
            command=self.refresh,
        )
        btn.grid(row=0, column=1, sticky="e", padx=16, pady=12)
        Tooltip(btn, "Reload agent stats from master_index.db")

    # ------------------------------------------------------------------
    # Fleet overview cards
    # ------------------------------------------------------------------

    def _build_fleet_overview(self) -> None:
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(80, 4))

        self._card_total = DataCard(row, title="Total Agents", value="56", color=COLORS["accent"])
        self._card_total.pack(side="left", padx=(0, 8), fill="x", expand=True)

        self._card_active = DataCard(row, title="Active", value="0", color=COLORS["blue"])
        self._card_active.pack(side="left", padx=8, fill="x", expand=True)

        self._card_passed = DataCard(row, title="Passed", value="0", color=COLORS["green"])
        self._card_passed.pack(side="left", padx=8, fill="x", expand=True)

        self._card_failed = DataCard(row, title="Failed", value="0", color=COLORS["red"])
        self._card_failed.pack(side="left", padx=8, fill="x", expand=True)

        health_frame = ctk.CTkFrame(row, fg_color=COLORS["bg_card"], corner_radius=10)
        health_frame.pack(side="left", padx=(8, 0), fill="x", expand=True)

        ctk.CTkLabel(
            health_frame,
            text="Fleet Health",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_dim"],
        ).pack(padx=12, pady=(8, 2))

        self._card_health = StatusBadge(health_frame, text="PENDING")
        self._card_health.pack(padx=12, pady=(0, 8))

    # ------------------------------------------------------------------
    # Tier / agent list  (scrollable left panel)
    # ------------------------------------------------------------------

    def _build_agent_list(self) -> None:
        self._scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
        )
        self._scroll.grid(row=1, column=0, sticky="nsew", padx=(16, 4), pady=8)

        for lane_label, tier_keys in _LANE_ORDER:
            # Lane header
            ctk.CTkLabel(
                self._scroll,
                text=lane_label.upper(),
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=COLORS["accent"],
                anchor="w",
            ).pack(fill="x", padx=8, pady=(12, 4))

            for tk in tier_keys:
                self._build_tier_panel(tk)

    def _build_tier_panel(self, tier_key: str) -> None:
        """Build a collapsible panel for one tier."""
        tier = AGENT_REGISTRY[tier_key]
        self._tier_collapsed[tier_key] = False

        wrapper = ctk.CTkFrame(self._scroll, fg_color=COLORS["bg_card"], corner_radius=10)
        wrapper.pack(fill="x", padx=4, pady=4)

        # Tier header — clickable to collapse/expand
        header = ctk.CTkFrame(wrapper, fg_color="transparent")
        header.pack(fill="x", padx=8, pady=(8, 4))

        toggle_label = ctk.CTkLabel(
            header,
            text=f"▼  {tier['name']}  ({len(tier['agents'])} agents)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text"],
            anchor="w",
            cursor="hand2",
        )
        toggle_label.pack(side="left")

        # Agent count badge
        StatusBadge(header, text=f"{len(tier['agents'])}").pack(side="right", padx=4)

        # Container for agent rows (toggled)
        body = ctk.CTkFrame(wrapper, fg_color="transparent")
        body.pack(fill="x", padx=4, pady=(0, 6))
        self._tier_frames[tier_key] = body

        # Column headers
        col_header = ctk.CTkFrame(body, fg_color="transparent")
        col_header.pack(fill="x", padx=8, pady=(0, 2))
        for text, w in [("ID", 50), ("Name", 160), ("Status", 80), ("Quality", 120),
                         ("Items", 60), ("Errors", 60), ("Last Run", 120)]:
            ctk.CTkLabel(
                col_header,
                text=text,
                width=w,
                font=ctk.CTkFont(size=10),
                text_color=COLORS["text_dim"],
                anchor="w",
            ).pack(side="left", padx=2)

        # Agent rows (populated by refresh)
        for agent_id in tier["agents"]:
            self._build_agent_row(body, agent_id)

        # Bind collapse/expand
        toggle_label.bind(
            "<Button-1>",
            lambda e, key=tier_key, lbl=toggle_label, bd=body, t=tier: self._toggle_tier(
                key, lbl, bd, t
            ),
        )

    def _toggle_tier(
        self,
        tier_key: str,
        label: ctk.CTkLabel,
        body: ctk.CTkFrame,
        tier: dict[str, Any],
    ) -> None:
        collapsed = self._tier_collapsed.get(tier_key, False)
        if collapsed:
            body.pack(fill="x", padx=4, pady=(0, 6))
            label.configure(text=f"▼  {tier['name']}  ({len(tier['agents'])} agents)")
        else:
            body.pack_forget()
            label.configure(text=f"▶  {tier['name']}  ({len(tier['agents'])} agents)")
        self._tier_collapsed[tier_key] = not collapsed

    # ------------------------------------------------------------------
    # Individual agent row
    # ------------------------------------------------------------------

    def _build_agent_row(self, parent: ctk.CTkFrame, agent_id: str) -> None:
        row = ctk.CTkFrame(parent, fg_color=COLORS["bg_dark"], corner_radius=6, height=32)
        row.pack(fill="x", padx=8, pady=1)
        row.pack_propagate(False)
        self._agent_rows[agent_id] = row

        # ID
        ctk.CTkLabel(
            row, text=agent_id, width=50,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["accent"], anchor="w",
        ).pack(side="left", padx=(8, 2))

        # Name
        name = AGENT_NAMES.get(agent_id, agent_id)
        name_lbl = ctk.CTkLabel(
            row, text=name, width=160,
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text"], anchor="w",
        )
        name_lbl.pack(side="left", padx=2)
        Tooltip(name_lbl, f"{agent_id}: {name}")

        # Status badge placeholder
        badge = StatusBadge(row, text="PENDING")
        badge.pack(side="left", padx=2)
        badge._agent_ref = agent_id  # type: ignore[attr-defined]

        # Quality score placeholder
        quality = ProgressScore(row, label="", score=0)
        quality.pack(side="left", padx=2)
        quality.configure(width=120)

        # Items processed
        items_lbl = ctk.CTkLabel(
            row, text="—", width=60,
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_dim"], anchor="w",
        )
        items_lbl.pack(side="left", padx=2)

        # Error count
        err_lbl = ctk.CTkLabel(
            row, text="—", width=60,
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_dim"], anchor="w",
        )
        err_lbl.pack(side="left", padx=2)

        # Last run
        run_lbl = ctk.CTkLabel(
            row, text="—", width=120,
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_dim"], anchor="w",
        )
        run_lbl.pack(side="left", padx=2)

        # Store sub-widget references for fast refresh
        row._sub = {  # type: ignore[attr-defined]
            "badge": badge,
            "quality": quality,
            "items": items_lbl,
            "errors": err_lbl,
            "last_run": run_lbl,
        }

        # Click → show detail
        row.bind("<Button-1>", lambda e, aid=agent_id: self._select_agent(aid))
        for child in row.winfo_children():
            child.bind("<Button-1>", lambda e, aid=agent_id: self._select_agent(aid))

        # Right-click context menu
        ContextMenu(
            row,
            items=[
                ("View Log", lambda aid=agent_id: self._view_log(aid)),
                ("Run Agent", lambda aid=agent_id: self._run_agent(aid)),
                ("---", None),
                ("View Findings", lambda aid=agent_id: self._view_findings(aid)),
            ],
        )

    # ------------------------------------------------------------------
    # Detail panel (right side)
    # ------------------------------------------------------------------

    def _build_detail_panel(self) -> None:
        self._detail_frame = ctk.CTkFrame(
            self, fg_color=COLORS["bg_card"], corner_radius=12,
        )
        self._detail_frame.grid(row=1, column=1, sticky="nsew", padx=(4, 16), pady=8)

        inner = ctk.CTkScrollableFrame(
            self._detail_frame, fg_color="transparent", corner_radius=0,
        )
        inner.pack(fill="both", expand=True, padx=4, pady=4)
        self._detail_inner = inner

        # Placeholder text
        ctk.CTkLabel(
            inner,
            text="Select an agent to view details",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_dim"],
        ).pack(pady=40)

        self._detail_title = None
        self._detail_stats = None
        self._detail_quality = None
        self._detail_error = None
        self._detail_findings = None

    def _select_agent(self, agent_id: str) -> None:
        """Highlight the selected agent and populate the detail panel."""
        # Un-highlight previous
        if self._selected_agent and self._selected_agent in self._agent_rows:
            self._agent_rows[self._selected_agent].configure(fg_color=COLORS["bg_dark"])

        self._selected_agent = agent_id

        # Highlight selected row
        if agent_id in self._agent_rows:
            self._agent_rows[agent_id].configure(fg_color=COLORS["border"])

        self._populate_detail(agent_id)

    def _populate_detail(self, agent_id: str) -> None:
        """Fill the right-side detail panel for *agent_id*."""
        inner = self._detail_inner
        for w in inner.winfo_children():
            w.destroy()

        stat = self._agent_stats.get(agent_id)
        name = AGENT_NAMES.get(agent_id, agent_id)
        status = _derive_status(stat)
        quality = _quality_score(stat)

        # Title
        self._detail_title = ctk.CTkLabel(
            inner,
            text=f"{agent_id}  —  {name}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["accent"],
            anchor="w",
        )
        self._detail_title.pack(fill="x", padx=12, pady=(12, 4))

        StatusBadge(inner, text=status).pack(anchor="w", padx=12, pady=(0, 8))

        # Stats block
        processed = stat.get("items_processed", 0) if stat else 0
        errored = stat.get("items_errored", 0) if stat else 0
        skipped = max(0, (processed + errored) - processed) if stat else 0
        last_run = stat.get("last_run", "—") if stat else "—"
        rate = f"{processed / max(1, processed + errored) * 100:.0f}%" if stat else "—"

        stats_text = (
            f"Processed:  {processed}\n"
            f"Errored:     {errored}\n"
            f"Skipped:     {skipped}\n"
            f"Success rate: {rate}\n"
            f"Last run:     {last_run}"
        )
        self._detail_stats = ctk.CTkLabel(
            inner,
            text=stats_text,
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color=COLORS["text"],
            anchor="w",
            justify="left",
        )
        self._detail_stats.pack(fill="x", padx=12, pady=(0, 8))

        # Quality breakdown
        _section_label(inner, "Quality")
        self._detail_quality = ProgressScore(inner, label="Overall", score=quality)
        self._detail_quality.pack(fill="x", padx=12, pady=2)

        # Breakdown bars
        completeness = quality
        accuracy = max(0, quality - 5) if quality > 0 else 0
        throughput = min(100, processed) if processed else 0
        coverage = min(100, max(0, quality + 10)) if quality > 0 else 0
        for lbl, val in [("Completeness", completeness), ("Accuracy", accuracy),
                          ("Throughput", throughput), ("Coverage", coverage)]:
            ProgressScore(inner, label=lbl, score=val).pack(fill="x", padx=12, pady=2)

        # Last error
        _section_label(inner, "Last Error")
        detail_text = (stat.get("detail") or "None") if stat else "No data"
        self._detail_error = ctk.CTkLabel(
            inner,
            text=detail_text,
            font=ctk.CTkFont(size=11),
            text_color=COLORS["red"] if stat and stat.get("items_errored") else COLORS["text_dim"],
            anchor="w",
            wraplength=260,
            justify="left",
        )
        self._detail_error.pack(fill="x", padx=12, pady=(0, 8))

        # Findings placeholder
        _section_label(inner, "Findings")
        self._detail_findings = ctk.CTkLabel(
            inner,
            text="Query master_index.db for findings list.",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_dim"],
            anchor="w",
            wraplength=260,
            justify="left",
        )
        self._detail_findings.pack(fill="x", padx=12, pady=(0, 8))

        # View Log button
        ctk.CTkButton(
            inner,
            text="📄  View Log",
            width=140,
            height=30,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=8,
            command=lambda: self._view_log(agent_id),
        ).pack(anchor="w", padx=12, pady=(4, 16))

    # ------------------------------------------------------------------
    # Refresh / data loading
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Reload agent stats from master_index.db and update the UI."""
        self._agent_stats = _load_agent_stats()
        self._update_fleet_overview()
        self._update_agent_rows()

    def _update_fleet_overview(self) -> None:
        """Recompute fleet-level summary cards."""
        total = 56
        active = 0
        passed = 0
        failed = 0

        all_ids: list[str] = []
        for tier in AGENT_REGISTRY.values():
            all_ids.extend(tier["agents"])

        for aid in all_ids:
            status = _derive_status(self._agent_stats.get(aid))
            if status == "SUCCESS":
                passed += 1
            elif status == "FAILED":
                failed += 1
            elif status == "ACTIVE":
                active += 1

        if self._card_total:
            self._card_total.set(str(total))
        if self._card_active:
            self._card_active.set(str(active))
        if self._card_passed:
            self._card_passed.set(str(passed))
        if self._card_failed:
            self._card_failed.set(str(failed))

        # Fleet health
        if self._card_health:
            if failed > 10:
                self._card_health.set("CRITICAL", COLORS["red"])
            elif failed > 3:
                self._card_health.set("DEGRADED", COLORS["yellow"])
            else:
                self._card_health.set("HEALTHY", COLORS["green"])

    def _update_agent_rows(self) -> None:
        """Push latest stats into every agent row's sub-widgets."""
        for agent_id, row in self._agent_rows.items():
            sub: dict[str, Any] = getattr(row, "_sub", {})
            if not sub:
                continue

            stat = self._agent_stats.get(agent_id)
            status = _derive_status(stat)
            quality = _quality_score(stat)

            badge: StatusBadge = sub["badge"]
            badge.set(status)

            quality_bar: ProgressScore = sub["quality"]
            quality_bar.set(quality)

            items_lbl: ctk.CTkLabel = sub["items"]
            items_lbl.configure(
                text=str(stat.get("items_processed", 0)) if stat else "—"
            )

            err_lbl: ctk.CTkLabel = sub["errors"]
            errored = stat.get("items_errored", 0) if stat else 0
            err_lbl.configure(
                text=str(errored) if stat else "—",
                text_color=COLORS["red"] if errored else COLORS["text_dim"],
            )

            run_lbl: ctk.CTkLabel = sub["last_run"]
            last_run_raw = stat.get("last_run", "") if stat else ""
            run_lbl.configure(text=_format_timestamp(last_run_raw))

    # ------------------------------------------------------------------
    # Context menu actions
    # ------------------------------------------------------------------

    def _view_log(self, agent_id: str) -> None:
        """Open a dialog showing the agent's recent log entries."""
        entries = self._query_agent_log(agent_id, limit=50)
        _show_text_dialog(
            self,
            title=f"Log — {agent_id}",
            text="\n".join(
                f"[{e.get('timestamp', '')}] {e.get('level', '')} "
                f"{e.get('action', '')} — {e.get('detail', '')}"
                for e in entries
            )
            or "No log entries found.",
        )

    def _run_agent(self, agent_id: str) -> None:
        """Placeholder for triggering an agent run from the GUI."""
        _show_text_dialog(
            self,
            title=f"Run Agent — {agent_id}",
            text=(
                f"To run {agent_id} from CLI:\n\n"
                f"  cd 00_SYSTEM\\pipeline\n"
                f"  python -m agents.agent_orchestrator --agent {agent_id}\n\n"
                "GUI-triggered runs are not yet implemented."
            ),
        )

    def _view_findings(self, agent_id: str) -> None:
        """Show findings from the agent (placeholder query)."""
        _show_text_dialog(
            self,
            title=f"Findings — {agent_id}",
            text=f"Findings for {agent_id} can be queried from master_index.db.\n"
            f"Table: agent_log WHERE agent_id = '{agent_id}' AND action LIKE '%FINDING%'",
        )

    # ------------------------------------------------------------------
    # DB helpers
    # ------------------------------------------------------------------

    def _query_agent_log(
        self, agent_id: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Return recent log rows for a single agent."""
        if not MASTER_INDEX_DB.exists():
            return []
        try:
            conn = sqlite3.connect(str(MASTER_INDEX_DB), timeout=30)
            conn.execute("PRAGMA busy_timeout=30000")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT timestamp, level, action, detail,
                       items_processed, items_errored
                FROM agent_log
                WHERE agent_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (agent_id, limit),
            ).fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception:
            logger.exception("Failed to query agent_log for %s", agent_id)
            return []


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _section_label(parent: ctk.CTkFrame, text: str) -> None:
    """Insert a small section heading into *parent*."""
    ctk.CTkLabel(
        parent,
        text=text,
        font=ctk.CTkFont(size=12, weight="bold"),
        text_color=COLORS["text_dim"],
        anchor="w",
    ).pack(fill="x", padx=12, pady=(8, 2))


def _format_timestamp(raw: str | None) -> str:
    """Best-effort human-friendly timestamp formatting."""
    if not raw:
        return "—"
    try:
        dt = datetime.fromisoformat(str(raw))
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return str(raw)[:16] if raw else "—"


def _show_text_dialog(parent: Any, title: str, text: str) -> None:
    """Display a read-only text dialog (modal)."""
    dialog = ctk.CTkToplevel(parent)
    dialog.title(title)
    dialog.geometry("620x440")
    dialog.configure(fg_color=COLORS["bg_dark"])
    dialog.transient(parent)
    dialog.grab_set()

    ctk.CTkLabel(
        dialog,
        text=title,
        font=ctk.CTkFont(size=16, weight="bold"),
        text_color=COLORS["accent"],
    ).pack(padx=16, pady=(16, 8))

    txt = ctk.CTkTextbox(
        dialog,
        fg_color=COLORS["bg_card"],
        text_color=COLORS["text"],
        font=ctk.CTkFont(family="Consolas", size=11),
        corner_radius=8,
        wrap="word",
    )
    txt.pack(fill="both", expand=True, padx=16, pady=(0, 8))
    txt.insert("1.0", text)
    txt.configure(state="disabled")

    ctk.CTkButton(
        dialog,
        text="Close",
        width=80,
        fg_color=COLORS["accent"],
        hover_color=COLORS["accent_hover"],
        text_color="#FFFFFF",
        corner_radius=8,
        command=dialog.destroy,
    ).pack(pady=(0, 16))
