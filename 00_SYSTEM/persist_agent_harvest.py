"""
Persist all harvested intelligence from background agents to litigation_context.db.
Sources: read-mcneillexparte, read-federal-pdf-blueprints, JTC/WDMI research.
"""
import sqlite3
import datetime

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"

def get_conn():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    return conn

def persist_mcneill_quotes(conn):
    """Persist McNeill's direct on-record admissions and statements."""
    quotes = [
        # (quote_text, source_file, category, lane, impeachment_value, page_number)
        (
            'Yes, I had my staff listen to it.',
            'MCNEILLEXPARTE/court_record_aug_11_2025',
            'judicial_admission',
            'E',
            10,
            'August 11, 2025 hearing transcript'
        ),
        (
            'Do not file any more. I will not look at it.',
            'MCNEILLEXPARTE/court_record_filing_ban',
            'denial_of_access',
            'E',
            10,
            'Hearing transcript - filing ban without MCR 2.625 authority'
        ),
        (
            'The court finds that this continued pattern of questioning is meant to harass the defendant.',
            'MCNEILLEXPARTE/court_record_cross_exam',
            'denial_of_due_process',
            'E',
            9,
            'Hearing transcript - characterizing cross-examination as harassment'
        ),
        (
            'I have represented Party A in the past.',
            'MCNEILLEXPARTE/court_record_disqualification',
            'judicial_admission',
            'E',
            10,
            'Hearing transcript - automatic disqualification admission under MCR 2.003(C)(1)(b)'
        ),
        (
            'McNeill called Andrew a liar and crazy on record, muting him 7+ times in a single contempt hearing.',
            'MCNEILLEXPARTE/contempt_hearing_record',
            'judicial_bias',
            'E',
            9,
            'Contempt hearing SC#5 November 2024'
        ),
        (
            'McNeill described court-ordered HealthWest evaluation that cleared father as a ghost evaluation and refused to consider it.',
            'MCNEILLEXPARTE/healthwest_exclusion',
            'evidence_exclusion',
            'E',
            10,
            'Hearing transcript - HealthWest evaluation suppression'
        ),
    ]
    
    inserted = 0
    for qt, sf, cat, lane, iv, pg in quotes:
        existing = conn.execute(
            "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text = ? AND source_file = ?",
            (qt, sf)
        ).fetchone()[0]
        if existing == 0:
            conn.execute(
                """INSERT INTO evidence_quotes 
                   (quote_text, source_file, category, lane, relevance_score, tags, is_duplicate)
                   VALUES (?, ?, ?, ?, ?, ?, 0)""",
                (qt, sf, cat, lane, float(iv)/10.0, pg)
            )
            inserted += 1
    
    conn.commit()
    print(f"McNeill quotes: {inserted} new rows inserted (of {len(quotes)} total)")
    return inserted

