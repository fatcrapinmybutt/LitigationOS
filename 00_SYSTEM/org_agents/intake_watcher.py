"""
ORG-intake: IntakeWatcher Agent
Monitors _INBOX folder, auto-classifies new files, routes them to correct buckets.
Handles bulk drops (ZIP extraction, folder drops).
"""
import sys
import os
import time
import zipfile
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from __init__ import (
    sha256_file, content_preview, detect_lane, detect_doc_type,
    get_bucket, safe_move, index_db, state_db, log_audit, init_index_db,
    LITIGOS_ROOT, INDEX_DB_PATH,
)

INBOX = LITIGOS_ROOT / "_INBOX"
EVIDENCE_ROOT_C = LITIGOS_ROOT  # buckets live under LitigationOS on C:
EVIDENCE_ROOT_I = Path(r"I:\EVIDENCE")


class IntakeWatcher:
    """Process files dropped into _INBOX, classify, and route them."""

    def __init__(self, dry_run=False, target_drive="C"):
        self.dry_run = dry_run
        self.target_drive = target_drive
        self.stats = {"processed": 0, "skipped": 0, "errors": 0, "dupes": 0, "zips_extracted": 0}
        INBOX.mkdir(parents=True, exist_ok=True)

    def _route_path(self, bucket, filename):
        """Determine destination path based on bucket and target drive."""
        if self.target_drive == "I":
            return EVIDENCE_ROOT_I / bucket / filename
        return EVIDENCE_ROOT_C / bucket / filename

    def _extract_zips(self):
        """Extract any ZIP files in _INBOX to a subfolder, then process contents."""
        for zp in INBOX.glob("*.zip"):
            try:
                extract_dir = INBOX / zp.stem
                extract_dir.mkdir(exist_ok=True)
                with zipfile.ZipFile(str(zp), "r") as zf:
                    zf.extractall(str(extract_dir))
                # Move the zip itself to archive
                safe_move(zp, LITIGOS_ROOT / "ARCHIVE" / "zips" / zp.name, dry_run=self.dry_run)
                self.stats["zips_extracted"] += 1
                print(f"  📦 Extracted: {zp.name} → {extract_dir}")
            except (zipfile.BadZipFile, OSError) as e:
                print(f"  ⚠️ Bad ZIP: {zp.name}: {e}")
                self.stats["errors"] += 1

    def process_inbox(self):
        """Process all files currently in _INBOX."""
        sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")
        print(f"\n{'='*60}")
        print(f"  INTAKE WATCHER — Processing _INBOX")
        print(f"  Dry run: {self.dry_run} | Target: {self.target_drive}:\\")
        print(f"{'='*60}\n")

        # Extract ZIPs first
        self._extract_zips()

        # Collect all files (including from extracted ZIPs)
        files = list(INBOX.rglob("*"))
        files = [f for f in files if f.is_file()]
        print(f"  Found {len(files)} files to process\n")

        if not files:
            print("  _INBOX is empty. Nothing to do.")
            return self.stats

        init_index_db()

        with index_db() as conn:
            for i, filepath in enumerate(files):
                try:
                    self._process_file(conn, filepath, i + 1, len(files))
                except Exception as e:
                    print(f"  ❌ Error processing {filepath.name}: {e}")
                    self.stats["errors"] += 1

                if (i + 1) % 100 == 0:
                    conn.commit()
                    print(f"  ... checkpoint at {i+1}/{len(files)}")

            conn.commit()

        print(f"\n{'='*60}")
        print(f"  INTAKE COMPLETE")
        for k, v in self.stats.items():
            print(f"    {k:20s} = {v}")
        print(f"{'='*60}")
        return self.stats

    def _process_file(self, conn, filepath, idx, total):
        """Process a single file: hash → check dupe → classify → route."""
        filename = filepath.name
        ext = filepath.suffix.lower()
        size = filepath.stat().st_size

        # SHA-256
        file_hash = sha256_file(filepath)
        if not file_hash:
            self.stats["skipped"] += 1
            return

        file_id = file_hash[:16]

        # Check for duplicate in INDEX
        existing = conn.execute("SELECT path FROM files WHERE sha256 = ?", (file_hash,)).fetchone()
        if existing:
            print(f"  [{idx}/{total}] DUPE: {filename} → already at {existing[0]}")
            self.stats["dupes"] += 1
            # Move dupe to dedup folder
            safe_move(filepath, LITIGOS_ROOT / "DEDUP_VERIFIED" / filename, dry_run=self.dry_run)
            return

        # Classify
        bucket = get_bucket(filepath)
        preview = content_preview(filepath, 500)
        lane = detect_lane(preview) if preview else None
        doc_type = detect_doc_type(preview, filename) if preview else "unknown"

        # Route
        dest = self._route_path(bucket, filename)
        moved, result = safe_move(filepath, dest, dry_run=self.dry_run)

        if moved:
            actual_dest = result if not self.dry_run else str(dest)
            drive = actual_dest[0] if len(actual_dest) > 1 else "C"

            conn.execute(
                """INSERT OR REPLACE INTO files 
                   (id, path, filename, extension, bucket, tier, drive, size_bytes, sha256,
                    case_lane, doc_type, content_preview, original_path, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (file_id, actual_dest, filename, ext, bucket, "hot", drive, size,
                 file_hash, lane, doc_type, preview, str(filepath), "indexed"),
            )

            conn.execute(
                """INSERT INTO migrations (file_id, from_path, to_path, from_drive, to_drive, action, reason, agent_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (file_id, str(filepath), actual_dest, "C", drive, "intake", "auto-classified from _INBOX", "ORG-intake"),
            )

            action = "ROUTE" if not self.dry_run else "WOULD_ROUTE"
            print(f"  [{idx}/{total}] {action}: {filename} → {bucket}/ (lane={lane}, type={doc_type})")
            self.stats["processed"] += 1
        else:
            print(f"  [{idx}/{total}] FAIL: {filename}: {result}")
            self.stats["errors"] += 1


def main():
    import argparse
    parser = argparse.ArgumentParser(description="IntakeWatcher: Process _INBOX files")
    parser.add_argument("--dry-run", action="store_true", help="Preview without moving files")
    parser.add_argument("--target", default="C", choices=["C", "I"], help="Target drive for routed files")
    args = parser.parse_args()

    watcher = IntakeWatcher(dry_run=args.dry_run, target_drive=args.target)
    stats = watcher.process_inbox()

    with state_db() as conn:
        log_audit(conn, "intake_run", "_INBOX",
                  f"processed={stats['processed']}, dupes={stats['dupes']}, errors={stats['errors']}",
                  "ORG-intake", "omega-v5.0")


if __name__ == "__main__":
    main()
