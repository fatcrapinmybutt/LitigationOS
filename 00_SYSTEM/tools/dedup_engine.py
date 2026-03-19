#!/usr/bin/env python3
"""
LitigationOS Content-Based Dedup Engine v1.0
=============================================
Finds duplicate files by content comparison (NOT just hashing).
Moves confirmed duplicates to I:\LitigationOS_Dedup\ — NEVER deletes.

Strategy:
1. Find files matching dupe patterns: (1), (2), _copy1, _2, etc.
2. Locate the "original" (same name without the suffix)
3. Compare file sizes first (fast filter)
4. Binary content comparison (authoritative check)
5. Move confirmed dupes to I:\LitigationOS_Dedup\{ext_subdir}\
6. Log every action to dedup_log.csv

Usage:
    python dedup_engine.py --ext .pdf          # Dedup PDFs only
    python dedup_engine.py --ext .csv,.json    # Dedup CSVs and JSONs
    python dedup_engine.py --all               # All extensions
    python dedup_engine.py --dry-run --all     # Preview only
"""

import sys
import os
import re
import csv
import shutil
import hashlib
import argparse
from pathlib import Path
from datetime import datetime

# Force UTF-8 output
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', errors='replace')

# === CONFIGURATION ===
SOURCE_DIR = Path(r"C:\Users\andre\LitigationOS")
DEDUP_DIR = Path(r"I:\LitigationOS_Dedup")
LOG_FILE = DEDUP_DIR / "dedup_log.csv"
CHUNK_SIZE = 8192  # 8KB chunks for binary comparison

# Extension to subdirectory mapping
EXT_MAP = {
    '.pdf': 'pdf', '.docx': 'docx', '.doc': 'docx',
    '.txt': 'txt', '.md': 'txt', '.rtf': 'txt',
    '.csv': 'csv', '.tsv': 'csv',
    '.json': 'json', '.jsonl': 'json', '.yaml': 'json', '.yml': 'json',
    '.py': 'scripts', '.ps1': 'scripts', '.bat': 'scripts', '.sh': 'scripts',
    '.jpg': 'images', '.jpeg': 'images', '.png': 'images', '.gif': 'images',
    '.svg': 'images', '.webp': 'images', '.heic': 'images',
    '.zip': 'archives', '.gz': 'archives', '.tar': 'archives',
    '.7z': 'archives', '.rar': 'archives',
}

# Regex patterns that indicate a file is a copy
DUPE_PATTERNS = [
    # (1), (2), (3) at end of basename — most common pattern
    re.compile(r'^(.+?)\s*\((\d+)\)$'),
    # _copy1, _copy2
    re.compile(r'^(.+?)_copy(\d+)$'),
    # Trailing _2, _3 (but not _v2 which is a version)
    re.compile(r'^(.+?)_(\d+)$'),
    # " - Copy" pattern from Windows
    re.compile(r'^(.+?)\s*-\s*Copy(?:\s*\((\d+)\))?$'),
]

# Files/patterns to NEVER touch (critical system files)
PROTECTED_PATTERNS = [
    'litigation_context.db',
    'flatten_manifest.db',
    'drive_inventory.db',
    '.git',
    '.gitignore',
    '.gitattributes',
    'copilot-instructions.md',
    'AGENTS.md',
    'LICENSE',
    'README.md',
    '00_SYSTEM',
]


def is_protected(filepath: Path) -> bool:
    """Check if file is protected from dedup moves."""
    name = filepath.name
    for pattern in PROTECTED_PATTERNS:
        if pattern in name or pattern in str(filepath):
            return True
    # Never touch database files
    if filepath.suffix in ('.db', '.db-shm', '.db-wal', '.sqlite'):
        return True
    return False


def find_original(candidate: Path, base_name: str, ext: str) -> Path | None:
    """Find the original file that this candidate is a copy of."""
    parent = candidate.parent
    # Direct match: original has the base_name + same extension
    original = parent / f"{base_name}{ext}"
    if original.exists() and original != candidate:
        return original
    return None


def content_equal(file_a: Path, file_b: Path) -> bool:
    """
    Compare two files by actual content — byte-by-byte.
    This is the AUTHORITATIVE check. We peek inside the document.
    Returns True if files are identical in content.
    """
    # Fast size check first
    try:
        if file_a.stat().st_size != file_b.stat().st_size:
            return False
    except OSError:
        return False

    # Zero-byte files are "equal" but we don't want to dedup them
    if file_a.stat().st_size == 0:
        return False

    # Byte-by-byte comparison
    try:
        with open(file_a, 'rb') as fa, open(file_b, 'rb') as fb:
            while True:
                chunk_a = fa.read(CHUNK_SIZE)
                chunk_b = fb.read(CHUNK_SIZE)
                if chunk_a != chunk_b:
                    return False
                if not chunk_a:  # EOF reached on both
                    return True
    except (OSError, PermissionError) as e:
        print(f"  [WARN] Cannot compare: {e}")
        return False


def get_dedup_target(filepath: Path) -> Path:
    """Determine where to move a duplicate file."""
    ext = filepath.suffix.lower()
    subdir = EXT_MAP.get(ext, 'misc')
    target_dir = DEDUP_DIR / subdir
    target_dir.mkdir(parents=True, exist_ok=True)

    target = target_dir / filepath.name
    # Handle name collision in dedup target
    counter = 1
    while target.exists():
        stem = filepath.stem
        target = target_dir / f"{stem}_dup{counter}{filepath.suffix}"
        counter += 1
    return target


