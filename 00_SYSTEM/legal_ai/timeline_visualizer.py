"""Interactive HTML timeline visualiser for LitigationOS.

Generates a standalone, dark-themed HTML page that shows all litigation
events, filings, orders, and deadlines across the six case lanes (A-F)
of Pigors v. Watson.  The page is fully filterable, searchable, and
print-friendly for court presentations.

Stdlib-only.  Zero external dependencies.
"""

from __future__ import annotations

import hashlib
import html as html_mod
import json
import logging
import re
import sqlite3
import textwrap
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("legal_ai.timeline_visualizer")

# ── Path resolution ──────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
_DB_PATH = _HERE.parents[1] / "litigation_context.db"

# ── Case constants ───────────────────────────────────────────────────

_PLAINTIFF = "Andrew James Pigors"
_DEFENDANT = "Emily A. Watson"
_CHILD = "L.D.W."
_JUDGE = "Hon. Jenny L. McNeill"

_LANE_META: Dict[str, Dict[str, str]] = {
    "A": {"name": "Custody", "case": "2024-001507-DC", "color": "#3b82f6",
           "court": "14th Circuit Court"},
    "B": {"name": "Housing", "case": "2025-002760-CZ", "color": "#22c55e",
           "court": "14th Circuit Court"},
    "C": {"name": "Convergence", "case": "Multi-lane", "color": "#a855f7",
           "court": "Multiple"},
    "D": {"name": "PPO", "case": "2023-5907-PP", "color": "#f97316",
           "court": "14th Circuit Court"},
    "E": {"name": "Misconduct/JTC", "case": "Judge McNeill", "color": "#ef4444",
           "court": "JTC / AGC"},
    "F": {"name": "Appellate", "case": "COA 366810", "color": "#06b6d4",
           "court": "Michigan Court of Appeals"},
}

_CATEGORY_ICONS: Dict[str, str] = {
    "filing": "📄",
    "order": "⚖️",
    "hearing": "🏛️",
    "deadline": "⏰",
    "evidence": "🔍",
    "communication": "💬",
    "incident": "⚠️",
    "administrative": "📋",
}

_SIGNIFICANCE_WEIGHT: Dict[str, int] = {
    "critical": 4,
    "major": 3,
    "minor": 2,
    "routine": 1,
}


# ── Enumerations ─────────────────────────────────────────────────────

class EventCategory(str, Enum):
    FILING = "filing"
    ORDER = "order"
    HEARING = "hearing"
    DEADLINE = "deadline"
    EVIDENCE = "evidence"
    COMMUNICATION = "communication"
    INCIDENT = "incident"
    ADMINISTRATIVE = "administrative"


