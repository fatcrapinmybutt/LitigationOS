#!/usr/bin/env python3
"""
Iterative Distillation Engine
Processes omega_zip_clusters one at a time: extract → deduplicate → merge → quarantine.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import argparse
import hashlib
import os
import shutil
import sqlite3
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
DB_PATH        = r"C:\Users\andre\LitigationOS\litigation_context.db"
STAGING_ROOT   = Path(r"F:\DISTILL_STAGING")
QUARANTINE_ROOT= Path(r"I:\DISTILLED_ORIGINALS")
MASTER_ROOT    = Path(r"C:\Users\andre\LitigationOS\DISTILLED")

FAT32_MAX_FILE = 4 * 1024 * 1024 * 1024 - 1  # 4 GB minus 1 byte
MIN_FREE_BYTES = 2 * 1024 * 1024 * 1024       # 2 GB preflight threshold


# ── Helpers ────────────────────────────────────────────────────────────────────

def get_free_bytes(path) -> int:
    """Return free bytes on the drive containing *path*."""
    try:
        path = Path(path)
        usage = shutil.disk_usage(path.anchor or path)
        return usage.free
    except OSError:
        return 0


def sha256_file(filepath: Path, buf_size: int = 1 << 16) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(buf_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def safe_relpath(member_name: str) -> str | None:
    """Reject path-traversal entries (e.g. ../../etc/passwd)."""
    cleaned = os.path.normpath(member_name)
    if cleaned.startswith("..") or os.path.isabs(cleaned):
        return None
    return cleaned


def find_zips_in(path: str) -> list[Path]:
    """If *path* is a zip, return it; if a directory, find zips inside it."""
    p = Path(path)
    if not p.exists():
        return []
    if p.is_file() and p.suffix.lower() == ".zip":
        return [p]
    if p.is_dir():
        return sorted(p.rglob("*.zip"))
    return []


# ── Database ───────────────────────────────────────────────────────────────────

def open_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def ensure_log_table(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS omega_distill_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            cluster_id      INTEGER NOT NULL,
            started_at      TEXT,
            finished_at     TEXT,
            zips_found      INTEGER DEFAULT 0,
            zips_extracted  INTEGER DEFAULT 0,
            zips_skipped    INTEGER DEFAULT 0,
            files_in        INTEGER DEFAULT 0,
            files_out       INTEGER DEFAULT 0,
            dupes_found     INTEGER DEFAULT 0,
            bytes_in        INTEGER DEFAULT 0,
            bytes_out       INTEGER DEFAULT 0,
            bytes_saved     INTEGER DEFAULT 0,
            errors          TEXT,
            dry_run         INTEGER DEFAULT 0
        )
    """)
    conn.commit()


def get_pending_clusters(conn: sqlite3.Connection, limit: int) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM omega_zip_clusters WHERE status = 'pending' "
        "ORDER BY priority DESC, total_size_mb ASC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_cluster_members(conn: sqlite3.Connection, cluster_id: int) -> list[str]:
    rows = conn.execute(
        "SELECT zip_path FROM omega_zip_cluster_members WHERE cluster_id = ?",
        (cluster_id,),
    ).fetchall()
    return [r["zip_path"] for r in rows]


def update_cluster_status(conn: sqlite3.Connection, cluster_id: int, status: str):
    conn.execute(
        "UPDATE omega_zip_clusters SET status = ?, processed_at = ? WHERE cluster_id = ?",
        (status, datetime.now(timezone.utc).isoformat(), cluster_id),
    )
    conn.commit()


def insert_distill_log(conn: sqlite3.Connection, metrics: dict):
    conn.execute(
        """INSERT INTO omega_distill_log
           (cluster_id, started_at, finished_at, zips_found, zips_extracted,
            zips_skipped, files_in, files_out, dupes_found, bytes_in, bytes_out,
            bytes_saved, errors, dry_run)
           VALUES (:cluster_id, :started_at, :finished_at, :zips_found,
                   :zips_extracted, :zips_skipped, :files_in, :files_out,
                   :dupes_found, :bytes_in, :bytes_out, :bytes_saved,
                   :errors, :dry_run)""",
        metrics,
    )
    conn.commit()


# ── Extraction ─────────────────────────────────────────────────────────────────

