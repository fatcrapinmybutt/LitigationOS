import sqlite3
import os
import sys
from datetime import datetime

DB_PATH = os.path.join("F:/FRED-PRIME", "database.db")

def log_file_event(file_name, path, extension, event_type="launch", category=None, tag=None):
    if not os.path.exists(DB_PATH):
        print("❌ ERROR: FRED-PRIME database not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Add schema columns if missing
    try:
        cursor.execute("ALTER TABLE files ADD COLUMN event_type TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE files ADD COLUMN category TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE files ADD COLUMN tag TEXT")
    except sqlite3.OperationalError:
        pass

    cursor.execute("""
        INSERT INTO files (name, path, extension, event_type, category, tag)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (file_name, path, extension, event_type, category, tag))

    conn.commit()
    conn.close()
    print(f"✅ Logged: {file_name} ({event_type})")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python autolog_file_logger.py <name> <path> <extension> [event_type] [category] [tag]")
        sys.exit(1)

    file_name = sys.argv[1]
    path = sys.argv[2]
    extension = sys.argv[3]
    event_type = sys.argv[4] if len(sys.argv) > 4 else "launch"
    category = sys.argv[5] if len(sys.argv) > 5 else None
    tag = sys.argv[6] if len(sys.argv) > 6 else None

    log_file_event(file_name, path, extension, event_type, category, tag)