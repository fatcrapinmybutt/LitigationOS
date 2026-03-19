"""
OMEGA Phase 2: Hash-Cluster Canonical Election
Identifies duplicate clusters and elects canonical files using priority rules.
"""
import sqlite3
import sys
import time
from pathlib import Path

from config import BUCKET_PRIORITY, get_cyclepack_dir
from safety import write_phase_checkpoint, is_phase_done


def score_path(file_path: str, depth: int, top_bucket: str) -> float:
    score = 100.0
    # Depth penalty: shallower = better
    score -= depth * 2.0
    # Bucket priority
    score += BUCKET_PRIORITY.get(top_bucket, 3) * 5.0
    # Path preference bonuses
    lp = file_path.lower()
    if "court_orders" in lp or "court_filings_final" in lp:
        score += 20
    elif "core_pdfs" in lp or "scanned_evidence" in lp:
        score += 15
    elif "sources" in lp or "extracts_full" in lp:
        score += 10
    elif "all_pc_evidence" in lp:
        score += 5
    # Penalize deeply nested evidence copies
    if "capstone" in lp and depth > 10:
        score -= 10
    return score


def run_dedup(cycle_dir: Path, dry_run: bool = False):
    db_path = cycle_dir / "inventory.db"
    if not db_path.exists():
        print("[PHASE2] inventory.db not found — run Phase 1 first", file=sys.stderr)
        if dry_run:
            print("[PHASE2] DRY RUN: would deduplicate files from inventory.db", file=sys.stderr)
            return
        sys.exit(1)

    if is_phase_done(cycle_dir, "phase2"):
        print("[PHASE2] Already complete, skipping", file=sys.stderr)
        return

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA journal_mode=WAL")

        # Create dedup table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS duplicate_clusters (
                sha256 TEXT PRIMARY KEY,
                total_copies INTEGER,
                canonical_path TEXT,
                canonical_id INTEGER,
                space_saved_mb REAL
            )
        """)

        start = time.time()
        print("[PHASE2] Finding duplicate clusters...", file=sys.stderr)

        # Find all duplicate SHA-256 clusters
        cursor = conn.execute("""
            SELECT sha256, COUNT(*) as cnt
            FROM files
            WHERE sha256 IS NOT NULL
            GROUP BY sha256
            HAVING cnt > 1
        """)
        clusters = cursor.fetchall()
        print(f"[PHASE2] Found {len(clusters):,} duplicate clusters", file=sys.stderr)

        total_saved_mb = 0.0
        canonical_count = 0

        for i, (sha, cnt) in enumerate(clusters):
            # Get all files in this cluster
            rows = conn.execute(
                "SELECT id, file_path, depth, top_bucket, size_bytes FROM files WHERE sha256 = ?",
                (sha,)
            ).fetchall()

            # Score each and pick canonical
            best_id = None
            best_score = -999
            file_size = rows[0][4] if rows else 0

            for rid, rpath, rdepth, rbucket, rsize in rows:
                s = score_path(rpath, rdepth, rbucket)
                if s > best_score:
                    best_score = s
                    best_id = rid
                    best_path = rpath

            if not dry_run:
                # Mark canonical
                conn.execute("UPDATE files SET is_canonical = 1, canonical_sha256 = ? WHERE id = ?", (sha, best_id))
                # Mark non-canonical
                for rid, rpath, rdepth, rbucket, rsize in rows:
                    if rid != best_id:
                        conn.execute("UPDATE files SET is_canonical = 0, canonical_sha256 = ? WHERE id = ?", (sha, rid))

                saved = file_size * (cnt - 1) / (1024 * 1024)
                total_saved_mb += saved
                conn.execute(
                    "INSERT OR REPLACE INTO duplicate_clusters VALUES (?, ?, ?, ?, ?)",
                    (sha, cnt, best_path, best_id, round(saved, 2))
                )
                canonical_count += 1

            if (i + 1) % 10000 == 0:
                conn.commit()
                print(f"[PHASE2] Processed {i+1:,}/{len(clusters):,} clusters", file=sys.stderr)

        # Mark all unique files (no duplicates) as canonical
        if not dry_run:
            conn.execute("""
                UPDATE files SET is_canonical = 1
                WHERE sha256 IS NOT NULL
                AND sha256 NOT IN (SELECT sha256 FROM duplicate_clusters)
            """)
            # Mark files with NULL hash as canonical (couldn't hash = keep them)
            conn.execute("UPDATE files SET is_canonical = 1 WHERE sha256 IS NULL")
            conn.commit()

        elapsed = time.time() - start

        # Stats
        total_files = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        canonical_total = conn.execute("SELECT COUNT(*) FROM files WHERE is_canonical = 1").fetchone()[0]

        print(f"\n[PHASE2] Dedup complete:", file=sys.stderr)
        print(f"  Total files:      {total_files:,}", file=sys.stderr)
        print(f"  Canonical files:  {canonical_total:,}", file=sys.stderr)
        print(f"  Duplicates:       {total_files - canonical_total:,}", file=sys.stderr)
        print(f"  Space saved:      {total_saved_mb:,.1f} MB", file=sys.stderr)
        print(f"  Reduction:        {100*(1 - canonical_total/max(total_files,1)):.1f}%", file=sys.stderr)
        print(f"  Elapsed:          {elapsed:.0f}s", file=sys.stderr)

        if not dry_run:
            import json
            stats = {
                "total_files": total_files,
                "canonical_files": canonical_total,
                "duplicate_clusters": len(clusters),
                "space_saved_mb": round(total_saved_mb, 1),
                "reduction_pct": round(100*(1 - canonical_total/max(total_files,1)), 1),
                "elapsed_seconds": round(elapsed, 1),
            }
            (cycle_dir / "dedup_stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
            write_phase_checkpoint(cycle_dir, "phase2", {"status": "done", "canonical": canonical_total, "elapsed": f"{elapsed:.0f}s"})
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Phase 2: Dedup")
    parser.add_argument("--cycle-ts", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    from config import CYCLE_TS
    ts = args.cycle_ts or CYCLE_TS
    run_dedup(get_cyclepack_dir(ts), args.dry_run)
