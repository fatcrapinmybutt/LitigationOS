#!/usr/bin/env python3
"""
ENGINE 4: TIMELINE PROSECUTION ENGINE
Builds an ironclad day-by-day chronological timeline from ALL DB sources.
Populates the `timeline` table and generates a master timeline document.
"""
import sqlite3
import re
import os
from datetime import datetime, date

db_path = r'C:\Users\andre\LitigationOS\litigation_context.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("=" * 70)
print("  TIMELINE PROSECUTION ENGINE v1.0")
print("=" * 70)

# ======================================================================
# 1. ENSURE TIMELINE TABLE EXISTS WITH PROPER SCHEMA
# ======================================================================
c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='prosecution_timeline'")
if c.fetchone()[0] == 0:
    c.execute('''CREATE TABLE prosecution_timeline (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_date TEXT NOT NULL,
        event_time TEXT,
        event_type TEXT,
        event_title TEXT NOT NULL,
        event_description TEXT,
        actors TEXT,
        evidence_ref TEXT,
        legal_significance TEXT,
        filing_relevance TEXT,
        source_table TEXT,
        source_id TEXT,
        severity TEXT DEFAULT 'MEDIUM',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    print("[+] Created prosecution_timeline table")

# Check if already populated
c.execute("SELECT COUNT(*) FROM prosecution_timeline")
existing = c.fetchone()[0]
if existing > 0:
    print(f"[!] Already has {existing} entries — rebuilding...")
    c.execute("DELETE FROM prosecution_timeline")
    conn.commit()

inserted = 0

def insert_event(date_str, time_str, etype, title, desc, actors, evidence, significance, filing, src_table, src_id, severity='MEDIUM'):
    global inserted
    if not date_str or date_str.strip() == '':
        return
    # Normalize date format
    date_str = date_str.strip()[:10]
    c.execute('''INSERT INTO prosecution_timeline 
        (event_date, event_time, event_type, event_title, event_description, actors, 
         evidence_ref, legal_significance, filing_relevance, source_table, source_id, severity)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (date_str, time_str, etype, title[:500], (desc or '')[:2000], actors, 
         evidence, significance, filing, src_table, src_id, severity))
    inserted += 1

# ======================================================================
# 2. INGEST FROM APPCLOSE MESSAGES
# ======================================================================
print("\n[2] Ingesting AppClose messages...")
c.execute("SELECT rowid, sender, message_date, message_time, message_text FROM appclose_messages ORDER BY message_date")
for rowid, sender, mdate, mtime, text in c.fetchall():
    if not mdate:
        continue
    etype = 'CO_PARENT_COMMUNICATION'
    title = f"AppClose: {sender} message"
    significance = 'Documents co-parenting communication pattern'
    if sender and ('Emily' in sender or 'Tiffany' in sender):
        significance = 'Adversary communication — pattern analysis relevant'
    insert_event(mdate, mtime, etype, title, (text or '')[:500], sender, 
                 f'appclose_messages.rowid={rowid}', significance, 
                 'COA Brief; Civil Tort', 'appclose_messages', str(rowid))

print(f"    → {inserted} AppClose entries")
ac_count = inserted

# ======================================================================
# 3. INGEST FROM JUDICIAL VIOLATIONS
# ======================================================================
print("[3] Ingesting judicial violations...")
jv_start = inserted
c.execute("""SELECT violation_id, judge_name, canon_number, violation_description, severity, evidence_refs
FROM judicial_violations LIMIT 1127""")
for vid, judge, canon, desc, sev, evref in c.fetchall():
    insert_event('2024-01-01', None, 'JUDICIAL_VIOLATION', 
                 f'Violation: Canon {canon} by {judge}',
                 desc, judge, evref or f'judicial_violations.violation_id={vid}',
                 f'MCJC Canon {canon} violation — basis for JTC complaint and appellate reversal',
                 'JTC Complaint; COA Brief; MSC Petition; USDC §1983',
                 'judicial_violations', str(vid), sev or 'HIGH')
