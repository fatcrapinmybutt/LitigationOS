#!/usr/bin/env python3
"""
ADVERSARY REBUTTAL MATRIX ENGINE
Scans all adversary content in DB, extracts every negative assertion/accusation,
maps to rebuttal evidence, tort causes, and filing targets.
"""
import sqlite3
import re
import json
from datetime import datetime

db_path = r'C:\Users\andre\LitigationOS\litigation_context.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

# ======================================================================
# CREATE REBUTTAL MATRIX TABLE
# ======================================================================
c.execute('''CREATE TABLE IF NOT EXISTS rebuttal_matrix (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT,
    source_id TEXT,
    adversary TEXT,
    assertion_text TEXT,
    assertion_category TEXT,
    assertion_severity TEXT,
    is_false_statement INTEGER DEFAULT 0,
    rebuttal_evidence TEXT,
    rebuttal_citation TEXT,
    tort_cause TEXT,
    filing_target TEXT,
    priority_score INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)''')

# ======================================================================
# SCAN 1: Evidence Quotes from Watson/Barnes/McNeill
# ======================================================================
c.execute("""SELECT id, quote_text, quote_type, speaker, legal_significance 
FROM evidence_quotes 
WHERE speaker LIKE '%WATSON%' OR speaker LIKE '%Emily%' OR speaker LIKE '%Barnes%' OR speaker LIKE '%McNeill%'""")
adversary_quotes = c.fetchall()
print(f'Scanning {len(adversary_quotes)} adversary evidence quotes...')

# Assertion categories
NEGATIVE_PATTERNS = {
    'FALSE_ACCUSATION': r'(?i)(alleged|accus|claim|assert|state|contend|danger|threat|abus|violen|harass|stalk|unstable|erratic|mental)',
    'CHARACTER_ATTACK': r'(?i)(unfit|incapab|irresponsib|neglect|reckless|disregard|fails?\s+to|refused?\s+to|unable)',
    'CUSTODY_CLAIM': r'(?i)(best\s+interest|sole\s+custody|full\s+custody|supervised|restrict|limit|deny|parenting\s+time|visitation)',
    'LEGAL_MANIPULATION': r'(?i)(contempt|violat|order|comply|failure|vexatious|frivolous|bad\s+faith|sanction)',
    'FINANCIAL_ATTACK': r'(?i)(support|payment|income|employ|abil.*pay|financial|arrear|wage)',
    'SUBSTANCE_CLAIM': r'(?i)(drug|alcohol|substance|test|screen|intoxicat|impair|under\s+the\s+influence)',
    'MENTAL_HEALTH': r'(?i)(mental|psych|evaluat|therap|counseli|diagnos|disorder|anxiety|depress|bipolar|narcissi)',
    'CHILD_WELFARE': r'(?i)(child|lincoln|son|minor|welfare|safety|risk|harm|protect)',
}

# Rebuttal evidence mapping
REBUTTAL_MAP = {
    'FALSE_ACCUSATION': 'NEGATIVE drug screen; 9 police investigations = 0 charges; HealthWest eval #1 ALL ZEROS',
    'CHARACTER_ATTACK': '526 cooperative AppClose messages; consistent parenting efforts documented; 9 investigations cleared',
    'CUSTODY_CLAIM': 'MCL 722.23 best interest factors; 332+ days separation; no evidence of harm; parental alienation documented',
    'LEGAL_MANIPULATION': 'Pro se litigant rights under MCR 2.002; access to justice; judicial misconduct documented (1,127 violations)',
    'FINANCIAL_ATTACK': 'IFP status; 3 job losses caused by incarceration; 59+ days jailed; $82,250+ documented damages',
    'SUBSTANCE_CLAIM': 'NEGATIVE drug screen results; no substance abuse history; false allegations pattern',
    'MENTAL_HEALTH': 'HealthWest eval #1 ALL ZEROS; eval #2 "Rule Out" only after judge biasing letter; no diagnosis',
    'CHILD_WELFARE': 'Lincoln thriving during all parenting time; no incidents; 9 police investigations = 0 concerns; AppClose messages show engaged father',
}

