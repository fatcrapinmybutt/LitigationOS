#!/usr/bin/env python3
"""Phase 6: Deep DB Intelligence Update — OMEGA Pipeline"""
import sqlite3, os, re, json
from datetime import datetime

db_path = r'C:\Users\andre\LitigationOS\litigation_context.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

# ======================================================================
# PHASE 6A: Create psych_analysis_results table
# ======================================================================
c.execute('''CREATE TABLE IF NOT EXISTS psych_analysis_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT,
    sender TEXT,
    message_date TEXT,
    message_text TEXT,
    pattern_detected TEXT,
    pattern_category TEXT,
    severity TEXT,
    tort_mapping TEXT,
    filing_target TEXT,
    rebuttal_point TEXT,
    evidence_strength TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)''')

# ======================================================================
# PHASE 6B: Populate from appclose_messages with pattern detection
# ======================================================================
PATTERNS = {
    'STONEWALLING': r'(?i)(i\s+don.?t\s+know|no\s+comment|not\s+sure|can.?t\s+remember|i\s+guess)',
    'GASLIGHTING': r'(?i)(you\s+always|you\s+never|that.?s\s+not\s+what|i\s+didn.?t\s+say|you.?re\s+(imagining|making|exaggerating|overreacting))',
    'GATEKEEPING': r'(?i)(i.?ll\s+decide|my\s+decision|not\s+your\s+(call|decision|business)|i\s+don.?t\s+have\s+to|you\s+don.?t\s+get\s+to|that.?s\s+not\s+up\s+to)',
    'MINIMIZATION': r'(?i)(it.?s\s+not\s+a\s+big\s+deal|you.?re\s+overreact|not\s+that\s+serious|calm\s+down|relax|chill)',
    'DEFLECTION': r'(?i)(what\s+about\s+you|you.?re\s+the\s+one|look\s+at\s+yourself|you\s+did|that.?s\s+your)',
    'HOSTILE_WITHHOLDING': r'(?i)(no\s*\.?$|nope|can.?t|won.?t|not\s+going\s+to|not\s+happening|we.?ll\s+see)',
    'ALIENATION_TACTIC': r'(?i)(lincoln\s+(doesn.?t|won.?t)|he\s+(doesn.?t|won.?t)\s+(want|need)|not\s+good\s+for|upset\s+him|confuse\s+him)',
    'CONTROLLING': r'(?i)(i\s+need\s+you\s+to|you\s+need\s+to|you\s+should|don.?t\s+you\s+dare|i\s+expect)',
    'EVASION': r'(?i)(we.?ll\s+see|maybe|i.?ll\s+think|not\s+right\s+now|later|some\s+other\s+time)',
    'MEDICAL_GATEKEEPING': r'(?i)(doctor|appointment|sick|health|medication|allerg|pediatri|medical)',
}

TORT_MAP = {
    'STONEWALLING': 'Tortious Interference with Parental Rights',
    'GASLIGHTING': 'Intentional Infliction of Emotional Distress',
    'GATEKEEPING': 'Tortious Interference with Parental Rights; Custodial Interference',
    'MINIMIZATION': 'Intentional Infliction of Emotional Distress',
    'DEFLECTION': 'Fraud/Misrepresentation',
    'HOSTILE_WITHHOLDING': 'Custodial Interference; Contempt',
    'ALIENATION_TACTIC': 'Parental Alienation; Tortious Interference',
    'CONTROLLING': 'Coercive Control Pattern',
    'EVASION': 'Obstruction of Parenting Time',
    'MEDICAL_GATEKEEPING': 'Medical Neglect; Tortious Interference',
}

