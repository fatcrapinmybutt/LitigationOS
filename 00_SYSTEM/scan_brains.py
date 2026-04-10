"""Scan all brain DBs and central DB for table/row counts."""
import sys, sqlite3, os
sys.path.insert(0, r"C:\Users\andre\LitigationOS")

CENTRAL = r"C:\Users\andre\LitigationOS\litigation_context.db"
BRAINS_DIR = r"C:\Users\andre\LitigationOS\00_SYSTEM\brains"

def get_tables_and_counts(db_path):
    result = {}
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA busy_timeout=60000")
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()]
        for t in tables:
            try:
                cnt = conn.execute(f'SELECT COUNT(*) FROM [{t}]').fetchone()[0]
                result[t] = cnt
            except Exception as e:
                result[t] = f"ERROR: {e}"
        conn.close()
    except Exception as e:
        result["__ERROR__"] = str(e)
    return result

print("=" * 80)
print("CENTRAL DB:", CENTRAL)
print("=" * 80)
central = get_tables_and_counts(CENTRAL)
key_tables = ['timeline_events', 'evidence_quotes', 'judicial_violations',
              'impeachment_matrix', 'contradiction_map', 'authority_chains_v2',
              'parties', 'claims', 'police_reports', 'berry_mcneill_intelligence',
              'master_citations', 'michigan_rules_extracted', 'md_sections',
              'file_inventory', 'md_cross_refs', 'deadlines', 'filing_packages']
for t in key_tables:
    if t in central:
        print(f"  {t}: {central[t]}")
    else:
        print(f"  {t}: NOT FOUND")

print(f"\n  Total tables in central: {len(central)}")

print("\n" + "=" * 80)
print("BRAIN DATABASES")
print("=" * 80)

for fname in sorted(os.listdir(BRAINS_DIR)):
    if not fname.endswith('.db'):
        continue
    path = os.path.join(BRAINS_DIR, fname)
    size_mb = os.path.getsize(path) / (1024*1024)
    print(f"\n--- {fname} ({size_mb:.1f} MB) ---")
    brain = get_tables_and_counts(path)
    for t, cnt in sorted(brain.items()):
        marker = ""
        if t in central and isinstance(cnt, int) and isinstance(central.get(t), int):
            if cnt > central[t]:
                marker = f"  *** BRAIN RICHER: +{cnt - central[t]} ***"
            elif cnt < central[t]:
                marker = f"  (central has more: +{central[t] - cnt})"
        elif t not in central and isinstance(cnt, int) and cnt > 0:
            marker = "  *** NEW TABLE (not in central) ***"
        print(f"  {t}: {cnt}{marker}")

print("\n" + "=" * 80)
print("SCHEMA DETAILS FOR KEY SYNC TARGETS")
print("=" * 80)

conn = sqlite3.connect(CENTRAL)
for t in ['timeline_events', 'parties', 'evidence_quotes', 'judicial_violations',
          'contradiction_map', 'impeachment_matrix', 'authority_chains_v2']:
    if t in central:
        cols = conn.execute(f"PRAGMA table_info([{t}])").fetchall()
        print(f"\n{t} columns: {[c[1] for c in cols]}")
conn.close()

# Also show schemas from brains for matching
for fname in ['narrative_brain.db', 'entity_brain.db']:
    path = os.path.join(BRAINS_DIR, fname)
    if os.path.exists(path):
        conn = sqlite3.connect(path)
        brain_tables = get_tables_and_counts(path)
        for t in brain_tables:
            if t in central or t in ['timeline_events', 'parties', 'evidence_quotes']:
                cols = conn.execute(f"PRAGMA table_info([{t}])").fetchall()
                print(f"\n{fname} -> {t} columns: {[c[1] for c in cols]}")
        conn.close()
