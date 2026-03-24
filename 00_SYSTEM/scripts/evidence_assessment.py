"""Evidence Arsenal Assessment — queries litigation_context.db for comprehensive evidence stats."""
import sqlite3, sys, os, json
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = r'C:\Users\andre\LitigationOS\litigation_context.db'
conn = sqlite3.connect(DB_PATH, timeout=60)
conn.execute("PRAGMA busy_timeout=60000")
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA cache_size=-32000")
conn.execute("PRAGMA temp_store=MEMORY")
conn.execute("PRAGMA synchronous=NORMAL")
conn.row_factory = sqlite3.Row

# ── 1. Core evidence table counts ──
core_tables = [
    'evidence_quotes', 'documents', 'file_inventory', 'judicial_violations',
    'narrative_context', 'critical_facts', 'case_timeline', 'claims',
    'docket_events', 'deadlines', 'authority_chains', 'filing_readiness',
    'risk_events', 'evidence_chain', 'exhibits', 'filing_packages',
]

print("=" * 60)
print("  EVIDENCE ARSENAL STATUS")
print("=" * 60)
counts = {}
for tbl in core_tables:
    try:
        count = conn.execute(f"SELECT COUNT(*) FROM [{tbl}]").fetchone()[0]
        counts[tbl] = count
        print(f"  {tbl:30s}: {count:>8,} rows")
    except Exception as e:
        print(f"  {tbl:30s}: TABLE NOT FOUND ({e})")

# ── 2. All evidence-related tables ──
print("\n" + "=" * 60)
print("  ALL EVIDENCE-RELATED TABLES")
print("=" * 60)
ev_tables = conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND "
    "(name LIKE '%evidence%' OR name LIKE '%exhibit%' OR name LIKE '%proof%' OR name LIKE '%quote%') "
    "ORDER BY name"
).fetchall()
for row in ev_tables:
    tbl = row[0]
    try:
        c = conn.execute(f"SELECT COUNT(*) FROM [{tbl}]").fetchone()[0]
        print(f"  {tbl:45s}: {c:>8,} rows")
    except:
        pass

# ── 3. Evidence by lane/vehicle ──
print("\n" + "=" * 60)
print("  EVIDENCE BY LANE / VEHICLE")
print("=" * 60)
for tbl in ['evidence_quotes', 'claims', 'narrative_context', 'critical_facts',
            'case_timeline', 'docket_events', 'judicial_violations']:
    try:
        cols = [c[1] for c in conn.execute(f"PRAGMA table_info({tbl})").fetchall()]
        lane_col = next((c for c in cols if 'lane' in c.lower() or 'vehicle' in c.lower()), None)
        if lane_col:
            rows = conn.execute(
                f"SELECT [{lane_col}], COUNT(*) as cnt FROM [{tbl}] "
                f"GROUP BY [{lane_col}] ORDER BY cnt DESC LIMIT 15"
            ).fetchall()
            print(f"\n  {tbl} by [{lane_col}]:")
            for r in rows:
                print(f"    {str(r[0]):40s}: {r[1]:>6,}")
    except Exception as e:
        print(f"  {tbl}: {e}")

# ── 4. Evidence quotes — sample high-value items ──
print("\n" + "=" * 60)
print("  HIGH-VALUE EVIDENCE SAMPLES")
print("=" * 60)
try:
    eq_cols = [c[1] for c in conn.execute("PRAGMA table_info(evidence_quotes)").fetchall()]
    print(f"  evidence_quotes columns: {eq_cols}")
    score_col = next((c for c in eq_cols if 'score' in c.lower() or 'weight' in c.lower() or 'strength' in c.lower()), None)
    if score_col:
        top = conn.execute(
            f"SELECT * FROM evidence_quotes ORDER BY [{score_col}] DESC LIMIT 5"
        ).fetchall()
        print(f"\n  Top 5 by [{score_col}]:")
        for r in top:
            print(f"    {dict(r)}")
    else:
        top = conn.execute("SELECT * FROM evidence_quotes LIMIT 5").fetchall()
        print("\n  Sample 5 rows:")
        for r in top:
            d = dict(r)
            # Truncate long values
            for k, v in d.items():
                if isinstance(v, str) and len(v) > 120:
                    d[k] = v[:120] + "..."
            print(f"    {d}")
except Exception as e:
    print(f"  evidence_quotes sample: {e}")

