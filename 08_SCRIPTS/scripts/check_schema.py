import sqlite3, sys, os
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
db = sqlite3.connect(r'C:\Users\andre\LitigationOS\litigation_context.db', timeout=30)
db.execute('PRAGMA journal_mode=WAL')

# Check if proposed tables already exist
for t in ['drive_files', 'file_atoms', 'provenance_refs', 'ingest_logs', 'gap_tickets', 'vehicles', 'authority_chains']:
    r = db.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone()
    print(f"{t}: {'EXISTS' if r[0] else 'MISSING'}")

# Check existing phase-related tables
r = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%drive%' OR name LIKE '%atom%' OR name LIKE '%provenance%' ORDER BY name").fetchall()
print(f"\nDrive/atom/provenance tables: {[x[0] for x in r]}")

# Check gap_tickets schema if exists
try:
    cols = db.execute("PRAGMA table_info(gap_tickets)").fetchall()
    print(f"\ngap_tickets columns: {[(c[1],c[2]) for c in cols]}")
except:
    print("\ngap_tickets: not found")

# Check vehicles schema
try:
    cols = db.execute("PRAGMA table_info(vehicles)").fetchall()
    print(f"\nvehicles columns: {[(c[1],c[2]) for c in cols]}")
except:
    print("\nvehicles: not found")

db.close()