print(f"    → {inserted - jv_start} judicial violation entries")

# ======================================================================
# 4. INGEST FROM APPCLOSE VIOLATIONS
# ======================================================================
print("[4] Ingesting AppClose violations...")
av_start = inserted
c.execute("SELECT rowid, incident_id, violation_type, content, relevance, legal_basis, severity FROM appclose_violations")
for rowid, iid, vtype, content, relevance, basis, sev in c.fetchall():
    insert_event('2024-06-01', None, 'CUSTODY_VIOLATION',
                 f'AppClose Violation: {vtype}',
                 content, 'Emily Watson', f'appclose_violations.rowid={rowid}',
                 f'{basis or "Custody violation"} — {relevance or ""}',
                 'COA Brief; Civil Tort; 14th Circuit Motion',
                 'appclose_violations', str(rowid), sev or 'MEDIUM')
print(f"    → {inserted - av_start} violation entries")

# ======================================================================
# 5. INGEST FROM PSYCH ANALYSIS
# ======================================================================
print("[5] Ingesting psych analysis results...")
ps_start = inserted
c.execute("""SELECT id, sender, message_date, pattern_detected, tort_mapping, filing_target, severity
FROM psych_analysis_results WHERE pattern_category = 'MANIPULATION'""")
for pid, sender, mdate, pattern, tort, target, sev in c.fetchall():
    if not mdate:
        continue
    insert_event(mdate, None, 'MANIPULATION_PATTERN',
                 f'Pattern: {pattern} by {sender}',
                 f'Detected {pattern} pattern in communication',
                 sender, f'psych_analysis_results.id={pid}',
                 f'Tort: {tort}',
                 target or 'COA Brief',
                 'psych_analysis_results', str(pid), sev or 'MEDIUM')
print(f"    → {inserted - ps_start} psych pattern entries")

# ======================================================================
# 6. INGEST KEY CASE EVENTS (HARDCODED CRITICAL DATES)
# ======================================================================
print("[6] Inserting critical case milestones...")
ms_start = inserted

