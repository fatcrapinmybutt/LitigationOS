"""
Distillation Dashboard — Phase 2.5
Real-time progress tracking for zip distillation pipeline.
"""
import sqlite3
import sys
import os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"


def print_dashboard():
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    
    # Overall cluster stats
    stats = conn.execute("""
        SELECT status, COUNT(*) as cnt, SUM(total_size_mb) as mb, SUM(total_files) as files
        FROM omega_zip_clusters
        GROUP BY status
    """).fetchall()
    
    total_clusters = sum(r[1] for r in stats)
    total_mb = sum(r[2] or 0 for r in stats)
    
    print("=" * 70)
    print("  DISTILLATION DASHBOARD — LitigationOS")
    print("=" * 70)
    
    print(f"\n  CLUSTER STATUS:")
    for status, cnt, mb, files in stats:
        pct = (cnt / total_clusters * 100) if total_clusters else 0
        print(f"    {status:>12}: {cnt:>4} clusters ({pct:>5.1f}%) | {mb or 0:>8.1f} MB | {files or 0:>6} files")
    
    # Distill log if exists
    try:
        log_stats = conn.execute("""
            SELECT COUNT(*) as processed,
                   SUM(files_extracted) as extracted,
                   SUM(dupes_found) as dupes,
                   SUM(bytes_saved) as saved
            FROM omega_distill_log
        """).fetchone()
        
        if log_stats and log_stats[0]:
            print(f"\n  DISTILLATION METRICS:")
            print(f"    Clusters processed: {log_stats[0]}")
            print(f"    Files extracted:    {log_stats[1] or 0:,}")
            print(f"    Duplicates found:   {log_stats[2] or 0:,}")
            saved_gb = (log_stats[3] or 0) / (1024**3)
            print(f"    Space saved:        {saved_gb:.2f} GB")
    except:
        print(f"\n  DISTILLATION METRICS: Not yet started")
    
    # Dupe analysis summary
    try:
        dupe = conn.execute("""
            SELECT SUM(CASE WHEN category='per_drive' THEN CAST(json_extract(value, '$.waste_gb') AS REAL) END) as total_waste
            FROM omega_dupe_analysis
            WHERE category = 'per_drive'
        """).fetchone()
        if dupe and dupe[0]:
            print(f"\n  DUPLICATION INTEL:")
            print(f"    Total wasted space: {dupe[0]:.1f} GB across all drives")
    except:
        pass
    
    # Top priority pending clusters
    pending = conn.execute("""
        SELECT c.cluster_id, c.member_count, c.total_size_mb, c.avg_relevance, c.priority, c.drives
        FROM omega_zip_clusters c
        WHERE c.status = 'pending'
        ORDER BY c.priority DESC
        LIMIT 10
    """).fetchall()
    
    if pending:
        print(f"\n  NEXT 10 CLUSTERS TO PROCESS:")
        print(f"  {'ID':>5} {'Zips':>5} {'MB':>8} {'Rel':>5} {'Pri':>7} Drives")
        for cid, cnt, mb, rel, pri, drives in pending:
            print(f"  {cid:>5} {cnt:>5} {mb:>8.1f} {rel:>5.1f} {pri:>7.1f} {drives}")
    
    # Drive space check
    print(f"\n  DISK SPACE:")
    for drive_letter in ['C', 'D', 'F', 'G', 'H', 'I']:
        drive_path = f"{drive_letter}:\\"
        try:
            import shutil
            total, used, free = shutil.disk_usage(drive_path)
            print(f"    {drive_letter}: {free/(1024**3):.1f} GB free / {total/(1024**3):.1f} GB total ({used/total*100:.0f}% used)")
        except:
            pass
    
    print(f"\n{'=' * 70}")
    conn.close()


if __name__ == "__main__":
    print_dashboard()
