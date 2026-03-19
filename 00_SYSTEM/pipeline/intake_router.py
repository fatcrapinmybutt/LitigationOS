"""
LitigationOS — Intake Auto-Router
Routes new files into the correct numbered directory based on extension,
content signals, and meek_lane classification.

Usage:
    python intake_router.py <file_or_dir> [--dry-run]
"""
import os
import re
import shutil
import sqlite3
import sys
from pathlib import Path

BASE = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = BASE / "00_SYSTEM" / "pipeline" / "agents" / "master_index.db"

# Extension → target directory mapping
ROUTE_MAP = {
    # Legal documents
    ".pdf":   "01_CASE_FILES",
    ".docx":  "01_CASE_FILES",
    ".doc":   "01_CASE_FILES",
    ".rtf":   "01_CASE_FILES",
    # Evidence
    ".png":   "02_EVIDENCE",
    ".jpg":   "02_EVIDENCE",
    ".jpeg":  "02_EVIDENCE",
    ".bmp":   "02_EVIDENCE",
    ".tif":   "02_EVIDENCE",
    ".tiff":  "02_EVIDENCE",
    ".gif":   "02_EVIDENCE",
    ".mp3":   "02_EVIDENCE",
    ".mp4":   "02_EVIDENCE",
    ".wav":   "02_EVIDENCE",
    # Legal authorities
    ".md":    "03_LEGAL_AUTHORITIES",
    ".txt":   "03_LEGAL_AUTHORITIES",
    # Court filings
    ".eml":   "04_COURT_FILINGS",
    # Analysis
    ".xlsx":  "05_ANALYSIS",
    ".xls":   "05_ANALYSIS",
    ".csv":   "05_ANALYSIS",
    # Data
    ".json":  "06_DATA",
    ".jsonl": "06_DATA",
    ".xml":   "06_DATA",
    ".yaml":  "06_DATA",
    ".yml":   "06_DATA",
    ".db":    "06_DATA",
    ".sqlite":"06_DATA",
    # Specs / code
    ".py":    "07_SPECS",
    ".js":    "07_SPECS",
    ".html":  "07_SPECS",
    ".css":   "07_SPECS",
    # Archives
    ".zip":   "99_ARCHIVE",
    ".7z":    "99_ARCHIVE",
    ".rar":   "99_ARCHIVE",
    ".tar":   "99_ARCHIVE",
    ".gz":    "99_ARCHIVE",
}

# Content signals for meek_lane classification
LANE_A_PAT = re.compile(
    r"watson|custody|parenting.?time|mcneill|2024.?001507|2023.?5907|"
    r"friend.?of.?court|foc|child.?support|visitation",
    re.IGNORECASE,
)
LANE_B_PAT = re.compile(
    r"shady.?oaks|hoopes|2025.?002760|habitability|security.?deposit|"
    r"landlord|tenant|lease|eviction|housing",
    re.IGNORECASE,
)
LANE_C_PAT = re.compile(
    r"1983|civil.?rights|due.?process|equal.?protection|monell|"
    r"judicial.?misconduct|jtc|bar.?grievance|conspiracy|1985",
    re.IGNORECASE,
)
LANE_D_PAT = re.compile(
    r"PPO|protection.?order|personal.?protection|contempt.?of.?court|"
    r"bond.?violat|stalking|MCL.?600\.2950|MCR.?3\.70[678]|"
    r"restrain|no.?contact|harassment.?order",
    re.IGNORECASE,
)
LANE_E_PAT = re.compile(
    r"bias|prejudic|impartial|recus|disqualif|"
    r"JTC|judicial.?tenure|judicial.?misconduct|canon\s+\d|"
    r"MCR.?2\.003|ex.?parte.?(?:contact|communication|order)|"
    r"McNeill.?(?:bias|misconduct|violat)",
    re.IGNORECASE,
)
LANE_F_PAT = re.compile(
    r"leave.?to.?appeal|interlocutory.?appeal|"
    r"court.?of.?appeals|COA|MSC|supreme.?court|"
    r"MCR.?7\.\d|standard.?of.?review|de.?novo|"
    r"abuse.?of.?discretion|clearly.?erroneous|"
    r"peremptory|superintending.?control",
    re.IGNORECASE,
)


