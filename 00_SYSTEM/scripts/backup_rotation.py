#!/usr/bin/env python3
"""
Automated Database Backup with Rotation & Verification.

Extends the existing db_backup_engine.py with:
- 7 daily + 4 weekly + 3 monthly rotation policy
- Integrity verification on every backup
- Lane DB backup support
- Scheduling integration (Windows Task Scheduler)

Usage:
    python backup_rotation.py                 # Run backup now
    python backup_rotation.py --schedule      # Install as scheduled task
    python backup_rotation.py --status        # Show backup inventory
    python backup_rotation.py --verify-all    # Verify all existing backups
"""

import sys
import os
import json
import sqlite3
import shutil
import hashlib
import logging
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', errors='replace')

# ── Configuration ──────────────────────────────────────────────────────
LITIGOS_ROOT = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = LITIGOS_ROOT / "litigation_context.db"

# Smart backup destination: prefer I:\ (external), fallback to local
_BACKUP_CANDIDATES = [
    Path(r"I:\LitigationOS_Backup"),       # External drive (preferred)
    Path(r"F:\LitigationOS_Backup"),       # Secondary external
    Path(r"G:\LitigationOS_Backup"),       # Tertiary external
    LITIGOS_ROOT / "12_ARCHIVES" / "db_backups",  # Local fallback
]

def _resolve_backup_root() -> Path:
    """Pick the first available backup destination drive."""
    for candidate in _BACKUP_CANDIDATES:
        drive = candidate.anchor  # e.g. "I:\\"
        if drive and Path(drive).exists():
            return candidate
        if not drive:
            # Local path (no drive letter) — always valid
            return candidate
    # Ultimate fallback
    return LITIGOS_ROOT / "12_ARCHIVES" / "db_backups"

BACKUP_ROOT = _resolve_backup_root()
MANIFEST_PATH = BACKUP_ROOT / "backup_manifest.json"

# Retention policy
KEEP_DAILY = 7
KEEP_WEEKLY = 4
KEEP_MONTHLY = 3

# Additional databases to back up
LANE_DBS = [
    LITIGOS_ROOT / "lane_A_custody.db",
    LITIGOS_ROOT / "lane_B_housing.db",
    LITIGOS_ROOT / "lane_C_convergence.db",
    LITIGOS_ROOT / "lane_D_ppo.db",
    LITIGOS_ROOT / "lane_E_misconduct.db",
    LITIGOS_ROOT / "lane_F_appellate.db",
    LITIGOS_ROOT / "agents" / "master_index.db",
    LITIGOS_ROOT / "mcr_rules.db",
]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
log = logging.getLogger("backup_rotation")


# ── Manifest Management ────────────────────────────────────────────────

def load_manifest() -> Dict:
    """Load or create backup manifest."""
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, 'r') as f:
            return json.load(f)
    return {"backups": [], "last_daily": None, "last_weekly": None, "last_monthly": None}


def save_manifest(manifest: Dict):
    """Save manifest to disk."""
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, 'w') as f:
        json.dump(manifest, f, indent=2, default=str)


# ── Backup Operations ──────────────────────────────────────────────────

