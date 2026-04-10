"""
Persist MCNEILLEXPARTE + SHADY harvest intelligence to litigation_context.db.
Schema-verify pattern: PRAGMA table_info() before every INSERT.
"""
import sqlite3
import datetime
import sys

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"

def get_conn():
    conn = sqlite3.connect(DB, timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn

def get_columns(conn, table):
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {r[1]: r[2] for r in rows}

def table_exists(conn, table):
    r = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
    return r[0] > 0

def safe_insert(conn, table, data_list, on_conflict="IGNORE"):
    if not data_list:
        return 0
    cols = get_columns(conn, table)
    if not cols:
        print(f"  [SKIP] Table {table} does not exist or has no columns")
        return 0
    valid_cols = list(cols.keys())
    inserted = 0
    for row_dict in data_list:
        filtered = {k: v for k, v in row_dict.items() if k in valid_cols}
        if not filtered:
            continue
        col_names = list(filtered.keys())
        placeholders = ",".join(["?"] * len(col_names))
        col_str = ",".join(col_names)
        vals = [filtered[c] for c in col_names]
        try:
            conn.execute(
                f"INSERT OR {on_conflict} INTO {table} ({col_str}) VALUES ({placeholders})",
                vals
            )
            inserted += 1
        except Exception as e:
            print(f"  [WARN] Insert into {table} failed: {e}")
    conn.commit()
    return inserted

def persist_mcneill_intelligence(conn):
    """Persist MCNEILLEXPARTE harvest findings."""
    print("\n=== MCNEILLEXPARTE HARVEST PERSISTENCE ===")
    
    # 1. Berry-McNeill Intelligence
    if table_exists(conn, "berry_mcneill_intelligence"):
        bmi_data = [
            {"category": "MARRIAGE_CONFIRMED", "detail": "McNeill-Berry share residential address: 4084 Oak Hollow Ct, Norton Shores, MI 49441. Kyle McNeill Berry (~24) same address. Both NIU Law (McNeill JD 1996, Berry JD 1998). Both MI Bar consecutively.", "source": "MCNEILLEXPARTE harvest 2026-04-03", "severity": "CRITICAL", "date_discovered": "2026-04-03"},
            {"category": "BERRY_RUSCO_NEXUS", "detail": "Cavan Berry office at 990 Terrace St = SAME as FOC Pamela Rusco. Berry is Attorney Magistrate at 60th District Court. Creates supervisory/collegial nexus with McNeill.", "source": "MCNEILLEXPARTE harvest 2026-04-03", "severity": "CRITICAL", "date_discovered": "2026-04-03"},
            {"category": "RONALD_BERRY_LINK", "detail": "Ronald Berry (Emily partner, 2160 Garland Dr) shares surname with Cavan. Both Norton Shores (~24K pop). Shannon Patrick Berry also in area. If related within 3rd degree: MCR 2.003(C)(1)(b) MANDATORY DISQUALIFICATION — never disclosed.", "source": "MCNEILLEXPARTE harvest 2026-04-03", "severity": "CRITICAL", "date_discovered": "2026-04-03"},
            {"category": "EX_PARTE_STATISTICS", "detail": "52 ex parte orders. 26.8% ex parte rate vs 5% national norm (5-6X elevated). 100% directional bias: ALL favored Watson, ZERO favored Pigors. Aug 8 2025: FIVE ex parte orders same day.", "source": "MCNEILLEXPARTE harvest 2026-04-03", "severity": "CRITICAL", "date_discovered": "2026-04-03"},
            {"category": "EVIDENCE_MANIPULATION", "detail": "McNeill: 'Yes, I had my staff listen to it' — personal acquisition of disputed evidence ex parte. Canon 3A(6) direct violation. Instructed Andrew to email HealthWest to secretary (not Clerk). Off-docket handling.", "source": "MCNEILLEXPARTE harvest 2026-04-03", "severity": "CRITICAL", "date_discovered": "2026-04-03"},
            {"category": "UNAUTHENTICATED_RECORDING", "detail": "Aug 5 2025: Emily submitted USB recording. Admitted WITHOUT MRE 901(A) authentication. NOT verified for MCL 750.539d (felony eavesdropping). Five ex parte orders based on unverified evidence. Andrew's lawful recording REJECTED.", "source": "MCNEILLEXPARTE harvest 2026-04-03", "severity": "CRITICAL", "date_discovered": "2026-04-03"},
            {"category": "HOSTILE_STATEMENTS", "detail": "McNeill called Andrew 'a liar' and 'crazy' on record. Sept/Oct 2025 Order: 'Court has serious concerns regarding Plaintiff mental health, which could be culmination of job loss, homelessness and family loss' — ACKNOWLEDGES she caused the harm, then weaponizes it.", "source": "MCNEILLEXPARTE harvest 2026-04-03", "severity": "CRITICAL", "date_discovered": "2026-04-03"},
            {"category": "MUTING_PATTERN", "detail": "7 muting incidents in single hearing + 3 additional mutes in separate Zoom hearing. Systematic suppression of pro se right to be heard. Canon 3A(4) violation.", "source": "MCNEILLEXPARTE harvest 2026-04-03", "severity": "HIGH", "date_discovered": "2026-04-03"},
            {"category": "FILING_BOND_ABUSE", "detail": "$250 bond imposed as precondition for filing motions WITHOUT MCR 2.625 vexatious litigant finding. No statutory authority. Effective access-to-courts bar. Canon 3A(4) + 1st Amendment violation.", "source": "MCNEILLEXPARTE harvest 2026-04-03", "severity": "HIGH", "date_discovered": "2026-04-03"},
            {"category": "DISQUALIFICATION_ERROR", "detail": "Sept 25 2024: Andrew filed Motion to Disqualify. McNeill DENIED IT HERSELF stating 'No bias shown'. MCR 2.003(D)(1) REQUIRES referral to Chief Judge for de novo review. McNeill failed to refer. PROCEDURAL ERROR PRESERVED.", "source": "MCNEILLEXPARTE harvest 2026-04-03", "severity": "CRITICAL", "date_discovered": "2026-04-03"},
            {"category": "ENFORCEMENT_ASYMMETRY", "detail": "27+ Emily parenting time violations: ZERO enforcement. Andrew filed 6 motions July 16 2024: sanctioned as 'frivolous harassment'. Canon 3B violation.", "source": "MCNEILLEXPARTE harvest 2026-04-03", "severity": "CRITICAL", "date_discovered": "2026-04-03"},
            {"category": "CONSPIRACY_CHAIN", "detail": "Ladas (founder) -> Maria Ladas-Hoopes (daughter, 60th Dist Judge) -> Kenneth Hoopes (spouse, Chief Judge 14th Circuit) -> Jenny McNeill (former partner) -> Cavan Berry (spouse, family law atty) -> 990 Terrace (FOC/60th Dist) -> Pamela Rusco (FOC). Single chain controls ALL courts Andrew faces.", "source": "MCNEILLEXPARTE harvest 2026-04-03", "severity": "CRITICAL", "date_discovered": "2026-04-03"},
            {"category": "CANON_VIOLATIONS_TOTAL", "detail": "1,127 MCJC canon violations: Canon 3A(1) faithfulness 560, Canon 3A(6) ex parte 169, Canon 3C disqualification 167, Canon 3A(5) prompt disposition 108. Total Canon 3: 1,062 of 1,072. McNeill = 62.2% of ALL case violations.", "source": "MCNEILLEXPARTE harvest 2026-04-03", "severity": "CRITICAL", "date_discovered": "2026-04-03"},
            {"category": "NO_BEST_INTEREST_FINDINGS", "detail": "MCL 722.27a REQUIRES written best interest findings in all custody modifications. McNeill issued ZERO best interest findings despite multiple custody orders. Canon 3A(1) violation.", "source": "MCNEILLEXPARTE harvest 2026-04-03", "severity": "CRITICAL", "date_discovered": "2026-04-03"},
            {"category": "ZERO_14DAY_HEARINGS", "detail": "MCR 3.207(C)(5) MANDATES hearing on ex parte custody order within 14 days. McNeill conducted ZERO hearings within mandated window. Systematic due process deprivation.", "source": "MCNEILLEXPARTE harvest 2026-04-03", "severity": "CRITICAL", "date_discovered": "2026-04-03"},
        ]
        n = safe_insert(conn, "berry_mcneill_intelligence", bmi_data)
        print(f"  berry_mcneill_intelligence: {n} rows inserted")
    
    # 2. Timeline events for key dates
    if table_exists(conn, "timeline_events"):
        timeline_data = [
            {"event_date": "2025-08-05", "event_description": "Emily submits USB recording to clerk off-docket. McNeill signs emergency ex parte order SAME DAY before Andrew notified. MRE 901 authentication absent. MCL 750.539d consent unverified.", "actor": "Emily Watson / McNeill", "category": "ex_parte", "lane": "E", "source_file": "MCNEILLEXPARTE harvest"},
            {"event_date": "2025-08-07", "event_description": "NSPD NS2505044: Albert Watson tells Officer Randall 'They want this incident documented so Emily can go tomorrow to get an Ex Parte order for full custody of her son' — PREMEDITATED CUSTODY GRAB DOCUMENTED", "actor": "Albert Watson", "category": "conspiracy", "lane": "E", "source_file": "MCNEILLEXPARTE harvest"},
            {"event_date": "2025-08-08", "event_description": "FIVE ex parte orders issued in single day suspending ALL parenting time. Zero notice to Andrew. 100% directional bias. Aug 8-11: zero business days for objection prep (served Friday, hearing Monday).", "actor": "McNeill", "category": "ex_parte", "lane": "E", "source_file": "MCNEILLEXPARTE harvest"},
            {"event_date": "2024-09-25", "event_description": "Andrew files Motion to Disqualify McNeill. McNeill denies it herself ('No bias shown') WITHOUT referring to Chief Judge per MCR 2.003(D)(1). PROCEDURAL ERROR PRESERVED for appeal.", "actor": "McNeill", "category": "disqualification", "lane": "E", "source_file": "MCNEILLEXPARTE harvest"},
        ]
        n = safe_insert(conn, "timeline_events", timeline_data)
        print(f"  timeline_events: {n} rows inserted")
    
    # 3. Impeachment entries
    if table_exists(conn, "impeachment_matrix"):
        imp_cols = get_columns(conn, "impeachment_matrix")
        imp_data = []
        
        base = {
            "impeachment_value": 10,
            "filing_relevance": "F01,F05,F06",
        }
        source_col = "source_doc" if "source_doc" in imp_cols else "source_file"
        
        entries = [
            ("McNeill", "ex_parte", "McNeill: 'Yes, I had my staff listen to it' — admitted personal acquisition of disputed evidence outside noticed hearing", "Canon 3A(6) direct violation. Did you tell the parties before having staff listen to evidence?"),
            ("McNeill", "bias", "McNeill: 'Court has serious concerns regarding Plaintiff mental health from job loss, homelessness and family loss' — acknowledges causing the very harm she then weaponizes", "You acknowledged his suffering came from court actions. Did you then use that suffering against him?"),
            ("McNeill", "procedure", "McNeill denied disqualification motion herself without referring to Chief Judge per MCR 2.003(D)(1)", "When Mr. Pigors moved to disqualify you, did you refer that motion to Chief Judge Hoopes as MCR 2.003(D)(1) requires?"),
            ("McNeill", "enforcement", "27+ Emily parenting time violations ZERO enforcement vs Andrew 6 motions = sanctioned as frivolous", "Can you explain why 27 documented violations by the defendant resulted in zero enforcement actions?"),
            ("McNeill", "ex_parte", "52 ex parte orders, 100% favored Watson, 0% favored Pigors. 26.8% ex parte rate vs 5% national norm.", "In your career, what percentage of your ex parte orders have favored one party over another?"),
            ("Albert Watson", "conspiracy", "NSPD NS2505044: Albert told police 'They want this documented so Emily can go tomorrow to get an Ex Parte order'", "On August 7, 2025, you told Officer Randall this was being documented for Emily to get an ex parte order. Was that your plan?"),
        ]
        for target, cat, summary, question in entries:
            row = {
                "category": cat,
                "evidence_summary": summary,
                source_col: "MCNEILLEXPARTE harvest 2026-04-03",
                "impeachment_value": 10,
                "cross_exam_question": question,
                "filing_relevance": "F01,F05,F06",
            }
            if "target" in imp_cols:
                row["target"] = target
            imp_data.append(row)
        
        n = safe_insert(conn, "impeachment_matrix", imp_data)
        print(f"  impeachment_matrix: {n} rows inserted")


def persist_shady_intelligence(conn):
    """Persist SHADY harvest findings."""
    print("\n=== SHADY HOUSING HARVEST PERSISTENCE ===")
    
    # 1. Evidence quotes for housing claims
    if table_exists(conn, "evidence_quotes"):
        eq_cols = get_columns(conn, "evidence_quotes")
        eq_data = []
        
        items = [
            ("B", "Three irreconcilable ledger versions: Version A=$61.64 CREDIT, Version B=$2,180.18 DUE (14 days apart). $2,241.82 discrepancy proves intentional fraud. Supports Counts I (Conversion treble), II (Fraud), IX (RICO), XV (Ledger Fraud).", "EXHIBIT_B_LEDGER_COMPARISON.md", "housing_fraud"),
            ("B", "$6,085.99 omitted payments: MDHHS housing assistance $1,962.45 (rejected), $768.48 (omitted), additional $3,355.06+. None on any ledger. Supports Count I (Conversion treble MCL 600.2919a = $18,257.97).", "EXHIBIT_C_PAYMENT_HISTORY.md", "financial"),
            ("B", "Shady Oaks Park MHP LLC administratively DISSOLVED by New Jersey. Still operating. All post-dissolution actions (rent, evictions, filings) VOID under MCL 450.4802. Any judgment obtained is void for lack of legal capacity.", "EXHIBIT_A_CORPORATE_STRUCTURE.md", "corporate"),
            ("B", "EGLE Violation VN-017235: Raw sewage overflow affecting Plaintiff lot and common areas. MCL 324.3109, 324.3115, R 325.3501 violations. Failed to remediate within timeframe. Supports Counts X, XI, XVIII.", "EXHIBIT_D_EGLE_VIOLATION.md", "habitability"),
            ("B", "July 17 2025 forced set-out: Locks drilled without court order. Property removed. FREE sign placed on belongings. No writ of restitution, no judgment, no MCL 600.5744 process. No pre-deprivation notice.", "SHADY photos/evidence", "eviction"),
            ("B", "Tax assessment fraud: Park assessed 74% below fair market value. $1,036,000+ valuation gap. Tenants pay full lot rent ($695/mo) while subsidizing tax savings. Supports Count XVI.", "EXHIBIT_E_TAX_ASSESSMENT.md", "financial"),
            ("B", "North Morris Estates LLC (corporate sibling) criminally convicted in NJ for identical violations. Proves Alden systemic pattern and NOTICE that practices were criminal. Supports Count VIII (veil piercing), IX (RICO).", "EXHIBIT_F_NORTH_MORRIS_CONVICTION.md", "corporate"),
            ("B", "Corporate hierarchy: Alden Global Capital (NY) -> Homes of America (DE) -> Shady Oaks (NJ-DISSOLVED). VRM Capital, Partridge Equity, Cricklewood MHP = financing entities. Unity of interest, commingling, common management, inadequate capitalization.", "EXHIBIT_A_CORPORATE_STRUCTURE.md", "corporate"),
            ("B", "Park manager false statements to 3 prospective buyers blocking sales. Misrepresented Plaintiff account status. Stated Plaintiff 'abandoned' property (false). Total blocked equity: $60,000-$105,000.", "buyer testimony/correspondence", "interference"),
            ("B", "Coerced lease modification March 26 2024: Forced sign with Cricklewood MHP LLC (not original landlord) under explicit eviction threat. Rent $325->$395->$695->$720 (114-121% increase). No 60-day MCL 554.632 notice. Duress.", "EXHIBIT_H_LEASE_TIMELINE.md", "coercion"),
            ("B", "Mitchell Shafer witness affidavit: Neighbor witnessed sewage conditions, July 3 2025 break-in (security camera footage), July 17 2025 set-out execution, Henry Brandel participation.", "witness database", "witness"),
            ("B", "Partridge Securities check $1,300.26 to Shady Oaks: demonstrates financial commingling between parent and operating entity. Veil piercing evidence: unified financial system, no separation.", "bank statements", "corporate"),
            ("B", "Title documentation: Lot 17, VIN 1646732. Establishes Plaintiff lawful ownership of manufactured home (personal property). Foundation for conversion claim.", "MI SOS records", "property"),
            ("B", "Utility overbilling: Unauthorized water/sewer $120/month without metering. Charges continued during uninhabitable periods (sewage failure). Systematic overbilling pattern.", "ledger/billing", "financial"),
            ("B", "Damages calculation: Actual $111,450-$244,500. Consequential (custody loss) $166,425-$809,625. Statutory treble $494,350-$1,046,000. Punitive $1,588,125-$4,980,375. TOTAL: $2.6M-$17.6M. Daily accrual $200-$915+.", "damages schedule", "damages"),
        ]
        
        for lane, quote, source, cat in items:
            row = {"lane": lane, "quote_text": quote, "source_file": source, "category": cat}
            if "is_duplicate" in eq_cols:
                row["is_duplicate"] = 0
            eq_data.append(row)
        
        n = safe_insert(conn, "evidence_quotes", eq_data)
        print(f"  evidence_quotes (housing): {n} rows inserted")
    
    # 2. Timeline events for housing
    if table_exists(conn, "timeline_events"):
        tl_data = [
            {"event_date": "2024-03-26", "event_description": "Coerced lease modification: Andrew forced to sign new lease with Cricklewood MHP LLC under explicit eviction threat. Rent increased from $325 to $695. No 60-day MCL 554.632 notice. Signed off-site under duress.", "actor": "Shady Oaks/Cricklewood", "category": "housing", "lane": "B", "source_file": "SHADY harvest"},
            {"event_date": "2025-07-03", "event_description": "Break-in at Andrew's Shady Oaks unit. Mitchell Shafer neighbor witness with security camera footage documenting the incident.", "actor": "Unknown", "category": "housing", "lane": "B", "source_file": "SHADY harvest"},
            {"event_date": "2025-07-17", "event_description": "Forced set-out: Locks drilled without court order, property removed, FREE sign placed on belongings. No writ of restitution, no judgment, no MCL 600.5744 process. Mitchell Shafer witnessed, Henry Brandel participated.", "actor": "Shady Oaks/Cox/Brown", "category": "eviction", "lane": "B", "source_file": "SHADY harvest"},
        ]
        n = safe_insert(conn, "timeline_events", tl_data)
        print(f"  timeline_events (housing): {n} rows inserted")
    
    # 3. Impeachment for housing adversaries
    if table_exists(conn, "impeachment_matrix"):
        imp_cols = get_columns(conn, "impeachment_matrix")
        source_col = "source_doc" if "source_doc" in imp_cols else "source_file"
        imp_data = [
            {"category": "corporate_fraud", "evidence_summary": "Shady Oaks Park MHP LLC DISSOLVED but still collecting rent and filing evictions. Ultra vires. All actions void under MCL 450.4802.", source_col: "SHADY harvest", "impeachment_value": 10, "cross_exam_question": "Is Shady Oaks Park MHP LLC currently in good standing with any state? When was it dissolved?", "filing_relevance": "F02,F04"},
            {"category": "ledger_fraud", "evidence_summary": "Three irreconcilable ledger versions with $2,241.82 discrepancy over 14 days. $6,085.99 in documented payments omitted from ALL versions.", source_col: "SHADY harvest", "impeachment_value": 10, "cross_exam_question": "Can you explain why three different ledger versions exist showing different balances 14 days apart?", "filing_relevance": "F02,F04"},
            {"category": "eviction_abuse", "evidence_summary": "July 17 2025: Locks drilled, property removed, FREE sign placed — all without court order, writ of restitution, or MCL 600.5744 process.", source_col: "SHADY harvest", "impeachment_value": 10, "cross_exam_question": "Did you obtain a court order or writ of restitution before removing Mr. Pigors' property on July 17?", "filing_relevance": "F02,F04"},
        ]
        if "target" in imp_cols:
            imp_data[0]["target"] = "Shady Oaks"
            imp_data[1]["target"] = "Shady Oaks"
            imp_data[2]["target"] = "Shady Oaks/Cox/Brown"
        n = safe_insert(conn, "impeachment_matrix", imp_data)
        print(f"  impeachment_matrix (housing): {n} rows inserted")


def verify_persistence(conn):
    """Verify row counts after persistence."""
    print("\n=== VERIFICATION ===")
    tables = ["berry_mcneill_intelligence", "evidence_quotes", "timeline_events", 
              "impeachment_matrix", "judicial_violations"]
    for t in tables:
        if table_exists(conn, t):
            count = conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
            print(f"  {t}: {count} total rows")


def main():
    print(f"Persisting harvest intelligence to {DB}")
    print(f"Timestamp: {datetime.datetime.now().isoformat()}")
    
    conn = get_conn()
    
    try:
        persist_mcneill_intelligence(conn)
        persist_shady_intelligence(conn)
        verify_persistence(conn)
        print("\n=== PERSISTENCE COMPLETE ===")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
