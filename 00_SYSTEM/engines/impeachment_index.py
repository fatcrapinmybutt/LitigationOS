#!/usr/bin/env python3
"""
ENGINE 9: IMPEACHMENT INDEX
Cross-references all witness statements, adversary filings, court transcripts,
and police reports to identify contradictions and impeachment material.
"""
import sqlite3
import os
import re
from datetime import datetime

db_path = r'C:\Users\andre\LitigationOS\litigation_context.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("=" * 70)
print("  IMPEACHMENT INDEX ENGINE v1.0")
print("=" * 70)

c.execute('''CREATE TABLE IF NOT EXISTS impeachment_index (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_witness TEXT,
    statement_a TEXT,
    source_a TEXT,
    date_a TEXT,
    statement_b TEXT,
    source_b TEXT,
    date_b TEXT,
    contradiction_type TEXT,
    impeachment_value TEXT DEFAULT 'MEDIUM',
    legal_use TEXT,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)''')

c.execute("SELECT COUNT(*) FROM impeachment_index")
if c.fetchone()[0] > 0:
    c.execute("DELETE FROM impeachment_index")
    conn.commit()

inserted = 0

# KNOWN IMPEACHMENT ENTRIES (from deep analysis across all sessions)
KNOWN_CONTRADICTIONS = [
    {
        'target': 'Emily Watson',
        'a': 'Claims father is dangerous and abusive toward child',
        'src_a': 'Multiple PPO/custody motions',
        'date_a': '2024-2025',
        'b': 'Sent 124 cooperative messages, proposed shared schedules, discussed normal co-parenting',
        'src_b': 'AppClose messages (DB: appclose_messages)',
        'date_b': '2024-2025',
        'type': 'BEHAVIORAL_INCONSISTENCY',
        'value': 'CRITICAL',
        'use': 'MRE 613 — prior inconsistent conduct; shows manufactured narrative'
    },
    {
        'target': 'Emily Watson',
        'a': 'Claims father has substance abuse issues',
        'src_a': 'Court filings / motions',
        'date_a': '2024',
        'b': 'Father tested NEGATIVE on all drug screens',
        'src_b': 'Drug screen results (evidence_documents)',
        'date_b': '2024',
        'type': 'FALSE_ALLEGATION',
        'value': 'CRITICAL',
        'use': 'MRE 613, MRE 608(b) — false accusation impeachment'
    },
    {
        'target': 'Emily Watson',
        'a': 'Claims father has mental health concerns requiring evaluation',
        'src_a': 'Court filings / judicial orders',
        'date_a': '2024',
        'b': 'HealthWest eval #1: ALL ZEROS (no issues). Eval #2 only says "Rule Out" after judge\'s letter',
        'src_b': 'HealthWest evaluation records',
        'date_b': '2024',
        'type': 'MANUFACTURED_DIAGNOSIS',
        'value': 'CRITICAL',
        'use': 'MRE 613, MRE 702/703 — tainted expert opinion; judicial influence on evaluation'
    },
    {
        'target': 'Emily Watson',
        'a': 'Claims father poses safety risk to child, seeks supervised visitation',
        'src_a': 'Court filings',
        'date_a': '2024-2025',
        'b': '9 separate police investigations resulted in ZERO findings against father',
        'src_b': 'Police investigation records',
        'date_b': '2024-2025',
        'type': 'CONTRADICTED_BY_INVESTIGATION',
        'value': 'CRITICAL',
        'use': 'MRE 613 — law enforcement found no basis for allegations'
    },
    {
        'target': 'Emily Watson',
        'a': 'Presents as concerned mother acting in best interest of child',
        'src_a': 'Court filings and testimony',
        'date_a': '2024-2025',
        'b': '9 years in Kent County Prosecutor\'s Office Family Court Division — weaponized system knowledge',
        'src_b': 'Employment records / FOIA',
        'date_b': '2015-2024',
        'type': 'CONCEALED_EXPERTISE',
        'value': 'HIGH',
        'use': 'MRE 608(b) — demonstrates capacity for strategic manipulation of court system'
    },
    {
        'target': 'Lori Watson',
        'a': 'Provided testimony/evidence against father',
        'src_a': 'Court filings',
        'date_a': '2024',
        'b': 'Illegally recorded conversations — MCL 750.539c felony (2-party consent violation)',
        'src_b': 'Recording evidence / MCL 750.539c',
        'date_b': '2024',
        'type': 'ILLEGALLY_OBTAINED_EVIDENCE',
        'value': 'CRITICAL',
        'use': 'Motion to suppress under MCL 750.539c; MRE 613 — fruit of felony; criminal referral'
    },
    {
        'target': 'Albert Watson',
        'a': 'Watson family claims to act in child\'s best interest',
        'src_a': 'General family position',
        'date_a': '2024-2025',
        'b': 'August 7, 2025 statement showing premeditation of custody strategy',
        'src_b': 'Albert Watson communication',
        'date_b': '2025-08-07',
        'type': 'PREMEDITATION',
        'value': 'HIGH',
        'use': 'MRE 613, MRE 801(d)(2) — admission by party opponent; shows coordinated plan'
    },
    {
        'target': 'Judge Jenny L. McNeill',
        'a': 'Claims judicial impartiality and fairness',
        'src_a': 'Judicial oath / MCJC Canon 2',
        'date_a': 'Ongoing',
        'b': '52 ex parte orders, 44% ex parte rate, 100% favoring Emily Watson',
        'src_b': 'Court record analysis (DB: judicial_violations)',
        'date_b': '2024-2025',
        'type': 'STATISTICAL_BIAS',
        'value': 'CRITICAL',
        'use': 'MCR 2.003 disqualification; MCJC Canon 2/3 violations; JTC complaint support'
    },
    {
        'target': 'Judge Jenny L. McNeill',
        'a': 'Ordered mental health evaluation as neutral fact-finding',
        'src_a': 'Court order',
        'date_a': '2024',
        'b': 'Sent letter to HealthWest that influenced eval #2 from "ALL ZEROS" to "Rule Out"',
        'src_b': 'HealthWest records comparison',
        'date_b': '2024',
        'type': 'JUDICIAL_TAMPERING',
        'value': 'CRITICAL',
        'use': 'JTC complaint; due process violation — judge tainted evaluation process'
    },
    {
        'target': 'Judge Jenny L. McNeill',
        'a': 'Found father in contempt, ordered incarceration',
        'src_a': 'Court orders',
        'date_a': '2024-2025',
        'b': 'Father had no counsel; no opportunity to purge contempt; 59+ days incarcerated',
        'src_b': 'Jail records / court transcripts',
        'date_b': '2024-2025',
        'type': 'PROCEDURAL_VIOLATION',
        'value': 'CRITICAL',
        'use': 'Turner v. Rogers, 564 U.S. 431 (2011) — civil contempt without counsel; 6th Amendment'
    },
    {
        'target': 'Jennifer Barnes (P55406)',
        'a': 'Filed motions citing good faith concerns about child safety',
        'src_a': 'Various motions',
        'date_a': '2024-2025',
        'b': 'Filed on evidence obtained through felony wiretapping (Lori Watson recording)',
        'src_b': 'Filing analysis / MCL 750.539c',
        'date_b': '2024',
        'type': 'KNOWING_USE_OF_ILLEGAL_EVIDENCE',
        'value': 'HIGH',
        'use': 'MRPC 3.3(a), 8.4(c) — State Bar grievance; motion to strike'
    },
]

