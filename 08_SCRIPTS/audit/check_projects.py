import sqlite3

db_path = r"C:\Users\andre\LitigationOS\00_SYSTEM\manifests\drive_C_manifest.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get projects table schema
cursor.execute("PRAGMA table_info(projects)")
schema = cursor.fetchall()
print("PROJECTS TABLE SCHEMA:")
for col in schema:
    print(f"  {col}")

# Get sample data
cursor.execute("SELECT * FROM projects LIMIT 10")
rows = cursor.fetchall()
print("\nSAMPLE PROJECT DATA:")
for row in rows:
    print(row)

# Get count
cursor.execute("SELECT COUNT(*) FROM projects")
count = cursor.fetchone()[0]
print(f"\nTotal projects: {count}")

conn.close()