def persist_mcneill_impeachment(conn):
    """Persist McNeill impeachment entries from agent harvest."""
    entries = [
        # (category, evidence_summary, source_file, quote_text, impeachment_value, cross_exam_question, filing_relevance)
        (
            'ex_parte_violation',
            'McNeill admitted on record Aug 11, 2025 that her staff listened to USB recording submitted ex parte by Emily Watson without notice to Andrew',
            'MCNEILLEXPARTE/aug_11_hearing',
            'Yes, I had my staff listen to it.',
            10,
            'Judge McNeill, on August 11, 2025, you admitted on the record that your staff listened to a USB recording submitted by the opposing party. Is that correct? And you listened to this recording before any hearing was held, correct?',
            'F01,F05,F06,F09'
        ),
        (
            'denial_of_access',
            'McNeill issued blanket filing ban without MCR 2.625 authority, telling Andrew Do not file any more, I will not look at it',
            'MCNEILLEXPARTE/filing_ban_hearing',
            'Do not file any more. I will not look at it.',
            10,
            'Judge McNeill, you told the plaintiff Do not file any more. Under what authority of MCR 2.625 did you issue this restriction? Was a written order ever entered?',
            'F01,F05,F06,F09'
        ),
        (
            'automatic_disqualification',
            'McNeill admitted I have represented Party A in the past triggering automatic disqualification under MCR 2.003(C)(1)(b) but then denied her own disqualification motion instead of forwarding to Chief Judge per MCR 2.003(D)(1)',
            'MCNEILLEXPARTE/disqualification_hearing',
            'I have represented Party A in the past.',
            10,
            'Judge McNeill, you stated on the record that you previously represented a party. MCR 2.003(C)(1)(b) mandates disqualification. Why did you deny your own recusal motion instead of forwarding it to the Chief Judge?',
            'F01,F03,F05,F06'
        ),
        (
            'evidence_suppression',
            'Court-ordered HealthWest evaluation cleared father as fit parent (LOCUS 12, Psychosis=0, Substance=0, Danger=0) but McNeill called it a ghost evaluation and excluded it from the record',
            'MCNEILLEXPARTE/healthwest_suppression',
            'McNeill described court-ordered HealthWest evaluation that cleared father as a ghost evaluation.',
            10,
            'Judge McNeill, you ordered a HealthWest evaluation. That evaluation found the father fit with a LOCUS score of 12. Why did you then describe that evaluation as a ghost evaluation and refuse to consider it?',
            'F01,F05,F06,F09'
        ),
        (
            'ex_parte_five_orders',
            'On August 8, 2025, McNeill signed 5 separate ex parte orders in a single day suspending ALL parenting time, changing custody from 50/50 to zero, without notice or hearing. This was 1 day after Albert Watson told police (NS2505044) the ex parte plan was premeditated.',
            'MCNEILLEXPARTE/aug_8_orders',
            'Five ex parte orders signed on same day, all without notice to Andrew, based on unsworn unverified motion.',
            10,
            'Judge McNeill, on August 8, 2025, you signed five separate orders affecting the fathers parental rights. Were any of these orders preceded by notice to the father? Was the underlying motion verified under oath as required by MCR 3.207(B)(1)?',
            'F01,F04,F05,F06,F09'
        ),
        (
            'contempt_abuse',
            'McNeill sentenced father to 59 total days incarceration across multiple contempt orders. SC#5: 14 days for objecting. SC#6+7: 45 days for birthday messages to child via court-approved AppClose platform. Father lost 2 jobs and 2 homes.',
            'MCNEILLEXPARTE/contempt_orders',
            'Total incarceration: 59 days. SC#5 14 days, SC#6+7 45 days. Lost 2 jobs, 2 homes.',
            10,
            'Judge McNeill, you sentenced the father to 59 days total incarceration. The SC#6 and SC#7 contempt was for sending birthday messages to his child via AppClose. How is sending birthday wishes through a court-approved platform contemptuous?',
            'F01,F04,F05,F06,F09'
        ),
        (
            'ex_parte_rate_anomaly',
            'McNeill entered 24 of 55 PPO orders (44%) ex parte. Normal judicial rate is 4-5%. McNeill rate is nearly 9X normal, demonstrating systematic procedural abuse.',
            'MCNEILLEXPARTE/ex_parte_analysis',
            '24 of 55 PPO orders (44%) entered ex parte vs normal 4-5% rate.',
            9,
            'Your Honor, records show that 44% of your PPO orders were entered ex parte, compared to the normal judicial rate of approximately 4-5%. Can you explain why your ex parte rate is nearly nine times the average?',
            'F06,F01,F05'
        ),
        (
            'secret_evaluation',
            'McNeill ordered a second secret HealthWest evaluation routed to her secretary, never disclosed to father. This constitutes a Brady-equivalent due process violation in family law context.',
            'MCNEILLEXPARTE/secret_eval',
            'Second secret HealthWest eval ordered, routed to secretary, never disclosed to father.',
            10,
            'Judge McNeill, did you order a second HealthWest evaluation of the father? Was this evaluation disclosed to the father or his file? Under Mathews v Eldridge, does a parent have a right to know about evaluations ordered by the court?',
            'F01,F04,F05,F06'
        ),
    ]

    inserted = 0
    for cat, es, sf, qt, iv, cxq, fr in entries:
        existing = conn.execute(
            "SELECT COUNT(*) FROM impeachment_matrix WHERE quote_text = ? AND source_file = ?",
            (qt, sf)
        ).fetchone()[0]
        if existing == 0:
            conn.execute(
                """INSERT INTO impeachment_matrix 
                   (category, evidence_summary, source_file, quote_text, impeachment_value, 
                    cross_exam_question, filing_relevance)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (cat, es, sf, qt, iv, cxq, fr)
            )
            inserted += 1
    
    conn.commit()
    print(f"McNeill impeachment: {inserted} new rows inserted (of {len(entries)} total)")
    return inserted

def persist_berry_connections(conn):
    """Persist Berry-McNeill-Rusco connection intelligence."""
    connections = [
        (
            'Cavan John Berry is McNeill spouse. Address: 4084 Oak Hollow Ct, Norton Shores MI. Both attended Northern Illinois U College of Law (McNeill 1996, Cavan 1998). Cavan is Attorney Magistrate at 60th District Court, 990 Terrace St - SAME ADDRESS as FOC Pamela Rusco.',
            'MCNEILLEXPARTE/berry_mcneill_connection',
            'cartel_connection',
            'E',
            10,
            'Berry-McNeill marriage, 990 Terrace nexus'
        ),
        (
            'Ronald Berry lives at 2160 Garland Dr with Emily Watson. Shares Berry surname with Cavan in Norton Shores (pop ~24,000). Shannon Patrick Berry confirmed as relative of Cavan Berry per Whitepages. If Ronald related to Cavan within 3rd degree, MCR 2.003(C)(1)(b) mandates automatic disqualification - NEVER DISCLOSED.',
            'MCNEILLEXPARTE/ronald_berry_connection',
            'cartel_connection',
            'E',
            10,
            'Ronald Berry-Cavan Berry familial connection, undisclosed conflict'
        ),
        (
            'Case reassignment: 2024-001507-DC reassigned from Judge Sprader to McNeill on 04/01/2024. Chief Judge Hoopes controls case assignments per MCR 8.111. Hoopes was McNeills former law partner at Ladas, Hoopes & McNeill (435 Whitehall Rd).',
            'MCNEILLEXPARTE/case_reassignment',
            'cartel_connection',
            'E',
            9,
            'Hoopes reassigned case to his former law partner McNeill'
        ),
    ]
    
    inserted = 0
    for qt, sf, cat, lane, iv, pg in connections:
        existing = conn.execute(
            "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text = ? AND source_file = ?",
            (qt, sf)
        ).fetchone()[0]
        if existing == 0:
            conn.execute(
                """INSERT INTO evidence_quotes 
                   (quote_text, source_file, category, lane, relevance_score, tags, is_duplicate)
                   VALUES (?, ?, ?, ?, ?, ?, 0)""",
                (qt, sf, cat, lane, float(iv)/10.0, pg)
            )
            inserted += 1
    
    conn.commit()
    print(f"Berry connections: {inserted} new rows inserted (of {len(connections)} total)")
    return inserted

def persist_mcr_filing_deadlines(conn):
    """Persist critical MCR filing deadline rules from agent harvest."""
    rules = [
        # (rule_number, rule_type, title, full_text)
        (
            'MCR 2.119(C)',
            'MCR',
            'Motion Service and Filing Deadlines',
            'MCR 2.119(C): Motion service 9 days before hearing (mail), 7 days before (e-service). Response service 5 days before (mail), 3 days before (e-service). Filing deadline: Motion 7 days before hearing; Response 3 days before hearing.'
        ),
        (
            'MCR 1.109(D)',
            'MCR',
            'Filing Format Standards',
            'MCR 1.109(D): Documents must be legible, English, 8.5x11 inches. Font: 12-13 point body, 10+ point footnotes. Caption must include court name, parties, case number, document ID.'
        ),
        (
            'MiFILE',
            'MCR',
            'MiFILE Electronic Document Standards',
            'MiFILE Standards: PDF preferred (text-searchable), OCR recommended for scans. 25MB per file maximum - split with labels when needed. Attachments: index on last page, numbered and referenced by filename.'
        ),
        (
            'MCR 7.204(A)',
            'MCR',
            'Claim of Appeal Requirements and Deadline',
            'MCR 7.204(A): Claim of Appeal must be filed within 21 days after entry of judgment (jurisdictional). File with COA Clerk, serve parties, pay $375 fee. Include: claim of appeal form, copy of judgment, proof of service.'
        ),
        (
            'MCR 7.210(B)(1)',
            'MCR',
            'Record on Appeal - Transcript Ordering Deadlines',
            'MCR 7.210(B)(1): Transcript must be ordered within 14 days of claim of appeal. Court reporter files within 56 days. If no transcript available: file settled statement under MCR 7.210(B)(2).'
        ),
        (
            'MCR 7.212(B)',
            'MCR',
            'Brief Filing Deadlines and Page Limits',
            'MCR 7.212(B): Appellant brief within 56 days after transcript filed. Appellee brief within 35 days after service of appellant brief. Reply brief within 21 days after service of appellee brief. Page limits: 50 pages main, 25 pages reply.'
        ),
        (
            'MCR 7.305(C)',
            'MCR',
            'MSC Leave to Appeal Deadline and Grounds',
            'MCR 7.305(C): MSC Leave to Appeal must be filed within 42 days from COA opinion/order. Grounds: conflict between panels, public interest, legal error, constitutional issue.'
        ),
        (
            'MCR 2.116(G)',
            'MCR',
            'Summary Disposition Timing Override',
            'MCR 2.116(G) override timing: Summary disposition motion 21 days, response 7 days, reply brief 4 days. Reply brief page limit: 5 pages.'
        ),
        (
            'MCR 1.109(E)',
            'MCR',
            'Citation Accuracy - Sanction Risk',
            'MCR 1.109(E): Citing overruled authority is SANCTIONABLE. All case citations must be verified against actual reporters. Primary AI risk: hallucinated case law.'
        ),
    ]
    
    inserted = 0
    for rnum, rtype, title, full_text in rules:
        existing = conn.execute(
            "SELECT COUNT(*) FROM michigan_rules_extracted WHERE rule_number = ? AND rule_type = ?",
            (rnum, rtype)
        ).fetchone()[0]
        if existing == 0:
            conn.execute(
                """INSERT INTO michigan_rules_extracted 
                   (rule_number, rule_type, title, full_text, text_length, source_file, is_key_rule)
                   VALUES (?, ?, ?, ?, ?, ?, 1)""",
                (rnum, rtype, title, full_text, len(full_text), 'agent_harvest_apr2026')
            )
            inserted += 1
    
    conn.commit()
    print(f"MCR filing deadlines: {inserted} new rules inserted (of {len(rules)} total)")
    return inserted

def persist_violation_stats(conn):
    """Persist aggregate violation statistics as evidence quotes for reference."""
    stats = [
        (
            'McNeill violation analysis from MCNEILLEXPARTE: 1,127 total violations cataloged. 377 CRITICAL (33.5%), 243 HIGH (21.6%), 484 MEDIUM (42.9%), 23 LOW (2.0%). 620 violations (55.0%) rated CRITICAL or HIGH - direct harm to fundamental parental rights.',
            'MCNEILLEXPARTE/benchbook_deviation_report',
            'judicial_violation_stats',
            'E',
            10,
            'Aggregate benchbook deviation analysis'
        ),
        (
            'McNeill ex parte statistics: 24 of 55 PPO orders (44%) entered ex parte. ALL 24 presided by McNeill. Normal judicial rate: 4-5%. McNeill rate: 44% - nearly 9X normal. 5 ex parte orders on August 8, 2025 alone.',
            'MCNEILLEXPARTE/ex_parte_rate_analysis',
            'judicial_violation_stats',
            'E',
            10,
            'Ex parte rate comparison analysis'
        ),
        (
            'McNeill case harm totals: 329+ days parent-child separation, 860+ parenting hours lost, 59 days total incarceration, 2 jobs lost, 2 homes lost. No best-interest hearing ever held. No unfitness finding ever made. ZERO written findings on any of 12 MCL 722.23 factors.',
            'MCNEILLEXPARTE/harm_totals',
            'harm_documentation',
            'E',
            10,
            'Aggregate harm to father and child'
        ),
        (
            'MCNEILLEXPARTE directory inventory: 160 .md files, 218 .txt files, 99 .pdf files, 153 .json files, 46 .csv files, 108 .docx, 3 .odt, 8 .zip. Complete litigation-ready evidence packages: JTC complaint, disqualification motion, affidavit of bias, superintending control motion, formal complaint (17 allegations, 41 exhibits), benchbook deviation report, Berry connection report, 200+ curated quotes, 24+ PDF motion packets.',
            'MCNEILLEXPARTE/directory_inventory',
            'evidence_inventory',
            'E',
            5,
            'MCNEILLEXPARTE directory contents as of April 2026'
        ),
    ]
    
    inserted = 0
    for qt, sf, cat, lane, iv, pg in stats:
        existing = conn.execute(
            "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text = ? AND source_file = ?",
            (qt, sf)
        ).fetchone()[0]
        if existing == 0:
            conn.execute(
                """INSERT INTO evidence_quotes 
                   (quote_text, source_file, category, lane, relevance_score, tags, is_duplicate)
                   VALUES (?, ?, ?, ?, ?, ?, 0)""",
                (qt, sf, cat, lane, float(iv)/10.0, pg)
            )
            inserted += 1
    
    conn.commit()
    print(f"Violation stats: {inserted} new rows inserted (of {len(stats)} total)")
    return inserted

def persist_jtic_filing_requirements(conn):
    """Persist JTC and WDMI filing requirements as evidence_quotes for reference."""
    reqs = [
        (
            'JTC Filing Requirements (web-researched April 2026): Must use official Request for Investigation Form (PDF from JTC website). Signature MUST be NOTARIZED. Cannot submit by email or fax. Max 2 complainants per form. Submit COPIES of supporting docs (not originals). Mail to: Judicial Tenure Commission, 3034 West Grand Blvd, Suite 8-350, Detroit, MI 48202. Phone: (313) 875-5110. JTC CANNOT reverse or modify judicial decisions - they only discipline judges. Fee: $0.',
            'web_research/jtc_filing_requirements',
            'filing_requirements',
            'E',
            8,
            'JTC official filing process'
        ),
        (
            'WDMI Federal Filing Requirements (web-researched April 2026): JS 44 Civil Cover Sheet required with every new case (Nature of Suit: 440 Other Civil Rights). AO 239 IFP application if cannot pay $405 filing fee. Pro se may paper file (CM/ECF exception for pro se). Filing divisions: Grand Rapids, Lansing, Kalamazoo, Marquette. Events in Muskegon -> Grand Rapids division. Specific Section 1983 complaint form available from court website.',
            'web_research/wdmi_filing_requirements',
            'filing_requirements',
            'C',
            8,
            'WDMI federal court filing process'
        ),
        (
            'SCAO Forms Database: 893 forms indexed in scao_forms table with FTS5 (scao_forms_fts). Key forms: MC 12 (Proof of Service), MC 20 (Fee Waiver), MC 302 (PPO Domestic), MC 375 (Motion), DC 100 (Complaint), DC 101 (Summons), CC 257 (Civil Cover Sheet), COA 1 (Claim of Appeal), JS 44 (Federal Cover Sheet), AO 239 (Federal IFP). SCAO website is JavaScript SPA - cannot scrape directly.',
            'litigation_context_db/scao_forms_table',
            'filing_requirements',
            'ALL',
            7,
            'SCAO forms database reference'
        ),
    ]
    
    inserted = 0
    for qt, sf, cat, lane, iv, pg in reqs:
        existing = conn.execute(
            "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text = ? AND source_file = ?",
            (qt, sf)
        ).fetchone()[0]
        if existing == 0:
            conn.execute(
                """INSERT INTO evidence_quotes 
                   (quote_text, source_file, category, lane, relevance_score, tags, is_duplicate)
                   VALUES (?, ?, ?, ?, ?, ?, 0)""",
                (qt, sf, cat, lane, float(iv)/10.0, pg)
            )
            inserted += 1
    
    conn.commit()
    print(f"Filing requirements: {inserted} new rows inserted (of {len(reqs)} total)")
    return inserted

def persist_mcr_violations_to_judicial(conn):
    """Persist specific MCR/MCL/Canon violations to judicial_violations table."""
    # Check schema
    cols = {r[1] for r in conn.execute("PRAGMA table_info(judicial_violations)")}
    print(f"judicial_violations columns: {sorted(cols)}")
    
    violations = [
        # Adapt to actual schema
        ('MCR 2.003(C)(1)(b)', 'McNeill admitted prior representation of party. Automatic disqualification triggered but self-denied instead of forwarding to Chief Judge per MCR 2.003(D)(1).', 'critical', 'E'),
        ('MCR 2.119(E)', 'Failed to provide notice of oral argument before entering August 8 orders. Father learned of orders AFTER entry.', 'critical', 'E'),
        ('MCR 2.119(F)', 'Failed to conduct required hearings before imposing extreme sanctions including complete parenting time suspension.', 'critical', 'E'),
        ('MCR 3.207(B)(1)', 'August 8, 2025 motion NOT verified under oath. Orders signed anyway in violation of verification requirement.', 'critical', 'E'),
        ('MCR 3.207(C)(5)', 'Requires contested motion hearing within 14 days. ZERO hearings held in required timeframe after August 8 orders.', 'critical', 'E'),
        ('MCR 2.517(A)(1)', 'Orders lack specific findings of fact required by rule. No written findings on any of 12 MCL 722.23 factors.', 'critical', 'E'),
        ('Canon 3(A)(4)', 'Ex parte communications on merits: staff listened to USB recording, secret HealthWest eval ordered and reviewed without father knowledge.', 'critical', 'E'),
        ('Canon 3(B)(5)', 'Patience, dignity, courtesy violated: called father liar and crazy on record, muted 7+ times in single hearing, characterized cross-examination as harassment.', 'high', 'E'),
        ('Canon 3(B)(7)', 'Primary ex parte communications violation: USB recording receipt, staff review of recording, secret evaluation, Emily Watson ex parte submissions.', 'critical', 'E'),
        ('MCL 722.23', 'ZERO written findings made on ANY of 12 statutory best-interest factors despite ordering complete custody change. 9 of 12 factors favor father per case analysis.', 'critical', 'A'),
        ('MCL 722.27a(9)', 'Mandatory enforcement of parenting time NOT applied despite 27+ documented court order violations by Emily Watson.', 'critical', 'A'),
        ('MCR 2.625', 'Filing ban issued without MCR 2.625 authority. McNeill told father Do not file any more, I will not look at it.', 'critical', 'E'),
    ]
    
    severity_map = {'critical': 10, 'high': 8, 'medium': 5, 'low': 2}
    
    if 'violation_type' in cols and 'description' in cols and 'severity' in cols:
        inserted = 0
        for vtype, desc, sev, lane in violations:
            existing = conn.execute(
                "SELECT COUNT(*) FROM judicial_violations WHERE violation_type = ? AND description = ?",
                (vtype, desc)
            ).fetchone()[0]
            if existing == 0:
                sev_int = severity_map.get(sev, 5)
                insert_cols = ['violation_type', 'description', 'severity']
                insert_vals = [vtype, desc, sev_int]
                if 'lane' in cols:
                    insert_cols.append('lane')
                    insert_vals.append(lane)
                if 'judge' in cols:
                    insert_cols.append('judge')
                    insert_vals.append('McNeill')
                    
                placeholders = ','.join(['?' for _ in insert_cols])
                col_str = ','.join(insert_cols)
                conn.execute(
                    f"INSERT INTO judicial_violations ({col_str}) VALUES ({placeholders})",
                    insert_vals
                )
                inserted += 1
        
        conn.commit()
        print(f"Judicial violations: {inserted} new rows inserted (of {len(violations)} total)")
        return inserted
    else:
        print(f"judicial_violations schema incompatible. Available columns: {sorted(cols)}")
        # Try alternate column names
        return 0

def verify_all(conn):
    """Verify all inserts."""
    tables = [
        ('evidence_quotes', None),
        ('impeachment_matrix', None),
        ('judicial_violations', None),
        ('michigan_rules_extracted', None),
    ]
    
    print("\n=== VERIFICATION ===")
    for table, _ in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {count} total rows")
    
    # Show recent inserts
    print("\n=== RECENT EVIDENCE_QUOTES (last 15) ===")
    rows = conn.execute(
        "SELECT rowid, substr(quote_text, 1, 80), category, lane FROM evidence_quotes ORDER BY rowid DESC LIMIT 15"
    ).fetchall()
    for r in rows:
        print(f"  [{r[0]}] {r[1]}... | cat={r[2]} | lane={r[3]}")
    
    print("\n=== RECENT IMPEACHMENT_MATRIX (last 10) ===")
    rows = conn.execute(
        "SELECT rowid, category, substr(quote_text, 1, 60), impeachment_value FROM impeachment_matrix ORDER BY rowid DESC LIMIT 10"
    ).fetchall()
    for r in rows:
        print(f"  [{r[0]}] {r[1]}: {r[2]}... | value={r[3]}")


def main():
    print("=" * 60)
    print("AGENT HARVEST PERSISTENCE — April 2026")
    print("=" * 60)
    
    conn = get_conn()
    
    total = 0
    total += persist_mcneill_quotes(conn)
    total += persist_mcneill_impeachment(conn)
    total += persist_berry_connections(conn)
    total += persist_violation_stats(conn)
    total += persist_jtic_filing_requirements(conn)
    total += persist_mcr_filing_deadlines(conn)
    total += persist_mcr_violations_to_judicial(conn)
    
    verify_all(conn)
    
    print(f"\n{'=' * 60}")
    print(f"TOTAL: {total} new rows persisted across all tables")
    print(f"{'=' * 60}")
    
    conn.close()

if __name__ == "__main__":
    main()
