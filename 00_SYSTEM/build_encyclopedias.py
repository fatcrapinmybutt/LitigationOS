"""
PROJECT SINGULARITY OMEGA — Encyclopedia & Adversary Brain Builder
Creates dedicated intelligence tables and populates from existing evidence.
"""
import sqlite3
import os
import sys
from datetime import datetime

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.row_factory = sqlite3.Row
    return conn

def create_adversary_tables(conn):
    """Create dedicated adversary intelligence tables for each person."""
    adversaries = [
        ("adversary_watson", "Emily A. Watson", "Defendant — custody, PPO, false allegations"),
        ("adversary_mcneill", "Hon. Jenny L. McNeill", "Judge — ex parte, bias, benchbook violations"),
        ("adversary_berry_ronald", "Ronald Berry", "Non-attorney — shadow legal ops, McNeill connection"),
        ("adversary_albert_watson", "Albert Watson", "Emily's father — premeditation, intimidation"),
        ("adversary_lori_watson", "Lori Watson", "Emily's mother — enabler, witness"),
        ("adversary_rusco", "Pamela Rusco", "FOC — systemic bias, same address as judge spouse"),
        ("adversary_hoopes", "Hon. Kenneth Hoopes", "Chief Judge — former law partner of McNeill"),
        ("adversary_ladas_hoopes", "Hon. Maria Ladas-Hoopes", "60th District — former partner of McNeill"),
        ("adversary_barnes", "Jennifer Barnes P55406", "Former opposing counsel — withdrew Mar 2026"),
    ]

    for table_name, person_name, description in adversaries:
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                fact_text TEXT NOT NULL,
                source_file TEXT,
                source_page TEXT,
                date_observed TEXT,
                severity INTEGER DEFAULT 5 CHECK(severity BETWEEN 1 AND 10),
                lane TEXT,
                cross_exam_question TEXT,
                impeachment_value INTEGER DEFAULT 0 CHECK(impeachment_value BETWEEN 0 AND 10),
                verified INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                source_table TEXT,
                source_row_id INTEGER,
                UNIQUE(fact_text, source_file)
            )
        """)
        conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{table_name}_category ON {table_name}(category)
        """)
        conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{table_name}_severity ON {table_name}(severity DESC)
        """)
        conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{table_name}_lane ON {table_name}(lane)
        """)
        print(f"  ✅ {table_name} ({person_name}) — {description}")

    # Master adversary registry
    conn.execute("""
        CREATE TABLE IF NOT EXISTS adversary_registry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT UNIQUE NOT NULL,
            person_name TEXT NOT NULL,
            description TEXT,
            role TEXT,
            threat_level INTEGER DEFAULT 5,
            total_facts INTEGER DEFAULT 0,
            last_updated TEXT DEFAULT (datetime('now'))
        )
    """)
    for table_name, person_name, description in adversaries:
        conn.execute("""
            INSERT OR REPLACE INTO adversary_registry (table_name, person_name, description, role)
            VALUES (?, ?, ?, ?)
        """, (table_name, person_name, description, 
              "defendant" if "Watson" in person_name and "Albert" not in person_name and "Lori" not in person_name
              else "judge" if "Hon." in person_name 
              else "foc" if "Rusco" in person_name
              else "counsel" if "Barnes" in person_name
              else "witness"))
    print(f"  ✅ adversary_registry (master index)")
    conn.commit()
    return [t[0] for t in adversaries]

