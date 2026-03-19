import sqlite3, sys
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

db = r"C:\Users\andre\LitigationOS\00_SYSTEM\manifests\omega_C_manifest.db"
c = sqlite3.connect(db)

print("=== TABLES ===")
for row in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
    print(f"  {row[0]}")

print("\n=== SCHEMA: files ===")
for row in c.execute("PRAGMA table_info(files)").fetchall():
    print(f"  {row[1]} ({row[2]})")

print("\n=== FILE COUNT ===")
print(f"  {c.execute('SELECT COUNT(*) FROM files').fetchone()[0]}")

print("\n=== SAMPLE ===")
cols = [d[0] for d in c.execute("SELECT * FROM files LIMIT 1").description]
print(f"  Columns: {cols}")
for r in c.execute("SELECT path, normalized_name, extension, size_bytes, magic_type, category, legal_score FROM files LIMIT 5").fetchall():
    print(f"  {r}")

print("\n=== EXTENSION DISTRIBUTION (top 20) ===")
for r in c.execute("SELECT extension, COUNT(*) as cnt FROM files GROUP BY extension ORDER BY cnt DESC LIMIT 20").fetchall():
    print(f"  {r[0]}: {r[1]}")

print("\n=== CATEGORY DISTRIBUTION ===")
for r in c.execute("SELECT category, COUNT(*) as cnt FROM files GROUP BY category ORDER BY cnt DESC LIMIT 20").fetchall():
    print(f"  {r[0]}: {r[1]}")

print("\n=== LEGAL SCORE DISTRIBUTION ===")
for r in c.execute("SELECT CASE WHEN legal_score >= 5 THEN 'HIGH (5+)' WHEN legal_score >= 2 THEN 'MED (2-4)' WHEN legal_score >= 1 THEN 'LOW (1)' ELSE 'NONE (0)' END as bucket, COUNT(*) FROM files GROUP BY bucket ORDER BY bucket").fetchall():
    print(f"  {r[0]}: {r[1]}")

print("\n=== MAGIC TYPE DISTRIBUTION (top 20) ===")
for r in c.execute("SELECT magic_type, COUNT(*) as cnt FROM files GROUP BY magic_type ORDER BY cnt DESC LIMIT 20").fetchall():
    print(f"  {r[0]}: {r[1]}")

c.close()
print("\nDone.")
