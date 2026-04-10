#!/usr/bin/env python3
"""Check database schema."""

import sqlite3

conn = sqlite3.connect(r"C:\Users\andre\LitigationOS\00_SYSTEM\brains\shadyoaks_brain.db")
cursor = conn.cursor()

tables = ['evidence_registry', 'contradictions', 'legal_theories', 'timeline_events']

for table in tables:
    print(f"\n{'='*80}")
    print(f"TABLE: {table}")
    print(f"{'='*80}")
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    for col in columns:
        cid, name, type_, notnull, dflt_value, pk = col
        print(f"  {name:30} {type_:15} PK:{pk} NOT NULL:{notnull}")

conn.close()
