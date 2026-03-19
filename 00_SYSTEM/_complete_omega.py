"""Complete the OMEGA scan: populate duplicates + summary tables.
Dedup by normalized_name + size_bytes (NO hashing)."""
import sqlite3, sys, time
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

db = r"C:\Users\andre\LitigationOS\00_SYSTEM\manifests\omega_C_manifest.db"
c = sqlite3.connect(db)
c.execute("PRAGMA journal_mode=WAL")
c.execute("PRAGMA synchronous=NORMAL")

print("=== PHASE: DEDUP (normalized_name + size_bytes) ===")
t0 = time.time()

# Clear old data
c.execute("DELETE FROM duplicates")
c.execute("DELETE FROM summary")

# Find duplicates: same normalized_name + size, different paths
# Only non-empty files with actual names
c.execute("""
    INSERT INTO duplicates (normalized_name, extension, size_bytes, copy_count, file_paths, total_waste)
    SELECT 
        normalized_name,
        extension,
        size_bytes,
        COUNT(*) as copy_count,
        GROUP_CONCAT(path, '|||') as file_paths,
        (COUNT(*) - 1) * size_bytes as total_waste
    FROM files
    WHERE normalized_name != '' 
      AND size_bytes > 0
      AND is_empty = 0
    GROUP BY normalized_name, size_bytes
    HAVING COUNT(*) > 1
    ORDER BY total_waste DESC
""")
dup_count = c.execute("SELECT COUNT(*) FROM duplicates").fetchone()[0]
dup_waste = c.execute("SELECT SUM(total_waste) FROM duplicates").fetchone()[0] or 0
print(f"  Duplicate groups: {dup_count}")
print(f"  Wasted space: {dup_waste/1024/1024:.1f} MB")

# Also find same-name different-size (possible versions)
print(f"\n  Time: {time.time()-t0:.1f}s")

print("\n=== PHASE: SUMMARY ===")
# Populate summary table
c.execute("""
    INSERT INTO summary (key, value) VALUES
    ('total_files', (SELECT COUNT(*) FROM files)),
    ('total_dirs', (SELECT COUNT(*) FROM directories)),
    ('total_size_bytes', (SELECT SUM(size_bytes) FROM files)),
    ('empty_files', (SELECT COUNT(*) FROM files WHERE is_empty=1)),
    ('duplicate_groups', (SELECT COUNT(*) FROM duplicates)),
    ('duplicate_waste_bytes', CAST(? AS TEXT)),
    ('legal_high_score_files', (SELECT COUNT(*) FROM files WHERE legal_score >= 5)),
    ('legal_any_score_files', (SELECT COUNT(*) FROM files WHERE legal_score >= 1)),
    ('scan_completed', datetime('now'))
""", (int(dup_waste),))

c.commit()

# Print summary
print("\n=== FINAL SUMMARY ===")
for r in c.execute("SELECT key, value FROM summary").fetchall():
    print(f"  {r[0]}: {r[1]}")

# Top 20 biggest duplicate groups
print("\n=== TOP 20 DUPLICATE GROUPS (by waste) ===")
for r in c.execute("""
    SELECT normalized_name, copy_count, size_bytes, total_waste
    FROM duplicates 
    ORDER BY total_waste DESC 
    LIMIT 20
""").fetchall():
    waste_mb = r[3] / 1024 / 1024
    print(f"  [{r[1]}x] {r[0]} — {waste_mb:.1f} MB waste")

# Top folders with most duplicates
print("\n=== FOLDERS WITH MOST DUPLICATES ===")
rows = c.execute("""
    SELECT f.top_folder, COUNT(*) as dup_files
    FROM files f
    JOIN duplicates d ON f.normalized_name = d.normalized_name AND f.size_bytes = d.size_bytes
    WHERE f.top_folder != ''
    GROUP BY f.top_folder
    ORDER BY dup_files DESC
    LIMIT 15
""").fetchall()
for r in rows:
    print(f"  {r[0]}: {r[1]} duplicate files")

c.close()
print(f"\nTotal time: {time.time()-t0:.1f}s")
print("Done.")
