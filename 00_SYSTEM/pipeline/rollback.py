"""
OMEGA Phase 0C: Rollback Script
One-command full revert to a safety snapshot.
"""
import json
import os
import shutil
import sys
from pathlib import Path

from config import MASTER_ROOT, BACKUPS_DIR, sha256_file


def rollback(snapshot_name: str, phase: str | None = None, dry_run: bool = False):
    snap_dir = BACKUPS_DIR / snapshot_name
    if not snap_dir.exists():
        print(f"[ROLLBACK] Snapshot not found: {snap_dir}", file=sys.stderr)
        sys.exit(1)

    lock = snap_dir / "snapshot.lock"
    if not lock.exists():
        print(f"[ROLLBACK] No snapshot.lock — snapshot may be invalid", file=sys.stderr)
        sys.exit(1)

    originals = snap_dir / "originals"
    manifest_path = snap_dir / "manifest.sha256.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    # If phase-specific rollback, use touchlog
    if phase:
        return _rollback_phase(snap_dir, originals, phase, manifest, dry_run)
    
    return _rollback_full(snap_dir, originals, manifest, dry_run)


def _rollback_full(snap_dir: Path, originals: Path, manifest: dict, dry_run: bool):
    restored = 0
    verified = 0
    removed = 0

    # 1. Restore all backed-up originals
    for f in originals.rglob("*"):
        if f.is_file():
            rel = f.relative_to(originals)
            dst = MASTER_ROOT / rel
            if dry_run:
                print(f"  [DRY] Would restore: {rel}")
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(f), str(dst))
            restored += 1

    # 2. Verify restored files match manifest
    for f in originals.rglob("*"):
        if f.is_file():
            rel = str(f.relative_to(originals)).replace("\\", "/")
            rel_win = str(f.relative_to(originals))
            entry = manifest.get(rel) or manifest.get(rel_win)
            if entry and not dry_run:
                dst = MASTER_ROOT / f.relative_to(originals)
                if sha256_file(dst) == entry["sha256"]:
                    verified += 1

    # 3. Remove new files created by pipeline (in cyclepacks)
    cyclepacks = MASTER_ROOT / "cyclepacks"
    if cyclepacks.exists():
        # Find cycles created AFTER this snapshot
        lock_data = json.loads((snap_dir / "snapshot.lock").read_text(encoding="utf-8"))
        snap_ts = lock_data["timestamp"]
        for cycle_dir in cyclepacks.iterdir():
            if cycle_dir.is_dir() and cycle_dir.name > f"CYCLE_{snap_ts}":
                if dry_run:
                    print(f"  [DRY] Would remove cycle: {cycle_dir.name}")
                else:
                    shutil.rmtree(str(cycle_dir))
                removed += 1

    action = "DRY RUN" if dry_run else "COMPLETE"
    print(f"[ROLLBACK {action}] Restored {restored}, verified {verified}, removed {removed} cycles")
    return {"restored": restored, "verified": verified, "removed": removed}


def _rollback_phase(snap_dir: Path, originals: Path, phase: str, manifest: dict, dry_run: bool):
    # Find the cycle that used this snapshot
    touchlogs = list(MASTER_ROOT.rglob(f"cyclepacks/*/touchlog_{phase}.jsonl"))
    if not touchlogs:
        print(f"[ROLLBACK] No touchlog found for phase {phase}", file=sys.stderr)
        return

    restored = 0
    for tlog in touchlogs:
        with open(tlog, "r", encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line)
                fpath = Path(entry["path"])
                rel = fpath.relative_to(MASTER_ROOT) if str(fpath).startswith(str(MASTER_ROOT)) else None
                if rel:
                    backup = originals / rel
                    if backup.exists():
                        if dry_run:
                            print(f"  [DRY] Would restore: {rel}")
                        else:
                            shutil.copy2(str(backup), str(fpath))
                        restored += 1
                    elif entry["action"] == "create":
                        if dry_run:
                            print(f"  [DRY] Would remove: {fpath}")
                        elif fpath.exists():
                            fpath.unlink()

    print(f"[ROLLBACK phase={phase}] Restored {restored} files")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Rollback to snapshot")
    parser.add_argument("--snapshot", required=True, help="Snapshot name e.g. SNAPSHOT_20260221_123456")
    parser.add_argument("--phase", default=None, help="Rollback specific phase only")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    rollback(args.snapshot, args.phase, args.dry_run)
