"""
SHADYOAKS-DESTRUCTION — Wave 2 Brain DB Write (schema-corrected)
Uses PRAGMA table_info to map correct columns before every write.
"""
import sqlite3

BRAIN_DB = r"C:\Users\andre\LitigationOS\00_SYSTEM\brains\shadyoaks_brain.db"
MAIN_DB  = r"C:\Users\andre\LitigationOS\litigation_context.db"

def get_conn(p):
    c = sqlite3.connect(p)
    c.execute("PRAGMA busy_timeout=60000")
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA cache_size=-32000")
    return c

def cols(c, tbl):
    return {r[1] for r in c.execute(f"PRAGMA table_info({tbl})").fetchall()}

brain = get_conn(BRAIN_DB)
main  = get_conn(MAIN_DB)

# ── introspect brain tables ───────────────────────────────────────────────────
er_cols  = cols(brain, "evidence_registry")
tl_cols  = cols(brain, "timeline_events")
ct_cols  = cols(brain, "contradictions")
print("evidence_registry cols:", sorted(er_cols))
print("timeline_events cols:  ", sorted(tl_cols))
print("contradictions cols:   ", sorted(ct_cols))

# ── EVIDENCE REGISTRY ─────────────────────────────────────────────────────────
# actual cols: id, exhibit_id, description, file_path, evidence_type,
#              date_of_evidence, actors_involved, legal_theory, bates_number, status, notes

ev_rows = [
    ("EV-NR-0001", "Court Notice of Hearing — 990 Terrace St, Muskegon",
     r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\NoReply_20250721_102658_0001.pdf",
     "PDF", "2025-07-21", "Shady Oaks MHP LLC", "retaliatory_eviction", "PIGORS-B-0001", "indexed",
     "Notice of Hearing, 990 Terrace St. Andrew listed as plaintiff."),
    ("EV-NR-0004", "Notice — 3+ late payments basis for eviction (mobile home owners notice)",
     r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\NoReply_20250721_102658_0004.pdf",
     "PDF", "2025-07-21", "Shady Oaks MHP LLC", "retaliatory_eviction", "PIGORS-B-0004", "indexed",
     "EVICTION BASIS DOCUMENT — 3+ late payments in 12-month period notice to mobile home owners."),
    ("EV-NR-0029", "Consent Order for Conditional Dismissal — Case 24058913LT — MDHHS payment clause",
     r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\NoReply_20250721_102658_0029.pdf",
     "PDF", "2024-01-01", "60th District Court", "void_judgment", "PIGORS-B-0029", "indexed",
     "PRIOR eviction case 24058913LT. MDHHS/third-party payment clause. Pattern of multiple filings = retaliatory eviction MCL 554.633."),
    ("EV-NR-0030", "Plaintiff = Shady Oaks Park MHP LLC — dissolved NJ 2022",
     r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\NoReply_20250721_102658_0030.pdf",
     "PDF", "2025-07-21", "Shady Oaks Park MHP LLC", "void_judgment", "PIGORS-B-0030", "indexed",
     "Dissolved LLC as plaintiff. MCL 450.4802 all acts void ab initio. MCR 2.612(C)(1)(d) void judgment."),
    ("EV-NR-0032", "Answer Nonpayment of Rent — Case 2025-25061626LT-LT CONFIRMED",
     r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\NoReply_20250721_102658_0032.pdf",
     "PDF", "2025-07-21", "Shady Oaks Park MHP LLC", "retaliatory_eviction", "PIGORS-B-0032", "indexed",
     "Case No. 2025-25061626LT-LT CONFIRMED."),
    ("EV-CD-0002", "MDHHS payment $1,962.45 Oct 1 2024 — NOT in ledger",
     r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\shady oaks 2_0002.pdf",
     "PDF", "2024-10-01", "MDHHS / Shady Oaks MHP LLC", "check_fraud", "PIGORS-B-0002", "critical",
     "MDHHS paid $1,962.45 Oct 1 2024. Not in ledger. Check fraud MCL 750.249."),
    ("EV-CD-0003", "HOA demanded 'proof check was cashed' — while holding the money",
     r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\shady oaks 2_0003.pdf",
     "PDF", "2024-10-01", "Shady Oaks MHP LLC", "check_fraud", "PIGORS-B-0003", "critical",
     "HOA email: 'We need a copy of the check and proof that check was cashed by Homes Of America' — while simultaneously receiving those funds."),
    ("EV-CD-0013", "MDHHS screenshot — HOA received $5507.26 + $1962.45",
     r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\shady oaks 2_0013.pdf",
     "PDF", "2024-10-01", "MDHHS", "check_fraud", "PIGORS-B-0013", "critical",
     "MDHHS benefits: 'SHADY OAKS MHP LLC...State Emergency Relief: $5507.26, $1962.45'. Proof HOA received payments it denied."),
    ("EV-CD-0016", "Andrew's brief — MCL 554.633 retaliatory eviction + Fair Housing Act",
     r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\shady oaks 2_0016.pdf",
     "PDF", "2025-04-15", "Andrew Pigors", "retaliatory_eviction", "PIGORS-B-0016", "indexed",
     "Brief citing MCL 554.633 (retaliatory eviction), MCL 600.2918(2)(a), Fair Housing Act. Pre-dismissal filing."),
    ("EV-COERCE-001", "Przybylek coercion email — $750 buy offer",
     r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\shady coercion (1).pdf.txt",
     "TXT", "2025-02-13", "Shelly Przybylek / Homes of America", "extortion", "PIGORS-B-C001", "critical",
     "FROM: shadyoaks@ourhomesofamerica.com. $750 offer. Drop all court cases. MCL 750.213 extortion + RICO predicate."),
    ("EV-VANDM-001", "VanDam Facebook Messenger screenshot — abandonment slander Feb 18 2026",
     r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\Screenshot_20260218_212004_One UI Home.jpg",
     "JPG", "2026-02-18", "Cassandra VanDam", "slander_of_title", "PIGORS-B-V001", "critical",
     "VanDam told Carmyn Hanna Andrew 'abandoned' trailer. Simultaneous with $750 purchase offer. MCL 565.108 slander of title."),
]