class Significance(str, Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    ROUTINE = "routine"


# ── Dataclasses ──────────────────────────────────────────────────────

@dataclass
class TimelineEvent:
    """A single event on the litigation timeline."""

    event_id: str
    date: str                    # ISO date  YYYY-MM-DD
    title: str
    description: str
    category: str                # EventCategory value
    lane: str                    # A-F
    parties_involved: List[str] = field(default_factory=list)
    court: str = ""
    significance: str = "routine"
    color: str = ""
    icon: str = ""
    linked_documents: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.color:
            meta = _LANE_META.get(self.lane, {})
            self.color = meta.get("color", "#9ca3af")
        if not self.icon:
            self.icon = _CATEGORY_ICONS.get(self.category, "📌")
        if not self.court:
            meta = _LANE_META.get(self.lane, {})
            self.court = meta.get("court", "")

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a plain dictionary."""
        return asdict(self)


@dataclass
class TimelineData:
    """Aggregate statistics for a set of timeline events."""

    events: List[TimelineEvent] = field(default_factory=list)
    date_range: Tuple[str, str] = ("", "")
    event_count: int = 0
    by_lane: Dict[str, int] = field(default_factory=dict)
    by_category: Dict[str, int] = field(default_factory=dict)
    by_significance: Dict[str, int] = field(default_factory=dict)
    by_year: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["events"] = [e.to_dict() for e in self.events]
        return d


# ── Seed events (embedded case history) ──────────────────────────────

_SEED_EVENTS: List[Dict[str, Any]] = [
    # ── 2023 ──
    {
        "event_id": "EVT-2023-001",
        "date": "2023-06-15",
        "title": "PPO filed (2023-5907-PP)",
        "description": "Personal Protection Order case initiated in 14th Circuit Court.",
        "category": "filing", "lane": "D", "significance": "critical",
        "parties_involved": [_DEFENDANT, _PLAINTIFF],
    },
    {
        "event_id": "EVT-2023-002",
        "date": "2023-09-01",
        "title": "Initial custody/parenting arrangements established",
        "description": "Preliminary parenting-time arrangements put in place following separation.",
        "category": "order", "lane": "A", "significance": "major",
        "parties_involved": [_PLAINTIFF, _DEFENDANT],
    },
    # ── 2024 ──
    {
        "event_id": "EVT-2024-001",
        "date": "2024-01-15",
        "title": "Custody case filed (2024-001507-DC)",
        "description": (
            "Andrew James Pigors files custody action in 14th Circuit Court.  "
            "Case assigned to Judge Jenny L. McNeill."
        ),
        "category": "filing", "lane": "A", "significance": "critical",
        "parties_involved": [_PLAINTIFF, _DEFENDANT],
    },
    {
        "event_id": "EVT-2024-002",
        "date": "2024-02-20",
        "title": "First ex parte order by Judge McNeill",
        "description": (
            "Emergency ex parte order entered without hearing or proper "
            "affidavit under MCR 3.207(B).  Parenting time restricted."
        ),
        "category": "order", "lane": "A", "significance": "critical",
        "parties_involved": [_JUDGE, _DEFENDANT],
    },
    {
        "event_id": "EVT-2024-003",
        "date": "2024-03-15",
        "title": "CPS report filed — bruising concerns",
        "description": (
            "Father reports bruising concerns for L.D.W. to Child "
            "Protective Services.  Investigation opened."
        ),
        "category": "incident", "lane": "A", "significance": "major",
        "parties_involved": [_PLAINTIFF, _CHILD],
    },
    {
        "event_id": "EVT-2024-004",
        "date": "2024-03-18",
        "title": "Retaliatory police report by mother",
        "description": (
            "Within 72 hours of CPS report, mother files police report "
            "against father.  Pattern of retaliatory filings documented."
        ),
        "category": "incident", "lane": "D", "significance": "major",
        "parties_involved": [_DEFENDANT, _PLAINTIFF],
    },
    {
        "event_id": "EVT-2024-005",
        "date": "2024-04-10",
        "title": "Multiple ex parte orders — spring period",
        "description": (
            "Second wave of ex parte orders entered before spring break.  "
            "Judge McNeill's ex parte rate reaches 18.26% (3.65× Michigan average)."
        ),
        "category": "order", "lane": "A", "significance": "critical",
        "parties_involved": [_JUDGE],
    },
    {
        "event_id": "EVT-2024-006",
        "date": "2024-05-01",
        "title": "Parenting time interference escalates",
        "description": (
            "Documented parenting-time interference incidents reach critical mass.  "
            "AppClose communications show systematic refusal of court-ordered time."
        ),
        "category": "incident", "lane": "A", "significance": "major",
        "parties_involved": [_DEFENDANT],
    },
    {
        "event_id": "EVT-2024-007",
        "date": "2024-06-15",
        "title": "PPO weaponisation incident",
        "description": (
            "PPO invoked after father files custody motion.  Pattern: "
            "custody motion → PPO allegation within 7 days → police intervention."
        ),
        "category": "incident", "lane": "D", "significance": "major",
        "parties_involved": [_DEFENDANT, _PLAINTIFF],
    },
    {
        "event_id": "EVT-2024-008",
        "date": "2024-08-01",
        "title": "Father's motions denied after delayed hearings",
        "description": (
            "Multiple substantive motions by father denied after extended "
            "delays.  Average time to ruling for father: 18.7 days vs 3.2 "
            "days for mother."
        ),
        "category": "order", "lane": "A", "significance": "major",
        "parties_involved": [_JUDGE, _PLAINTIFF],
    },
    {
        "event_id": "EVT-2024-009",
        "date": "2024-10-01",
        "title": "Police reports filed by multiple parties",
        "description": (
            "Multiple police reports filed in connection with custody "
            "and PPO disputes.  Documentation supports pattern-of-conduct argument."
        ),
        "category": "evidence", "lane": "A", "significance": "minor",
        "parties_involved": [_PLAINTIFF, _DEFENDANT],
    },
    {
        "event_id": "EVT-2024-010",
        "date": "2024-11-15",
        "title": "305 parenting time interference incidents documented",
        "description": (
            "Running total of documented parenting-time interference "
            "incidents reaches 305.  AppClose records serve as primary evidence."
        ),
        "category": "evidence", "lane": "A", "significance": "critical",
        "parties_involved": [_DEFENDANT],
    },
    # ── 2025 ──
    {
        "event_id": "EVT-2025-001",
        "date": "2025-01-15",
        "title": "Housing complaint filed (2025-002760-CZ)",
        "description": (
            "Pigors files housing discrimination/conditions complaint "
            "against Shady Oaks in 14th Circuit Court."
        ),
        "category": "filing", "lane": "B", "significance": "critical",
        "parties_involved": [_PLAINTIFF],
    },
    {
        "event_id": "EVT-2025-002",
        "date": "2025-03-01",
        "title": "COA appeal filed (366810)",
        "description": (
            "Appeal filed in Michigan Court of Appeals challenging trial "
            "court orders in custody case 2024-001507-DC."
        ),
        "category": "filing", "lane": "F", "significance": "critical",
        "parties_involved": [_PLAINTIFF],
    },
    {
        "event_id": "EVT-2025-003",
        "date": "2025-04-01",
        "title": "JTC complaint preparation",
        "description": (
            "Preparation of Judicial Tenure Commission complaint against "
            "Judge McNeill citing ex parte order pattern, asymmetric "
            "treatment, and MCR violations."
        ),
        "category": "administrative", "lane": "E", "significance": "major",
        "parties_involved": [_PLAINTIFF, _JUDGE],
    },
    {
        "event_id": "EVT-2025-004",
        "date": "2025-04-15",
        "title": "AGC complaint preparation",
        "description": (
            "Attorney Grievance Commission complaint preparation "
            "regarding opposing counsel conduct."
        ),
        "category": "administrative", "lane": "E", "significance": "major",
        "parties_involved": [_PLAINTIFF],
    },
    {
        "event_id": "EVT-2025-005",
        "date": "2025-05-01",
        "title": "Federal §1983 action under consideration",
        "description": (
            "Federal civil rights complaint (42 U.S.C. §1983) under "
            "consideration for due-process violations by Judge McNeill."
        ),
        "category": "administrative", "lane": "A", "significance": "major",
        "parties_involved": [_PLAINTIFF, _JUDGE],
    },
    {
        "event_id": "EVT-2025-006",
        "date": "2025-07-01",
        "title": "Multi-jurisdiction strategy active",
        "description": (
            "Simultaneous proceedings in circuit court, appellate court, "
            "and administrative bodies.  Multi-court pressure increases "
            "procedural compliance."
        ),
        "category": "administrative", "lane": "C", "significance": "major",
        "parties_involved": [_PLAINTIFF],
    },
    # ── 2026 ──
    {
        "event_id": "EVT-2026-001",
        "date": "2026-01-15",
        "title": "Current filing wave preparation",
        "description": (
            "Comprehensive filing wave across all six case lanes.  "
            "LitigationOS pipeline processing evidence and generating "
            "court-ready documents."
        ),
        "category": "administrative", "lane": "C", "significance": "critical",
        "parties_involved": [_PLAINTIFF],
    },
    {
        "event_id": "EVT-2026-002",
        "date": "2026-02-01",
        "title": "MCR 2.003 disqualification motion preparation",
        "description": (
            "Disqualification motion against Judge McNeill citing "
            "18.26% ex parte rate (3.65× normal), asymmetric denial "
            "rates, and timeline disparities."
        ),
        "category": "filing", "lane": "E", "significance": "critical",
        "parties_involved": [_PLAINTIFF, _JUDGE],
    },
]


# ── TimelineVisualizer ───────────────────────────────────────────────

class TimelineVisualizer:
    """Generate interactive HTML timeline for litigation events.

    Usage::

        viz = TimelineVisualizer()
        html = viz.generate()               # uses seed + DB events
        viz.export_html(Path("timeline.html"))
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or _DB_PATH
        self._events: List[TimelineEvent] = []
        self._generations: int = 0
        self._events_loaded_from_db: int = 0
        self._load_seed_events()
        logger.info(
            "TimelineVisualizer initialised (%d seed events, db=%s)",
            len(self._events), self._db_path,
        )

    # ── Database ─────────────────────────────────────────────────────

    def _connect_db(self) -> Optional[sqlite3.Connection]:
        """Open a WAL-mode connection to the central database."""
        if not self._db_path.exists():
            logger.warning("Database not found at %s", self._db_path)
            return None
        try:
            conn = sqlite3.connect(str(self._db_path), timeout=30)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA busy_timeout=60000")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA cache_size=-32000")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA synchronous=NORMAL")
            return conn
        except sqlite3.Error as exc:
            logger.error("DB connection failed: %s", exc)
            return None

    def _safe_query(
        self,
        conn: sqlite3.Connection,
        sql: str,
        params: Tuple[Any, ...] = (),
    ) -> List[sqlite3.Row]:
        try:
            return conn.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.warning("Query failed: %s — %s", exc, sql[:120])
            return []

    def _table_exists(self, conn: sqlite3.Connection, name: str) -> bool:
        rows = self._safe_query(
            conn,
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (name,),
        )
        return len(rows) > 0

    # ── Seed loading ─────────────────────────────────────────────────

    def _load_seed_events(self) -> None:
        """Populate internal event list from embedded seed data."""
        for seed in _SEED_EVENTS:
            self._events.append(TimelineEvent(
                event_id=seed["event_id"],
                date=seed["date"],
                title=seed["title"],
                description=seed["description"],
                category=seed["category"],
                lane=seed["lane"],
                parties_involved=seed.get("parties_involved", []),
                significance=seed.get("significance", "routine"),
            ))

    # ── Public API ───────────────────────────────────────────────────

    def add_event(self, event: TimelineEvent) -> None:
        """Add a single event to the internal list."""
        self._events.append(event)

    def add_events_from_dict(self, events: List[Dict[str, Any]]) -> int:
        """Bulk-add events from dictionaries.

        Returns:
            Number of events successfully added.
        """
        added = 0
        for ev in events:
            try:
                self._events.append(TimelineEvent(
                    event_id=ev.get("event_id", f"EVT-BULK-{added}"),
                    date=ev.get("date", ""),
                    title=ev.get("title", "Untitled"),
                    description=ev.get("description", ""),
                    category=ev.get("category", "administrative"),
                    lane=ev.get("lane", "C"),
                    parties_involved=ev.get("parties_involved", []),
                    court=ev.get("court", ""),
                    significance=ev.get("significance", "routine"),
                    color=ev.get("color", ""),
                    icon=ev.get("icon", ""),
                    linked_documents=ev.get("linked_documents", []),
                ))
                added += 1
            except (TypeError, ValueError) as exc:
                logger.warning("Skipping invalid event dict: %s", exc)
        return added

    def generate_from_db(self) -> str:
        """Load events from the database and generate HTML."""
        conn = self._connect_db()
        if conn is None:
            logger.info("No DB — generating from seed events only")
            return self.generate()

        try:
            # Load from filings table
            if self._table_exists(conn, "filings"):
                rows = self._safe_query(
                    conn,
                    """
                    SELECT filing_id, filed_date, filing_type, description,
                           lane, filed_by, court, case_number
                    FROM filings
                    WHERE filed_date IS NOT NULL
                    ORDER BY filed_date
                    LIMIT 500
                    """,
                )
                for r in rows:
                    self._events.append(TimelineEvent(
                        event_id=f"DB-FIL-{r['filing_id']}",
                        date=str(r["filed_date"])[:10],
                        title=f"Filing: {r['filing_type']}",
                        description=str(r["description"] or r["filing_type"]),
                        category="filing",
                        lane=str(r["lane"] or "C"),
                        parties_involved=[str(r["filed_by"] or "")],
                        court=str(r["court"] or ""),
                        significance="major",
                    ))
                    self._events_loaded_from_db += 1

            # Load from orders table
            if self._table_exists(conn, "orders"):
                rows = self._safe_query(
                    conn,
                    """
                    SELECT order_id, order_date, order_type, description,
                           judge, ex_parte, case_number
                    FROM orders
                    WHERE order_date IS NOT NULL
                    ORDER BY order_date
                    LIMIT 500
                    """,
                )
                for r in rows:
                    is_ex = str(r["ex_parte"]).lower() in ("1", "true", "yes")
                    self._events.append(TimelineEvent(
                        event_id=f"DB-ORD-{r['order_id']}",
                        date=str(r["order_date"])[:10],
                        title=f"Order: {r['order_type']}"
                               + (" (EX PARTE)" if is_ex else ""),
                        description=str(r["description"] or r["order_type"]),
                        category="order",
                        lane="A",
                        parties_involved=[str(r["judge"] or "")],
                        significance="critical" if is_ex else "major",
                    ))
                    self._events_loaded_from_db += 1

            # Load from deadlines table
            if self._table_exists(conn, "deadlines"):
                rows = self._safe_query(
                    conn,
                    """
                    SELECT deadline_id, due_date_iso, title, description,
                           vehicle_name, status
                    FROM deadlines
                    WHERE due_date_iso IS NOT NULL
                    ORDER BY due_date_iso
                    LIMIT 200
                    """,
                )
                for r in rows:
                    self._events.append(TimelineEvent(
                        event_id=f"DB-DL-{r['deadline_id']}",
                        date=str(r["due_date_iso"])[:10],
                        title=f"Deadline: {r['title']}",
                        description=str(r["description"] or ""),
                        category="deadline",
                        lane="C",
                        significance="major" if str(r["status"]).lower() != "done" else "routine",
                    ))
                    self._events_loaded_from_db += 1

        finally:
            conn.close()

        return self.generate()

    def filter_events(
        self,
        *,
        lane: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        significance: Optional[str] = None,
    ) -> List[TimelineEvent]:
        """Return events matching the given filters."""
        result = list(self._events)
        if lane:
            result = [e for e in result if e.lane == lane]
        if category:
            result = [e for e in result if e.category == category]
        if significance:
            result = [e for e in result if e.significance == significance]
        if start_date:
            result = [e for e in result if e.date >= start_date]
        if end_date:
            result = [e for e in result if e.date <= end_date]
        return result

    def get_timeline_data(self) -> TimelineData:
        """Compute aggregate statistics for current events."""
        events = sorted(self._events, key=lambda e: e.date)
        dates = [e.date for e in events if e.date]
        lane_counts = Counter(e.lane for e in events)
        cat_counts = Counter(e.category for e in events)
        sig_counts = Counter(e.significance for e in events)
        year_counts = Counter(e.date[:4] for e in events if len(e.date) >= 4)

        return TimelineData(
            events=events,
            date_range=(dates[0] if dates else "", dates[-1] if dates else ""),
            event_count=len(events),
            by_lane=dict(lane_counts),
            by_category=dict(cat_counts),
            by_significance=dict(sig_counts),
            by_year=dict(year_counts),
        )

    # ── HTML generation ──────────────────────────────────────────────

    def generate(self, events: Optional[List[TimelineEvent]] = None) -> str:
        """Generate the full standalone HTML timeline.

        Args:
            events: Optional override list.  Uses internal events if *None*.

        Returns:
            Complete HTML string.
        """
        evts = sorted(
            events or self._events,
            key=lambda e: e.date,
        )
        data = self.get_timeline_data()
        self._generations += 1

        events_json = json.dumps(
            [e.to_dict() for e in evts],
            indent=None,
            default=str,
        )

        parts = [
            "<!DOCTYPE html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="UTF-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            f"<title>LitigationOS Timeline — Pigors v. Watson</title>",
            "<style>",
            self._render_css(),
            "</style>",
            "</head>",
            "<body>",
            self._render_header(data),
            self._render_filter_controls(),
            self._render_statistics_panel(data),
            '<div id="timeline-container" class="timeline-container">',
            '<div class="timeline-line"></div>',
        ]

        for idx, ev in enumerate(evts):
            parts.append(self._render_event_card(ev, idx))

        parts.extend([
            "</div>",  # timeline-container
            '<div id="no-results" class="no-results" style="display:none;">',
            "No events match the current filters.",
            "</div>",
            "<script>",
            f"const EVENTS_DATA = {events_json};",
            self._render_javascript(),
            "</script>",
            "</body>",
            "</html>",
        ])

        return "\n".join(parts)

    def generate_print_version(self) -> str:
        """Generate a simplified, print-friendly HTML timeline."""
        evts = sorted(self._events, key=lambda e: e.date)
        data = self.get_timeline_data()

        rows_html: List[str] = []
        for ev in evts:
            esc = html_mod.escape
            rows_html.append(
                f"<tr>"
                f'<td class="print-date">{esc(ev.date)}</td>'
                f'<td><span class="print-lane" style="color:{esc(ev.color)}">'
                f"Lane {esc(ev.lane)}</span></td>"
                f'<td class="print-cat">{esc(ev.icon)} {esc(ev.category.title())}</td>'
                f"<td><strong>{esc(ev.title)}</strong><br>"
                f'<span class="print-desc">{esc(ev.description[:200])}</span></td>'
                f'<td class="print-sig">{esc(ev.significance.title())}</td>'
                f"</tr>"
            )

        return textwrap.dedent(f"""\
            <!DOCTYPE html>
            <html lang="en">
            <head>
            <meta charset="UTF-8">
            <title>Litigation Timeline — Pigors v. Watson (Print)</title>
            <style>
            body {{ font-family: 'Times New Roman', serif; font-size: 11pt;
                   color: #000; margin: 1in; }}
            h1 {{ font-size: 16pt; text-align: center; margin-bottom: 4pt; }}
            h2 {{ font-size: 12pt; text-align: center; color: #555;
                 margin-top: 0; margin-bottom: 12pt; }}
            table {{ width: 100%; border-collapse: collapse; font-size: 10pt; }}
            th {{ text-align: left; border-bottom: 2px solid #000; padding: 4px 6px;
                 font-size: 9pt; text-transform: uppercase; }}
            td {{ padding: 4px 6px; border-bottom: 1px solid #ccc; vertical-align: top; }}
            .print-date {{ white-space: nowrap; font-weight: 600; }}
            .print-lane {{ font-weight: 700; font-size: 9pt; }}
            .print-cat {{ white-space: nowrap; }}
            .print-desc {{ font-size: 9pt; color: #444; }}
            .print-sig {{ font-size: 9pt; text-align: center; }}
            .stats {{ font-size: 9pt; color: #666; margin-bottom: 8pt; text-align: center; }}
            @media print {{ body {{ margin: 0.5in; }} }}
            </style>
            </head>
            <body>
            <h1>Pigors v. Watson — Litigation Timeline</h1>
            <h2>{_PLAINTIFF} (Pro Se Plaintiff) v. {_DEFENDANT}</h2>
            <p class="stats">
              {data.event_count} events &bull;
              {data.date_range[0]} to {data.date_range[1]} &bull;
              Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
            </p>
            <table>
            <thead>
              <tr><th>Date</th><th>Lane</th><th>Type</th><th>Event</th><th>Significance</th></tr>
            </thead>
            <tbody>
            {"".join(rows_html)}
            </tbody>
            </table>
            </body>
            </html>
        """)

    # ── Export ────────────────────────────────────────────────────────

    def export_html(self, output_path: Path) -> str:
        """Write the interactive HTML timeline to *output_path*."""
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        content = self.generate()
        out.write_text(content, encoding="utf-8")
        logger.info("Exported HTML timeline to %s", out)
        return str(out)

    def export_json(self, output_path: Path) -> str:
        """Export events as JSON."""
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "event_count": len(self._events),
            "events": [e.to_dict() for e in sorted(self._events, key=lambda e: e.date)],
        }
        out.write_text(
            json.dumps(data, indent=2, default=str),
            encoding="utf-8",
        )
        logger.info("Exported %d events to %s", len(self._events), out)
        return str(out)

    # ── Stats ────────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Return operational statistics."""
        data = self.get_timeline_data()
        return {
            "total_events": len(self._events),
            "events_from_db": self._events_loaded_from_db,
            "events_from_seeds": len(self._events) - self._events_loaded_from_db,
            "generations": self._generations,
            "date_range": data.date_range,
            "by_lane": data.by_lane,
            "by_category": data.by_category,
            "by_significance": data.by_significance,
            "by_year": data.by_year,
            "db_path": str(self._db_path),
            "db_exists": self._db_path.exists(),
            "supported_categories": [c.value for c in EventCategory],
            "supported_lanes": list(_LANE_META.keys()),
        }

    # ── Private rendering helpers ────────────────────────────────────

    def _render_event_card(self, event: TimelineEvent, index: int) -> str:
        """Render a single timeline event as an HTML card."""
        esc = html_mod.escape
        side = "left" if index % 2 == 0 else "right"
        sig_class = f"sig-{event.significance}"
        lane_info = _LANE_META.get(event.lane, {})
        lane_label = f"Lane {event.lane}: {lane_info.get('name', '')}"

        docs_html = ""
        if event.linked_documents:
            doc_items = "".join(
                f"<li>{esc(d)}</li>" for d in event.linked_documents[:5]
            )
            docs_html = f'<ul class="event-docs">{doc_items}</ul>'

        parties_html = ""
        if event.parties_involved:
            parties_html = (
                f'<div class="event-parties">'
                f'{", ".join(esc(p) for p in event.parties_involved)}'
                f"</div>"
            )

        return textwrap.dedent(f"""\
            <div class="timeline-event timeline-{side} {sig_class}"
                 data-lane="{esc(event.lane)}"
                 data-category="{esc(event.category)}"
                 data-significance="{esc(event.significance)}"
                 data-date="{esc(event.date)}"
                 data-search="{esc((event.title + ' ' + event.description).lower())}">
              <div class="event-dot" style="background:{esc(event.color)}"></div>
              <div class="event-card" style="border-left: 3px solid {esc(event.color)}">
                <div class="event-header">
                  <span class="event-date">{esc(event.date)}</span>
                  <span class="event-badge lane-badge" style="background:{esc(event.color)}20;color:{esc(event.color)}">{esc(lane_label)}</span>
                  <span class="event-badge cat-badge">{esc(event.icon)} {esc(event.category.title())}</span>
                </div>
                <h3 class="event-title">{esc(event.title)}</h3>
                <p class="event-description">{esc(event.description)}</p>
                {parties_html}
                {docs_html}
                <div class="event-footer">
                  <span class="event-court">{esc(event.court)}</span>
                  <span class="event-significance {sig_class}-badge">{esc(event.significance.upper())}</span>
                </div>
              </div>
            </div>
        """)

    def _render_filter_controls(self) -> str:
        """Render the filter UI controls."""
        lane_buttons: List[str] = []
        for lane_id, meta in _LANE_META.items():
            esc = html_mod.escape
            lane_buttons.append(
                f'<button class="filter-btn lane-filter" data-lane="{esc(lane_id)}" '
                f'style="--lane-color:{esc(meta["color"])}">'
                f'{esc(lane_id)}: {esc(meta["name"])}</button>'
            )

        cat_buttons: List[str] = []
        for cat in EventCategory:
            icon = _CATEGORY_ICONS.get(cat.value, "📌")
            cat_buttons.append(
                f'<button class="filter-btn cat-filter" data-category="{html_mod.escape(cat.value)}">'
                f"{icon} {html_mod.escape(cat.value.title())}</button>"
            )

        sig_buttons: List[str] = []
        for sig in Significance:
            sig_buttons.append(
                f'<button class="filter-btn sig-filter" data-significance="{html_mod.escape(sig.value)}">'
                f"{html_mod.escape(sig.value.title())}</button>"
            )

        return textwrap.dedent(f"""\
            <div class="controls-panel">
              <div class="controls-row">
                <div class="control-group">
                  <label>Search</label>
                  <input type="text" id="search-input" class="search-input"
                         placeholder="Search events…">
                </div>
                <div class="control-group">
                  <label>Date Range</label>
                  <input type="date" id="date-start" class="date-input">
                  <span class="date-sep">to</span>
                  <input type="date" id="date-end" class="date-input">
                </div>
                <div class="control-group">
                  <label>Zoom</label>
                  <select id="zoom-select" class="zoom-select">
                    <option value="all">All Time</option>
                    <option value="2023">2023</option>
                    <option value="2024">2024</option>
                    <option value="2025">2025</option>
                    <option value="2026">2026</option>
                  </select>
                </div>
                <button class="reset-btn" id="reset-filters">✕ Reset</button>
              </div>
              <div class="controls-row">
                <div class="control-group">
                  <label>Lane</label>
                  <div class="btn-group">
                    {"".join(lane_buttons)}
                  </div>
                </div>
              </div>
              <div class="controls-row">
                <div class="control-group">
                  <label>Category</label>
                  <div class="btn-group">
                    {"".join(cat_buttons)}
                  </div>
                </div>
              </div>
              <div class="controls-row">
                <div class="control-group">
                  <label>Significance</label>
                  <div class="btn-group">
                    {"".join(sig_buttons)}
                  </div>
                </div>
              </div>
            </div>
        """)

    def _render_header(self, data: TimelineData) -> str:
        """Render the page header."""
        esc = html_mod.escape
        return textwrap.dedent(f"""\
            <header class="header">
              <div class="header-inner">
                <div class="header-title">
                  <h1>⚖️ Pigors v. Watson — Litigation Timeline</h1>
                  <p class="header-subtitle">
                    {esc(_PLAINTIFF)} (Pro Se) &bull;
                    {data.event_count} events &bull;
                    {esc(data.date_range[0])} to {esc(data.date_range[1])}
                  </p>
                </div>
                <div class="header-actions">
                  <button onclick="window.print()" class="action-btn">🖨️ Print</button>
                  <button onclick="exportJSON()" class="action-btn">📥 Export JSON</button>
                </div>
              </div>
            </header>
        """)

    def _render_statistics_panel(self, data: TimelineData) -> str:
        """Render the statistics summary panel."""
        esc = html_mod.escape

        lane_stats: List[str] = []
        for lane_id, meta in _LANE_META.items():
            count = data.by_lane.get(lane_id, 0)
            lane_stats.append(
                f'<div class="stat-item">'
                f'<span class="stat-color" style="background:{esc(meta["color"])}"></span>'
                f'<span class="stat-label">{esc(lane_id)}: {esc(meta["name"])}</span>'
                f'<span class="stat-value">{count}</span>'
                f"</div>"
            )

        cat_stats: List[str] = []
        for cat in EventCategory:
            count = data.by_category.get(cat.value, 0)
            icon = _CATEGORY_ICONS.get(cat.value, "📌")
            cat_stats.append(
                f'<div class="stat-item">'
                f'<span class="stat-icon">{icon}</span>'
                f'<span class="stat-label">{esc(cat.value.title())}</span>'
                f'<span class="stat-value">{count}</span>'
                f"</div>"
            )

        year_stats: List[str] = []
        for year in sorted(data.by_year.keys()):
            count = data.by_year[year]
            year_stats.append(
                f'<div class="stat-item">'
                f'<span class="stat-label">{esc(year)}</span>'
                f'<span class="stat-value">{count}</span>'
                f"</div>"
            )

        return textwrap.dedent(f"""\
            <div class="stats-panel" id="stats-panel">
              <div class="stats-toggle" onclick="toggleStats()">
                📊 Statistics <span id="stats-arrow">▸</span>
              </div>
              <div class="stats-content" id="stats-content" style="display:none;">
                <div class="stats-grid">
                  <div class="stats-card">
                    <h4>By Lane</h4>
                    {"".join(lane_stats)}
                  </div>
                  <div class="stats-card">
                    <h4>By Category</h4>
                    {"".join(cat_stats)}
                  </div>
                  <div class="stats-card">
                    <h4>By Year</h4>
                    {"".join(year_stats)}
                  </div>
                  <div class="stats-card">
                    <h4>By Significance</h4>
                    <div class="stat-item">
                      <span class="stat-label">Critical</span>
                      <span class="stat-value sig-critical-badge">{data.by_significance.get("critical", 0)}</span>
                    </div>
                    <div class="stat-item">
                      <span class="stat-label">Major</span>
                      <span class="stat-value sig-major-badge">{data.by_significance.get("major", 0)}</span>
                    </div>
                    <div class="stat-item">
                      <span class="stat-label">Minor</span>
                      <span class="stat-value">{data.by_significance.get("minor", 0)}</span>
                    </div>
                    <div class="stat-item">
                      <span class="stat-label">Routine</span>
                      <span class="stat-value">{data.by_significance.get("routine", 0)}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
        """)

    def _render_css(self) -> str:
        """Return the complete CSS stylesheet."""
        return textwrap.dedent("""\
            /* ── LitigationOS Timeline — Dark Theme ── */
            :root {
                --bg: #0a0e17;
                --surface: #111827;
                --surface2: #1f2937;
                --border: #374151;
                --text: #f9fafb;
                --text2: #9ca3af;
                --accent: #3b82f6;
                --green: #22c55e;
                --yellow: #eab308;
                --red: #ef4444;
                --orange: #f97316;
                --purple: #a855f7;
                --cyan: #06b6d4;
                --pink: #ec4899;
            }

            *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
                             'Helvetica Neue', Arial, sans-serif;
                background: var(--bg);
                color: var(--text);
                line-height: 1.5;
                min-height: 100vh;
            }

            /* ── Header ── */
            .header {
                background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%);
                padding: 1.25rem 2rem;
                border-bottom: 1px solid var(--border);
                position: sticky;
                top: 0;
                z-index: 100;
            }
            .header-inner {
                max-width: 1400px;
                margin: 0 auto;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 0.75rem;
            }
            .header h1 {
                font-size: 1.2rem;
                font-weight: 700;
                letter-spacing: -0.02em;
            }
            .header-subtitle {
                font-size: 0.8rem;
                color: var(--text2);
                margin-top: 2px;
            }
            .header-actions { display: flex; gap: 0.5rem; }
            .action-btn {
                background: var(--surface2);
                color: var(--text);
                border: 1px solid var(--border);
                padding: 0.4rem 0.8rem;
                border-radius: 6px;
                font-size: 0.78rem;
                cursor: pointer;
                transition: background 0.2s;
            }
            .action-btn:hover { background: var(--border); }

            /* ── Controls Panel ── */
            .controls-panel {
                max-width: 1400px;
                margin: 1rem auto;
                padding: 0 2rem;
            }
            .controls-row {
                display: flex;
                flex-wrap: wrap;
                gap: 1rem;
                align-items: flex-end;
                margin-bottom: 0.75rem;
            }
            .control-group {
                display: flex;
                flex-direction: column;
                gap: 0.3rem;
            }
            .control-group label {
                font-size: 0.7rem;
                font-weight: 600;
                color: var(--text2);
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            .search-input, .date-input, .zoom-select {
                background: var(--surface);
                border: 1px solid var(--border);
                color: var(--text);
                padding: 0.4rem 0.6rem;
                border-radius: 6px;
                font-size: 0.82rem;
                outline: none;
                transition: border-color 0.2s;
            }
            .search-input:focus, .date-input:focus, .zoom-select:focus {
                border-color: var(--accent);
            }
            .search-input { width: 220px; }
            .date-input { width: 140px; }
            .date-sep { color: var(--text2); font-size: 0.8rem; align-self: center; }
            .zoom-select { width: 120px; }

            .btn-group { display: flex; flex-wrap: wrap; gap: 0.35rem; }
            .filter-btn {
                background: var(--surface);
                color: var(--text2);
                border: 1px solid var(--border);
                padding: 0.3rem 0.6rem;
                border-radius: 5px;
                font-size: 0.75rem;
                cursor: pointer;
                transition: all 0.15s;
            }
            .filter-btn:hover { border-color: var(--accent); color: var(--text); }
            .filter-btn.active {
                background: var(--accent);
                color: #fff;
                border-color: var(--accent);
            }
            .lane-filter.active {
                background: var(--lane-color, var(--accent));
                border-color: var(--lane-color, var(--accent));
            }
            .reset-btn {
                background: transparent;
                color: var(--red);
                border: 1px solid rgba(239,68,68,0.3);
                padding: 0.4rem 0.8rem;
                border-radius: 6px;
                font-size: 0.78rem;
                cursor: pointer;
                align-self: flex-end;
            }
            .reset-btn:hover { background: rgba(239,68,68,0.1); }

            /* ── Statistics Panel ── */
            .stats-panel {
                max-width: 1400px;
                margin: 0 auto 1rem;
                padding: 0 2rem;
            }
            .stats-toggle {
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 6px;
                padding: 0.5rem 1rem;
                cursor: pointer;
                font-size: 0.85rem;
                font-weight: 600;
                transition: background 0.2s;
                user-select: none;
            }
            .stats-toggle:hover { background: var(--surface2); }
            .stats-content {
                background: var(--surface);
                border: 1px solid var(--border);
                border-top: none;
                border-radius: 0 0 6px 6px;
                padding: 1rem;
            }
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1rem;
            }
            .stats-card {
                background: var(--surface2);
                border-radius: 6px;
                padding: 0.75rem;
            }
            .stats-card h4 {
                font-size: 0.75rem;
                color: var(--text2);
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 0.5rem;
                border-bottom: 1px solid var(--border);
                padding-bottom: 0.3rem;
            }
            .stat-item {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 0.2rem 0;
                font-size: 0.8rem;
            }
            .stat-color {
                display: inline-block;
                width: 10px; height: 10px;
                border-radius: 2px;
                margin-right: 0.4rem;
                flex-shrink: 0;
            }
            .stat-icon { margin-right: 0.3rem; font-size: 0.85rem; }
            .stat-label { flex: 1; color: var(--text2); }
            .stat-value { font-weight: 700; min-width: 28px; text-align: right; }

            /* ── Timeline ── */
            .timeline-container {
                max-width: 1100px;
                margin: 0 auto;
                padding: 2rem 2rem 4rem;
                position: relative;
            }
            .timeline-line {
                position: absolute;
                left: 50%;
                top: 0;
                bottom: 0;
                width: 2px;
                background: var(--border);
                transform: translateX(-50%);
            }

            .timeline-event {
                position: relative;
                width: 47%;
                margin-bottom: 2rem;
                opacity: 1;
                transition: opacity 0.3s, transform 0.3s;
            }
            .timeline-event.hidden {
                display: none !important;
            }
            .timeline-left { margin-right: auto; margin-left: 0; }
            .timeline-right { margin-left: auto; margin-right: 0; }

            .event-dot {
                position: absolute;
                width: 14px; height: 14px;
                border-radius: 50%;
                top: 1.2rem;
                z-index: 2;
                border: 2px solid var(--bg);
                box-shadow: 0 0 0 2px var(--border);
            }
            .timeline-left .event-dot { right: -38px; }
            .timeline-right .event-dot { left: -38px; }

            .event-card {
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 8px;
                padding: 0.85rem 1rem;
                transition: transform 0.2s, box-shadow 0.2s;
            }
            .event-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            }

            .event-header {
                display: flex;
                flex-wrap: wrap;
                gap: 0.4rem;
                align-items: center;
                margin-bottom: 0.4rem;
            }
            .event-date {
                font-size: 0.75rem;
                font-weight: 700;
                color: var(--text2);
                font-family: 'Courier New', monospace;
            }
            .event-badge {
                display: inline-block;
                padding: 1px 6px;
                border-radius: 4px;
                font-size: 0.68rem;
                font-weight: 600;
            }
            .lane-badge { }
            .cat-badge {
                background: var(--surface2);
                color: var(--text2);
            }
            .event-title {
                font-size: 0.92rem;
                font-weight: 700;
                margin-bottom: 0.3rem;
                line-height: 1.3;
            }
            .event-description {
                font-size: 0.8rem;
                color: var(--text2);
                line-height: 1.5;
                margin-bottom: 0.4rem;
            }
            .event-parties {
                font-size: 0.72rem;
                color: var(--text2);
                font-style: italic;
                margin-bottom: 0.3rem;
            }
            .event-docs {
                list-style: none;
                padding: 0;
                margin: 0.3rem 0;
            }
            .event-docs li {
                font-size: 0.72rem;
                color: var(--accent);
                padding: 1px 0;
            }
            .event-docs li::before { content: '📎 '; }
            .event-footer {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 0.4rem;
                padding-top: 0.4rem;
                border-top: 1px solid rgba(55,65,81,0.5);
            }
            .event-court {
                font-size: 0.7rem;
                color: var(--text2);
            }
            .event-significance {
                font-size: 0.65rem;
                font-weight: 700;
                padding: 1px 6px;
                border-radius: 3px;
            }

            /* Significance badges */
            .sig-critical .event-card { border-left-width: 4px; }
            .sig-critical-badge {
                background: rgba(239,68,68,0.15);
                color: var(--red);
            }
            .sig-major-badge {
                background: rgba(249,115,22,0.15);
                color: var(--orange);
            }
            .sig-minor-badge {
                background: rgba(234,179,8,0.15);
                color: var(--yellow);
            }
            .sig-routine-badge {
                background: rgba(156,163,175,0.15);
                color: var(--text2);
            }

            .no-results {
                text-align: center;
                padding: 3rem;
                color: var(--text2);
                font-size: 1.1rem;
            }

            /* ── Responsive ── */
            @media (max-width: 768px) {
                .timeline-line { left: 20px; }
                .timeline-event { width: calc(100% - 40px); margin-left: 40px !important; margin-right: 0 !important; }
                .event-dot { left: -30px !important; right: auto !important; }
                .controls-row { flex-direction: column; }
                .search-input { width: 100%; }
                .header-inner { flex-direction: column; text-align: center; }
            }

            /* ── Print ── */
            @media print {
                body { background: #fff; color: #000; }
                .header { background: none; border-bottom: 2px solid #000; position: static; }
                .header h1 { color: #000; }
                .header-subtitle { color: #333; }
                .header-actions, .controls-panel, .stats-panel, .reset-btn { display: none !important; }
                .timeline-line { background: #ccc; }
                .event-card {
                    background: #fff;
                    border: 1px solid #ccc;
                    break-inside: avoid;
                    -webkit-print-color-adjust: exact;
                    print-color-adjust: exact;
                }
                .event-dot { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
                .timeline-event { opacity: 1 !important; }
            }
        """)

    def _render_javascript(self) -> str:
        """Return the complete JavaScript for interactivity."""
        return textwrap.dedent("""\
            // ── LitigationOS Timeline — Interactive JS ──

            const state = {
                lanes: new Set(),
                categories: new Set(),
                significance: new Set(),
                search: '',
                dateStart: '',
                dateEnd: '',
                zoom: 'all'
            };

            function getEvents() {
                return document.querySelectorAll('.timeline-event');
            }

            function applyFilters() {
                const events = getEvents();
                let visible = 0;
                events.forEach(el => {
                    const lane = el.dataset.lane;
                    const cat = el.dataset.category;
                    const sig = el.dataset.significance;
                    const date = el.dataset.date;
                    const searchText = el.dataset.search || '';

                    let show = true;

                    if (state.lanes.size > 0 && !state.lanes.has(lane)) show = false;
                    if (state.categories.size > 0 && !state.categories.has(cat)) show = false;
                    if (state.significance.size > 0 && !state.significance.has(sig)) show = false;

                    if (state.search && !searchText.includes(state.search.toLowerCase())) show = false;

                    if (state.dateStart && date < state.dateStart) show = false;
                    if (state.dateEnd && date > state.dateEnd) show = false;

                    if (state.zoom !== 'all') {
                        if (!date.startsWith(state.zoom)) show = false;
                    }

                    if (show) {
                        el.classList.remove('hidden');
                        visible++;
                    } else {
                        el.classList.add('hidden');
                    }
                });

                const noResults = document.getElementById('no-results');
                if (noResults) {
                    noResults.style.display = visible === 0 ? 'block' : 'none';
                }
            }

            // Toggle filter buttons
            function setupFilterButtons(selector, stateSet) {
                document.querySelectorAll(selector).forEach(btn => {
                    btn.addEventListener('click', () => {
                        const val = btn.dataset.lane || btn.dataset.category || btn.dataset.significance;
                        if (btn.classList.contains('active')) {
                            btn.classList.remove('active');
                            stateSet.delete(val);
                        } else {
                            btn.classList.add('active');
                            stateSet.add(val);
                        }
                        applyFilters();
                    });
                });
            }

            setupFilterButtons('.lane-filter', state.lanes);
            setupFilterButtons('.cat-filter', state.categories);
            setupFilterButtons('.sig-filter', state.significance);

            // Search
            const searchInput = document.getElementById('search-input');
            if (searchInput) {
                searchInput.addEventListener('input', (e) => {
                    state.search = e.target.value;
                    applyFilters();
                });
            }

            // Date range
            const dateStart = document.getElementById('date-start');
            const dateEnd = document.getElementById('date-end');
            if (dateStart) {
                dateStart.addEventListener('change', (e) => {
                    state.dateStart = e.target.value;
                    applyFilters();
                });
            }
            if (dateEnd) {
                dateEnd.addEventListener('change', (e) => {
                    state.dateEnd = e.target.value;
                    applyFilters();
                });
            }

            // Zoom select
            const zoomSelect = document.getElementById('zoom-select');
            if (zoomSelect) {
                zoomSelect.addEventListener('change', (e) => {
                    state.zoom = e.target.value;
                    applyFilters();
                });
            }

            // Reset
            const resetBtn = document.getElementById('reset-filters');
            if (resetBtn) {
                resetBtn.addEventListener('click', () => {
                    state.lanes.clear();
                    state.categories.clear();
                    state.significance.clear();
                    state.search = '';
                    state.dateStart = '';
                    state.dateEnd = '';
                    state.zoom = 'all';

                    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                    if (searchInput) searchInput.value = '';
                    if (dateStart) dateStart.value = '';
                    if (dateEnd) dateEnd.value = '';
                    if (zoomSelect) zoomSelect.value = 'all';

                    applyFilters();
                });
            }

            // Stats toggle
            function toggleStats() {
                const content = document.getElementById('stats-content');
                const arrow = document.getElementById('stats-arrow');
                if (content.style.display === 'none') {
                    content.style.display = 'block';
                    arrow.textContent = '▾';
                } else {
                    content.style.display = 'none';
                    arrow.textContent = '▸';
                }
            }

            // Export JSON
            function exportJSON() {
                const blob = new Blob([JSON.stringify(EVENTS_DATA, null, 2)], {type: 'application/json'});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'litigation_timeline_' + new Date().toISOString().slice(0,10) + '.json';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }
        """)
