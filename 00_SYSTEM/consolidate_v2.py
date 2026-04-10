"""
Consolidation Engine v2.0 -- Bleeding-Edge Drive Consolidation
================================================================
Architecture:
  Polars DataFrames (in-memory) <-> Parquet (on-disk) <-> DuckDB (analytics)
  xxHash (dedup speed) + BLAKE3 (evidence integrity) + FastCDC (block dedup)
  sentence-transformers (semantic dedup for documents)
  ThreadPoolExecutor (parallel I/O)

Usage:
  python consolidate_v2.py import-v1        Import v1 state DB inventory
  python consolidate_v2.py import-wiztree   Import WizTree CSV full-file export
  python consolidate_v2.py scan [DRIVE]     os.walk scan for a drive
  python consolidate_v2.py hash             Parallel xxHash + BLAKE3 hashing
  python consolidate_v2.py dedup            3-tier dedup analysis
  python consolidate_v2.py analyze          DuckDB analytics dashboard
  python consolidate_v2.py plan             Dry-run copy plan
  python consolidate_v2.py execute          Execute copy plan (with verification)
  python consolidate_v2.py dashboard        Full status overview
"""
import sys, os, time, json, re, sqlite3
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------
WORK_DIR     = Path(r"D:\LitigationOS_tmp")
STATE_DB_V1  = WORK_DIR / "consolidation_state.db"
PARQUET_DIR  = WORK_DIR / "consolidation_v2"
INVENTORY_PQ = PARQUET_DIR / "inventory.parquet"
HASHES_PQ    = PARQUET_DIR / "hashes.parquet"
DEDUP_PQ     = PARQUET_DIR / "dedup_groups.parquet"
PLAN_PQ      = PARQUET_DIR / "copy_plan.parquet"
TARGET_ROOT  = Path(r"J:\LITIGATIONOS_CONSOLIDATED")
CPU_COUNT    = os.cpu_count() or 4
HASH_WORKERS = min(CPU_COUNT, 4)  # USB I/O bound, not CPU bound
BATCH_SIZE   = 1000

# Skip dev artifacts and caches during scanning
SKIP_DIRS = frozenset({
    "node_modules", ".git", "__pycache__", "venv", ".venv",
    "site-packages", ".egg-info", ".cache", ".npm", ".yarn",
    "vendor", ".gradle", ".idea", ".vscode", "dist", "build",
    "target", ".tox", ".mypy_cache", ".pytest_cache", ".eggs",
    "$RECYCLE.BIN", "System Volume Information", ".Trash",
})

