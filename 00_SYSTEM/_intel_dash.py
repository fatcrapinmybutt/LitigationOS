
import sqlite3, json
from datetime import date
conn = sqlite3.connect(r"C:\\Users\\andre\\LitigationOS\\litigation_context.db")
conn.execute("PRAGMA busy_timeout=30000")
tables = [
    ("evidence_quotes", "SELECT COUNT(*) FROM evidence_quotes WHERE is_duplicate=0"),
    ("timeline_events", "SELECT COUNT(*) FROM timeline_events"),
    ("impeachment_matrix", "SELECT COUNT(*) FROM impeachment_matrix"),
    ("contradiction_map", "SELECT COUNT(*) FROM contradiction_map"),
    ("judicial_violations", "SELECT COUNT(*) FROM judicial_violations"),
    ("berry_mcneill_intel", "SELECT COUNT(*) FROM berry_mcneill_intelligence"),
    ("authority_chains_v2", "SELECT COUNT(*) FROM authority_chains_v2"),
    ("police_reports", "SELECT COUNT(*) FROM police_reports"),
    ("michigan_rules", "SELECT COUNT(*) FROM michigan_rules_extracted"),
    ("file_inventory", "SELECT COUNT(*) FROM file_inventory"),
]
results = {}
for name, sql in tables:
    try:
        results[name] = conn.execute(sql).fetchone()[0]
    except:
        results[name] = "N/A"
sep_days = (date.today() - date(2025, 7, 29)).days
results["separation_days"] = sep_days
conn.close()
print(json.dumps(results))
