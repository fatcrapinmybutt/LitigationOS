"""
SINGULARITY Automation Master — Disk Organization Campaign
Phase 0: Comprehensive analysis of all drives
Phase 1: C:\ space recovery
Phase 2: J:\ canonical structure creation
Phase 3: Evidence mirroring to J:\

RULES: COPY-only (never move/delete). All operations logged.
"""
import os
import sys
import sqlite3
import hashlib
import json
import time
from pathlib import Path
from datetime import datetime, date
from collections import defaultdict

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
J_ROOT = Path(r"J:\LitigationOS_CENTRAL")
LOG_PATH = Path(r"D:\LitigationOS_tmp\automation_log.jsonl")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn

def log_action(action: str, details: dict):
    entry = {"ts": datetime.now().isoformat(), "action": action, **details}
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

# ============================================================
# PHASE 0: ANALYSIS
# ============================================================
def phase0_analysis():
    """Comprehensive analysis of all drives and the repo."""
    conn = get_db()
    results = {}

    # 1. Per-drive file counts and sizes
    rows = conn.execute("""
        SELECT drive_letter, COUNT(*) as files, 
               ROUND(SUM(size_bytes)/1073741824.0, 2) as gb,
               COUNT(DISTINCT extension) as ext_types
        FROM file_inventory 
        GROUP BY drive_letter ORDER BY files DESC
    """).fetchall()
    results["drives_file_inventory"] = [
        {"drive": r[0], "files": r[1], "gb": r[2], "ext_types": r[3]} for r in rows
    ]

    # 2. Top-level directory analysis on C:\
    rows = conn.execute("""
        SELECT 
            CASE 
                WHEN file_path LIKE '%\\Desktop\\%' THEN 'Desktop'
                WHEN file_path LIKE '%\\LitigationOS\\01_EVIDENCE\\%' THEN 'LitOS/01_EVIDENCE'
                WHEN file_path LIKE '%\\LitigationOS\\00_SYSTEM\\%' THEN 'LitOS/00_SYSTEM'
                WHEN file_path LIKE '%\\LitigationOS\\05_FILINGS\\%' THEN 'LitOS/05_FILINGS'
                WHEN file_path LIKE '%\\LitigationOS\\10_EXTERNAL\\%' THEN 'LitOS/10_EXTERNAL'
                WHEN file_path LIKE '%\\LitigationOS\\09_REFERENCE\\%' THEN 'LitOS/09_REFERENCE'
                WHEN file_path LIKE '%\\LitigationOS\\.git\\%' THEN 'LitOS/.git'
                WHEN file_path LIKE '%\\LitigationOS\\%' THEN 'LitOS/other'
                WHEN file_path LIKE '%\\Downloads\\%' THEN 'Downloads'
                WHEN file_path LIKE '%\\Documents\\%' THEN 'Documents'
                ELSE 'C_other'
            END as area,
            COUNT(*) as files,
            ROUND(SUM(size_bytes)/1073741824.0, 2) as gb
        FROM file_inventory WHERE drive_letter = 'C'
        GROUP BY area ORDER BY gb DESC
    """).fetchall()
    results["c_drive_areas"] = [{"area": r[0], "files": r[1], "gb": r[2]} for r in rows]

    # 3. Desktop subdirectories (biggest opportunity for migration)
    rows = conn.execute("""
        SELECT 
            REPLACE(
                SUBSTR(file_path, 1, 
                    CASE WHEN INSTR(SUBSTR(file_path, 27), '\\') > 0 
                         THEN INSTR(SUBSTR(file_path, 27), '\\') + 26
                         ELSE LENGTH(file_path) END
                ),
                'C:\\Users\\andre\\Desktop\\', ''
            ) as subdir,
            COUNT(*) as files,
            ROUND(SUM(size_bytes)/1073741824.0, 2) as gb
        FROM file_inventory 
        WHERE drive_letter = 'C' AND file_path LIKE '%\\Desktop\\%'
        GROUP BY subdir
        HAVING SUM(size_bytes) > 1048576
        ORDER BY gb DESC LIMIT 25
    """).fetchall()
    results["desktop_dirs"] = [{"dir": r[0], "files": r[1], "gb": r[2]} for r in rows]

    # 4. Duplicate analysis (files with same SHA-256)
    row = conn.execute("""
        SELECT COUNT(*) as total_with_hash,
               (SELECT COUNT(*) FROM (
                   SELECT sha256 FROM file_inventory 
                   WHERE sha256 IS NOT NULL 
                   GROUP BY sha256 HAVING COUNT(*) > 1
               )) as dup_hashes,
               (SELECT COUNT(*) FROM file_inventory fi1
                WHERE sha256 IS NOT NULL
                AND EXISTS (SELECT 1 FROM file_inventory fi2 
                           WHERE fi2.sha256 = fi1.sha256 AND fi2.id != fi1.id)
               ) as dup_files
        FROM file_inventory WHERE sha256 IS NOT NULL
    """).fetchone()
    results["dedup"] = {"hashed_files": row[0], "duplicate_hashes": row[1], "duplicate_files": row[2]}

    # 5. Un-ingested evidence summary
    rows = conn.execute("""
        SELECT drive_letter, extension, COUNT(*) as cnt,
               ROUND(SUM(size_bytes)/1048576.0, 1) as mb
        FROM file_inventory 
        WHERE ingested = 0 
          AND extension IN ('.pdf', '.docx', '.txt', '.md', '.mp4', '.mp3')
        GROUP BY drive_letter, extension
        ORDER BY cnt DESC LIMIT 30
    """).fetchall()
    results["un_ingested"] = [
        {"drive": r[0], "ext": r[1], "count": r[2], "mb": r[3]} for r in rows
    ]

    # 6. ZIP files (102 GB potential)
    rows = conn.execute("""
        SELECT drive_letter, COUNT(*) as zips, 
               ROUND(SUM(size_bytes)/1073741824.0, 2) as gb
        FROM file_inventory WHERE extension = '.zip'
        GROUP BY drive_letter ORDER BY gb DESC
    """).fetchall()
    results["zip_files"] = [{"drive": r[0], "count": r[1], "gb": r[2]} for r in rows]

    # 7. Separation days (always report)
    sep_date = date(2025, 7, 29)
    today = date.today()
    results["separation_days"] = (today - sep_date).days

    conn.close()
    return results


