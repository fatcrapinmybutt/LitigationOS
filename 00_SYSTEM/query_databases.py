#!/usr/bin/env python
"""Query LitigationOS databases and evolution_log.json"""
import sqlite3
import json
import os
import sys

# Set UTF8 encoding
os.environ['PYTHONUTF8'] = '1'

# Change to correct directory
os.chdir(r'C:\Users\andre\LitigationOS\00_SYSTEM')

print("=" * 80)
print("LITIGATIONOS DATABASE DIAGNOSTIC QUERIES")
print("=" * 80)
print()

# ===== DATABASE 1: master_index.db =====
print("\n" + "=" * 80)
print("1. MASTER_INDEX.DB - C:\\Users\\andre\\LitigationOS\\00_SYSTEM\\pipeline\\agents\\master_index.db")
print("=" * 80)

db1_path = r'C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\agents\master_index.db'

try:
    conn = sqlite3.connect(db1_path, timeout=60)
    conn.execute('PRAGMA busy_timeout = 60000')
    conn.execute('PRAGMA journal_mode = WAL')
    c = conn.cursor()
    
    # List all tables
    print("\n--- TABLES IN DATABASE ---")
    c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = c.fetchall()
    print(f"Total tables: {len(tables)}")
    for (table_name,) in tables:
        print(f"  - {table_name}")
    
    # Check agent_log table
    if any(t[0] == 'agent_log' for t in tables):
        print("\n--- AGENT_LOG TABLE ---")
        c.execute("SELECT COUNT(*) FROM agent_log")
        count = c.fetchone()[0]
        print(f"Row count: {count}")
        
        print("\nGroup by action:")
        c.execute("SELECT action, COUNT(*) as cnt FROM agent_log GROUP BY action ORDER BY cnt DESC")
        for action, cnt in c.fetchall():
            print(f"  {action}: {cnt}")
        
        print("\nGroup by agent_id:")
        c.execute("SELECT agent_id, COUNT(*) as cnt FROM agent_log GROUP BY agent_id ORDER BY cnt DESC LIMIT 10")
        for agent_id, cnt in c.fetchall():
            print(f"  {agent_id}: {cnt}")
        
        print("\nGroup by level:")
        c.execute("SELECT level, COUNT(*) as cnt FROM agent_log GROUP BY level ORDER BY cnt DESC")
        for level, cnt in c.fetchall():
            print(f"  {level}: {cnt}")
        
        print("\nFirst 10 FATAL/CRASH entries:")
        c.execute("SELECT * FROM agent_log WHERE level IN ('FATAL', 'CRASH') LIMIT 10")
        rows = c.fetchall()
        if rows:
            for row in rows:
                print(f"  {row}")
        else:
            print("  (No FATAL/CRASH entries)")
    
    # Check ready_queue table
    if any(t[0] == 'ready_queue' for t in tables):
        print("\n--- READY_QUEUE TABLE ---")
        c.execute("SELECT status, COUNT(*) as cnt FROM ready_queue GROUP BY status ORDER BY cnt DESC")
        for status, cnt in c.fetchall():
            print(f"  {status}: {cnt}")
    
    # Check files table
    if any(t[0] == 'files' for t in tables):
        print("\n--- FILES TABLE ---")
        c.execute("SELECT COUNT(*) FROM files")
        count = c.fetchone()[0]
        print(f"Total files: {count}")
        
        print("\nGroup by category:")
        c.execute("SELECT category, COUNT(*) as cnt FROM files GROUP BY category ORDER BY cnt DESC LIMIT 10")
        for category, cnt in c.fetchall():
            print(f"  {category}: {cnt}")
    
    conn.close()
    print("\n✓ master_index.db queries completed")
    
except Exception as e:
    print(f"\n✗ Error querying master_index.db: {e}")
    import traceback
    traceback.print_exc()

# ===== JSON FILE: evolution_log.json =====
print("\n" + "=" * 80)
print("2. EVOLUTION_LOG.JSON - C:\\Users\\andre\\LitigationOS\\00_SYSTEM\\local_model\\evolution_log.json")
print("=" * 80)

json_path = r'C:\Users\andre\LitigationOS\00_SYSTEM\local_model\evolution_log.json'

try:
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n--- JSON STRUCTURE ---")
    print(f"Type: {type(data)}")
    if isinstance(data, list):
        print(f"Total entries: {len(data)}")
        if data:
            print(f"\nFirst entry keys: {list(data[0].keys())}")
            print(f"First entry cycle: {data[0].get('cycle')}")
            print(f"First entry timestamp: {data[0].get('timestamp')}")
            
            print(f"\n--- LAST ENTRY ---")
            last = data[-1]
            print(f"Cycle: {last.get('cycle')}")
            print(f"Timestamp: {last.get('timestamp')}")
            print(f"Keys: {list(last.keys())}")
            if 'phases' in last:
                print(f"Phases: {list(last['phases'].keys())}")
                for phase, details in last['phases'].items():
                    print(f"  {phase}: {details}")
    elif isinstance(data, dict):
        print(f"\nTop-level keys: {list(data.keys())}")
    
    print("\n✓ evolution_log.json read successfully")
    
except Exception as e:
    print(f"\n✗ Error reading evolution_log.json: {e}")
    import traceback
    traceback.print_exc()

# ===== DATABASE 2: litigation_context.db =====
print("\n" + "=" * 80)
print("3. LITIGATION_CONTEXT.DB - C:\\Users\\andre\\LitigationOS\\litigation_context.db")
print("=" * 80)

db2_path = r'C:\Users\andre\LitigationOS\litigation_context.db'

try:
    conn = sqlite3.connect(db2_path, timeout=60)
    conn.execute('PRAGMA busy_timeout = 60000')
    c = conn.cursor()
    
    # List all tables
    print("\n--- TABLES IN DATABASE ---")
    c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = c.fetchall()
    print(f"Total tables: {len(tables)}")
    for (table_name,) in tables:
        print(f"  - {table_name}")
    
    # Check memory_store table
    if any(t[0] == 'memory_store' for t in tables):
        print("\n--- MEMORY_STORE TABLE ---")
        c.execute("SELECT memory_type, COUNT(*) as cnt FROM memory_store GROUP BY memory_type ORDER BY cnt DESC")
        for memory_type, cnt in c.fetchall():
            print(f"  {memory_type}: {cnt}")
    
    # Check engine_metrics table
    if any(t[0] == 'engine_metrics' for t in tables):
        print("\n--- ENGINE_METRICS TABLE ---")
        c.execute("SELECT COUNT(*) FROM engine_metrics")
        count = c.fetchone()[0]
        print(f"Total rows: {count}")
        
        print("\nRecent 5 entries:")
        c.execute("SELECT * FROM engine_metrics ORDER BY rowid DESC LIMIT 5")
        rows = c.fetchall()
        for row in rows:
            print(f"  {row}")
    
    conn.close()
    print("\n✓ litigation_context.db queries completed")
    
except Exception as e:
    print(f"\n✗ Error querying litigation_context.db: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("ALL QUERIES COMPLETED")
print("=" * 80)
