import sys, os, sqlite3
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

print("=" * 80)
print("SCRIPT INGESTION & CATALOGING SYSTEMS ANALYSIS")
print("=" * 80)

# 1. Check script_vault.db
print("\n[1] SCRIPT_VAULT.DB ANALYSIS")
print("-" * 80)
script_vault_path = r"C:\Users\andre\LitigationOS\script_vault.db"
if os.path.exists(script_vault_path):
    print(f"✓ Found: {script_vault_path}")
    try:
        conn = sqlite3.connect(script_vault_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = cursor.fetchall()
        print(f"\nTables ({len(tables)}):")
        for table_name, in tables:
            cursor.execute(f"SELECT COUNT(*) FROM [{table_name}];")
            count = cursor.fetchone()[0]
            
            # Get columns
            cursor.execute(f"PRAGMA table_info([{table_name}]);")
            columns = cursor.fetchall()
            col_names = [col[1] for col in columns]
            
            print(f"  • {table_name}: {count:,} rows")
            if col_names:
                print(f"    Columns: {', '.join(col_names[:12])}")
                if len(col_names) > 12:
                    print(f"    ... and {len(col_names) - 12} more")
        
        conn.close()
    except Exception as e:
        print(f"ERROR: {e}")
else:
    print(f"✗ Not found: {script_vault_path}")

# 2. Check litigation_context.db for mega_file_harvest table
print("\n[2] LITIGATION_CONTEXT.DB - MEGA_FILE_HARVEST TABLE")
print("-" * 80)
db_paths = [
    r"C:\Users\andre\LitigationOS\litigation_context.db",
    r"C:\Users\andre\LitigationOS\09_DATA\litigation_context.db"
]

found_db = False
for db_path in db_paths:
    if not os.path.exists(db_path):
        continue
    
    found_db = True
    print(f"Checking: {db_path}")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if mega_file_harvest exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='mega_file_harvest';")
        if cursor.fetchone():
            print("  ✓ mega_file_harvest table exists")
            
            # Get columns
            cursor.execute("PRAGMA table_info(mega_file_harvest);")
            columns = cursor.fetchall()
            col_names = [col[1] for col in columns]
            print(f"  Total columns: {len(col_names)}")
            print(f"  Columns: {', '.join(col_names[:20])}")
            if len(col_names) > 20:
                print(f"  ... and {len(col_names) - 20} more")
            
            # Check for Python-related columns
            python_cols = [c for c in col_names if 'python' in c.lower()]
            if python_cols:
                print(f"  ⚠ Python-related columns: {python_cols}")
                
                cursor.execute("SELECT COUNT(*) FROM mega_file_harvest;")
                count = cursor.fetchone()[0]
                print(f"  Total rows: {count:,}")
                
                # Sample data
                for col in python_cols:
                    cursor.execute(f"SELECT COUNT(*) FROM mega_file_harvest WHERE [{col}] IS NOT NULL AND [{col}] != '';")
                    non_null = cursor.fetchone()[0]
                    if non_null > 0:
                        print(f"    - {col}: {non_null:,} rows with data")
            else:
                cursor.execute("SELECT COUNT(*) FROM mega_file_harvest;")
                count = cursor.fetchone()[0]
                print(f"  ✓ No Python-specific columns. Total rows: {count:,}")
        else:
            print("  ✗ mega_file_harvest table not found")
        
        conn.close()
    except Exception as e:
        print(f"  ERROR: {e}")

if not found_db:
    print("✗ No litigation_context.db databases found")

# 3. Analyze self_evolve_v2.py
print("\n[3] SELF_EVOLVE_V2.PY ANALYSIS")
print("-" * 80)
self_evolve_path = r"C:\Users\andre\LitigationOS\00_SYSTEM\local_model\self_evolve_v2.py"
if os.path.exists(self_evolve_path):
    print(f"✓ Found: {self_evolve_path}")
    try:
        with open(self_evolve_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Count key patterns
        import re
        classes = len(re.findall(r'^class \w+', content, re.MULTILINE))
        functions = len(re.findall(r'^def \w+', content, re.MULTILINE))
        size = len(content)
        lines = len(content.split('\n'))
        
        print(f"  Size: {size:,} bytes, {lines:,} lines")
        print(f"  Classes: {classes}, Functions: {functions}")
        
        # Check what it does
        keywords = []
        if 'SelfEvolver' in content:
            keywords.append("SelfEvolver class")
        if 'evolution' in content.lower():
            keywords.append("Model evolution")
        if 'script' in content.lower():
            keywords.append("Script logic")
        if 'catalog' in content.lower():
            keywords.append("Cataloging")
        if 'ingest' in content.lower():
            keywords.append("Ingestion")
        if 'knowledge' in content.lower():
            keywords.append("Knowledge management")
        
        if keywords:
            print(f"  Keywords: {', '.join(keywords)}")
        
        # Check imports
        imports = re.findall(r'^import (\w+)|^from (\w+)', content, re.MULTILINE)
        unique_modules = sorted(set(m[0] if m[0] else m[1] for m in imports))
        print(f"  Key modules: {', '.join(unique_modules[:10])}")
    except Exception as e:
        print(f"  ERROR: {e}")
else:
    print(f"✗ Not found: {self_evolve_path}")

# 4. Check agents directory
print("\n[4] AGENT DISCOVERY - AGENTS DIRECTORY")
print("-" * 80)
agents_dir = r"C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\agents"
if os.path.exists(agents_dir):
    print(f"✓ Found: {agents_dir}")
    
    agent_files = []
    for root, dirs, files in os.walk(agents_dir):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                filepath = os.path.join(root, file)
                agent_files.append(filepath)
    
    print(f"  Total agent files: {len(agent_files)}")
    
    # Check for script-related agents
    script_keywords = ['script', 'discover', 'catalog', 'ingest', 'absorb', 'forge', 'capability']
    script_related = []
    
    for filepath in agent_files:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().lower()
            
            if any(kw in content for kw in script_keywords):
                relative = os.path.relpath(filepath, agents_dir)
                script_related.append(relative)
        except:
            pass
    
    if script_related:
        print(f"\n  Script/Discovery-related agents ({len(script_related)}):")
        for agent in sorted(script_related):
            print(f"    • {agent}")
    else:
        print("  ✗ No script/discovery-related agents found")
else:
    print(f"✗ Not found: {agents_dir}")

# 5. Fast concept search
print("\n[5] CONCEPT SEARCH")
print("-" * 80)
concepts = ['code_absorber', 'script_forge', 'capability_index']
base_dir = r"C:\Users\andre\LitigationOS"

print("Searching for concepts in Python files...")
for concept in concepts:
    found = False
    import glob
    for filepath in glob.glob(f"{base_dir}/**/*.py", recursive=True):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                if concept in f.read().lower():
                    if not found:
                        print(f"  ✓ '{concept}' found in:")
                        found = True
                    print(f"    • {os.path.relpath(filepath, base_dir)}")
        except:
            pass
    
    if not found:
        print(f"  ✗ '{concept}' not found")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
