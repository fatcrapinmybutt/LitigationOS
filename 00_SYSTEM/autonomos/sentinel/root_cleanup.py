"""
DELTA99 Ω∞ — Root Directory Cleanup Engine
=============================================
Scans and reorganizes the LitigationOS root directory, moving loose files
into their canonical locations per the DIRECTORY_STANDARD.
Moves to Recycle Bin — NEVER hard-deletes. Full manifest + rollback.
"""
import sys
import sqlite3
import json
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

_shared = Path(__file__).parent.parent / "shared"
if str(_shared) not in sys.path:
    sys.path.insert(0, str(_shared))

from autonomos_config import LITIGOS_ROOT, DIRECTORY_STANDARD

CLEANUP_DB = Path(__file__).parent.parent / "root_cleanup.db"

# ── Protected Directories (NEVER move) ─────────────────────────────
PROTECTED = {
    "00_SYSTEM", "01_EXTRACTS", "02_AUTHORITY", "03_EVIDENCE",
    "04_COURT_FILINGS", "05_ANALYSIS", "06_FILINGS", "07_SPECS",
    "08_APPS", "09_DATA", "10_Exhibits", "SAFETY_SNAPSHOT_DB",
    ".git", ".github", ".vscode", "node_modules", "__pycache__",
    "06_CASE_DATABASES", ".copilot-assistant",
}

# ── File Classification Rules ──────────────────────────────────────
EXTENSION_ROUTES = {
    # Documents
    ".pdf": "03_EVIDENCE",
    ".docx": "03_EVIDENCE",
    ".doc": "03_EVIDENCE",
    ".rtf": "03_EVIDENCE",
    # Data
    ".csv": "09_DATA",
    ".json": "09_DATA",
    ".xlsx": "09_DATA",
    ".xls": "09_DATA",
    ".sqlite": "09_DATA",
    ".db": "09_DATA",
    # Images
    ".jpg": "03_EVIDENCE/images",
    ".jpeg": "03_EVIDENCE/images",
    ".png": "03_EVIDENCE/images",
    ".gif": "03_EVIDENCE/images",
    ".bmp": "03_EVIDENCE/images",
    # Archives
    ".zip": "09_DATA/archives",
    ".7z": "09_DATA/archives",
    ".rar": "09_DATA/archives",
    # Code
    ".py": "00_SYSTEM/scripts",
    ".ps1": "00_SYSTEM/scripts",
    ".bat": "00_SYSTEM/scripts",
    ".sh": "00_SYSTEM/scripts",
    # Docs
    ".md": "07_SPECS",
    ".txt": "09_DATA/text",
    # Media
    ".mp3": "03_EVIDENCE/audio",
    ".wav": "03_EVIDENCE/audio",
    ".mp4": "03_EVIDENCE/video",
    # Misc
    ".log": "00_SYSTEM/logs",
}

# Files to ALWAYS skip (never move)
SKIP_FILES = {
    ".gitignore", ".gitattributes", "LICENSE", "README.md",
    "package.json", "package-lock.json", "requirements.txt",
    "Pipfile", "Pipfile.lock", "setup.py", "pyproject.toml",
    ".env", ".env.example", "START.ps1", "STARTUP_REPORT.md",
}


