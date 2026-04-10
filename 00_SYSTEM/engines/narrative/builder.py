"""
Core Narrative Builder — constructs chronological narratives from
narrative_events for court filings.

Every connection uses PRAGMA busy_timeout=60000, journal_mode=WAL,
cache_size=-32000. FTS5 queries are sanitized before MATCH.
"""

import json
import logging
import re
import sqlite3
from datetime import date
from typing import List, Optional

from .models import NarrativeEvent, SeverityLevel, _dump_json_field

logger = logging.getLogger(__name__)

SEPARATION_DATE = date(2025, 7, 29)

INSERT_SQL = """
INSERT INTO narrative_events (
    event_date, event_summary, detailed_narrative, lane,
    claim_elements, evidence_refs, timeline_event_ids, exhibit_refs,
    legal_significance, actors, severity, narrative_order, tags
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

COLUMNS = [
    "id", "event_date", "event_summary", "detailed_narrative", "lane",
    "claim_elements", "evidence_refs", "timeline_event_ids", "exhibit_refs",
    "legal_significance", "actors", "severity", "narrative_order",
    "created_at", "tags",
]


def _safe_fts5(query: str) -> str:
    """Sanitize a query for FTS5 MATCH to prevent syntax errors."""
    return re.sub(r'[^\w\s*"]', " ", query).strip()


def _get_conn(db_path: str) -> sqlite3.Connection:
    """Open a DB connection with required PRAGMAs."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    return conn


