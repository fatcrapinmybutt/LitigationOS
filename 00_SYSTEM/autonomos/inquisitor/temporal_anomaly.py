"""
DELTA99 Ω∞ — Temporal Anomaly Detector
========================================
Scans master_chronological_timeline and docket_events for suspicious timing
patterns: same-day filings + rulings, clustered adverse actions, impossible
timelines, coordination signatures between Watson/Berry/McNeill/Rusco.

Feeds: d99-counter-intel
"""
import sys
import sqlite3
import json
import time
import re
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict

_shared = Path(__file__).parent.parent / "shared"
if str(_shared) not in sys.path:
    sys.path.insert(0, str(_shared))

from autonomos_config import CENTRAL_DB

TEMPORAL_DB = Path(__file__).parent / "temporal_anomaly.db"

# ── Known Adversary Names ──────────────────────────────────────────
ADVERSARIES = {
    "Watson": ["watson", "emily", "emily watson", "emily a. watson"],
    "Berry": ["berry", "ron berry", "ronald berry"],
    "McNeill": ["mcneill", "jenny mcneill", "jenny l. mcneill", "judge mcneill"],
    "Rusco": ["rusco", "pamela rusco", "pam rusco"],
    "Barnes": ["barnes", "jennifer barnes"],
    "Albert_Watson": ["albert watson", "albert"],
    "Cody_Watson": ["cody watson", "cody"],
    "Martini": ["martini", "mandi martini"],
}

# Window thresholds
SAME_DAY_HOURS = 24
COORDINATION_WINDOW_DAYS = 2  # Watson files → McNeill rules within 48hrs
CLUSTER_WINDOW_DAYS = 7


def _init_db() -> sqlite3.Connection:
    TEMPORAL_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(TEMPORAL_DB), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS temporal_anomalies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            anomaly_type TEXT NOT NULL,
            severity TEXT DEFAULT 'MEDIUM',
            event_a TEXT DEFAULT '',
            event_a_date TEXT DEFAULT '',
            event_b TEXT DEFAULT '',
            event_b_date TEXT DEFAULT '',
            time_delta_hours REAL DEFAULT 0.0,
            actors_involved TEXT DEFAULT '',
            description TEXT DEFAULT '',
            detected_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_ta_type ON temporal_anomalies(anomaly_type);
        CREATE INDEX IF NOT EXISTS idx_ta_sev ON temporal_anomalies(severity);

        CREATE TABLE IF NOT EXISTS coordination_signatures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor_a TEXT NOT NULL,
            actor_b TEXT NOT NULL,
            action_a TEXT DEFAULT '',
            action_b TEXT DEFAULT '',
            date_a TEXT DEFAULT '',
            date_b TEXT DEFAULT '',
            hours_apart REAL DEFAULT 0.0,
            pattern_description TEXT DEFAULT '',
            detected_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS scan_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            events_scanned INTEGER DEFAULT 0,
            anomalies_found INTEGER DEFAULT 0,
            coordination_sigs INTEGER DEFAULT 0,
            duration_s REAL DEFAULT 0.0,
            run_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    return conn


@dataclass
class TimelineEvent:
    rowid: int
    date_str: str
    date_obj: datetime = None
    description: str = ""
    source: str = ""
    actors: list = field(default_factory=list)


def _parse_date(d: str) -> datetime | None:
    """Parse various date formats."""
    if not d:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%m/%d/%Y", "%m-%d-%Y",
                "%Y-%m-%d %H:%M:%S", "%B %d, %Y"):
        try:
            return datetime.strptime(str(d).strip()[:19], fmt)
        except (ValueError, TypeError):
            continue
    return None


def _extract_actors(text: str) -> list[str]:
    """Identify adversaries mentioned in text."""
    text_lower = text.lower()
    found = []
    for actor, aliases in ADVERSARIES.items():
        for alias in aliases:
            if alias in text_lower:
                found.append(actor)
                break
    return found


