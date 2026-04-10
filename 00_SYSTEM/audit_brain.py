"""Comprehensive audit of mbp_brain.db — duplicates, bloat, optimization targets."""
import sqlite3, os, json

DB = r"C:\Users\andre\LitigationOS\mbp_brain.db"
db = sqlite3.connect(DB)
db.execute("PRAGMA busy_timeout=30000")
db.execute("PRAGMA cache_size=-32000")

print("=" * 60)
print("THEMANBEARPIG BRAIN DB — FULL AUDIT")
print("=" * 60)

sz = os.path.getsize(DB)
print(f"\nDB file size: {sz/1048576:.1f} MB")
ps = db.execute("PRAGMA page_size").fetchone()[0]
pc = db.execute("PRAGMA page_count").fetchone()[0]
fc = db.execute("PRAGMA freelist_count").fetchone()[0]
print(f"Page size: {ps}, Pages: {pc:,}, Free: {fc:,}")
print(f"Used: {(pc-fc)*ps/1048576:.1f} MB, Wasted: {fc*ps/1048576:.1f} MB")

# --- NODE ANALYSIS ---
print("\n" + "=" * 60)
print("NODE ANALYSIS (232K nodes)")
print("=" * 60)

rows = db.execute("SELECT node_type, COUNT(*) c FROM nodes GROUP BY node_type ORDER BY c DESC").fetchall()
for r in rows:
    print(f"  {r[0]:25s} {r[1]:>8,}")

# Duplicate detection
print("\n--- DUPLICATE DETECTION ---")
for nt in ["Quote", "CaseLaw", "CourtRule", "Statute", "Event", "Pattern"]:
    total = db.execute("SELECT COUNT(*) FROM nodes WHERE node_type=?", (nt,)).fetchone()[0]
    unique_label = db.execute("SELECT COUNT(DISTINCT label) FROM nodes WHERE node_type=?", (nt,)).fetchone()[0]
    unique_short = db.execute("SELECT COUNT(DISTINCT substr(label,1,80)) FROM nodes WHERE node_type=?", (nt,)).fetchone()[0]
    dup_pct = (1 - unique_label / max(total, 1)) * 100
    print(f"  {nt:15s}: {total:>8,} total, {unique_label:>8,} unique labels ({dup_pct:.1f}% duplicates), {unique_short:>8,} unique(80ch)")

# Text size analysis
print("\n--- TEXT SIZE ANALYSIS ---")
r = db.execute("SELECT SUM(LENGTH(label)), SUM(LENGTH(description)), SUM(LENGTH(metadata)) FROM nodes").fetchone()
print(f"  Node labels:       {(r[0] or 0)/1048576:.1f} MB")
print(f"  Node descriptions: {(r[1] or 0)/1048576:.1f} MB")
print(f"  Node metadata:     {(r[2] or 0)/1048576:.1f} MB")
r = db.execute("SELECT SUM(LENGTH(evidence)) FROM edges").fetchone()
print(f"  Edge evidence:     {(r[0] or 0)/1048576:.1f} MB")

# Description bloat analysis
print("\n--- DESCRIPTION LENGTH BY TYPE ---")
for nt in ["Quote", "CaseLaw", "CourtRule", "Event", "Statute", "Pattern", "Contradiction"]:
    r = db.execute("SELECT AVG(LENGTH(COALESCE(description,''))), MAX(LENGTH(COALESCE(description,''))), COUNT(*) FROM nodes WHERE node_type=?", (nt,)).fetchone()
    if r[0]:
        print(f"  {nt:15s}: avg {r[0]:>6.0f} ch, max {r[1]:>8,} ch, count {r[2]:>8,}  ({r[0]*r[2]/1048576:.1f} MB total)")

# --- EDGE ANALYSIS ---
print("\n" + "=" * 60)
print("EDGE ANALYSIS (770K edges)")
print("=" * 60)

rows = db.execute("SELECT edge_type, COUNT(*) c, AVG(LENGTH(COALESCE(evidence,''))) FROM edges GROUP BY edge_type ORDER BY c DESC").fetchall()
for r in rows:
    print(f"  {r[0]:25s} {r[1]:>8,}  avg_evidence: {r[2]:>6.0f} ch")

