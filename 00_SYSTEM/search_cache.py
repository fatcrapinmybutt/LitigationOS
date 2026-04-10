import sqlite3

db_path = r'G:\_CONVERGENCE_DUPES\cache_1773489732.sqlite'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = [row[0] for row in cursor.fetchall()]

print("CACHE DATABASE: cache_1773489732.sqlite")
print("="*70)
print(f"Total tables: {len(tables)}\n")

total_rows = 0
for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM '{table}';")
    count = cursor.fetchone()[0]
    total_rows += count
    print(f"{table}: {count:,} rows")

print(f"\nTOTAL ROWS ACROSS ALL TABLES: {total_rows:,}")

# Now look for specific aggregate values or patterns
print("\n" + "="*70)
print("LOOKING FOR TARGET NUMBERS IN DATA...")
print("="*70)

# Check all numeric values in all tables
target_nums = [76329, 82250, 305, 24, 76.329, 82.250, 82250.00]

for table in tables:
    cursor.execute(f"PRAGMA table_info('{table}');")
    columns = [row[1] for row in cursor.fetchall()]
    
    for col in columns:
        # Try to find any of our target numbers
        for target in target_nums:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM '{table}' WHERE '{col}' = ?;", (target,))
                count = cursor.fetchone()[0]
                if count > 0:
                    print(f"MATCH: {table}.{col} has {count} row(s) with value {target}")
                    cursor.execute(f"SELECT '{col}' FROM '{table}' WHERE '{col}' = ? LIMIT 5;", (target,))
                    for row in cursor.fetchall():
                        print(f"  -> {row[0]}")
            except:
                pass

conn.close()