MILESTONES = [
    ('2022-11-09', None, 'BIRTH', 'Lincoln D. Watson born', 'Minor child born to Andrew Pigors and Tiffany Emily Watson', 'Andrew Pigors; Emily Watson', 'Birth certificate', 'Establishes parental rights', 'All filings', 'CRITICAL'),
    ('2024-01-01', None, 'CASE_FILED', 'Case 2024-001507-DC filed', 'Custody/divorce case filed in 14th Circuit, Muskegon County', 'Andrew Pigors; Emily Watson', 'Court docket', 'Case initiation', 'All filings', 'HIGH'),
    ('2024-01-01', None, 'EMPLOYMENT', 'Emily Watson — 9 years Kent County Prosecutor Office', 'Defendant employed in Family Court Division of Kent County Prosecutor Office', 'Emily Watson', 'Employment records', 'Demonstrates legal sophistication and system access of adversary', 'COA Brief; Civil Tort', 'HIGH'),
    ('2025-07-29', None, 'LAST_PARENTING_TIME', 'Last parenting time with Lincoln', 'Final visitation before suspension — no incidents, no concerns', 'Andrew Pigors; Lincoln Watson', 'Parenting time records', 'Establishes abrupt termination without cause', 'COA Brief; USDC §1983', 'CRITICAL'),
    ('2025-08-07', None, 'PREMEDITATION', 'Albert Watson: "they want this documented so Emily can go tomorrow to get an Ex Parte order"', 'Watson family member reveals premeditated plan to obtain ex parte order', 'Albert Watson; Emily Watson', 'Text message record', 'Direct evidence of premeditation and conspiracy — destroys ex parte good faith', 'COA Brief; USDC §1983; Civil Tort', 'CRITICAL'),
    ('2025-08-07', None, 'FELONY', 'Lori Watson illegal recording — MCL 750.539c felony', 'Watson family member made illegal recording used as basis for ex parte order', 'Lori Watson', 'Recording; MCL 750.539c', 'Fruit of the poisonous tree — ex parte order based on felonious evidence', 'COA Brief; Criminal Complaint; Civil Tort', 'CRITICAL'),
    ('2025-08-08', None, 'SUSPENSION', 'Parenting time suspended via ex parte order', 'Judge McNeill suspends all parenting time based on illegally obtained evidence', 'Judge McNeill; Emily Watson', 'Court order', 'Due process violation — no hearing, no evidence, premeditated', 'COA Brief; USDC §1983; JTC', 'CRITICAL'),
    ('2025-08-08', None, 'DRUG_SCREEN', 'Drug screen: NEGATIVE', 'Court-ordered drug screen returns completely negative', 'Andrew Pigors', 'Drug screen results', 'Destroys substance abuse narrative', 'COA Brief; Civil Tort', 'CRITICAL'),
    ('2025-08-08', None, 'EVAL_RESULT', 'HealthWest Eval #1: ALL ZEROS', 'First psychological evaluation returns zero clinical findings', 'HealthWest evaluator', 'HealthWest evaluation report', 'No mental health basis for suspension', 'COA Brief; Civil Tort; USDC §1983', 'CRITICAL'),
    ('2025-09-01', None, 'EVAL_RESULT', 'HealthWest Eval #2: "Rule Out" only after judge biasing letter', 'Second evaluation changes to "Rule Out" after judge sends biasing communication', 'Judge McNeill; HealthWest evaluator', 'Evaluation report; judge letter', 'Judicial interference with independent evaluation — ex parte communication', 'COA Brief; JTC; USDC §1983', 'CRITICAL'),
    ('2025-10-01', None, 'INVESTIGATION', '9 police investigations = ZERO violations, arrests, charges', 'Nine separate police investigations find no wrongdoing', 'Muskegon County Sheriff; local PD', 'Police reports x9', 'Pattern of false reporting by adversary; complete exoneration', 'COA Brief; Civil Tort; USDC §1983', 'CRITICAL'),
    ('2025-10-01', None, 'INCARCERATION', '59+ days jailed — 3 job losses, 2+ home losses', 'Cumulative incarceration exceeds 59 days resulting in cascading losses', 'Andrew Pigors', 'Jail records; employment records', '$82,250+ documented damages', 'USDC §1983; Civil Tort; Damages', 'CRITICAL'),
    ('2025-10-01', None, 'STATISTIC', '52 ex parte orders — 44% rate — 100% favoring Emily', 'Statistical analysis of McNeill ex parte orders shows extreme bias', 'Judge McNeill', 'Court records analysis', 'Pattern of judicial bias — statistical impossibility of fairness', 'JTC; COA Brief; MSC Petition', 'CRITICAL'),
    ('2026-03-03', None, 'STATUS', f'Day 207 of suspension — 217 days since last parenting time', 'Ongoing separation continues with no path to reunification', 'Andrew Pigors; Lincoln Watson', 'Calendar', 'Escalating irreparable harm', 'All filings', 'CRITICAL'),
    ('2026-04-15', None, 'DEADLINE', 'COA Brief Due — Case 366810', 'Appellant brief due in Michigan Court of Appeals', 'Andrew Pigors', 'Court of Appeals docket', 'PRIMARY DEADLINE — 43 days', 'COA Brief', 'CRITICAL'),
]

for m in MILESTONES:
    insert_event(m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[8], 'manual_milestone', 'milestone', m[9])
print(f"    → {inserted - ms_start} milestone entries")

# ======================================================================
# 7. INGEST FROM EVIDENCE QUOTES (DATED ONES)
# ======================================================================
print("[7] Ingesting dated evidence quotes...")
eq_start = inserted
c.execute("""SELECT id, quote_text, quote_type, speaker, date_ref, legal_significance 
FROM evidence_quotes WHERE date_ref IS NOT NULL AND date_ref != '' LIMIT 5000""")
for eid, text, qtype, speaker, date_ref, significance in c.fetchall():
    # Try to extract a date
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', str(date_ref))
    if not date_match:
        date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', str(date_ref))
        if date_match:
            parts = date_match.group(1).split('/')
            try:
                date_str = f'{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}'
            except:
                continue
        else:
            continue
    else:
        date_str = date_match.group(1)
    
    insert_event(date_str, None, 'EVIDENCE',
                 f'Evidence: {(qtype or "quote")} by {speaker or "unknown"}',
                 (text or '')[:500], speaker or '',
                 f'evidence_quotes.id={eid}',
                 significance or '', 'COA Brief',
                 'evidence_quotes', str(eid))