FILING_MAP = {
    'STONEWALLING': 'COA Brief; Civil Tort',
    'GASLIGHTING': 'USDC §1983; Civil Tort',
    'GATEKEEPING': 'COA Brief; 14th Circuit Motion',
    'MINIMIZATION': 'Civil Tort',
    'DEFLECTION': 'COA Brief',
    'HOSTILE_WITHHOLDING': 'COA Brief; 14th Circuit Contempt',
    'ALIENATION_TACTIC': 'COA Brief; Civil Tort; USDC §1983',
    'CONTROLLING': 'Civil Tort; USDC §1983',
    'EVASION': '14th Circuit Motion; COA Brief',
    'MEDICAL_GATEKEEPING': 'COA Brief; CPS Complaint; Civil Tort',
}

c.execute('SELECT COUNT(*) FROM psych_analysis_results')
existing = c.fetchone()[0]

if existing == 0:
    inserted = 0
    
    # Emily's messages
    c.execute("SELECT rowid, sender, message_date, message_text FROM appclose_messages WHERE sender LIKE '%Emily%' OR sender LIKE '%Tiffany%'")
    emily_msgs = c.fetchall()
    
    for rowid, sender, date, text in emily_msgs:
        if not text or len(text.strip()) < 3:
            continue
        for pattern_name, regex in PATTERNS.items():
            if re.search(regex, text):
                severity = 'HIGH' if pattern_name in ('GASLIGHTING', 'ALIENATION_TACTIC', 'MEDICAL_GATEKEEPING') else 'MEDIUM'
                c.execute('''INSERT INTO psych_analysis_results 
                    (message_id, sender, message_date, message_text, pattern_detected, pattern_category, 
                     severity, tort_mapping, filing_target, rebuttal_point, evidence_strength)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (str(rowid), sender, date, text[:500], pattern_name, 'MANIPULATION',
                     severity, TORT_MAP.get(pattern_name, ''), FILING_MAP.get(pattern_name, ''),
                     f'Pattern: {pattern_name} detected in message dated {date}',
                     'STRONG' if len(text) > 50 else 'MODERATE'))
                inserted += 1
    
    # Andrew's contrasting messages (cooperative pattern)
    c.execute("SELECT rowid, sender, message_date, message_text FROM appclose_messages WHERE sender LIKE '%Andrew%' OR sender LIKE '%Andre%'")
    andrew_msgs = c.fetchall()
    
    COOPERATIVE = r'(?i)(please|thank|hope|love|miss|concern|lincoln.?s|doctor|school|schedule|pick\s*up|drop\s*off|let\s+me\s+know|happy|excited)'
    for rowid, sender, date, text in andrew_msgs:
        if not text or len(text.strip()) < 3:
            continue
        if re.search(COOPERATIVE, text):
            c.execute('''INSERT INTO psych_analysis_results 
                (message_id, sender, message_date, message_text, pattern_detected, pattern_category, 
                 severity, tort_mapping, filing_target, rebuttal_point, evidence_strength)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (str(rowid), sender, date, text[:500], 'COOPERATIVE_PARENT', 'CONTRAST',
                 'LOW', '', 'COA Brief (Contrast Evidence)',
                 f'Cooperative parenting communication dated {date}',
                 'STRONG'))
            inserted += 1
    
    conn.commit()
    print(f'Inserted {inserted} psych analysis results')
else:
    print(f'Already populated: {existing} rows')

# ======================================================================
# PHASE 6C: Create omega_analysis_summary table
# ======================================================================
c.execute('''CREATE TABLE IF NOT EXISTS omega_analysis_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT UNIQUE,
    metric_value TEXT,
    category TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
)''')

# Gather metrics
metrics = {}
c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
metrics['total_tables'] = str(c.fetchone()[0])

c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall() if not r[0].startswith('sqlite_')]
total_rows = 0
for t in tables:
    try:
        c.execute(f'SELECT COUNT(*) FROM [{t}]')
        total_rows += c.fetchone()[0]
    except:
        pass
metrics['total_rows'] = str(total_rows)

c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name LIKE '%fts%'")
metrics['fts_indexes'] = str(c.fetchone()[0])