def parse_dupe_candidate(filepath: Path) -> tuple[str, str] | None:
    """
    Check if filename matches a duplicate pattern.
    Returns (original_base_name, extension) or None.
    """
    stem = filepath.stem
    ext = filepath.suffix

    for pattern in DUPE_PATTERNS:
        match = pattern.match(stem)
        if match:
            base = match.group(1).rstrip()
            return (base, ext)
    return None


def init_log():
    """Initialize the CSV log file."""
    if not LOG_FILE.exists():
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'action', 'source_file', 'original_file',
                'destination', 'size_bytes', 'content_match', 'sha256'
            ])


def log_action(action, source, original, destination, size, content_match, sha):
    """Append a row to the dedup log."""
    with open(LOG_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().isoformat(), action, str(source), str(original),
            str(destination), size, content_match, sha
        ])


def sha256_file(filepath: Path) -> str:
    """Compute SHA-256 for audit trail."""
    h = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(CHUNK_SIZE * 16), b''):
                h.update(chunk)
        return h.hexdigest()[:16]  # Short hash for log readability
    except (OSError, PermissionError):
        return "ERROR"


def run_dedup(extensions: list[str], dry_run: bool = False, limit: int = 0):
    """Main dedup execution."""
    init_log()

    print(f"\n{'='*60}")
    print(f"LitigationOS Dedup Engine v1.0")
    print(f"Source: {SOURCE_DIR}")
    print(f"Target: {DEDUP_DIR}")
    print(f"Extensions: {', '.join(extensions) if extensions else 'ALL'}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE — moving files'}")
    print(f"{'='*60}\n")

    # Collect root-level files only
    all_files = [f for f in SOURCE_DIR.iterdir() if f.is_file()]

    if extensions:
        all_files = [f for f in all_files if f.suffix.lower() in extensions]

    print(f"Scanning {len(all_files)} files...")

    candidates = []
    for f in all_files:
        if is_protected(f):
            continue
        result = parse_dupe_candidate(f)
        if result:
            candidates.append((f, result[0], result[1]))

    print(f"Found {len(candidates)} duplicate candidates\n")

    moved = 0
    skipped = 0
    no_original = 0
    content_mismatch = 0
    errors = 0

    for i, (candidate, base_name, ext) in enumerate(candidates):
        if limit and moved >= limit:
            print(f"\n[LIMIT] Reached move limit of {limit}")
            break

        if (i + 1) % 50 == 0:
            print(f"  Progress: {i+1}/{len(candidates)} checked, {moved} moved")

        try:
            original = find_original(candidate, base_name, ext)
            if not original:
                no_original += 1
                continue

            # Content comparison — THE authoritative check
            if content_equal(candidate, original):
                target = get_dedup_target(candidate)
                size = candidate.stat().st_size
                sha = sha256_file(candidate)

                if dry_run:
                    print(f"  [DRY] Would move: {candidate.name}")
                    print(f"         Original: {original.name}")
                    print(f"         Size: {size:,} bytes")
                    log_action('DRY_MOVE', candidate, original, target, size, True, sha)
                else:
                    shutil.move(str(candidate), str(target))
                    print(f"  [MOVED] {candidate.name} -> {target.parent.name}/")
                    log_action('MOVED', candidate, original, target, size, True, sha)
                moved += 1
            else:
                content_mismatch += 1
                log_action('KEPT_DIFFERENT', candidate, original, 'N/A',
                          candidate.stat().st_size, False, 'N/A')

        except (OSError, PermissionError) as e:
            errors += 1
            print(f"  [ERROR] {candidate.name}: {e}")
            log_action('ERROR', candidate, 'N/A', 'N/A', 0, False, str(e))

    print(f"\n{'='*60}")
    print(f"RESULTS:")
    print(f"  Candidates checked:  {len(candidates)}")
    print(f"  Confirmed dupes:     {moved} {'(dry run)' if dry_run else '(moved)'}")
    print(f"  Content different:   {content_mismatch} (kept — not true dupes)")
    print(f"  No original found:   {no_original}")
    print(f"  Errors:              {errors}")
    print(f"  Log: {LOG_FILE}")
    print(f"{'='*60}\n")

    return moved, content_mismatch, no_original, errors


def main():
    parser = argparse.ArgumentParser(description='LitigationOS Content-Based Dedup Engine')
    parser.add_argument('--ext', type=str, help='Comma-separated extensions (e.g., .pdf,.csv)')
    parser.add_argument('--all', action='store_true', help='Process all file types')
    parser.add_argument('--dry-run', action='store_true', help='Preview without moving')
    parser.add_argument('--limit', type=int, default=0, help='Max files to move (0=unlimited)')
    args = parser.parse_args()

    if not args.ext and not args.all:
        parser.error("Specify --ext or --all")

    if not DEDUP_DIR.exists():
        print(f"ERROR: Dedup target {DEDUP_DIR} does not exist!")
        sys.exit(1)

    extensions = []
    if args.ext:
        extensions = [e.strip() if e.startswith('.') else f'.{e.strip()}'
                     for e in args.ext.split(',')]

    run_dedup(extensions, dry_run=args.dry_run, limit=args.limit)


if __name__ == '__main__':
    main()
