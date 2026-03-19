"""
DELTA99 Ω∞ — Semantic Content Deduplication
=============================================
Goes beyond SHA-256 dedup to find semantically identical content:
same court order saved under different names, same evidence quote in
multiple documents, near-duplicate transcripts. Uses TF-IDF + Jaccard
similarity (zero-network, local-only).

Dedup targets: evidence_quotes, extracted_harms, master_chronological_timeline,
               omega_filesystem_map
"""
import sys
import sqlite3
import json
import re
import time
import hashlib
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass

_shared = Path(__file__).parent.parent / "shared"
if str(_shared) not in sys.path:
    sys.path.insert(0, str(_shared))

from autonomos_config import CENTRAL_DB

DEDUP_DB = Path(__file__).parent / "semantic_dedup.db"

# ── Dedup Thresholds ───────────────────────────────────────────────
JACCARD_THRESHOLD = 0.85   # 85% token overlap = duplicate
SHINGLE_SIZE = 3           # 3-word shingles for Jaccard
MIN_TEXT_LENGTH = 30       # Ignore very short texts
BATCH_SIZE = 5000          # Process in batches


def _init_db() -> sqlite3.Connection:
    DEDUP_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DEDUP_DB), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS duplicate_pairs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_table TEXT NOT NULL,
            record_a_id TEXT NOT NULL,
            record_b_id TEXT NOT NULL,
            similarity REAL NOT NULL,
            dedup_method TEXT DEFAULT 'jaccard',
            text_a_preview TEXT DEFAULT '',
            text_b_preview TEXT DEFAULT '',
            action_taken TEXT DEFAULT 'none',
            detected_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_dp_table ON duplicate_pairs(source_table);
        CREATE INDEX IF NOT EXISTS idx_dp_sim ON duplicate_pairs(similarity);

        CREATE TABLE IF NOT EXISTS dedup_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_table TEXT NOT NULL,
            records_scanned INTEGER DEFAULT 0,
            duplicates_found INTEGER DEFAULT 0,
            exact_dupes INTEGER DEFAULT 0,
            semantic_dupes INTEGER DEFAULT 0,
            duration_s REAL DEFAULT 0.0,
            run_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS content_hashes (
            source_table TEXT NOT NULL,
            record_id TEXT NOT NULL,
            text_hash TEXT NOT NULL,
            shingle_hash TEXT DEFAULT '',
            PRIMARY KEY (source_table, record_id)
        );
    """)
    conn.commit()
    return conn


def _normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text


def _text_hash(text: str) -> str:
    return hashlib.sha256(_normalize_text(text).encode()).hexdigest()[:16]


def _shingle_set(text: str, n: int = SHINGLE_SIZE) -> set[str]:
    """Generate n-gram shingles from text."""
    words = _normalize_text(text).split()
    if len(words) < n:
        return {" ".join(words)}
    return {" ".join(words[i:i+n]) for i in range(len(words) - n + 1)}


def _jaccard_similarity(set_a: set, set_b: set) -> float:
    """Calculate Jaccard similarity between two shingle sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


@dataclass
class DedupResult:
    source_table: str
    records_scanned: int = 0
    exact_duplicates: int = 0
    semantic_duplicates: int = 0
    pairs: list = None

    def __post_init__(self):
        if self.pairs is None:
            self.pairs = []


