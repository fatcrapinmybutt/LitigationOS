"""
OMEGA Phase 0A: Safety Snapshot System
IRON RULE: Nothing in LITIGATIONOS_MASTER gets modified until a verified backup exists.
"""
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

from config import (
    MASTER_ROOT, BACKUPS_DIR, MASTER_MODIFIABLE, LEXOS_BIBLE,
    sha256_file, long_path,
)


def create_snapshot(cycle_ts: str | None = None) -> Path:
    ts = cycle_ts or datetime.now().strftime("%Y%m%d_%H%M%S")
    snap_dir = BACKUPS_DIR / f"SNAPSHOT_{ts}"
    snap_dir.mkdir(parents=True, exist_ok=True)
    originals_dir = snap_dir / "originals"
    originals_dir.mkdir(exist_ok=True)

    print(f"[SAFETY] Creating snapshot at {snap_dir}", file=sys.stderr)

    # 1. SHA-256 manifest of entire LITIGATIONOS_MASTER
    manifest = {}
    file_count = 0
    for f in MASTER_ROOT.rglob("*"):
        if f.is_file() and "backups" not in f.parts and "cyclepacks" not in f.parts:
            try:
                rel = f.relative_to(MASTER_ROOT)
                manifest[str(rel)] = {
                    "sha256": sha256_file(f),
                    "size": f.stat().st_size,
                    "mtime": f.stat().st_mtime,
                }
                file_count += 1
            except (PermissionError, OSError):
                pass
    
    manifest_path = snap_dir / "manifest.sha256.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[SAFETY] Manifest: {file_count} files hashed", file=sys.stderr)

    # 2. Copy all modifiable master files
    copied = 0
    for fname in MASTER_MODIFIABLE:
        src = MASTER_ROOT / fname
        if src.exists():
            dst = originals_dir / fname
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src), str(dst))
            copied += 1

    # 3. Copy LEXOS brain nuclei
    brains_dir = LEXOS_BIBLE / "brains"
    if brains_dir.exists():
        brains_dst = originals_dir / "lexos_bible" / "brains"
        brains_dst.mkdir(parents=True, exist_ok=True)
        for brain_file in brains_dir.glob("brain_*.json"):
            shutil.copy2(str(brain_file), str(brains_dst / brain_file.name))
            copied += 1

    print(f"[SAFETY] Copied {copied} modifiable files to originals/", file=sys.stderr)

    # 4. Integrity check — verify every copied file
    errors = []
    for f in originals_dir.rglob("*"):
        if f.is_file():
            rel = f.relative_to(originals_dir)
            src = MASTER_ROOT / rel
            if src.exists():
                src_hash = sha256_file(src)
                dst_hash = sha256_file(f)
                if src_hash != dst_hash:
                    errors.append(str(rel))

    if errors:
        print(f"[SAFETY] ABORT — integrity check failed for: {errors}", file=sys.stderr)
        sys.exit(1)

    # 5. Write snapshot lock
    lock_data = {
        "timestamp": ts,
        "files_hashed": file_count,
        "files_copied": copied,
        "integrity_verified": True,
        "created_at": datetime.now().isoformat(),
    }
    lock_path = snap_dir / "snapshot.lock"
    lock_path.write_text(json.dumps(lock_data, indent=2), encoding="utf-8")

    print(f"[SAFETY] Snapshot LOCKED: {snap_dir}", file=sys.stderr)
    return snap_dir


def verify_snapshot_exists(snap_dir: Path) -> bool:
    lock = snap_dir / "snapshot.lock"
    if not lock.exists():
        print(f"[SAFETY] No snapshot.lock at {snap_dir} — refusing to run pipeline", file=sys.stderr)
        return False
    data = json.loads(lock.read_text(encoding="utf-8"))
    if not data.get("integrity_verified"):
        print(f"[SAFETY] Snapshot integrity NOT verified — refusing to run", file=sys.stderr)
        return False
    return True


def write_phase_checkpoint(cycle_dir: Path, phase: str, data: dict):
    cp_dir = cycle_dir / "checkpoints"
    cp_dir.mkdir(parents=True, exist_ok=True)
    cp_path = cp_dir / f"{phase}_complete.json"
    data["completed_at"] = datetime.now().isoformat()
    cp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"[CHECKPOINT] Phase {phase} complete", file=sys.stderr)


def is_phase_done(cycle_dir: Path, phase: str) -> bool:
    cp = cycle_dir / "checkpoints" / f"{phase}_complete.json"
    if cp.exists():
        data = json.loads(cp.read_text(encoding="utf-8"))
        return data.get("status") == "done"
    return False


def write_touchlog(cycle_dir: Path, phase: str, path: str, action: str,
                   sha_before: str | None = None, sha_after: str | None = None):
    log_path = cycle_dir / f"touchlog_{phase}.jsonl"
    entry = {
        "path": path,
        "action": action,
        "sha_before": sha_before,
        "sha_after": sha_after,
        "timestamp": datetime.now().isoformat(),
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Create safety snapshot")
    parser.add_argument("--cycle-ts", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        print("[SAFETY] DRY RUN — would create snapshot but not writing")
        sys.exit(0)

    snap = create_snapshot(args.cycle_ts)
    print(f"Snapshot created: {snap}")
