#!/usr/bin/env python3
"""
ENGINE 2: EVIDENCE EXHIBIT COMPILER
Generates numbered exhibit binders with cover sheets and master index.
"""
import sqlite3
import os
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
logger.info("  EVIDENCE EXHIBIT COMPILER v1.0")
logger.info("=" * 70)

# Create exhibit registry table
c.execute('''CREATE TABLE IF NOT EXISTS exhibit_registry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exhibit_number TEXT UNIQUE NOT NULL,
    exhibit_title TEXT NOT NULL,
    exhibit_type TEXT,
    description TEXT,
    source_table TEXT,
    source_query TEXT,
    file_path TEXT,
    page_count INTEGER DEFAULT 0,
    filing_target TEXT,
    bates_start TEXT,
    bates_end TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)''')

c.execute("SELECT COUNT(*) FROM exhibit_registry")
if c.fetchone()[0] > 0:
    c.execute("DELETE FROM exhibit_registry")
    conn.commit()

# Define exhibit structure based on DB intelligence
exhibits = [
    # Core Evidence
    ('A', 'AppClose Communication Record — Complete', 'COMMUNICATION',
     '650 co-parenting messages (May 2024–Aug 2025) demonstrating Father cooperative pattern and Mother gatekeeping pattern',
     'appclose_messages', 'COA Brief; Civil Tort; All Courts'),
    ('B', 'AppClose Psychological Analysis', 'ANALYSIS',
     '146KB line-by-line analysis of all messages with pattern detection, tort mapping, and rebuttal points',
     'psych_analysis_results', 'COA Brief; Civil Tort'),
    ('C', 'Drug Screen Results — NEGATIVE', 'MEDICAL',
     'Court-ordered drug screen returning completely negative results — destroys substance abuse narrative',
     'evidence_quotes', 'COA Brief; USDC §1983'),
    ('D', 'HealthWest Evaluation #1 — ALL ZEROS', 'MEDICAL',
     'First independent psychological evaluation with zero clinical findings',
     'evidence_quotes', 'COA Brief; USDC §1983'),
    ('E', 'HealthWest Evaluation #2 — "Rule Out" After Judge Letter', 'MEDICAL',
     'Second evaluation changed after judicial interference — comparison with Eval #1',
     'evidence_quotes', 'COA Brief; JTC; USDC §1983'),
    ('F', 'Judge McNeill Communication to HealthWest Evaluator', 'JUDICIAL',
     'Ex parte communication from judge to evaluator that preceded changed evaluation findings',
     'judicial_violations', 'JTC; COA Brief; USDC §1983'),
    ('G', 'Albert Watson Premeditation Statement', 'WITNESS',
     '"they want this documented so Emily can go tomorrow to get an Ex Parte order" — Aug 7, 2025',
     'evidence_quotes', 'COA Brief; Civil Tort; USDC §1983'),
    ('H', 'Lori Watson Illegal Recording — MCL 750.539c', 'EVIDENCE',
     'Recording made in violation of Michigan eavesdropping felony statute — basis for ex parte order',
     'evidence_quotes', 'COA Brief; Criminal Referral'),
    ('I', 'Police Investigation Reports (9) — Zero Findings', 'LAW_ENFORCEMENT',
     'Nine separate police investigations yielding zero violations, arrests, or charges',
     'evidence_quotes', 'COA Brief; USDC §1983; Civil Tort'),
    ('J', 'Ex Parte Order Statistical Analysis', 'STATISTICAL',
     '52 orders, 44% rate, 100% favoring Mother — statistical proof of bias',
     'judicial_violations', 'COA Brief; JTC; MSC Petition'),
    ('K', 'Incarceration Records — 59+ Days', 'RECORDS',
     'Jail records documenting 59+ cumulative days of incarceration',
     'timeline', 'USDC §1983; Civil Tort; COA Brief'),
    ('L', 'Employment Termination Records — 3 Job Losses', 'EMPLOYMENT',
     'Documentation of three employment terminations caused by incarceration and court disruption',
     'damages_itemization', 'Civil Tort; USDC §1983'),
    ('M', 'Housing Loss Documentation', 'HOUSING',
     'Records of two housing losses resulting from economic destabilization',
     'damages_itemization', 'Civil Tort; USDC §1983'),
    ('N', 'Damages Itemization Schedule', 'FINANCIAL',
     'Complete itemized damages calculation with evidence citations — $259,100–$516,450+',
     'damages_itemization', 'All Courts'),
    ('O', 'Constitutional Violation Map', 'LEGAL',
     '11 mapped constitutional violations with controlling caselaw and Michigan authority',
     'constitutional_violations', 'USDC §1983; COA Brief'),
    ('P', 'Judicial Canon Violation Matrix', 'JUDICIAL',
     f'1,127 documented MCJC canon violations by Judge McNeill',
     'judicial_violations', 'JTC; MSC Petition; COA Brief'),
    ('Q', 'Rebuttal Matrix — Adversary Assertions', 'LEGAL',
     '553 adversary assertions with mapped rebuttals, tort causes, and filing targets',
     'rebuttal_matrix', 'All Courts'),
    ('R', 'Master Prosecution Timeline', 'TIMELINE',
     '1,899 chronological events from all DB sources — complete case history',
     'prosecution_timeline', 'All Courts'),
    ('S', 'AppClose Violation Record — 44 Incidents', 'VIOLATION',
     'Documented custody/communication violations with dates, content, and legal basis',
     'appclose_violations', 'COA Brief; 14th Circuit'),
    ('T', 'Emily Watson Employment — Kent County Prosecutor', 'BACKGROUND',
     'Documentation of Mother 9-year employment at Kent County Prosecutor Office Family Court Division',
     'evidence_quotes', 'COA Brief; Civil Tort'),
    ('U', 'Parental Alienation Assessment', 'ANALYSIS',
     'Scored alienation analysis using accepted frameworks with evidence mapping',
     'psych_analysis_results', 'COA Brief; Civil Tort'),
]

