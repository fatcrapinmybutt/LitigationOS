"""
I:\ Drive ZIP Unpack, Dedup & Triage Engine
============================================
Recursively unpacks all ZIPs on I:\, deduplicates by content,
classifies files as litigation-worthy (GOOD) or not (OTHER),
and flattens everything into two top-level folders.

Usage:
    python I_drive_unpack_triage.py [--batch-size 20] [--dry-run]
"""

import os
import sys
import zipfile
import hashlib
import shutil
import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Force UTF-8 stdout
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

# ─── CONFIGURATION ────────────────────────────────────────────────
DRIVE = Path("I:\\")
PROCESSING_DIR = DRIVE / "_PROCESSING"
STAGING_DIR = PROCESSING_DIR / "staging"
GOOD_DIR = DRIVE / "GOOD"
OTHER_DIR = DRIVE / "OTHER"
MANIFEST_FILE = PROCESSING_DIR / "zip_manifest.json"
PROGRESS_FILE = PROCESSING_DIR / "progress.json"
DEDUP_LOG = PROCESSING_DIR / "dedup_log.json"
REPORT_FILE = PROCESSING_DIR / "final_report.txt"
BATCH_SIZE = 20

# Folders we create / own — skip during scanning
OWN_FOLDERS = {"_PROCESSING", "GOOD", "OTHER"}

# ─── LITIGATION KEYWORD DETECTION ─────────────────────────────────
LITIGATION_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt',
    '.xls', '.xlsx', '.csv',
    '.jpg', '.jpeg', '.png', '.tif', '.tiff', '.bmp', '.gif',
    '.eml', '.msg', '.mbox',
    '.html', '.htm', '.xml', '.json',
    '.mp3', '.wav', '.mp4', '.avi', '.mov', '.mkv',
}

LITIGATION_KEYWORDS = re.compile(
    r'(?i)\b('
    r'court|custody|motion|order|filing|judge|docket|hearing|'
    r'deposition|subpoena|affidavit|complaint|respondent|petitioner|'
    r'plaintiff|defendant|attorney|counsel|guardian.?ad.?litem|'
    r'parenting.?time|child.?support|alimony|spousal|divorce|'
    r'visitation|custody.?evaluation|mediation|arbitration|'
    r'discovery|interrogator|exhibit|testimony|witness|sworn|'
    r'stipulat|judgment|decree|appeal|brief|memorandum|'
    r'pigors|watson|hoopes|ladas|shady.?oaks|'
    r'mcr|mcl|mre|frcp|fre|'
    r'ppo|protection.?order|restraining|'
    r'circuit.?court|probate|family.?division|'
    r'case.?no|docket.?no|file.?no|'
    r'2024.?001507|2023.?5907|2025.?002760|'
    r'bates|exhibit|evidence|record|'
    r'disqualif|recus|bias|misconduct|'
    r'email|correspondence|communication|letter|notice|'
    r'financial|bank|account|tax|income|'
    r'medical|mental.?health|therap|counsel|psych|'
    r'school|education|report.?card|iep|'
    r'photo|picture|screenshot|image|video|recording'
    r')\b'
)

LITIGATION_FILENAME_PATTERNS = re.compile(
    r'(?i)(motion|order|brief|filing|exhibit|affidavit|subpoena|'
    r'complaint|petition|response|reply|memo|notice|'
    r'pigors|watson|court|custody|hearing|depo|'
    r'transcript|ruling|stipulat|judgment|decree|'
    r'discovery|interrogat|admission|'
    r'bank.?stat|tax.?return|pay.?stub|w2|1099|'
    r'email|text.?msg|message|chat|'
    r'photo|screenshot|evidence|record|report|'
    r'medical|school|therap|eval)'
)


def ensure_dirs():
    """Create all working directories."""
    for d in [PROCESSING_DIR, STAGING_DIR, GOOD_DIR, OTHER_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def load_progress():
    """Load progress state from checkpoint file."""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"scanned": False, "unpacked_zips": [], "phase": "init"}


def save_progress(progress):
    """Save progress state for crash recovery."""
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=2, default=str)


# ─── PHASE 1: SCAN FOR ZIPS ──────────────────────────────────────

