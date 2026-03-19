import sqlite3

db_path = r"C:\Users\andre\LitigationOS\00_SYSTEM\brains\cross_brain_index.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get the FTS5 table definition
cursor.execute("SELECT sql FROM sqlite_master WHERE name='universal_search'")
result = cursor.fetchone()
if result:
    print("FTS5 Table Definition:")
    print(result[0])
else:
    print("No definition found")

conn.close()
