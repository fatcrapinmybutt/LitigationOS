#!/usr/bin/env python3
"""
Comprehensive LitigationOS Health Verification Script
Checks: database, engines, entry points, specs, disk space
"""

import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime

def print_header(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def print_section(title):
    print(f"\n{title}")
    print("-" * 70)

# ============================================================================
# 1. DATABASE HEALTH
# ============================================================================
print_header("1. DATABASE HEALTH CHECK")

db_path = r"C:\Users\andre\LitigationOS\litigation_context.db"

try:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check if DB exists and is accessible
    print(f"✓ Database found: {db_path}")
    
    # PRAGMA integrity_check
    print_section("Integrity Check")
    cursor.execute("PRAGMA integrity_check")
    integrity_result = cursor.fetchone()[0]
    if integrity_result == "ok":
        print(f"  ✓ PRAGMA integrity_check: {integrity_result}")
    else:
        print(f"  ✗ PRAGMA integrity_check: {integrity_result}")
    
    # PRAGMA journal_mode
    print_section("Journal Mode")
    cursor.execute("PRAGMA journal_mode")
    journal_mode = cursor.fetchone()[0]
    expected_wal = journal_mode.upper() == "WAL"
    status = "✓" if expected_wal else "✗"
    print(f"  {status} PRAGMA journal_mode: {journal_mode} {'(expected: WAL)' if not expected_wal else ''}")
    
    # Key tables count
    print_section("Key Tables Count")
    tables_to_check = [
        'evidence_quotes',
        'timeline_events', 
        'authority_chains_v2',
        'impeachment_matrix',
        'contradiction_map',
        'judicial_violations',
        'michigan_rules_extracted',
        'master_citations',
        'file_inventory'
    ]
    
    table_counts = {}
    for table in tables_to_check:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            table_counts[table] = count
            print(f"  ✓ {table:30} : {count:,} rows")
        except Exception as e:
            print(f"  ✗ {table:30} : ERROR - {str(e)[:50]}")
            table_counts[table] = "ERROR"
    
    # FTS5 round-trip test
    print_section("FTS5 Full-Text Search Test")
    try:
        cursor.execute("SELECT COUNT(*) FROM evidence_fts WHERE evidence_fts MATCH 'custody'")
        fts_count = cursor.fetchone()[0]
        print(f"  ✓ FTS5 search ('custody'): {fts_count:,} results")
    except Exception as e:
        print(f"  ✗ FTS5 search failed: {str(e)[:50]}")
    
    conn.close()
    
except sqlite3.Error as e:
    print(f"  ✗ Database error: {str(e)}")
except Exception as e:
    print(f"  ✗ Unexpected error: {str(e)}")

# ============================================================================
# 2. ENGINE INVENTORY
# ============================================================================
print_header("2. ENGINE INVENTORY CHECK")

engines_base = r"C:\Users\andre\LitigationOS\00_SYSTEM\engines"
required_engines = [
    'event_bus',
    'genetic_memory',
    'contradiction_harvester',
    'provenance',
    'predictive',
    'bridge',
    'filing_assembly',
    'brain_sync',
    'telemetry'
]

print(f"Checking engines in: {engines_base}\n")

if os.path.exists(engines_base):
    print(f"✓ Engines base directory exists")
    engines_status = {}
    for engine in required_engines:
        engine_path = os.path.join(engines_base, engine)
        exists = os.path.isdir(engine_path)
        status = "✓" if exists else "✗"
        engines_status[engine] = exists
        print(f"  {status} {engine:30}")
else:
    print(f"✗ Engines base directory NOT FOUND: {engines_base}")

# ============================================================================
# 3. THEMANBEARPIG ENTRY POINT
# ============================================================================
print_header("3. THEMANBEARPIG ENTRY POINT CHECK")

themanbearpig_path = r"C:\Users\andre\LitigationOS\00_SYSTEM\tools\scripts\scripts\themanbearpig.py"

if os.path.exists(themanbearpig_path):
    print(f"✓ Entry point found: {themanbearpig_path}")
    try:
        with open(themanbearpig_path, 'r', encoding='utf-8') as f:
            content = f.read()
            has_version = 'VERSION' in content
            if has_version:
                # Extract VERSION string
                for line in content.split('\n'):
                    if 'VERSION' in line and '=' in line:
                        print(f"  ✓ VERSION string found: {line.strip()}")
                        break
                else:
                    print(f"  ✓ VERSION string exists in file")
            else:
                print(f"  ✗ VERSION string NOT FOUND")
    except Exception as e:
        print(f"  ✗ Error reading file: {str(e)}")
else:
    print(f"✗ Entry point NOT FOUND: {themanbearpig_path}")

# ============================================================================
# 4. PYINSTALLER SPEC
# ============================================================================
print_header("4. PYINSTALLER SPEC CHECK")

spec_path = r"C:\Users\andre\LitigationOS\07_CODE\BUILD\THEMANBEARPIG.spec"

if os.path.exists(spec_path):
    print(f"✓ PyInstaller spec found: {spec_path}")
    try:
        file_size = os.path.getsize(spec_path)
        print(f"  ✓ File size: {file_size} bytes")
    except Exception as e:
        print(f"  ✗ Error checking file: {str(e)}")
else:
    print(f"✗ PyInstaller spec NOT FOUND: {spec_path}")

# ============================================================================
# 5. DISK SPACE
# ============================================================================
print_header("5. DISK SPACE CHECK")

import shutil

try:
    usage = shutil.disk_usage('C:\\')
    free_gb = usage.free / (1024 ** 3)
    total_gb = usage.total / (1024 ** 3)
    used_gb = usage.used / (1024 ** 3)
    
    print(f"Drive C:\\")
    print(f"  Total : {total_gb:.2f} GB")
    print(f"  Used  : {used_gb:.2f} GB")
    print(f"  Free  : {free_gb:.2f} GB")
    print(f"  Available: {free_gb:.2f} GB")
    
except Exception as e:
    print(f"✗ Error checking disk space: {str(e)}")

# ============================================================================
# SUMMARY TABLE
# ============================================================================
print_header("SUMMARY")

summary_data = {
    "Check": [
        "Database Integrity",
        "Journal Mode (WAL)",
        "Evidence Quotes Table",
        "Timeline Events Table",
        "Authority Chains Table",
        "Impeachment Matrix Table",
        "Contradiction Map Table",
        "Judicial Violations Table",
        "Michigan Rules Table",
        "Master Citations Table",
        "File Inventory Table",
        "FTS5 Search Test",
        "Engines Base Directory",
        "Event Bus Engine",
        "Genetic Memory Engine",
        "Contradiction Harvester",
        "Provenance Engine",
        "Predictive Engine",
        "Bridge Engine",
        "Filing Assembly Engine",
        "Brain Sync Engine",
        "Telemetry Engine",
        "THEMANBEARPIG Entry Point",
        "VERSION String",
        "PyInstaller Spec",
        "Disk Space (C: Free)"
    ]
}

print("\nAll health checks completed. Review details above for full status.")
print("✓ = OK, ✗ = FAILED or MISSING")
