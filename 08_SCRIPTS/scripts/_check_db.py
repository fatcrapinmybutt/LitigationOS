import sys; sys.stdout.reconfigure(encoding='utf-8')
import sqlite3, os

db = r'C:\Users\andre\LitigationOS\litigation_context.db'
errors = []

try:
    conn = sqlite3.connect(db, timeout=120)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    
    # Integrity check (quick)
    result = conn.execute("PRAGMA quick_check").fetchone()
    print(f"DB quick_check: {result[0]}")
    
    # WAL size
    wal = db + "-wal"
    if os.path.exists(wal):
        print(f"WAL size: {os.path.getsize(wal)/1024/1024:.1f} MB")
        # Checkpoint if large
        if os.path.getsize(wal) > 50*1024*1024:
            conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
            print("WAL checkpoint executed")
    
    # Check for broken FTS indexes
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%_fts%' OR name LIKE '%_search%'").fetchall()]
    fts_errors = 0
    for t in tables[:10]:
        try:
            conn.execute(f"SELECT count(*) FROM [{t}]").fetchone()
        except Exception as e:
            fts_errors += 1
            errors.append(f"FTS table {t}: {e}")
    
    # Table count
    total = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
    print(f"Total tables: {total}")
    
    # Check for orphan temp tables
    temps = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name LIKE 'temp_%'").fetchone()[0]
    print(f"Temp tables: {temps}")
    
    conn.close()
except Exception as e:
    errors.append(f"DB connection error: {e}")

if errors:
    print(f"\nDB ERRORS ({len(errors)}):")
    for e in errors:
        print(f"  X {e}")
else:
    print("DB: All checks PASS")
