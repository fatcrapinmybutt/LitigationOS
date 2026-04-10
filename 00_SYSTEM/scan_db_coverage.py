"""Scan DB coverage vs discovered files — identify gaps for ingestion."""
import sqlite3, os

db = sqlite3.connect(r"C:\Users\andre\LitigationOS\litigation_context.db")
db.execute("PRAGMA busy_timeout=60000")
db.execute("PRAGMA journal_mode=WAL")

# 1. Police reports already indexed
print("=== ALREADY-INDEXED POLICE REPORTS ===")
rows = db.execute(
    "SELECT DISTINCT source_file FROM evidence_quotes "
    "WHERE source_file LIKE '%police%' OR source_file LIKE '%NSPD%' OR source_file LIKE '%Police%' "
    "LIMIT 30"
).fetchall()
for r in rows:
    print(f"  {r[0]}")
print(f"  Total distinct sources: {len(rows)}")

# 2. SCAO forms in DB
print("\n=== COURT FORMS IN DB ===")
rows = db.execute(
    "SELECT rule_type, COUNT(*) FROM michigan_rules_extracted "
    "WHERE rule_type IN ('SCAO','FORM','FOC_FORM','MC_FORM','DC_FORM','SCAO_FORM') "
    "GROUP BY rule_type"
).fetchall()
for r in rows:
    print(f"  {r[0]}: {r[1]}")
if not rows:
    print("  NONE — forms not yet indexed!")

# 3. Rule type breakdown
print("\n=== RULE TYPE BREAKDOWN ===")
rows = db.execute(
    "SELECT rule_type, COUNT(*) as cnt FROM michigan_rules_extracted "
    "GROUP BY rule_type ORDER BY cnt DESC LIMIT 20"
).fetchall()
for r in rows:
    print(f"  {r[0]}: {r[1]:,}")

# 4. Adversary coverage in evidence_quotes
print("\n=== ADVERSARY COVERAGE (evidence_quotes) ===")
adversaries = [
    "Kim Davis", "VanDam", "Cassandra", "Duguid", "Hilson", "Kostrzewa",
    "Cavan Berry", "Ronald Berry", "Albert Watson", "Lori Watson",
    "Randall", "Shady Oaks", "Alden", "Brian Cross", "Kent County",
    "Prosecutor", "DHHS", "CPS", "DHS"
]
for name in adversaries:
    cnt = db.execute(
        "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE ?",
        (f"%{name}%",)
    ).fetchone()[0]
    if cnt > 0:
        print(f"  {name}: {cnt} quotes")
    else:
        print(f"  {name}: ** ZERO ** — GAP")

# 5. Timeline events for adversaries
print("\n=== ADVERSARY COVERAGE (timeline_events) ===")
for name in adversaries:
    cnt = db.execute(
        "SELECT COUNT(*) FROM timeline_events WHERE event_description LIKE ? OR actors LIKE ?",
        (f"%{name}%", f"%{name}%")
    ).fetchone()[0]
    if cnt > 0:
        print(f"  {name}: {cnt} events")

# 6. Documents table status
print("\n=== DOCUMENTS TABLE ===")
cols = [r[1] for r in db.execute("PRAGMA table_info(documents)").fetchall()]
print(f"  Columns: {cols}")
cnt = db.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
print(f"  Total indexed docs: {cnt}")

# 7. Check for unindexed high-value files
print("\n=== KEY FILES NOT IN DB ===")
key_files = [
    r"C:\Users\andre\Desktop\Case_61-25006911-01_Pigors.pdf",
    r"C:\Users\andre\Desktop\Assault_Battery_From_Attorney_Reports.pdf",
    r"J:\POLICE_REPORTS\Albert calling police_426dc1c1.pdf",
    r"C:\Users\andre\Documents\2025 Michigan Child Support Formula Manual.pdf",
    r"C:\Users\andre\LitigationOS\02_AUTHORITY\FULL BENCHBOOK CONTEMPT RULES_001.pdf",
]
for f in key_files:
    if os.path.exists(f):
        # Check if in documents table
        basename = os.path.basename(f)
        found = db.execute(
            "SELECT COUNT(*) FROM documents WHERE title LIKE ? OR doc_type LIKE ?",
            (f"%{basename[:30]}%", f"%{basename[:30]}%")
        ).fetchone()[0]
        status = "INDEXED" if found > 0 else "** NOT INDEXED **"
        print(f"  {status}: {basename}")
    else:
        print(f"  FILE MISSING: {f}")

db.close()
print("\nDone.")