# ============================================================
# PHASE 1: C:\ SPACE RECOVERY PLAN
# ============================================================
def phase1_recovery_plan():
    """Identify reclaimable space on C:\ — plan only, no action."""
    conn = get_db()
    plan = []

    # 1. Old backups on Desktop
    rows = conn.execute("""
        SELECT file_path, file_name, size_bytes FROM file_inventory
        WHERE drive_letter = 'C' 
          AND (file_path LIKE '%BACKUP%' OR file_path LIKE '%backup%')
        ORDER BY size_bytes DESC LIMIT 20
    """).fetchall()
    backup_gb = sum(r[2] for r in rows) / 1073741824.0
    plan.append({
        "category": "Desktop backups",
        "reclaimable_gb": round(backup_gb, 2),
        "action": "COPY to J:\\LitigationOS_CENTRAL\\ARCHIVE\\C_backups\\, then remove from C:\\",
        "files": len(rows),
        "risk": "LOW — these are copies of repo state from March 8 2026"
    })

    # 2. Downloads folder
    rows = conn.execute("""
        SELECT COUNT(*), ROUND(SUM(size_bytes)/1073741824.0, 2)
        FROM file_inventory 
        WHERE drive_letter = 'C' AND file_path LIKE '%\\Downloads\\%'
    """).fetchone()
    plan.append({
        "category": "Downloads folder",
        "reclaimable_gb": rows[1] or 0,
        "action": "Review and archive to J:\\, purge installers/temp files",
        "files": rows[0],
        "risk": "MEDIUM — review before removing"
    })

    # 3. __pycache__ directories
    rows = conn.execute("""
        SELECT COUNT(*), ROUND(SUM(size_bytes)/1048576.0, 1)
        FROM file_inventory 
        WHERE drive_letter = 'C' AND file_path LIKE '%__pycache__%'
    """).fetchone()
    plan.append({
        "category": "__pycache__ (auto-regenerated)",
        "reclaimable_mb": rows[1] or 0,
        "action": "Safe to purge — Python regenerates these on import",
        "files": rows[0],
        "risk": "ZERO"
    })

    # 4. 10_EXTERNAL (capstone data, test images)
    rows = conn.execute("""
        SELECT COUNT(*), ROUND(SUM(size_bytes)/1073741824.0, 2)
        FROM file_inventory 
        WHERE drive_letter = 'C' AND file_path LIKE '%10_EXTERNAL%'
    """).fetchone()
    plan.append({
        "category": "10_EXTERNAL/ (capstone, external tools)",
        "reclaimable_gb": rows[1] or 0,
        "action": "COPY to J:\\, consider removing from repo (large binary files)",
        "files": rows[0],
        "risk": "LOW — external reference data, not evidence"
    })

    # 5. Large .db files that might be stale
    rows = conn.execute("""
        SELECT file_path, file_name, ROUND(size_bytes/1048576.0, 1) as mb
        FROM file_inventory 
        WHERE drive_letter = 'C' AND extension = '.db' AND size_bytes > 10485760
        ORDER BY size_bytes DESC LIMIT 15
    """).fetchall()
    plan.append({
        "category": "Large databases (>10MB)",
        "items": [{"path": r[0], "name": r[1], "mb": r[2]} for r in rows],
        "action": "Audit — consolidate duplicates, move cold DBs to J:\\",
        "risk": "MEDIUM — some may be actively used"
    })

    conn.close()
    return plan


