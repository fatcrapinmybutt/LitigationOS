#!/usr/bin/env python3
"""
Michigan Court Abbreviation Catalogue → litigation_context.db Ingestion Engine
Parses the 16-section legal catalogue and inserts structured data into:
  - courts (upsert)
  - michigan_case_law (upsert)
  - NEW: court_abbreviations, case_type_codes, constitutional_provisions,
         foc_duties, best_interest_factors, appellate_pathways, 
         administrative_bodies, legal_statutes, judicial_accountability,
         catalogue_verified_items
Also produces catalogue.json for machine-readable access.
"""

import sqlite3, json, os, sys, datetime

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
OUT_JSON = r"C:\Users\andre\LitigationOS\02_AUTHORITY\catalogue.json"
OUT_MD = r"C:\Users\andre\LitigationOS\02_AUTHORITY\michigan_court_catalogue.md"

def get_conn():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.row_factory = sqlite3.Row
    return conn

# ─────────────────────────────────────────────────────────────
# SCHEMA CREATION
# ─────────────────────────────────────────────────────────────
DDL = [
    """CREATE TABLE IF NOT EXISTS court_abbreviations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        abbreviation TEXT NOT NULL UNIQUE,
        full_name TEXT NOT NULL,
        acronym TEXT,
        tier TEXT NOT NULL,
        jurisdiction TEXT NOT NULL DEFAULT 'MI',
        constitutional_basis TEXT,
        description TEXT,
        website TEXT,
        citation_example TEXT,
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )""",
    """CREATE TABLE IF NOT EXISTS case_type_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL,
        label TEXT NOT NULL,
        court_type TEXT NOT NULL,
        case_type TEXT NOT NULL,
        description TEXT,
        authority TEXT,
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        UNIQUE(code, court_type)
    )""",
    """CREATE TABLE IF NOT EXISTS constitutional_provisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        provision TEXT NOT NULL UNIQUE,
        source TEXT NOT NULL,
        concept TEXT,
        description TEXT,
        relevance TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )""",
    """CREATE TABLE IF NOT EXISTS foc_duties (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mcl_section TEXT NOT NULL UNIQUE,
        duty TEXT NOT NULL,
        description TEXT,
        critical_note TEXT,
        source_url TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )""",
    """CREATE TABLE IF NOT EXISTS best_interest_factors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        factor_letter TEXT NOT NULL UNIQUE,
        mcl_subsection TEXT NOT NULL,
        description TEXT NOT NULL,
        strategic_note TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )""",
    """CREATE TABLE IF NOT EXISTS appellate_pathways (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        route_name TEXT NOT NULL UNIQUE,
        from_court TEXT NOT NULL,
        to_court TEXT NOT NULL,
        authority TEXT NOT NULL,
        standard TEXT,
        deadline TEXT,
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )""",
    """CREATE TABLE IF NOT EXISTS administrative_bodies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        abbreviation TEXT NOT NULL UNIQUE,
        full_name TEXT NOT NULL,
        body_type TEXT NOT NULL,
        scope TEXT,
        authority TEXT,
        parent_body TEXT,
        website TEXT,
        citation_example TEXT,
        description TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )""",
    """CREATE TABLE IF NOT EXISTS legal_statutes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        citation TEXT NOT NULL UNIQUE,
        title TEXT NOT NULL,
        act_name TEXT,
        subject TEXT,
        description TEXT,
        source_url TEXT,
        key_provisions TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )""",
    """CREATE TABLE IF NOT EXISTS judicial_accountability (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mechanism TEXT NOT NULL UNIQUE,
        authority TEXT NOT NULL,
        mechanism_type TEXT NOT NULL,
        who_files TEXT,
        description TEXT,
        process_steps TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )""",
    """CREATE TABLE IF NOT EXISTS catalogue_verified_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item TEXT NOT NULL,
        verified_value TEXT NOT NULL,
        primary_authority TEXT NOT NULL,
        verification_status TEXT NOT NULL DEFAULT 'VERIFIED',
        acquire_plan TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )""",
]

# ─────────────────────────────────────────────────────────────
# DATA — § 1+2: Court Abbreviations (State + Federal)
# ─────────────────────────────────────────────────────────────
COURT_ABBREVS = [
    ("Mich.", "Michigan Supreme Court", "MSC", "Supreme Court", "MI",
     "Mich. Const. 1963, art. VI, § 1; art. VI, § 4",
     "Highest court in Michigan. General superintending control over all courts. Final appellate jurisdiction.",
     "https://www.courts.michigan.gov/courts/michigan-supreme-court/",
     "Smith v Jones, 500 Mich 123 (2020)", None),
    ("Mich. App.", "Michigan Court of Appeals", "COA", "Appellate Court", "MI",
     "Mich. Const. 1963, art. VI, § 1",
     "Intermediate appellate court. Hears appeals from circuit courts, probate courts, and certain administrative agencies.",
     "https://www.courts.michigan.gov/courts/michigan-court-of-appeals/",
     "Smith v Jones, 300 Mich App 123 (2020)", None),
    ("Cir. Ct.", "Circuit Court", None, "Trial Court – General", "MI",
     "Mich. Const. 1963, art. VI, § 11",
     "Highest trial court. General jurisdiction: civil claims >$25K, felonies, family law, appeals from district/probate.",
     None, None, None),
    ("Dist. Ct.", "District Court", None, "Trial Court – Limited", "MI",
     "Mich. Const. 1963, art. VI, § 15",
     "People's court. Civil claims ≤$25K (MCL 600.8301), misdemeanors, civil infractions, landlord-tenant, small claims.",
     None, None, None),
    ("Prob. Ct.", "Probate Court", None, "Trial Court – Limited", "MI",
     "Mich. Const. 1963, art. VI, § 15",
     "Exclusive jurisdiction: estates, trusts, mental health, guardianships/conservatorships, matters involving minors.",
     None, None, None),
    ("Mun. Ct.", "Municipal Court", None, "Trial Court – Local", "MI",
     None,
     "Retained by small number of cities. Predate 1968 district court system. Local ordinances, limited civil.",
     None, None, "[UNVERIFIED: current exhaustive list of retained municipal courts]"),
    ("JTC", "Judicial Tenure Commission", None, "Administrative / Oversight Body", "MI",
     "Mich. Const. 1963, art. VI, § 30",
     "Independent body investigating judicial misconduct. Can recommend discipline including removal to MSC.",
     "http://jtc.courts.mi.gov/", None, None),
    # Federal courts
    ("U.S.", "United States Supreme Court", "SCOTUS", "Federal – Supreme Court", "US",
     "U.S. Const. art. III, § 1",
     "Highest federal court. Final authority on federal constitutional questions. Binding on all U.S. courts.",
     "https://www.supremecourt.gov/",
     "Marbury v. Madison, 5 U.S. (1 Cranch) 137 (1803)", None),
    ("6th Cir.", "U.S. Court of Appeals for the Sixth Circuit", None, "Federal – Circuit Court of Appeals", "US",
     None,
     "Federal intermediate appellate court covering Michigan, Ohio, Kentucky, Tennessee. Located in Cincinnati, OH.",
     "https://www.ca6.uscourts.gov/",
     "Smith v. Jones, 123 F.3d 456 (6th Cir. 2020)", None),
    ("E.D. Mich.", "U.S. District Court for the Eastern District of Michigan", None, "Federal – District Court", "US",
     None,
     "Federal trial court for eastern Michigan. Primary courthouse in Detroit.",
     "https://www.mied.uscourts.gov/",
     "Doe v. Roe, 456 F. Supp. 3d 789 (E.D. Mich. 2021)",
     "[UNVERIFIED: exhaustive list of division cities]"),
    ("W.D. Mich.", "U.S. District Court for the Western District of Michigan", None, "Federal – District Court", "US",
     None,
     "Federal trial court for western Michigan. Primary courthouse Grand Rapids. Divisions: GR, Kalamazoo, Lansing, Marquette.",
     "https://www.miwd.uscourts.gov/",
     "Doe v. Roe, 789 F. Supp. 3d 123 (W.D. Mich. 2021)", None),
]

