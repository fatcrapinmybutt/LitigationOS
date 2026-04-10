"""Persist MD harvest intelligence from COURT_FILING_PACKETS/MD/ into litigation_context.db.
Findings from 56 markdown files (~36MB) harvested by explore agents.
Rule 22: All Python at D:\LitigationOS_tmp\
"""
import sqlite3
import datetime

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"

# Verified findings from MD harvest — 56 files analyzed
HARVEST_ROWS = [
    # JTC Complaint findings
    ("COURT_FILING_PACKETS/MD/FORMAL_COMPLAINT_JUDICIAL_TENURE_COMMISSION.md",
     "jtc_complaint", "JTC complaint documents 7 grounds, 47 incidents over 32 months against McNeill",
     "CRITICAL", "E", "McNeill", "FORMAL_COMPLAINT_JUDICIAL_TENURE_COMMISSION.md",
     "MCJC Canon 1,2,3; MCR 2.003", "F06_JTC"),
    
    # Disqualification Motion
    ("COURT_FILING_PACKETS/MD/Motion_for_Disqualification_Judge_McNeill.md",
     "disqualification", "5 documented bias patterns meeting MCL 600.1521 standard for disqualification",
     "CRITICAL", "E", "McNeill", "Motion_for_Disqualification_Judge_McNeill.md",
     "MCR 2.003; MCL 600.1521", "F03_DISQUALIFICATION"),
    
    # Ex Parte Violations Detail
    ("COURT_FILING_PACKETS/MD/EX_PARTE_HEARING_VIOLATIONS_DETAILED.md",
     "ex_parte_violations", "7 major violations from Aug 5-11 2025: judge admitted 'Yes I had my staff listen to it'; MCL 750.539 wiretapping by Emily",
     "CRITICAL", "E", "McNeill,Emily Watson", "EX_PARTE_HEARING_VIOLATIONS_DETAILED.md",
     "MCR 2.003; MCL 750.539; MCJC Canon 3A(6)", "F06_JTC,F01_MSC"),
    
    # Appellate Brief Violations
    ("COURT_FILING_PACKETS/MD/APPELLATE_BRIEF_DOCUMENTED_VIOLATIONS.md",
     "appellate_violations", "10 legal violations establishing abuse of discretion with standard of review for each",
     "CRITICAL", "F", "McNeill", "APPELLATE_BRIEF_DOCUMENTED_VIOLATIONS.md",
     "MCR 7.212; MCR 2.003; MCL 722.23", "F09_COA"),
    
    # Emergency Motion
    ("COURT_FILING_PACKETS/MD/EMERGENCY MOTION TO RESTORE PARENTING TIME.md",
     "emergency_motion", "4-part emergency relief test all satisfied: irreparable harm, likelihood of success, balance of hardships, public interest",
     "CRITICAL", "A", "McNeill,Emily Watson", "EMERGENCY MOTION TO RESTORE PARENTING TIME.md",
     "MCR 3.207; MCL 722.27a; Troxel v Granville", "F10_COA_EMERGENCY"),
    
    # Supplemental JTC
    ("COURT_FILING_PACKETS/MD/SUPPLEMENTAL_JTC_COMPLAINT_EX_PARTE_VIOLATIONS.md",
     "supplemental_jtc", "7 additional specific ex parte violations beyond initial JTC complaint",
     "CRITICAL", "E", "McNeill", "SUPPLEMENTAL_JTC_COMPLAINT_EX_PARTE_VIOLATIONS.md",
     "MCJC Canon 3A(4)(6); MCR 2.003", "F06_JTC"),
    
    # Judicial Misconduct Timeline
    ("COURT_FILING_PACKETS/MD/JUDICIAL_MISCONDUCT_TIMELINE.md",
     "misconduct_timeline", "47 incidents distributed across 7 violation grounds over 32 months Oct 2023-present",
     "CRITICAL", "E", "McNeill", "JUDICIAL_MISCONDUCT_TIMELINE.md",
     "MCJC Canon 1-3; MCR 2.003", "F06_JTC,F01_MSC"),
    
    # Comprehensive Legal Analysis
    ("COURT_FILING_PACKETS/MD/COMPREHENSIVE_LEGAL_ANALYSIS_Pigors_v_Watson.md",
     "comprehensive_analysis", "755 documents analyzed: multi-lane synthesis covering custody, PPO, housing, judicial misconduct, federal civil rights",
     "CRITICAL", "ALL", "ALL", "COMPREHENSIVE_LEGAL_ANALYSIS_Pigors_v_Watson.md",
     "Multiple", "ALL"),
    
    # $250 Sanction Fee — NEW
    ("COURT_FILING_PACKETS/MD/",
     "sanction_violation", "Judge imposed $250 sanction fee without vexatious litigant finding — MCR 1.109(E) violation",
     "CRITICAL", "E", "McNeill", "Multiple MD sources",
     "MCR 1.109(E); In re Contempt of Dudzinski", "F06_JTC,F01_MSC"),
    
    # Stigmatizing Language — NEW
    ("COURT_FILING_PACKETS/MD/",
     "stigmatizing_language", "Judge called Father 'crazy' and 'liar' in judicial orders — violates MCJC Canon 2A (dignity of judicial office)",
     "CRITICAL", "E", "McNeill", "Multiple MD sources",
     "MCJC Canon 2A; Canon 3A(3)", "F06_JTC"),
    
    # Secret Second Eval — NEW
    ("COURT_FILING_PACKETS/MD/",
     "secret_evaluation", "Judge obtained undisclosed second HealthWest evaluation Father never completed or saw — violates due process and MRE 901",
     "CRITICAL", "E", "McNeill", "Multiple MD sources",
     "US Const Amend XIV; MRE 901; Mathews v Eldridge", "F01_MSC,F04_FEDERAL"),
    
    # Email to Secretary — NEW
    ("COURT_FILING_PACKETS/MD/",
     "improper_routing", "Judge directed Father to email HealthWest evaluation to her secretary instead of filing with clerk — violates open court principle",
     "HIGH", "E", "McNeill", "EX_PARTE_HEARING_VIOLATIONS_DETAILED.md",
     "MCR 8.119; MI Const art 1 sec 14", "F06_JTC"),
    
    # USB Recording Chain
    ("COURT_FILING_PACKETS/MD/EX_PARTE_HEARING_VIOLATIONS_DETAILED.md",
     "recording_chain", "USB submitted directly to clerk not served on Father first; judge admitted staff listened to it ex parte",
     "HIGH", "E", "McNeill,Emily Watson", "EX_PARTE_HEARING_VIOLATIONS_DETAILED.md",
     "MCR 2.107; MCJC Canon 3A(4)", "F06_JTC,F01_MSC"),
    
    # Service Pattern
    ("COURT_FILING_PACKETS/MD/",
     "service_pattern", "4 documented instances of inadequate service establishing pattern not isolated incident",
     "HIGH", "E", "McNeill,Emily Watson", "Multiple MD sources",
     "MCR 2.107; MCR 2.105", "F01_MSC,F09_COA"),
    
    # Pre-Litigation Baseline
    ("COURT_FILING_PACKETS/MD/",
     "pre_litigation_baseline", "Pre-litigation Father was consistent primary caregiver with no abuse history and no CPS findings — establishes baseline destroyed by judicial misconduct",
     "HIGH", "A", "Andrew Pigors", "COMPREHENSIVE_LEGAL_ANALYSIS_Pigors_v_Watson.md",
     "MCL 722.23; MCL 722.27(1)(c)", "F05_MSC,F09_COA"),
    
    # Emily Wiretapping Argument
    ("COURT_FILING_PACKETS/MD/EX_PARTE_HEARING_VIOLATIONS_DETAILED.md",
     "wiretapping_issue", "Emily's recording potentially violates MCL 750.539 if she was not participant in recorded conversation; Sullivan v Gray one-party consent requires PARTICIPANT status",
     "HIGH", "D", "Emily Watson", "EX_PARTE_HEARING_VIOLATIONS_DETAILED.md",
     "MCL 750.539c; Sullivan v Gray 117 Mich App 476 (1982)", "F08_PPO"),
    
    # Bias Pattern Summary
    ("COURT_FILING_PACKETS/MD/Motion_for_Disqualification_Judge_McNeill.md",
     "bias_patterns", "5 systematic bias patterns: (1) evidence exclusion favoring Emily, (2) ex parte communications, (3) disproportionate sanctions, (4) denial of hearing rights, (5) personal/professional conflicts of interest",
     "HIGH", "E", "McNeill", "Motion_for_Disqualification_Judge_McNeill.md",
     "MCR 2.003(C)(1); MCJC Canon 3", "F03_DISQUALIFICATION"),
    
    # 10 Appellate Violations Detail
    ("COURT_FILING_PACKETS/MD/APPELLATE_BRIEF_DOCUMENTED_VIOLATIONS.md",
     "appellate_10_violations", "10 specific violations: (1) improper burden shifting, (2) excluding favorable evidence, (3) one-sided fact finding, (4) ignoring statutory factors, (5) ex parte communications, (6) disproportionate contempt, (7) due process denial, (8) conflict of interest, (9) improper PPO scope, (10) retaliatory filing restrictions",
     "HIGH", "F", "McNeill", "APPELLATE_BRIEF_DOCUMENTED_VIOLATIONS.md",
     "MCR 7.212; MCL 722.23; US Const Amend XIV", "F09_COA"),
    
    # Medication Coercion (from MD files)
    ("COURT_FILING_PACKETS/MD/",
     "medication_coercion_md", "MD files confirm: judge and Emily discussed on record that prescription medication is 'only way' Father could see child — constitutes unlawful practice of medicine and coercive conditioning of parental rights",
     "CRITICAL", "E", "McNeill,Emily Watson", "Multiple MD sources",
     "MCL 333.16215; US Const Amend XIV; Troxel v Granville", "F01_MSC,F04_FEDERAL"),
    
    # Filing Ban (from MD files)
    ("COURT_FILING_PACKETS/MD/",
     "filing_ban_md", "MD files confirm verbatim: judge stated 'Do not file anymore, I will not look at it' — direct denial of access to courts violating First Amendment and MI Const art 1 sec 13",
     "CRITICAL", "E", "McNeill", "Multiple MD sources",
     "US Const Amend I; MI Const art 1 sec 13; Boddie v Connecticut", "F01_MSC,F04_FEDERAL"),
]

