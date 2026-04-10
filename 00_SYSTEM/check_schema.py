import sqlite3
conn = sqlite3.connect(r'D:\LitigationOS_tmp\consolidation_state.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(file_inventory)")
for row in cursor.fetchall():
    print(row)
conn.close()
