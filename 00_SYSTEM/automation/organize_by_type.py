#!/usr/bin/env python3
"""
LitigationOS Organize by Type — Right-click context menu target.
Usage: python organize_by_type.py <folder_path>
Moves files into type-bucket subdirectories (_PDF, _TXT, _MD, etc.)
Preserves directory structure within each bucket. Never touches .py files.
"""
import sys, os, shutil, csv, hashlib
from pathlib import Path
from datetime import datetime

TYPE_MAP = {
    ".pdf": "_PDF", ".txt": "_TXT", ".md": "_MD", ".csv": "_CSV",
    ".json": "_JSON", ".docx": "_DOCX", ".doc": "_DOCX",
    ".html": "_HTML", ".htm": "_HTML", ".db": "_DB", ".sqlite": "_DB",
    ".zip": "_ZIP", ".7z": "_ZIP", ".rar": "_ZIP", ".tar": "_ZIP", ".gz": "_ZIP",
    ".xlsx": "_XLSX", ".xls": "_XLSX",
    ".png": "_IMG", ".jpg": "_IMG", ".jpeg": "_IMG", ".gif": "_IMG",
    ".bmp": "_IMG", ".tiff": "_IMG", ".svg": "_IMG", ".webp": "_IMG",
    ".mp4": "_MEDIA", ".avi": "_MEDIA", ".mov": "_MEDIA", ".mkv": "_MEDIA",
    ".mp3": "_MEDIA", ".wav": "_MEDIA", ".flac": "_MEDIA",
    ".pptx": "_PPTX", ".ppt": "_PPTX",
    ".eml": "_EMAIL", ".msg": "_EMAIL",
}

PROTECTED = {".git", ".github", ".agents", ".venv", ".vscode", "00_SYSTEM",
             "node_modules", "__pycache__", "site-packages", "_MANIFEST",
             "_DEDUP_TRASH"}

def quick_hash(path):
    """First + last 64KB for fast comparison."""
    h = hashlib.sha256()
    try:
        sz = path.stat().st_size
        with open(path, "rb") as f:
            h.update(f.read(65536))
            if sz > 65536:
                f.seek(max(0, sz - 65536))
                h.update(f.read(65536))
    except (OSError, PermissionError):
        return None
    return h.hexdigest()

def organize_folder(target):
    target = Path(target).resolve()
    if not target.is_dir():
        print(f"ERROR: {target} is not a directory")
        return

    log_dir = target / "_MANIFEST"
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / f"organize_log_{datetime.now():%Y%m%d_%H%M%S}.csv"

    # Collect files
    all_files = []
    for root, dirs, files in os.walk(target):
        dirs[:] = [d for d in dirs if d not in PROTECTED and not d.startswith("_")]
        for f in files:
            fp = Path(root) / f
            ext = fp.suffix.lower()
            if ext == ".py":
                continue
            if ext in TYPE_MAP:
                all_files.append((fp, ext))

    total = len(all_files)
    if total == 0:
        print("No organizable files found.")
        return

    print(f"Found {total:,} files to organize in {target}")

    # Create buckets
    buckets_needed = set(TYPE_MAP[ext] for _, ext in all_files)
    for bucket in buckets_needed:
        (target / bucket).mkdir(exist_ok=True)

    moved = 0
    skipped = 0
    errors = 0

    with open(log_path, "w", newline="", encoding="utf-8") as csvf:
        writer = csv.writer(csvf)
        writer.writerow(["action", "source", "destination", "size", "hash"])

        for i, (fp, ext) in enumerate(all_files):
            if i % 200 == 0 and i > 0:
                print(f"  Progress: {i:,}/{total:,} ({moved:,} moved)")
            try:
                bucket = TYPE_MAP[ext]
                rel = fp.relative_to(target)
                dest = target / bucket / rel
                
                if dest.exists():
                    skipped += 1
                    writer.writerow(["SKIPPED_EXISTS", str(fp), str(dest), fp.stat().st_size, ""])
                    continue

                dest.parent.mkdir(parents=True, exist_ok=True)
                h = quick_hash(fp)
                shutil.move(str(fp), str(dest))
                writer.writerow(["MOVED", str(fp), str(dest), dest.stat().st_size, h or ""])
                moved += 1
            except Exception as e:
                errors += 1
                writer.writerow(["ERROR", str(fp), "", 0, str(e)])

    print(f"\n{'='*60}")
    print(f"ORGANIZE COMPLETE: {target}")
    print(f"  Files found:    {total:,}")
    print(f"  Moved:          {moved:,}")
    print(f"  Skipped:        {skipped:,}")
    print(f"  Errors:         {errors}")
    print(f"  Buckets:        {', '.join(sorted(buckets_needed))}")
    print(f"  Log:            {log_path}")
    print(f"{'='*60}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python organize_by_type.py <folder_path>")
        sys.exit(1)
    organize_folder(sys.argv[1])
    input("\nPress Enter to close...")
