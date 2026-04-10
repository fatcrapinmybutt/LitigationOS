"""Quick brain DB stats for cluster supernode plan."""
import sqlite3, os, json
from collections import Counter

DB = r"C:\Users\andre\LitigationOS\mbp_brain.db"
if not os.path.exists(DB):
    print(f"ERROR: {DB} not found")
    exit(1)

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

# 1. Node type distribution
print("=== NODE TYPE DISTRIBUTION ===")
rows = conn.execute("SELECT node_type, COUNT(*) as cnt FROM nodes GROUP BY node_type ORDER BY cnt DESC").fetchall()
for r in rows:
    print(f"  {r['node_type']:25s} {r['cnt']:>8,d}")
total_nodes = sum(r['cnt'] for r in rows)
print(f"  {'TOTAL':25s} {total_nodes:>8,d}")

# 2. Lane distribution
print("\n=== LANE DISTRIBUTION ===")
rows = conn.execute("SELECT lane, COUNT(*) as cnt FROM nodes GROUP BY lane ORDER BY cnt DESC").fetchall()
for r in rows:
    print(f"  {str(r['lane']):25s} {r['cnt']:>8,d}")

# 3. Nodes with dates (for temporal clustering)
print("\n=== TEMPORAL COVERAGE ===")
r = conn.execute("SELECT COUNT(*) as cnt FROM nodes WHERE date_start IS NOT NULL AND date_start != ''").fetchone()
print(f"  Nodes with date_start: {r['cnt']:,d}")
r = conn.execute("SELECT MIN(date_start) as mn, MAX(date_start) as mx FROM nodes WHERE date_start IS NOT NULL AND date_start != ''").fetchone()
print(f"  Date range: {r['mn']} to {r['mx']}")

# 4. Edge type distribution
print("\n=== EDGE TYPE DISTRIBUTION ===")
rows = conn.execute("SELECT edge_type, COUNT(*) as cnt FROM edges GROUP BY edge_type ORDER BY cnt DESC").fetchall()
for r in rows:
    print(f"  {r['edge_type']:25s} {r['cnt']:>8,d}")
total_edges = sum(r['cnt'] for r in rows)
print(f"  {'TOTAL':25s} {total_edges:>8,d}")

# 5. Edge weight distribution
print("\n=== EDGE WEIGHT DISTRIBUTION ===")
for threshold in [0.1, 0.2, 0.3, 0.5, 0.7, 0.9]:
    r = conn.execute("SELECT COUNT(*) as cnt FROM edges WHERE weight < ?", (threshold,)).fetchone()
    print(f"  weight < {threshold}: {r['cnt']:,d}")

# 6. Connectivity (nodes with most edges)
print("\n=== TOP 15 CONNECTED NODES ===")
rows = conn.execute("""
    SELECT n.id, n.node_type, n.label, COUNT(*) as edge_count
    FROM nodes n
    JOIN edges e ON n.id = e.source_id OR n.id = e.target_id
    GROUP BY n.id
    ORDER BY edge_count DESC LIMIT 15
""").fetchall()
for r in rows:
    print(f"  {r['edge_count']:>5d} edges | {r['node_type']:15s} | {r['label'][:60]}")

# 7. Chains summary
print("\n=== CHAINS ===")
r = conn.execute("SELECT COUNT(*) as cnt FROM chains").fetchone()
print(f"  Total chains: {r['cnt']}")
rows = conn.execute("SELECT chain_type, COUNT(*) as cnt FROM chains GROUP BY chain_type ORDER BY cnt DESC LIMIT 10").fetchall()
for r in rows:
    print(f"  {r['chain_type']:25s} {r['cnt']:>5d}")

# 8. Graph data JSON stats
gj = r"C:\Users\andre\LitigationOS\08_MEDIA\MANBEARPIG_V9\graph_data.json"
if os.path.exists(gj):
    with open(gj, 'r', encoding='utf-8') as f:
        gd = json.load(f)
    print(f"\n=== GRAPH_DATA.JSON ===")
    print(f"  Nodes: {len(gd.get('nodes', []))}")
    print(f"  Links: {len(gd.get('links', []))}")
    # Node types in JSON
    types = Counter(n.get('type','?') for n in gd.get('nodes', []))
    print(f"  Types: {dict(types.most_common(10))}")

# 9. Tables list
print("\n=== ALL TABLES ===")
rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
for r in rows:
    cnt = conn.execute(f"SELECT COUNT(*) FROM [{r['name']}]").fetchone()[0]
    print(f"  {r['name']:30s} {cnt:>10,d} rows")

conn.close()
print("\nDone.")
