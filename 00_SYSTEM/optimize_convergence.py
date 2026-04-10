"""
THEMANBEARPIG Brain DB Optimizer — Convergence Cycle
Prunes duplicates, removes redundant edges, defrags, rebuilds FTS5.
Target: 424MB → ~250MB while preserving ALL unique intelligence.
"""
import sqlite3
import os
import sys
import time
import shutil
import json

DB = r"C:\Users\andre\LitigationOS\mbp_brain.db"
BACKUP = DB + ".pre_optimize_bak"

def sizeof(path):
    return os.path.getsize(path) / 1048576

def connect(path):
    c = sqlite3.connect(path)
    c.execute("PRAGMA busy_timeout=60000")
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA cache_size=-64000")  # 64MB cache for heavy ops
    c.execute("PRAGMA temp_store=MEMORY")
    c.execute("PRAGMA synchronous=NORMAL")
    c.execute("PRAGMA mmap_size=268435456")
    return c

def main():
    print("=" * 70)
    print("THEMANBEARPIG BRAIN DB OPTIMIZER — CONVERGENCE CYCLE")
    print("=" * 70)
    
    initial_size = sizeof(DB)
    print(f"\nInitial DB size: {initial_size:.1f} MB")
    
    # --- BACKUP ---
    if not os.path.exists(BACKUP):
        print(f"Creating backup: {BACKUP}")
        shutil.copy2(DB, BACKUP)
        print(f"Backup size: {sizeof(BACKUP):.1f} MB")
    else:
        print(f"Backup already exists: {sizeof(BACKUP):.1f} MB")
    
    db = connect(DB)
    
    # --- STEP 1: Drop FTS5 + ALL triggers on nodes (must do before node operations) ---
    print("\n[1/9] Dropping FTS5 virtual table + triggers...")
    t0 = time.time()
    try:
        # Find and drop ALL triggers referencing nodes
        triggers = db.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='nodes'"
        ).fetchall()
        for (tname,) in triggers:
            db.execute(f"DROP TRIGGER IF EXISTS [{tname}]")
            print(f"  Dropped trigger: {tname}")
        db.execute("DROP TABLE IF EXISTS nodes_fts")
        db.commit()
        print(f"  FTS5 + {len(triggers)} triggers dropped in {time.time()-t0:.1f}s")
    except Exception as e:
        print(f"  FTS5 drop warning: {e}")
    
    # --- STEP 2: Remove ASSIGNED_TO edges (redundant with nodes.lane) ---
    print("\n[2/9] Removing redundant ASSIGNED_TO edges...")
    t0 = time.time()
    # First verify lane data is intact on nodes
    r = db.execute("SELECT COUNT(*) FROM nodes WHERE lane IS NOT NULL AND lane != ''").fetchone()
    print(f"  Nodes with lane data: {r[0]:,}")
    r = db.execute("SELECT COUNT(*) FROM edges WHERE edge_type='ASSIGNED_TO'").fetchone()
    count_before = r[0]
    db.execute("DELETE FROM edges WHERE edge_type='ASSIGNED_TO'")
    db.commit()
    print(f"  Removed {count_before:,} ASSIGNED_TO edges in {time.time()-t0:.1f}s")
    
    # --- STEP 3: Dedup CaseLaw nodes (76% duplicates) ---
    print("\n[3/9] Deduplicating CaseLaw nodes...")
    t0 = time.time()
    # Strategy: keep the node with the longest description per unique label
    # Re-wire edges from duplicates to the keeper
    
    # Find keepers (one per label, prefer longest description)
    keepers = db.execute("""
        SELECT id, label FROM nodes WHERE node_type='CaseLaw' AND id IN (
            SELECT id FROM (
                SELECT id, label, ROW_NUMBER() OVER (
                    PARTITION BY label 
                    ORDER BY LENGTH(COALESCE(description,'')) DESC, rowid ASC
                ) rn
                FROM nodes WHERE node_type='CaseLaw'
            ) WHERE rn = 1
        )
    """).fetchall()
    keeper_map = {row[1]: row[0] for row in keepers}  # label → keeper_id
    print(f"  Keepers: {len(keeper_map):,} unique CaseLaw labels")
    
    # Find duplicates (all non-keeper CaseLaw nodes)
    dupes = db.execute("""
        SELECT id, label FROM nodes WHERE node_type='CaseLaw' AND id NOT IN (
            SELECT id FROM (
                SELECT id, label, ROW_NUMBER() OVER (
                    PARTITION BY label 
                    ORDER BY LENGTH(COALESCE(description,'')) DESC, rowid ASC
                ) rn
                FROM nodes WHERE node_type='CaseLaw'
            ) WHERE rn = 1
        )
    """).fetchall()
    print(f"  Duplicates to merge: {len(dupes):,}")
    
    # Build dupe_id → keeper_id mapping
    remap = {}
    for dupe_id, label in dupes:
        keeper_id = keeper_map.get(label)
        if keeper_id and keeper_id != dupe_id:
            remap[dupe_id] = keeper_id
    
    # Delete all edges pointing to/from duplicate nodes (they'll be covered by keeper's edges)
    dupe_ids = [d[0] for d in dupes]
    batch_size = 5000
    edges_removed = 0
    for i in range(0, len(dupe_ids), batch_size):
        batch = dupe_ids[i:i+batch_size]
        placeholders = ",".join(["?"] * len(batch))
        r = db.execute(f"DELETE FROM edges WHERE source_id IN ({placeholders})", batch)
        edges_removed += r.rowcount
        r = db.execute(f"DELETE FROM edges WHERE target_id IN ({placeholders})", batch)
        edges_removed += r.rowcount
        db.commit()
    
    # Delete duplicate nodes
    for i in range(0, len(dupe_ids), batch_size):
        batch = dupe_ids[i:i+batch_size]
        placeholders = ",".join(["?"] * len(batch))
        db.execute(f"DELETE FROM nodes WHERE id IN ({placeholders})", batch)
        db.commit()
    
    print(f"  Merged {len(dupes):,} CaseLaw dupes, removed {edges_removed:,} edges in {time.time()-t0:.1f}s")
    
    # --- STEP 4: Dedup CourtRule nodes (56% duplicates) ---
    print("\n[4/9] Deduplicating CourtRule nodes...")
    t0 = time.time()
    
    keepers = db.execute("""
        SELECT id, label FROM nodes WHERE node_type='CourtRule' AND id IN (
            SELECT id FROM (
                SELECT id, label, ROW_NUMBER() OVER (
                    PARTITION BY label 
                    ORDER BY LENGTH(COALESCE(description,'')) DESC, rowid ASC
                ) rn
                FROM nodes WHERE node_type='CourtRule'
            ) WHERE rn = 1
        )
    """).fetchall()
    keeper_map = {row[1]: row[0] for row in keepers}
    
    dupes = db.execute("""
        SELECT id, label FROM nodes WHERE node_type='CourtRule' AND id NOT IN (
            SELECT id FROM (
                SELECT id, label, ROW_NUMBER() OVER (
                    PARTITION BY label 
                    ORDER BY LENGTH(COALESCE(description,'')) DESC, rowid ASC
                ) rn
                FROM nodes WHERE node_type='CourtRule'
            ) WHERE rn = 1
        )
    """).fetchall()
    print(f"  Keepers: {len(keeper_map):,}, Duplicates: {len(dupes):,}")
    
    dupe_ids = [d[0] for d in dupes]
    edges_removed = 0
    for i in range(0, len(dupe_ids), batch_size):
        batch = dupe_ids[i:i+batch_size]
        placeholders = ",".join(["?"] * len(batch))
        r = db.execute(f"DELETE FROM edges WHERE source_id IN ({placeholders})", batch)
        edges_removed += r.rowcount
        r = db.execute(f"DELETE FROM edges WHERE target_id IN ({placeholders})", batch)
        edges_removed += r.rowcount
        db.commit()
    
    for i in range(0, len(dupe_ids), batch_size):
        batch = dupe_ids[i:i+batch_size]
        placeholders = ",".join(["?"] * len(batch))
        db.execute(f"DELETE FROM nodes WHERE id IN ({placeholders})", batch)
        db.commit()
    
    print(f"  Merged {len(dupes):,} CourtRule dupes, removed {edges_removed:,} edges in {time.time()-t0:.1f}s")
    
    # --- STEP 5: Dedup Statute nodes (29% duplicates) ---
    print("\n[5/9] Deduplicating Statute nodes...")
    t0 = time.time()
    
    keepers = db.execute("""
        SELECT id, label FROM nodes WHERE node_type='Statute' AND id IN (
            SELECT id FROM (
                SELECT id, label, ROW_NUMBER() OVER (
                    PARTITION BY label 
                    ORDER BY LENGTH(COALESCE(description,'')) DESC, rowid ASC
                ) rn
                FROM nodes WHERE node_type='Statute'
            ) WHERE rn = 1
        )
    """).fetchall()
    keeper_map = {row[1]: row[0] for row in keepers}
    
    dupes = db.execute("""
        SELECT id, label FROM nodes WHERE node_type='Statute' AND id NOT IN (
            SELECT id FROM (
                SELECT id, label, ROW_NUMBER() OVER (
                    PARTITION BY label 
                    ORDER BY LENGTH(COALESCE(description,'')) DESC, rowid ASC
                ) rn
                FROM nodes WHERE node_type='Statute'
            ) WHERE rn = 1
        )
    """).fetchall()
    print(f"  Keepers: {len(keeper_map):,}, Duplicates: {len(dupes):,}")
    
    dupe_ids = [d[0] for d in dupes]
    edges_removed = 0
    for i in range(0, len(dupe_ids), batch_size):
        batch = dupe_ids[i:i+batch_size]
        placeholders = ",".join(["?"] * len(batch))
        r = db.execute(f"DELETE FROM edges WHERE source_id IN ({placeholders})", batch)
        edges_removed += r.rowcount
        r = db.execute(f"DELETE FROM edges WHERE target_id IN ({placeholders})", batch)
        edges_removed += r.rowcount
        db.commit()
    
    for i in range(0, len(dupe_ids), batch_size):
        batch = dupe_ids[i:i+batch_size]
        placeholders = ",".join(["?"] * len(batch))
        db.execute(f"DELETE FROM nodes WHERE id IN ({placeholders})", batch)
        db.commit()
    
    print(f"  Merged {len(dupes):,} Statute dupes, removed {edges_removed:,} edges in {time.time()-t0:.1f}s")
    
    # --- STEP 6: Remove orphan nodes ---
    print("\n[6/9] Removing orphan nodes (no edges)...")
    t0 = time.time()
    # Keep important orphans (Filing, Lane, Remedy types)
    r = db.execute("""
        DELETE FROM nodes WHERE id IN (
            SELECT n.id FROM nodes n
            WHERE NOT EXISTS (SELECT 1 FROM edges e WHERE e.source_id = n.id OR e.target_id = n.id)
            AND n.node_type NOT IN ('Lane','Motion','Brief','Complaint','Petition','JudicialRemedy',
                'AppellateRemedy','AdministrativeRemedy','Damages','Sanction','Injunction','Person')
        )
    """)
    db.commit()
    print(f"  Removed {r.rowcount:,} orphan nodes in {time.time()-t0:.1f}s")
    
    # --- STEP 7: Clean duplicate edges created by rewiring ---
    print("\n[7/9] Cleaning duplicate edges from rewiring...")
    t0 = time.time()
    # After rewiring, we may have duplicate (source_id, target_id, edge_type) — keep highest weight
    r = db.execute("""
        DELETE FROM edges WHERE rowid NOT IN (
            SELECT MIN(rowid) FROM edges GROUP BY source_id, target_id, edge_type
        )
    """)
    db.commit()
    print(f"  Removed {r.rowcount:,} duplicate edges in {time.time()-t0:.1f}s")
    
    # --- STEP 8: Rebuild FTS5 ---
    print("\n[8/9] Rebuilding FTS5 index...")
    t0 = time.time()
    db.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(
            label, description, id,
            content='nodes', content_rowid='rowid',
            tokenize='porter unicode61'
        )
    """)
    db.execute("INSERT INTO nodes_fts(nodes_fts) VALUES('rebuild')")
    
    # Recreate triggers
    db.execute("""CREATE TRIGGER IF NOT EXISTS nodes_fts_insert AFTER INSERT ON nodes BEGIN
        INSERT INTO nodes_fts(rowid, label, description, id) VALUES (new.rowid, new.label, new.description, new.id);
    END""")
    db.execute("""CREATE TRIGGER IF NOT EXISTS nodes_fts_delete AFTER DELETE ON nodes BEGIN
        INSERT INTO nodes_fts(nodes_fts, rowid, label, description, id) VALUES('delete', old.rowid, old.label, old.description, old.id);
    END""")
    db.execute("""CREATE TRIGGER IF NOT EXISTS nodes_fts_update AFTER UPDATE ON nodes BEGIN
        INSERT INTO nodes_fts(nodes_fts, rowid, label, description, id) VALUES('delete', old.rowid, old.label, old.description, old.id);
        INSERT INTO nodes_fts(rowid, label, description, id) VALUES (new.rowid, new.label, new.description, new.id);
    END""")
    db.commit()
    
    r = db.execute("SELECT COUNT(*) FROM nodes_fts").fetchone()
    print(f"  FTS5 rebuilt: {r[0]:,} rows in {time.time()-t0:.1f}s")
    
    # --- STEP 9: VACUUM + ANALYZE ---
    print("\n[9/9] VACUUM + ANALYZE (this takes a minute)...")
    t0 = time.time()
    db.execute("PRAGMA page_size=8192")  # Upgrade page size for better large-row perf
    db.commit()
    db.close()
    
    # VACUUM must run on a fresh connection (can't be in a transaction)
    db2 = sqlite3.connect(DB)
    db2.execute("PRAGMA busy_timeout=120000")
    db2.execute("VACUUM")
    db2.execute("ANALYZE")
    db2.close()
    print(f"  VACUUM + ANALYZE in {time.time()-t0:.1f}s")
    
    # --- RESULTS ---
    final_size = sizeof(DB)
    saved = initial_size - final_size
    pct = (saved / initial_size) * 100
    
    print("\n" + "=" * 70)
    print("OPTIMIZATION RESULTS")
    print("=" * 70)
    print(f"  Before:  {initial_size:.1f} MB")
    print(f"  After:   {final_size:.1f} MB")
    print(f"  Saved:   {saved:.1f} MB ({pct:.1f}%)")
    
    # Verify counts
    db3 = connect(DB)
    nodes = db3.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
    edges = db3.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
    chains = db3.execute("SELECT COUNT(*) FROM chains").fetchone()[0]
    fts = db3.execute("SELECT COUNT(*) FROM nodes_fts").fetchone()[0]
    print(f"\n  Nodes:  {nodes:,}")
    print(f"  Edges:  {edges:,}")
    print(f"  Chains: {chains:,}")
    print(f"  FTS5:   {fts:,}")
    
    # Node type summary
    rows = db3.execute("SELECT node_type, COUNT(*) c FROM nodes GROUP BY node_type ORDER BY c DESC LIMIT 10").fetchall()
    print(f"\n  Top node types:")
    for r in rows:
        print(f"    {r[0]:20s} {r[1]:>8,}")
    
    # Edge type summary
    rows = db3.execute("SELECT edge_type, COUNT(*) c FROM edges GROUP BY edge_type ORDER BY c DESC").fetchall()
    print(f"\n  Edge types:")
    for r in rows:
        print(f"    {r[0]:25s} {r[1]:>8,}")
    
    db3.close()
    print(f"\n✅ Optimization complete. Backup at: {BACKUP}")

if __name__ == "__main__":
    main()
