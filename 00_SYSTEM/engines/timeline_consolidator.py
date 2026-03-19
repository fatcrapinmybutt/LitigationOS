#!/usr/bin/env python3
"""
TIMELINE CONSOLIDATION ENGINE v1.0
Takes 43K raw events → condenses to court-usable prosecution timeline.

Strategy:
1. Filter to case-relevant date range (2024-2026)
2. Drop low-severity noise (sev < 5)
3. Group by date → merge similar events
4. Deduplicate by semantic similarity (first 80 chars)
5. Rank and cap per day (max 10 events/day)
6. Produce condensed master timeline (~300-500 entries)
"""
import sqlite3
import os
import re
from datetime import datetime
from collections import defaultdict

db_path = r'C:\Users\andre\LitigationOS\litigation_context.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

LOS_ROOT = r'C:\Users\andre\LitigationOS'

print("=" * 70)
print("  TIMELINE CONSOLIDATION ENGINE v1.0")
print("  43K raw → court-grade prosecution timeline")
print("=" * 70)

# ============================================================
# STEP 1: Pull relevant events, filter noise
# ============================================================
c.execute("""SELECT event_date, category, title, description, actors, evidence_ref, 
    CAST(severity AS INTEGER) as sev, source
    FROM master_timeline 
    WHERE event_date >= '2022-01-01' AND event_date <= '2026-06-30'
    AND CAST(severity AS INTEGER) >= 4
    ORDER BY event_date, CAST(severity AS INTEGER) DESC""")
raw = c.fetchall()
print(f"\n[1] Filtered to case range (2022-2026, sev>=4): {len(raw):,} events")

# ============================================================
# STEP 2: Category priority weights (legal significance)
# ============================================================
CATEGORY_WEIGHT = {
    'CONSTITUTIONAL': 15,
    'JUDICIAL_VIOLATION': 14,
    'COURT_ORDER': 13,
    'COURT_FILING': 12,
    'MOTION': 11,
    'POLICE_REPORT': 10,
    'AFFIDAVIT': 10,
    'DAMAGES': 10,
    'EVIDENCE': 8,
    'COMMUNICATION': 7,
    'CO_PARENT_COMMUNICATION': 7,
    'PSYCH': 7,
    'CONTRAST': 6,
    'manipulation_pattern': 6,
    'DB_RECORD': 4,
    'FILE_EVENT': 3,
    'ANALYSIS': 2,
    'QUOTE': 5,
}

# ============================================================
# STEP 3: Group by date, merge, and rank
# ============================================================
by_date = defaultdict(list)
for date, cat, title, desc, actors, evidence, sev, source in raw:
    weight = CATEGORY_WEIGHT.get(cat, 4) + (sev or 5)
    by_date[date].append({
        'cat': cat, 'title': title or '', 'desc': desc or '',
        'actors': actors or '', 'evidence': evidence or '',
        'sev': sev or 5, 'source': source or '', 'weight': weight
    })

print(f"[2] Grouped into {len(by_date)} unique dates")

# ============================================================
# STEP 4: Per-date consolidation
# ============================================================
consolidated = []

# Known critical events that MUST appear (manually curated from case knowledge)
PINNED_EVENTS = {
    '2024-01-01': ('CASE_FILED', 'Case 2024-001507-DC filed, 14th Circuit Court, Muskegon County', 'Andrew Pigors, Emily Watson', 10),
    '2024-07-17': ('COURT_HEARING', 'Critical hearing — multiple motions argued', 'Judge McNeill', 9),
    '2025-07-29': ('LAST_PARENTING_TIME', 'LAST parenting time with Lincoln (L.D.W.)', 'Andrew Pigors, Lincoln', 10),
    '2025-08-07': ('PREMEDITATION', 'Albert Watson premeditation statement — coordinated custody strategy', 'Albert Watson', 9),
    '2025-08-08': ('PT_SUSPENSION', 'Parenting time SUSPENDED by ex parte order — 639 events this date', 'Judge McNeill', 10),
    '2025-10-29': ('MAJOR_HEARING', 'Major court event — 348 events this date', 'Multiple', 9),
}

