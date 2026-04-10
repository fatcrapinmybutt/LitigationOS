"""
Phase 0: Full File Tree Inventory — DuckDB-Powered Disk Awareness
Scans all accessible drives, loads into DuckDB for instant analytics.
Outputs: J:\LitigationOS_CENTRAL\FULL_INVENTORY.parquet + summary report.

Uses os.scandir (single-pass, fastest Python method) with error resilience.
"""
import os
import sys
import time
import hashlib
import sqlite3
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# DuckDB for analytics
try:
    import duckdb
    HAS_DUCKDB = True
except ImportError:
    HAS_DUCKDB = False
    print("[WARN] DuckDB not available — falling back to SQLite analytics")

# Polars for fast DataFrames
try:
    import polars as pl
    HAS_POLARS = True
except ImportError:
    HAS_POLARS = False


# ── Configuration ──────────────────────────────────────────────────
DRIVES_TO_SCAN = ["C:\\", "D:\\", "F:\\", "G:\\", "I:\\", "J:\\"]
OUTPUT_DIR = Path("J:\\LitigationOS_CENTRAL")
PARQUET_PATH = OUTPUT_DIR / "FULL_INVENTORY.parquet"
REPORT_PATH = OUTPUT_DIR / "DISK_AWARENESS_REPORT.md"
BATCH_SIZE = 50_000

# Skip directories that are massive bloat and not evidence
SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "pytools_venv", ".tox", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", "site-packages", "dist-packages",
    "$Recycle.Bin", "System Volume Information",
    "Windows", "Program Files", "Program Files (x86)",
    "ProgramData", "AppData",
}

# High-value evidence extensions
EVIDENCE_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".txt", ".md", ".csv", ".json",
    ".mp4", ".mp3", ".wav", ".m4a", ".mbox", ".eml",
    ".jpg", ".jpeg", ".png", ".tiff", ".bmp",
    ".xlsx", ".xls", ".rtf", ".odt",
    ".db", ".sqlite", ".sqlite3",
}

# Bloat extensions (valuable to catalog but low evidence value)
BLOAT_EXTENSIONS = {
    ".pyc", ".pyi", ".pyo", ".chk", ".tmp", ".bak",
    ".log", ".cache", ".dmp",
}


def scan_drive(drive_path: str, callback=None) -> list[dict]:
    """Scan a drive using os.scandir (single-pass, fastest Python method).
    
    Yields dicts with: path, name, ext, size, mtime, drive, is_evidence, is_bloat
    """
    rows = []
    errors = 0
    count = 0
    drive_letter = drive_path[0]
    
    def _scan_dir(dir_path: str, depth: int = 0):
        nonlocal errors, count
        if depth > 30:  # prevent infinite recursion from symlink loops
            return
        try:
            with os.scandir(dir_path) as it:
                for entry in it:
                    try:
                        name = entry.name
                        # Skip known bloat directories
                        if entry.is_dir(follow_symlinks=False):
                            if name in SKIP_DIRS or name.startswith('.'):
                                continue
                            _scan_dir(entry.path, depth + 1)
                            continue
                        
                        if not entry.is_file(follow_symlinks=False):
                            continue
                        
                        stat = entry.stat(follow_symlinks=False)
                        ext = os.path.splitext(name)[1].lower()
                        
                        rows.append({
                            "file_path": entry.path,
                            "file_name": name,
                            "extension": ext,
                            "size_bytes": stat.st_size,
                            "modified_ts": stat.st_mtime,
                            "drive_letter": drive_letter,
                            "is_evidence": ext in EVIDENCE_EXTENSIONS,
                            "is_bloat": ext in BLOAT_EXTENSIONS,
                            "depth": depth,
                        })
                        count += 1
                        
                        if count % 50000 == 0 and callback:
                            callback(drive_letter, count, errors)
                            
                    except (PermissionError, OSError):
                        errors += 1
                        continue
        except (PermissionError, OSError):
            errors += 1
    
    print(f"[SCAN] Starting {drive_path} ...")
    t0 = time.time()
    _scan_dir(drive_path)
    elapsed = time.time() - t0
    print(f"[SCAN] {drive_letter}:\\ complete: {count:,} files, {errors} errors, {elapsed:.1f}s")
    return rows


def progress_callback(drive: str, count: int, errors: int):
    print(f"  [{drive}:\\] {count:,} files scanned ({errors} errors)...")