def scan_zips():
    """Find all ZIP files on I:\ recursively, excluding our own folders."""
    print(f"\n{'='*60}")
    print(f"PHASE 1: Scanning {DRIVE} for ZIP files...")
    print(f"{'='*60}")

    zips = []
    for root, dirs, files in os.walk(DRIVE):
        # Skip our own processing/output folders
        rel = Path(root).relative_to(DRIVE)
        if rel.parts and rel.parts[0] in OWN_FOLDERS:
            dirs.clear()
            continue

        for f in files:
            if f.lower().endswith('.zip'):
                fp = Path(root) / f
                try:
                    size = fp.stat().st_size
                    zips.append({"path": str(fp), "size": size, "unpacked": False})
                except OSError as e:
                    print(f"  [WARN] Cannot stat {fp}: {e}")

    # Save manifest
    with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
        json.dump(zips, f, indent=2)

    print(f"  Found {len(zips)} ZIP files")
    print(f"  Total size: {sum(z['size'] for z in zips) / (1024*1024):.1f} MB")
    print(f"  Manifest saved to {MANIFEST_FILE}")
    return zips


# ─── PHASE 2: BATCH UNPACK ───────────────────────────────────────

def safe_extract_name(original_name, staging_path):
    """Generate a unique flat filename to avoid collisions."""
    base = Path(original_name).name  # strip subdirs from zip entry
    if not base:
        return None  # directory entry
    target = staging_path / base
    if not target.exists():
        return target

    stem = target.stem
    suffix = target.suffix
    counter = 1
    while True:
        candidate = staging_path / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def unpack_single_zip(zip_path, staging_dir, stats):
    """Unpack a single ZIP, flatten contents, handle nested zips."""
    nested_zips = []
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                target = safe_extract_name(info.filename, staging_dir)
                if target is None:
                    continue
                try:
                    with zf.open(info) as src, open(target, 'wb') as dst:
                        shutil.copyfileobj(src, dst)
                    stats['extracted'] += 1

                    # Check for nested zip
                    if target.suffix.lower() == '.zip':
                        nested_zips.append(target)
                except Exception as e:
                    print(f"    [WARN] Failed to extract {info.filename}: {e}")
                    stats['errors'] += 1

    except zipfile.BadZipFile:
        print(f"    [WARN] Bad ZIP file: {zip_path}")
        stats['bad_zips'] += 1
    except Exception as e:
        print(f"    [ERROR] Failed to open {zip_path}: {e}")
        stats['errors'] += 1

    # Recursively handle nested zips
    for nested in nested_zips:
        print(f"    [NESTED] Unpacking {nested.name}...")
        unpack_single_zip(nested, staging_dir, stats)
        # Move the nested zip itself to staging (it's already there)
        stats['nested'] += 1


def batch_unpack(zips, progress, batch_size=BATCH_SIZE):
    """Unpack ZIPs in batches, with progress checkpointing."""
    print(f"\n{'='*60}")
    print(f"PHASE 2: Unpacking {len(zips)} ZIPs in batches of {batch_size}...")
    print(f"{'='*60}")

    already_done = set(progress.get("unpacked_zips", []))
    remaining = [z for z in zips if z["path"] not in already_done]
    print(f"  Already unpacked: {len(already_done)}, Remaining: {len(remaining)}")

    stats = {'extracted': 0, 'errors': 0, 'bad_zips': 0, 'nested': 0}
    batch_num = 0

    for i in range(0, len(remaining), batch_size):
        batch = remaining[i:i + batch_size]
        batch_num += 1
        print(f"\n  --- Batch {batch_num} ({len(batch)} ZIPs) ---")

        for z in batch:
            zp = z["path"]
            print(f"  Unpacking: {Path(zp).name} ({z['size'] / 1024:.0f} KB)")
            unpack_single_zip(Path(zp), STAGING_DIR, stats)
            progress["unpacked_zips"].append(zp)

        # Checkpoint after each batch
        progress["phase"] = "unpacking"
        save_progress(progress)
        print(f"  Batch {batch_num} done. Extracted so far: {stats['extracted']}")

    progress["phase"] = "unpack_complete"
    save_progress(progress)
    print(f"\n  Unpack complete: {stats['extracted']} files extracted, "
          f"{stats['errors']} errors, {stats['bad_zips']} bad zips, "
          f"{stats['nested']} nested zips")
    return stats


