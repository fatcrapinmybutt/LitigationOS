"""
ORG-dedup: ContentDedup Agent
Three-phase dedup: SHA-256 exact → Jaccard preview → deep content comparison.
Selects canonical (newest + most complete). Moves dupes to I:\\DEDUP_VERIFIED\\.
User mandate: NO hashing-only dedup. Must open and compare actual content.
"""
import sys
import os
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from __init__ import (
    sha256_file, content_preview, safe_move, index_db, state_db, log_audit,
    LITIGOS_ROOT,
)

DEDUP_DEST = Path(r"I:\DEDUP_VERIFIED")
SIMILARITY_THRESHOLD = 0.85  # Jaccard threshold for "near-dupe"
BATCH_SIZE = 500


def jaccard_similarity(text_a, text_b):
    """Compute Jaccard similarity between two text strings (word-level)."""
    if not text_a or not text_b:
        return 0.0
    words_a = set(text_a.lower().split())
    words_b = set(text_b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


def pick_canonical(files_info):
    """Select the canonical file from a group of duplicates.
    Priority: 1) On C:\\ drive (active), 2) Newest mtime, 3) Largest file."""
    scored = []
    for f in files_info:
        score = 0
        path = Path(f["path"])
        # Prefer C:\ (active working drive)
        if f.get("drive") == "C":
            score += 1000
        # Prefer newer modification time
        if path.exists():
            try:
                score += int(path.stat().st_mtime)
            except OSError:
                pass
        # Prefer larger (more complete)
        score += (f.get("size_bytes") or 0) / 1_000_000
        scored.append((score, f))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1] if scored else files_info[0]


