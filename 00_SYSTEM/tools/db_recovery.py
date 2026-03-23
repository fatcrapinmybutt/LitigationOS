import sqlite3
import os
import time

db_path = r"..\..\litigation_context.db"

# Try to recover
try:
    print("Attempting database recovery...")
    conn = sqlite3.connect(db_path, timeout=3)
    conn.execute("PRAGMA journal_mode=DELETE")
    conn.execute("PRAGMA integrity_check")
    conn.close()
    print("Recovery completed")
except Exception as e:
    print(f"Recovery error: {e}")
    
time.sleep(1)

# Now try write
try:
    print("Testing write access...")
    conn = sqlite3.connect(db_path, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("CREATE TABLE IF NOT EXISTS _lock_test (id INTEGER)")
    conn.execute("DROP TABLE _lock_test")
    print("DB WRITE OK")
    conn.close()
except Exception as e:
    print(f"Write failed: {e}")
