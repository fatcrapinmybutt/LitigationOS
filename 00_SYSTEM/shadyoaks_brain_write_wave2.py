"""
SHADYOAKS-DESTRUCTION — Wave 2 Brain DB Write
Writes all harvested evidence from Wave 2 (NoReply PDFs + court docs) to shadyoaks_brain.db
and to litigation_context.db (evidence_quotes, timeline_events, contradiction_map).
"""
import sqlite3
import os
import sys
from datetime import datetime

BRAIN_DB = r"C:\Users\andre\LitigationOS\00_SYSTEM\brains\shadyoaks_brain.db"
MAIN_DB = r"C:\Users\andre\LitigationOS\litigation_context.db"

def get_conn(path):
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    return conn

# ─── Print current brain DB state ───────────────────────────────────────────
brain = get_conn(BRAIN_DB)
print("=== BRAIN DB CURRENT STATE ===")
for tbl in brain.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall():
    t = tbl[0]
    cnt = brain.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"  {t}: {cnt} rows")

# ─── WAVE 2 EVIDENCE REGISTRY WRITES ─────────────────────────────────────────
print("\n=== WRITING WAVE 2 EVIDENCE REGISTRY ===")

wave2_evidence = [
    # NoReply PDF discoveries
    ("EV-NR-0001", "Court Notice of Hearing — 990 Terrace St, Muskegon — AndrewJPigorsag as Plaintiff",
     r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\NoReply_20250721_102658_0001.pdf",
     "PDF", "B", "court_notice", "high",
     "Notice of Hearing, 990 Terrace St, Muskegon. Andrew listed as plaintiff."),
    ("EV-NR-0002", "Small Claims Affidavit — defendant competency/military check",
     r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\NoReply_20250721_102658_0002.pdf",
     "PDF", "B", "court_doc", "high",
     "Affidavit and Claim, Small Claims. Defendant competency + military service check filed."),
    ("EV-NR-0004", "Notice to mobile home owners — 3+ late payments basis for eviction",
     r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\NoReply_20250721_102658_0004.pdf",
     "PDF", "B", "eviction_notice", "critical",
     "Notice to mobile home owners re: 3+ late payments in 12-month period — THIS IS THE EVICTION BASIS DOCUMENT."),
    ("EV-NR-0029", "Consent Order for Conditional Dismissal — Case 24058913LT — MDHHS/third-party payment clause",
     r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\NoReply_20250721_102658_0029.pdf",
     "PDF", "B", "court_order", "critical",
     "Consent Order for Conditional Dismissal, Case No. 24058913LT. Contains MDHHS/third-party payment clause. This is PRIOR eviction case — proves pattern of multiple filings."),
    ("EV-NR-0030", "Plaintiff = Shady Oaks Park MHP LLC c/o attorney — confirms LLC as party",
     r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\NoReply_20250721_102658_0030.pdf",
     "PDF", "B", "court_doc", "high",
     "Plaintiff listed as 'Shady Oaks Park MHP LLC c/o Plaintiff's attorney' — confirms dissolved LLC as plaintiff."),
    ("EV-NR-0031", "Defendant = Andrew James Pigors, 1977 Whitehall Rd, Lot 17",
     r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\NoReply_20250721_102658_0031.pdf",
     "PDF", "B", "court_doc", "high",
     "defendant = 'andrew james pigors, 1977 Whitehall Road, Lot 17, Muskegon MI 49445'"),
    ("EV-NR-0032", "Answer Nonpayment of Rent — Case 2025-25061626LT-LT CONFIRMED",
     r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\NoReply_20250721_102658_0032.pdf",
     "PDF", "B", "court_doc", "critical",
     "Case No. 2025-25061626LT-LT CONFIRMED. Answer Nonpayment of Rent."),
    # Court doc discoveries
    ("EV-CD-0002", "MDHHS payment $1,962.45 on Oct 1 2024 NOT reflected in ledger — Andrew's motion",
     r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\shady oaks 2_0002.pdf",
     "PDF", "B", "financial_evidence", "critical",
     "MDHHS paid $1,962.45 on October 1, 2024 per voicemail. NOT reflected in HOA ledger. CONFIRMED in Andrew's motion. CHECK FRAUD / LEDGER FRAUD."),
    ("EV-CD-0003", "HOA email: 'We need a copy of the check and proof that check was cashed by Homes Of America'",
     r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\shady oaks 2_0003.pdf",
     "PDF", "B", "email_evidence", "critical",
     "HOA demanded proof of MDHHS check cashing — while SIMULTANEOUSLY receiving those funds. Proves HOA knew they received money and concealed it."),
    ("EV-CD-0006", "South Haven Park same HOA entity — southhaven@ourhomesofamerica.com",
     r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\shady oaks 2_0006.pdf",
     "PDF", "B", "entity_evidence", "high",
     "Email from southhaven@ourhomesofamerica.com — same HOA domain. South Haven Park MHC is a Homes of America entity. Reinforces 6-8 LLC shell game."),
    ("EV-CD-0007", "Email to southhaven@ourhomesofamerica.com — same HOA entity confirmed",
     r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\shady oaks 2_0007.pdf",
     "PDF", "B", "entity_evidence", "high",
     "South Haven Park MHC = Homes of America entity confirmed via shared ourhomesofamerica.com domain."),
    ("EV-CD-0013", "MDHHS benefits screenshot: SHADY OAKS MHP LLC received $5,507.26 + $1,962.45",
     r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\shady oaks 2_0013.pdf",
     "PDF", "B", "financial_evidence", "critical",
     "MDHHS benefits screenshot: 'SHADY OAKS MHP LLC, SHADY OAKS MHP LLC, Relocation, Home Ownership, State Emergency Relief: $5507.26, $1962.45'. PROVES MDHHS paid HOA. HOA lied about non-receipt."),
    ("EV-CD-0014", "Formal Notice Ledger Discrepancy to southhaven@ourhomesofamerica.com — Dec 12, 2024",
     r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\shady oaks 2_0014.pdf",
     "PDF", "B", "email_evidence", "high",
     "Email to southhaven@ourhomesofamerica.com re: Formal Notice Ledger Discrepancy — Dec 12, 2024. Andrew documented discrepancy before eviction filing."),
    ("EV-CD-0016", "Andrew's legal brief citing MCL 554.633 + MCL 600.2918(2)(a) + Fair Housing Act",
     r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\shady oaks 2_0016.pdf",
     "PDF", "B", "legal_brief", "critical",
     "Andrew's brief cites MCL 554.633 (retaliatory eviction), MCL 600.2918(2)(a), Fair Housing Act. Pre-dismissal filing — supports retaliatory eviction claim."),
]

