"""
Ingest 767 harvest text files from I: drive into litigation_context.db.
- Reads full text content from each .txt file
- Reads metadata from harvest_catalog.jsonl
- Inserts into harvest_texts (deduped by original_filename)
- Creates harvest_evidence_meta table for term counts, party mentions, dates
"""
import sys, os, json, hashlib, time, re

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', errors='replace')

import sqlite3

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
TEXTS_DIR = r"I:\20260209_0430_HARVEST_000000006_FULL_SAFE\texts"
CATALOG_PATH = r"C:\Users\andre\LitigationOS\temp\harvest_catalog.jsonl"
HARVEST_WAVE = "HARVEST_007"

def topic_to_lane(topic):
    mapping = {
        'custody': 'A', 'housing': 'B', 'PPO': 'D', 'ppo': 'D',
        'judicial_misconduct': 'E', 'appellate': 'F',
        'evidence': 'C', 'financial': 'A', 'general': 'C'
    }
    return mapping.get(topic, 'C')

def topic_to_category(topic):
    mapping = {
        'custody': 'custody_proceeding', 'housing': 'housing_dispute',
        'PPO': 'protection_order', 'ppo': 'protection_order',
        'judicial_misconduct': 'judicial_complaint', 'appellate': 'appellate_filing',
        'evidence': 'evidence_document', 'financial': 'financial_record',
        'general': 'general_document'
    }
    return mapping.get(topic, 'general_document')

def extract_judges(text):
    judges = set()
    patterns = [r'McNeill', r'Judge\s+McNeill', r'Hon\.\s*Jenny', r'Jenny\s+L?\.\s*McNeill']
    for p in patterns:
        if re.search(p, text, re.IGNORECASE):
            judges.add('McNeill')
            break
    return ', '.join(judges) if judges else ''

def compute_litigation_value(meta):
    """Score 0-100 based on legal term density + party mentions."""
    hits = meta.get('total_term_hits', 0)
    parties = sum(meta.get('party_mentions', {}).values())
    cases = len(meta.get('case_numbers', []))
    dates = len(meta.get('dates_found', []))
    score = min(100, (hits * 0.3) + (parties * 2) + (cases * 10) + (dates * 1))
    return round(score)