er_insert = 0
for r in ev_rows:
    exhibit_id, description, file_path, evidence_type, date_of_evidence, actors_involved, legal_theory, bates_number, status, notes = r
    try:
        brain.execute(
            "INSERT OR IGNORE INTO evidence_registry (exhibit_id, description, file_path, evidence_type, date_of_evidence, actors_involved, legal_theory, bates_number, status, notes) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (exhibit_id, description, file_path, evidence_type, date_of_evidence, actors_involved, legal_theory, bates_number, status, notes)
        )
        er_insert += 1
    except Exception as e:
        print(f"  ERR evidence_registry {exhibit_id}: {e}")

brain.commit()
print(f"evidence_registry: inserted {er_insert}/{len(ev_rows)}")

# ── TIMELINE EVENTS ───────────────────────────────────────────────────────────
print("timeline_events cols:", sorted(tl_cols))
# Will adaptive-insert based on what cols exist
tl_rows = [
    ("2024-10-01", "MDHHS paid $1,962.45 to HOA — not in ledger", "MDHHS", "Shady Oaks MHP LLC", "check_fraud", "critical"),
    ("2024-12-12", "Andrew sent formal Ledger Discrepancy notice to southhaven@ourhomesofamerica.com", "Andrew Pigors", "Shady Oaks MHP LLC", "disputed_ledger", "high"),
    ("2025-01-01", "Prior eviction Case 24058913LT — Consent Order dismissed with MDHHS payment clause", "Shady Oaks Park MHP LLC", "Andrew Pigors", "retaliatory_eviction", "critical"),
    ("2025-02-13", "Przybylek coercion email: $750 buy offer, drop all court cases", "Shelly Przybylek", "Andrew Pigors", "extortion", "critical"),
    ("2025-02-18", "VanDam told Carmyn Hanna Andrew 'abandoned' trailer via Facebook Messenger", "Cassandra VanDam", "Andrew Pigors", "slander_of_title", "critical"),
    ("2025-07-14", "Post-eviction destruction: smashed L.D.W. belongings, FOR FREE sign, replaced locks", "Nicole Browley / HOA", "Andrew Pigors", "property_destruction", "critical"),
    ("2025-07-17", "Andrew called Muskegon County Sheriff — security cameras caught Nicole Browley drilling his deadbolt", "Andrew Pigors", "Muskegon County Sheriff", "police_call_exculpatory", "critical"),
    ("2025-07-17", "HOA filed false police report: claimed Andrew smashed their locks — REVERSED", "Shady Oaks HOA", "Andrew Pigors", "false_police_report", "critical"),
    ("2025-07-17", "Writ of eviction + lot return executed by MCSO for dissolved LLC — void ab initio", "Hon. Maria Ladas-Hoopes", "Andrew Pigors", "void_judgment", "critical"),
    ("2025-08-01", "Kenneth Hoopes denied Andrew's emergency petition — went on vacation — undisclosed conflict", "Kenneth Hoopes", "Andrew Pigors", "judicial_cartel", "critical"),
]

