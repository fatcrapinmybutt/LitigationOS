#!/usr/bin/env python3
"""
ENGINE 3: ADVERSARY FILING DEEP READER
Scans all adversary-related files on disk, extracts text content,
identifies every factual assertion, and feeds into rebuttal_matrix.
"""
import sqlite3
import os
import re
from datetime import datetime

db_path = r'C:\Users\andre\LitigationOS\litigation_context.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("=" * 70)
print("  ADVERSARY FILING DEEP READER v1.0")
print("=" * 70)

# Create adversary assertions table
c.execute('''CREATE TABLE IF NOT EXISTS adversary_assertions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT,
    file_name TEXT,
    assertion_text TEXT,
    assertion_type TEXT,
    speaker TEXT,
    page_ref TEXT,
    is_false INTEGER DEFAULT 0,
    rebuttal_evidence TEXT,
    severity TEXT DEFAULT 'MEDIUM',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)''')

c.execute("SELECT COUNT(*) FROM adversary_assertions")
if c.fetchone()[0] > 0:
    c.execute("DELETE FROM adversary_assertions")
    conn.commit()

# Find adversary files on disk
print("\n[1] Scanning disk for adversary files...")
c.execute("""SELECT file_path, file_name, extension FROM disk_inventory_omega 
WHERE (file_name LIKE '%emily%' OR file_name LIKE '%watson%' OR file_name LIKE '%barnes%' 
   OR file_name LIKE '%mcneill%' OR file_name LIKE '%exparte%' OR file_name LIKE '%ex_parte%'
   OR file_name LIKE '%adversar%')
AND extension IN ('.txt', '.md', '.csv')
ORDER BY extension, file_name""")
text_files = c.fetchall()
print(f"    Found {len(text_files)} readable adversary text files")

# Assertion detection patterns
ASSERTION_PATTERNS = {
    'ACCUSATION': r'(?i)(alleged|accus|claim|assert|danger|threat|abus|violen|harass|stalk|unstable|erratic|mental\s+health|substance|drug|alcohol)',
    'FALSE_STATEMENT': r'(?i)(father\s+(is|was|has|did|does|refused|failed|neglect)|respondent\s+(is|was|has)|plaintiff\s+(is|was|has)|mr\.?\s+pigors\s+(is|was|has|did))',
    'CHARACTER_ATTACK': r'(?i)(unfit|incapab|irresponsib|neglect|reckless|disregard|volatile|unpredictab|intimidat)',
    'CUSTODY_DEMAND': r'(?i)(sole\s+custody|full\s+custody|supervised|restrict|suspend|terminat|deny|no\s+contact|no\s+parenting)',
    'FINANCIAL_CLAIM': r'(?i)(support|payment|income|employ|abil.*pay|financial|arrear|contempt)',
    'JUDICIAL_ORDER': r'(?i)(order|hereby|court\s+finds|it\s+is\s+ordered|shall|must\s+not|prohibited|restrained)',
    'NEGATIVE_CONNOTATION': r'(?i)(concern|worry|fear|afraid|unsafe|risk|harm|protect|best\s+interest|welfare)',
}

REBUTTAL_MAP = {
    'ACCUSATION': 'NEGATIVE drug screen; ALL ZEROS eval; 9 investigations = 0 findings',
    'FALSE_STATEMENT': 'Contradicted by documentary evidence in LitigationOS DB',
    'CHARACTER_ATTACK': '526 cooperative AppClose messages; consistent parenting record',
    'CUSTODY_DEMAND': 'No best interest analysis performed; MCL 722.23 factors favor Father',
    'FINANCIAL_CLAIM': 'IFP status; 3 job losses caused BY litigation abuse, not negligence',
    'JUDICIAL_ORDER': 'Based on illegally obtained evidence (MCL 750.539c); due process violation',
    'NEGATIVE_CONNOTATION': 'No evidence supports concerns; 9 police investigations cleared Father',
}

inserted = 0
files_read = 0
files_failed = 0