def build_analytics(all_rows: list[dict]) -> dict:
    """Build analytics using DuckDB (or pure Python fallback)."""
    analytics = {}
    
    if HAS_DUCKDB and HAS_POLARS:
        print(f"\n[ANALYTICS] Loading {len(all_rows):,} rows into DuckDB via Polars...")
        t0 = time.time()
        
        df = pl.DataFrame(all_rows)
        
        # Save to Parquet for persistence
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        df.write_parquet(str(PARQUET_PATH))
        print(f"[ANALYTICS] Saved to {PARQUET_PATH} ({PARQUET_PATH.stat().st_size / 1048576:.1f} MB)")
        
        # DuckDB analytics
        con = duckdb.connect()
        con.execute("CREATE TABLE inv AS SELECT * FROM read_parquet(?)", [str(PARQUET_PATH)])
        
        # Drive summary
        drive_summary = con.execute("""
            SELECT drive_letter, 
                   COUNT(*) as files,
                   ROUND(SUM(size_bytes) / 1073741824.0, 2) as gb,
                   COUNT(CASE WHEN is_evidence THEN 1 END) as evidence_files,
                   COUNT(CASE WHEN is_bloat THEN 1 END) as bloat_files
            FROM inv GROUP BY drive_letter ORDER BY files DESC
        """).fetchall()
        analytics["drive_summary"] = drive_summary
        
        # Extension summary (top 50)
        ext_summary = con.execute("""
            SELECT extension,
                   COUNT(*) as files,
                   ROUND(SUM(size_bytes) / 1073741824.0, 2) as gb
            FROM inv WHERE extension != '' 
            GROUP BY extension ORDER BY gb DESC LIMIT 50
        """).fetchall()
        analytics["ext_summary"] = ext_summary
        
        # Bloat analysis
        bloat = con.execute("""
            SELECT extension,
                   COUNT(*) as files,
                   ROUND(SUM(size_bytes) / 1073741824.0, 2) as gb,
                   drive_letter
            FROM inv WHERE is_bloat = true
            GROUP BY extension, drive_letter ORDER BY gb DESC LIMIT 30
        """).fetchall()
        analytics["bloat"] = bloat
        
        # Evidence hotspots (directories with most evidence files)
        # Extract parent directory (2 levels up from file)
        evidence_dirs = con.execute("""
            WITH dirs AS (
                SELECT 
                    regexp_replace(file_path, '[^\\\\]+$', '') as dir_path,
                    drive_letter,
                    extension,
                    size_bytes
                FROM inv WHERE is_evidence = true
            )
            SELECT dir_path, 
                   COUNT(*) as evidence_files,
                   ROUND(SUM(size_bytes) / 1048576.0, 1) as mb
            FROM dirs
            GROUP BY dir_path
            HAVING evidence_files >= 10
            ORDER BY evidence_files DESC LIMIT 50
        """).fetchall()
        analytics["evidence_dirs"] = evidence_dirs
        
        # Find .mbox files
        mbox = con.execute("""
            SELECT file_path, file_name, 
                   ROUND(size_bytes / 1048576.0, 1) as mb
            FROM inv WHERE extension = '.mbox'
        """).fetchall()
        analytics["mbox_files"] = mbox
        
        # Find .zip files
        zips = con.execute("""
            SELECT drive_letter,
                   COUNT(*) as zip_count,
                   ROUND(SUM(size_bytes) / 1073741824.0, 2) as gb
            FROM inv WHERE extension IN ('.zip', '.rar', '.7z', '.tar', '.gz')
            GROUP BY drive_letter ORDER BY gb DESC
        """).fetchall()
        analytics["zip_summary"] = zips
        
        # Find large files (>100MB)
        large = con.execute("""
            SELECT file_path, file_name, extension,
                   ROUND(size_bytes / 1073741824.0, 2) as gb
            FROM inv WHERE size_bytes > 104857600
            ORDER BY size_bytes DESC LIMIT 50
        """).fetchall()
        analytics["large_files"] = large
        
        # Duplicate name+size candidates (fast heuristic)
        dup_candidates = con.execute("""
            SELECT file_name, size_bytes, COUNT(*) as copies,
                   ARRAY_AGG(drive_letter) as drives
            FROM inv
            WHERE size_bytes > 1024
            GROUP BY file_name, size_bytes
            HAVING copies > 1
            ORDER BY size_bytes * copies DESC LIMIT 50
        """).fetchall()
        analytics["dup_candidates"] = dup_candidates
        
        # J:\ LitigationOS variants
        j_variants = con.execute("""
            SELECT regexp_extract(file_path, 'J:\\\\([^\\\\]+)', 1) as root_dir,
                   COUNT(*) as files,
                   ROUND(SUM(size_bytes) / 1073741824.0, 2) as gb
            FROM inv WHERE drive_letter = 'J'
            GROUP BY root_dir ORDER BY gb DESC LIMIT 30
        """).fetchall()
        analytics["j_variants"] = j_variants
        
        elapsed = time.time() - t0
        print(f"[ANALYTICS] Complete in {elapsed:.1f}s")
        con.close()
        
    else:
        # Pure Python fallback
        print(f"\n[ANALYTICS] Processing {len(all_rows):,} rows (pure Python)...")
        drive_counts = defaultdict(lambda: {"files": 0, "bytes": 0, "evidence": 0, "bloat": 0})
        for r in all_rows:
            d = drive_counts[r["drive_letter"]]
            d["files"] += 1
            d["bytes"] += r["size_bytes"]
            if r["is_evidence"]: d["evidence"] += 1
            if r["is_bloat"]: d["bloat"] += 1
        analytics["drive_summary"] = [
            (k, v["files"], round(v["bytes"]/1073741824, 2), v["evidence"], v["bloat"])
            for k, v in sorted(drive_counts.items(), key=lambda x: -x[1]["files"])
        ]
    
    return analytics