def create_encyclopedia_tables(conn):
    """Create comprehensive encyclopedia tables for each litigation domain."""

    # Custody Encyclopedia — MCL 722.23 factors
    conn.execute("""
        CREATE TABLE IF NOT EXISTS encyclopedia_custody (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            factor TEXT NOT NULL,
            factor_letter TEXT CHECK(factor_letter IN ('a','b','c','d','e','f','g','h','i','j','k','l')),
            factor_text TEXT,
            andrew_evidence TEXT,
            emily_claims TEXT,
            trial_finding TEXT,
            current_status TEXT,
            foc_finding TEXT,
            key_authority TEXT,
            key_case_law TEXT,
            evidence_quote_ids TEXT,
            strength_score INTEGER DEFAULT 5,
            lane TEXT DEFAULT 'A',
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Parenting Time Encyclopedia
    conn.execute("""
        CREATE TABLE IF NOT EXISTS encyclopedia_parenting_time (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            event_date TEXT,
            scheduled_time TEXT,
            actual_outcome TEXT,
            denial_reason TEXT,
            denial_by TEXT,
            appclose_ref TEXT,
            court_order_ref TEXT,
            contempt_basis TEXT,
            days_denied INTEGER,
            evidence_refs TEXT,
            lane TEXT DEFAULT 'A',
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Child Support Encyclopedia
    conn.execute("""
        CREATE TABLE IF NOT EXISTS encyclopedia_child_support (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            detail TEXT,
            amount REAL,
            date_effective TEXT,
            foc_involvement TEXT,
            authority TEXT,
            order_ref TEXT,
            status TEXT,
            lane TEXT DEFAULT 'A',
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Judicial Bias Encyclopedia
    conn.execute("""
        CREATE TABLE IF NOT EXISTS encyclopedia_judicial_bias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            judge TEXT NOT NULL,
            bias_type TEXT NOT NULL,
            incident_date TEXT,
            incident_description TEXT,
            canon_violated TEXT,
            mcr_violated TEXT,
            benchbook_section TEXT,
            benchbook_deviation TEXT,
            witness TEXT,
            evidence_refs TEXT,
            severity INTEGER DEFAULT 5,
            jtc_exhibit TEXT,
            lane TEXT DEFAULT 'E',
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Torts & Civil Claims Encyclopedia
    conn.execute("""
        CREATE TABLE IF NOT EXISTS encyclopedia_torts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tort_name TEXT NOT NULL,
            tort_type TEXT,
            elements TEXT,
            defendant TEXT,
            facts_supporting TEXT,
            facts_against TEXT,
            primary_authority TEXT,
            michigan_statute TEXT,
            federal_statute TEXT,
            key_cases TEXT,
            damages_model TEXT,
            statute_of_limitations TEXT,
            sol_deadline TEXT,
            filing_lane TEXT,
            strength_score INTEGER DEFAULT 5,
            status TEXT DEFAULT 'viable',
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # PPO Encyclopedia
    conn.execute("""
        CREATE TABLE IF NOT EXISTS encyclopedia_ppo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            event_date TEXT,
            description TEXT,
            filed_by TEXT,
            against TEXT,
            case_number TEXT DEFAULT '2023-5907-PP',
            weaponization_indicator INTEGER DEFAULT 0,
            recantation_ref TEXT,
            contempt_action TEXT,
            jail_days INTEGER DEFAULT 0,
            authority TEXT,
            evidence_refs TEXT,
            lane TEXT DEFAULT 'D',
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # False Allegations Encyclopedia
    conn.execute("""
        CREATE TABLE IF NOT EXISTS encyclopedia_false_allegations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            allegation TEXT NOT NULL,
            alleged_by TEXT DEFAULT 'Emily A. Watson',
            alleged_date TEXT,
            allegation_detail TEXT,
            debunked_by TEXT,
            debunked_evidence TEXT,
            police_report_ref TEXT,
            investigation_result TEXT,
            projection_indicator TEXT,
            evidence_count INTEGER DEFAULT 0,
            severity INTEGER DEFAULT 5,
            lane TEXT,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Separation Crisis Encyclopedia
    conn.execute("""
        CREATE TABLE IF NOT EXISTS encyclopedia_separation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            event_date TEXT,
            description TEXT,
            harm_to_child TEXT,
            harm_to_father TEXT,
            constitutional_violation TEXT,
            authority TEXT,
            evidence_refs TEXT,
            days_since_last_contact INTEGER,
            lane TEXT DEFAULT 'A',
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Cartel Intelligence Encyclopedia
    conn.execute("""
        CREATE TABLE IF NOT EXISTS encyclopedia_cartel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            connection_type TEXT NOT NULL,
            person_a TEXT,
            person_b TEXT,
            relationship TEXT,
            evidence TEXT,
            significance TEXT,
            address_overlap TEXT,
            law_firm TEXT,
            date_discovered TEXT,
            severity INTEGER DEFAULT 5,
            lane TEXT DEFAULT 'E',
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Master Encyclopedia Index
    conn.execute("""
        CREATE TABLE IF NOT EXISTS encyclopedia_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT UNIQUE NOT NULL,
            domain TEXT NOT NULL,
            description TEXT,
            row_count INTEGER DEFAULT 0,
            last_updated TEXT DEFAULT (datetime('now'))
        )
    """)

    encyclopedias = [
        ("encyclopedia_custody", "custody", "MCL 722.23 best interest factors analysis"),
        ("encyclopedia_parenting_time", "parenting_time", "Parenting time denial/interference log"),
        ("encyclopedia_child_support", "child_support", "Child support calculations and enforcement"),
        ("encyclopedia_judicial_bias", "judicial_bias", "Judicial misconduct patterns and JTC evidence"),
        ("encyclopedia_torts", "torts", "Civil tort claims with elements and evidence"),
        ("encyclopedia_ppo", "ppo", "PPO history, weaponization, termination grounds"),
        ("encyclopedia_false_allegations", "false_allegations", "Debunked false allegations pattern"),
        ("encyclopedia_separation", "separation", "Parent-child separation crisis timeline"),
        ("encyclopedia_cartel", "cartel", "Judicial cartel connections and intelligence"),
    ]
    for table_name, domain, description in encyclopedias:
        conn.execute("""
            INSERT OR REPLACE INTO encyclopedia_index (table_name, domain, description)
            VALUES (?, ?, ?)
        """, (table_name, domain, description))
        print(f"  ✅ {table_name} ({domain})")

    conn.commit()
    return [t[0] for t in encyclopedias]

def populate_adversary_brains(conn):
    """Populate adversary brain tables from existing evidence sources."""
    
    # Mapping of search terms to adversary tables
    adversary_search = {
        "adversary_watson": ["Emily", "Watson", "defendant", "mother"],
        "adversary_mcneill": ["McNeill", "judge", "court"],
        "adversary_berry_ronald": ["Ronald Berry", "Ron Berry", "Berry"],
        "adversary_albert_watson": ["Albert Watson", "Albert", "father-in-law"],
        "adversary_rusco": ["Rusco", "FOC", "Friend of Court", "friend of the court"],
        "adversary_hoopes": ["Hoopes", "Chief Judge", "chief judge"],
        "adversary_ladas_hoopes": ["Ladas", "Ladas-Hoopes", "60th District"],
        "adversary_barnes": ["Barnes", "P55406", "opposing counsel"],
    }

    total_inserted = 0

    for table_name, search_terms in adversary_search.items():
        table_count = 0

        # 1. From evidence_quotes
        for term in search_terms[:2]:  # Use first 2 terms to avoid over-matching
            try:
                rows = conn.execute("""
                    SELECT rowid, quote_text, source_file, category, lane, page_number
                    FROM evidence_quotes
                    WHERE quote_text LIKE ? AND is_duplicate = 0
                    LIMIT 200
                """, (f"%{term}%",)).fetchall()

                inserts = []
                for r in rows:
                    inserts.append((
                        r["category"] or "evidence",
                        r["quote_text"][:2000],
                        r["source_file"],
                        str(r["page_number"]) if r["page_number"] else None,
                        None,  # date
                        5,  # severity
                        r["lane"],
                        None,  # cross_exam
                        0,  # impeachment
                        0,  # verified
                        "evidence_quotes",
                        r["rowid"]
                    ))
                if inserts:
                    conn.executemany(f"""
                        INSERT OR IGNORE INTO {table_name}
                        (category, fact_text, source_file, source_page, date_observed,
                         severity, lane, cross_exam_question, impeachment_value, verified,
                         source_table, source_row_id)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                    """, inserts)
                    table_count += len(inserts)
            except Exception as e:
                print(f"    ⚠️ evidence_quotes error for {table_name}/{term}: {e}")

        # 2. From impeachment_matrix
        for term in search_terms[:2]:
            try:
                rows = conn.execute("""
                    SELECT rowid, category, evidence_summary, source_file, 
                           impeachment_value, cross_exam_question, filing_relevance, event_date
                    FROM impeachment_matrix
                    WHERE evidence_summary LIKE ? OR cross_exam_question LIKE ?
                    LIMIT 100
                """, (f"%{term}%", f"%{term}%")).fetchall()

                inserts = []
                for r in rows:
                    inserts.append((
                        r["category"] or "impeachment",
                        r["evidence_summary"][:2000],
                        r["source_file"],
                        None,
                        r["event_date"],
                        min(10, (r["impeachment_value"] or 5)),
                        r["filing_relevance"],
                        r["cross_exam_question"],
                        r["impeachment_value"] or 5,
                        1,
                        "impeachment_matrix",
                        r["rowid"]
                    ))
                if inserts:
                    conn.executemany(f"""
                        INSERT OR IGNORE INTO {table_name}
                        (category, fact_text, source_file, source_page, date_observed,
                         severity, lane, cross_exam_question, impeachment_value, verified,
                         source_table, source_row_id)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                    """, inserts)
                    table_count += len(inserts)
            except Exception as e:
                print(f"    ⚠️ impeachment_matrix error for {table_name}/{term}: {e}")

        # 3. From contradiction_map
        for term in search_terms[:2]:
            try:
                rows = conn.execute("""
                    SELECT rowid, contradiction_text, source_a, source_b, severity, lane
                    FROM contradiction_map
                    WHERE contradiction_text LIKE ? OR source_a LIKE ? OR source_b LIKE ?
                    LIMIT 100
                """, (f"%{term}%", f"%{term}%", f"%{term}%")).fetchall()

                inserts = []
                for r in rows:
                    sev_map = {"critical": 10, "high": 8, "medium": 6, "low": 3}
                    sev = sev_map.get(str(r["severity"]).lower(), 5)
                    inserts.append((
                        "contradiction",
                        r["contradiction_text"][:2000],
                        f"{r['source_a']} vs {r['source_b']}",
                        None, None, sev,
                        r["lane"],
                        None, sev, 1,
                        "contradiction_map",
                        r["rowid"]
                    ))
                if inserts:
                    conn.executemany(f"""
                        INSERT OR IGNORE INTO {table_name}
                        (category, fact_text, source_file, source_page, date_observed,
                         severity, lane, cross_exam_question, impeachment_value, verified,
                         source_table, source_row_id)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                    """, inserts)
                    table_count += len(inserts)
            except Exception as e:
                print(f"    ⚠️ contradiction_map error for {table_name}/{term}: {e}")

        # 4. From judicial_violations (for judicial adversaries)
        if table_name in ("adversary_mcneill", "adversary_hoopes", "adversary_ladas_hoopes"):
            try:
                judge_term = search_terms[0]
                rows = conn.execute("""
                    SELECT rowid, violation_type, description, date, severity, 
                           mcr_violated, canon_violated, evidence_ref
                    FROM judicial_violations
                    WHERE description LIKE ? OR violation_type LIKE ?
                    LIMIT 500
                """, (f"%{judge_term}%", f"%{judge_term}%")).fetchall()

                inserts = []
                for r in rows:
                    inserts.append((
                        r["violation_type"] or "judicial_violation",
                        r["description"][:2000],
                        r["evidence_ref"],
                        None,
                        r["date"],
                        r["severity"] if r["severity"] else 7,
                        "E",
                        None,
                        r["severity"] if r["severity"] else 7,
                        1,
                        "judicial_violations",
                        r["rowid"]
                    ))
                if inserts:
                    conn.executemany(f"""
                        INSERT OR IGNORE INTO {table_name}
                        (category, fact_text, source_file, source_page, date_observed,
                         severity, lane, cross_exam_question, impeachment_value, verified,
                         source_table, source_row_id)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                    """, inserts)
                    table_count += len(inserts)
            except Exception as e:
                print(f"    ⚠️ judicial_violations error for {table_name}: {e}")

        # 5. From berry_mcneill_intelligence
        if table_name in ("adversary_mcneill", "adversary_berry_ronald", "adversary_hoopes"):
            try:
                rows = conn.execute("""
                    SELECT rowid, * FROM berry_mcneill_intelligence LIMIT 200
                """).fetchall()
                cols = [d[0] for d in conn.execute("PRAGMA table_info(berry_mcneill_intelligence)").fetchall()]
                col_names = [c[1] for c in conn.execute("PRAGMA table_info(berry_mcneill_intelligence)").fetchall()]
                
                inserts = []
                for r in rows:
                    text_parts = []
                    for cn in col_names:
                        val = r[cn] if cn in r.keys() else None
                        if val and isinstance(val, str) and len(val) > 10:
                            text_parts.append(f"{cn}: {val}")
                    fact = "; ".join(text_parts[:3])[:2000]
                    if fact:
                        inserts.append((
                            "cartel_intelligence",
                            fact,
                            "berry_mcneill_intelligence",
                            None, None, 8, "E",
                            None, 8, 1,
                            "berry_mcneill_intelligence",
                            r["rowid"]
                        ))
                if inserts:
                    conn.executemany(f"""
                        INSERT OR IGNORE INTO {table_name}
                        (category, fact_text, source_file, source_page, date_observed,
                         severity, lane, cross_exam_question, impeachment_value, verified,
                         source_table, source_row_id)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                    """, inserts)
                    table_count += len(inserts)
            except Exception as e:
                print(f"    ⚠️ berry_mcneill_intelligence error for {table_name}: {e}")

        total_inserted += table_count
        # Update registry
        actual = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        conn.execute("UPDATE adversary_registry SET total_facts=?, last_updated=datetime('now') WHERE table_name=?",
                     (actual, table_name))
        print(f"  📊 {table_name}: {actual} facts ({table_count} new)")

    conn.commit()
    return total_inserted

def populate_encyclopedias(conn):
    """Populate encyclopedia tables from existing data."""
    total = 0

    # 1. Custody factors — seed from MCL 722.23
    factors = [
        ("a", "Love, affection, and other emotional ties", "The love, affection, and other emotional ties existing between the parties involved and the child"),
        ("b", "Capacity to provide love and guidance", "The capacity and disposition of the parties involved to give the child love, affection, and guidance and to continue the education and raising of the child in his or her religion or creed, if any"),
        ("c", "Capacity to provide food, clothing, medical care", "The capacity and disposition of the parties involved to provide the child with food, clothing, medical care or other remedial care"),
        ("d", "Length of time in stable environment", "The length of time the child has lived in a stable, satisfactory environment, and the desirability of maintaining continuity"),
        ("e", "Permanence of family unit", "The permanence, as a family unit, of the existing or proposed custodial home or homes"),
        ("f", "Moral fitness", "The moral fitness of the parties involved"),
        ("g", "Mental and physical health", "The mental and physical health of the parties involved"),
        ("h", "Home, school, community record", "The home, school, and community record of the child"),
        ("i", "Reasonable preference of child", "The reasonable preference of the child, if the court considers the child to be of sufficient age to express preference"),
        ("j", "Willingness to facilitate relationship", "The willingness and ability of each of the parties to facilitate and encourage a close and continuing parent-child relationship between the child and the other parent or the child and the parents"),
        ("k", "Domestic violence", "Domestic violence, regardless of whether the violence was directed against or witnessed by the child"),
        ("l", "Any other relevant factor", "Any other factor considered by the court to be relevant to a particular child custody dispute"),
    ]
    inserts = []
    for letter, name, text in factors:
        inserts.append((name, letter, text, None, None, None, None, None, 
                        "MCL 722.23", None, None, 5, "A", None))
    conn.executemany("""
        INSERT OR IGNORE INTO encyclopedia_custody 
        (factor, factor_letter, factor_text, andrew_evidence, emily_claims, trial_finding,
         current_status, foc_finding, key_authority, key_case_law, evidence_quote_ids,
         strength_score, lane, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, inserts)
    total += len(inserts)
    print(f"  ✅ encyclopedia_custody: {len(inserts)} factors seeded")

    # 2. False allegations — seed known debunked allegations
    allegations = [
        ("Arsenic/poisoning", "2023", "Alleged Andrew poisoned child", "No toxicology results; ER visit cleared", 37),
        ("Physical assault", "2023", "Alleged Andrew pushed/hit Emily", "No police report, no evidence, no injuries", 0),
        ("Sexual assault", "2023", "Alleged Andrew committed sexual assault", "No investigation, no evidence, debunked", 15),
        ("Cocaine straw", "2023", "Alleged cocaine paraphernalia found", "Item never tested, no chain of custody", 5),
        ("Meth use (projection)", "2023-2025", "Alleged Andrew uses methamphetamine", "Officer Randall report: EMILY admitted meth use. Projection pattern", 160),
        ("Child abuse/danger", "2023-2025", "Alleged Andrew is danger to child", "HealthWest eval: Psychosis=0, Substance=0, Danger=0, LOCUS=12", 49),
        ("Mental instability", "2023-2025", "Alleged Andrew is mentally unstable", "HealthWest LOCUS=12/Level One — lowest care level. Judge EXCLUDED this eval", 91),
        ("Suicidal threats", "2023", "Alleged Andrew made suicidal statements", "Police welfare checks ALL cleared Andrew", 0),
        ("Stalking", "2023-2024", "Alleged Andrew stalked Emily", "PPO filed 2 days after recantation Oct 15 2023", 0),
    ]
    inserts = []
    for alleg, date, detail, debunked, count in allegations:
        inserts.append((alleg, "Emily A. Watson", date, detail, debunked, None, None,
                        count, 8, None, None))
    conn.executemany("""
        INSERT OR IGNORE INTO encyclopedia_false_allegations
        (allegation, alleged_by, alleged_date, allegation_detail, debunked_by,
         debunked_evidence, police_report_ref, evidence_count, severity, lane, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, inserts)
    total += len(inserts)
    print(f"  ✅ encyclopedia_false_allegations: {len(inserts)} allegations seeded")

    # 3. Tort claims — seed viable claims
    torts = [
        ("IIED", "intentional_tort", "Intentional Infliction of Emotional Distress",
         "1) Extreme and outrageous conduct | 2) Intent or recklessness | 3) Severe emotional distress | 4) Causation",
         "Emily A. Watson", "MCL 600.2913", "Roberts v Auto-Owners, 422 Mich 594 (1985)", "A,D"),
        ("Abuse of Process", "intentional_tort", "Using legal process for improper purpose",
         "1) Ulterior purpose | 2) Willful act in use of process not proper in regular conduct",
         "Emily A. Watson; Hon. Jenny L. McNeill", "Common law", "Friedman v Dozorc, 412 Mich 1 (1981)", "A,D,E"),
        ("Malicious Prosecution", "intentional_tort", "Initiating criminal proceedings without probable cause",
         "1) Prior proceeding terminated favorably | 2) Absence of probable cause | 3) Malice | 4) Special injury",
         "Emily A. Watson", "MCL 600.2907", "Matthews v Blue Cross, 456 Mich 365 (1998)", "D,CRIMINAL"),
        ("Civil Conspiracy", "intentional_tort", "Agreement to accomplish unlawful purpose",
         "1) Concerted action | 2) By combination of 2+ persons | 3) To accomplish criminal/unlawful purpose | 4) Overt act | 5) Resulting injury",
         "Emily A. Watson; Albert Watson; Ronald Berry; Hon. Jenny L. McNeill", "Common law", "Advocacy Org v Auto Club, 257 Mich App 365 (2003)", "C,E"),
        ("Fraud on the Court", "equitable", "Deceiving the court to obtain favorable ruling",
         "1) Material misrepresentation | 2) Made to court | 3) Knowingly false | 4) Court relied on it | 5) Adverse impact",
         "Emily A. Watson", "MCR 2.612(C)(1)(c)", "In re Contempt of Henry, 282 Mich App 656 (2009)", "A,F"),
        ("42 USC §1983 - Due Process", "federal_civil_rights", "Deprivation of constitutional rights under color of law",
         "1) Action under color of state law | 2) Deprivation of federal right | 3) Causation | 4) Damages",
         "Hon. Jenny L. McNeill", "42 USC §1983; 28 USC §1343", "Monell v Dept of Social Services, 436 US 658 (1978)", "C"),
        ("42 USC §1983 - Parental Rights", "federal_civil_rights", "Interference with fundamental right to parent",
         "1) State action | 2) Fundamental right to parent-child relationship | 3) Without due process | 4) Damages",
         "Hon. Jenny L. McNeill", "42 USC §1983; US Const Amend XIV", "Troxel v Granville, 530 US 57 (2000)", "C"),
    ]
    inserts = []
    for name, ttype, elements_desc, elements, defendant, statute, cases, lanes in torts:
        inserts.append((name, ttype, elements, defendant, None, None, statute, None, None,
                        cases, None, None, None, lanes, 7, "viable", None))
    conn.executemany("""
        INSERT OR IGNORE INTO encyclopedia_torts
        (tort_name, tort_type, elements, defendant, facts_supporting, facts_against,
         primary_authority, michigan_statute, federal_statute, key_cases, damages_model,
         statute_of_limitations, sol_deadline, filing_lane, strength_score, status, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, inserts)
    total += len(inserts)
    print(f"  ✅ encyclopedia_torts: {len(inserts)} claims seeded")

    # 4. Cartel connections
    cartel = [
        ("law_firm_partnership", "Hon. Jenny L. McNeill", "Hon. Kenneth Hoopes",
         "Former law partners at Ladas, Hoopes & McNeill, 435 Whitehall Rd",
         "Firm records, bar association records", "Judge deciding case was partners with chief judge who would hear recusal", None, "Ladas, Hoopes & McNeill"),
        ("law_firm_partnership", "Hon. Jenny L. McNeill", "Hon. Maria Ladas-Hoopes",
         "Former law partners at Ladas, Hoopes & McNeill",
         "Firm records", "Three former partners now control 14th Circuit AND 60th District", None, "Ladas, Hoopes & McNeill"),
        ("spousal_connection", "Hon. Jenny L. McNeill", "Cavan Berry",
         "Married — Cavan Berry is atty magistrate at 60th District, office at 990 Terrace St (same as FOC)",
         "Marriage records, court personnel records", "Judge's spouse works at same address as FOC office", "990 Terrace St, Muskegon", None),
        ("family_connection", "Ronald Berry", "Cavan Berry",
         "Related — Ronald Berry connected to Cavan Berry (judge's spouse)",
         "Family records, public records", "Emily's boyfriend connected to presiding judge's family", None, None),
        ("address_overlap", "Pamela Rusco (FOC)", "Cavan Berry",
         "Both at 990 Terrace St, Muskegon MI 49442",
         "FOC records, court records", "FOC officer works from same address as judge's spouse", "990 Terrace St, Muskegon", None),
        ("cohabitation", "Emily A. Watson", "Ronald Berry",
         "Living together at 2160 Garland Dr, Norton Shores",
         "Address records, court filings", "Defendant cohabitating with person connected to presiding judge", "2160 Garland Dr", None),
    ]
    inserts = []
    for ctype, pa, pb, rel, ev, sig, addr, firm in cartel:
        inserts.append((ctype, pa, pb, rel, ev, sig, addr, firm, None, 9, "E", None))
    conn.executemany("""
        INSERT OR IGNORE INTO encyclopedia_cartel
        (connection_type, person_a, person_b, relationship, evidence, significance,
         address_overlap, law_firm, date_discovered, severity, lane, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, inserts)
    total += len(inserts)
    print(f"  ✅ encyclopedia_cartel: {len(inserts)} connections seeded")

    # 5. PPO events
    ppo_events = [
        ("recantation", "2023-10-13", "Emily recants: 'nothing was physical' — NSPD-2023-08121", "Emily A. Watson", "Andrew Pigors", 0, "NSPD-2023-08121"),
        ("filing", "2023-10-15", "Emily files PPO (2023-5907-PP) — 2 DAYS after recanting", "Emily A. Watson", "Andrew Pigors", 1, None),
        ("ex_parte_grant", "2023-12-03", "PPO granted same day as filed — ex parte, no hearing", "Hon. Jenny L. McNeill", "Andrew Pigors", 1, None),
        ("contempt_sc5", "2024-11-15", "Show Cause #5 — 14 days jail. Andrew muted 3x during hearing", "Hon. Jenny L. McNeill", "Andrew Pigors", 1, None),
        ("contempt_sc67", "2025-11-26", "Show Cause #6+7 — 45 days jail for birthday messages via AppClose", "Hon. Jenny L. McNeill", "Andrew Pigors", 1, None),
    ]
    inserts = []
    for etype, edate, desc, filed_by, against, weap, ref in ppo_events:
        inserts.append((etype, edate, desc, filed_by, against, "2023-5907-PP", weap, ref, None, 0 if etype == "recantation" else (14 if "14 days" in desc else (45 if "45 days" in desc else 0)), "MCL 600.2950", None, "D", None))
    conn.executemany("""
        INSERT OR IGNORE INTO encyclopedia_ppo
        (event_type, event_date, description, filed_by, against, case_number,
         weaponization_indicator, recantation_ref, contempt_action, jail_days,
         authority, evidence_refs, lane, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, inserts)
    total += len(inserts)
    print(f"  ✅ encyclopedia_ppo: {len(inserts)} events seeded")

    conn.commit()
    return total

def update_index_counts(conn):
    """Update row counts in encyclopedia_index."""
    tables = conn.execute("SELECT table_name FROM encyclopedia_index").fetchall()
    for t in tables:
        try:
            count = conn.execute(f"SELECT COUNT(*) FROM {t['table_name']}").fetchone()[0]
            conn.execute("UPDATE encyclopedia_index SET row_count=?, last_updated=datetime('now') WHERE table_name=?",
                        (count, t['table_name']))
        except:
            pass
    conn.commit()

def main():
    print("=" * 70)
    print("🏛️  PROJECT SINGULARITY OMEGA — Encyclopedia & Adversary Brain Builder")
    print("=" * 70)
    
    conn = get_conn()

    print("\n📋 Phase 1: Creating Adversary Brain Tables...")
    adversary_tables = create_adversary_tables(conn)

    print(f"\n📚 Phase 2: Creating Encyclopedia Tables...")
    encyclopedia_tables = create_encyclopedia_tables(conn)

    print(f"\n🧠 Phase 3: Populating Adversary Brains from Evidence...")
    adversary_count = populate_adversary_brains(conn)

    print(f"\n📖 Phase 4: Seeding Encyclopedias with Core Knowledge...")
    encyclopedia_count = populate_encyclopedias(conn)

    print(f"\n📊 Phase 5: Updating Index Counts...")
    update_index_counts(conn)

    # Final stats
    print("\n" + "=" * 70)
    print("📊 FINAL STATS")
    print("=" * 70)
    
    print("\n  ADVERSARY BRAINS:")
    for row in conn.execute("SELECT table_name, person_name, total_facts FROM adversary_registry ORDER BY total_facts DESC"):
        print(f"    {row['person_name']:35s} → {row['total_facts']:,} facts")

    print("\n  ENCYCLOPEDIAS:")
    for row in conn.execute("SELECT table_name, domain, row_count FROM encyclopedia_index ORDER BY row_count DESC"):
        print(f"    {row['domain']:25s} → {row['row_count']:,} entries")

    total_adversary = conn.execute("SELECT SUM(total_facts) FROM adversary_registry").fetchone()[0] or 0
    total_encyclopedia = conn.execute("SELECT SUM(row_count) FROM encyclopedia_index").fetchone()[0] or 0
    
    print(f"\n  TOTALS: {total_adversary:,} adversary facts + {total_encyclopedia:,} encyclopedia entries")
    print(f"  = {total_adversary + total_encyclopedia:,} total intelligence items")
    
    conn.close()
    print("\n✅ ALL DONE — encyclopedias and adversary brains built!")

if __name__ == "__main__":
    main()