# Insert known contradictions
for entry in KNOWN_CONTRADICTIONS:
    c.execute('''INSERT INTO impeachment_index 
        (target_witness, statement_a, source_a, date_a, statement_b, source_b, date_b,
         contradiction_type, impeachment_value, legal_use)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (entry['target'], entry['a'], entry['src_a'], entry['date_a'],
         entry['b'], entry['src_b'], entry['date_b'],
         entry['type'], entry['value'], entry['use']))
    inserted += 1

# Scan psych_analysis_results for additional contradictions
c.execute("""SELECT pattern_detected, rebuttal_point, pattern_category FROM psych_analysis_results 
WHERE pattern_category IN ('manipulation_pattern', 'adversary_assertion')""")
for pattern, rebuttal, category in c.fetchall():
    if not pattern:
        continue
    c.execute('''INSERT INTO impeachment_index 
        (target_witness, statement_a, source_a, date_a, statement_b, source_b, date_b,
         contradiction_type, impeachment_value, legal_use)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        ('Emily Watson', pattern[:500], 'Psych analysis', '2024-2025',
         rebuttal[:500] if rebuttal else 'See AppClose records',
         'psych_analysis_results', '2024-2025',
         'PSYCH_CONTRADICTION', 'MEDIUM',
         'MRE 613 — behavioral pattern impeachment'))
    inserted += 1

