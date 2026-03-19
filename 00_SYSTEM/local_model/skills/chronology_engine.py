#!/usr/bin/env python3
"""
MBP LitigationOS -- Chronology Engine Skill
=============================================
Unified chronology from global_chronology (7,131 rows),
master_timeline (5,536 rows), chronological_misconduct (392 rows),
and docket_events (7 rows) for Pigors v. Watson (COA 366810,
14th Circuit, Muskegon County, Hon. Jenny L. McNeill).
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parent.parent
        if "skills" in str(Path(__file__))
        else Path(__file__).resolve().parent
    ),
)
try:
    from cycle_method import cycle_json, cycle_print
except ImportError:
    cycle_json = lambda obj, **kw: print(json.dumps(obj, default=str))
    cycle_print = print

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)

# Approximate separation start (for calculation baseline)
SEPARATION_START = "2024-06-01"


def _get_db() -> Optional[sqlite3.Connection]:
    """Get read-only DB connection."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA query_only=ON")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        return None


def _parse_date(s: Optional[str]) -> Optional[str]:
    """Normalize a date string to ISO format if possible."""
    if not s:
        return None
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S", "%B %d, %Y"):
        try:
            return datetime.strptime(s[:10] if len(s) >= 10 else s, fmt).strftime(
                "%Y-%m-%d"
            )
        except (ValueError, TypeError):
            continue
    # Return as-is if not parseable but non-empty
    return s if s else None


