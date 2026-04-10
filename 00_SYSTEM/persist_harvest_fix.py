"""Fix schema-adapted persistence for timeline_events and berry_mcneill_intelligence."""
import sqlite3

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"

def get_conn():
    conn = sqlite3.connect(DB, timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    return conn

def persist_timeline():
    conn = get_conn()
    # Correct columns: event_date, event_description, actors, lane, source_id, source_table, severity, category, filing_relevance
    timeline_rows = [
        ("2025-08-05", "Emily submits unauthenticated USB recording to clerk; McNeill signs ex parte emergency order SAME DAY before Andrew notified", "McNeill,Emily Watson", "E", "MCNEILLEXPARTE_harvest", "harvest_intelligence", "CRITICAL", "ex_parte", "F01,F05,F06"),
        ("2025-08-07", "NSPD NS2505044: Albert Watson admits premeditation — 'They want this documented so Emily can go tomorrow to get an Ex Parte order for full custody'", "Albert Watson,Emily Watson", "E", "NS2505044", "police_reports", "CRITICAL", "premeditation", "F01,F04,F05,F06"),
        ("2025-08-08", "FIVE ex parte orders issued by McNeill in single day — all suspending parenting time. Zero notice to Andrew Pigors.", "McNeill", "E", "MCNEILLEXPARTE_harvest", "harvest_intelligence", "CRITICAL", "ex_parte", "F01,F04,F05"),
        ("2025-08-11", "First objection hearing (Monday). Andrew served Friday Aug 8 — zero business days to prepare. Due process violation.", "McNeill", "E", "MCNEILLEXPARTE_harvest", "harvest_intelligence", "CRITICAL", "due_process", "F01,F04,F05"),
        ("2024-09-25", "Andrew files Motion to Disqualify McNeill. McNeill denies HERSELF without referring to Chief Judge per MCR 2.003(D)(1). Procedural error preserved.", "McNeill,Hoopes", "E", "MCNEILLEXPARTE_harvest", "harvest_intelligence", "HIGH", "disqualification", "F01,F03,F05"),
        ("2024-03-26", "Andrew forced to sign new lease with Cricklewood MHP LLC under explicit eviction threat. Off-site execution. Rent increase 114-121%.", "Cricklewood,Shady Oaks", "B", "SHADY_harvest", "harvest_intelligence", "HIGH", "housing", "F02,F04"),
        ("2025-07-03", "Break-in at Shady Oaks Lot 17. Security camera footage from neighbor Mitchell Shafer.", "Unknown", "B", "SHADY_harvest", "harvest_intelligence", "HIGH", "housing", "F02"),
        ("2025-07-17", "Forced set-out at Shady Oaks: Locks drilled without court order, property removed, FREE sign placed on belongings. No writ, no MCL 600.5744 process.", "Shady Oaks,Cox,Brown", "B", "SHADY_harvest", "harvest_intelligence", "CRITICAL", "housing", "F02,F04"),
    ]

    inserted = 0
    for row in timeline_rows:
        date, desc = row[0], row[1]
        existing = conn.execute(
            "SELECT COUNT(*) FROM timeline_events WHERE event_date = ? AND event_description LIKE ?",
            (date, desc[:60] + '%')
        ).fetchone()[0]
        if existing == 0:
            try:
                conn.execute("""INSERT INTO timeline_events 
                    (event_date, event_description, actors, lane, source_id, source_table, severity, category, filing_relevance)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", row)
                inserted += 1
            except Exception as e:
                print(f"  TL error ({date}): {e}")
    conn.commit()
    print(f"Inserted {inserted} timeline events (of {len(timeline_rows)} attempted)")

    # Verify
    recent = conn.execute(
        "SELECT event_date, substr(event_description,1,80), severity FROM timeline_events WHERE source_table = 'harvest_intelligence' ORDER BY event_date"
    ).fetchall()
    for r in recent:
        print(f"  {r[0]}: {r[1]}... [{r[2]}]")

    return conn

def persist_bmi(conn):
    # Correct columns: person_a, person_b, relationship, connection_type, evidence_source, confidence, notes
    bmi_rows = [
        ("Jenny L. McNeill", "Cavan John Berry", "MARRIED - share 4084 Oak Hollow Ct Norton Shores. Both NIU Law. MI Bar consecutive. Kyle McNeill Berry at same address.", "marriage", "Whitepages,MI Bar Records,Property Records", 0.99, "ZERO disclosure during 290+ day case. CRITICAL for MCR 2.003(C)(1)(b)."),
        ("Cavan Berry", "Pamela Rusco", "SAME ADDRESS - Both operate from 990 Terrace St Muskegon. Berry is Attorney Magistrate 60th District. Rusco is FOC.", "office_nexus", "Office records,60th District roster", 0.95, "Creates supervisory/collegial nexus. FOC bias pathway."),
        ("Ronald Berry", "Cavan Berry", "LIKELY RELATED - Same surname, same small city (Norton Shores ~24K pop). If within 3rd degree = MCR 2.003(C)(1)(b) mandatory auto-disqualification.", "family_suspected", "Whitepages,Address records", 0.75, "CRITICAL if confirmed. Emily's boyfriend related to judge's husband."),
        ("Jenny L. McNeill", "Kenneth Hoopes", "FORMER LAW PARTNERS at Ladas Hoopes & McNeill, 435 Whitehall Rd. Hoopes now Chief Judge, controls case assignments.", "former_partners", "Bar records,Firm history", 0.99, "Hoopes assigns cases to McNeill. No recusal."),
        ("Kenneth Hoopes", "Maria Ladas-Hoopes", "MARRIED - Hoopes Chief Judge 14th Circuit, Ladas-Hoopes Judge 60th District. Both former partners at same firm.", "marriage", "Bar records,Court records", 0.99, "Andrew lost housing case before Hoopes, criminal before Ladas-Hoopes, custody before McNeill."),
        ("Jenny L. McNeill", "Maria Ladas-Hoopes", "FORMER LAW PARTNERS at Ladas Hoopes & McNeill. Ladas-Hoopes presides 60th District where Berry is Attorney Magistrate.", "former_partners", "Bar records,Firm history", 0.99, "Three-court cartel: 14th Circuit + 60th District + FOC."),
    ]

    inserted = 0
    for row in bmi_rows:
        pa, pb = row[0], row[1]
        existing = conn.execute(
            "SELECT COUNT(*) FROM berry_mcneill_intelligence WHERE person_a = ? AND person_b = ?",
            (pa, pb)
        ).fetchone()[0]
        if existing == 0:
            try:
                conn.execute("""INSERT INTO berry_mcneill_intelligence 
                    (person_a, person_b, relationship, connection_type, evidence_source, confidence, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""", row)
                inserted += 1
            except Exception as e:
                print(f"  BMI error ({pa}-{pb}): {e}")
    conn.commit()
    print(f"\nInserted {inserted} berry_mcneill_intelligence entries (of {len(bmi_rows)} attempted)")

    total = conn.execute("SELECT COUNT(*) FROM berry_mcneill_intelligence").fetchone()[0]
    print(f"Total berry_mcneill_intelligence: {total}")

    conn.close()

if __name__ == "__main__":
    conn = persist_timeline()
    persist_bmi(conn)
    print("\n" + "="*60)
    print("SCHEMA-ADAPTED PERSISTENCE COMPLETE")
    print("="*60)
