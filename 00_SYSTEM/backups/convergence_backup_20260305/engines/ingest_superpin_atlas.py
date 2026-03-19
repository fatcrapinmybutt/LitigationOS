#!/usr/bin/env python3
"""
ingest_superpin_atlas.py — Ingest Superpin + Atlas + Gemini Masterpack Data
Creates: superpin_atlas_data, superpin_gemini_data tables with FTS5 indexes
Sources:
  - F:\MI_SUPERPIN_ATLAS_v2026-02-14\MI_SUPERPIN_ATLAS_v2026-02-14\
  - F:\MI_SUPERPIN_ATLAS_v2026-02-14__1\MI_SUPERPIN_ATLAS_v2026-02-14\
  - F:\LITIGATIONOS_AUTHORITY_UNIVERSE_SUPERPIN_v2026-02-14\
  - F:\LITIGATIONOS_GEMINI_MASTERPACK_v2026-02-14_01\ (nested)
  - F:\LITIGATIONOS_GEMINI_MASTERPACK_v2026-02-14_02\ (nested)
"""
import sys, os, sqlite3, json, hashlib, re
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

DB = r'C:\Users\andre\LitigationOS\litigation_context.db'

SUPERPIN_DIRS = [
    r'F:\MI_SUPERPIN_ATLAS_v2026-02-14\MI_SUPERPIN_ATLAS_v2026-02-14',
    r'F:\MI_SUPERPIN_ATLAS_v2026-02-14__1\MI_SUPERPIN_ATLAS_v2026-02-14',
    r'F:\LITIGATIONOS_AUTHORITY_UNIVERSE_SUPERPIN_v2026-02-14',
]

GEMINI_DIRS = [
    r'F:\LITIGATIONOS_GEMINI_MASTERPACK_v2026-02-14_01',
    r'F:\LITIGATIONOS_GEMINI_MASTERPACK_v2026-02-14_02',
]

READABLE_EXTS = {'.md', '.txt', '.json', '.csv', '.yaml', '.yml', '.py', '.jsonl', '.rtf'}


def _conn():
    c = sqlite3.connect(DB, timeout=120)
    c.execute('PRAGMA busy_timeout=60000')
    c.execute('PRAGMA journal_mode=WAL')
    return c


def extract_tags(filename, content_preview):
    """Extract category tags from filename and content."""
    tags = []
    fn = filename.lower()
    if 'atlas' in fn: tags.append('atlas')
    if 'superpin' in fn: tags.append('superpin')
    if 'authority' in fn: tags.append('authority')
    if 'vehicle' in fn: tags.append('vehicle')
    if 'constitution' in fn: tags.append('constitutional')
    if 'mental_health' in fn or 'mdhhs' in fn: tags.append('mental_health')
    if 'benchbook' in fn: tags.append('benchbook')
    if 'checklist' in fn: tags.append('checklist')
    if 'lexicon' in fn: tags.append('lexicon')
    if 'citation' in fn: tags.append('citation')
    if 'automation' in fn or 'template' in fn: tags.append('template')
    if 'filing' in fn: tags.append('filing')
    if 'deadline' in fn or 'time' in fn: tags.append('deadline')
    if 'service' in fn or 'notice' in fn: tags.append('service')
    if 'discovery' in fn or 'subpoena' in fn: tags.append('discovery')
    if 'evidence' in fn or 'foundation' in fn: tags.append('evidence')
    if 'appellate' in fn or 'coa' in fn or 'msc' in fn: tags.append('appellate')
    if 'standard_of_review' in fn: tags.append('standard_of_review')
    if 'record' in fn: tags.append('record')
    if 'rule' in fn: tags.append('rule')
    if 'master' in fn: tags.append('master')
    if 'gemini' in fn: tags.append('gemini')
    if 'iop' in fn: tags.append('iop')
    if 'pdf' in fn or 'qa' in fn: tags.append('qa')
    if 'gap' in fn: tags.append('gap_audit')
    if 'taxonomy' in fn: tags.append('taxonomy')
    if 'readme' in fn: tags.append('readme')
    return ','.join(tags) if tags else 'general'


def categorize_file(filename):
    """Determine category from filename."""
    fn = filename.lower()
    if any(x in fn for x in ['atlas', 'superpin']): return 'atlas'
    if 'authority' in fn: return 'authority'
    if 'vehicle' in fn: return 'vehicle_law'
    if 'constitution' in fn: return 'constitutional'
    if 'mental_health' in fn or 'mdhhs' in fn: return 'mental_health'
    if 'benchbook' in fn: return 'benchbook'
    if 'checklist' in fn or 'qa' in fn: return 'quality_assurance'
    if 'lexicon' in fn: return 'lexicon'
    if 'citation' in fn: return 'citation'
    if 'template' in fn or 'automation' in fn: return 'template'
    if 'filing' in fn: return 'filing'
    if 'deadline' in fn or 'time' in fn: return 'deadline'
    if 'appellate' in fn: return 'appellate'
    if 'discovery' in fn or 'subpoena' in fn: return 'discovery'
    if 'evidence' in fn: return 'evidence'
    if 'master' in fn: return 'master_index'
    if 'rule' in fn: return 'rules'
    if 'readme' in fn: return 'documentation'
    return 'general'


def read_file_safe(fpath, max_bytes=500_000):
    """Read file content safely with encoding fallback."""
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            return f.read(max_bytes)
    except UnicodeDecodeError:
        try:
            with open(fpath, 'r', encoding='latin-1') as f:
                return f.read(max_bytes)
        except Exception:
            return None
    except Exception:
        return None


