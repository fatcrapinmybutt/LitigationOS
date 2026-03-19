"""
OMEGA Phase 4E: Archive Deep Extraction
Enumerate and extract legal documents from ZIP/RAR archives.
"""
import json
import os
import sqlite3
import sys
import time
import zipfile
from pathlib import Path

from config import get_cyclepack_dir, long_path, sha256_file, report_progress, LEGAL_EXTENSIONS
from safety import write_phase_checkpoint, is_phase_done

# Extensions safe to extract from archives
SAFE_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md", ".json", ".csv", ".jsonl",
                   ".rtf", ".odt", ".html", ".htm", ".xml"}

# Extensions / paths to never extract
BLOCKED_PATTERNS = {
    "node_modules", "__pycache__", ".git", ".venv", "venv",
    ".class", ".exe", ".dll", ".so", ".o", ".obj", ".pyc", ".pyo",
    ".jar", ".war", ".ear", ".whl", ".egg-info",
}


def _is_safe_entry(name: str) -> bool:
    """Check if archive entry is safe to extract."""
    name_lower = name.lower().replace("\\", "/")
    # Block dangerous paths
    for blocked in BLOCKED_PATTERNS:
        if blocked in name_lower:
            return False
    # Only allow known safe extensions
    ext = os.path.splitext(name_lower)[1]
    return ext in SAFE_EXTENSIONS


def extract_zip(zip_path: str, staging_dir: Path) -> list[dict]:
    """Extract legal documents from a ZIP file. Returns list of extracted file info."""
    entries: list[dict] = []
    try:
        with zipfile.ZipFile(long_path(zip_path), "r") as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                entry = {
                    "archive_path": zip_path,
                    "inner_path": info.filename,
                    "size": info.file_size,
                    "compressed_size": info.compress_size,
                    "extracted": False,
                }

                if not _is_safe_entry(info.filename):
                    entry["skip_reason"] = "blocked_pattern_or_extension"
                    entries.append(entry)
                    continue

                # Extract to staging directory
                safe_name = info.filename.replace("/", "_").replace("\\", "_")
                out_path = staging_dir / safe_name
                try:
                    data = zf.read(info.filename)
                    out_path.write_bytes(data)
                    entry["extracted"] = True
                    entry["extracted_path"] = str(out_path)
                    entry["sha256"] = sha256_file(out_path)
                    entry["extension"] = os.path.splitext(info.filename)[1].lower()
                except Exception as e:
                    entry["error"] = str(e)[:200]

                entries.append(entry)
    except (zipfile.BadZipFile, OSError) as e:
        entries.append({"archive_path": zip_path, "error": str(e)[:200]})
    return entries


def extract_rar(rar_path: str, staging_dir: Path) -> list[dict]:
    """Extract legal documents from a RAR file using rarfile."""
    entries: list[dict] = []
    try:
        import rarfile
    except ImportError:
        return [{"archive_path": rar_path, "error": "rarfile not installed"}]

    try:
        with rarfile.RarFile(long_path(rar_path), "r") as rf:
            for info in rf.infolist():
                if info.is_dir():
                    continue
                entry = {
                    "archive_path": rar_path,
                    "inner_path": info.filename,
                    "size": info.file_size,
                    "compressed_size": info.compress_size,
                    "extracted": False,
                }

                if not _is_safe_entry(info.filename):
                    entry["skip_reason"] = "blocked_pattern_or_extension"
                    entries.append(entry)
                    continue

                safe_name = info.filename.replace("/", "_").replace("\\", "_")
                out_path = staging_dir / safe_name
                try:
                    data = rf.read(info.filename)
                    out_path.write_bytes(data)
                    entry["extracted"] = True
                    entry["extracted_path"] = str(out_path)
                    entry["sha256"] = sha256_file(out_path)
                    entry["extension"] = os.path.splitext(info.filename)[1].lower()
                except Exception as e:
                    entry["error"] = str(e)[:200]

                entries.append(entry)
    except Exception as e:
        entries.append({"archive_path": rar_path, "error": str(e)[:200]})
    return entries


def _insert_extracted_files(conn: sqlite3.Connection, entries: list[dict]):
    """Insert extracted archive contents into inventory.db files table."""
    for entry in entries:
        if not entry.get("extracted"):
            continue
        try:
            conn.execute("""
                INSERT OR IGNORE INTO files
                    (file_path, sha256, size_bytes, extension, top_bucket, is_canonical, priority)
                VALUES (?, ?, ?, ?, 'archive_extracted', 0, 'MEDIUM')
            """, (
                entry["extracted_path"],
                entry.get("sha256", ""),
                entry.get("size", 0),
                entry.get("extension", ""),
            ))
        except sqlite3.Error:
            continue
    conn.commit()


def run_archive_extract(cycle_dir: Path, dry_run: bool = False):
    db_path = cycle_dir / "inventory.db"
    if not db_path.exists():
        print("[PHASE4E] inventory.db not found", file=sys.stderr)
        sys.exit(1)

    if is_phase_done(cycle_dir, "phase4e"):
        print("[PHASE4E] Already complete, skipping", file=sys.stderr)
        return

    staging_dir = cycle_dir / "extracts" / "archive_staging"
    staging_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    rows = conn.execute("""
        SELECT id, file_path, sha256, size_bytes, extension FROM files
        WHERE is_canonical = 1 AND extension IN ('.zip', '.rar')
        ORDER BY size_bytes ASC
    """).fetchall()

    start = time.time()
    archives_processed = 0
    files_extracted = 0
    files_skipped = 0
    errors = 0
    all_entries: list[dict] = []
    inventory_path = cycle_dir / "archive_inventory.jsonl"

    print(f"[PHASE4E] Processing {len(rows):,} archives...", file=sys.stderr)

    with open(inventory_path, "a", encoding="utf-8") as inv_log:
        for i, (fid, fpath, sha, size, ext) in enumerate(rows):
            if dry_run:
                archives_processed += 1
                continue

            if ext == ".zip":
                entries = extract_zip(fpath, staging_dir)
            elif ext == ".rar":
                entries = extract_rar(fpath, staging_dir)
            else:
                continue

            archives_processed += 1
            archive_record = {
                "archive_path": fpath,
                "archive_sha256": sha,
                "archive_size": size,
                "contents": entries,
                "extraction_ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
            inv_log.write(json.dumps(archive_record) + "\n")

            for entry in entries:
                if entry.get("extracted"):
                    files_extracted += 1
                elif entry.get("skip_reason"):
                    files_skipped += 1
                elif entry.get("error"):
                    errors += 1

            all_entries.extend(entries)

            # Insert extracted files into inventory
            _insert_extracted_files(conn, entries)

            if (i + 1) % 100 == 0:
                report_progress("phase4e", i + 1, len(rows))

    elapsed = time.time() - start
    print(
        f"[PHASE4E] Done: {archives_processed:,} archives, {files_extracted:,} extracted, "
        f"{files_skipped:,} skipped, {errors} errors in {elapsed:.0f}s",
        file=sys.stderr,
    )

    if not dry_run:
        stats = {
            "archives_processed": archives_processed,
            "files_extracted": files_extracted,
            "files_skipped": files_skipped,
            "errors": errors,
            "elapsed": round(elapsed, 1),
        }
        (cycle_dir / "archive_extract_stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
        write_phase_checkpoint(cycle_dir, "phase4e", {"status": "done", **stats})

    conn.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Phase 4E: Archive Deep Extraction")
    parser.add_argument("--cycle-ts", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    from config import CYCLE_TS
    run_archive_extract(get_cyclepack_dir(args.cycle_ts or CYCLE_TS), args.dry_run)