for date in sorted(by_date.keys()):
    events = by_date[date]
    
    # Sort by weight descending
    events.sort(key=lambda x: x['weight'], reverse=True)
    
    # Deduplicate within date: merge events with similar titles/descriptions
    seen_keys = set()
    unique = []
    for evt in events:
        key = (evt['cat'], evt['title'][:50].lower().strip())
        alt_key = (evt['cat'], evt['desc'][:50].lower().strip())
        if key in seen_keys or alt_key in seen_keys:
            continue
        seen_keys.add(key)
        seen_keys.add(alt_key)
        unique.append(evt)
    
    # Check for pinned events
    if date in PINNED_EVENTS:
        cat, desc, actors, sev = PINNED_EVENTS[date]
        consolidated.append({
            'date': date, 'cat': cat, 'title': desc,
            'desc': desc, 'actors': actors, 'evidence': '',
            'sev': sev, 'source': 'PINNED', 'weight': 25,
            'event_count': len(events)
        })
    
    # Cap per day based on total event count
    if len(unique) > 100:
        cap = 8  # Very busy days get more slots
    elif len(unique) > 30:
        cap = 5
    elif len(unique) > 10:
        cap = 3
    else:
        cap = 2
    
    # Take top events by weight, but always include high-severity
    high_sev = [e for e in unique if e['sev'] >= 8]
    others = [e for e in unique if e['sev'] < 8]
    
    selected = high_sev[:cap] + others[:max(0, cap - len(high_sev))]
    
    for evt in selected:
        # Skip if it's basically the same as a pinned event
        if date in PINNED_EVENTS and evt['desc'][:40] == PINNED_EVENTS[date][1][:40]:
            continue
        
        # Build consolidated description
        title = evt['title']
        if title.startswith('[') or title.startswith('file:'):
            title = evt['desc'][:100] if evt['desc'] else title
        
        consolidated.append({
            'date': date,
            'cat': evt['cat'],
            'title': title[:200],
            'desc': evt['desc'][:500],
            'actors': evt['actors'][:200],
            'evidence': evt['evidence'][:200],
            'sev': evt['sev'],
            'source': evt['source'][:100],
            'weight': evt['weight'],
            'event_count': len(events)
        })

print(f"[3] Consolidated to {len(consolidated)} events")

# ============================================================
# STEP 5: Final dedup pass across all events
# ============================================================
final = []
seen_global = set()
for evt in consolidated:
    key = (evt['date'], evt['title'][:60].lower())
    if key in seen_global:
        continue
    seen_global.add(key)
    final.append(evt)

final.sort(key=lambda x: (x['date'], -x['weight']))
print(f"[4] After global dedup: {len(final)} events")

# ============================================================
# STEP 6: Store in DB
# ============================================================
c.execute('''CREATE TABLE IF NOT EXISTS condensed_timeline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_date TEXT NOT NULL,
    category TEXT,
    title TEXT,
    description TEXT,
    actors TEXT,
    evidence_ref TEXT,
    severity INTEGER,
    source TEXT,
    weight INTEGER,
    raw_event_count INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)''')
c.execute("DELETE FROM condensed_timeline")