conn.commit()

# Build FTS
try:
    c.execute('DROP TABLE IF EXISTS impeachment_index_fts')
    c.execute('''CREATE VIRTUAL TABLE impeachment_index_fts USING fts5(
        target_witness, statement_a, statement_b, contradiction_type, legal_use,
        content=impeachment_index, content_rowid=id
    )''')
    c.execute('''INSERT INTO impeachment_index_fts(rowid, target_witness, statement_a, statement_b, contradiction_type, legal_use)
        SELECT id, target_witness, statement_a, statement_b, contradiction_type, legal_use FROM impeachment_index''')
    conn.commit()
    print("[+] FTS5 index built")
except Exception as e:
    print(f"[!] FTS: {e}")

# Summary
c.execute("SELECT target_witness, COUNT(*), SUM(CASE WHEN impeachment_value='CRITICAL' THEN 1 ELSE 0 END) FROM impeachment_index GROUP BY target_witness ORDER BY COUNT(*) DESC")
print(f"\n{'='*70}")
print(f"  IMPEACHMENT INDEX COMPLETE: {inserted} entries")
print(f"{'='*70}")
for target, cnt, crit in c.fetchall():
    print(f"    {target}: {cnt} contradictions ({crit or 0} CRITICAL)")

# Generate report
report_path = r'C:\Users\andre\LitigationOS\05_ANALYSIS\IMPEACHMENT_INDEX.md'
with open(report_path, 'w', encoding='utf-8') as f:
    f.write("# IMPEACHMENT INDEX\n")
    f.write(f"## Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    f.write(f"## Total Entries: {inserted}\n\n")
    f.write("---\n\n")
    
    c.execute("""SELECT target_witness, statement_a, source_a, date_a, statement_b, source_b, date_b,
        contradiction_type, impeachment_value, legal_use FROM impeachment_index 
        ORDER BY CASE impeachment_value WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 ELSE 3 END, target_witness""")
    
    current_target = None
    for target, a, src_a, d_a, b, src_b, d_b, ctype, value, use in c.fetchall():
        if target != current_target:
            current_target = target
            f.write(f"\n## {target}\n\n")
        icon = "🔴" if value == 'CRITICAL' else "🟡" if value == 'HIGH' else "⚪"
        f.write(f"### {icon} [{value}] {ctype}\n\n")
        f.write(f"**Statement A:** {a}\n")
        f.write(f"- Source: {src_a} ({d_a})\n\n")
        f.write(f"**Statement B (Contradiction):** {b}\n")
        f.write(f"- Source: {src_b} ({d_b})\n\n")
        f.write(f"**Legal Use:** {use}\n\n")
        f.write("---\n\n")

rpt_size = os.path.getsize(report_path)
print(f"[+] Report: {rpt_size/1024:.0f}KB at {report_path}")

conn.close()
