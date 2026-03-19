#!/usr/bin/env python3
"""
MBP LitigationOS — Timeline Visualization Skill (m43)
======================================================
Generates structured timeline data for visualization from docket_events,
master_timeline, conspiracy_timeline, and judicial_violations tables.

Outputs JSON-ready and CSV-exportable timeline data for charting.

Tables used:
    docket_events (221 rows)
    master_timeline
    conspiracy_timeline (2,512 rows)
    judicial_violations (1,127 rows)
    extracted_harms (26,459 rows)

Usage:
    from skills.timeline_visualization import TimelineVisualization
    viz = TimelineVisualization()
    data = viz.generate_timeline_data("2024-01-01", "2025-12-31")
"""

from __future__ import annotations

import csv
import json
import io
import os
import sqlite3
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent
    if "skills" in str(Path(__file__)) else Path(__file__).resolve().parent))
try:
    from cycle_method import cycle_json, cycle_print
except ImportError:
    cycle_json = lambda obj, **kw: print(json.dumps(obj, default=str))
    cycle_print = print

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)

SEPARATION_START = date(2025, 8, 8)


def _get_db() -> Optional[sqlite3.Connection]:
    try:
        conn = sqlite3.connect(DB_PATH, timeout=60)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("PRAGMA query_only=ON")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        return None


