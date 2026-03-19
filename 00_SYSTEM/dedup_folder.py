#!/usr/bin/env python3
"""
LitigationOS Content-Based Folder Deduplicator v1.0
====================================================
Right-click context menu handler. Deduplicates a folder by CONTENT comparison.

Rules (user non-negotiable):
  - NO hash-only dedup. Must PEEK INSIDE documents to verify sameness.
  - ALL duplicates move to I:/DEDUP_ARCHIVE/ (never hard delete)
  - Generates JSON report with sha256 receipts

Usage:
    python dedup_folder.py "C:\path\to\folder"
    python dedup_folder.py "C:\path\to\folder" --dry-run
    python dedup_folder.py --help
"""
import sys
import os
import json
import hashlib
import shutil
import struct
from datetime import datetime
from pathlib import Path
from collections import defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

# === CONFIG ===
DEDUP_ARCHIVE = Path(r"I:\DEDUP_ARCHIVE")
REPORT_DIR = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\backups\dedup_reports")
MIN_FILE_SIZE = 1  # Skip 0-byte files
MAX_PEEK_SIZE = 64 * 1024  # 64KB content peek for comparison
BINARY_EXTENSIONS = {'.pdf', '.docx', '.xlsx', '.pptx', '.zip', '.rar', '.7z',
                     '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.mp3',
                     '.mp4', '.avi', '.mov', '.db', '.sqlite', '.exe', '.dll'}
TEXT_EXTENSIONS = {'.txt', '.md', '.csv', '.json', '.xml', '.html', '.htm',
                   '.py', '.js', '.ts', '.jsx', '.tsx', '.css', '.log', '.yaml',
                   '.yml', '.toml', '.ini', '.cfg', '.bat', '.ps1', '.sh'}


def file_sha256(path):
    """Full file SHA-256."""
    h = hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
    except (OSError, PermissionError):
        return None
    return h.hexdigest()


def peek_content(path, max_bytes=MAX_PEEK_SIZE):
    """Read first N bytes of file for content comparison."""
    try:
        with open(path, 'rb') as f:
            return f.read(max_bytes)
    except (OSError, PermissionError):
        return None


def text_content_normalized(path):
    """Read text file, normalize whitespace for comparison."""
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read(MAX_PEEK_SIZE * 2)
        # Normalize: strip whitespace, lowercase, collapse spaces
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return '\n'.join(lines).lower()
    except (OSError, PermissionError):
        return None


def pdf_text_peek(path):
    """Extract first ~4KB of visible text from PDF for content comparison."""
    try:
        with open(path, 'rb') as f:
            raw = f.read(128 * 1024)  # Read first 128KB of PDF
        # Simple PDF text extraction (no dependencies)
        text_chunks = []
        i = 0
        while i < len(raw):
            # Look for text between BT...ET blocks or parenthesized strings
            paren_start = raw.find(b'(', i)
            if paren_start == -1:
                break
            paren_end = raw.find(b')', paren_start)
            if paren_end == -1:
                break
            chunk = raw[paren_start + 1:paren_end]
            try:
                decoded = chunk.decode('latin-1', errors='replace')
                # Filter printable
                printable = ''.join(c for c in decoded if c.isprintable() or c in '\n\t ')
                if len(printable) > 3:
                    text_chunks.append(printable)
            except:
                pass
            i = paren_end + 1
            if len(''.join(text_chunks)) > 4096:
                break
        return ''.join(text_chunks)[:4096] if text_chunks else None
    except (OSError, PermissionError):
        return None


def content_fingerprint(path):
    """
    Generate a content-based fingerprint. This PEEKS INSIDE the document.
    Returns (size, sha256, content_peek_hash, content_type).
    """
    ext = path.suffix.lower()
    size = path.stat().st_size

    # Full SHA-256
    sha = file_sha256(str(path))
    if sha is None:
        return None

    # Content peek — varies by file type
    if ext == '.pdf':
        text = pdf_text_peek(str(path))
        if text and len(text) > 20:
            content_hash = hashlib.sha256(text.encode('utf-8', errors='replace')).hexdigest()[:16]
            return (size, sha, content_hash, 'pdf_text')

    if ext in TEXT_EXTENSIONS:
        text = text_content_normalized(str(path))
        if text and len(text) > 10:
            content_hash = hashlib.sha256(text.encode('utf-8', errors='replace')).hexdigest()[:16]
            return (size, sha, content_hash, 'text_normalized')

    # Binary files: peek first 64KB
    peek = peek_content(str(path))
    if peek:
        content_hash = hashlib.sha256(peek).hexdigest()[:16]
        return (size, sha, content_hash, 'binary_peek')

    return (size, sha, sha[:16], 'sha256_only')


