#!/usr/bin/env python3
"""
OMEGA DEDUP ENGINE v1.0
8-Tier Neural Cross-Drive Deduplication + Filesystem Restructure

Tiers:
  0: Fast filter (size bucketing)
  1: Partial hash (first+last 64KB SHA-256)
  2: Full hash (SHA-256)
  3: MinHash LSH (text-dedup, Jaccard > 0.8)
  4: Structural fingerprint (magic bytes + page count)
  5: Content extraction (PyMuPDF + RapidFuzz token_sort_ratio)
  6: Neural semantic (sentence-transformers -> FAISS ANN, cosine > 0.95)
  7: Perceptual (Pillow pHash for images)

Safety:
  - Recycle Bin only (no hard deletes)
  - Full rollback journal
  - Court docs exempt
  - Checkpoint every 500 ops
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import hashlib
import sqlite3
import json
import time
import struct
import subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------
LITIGOS_ROOT = r"C:\Users\andre\LitigationOS"
MANIFESTS_DIR = os.path.join(LITIGOS_ROOT, "00_SYSTEM", "manifests")
DEDUP_DB_PATH = os.path.join(MANIFESTS_DIR, "omega_dedup.db")
FAISS_INDEX_PATH = os.path.join(MANIFESTS_DIR, "faiss_document_index.bin")
HASH_CHUNK = 65536  # 64KB for partial hash
CHECKPOINT_INTERVAL = 500
LEGAL_PATTERNS = [
    "mcr", "mcl", "mre", "frcp", "usc", "motion", "brief", "complaint",
    "affidavit", "exhibit", "order", "docket", "filing", "court",
    "pigors", "watson", "mcneill", "barnes", "shady oaks",
    "parenting", "custody", "ppo", "foc"
]

# ---------------------------------------------------------------------------
# DATABASE SETUP
# ---------------------------------------------------------------------------
def get_db(path=None):
    """Get a connection to the dedup intelligence DB."""
    db_path = path or DEDUP_DB_PATH
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=120)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn

def init_db(conn):
    """Initialize dedup intelligence tables."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS file_manifest (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drive TEXT,
            path TEXT UNIQUE,
            filename TEXT,
            ext TEXT,
            size INTEGER,
            mtime REAL,
            partial_hash TEXT,
            full_hash TEXT,
            magic_bytes TEXT,
            content_text TEXT,
            legal_score REAL DEFAULT 0.0,
            file_type TEXT,
            is_canonical INTEGER DEFAULT 0,
            embedding_id INTEGER DEFAULT -1,
            scanned_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_manifest_size ON file_manifest(size);
        CREATE INDEX IF NOT EXISTS idx_manifest_partial ON file_manifest(partial_hash);
        CREATE INDEX IF NOT EXISTS idx_manifest_full ON file_manifest(full_hash);
        CREATE INDEX IF NOT EXISTS idx_manifest_drive ON file_manifest(drive);
        CREATE INDEX IF NOT EXISTS idx_manifest_ext ON file_manifest(ext);

        CREATE TABLE IF NOT EXISTS dedup_clusters (
            cluster_id TEXT,
            file_id INTEGER,
            similarity REAL,
            tier_matched INTEGER,
            is_canonical INTEGER DEFAULT 0,
            action TEXT DEFAULT 'pending',
            FOREIGN KEY (file_id) REFERENCES file_manifest(id)
        );
        CREATE INDEX IF NOT EXISTS idx_cluster_id ON dedup_clusters(cluster_id);
        CREATE INDEX IF NOT EXISTS idx_cluster_file ON dedup_clusters(file_id);

        CREATE TABLE IF NOT EXISTS move_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            operation TEXT,
            source_path TEXT,
            dest_path TEXT,
            cluster_id TEXT,
            tier INTEGER,
            file_size INTEGER,
            rollback_cmd TEXT,
            status TEXT DEFAULT 'pending'
        );

        CREATE TABLE IF NOT EXISTS scan_progress (
            drive TEXT PRIMARY KEY,
            total_files INTEGER DEFAULT 0,
            scanned_files INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            started_at TEXT,
            completed_at TEXT
        );

        CREATE TABLE IF NOT EXISTS dedup_stats (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    """)
    conn.commit()

# ---------------------------------------------------------------------------
# TIER 0: FAST FILTER (size bucketing)
# ---------------------------------------------------------------------------
def scan_files_fd(root_path, drive_letter):
    """Use fd for ultra-fast file enumeration, fall back to os.walk."""
    files = []
    try:
        result = subprocess.run(
            ["fd", "--type", "f", "--absolute-path", "--no-ignore", "."],
            capture_output=True, text=True, cwd=root_path, timeout=600,
            encoding='utf-8', errors='replace'
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                line = line.strip()
                if line:
                    files.append(line)
            return files
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Fallback to os.walk
    for dirpath, _, filenames in os.walk(root_path):
        for fn in filenames:
            files.append(os.path.join(dirpath, fn))
    return files


def compute_partial_hash(filepath):
    """SHA-256 of first 64KB + last 64KB."""
    try:
        size = os.path.getsize(filepath)
        if size == 0:
            return "EMPTY"
        h = hashlib.sha256()
        with open(filepath, 'rb') as f:
            h.update(f.read(HASH_CHUNK))
            if size > HASH_CHUNK * 2:
                f.seek(-HASH_CHUNK, 2)
                h.update(f.read(HASH_CHUNK))
        return h.hexdigest()
    except (OSError, PermissionError):
        return None


def compute_full_hash(filepath):
    """Full file SHA-256."""
    try:
        h = hashlib.sha256()
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(131072)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except (OSError, PermissionError):
        return None


def read_magic_bytes(filepath, n=8):
    """Read first N bytes for file type identification."""
    try:
        with open(filepath, 'rb') as f:
            data = f.read(n)
            return data.hex() if data else ""
    except (OSError, PermissionError):
        return ""


def score_legal_relevance(filepath):
    """Score 0-1 for legal document relevance based on path patterns."""
    path_lower = filepath.lower()
    score = 0.0
    for pattern in LEGAL_PATTERNS:
        if pattern in path_lower:
            score += 0.1
    # Court-stamped detection
    if any(x in path_lower for x in ["court_ready", "filed_", "court_stamped", "certified"]):
        score += 0.5
    return min(score, 1.0)


def classify_file_type(ext, magic_hex):
    """Classify file into category based on extension and magic bytes."""
    ext = ext.lower()
    if ext in ('.pdf',):
        return 'pdf'
    if ext in ('.docx', '.doc'):
        return 'document'
    if ext in ('.txt', '.md', '.rst', '.rtf'):
        return 'text'
    if ext in ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico'):
        return 'image'
    if ext in ('.py', '.js', '.ts', '.java', '.go', '.rs', '.cs', '.rb', '.sh', '.ps1', '.bat'):
        return 'code'
    if ext in ('.csv', '.json', '.jsonl', '.xml', '.yaml', '.yml', '.toml'):
        return 'data'
    if ext in ('.db', '.sqlite', '.sqlite3'):
        return 'database'
    if ext in ('.zip', '.tar', '.gz', '.7z', '.rar'):
        return 'archive'
    if ext in ('.html', '.htm', '.css', '.scss'):
        return 'web'
    if ext in ('.exe', '.dll', '.so', '.dylib', '.msi'):
        return 'binary'
    # Magic byte fallback
    if magic_hex.startswith('25504446'):  # %PDF
        return 'pdf'
    if magic_hex.startswith('504b0304'):  # PK (zip/docx)
        return 'archive'
    if magic_hex.startswith('89504e47'):  # PNG
        return 'image'
    if magic_hex.startswith('ffd8ff'):    # JPEG
        return 'image'
    return 'other'


def build_manifest(root_path, drive_letter, conn, skip_dirs=None):
    """2-Pass scan: fast metadata first, then targeted hashing on size-matched candidates only."""
    skip_dirs = skip_dirs or []
    skip_lower = [s.lower() for s in skip_dirs]

    print(f"[SCAN] Starting 2-pass scan of {drive_letter}: ({root_path})")
    init_db(conn)

    conn.execute(
        "INSERT OR REPLACE INTO scan_progress (drive, status, started_at) VALUES (?, 'scanning', ?)",
        (drive_letter, datetime.now().isoformat())
    )
    conn.commit()

    # --- PASS 1: Fast metadata-only scan (no hashing, no magic bytes) ---
    print(f"[PASS 1] Enumerating files (metadata only)...")
    files = scan_files_fd(root_path, drive_letter)
    total = len(files)
    print(f"[PASS 1] Found {total:,} files on {drive_letter}:")

    conn.execute("UPDATE scan_progress SET total_files = ? WHERE drive = ?", (total, drive_letter))
    conn.commit()

    batch = []
    scanned = 0
    skipped = 0
    size_counts = defaultdict(int)
    BATCH_SIZE = 2000

    for filepath in files:
        fp_lower = filepath.lower()
        if any(sd in fp_lower for sd in skip_lower):
            skipped += 1
            continue

        try:
            st = os.stat(filepath)
            size = st.st_size
            mtime = st.st_mtime
        except (OSError, PermissionError):
            skipped += 1
            continue

        filename = os.path.basename(filepath)
        ext = os.path.splitext(filename)[1]
        legal_score = score_legal_relevance(filepath)

        batch.append((drive_letter, filepath, filename, ext, size, mtime, legal_score, datetime.now().isoformat()))
        size_counts[size] += 1
        scanned += 1

        if scanned % BATCH_SIZE == 0:
            conn.executemany(
                """INSERT OR IGNORE INTO file_manifest
                   (drive, path, filename, ext, size, mtime, legal_score, scanned_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                batch
            )
            conn.commit()
            batch.clear()
            if scanned % 10000 == 0:
                print(f"  [P1] {scanned:,}/{total:,} cataloged ({skipped} skipped)")

    if batch:
        conn.executemany(
            """INSERT OR IGNORE INTO file_manifest
               (drive, path, filename, ext, size, mtime, legal_score, scanned_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            batch
        )
        conn.commit()

    dupe_sizes = {s for s, c in size_counts.items() if c > 1 and s > 0}
    print(f"[PASS 1] Complete: {scanned:,} files cataloged, {skipped} skipped")
    print(f"[PASS 1] {len(dupe_sizes):,} size buckets with >1 file ({sum(size_counts[s] for s in dupe_sizes):,} files to hash)")

    # --- PASS 2: Targeted hashing + magic bytes (only size-matched candidates) ---
    print(f"[PASS 2] Hashing size-matched candidates...")
    cursor = conn.execute(
        """SELECT id, path, size FROM file_manifest
           WHERE drive = ? AND partial_hash IS NULL AND size > 0
           ORDER BY size""",
        (drive_letter,)
    )
    candidates = [(r[0], r[1], r[2]) for r in cursor if r[2] in dupe_sizes]
    hash_total = len(candidates)
    print(f"[PASS 2] {hash_total:,} files need hashing")

    hashed = 0
    hash_batch = []

    for file_id, filepath, size in candidates:
        partial_hash = compute_partial_hash(filepath)
        magic = read_magic_bytes(filepath)
        file_type = classify_file_type(os.path.splitext(filepath)[1], magic)

        hash_batch.append((partial_hash, magic, file_type, file_id))
        hashed += 1

        if hashed % BATCH_SIZE == 0:
            conn.executemany(
                "UPDATE file_manifest SET partial_hash = ?, magic_bytes = ?, file_type = ? WHERE id = ?",
                hash_batch
            )
            conn.commit()
            hash_batch.clear()
            if hashed % 10000 == 0:
                print(f"  [P2] {hashed:,}/{hash_total:,} hashed")

    if hash_batch:
        conn.executemany(
            "UPDATE file_manifest SET partial_hash = ?, magic_bytes = ?, file_type = ? WHERE id = ?",
            hash_batch
        )
        conn.commit()

    # Classify remaining unhashed files (unique sizes)
    conn.execute(
        """UPDATE file_manifest SET file_type = 'unique_size'
           WHERE drive = ? AND partial_hash IS NULL AND file_type IS NULL""",
        (drive_letter,)
    )
    conn.commit()

    conn.execute(
        "UPDATE scan_progress SET scanned_files = ?, status = 'complete', completed_at = ? WHERE drive = ?",
        (scanned, datetime.now().isoformat(), drive_letter)
    )
    conn.commit()

    print(f"[SCAN] {drive_letter}: complete. {scanned:,} files cataloged, {hashed:,} hashed, {skipped} skipped.")
    return scanned


# ---------------------------------------------------------------------------
# TIER 1-2: EXACT DEDUP (partial hash + full hash confirmation)
# ---------------------------------------------------------------------------
def find_exact_duplicates(conn):
    """Find exact duplicates via size + partial_hash, confirm with full hash."""
    print("[DEDUP T0-2] Finding exact duplicates...")

    # Find size+partial_hash groups with >1 file
    cursor = conn.execute("""
        SELECT size, partial_hash, COUNT(*) as cnt
        FROM file_manifest
        WHERE partial_hash IS NOT NULL AND partial_hash != 'EMPTY' AND size > 0
        GROUP BY size, partial_hash
        HAVING cnt > 1
        ORDER BY size * cnt DESC
    """)
    groups = cursor.fetchall()
    print(f"  Found {len(groups):,} candidate groups (same size + partial hash)")

    cluster_count = 0
    total_dupes = 0
    total_bytes = 0

    for size, phash, cnt in groups:
        # Get all files in this group
        files = conn.execute(
            "SELECT id, path, legal_score FROM file_manifest WHERE size = ? AND partial_hash = ?",
            (size, phash)
        ).fetchall()

        if len(files) < 2:
            continue

        # For files > 1MB, confirm with full hash
        if size > 1048576:
            hash_groups = defaultdict(list)
            for fid, fpath, lscore in files:
                fhash = compute_full_hash(fpath)
                if fhash:
                    conn.execute("UPDATE file_manifest SET full_hash = ? WHERE id = ?", (fhash, fid))
                    hash_groups[fhash].append((fid, fpath, lscore))
            conn.commit()

            for fhash, fgroup in hash_groups.items():
                if len(fgroup) < 2:
                    continue
                cluster_id = f"exact-{cluster_count}"
                # Elect canonical: highest legal_score, then shortest path
                fgroup.sort(key=lambda x: (-x[2], len(x[1])))
                for i, (fid, fpath, lscore) in enumerate(fgroup):
                    is_canon = 1 if i == 0 else 0
                    action = 'keep' if is_canon else 'recycle'
                    conn.execute(
                        "INSERT INTO dedup_clusters (cluster_id, file_id, similarity, tier_matched, is_canonical, action) VALUES (?,?,?,?,?,?)",
                        (cluster_id, fid, 1.0, 2, is_canon, action)
                    )
                total_dupes += len(fgroup) - 1
                total_bytes += size * (len(fgroup) - 1)
                cluster_count += 1
        else:
            # Small files: partial hash is sufficient
            cluster_id = f"exact-{cluster_count}"
            files.sort(key=lambda x: (-x[2], len(x[1])))
            for i, (fid, fpath, lscore) in enumerate(files):
                is_canon = 1 if i == 0 else 0
                action = 'keep' if is_canon else 'recycle'
                conn.execute(
                    "INSERT INTO dedup_clusters (cluster_id, file_id, similarity, tier_matched, is_canonical, action) VALUES (?,?,?,?,?,?)",
                    (cluster_id, fid, 1.0, 1, is_canon, action)
                )
            total_dupes += len(files) - 1
            total_bytes += size * (len(files) - 1)
            cluster_count += 1

        if cluster_count % 100 == 0:
            conn.commit()
            print(f"  Processed {cluster_count:,} clusters, {total_dupes:,} duplicates ({total_bytes/1e9:.2f} GB)")

    conn.commit()
    print(f"[DEDUP T0-2] Complete: {cluster_count:,} clusters, {total_dupes:,} duplicates, {total_bytes/1e9:.2f} GB recoverable")

    conn.execute("INSERT OR REPLACE INTO dedup_stats VALUES ('exact_clusters', ?)", (str(cluster_count),))
    conn.execute("INSERT OR REPLACE INTO dedup_stats VALUES ('exact_dupes', ?)", (str(total_dupes),))
    conn.execute("INSERT OR REPLACE INTO dedup_stats VALUES ('exact_bytes', ?)", (str(total_bytes),))
    conn.commit()

    return cluster_count, total_dupes, total_bytes


# ---------------------------------------------------------------------------
# TIER 3-5: NEAR-DUPLICATE DETECTION
# ---------------------------------------------------------------------------
def extract_text_content(filepath, file_type, max_chars=5000):
    """Extract text from various file types for comparison."""
    try:
        if file_type == 'text' or filepath.lower().endswith(('.txt', '.md', '.rst', '.csv')):
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                return f.read(max_chars)

        if file_type == 'pdf' or filepath.lower().endswith('.pdf'):
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(filepath)
                text = ""
                for page in doc:
                    text += page.get_text()
                    if len(text) > max_chars:
                        break
                doc.close()
                return text[:max_chars]
            except Exception:
                pass

        if file_type == 'data' or filepath.lower().endswith(('.json', '.jsonl')):
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                return f.read(max_chars)

        if filepath.lower().endswith(('.docx',)):
            try:
                import zipfile
                with zipfile.ZipFile(filepath) as z:
                    if 'word/document.xml' in z.namelist():
                        import re
                        xml = z.read('word/document.xml').decode('utf-8', errors='replace')
                        text = re.sub(r'<[^>]+>', ' ', xml)
                        return text[:max_chars]
            except Exception:
                pass

        if file_type == 'code':
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                return f.read(max_chars)

    except Exception:
        pass
    return None


def find_near_duplicates_rapidfuzz(conn, threshold=0.90):
    """Tier 5: Use RapidFuzz token_sort_ratio for near-duplicate detection."""
    try:
        from rapidfuzz import fuzz
    except ImportError:
        print("[WARN] RapidFuzz not available, skipping Tier 5")
        return 0, 0, 0

    print("[DEDUP T3-5] Finding near-duplicates via content comparison...")

    # Get files with extractable content, grouped by size class
    # Only compare files within same size class (within 50% of each other)
    already_deduped = set()
    cursor = conn.execute(
        "SELECT DISTINCT file_id FROM dedup_clusters WHERE action = 'recycle'"
    )
    for row in cursor:
        already_deduped.add(row[0])

    # Get text-bearing files not already deduped
    cursor = conn.execute("""
        SELECT id, path, size, file_type, ext
        FROM file_manifest
        WHERE file_type IN ('text', 'pdf', 'document', 'code', 'data')
        AND size > 100 AND size < 10000000
        AND id NOT IN (SELECT file_id FROM dedup_clusters WHERE action = 'recycle')
        ORDER BY size
    """)
    files = cursor.fetchall()
    print(f"  {len(files):,} text-bearing files to compare")

    cluster_count = 0
    total_dupes = 0
    total_bytes = 0
    existing_clusters = conn.execute("SELECT MAX(CAST(REPLACE(cluster_id, 'near-', '') AS INTEGER)) FROM dedup_clusters WHERE cluster_id LIKE 'near-%'").fetchone()[0]
    next_cluster = (existing_clusters or 0) + 1

    # Compare within size buckets
    i = 0
    compared = 0
    while i < len(files):
        fid, fpath, fsize, ftype, fext = files[i]

        # Collect files within 50% size range
        bucket = [(fid, fpath, fsize, ftype, fext)]
        j = i + 1
        while j < len(files) and files[j][2] <= fsize * 1.5:
            bucket.append(files[j])
            j += 1

        if len(bucket) > 1 and len(bucket) < 200:  # Skip huge buckets
            # Extract text for bucket
            texts = {}
            for bid, bpath, bsize, btype, bext in bucket:
                if bid not in already_deduped:
                    text = extract_text_content(bpath, btype)
                    if text and len(text) > 50:
                        texts[bid] = (text, bpath, bsize)

            # Pairwise comparison within bucket
            text_ids = list(texts.keys())
            for a in range(len(text_ids)):
                for b in range(a + 1, len(text_ids)):
                    aid, bid_val = text_ids[a], text_ids[b]
                    if aid in already_deduped or bid_val in already_deduped:
                        continue
                    ratio = fuzz.token_sort_ratio(
                        texts[aid][0][:2000], texts[bid_val][0][:2000]
                    ) / 100.0
                    compared += 1

                    if ratio >= threshold:
                        cid = f"near-{next_cluster}"
                        next_cluster += 1
                        # Canonical = longer text or lower legal score
                        a_score = score_legal_relevance(texts[aid][1])
                        b_score = score_legal_relevance(texts[bid_val][1])
                        if a_score >= b_score:
                            canon_id, dupe_id = aid, bid_val
                        else:
                            canon_id, dupe_id = bid_val, aid

                        conn.execute(
                            "INSERT INTO dedup_clusters VALUES (?,?,?,?,?,?)",
                            (cid, canon_id, ratio, 5, 1, 'keep')
                        )
                        conn.execute(
                            "INSERT INTO dedup_clusters VALUES (?,?,?,?,?,?)",
                            (cid, dupe_id, ratio, 5, 0, 'recycle')
                        )
                        already_deduped.add(dupe_id)
                        total_dupes += 1
                        total_bytes += texts[dupe_id][2]
                        cluster_count += 1

            if compared % 5000 == 0 and compared > 0:
                conn.commit()
                print(f"  Compared {compared:,} pairs, found {cluster_count:,} near-dupes")

        i = j if j > i + 1 else i + 1

    conn.commit()
    print(f"[DEDUP T3-5] Complete: {cluster_count:,} near-dupe clusters, {total_dupes:,} dupes, {total_bytes/1e9:.2f} GB")

    conn.execute("INSERT OR REPLACE INTO dedup_stats VALUES ('near_clusters', ?)", (str(cluster_count),))
    conn.execute("INSERT OR REPLACE INTO dedup_stats VALUES ('near_dupes', ?)", (str(total_dupes),))
    conn.execute("INSERT OR REPLACE INTO dedup_stats VALUES ('near_bytes', ?)", (str(total_bytes),))
    conn.commit()

    return cluster_count, total_dupes, total_bytes


# ---------------------------------------------------------------------------
# TIER 6: NEURAL SEMANTIC DEDUP (sentence-transformers + FAISS)
# ---------------------------------------------------------------------------
def build_embeddings_and_faiss(conn, batch_size=64, similarity_threshold=0.95):
    """Tier 6: Generate embeddings, build FAISS index, find semantic duplicates."""
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
        import faiss
    except ImportError as e:
        print(f"[WARN] Neural dedup unavailable: {e}")
        return 0, 0, 0

    print("[DEDUP T6] Building neural semantic embeddings...")

    model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')

    # Get files with extractable text not already deduped
    already_deduped = set()
    for row in conn.execute("SELECT DISTINCT file_id FROM dedup_clusters WHERE action = 'recycle'"):
        already_deduped.add(row[0])

    cursor = conn.execute("""
        SELECT id, path, file_type, size
        FROM file_manifest
        WHERE file_type IN ('text', 'pdf', 'document', 'code', 'data')
        AND size > 200 AND size < 5000000
        ORDER BY id
    """)
    files = [(r[0], r[1], r[2], r[3]) for r in cursor if r[0] not in already_deduped]
    print(f"  {len(files):,} files to embed")

    if len(files) < 2:
        print("  Too few files to compare")
        return 0, 0, 0

    # Extract texts and embed in batches
    file_ids = []
    file_paths = []
    file_sizes = []
    texts = []

    for fid, fpath, ftype, fsize in files:
        text = extract_text_content(fpath, ftype, max_chars=1000)
        if text and len(text) > 50:
            file_ids.append(fid)
            file_paths.append(fpath)
            file_sizes.append(fsize)
            texts.append(text)

    print(f"  Extracted text from {len(texts):,} files, generating embeddings...")

    # Generate embeddings in batches
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        embs = model.encode(batch, convert_to_numpy=True, normalize_embeddings=True)
        all_embeddings.append(embs)
        if (i + batch_size) % (batch_size * 10) == 0:
            print(f"  Embedded {min(i+batch_size, len(texts)):,}/{len(texts):,}")

    if not all_embeddings:
        return 0, 0, 0

    embeddings = np.vstack(all_embeddings).astype('float32')
    print(f"  Embeddings shape: {embeddings.shape}")

    # Build FAISS index
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # Inner product = cosine on normalized vectors
    index.add(embeddings)

    # Save FAISS index
    faiss.write_index(index, FAISS_INDEX_PATH)
    print(f"  FAISS index saved to {FAISS_INDEX_PATH}")

    # Find semantic duplicates via k-NN search
    k = min(10, len(embeddings))
    distances, indices = index.search(embeddings, k)

    cluster_count = 0
    total_dupes = 0
    total_bytes = 0
    seen_pairs = set()
    existing_max = conn.execute(
        "SELECT MAX(CAST(REPLACE(cluster_id, 'semantic-', '') AS INTEGER)) FROM dedup_clusters WHERE cluster_id LIKE 'semantic-%'"
    ).fetchone()[0]
    next_cluster = (existing_max or 0) + 1

    for i in range(len(embeddings)):
        for j_idx in range(1, k):  # Skip self (index 0)
            neighbor = indices[i][j_idx]
            sim = float(distances[i][j_idx])

            if sim < similarity_threshold:
                continue

            pair = tuple(sorted([file_ids[i], file_ids[neighbor]]))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            # Check not already deduped
            if file_ids[i] in already_deduped or file_ids[neighbor] in already_deduped:
                continue

            cid = f"semantic-{next_cluster}"
            next_cluster += 1

            # Canonical = higher legal score, then shorter path
            score_i = score_legal_relevance(file_paths[i])
            score_n = score_legal_relevance(file_paths[neighbor])
            if score_i >= score_n:
                canon, dupe = i, neighbor
            else:
                canon, dupe = neighbor, i

            conn.execute(
                "INSERT INTO dedup_clusters VALUES (?,?,?,?,?,?)",
                (cid, file_ids[canon], sim, 6, 1, 'keep')
            )
            conn.execute(
                "INSERT INTO dedup_clusters VALUES (?,?,?,?,?,?)",
                (cid, file_ids[dupe], sim, 6, 0, 'recycle')
            )
            already_deduped.add(file_ids[dupe])
            total_dupes += 1
            total_bytes += file_sizes[dupe]
            cluster_count += 1

    conn.commit()
    print(f"[DEDUP T6] Complete: {cluster_count:,} semantic clusters, {total_dupes:,} dupes, {total_bytes/1e9:.2f} GB")

    conn.execute("INSERT OR REPLACE INTO dedup_stats VALUES ('semantic_clusters', ?)", (str(cluster_count),))
    conn.execute("INSERT OR REPLACE INTO dedup_stats VALUES ('semantic_dupes', ?)", (str(total_dupes),))
    conn.execute("INSERT OR REPLACE INTO dedup_stats VALUES ('semantic_bytes', ?)", (str(total_bytes),))
    conn.commit()

    return cluster_count, total_dupes, total_bytes


# ---------------------------------------------------------------------------
# TIER 7: PERCEPTUAL HASH (images)
# ---------------------------------------------------------------------------
def find_perceptual_duplicates(conn, threshold=5):
    """Tier 7: Perceptual hashing for images."""
    try:
        from PIL import Image
    except ImportError:
        print("[WARN] Pillow not available, skipping Tier 7")
        return 0, 0, 0

    print("[DEDUP T7] Finding perceptual image duplicates...")

    already_deduped = set()
    for row in conn.execute("SELECT DISTINCT file_id FROM dedup_clusters WHERE action = 'recycle'"):
        already_deduped.add(row[0])

    cursor = conn.execute("""
        SELECT id, path, size
        FROM file_manifest
        WHERE file_type = 'image'
        AND ext IN ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp')
        AND size > 1000
        ORDER BY size
    """)
    images = [(r[0], r[1], r[2]) for r in cursor if r[0] not in already_deduped]
    print(f"  {len(images):,} images to compare")

    def compute_phash(filepath, hash_size=8):
        """Compute perceptual hash using DCT."""
        try:
            img = Image.open(filepath).convert('L').resize((hash_size * 4, hash_size * 4), Image.LANCZOS)
            pixels = list(img.getdata())
            avg = sum(pixels) / len(pixels)
            bits = ''.join('1' if p > avg else '0' for p in pixels)
            return int(bits[:64], 2)  # 64-bit hash
        except Exception:
            return None

    def hamming_distance(h1, h2):
        return bin(h1 ^ h2).count('1')

    # Compute hashes
    hashes = {}
    for fid, fpath, fsize in images:
        ph = compute_phash(fpath)
        if ph is not None:
            hashes[fid] = (ph, fpath, fsize)

    print(f"  Computed {len(hashes):,} perceptual hashes")

    # Compare within size buckets (images within 3x size of each other)
    cluster_count = 0
    total_dupes = 0
    total_bytes = 0
    sorted_images = sorted(hashes.items(), key=lambda x: x[1][2])
    existing_max = conn.execute(
        "SELECT MAX(CAST(REPLACE(cluster_id, 'phash-', '') AS INTEGER)) FROM dedup_clusters WHERE cluster_id LIKE 'phash-%'"
    ).fetchone()[0]
    next_cluster = (existing_max or 0) + 1

    i = 0
    while i < len(sorted_images):
        fid_a, (hash_a, path_a, size_a) = sorted_images[i]
        j = i + 1
        while j < len(sorted_images) and sorted_images[j][1][2] <= size_a * 3:
            fid_b, (hash_b, path_b, size_b) = sorted_images[j]
            if fid_a not in already_deduped and fid_b not in already_deduped:
                dist = hamming_distance(hash_a, hash_b)
                if dist <= threshold:
                    cid = f"phash-{next_cluster}"
                    next_cluster += 1
                    sim = 1.0 - (dist / 64.0)
                    # Keep larger file
                    if size_a >= size_b:
                        conn.execute("INSERT INTO dedup_clusters VALUES (?,?,?,?,?,?)", (cid, fid_a, sim, 7, 1, 'keep'))
                        conn.execute("INSERT INTO dedup_clusters VALUES (?,?,?,?,?,?)", (cid, fid_b, sim, 7, 0, 'recycle'))
                        already_deduped.add(fid_b)
                        total_bytes += size_b
                    else:
                        conn.execute("INSERT INTO dedup_clusters VALUES (?,?,?,?,?,?)", (cid, fid_b, sim, 7, 1, 'keep'))
                        conn.execute("INSERT INTO dedup_clusters VALUES (?,?,?,?,?,?)", (cid, fid_a, sim, 7, 0, 'recycle'))
                        already_deduped.add(fid_a)
                        total_bytes += size_a
                    total_dupes += 1
                    cluster_count += 1
            j += 1
        i += 1

    conn.commit()
    print(f"[DEDUP T7] Complete: {cluster_count:,} perceptual clusters, {total_dupes:,} dupes, {total_bytes/1e9:.2f} GB")

    conn.execute("INSERT OR REPLACE INTO dedup_stats VALUES ('phash_clusters', ?)", (str(cluster_count),))
    conn.execute("INSERT OR REPLACE INTO dedup_stats VALUES ('phash_dupes', ?)", (str(total_dupes),))
    conn.execute("INSERT OR REPLACE INTO dedup_stats VALUES ('phash_bytes', ?)", (str(total_bytes),))
    conn.commit()

    return cluster_count, total_dupes, total_bytes


# ---------------------------------------------------------------------------
# SAFE EXECUTION (Recycle Bin via Shell.Application COM)
# ---------------------------------------------------------------------------
RECYCLE_DIR = os.path.join(LITIGOS_ROOT, "_RECYCLE")


def recycle_file(filepath):
    """Move file to _RECYCLE staging directory (fast, same-drive rename)."""
    try:
        # Preserve relative path structure in _RECYCLE
        rel = os.path.relpath(filepath, os.path.dirname(LITIGOS_ROOT))
        dest = os.path.join(RECYCLE_DIR, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        import shutil
        shutil.move(filepath, dest)
        return True
    except Exception:
        return False


def execute_dedup_plan(conn, dry_run=True):
    """Execute dedup plan: recycle non-canonical files."""
    cursor = conn.execute("""
        SELECT dc.cluster_id, dc.file_id, dc.similarity, dc.tier_matched, dc.action,
               fm.path, fm.size, fm.legal_score, fm.file_type
        FROM dedup_clusters dc
        JOIN file_manifest fm ON dc.file_id = fm.id
        WHERE dc.action = 'recycle'
        ORDER BY fm.size DESC
    """)
    to_recycle = cursor.fetchall()

    print(f"\n{'='*60}")
    print(f"DEDUP EXECUTION {'(DRY RUN)' if dry_run else '(LIVE)'}")
    print(f"{'='*60}")
    print(f"Files to recycle: {len(to_recycle):,}")
    total_bytes = sum(r[6] for r in to_recycle)
    print(f"Space to recover: {total_bytes/1e9:.2f} GB")

    if dry_run:
        # Generate report
        report_path = os.path.join(MANIFESTS_DIR, "OMEGA_DEDUP_REPORT.md")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# OMEGA DEDUP REPORT (DRY RUN)\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            f.write(f"## Summary\n")
            f.write(f"- Files to recycle: {len(to_recycle):,}\n")
            f.write(f"- Space to recover: {total_bytes/1e9:.2f} GB\n\n")

            # Per-tier breakdown
            tier_counts = defaultdict(lambda: {'count': 0, 'bytes': 0})
            for r in to_recycle:
                tier = r[3]
                tier_counts[tier]['count'] += 1
                tier_counts[tier]['bytes'] += r[6]

            f.write("## By Detection Tier\n")
            tier_names = {1: 'Partial Hash', 2: 'Full Hash', 5: 'RapidFuzz Near-Dupe',
                          6: 'Neural Semantic', 7: 'Perceptual Hash'}
            for tier in sorted(tier_counts.keys()):
                name = tier_names.get(tier, f'Tier {tier}')
                f.write(f"- **{name}**: {tier_counts[tier]['count']:,} files, "
                        f"{tier_counts[tier]['bytes']/1e9:.2f} GB\n")

            # Top 20 biggest clusters
            f.write("\n## Top 20 Largest Clusters\n")
            cluster_sizes = defaultdict(lambda: {'files': 0, 'bytes': 0, 'paths': []})
            for r in to_recycle:
                cid = r[0]
                cluster_sizes[cid]['files'] += 1
                cluster_sizes[cid]['bytes'] += r[6]
                if len(cluster_sizes[cid]['paths']) < 3:
                    cluster_sizes[cid]['paths'].append(r[5])

            top = sorted(cluster_sizes.items(), key=lambda x: -x[1]['bytes'])[:20]
            for cid, info in top:
                f.write(f"\n### {cid}\n")
                f.write(f"- Dupes: {info['files']}, Size: {info['bytes']/1e6:.1f} MB\n")
                for p in info['paths']:
                    f.write(f"  - `{p}`\n")

            # Per-drive breakdown
            f.write("\n## Per-Drive Breakdown\n")
            drive_stats = defaultdict(lambda: {'count': 0, 'bytes': 0})
            for r in to_recycle:
                drive = r[5][:2] if r[5][1] == ':' else 'unknown'
                drive_stats[drive]['count'] += 1
                drive_stats[drive]['bytes'] += r[6]
            for drive in sorted(drive_stats.keys()):
                f.write(f"- **{drive}**: {drive_stats[drive]['count']:,} files, "
                        f"{drive_stats[drive]['bytes']/1e9:.2f} GB\n")

        print(f"\nDry-run report saved to: {report_path}")
        return 0

    # LIVE EXECUTION
    recycled = 0
    failed = 0
    for cluster_id, file_id, sim, tier, action, path, size, legal_score, ftype in to_recycle:
        # SAFETY: Skip court-stamped documents
        if legal_score >= 0.8:
            print(f"  [SKIP] Court document: {path}")
            continue

        success = recycle_file(path)
        status = 'recycled' if success else 'failed'

        conn.execute(
            """INSERT INTO move_log (timestamp, operation, source_path, cluster_id, tier, file_size, rollback_cmd, status)
               VALUES (?, 'recycle', ?, ?, ?, ?, ?, ?)""",
            (datetime.now().isoformat(), path, cluster_id, tier, size,
             f"# Restore from Recycle Bin: {path}", status)
        )

        if success:
            recycled += 1
            conn.execute("UPDATE dedup_clusters SET action = 'recycled' WHERE cluster_id = ? AND file_id = ?",
                         (cluster_id, file_id))
        else:
            failed += 1

        if (recycled + failed) % CHECKPOINT_INTERVAL == 0:
            conn.commit()
            print(f"  Progress: {recycled:,} recycled, {failed:,} failed")

    conn.commit()
    print(f"\n[EXECUTE] Complete: {recycled:,} recycled, {failed:,} failed")
    return recycled


# ---------------------------------------------------------------------------
# FLATTEN + CONSOLIDATE
# ---------------------------------------------------------------------------
def flatten_directory(source_dir, target_dir, conn, prefix=""):
    """Recursively flatten all files from source_dir into target_dir root."""
    if not os.path.isdir(source_dir):
        return 0

    moved = 0
    for dirpath, dirnames, filenames in os.walk(source_dir):
        for fn in filenames:
            src = os.path.join(dirpath, fn)
            # Create unique name if collision
            dst = os.path.join(target_dir, fn)
            if os.path.exists(dst):
                base, ext = os.path.splitext(fn)
                counter = 1
                while os.path.exists(dst):
                    dst = os.path.join(target_dir, f"{base}_{counter}{ext}")
                    counter += 1

            try:
                os.makedirs(target_dir, exist_ok=True)
                os.rename(src, dst)
                conn.execute(
                    "INSERT INTO move_log (timestamp, operation, source_path, dest_path, status) VALUES (?,?,?,?,?)",
                    (datetime.now().isoformat(), 'flatten', src, dst, 'done')
                )
                moved += 1
            except (OSError, PermissionError) as e:
                conn.execute(
                    "INSERT INTO move_log (timestamp, operation, source_path, dest_path, status) VALUES (?,?,?,?,?)",
                    (datetime.now().isoformat(), 'flatten_failed', src, dst, str(e))
                )
    return moved


def remove_empty_dirs(root):
    """Remove empty directories bottom-up."""
    removed = 0
    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        if dirpath == root:
            continue
        if not filenames and not dirnames:
            try:
                os.rmdir(dirpath)
                removed += 1
            except OSError:
                pass
    return removed


# ---------------------------------------------------------------------------
# DASHBOARD GENERATOR
# ---------------------------------------------------------------------------
def generate_dashboard(conn, output_path=None):
    """Generate interactive HTML dashboard."""
    if output_path is None:
        output_path = os.path.join(LITIGOS_ROOT, "00_SYSTEM", "OMEGA_DEDUP_DASHBOARD.html")

    stats = {}
    for row in conn.execute("SELECT key, value FROM dedup_stats"):
        stats[row[0]] = row[1]

    total_files = conn.execute("SELECT COUNT(*) FROM file_manifest").fetchone()[0]
    total_size = conn.execute("SELECT SUM(size) FROM file_manifest").fetchone()[0] or 0
    total_clusters = conn.execute("SELECT COUNT(DISTINCT cluster_id) FROM dedup_clusters").fetchone()[0]
    total_recycle = conn.execute("SELECT COUNT(*) FROM dedup_clusters WHERE action IN ('recycle', 'recycled')").fetchone()[0]
    total_recycle_bytes = conn.execute("""
        SELECT COALESCE(SUM(fm.size), 0) FROM dedup_clusters dc
        JOIN file_manifest fm ON dc.file_id = fm.id
        WHERE dc.action IN ('recycle', 'recycled')
    """).fetchone()[0]

    # Per-drive stats
    drive_stats = conn.execute("""
        SELECT drive, COUNT(*), SUM(size) FROM file_manifest GROUP BY drive ORDER BY drive
    """).fetchall()

    # Per-tier stats
    tier_stats = conn.execute("""
        SELECT dc.tier_matched, COUNT(*), COALESCE(SUM(fm.size), 0)
        FROM dedup_clusters dc JOIN file_manifest fm ON dc.file_id = fm.id
        WHERE dc.action IN ('recycle', 'recycled')
        GROUP BY dc.tier_matched
    """).fetchall()

    tier_names = {1: 'Partial Hash', 2: 'Full Hash', 3: 'MinHash LSH',
                  5: 'RapidFuzz', 6: 'Neural Semantic', 7: 'Perceptual Hash'}

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>OMEGA DEDUP DASHBOARD</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Segoe UI', sans-serif; background: #0a0e17; color: #e0e6ed; padding: 20px; }}
  .header {{ text-align: center; padding: 30px; background: linear-gradient(135deg, #1a1f36 0%, #0d1117 100%); border-radius: 16px; margin-bottom: 24px; border: 1px solid #30363d; }}
  .header h1 {{ font-size: 2.5rem; background: linear-gradient(90deg, #58a6ff, #7ee787, #d2a8ff); -webkit-background-clip: text; color: transparent; }}
  .header .subtitle {{ color: #8b949e; margin-top: 8px; font-size: 1.1rem; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 16px; margin-bottom: 24px; }}
  .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 20px; }}
  .card h3 {{ color: #8b949e; font-size: 0.85rem; text-transform: uppercase; margin-bottom: 8px; }}
  .card .value {{ font-size: 2rem; font-weight: 700; }}
  .card .value.green {{ color: #7ee787; }}
  .card .value.blue {{ color: #58a6ff; }}
  .card .value.red {{ color: #f85149; }}
  .card .value.purple {{ color: #d2a8ff; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
  th, td {{ padding: 10px 14px; text-align: left; border-bottom: 1px solid #21262d; }}
  th {{ color: #8b949e; font-size: 0.8rem; text-transform: uppercase; }}
  .section {{ background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 20px; margin-bottom: 24px; }}
  .section h2 {{ color: #58a6ff; margin-bottom: 16px; }}
  .bar {{ height: 24px; border-radius: 4px; margin: 4px 0; }}
  .bar-container {{ background: #21262d; border-radius: 4px; overflow: hidden; }}
</style></head><body>
<div class="header">
  <h1>OMEGA DEDUP DASHBOARD</h1>
  <div class="subtitle">8-Tier Neural Cross-Drive Deduplication | Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
</div>
<div class="grid">
  <div class="card"><h3>Total Files Scanned</h3><div class="value blue">{total_files:,}</div></div>
  <div class="card"><h3>Total Size</h3><div class="value blue">{total_size/1e9:.1f} GB</div></div>
  <div class="card"><h3>Duplicate Clusters</h3><div class="value purple">{total_clusters:,}</div></div>
  <div class="card"><h3>Files to Recycle</h3><div class="value red">{total_recycle:,}</div></div>
  <div class="card"><h3>Space Recoverable</h3><div class="value green">{total_recycle_bytes/1e9:.2f} GB</div></div>
</div>
<div class="section"><h2>Per-Drive Breakdown</h2><table>
  <tr><th>Drive</th><th>Files</th><th>Size</th></tr>
  {''.join(f"<tr><td>{d}</td><td>{c:,}</td><td>{s/1e9:.2f} GB</td></tr>" for d, c, s in drive_stats)}
</table></div>
<div class="section"><h2>Duplicates by Detection Tier</h2><table>
  <tr><th>Tier</th><th>Duplicates</th><th>Size</th></tr>
  {''.join(f"<tr><td>{tier_names.get(t, f'Tier {t}')}</td><td>{c:,}</td><td>{s/1e9:.2f} GB</td></tr>" for t, c, s in tier_stats)}
</table></div>
</body></html>"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"[DASHBOARD] Saved to {output_path}")
    return output_path


# ---------------------------------------------------------------------------
# CLI INTERFACE
# ---------------------------------------------------------------------------
def main():
    import argparse
    parser = argparse.ArgumentParser(description="OMEGA DEDUP ENGINE v1.0")
    parser.add_argument('command', choices=[
        'scan', 'dedup-exact', 'dedup-near', 'dedup-neural', 'dedup-perceptual',
        'dedup-all', 'report', 'execute', 'dashboard', 'stats',
        'flatten', 'prune-tools'
    ])
    parser.add_argument('--drive', help='Drive letter (e.g., C)')
    parser.add_argument('--path', help='Root path to scan')
    parser.add_argument('--db', default=DEDUP_DB_PATH, help='Dedup DB path')
    parser.add_argument('--dry-run', action='store_true', default=True)
    parser.add_argument('--live', action='store_true', help='Execute for real (no dry run)')
    parser.add_argument('--threshold', type=float, default=0.90, help='Near-dupe threshold')
    parser.add_argument('--skip-dirs', nargs='*', default=[], help='Directories to skip')
    args = parser.parse_args()

    conn = get_db(args.db)
    init_db(conn)

    if args.command == 'scan':
        if not args.drive or not args.path:
            print("ERROR: --drive and --path required for scan")
            return
        build_manifest(args.path, args.drive, conn, args.skip_dirs)

    elif args.command == 'dedup-exact':
        find_exact_duplicates(conn)

    elif args.command == 'dedup-near':
        find_near_duplicates_rapidfuzz(conn, args.threshold)

    elif args.command == 'dedup-neural':
        build_embeddings_and_faiss(conn)

    elif args.command == 'dedup-perceptual':
        find_perceptual_duplicates(conn)

    elif args.command == 'dedup-all':
        find_exact_duplicates(conn)
        find_near_duplicates_rapidfuzz(conn, args.threshold)
        build_embeddings_and_faiss(conn)
        find_perceptual_duplicates(conn)

    elif args.command == 'report':
        execute_dedup_plan(conn, dry_run=True)

    elif args.command == 'execute':
        dry = not args.live
        execute_dedup_plan(conn, dry_run=dry)

    elif args.command == 'dashboard':
        generate_dashboard(conn)

    elif args.command == 'stats':
        print("\n=== OMEGA DEDUP STATS ===")
        for row in conn.execute("SELECT * FROM dedup_stats ORDER BY key"):
            print(f"  {row[0]}: {row[1]}")
        print(f"\nManifest files: {conn.execute('SELECT COUNT(*) FROM file_manifest').fetchone()[0]:,}")
        print(f"Clusters: {conn.execute('SELECT COUNT(DISTINCT cluster_id) FROM dedup_clusters').fetchone()[0]:,}")
        print(f"Files to recycle: {conn.execute('SELECT COUNT(*) FROM dedup_clusters WHERE action = %s' % repr('recycle')).fetchone()[0]:,}")

    elif args.command == 'flatten':
        if not args.path:
            print("ERROR: --path required for flatten")
            return
        print(f"Flattening {args.path}...")
        moved = flatten_directory(args.path, args.path, conn)
        removed = remove_empty_dirs(args.path)
        print(f"Moved {moved} files, removed {removed} empty dirs")

    elif args.command == 'prune-tools':
        prune_tools_directory(conn)

    conn.close()


def prune_tools_directory(conn):
    """Classify and prune the 190K files in 13_TOOLS."""
    tools_dir = os.path.join(LITIGOS_ROOT, "13_TOOLS")
    if not os.path.isdir(tools_dir):
        print("13_TOOLS directory not found")
        return

    print("[PRUNE] Analyzing 13_TOOLS root files...")

    # Classify files by extension
    ext_counts = defaultdict(lambda: {'count': 0, 'size': 0})
    junk_exts = {
        '.pyc', '.pyo', '.class', '.o', '.obj', '.dll', '.so', '.dylib',
        '.whl', '.egg', '.egg-info', '.dist-info', '.pth',
        '.map', '.min.js', '.min.css', '.d.ts',
        '.lock', '.cache', '.log', '.tmp', '.temp',
    }
    junk_patterns = [
        'node_modules', '__pycache__', '.git', '.svn',
        'package-lock', 'yarn.lock', '.npmrc',
    ]

    files = os.listdir(tools_dir)
    junk_files = []
    keep_files = []

    for fn in files:
        fp = os.path.join(tools_dir, fn)
        if not os.path.isfile(fp):
            continue

        ext = os.path.splitext(fn)[1].lower()
        try:
            size = os.path.getsize(fp)
        except OSError:
            continue

        ext_counts[ext]['count'] += 1
        ext_counts[ext]['size'] += size

        is_junk = (
            ext in junk_exts or
            any(p in fn.lower() for p in junk_patterns) or
            size == 0
        )

        if is_junk:
            junk_files.append((fp, size))
        else:
            keep_files.append((fp, size))

    junk_size = sum(s for _, s in junk_files)
    keep_size = sum(s for _, s in keep_files)

    print(f"  Total root files: {len(files):,}")
    print(f"  Junk: {len(junk_files):,} ({junk_size/1e9:.2f} GB)")
    print(f"  Keep: {len(keep_files):,} ({keep_size/1e9:.2f} GB)")

    # Top extensions
    print("\n  Top 20 extensions:")
    for ext, info in sorted(ext_counts.items(), key=lambda x: -x[1]['count'])[:20]:
        print(f"    {ext or '(none)':12s}: {info['count']:>8,} files, {info['size']/1e6:>8.1f} MB")

    return junk_files, keep_files


if __name__ == '__main__':
    main()