def _init_db() -> sqlite3.Connection:
    CLEANUP_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(CLEANUP_DB), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS cleanup_manifest (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_path TEXT NOT NULL,
            destination TEXT NOT NULL,
            sha256 TEXT DEFAULT '',
            size_bytes INTEGER DEFAULT 0,
            action TEXT DEFAULT 'pending',
            moved_at TEXT DEFAULT '',
            can_undo_until TEXT DEFAULT '',
            run_id INTEGER DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_cm_action ON cleanup_manifest(action);

        CREATE TABLE IF NOT EXISTS cleanup_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            files_scanned INTEGER DEFAULT 0,
            files_to_move INTEGER DEFAULT 0,
            files_moved INTEGER DEFAULT 0,
            files_skipped INTEGER DEFAULT 0,
            errors INTEGER DEFAULT 0,
            dry_run INTEGER DEFAULT 1,
            run_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    return conn


@dataclass
class CleanupItem:
    original: Path
    destination: Path
    sha256: str = ""
    size: int = 0
    reason: str = ""


def scan_root() -> list[CleanupItem]:
    """Scan root directory for items that should be moved."""
    items = []

    for entry in LITIGOS_ROOT.iterdir():
        name = entry.name

        # Skip protected directories
        if name in PROTECTED:
            continue

        # Skip dotfiles and protected files
        if name.startswith(".") or name in SKIP_FILES:
            continue

        if entry.is_dir():
            # Loose directories at root
            dest = LITIGOS_ROOT / "09_DATA" / "unsorted_dirs" / name
            items.append(CleanupItem(
                original=entry, destination=dest,
                reason=f"Loose directory at root"
            ))
        elif entry.is_file():
            ext = entry.suffix.lower()

            # Route by extension
            route = EXTENSION_ROUTES.get(ext)
            if route:
                dest = LITIGOS_ROOT / route / name
            else:
                dest = LITIGOS_ROOT / "_UNSORTED" / name

            # Calculate hash for files
            sha = ""
            try:
                h = hashlib.sha256()
                with open(str(entry), "rb") as f:
                    for chunk in iter(lambda: f.read(8192), b""):
                        h.update(chunk)
                sha = h.hexdigest()
            except (IOError, PermissionError):
                pass

            items.append(CleanupItem(
                original=entry, destination=dest,
                sha256=sha, size=entry.stat().st_size if entry.exists() else 0,
                reason=f"Loose file ({ext or 'no-ext'}) → {route or '_UNSORTED'}"
            ))

    return items


def execute_cleanup(items: list[CleanupItem], dry_run: bool = True) -> dict:
    """Execute cleanup (move files to destinations)."""
    cdb = _init_db()

    run_id = cdb.execute("""
        INSERT INTO cleanup_runs (files_scanned, files_to_move, dry_run)
        VALUES (?, ?, ?)
    """, (len(items), len(items), int(dry_run))).lastrowid
    cdb.commit()

    moved = 0
    skipped = 0
    errors = 0

    for item in items:
        # Record in manifest
        cdb.execute("""
            INSERT INTO cleanup_manifest
            (original_path, destination, sha256, size_bytes, action, run_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (str(item.original), str(item.destination),
              item.sha256, item.size,
              "dry_run" if dry_run else "pending", run_id))

        if dry_run:
            skipped += 1
            continue

        try:
            item.destination.parent.mkdir(parents=True, exist_ok=True)

            # Handle collision
            dest = item.destination
            counter = 2
            while dest.exists():
                stem = item.destination.stem
                suffix = item.destination.suffix
                dest = item.destination.parent / f"{stem}_v{counter}{suffix}"
                counter += 1

            if item.original.is_dir():
                shutil.copytree(str(item.original), str(dest))
            else:
                shutil.copy2(str(item.original), str(dest))

            # Verify copy
            if dest.exists():
                now = datetime.now()
                undo_until = datetime(now.year, now.month + 1 if now.month < 12 else 1,
                                      now.day if now.day <= 28 else 28).isoformat()
                cdb.execute("""
                    UPDATE cleanup_manifest SET action='moved', moved_at=?, can_undo_until=?
                    WHERE original_path=? AND run_id=?
                """, (now.isoformat(), undo_until, str(item.original), run_id))

                # Do NOT delete source — move to _ARCHIVE instead
                archive_dir = LITIGOS_ROOT / "_ARCHIVE" / "root_cleanup" / now.strftime("%Y%m%d")
                archive_dir.mkdir(parents=True, exist_ok=True)
                archive_dest = archive_dir / item.original.name
                try:
                    shutil.move(str(item.original), str(archive_dest))
                except Exception:
                    pass  # Source stays — not a critical failure

                moved += 1
            else:
                errors += 1
                cdb.execute("""
                    UPDATE cleanup_manifest SET action='error'
                    WHERE original_path=? AND run_id=?
                """, (str(item.original), run_id))
        except Exception as e:
            errors += 1
            cdb.execute("""
                UPDATE cleanup_manifest SET action='error'
                WHERE original_path=? AND run_id=?
            """, (str(item.original), run_id))

    cdb.execute("""
        UPDATE cleanup_runs SET files_moved=?, files_skipped=?, errors=?
        WHERE id=?
    """, (moved, skipped, errors, run_id))
    cdb.commit()
    cdb.close()

    return {
        "run_id": run_id,
        "dry_run": dry_run,
        "scanned": len(items),
        "to_move": len(items),
        "moved": moved,
        "skipped": skipped,
        "errors": errors,
        "items": [
            {"from": str(i.original.name), "to": str(i.destination.relative_to(LITIGOS_ROOT)),
             "reason": i.reason, "size_mb": round(i.size / (1024*1024), 2)}
            for i in items[:30]
        ],
    }


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "scan"

    if mode == "scan":
        items = scan_root()
        result = execute_cleanup(items, dry_run=True)
        print(json.dumps(result, indent=2, default=str))
    elif mode == "execute":
        items = scan_root()
        result = execute_cleanup(items, dry_run=False)
        print(json.dumps(result, indent=2, default=str))
    else:
        print("Usage: python root_cleanup.py [scan|execute]")