# ─────────────────────────────────────────────────────────────
# DATA — § 3: Court Rule & Administrative Authorities
# ─────────────────────────────────────────────────────────────
ADMIN_BODIES = [
    ("MCR", "Michigan Court Rules", "Rule Set",
     "General procedure in all Michigan courts",
     "Promulgated by Michigan Supreme Court",
     "Michigan Supreme Court", None,
     "MCR 2.116 (summary disposition)",
     "Principal procedural rules governing practice in all Michigan courts. Covers pleadings, motions, discovery, trials, appeals."),
    ("MRE", "Michigan Rules of Evidence", "Rule Set",
     "Evidentiary standards in all Michigan courts",
     "Promulgated by Michigan Supreme Court",
     "Michigan Supreme Court", None,
     "MRE 803 (hearsay exceptions)",
     "Governs admissibility of evidence. Modeled in part on Federal Rules of Evidence."),
    ("MRPC", "Michigan Rules of Professional Conduct", "Rule Set",
     "Professional ethics for Michigan-licensed attorneys",
     "Promulgated by Michigan Supreme Court",
     "Michigan Supreme Court", None,
     "MRPC 1.7 (conflict of interest)",
     "Ethical rules for attorneys. Enforcement: Attorney Grievance Commission / Attorney Discipline Board."),
    ("MCJC", "Michigan Code of Judicial Conduct", "Rule Set",
     "Professional ethics for Michigan judges",
     "Promulgated by Michigan Supreme Court",
     "Michigan Supreme Court", None, None,
     "Sets ethical standards for judges. Enforced by Judicial Tenure Commission (JTC)."),
    ("SCAO", "State Court Administrative Office", "Administrative Body",
     "Statewide court administration and standardized forms",
     "Michigan Supreme Court (parent body)",
     "Michigan Supreme Court",
     "https://www.courts.michigan.gov/scao/", None,
     "Administrative arm of MSC. Provides admin support, court statistics, standard court forms."),
    ("APA", "Michigan Administrative Procedures Act of 1969", "Statute",
     "Foundation for all administrative agency proceedings",
     "MCL 24.201 et seq. (PA 306 of 1969)",
     None,
     "https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-Act-306-of-1969", None,
     "Establishes requirements for rulemaking, contested cases, notice/evidence/hearing, agency decisions, judicial review."),
    ("MOAHR", "Michigan Office of Administrative Hearings and Rules", "Administrative Agency",
     "Centralized administrative hearings for state agencies including MDHHS",
     "MI Admin Code R 792.10101 et seq.",
     "LARA",
     "https://www.michigan.gov/lara/bureau-list/moahr", None,
     "Within LARA. Administers MAHS Uniform Hearing Rules. NOT a court."),
    ("MDHHS", "Michigan Department of Health and Human Services", "Executive Agency",
     "Health, welfare, and social services programs",
     "MCL 400.1 et seq. (Social Welfare Act)", None,
     "https://www.michigan.gov/mdhhs", None,
     "Administers Medicaid, food assistance, cash assistance. Fair hearings adjudicated by MOAHR."),
]

# ─────────────────────────────────────────────────────────────
# DATA — § 6: Case Type Classification Codes
# ─────────────────────────────────────────────────────────────
CASE_TYPE_CODES = [
    # Circuit Court
    ("AA", "Administrative Agencies", "Circuit Court", "Appeal",
     "Appeals from state/local administrative agencies, licensing boards, regulatory bodies.", None, None),
    ("AR", "Criminal Appeals", "Circuit Court", "Appeal",
     "Appeals of criminal convictions or sentences from district court.", None, None),
    ("AV", "Civil Appeals", "Circuit Court", "Appeal",
     "Appeals of civil judgments from district or probate court.", None, None),
    ("CH", "Housing", "Circuit Court", "Civil",
     "Circuit-level housing matters including appeals from district court housing cases.", None, None),
    ("DM", "Divorce with Minor Children", "Circuit Court", "Domestic Relations",
     "Divorce/separate maintenance with minor children. Requires custody, PT, child support determinations.", None, None),
    ("FY", "Felony", "Circuit Court", "Criminal",
     "Felony-level offenses. Circuit courts have original jurisdiction over all felonies.", None, None),
    # District Court
    ("GC", "General Civil", "District Court", "Civil",
     "General civil claims for money damages up to $25,000.", "MCL 600.8301(1)", None),
    ("LT", "Landlord-Tenant", "District Court", "Civil",
     "Summary proceedings for possession of property, including eviction.", None, None),
    ("SC", "Small Claims", "District Court", "Civil",
     "Informal proceedings for civil money claims. Limit: $7,000 effective 2024-01-01. Attorneys generally barred.",
     "MCL 600.8401(1)(e)", None),
    ("SM", "Statute Misdemeanor", "District Court", "Criminal",
     "State-law misdemeanor offenses punishable by up to one year jail.", None, None),
    ("SI", "Statute Civil Infraction", "District Court", "Civil Infraction",
     "Non-criminal civil infractions including traffic offenses. No jail.", None, None),
    # Probate Court
    ("DA", "Supervised Estates", "Probate Court", "Estate",
     "Formal court-supervised administration of decedent's estate.", None, None),
    ("DE", "Unsupervised Estates", "Probate Court", "Estate",
     "Independent administration without routine court oversight.", None, None),
    ("MI", "Mental Illness", "Probate Court", "Mental Health",
     "Involuntary hospitalization/treatment proceedings for serious mental illness.", None, None),
    ("JA", "Judicial Admission", "Probate Court", "Mental Health",
     "Voluntary admission proceedings for mental health treatment under judicial oversight.", None, None),
    # Additional common codes
    ("DC", "Domestic – Custody", "Circuit Court", "Domestic Relations",
     "Custody cases including modification motions. Lane A in LitigationOS.", None, "Pigors v Watson: 2024-001507-DC"),
    ("PP", "Personal Protection", "Circuit Court", "Domestic Relations",
     "Personal protection orders (PPO/DVPO). Lane D in LitigationOS.", "MCL 600.2950", "Watson PPO: 2023-5907-PP"),
    ("CZ", "Civil – General", "Circuit Court", "Civil",
     "General civil cases in circuit court.", None, "Pigors v Watson housing: 2025-002760-CZ"),
]

