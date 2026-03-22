#!/usr/bin/env python3
"""
APEX Evidence Timeline Builder v1.0
Cross-references brain DB intelligence with docket events, judicial violations,
and evidence quotes to build a unified chronological timeline.
Outputs to timeline_entries table in litigation_context.db (which was missing).
"""
import sys
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

import sqlite3
import re
import json
from datetime import datetime
from collections import defaultdict

BRAIN_DB = r'C:\Users\andre\LitigationOS\00_SYSTEM\brains\chat_intelligence_brain.db'
LIT_DB = r'C:\Users\andre\LitigationOS\litigation_context.db'

# Date extraction patterns
DATE_PATTERNS = [
    re.compile(r'\b(\d{4}-\d{2}-\d{2})\b'),                    # ISO: 2024-01-15
    re.compile(r'\b(\d{1,2}/\d{1,2}/\d{4})\b'),                 # US: 1/15/2024
    re.compile(r'\b(\d{1,2}/\d{1,2}/\d{2})\b'),                 # Short: 1/15/24
    re.compile(r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4})\b', re.IGNORECASE),
    re.compile(r'\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{4})\b', re.IGNORECASE),
]

MONTH_MAP = {
    'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
    'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
    'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
}

def normalize_date(date_str):
    """Convert various date formats to ISO YYYY-MM-DD"""
    date_str = date_str.strip().rstrip(',')
    
    # Already ISO
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', date_str)
    if m:
        return date_str
    
    # US format M/D/YYYY
    m = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})$', date_str)
    if m:
        return f"{m.group(3)}-{m.group(1).zfill(2)}-{m.group(2).zfill(2)}"
    
    # Short US M/D/YY
    m = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{2})$', date_str)
    if m:
        year = int(m.group(3))
        year = 2000 + year if year < 50 else 1900 + year
        return f"{year}-{m.group(1).zfill(2)}-{m.group(2).zfill(2)}"
    
    # Month name formats
    for pattern in [
        r'(\w+)\s+(\d{1,2}),?\s+(\d{4})',   # January 15, 2024
        r'(\d{1,2})\s+(\w+)\s+(\d{4})',       # 15 January 2024
    ]:
        m = re.match(pattern, date_str, re.IGNORECASE)
        if m:
            groups = m.groups()
            if groups[0].isdigit():
                day, month_name, year = groups
            else:
                month_name, day, year = groups
            month_key = month_name[:3].lower()
            if month_key in MONTH_MAP:
                return f"{year}-{MONTH_MAP[month_key]}-{str(day).zfill(2)}"
    
    return None


def extract_dates(text):
    """Extract all dates from text, return as normalized ISO strings"""
    dates = set()
    for pattern in DATE_PATTERNS:
        for match in pattern.finditer(text):
            iso = normalize_date(match.group(1))
            if iso and '2018' <= iso[:4] <= '2027':  # Reasonable range
                dates.add(iso)
    return sorted(dates)


def categorize_event(text):
    """Categorize a timeline event"""
    text_lower = text.lower()
    
    categories = [
        ('court_hearing', ['hearing', 'proceedings', 'appeared', 'the court']),
        ('court_order', ['order', 'ordered', 'judgment', 'it is hereby']),
        ('motion_filed', ['motion', 'filed', 'moves this court']),
        ('custody_event', ['custody', 'parenting time', 'visitation', 'pick up', 'drop off']),
        ('ppo_event', ['ppo', 'protection order', 'restraining', 'no contact']),
        ('police_event', ['police', 'officer', 'arrest', 'jail', 'incarcerat']),
        ('housing_event', ['evict', 'lockout', 'property', 'shady oaks', 'rent', 'lease']),
        ('evidence_event', ['recording', 'video', 'photo', 'document', 'exhibit']),
        ('communication', ['email', 'text', 'message', 'called', 'voicemail']),
        ('cps_event', ['cps', 'dhhs', 'child protective', 'investigation']),
        ('legal_filing', ['brief', 'appeal', 'petition', 'complaint', 'response']),
        ('misconduct', ['bias', 'misconduct', 'ex parte', 'jtc', 'disqualif']),
    ]
    
    for cat, keywords in categories:
        if any(kw in text_lower for kw in keywords):
            return cat
    return 'general_event'


