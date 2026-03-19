"""Checkpoint status dump."""
import json, sqlite3

try:
    ck = json.load(open('agents/checkpoints/A10-PDF-HARVEST.checkpoint.json'))
    print(f"A10 checkpoint: {ck['processed']}/{ck['total']} skip:{ck.get('skipped',0)} err:{ck.get('errored',0)}")
except:
    print("A10: no checkpoint file yet")

db = sqlite3.connect('agents/master_index.db')

fa = db.execute('SELECT COUNT(*) FROM fact_atoms').fetchone()[0]
ca = db.execute('SELECT COUNT(*) FROM citation_atoms').fetchone()[0]
atoms = db.execute('SELECT COUNT(*) FROM atoms').fetchone()[0]
jf = db.execute('SELECT COUNT(*) FROM judicial_findings').fetchone()[0]
pp = db.execute("SELECT COUNT(*) FROM files WHERE extension='.pdf' AND processed=1").fetchone()[0]

for lane in ['A', 'B', 'C', 'UNCLASSIFIED']:
    cnt = db.execute('SELECT COUNT(*) FROM files WHERE meek_lane=?', (lane,)).fetchone()[0]
    print(f"Lane {lane}: {cnt} files")

print(f"\nPDFs processed: {pp}")
print(f"fact_atoms: {fa:,}")
print(f"citation_atoms: {ca:,}")
print(f"atoms (intel): {atoms:,}")
print(f"judicial_findings: {jf:,}")

total = db.execute('SELECT COUNT(*) FROM files').fetchone()[0]
hashed = db.execute('SELECT COUNT(*) FROM files WHERE sha256 IS NOT NULL').fetchone()[0]
can = db.execute('SELECT COUNT(*) FROM files WHERE is_canonical=1').fetchone()[0]
dp = db.execute('SELECT COUNT(*) FROM files WHERE dest_path IS NOT NULL').fetchone()[0]
acts = db.execute('SELECT COUNT(*) FROM action_scores').fetchone()[0]
rdy = db.execute('SELECT COUNT(*) FROM action_scores WHERE composite_score >= 70').fetchone()[0]
print(f"\nTotal: {total:,} Hashed: {hashed:,} Canonical: {can:,} dest_path: {dp:,}")
print(f"Actions: {acts} Ready-to-file: {rdy}")

# Top citation types
rows = db.execute("SELECT citation_type, COUNT(*) as c FROM citation_atoms GROUP BY citation_type ORDER BY c DESC").fetchall()
print("\nCitation atoms by type:")
for r in rows:
    print(f"  {r[0]}: {r[1]:,}")

# Lane-classified PDFs
for lane in ['A', 'B', 'C', 'UNCLASSIFIED']:
    cnt = db.execute("SELECT COUNT(*) FROM files WHERE extension='.pdf' AND meek_lane=?", (lane,)).fetchone()[0]
    print(f"PDF Lane {lane}: {cnt}")