# ─────────────────────────────────────────────────────────────
# DATA — § 7: Best Interest Factors (MCL 722.23)
# ─────────────────────────────────────────────────────────────
BEST_INTEREST = [
    ("a", "MCL 722.23(a)", "The love, affection, and other emotional ties existing between the parties involved and the child",
     "Andrew documented consistent contact attempts via AppClose despite withholding."),
    ("b", "MCL 722.23(b)", "The capacity and disposition of the parties to give the child love, affection, and guidance and to continue the education and raising of the child in their religion or creed",
     None),
    ("c", "MCL 722.23(c)", "The capacity and disposition of the parties to provide the child with food, clothing, medical care, and other material needs",
     "HealthWest cleared Andrew. LOCUS=12, Level One."),
    ("d", "MCL 722.23(d)", "The length of time the child has lived in a stable, satisfactory environment, and the desirability of maintaining continuity",
     None),
    ("e", "MCL 722.23(e)", "The permanence, as a family unit, of the existing or proposed custodial home",
     None),
    ("f", "MCL 722.23(f)", "The moral fitness of the parties involved",
     "Emily's false allegations pattern, meth use admission (Officer Randall report)."),
    ("g", "MCL 722.23(g)", "The mental and physical health of the parties involved",
     "HealthWest: Psychosis=0, Substance=0, Danger=0. EXCLUDED by McNeill."),
    ("h", "MCL 722.23(h)", "The home, school, and community record of the child",
     None),
    ("i", "MCL 722.23(i)", "The reasonable preference of the child, if the court considers the child to be of sufficient age to express preference",
     "L.D.W. too young (DOB Nov 9, 2022) for meaningful preference."),
    ("j", "MCL 722.23(j)", "The willingness and ability of each of the parties to facilitate and encourage a close and continuing parent-child relationship between the child and the other parent",
     "KEY FACTOR. Emily withholds child 230+ days. Factor (j) = willingness to foster. NOT MCL 722.27c (does not exist)."),
    ("k", "MCL 722.23(k)", "Domestic violence, regardless of whether the violence was directed against or witnessed by the child",
     "Emily's false DV allegations pattern — 0 evidence, 0 charges."),
    ("l", "MCL 722.23(l)", "Any other factor considered by the court to be relevant to a particular child custody dispute",
     "Judicial cartel (McNeill/Hoopes/Ladas-Hoopes), 59 days jail, loss of 2 homes + 2 jobs."),
]

# ─────────────────────────────────────────────────────────────
# DATA — § 8: Constitutional Provisions
# ─────────────────────────────────────────────────────────────
CONSTITUTIONAL = [
    ("U.S. Const. amend. XIV, § 1", "U.S. Constitution",
     "Due Process / Equal Protection",
     "No State shall deprive any person of life, liberty, or property without due process of law; nor deny equal protection",
     "Parental rights = fundamental liberty interest. Fathers cannot be treated differently without compelling state interest."),
    ("U.S. Const. amend. I", "U.S. Constitution",
     "Freedom of Speech/Religion/Assembly",
     "Freedom of speech, religion, and assembly",
     "Religious upbringing disputes MCL 722.23(b); parental expression. Birthday messages via AppClose = 1st Amendment."),
    ("U.S. Const. amend. IV", "U.S. Constitution",
     "Unreasonable Searches",
     "Right against unreasonable searches and seizures",
     "Home investigations by FOC or CPS."),
    ("U.S. Const. amend. V", "U.S. Constitution",
     "Due Process / Self-Incrimination",
     "Due process; right against self-incrimination",
     "Parallel federal due process protection."),
    ("U.S. Const. amend. VI", "U.S. Constitution",
     "Right to Counsel / Confrontation",
     "Right to counsel, confrontation of witnesses",
     "Applicable in criminal contempt proceedings arising from family law. Relevant to CRIMINAL lane."),
    ("Mich. Const. 1963, art. I, § 17", "Michigan Constitution",
     "Due Process",
     "No person shall be deprived of life, liberty, or property without due process of law",
     "State-level due process. All custody proceedings must satisfy notice + opportunity to be heard."),
    ("Mich. Const. 1963, art. I, § 2", "Michigan Constitution",
     "Equal Protection",
     "No person shall be denied equal protection of the laws",
     "Gender-neutral custody law. Fathers and mothers treated equally under MCL 722.23."),
    ("Mich. Const. 1963, art. VI, § 1", "Michigan Constitution",
     "One Court of Justice",
     "Establishes Michigan's unified court system",
     "Foundation for all Michigan courts."),
    ("Mich. Const. 1963, art. VI, § 4", "Michigan Constitution",
     "Superintending Control",
     "MSC shall have general superintending control over all courts",
     "Basis for MCR 7.306 superintending control. KEY for MSC original jurisdiction filings."),
    ("Mich. Const. 1963, art. VI, § 30", "Michigan Constitution",
     "Judicial Tenure Commission",
     "JTC established for judicial accountability",
     "Constitutional basis for JTC complaints against McNeill."),
]

