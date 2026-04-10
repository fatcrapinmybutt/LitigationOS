"""Benchmark mbp_brain.db — indexes, query times, optimization targets."""
import sqlite3, time, os

DB = r"C:\Users\andre\LitigationOS\mbp_brain.db"
c = sqlite3.connect(DB)
c.execute("PRAGMA journal_mode=WAL")
c.execute("PRAGMA cache_size=-32000")
c.execute("PRAGMA mmap_size=268435456")

# Indexes
idxs = c.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()
print(f"Indexes: {len(idxs)}")
for i in idxs:
    print(f"  {i[0]}")

# Table sizes
print("\n--- Table Sizes ---")
tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
for (t,) in tables:
    n = c.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
    print(f"  {t}: {n:,}")

# Benchmark queries
print("\n--- Query Benchmarks ---")
benchmarks = [
    ("All filing nodes", "SELECT * FROM nodes WHERE layer='FILING'"),
    ("All authority nodes (COUNT)", "SELECT COUNT(*) FROM nodes WHERE layer='AUTHORITY'"),
    ("Top 10 chains", "SELECT * FROM chains ORDER BY score DESC LIMIT 10"),
    ("LIKE search (custody)", "SELECT COUNT(*) FROM nodes WHERE label LIKE '%custody%'"),
    ("Edge count for filing", "SELECT COUNT(*) FROM edges WHERE source IN (SELECT id FROM nodes WHERE layer='FILING')"),
    ("Gaps (open)", "SELECT COUNT(*) FROM gaps WHERE resolved=0"),
    ("Node by ID", "SELECT * FROM nodes WHERE id='MCR_2.003'"),
    ("Edges by source", "SELECT * FROM edges WHERE source='MCR_2.003' LIMIT 50"),
    ("Full node scan", "SELECT COUNT(*) FROM nodes"),
    ("Full edge scan", "SELECT COUNT(*) FROM edges"),
]

for name, sql in benchmarks:
    t0 = time.perf_counter()
    try:
        rows = c.execute(sql).fetchall()
        ms = (time.perf_counter() - t0) * 1000
        print(f"  {name}: {ms:.1f}ms ({len(rows)} rows)")
    except Exception as e:
        print(f"  {name}: ERROR — {e}")

# Check if FTS exists
fts = c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%fts%'").fetchall()
print(f"\nFTS tables: {[f[0] for f in fts] if fts else 'NONE'}")

# Column info for nodes
print("\n--- nodes columns ---")
cols = c.execute("PRAGMA table_info(nodes)").fetchall()
for col in cols:
    print(f"  {col[1]} ({col[2]})")

print("\n--- edges columns ---")
cols = c.execute("PRAGMA table_info(edges)").fetchall()
for col in cols:
    print(f"  {col[1]} ({col[2]})")

# DB file size
sz = os.path.getsize(DB)
print(f"\nDB size: {sz/1024/1024:.1f} MB")

# graph_data.json size
gj = r"C:\Users\andre\LitigationOS\08_MEDIA\MANBEARPIG_V9\graph_data.json"
if os.path.exists(gj):
    import json
    t0 = time.perf_counter()
    with open(gj) as f:
        data = json.load(f)
    ms = (time.perf_counter() - t0) * 1000
    print(f"graph_data.json: {os.path.getsize(gj)/1024/1024:.1f} MB, load time: {ms:.0f}ms")
    print(f"  nodes: {len(data.get('nodes',[]))}, edges: {len(data.get('edges',[]))}")

c.close()