def main():
    t0 = time.time()

    # Load catalog metadata
    print(f"Loading catalog from {CATALOG_PATH}...")
    catalog = {}
    with open(CATALOG_PATH, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            catalog[rec['file_name']] = rec
    print(f"  Catalog: {len(catalog)} entries")

    # List text files
    txt_files = sorted([f for f in os.listdir(TEXTS_DIR) if f.endswith('.txt')])
    print(f"  Text files: {len(txt_files)}")

    # Connect to DB
    conn = sqlite3.connect(DB_PATH, timeout=180)
    conn.execute("PRAGMA busy_timeout = 180000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA synchronous = NORMAL")

    # Check existing harvest_texts for duplicates
    existing = set()
    try:
        rows = conn.execute("SELECT original_filename FROM harvest_texts").fetchall()
        existing = {r[0] for r in rows}
        print(f"  Existing harvest_texts: {len(existing)} rows")
    except Exception as e:
        print(f"  Warning checking existing: {e}")

    # Check harvest_texts columns
    cols = conn.execute("PRAGMA table_info(harvest_texts)").fetchall()
    col_names = [c[1] for c in cols]
    print(f"  harvest_texts columns: {col_names}")

    # Create metadata table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS harvest_evidence_meta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT UNIQUE,
            file_path TEXT,
            size_bytes INTEGER,
            topic TEXT,
            case_lane TEXT,
            total_term_hits INTEGER,
            mcr_count INTEGER DEFAULT 0,
            mcl_count INTEGER DEFAULT 0,
            ex_parte_count INTEGER DEFAULT 0,
            parenting_time_count INTEGER DEFAULT 0,
            custody_count INTEGER DEFAULT 0,
            ppo_count INTEGER DEFAULT 0,
            contempt_count INTEGER DEFAULT 0,
            hearing_count INTEGER DEFAULT 0,
            order_count INTEGER DEFAULT 0,
            motion_count INTEGER DEFAULT 0,
            bond_count INTEGER DEFAULT 0,
            alienation_count INTEGER DEFAULT 0,
            constitutional_count INTEGER DEFAULT 0,
            due_process_count INTEGER DEFAULT 0,
            mcneill_mentions INTEGER DEFAULT 0,
            watson_mentions INTEGER DEFAULT 0,
            pigors_mentions INTEGER DEFAULT 0,
            barnes_mentions INTEGER DEFAULT 0,
            berry_mentions INTEGER DEFAULT 0,
            rusco_mentions INTEGER DEFAULT 0,
            case_numbers TEXT,
            dates_found TEXT,
            litigation_value INTEGER DEFAULT 0,
            harvest_wave TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Build insert rows
    harvest_rows = []
    meta_rows = []
    skipped_dup = 0
    skipped_err = 0
    total_chars = 0
    total_words = 0

    for i, fname in enumerate(txt_files):
        if fname in existing:
            skipped_dup += 1
            continue

        fpath = os.path.join(TEXTS_DIR, fname)
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                text = f.read()
        except Exception as e:
            print(f"  ERROR reading {fname}: {e}")
            skipped_err += 1
            continue

        meta = catalog.get(fname, {})
        topic = meta.get('topic', 'general')
        lane = topic_to_lane(topic)
        category = topic_to_category(topic)
        char_count = len(text)
        word_count = len(text.split())
        total_chars += char_count
        total_words += word_count

        case_nums = ', '.join(meta.get('case_numbers', []))
        judges = extract_judges(text)
        lit_value = compute_litigation_value(meta)

        harvest_id = f"{HARVEST_WAVE}_{i+1:04d}"

        # For harvest_texts
        harvest_rows.append((
            harvest_id,
            fpath,
            fname,
            category,
            topic,
            lane,
            text,
            char_count,
            word_count,
            case_nums,
            judges,
            lit_value
        ))

        # For harvest_evidence_meta
        tc = meta.get('term_counts', {})
        pm = meta.get('party_mentions', {})
        meta_rows.append((
            fname,
            fpath,
            meta.get('size_bytes', char_count),
            topic,
            lane,
            meta.get('total_term_hits', 0),
            tc.get('MCR', 0),
            tc.get('MCL', 0),
            tc.get('ex parte', 0),
            tc.get('parenting time', 0),
            tc.get('custody', 0),
            tc.get('PPO', 0),
            tc.get('contempt', 0),
            tc.get('hearing', 0),
            tc.get('order', 0),
            tc.get('motion', 0),
            tc.get('bond', 0),
            tc.get('alienation', 0),
            tc.get('constitutional', 0),
            tc.get('due process', 0),
            pm.get('McNeill', 0),
            pm.get('Watson', 0),
            pm.get('Pigors', 0),
            pm.get('Barnes', 0),
            pm.get('Berry', 0),
            pm.get('Rusco', 0),
            json.dumps(meta.get('case_numbers', [])),
            json.dumps(meta.get('dates_found', [])),
            lit_value,
            HARVEST_WAVE
        ))

        if (i + 1) % 100 == 0:
            print(f"  Read {i+1}/{len(txt_files)} files ({total_chars:,} chars)...")

    print(f"\nRead complete: {len(harvest_rows)} new files, {skipped_dup} duplicates skipped, {skipped_err} errors")
    print(f"Total text: {total_chars:,} chars, {total_words:,} words")

    # Batch insert into harvest_texts
    if harvest_rows:
        print(f"\nInserting {len(harvest_rows)} rows into harvest_texts...")
        conn.executemany("""
            INSERT OR IGNORE INTO harvest_texts
            (harvest_id, source_file, original_filename, doc_category, doc_subcategory,
             lane, text_content, char_count, word_count, case_numbers_found,
             judges_found, litigation_value)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, harvest_rows)
        conn.commit()
        print("  harvest_texts insert complete.")

    # Batch insert into harvest_evidence_meta
    if meta_rows:
        print(f"Inserting {len(meta_rows)} rows into harvest_evidence_meta...")
        conn.executemany("""
            INSERT OR IGNORE INTO harvest_evidence_meta
            (file_name, file_path, size_bytes, topic, case_lane, total_term_hits,
             mcr_count, mcl_count, ex_parte_count, parenting_time_count,
             custody_count, ppo_count, contempt_count, hearing_count,
             order_count, motion_count, bond_count, alienation_count,
             constitutional_count, due_process_count,
             mcneill_mentions, watson_mentions, pigors_mentions,
             barnes_mentions, berry_mentions, rusco_mentions,
             case_numbers, dates_found, litigation_value, harvest_wave)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, meta_rows)
        conn.commit()
        print("  harvest_evidence_meta insert complete.")

    # Verify
    ht_count = conn.execute("SELECT COUNT(*) FROM harvest_texts").fetchone()[0]
    hm_count = conn.execute("SELECT COUNT(*) FROM harvest_evidence_meta").fetchone()[0]
    ht_chars = conn.execute("SELECT SUM(char_count) FROM harvest_texts WHERE harvest_id LIKE 'HARVEST_007%'").fetchone()[0] or 0

    # Update harvest_progress
    conn.execute("""
        INSERT OR REPLACE INTO harvest_progress
        (source_root, wave_name, files_processed, files_skipped, files_errored,
         total_chars, total_pages, started_at, completed_at, status)
        VALUES (?, ?, ?, ?, ?, ?, 0, ?, datetime('now'), 'complete')
    """, (
        TEXTS_DIR, HARVEST_WAVE, len(harvest_rows), skipped_dup, skipped_err,
        total_chars, time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(t0))
    ))
    conn.commit()

    # Topic distribution in new meta
    print("\n=== TOPIC DISTRIBUTION (harvest_evidence_meta) ===")
    topics = conn.execute("""
        SELECT topic, COUNT(*), SUM(total_term_hits), ROUND(AVG(litigation_value),1)
        FROM harvest_evidence_meta
        GROUP BY topic ORDER BY COUNT(*) DESC
    """).fetchall()
    for t in topics:
        print(f"  {t[0]:25s} {t[1]:4d} files  {t[2]:6d} term hits  avg_value={t[3]}")

    elapsed = time.time() - t0
    print(f"\n=== DONE in {elapsed:.1f}s ===")
    print(f"  harvest_texts:         {ht_count} total rows ({ht_chars:,} chars from HARVEST_007)")
    print(f"  harvest_evidence_meta: {hm_count} total rows")
    print(f"  harvest_progress:      HARVEST_007 logged")

    conn.close()

if __name__ == '__main__':
    main()
