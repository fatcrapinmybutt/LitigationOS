#!/usr/bin/env python3
"""Prune empty tables from litigation_context.db, preserving FTS5 shadow tables and protected tables."""
import sys
import sqlite3
import os
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'litigation_context.db')

# FTS5 shadow table suffixes
FTS_SUFFIXES = ('_fts', '_content', '_docsize', '_config', '_data', '_idx')

# Protected table names (never drop)
PROTECTED_NAMES = {'todo_deps'}

def is_fts_shadow_table(name, all_tables):
    """Check if a table is an FTS5 shadow table of any existing table."""
    lower = name.lower()
    # Direct suffix match
    for suffix in FTS_SUFFIXES:
        if lower.endswith(suffix):
            return True
    # Check if it's a shadow of a known FTS5 virtual table pattern:
    # FTS5 creates: base_content, base_docsize, base_config, base_data, base_idx
    for suffix in ('_content', '_docsize', '_config', '_data', '_idx'):
        if lower.endswith(suffix):
            base = lower[:-len(suffix)]
            if base in all_tables or f"{base}_fts" in all_tables:
                return True
    return False

def has_log_in_name(name):
    return 'log' in name.lower()

def main():
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Starting empty table prune...")
    print(f"Database: {os.path.abspath(DB)}")

    conn = sqlite3.connect(DB, timeout=120)
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    cur = conn.cursor()

    # Get all tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    all_tables = [r[0] for r in cur.fetchall()]
    all_tables_lower = {t.lower() for t in all_tables}
    total_tables = len(all_tables)
    print(f"Total tables found: {total_tables}")

    # Categorize tables
    empty_tables = []
    nonempty_tables = []
    for t in all_tables:
        try:
            cur.execute(f'SELECT COUNT(*) FROM "{t}"')
            count = cur.fetchone()[0]
        except Exception as e:
            print(f"  WARN: Could not count rows in '{t}': {e}")
            continue
        if count == 0:
            empty_tables.append(t)
        else:
            nonempty_tables.append(t)

    print(f"Non-empty tables: {len(nonempty_tables)}")
    print(f"Empty tables: {len(empty_tables)}")

    # Determine which empty tables to drop
    drop_list = []
    excluded = []
    for t in empty_tables:
        reason = None
        if t in PROTECTED_NAMES:
            reason = "protected name"
        elif is_fts_shadow_table(t, all_tables_lower):
            reason = "FTS5 shadow table"
        elif has_log_in_name(t):
            reason = "log table"
        
        if reason:
            excluded.append((t, reason))
        else:
            drop_list.append(t)

    # Backup: write full table list before dropping
    backup_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_table_backup_before_prune.txt')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(f"# Table backup before prune — {datetime.now():%Y-%m-%d %H:%M:%S}\n")
        f.write(f"# Total tables: {total_tables}\n\n")
        f.write("## ALL TABLES:\n")
        for t in all_tables:
            f.write(f"  {t}\n")
        f.write(f"\n## TABLES TO DROP ({len(drop_list)}):\n")
        for t in drop_list:
            try:
                cur.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (t,))
                sql = cur.fetchone()
                f.write(f"  {t}\n    CREATE: {sql[0] if sql else 'N/A'}\n")
            except:
                f.write(f"  {t}\n    CREATE: N/A\n")
        f.write(f"\n## EXCLUDED FROM DROP ({len(excluded)}):\n")
        for t, reason in excluded:
            f.write(f"  {t} — {reason}\n")
    print(f"\nBackup written to: {backup_path}")

    # Print exclusions
    print(f"\n--- EXCLUDED ({len(excluded)}) ---")
    for t, reason in excluded:
        print(f"  SKIP: {t} — {reason}")

    # Print and execute drops
    print(f"\n--- DROPPING {len(drop_list)} EMPTY TABLES ---")
    dropped = 0
    errors = 0
    for t in drop_list:
        try:
            cur.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (t,))
            row = cur.fetchone()
            create_sql = row[0] if row else 'N/A'
            print(f"  DROP: {t}")
            cur.execute(f'DROP TABLE IF EXISTS "{t}"')
            dropped += 1
        except Exception as e:
            print(f"  ERROR dropping '{t}': {e}")
            errors += 1

    conn.commit()

    # Verify final count
    cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
    remaining = cur.fetchone()[0]
    conn.close()

    print(f"\n{'='*60}")
    print(f"Dropped {dropped} empty tables. Errors: {errors}")
    print(f"Remaining: {remaining} tables")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
