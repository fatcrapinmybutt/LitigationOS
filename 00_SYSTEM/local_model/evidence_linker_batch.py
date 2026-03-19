"""
evidence_linker_batch.py
-------------------------
Automatically links unlinked claims to matching evidence_quotes
using FTS5 keyword search on the litigation_context.db.

Inserts matches into claim_evidence_links with relevance scores.
"""

import sqlite3
import re
import os
import sys
import time

# ── Config ──────────────────────────────────────────────────────
DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
MIN_RELEVANCE = 0.25          # minimum FTS5 rank threshold (lower = more permissive)
MAX_LINKS_PER_CLAIM = 5       # cap evidence links per claim
MIN_KEYWORD_LEN = 4           # ignore words shorter than this
BATCH_SIZE = 50               # commit every N claims
LINK_METHOD = "keyword_fts_batch"

# Stop words to filter out of FTS queries
STOP_WORDS = {
    "the", "and", "for", "that", "this", "with", "from", "have", "has",
    "was", "were", "are", "been", "being", "will", "would", "could",
    "should", "shall", "may", "might", "must", "can", "not", "but",
    "its", "his", "her", "their", "they", "them", "she", "him",
    "who", "whom", "which", "what", "when", "where", "how", "why",
    "any", "all", "each", "every", "both", "few", "more", "most",
    "other", "some", "such", "only", "own", "same", "than", "too",
    "very", "just", "also", "into", "over", "after", "before",
    "about", "between", "through", "during", "upon", "under",
    "does", "did", "had", "there", "here", "then", "once",
    "court", "plaintiff", "defendant", "order", "filed", "case",
    "party", "parties", "motion", "hearing", "stated", "regarding",
}


def extract_keywords(text):
    """Extract meaningful keywords from proposition text for FTS5 query."""
    if not text:
        return []
    # Remove punctuation, lowercase
    clean = re.sub(r"[^\w\s]", " ", text.lower())
    words = clean.split()
    # Filter: min length, not a stop word, not purely numeric
    keywords = [
        w for w in words
        if len(w) >= MIN_KEYWORD_LEN
        and w not in STOP_WORDS
        and not w.isdigit()
    ]
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for w in keywords:
        if w not in seen:
            seen.add(w)
            unique.append(w)
    return unique[:12]  # cap at 12 keywords to keep FTS manageable


def build_fts_query(keywords):
    """Build an FTS5 OR query from keywords."""
    if not keywords:
        return None
    # Escape any FTS5 special chars in each keyword
    safe = []
    for kw in keywords:
        # FTS5: wrap in quotes to treat as literal
        safe.append(f'"{kw}"')
    return " OR ".join(safe)