# ─── PHASE 3: FLATTEN ────────────────────────────────────────────

def flatten_staging():
    """Ensure all files in staging are at the root level (de-nest)."""
    print(f"\n{'='*60}")
    print(f"PHASE 3: Flattening staging directory...")
    print(f"{'='*60}")

    moved = 0
    for root, dirs, files in os.walk(STAGING_DIR):
        if Path(root) == STAGING_DIR:
            continue  # already at top level
        for f in files:
            src = Path(root) / f
            dst = safe_extract_name(f, STAGING_DIR)
            if dst:
                shutil.move(str(src), str(dst))
                moved += 1

    # Remove empty subdirectories
    for root, dirs, files in os.walk(STAGING_DIR, topdown=False):
        if Path(root) != STAGING_DIR and not files and not dirs:
            try:
                os.rmdir(root)
            except OSError:
                pass

    print(f"  Flattened {moved} files to staging root")
    return moved


# ─── PHASE 4: CONTENT-BASED DEDUP ────────────────────────────────

def file_fingerprint(filepath, chunk_size=8192):
    """Read first 8KB for quick fingerprint + file size."""
    try:
        size = filepath.stat().st_size
        with open(filepath, 'rb') as f:
            head = f.read(chunk_size)
        return (size, hashlib.sha256(head).hexdigest())
    except Exception:
        return None


def files_identical(path_a, path_b, chunk_size=65536):
    """Full binary comparison of two files — the real content-based dedup."""
    try:
        if path_a.stat().st_size != path_b.stat().st_size:
            return False
        with open(path_a, 'rb') as fa, open(path_b, 'rb') as fb:
            while True:
                ca = fa.read(chunk_size)
                cb = fb.read(chunk_size)
                if ca != cb:
                    return False
                if not ca:
                    return True
    except Exception:
        return False


def dedup_content():
    """Content-based dedup: group by fingerprint, then full-compare matches."""
    print(f"\n{'='*60}")
    print(f"PHASE 4: Content-based deduplication...")
    print(f"{'='*60}")

    files = [STAGING_DIR / f for f in os.listdir(STAGING_DIR)
             if (STAGING_DIR / f).is_file()]
    print(f"  Total files in staging: {len(files)}")

    # Group by quick fingerprint (size + first 8KB hash)
    fingerprints = defaultdict(list)
    for fp in files:
        sig = file_fingerprint(fp)
        if sig:
            fingerprints[sig].append(fp)

    unique_sigs = sum(1 for v in fingerprints.values() if len(v) == 1)
    dupe_groups = {k: v for k, v in fingerprints.items() if len(v) > 1}
    print(f"  Unique by fingerprint: {unique_sigs}")
    print(f"  Potential duplicate groups: {len(dupe_groups)}")

    # Full binary compare within each group
    dupes_removed = 0
    dedup_log = []

    for sig, group in dupe_groups.items():
        # Within each group, do full binary comparison
        keep = [group[0]]
        for candidate in group[1:]:
            is_dupe = False
            for keeper in keep:
                if files_identical(keeper, candidate):
                    is_dupe = True
                    dedup_log.append({
                        "kept": str(keeper.name),
                        "removed": str(candidate.name),
                        "size": candidate.stat().st_size,
                        "reason": "identical_content"
                    })
                    # Don't hard delete — just remove from staging
                    candidate.unlink()
                    dupes_removed += 1
                    break
            if not is_dupe:
                keep.append(candidate)

    # Save dedup log
    with open(DEDUP_LOG, 'w', encoding='utf-8') as f:
        json.dump(dedup_log, f, indent=2)

    remaining = len([f for f in os.listdir(STAGING_DIR) if (STAGING_DIR / f).is_file()])
    print(f"  Duplicates removed: {dupes_removed}")
    print(f"  Unique files remaining: {remaining}")
    print(f"  Dedup log saved to {DEDUP_LOG}")
    return dupes_removed, remaining


# ─── PHASE 5: CLASSIFY ───────────────────────────────────────────