def classify_lane(filepath: Path) -> str:
    """Classify file into a meek_lane based on filename + first 4K content."""
    name = filepath.name.lower()
    text = name
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text += " " + f.read(4096)
    except Exception:
        pass

    if LANE_E_PAT.search(text):
        return "E"
    if LANE_D_PAT.search(text):
        return "D"
    if LANE_F_PAT.search(text):
        return "F"
    if LANE_C_PAT.search(text):
        return "C"
    if LANE_A_PAT.search(text):
        return "A"
    if LANE_B_PAT.search(text):
        return "B"
    return "UNCLASSIFIED"


def route_file(filepath: Path, dry_run: bool = False) -> str:
    """Route a single file to the correct LitigationOS directory."""
    ext = filepath.suffix.lower()
    target_dir_name = ROUTE_MAP.get(ext, "99_ARCHIVE")
    lane = classify_lane(filepath)

    # Lane-specific subdirs for legal docs
    if target_dir_name in ("01_CASE_FILES", "03_LEGAL_AUTHORITIES", "04_COURT_FILINGS"):
        lane_subdir = {
            "A": "lane_a_watson", "B": "lane_b_shady_oaks", "C": "lane_c_federal",
            "D": "lane_d_ppo", "E": "lane_e_misconduct", "F": "lane_f_appellate",
        }.get(lane, "unclassified")
        dest_dir = BASE / target_dir_name / lane_subdir
    else:
        dest_dir = BASE / target_dir_name

    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / filepath.name

    # Collision handling
    if dest.exists() and dest != filepath:
        stem, suffix = filepath.stem, filepath.suffix
        counter = 2
        while dest.exists():
            dest = dest_dir / f"{stem}_{counter}{suffix}"
            counter += 1

    action = "MOVE" if filepath.drive == dest.drive else "COPY"
    if dry_run:
        print(f"[DRY-RUN] {action}: {filepath} -> {dest} (lane={lane})")
        return f"DRY:{action}"

    if action == "MOVE":
        shutil.move(str(filepath), str(dest))
    else:
        shutil.copy2(str(filepath), str(dest))

    # Register in DB
    try:
        db = sqlite3.connect(str(DB_PATH))
        db.execute(
            "INSERT OR IGNORE INTO files (full_path, file_name, extension, size_bytes, drive, depth, meek_lane, processed) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 0)",
            (str(dest), dest.name, ext, dest.stat().st_size, dest.drive[0] if dest.drive else "C",
             len(dest.relative_to(BASE).parts), lane),
        )
        db.commit()
        db.close()
    except Exception as e:
        print(f"  DB warn: {e}")

    print(f"[{action}] {filepath.name} -> {dest.parent.name}/ (lane={lane})")
    return action


def route_directory(dirpath: Path, dry_run: bool = False) -> dict:
    """Route all files in a directory."""
    stats = {"moved": 0, "copied": 0, "skipped": 0, "errors": 0}
    for f in sorted(dirpath.rglob("*")):
        if not f.is_file():
            continue
        if f.name.startswith(".") or "__pycache__" in str(f):
            stats["skipped"] += 1
            continue
        try:
            result = route_file(f, dry_run=dry_run)
            if "MOVE" in result:
                stats["moved"] += 1
            elif "COPY" in result:
                stats["copied"] += 1
        except Exception as e:
            print(f"  ERROR: {f.name}: {e}")
            stats["errors"] += 1
    return stats


def main():
    if len(sys.argv) < 2:
        print("Usage: python intake_router.py <file_or_dir> [--dry-run]")
        sys.exit(1)

    target = Path(sys.argv[1])
    dry_run = "--dry-run" in sys.argv

    if not target.exists():
        print(f"ERROR: {target} does not exist")
        sys.exit(1)

    if target.is_file():
        route_file(target, dry_run=dry_run)
    elif target.is_dir():
        stats = route_directory(target, dry_run=dry_run)
        print(f"\nDone: {stats}")
    else:
        print(f"ERROR: {target} is not a file or directory")
        sys.exit(1)


if __name__ == "__main__":
    main()
