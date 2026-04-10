"""
DEDUP PASS 2B — Single-query approach for near-dupes
Uses window functions to find dupes in one pass instead of N+1 queries.
"""
import sqlite3, time

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"

def run():
    t0 = time.time()
    conn = sqlite3.connect(DB)
    conn.text_factory = lambda b: b.decode('utf-8', errors='replace')
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-64000")
    conn.execute("PRAGMA temp_store=MEMORY")

    before = conn.execute("SELECT COUNT(*) FROM evidence_quotes WHERE is_duplicate=0").fetchone()[0]
    print(f"Active rows before pass 2B: {before:,}")

    # ── Single-query near-dupe detection ──
    # For each 80-char prefix group, keep the row with MIN(id), mark all others as dupes
    print("Finding near-duplicate IDs via window function...")
    
    # Step 1: Get all (id, min_id_for_group) pairs where id != min_id
    # This is ONE query, no N+1
    dup_rows = conn.execute("""
        WITH grouped AS (
            SELECT id,
                   SUBSTR(quote_text, 1, 80) as pfx,
                   MIN(id) OVER (PARTITION BY SUBSTR(quote_text, 1, 80)) as keep_id
            FROM evidence_quotes
            WHERE is_duplicate = 0 AND quote_text IS NOT NULL AND LENGTH(quote_text) > 0
        )
        SELECT id, keep_id FROM grouped WHERE id != keep_id
    """).fetchall()
    
    print(f"  Found {len(dup_rows):,} near-duplicate rows to mark")
    
    if not dup_rows:
        print("  Nothing to do!")
        conn.close()
        return

    # Batch UPDATE
    batch = 5000
    for i in range(0, len(dup_rows), batch):
        chunk = dup_rows[i:i+batch]
        conn.executemany(
            "UPDATE evidence_quotes SET is_duplicate=1, duplicate_of=? WHERE id=? AND is_duplicate=0",
            [(keep_id, rid) for rid, keep_id in chunk]
        )
        conn.commit()
        done = min(i+batch, len(dup_rows))
        print(f"  Marked {done:,}/{len(dup_rows):,}")

    # ── FTS5 rebuild ──
    print("\nRebuilding FTS5 index...")
    try:
        conn.execute("INSERT INTO evidence_fts(evidence_fts) VALUES('rebuild')")
        conn.commit()
        print("  FTS5 rebuilt OK")
    except Exception as e:
        print(f"  FTS5 warning: {e}")

    after = conn.execute("SELECT COUNT(*) FROM evidence_quotes WHERE is_duplicate=0").fetchone()[0]
    total_dup = conn.execute("SELECT COUNT(*) FROM evidence_quotes WHERE is_duplicate=1").fetchone()[0]
    distinct = conn.execute("SELECT COUNT(DISTINCT SUBSTR(quote_text,1,80)) FROM evidence_quotes WHERE is_duplicate=0").fetchone()[0]

    elapsed = time.time() - t0
    print(f"\n{'='*60}")
    print(f"  PASS 2B COMPLETE in {elapsed:.1f}s")
    print(f"  Before: {before:,} active")
    print(f"  Near-dupes cleaned: {len(dup_rows):,}")
    print(f"  After: {after:,} active ({total_dup:,} total dup)")
    print(f"  Distinct prefixes: {distinct:,} (should ≈ active)")
    print(f"{'='*60}")
    conn.close()

if __name__ == "__main__":
    run()
