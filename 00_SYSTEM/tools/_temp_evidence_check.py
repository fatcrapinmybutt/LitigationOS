import sqlite3

db_path = r'C:\Users\andre\LitigationOS\litigation_context.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if evidence table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='evidence'")
exists = cursor.fetchone()

if exists:
    print("TABLE: evidence")
    print("=" * 80)
    print("\nColumns:")
    print("-" * 80)
    cursor.execute("PRAGMA table_info(evidence)")
    columns = cursor.fetchall()
    for col_id, col_name, col_type, not_null, default_val, pk in columns:
        pk_marker = " [PK]" if pk else ""
        nn_marker = " [NOT NULL]" if not_null else ""
        print(f"  {col_id:2d}. {col_name:30s} {col_type:15s}{pk_marker}{nn_marker}")
        if default_val:
            print(f"      Default: {default_val}")
    
    cursor.execute("SELECT COUNT(*) FROM evidence")
    count = cursor.fetchone()[0]
    print(f"\nRow count: {count}")
else:
    print("evidence table NOT FOUND")

conn.close()
