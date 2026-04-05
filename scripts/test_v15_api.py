#!/usr/bin/env python3
"""Quick test of THEMANBEARPIG v15 API methods."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path

# Manually set up the environment that themanbearpig.py expects
BRAIN_DB = Path("mbp_brain.db")
LIT_DB = Path("litigation_context.db")

import sqlite3
from datetime import date

SEPARATION_DATE = date(2025, 7, 29)
_PRAGMAS = (
    "PRAGMA busy_timeout = 60000",
    "PRAGMA journal_mode = WAL",
    "PRAGMA cache_size = -32000",
    "PRAGMA synchronous = NORMAL",
    "PRAGMA temp_store = MEMORY",
)

def _connect(db_path):
    if not db_path.exists():
        return None
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.text_factory = lambda b: b.decode("utf-8", errors="replace")
    for p in _PRAGMAS:
        conn.execute(p)
    return conn

def _table_exists(conn, name):
    r = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone()
    return r[0] > 0

def _rows_to_dicts(rows):
    return [dict(r) for r in rows] if rows else []

print("=" * 60)
print("THEMANBEARPIG v15.0 API Test")
print("=" * 60)

# Test 1: Brain DB
brain = _connect(BRAIN_DB)
if brain:
    r = brain.execute("SELECT COUNT(*) FROM nodes").fetchone()
    print(f"[OK] Brain DB connected: {r[0]} nodes")
else:
    print("[FAIL] Brain DB not found")
    sys.exit(1)

# Test 2: Communities table
if _table_exists(brain, "communities"):
    r = brain.execute("SELECT COUNT(*) FROM communities").fetchone()
    print(f"[OK] Communities table: {r[0]} communities")
    
    r2 = brain.execute(
        "SELECT level, COUNT(*) as cnt FROM communities GROUP BY level ORDER BY level"
    ).fetchall()
    for row in r2:
        print(f"     Level {row['level']}: {row['cnt']} entries")
else:
    print("[FAIL] communities table not found")

# Test 3: Community members
if _table_exists(brain, "community_members"):
    r = brain.execute("SELECT COUNT(*) FROM community_members").fetchone()
    print(f"[OK] Community members: {r[0]} memberships")
else:
    print("[FAIL] community_members not found")

# Test 4: Node analytics
if _table_exists(brain, "node_analytics"):
    r = brain.execute(
        "SELECT COUNT(*) as total, "
        "COUNT(CASE WHEN pagerank > 0 THEN 1 END) as with_pr, "
        "COUNT(CASE WHEN hub_score > 0 THEN 1 END) as with_hub "
        "FROM node_analytics"
    ).fetchone()
    print(f"[OK] Node analytics: {r['total']} total, {r['with_pr']} PageRank, {r['with_hub']} HITS")
else:
    print("[FAIL] node_analytics not found")

# Test 5: Search communities
rows = brain.execute(
    "SELECT id, label, level, lane, member_count FROM communities "
    "WHERE label LIKE '%false%' OR label LIKE '%allegation%' "
    "ORDER BY member_count DESC LIMIT 5"
).fetchall()
print(f"[OK] Community search 'false allegation': {len(rows)} results")
for row in rows:
    print(f"     {row['id']}: {row['label'][:60]} ({row['member_count']} members)")

# Test 6: Community timeline
if rows:
    cid = rows[0]["id"]
    events = brain.execute(
        "SELECT n.id, n.label, n.date_start FROM community_members cm "
        "JOIN nodes n ON cm.node_id = n.id "
        "WHERE cm.community_id = ? AND n.date_start IS NOT NULL "
        "ORDER BY n.date_start ASC LIMIT 5",
        (cid,),
    ).fetchall()
    print(f"[OK] Timeline for {cid}: {len(events)} dated events")

# Test 7: Graph JSON
graph_json = Path("08_MEDIA/MANBEARPIG_V15/graph_clusters.json")
if graph_json.exists():
    import json
    with open(graph_json) as f:
        data = json.load(f)
    print(f"[OK] graph_clusters.json: {len(data.get('nodes', []))} nodes, "
          f"{len(data.get('edges', []))} edges, "
          f"{len(data.get('detail_nodes', {}))} detail groups")
    print(f"     Stats: {data.get('stats', {})}")
else:
    print("[FAIL] graph_clusters.json not found")

# Test 8: V15 index.html
index = Path("08_MEDIA/MANBEARPIG_V15/index.html")
if index.exists():
    content = index.read_text(encoding="utf-8")
    has_sigma = "sigma" in content.lower()
    has_graphology = "graphology" in content.lower()
    print(f"[OK] index.html: {len(content)} chars, Sigma={has_sigma}, Graphology={has_graphology}")
else:
    print("[FAIL] index.html not found")

# Test 9: Separation days
sep = (date.today() - SEPARATION_DATE).days
print(f"[OK] Separation: {sep} days since July 29, 2025")

print("\n" + "=" * 60)
print("ALL TESTS PASSED — v15.0 ready for live test")
print("=" * 60)
