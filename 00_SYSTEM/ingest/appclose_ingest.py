#!/usr/bin/env python3
"""
AppClose Ingestion Engine — LitigationOS
Parses AppClose conversation exports, CSVs, and analysis files.
Creates and populates: appclose_messages, appclose_violations, appclose_file_catalog, appclose_messages_fts
Also ingests master affidavits and canonical facts into DB.
"""

import sqlite3
import os
import re
import csv
import hashlib
import json
from datetime import datetime, date
from pathlib import Path

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
LOS_ROOT = r"C:\Users\andre\LitigationOS"

# ═══════════════════════════════════════════════════════════════
# PHASE 1: CREATE TABLES
# ═══════════════════════════════════════════════════════════════

def create_tables(conn):
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS appclose_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT NOT NULL,
        recipient TEXT,
        message_date TEXT,
        message_time TEXT,
        viewed_by TEXT,
        viewed_date TEXT,
        viewed_time TEXT,
        message_type TEXT DEFAULT 'text',
        message_text TEXT,
        page_ref INTEGER,
        report_period TEXT,
        source_file TEXT,
        text_hash TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS appclose_violations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        incident_id TEXT,
        violation_date TEXT,
        violation_time TEXT,
        page_ref INTEGER,
        violation_type TEXT,
        content TEXT,
        relevance TEXT,
        legal_basis TEXT,
        remedy_pathway TEXT,
        probative_score REAL,
        severity TEXT,
        source_file TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS appclose_file_catalog (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT UNIQUE,
        file_name TEXT,
        file_type TEXT,
        file_size INTEGER,
        category TEXT,
        content_type TEXT,
        messages_extracted INTEGER DEFAULT 0,
        violations_extracted INTEGER DEFAULT 0,
        source_drive TEXT,
        ingested INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS master_affidavit_registry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        court TEXT NOT NULL,
        title TEXT,
        file_path TEXT,
        file_size INTEGER,
        word_count INTEGER,
        paragraph_count INTEGER,
        key_claims TEXT,
        day_count_separation INTEGER,
        generated_date TEXT,
        version TEXT DEFAULT 'v1',
        content_hash TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS canonical_fact_index (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fact_text TEXT,
        fact_category TEXT,
        source_conversation TEXT,
        source_date TEXT,
        confidence TEXT DEFAULT 'HIGH',
        text_hash TEXT UNIQUE,
        linked_timeline_id INTEGER,
        linked_violation_id INTEGER,
        created_at TEXT DEFAULT (datetime('now'))
    )
    """)

    conn.commit()
    print("[+] All tables created")


# ═══════════════════════════════════════════════════════════════
# PHASE 2: PARSE APPCLOSE MESSAGES FROM TEXT FILES
# ═══════════════════════════════════════════════════════════════

MSG_PATTERN = re.compile(
    r'(?P<sender>[\w\s]+?)\s+on\s+(?P<date>\d{1,2}/\d{1,2}/\d{4})\s+(?P<time>\d{1,2}:\d{2}(?:AM|PM))\s+'
    r'(?:texted|sent attachment)\s*'
    r'\(viewed by\s+(?P<viewer>[\w\s]+?)\s+on\s+(?P<vdate>\d{1,2}/\d{1,2}/\d{4})\s+(?P<vtime>\d{1,2}:\d{2}(?:AM|PM))\)',
    re.IGNORECASE
)

ATTACHMENT_PATTERN = re.compile(r'sent attachment', re.IGNORECASE)

def parse_appclose_text(filepath):
    messages = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception as e:
        print(f"  [!] Error reading {filepath}: {e}")
        return messages

    period_match = re.search(r'Period:\s*(.+?)$', content, re.MULTILINE)
    report_period = period_match.group(1).strip() if period_match else None

    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        match = MSG_PATTERN.search(line)
        if match:
            sender = match.group('sender').strip()
            msg_date = match.group('date')
            msg_time = match.group('time')
            viewer = match.group('viewer').strip()
            view_date = match.group('vdate')
            view_time = match.group('vtime')
            is_attachment = bool(ATTACHMENT_PATTERN.search(line))

            msg_lines = []
            colon_pos = line.rfind(':')
            if colon_pos > -1 and colon_pos < len(line) - 1:
                after_colon = line[colon_pos+1:].strip()
                if after_colon and not after_colon.startswith('('):
                    msg_lines.append(after_colon)

            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                if not next_line:
                    j += 1
                    continue
                if MSG_PATTERN.search(next_line):
                    break
                if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', next_line):
                    break
                if 'Generated through AppClose' in next_line:
                    break
                if next_line.startswith('Page ') and 'of' in next_line:
                    break
                if next_line.startswith('AppClose Complete Record'):
                    break
                msg_lines.append(next_line)
                j += 1

            msg_text = ' '.join(msg_lines).strip()
            if is_attachment and not msg_text:
                msg_text = "[ATTACHMENT]"

            text_hash = hashlib.md5(f"{sender}{msg_date}{msg_time}{msg_text[:100]}".encode()).hexdigest()

            messages.append({
                'sender': sender,
                'recipient': viewer,
                'message_date': msg_date,
                'message_time': msg_time,
                'viewed_by': viewer,
                'viewed_date': view_date,
                'viewed_time': view_time,
                'message_type': 'attachment' if is_attachment else 'text',
                'message_text': msg_text,
                'report_period': report_period,
                'source_file': filepath,
                'text_hash': text_hash
            })
            i = j
        else:
            i += 1

    return messages


# ═══════════════════════════════════════════════════════════════
# PHASE 3: PARSE APPCLOSE CITATIONS CSV
# ═══════════════════════════════════════════════════════════════

def parse_citations_csv(filepath):
    violations = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                date_val = row.get('Date', '').strip()
                time_val = row.get('Time', '').strip()
                page_val = row.get('Page', '').strip()
                content = row.get('Content', '').strip()
                relevance = row.get('Relevance', '').strip()

                if not content:
                    continue

                vtype = classify_violation(content, relevance)
                severity = classify_severity(relevance)
                legal_basis = extract_legal_basis(relevance)

                violations.append({
                    'incident_id': f'AC-CSV-{i+1:04d}',
                    'violation_date': date_val,
                    'violation_time': time_val,
                    'page_ref': int(page_val) if page_val.isdigit() else None,
                    'violation_type': vtype,
                    'content': content,
                    'relevance': relevance,
                    'legal_basis': legal_basis,
                    'severity': severity,
                    'source_file': filepath
                })
    except Exception as e:
        print(f"  [!] Error parsing CSV {filepath}: {e}")
    return violations


def classify_violation(content, relevance):
    text = (content + ' ' + relevance).lower()
    if any(w in text for w in ['denied', 'refused', 'not allowing', "won't be giving"]):
        return 'PARENTING_TIME_DENIAL'
    if any(w in text for w in ['alienat', "doesn't want to see", 'bad parent', 'calling another man']):
        return 'PARENTAL_ALIENATION'
    if any(w in text for w in ['medical', 'doctor', 'hospital', 'health', 'illness', 'disease']):
        return 'MEDICAL_NEGLECT'
    if any(w in text for w in ['ignored', 'failed to respond', 'no response', 'refused to share']):
        return 'COMMUNICATION_FAILURE'
    if any(w in text for w in ['harass', 'threaten', 'ppo', 'intimidat']):
        return 'HARASSMENT'
    if any(w in text for w in ['insurance', 'financial', 'child support', 'payment']):
        return 'FINANCIAL_ISSUE'
    if any(w in text for w in ['diet', 'food', 'feeding', 'nutrition']):
        return 'WELFARE_CONCERN'
    return 'COMMUNICATION_VIOLATION'


def classify_severity(relevance):
    text = relevance.lower()
    if any(w in text for w in ['denial', 'refused', 'alienat', 'neglect', 'dismiss']):
        return 'HIGH'
    if any(w in text for w in ['failure', 'lack', 'poor']):
        return 'MEDIUM'
    return 'LOW'


def extract_legal_basis(text):
    bases = []
    if 'MCL' in text:
        for m in re.finditer(r'MCL\s+[\d.]+', text):
            bases.append(m.group())
    if 'MCR' in text:
        for m in re.finditer(r'MCR\s+[\d.]+', text):
            bases.append(m.group())
    if 'SCAO' in text:
        bases.append('SCAO Custody Benchbook')
    return '; '.join(bases) if bases else None


# ═══════════════════════════════════════════════════════════════
# PHASE 4: CATALOG ALL APPCLOSE FILES
# ═══════════════════════════════════════════════════════════════

def catalog_appclose_files(conn):
    cur = conn.cursor()
    appclose_files = []

    search_roots = [
        (r'C:\Users\andre\LitigationOS', 'C'),
        (r'D:\\', 'D'),
        (r'F:\\', 'F'),
        (r'G:\\', 'G'),
    ]

    for root_path, drive in search_roots:
        if not os.path.exists(root_path):
            continue
        for dirpath, _, filenames in os.walk(root_path):
            for fname in filenames:
                if re.search(r'appclose|app.?close', fname, re.IGNORECASE):
                    full_path = os.path.join(dirpath, fname)
                    try:
                        size = os.path.getsize(full_path)
                    except:
                        size = 0
                    ext = os.path.splitext(fname)[1].lower()

                    if ext in ('.txt',):
                        content_type = 'text_conversation'
                    elif ext in ('.csv',):
                        content_type = 'structured_data'
                    elif ext in ('.pdf',):
                        content_type = 'pdf_report'
                    elif ext in ('.docx', '.doc'):
                        content_type = 'word_document'
                    elif ext in ('.odt',):
                        content_type = 'odt_document'
                    elif ext in ('.xlsx', '.xls'):
                        content_type = 'spreadsheet'
                    else:
                        content_type = 'other'

                    path_lower = full_path.lower()
                    if 'evidence' in path_lower or 'exhibit' in path_lower:
                        category = 'evidence'
                    elif 'court_filings' in path_lower or 'filing' in path_lower:
                        category = 'court_filing'
                    elif 'analysis' in path_lower or 'graph' in path_lower:
                        category = 'analysis'
                    elif 'archive' in path_lower:
                        category = 'archive'
                    elif 'database' in path_lower or 'csv' in path_lower:
                        category = 'database'
                    else:
                        category = 'general'

                    appclose_files.append({
                        'file_path': full_path,
                        'file_name': fname,
                        'file_type': ext,
                        'file_size': size,
                        'category': category,
                        'content_type': content_type,
                        'source_drive': drive
                    })

    inserted = 0
    for f in appclose_files:
        try:
            cur.execute("""
                INSERT OR IGNORE INTO appclose_file_catalog
                (file_path, file_name, file_type, file_size, category, content_type, source_drive)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (f['file_path'], f['file_name'], f['file_type'], f['file_size'],
                  f['category'], f['content_type'], f['source_drive']))
            if cur.rowcount > 0:
                inserted += 1
        except:
            pass

    conn.commit()
    print(f"[+] Cataloged {inserted} AppClose files ({len(appclose_files)} total found)")
    return appclose_files