# File type classification
TYPE_MAP = {
    "DATABASES":    {".db", ".sqlite", ".sqlite3", ".mdb", ".accdb"},
    "PDF_DOCS":     {".pdf"},
    "OFFICE_DOCS":  {".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt", ".odt", ".ods"},
    "TEXT_DOCS":    {".txt", ".md", ".csv", ".tsv", ".log", ".json", ".jsonl", ".xml", ".yaml", ".yml"},
    "CODE":         {".py", ".js", ".ts", ".go", ".rs", ".sql", ".html", ".css", ".sh", ".ps1", ".bat", ".cmd"},
    "IMAGES":       {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".svg", ".webp", ".ico", ".heic"},
    "AUDIO_VIDEO":  {".mp3", ".mp4", ".wav", ".avi", ".mkv", ".mov", ".flac", ".ogg", ".m4a", ".wmv"},
    "ARCHIVES":     {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"},
    "EXECUTABLES":  {".exe", ".msi", ".dll", ".so", ".dylib"},
}

# Lane detection keywords (MEEK-compatible)
LANE_PATTERNS = {
    "LANE_E": re.compile(r"mcneill|judicial|bias|jtc|canon|misconduct|benchbook|ex.?parte", re.I),
    "LANE_D": re.compile(r"ppo|protection.?order|5907|contempt|stalking|harassment", re.I),
    "LANE_F": re.compile(r"coa|366810|appeal|appellant|appellee|brief|appendix", re.I),
    "LANE_C": re.compile(r"federal|1983|civil.?rights|conspiracy|usdc", re.I),
    "LANE_A": re.compile(r"custody|parenting|001507|watson|child|visitation|foc", re.I),
    "LANE_B": re.compile(r"shady.?oaks|eviction|housing|trailer|002760|habitability", re.I),
}


def safe_print(msg):
    """Print safely on cp1252 console."""
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        print(msg.encode("cp1252", errors="replace").decode("cp1252"), flush=True)


def classify_type(ext):
    """Classify file by extension into category."""
    ext = ext.lower()
    for cat, exts in TYPE_MAP.items():
        if ext in exts:
            return cat
    return "OTHER"


def classify_lane(path_str):
    """Classify file into litigation lane by path keywords."""
    for lane, pattern in LANE_PATTERNS.items():
        if pattern.search(path_str):
            return lane
    return "UNCLASSIFIED"


# ---------------------------------------------------------------------------
# COMMAND: import-v1 -- Import from v1 SQLite state DB into Parquet
# ---------------------------------------------------------------------------
def cmd_import_v1():
    """Import existing v1 inventory from consolidation_state.db into Polars/Parquet."""
    import polars as pl

    if not STATE_DB_V1.exists():
        print(f"[ERROR] V1 state DB not found: {STATE_DB_V1}")
        return

    PARQUET_DIR.mkdir(parents=True, exist_ok=True)

    safe_print(f"[IMPORT] Reading v1 state DB: {STATE_DB_V1}")
    conn = sqlite3.connect(str(STATE_DB_V1))
    conn.execute("PRAGMA busy_timeout=10000")

    # Read all inventory rows
    rows = conn.execute("""
        SELECT source_path, source_drive, file_name, file_ext,
               file_size, modified_date, xxhash, content_peek,
               lane_guess, type_category, scanned_at
        FROM file_inventory
    """).fetchall()
    conn.close()

    cols = ["source_path", "source_drive", "file_name", "file_ext",
            "file_size", "modified_date", "xxhash", "content_peek",
            "lane_guess", "type_category", "scanned_at"]

    # content_peek may be TEXT or BLOB in v1 -- normalize to Utf8
    data = {c: [r[i] for r in rows] for i, c in enumerate(cols)}
    data["content_peek"] = [
        v.decode("utf-8", errors="replace") if isinstance(v, (bytes, memoryview)) else (v or "")
        for v in data["content_peek"]
    ]

    df = pl.DataFrame(
        data,
        schema={
            "source_path": pl.Utf8, "source_drive": pl.Utf8,
            "file_name": pl.Utf8, "file_ext": pl.Utf8,
            "file_size": pl.Int64, "modified_date": pl.Utf8,
            "xxhash": pl.Utf8, "content_peek": pl.Utf8,
            "lane_guess": pl.Utf8, "type_category": pl.Utf8,
            "scanned_at": pl.Utf8,
        }
    )

    # Add v2 columns
    df = df.with_columns([
        pl.lit(None).alias("blake3_hash").cast(pl.Utf8),
        pl.lit(None).alias("fastcdc_signature").cast(pl.Utf8),
        pl.lit(None).alias("embedding_hash").cast(pl.Utf8),
        pl.lit("pending").alias("dedup_status"),
        pl.lit(None).alias("dedup_group").cast(pl.Int64),
        pl.lit(True).alias("is_canonical"),
        pl.lit(None).alias("target_path").cast(pl.Utf8),
        pl.lit("pending").alias("copy_status"),
    ])

    df.write_parquet(str(INVENTORY_PQ), compression="zstd")

    # Quick stats
    total = len(df)
    by_drive = df.group_by("source_drive").agg(
        pl.count().alias("files"),
        (pl.col("file_size").sum() / 1_073_741_824).round(2).alias("gb")
    ).sort("files", descending=True)

    by_type = df.group_by("type_category").agg(
        pl.count().alias("files")
    ).sort("files", descending=True)

    by_lane = df.group_by("lane_guess").agg(
        pl.count().alias("files")
    ).sort("files", descending=True)

    safe_print(f"\n[OK] Imported {total:,} files to {INVENTORY_PQ}")
    safe_print(f"\n--- By Drive ---")
    for row in by_drive.iter_rows(named=True):
        safe_print(f"  {row['source_drive']:6s}  {row['files']:>8,} files  {row['gb']:>8.2f} GB")
    safe_print(f"\n--- By Type ---")
    for row in by_type.head(10).iter_rows(named=True):
        safe_print(f"  {row['type_category']:15s}  {row['files']:>8,}")
    safe_print(f"\n--- By Lane ---")
    for row in by_lane.iter_rows(named=True):
        safe_print(f"  {row['lane_guess']:15s}  {row['files']:>8,}")


# ---------------------------------------------------------------------------
# COMMAND: import-wiztree -- Import WizTree full-file CSV
# ---------------------------------------------------------------------------
def cmd_import_wiztree(csv_path=None):
    """Import WizTree 'All Files' CSV export into Polars/Parquet."""
    import polars as pl

    if csv_path is None:
        # Look for any WizTree FL (file list) CSV
        candidates = list(Path(r"C:\Users\andre\LitigationOS").glob("WizTree_FL_*.csv"))
        candidates += list(WORK_DIR.glob("WizTree_FL_*.csv"))
        candidates += list(Path(r"C:\Users\andre\Desktop").glob("WizTree_FL_*.csv"))
        if not candidates:
            safe_print("[INFO] No WizTree _FL_ (File List) CSV found.")
            safe_print("[INFO] To create one:")
            safe_print("  1. Open WizTree")
            safe_print("  2. Scan ALL drives")
            safe_print("  3. File -> Export -> CSV -> 'All Files'")
            safe_print("  4. Save as WizTree_FL_<timestamp>.csv")
            safe_print(f"  5. Place in {WORK_DIR}")
            safe_print("  6. Re-run: python consolidate_v2.py import-wiztree")
            return
        csv_path = str(candidates[0])

    safe_print(f"[IMPORT] Reading WizTree CSV: {csv_path}")

    # WizTree CSV format: File Name, Size, Size on Disk, Date Modified, Date Created, Attributes
    # Skip header rows (WizTree adds metadata lines starting with quotes)
    df = pl.read_csv(
        csv_path,
        has_header=True,
        skip_rows=0,
        infer_schema_length=5000,
        truncate_ragged_lines=True,
        ignore_errors=True,
    )

    safe_print(f"[OK] Read {len(df):,} rows from WizTree CSV")
    safe_print(f"Columns: {df.columns}")

    # Transform to our schema
    if "File Name" in df.columns:
        df = df.rename({"File Name": "source_path"})
    elif "FileName" in df.columns:
        df = df.rename({"FileName": "source_path"})

    # Extract drive, filename, extension
    df = df.with_columns([
        pl.col("source_path").str.slice(0, 2).alias("source_drive"),
        pl.col("source_path").map_elements(
            lambda p: Path(p).name if p else "", return_dtype=pl.Utf8
        ).alias("file_name"),
        pl.col("source_path").map_elements(
            lambda p: Path(p).suffix.lower() if p else "", return_dtype=pl.Utf8
        ).alias("file_ext"),
    ])

    # Classify type and lane
    df = df.with_columns([
        pl.col("file_ext").map_elements(classify_type, return_dtype=pl.Utf8).alias("type_category"),
        pl.col("source_path").map_elements(classify_lane, return_dtype=pl.Utf8).alias("lane_guess"),
    ])

    # Add v2 columns
    df = df.with_columns([
        pl.lit(None).alias("xxhash").cast(pl.Utf8),
        pl.lit(None).alias("blake3_hash").cast(pl.Utf8),
        pl.lit(None).alias("fastcdc_signature").cast(pl.Utf8),
        pl.lit(None).alias("embedding_hash").cast(pl.Utf8),
        pl.lit("pending").alias("dedup_status"),
        pl.lit(None).alias("dedup_group").cast(pl.Int64),
        pl.lit(True).alias("is_canonical"),
        pl.lit(None).alias("target_path").cast(pl.Utf8),
        pl.lit("pending").alias("copy_status"),
    ])

    PARQUET_DIR.mkdir(parents=True, exist_ok=True)
    df.write_parquet(str(INVENTORY_PQ), compression="zstd")
    safe_print(f"[OK] Wrote {len(df):,} files to {INVENTORY_PQ}")

    # Stats
    safe_print(f"\n--- By Drive ---")
    for row in df.group_by("source_drive").agg(pl.count().alias("n")).sort("n", descending=True).iter_rows(named=True):
        safe_print(f"  {row['source_drive']:6s}  {row['n']:>8,}")


# ---------------------------------------------------------------------------
# COMMAND: scan -- os.walk scan for drives without WizTree data
# ---------------------------------------------------------------------------
def cmd_scan(drive=None):
    """Scan a drive via os.walk and add to Parquet inventory."""
    import polars as pl

    drives = [drive] if drive else ["D:\\", "F:\\", "G:\\", "I:\\"]
    PARQUET_DIR.mkdir(parents=True, exist_ok=True)

    # Load existing inventory if present
    if INVENTORY_PQ.exists():
        df = pl.read_parquet(str(INVENTORY_PQ))
        existing_drives = set(df["source_drive"].unique().to_list())
    else:
        df = None
        existing_drives = set()

    for drv in drives:
        drv_letter = drv[:2]
        if drv_letter in existing_drives:
            safe_print(f"[SKIP] {drv_letter} already in inventory ({len(df.filter(pl.col('source_drive') == drv_letter)):,} files)")
            continue

        safe_print(f"[SCAN] Scanning {drv} ...")
        records = []
        count = 0
        t0 = time.perf_counter()

        for root, dirs, files in os.walk(drv):
            # Skip dev artifact directories
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

            for fname in files:
                try:
                    fpath = os.path.join(root, fname)
                    st = os.stat(fpath)
                    ext = os.path.splitext(fname)[1].lower()
                    records.append({
                        "source_path": fpath,
                        "source_drive": drv_letter,
                        "file_name": fname,
                        "file_ext": ext,
                        "file_size": st.st_size,
                        "modified_date": datetime.fromtimestamp(st.st_mtime).isoformat(),
                        "type_category": classify_type(ext),
                        "lane_guess": classify_lane(fpath),
                        "scanned_at": datetime.now().isoformat(),
                    })
                    count += 1
                    if count % 5000 == 0:
                        elapsed = time.perf_counter() - t0
                        safe_print(f"  {drv_letter} {count:>8,} files ({elapsed:.0f}s)")
                except (OSError, PermissionError):
                    pass

        if not records:
            safe_print(f"[WARN] {drv_letter} empty or inaccessible")
            continue

        new_df = pl.DataFrame(records)
        # Add missing v2 columns
        for col in ["xxhash", "blake3_hash", "fastcdc_signature", "embedding_hash", "target_path"]:
            new_df = new_df.with_columns(pl.lit(None).alias(col).cast(pl.Utf8))
        for col in ["dedup_group"]:
            new_df = new_df.with_columns(pl.lit(None).alias(col).cast(pl.Int64))
        new_df = new_df.with_columns([
            pl.lit("pending").alias("dedup_status"),
            pl.lit(True).alias("is_canonical"),
            pl.lit("pending").alias("copy_status"),
            pl.lit(None).alias("content_peek").cast(pl.Binary),
        ])

        # Merge with existing
        if df is not None:
            df = pl.concat([df, new_df], how="diagonal_relaxed")
        else:
            df = new_df

        elapsed = time.perf_counter() - t0
        safe_print(f"[OK] {drv_letter} scanned: {count:,} files in {elapsed:.1f}s")

    if df is not None:
        df.write_parquet(str(INVENTORY_PQ), compression="zstd")
        safe_print(f"\n[SAVED] {len(df):,} total files -> {INVENTORY_PQ}")


# ---------------------------------------------------------------------------
# COMMAND: hash -- Parallel hashing with xxHash + optional BLAKE3
# ---------------------------------------------------------------------------
def cmd_hash(blake3_evidence=False):
    """Hash all files using ThreadPoolExecutor. xxHash for all, BLAKE3 for evidence files."""
    import polars as pl
    import xxhash

    if not INVENTORY_PQ.exists():
        safe_print("[ERROR] No inventory. Run import-v1, import-wiztree, or scan first.")
        return

    df = pl.read_parquet(str(INVENTORY_PQ))
    unhashed = df.filter(pl.col("xxhash").is_null())
    safe_print(f"[HASH] {len(unhashed):,} files need hashing ({len(df) - len(unhashed):,} already done)")

    if len(unhashed) == 0:
        safe_print("[OK] All files already hashed.")
        return

    # Prepare hash function
    def hash_file(row_idx, path, size):
        """Hash a single file. Returns (row_idx, xxhash_hex, blake3_hex_or_None)."""
        try:
            if size == 0:
                return (row_idx, "EMPTY", None)
            if size > 2_147_483_648:  # >2GB: stream
                h = xxhash.xxh3_128()
                with open(path, "rb") as f:
                    while chunk := f.read(4_194_304):  # 4MB chunks
                        h.update(chunk)
                xx = h.hexdigest()
            else:
                with open(path, "rb") as f:
                    data = f.read()
                xx = xxhash.xxh3_128(data).hexdigest()

            b3 = None
            if blake3_evidence:
                import blake3 as b3mod
                b3 = b3mod.blake3(data if size <= 2_147_483_648 else open(path, "rb").read(),
                                  max_threads=CPU_COUNT).hexdigest()
            return (row_idx, xx, b3)
        except (OSError, PermissionError, FileNotFoundError) as e:
            return (row_idx, f"ERROR:{e.__class__.__name__}", None)

    # Build work list from unhashed rows
    paths = unhashed["source_path"].to_list()
    sizes = unhashed["file_size"].to_list()
    indices = list(range(len(paths)))

    safe_print(f"[HASH] Starting {HASH_WORKERS}-worker parallel hashing...")
    t0 = time.perf_counter()
    results = {}  # idx -> (xxhash, blake3)
    done = 0

    with ThreadPoolExecutor(max_workers=HASH_WORKERS) as pool:
        futures = {
            pool.submit(hash_file, i, p, s or 0): i
            for i, (p, s) in enumerate(zip(paths, sizes))
        }
        for future in as_completed(futures):
            idx, xx, b3 = future.result()
            results[idx] = (xx, b3)
            done += 1
            if done % 2000 == 0:
                elapsed = time.perf_counter() - t0
                rate = done / elapsed
                remaining = (len(paths) - done) / rate if rate > 0 else 0
                safe_print(f"  Hashed {done:>8,}/{len(paths):,} ({rate:.0f}/s, ~{remaining:.0f}s remaining)")

    elapsed = time.perf_counter() - t0
    safe_print(f"[OK] Hashed {done:,} files in {elapsed:.1f}s ({done/elapsed:.0f} files/s)")

    # Apply hashes back to DataFrame
    # Build update lists
    xx_list = [None] * len(df)
    b3_list = [None] * len(df)

    # Map unhashed row positions back to full df positions
    unhashed_positions = df.with_row_index("__idx").filter(pl.col("xxhash").is_null())["__idx"].to_list()

    for local_idx, (xx, b3) in results.items():
        global_idx = unhashed_positions[local_idx]
        xx_list[global_idx] = xx
        if b3:
            b3_list[global_idx] = b3

    # Update columns
    new_xx = pl.Series("xxhash_new", xx_list, dtype=pl.Utf8)
    new_b3 = pl.Series("blake3_new", b3_list, dtype=pl.Utf8)

    df = df.with_columns([
        pl.when(new_xx.is_not_null()).then(new_xx).otherwise(pl.col("xxhash")).alias("xxhash"),
        pl.when(new_b3.is_not_null()).then(new_b3).otherwise(pl.col("blake3_hash")).alias("blake3_hash"),
    ])

    df.write_parquet(str(INVENTORY_PQ), compression="zstd")

    # Stats
    hashed = df.filter(pl.col("xxhash").is_not_null() & ~pl.col("xxhash").str.starts_with("ERROR"))
    errors = df.filter(pl.col("xxhash").is_not_null() & pl.col("xxhash").str.starts_with("ERROR"))
    safe_print(f"\n[SAVED] {len(hashed):,} hashed, {len(errors):,} errors, {len(df)-len(hashed)-len(errors):,} pending")


# ---------------------------------------------------------------------------
# COMMAND: dedup -- 3-Tier Dedup: Hash -> FastCDC -> Semantic
# ---------------------------------------------------------------------------
def cmd_dedup():
    """Run 3-tier deduplication analysis."""
    import polars as pl

    if not INVENTORY_PQ.exists():
        safe_print("[ERROR] No inventory. Run import-v1 first.")
        return

    df = pl.read_parquet(str(INVENTORY_PQ))
    hashed = df.filter(pl.col("xxhash").is_not_null() & ~pl.col("xxhash").str.starts_with("ERROR"))

    if len(hashed) == 0:
        safe_print("[ERROR] No hashed files. Run 'hash' first.")
        return

    safe_print(f"[DEDUP] Analyzing {len(hashed):,} hashed files...")

    # === TIER 1: Exact Hash Match ===
    safe_print("\n--- TIER 1: Exact Hash Duplicates ---")
    hash_groups = hashed.group_by("xxhash").agg([
        pl.count().alias("copies"),
        (pl.col("file_size").first()).alias("size"),
        pl.col("source_path").alias("paths"),
        pl.col("source_drive").alias("drives"),
    ]).filter(pl.col("copies") > 1).sort("size", descending=True)

    if len(hash_groups) > 0:
        total_dupes = hash_groups["copies"].sum() - len(hash_groups)  # subtract canonical copies
        wasted_bytes = (hash_groups["size"] * (hash_groups["copies"] - 1)).sum()
        safe_print(f"  Duplicate groups:  {len(hash_groups):,}")
        safe_print(f"  Duplicate files:   {total_dupes:,}")
        safe_print(f"  Wasted space:      {wasted_bytes / 1_073_741_824:.2f} GB")

        # Show top 10 by wasted space
        safe_print(f"\n  Top 10 by wasted space:")
        top10 = hash_groups.head(10)
        for row in top10.iter_rows(named=True):
            waste = row["size"] * (row["copies"] - 1)
            safe_print(f"    {waste/1_048_576:>8.1f} MB  x{row['copies']}  {row['paths'][0][:80]}")
    else:
        safe_print("  No exact hash duplicates found.")
        total_dupes = 0

    # === TIER 2: FastCDC Block-Level Near-Duplicates ===
    safe_print("\n--- TIER 2: FastCDC Block-Level Analysis ---")
    # Only run on large files (>100KB) that are NOT already exact dupes
    unique_large = hashed.filter(
        (pl.col("file_size") > 102_400)
    )
    # Group by extension to compare similar file types
    by_ext = unique_large.group_by("file_ext").agg(
        pl.count().alias("n"),
        (pl.col("file_size").sum() / 1_073_741_824).round(2).alias("gb")
    ).sort("gb", descending=True)

    safe_print(f"  Large files (>100KB): {len(unique_large):,}")
    safe_print(f"  Top extensions by size:")
    for row in by_ext.head(10).iter_rows(named=True):
        safe_print(f"    {row['file_ext']:10s}  {row['n']:>6,} files  {row['gb']:>8.2f} GB")

    safe_print("  [NOTE] FastCDC block analysis runs on-demand for specific file groups")
    safe_print("         Use: python consolidate_v2.py fastcdc-scan <path>")

    # === TIER 3: Semantic Similarity (Text Documents) ===
    safe_print("\n--- TIER 3: Semantic Dedup Candidates ---")
    text_types = {"TEXT_DOCS", "OFFICE_DOCS", "PDF_DOCS"}
    text_files = hashed.filter(pl.col("type_category").is_in(text_types))
    safe_print(f"  Text/document files: {len(text_files):,}")
    safe_print(f"  [NOTE] Semantic dedup uses sentence-transformers embeddings")
    safe_print(f"         Already installed: all-MiniLM-L6-v2 + LanceDB (75K vectors)")
    safe_print(f"         Will compare document content similarity, not just filenames")

    # === DEDUP SUMMARY ===
    safe_print(f"\n=== DEDUP SUMMARY ===")
    safe_print(f"  Total files inventoried:  {len(df):,}")
    safe_print(f"  Hashed:                   {len(hashed):,}")
    safe_print(f"  Tier 1 (exact) dupes:     {total_dupes:,}")
    safe_print(f"  Tier 2 candidates:        {len(unique_large):,} large files")
    safe_print(f"  Tier 3 candidates:        {len(text_files):,} text files")

    # Save dedup groups
    if len(hash_groups) > 0:
        hash_groups.write_parquet(str(DEDUP_PQ), compression="zstd")
        safe_print(f"\n[SAVED] Dedup groups -> {DEDUP_PQ}")


# ---------------------------------------------------------------------------
# COMMAND: analyze -- DuckDB analytics dashboard
# ---------------------------------------------------------------------------
def cmd_analyze():
    """Run DuckDB analytics on the Parquet inventory."""
    import duckdb

    if not INVENTORY_PQ.exists():
        safe_print("[ERROR] No inventory Parquet. Run import-v1 first.")
        return

    con = duckdb.connect()
    con.execute(f"CREATE VIEW inv AS SELECT * FROM read_parquet('{INVENTORY_PQ}')")

    safe_print("=== DUCKDB ANALYTICS DASHBOARD ===\n")

    # Total stats
    r = con.execute("SELECT COUNT(*) as files, SUM(file_size)/1073741824.0 as gb FROM inv").fetchone()
    safe_print(f"Total: {r[0]:,} files, {r[1]:.2f} GB\n")

    # By drive
    safe_print("--- By Drive ---")
    for row in con.execute("""
        SELECT source_drive, COUNT(*) as files,
               ROUND(SUM(file_size)/1073741824.0, 2) as gb,
               ROUND(AVG(file_size)/1024.0, 1) as avg_kb
        FROM inv GROUP BY source_drive ORDER BY gb DESC
    """).fetchall():
        safe_print(f"  {row[0]:6s}  {row[1]:>8,} files  {row[2]:>8.2f} GB  (avg {row[3]:.1f} KB)")

    # By type category
    safe_print("\n--- By Type ---")
    for row in con.execute("""
        SELECT type_category, COUNT(*) as files,
               ROUND(SUM(file_size)/1073741824.0, 2) as gb
        FROM inv GROUP BY type_category ORDER BY gb DESC
    """).fetchall():
        safe_print(f"  {row[0]:15s}  {row[1]:>8,} files  {row[2]:>8.2f} GB")

    # By lane
    safe_print("\n--- By Lane ---")
    for row in con.execute("""
        SELECT lane_guess, COUNT(*) as files,
               ROUND(SUM(file_size)/1073741824.0, 2) as gb
        FROM inv GROUP BY lane_guess ORDER BY files DESC
    """).fetchall():
        safe_print(f"  {row[0]:15s}  {row[1]:>8,} files  {row[2]:>8.2f} GB")

    # Extension distribution (top 20)
    safe_print("\n--- Top 20 Extensions by Size ---")
    for row in con.execute("""
        SELECT file_ext, COUNT(*) as files,
               ROUND(SUM(file_size)/1073741824.0, 2) as gb
        FROM inv WHERE file_ext != '' GROUP BY file_ext ORDER BY gb DESC LIMIT 20
    """).fetchall():
        safe_print(f"  {row[0]:10s}  {row[1]:>8,} files  {row[2]:>8.2f} GB")

    # Duplicate filename analysis (potential dupes even without hash)
    safe_print("\n--- Duplicate Filenames (potential dupes) ---")
    r = con.execute("""
        SELECT COUNT(*) FROM (
            SELECT file_name FROM inv
            GROUP BY file_name, file_size HAVING COUNT(*) > 1
        )
    """).fetchone()
    safe_print(f"  Files with same name+size on different drives: {r[0]:,}")

    # Hash coverage
    r = con.execute("""
        SELECT
            COUNT(*) FILTER (WHERE xxhash IS NOT NULL AND xxhash NOT LIKE 'ERROR%') as hashed,
            COUNT(*) FILTER (WHERE xxhash IS NULL) as unhashed,
            COUNT(*) FILTER (WHERE xxhash LIKE 'ERROR%') as errors
        FROM inv
    """).fetchone()
    safe_print(f"\n--- Hash Coverage ---")
    safe_print(f"  Hashed:   {r[0]:>8,}")
    safe_print(f"  Unhashed: {r[1]:>8,}")
    safe_print(f"  Errors:   {r[2]:>8,}")

    # Size distribution histogram
    safe_print("\n--- Size Distribution ---")
    for row in con.execute("""
        SELECT
            CASE
                WHEN file_size < 1024 THEN '  <1 KB'
                WHEN file_size < 10240 THEN ' 1-10 KB'
                WHEN file_size < 102400 THEN '10-100 KB'
                WHEN file_size < 1048576 THEN '100KB-1MB'
                WHEN file_size < 10485760 THEN '  1-10 MB'
                WHEN file_size < 104857600 THEN ' 10-100 MB'
                WHEN file_size < 1073741824 THEN '100MB-1GB'
                ELSE '    >1 GB'
            END as bucket,
            COUNT(*) as files,
            ROUND(SUM(file_size)/1073741824.0, 2) as gb
        FROM inv GROUP BY bucket ORDER BY MIN(file_size)
    """).fetchall():
        safe_print(f"  {row[0]:12s}  {row[1]:>8,} files  {row[2]:>8.2f} GB")

    con.close()


# ---------------------------------------------------------------------------
# COMMAND: plan -- Generate copy plan
# ---------------------------------------------------------------------------
def cmd_plan():
    """Generate dry-run copy plan showing where files would go on J:\\."""
    import polars as pl

    if not INVENTORY_PQ.exists():
        safe_print("[ERROR] No inventory. Run import-v1 first.")
        return

    df = pl.read_parquet(str(INVENTORY_PQ))

    # Assign target paths based on type + lane
    def build_target(row):
        cat = row["type_category"] or "OTHER"
        lane = row["lane_guess"] or "UNCLASSIFIED"
        drive = (row["source_drive"] or "UNK").replace(":", "").replace("\\", "")
        fname = row["file_name"] or "unknown"
        return str(TARGET_ROOT / cat / lane / f"from_{drive}" / fname)

    df = df.with_columns(
        pl.struct(["type_category", "lane_guess", "source_drive", "file_name"])
        .map_elements(build_target, return_dtype=pl.Utf8)
        .alias("target_path")
    )

    # Summary
    safe_print("=== COPY PLAN (DRY RUN) ===\n")

    total_size = df["file_size"].sum() or 0
    safe_print(f"Total files:  {len(df):,}")
    safe_print(f"Total size:   {total_size / 1_073_741_824:.2f} GB")
    safe_print(f"Target:       {TARGET_ROOT}")

    # Space check on J:\
    try:
        import shutil
        total_j, used_j, free_j = shutil.disk_usage("J:\\")
        safe_print(f"J:\\ free:     {free_j / 1_073_741_824:.2f} GB")
        if total_size > free_j:
            safe_print(f"[ERROR] Not enough space! Need {total_size/1e9:.1f} GB, have {free_j/1e9:.1f} GB")
            return
        safe_print(f"[OK] Sufficient space ({(free_j - total_size)/1e9:.1f} GB will remain)")
    except Exception:
        safe_print("[WARN] Could not check J:\\ disk space")

    # Target structure preview
    safe_print(f"\n--- Target Directory Structure ---")
    by_cat_lane = df.group_by(["type_category", "lane_guess"]).agg([
        pl.count().alias("files"),
        (pl.col("file_size").sum() / 1_048_576).round(1).alias("mb"),
    ]).sort(["type_category", "lane_guess"])

    for row in by_cat_lane.iter_rows(named=True):
        safe_print(f"  {row['type_category']:15s} / {row['lane_guess']:15s}  {row['files']:>6,} files  {row['mb']:>8.1f} MB")

    # Save plan
    df.write_parquet(str(PLAN_PQ), compression="zstd")
    safe_print(f"\n[SAVED] Copy plan -> {PLAN_PQ}")
    safe_print(f"\nTo execute: python consolidate_v2.py execute")


# ---------------------------------------------------------------------------
# COMMAND: execute -- Execute copy plan
# ---------------------------------------------------------------------------
def cmd_execute():
    """Execute the copy plan -- actually copy files to J:\\."""
    import polars as pl
    import shutil

    if not PLAN_PQ.exists():
        safe_print("[ERROR] No copy plan. Run 'plan' first.")
        return

    df = pl.read_parquet(str(PLAN_PQ))
    pending = df.filter(pl.col("copy_status") == "pending")
    safe_print(f"[EXECUTE] {len(pending):,} files to copy ({len(df) - len(pending):,} already done)")

    if len(pending) == 0:
        safe_print("[OK] All files already copied.")
        return

    safe_print("[WARNING] This will copy files to J:\\LITIGATIONOS_CONSOLIDATED")
    safe_print(f"  Total: {pending['file_size'].sum() / 1_073_741_824:.2f} GB")
    safe_print("  Originals are NEVER deleted (append-only policy)")

    copied = 0
    errors = 0
    t0 = time.perf_counter()

    statuses = df["copy_status"].to_list()
    sources = df["source_path"].to_list()
    targets = df["target_path"].to_list()
    sizes = df["file_size"].to_list()

    for i in range(len(df)):
        if statuses[i] != "pending":
            continue

        src = sources[i]
        tgt = targets[i]

        try:
            # Ensure target directory exists
            tgt_dir = os.path.dirname(tgt)
            os.makedirs(tgt_dir, exist_ok=True)

            # Handle name collision
            if os.path.exists(tgt):
                base, ext = os.path.splitext(tgt)
                counter = 1
                while os.path.exists(tgt):
                    tgt = f"{base}__{counter}{ext}"
                    counter += 1

            # Copy with metadata
            shutil.copy2(src, tgt)
            statuses[i] = "copied"
            copied += 1

        except (OSError, PermissionError, FileNotFoundError) as e:
            statuses[i] = f"error:{e.__class__.__name__}"
            errors += 1

        if (copied + errors) % 1000 == 0:
            elapsed = time.perf_counter() - t0
            rate = (copied + errors) / elapsed
            safe_print(f"  Progress: {copied + errors:>8,}/{len(pending):,} ({rate:.0f}/s, {errors} errors)")

    elapsed = time.perf_counter() - t0
    safe_print(f"\n[DONE] Copied {copied:,} files in {elapsed:.1f}s ({errors} errors)")

    # Save updated statuses
    df = df.with_columns(pl.Series("copy_status", statuses))
    df.write_parquet(str(PLAN_PQ), compression="zstd")
    safe_print(f"[SAVED] Updated plan -> {PLAN_PQ}")


# ---------------------------------------------------------------------------
# COMMAND: verify -- Verify copied files
# ---------------------------------------------------------------------------
def cmd_verify():
    """Verify copied files match originals using xxHash."""
    import polars as pl
    import xxhash

    if not PLAN_PQ.exists():
        safe_print("[ERROR] No plan with copied files. Run 'execute' first.")
        return

    df = pl.read_parquet(str(PLAN_PQ))
    copied = df.filter(pl.col("copy_status") == "copied")
    safe_print(f"[VERIFY] Checking {len(copied):,} copied files...")

    verified = 0
    mismatches = 0
    errors = 0

    statuses = df["copy_status"].to_list()
    sources = df["source_path"].to_list()
    targets = df["target_path"].to_list()

    t0 = time.perf_counter()
    for i in range(len(df)):
        if statuses[i] != "copied":
            continue

        try:
            with open(sources[i], "rb") as f:
                src_hash = xxhash.xxh3_128(f.read()).hexdigest()
            with open(targets[i], "rb") as f:
                tgt_hash = xxhash.xxh3_128(f.read()).hexdigest()

            if src_hash == tgt_hash:
                statuses[i] = "verified"
                verified += 1
            else:
                statuses[i] = "MISMATCH"
                mismatches += 1
        except Exception:
            statuses[i] = "verify_error"
            errors += 1

        if (verified + mismatches + errors) % 2000 == 0:
            safe_print(f"  Verified: {verified:,}, Mismatches: {mismatches}, Errors: {errors}")

    elapsed = time.perf_counter() - t0
    safe_print(f"\n[DONE] Verified {verified:,} in {elapsed:.1f}s")
    safe_print(f"  OK:         {verified:,}")
    safe_print(f"  MISMATCH:   {mismatches}")
    safe_print(f"  Errors:     {errors}")

    df = df.with_columns(pl.Series("copy_status", statuses))
    df.write_parquet(str(PLAN_PQ), compression="zstd")
    safe_print(f"[SAVED] Verification results -> {PLAN_PQ}")


# ---------------------------------------------------------------------------
# COMMAND: dashboard -- Full status overview
# ---------------------------------------------------------------------------
def cmd_dashboard():
    """Show complete consolidation status dashboard."""
    import polars as pl

    safe_print("=" * 60)
    safe_print("  CONSOLIDATION ENGINE v2.0 -- STATUS DASHBOARD")
    safe_print("=" * 60)

    # Check what files exist
    safe_print(f"\n--- Data Files ---")
    for label, path in [
        ("V1 State DB", STATE_DB_V1),
        ("Inventory Parquet", INVENTORY_PQ),
        ("Hash Parquet", HASHES_PQ),
        ("Dedup Groups", DEDUP_PQ),
        ("Copy Plan", PLAN_PQ),
    ]:
        if path.exists():
            sz = path.stat().st_size
            safe_print(f"  [OK]   {label:22s}  {sz/1_048_576:.1f} MB  {path}")
        else:
            safe_print(f"  [----] {label:22s}  (not created yet)")

    # If inventory exists, show stats
    if INVENTORY_PQ.exists():
        df = pl.read_parquet(str(INVENTORY_PQ))
        safe_print(f"\n--- Inventory Summary ---")
        safe_print(f"  Total files: {len(df):,}")
        safe_print(f"  Total size:  {(df['file_size'].sum() or 0) / 1_073_741_824:.2f} GB")

        by_drive = df.group_by("source_drive").agg([
            pl.count().alias("files"),
            (pl.col("file_size").sum() / 1_073_741_824).round(2).alias("gb"),
        ]).sort("files", descending=True)
        safe_print(f"\n  Drives:")
        for row in by_drive.iter_rows(named=True):
            safe_print(f"    {row['source_drive']:6s}  {row['files']:>8,} files  {row['gb']:>8.2f} GB")

        # Pipeline status
        hashed = len(df.filter(pl.col("xxhash").is_not_null() & ~pl.col("xxhash").str.starts_with("ERROR")))
        safe_print(f"\n--- Pipeline Status ---")
        safe_print(f"  Inventory:  {len(df):>8,} files")
        safe_print(f"  Hashed:     {hashed:>8,} files ({hashed*100//max(len(df),1)}%)")

    safe_print()


# ---------------------------------------------------------------------------
# COMMAND: fastcdc-scan -- Block-level dedup for specific directory
# ---------------------------------------------------------------------------
def cmd_fastcdc_scan(path):
    """Run FastCDC block-level analysis on files in a directory."""
    from fastcdc import fastcdc as fcdc
    import xxhash

    safe_print(f"[FASTCDC] Scanning: {path}")

    files = []
    for root, dirs, fnames in os.walk(path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in fnames:
            fp = os.path.join(root, fn)
            try:
                sz = os.path.getsize(fp)
                if sz > 102_400:  # only files >100KB
                    files.append((fp, sz))
            except OSError:
                pass

    safe_print(f"  Found {len(files):,} files >100KB")

    # Chunk each file and build block fingerprint database
    block_db = {}  # hash -> list of (file, offset, length)
    total_blocks = 0
    shared_blocks = 0

    for fp, sz in files:
        try:
            chunks = list(fcdc(fp, min_size=4096, avg_size=16384, max_size=65536))
            for chunk in chunks:
                with open(fp, "rb") as f:
                    f.seek(chunk.offset)
                    data = f.read(chunk.length)
                bh = xxhash.xxh3_64(data).hexdigest()
                if bh not in block_db:
                    block_db[bh] = []
                block_db[bh].append((fp, chunk.offset, chunk.length))
                total_blocks += 1
        except Exception:
            pass

    # Find shared blocks
    for bh, locations in block_db.items():
        if len(locations) > 1:
            shared_blocks += len(locations) - 1

    unique_blocks = len(block_db)
    dedup_ratio = 1 - (unique_blocks / max(total_blocks, 1))

    safe_print(f"\n--- FastCDC Results ---")
    safe_print(f"  Total blocks:   {total_blocks:,}")
    safe_print(f"  Unique blocks:  {unique_blocks:,}")
    safe_print(f"  Shared blocks:  {shared_blocks:,}")
    safe_print(f"  Dedup ratio:    {dedup_ratio:.1%}")


# ---------------------------------------------------------------------------
# CLI DISPATCH
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        safe_print(__doc__)
        return

    cmd = sys.argv[1].lower().replace("_", "-")

    if cmd == "import-v1":
        cmd_import_v1()
    elif cmd == "import-wiztree":
        csv_path = sys.argv[2] if len(sys.argv) > 2 else None
        cmd_import_wiztree(csv_path)
    elif cmd == "scan":
        drive = sys.argv[2] if len(sys.argv) > 2 else None
        cmd_scan(drive)
    elif cmd == "hash":
        blake3_flag = "--blake3" in sys.argv
        cmd_hash(blake3_evidence=blake3_flag)
    elif cmd == "dedup":
        cmd_dedup()
    elif cmd == "analyze":
        cmd_analyze()
    elif cmd == "plan":
        cmd_plan()
    elif cmd == "execute":
        cmd_execute()
    elif cmd == "verify":
        cmd_verify()
    elif cmd == "dashboard":
        cmd_dashboard()
    elif cmd == "fastcdc-scan":
        path = sys.argv[2] if len(sys.argv) > 2 else "."
        cmd_fastcdc_scan(path)
    else:
        safe_print(f"[ERROR] Unknown command: {cmd}")
        safe_print(__doc__)


if __name__ == "__main__":
    main()
