"""
_omega_flatten.py — Flatten 8 court-action filing dirs into 01_FILINGS/ structure.
Usage:
    python _omega_flatten.py --dry-run   (default, preview only)
    python _omega_flatten.py --live       (execute moves)
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import shutil
import sqlite3
import argparse
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(r'C:\Users\andre\LitigationOS')
DB_PATH = BASE / '00_SYSTEM' / 'manifests' / 'omega_dedup.db'

FLATTEN_MAP = {
    '01_COA_366810':        '01_FILINGS/COA_366810',
    '02_TRIAL_14TH':        '01_FILINGS/TRIAL_14TH',
    '03_FEDERAL_1983':      '01_FILINGS/FEDERAL_1983',
    '04_JTC_MCNEILL':       '01_FILINGS/JTC_MCNEILL',
    '04_MSC_ORIGINAL_ACTION': '01_FILINGS/MSC_ACTION',
    '05_BAR_BARNES':        '01_FILINGS/BAR_BARNES',
    '06_EMERGENCY':         '01_FILINGS/EMERGENCY',
    '06_FILINGS':           '01_FILINGS/ADMIN',
}


def resolve_conflict(dest_dir: Path, filename: str) -> Path:
    """If dest_dir/filename exists, append _2, _3, … before the extension."""
    candidate = dest_dir / filename
    if not candidate.exists():
        return candidate
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    counter = 2
    while True:
        candidate = dest_dir / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def flatten(live: bool):
    mode = "LIVE" if live else "DRY-RUN"
    print(f"═══ OMEGA FLATTEN — {mode} ═══\n")

    conn = None
    if live:
        conn = sqlite3.connect(str(DB_PATH), timeout=120)
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("PRAGMA journal_mode=WAL")

    total_moved = 0
    total_skipped = 0
    total_conflicts = 0
    total_bytes = 0
    empty_dirs_removed = 0

    for src_name, dest_rel in FLATTEN_MAP.items():
        src_dir = BASE / src_name
        dest_dir = BASE / dest_rel

        if not src_dir.exists():
            print(f"  SKIP  {src_name}/ — does not exist")
            continue

        if live:
            dest_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n── {src_name}/  →  {dest_rel}/")

        dir_moved = 0
        dir_conflicts = 0

        for root, dirs, files in os.walk(str(src_dir)):
            for fname in files:
                src_file = Path(root) / fname

                if not src_file.exists():
                    total_skipped += 1
                    continue

                file_size = src_file.stat().st_size
                dest_file = resolve_conflict(dest_dir, fname)

                if dest_file.name != fname:
                    dir_conflicts += 1
                    total_conflicts += 1

                if live:
                    ts = datetime.now(timezone.utc).isoformat()
                    rollback = f'shutil.move(r"{dest_file}", r"{src_file}")'
                    try:
                        shutil.move(str(src_file), str(dest_file))
                        conn.execute(
                            "INSERT INTO move_log (timestamp, operation, source_path, dest_path, file_size, rollback_cmd, status) "
                            "VALUES (?, 'flatten', ?, ?, ?, ?, 'completed')",
                            (ts, str(src_file), str(dest_file), file_size, rollback)
                        )
                    except Exception as e:
                        conn.execute(
                            "INSERT INTO move_log (timestamp, operation, source_path, dest_path, file_size, rollback_cmd, status) "
                            "VALUES (?, 'flatten', ?, ?, ?, ?, ?)",
                            (ts, str(src_file), str(dest_file), file_size, rollback, f'error: {e}')
                        )
                        print(f"    ERROR: {src_file} — {e}")
                        total_skipped += 1
                        continue

                total_moved += 1
                total_bytes += file_size
                dir_moved += 1

                if total_moved % 500 == 0:
                    print(f"    … {total_moved} files processed …")

        print(f"    {dir_moved} files  ({dir_conflicts} renames)")

    # Clean up empty source directories
    if live:
        print("\n── Cleaning empty source directories …")
        for src_name in FLATTEN_MAP:
            src_dir = BASE / src_name
            if not src_dir.exists():
                continue
            # Walk bottom-up to remove empty dirs
            for root, dirs, files in os.walk(str(src_dir), topdown=False):
                for d in dirs:
                    dp = Path(root) / d
                    try:
                        if dp.exists() and not any(dp.iterdir()):
                            dp.rmdir()
                            empty_dirs_removed += 1
                    except OSError:
                        pass
            # Remove the source root if empty
            try:
                if src_dir.exists() and not any(src_dir.iterdir()):
                    src_dir.rmdir()
                    empty_dirs_removed += 1
                    print(f"    Removed empty: {src_name}/")
                else:
                    remaining = sum(1 for _ in src_dir.rglob('*') if _.is_file())
                    if remaining:
                        print(f"    Kept {src_name}/ — {remaining} files remain")
            except OSError:
                pass

        conn.commit()
        conn.close()

    mb = total_bytes / (1024 * 1024)
    print(f"\n{'═' * 50}")
    print(f"  Mode:              {mode}")
    print(f"  Files processed:   {total_moved}")
    print(f"  Renames (conflicts): {total_conflicts}")
    print(f"  Skipped/errors:    {total_skipped}")
    print(f"  Data moved:        {mb:,.1f} MB")
    if live:
        print(f"  Empty dirs removed: {empty_dirs_removed}")
    print(f"{'═' * 50}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Flatten filing directories into 01_FILINGS/')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--dry-run', action='store_true', default=True, help='Preview only (default)')
    group.add_argument('--live', action='store_true', help='Execute moves')
    args = parser.parse_args()

    flatten(live=args.live)
