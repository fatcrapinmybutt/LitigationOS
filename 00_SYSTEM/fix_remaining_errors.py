"""
Fix remaining Phase 18-33 errors:
1. damages_schedule - wrong columns (has: claim, legal_authority, damages_conservative, damages_aggressive, multiplier, notes)
2. acquisition_radar - table doesn't exist in shadyoaks_brain.db (need to create it)
3. Verify coercion_emails table and populate
4. Create acquisition_radar in brain DB
"""
import sqlite3
import os
import sys

BRAIN_DB = r"C:\Users\andre\LitigationOS\00_SYSTEM\brains\shadyoaks_brain.db"
MAIN_DB  = r"C:\Users\andre\LitigationOS\litigation_context.db"

out = []

# ── BRAIN DB ──────────────────────────────────────────────────────────────────
bc = sqlite3.connect(BRAIN_DB)
bc.execute("PRAGMA journal_mode=WAL")
bc.execute("PRAGMA busy_timeout=60000")
bc.execute("PRAGMA cache_size=-32000")

# 1. Show actual damages_schedule columns
cols = [r[1] for r in bc.execute("PRAGMA table_info(damages_schedule)")]
out.append(f"damages_schedule cols: {cols}")

# 2. Populate damages_schedule with correct column mapping
# columns: id(auto), claim, legal_authority, damages_conservative, damages_aggressive, multiplier, notes
damages_rows = [
    ("Wrongful Eviction",            "MCL 600.5720; MCR 4.201",                  25000,  75000,  1.0, "Lock drilling July 14/17"),
    ("Slander of Title",             "MCL 565.108; Restatement 624",             50000,  150000, 2.0, "VanDam: 'abandoned the home' Feb 18 2026"),
    ("CPA Violations",               "MCL 445.911",                              10000,  50000,  3.0, "Treble damages; Shelly $750 coercion offer"),
    ("Financial Fraud/Ledger",       "MCL 440.1306; MCL 600.2918",               25000,  75000,  2.0, "DHS $1962.45 not credited; $1300.26 omitted"),
    ("Conversion of Personal Property","MCL 600.2919a",                          15000,  50000,  2.0, "Post-eviction: son's belongings smashed, free sign"),
    ("Illegal Lockout",              "MCL 600.2918",                             10000,  30000,  1.0, "Lock drilling before lawful eviction date"),
    ("False Police Report",          "MCL 750.411a; MCL 600.2907",               25000,  100000, 2.0, "HOA claimed Andrew smashed their locks"),
    ("Spoliation of Evidence",       "MCR 2.313; SJI2d 6.01",                   15000,  50000,  1.5, "Zego portal wiped; XLS/CSV ledgers emptied"),
    ("Res Judicata Insertion",       "MCR 2.612(C)(1)(c); MCL 600.2918",        25000,  100000, 2.0, "Brown inserted RJ in order without oral ruling"),
    ("Forgery Allegation Abuse",     "MCR 1.109(E)(5); MCL 750.248",            10000,  50000,  2.0, "Brown defamation re: MCR 2.119(G)(3) proposed order"),
    ("EGLE Violation Exposure",      "MCL 324.3112; MCL 445.911",                5000,   25000,  1.5, "VN-017235 sewage while charging $114 water/sewer fee"),
    ("Judicial Cartel / Due Process","42 USC 1983; US Const. XIV",              100000, 500000, 3.0, "Hoopes denied emergency stay; Ladas-Hoopes issued eviction — no conflict disclosure"),
    ("Treble CPA Aggregate",         "MCL 445.911(2)",                          45000,  225000, 3.0, "3x CPA base damages"),
]
inserted = 0
errors   = 0
for row in damages_rows:
    try:
        bc.execute(
            "INSERT OR IGNORE INTO damages_schedule (claim,legal_authority,damages_conservative,damages_aggressive,multiplier,notes) VALUES (?,?,?,?,?,?)",
            row
        )
        inserted += 1
    except Exception as e:
        errors += 1
        out.append(f"damages err: {e}")
bc.commit()
out.append(f"damages_schedule inserted: {inserted}, errors: {errors}")
out.append(f"damages_schedule total: {bc.execute('SELECT COUNT(*) FROM damages_schedule').fetchone()[0]}")

# 3. Create acquisition_radar in brain DB if missing
bc.execute("""
CREATE TABLE IF NOT EXISTS acquisition_radar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_type TEXT,
    agency TEXT,
    description TEXT,
    priority TEXT,
    status TEXT DEFAULT 'PENDING',
    foia_method TEXT,
    expected_content TEXT,
    created_at TEXT DEFAULT (datetime('now'))
)
""")
bc.commit()
out.append("acquisition_radar table created/verified")