# New judicial_violations entries from MD harvest (not already in DB)
JUDICIAL_VIOLATIONS = [
    ("sanction_violation", "Imposed $250 sanction fee without vexatious litigant finding required by MCR 1.109(E)", 
     None, "MCR 1.109(E)", "Canon 2A", "COURT_FILING_PACKETS/MD/", 
     "Judge imposed $250 sanction without following MCR 1.109(E) procedures", 9, "E"),
    
    ("stigmatizing_language", "Called Father 'crazy' and 'liar' in judicial orders — violates dignity of judicial office",
     None, "MCJC Canon 2A", "Canon 2A", "COURT_FILING_PACKETS/MD/",
     "Judge used stigmatizing language 'crazy' and 'liar' about Father in written orders", 8, "E"),
    
    ("secret_evaluation", "Obtained undisclosed second HealthWest evaluation that Father never completed or saw",
     None, "MRE 901; US Const Amend XIV", "Canon 3A(4)", "COURT_FILING_PACKETS/MD/",
     "Judge obtained secret second evaluation without Fathers knowledge — due process violation", 9, "E"),
    
    ("improper_document_routing", "Directed Father to email HealthWest evaluation to her secretary instead of filing with clerk",
     None, "MCR 8.119", "Canon 3A(4)", "COURT_FILING_PACKETS/MD/",
     "Judge bypassed clerk filing system by directing document to her personal secretary", 8, "E"),
    
    ("ex_parte_usb_listening", "Admitted on record: 'Yes, I had my staff listen to it' regarding USB recording submitted ex parte",
     "2025-08-08", "MCR 2.003; MCJC Canon 3A(4)", "Canon 3A(4)(6)", "EX_PARTE_HEARING_VIOLATIONS_DETAILED.md",
     "Judge admitted staff listened to USB recording ex parte — Canon 3A(4) direct violation", 10, "E"),
]

