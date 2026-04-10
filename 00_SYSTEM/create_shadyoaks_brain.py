"""
SHADYOAKS-DESTRUCTION Brain DB Creator
Creates 00_SYSTEM/brains/shadyoaks_brain.db with all known intelligence.
Run from D:\LitigationOS_tmp to avoid shadow module issues.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

import sqlite3
from datetime import datetime

DB_PATH = r"C:\Users\andre\LitigationOS\00_SYSTEM\brains\shadyoaks_brain.db"

def create_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA synchronous=NORMAL")
    c = conn.cursor()

    # ── ENTITIES TABLE ─────────────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS entities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        entity_type TEXT, -- LLC, INDIVIDUAL, COURT, AGENCY
        role TEXT,
        state_of_reg TEXT,
        reg_status TEXT,   -- ACTIVE, DISSOLVED, UNKNOWN
        address TEXT,
        contact TEXT,
        notes TEXT,
        threat_level INTEGER DEFAULT 0, -- 1-10
        created_at TEXT DEFAULT (datetime('now'))
    )""")

    # ── LLC CHAIN TABLE ─────────────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS llc_chain (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_name TEXT NOT NULL,
        parent_entity TEXT,
        state_of_reg TEXT,
        registration_num TEXT,
        reg_status TEXT,
        reg_agent TEXT,
        principal_address TEXT,
        mi_lara_license TEXT,
        dissolved_date TEXT,
        notes TEXT
    )""")

    # ── TIMELINE EVENTS TABLE ───────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS timeline_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_date TEXT,
        event_type TEXT,
        actor TEXT,
        target TEXT,
        description TEXT NOT NULL,
        legal_significance TEXT,
        evidence_refs TEXT,
        lane TEXT DEFAULT 'B',
        severity INTEGER DEFAULT 5
    )""")

    # ── EVIDENCE REGISTRY TABLE ─────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS evidence_registry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exhibit_id TEXT,
        description TEXT NOT NULL,
        file_path TEXT,
        evidence_type TEXT,
        date_of_evidence TEXT,
        actors_involved TEXT,
        legal_theory TEXT,
        bates_number TEXT,
        status TEXT DEFAULT 'UNPROCESSED',
        notes TEXT
    )""")

    # ── LARA INTELLIGENCE TABLE ─────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS lara_intelligence (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_title TEXT,
        file_path TEXT,
        lara_license TEXT,
        entity_name TEXT,
        violation_type TEXT,
        date TEXT,
        agency TEXT,
        significance TEXT,
        notes TEXT
    )""")

    # ── POST EVICTION TORTS TABLE ───────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS post_eviction_torts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tort_name TEXT NOT NULL,
        date TEXT,
        actor TEXT,
        witness TEXT,
        description TEXT,
        evidence TEXT,
        damages_conservative INTEGER,
        damages_aggressive INTEGER,
        legal_authority TEXT,
        status TEXT DEFAULT 'UNPLED'
    )""")

    # ── JUDICIAL CARTEL TABLE ───────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS judicial_cartel (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        judge_name TEXT NOT NULL,
        court TEXT,
        case_number TEXT,
        relationship TEXT,
        conduct TEXT,
        violation TEXT,
        canon TEXT,
        evidence TEXT,
        impact TEXT
    )""")

    # ── COERCION EMAILS TABLE ───────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS coercion_emails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        from_entity TEXT,
        to_party TEXT,
        subject TEXT,
        summary TEXT,
        legal_significance TEXT,
        file_path TEXT,
        exhibit_id TEXT
    )""")

    # ── DAMAGES SCHEDULE TABLE ──────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS damages_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        claim TEXT NOT NULL,
        legal_authority TEXT,
        damages_conservative INTEGER,
        damages_aggressive INTEGER,
        multiplier TEXT,
        notes TEXT
    )""")

    # ── LEGAL THEORIES TABLE ────────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS legal_theories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        count_number INTEGER,
        theory_name TEXT NOT NULL,
        authority TEXT,
        elements TEXT,
        evidence_summary TEXT,
        status TEXT DEFAULT 'VIABLE',
        layer_ref TEXT
    )""")

    # ── WITNESSES TABLE ─────────────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS witnesses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT,
        affiliation TEXT,
        contact TEXT,
        testimony_value TEXT,
        subpoena_priority INTEGER DEFAULT 5,
        notes TEXT
    )""")

    # ── CONTRADICTIONS TABLE ────────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS contradictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        actor TEXT,
        statement_a TEXT,
        source_a TEXT,
        statement_b TEXT,
        source_b TEXT,
        significance TEXT,
        impeachment_value INTEGER DEFAULT 5
    )""")

    # ── FALSE ALLEGATIONS TABLE ─────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS false_allegations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        actor TEXT,
        allegation TEXT,
        rebuttal TEXT,
        evidence TEXT,
        charges_filed TEXT DEFAULT 'NO'
    )""")

    conn.commit()

    # ════════════════════════════════════════════════════════════════════════════
    # POPULATE ENTITIES
    # ════════════════════════════════════════════════════════════════════════════
    entities = [
        ("Alden Global Capital LLC", "LLC", "Ultimate Controller", "NY", "ACTIVE",
         "New York", "Founders: Randall Smith, Heath Freeman", 10),
        ("Alden Global Capital Advisors LP", "LLC", "Affiliated Fund", "NY", "ACTIVE",
         "New York", "hedge fund, distressed debt", 10),
        ("Homes of America LLC", "LLC", "Operator/Manager", "DE/NJ", "ACTIVE",
         "77 Engle St, Englewood NJ 07631", "mhp@ourhomesofamerica.com; Bryon Fields; 646-779-4400", 10),
        ("Shady Oaks Park MHP LLC", "LLC", "Named Defendant – DISSOLVED NJ 2022", "NJ", "DISSOLVED",
         "1977 Whitehall Rd, North Muskegon MI 49445", "License #1201891 (LARA-BCC)", 10),
        ("Cricklewood MHP LLC", "LLC", "Sister Entity – Still Operating", "NJ/FL/TX", "ACTIVE",
         None, "Used same management and controls", 9),
        ("Partridge Equity Group", "LLC", "Real Estate Fund/Equity Arm", "Unknown", "UNKNOWN",
         None, "Alden capital vehicle", 9),
        ("VRM Capital Corp", "LLC", "Capital Vehicle", "Unknown", "UNKNOWN",
         None, "Linked to Alden/Partridge", 8),
        ("Nicole Browley", "INDIVIDUAL", "Park Manager – Primary Executor",
         None, None, "Shady Oaks Park", "Authorized entry per Dep. Schmidt; borrowed drill from neighbor", 10),
        ("Kim Davis", "INDIVIDUAL", "Park Manager – Prior Operations", None, None,
         "Shady Oaks Park", "Management continuity", 8),
        ("Cassandra VanDam", "INDIVIDUAL", "Park Manager – Facebook Confession",
         None, None, "Shady Oaks Park", "Feb 18 2026: told buyer Andrew 'abandoned' trailer", 10),
        ("Shelly Przybalek", "INDIVIDUAL", "Manager – Multiple Parks", None, None,
         None, "Involved across entities: Cricklewood, South Haven, River Haven", 8),
        ("Jeremy Brown", "INDIVIDUAL", "Defense Attorney – Fraud on Court",
         None, None, None, "P77427; inserted res judicata language; accused Andrew of signature forgery", 10),
        ("Bryon Fields", "INDIVIDUAL", "Homes of America Principal",
         None, None, "77 Engle St, Englewood NJ 07631", "LARA contact; mhp@ourhomesofamerica.com", 9),
        ("Hon. Maria Ladas-Hoopes", "COURT", "60th District – Eviction Judge",
         None, None, None, "Wife of Kenneth Hoopes; former partner Ladas Hoopes & McNeill", 10),
        ("Hon. Kenneth Hoopes", "COURT", "14th Circuit – Housing + Chief Judge",
         None, None, None, "Former partner McNeill; dismissed housing case; denied emergency order then vacationed", 10),
        ("Hon. Jenny L. McNeill", "COURT", "14th Circuit – Custody + PPO",
         None, None, None, "Former partner Hoopes; used housing instability to suspend parenting time", 10),
        ("EGLE", "AGENCY", "Environmental Regulator",
         None, None, None, "VN-017235 sewage violation; Amanda StAmour investigator", 7),
        ("LARA-BCC", "AGENCY", "MI Licensing and Regulatory Affairs",
         None, None, None, "License #1201891 issued to Shady Oaks; Valerie (licensing); told EGLE: Bryon Fields contact", 8),
        ("Carmyn Hanna", "INDIVIDUAL", "Prospective Buyer – Adverse Witness",
         None, None, None, "Received VanDam FB Messenger msg Feb 18 2026 stating abandonment", 9),
        ("Deputy Douglas Schmidt", "INDIVIDUAL", "Muskegon Co. Sheriff – Eviction Witness",
         None, None, None, "Present July 17 2025; Browley stated HoA authorized entry to Schmidt", 8),
        ("Aaron Cox", "INDIVIDUAL", "Associated Individual", None, None, None, "Named in prior litigation", 7),
        ("Joseph Khalil", "INDIVIDUAL", "Associated Individual", None, None, None, "Named in prior litigation", 7),
    ]
    c.executemany("""INSERT OR IGNORE INTO entities
        (name, entity_type, role, state_of_reg, reg_status, address, contact, threat_level)
        VALUES (?,?,?,?,?,?,?,?)""", entities)

    # ════════════════════════════════════════════════════════════════════════════
    # POPULATE LLC CHAIN
    # ════════════════════════════════════════════════════════════════════════════
    llcs = [
        ("Alden Global Capital LLC", None, "NY", None, "ACTIVE",
         "CT Corporation System", "New York, NY", None, None,
         "Ultimate controller – Randall Smith + Heath Freeman"),
        ("Alden Global Capital Advisors LP", "Alden Global Capital LLC", "NY", None, "ACTIVE",
         "CT Corporation System", "New York, NY", None, None,
         "Hedge fund arm – distressed debt investment vehicle"),
        ("Homes of America LLC", "Alden Global Capital LLC", "DE/NJ", None, "ACTIVE",
         None, "77 Engle St, Englewood NJ 07631", None, None,
         "Operator; manages all MHP properties under Alden umbrella"),
        ("Shady Oaks Park MHP LLC", "Homes of America LLC", "NJ", None, "DISSOLVED",
         None, "1977 Whitehall Rd, North Muskegon MI 49445", "1201891",
         "2022",
         "DISSOLVED 2022 – had NO standing to maintain any legal action; all acts VOID under MCL 450.4802"),
        ("Cricklewood MHP LLC (NJ)", "Homes of America LLC", "NJ", None, "ACTIVE",
         None, None, None, None,
         "Sister entity – same management team; used interchangeably with Shady Oaks"),
        ("Cricklewood MHP LLC (FL)", "Homes of America LLC", "FL", None, "ACTIVE",
         None, None, None, None,
         "Florida registration – same enterprise name"),
        ("Cricklewood MHP LLC (TX)", "Homes of America LLC", "TX", None, "ACTIVE",
         None, None, None, None,
         "Texas registration – same enterprise, veil-pierce target"),
        ("Partridge Equity Group", "Alden Global Capital LLC", "Unknown", None, "UNKNOWN",
         None, None, None, None,
         "Capital vehicle / equity arm; role in eviction proceedings unclear; LARA may reveal details"),
        ("VRM Capital Corp", "Alden Global Capital LLC", "Unknown", None, "UNKNOWN",
         None, None, None, None,
         "Additional capital vehicle; linked to Alden/Partridge"),
    ]
    c.executemany("""INSERT OR IGNORE INTO llc_chain
        (entity_name, parent_entity, state_of_reg, registration_num, reg_status,
         reg_agent, principal_address, mi_lara_license, dissolved_date, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?)""", llcs)

    # ════════════════════════════════════════════════════════════════════════════
    # POPULATE TIMELINE EVENTS
    # ════════════════════════════════════════════════════════════════════════════
    events = [
        ("2022-XX-XX", "LEGAL", "Shady Oaks Park MHP LLC", "NJ State",
         "Shady Oaks Park MHP LLC DISSOLVED by New Jersey",
         "Dissolved entity has no legal capacity to sue or hold property under MCL 450.4802",
         "LARA records; NJ corporate filings", "B", 10),
        ("2024-12-XX", "ENTITY_FRAUD", "Homes of America LLC", "Andrew Pigors",
         "Homes of America took over Shady Oaks management without disclosing entity change to tenants",
         "Failure to disclose operator change; tenants not informed; MCL 125.2303 compliance failure",
         "Lease documents; ledger changes; Andrew testimony", "B", 9),
        ("2025-XX-XX", "COERCION", "Homes of America / Management", "Andrew Pigors",
         "HOA sent emails trying to coerce Andrew into selling his trailer and handing over the keys BEFORE hearing",
         "Pre-litigation coercion; constitutes evidence of intent to dispossess without due process",
         "Emails – Andrew has copies", "B", 10),
        ("2025-05-06", "REGULATORY", "Andrew Pigors", "LARA / AG",
         "Andrew filed formal LARA and AG complaints regarding Shady Oaks licensing deception and LLC fraud",
         "Creates regulatory record; supports RICO predicate; AG investigation potential",
         "01_EVIDENCE/HOUSING/2025-05-06_MI_LARA_Complaint_ShadyOaks.docx; 2025-05-06_AG_LARA_Formal_Complaint_ShadyOaks.docx",
         "B", 8),
        ("2025-07-17", "EVICTION", "Hon. Maria Ladas-Hoopes / HOA", "Andrew Pigors",
         "Writ of eviction/lot return executed. Andrew called Muskegon County Sheriff after security cameras caught defendants drilling locks. Deputy Douglas Schmidt present. Nicole Browley stated Homes of America authorized entry.",
         "Andrew CALLED the police (exculpatory). HOA used dissolved entity to obtain writ. Ladas-Hoopes presided over eviction proceedings in 60th District.",
         "Security camera footage; police report; Andrew affidavit; Browley statement to Schmidt", "B", 10),
        ("2025-07-17", "PROPERTY_CRIME", "Nicole Browley / HOA", "Andrew Pigors",
         "Defendants borrowed drill from neighbor, drilled off Andrew's deadbolt, removed ALL personal belongings, threw them in the yard, installed new lock.",
         "Criminal trespass; conversion; tortious; L.D.W.'s belongings included – child harm documented",
         "Security camera footage; witness (neighbor who lent drill); Deputy Schmidt police report", "B", 10),
        ("2025-07-17", "PROPERTY_CRIME", "HOA / Management", "Andrew Pigors + L.D.W.",
         "Defendants smashed L.D.W.'s belongings during eviction execution. Child's property destroyed.",
         "Destruction of child's belongings = separate damages; MCL 722.23 child harm factor",
         "Security camera footage; Andrew testimony; photos before/after", "B", 10),
        ("2025-07-18", "CONVERSION", "HOA / Management", "Andrew Pigors",
         "Less than 24 hours after eviction: defendants placed 'FOR FREE' sign on Andrew's personal belongings in the yard",
         "Conversion (MCL 600.2919a): exercising dominion over another's property. Treble damages available.",
         "Photos; witness testimony; Andrew testimony", "B", 10),
        ("2025-07-XX", "FALSE_POLICE_REPORT", "HOA / Management", "Andrew Pigors",
         "Defendants filed FALSE police report claiming Andrew came back and smashed THEIR locks off of HIS home",
         "False police report (MCL 750.411a); fabricated reverse allegation to criminalize Andrew's attempt to access own property",
         "Police report (NSPD); Andrew's security camera footage (exculpatory); Andrew testimony", "B", 10),
        ("2025-08-09", "JUDICIAL_CARTEL", "Hon. Kenneth Hoopes", "Andrew Pigors",
         "Andrew petitioned 14th Circuit (Hoopes) for emergency order to stop eviction. Hoopes DENIED and went on vacation.",
         "Dereliction of duty; failure to act on emergency; conflict with Ladas-Hoopes (wife) who issued eviction writ",
         "14th Circuit docket; Andrew petition; Hoopes order of denial", "B", 10),
        ("2025-XX-XX", "JUDICIAL_CARTEL", "Hon. Kenneth Hoopes", "Andrew Pigors",
         "Hoopes dismissed 2025-002760-CZ with prejudice. Jeremy Brown's proposed order inserted 'res judicata' language that Hoopes did NOT orally rule.",
         "Fraud on the court; Brown MCR 9.104/MRPC 3.3/8.4(c); Hoopes signed order containing language he did not rule",
         "Hearing transcript; proposed order; final order – side-by-side comparison", "B", 10),
        ("2026-02-18", "CONVERSION", "Cassandra VanDam", "Andrew Pigors",
         "VanDam told prospective buyer Carmyn Hanna via Facebook Messenger that Andrew 'abandoned' his trailer and/or 'does not own the home'",
         "Slander of Title (MCL 565.108); Tortious Interference; Wire Fraud predicate; 3rd blocked sale",
         "Facebook Messenger screenshot; VanDam account ID; Carmyn Hanna (subpoena target)", "B", 10),
    ]
    c.executemany("""INSERT OR IGNORE INTO timeline_events
        (event_date, event_type, actor, target, description, legal_significance, evidence_refs, lane, severity)
        VALUES (?,?,?,?,?,?,?,?,?)""", events)

    # ════════════════════════════════════════════════════════════════════════════
    # POPULATE EVIDENCE REGISTRY
    # ════════════════════════════════════════════════════════════════════════════
    evidence = [
        ("EX-B-LARA-01", "LARA license #1201891 communication – EGLE/LARA email chain showing Bryon Fields as contact",
         "01_EVIDENCE/HOUSING/EX_MISC_RE_ Shady Oaks Park MHP License # 1201891.pdf_001.txt",
         "EMAIL", "2025-04-04", "LARA-BCC; EGLE Amanda StAmour; Bryon Fields", "RICO predicate; operator ID", None, "ACTIVE"),
        ("EX-B-LARA-02", "Exhibit D LARA HOA Ownership records",
         "01_EVIDENCE/HOUSING/Exhibit_D_LARA_HOA_Ownership.pdf",
         "PDF", "2025", "LARA; Homes of America", "Entity fraud; piercing veil", None, "ACTIVE"),
        ("EX-B-LARA-03", "MI LARA Formal Complaint filed by Andrew – May 2025",
         "01_EVIDENCE/HOUSING/2025-05-06_MI_LARA_Complaint_ShadyOaks.docx",
         "DOCX", "2025-05-06", "Andrew Pigors; LARA", "Regulatory record; AG referral", None, "ACTIVE"),
        ("EX-B-LARA-04", "AG LARA Formal Complaint – May 2025",
         "01_EVIDENCE/HOUSING/2025-05-06_AG_LARA_Formal_Complaint_ShadyOaks.docx",
         "DOCX", "2025-05-06", "Andrew Pigors; MI Attorney General", "AG investigation trigger", None, "ACTIVE"),
        ("EX-B-LARA-05", "LARA License Deception Report",
         "04_ANALYSIS/LARA_License_Deception_Report_1.docx",
         "DOCX", "2025", "LARA; Shady Oaks", "License fraud; dissolved entity operating under active license", None, "ACTIVE"),
        ("EX-B-LARA-06", "LARA Enforcement Narrative Summary",
         "04_ANALYSIS/2025-05-06_LARA_ENFORCEMENT_Narrative_Summary_1.pdf",
         "PDF", "2025-05-06", "Andrew Pigors", "Summary of LARA enforcement violations", None, "ACTIVE"),
        ("EX-B-EGLE-01", "EGLE Violation Notice VN-017235 – Sewage discharge onto ground",
         "01_EVIDENCE/HOUSING/",
         "PDF", "2025", "EGLE; Shady Oaks", "Constructive eviction; habitability; environmental tort", None, "ACTIVE"),
        ("EX-B-CAM-01", "Security camera footage: July 17 2025 – defendants drilling Andrew's deadbolt",
         "Security cameras at 1977 Whitehall Rd Lot 17",
         "VIDEO", "2025-07-17", "Nicole Browley; HOA employees", "Conversion; trespass; exculpatory (Andrew called police)", None, "CRITICAL"),
        ("EX-B-FB-01", "Facebook Messenger screenshot: VanDam to Carmyn Hanna Feb 18 2026 – 'abandoned' statement",
         "01_EVIDENCE/HOUSING/",
         "SCREENSHOT", "2026-02-18", "Cassandra VanDam; Carmyn Hanna", "Slander of Title; Tortious Interference; Wire Fraud predicate", None, "CRITICAL"),
        ("EX-B-EMAIL-COERCE", "HOA coercion emails – attempting to get Andrew to sell trailer and hand over keys BEFORE hearing",
         "Email records – Andrew has copies",
         "EMAIL", "2025", "HOA / Management", "Pre-litigation coercion; civil conspiracy; intent to dispossess", None, "CRITICAL"),
        ("EX-B-POLICE-FALSE", "False police report filed by HOA claiming Andrew broke their locks",
         "NSPD records",
         "POLICE_REPORT", "2025-07-XX", "HOA / Management", "MCL 750.411a false report; reverse criminalization pattern", None, "CRITICAL"),
        ("EX-B-PHOTO-DEST", "Photos of destruction of Andrew and L.D.W.'s belongings post-eviction",
         "Andrew's phone / security camera",
         "PHOTO", "2025-07-17", "HOA / Nicole Browley", "Conversion; child harm; damages documentation", None, "CRITICAL"),
        ("EX-B-PHOTO-FREE", "'FOR FREE' sign on Andrew's belongings – placed by defendants",
         "Andrew's phone / security camera",
         "PHOTO", "2025-07-18", "HOA / Management", "Conversion (MCL 600.2919a) – treble damages", None, "CRITICAL"),
        ("EX-B-HOOPES-DENY", "Hoopes denial of emergency petition to stop eviction (then went on vacation)",
         "14th Circuit docket 2025-002760-CZ",
         "COURT_ORDER", "2025-08-09", "Hon. Kenneth Hoopes", "Dereliction; conflict of interest; cartel coordination", None, "CRITICAL"),
        ("EX-B-LADA-WRIT", "Writ of eviction/lot return issued by Ladas-Hoopes (60th District)",
         "60th District Court records",
         "COURT_ORDER", "2025-07-17", "Hon. Maria Ladas-Hoopes", "Judicial cartel; standing issue (dissolved LLC had no right to petition)", None, "CRITICAL"),
        ("EX-B-BROWN-ORDER", "Jeremy Brown's proposed order inserting res judicata language",
         "14th Circuit docket",
         "COURT_ORDER", "2025", "Jeremy Brown P77427", "Fraud on court; MCR 9.104; MRPC 3.3; 8.4(c)", None, "CRITICAL"),
        ("EX-B-DOOR-PHOTOS", "Photos of what was posted on Andrew's door (rebutting Brown's false signature allegation)",
         "Andrew's phone",
         "PHOTO", "2025", "Andrew Pigors", "Rebuttal of Brown's forgery accusation", None, "ACTIVE"),
    ]
    c.executemany("""INSERT OR IGNORE INTO evidence_registry
        (exhibit_id, description, file_path, evidence_type, date_of_evidence, actors_involved, legal_theory, bates_number, status)
        VALUES (?,?,?,?,?,?,?,?,?)""", evidence)

    # ════════════════════════════════════════════════════════════════════════════
    # POPULATE LARA INTELLIGENCE
    # ════════════════════════════════════════════════════════════════════════════
    lara_rows = [
        ("LARA BCC License Email Chain", "01_EVIDENCE/HOUSING/EX_MISC_RE_ Shady Oaks Park MHP License # 1201891.pdf_001.txt",
         "1201891", "Shady Oaks Park MHP LLC", "Operating under license of dissolved entity",
         "2025-04-04", "LARA-BCC + EGLE",
         "Bryon Fields identified as Homes of America contact; license issued to dissolved NJ entity"),
        ("Exhibit D – LARA HOA Ownership", "01_EVIDENCE/HOUSING/Exhibit_D_LARA_HOA_Ownership.pdf",
         "1201891", "Homes of America LLC", "Undisclosed ownership transfer",
         "2025", "LARA",
         "Shows HOA as actual operator; license still in dissolved Shady Oaks name"),
        ("LARA Formal Complaint (Andrew)", "01_EVIDENCE/HOUSING/2025-05-06_MI_LARA_Complaint_ShadyOaks.docx",
         "1201891", "Shady Oaks Park MHP LLC / HOA", "Licensing deception; dissolved entity",
         "2025-05-06", "MI LARA",
         "Filed by Andrew; creates regulatory record; supports AG referral"),
        ("AG LARA Formal Complaint", "01_EVIDENCE/HOUSING/2025-05-06_AG_LARA_Formal_Complaint_ShadyOaks.docx",
         "1201891", "Shady Oaks / HOA", "Multi-LLC fraud; abandoned tenant protections",
         "2025-05-06", "MI Attorney General",
         "AG referral complaint; RICO predicate; consumer protection"),
        ("LARA License Deception Report", "04_ANALYSIS/LARA_License_Deception_Report_1.docx",
         "1201891", "Shady Oaks Park MHP LLC", "License deception; dissolved entity continuing operations",
         "2025", "Internal Analysis",
         "Full analysis of how dissolved entity continued using LARA license"),
        ("LARA Enforcement Narrative Summary", "04_ANALYSIS/2025-05-06_LARA_ENFORCEMENT_Narrative_Summary_1.pdf",
         "1201891", "Shady Oaks / HOA", "Multiple regulatory violations",
         "2025-05-06", "Internal Analysis",
         "Summary of all LARA violations for enforcement purposes"),
    ]
    c.executemany("""INSERT OR IGNORE INTO lara_intelligence
        (document_title, file_path, lara_license, entity_name, violation_type, date, agency, significance)
        VALUES (?,?,?,?,?,?,?,?)""", lara_rows)

    # ════════════════════════════════════════════════════════════════════════════
    # POPULATE POST EVICTION TORTS
    # ════════════════════════════════════════════════════════════════════════════
    torts = [
        ("Lock Drilling – Unauthorized Entry", "2025-07-17", "Nicole Browley / HOA",
         "Deputy Douglas Schmidt; neighbor (lent drill); Andrew Pigors; security cameras",
         "Defendants borrowed neighbor's drill, drilled off Andrew's deadbolt to execute eviction. Andrew had called sheriff himself (exculpatory – he reported it).",
         "Security camera footage; Deputy Schmidt report; neighbor testimony; Andrew affidavit",
         5000, 15000, "MCL 600.2918; MCL 750.110 (breaking/entering); Trespass",
         "UNPLED"),
        ("Destruction of Personal Belongings", "2025-07-17", "Nicole Browley / HOA employees",
         "Andrew Pigors; Deputy Schmidt; security cameras",
         "All personal belongings removed from home, thrown in yard. Items damaged and destroyed during removal.",
         "Security camera footage; photos before/after; Andrew testimony; Deputy Schmidt present",
         25000, 75000, "MCL 600.2919a (conversion, treble damages); MCL 600.2918 (wrongful eviction)",
         "UNPLED"),
        ("Destruction of L.D.W.'s Belongings", "2025-07-17", "Nicole Browley / HOA employees",
         "Andrew Pigors; L.D.W. (minor child); security cameras",
         "Child's personal belongings (toys, clothing, etc.) smashed and destroyed during eviction execution. Child was present.",
         "Security camera footage; photos; Andrew testimony; L.D.W. harm documentation",
         10000, 35000, "MCL 600.2919a; MCL 722.23 child harm; intentional infliction of emotional distress",
         "UNPLED"),
        ("'FOR FREE' Sign on Personal Property", "2025-07-18", "HOA / Management",
         "Andrew Pigors; potential buyer witnesses; photos",
         "Less than 24 hours post-eviction: defendants placed 'FOR FREE' sign on Andrew's personal belongings left in yard.",
         "Photos (Andrew's phone/security cameras); witness testimony; timeline documentation",
         15000, 45000, "MCL 600.2919a conversion (treble damages); conversion by dominion; trespass to chattels",
         "UNPLED"),
        ("New Lock Installation – Lockout", "2025-07-17", "Nicole Browley / HOA",
         "Andrew Pigors; Deputy Schmidt; security cameras",
         "Defendants replaced all locks with new locks, permanently locking Andrew out of his own home while title remained in his name.",
         "Security camera footage; lock change records; Andrew's certificate of title; Deputy Schmidt present",
         10000, 30000, "MCL 600.2918 (wrongful eviction); MCL 600.2919a; constructive possession",
         "UNPLED"),
        ("False Police Report – Reverse Criminalization", "2025-07-XX", "HOA / Management",
         "Andrew Pigors; NSPD records; Andrew's security cameras (exculpatory)",
         "Defendants filed false police report claiming Andrew came back and smashed THEIR locks off of HIS home. Andrew had never returned. Security cameras prove his absence.",
         "NSPD false report records; Andrew's security camera footage showing no return; Andrew affidavit",
         0, 0, "MCL 750.411a (false report to peace officer); malicious prosecution; abuse of process",
         "UNPLED"),
        ("Seizure of 7 Manufactured Home Titles", "2025-07-17", "HOA / Management",
         "Andrew Pigors; LARA records; title records",
         "Defendants seized 7 manufactured home titles on the day of eviction – pretending to own the titles.",
         "Title records; LARA documents; Andrew testimony",
         35000, 105000, "MCL 600.2919a treble; title conversion; slander of title",
         "UNPLED"),
        ("Removal of Critical Legal Documents and Exhibits", "2025-07-17", "HOA / Management",
         "Andrew Pigors; testimony",
         "During eviction execution, critical legal documents and litigation exhibits were removed from Andrew's home without inventory or preservation.",
         "Andrew affidavit; list of missing documents",
         10000, 50000, "Spoliation; conversion; MCL 600.2919a; due process harm (MCL 600.2918)",
         "UNPLED"),
    ]
    c.executemany("""INSERT OR IGNORE INTO post_eviction_torts
        (tort_name, date, actor, witness, description, evidence, damages_conservative, damages_aggressive, legal_authority, status)
        VALUES (?,?,?,?,?,?,?,?,?,?)""", torts)

    # ════════════════════════════════════════════════════════════════════════════
    # POPULATE JUDICIAL CARTEL
    # ════════════════════════════════════════════════════════════════════════════
    cartel = [
        ("Hon. Maria Ladas-Hoopes", "60th District Court", "2025-25061626LT-LT (eviction)",
         "Wife of Chief Judge Kenneth Hoopes; former partner Ladas, Hoopes & McNeill (435 Whitehall Rd)",
         "Issued writ of eviction/lot return to dissolved LLC with no standing. Allowed HOA to proceed despite ownership fraud.",
         "MCR 2.003(C)(1)(b) – bias; MCR 2.003(C)(2)(a) – appearance of partiality",
         "Canon 3C – failure to recuse; Canon 2A – failure to disclose",
         "Writ of eviction; 60th District docket",
         "Eviction executed by wife's court – weaponized against Andrew; fed into custody/housing cartel loop"),
        ("Hon. Kenneth Hoopes", "14th Circuit – Civil", "2025-002760-CZ",
         "Former partner McNeill; husband of Ladas-Hoopes; CHIEF JUDGE (reassignment gatekeeper)",
         "Dismissed housing case with prejudice. Denied emergency order to stop eviction then went on vacation. Signed Brown's fraudulent order containing res judicata language Hoopes never orally ruled.",
         "MCR 2.003(D)(1) – failed to recuse or disclose; MCR 2.003(C)(1)(b)(c)",
         "Canon 2A – failure to disclose; Canon 3C – failure to recuse; Canon 3B – signed fraudulent order",
         "Housing case docket; Hoopes' order of denial; final dismissal order vs. transcript",
         "Killed housing case; enabled cartel feedback loop: housing loss → custody loss"),
        ("Hon. Jenny L. McNeill", "14th Circuit – Family", "2024-001507-DC; 2023-5907-PP",
         "Former partner Ladas, Hoopes & McNeill; married Cavan Berry (FOC building attorney)",
         "Used Andrew's housing instability (caused by Ladas-Hoopes eviction + Hoopes dismissal) to justify suspending all parenting time. Aug 8 2025: five ex parte orders.",
         "MCR 2.003(D)(1); MCR 2.003(C)(1)(b); 5,059 documented violations",
         "Canon 3C; Canon 2A; Canon 1",
         "Custody docket; hearing transcripts; five ex parte orders",
         "Weaponized housing crisis (created by firm partners) to destroy custody. The perfect closed cartel loop."),
    ]
    c.executemany("""INSERT OR IGNORE INTO judicial_cartel
        (judge_name, court, case_number, relationship, conduct, violation, canon, evidence, impact)
        VALUES (?,?,?,?,?,?,?,?,?)""", cartel)

    # ════════════════════════════════════════════════════════════════════════════
    # POPULATE CONTRADICTIONS
    # ════════════════════════════════════════════════════════════════════════════
    contradictions = [
        ("Homes of America / Shady Oaks",
         "HOA/SO claimed to own Andrew's manufactured home and have right to evict",
         "HOA communications and court filings",
         "HOA sent emails acknowledging they did NOT know whether they owned the trailer; tried to coerce Andrew into selling it to them",
         "HOA coercion emails (pre-litigation)",
         "They claimed ownership in court but privately admitted they didn't know if they owned it",
         10),
        ("Jeremy Brown P77427",
         "Brown claimed Andrew forged judge's signature",
         "Allegations during litigation",
         "Andrew has photos of what was actually posted on his door; no charges were ever filed; allegation abandoned",
         "Photos of door posting; no criminal charges filed; allegation never pursued",
         "False accusation – no charges, no evidence, abandoned by Brown",
         10),
        ("HOA / Management",
         "Defendants told prospective buyer Andrew 'abandoned' his trailer",
         "VanDam Facebook Messenger Feb 18 2026",
         "Andrew never abandoned his home; he was forcibly evicted while calling sheriff himself (exculpatory)",
         "Security camera footage; Andrew affidavit; Andrew called sheriff (NSPD records)",
         "Their own 'abandonment' claim is destroyed by Andrew's act of calling the police to resist the eviction",
         10),
        ("HOA / Management",
         "Filed police report claiming Andrew came back and smashed their locks",
         "NSPD records",
         "Andrew's security cameras show he never returned; Andrew called police himself at time of eviction (he is the victim, not perpetrator)",
         "Security camera footage (no return); NSPD records of Andrew's own call July 17 2025",
         "False police report directly contradicted by security camera footage",
         10),
        ("Shady Oaks Park MHP LLC",
         "Filed and maintained legal actions in Michigan courts",
         "2025-002760-CZ docket; 2025-25061626LT-LT",
         "Shady Oaks Park MHP LLC was DISSOLVED in New Jersey in 2022 – no legal capacity to sue",
         "LARA records; NJ corporate dissolution records; MCL 450.4802",
         "Dissolved entity cannot maintain any legal action; all acts VOID as matter of law",
         10),
    ]
    c.executemany("""INSERT OR IGNORE INTO contradictions
        (actor, statement_a, source_a, statement_b, source_b, significance, impeachment_value)
        VALUES (?,?,?,?,?,?,?)""", contradictions)

    # ════════════════════════════════════════════════════════════════════════════
    # POPULATE FALSE ALLEGATIONS
    # ════════════════════════════════════════════════════════════════════════════
    false_alleg = [
        ("2025-XX-XX", "Jeremy Brown P77427",
         "Alleged Andrew Pigors falsified/forged the judge's signature on a document",
         "Andrew vehemently denied. Has photos of what was posted on his door. Brown never pursued charges and allegation was abandoned.",
         "Photos of door posting (Andrew's phone); no criminal charges filed; allegation abandoned",
         "NO"),
        ("2025-07-XX", "HOA / Management",
         "Filed false police report claiming Andrew returned to property and smashed their locks off his home",
         "Andrew's security cameras show he never returned. Andrew was the one who called the police on July 17 2025.",
         "NSPD records showing Andrew's call; security camera footage; Andrew affidavit",
         "NO"),
        ("2026-02-18", "Cassandra VanDam",
         "Told prospective buyer Carmyn Hanna that Andrew 'abandoned' his trailer and 'does not own the home'",
         "Andrew never abandoned his home. He holds the certificate of title for VIN 1646732. He was forcibly evicted.",
         "Certificate of title VIN 1646732; Andrew affidavit; security camera footage; Andrew called police himself",
         "NO"),
    ]
    c.executemany("""INSERT OR IGNORE INTO false_allegations
        (date, actor, allegation, rebuttal, evidence, charges_filed)
        VALUES (?,?,?,?,?,?)""", false_alleg)

    # ════════════════════════════════════════════════════════════════════════════
    # POPULATE DAMAGES SCHEDULE
    # ════════════════════════════════════════════════════════════════════════════
    damages = [
        ("Wrongful Eviction (MCL 600.2918)", "MCL 600.2918", 50000, 150000, "2×", "Base + double damages under statute"),
        ("Conversion – Manufactured Home Title (MCL 600.2919a)", "MCL 600.2919a", 25000, 45000, "3×", "Treble damages on home value"),
        ("Conversion – Personal Belongings", "MCL 600.2919a", 25000, 75000, "3×", "Treble on destroyed/stolen property"),
        ("Conversion – L.D.W.'s Belongings", "MCL 600.2919a; MCL 722.23", 10000, 35000, "3×", "Child's property + child harm"),
        ("Conversion – 7 Manufactured Home Titles", "MCL 600.2919a", 35000, 105000, "3×", "Treble on 7 title conversions"),
        ("Slander of Title (MCL 565.108)", "MCL 565.108", 25000, 75000, "1×", "Title cloud damages"),
        ("Tortious Interference – 3 Blocked Sales", "Prysak v R.L. Polk", 75000, 135000, "1×", "3 blocked sales × avg $35K"),
        ("False Police Report Damages", "MCL 750.411a; malicious prosecution", 15000, 50000, "1×", "Prosecution costs + reputational harm"),
        ("Post-Eviction Destruction – Lock Drilling", "MCL 600.2918; trespass", 5000, 15000, "1×", "Actual damages"),
        ("Post-Eviction – Legal Document Removal", "MCL 600.2919a; spoliation", 10000, 50000, "1×", "Critical litigation harm"),
        ("EGLE Sewage Constructive Eviction", "MCL 125.2319; MCL 554.139", 20000, 60000, "1×", "Habitability + constructive eviction"),
        ("LLC Fraud / Entity Deception", "MCL 450.4802; RICO", 50000, 150000, "3×", "RICO treble on predicate acts"),
        ("42 USC 1983 – Judicial Cartel (Hoopes + Ladas-Hoopes)", "42 USC 1983", 100000, 500000, "Punitive", "Constitutional deprivation of property + housing"),
        ("42 USC 1985(3) – Conspiracy (Private + State Actors)", "42 USC 1985(3)", 50000, 250000, "Punitive", "Civil conspiracy; housing + custody cartel"),
        ("RICO (18 USC 1962)", "18 USC 1962(c)(d)", 200000, 600000, "3×", "RICO treble on pattern of racketeering"),
        ("Emotional Distress + Outrage (IIED)", "Hyv v City of NY analogy; Michigan IIED", 50000, 200000, "1×", "Extreme and outrageous conduct"),
        ("LAYER 8 BASE DAMAGES", "Multiple", 338000, 1106000, "Various", "Base from prior SKILL.md Layer 8 analysis"),
        ("LAYER 16 ONGOING CONVERSION WAR ADDITIVE", "Multiple", 200000, 320000, "Running", "Ongoing tort streams (Layer 16)"),
    ]
    c.executemany("""INSERT OR IGNORE INTO damages_schedule
        (claim, legal_authority, damages_conservative, damages_aggressive, multiplier, notes)
        VALUES (?,?,?,?,?,?)""", damages)

    # ════════════════════════════════════════════════════════════════════════════
    # POPULATE LEGAL THEORIES (24 counts)
    # ════════════════════════════════════════════════════════════════════════════
    theories = [
        (1, "Wrongful Eviction", "MCL 600.2918", "Entry without court order; disruption of possession; damages", "HOA used dissolved LLC; VOID writ from cartel judge", "VIABLE", "L2"),
        (2, "Conversion of Manufactured Home", "MCL 600.2919a", "Dominion over property; without consent; damages", "Lock drilled; new lock installed; Andrew locked out of titled home", "VIABLE", "L2"),
        (3, "Conversion of Personal Property", "MCL 600.2919a", "Same + treble", "Belongings thrown in yard; destroyed; 'FOR FREE' sign", "VIABLE", "L2"),
        (4, "Conversion of 7 Home Titles", "MCL 600.2919a", "Same + treble", "7 manufactured home titles seized day of eviction", "VIABLE", "L2"),
        (5, "Slander of Title", "MCL 565.108", "False statement; published to 3rd party; disparages title; special damages", "VanDam Facebook Feb 18 2026: 'abandoned'; 3 blocked sales", "VIABLE", "L13"),
        (6, "Tortious Interference with Business Relations", "Prysak v R.L. Polk Co.", "Business relationship; defendants' knowledge; intentional interference; causation; damages", "3 prospective sales blocked by management statements", "VIABLE", "L13"),
        (7, "Fraud – Misrepresentation of Ownership", "MCL 600.2913", "False statement of material fact; knowledge of falsity; intent; reliance; damages", "HOA claimed ownership in court while privately admitting ignorance", "VIABLE", "L2"),
        (8, "Fraud on the Court – Jeremy Brown", "MRPC 3.3; 8.4(c); MCR 9.104", "Attorney inserted unordered res judicata language; knowing misrepresentation to court", "Hearing transcript vs. proposed order: irreconcilable", "VIABLE", "L14/15"),
        (9, "False Police Report", "MCL 750.411a; malicious prosecution", "Filed false report; claiming Andrew broke defendants' locks; exculpated by security cameras", "NSPD records; security camera footage (Andrew never returned)", "VIABLE", "L17"),
        (10, "Trespass", "Common law; MCL 600.2918", "Unauthorized entry to curtilage and dwelling", "Lock drilled; Deputy Schmidt present; HOA authorized per Browley", "VIABLE", "L17"),
        (11, "Constructive Eviction – Sewage", "MCL 125.2319; MCL 554.139", "Habitability breach; sewage discharge; EGLE confirmed", "EGLE VN-017235; sewage on ground; LARA complaints", "VIABLE", "L5"),
        (12, "LLC Ultra Vires – Dissolved Entity", "MCL 450.4802", "All acts of dissolved entity are VOID ab initio", "Shady Oaks dissolved NJ 2022; LARA license still active", "VIABLE", "L0"),
        (13, "Fraudulent Concealment of Entity Change", "MCL 450.4802; MCL 125.2303", "HOA took over without disclosing change to tenants; Dec 2024", "Ledger changes; new management; no disclosure to Andrew", "VIABLE", "L17"),
        (14, "Civil Conspiracy", "MCL 600.2907; Dennis v. Sparks", "Agreement; unlawful act; overt act; damages", "HOA + cartel judges: eviction + custody closed loop", "VIABLE", "L11"),
        (15, "42 USC 1983 – Deprivation of Property", "42 USC 1983; 14th Amendment", "State action; under color of law; deprivation; no due process", "Ladas-Hoopes issued writ to dissolved LLC; Hoopes dismissed without recusal", "VIABLE", "L14"),
        (16, "42 USC 1985(3) – Conspiracy to Deprive Rights", "42 USC 1985(3)", "Conspiracy; between 2+ persons; deprive of equal rights; injury", "Private (HOA) + state (judges) actors: housing + custody coordinated deprivation", "VIABLE", "L14"),
        (17, "RICO – Pattern of Racketeering", "18 USC 1962(c)(d)", "Enterprise; pattern; predicate acts (wire fraud, mail fraud, extortion)", "6-8 LLCs; wire fraud (Facebook msg); coercion emails; title fraud", "VIABLE", "L2"),
        (18, "Fair Housing Act Violation", "42 USC 3604", "Discriminatory housing practices; interference with housing rights", "Retaliatory eviction; habitability; targeted removal", "VIABLE", "L2"),
        (19, "MCL 600.2918 – Tortious Forcible Entry", "MCL 600.2918", "Forcible entry; without consent; with force", "Drill used on lock; not peaceful entry", "VIABLE", "L17"),
        (20, "Intentional Infliction of Emotional Distress", "Michigan IIED standard", "Extreme and outrageous conduct; intent; severe distress", "Destroyed child's belongings in front of father + child; 'FOR FREE' sign", "VIABLE", "L17"),
        (21, "Quiet Title", "MCR 3.411; MCL 600.521", "Clear adverse claim; plaintiff holds title; defendants cloud title", "VIN 1646732 title in Andrew's name; defendants possess property", "VIABLE", "L16"),
        (22, "Declaratory Judgment", "MCL 600.521; MCR 2.605", "Actual controversy; plaintiff has interest; judgment appropriate", "Title status; VOID dissolution; veil-pierce declaration", "VIABLE", "L2"),
        (23, "MCR 2.612 Motion to Vacate Order", "MCR 2.612(C)(1)(c)(b)(f)", "Fraud on court (Brown); newly discovered evidence (Hoopes conflict); extraordinary circumstances", "Three independent grounds; see Layer 15", "VIABLE", "L15"),
        (24, "ARDC / JTC Complaints", "MCR 9.104; Canons 1,2A,3B,3C", "Professional misconduct (Brown); judicial misconduct (Hoopes + Ladas-Hoopes)", "Pattern of conduct; combined JTC filing for all three cartel judges", "VIABLE", "L14"),
    ]
    c.executemany("""INSERT OR IGNORE INTO legal_theories
        (count_number, theory_name, authority, elements, evidence_summary, status, layer_ref)
        VALUES (?,?,?,?,?,?,?)""", theories)

    # ════════════════════════════════════════════════════════════════════════════
    # POPULATE WITNESSES
    # ════════════════════════════════════════════════════════════════════════════
    witnesses = [
        ("Nicole Browley", "Adverse – Primary Executor",
         "Homes of America", None,
         "Stated to Deputy Schmidt that HOA authorized entry. Borrowed drill. Primary witness to eviction execution.",
         10),
        ("Deputy Douglas Schmidt", "Neutral/Government – Key Eyewitness",
         "Muskegon County Sheriff", None,
         "Present July 17 2025. Heard Browley admit HOA authorized entry. Forced Andrew to watch destruction. NSPD report.",
         10),
        ("Carmyn Hanna", "Adverse Witness / Victim",
         "Prospective Buyer", None,
         "Received VanDam's Facebook Messenger statement Feb 18 2026. Primary witness to slander of title.",
         10),
        ("Cassandra VanDam", "Adverse – Facebook Confession",
         "Shady Oaks / HOA", None,
         "Sent 'abandoned' Facebook message. Full 17-question cross-exam prepared (Layer 1.3). Cross-exam on Feb 18 2026 message in Layer 13.",
         10),
        ("Neighbor (Lent Drill)", "Neutral – Tool Provider",
         "1977 Whitehall Rd neighborhood", None,
         "Lent drill to Browley for lock drilling. Corroborates forcible entry method.",
         8),
        ("Amanda StAmour", "Government – EGLE Investigator",
         "EGLE Water Resources Division", "STAMOURA@michigan.gov",
         "Investigated sewage discharge VN-017235. April 2025 email to LARA confirms active EGLE case.",
         8),
        ("Bryon Fields", "Adverse – HOA Principal",
         "Homes of America LLC", "mhp@ourhomesofamerica.com",
         "LARA contact for Shady Oaks. 77 Engle St, Englewood NJ. Principal of HOA operations.",
         9),
        ("Jeremy Brown P77427", "Adverse – Defense Attorney",
         "Shady Oaks defendants", None,
         "Inserted res judicata language; accused Andrew of forgery; cross-exam targets: comparison of oral ruling vs. proposed order language.",
         10),
        ("Kim Davis", "Adverse – Prior Manager",
         "Shady Oaks Park", None,
         "Operations manager before Browley/VanDam era. Management continuity.",
         7),
    ]
    c.executemany("""INSERT OR IGNORE INTO witnesses
        (name, role, affiliation, contact, testimony_value, subpoena_priority)
        VALUES (?,?,?,?,?,?)""", witnesses)

    conn.commit()

    # ── VERIFY ────────────────────────────────────────────────────────────────
    stats = conn.execute("""SELECT
        (SELECT COUNT(*) FROM entities) as entities,
        (SELECT COUNT(*) FROM llc_chain) as llcs,
        (SELECT COUNT(*) FROM timeline_events) as timeline,
        (SELECT COUNT(*) FROM evidence_registry) as evidence,
        (SELECT COUNT(*) FROM lara_intelligence) as lara,
        (SELECT COUNT(*) FROM post_eviction_torts) as torts,
        (SELECT COUNT(*) FROM judicial_cartel) as judges,
        (SELECT COUNT(*) FROM contradictions) as contradictions,
        (SELECT COUNT(*) FROM false_allegations) as false_alleg,
        (SELECT COUNT(*) FROM damages_schedule) as damages,
        (SELECT COUNT(*) FROM legal_theories) as theories,
        (SELECT COUNT(*) FROM witnesses) as witnesses
    """).fetchone()

    labels = ["entities","llcs","timeline","evidence","lara","torts",
              "judges","contradictions","false_allegations","damages","theories","witnesses"]
    print(f"\n✅ shadyoaks_brain.db CREATED: {DB_PATH}")
    print("=" * 60)
    for label, val in zip(labels, stats):
        print(f"  {label:<22} {val:>5} rows")
    print("=" * 60)
    total = sum(stats)
    print(f"  {'TOTAL ROWS':<22} {total:>5}")

    conn.close()
    print("\n✅ DONE — shadyoaks_brain.db ready for Lane B operations.")

if __name__ == "__main__":
    create_db()