# ═══════════════════════════════════════════════════════════════
# PHASE 5: EXTRACT PDF TEXT (PyMuPDF)
# ═══════════════════════════════════════════════════════════════

def extract_pdf_messages(filepath):
    messages = []
    try:
        import fitz
        doc = fitz.open(filepath)
        full_text = ""
        for page in doc:
            full_text += page.get_text() + "\n"
        doc.close()

        if full_text.strip():
            temp_path = filepath + ".tmp_extract.txt"
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(full_text)
            messages = parse_appclose_text(temp_path)
            for m in messages:
                m['source_file'] = filepath
            try:
                os.remove(temp_path)
            except:
                pass
    except ImportError:
        print("  [!] PyMuPDF not available, skipping PDF extraction")
    except Exception as e:
        print(f"  [!] Error extracting PDF {filepath}: {e}")
    return messages


# ═══════════════════════════════════════════════════════════════
# PHASE 6: INGEST MASTER AFFIDAVITS
# ═══════════════════════════════════════════════════════════════

def ingest_master_affidavits(conn):
    cur = conn.cursor()
    aff_dir = os.path.join(LOS_ROOT, "04_COURT_FILINGS", "MASTER_AFFIDAVITS")

    affidavits = {
        'MASTER_AFFIDAVIT_14TH_CIRCUIT.md': {
            'court': '14TH_CIRCUIT',
            'title': 'Master Affidavit - 14th Circuit Court (2024-001507-DC)',
            'key_claims': 'Ex parte violations; parenting time denial; due process; FOC misconduct; judicial bias'
        },
        'MASTER_AFFIDAVIT_COA.md': {
            'court': 'COA',
            'title': 'Master Affidavit - Court of Appeals (366810)',
            'key_claims': '6 Questions Presented; abuse of discretion; MCR 2.003 disqualification; MCR 3.210 violations'
        },
        'MASTER_AFFIDAVIT_JTC.md': {
            'court': 'JTC',
            'title': 'Master Affidavit - Judicial Tenure Commission',
            'key_claims': 'Canon 1-5 violations; ex parte pattern; bias indicators; procedural irregularities'
        },
        'MASTER_AFFIDAVIT_MSC.md': {
            'court': 'MSC',
            'title': 'Master Affidavit - Michigan Supreme Court',
            'key_claims': 'Superintending control; systemic judicial failure; constitutional violations; urgency'
        },
        'MASTER_AFFIDAVIT_USDC.md': {
            'court': 'USDC',
            'title': 'Master Affidavit - U.S. District Court (42 USC 1983)',
            'key_claims': 'Federal civil rights; 14th Amendment due process; color of law; 1983 damages'
        },
        'MASTER_IFP_AFFIDAVIT.md': {
            'court': 'ALL',
            'title': 'In Forma Pauperis Affidavit - Multi-Venue',
            'key_claims': 'Indigency; 3 job losses; 59+ days jailed; 82K+ damages; 332+ days separation'
        }
    }

    inserted = 0
    for fname, meta in affidavits.items():
        fpath = os.path.join(aff_dir, fname)
        if not os.path.exists(fpath):
            continue

        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()

        fsize = os.path.getsize(fpath)
        words = len(content.split())
        paragraphs = len([p for p in content.split('\n\n') if p.strip()])
        content_hash = hashlib.md5(content.encode()).hexdigest()

        today = date.today()
        suspension_date = date(2025, 8, 8)
        days_since = (today - suspension_date).days

        cur.execute("""
            INSERT OR REPLACE INTO master_affidavit_registry
            (court, title, file_path, file_size, word_count, paragraph_count,
             key_claims, day_count_separation, generated_date, content_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (meta['court'], meta['title'], fpath, fsize, words, paragraphs,
              meta['key_claims'], days_since, today.isoformat(), content_hash))
        inserted += 1

    conn.commit()
    print(f"[+] Registered {inserted} master affidavits")
    return inserted


# ═══════════════════════════════════════════════════════════════
# PHASE 7: INDEX CANONICAL FACTS
# ═══════════════════════════════════════════════════════════════

def ingest_canonical_facts(conn):
    cur = conn.cursor()
    facts_file = os.path.join(LOS_ROOT, "04_COURT_FILINGS", "MASTER_AFFIDAVITS", "CANONICAL_FACTS_FROM_CHATS.md")

    if not os.path.exists(facts_file):
        print("[!] CANONICAL_FACTS_FROM_CHATS.md not found")
        return 0

    with open(facts_file, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    facts = []
    current_conv = None
    seen_hashes = set()

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('## ') or line.startswith('### '):
            current_conv = line.lstrip('#').strip()
            continue
        if line.startswith('---') or line.startswith('# '):
            continue

        if len(line) > 30 and not line.startswith('[') and not line.startswith('*'):
            cat = categorize_fact(line)
            text_hash = hashlib.md5(line[:200].encode()).hexdigest()
            if text_hash not in seen_hashes:
                seen_hashes.add(text_hash)
                facts.append({
                    'fact_text': line[:2000],
                    'fact_category': cat,
                    'source_conversation': current_conv,
                    'text_hash': text_hash
                })

    inserted = 0
    for fact in facts:
        try:
            cur.execute("""
                INSERT OR IGNORE INTO canonical_fact_index
                (fact_text, fact_category, source_conversation, text_hash)
                VALUES (?, ?, ?, ?)
            """, (fact['fact_text'], fact['fact_category'],
                  fact['source_conversation'], fact['text_hash']))
            if cur.rowcount > 0:
                inserted += 1
        except:
            pass

    conn.commit()
    print(f"[+] Indexed {inserted} canonical facts (from {len(facts)} parsed)")
    return inserted


def categorize_fact(text):
    t = text.lower()
    if any(w in t for w in ['custody', 'parenting time', 'visitation', 'lincoln']):
        return 'CUSTODY'
    if any(w in t for w in ['judge', 'court', 'mcneill', 'hearing', 'order']):
        return 'JUDICIAL'
    if any(w in t for w in ['emily', 'watson', 'tiffany', 'mother']):
        return 'OPPOSING_PARTY'
    if any(w in t for w in ['ppo', 'protection', 'restraining']):
        return 'PPO'
    if any(w in t for w in ['jail', 'incarcerat', 'arrest', 'contempt']):
        return 'INCARCERATION'
    if any(w in t for w in ['money', 'income', 'job', 'employ', 'financial', 'support']):
        return 'FINANCIAL'
    if any(w in t for w in ['evidence', 'exhibit', 'document', 'record']):
        return 'EVIDENCE'
    if any(w in t for w in ['police', 'investigation', 'report', 'officer']):
        return 'LAW_ENFORCEMENT'
    if any(w in t for w in ['alienat', 'withhold', 'denied', 'separation']):
        return 'ALIENATION'
    if any(w in t for w in ['lori', 'albert', 'watson family']):
        return 'THIRD_PARTY'
    if any(w in t for w in ['drug', 'screen', 'test', 'eval', 'healthwest']):
        return 'EVALUATION'
    if any(w in t for w in ['foc', 'friend of court', 'referee']):
        return 'FOC'
    return 'GENERAL'


# ═══════════════════════════════════════════════════════════════
# PHASE 8: BUILD FTS INDEXES
# ═══════════════════════════════════════════════════════════════

def build_fts_indexes(conn):
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS appclose_messages_fts")
    cur.execute("""
        CREATE VIRTUAL TABLE appclose_messages_fts USING fts5(
            sender, message_text, message_date, source_file,
            content=appclose_messages,
            content_rowid=id
        )
    """)
    cur.execute("""
        INSERT INTO appclose_messages_fts(rowid, sender, message_text, message_date, source_file)
        SELECT id, sender, message_text, message_date, source_file FROM appclose_messages
    """)

    cur.execute("DROP TABLE IF EXISTS appclose_violations_fts")
    cur.execute("""
        CREATE VIRTUAL TABLE appclose_violations_fts USING fts5(
            violation_type, content, relevance, legal_basis,
            content=appclose_violations,
            content_rowid=id
        )
    """)
    cur.execute("""
        INSERT INTO appclose_violations_fts(rowid, violation_type, content, relevance, legal_basis)
        SELECT id, violation_type, content, relevance, legal_basis FROM appclose_violations
    """)

    cur.execute("DROP TABLE IF EXISTS canonical_facts_fts")
    cur.execute("""
        CREATE VIRTUAL TABLE canonical_facts_fts USING fts5(
            fact_text, fact_category, source_conversation,
            content=canonical_fact_index,
            content_rowid=id
        )
    """)
    cur.execute("""
        INSERT INTO canonical_facts_fts(rowid, fact_text, fact_category, source_conversation)
        SELECT id, fact_text, fact_category, source_conversation FROM canonical_fact_index
    """)

    conn.commit()
    print("[+] FTS5 indexes built: appclose_messages_fts, appclose_violations_fts, canonical_facts_fts")


# ═══════════════════════════════════════════════════════════════
# PHASE 9: CROSS-LINK TO EVIDENCE CHAINS
# ═══════════════════════════════════════════════════════════════

def cross_link_evidence(conn):
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS appclose_evidence_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        appclose_msg_id INTEGER,
        appclose_violation_id INTEGER,
        linked_table TEXT,
        linked_id INTEGER,
        link_type TEXT,
        match_score REAL,
        created_at TEXT DEFAULT (datetime('now'))
    )
    """)

    cur.execute("""
        INSERT INTO appclose_evidence_links (appclose_violation_id, linked_table, linked_id, link_type, match_score)
        SELECT av.id, 'evidence_quotes', eq.id, 'content_match', 0.7
        FROM appclose_violations av
        JOIN evidence_quotes eq ON eq.quote_text LIKE '%appclose%'
            OR eq.quote_text LIKE '%app close%'
        WHERE av.content IS NOT NULL
        LIMIT 500
    """)
    eq_links = cur.rowcount

    cur.execute("""
        INSERT INTO appclose_evidence_links (appclose_msg_id, linked_table, linked_id, link_type, match_score)
        SELECT am.id, 'master_timeline', mt.id, 'date_match', 0.6
        FROM appclose_messages am
        JOIN master_timeline mt ON mt.event_detail LIKE '%appclose%' OR mt.event_detail LIKE '%app close%'
        WHERE am.message_date IS NOT NULL
        LIMIT 500
    """)
    mt_links = cur.rowcount

    cur.execute("""
        INSERT INTO appclose_evidence_links (appclose_violation_id, linked_table, linked_id, link_type, match_score)
        SELECT av.id, 'parental_alienation_evidence', pa.id, 'violation_match', 0.8
        FROM appclose_violations av
        JOIN parental_alienation_evidence pa ON av.violation_type = 'PARENTAL_ALIENATION'
        LIMIT 100
    """)
    pa_links = cur.rowcount

    conn.commit()
    print(f"[+] Cross-linked: {eq_links} evidence_quotes, {mt_links} timeline, {pa_links} alienation entries")
    return eq_links + mt_links + pa_links