def main():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    
    # Verify harvest_intelligence schema
    cols = {r[1] for r in conn.execute("PRAGMA table_info(harvest_intelligence)")}
    print(f"harvest_intelligence columns: {sorted(cols)}")
    
    # Verify judicial_violations schema  
    jv_cols = {r[1] for r in conn.execute("PRAGMA table_info(judicial_violations)")}
    print(f"judicial_violations columns: {sorted(jv_cols)}")
    
    # Current counts
    hi_count = conn.execute("SELECT COUNT(*) FROM harvest_intelligence").fetchone()[0]
    jv_count = conn.execute("SELECT COUNT(*) FROM judicial_violations").fetchone()[0]
    print(f"\nBefore: harvest_intelligence={hi_count}, judicial_violations={jv_count}")
    
    # Insert harvest_intelligence rows
    hi_inserted = 0
    for row in HARVEST_ROWS:
        source, category, finding, severity, lane, actors, evidence_refs, legal_authority, filing_use = row
        # Check for duplicates by category + finding substring
        existing = conn.execute(
            "SELECT COUNT(*) FROM harvest_intelligence WHERE category = ? AND finding LIKE ?",
            (category, finding[:80] + '%')
        ).fetchone()[0]
        if existing == 0:
            conn.execute("""
                INSERT INTO harvest_intelligence 
                (source, category, finding, severity, lane, actors, evidence_refs, legal_authority, filing_use, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (source, category, finding, severity, lane, actors, evidence_refs, legal_authority, filing_use,
                  datetime.datetime.now().isoformat()))
            hi_inserted += 1
        else:
            print(f"  SKIP (dup): {category}")
    
    # Insert judicial_violations rows
    jv_inserted = 0
    for row in JUDICIAL_VIOLATIONS:
        vtype, desc, date_occ, mcr, canon, src_file, src_quote, severity, lane = row
        # Check for duplicates
        existing = conn.execute(
            "SELECT COUNT(*) FROM judicial_violations WHERE violation_type = ? AND description LIKE ?",
            (vtype, desc[:60] + '%')
        ).fetchone()[0]
        if existing == 0:
            conn.execute("""
                INSERT INTO judicial_violations 
                (violation_type, description, date_occurred, mcr_rule, canon, source_file, source_quote, severity, lane, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (vtype, desc, date_occ, mcr, canon, src_file, src_quote, severity, lane,
                  datetime.datetime.now().isoformat()))
            jv_inserted += 1
        else:
            print(f"  SKIP (dup): {vtype}")
    
    conn.commit()
    
    # Verify
    hi_after = conn.execute("SELECT COUNT(*) FROM harvest_intelligence").fetchone()[0]
    jv_after = conn.execute("SELECT COUNT(*) FROM judicial_violations").fetchone()[0]
    
    print(f"\nAfter: harvest_intelligence={hi_after} (+{hi_after - hi_count}), judicial_violations={jv_after} (+{jv_after - jv_count})")
    print(f"Inserted: {hi_inserted} harvest rows, {jv_inserted} judicial violation rows")
    
    # Show CRITICAL findings count
    crit = conn.execute("SELECT COUNT(*) FROM harvest_intelligence WHERE severity='CRITICAL'").fetchone()[0]
    print(f"Total CRITICAL findings: {crit}")
    
    conn.close()
    print("\nDONE — MD harvest persisted to litigation_context.db")

if __name__ == "__main__":
    main()
