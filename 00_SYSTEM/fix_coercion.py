"""Fix coercion_emails (wrong column names) + continue Phase 34 (Encyclopedia update)."""
import sqlite3

BRAIN = r"C:\Users\andre\LitigationOS\00_SYSTEM\brains\shadyoaks_brain.db"
out   = []

bc = sqlite3.connect(BRAIN)
bc.execute("PRAGMA journal_mode=WAL"); bc.execute("PRAGMA busy_timeout=60000")

# actual coercion_emails columns: id, date, from_entity, to_party, subject, summary, legal_significance, file_path, exhibit_id
coercion_data = [
    ("2025-02-13",
     "Shelly Przybylek (Shady Oaks Manager)",
     "Andrew Pigors",
     "Settlement Proposal — Lot 17",
     "HOA offers $750 + debt wipe IF Andrew surrenders keys/title AND drops all court proceedings.",
     "Extortion/coercion: conditioning settlement on dismissal of all pending proceedings. MCL 750.213, MCL 445.911 (CPA), MCR 1.109(E)(5).",
     None, "COERCE-001"),
    ("2026-02-18",
     "Cassandra VanDam (Shady Oaks Agent) via Facebook Messenger",
     "Prospective Buyer (Public Statement)",
     "Lot 17 availability inquiry",
     "VanDam: 'No maam he abandoned the home it is no longer his home. Andrew Pigors does not own a home at Shady Oaks MHC. We are in the process thru our legal team.'",
     "Slander of title — public false statement Andrew abandoned and no longer owns Lot 17 trailer. MCL 565.108; MCL 600.2911. Andrew DID NOT abandon — forcibly evicted after contested proceedings.",
     r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\Screenshot_20260218_212004_One UI Home.jpg",
     "VANDM-001"),
    ("2025-01-01",
     "Shady Oaks HOA (email chain — exact date TBD)",
     "Andrew Pigors",
     "Lot 17 purchase offer pre-hearing",
     "HOA attempted to purchase/coerce transfer of trailer PRIOR to eviction hearing. Exact text pending full email extraction from FOIA/subpoena.",
     "Pre-hearing coercion undermines MCL 554.131 mobile home residency rights. Evidence of predatory intent before judicial process.",
     None, "COERCE-002"),
]
ins = 0
for row in coercion_data:
    try:
        bc.execute(
            "INSERT INTO coercion_emails (date,from_entity,to_party,subject,summary,legal_significance,file_path,exhibit_id) VALUES (?,?,?,?,?,?,?,?)",
            row
        )
        ins += 1
    except Exception as e:
        out.append(f"coercion err: {e}")
bc.commit()
out.append(f"coercion_emails inserted: {ins}")
out.append(f"coercion_emails total: {bc.execute('SELECT COUNT(*) FROM coercion_emails').fetchone()[0]}")

# Final brain counts
brain_tables = [r[0] for r in bc.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
out.append("\n=== BRAIN DB FINAL COUNTS ===")
for t in brain_tables:
    cnt = bc.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
    out.append(f"  {t}: {cnt}")

bc.close()

with open(r"C:\Users\andre\temp\coercion_fix_output.txt","w",encoding="utf-8") as f:
    f.write("\n".join(out))
print("DONE")
