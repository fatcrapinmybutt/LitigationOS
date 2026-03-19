import sys, os, sqlite3
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

db = r"C:\Users\andre\LitigationOS\00_SYSTEM\manifests\drive_C_manifest.db"
conn = sqlite3.connect(db)
print("=== FILES TABLE SCHEMA ===")
for row in conn.execute("PRAGMA table_info(files)"):
    print(f"  {row}")
print("\n=== SAMPLE ROW ===")
for row in conn.execute("SELECT * FROM files LIMIT 1"):
    print(f"  {row}")
print("\n=== CONSOLIDATION_PLAN SCHEMA ===")
db2 = r"C:\Users\andre\LitigationOS\00_SYSTEM\manifests\consolidation_plan.db"
conn2 = sqlite3.connect(db2)
for t in ['dedup_groups','move_plan','trash_plan','stats']:
    print(f"\n--- {t} ---")
    for row in conn2.execute(f"PRAGMA table_info({t})"):
        print(f"  {row}")
    print("Sample:")
    for row in conn2.execute(f"SELECT * FROM {t} LIMIT 2"):
        print(f"  {row}")
conn.close()
conn2.close()
