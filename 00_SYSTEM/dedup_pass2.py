"""
DEDUP PASS 2 — Clean remaining artifacts + near-dupes
Targets: SHARD indexes, file paths, separator lines, JSON blobs,
case headers (keep 1 per group), whitespace-only rows, etc.
"""
import sqlite3, time, hashlib, re

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"

def run():
    t0 = time.time()
    conn = sqlite3.connect(DB)
    conn.text_factory = lambda b: b.decode('utf-8', errors='replace')
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")

    before = conn.execute("SELECT COUNT(*) FROM evidence_quotes WHERE is_duplicate=0").fetchone()[0]
    print(f"Active rows before pass 2: {before:,}")

    # ── Phase A: artifact patterns ──
    artifact_patterns = [
        ("SHARD::", "quote_text LIKE 'SHARD::%'"),
        ("file paths H:\\", "quote_text LIKE 'H:\\%'"),
        ("file paths I:\\", "quote_text LIKE 'I:\\%'"),
        ("file paths /mnt/", "quote_text LIKE '/mnt/%'"),
        ("JSON zip_name", "quote_text LIKE '{%\"zip_name\"%'"),
        ("HIGH_PRIORITY_SNIPPETS", "quote_text LIKE 'HIGH_PRIORITY_SNIPPETS%'"),
        ("separator lines", "quote_text LIKE '======%' AND LENGTH(quote_text) < 200"),
        ("separator dashes", "quote_text LIKE '------%' AND LENGTH(quote_text) < 200"),
        ("empty/whitespace", "TRIM(quote_text) = '' OR LENGTH(TRIM(quote_text)) < 5"),
        ("Component Value Ref Range", "quote_text LIKE '%Component Value Ref%Range Test Method%'"),
        ("EJCDC copyright", "quote_text LIKE '%EJCDC%Standard General Conditions%'"),
        ("student fee form", "quote_text LIKE 'If a student fee will be charged%'"),
        ("Disability glossary", "quote_text LIKE 'Disability glossary%impairments%'"),
        ("DATE INVOICE vendor", "quote_text LIKE '%DATE INVOICE%REF%PAID CK%AMOUNT VENDOR%'"),
        ("Civil Discovery Guidebook", "quote_text LIKE 'Civil Discovery%Guidebook to the New Civil Discovery%'"),
        ("Run Date DECISIONS", "quote_text LIKE '%Run Date:%DECISIONS AND NOTICES RELEASED%'"),
        ("Michigan IV-D manual", "quote_text LIKE 'Michigan IV-D Child Support Manual%'"),
    ]

    total_artifacts = 0
    for label, sql_cond in artifact_patterns:
        cur = conn.execute(f"UPDATE evidence_quotes SET is_duplicate=1 WHERE is_duplicate=0 AND ({sql_cond})")
        n = cur.rowcount
        if n > 0:
            print(f"  {label}: {n:,} rows")
            total_artifacts += n
    conn.commit()
    print(f"  Phase A total: {total_artifacts:,} artifact rows cleaned\n")

    # ── Phase B: prefix-based near-dupes (keep oldest per 80-char prefix) ──
    print("Phase B: Finding near-duplicate groups (80-char prefix)...")
    rows = conn.execute("""
        SELECT SUBSTR(quote_text, 1, 80) as pfx, MIN(id) as keep_id, COUNT(*) as cnt
        FROM evidence_quotes
        WHERE is_duplicate = 0 AND quote_text IS NOT NULL
        GROUP BY SUBSTR(quote_text, 1, 80)
        HAVING cnt > 1
    """).fetchall()

    dup_ids = []
    for pfx, keep_id, cnt in rows:
        ids = conn.execute("""
            SELECT id FROM evidence_quotes
            WHERE is_duplicate = 0 AND SUBSTR(quote_text, 1, 80) = ?
            AND id != ?
        """, (pfx, keep_id)).fetchall()
        for (rid,) in ids:
            dup_ids.append((keep_id, rid))

    print(f"  Found {len(dup_ids):,} near-duplicate rows to mark")

    # Batch update
    batch = 5000
    for i in range(0, len(dup_ids), batch):
        chunk = dup_ids[i:i+batch]
        conn.executemany(
            "UPDATE evidence_quotes SET is_duplicate=1, duplicate_of=? WHERE id=?",
            chunk
        )
        conn.commit()
        print(f"  Marked {min(i+batch, len(dup_ids)):,}/{len(dup_ids):,}")

    # ── Phase C: FTS5 rebuild ──
    print("\nRebuilding FTS5 index...")
    try:
        conn.execute("INSERT INTO evidence_fts(evidence_fts) VALUES('rebuild')")
        conn.commit()
        print("  FTS5 rebuilt OK")
    except Exception as e:
        print(f"  FTS5 rebuild warning: {e}")

    after = conn.execute("SELECT COUNT(*) FROM evidence_quotes WHERE is_duplicate=0").fetchone()[0]
    total_dup = conn.execute("SELECT COUNT(*) FROM evidence_quotes WHERE is_duplicate=1").fetchone()[0]

    elapsed = time.time() - t0
    print(f"\n{'='*60}")
    print(f"  PASS 2 COMPLETE in {elapsed:.1f}s")
    print(f"  Before: {before:,} active")
    print(f"  Artifacts cleaned: {total_artifacts:,}")
    print(f"  Near-dupes cleaned: {len(dup_ids):,}")
    print(f"  After: {after:,} active ({total_dup:,} total marked dup)")
    print(f"{'='*60}")
    conn.close()

if __name__ == "__main__":
    run()