TORT_CAUSE_MAP = {
    'FALSE_ACCUSATION': 'Defamation; Malicious Prosecution; Abuse of Process',
    'CHARACTER_ATTACK': 'Defamation Per Se; IIED',
    'CUSTODY_CLAIM': 'Tortious Interference with Parental Rights; Due Process Violation (14th Amend)',
    'LEGAL_MANIPULATION': 'Abuse of Process; Malicious Prosecution',
    'FINANCIAL_ATTACK': 'Wrongful Imprisonment; Economic Interference',
    'SUBSTANCE_CLAIM': 'Defamation; False Light; IIED',
    'MENTAL_HEALTH': 'Defamation; False Light; Due Process Violation',
    'CHILD_WELFARE': 'Parental Alienation Tort; IIED; Custodial Interference',
}

FILING_TARGET_MAP = {
    'FALSE_ACCUSATION': 'COA Brief; USDC §1983; Civil Tort',
    'CHARACTER_ATTACK': 'COA Brief; Civil Tort; Bar Complaint',
    'CUSTODY_CLAIM': 'COA Brief; USDC §1983; 14th Circuit Motion',
    'LEGAL_MANIPULATION': 'COA Brief; JTC; Bar Complaint',
    'FINANCIAL_ATTACK': 'COA Brief; USDC §1983; Civil Tort',
    'SUBSTANCE_CLAIM': 'COA Brief; Civil Tort; USDC §1983',
    'MENTAL_HEALTH': 'COA Brief; Civil Tort; USDC §1983',
    'CHILD_WELFARE': 'COA Brief; CPS Counter-Complaint; Civil Tort',
}

