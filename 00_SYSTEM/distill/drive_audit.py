#!/usr/bin/env python3
"""Full Drive Audit — Comprehensive per-drive analysis with reclamation opportunities."""
import sys, sqlite3, os
from datetime import datetime, timedelta
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"

def connect():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def top_files(conn, drive, n=20):
    """Top N largest files/directories on a drive."""
    cur = conn.execute(
        "SELECT path, filename, size_bytes, file_type, modified "
        "FROM omega_filesystem_map WHERE drive=? AND size_bytes IS NOT NULL "
        "ORDER BY size_bytes DESC LIMIT ?", (drive, n))
    return cur.fetchall()

def type_distribution(conn, drive):
    """File type distribution by count and total size."""
    cur = conn.execute(
        "SELECT file_type, COUNT(*) as cnt, SUM(size_bytes) as total_bytes "
        "FROM omega_filesystem_map WHERE drive=? AND file_type IS NOT NULL "
        "GROUP BY file_type ORDER BY total_bytes DESC", (drive,))
    return cur.fetchall()

def age_analysis(conn, drive):
    """Analyze file ages: <30d, 30-90d, 90-365d, >1yr."""
    now = datetime.now()
    buckets = {"<30 days": 0, "30-90 days": 0, "90-365 days": 0, ">1 year": 0, "unknown": 0}
    bucket_size = {"<30 days": 0, "30-90 days": 0, "90-365 days": 0, ">1 year": 0, "unknown": 0}
    cur = conn.execute(
        "SELECT modified, size_bytes FROM omega_filesystem_map WHERE drive=?", (drive,))
    for row in cur:
        mod, sz = row["modified"], row["size_bytes"] or 0
        if not mod:
            buckets["unknown"] += 1
            bucket_size["unknown"] += sz
            continue
        try:
            dt = datetime.fromisoformat(mod.replace("Z", "+00:00").split("+")[0])
            delta = (now - dt).days
        except Exception:
            buckets["unknown"] += 1
            bucket_size["unknown"] += sz
            continue
        if delta < 30:
            buckets["<30 days"] += 1; bucket_size["<30 days"] += sz
        elif delta < 90:
            buckets["30-90 days"] += 1; bucket_size["30-90 days"] += sz
        elif delta < 365:
            buckets["90-365 days"] += 1; bucket_size["90-365 days"] += sz
        else:
            buckets[">1 year"] += 1; bucket_size[">1 year"] += sz
    return buckets, bucket_size

def dupe_crossref(conn, drive):
    """Cross-reference with omega_dupe_analysis for this drive."""
    results = {}
    for key_prefix in ['drive_waste_bytes', 'drive_dupe_files', 'drive_total_bytes']:
        cur = conn.execute(
            "SELECT key, value_num FROM omega_dupe_analysis WHERE category=? AND key LIKE ?",
            (key_prefix, f"%{drive}%"))
        row = cur.fetchone()
        if row:
            results[key_prefix] = row["value_num"]
        else:
            # Try exact drive match
            cur2 = conn.execute(
                "SELECT key, value_num FROM omega_dupe_analysis WHERE category=? AND key=?",
                (key_prefix, drive))
            row2 = cur2.fetchone()
            results[key_prefix] = row2["value_num"] if row2 else 0
    # Cross-drive dupes
    cur = conn.execute(
        "SELECT key, value_num FROM omega_dupe_analysis WHERE category='cross_drive_pair' AND key LIKE ?",
        (f"%{drive}%",))
    results["cross_drive_pairs"] = [(r["key"], r["value_num"]) for r in cur.fetchall()]
    return results

def fmt_bytes(b):
    if b is None: return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(b) < 1024: return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"

def reclamation_opportunities(drive):
    """Known reclamation opportunities per drive."""
    ops = {
        "C_LITIGOS": [
            ("Move .ollama to H:", "~8.69 GB", "HIGH",
             "LLM model cache can live on H: drive; symlink back to C:"),
            ("Temp/cache cleanup", "~1-3 GB estimated", "MEDIUM",
             "Clean pip cache, npm cache, __pycache__, .pyc files"),
            ("Duplicate archives", "Variable", "MEDIUM",
             "Multiple .zip files at root level may be redundant"),
        ],
        "I": [
            ("Distilled originals quarantine", "Variable", "MEDIUM",
             "After distillation, originals in I: can be archived or removed"),
            ("Junk quarantine candidates", "Variable", "LOW",
             "Identify low-value files (temp, thumbs.db, .DS_Store equivalents)"),
        ],
        "D": [
            ("Consolidate scattered files", "Variable", "LOW",
             "D: drive may have fragmented project files"),
        ],
    }
    return ops.get(drive, [])

def save_audit(conn, drive, stats):
    """Save audit results to omega_drive_audit table."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS omega_drive_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drive TEXT NOT NULL,
            metric TEXT NOT NULL,
            value_num REAL,
            value_text TEXT,
            ts TEXT DEFAULT (datetime('now'))
        )
    """)
    for metric, val in stats.items():
        if isinstance(val, (int, float)):
            conn.execute("INSERT INTO omega_drive_audit (drive, metric, value_num) VALUES (?,?,?)",
                         (drive, metric, val))
        else:
            conn.execute("INSERT INTO omega_drive_audit (drive, metric, value_text) VALUES (?,?,?)",
                         (drive, metric, str(val)[:500]))
    conn.commit()