# ─────────────────────────────────────────────────────────────
# DATA — § 9: FOC Duties
# ─────────────────────────────────────────────────────────────
FOC_DUTIES = [
    ("MCL 552.503", "Office creation / supervision",
     "Each circuit must have an FOC office; FOC serves under direction of the chief judge.", None, None),
    ("MCL 552.505(1)(a)", "Inform parties of rights",
     "FOC must inform parties of rights and available services at start of case.", None, None),
    ("MCL 552.505(1)(b)", "Pamphlets / self-help forms",
     "Must provide pamphlets explaining procedures, duties, rights, including right to meet with investigator.", None, None),
    ("MCL 552.505(1)(c)", "Motion forms",
     "Must make available forms/instructions for motions to modify support, custody, or parenting time.", None, None),
    ("MCL 552.505(1)(d)", "ADR notification",
     "Must inform parties about alternative dispute resolution options.", None, None),
    ("MCL 552.505(1)(e)", "Joint custody notice",
     "Must inform parents about the availability of joint custody.", None, None),
    ("MCL 552.505(1)(f)", "Custody investigation",
     "If ordered by court, FOC investigates all relevant facts regarding custody/PT, makes written report and recommendation.",
     "MCL 552.505(1)(f) requires FOC to grant meeting with party during investigation IF REQUESTED. Failure = procedural violation.",
     "https://legislature.mi.gov/Laws/MCL?objectName=mcl-552-505"),
    ("MCL 552.507", "Referee hearings",
     "FOC referees hear most domestic relations matters and issue recommended orders. 21 days to object for de novo review.", None, None),
    ("MCL 552.509", "Enforcement",
     "FOC must initiate enforcement proceedings for support, custody, parenting time, health care orders.", None, None),
    ("MCL 552.511", "Support enforcement",
     "Specific enforcement mechanisms for child support arrearages.", None, None),
    ("MCL 552.517d", "Parenting time enforcement",
     "FOC duties specific to parenting time compliance.", None, None),
    ("MCL 552.526", "Grievance procedure",
     "Step 1: Written grievance to FOC (30 day response). Step 2: Written grievance to Chief Judge (30 days). Step 3: Citizens Advisory Committee (MCL 552.528).",
     "Grievance form: SCAO FOC 1a. Grievances address office conduct, NOT legal decisions — those require de novo hearing or appeal.",
     "https://www.courts.michigan.gov/Administration/SCAO/Forms/courtforms/foc1a.pdf"),
]

# ─────────────────────────────────────────────────────────────
# DATA — § 10: Judicial Accountability Mechanisms
# ─────────────────────────────────────────────────────────────
ACCOUNTABILITY = [
    ("JTC complaint", "Mich. Const. art. VI, § 30; MCR 9.200", "Administrative",
     "Any person",
     "Independent constitutional body investigating judicial misconduct. Can recommend admonition through removal.",
     "1) File Request for Investigation 2) Confidential investigation 3) 28-day letter to judge 4) Formal public complaint 5) Hearing before master 6) Findings to JTC 7) MSC disposition: admonition→censure→suspension→retirement→removal"),
    ("Motion for disqualification/recusal", "MCR 2.003", "Court proceeding",
     "Party or attorney",
     "Motion + Affidavit of Bias. Must file ASAP after discovering grounds. MCR 2.003(C)(1): (a) personal knowledge, (b) bias/prejudice, (c) prior involvement.",
     None),
    ("Appeal for abuse of discretion", "MCR 7.203; MCR 7.301", "Appellate",
     "Party",
     "Challenge trial court decisions on appeal. Abuse of discretion standard for custody; clear error for findings of fact.",
     None),
    ("Complaint for superintending control", "MCR 3.302; Mich. Const. art. VI, § 4", "Extraordinary writ",
     "Party",
     "Extraordinary writ. No adequate legal remedy by appeal. MSC general superintending control over all courts.",
     None),
    ("42 U.S.C. § 1983 civil rights action", "42 U.S.C. § 1983; U.S. Const. amend. XIV", "Federal civil suit",
     "Affected party",
     "Federal cause of action against state actors who deprive constitutional rights under color of state law. Judicial immunity bars monetary damages for judicial acts, but injunctive/declaratory relief may be available (Pulliam v Allen, 466 U.S. 522).",
     None),
    ("Attorney Grievance Commission complaint", "MCR 9.100 et seq.", "Attorney discipline",
     "Any person",
     "Ethical violations by attorneys. Filed with AGC. Adjudicated by Attorney Discipline Board.",
     None),
    ("Legislative impeachment", "Mich. Const. art. XI, § 7", "Legislative",
     "Legislature",
     "Constitutional mechanism for removing judges through legislative process.",
     None),
]