# 4. Populate acquisition_radar
foia_rows = [
    ("police_report", "MUSKEGON COUNTY SHERIFF", "Deputy Douglas Schmidt report — July 17 2025 lock drilling call by Andrew", "CRITICAL", "PENDING", "FOIA MCL 15.231", "Confirms Andrew called MCSO; HOA drilled locks before lawful date"),
    ("police_report", "MUSKEGON COUNTY SHERIFF", "HOA false police report — claiming Andrew smashed locks post-eviction", "CRITICAL", "PENDING", "FOIA MCL 15.231", "HOA retaliation; cross-ref with Schmidt report"),
    ("dispatch_records", "MUSKEGON COUNTY SHERIFF", "Dispatch audio/CAD July 17 2025 — Shady Oaks / 1977 Whitehall Rd Lot 17", "HIGH", "PENDING", "FOIA MCL 15.231", "Exact timeline of Andrew's call vs HOA arrival"),
    ("payment_records", "MICHIGAN DHHS/DHS", "DHS rental assistance payment $1,962.45 — cashed but not credited", "CRITICAL", "PENDING", "FOIA MCL 15.231", "Wire transfer / check records to Shady Oaks; constitutes embezzlement"),
    ("court_record", "60th DISTRICT COURT", "Eviction docket 2025-061626-LT — full file including exhibits submitted by HOA", "CRITICAL", "PENDING", "Court FOIA / court access", "HOA title claims — prove they didn't know if they owned trailer"),
    ("court_record", "14th CIRCUIT COURT", "Case 2025-002760-CZ — hearing transcript oral argument vs Brown's written order", "CRITICAL", "PENDING", "Court FOIA / court reporter", "Compare oral ruling vs res judicata language Brown inserted"),
    ("corporate_records", "MICHIGAN LARA", "All Shady Oaks LLC filings — all 6-8 entities, annual reports, dissolution docs", "HIGH", "PENDING", "LARA FOIA", "Entity chain; who was licensed at time of eviction"),
    ("financial_records", "ZEGO/PROPTECH", "Historical payment portal records for Lot 17 2022-2025", "HIGH", "PENDING", "Subpoena", "Pre-2025 history wiped — constitutes spoliation"),
    ("security_footage", "SHADY OAKS MHP LLC", "Security camera footage July 14-17 2025 — lock drilling event", "CRITICAL", "PENDING", "Litigation hold / subpoena", "HOA's own cameras may show lock drilling"),
    ("financial_records", "ALDEN GLOBAL CAPITAL", "Lot 17 acquisition price; allocation in $275M deal", "MEDIUM", "PENDING", "Subpoena", "Show Andrew's trailer value in acquisition"),
    ("email_records", "SHADY OAKS / HOA", "All HOA emails re Lot 17 — coercion, sale negotiations, title confusion", "CRITICAL", "PENDING", "Subpoena / litigation hold", "Shelly Przybylek + Cassandra VanDam full email chains"),
]
fi_ins = 0
fi_err = 0
for row in foia_rows:
    try:
        bc.execute(
            "INSERT INTO acquisition_radar (target_type,agency,description,priority,status,foia_method,expected_content) VALUES (?,?,?,?,?,?,?)",
            row
        )
        fi_ins += 1
    except Exception as e:
        fi_err += 1
        out.append(f"foia err: {e}")
bc.commit()
out.append(f"acquisition_radar inserted: {fi_ins}, errors: {fi_err}")
out.append(f"acquisition_radar total: {bc.execute('SELECT COUNT(*) FROM acquisition_radar').fetchone()[0]}")

# 5. Populate coercion_emails (was 0)
try:
    ce_cols = [r[1] for r in bc.execute("PRAGMA table_info(coercion_emails)")]
    out.append(f"coercion_emails cols: {ce_cols}")
except:
    out.append("coercion_emails table missing - creating")
    bc.execute("""
    CREATE TABLE IF NOT EXISTS coercion_emails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT, sender TEXT, recipient TEXT, subject TEXT,
        body_excerpt TEXT, legal_significance TEXT, lane TEXT DEFAULT 'B',
        created_at TEXT DEFAULT (datetime('now'))
    )""")
    bc.commit()

ce_cols = [r[1] for r in bc.execute("PRAGMA table_info(coercion_emails)")]
out.append(f"coercion_emails cols after ensure: {ce_cols}")

coercion_data = [
    ("2025-02-13", "Shelly Przybylek (Shady Oaks Manager)",  "Andrew Pigors",
     "Settlement Proposal — Lot 17",
     "give us the keys and title to your home...they will buy your home from you for $750 and wipe away all the debt...You would have to drop all court processes.",
     "Extortion / coercion: conditioning financial settlement on dismissal of all pending court proceedings. Violates MCL 750.213 (extortion), MCL 445.911 (CPA unfair trade practice), MCR 1.109(E)(5) (improper threat)."),
    ("2026-02-18", "Cassandra VanDam (Shady Oaks Agent)", "Prospective Buyer",
     "Lot 17 availability inquiry (Facebook Messenger)",
     "No maam he abandoned the home it is no longer his home. Andrew Pigors does not own a home at Shady Oaks MHC. We are in the process thru our legal team: Once that process is completed we will place the home up for sale but I don't have a date for that yet.",
     "Slander of title: Public false statement that Andrew abandoned and no longer owns Lot 17 trailer. MCL 565.108; MCL 600.2911 (defamation). Andrew did NOT abandon — forcibly evicted after contested proceedings."),
    ("2025-01-01", "Shady Oaks HOA (via email)",            "Andrew Pigors",
     "Lot 17 purchase offer — pre-hearing",
     "[Emails indicating HOA attempted to purchase/coerce transfer of trailer prior to eviction hearing. Exact text TBD pending full email extraction.]",
     "Pre-hearing coercion: Attempting to force private sale before exhausting litigation. Undermines MCL 554.131 mobile home residency rights."),
]
ce_ins = 0
for row in coercion_data:
    try:
        bc.execute(
            "INSERT INTO coercion_emails (date,sender,recipient,subject,body_excerpt,legal_significance) VALUES (?,?,?,?,?,?)",
            row
        )
        ce_ins += 1
    except Exception as e:
        out.append(f"coercion err: {e}")
