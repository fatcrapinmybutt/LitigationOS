#!/usr/bin/env python3
"""
LitigationOS Content-Based Deduplication Engine
Applies ai-codebase-deep-modules + agent-memory-systems patterns.
Iron Rule: peek inside documents, don't just hash.
"""
import sys, os, hashlib, sqlite3, json, time, difflib, struct
from pathlib import Path
from datetime import datetime
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DB_PATH = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")
REPORT_DIR = Path(r"C:\Users\andre\LitigationOS\05_ANALYSIS")
DEFAULT_DEDUP_DEST = Path(r"I:\_DEDUP")
DEFAULT_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt', '.md', '.xlsx', '.msg', '.eml'}
CONTENT_PEEK_LIMIT = 5000          # max chars to extract per file for comparison
HASH_BUF_SIZE = 65536              # 64 KB read chunks for hashing
NEAR_DUP_THRESHOLD = 0.90         # similarity >= this = near-duplicate
EXACT_DUP_THRESHOLD = 0.99        # similarity >= this = exact content match
PROGRESS_INTERVAL = 100            # print progress every N files

# ---------------------------------------------------------------------------
# PUBLIC INTERFACE
# ---------------------------------------------------------------------------
# dedup_scan(drives, extensions, dry_run=True, max_files=10000) -> dict
# dedup_review(report_path) -> list[dict]
# dedup_execute(report_path, move_dest) -> dict

# ---------------------------------------------------------------------------
# Module 0: Database Connection (WAL + busy_timeout per project rules)
# ---------------------------------------------------------------------------