# ─────────────────────────────────────────────────────────────
# DATA — § 11+12: Case Law (State + Federal)
# ─────────────────────────────────────────────────────────────
CASE_LAW = [
    # Michigan Family Law
    ("Vodvarka v Grasmeyer", "259 Mich App 499; 675 NW2d 847", "Mich. App.", 2003,
     "Established threshold standard for custody modification: proper cause or change of circumstances since last order; only post-order events generally considered.",
     "Custody modification standard — change of circumstances threshold", "A"),
    ("Ireland v Smith", "451 Mich 457; 547 NW2d 686", "Mich.", 1996,
     "Third-party daycare is not equivalent to parental care; court may consider parent's personal availability.",
     "Parental care vs daycare", "A"),
    ("Bowers v Bowers", "190 Mich App 751; 476 NW2d 666", "Mich. App.", 1991,
     "Established custodial environment determined by whether child naturally looks to custodian for guidance, discipline, necessities, comfort.",
     "Established custodial environment definition", "A"),
    ("Fletcher v Fletcher", "447 Mich 871; 526 NW2d 889", "Mich.", 1994,
     "MSC clarified standard: trial court must make findings on all best interest factors on the record.",
     "All 12 factors must be addressed on record", "A"),
    ("Shade v Wright", "291 Mich App 17; 805 NW2d 1", "Mich. App.", 2010,
     "Court must consider all 12 best interest factors when initial custody is determined; cannot skip factors.",
     "Cannot skip best interest factors", "A"),
    ("Eldred v Ziny", "246 Mich App 142; 631 NW2d 748", "Mich. App.", 2001,
     "Court must make independent findings on the record for each best interest factor; conclusory findings insufficient.",
     "Conclusory findings = insufficient = reversible error", "A"),
    ("Pierron v Pierron", "486 Mich 81; 782 NW2d 480", "Mich.", 2010,
     "Court must make specific findings for each best interest factor; failure is reversible error.",
     "Specific findings mandatory for each factor", "A"),
    ("Brown v Loveman", "260 Mich App 576; 680 NW2d 432", "Mich. App.", 2004,
     "Parenting time cannot be restricted without evidence of endangerment; must apply MCL 722.27a factors.",
     "PT restriction requires endangerment evidence", "A"),
    ("Berger v Berger", "277 Mich App 700; 747 NW2d 336", "Mich. App.", 2008,
     "Parent may not be denied PT solely because of refusal to comply with condition not required by law.",
     "Cannot condition PT on unlawful requirements — KEY for medication coercion", "A"),
    # Federal landmarks
    ("Stanley v Illinois", "405 U.S. 645", "U.S.", 1972,
     "Unwed fathers have due process right to fitness hearing before custody deprivation; cannot presume unfit based on gender/marital status.",
     "Father's due process rights — gender-neutral custody", "A,C"),
    ("Santosky v Kramer", "455 U.S. 745", "U.S.", 1982,
     "Termination of parental rights requires clear and convincing evidence — not merely preponderance.",
     "Clear and convincing standard for parental rights", "A,C"),
    ("Troxel v Granville", "530 U.S. 57", "U.S.", 2000,
     "14th Amendment protects parent's fundamental right to care, custody, control of children. Fit parents presumed to act in child's best interest.",
     "Fundamental parental rights under 14th Amendment", "A,C"),
    ("Meyer v Nebraska", "262 U.S. 390", "U.S.", 1923,
     "Liberty protected by 14th Amendment includes right to establish a home and bring up children.",
     "Foundation for parental liberty interest", "C"),
    ("Pierce v Society of Sisters", "268 U.S. 510", "U.S.", 1925,
     "Parents have fundamental liberty interest in directing upbringing and education of children.",
     "Parental direction of upbringing", "C"),
    ("Lassiter v Dep't of Social Services", "452 U.S. 18", "U.S.", 1981,
     "Due process may require appointment of counsel for indigent parents in termination proceedings, depending on circumstances.",
     "Right to counsel in termination proceedings", "C"),
    ("Pulliam v Allen", "466 U.S. 522", "U.S.", 1984,
     "Judicial immunity does NOT bar federal injunctive or declaratory relief under § 1983 for constitutional violations by judges (partially limited by FCIA 1996).",
     "Injunctive relief against judges — key for § 1983 Lane C", "C,E"),
    ("Mathews v Eldridge", "424 U.S. 319", "U.S.", 1976,
     "Three-factor balancing test for what process is due: (1) private interest, (2) risk of erroneous deprivation + value of safeguards, (3) government interest/burden.",
     "Due process balancing — USE THIS not Brady in family law", "A,C"),
]

# ─────────────────────────────────────────────────────────────
# DATA — § 13: Appellate Escalation Pathways
# ─────────────────────────────────────────────────────────────
APPELLATE_PATHS = [
    ("De novo hearing", "FOC Referee", "Circuit Court Judge",
     "MCL 552.507", "New evidence permitted", "21 days from recommended order",
     "ALWAYS object to unfavorable referee recommendations within 21 days."),
    ("Appeal of right", "Circuit Court", "Court of Appeals",
     "MCR 7.203(A); MCR 7.202(6)(a)(iii)",
     "Abuse of discretion for custody; clear error for findings of fact",
     "21 days from final order",
     "COA 366810 — Pigors v Watson currently on this pathway."),
    ("Application for leave (interlocutory)", "Circuit Court", "Court of Appeals",
     "MCR 7.203(B)", "Discretionary", "21 days from order", None),
    ("Application for leave to MSC", "Court of Appeals", "Michigan Supreme Court",
     "MCR 7.301", "Discretionary; significant legal question",
     "42 days from COA decision", None),
    ("Complaint for superintending control", "Any court", "Higher court",
     "MCR 3.302; Mich. Const. art. VI, § 4",
     "Extraordinary writ; no adequate legal remedy by appeal",
     "No strict deadline; file promptly",
     "KEY pathway when lower courts are compromised. Required for McNeill/Hoopes/Ladas-Hoopes cartel."),
    ("Mandamus / prohibition", "Trial court", "COA or MSC",
     "MCR 7.206", "Extraordinary writ; clear legal right; no other remedy",
     "File promptly", None),
    ("Federal habeas corpus", "State custody", "Federal court",
     "28 U.S.C. § 2254", "Exhaustion of state remedies required",
     "1 year from final state judgment", None),
    ("42 U.S.C. § 1983 action", "State actors", "Federal district court",
     "42 U.S.C. § 1983; 28 U.S.C. § 1331",
     "Constitutional violation under color of state law",
     "Michigan: 3 years statute of limitations",
     "Separate from Rooker-Feldman. Ongoing violations may proceed. Lane C."),
]

