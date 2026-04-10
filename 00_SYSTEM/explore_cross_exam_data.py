"""Explore impeachment_matrix, contradiction_map, and evidence_quotes for cross-exam bank building."""
import sqlite3, os, json

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"

conn = sqlite3.connect(DB, timeout=60)
conn.execute("PRAGMA busy_timeout=60000")
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA cache_size=-32000")
conn.row_factory = sqlite3.Row

# 1. Schema of impeachment_matrix
print("=" * 80)
print("IMPEACHMENT_MATRIX SCHEMA")
print("=" * 80)
cols = conn.execute("PRAGMA table_info(impeachment_matrix)").fetchall()
for c in cols:
    print(f"  {c['name']:30s} {c['type']:15s} nullable={c['notnull']==0}")

print(f"\nTotal rows: {conn.execute('SELECT COUNT(*) FROM impeachment_matrix').fetchone()[0]}")

# Sample Watson rows
print("\n--- Watson impeachment samples (top 10 by severity) ---")
try:
    rows = conn.execute("""
        SELECT * FROM impeachment_matrix 
        WHERE target LIKE '%Watson%' OR target LIKE '%Emily%' OR target LIKE '%mother%' OR target LIKE '%defendant%'
        ORDER BY CASE WHEN typeof(severity) = 'integer' OR typeof(severity) = 'real' THEN CAST(severity AS REAL) ELSE 0 END DESC
        LIMIT 10
    """).fetchall()
    for r in rows:
        print(dict(r))
except Exception as e:
    print(f"Error querying Watson: {e}")
    # Try alternate column names
    rows = conn.execute("SELECT * FROM impeachment_matrix LIMIT 3").fetchall()
    for r in rows:
        print(dict(r))

# Sample McNeill rows
print("\n--- McNeill impeachment samples (top 10 by severity) ---")
try:
    rows = conn.execute("""
        SELECT * FROM impeachment_matrix 
        WHERE target LIKE '%McNeill%' OR target LIKE '%judge%' OR target LIKE '%judicial%'
        ORDER BY CASE WHEN typeof(severity) = 'integer' OR typeof(severity) = 'real' THEN CAST(severity AS REAL) ELSE 0 END DESC
        LIMIT 10
    """).fetchall()
    for r in rows:
        print(dict(r))
except Exception as e:
    print(f"Error querying McNeill: {e}")

# 2. Schema of contradiction_map
print("\n" + "=" * 80)
print("CONTRADICTION_MAP SCHEMA")
print("=" * 80)
cols = conn.execute("PRAGMA table_info(contradiction_map)").fetchall()
for c in cols:
    print(f"  {c['name']:30s} {c['type']:15s} nullable={c['notnull']==0}")

print(f"\nTotal rows: {conn.execute('SELECT COUNT(*) FROM contradiction_map').fetchone()[0]}")

# Sample Watson contradictions
print("\n--- Watson contradiction samples (top 10) ---")
try:
    rows = conn.execute("""
        SELECT * FROM contradiction_map 
        WHERE entity LIKE '%Watson%' OR entity LIKE '%Emily%' OR actor LIKE '%Watson%' OR actor LIKE '%Emily%'
        LIMIT 10
    """).fetchall()
    if not rows:
        # Try broader search across all text columns
        all_cols = [c['name'] for c in cols]
        print(f"  No results with entity/actor. Columns: {all_cols}")
        rows = conn.execute("SELECT * FROM contradiction_map LIMIT 5").fetchall()
    for r in rows:
        print(dict(r))
except Exception as e:
    print(f"Error: {e}")
    rows = conn.execute("SELECT * FROM contradiction_map LIMIT 5").fetchall()
    for r in rows:
        print(dict(r))

# McNeill contradictions
print("\n--- McNeill contradiction samples (top 10) ---")
try:
    rows = conn.execute("""
        SELECT * FROM contradiction_map 
        WHERE entity LIKE '%McNeill%' OR entity LIKE '%judge%' OR actor LIKE '%McNeill%' OR actor LIKE '%judge%'
        LIMIT 10
    """).fetchall()
    if not rows:
        all_cols = [c['name'] for c in cols]
        print(f"  No results. Will search all columns.")
        # Search across all text columns
        conditions = " OR ".join(f"{c} LIKE '%McNeill%'" for c in all_cols if 'TEXT' in str(conn.execute(f"SELECT typeof({c}) FROM contradiction_map LIMIT 1").fetchone()[0]).upper() or True)
        rows = conn.execute(f"SELECT * FROM contradiction_map WHERE {conditions} LIMIT 5").fetchall()
    for r in rows:
        print(dict(r))
except Exception as e:
    print(f"Error: {e}")

# 3. Evidence quotes schema + counts by category
print("\n" + "=" * 80)
print("EVIDENCE_QUOTES SCHEMA")
print("=" * 80)
cols = conn.execute("PRAGMA table_info(evidence_quotes)").fetchall()
for c in cols:
    print(f"  {c['name']:30s} {c['type']:15s} nullable={c['notnull']==0}")

print(f"\nTotal rows: {conn.execute('SELECT COUNT(*) FROM evidence_quotes').fetchone()[0]}")

# Categories
print("\n--- Top 20 categories ---")
try:
    rows = conn.execute("""
        SELECT category, COUNT(*) as cnt FROM evidence_quotes 
        GROUP BY category ORDER BY cnt DESC LIMIT 20
    """).fetchall()
    for r in rows:
        print(f"  {r['category']:40s} {r['cnt']:>6d}")
except:
    pass

# 4. Check for judicial_violations table
print("\n" + "=" * 80)
print("JUDICIAL_VIOLATIONS SCHEMA")
print("=" * 80)
try:
    cols = conn.execute("PRAGMA table_info(judicial_violations)").fetchall()
    for c in cols:
        print(f"  {c['name']:30s} {c['type']:15s}")
    print(f"\nTotal rows: {conn.execute('SELECT COUNT(*) FROM judicial_violations').fetchone()[0]}")
    rows = conn.execute("SELECT * FROM judicial_violations LIMIT 3").fetchall()
    for r in rows:
        print(dict(r))
except Exception as e:
    print(f"Table error: {e}")

conn.close()
print("\n✅ Exploration complete")
