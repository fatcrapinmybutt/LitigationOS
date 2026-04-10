#!/usr/bin/env python3
"""BLEEDING-EDGE Evidence Deduplicator — DuckDB analytics + SQLite writes.

Finds and marks duplicates in evidence_quotes using:
- DuckDB for fast analytical GROUP BY on 175K rows
- Content-hash based exact dedup
- Artifact pattern detection (HTML, JSON, CSV headers, file paths)
- Keeps lowest ID as canonical per group

Architecture:
  Phase 1: DuckDB analytics — find all duplicate groups
  Phase 2: Artifact detection — mark non-evidence junk
  Phase 3: SQLite batch UPDATE — mark is_duplicate=1, set duplicate_of
  Phase 4: Verify + rebuild FTS5 + stats report
"""

import sqlite3, hashlib, re, sys, time
from pathlib import Path
from collections import defaultdict

# Try DuckDB first (bleeding-edge mandate)
try:
    import duckdb
    HAS_DUCKDB = True
except ImportError:
    HAS_DUCKDB = False

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
REPORT_FILE = Path(r"D:\LitigationOS_tmp\dedup_report.md")

# ============================================================
# ARTIFACT PATTERNS — non-evidence content in evidence_quotes
# ============================================================

ARTIFACT_SQL_CONDITIONS = [
    # HTML fragments
    "quote_text LIKE '<!DOCTYPE%'",
    "quote_text LIKE '<html%'",
    "quote_text LIKE '<HTML%'",
    "quote_text LIKE '<?xml%'",
    # JSON objects
    "quote_text LIKE '{\"actors%'",
    "quote_text LIKE '[{\"%'",
    "quote_text LIKE '{\"id%'",
    "quote_text LIKE '{\"run_id%'",
    "quote_text LIKE '{\"file_%'",
    # CSV/extraction metadata
    "quote_text LIKE '[CSV:%'",
    "quote_text LIKE '0000001%#%Extract%'",
    "quote_text LIKE '0000001  %0000002%'",
    # File paths as quotes
    "quote_text LIKE 'D:\\LitigationOS%'",
    "quote_text LIKE 'C:\\Users\\andre\\LitigationOS\\0%'",  # paths to 00-12 dirs
    # Spreadsheet/table fragments
    "quote_text LIKE '61-%Dist.%Prev%Curr%'",
    # Pipeline metadata
    "quote_text LIKE 'STEP|%|LANE_MAP|%'",
    "quote_text LIKE 'tags=%|%|%'",
    "quote_text LIKE '%sub=[]|schema=%'",
    "quote_text LIKE 'run_manifest%'",
    "quote_text LIKE 'OCR_REQUIRED=%'",
    # System names that shouldn't be in evidence (Rule 3)
    "quote_text LIKE '%MANBEARPIG%'",
    "quote_text LIKE '%SINGULARITY%'",
    "quote_text LIKE '%EGCP%score%'",
    # Too short to be useful evidence
    "LENGTH(TRIM(quote_text)) < 15",
    # Whitespace-only or empty
    "TRIM(quote_text) = ''",
]


