"""
OMEGA Phase 0E: Post-Pipeline Validation
Verifies nothing was corrupted during pipeline execution.
"""
import json
import sys
from pathlib import Path

from config import MASTER_ROOT, BACKUPS_DIR, sha256_file


def validate(snapshot_name: str) -> dict:
    snap_dir = BACKUPS_DIR / snapshot_name
    manifest_path = snap_dir / "manifest.sha256.json"
    originals = snap_dir / "originals"

    if not manifest_path.exists():
        print(f"[VALIDATE] No manifest at {manifest_path}", file=sys.stderr)
        sys.exit(1)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    
    modified = []
    deleted = []
    new_files = []
    backup_verified = []
    orphan_mods = []  # modified but no backup

    # 1. Check every file from original manifest
    for rel_path, info in manifest.items():
        full = MASTER_ROOT / rel_path
        if not full.exists():
            deleted.append(rel_path)
        else:
            current_hash = sha256_file(full)
            if current_hash != info["sha256"]:
                modified.append(rel_path)
                # Check if backup exists
                backup = originals / rel_path
                if backup.exists():
                    backup_verified.append(rel_path)
                else:
                    orphan_mods.append(rel_path)

    # 2. Find new files (not in original manifest)
    for f in MASTER_ROOT.rglob("*"):
        if f.is_file() and "backups" not in f.parts:
            rel = str(f.relative_to(MASTER_ROOT))
            if rel not in manifest:
                new_files.append(rel)

    # 3. Determine PASS/WARN/FAIL
    status = "PASS"
    warnings = []
    failures = []

    if deleted:
        failures.append(f"{len(deleted)} files DELETED (pipeline should NEVER delete)")
        status = "FAIL"

    if orphan_mods:
        failures.append(f"{len(orphan_mods)} files modified WITHOUT backup")
        status = "FAIL"

    if modified:
        warnings.append(f"{len(modified)} files modified (expected for merge phases)")

    if new_files:
        # Check they're all in expected locations
        unexpected = [f for f in new_files if not (
            "cyclepacks" in f or "backups" in f
        )]
        if unexpected:
            warnings.append(f"{len(unexpected)} new files outside cyclepacks/backups")

    if not failures and warnings:
        status = "WARN"

    report = {
        "status": status,
        "snapshot": snapshot_name,
        "original_file_count": len(manifest),
        "modified": len(modified),
        "deleted": len(deleted),
        "new_files": len(new_files),
        "backup_verified": len(backup_verified),
        "orphan_modifications": len(orphan_mods),
        "warnings": warnings,
        "failures": failures,
        "modified_files": modified[:50],
        "deleted_files": deleted[:50],
        "orphan_mod_files": orphan_mods[:50],
    }

    # Write report
    report_path = MASTER_ROOT / "cyclepacks" / "validation_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"\n{'='*60}", file=sys.stderr)
    print(f"  VALIDATION: {status}", file=sys.stderr)
    print(f"  Modified: {len(modified)} | Deleted: {len(deleted)} | New: {len(new_files)}", file=sys.stderr)
    if warnings:
        for w in warnings:
            print(f"  WARN: {w}", file=sys.stderr)
    if failures:
        for f in failures:
            print(f"  FAIL: {f}", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)

    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Validate pipeline integrity")
    parser.add_argument("--snapshot", required=True)
    args = parser.parse_args()
    validate(args.snapshot)
