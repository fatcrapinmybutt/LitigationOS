#!/usr/bin/env python3
"""
LitigationOS Scheduled Maintenance — Auto-runs on schedule.
1. Scans LitigationOS root for new unorganized files → moves to type buckets
2. Deduplicates within each type bucket
3. Checks external drives for new litigation files → copies unique ones in
4. Generates health report
"""
import sys, os, hashlib, shutil, csv, json
from pathlib import Path
from datetime import datetime

LITROOT = Path(r"C:\Users\andre\LitigationOS")
DRIVES = ["D:\\", "F:\\", "J:\\"]
TRASH = LITROOT / "_DEDUP_TRASH"
MANIFEST = LITROOT / "_MANIFEST"
REPORT_DIR = LITROOT / "00_SYSTEM" / "automation" / "reports"

TYPE_MAP = {
    ".pdf": "_PDF", ".txt": "_TXT", ".md": "_MD", ".csv": "_CSV",
    ".json": "_JSON", ".docx": "_DOCX", ".doc": "_DOCX",
    ".html": "_HTML", ".htm": "_HTML", ".db": "_DB", ".sqlite": "_DB",
    ".zip": "_ZIP", ".7z": "_ZIP", ".rar": "_ZIP",
}

PROTECTED = {".git", ".github", ".agents", ".venv", ".vscode", "00_SYSTEM",
             "node_modules", "__pycache__", "site-packages", "_MANIFEST",
             "_DEDUP_TRASH", "_PDF", "_TXT", "_MD", "_CSV", "_JSON",
             "_DOCX", "_HTML", "_DB", "_ZIP"}

def sha256(path):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
    except (OSError, PermissionError):
        return None
    return h.hexdigest()

def phase1_organize():
    """Move new unorganized files into type buckets."""
    moved = 0
    for root, dirs, files in os.walk(LITROOT):
        dirs[:] = [d for d in dirs if d not in PROTECTED and not d.startswith("_")]
        for f in files:
            fp = Path(root) / f
            ext = fp.suffix.lower()
            if ext == ".py" or ext not in TYPE_MAP:
                continue
            bucket = TYPE_MAP[ext]
            dest_dir = LITROOT / bucket
            dest = dest_dir / fp.name
            if dest.exists():
                continue
            try:
                dest_dir.mkdir(exist_ok=True)
                shutil.move(str(fp), str(dest))
                moved += 1
            except Exception:
                pass
    return moved

def phase2_dedupe():
    """SHA-256 dedup within each type bucket."""
    dupes = 0
    freed = 0
    TRASH.mkdir(exist_ok=True)
    for bucket in LITROOT.iterdir():
        if not bucket.is_dir() or not bucket.name.startswith("_") or bucket.name in {"_MANIFEST", "_DEDUP_TRASH"}:
            continue
        seen = {}
        for fp in bucket.rglob("*"):
            if not fp.is_file() or fp.suffix.lower() == ".py":
                continue
            h = sha256(fp)
            if h is None:
                continue
            if h in seen:
                sz = fp.stat().st_size
                try:
                    dest = TRASH / fp.name
                    c = 0
                    while dest.exists():
                        c += 1
                        dest = TRASH / f"{fp.stem}_{c}{fp.suffix}"
                    shutil.move(str(fp), str(dest))
                    dupes += 1
                    freed += sz
                except Exception:
                    pass
            else:
                seen[h] = fp
    return dupes, freed

def phase3_ingest_drives():
    """Check external drives for new unique files."""
    copied = 0
    known_hashes = set()
    # Build hash set of existing files
    for bucket in LITROOT.iterdir():
        if bucket.is_dir() and bucket.name.startswith("_") and bucket.name not in {"_MANIFEST", "_DEDUP_TRASH"}:
            for fp in bucket.rglob("*"):
                if fp.is_file():
                    h = sha256(fp)
                    if h:
                        known_hashes.add(h)

    for drive in DRIVES:
        dp = Path(drive)
        if not dp.exists():
            continue
        for root, dirs, files in os.walk(dp):
            dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", "node_modules"}]
            for f in files:
                fp = Path(root) / f
                ext = fp.suffix.lower()
                if ext not in TYPE_MAP or ext == ".py":
                    continue
                try:
                    h = sha256(fp)
                    if h and h not in known_hashes:
                        bucket = TYPE_MAP[ext]
                        dest = LITROOT / bucket / fp.name
                        if not dest.exists():
                            (LITROOT / bucket).mkdir(exist_ok=True)
                            shutil.copy2(str(fp), str(dest))
                            known_hashes.add(h)
                            copied += 1
                except Exception:
                    pass
    return copied

def generate_report(organized, dupes, freed, ingested):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now()
    report = {
        "timestamp": ts.isoformat(),
        "phase1_organized": organized,
        "phase2_dupes_removed": dupes,
        "phase2_space_freed_mb": round(freed / (1024**2), 1),
        "phase3_new_files_ingested": ingested,
        "buckets": {}
    }
    for bucket in sorted(LITROOT.iterdir()):
        if bucket.is_dir() and bucket.name.startswith("_") and bucket.name not in {"_MANIFEST", "_DEDUP_TRASH"}:
            count = sum(1 for _ in bucket.rglob("*") if _.is_file())
            report["buckets"][bucket.name] = count

    rp = REPORT_DIR / f"maintenance_{ts:%Y%m%d_%H%M%S}.json"
    with open(rp, "w") as f:
        json.dump(report, f, indent=2)
    return rp

def main():
    print(f"[{datetime.now():%Y-%m-%d %H:%M}] LitigationOS Scheduled Maintenance")
    print("Phase 1: Organizing new files...")
    organized = phase1_organize()
    print(f"  → {organized} files organized")

    print("Phase 2: Deduplicating...")
    dupes, freed = phase2_dedupe()
    print(f"  → {dupes} dupes removed, {freed/(1024**2):.1f} MB freed")

    print("Phase 3: Ingesting from external drives...")
    ingested = phase3_ingest_drives()
    print(f"  → {ingested} new files ingested")

    rp = generate_report(organized, dupes, freed, ingested)
    print(f"\nReport: {rp}")
    print("Maintenance complete.")

if __name__ == "__main__":
    main()