# ── 5. Claims analysis ──
print("\n" + "=" * 60)
print("  CLAIMS ANALYSIS")
print("=" * 60)
try:
    cl_cols = [c[1] for c in conn.execute("PRAGMA table_info(claims)").fetchall()]
    print(f"  claims columns: {cl_cols}")

    # Status distribution
    status_col = next((c for c in cl_cols if 'status' in c.lower()), None)
    if status_col:
        rows = conn.execute(
            f"SELECT [{status_col}], COUNT(*) FROM claims GROUP BY [{status_col}] ORDER BY COUNT(*) DESC"
        ).fetchall()
        print(f"\n  Claims by [{status_col}]:")
        for r in rows:
            print(f"    {str(r[0]):30s}: {r[1]:>6,}")

    # Type distribution
    type_col = next((c for c in cl_cols if 'type' in c.lower()), None)
    if type_col:
        rows = conn.execute(
            f"SELECT [{type_col}], COUNT(*) FROM claims GROUP BY [{type_col}] ORDER BY COUNT(*) DESC LIMIT 15"
        ).fetchall()
        print(f"\n  Claims by [{type_col}]:")
        for r in rows:
            print(f"    {str(r[0]):40s}: {r[1]:>6,}")

    # Sample claims
    print("\n  Sample claims (first 5):")
    for r in conn.execute("SELECT * FROM claims LIMIT 5").fetchall():
        d = dict(r)
        for k, v in d.items():
            if isinstance(v, str) and len(v) > 100:
                d[k] = v[:100] + "..."
        print(f"    {d}")
except Exception as e:
    print(f"  claims: {e}")

# ── 6. Filing readiness check ──
print("\n" + "=" * 60)
print("  FILING READINESS")
print("=" * 60)
try:
    fr_cols = [c[1] for c in conn.execute("PRAGMA table_info(filing_readiness)").fetchall()]
    print(f"  filing_readiness columns: {fr_cols}")
    rows = conn.execute("SELECT * FROM filing_readiness LIMIT 10").fetchall()
    for r in rows:
        d = dict(r)
        for k, v in d.items():
            if isinstance(v, str) and len(v) > 100:
                d[k] = v[:100] + "..."
        print(f"    {d}")
except Exception as e:
    print(f"  filing_readiness: {e}")

# ── 7. Deadlines ──
print("\n" + "=" * 60)
print("  UPCOMING DEADLINES")
print("=" * 60)
try:
    dl_cols = [c[1] for c in conn.execute("PRAGMA table_info(deadlines)").fetchall()]
    print(f"  deadlines columns: {dl_cols}")
    date_col = next((c for c in dl_cols if 'date' in c.lower() or 'due' in c.lower()), None)
    if date_col:
        rows = conn.execute(
            f"SELECT * FROM deadlines ORDER BY [{date_col}] ASC LIMIT 10"
        ).fetchall()
        for r in rows:
            d = dict(r)
            for k, v in d.items():
                if isinstance(v, str) and len(v) > 80:
                    d[k] = v[:80] + "..."
            print(f"    {d}")
except Exception as e:
    print(f"  deadlines: {e}")

# ── 8. Judicial violations summary ──
print("\n" + "=" * 60)
print("  JUDICIAL VIOLATIONS SUMMARY")
print("=" * 60)
try:
    jv_cols = [c[1] for c in conn.execute("PRAGMA table_info(judicial_violations)").fetchall()]
    print(f"  judicial_violations columns: {jv_cols}")
    type_col = next((c for c in jv_cols if 'type' in c.lower() or 'category' in c.lower() or 'violation' in c.lower()), None)
    if type_col:
        rows = conn.execute(
            f"SELECT [{type_col}], COUNT(*) FROM judicial_violations GROUP BY [{type_col}] ORDER BY COUNT(*) DESC LIMIT 15"
        ).fetchall()
        print(f"\n  By [{type_col}]:")
        for r in rows:
            print(f"    {str(r[0]):50s}: {r[1]:>6,}")
    else:
        print("  No type/category column found. Sample rows:")
        for r in conn.execute("SELECT * FROM judicial_violations LIMIT 3").fetchall():
            print(f"    {dict(r)}")
except Exception as e:
    print(f"  judicial_violations: {e}")

# ── 9. Total table count ──
print("\n" + "=" * 60)
print("  DATABASE SUMMARY")
print("=" * 60)
total_tables = conn.execute(
    "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
).fetchone()[0]
db_size = os.path.getsize(DB_PATH)
print(f"  Total tables: {total_tables}")
print(f"  DB size: {db_size / (1024*1024):.1f} MB")

conn.close()
print("\n✅ Evidence assessment complete.")
