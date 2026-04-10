"""
Persist MCNEILLEXPARTE + SHADY harvest intelligence to litigation_context.db.
Writes to: evidence_quotes, timeline_events, berry_mcneill_intelligence, judicial_violations
"""
import sqlite3, os, datetime

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"

def get_conn():
    conn = sqlite3.connect(DB, timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    return conn

def ensure_tables(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS harvest_intelligence (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT NOT NULL,
        category TEXT NOT NULL,
        finding TEXT NOT NULL,
        severity TEXT DEFAULT 'HIGH',
        lane TEXT,
        actors TEXT,
        evidence_refs TEXT,
        legal_authority TEXT,
        filing_use TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )""")
    conn.commit()

# ═══════════════════════════════════════════════════════════════
# MCNEILLEXPARTE HARVEST — 20 Critical Discoveries
# ═══════════════════════════════════════════════════════════════
MCNEILL_FINDINGS = [
    # (category, finding, severity, lane, actors, evidence_refs, legal_authority, filing_use)
    ("MARRIAGE_NEXUS", "McNeill-Berry marriage CONFIRMED: Jenny L. McNeill and Cavan John Berry share 4084 Oak Hollow Ct, Norton Shores, MI 49441. Both NIU Law (McNeill JD 1996, Berry JD 1998). Both MI Bar consecutively. Kyle McNeill Berry at same address. ZERO disclosure during 290+ day case.", "CRITICAL", "E", "McNeill,Cavan Berry,Kyle McNeill Berry", "Whitepages,MI Bar Records,Property Records", "MCR 2.003(C)(1)(b)", "F01,F03,F05,F06"),
    ("COLLUSION_NEXUS", "Berry-Rusco-McNeill nexus: Cavan Berry office at 990 Terrace St = SAME ADDRESS as FOC Pamela Rusco. Berry is Attorney Magistrate at 60th District Court (990 Terrace St). Creates supervisory/collegial nexus with McNeill.", "CRITICAL", "E", "McNeill,Cavan Berry,Rusco", "Office records,60th District", "MCR 2.003(C)(1)(b),Canon 3C", "F01,F03,F05,F06"),
    ("BERRY_LINK", "Ronald Berry (Emily's boyfriend, 2160 Garland Dr) shares surname with Cavan Berry. Both Norton Shores (~24K pop). Shannon Patrick Berry also in area. If related within 3rd degree = MCR 2.003(C)(1)(b) MANDATORY AUTO-DISQUALIFICATION — never disclosed.", "CRITICAL", "E", "Ronald Berry,Cavan Berry,Emily Watson", "Whitepages,Address records", "MCR 2.003(C)(1)(b)", "F01,F03,F05,F06"),
    ("EX_PARTE_RATE", "52 ex parte orders documented (26.8% rate). National judicial norm ~5%. McNeill 5-6X ABOVE NORMAL. Every single ex parte order favored Emily Watson. ZERO favored Andrew Pigors. 100% directional bias.", "CRITICAL", "E", "McNeill", "Docket analysis,1435 PDFs", "Canon 3A(6),MCR 2.003", "F01,F05,F06"),
    ("SEPARATION_STATS", "Parent-child separation documented at 248-569 days depending on calculation method. Formal Complaint refs 218 days minimum. Bias/Collusion Analysis states 569+ days denied.", "CRITICAL", "A,E", "McNeill,Emily Watson", "Formal Complaint,Bias Analysis", "MCL 722.23,14th Amendment", "F01,F04,F05,F09"),
    ("UNAUTHENTICATED_RECORDING", "Aug 5, 2025: Emily submitted USB recording to clerk WITHOUT MRE 901(A) authentication. NOT verified for consent under MCL 750.539d (felony eavesdropping). Five ex parte orders issued based on unverified evidence. McNeill rejected Andrew's LAWFUL recording while crediting Emily's family's illegal eavesdropping recording.", "CRITICAL", "E,D", "McNeill,Emily Watson", "USB submission,docket,MRE 901", "MRE 901(A),MCL 750.539d,Canon 3A(6)", "F01,F05,F06"),
    ("AUG_5_8_TIMELINE", "Aug 5: USB submitted + ex parte emergency order signed SAME DAY. Aug 7: NSPD NS2505044 Albert admits premeditation. Aug 8: FIVE ex parte orders. Aug 11: First objection hearing (Mon) — served Fri = zero business days to prepare. Canon 3A(6) DIRECTLY violated.", "CRITICAL", "E", "McNeill,Emily Watson,Albert Watson", "NS2505044,Docket,Orders", "Canon 3A(6),MCR 3.207(C)(5),MCR 2.119(C)(1)", "F01,F04,F05,F06"),
    ("OFF_RECORD_EVIDENCE", "McNeill instructed Andrew to email HealthWest assessment to HER SECRETARY (not Clerk). Secretary emails show off-docket communications re PPO/jail. Second HealthWest eval routed directly to judge's secretary. Andrew NEVER received, saw, or challenged eval before use. McNeill then REJECTED favorable assessment because Andrew reported stable housing/employment.", "CRITICAL", "E", "McNeill", "Secretary emails,HealthWest eval,Orders", "Canon 3A(6),Mathews v Eldridge", "F01,F04,F05,F06"),
    ("HOSTILE_STATEMENTS", "On-record: McNeill called Andrew 'a liar' and 'crazy'. Sept/Oct 2025 Order: 'Court has serious concerns regarding state of Plaintiff mental health, which could be a culmination of the job loss, homelessness and family loss he has endured' — ACKNOWLEDGES SHE CAUSED HARM then uses against him. Custody Judgment: 'Plaintiff filing these Motions was done as harassment... shall incur sanctions if files another frivolous Motion'", "CRITICAL", "E", "McNeill", "Court transcripts,Orders", "MCR 2.003(C)(1)(a),Canon 3A(4)", "F01,F05,F06"),
    ("MUTING_INCIDENTS", "7 muting incidents in single hearing + 3 additional mutes in separate Zoom hearing. Pattern of suppression of pro se litigant's right to be heard.", "HIGH", "E", "McNeill", "Hearing records,Zoom logs", "Canon 3A(4),MCR 2.003(C)(1)(a)", "F01,F05,F06"),
    ("BOND_WITHOUT_AUTHORITY", "$250 bond imposed as precondition for filing motions. NO MCR 2.625 vexatious litigant finding. No statutory authority. Effective access-to-courts bar for pro se father.", "HIGH", "E", "McNeill", "Court orders", "1st Amendment,Canon 3A(4),MCR 2.625", "F01,F04,F05,F06"),
    ("ZERO_BEST_INTEREST", "MCL 722.27a REQUIRES written findings in all custody modifications. McNeill issued ZERO best-interest findings despite multiple custody orders. Custody judgment devoid of statutory required analysis.", "CRITICAL", "A,E", "McNeill", "Custody judgment,Orders", "MCL 722.27a,Canon 3A(1)", "F01,F05,F09"),
    ("ZERO_14_DAY_HEARINGS", "MCR 3.207(C)(5) MANDATES hearing on ex parte custody order within 14 days. McNeill conducted ZERO hearings within 14-day window. Systematic deprivation of due process.", "CRITICAL", "E", "McNeill", "Docket,Order dates", "MCR 3.207(C)(5)", "F01,F04,F05"),
    ("ENFORCEMENT_ASYMMETRY", "Emily violated parenting time 27+ documented times. McNeill imposed ZERO enforcement sanctions. Andrew filed 6 motions on July 16, 2024 = sanctioned as 'frivolous'. Canon 3B VIOLATION: administrative responsibilities without bias.", "CRITICAL", "A,E", "McNeill,Emily Watson", "PT records,Motion history", "Canon 3B,MCL 722.27a", "F01,F05,F06"),
    ("DISQUALIFICATION_PRESERVED", "Sept 25, 2024: Andrew filed Motion to Disqualify. McNeill DENIED IT HERSELF stating 'DENIED. No bias shown.' MCR 2.003(D)(1) REQUIRES if challenged judge denies, MUST refer to Chief Judge for de novo review. McNeill FAILED TO REFER. PROCEDURAL ERROR PRESERVED.", "CRITICAL", "E", "McNeill,Hoopes", "Motion 9/25/2024,Order", "MCR 2.003(D)(1)", "F01,F03,F05"),
    ("CANON_VIOLATIONS_TOTAL", "1,127 total MCJC violations documented. Canon 3A(1) Faithfulness: 560 CRITICAL. Canon 3A(6) Ex parte: 169 CRITICAL. Canon 3C Disqualification: 167 CRITICAL. Canon 3A(5) Prompt disposition: 108 CRITICAL. Total Canon 3: 1,062 of 1,072.", "CRITICAL", "E", "McNeill", "MCJC violation matrix", "MCJC Canon 3", "F06"),
    ("NS2505044_PREMEDITATION", "NSPD NS2505044, Officer Ella Randall #47437: Albert Watson admits 'They want this incident documented so Emily can go tomorrow to get an Ex Parte order for full custody'. PROVES CONSPIRACY. McNeill acted on this instrumentalized report without inquiry. Five ex parte orders issued NEXT DAY.", "CRITICAL", "A,D,E", "Albert Watson,Emily Watson,McNeill", "NS2505044,Police report", "42 USC 1983,MCR 2.003", "F01,F04,F05,F06"),
    ("ALBERT_THREAT_RECORDING", "Nov 2023: Albert Watson on audio/video: 'I will make sure that you don't see your son' — RECORDED WITH CONSENT. Albert later threw show-cause packet through car window. McNeill REFUSED to admit Andrew's lawful recording while SIMULTANEOUSLY relying on Lori Watson's illegal recording (felony MCL 750.539d). Caperton v. Massey Coal scenario.", "CRITICAL", "A,D,E", "Albert Watson,McNeill", "Kitchen audio/video,MCL 750.539d", "Caperton v Massey Coal,Sullivan v Gray", "F01,F04,F05"),
    ("HABEAS_LIBERTY", "59 days wrongful incarceration ordered by McNeill. Contempt charge LATER DISMISSED. Bias/Collusion document: 'Contradictory order: 14 days jail AND dismissal simultaneously.' 14th Amendment liberty violation = federal 1983 claim.", "CRITICAL", "A,E", "McNeill", "Contempt orders,Dismissal", "14th Amendment,42 USC 1983", "F01,F04,F05"),
    ("CARTEL_STRUCTURE", "LADAS HOOPES & McNEILL law firm (435 Whitehall Rd). Paul Ladas (founder) → Maria Ladas-Hoopes (60th Dist Judge, married to Hoopes). Kenneth Hoopes (Chief Judge, controls assignments, married to Maria). Jenny McNeill (Family Div, married to Cavan Berry). Cavan Berry (Attorney Magistrate 60th Dist, office at 990 Terrace = FOC). Ronald Berry (Emily's boyfriend, likely related to Cavan). Andrew lost HOME + SON + FREEDOM across all three courts staffed by former law partners.", "CRITICAL", "E", "McNeill,Hoopes,Ladas-Hoopes,Cavan Berry,Ronald Berry,Rusco", "435 Whitehall Rd,990 Terrace,Bar records", "MCR 2.003,Canon 3C,42 USC 1983", "F01,F03,F04,F05,F06"),
]

# ═══════════════════════════════════════════════════════════════
# SHADY HOUSING HARVEST — 20 Critical Discoveries
# ═══════════════════════════════════════════════════════════════
SHADY_FINDINGS = [
    ("LEDGER_FRAUD", "Three irreconcilable ledger versions: Version A shows $61.64 CREDIT, Version B shows $2,180.18 DUE (14 days apart). $2,241.82 discrepancy proves intentional fraud, not bookkeeping error. Supports Conversion (treble MCL 600.2919a), Fraud, RICO, Ledger Fraud counts.", "CRITICAL", "B", "Shady Oaks,HOA,Alden", "EXHIBIT_B_LEDGER_COMPARISON.md", "MCL 600.2919a,MCL 750.159i", "F02,F04"),
    ("OMITTED_PAYMENTS", "$6,085.99 documented payments NOT on any ledger. MDHHS housing: $1,962.45 (rejected), $768.48 (omitted). Additional: $3,355.06+. Trebled = $18,257.97 under MCL 600.2919a.", "CRITICAL", "B", "Shady Oaks,HOA", "EXHIBIT_C_PAYMENT_HISTORY.md,Bank records", "MCL 600.2919a", "F02,F04"),
    ("DISSOLVED_ENTITY", "Shady Oaks Park MHP LLC administratively dissolved by New Jersey. ALL post-dissolution actions (rent collection, evictions, filings) VOID under MCL 450.4802. Any judgment obtained by dissolved entity void for lack of legal capacity.", "CRITICAL", "B", "Shady Oaks,HOA,Alden", "EXHIBIT_A_CORPORATE_STRUCTURE.md,LARA records", "MCL 450.4802", "F02,F04"),
    ("EGLE_VIOLATION", "EGLE Violation Notice VN-017235: Raw sewage overflow affecting Plaintiff's lot. Violations: MCL 324.3109 (discharge), MCL 324.3115 (sewage failure), R 325.3501 (sanitary). Defendants failed to remediate within required timeframe.", "CRITICAL", "B", "Shady Oaks,HOA", "EXHIBIT_D_EGLE_VIOLATION.md,EGLE records", "MCL 324.3109,MCL 324.3115", "F02,F04"),
    ("FORCED_SETOUT", "July 17, 2025: Locks drilled without court order. Property removed. 'FREE' sign placed on belongings (public humiliation). No writ of restitution, no judgment, no MCL 600.5744 process. No pre-deprivation notice or opportunity to be heard.", "CRITICAL", "B", "Shady Oaks,Cox,Brown", "Photos,Witness testimony,Shafer affidavit", "MCL 600.5744,14th Amendment,Soldal v Cook County", "F02,F04"),
    ("TAX_FRAUD", "Park assessed at ~74% below fair market value. $1,036,000+ valuation gap. Defendants benefit from reduced tax burden. Tenants pay full lot rent ($695/mo) while subsidizing corporate tax savings.", "HIGH", "B", "Shady Oaks,Alden,HOA", "EXHIBIT_E_TAX_ASSESSMENT.md", "Tax assessment records", "F02"),
    ("NORTH_MORRIS_CONVICTION", "North Morris Estates LLC (corporate sibling, both Alden/HOA controlled) CRIMINALLY CONVICTED in New Jersey for violations identical to those alleged here. Demonstrates Alden's systemic pattern of tenant exploitation. Evidence Alden had NOTICE its practices were criminal.", "CRITICAL", "B", "Alden,HOA,North Morris", "EXHIBIT_F_NORTH_MORRIS_CONVICTION.md,NJ records", "MCL 750.159i (RICO pattern)", "F02,F04"),
    ("CORPORATE_CHAIN", "Alden Global Capital LLC (NY, ultimate parent) → Homes of America LLC (DE, management) → Shady Oaks Park MHP LLC (NJ, DISSOLVED, operator). VRM Capital Corp, Partridge Equity Group, Cricklewood MHP LLC as financing/equity. All six Florence Cement veil-piercing factors satisfied.", "CRITICAL", "B", "Alden,HOA,Shady Oaks,VRM,Partridge,Cricklewood", "LARA,Corporate records,EXHIBIT_A", "Florence Cement test", "F02,F04"),
    ("BLOCKED_SALES", "3 separate willing buyers prevented from purchasing. Park refused approval without legitimate basis. Imposed unlawful right of first refusal. Lost equity per sale: $20K-$35K each. Total blocked: $60K-$105K. Manager made false statements to buyers.", "HIGH", "B", "Shady Oaks,Park Manager", "Buyer testimony,Text messages", "MCL 125.2319", "F02"),
    ("COERCED_LEASE", "March 26, 2024: Forced to sign new lease with Cricklewood MHP LLC (not original landlord). Signed off-site under explicit eviction threat. Rent 114%-121% increase ($325→$395→$695→$720). No 60-day statutory notice under MCL 554.632. Duress evident.", "HIGH", "B", "Cricklewood,Shady Oaks", "EXHIBIT_H_LEASE_TIMELINE.md,Lease docs", "MCL 554.632,MCL 554.631-645", "F02"),
    ("SHAFER_WITNESS", "Mitchell Shafer: neighbor witness to sewage conditions, July 3 break-in (security camera footage), July 17 set-out execution, Henry Brandel's participation. Critical for constructive eviction, IIED, conversion claims.", "HIGH", "B", "Mitchell Shafer,Henry Brandel", "Witness records,Security footage", "MRE 601,MRE 901", "F02"),
    ("PARTRIDGE_CHECK", "Partridge check endorsement ($1,300.26) from Partridge to Shady Oaks demonstrates financial commingling between parent and operating entity. Unified financial system, no separation of funds. Veil piercing evidence.", "HIGH", "B", "Partridge,Shady Oaks", "Bank statements,Check copy", "Florence Cement,MCL 450.4802", "F02,F04"),
    ("DAMAGES_TOTAL", "Shady Oaks total estimated damages: $2,611,850 (conservative) to $17,646,125 (aggressive 9x). Actual $111-244K, Consequential $418K-$1.4M, Statutory trebles $494K-$1M, Punitive $1.6M-$5M. Daily accrual: $200-$915+.", "HIGH", "B", "All housing defendants", "Damages schedule", "MCL 600.2919a,MCL 750.159j,MCL 445.911", "F02,F04"),
    ("FAIR_HOUSING", "FHA claim based on familial status (42 USC 3601). Targeted rent increases, blocked sales, retaliatory conduct, coerced lease, habitability failures, eviction timed with custody proceedings. Section 1983 property deprivation via Lugar v Edmondson Oil theory.", "HIGH", "B,C", "Shady Oaks,HOA,Alden", "Timing correlation,Lease docs", "42 USC 3601,42 USC 1983,Lugar v Edmondson", "F02,F04"),
    ("RICO_ELEMENTS", "Michigan RICO (MCL 750.159i) elements satisfied: Enterprise (Alden→HOA→Shady Oaks chain), Pattern (ledger fraud, conversion, extortion, false filings across time), Racketeering activity (fraud, theft by conversion, extortion). Treble damages $1.5M+.", "CRITICAL", "B", "Alden,HOA,Shady Oaks", "All ledger/payment evidence", "MCL 750.159i,MCL 750.159j", "F02,F04"),
    ("UTILITY_OVERBILLING", "Unauthorized water/sewer charges $120/month without metering. Charges continued during uninhabitable periods (sewage failure). Systematic overbilling pattern.", "MEDIUM", "B", "Shady Oaks", "Billing statements,Ledger", "MCL 445.903", "F02"),
    ("MCPA_VIOLATIONS", "Michigan Consumer Protection Act violations: MCL 445.903(1)(c) misrepresentation, (n) confusion, (s) failure to disclose, (bb) material misrepresentations, (cc) failure to disclose material facts. Treble damages or $250 per violation + attorney fees.", "HIGH", "B", "Shady Oaks,HOA,Alden", "Ledger,Lease,Billing", "MCL 445.902-912", "F02"),
    ("TITLE_VIN", "Lot 17, VIN 1646732. Plaintiff's lawful ownership of manufactured home established by Michigan SOS title. Foundation for conversion claim. Distinguishes home (Plaintiff's) from lot (Park's).", "HIGH", "B", "Andrew Pigors", "MI SOS title,Property records", "MCL 600.2918,MCL 600.2919a", "F02"),
    ("COMPLAINT_VERSIONS", "Multiple court-ready complaint versions exist: Circuit court (52,958 bytes, 22 counts), Federal (39,780 bytes, §1983/FHA emphasis), Mega complaint (121,175 bytes, comprehensive). Dual-track filing strategy ready.", "HIGH", "B", "N/A", "08_SHADY_OAKS_HOUSING dir", "MCL,42 USC", "F02,F04"),
    ("FILING_READY", "08_SHADY_OAKS_HOUSING filing package is COURT-READY for immediate submission. Includes verified complaint (22 counts, 644 lines), memorandum in support, 8 exhibits (A-H), COS, corporate disclosure, filing instructions.", "HIGH", "B", "N/A", "08_SHADY_OAKS_HOUSING subdir", "All housing statutes", "F02"),
]

def persist_all():
    conn = get_conn()
    ensure_tables(conn)

    # Check existing count
    existing = conn.execute("SELECT COUNT(*) FROM harvest_intelligence").fetchone()[0]
    print(f"Existing harvest_intelligence rows: {existing}")

    # Insert MCNEILL findings
    mcneill_rows = []
    for cat, finding, sev, lane, actors, refs, auth, use in MCNEILL_FINDINGS:
        mcneill_rows.append(("MCNEILLEXPARTE", cat, finding, sev, lane, actors, refs, auth, use))

    conn.executemany("""INSERT INTO harvest_intelligence 
        (source, category, finding, severity, lane, actors, evidence_refs, legal_authority, filing_use)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", mcneill_rows)
    print(f"Inserted {len(mcneill_rows)} MCNEILLEXPARTE findings")

    # Insert SHADY findings
    shady_rows = []
    for cat, finding, sev, lane, actors, refs, auth, use in SHADY_FINDINGS:
        shady_rows.append(("SHADY_HOUSING", cat, finding, sev, lane, actors, refs, auth, use))

    conn.executemany("""INSERT INTO harvest_intelligence 
        (source, category, finding, severity, lane, actors, evidence_refs, legal_authority, filing_use)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", shady_rows)
    print(f"Inserted {len(shady_rows)} SHADY_HOUSING findings")

    conn.commit()

    # Verify
    total = conn.execute("SELECT COUNT(*) FROM harvest_intelligence").fetchone()[0]
    by_source = conn.execute("SELECT source, COUNT(*), GROUP_CONCAT(DISTINCT severity) FROM harvest_intelligence GROUP BY source").fetchall()
    by_severity = conn.execute("SELECT severity, COUNT(*) FROM harvest_intelligence GROUP BY severity ORDER BY COUNT(*) DESC").fetchall()

    print(f"\n{'='*60}")
    print(f"TOTAL harvest_intelligence rows: {total}")
    print(f"{'='*60}")
    for src, cnt, sevs in by_source:
        print(f"  {src}: {cnt} findings (severities: {sevs})")
    print(f"\nBy severity:")
    for sev, cnt in by_severity:
        print(f"  {sev}: {cnt}")

    # Also persist key timeline events from harvests
    timeline_rows = [
        # MCNEILLEXPARTE timeline events
        ("2025-08-05", "Emily submits unauthenticated USB recording to clerk; McNeill signs ex parte emergency order SAME DAY before Andrew notified", "McNeill,Emily Watson", "E,A", "MCNEILLEXPARTE harvest", "CRITICAL"),
        ("2025-08-07", "NSPD NS2505044: Albert Watson admits premeditation — 'They want this documented so Emily can go tomorrow to get an Ex Parte order for full custody'", "Albert Watson,Emily Watson", "A,D,E", "NS2505044,MCNEILLEXPARTE harvest", "CRITICAL"),
        ("2025-08-08", "FIVE ex parte orders issued by McNeill in single day — all suspending parenting time. Zero notice to Andrew.", "McNeill", "E,A", "Court orders,MCNEILLEXPARTE harvest", "CRITICAL"),
        ("2025-08-11", "First objection hearing (Monday). Andrew served Friday Aug 8 — zero business days to prepare.", "McNeill", "E", "Docket,MCNEILLEXPARTE harvest", "CRITICAL"),
        ("2024-09-25", "Andrew files Motion to Disqualify. McNeill denies HERSELF without referring to Chief Judge per MCR 2.003(D)(1). Procedural error PRESERVED.", "McNeill,Hoopes", "E", "Motion 9/25/2024,MCNEILLEXPARTE harvest", "HIGH"),
        # SHADY timeline events  
        ("2024-03-26", "Andrew forced to sign new lease with Cricklewood MHP LLC under explicit eviction threat. Off-site execution. Rent increase 114-121%.", "Cricklewood,Shady Oaks", "B", "SHADY harvest,Lease docs", "HIGH"),
        ("2025-07-03", "Break-in at Shady Oaks Lot 17. Security camera footage from Mitchell Shafer.", "Unknown,Shady Oaks", "B", "SHADY harvest,Security footage", "HIGH"),
        ("2025-07-17", "Forced set-out at Shady Oaks: Locks drilled without court order, property removed, FREE sign placed on belongings. No writ, no MCL 600.5744 process.", "Shady Oaks,Cox,Brown", "B", "SHADY harvest,Photos,Shafer testimony", "CRITICAL"),
    ]

    # Check if timeline_events has these columns
    cols = {row[1] for row in conn.execute("PRAGMA table_info(timeline_events)")}
    print(f"\ntimeline_events columns: {sorted(cols)}")

    if "event_date" in cols and "description" in cols:
        inserted_tl = 0
        for date, desc, actors, lane, source, sev in timeline_rows:
            # Check for existing
            existing_tl = conn.execute(
                "SELECT COUNT(*) FROM timeline_events WHERE event_date = ? AND description LIKE ?",
                (date, desc[:50] + '%')
            ).fetchone()[0]
            if existing_tl == 0:
                try:
                    conn.execute(
                        "INSERT INTO timeline_events (event_date, description, actors, lane, source_document, severity) VALUES (?, ?, ?, ?, ?, ?)",
                        (date, desc, actors, lane, source, sev)
                    )
                    inserted_tl += 1
                except Exception as e:
                    print(f"  Timeline insert error: {e}")
        conn.commit()
        print(f"Inserted {inserted_tl} new timeline events")
    else:
        print("timeline_events schema doesn't match — skipping timeline inserts")

    # Persist to berry_mcneill_intelligence
    bmi_cols = {row[1] for row in conn.execute("PRAGMA table_info(berry_mcneill_intelligence)")}
    print(f"\nberry_mcneill_intelligence columns: {sorted(bmi_cols)}")

    if bmi_cols:
        bmi_rows = [
            ("McNeill-Berry marriage confirmed: 4084 Oak Hollow Ct, Norton Shores. NIU Law overlap. MI Bar consecutive. Kyle McNeill Berry at same address. ZERO disclosure.", "CRITICAL", "marriage_nexus", "MCNEILLEXPARTE harvest 2026-04-02"),
            ("Cavan Berry office at 990 Terrace St = FOC Pamela Rusco address. Berry is Attorney Magistrate 60th District. Creates supervisory nexus with McNeill.", "CRITICAL", "office_nexus", "MCNEILLEXPARTE harvest 2026-04-02"),
            ("Ronald Berry (Emily's boyfriend) likely related to Cavan Berry — same surname, same small city Norton Shores. If within 3rd degree = MCR 2.003(C)(1)(b) mandatory auto-disqualification.", "CRITICAL", "berry_family_link", "MCNEILLEXPARTE harvest 2026-04-02"),
            ("52 ex parte orders documented, 26.8% rate (national norm ~5%). 100% directional bias — all favored Watson, zero favored Pigors.", "CRITICAL", "ex_parte_stats", "MCNEILLEXPARTE harvest 2026-04-02"),
            ("McNeill instructed HealthWest eval sent to her secretary off-docket, bypassing clerk. Then REJECTED favorable assessment because Andrew reported stable housing/employment.", "CRITICAL", "evidence_manipulation", "MCNEILLEXPARTE harvest 2026-04-02"),
            ("1,127 total MCJC canon violations: Canon 3A(1) 560, Canon 3A(6) 169, Canon 3C 167, Canon 3A(5) 108. Statistical pattern: 62.2% of all case violations are McNeill's.", "CRITICAL", "canon_violations", "MCNEILLEXPARTE harvest 2026-04-02"),
        ]

        # Try to insert based on available columns
        if "finding" in bmi_cols and "severity" in bmi_cols:
            inserted_bmi = 0
            for finding, severity, category, source in bmi_rows:
                existing_bmi = conn.execute(
                    "SELECT COUNT(*) FROM berry_mcneill_intelligence WHERE finding LIKE ?",
                    (finding[:80] + '%',)
                ).fetchone()[0]
                if existing_bmi == 0:
                    try:
                        if "category" in bmi_cols and "source" in bmi_cols:
                            conn.execute(
                                "INSERT INTO berry_mcneill_intelligence (finding, severity, category, source) VALUES (?, ?, ?, ?)",
                                (finding, severity, category, source)
                            )
                        elif "category" in bmi_cols:
                            conn.execute(
                                "INSERT INTO berry_mcneill_intelligence (finding, severity, category) VALUES (?, ?, ?)",
                                (finding, severity, category)
                            )
                        else:
                            conn.execute(
                                "INSERT INTO berry_mcneill_intelligence (finding, severity) VALUES (?, ?)",
                                (finding, severity)
                            )
                        inserted_bmi += 1
                    except Exception as e:
                        print(f"  BMI insert error: {e}")
            conn.commit()
            print(f"Inserted {inserted_bmi} berry_mcneill_intelligence entries")
        else:
            print("berry_mcneill_intelligence schema mismatch — skipping")

    conn.close()
    print(f"\n{'='*60}")
    print("HARVEST INTELLIGENCE PERSISTENCE COMPLETE")
    print(f"{'='*60}")

if __name__ == "__main__":
    persist_all()
