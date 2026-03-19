import sqlite3
import sys

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

print("=" * 70)
print("MCR_RULES.DB AUDIT")
print("=" * 70)

try:
    c = sqlite3.connect('mcr_rules.db')
    c.execute('PRAGMA busy_timeout=60000')
    tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print(f'\nTables found: {len(tables)}')
    print(f'Table names: {tables}\n')
    
    for t in tables:
        cnt = c.execute(f'SELECT COUNT(*) FROM [{t}]').fetchone()[0]
        print(f'{t}: {cnt} rows')
        cols = [r[1] for r in c.execute(f'PRAGMA table_info([{t}])').fetchall()]
        print(f'  Columns: {cols}')
    
    c.close()
    print("\n✓ mcr_rules.db: ACCESSIBLE")
except Exception as e:
    print(f"\n✗ mcr_rules.db ERROR: {e}")

print("\n" + "=" * 70)
print("LITIGATION_CONTEXT.DB AUDIT (MCL AUTHORITY)")
print("=" * 70)

try:
    c = sqlite3.connect('litigation_context.db')
    c.execute('PRAGMA busy_timeout=60000')
    c.execute('PRAGMA cache_size=-32000')
    
    # Check MCL tables
    for t in ['mcl_authority_library', 'mcr_encyclopedia', 'mcr_encyclopedia_fts']:
        try:
            cnt = c.execute(f'SELECT COUNT(*) FROM [{t}]').fetchone()[0]
            print(f'{t}: {cnt} rows')
        except Exception as e:
            print(f'{t}: ERROR - {e}')
    
    # Check key MCL entries
    try:
        rows = c.execute('SELECT mcl_number, title FROM mcl_authority_library WHERE mcl_number LIKE "722%" LIMIT 10').fetchall()
        print(f'\nMCL 722.x entries: {len(rows)}')
        for r in rows[:5]:
            print(f'  {r[0]}: {r[1][:60]}')
    except Exception as e:
        print(f'\nMCL 722 query error: {e}')
    
    # Check MCR entries
    try:
        rows = c.execute('SELECT COUNT(*) FROM mcl_authority_library WHERE mcl_number LIKE "MCR%" OR title LIKE "%Court Rule%"').fetchone()[0]
        print(f'\nMCR entries in library: {rows}')
    except Exception as e:
        print(f'MCR count error: {e}')
    
    c.close()
    print("\n✓ litigation_context.db: ACCESSIBLE")
except Exception as e:
    print(f"\n✗ litigation_context.db ERROR: {e}")
