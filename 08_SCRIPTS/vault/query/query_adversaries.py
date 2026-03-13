import sys, sqlite3
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

conn = sqlite3.connect(r"C:\Users\andre\LitigationOS\litigation_context.db", timeout=180)
conn.execute("PRAGMA busy_timeout=180000")
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA cache_size=-32000")

# 1. Search harvest_texts for Watson family members
print("=== WATSON FAMILY MENTIONS IN HARVEST ===")
for name in ['Albert', 'Lori Watson', 'Lori', 'Cody', 'Emily Watson', 'Ronald Berry', 'Kent County']:
    count = conn.execute("SELECT COUNT(*) FROM harvest_texts WHERE text_content LIKE ?", (f'%{name}%',)).fetchone()[0]
    print(f"  {name:20s}: {count} files")

# 2. Search for Watson family in evidence_quotes
print("\n=== WATSON FAMILY IN EVIDENCE_QUOTES ===")
for name in ['Albert', 'Lori', 'Cody', 'Kent County Prosecutor', 'Emily', 'Berry']:
    count = conn.execute("SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE ?", (f'%{name}%',)).fetchone()[0]
    print(f"  {name:25s}: {count} quotes")

# 3. Check witness_profiles for Watson family
print("\n=== WITNESS PROFILES ===")
rows = conn.execute("SELECT * FROM witness_profiles").fetchall()
cols = [d[0] for d in conn.execute("PRAGMA table_info(witness_profiles)").fetchall()]
col_names = [c[1] for c in conn.execute("PRAGMA table_info(witness_profiles)").fetchall()]
print(f"  Columns: {col_names}")
for r in rows:
    print(f"  {dict(zip(col_names, r))}")

# 4. Check cycle6 tables for Watson family data
print("\n=== CYCLE6 WITNESSES ===")
try:
    rows = conn.execute("SELECT * FROM cycle6_witnesses").fetchall()
    cols = [c[1] for c in conn.execute("PRAGMA table_info(cycle6_witnesses)").fetchall()]
    for r in rows:
        print(f"  {dict(zip(cols, r))}")
except: print("  table not found")

# 5. Kent County employment data
print("\n=== KENT COUNTY EMPLOYMENT DATA ===")
for tbl in ['cycle6_financial_data', 'cycle6_employment']:
    try:
        cols = [c[1] for c in conn.execute(f"PRAGMA table_info({tbl})").fetchall()]
        rows = conn.execute(f"SELECT * FROM {tbl}").fetchall()
        print(f"\n  {tbl} ({len(rows)} rows, cols: {cols}):")
        for r in rows[:20]:
            print(f"    {dict(zip(cols, r))}")
    except Exception as e:
        print(f"  {tbl}: {e}")

# 6. Search for PPO-related evidence
print("\n=== PPO EVIDENCE (lies, false claims) ===")
ppo_count = conn.execute("""
    SELECT COUNT(*) FROM harvest_texts 
    WHERE text_content LIKE '%PPO%' AND harvest_id LIKE 'HARVEST_007%'
""").fetchone()[0]
print(f"  PPO files in harvest: {ppo_count}")

# False PPO / lying patterns
for pattern in ['false statement', 'fabricat', 'lied', 'lying', 'perjur', 'contradict', 'inconsistent', 'no evidence of', 'unfounded', 'exaggerat']:
    count = conn.execute("SELECT COUNT(*) FROM harvest_texts WHERE text_content LIKE ? AND text_content LIKE '%PPO%'", (f'%{pattern}%',)).fetchone()[0]
    print(f"  PPO + '{pattern}': {count} files")

# 7. Search for conspiracy / collusion patterns
print("\n=== CONSPIRACY / COLLUSION PATTERNS ===")
for pattern in ['collu', 'conspir', 'coordinated', 'working together', 'agreed to', 'scheme', 'plan to', 'arranged']:
    count = conn.execute("SELECT COUNT(*) FROM harvest_texts WHERE text_content LIKE ?", (f'%{pattern}%',)).fetchone()[0]
    if count > 0:
        print(f"  '{pattern}': {count} files")

# 8. Sample key evidence about Watson family lies
print("\n=== SAMPLE: Watson PPO false claims ===")
rows = conn.execute("""
    SELECT original_filename, substr(text_content, 1, 500)
    FROM harvest_texts 
    WHERE (text_content LIKE '%false%' OR text_content LIKE '%lie%' OR text_content LIKE '%fabricat%')
    AND text_content LIKE '%PPO%'
    AND harvest_id LIKE 'HARVEST_007%'
    LIMIT 5
""").fetchall()
for r in rows:
    print(f"\n  FILE: {r[0]}")
    print(f"  PREVIEW: {r[1][:300]}")

# 9. Check claims table for existing Watson-related claims
print("\n=== EXISTING CLAIMS vs WATSON ===")
try:
    rows = conn.execute("""
        SELECT claim_id, claim_type, status, vehicle_name 
        FROM claims 
        WHERE claim_text LIKE '%Watson%' OR claim_text LIKE '%Emily%' OR claim_text LIKE '%PPO%'
        LIMIT 20
    """).fetchall()
    for r in rows:
        print(f"  {r}")
except Exception as e:
    cols = [c[1] for c in conn.execute("PRAGMA table_info(claims)").fetchall()]
    print(f"  Claims columns: {cols}")
    print(f"  Error: {e}")

# 10. adversary_models table
print("\n=== ADVERSARY MODELS ===")
try:
    cols = [c[1] for c in conn.execute("PRAGMA table_info(adversary_models)").fetchall()]
    rows = conn.execute("SELECT * FROM adversary_models LIMIT 30").fetchall()
    print(f"  Columns: {cols}, {len(rows)} rows")
    for r in rows[:10]:
        d = dict(zip(cols, r))
        print(f"  {d.get('adversary','?')} | {d.get('attack_type','?')} | {d.get('filing_vehicle','?')} | {d.get('risk_level','?')}")
except Exception as e:
    print(f"  Error: {e}")

# 11. damages tables
print("\n=== DAMAGES TABLES ===")
for tbl in ['damages_quantification', 'damages_methodology', 'damages_evidence_links']:
    try:
        cols = [c[1] for c in conn.execute(f"PRAGMA table_info({tbl})").fetchall()]
        count = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        print(f"\n  {tbl} ({count} rows, cols: {cols})")
        rows = conn.execute(f"SELECT * FROM {tbl} LIMIT 10").fetchall()
        for r in rows:
            print(f"    {dict(zip(cols, r))}")
    except Exception as e:
        print(f"  {tbl}: {e}")

conn.close()
