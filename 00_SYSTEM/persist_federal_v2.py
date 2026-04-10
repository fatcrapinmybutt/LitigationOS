"""Persist Federal Citation PDF v2 intelligence to litigation_context.db.
New SCOTUS cases, doctrinal workarounds, RICO elements, criminal referrals, damages framework.
"""
import sqlite3, os, datetime

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"

def get_conn():
    conn = sqlite3.connect(DB, timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    return conn

def persist_scotus_cases(conn):
    """Persist new SCOTUS cases to authority_chains_v2."""
    cases = [
        ("Withrow v. Larkin", "421 US 35 (1975)",
         "Combination of investigative and adjudicative functions in same body creates unconstitutional risk of bias",
         "McNeill combines investigative (reviewing evidence ex parte) and adjudicative (ruling on custody) functions"),
        ("Ward v. Monroeville", "409 US 57 (1972)",
         "Due process violated when judge has direct financial interest in case outcome",
         "McNeill-Berry-FOC nexus creates financial/professional interest in case outcomes via 990 Terrace shared address"),
        ("Sacramento v. Lewis", "523 US 833 (1998)",
         "Substantive due process violation requires conduct that shocks the conscience",
         "59 days jail for birthday messages, 5 ex parte orders in one day after premeditated setup shocks the conscience"),
        ("Memphis Community School Dist v. Stachura", "477 US 299 (1986)",
         "Compensatory damages for constitutional violations based on actual injury, not abstract value of rights",
         "Actual injuries: lost parenting time, lost jobs, lost homes, incarceration, emotional distress"),
        ("Thompson v. Clark", "596 US 36 (2022)",
         "Favorable termination for malicious prosecution requires only that charges terminated without conviction, not affirmative indication of innocence",
         "9 NSPD contacts, ZERO arrests/charges across all contacts = favorable termination for every false report"),
        ("Griffin v. Illinois", "351 US 12 (1956)",
         "Equal protection requires that indigent litigants not be denied access to appellate review solely due to inability to pay",
         "Andrew cannot afford $2K+ transcripts or $375+ filing fees - MCR 7.210(B)(2) settled statements + MC 20 fee waiver"),
        ("Evitts v. Lucey", "469 US 387 (1985)",
         "Due process requires an effective appellate process, not merely a nominal right to appeal",
         "McNeill's filing ban ('Do not file anymore, I will not look at it') denies effective appellate process"),
        ("Parratt v. Taylor", "451 US 527 (1981)",
         "Random unauthorized deprivation by state employee - adequate post-deprivation remedy may satisfy due process",
         "14th Circuit remedy inadequate when all 3 judges are former law partners - MSC/federal venue required"),
        ("Zinermon v. Burch", "494 US 113 (1990)",
         "When deprivation is foreseeable and pre-deprivation hearing practicable, post-deprivation remedy insufficient",
         "Ex parte orders were deliberate choices, not random - pre-deprivation hearing was required and denied"),
    ]
    rows = []
    for name, cite, holding, application in cases:
        rows.append((
            f"42 USC 1983 ({name})", cite, "supports",
            "Federal Civil Rights Citation Index (VERIFIED)", "case_law", "C",
            f"HOLDING: {holding}. APPLICATION TO PIGORS: {application}"
        ))
    conn.executemany("""
        INSERT OR IGNORE INTO authority_chains_v2
        (primary_citation, supporting_citation, relationship, source_document, source_type, lane, paragraph_context)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, rows)
    conn.commit()
    ct = conn.execute("SELECT changes()").fetchone()[0]
    print(f"[1] SCOTUS cases: {ct} rows inserted into authority_chains_v2")
    return ct

def persist_doctrinal_workarounds(conn):
    """Persist doctrinal defense workarounds to evidence_quotes."""
    workarounds = [
        ("Rooker-Feldman Bypass",
         "Frame §1983 claims as FORWARD-LOOKING constitutional violations, not review of state court judgment. "
         "Seek injunctive relief (restore parenting time) and damages (lost time, imprisonment), not reversal of custody order. "
         "Exxon Mobil Corp v. Saudi Basic Industries, 544 US 280 (2005): Rooker-Feldman applies only to state-court losers "
         "complaining of injuries caused BY the judgment, not to independent claims of constitutional violations.",
         "C", "federal_strategy"),
        ("Younger Abstention — All 4 Exceptions Present",
         "EXCEPTION 1: Bad faith prosecution — Emily's false allegations used to trigger ex parte orders (NS2505044 premeditation). "
         "EXCEPTION 2: Patently unconstitutional statute applied — PPO weaponized without Best Interest analysis. "
         "EXCEPTION 3: Inadequate state forum — all 3 circuit judges are former law partners (McNeill/Hoopes/Ladas-Hoopes). "
         "EXCEPTION 4: Extraordinary circumstances — 59 days jail, 300+ days separation, father deemed fit but excluded. "
         "Younger v. Harris, 401 US 37 (1971); Middlesex County Ethics Comm. v. Garden State Bar Assn., 457 US 423 (1982).",
         "C", "federal_strategy"),
        ("Qualified Immunity Defeat Strategy",
         "TWO-PRONG APPROACH: (1) Clearly established right — parental rights are fundamental (Troxel v. Granville, 530 US 57). "
         "(2) Obvious clarity — no reasonable judge would issue 5 ex parte orders in one day without hearing, jail a father "
         "for birthday messages, or exclude a court-ordered psych eval showing fitness. "
         "Hope v. Pelzer, 536 US 730 (2002): obvious clarity standard — specific prior case not required. "
         "Taylor v. Riojas, 592 US 7 (2020): violations so obvious that no precedent needed.",
         "C", "federal_strategy"),
        ("Judicial Immunity Pierce — Administrative Acts Exception",
         "PIERCE STRATEGY: Judicial immunity applies ONLY to judicial acts. Administrative acts are NOT protected. "
         "Forrester v. White, 484 US 219 (1988): hiring/firing decisions are administrative, not judicial. "
         "Stump v. Sparkman, 435 US 349 (1978): 4-factor test for judicial act. "
         "McNeill's administrative acts: (a) directing staff to listen to USB recording, (b) routing HealthWest eval "
         "to secretary, (c) coordinating with FOC at shared address, (d) scheduling ex parte without notice. "
         "These are administrative decisions that judicial immunity does NOT protect.",
         "E", "federal_strategy"),
    ]
    rows = []
    for title, text, lane, cat in workarounds:
        rows.append((
            "Federal_Civil_Rights_Citation_Index_VERIFIED.pdf",
            f"DOCTRINAL WORKAROUND: {title} — {text}",
            None, cat, lane, 9.5, "F04,F05", "federal,doctrinal_workaround,strategy",
        ))
    conn.executemany("""
        INSERT INTO evidence_quotes
        (source_file, quote_text, page_number, category, lane, relevance_score, filing_refs, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)
    conn.commit()
    ct = conn.execute("SELECT changes()").fetchone()[0]
    print(f"[2] Doctrinal workarounds: {ct} rows inserted into evidence_quotes")
    return ct

def persist_rico_elements(conn):
    """Persist RICO elements and criminal referral statutes."""
    rico_data = [
        ("RICO Elements — 18 USC §1962",
         "ENTERPRISE: McNeill + Hoopes + Ladas-Hoopes + Rusco + Barnes = associated-in-fact enterprise "
         "operating through 14th Circuit Court system (990 Terrace/435 Whitehall nexus). "
         "PATTERN: 2+ predicate acts within 10 years — (a) wire fraud (ex parte communications), "
         "(b) honest services fraud §1346, (c) extortion under color of right (Hobbs Act §1951), "
         "(d) obstruction of justice (evidence exclusion, filing ban). "
         "AFFECTING COMMERCE: Court system processes interstate commerce (child support, housing). "
         "18 USC §1964(c): treble damages + attorney fees for private RICO action.",
         "C", "federal_strategy"),
        ("Criminal Referral — 18 USC §241 Conspiracy Against Rights",
         "Whoever conspires to injure, oppress, threaten, or intimidate any person in the free exercise "
         "of any right secured by the Constitution. PENALTY: up to 10 years. "
         "APPLICATION: McNeill + Emily + Albert coordinated Aug 7-8 2025 to deprive Andrew of parental rights "
         "via premeditated ex parte order scheme (NS2505044 proves premeditation).",
         "C", "criminal_referral"),
        ("Criminal Referral — 18 USC §242 Deprivation Under Color of Law",
         "Whoever under color of any law willfully subjects any person to the deprivation of any rights "
         "secured by the Constitution. PENALTY: up to 10 years; up to life if bodily injury/death. "
         "APPLICATION: McNeill acting under color of judicial authority deprived Andrew of liberty (59 days jail), "
         "parental rights (300+ days), property (2 homes lost), and due process (ex parte orders without notice).",
         "E", "criminal_referral"),
        ("Criminal Referral — 18 USC §1346 Honest Services Fraud",
         "Scheme to deprive another of the intangible right of honest services. "
         "APPLICATION: McNeill owed honest judicial services to litigants. Instead provided rigged proceedings "
         "favoring Emily while concealing: Berry family connection, Barnes colleague relationship, "
         "FOC bias, and HealthWest evaluation results.",
         "E", "criminal_referral"),
        ("Criminal Referral — 18 USC §1951 Hobbs Act Extortion",
         "Extortion under color of official right — obtaining property from another with consent induced "
         "under color of official right. APPLICATION: McNeill used judicial authority to extract compliance: "
         "'shut my mouth' + contempt threats = coerced silence; medication requirement = coerced medical submission; "
         "filing ban = coerced waiver of access to courts.",
         "E", "criminal_referral"),
    ]
    rows = []
    for title, text, lane, cat in rico_data:
        rows.append((
            "Federal_Civil_Rights_Citation_Index_VERIFIED.pdf",
            f"{title}: {text}", None, cat, lane, 9.0, "F04,F05", "federal,rico,criminal_referral",
        ))
    conn.executemany("""
        INSERT INTO evidence_quotes
        (source_file, quote_text, page_number, category, lane, relevance_score, filing_refs, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)
    conn.commit()
    ct = conn.execute("SELECT changes()").fetchone()[0]
    print(f"[3] RICO + criminal referrals: {ct} rows inserted into evidence_quotes")
    return ct

def persist_damages_framework(conn):
    """Persist federal damages framework to authority_chains_v2."""
    damages = [
        ("Compensatory Damages (Parenting Time)",
         "Per-diem calculation: constitutional right to parent × days deprived. "
         "Carey v. Piphus, 435 US 247 (1978): actual injury must be proven for compensatory damages. "
         "Stachura, 477 US 299: not abstract value of rights but actual injuries suffered.",
         "42 USC 1983 (Carey v. Piphus)"),
        ("Compensatory Damages (False Imprisonment)",
         "59 days incarceration without adequate due process. "
         "Per-diem rate × days × conditions. Common range: $500-$5,000/day depending on conditions.",
         "42 USC 1983 (false imprisonment)"),
        ("Punitive Damages (§1983 Deterrence)",
         "Smith v. Wade, 461 US 30 (1983): punitive damages available when defendant acts with "
         "reckless or callous disregard of plaintiff's rights. "
         "McNeill's pattern of 5,059+ violations demonstrates reckless disregard.",
         "42 USC 1983 (Smith v. Wade)"),
        ("Nominal Damages (Rights Vindication)",
         "Carey v. Piphus: even without provable actual injury, nominal damages available "
         "for constitutional violation itself. Important for establishing precedent.",
         "42 USC 1983 (nominal damages)"),
        ("Attorney Fees / Costs (Pro Se)",
         "42 USC §1988: prevailing party entitled to attorney fees. "
         "Pro se litigants cannot recover attorney fees (Kay v. Ehrler, 499 US 432 (1991)) "
         "BUT can recover out-of-pocket litigation costs, filing fees, copying, mileage.",
         "42 USC 1988"),
    ]
    rows = []
    for title, text, primary in damages:
        rows.append((
            primary, f"Federal Damages: {title}", "supports",
            "Federal_Civil_Rights_Citation_Index_VERIFIED.pdf", "case_law", "C",
            text
        ))
    conn.executemany("""
        INSERT OR IGNORE INTO authority_chains_v2
        (primary_citation, supporting_citation, relationship, source_document, source_type, lane, paragraph_context)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, rows)
    conn.commit()
    ct = conn.execute("SELECT changes()").fetchone()[0]
    print(f"[4] Damages framework: {ct} rows inserted into authority_chains_v2")
    return ct

def persist_blueprint_defendants(conn):
    """Persist potential new defendants from BLUEPRINTS (VERIFIED names only)."""
    defendants = [
        ("Stacey Buhl", "FOC Referee, 14th Circuit",
         "BLUEPRINT identifies as FOC Referee involved in custody proceedings. REQUIRES VERIFICATION — "
         "not yet confirmed in evidence_quotes or police_reports. If confirmed, potential defendant for "
         "FOC bias claims and due process violations in referee recommendations.",
         "A", "defendant_identification"),
        ("Sarah Varran", "FOC Supervisor, 14th Circuit",
         "BLUEPRINT identifies as FOC Supervisor. REQUIRES VERIFICATION — supervisor of Rusco and FOC staff. "
         "Potential liability for failure to supervise, institutional bias in FOC recommendations.",
         "A", "defendant_identification"),
        ("Kim Avery", "Shady Oaks Park Manager/Agent",
         "BLUEPRINT identifies as Shady Oaks representative involved in housing actions. "
         "REQUIRES VERIFICATION — potential defendant for constructive eviction, property destruction, utility shutoff.",
         "B", "defendant_identification"),
        ("Brent Raterink", "Code Enforcement Officer",
         "BLUEPRINT identifies as code enforcement officer involved in housing inspections. "
         "REQUIRES VERIFICATION — potential defendant for selective enforcement, retaliatory inspections.",
         "B", "defendant_identification"),
    ]
    rows = []
    for name, role, text, lane, cat in defendants:
        rows.append((
            "COURT_FILING_PACKETS/BLUEPRINTS/federal_civil_rights_system_blueprint.pdf",
            f"POTENTIAL DEFENDANT (REQUIRES VERIFICATION): {name} — {role}. {text}",
            None, cat, lane, 5.0, "F04,F05", "defendant,blueprint,unverified",
        ))
    conn.executemany("""
        INSERT INTO evidence_quotes
        (source_file, quote_text, page_number, category, lane, relevance_score, filing_refs, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)
    conn.commit()
    ct = conn.execute("SELECT changes()").fetchone()[0]
    print(f"[5] Blueprint defendants: {ct} rows inserted into evidence_quotes")
    return ct

def main():
    conn = get_conn()
    total = 0
    try:
        total += persist_scotus_cases(conn)
        total += persist_doctrinal_workarounds(conn)
        total += persist_rico_elements(conn)
        total += persist_damages_framework(conn)
        total += persist_blueprint_defendants(conn)
        print(f"\n=== TOTAL: {total} rows persisted across authority_chains_v2 + evidence_quotes ===")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
