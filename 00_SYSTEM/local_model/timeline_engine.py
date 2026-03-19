"""
THE MANBEARPIG — Timeline Reconstruction Engine (EPOCH v1.0)
Merges temporal data from all litigation tables into a unified,
court-ready chronology for Pigors v. Watson consolidated cases.

Stdlib only: sqlite3, re, json, datetime, collections, os
"""

import os
import re
import json
import sqlite3
from datetime import datetime, timedelta, date
from collections import defaultdict, OrderedDict

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH", r"C:\Users\andre\LitigationOS\litigation_context.db"
)

# Case-ID to lane mapping
CASE_LANE_MAP = {
    "2024-001507-DC": "A",
    "2023-5907-PP": "D",
    "COA-366810": "F",
    "JTC-001": "E",
    "MSC-ORIGINAL": "E",
    "SHADY-OAKS": "B",
    "CIVIL-CONSPIRACY": "C",
    "USDC-1983": "C",
}

# Direct single-letter lane IDs already in the DB
DIRECT_LANE_IDS = {"A", "B", "C", "D", "E", "F", "G"}

# Date-extraction regex patterns (ordered by specificity)
_DATE_PATTERNS = [
    # ISO: 2024-06-15 or 2024-06-15T12:00:00 or 2024-06-15 12:00:00
    re.compile(r'\b(\d{4})-(\d{1,2})-(\d{1,2})(?:[T ]\d{2}:\d{2}(?::\d{2})?)?\b'),
    # US: MM/DD/YYYY
    re.compile(r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b'),
    # US short: MM/DD/YY
    re.compile(r'\b(\d{1,2})/(\d{1,2})/(\d{2})\b'),
    # Long: January 15, 2024 or Jan 15, 2024
    re.compile(
        r'\b(January|February|March|April|May|June|July|August|September|'
        r'October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|'
        r'Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})\b',
        re.IGNORECASE,
    ),
]

_MONTH_NAMES = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

# Known separation start date (ex parte order suspending parenting time)
SEPARATION_START = date(2024, 7, 1)


def _safe_date(year, month, day):
    """Return a date object or None if values are out of range."""
    try:
        y = int(year)
        m = int(month)
        d = int(day)
        if y < 100:
            y += 2000
        if not (1 <= m <= 12 and 1 <= d <= 31 and 1900 <= y <= 2100):
            return None
        return date(y, m, d)
    except (ValueError, TypeError, OverflowError):
        return None


def parse_date(text):
    """Parse a date string trying multiple formats. Returns date or None."""
    if not text:
        return None
    text = str(text).strip()

    # Fast path: direct ISO
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S",
                "%m/%d/%Y", "%m/%d/%y", "%B %d, %Y", "%b %d, %Y",
                "%B %d %Y", "%b %d %Y"):
        try:
            return datetime.strptime(text[:19] if "T" in text or " " in text else text, fmt).date()
        except (ValueError, TypeError):
            continue

    # Regex fallback: ISO
    m = _DATE_PATTERNS[0].search(text)
    if m:
        return _safe_date(m.group(1), m.group(2), m.group(3))

    # Regex fallback: MM/DD/YYYY
    m = _DATE_PATTERNS[1].search(text)
    if m:
        return _safe_date(m.group(3), m.group(1), m.group(2))

    # Regex fallback: MM/DD/YY
    m = _DATE_PATTERNS[2].search(text)
    if m:
        return _safe_date(m.group(3), m.group(1), m.group(2))

    # Regex fallback: Month DD, YYYY
    m = _DATE_PATTERNS[3].search(text)
    if m:
        month_num = _MONTH_NAMES.get(m.group(1).lower())
        if month_num:
            return _safe_date(m.group(3), month_num, m.group(2))

    return None