# Insert exhibits
for ex_num, title, ex_type, desc, src, filing in exhibits:
    bates = f'PIGORS-{ord(ex_num)-64:04d}'
    c.execute('''INSERT INTO exhibit_registry 
        (exhibit_number, exhibit_title, exhibit_type, description, source_table, filing_target, bates_start)
        VALUES (?, ?, ?, ?, ?, ?, ?)''',
        (f'Exhibit {ex_num}', title, ex_type, desc, src, filing, bates))

conn.commit()
print(f"[+] Registered {len(exhibits)} exhibits")

# Generate Exhibit Index Document
exhibit_dir = r'C:\Users\andre\LitigationOS\04_COURT_FILINGS\EXHIBITS'
os.makedirs(exhibit_dir, exist_ok=True)

index_path = os.path.join(exhibit_dir, 'EXHIBIT_INDEX.md')
with open(index_path, 'w', encoding='utf-8') as f:
    f.write("# MASTER EXHIBIT INDEX\n")
    f.write("## Pigors v. Watson — Case 2024-001507-DC / COA 366810\n")
    f.write(f"## Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
    f.write(f"**Total Exhibits: {len(exhibits)}**\n\n")
    f.write("---\n\n")
    f.write("| Exhibit | Title | Type | Filing Target |\n")
    f.write("|---------|-------|------|---------------|\n")
    for ex_num, title, ex_type, desc, src, filing in exhibits:
        f.write(f"| **{ex_num}** | {title[:50]} | {ex_type} | {filing[:40]} |\n")
    f.write("\n---\n\n")
    
    for ex_num, title, ex_type, desc, src, filing in exhibits:
        f.write(f"## Exhibit {ex_num}: {title}\n\n")
        f.write(f"**Type:** {ex_type}\n\n")
        f.write(f"**Description:** {desc}\n\n")
        f.write(f"**Source:** `{src}` table in litigation_context.db\n\n")
        f.write(f"**Filing Target:** {filing}\n\n")
        f.write(f"**Bates Number:** PIGORS-{ord(ex_num)-64:04d}\n\n")
        f.write("---\n\n")

    # Generate individual cover sheets
    for ex_num, title, ex_type, desc, src, filing in exhibits:
        cover_path = os.path.join(exhibit_dir, f'EXHIBIT_{ex_num}_COVER.md')
        with open(cover_path, 'w', encoding='utf-8') as cf:
            cf.write(f"# EXHIBIT {ex_num}\n\n")
            cf.write("---\n\n")
            cf.write(f"## {title}\n\n")
            cf.write("---\n\n")
            cf.write("**IN THE MICHIGAN COURT OF APPEALS**\n\n")
            cf.write("Case No. 366810\n\n")
            cf.write("**ANDREW J. PIGORS**, Plaintiff-Appellant\n\n")
            cf.write("v.\n\n")
            cf.write("**TIFFANY EMILY WATSON**, Defendant-Appellee\n\n")
            cf.write("---\n\n")
            cf.write(f"**Type:** {ex_type}\n\n")
            cf.write(f"**Description:** {desc}\n\n")
            cf.write(f"**Bates:** PIGORS-{ord(ex_num)-64:04d}\n\n")

idx_size = os.path.getsize(index_path)
cover_count = len([f for f in os.listdir(exhibit_dir) if f.endswith('_COVER.md')])
print(f"[+] Generated {idx_size/1024:.0f}KB master index")
print(f"[+] Generated {cover_count} exhibit cover sheets")

# Build FTS
try:
    c.execute('DROP TABLE IF EXISTS exhibit_registry_fts')
    c.execute('''CREATE VIRTUAL TABLE exhibit_registry_fts USING fts5(
        exhibit_number, exhibit_title, description, filing_target,
        content=exhibit_registry, content_rowid=id
    )''')
    c.execute('''INSERT INTO exhibit_registry_fts(rowid, exhibit_number, exhibit_title, description, filing_target)
        SELECT id, exhibit_number, exhibit_title, description, filing_target FROM exhibit_registry''')
    conn.commit()
    print("[+] FTS5 index built")
except Exception as e:
    print(f"[!] FTS error: {e}")

print(f"\n{'='*70}")
print(f"  EXHIBIT COMPILER COMPLETE: {len(exhibits)} exhibits registered")
print(f"  Index: {exhibit_dir}\\EXHIBIT_INDEX.md")
print(f"  Covers: {cover_count} cover sheets generated")
print(f"{'='*70}")

conn.close()
