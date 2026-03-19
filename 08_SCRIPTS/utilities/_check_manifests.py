import sys, os, sqlite3
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

manifest_dir = r"C:\Users\andre\LitigationOS\00_SYSTEM\manifests"
for db_file in sorted(os.listdir(manifest_dir)):
    if not db_file.endswith('.db'):
        continue
    db_path = os.path.join(manifest_dir, db_file)
    try:
        conn = sqlite3.connect(db_path)
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        row_counts = {}
        for t in tables:
            try:
                cnt = conn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
                row_counts[t] = cnt
            except:
                row_counts[t] = -1
        conn.close()
        total = sum(v for v in row_counts.values() if v > 0)
        print(f"\n{db_file} ({os.path.getsize(db_path)/1024/1024:.1f} MB)")
        print(f"  Tables: {', '.join(tables)}")
        for t, c in sorted(row_counts.items(), key=lambda x: -x[1]):
            print(f"  {t}: {c:,} rows")
    except Exception as e:
        print(f"\n{db_file}: ERROR - {e}")