def _load_timeline(central: sqlite3.Connection) -> list[TimelineEvent]:
    """Load and parse timeline events."""
    events = []

    # From master_chronological_timeline
    try:
        rows = central.execute("""
            SELECT rowid, event_date, event_description, source
            FROM master_chronological_timeline
            ORDER BY event_date LIMIT 15000
        """).fetchall()
        for r in rows:
            evt = TimelineEvent(rowid=r[0], date_str=str(r[1] or ""),
                                description=str(r[2] or ""), source=str(r[3] or ""))
            evt.date_obj = _parse_date(evt.date_str)
            evt.actors = _extract_actors(evt.description)
            if evt.date_obj:
                events.append(evt)
    except sqlite3.Error:
        pass

    # From docket_events
    try:
        rows = central.execute("""
            SELECT rowid, event_date, event_description, event_type
            FROM docket_events
            ORDER BY event_date LIMIT 5000
        """).fetchall()
        for r in rows:
            evt = TimelineEvent(rowid=r[0] + 100000, date_str=str(r[1] or ""),
                                description=str(r[2] or ""), source=f"docket:{r[3] or ''}")
            evt.date_obj = _parse_date(evt.date_str)
            evt.actors = _extract_actors(evt.description)
            if evt.date_obj:
                events.append(evt)
    except sqlite3.Error:
        pass

    events.sort(key=lambda e: e.date_obj)
    return events


def detect_same_day_anomalies(events: list[TimelineEvent]) -> list[dict]:
    """Find filing + ruling on same day."""
    anomalies = []
    by_date = defaultdict(list)
    for e in events:
        date_key = e.date_obj.strftime("%Y-%m-%d")
        by_date[date_key].append(e)

    for date_key, day_events in by_date.items():
        if len(day_events) < 2:
            continue

        # Look for filing + ruling/order on same day
        filings = [e for e in day_events
                    if any(w in e.description.lower() for w in
                           ["filed", "motion", "petition", "complaint"])]
        rulings = [e for e in day_events
                   if any(w in e.description.lower() for w in
                          ["order", "ruling", "granted", "denied", "entered"])]

        for f in filings:
            for r in rulings:
                if f.rowid != r.rowid:
                    anomalies.append({
                        "type": "SAME_DAY_FILE_AND_RULE",
                        "severity": "CRITICAL",
                        "event_a": f.description[:200],
                        "event_a_date": date_key,
                        "event_b": r.description[:200],
                        "event_b_date": date_key,
                        "hours_apart": 0,
                        "actors": list(set(f.actors + r.actors)),
                    })

    return anomalies


def detect_coordination_signatures(events: list[TimelineEvent]) -> list[dict]:
    """Detect Watson → McNeill coordination pattern."""
    sigs = []

    # Group events by actor
    watson_events = [e for e in events if "Watson" in e.actors]
    mcneill_events = [e for e in events if "McNeill" in e.actors]
    berry_events = [e for e in events if "Berry" in e.actors]

    # Watson files → McNeill rules within 48 hours
    for we in watson_events:
        if not any(w in we.description.lower() for w in ["filed", "motion", "petition"]):
            continue
        for me in mcneill_events:
            if not any(w in me.description.lower() for w in ["order", "ruling", "granted"]):
                continue
            delta = (me.date_obj - we.date_obj).total_seconds() / 3600
            if 0 <= delta <= COORDINATION_WINDOW_DAYS * 24:
                sigs.append({
                    "actor_a": "Watson",
                    "actor_b": "McNeill",
                    "action_a": we.description[:200],
                    "action_b": me.description[:200],
                    "date_a": we.date_str,
                    "date_b": me.date_str,
                    "hours_apart": round(delta, 1),
                    "pattern": "Watson files → McNeill rules within 48hrs",
                })

    # Berry files within 48 hours of McNeill order
    for me in mcneill_events:
        for be in berry_events:
            delta = (be.date_obj - me.date_obj).total_seconds() / 3600
            if 0 <= delta <= COORDINATION_WINDOW_DAYS * 24:
                sigs.append({
                    "actor_a": "McNeill",
                    "actor_b": "Berry",
                    "action_a": me.description[:200],
                    "action_b": be.description[:200],
                    "date_a": me.date_str,
                    "date_b": be.date_str,
                    "hours_apart": round(delta, 1),
                    "pattern": "McNeill orders → Berry files within 48hrs",
                })

    return sigs


