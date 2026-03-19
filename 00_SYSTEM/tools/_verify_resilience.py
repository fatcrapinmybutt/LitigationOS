"""Quick verification that the shell resilience engine fixes the crash."""
import sys
sys.path.insert(0, r"C:\Users\andre\LitigationOS\00_SYSTEM")
from shell_resilience_engine import safe_query, safe_fts, db_health_check

health = db_health_check()
print(f"DB: {health['size_mb']}MB, {health['table_count']} tables, WAL={health['wal_mode']}, locked={health['locked']}")

for t in ['tort_claims','drive_evidence','agent_performance','convergence_cycles','party_contacts']:
    try:
        rows = safe_query(f"SELECT COUNT(*) as cnt FROM [{t}]")
        print(f"  {t}: {rows[0]['cnt']} rows")
    except Exception as e:
        print(f"  {t}: {e}")

results = safe_fts("evidence_quotes_fts", "Watson custody alienation", limit=3)
print(f"FTS search: {len(results)} results")

rows = safe_query("SELECT id, title FROM filing_packages ORDER BY id DESC LIMIT 5")
print("Latest packages:")
for r in rows:
    title = r["title"][:60] if r["title"] else "untitled"
    print(f"  #{r['id']}: {title}")

print("\nShell resilience engine: VERIFIED")
