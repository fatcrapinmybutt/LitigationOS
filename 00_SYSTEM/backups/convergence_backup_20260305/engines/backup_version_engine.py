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

LITOS_ROOT = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = LITOS_ROOT / "litigation_context.db"
BACKUP_DIR = LITOS_ROOT / "00_SYSTEM" / "backups"
MAX_BACKUPS = 5  # Keep last 5 backups

class BackupVersionEngine:
    def __init__(self):
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        self.manifest = self._load_manifest()
    
    def _load_manifest(self):
        manifest_path = BACKUP_DIR / "backup_manifest.json"
        if manifest_path.exists():
            with open(manifest_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"backups": [], "file_versions": {}}
    
    def _save_manifest(self):
        with open(BACKUP_DIR / "backup_manifest.json", 'w', encoding='utf-8') as f:
            json.dump(self.manifest, f, indent=2, default=str)
    
    def _file_hash(self, filepath):
        h = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        return h.hexdigest()[:16]
    
    def backup_critical_files(self):
        """Backup critical filing stacks and configs."""
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
                except:
                    pass
    
    def version_filing_stacks(self):
        """Track versions of filing stack documents."""
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
        print("Starting backup...")
        backup = self.backup_critical_files()
        print(f"Backup complete: {backup['size_mb']}MB, {len(backup['items'])} items")
        
        print("Tracking file versions...")
        changes = self.version_filing_stacks()
        print(f"Version tracking: {len(changes)} changes detected")
        
        report = self.generate_report()
        print(report)
        
        # Save report
        with open(BACKUP_DIR / "BACKUP_REPORT.txt", 'w', encoding='utf-8') as f:
            f.write(report)
        
        return report


if __name__ == "__main__":
    engine = BackupVersionEngine()
    engine.run()
