"""
Automated Maintenance Runner — Phase 6.7
Executes scheduled maintenance tasks from schedule.json
"""
import sqlite3
import sys
import os
import json
import shutil
import hashlib
import time
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
SCHEDULE_PATH = r"C:\Users\andre\LitigationOS\00_SYSTEM\maintenance\schedule.json"


def ensure_log_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT,
            category TEXT,
            status TEXT,
            details TEXT,
            duration_seconds REAL,
            run_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()


def log_task(conn, name, category, status, details, duration):
    conn.execute(
        "INSERT INTO maintenance_log (task_name, category, status, details, duration_seconds) VALUES (?,?,?,?,?)",
        (name, category, status, details, duration)
    )
    conn.commit()


def disk_space_check(drives, threshold_gb=2):
    results = []
    for d in drives:
        try:
            total, used, free = shutil.disk_usage(f"{d}:\\")
            free_gb = free / (1024**3)
            status = "OK" if free_gb >= threshold_gb else "ALERT"
            results.append(f"{d}: {free_gb:.1f}GB free [{status}]")
            if status == "ALERT":
                print(f"  [!] ALERT: {d}: drive only {free_gb:.1f}GB free!")
        except Exception as e:
            results.append(f"{d}: ERROR - {e}")
    return "; ".join(results)


def db_integrity_check(db_path):
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        result = conn.execute("PRAGMA integrity_check").fetchone()[0]
        table_count = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
        conn.close()
        return f"integrity={result}, tables={table_count}"
    except Exception as e:
        return f"ERROR: {e}"


def temp_cleanup(paths, max_age_days=7):
    cleaned = 0
    cleaned_bytes = 0
    cutoff = time.time() - (max_age_days * 86400)
    
    for base_path in paths:
        if not os.path.exists(base_path):
            continue
        try:
            for root, dirs, files in os.walk(base_path, topdown=False):
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        if os.path.getmtime(fp) < cutoff:
                            size = os.path.getsize(fp)
                            os.remove(fp)
                            cleaned += 1
                            cleaned_bytes += size
                    except:
                        pass
        except:
            pass
    
    return f"Cleaned {cleaned} files ({cleaned_bytes/(1024**2):.1f} MB)"


def run_daily(schedule, conn):
    print("\n[DAILY MAINTENANCE]")
    for task in schedule.get('daily', {}).get('tasks', []):
        name = task['name']
        start = time.time()
        print(f"  Running: {name}...")
        
        try:
            if name == 'disk_space_check':
                result = disk_space_check(task['drives'], task.get('alert_threshold_gb', 2))
            elif name == 'db_integrity_check':
                result = db_integrity_check(task['db_path'])
            elif name == 'temp_cleanup':
                result = temp_cleanup(task['paths'], task.get('max_age_days', 7))
            elif name == 'agent_health_check':
                result = "Agent check: placeholder (manual review needed)"
            else:
                result = f"Unknown task: {name}"
            
            duration = time.time() - start
            status = "ALERT" if "ALERT" in str(result) or "ERROR" in str(result) else "OK"
            log_task(conn, name, "daily", status, result, duration)
            print(f"    -> {result} ({duration:.1f}s)")
        except Exception as e:
            duration = time.time() - start
            log_task(conn, name, "daily", "ERROR", str(e), duration)
            print(f"    -> ERROR: {e}")


def run_maintenance(category="daily"):
    with open(SCHEDULE_PATH, 'r') as f:
        schedule = json.load(f)
    
    conn = sqlite3.connect(DB_PATH)
    ensure_log_table(conn)
    
    print(f"{'='*60}")
    print(f"  MAINTENANCE RUNNER — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    if category in ("daily", "all"):
        run_daily(schedule, conn)
    
    # Show recent logs
    recent = conn.execute("""
        SELECT task_name, status, details, run_at 
        FROM maintenance_log 
        ORDER BY id DESC LIMIT 10
    """).fetchall()
    
    print(f"\n  RECENT MAINTENANCE LOG:")
    for name, status, details, run_at in recent:
        icon = "[OK]" if status == "OK" else "[!!]"
        print(f"    {icon} {run_at} | {name}: {details[:60]}")
    
    conn.close()
    print(f"\n{'='*60}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--category', default='daily', choices=['daily', 'weekly', 'monthly', 'all'])
    args = parser.parse_args()
    run_maintenance(args.category)
