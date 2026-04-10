import sqlite3

db_path = r'C:\Users\andre\LitigationOS\mbp_brain.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print('=' * 80)
print('1. LIST ALL TABLES')
print('=' * 80)
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
for table in tables:
    print(f'  - {table}')

print('\n' + '=' * 80)
print('2. TABLE SCHEMAS (PRAGMA table_info)')
print('=' * 80)
table_names = ['nodes', 'edges', 'ingest_queue', 'brain_ops', 'versions']
for table_name in table_names:
    print(f'\nTable: {table_name}')
    cursor.execute(f'PRAGMA table_info({table_name})')
    columns = cursor.fetchall()
    if columns:
        print(f'  Columns:')
        for cid, name, type_, notnull, dflt_value, pk in columns:
            print(f'    - {name}: {type_} (PK={pk}, NOT NULL={notnull}, Default={dflt_value})')
    else:
        print(f'  [Table does not exist or has no columns]')

print('\n' + '=' * 80)
print('3. COUNT ROWS IN ingest_queue')
print('=' * 80)
cursor.execute('SELECT count(*) FROM ingest_queue')
count = cursor.fetchone()[0]
print(f'  Total rows: {count}')

print('\n' + '=' * 80)
print('4. DISTINCT node_types')
print('=' * 80)
cursor.execute('SELECT DISTINCT node_type FROM nodes LIMIT 20')
node_types = [row[0] for row in cursor.fetchall()]
for nt in node_types:
    print(f'  - {nt}')

print('\n' + '=' * 80)
print('5. DISTINCT lane VALUES')
print('=' * 80)
cursor.execute('SELECT DISTINCT lane FROM nodes WHERE lane IS NOT NULL LIMIT 20')
lanes = [row[0] for row in cursor.fetchall()]
for lane in lanes:
    print(f'  - {lane}')

print('\n' + '=' * 80)
print('6. LANE NODES (id LIKE "lane-%")')
print('=' * 80)
cursor.execute('SELECT id, label FROM nodes WHERE id LIKE "lane-%" LIMIT 10')
lane_nodes = cursor.fetchall()
if lane_nodes:
    for id_val, label in lane_nodes:
        print(f'  - {id_val}: {label}')
else:
    print('  [No lane nodes found]')

print('\n' + '=' * 80)
print('7. DISTINCT edge_types')
print('=' * 80)
cursor.execute('SELECT DISTINCT edge_type FROM edges LIMIT 20')
edge_types = [row[0] for row in cursor.fetchall()]
for et in edge_types:
    print(f'  - {et}')

print('\n' + '=' * 80)
print('8. SAMPLE NODES')
print('=' * 80)
cursor.execute('SELECT id, node_type, layer, label, lane FROM nodes LIMIT 5')
sample_nodes = cursor.fetchall()
for id_val, node_type, layer, label, lane in sample_nodes:
    print(f'  ID: {id_val}')
    print(f'    node_type: {node_type}')
    print(f'    layer: {layer}')
    print(f'    label: {label}')
    print(f'    lane: {lane}')
    print()

conn.close()