def _get_db() -> sqlite3.Connection:
    """Open litigation_context.db with mandatory PRAGMAs."""
    conn = sqlite3.connect(str(DB_PATH), timeout=120)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_tables(conn: sqlite3.Connection) -> None:
    """Idempotently create tables/indexes the engine needs."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS content_dedup_registry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            file_name TEXT,
            file_size INTEGER,
            sha256_hash TEXT,
            content_signature TEXT,
            drive_letter TEXT,
            lane TEXT,
            duplicate_of TEXT,
            action TEXT DEFAULT 'pending',
            action_date TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_dedup_hash ON content_dedup_registry(sha256_hash)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_dedup_drive ON content_dedup_registry(drive_letter)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_dedup_action ON content_dedup_registry(action)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_dedup_path ON content_dedup_registry(file_path)")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS drive_organization_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drive_letter TEXT NOT NULL,
            action_type TEXT NOT NULL,
            source_path TEXT,
            dest_path TEXT,
            file_count INTEGER DEFAULT 0,
            bytes_moved INTEGER DEFAULT 0,
            status TEXT DEFAULT 'planned',
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()

# ---------------------------------------------------------------------------
# Module 1: Hash Scanner — fast SHA-256 screening
# ---------------------------------------------------------------------------

def _sha256(filepath: Path) -> str:
    """Compute SHA-256 hex digest for a file. Returns empty string on error."""
    h = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(HASH_BUF_SIZE)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except (OSError, PermissionError):
        return ""


def _scan_files(drives: list[str], extensions: set[str],
                max_files: int) -> list[dict]:
    """Walk drives and collect file metadata up to max_files."""
    results = []
    count = 0
    errors = 0
    for drive in drives:
        root = Path(drive)
        if not root.exists():
            print(f"  [WARN] Path not found, skipping: {drive}")
            continue
        for dirpath, _dirs, filenames in os.walk(root):
            # Skip hidden/system directories
            dp = Path(dirpath)
            parts_lower = [p.lower() for p in dp.parts]
            if any(skip in parts_lower for skip in
                   ['$recycle.bin', 'system volume information',
                    '.git', '__pycache__', 'node_modules', '_dedup']):
                continue
            for fname in filenames:
                if count >= max_files:
                    return results
                fp = dp / fname
                ext = fp.suffix.lower()
                if ext not in extensions:
                    continue
                try:
                    stat = fp.stat()
                    fsize = stat.st_size
                    if fsize == 0:
                        continue
                except (OSError, PermissionError):
                    errors += 1
                    continue
                count += 1
                if count % PROGRESS_INTERVAL == 0:
                    print(f"  [SCAN] {count:,} files indexed ({errors} errors)...")
                results.append({
                    'path': str(fp),
                    'name': fname,
                    'size': fsize,
                    'ext': ext,
                    'drive': fp.drive or str(fp.parts[0]),
                    'mtime': stat.st_mtime,
                })
    print(f"  [SCAN] Complete: {count:,} files indexed ({errors} access errors)")
    return results


def _hash_phase(file_list: list[dict]) -> dict[str, list[dict]]:
    """Compute SHA-256 for every file, group by hash. Returns groups with 2+ members."""
    print(f"\n--- Phase 1: SHA-256 hashing {len(file_list):,} files ---")
    t0 = time.time()
    hash_errors = 0
    for i, entry in enumerate(file_list):
        digest = _sha256(Path(entry['path']))
        if digest:
            entry['sha256'] = digest
        else:
            entry['sha256'] = ''
            hash_errors += 1
        if (i + 1) % PROGRESS_INTERVAL == 0:
            print(f"  [HASH] {i+1:,}/{len(file_list):,} "
                  f"({hash_errors} errors, "
                  f"{time.time()-t0:.1f}s elapsed)")

    elapsed = time.time() - t0
    print(f"  [HASH] Complete in {elapsed:.1f}s ({hash_errors} errors)")

    # Group by hash — only keep groups with duplicates
    groups: dict[str, list[dict]] = {}
    for entry in file_list:
        h = entry['sha256']
        if not h:
            continue
        groups.setdefault(h, []).append(entry)
    dup_groups = {h: members for h, members in groups.items() if len(members) >= 2}
    total_dups = sum(len(m) for m in dup_groups.values())
    print(f"  [HASH] Found {len(dup_groups):,} hash groups "
          f"containing {total_dups:,} files")
    return dup_groups

# ---------------------------------------------------------------------------
# Module 2: Content Peeker — open files and extract text
# ---------------------------------------------------------------------------

def _peek_pdf(filepath: Path) -> str:
    """Extract text from first 3 pages of a PDF."""
    # Try PyMuPDF first (best quality)
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(filepath))
        pages = min(3, len(doc))
        text = ""
        for i in range(pages):
            text += doc[i].get_text()
            if len(text) >= CONTENT_PEEK_LIMIT:
                break
        doc.close()
        return text[:CONTENT_PEEK_LIMIT]
    except ImportError:
        pass
    except Exception:
        pass

    # Fallback: extract ASCII strings from raw bytes
    try:
        with open(filepath, 'rb') as f:
            raw = f.read(min(200_000, filepath.stat().st_size))
        # Extract printable ASCII runs of 4+ characters
        chunks = []
        current = []
        for byte in raw:
            if 32 <= byte < 127:
                current.append(chr(byte))
            else:
                if len(current) >= 4:
                    chunks.append(''.join(current))
                current = []
        if len(current) >= 4:
            chunks.append(''.join(current))
        text = ' '.join(chunks)
        return text[:CONTENT_PEEK_LIMIT]
    except (OSError, PermissionError):
        return ""


def _peek_docx(filepath: Path) -> str:
    """Extract text from a DOCX by reading word/document.xml from its zip."""
    import zipfile
    import re
    try:
        with zipfile.ZipFile(str(filepath), 'r') as z:
            if 'word/document.xml' not in z.namelist():
                return ""
            xml_bytes = z.read('word/document.xml')
            xml_text = xml_bytes.decode('utf-8', errors='replace')
            # Strip XML tags, keep text content
            clean = re.sub(r'<[^>]+>', ' ', xml_text)
            clean = re.sub(r'\s+', ' ', clean).strip()
            return clean[:CONTENT_PEEK_LIMIT]
    except (zipfile.BadZipFile, KeyError, OSError, PermissionError):
        return ""


def _peek_text(filepath: Path) -> str:
    """Read first CONTENT_PEEK_LIMIT chars from a text file."""
    encodings = ['utf-8', 'latin-1', 'cp1252']
    for enc in encodings:
        try:
            with open(filepath, 'r', encoding=enc, errors='replace') as f:
                return f.read(CONTENT_PEEK_LIMIT)
        except (OSError, PermissionError):
            return ""
        except UnicodeDecodeError:
            continue
    return ""


def _peek_xlsx(filepath: Path) -> str:
    """Extract header row and first few rows from an xlsx file."""
    # Try openpyxl
    try:
        import openpyxl
        wb = openpyxl.load_workbook(str(filepath), read_only=True, data_only=True)
        ws = wb.active
        rows = []
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i >= 10:
                break
            rows.append(' '.join(str(c) for c in row if c is not None))
        wb.close()
        return '\n'.join(rows)[:CONTENT_PEEK_LIMIT]
    except ImportError:
        pass
    except Exception:
        pass

    # Fallback: treat as zip, read sharedStrings.xml
    import zipfile
    import re
    try:
        with zipfile.ZipFile(str(filepath), 'r') as z:
            if 'xl/sharedStrings.xml' in z.namelist():
                xml_bytes = z.read('xl/sharedStrings.xml')
                xml_text = xml_bytes.decode('utf-8', errors='replace')
                clean = re.sub(r'<[^>]+>', ' ', xml_text)
                clean = re.sub(r'\s+', ' ', clean).strip()
                return clean[:CONTENT_PEEK_LIMIT]
    except (zipfile.BadZipFile, OSError, PermissionError):
        pass
    return ""


def _peek_raw(filepath: Path) -> str:
    """Read first 4096 bytes and decode as text."""
    try:
        with open(filepath, 'rb') as f:
            raw = f.read(4096)
        return raw.decode('utf-8', errors='replace')
    except (OSError, PermissionError):
        return ""


def _peek_content(filepath: Path, ext: str) -> str:
    """Dispatch to the correct content peeker based on file extension."""
    if ext == '.pdf':
        return _peek_pdf(filepath)
    elif ext in ('.docx',):
        return _peek_docx(filepath)
    elif ext in ('.txt', '.md', '.eml', '.msg'):
        return _peek_text(filepath)
    elif ext in ('.xlsx',):
        return _peek_xlsx(filepath)
    elif ext in ('.doc',):
        # Legacy .doc — try raw bytes extraction
        return _peek_raw(filepath)
    else:
        return _peek_raw(filepath)

# ---------------------------------------------------------------------------
# Module 2b: Name + Size Matcher (dead-giveaway duplicate detection)
# ---------------------------------------------------------------------------

def _name_size_match(file_list: list[dict]) -> list[dict]:
    """Detect files with similar names AND exact same sizes — dead giveaway
    for duplicates even when hashes differ (e.g., metadata-only changes).

    Groups by (normalized_name, file_size) to find copies across drives.
    Returns list of match groups for content verification.
    """
    import re
    print(f"\n--- Phase 1b: Name + Size matching on {len(file_list):,} files ---")
    t0 = time.time()

    def _normalize_name(name: str) -> str:
        """Normalize filename: strip version suffixes, copy markers, etc."""
        stem, ext = os.path.splitext(name.lower())
        # Remove common copy/version patterns
        stem = re.sub(r'[\s_-]*\(?\d+\)?$', '', stem)       # trailing (1), _2, etc.
        stem = re.sub(r'[\s_-]*copy[\s_-]*\d*', '', stem)    # "copy", "copy 2"
        stem = re.sub(r'[\s_-]*v\d+[\.\d]*$', '', stem)      # v2, v3.1
        stem = re.sub(r'[\s_-]*final[\s_-]*\d*', '', stem)    # "final", "final2"
        stem = re.sub(r'[\s_-]*draft[\s_-]*\d*', '', stem)    # "draft", "draft3"
        stem = re.sub(r'[\s_-]*backup[\s_-]*\d*', '', stem)   # "backup"
        stem = re.sub(r'[\s_-]*old$', '', stem)               # "old"
        stem = re.sub(r'[\s_-]+', '_', stem.strip())          # collapse whitespace
        return stem + ext

    # Group by (normalized_name, size)
    groups: dict[tuple[str, int], list[dict]] = {}
    for entry in file_list:
        key = (_normalize_name(entry['name']), entry['size'])
        groups.setdefault(key, []).append(entry)

    # Filter to groups with 2+ members from different paths
    match_groups = {}
    for key, members in groups.items():
        if len(members) < 2:
            continue
        # Ensure they're actually from different locations (not same dir)
        dirs = set(os.path.dirname(m['path']) for m in members)
        if len(dirs) >= 2:
            match_groups[key] = members

    total_matches = sum(len(m) for m in match_groups.values())
    elapsed = time.time() - t0
    print(f"  [NAME+SIZE] Found {len(match_groups):,} groups "
          f"({total_matches:,} files) in {elapsed:.1f}s")

    return match_groups


def _folder_size_match(drives: list[str]) -> list[dict]:
    """Detect folders with identical total sizes — dead giveaway for
    cloned directory trees across drives.

    Returns list of folder-pair matches with size details.
    """
    print(f"\n--- Phase 1c: Folder size matching across {len(drives)} drives ---")
    t0 = time.time()

    folder_sizes: dict[str, dict] = {}  # normalized_name -> {path, size, file_count}

    for drive in drives:
        root = Path(drive)
        if not root.exists():
            continue
        for dirpath, subdirs, filenames in os.walk(root):
            dp = Path(dirpath)
            parts_lower = [p.lower() for p in dp.parts]
            if any(skip in parts_lower for skip in
                   ['$recycle.bin', 'system volume information',
                    '.git', '__pycache__', 'node_modules', '_dedup']):
                subdirs.clear()
                continue
            # Only measure leaf-ish dirs (dirs with files)
            if not filenames:
                continue
            try:
                total_size = 0
                file_count = 0
                for fn in filenames:
                    fp = dp / fn
                    try:
                        total_size += fp.stat().st_size
                        file_count += 1
                    except (OSError, PermissionError):
                        pass
                if total_size == 0:
                    continue
                dir_name = dp.name.lower()
                key = (dir_name, total_size, file_count)
                folder_sizes.setdefault(key, []).append({
                    'path': str(dp),
                    'name': dp.name,
                    'total_size': total_size,
                    'file_count': file_count,
                    'drive': dp.drive or str(dp.parts[0]),
                })
            except (OSError, PermissionError):
                continue

    # Filter to groups from different drives with matching sizes
    dup_folders = []
    for key, folders in folder_sizes.items():
        if len(folders) < 2:
            continue
        drives_seen = set(f['drive'] for f in folders)
        if len(drives_seen) >= 2:
            dup_folders.append({
                'folder_name': key[0],
                'total_size': key[1],
                'file_count': key[2],
                'locations': folders,
                'location_count': len(folders),
            })

    elapsed = time.time() - t0
    total_dup_folders = sum(d['location_count'] for d in dup_folders)
    space_wasted = sum(d['total_size'] * (d['location_count'] - 1)
                       for d in dup_folders)
    print(f"  [FOLDER] Found {len(dup_folders):,} duplicate folder groups "
          f"({total_dup_folders:,} folders, {_fmt_bytes(space_wasted)} wasted) "
          f"in {elapsed:.1f}s")
    return dup_folders


# ---------------------------------------------------------------------------
# Module 3: Similarity Scorer
# ---------------------------------------------------------------------------

def score_similarity(text_a: str, text_b: str) -> float:
    """Content-based similarity using SequenceMatcher. Returns 0.0-1.0."""
    if not text_a or not text_b:
        return 0.0
    # Normalize whitespace
    text_a = ' '.join(text_a.split())[:CONTENT_PEEK_LIMIT]
    text_b = ' '.join(text_b.split())[:CONTENT_PEEK_LIMIT]
    if text_a == text_b:
        return 1.0
    return difflib.SequenceMatcher(None, text_a, text_b).ratio()

# ---------------------------------------------------------------------------
# Module 4: Content Verification Phase
# ---------------------------------------------------------------------------

def _content_verify(dup_groups: dict[str, list[dict]]) -> list[dict]:
    """For each hash-duplicate group, peek inside and score similarity.

    Returns a flat list of verified duplicate pairs with similarity scores.
    """
    print(f"\n--- Phase 2: Content verification on {len(dup_groups):,} groups ---")
    t0 = time.time()
    pairs = []
    groups_done = 0

    for hash_val, members in dup_groups.items():
        groups_done += 1
        if groups_done % 50 == 0:
            print(f"  [PEEK] {groups_done:,}/{len(dup_groups):,} groups verified "
                  f"({time.time()-t0:.1f}s)")

        # Extract content for each member
        contents = []
        for m in members:
            fp = Path(m['path'])
            text = _peek_content(fp, m['ext'])
            contents.append(text)
            m['content_preview'] = text[:200]  # store short preview

        # Compare first file (candidate original) against all others
        # Pick oldest file as the "original" candidate
        members_sorted = sorted(members, key=lambda x: x['mtime'])
        original = members_sorted[0]
        original_text = contents[members.index(original)]

        for other in members_sorted[1:]:
            other_text = contents[members.index(other)]
            sim = score_similarity(original_text, other_text)

            # Classify the relationship
            if sim >= EXACT_DUP_THRESHOLD:
                action = 'exact_dup'
            elif sim >= NEAR_DUP_THRESHOLD:
                action = 'near_dup'
            elif not original_text and not other_text:
                action = 'review_needed'   # couldn't read either file
            else:
                action = 'unique'           # same hash but different extracted content

            pairs.append({
                'original_path': original['path'],
                'duplicate_path': other['path'],
                'sha256': hash_val,
                'original_size': original['size'],
                'duplicate_size': other['size'],
                'similarity': round(sim, 4),
                'action': action,
                'original_preview': original.get('content_preview', ''),
                'duplicate_preview': other.get('content_preview', ''),
            })

    elapsed = time.time() - t0
    exact = sum(1 for p in pairs if p['action'] == 'exact_dup')
    near = sum(1 for p in pairs if p['action'] == 'near_dup')
    unique = sum(1 for p in pairs if p['action'] == 'unique')
    review = sum(1 for p in pairs if p['action'] == 'review_needed')
    print(f"  [PEEK] Complete in {elapsed:.1f}s: "
          f"{exact} exact, {near} near-dup, {unique} unique, {review} review-needed")
    return pairs

# ---------------------------------------------------------------------------
# Module 5: DB Logger
# ---------------------------------------------------------------------------

def _log_to_db(file_list: list[dict], pairs: list[dict],
               conn: sqlite3.Connection) -> None:
    """Write scan results to content_dedup_registry."""
    print(f"\n--- Phase 3: Logging {len(file_list):,} files + "
          f"{len(pairs):,} pairs to DB ---")
    t0 = time.time()

    # Build a lookup for duplicate_of relationships
    dup_map: dict[str, tuple[str, str]] = {}  # path -> (original_path, action)
    for p in pairs:
        dup_map[p['duplicate_path']] = (p['original_path'], p['action'])

    # Upsert each file
    inserted = 0
    for entry in file_list:
        path = entry['path']
        dup_info = dup_map.get(path)
        duplicate_of = dup_info[0] if dup_info else None
        action = dup_info[1] if dup_info else 'unique'
        sig = entry.get('content_preview', '')

        # Check if path already registered
        existing = conn.execute(
            "SELECT id FROM content_dedup_registry WHERE file_path = ?",
            (path,)
        ).fetchone()

        if existing:
            conn.execute("""
                UPDATE content_dedup_registry
                SET sha256_hash = ?, content_signature = ?,
                    duplicate_of = ?, action = ?, action_date = ?
                WHERE file_path = ?
            """, (entry.get('sha256', ''), sig, duplicate_of, action,
                  datetime.now().isoformat(), path))
        else:
            conn.execute("""
                INSERT INTO content_dedup_registry
                    (file_path, file_name, file_size, sha256_hash,
                     content_signature, drive_letter, duplicate_of,
                     action, action_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (path, entry['name'], entry['size'],
                  entry.get('sha256', ''), sig,
                  entry.get('drive', ''), duplicate_of, action,
                  datetime.now().isoformat()))
            inserted += 1

    conn.commit()
    print(f"  [DB] Logged in {time.time()-t0:.1f}s "
          f"({inserted} new, {len(file_list)-inserted} updated)")