def extract_zip_safe(zip_path: Path, dest: Path, errors: list) -> tuple[int, int]:
    """Extract *zip_path* into *dest*. Returns (files_extracted, bytes_extracted)."""
    files_out = 0
    bytes_out = 0
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                rel = safe_relpath(info.filename)
                if rel is None:
                    errors.append(f"SKIP path-traversal: {info.filename} in {zip_path}")
                    continue
                # FAT32 4 GB limit
                if info.file_size >= FAT32_MAX_FILE:
                    errors.append(
                        f"SKIP >4GB file: {info.filename} "
                        f"({info.file_size / 1e9:.2f} GB) in {zip_path}"
                    )
                    continue
                # Check staging disk space before each file
                if get_free_bytes(STAGING_ROOT) < max(info.file_size * 2, MIN_FREE_BYTES // 4):
                    errors.append(f"ABORT low disk during extraction of {zip_path}")
                    break
                target = dest / rel
                ensure_dir(target.parent)
                try:
                    with zf.open(info) as src, open(target, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    files_out += 1
                    bytes_out += target.stat().st_size
                except Exception as e:
                    errors.append(f"ERR extracting {info.filename} from {zip_path}: {e}")
    except zipfile.BadZipFile:
        errors.append(f"CORRUPTED zip: {zip_path}")
    except RuntimeError as e:
        if "password" in str(e).lower() or "encrypted" in str(e).lower():
            errors.append(f"PASSWORD-PROTECTED zip: {zip_path}")
        else:
            errors.append(f"RUNTIME ERROR on {zip_path}: {e}")
    except Exception as e:
        errors.append(f"UNEXPECTED ERROR on {zip_path}: {e}")
    return files_out, bytes_out


# ── Deduplication ──────────────────────────────────────────────────────────────

def build_hash_index(staging_dir: Path) -> dict[str, list[Path]]:
    """Walk staging_dir, SHA-256 every file, return {hash: [paths]}."""
    index: dict[str, list[Path]] = {}
    for root, _dirs, files in os.walk(staging_dir):
        for fname in files:
            fpath = Path(root) / fname
            try:
                h = sha256_file(fpath)
                index.setdefault(h, []).append(fpath)
            except OSError as e:
                print(f"  ⚠ hash failed: {fpath}: {e}")
    return index


def pick_best(paths: list[Path]) -> Path:
    """From a list of duplicate files, keep the newest; break ties by largest."""
    return max(paths, key=lambda p: (p.stat().st_mtime, p.stat().st_size))


def deduplicate_and_merge(staging_dir: Path, master_dir: Path) -> tuple[int, int, int, int, int]:
    """Deduplicate staging_dir → master_dir.
    Returns (files_in, files_out, dupes_found, bytes_in, bytes_out).
    """
    index = build_hash_index(staging_dir)
    files_in = sum(len(v) for v in index.values())
    bytes_in = 0
    bytes_out = 0
    dupes_found = 0
    files_out = 0

    ensure_dir(master_dir)
    seen_names: dict[str, int] = {}  # handle name collisions in flat output

    for _hash, paths in index.items():
        best = pick_best(paths)
        dupes_found += len(paths) - 1
        for p in paths:
            try:
                bytes_in += p.stat().st_size
            except OSError:
                pass

        # Preserve relative path from staging dir for the best copy
        try:
            rel = best.relative_to(staging_dir)
        except ValueError:
            rel = Path(best.name)

        target = master_dir / rel
        ensure_dir(target.parent)

        # Handle name collisions
        if target.exists():
            stem = target.stem
            suffix = target.suffix
            count = seen_names.get(str(target), 0) + 1
            seen_names[str(target)] = count
            target = target.parent / f"{stem}_dup{count}{suffix}"

        try:
            shutil.copy2(best, target)
            bytes_out += target.stat().st_size
            files_out += 1
        except OSError as e:
            print(f"  ⚠ copy failed: {best} → {target}: {e}")

    return files_in, files_out, dupes_found, bytes_in, bytes_out


# ── Quarantine ─────────────────────────────────────────────────────────────────

def quarantine_zips(zip_paths: list[Path], cluster_id: int, errors: list):
    """Move original zips to quarantine folder."""
    qdir = QUARANTINE_ROOT / f"cluster_{cluster_id}"
    ensure_dir(qdir)
    for zp in zip_paths:
        if not zp.exists():
            continue
        dest = qdir / zp.name
        if dest.exists():
            dest = qdir / f"{zp.stem}_{int(time.time())}{zp.suffix}"
        try:
            shutil.move(str(zp), str(dest))
        except Exception as e:
            errors.append(f"QUARANTINE FAILED {zp}: {e}")


# ── Dashboard ──────────────────────────────────────────────────────────────────

def print_dashboard(idx: int, total: int, cid: int, metrics: dict):
    bar_len = 30
    pct = (idx + 1) / total if total else 0
    filled = int(bar_len * pct)
    bar = "█" * filled + "░" * (bar_len - filled)

    saved_mb = metrics["bytes_saved"] / (1024 * 1024)
    in_mb = metrics["bytes_in"] / (1024 * 1024)
    out_mb = metrics["bytes_out"] / (1024 * 1024)
    dedup_pct = (
        (metrics["dupes_found"] / metrics["files_in"] * 100)
        if metrics["files_in"] > 0 else 0
    )
    elapsed = metrics.get("elapsed_sec", 0)

    print()
    print("=" * 70)
    print(f"  DISTILLATION PROGRESS  [{bar}] {pct:.0%}  ({idx+1}/{total})")
    print(f"  Cluster {cid}")
    print(f"  {'─' * 62}")
    print(f"  Zips found       : {metrics['zips_found']:>6}")
    print(f"  Zips extracted   : {metrics['zips_extracted']:>6}  "
          f"(skipped: {metrics['zips_skipped']})")
    print(f"  Files in         : {metrics['files_in']:>6}  →  "
          f"Files out: {metrics['files_out']}")
    print(f"  Dupes found      : {metrics['dupes_found']:>6}  ({dedup_pct:.1f}%)")
    print(f"  Size in          : {in_mb:>9.2f} MB  →  Size out: {out_mb:.2f} MB")
    print(f"  Space saved      : {saved_mb:>9.2f} MB")
    print(f"  Elapsed          : {elapsed:>9.1f} sec")
    if metrics.get("errors"):
        err_lines = metrics["errors"].split("\n")
        print(f"  Errors           : {len(err_lines)}")
        for e in err_lines[:5]:
            print(f"    ! {e}")
        if len(err_lines) > 5:
            print(f"    ... and {len(err_lines) - 5} more")
    print("=" * 70)


# ── Main Pipeline ──────────────────────────────────────────────────────────────

def process_cluster(conn: sqlite3.Connection, cluster: dict,
                    idx: int, total: int, dry_run: bool) -> dict:
    cid = cluster["cluster_id"]
    started = datetime.now(timezone.utc).isoformat()
    errors_list: list[str] = []
    staging_dir = STAGING_ROOT / f"cluster_{cid}"
    master_dir = MASTER_ROOT / f"cluster_{cid}"

    print(f"\n{'━' * 70}")
    print(f"  ▶ Cluster {cid}  |  members: {cluster['member_count']}  |  "
          f"~{cluster['total_size_mb']:.1f} MB  |  priority: {cluster['priority']}")
    print(f"{'━' * 70}")

    # Gather all zip files from member paths
    member_paths = get_cluster_members(conn, cid)
    all_zips: list[Path] = []
    for mp in member_paths:
        found = find_zips_in(mp)
        all_zips.extend(found)
    all_zips = list(dict.fromkeys(all_zips))  # dedupe preserving order

    print(f"  Member paths: {len(member_paths)}  →  Zip files found: {len(all_zips)}")
    for z in all_zips[:8]:
        print(f"    {z}")
    if len(all_zips) > 8:
        print(f"    ... and {len(all_zips) - 8} more")

    metrics = dict(
        cluster_id=cid, started_at=started, finished_at=None,
        zips_found=len(all_zips), zips_extracted=0, zips_skipped=0,
        files_in=0, files_out=0, dupes_found=0,
        bytes_in=0, bytes_out=0, bytes_saved=0,
        errors="", dry_run=1 if dry_run else 0, elapsed_sec=0,
    )

    if dry_run:
        total_zip_size = sum(
            z.stat().st_size for z in all_zips if z.exists()
        )
        print(f"  [DRY RUN] Would extract {len(all_zips)} zips "
              f"(~{total_zip_size / 1e6:.1f} MB) → staging → deduplicate → master")
        metrics["finished_at"] = datetime.now(timezone.utc).isoformat()
        print_dashboard(idx, total, cid, metrics)
        insert_distill_log(conn, metrics)
        return metrics

    if len(all_zips) == 0:
        print("  ⓘ  No zip files found in member paths. Marking done.")
        update_cluster_status(conn, cid, "done")
        metrics["finished_at"] = datetime.now(timezone.utc).isoformat()
        print_dashboard(idx, total, cid, metrics)
        insert_distill_log(conn, metrics)
        return metrics

    # ── Preflight: disk space ──────────────────────────────────────────────
    free = get_free_bytes(STAGING_ROOT.anchor if STAGING_ROOT.anchor else STAGING_ROOT)
    if free < MIN_FREE_BYTES:
        msg = (f"ABORT: F: only {free / 1e9:.2f} GB free "
               f"(need {MIN_FREE_BYTES / 1e9:.0f} GB)")
        print(f"  ✖ {msg}")
        errors_list.append(msg)
        update_cluster_status(conn, cid, "error")
        metrics["errors"] = "\n".join(errors_list)
        metrics["finished_at"] = datetime.now(timezone.utc).isoformat()
        insert_distill_log(conn, metrics)
        return metrics

    # ── Mark processing ────────────────────────────────────────────────────
    update_cluster_status(conn, cid, "processing")
    t0 = time.time()

    # ── Extract ────────────────────────────────────────────────────────────
    ensure_dir(staging_dir)
    for zp in all_zips:
        print(f"  📦 Extracting: {zp.name} ...", end=" ", flush=True)
        f_out, b_out = extract_zip_safe(zp, staging_dir / zp.stem, errors_list)
        if f_out > 0:
            metrics["zips_extracted"] += 1
            print(f"{f_out} files, {b_out / 1e6:.1f} MB")
        else:
            metrics["zips_skipped"] += 1
            print("(skipped)")

    # ── Deduplicate & merge ────────────────────────────────────────────────
    print("  🔍 Building SHA-256 index & deduplicating ...")
    fi, fo, dupes, bi, bo = deduplicate_and_merge(staging_dir, master_dir)
    metrics.update(
        files_in=fi, files_out=fo, dupes_found=dupes,
        bytes_in=bi, bytes_out=bo, bytes_saved=bi - bo,
    )

    # ── Quarantine originals ───────────────────────────────────────────────
    print("  📁 Quarantining original zips ...")
    quarantine_zips(all_zips, cid, errors_list)

    # ── Cleanup staging ────────────────────────────────────────────────────
    try:
        shutil.rmtree(staging_dir)
    except Exception as e:
        errors_list.append(f"CLEANUP STAGING FAILED: {e}")

    # ── Finalise ───────────────────────────────────────────────────────────
    elapsed = time.time() - t0
    metrics["elapsed_sec"] = elapsed
    metrics["errors"] = "\n".join(errors_list) if errors_list else ""
    metrics["finished_at"] = datetime.now(timezone.utc).isoformat()

    status = "done" if not errors_list else "done"
    update_cluster_status(conn, cid, status)
    insert_distill_log(conn, metrics)
    print_dashboard(idx, total, cid, metrics)
    return metrics


def main():
    parser = argparse.ArgumentParser(description="Iterative Distillation Engine")
    parser.add_argument("--limit", type=int, default=5,
                        help="Max clusters to process (default: 5)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show plan without extracting/moving files")
    args = parser.parse_args()

    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║           ITERATIVE  DISTILLATION  ENGINE  v1.0                     ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print(f"  Database : {DB_PATH}")
    print(f"  Staging  : {STAGING_ROOT}")
    print(f"  Master   : {MASTER_ROOT}")
    print(f"  Quarantine: {QUARANTINE_ROOT}")
    print(f"  Mode     : {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"  Limit    : {args.limit} clusters")

    # Ensure output directories exist (create only on live runs)
    for d in [MASTER_ROOT]:
        ensure_dir(d)
    if not args.dry_run:
        for d in [STAGING_ROOT, QUARANTINE_ROOT]:
            try:
                ensure_dir(d)
            except OSError as e:
                print(f"  ⚠ Cannot create {d}: {e}")

    conn = open_db()
    ensure_log_table(conn)

    clusters = get_pending_clusters(conn, args.limit)
    print(f"\n  Pending clusters found: {len(clusters)}")
    if not clusters:
        print("  Nothing to process. Exiting.")
        conn.close()
        return

    grand = dict(zips_found=0, zips_extracted=0, zips_skipped=0,
                 files_in=0, files_out=0, dupes_found=0,
                 bytes_in=0, bytes_out=0, bytes_saved=0, errors=0)

    for i, cl in enumerate(clusters):
        m = process_cluster(conn, cl, i, len(clusters), args.dry_run)
        for k in ["zips_found", "zips_extracted", "zips_skipped",
                   "files_in", "files_out", "dupes_found",
                   "bytes_in", "bytes_out", "bytes_saved"]:
            grand[k] += m.get(k, 0)
        if m.get("errors"):
            grand["errors"] += len(m["errors"].split("\n"))

    # ── Grand Summary ──────────────────────────────────────────────────────
    print("\n")
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                    DISTILLATION  COMPLETE                           ║")
    print("╠══════════════════════════════════════════════════════════════════════╣")
    print(f"║  Clusters processed : {len(clusters):>6}                                      ║")
    print(f"║  Zips found/extracted: {grand['zips_found']:>5} / {grand['zips_extracted']:<5}                              ║")
    print(f"║  Files in → out     : {grand['files_in']:>6} → {grand['files_out']:<6}                            ║")
    print(f"║  Duplicates removed : {grand['dupes_found']:>6}                                      ║")
    print(f"║  Space saved        : {grand['bytes_saved'] / 1e6:>9.2f} MB                              ║")
    print(f"║  Errors             : {grand['errors']:>6}                                      ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")

    conn.close()


if __name__ == "__main__":
    main()