class ChronologyEngine:
    """Unified chronology engine merging all timeline sources."""

    CASE_CAPTION = "Pigors v. Watson"
    COA_DOCKET = "COA 366810"

    # ── Raw data access ───────────────────────────────────────────────

    def get_global_chronology(
        self, date_range: Optional[List[str]] = None, limit: int = 500
    ) -> List[Dict]:
        """Query global_chronology (7,131 rows)."""
        conn = _get_db()
        if not conn:
            return []
        try:
            if date_range and len(date_range) == 2:
                rows = conn.execute(
                    "SELECT * FROM global_chronology "
                    "WHERE date_iso >= ? AND date_iso <= ? "
                    "ORDER BY date_iso LIMIT ?",
                    (date_range[0], date_range[1], limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM global_chronology ORDER BY rowid LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []
        finally:
            conn.close()

    def get_master_timeline(
        self, date_range: Optional[List[str]] = None, limit: int = 500
    ) -> List[Dict]:
        """Query master_timeline (5,536 rows)."""
        conn = _get_db()
        if not conn:
            return []
        try:
            if date_range and len(date_range) == 2:
                rows = conn.execute(
                    "SELECT * FROM master_timeline "
                    "WHERE date_iso >= ? AND date_iso <= ? "
                    "ORDER BY date_iso LIMIT ?",
                    (date_range[0], date_range[1], limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM master_timeline ORDER BY rowid LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []
        finally:
            conn.close()

    def get_chronological_misconduct(self, limit: int = 200) -> List[Dict]:
        """Query chronological_misconduct (392 rows)."""
        conn = _get_db()
        if not conn:
            return []
        try:
            rows = conn.execute(
                "SELECT * FROM chronological_misconduct ORDER BY rowid LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []
        finally:
            conn.close()

    def get_docket_events(self, limit: int = 50) -> List[Dict]:
        """Query docket_events (7 rows)."""
        conn = _get_db()
        if not conn:
            return []
        try:
            rows = conn.execute(
                "SELECT * FROM docket_events ORDER BY event_date_iso LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []
        finally:
            conn.close()

    # ── Timeline builders ─────────────────────────────────────────────

    def build_complete_timeline(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict:
        """Merge all chronology sources into a unified timeline."""
        conn = _get_db()
        if not conn:
            return {"error": "DB unavailable", "events": []}
        try:
            events: List[Dict] = []

            # 1. global_chronology
            try:
                rows = conn.execute(
                    "SELECT * FROM global_chronology ORDER BY rowid LIMIT 2000"
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    # Normalize date field
                    dt = None
                    for key in ("date_iso", "date", "event_date"):
                        if d.get(key):
                            dt = _parse_date(str(d[key]))
                            break
                    d["_normalized_date"] = dt or ""
                    d["_source"] = "global_chronology"
                    events.append(d)
            except Exception:
                pass

            # 2. master_timeline
            try:
                rows = conn.execute(
                    "SELECT * FROM master_timeline ORDER BY rowid LIMIT 2000"
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    dt = None
                    for key in ("date_iso", "date", "event_date"):
                        if d.get(key):
                            dt = _parse_date(str(d[key]))
                            break
                    d["_normalized_date"] = dt or ""
                    d["_source"] = "master_timeline"
                    events.append(d)
            except Exception:
                pass

            # 3. chronological_misconduct
            try:
                rows = conn.execute(
                    "SELECT * FROM chronological_misconduct ORDER BY rowid LIMIT 500"
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    dt = None
                    for key in ("date_iso", "date", "event_date"):
                        if d.get(key):
                            dt = _parse_date(str(d[key]))
                            break
                    d["_normalized_date"] = dt or ""
                    d["_source"] = "chronological_misconduct"
                    events.append(d)
            except Exception:
                pass

            # 4. docket_events
            try:
                rows = conn.execute(
                    "SELECT * FROM docket_events ORDER BY event_date_iso"
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["_normalized_date"] = _parse_date(
                        d.get("event_date_iso", "")
                    ) or ""
                    d["_source"] = "docket_events"
                    events.append(d)
            except Exception:
                pass

            # Sort by date
            events.sort(key=lambda e: e.get("_normalized_date", "") or "")

            # Apply date range filter
            if start_date:
                events = [
                    e for e in events
                    if (e.get("_normalized_date") or "") >= start_date
                ]
            if end_date:
                events = [
                    e for e in events
                    if (e.get("_normalized_date") or "") <= end_date
                ]

            return {
                "case": self.CASE_CAPTION,
                "docket": self.COA_DOCKET,
                "date_range": {
                    "start": start_date,
                    "end": end_date,
                },
                "total_events": len(events),
                "by_source": {
                    "global_chronology": sum(
                        1 for e in events if e.get("_source") == "global_chronology"
                    ),
                    "master_timeline": sum(
                        1 for e in events if e.get("_source") == "master_timeline"
                    ),
                    "chronological_misconduct": sum(
                        1
                        for e in events
                        if e.get("_source") == "chronological_misconduct"
                    ),
                    "docket_events": sum(
                        1 for e in events if e.get("_source") == "docket_events"
                    ),
                },
                "events": events,
            }
        except Exception as e:
            return {"error": str(e), "events": []}
        finally:
            conn.close()

    def build_misconduct_timeline(self) -> Dict:
        """Build misconduct-focused timeline from chronological_misconduct."""
        conn = _get_db()
        if not conn:
            return {"error": "DB unavailable"}
        try:
            events = []
            try:
                rows = conn.execute(
                    "SELECT * FROM chronological_misconduct ORDER BY rowid"
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    dt = None
                    for key in ("date_iso", "date", "event_date"):
                        if d.get(key):
                            dt = _parse_date(str(d[key]))
                            break
                    d["_normalized_date"] = dt or ""
                    events.append(d)
            except Exception:
                pass

            events.sort(key=lambda e: e.get("_normalized_date", "") or "")

            # Supplement with judicial_violations
            violations = []
            try:
                rows = conn.execute(
                    "SELECT * FROM judicial_violations ORDER BY rowid"
                ).fetchall()
                violations = [dict(r) for r in rows]
            except Exception:
                pass

            return {
                "case": self.CASE_CAPTION,
                "focus": "judicial_misconduct",
                "total_misconduct_events": len(events),
                "total_violations": len(violations),
                "misconduct_events": events,
                "judicial_violations": violations,
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()

    def build_separation_timeline(self) -> Dict:
        """Build timeline of parent-child separation events (329+ days)."""
        conn = _get_db()
        if not conn:
            return {"error": "DB unavailable"}
        try:
            # Search for separation-related events
            separation_events: List[Dict] = []
            keywords = [
                "separation", "parenting time", "custody", "contact",
                "visitation", "denied", "suspended", "no contact",
            ]

            # Search global_chronology
            try:
                rows = conn.execute(
                    "SELECT * FROM global_chronology ORDER BY rowid LIMIT 7131"
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    text = " ".join(
                        str(v).lower() for v in d.values() if v is not None
                    )
                    if any(kw in text for kw in keywords):
                        dt = None
                        for key in ("date_iso", "date", "event_date"):
                            if d.get(key):
                                dt = _parse_date(str(d[key]))
                                break
                        d["_normalized_date"] = dt or ""
                        d["_source"] = "global_chronology"
                        separation_events.append(d)
            except Exception:
                pass

            # Search master_timeline
            try:
                rows = conn.execute(
                    "SELECT * FROM master_timeline ORDER BY rowid LIMIT 5536"
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    text = " ".join(
                        str(v).lower() for v in d.values() if v is not None
                    )
                    if any(kw in text for kw in keywords):
                        dt = None
                        for key in ("date_iso", "date", "event_date"):
                            if d.get(key):
                                dt = _parse_date(str(d[key]))
                                break
                        d["_normalized_date"] = dt or ""
                        d["_source"] = "master_timeline"
                        separation_events.append(d)
            except Exception:
                pass

            separation_events.sort(
                key=lambda e: e.get("_normalized_date", "") or ""
            )

            days = self.calculate_separation_days()

            return {
                "case": self.CASE_CAPTION,
                "focus": "parent_child_separation",
                "separation_start": SEPARATION_START,
                "days_separated": days.get("days", "329+"),
                "total_events": len(separation_events),
                "events": separation_events,
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()

    def find_events_by_topic(self, topic: str) -> List[Dict]:
        """Search timelines for specific events via FTS / LIKE."""
        conn = _get_db()
        if not conn:
            return []
        results: List[Dict] = []
        try:
            # Search global_chronology
            try:
                rows = conn.execute(
                    "SELECT * FROM global_chronology "
                    "WHERE rowid IN (SELECT rowid FROM global_chronology LIMIT 7131)"
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    if any(
                        topic.lower() in str(v).lower()
                        for v in d.values()
                        if v is not None
                    ):
                        d["_source"] = "global_chronology"
                        results.append(d)
            except Exception:
                pass

            # Search master_timeline
            try:
                rows = conn.execute(
                    "SELECT * FROM master_timeline "
                    "WHERE rowid IN (SELECT rowid FROM master_timeline LIMIT 5536)"
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    if any(
                        topic.lower() in str(v).lower()
                        for v in d.values()
                        if v is not None
                    ):
                        d["_source"] = "master_timeline"
                        results.append(d)
            except Exception:
                pass

            # Search chronological_misconduct
            try:
                rows = conn.execute(
                    "SELECT * FROM chronological_misconduct ORDER BY rowid"
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    if any(
                        topic.lower() in str(v).lower()
                        for v in d.values()
                        if v is not None
                    ):
                        d["_source"] = "chronological_misconduct"
                        results.append(d)
            except Exception:
                pass

        except Exception:
            pass
        finally:
            conn.close()
        return results

    def calculate_separation_days(self) -> Dict:
        """Calculate exact days of parent-child separation."""
        try:
            start = datetime.strptime(SEPARATION_START, "%Y-%m-%d").date()
            today = date.today()
            delta = (today - start).days
            return {
                "separation_start": SEPARATION_START,
                "as_of": today.isoformat(),
                "days": delta,
                "months": round(delta / 30.44, 1),
                "years": round(delta / 365.25, 2),
                "note": (
                    f"{delta} days of parent-child separation — "
                    "fundamental parental rights under 14th Amendment"
                ),
            }
        except Exception as e:
            return {"error": str(e), "days": "329+"}

    def generate_timeline_exhibit(self) -> Dict:
        """Generate a formatted timeline suitable for court exhibit."""
        complete = self.build_complete_timeline()
        events = complete.get("events", [])

        lines: List[str] = []
        lines.append("=" * 72)
        lines.append(
            f"  TIMELINE EXHIBIT — {self.CASE_CAPTION} ({self.COA_DOCKET})"
        )
        lines.append("=" * 72)
        lines.append("")

        prev_date = ""
        for i, event in enumerate(events[:300], 1):
            dt = event.get("_normalized_date", "")
            source = event.get("_source", "unknown")

            # Date header when date changes
            if dt and dt != prev_date:
                lines.append(f"\n--- {dt} ---")
                prev_date = dt

            # Build description from available fields
            desc_parts = []
            for key in ("title", "summary", "event_type", "description", "text"):
                val = event.get(key)
                if val and str(val).strip():
                    desc_parts.append(str(val).strip())
            desc = " | ".join(desc_parts[:3]) if desc_parts else "(no description)"

            lines.append(f"  {i:>4}. [{source}] {desc[:120]}")

        lines.append("")
        lines.append("=" * 72)
        lines.append(f"  Total events: {len(events)}")
        sep = self.calculate_separation_days()
        lines.append(
            f"  Parent-child separation: {sep.get('days', '329+')} days "
            f"(as of {sep.get('as_of', 'today')})"
        )
        lines.append("=" * 72)

        exhibit_text = "\n".join(lines)
        return {
            "case": self.CASE_CAPTION,
            "docket": self.COA_DOCKET,
            "exhibit_type": "timeline",
            "total_events": len(events),
            "exhibit_text": exhibit_text,
        }


# ── CLI ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ce = ChronologyEngine()
    usage = (
        "Chronology Engine Skill\n"
        "Usage:\n"
        "  python chronology_engine.py global [START] [END] [LIMIT]\n"
        "  python chronology_engine.py timeline [START] [END] [LIMIT]\n"
        "  python chronology_engine.py misconduct [LIMIT]\n"
        "  python chronology_engine.py docket [LIMIT]\n"
        "  python chronology_engine.py complete [START] [END]\n"
        "  python chronology_engine.py misconduct-timeline\n"
        "  python chronology_engine.py separation\n"
        "  python chronology_engine.py search <TOPIC>\n"
        "  python chronology_engine.py days\n"
        "  python chronology_engine.py exhibit\n"
    )

    if len(sys.argv) < 2:
        print(usage)
        sys.exit(0)

    cmd = sys.argv[1].lower()

    if cmd == "global":
        dr = [sys.argv[2], sys.argv[3]] if len(sys.argv) > 3 else None
        lim = int(sys.argv[4]) if len(sys.argv) > 4 else 500
        cycle_json(ce.get_global_chronology(dr, lim))
    elif cmd == "timeline":
        dr = [sys.argv[2], sys.argv[3]] if len(sys.argv) > 3 else None
        lim = int(sys.argv[4]) if len(sys.argv) > 4 else 500
        cycle_json(ce.get_master_timeline(dr, lim))
    elif cmd == "misconduct":
        lim = int(sys.argv[2]) if len(sys.argv) > 2 else 200
        cycle_json(ce.get_chronological_misconduct(lim))
    elif cmd == "docket":
        lim = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        cycle_json(ce.get_docket_events(lim))
    elif cmd == "complete":
        sd = sys.argv[2] if len(sys.argv) > 2 else None
        ed = sys.argv[3] if len(sys.argv) > 3 else None
        cycle_json(ce.build_complete_timeline(sd, ed))
    elif cmd == "misconduct-timeline":
        cycle_json(ce.build_misconduct_timeline())
    elif cmd == "separation":
        cycle_json(ce.build_separation_timeline())
    elif cmd == "search":
        if len(sys.argv) < 3:
            print("Error: topic required", file=sys.stderr)
            sys.exit(1)
        cycle_json(ce.find_events_by_topic(" ".join(sys.argv[2:])))
    elif cmd == "days":
        cycle_json(ce.calculate_separation_days())
    elif cmd == "exhibit":
        result = ce.generate_timeline_exhibit()
        if "exhibit_text" in result:
            print(result["exhibit_text"])
            print(
                f"\n--- {result.get('total_events', 0)} events ---",
                file=sys.stderr,
            )
        else:
            cycle_json(result)
    else:
        print(usage)
