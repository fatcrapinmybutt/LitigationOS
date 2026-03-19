#!/usr/bin/env python3
"""
DRIVE ORGANIZER v4 — Tight 7-folder structure (FAT32 safe)
=============================================================
Direct classify + sort into consolidated structure:
  Evidence  — scanned PDFs, exhibits, photos, images, video, audio
  Court     — filings, orders, motions, forms, templates, dockets
  Legal     — analysis, strategy, authorities, reference, canons, rules
  Data      — JSON, CSV, DB, YAML, XML, structured data
  Code      — Python, scripts, tools, configs, EXE, DLL, system files
  AI        — prompts, superpins, LLM outputs, conversations, chat exports
  Archives  — ZIP bundles (not unzipped)
  _Trash    — junk, corrupt, empty, lock files

Max depth: 2 levels (Drive:\\Category\\file). No sub-nesting.

Usage:
    python drive_organizer_v4.py F
    python drive_organizer_v4.py --dry-run D F
"""
import os
import sys
import re
import shutil
import time
from pathlib import Path
from collections import Counter
from datetime import datetime

# ════════════════════════════════════════════════════════════════
# 7 Target Folders
# ════════════════════════════════════════════════════════════════

TARGET_FOLDERS = {
    "Evidence":  "Scanned PDFs, exhibits, photos, images, video, audio",
    "Court":     "Filings, orders, motions, forms, templates, dockets",
    "Legal":     "Analysis, strategy, authorities, reference, canons",
    "Data":      "JSON, CSV, DB, YAML, XML, structured data",
    "Code":      "Python, scripts, tools, configs, system files",
    "AI":        "Prompts, superpins, LLM outputs, conversations",
    "Archives":  "ZIP bundles (not unzipped)",
    "_Trash":    "Junk, corrupt, empty, lock files",
}

SKIP_DIRS = {
    "system volume information", "$recycle.bin", "_organizer_log",
    "_trash", "evidence", "court", "legal", "data", "code", "ai", "archives",
    "boot", "efi", "sources", "support",
    # Old v2/v3 folders (skip if still present)
    "01_scanned_evidence", "02_court_documents", "03_legal_analysis",
    "04_case_data", "05_code_and_tools", "06_archives", "07_media",
    "08_llm_and_prompts", "09_forms_and_templates", "10_reference",
    "11_system_files", "_recycle",
}

# ════════════════════════════════════════════════════════════════
# Classification
# ════════════════════════════════════════════════════════════════

EXT_MAP = {
    # Evidence (media/images)
    ".png": "Evidence", ".jpg": "Evidence", ".jpeg": "Evidence",
    ".gif": "Evidence", ".bmp": "Evidence", ".svg": "Evidence",
    ".ico": "Evidence", ".webp": "Evidence",
    ".mp4": "Evidence", ".mkv": "Evidence", ".avi": "Evidence",
    ".mov": "Evidence", ".mp3": "Evidence", ".wav": "Evidence",
    ".html": "Evidence", ".htm": "Evidence",
    # Court (forms/templates)
    ".docx": "Court", ".doc": "Court", ".rtf": "Court", ".odt": "Court",
    # Data
    ".json": "Data", ".jsonl": "Data", ".csv": "Data",
    ".db": "Data", ".sqlite": "Data",
    ".yaml": "Data", ".yml": "Data", ".xml": "Data",
    ".graphml": "Data", ".cypher": "Data",
    # Code
    ".py": "Code", ".ps1": "Code", ".sh": "Code",
    ".bat": "Code", ".cmd": "Code",
    ".ts": "Code", ".tsx": "Code", ".js": "Code", ".jsx": "Code",
    ".go": "Code", ".rs": "Code",
    ".toml": "Code", ".cfg": "Code", ".ini": "Code", ".lock": "Code",
    ".exe": "Code", ".msi": "Code", ".dll": "Code", ".sys": "Code",
    ".iso": "Code", ".inf": "Code", ".efi": "Code",
    ".cat": "Code", ".mui": "Code", ".wim": "Code",
    # Archives
    ".zip": "Archives", ".7z": "Archives", ".rar": "Archives",
    ".tar": "Archives", ".gz": "Archives", ".bz2": "Archives", ".xz": "Archives",
}
# Add .part001-.part009
for i in range(1, 10):
    EXT_MAP[f".part{i:03d}"] = "Archives"

