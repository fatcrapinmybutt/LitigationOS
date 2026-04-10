"""
Persist ALL harvest intelligence to litigation_context.db.
Uses ACTUAL harvest_intelligence schema: source, category, finding, severity, lane, actors, evidence_refs, legal_authority, filing_use
"""
import sqlite3
from datetime import date

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"

def conn():
    c = sqlite3.connect(DB, timeout=60)
    c.execute("PRAGMA busy_timeout=60000")
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA cache_size=-32000")
    return c

def sep_days():
    return (date.today() - date(2025, 7, 29)).days

def main():
    db = conn()
    total = 0

    rows = []

    # === FILING STACKS HARVEST (1,171 files) ===
    stacks = [
        ("FILING_STACKS", "FILING_INVENTORY", "Omnibus Motion to Vacate — 95% ready, court-formatted, MCR 2.612 compliant", "CRITICAL", "A", "McNeill,Watson", "05_FILINGS/GOLDEN_SET/F01/", "MCR 2.612, MCL 722.23, MCL 722.27", "F01_MSC_PETITION"),
        ("FILING_STACKS", "FILING_INVENTORY", "MSC Bypass Application — 90% ready, MCR 7.305 compliant, emergency posture", "CRITICAL", "F", "McNeill,Hoopes,Ladas-Hoopes", "05_FILINGS/GOLDEN_SET/F02/", "MCR 7.305, MCR 7.306, Const art 6 §4", "F02_MSC_APPLICATION"),
        ("FILING_STACKS", "FILING_INVENTORY", "MCR 2.003 Disqualification v2 — 82% ready, affidavit of bias required", "HIGH", "E", "McNeill", "05_FILINGS/GOLDEN_SET/F03/", "MCR 2.003(C)(1)(a)(b)(c)", "F03_DISQUALIFICATION"),
        ("FILING_STACKS", "FILING_INVENTORY", "Federal §1983 Civil Rights Complaint — 88% ready, Berry conspiracy count included", "CRITICAL", "C", "McNeill,Watson,Berry,Hoopes,Ladas-Hoopes,Rusco", "05_FILINGS/GOLDEN_SET/F04/", "42 USC §1983, 28 USC §1343, Monell v DoSS", "F04_FEDERAL_1983"),
        ("FILING_STACKS", "FILING_INVENTORY", "MSC Original Action — superintending control — 90% ready", "CRITICAL", "F", "McNeill,Hoopes", "05_FILINGS/GOLDEN_SET/F05/", "MCR 7.306, Const art 6 §4, MCR 7.315(C)", "F05_MSC_ORIGINAL"),
        ("FILING_STACKS", "FILING_INVENTORY", "JTC Complaint — 88% ready, 1,127 MCJC violations documented", "HIGH", "E", "McNeill", "05_FILINGS/GOLDEN_SET/F06/", "MCJC Canon 1-7, MCR 9.104-9.125", "F06_JTC_COMPLAINT"),
        ("FILING_STACKS", "FILING_INVENTORY", "Custody Modification — MCL 722.23 all 12 factors briefed", "HIGH", "A", "Watson,McNeill", "05_FILINGS/GOLDEN_SET/F07/", "MCL 722.23(a)-(l), Vodvarka v Grasmeyer", "F07_CUSTODY_MOD"),
        ("FILING_STACKS", "FILING_INVENTORY", "PPO Termination Motion — MCL 600.2950, changed circumstances", "MEDIUM", "D", "Watson", "05_FILINGS/GOLDEN_SET/F08/", "MCL 600.2950, MCR 3.707(B)", "F08_PPO_TERMINATION"),
        ("FILING_STACKS", "FILING_INVENTORY", "COA Brief — 366810 appeal of right — 95% ready, 50pp limit compliant", "CRITICAL", "F", "McNeill", "05_FILINGS/GOLDEN_SET/F09/", "MCR 7.212, MCR 7.204/7.205", "F09_COA_BRIEF"),
        ("FILING_STACKS", "FILING_INVENTORY", "Emergency Motion — restore parenting time — FILED 3/25/2026", "CRITICAL", "A", "McNeill,Watson", "05_FILINGS/GOLDEN_SET/F10/", "MCR 3.207, MCL 722.27a", "F10_EMERGENCY_MOTION"),
        ("FILING_STACKS", "STATISTICS", f"620 evidence findings: 402 NUCLEAR, 207 CRITICAL, 11 HIGH across all lanes", "CRITICAL", "ALL", "Watson,McNeill,Berry,Hoopes", "", "42 USC §1983, MCL 722.23", "ALL_FILINGS"),
        ("FILING_STACKS", "STATISTICS", f"63 exhibits Bates-stamped PIGORS-0001 through PIGORS-0412", "HIGH", "ALL", "", "", "MRE 901, MRE 902", "ALL_FILINGS"),
        ("FILING_STACKS", "STATISTICS", f"30+ case law authorities verified and categorized", "HIGH", "ALL", "", "", "", "ALL_FILINGS"),
        ("FILING_STACKS", "STATISTICS", f"Damage claim range: $1.87M - $19.1M across all lanes", "CRITICAL", "C", "", "", "42 USC §1983, §1988", "F04_FEDERAL_1983"),
        ("FILING_STACKS", "STATISTICS", f"Total filing fees across all 6 courts: $1,740", "MEDIUM", "ALL", "", "", "", "ALL_FILINGS"),
        ("FILING_STACKS", "STATISTICS", f"5 affidavits require notarization before filing", "HIGH", "ALL", "Pigors", "", "28 USC §1746", "ALL_FILINGS"),
        ("FILING_STACKS", "STATISTICS", f"MCR 2.113 compliance: EXCELLENT across all documents", "HIGH", "ALL", "", "", "MCR 2.113", "ALL_FILINGS"),
        ("FILING_STACKS", "STATISTICS", f"Zero AI contamination detected in filing stacks", "HIGH", "ALL", "", "", "", "ALL_FILINGS"),
        ("FILING_STACKS", "CASE_LAW", "Vodvarka v Grasmeyer 259 Mich App 499 (2003) — change of circumstances standard for custody modification", "HIGH", "A", "", "", "MCL 722.27(1)(c)", "F07_CUSTODY_MOD"),
        ("FILING_STACKS", "CASE_LAW", "Pierron v Pierron 486 Mich 81 (2010) — due process in custody proceedings, appellate review standard", "CRITICAL", "F", "", "", "MCL 722.28", "F09_COA_BRIEF"),
        ("FILING_STACKS", "CASE_LAW", "Monell v DoSS 436 US 658 (1978) — municipal liability under §1983, policy/custom requirement", "CRITICAL", "C", "", "", "42 USC §1983", "F04_FEDERAL_1983"),
        ("FILING_STACKS", "CASE_LAW", "Troxel v Granville 530 US 57 (2000) — fundamental right of parents to direct upbringing of children", "CRITICAL", "C", "", "", "US Const Amend XIV", "F04_FEDERAL_1983"),
        ("FILING_STACKS", "CASE_LAW", "Mathews v Eldridge 424 US 319 (1976) — due process balancing test (NOT Brady) for family law", "CRITICAL", "C", "", "", "US Const Amend XIV", "F04_FEDERAL_1983"),
        ("FILING_STACKS", "CASE_LAW", "Shade v Wright 291 Mich App 17 (2010) — evidentiary standards in custody modification", "HIGH", "A", "", "", "MCL 722.27", "F01_MSC_PETITION"),
        ("FILING_STACKS", "CASE_LAW", "Brown v Loveman 260 Mich App 576 (2004) — parenting time enforcement standards", "HIGH", "A", "", "", "MCL 722.27a", "F07_CUSTODY_MOD"),
        ("FILING_STACKS", "CASE_LAW", "Fletcher v Fletcher 447 Mich 871 (1994) — best interest factors analysis methodology", "HIGH", "A", "", "", "MCL 722.23", "F07_CUSTODY_MOD"),
        ("FILING_STACKS", "CASE_LAW", "Harville v State Plumbing 292 Mich App 234 (2011) — §1983 color of state law element", "HIGH", "C", "", "", "42 USC §1983", "F04_FEDERAL_1983"),
        ("FILING_STACKS", "CASE_LAW", "In re Hague 412 Mich 532 (1982) — judicial disqualification standard, appearance of impropriety", "CRITICAL", "E", "", "", "MCR 2.003, MCJC Canon 2", "F03_DISQUALIFICATION"),
    ]
    rows.extend(stacks)

    # === WATSONS CATALOG (556 files, 290 MB) ===
    watsons = [
        ("WATSONS", "EVIDENCE_FILE", "HIGHSIGNAL_QUOTES_UNIFIED_RAW.csv — 66,516 KB raw quote database, highest-value evidence", "CRITICAL", "A", "Watson,McNeill,Berry", "WATSONS/MEEK234/HIGHSIGNAL_QUOTES_UNIFIED_RAW.csv", "", "ALL_FILINGS"),
        ("WATSONS", "EVIDENCE_FILE", "watson_conspiracy_evidence.csv — 9,472 KB, 42 USC §1985(3) conspiracy evidence", "CRITICAL", "C", "Watson,Berry,McNeill", "WATSONS/watson_conspiracy_evidence.csv", "42 USC §1985(3)", "F04_FEDERAL_1983"),
        ("WATSONS", "EVIDENCE_FILE", "watson_family_conspiracy.json — 61,734 evidence items against 6 conspirators", "CRITICAL", "C", "Watson,Albert Watson,Lori Watson,Ronald Berry,Cavan Berry,McNeill", "WATSONS/watson_family_conspiracy.json", "42 USC §1985, RICO 18 USC §1962", "F04_FEDERAL_1983"),
        ("WATSONS", "EVIDENCE_FILE", "impeachment_watson.md — 106+ impeachment items with MRE 613(a) cross-exam questions", "CRITICAL", "A", "Watson", "WATSONS/impeachment_watson.md", "MRE 613(a), MRE 801(d)(1)", "ALL_FILINGS"),
        ("WATSONS", "EVIDENCE_FILE", "ronald_berry_evidence.csv — 12,028 KB, non-attorney legal ops documentation", "HIGH", "C", "Ronald Berry", "WATSONS/ronald_berry_evidence.csv", "MCL 600.916 (UPL)", "F04_FEDERAL_1983"),
        ("WATSONS", "EVIDENCE_FILE", "MSC-JTC Exhibits Binder PDF — 182 pages, 8,081 KB", "CRITICAL", "E", "McNeill", "WATSONS/MSC-JTC_Exhibits_Binder.pdf", "MCJC Canon 1-7", "F06_JTC_COMPLAINT"),
        ("WATSONS", "DISCOVERY", "Interrogatories READY — MCR 2.309 compliant", "HIGH", "A", "Watson", "", "MCR 2.309", "DISCOVERY"),
        ("WATSONS", "DISCOVERY", "Requests for Admission READY — MCR 2.312 compliant", "HIGH", "A", "Watson", "", "MCR 2.312", "DISCOVERY"),
        ("WATSONS", "DISCOVERY", "Requests for Production READY — MCR 2.310 compliant", "HIGH", "A", "Watson", "", "MCR 2.310", "DISCOVERY"),
    ]
    rows.extend(watsons)

    # === MCNEILLEXPARTE (812 files) ===
    mcneill = [
        ("MCNEILLEXPARTE", "JUDICIAL_VIOLATION", "52 ex parte orders documented — 100% favored Watson, 0% favored Pigors", "CRITICAL", "E", "McNeill", "", "MCJC Canon 3(B)(7), MCR 2.003(C)(1)", "F06_JTC_COMPLAINT"),
        ("MCNEILLEXPARTE", "JUDICIAL_VIOLATION", "44% ex parte rate vs 5% national judicial norm — 8.8x deviation", "CRITICAL", "E", "McNeill", "", "MCJC Canon 3(B)(7)", "F06_JTC_COMPLAINT"),
        ("MCNEILLEXPARTE", "JUDICIAL_VIOLATION", "1,127 MCJC Canon violations documented from 812 files", "CRITICAL", "E", "McNeill", "", "MCJC Canon 1-7", "F06_JTC_COMPLAINT"),
        ("MCNEILLEXPARTE", "JUDICIAL_VIOLATION", "McNeill quote: 'Yes, I had my staff listen to it' — improper staff involvement in ex parte review", "CRITICAL", "E", "McNeill", "", "MCJC Canon 3(B)(7), MCR 2.003", "F03_DISQUALIFICATION"),
        ("MCNEILLEXPARTE", "JUDICIAL_VIOLATION", "McNeill quote: 'Do not file anymore, I will not look at it' — direct denial of access to courts", "CRITICAL", "E", "McNeill", "", "US Const Amend I, Const 1963 art 1 §13", "F04_FEDERAL_1983"),
        ("MCNEILLEXPARTE", "JUDICIAL_VIOLATION", "McNeill told Andrew to 'shut my mouth' during contempt hearing — jailed for objecting to unlawful medication coercion", "CRITICAL", "E", "McNeill", "", "US Const Amend I, MCJC Canon 3(B)(4)", "F04_FEDERAL_1983"),
        ("MCNEILLEXPARTE", "JUDICIAL_VIOLATION", "Aug 8, 2025 Five Orders Day — 5 ex parte orders in 1 day, zero notice to Father", "CRITICAL", "E", "McNeill,Watson", "", "US Const Amend XIV, MCJC Canon 3(B)(7)", "F05_MSC_ORIGINAL"),
        ("MCNEILLEXPARTE", "JUDICIAL_VIOLATION", "Contempt SC#5 (14 days) + SC#6+7 (45 days) = 59 days jail total — for birthday messages via AppClose", "CRITICAL", "E", "McNeill", "", "US Const Amend I, Amend VIII", "F04_FEDERAL_1983"),
        ("MCNEILLEXPARTE", "JUDICIAL_VIOLATION", "HealthWest evaluation excluded — court-ordered eval showed Father fit (LOCUS 12, Psychosis=0, Substance=0, Danger=0)", "CRITICAL", "E", "McNeill", "", "MRE 702, MRE 703, MCL 722.23(c)(g)", "F09_COA_BRIEF"),
        ("MCNEILLEXPARTE", "JUDICIAL_VIOLATION", "McNeill and Watson discussed requiring prescription medication as condition for parenting time — unlawful practice of medicine", "CRITICAL", "E", "McNeill,Watson", "", "MCL 333.17011 (practice of medicine), US Const Amend XIV", "F04_FEDERAL_1983"),
    ]
    rows.extend(mcneill)

    # === SHADY OAKS HOUSING (2,154 files) ===
    shady = [
        ("SHADY", "HOUSING_VIOLATION", "21 causes of action identified across housing cluster", "CRITICAL", "B", "Shady Oaks", "", "MCL 554.139, MCL 125.530", "HOUSING_COMPLAINT"),
        ("SHADY", "HOUSING_VIOLATION", "EGLE VN-017235 — documented sewage violation, environmental hazard", "CRITICAL", "B", "Shady Oaks", "", "MCL 324.3109, EGLE reg", "HOUSING_COMPLAINT"),
        ("SHADY", "HOUSING_VIOLATION", "3 blocked home sales documented — interference with property rights", "HIGH", "B", "Shady Oaks", "", "MCL 600.2919a (tortious interference)", "HOUSING_COMPLAINT"),
        ("SHADY", "HOUSING_VIOLATION", "Water shutoff without notice — habitability violation", "HIGH", "B", "Shady Oaks", "", "MCL 554.139(1)(a)(d)", "HOUSING_COMPLAINT"),
        ("SHADY", "HOUSING_VIOLATION", "Damages model: $111K-$244K actual + $1.5M-$4.9M total with statutory multipliers", "CRITICAL", "B", "Shady Oaks", "", "MCL 600.3204, MCL 554.139", "HOUSING_COMPLAINT"),
        ("SHADY", "HOUSING_VIOLATION", "Lockout/exclusion from property without legal process", "HIGH", "B", "Shady Oaks", "", "MCL 554.601 et seq", "HOUSING_COMPLAINT"),
    ]
    rows.extend(shady)

    # === CRITICAL TESTIMONY (user-provided, affidavit-grade) ===
    testimony = [
        ("USER_TESTIMONY", "TESTIMONY", f"Father-child separation: {sep_days()} days since July 29, 2025 — last contact with L.D.W.", "CRITICAL", "A", "McNeill,Watson", "", "US Const Amend XIV, MCL 722.27a", "ALL_FILINGS"),
        ("USER_TESTIMONY", "TESTIMONY", "Albert Watson attended EVERY custody exchange defying McNeill verbal order 'keep her family out of it' — transcripts confirm", "CRITICAL", "A", "Albert Watson,McNeill", "", "MCL 722.23(j)(k)", "F07_CUSTODY_MOD"),
        ("USER_TESTIMONY", "TESTIMONY", "Selective enforcement: Albert Watson zero consequences for violating order vs Andrew 59 days jail", "CRITICAL", "E", "McNeill,Albert Watson", "", "US Const Amend XIV (equal protection)", "F04_FEDERAL_1983"),
        ("USER_TESTIMONY", "TESTIMONY", "Cody Watson = road harassment ONLY, NOT custody exchange conduct", "MEDIUM", "A", "Cody Watson", "", "", "CASE_INTELLIGENCE"),
        ("USER_TESTIMONY", "TESTIMONY", "Emily posted Instagram family portrait with Ron Berry replacing Andrew — parental alienation evidence", "CRITICAL", "A", "Watson,Ronald Berry", "", "MCL 722.23(j)", "F07_CUSTODY_MOD"),
        ("USER_TESTIMONY", "TESTIMONY", "NS2505044: Albert Watson told police 'They want this documented so Emily can go tomorrow to get an Ex Parte order' — premeditated conspiracy", "CRITICAL", "C", "Albert Watson,Watson", "NSPD NS2505044", "42 USC §1985(3)", "F04_FEDERAL_1983"),
        ("USER_TESTIMONY", "TESTIMONY", "Emily recanted Oct 13, 2023 'nothing was physical' (NSPD-2023-08121) then filed PPO Oct 15 — 2 days later", "CRITICAL", "D", "Watson", "NSPD-2023-08121", "MCL 600.2950, MRE 613(a)", "F08_PPO_TERMINATION"),
        ("USER_TESTIMONY", "TESTIMONY", "Officer Ella Randall report: Emily admitted METH USE — projection pattern in false allegations against Andrew", "CRITICAL", "A", "Watson", "NSPD police report", "MCL 722.23(g)(k)", "F07_CUSTODY_MOD"),
    ]
    rows.extend(testimony)

    # === ADVERSARY NETWORK ===
    adversary = [
        ("ADVERSARY_NET", "CONSPIRACY", "THREE-COURT JUDICIAL CARTEL: McNeill + Hoopes + Ladas-Hoopes = former partners at Ladas Hoopes & McNeill, 435 Whitehall Rd", "CRITICAL", "E", "McNeill,Hoopes,Ladas-Hoopes", "", "42 USC §1983, MCR 2.003, MCJC Canon 1-3", "F05_MSC_ORIGINAL"),
        ("ADVERSARY_NET", "CONSPIRACY", "Berry-McNeill family nexus: Ronald Berry (Emily boyfriend) related to Cavan Berry (McNeill spouse, 60th District magistrate)", "CRITICAL", "C", "Ronald Berry,Cavan Berry,McNeill", "", "42 USC §1985(3), MCR 2.003(C)(1)(a)", "F04_FEDERAL_1983"),
        ("ADVERSARY_NET", "CONSPIRACY", "FOC Rusco operates from 990 Terrace St = same address as Cavan Berry office", "HIGH", "E", "Rusco,Cavan Berry", "", "MCR 2.003, MCJC Canon 2", "F03_DISQUALIFICATION"),
        ("ADVERSARY_NET", "CONSPIRACY", "Watson family coordinated: Albert premeditation (NS2505044) + Emily false allegations + Lori support + Cody road harassment", "CRITICAL", "C", "Watson,Albert Watson,Lori Watson,Cody Watson", "", "42 USC §1985(3)", "F04_FEDERAL_1983"),
        ("ADVERSARY_NET", "CONSPIRACY", "Barnes P55406 withdrawal Mar 2026 — Emily now unrepresented, served DIRECTLY at 2160 Garland Dr", "MEDIUM", "A", "Watson,Barnes", "", "MCR 2.107", "ALL_FILINGS"),
    ]
    rows.extend(adversary)

    # === INSERT ALL ===
    insert_sql = """INSERT INTO harvest_intelligence 
        (source, category, finding, severity, lane, actors, evidence_refs, legal_authority, filing_use)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    
    db.executemany(insert_sql, rows)
    db.commit()
    total = len(rows)

    # Verify
    count = db.execute("SELECT COUNT(*) FROM harvest_intelligence").fetchone()[0]
    print(f"✅ harvest_intelligence: {total} rows inserted, {count} total in table")

    # === BERRY_MCNEILL_INTELLIGENCE ===
    cols = {r[1] for r in db.execute("PRAGMA table_info(berry_mcneill_intelligence)").fetchall()}
    print(f"berry_mcneill_intelligence columns: {cols}")
    
    bmi_rows = []
    if 'finding' in cols and 'source' in cols:
        bmi_sql = f"INSERT OR IGNORE INTO berry_mcneill_intelligence ({', '.join(c for c in ['source','finding','severity','actors','evidence_refs'] if c in cols)}) VALUES ({', '.join('?' for c in ['source','finding','severity','actors','evidence_refs'] if c in cols)})"
        bmi_data = [
            ("MCNEILLEXPARTE_harvest", "52 ex parte orders, 100% favored Watson — 44% ex parte rate vs 5% national norm", "CRITICAL", "McNeill", "MCNEILLEXPARTE/812_files"),
            ("MCNEILLEXPARTE_harvest", "McNeill quote: 'Do not file anymore, I will not look at it' — denial of access to courts", "CRITICAL", "McNeill", "hearing_testimony"),
            ("MCNEILLEXPARTE_harvest", "McNeill told Andrew 'shut my mouth' then jailed him 14 days for contempt — SC#5", "CRITICAL", "McNeill", "hearing_transcript"),
            ("SHADY_harvest", "McNeill/Hoopes/Ladas-Hoopes = former partners at Ladas Hoopes & McNeill firm, 435 Whitehall Rd", "CRITICAL", "McNeill,Hoopes,Ladas-Hoopes", "public_records"),
            ("WATSONS_harvest", "watson_family_conspiracy.json: 61,734 evidence items against 6 conspirators in Watson-Berry network", "CRITICAL", "Watson,Berry,Albert Watson", "WATSONS/watson_family_conspiracy.json"),
        ]
        bmi_filtered = [tuple(v for v, c in zip(row, ['source','finding','severity','actors','evidence_refs']) if c in cols) for row in bmi_data]
        try:
            db.executemany(bmi_sql, bmi_filtered)
            db.commit()
            bmi_count = db.execute("SELECT COUNT(*) FROM berry_mcneill_intelligence").fetchone()[0]
            print(f"✅ berry_mcneill_intelligence: {len(bmi_filtered)} rows inserted, {bmi_count} total")
        except Exception as e:
            print(f"⚠️ berry_mcneill_intelligence insert error: {e}")
            # Try simpler approach
            for row in bmi_data:
                try:
                    db.execute("INSERT INTO berry_mcneill_intelligence (source, finding, severity) VALUES (?,?,?)", (row[0], row[1], row[2]))
                except:
                    pass
            db.commit()
            print("  Fallback inserts attempted")
    else:
        print(f"⚠️ berry_mcneill_intelligence has unexpected schema: {cols}")
        # Try to insert with whatever columns exist
        for val in ["52 ex parte orders 100% Watson", "McNeill 'Do not file anymore'", "59 days jail for birthday messages"]:
            try:
                col_list = list(cols - {'id', 'created_at'})
                if col_list:
                    db.execute(f"INSERT INTO berry_mcneill_intelligence ({col_list[0]}) VALUES (?)", (val,))
            except:
                pass
        db.commit()

    db.close()
    print(f"\n🏁 TOTAL: {total} harvest intelligence rows persisted")
    print(f"   Separation days: {sep_days()}")

if __name__ == "__main__":
    main()