# ─────────────────────────────────────────────────────────────
# DATA — § 16: Verified Items
# ─────────────────────────────────────────────────────────────
VERIFIED_ITEMS = [
    ("District Court civil jurisdiction limit", "$25,000 (exclusive)", "MCL 600.8301(1)", "VERIFIED"),
    ("Small Claims jurisdictional limit (current)", "$7,000 effective 2024-01-01", "MCL 600.8401(1)(e)", "VERIFIED"),
    ("Small Claims limit prior period (2021-2023)", "$6,500", "MCL 600.8401", "VERIFIED"),
    ("MSC general superintending control", "Art. VI, § 4", "Mich. Const. 1963, art. VI, § 4", "VERIFIED"),
    ("MSC One Court of Justice foundation", "Art. VI, § 1", "Mich. Const. 1963, art. VI, § 1", "VERIFIED"),
    ("MOAHR parent department", "LARA", "michigan.gov/lara/bureau-list/moahr", "VERIFIED"),
    ("MAHS Uniform Hearing Rules scope", "R 792.10101", "MI Admin Code R 792.10101", "VERIFIED"),
    ("MAHS public benefits hearing scope", "R 792.11001", "MI Admin Code R 792.11001", "VERIFIED"),
    ("APA contested case definition", "MCL 24.203(3)", "MCL 24.201 et seq. (PA 306 of 1969)", "VERIFIED"),
    ("Business Court jurisdiction", "MCL 600.8035", "Michigan Legislature", "VERIFIED"),
    ("W.D. Mich. division locations", "Grand Rapids, Kalamazoo, Lansing, Marquette", "miwd.uscourts.gov", "VERIFIED"),
    ("6th Circuit states", "MI, OH, KY, TN", "ca6.uscourts.gov", "VERIFIED"),
    ("Child Custody Act of 1970", "MCL 722.21-722.31", "PA 91 of 1970", "VERIFIED"),
    ("Best Interest factors count", "12 factors in MCL 722.23", "MCL 722.23", "VERIFIED"),
    ("Gender neutrality of custody law", "No presumption for either parent", "MCL 722.23", "VERIFIED"),
    ("Parenting time authority", "MCL 722.27a", "Michigan Legislature", "VERIFIED"),
    ("Makeup parenting time", "MCL 722.27b", "Michigan Legislature", "VERIFIED"),
    ("Custody modification standard", "Proper cause or change of circumstances", "MCL 722.27(1)(c); Vodvarka", "VERIFIED"),
    ("100-mile rule", "MCL 722.31", "Michigan Legislature", "VERIFIED"),
    ("FOC creation and supervision", "MCL 552.503", "PA 294 of 1982", "VERIFIED"),
    ("FOC duties (custody investigation)", "MCL 552.505", "Michigan Legislature", "VERIFIED"),
    ("FOC referee hearings / de novo review", "MCL 552.507", "Michigan Legislature", "VERIFIED"),
    ("FOC grievance procedure", "MCL 552.526", "Michigan Legislature", "VERIFIED"),
    ("JTC constitutional basis", "Mich. Const. art. VI, § 30", "Michigan Constitution", "VERIFIED"),
    ("JTC court rules", "MCR 9.200 et seq.", "Michigan Supreme Court", "VERIFIED"),
    ("Stanley v Illinois", "405 U.S. 645 (1972)", "U.S. Supreme Court", "VERIFIED"),
    ("Santosky v Kramer", "455 U.S. 745 (1982)", "U.S. Supreme Court", "VERIFIED"),
    ("Troxel v Granville", "530 U.S. 57 (2000)", "U.S. Supreme Court", "VERIFIED"),
    ("Pulliam v Allen", "466 U.S. 522 (1984)", "U.S. Supreme Court", "VERIFIED"),
    ("42 U.S.C. § 1983", "Civil action for deprivation of rights", "Federal statute", "VERIFIED"),
    ("Appeal of right deadline", "21 days from final order", "MCR 7.204(A)", "VERIFIED"),
    ("Application for leave to MSC", "42 days from COA decision", "MCR 7.301", "VERIFIED"),
    ("Mathews v Eldridge", "424 U.S. 319 (1976)", "U.S. Supreme Court", "VERIFIED"),
]

UNVERIFIED_ITEMS = [
    ("Retained Michigan Municipal Courts list", None, None,
     "UNVERIFIED", "Consult SCAO court directory at courts.michigan.gov"),
    ("E.D. Mich. division city list", None, None,
     "UNVERIFIED", "Consult mied.uscourts.gov official court locator"),
    ("MUPA exact MCL citation", None, None,
     "UNVERIFIED", "Consult legislature.mi.gov for MCL 449 et seq."),
    ("Active Business Court circuit dockets", None, None,
     "UNVERIFIED", "Consult SCAO at courts.michigan.gov/business-court-search/"),
    ("SCAO case-type code provenance", None, None,
     "UNVERIFIED", "Request SCAO case-type code list or cite applicable SCAO administrative memorandum"),
    ("Michigan Citation Manual current edition", None, None,
     "UNVERIFIED", "Consult State Bar of Michigan or ICLE"),
    ("Law Library of Michigan URL", None, None,
     "UNVERIFIED", "Confirm at michigan.gov"),
]

# ─────────────────────────────────────────────────────────────
# DATA — Key Legal Statutes (§ 7 + § 4 + § 5)
# ─────────────────────────────────────────────────────────────
STATUTES = [
    ("MCL 722.21-722.31", "Child Custody Act of 1970", "PA 91 of 1970",
     "Custody / Family Law",
     "Foundational statute for all Michigan custody determinations. 12 best interest factors. Gender-neutral.",
     "https://legislature.mi.gov/Laws/MCL?objectName=mcl-Act-91-of-1970",
     "MCL 722.23 (factors), 722.27 (modification), 722.27a (PT), 722.27b (makeup PT), 722.31 (100-mile)"),
    ("MCL 552.501-552.535", "Friend of the Court Act", "PA 294 of 1982",
     "Court Administration",
     "Creates FOC office in each circuit. Duties: investigation, enforcement, referee hearings, grievance process.",
     "https://legislature.mi.gov/Laws/MCL?objectName=MCL-ACT-294-OF-1982",
     "552.503 (creation), 552.505 (duties), 552.507 (referee), 552.526 (grievance)"),
    ("MCL 24.201 et seq.", "Administrative Procedures Act", "PA 306 of 1969",
     "Administrative Law",
     "Foundation for all administrative agency proceedings. Rulemaking, contested cases, judicial review.",
     "https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-Act-306-of-1969",
     "24.203(3) (contested case def), 24.271-24.288 (hearings), 24.301+ (judicial review)"),
    ("MCL 600.8301", "District Court Jurisdiction", "Revised Judicature Act",
     "Jurisdiction",
     "District court exclusive jurisdiction in civil actions ≤$25,000.",
     "https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-600-8301", None),
    ("MCL 600.8401", "Small Claims Jurisdiction", "Revised Judicature Act",
     "Jurisdiction",
     "Small claims limit: $7,000 effective 2024-01-01. Schedule of prior limits in statute.",
     "https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-600-8401", None),
    ("MCL 600.8035", "Business Court Jurisdiction", "Revised Judicature Act",
     "Jurisdiction / Business",
     "Business courts as specialized dockets within circuit court for commercial disputes.",
     "https://www.legislature.mi.gov/Laws/MCL?objectName=MCL-600-8035", None),
    ("MCL 450.1101 et seq.", "Michigan Business Corporation Act", "BCA",
     "Corporate Law",
     "Formation, governance, dissolution of Michigan business corporations.",
     "https://www.legislature.mi.gov/", None),
    ("MCL 440.1101 et seq.", "Uniform Commercial Code (MI)", "UCC",
     "Commercial Law",
     "Commercial transactions: sales, secured transactions, negotiable instruments.",
     "https://www.legislature.mi.gov/", None),
    ("MCL 450.4101 et seq.", "Michigan LLC Act", "LLC Act",
     "Business Law",
     "Formation, governance, dissolution of Michigan LLCs.",
     "https://www.legislature.mi.gov/", None),
    ("MCL 600.2950", "Personal Protection Orders", "Revised Judicature Act",
     "PPO / Domestic Relations",
     "PPO authority. Ex parte if immediate harm. Lane D in LitigationOS.",
     "https://www.legislature.mi.gov/", None),
    ("42 U.S.C. § 1983", "Civil Action for Deprivation of Rights", "Federal Statute",
     "Federal Civil Rights",
     "Federal cause of action against state actors who deprive constitutional rights under color of state law.",
     "https://www.law.cornell.edu/uscode/text/42/1983",
     "Monetary damages barred for judicial acts. Injunctive/declaratory relief available (Pulliam). Qualified immunity for non-judicial actors."),
    ("28 U.S.C. § 1331", "Federal Question Jurisdiction", "Federal Statute",
     "Federal Jurisdiction",
     "District courts have original jurisdiction of civil actions arising under Constitution, laws, or treaties of US.",
     "https://www.law.cornell.edu/uscode/text/28/1331", None),
    ("28 U.S.C. § 2254", "Federal Habeas Corpus", "Federal Statute",
     "Federal Habeas",
     "Habeas corpus for persons in state custody. Exhaustion of state remedies required. 1-year limitations.",
     "https://www.law.cornell.edu/uscode/text/28/2254", None),
]