# ============================================================  
# PHASE 2: J:\ CANONICAL STRUCTURE
# ============================================================
def phase2_create_structure():
    """Create the canonical organization structure on J:\."""
    dirs = [
        J_ROOT / "EVIDENCE_BY_LANE" / "A_CUSTODY",
        J_ROOT / "EVIDENCE_BY_LANE" / "B_HOUSING",
        J_ROOT / "EVIDENCE_BY_LANE" / "C_FEDERAL",
        J_ROOT / "EVIDENCE_BY_LANE" / "D_PPO",
        J_ROOT / "EVIDENCE_BY_LANE" / "E_MISCONDUCT",
        J_ROOT / "EVIDENCE_BY_LANE" / "F_APPELLATE",
        J_ROOT / "EVIDENCE_BY_LANE" / "CRIMINAL",
        J_ROOT / "UNPACKED",
        J_ROOT / "DATABASES",
        J_ROOT / "ARCHIVE" / "C_backups",
        J_ROOT / "ARCHIVE" / "C_desktop",
        J_ROOT / "DEDUP_REPORT",
        J_ROOT / "INVENTORY",
        J_ROOT / "EVIDENCE_MIRROR" / "Desktop",
        J_ROOT / "EVIDENCE_MIRROR" / "I_drive",
        J_ROOT / "EVIDENCE_MIRROR" / "G_drive",
    ]
    created = []
    for d in dirs:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created.append(str(d))
            log_action("mkdir", {"path": str(d)})
    return created


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "analysis"
    
    if mode == "analysis":
        print("=" * 60)
        print("PHASE 0: COMPREHENSIVE ANALYSIS")
        print("=" * 60)
        results = phase0_analysis()
        
        print(f"\n📊 Separation days: {results['separation_days']}")
        
        print("\n--- Drive Inventory ---")
        for d in results["drives_file_inventory"]:
            print(f"  {d['drive'] or '?':>2}: {d['files']:>8,} files  {d['gb']:>8} GB  {d['ext_types']} types")
        
        print("\n--- C:\\ Area Breakdown ---")
        for a in results["c_drive_areas"]:
            print(f"  {a['area']:<25} {a['files']:>8,} files  {a['gb']:>8} GB")
        
        print("\n--- Desktop Directories ---")
        for d in results["desktop_dirs"][:15]:
            print(f"  {d['dir']:<40} {d['files']:>6,} files  {d['gb']:>6} GB")
        
        print(f"\n--- Dedup Status ---")
        dd = results["dedup"]
        print(f"  Hashed files: {dd['hashed_files']:,}")
        print(f"  Duplicate hashes: {dd['duplicate_hashes']:,}")
        print(f"  Duplicate files: {dd['duplicate_files']:,}")
        
        print(f"\n--- ZIP Files (potential evidence) ---")
        for z in results["zip_files"]:
            print(f"  {z['drive'] or '?':>2}: {z['count']:>5} zips  {z['gb']:>8} GB")
        
        print(f"\n--- Un-ingested Evidence ---")
        for u in results["un_ingested"][:15]:
            print(f"  {u['drive'] or '?':>2} {u['ext']:<6} {u['count']:>6,} files  {u['mb']:>8} MB")
    
    elif mode == "plan":
        print("=" * 60)
        print("PHASE 1: C:\\ SPACE RECOVERY PLAN")
        print("=" * 60)
        plan = phase1_recovery_plan()
        for item in plan:
            print(f"\n📦 {item['category']}")
            if "reclaimable_gb" in item:
                print(f"   Reclaimable: {item['reclaimable_gb']} GB")
            if "reclaimable_mb" in item:
                print(f"   Reclaimable: {item['reclaimable_mb']} MB")
            print(f"   Action: {item['action']}")
            print(f"   Risk: {item['risk']}")
            if "files" in item:
                print(f"   Files: {item['files']}")
            if "items" in item:
                for db in item["items"][:10]:
                    print(f"     {db['mb']:>8} MB  {db['name']}")
    
    elif mode == "structure":
        print("=" * 60)
        print("PHASE 2: CREATE J:\\ CANONICAL STRUCTURE")
        print("=" * 60)
        created = phase2_create_structure()
        print(f"Created {len(created)} directories:")
        for d in created:
            print(f"  ✅ {d}")
        if not created:
            print("  All directories already exist.")
    
    else:
        print(f"Unknown mode: {mode}")
        print("Usage: python automation_master.py [analysis|plan|structure]")
