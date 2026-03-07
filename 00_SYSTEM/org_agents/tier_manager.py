"""
ORG-tier: TierManager Agent
Promotes files from I:\\→C:\\ when referenced in active filings.
Demotes files from C:\\→I:\\ when >90 days untouched and not in active filings.
Maintains C:\\ ≥ 60 GB free target.
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))
from __init__ import (
    safe_move, index_db, state_db, log_audit, LITIGOS_ROOT,
)

C_FREE_TARGET_GB = 60  # Maintain at least 60 GB free on C:
COLD_THRESHOLD_DAYS = 90  # Files untouched for 90+ days are candidates for demotion
EVIDENCE_ROOT_I = Path(r"I:\EVIDENCE")


class TierManager:
    """Manage hot/cold tier placement across C:\\ and I:\\ drives."""

    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.stats = {
            "promoted": 0, "demoted": 0, "skipped_active": 0,
            "c_free_gb": 0.0, "i_free_gb": 0.0, "errors": 0,
        }

    def run(self):
        """Run tier management cycle."""
        sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")
        print(f"\n{'='*60}")
        print(f"  TIER MANAGER — Drive Space Optimization")
        print(f"  Dry run: {self.dry_run}")
        print(f"{'='*60}\n")

        self._check_drive_space()
        self._promote_active()
        self._demote_cold()
        self._check_drive_space()  # After changes

        print(f"\n{'='*60}")
        print(f"  TIER MANAGEMENT COMPLETE")
        for k, v in self.stats.items():
            if isinstance(v, float):
                print(f"    {k:20s} = {v:.1f}")
            else:
                print(f"    {k:20s} = {v}")
        print(f"{'='*60}")
        return self.stats

    def _check_drive_space(self):
        """Check free space on C:\\ and I:\\."""
        try:
            c_stat = os.statvfs("C:\\") if hasattr(os, "statvfs") else None
            if c_stat:
                self.stats["c_free_gb"] = (c_stat.f_bavail * c_stat.f_frsize) / (1024**3)
            else:
                import shutil
                c_total, c_used, c_free = shutil.disk_usage("C:\\")
                self.stats["c_free_gb"] = c_free / (1024**3)
        except Exception:
            self.stats["c_free_gb"] = -1

        try:
            if Path("I:\\").exists():
                import shutil
                i_total, i_used, i_free = shutil.disk_usage("I:\\")
                self.stats["i_free_gb"] = i_free / (1024**3)
            else:
                self.stats["i_free_gb"] = -1
        except Exception:
            self.stats["i_free_gb"] = -1

        print(f"  C:\\ free: {self.stats['c_free_gb']:.1f} GB  |  I:\\ free: {self.stats['i_free_gb']:.1f} GB")
        if self.stats["c_free_gb"] < C_FREE_TARGET_GB:
            print(f"  ⚠️ C:\\ below target ({C_FREE_TARGET_GB} GB) — demotion priority HIGH")

    def _promote_active(self):
        """Promote files from I:\\ to C:\\ if they are referenced by active filings."""
        print("\n  ── Promotion: I:\\ → C:\\ (active filing references) ──\n")

        with index_db() as conn:
            # Find files on I:\ that are linked to active filings
            candidates = conn.execute(
                """SELECT f.id, f.path, f.filename, f.bucket, f.size_bytes
                   FROM files f
                   JOIN file_links fl ON f.id = fl.target_id
                   JOIN files filing ON fl.source_id = filing.id
                   JOIN filing_tracker ft ON filing.id = ft.file_id
                   WHERE f.drive = 'I' AND f.tier = 'cold'
                   AND ft.status IN ('draft', 'review', 'final')
                   AND fl.link_type IN ('supports', 'exhibits')
                   ORDER BY f.size_bytes ASC
                   LIMIT 50""",
            ).fetchall()

            if not candidates:
                print("  No files need promotion.")
                return

            for row in candidates:
                f = dict(row)
                src = Path(f["path"])
                dst = LITIGOS_ROOT / f["bucket"] / f["filename"]

                moved, result = safe_move(src, dst, dry_run=self.dry_run)
                if moved:
                    actual_dst = result if not self.dry_run else str(dst)
                    conn.execute(
                        "UPDATE files SET path = ?, drive = 'C', tier = 'hot' WHERE id = ?",
                        (actual_dst, f["id"]),
                    )
                    conn.execute(
                        """INSERT INTO migrations (file_id, from_path, to_path, from_drive, to_drive, action, reason, agent_id)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (f["id"], str(src), actual_dst, "I", "C", "promote", "referenced by active filing", "ORG-tier"),
                    )
                    self.stats["promoted"] += 1
                    action = "PROMOTE" if not self.dry_run else "WOULD_PROMOTE"
                    print(f"  {action}: {f['filename'][:50]} → C:\\{f['bucket']}\\")

            conn.commit()

    def _demote_cold(self):
        """Demote files from C:\\ to I:\\ if they are old, large, and not in active filings."""
        print("\n  ── Demotion: C:\\ → I:\\ (cold files > 90 days) ──\n")

        # Only demote if C:\ is tight on space
        if self.stats["c_free_gb"] >= C_FREE_TARGET_GB:
            print(f"  C:\\ has {self.stats['c_free_gb']:.1f} GB free (≥ {C_FREE_TARGET_GB} GB target). Skipping demotion.")
            return

        if self.stats["i_free_gb"] < 5:
            print(f"  I:\\ has only {self.stats['i_free_gb']:.1f} GB free. Cannot demote to I:\\.")
            return

        cutoff = (datetime.now() - timedelta(days=COLD_THRESHOLD_DAYS)).isoformat()

        with index_db() as conn:
            # Find large C:\ files not in active filings, not recently classified
            candidates = conn.execute(
                """SELECT f.id, f.path, f.filename, f.bucket, f.size_bytes, f.case_lane
                   FROM files f
                   WHERE f.drive = 'C' AND f.tier = 'hot'
                   AND f.indexed_at < ?
                   AND f.size_bytes > 1000000
                   AND f.id NOT IN (
                       SELECT fl.target_id FROM file_links fl
                       JOIN files filing ON fl.source_id = filing.id
                       JOIN filing_tracker ft ON filing.id = ft.file_id
                       WHERE ft.status IN ('draft', 'review', 'final')
                   )
                   AND f.bucket NOT IN ('SYS', 'DB')
                   ORDER BY f.size_bytes DESC
                   LIMIT 100""",
                (cutoff,),
            ).fetchall()

            if not candidates:
                print("  No files eligible for demotion.")
                return

            demoted_bytes = 0
            target_bytes = (C_FREE_TARGET_GB - self.stats["c_free_gb"]) * (1024**3)

            for row in candidates:
                if demoted_bytes >= target_bytes:
                    break

                f = dict(row)
                lane_subdir = f["case_lane"] or "uncategorized"
                src = Path(f["path"])
                dst = EVIDENCE_ROOT_I / f["bucket"] / lane_subdir / f["filename"]

                moved, result = safe_move(src, dst, dry_run=self.dry_run)
                if moved:
                    actual_dst = result if not self.dry_run else str(dst)
                    conn.execute(
                        "UPDATE files SET path = ?, drive = 'I', tier = 'cold' WHERE id = ?",
                        (actual_dst, f["id"]),
                    )
                    conn.execute(
                        """INSERT INTO migrations (file_id, from_path, to_path, from_drive, to_drive, action, reason, agent_id)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (f["id"], str(src), actual_dst, "C", "I", "demote",
                         f"cold >{COLD_THRESHOLD_DAYS}d, not in active filing", "ORG-tier"),
                    )
                    demoted_bytes += f["size_bytes"] or 0
                    self.stats["demoted"] += 1
                    size_mb = (f["size_bytes"] or 0) / (1024 * 1024)
                    action = "DEMOTE" if not self.dry_run else "WOULD_DEMOTE"
                    print(f"  {action}: {f['filename'][:50]} ({size_mb:.1f} MB) → I:\\EVIDENCE\\{f['bucket']}\\")

            conn.commit()
            print(f"\n  Demoted {demoted_bytes / (1024**3):.2f} GB total")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="TierManager: Hot/Cold file tier management")
    parser.add_argument("--dry-run", action="store_true", help="Preview without moving files")
    args = parser.parse_args()

    mgr = TierManager(dry_run=args.dry_run)
    stats = mgr.run()

    with state_db() as conn:
        log_audit(conn, "tier_run", "drives",
                  f"promoted={stats['promoted']}, demoted={stats['demoted']}, c_free={stats['c_free_gb']:.1f}GB",
                  "ORG-tier", "omega-v5.0")


if __name__ == "__main__":
    main()