def main():
    conn = get_conn()
    ts = datetime.datetime.now().isoformat()
    counts = {}

    # 1. Create tables
    print(f"[{ts[:19]}] Creating tables...")
    for ddl in DDL:
        conn.execute(ddl)
    conn.commit()
    print(f"  → {len(DDL)} tables created/verified")

    # 2. Court Abbreviations
    print("Inserting court abbreviations...")
    c = 0
    for row in COURT_ABBREVS:
        try:
            conn.execute(
                "INSERT OR REPLACE INTO court_abbreviations "
                "(abbreviation, full_name, acronym, tier, jurisdiction, constitutional_basis, "
                "description, website, citation_example, notes) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)", row)
            c += 1
        except Exception as e:
            print(f"  WARN: {row[0]}: {e}")
    conn.commit()
    counts["court_abbreviations"] = c
    print(f"  → {c} court abbreviations")

    # 3. Administrative Bodies
    print("Inserting administrative bodies...")
    c = 0
    for row in ADMIN_BODIES:
        try:
            conn.execute(
                "INSERT OR REPLACE INTO administrative_bodies "
                "(abbreviation, full_name, body_type, scope, authority, parent_body, "
                "website, citation_example, description) "
                "VALUES (?,?,?,?,?,?,?,?,?)", row)
            c += 1
        except Exception as e:
            print(f"  WARN: {row[0]}: {e}")
    conn.commit()
    counts["administrative_bodies"] = c
    print(f"  → {c} administrative bodies")

    # 4. Case Type Codes
    print("Inserting case type codes...")
    c = 0
    for row in CASE_TYPE_CODES:
        try:
            conn.execute(
                "INSERT OR REPLACE INTO case_type_codes "
                "(code, label, court_type, case_type, description, authority, notes) "
                "VALUES (?,?,?,?,?,?,?)", row)
            c += 1
        except Exception as e:
            print(f"  WARN: {row[0]}: {e}")
    conn.commit()
    counts["case_type_codes"] = c
    print(f"  → {c} case type codes")

    # 5. Best Interest Factors
    print("Inserting best interest factors...")
    c = 0
    for row in BEST_INTEREST:
        try:
            conn.execute(
                "INSERT OR REPLACE INTO best_interest_factors "
                "(factor_letter, mcl_subsection, description, strategic_note) "
                "VALUES (?,?,?,?)", row)
            c += 1
        except Exception as e:
            print(f"  WARN: {row[0]}: {e}")
    conn.commit()
    counts["best_interest_factors"] = c
    print(f"  → {c} best interest factors")

    # 6. Constitutional Provisions
    print("Inserting constitutional provisions...")
    c = 0
    for row in CONSTITUTIONAL:
        try:
            conn.execute(
                "INSERT OR REPLACE INTO constitutional_provisions "
                "(provision, source, concept, description, relevance) "
                "VALUES (?,?,?,?,?)", row)
            c += 1
        except Exception as e:
            print(f"  WARN: {row[0]}: {e}")
    conn.commit()
    counts["constitutional_provisions"] = c
    print(f"  → {c} constitutional provisions")

    # 7. FOC Duties
    print("Inserting FOC duties...")
    c = 0
    for row in FOC_DUTIES:
        try:
            conn.execute(
                "INSERT OR REPLACE INTO foc_duties "
                "(mcl_section, duty, description, critical_note, source_url) "
                "VALUES (?,?,?,?,?)", row)
            c += 1
        except Exception as e:
            print(f"  WARN: {row[0]}: {e}")
    conn.commit()
    counts["foc_duties"] = c
    print(f"  → {c} FOC duties")

    # 8. Judicial Accountability
    print("Inserting judicial accountability mechanisms...")
    c = 0
    for row in ACCOUNTABILITY:
        try:
            conn.execute(
                "INSERT OR REPLACE INTO judicial_accountability "
                "(mechanism, authority, mechanism_type, who_files, description, process_steps) "
                "VALUES (?,?,?,?,?,?)", row)
            c += 1
        except Exception as e:
            print(f"  WARN: {row[0]}: {e}")
    conn.commit()
    counts["judicial_accountability"] = c
    print(f"  → {c} accountability mechanisms")

    # 9. Case Law (upsert into michigan_case_law)
    print("Upserting case law...")
    c = 0
    for row in CASE_LAW:
        name, cite, court, year, holding, relevance, lane = row
        existing = conn.execute(
            "SELECT id FROM michigan_case_law WHERE citation = ?", (cite,)
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE michigan_case_law SET holding=?, relevance=?, lane=? WHERE citation=?",
                (holding, relevance, lane, cite))
        else:
            conn.execute(
                "INSERT INTO michigan_case_law (case_name, citation, court, year, holding, relevance, lane) "
                "VALUES (?,?,?,?,?,?,?)", (name, cite, court, year, holding, relevance, lane))
        c += 1
    conn.commit()
    counts["case_law_upserted"] = c
    print(f"  → {c} case law entries upserted")

    # 10. Appellate Pathways
    print("Inserting appellate pathways...")
    c = 0
    for row in APPELLATE_PATHS:
        try:
            conn.execute(
                "INSERT OR REPLACE INTO appellate_pathways "
                "(route_name, from_court, to_court, authority, standard, deadline, notes) "
                "VALUES (?,?,?,?,?,?,?)", row)
            c += 1
        except Exception as e:
            print(f"  WARN: {row[0]}: {e}")
    conn.commit()
    counts["appellate_pathways"] = c
    print(f"  → {c} appellate pathways")

    # 11. Legal Statutes
    print("Inserting legal statutes...")
    c = 0
    for row in STATUTES:
        try:
            conn.execute(
                "INSERT OR REPLACE INTO legal_statutes "
                "(citation, title, act_name, subject, description, source_url, key_provisions) "
                "VALUES (?,?,?,?,?,?,?)", row)
            c += 1
        except Exception as e:
            print(f"  WARN: {row[0]}: {e}")
    conn.commit()
    counts["legal_statutes"] = c
    print(f"  → {c} legal statutes")

    # 12. Verified Items
    print("Inserting verified/unverified items...")
    c = 0
    for row in VERIFIED_ITEMS:
        try:
            conn.execute(
                "INSERT OR REPLACE INTO catalogue_verified_items "
                "(item, verified_value, primary_authority, verification_status) "
                "VALUES (?,?,?,?)", row)
            c += 1
        except Exception as e:
            print(f"  WARN: {row[0]}: {e}")
    for item, _, _, status, plan in UNVERIFIED_ITEMS:
        try:
            conn.execute(
                "INSERT OR REPLACE INTO catalogue_verified_items "
                "(item, verified_value, primary_authority, verification_status, acquire_plan) "
                "VALUES (?,?,?,?,?)", (item, "PENDING", "PENDING", status, plan))
            c += 1
        except Exception as e:
            print(f"  WARN: {item}: {e}")
    conn.commit()
    counts["verified_items"] = c
    print(f"  → {c} verified/unverified items")

    # 13. Upsert into courts table (expand from 3 to 11+)
    print("Upserting courts table...")
    c = 0
    for row in COURT_ABBREVS:
        abbr, name, acronym, tier, juris, const, desc, web, cite, notes = row
        existing = conn.execute("SELECT id FROM courts WHERE name = ?", (name,)).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO courts (name, type, efiling_url, notes, jurisdiction_id) VALUES (?,?,?,?,?)",
                (name, tier.lower().replace(" ", "_").replace("–", ""), web, desc, juris))
            c += 1
    conn.commit()
    counts["courts_added"] = c
    print(f"  → {c} new courts added")

    # ─── Generate catalogue.json ───
    print("\nGenerating catalogue.json...")
    catalogue = {
        "generated": datetime.datetime.now().isoformat(),
        "source": "Michigan Court Abbreviation Catalogue v1.0",
        "sections": {
            "court_abbreviations": [
                {"abbreviation": r[0], "full_name": r[1], "acronym": r[2], 
                 "tier": r[3], "jurisdiction": r[4], "constitutional_basis": r[5],
                 "description": r[6], "website": r[7]}
                for r in COURT_ABBREVS
            ],
            "administrative_bodies": [
                {"abbreviation": r[0], "full_name": r[1], "type": r[2],
                 "scope": r[3], "authority": r[4], "parent": r[5]}
                for r in ADMIN_BODIES
            ],
            "case_type_codes": [
                {"code": r[0], "label": r[1], "court": r[2], 
                 "type": r[3], "description": r[4], "authority": r[5]}
                for r in CASE_TYPE_CODES
            ],
            "best_interest_factors": [
                {"factor": r[0], "subsection": r[1], "description": r[2]}
                for r in BEST_INTEREST
            ],
            "constitutional_provisions": [
                {"provision": r[0], "source": r[1], "concept": r[2], "text": r[3]}
                for r in CONSTITUTIONAL
            ],
            "foc_duties": [
                {"section": r[0], "duty": r[1], "description": r[2]}
                for r in FOC_DUTIES
            ],
            "case_law": [
                {"name": r[0], "citation": r[1], "court": r[2], "year": r[3], "holding": r[4]}
                for r in CASE_LAW
            ],
            "appellate_pathways": [
                {"route": r[0], "from": r[1], "to": r[2], "authority": r[3],
                 "standard": r[4], "deadline": r[5]}
                for r in APPELLATE_PATHS
            ],
            "legal_statutes": [
                {"citation": r[0], "title": r[1], "act": r[2], "subject": r[3]}
                for r in STATUTES
            ],
            "accountability_mechanisms": [
                {"mechanism": r[0], "authority": r[1], "type": r[2], "who_files": r[3]}
                for r in ACCOUNTABILITY
            ],
        },
        "verification": {
            "verified_count": len(VERIFIED_ITEMS),
            "unverified_count": len(UNVERIFIED_ITEMS),
            "items": [
                {"item": r[0], "value": r[1], "authority": r[2], "status": r[3]}
                for r in VERIFIED_ITEMS
            ] + [
                {"item": r[0], "status": r[3], "acquire_plan": r[4]}
                for r in UNVERIFIED_ITEMS
            ],
        }
    }

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(catalogue, f, indent=2, ensure_ascii=False)
    print(f"  → catalogue.json written: {os.path.getsize(OUT_JSON):,} bytes")

    # ─── Final verification ───
    print("\n" + "=" * 60)
    print("INGESTION COMPLETE — VERIFICATION")
    print("=" * 60)
    total = 0
    for table, count in counts.items():
        total += count
        # Verify actual DB count
        tname = table.replace("_upserted", "").replace("_added", "")
        if tname in ("case_law", "courts"):
            tname = "michigan_case_law" if "case" in tname else "courts"
        try:
            db_count = conn.execute(f"SELECT COUNT(*) FROM {tname}").fetchone()[0]
            print(f"  {table:30s}: {count:4d} inserted → {db_count:6d} total in DB")
        except:
            print(f"  {table:30s}: {count:4d} inserted")
    print(f"\n  TOTAL RECORDS INGESTED: {total}")
    print(f"  Tables created/updated: {len(counts)}")

    # Cross-reference check: case law now in DB
    case_count = conn.execute("SELECT COUNT(*) FROM michigan_case_law").fetchone()[0]
    print(f"\n  michigan_case_law total: {case_count} (was 58)")
    courts_count = conn.execute("SELECT COUNT(*) FROM courts").fetchone()[0]
    print(f"  courts total: {courts_count} (was 3)")

    # New tables
    for t in ["court_abbreviations", "case_type_codes", "constitutional_provisions",
              "foc_duties", "best_interest_factors", "appellate_pathways",
              "administrative_bodies", "legal_statutes", "judicial_accountability",
              "catalogue_verified_items"]:
        cnt = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {cnt}")

    conn.close()
    print(f"\n✅ ALL DONE — {total} records across {len(counts)} tables + catalogue.json")


if __name__ == "__main__":
    main()
