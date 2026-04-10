"""Archive dist/ and build/ from C:/LitigationOS to J:/LitigationOS_CENTRAL/ARCHIVE/.

Copies src -> dst, verifies file counts match, then removes source dirs.
Frees ~1.73 GB on the C:\\ NVMe SSD.
"""
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(r"C:\Users\andre\LitigationOS")
ARCHIVE_ROOT = Path(r"J:\LitigationOS_CENTRAL\ARCHIVE")

DIRS_TO_ARCHIVE = [
    REPO_ROOT / "dist",
    REPO_ROOT / "build",
]


def count_files(path: Path) -> int:
    return sum(1 for _ in path.rglob("*") if _.is_file())


def count_bytes(path: Path) -> int:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def fmt_mb(n: int) -> str:
    return f"{n / 1024 / 1024:.1f} MB"


def archive_dir(src: Path, archive_root: Path, dry_run: bool = False) -> bool:
    if not src.exists():
        print(f"[SKIP] {src} does not exist — already removed or never created")
        return True

    dst = archive_root / src.name
    src_count = count_files(src)
    src_bytes = count_bytes(src)
    print(f"\n[ARCHIVE] {src}")
    print(f"  Files: {src_count}, Size: {fmt_mb(src_bytes)}")
    print(f"  Destination: {dst}")

    if dry_run:
        print("  [DRY RUN] Would copy and delete")
        return True

    # Create archive root if needed
    archive_root.mkdir(parents=True, exist_ok=True)

    # If dst already exists, remove it first (prior partial archive)
    if dst.exists():
        print(f"  [NOTE] Destination exists — removing old archive first")
        shutil.rmtree(dst)

    # Copy
    print(f"  Copying {src_count} files...")
    shutil.copytree(src, dst)

    # Verify
    dst_count = count_files(dst)
    if dst_count != src_count:
        print(f"  [FAIL] Copy verification failed: src={src_count} dst={dst_count}")
        return False

    print(f"  [VERIFIED] {dst_count}/{src_count} files copied correctly")

    # Remove source
    shutil.rmtree(src)
    print(f"  [DELETED] Source removed: {src}")
    return True


def main():
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("[DRY RUN MODE] No files will be moved\n")

    if not ARCHIVE_ROOT.parent.exists():
        print(f"[ERROR] J:\\ drive not mounted or ARCHIVE root parent missing: {ARCHIVE_ROOT.parent}")
        sys.exit(1)

    print("=" * 60)
    print("ARCHIVE DIST + BUILD")
    print("=" * 60)

    freed = 0
    success_count = 0

    for src in DIRS_TO_ARCHIVE:
        if src.exists():
            freed += count_bytes(src)

    print(f"Space to reclaim: {fmt_mb(freed)}")

    for src in DIRS_TO_ARCHIVE:
        ok = archive_dir(src, ARCHIVE_ROOT, dry_run=dry_run)
        if ok:
            success_count += 1

    print(f"\n[DONE] {success_count}/{len(DIRS_TO_ARCHIVE)} directories archived")
    print(f"Space freed: ~{fmt_mb(freed)}")

    # Show current C:\ free space
    try:
        import shutil as sh
        usage = sh.disk_usage(str(REPO_ROOT.drive) + "\\")
        print(f"C:\\ free space now: {fmt_mb(usage.free)}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