# Duplicate edges
print("\n--- DUPLICATE EDGES ---")
r = db.execute("SELECT COUNT(*) FROM (SELECT source_id, target_id, edge_type, COUNT(*) c FROM edges GROUP BY source_id, target_id, edge_type HAVING c > 1)").fetchone()
print(f"  Duplicate (src,tgt,type) combos: {r[0]:,}")

# --- INDEX ANALYSIS ---
print("\n" + "=" * 60)
print("INDEX ANALYSIS")
print("=" * 60)
rows = db.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index' ORDER BY tbl_name").fetchall()
for r in rows:
    print(f"  {r[0]:45s} on {r[1]}")

# --- FTS5 OVERHEAD ---
print("\n" + "=" * 60)
print("FTS5 OVERHEAD ESTIMATE")
print("=" * 60)
# Estimate FTS5 size by checking shadow tables
for t in ["nodes_fts_content", "nodes_fts_idx", "nodes_fts_data", "nodes_fts_docsize"]:
    try:
        r = db.execute(f"SELECT COUNT(*), SUM(LENGTH(block)) FROM [{t}]").fetchone()
        if r[1]:
            print(f"  {t}: {r[0]:,} rows, {r[1]/1048576:.1f} MB")
    except Exception as e:
        print(f"  {t}: error — {e}")

# --- PRUNING OPPORTUNITIES ---
print("\n" + "=" * 60)
print("PRUNING OPPORTUNITIES")
print("=" * 60)

# Nodes with no edges (orphans)
r = db.execute("""
    SELECT COUNT(*) FROM nodes n 
    WHERE NOT EXISTS (SELECT 1 FROM edges e WHERE e.source_id = n.id OR e.target_id = n.id)
""").fetchone()
print(f"  Orphan nodes (no edges): {r[0]:,}")

# Low-value nodes: Quote with very short labels
r = db.execute("SELECT COUNT(*) FROM nodes WHERE node_type='Quote' AND LENGTH(label) < 20").fetchone()
print(f"  Short quotes (<20 chars): {r[0]:,}")

# Nodes with NULL/empty description
r = db.execute("SELECT COUNT(*) FROM nodes WHERE description IS NULL OR description = ''").fetchone()
print(f"  Nodes with empty description: {r[0]:,}")

# Edges with zero weight
r = db.execute("SELECT COUNT(*) FROM edges WHERE weight = 0 OR weight IS NULL").fetchone()
print(f"  Zero-weight edges: {r[0]:,}")

# ASSIGNED_TO edges (lane assignments — could be stored as column instead)
r = db.execute("SELECT COUNT(*) FROM edges WHERE edge_type='ASSIGNED_TO'").fetchone()
print(f"  ASSIGNED_TO edges (lane assignments): {r[0]:,}")
print(f"    → These are redundant with nodes.lane column. Removing saves ~26% of edges.")

# RELATED edges (weak, low info)
r = db.execute("SELECT COUNT(*), AVG(weight) FROM edges WHERE edge_type='RELATED'").fetchone()
print(f"  RELATED edges: {r[0]:,} (avg weight: {r[1]:.3f})")
print(f"    → Low-specificity edges. Pruning below weight 0.3 may remove many.")

r = db.execute("SELECT COUNT(*) FROM edges WHERE edge_type='RELATED' AND weight < 0.3").fetchone()
print(f"    → RELATED with weight < 0.3: {r[0]:,}")

# --- VACUUM POTENTIAL ---
print("\n" + "=" * 60)
print("OPTIMIZATION ACTIONS")
print("=" * 60)
print(f"  1. Remove ASSIGNED_TO edges (200K) — lane info in nodes.lane column")
print(f"  2. Dedup Quote nodes (~{120000-90000:,} removable)")
print(f"  3. Dedup CaseLaw nodes by label")
print(f"  4. Truncate long descriptions (>500ch) to save text space")
print(f"  5. Remove zero-weight edges")
print(f"  6. Prune RELATED edges with weight < 0.3")
print(f"  7. Drop + rebuild FTS5 after pruning")
print(f"  8. Change page_size from 4096 → 8192 for large-row data")
print(f"  9. VACUUM to reclaim space")

db.close()
print("\nAudit complete.")
