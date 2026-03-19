#!/usr/bin/env python3
"""OMEGA Integrity Checker — validates DB + files + configs against baseline."""
import hashlib, os, sys, json, sqlite3
from datetime import datetime

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
BACKUP_7Z = r"C:\Users\andre\SAFETY_SNAPSHOT_DB\litigation_context.db.7z"
MANIFEST = r"C:\Users\andre\SAFETY_SNAPSHOT_DB\MANIFEST.txt"

CRITICAL_PATHS = [
    DB_PATH,
    r"C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\config.py",
    r"C:\Users\andre\LitigationOS\13_TOOLS\START.ps1",
    r"C:\Users\andre\.github\copilot-instructions.md",
]

NEVER_DELETE = [
    DB_PATH,
    r"C:\Users\andre\LitigationOS\06_EMERGENCY",
    r"C:\Users\andre\LitigationOS\01_COA_366810",
    r"C:\Users\andre\LitigationOS\02_TRIAL_14TH",
    r"C:\Users\andre\LitigationOS\03_FEDERAL_1983",
    r"C:\Users\andre\LitigationOS\04_JTC_MCNEILL",
]

MIN_FREE_GB = 2  # Abort operations if less than this

def check_disk_space():
    """Check all drives have minimum free space."""
    import ctypes
    results = []
    for drive in ["C:\\", "D:\\", "F:\\", "G:\\", "H:\\", "I:\\"]:
        free = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(drive, None, None, ctypes.byref(free))
        free_gb = free.value / (1024**3)
        ok = free_gb >= MIN_FREE_GB
        results.append({"drive": drive, "free_gb": round(free_gb, 2), "ok": ok})
    return results

def check_critical_files():
    """Verify all critical files exist."""
    results = []
    for p in CRITICAL_PATHS:
        exists = os.path.exists(p)
        size = os.path.getsize(p) if exists else 0
        results.append({"path": p, "exists": exists, "size": size})
    return results

def check_db_integrity():
    """Run SQLite integrity check."""
    try:
        conn = sqlite3.connect(DB_PATH)
        result = conn.execute("PRAGMA integrity_check").fetchone()[0]
        table_count = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
        conn.close()
        return {"integrity": result, "tables": table_count, "ok": result == "ok"}
    except Exception as e:
        return {"integrity": str(e), "tables": 0, "ok": False}

def check_backup():
    """Verify backup archive exists."""
    exists = os.path.exists(BACKUP_7Z)
    size = os.path.getsize(BACKUP_7Z) if exists else 0
    return {"exists": exists, "size": size, "path": BACKUP_7Z}

def run_all():
    """Run all integrity checks."""
    print(f"=== OMEGA INTEGRITY CHECK — {datetime.now().isoformat()} ===\n")
    
    disks = check_disk_space()
    print("DISK SPACE:")
    for d in disks:
        status = "✓" if d["ok"] else "✗ CRITICAL"
        print(f"  {status} {d['drive']} {d['free_gb']}GB free")
    
    files = check_critical_files()
    print("\nCRITICAL FILES:")
    for f in files:
        status = "✓" if f["exists"] else "✗ MISSING"
        print(f"  {status} {f['path']} ({f['size']} bytes)")
    
    db = check_db_integrity()
    print(f"\nDATABASE:")
    print(f"  {'✓' if db['ok'] else '✗'} Integrity: {db['integrity']}")
    print(f"  Tables: {db['tables']}")
    
    backup = check_backup()
    print(f"\nBACKUP:")
    print(f"  {'✓' if backup['exists'] else '✗'} {backup['path']} ({backup['size']} bytes)")
    
    all_ok = (
        all(d["ok"] for d in disks) and
        all(f["exists"] for f in files) and
        db["ok"] and backup["exists"]
    )
    print(f"\n{'='*50}")
    print(f"OVERALL: {'✓ ALL CHECKS PASSED' if all_ok else '✗ ISSUES DETECTED'}")
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(run_all())
