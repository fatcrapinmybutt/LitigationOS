"""fix_harvest_quality.py — Fix harvest data quality issues in evidence_quotes.

Step 1: Re-classify 1,061 missing lane assignments (path + content fallback).
Step 2: Remove true duplicates (same source_file + quote_text).
Step 3: Downweight very short entries (< 50 chars) to relevance_score=0.1.
"""

import sqlite3
import re
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "litigation_context.db"

LANE_RULES = [
    ("A", re.compile(r"custody|MCL[\s._]722|best.interest|parenting|722\.23|visitation|custodial", re.I)),
    ("B", re.compile(r"housing|shady|eviction|Homes.of.America|Cricklewood|Partridge|Alden|MHP", re.I)),
    ("D", re.compile(r"PPO|protection.order|2023.5907|stalking|domestic.violence", re.I)),
    ("E", re.compile(r"judicial|McNeill|Hoopes|JTC|misconduct|Ladas|recusal|disqualif", re.I)),
    ("F", re.compile(r"appeal|COA|366810|appellate|MCR.7\.2|Court.of.Appeals", re.I)),
    ("CRIMINAL", re.compile(r"criminal|25245676|Kostrzewa|60th.District|misdemeanor", re.I)),
]


def classify_lane(source_file: str, quote_text: str) -> str:
    """Classify into a lane using path first, then content fallback."""
    src = source_file or ""
    txt = quote_text or ""
    # Path-based (higher confidence)
    for lane, pattern in LANE_RULES:
        if pattern.search(src):
            return lane
    # Content-based fallback
    for lane, pattern in LANE_RULES:
        if pattern.search(txt):
            return lane
    # Default to custody (primary case)
    return "A"


def connect():
    conn = sqlite3.connect(str(DB_PATH), timeout=120)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    return conn


def fix_missing_lanes(conn: sqlite3.Connection) -> dict:
    """Step 1: Re-classify missing lane assignments."""
    cur = conn.execute(
        "SELECT rowid, source_file, quote_text FROM evidence_quotes "
        "WHERE tags='go_harvest' AND (lane IS NULL OR lane='' OR lane=' ')"
    )
    rows = cur.fetchall()
    total = len(rows)
    print(f"[STEP 1] Found {total} harvest rows with missing lane.")

    lane_counts = {}
    for rowid, src, txt in rows:
        lane = classify_lane(src, txt)
        lane_counts[lane] = lane_counts.get(lane, 0) + 1
        conn.execute(
            "UPDATE evidence_quotes SET lane=? WHERE rowid=?",
            (lane, rowid),
        )
    conn.commit()

    # Verify
    remaining = conn.execute(
        "SELECT COUNT(*) FROM evidence_quotes "
        "WHERE tags='go_harvest' AND (lane IS NULL OR lane='' OR lane=' ')"
    ).fetchone()[0]
    print(f"  Classified {total} rows. Remaining unclassified: {remaining}")
    for lane, cnt in sorted(lane_counts.items()):
        print(f"    lane={lane}: {cnt}")
    return {"classified": total, "remaining": remaining, "breakdown": lane_counts}


def remove_duplicates(conn: sqlite3.Connection) -> dict:
    """Step 2: Remove true duplicates (same source_file + quote_text, keep lowest rowid)."""
    # Count before
    before = conn.execute(
        "SELECT COUNT(*) FROM evidence_quotes WHERE tags='go_harvest'"
    ).fetchone()[0]

    # Find exact duplicate count first
    dupe_count = conn.execute(
        "SELECT COUNT(*) FROM evidence_quotes "
        "WHERE tags='go_harvest' AND rowid NOT IN ("
        "  SELECT MIN(rowid) FROM evidence_quotes "
        "  WHERE tags='go_harvest' GROUP BY source_file, quote_text"
        ")"
    ).fetchone()[0]
    print(f"[STEP 2] Found {dupe_count} true duplicates (same source_file + quote_text).")

    conn.execute(
        "DELETE FROM evidence_quotes "
        "WHERE tags='go_harvest' AND rowid NOT IN ("
        "  SELECT MIN(rowid) FROM evidence_quotes "
        "  WHERE tags='go_harvest' GROUP BY source_file, quote_text"
        ")"
    )
    conn.commit()

    after = conn.execute(
        "SELECT COUNT(*) FROM evidence_quotes WHERE tags='go_harvest'"
    ).fetchone()[0]
    deleted = before - after
    print(f"  Deleted {deleted} duplicates. Before: {before}, After: {after}")
    return {"before": before, "after": after, "deleted": deleted}


def flag_short_entries(conn: sqlite3.Connection) -> dict:
    """Step 3: Downweight very short entries (< 50 chars) to relevance_score=0.1."""
    count_before = conn.execute(
        "SELECT COUNT(*) FROM evidence_quotes "
        "WHERE tags='go_harvest' AND LENGTH(quote_text) < 50"
    ).fetchone()[0]
    print(f"[STEP 3] Found {count_before} short entries (< 50 chars).")

    conn.execute(
        "UPDATE evidence_quotes SET relevance_score=0.1 "
        "WHERE tags='go_harvest' AND LENGTH(quote_text) < 50"
    )
    conn.commit()

    verified = conn.execute(
        "SELECT COUNT(*) FROM evidence_quotes "
        "WHERE tags='go_harvest' AND LENGTH(quote_text) < 50 AND relevance_score=0.1"
    ).fetchone()[0]
    print(f"  Downweighted {verified} rows to relevance_score=0.1")
    return {"flagged": count_before, "verified": verified}


def main():
    if not DB_PATH.exists():
        print(f"ERROR: DB not found at {DB_PATH}")
        sys.exit(1)

    print(f"Database: {DB_PATH}")
    print(f"{'='*60}")
    conn = connect()

    try:
        step1 = fix_missing_lanes(conn)
        print()
        step2 = remove_duplicates(conn)
        print()
        step3 = flag_short_entries(conn)

        # Rebuild FTS5 if it exists
        try:
            conn.execute("INSERT INTO evidence_fts(evidence_fts) VALUES('rebuild')")
            conn.commit()
            print("\n[FTS5] Rebuilt evidence_fts index.")
        except Exception as e:
            print(f"\n[FTS5] Rebuild skipped: {e}")

        # Final summary
        final_count = conn.execute(
            "SELECT COUNT(*) FROM evidence_quotes WHERE tags='go_harvest'"
        ).fetchone()[0]

        print(f"\n{'='*60}")
        print("HARVEST QUALITY FIX SUMMARY")
        print(f"{'='*60}")
        print(f"  Lane classification: {step1['classified']} rows classified, {step1['remaining']} remaining")
        print(f"  Deduplication:       {step2['deleted']} duplicates removed")
        print(f"  Short entries:       {step3['flagged']} rows downweighted to 0.1")
        print(f"  Final harvest count: {final_count}")
        print(f"{'='*60}")
        print("ALL FIXES APPLIED SUCCESSFULLY.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
