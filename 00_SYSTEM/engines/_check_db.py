import sqlite3
from pathlib import Path
conn = sqlite3.connect(str(Path(__file__).resolve().parents[2] / "litigation_context.db"))
conn.execute("PRAGMA busy_timeout=60000")
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA cache_size=-32000")
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
print(f"Tables: {c.fetchone()[0]}")
for n in ['adversary_assertions','citation_validation','filing_compliance','impeachment_index','alienation_scoring','exhibit_registry','prosecution_timeline','damages_itemization','constitutional_violations','rebuttal_matrix','psych_analysis_results']:
    try:
        c.execute(f"SELECT COUNT(*) FROM {n}")
        print(f"  {n}: {c.fetchone()[0]}")
    except Exception:
        print(f"  {n}: NOT FOUND")
