"""
EVIDENCE DEDUP + CONSOLIDATION
- Groups 30K+ evidence rows by (source_file, approximate position)
- Merges overlapping hits into single consolidated evidence items
- Each consolidated item tagged with ALL claims, adversaries, torts it supports
- Creates evidence_consolidated table (the clean, citable source of truth)
"""
import sys, os, json, re, time
from collections import defaultdict

# Regex to validate that a name is safe to interpolate into SQL (word chars only)
_SAFE_LABEL_RE = re.compile(r'^\w+$')

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', errors='replace')

import sqlite3

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

STRENGTH_RANK = {
    'STRONG_COURT_ORDER': 6,
    'STRONG_SWORN': 5,
    'STRONG_TESTIMONY': 4,
    'STRONG_OFFICIAL': 3,
    'MODERATE_DOCUMENTARY': 2,
    'MODERATE': 1,
}

def main():
    t0 = time.time()
    conn = sqlite3.connect(DB_PATH, timeout=180)
    conn.execute("PRAGMA busy_timeout = 180000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -64000")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA synchronous = NORMAL")

    # Load all actionable evidence
    print("Loading actionable_evidence...")
    rows = conn.execute("""
        SELECT id, claim_id, claim_name, tort_type, adversary, filing_vehicle,
               source_file, harvest_id, evidence_text, strength, admissibility_notes,
               case_lane, topic, line_number, char_offset
        FROM actionable_evidence
        ORDER BY source_file, char_offset
    """).fetchall()
    print(f"  Raw rows: {len(rows):,}")

    # Group by (source_file, line_number bucket)
    # Two hits within 5 lines of each other in the same file = same evidence
    LINE_BUCKET = 5
    groups = defaultdict(list)
    for r in rows:
        src = r[6]   # source_file
        line = r[13] or 0  # line_number
        bucket = line // LINE_BUCKET
        key = (src, bucket)
        groups[key].append(r)

    print(f"  Unique evidence locations: {len(groups):,}")
    print(f"  Dedup ratio: {len(rows)/max(len(groups),1):.1f}x")

    # Consolidate each group
    conn.execute("DROP TABLE IF EXISTS evidence_consolidated")
    conn.execute("""
        CREATE TABLE evidence_consolidated (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_file TEXT NOT NULL,
            line_number INTEGER,
            evidence_text TEXT NOT NULL,
            best_strength TEXT,
            strength_rank INTEGER,
            admissibility TEXT,
            claim_ids TEXT,
            claim_names TEXT,
            tort_types TEXT,
            adversaries TEXT,
            filing_vehicles TEXT,
            num_claims INTEGER,
            num_patterns INTEGER,
            case_lane TEXT,
            topic TEXT,
            harvest_id TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    consolidated = []
    for (src_file, bucket), items in groups.items():
        # Merge all claim info
        claim_ids = sorted(set(r[1] for r in items))
        claim_names = sorted(set(r[2] for r in items))
        tort_types = sorted(set(r[3] for r in items))
        adversaries = sorted(set(a.strip() for r in items for a in r[4].split(',')))
        vehicles = sorted(set(v.strip() for r in items for v in (r[5] or '').split(',') if v.strip()))

        # Pick the best (longest) evidence text
        best_text = max(items, key=lambda r: len(r[8] or ''))[8]

        # Pick highest strength
        best_strength = max(items, key=lambda r: STRENGTH_RANK.get(r[9], 0))
        strength = best_strength[9]
        strength_rank = STRENGTH_RANK.get(strength, 0)
        admiss = best_strength[10]

        # Representative line number
        line_num = items[0][13] or 0
        case_lane = next((r[11] for r in items if r[11]), '')
        topic = next((r[12] for r in items if r[12]), '')
        harvest_id = next((r[7] for r in items if r[7]), '')

        consolidated.append((
            src_file, line_num, best_text[:2000],
            strength, strength_rank, admiss,
            ', '.join(claim_ids), ', '.join(claim_names[:5]),
            ', '.join(tort_types), ', '.join(adversaries),
            ', '.join(vehicles), len(claim_ids), len(items),
            case_lane, topic, harvest_id
        ))

    # Batch insert
    print(f"Inserting {len(consolidated):,} consolidated evidence rows...")
    conn.executemany("""
        INSERT INTO evidence_consolidated
        (source_file, line_number, evidence_text, best_strength, strength_rank,
         admissibility, claim_ids, claim_names, tort_types, adversaries,
         filing_vehicles, num_claims, num_patterns, case_lane, topic, harvest_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, consolidated)
    conn.commit()

    # Create indexes
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ec_source ON evidence_consolidated(source_file)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ec_strength ON evidence_consolidated(strength_rank DESC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ec_adversary ON evidence_consolidated(adversaries)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ec_claims ON evidence_consolidated(num_claims DESC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ec_tort ON evidence_consolidated(tort_types)")
    conn.commit()

    # ─── REPORT ──────────────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("  EVIDENCE CONSOLIDATION REPORT")
    print("=" * 80)

    print(f"\n  Raw evidence rows:          {len(rows):>8,}")
    print(f"  Consolidated (unique):      {len(consolidated):>8,}")
    print(f"  Duplicates removed:         {len(rows) - len(consolidated):>8,}")
    print(f"  Dedup ratio:                {len(rows)/max(len(consolidated),1):>8.1f}x")

    # By strength
    print("\n--- CONSOLIDATED BY STRENGTH ---")
    strengths = conn.execute("""
        SELECT best_strength, COUNT(*), ROUND(AVG(num_claims),1), SUM(num_patterns)
        FROM evidence_consolidated
        GROUP BY best_strength ORDER BY MAX(strength_rank) DESC
    """).fetchall()
    for s in strengths:
        print(f"  {s[0]:25s}  {s[1]:>6,} items  avg {s[2]} claims/item  {s[3]:>7,} raw patterns")

    # By adversary — single query with conditional aggregation (replaces 22 round-trips)
    # Names are validated against \w+ so only [A-Za-z0-9_] chars are interpolated.
    _ADV_NAMES = [
        'McNeill', 'Emily_Watson', 'Watson', 'Muskegon_County', 'Watson_Family',
        'Lori_Watson', 'Albert_Watson', 'Cody_Watson', 'Ronald_Berry', 'Rusco', 'Barnes',
    ]
    _safe_adv = [a for a in _ADV_NAMES if _SAFE_LABEL_RE.match(a)]
    adv_sql = "SELECT " + ", ".join(
        f"SUM(CASE WHEN adversaries LIKE '%{a}%' THEN 1 ELSE 0 END) AS cnt_{i},"
        f" SUM(CASE WHEN adversaries LIKE '%{a}%' AND strength_rank >= 3 THEN 1 ELSE 0 END) AS strong_{i}"
        for i, a in enumerate(_safe_adv)
    ) + " FROM evidence_consolidated"
    adv_row = conn.execute(adv_sql).fetchone()
    print("\n--- CONSOLIDATED BY ADVERSARY ---")
    for i, adv in enumerate(_safe_adv):
        count = adv_row[i * 2]
        strong = adv_row[i * 2 + 1]
        if count > 0:
            print(f"  {adv:20s}  {count:>6,} unique items  ({strong:,} STRONG+)")

    # By tort type — single query with conditional aggregation (replaces 19 round-trips)
    # Names are validated against \w+ so only [A-Za-z0-9_] chars are interpolated.
    _TORT_NAMES = [
        'due_process_violation', 'judicial_misconduct', 'abuse_of_process',
        'civil_rights_1983', 'perjury_fraud', 'tortious_interference',
        'civil_conspiracy', 'fraud', 'emotional_distress', 'damages',
        'constitutional_violation', 'spoliation', 'conflict_of_interest',
        'civil_rights_1983_monell', 'equal_protection', 'unauthorized_practice',
        'obstruction', 'punitive_damages', 'procedural_violation',
    ]
    _safe_torts = [t for t in _TORT_NAMES if _SAFE_LABEL_RE.match(t)]
    tort_sql = "SELECT " + ", ".join(
        f"SUM(CASE WHEN tort_types LIKE '%{t}%' THEN 1 ELSE 0 END) AS tort_{i}"
        for i, t in enumerate(_safe_torts)
    ) + " FROM evidence_consolidated"
    tort_row = conn.execute(tort_sql).fetchone()
    print("\n--- CONSOLIDATED BY TORT TYPE ---")
    for i, tort in enumerate(_safe_torts):
        count = tort_row[i]
        if count > 0:
            print(f"  {tort:35s}  {count:>6,} items")

    # Multi-claim evidence (hits multiple torts — most powerful)
    print("\n--- MULTI-CLAIM EVIDENCE (covers 3+ claims — MOST POWERFUL) ---")
    multi = conn.execute("""
        SELECT source_file, num_claims, num_patterns, adversaries, 
               tort_types, best_strength, substr(evidence_text, 1, 150)
        FROM evidence_consolidated
        WHERE num_claims >= 3
        ORDER BY num_claims DESC, num_patterns DESC
        LIMIT 25
    """).fetchall()

    # Top 20 files by evidence density
    print("\n--- TOP 20 FILES BY EVIDENCE DENSITY ---")
    top = conn.execute("""
        SELECT source_file, COUNT(*) as items, SUM(num_claims) as total_claims,
               MAX(num_claims) as max_claims, 
               GROUP_CONCAT(DISTINCT best_strength) as strengths
        FROM evidence_consolidated
        GROUP BY source_file
        ORDER BY total_claims DESC
        LIMIT 20
    """).fetchall()
    for t in top:
        print(f"  {t[0][:60]:60s}  {t[1]:>4} items  {t[2]:>5} claim-hits  max={t[3]}  [{t[4][:40]}]")

    # Summary — single query replaces 3 separate COUNT(*) round-trips and also
    # captures the accurate total for 3+ claim items (not capped by LIMIT 25 above).
    summary_row = conn.execute("""
        SELECT
            SUM(CASE WHEN strength_rank >= 3 THEN 1 ELSE 0 END) AS total_strong,
            SUM(CASE WHEN num_claims >= 2 THEN 1 ELSE 0 END) AS total_multi,
            COUNT(DISTINCT source_file) AS total_files,
            SUM(CASE WHEN num_claims >= 3 THEN 1 ELSE 0 END) AS total_3plus
        FROM evidence_consolidated
    """).fetchone()
    total_strong = summary_row[0] or 0
    total_multi = summary_row[1] or 0
    total_files = summary_row[2] or 0
    total_3plus = summary_row[3] or 0

    # Print multi-claim section header with the accurate total, then the sample rows
    print(f"\n--- MULTI-CLAIM EVIDENCE (covers 3+ claims — MOST POWERFUL) ---")
    print(f"  {total_3plus:,} items cover 3+ claims (showing top {len(multi)})")
    for m in multi:
        print(f"  [{m[1]} claims, {m[2]} patterns] {m[0][:50]:50s} vs:{m[3][:40]} | {m[5]}")
        print(f"    Torts: {m[4][:100]}")
        print(f"    Text: {m[6][:120]}...")

    elapsed = time.time() - t0
    print(f"\n=== CONSOLIDATION COMPLETE in {elapsed:.1f}s ===")
    print(f"  Unique evidence items:   {len(consolidated):,}")
    print(f"  Across files:            {total_files:,}")
    print(f"  STRONG+ strength:        {total_strong:,} ({100*total_strong/len(consolidated):.0f}%)")
    print(f"  Multi-claim (2+):        {total_multi:,} ({100*total_multi/len(consolidated):.0f}%)")

    conn.close()

if __name__ == '__main__':
    main()