NAME_PATTERNS = [
    # Evidence — scanned PDFs
    (re.compile(r"(?i)scanned|scan_\d|_0\d{2,3}\.pdf"), "Evidence"),
    (re.compile(r"(?i)2sided.*scanned.*\.pdf"), "Evidence"),
    (re.compile(r"(?i)(court.?docs?|ppo.?cust|exparte|healthwest|jtc|rusco|dockets|custody|transcript).*\.pdf"), "Evidence"),
    # Court — non-scanned PDFs
    (re.compile(r"(?i)(order|motion|brief|complaint|filing|exhibit|appendix|affidavit|subpoena|docket).*\.pdf"), "Court"),
    (re.compile(r"(?i)(COA_|MSC_|JTC_|ADMIN_Filing).*\.pdf"), "Court"),
    (re.compile(r"(?i)(SCAO|court.?form|form_|template|Application_for_Leave|Filing_Checklist)"), "Court"),
    (re.compile(r"(?i)michigan.*court.*form"), "Court"),
    (re.compile(r"(?i)\.pdf$"), "Court"),  # remaining PDFs → Court
    # Legal — analysis + reference
    (re.compile(r"(?i)(analysis|strategy|chronolog|timeline|comprehensive.*legal|violations|ADVANCED_LITIGATION|ACTION_PLAN)"), "Legal"),
    (re.compile(r"(?i)(CASE_CHRONOLOGY|EVENT_INDEX|APPELLATE_BRIEF|ARGUMENT)"), "Legal"),
    (re.compile(r"(?i)(SCANS_JUDICIAL|VOLUME_INDEX|TIMELINE_EVENTS)"), "Legal"),
    (re.compile(r"(?i)(authorit|CANON|rule_|MCR_|MCL_|benchbook|COURT.*RULES)"), "Legal"),
    (re.compile(r"(?i)(benchbook|civilbb|contemptbb|familybb).*\.pdf"), "Legal"),
    # AI — prompts/superpins/LLM
    (re.compile(r"(?i)(superpin|SUPERPIN|PIGGYPIGGY|gemini.*mainframe|MEGA_SUPER|HYPERPIN)"), "AI"),
    (re.compile(r"(?i)(copilot.*superpin|COPILOT_SUPERPIN|JUDICIAL_CANON_APPENDONLY)"), "AI"),
    (re.compile(r"(?i)(conversations?\.|BIGCHAT|chat_export|CONGLOMERATE|WARCHEST_APPENDED|LEGALWARCHEST)"), "AI"),
    (re.compile(r"(?i)(LLM_AUTO_PLAN|OFFLOAD|AUTOPILOT|AUTONOMOUS_OPERATION)"), "AI"),
    (re.compile(r"(?i)(KNOWLEDGE_ALL|ATTACHMENTS_DIGEST)"), "AI"),
    # Junk
    (re.compile(r"(?i)^\.~lock\."), "_Trash"),
    (re.compile(r"(?i)\.(tmp|bak|pyc|pyo|class|o|obj)$"), "_Trash"),
    (re.compile(r"(?i)^(thumbs\.db|desktop\.ini|\.ds_store)$"), "_Trash"),
    (re.compile(r"(?i)__pycache__"), "_Trash"),
]


def classify(filepath: Path) -> str:
    name = filepath.name
    ext = filepath.suffix.lower()

    try:
        size = filepath.stat().st_size
    except OSError:
        return "_Trash"

    if size == 0 and ext not in (".sh", ".bat", ".cmd", ".cfg", ".ini"):
        return "_Trash"

    for pattern, folder in NAME_PATTERNS:
        if pattern.search(name):
            return folder

    if ext in EXT_MAP:
        return EXT_MAP[ext]

    if ext in (".txt", ".md"):
        name_upper = name.upper()
        if any(k in name_upper for k in ("SUPERPIN", "COPILOT", "GEMINI", "PROMPT", "CHAT", "PIGGYPIGGY", "WARCHEST", "CONVO")):
            return "AI"
        if any(k in name_upper for k in ("ANALYSIS", "STRATEGY", "CHRONOL", "TIMELINE", "VIOLATION", "BRIEF", "ARGUMENT")):
            return "Legal"
        if any(k in name_upper for k in ("AUTHORITY", "CANON", "RULE", "MCR", "MCL", "BENCHBOOK")):
            return "Legal"
        if any(k in name_upper for k in ("README", "CHANGELOG", "TODO", "NOTES")):
            return "Code"
        return "Legal"

    if ext == ".ocx":
        return "Court"

    if size < 100:
        return "_Trash"
    return "Data"


