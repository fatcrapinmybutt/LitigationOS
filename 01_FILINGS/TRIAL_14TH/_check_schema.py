import sqlite3
conn = sqlite3.connect(r"C:\Users\andre\LitigationOS\litigation_context.db")
conn.execute("PRAGMA busy_timeout=60000")
for t in ["shadyoaks_claim_table","canonical_fact_index","evidence_quotes"]:
    cols = conn.execute(f"PRAGMA table_info({t})").fetchall()
    print(f"{t}: {[c[1] for c in cols]}")
    row = conn.execute(f"SELECT * FROM {t} LIMIT 1").fetchone()
    print(f"  sample: {row}")
    print()
conn.close()
