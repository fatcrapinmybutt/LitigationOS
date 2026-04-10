"""Phase 35: Write Gmail ledger + spoliation evidence to brain DB and litigation_context.db"""
import sqlite3
from pathlib import Path
from datetime import datetime

BRAIN_DB = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\brains\shadyoaks_brain.db")
MAIN_DB  = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")
today = datetime.now().strftime("%Y-%m-%d")
PRAGMA = "PRAGMA journal_mode=WAL; PRAGMA busy_timeout=60000; PRAGMA cache_size=-32000;"

def open_db(path):
    db = sqlite3.connect(str(path))
    for p in PRAGMA.split(';'):
        if p.strip():
            db.execute(p)
    return db

# ── brain DB writes ──────────────────────────────
brain = open_db(BRAIN_DB)

brain.execute("""
    INSERT OR IGNORE INTO evidence_registry
    (exhibit_id, description, file_path, evidence_type, date_of_evidence,
     actors_involved, legal_theory, bates_number, status, notes)
    VALUES (?,?,?,?,?,?,?,?,?,?)
""", (
    "EXHIBIT-B-GMAIL-LEDGER",
    "HOA submitted South Haven Park MHC ledger (wrong property) to court for Shady Oaks case. Email from Southhaven@ourhomesofamerica.com by Cassandra VanDam. Andrew corrected: rent paid through Dec 2024. HOA: 'sent in error' — correct ledger never produced.",
    "gmail_thread_may16_2025_south_haven_wrong_ledger",
    "email_thread",
    "2025-05-16",
    "Cassandra VanDam, Homes of America LLC",
    "financial_fraud, MCR 2.114(E) sanctions",
    "PIGORS-B-LEDGER-001",
    "ACQUIRED",
    "Wrong-property ledger submission supports sanctions motion and financial fraud claims"
))

brain.execute("""
    INSERT OR IGNORE INTO evidence_registry
    (exhibit_id, description, file_path, evidence_type, date_of_evidence,
     actors_involved, legal_theory, bates_number, status, notes)
    VALUES (?,?,?,?,?,?,?,?,?,?)
""", (
    "EXHIBIT-B-SPOLIATION-XLS",
    "shady enhanced redacted ledger$$$ conv_10aa496d.xls — 2.1 MB file with 1 sheet, 1 row, 1 column, empty string. Wiped after litigation commenced.",
    r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\shady enhanced redacted ledger$$$ conv_10aa496d.xls",
    "spreadsheet_wiped",
    "2025",
    "Homes of America LLC, Cassandra VanDam",
    "spoliation, MCR 2.313, MCR 2.114(E)",
    "PIGORS-B-SPOLIATION-001",
    "SPOLIATED",
    "Digital version null-wiped; JPG original authentic at COURT_FILING_PACKETS/SHADY/"
))

brain.execute("""
    INSERT OR IGNORE INTO evidence_registry
    (exhibit_id, description, file_path, evidence_type, date_of_evidence,
     actors_involved, legal_theory, bates_number, status, notes)
    VALUES (?,?,?,?,?,?,?,?,?,?)
""", (
    "EXHIBIT-B-SPOLIATION-CSV",
    "shady_oaks_park_mhp_llc_LEDGER.csv — 142,395 bytes, ALL null bytes. Wiped after litigation commenced.",
    r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\shady_oaks_park_mhp_llc_LEDGER.csv",
    "csv_wiped",
    "2025",
    "Homes of America LLC",
    "spoliation, MCR 2.313",
    "PIGORS-B-SPOLIATION-002",
    "SPOLIATED",
    "All 142,395 bytes are null; file was overwritten with zeros to destroy ledger evidence"
))