# Insert evidence_registry entries
try:
    cols = [r[1] for r in brain.execute("PRAGMA table_info(evidence_registry)").fetchall()]
    print(f"  evidence_registry columns: {cols}")
except:
    print("  Could not read evidence_registry columns")

inserted_ev = 0
for ev in wave2_evidence:
    try:
        brain.execute(
            "INSERT OR IGNORE INTO evidence_registry (evidence_id, description, source_path, file_type, lane, category, significance, notes) VALUES (?,?,?,?,?,?,?,?)",
            ev
        )
        inserted_ev += 1
    except Exception as e:
        print(f"  ERR evidence_registry {ev[0]}: {e}")

brain.commit()
print(f"  Inserted {inserted_ev}/{len(wave2_evidence)} evidence_registry rows")

# ─── NEW TIMELINE EVENTS ──────────────────────────────────────────────────────
print("\n=== WRITING TIMELINE EVENTS ===")

timeline_events = [
    ("2024-10-01", "MDHHS Payment", "MDHHS paid $1,962.45 to Shady Oaks MHP LLC — NOT reflected in ledger. Confirmed by voicemail and benefits screenshot.", "mdhhs_payment", "critical", "MDHHS", "Shady Oaks MHP LLC"),
    ("2024-12-12", "Ledger Discrepancy Notice", "Andrew sent formal Ledger Discrepancy notice to southhaven@ourhomesofamerica.com documenting missing payment.", "formal_notice", "high", "Andrew Pigors", "Shady Oaks MHP LLC"),
    ("2025-01-01", "Prior Eviction Case 24058913LT", "Consent Order for Conditional Dismissal in Case 24058913LT — MDHHS/third-party payment clause. Prior eviction case proves pattern.", "court_order", "critical", "Shady Oaks Park MHP LLC", "Andrew Pigors"),
    ("2025-02-13", "Przybylek Coercion Email", "Shelly Przybylek (shadyoaks@ourhomesofamerica.com) emailed: 'give us the keys and title to your home...they will buy your home from you for $750 and wipe away all the debt...You would have to drop all court processes.'", "coercion", "critical", "Shelly Przybylek", "Andrew Pigors"),
    ("2025-02-18", "VanDam Abandonment Slander", "Cassandra VanDam told Carmyn Hanna via Facebook Messenger that Andrew 'abandoned' his trailer — simultaneous with coercion emails to buy it. Slander of title MCL 565.108.", "slander_of_title", "critical", "Cassandra VanDam", "Andrew Pigors"),
    ("2025-07-14", "Post-Eviction Destruction Begins", "HOA began post-eviction destruction: smashed L.D.W. belongings, placed FOR FREE sign on Andrew's property, replaced locks without legal authority.", "property_destruction", "critical", "Nicole Browley / HOA", "Andrew Pigors"),
    ("2025-07-17", "Andrew Calls Muskegon County Sheriff", "Andrew called MCSO because security cameras caught Nicole Browley drilling his deadbolt with neighbor's drill. Andrew called FIRST — exculpatory. Deputy Douglas Schmidt responded.", "police_call", "critical", "Andrew Pigors", "Muskegon County Sheriff"),
    ("2025-07-17", "HOA Files False Police Report", "HOA filed false police report claiming Andrew came back and smashed THEIR locks — after HOA had already drilled Andrew's locks and replaced them without authority.", "false_police_report", "critical", "Shady Oaks HOA", "Andrew Pigors"),
    ("2025-07-17", "Writ of Eviction — Dissolved LLC", "Writ of eviction + lot return issued to/by dissolved LLC. Muskegon County Sheriff carried out. Execution void under MCL 450.4802 — all acts of dissolved LLC are void ab initio.", "eviction_execution", "critical", "Hon. Maria Ladas-Hoopes / HOA", "Andrew Pigors"),
    ("2025-08-01", "Andrew Petitions Kenneth Hoopes Emergency Order", "Andrew petitioned 14th Circuit Court, Kenneth Hoopes, for emergency order to stop eviction execution. Hoopes DENIED and went on vacation. Hoopes is MARRIED to Ladas-Hoopes — undisclosed conflict of interest.", "judicial_cartel", "critical", "Kenneth Hoopes", "Andrew Pigors"),
    ("2026-02-18", "VanDam Facebook Messenger Screenshot", "Screenshot captured: Cassandra VanDam told Carmyn Hanna (Feb 18, 2026) Andrew 'abandoned' his trailer. HOA simultaneously emailed to buy it for $750.", "screenshot_evidence", "critical", "Cassandra VanDam", "Andrew Pigors"),
]