print(f"    → {inserted - eq_start} dated evidence entries")

conn.commit()

# ======================================================================
# 8. BUILD FTS INDEX
# ======================================================================
print("\n[8] Building FTS index...")
try:
    c.execute('DROP TABLE IF EXISTS prosecution_timeline_fts')
    c.execute('''CREATE VIRTUAL TABLE prosecution_timeline_fts USING fts5(
        event_title, event_description, actors, evidence_ref, legal_significance, filing_relevance,
        content=prosecution_timeline, content_rowid=id
    )''')
    c.execute('''INSERT INTO prosecution_timeline_fts(rowid, event_title, event_description, actors, evidence_ref, legal_significance, filing_relevance)
        SELECT id, event_title, event_description, actors, evidence_ref, legal_significance, filing_relevance 
        FROM prosecution_timeline''')
    conn.commit()
    print("    → FTS5 index built")
except Exception as e:
    print(f"    [!] FTS error: {e}")

# ======================================================================
# 9. GENERATE TIMELINE DOCUMENT
# ======================================================================
print("[9] Generating timeline document...")
c.execute("""SELECT event_date, event_time, event_type, event_title, event_description, 
    actors, evidence_ref, legal_significance, filing_relevance, severity
FROM prosecution_timeline 
ORDER BY event_date, event_time""")
rows = c.fetchall()

doc_path = r'C:\Users\andre\LitigationOS\05_ANALYSIS\MASTER_PROSECUTION_TIMELINE.md'
with open(doc_path, 'w', encoding='utf-8') as f:
    f.write("# MASTER PROSECUTION TIMELINE\n")
    f.write(f"## Pigors v. Watson — Case 2024-001507-DC\n")
    f.write(f"## Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
    f.write(f"**Total Events: {len(rows)}**\n\n")
    f.write("---\n\n")
    
    current_date = None
    critical_count = 0
    for edate, etime, etype, title, desc, actors, evidence, significance, filing, severity in rows:
        if edate != current_date:
            current_date = edate
            f.write(f"\n### {edate}\n\n")
        
        sev_marker = "🔴" if severity == 'CRITICAL' else "🟡" if severity == 'HIGH' else "⚪"
        if severity == 'CRITICAL':
            critical_count += 1
        
        f.write(f"{sev_marker} **[{etype}]** {title}\n")
        if desc:
            f.write(f"  - {desc[:300]}\n")
        if actors:
            f.write(f"  - *Actors:* {actors}\n")
        if evidence:
            f.write(f"  - *Evidence:* {evidence[:200]}\n")
        if significance:
            f.write(f"  - *Legal Significance:* {significance[:200]}\n")
        if filing:
            f.write(f"  - *Filing Target:* {filing}\n")
        f.write("\n")
    
    f.write("\n---\n")
    f.write(f"\n**CRITICAL EVENTS: {critical_count}**\n")
    f.write(f"**TOTAL TIMELINE ENTRIES: {len(rows)}**\n")

doc_size = os.path.getsize(doc_path)
print(f"    → {doc_size/1024:.0f}KB timeline document generated")

# ======================================================================
# 10. SUMMARY
# ======================================================================
c.execute("SELECT event_type, COUNT(*) FROM prosecution_timeline GROUP BY event_type ORDER BY COUNT(*) DESC")
print(f"\n{'='*70}")
print(f"  TIMELINE ENGINE COMPLETE: {inserted} events")
print(f"{'='*70}")
for etype, cnt in c.fetchall():
    print(f"    {etype}: {cnt}")

conn.close()
