"""Quick checkpoint status using read-only WAL snapshot."""
import json, sqlite3, os, sys

DB = r"C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\agents\master_index.db"
db = sqlite3.connect(DB, timeout=2)
db.execute("PRAGMA query_only = ON")
db.execute("PRAGMA busy_timeout = 2000")

try:
    r = lambda q: db.execute(q).fetchone()[0]
    print(f"Total: {r('SELECT COUNT(*) FROM files'):,}")
    print(f"Hashed: {r('SELECT COUNT(*) FROM files WHERE sha256 IS NOT NULL'):,}")
    print(f"Canonical: {r('SELECT COUNT(*) FROM files WHERE is_canonical=1'):,}")
    print(f"dest_path: {r('SELECT COUNT(*) FROM files WHERE dest_path IS NOT NULL'):,}")
    print(f"fact_atoms: {r('SELECT COUNT(*) FROM fact_atoms'):,}")
    print(f"citation_atoms: {r('SELECT COUNT(*) FROM citation_atoms'):,}")
    print(f"atoms: {r('SELECT COUNT(*) FROM atoms'):,}")
    print(f"judicial: {r('SELECT COUNT(*) FROM judicial_findings'):,}")
    q = "SELECT COUNT(*) FROM files WHERE extension='.pdf' AND processed=1"
    print(f"PDFs processed: {r(q):,}")
    
    for ct in db.execute("SELECT citation_type, COUNT(*) as c FROM citation_atoms GROUP BY citation_type ORDER BY c DESC").fetchall():
        print(f"  cite_{ct[0]}: {ct[1]:,}")
    for l in ['A','B','C','UNCLASSIFIED']:
        c = db.execute("SELECT COUNT(*) FROM files WHERE meek_lane=?", (l,)).fetchone()[0]
        if c: print(f"  Lane_{l}: {c}")
except Exception as e:
    print(f"DB busy: {e}")
finally:
    db.close()

# Checkpoint files
CK = r"C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\agents\checkpoints"
for f in sorted(os.listdir(CK)):
    if f.endswith('.json'):
        try:
            d = json.load(open(os.path.join(CK, f)))
            print(f"  {f}: {d.get('processed',0)}/{d.get('total','?')} skip={d.get('skipped',0)} err={d.get('errored',0)}")
        except:
            pass