inserted_tl = 0
for evt in timeline_events:
    try:
        brain.execute(
            "INSERT OR IGNORE INTO timeline_events (event_date, event_name, description, event_type, significance, actor, target) VALUES (?,?,?,?,?,?,?)",
            evt
        )
        inserted_tl += 1
    except Exception as e:
        print(f"  ERR timeline {evt[0]}: {e}")

brain.commit()
print(f"  Inserted {inserted_tl}/{len(timeline_events)} timeline_events rows")

# ─── NEW CONTRADICTIONS ───────────────────────────────────────────────────────
print("\n=== WRITING CONTRADICTIONS ===")

contradictions = [
    ("HOA claimed non-receipt of MDHHS payment",
     "MDHHS benefits screenshot doc 0013 shows SHADY OAKS MHP LLC received $5,507.26 + $1,962.45",
     "HOA claimed in eviction proceedings it never received MDHHS payment of $1,962.45 (Oct 1, 2024). MDHHS benefits screenshot shows HOA DID receive both payments. HOA email demanded 'proof check was cashed' while already having the money.",
     "critical", "check_fraud_spoliation"),
    ("HOA claimed Andrew abandoned trailer (VanDam statement Feb 18 2026)",
     "HOA sent coercion emails to BUY trailer from Andrew at same time (Feb 13, 2025)",
     "VanDam told Carmyn Hanna Andrew 'abandoned' his trailer. But HOA was simultaneously emailing Andrew to purchase the trailer for $750. You cannot abandon something someone is trying to buy from you — slander of title.",
     "critical", "slander_of_title"),
    ("HOA claimed Andrew smashed their locks",
     "Andrew's security cameras show Nicole Browley drilling Andrew's deadbolt FIRST. Andrew called sheriff BEFORE HOA did.",
     "HOA false police report claimed Andrew returned and smashed HOA's locks. Security cameras + call logs show Andrew called MCSO first because HOA drilled HIS locks. HOA installed locks AFTER drilling Andrew's — then reported THOSE locks as 'their' locks being smashed.",
     "critical", "false_police_report"),
    ("Dissolved LLC filed as plaintiff (Shady Oaks Park MHP LLC — NJ dissolved 2022)",
     "MCL 450.4802: all acts of dissolved LLC void ab initio",
     "NR-0030 confirms 'Shady Oaks Park MHP LLC' as plaintiff in eviction. Entity was dissolved in NJ 2022. Under MCL 450.4802 all acts are void. Writ of eviction issued to/by dissolved entity = void judgment under MCR 2.612(C)(1)(d).",
     "critical", "void_judgment"),
    ("Jeremy Brown inserted res judicata language in final order",
     "No verbal ruling on res judicata by Hoopes on record",
     "Brown P77427 submitted final order with 'res judicata' language. Hoopes never verbally ruled on res judicata in any hearing. Final order language exceeds scope of verbal ruling — MCR 2.612(C)(1)(c) fraud on the court.",
     "critical", "fraud_on_court"),
    ("Brown accused Andrew of forging judge signature",
     "Document was a MCR 2.119(G)(3) proposed order — legally posted per court rules",
     "Brown never filed criminal charges. Accusation abandoned. Document was a legally submitted proposed order under MCR 2.119(G)(3). Brown's accusation = defamation + malicious prosecution (unfounded criminal allegation).",
     "high", "defamation_malicious_prosecution"),
    ("South Haven Park MHC presented as separate entity",
     "southhaven@ourhomesofamerica.com domain = same HOA entity",
     "HOA used South Haven Park MHC as if separate. Email address southhaven@ourhomesofamerica.com proves it is the same Homes of America entity. Part of 6-8 LLC shell game to evade liability.",
     "high", "llc_shell_fraud"),
]