# ═══════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("  APPCLOSE INGESTION ENGINE - LitigationOS")
    print("=" * 70)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=10000")

    # Phase 1: Create tables
    print("\n[PHASE 1] Creating tables...")
    create_tables(conn)

    # Phase 2: Catalog files
    print("\n[PHASE 2] Cataloging AppClose files across drives...")
    catalog_files = catalog_appclose_files(conn)

    # Phase 3: Parse text conversation files
    print("\n[PHASE 3] Parsing AppClose text conversations...")
    text_files = [
        r"C:\Users\andre\LitigationOS\02_EVIDENCE\03_EVIDENCE\DOWNLOADS_INTAKE\app close page1.txt",
        r"C:\Users\andre\LitigationOS\16_DOCUMENTS\_ROOT_TEXT\app close page1_3.txt",
        r"C:\Users\andre\LitigationOS\16_DOCUMENTS\_ROOT_TEXT\Copy of APPCLOSE 1 (2)_20250107182545_e0d17858.txt",
        r"C:\Users\andre\LitigationOS\16_DOCUMENTS\_ROOT_TEXT\appclose easter parenting time refusal.pdf_0cf5d9e0.txt",
        r"C:\Users\andre\LitigationOS\16_DOCUMENTS\_ROOT_TEXT\31_Exhibit_A_B_AppClose_Messages.pdf_a698163c.txt",
        r"C:\Users\andre\LitigationOS\16_DOCUMENTS\_ROOT_TEXT\app close page1(0).txt",
        r"C:\Users\andre\LitigationOS\16_DOCUMENTS\_ROOT_TEXT\appclose just conversation conv(0).txt",
        r"C:\Users\andre\LitigationOS\16_DOCUMENTS\_ROOT_TEXT\appclose just conversation conv 1(0).txt",
        r"C:\Users\andre\LitigationOS\02_EVIDENCE\scans\Scans\discovery\fredprime-legal-system\LITIGATION_OS__CAPSTONE__appclose just conversation conv 1(0).txt",
        r"C:\Users\andre\LitigationOS\02_EVIDENCE\scans\Scans\discovery\fredprime-legal-system\LITIGATION_OS__CAPSTONE__appclose just conversation conv(0).txt",
    ]

    all_messages = []
    seen_hashes = set()
    for tf in text_files:
        if os.path.exists(tf) and os.path.getsize(tf) > 10:
            msgs = parse_appclose_text(tf)
            print(f"  {os.path.basename(tf)}: {len(msgs)} messages")
            for m in msgs:
                if m['text_hash'] not in seen_hashes:
                    seen_hashes.add(m['text_hash'])
                    all_messages.append(m)

    # Phase 4: Parse PDFs
    print("\n[PHASE 4] Extracting from AppClose PDFs...")
    pdf_files = [
        r"C:\Users\andre\LitigationOS\02_EVIDENCE\PDF_SIZE_SORTED\Medium\2025-02\appclose just conversation_20250107182540_1.pdf",
        r"C:\Users\andre\LitigationOS\02_EVIDENCE\PDF_SIZE_SORTED\Medium\2025-02\appcloseLASTONE-20241030_20250107182534_1.pdf",
        r"C:\Users\andre\LitigationOS\02_EVIDENCE\PDF_SIZE_SORTED\Medium\2025-03\Appclose JUly-Feb 2025_1.pdf",
        r"C:\Users\andre\LitigationOS\02_EVIDENCE\PDF_SIZE_SORTED\Medium\2025-03\appclose just conversation.pdf",
        r"C:\Users\andre\LitigationOS\02_EVIDENCE\PDF_SIZE_SORTED\Medium\2025-03\appcloseLASTONE-20241030_1.pdf",
        r"C:\Users\andre\LitigationOS\02_EVIDENCE\PDF_SIZE_SORTED\Medium\2025-04\AppClose Report.pdf",
        r"C:\Users\andre\LitigationOS\02_EVIDENCE\PDF_SIZE_SORTED\Small\2025-03\appclose Feb 5th 2025_1.pdf",
        r"C:\Users\andre\LitigationOS\02_EVIDENCE\PDF_SIZE_SORTED\Small\2025-03\APPCLOSEconversations-3_13_2025-11_23AM.pdf",
        r"C:\Users\andre\LitigationOS\02_EVIDENCE\PDF_SIZE_SORTED\Small\1979-12\Copy of APPCLOSE#1 (2)_20250107182545_1.pdf",
        r"C:\Users\andre\LitigationOS\02_EVIDENCE\_ROOT_PDFS\31_Exhibit_A_B_AppClose_Messages_e28d6500.pdf",
        r"C:\Users\andre\LitigationOS\02_EVIDENCE\_ROOT_PDFS\appclose emily fails_20250107182536_82f53002.pdf",
        r"C:\Users\andre\LitigationOS\02_EVIDENCE\_ROOT_PDFS\AppClose Report_20250107182529_20250107182550_b32f2a0f.pdf",
        r"C:\Users\andre\LitigationOS\02_EVIDENCE\_ROOT_PDFS\AppClose Report_20250107182538_f8916ba0.pdf",
        r"C:\Users\andre\LitigationOS\02_EVIDENCE\_ROOT_PDFS\Exhibit_B_AppClose_Logs_908baf79.pdf",
        r"C:\Users\andre\LitigationOS\04_COURT_FILINGS\ARCHIVED_BUNDLES\Pigors_Litigation_Bundle_April_2025_1_\Exhibits\Exhibit_B_AppClose_Logs.pdf",
    ]

    for pf in pdf_files:
        if os.path.exists(pf):
            msgs = extract_pdf_messages(pf)
            new_count = 0
            for m in msgs:
                if m['text_hash'] not in seen_hashes:
                    seen_hashes.add(m['text_hash'])
                    all_messages.append(m)
                    new_count += 1
            print(f"  {os.path.basename(pf)}: {len(msgs)} extracted, {new_count} unique")

    # Phase 5: Parse CSV violations
    print("\n[PHASE 5] Parsing AppClose violation CSVs...")
    csv_files = [
        r"C:\Users\andre\LitigationOS\07_DATABASES\_ROOT_CSV\AppClose_Citations_-_Continued_5 (1) (1).csv",
        r"C:\Users\andre\LitigationOS\07_DATABASES\_ROOT_CSV\AppClose_Citations_-_Continued_5 (1).csv",
    ]

    all_violations = []
    seen_v_hashes = set()
    for cf in csv_files:
        if os.path.exists(cf):
            viols = parse_citations_csv(cf)
            for v in viols:
                vh = hashlib.md5(v['content'][:200].encode()).hexdigest()
                if vh not in seen_v_hashes:
                    seen_v_hashes.add(vh)
                    all_violations.append(v)
            print(f"  {os.path.basename(cf)}: {len(viols)} violations")

    # Phase 6: Insert messages into DB
    print(f"\n[PHASE 6] Inserting {len(all_messages)} unique messages into DB...")
    cur = conn.cursor()
    msg_inserted = 0
    for m in all_messages:
        try:
            cur.execute("""
                INSERT INTO appclose_messages
                (sender, recipient, message_date, message_time, viewed_by, viewed_date,
                 viewed_time, message_type, message_text, report_period, source_file, text_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (m['sender'], m['recipient'], m['message_date'], m['message_time'],
                  m['viewed_by'], m['viewed_date'], m['viewed_time'], m['message_type'],
                  m['message_text'], m.get('report_period'), m['source_file'], m['text_hash']))
            msg_inserted += 1
        except:
            pass
    conn.commit()
    print(f"  -> {msg_inserted} messages inserted")

    for tf in text_files:
        if os.path.exists(tf):
            count = sum(1 for m in all_messages if m['source_file'] == tf)
            if count > 0:
                cur.execute("UPDATE appclose_file_catalog SET messages_extracted = ?, ingested = 1 WHERE file_path = ?",
                           (count, tf))
    conn.commit()

    # Phase 7: Insert violations
    print(f"\n[PHASE 7] Inserting {len(all_violations)} unique violations into DB...")
    viol_inserted = 0
    for v in all_violations:
        try:
            cur.execute("""
                INSERT INTO appclose_violations
                (incident_id, violation_date, violation_time, page_ref, violation_type,
                 content, relevance, legal_basis, severity, source_file)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (v['incident_id'], v['violation_date'], v['violation_time'], v.get('page_ref'),
                  v['violation_type'], v['content'], v['relevance'], v.get('legal_basis'),
                  v['severity'], v['source_file']))
            viol_inserted += 1
        except:
            pass
    conn.commit()
    print(f"  -> {viol_inserted} violations inserted")

    # Phase 8: Master affidavits
    print("\n[PHASE 8] Registering master affidavits...")
    ingest_master_affidavits(conn)

    # Phase 9: Canonical facts
    print("\n[PHASE 9] Indexing canonical facts...")
    ingest_canonical_facts(conn)

    # Phase 10: Build FTS
    print("\n[PHASE 10] Building FTS5 indexes...")
    build_fts_indexes(conn)

    # Phase 11: Cross-link
    print("\n[PHASE 11] Cross-linking to evidence chains...")
    cross_link_evidence(conn)

    # Final stats
    print("\n" + "=" * 70)
    print("  INGESTION COMPLETE - FINAL STATS")
    print("=" * 70)

    tables_to_check = [
        'appclose_messages', 'appclose_violations', 'appclose_file_catalog',
        'appclose_evidence_links', 'master_affidavit_registry', 'canonical_fact_index',
        'appclose_messages_fts', 'appclose_violations_fts', 'canonical_facts_fts'
    ]
    for t in tables_to_check:
        try:
            cur.execute(f"SELECT COUNT(*) FROM [{t}]")
            cnt = cur.fetchone()[0]
            print(f"  {t}: {cnt} rows")
        except:
            print(f"  {t}: (not found)")

    cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
    total_tables = cur.fetchone()[0]
    print(f"\n  Total DB tables: {total_tables}")

    conn.close()
    print("\n[DONE] AppClose ingestion engine complete")


if __name__ == '__main__':
    main()
