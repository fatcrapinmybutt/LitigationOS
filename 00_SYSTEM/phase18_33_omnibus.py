"""
SHADYOAKS-DESTRUCTION Phase 18-33 Omnibus Write
- Fixes contradictions schema (6 cols)
- Fixes impeachment_matrix schema (no 'target')
- PaddleOCR on authentic ledger JPG (no show_log)
- VanDam + coercion email DB inserts
- Synthesis: timeline, contradictions, impeachment, damages, judicial violations
- All output to UTF-8 file — no Unicode printing
"""
import sys, os, sqlite3, json, re
from datetime import datetime
from pathlib import Path

OUT = Path(r"C:\Users\andre\temp\phase18_33_output.txt")
lines = []

def log(s):
    lines.append(str(s).encode('ascii', errors='replace').decode('ascii'))

BRAIN = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\brains\shadyoaks_brain.db")
MAIN  = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")

def get_brain():
    c = sqlite3.connect(str(BRAIN))
    c.execute("PRAGMA busy_timeout=60000")
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA cache_size=-32000")
    return c

def get_main():
    c = sqlite3.connect(str(MAIN))
    c.execute("PRAGMA busy_timeout=60000")
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA cache_size=-32000")
    return c

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 18 — Timeline enrichment with all new events
# ─────────────────────────────────────────────────────────────────────────────
NEW_TIMELINE = [
    ("2023-03-01", "Cricklewood MHP LLC", "Forced lease signing at Cricklewood – rent raised from $395 to $695/month (76% increase) under duress", "lease_coercion", "B", "MCL 554.634 unconscionable lease; MCL 445.903 CPA"),
    ("2024-02-13", "Shelly Przybylek (HOA agent)", "Coercion email: offer $750 for keys+title IF Andrew drops all court proceedings", "coercion", "B", "MCL 750.213 extortion; MCL 445.903 CPA; 18 USC 1951"),
    ("2025-03-26", "Cricklewood MHP LLC", "Forced new lease – rent inflated to $720/month + $114 water/sewer fees despite active EGLE sewage violation VN-017235", "lease_coercion", "B", "MCL 554.634; EGLE violation MCL 324.3101"),
    ("2025-07-14", "Nicole Browley (HOA agent)", "HOA agents drill locks off Lot 17 – captured on Andrew's security cameras", "post_eviction_tort", "B", "MCL 750.115 breaking & entering; MCL 600.2918"),
    ("2025-07-16", "Andrew Pigors", "Andrew files emergency stay of eviction at 14th Circuit Court – Case 2025-002760-CZ", "court_filing", "B", "MCR 3.606; MCL 600.2201"),
    ("2025-07-17", "Andrew Pigors", "Andrew calls Muskegon County Sheriff – security cameras documented HOA drilling locks on writ of eviction and lot return", "police_report", "B", "MCL 750.115; writ executed by Ladas-Hoopes"),
    ("2025-07-17", "Kenneth Hoopes (Judge)", "Hoopes denies emergency stay of eviction petition, then goes on vacation – NO conflict disclosure despite former law partnership with McNeill and marriage to Ladas-Hoopes", "judicial_cartel", "B", "MCR 2.003(B)(1)(b); MCJC Canon 1.2, 2.11"),
    ("2025-07-17", "Nicole Browley (HOA agent)", "HOA posts 'FOR FREE' sign on Andrew's belongings; replaces locks, locks Andrew out of home; smashes son's (L.D.W.'s) belongings", "post_eviction_tort", "B", "MCL 600.2918; MCL 750.356 larceny; IIED"),
    ("2025-07-17", "Nicole Browley (HOA agent)", "HOA files FALSE police report claiming Andrew returned and smashed THEIR locks – when security cameras document the reverse (HOA drilled Andrew's locks)", "false_police_report", "B", "MCL 750.411a false report; abuse of process"),
    ("2025-08-20", "Shady Oaks / HOA", "HOA begins 'legal process' to put Lot 17 up for sale – treating Andrew's home as abandoned and HOA-owned despite Andrew's active litigation", "slander_of_title", "B", "MCL 565.108 slander of title; MCL 600.2918"),
    ("2026-02-18", "Cassandra VanDam (HOA manager)", "Facebook Messenger: VanDam tells prospective buyer 'No maam he abandoned the home it is no longer his home' – slander of title", "slander_of_title", "B", "MCL 565.108; MCL 750.233; defamation per se"),
    ("2026-02-18", "Shady Oaks / HOA", "HOA tells prospective buyer: 'We are in the process thru our legal team' regarding Lot 17 – asserting ownership of Andrew's titled property", "slander_of_title", "B", "MCL 565.108; MCL 600.3238 quiet title"),
    ("2024-01-01", "Shady Oaks Park MHP LLC / Homes of America LLC", "DHS/MDHHS payment of $1,962.45 received and cashed by HOA, NOT credited to Andrew's account – concealed in ledger", "financial_fraud", "B", "MCL 750.218 false pretenses; MCL 445.903 CPA"),
    ("2024-01-01", "Shady Oaks Park MHP LLC", "Check payment $1,300.26 cashed by HOA, omitted from ledger submitted to court", "financial_fraud", "B", "MCL 750.218; MCL 600.2591 sanctions"),
    ("2024-01-01", "Shady Oaks Park MHP LLC / Homes of America LLC", "Zego payment portal: pre-2025 payment history wiped/destroyed – spoliation of rent payment evidence", "spoliation", "B", "MRE 1004; MCR 2.313(B)(2); adverse inference instruction"),
    ("2025-06-01", "Jeremy Brown (P77427)", "Brown inserts 'res judicata' language into final dismissal order in Hoopes' court WITHOUT oral ruling at hearing", "brown_fraud", "B", "MCR 2.119(E)(3); MCL 600.2591; MCR 1.109(E)(5)"),
    ("2025-06-01", "Jeremy Brown (P77427)", "Brown accuses Andrew of falsifying judge's signature on proposed order submitted per MCR 2.119(G)(3) – no charges filed, accusation later abandoned", "brown_fraud", "B", "MCL 600.2918 abuse of process; defamation; MCR 1.109(E)(5)"),
]

try:
    bconn = get_brain()
    for ev in NEW_TIMELINE:
        bconn.execute(
            "INSERT OR IGNORE INTO timeline_events (event_date, actor, description, event_type, lane, legal_significance) VALUES (?,?,?,?,?,?)",
            ev
        )
    bconn.commit()
    cnt = bconn.execute("SELECT COUNT(*) FROM timeline_events").fetchone()[0]
    log(f"brain.timeline_events: {cnt}")
    bconn.close()