class NarrativeBuilder:
    """Builds chronological narratives from narrative_events for court filings."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_statement_of_facts(
        self,
        lane: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        severity_min: str = "low",
    ) -> str:
        """Generate a court-ready Statement of Facts section.

        Returns formatted text with numbered paragraphs, evidence citations,
        and exhibit references in chronological order.
        """
        events = self._query_events(lane=lane, date_from=date_from,
                                    date_to=date_to, severity_min=severity_min)
        if not events:
            return "No narrative events found for the specified criteria."

        sep_days = self.get_separation_counter()
        lines: list[str] = []
        lines.append("STATEMENT OF FACTS")
        lines.append("")

        for idx, ev in enumerate(events, start=1):
            para = f"    {idx}. "
            if ev.detailed_narrative:
                para += ev.detailed_narrative
            else:
                para += ev.event_summary

            # Append exhibit references inline
            if ev.exhibit_refs:
                refs_str = "; ".join(ev.exhibit_refs)
                para += f" ({refs_str}.)"

            lines.append(para)
            lines.append("")

        lines.append(
            f"    As of the date of this filing, Plaintiff-Father has been "
            f"completely separated from the minor child, L.D.W., for "
            f"{sep_days} consecutive days — since July 29, 2025."
        )
        return "\n".join(lines)

    def build_claim_narrative(self, claim_element: str) -> str:
        """Build narrative for a specific legal claim element.

        E.g., 'MCL 722.23(j)' returns all events proving factor j.
        """
        conn = _get_conn(self.db_path)
        try:
            pattern = f"%{claim_element}%"
            rows = conn.execute(
                f"SELECT {', '.join(COLUMNS)} FROM narrative_events "
                "WHERE claim_elements LIKE ? "
                "ORDER BY event_date ASC",
                (pattern,),
            ).fetchall()
            events = [NarrativeEvent.from_row(r, COLUMNS) for r in rows]
        finally:
            conn.close()

        if not events:
            return f"No narrative events found for claim element: {claim_element}"

        lines: list[str] = [f"NARRATIVE FOR CLAIM: {claim_element}", ""]
        for idx, ev in enumerate(events, start=1):
            text = ev.detailed_narrative or ev.event_summary
            significance = f" [{ev.legal_significance}]" if ev.legal_significance else ""
            lines.append(f"    {idx}. [{ev.event_date}] {text}{significance}")
            lines.append("")
        return "\n".join(lines)

    def build_defendant_narrative(self, defendant: str) -> str:
        """Build chronological narrative of a specific defendant's conduct."""
        conn = _get_conn(self.db_path)
        try:
            pattern = f"%{defendant}%"
            rows = conn.execute(
                f"SELECT {', '.join(COLUMNS)} FROM narrative_events "
                "WHERE actors LIKE ? "
                "ORDER BY event_date ASC",
                (pattern,),
            ).fetchall()
            events = [NarrativeEvent.from_row(r, COLUMNS) for r in rows]
        finally:
            conn.close()

        if not events:
            return f"No narrative events found for defendant: {defendant}"

        lines: list[str] = [
            f"CHRONOLOGICAL CONDUCT OF {defendant.upper()}", ""
        ]
        for idx, ev in enumerate(events, start=1):
            text = ev.detailed_narrative or ev.event_summary
            lines.append(f"    {idx}. [{ev.event_date}] {text}")
            if ev.legal_significance:
                lines.append(f"       Legal significance: {ev.legal_significance}")
            lines.append("")
        return "\n".join(lines)

    def get_separation_counter(self) -> int:
        """Calculate days since last contact (July 29, 2025). Always dynamic."""
        return (date.today() - SEPARATION_DATE).days

    def link_evidence_to_timeline(self) -> int:
        """Auto-link evidence_quotes to timeline_events by date proximity
        and content similarity.  Updates narrative_events with discovered
        evidence_refs.  Returns count of events updated.
        """
        conn = _get_conn(self.db_path)
        updated = 0
        try:
            rows = conn.execute(
                f"SELECT {', '.join(COLUMNS)} FROM narrative_events "
                "ORDER BY event_date ASC"
            ).fetchall()
            events = [NarrativeEvent.from_row(r, COLUMNS) for r in rows]

            for ev in events:
                new_refs = list(ev.evidence_refs)

                # Search by date proximity (same day ±1 day)
                dt = ev.date_obj()
                if dt:
                    date_str = dt.isoformat()
                    eq_rows = conn.execute(
                        "SELECT id FROM evidence_quotes "
                        "WHERE created_at LIKE ? LIMIT 10",
                        (f"{date_str}%",),
                    ).fetchall()
                    for er in eq_rows:
                        ref = str(er[0])
                        if ref not in new_refs:
                            new_refs.append(ref)

                # Search by keyword overlap from event_summary
                keywords = _extract_keywords(ev.event_summary)
                for kw in keywords[:3]:
                    safe = _safe_fts5(kw)
                    if not safe or len(safe) < 4:
                        continue
                    try:
                        eq_rows = conn.execute(
                            "SELECT id FROM evidence_quotes "
                            "WHERE quote_text LIKE ? LIMIT 5",
                            (f"%{kw}%",),
                        ).fetchall()
                        for er in eq_rows:
                            ref = str(er[0])
                            if ref not in new_refs:
                                new_refs.append(ref)
                    except sqlite3.OperationalError:
                        logger.debug("Keyword search failed for: %s", kw)

                if len(new_refs) > len(ev.evidence_refs):
                    conn.execute(
                        "UPDATE narrative_events SET evidence_refs = ? WHERE id = ?",
                        (_dump_json_field(new_refs), ev.id),
                    )
                    updated += 1

            conn.commit()
            logger.info("Updated evidence links for %d narrative events", updated)
        finally:
            conn.close()
        return updated

    def generate_exhibit_list(self, lane: Optional[str] = None) -> list:
        """Generate ordered exhibit list from narrative events."""
        events = self._query_events(lane=lane, severity_min="low")
        exhibits: list[dict] = []
        seen: set[str] = set()
        letter_idx = 0

        for ev in events:
            for ref in ev.exhibit_refs:
                if ref in seen:
                    continue
                seen.add(ref)
                letter = chr(ord("A") + letter_idx) if letter_idx < 26 else f"A{letter_idx - 25}"
                exhibits.append({
                    "label": f"Exhibit {letter}",
                    "description": ref,
                    "event_date": ev.event_date,
                    "event_summary": ev.event_summary,
                    "lane": ev.lane,
                })
                letter_idx += 1

        return exhibits

    def insert_event(self, event: NarrativeEvent) -> int:
        """Insert a single narrative event and return its new ID."""
        conn = _get_conn(self.db_path)
        try:
            cur = conn.execute(INSERT_SQL, event.to_insert_tuple())
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def insert_events(self, events: List[NarrativeEvent]) -> int:
        """Bulk-insert narrative events. Returns count inserted."""
        conn = _get_conn(self.db_path)
        try:
            conn.executemany(INSERT_SQL, [e.to_insert_tuple() for e in events])
            conn.commit()
            return len(events)
        finally:
            conn.close()

    def get_event_count(self, lane: Optional[str] = None) -> int:
        """Return total narrative events, optionally filtered by lane."""
        conn = _get_conn(self.db_path)
        try:
            if lane:
                row = conn.execute(
                    "SELECT COUNT(*) FROM narrative_events WHERE lane = ?",
                    (lane,),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT COUNT(*) FROM narrative_events"
                ).fetchone()
            return row[0] if row else 0
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _query_events(
        self,
        lane: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        severity_min: str = "low",
    ) -> List[NarrativeEvent]:
        """Query narrative_events with optional filters, ordered chronologically."""
        conn = _get_conn(self.db_path)
        try:
            clauses: list[str] = []
            params: list = []

            severities = SeverityLevel.at_least(severity_min)
            placeholders = ", ".join("?" for _ in severities)
            clauses.append(f"severity IN ({placeholders})")
            params.extend(severities)

            if lane:
                clauses.append("lane LIKE ?")
                params.append(f"%{lane}%")
            if date_from:
                clauses.append("event_date >= ?")
                params.append(date_from)
            if date_to:
                clauses.append("event_date <= ?")
                params.append(date_to)

            where = " AND ".join(clauses) if clauses else "1=1"
            sql = (
                f"SELECT {', '.join(COLUMNS)} FROM narrative_events "
                f"WHERE {where} "
                "ORDER BY event_date ASC, narrative_order ASC"
            )
            rows = conn.execute(sql, params).fetchall()
            return [NarrativeEvent.from_row(r, COLUMNS) for r in rows]
        finally:
            conn.close()


def _extract_keywords(text: str) -> list:
    """Extract meaningful keywords from a summary for evidence matching."""
    stop = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "was", "were", "are", "be", "been",
        "being", "has", "had", "have", "do", "did", "does", "not", "no", "all",
        "that", "this", "it", "its", "as", "up", "out", "if", "about", "who",
        "which", "what", "when", "where", "how", "each", "she", "he", "his",
        "her", "they", "them", "their", "so", "than", "then", "into", "over",
    }
    words = re.findall(r"[A-Za-z]{4,}", text)
    return [w for w in words if w.lower() not in stop]
