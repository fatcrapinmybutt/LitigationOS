"""Persist Federal Civil Rights Citation Index + Court Rules Harvest to litigation_context.db"""
import sqlite3
import os
from datetime import datetime

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"

def get_conn():
    conn = sqlite3.connect(DB, timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    return conn

def persist_federal_case_law(conn):
    """Persist verified Supreme Court case law from Federal Citation Index PDF."""
    cases = [
        # Parental Rights
        ("Troxel v. Granville", "530 U.S. 57 (2000)", "SCOTUS", "Liberty interest of parents in care, custody, control of children is fundamental. Court cannot use freestanding best interest to override fit parent decision.", "parental_rights", "C,A,F", 10.0, "F04,F05,F01,F09"),
        ("Stanley v. Illinois", "405 U.S. 645 (1972)", "SCOTUS", "Unwed father has constitutionally protected interest in children. Cannot deprive without hearing on fitness.", "parental_rights", "C,A", 9.0, "F04,F05"),
        ("Santosky v. Kramer", "455 U.S. 745 (1982)", "SCOTUS", "Before severing parental rights, state must prove by clear and convincing evidence.", "parental_rights", "C,A,F", 9.0, "F04,F05,F09"),
        ("Meyer v. Nebraska", "262 U.S. 390 (1923)", "SCOTUS", "Due Process protects right to establish home, bring up children. Foundational parent-child constitutional protection.", "parental_rights", "C", 8.0, "F04"),
        # Due Process / Neutral Tribunal
        ("Mathews v. Eldridge", "424 U.S. 319 (1976)", "SCOTUS", "Three-factor balancing for due process: private interest, risk of erroneous deprivation, government interest. High process required for fundamental interests.", "due_process", "C,E,A,F", 10.0, "F04,F06,F01,F09"),
        ("Tumey v. Ohio", "273 U.S. 510 (1927)", "SCOTUS", "Defendant deprived of due process if required to submit to non-impartial tribunal. Even appearance of partiality violates due process.", "judicial_bias", "C,E", 9.0, "F04,F06"),
        ("In re Murchison", "349 U.S. 133 (1955)", "SCOTUS", "Fair trial in fair tribunal is basic due process requirement. Justice must satisfy the appearance of justice.", "judicial_bias", "C,E", 9.0, "F04,F06"),
        ("Withrow v. Larkin", "421 U.S. 35 (1975)", "SCOTUS", "Due process requires impartial tribunal. Combination of investigative and adjudicative roles creates constitutional concern.", "judicial_bias", "C,E", 8.0, "F04,F06"),
        ("Ward v. Village of Monroeville", "409 U.S. 57 (1972)", "SCOTUS", "When judge system itself compromised, remedy is removal from system entirely, not appeal within system.", "judicial_bias", "C,E", 9.0, "F04,F06,F01"),
        ("Caperton v. A.T. Massey Coal Co.", "556 U.S. 868 (2009)", "SCOTUS", "Due Process requires recusal when extreme facts create probability of bias too high to be constitutionally tolerable. Objective standard. PRIMARY JUDICIAL DISQUALIFICATION AUTHORITY.", "judicial_bias", "C,E,A,F", 10.0, "F04,F06,F01,F03,F09"),
        # Fraud on Court
        ("Hazel-Atlas Glass Co. v. Hartford-Empire Co.", "322 U.S. 238 (1944)", "SCOTUS", "Courts have inherent power to vacate judgments obtained through fraud regardless of term expiration. No time limit on challenging void judgments.", "fraud_on_court", "C,A,D,F", 10.0, "F04,F05,F01,F09"),
        ("County of Sacramento v. Lewis", "523 U.S. 833 (1998)", "SCOTUS", "Substantive due process violated when government conduct shocks the conscience — egregious or arbitrary in constitutional sense.", "substantive_due_process", "C", 9.0, "F04"),
        # Civil Rights Damages
        ("Memphis Community School Dist. v. Stachura", "477 U.S. 299 (1986)", "SCOTUS", "Section 1983 plaintiffs may recover compensatory for actual injuries including non-economic. Punitive available for malice or reckless indifference.", "damages", "C", 8.0, "F04"),
        ("Thompson v. Clark", "596 U.S. 36 (2022)", "SCOTUS", "For section 1983 malicious prosecution, plaintiff need not show prosecution ended with affirmative indication of innocence. Most recent SCOTUS ruling on 1983 malicious prosecution.", "malicious_prosecution", "C", 9.0, "F04"),
        # Appellate Access
        ("Griffin v. Illinois", "351 U.S. 12 (1956)", "SCOTUS", "State cannot structure appellate system to deny meaningful review to any class.", "appellate_access", "C,F", 8.0, "F04,F09"),
        ("Evitts v. Lucey", "469 U.S. 387 (1985)", "SCOTUS", "Due process guarantees fair appellate proceeding where appeal provided.", "appellate_access", "C,F", 8.0, "F04,F09"),
        # Rooker-Feldman / Jurisdiction
        ("Exxon Mobil Corp. v. Saudi Basic Industries Corp.", "544 U.S. 280 (2005)", "SCOTUS", "Rooker-Feldman confined to state-court losers complaining of injuries caused by state-court judgments. Does not bar independent constitutional claims. PRIMARY ROOKER-FELDMAN WORKAROUND.", "federal_jurisdiction", "C", 10.0, "F04"),
        # Conspiracy
        ("Griffin v. Breckenridge", "403 U.S. 88 (1971)", "SCOTUS", "Section 1985(3) class-based animus requirement. Gender discrimination against fathers satisfies.", "conspiracy", "C", 8.0, "F04"),
        # Qualified Immunity
        ("Harlow v. Fitzgerald", "457 U.S. 800 (1982)", "SCOTUS", "Officers liable only if violated clearly established right. Absolute judicial immunity not available for administrative acts or acts in absence of all jurisdiction.", "immunity", "C", 8.0, "F04"),
    ]

    cursor = conn.cursor()
    inserted = 0
    for case_name, citation, source_type, holding, category, lane, score, filing_refs in cases:
        quote_text = f"[VERIFIED SCOTUS] {case_name}, {citation}: {holding}"
        cursor.execute("""
            INSERT INTO evidence_quotes (source_file, quote_text, page_number, category, lane, relevance_score, filing_refs, tags, is_duplicate, duplicate_of)
            SELECT ?, ?, 1, ?, ?, ?, ?, ?, 0, NULL
            WHERE NOT EXISTS (SELECT 1 FROM evidence_quotes WHERE quote_text LIKE ?)
        """, (
            "Federal_Civil_Rights_Citation_Index_VERIFIED.pdf",
            quote_text, category, lane, score, filing_refs,
            f"scotus,verified,{source_type.lower()},{category}",
            f"%{case_name}%{citation}%"
        ))
        inserted += cursor.rowcount

    # Also add to authority_chains_v2
    authority_rows = [
        ("42 USC 1983", "Troxel v. Granville, 530 U.S. 57 (2000)", "supports", "Federal_Citation_Index", "verified_authority", "C", "Parental rights fundamental liberty interest under 14th Amendment"),
        ("42 USC 1983", "Caperton v. A.T. Massey Coal Co., 556 U.S. 868 (2009)", "supports", "Federal_Citation_Index", "verified_authority", "C", "Judicial bias probability standard for disqualification"),
        ("42 USC 1983", "Mathews v. Eldridge, 424 U.S. 319 (1976)", "supports", "Federal_Citation_Index", "verified_authority", "C", "Three-factor due process balancing test"),
        ("42 USC 1983", "Hazel-Atlas Glass Co. v. Hartford-Empire Co., 322 U.S. 238 (1944)", "supports", "Federal_Citation_Index", "verified_authority", "C", "Fraud on court vacatur - no time limit"),
        ("42 USC 1983", "Exxon Mobil Corp. v. Saudi Basic Industries, 544 U.S. 280 (2005)", "supports", "Federal_Citation_Index", "verified_authority", "C", "Rooker-Feldman workaround for independent constitutional claims"),
        ("42 USC 1983", "Thompson v. Clark, 596 U.S. 36 (2022)", "supports", "Federal_Citation_Index", "verified_authority", "C", "Malicious prosecution favorable termination standard"),
        ("42 USC 1985(3)", "Griffin v. Breckenridge, 403 U.S. 88 (1971)", "supports", "Federal_Citation_Index", "verified_authority", "C", "Class-based animus for conspiracy claims"),
        ("42 USC 1983", "County of Sacramento v. Lewis, 523 U.S. 833 (1998)", "supports", "Federal_Citation_Index", "verified_authority", "C", "Shocks the conscience substantive due process standard"),
        ("42 USC 1988", "42 USC 1988(b)", "supports", "Federal_Citation_Index", "verified_authority", "C", "Attorney fees for prevailing 1983/1985/1986 plaintiff"),
        ("18 USC 1962(c)", "18 USC 1964(c)", "enables", "Federal_Citation_Index", "verified_authority", "C", "RICO treble damages plus mandatory attorney fees"),
    ]

    for primary, supporting, relationship, source_doc, source_type, lane, context in authority_rows:
        cursor.execute("""
            INSERT INTO authority_chains_v2 (primary_citation, supporting_citation, relationship, source_document, source_type, lane, paragraph_context)
            SELECT ?, ?, ?, ?, ?, ?, ?
            WHERE NOT EXISTS (SELECT 1 FROM authority_chains_v2 WHERE primary_citation = ? AND supporting_citation = ? AND source_document = ?)
        """, (primary, supporting, relationship, source_doc, source_type, lane, context,
              primary, supporting, source_doc))
        inserted += cursor.rowcount

    conn.commit()
    return inserted

def persist_federal_statutes(conn):
    """Persist federal statute authorities."""
    statutes = [
        ("42 USC 1983", "Civil Action for Deprivation of Rights", "Every person acting under color of state law who deprives a citizen of constitutionally protected rights is liable for compensatory and punitive damages.", "C", 10.0, "F04"),
        ("42 USC 1985(3)", "Conspiracy to Interfere with Civil Rights", "Two or more persons conspiring to deprive person of equal protection liable for damages. Requires class-based animus (gender discrimination against fathers). Overt act + injury.", "C", 10.0, "F04"),
        ("42 USC 1986", "Action for Neglect to Prevent", "Persons with knowledge of 1985 conspiracy and power to prevent who fail to act are liable. Derivative — must bring 1985 first.", "C", 8.0, "F04"),
        ("42 USC 1988(b)", "Attorney Fees in Civil Rights Actions", "Prevailing plaintiff in 1983/1985/1986 action may recover reasonable attorney fees via lodestar method.", "C", 7.0, "F04"),
        ("18 USC 1962(c)(d)", "RICO — Racketeer Influenced and Corrupt Organizations", "Unlawful to conduct enterprise affairs through pattern of racketeering. Civil remedy: treble damages plus mandatory attorney fees under 18 USC 1964(c).", "C", 9.0, "F04"),
        ("18 USC 241", "Criminal Conspiracy Against Rights", "Conspiracy to injure/oppress in exercise of federal rights. Up to 10 years. FBI referral only.", "C", 7.0, "F04"),
        ("18 USC 242", "Criminal Deprivation Under Color of Law", "Criminal deprivation of constitutional rights under color of law. 1-10 years imprisonment. FBI referral.", "C", 7.0, "F04"),
    ]

    cursor = conn.cursor()
    inserted = 0
    for citation, title, text, lane, score, filing_refs in statutes:
        quote = f"[FEDERAL STATUTE] {citation} — {title}: {text}"
        cursor.execute("""
            INSERT INTO evidence_quotes (source_file, quote_text, page_number, category, lane, relevance_score, filing_refs, tags, is_duplicate, duplicate_of)
            SELECT ?, ?, 1, 'federal_statute', ?, ?, ?, 'federal,statute,verified,1983', 0, NULL
            WHERE NOT EXISTS (SELECT 1 FROM evidence_quotes WHERE quote_text LIKE ?)
        """, ("Federal_Civil_Rights_Citation_Index_VERIFIED.pdf", quote, lane, score, filing_refs, f"%{citation}%{title}%"))
        inserted += cursor.rowcount

    conn.commit()
    return inserted

def persist_defense_workarounds(conn):
    """Persist defense doctrine workarounds from the citation index."""
    workarounds = [
        ("Rooker-Feldman", "Frame federal complaint not as appeal of state decisions but as forward-looking 1983 action for constitutional violations by state actors. Void judgment from fraud/bias not entitled to Rooker-Feldman protection. Exxon Mobil v. Saudi Basic, 544 U.S. 280 (2005).", "F04"),
        ("Younger Abstention", "Four exceptions ALL present: bad faith prosecution (criminal timed with custody); harassment (PPO + eviction + custody + criminal); flagrant unconstitutionality (all judges connected); irreparable harm (permanent child separation). Sprint Communications v. Jacobs, 571 U.S. 69 (2013).", "F04"),
        ("Qualified Immunity", "Judicial bias (Caperton 2009), fraud on court, ex parte communications all clearly established rights. Secretary has weaker immunity. 1985 conspiracy claims not subject to QI same way. Harlow v. Fitzgerald, 457 U.S. 800 (1982).", "F04"),
        ("Absolute Judicial Immunity", "Not available for: administrative acts (scheduling, access); acts in absence of all jurisdiction; prospective injunctive relief; 1983 prospective claims survive immunity.", "F04"),
        ("Statute of Limitations", "Continuing violation doctrine: each day of parental deprivation = new independent injury. Clock runs from last act not first. 3-year SOL under MCL 600.5805(2) per Wilson v Garcia, 471 U.S. 261 (1985).", "F04"),
    ]

    cursor = conn.cursor()
    inserted = 0
    for defense, workaround, filing_refs in workarounds:
        quote = f"[DEFENSE WORKAROUND] {defense}: {workaround}"
        cursor.execute("""
            INSERT INTO evidence_quotes (source_file, quote_text, page_number, category, lane, relevance_score, filing_refs, tags, is_duplicate, duplicate_of)
            SELECT ?, ?, 1, 'defense_workaround', 'C', 10.0, ?, 'federal,defense,workaround,verified', 0, NULL
            WHERE NOT EXISTS (SELECT 1 FROM evidence_quotes WHERE quote_text LIKE ?)
        """, ("Federal_Civil_Rights_Citation_Index_VERIFIED.pdf", quote, filing_refs, f"%{defense}%"))
        inserted += cursor.rowcount

    conn.commit()
    return inserted

def persist_mcr_timing_rules(conn):
    """Persist MCR timing rules from the court rules harvest."""
    rules = [
        ("MCR 2.119(C)", "Motion Practice Timing", "RULE", "Motion service: mail 9 days, delivery/e-service 7 days before hearing. Response: mail 5 days, e-service 3 days before hearing. Filing: motion 7 days, response 3 days before hearing.", "motion_timing"),
        ("MCR 2.116(G)", "Summary Disposition Override", "RULE", "Summary disposition overrides 2.119(C): Motion service 21 days before hearing. Response 7 days before hearing. Reply brief 4 days before hearing, 5-page limit.", "summary_disposition"),
        ("MCR 1.108", "Computation of Time", "RULE", "Mail adds 3 days to any deadline. E-service/delivery adds 0 days. Excludes intermediate Saturdays, Sundays, legal holidays when period is less than 7 days.", "deadline_computation"),
        ("MCR 1.109(D)", "Filing Standards", "RULE", "Document format: 8.5x11 inches, 12-13pt font minimum, 10pt footnotes minimum. MiFILE: PDF text-searchable preferred, 25MB per file limit, attachments indexed on last page.", "filing_standards"),
        ("MCR 7.204(A)", "Claim of Appeal Deadline", "RULE", "21 days from entry of judgment or order. JURISDICTIONAL — cannot be extended. Transcript order within 14 days of filing claim. Reporter has 56 days.", "appellate_deadline"),
        ("MCR 3.210(D)", "Parenting Time Restrictions", "RULE", "Restrictions on parenting time require clear and convincing evidence findings under MCR 2.517. Court must make specific findings of fact.", "parenting_time"),
    ]

    cursor = conn.cursor()
    inserted = 0
    for rule_cite, title, rule_type, text, category in rules:
        cursor.execute("""
            INSERT INTO michigan_rules_extracted (rule_number, title, rule_type, full_text, text_length, source_file, is_key_rule)
            SELECT ?, ?, ?, ?, ?, 'COURT_FILING_PACKETS/RULES harvest', 1
            WHERE NOT EXISTS (SELECT 1 FROM michigan_rules_extracted WHERE rule_number = ? AND full_text LIKE ?)
        """, (rule_cite, title, rule_type, text, len(text), rule_cite, f"%{text[:50]}%"))
        inserted += cursor.rowcount

    conn.commit()
    return inserted

def persist_top_authority_violations(conn):
    """Persist top MCR/MCL violation counts from court rules harvest."""
    violations = [
        ("MCL 722.27a", "Parenting Time", 1179, "35276", "A,D"),
        ("MCR 2.119", "Motion Practice", 945, "19460", "A,D,E"),
        ("MCR 3.207", "Domestic Relations Procedure", 922, "19066", "A"),
        ("MCL 600.2918", "Wrongful Eviction", 678, "5726", "B"),
        ("MCL 600.2950a", "PPO Nondomestic/Stalking", 672, "10777", "D"),
        ("MCR 3.705", "PPO Issuance", 672, "10777", "D"),
        ("MCR 2.003", "Disqualification of Judge", 559, "26834", "E"),
        ("MCR 3.707", "PPO Modification/Termination", 523, "8809", "D"),
        ("MCL 722.23", "Best Interest Factors", 342, "4900", "A"),
    ]

    cursor = conn.cursor()
    inserted = 0
    for authority, title, violation_count, severity_score, lane in violations:
        quote = f"[AUTHORITY VIOLATION STATS] {authority} ({title}): {violation_count} violations documented, severity score {severity_score}. Source: COURT_FILING_PACKETS/RULES/top_mcr_mcl_rules_CITES_PURE.csv"
        cursor.execute("""
            INSERT INTO evidence_quotes (source_file, quote_text, page_number, category, lane, relevance_score, filing_refs, tags, is_duplicate, duplicate_of)
            SELECT ?, ?, 1, 'authority_violation_stats', ?, 8.0, 'F01,F04,F05,F06', ?, 0, NULL
            WHERE NOT EXISTS (SELECT 1 FROM evidence_quotes WHERE quote_text LIKE ?)
        """, ("COURT_FILING_PACKETS/RULES/top_mcr_mcl_rules_CITES_PURE.csv", quote, lane,
              f"authority,violation,stats,{authority.lower().replace(' ', '_')}",
              f"%{authority}%{violation_count} violations%"))
        inserted += cursor.rowcount

    conn.commit()
    return inserted

def main():
    conn = get_conn()
    total = 0

    print("=== PERSISTING FEDERAL CITATION INDEX + RULES HARVEST ===\n")

    n = persist_federal_case_law(conn)
    print(f"[1] Federal case law + authority chains: {n} rows")
    total += n

    n = persist_federal_statutes(conn)
    print(f"[2] Federal statutes: {n} rows")
    total += n

    n = persist_defense_workarounds(conn)
    print(f"[3] Defense workarounds: {n} rows")
    total += n

    n = persist_mcr_timing_rules(conn)
    print(f"[4] MCR timing rules: {n} rows")
    total += n

    n = persist_top_authority_violations(conn)
    print(f"[5] Top authority violations: {n} rows")
    total += n

    # Verify totals
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM evidence_quotes")
    eq = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM authority_chains_v2")
    ac = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM michigan_rules_extracted")
    mr = cur.fetchone()[0]

    print(f"\n=== TOTAL PERSISTED: {total} rows ===")
    print(f"evidence_quotes: {eq}")
    print(f"authority_chains_v2: {ac}")
    print(f"michigan_rules_extracted: {mr}")

    conn.close()

if __name__ == "__main__":
    main()