for table in ['appclose_messages', 'appclose_violations', 'psych_analysis_results', 
              'canonical_fact_index', 'judicial_violations', 'evidence_quotes',
              'timeline', 'filing_documents', 'authority_entries']:
    try:
        c.execute(f'SELECT COUNT(*) FROM [{table}]')
        metrics[f'rows_{table}'] = str(c.fetchone()[0])
    except:
        metrics[f'rows_{table}'] = '0'

for name, value in metrics.items():
    c.execute('INSERT OR REPLACE INTO omega_analysis_summary (metric_name, metric_value, category, updated_at) VALUES (?, ?, ?, ?)',
              (name, value, 'system', datetime.now().isoformat()))
conn.commit()

# ======================================================================
# PHASE 6D: Build FTS for psych_analysis_results
# ======================================================================
try:
    c.execute('DROP TABLE IF EXISTS psych_analysis_fts')
    c.execute('''CREATE VIRTUAL TABLE psych_analysis_fts USING fts5(
        sender, message_text, pattern_detected, tort_mapping, rebuttal_point,
        content=psych_analysis_results, content_rowid=id
    )''')
    c.execute('''INSERT INTO psych_analysis_fts(rowid, sender, message_text, pattern_detected, tort_mapping, rebuttal_point)
        SELECT id, sender, message_text, pattern_detected, tort_mapping, rebuttal_point FROM psych_analysis_results''')
    conn.commit()
    print('FTS5 index built for psych_analysis_results')
except Exception as e:
    print(f'FTS error: {e}')

# ======================================================================
# PHASE 6E: Catalog newly unpacked files into disk_inventory
# ======================================================================
c.execute('''CREATE TABLE IF NOT EXISTS disk_inventory_omega (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT,
    file_name TEXT,
    extension TEXT,
    size_bytes INTEGER,
    parent_dir TEXT,
    category TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)''')

c.execute('SELECT COUNT(*) FROM disk_inventory_omega')
if c.fetchone()[0] == 0:
    los = r'C:\Users\andre\LitigationOS'
    batch = []
    count = 0
    for root, dirs, files in os.walk(los):
        dirs[:] = [d for d in dirs if d not in {'node_modules', '.git', '__pycache__', '.agents', '.copilot'}]
        for f in files:
            fp = os.path.join(root, f)
            try:
                sz = os.path.getsize(fp)
            except:
                sz = 0
            ext = os.path.splitext(f)[1].lower()
            rel = os.path.relpath(root, los)
            cat = rel.split(os.sep)[0] if os.sep in rel else rel
            batch.append((fp, f, ext, sz, rel, cat))
            count += 1
            if len(batch) >= 5000:
                c.executemany('INSERT INTO disk_inventory_omega (file_path, file_name, extension, size_bytes, parent_dir, category) VALUES (?, ?, ?, ?, ?, ?)', batch)
                conn.commit()
                batch = []
    if batch:
        c.executemany('INSERT INTO disk_inventory_omega (file_path, file_name, extension, size_bytes, parent_dir, category) VALUES (?, ?, ?, ?, ?, ?)', batch)
        conn.commit()
    print(f'Cataloged {count} files into disk_inventory_omega')
else:
    c.execute('SELECT COUNT(*) FROM disk_inventory_omega')
    print(f'Already cataloged: {c.fetchone()[0]} files')

# Print summary
print(f'\n=== DB INTELLIGENCE UPDATE COMPLETE ===')
print(f'  Tables: {metrics["total_tables"]}')
print(f'  Total rows: {metrics["total_rows"]}')
print(f'  FTS indexes: {metrics["fts_indexes"]}')
print(f'  Psych results: {metrics["rows_psych_analysis_results"]}')
print(f'  AppClose messages: {metrics["rows_appclose_messages"]}')
print(f'  Judicial violations: {metrics["rows_judicial_violations"]}')
print(f'  Authority entries: {metrics["rows_authority_entries"]}')

conn.close()