def peek_content(filepath, max_bytes=4096):
    """Read first N bytes of a file as text for keyword scanning."""
    try:
        with open(filepath, 'rb') as f:
            raw = f.read(max_bytes)
        # Try UTF-8, fall back to latin-1
        try:
            return raw.decode('utf-8', errors='replace')
        except Exception:
            return raw.decode('latin-1', errors='replace')
    except Exception:
        return ""


def classify_file(filepath):
    """
    Determine if a file is litigation-worthy.
    Checks: filename patterns, extension, and content peek.
    Returns: 'GOOD' or 'OTHER'
    """
    name = filepath.name
    ext = filepath.suffix.lower()

    # 1) Filename pattern match
    if LITIGATION_FILENAME_PATTERNS.search(name):
        return 'GOOD'

    # 2) Known litigation extensions get content-peeked
    if ext in LITIGATION_EXTENSIONS:
        content = peek_content(filepath)
        if LITIGATION_KEYWORDS.search(content):
            return 'GOOD'
        # Even without keyword match, common doc types might be relevant
        if ext in {'.pdf', '.doc', '.docx', '.eml', '.msg'}:
            # Lower bar: if it's a document, lean toward keeping
            return 'GOOD'

    # 3) Text-based files: always peek
    if ext in {'.txt', '.md', '.rtf', '.csv', '.html', '.htm', '.xml', '.json', '.log'}:
        content = peek_content(filepath)
        if LITIGATION_KEYWORDS.search(content):
            return 'GOOD'

    # 4) Media files (photos/videos) — likely evidence
    if ext in {'.jpg', '.jpeg', '.png', '.tif', '.tiff', '.bmp', '.gif',
               '.mp4', '.avi', '.mov', '.mkv', '.mp3', '.wav', '.m4a'}:
        return 'GOOD'

    # 5) Everything else → OTHER
    return 'OTHER'


def classify_all():
    """Classify all files in staging."""
    print(f"\n{'='*60}")
    print(f"PHASE 5: Classifying files...")
    print(f"{'='*60}")

    files = [STAGING_DIR / f for f in os.listdir(STAGING_DIR)
             if (STAGING_DIR / f).is_file()]

    results = {'GOOD': [], 'OTHER': []}
    for fp in files:
        verdict = classify_file(fp)
        results[verdict].append(fp)

    print(f"  GOOD (litigation-worthy): {len(results['GOOD'])}")
    print(f"  OTHER: {len(results['OTHER'])}")
    return results


# ─── PHASE 6: FINAL MOVE ─────────────────────────────────────────

def move_classified(results):
    """Move classified files to GOOD/ and OTHER/ as flat dirs."""
    print(f"\n{'='*60}")
    print(f"PHASE 6: Moving files to final destinations...")
    print(f"{'='*60}")

    for category, files in results.items():
        dest_dir = GOOD_DIR if category == 'GOOD' else OTHER_DIR
        for fp in files:
            target = dest_dir / fp.name
            # Handle collision in destination
            if target.exists():
                stem = target.stem
                suffix = target.suffix
                counter = 1
                while target.exists():
                    target = dest_dir / f"{stem}_{counter}{suffix}"
                    counter += 1
            shutil.move(str(fp), str(target))

        print(f"  Moved {len(files)} files to {dest_dir}")


# ─── PHASE 7: CLEANUP & REPORT ───────────────────────────────────