for fpath, fname, ext in text_files:
    if not os.path.exists(fpath):
        continue
    try:
        with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        if len(content) < 50:
            continue
        files_read += 1
        
        # Split into sentences/lines for assertion extraction
        lines = re.split(r'[.\n]+', content)
        for line in lines:
            line = line.strip()
            if len(line) < 20:
                continue
            for atype, pattern in ASSERTION_PATTERNS.items():
                if re.search(pattern, line):
                    # Determine if likely false based on known rebuttals
                    is_false = 1 if atype in ('ACCUSATION', 'FALSE_STATEMENT', 'CHARACTER_ATTACK') else 0
                    c.execute('''INSERT INTO adversary_assertions 
                        (file_path, file_name, assertion_text, assertion_type, speaker,
                         is_false, rebuttal_evidence, severity)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                        (fpath, fname, line[:500], atype, 
                         'Emily Watson/Barnes' if 'emily' in fname.lower() or 'watson' in fname.lower() or 'barnes' in fname.lower() else 'Judge McNeill',
                         is_false, REBUTTAL_MAP.get(atype, ''),
                         'HIGH' if atype in ('ACCUSATION', 'FALSE_STATEMENT', 'JUDICIAL_ORDER') else 'MEDIUM'))
                    inserted += 1
                    break  # One assertion type per line
    except Exception as e:
        files_failed += 1

conn.commit()
print(f"\n[2] Extracted {inserted} assertions from {files_read} files ({files_failed} failed)")

# Also scan evidence_quotes for adversary content not yet in rebuttal_matrix
print("\n[3] Scanning evidence_quotes for unprocessed adversary content...")
eq_start = inserted
c.execute("""SELECT id, quote_text, speaker, legal_significance FROM evidence_quotes
WHERE (speaker LIKE '%WATSON%' OR speaker LIKE '%Emily%' OR speaker LIKE '%McNeill%' OR speaker LIKE '%Barnes%')
AND id NOT IN (SELECT source_id FROM rebuttal_matrix WHERE source_type = 'evidence_quote')
LIMIT 1000""")
for eid, text, speaker, sig in c.fetchall():
    if not text or len(text.strip()) < 20:
        continue
    for atype, pattern in ASSERTION_PATTERNS.items():
        if re.search(pattern, text):
            c.execute('''INSERT INTO adversary_assertions 
                (file_path, file_name, assertion_text, assertion_type, speaker,
                 is_false, rebuttal_evidence, severity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                ('DB:evidence_quotes', f'eq_{eid}', text[:500], atype, speaker or 'Unknown',
                 1 if atype in ('ACCUSATION', 'FALSE_STATEMENT') else 0,
                 REBUTTAL_MAP.get(atype, ''),
                 'HIGH' if atype in ('ACCUSATION', 'FALSE_STATEMENT') else 'MEDIUM'))
            inserted += 1
            break
conn.commit()
print(f"    → {inserted - eq_start} additional assertions from evidence_quotes")

# Build FTS
try:
    c.execute('DROP TABLE IF EXISTS adversary_assertions_fts')
    c.execute('''CREATE VIRTUAL TABLE adversary_assertions_fts USING fts5(
        assertion_text, assertion_type, speaker, rebuttal_evidence,
        content=adversary_assertions, content_rowid=id
    )''')
    c.execute('''INSERT INTO adversary_assertions_fts(rowid, assertion_text, assertion_type, speaker, rebuttal_evidence)
        SELECT id, assertion_text, assertion_type, speaker, rebuttal_evidence FROM adversary_assertions''')
    conn.commit()
    print("[+] FTS5 index built")
except Exception as e:
    print(f"[!] FTS error: {e}")

# Summary
c.execute("SELECT assertion_type, COUNT(*), SUM(is_false) FROM adversary_assertions GROUP BY assertion_type ORDER BY COUNT(*) DESC")
print(f"\n{'='*70}")
print(f"  ADVERSARY READER COMPLETE: {inserted} assertions extracted")
print(f"  Files read: {files_read} | Failed: {files_failed}")
print(f"{'='*70}")
for atype, cnt, false_cnt in c.fetchall():
    print(f"    {atype}: {cnt} ({false_cnt or 0} flagged false)")

conn.close()