def wal_checkpoint(db_path: Path) -> bool:
    """Force WAL checkpoint before backup."""
    try:
        conn = sqlite3.connect(str(db_path), timeout=120)
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.close()
        log.info(f"  WAL checkpoint: {db_path.name}")
        return True
    except Exception as e:
        log.warning(f"  WAL checkpoint failed for {db_path.name}: {e}")
        return False


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 of a file."""
    h = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def verify_backup(backup_path: Path) -> Dict:
    """Verify backup integrity."""
    result = {"path": str(backup_path), "status": "unknown"}

    if not backup_path.exists():
        result["status"] = "missing"
        return result

    try:
        conn = sqlite3.connect(str(backup_path), timeout=30)
        check = conn.execute("PRAGMA integrity_check").fetchone()
        table_count = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
        ).fetchone()[0]
        conn.close()

        result["integrity"] = check[0]
        result["tables"] = table_count
        result["size_mb"] = round(backup_path.stat().st_size / (1024 * 1024), 2)
        result["status"] = "ok" if check[0] == "ok" else "corrupt"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def backup_database(db_path: Path, dest_dir: Path, label: str) -> Optional[Dict]:
    """Backup a single database file with verification."""
    if not db_path.exists():
        log.info(f"  Skipping {db_path.name} (not found)")
        return None

    dest_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{db_path.stem}_{label}_{timestamp}.db"
    backup_path = dest_dir / backup_name

    log.info(f"  Backing up: {db_path.name} ({db_path.stat().st_size / (1024**3):.2f} GB)")

    # WAL checkpoint first
    wal_checkpoint(db_path)

    # Copy
    try:
        shutil.copy2(str(db_path), str(backup_path))
    except Exception as e:
        log.error(f"  Copy failed: {e}")
        return None

    # Verify
    check = verify_backup(backup_path)
    if check["status"] != "ok":
        log.error(f"  ⚠ INTEGRITY CHECK FAILED: {check}")
        return None

    # Hash
    sha256 = compute_sha256(backup_path)

    entry = {
        "timestamp": timestamp,
        "label": label,
        "source": str(db_path),
        "backup_path": str(backup_path),
        "size_mb": check["size_mb"],
        "tables": check["tables"],
        "sha256": sha256,
        "integrity": "ok",
    }

    log.info(f"  ✓ {backup_name} ({check['size_mb']} MB, {check['tables']} tables)")
    return entry


# ── Rotation Policy ────────────────────────────────────────────────────

def classify_backup_age(backup_entry: Dict) -> str:
    """Classify a backup as daily/weekly/monthly based on age."""
    ts = datetime.strptime(backup_entry["timestamp"], "%Y%m%d_%H%M%S")
    age = datetime.now() - ts

    if age.days < 7:
        return "daily"
    elif age.days < 30:
        return "weekly"
    else:
        return "monthly"


def apply_rotation(manifest: Dict, db_name: str):
    """Apply retention policy: keep N daily, N weekly, N monthly."""
    relevant = [b for b in manifest["backups"] if Path(b["source"]).stem == db_name]
    relevant.sort(key=lambda x: x["timestamp"], reverse=True)

    daily = [b for b in relevant if classify_backup_age(b) == "daily"]
    weekly = [b for b in relevant if classify_backup_age(b) == "weekly"]
    monthly = [b for b in relevant if classify_backup_age(b) == "monthly"]

    # Determine what to keep
    keep = set()
    for b in daily[:KEEP_DAILY]:
        keep.add(b["backup_path"])
    for b in weekly[:KEEP_WEEKLY]:
        keep.add(b["backup_path"])
    for b in monthly[:KEEP_MONTHLY]:
        keep.add(b["backup_path"])

    # Delete excess
    removed = 0
    for b in relevant:
        if b["backup_path"] not in keep:
            bp = Path(b["backup_path"])
            if bp.exists():
                # Move to I:\Recycle rather than hard delete
                recycle = BACKUP_ROOT / "_recycled"
                recycle.mkdir(exist_ok=True)
                try:
                    shutil.move(str(bp), str(recycle / bp.name))
                    removed += 1
                except Exception as e:
                    log.warning(f"  Could not recycle {bp.name}: {e}")

    # Update manifest
    manifest["backups"] = [
        b for b in manifest["backups"]
        if b["backup_path"] in keep or Path(b["source"]).stem != db_name
    ]

    if removed:
        log.info(f"  Rotated {removed} old backups for {db_name} (moved to _recycled/)")


# ── Main Backup Run ────────────────────────────────────────────────────

def run_backup():
    """Execute full backup with rotation."""
    log.info("=" * 60)
    log.info("LitigationOS Backup — Rotation Engine")
    log.info("=" * 60)

    manifest = load_manifest()
    now = datetime.now()
    label = "daily"

    # Determine if this is a weekly or monthly backup
    if manifest.get("last_weekly"):
        last_weekly = datetime.fromisoformat(manifest["last_weekly"])
        if (now - last_weekly).days >= 7:
            label = "weekly"
    else:
        label = "weekly"

    if manifest.get("last_monthly"):
        last_monthly = datetime.fromisoformat(manifest["last_monthly"])
        if (now - last_monthly).days >= 30:
            label = "monthly"
    else:
        label = "monthly"

    log.info(f"Backup type: {label.upper()}")
    log.info(f"Destination: {BACKUP_ROOT}")

    # Ensure backup root exists
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

    # 1. Backup main database
    log.info("\n── Main Database ──")
    entry = backup_database(DB_PATH, BACKUP_ROOT / "main", label)
    if entry:
        manifest["backups"].append(entry)

    # 2. Backup lane databases
    log.info("\n── Lane Databases ──")
    for lane_db in LANE_DBS:
        entry = backup_database(lane_db, BACKUP_ROOT / "lanes", label)
        if entry:
            manifest["backups"].append(entry)

    # 3. Apply rotation
    log.info("\n── Rotation ──")
    apply_rotation(manifest, "litigation_context")
    for lane_db in LANE_DBS:
        if lane_db.exists():
            apply_rotation(manifest, lane_db.stem)

    # 4. Update manifest
    manifest[f"last_{label}"] = now.isoformat()
    if label in ("weekly", "monthly"):
        manifest["last_daily"] = now.isoformat()
    save_manifest(manifest)

    # 5. Summary
    total_size = sum(
        b.get("size_mb", 0) for b in manifest["backups"]
        if Path(b["backup_path"]).exists()
    )
    log.info(f"\n✓ Backup complete: {len(manifest['backups'])} total backups, {total_size:.1f} MB")


def show_status():
    """Show current backup inventory."""
    manifest = load_manifest()
    print(f"\n{'='*60}")
    print(f"BACKUP INVENTORY — {BACKUP_ROOT}")
    print(f"{'='*60}")
    print(f"Total entries: {len(manifest['backups'])}")
    print(f"Last daily:   {manifest.get('last_daily', 'never')}")
    print(f"Last weekly:  {manifest.get('last_weekly', 'never')}")
    print(f"Last monthly: {manifest.get('last_monthly', 'never')}")

    if manifest["backups"]:
        print(f"\n{'Timestamp':<20} {'Label':<10} {'Source':<30} {'Size MB':<10} {'Status'}")
        print("-" * 90)
        for b in sorted(manifest["backups"], key=lambda x: x["timestamp"], reverse=True):
            source = Path(b["source"]).stem
            exists = "✓" if Path(b["backup_path"]).exists() else "✗ MISSING"
            print(f"{b['timestamp']:<20} {b['label']:<10} {source:<30} {b.get('size_mb', '?'):<10} {exists}")


def verify_all():
    """Verify all existing backups."""
    manifest = load_manifest()
    print(f"\nVerifying {len(manifest['backups'])} backups...")
    ok = 0
    bad = 0
    for b in manifest["backups"]:
        bp = Path(b["backup_path"])
        if bp.exists():
            result = verify_backup(bp)
            status = "✓" if result["status"] == "ok" else f"✗ {result['status']}"
            print(f"  {bp.name}: {status}")
            if result["status"] == "ok":
                ok += 1
            else:
                bad += 1
        else:
            print(f"  {bp.name}: ✗ MISSING")
            bad += 1
    print(f"\n{ok} OK, {bad} issues")


# ── CLI ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="LitigationOS Backup Rotation")
    parser.add_argument('--schedule', action='store_true', help='Install Windows scheduled task')
    parser.add_argument('--status', action='store_true', help='Show backup inventory')
    parser.add_argument('--verify-all', action='store_true', help='Verify all backups')
    args = parser.parse_args()

    if args.status:
        show_status()
    elif args.verify_all:
        verify_all()
    elif args.schedule:
        print("To schedule daily backups, run in an elevated PowerShell:")
        print(f'  schtasks /create /tn "LitigationOS_Backup" /tr '
              f'"python {__file__}" /sc daily /st 03:00 /f')
    else:
        run_backup()