def cleanup_and_report(zip_count, unpack_stats, dupes_removed, unique_count, results):
    """Remove empty dirs and produce summary report."""
    print(f"\n{'='*60}")
    print(f"PHASE 7: Cleanup & Report")
    print(f"{'='*60}")

    # Remove staging if empty
    try:
        if STAGING_DIR.exists() and not any(STAGING_DIR.iterdir()):
            STAGING_DIR.rmdir()
            print(f"  Removed empty staging directory")
    except OSError:
        pass

    # Build report
    report = f"""
╔══════════════════════════════════════════════════════════╗
║         I:\\ DRIVE UNPACK & TRIAGE REPORT               ║
╠══════════════════════════════════════════════════════════╣
║  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S'):<43} ║
╠══════════════════════════════════════════════════════════╣
║  ZIP files found:      {zip_count:<33} ║
║  Files extracted:      {unpack_stats.get('extracted', 0):<33} ║
║  Bad ZIPs skipped:     {unpack_stats.get('bad_zips', 0):<33} ║
║  Nested ZIPs found:    {unpack_stats.get('nested', 0):<33} ║
║  Extraction errors:    {unpack_stats.get('errors', 0):<33} ║
╠══════════════════════════════════════════════════════════╣
║  Duplicates removed:   {dupes_removed:<33} ║
║  Unique files:         {unique_count:<33} ║
╠══════════════════════════════════════════════════════════╣
║  GOOD (litigation):    {len(results.get('GOOD', [])):<33} ║
║  OTHER:                {len(results.get('OTHER', [])):<33} ║
╠══════════════════════════════════════════════════════════╣
║  Output: I:\\GOOD\\     (litigation-worthy, flat)         ║
║  Output: I:\\OTHER\\    (everything else, flat)            ║
╚══════════════════════════════════════════════════════════╝
"""
    print(report)

    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"  Report saved to {REPORT_FILE}")


# ─── ALSO PROCESS LOOSE FILES (non-zip) ──────────────────────────

def collect_loose_files():
    """Collect non-ZIP files already on I:\ that aren't in our folders."""
    print(f"\n{'='*60}")
    print(f"PHASE 2b: Collecting loose (non-ZIP) files...")
    print(f"{'='*60}")

    count = 0
    for root, dirs, files in os.walk(DRIVE):
        rel = Path(root).relative_to(DRIVE)
        if rel.parts and rel.parts[0] in OWN_FOLDERS:
            dirs.clear()
            continue

        for f in files:
            if f.lower().endswith('.zip'):
                continue
            src = Path(root) / f
            dst = safe_extract_name(f, STAGING_DIR)
            if dst:
                try:
                    shutil.copy2(str(src), str(dst))
                    count += 1
                except Exception as e:
                    print(f"  [WARN] Cannot copy {src}: {e}")

    print(f"  Collected {count} loose files into staging")
    return count


# ─── MAIN ────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="I:\\ Drive ZIP Unpack & Triage")
    parser.add_argument('--batch-size', type=int, default=BATCH_SIZE,
                        help=f'ZIPs per batch (default: {BATCH_SIZE})')
    parser.add_argument('--dry-run', action='store_true',
                        help='Scan and report only, no extraction')
    parser.add_argument('--skip-scan', action='store_true',
                        help='Skip scan phase, use existing manifest')
    parser.add_argument('--resume', action='store_true',
                        help='Resume from last checkpoint')
    args = parser.parse_args()

    print(f"\n{'#'*60}")
    print(f"#  I:\\ DRIVE UNPACK, DEDUP & TRIAGE ENGINE")
    print(f"#  Batch size: {args.batch_size} | Dry run: {args.dry_run}")
    print(f"#  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")

    ensure_dirs()
    progress = load_progress() if args.resume else {"scanned": False, "unpacked_zips": [], "phase": "init"}

    # Phase 1: Scan
    if args.skip_scan and MANIFEST_FILE.exists():
        with open(MANIFEST_FILE, 'r', encoding='utf-8') as f:
            zips = json.load(f)
        print(f"\n  Loaded existing manifest: {len(zips)} ZIPs")
    else:
        zips = scan_zips()
        progress["scanned"] = True
        save_progress(progress)

    if args.dry_run:
        print("\n  [DRY RUN] Stopping after scan. Review manifest at:")
        print(f"  {MANIFEST_FILE}")
        return

    # Phase 2: Unpack
    unpack_stats = batch_unpack(zips, progress, args.batch_size)

    # Phase 2b: Collect loose files
    collect_loose_files()

    # Phase 3: Flatten
    flatten_staging()

    # Phase 4: Dedup
    dupes_removed, unique_count = dedup_content()

    # Phase 5: Classify
    results = classify_all()

    # Phase 6: Move
    move_classified(results)

    # Phase 7: Report
    cleanup_and_report(
        zip_count=len(zips),
        unpack_stats=unpack_stats,
        dupes_removed=dupes_removed,
        unique_count=unique_count,
        results=results
    )

    print(f"\n  ✅ DONE. Check I:\\GOOD\\ and I:\\OTHER\\")


if __name__ == '__main__':
    main()
