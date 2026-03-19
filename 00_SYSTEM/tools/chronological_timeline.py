#!/usr/bin/env python3
"""
Tool #76 — Chronological Master Timeline
=============================================
Mines the entire database to build a comprehensive chronological
timeline of ALL events in Pigors v. Watson.

This is the foundation document for:
- Affidavits (sworn chronology)
- Brief narratives (fact sections)
- Trial preparation (opening statement)
- Evidence organization (what happened when)

Sources: docket_events, evidence_quotes, detected_contradictions,
chatgpt_evidence, judicial_violations, and more.
"""
import sys, json, sqlite3
from pathlib import Path
from datetime import datetime
from collections import defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

def mine_timeline_events():
    """Extract dated events from all DB tables."""
    events = []
    
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=60)
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA cache_size=-32000")
        
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        
        # 1. Docket events
        if 'docket_events' in tables:
            try:
                cols = [r[1] for r in conn.execute("PRAGMA table_info(docket_events)").fetchall()]
                date_col = next((c for c in cols if 'date' in c.lower()), None)
                desc_col = next((c for c in cols if c.lower() in ('description', 'event_description', 'event', 'text')), None)
                
                if date_col and desc_col:
                    rows = conn.execute(f"""
                        SELECT {date_col}, {desc_col} FROM docket_events 
                        WHERE {date_col} IS NOT NULL AND {date_col} != ''
                        ORDER BY {date_col}
                        LIMIT 500
                    """).fetchall()
                    for date, desc in rows:
                        if date and desc:
                            events.append({
                                'date': str(date)[:10],
                                'event': str(desc)[:200],
                                'source': 'docket_events',
                                'category': 'Court',
                            })
            except Exception as e:
                print(f"  docket_events error: {e}")
        
        # 2. Evidence quotes with dates
        if 'evidence_quotes' in tables:
            try:
                cols = [r[1] for r in conn.execute("PRAGMA table_info(evidence_quotes)").fetchall()]
                date_col = next((c for c in cols if 'date' in c.lower()), None)
                text_col = next((c for c in cols if c.lower() in ('quote_text', 'text', 'quote')), None)
                
                if date_col and text_col:
                    rows = conn.execute(f"""
                        SELECT {date_col}, {text_col} FROM evidence_quotes 
                        WHERE {date_col} IS NOT NULL AND {date_col} != ''
                        AND length({text_col}) > 20
                        ORDER BY {date_col}
                        LIMIT 300
                    """).fetchall()
                    for date, text in rows:
                        if date and text:
                            events.append({
                                'date': str(date)[:10],
                                'event': str(text)[:200],
                                'source': 'evidence_quotes',
                                'category': 'Evidence',
                            })
            except Exception as e:
                print(f"  evidence_quotes error: {e}")
        
        # 3. Judicial violations
        if 'judicial_violations' in tables:
            try:
                cols = [r[1] for r in conn.execute("PRAGMA table_info(judicial_violations)").fetchall()]
                date_col = next((c for c in cols if 'date' in c.lower()), None)
                desc_col = next((c for c in cols if c.lower() in ('description', 'violation_description', 'violation_type', 'text')), None)
                
                if date_col and desc_col:
                    rows = conn.execute(f"""
                        SELECT {date_col}, {desc_col} FROM judicial_violations 
                        WHERE {date_col} IS NOT NULL AND {date_col} != ''
                        ORDER BY {date_col}
                        LIMIT 200
                    """).fetchall()
                    for date, desc in rows:
                        if date and desc:
                            events.append({
                                'date': str(date)[:10],
                                'event': f"JUDICIAL: {str(desc)[:180]}",
                                'source': 'judicial_violations',
                                'category': 'Judicial',
                            })
            except Exception as e:
                print(f"  judicial_violations error: {e}")
        
        # 4. Deadlines
        if 'deadlines' in tables:
            try:
                cols = [r[1] for r in conn.execute("PRAGMA table_info(deadlines)").fetchall()]
                date_col = next((c for c in cols if 'date' in c.lower() or 'due' in c.lower()), None)
                desc_col = next((c for c in cols if c.lower() in ('description', 'title', 'name', 'text')), None)
                
                if date_col and desc_col:
                    rows = conn.execute(f"""
                        SELECT {date_col}, {desc_col} FROM deadlines 
                        WHERE {date_col} IS NOT NULL
                        ORDER BY {date_col}
                        LIMIT 100
                    """).fetchall()
                    for date, desc in rows:
                        if date and desc:
                            events.append({
                                'date': str(date)[:10],
                                'event': f"DEADLINE: {str(desc)[:180]}",
                                'source': 'deadlines',
                                'category': 'Deadline',
                            })
            except Exception as e:
                print(f"  deadlines error: {e}")
        
        conn.close()
    except Exception as e:
        print(f"  DB connection error: {e}")
    
    return events