bc.commit()
out.append(f"coercion_emails inserted: {ce_ins}")
out.append(f"coercion_emails total: {bc.execute('SELECT COUNT(*) FROM coercion_emails').fetchone()[0]}")

# 6. Add judicial_violations to litigation_context.db for Hoopes + Ladas-Hoopes
mc = sqlite3.connect(MAIN_DB)
mc.execute("PRAGMA journal_mode=WAL")
mc.execute("PRAGMA busy_timeout=60000")
mc.execute("PRAGMA cache_size=-32000")

jv_rows = [
    ("CONFLICT_NON_DISCLOSURE", "Judge Maria Ladas-Hoopes issued eviction writ (2025-061626-LT) in 60th District Court for Shady Oaks MHP LLC. Ladas-Hoopes is former partner at Ladas, Hoopes & McNeill, 435 Whitehall Rd. LLC's attorney Jeremy Brown (P77427) has direct ties to the firm. No conflict of interest disclosure made.", "2025-07-14", "MCR 2.003; MCJC Canon 2.11", "MCJC Canon 2.11(A) - disqualification required when judge's impartiality might be questioned", "2025-061626-LT eviction docket", "Eviction writ issued without conflict disclosure; Ladas-Hoopes-McNeill partnership = undisclosed conflict", "CRITICAL", "B"),
    ("CONFLICT_NON_DISCLOSURE", "Judge Kenneth Hoopes denied Andrew's emergency petition to stay eviction (Case 2025-002760-CZ). Kenneth Hoopes is former law partner of Ladas-Hoopes AND McNeill at same firm. Then went on vacation. No conflict disclosure. Andrew had no remedy in 14th Circuit because both circuit judges = former partners.", "2025-07-14", "MCR 2.003; MCR 3.310(C)", "MCJC Canon 2.11(A); MCR 2.003(C)(1)(b) - bias or appearance of partiality", "2025-002760-CZ emergency petition record", "Denied emergency stay; went on vacation; Hoopes-McNeill-Ladas partnership undisclosed", "CRITICAL", "B"),
    ("IMPROPER_ORDER_LANGUAGE", "Jeremy Brown (P77427), attorney for Shady Oaks, inserted 'res judicata' into final dismissal order in Case 2025-002760-CZ without that doctrine being argued orally or ruled upon by Judge Hoopes. Order language expands scope of dismissal beyond what was ruled.", "2025-01-01", "MCR 2.612(C)(1)(c)", "MCR 2.119(C) - proposed orders must conform to court's ruling; MCL 600.2918 - abuse of process", "2025-002760-CZ final order", "Res judicata inserted without oral ruling — constitutes fraud on the court", "CRITICAL", "B"),
]
jv_ins = 0
for row in jv_rows:
    try:
        mc.execute(
            "INSERT INTO judicial_violations (violation_type,description,date_occurred,mcr_rule,canon,source_file,source_quote,severity,lane) VALUES (?,?,?,?,?,?,?,?,?)",
            row
        )
        jv_ins += 1
    except Exception as e:
        out.append(f"jv err: {e}")
mc.commit()
out.append(f"judicial_violations (housing) inserted: {jv_ins}")

# ── FINAL COUNTS ──────────────────────────────────────────────────────────────
bc2 = sqlite3.connect(BRAIN_DB)
brain_tables = [r[0] for r in bc2.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
out.append("\n=== BRAIN DB FINAL COUNTS ===")
for t in brain_tables:
    cnt = bc2.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
    out.append(f"  {t}: {cnt}")

out.append("\n=== LITIGATION_CONTEXT LANE=B COUNTS ===")
for tbl in ["evidence_quotes","timeline_events","impeachment_matrix","contradiction_map","judicial_violations"]:
    try:
        cnt = mc.execute(f"SELECT COUNT(*) FROM {tbl} WHERE lane='B'").fetchone()[0]
        out.append(f"  {tbl} (B): {cnt}")
    except Exception as e:
        out.append(f"  {tbl}: {e}")

bc.close(); mc.close(); bc2.close()

out_path = r"C:\Users\andre\temp\fix_remaining_output.txt"
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("DONE")
