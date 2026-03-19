"""Phase 1.5: Asset Inventory — Catalog all DB tables, filings, code, Neo4j data."""
import sqlite3, sys, os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB = r'C:\Users\andre\LitigationOS\litigation_context.db'
conn = sqlite3.connect(DB)

conn.execute('''CREATE TABLE IF NOT EXISTS omega_asset_inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT, name TEXT, detail TEXT, status TEXT, quality_score REAL,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(category, name)
)''')
conn.commit()

print('=== ASSET INVENTORY ===')

# 1. DB Tables
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
populated = 0
empty = 0
for (t,) in tables:
    try:
        cnt = conn.execute(f'SELECT COUNT(*) FROM [{t}]').fetchone()[0]
        if cnt > 0:
            populated += 1
        else:
            empty += 1
    except:
        pass

print(f'  DB Tables: {len(tables)} total, {populated} populated, {empty} empty')

# Key litigation tables
print('  Key Tables:')
key_tables = ['claims', 'evidence_quotes', 'legal_actions', 'filings', 'rulings',
              'exhibits', 'case_lanes', 'court_orders', 'judicial_violations',
              'agents', 'skills', 'omega_filesystem_map', 'omega_zip_intelligence',
              'scan_inventory', 'safety_snapshots']
for t in key_tables:
    try:
        cnt = conn.execute(f'SELECT COUNT(*) FROM [{t}]').fetchone()[0]
        print(f'    {t}: {cnt:,} rows')
        conn.execute('INSERT OR REPLACE INTO omega_asset_inventory (category, name, detail, status) VALUES (?,?,?,?)',
                    ('db_table', t, f'{cnt} rows', 'populated' if cnt > 0 else 'empty'))
    except Exception as e:
        print(f'    {t}: NOT FOUND')

conn.commit()

# 2. Filing directories
print()
print('  Filing Directories:')
for d in ['01_COA_366810', '02_TRIAL_14TH', '03_FEDERAL_1983', '04_JTC_MCNEILL', '05_BAR_BARNES', '06_EMERGENCY']:
    p = os.path.join(r'C:\Users\andre\LitigationOS', d)
    if os.path.exists(p):
        cnt = sum(1 for _, _, files in os.walk(p) for f in files)
        print(f'    {d}: {cnt} files')
        conn.execute('INSERT OR REPLACE INTO omega_asset_inventory (category, name, detail, status) VALUES (?,?,?,?)',
                    ('filing_dir', d, f'{cnt} files', 'active'))

# 3. Code assets
print()
print('  Code Assets:')
code_assets = [
    ('Desktop App', r'C:\Users\andre\LitigationOS\00_SYSTEM\apps\desktop'),
    ('Mobile App (Expo)', r'C:\Users\andre\LitigationOS\13_TOOLS'),
    ('Pipeline', r'C:\Users\andre\LitigationOS\00_SYSTEM\pipeline'),
    ('Autopilot Suite', r'C:\Users\andre\LitigationOS\00_SYSTEM\autopilot_suite'),
]
for name, path in code_assets:
    if os.path.exists(path):
        exts = ('.py', '.js', '.ts', '.jsx', '.tsx', '.ps1')
        cnt = sum(1 for _, _, files in os.walk(path) for f in files if any(f.endswith(e) for e in exts))
        print(f'    {name}: {cnt} code files')
        conn.execute('INSERT OR REPLACE INTO omega_asset_inventory (category, name, detail, status) VALUES (?,?,?,?)',
                    ('code_asset', name, f'{cnt} code files at {path}', 'active'))

# 4. Neo4j data
print()
print('  Neo4j Data:')
neo4j_files = []
for root, dirs, files in os.walk(r'C:\Users\andre\LitigationOS\00_SYSTEM'):
    for f in files:
        if 'neo4j' in f.lower() and f.endswith(('.csv', '.cypher')):
            neo4j_files.append(os.path.join(root, f))
for nf in neo4j_files[:10]:
    size_kb = os.path.getsize(nf) / 1024
    print(f'    {os.path.basename(nf)}: {size_kb:.0f}KB')
print(f'    Total: {len(neo4j_files)} Neo4j export files')

# 5. Skills
print()
print('  Skills:')
agent_skills = r'C:\Users\andre\LitigationOS\.agents\skills'
if os.path.exists(agent_skills):
    skill_count = sum(1 for _, _, files in os.walk(agent_skills) for f in files if f.endswith('.md'))
    print(f'    .agents/skills: {skill_count} skill files')
local_skills = r'C:\Users\andre\LitigationOS\local_model\skills'
if os.path.exists(local_skills):
    skill_count2 = sum(1 for _, _, files in os.walk(local_skills) for f in files if f.endswith('.md'))
    print(f'    local_model/skills: {skill_count2} skill files')
user_skills = r'C:\Users\andre\skills'
if os.path.exists(user_skills):
    skill_count3 = len([f for f in os.listdir(user_skills) if os.path.isfile(os.path.join(user_skills, f))])
    print(f'    C:/Users/andre/skills: {skill_count3} files')

conn.commit()
conn.close()
print()
print('Asset inventory complete.')
