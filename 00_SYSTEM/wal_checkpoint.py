"""WAL checkpoint on litigation_context.db to recover ~2.7 GB disk space."""
import sqlite3

db_path = r"C:\Users\andre\LitigationOS\litigation_context.db"
conn = sqlite3.connect(db_path)
conn.execute("PRAGMA busy_timeout = 120000")

# Check WAL size before
import os
wal_path = db_path + "-wal"
shm_path = db_path + "-shm"
wal_size = os.path.getsize(wal_path) if os.path.exists(wal_path) else 0
print(f"WAL size before: {wal_size / (1024**2):.1f} MB")

# Checkpoint
result = conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
print(f"Checkpoint result: busy={result[0]}, log={result[1]}, checkpointed={result[2]}")

conn.close()

wal_size_after = os.path.getsize(wal_path) if os.path.exists(wal_path) else 0
print(f"WAL size after: {wal_size_after / (1024**2):.1f} MB")
print(f"Recovered: {(wal_size - wal_size_after) / (1024**2):.1f} MB")
