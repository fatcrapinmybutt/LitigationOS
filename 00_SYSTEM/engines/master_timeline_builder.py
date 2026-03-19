#!/usr/bin/env python3
"""
MASTER CHRONOLOGICAL TIMELINE BUILDER v2.0
Scans ALL database tables and ALL LitigationOS files to build
the definitive prosecution timeline with full context.

Phase 1: Extract every dated event from every DB table
Phase 2: Scan all text files for date-stamped events
Phase 3: Deduplicate, normalize, and merge
Phase 4: Output master timeline markdown
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
print("  MASTER CHRONOLOGICAL TIMELINE BUILDER v2.0")
print("  Extracting from ALL DB tables + ALL files")
print("=" * 70)

# Master event list: [(date_str, time_str, source, category, title, description, actors, evidence, severity)]
events = []

# ============================================================
# PHASE 1: EXTRACT FROM ALL DATABASE TABLES
# ============================================================
print("\n[PHASE 1] Extracting from database tables...")

# 1a. prosecution_timeline (existing timeline - 1,899 events)
c.execute("""SELECT event_date, event_time, event_type, event_title, event_description, 
    actors, evidence_ref, severity FROM prosecution_timeline 
    WHERE event_date IS NOT NULL""")
count = 0
for date, time, etype, title, desc, actors, evidence, severity in c.fetchall():
    events.append((str(date or ''), str(time or ''), 'prosecution_timeline', 
                   etype or 'UNKNOWN', title or '', desc or '', actors or '', evidence or '', severity or 5))
    count += 1
print(f"  prosecution_timeline: {count} events")

# 1b. appclose_messages
try:
    c.execute("PRAGMA table_info(appclose_messages)")
    cols = [r[1] for r in c.fetchall()]
    date_col = 'message_date' if 'message_date' in cols else 'date' if 'date' in cols else 'sent_date' if 'sent_date' in cols else 'timestamp' if 'timestamp' in cols else None
    sender_col = 'sender' if 'sender' in cols else 'from_user' if 'from_user' in cols else None
    msg_col = 'message_text' if 'message_text' in cols else 'message' if 'message' in cols else 'content' if 'content' in cols else 'text' if 'text' in cols else None
    
    if date_col and msg_col:
        query = f"SELECT {date_col}, {sender_col + ',' if sender_col else ''} {msg_col} FROM appclose_messages WHERE {date_col} IS NOT NULL ORDER BY {date_col}"
        c.execute(query)
        count = 0
        for row in c.fetchall():
            if sender_col:
                date_val, sender, msg = row[0], row[1], row[2]
            else:
                date_val, sender, msg = row[0], 'Unknown', row[1]
            events.append((str(date_val), '', 'appclose_messages', 'COMMUNICATION',
                          f'AppClose: {sender}', str(msg or '')[:300], str(sender or ''), '', 3))
            count += 1
        print(f"  appclose_messages: {count} events")
except Exception as e:
    print(f"  appclose_messages: skipped ({e})")

# 1c. judicial_violations
try:
    c.execute("PRAGMA table_info(judicial_violations)")
    cols = [r[1] for r in c.fetchall()]
    date_col = next((c for c in cols if 'date' in c.lower()), None)
    desc_col = next((c for c in cols if c in ('description', 'violation_description', 'details')), None)
    type_col = next((c for c in cols if c in ('violation_type', 'type', 'category')), None)
    
    if date_col:
        fields = [date_col]
        if desc_col: fields.append(desc_col)
        if type_col: fields.append(type_col)
        c.execute(f"SELECT {','.join(fields)} FROM judicial_violations WHERE {date_col} IS NOT NULL")
        count = 0
        for row in c.fetchall():
            d = str(row[0])
            desc = str(row[1]) if len(row) > 1 else ''
            vtype = str(row[2]) if len(row) > 2 else 'JUDICIAL_VIOLATION'
            events.append((d, '', 'judicial_violations', 'JUDICIAL_VIOLATION',
                          f'Judicial Violation: {vtype}', desc[:500], 'Judge McNeill', '', 9))
            count += 1
        print(f"  judicial_violations: {count} events")
except Exception as e:
    print(f"  judicial_violations: skipped ({e})")

# 1d. constitutional_violations
try:
    c.execute("SELECT incident_date, amendment, violation_type, description, actors FROM constitutional_violations WHERE incident_date IS NOT NULL")
    count = 0
    for date, amend, vtype, desc, actors in c.fetchall():
        events.append((str(date), '', 'constitutional_violations', 'CONSTITUTIONAL',
                      f'{amend}: {vtype}', str(desc or '')[:500], str(actors or ''), '', 10))
        count += 1
    print(f"  constitutional_violations: {count} events")
except Exception as e:
    print(f"  constitutional_violations: skipped ({e})")

# 1e. damages_itemization
try:
    c.execute("SELECT date_incurred, category, description, amount, legal_basis FROM damages_itemization WHERE date_incurred IS NOT NULL")
    count = 0
    for date, cat, desc, amt, basis in c.fetchall():
        events.append((str(date), '', 'damages_itemization', 'DAMAGES',
                      f'Damages: {cat}', f'{desc} — ${amt:,.0f}' if amt else str(desc or ''), '', str(basis or ''), 7))
        count += 1
    print(f"  damages_itemization: {count} events")
except Exception as e:
    print(f"  damages_itemization: skipped ({e})")

# 1f. evidence_documents
try:
    c.execute("PRAGMA table_info(evidence_documents)")
    cols = [r[1] for r in c.fetchall()]
    date_col = next((c for c in cols if 'date' in c.lower()), None)
    title_col = next((c for c in cols if c in ('title', 'document_title', 'name', 'file_name')), None)
    type_col = next((c for c in cols if c in ('doc_type', 'document_type', 'type', 'category')), None)
    
    if date_col:
        fields = [date_col]
        if title_col: fields.append(title_col)
        if type_col: fields.append(type_col)
        c.execute(f"SELECT {','.join(fields)} FROM evidence_documents WHERE {date_col} IS NOT NULL")
        count = 0
        for row in c.fetchall():
            d = str(row[0])
            title = str(row[1]) if len(row) > 1 else 'Evidence Document'
            dtype = str(row[2]) if len(row) > 2 else 'EVIDENCE'
            events.append((d, '', 'evidence_documents', 'EVIDENCE',
                          f'Evidence: {title[:100]}', dtype, '', '', 6))
            count += 1
        print(f"  evidence_documents: {count} events")
except Exception as e:
    print(f"  evidence_documents: skipped ({e})")

# 1g. filing_documents
try:
    c.execute("PRAGMA table_info(filing_documents)")
    cols = [r[1] for r in c.fetchall()]
    date_col = next((c for c in cols if 'date' in c.lower()), None)
    title_col = next((c for c in cols if c in ('title', 'document_title', 'name')), None)
    type_col = next((c for c in cols if c in ('doc_type', 'filing_type', 'type')), None)
    court_col = next((c for c in cols if c in ('court', 'court_name')), None)
    
    if date_col:
        fields = [date_col]
        if title_col: fields.append(title_col)
        if type_col: fields.append(type_col)
        if court_col: fields.append(court_col)
        c.execute(f"SELECT {','.join(fields)} FROM filing_documents WHERE {date_col} IS NOT NULL")
        count = 0
        for row in c.fetchall():
            d = str(row[0])
            title = str(row[1]) if len(row) > 1 else 'Court Filing'
            ftype = str(row[2]) if len(row) > 2 else ''
            court = str(row[3]) if len(row) > 3 else ''
            events.append((d, '', 'filing_documents', 'COURT_FILING',
                          f'Filing: {title[:100]}', f'{ftype} — {court}', '', '', 8))
            count += 1
        print(f"  filing_documents: {count} events")
except Exception as e:
    print(f"  filing_documents: skipped ({e})")

# 1h. evidence_quotes with date references
try:
    c.execute("SELECT date_ref, quote_text, speaker, evidence_category, legal_significance FROM evidence_quotes WHERE date_ref IS NOT NULL AND date_ref != ''")
    count = 0
    for date, quote, speaker, cat, sig in c.fetchall():
        events.append((str(date), '', 'evidence_quotes', str(cat or 'QUOTE'),
                      f'Quote ({speaker or "Unknown"})', str(quote or '')[:300], str(speaker or ''), str(sig or ''), 6))
        count += 1
    print(f"  evidence_quotes: {count} events")
except Exception as e:
    print(f"  evidence_quotes: skipped ({e})")

# 1i. psych_analysis_results
try:
    c.execute("SELECT message_date, sender, message_text, pattern_detected, pattern_category, severity FROM psych_analysis_results WHERE message_date IS NOT NULL")
    count = 0
    for date, sender, msg, pattern, cat, sev in c.fetchall():
        sev_num = 8 if sev == 'HIGH' else 6 if sev == 'MEDIUM' else 4
        events.append((str(date), '', 'psych_analysis', str(cat or 'PSYCH'),
                      f'Psych Pattern: {pattern or "detected"}', str(msg or '')[:300], str(sender or ''), '', sev_num))
        count += 1
    print(f"  psych_analysis_results: {count} events")
except Exception as e:
    print(f"  psych_analysis_results: skipped ({e})")

# 1j. Scan ALL other tables for date columns dynamically
print("\n  Scanning remaining tables for date columns...")
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '%fts%' AND name NOT LIKE '%_config' AND name NOT LIKE '%_content' AND name NOT LIKE '%_data' AND name NOT LIKE '%_idx' AND name NOT LIKE '%_docsize'")
all_tables = [r[0] for r in c.fetchall()]
ALREADY_SCANNED = {'prosecution_timeline', 'appclose_messages', 'judicial_violations', 
                   'constitutional_violations', 'damages_itemization', 'evidence_documents',
                   'filing_documents', 'evidence_quotes', 'psych_analysis_results',
                   'adversary_assertions', 'citation_validation', 'filing_compliance',
                   'impeachment_index', 'alienation_scoring', 'exhibit_registry',
                   'filing_finalization', 'filing_sequence', 'omega_analysis_summary',
                   'disk_inventory_omega', 'rebuttal_matrix', 'sqlite_sequence'}

extra_count = 0
for table in all_tables:
    if table in ALREADY_SCANNED:
        continue
    try:
        c.execute(f"PRAGMA table_info({table})")
        cols = [r[1] for r in c.fetchall()]
        date_cols = [col for col in cols if any(d in col.lower() for d in ['date', 'timestamp', 'created', 'filed', 'occurred'])]
        text_cols = [col for col in cols if any(t in col.lower() for t in ['text', 'content', 'description', 'title', 'name', 'message', 'body', 'summary', 'detail'])]
        
        if not date_cols:
            continue
        
        dc = date_cols[0]
        tc = text_cols[0] if text_cols else None
        
        query = f"SELECT {dc}"
        if tc:
            query += f", {tc}"
        query += f" FROM {table} WHERE {dc} IS NOT NULL AND {dc} != '' LIMIT 500"
        
        c.execute(query)
        rows = c.fetchall()
        for row in rows:
            d = str(row[0])
            # Validate it looks like a date
            if not re.search(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', d):
                continue
            text = str(row[1])[:300] if len(row) > 1 else ''
            events.append((d, '', table, 'DB_RECORD', f'[{table}]', text, '', '', 4))
            extra_count += 1
    except:
        continue

print(f"  Additional tables: {extra_count} events from dynamic scan")

print(f"\n  PHASE 1 TOTAL: {len(events)} events from database")

# ============================================================
# PHASE 2: SCAN ALL TEXT FILES FOR DATED EVENTS
# ============================================================
print("\n[PHASE 2] Scanning LitigationOS files for dated events...")

DATE_PATTERNS = [
    # ISO format: 2024-01-15
    (r'(\d{4}-\d{1,2}-\d{1,2})', '%Y-%m-%d'),
    # US format: 01/15/2024 or 1/15/2024
    (r'(\d{1,2}/\d{1,2}/\d{4})', '%m/%d/%Y'),
    # Written: January 15, 2024
    (r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})', None),
    # Written short: Jan 15, 2024
    (r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})', None),
]

MONTH_MAP = {
    'january': '01', 'february': '02', 'march': '03', 'april': '04',
    'may': '05', 'june': '06', 'july': '07', 'august': '08',
    'september': '09', 'october': '10', 'november': '11', 'december': '12',
    'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
    'jun': '06', 'jul': '07', 'aug': '08', 'sep': '09',
    'oct': '10', 'nov': '11', 'dec': '12'
}

def normalize_date(date_str):
    """Normalize any date format to YYYY-MM-DD."""
    date_str = date_str.strip().rstrip(',')
    
    # Try ISO
    m = re.match(r'^(\d{4})-(\d{1,2})-(\d{1,2})', date_str)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    
    # Try US format
    m = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})', date_str)
    if m:
        return f"{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    
    # Try written format
    for month_name, month_num in MONTH_MAP.items():
        if month_name in date_str.lower():
            m = re.search(r'(\d{1,2}),?\s+(\d{4})', date_str)
            if m:
                return f"{m.group(2)}-{month_num}-{int(m.group(1)):02d}"
    
    return date_str

def extract_context(content, pos, window=150):
    """Extract surrounding context around a date match."""
    start = max(0, pos - window)
    end = min(len(content), pos + window)
    ctx = content[start:end].replace('\n', ' ').strip()
    return ctx

SKIP_DIRS = {'.git', 'node_modules', '__pycache__', '.agents', '.copilot', '10_ARCHIVES'}
SCAN_EXTENSIONS = {'.md', '.txt', '.csv', '.log'}

file_events = 0
files_scanned = 0
seen_file_events = set()  # Dedup within files

for root, dirs, files in os.walk(LOS_ROOT):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    
    for fname in files:
        ext = os.path.splitext(fname)[1].lower()
        if ext not in SCAN_EXTENSIONS:
            continue
        
        fpath = os.path.join(root, fname)
        try:
            size = os.path.getsize(fpath)
            if size > 5_000_000 or size < 50:  # Skip >5MB and tiny files
                continue
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except:
            continue
        
        files_scanned += 1
        rel_path = os.path.relpath(fpath, LOS_ROOT)
        
        # Extract dates with context
        for pattern, fmt in DATE_PATTERNS:
            for match in re.finditer(pattern, content):
                raw_date = match.group(1)
                normalized = normalize_date(raw_date)
                
                # Validate year range
                year_match = re.search(r'(\d{4})', normalized)
                if year_match:
                    year = int(year_match.group(1))
                    if year < 2015 or year > 2027:
                        continue
                
                context = extract_context(content, match.start())
                
                # Dedup key
                dedup_key = (normalized, context[:80])
                if dedup_key in seen_file_events:
                    continue
                seen_file_events.add(dedup_key)
                
                # Determine category from file path
                category = 'FILE_EVENT'
                if '04_COURT_FILINGS' in rel_path:
                    category = 'COURT_FILING'
                elif '02_EVIDENCE' in rel_path:
                    category = 'EVIDENCE'
                elif '03_COMMUNICATIONS' in rel_path or 'appclose' in fname.lower():
                    category = 'COMMUNICATION'
                elif '05_ANALYSIS' in rel_path:
                    category = 'ANALYSIS'
                elif 'affidavit' in fname.lower():
                    category = 'AFFIDAVIT'
                elif 'police' in fname.lower() or 'report' in fname.lower():
                    category = 'POLICE_REPORT'
                elif 'order' in fname.lower():
                    category = 'COURT_ORDER'
                elif 'motion' in fname.lower():
                    category = 'MOTION'
                
                events.append((normalized, '', f'file:{rel_path}', category,
                              fname, context[:300], '', '', 5))
                file_events += 1

print(f"  Files scanned: {files_scanned}")
print(f"  File events extracted: {file_events}")

print(f"\n  TOTAL RAW EVENTS: {len(events)}")

# ============================================================
# PHASE 3: NORMALIZE, DEDUPLICATE, AND SORT
# ============================================================
print("\n[PHASE 3] Normalizing and deduplicating...")

# Normalize all dates
normalized_events = []
for date, time, source, category, title, desc, actors, evidence, severity in events:
    norm_date = normalize_date(date)
    # Final validation
    if not re.match(r'^\d{4}-\d{2}-\d{2}', norm_date):
        continue
    normalized_events.append((norm_date, time, source, category, title, desc, actors, evidence, severity))

print(f"  After normalization: {len(normalized_events)} events")

# Sort chronologically
normalized_events.sort(key=lambda x: (x[0], -(int(x[8]) if isinstance(x[8], (int, float)) else 5), x[3]))

# Deduplicate (same date + similar description = likely duplicate)
final_events = []
seen = set()
for evt in normalized_events:
    # Dedup key: date + first 60 chars of description
    key = (evt[0], evt[4][:60] if evt[4] else evt[5][:60])
    if key in seen:
        continue
    seen.add(key)
    final_events.append(evt)

print(f"  After deduplication: {len(final_events)} events")

# ============================================================
# PHASE 4: STORE IN DATABASE
# ============================================================
print("\n[PHASE 4] Storing master timeline in database...")

c.execute('''CREATE TABLE IF NOT EXISTS master_timeline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_date TEXT NOT NULL,
    event_time TEXT,
    source TEXT,
    category TEXT,
    title TEXT,
    description TEXT,
    actors TEXT,
    evidence_ref TEXT,
    severity INTEGER DEFAULT 5,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)''')
c.execute("DELETE FROM master_timeline")

for date, time, source, category, title, desc, actors, evidence, severity in final_events:
    c.execute('''INSERT INTO master_timeline 
        (event_date, event_time, source, category, title, description, actors, evidence_ref, severity)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (date, time, source, category, title, desc, actors, evidence, severity))

conn.commit()

# Build FTS index
try:
    c.execute('DROP TABLE IF EXISTS master_timeline_fts')
    c.execute('''CREATE VIRTUAL TABLE master_timeline_fts USING fts5(
        title, description, actors, category,
        content=master_timeline, content_rowid=id
    )''')
    c.execute('''INSERT INTO master_timeline_fts(rowid, title, description, actors, category)
        SELECT id, title, description, actors, category FROM master_timeline''')
    conn.commit()
    print("[+] FTS5 index built")
except Exception as e:
    print(f"[!] FTS: {e}")

# ============================================================
# PHASE 5: GENERATE MASTER TIMELINE REPORT
# ============================================================
print("\n[PHASE 5] Generating master timeline report...")

output_path = os.path.join(LOS_ROOT, '05_ANALYSIS', 'MASTER_CHRONOLOGICAL_TIMELINE.md')

# Gather stats
c.execute("SELECT MIN(event_date), MAX(event_date) FROM master_timeline")
date_min, date_max = c.fetchone()

c.execute("SELECT category, COUNT(*) FROM master_timeline GROUP BY category ORDER BY COUNT(*) DESC")
cat_stats = c.fetchall()

c.execute("SELECT source, COUNT(*) FROM master_timeline GROUP BY source ORDER BY COUNT(*) DESC LIMIT 20")
source_stats = c.fetchall()

c.execute("SELECT event_date, COUNT(*) FROM master_timeline GROUP BY event_date ORDER BY COUNT(*) DESC LIMIT 10")
hottest_days = c.fetchall()

# Count by year-month
c.execute("SELECT substr(event_date,1,7) as ym, COUNT(*) FROM master_timeline GROUP BY ym ORDER BY ym")
monthly = c.fetchall()

with open(output_path, 'w', encoding='utf-8') as f:
    f.write("# MASTER CHRONOLOGICAL TIMELINE\n")
    f.write(f"## Andrew J. Pigors v. Tiffany Emily Watson\n")
    f.write(f"## Case No. 2024-001507-DC | COA 366810\n\n")
    f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    f.write(f"**Total Events:** {len(final_events):,}\n")
    f.write(f"**Date Range:** {date_min} to {date_max}\n")
    f.write(f"**Sources:** {len(set(e[2] for e in final_events))} unique sources\n\n")
    f.write("---\n\n")
    
    # Statistics
    f.write("## EVENT STATISTICS\n\n")
    f.write("### By Category\n\n")
    f.write("| Category | Count |\n|----------|-------|\n")
    for cat, cnt in cat_stats:
        f.write(f"| {cat} | {cnt:,} |\n")
    
    f.write("\n### By Month\n\n")
    f.write("| Month | Events |\n|-------|--------|\n")
    for ym, cnt in monthly:
        f.write(f"| {ym} | {cnt:,} |\n")
    
    f.write("\n### Hottest Days (Most Events)\n\n")
    f.write("| Date | Events |\n|------|--------|\n")
    for d, cnt in hottest_days:
        f.write(f"| {d} | {cnt:,} |\n")
    
    f.write("\n### Top Sources\n\n")
    f.write("| Source | Events |\n|--------|--------|\n")
    for src, cnt in source_stats:
        f.write(f"| {src[:60]} | {cnt:,} |\n")
    
    f.write("\n---\n\n")
    
    # Full chronological timeline
    f.write("## FULL CHRONOLOGICAL TIMELINE\n\n")
    
    c.execute("""SELECT event_date, category, title, description, actors, evidence_ref, severity, source
        FROM master_timeline ORDER BY event_date, severity DESC""")
    
    current_month = None
    current_date = None
    
    for date, cat, title, desc, actors, evidence, severity, source in c.fetchall():
        month = date[:7] if date else 'Unknown'
        
        if month != current_month:
            current_month = month
            f.write(f"\n---\n\n## {month}\n\n")
        
        if date != current_date:
            current_date = date
            f.write(f"\n### 📅 {date}\n\n")
        
        # Severity indicator
        sev = int(severity) if isinstance(severity, (int, float)) else (int(severity) if str(severity).isdigit() else 5)
        if sev >= 9:
            icon = "🔴"
        elif sev >= 7:
            icon = "🟡"
        elif sev >= 5:
            icon = "🔵"
        else:
            icon = "⚪"
        
        f.write(f"{icon} **[{cat}]** {title}")
        if actors:
            f.write(f" *(Actors: {actors[:100]})*")
        f.write("\n")
        
        if desc and desc != title:
            f.write(f"> {desc[:500]}\n")
        
        if evidence:
            f.write(f"> *Evidence: {evidence[:200]}*\n")
        
        f.write(f"> *Source: {source[:80]}*\n\n")

file_size = os.path.getsize(output_path)

# ============================================================
# SUMMARY
# ============================================================
print(f"\n{'='*70}")
print(f"  MASTER CHRONOLOGICAL TIMELINE COMPLETE")
print(f"  Events: {len(final_events):,} (from {len(events):,} raw)")
print(f"  Date range: {date_min} → {date_max}")
print(f"  Categories: {len(cat_stats)}")
print(f"  Report: {file_size/1024:.0f}KB → {output_path}")
print(f"{'='*70}")

print(f"\n  Top categories:")
for cat, cnt in cat_stats[:8]:
    print(f"    {cat}: {cnt:,}")

print(f"\n  Hottest days:")
for d, cnt in hottest_days[:5]:
    print(f"    {d}: {cnt} events")

conn.close()
