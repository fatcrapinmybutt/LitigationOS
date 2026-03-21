"""Dashboard screen — main command center for LitigationOS.

Displays a comprehensive overview with:
- Alert banner for EMERGENCY/CRITICAL deadlines
- Case overview with lane assignments and status indicators
- Filing readiness scores (progress bars, colour-coded)
- Deadline panel with urgency indicators (red/yellow/green)
- Evidence summary per lane with strength scores
- Quick-action buttons: New Case, Add Evidence, Generate Filing, Run QA

Wired to ALL engines: DeadlineEngine, FilingEngine, EvidenceEngine,
CourtRulesEngine, DocumentEngine.
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import TYPE_CHECKING, Callable, Optional

import customtkinter as ctk

from litigationos.gui.widgets import (
    COLORS,
    PRIORITY_COLORS,
    STATUS_COLORS,
    DataCard,
    DeadlineRow,
    ProgressScore,
    StatusBadge,
)

if TYPE_CHECKING:
    from litigationos.db.connection import DatabaseManager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lane definitions (mirrors the six case lanes from COPILOT_INSTRUCTIONS)
# ---------------------------------------------------------------------------

LANE_META: dict[str, dict[str, str]] = {
    "A": {"label": "Custody",     "icon": "👶", "color": COLORS["blue"]},
    "B": {"label": "Housing",     "icon": "🏠", "color": COLORS["green"]},
    "C": {"label": "Convergence", "icon": "🔗", "color": COLORS["yellow"]},
    "D": {"label": "PPO",         "icon": "🛡", "color": COLORS["orange"]},
    "E": {"label": "Misconduct",  "icon": "⚖",  "color": COLORS["red"]},
    "F": {"label": "Appellate",   "icon": "📜", "color": COLORS["accent"]},
}

_LANE_CASE_TYPES: dict[str, str] = {
    "family":    "A",
    "civil":     "B",
    "criminal":  "D",
    "appellate": "F",
    "federal":   "E",
}

# ---------------------------------------------------------------------------
# Engine imports — graceful fallback for each
# ---------------------------------------------------------------------------

try:
    from litigationos.engines.deadline import DeadlineEngine
    _HAS_DEADLINE_ENGINE = True
except ImportError:
    _HAS_DEADLINE_ENGINE = False

try:
    from litigationos.engines.filing import FilingEngine
    _HAS_FILING_ENGINE = True
except ImportError:
    _HAS_FILING_ENGINE = False

try:
    from litigationos.engines.evidence import EvidenceEngine
    _HAS_EVIDENCE_ENGINE = True
except ImportError:
    _HAS_EVIDENCE_ENGINE = False

try:
    from litigationos.engines.court_rules import CourtRulesEngine
    _HAS_RULES_ENGINE = True
except ImportError:
    _HAS_RULES_ENGINE = False

# Litigation DB bridge — read-only access to litigation_context.db
try:
    from litigationos.db.litigation_bridge import LitigationBridge
    _HAS_BRIDGE = True
except ImportError:
    _HAS_BRIDGE = False


# ===================================================================
# DashboardFrame
# ===================================================================

class DashboardFrame(ctk.CTkFrame):
    """Main command-centre dashboard with alerts, cases, filings,
    deadlines, evidence summary, and quick-action buttons."""

    def __init__(
        self,
        parent,
        db: "DatabaseManager",
        navigate_cb: Optional[Callable[[str], None]] = None,
        **kwargs,
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._db = db
        self._navigate_cb = navigate_cb
        self._bridge: Optional[LitigationBridge] = None
        self._init_bridge()

        # --- scrollable container ---
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0,
        )
        self._scroll.pack(fill="both", expand=True)

        # --- build layout sections (top → bottom) ---
        self._build_header()
        self._alert_container = self._build_section("🚨  ALERTS")
        self._deadline_container = self._build_section("⏰  DEADLINE ALERTS")
        self._build_body()                          # cases + filings (2-col)
        self._build_evidence_panel()                # evidence summary per lane
        self._build_quick_actions()                 # action buttons
        self._stats_container = self._build_section("📊  QUICK STATS")

        # Widget lists cleared/rebuilt on every refresh
        self._deadline_widgets: list[ctk.CTkBaseClass] = []
        self._case_widgets: list[ctk.CTkBaseClass] = []
        self._filing_widgets: list[ctk.CTkBaseClass] = []
        self._stat_cards: list[DataCard] = []

        self.refresh()

    # ------------------------------------------------------------------
    # Bridge to litigation_context.db
    # ------------------------------------------------------------------

    def _init_bridge(self) -> None:
        """Create bridge to the real litigation DB if available."""
        if not _HAS_BRIDGE:
            return
        try:
            db_path = self._db.db_path if self._db else None
            self._bridge = LitigationBridge(db_path)
            if self._bridge.is_real_db:
                logger.info("LitigationBridge connected to real DB")
            else:
                self._bridge = None
        except Exception:
            self._bridge = None

    # ------------------------------------------------------------------
    # Layout helpers
    # ------------------------------------------------------------------

    def _build_header(self) -> None:
        hdr = ctk.CTkFrame(self._scroll, fg_color=COLORS["bg_card"], corner_radius=12)
        hdr.pack(fill="x", padx=16, pady=(16, 8))

        ctk.CTkLabel(
            hdr,
            text="⚖  LITIGATION COMMAND CENTER",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS["text"],
        ).pack(side="left", padx=16, pady=12)

        ctk.CTkLabel(
            hdr,
            text=datetime.now().strftime("%A, %B %d, %Y"),
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_dim"],
        ).pack(side="right", padx=16, pady=12)

        ctk.CTkButton(
            hdr,
            text="⟳  Refresh",
            width=100,
            command=self.refresh,
            fg_color=COLORS["blue"],
            hover_color=COLORS["accent"],
            corner_radius=8,
        ).pack(side="right", padx=(0, 8), pady=12)

    def _build_section(self, title: str) -> ctk.CTkFrame:
        """Create a titled section and return its inner content frame."""
        wrapper = ctk.CTkFrame(self._scroll, fg_color="transparent")
        wrapper.pack(fill="x", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            wrapper,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_dim"],
            anchor="w",
        ).pack(anchor="w")

        container = ctk.CTkFrame(wrapper, fg_color="transparent")
        container.pack(fill="x", pady=(4, 0))
        return container

    # --- two-column body: cases | filings ---

    def _build_body(self) -> None:
        """Build the two-column body (cases left, filings right)."""
        body = ctk.CTkFrame(self._scroll, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=4)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)

        # Left — Case overview with lane badges
        left = ctk.CTkFrame(body, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        ctk.CTkLabel(
            left,
            text="📁  ACTIVE CASES",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_dim"],
            anchor="w",
        ).pack(anchor="w", pady=(0, 4))

        self._cases_frame = ctk.CTkScrollableFrame(
            left, fg_color=COLORS["bg_card"], corner_radius=10, height=260,
        )
        self._cases_frame.pack(fill="both", expand=True)

        # Right — Filing readiness
        right = ctk.CTkFrame(body, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        ctk.CTkLabel(
            right,
            text="📄  FILING READINESS",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_dim"],
            anchor="w",
        ).pack(anchor="w", pady=(0, 4))

        self._filings_frame = ctk.CTkScrollableFrame(
            right, fg_color=COLORS["bg_card"], corner_radius=10, height=260,
        )
        self._filings_frame.pack(fill="both", expand=True)

    # --- evidence summary panel ---

    def _build_evidence_panel(self) -> None:
        """Build the per-lane evidence summary section."""
        wrapper = ctk.CTkFrame(self._scroll, fg_color="transparent")
        wrapper.pack(fill="x", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            wrapper,
            text="🔬  EVIDENCE SUMMARY",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_dim"],
            anchor="w",
        ).pack(anchor="w")

        self._evidence_frame = ctk.CTkFrame(
            wrapper, fg_color="transparent",
        )
        self._evidence_frame.pack(fill="x", pady=(4, 0))

    # --- quick-action buttons ---

    def _build_quick_actions(self) -> None:
        """Build the quick-action button bar."""
        wrapper = ctk.CTkFrame(self._scroll, fg_color="transparent")
        wrapper.pack(fill="x", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            wrapper,
            text="⚡  QUICK ACTIONS",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_dim"],
            anchor="w",
        ).pack(anchor="w", pady=(0, 4))

        btn_bar = ctk.CTkFrame(
            wrapper, fg_color=COLORS["bg_card"], corner_radius=10,
        )
        btn_bar.pack(fill="x", pady=(4, 0))
        btn_bar.columnconfigure((0, 1, 2, 3), weight=1)

        actions: list[tuple[str, str, str, str]] = [
            ("📁  New Case",        COLORS["blue"],   "cases",        "new_case"),
            ("📎  Add Evidence",    COLORS["green"],  "evidence",     "add_evidence"),
            ("📄  Generate Filing", COLORS["orange"], "filing_wizard", "gen_filing"),
            ("✅  Run QA",          COLORS["red"],    "filings",      "run_qa"),
        ]

        for col, (text, color, screen, action_id) in enumerate(actions):
            ctk.CTkButton(
                btn_bar,
                text=text,
                fg_color=color,
                hover_color=COLORS["accent"],
                corner_radius=8,
                height=40,
                font=ctk.CTkFont(size=13, weight="bold"),
                command=lambda s=screen: self._on_quick_action(s),
            ).grid(row=0, column=col, sticky="ew", padx=8, pady=10)

    def _on_quick_action(self, screen_name: str) -> None:
        """Navigate to the target screen via the app's switch callback."""
        if self._navigate_cb:
            self._navigate_cb(screen_name)

    # ------------------------------------------------------------------
    # Public refresh methods (callable individually)
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Reload *all* dashboard data from the database."""
        self._load_alerts()
        self.refresh_deadlines()
        self.refresh_cases()
        self.refresh_filings()
        self._load_evidence_summary()
        self._load_stats()

    def refresh_cases(self) -> None:
        """Reload case data into the case overview panel."""
        self._load_cases()

    def refresh_deadlines(self) -> None:
        """Reload deadline data into the deadline panel."""
        self._load_deadlines()

    def refresh_filings(self) -> None:
        """Reload filing status into the filing readiness panel."""
        self._load_filings()

    # ------------------------------------------------------------------
    # Internal data loaders
    # ------------------------------------------------------------------

    def _clear_container(self, container: ctk.CTkFrame) -> None:
        for w in container.winfo_children():
            w.destroy()

    # --- alerts ---

    def _load_alerts(self) -> None:
        """Show alert banner for EMERGENCY/CRITICAL deadlines from bridge or engine."""
        self._clear_container(self._alert_container)

        critical_deadlines: list[dict] = []

        # --- Bridge path: check real deadlines ---
        if self._bridge:
            bridge_rows = self._bridge.get_deadlines(status="pending")
            for d in bridge_rows:
                due_str = d.get("due_date", "")
                try:
                    due = date.fromisoformat(due_str)
                    days = (due - date.today()).days
                except (ValueError, TypeError):
                    continue
                if days < 0:
                    d["_urgency"] = "OVERDUE"
                    critical_deadlines.append(d)
                elif days <= 3:
                    d["_urgency"] = "EMERGENCY"
                    critical_deadlines.append(d)
                elif days <= 7:
                    urg = d.get("urgency", "")
                    if urg in ("critical", "high", "CRITICAL", "HIGH"):
                        d["_urgency"] = "CRITICAL"
                        critical_deadlines.append(d)
        elif _HAS_DEADLINE_ENGINE and self._db:
            try:
                engine = DeadlineEngine(self._db)
                overdue = engine.get_overdue()
                upcoming = engine.get_upcoming(days=7)
                for d in overdue:
                    d["_urgency"] = "OVERDUE"
                    critical_deadlines.append(d)
                for d in upcoming:
                    try:
                        due = date.fromisoformat(d.get("due_date", ""))
                        days = (due - date.today()).days
                    except (ValueError, TypeError):
                        days = 999
                    if days <= 3:
                        d["_urgency"] = "EMERGENCY"
                        critical_deadlines.append(d)
                    elif days <= 7 and d.get("priority") in ("critical", "high"):
                        d["_urgency"] = "CRITICAL"
                        critical_deadlines.append(d)
            except Exception:
                logger.debug("DeadlineEngine alert check failed")

        if not critical_deadlines:
            return

        banner = ctk.CTkFrame(
            self._alert_container, fg_color=COLORS["red"], corner_radius=8,
        )
        banner.pack(fill="x", pady=4)

        ctk.CTkLabel(
            banner,
            text=f"⚠  {len(critical_deadlines)} URGENT DEADLINE(S) REQUIRE ATTENTION",
            font=ctk.CTkFont(size=14, weight="bold"), text_color="#ffffff",
        ).pack(padx=12, pady=(8, 2))

        for d in critical_deadlines[:5]:
            urgency = d.get("_urgency", "CRITICAL")
            title = d.get("title", "Deadline")
            due = d.get("due_date", "")
            ctk.CTkLabel(
                banner,
                text=f"  [{urgency}] {title} — Due: {due}",
                font=ctk.CTkFont(size=12), text_color="#ffffff",
            ).pack(anchor="w", padx=16, pady=1)

        ctk.CTkLabel(banner, text="", height=4).pack()  # spacer

    # --- deadlines ---

    def _load_deadlines(self) -> None:
        self._clear_container(self._deadline_container)

        rows: list[dict] = []

        # --- Bridge path: real deadlines from litigation_context.db ---
        if self._bridge:
            bridge_rows = self._bridge.get_deadlines(status="pending", limit=5)
            if bridge_rows:
                rows = bridge_rows

        # --- Engine path ---
        if not rows and _HAS_DEADLINE_ENGINE and self._db:
            try:
                engine = DeadlineEngine(self._db)
                upcoming = engine.get_upcoming(days=30)
                rows = upcoming[:5]
            except Exception:
                logger.debug("DeadlineEngine upcoming load failed; falling back to raw DB")

        if not rows:
            try:
                rows_raw = self._db.fetchall(
                    "SELECT d.*, c.title AS case_title FROM deadlines d "
                    "LEFT JOIN cases c ON d.case_id = c.id "
                    "WHERE d.status = 'pending' AND d.due_date >= date('now') "
                    "ORDER BY d.due_date ASC LIMIT 5",
                )
                rows = [dict(r) for r in rows_raw]
            except Exception:
                logger.exception("Failed to load deadlines")

        if not rows:
            ctk.CTkLabel(
                self._deadline_container,
                text="No upcoming deadlines",
                text_color=COLORS["text_dim"],
                font=ctk.CTkFont(size=12),
            ).pack(pady=8)
            return

        for d in rows:
            if not isinstance(d, dict):
                d = dict(d)
            try:
                due = date.fromisoformat(d["due_date"])
                days_remaining = (due - date.today()).days
            except (ValueError, TypeError, KeyError):
                days_remaining = 999

            label = d.get("title") or "Deadline"
            case_title = d.get("case_title")
            if case_title:
                label = f"{label}  —  {case_title}"

            DeadlineRow(
                self._deadline_container,
                title=label,
                due_date=d.get("due_date", ""),
                priority=d.get("priority", "medium"),
                days_remaining=days_remaining,
            ).pack(fill="x", pady=2)

    # --- cases (with lane assignment) ---

    @staticmethod
    def _detect_lane(case: dict) -> str:
        """Determine the lane letter for a case based on its type/number."""
        case_type = (case.get("case_type") or "").lower()
        if case_type in _LANE_CASE_TYPES:
            return _LANE_CASE_TYPES[case_type]

        case_num = (case.get("case_number") or "").upper()
        if "PP" in case_num:
            return "D"
        if "CZ" in case_num:
            return "B"
        if "DC" in case_num:
            return "A"
        return "C"

    def _load_cases(self) -> None:
        self._clear_container(self._cases_frame)

        # --- Bridge path: synthesize cases from real litigation DB ---
        if self._bridge:
            cases = self._bridge.get_active_cases()
            if cases:
                for c in cases:
                    lane = c.get("lane", "C")
                    meta = LANE_META.get(lane, LANE_META["C"])
                    frame = ctk.CTkFrame(self._cases_frame, fg_color="transparent")
                    frame.pack(fill="x", pady=2, padx=4)

                    lane_badge = ctk.CTkFrame(frame, fg_color=meta["color"], corner_radius=4, width=28)
                    lane_badge.pack(side="left", padx=(0, 6), pady=2)
                    lane_badge.pack_propagate(False)
                    ctk.CTkLabel(
                        lane_badge, text=meta["icon"], font=ctk.CTkFont(size=12), width=28,
                    ).pack(expand=True)

                    case_label = f"{c.get('case_number', '')}  {c.get('case_type', '')}"
                    btn = ctk.CTkButton(
                        frame, text=case_label, anchor="w",
                        fg_color="transparent", hover_color=COLORS["bg_sidebar"],
                        text_color=COLORS["text"], font=ctk.CTkFont(size=13),
                        command=lambda: self._on_case_click(0),
                    )
                    btn.pack(side="left", fill="x", expand=True)

                    ctk.CTkLabel(
                        frame, text=f"Lane {lane}",
                        font=ctk.CTkFont(size=10), text_color=meta["color"],
                    ).pack(side="right", padx=(0, 4))

                    activity = c.get("last_activity", "")
                    evts = c.get("event_count", 0)
                    ctk.CTkLabel(
                        frame, text=f"{evts} events · {activity}",
                        font=ctk.CTkFont(size=10), text_color=COLORS["text_dim"],
                    ).pack(side="right", padx=4)
                return

        # --- Fallback: app-schema cases table ---
        try:
            rows = self._db.fetchall(
                "SELECT id, case_number, title, case_type, status, updated_at "
                "FROM cases WHERE status = 'active' "
                "ORDER BY updated_at DESC LIMIT 20",
            )
        except Exception:
            logger.exception("Failed to load cases")
            rows = []

        if not rows:
            ctk.CTkLabel(
                self._cases_frame,
                text="No active cases",
                text_color=COLORS["text_dim"],
            ).pack(pady=20)
            return

        for row in rows:
            c = dict(row)
            case_id = c["id"]
            lane = self._detect_lane(c)
            meta = LANE_META.get(lane, LANE_META["C"])

            frame = ctk.CTkFrame(self._cases_frame, fg_color="transparent")
            frame.pack(fill="x", pady=2, padx=4)

            # Lane indicator badge
            lane_badge = ctk.CTkFrame(frame, fg_color=meta["color"], corner_radius=4, width=28)
            lane_badge.pack(side="left", padx=(0, 6), pady=2)
            lane_badge.pack_propagate(False)
            ctk.CTkLabel(
                lane_badge,
                text=meta["icon"],
                font=ctk.CTkFont(size=12),
                width=28,
            ).pack(expand=True)

            # Case button
            case_label = f"{c.get('case_number', '')}  {c['title']}"
            btn = ctk.CTkButton(
                frame,
                text=case_label,
                anchor="w",
                fg_color="transparent",
                hover_color=COLORS["bg_sidebar"],
                text_color=COLORS["text"],
                font=ctk.CTkFont(size=13),
                command=lambda cid=case_id: self._on_case_click(cid),
            )
            btn.pack(side="left", fill="x", expand=True)

            # Lane letter + status
            ctk.CTkLabel(
                frame,
                text=f"Lane {lane}",
                font=ctk.CTkFont(size=10),
                text_color=meta["color"],
            ).pack(side="right", padx=(0, 4))

            StatusBadge(frame, text=c.get("status", "active")).pack(
                side="right", padx=4,
            )

    def _on_case_click(self, case_id: int) -> None:
        if self._navigate_cb:
            self._navigate_cb("cases")

    # --- filings ---

    def _load_filings(self) -> None:
        self._clear_container(self._filings_frame)

        # --- Bridge path: show recent docket events as filing activity ---
        if self._bridge:
            events = self._bridge.get_recent_docket_events(limit=10)
            if events:
                for ev in events:
                    desc = ev.get("description", "")
                    ev_type = ev.get("event_type", "")
                    case_num = ev.get("case_number", "")
                    ev_date = ev.get("event_date", "")
                    label = f"[{ev_type.upper()}]  {desc[:60]}"
                    if case_num:
                        label += f"  ({case_num})"

                    row = ctk.CTkFrame(self._filings_frame, fg_color="transparent")
                    row.pack(fill="x", pady=2, padx=4)
                    ctk.CTkLabel(
                        row, text=label, anchor="w",
                        font=ctk.CTkFont(size=12), text_color=COLORS["text"],
                    ).pack(side="left", fill="x", expand=True)
                    ctk.CTkLabel(
                        row, text=ev_date,
                        font=ctk.CTkFont(size=10), text_color=COLORS["text_dim"],
                    ).pack(side="right", padx=4)
                return

        # --- Fallback: app-schema filings table ---
        try:
            rows = self._db.fetchall(
                "SELECT id, title, filing_type, status, compliance_score "
                "FROM filings WHERE status NOT IN ('filed', 'served') "
                "ORDER BY created_at DESC LIMIT 10",
            )
        except Exception:
            logger.exception("Failed to load filings")
            rows = []

        if not rows:
            ctk.CTkLabel(
                self._filings_frame,
                text="No pending filings",
                text_color=COLORS["text_dim"],
            ).pack(pady=20)
            return

        filing_engine = None
        if _HAS_FILING_ENGINE and self._db:
            try:
                filing_engine = FilingEngine(self._db)
            except Exception:
                pass

        for row in rows:
            f = dict(row)
            score = int(f.get("compliance_score") or 0)

            if score == 0 and filing_engine:
                try:
                    score = filing_engine.score_filing(f["id"])
                except Exception:
                    pass

            status = f.get("status", "draft")
            label = f.get("title") or f.get("filing_type", "Filing")
            display = f"[{status.upper()}]  {label}"

            ProgressScore(
                self._filings_frame, label=display, score=score,
            ).pack(fill="x", pady=2, padx=4)

    # --- evidence summary (per lane) ---

    def _load_evidence_summary(self) -> None:
        """Load evidence counts grouped by lane with optional strength scores."""
        self._clear_container(self._evidence_frame)

        # Gather per-lane evidence data
        lane_counts: dict[str, int] = {k: 0 for k in LANE_META}
        lane_strength: dict[str, list[float]] = {k: [] for k in LANE_META}

        # --- Bridge path: real evidence_quotes data ---
        if self._bridge:
            by_lane = self._bridge.get_evidence_by_lane()
            if by_lane:
                for lane_key, data in by_lane.items():
                    if lane_key in lane_counts:
                        lane_counts[lane_key] = data["count"]
                        avg = data.get("avg_score", 0)
                        if avg:
                            lane_strength[lane_key] = [float(avg)]
            # Fall through to rendering below
        else:
            # --- Fallback: app-schema evidence + cases tables ---
            try:
                rows = self._db.fetchall(
                    "SELECT e.case_id, e.relevance_score, c.case_type, c.case_number "
                    "FROM evidence e "
                    "LEFT JOIN cases c ON e.case_id = c.id "
                    "WHERE c.status = 'active'",
                )
            except Exception:
                logger.debug("Evidence summary query failed")
                rows = []

            for row in rows:
                r = dict(row)
                lane = self._detect_lane(r)
                lane_counts[lane] = lane_counts.get(lane, 0) + 1
                score = r.get("relevance_score")
                if score is not None:
                    lane_strength.setdefault(lane, []).append(float(score))

        # Build grid — one card per lane
        grid = ctk.CTkFrame(self._evidence_frame, fg_color="transparent")
        grid.pack(fill="x")

        active_lanes = [k for k in LANE_META if lane_counts.get(k, 0) > 0]
        if not active_lanes:
            active_lanes = list(LANE_META.keys())

        cols = min(len(active_lanes), 6)
        for i in range(cols):
            grid.columnconfigure(i, weight=1)

        for col, lane in enumerate(active_lanes[:6]):
            meta = LANE_META[lane]
            count = lane_counts.get(lane, 0)
            scores = lane_strength.get(lane, [])
            avg = int(sum(scores) / len(scores)) if scores else 0

            card = ctk.CTkFrame(grid, fg_color=COLORS["bg_card"], corner_radius=10)
            card.grid(row=0, column=col, sticky="nsew", padx=4, pady=4)

            # Lane header strip
            strip = ctk.CTkFrame(card, fg_color=meta["color"], height=4, corner_radius=2)
            strip.pack(fill="x", padx=6, pady=(6, 2))

            ctk.CTkLabel(
                card,
                text=f"{meta['icon']}  Lane {lane}: {meta['label']}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=COLORS["text"],
            ).pack(padx=8, pady=(4, 0))

            ctk.CTkLabel(
                card,
                text=f"{count} item{'s' if count != 1 else ''}",
                font=ctk.CTkFont(size=20, weight="bold"),
                text_color=meta["color"],
            ).pack(padx=8, pady=(2, 0))

            # Strength score bar
            if avg >= 80:
                bar_color = COLORS["green"]
            elif avg >= 50:
                bar_color = COLORS["yellow"]
            else:
                bar_color = COLORS["red"]

            strength_label = f"Strength: {avg}%" if avg else "No scores"
            ctk.CTkLabel(
                card,
                text=strength_label,
                font=ctk.CTkFont(size=10),
                text_color=COLORS["text_dim"],
            ).pack(padx=8, pady=(0, 2))

            bar = ctk.CTkProgressBar(
                card,
                progress_color=bar_color,
                fg_color=COLORS["border"],
                height=6,
                corner_radius=3,
            )
            bar.pack(fill="x", padx=10, pady=(0, 8))
            bar.set(avg / 100.0 if avg else 0)

    # --- quick stats ---

    def _load_stats(self) -> None:
        self._clear_container(self._stats_container)

        def _count(sql: str) -> int:
            try:
                row = self._db.fetchone(sql)
                return row[0] if row else 0
            except Exception:
                return 0

        # --- Bridge path: real litigation DB stats ---
        if self._bridge:
            stats = self._bridge.get_dashboard_stats()
            if stats:
                evidence = stats.get("evidence_count", 0)
                documents = stats.get("document_count", 0)
                violations = stats.get("violation_count", 0)
                docket = stats.get("docket_count", 0)
                files = stats.get("file_count", 0)
                pending = stats.get("deadline_count", 0)
                next_date = stats.get("next_deadline_date")

                next_deadline_days = None
                if next_date:
                    try:
                        nxt = date.fromisoformat(next_date)
                        next_deadline_days = (nxt - date.today()).days
                    except (ValueError, TypeError):
                        pass

                row_frame = ctk.CTkFrame(self._stats_container, fg_color="transparent")
                row_frame.pack(fill="x")

                # Build two rows of stat cards for the full arsenal
                # Row 1: Core counts
                row_frame.columnconfigure((0, 1, 2, 3), weight=1)

                if next_deadline_days is not None:
                    dl_value = f"{next_deadline_days}d"
                    dl_title = f"Next Deadline ({pending} pending)"
                    dl_color = COLORS["red"] if next_deadline_days <= 7 else COLORS["orange"]
                else:
                    dl_value = str(pending)
                    dl_title = "Pending Deadlines"
                    dl_color = COLORS["orange"]

                cards_r1: list[tuple[str, str | int, str]] = [
                    (dl_title, dl_value, dl_color),
                    ("Evidence Quotes", f"{evidence:,}", COLORS["yellow"]),
                    ("Documents", f"{documents:,}", COLORS["green"]),
                    ("Judicial Violations", f"{violations:,}", COLORS["red"]),
                ]
                for i, (title, value, color) in enumerate(cards_r1):
                    card = DataCard(row_frame, title=title, value=value, color=color)
                    card.grid(row=0, column=i, sticky="nsew", padx=6, pady=6)
                    self._stat_cards.append(card)

                # Row 2: Additional arsenal
                row2 = ctk.CTkFrame(self._stats_container, fg_color="transparent")
                row2.pack(fill="x")
                row2.columnconfigure((0, 1, 2), weight=1)

                file_display = f"{files:,}" if files < 1_000_000 else f"{files // 1000}K"
                cards_r2: list[tuple[str, str | int, str]] = [
                    ("Docket Events", f"{docket:,}", COLORS["blue"]),
                    ("Files Inventoried", file_display, COLORS["accent"]),
                    ("Litigation Arsenal", f"{evidence + documents + violations:,}", COLORS["green"]),
                ]
                for i, (title, value, color) in enumerate(cards_r2):
                    card = DataCard(row2, title=title, value=value, color=color)
                    card.grid(row=0, column=i, sticky="nsew", padx=6, pady=6)
                    self._stat_cards.append(card)
                return

        # --- Fallback: app-schema tables ---
        cases = _count("SELECT COUNT(*) FROM cases")
        filings = _count("SELECT COUNT(*) FROM filings")
        evidence = _count("SELECT COUNT(*) FROM evidence")

        # Engine-backed deadline countdown
        pending = 0
        next_deadline_days = None
        if _HAS_DEADLINE_ENGINE and self._db:
            try:
                engine = DeadlineEngine(self._db)
                upcoming = engine.get_upcoming(days=90)
                pending = len(upcoming)
                if upcoming:
                    try:
                        first_due = date.fromisoformat(upcoming[0].get("due_date", ""))
                        next_deadline_days = (first_due - date.today()).days
                    except (ValueError, TypeError):
                        pass
            except Exception:
                pending = _count(
                    "SELECT COUNT(*) FROM deadlines WHERE status='pending' AND due_date >= date('now')",
                )
        else:
            pending = _count(
                "SELECT COUNT(*) FROM deadlines WHERE status='pending' AND due_date >= date('now')",
            )

        # Engine-backed evidence coverage
        evidence_gaps = 0
        if _HAS_EVIDENCE_ENGINE and self._db:
            try:
                ev_engine = EvidenceEngine(self._db)
                case_rows = self._db.fetchall("SELECT id FROM cases WHERE status = 'active'")
                for cr in case_rows:
                    try:
                        gaps = ev_engine.check_gaps(dict(cr)["id"])
                        evidence_gaps += len(gaps)
                    except Exception:
                        pass
            except Exception:
                pass

        # Engine-backed filing readiness
        avg_score = 0
        if _HAS_FILING_ENGINE and self._db:
            try:
                fe = FilingEngine(self._db)
                pending_filings = fe.get_filings(status="draft")
                if pending_filings:
                    scores = [
                        int(pf.get("compliance_score") or 0)
                        for pf in pending_filings[:10]
                    ]
                    avg_score = int(sum(scores) / len(scores)) if scores else 0
            except Exception:
                pass

        row_frame = ctk.CTkFrame(self._stats_container, fg_color="transparent")
        row_frame.pack(fill="x")
        row_frame.columnconfigure((0, 1, 2, 3), weight=1)

        if next_deadline_days is not None:
            dl_value = f"{next_deadline_days}d"
            dl_title = f"Next Deadline ({pending} pending)"
            dl_color = COLORS["red"] if next_deadline_days <= 7 else COLORS["orange"]
        else:
            dl_value = str(pending)
            dl_title = "Pending Deadlines"
            dl_color = COLORS["orange"]

        cards: list[tuple[str, str | int, str]] = [
            (dl_title, dl_value, dl_color),
            ("Filing Readiness", f"{avg_score}%" if avg_score else str(filings), COLORS["green"]),
            (
                f"Evidence ({evidence_gaps} gaps)" if evidence_gaps else "Evidence Items",
                evidence,
                COLORS["yellow"],
            ),
            ("Total Cases", cases, COLORS["blue"]),
        ]

        for i, (title, value, color) in enumerate(cards):
            card = DataCard(row_frame, title=title, value=value, color=color)
            card.grid(row=0, column=i, sticky="nsew", padx=6, pady=6)
            self._stat_cards.append(card)
