"""Persist PDF_OUTPUT harvest intelligence to litigation_context.db"""
import sqlite3
from datetime import datetime

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
conn = sqlite3.connect(DB, timeout=60)
conn.execute("PRAGMA busy_timeout=60000")
conn.execute("PRAGMA journal_mode=WAL")

# Verify harvest_intelligence schema
cols = {r[1] for r in conn.execute("PRAGMA table_info(harvest_intelligence)")}
print(f"harvest_intelligence columns: {cols}")

# PDF_OUTPUT findings to persist
findings = [
    # Damages quantification
    ("PDF_OUTPUT/DAMAGES_QUANTIFICATION_COMPLETE.pdf", "damages", 
     "Total damages across all lanes: $3.4M-$22.9M. Lane A (Custody): $588K-$1.9M. Lane B (Housing): $1.05M-$7.08M with RICO treble. Lane D (PPO): included in A. Lane E (Judicial): included in Federal. Federal §1983: $1.2M-$7.5M.",
     "CRITICAL", "ALL", "Emily Watson,McNeill,Shady Oaks,Hoopes", 
     "DAMAGES_QUANTIFICATION_COMPLETE.pdf", "MCL 600.2919a,42 USC §1983,MCL 722.23", "F01,F02,F04,F05"),
    
    # Evidence claim matrix
    ("PDF_OUTPUT/EVIDENCE_CLAIM_MATRIX.pdf", "evidence_strength",
     "Evidence strength by lane: Lane A STRONG (8/12 factors strong), Lane B OVERWHELMING (19/22 counts strong), Lane D STRONG (5/5 claims), Lane E OVERWHELMING (6/7 categories strong), Lane F STRONG APPEAL (6/7 issues), Federal VIABLE (3/7 strong, 4/7 moderate).",
     "HIGH", "ALL", "Emily Watson,McNeill,Shady Oaks", 
     "EVIDENCE_CLAIM_MATRIX.pdf", "MCL 722.23,42 USC §3601", "F01,F02,F04,F05,F06,F09"),
    
    # Impeachment playbook
    ("PDF_OUTPUT/IMPEACHMENT_PLAYBOOK.pdf", "impeachment",
     "MRE 613 cross-examination scripts for: Emily Watson (false allegations pattern, recantation Oct 13 2023, meth admission), Albert Watson (NS2505044 premeditation, kitchen recording), McNeill (ex parte orders, contempt abuse, evidence exclusion), Berry connections, Kim Shady (ledger fraud). COMMIT-PIN-CONFRONT-EXHIBIT methodology.",
     "CRITICAL", "ALL", "Emily Watson,Albert Watson,McNeill,Ronald Berry,Kim Shady",
     "IMPEACHMENT_PLAYBOOK.pdf", "MRE 613,MRE 608,MRE 801(d)(1)(A)", "F01,F04,F05,F06,F09"),
    
    # Witness lists
    ("PDF_OUTPUT/WITNESS_LISTS_ALL_CASES.pdf", "witness_intelligence",
     "72-page comprehensive witness index across all 6 lanes. Includes: Andrew Pigors (plaintiff), Emily Watson, Albert Watson, Lori Watson, Ronald Berry, Cavan Berry, Judge McNeill, Pamela Rusco, Officer Randall, HealthWest clinicians, Shady Oaks management, FOC officers, neighbors, family members. Contact info, anticipated testimony, impeachment references for each.",
     "HIGH", "ALL", "Emily Watson,Albert Watson,Lori Watson,Ronald Berry,Cavan Berry,McNeill,Rusco",
     "WITNESS_LISTS_ALL_CASES.pdf", "MRE 601-615", "F01,F02,F04,F05,F06"),
    
    # Master filing calendar
    ("PDF_OUTPUT/MASTER_FILING_CALENDAR.pdf", "filing_strategy",
     "31-page filing wave strategy. Wave 0 (Emergency 7 days): Disqualification MCR 2.003, Contempt, Restore PT. Wave 1 (14 days): COA brief 366810, PPO termination, JTC. Wave 2 (30 days): Federal §1983, Housing. Wave 3 (45 days): MSC Superintending, AGC. Wave 4 (60 days): Full custody mod. Wave 6: Post-judgment. 213/285 todos DONE (74.7%).",
     "HIGH", "ALL", "Andrew Pigors",
     "MASTER_FILING_CALENDAR.pdf", "MCR 2.003,MCR 7.212,MCR 7.306,42 USC §1983", "F01,F04,F05,F06,F09,F10"),
    
    # Key statistics from master index
    ("PDF_OUTPUT/00_MASTER_INDEX.pdf", "key_statistics",
     "Critical stats from litigation war room: 24 ex parte orders (18.26% rate vs 5% norm = 3.65x abnormality), 569+ days denied parenting time, 59 days wrongful incarceration, 305 documented interference incidents, $1,056.60/month CS while denied ALL contact, 3 jobs lost from incarceration. NOTE: Some figures differ from our DB counts which are authoritative.",
     "HIGH", "ALL", "McNeill,Emily Watson",
     "00_MASTER_INDEX.pdf", "MCR 2.003,MCL 722.23(j)", "F01,F05,F06,F09"),
    
    # Trial briefs
    ("PDF_OUTPUT/TRIAL_BRIEF_CUSTODY.pdf", "legal_analysis",
     "7-page custody trial brief with IRAC structure for all 12 MCL 722.23 factors. Key argument: Factor (j) is DEVASTATING - 305 interference incidents + 569 days denied = systematic alienation. Factor (l) includes 59 days jailed, 3 jobs lost, judicial misconduct pattern. Recommended standard: clear and convincing evidence for ECE modification.",
     "HIGH", "A", "Emily Watson,McNeill",
     "TRIAL_BRIEF_CUSTODY.pdf", "MCL 722.23,MCL 722.27(1)(c),Vodvarka v Grasmeyer", "F05,F09"),
    
    ("PDF_OUTPUT/TRIAL_BRIEF_HOUSING.pdf", "legal_analysis",
     "10-page housing trial brief with 22 causes of action. Key evidence: 3 irreconcilable ledger versions (fraud), 74% tax undervaluation ($1.036M gap), utility shutoffs, property destruction. Corporate chain: Alden Global → Homes of America → Shady Oaks Park MHP LLC. Treble damages under MCL 600.2919a.",
     "HIGH", "B", "Shady Oaks,Homes of America,Alden Global",
     "TRIAL_BRIEF_HOUSING.pdf", "MCL 600.2919a,MCL 554.601,42 USC §3601", "F02,F04"),
    
    # Settlement demand analysis
    ("PDF_OUTPUT/SETTLEMENT_DEMAND_ANALYSIS.pdf", "settlement_strategy",
     "13-page settlement demand analysis across all lanes. Housing demand: $850K-$3.2M (pre-treble). Federal demand: $1.5M-$7.5M. Custody/judicial: non-monetary demands (recusal, restored PT, expungement). Strategy: file housing demand letter 30 days before federal complaint.",
     "MEDIUM", "ALL", "Shady Oaks,Emily Watson,McNeill",
     "SETTLEMENT_DEMAND_ANALYSIS.pdf", "MCL 600.2919a,42 USC §1983", "F02,F04"),
    
    # Subpoena templates  
    ("PDF_OUTPUT/SUBPOENA_TEMPLATES.pdf", "discovery_tools",
     "35-page subpoena templates covering: court records (14th Circuit docket, ex parte orders), police reports (NSPD all incidents), medical (HealthWest evaluation excluded by McNeill), financial (Shady Oaks ledgers, tax records), communications (Emily-Berry, Emily-Albert, Emily-Barnes), FOC records (Rusco contacts with HealthWest). Duces tecum and ad testificandum versions.",
     "MEDIUM", "ALL", "McNeill,Rusco,Emily Watson,Albert Watson,Shady Oaks",
     "SUBPOENA_TEMPLATES.pdf", "MCR 2.305,MCR 2.306", "F01,F02,F04,F05"),
    
    # Deposition notices
    ("PDF_OUTPUT/DEPOSITION_NOTICES.pdf", "discovery_tools",
     "28-page deposition notice package for: Emily Watson (custody, false allegations, alienation), Albert Watson (NS2505044, premeditation), Pamela Rusco (FOC bias, HealthWest contact), Officer Randall (Emily meth admission), McNeill (if recused - judicial misconduct), Ronald Berry (legal assistance, COA clerk role). Includes examination outlines.",
     "MEDIUM", "ALL", "Emily Watson,Albert Watson,Rusco,Officer Randall,Ronald Berry",
     "DEPOSITION_NOTICES.pdf", "MCR 2.306,MCR 2.307", "F01,F04,F05"),
    
    # Federal initial disclosures
    ("PDF_OUTPUT/FEDERAL_INITIAL_DISCLOSURES.pdf", "federal_procedure",
     "22-page FRCP 26(a)(1) initial disclosures package for federal §1983 action. Identifies: 20 defendants, 150+ witnesses, 500+ documents, damages computation. Includes: witness list with contact info, document index by category, insurance agreements, damages methodology.",
     "HIGH", "C", "All adversaries",
     "FEDERAL_INITIAL_DISCLOSURES.pdf", "FRCP 26(a)(1),42 USC §1983", "F04"),
    
    # Motions in limine
    ("PDF_OUTPUT/MOTIONS_IN_LIMINE_ALL_CASES.pdf", "trial_prep",
     "6-page motions in limine package: (1) Exclude Emily's unsubstantiated allegations per MRE 403/404, (2) Admit Sullivan v Gray recordings per MCL 750.539c, (3) Exclude character evidence not proper per MRE 404(a), (4) Admit HealthWest evaluation per MRE 702-703, (5) Judicial notice of ex parte order pattern per MRE 201.",
     "MEDIUM", "ALL", "Emily Watson,McNeill",
     "MOTIONS_IN_LIMINE_ALL_CASES.pdf", "MRE 403,MRE 404,MCL 750.539c,MRE 702,MRE 201", "F05,F09"),
]

inserted = 0
skipped = 0
for f in findings:
    source, category, finding, severity, lane, actors, evidence_refs, legal_authority, filing_use = f
    # Check for existing
    existing = conn.execute(
        "SELECT COUNT(*) FROM harvest_intelligence WHERE source=? AND category=?",
        (source, category)
    ).fetchone()[0]
    if existing > 0:
        skipped += 1
        continue
    conn.execute("""
        INSERT INTO harvest_intelligence (source, category, finding, severity, lane, actors, evidence_refs, legal_authority, filing_use)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (source, category, finding, severity, lane, actors, evidence_refs, legal_authority, filing_use))
    inserted += 1

conn.commit()

# Verify
total = conn.execute("SELECT COUNT(*) FROM harvest_intelligence").fetchone()[0]
pdf_count = conn.execute("SELECT COUNT(*) FROM harvest_intelligence WHERE source LIKE 'PDF_OUTPUT%'").fetchone()[0]
print(f"\nInserted: {inserted}, Skipped (existing): {skipped}")
print(f"Total harvest_intelligence: {total}")
print(f"PDF_OUTPUT entries: {pdf_count}")

conn.close()
print("DONE")