def print_dashboard(drive, top, types, age_counts, age_sizes, dupes, reclam):
    """Print per-drive dashboard."""
    w = 80
    print("\n" + "=" * w)
    print(f"  DRIVE AUDIT: {drive}")
    print("=" * w)

    # Top files
    print(f"\n  {'TOP 20 LARGEST FILES':^{w-4}}")
    print("  " + "-" * (w - 4))
    for i, f in enumerate(top, 1):
        name = f["filename"] or "(dir)"
        sz = fmt_bytes(f["size_bytes"])
        ftype = f["file_type"] or "?"
        print(f"  {i:>3}. {sz:>10}  [{ftype:<10}]  {name[:45]}")

    # Type distribution
    print(f"\n  {'TYPE DISTRIBUTION':^{w-4}}")
    print("  " + "-" * (w - 4))
    print(f"  {'Type':<20} {'Count':>10} {'Total Size':>15}")
    for t in types[:15]:
        print(f"  {(t['file_type'] or '?'):<20} {t['cnt']:>10,} {fmt_bytes(t['total_bytes']):>15}")

    # Age analysis
    print(f"\n  {'AGE ANALYSIS':^{w-4}}")
    print("  " + "-" * (w - 4))
    print(f"  {'Age Bucket':<20} {'Files':>10} {'Size':>15}")
    for bucket in ["<30 days", "30-90 days", "90-365 days", ">1 year", "unknown"]:
        print(f"  {bucket:<20} {age_counts.get(bucket,0):>10,} {fmt_bytes(age_sizes.get(bucket,0)):>15}")

    # Dupe cross-reference
    print(f"\n  {'DUPLICATE ANALYSIS':^{w-4}}")
    print("  " + "-" * (w - 4))
    waste = dupes.get("drive_waste_bytes", 0)
    dfiles = dupes.get("drive_dupe_files", 0)
    total = dupes.get("drive_total_bytes", 0)
    print(f"  Total indexed bytes:  {fmt_bytes(total)}")
    print(f"  Duplicate files:      {int(dfiles):,}")
    print(f"  Wasted by dupes:      {fmt_bytes(waste)}")
    if dupes.get("cross_drive_pairs"):
        print(f"  Cross-drive overlaps:")
        for pair, val in dupes["cross_drive_pairs"][:5]:
            print(f"    {pair}: {fmt_bytes(val)}")

    # Reclamation
    if reclam:
        print(f"\n  {'RECLAMATION OPPORTUNITIES':^{w-4}}")
        print("  " + "-" * (w - 4))
        for action, est_size, priority, note in reclam:
            print(f"  [{priority:<6}] {action}")
            print(f"          Est: {est_size}  — {note}")

    print()

def main():
    print("=" * 80)
    print("  OMEGA DRIVE AUDIT — Full Filesystem Analysis")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    conn = connect()

    # Get drives
    cur = conn.execute("SELECT DISTINCT drive FROM omega_filesystem_map ORDER BY drive")
    drives = [r["drive"] for r in cur.fetchall()]
    print(f"\n  Drives found: {', '.join(drives)}")

    # Global stats
    cur = conn.execute("SELECT COUNT(*) as cnt, SUM(size_bytes) as total FROM omega_filesystem_map")
    g = cur.fetchone()
    print(f"  Total files indexed: {g['cnt']:,}")
    print(f"  Total size indexed:  {fmt_bytes(g['total'])}")

    # Clear old audit data
    conn.execute("DROP TABLE IF EXISTS omega_drive_audit")

    for drive in drives:
        top = top_files(conn, drive)
        types = type_distribution(conn, drive)
        age_counts, age_sizes = age_analysis(conn, drive)
        dupes = dupe_crossref(conn, drive)
        reclam = reclamation_opportunities(drive)

        # Collect stats for saving
        cur = conn.execute(
            "SELECT COUNT(*) as cnt, SUM(size_bytes) as total FROM omega_filesystem_map WHERE drive=?",
            (drive,))
        ds = cur.fetchone()
        stats = {
            "total_files": ds["cnt"],
            "total_bytes": ds["total"] or 0,
            "dupe_waste_bytes": dupes.get("drive_waste_bytes", 0),
            "dupe_file_count": dupes.get("drive_dupe_files", 0),
            "type_count": len(types),
            "reclamation_items": len(reclam),
        }
        for bucket, cnt in age_counts.items():
            stats[f"age_{bucket.replace(' ','_').replace('<','lt').replace('>','gt')}_count"] = cnt
            stats[f"age_{bucket.replace(' ','_').replace('<','lt').replace('>','gt')}_bytes"] = age_sizes[bucket]

        save_audit(conn, drive, stats)
        print_dashboard(drive, top, types, age_counts, age_sizes, dupes, reclam)

    # Summary
    print("=" * 80)
    print("  CROSS-DRIVE SUMMARY")
    print("=" * 80)
    cur = conn.execute(
        "SELECT drive, SUM(value_num) FROM omega_drive_audit "
        "WHERE metric='total_bytes' GROUP BY drive ORDER BY SUM(value_num) DESC")
    print(f"\n  {'Drive':<15} {'Total Size':>15}")
    print("  " + "-" * 32)
    for r in cur.fetchall():
        print(f"  {r[0]:<15} {fmt_bytes(r[1]):>15}")

    cur = conn.execute("SELECT SUM(value_num) FROM omega_drive_audit WHERE metric='dupe_waste_bytes'")
    total_waste = cur.fetchone()[0] or 0
    print(f"\n  Total reclamable from dupes: {fmt_bytes(total_waste)}")
    print(f"\n  Audit saved to omega_drive_audit table ({DB})")
    print("=" * 80)

    conn.close()

if __name__ == "__main__":
    main()
