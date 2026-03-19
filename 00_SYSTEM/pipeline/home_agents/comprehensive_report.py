import sqlite3
import json

db_path = r"C:\Users\andre\LitigationOS\00_SYSTEM\manifests\drive_H_manifest.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("\n" + "="*90)
print("COMPREHENSIVE DEEP FORENSIC SCAN REPORT - H: DRIVE")
print("="*90)

# Get summary
cursor.execute("SELECT * FROM summary")
summary_rows = cursor.fetchall()
summary = {}
for key, value in summary_rows:
    summary[key] = value

print("\n📊 SCAN SUMMARY")
print("─" * 90)
print(f"  Drive: {summary.get('drive', 'N/A').strip('\"')}")
print(f"  Scan Time: {summary.get('scan_time', 'N/A').strip('\"')}")
print(f"  Total Duration: {summary.get('elapsed_seconds', 'N/A')} seconds (~11.5 minutes)")
print(f"  Total Files: {summary.get('total_files', 'N/A')}")
print(f"  Total Directories: {summary.get('total_dirs', 'N/A')}")
print(f"  Scan Errors: {summary.get('scan_errors', 'N/A')}")

# Parse categories
try:
    categories_str = summary.get('categories', '{}').strip('\"')
    categories = json.loads(categories_str)
    print(f"\n📁 FILE CATEGORIES BREAKDOWN")
    print("─" * 90)
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat:25} : {count:6} files")
except:
    pass

# Legal files analysis
print(f"\n⚖️  LEGAL FILES ANALYSIS")
print("─" * 90)
cursor.execute("""
    SELECT COUNT(*) as count, 
           AVG(legal_score) as avg_score,
           MAX(legal_score) as max_score
    FROM files 
    WHERE legal_score > 0
""")
legal_stats = cursor.fetchone()
print(f"  Files with Legal Signals: {legal_stats[0]}")
avg_score = legal_stats[1] if legal_stats[1] else 0
max_score = legal_stats[2] if legal_stats[2] else 0
print(f"  Average Legal Score: {avg_score:.1f}")
print(f"  Maximum Legal Score: {max_score}")

# Top legal files
print(f"\n  Top 20 Legal Files (by score):")
print("  " + "─" * 86)
cursor.execute("""
    SELECT filename, legal_score, category, size_bytes 
    FROM files 
    WHERE legal_score > 0 
    ORDER BY legal_score DESC 
    LIMIT 20
""")
for i, (filename, score, category, size) in enumerate(cursor.fetchall(), 1):
    size_kb = size / 1024
    print(f"    {i:2}. [{score:2.0f}pts] {filename[:50]:50} ({size_kb:8.0f}KB) [{category}]")

# Duplicates analysis
print(f"\n🔄 DUPLICATES ANALYSIS")
print("─" * 90)
cursor.execute("""
    SELECT COUNT(DISTINCT sha256_1mb) as unique_hashes,
           COUNT(*) - COUNT(DISTINCT sha256_1mb) as duplicate_count
    FROM files 
    WHERE sha256_1mb IS NOT NULL
""")
unique, duplicates = cursor.fetchone()
total_hashed = unique + (duplicates if duplicates else 0)
print(f"  Files with Hash: {total_hashed}")
print(f"  Unique Hashes: {unique}")
print(f"  Duplicate Instances: {duplicates if duplicates else 0}")

# Archive files
print(f"\n📦 ARCHIVE FILES")
print("─" * 90)
cursor.execute("""
    SELECT COUNT(*) as count, SUM(size_bytes) as total_size
    FROM files 
    WHERE category = 'archive'
""")
arch_count, arch_size = cursor.fetchone()
print(f"  Archive Files: {arch_count}")
print(f"  Total Archive Size: {arch_size/1024/1024/1024:.2f} GB" if arch_size else "  Total Size: 0 MB")

cursor.execute("""
    SELECT filename, size_bytes 
    FROM files 
    WHERE category = 'archive'
    ORDER BY size_bytes DESC
    LIMIT 10
""")
print(f"\n  Top 10 Largest Archives:")
print("  " + "─" * 86)
for i, (filename, size) in enumerate(cursor.fetchall(), 1):
    print(f"    {i:2}. {filename[:60]:60} {size/1024/1024:8.1f} MB")

# Trash/temp files
print(f"\n🗑️  TRASH & TEMPORARY FILES")
print("─" * 90)
cursor.execute("""
    SELECT COUNT(*) as count, SUM(size_bytes) as total_size
    FROM files 
    WHERE is_trash = 1 OR is_empty = 1
""")
trash_count, trash_size = cursor.fetchone()
print(f"  Trash/Empty Files: {trash_count}")
print(f"  Total Size: {trash_size/1024/1024:.2f} MB" if trash_size else "  Total Size: 0 MB")

# Source code
print(f"\n💻 SOURCE CODE FILES")
print("─" * 90)
cursor.execute("""
    SELECT COUNT(*) as count, SUM(size_bytes) as total_size
    FROM files 
    WHERE category = 'source_code'
""")
code_count, code_size = cursor.fetchone()
print(f"  Source Code Files: {code_count}")
print(f"  Total Size: {code_size/1024/1024:.2f} MB" if code_size else "  Total Size: 0 MB")

# Projects detected
print(f"\n🚀 PROJECTS DETECTED")
print("─" * 90)
cursor.execute("""
    SELECT COUNT(*) as count,
           SUM(CASE WHEN project_type = 'python_package' THEN 1 ELSE 0 END) as python_count,
           SUM(CASE WHEN project_type = 'node_app' THEN 1 ELSE 0 END) as node_count,
           SUM(CASE WHEN project_type = 'database_dir' THEN 1 ELSE 0 END) as db_count,
           SUM(CASE WHEN project_type = 'litigationos_pipeline' THEN 1 ELSE 0 END) as litos_count
    FROM projects
""")
total_proj, py, node, db, litos = cursor.fetchone()
print(f"  Total Projects: {total_proj}")
print(f"    - Python Packages: {py if py else 0}")
print(f"    - Node Applications: {node if node else 0}")
print(f"    - Database Directories: {db if db else 0}")
print(f"    - LitigationOS Pipelines: {litos if litos else 0}")

print(f"\n  Top 15 Projects (by size):")
print("  " + "─" * 86)
cursor.execute("""
    SELECT root_path, project_type, file_count, total_size_bytes 
    FROM projects 
    ORDER BY total_size_bytes DESC 
    LIMIT 15
""")
for i, (path, ptype, fcount, size) in enumerate(cursor.fetchall(), 1):
    path_display = path[-50:] if len(path) > 50 else path
    print(f"    {i:2}. [{ptype:20}] {path_display:50} {size/1024/1024:8.1f}MB ({fcount} files)")

# Document summary
print(f"\n📄 DOCUMENT SUMMARY")
print("─" * 90)
cursor.execute("""
    SELECT category, COUNT(*) as count, SUM(size_bytes) as total_size
    FROM files
    WHERE category IN ('document_pdf', 'document_office', 'text', 'config')
    GROUP BY category
    ORDER BY count DESC
""")
for cat, count, size in cursor.fetchall():
    print(f"  {cat:20}: {count:6} files, {size/1024/1024:8.1f} MB")

conn.close()

print("\n" + "="*90)
print("END OF COMPREHENSIVE SCAN REPORT")
print("="*90 + "\n")