# ---------------------------------------------------------------------------
# Module 6: Report Generator
# ---------------------------------------------------------------------------

def _generate_report(file_list: list[dict], dup_groups: dict[str, list[dict]],
                     pairs: list[dict], report_path: Path,
                     dry_run: bool, folder_matches: list[dict] = None) -> dict:
    """Generate a markdown dedup report and return summary dict."""
    exact_pairs = [p for p in pairs if p['action'] == 'exact_dup']
    near_pairs = [p for p in pairs if p['action'] == 'near_dup']
    review_pairs = [p for p in pairs if p['action'] == 'review_needed']
    unique_pairs = [p for p in pairs if p['action'] == 'unique']

    space_exact = sum(p['duplicate_size'] for p in exact_pairs)
    space_near = sum(p['duplicate_size'] for p in near_pairs)

    summary = {
        'timestamp': datetime.now().isoformat(),
        'total_files_scanned': len(file_list),
        'hash_groups_found': len(dup_groups),
        'total_candidate_pairs': len(pairs),
        'exact_duplicates': len(exact_pairs),
        'near_duplicates': len(near_pairs),
        'review_needed': len(review_pairs),
        'false_positives': len(unique_pairs),
        'space_recoverable_exact_bytes': space_exact,
        'space_recoverable_near_bytes': space_near,
        'dry_run': dry_run,
    }

    # Write markdown report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# LitigationOS Content Deduplication Report\n\n")
        f.write(f"**Generated:** {summary['timestamp']}\n")
        f.write(f"**Mode:** {'DRY RUN' if dry_run else 'EXECUTE'}\n\n")
        f.write("## Summary\n\n")
        f.write(f"| Metric | Value |\n|--------|-------|\n")
        f.write(f"| Files Scanned | {summary['total_files_scanned']:,} |\n")
        f.write(f"| Hash Groups | {summary['hash_groups_found']:,} |\n")
        f.write(f"| Content-Verified Exact Duplicates | {summary['exact_duplicates']:,} |\n")
        f.write(f"| Near-Duplicates (≥{NEAR_DUP_THRESHOLD}) | {summary['near_duplicates']:,} |\n")
        f.write(f"| Review Needed (unreadable) | {summary['review_needed']:,} |\n")
        f.write(f"| False Positives (same hash, different content) | {summary['false_positives']:,} |\n")
        f.write(f"| Space Recoverable (exact) | {_fmt_bytes(space_exact)} |\n")
        f.write(f"| Space Recoverable (near) | {_fmt_bytes(space_near)} |\n\n")

        if exact_pairs:
            f.write("## Exact Duplicates\n\n")
            for i, p in enumerate(exact_pairs[:100], 1):
                f.write(f"### Group {i} (similarity: {p['similarity']:.2%})\n")
                f.write(f"- **Original:** `{p['original_path']}` "
                        f"({_fmt_bytes(p['original_size'])})\n")
                f.write(f"- **Duplicate:** `{p['duplicate_path']}` "
                        f"({_fmt_bytes(p['duplicate_size'])})\n")
                f.write(f"- SHA-256: `{p['sha256'][:16]}...`\n\n")
            if len(exact_pairs) > 100:
                f.write(f"*... and {len(exact_pairs) - 100} more exact duplicates*\n\n")

        if near_pairs:
            f.write("## Near-Duplicates\n\n")
            for i, p in enumerate(near_pairs[:50], 1):
                f.write(f"### Pair {i} (similarity: {p['similarity']:.2%})\n")
                f.write(f"- **File A:** `{p['original_path']}`\n")
                f.write(f"- **File B:** `{p['duplicate_path']}`\n")
                f.write(f"- SHA-256: `{p['sha256'][:16]}...`\n\n")
            if len(near_pairs) > 50:
                f.write(f"*... and {len(near_pairs) - 50} more near-duplicates*\n\n")

        if review_pairs:
            f.write("## Needs Manual Review\n\n")
            for p in review_pairs[:25]:
                f.write(f"- `{p['duplicate_path']}` ↔ `{p['original_path']}`\n")
            f.write("\n")

        # Folder size matches
        if folder_matches:
            f.write("## Duplicate Folders (Same Name + Size + File Count)\n\n")
            f.write("These folders have identical names, total sizes, and file counts "
                    "across different drives — a dead giveaway for cloned directories.\n\n")
            sorted_fm = sorted(folder_matches,
                               key=lambda x: x['total_size'] * (x['location_count'] - 1),
                               reverse=True)
            for i, fm in enumerate(sorted_fm[:50], 1):
                wasted = fm['total_size'] * (fm['location_count'] - 1)
                f.write(f"### Folder Group {i}: `{fm['folder_name']}` "
                        f"({_fmt_bytes(fm['total_size'])}, "
                        f"{fm['file_count']} files, "
                        f"{fm['location_count']} copies → "
                        f"{_fmt_bytes(wasted)} wasted)\n")
                for loc in fm['locations']:
                    f.write(f"- `{loc['path']}` [{loc['drive']}]\n")
                f.write("\n")
            if len(sorted_fm) > 50:
                f.write(f"*... and {len(sorted_fm) - 50} more folder groups*\n\n")
            total_folder_waste = sum(
                d['total_size'] * (d['location_count'] - 1) for d in folder_matches)
            f.write(f"**Total folder duplication waste: "
                    f"{_fmt_bytes(total_folder_waste)}**\n\n")
            summary['duplicate_folders'] = len(folder_matches)
            summary['folder_waste_bytes'] = total_folder_waste

    print(f"  [REPORT] Written to {report_path}")
    return summary