def detect_cluster_anomalies(events: list[TimelineEvent]) -> list[dict]:
    """Detect suspicious clustering of adverse actions."""
    anomalies = []

    # Look for 3+ adverse actions within 7 days
    adverse_keywords = ["denied", "contempt", "suspended", "restricted",
                        "ex parte", "no contact", "supervised"]

    adverse_events = []
    for e in events:
        desc_lower = e.description.lower()
        if any(kw in desc_lower for kw in adverse_keywords):
            adverse_events.append(e)

    # Sliding window
    for i, ae in enumerate(adverse_events):
        cluster = [ae]
        for j in range(i + 1, len(adverse_events)):
            delta_days = (adverse_events[j].date_obj - ae.date_obj).days
            if delta_days <= CLUSTER_WINDOW_DAYS:
                cluster.append(adverse_events[j])
            else:
                break

        if len(cluster) >= 3:
            anomalies.append({
                "type": "ADVERSE_ACTION_CLUSTER",
                "severity": "HIGH",
                "count": len(cluster),
                "window_start": ae.date_str,
                "window_end": cluster[-1].date_str,
                "days_span": (cluster[-1].date_obj - ae.date_obj).days,
                "events": [c.description[:100] for c in cluster[:5]],
                "actors": list(set(a for c in cluster for a in c.actors)),
            })

    return anomalies


def run_full_scan() -> dict:
    """Run complete temporal anomaly detection."""
    start = time.time()
    tdb = _init_db()

    central = sqlite3.connect(str(CENTRAL_DB), timeout=30)
    central.execute("PRAGMA busy_timeout=120000")

    events = _load_timeline(central)
    central.close()

    same_day = detect_same_day_anomalies(events)
    coord_sigs = detect_coordination_signatures(events)
    clusters = detect_cluster_anomalies(events)

    # Persist anomalies
    all_anomalies = same_day + [
        {"type": a["type"], "severity": a.get("severity", "HIGH"),
         "event_a": str(a.get("events", [""])[0])[:200],
         "event_a_date": a.get("window_start", ""),
         "description": f"{a['count']} adverse actions in {a['days_span']} days"}
        for a in clusters
    ]

    for a in all_anomalies:
        tdb.execute("""
            INSERT INTO temporal_anomalies
            (anomaly_type, severity, event_a, event_a_date, event_b, event_b_date,
             time_delta_hours, actors_involved, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            a.get("type", ""), a.get("severity", "MEDIUM"),
            a.get("event_a", "")[:500], a.get("event_a_date", ""),
            a.get("event_b", "")[:500], a.get("event_b_date", ""),
            a.get("hours_apart", 0),
            json.dumps(a.get("actors", [])),
            a.get("description", "")[:500],
        ))

    for s in coord_sigs:
        tdb.execute("""
            INSERT INTO coordination_signatures
            (actor_a, actor_b, action_a, action_b, date_a, date_b,
             hours_apart, pattern_description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (s["actor_a"], s["actor_b"], s["action_a"][:500],
              s["action_b"][:500], s["date_a"], s["date_b"],
              s["hours_apart"], s["pattern"]))

    duration = round(time.time() - start, 2)
    tdb.execute("""
        INSERT INTO scan_runs (events_scanned, anomalies_found, coordination_sigs, duration_s)
        VALUES (?, ?, ?, ?)
    """, (len(events), len(all_anomalies), len(coord_sigs), duration))
    tdb.commit()
    tdb.close()

    return {
        "events_scanned": len(events),
        "same_day_anomalies": len(same_day),
        "coordination_signatures": len(coord_sigs),
        "adverse_clusters": len(clusters),
        "total_anomalies": len(all_anomalies) + len(coord_sigs),
        "top_coordination": coord_sigs[:5],
        "top_clusters": clusters[:3],
        "duration_s": duration,
    }


if __name__ == "__main__":
    result = run_full_scan()
    print(json.dumps(result, indent=2, default=str))
