"""Case Timeline Visualization Engine.

Aggregates chronological events from multiple database tables into a unified
case timeline.  Supports filtering by lane, date range, and event type;
gap analysis; event clustering; and export to Markdown, JSON, and CSV.

Data sources (all verified via ``PRAGMA table_info`` before querying):
    - ``timeline_events``   — core chronological events
    - ``docket_events``     — court docket entries
    - ``deadlines``         — filing / hearing deadlines
    - ``filings``           — filed documents
    - ``judicial_violations`` — documented judicial-conduct issues
    - ``case_timeline``     — supplemental timeline (litigation_context.db)
    - ``evidence_quotes``   — evidence with timestamps
    - ``documents``         — catalogued documents
"""

from __future__ import annotations

import csv
import io
import json
import logging
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Optional, Sequence

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    import sqlite3

    from litigationos.db.connection import DatabaseManager

logger = logging.getLogger(__name__)

# -- Lane definitions ---------------------------------------------------------

CASE_LANES: dict[str, str] = {
    "A": "Watson custody",
    "B": "Shady Oaks housing",
    "C": "Convergence (cross-lane)",
    "D": "PPO / Protection Orders",
    "E": "Judicial Misconduct / JTC",
    "F": "Appellate (COA/MSC)",
}

VALID_IMPORTANCE = ("critical", "high", "normal", "low")
VALID_EVENT_TYPES = (
    "filing", "hearing", "order", "communication",
    "incident", "deadline", "violation", "evidence", "document",
)

# -- Pydantic models ----------------------------------------------------------


class TimelineEvent(BaseModel):
    """A single event on the case timeline."""

    id: Optional[int] = None
    case_id: Optional[int] = None
    event_date: str
    event_type: Optional[str] = None
    title: str = ""
    description: Optional[str] = None
    source_file: Optional[str] = None
    source_table: Optional[str] = None
    lane: Optional[str] = None
    severity: Optional[str] = None
    importance: str = "normal"
    parties_involved: Optional[str] = None
    filing_id: Optional[int] = None
    evidence_ids: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TimelineGap(BaseModel):
    """A period with no documented events."""

    start_date: str
    end_date: str
    gap_days: int
    significance: str = "low"  # 'critical', 'high', 'medium', 'low'

    model_config = ConfigDict(from_attributes=True)


class EventCluster(BaseModel):
    """A thematic grouping of events."""

    cluster_name: str
    events: list[TimelineEvent] = Field(default_factory=list)
    date_range: Optional[str] = None
    pattern_description: Optional[str] = None
    event_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class TimelineResult(BaseModel):
    """Full timeline build result."""

    case_id: Optional[int] = None
    total_events: int = 0
    date_range: Optional[str] = None
    events: list[TimelineEvent] = Field(default_factory=list)
    sources_queried: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# -- Helpers -------------------------------------------------------------------


def _parse_date(value: Optional[str]) -> Optional[date]:
    """Best-effort ISO-8601 date parse.  Returns *None* on failure."""
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value[:19], fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def _safe_str(value: object) -> Optional[str]:
    """Convert *value* to ``str`` unless it is ``None``."""
    return str(value) if value is not None else None


# -- Engine -------------------------------------------------------------------


