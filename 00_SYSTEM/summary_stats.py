"""Quick DB stats for compaction summary."""
import sqlite3

db = r"C:\Users\andre\LitigationOS\litigation_context.db"
conn = sqlite3.connect(db)
conn.execute("PRAGMA busy_timeout=60000")
conn.execute("PRAGMA journal_mode=WAL")

tables = [
    "evidence_quotes", "authority_chains_v2", "timeline_events",
    "impeachment_matrix", "contradiction_map", "judicial_violations",
    "adversary_profiles", "causal_chains", "rebuttal_matrix",
    "harvest_intelligence", "police_reports", "michigan_rules_extracted",
    "master_citations", "md_sections", "filing_readiness",
    "engine_registry", "engine_manifest"
]

for t in tables:
    try:
        cnt = conn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
        print(f"{t}: {cnt:,}")
    except Exception as e:
        print(f"{t}: ERROR - {e}")

total = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
print(f"\nTotal tables: {total}")

conn.close()