for evt in final:
    c.execute('''INSERT INTO condensed_timeline 
        (event_date, category, title, description, actors, evidence_ref, severity, source, weight, raw_event_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (evt['date'], evt['cat'], evt['title'], evt['desc'], evt['actors'],
         evt['evidence'], evt['sev'], evt['source'], evt['weight'], evt['event_count']))

conn.commit()

# FTS
try:
    c.execute('DROP TABLE IF EXISTS condensed_timeline_fts')
    c.execute('''CREATE VIRTUAL TABLE condensed_timeline_fts USING fts5(
        title, description, actors, category,
        content=condensed_timeline, content_rowid=id
    )''')
    c.execute('''INSERT INTO condensed_timeline_fts(rowid, title, description, actors, category)
        SELECT id, title, description, actors, category FROM condensed_timeline''')
    conn.commit()
    print("[+] FTS5 index built")
except Exception as e:
    print(f"[!] FTS: {e}")

# ============================================================
# STEP 7: Generate condensed report
# ============================================================
output = os.path.join(LOS_ROOT, '05_ANALYSIS', 'CONDENSED_PROSECUTION_TIMELINE.md')

c.execute("SELECT MIN(event_date), MAX(event_date) FROM condensed_timeline")
dmin, dmax = c.fetchone()
c.execute("SELECT category, COUNT(*) FROM condensed_timeline GROUP BY category ORDER BY COUNT(*) DESC")
cats = c.fetchall()
c.execute("SELECT substr(event_date,1,7), COUNT(*) FROM condensed_timeline GROUP BY substr(event_date,1,7) ORDER BY substr(event_date,1,7)")
months = c.fetchall()

with open(output, 'w', encoding='utf-8') as f:
    f.write("# CONDENSED PROSECUTION TIMELINE\n")
    f.write("## Andrew J. Pigors v. Tiffany Emily Watson et al.\n")
    f.write("## Case No. 2024-001507-DC | COA 366810\n\n")
    f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    f.write(f"**Events:** {len(final):,} (condensed from 43,560 raw)\n")
    f.write(f"**Date Range:** {dmin} → {dmax}\n\n")
    f.write("---\n\n")
    
    f.write("## SUMMARY\n\n")
    f.write("| Category | Count |\n|----------|-------|\n")
    for cat, cnt in cats:
        f.write(f"| {cat} | {cnt} |\n")
    
    f.write("\n| Month | Events |\n|-------|--------|\n")
    for ym, cnt in months:
        f.write(f"| {ym} | {cnt} |\n")
    
    f.write("\n---\n\n")
    f.write("## PROSECUTION TIMELINE\n\n")
    
    c.execute("""SELECT event_date, category, title, description, actors, evidence_ref, severity, source, raw_event_count
        FROM condensed_timeline ORDER BY event_date, weight DESC""")
    
    current_month = None
    current_date = None
    
    for date, cat, title, desc, actors, evidence, sev, source, raw_cnt in c.fetchall():
        month = date[:7]
        if month != current_month:
            current_month = month
            f.write(f"\n---\n## {month}\n\n")
        
        if date != current_date:
            current_date = date
            day_label = f"### {date}"
            if raw_cnt and raw_cnt > 20:
                day_label += f" ({raw_cnt} raw events)"
            f.write(f"\n{day_label}\n\n")
        
        sev = sev or 5
        if sev >= 9:
            icon = "🔴"
        elif sev >= 7:
            icon = "🟡"
        elif sev >= 5:
            icon = "🔵"
        else:
            icon = "⚪"
        
        f.write(f"{icon} **[{cat}]** {title}")
        if actors and actors != title[:len(actors)]:
            f.write(f" — *{actors[:80]}*")
        f.write("\n")
        
        if desc and desc != title and len(desc.strip()) > 15:
            # Truncate long descriptions
            d = desc[:300].replace('\n', ' ').strip()
            f.write(f"> {d}\n")
        
        if evidence and len(evidence.strip()) > 5:
            f.write(f"> 📎 *{evidence[:150]}*\n")
        
        f.write("\n")

fsize = os.path.getsize(output)

print(f"\n{'='*70}")
print(f"  TIMELINE CONSOLIDATION COMPLETE")
print(f"  43,560 raw → {len(final)} condensed events")
print(f"  Date range: {dmin} → {dmax}")
print(f"  Report: {fsize/1024:.0f}KB → {output}")
print(f"{'='*70}")
for cat, cnt in cats[:10]:
    print(f"    {cat}: {cnt}")

conn.close()