def organize_drive(drive_letter: str, dry_run: bool = False):
    root = Path(f"{drive_letter}:\\")
    if not root.exists():
        print(f"SKIP {drive_letter}: — not found")
        return

    mode = "DRY RUN" if dry_run else "LIVE"
    print(f"\n{'='*60}")
    print(f"  DRIVE ORGANIZER v4 — {drive_letter}:\\ [{mode}]")
    print(f"{'='*60}")
    t0 = time.time()

    folder_counts = Counter()
    errors = []
    moved = 0

    # Phase 1: Create folders
    print(f"\n[{drive_letter}] Phase 1: CREATE FOLDERS")
    for folder, desc in TARGET_FOLDERS.items():
        target = root / folder
        if not dry_run:
            target.mkdir(exist_ok=True)
        print(f"  {'[DRY] ' if dry_run else ''}{folder}/ — {desc}")

    # Phase 2: Scan
    print(f"\n[{drive_letter}] Phase 2: SCAN")
    all_files = []
    for dirpath, dirnames, filenames in os.walk(str(root)):
        dp = Path(dirpath)
        rel = dp.relative_to(root)
        parts_lower = [p.lower() for p in rel.parts]
        do_skip = False
        for p in parts_lower:
            if p in SKIP_DIRS or p.startswith("$"):
                do_skip = True
                break
        if do_skip:
            dirnames.clear()
            continue
        for fname in filenames:
            all_files.append(dp / fname)
    print(f"  Found {len(all_files):,} files")

    # Phase 3: Classify + sort
    print(f"\n[{drive_letter}] Phase 3: CLASSIFY + SORT")
    for i, fp in enumerate(all_files):
        if not fp.exists():
            continue
        target_folder = classify(fp)
        dst = root / target_folder / fp.name
        if dst.exists():
            stem = dst.stem
            suffix = dst.suffix
            counter = 2
            while dst.exists():
                dst = dst.parent / f"{stem}_{counter}{suffix}"
                counter += 1
        if not dry_run:
            try:
                fp.rename(dst)
                moved += 1
            except OSError:
                try:
                    shutil.move(str(fp), str(dst))
                    moved += 1
                except Exception as e:
                    errors.append(f"{fp}: {e}")
        else:
            moved += 1
        folder_counts[target_folder] += 1

        if (i + 1) % 5000 == 0:
            print(f"  Processed {i+1:,}/{len(all_files):,} ...")

    print(f"\n  Results:")
    for folder, count in sorted(folder_counts.items(), key=lambda x: -x[1]):
        print(f"  {folder}: {count:,} files")

    # Phase 4: Clean empty dirs
    print(f"\n[{drive_letter}] Phase 4: CLEAN EMPTY DIRS")
    cleaned = 0
    for dirpath, _, _ in os.walk(str(root), topdown=False):
        dp = Path(dirpath)
        if dp == root:
            continue
        name_lower = dp.name.lower()
        if name_lower in SKIP_DIRS or name_lower.startswith("$"):
            continue
        if dp.name in TARGET_FOLDERS or name_lower == "_organizer_log":
            continue
        try:
            if not any(dp.iterdir()):
                if not dry_run:
                    dp.rmdir()
                cleaned += 1
        except OSError:
            pass
    print(f"  Removed {cleaned} empty directories")

    # Log
    elapsed = time.time() - t0
    if not dry_run:
        log_dir = root / "_ORGANIZER_LOG"
        log_dir.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(log_dir / f"v4_summary_{ts}.txt", "w") as f:
            f.write(f"Drive Organizer v4 — {drive_letter}:\\\n")
            f.write(f"Elapsed: {elapsed:.1f}s\nMoved: {moved}\nCleaned: {cleaned}\n\n")
            for folder, count in sorted(folder_counts.items(), key=lambda x: -x[1]):
                f.write(f"  {folder}: {count}\n")
            if errors:
                f.write(f"\nErrors ({len(errors)}):\n")
                for e in errors[:50]:
                    f.write(f"  {e}\n")

    print(f"\n{'─'*60}")
    print(f"  DONE in {elapsed:.1f}s — {drive_letter}:\\")
    print(f"    moved: {moved:,}  cleaned: {cleaned}  errors: {len(errors)}")
    print(f"{'─'*60}")


def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: python drive_organizer_v4.py [--dry-run] D [F G H]")
        sys.exit(1)
    dry_run = "--dry-run" in args
    drives = [a.upper().rstrip(":\\") for a in args if a != "--dry-run"]
    for d in drives:
        if d == "C":
            print("SKIPPING C: — use c_drive_organize.py")
            continue
        organize_drive(d, dry_run)


if __name__ == "__main__":
    main()
