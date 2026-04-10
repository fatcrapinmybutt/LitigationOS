#!/usr/bin/env python3
"""Persist Dossier Findings — Filter artifacts, dedup, bulk INSERT into litigation_context.db.

Reads txt_hunt_results.json + pdf_hunt_results.json, filters false positives,
deduplicates against existing evidence_quotes rows, and inserts new evidence.

Architecture:
  Phase 1: Load JSON results (orjson for speed)
  Phase 2: Artifact filter — remove code/metadata/pipeline artifacts
  Phase 3: Content-based dedup against existing DB rows (SHA-256 + LIKE prefix)
  Phase 4: MEEK lane assignment
  Phase 5: Batch INSERT with executemany + verify
  Phase 6: FTS5 rebuild + stats report
"""

import sqlite3, hashlib, re, sys, time, json
from pathlib import Path
from collections import Counter

# Try orjson first (10x faster), fallback to stdlib
try:
    import orjson
    def load_json(path):
        with open(path, "rb") as f:
            return orjson.loads(f.read())
except ImportError:
    def load_json(path):
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return json.load(f)

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
TXT_JSON = Path(r"D:\LitigationOS_tmp\txt_hunt_results.json")
PDF_JSON = Path(r"D:\LitigationOS_tmp\pdf_hunt_results.json")
REPORT_FILE = Path(r"D:\LitigationOS_tmp\persist_report.md")

# ============================================================
# PHASE 2: Artifact Filters
# ============================================================

# Lines matching these patterns are system artifacts, not real evidence
ARTIFACT_PATTERNS = [
    re.compile(r'^\s*[\[{]'),                         # JSON/dict starts
    re.compile(r'run_id|DOC_[a-f0-9]{8,}'),          # Pipeline run IDs
    re.compile(r'MEEK[234]_|OCR_REQUIRED='),          # MEEK pipeline tags
    re.compile(r'tags=DISQUAL|tags=.*\|.*\|'),        # Tag metadata lines
    re.compile(r'evidence_atoms|filing_readiness'),    # DB table names
    re.compile(r'SELECT\s|INSERT\s|CREATE\s|PRAGMA'),  # SQL statements
    re.compile(r'def\s+\w+\(|class\s+\w+[:(]'),      # Python code
    re.compile(r'import\s+\w+|from\s+\w+\s+import'),  # Python imports
    re.compile(r'FileProcessingLog|encyclopediaUNIVERSE'), # Known noise files
    re.compile(r'STEP\|\d+\|LANE_MAP'),               # Pipeline step markers
    re.compile(r'sub=\[\]?\|schema='),                 # Schema metadata
    re.compile(r'^\s*\|.*\|.*\|.*\|'),                 # Table/CSV rows with pipes
    re.compile(r'LitigationOS|MANBEARPIG|SINGULARITY'), # System names (Rule 3)
    re.compile(r'evidence_quotes|authority_chains|impeachment_matrix'), # DB table names
    re.compile(r'C:\\Users\\andre\\|D:\\LitigationOS'), # File paths
    re.compile(r'EGCP|LOCUS\s*=\s*\d+|brain_'),       # Scoring/engine refs
]

# Source files that are known noise generators
NOISE_SOURCES = {
    "encyclopediauniverse", "fileprocessinglog", "evidence_atoms.csv",
    "contradiction_map", "run_manifest", "pipeline_log",
}

def is_artifact(quote_text: str, source_file: str) -> bool:
    """Return True if this quote is a system artifact, not real evidence."""
    if not quote_text or len(quote_text.strip()) < 20:
        return True
    # Check source file
    src_lower = source_file.lower() if source_file else ""
    for noise in NOISE_SOURCES:
        if noise in src_lower:
            return True
    # Check content patterns
    for pat in ARTIFACT_PATTERNS:
        if pat.search(quote_text):
            return True
    return False


# ============================================================
# PHASE 4: MEEK Lane Assignment
# ============================================================

MEEK_PATTERNS = {
    "E": re.compile(r'mcneill|judicial|bias|jtc|canon|misconduct|benchbook|ex parte|disqualif|hoopes|ladas', re.I),
    "D": re.compile(r'\bppo\b|protection order|5907|stalking|harassment', re.I),
    "F": re.compile(r'\bcoa\b|366810|appeal|appellant|appellee|brief.*appeal', re.I),
    "C": re.compile(r'federal|§\s*1983|42\s*usc|conspiracy|civil rights', re.I),
    "A": re.compile(r'custody|parenting|001507|watson|child|visitation|foc|best interest|mcl 722', re.I),
    "B": re.compile(r'shady oaks|eviction|housing|trailer|002760|habitability', re.I),
}