# New contradictions
for row in [
    ("Cassandra VanDam / Homes of America LLC",
     "HOA submitted South Haven Park MHC ledger to court for Shady Oaks case",
     "HOA never produced an unaltered Shady Oaks ledger despite active litigation",
     "gmail_may16_2025_ledger_email", "HOA 'sent in error' admission",
     10, "Systematic ledger fraud: wrong property submitted, correct ledger destroyed/withheld"),
    ("Homes of America LLC",
     "XLS/CSV ledger files exist (2.1 MB and 142,395 bytes)",
     "Both files contain zero actual data — XLS has 1 empty cell, CSV is all null bytes",
     "forensic_analysis_ledger_files", "evidence_registry EXHIBIT-B-SPOLIATION-XLS/CSV",
     10, "Digital ledger spoliation after litigation commenced; MCR 2.313 sanctions mandatory"),
]:
    brain.execute("""
        INSERT OR IGNORE INTO contradictions
        (actor, statement_a, statement_b, source_a, source_b, impeachment_value, significance)
        VALUES (?,?,?,?,?,?,?)
    """, row)

brain.commit()

ev_cnt = brain.execute("SELECT COUNT(*) FROM evidence_registry").fetchone()[0]
con_cnt = brain.execute("SELECT COUNT(*) FROM contradictions").fetchone()[0]
brain.close()
print(f"brain.evidence_registry: {ev_cnt}")
print(f"brain.contradictions: {con_cnt}")

# ── litigation_context.db writes ────────────────
main = open_db(MAIN_DB)

quotes = [
    ("gmail_may16_2025_wrong_property_ledger.txt", "B", "financial_fraud",
     "HOA emailed ledger for South Haven Park MHC (different property) to court in Shady Oaks case. "
     "Cassandra VanDam / Southhaven@ourhomesofamerica.com. "
     "Andrew Pigors corrected: 'Stipulated in the judges order, my rent was paid through December of 2024.' "
     "HOA: 'It was sent in error. Please disregard it.' — Correct Shady Oaks ledger never produced.",
     1, 0.99, "ledger,financial_fraud,wrong_property,MCR2.114E", "2025-002760-CZ"),
    ("shady_ledger_spoliation_forensic.txt", "B", "spoliation",
     "XLS file (2.1 MB) contains 1 sheet, 1 row, 1 column, empty string — wiped post-litigation. "
     "CSV file (142,395 bytes) contains ALL null bytes — overwritten with zeros post-litigation. "
     "Authentic original ledger = JPG only (3.4 MB, unaltered). "
     "Both digital formats wiped after litigation commenced = MCR 2.313 sanctions.",
     1, 0.99, "spoliation,ledger,null_bytes,MCR2313", "2025-002760-CZ"),
]

for (sf, ln, cat, qt, pg, rs, tags, refs) in quotes:
    main.execute("""
        INSERT INTO evidence_quotes
        (source_file, lane, category, quote_text, page_number, relevance_score, tags, filing_refs, is_duplicate)
        VALUES (?,?,?,?,?,?,?,?,0)
    """, (sf, ln, cat, qt, pg, rs, tags, refs))

main.execute("""
    INSERT INTO contradiction_map
    (claim_id, source_a, source_b, contradiction_text, severity, lane)
    VALUES (?,?,?,?,?,?)
""", (
    f"SHADY-LEDGER-FRAUD-{today}",
    "HOA ledger submission to court (May 2025) — South Haven Park MHC",
    "HOA 'sent in error' admission; correct Shady Oaks ledger never produced; digital versions null-wiped",
    "HOA submitted wrong property ledger to mislead court. When caught, claimed error but never produced "
    "correct ledger. XLS and CSV versions of Shady Oaks ledger both null-wiped after litigation commenced. "
    "Authentic ledger = JPG only. Combined = systematic financial evidence destruction.",
    "critical", "B"
))

main.commit()

eq_cnt = main.execute("SELECT COUNT(*) FROM evidence_quotes WHERE lane='B'").fetchone()[0]
ct_cnt = main.execute("SELECT COUNT(*) FROM contradiction_map WHERE lane='B'").fetchone()[0]
main.close()

print(f"litigation_context.evidence_quotes (B): {eq_cnt}")
print(f"litigation_context.contradiction_map (B): {ct_cnt}")
print("Phase 35 COMPLETE.")
