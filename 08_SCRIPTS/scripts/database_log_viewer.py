import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join("F:/FRED-PRIME", "database.db")

def connect_db():
    if not os.path.exists(DB_PATH):
        print("❌ FRED-PRIME database not found.")
        return None
    return sqlite3.connect(DB_PATH)

def show_logs():
    conn = connect_db()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, path, extension, created_at FROM files ORDER BY created_at DESC")
    rows = cursor.fetchall()
    print("\n=== FRED-PRIME FILE LOGS ===\n")
    for row in rows:
        print(f"[{row[0]}] {row[1]} ({row[3]})")
        print(f"     📁 {row[2]}")
        print(f"     🕒 {row[4]}")
        print("-" * 50)
    conn.close()

def search_by_type(file_ext):
    conn = connect_db()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, path, extension, created_at FROM files WHERE extension = ? ORDER BY created_at DESC", (file_ext,))
    rows = cursor.fetchall()
    print(f"\n=== FRED-PRIME FILES: {file_ext.upper()} ===\n")
    for row in rows:
        print(f"[{row[0]}] {row[1]} - {row[4]}")
    conn.close()

if __name__ == "__main__":
    print("FRED-PRIME Log Viewer")
    print("1. Show All Logs")
    print("2. Filter by Extension (e.g., .docx, .ps1, .html)")
    choice = input("Choose option: ")
    if choice == "1":
        show_logs()
    elif choice == "2":
        ext = input("Enter extension (include the dot, e.g., .docx): ")
        search_by_type(ext.strip())
    else:
        print("Invalid selection.")