def assign_lane(text: str) -> str:
    """Assign MEEK lane. Priority: E > D > F > C > A > B."""
    for lane, pat in MEEK_PATTERNS.items():
        if pat.search(text):
            return lane
    return "A"  # Default to custody


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("  DOSSIER PERSISTENCE ENGINE")
    print("  Filter → Dedup → Lane → INSERT → Verify")
    print("=" * 70)
    t0 = time.time()

    # --- Phase 1: Load JSON ---
    print("\n📥 PHASE 1: Loading hunt results...")
    all_quotes = []

    for jpath, source_type in [(TXT_JSON, "txt"), (PDF_JSON, "pdf")]:
        if jpath.exists():
            data = load_json(str(jpath))
            sg = data.get("smoking_guns", [])
            hv = data.get("high_value_quotes", [])
            print(f"  {source_type.upper()}: {len(sg)} smoking guns + {len(hv)} high-value")
            for item in sg + hv:
                all_quotes.append({
                    "source_file": item.get("file", ""),
                    "quote_text": item.get("quote", item.get("text", "")),
                    "score": item.get("score", 0),
                    "keywords": item.get("keywords", ""),
                    "source_type": source_type,
                })
        else:
            print(f"  {source_type.upper()}: NOT FOUND at {jpath}")

    print(f"  Total raw quotes: {len(all_quotes)}")

    # --- Phase 2: Filter artifacts ---
    print("\n🧹 PHASE 2: Filtering artifacts...")
    clean_quotes = []
    filtered_count = 0
    for q in all_quotes:
        if is_artifact(q["quote_text"], q["source_file"]):
            filtered_count += 1
        else:
            clean_quotes.append(q)
    print(f"  Filtered out: {filtered_count} artifacts")
    print(f"  Clean quotes: {len(clean_quotes)}")

    # --- Phase 3: Content-based dedup ---
    print("\n🔍 PHASE 3: Dedup (internal + against DB)...")

    # Internal dedup by content hash
    seen_hashes = set()
    deduped = []
    for q in clean_quotes:
        h = hashlib.sha256(q["quote_text"].strip().lower().encode()).hexdigest()[:16]
        if h not in seen_hashes:
            seen_hashes.add(h)
            deduped.append(q)
    internal_dupes = len(clean_quotes) - len(deduped)
    print(f"  Internal duplicates removed: {internal_dupes}")

    # DB dedup — check first 80 chars of each quote against existing rows
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")

    # Get count of existing rows
    existing_count = conn.execute("SELECT COUNT(*) FROM evidence_quotes").fetchone()[0]
    print(f"  Existing DB rows: {existing_count:,}")

    # Sample existing quote prefixes for fast dedup
    print("  Loading existing quote prefixes for dedup...")
    existing_prefixes = set()
    cursor = conn.execute("SELECT SUBSTR(quote_text, 1, 80) FROM evidence_quotes WHERE quote_text IS NOT NULL")
    for row in cursor:
        if row[0]:
            existing_prefixes.add(row[0].strip().lower())
    print(f"  Loaded {len(existing_prefixes):,} existing prefixes")

    new_quotes = []
    db_dupes = 0
    for q in deduped:
        prefix = q["quote_text"].strip().lower()[:80]
        if prefix in existing_prefixes:
            db_dupes += 1
        else:
            new_quotes.append(q)
    print(f"  DB duplicates removed: {db_dupes}")
    print(f"  Truly new quotes: {len(new_quotes)}")

    # --- Phase 4: Lane assignment ---
    print("\n🏷️ PHASE 4: MEEK lane assignment...")
    lane_counts = Counter()
    for q in new_quotes:
        lane = assign_lane(q["quote_text"])
        q["lane"] = lane
        lane_counts[lane] += 1
    for lane in sorted(lane_counts):
        print(f"  Lane {lane}: {lane_counts[lane]}")

    # --- Phase 5: Batch INSERT ---
    print(f"\n💾 PHASE 5: Inserting {len(new_quotes)} new quotes...")
    if new_quotes:
        rows = []
        for q in new_quotes:
            # Determine category from keywords
            kw = q.get("keywords", "")
            if isinstance(kw, list):
                kw = ", ".join(kw)
            category = "general"
            if any(x in kw for x in ["ex parte", "bias", "mcneill", "judicial"]):
                category = "judicial_misconduct"
            elif any(x in kw for x in ["meth", "arsenic", "poison", "fabricat"]):
                category = "false_allegations"
            elif any(x in kw for x in ["custody", "parenting", "best interest"]):
                category = "custody"
            elif any(x in kw for x in ["ppo", "contempt", "jail"]):
                category = "ppo_contempt"
            elif any(x in kw for x in ["albert", "admitted", "premeditated"]):
                category = "admissions"

            rows.append((
                q["source_file"],
                q["quote_text"][:4000],  # cap length
                None,                     # page_number
                category,
                q["lane"],
                min(q.get("score", 0) / 50.0, 1.0),  # normalize to 0-1
                None,                     # filing_refs
                f"dossier_hunt_{q['source_type']}",
                0,                        # is_duplicate
                None,                     # duplicate_of
            ))

        conn.executemany("""
            INSERT INTO evidence_quotes
                (source_file, quote_text, page_number, category, lane, relevance_score,
                 filing_refs, tags, is_duplicate, duplicate_of)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, rows)
        conn.commit()

        # Verify
        new_count = conn.execute("SELECT COUNT(*) FROM evidence_quotes").fetchone()[0]
        inserted = new_count - existing_count
        print(f"  ✅ Inserted: {inserted} rows")
        print(f"  DB total now: {new_count:,}")
    else:
        print("  ⚠️ No new quotes to insert")
        inserted = 0

    # --- Phase 6: FTS5 rebuild + report ---
    print("\n🔄 PHASE 6: Rebuilding FTS5 index...")
    try:
        conn.execute("INSERT INTO evidence_fts(evidence_fts) VALUES('rebuild')")
        conn.commit()
        print("  ✅ FTS5 index rebuilt")
    except Exception as e:
        print(f"  ⚠️ FTS5 rebuild skipped: {e}")

    conn.close()

    elapsed = time.time() - t0
    print(f"\n{'=' * 70}")
    print(f"  COMPLETE in {elapsed:.1f}s")
    print(f"  Raw quotes loaded: {len(all_quotes)}")
    print(f"  Artifacts filtered: {filtered_count}")
    print(f"  Internal dupes: {internal_dupes}")
    print(f"  DB dupes: {db_dupes}")
    print(f"  New quotes inserted: {inserted}")
    print(f"  Lane breakdown: {dict(lane_counts)}")
    print(f"{'=' * 70}")

    # Write report
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(f"# Dossier Persistence Report\n")
        f.write(f"**Elapsed:** {elapsed:.1f}s\n\n")
        f.write(f"| Metric | Count |\n|--------|-------|\n")
        f.write(f"| Raw quotes loaded | {len(all_quotes)} |\n")
        f.write(f"| Artifacts filtered | {filtered_count} |\n")
        f.write(f"| Internal duplicates | {internal_dupes} |\n")
        f.write(f"| DB duplicates | {db_dupes} |\n")
        f.write(f"| **New quotes inserted** | **{inserted}** |\n")
        f.write(f"| DB total (before) | {existing_count:,} |\n")
        f.write(f"| DB total (after) | {existing_count + inserted:,} |\n\n")
        f.write(f"## Lane Breakdown\n\n")
        for lane in sorted(lane_counts):
            f.write(f"- **Lane {lane}**: {lane_counts[lane]}\n")
        f.write(f"\n## Artifact Filter Patterns\n\n")
        f.write(f"Filtered {filtered_count} entries matching:\n")
        f.write(f"- JSON/dict syntax, pipeline run IDs, MEEK tags\n")
        f.write(f"- SQL statements, Python code, file paths\n")
        f.write(f"- System names (LitigationOS, MANBEARPIG, SINGULARITY)\n")
        f.write(f"- Known noise sources (encyclopediaUNIVERSE, FileProcessingLog)\n")
    print(f"\n📝 Report: {REPORT_FILE}")

if __name__ == "__main__":
    main()