def collect_files(dirs, label):
    """Collect all readable files from directories recursively."""
    files = []
    for d in dirs:
        if not os.path.exists(d):
            print(f"  ⚠ Directory not found: {d}")
            continue
        for root, _, fnames in os.walk(d):
            for fn in fnames:
                ext = os.path.splitext(fn)[1].lower()
                if ext in READABLE_EXTS:
                    files.append(os.path.join(root, fn))
    print(f"  [{label}] Found {len(files)} readable files")
    return files


def ingest_superpin():
    """Ingest Superpin + Atlas data into superpin_atlas_data table."""
    conn = _conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS superpin_atlas_data (
            doc_id TEXT PRIMARY KEY,
            filename TEXT,
            content TEXT,
            category TEXT,
            tags TEXT,
            source_dir TEXT,
            file_size INTEGER,
            content_hash TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("DELETE FROM superpin_atlas_data")

    files = collect_files(SUPERPIN_DIRS, 'SUPERPIN+ATLAS')
    seen_hashes = set()
    count = 0

    for fpath in files:
        content = read_file_safe(fpath)
        if not content or len(content.strip()) < 10:
            continue

        chash = hashlib.md5(content.encode('utf-8', errors='replace')).hexdigest()
        if chash in seen_hashes:
            continue
        seen_hashes.add(chash)

        fname = os.path.basename(fpath)
        doc_id = f"sp_{hashlib.md5(fpath.encode()).hexdigest()[:12]}"
        category = categorize_file(fname)
        tags = extract_tags(fname, content[:500])
        fsize = os.path.getsize(fpath)

        conn.execute(
            "INSERT OR REPLACE INTO superpin_atlas_data VALUES (?,?,?,?,?,?,?,?,?)",
            (doc_id, fname, content, category, tags, os.path.dirname(fpath), fsize, chash, datetime.now().isoformat())
        )
        count += 1

    conn.commit()
    print(f"  ✅ Inserted {count} superpin/atlas documents (deduped from {len(files)} files)")

    # Create FTS5 index
    try:
        conn.execute("DROP TABLE IF EXISTS superpin_atlas_fts")
    except:
        pass
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS superpin_atlas_fts USING fts5(
            filename, content, category, tags,
            content='superpin_atlas_data',
            content_rowid='rowid'
        )
    """)
    conn.execute("""
        INSERT INTO superpin_atlas_fts(rowid, filename, content, category, tags)
        SELECT rowid, filename, content, category, tags FROM superpin_atlas_data
    """)
    conn.commit()
    print(f"  ✅ FTS5 index created for superpin_atlas_data")

    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    conn.close()
    return count


def ingest_gemini():
    """Ingest Gemini Masterpack data into superpin_gemini_data table."""
    conn = _conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS superpin_gemini_data (
            doc_id TEXT PRIMARY KEY,
            filename TEXT,
            content TEXT,
            category TEXT,
            tags TEXT,
            source_dir TEXT,
            file_size INTEGER,
            content_hash TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("DELETE FROM superpin_gemini_data")

    files = collect_files(GEMINI_DIRS, 'GEMINI')
    seen_hashes = set()
    count = 0

    for fpath in files:
        content = read_file_safe(fpath)
        if not content or len(content.strip()) < 10:
            continue

        chash = hashlib.md5(content.encode('utf-8', errors='replace')).hexdigest()
        if chash in seen_hashes:
            continue
        seen_hashes.add(chash)

        fname = os.path.basename(fpath)
        doc_id = f"gm_{hashlib.md5(fpath.encode()).hexdigest()[:12]}"
        category = categorize_file(fname)
        tags = extract_tags(fname, content[:500])
        fsize = os.path.getsize(fpath)

        conn.execute(
            "INSERT OR REPLACE INTO superpin_gemini_data VALUES (?,?,?,?,?,?,?,?,?)",
            (doc_id, fname, content, category, tags, os.path.dirname(fpath), fsize, chash, datetime.now().isoformat())
        )
        count += 1

    conn.commit()
    print(f"  ✅ Inserted {count} Gemini masterpack documents (deduped from {len(files)} files)")

    # Create FTS5 index
    try:
        conn.execute("DROP TABLE IF EXISTS superpin_gemini_fts")
    except:
        pass
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS superpin_gemini_fts USING fts5(
            filename, content, category, tags,
            content='superpin_gemini_data',
            content_rowid='rowid'
        )
    """)
    conn.execute("""
        INSERT INTO superpin_gemini_fts(rowid, filename, content, category, tags)
        SELECT rowid, filename, content, category, tags FROM superpin_gemini_data
    """)
    conn.commit()
    print(f"  ✅ FTS5 index created for superpin_gemini_data")

    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    conn.close()
    return count


if __name__ == '__main__':
    print("=" * 70)
    print("SUPERPIN + ATLAS + GEMINI INGESTION ENGINE")
    print("=" * 70)

    print("\n[PHASE 1] Ingesting Superpin + Atlas data...")
    sp_count = ingest_superpin()

    print("\n[PHASE 2] Ingesting Gemini Masterpack data...")
    gm_count = ingest_gemini()

    print(f"\n{'=' * 70}")
    print(f"INGESTION COMPLETE: {sp_count} superpin + {gm_count} gemini = {sp_count + gm_count} total documents")
    print(f"{'=' * 70}")