def generate_report(analytics: dict, total_files: int, total_time: float) -> str:
    """Generate markdown report."""
    sep_days = (datetime.now() - datetime(2025, 7, 29)).days
    lines = [
        f"# DISK AWARENESS REPORT",
        f"> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"> Total files scanned: {total_files:,}",
        f"> Scan time: {total_time:.1f}s",
        f"> Separation days: {sep_days}",
        f"",
        f"## Drive Summary",
        f"| Drive | Files | GB | Evidence | Bloat |",
        f"|-------|-------|----|----------|-------|",
    ]
    
    total_gb = 0
    total_evidence = 0
    total_bloat = 0
    for row in analytics.get("drive_summary", []):
        drive, files, gb, evidence, bloat = row
        lines.append(f"| {drive}:\\ | {files:,} | {gb} | {evidence:,} | {bloat:,} |")
        total_gb += gb
        total_evidence += evidence
        total_bloat += bloat
    lines.append(f"| **TOTAL** | **{total_files:,}** | **{total_gb:.1f}** | **{total_evidence:,}** | **{total_bloat:,}** |")
    
    # Extension breakdown
    lines.extend(["", "## Top Extensions by Size", "| Extension | Files | GB |", "|-----------|-------|----|"])
    for ext, files, gb in analytics.get("ext_summary", [])[:30]:
        lines.append(f"| {ext or '(none)'} | {files:,} | {gb} |")
    
    # Bloat
    lines.extend(["", "## Bloat Analysis", "| Extension | Drive | Files | GB |", "|-----------|-------|-------|----|"])
    for ext, files, gb, drive in analytics.get("bloat", []):
        lines.append(f"| {ext} | {drive}:\\ | {files:,} | {gb} |")
    
    # MBOX discovery
    mbox = analytics.get("mbox_files", [])
    if mbox:
        lines.extend(["", "## 📧 EMAIL ARCHIVES FOUND"])
        for path, name, mb in mbox:
            lines.append(f"- **{name}** ({mb} MB): `{path}`")
    else:
        lines.extend(["", "## 📧 EMAIL ARCHIVES", "- None found across all drives"])
    
    # Zip summary
    lines.extend(["", "## 📦 Archive Files (Zip/RAR/7z)", "| Drive | Count | GB |", "|-------|-------|----|"])
    for drive, count, gb in analytics.get("zip_summary", []):
        lines.append(f"| {drive}:\\ | {count:,} | {gb} |")
    
    # Large files
    lines.extend(["", "## 🐘 Largest Files (>100 MB)", "| File | Extension | GB | Path |", "|------|-----------|----|----|"])
    for path, name, ext, gb in analytics.get("large_files", [])[:20]:
        lines.append(f"| {name[:40]} | {ext} | {gb} | `{path[:60]}...` |")
    
    # J:\ variants
    if analytics.get("j_variants"):
        lines.extend(["", "## J:\\ Directory Breakdown", "| Directory | Files | GB |", "|-----------|-------|----|"])
        for root, files, gb in analytics["j_variants"]:
            lines.append(f"| {root or '(root files)'} | {files:,} | {gb} |")
    
    # Duplicate candidates
    if analytics.get("dup_candidates"):
        lines.extend(["", "## 🔄 Potential Duplicates (same name + size)", "| File Name | Size | Copies | Drives |", "|-----------|------|--------|--------|"])
        for name, size, copies, drives in analytics["dup_candidates"][:20]:
            size_str = f"{size/1048576:.1f} MB" if size > 1048576 else f"{size/1024:.0f} KB"
            lines.append(f"| {name[:50]} | {size_str} | {copies} | {drives} |")
    
    # Evidence hotspots
    if analytics.get("evidence_dirs"):
        lines.extend(["", "## 🎯 Evidence Hotspot Directories", "| Directory | Evidence Files | MB |", "|-----------|---------------|-----|"])
        for path, files, mb in analytics["evidence_dirs"][:20]:
            lines.append(f"| `{path[:70]}` | {files:,} | {mb} |")
    
    # Recommendations
    lines.extend([
        "",
        "## 🎯 RECOMMENDED ACTIONS",
        "",
        "### Immediate (Phase 1 — Bloat Reduction)",
        f"- Clear __pycache__ across all drives ({total_bloat:,} bloat files found)",
        "- Review .chk files for evidence value, then archive",
        "- Catalog node_modules sizes",
        "",
        "### Short-term (Phase 2 — Zip Unpacking)",
        "- Unpack all archives to J:\\LitigationOS_CENTRAL\\UNPACKED\\",
        "- Prioritize evidence-likely zips (case files, court docs)",
        "- Flatten deep nesting to max 3 levels",
        "",
        "### Medium-term (Phase 3 — Organization)",
        "- Build canonical evidence mirror on J:\\",
        "- MEEK lane classification on all evidence files",
        "- Content-based dedup using existing omega_dedup infrastructure",
        "",
        "### LitigationOS Internal",
        "- Audit 20+ root-level .py scripts → archive unused",
        "- Clean repo __pycache__",
        "- Consolidate stale analysis files",
    ])
    
    return "\n".join(lines)


