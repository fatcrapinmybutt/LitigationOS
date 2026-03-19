#!/usr/bin/env python3
"""Verify key database facts that filings reference."""
import sys, sqlite3, os
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

db = sqlite3.connect(r'C:\Users\andre\LitigationOS\litigation_context.db')
db.execute('PRAGMA busy_timeout=60000')
db.execute('PRAGMA journal_mode=WAL')
db.execute('PRAGMA cache_size=-32000')

print('=== VERIFIABLE FACTS FROM DATABASE ===\n')

# Core counts
queries = {
    'judicial_violations': 'SELECT COUNT(*) FROM judicial_violations',
    'claims': 'SELECT COUNT(*) FROM claims',
    'evidence_quotes': 'SELECT COUNT(*) FROM evidence_quotes',
    'watson_perjury_compilation': 'SELECT COUNT(*) FROM watson_perjury_compilation',
    'conspiracy_timeline': 'SELECT COUNT(*) FROM conspiracy_timeline',
    'citation_validation': 'SELECT COUNT(*) FROM citation_validation',
    'adversary_assertions': 'SELECT COUNT(*) FROM adversary_assertions',
    'actor_violations': 'SELECT COUNT(*) FROM actor_violations',
    'watson_family_conspiracy': 'SELECT COUNT(*) FROM watson_family_conspiracy',
    'berry_ethics_violations': 'SELECT COUNT(*) FROM berry_ethics_violations',
}

for name, q in queries.items():
    try:
        row = db.execute(q).fetchone()
        print(f'  {name}: {row[0]:,}')
    except Exception as e:
        print(f'  {name}: ERROR - {e}')

# Ex-parte orders check
print('\n=== EX-PARTE ORDERS SEARCH ===')
search_tables = ['docket_events', 'judicial_violations', 'evidence_quotes']
for tbl in search_tables:
    try:
        cols = [r[1] for r in db.execute(f'PRAGMA table_info({tbl})').fetchall()]
        text_cols = [c for c in cols if any(kw in c.lower() for kw in ['desc', 'text', 'content', 'quote', 'summary', 'event', 'detail', 'violation', 'type'])]
        if text_cols:
            for col in text_cols[:2]:
                try:
                    rows = db.execute(f"SELECT COUNT(*) FROM {tbl} WHERE {col} LIKE '%ex parte%' OR {col} LIKE '%ex-parte%'").fetchone()
                    if rows[0] > 0:
                        print(f'  {tbl}.{col}: {rows[0]} rows mention ex-parte')
                        samples = db.execute(f"SELECT {col} FROM {tbl} WHERE {col} LIKE '%ex parte%' OR {col} LIKE '%ex-parte%' LIMIT 3").fetchall()
                        for s in samples:
                            text = str(s[0])[:150]
                            print(f'    → {text}')
                except:
                    pass
    except Exception as e:
        print(f'  {tbl}: {e}')

# Actor violations breakdown
print('\n=== ACTOR VIOLATIONS BREAKDOWN ===')
try:
    cols = [r[1] for r in db.execute('PRAGMA table_info(actor_violations)').fetchall()]
    actor_col = [c for c in cols if 'actor' in c.lower() or 'name' in c.lower() or 'party' in c.lower()]
    if actor_col:
        rows = db.execute(f"SELECT {actor_col[0]}, COUNT(*) as cnt FROM actor_violations GROUP BY {actor_col[0]} ORDER BY cnt DESC LIMIT 10").fetchall()
        for r in rows:
            print(f'  {r[0]}: {r[1]}')
    else:
        print(f'  Columns: {cols}')
except Exception as e:
    print(f'  ERROR: {e}')

# Key dates verification
print('\n=== KEY DATES SEARCH ===')
try:
    # Search for May 2024 and August 2025 ex-parte dates
    for date_pattern in ['2024-05', '2025-08', 'May 2024', 'August 2025', 'Aug 2025']:
        count = db.execute(f"SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%{date_pattern}%'").fetchone()
        if count[0] > 0:
            print(f'  evidence_quotes mentioning "{date_pattern}": {count[0]}')
except Exception as e:
    print(f'  Date search error: {e}')

db.close()
print('\n=== DONE ===')