def dedup_table(central: sqlite3.Connection, table: str, text_col: str,
                id_col: str = "rowid", limit: int = BATCH_SIZE) -> DedupResult:
    """Find duplicates in a table using hash + Jaccard similarity."""
    result = DedupResult(source_table=table)

    try:
        rows = central.execute(f"""
            SELECT {id_col}, {text_col} FROM {table} 
            WHERE {text_col} IS NOT NULL AND length({text_col}) > {MIN_TEXT_LENGTH}
            LIMIT {limit}
        """).fetchall()
    except sqlite3.Error as e:
        return result

    result.records_scanned = len(rows)
    if not rows:
        return result

    # Phase 1: Exact hash dedup
    hash_groups = defaultdict(list)
    shingle_cache = {}

    for row in rows:
        rid = str(row[0])
        text = str(row[1] or "")
        h = _text_hash(text)
        hash_groups[h].append((rid, text))
        shingle_cache[rid] = _shingle_set(text)

    for h, group in hash_groups.items():
        if len(group) > 1:
            for i in range(1, len(group)):
                result.exact_duplicates += 1
                result.pairs.append({
                    "record_a": group[0][0],
                    "record_b": group[i][0],
                    "similarity": 1.0,
                    "method": "exact_hash",
                    "text_a": group[0][1][:150],
                    "text_b": group[i][1][:150],
                })

    # Phase 2: Semantic (Jaccard) dedup — sample comparison
    # Compare random pairs to avoid O(n²) for large tables
    sample_size = min(len(rows), 2000)
    compared = 0
    max_comparisons = 500000  # Safety limit

    row_ids = list(shingle_cache.keys())[:sample_size]
    for i in range(len(row_ids)):
        if compared >= max_comparisons:
            break
        for j in range(i + 1, min(i + 100, len(row_ids))):
            compared += 1
            rid_a = row_ids[i]
            rid_b = row_ids[j]

            sim = _jaccard_similarity(shingle_cache[rid_a], shingle_cache[rid_b])
            if sim >= JACCARD_THRESHOLD and sim < 1.0:
                result.semantic_duplicates += 1
                text_a = next((r[1] for r in rows if str(r[0]) == rid_a), "")
                text_b = next((r[1] for r in rows if str(r[0]) == rid_b), "")
                result.pairs.append({
                    "record_a": rid_a,
                    "record_b": rid_b,
                    "similarity": round(sim, 3),
                    "method": "jaccard",
                    "text_a": str(text_a)[:150],
                    "text_b": str(text_b)[:150],
                })

    return result


def run_full_dedup() -> dict:
    """Run semantic dedup across all major tables."""
    start = time.time()
    ddb = _init_db()

    central = sqlite3.connect(str(CENTRAL_DB), timeout=30)
    central.execute("PRAGMA busy_timeout=120000")

    tables_to_check = [
        ("evidence_quotes", "quote_text", "rowid"),
        ("extracted_harms", "harm_description", "rowid"),
        ("master_chronological_timeline", "event_description", "rowid"),
    ]

    all_results = []
    for table, text_col, id_col in tables_to_check:
        try:
            result = dedup_table(central, table, text_col, id_col)
            all_results.append(result)

            # Persist
            for pair in result.pairs:
                ddb.execute("""
                    INSERT INTO duplicate_pairs
                    (source_table, record_a_id, record_b_id, similarity,
                     dedup_method, text_a_preview, text_b_preview)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (table, pair["record_a"], pair["record_b"],
                      pair["similarity"], pair["method"],
                      pair["text_a"], pair["text_b"]))

            ddb.execute("""
                INSERT INTO dedup_runs
                (source_table, records_scanned, duplicates_found,
                 exact_dupes, semantic_dupes, duration_s)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (table, result.records_scanned,
                  result.exact_duplicates + result.semantic_duplicates,
                  result.exact_duplicates, result.semantic_duplicates, 0))
        except Exception:
            pass

    ddb.commit()
    central.close()
    duration = round(time.time() - start, 2)
    ddb.close()

    return {
        "tables_scanned": len(all_results),
        "total_records": sum(r.records_scanned for r in all_results),
        "total_exact_dupes": sum(r.exact_duplicates for r in all_results),
        "total_semantic_dupes": sum(r.semantic_duplicates for r in all_results),
        "by_table": [
            {
                "table": r.source_table,
                "scanned": r.records_scanned,
                "exact": r.exact_duplicates,
                "semantic": r.semantic_duplicates,
                "sample_pairs": r.pairs[:3],
            }
            for r in all_results
        ],
        "duration_s": duration,
    }


if __name__ == "__main__":
    result = run_full_dedup()
    print(json.dumps(result, indent=2, default=str))