def main():
    print("=" * 70)
    print("  PHASE 0: FULL FILE TREE INVENTORY")
    print(f"  Drives: {', '.join(DRIVES_TO_SCAN)}")
    print(f"  Output: {PARQUET_PATH}")
    print("=" * 70)
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    all_rows = []
    t_start = time.time()
    
    for drive in DRIVES_TO_SCAN:
        if not os.path.exists(drive):
            print(f"[SKIP] {drive} not accessible")
            continue
        rows = scan_drive(drive, callback=progress_callback)
        all_rows.extend(rows)
    
    total_time = time.time() - t_start
    print(f"\n[TOTAL] {len(all_rows):,} files scanned in {total_time:.1f}s")
    
    # Build analytics
    analytics = build_analytics(all_rows)
    
    # Generate report
    report = generate_report(analytics, len(all_rows), total_time)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"\n[REPORT] Written to {REPORT_PATH}")
    
    # Also save to LitigationOS analysis directory
    analysis_copy = Path("C:\\Users\\andre\\LitigationOS\\04_ANALYSIS\\DISK_AWARENESS_REPORT.md")
    analysis_copy.write_text(report, encoding="utf-8")
    print(f"[REPORT] Copy at {analysis_copy}")
    
    # Print key findings
    print("\n" + "=" * 70)
    print("  KEY FINDINGS")
    print("=" * 70)
    
    for row in analytics.get("drive_summary", []):
        drive, files, gb, evidence, bloat = row
        print(f"  {drive}:\\ — {files:,} files ({gb} GB), {evidence:,} evidence, {bloat:,} bloat")
    
    mbox = analytics.get("mbox_files", [])
    if mbox:
        print(f"\n  📧 MBOX FOUND: {mbox[0][0]}")
    
    zips = analytics.get("zip_summary", [])
    total_zips = sum(z[1] for z in zips)
    total_zip_gb = sum(z[2] for z in zips)
    print(f"\n  📦 Archives: {total_zips:,} files ({total_zip_gb:.1f} GB) — ready for unpacking")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
