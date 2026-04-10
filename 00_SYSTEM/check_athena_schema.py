"""Check DB schemas for ATHENA engine design."""
import sqlite3

conn = sqlite3.connect(r"C:\Users\andre\LitigationOS\litigation_context.db")
conn.row_factory = sqlite3.Row

for tbl in ["master_citations", "critical_facts", "irac_analyses", "authority_chains_v2", "michigan_rules_extracted"]:
    cols = [(r[1], r[2]) for r in conn.execute(f"PRAGMA table_info({tbl})")]
    cnt = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
    print(f"{tbl} ({cnt:,} rows): {[c[0] for c in cols]}")

print("\n--- Sample authority_chains_v2 ---")
for r in conn.execute("SELECT primary_citation, relationship, lane FROM authority_chains_v2 LIMIT 8").fetchall():
    print(dict(r))

print("\n--- Sample master_citations ---")
for r in conn.execute("SELECT * FROM master_citations LIMIT 5").fetchall():
    print(dict(r))

# Federal/SCOTUS vs Michigan
scotus = conn.execute("SELECT COUNT(*) FROM authority_chains_v2 WHERE primary_citation LIKE '%U.S.%' OR primary_citation LIKE '%S.Ct.%' OR primary_citation LIKE '%USC%'").fetchone()[0]
mich = conn.execute("SELECT COUNT(*) FROM authority_chains_v2 WHERE primary_citation LIKE '%Mich%' OR primary_citation LIKE '%MCL%' OR primary_citation LIKE '%MCR%'").fetchone()[0]
print(f"\nFederal/SCOTUS citations: {scotus:,}")
print(f"Michigan citations: {mich:,}")

# Key doctrines
doctrines = conn.execute("SELECT DISTINCT primary_citation FROM authority_chains_v2 WHERE primary_citation LIKE '%Vodvarka%' OR primary_citation LIKE '%Troxel%' OR primary_citation LIKE '%Mathews%' OR primary_citation LIKE '%Pierron%' LIMIT 20").fetchall()
print(f"Key case law: {[r[0] for r in doctrines]}")

# Check what rule_types exist
types = conn.execute("SELECT rule_type, COUNT(*) as cnt FROM michigan_rules_extracted GROUP BY rule_type ORDER BY cnt DESC").fetchall()
print(f"\nRule types: {[(r[0], r[1]) for r in types]}")

conn.close()