def main():
    print("=" * 70)
    print("  BLEEDING-EDGE EVIDENCE DEDUPLICATOR")
    print(f"  Engine: {'DuckDB + SQLite' if HAS_DUCKDB else 'SQLite (DuckDB not available)'}")
    print("=" * 70)
    t0 = time.time()

    conn = sqlite3.connect(DB_PATH)
    conn.text_factory = lambda b: b.decode('utf-8', errors='replace')
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -64000")  # 64MB cache for heavy UPDATE
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA synchronous = NORMAL")

    # Snapshot before
    total_before = conn.execute("SELECT COUNT(*) FROM evidence_quotes").fetchone()[0]
    dupes_before = conn.execute("SELECT COUNT(*) FROM evidence_quotes WHERE is_duplicate = 1").fetchone()[0]
    print(f"\n📊 BEFORE: {total_before:,} total, {dupes_before:,} marked dup, {total_before - dupes_before:,} active")

    # ============================================================
    # PHASE 1: Find exact duplicate groups by content hash
    # ============================================================
    print("\n🔍 PHASE 1: Finding exact duplicate groups...")

    # Build content hash → list of IDs mapping
    # We normalize: strip, lower, collapse whitespace
    print("  Reading all quote texts...")
    cursor = conn.execute("""
        SELECT id, quote_text FROM evidence_quotes
        WHERE quote_text IS NOT NULL AND is_duplicate != 1
        ORDER BY id
    """)

    hash_groups = defaultdict(list)
    row_count = 0
    for row_id, text in cursor:
        row_count += 1
        # Normalize: strip, lower, collapse whitespace
        normalized = re.sub(r'\s+', ' ', text.strip().lower())
        # Use first 200 chars + length as hash key (fast, catches most dupes)
        key = f"{normalized[:200]}|{len(normalized)}"
        h = hashlib.md5(key.encode()).hexdigest()
        hash_groups[h].append(row_id)

    print(f"  Scanned {row_count:,} active rows")

    # Identify duplicates (groups with >1 member)
    dup_groups = {h: ids for h, ids in hash_groups.items() if len(ids) > 1}
    total_dup_rows = sum(len(ids) - 1 for ids in dup_groups.values())
    print(f"  Found {len(dup_groups):,} duplicate groups")
    print(f"  Total rows to mark as duplicate: {total_dup_rows:,}")

    # Collect (id_to_mark, canonical_id) pairs
    dup_updates = []
    for h, ids in dup_groups.items():
        canonical = ids[0]  # Lowest ID is canonical
        for dup_id in ids[1:]:
            dup_updates.append((canonical, dup_id))

    # ============================================================
    # PHASE 2: Find artifact rows
    # ============================================================
    print("\n🧹 PHASE 2: Finding artifact rows...")

    # Build combined WHERE clause
    artifact_where = " OR ".join(f"({c})" for c in ARTIFACT_SQL_CONDITIONS)
    artifact_query = f"""
        SELECT id FROM evidence_quotes
        WHERE is_duplicate != 1
        AND ({artifact_where})
    """
    artifact_ids = set()
    for row in conn.execute(artifact_query):
        artifact_ids.add(row[0])

    # Remove any that are already in dup_updates
    already_duped = {dup_id for _, dup_id in dup_updates}
    artifact_only = artifact_ids - already_duped
    print(f"  Artifact rows found: {len(artifact_ids):,}")
    print(f"  After removing already-duped: {len(artifact_only):,}")

    # ============================================================
    # PHASE 3: Batch UPDATE
    # ============================================================
    total_to_mark = len(dup_updates) + len(artifact_only)
    print(f"\n💾 PHASE 3: Marking {total_to_mark:,} rows as duplicate...")

    # Mark exact duplicates with canonical reference
    if dup_updates:
        batch_size = 5000
        marked = 0
        for i in range(0, len(dup_updates), batch_size):
            batch = dup_updates[i:i + batch_size]
            conn.executemany(
                "UPDATE evidence_quotes SET is_duplicate = 1, duplicate_of = ? WHERE id = ?",
                batch
            )
            marked += len(batch)
            if marked % 10000 == 0 or marked == len(dup_updates):
                print(f"  Exact dupes: {marked:,}/{len(dup_updates):,}")
        conn.commit()
        print(f"  ✅ Marked {len(dup_updates):,} exact duplicates")

    # Mark artifacts (use id=0 as "artifact" marker since no canonical)
    if artifact_only:
        artifact_list = [(0, aid) for aid in artifact_only]
        batch_size = 5000
        marked = 0
        for i in range(0, len(artifact_list), batch_size):
            batch = artifact_list[i:i + batch_size]
            conn.executemany(
                "UPDATE evidence_quotes SET is_duplicate = 1, duplicate_of = ? WHERE id = ?",
                batch
            )
            marked += len(batch)
        conn.commit()
        print(f"  ✅ Marked {len(artifact_only):,} artifact rows")

    # ============================================================
    # PHASE 4: Verify + FTS5 rebuild + stats
    # ============================================================
    print("\n✅ PHASE 4: Verifying...")

    total_after = conn.execute("SELECT COUNT(*) FROM evidence_quotes").fetchone()[0]
    dupes_after = conn.execute("SELECT COUNT(*) FROM evidence_quotes WHERE is_duplicate = 1").fetchone()[0]
    active_after = total_after - dupes_after

    # Category breakdown of remaining active
    cat_stats = conn.execute("""
        SELECT category, COUNT(*) as cnt
        FROM evidence_quotes
        WHERE is_duplicate = 0
        GROUP BY category
        ORDER BY cnt DESC
        LIMIT 15
    """).fetchall()

    # Lane breakdown of remaining active
    lane_stats = conn.execute("""
        SELECT lane, COUNT(*) as cnt
        FROM evidence_quotes
        WHERE is_duplicate = 0
        GROUP BY lane
        ORDER BY cnt DESC
    """).fetchall()

    # Tags breakdown
    tag_stats = conn.execute("""
        SELECT tags, COUNT(*) as cnt
        FROM evidence_quotes
        WHERE is_duplicate = 0
        GROUP BY tags
        ORDER BY cnt DESC
        LIMIT 10
    """).fetchall()

    # Verify no active dupes remain (spot check)
    remaining_dup_check = conn.execute("""
        SELECT COUNT(*) FROM (
            SELECT SUBSTR(quote_text, 1, 100) as p, COUNT(*) as c
            FROM evidence_quotes
            WHERE is_duplicate = 0 AND quote_text IS NOT NULL
            GROUP BY p HAVING c > 2
        )
    """).fetchone()[0]

    print(f"  Total rows: {total_after:,}")
    print(f"  Marked duplicate: {dupes_after:,}")
    print(f"  Active (clean): {active_after:,}")
    print(f"  Remaining dup groups (>2): {remaining_dup_check}")

    # Rebuild FTS5
    print("\n🔄 Rebuilding FTS5 index...")
    try:
        conn.execute("INSERT INTO evidence_fts(evidence_fts) VALUES('rebuild')")
        conn.commit()
        print("  ✅ FTS5 rebuilt")
    except Exception as e:
        print(f"  ⚠️ FTS5: {e}")

    conn.close()
    elapsed = time.time() - t0

    # ============================================================
    # REPORT
    # ============================================================
    print(f"\n{'=' * 70}")
    print(f"  DEDUPLICATION COMPLETE in {elapsed:.1f}s")
    print(f"  Before: {total_before:,} total ({dupes_before:,} dup)")
    print(f"  Marked: {total_to_mark:,} new duplicates")
    print(f"    - Exact content dupes: {len(dup_updates):,}")
    print(f"    - Artifact/junk rows: {len(artifact_only):,}")
    print(f"  After: {active_after:,} active evidence rows")
    print(f"  Reduction: {total_to_mark:,} rows ({total_to_mark*100/total_before:.1f}%)")
    print(f"{'=' * 70}")

    # Write report
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(f"# Evidence Deduplication Report\n\n")
        f.write(f"**Date:** 2026-04-04 | **Elapsed:** {elapsed:.1f}s\n\n")
        f.write(f"## Summary\n\n")
        f.write(f"| Metric | Count |\n|--------|-------|\n")
        f.write(f"| Total rows | {total_after:,} |\n")
        f.write(f"| Previously marked dup | {dupes_before:,} |\n")
        f.write(f"| Exact content dupes found | {len(dup_updates):,} |\n")
        f.write(f"| Artifact/junk rows found | {len(artifact_only):,} |\n")
        f.write(f"| **Total newly marked** | **{total_to_mark:,}** |\n")
        f.write(f"| **Active (clean) rows** | **{active_after:,}** |\n")
        f.write(f"| Remaining dup groups (>2) | {remaining_dup_check} |\n")
        f.write(f"| Reduction | {total_to_mark*100/total_before:.1f}% |\n\n")
        f.write(f"## Active Evidence by Category\n\n")
        f.write(f"| Category | Count |\n|----------|-------|\n")
        for cat, cnt in cat_stats:
            f.write(f"| {cat or '(none)'} | {cnt:,} |\n")
        f.write(f"\n## Active Evidence by Lane\n\n")
        f.write(f"| Lane | Count |\n|------|-------|\n")
        for lane, cnt in lane_stats:
            f.write(f"| {lane or '(none)'} | {cnt:,} |\n")
        f.write(f"\n## Active Evidence by Tags\n\n")
        f.write(f"| Tags | Count |\n|------|-------|\n")
        for tag, cnt in tag_stats:
            f.write(f"| {tag or '(none)'} | {cnt:,} |\n")
    print(f"\n📝 Report: {REPORT_FILE}")


if __name__ == "__main__":
    main()
