"""Persist intelligence from MD batch3 + numbered subdirs harvest agents.
Sources: WITNESS_LISTS, SETTLEMENT_DEMAND, MOTIONS_IN_LIMINE, DEPOSITION_NOTICES,
FEDERAL_INITIAL_DISCLOSURES, TRIAL_BRIEF_CUSTODY, MASTER_CHRONOLOGICAL_TIMELINE,
CRIMINAL_DEFENSE_PREP, parenting time docs, PDF_READY inventory.
"""
import sqlite3, os, datetime

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"

def get_conn():
    conn = sqlite3.connect(DB, timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    return conn

def count_before_after(conn, table, label):
    before = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    return before, label

def persist_witness_intelligence(conn):
    """Key witnesses from WITNESS_LISTS_ALL_CASES.md (54.4 KB)"""
    witnesses = [
        # Lane A - Custody
        ("Andrew J. Pigors", "Plaintiff/Father - 3-4 hrs direct, 1-2 hrs cross. Topics: parental bond, denied parenting time, interference incidents, 59 days incarceration, jobs lost, false allegations, PPO abuse, ex parte orders, all 12 MCL 722.23 factors", "A", "witness_testimony"),
        ("Emily A. Watson", "Defendant/Mother - Topics: false allegations timeline, recantation Oct 13 2023, PPO filing Oct 15 2023, meth admission to Officer Randall, Albert Watson premeditation NS2505044, Instagram family portrait alienation", "A", "witness_testimony"),
        ("Albert Watson", "Adverse witness - Topics: NS2505044 premeditation admission, kitchen audio/video recording, attended EVERY custody exchange after McNeill said keep family out, intimidation pattern", "A", "witness_testimony"),
        ("Lori Watson", "Adverse witness - Topics: Kent County background, involvement in custody dispute, corroboration of Albert's conduct at exchanges", "A", "witness_testimony"),
        ("HealthWest Clinician", "Expert/fact witness - Topics: Court-ordered evaluation, Father deemed fit parent, LOCUS Score 12 Level One, Psychosis=0 Substance=0 Danger=0, evaluation excluded by McNeill, Rusco contact Oct 29 2025", "A", "witness_testimony"),
        ("Officer Ella Randall", "NSPD officer - Topics: Emily admitted meth use, welfare check reports, all contacts cleared Andrew, zero arrests across all contacts", "A", "witness_testimony"),
        # Lane D - PPO
        ("Ronald Berry", "NON-ATTORNEY providing legal assistance to Emily. Lives at 2160 Garland Dr with Emily. Related to Cavan Berry (McNeill spouse). Coordinated ex parte communications.", "D", "witness_testimony"),
        # Lane E - Judicial
        ("Pamela Rusco", "FOC officer - Topics: systemic bias toward Emily, HealthWest clinician contact Oct 29 2025, 990 Terrace St nexus, recommendation patterns favoring Emily despite evidence", "E", "witness_testimony"),
        # Lane B - Housing
        ("Shady Oaks witnesses", "Housing witnesses - Topics: coerced lease modification $325 to $695/month, property condition complaints, MHP LLC dissolution, lockout events, utility shutoffs", "B", "witness_testimony"),
    ]
    rows = [(f"COURT_FILING_PACKETS/WITNESS_LISTS_ALL_CASES.md", w[0] + ": " + w[1], None, w[3], w[2], 0.95, None, "witness_intelligence", datetime.datetime.now().isoformat(), 0, None) for w in witnesses]
    conn.executemany("INSERT INTO evidence_quotes (source_file, quote_text, page_number, category, lane, relevance_score, filing_refs, tags, created_at, is_duplicate, duplicate_of) VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows)
    return len(rows)

def persist_settlement_demands(conn):
    """Damages from SETTLEMENT_DEMAND_ANALYSIS.md - $3.4M-$22.9M total"""
    demands = [
        ("Lane A Custody: Loss of parental relationship (569+ days) $100K-$500K, Emotional distress $50K-$250K, Lost wages (3 jobs, 59 days jailed) $75K-$150K, Child support paid during denial $15K-$30K. Authority: Bowie v Arder 441 Mich 23 (1992), Roberts v Auto-Owners 422 Mich 594 (1985)", "A", "damages_quantification"),
        ("Lane B Housing: Property destruction $25K-$75K, Constructive eviction $10K-$30K, Utility shutoff damages $5K-$15K, Title interference $20K-$60K, Treble damages under MCL 600.2919a. Total Lane B: $60K-$180K (pre-treble) to $180K-$540K (trebled)", "B", "damages_quantification"),
        ("Lane D PPO: Wrongful PPO continuation $25K-$75K, Contempt abuse (59 days) $50K-$200K, 1st Amendment violation (birthday messages) $25K-$100K. Total Lane D: $100K-$375K", "D", "damages_quantification"),
        ("Lane E Judicial: Due process violations $100K-$500K, Ex parte order pattern (24 of 55 = 44%) $50K-$250K, Evidence exclusion $25K-$100K. Total Lane E: $175K-$850K", "E", "damages_quantification"),
        ("Federal 1983: Compensatory across all lanes $620K-$2.48M, Punitive multiplier (2x-5x) $1.24M-$12.4M, Attorney fees waived (pro se) but out-of-pocket costs recoverable under 42 USC 1988. Total: $3.4M-$22.9M", "C", "damages_quantification"),
    ]
    rows = [(f"COURT_FILING_PACKETS/SETTLEMENT_DEMAND_ANALYSIS.md", d[0], None, d[2], d[1], 0.9, None, "damages_settlement", datetime.datetime.now().isoformat(), 0, None) for d in demands]
    conn.executemany("INSERT INTO evidence_quotes (source_file, quote_text, page_number, category, lane, relevance_score, filing_refs, tags, created_at, is_duplicate, duplicate_of) VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows)
    return len(rows)

def persist_motions_in_limine(conn):
    """Pre-trial motion strategies from MOTIONS_IN_LIMINE_ALL_CASES.md"""
    motions = [
        ("MIL No.1: EXCLUDE Incarceration as Evidence of Unfitness. Legal Theory: MRE 404(b), MRE 403, People v Starr 457 Mich 490 (1998). Civil contempt not criminal; probative value substantially outweighed by unfair prejudice.", "A"),
        ("MIL No.2: EXCLUDE Unsubstantiated Abuse Allegations. Legal Theory: MRE 403, MRE 802. No police charges, no CPS findings, all welfare checks cleared Andrew. Prejudice outweighs probative value.", "A"),
        ("MIL No.3: EXCLUDE Emily's Hearsay Statements About Andrew's Mental State. Legal Theory: MRE 802, MRE 701, MRE 702. Emily has no medical training to diagnose. Lay opinion on mental state inadmissible.", "A"),
        ("MIL No.4: ADMIT HealthWest Evaluation. Legal Theory: MRE 803(4) medical records exception, MRE 702-703. Court-ordered eval excluded by McNeill despite Father deemed fit. LOCUS 12, all scores zero.", "A"),
        ("MIL No.5: ADMIT Kitchen Audio/Video Recording. Sullivan v Gray 117 Mich App 476 (1982) one-party consent. MCL 750.539c. Albert Watson premeditation and intimidation captured.", "A"),
        ("MIL No.6: EXCLUDE PPO as Evidence of DV. PPO filed 2 days after Emily recanted to police. No finding of actual violence. Fraudulent basis undermines probative value. MRE 403.", "D"),
    ]
    rows = [(f"COURT_FILING_PACKETS/MOTIONS_IN_LIMINE_ALL_CASES.md", m[0], None, "motion_strategy", m[1], 0.95, None, "motions_in_limine", datetime.datetime.now().isoformat(), 0, None) for m in motions]
    conn.executemany("INSERT INTO evidence_quotes (source_file, quote_text, page_number, category, lane, relevance_score, filing_refs, tags, created_at, is_duplicate, duplicate_of) VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows)
    return len(rows)

def persist_deposition_targets(conn):
    """Deposition strategy from DEPOSITION_NOTICES.md (31.3 KB)"""
    targets = [
        ("Deposition Target: Emily A. Watson. Topics: background, false allegations timeline, Oct 13 2023 recantation to police, Oct 15 PPO filing, Albert Watson premeditation, ex parte communications with judge, meth admission, parenting interference, Instagram family portrait. Authority: MCR 2.306 (Depositions Upon Oral Examination), MCR 2.306(B)(1) 7+ days notice minimum.", "A"),
        ("Deposition Target: Pamela Rusco (FOC). Topics: HealthWest clinician contact Oct 29 2025, recommendation methodology, 990 Terrace St office sharing with Cavan Berry, bias indicators, Emily Watson access to FOC. Authority: MCR 2.306.", "E"),
        ("Deposition Target: Albert Watson. Topics: NS2505044 premeditation admission to police Aug 7 2025, kitchen recording Nov 2023, attendance at EVERY custody exchange after McNeill verbal order to keep family out, intimidation pattern. Authority: MCR 2.306.", "A"),
        ("Deposition Target: HealthWest Clinician. Topics: evaluation methodology, LOCUS 12 scoring, Rusco contact, how evaluation was routed to secretary, why excluded from record. Authority: MCR 2.306, MRE 702-703.", "E"),
    ]
    rows = [(f"COURT_FILING_PACKETS/DEPOSITION_NOTICES.md", t[0], None, "deposition_strategy", t[1], 0.9, None, "deposition_targets", datetime.datetime.now().isoformat(), 0, None) for t in targets]
    conn.executemany("INSERT INTO evidence_quotes (source_file, quote_text, page_number, category, lane, relevance_score, filing_refs, tags, created_at, is_duplicate, duplicate_of) VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows)
    return len(rows)

def persist_criminal_defense_intel(conn):
    """Criminal defense prep from CRIMINAL_DEFENSE_PREP directory"""
    intel = [
        ("Criminal Case 2025-25245676SM, 60th District, Judge Kostrzewa. Defense preparation includes: incident report analysis, badge camera footage preservation request, inmate witness identification. CRITICAL GAPS: exact altercation date, full name/booking info for Jonathon Jones, second attacker identity, GD member from breakfast tray incident, incident report numbers, badge camera preservation status.", "CRIMINAL"),
        ("Criminal defense strategy: 100% SEPARATE from Lanes A-F. Key files: DEFENSE_PREPARATION_2025-25245676SM.md (31 KB), ATTORNEY_MEETING_PLAYBOOK.md (10.72 KB). Format marked CONFIDENTIAL - ATTORNEY-CLIENT MEETING PREPARATION.", "CRIMINAL"),
    ]
    rows = [(f"COURT_FILING_PACKETS/CRIMINAL_DEFENSE_PREP/", i[0], None, "criminal_defense", i[1], 0.85, None, "criminal_defense", datetime.datetime.now().isoformat(), 0, None) for i in intel]
    conn.executemany("INSERT INTO evidence_quotes (source_file, quote_text, page_number, category, lane, relevance_score, filing_refs, tags, created_at, is_duplicate, duplicate_of) VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows)
    return len(rows)

def persist_authority_chains(conn):
    """New authority chains from motions in limine and settlement demand"""
    chains = [
        # Motions in limine authorities
        ("MRE 404(b)", "People v Starr 457 Mich 490 (1998)", "supports_exclusion", "COURT_FILING_PACKETS/MOTIONS_IN_LIMINE_ALL_CASES.md", "motion_in_limine", "A", "MRE 404(b) character evidence exclusion for incarceration evidence"),
        ("MRE 403", "People v Starr 457 Mich 490 (1998)", "unfair_prejudice", "COURT_FILING_PACKETS/MOTIONS_IN_LIMINE_ALL_CASES.md", "motion_in_limine", "A", "Probative value substantially outweighed by unfair prejudice"),
        ("Sullivan v Gray 117 Mich App 476 (1982)", "MCL 750.539c", "one_party_consent", "COURT_FILING_PACKETS/MOTIONS_IN_LIMINE_ALL_CASES.md", "motion_in_limine", "A", "One-party recording consent - Albert Watson kitchen audio/video"),
        ("MRE 803(4)", "HealthWest Evaluation", "medical_records_exception", "COURT_FILING_PACKETS/MOTIONS_IN_LIMINE_ALL_CASES.md", "motion_in_limine", "A", "Medical records hearsay exception for court-ordered HealthWest eval"),
        # Settlement demand authorities
        ("Bowie v Arder 441 Mich 23 (1992)", "Parental relationship damages", "damages_authority", "COURT_FILING_PACKETS/SETTLEMENT_DEMAND_ANALYSIS.md", "settlement", "A", "Loss of parental relationship damages $100K-$500K"),
        ("Roberts v Auto-Owners 422 Mich 594 (1985)", "Emotional distress damages", "damages_authority", "COURT_FILING_PACKETS/SETTLEMENT_DEMAND_ANALYSIS.md", "settlement", "A", "Emotional distress damages for parent $50K-$250K"),
        ("MCL 600.2919a", "Treble damages housing", "statutory_multiplier", "COURT_FILING_PACKETS/SETTLEMENT_DEMAND_ANALYSIS.md", "settlement", "B", "Treble damages for housing violations - $60K-$180K to $180K-$540K"),
        ("42 USC 1988", "Attorney fees/costs", "fee_shifting", "COURT_FILING_PACKETS/SETTLEMENT_DEMAND_ANALYSIS.md", "settlement", "C", "Pro se cannot claim attorney fees but can claim out-of-pocket costs"),
    ]
    rows = [(c[0], c[1], c[2], c[3], c[4], c[5], c[6]) for c in chains]
    conn.executemany("INSERT INTO authority_chains_v2 (primary_citation, supporting_citation, relationship, source_document, source_type, lane, paragraph_context) VALUES (?,?,?,?,?,?,?)", rows)
    return len(rows)

def persist_parenting_time_evidence(conn):
    """Parenting time documentation from numbered subdirs"""
    pt_evidence = [
        ("Parenting Time Weeks 7-11, 7-15, 7-25, 7-29 (2025): 16 files documenting parenting time logs during final weeks before complete denial. Last contact July 29, 2025. These logs are critical evidence of Andrew's active parenting and Emily's escalating interference in the weeks leading to total suspension.", "A", "parenting_time_logs"),
        ("PDF_READY directory: 52 court-ready PDF documents across all filing lanes. Organized filing archive spanning 01_CIRCUIT, 02_COA, 03_JTC, 04_MSC, 05_USDC plus docx_extract, HTML, and formatted outputs.", "A", "filing_inventory"),
        ("Filing directory structure: 15 major directories containing ~1,200+ files totaling ~1 GB. Courts covered: 14th Circuit, Court of Appeals, JTC, MSC, USDC WDMI. All pro se filings by Andrew J. Pigors.", "A", "filing_inventory"),
    ]
    rows = [(f"COURT_FILING_PACKETS/", p[0], None, p[2], p[1], 0.85, None, "parenting_time", datetime.datetime.now().isoformat(), 0, None) for p in pt_evidence]
    conn.executemany("INSERT INTO evidence_quotes (source_file, quote_text, page_number, category, lane, relevance_score, filing_refs, tags, created_at, is_duplicate, duplicate_of) VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows)
    return len(rows)

def persist_impeachment_from_witnesses(conn):
    """Impeachment entries from witness list intelligence"""
    # Check schema first
    cols = {r[1] for r in conn.execute("PRAGMA table_info(impeachment_matrix)").fetchall()}
    imp_data = [
        ("parental_alienation", "Emily posted Instagram family portrait with L.D.W., her other son, and Ronald Berry - deliberate father replacement imagery. Combined with 569+ days denial of parenting time.", "COURT_FILING_PACKETS/WITNESS_LISTS_ALL_CASES.md", "Father told L.D.W. is part of new family unit. Instagram evidence of deliberate alienation.", 9, "Did Emily post a family portrait on Instagram featuring Ronald Berry, her other son, and L.D.W. - without Andrew?", "F01,F04,F05,F09", None),
        ("premeditation", "Albert Watson attended EVERY custody exchange after McNeill verbally ordered to keep family out of it. Direct defiance of judicial instruction, documented in transcripts.", "COURT_FILING_PACKETS/WITNESS_LISTS_ALL_CASES.md", "Albert Watson defied McNeill verbal order to keep family out, attending every exchange as intimidation.", 8, "Did Albert Watson attend custody exchanges after the judge instructed the parties to keep family members out?", "F01,F04,F05", None),
        ("false_allegations", "Emily made 5 escalating false allegations: suicidal, arsenic poisoning, physical assault, drug use, threats. ALL cleared by police/medical. Zero arrests, zero charges, zero CPS findings.", "COURT_FILING_PACKETS/WITNESS_LISTS_ALL_CASES.md", "Systematic pattern of escalating fabricated allegations, each debunked by authorities.", 10, "How many of Emily Watson's allegations against Andrew resulted in criminal charges or CPS findings?", "F01,F04,F05,F06,F09", None),
    ]
    rows = [(d[0], d[1], d[2], d[3], d[4], d[5], d[6], d[7]) for d in imp_data]
    conn.executemany("INSERT INTO impeachment_matrix (category, evidence_summary, source_file, quote_text, impeachment_value, cross_exam_question, filing_relevance, event_date) VALUES (?,?,?,?,?,?,?,?)", rows)
    return len(rows)

def main():
    conn = get_conn()
    now = datetime.datetime.now().isoformat()
    print(f"=== Wave 3 Persistence: {now} ===\n")

    # Get baseline counts
    tables = ["evidence_quotes", "authority_chains_v2", "impeachment_matrix"]
    baselines = {}
    for t in tables:
        baselines[t] = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t} baseline: {baselines[t]:,}")

    print()

    # Execute all persistence functions
    funcs = [
        ("Witness Intelligence", persist_witness_intelligence),
        ("Settlement Demands", persist_settlement_demands),
        ("Motions in Limine", persist_motions_in_limine),
        ("Deposition Targets", persist_deposition_targets),
        ("Criminal Defense Intel", persist_criminal_defense_intel),
        ("Authority Chains", persist_authority_chains),
        ("Parenting Time Evidence", persist_parenting_time_evidence),
        ("Impeachment from Witnesses", persist_impeachment_from_witnesses),
    ]

    total_inserted = 0
    for name, func in funcs:
        try:
            count = func(conn)
            conn.commit()
            print(f"  ✅ {name}: {count} rows inserted")
            total_inserted += count
        except Exception as e:
            print(f"  ❌ {name}: {e}")
            conn.rollback()

    print(f"\n  TOTAL INSERTED: {total_inserted}")

    # Verify new counts
    print("\n=== POST-PERSISTENCE COUNTS ===")
    for t in tables:
        after = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        delta = after - baselines[t]
        print(f"  {t}: {after:,} (+{delta})")

    conn.close()
    print("\n✅ Wave 3 persistence complete!")

if __name__ == "__main__":
    main()