def setup_timeline_table(lit_db):
    """Create timeline_entries table if it doesn't exist"""
    lit_db.execute("""CREATE TABLE IF NOT EXISTS timeline_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_date TEXT NOT NULL,
        event_type TEXT,
        description TEXT,
        lane TEXT,
        source TEXT,
        source_id TEXT,
        actors TEXT,
        confidence REAL DEFAULT 0.5,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    lit_db.execute('CREATE INDEX IF NOT EXISTS idx_timeline_date ON timeline_entries(event_date)')
    lit_db.execute('CREATE INDEX IF NOT EXISTS idx_timeline_lane ON timeline_entries(lane)')
    lit_db.execute('CREATE INDEX IF NOT EXISTS idx_timeline_type ON timeline_entries(event_type)')
    lit_db.commit()


def harvest_from_brain(brain_db, limit=5000):
    """Extract dated events from brain DB high-relevance messages"""
    rows = brain_db.execute("""
        SELECT rowid, content, lanes, source_platform, legal_relevance_score, is_user_truth
        FROM chat_intelligence 
        WHERE legal_relevance_score >= 0.5
        AND length(content) BETWEEN 30 AND 2000
        ORDER BY legal_relevance_score DESC
        LIMIT ?
    """, (limit,)).fetchall()
    
    events = []
    for rowid, content, lanes, platform, score, is_user in rows:
        dates = extract_dates(content)
        if not dates:
            continue
        
        # Create one event per date found
        for date in dates:
            event_type = categorize_event(content)
            # Use first 300 chars as description
            desc = content[:300].strip()
            if len(content) > 300:
                desc += '...'
            
            confidence = score * (1.2 if is_user else 0.8)
            confidence = min(1.0, confidence)
            
            events.append({
                'date': date,
                'type': event_type,
                'description': desc,
                'lane': lanes or '',
                'source': f'brain:{platform}',
                'source_id': str(rowid),
                'confidence': round(confidence, 3)
            })
    
    return events


def harvest_from_docket(lit_db):
    """Pull existing docket events into timeline format"""
    rows = lit_db.execute("""
        SELECT event_date, event_type, description, filed_by, case_number
        FROM docket_events 
        WHERE event_date IS NOT NULL
        ORDER BY event_date
    """).fetchall()
    
    events = []
    for date, etype, desc, filed_by, case_num in rows:
        iso = normalize_date(str(date)) if date else None
        if not iso:
            continue
        
        lane = ''
        if case_num:
            if '001507' in str(case_num):
                lane = 'A'
            elif '5907' in str(case_num):
                lane = 'D'
            elif '002760' in str(case_num):
                lane = 'B'
        
        events.append({
            'date': iso,
            'type': etype or 'docket_event',
            'description': f"[{case_num}] {desc}" if case_num else str(desc),
            'lane': lane,
            'source': 'docket_events',
            'source_id': f'{case_num}:{date}',
            'confidence': 0.95  # Court records = high confidence
        })
    
    return events


def harvest_from_violations(lit_db):
    """Pull judicial violations into timeline"""
    rows = lit_db.execute("""
        SELECT date_occurred, violation_type, description, mcr_rule, severity, lane
        FROM judicial_violations
        WHERE date_occurred IS NOT NULL
    """).fetchall()
    
    events = []
    for date, vtype, desc, mcr, severity, lane in rows:
        iso = normalize_date(str(date)) if date else None
        if not iso:
            continue
        
        events.append({
            'date': iso,
            'type': 'judicial_violation',
            'description': f"[{vtype}] {desc} (MCR {mcr})" if mcr else f"[{vtype}] {desc}",
            'lane': lane or 'E',
            'source': 'judicial_violations',
            'source_id': f'{vtype}:{date}',
            'confidence': 0.9
        })
    
    return events


def deduplicate_events(events):
    """Remove duplicate events (same date + similar description)"""
    seen = set()
    unique = []
    for e in events:
        # Key: date + first 80 chars of description
        key = f"{e['date']}:{e['description'][:80].lower()}"
        if key not in seen:
            seen.add(key)
            unique.append(e)
    return unique


def main():
    print("=" * 60)
    print("APEX Evidence Timeline Builder v1.0")
    print("=" * 60)
    
    brain = sqlite3.connect(BRAIN_DB)
    brain.execute('PRAGMA busy_timeout=60000')
    
    lit = sqlite3.connect(LIT_DB)
    lit.execute('PRAGMA busy_timeout=60000')
    lit.execute('PRAGMA journal_mode=WAL')
    lit.execute('PRAGMA cache_size=-32000')
    
    # Create timeline table
    setup_timeline_table(lit)
    existing = lit.execute("SELECT COUNT(*) FROM timeline_entries").fetchone()[0]
    print(f"Existing timeline entries: {existing}")
    
    # Harvest from all sources
    print("\nHarvesting from brain DB...")
    brain_events = harvest_from_brain(brain)
    print(f"  Brain events with dates: {len(brain_events)}")
    
    print("Harvesting from docket events...")
    docket_events = harvest_from_docket(lit)
    print(f"  Docket events: {len(docket_events)}")
    
    print("Harvesting from judicial violations...")
    violation_events = harvest_from_violations(lit)
    print(f"  Violation events: {len(violation_events)}")
    
    # Combine and deduplicate
    all_events = brain_events + docket_events + violation_events
    all_events = deduplicate_events(all_events)
    all_events.sort(key=lambda e: e['date'])
    print(f"\nTotal unique events: {len(all_events)}")
    
    # Insert
    batch = [(
        e['date'], e['type'], e['description'], e['lane'],
        e['source'], e['source_id'], '', e['confidence'],
        datetime.now().isoformat()
    ) for e in all_events]
    
    lit.executemany("""INSERT OR IGNORE INTO timeline_entries 
        (event_date, event_type, description, lane, source, source_id, 
         actors, confidence, created_at)
        VALUES (?,?,?,?,?,?,?,?,?)""", batch)
    lit.commit()
    
    final_count = lit.execute("SELECT COUNT(*) FROM timeline_entries").fetchone()[0]
    
    # Stats
    print(f"\n{'=' * 60}")
    print(f"Timeline Build Complete!")
    print(f"  New entries: {final_count - existing}")
    print(f"  Total entries: {final_count}")
    
    # Date range
    date_range = lit.execute("""
        SELECT MIN(event_date), MAX(event_date) FROM timeline_entries
    """).fetchone()
    print(f"  Date range: {date_range[0]} to {date_range[1]}")
    
    # By type
    print(f"\n  Events by type:")
    types = lit.execute("""
        SELECT event_type, COUNT(*) FROM timeline_entries 
        GROUP BY event_type ORDER BY COUNT(*) DESC
    """).fetchall()
    for t, c in types:
        print(f"    {t}: {c}")
    
    # By lane
    print(f"\n  Events by lane:")
    lanes = lit.execute("""
        SELECT lane, COUNT(*) FROM timeline_entries 
        WHERE lane != '' GROUP BY lane ORDER BY COUNT(*) DESC
    """).fetchall()
    for l, c in lanes:
        print(f"    Lane {l}: {c}")
    
    # By year
    print(f"\n  Events by year:")
    years = lit.execute("""
        SELECT substr(event_date, 1, 4) as yr, COUNT(*) FROM timeline_entries 
        GROUP BY yr ORDER BY yr
    """).fetchall()
    for y, c in years:
        print(f"    {y}: {c}")
    
    brain.close()
    lit.close()
    print(f"\n{'=' * 60}")

if __name__ == '__main__':
    main()