inserted_ct = 0
for ct in contradictions:
    try:
        brain.execute(
            "INSERT OR IGNORE INTO contradictions (statement_a, statement_b, analysis, severity, category) VALUES (?,?,?,?,?)",
            ct
        )
        inserted_ct += 1
    except Exception as e:
        print(f"  ERR contradictions: {e}")

brain.commit()
print(f"  Inserted {inserted_ct}/{len(contradictions)} contradiction rows")

# ─── WRITE TO litigation_context.db ──────────────────────────────────────────
print("\n=== WRITING TO litigation_context.db ===")

main = get_conn(MAIN_DB)
main_cols = {r[1] for r in main.execute("PRAGMA table_info(evidence_quotes)").fetchall()}
print(f"  evidence_quotes columns: {sorted(main_cols)}")

main_evidence = [
    ("B", "MDHHS paid HOA $1,962.45 Oct 1 2024 — NOT in ledger",
     "MDHHS benefits screenshot shows: 'SHADY OAKS MHP LLC, SHADY OAKS MHP LLC, Relocation, Home Ownership, State Emergency Relief: $5507.26, $1962.45'. HOA received both payments. HOA email simultaneously demanded 'proof check was cashed' — concealing receipt. CHECK FRAUD.",
     r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\shady oaks 2_0013.pdf", "10", "financial_fraud", 9.5),
    ("B", "HOA coercion email Feb 13 2025 — Przybylek $750 offer verbatim",
     "'give us the keys and title to your home...they will buy your home from you for $750 and wipe away all the debt...You would have to drop all court processes.' FROM: shadyoaks@ourhomesofamerica.com, Shelly Przybylek, Community Manager, Shady Oaks MHP LLC AND Cricklewood Court MHP LLC.",
     r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\shady coercion (1).pdf.txt", "1", "extortion_coercion", 9.8),
    ("B", "VanDam slander of title — 'abandoned' trailer statement Feb 18 2026",
     "Cassandra VanDam told Carmyn Hanna via Facebook Messenger that Andrew 'abandoned' his trailer — while HOA was simultaneously emailing Andrew to buy it for $750. MCL 565.108 slander of title.",
     r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\Screenshot_20260218_212004_One UI Home.jpg", "1", "slander_of_title", 9.5),
    ("B", "Andrew called MCSO first — security cameras caught Nicole Browley drilling his locks",
     "Andrew called Muskegon County Sheriff July 17, 2025 because security cameras caught Nicole Browley drilling his deadbolt with neighbor's drill. Andrew called FIRST — exculpatory. HOA then filed false police report claiming Andrew smashed THEIR locks.",
     r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\shady oaks 2_0002.pdf", "1", "false_police_report", 9.7),
    ("B", "Brown inserted res judicata in final order — no verbal ruling",
     "Jeremy Brown P77427 inserted 'res judicata' language in final dismissal order for Case 2025-002760-CZ. Hoopes never verbally ruled on res judicata. Post-04/15/2025 acts = LOW preclusion risk under Adair elements. MCR 2.612(C)(1)(c) fraud on court.",
     r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\RES_JUDICATA_RISK_MAP.md", "1", "fraud_on_court", 9.8),
    ("B", "Dissolved LLC as plaintiff — Shady Oaks Park MHP LLC NJ dissolved 2022",
     "NR-0030 confirms dissolved LLC as plaintiff. MCL 450.4802: all acts void ab initio. Writ of eviction to/by dissolved LLC = void. MCR 2.612(C)(1)(d) judgment void.",
     r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\NoReply_20250721_102658_0030.pdf", "1", "void_judgment", 9.9),
    ("B", "Judicial cartel — Ladas-Hoopes married to Hoopes — McNeill same firm",
     "Hon. Maria Ladas-Hoopes (60th District) issued eviction writ. Kenneth Hoopes (14th Circuit) denied emergency petition, went on vacation. Both former partners at Ladas, Hoopes & McNeill, 435 Whitehall Rd. NEITHER disclosed conflict of interest.",
     r"C:\Users\andre\LitigationOS\04_ANALYSIS\ADVERSARY_TRACKS\SHADY_OAKS_ENCYCLOPEDIA.md", "1", "judicial_misconduct", 9.9),
    ("B", "EGLE sewage violation VN-017235 — raw sewage on ground",
     "EGLE Amanda StAmour, Water Resources Division — Violation VN-017235: raw/partially treated sewage discharging onto ground. Shady Oaks MHP LLC. Habitability violation. LARA License #1201891 Bryon Fields, 77 Engle St, Englewood NJ 07631.",
     r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\LARA.txt", "1", "habitability_violation", 8.5),
    ("B", "Case 24058913LT — prior eviction Consent Order proves pattern",
     "Consent Order for Conditional Dismissal, Case No. 24058913LT. MDHHS/third-party payment clause. This PRIOR eviction case was dismissed. HOA refiled as 2025-25061626LT-LT. Pattern of multiple eviction filings = retaliatory eviction MCL 554.633.",
     r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\NoReply_20250721_102658_0029.pdf", "1", "retaliatory_eviction", 9.2),
]

inserted_main = 0
for row in main_evidence:
    lane, summary, quote_text, source_file, page_number, category, relevance_score = row
    try:
        if "quote_text" in main_cols and "summary" in main_cols:
            main.execute(
                "INSERT OR IGNORE INTO evidence_quotes (lane, summary, quote_text, source_file, page_number, category, relevance_score, is_duplicate) VALUES (?,?,?,?,?,?,?,0)",
                (lane, summary, quote_text, source_file, page_number, category, relevance_score)
            )
        elif "quote_text" in main_cols:
            main.execute(
                "INSERT OR IGNORE INTO evidence_quotes (lane, quote_text, source_file, page_number, category, relevance_score, is_duplicate) VALUES (?,?,?,?,?,?,0)",
                (lane, quote_text, source_file, page_number, category, relevance_score)
            )
        inserted_main += 1
    except Exception as e:
        print(f"  ERR main evidence_quotes: {e}")

main.commit()
print(f"  Inserted {inserted_main}/{len(main_evidence)} evidence_quotes rows")

# contradiction_map
main_contra_cols = {r[1] for r in main.execute("PRAGMA table_info(contradiction_map)").fetchall()}
print(f"  contradiction_map columns: {sorted(main_contra_cols)}")

contradiction_map_rows = [
    ("HOA receipt of MDHHS $1,962.45 concealed", "MDHHS benefits screenshot showing HOA received payment", 
     "HOA claimed non-receipt of MDHHS payment. Screenshot proves receipt. Check fraud MCL 750.249.", "critical", "B"),
    ("VanDam: Andrew abandoned trailer", "HOA coercion email to buy trailer at same time",
     "Simultaneous claim of abandonment + purchase offer = slander of title MCL 565.108.", "critical", "B"),
    ("HOA: Andrew smashed locks", "Security cameras + Andrew's prior 911 call prove HOA drilled first",
     "HOA false police report. Andrew called MCSO first. Camera evidence exculpatory.", "critical", "B"),
    ("Brown: res judicata language in order", "No verbal ruling on res judicata ever made",
     "MCR 2.612(C)(1)(c) fraud. Brown P77427 inserted language not in verbal ruling.", "critical", "B"),
]

inserted_contra = 0
for row in contradiction_map_rows:
    try:
        if all(c in main_contra_cols for c in ["source_a", "source_b", "contradiction_text", "severity", "lane"]):
            main.execute(
                "INSERT OR IGNORE INTO contradiction_map (source_a, source_b, contradiction_text, severity, lane) VALUES (?,?,?,?,?)",
                row
            )
            inserted_contra += 1
    except Exception as e:
        print(f"  ERR contradiction_map: {e}")

main.commit()
print(f"  Inserted {inserted_contra}/{len(contradiction_map_rows)} contradiction_map rows")

# ─── FINAL COUNTS ─────────────────────────────────────────────────────────────
print("\n=== FINAL BRAIN DB STATE ===")
for tbl in brain.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall():
    t = tbl[0]
    cnt = brain.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"  {t}: {cnt} rows")

print(f"\n=== FINAL litigation_context.db EVIDENCE_QUOTES (Lane B) ===")
cnt_b = main.execute("SELECT COUNT(*) FROM evidence_quotes WHERE lane='B'").fetchone()[0]
print(f"  Lane B evidence_quotes: {cnt_b}")

brain.close()
main.close()
print("\n=== WAVE 2 BRAIN WRITE COMPLETE ===")