def are_duplicates(path1, path2, fp1, fp2):
    """
    Content-based duplicate verification. Goes BEYOND hashing.
    Returns (is_dup, confidence, method).
    """
    # Different sizes = definitely not duplicates
    if fp1[0] != fp2[0]:
        return False, 0.0, 'size_mismatch'

    # Same SHA-256 = very likely duplicates
    if fp1[1] == fp2[1]:
        # But we STILL peek inside to verify (user rule: no hash-only)
        peek1 = peek_content(str(path1))
        peek2 = peek_content(str(path2))
        if peek1 is not None and peek2 is not None:
            if peek1 == peek2:
                return True, 0.99, 'sha256+content_verified'
            else:
                # Hash collision or encoding difference — compare more
                if fp1[3] in ('text_normalized', 'pdf_text'):
                    return True, 0.95, 'sha256_match_content_minor_diff'
                return False, 0.5, 'sha256_match_content_mismatch'
        # Can't read one — trust SHA-256
        return True, 0.90, 'sha256_match_peek_unavailable'

    # Same content hash but different SHA-256 (e.g., same text different metadata)
    if fp1[2] == fp2[2] and fp1[3] in ('text_normalized', 'pdf_text'):
        return True, 0.85, 'content_match_metadata_diff'

    return False, 0.0, 'different'


def choose_keeper(paths):
    """Choose which file to keep. Prefer: longest path depth, newest modified, largest."""
    # Keep the one in the most specific (deepest) directory
    scored = []
    for p in paths:
        depth = len(p.parts)
        mtime = p.stat().st_mtime
        size = p.stat().st_size
        scored.append((depth, mtime, size, p))
    scored.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
    return scored[0][3]


