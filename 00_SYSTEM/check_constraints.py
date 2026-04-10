import sqlite3, os
db = r"C:\Users\andre\LitigationOS\mbp_brain.db"
conn = sqlite3.connect(db)
conn.execute("PRAGMA busy_timeout=60000")

# Get CREATE TABLE statements for exact constraints
for tbl in ['nodes', 'edges', 'ingest_queue', 'brain_ops', 'versions']:
    row = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (tbl,)).fetchone()
    print(f"\n=== {tbl} ===")
    print(row[0] if row else "NOT FOUND")

# Get all indexes
print("\n=== INDEXES ===")
for row in conn.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL"):
    print(f"{row[0]} ON {row[1]}: {row[2]}")

# Check total nodes and edges
print(f"\nTotal nodes: {conn.execute('SELECT count(*) FROM nodes').fetchone()[0]}")
print(f"Total edges: {conn.execute('SELECT count(*) FROM edges').fetchone()[0]}")
print(f"Total ingest_queue: {conn.execute('SELECT count(*) FROM ingest_queue').fetchone()[0]}")

# Check if there's a unique constraint on ingest_queue.file_path
print("\n=== ingest_queue indexes ===")
for row in conn.execute("PRAGMA index_list(ingest_queue)"):
    print(row)
    idx_name = row[1]
    for col in conn.execute(f"PRAGMA index_info({idx_name})"):
        print(f"  col: {col}")

conn.close()