inserted = 0
c.execute('SELECT COUNT(*) FROM rebuttal_matrix')
if c.fetchone()[0] == 0:
    # Process evidence quotes
    for qid, text, qtype, speaker, significance in adversary_quotes:
        if not text or len(text.strip()) < 10:
            continue
        for cat, pattern in NEGATIVE_PATTERNS.items():
            if re.search(pattern, text):
                priority = 90 if cat in ('FALSE_ACCUSATION', 'SUBSTANCE_CLAIM', 'MENTAL_HEALTH') else 70
                c.execute('''INSERT INTO rebuttal_matrix 
                    (source_type, source_id, adversary, assertion_text, assertion_category, 
                     assertion_severity, is_false_statement, rebuttal_evidence, rebuttal_citation,
                     tort_cause, filing_target, priority_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    ('evidence_quote', str(qid), speaker or 'UNKNOWN', text[:500], cat,
                     'HIGH' if priority >= 80 else 'MEDIUM', 1,
                     REBUTTAL_MAP.get(cat, ''), significance or '',
                     TORT_CAUSE_MAP.get(cat, ''), FILING_TARGET_MAP.get(cat, ''), priority))
                inserted += 1

    # Process judicial violations
    c.execute("""SELECT violation_id, judge_name, canon_number, canon_text, violation_description, severity
    FROM judicial_violations LIMIT 500""")
    jv_rows = c.fetchall()
    print(f'Processing {len(jv_rows)} judicial violations...')
    
    for vid, judge, canon, canon_text, desc, sev in jv_rows:
        if not desc:
            continue
        priority = 95 if sev in ('CRITICAL', 'HIGH') else 75
        c.execute('''INSERT INTO rebuttal_matrix 
            (source_type, source_id, adversary, assertion_text, assertion_category,
             assertion_severity, is_false_statement, rebuttal_evidence, rebuttal_citation,
             tort_cause, filing_target, priority_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            ('judicial_violation', str(vid), judge or 'Judge McNeill', desc[:500], 'JUDICIAL_MISCONDUCT',
             sev or 'HIGH', 0, f'Canon {canon}: {(canon_text or "")[:200]}',
             f'MCJC Canon {canon}; MCR 2.003',
             'Due Process Violation; Judicial Misconduct; §1983',
             'JTC Complaint; COA Brief; USDC §1983; MSC Petition', priority))
        inserted += 1

    # Process AppClose psych patterns (Emily's manipulation)
    c.execute("""SELECT id, message_text, pattern_detected, tort_mapping, filing_target, severity
    FROM psych_analysis_results WHERE pattern_category = 'MANIPULATION'""")
    psych_rows = c.fetchall()
    print(f'Processing {len(psych_rows)} psych manipulation patterns...')
    
    for pid, text, pattern, tort, target, sev in psych_rows:
        priority = 85 if sev == 'HIGH' else 65
        c.execute('''INSERT INTO rebuttal_matrix 
            (source_type, source_id, adversary, assertion_text, assertion_category,
             assertion_severity, is_false_statement, rebuttal_evidence, rebuttal_citation,
             tort_cause, filing_target, priority_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            ('psych_analysis', str(pid), 'Emily Watson', text[:500], f'MANIPULATION_{pattern}',
             sev, 0, '526 cooperative Andrew messages contrast; pattern analysis shows systematic behavior',
             'AppClose message record; APPCLOSE_PSYCHOLOGICAL_ANALYSIS.md',
             tort or '', target or '', priority))
        inserted += 1

    conn.commit()
    print(f'\nInserted {inserted} rebuttal matrix entries')
else:
    c.execute('SELECT COUNT(*) FROM rebuttal_matrix')
    print(f'Already populated: {c.fetchone()[0]} entries')

# ======================================================================
# BUILD FTS FOR REBUTTAL MATRIX
# ======================================================================
try:
    c.execute('DROP TABLE IF EXISTS rebuttal_matrix_fts')
    c.execute('''CREATE VIRTUAL TABLE rebuttal_matrix_fts USING fts5(
        adversary, assertion_text, assertion_category, rebuttal_evidence, tort_cause, filing_target,
        content=rebuttal_matrix, content_rowid=id
    )''')
    c.execute('''INSERT INTO rebuttal_matrix_fts(rowid, adversary, assertion_text, assertion_category, rebuttal_evidence, tort_cause, filing_target)
        SELECT id, adversary, assertion_text, assertion_category, rebuttal_evidence, tort_cause, filing_target FROM rebuttal_matrix''')
    conn.commit()
    print('FTS5 index built for rebuttal_matrix')
except Exception as e:
    print(f'FTS error: {e}')

# ======================================================================
# GENERATE SUMMARY REPORT
# ======================================================================
c.execute("""SELECT assertion_category, COUNT(*), 
    SUM(CASE WHEN assertion_severity = 'HIGH' THEN 1 ELSE 0 END),
    SUM(CASE WHEN assertion_severity = 'CRITICAL' THEN 1 ELSE 0 END)
FROM rebuttal_matrix GROUP BY assertion_category ORDER BY COUNT(*) DESC""")

print('\n=== REBUTTAL MATRIX SUMMARY ===')
total = 0
for cat, cnt, high, critical in c.fetchall():
    total += cnt
    print(f'  {cat}: {cnt} entries ({high or 0} HIGH, {critical or 0} CRITICAL)')
print(f'  TOTAL: {total} rebuttal entries')

# Filing target distribution
c.execute("""SELECT filing_target, COUNT(*) FROM rebuttal_matrix 
WHERE filing_target != '' GROUP BY filing_target ORDER BY COUNT(*) DESC LIMIT 10""")
print('\n=== TOP FILING TARGETS ===')
for target, cnt in c.fetchall():
    print(f'  {cnt} entries → {target[:80]}')

# Top priority items
c.execute("""SELECT assertion_text, adversary, assertion_category, priority_score, tort_cause
FROM rebuttal_matrix WHERE priority_score >= 90 ORDER BY priority_score DESC LIMIT 10""")
print('\n=== TOP 10 HIGHEST PRIORITY REBUTTALS ===')
for text, adv, cat, pri, tort in c.fetchall():
    print(f'  [P{pri}] {adv}: {text[:80]}...')
    print(f'         Tort: {tort[:60]}')

conn.close()
print('\n✅ Rebuttal Matrix Engine complete.')