def search_evidence(cursor, fts_query, limit=MAX_LINKS_PER_CLAIM):
    """Search evidence_quotes_fts and return ranked results."""
    try:
        cursor.execute(
            """
            SELECT rowid, rank
            FROM evidence_quotes_fts
            WHERE evidence_quotes_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (fts_query, limit),
        )
        return cursor.fetchall()
    except sqlite3.OperationalError as e:
        # FTS query syntax error — skip this claim
        return []


def normalize_score(rank_value, keyword_count):
    """Convert FTS5 rank (negative, lower=better) to 0-1 relevance score."""
    # FTS5 rank is negative; closer to 0 = worse, more negative = better match
    # Normalize: we use abs(rank) scaled by keyword count
    if rank_value >= 0:
        return 0.0
    raw = abs(rank_value)
    # Scale by keyword count (more keywords matching = better)
    # Typical FTS5 BM25 ranks range from -0.1 to -50+
    score = min(raw / max(keyword_count, 1), 1.0)
    return round(score, 4)


def main():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    cur = conn.cursor()

    # ── Step 1: Get all unlinked claims ─────────────────────────
    print("=" * 60)
    print("EVIDENCE LINKER BATCH — LitigationOS")
    print("=" * 60)

    cur.execute(
        """
        SELECT claim_id, classification, actor, proposition
        FROM claims
        WHERE claim_id NOT IN (SELECT claim_id FROM claim_evidence_links)
        """
    )
    unlinked = cur.fetchall()
    total_unlinked = len(unlinked)
    print(f"\nUnlinked claims found: {total_unlinked}")
    print(f"Evidence quotes in DB: ", end="")
    cur.execute("SELECT COUNT(*) FROM evidence_quotes")
    print(f"{cur.fetchone()[0]:,}")
    print(f"Config: min_relevance={MIN_RELEVANCE}, max_links={MAX_LINKS_PER_CLAIM}")
    print("-" * 60)

    # ── Step 2: Process each claim ──────────────────────────────
    linked_count = 0
    skipped_no_kw = 0
    skipped_no_match = 0
    total_links_inserted = 0
    start_time = time.time()

    for idx, (claim_id, classification, actor, proposition) in enumerate(unlinked, 1):
        # Extract keywords from proposition + classification
        search_text = f"{proposition or ''} {classification or ''}"
        keywords = extract_keywords(search_text)

        if not keywords:
            skipped_no_kw += 1
            if idx % BATCH_SIZE == 0:
                print(f"  [{idx}/{total_unlinked}] skipped (no keywords)")
            continue

        fts_query = build_fts_query(keywords)
        if not fts_query:
            skipped_no_kw += 1
            continue

        # Search evidence
        results = search_evidence(cur, fts_query)

        if not results:
            skipped_no_match += 1
            if idx % BATCH_SIZE == 0:
                print(f"  [{idx}/{total_unlinked}] no FTS matches")
            continue

        # Filter by relevance threshold and insert links
        claim_linked = False
        for evidence_rowid, rank_val in results:
            score = normalize_score(rank_val, len(keywords))
            if score >= MIN_RELEVANCE:
                try:
                    cur.execute(
                        """
                        INSERT INTO claim_evidence_links
                            (claim_id, evidence_id, relevance_score, link_method)
                        VALUES (?, ?, ?, ?)
                        """,
                        (claim_id, evidence_rowid, score, LINK_METHOD),
                    )
                    total_links_inserted += 1
                    claim_linked = True
                except sqlite3.IntegrityError:
                    pass  # duplicate link, skip

        if claim_linked:
            linked_count += 1
        else:
            skipped_no_match += 1

        # Progress reporting + batch commit
        if idx % BATCH_SIZE == 0:
            conn.commit()
            elapsed = time.time() - start_time
            rate = idx / elapsed if elapsed > 0 else 0
            print(
                f"  [{idx}/{total_unlinked}] "
                f"linked={linked_count} | "
                f"links_inserted={total_links_inserted} | "
                f"{rate:.1f} claims/sec"
            )

    # Final commit
    conn.commit()
    elapsed = time.time() - start_time

    # ── Step 3: Report ──────────────────────────────────────────
    print("\n" + "=" * 60)
    print("BATCH COMPLETE")
    print("=" * 60)
    print(f"Total unlinked claims processed:  {total_unlinked}")
    print(f"Claims successfully linked:       {linked_count}")
    print(f"Total evidence links inserted:    {total_links_inserted}")
    print(f"Skipped (no usable keywords):     {skipped_no_kw}")
    print(f"Skipped (no match above {MIN_RELEVANCE}):  {skipped_no_match}")
    print(f"Still unlinked:                   {total_unlinked - linked_count}")
    print(f"Link rate:                        {linked_count/max(total_unlinked,1)*100:.1f}%")
    print(f"Elapsed time:                     {elapsed:.1f}s")

    # Verify final state
    cur.execute(
        "SELECT COUNT(*) FROM claims WHERE claim_id NOT IN (SELECT claim_id FROM claim_evidence_links)"
    )
    remaining = cur.fetchone()[0]
    print(f"\nVerification — claims still unlinked in DB: {remaining}")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