def _fmt_bytes(n: int) -> str:
    """Format byte count as human-readable string."""
    if n < 1024:
        return f"{n} B"
    elif n < 1024 ** 2:
        return f"{n / 1024:.1f} KB"
    elif n < 1024 ** 3:
        return f"{n / 1024**2:.1f} MB"
    else:
        return f"{n / 1024**3:.2f} GB"

# ---------------------------------------------------------------------------
# Module 7: Executor — move duplicates (NEVER delete)
# ---------------------------------------------------------------------------

def _execute_moves(pairs: list[dict], move_dest: Path,
                   conn: sqlite3.Connection) -> dict:
    """Move confirmed duplicates to move_dest. Returns execution stats."""
    import shutil
    date_folder = move_dest / datetime.now().strftime("%Y-%m-%d")
    date_folder.mkdir(parents=True, exist_ok=True)

    movable = [p for p in pairs if p['action'] in ('exact_dup', 'near_dup')]
    print(f"\n--- Executing moves: {len(movable):,} files → {date_folder} ---")

    moved = 0
    failed = 0
    bytes_moved = 0

    for p in movable:
        src = Path(p['duplicate_path'])
        if not src.exists():
            failed += 1
            continue
        # Preserve relative structure under date folder
        dest_name = src.name
        dest_file = date_folder / dest_name
        # Handle name collisions
        counter = 1
        while dest_file.exists():
            stem = src.stem
            dest_file = date_folder / f"{stem}_dup{counter}{src.suffix}"
            counter += 1
        try:
            shutil.move(str(src), str(dest_file))
            bytes_moved += p['duplicate_size']
            moved += 1

            # Update DB
            conn.execute("""
                UPDATE content_dedup_registry
                SET action = 'moved', action_date = ?
                WHERE file_path = ?
            """, (datetime.now().isoformat(), p['duplicate_path']))

            # Log the move
            conn.execute("""
                INSERT INTO drive_organization_log
                    (drive_letter, action_type, source_path, dest_path,
                     file_count, bytes_moved, status, notes)
                VALUES (?, 'dedup_move', ?, ?, 1, ?, 'completed',
                        'Content-verified duplicate moved by dedup engine')
            """, (src.drive or str(src.parts[0]),
                  str(src), str(dest_file), p['duplicate_size']))

        except (OSError, PermissionError, shutil.Error) as e:
            failed += 1
            print(f"  [MOVE] FAILED: {src} -> {e}")

    conn.commit()
    print(f"  [MOVE] Done: {moved:,} moved, {failed:,} failed, "
          f"{_fmt_bytes(bytes_moved)} freed")
    return {'moved': moved, 'failed': failed, 'bytes_moved': bytes_moved}

# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------

def dedup_scan(drives: list[str], extensions: list[str] | None = None,
               dry_run: bool = True, max_files: int = 10000,
               report_path: str | None = None) -> dict:
    """Run the full content-based deduplication scan.

    Args:
        drives: List of root paths to scan.
        extensions: File extensions to include (with dot).
        dry_run: If True (default), only report — don't move files.
        max_files: Maximum number of files to index.
        report_path: Override path for the markdown report.

    Returns:
        Summary dict with scan statistics.
    """
    ext_set = set(extensions) if extensions else DEFAULT_EXTENSIONS
    rpath = Path(report_path) if report_path else (REPORT_DIR / "DEDUP_REPORT.md")

    print("=" * 60)
    print("  LitigationOS Content-Based Deduplication Engine")
    print(f"  Mode: {'DRY RUN' if dry_run else 'EXECUTE (will move files)'}")
    print(f"  Drives: {drives}")
    print(f"  Extensions: {sorted(ext_set)}")
    print(f"  Max files: {max_files:,}")
    print("=" * 60)

    # Phase 0: DB setup
    conn = _get_db()
    _ensure_tables(conn)

    # Phase 1: Scan & hash
    file_list = _scan_files(drives, ext_set, max_files)
    if not file_list:
        print("\n  No files found. Check drives/extensions.")
        conn.close()
        return {'total_files_scanned': 0, 'error': 'no_files'}

    dup_groups = _hash_phase(file_list)

    # Phase 1b: Name + Size matching (catches copies with metadata changes)
    name_size_groups = _name_size_match(file_list)

    # Merge name+size matches into dup_groups for content verification
    # (only add groups not already caught by hash matching)
    hashed_paths = set()
    for members in dup_groups.values():
        for m in members:
            hashed_paths.add(m['path'])

    ns_extra = 0
    for key, members in name_size_groups.items():
        member_paths = set(m['path'] for m in members)
        if not member_paths.issubset(hashed_paths):
            # These weren't caught by hash — use a synthetic key
            synth_key = f"ns_{key[0]}_{key[1]}"
            if synth_key not in dup_groups:
                dup_groups[synth_key] = members
                ns_extra += 1
    if ns_extra:
        print(f"  [NAME+SIZE] Added {ns_extra} extra groups for content verification")

    # Phase 1c: Folder size matching
    dup_folders = _folder_size_match(drives)
    # Store folder matches in summary for report
    folder_match_data = dup_folders

    # Phase 2: Content verification
    pairs = _content_verify(dup_groups) if dup_groups else []

    # Phase 3: Log to DB
    _log_to_db(file_list, pairs, conn)

    # Phase 4: Generate report (includes folder matches)
    summary = _generate_report(file_list, dup_groups, pairs, rpath, dry_run,
                               folder_matches=folder_match_data)

    # Phase 5: Execute (if not dry run)
    if not dry_run and pairs:
        exec_stats = _execute_moves(pairs, DEFAULT_DEDUP_DEST, conn)
        summary['execution'] = exec_stats

    conn.close()

    print(f"\n{'=' * 60}")
    print(f"  SCAN COMPLETE")
    print(f"  Files: {summary['total_files_scanned']:,}")
    print(f"  Exact dups: {summary['exact_duplicates']:,}")
    print(f"  Near dups: {summary['near_duplicates']:,}")
    print(f"  Space recoverable: {_fmt_bytes(summary['space_recoverable_exact_bytes'])}")
    print(f"  Report: {rpath}")
    print(f"{'=' * 60}")
    return summary