class TimelineVisualization:
    """Generate timeline data structures for visualization and export."""

    def generate_timeline_data(
        self,
        start_date: str,
        end_date: str,
        event_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Combine docket, master_timeline, and conspiracy events into unified JSON.

        Args:
            start_date: ISO date string (YYYY-MM-DD)
            end_date: ISO date string (YYYY-MM-DD)
            event_types: Optional filter list (e.g., ['docket','conspiracy','violation'])
        """
        conn = _get_db()
        if not conn:
            return {"error": "DB unavailable"}
        events: List[Dict] = []
        include_all = not event_types
        try:
            # Docket events
            if include_all or "docket" in event_types:
                rows = conn.execute(
                    "SELECT event_id, case_id, event_date_iso as event_date, "
                    "title, event_type, summary, truth_tag "
                    "FROM docket_events "
                    "WHERE event_date_iso BETWEEN ? AND ? "
                    "ORDER BY event_date_iso",
                    (start_date, end_date),
                ).fetchall()
                for r in rows:
                    events.append({
                        "source": "docket",
                        "id": r["event_id"],
                        "date": r["event_date"],
                        "title": r["title"],
                        "type": r["event_type"],
                        "detail": r["summary"],
                        "case_id": r["case_id"],
                        "truth_tag": r["truth_tag"],
                    })

            # Master timeline
            if include_all or "timeline" in event_types:
                try:
                    rows = conn.execute(
                        "SELECT id, event_date, event_summary, event_detail, "
                        "lanes, people, event_type "
                        "FROM master_timeline "
                        "WHERE event_date BETWEEN ? AND ? "
                        "ORDER BY event_date",
                        (start_date, end_date),
                    ).fetchall()
                    for r in rows:
                        events.append({
                            "source": "master_timeline",
                            "id": r["id"],
                            "date": r["event_date"],
                            "title": r["event_summary"],
                            "type": r["event_type"],
                            "detail": r["event_detail"],
                            "lanes": r["lanes"],
                            "people": r["people"],
                        })
                except Exception:
                    pass

            # Conspiracy timeline
            if include_all or "conspiracy" in event_types:
                rows = conn.execute(
                    "SELECT id, date, actor, action, coordinated_with, "
                    "evidence_source, conspiracy_type, severity "
                    "FROM conspiracy_timeline "
                    "WHERE date BETWEEN ? AND ? ORDER BY date",
                    (start_date, end_date),
                ).fetchall()
                for r in rows:
                    events.append({
                        "source": "conspiracy",
                        "id": r["id"],
                        "date": r["date"],
                        "title": f"{r['actor']}: {r['action'][:80]}",
                        "type": r["conspiracy_type"],
                        "detail": r["action"],
                        "actor": r["actor"],
                        "coordinated_with": r["coordinated_with"],
                        "severity": r["severity"],
                    })

            # Judicial violations
            if include_all or "violation" in event_types:
                try:
                    rows = conn.execute(
                        "SELECT id, date, violation_type, description, "
                        "authority_violated, severity "
                        "FROM judicial_violations "
                        "WHERE date BETWEEN ? AND ? ORDER BY date",
                        (start_date, end_date),
                    ).fetchall()
                    for r in rows:
                        events.append({
                            "source": "judicial_violation",
                            "id": r["id"],
                            "date": r["date"],
                            "title": r["violation_type"],
                            "type": "judicial_violation",
                            "detail": r["description"],
                            "authority_violated": r["authority_violated"],
                            "severity": r["severity"],
                        })
                except Exception:
                    pass

            # Sort all events by date
            events.sort(key=lambda e: e.get("date") or "")

        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()

        return {
            "start_date": start_date,
            "end_date": end_date,
            "event_types": event_types or ["all"],
            "total_events": len(events),
            "events": events,
        }

    def separation_timeline(self) -> Dict[str, Any]:
        """Day-by-day separation counter from Aug 8, 2025 to present."""
        today = date.today()
        total_days = max(0, (today - SEPARATION_START).days)

        milestones = []
        for d in [30, 60, 90, 180, 365, 500, 567]:
            milestone_date = SEPARATION_START + timedelta(days=d)
            if milestone_date <= today:
                milestones.append({
                    "day": d,
                    "date": milestone_date.isoformat(),
                    "label": f"Day {d} of separation",
                })

        # Get key events during separation from docket
        conn = _get_db()
        events = []
        if conn:
            try:
                rows = conn.execute(
                    "SELECT event_date_iso, title, event_type "
                    "FROM docket_events "
                    "WHERE event_date_iso >= ? ORDER BY event_date_iso",
                    (SEPARATION_START.isoformat(),),
                ).fetchall()
                for r in rows:
                    try:
                        evt_date = date.fromisoformat(r["event_date_iso"])
                        day_num = (evt_date - SEPARATION_START).days
                    except (ValueError, TypeError):
                        day_num = None
                    events.append({
                        "date": r["event_date_iso"],
                        "day_of_separation": day_num,
                        "title": r["title"],
                        "type": r["event_type"],
                    })
            except Exception:
                pass
            finally:
                conn.close()

        return {
            "separation_start": SEPARATION_START.isoformat(),
            "as_of": today.isoformat(),
            "total_days_separated": total_days,
            "milestones": milestones,
            "events_during_separation": events,
        }

    def ex_parte_timeline(self) -> Dict[str, Any]:
        """All ex parte events with dates, descriptions, and authorities violated."""
        conn = _get_db()
        if not conn:
            return {"error": "DB unavailable"}
        events = []
        try:
            # From judicial_violations
            try:
                rows = conn.execute(
                    "SELECT id, date, violation_type, description, "
                    "authority_violated, severity "
                    "FROM judicial_violations "
                    "WHERE violation_type LIKE '%ex parte%' "
                    "OR description LIKE '%ex parte%' "
                    "ORDER BY date",
                ).fetchall()
                for r in rows:
                    events.append({
                        "source": "judicial_violations",
                        "id": r["id"],
                        "date": r["date"],
                        "type": r["violation_type"],
                        "description": r["description"],
                        "authority_violated": r["authority_violated"],
                        "severity": r["severity"],
                    })
            except Exception:
                pass

            # From conspiracy_timeline
            rows = conn.execute(
                "SELECT id, date, actor, action, coordinated_with, "
                "conspiracy_type, severity "
                "FROM conspiracy_timeline "
                "WHERE action LIKE '%ex parte%' "
                "OR conspiracy_type LIKE '%ex parte%' "
                "ORDER BY date",
            ).fetchall()
            for r in rows:
                events.append({
                    "source": "conspiracy_timeline",
                    "id": r["id"],
                    "date": r["date"],
                    "actor": r["actor"],
                    "description": r["action"],
                    "type": r["conspiracy_type"],
                    "coordinated_with": r["coordinated_with"],
                    "severity": r["severity"],
                })

            # From docket_events
            rows = conn.execute(
                "SELECT event_id, event_date_iso, title, summary "
                "FROM docket_events "
                "WHERE title LIKE '%ex parte%' OR summary LIKE '%ex parte%' "
                "ORDER BY event_date_iso",
            ).fetchall()
            for r in rows:
                events.append({
                    "source": "docket_events",
                    "id": r["event_id"],
                    "date": r["event_date_iso"],
                    "description": r["title"],
                    "detail": r["summary"],
                    "type": "ex_parte_docket",
                })

            events.sort(key=lambda e: e.get("date") or "")
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()

        return {
            "total_ex_parte_events": len(events),
            "events": events,
        }

    def ppo_custody_correlation(self) -> Dict[str, Any]:
        """Side-by-side PPO and custody events to show correlation."""
        conn = _get_db()
        if not conn:
            return {"error": "DB unavailable"}
        ppo_events = []
        custody_events = []
        try:
            # PPO events from docket
            rows = conn.execute(
                "SELECT event_id, case_id, event_date_iso, title, summary "
                "FROM docket_events "
                "WHERE case_id LIKE '%5907%' OR title LIKE '%PPO%' "
                "OR title LIKE '%protection%' "
                "ORDER BY event_date_iso",
            ).fetchall()
            for r in rows:
                ppo_events.append({
                    "date": r["event_date_iso"],
                    "title": r["title"],
                    "detail": r["summary"],
                    "case_id": r["case_id"],
                })

            # Custody events
            rows = conn.execute(
                "SELECT event_id, case_id, event_date_iso, title, summary "
                "FROM docket_events "
                "WHERE case_id LIKE '%1507%' OR title LIKE '%custody%' "
                "OR title LIKE '%parenting%' "
                "ORDER BY event_date_iso",
            ).fetchall()
            for r in rows:
                custody_events.append({
                    "date": r["event_date_iso"],
                    "title": r["title"],
                    "detail": r["summary"],
                    "case_id": r["case_id"],
                })
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()

        return {
            "ppo_events": ppo_events,
            "custody_events": custody_events,
            "ppo_count": len(ppo_events),
            "custody_count": len(custody_events),
            "correlation_note": (
                "Review dates for Watson-files-PPO → McNeill-rules-custody pattern. "
                "24/55 orders (43.6%) entered ex parte."
            ),
        }

    def docket_timeline(self, case_id: str) -> Dict[str, Any]:
        """Complete docket timeline for a specific case."""
        conn = _get_db()
        if not conn:
            return {"error": "DB unavailable"}
        events = []
        try:
            rows = conn.execute(
                "SELECT event_id, event_date_iso, record_date_iso, "
                "title, event_type, summary, truth_tag "
                "FROM docket_events WHERE case_id = ? "
                "ORDER BY event_date_iso",
                (case_id,),
            ).fetchall()
            for r in rows:
                events.append(dict(r))
        except Exception as e:
            return {"error": str(e), "case_id": case_id}
        finally:
            conn.close()

        return {
            "case_id": case_id,
            "total_events": len(events),
            "events": events,
        }

    def export_csv(
        self,
        timeline_data: Dict[str, Any],
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Export timeline data to CSV. Returns CSV string if no output_path."""
        events = timeline_data.get("events", [])
        if not events:
            return {"error": "No events to export"}

        # Determine all keys across events
        all_keys = set()
        for evt in events:
            all_keys.update(evt.keys())
        fieldnames = sorted(all_keys)

        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for evt in events:
            writer.writerow(evt)

        csv_content = buf.getvalue()
        buf.close()

        if output_path:
            with open(output_path, "w", encoding="utf-8", newline="") as f:
                f.write(csv_content)
            return {
                "status": "exported",
                "path": output_path,
                "rows": len(events),
                "columns": len(fieldnames),
            }

        return {
            "status": "generated",
            "rows": len(events),
            "columns": len(fieldnames),
            "csv": csv_content[:2000],
            "truncated": len(csv_content) > 2000,
        }


# ── JSON-RPC dispatch ─────────────────────────────────────────────────

def handle_rpc(method: str, params: Dict[str, Any] = None) -> Dict:
    params = params or {}
    viz = TimelineVisualization()
    dispatch = {
        "generate_timeline_data": viz.generate_timeline_data,
        "separation_timeline": viz.separation_timeline,
        "ex_parte_timeline": viz.ex_parte_timeline,
        "ppo_custody_correlation": viz.ppo_custody_correlation,
        "docket_timeline": viz.docket_timeline,
        "export_csv": viz.export_csv,
    }
    fn = dispatch.get(method)
    if not fn:
        return {"error": f"Unknown method: {method}", "available": list(dispatch.keys())}
    try:
        result = fn(**params)
        return {"result": result, "method": method, "status": "ok"}
    except Exception as e:
        return {"error": str(e), "method": method}


if __name__ == "__main__":
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    viz = TimelineVisualization()
    print("=== Timeline Visualization Skill (m43) ===\n")

    sep = viz.separation_timeline()
    print(f"Days separated: {sep['total_days_separated']}")
    print(f"Milestones reached: {len(sep['milestones'])}")

    exp = viz.ex_parte_timeline()
    print(f"Ex parte events: {exp['total_ex_parte_events']}")

    corr = viz.ppo_custody_correlation()
    print(f"PPO events: {corr['ppo_count']}, Custody events: {corr['custody_count']}")

    print("\n[OK] Timeline Visualization operational")