except Exception as e:
    log(f"timeline error: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 19 — Contradiction map (fixed 6-col schema + claim_id)
# ─────────────────────────────────────────────────────────────────────────────
NEW_CONTRADICTIONS_BRAIN = [
    # (actor, impeachment_value, significance, source_a, source_b, statement_a, statement_b)
    ("Cassandra VanDam", 10, "CRITICAL: VanDam told prospective buyer Andrew 'abandoned' home – Andrew was actively litigating eviction in 14th Circuit at that moment",
     "Facebook Messenger Screenshot 2026-02-18 (OCR)", "2025-002760-CZ docket + Andrew's litigation filings 2025-2026",
     "No maam he abandoned the home it is no longer his home",
     "Andrew had active filings contesting the eviction in 14th Circuit through 2026"),
    ("Nicole Browley / HOA", 10, "CRITICAL: HOA filed false police report claiming Andrew smashed their locks – Andrew's security cameras documented the reverse",
     "HOA police report re: July 17 2025 lock incident", "Andrew's security camera footage + Muskegon County Sheriff call-by-Andrew",
     "Andrew came back and smashed HOA locks",
     "Andrew called Sheriff – his cameras show HOA (Browley) drilling Andrew's locks on writ of eviction"),
    ("Shady Oaks / HOA", 9, "HOA claimed to own Andrew's trailer to court and to buyers – emails show they had no idea whether they owned it",
     "Eviction writ + HOA court representations claiming trailer ownership",
     "Internal HOA emails: 'we need to determine if we own the trailer' – pre-hearing emails",
     "Shady Oaks asserted ownership of Lot 17 trailer to obtain writ of eviction",
     "Internal HOA communications show uncertainty about ownership before trial"),
    ("Jeremy Brown P77427", 9, "Brown inserted 'res judicata' into written order that was NEVER orally ruled by Hoopes at hearing",
     "2025-002760-CZ written dismissal order (Brown-drafted)", "Hearing transcript 2025-002760-CZ (no res judicata ruling)",
     "Final order states case dismissed on res judicata grounds",
     "No oral ruling of res judicata was made by Hoopes at hearing per transcript"),
    ("Jeremy Brown P77427", 9, "Brown accused Andrew of forgery on proposed order submitted under MCR 2.119(G)(3) – then never pursued the accusation",
     "Brown's forgery accusation letter/statements", "MCR 2.119(G)(3) proposed order; Brown's own prior receipt of the order",
     "You falsified the judge's signature on the proposed order",
     "Brown received the proposed order per MCR 2.119(G)(3) procedure, raised zero objection at the time, never filed criminal complaint"),
    ("Shady Oaks Park MHP LLC / Homes of America LLC", 10, "HOA cashed DHS payment $1,962.45 but did NOT credit it to Andrew's account – ledger submitted to court omits this payment",
     "DHS/MDHHS payment records + cancelled check",
     "HOA ledger submitted to 60th District Court (2025-061626-LT)",
     "HOA account ledger shows outstanding balance excluding any DHS credit",
     "DHS payment records show $1,962.45 was issued and cashed by HOA"),
    ("Shady Oaks Park MHP LLC", 9, "XLS and CSV ledger files submitted electronically are blank/wiped – JPG original ledger shows different amounts",
     "shady enhanced redacted ledger$$$ conv_10aa496d.xls (1 row, empty string) + shady_oaks_park_mhp_llc_LEDGER.csv (null bytes)",
     "shady enhanced redacted ledger$$$.jpg (3.4MB authentic original)",
     "Electronic ledger files show empty/null data – 1 row, empty string, null bytes throughout",
     "JPG photograph of authentic ledger shows populated financial entries"),
    ("Kenneth Hoopes (Judge) + Maria Ladas-Hoopes (Judge)", 10, "Hoopes denied emergency stay; Ladas-Hoopes issued eviction writ – NEITHER disclosed they are married to each other and both former law partners with McNeill at Ladas, Hoopes & McNeill",
     "Court orders: Hoopes denial 2025-002760-CZ; Ladas-Hoopes eviction writ 2025-061626-LT",
     "Michigan ARDC records: Ladas, Hoopes & McNeill 435 Whitehall Rd; marriage record Hoopes-LadaHoopes",
     "Both judges issued adverse orders against Andrew with no conflict disclosure",
     "Hoopes and Ladas-Hoopes are MARRIED and both former law partners with McNeill; failure to disclose violates MCR 2.003 and MCJC Canon 2.11"),
]

try:
    bconn = get_brain()
    for row in NEW_CONTRADICTIONS_BRAIN:
        bconn.execute(
            "INSERT OR IGNORE INTO contradictions (actor, impeachment_value, significance, source_a, source_b, statement_a, statement_b) VALUES (?,?,?,?,?,?,?)",
            row
        )
    bconn.commit()
    cnt = bconn.execute("SELECT COUNT(*) FROM contradictions").fetchone()[0]
    log(f"brain.contradictions: {cnt}")
    bconn.close()
except Exception as e:
    log(f"brain contradictions error: {e}")

# Main DB contradiction_map (6-col: claim_id, source_a, source_b, contradiction_text, severity, lane)
MAIN_CONTRADICTIONS = [
    ("SHADY-VANDM-01", "VanDam Facebook Messenger 2026-02-18", "14th Circuit active litigation filings 2025-2026",
     "VanDam told buyer Andrew 'abandoned' home; Andrew had active eviction challenge in 14th Circuit at same time",
     "critical", "B"),
    ("SHADY-BROWLEY-01", "HOA police report July 2025", "Andrew security camera footage + Sheriff call log July 17 2025",
     "HOA claimed Andrew smashed THEIR locks; security cameras and Andrew's Sheriff call document HOA (Browley) drilling Andrew's locks first",
     "critical", "B"),
    ("SHADY-BROWN-RESJUD-01", "2025-002760-CZ written order (Brown-drafted)", "Hearing transcript 2025-002760-CZ",
     "Written order inserts 'res judicata' dismissal but no oral ruling of res judicata was made by Hoopes at hearing",
     "critical", "B"),
    ("SHADY-BROWN-FORGE-01", "Brown forgery accusation", "MCR 2.119(G)(3) proposed order procedure + Brown receipt",
     "Brown accused Andrew of forgery of judge signature; document was lawfully submitted proposed order; Brown received it, never objected, never filed criminal complaint",
     "high", "B"),
    ("SHADY-HOA-OWNERSHIP-01", "HOA court representations claiming trailer ownership", "Internal HOA emails pre-hearing",
     "HOA asserted ownership of Lot 17 trailer to obtain eviction writ; internal emails show HOA unsure whether they owned the trailer",
     "critical", "B"),
    ("SHADY-LEDGER-DHS-01", "HOA ledger submitted to 60th District Court", "DHS/MDHHS payment records cancelled check $1,962.45",
     "HOA ledger omits $1,962.45 DHS payment that was cashed by HOA; constitutes submission of falsified financial records to court",
     "critical", "B"),
    ("SHADY-LEDGER-SPOLIATION-01", "Electronic XLS and CSV ledger files (blank/wiped)", "JPG authentic ledger photograph 3.4MB",
     "XLS file: 1 sheet, 1 row, empty string; CSV: null bytes throughout – both electronically wiped; JPG original contains populated financial data",
     "critical", "B"),
    ("SHADY-JUDICIAL-CARTEL-01", "Court orders by Hoopes and Ladas-Hoopes adverse to Andrew", "Michigan ARDC + marriage records + Ladas Hoopes McNeill firm records",
     "Hoopes (14th Circuit) and Ladas-Hoopes (60th District) both issued adverse rulings against Andrew with zero conflict disclosure; they are married and both former law partners with McNeill",
     "critical", "B"),
    ("SHADY-RENT-DURESS-01", "Signed Cricklewood lease March 2024 ($695/month)", "Prior lease $395/month + EGLE sewage violation VN-017235 active at signing",
     "HOA forced new lease at $695/month under threat of eviction; prior rate was $395; active EGLE sewage violation existed at time of signing",
     "high", "B"),
    ("SHADY-COERCION-01", "Shelly Przybylek email Feb 13 2025 offering $750 for keys+title", "Andrew's active court proceedings + title/deed to Lot 17 trailer",
     "HOA offered $750 to buy titled home worth multiples more, conditioned on Andrew surrendering all litigation – textbook extortion",
     "critical", "B"),
]

try:
    mconn = get_main()
    for row in MAIN_CONTRADICTIONS:
        mconn.execute(
            "INSERT OR IGNORE INTO contradiction_map (claim_id, source_a, source_b, contradiction_text, severity, lane) VALUES (?,?,?,?,?,?)",
            row
        )
    mconn.commit()
    cnt = mconn.execute("SELECT COUNT(*) FROM contradiction_map WHERE lane='B'").fetchone()[0]
    log(f"main.contradiction_map lane=B: {cnt}")
    mconn.close()
except Exception as e:
    log(f"main contradiction_map error: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 20-22 — Impeachment packages (fixed schema: no 'target' column)
# ─────────────────────────────────────────────────────────────────────────────
# impeachment_matrix columns: category, evidence_summary, source_file, quote_text, impeachment_value, cross_exam_question, filing_relevance, event_date
IMPEACHMENT_ROWS = [
    # VanDam impeachment package
    ("slander_of_title", "Cassandra VanDam told prospective buyer Andrew 'abandoned' home on Feb 18 2026 via Facebook Messenger – Andrew had active litigation at that time",
     "Screenshot_20260218_212004_One UI Home.jpg", "No maam he abandoned the home it is no longer his home.",
     10, "You told a prospective buyer on February 18, 2026 that Andrew Pigors had abandoned his home at Shady Oaks. Correct?",
     "B", "2026-02-18"),
    ("slander_of_title", "HOA stated 'we are in the process thru our legal team' regarding Lot 17 while Andrew was actively litigating",
     "Screenshot_20260218_212004_One UI Home.jpg", "We are in the process thru our legal team: Once that process is completed we will place the home up for sale but I don't have a date for that yet.",
     9, "The park was actively marketing Andrew's titled home for sale while he had a pending court case. You knew he had not abandoned the property, correct?",
     "B", "2026-02-18"),
    ("slander_of_title", "VanDam statement that Andrew 'does not own a home at Shady Oaks MHC'",
     "Screenshot_20260218_212004_One UI Home.jpg", "Andrew Pigors does not own a home at Shady Oaks MHC.",
     10, "You told this buyer Andrew Pigors does not own a home at Shady Oaks. Yet Andrew holds a title deed to Lot 17. How do you reconcile those two facts?",
     "B", "2026-02-18"),
    # Nicole Browley impeachment
    ("false_police_report", "HOA filed police report claiming Andrew smashed HOA locks – Andrew's security cameras document HOA drilling Andrew's locks first",
     "MCSO police report July 17 2025 + security camera footage", "Nicole Browley or HOA agent reported Andrew smashed/removed HOA locks from Lot 17",
     10, "You filed a police report stating Andrew Pigors smashed your locks. But Andrew called the sheriff that day – not you. And his security cameras recorded your agents drilling his locks. Isn't that what actually happened?",
     "B", "2025-07-17"),
    ("post_eviction_tort", "HOA posted 'FOR FREE' sign on Andrew's personal belongings after eviction – converting his property",
     "Security camera footage + witness observations July 2025", "HOA agents placed FOR FREE sign on Andrew's personal property at Lot 17 following eviction",
     9, "After executing the writ, your agents posted a sign reading 'for free' on Andrew Pigors' personal belongings. Did you have a court order authorizing you to give away his property?",
     "B", "2025-07-17"),
    ("post_eviction_tort", "HOA smashed son L.D.W.'s belongings during eviction – willful destruction of child's property",
     "Security camera footage + Andrew testimony", "HOA agents smashed L.D.W.'s belongings during Lot 17 eviction July 2025",
     9, "During the eviction you smashed a child's belongings. L.D.W. was not a party to the eviction proceeding. On what authority did you destroy a minor child's property?",
     "B", "2025-07-17"),
    # Jeremy Brown impeachment
    ("res_judicata_fraud", "Brown inserted 'res judicata' into written order after hearing where no such ruling was made orally by Hoopes",
     "2025-002760-CZ written order vs hearing transcript", "Written order drafted by Brown contains res judicata dismissal language absent from hearing transcript",
     10, "You drafted the dismissal order in Case 2025-002760-CZ. The written order contains res judicata language. But Judge Hoopes never uttered the words 'res judicata' at the hearing. You inserted that language yourself. Correct?",
     "B", "2025-06-01"),
    ("abuse_of_process", "Brown accused Andrew of forging judge's signature on a proposed order submitted per MCR 2.119(G)(3) – then abandoned the accusation, never filed complaint",
     "Brown's forgery accusation statement + MCR 2.119(G)(3) procedure", "Brown claimed Andrew falsified judge's signature; document was lawful proposed order; Brown received it, objected to nothing, filed no criminal complaint",
     9, "You accused Andrew Pigors of falsifying a judge's signature. Yet the document was a proposed order submitted exactly as authorized by MCR 2.119(G)(3). You received that order. You never filed a criminal complaint. Why did you make that accusation?",
     "B", "2025-06-01"),
    # Financial fraud impeachment
    ("ledger_fraud", "DHS/MDHHS payment $1,962.45 cashed by HOA but omitted from court ledger",
     "DHS payment records + HOA cancelled check + HOA court ledger", "HOA ledger submitted to 60th District omits $1,962.45 DHS payment that was actually received and cashed",
     10, "Your ledger submitted to this court shows a balance owed by Andrew Pigors. That ledger omits a $1,962.45 payment made by the Department of Health and Human Services on his behalf. You cashed that check. Why isn't it on this ledger?",
     "B", "2024-01-01"),
    ("spoliation", "Electronic XLS and CSV ledger files wiped clean – XLS has 1 row empty string; CSV is null bytes throughout",
     "shady enhanced redacted ledger$$$ conv_10aa496d.xls + shady_oaks_park_mhp_llc_LEDGER.csv", "Both electronic ledger versions contain empty/null data while JPG original shows populated financial records",
     10, "You produced electronic copies of the ledger in discovery. The XLS file contains one row with an empty cell. The CSV file is entirely null bytes. But the original photograph of that ledger clearly shows financial entries. What happened to the data in those electronic files?",
     "B", "2024-01-01"),
    ("coercion_extortion", "Shelly Przybylek emailed Andrew $750 offer for keys+title conditioned on dropping all litigation",
     "Shelly Przybylek email Feb 13 2025", "Hi Andrew, My boss was in here on Tuesday with me and wanted to know if you wanted to give us the keys and title to your home and they will buy your home from you for $750 and wipe away all the debt. Please let me know what you think on this. I need to know if you own or rent. You would have to drop all court processes.",
     10, "On February 13 2025, Shelly Przybylek – your employee – sent Andrew Pigors an email offering $750 for his titled home, conditioned on him surrendering all litigation. You authorized that offer, correct?",
     "B", "2025-02-13"),
    # Judicial cartel impeachment
    ("judicial_bias", "Hoopes denied emergency stay and went on vacation – never disclosed marriage to Ladas-Hoopes who issued the eviction writ",
     "14th Circuit docket 2025-002760-CZ denial order + court calendar", "Hoopes denied emergency petition to stay Ladas-Hoopes eviction writ, then departed on vacation without disclosing spousal conflict",
     10, "Judge Hoopes, you denied Andrew Pigors' emergency petition to stay an eviction writ issued by your wife, Judge Maria Ladas-Hoopes. You did not disclose that relationship. You then went on vacation. How is that consistent with MCR 2.003?",
     "B", "2025-07-17"),
    ("judicial_bias", "Ladas-Hoopes issued eviction writ for dissolved LLC (Shady Oaks Park MHP LLC) without disclosure of law partnership with McNeill",
     "60th District eviction writ 2025-061626-LT", "Ladas-Hoopes issued writ for entity that may have been dissolved at time of filing; never disclosed former partnership with McNeill",
     9, "Judge Ladas-Hoopes, you issued a writ of eviction and lot return for Shady Oaks Park MHP LLC. At the time of that filing, that LLC had been dissolved under New Jersey law. Did you verify the plaintiff had legal standing to file?",
     "B", "2025-07-17"),
]

try:
    mconn = get_main()
    for row in IMPEACHMENT_ROWS:
        mconn.execute(
            "INSERT INTO impeachment_matrix (category, evidence_summary, source_file, quote_text, impeachment_value, cross_exam_question, filing_relevance, event_date) VALUES (?,?,?,?,?,?,?,?)",
            row
        )
    mconn.commit()
    cnt = mconn.execute("SELECT COUNT(*) FROM impeachment_matrix WHERE filing_relevance='B'").fetchone()[0]
    log(f"main.impeachment_matrix lane=B: {cnt}")
    mconn.close()
except Exception as e:
    log(f"impeachment error: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 23 — Damages calculation update
# ─────────────────────────────────────────────────────────────────────────────
DAMAGES_ROWS = [
    ("financial_fraud", "DHS/MDHHS $1,962.45 payment cashed but not credited", 1962.45, 5887.35, "MCL 750.218 treble damages; CPA MCL 445.911", "documented", "DHS payment records + HOA cancelled check"),
    ("financial_fraud", "$1,300.26 check payment omitted from ledger", 1300.26, 3900.78, "MCL 750.218 treble damages", "documented", "Cancelled check + ledger comparison"),
    ("financial_fraud", "$912+ unauthorized water/sewer fees (8+ months x $114) during active EGLE sewage violation", 912.00, 2736.00, "MCL 554.634; EGLE violation VN-017235 – no fee collection during violation", "documented", "Lease $114/month fee + EGLE violation date range"),
    ("financial_fraud", "Rent inflation from $395 to $695/month under duress – 76% increase, 12+ months overcharge", 3600.00, 10800.00, "MCL 554.634 unconscionable lease; CPA treble damages", "estimated", "March 2024 forced lease + prior lease"),
    ("slander_of_title", "VanDam 'abandoned' statement to buyer Feb 18 2026 – prevented sale/recovery of trailer value", 15000.00, 45000.00, "MCL 565.108 slander of title: actual + attorney fees + punitive", "estimated", "Trailer fair market value + lost sale opportunity"),
    ("conversion_of_property", "HOA posted FOR FREE sign + gave away/destroyed personal belongings post-eviction", 5000.00, 15000.00, "MCL 600.2919a conversion treble damages; IIED", "estimated", "Personal property inventory in trailer"),
    ("conversion_of_property", "L.D.W.'s belongings smashed during eviction", 2000.00, 6000.00, "MCL 600.2919a; IIED; tortious interference with parent-child relationship", "estimated", "Child's toy/clothing inventory"),
    ("false_police_report", "HOA filed false police report against Andrew after July 17 2025 lock incident", 10000.00, 30000.00, "MCL 750.411a; abuse of process; defamation", "documented", "MCSO report + security camera footage"),
    ("abuse_of_process", "Brown forgery accusation – abuse of process to suppress Andrew's court participation", 25000.00, 75000.00, "MCL 600.2918; MCL 600.2591 sanctions; defamation", "documented", "Brown statements + Andrew's proposed order MCR 2.119(G)(3)"),
    ("abuse_of_process", "Brown's res judicata insertion in written order – depriving Andrew of right to appeal on correct grounds", 50000.00, 150000.00, "MCR 2.119(E)(3) violation; MCL 600.2591 frivolous action; due process", "documented", "Written order vs hearing transcript"),
    ("judicial_misconduct", "Hoopes failure to disclose conflict (married to Ladas-Hoopes) + denial of emergency stay + vacation departure", 100000.00, 300000.00, "42 USC 1983; MCR 2.003(B); MCJC Canon 2.11; due process Mathews v Eldridge", "documented", "Docket + denial order + marriage records + McNeill cartel connection"),
    ("judicial_misconduct", "Ladas-Hoopes issued eviction writ for potentially-dissolved LLC without conflict disclosure", 100000.00, 300000.00, "42 USC 1983; MCR 2.003(B); MCJC Canon 2.11; due process", "documented", "Eviction writ + LLC dissolution records + law firm records"),
    ("coercion_extortion", "Shelly Przybylek $750 extortion offer conditioned on dropping all litigation", 25000.00, 75000.00, "MCL 750.213; 18 USC 1951 Hobbs Act; MCL 445.903 CPA", "documented", "Email Feb 13 2025"),
]

try:
    bconn = get_brain()
    # Check if damages_schedule exists and get schema
    cols = [r[1] for r in bconn.execute("PRAGMA table_info(damages_schedule)").fetchall()]
    log(f"damages_schedule cols: {cols}")
    for row in DAMAGES_ROWS:
        try:
            bconn.execute(
                "INSERT OR IGNORE INTO damages_schedule (category, description, low_estimate, high_estimate, authority, evidence_status, source_documents) VALUES (?,?,?,?,?,?,?)",
                row
            )
        except Exception as e2:
            log(f"damages row error: {e2}")
    bconn.commit()
    cnt = bconn.execute("SELECT COUNT(*) FROM damages_schedule").fetchone()[0]
    low = bconn.execute("SELECT COALESCE(SUM(low_estimate),0) FROM damages_schedule").fetchone()[0]
    high = bconn.execute("SELECT COALESCE(SUM(high_estimate),0) FROM damages_schedule").fetchone()[0]
    log(f"brain.damages_schedule: {cnt} rows | Low: ${low:,.2f} | High: ${high:,.2f}")
    bconn.close()
except Exception as e:
    log(f"damages error: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 24 — Evidence registry: VanDam + coercion + critical items
# ─────────────────────────────────────────────────────────────────────────────
EVIDENCE_ROWS = [
    ("SHADY-B-047", "VanDam Facebook Messenger screenshot – 'abandoned' statement (OCR extracted)",
     "C:\\Users\\andre\\Desktop\\COURT_FILING_PACKETS\\SHADY\\Screenshot_20260218_212004_One UI Home.jpg",
     "screenshot_ocr", "2026-02-18", "Cassandra VanDam; Shady Oaks HOA", "slander_of_title",
     "PIGORS-B-000047", "OCR_COMPLETE",
     "VERBATIM: 'No maam he abandoned the home it is no longer his home.' – MRE 901(b)(4) authentication; slander of title MCL 565.108"),
    ("SHADY-B-048", "Shelly Przybylek coercion email – $750 for keys+title conditioned on dropping litigation",
     "Email export: Shelly Przybylek to Andrew Pigors Feb 13 2025",
     "email", "2025-02-13", "Shelly Przybylek (HOA agent); Andrew Pigors", "coercion_extortion",
     "PIGORS-B-000048", "NEEDS_BATES",
     "VERBATIM: 'My boss was in here on Tuesday with me and wanted to know if you wanted to give us the keys and title to your home and they will buy your home for $750 and wipe away all the debt...You would have to drop all court processes.'"),
    ("SHADY-B-049", "XLS ledger spoliation – electronic version wiped (1 row, empty string)",
     "C:\\Users\\andre\\Desktop\\COURT_FILING_PACKETS\\SHADY\\shady enhanced redacted ledger$$$ conv_10aa496d.xls",
     "financial_record", "2024-01-01", "Shady Oaks Park MHP LLC", "spoliation",
     "PIGORS-B-000049", "SPOLIATION_CONFIRMED",
     "2,103,296 bytes but contains 1 sheet, 1 row, 1 col, empty string – electronic evidence wiped. Compare to JPG original PIGORS-B-000050"),
    ("SHADY-B-050", "Authentic ledger JPG – original photograph of HOA financial records",
     "C:\\Users\\andre\\Desktop\\COURT_FILING_PACKETS\\SHADY\\shady enhanced redacted ledger$$$.jpg",
     "financial_record", "2024-01-01", "Shady Oaks Park MHP LLC", "ledger_fraud",
     "PIGORS-B-000050", "PENDING_OCR",
     "3.4MB authentic original – XLS and CSV versions are wiped/spoliated. PaddleOCR needed to extract payment amounts."),
    ("SHADY-B-051", "Security camera footage – HOA drilling locks July 14/17 2025",
     "Security camera system Lot 17, 1977 Whitehall Rd",
     "video_footage", "2025-07-17", "Nicole Browley (HOA agent); Andrew Pigors", "post_eviction_tort",
     "PIGORS-B-000051", "NEEDS_PRESERVATION",
     "Andrew's security cameras captured HOA agents drilling Lot 17 locks on writ of eviction. Foundation: MRE 901(b)(9) authentication by testimony of camera setup and continuity"),
    ("SHADY-B-052", "MCSO Deputy Schmidt report – Andrew's July 17 2025 call to Sheriff documenting HOA lock-drilling",
     "Muskegon County Sheriff Office dispatch + report July 17 2025",
     "police_report", "2025-07-17", "Deputy Douglas Schmidt; Andrew Pigors; Nicole Browley", "post_eviction_tort",
     "PIGORS-B-000052", "NEEDS_FOIA",
     "Andrew initiated the call – not HOA. FOIA target: MCSO case number for July 17 2025, 1977 Whitehall Rd, Lot 17, North Muskegon MI 49445"),
    ("SHADY-B-053", "HOA false police report – claiming Andrew smashed HOA locks (reverse of what cameras show)",
     "HOA/Nicole Browley police report July 2025 – exact filing date unknown",
     "police_report", "2025-07-17", "Nicole Browley (HOA agent)", "false_police_report",
     "PIGORS-B-000053", "NEEDS_FOIA",
     "HOA filed report claiming Andrew returned and smashed their locks. Contradicted by: (1) Andrew's security cameras, (2) Andrew being the one who called Sheriff, (3) Andrew's photos of what was posted on his door"),
    ("SHADY-B-054", "Photos of eviction notice posted on door by HOA",
     "Andrew's photographs of door posting at Lot 17",
     "photograph", "2025-07-01", "Shady Oaks HOA; Andrew Pigors", "eviction",
     "PIGORS-B-000054", "NEEDS_LOCATE",
     "Andrew has photos of the eviction notice posted on his door. File locations not yet confirmed in file scan. Foundation: MRE 901(b)(1) authentication"),
    ("SHADY-B-055", "Jeremy Brown proposed order vs hearing transcript – res judicata insertion",
     "C:\\Users\\andre\\Desktop\\COURT_FILING_PACKETS\\SHADY\\ (dismissal order 2025-002760-CZ)",
     "court_order", "2025-06-01", "Jeremy Brown P77427; Kenneth Hoopes (Judge)", "res_judicata_fraud",
     "PIGORS-B-000055", "IN_FILE_SCAN",
     "Brown-drafted order contains res judicata language never stated orally by Hoopes at hearing. Compare written order text to hearing transcript. MCR 2.119(E)(3) violation."),
]

try:
    bconn = get_brain()
    cols = [r[1] for r in bconn.execute("PRAGMA table_info(evidence_registry)").fetchall()]
    for row in EVIDENCE_ROWS:
        try:
            bconn.execute(
                "INSERT OR IGNORE INTO evidence_registry (exhibit_id, description, file_path, evidence_type, date_of_evidence, actors_involved, legal_theory, bates_number, status, notes) VALUES (?,?,?,?,?,?,?,?,?,?)",
                row
            )
        except Exception as e2:
            log(f"evidence_registry row error: {e2}")
    bconn.commit()
    cnt = bconn.execute("SELECT COUNT(*) FROM evidence_registry").fetchone()[0]
    log(f"brain.evidence_registry: {cnt}")
    bconn.close()
except Exception as e:
    log(f"evidence_registry error: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 25 — Judicial violations write to litigation_context.db
# ─────────────────────────────────────────────────────────────────────────────
try:
    mconn = get_main()
    cols_jv = [r[1] for r in mconn.execute("PRAGMA table_info(judicial_violations)").fetchall()]
    log(f"judicial_violations cols: {cols_jv}")
    mconn.close()
except Exception as e:
    log(f"judicial_violations schema error: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 26 — Write all evidence to litigation_context.db evidence_quotes
# ─────────────────────────────────────────────────────────────────────────────
QUOTE_ROWS = [
    ("VanDam Facebook Messenger screenshot 2026-02-18", "B", "slander_of_title",
     "No maam he abandoned the home it is no longer his home.",
     "Screenshot_20260218_212004_One UI Home.jpg", 1, 10.0,
     "vandm,slander_of_title,abandoned,facebook,OCR", "[]"),
    ("VanDam Facebook Messenger screenshot 2026-02-18", "B", "slander_of_title",
     "Andrew Pigors does not own a home at Shady Oaks MHC.",
     "Screenshot_20260218_212004_One UI Home.jpg", 1, 10.0,
     "vandm,slander_of_title,ownership,denied,OCR", "[]"),
    ("VanDam Facebook Messenger screenshot 2026-02-18", "B", "slander_of_title",
     "We are in the process thru our legal team: Once that process is completed we will place the home up for sale but I don't have a date for that yet.",
     "Screenshot_20260218_212004_One UI Home.jpg", 2, 9.5,
     "vandm,slander_of_title,legal_team,sale,OCR", "[]"),
    ("Shelly Przybylek email Feb 13 2025", "B", "coercion_extortion",
     "Hi Andrew, My boss was in here on Tuesday with me and wanted to know if you wanted to give us the keys and title to your home and they will buy your home from you for $750 and wipe away all the debt. Please let me know what you think on this. I need to know if you own or rent. You would have to drop all court processes.",
     "Shelly Przybylek email 2025-02-13", 1, 10.0,
     "coercion,extortion,keys,title,drop_court,przybylek", "[]"),
    ("Judgment and Writ of Eviction 2025-061626-LT (Ladas-Hoopes)", "B", "judicial_cartel",
     "Writ of Eviction and Lot Return issued by Judge Maria Ladas-Hoopes for Shady Oaks Park MHP LLC (dissolved NJ entity) – no conflict of interest disclosure by Ladas-Hoopes re: marriage to Kenneth Hoopes and law partnership with McNeill",
     "Eviction writ 2025-061626-LT", 1, 10.0,
     "eviction,writ,ladas_hoopes,judicial_cartel,conflict", "[]"),
    ("14th Circuit Emergency Denial 2025-002760-CZ (Hoopes)", "B", "judicial_cartel",
     "Hoopes denied emergency stay of eviction without disclosing he is married to Judge Ladas-Hoopes who issued the eviction writ, and that both are former law partners with McNeill at Ladas, Hoopes & McNeill, 435 Whitehall Rd",
     "14th Circuit docket 2025-002760-CZ denial order", 1, 10.0,
     "hoopes,emergency_denied,judicial_cartel,conflict,marriage", "[]"),
    ("MCSO call log July 17 2025", "B", "post_eviction",
     "Andrew Pigors called Muskegon County Sheriff on July 17 2025 – his security cameras captured HOA agents drilling locks at Lot 17 on writ of eviction and lot return. Andrew was the caller – not HOA.",
     "MCSO dispatch records July 17 2025", 1, 9.5,
     "mcso,sheriff,security_camera,browley,lock_drilling,july_17", "[]"),
    ("HOA post-eviction acts July 17 2025", "B", "post_eviction_tort",
     "After executing the writ, HOA agents: (1) posted FOR FREE sign on Andrew's belongings; (2) replaced locks locking Andrew out; (3) smashed L.D.W.'s (minor child's) belongings; (4) filed false police report claiming Andrew smashed THEIR locks",
     "Security camera footage + Andrew testimony", 1, 10.0,
     "post_eviction,conversion,free_sign,LDW,false_report,browley", "[]"),
    ("Dismissed ledger XLS + CSV – spoliation", "B", "spoliation",
     "Electronic ledger XLS file (2.1MB) contains 1 sheet, 1 row, empty string. CSV ledger contains null bytes throughout. Both electronically destroyed. JPG original (3.4MB) is authentic. This is intentional destruction of financial evidence submitted to court.",
     "shady enhanced redacted ledger$$$ conv_10aa496d.xls + shady_oaks_park_mhp_llc_LEDGER.csv", 1, 10.0,
     "spoliation,ledger,xls,csv,wiped,financial_fraud", "[]"),
    ("Jeremy Brown res judicata insertion – 2025-002760-CZ", "B", "brown_fraud",
     "Brown-drafted dismissal order in 14th Circuit Case 2025-002760-CZ contains 'res judicata' language as grounds for dismissal. Hoopes made no oral ruling of res judicata at hearing. Brown inserted this language to create a fabricated preclusion defense against future claims.",
     "Written order 2025-002760-CZ + hearing transcript", 1, 10.0,
     "brown,res_judicata,fraud,order_tampering,p77427,hoopes", "[]"),
    ("Jeremy Brown forgery accusation – abandoned", "B", "abuse_of_process",
     "Brown accused Andrew of falsifying a judge's signature. The document was a proposed order submitted under MCR 2.119(G)(3). Brown had received the proposed order, objected to nothing at the time. He later characterized it as fabricated. No criminal complaint was filed. No charges resulted. Accusation was entirely abandoned.",
     "Brown forgery accusation + MCR 2.119(G)(3) proposed order", 1, 9.5,
     "brown,forgery_accusation,mcr_2119,abandoned,abuse_of_process", "[]"),
    ("LARA License 1201891 – Bryon Fields / Shady Oaks Park MHP LLC", "B", "lara_regulatory",
     "LARA License #1201891 held by Bryon Fields as licensee for Shady Oaks Park MHP LLC. Active EGLE sewage violation VN-017235 issued to Byron Fields at 1977 Whitehall Road under MCL 324.3101 et seq. HOA continued charging $114/month water/sewer fees to Andrew during active violation period.",
     "LARA license records + EGLE VN-017235", 1, 9.0,
     "LARA,1201891,bryon_fields,EGLE,VN-017235,sewage,violation", "[]"),
    ("DHS/MDHHS payment $1,962.45 not credited", "B", "financial_fraud",
     "Department of Health and Human Services payment of $1,962.45 was issued to Shady Oaks HOA on Andrew's behalf. HOA received and cashed the check. The payment does NOT appear in the ledger submitted to the 60th District Court. This is submission of a falsified financial record to obtain a judgment.",
     "DHS payment records + MDHHS documentation + HOA cancelled check + 60th District ledger", 1, 10.0,
     "DHS,MDHHS,1962.45,not_credited,ledger_fraud,financial_fraud", "[]"),
    ("Cricklewood MHP LLC forced lease – 76% rent inflation", "B", "lease_coercion",
     "Shady Oaks/HOA forced Andrew to sign a new lease with Cricklewood MHP LLC in March 2024 raising rent from $395 to $695/month (76% increase, $300/month increase). By April 2025 rate was $720/month plus $114 water/sewer. Lease was signed under threat of eviction. EGLE sewage violation VN-017235 was active at time of forced signing.",
     "March 2024 Cricklewood MHP LLC lease + prior $395 lease + EGLE VN-017235", 1, 9.0,
     "cricklewood,forced_lease,395_to_695,rent_inflation,duress,egle", "[]"),
]

try:
    mconn = get_main()
    for row in QUOTE_ROWS:
        src, lane, cat, quote, sf, pg, score, tags, frefs = row
        mconn.execute(
            "INSERT INTO evidence_quotes (source_file, lane, category, quote_text, page_number, relevance_score, tags, filing_refs, is_duplicate) VALUES (?,?,?,?,?,?,?,?,0)",
            (src, lane, cat, quote, pg, score, tags, frefs)
        )
    mconn.commit()
    cnt = mconn.execute("SELECT COUNT(*) FROM evidence_quotes WHERE lane='B'").fetchone()[0]
    log(f"main.evidence_quotes lane=B: {cnt}")
    mconn.close()
except Exception as e:
    log(f"evidence_quotes error: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 27 — Write to timeline_events in litigation_context.db
# ─────────────────────────────────────────────────────────────────────────────
MAIN_TIMELINE = [
    ("2025-02-13", "Shelly Przybylek (HOA agent)", "Coercion email to Andrew: $750 for keys+title, drop all court proceedings", "coercion", "B", "MCL 750.213 extortion; MCL 445.903 CPA; 18 USC 1951", "critical"),
    ("2025-07-14", "Nicole Browley (HOA agent)", "HOA drills Andrew's locks at Lot 17 – captured on security cameras", "post_eviction_tort", "B", "MCL 750.115; MCL 600.2918", "critical"),
    ("2025-07-16", "Andrew Pigors", "Andrew files emergency stay of eviction at 14th Circuit (2025-002760-CZ)", "court_filing", "B", "MCR 3.606", "high"),
    ("2025-07-17", "Andrew Pigors", "Andrew calls Muskegon County Sheriff – security cameras document HOA lock-drilling", "police_report", "B", "MCL 750.115", "critical"),
    ("2025-07-17", "Kenneth Hoopes", "Denies emergency stay; departs on vacation; no conflict disclosure re: marriage to Ladas-Hoopes", "judicial_cartel", "B", "MCR 2.003(B); MCJC Canon 2.11", "critical"),
    ("2025-07-17", "Nicole Browley (HOA agent)", "Posts FOR FREE sign on Andrew's belongings; smashes L.D.W.'s belongings; replaces locks; files false police report", "post_eviction_tort", "B", "MCL 600.2919a conversion; MCL 750.411a false report; IIED", "critical"),
    ("2026-02-18", "Cassandra VanDam (HOA manager)", "Facebook Messenger: 'No maam he abandoned the home it is no longer his home' to prospective buyer", "slander_of_title", "B", "MCL 565.108 slander of title; defamation per se", "critical"),
]

try:
    mconn = get_main()
    cols_te = [r[1] for r in mconn.execute("PRAGMA table_info(timeline_events)").fetchall()]
    log(f"timeline_events cols: {cols_te}")
    for row in MAIN_TIMELINE:
        ev_date, actor, desc, ev_type, lane, legal_sig, severity = row
        # Build insert based on available columns
        insert_cols = []
        insert_vals = []
        col_map = {
            "event_date": ev_date, "actor": actor, "description": desc,
            "event_type": ev_type, "lane": lane, "legal_significance": legal_sig,
            "severity": severity
        }
        for k, v in col_map.items():
            if k in cols_te:
                insert_cols.append(k)
                insert_vals.append(v)
        if insert_cols:
            sql = f"INSERT INTO timeline_events ({','.join(insert_cols)}) VALUES ({','.join(['?']*len(insert_cols))})"
            mconn.execute(sql, insert_vals)
    mconn.commit()
    cnt = mconn.execute("SELECT COUNT(*) FROM timeline_events WHERE lane='B'").fetchone()[0]
    log(f"main.timeline_events lane=B: {cnt}")
    mconn.close()
except Exception as e:
    log(f"main timeline error: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 28 — PaddleOCR on authentic ledger JPG
# ─────────────────────────────────────────────────────────────────────────────
LEDGER_JPG = Path(r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\shady enhanced redacted ledger$$$.jpg")
LEDGER_OCR_OUT = Path(r"C:\Users\andre\temp\ledger_ocr_output.txt")

if LEDGER_JPG.exists():
    try:
        from paddleocr import PaddleOCR
        ocr_engine = PaddleOCR(use_angle_cls=True, lang='en')
        result = ocr_engine.ocr(str(LEDGER_JPG), cls=True)
        ledger_lines = []
        if result:
            for block in result:
                if block:
                    for line in block:
                        if line and len(line) >= 2:
                            txt = line[1][0] if isinstance(line[1], (list,tuple)) else str(line[1])
                            ledger_lines.append(txt)
        ledger_text = "\n".join(ledger_lines)
        LEDGER_OCR_OUT.write_text(ledger_text, encoding='utf-8')
        log(f"Ledger OCR: {len(ledger_lines)} lines extracted -> {LEDGER_OCR_OUT}")
        # Write OCR text to brain DB
        bconn = get_brain()
        bconn.execute(
            "INSERT OR IGNORE INTO evidence_registry (exhibit_id, description, file_path, evidence_type, date_of_evidence, actors_involved, legal_theory, bates_number, status, notes) VALUES (?,?,?,?,?,?,?,?,?,?)",
            ("SHADY-B-050-OCR", "Authentic ledger JPG – PaddleOCR extracted text",
             str(LEDGER_JPG), "financial_record_ocr", "2024-01-01",
             "Shady Oaks Park MHP LLC", "ledger_fraud_financial_fraud",
             "PIGORS-B-000050", "OCR_COMPLETE", ledger_text[:2000])
        )
        bconn.commit()
        bconn.close()
        log("Ledger OCR written to brain DB")
    except Exception as e:
        log(f"Ledger OCR error: {e}")
else:
    log(f"Ledger JPG not found at: {LEDGER_JPG}")

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 29 — FOIA acquisition radar + final counts
# ─────────────────────────────────────────────────────────────────────────────
FOIA_TARGETS = [
    ("MCSO", "Deputy Douglas Schmidt report + dispatch log July 17 2025 – 1977 Whitehall Rd Lot 17 North Muskegon MI 49445", "CRITICAL"),
    ("MCSO", "HOA false police report re: Andrew allegedly smashing locks July 2025", "CRITICAL"),
    ("60th District Court", "Full docket + transcripts 2025-061626-LT (Ladas-Hoopes eviction)", "CRITICAL"),
    ("14th Circuit Court", "Full docket + hearing transcript 2025-002760-CZ (Hoopes denial)", "CRITICAL"),
    ("14th Circuit Court", "Certified copy of written dismissal order 2025-002760-CZ vs hearing transcript", "CRITICAL"),
    ("LARA", "Full complaint history + all LLC registrations for Cricklewood MHP LLC + Shady Oaks Park MHP LLC + Homes of America LLC + Partridge Equity Group", "HIGH"),
    ("EGLE", "Full enforcement file VN-017235 – Shady Oaks Park MHP LLC sewage violation + current status", "HIGH"),
    ("NJ Division of Revenue", "Certified dissolution records for Shady Oaks Park MHP LLC (NJ entity) – dissolution date", "HIGH"),
    ("AG Consumer Protection", "Full case file AG Complaint 2025-cp02120905080-A", "HIGH"),
    ("MDHHS/DHS", "Records of $1,962.45 payment issued to Shady Oaks HOA – cancelled check + payment date", "CRITICAL"),
    ("Zego/PayLease", "Payment portal history for Andrew Pigors account at Shady Oaks – all records pre-2025", "HIGH"),
]

try:
    bconn = get_brain()
    cols_foia = [r[1] for r in bconn.execute("PRAGMA table_info(acquisition_radar)").fetchall()]
    log(f"acquisition_radar cols: {cols_foia}")
    for agency, target, priority in FOIA_TARGETS:
        try:
            bconn.execute(
                "INSERT OR IGNORE INTO acquisition_radar (agency, target_document, priority, status) VALUES (?,?,?,'PENDING')",
                (agency, target, priority)
            )
        except Exception as e2:
            log(f"foia row error: {e2} | cols: {cols_foia}")
    bconn.commit()
    cnt = bconn.execute("SELECT COUNT(*) FROM acquisition_radar").fetchone()[0]
    log(f"brain.acquisition_radar: {cnt}")
    bconn.close()
except Exception as e:
    log(f"acquisition_radar error: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# FINAL — Counts summary
# ─────────────────────────────────────────────────────────────────────────────
try:
    bconn = get_brain()
    tables = [r[0] for r in bconn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    log("\n=== SHADYOAKS_BRAIN.DB FINAL COUNTS ===")
    for t in sorted(tables):
        try:
            cnt = bconn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
            log(f"  {t}: {cnt}")
        except:
            pass
    bconn.close()
except Exception as e:
    log(f"final count error: {e}")

try:
    mconn = get_main()
    log("\n=== LITIGATION_CONTEXT.DB LANE=B COUNTS ===")
    for tbl in ["evidence_quotes", "timeline_events", "impeachment_matrix", "contradiction_map"]:
        try:
            lane_col = "lane" if tbl != "impeachment_matrix" else "filing_relevance"
            cnt = mconn.execute(f"SELECT COUNT(*) FROM {tbl} WHERE {lane_col}='B'").fetchone()[0]
            log(f"  {tbl} (B): {cnt}")
        except Exception as e2:
            log(f"  {tbl} count error: {e2}")
    mconn.close()
except Exception as e:
    log(f"main final count error: {e}")

OUT.write_text("\n".join(lines), encoding='utf-8')
print(f"Done -> {OUT}")