def extract_dates_from_text(text):
    """Extract all dates found in a free-text string."""
    if not text:
        return []
    text = str(text)
    found = []

    for pat in _DATE_PATTERNS:
        for m in pat.finditer(text):
            groups = m.groups()
            if pat is _DATE_PATTERNS[0]:
                d = _safe_date(groups[0], groups[1], groups[2])
            elif pat in (_DATE_PATTERNS[1], _DATE_PATTERNS[2]):
                d = _safe_date(groups[2], groups[0], groups[1])
            elif pat is _DATE_PATTERNS[3]:
                month_num = _MONTH_NAMES.get(groups[0].lower())
                d = _safe_date(groups[2], month_num, groups[1]) if month_num else None
            else:
                d = None
            if d:
                found.append(d)
    return sorted(set(found))


def _resolve_lane(case_id):
    """Map a case_id to a lane letter (A-F) or 'UNKNOWN'."""
    if not case_id:
        return "UNKNOWN"
    cid = str(case_id).strip().upper()
    if cid in DIRECT_LANE_IDS:
        return cid
    for prefix, lane in CASE_LANE_MAP.items():
        if prefix.upper() in cid or cid in prefix.upper():
            return lane
    return "UNKNOWN"


class TimelineEngine:
    """Unified Timeline Reconstruction Engine for Pigors v. Watson."""

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._error_log = []

    # ------------------------------------------------------------------
    # Database helpers
    # ------------------------------------------------------------------

    def _get_db(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA query_only=ON")
        conn.row_factory = sqlite3.Row
        return conn

    def _query(self, sql, params=(), one=False):
        """Execute a read query with retry logic."""
        last_err = None
        for attempt in range(3):
            try:
                conn = self._get_db()
                try:
                    cur = conn.execute(sql, params)
                    rows = [dict(r) for r in (cur.fetchall() if not one else [cur.fetchone() or {}])]
                    return rows[0] if one else rows
                finally:
                    conn.close()
            except Exception as exc:
                last_err = exc
                self._error_log.append(f"query attempt {attempt}: {exc}")
                import time
                time.sleep(min(2 ** attempt, 4))
        self._error_log.append(f"query failed after retries: {last_err}")
        return {} if one else []

    # ------------------------------------------------------------------
    # Event collectors (one per source table)
    # ------------------------------------------------------------------

    def _collect_docket_events(self):
        """Collect events from docket_events table."""
        rows = self._query(
            "SELECT event_date_iso, title, event_type, summary, case_id "
            "FROM docket_events WHERE event_date_iso IS NOT NULL"
        )
        events = []
        for r in rows:
            d = parse_date(r.get("event_date_iso"))
            if d:
                events.append({
                    "date": d,
                    "description": r.get("title", ""),
                    "detail": r.get("summary", ""),
                    "source_table": "docket_events",
                    "lane": _resolve_lane(r.get("case_id")),
                    "event_type": r.get("event_type", "docket"),
                    "conflict_flag": False,
                    "related_items": [],
                })
        return events

    def _collect_deadlines(self):
        """Collect events from deadlines table."""
        rows = self._query(
            "SELECT due_date_iso, title, basis_authority, status, case_id "
            "FROM deadlines WHERE due_date_iso IS NOT NULL"
        )
        events = []
        for r in rows:
            d = parse_date(r.get("due_date_iso"))
            if d:
                authority = r.get("basis_authority", "") or ""
                status = r.get("status", "") or ""
                events.append({
                    "date": d,
                    "description": f"[DEADLINE] {r.get('title', '')}",
                    "detail": f"Authority: {authority} | Status: {status}",
                    "source_table": "deadlines",
                    "lane": _resolve_lane(r.get("case_id")),
                    "event_type": "deadline",
                    "conflict_flag": False,
                    "related_items": [],
                })
        return events

    def _collect_evidence_quotes(self):
        """Collect temporal events from evidence_quotes (date_ref + text)."""
        rows = self._query(
            "SELECT id, date_ref, quote_text, evidence_category, speaker, "
            "legal_significance FROM evidence_quotes"
        )
        events = []
        for r in rows:
            # Primary: use date_ref column
            d = parse_date(r.get("date_ref"))
            if d:
                events.append({
                    "date": d,
                    "description": f"[EVIDENCE] {(r.get('evidence_category') or 'QUOTE').upper()}"
                                   f" — {(r.get('speaker') or 'Unknown')}",
                    "detail": str(r.get("quote_text", ""))[:300],
                    "source_table": "evidence_quotes",
                    "lane": "UNKNOWN",
                    "event_type": "evidence",
                    "conflict_flag": False,
                    "related_items": [f"evidence_quotes.id={r.get('id')}"],
                })
            else:
                # Fallback: extract dates from quote_text
                text = r.get("quote_text", "") or ""
                for extracted in extract_dates_from_text(text):
                    events.append({
                        "date": extracted,
                        "description": f"[EVIDENCE-REF] {(r.get('evidence_category') or 'QUOTE').upper()}"
                                       f" — {(r.get('speaker') or 'Unknown')}",
                        "detail": text[:200],
                        "source_table": "evidence_quotes",
                        "lane": "UNKNOWN",
                        "event_type": "evidence_ref",
                        "conflict_flag": False,
                        "related_items": [f"evidence_quotes.id={r.get('id')}"],
                    })
        return events

    def _collect_contradictions(self):
        """Collect temporal references from contradiction_map."""
        rows = self._query(
            "SELECT id, source_a_text, source_b_text, contradiction_type, "
            "severity, legal_impact FROM contradiction_map"
        )
        events = []
        for r in rows:
            dates_a = extract_dates_from_text(r.get("source_a_text"))
            dates_b = extract_dates_from_text(r.get("source_b_text"))
            all_dates = sorted(set(dates_a + dates_b))
            for d in all_dates:
                events.append({
                    "date": d,
                    "description": f"[CONTRADICTION] {r.get('contradiction_type', '')} "
                                   f"(severity: {r.get('severity', '')})",
                    "detail": str(r.get("legal_impact", ""))[:300],
                    "source_table": "contradiction_map",
                    "lane": "UNKNOWN",
                    "event_type": "contradiction",
                    "conflict_flag": True,
                    "related_items": [f"contradiction_map.id={r.get('id')}"],
                })
        return events

    def _collect_impeachment(self):
        """Collect temporal references from impeachment_items."""
        rows = self._query(
            "SELECT id, speaker, statement, contradicting_text, severity "
            "FROM impeachment_items"
        )
        events = []
        for r in rows:
            dates_stmt = extract_dates_from_text(r.get("statement"))
            dates_contra = extract_dates_from_text(r.get("contradicting_text"))
            all_dates = sorted(set(dates_stmt + dates_contra))
            for d in all_dates:
                events.append({
                    "date": d,
                    "description": f"[IMPEACHMENT] {r.get('speaker', 'Unknown')} "
                                   f"(severity: {r.get('severity', '')})",
                    "detail": str(r.get("statement", ""))[:200],
                    "source_table": "impeachment_items",
                    "lane": "UNKNOWN",
                    "event_type": "impeachment",
                    "conflict_flag": True,
                    "related_items": [f"impeachment_items.id={r.get('id')}"],
                })
        return events

    def _collect_judicial_violations(self):
        """Collect events from judicial_violations table."""
        rows = self._query(
            "SELECT violation_id, judge_name, canon_number, "
            "violation_description, severity, created_at "
            "FROM judicial_violations WHERE created_at IS NOT NULL"
        )
        events = []
        for r in rows:
            d = parse_date(r.get("created_at"))
            if d:
                events.append({
                    "date": d,
                    "description": f"[JUDICIAL VIOLATION] Canon {r.get('canon_number', '?')} "
                                   f"— {r.get('judge_name', '')}",
                    "detail": str(r.get("violation_description", ""))[:300],
                    "source_table": "judicial_violations",
                    "lane": "E",
                    "event_type": "judicial_violation",
                    "conflict_flag": False,
                    "related_items": [
                        f"judicial_violations.violation_id={r.get('violation_id')}"
                    ],
                })
        return events

    # ------------------------------------------------------------------
    # Core timeline builder
    # ------------------------------------------------------------------

    def build_unified_timeline(self, start_date=None, end_date=None, lanes=None):
        """
        Build a unified, sorted timeline merging all source tables.

        Args:
            start_date: Filter start (str or date). Inclusive.
            end_date:   Filter end (str or date). Inclusive.
            lanes:      List of lane letters to include (e.g. ['A','D','F']).
                        None = all lanes.

        Returns:
            List of TimelineEvent dicts sorted by date ascending.
        """
        start = parse_date(start_date) if isinstance(start_date, str) else start_date
        end = parse_date(end_date) if isinstance(end_date, str) else end_date

        # Collect from all sources
        all_events = []
        collectors = [
            self._collect_docket_events,
            self._collect_deadlines,
            self._collect_evidence_quotes,
            self._collect_contradictions,
            self._collect_impeachment,
            self._collect_judicial_violations,
        ]
        for collector in collectors:
            try:
                all_events.extend(collector())
            except Exception as exc:
                self._error_log.append(f"{collector.__name__}: {exc}")

        # Filter by date range
        if start:
            all_events = [e for e in all_events if e["date"] >= start]
        if end:
            all_events = [e for e in all_events if e["date"] <= end]

        # Filter by lanes
        if lanes:
            lane_set = {l.upper() for l in lanes}
            all_events = [e for e in all_events if e["lane"] in lane_set or e["lane"] == "UNKNOWN"]

        # Sort by date, then source table for stability
        all_events.sort(key=lambda e: (e["date"], e["source_table"], e["description"]))

        # Mark conflict zones: dates that have contradiction or impeachment items
        conflict_dates = {
            e["date"] for e in all_events if e["event_type"] in ("contradiction", "impeachment")
        }
        for e in all_events:
            if e["date"] in conflict_dates:
                e["conflict_flag"] = True

        return all_events

    # ------------------------------------------------------------------
    # Temporal anomaly detection
    # ------------------------------------------------------------------

    def find_temporal_anomalies(self):
        """
        Detect temporal anomalies in the litigation record:
        - Same-day ex parte orders (impossibly fast)
        - Long gaps with no proceedings
        - Orders on dates with no scheduled hearing
        - Date inconsistencies between sources
        """
        timeline = self.build_unified_timeline()
        anomalies = []

        if not timeline:
            return anomalies

        # Index events by date
        by_date = defaultdict(list)
        for e in timeline:
            by_date[e["date"]].append(e)

        # --- 1. Same-day anomalies (hearing + order on same date) ---
        for dt, events in by_date.items():
            types = {e["event_type"] for e in events}
            descs = " ".join(e["description"].lower() for e in events)
            if ("hearing" in descs or "ex parte" in descs) and "order" in types:
                anomalies.append({
                    "type": "SAME_DAY_ORDER",
                    "date": dt,
                    "description": "Order issued same day as hearing/ex parte proceeding",
                    "severity": "HIGH",
                    "events": [e["description"] for e in events],
                })

        # --- 2. Gaps in proceedings (>60 days between docket events) ---
        docket_dates = sorted(
            {e["date"] for e in timeline if e["source_table"] == "docket_events"}
        )
        for i in range(1, len(docket_dates)):
            gap = (docket_dates[i] - docket_dates[i - 1]).days
            if gap > 60:
                anomalies.append({
                    "type": "PROCEEDING_GAP",
                    "date": docket_dates[i - 1],
                    "description": f"{gap}-day gap in proceedings "
                                   f"({docket_dates[i-1]} to {docket_dates[i]})",
                    "severity": "MEDIUM" if gap < 120 else "HIGH",
                    "events": [],
                })

        # --- 3. Orders on dates with no hearing ---
        order_dates = {
            e["date"] for e in timeline
            if e["source_table"] == "docket_events" and e.get("event_type") == "order"
        }
        hearing_dates = {
            e["date"] for e in timeline
            if e["source_table"] == "docket_events" and "hearing" in (e.get("event_type") or "").lower()
        }
        for od in order_dates - hearing_dates:
            descs = [e["description"] for e in by_date.get(od, [])
                     if e["source_table"] == "docket_events"]
            anomalies.append({
                "type": "ORDER_NO_HEARING",
                "date": od,
                "description": f"Order issued on {od} with no hearing on that date",
                "severity": "MEDIUM",
                "events": descs,
            })

        # --- 4. Date inconsistencies (same event, different dates in sources) ---
        # Look for evidence/contradiction items on docket-event dates
        contradiction_events = [
            e for e in timeline if e["event_type"] == "contradiction"
        ]
        for ce in contradiction_events:
            docket_on_date = [
                e for e in by_date.get(ce["date"], [])
                if e["source_table"] == "docket_events"
            ]
            if docket_on_date:
                anomalies.append({
                    "type": "DATE_INCONSISTENCY",
                    "date": ce["date"],
                    "description": f"Contradiction found for date with docket activity: {ce['date']}",
                    "severity": "HIGH",
                    "events": [ce["description"]] + [d["description"] for d in docket_on_date],
                })

        # Sort by date
        anomalies.sort(key=lambda a: a["date"])
        return anomalies

    # ------------------------------------------------------------------
    # Separation timeline
    # ------------------------------------------------------------------

    def build_separation_timeline(self, separation_start=None):
        """
        Build a focused timeline tracking parent-child separation.

        Tracks every event from the separation start date to present,
        tagging events that extended or could have ended the separation.

        References:
            - MCL 722.27a (parenting time)
            - Troxel v Granville, 530 US 57 (2000) (fundamental parental rights)
        """
        sep_start = separation_start or SEPARATION_START
        today = date.today()
        days_separated = (today - sep_start).days

        timeline = self.build_unified_timeline(
            start_date=sep_start, end_date=today
        )

        # Tag separation-relevant events
        separation_keywords = [
            "parenting", "custody", "visitation", "contact", "separation",
            "suspend", "restrict", "reunif", "child", "parent", "ex parte",
            "ppo", "protection", "access",
        ]

        separation_events = []
        for e in timeline:
            text = f"{e['description']} {e.get('detail', '')}".lower()
            relevant = any(kw in text for kw in separation_keywords)
            entry = dict(e)
            entry["separation_relevant"] = relevant
            entry["day_number"] = (e["date"] - sep_start).days
            separation_events.append(entry)

        return {
            "separation_start": sep_start.isoformat(),
            "current_date": today.isoformat(),
            "days_separated": days_separated,
            "total_events": len(separation_events),
            "separation_relevant_count": sum(
                1 for e in separation_events if e["separation_relevant"]
            ),
            "legal_authority": [
                "MCL 722.27a — Parenting time",
                "Troxel v Granville, 530 US 57 (2000) — Fundamental parental rights",
                "MCL 722.23(j) — Factor J: willingness to facilitate parent-child relationship",
            ],
            "events": separation_events,
        }

    # ------------------------------------------------------------------
    # Date clustering
    # ------------------------------------------------------------------

    def find_date_clusters(self, window_days=7):
        """
        Find clusters of activity (multiple events within N days).
        Often reveals coordinated actions (e.g., multiple filings +
        orders in the same week).

        Returns list of clusters, each with date range, event count,
        and the events within.
        """
        timeline = self.build_unified_timeline()
        if not timeline:
            return []

        clusters = []
        used = set()

        for i, event in enumerate(timeline):
            if i in used:
                continue
            cluster_events = [event]
            used.add(i)

            for j in range(i + 1, len(timeline)):
                if j in used:
                    continue
                if (timeline[j]["date"] - event["date"]).days <= window_days:
                    cluster_events.append(timeline[j])
                    used.add(j)
                elif (timeline[j]["date"] - event["date"]).days > window_days:
                    break

            if len(cluster_events) >= 3:
                cluster_start = cluster_events[0]["date"]
                cluster_end = cluster_events[-1]["date"]
                lanes_involved = sorted({e["lane"] for e in cluster_events})
                sources = sorted({e["source_table"] for e in cluster_events})
                has_conflict = any(e["conflict_flag"] for e in cluster_events)

                clusters.append({
                    "start_date": cluster_start.isoformat(),
                    "end_date": cluster_end.isoformat(),
                    "span_days": (cluster_end - cluster_start).days,
                    "event_count": len(cluster_events),
                    "lanes": lanes_involved,
                    "source_tables": sources,
                    "has_conflicts": has_conflict,
                    "events": cluster_events,
                })

        # Sort by event count descending (densest clusters first)
        clusters.sort(key=lambda c: c["event_count"], reverse=True)
        return clusters

    # ------------------------------------------------------------------
    # Court-ready chronology
    # ------------------------------------------------------------------

    def generate_chronology_section(self, start_date=None, end_date=None):
        """
        Generate a court-filing-ready chronology section with numbered
        paragraphs, dates, events, and record citations.

        Format: "XX. On [date], [event]. [citation to record]."
        """
        timeline = self.build_unified_timeline(
            start_date=start_date, end_date=end_date
        )

        # Deduplicate: keep only docket_events and deadlines for chronology
        # (evidence/contradiction refs are too noisy for a filing section)
        filing_sources = {"docket_events", "deadlines", "judicial_violations"}
        chronology_events = [
            e for e in timeline if e["source_table"] in filing_sources
        ]

        lines = []
        lines.append("STATEMENT OF FACTS — CHRONOLOGY")
        lines.append("")

        for idx, event in enumerate(chronology_events, start=1):
            dt_str = event["date"].strftime("%B %d, %Y")
            desc = event["description"].replace("[DEADLINE] ", "").replace(
                "[JUDICIAL VIOLATION] ", ""
            )
            detail = event.get("detail", "")

            # Build citation reference
            if event["source_table"] == "docket_events":
                cite = f"(Docket Entry, {dt_str})"
            elif event["source_table"] == "deadlines":
                authority = detail.split("Authority: ")[-1].split(" |")[0] if "Authority:" in detail else ""
                cite = f"({authority})" if authority else "(Court Deadline)"
            elif event["source_table"] == "judicial_violations":
                cite = "(Judicial Conduct Record)"
            else:
                cite = f"({event['source_table']})"

            line = f"    {idx}. On {dt_str}, {desc}. {cite}"
            lines.append(line)

        lines.append("")
        lines.append(f"    [Total chronology entries: {len(chronology_events)}]")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Key dates
    # ------------------------------------------------------------------

    def get_key_dates(self):
        """
        Return the most important dates in the case:
        filing dates, hearing dates, order dates, separation start,
        appeal filing date, and upcoming deadlines.
        """
        timeline = self.build_unified_timeline()
        today = date.today()

        result = {
            "separation_start": SEPARATION_START.isoformat(),
            "days_since_separation": (today - SEPARATION_START).days,
            "filing_dates": [],
            "hearing_dates": [],
            "order_dates": [],
            "appeal_dates": [],
            "upcoming_deadlines": [],
            "past_deadlines": [],
        }

        for e in timeline:
            entry = {"date": e["date"].isoformat(), "description": e["description"], "lane": e["lane"]}
            etype = (e.get("event_type") or "").lower()
            desc_lower = e["description"].lower()

            if etype == "filing" or "filed" in desc_lower or "complaint" in desc_lower:
                result["filing_dates"].append(entry)
            elif "hearing" in etype or "hearing" in desc_lower:
                result["hearing_dates"].append(entry)
            elif etype == "order" or "order" in desc_lower:
                result["order_dates"].append(entry)

            if e["lane"] == "F" or "appeal" in desc_lower or "coa" in desc_lower:
                result["appeal_dates"].append(entry)

            if e["source_table"] == "deadlines":
                if e["date"] >= today:
                    result["upcoming_deadlines"].append(entry)
                else:
                    result["past_deadlines"].append(entry)

        # Sort upcoming deadlines by date (soonest first)
        result["upcoming_deadlines"].sort(key=lambda x: x["date"])
        return result

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_timeline(self, format="dict", start_date=None, end_date=None):
        """
        Export the unified timeline.

        Args:
            format: 'dict' returns list of dicts, 'json' returns JSON string,
                    'text' returns human-readable text.
            start_date: Optional start filter.
            end_date:   Optional end filter.
        """
        timeline = self.build_unified_timeline(
            start_date=start_date, end_date=end_date
        )

        if format == "dict":
            # Convert date objects to ISO strings for serialization safety
            out = []
            for e in timeline:
                entry = dict(e)
                entry["date"] = e["date"].isoformat()
                out.append(entry)
            return out

        if format == "json":
            out = []
            for e in timeline:
                entry = dict(e)
                entry["date"] = e["date"].isoformat()
                out.append(entry)
            return json.dumps(out, indent=2, default=str)

        if format == "text":
            lines = []
            current_month = None
            for e in timeline:
                month_key = e["date"].strftime("%B %Y")
                if month_key != current_month:
                    lines.append(f"\n=== {month_key} ===")
                    current_month = month_key
                flag = " [!CONFLICT]" if e["conflict_flag"] else ""
                lines.append(
                    f"  {e['date'].isoformat()} | [{e['lane']}] "
                    f"{e['description']}{flag}"
                )
            return "\n".join(lines)

        raise ValueError(f"Unsupported format: {format!r}. Use 'dict', 'json', or 'text'.")


# ======================================================================
# Main: build timeline and print key stats
# ======================================================================

if __name__ == "__main__":
    import time as _time

    print("=" * 70)
    print("THE MANBEARPIG — Timeline Reconstruction Engine")
    print("Pigors v. Watson — Consolidated Timeline Build")
    print("=" * 70)

    t0 = _time.time()
    engine = TimelineEngine()

    # 1. Unified timeline
    print("\n[1] Building unified timeline...")
    timeline = engine.build_unified_timeline()
    elapsed = _time.time() - t0
    print(f"    Total events:  {len(timeline)}")
    if timeline:
        print(f"    Date range:    {timeline[0]['date']} to {timeline[-1]['date']}")

    # Stats by source
    source_counts = defaultdict(int)
    lane_counts = defaultdict(int)
    for e in timeline:
        source_counts[e["source_table"]] += 1
        lane_counts[e["lane"]] += 1

    print("    By source:")
    for src, cnt in sorted(source_counts.items(), key=lambda x: -x[1]):
        print(f"      {src:30s} {cnt:>5d}")
    print("    By lane:")
    for lane, cnt in sorted(lane_counts.items()):
        print(f"      Lane {lane:10s} {cnt:>5d}")

    # 2. Conflict zones
    conflicts = [e for e in timeline if e["conflict_flag"]]
    print(f"\n[2] Conflict zones: {len(conflicts)} events flagged")

    # 3. Anomalies
    print("\n[3] Temporal anomalies...")
    anomalies = engine.find_temporal_anomalies()
    print(f"    Found: {len(anomalies)} anomalies")
    for a in anomalies[:5]:
        print(f"    - [{a['severity']}] {a['type']}: {a['description']}")
    if len(anomalies) > 5:
        print(f"    ... and {len(anomalies) - 5} more")

    # 4. Separation timeline
    print("\n[4] Separation timeline...")
    sep = engine.build_separation_timeline()
    print(f"    Days separated: {sep['days_separated']}")
    print(f"    Total events:   {sep['total_events']}")
    print(f"    Relevant events: {sep['separation_relevant_count']}")

    # 5. Clusters
    print("\n[5] Date clusters (7-day window)...")
    clusters = engine.find_date_clusters(window_days=7)
    print(f"    Found: {len(clusters)} clusters")
    for c in clusters[:3]:
        print(f"    - {c['start_date']} to {c['end_date']}: "
              f"{c['event_count']} events, lanes={c['lanes']}")

    # 6. Key dates
    print("\n[6] Key dates...")
    kd = engine.get_key_dates()
    print(f"    Days since separation: {kd['days_since_separation']}")
    print(f"    Filing dates:   {len(kd['filing_dates'])}")
    print(f"    Hearing dates:  {len(kd['hearing_dates'])}")
    print(f"    Order dates:    {len(kd['order_dates'])}")
    print(f"    Upcoming deadlines: {len(kd['upcoming_deadlines'])}")
    for dl in kd["upcoming_deadlines"][:3]:
        print(f"      - {dl['date']}: {dl['description']}")

    # 7. Errors
    if engine._error_log:
        print(f"\n[!] Errors encountered: {len(engine._error_log)}")
        for err in engine._error_log[:5]:
            print(f"    - {err}")

    print(f"\n[Done] Built in {_time.time() - t0:.2f}s")
    print("=" * 70)
