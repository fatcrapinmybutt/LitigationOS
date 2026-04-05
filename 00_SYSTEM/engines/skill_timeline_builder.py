#!/usr/bin/env python3
"""
skill_timeline_builder.py — Timeline Builder Skill
Wired to: master_chronological_timeline (14,568 rows)
"""
import sys, os, sqlite3, json
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding='utf-8')
except (AttributeError, OSError):
    pass
DB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'litigation_context.db')

def _conn():
    c = sqlite3.connect(DB, timeout=120)
    c.execute('PRAGMA busy_timeout=60000')
    c.execute('PRAGMA journal_mode=WAL')
    c.execute('PRAGMA cache_size=-32000')
    c.row_factory = sqlite3.Row
    return c

# ── Core Functions──────────────────────────────────────────────────

def get_timeline(start_date=None, end_date=None, limit=500):
    """Get timeline events between dates. Dates in YYYY-MM-DD format."""
    conn = _conn()
    if start_date and end_date:
        rows = conn.execute(
            "SELECT * FROM master_chronological_timeline "
            "WHERE event_date >= ? AND event_date <= ? ORDER BY event_date",
            (start_date, end_date)
        ).fetchall()
    elif start_date:
        rows = conn.execute(
            "SELECT * FROM master_chronological_timeline WHERE event_date >= ? ORDER BY event_date LIMIT ?",
            (start_date, limit)
        ).fetchall()
    elif end_date:
        rows = conn.execute(
            "SELECT * FROM master_chronological_timeline WHERE event_date <= ? ORDER BY event_date DESC LIMIT ?",
            (end_date, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM master_chronological_timeline ORDER BY event_date LIMIT ?", (limit,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_events_by_actor(actor, limit=200):
    """Get timeline events for a specific actor."""
    conn = _conn()
    rows = conn.execute(
        "SELECT * FROM master_chronological_timeline WHERE actor LIKE ? ORDER BY event_date",
        (f'%{actor}%',)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows[:limit]]


def get_events_by_type(event_type, limit=200):
    """Get timeline events by event_type or case_type."""
    conn = _conn()
    rows = conn.execute(
        "SELECT * FROM master_chronological_timeline "
        "WHERE event_type LIKE ? OR case_type LIKE ? ORDER BY event_date",
        (f'%{event_type}%', f'%{event_type}%')
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows[:limit]]


def get_timeline_stats():
    """Get statistical overview of the timeline."""
    conn = _conn()
    total = conn.execute("SELECT COUNT(*) FROM master_chronological_timeline").fetchone()[0]
    date_range = conn.execute(
        "SELECT MIN(event_date), MAX(event_date) FROM master_chronological_timeline WHERE event_date IS NOT NULL"
    ).fetchone()
    actors = conn.execute(
        "SELECT actor, COUNT(*) as cnt FROM master_chronological_timeline GROUP BY actor ORDER BY cnt DESC LIMIT 20"
    ).fetchall()
    types = conn.execute(
        "SELECT event_type, COUNT(*) as cnt FROM master_chronological_timeline GROUP BY event_type ORDER BY cnt DESC LIMIT 20"
    ).fetchall()
    case_types = conn.execute(
        "SELECT case_type, COUNT(*) as cnt FROM master_chronological_timeline GROUP BY case_type ORDER BY cnt DESC"
    ).fetchall()
    harm_events = conn.execute(
        "SELECT COUNT(*) FROM master_chronological_timeline WHERE harm_to_andrew IS NOT NULL AND harm_to_andrew != ''"
    ).fetchone()[0]
    conn.close()
    return {
        'total_events': total,
        'date_range': (date_range[0], date_range[1]) if date_range else None,
        'top_actors': [dict(r) for r in actors],
        'top_event_types': [dict(r) for r in types],
        'case_types': [dict(r) for r in case_types],
        'harm_events': harm_events
    }


def search_timeline(query, limit=100):
    """Full-text search across timeline descriptions and titles."""
    conn = _conn()
    rows = conn.execute(
        "SELECT * FROM master_chronological_timeline "
        "WHERE title LIKE ? OR description LIKE ? OR harm_to_andrew LIKE ? ORDER BY event_date LIMIT ?",
        (f'%{query}%', f'%{query}%', f'%{query}%', limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Main ────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("=" * 70)
    print("TIMELINE BUILDER SKILL — DB-WIRED")
    print("=" * 70)

    stats = get_timeline_stats()
    print(f"\n[STATS] {stats['total_events']} events, range: {stats['date_range']}")
    print(f"  Harm events: {stats['harm_events']}")

    print("\n  Top actors:")
    for a in stats['top_actors'][:10]:
        print(f"    • {a['actor']}: {a['cnt']} events")

    print("\n  Case types:")
    for ct in stats['case_types']:
        print(f"    • {ct['case_type']}: {ct['cnt']} events")

    print("\n  Top event types:")
    for et in stats['top_event_types'][:10]:
        print(f"    • {et['event_type']}: {et['cnt']} events")

    print("\n✅ Timeline Builder Skill operational")
