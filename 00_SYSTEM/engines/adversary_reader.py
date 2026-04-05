#!/usr/bin/env python3
"""
ENGINE 3: ADVERSARY FILING DEEP READER
Scans all adversary-related files on disk, extracts text content,
identifies every factual assertion, and feeds into rebuttal_matrix.
"""
import sqlite3
import os
import re
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

db_path = str(Path(__file__).resolve().parents[2] / "litigation_context.db")
conn = sqlite3.connect(db_path)
conn.execute("PRAGMA busy_timeout = 60000")
conn.execute("PRAGMA journal_mode = WAL")
conn.execute("PRAGMA cache_size = -32000")
c = conn.cursor()

logger.info("=" * 70)
logger.info("  ADVERSARY FILING DEEP READER v1.0")
logger.info("=" * 70)

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
logger.info("\n[1] Scanning disk for adversary files...")
c.execute("""SELECT file_path, file_name, extension FROM disk_inventory_omega 
WHERE (file_name LIKE '%emily%' OR file_name LIKE '%watson%' OR file_name LIKE '%barnes%' 
   OR file_name LIKE '%mcneill%' OR file_name LIKE '%exparte%' OR file_name LIKE '%ex_parte%'
   OR file_name LIKE '%adversar%')
AND extension IN ('.txt', '.md', '.csv')
ORDER BY extension, file_name
LIMIT 5000""")
text_files = c.fetchall()
logger.info("    Found %d readable adversary text files", len(text_files))

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
logger.info("\n[2] Extracted %d assertions from %d files (%d failed)", inserted, files_read, files_failed)

# Also scan evidence_quotes for adversary content not yet in rebuttal_matrix
logger.info("\n[3] Scanning evidence_quotes for unprocessed adversary content...")
eq_start = inserted
c.execute("""SELECT eq.id, eq.quote_text, eq.speaker, eq.legal_significance FROM evidence_quotes eq
LEFT JOIN rebuttal_matrix rm ON eq.id = rm.source_id AND rm.source_type = 'evidence_quote'
WHERE (eq.speaker LIKE '%WATSON%' OR eq.speaker LIKE '%Emily%' OR eq.speaker LIKE '%McNeill%' OR eq.speaker LIKE '%Barnes%')
AND rm.source_id IS NULL
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
logger.info("    → %d additional assertions from evidence_quotes", inserted - eq_start)

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
    logger.info("[+] FTS5 index built")
except Exception as e:
    logger.error("[!] FTS error: %s", e)

# Summary
c.execute("SELECT assertion_type, COUNT(*), SUM(is_false) FROM adversary_assertions GROUP BY assertion_type ORDER BY COUNT(*) DESC")
logger.info("\n%s", "=" * 70)
logger.info("  ADVERSARY READER COMPLETE: %d assertions extracted", inserted)
logger.info("  Files read: %d | Failed: %d", files_read, files_failed)
logger.info("=" * 70)
for atype, cnt, false_cnt in c.fetchall():
    logger.info("    %s: %d (%d flagged false)", atype, cnt, false_cnt or 0)

conn.close()