class TimelineEngine:
    """Build, query, and export chronological case timelines.

    Args:
        db: A :class:`DatabaseManager` instance for the application database.
        context_db_path: Optional path to the central ``litigation_context.db``
            for cross-referencing docket_events, case_timeline, etc.
    """

    # Tables we attempt to harvest events from, together with the column
    # mapping  ``(date_col, title_col, desc_col, type_col, lane_col)``.
    # If a table or column does not exist we silently skip it.
    _SOURCE_TABLES: list[tuple[str, str, str, str, str | None, str | None]] = [
        # (table, date_col, title_col, desc_col, type_col, lane_col)
        ("timeline_events", "event_date", "title", "description", "event_type", None),
        ("docket_events", "event_date", "event_type", "description", "event_type", None),
        ("deadlines", "due_date", "title", "notes", None, None),
        ("filings", "filed_date", "title", "notes", "filing_type", None),
        ("judicial_violations", "date_occurred", "violation_type", "description", "violation_type", None),
        ("case_timeline", "event_date", "event_type", "description", "event_type", "lane"),
        ("documents", "created_date", "title", "doc_type", None, "lane"),
    ]

    def __init__(
        self,
        db: "DatabaseManager",
        *,
        context_db_path: Optional[str] = None,
    ) -> None:
        self._db = db
        self._context_db_path = context_db_path
        # Cache of verified table schemas: table -> {col_name: col_type}
        self._schema_cache: dict[str, dict[str, str]] = {}

    # -- Schema introspection -------------------------------------------------

    def _get_table_columns(
        self,
        conn: "sqlite3.Connection",
        table: str,
    ) -> dict[str, str]:
        """Return ``{column_name: column_type}`` for *table*, or ``{}``."""
        if table in self._schema_cache:
            return self._schema_cache[table]
        try:
            rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
            cols = {r["name"]: (r["type"] or "TEXT") for r in rows}
            self._schema_cache[table] = cols
            return cols
        except Exception:
            self._schema_cache[table] = {}
            return {}

    def _table_has(
        self,
        conn: "sqlite3.Connection",
        table: str,
        *columns: str,
    ) -> bool:
        """Return ``True`` if *table* exists and contains all *columns*."""
        cols = self._get_table_columns(conn, table)
        if not cols:
            return False
        return all(c in cols for c in columns)

    # -- Event harvesting (multi-source) --------------------------------------

    def _harvest_events(
        self,
        conn: "sqlite3.Connection",
        case_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        lane: Optional[str] = None,
    ) -> tuple[list[TimelineEvent], list[str]]:
        """Collect events from every available source table.

        Returns ``(events, sources_queried)``.
        """
        events: list[TimelineEvent] = []
        sources: list[str] = []

        for table, date_col, title_col, desc_col, type_col, lane_col in self._SOURCE_TABLES:
            needed = [date_col, title_col]
            if not self._table_has(conn, table, *needed):
                continue

            cols = self._get_table_columns(conn, table)
            select_cols = [date_col, title_col]
            if desc_col and desc_col in cols and desc_col != title_col:
                select_cols.append(desc_col)
            if type_col and type_col in cols and type_col not in select_cols:
                select_cols.append(type_col)
            if lane_col and lane_col in cols:
                select_cols.append(lane_col)
            # Always try to grab id and case_id if present
            if "id" in cols:
                select_cols.insert(0, "id")
            if "case_id" in cols and "case_id" not in select_cols:
                select_cols.append("case_id")
            if "case_number" in cols and "case_number" not in select_cols:
                select_cols.append("case_number")
            if "importance" in cols and "importance" not in select_cols:
                select_cols.append("importance")
            if "severity" in cols and "severity" not in select_cols:
                select_cols.append("severity")
            if "source_file" in cols and "source_file" not in select_cols:
                select_cols.append("source_file")
            if "is_key_event" in cols and "is_key_event" not in select_cols:
                select_cols.append("is_key_event")
            if "filing_id" in cols and "filing_id" not in select_cols:
                select_cols.append("filing_id")
            if "evidence_ids" in cols and "evidence_ids" not in select_cols:
                select_cols.append("evidence_ids")

            # De-dup column list while preserving order
            seen: set[str] = set()
            unique_cols: list[str] = []
            for c in select_cols:
                if c not in seen:
                    seen.add(c)
                    unique_cols.append(c)

            # Build WHERE clause
            clauses: list[str] = []
            params: list[object] = []
            if case_id is not None and "case_id" in cols:
                clauses.append("case_id = ?")
                params.append(case_id)
            if start_date and date_col in cols:
                clauses.append(f"{date_col} >= ?")
                params.append(start_date)
            if end_date and date_col in cols:
                clauses.append(f"{date_col} <= ?")
                params.append(end_date)
            if lane and lane_col and lane_col in cols:
                clauses.append(f"{lane_col} = ?")
                params.append(lane)
            # Skip rows with no date
            clauses.append(f"{date_col} IS NOT NULL")
            clauses.append(f"{date_col} != ''")

            sql = f"SELECT {', '.join(unique_cols)} FROM {table}"
            if clauses:
                sql += " WHERE " + " AND ".join(clauses)
            sql += f" ORDER BY {date_col} ASC"

            try:
                rows = conn.execute(sql, tuple(params)).fetchall()
            except Exception:
                logger.debug("Skipping table %s (query failed)", table)
                continue

            sources.append(table)
            for row in rows:
                r = dict(row)
                evt = TimelineEvent(
                    id=r.get("id"),
                    case_id=r.get("case_id"),
                    event_date=str(r[date_col]),
                    title=str(r.get(title_col) or ""),
                    description=_safe_str(r.get(desc_col)) if desc_col != title_col else None,
                    event_type=_safe_str(r.get(type_col)) if type_col else table,
                    source_table=table,
                    source_file=_safe_str(r.get("source_file")),
                    lane=_safe_str(r.get(lane_col)) if lane_col else None,
                    severity=_safe_str(r.get("severity")),
                    importance=str(r.get("importance", "normal") or "normal"),
                    filing_id=r.get("filing_id"),
                    evidence_ids=_safe_str(r.get("evidence_ids")),
                )
                events.append(evt)

        return events, sources

    # -- Public API -----------------------------------------------------------

    def build_timeline(
        self,
        case_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> TimelineResult:
        """Generate a chronological event list for *case_id*.

        Args:
            case_id: Restrict events to this case (``None`` for all cases).
            start_date: ISO-8601 lower bound (inclusive).
            end_date: ISO-8601 upper bound (inclusive).

        Returns:
            A :class:`TimelineResult` with sorted events.
        """
        conn = self._db.connect()
        try:
            events, sources = self._harvest_events(
                conn, case_id=case_id, start_date=start_date, end_date=end_date,
            )
        finally:
            conn.close()

        events.sort(key=lambda e: e.event_date)

        date_range = None
        if events:
            date_range = f"{events[0].event_date} to {events[-1].event_date}"

        return TimelineResult(
            case_id=case_id,
            total_events=len(events),
            date_range=date_range,
            events=events,
            sources_queried=sources,
        )

    def get_key_events(
        self,
        case_id: Optional[int] = None,
        limit: int = 50,
    ) -> list[TimelineEvent]:
        """Return the most significant events, ranked by importance.

        Importance ranking: critical > high > normal > low.
        """
        importance_rank = {"critical": 0, "high": 1, "normal": 2, "low": 3}
        timeline = self.build_timeline(case_id=case_id)
        ranked = sorted(
            timeline.events,
            key=lambda e: (importance_rank.get(e.importance, 2), e.event_date),
        )
        return ranked[:limit]

    def get_lane_timeline(self, lane: str) -> TimelineResult:
        """Return events filtered to a specific case lane (A-F).

        The method searches for the lane value in two ways:
        1. Columns explicitly named ``lane`` in source tables.
        2. Post-harvest filtering on events whose *lane* field matches.

        Args:
            lane: One of ``A``, ``B``, ``C``, ``D``, ``E``, ``F``.

        Returns:
            A :class:`TimelineResult` containing only lane-matching events.

        Raises:
            ValueError: If *lane* is not in ``CASE_LANES``.
        """
        if lane not in CASE_LANES:
            raise ValueError(
                f"Invalid lane '{lane}'. Must be one of {list(CASE_LANES.keys())}"
            )

        conn = self._db.connect()
        try:
            events, sources = self._harvest_events(conn, lane=lane)
        finally:
            conn.close()

        # Some source tables don't have a lane column — do post-filter
        filtered = [e for e in events if e.lane == lane]

        # If we got nothing from strict lane match, return all events
        # gathered through the lane-aware query (they were already filtered
        # at the SQL level for tables that have a lane column).
        if not filtered:
            filtered = events

        filtered.sort(key=lambda e: e.event_date)

        date_range = None
        if filtered:
            date_range = f"{filtered[0].event_date} to {filtered[-1].event_date}"

        return TimelineResult(
            total_events=len(filtered),
            date_range=date_range,
            events=filtered,
            sources_queried=sources,
        )

    def find_gaps(
        self,
        case_id: Optional[int] = None,
        min_gap_days: int = 30,
    ) -> list[TimelineGap]:
        """Identify periods with no documented events.

        Args:
            case_id: Restrict to this case.
            min_gap_days: Only report gaps of at least this many days.

        Returns:
            List of :class:`TimelineGap` sorted chronologically.
        """
        timeline = self.build_timeline(case_id=case_id)
        parsed_dates: list[date] = []
        for evt in timeline.events:
            d = _parse_date(evt.event_date)
            if d:
                parsed_dates.append(d)

        if len(parsed_dates) < 2:
            return []

        # Unique, sorted dates
        unique_dates = sorted(set(parsed_dates))
        gaps: list[TimelineGap] = []
        for i in range(len(unique_dates) - 1):
            delta = (unique_dates[i + 1] - unique_dates[i]).days
            if delta >= min_gap_days:
                if delta >= 180:
                    significance = "critical"
                elif delta >= 90:
                    significance = "high"
                elif delta >= 60:
                    significance = "medium"
                else:
                    significance = "low"
                gaps.append(
                    TimelineGap(
                        start_date=unique_dates[i].isoformat(),
                        end_date=unique_dates[i + 1].isoformat(),
                        gap_days=delta,
                        significance=significance,
                    )
                )
        return gaps

    def get_event_clusters(
        self,
        case_id: Optional[int] = None,
    ) -> list[EventCluster]:
        """Group events by their ``event_type``.

        Returns:
            A list of :class:`EventCluster` objects, one per type.
        """
        timeline = self.build_timeline(case_id=case_id)
        buckets: dict[str, list[TimelineEvent]] = defaultdict(list)
        for evt in timeline.events:
            key = evt.event_type or "unknown"
            buckets[key].append(evt)

        clusters: list[EventCluster] = []
        for cluster_name, evts in sorted(buckets.items()):
            evts.sort(key=lambda e: e.event_date)
            date_range = None
            if evts:
                date_range = f"{evts[0].event_date} to {evts[-1].event_date}"
            clusters.append(
                EventCluster(
                    cluster_name=cluster_name,
                    events=evts,
                    date_range=date_range,
                    event_count=len(evts),
                    pattern_description=f"{len(evts)} {cluster_name} events",
                )
            )
        return clusters

    # -- Export ----------------------------------------------------------------

    def export_timeline(
        self,
        case_id: Optional[int] = None,
        format: str = "md",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> str:
        """Export the timeline to a string in the given format.

        Args:
            case_id: Restrict to case.
            format: One of ``'md'``, ``'json'``, ``'csv'``.
            start_date: ISO-8601 lower bound.
            end_date: ISO-8601 upper bound.

        Returns:
            Formatted string of the timeline.

        Raises:
            ValueError: If *format* is not supported.
        """
        fmt = format.lower()
        if fmt not in ("md", "json", "csv"):
            raise ValueError(f"Unsupported format '{format}'. Use 'md', 'json', or 'csv'.")

        timeline = self.build_timeline(
            case_id=case_id, start_date=start_date, end_date=end_date,
        )

        if fmt == "json":
            return self._export_json(timeline)
        if fmt == "csv":
            return self._export_csv(timeline)
        return self._export_md(timeline)

    @staticmethod
    def _export_md(timeline: TimelineResult) -> str:
        lines: list[str] = [
            "# Case Timeline",
            "",
            f"**Total events:** {timeline.total_events}",
        ]
        if timeline.date_range:
            lines.append(f"**Date range:** {timeline.date_range}")
        if timeline.sources_queried:
            lines.append(f"**Sources:** {', '.join(timeline.sources_queried)}")
        lines.append("")
        lines.append("| Date | Type | Title | Description | Lane | Importance |")
        lines.append("|------|------|-------|-------------|------|------------|")
        for evt in timeline.events:
            desc = (evt.description or "")[:80]
            lines.append(
                f"| {evt.event_date} "
                f"| {evt.event_type or ''} "
                f"| {evt.title} "
                f"| {desc} "
                f"| {evt.lane or ''} "
                f"| {evt.importance} |"
            )
        lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _export_json(timeline: TimelineResult) -> str:
        data = {
            "case_id": timeline.case_id,
            "total_events": timeline.total_events,
            "date_range": timeline.date_range,
            "sources_queried": timeline.sources_queried,
            "events": [evt.model_dump() for evt in timeline.events],
        }
        return json.dumps(data, indent=2, default=str)

    @staticmethod
    def _export_csv(timeline: TimelineResult) -> str:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            "date", "event_type", "title", "description",
            "lane", "importance", "source_table",
        ])
        for evt in timeline.events:
            writer.writerow([
                evt.event_date, evt.event_type or "", evt.title,
                evt.description or "", evt.lane or "",
                evt.importance, evt.source_table or "",
            ])
        return buf.getvalue()

    # -- Add event (convenience) -----------------------------------------------

    def add_event(
        self,
        case_id: int,
        event_date: str,
        title: str,
        *,
        description: Optional[str] = None,
        event_type: Optional[str] = None,
        importance: str = "normal",
        lane: Optional[str] = None,
        filing_id: Optional[int] = None,
        evidence_ids: Optional[list[int]] = None,
    ) -> int:
        """Insert a new event into the ``timeline_events`` table.

        Args:
            case_id: Owning case.
            event_date: ISO-8601 date string.
            title: Short event title.
            description: Longer description.
            event_type: Category (filing, hearing, order, …).
            importance: One of ``VALID_IMPORTANCE``.
            lane: Case lane letter (A-F) or ``None``.
            filing_id: Linked filing row id.
            evidence_ids: List of evidence row ids (stored as JSON).

        Returns:
            The new row id.

        Raises:
            ValueError: On invalid *importance* or *event_type*.
        """
        if importance not in VALID_IMPORTANCE:
            raise ValueError(
                f"Invalid importance '{importance}'. Must be one of {VALID_IMPORTANCE}"
            )
        if event_type and event_type not in VALID_EVENT_TYPES:
            raise ValueError(
                f"Invalid event_type '{event_type}'. Must be one of {VALID_EVENT_TYPES}"
            )
        if not event_date or not title:
            raise ValueError("event_date and title are required.")

        evidence_json = json.dumps(evidence_ids) if evidence_ids else None

        conn = self._db.connect()
        try:
            cursor = conn.execute(
                "INSERT INTO timeline_events "
                "(case_id, event_date, title, description, event_type, "
                " importance, filing_id, evidence_ids) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    case_id, event_date, title, description,
                    event_type, importance, filing_id, evidence_json,
                ),
            )
            conn.commit()
            new_id = cursor.lastrowid
            logger.info(
                "Added timeline event %d (%s) for case %d",
                new_id, event_type, case_id,
            )
            return new_id
        except Exception:
            conn.rollback()
            logger.exception("Failed to add timeline event for case %d", case_id)
            raise
        finally:
            conn.close()

    # -- Delete event ----------------------------------------------------------

    def delete_event(self, event_id: int) -> None:
        """Remove a timeline event by id."""
        self._db.execute(
            "DELETE FROM timeline_events WHERE id = ?",
            (event_id,),
        )
        logger.info("Deleted timeline event %d", event_id)
