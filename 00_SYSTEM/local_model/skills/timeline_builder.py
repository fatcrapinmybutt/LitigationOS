#!/usr/bin/env python3
"""
MBP LitigationOS -- Timeline Builder Skill
============================================
Build chronological timeline from DB evidence tables.
Merges docket_events, evidence_quotes, documents, and claims.
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent if 'skills' in str(Path(__file__)) else Path(__file__).resolve().parent))
try:
    from cycle_method import cycle_json, cycle_print
except ImportError:
    cycle_json = lambda obj, **kw: print(json.dumps(obj, default=str))
    cycle_print = print

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)


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


def build_timeline(case_id: Optional[str] = None,
                   include_evidence: bool = True,
                   include_documents: bool = True,
                   limit: int = 500) -> List[Dict]:
    """
    Build comprehensive chronological timeline.
    Merges data from multiple tables into a unified event list.

    Returns: [{date, title, type, summary, source_table, case_id}]
    """
    events: List[Dict] = []

    try:
        conn = _get_db()
        if not conn:
            return events

        # 1. Docket events (primary timeline)
        try:
            if case_id:
                rows = conn.execute(
                    "SELECT event_date_iso, title, event_type, summary, case_id "
                    "FROM docket_events WHERE case_id = ? "
                    "ORDER BY event_date_iso",
                    (case_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT event_date_iso, title, event_type, summary, case_id "
                    "FROM docket_events ORDER BY event_date_iso"
                ).fetchall()

            for row in rows:
                events.append({
                    "date": row["event_date_iso"] or "",
                    "title": row["title"] or "",
                    "type": row["event_type"] or "docket",
                    "summary": row["summary"] or "",
                    "source_table": "docket_events",
                    "case_id": row["case_id"] or "",
                })
        except Exception:
            pass

        # 2. Deadlines
        try:
            if case_id:
                rows = conn.execute(
                    "SELECT due_date_iso, title, basis, risk_if_missed, status, case_id "
                    "FROM deadlines WHERE case_id = ? ORDER BY due_date_iso",
                    (case_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT due_date_iso, title, basis, risk_if_missed, status, case_id "
                    "FROM deadlines ORDER BY due_date_iso"
                ).fetchall()

            for row in rows:
                events.append({
                    "date": row["due_date_iso"] or "",
                    "title": f"DEADLINE: {row['title'] or ''}",
                    "type": "deadline",
                    "summary": f"Basis: {row['basis'] or ''}. Risk: {row['risk_if_missed'] or ''}. Status: {row['status'] or ''}",
                    "source_table": "deadlines",
                    "case_id": row["case_id"] or "",
                })
        except Exception:
            pass

        # 3. Evidence quotes with dates
        if include_evidence:
            try:
                rows = conn.execute(
                    "SELECT date_ref, substr(quote_text, 1, 200) as text, "
                    "evidence_category, speaker, legal_significance "
                    "FROM evidence_quotes "
                    "WHERE date_ref IS NOT NULL AND date_ref != '' "
                    "ORDER BY date_ref "
                    "LIMIT ?",
                    (limit,),
                ).fetchall()

                for row in rows:
                    events.append({
                        "date": row["date_ref"] or "",
                        "title": f"Evidence: {row['evidence_category'] or 'General'}",
                        "type": "evidence",
                        "summary": f"[{row['speaker'] or 'Unknown'}]: {row['text'] or ''}",
                        "source_table": "evidence_quotes",
                        "case_id": "",
                    })
            except Exception:
                pass

        # 4. Documents by date
        if include_documents:
            try:
                rows = conn.execute(
                    "SELECT modified_date, file_name, evidence_category, page_count "
                    "FROM documents "
                    "WHERE modified_date IS NOT NULL AND modified_date != '' "
                    "ORDER BY modified_date "
                    "LIMIT ?",
                    (limit,),
                ).fetchall()

                for row in rows:
                    events.append({
                        "date": row["modified_date"] or "",
                        "title": row["file_name"] or "Document",
                        "type": "document",
                        "summary": f"Category: {row['evidence_category'] or 'N/A'}, Pages: {row['page_count'] or 'N/A'}",
                        "source_table": "documents",
                        "case_id": "",
                    })
            except Exception:
                pass

        conn.close()

        # Sort chronologically
        def sort_key(e):
            try:
                return e.get("date", "") or ""
            except Exception:
                return ""

        events.sort(key=sort_key)

        # Trim to limit
        events = events[:limit]

    except Exception:
        pass

    return events


def get_timeline_summary(case_id: Optional[str] = None) -> Dict:
    """Get a summary of the timeline with counts by type and date range."""
    try:
        events = build_timeline(case_id)
        if not events:
            return {"total": 0, "by_type": {}, "date_range": {}}

        by_type: Dict[str, int] = {}
        dates = []
        for e in events:
            t = e.get("type", "unknown")
            by_type[t] = by_type.get(t, 0) + 1
            d = e.get("date", "")
            if d:
                dates.append(d)

        return {
            "total": len(events),
            "by_type": by_type,
            "date_range": {
                "earliest": min(dates) if dates else "",
                "latest": max(dates) if dates else "",
            },
        }
    except Exception:
        return {"total": 0, "by_type": {}, "date_range": {}}


# ── CLI ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    case = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "--summary" else None

    if "--summary" in sys.argv:
        result = get_timeline_summary(case)
        cycle_json(result)
        print(f"--- Timeline: summary ---", file=sys.stderr)
    else:
        events = build_timeline(case)
        cycle_json(events)
        print(f"--- Timeline: {len(events) if isinstance(events, list) else 'result'} ---",
              file=sys.stderr)