# Map cols to a safe insert
tl_insert = 0
for r in tl_rows:
    event_date, description, actor, target, event_type, significance = r
    # Build adaptive insert
    fields, vals = [], []
    for col, val in [("event_date", event_date), ("description", description), ("actor", actor),
                     ("target", target), ("event_type", event_type), ("significance", significance)]:
        if col in tl_cols:
            fields.append(col)
            vals.append(val)
    # also try common aliases
    for alias, val in [("date", event_date), ("details", description), ("summary", description)]:
        if alias in tl_cols and alias not in fields:
            fields.append(alias)
            vals.append(val)
    if not fields:
        print(f"  SKIP timeline: no matching cols for {event_date}")
        continue
    ph = ",".join("?" * len(fields))
    try:
        brain.execute(f"INSERT INTO timeline_events ({','.join(fields)}) VALUES ({ph})", vals)
        tl_insert += 1
    except Exception as e:
        print(f"  ERR timeline {event_date}: {e}")

brain.commit()
print(f"timeline_events: inserted {tl_insert}/{len(tl_rows)}")

# ── CONTRADICTIONS ────────────────────────────────────────────────────────────
ct_insert = 0
ct_data = [
    ("HOA claimed no receipt of MDHHS $1,962.45", "MDHHS screenshot proves SHADY OAKS MHP LLC received $5,507.26 + $1,962.45", "critical", "check_fraud"),
    ("VanDam: Andrew abandoned trailer", "HOA coercion email offering to buy trailer at same time — cannot abandon what they're trying to buy", "critical", "slander_of_title"),
    ("HOA: Andrew smashed their locks", "Andrew's security cameras + MCSO call log prove Andrew called first; Nicole Browley drilled Andrew's locks first", "critical", "false_police_report"),
    ("Brown: res judicata in final order", "Hoopes never verbally ruled on res judicata — Brown inserted language beyond verbal ruling", "critical", "fraud_on_court"),
    ("Shady Oaks Park MHP LLC valid plaintiff", "LLC dissolved NJ 2022 — MCL 450.4802 all acts void ab initio", "critical", "void_judgment"),
    ("Brown: Andrew forged judge signature", "Document was MCR 2.119(G)(3) proposed order — legally submitted. Brown never filed charges.", "high", "defamation"),
    ("South Haven Park MHC is separate entity", "southhaven@ourhomesofamerica.com domain proves same Homes of America entity — LLC shell game", "high", "fraud"),
]

for r in ct_data:
    sa, sb, sev, cat = r
    flds, vls = [], []
    for col, val in [("statement_a", sa), ("statement_b", sb), ("severity", sev), ("category", cat)]:
        if col in ct_cols:
            flds.append(col); vls.append(val)
    # common aliases
    for a, v in [("claim_a", sa), ("claim_b", sb), ("source_a", sa), ("source_b", sb)]:
        if a in ct_cols and a not in flds:
            flds.append(a); vls.append(v)
    if not flds:
        print(f"  SKIP contradiction — no matching cols")
        continue
    ph = ",".join("?" * len(flds))
    try:
        brain.execute(f"INSERT INTO contradictions ({','.join(flds)}) VALUES ({ph})", vls)
        ct_insert += 1
    except Exception as e:
        print(f"  ERR contradiction {sa[:30]}: {e}")

brain.commit()
print(f"contradictions: inserted {ct_insert}/{len(ct_data)}")

# ── FINAL STATE ───────────────────────────────────────────────────────────────
print("\n=== BRAIN DB FINAL ===")
for tbl in brain.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall():
    t = tbl[0]
    cnt = brain.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"  {t}: {cnt}")

print(f"\nlitigation_context.db Lane B evidence_quotes: {main.execute('SELECT COUNT(*) FROM evidence_quotes WHERE lane=?', ('B',)).fetchone()[0]}")
print(f"litigation_context.db contradiction_map (all): {main.execute('SELECT COUNT(*) FROM contradiction_map').fetchone()[0]}")

brain.close(); main.close()
print("DONE")
