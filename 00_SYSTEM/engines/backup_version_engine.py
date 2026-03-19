#!/usr/bin/env python3
"""Backup & Versioning Engine v1.0 - Scheduled DB snapshots and file versioning."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import sqlite3
import os
import shutil
import hashlib
import json
from pathlib import Path
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

LITOS_ROOT = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = LITOS_ROOT / "litigation_context.db"
BACKUP_DIR = LITOS_ROOT / "00_SYSTEM" / "backups"
MAX_BACKUPS = 5  # Keep last 5 backups

class BackupVersionEngine:
    def __init__(self):
        """Initialize backup and versioning engine."""
        try:
            BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error("Failed to create backup directory: %s", e)
        self.manifest = self._load_manifest()
    
    def _load_manifest(self):
        """Load the backup manifest from disk.
        
        Returns:
            dict: Manifest data, or default empty manifest on failure.
        """
        manifest_path = BACKUP_DIR / "backup_manifest.json"
        if manifest_path.exists():
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError, OSError) as e:
                logger.error("Failed to load manifest: %s", e)
        return {"backups": [], "file_versions": {}}
    
    def _save_manifest(self):
        """Save the backup manifest to disk."""
        try:
            with open(BACKUP_DIR / "backup_manifest.json", 'w', encoding='utf-8') as f:
                json.dump(self.manifest, f, indent=2, default=str)
        except (IOError, OSError) as e:
            logger.error("Failed to save manifest: %s", e)
    
    def _file_hash(self, filepath):
        """Compute SHA-256 hash prefix for a file.
        
        Args:
            filepath: Path to the file.
            
        Returns:
            str: First 16 chars of SHA-256 hex digest, or 'ERROR' on failure.
        """
        try:
            h = hashlib.sha256()
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    h.update(chunk)
            return h.hexdigest()[:16]
        except (IOError, OSError) as e:
            logger.error("Failed to hash file %s: %s", filepath, e)
            return "ERROR_HASH"
    
    def backup_critical_files(self):
        """Backup critical filing stacks and configs.
        
        Returns:
            dict: Backup entry with timestamp, path, items, size_mb.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_subdir = BACKUP_DIR / f"backup_{timestamp}"
        backup_subdir.mkdir(parents=True, exist_ok=True)
        
        # Critical directories to backup
        critical_dirs = [
            "00_SYSTEM/engines",
            "00_SYSTEM/calendar",
            ".github",
            ".copilot/agents",
        ]
        
        # Critical individual files
        critical_files = [
            ".github/copilot-instructions.md",
            "00_SYSTEM/FILING_READINESS_AUDIT.md",
            "00_SYSTEM/PLACEHOLDER_MASTER_REPORT.md",
        ]
        
        backed_up = []
        
        for cdir in critical_dirs:
            src = LITOS_ROOT / cdir
            if src.exists():
                dst = backup_subdir / cdir
                try:
                    shutil.copytree(src, dst, dirs_exist_ok=True,
                                   ignore=shutil.ignore_patterns('*.pyc', '__pycache__', '*.lock'))
                    file_count = sum(1 for _ in dst.rglob('*') if _.is_file())
                    backed_up.append(f"{cdir} ({file_count} files)")
                except Exception as e:
                    backed_up.append(f"{cdir} (FAILED: {e})")
        
        for cfile in critical_files:
            src = LITOS_ROOT / cfile
            if src.exists():
                dst = backup_subdir / cfile
                dst.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.copy2(src, dst)
                    backed_up.append(cfile)
                except Exception as e:
                    backed_up.append(f"{cfile} (FAILED: {e})")
        
        # Calculate backup size
        total_size = sum(f.stat().st_size for f in backup_subdir.rglob('*') if f.is_file())
        
        entry = {
            "timestamp": timestamp,
            "path": str(backup_subdir),
            "items": backed_up,
            "size_mb": round(total_size / (1024*1024), 2),
        }
        self.manifest["backups"].append(entry)
        
        # Prune old backups
        self._prune_backups()
        self._save_manifest()
        
        return entry
    
    def _prune_backups(self):
        """Keep only MAX_BACKUPS most recent."""
        while len(self.manifest["backups"]) > MAX_BACKUPS:
            oldest = self.manifest["backups"].pop(0)
            old_path = Path(oldest["path"])
            if old_path.exists():
                try:
                    shutil.rmtree(old_path)
                except Exception as e:
                    logger.warning("Failed to remove old backup %s: %s", old_path, e)
    
    def version_filing_stacks(self):
        """Track versions of filing stack documents.
        
        Returns:
            list: Change descriptions (NEW or MODIFIED entries).
        """
        stacks = [
            "01_COA_366810",
            "02_TRIAL_14TH",
            "03_FEDERAL_1983",
            "04_MSC_ORIGINAL_ACTION",
            "06_EMERGENCY",
        ]
        
        changes = []
        for stack in stacks:
            stack_path = LITOS_ROOT / stack
            if not stack_path.exists():
                continue
            
            for f in stack_path.rglob("*.md"):
                rel = str(f.relative_to(LITOS_ROOT))
                current_hash = self._file_hash(f)
                
                prev = self.manifest["file_versions"].get(rel)
                if prev is None:
                    self.manifest["file_versions"][rel] = {
                        "hash": current_hash,
                        "first_seen": datetime.now().isoformat(),
                        "last_modified": datetime.now().isoformat(),
                        "versions": 1,
                    }
                    changes.append(f"NEW: {rel}")
                elif prev["hash"] != current_hash:
                    prev["hash"] = current_hash
                    prev["last_modified"] = datetime.now().isoformat()
                    prev["versions"] = prev.get("versions", 1) + 1
                    changes.append(f"MODIFIED: {rel} (v{prev['versions']})")
        
        self._save_manifest()
        return changes
    
    def generate_report(self):
        """Generate backup status report."""
        lines = []
        lines.append("=" * 60)
        lines.append("  BACKUP & VERSIONING REPORT")
        lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("=" * 60)
        lines.append("")
        
        lines.append(f"  Backups: {len(self.manifest['backups'])}")
        for b in self.manifest['backups']:
            lines.append(f"    {b['timestamp']} | {b['size_mb']}MB | {len(b['items'])} items")
        
        lines.append("")
        lines.append(f"  Tracked Files: {len(self.manifest['file_versions'])}")
        
        multi_version = {k: v for k, v in self.manifest['file_versions'].items() if v.get('versions', 1) > 1}
        if multi_version:
            lines.append(f"  Files with Multiple Versions: {len(multi_version)}")
            for k, v in sorted(multi_version.items(), key=lambda x: -x[1].get('versions', 1))[:10]:
                lines.append(f"    v{v['versions']}: {k}")
        
        lines.append("")
        lines.append("=" * 60)
        return "\n".join(lines)
    
    def run(self):
        """Execute full backup and versioning cycle.
        
        Returns:
            str: Backup report text, or error message on failure.
        """
        try:
            print("Starting backup...")
            backup = self.backup_critical_files()
            print(f"Backup complete: {backup['size_mb']}MB, {len(backup['items'])} items")
            
            print("Tracking file versions...")
            changes = self.version_filing_stacks()
            print(f"Version tracking: {len(changes)} changes detected")
            
            report = self.generate_report()
            print(report)
            
            # Save report
            try:
                with open(BACKUP_DIR / "BACKUP_REPORT.txt", 'w', encoding='utf-8') as f:
                    f.write(report)
            except (IOError, OSError) as e:
                logger.error("Failed to save backup report: %s", e)
            
            return report
        except Exception as e:
            logger.error("Backup engine failed: %s", e)
            return f"[ERROR] Backup engine failed: {e}"


if __name__ == "__main__":
    try:
        engine = BackupVersionEngine()
        engine.run()
    except Exception as e:
        logger.error("Backup version engine crashed: %s", e)
        print(f"[ERROR] Backup version engine crashed: {e}")