def dedup_review(report_path: str) -> list[dict]:
    """Load a dedup report and return duplicate pairs from the DB.

    Args:
        report_path: Path to a previously generated DEDUP_REPORT.md.

    Returns:
        List of duplicate pair dicts from the database.
    """
    conn = _get_db()
    rows = conn.execute("""
        SELECT file_path, file_name, file_size, sha256_hash,
               duplicate_of, action, content_signature
        FROM content_dedup_registry
        WHERE action IN ('exact_dup', 'near_dup', 'review_needed')
        ORDER BY sha256_hash, action
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def dedup_execute(report_path: str,
                  move_dest: str = r"I:\_DEDUP") -> dict:
    """Execute dedup moves for previously-scanned duplicates.

    Args:
        report_path: Path to the report (used for context/logging).
        move_dest: Destination root for moved duplicates.

    Returns:
        Execution statistics dict.
    """
    conn = _get_db()
    rows = conn.execute("""
        SELECT r1.file_path as duplicate_path,
               r1.duplicate_of as original_path,
               r1.file_size as duplicate_size,
               r1.sha256_hash as sha256,
               r1.action
        FROM content_dedup_registry r1
        WHERE r1.action IN ('exact_dup', 'near_dup')
          AND r1.duplicate_of IS NOT NULL
    """).fetchall()

    pairs = [dict(r) for r in rows]
    # Set similarity to 1.0 for exact, 0.95 for near
    for p in pairs:
        p['similarity'] = 1.0 if p['action'] == 'exact_dup' else 0.95

    result = _execute_moves(pairs, Path(move_dest), conn)
    conn.close()
    return result


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description='LitigationOS Content-Based Deduplication Engine')
    parser.add_argument('--drives', nargs='+',
                        default=[r'C:\Users\andre\LitigationOS'],
                        help='Drives/paths to scan')
    parser.add_argument('--extensions', nargs='+',
                        default=['.pdf', '.docx', '.doc', '.txt', '.md'],
                        help='File extensions to include')
    parser.add_argument('--execute', action='store_true',
                        help='Actually move duplicates (default: dry run)')
    parser.add_argument('--max-files', type=int, default=10000,
                        help='Max files to scan')
    parser.add_argument('--report', default=None,
                        help='Path for report output')
    parser.add_argument('--folders-only', action='store_true',
                        help='Only run folder-size matching (fast)')
    parser.add_argument('--target', default=None,
                        help='Single file/folder to find duplicates of (context menu mode)')
    args = parser.parse_args()

    if args.target:
        # Context menu mode — find all duplicates of a specific file or folder
        target = Path(args.target)
        if not target.exists():
            print(f"ERROR: Target not found: {args.target}")
            sys.exit(1)

        print(f"Finding duplicates of: {target}")
        all_drives = [r'C:\Users\andre\LitigationOS', r'D:\\', r'F:\\',
                      r'G:\\', r'H:\\', r'I:\\']

        if target.is_file():
            # Single file mode: find by name + size
            t_name = target.name.lower()
            t_size = target.stat().st_size
            t_hash = _sha256(target)
            t_text = _peek_content(target, target.suffix.lower())

            print(f"  Name: {t_name}")
            print(f"  Size: {_fmt_bytes(t_size)}")
            print(f"  SHA-256: {t_hash[:16]}...")
            print(f"\nSearching all drives...")

            matches = []
            for drive in all_drives:
                root = Path(drive)
                if not root.exists():
                    continue
                for dirpath, _dirs, filenames in os.walk(root):
                    dp = Path(dirpath)
                    parts_lower = [p.lower() for p in dp.parts]
                    if any(skip in parts_lower for skip in
                           ['$recycle.bin', 'system volume information',
                            '.git', '__pycache__', 'node_modules', '_dedup']):
                        continue
                    for fn in filenames:
                        fp = dp / fn
                        if str(fp).lower() == str(target).lower():
                            continue  # skip self
                        try:
                            st = fp.stat()
                        except (OSError, PermissionError):
                            continue
                        # Match by name similarity + exact size
                        name_match = (fn.lower() == t_name or
                                      fn.lower().replace(' ', '_') == t_name.replace(' ', '_'))
                        size_match = st.st_size == t_size
                        if name_match and size_match:
                            # Verify with hash
                            h = _sha256(fp)
                            sim = 0.0
                            if h == t_hash:
                                sim = 1.0
                            elif t_text:
                                other_text = _peek_content(fp, fp.suffix.lower())
                                sim = score_similarity(t_text, other_text)
                            matches.append({
                                'path': str(fp),
                                'size': st.st_size,
                                'hash_match': h == t_hash,
                                'similarity': sim,
                                'drive': fp.drive,
                            })

            print(f"\n{'='*60}")
            print(f"  DUPLICATES OF: {target.name}")
            print(f"{'='*60}")
            if matches:
                for m in sorted(matches, key=lambda x: -x['similarity']):
                    tag = "EXACT" if m['hash_match'] else f"SIM:{m['similarity']:.0%}"
                    print(f"  [{tag}] {m['path']} ({_fmt_bytes(m['size'])})")
                print(f"\nFound {len(matches)} duplicate(s)")
            else:
                print("  No duplicates found across any drive.")

        elif target.is_dir():
            # Folder mode: find by name + total size + file count
            t_files = list(target.rglob('*'))
            t_file_count = sum(1 for f in t_files if f.is_file())
            t_total_size = sum(f.stat().st_size for f in t_files
                               if f.is_file())
            print(f"  Files: {t_file_count}, Total size: {_fmt_bytes(t_total_size)}")
            print(f"\nSearching for matching folders...")

            folder_matches = _folder_size_match(all_drives)
            t_name_lower = target.name.lower()
            hits = [fm for fm in folder_matches
                    if fm['folder_name'] == t_name_lower]

            print(f"\n{'='*60}")
            print(f"  FOLDER DUPLICATES OF: {target.name}")
            print(f"{'='*60}")
            if hits:
                for fm in hits:
                    for loc in fm['locations']:
                        if loc['path'].lower() != str(target).lower():
                            print(f"  {loc['path']} "
                                  f"({_fmt_bytes(loc['total_size'])}, "
                                  f"{loc['file_count']} files)")
            else:
                print("  No matching folders found.")

    elif args.folders_only:
        # Fast folder-only scan
        dup_folders = _folder_size_match(args.drives)
        rpath = Path(args.report) if args.report else (
            REPORT_DIR / "FOLDER_DEDUP_REPORT.md")
        rpath.parent.mkdir(parents=True, exist_ok=True)
        with open(rpath, 'w', encoding='utf-8') as f:
            f.write("# LitigationOS Folder Deduplication Report\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n")
            f.write(f"**Drives scanned:** {args.drives}\n\n")
            total_waste = sum(d['total_size'] * (d['location_count'] - 1)
                              for d in dup_folders)
            f.write(f"**Duplicate folder groups:** {len(dup_folders)}\n")
            f.write(f"**Total wasted space:** {_fmt_bytes(total_waste)}\n\n")
            for i, fm in enumerate(
                sorted(dup_folders,
                       key=lambda x: x['total_size'] * (x['location_count'] - 1),
                       reverse=True)[:100], 1):
                wasted = fm['total_size'] * (fm['location_count'] - 1)
                f.write(f"## {i}. `{fm['folder_name']}` — "
                        f"{_fmt_bytes(wasted)} wasted\n")
                for loc in fm['locations']:
                    f.write(f"- `{loc['path']}` ({loc['file_count']} files)\n")
                f.write("\n")
        print(f"Report saved: {rpath}")
        print(json.dumps({
            'duplicate_folders': len(dup_folders),
            'total_waste_bytes': total_waste
        }, indent=2))

    else:
        report = dedup_scan(
            args.drives, args.extensions,
            dry_run=not args.execute,
            max_files=args.max_files,
            report_path=args.report,
        )
        print(json.dumps(report, indent=2, default=str))