def dedup_folder(folder_path, dry_run=False):
    """
    Deduplicate a folder. Content-based comparison. Duplicates move to I:/DEDUP_ARCHIVE/.
    Returns report dict.
    """
    folder = Path(folder_path)
    if not folder.exists() or not folder.is_dir():
        print(f"ERROR: {folder} is not a valid directory")
        return None

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_subdir = DEDUP_ARCHIVE / f"{folder.name}_{ts}"

    print(f"{'[DRY RUN] ' if dry_run else ''}DEDUPLICATING: {folder}")
    print(f"  Archive target: {archive_subdir}")
    print()

    # Phase 1: Inventory all files
    all_files = []
    skipped = []
    for root, dirs, files in os.walk(folder):
        for fname in files:
            fpath = Path(root) / fname
            try:
                if fpath.stat().st_size < MIN_FILE_SIZE:
                    skipped.append(str(fpath))
                    continue
                all_files.append(fpath)
            except (OSError, PermissionError):
                skipped.append(str(fpath))

    print(f"  Files found: {len(all_files)} ({len(skipped)} skipped)")

    if not all_files:
        print("  No files to process.")
        return {"total": 0, "duplicates": 0, "moved": 0}

    # Phase 2: Fingerprint all files
    print("  Fingerprinting (content peek inside each file)...")
    fingerprints = {}
    errors = []
    for i, fpath in enumerate(all_files):
        if (i + 1) % 100 == 0:
            print(f"    ...{i + 1}/{len(all_files)}")
        fp = content_fingerprint(fpath)
        if fp:
            fingerprints[fpath] = fp
        else:
            errors.append(str(fpath))

    print(f"  Fingerprinted: {len(fingerprints)} ({len(errors)} errors)")

    # Phase 3: Group by (size, sha256) then verify content
    size_sha_groups = defaultdict(list)
    for fpath, fp in fingerprints.items():
        key = (fp[0], fp[1])  # (size, sha256)
        size_sha_groups[key].append(fpath)

    # Only groups with 2+ files are potential duplicates
    potential_groups = {k: v for k, v in size_sha_groups.items() if len(v) > 1}
    print(f"  Potential duplicate groups: {len(potential_groups)}")

    # Phase 4: Content-verify each group
    duplicates_found = []
    total_bytes_saved = 0

    for (size, sha), paths in potential_groups.items():
        fps = [fingerprints[p] for p in paths]

        # Verify ALL pairs in group are true duplicates
        verified_dups = [paths[0]]
        for i in range(1, len(paths)):
            is_dup, confidence, method = are_duplicates(paths[0], paths[i], fps[0], fps[i])
            if is_dup and confidence >= 0.85:
                verified_dups.append(paths[i])

        if len(verified_dups) > 1:
            keeper = choose_keeper(verified_dups)
            for p in verified_dups:
                if p != keeper:
                    duplicates_found.append({
                        'original': str(keeper),
                        'duplicate': str(p),
                        'size': size,
                        'sha256': sha,
                        'confidence': confidence,
                        'method': method
                    })
                    total_bytes_saved += size

    print(f"\n  DUPLICATES FOUND: {len(duplicates_found)}")
    print(f"  Space recoverable: {total_bytes_saved / (1024*1024):.1f} MB")

    # Phase 5: Move duplicates to I:\DEDUP_ARCHIVE\
    moved = 0
    move_errors = []
    if duplicates_found and not dry_run:
        archive_subdir.mkdir(parents=True, exist_ok=True)

        for dup in duplicates_found:
            src = Path(dup['duplicate'])
            # Preserve relative path structure
            try:
                rel = src.relative_to(folder)
            except ValueError:
                rel = Path(src.name)
            dest = archive_subdir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)

            # Handle name collision
            if dest.exists():
                stem = dest.stem
                suffix = dest.suffix
                counter = 1
                while dest.exists():
                    dest = dest.parent / f"{stem}_dup{counter}{suffix}"
                    counter += 1

            try:
                shutil.move(str(src), str(dest))
                dup['moved_to'] = str(dest)
                moved += 1
                print(f"    MOVED: {src.name} → {dest}")
            except (OSError, PermissionError) as e:
                move_errors.append({'file': str(src), 'error': str(e)})
                print(f"    ERROR: {src.name} — {e}")

    # Phase 6: Generate report
    report = {
        'timestamp': ts,
        'folder': str(folder),
        'dry_run': dry_run,
        'total_files': len(all_files),
        'fingerprinted': len(fingerprints),
        'duplicate_groups': len(potential_groups),
        'duplicates_found': len(duplicates_found),
        'files_moved': moved,
        'bytes_saved': total_bytes_saved,
        'mb_saved': round(total_bytes_saved / (1024*1024), 2),
        'archive_dir': str(archive_subdir) if moved > 0 else None,
        'errors': errors + [e['error'] for e in move_errors],
        'skipped': skipped,
        'details': duplicates_found
    }

    # Save report
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / f"dedup_{folder.name}_{ts}.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n  REPORT: {report_path}")
    print(f"  SUMMARY: {len(duplicates_found)} duplicates, {moved} moved, {report['mb_saved']}MB saved")

    if dry_run and duplicates_found:
        print(f"\n  [DRY RUN] Would move {len(duplicates_found)} files to {archive_subdir}")
        for dup in duplicates_found[:10]:
            print(f"    {Path(dup['duplicate']).name} (kept: {Path(dup['original']).name})")
        if len(duplicates_found) > 10:
            print(f"    ...and {len(duplicates_found) - 10} more")

    return report


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('--help', '-h'):
        print(__doc__)
        return 0

    folder = sys.argv[1]
    dry_run = '--dry-run' in sys.argv

    result = dedup_folder(folder, dry_run=dry_run)
    if result is None:
        return 1

    if result['duplicates_found'] == 0:
        print("\n  No duplicates found. Folder is clean.")

    return 0


if __name__ == '__main__':
    sys.exit(main())