class ContentDedup:
    """Content-based deduplication across INDEX.db."""

    def __init__(self, dry_run=False, batch_size=BATCH_SIZE):
        self.dry_run = dry_run
        self.batch_size = batch_size
        self.stats = {
            "phase1_exact": 0, "phase2_near": 0, "phase3_deep": 0,
            "dupes_found": 0, "dupes_moved": 0, "errors": 0,
            "clusters_created": 0,
        }
        DEDUP_DEST.mkdir(parents=True, exist_ok=True)

    def run(self):
        """Run all three dedup phases."""
        sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")
        print(f"\n{'='*60}")
        print(f"  CONTENT DEDUP — Three-Phase Analysis")
        print(f"  Dry run: {self.dry_run}")
        print(f"{'='*60}\n")

        self._phase1_exact_hash()
        self._phase2_near_match()
        # Phase 3 runs automatically on phase 2 candidates

        print(f"\n{'='*60}")
        print(f"  DEDUP COMPLETE")
        for k, v in self.stats.items():
            print(f"    {k:20s} = {v}")
        print(f"{'='*60}")
        return self.stats

    def _phase1_exact_hash(self):
        """Phase 1: Group files by identical SHA-256 hash."""
        print("  ── Phase 1: Exact SHA-256 Match ──\n")

        with index_db() as conn:
            # Find all SHA-256 hashes that appear more than once
            dupes = conn.execute(
                """SELECT sha256, COUNT(*) as cnt 
                   FROM files WHERE status NOT IN ('deduped','archived')
                   GROUP BY sha256 HAVING cnt > 1 
                   ORDER BY cnt DESC LIMIT ?""",
                (self.batch_size,),
            ).fetchall()

            if not dupes:
                print("  No exact hash duplicates found.")
                return

            print(f"  Found {len(dupes)} duplicate hash groups\n")

            for dupe_row in dupes:
                hash_val = dupe_row["sha256"]
                files = conn.execute(
                    "SELECT id, path, filename, drive, size_bytes, status FROM files WHERE sha256 = ? AND status NOT IN ('deduped','archived')",
                    (hash_val,),
                ).fetchall()

                if len(files) < 2:
                    continue

                files_info = [dict(f) for f in files]
                canonical = pick_canonical(files_info)
                cluster_id = f"exact_{hash_val[:12]}"

                for f in files_info:
                    is_canon = f["id"] == canonical["id"]
                    conn.execute(
                        "INSERT OR REPLACE INTO dedup_clusters (cluster_id, file_id, is_canonical, similarity_score) VALUES (?, ?, ?, ?)",
                        (cluster_id, f["id"], is_canon, 1.0),
                    )

                    if not is_canon:
                        self._move_dupe(conn, f, canonical, cluster_id, "exact_hash")

                self.stats["phase1_exact"] += len(files_info) - 1
                self.stats["clusters_created"] += 1

            conn.commit()

    def _phase2_near_match(self):
        """Phase 2: Jaccard similarity on content previews (same extension, similar size)."""
        print("\n  ── Phase 2: Near-Match (Jaccard on content preview) ──\n")

        with index_db() as conn:
            # Group by extension + similar size (within 20%)
            extensions = conn.execute(
                """SELECT DISTINCT extension FROM files 
                   WHERE status = 'classified' AND content_preview IS NOT NULL AND content_preview != ''
                   ORDER BY extension""",
            ).fetchall()

            for ext_row in extensions:
                ext = ext_row["extension"]
                files = conn.execute(
                    """SELECT id, path, filename, drive, size_bytes, content_preview 
                       FROM files WHERE extension = ? AND status = 'classified' 
                       AND content_preview IS NOT NULL AND content_preview != ''
                       ORDER BY size_bytes""",
                    (ext,),
                ).fetchall()

                if len(files) < 2:
                    continue

                files_list = [dict(f) for f in files]
                # Compare adjacent files (sorted by size — similar sizes are adjacent)
                for i in range(len(files_list)):
                    for j in range(i + 1, min(i + 10, len(files_list))):
                        a, b = files_list[i], files_list[j]
                        # Size filter: within 30% of each other
                        if a["size_bytes"] and b["size_bytes"]:
                            ratio = min(a["size_bytes"], b["size_bytes"]) / max(a["size_bytes"], b["size_bytes"])
                            if ratio < 0.7:
                                continue

                        sim = jaccard_similarity(a["content_preview"], b["content_preview"])
                        if sim >= SIMILARITY_THRESHOLD:
                            # Phase 3: Deep comparison for this pair
                            self._phase3_deep_compare(conn, a, b, sim)

            conn.commit()

    def _phase3_deep_compare(self, conn, file_a, file_b, preview_sim):
        """Phase 3: Open both files and compare actual content."""
        path_a, path_b = Path(file_a["path"]), Path(file_b["path"])
        if not path_a.exists() or not path_b.exists():
            return

        try:
            # Read full content (up to 10KB)
            full_a = content_preview(path_a, 10000)
            full_b = content_preview(path_b, 10000)

            if not full_a or not full_b:
                return

            deep_sim = jaccard_similarity(full_a, full_b)
            if deep_sim < SIMILARITY_THRESHOLD:
                return  # False positive — different enough

            # Confirmed near-dupe
            files_info = [file_a, file_b]
            canonical = pick_canonical(files_info)
            non_canonical = file_b if canonical["id"] == file_a["id"] else file_a
            cluster_id = f"near_{canonical['id'][:8]}_{non_canonical['id'][:8]}"

            conn.execute(
                "INSERT OR REPLACE INTO dedup_clusters (cluster_id, file_id, is_canonical, similarity_score) VALUES (?, ?, ?, ?)",
                (cluster_id, canonical["id"], True, 1.0),
            )
            conn.execute(
                "INSERT OR REPLACE INTO dedup_clusters (cluster_id, file_id, is_canonical, similarity_score) VALUES (?, ?, ?, ?)",
                (cluster_id, non_canonical["id"], False, deep_sim),
            )

            self._move_dupe(conn, non_canonical, canonical, cluster_id, f"near_match(sim={deep_sim:.2f})")
            self.stats["phase2_near"] += 1
            self.stats["phase3_deep"] += 1
            self.stats["clusters_created"] += 1

        except Exception as e:
            self.stats["errors"] += 1

    def _move_dupe(self, conn, dupe, canonical, cluster_id, reason):
        """Move a confirmed dupe to I:\\DEDUP_VERIFIED\\ and update INDEX."""
        src = Path(dupe["path"])
        dst = DEDUP_DEST / cluster_id / dupe["filename"]

        moved, result = safe_move(src, dst, dry_run=self.dry_run)
        if moved:
            actual_dst = result if not self.dry_run else str(dst)
            conn.execute(
                "UPDATE files SET status = 'deduped', canonical_id = ?, dupe_cluster = ?, tier = 'dedup', path = ? WHERE id = ?",
                (canonical["id"], cluster_id, actual_dst, dupe["id"]),
            )
            conn.execute(
                """INSERT INTO migrations (file_id, from_path, to_path, from_drive, to_drive, action, reason, agent_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (dupe["id"], str(src), actual_dst, dupe.get("drive", "?"), "I", "dedup", reason, "ORG-dedup"),
            )
            self.stats["dupes_found"] += 1
            self.stats["dupes_moved"] += 1
            action = "DEDUP" if not self.dry_run else "WOULD_DEDUP"
            print(f"  {action}: {dupe['filename'][:50]} → DEDUP_VERIFIED/ (canonical: {canonical['filename'][:30]})")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="ContentDedup: Three-phase content deduplication")
    parser.add_argument("--dry-run", action="store_true", help="Preview without moving files")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE, help="Max clusters per phase")
    args = parser.parse_args()

    dedup = ContentDedup(dry_run=args.dry_run, batch_size=args.batch_size)
    stats = dedup.run()

    with state_db() as conn:
        log_audit(conn, "dedup_run", "INDEX.db",
                  f"dupes={stats['dupes_found']}, moved={stats['dupes_moved']}, clusters={stats['clusters_created']}",
                  "ORG-dedup", "omega-v5.0")


if __name__ == "__main__":
    main()