def add_known_events(events):
    """Add known key events from case history."""
    known = [
        ('2022-11-09', 'L.D.W. born', 'Known', 'Personal'),
        ('2023-10-01', 'Emily Watson files PPO petition (2023-5907-PP) — alleged straw incident', 'Known', 'Court'),
        ('2024-01-01', 'Case 2024-001507-DC filed — custody/parenting time', 'Known', 'Court'),
        ('2024-05-01', 'Andrew files ex-parte motion (legitimate)', 'Known', 'Court'),
        ('2025-08-01', 'Emily files ex-parte to suspend ALL parenting time (fraudulent)', 'Known', 'Court'),
        ('2025-08-15', 'Judge McNeill grants Emily\'s ex-parte without hearing', 'Known', 'Judicial'),
    ]
    for date, event, source, category in known:
        events.append({
            'date': date,
            'event': event,
            'source': source,
            'category': category,
        })
    return events

def main():
    print("=" * 70)
    print("CHRONOLOGICAL MASTER TIMELINE — Tool #76")
    print("=" * 70)
    
    events = mine_timeline_events()
    events = add_known_events(events)
    
    # Sort by date
    events.sort(key=lambda e: e.get('date', '9999'))
    
    # Deduplicate similar events on same date
    seen = set()
    unique_events = []
    for e in events:
        key = f"{e['date']}:{e['event'][:50]}"
        if key not in seen:
            seen.add(key)
            unique_events.append(e)
    
    # Group by year
    by_year = defaultdict(list)
    for e in unique_events:
        year = e['date'][:4] if len(e['date']) >= 4 else 'Unknown'
        by_year[year].append(e)
    
    # Count by category
    by_category = defaultdict(int)
    for e in unique_events:
        by_category[e['category']] += 1
    
    print(f"\n  Total events mined: {len(events)}")
    print(f"  Unique events: {len(unique_events)}")
    print(f"  Years covered: {min(by_year.keys())} — {max(by_year.keys())}")
    print(f"\n  By category:")
    for cat, cnt in sorted(by_category.items(), key=lambda x: -x[1]):
        print(f"    {cat}: {cnt}")
    
    lines = [
        "# 📅 CHRONOLOGICAL MASTER TIMELINE",
        "## Pigors v. Watson — Complete Event History",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        f"*{len(unique_events)} events from {len(by_year)} years*\n",
        "---\n",
    ]
    
    for year in sorted(by_year.keys()):
        year_events = by_year[year]
        lines.append(f"## {year} ({len(year_events)} events)\n")
        
        for e in year_events[:100]:  # Cap per year
            icon = {'Court': '⚖️', 'Evidence': '📄', 'Judicial': '🔴', 'Deadline': '⏰', 'Personal': '👤'}.get(e['category'], '•')
            lines.append(f"- **{e['date']}** {icon} {e['event']}")
        
        if len(year_events) > 100:
            lines.append(f"  *... and {len(year_events) - 100} more events*")
        lines.append("")
    
    lines.extend([
        "---",
        "## Category Summary",
        "| Category | Count |",
        "|----------|-------|",
    ])
    for cat, cnt in sorted(by_category.items(), key=lambda x: -x[1]):
        lines.append(f"| {cat} | {cnt} |")
    
    lines.extend([
        "",
        f"*Chronological Master Timeline — Tool #76*",
        f"*{len(unique_events)} events across {len(by_year)} years*",
    ])
    
    md_path = REPORTS_DIR / "MASTER_TIMELINE.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "master_timeline.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Chronological Master Timeline (#76)',
        'total_mined': len(events),
        'unique_events': len(unique_events),
        'years': len(by_year),
        'by_category': dict(by_category),
        'events': unique_events[:500],  # Top 500
    }, indent=2, default=str), encoding='utf-8')
    
    print(f"\n✅ Master timeline built: {len(unique_events)} events")
    print(f"   Reports: MASTER_TIMELINE.md + master_timeline.json")

if __name__ == '__main__':
    main()
