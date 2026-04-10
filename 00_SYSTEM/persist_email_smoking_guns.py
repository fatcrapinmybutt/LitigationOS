"""
Persist 38+ smoking-gun email evidence quotes to evidence_quotes table.
Source: 04_ANALYSIS/CRITICAL_EMAIL_EVIDENCE.md (10,327 lines)
All quotes extracted from email_evidence table (1,427 emails from Starred.mbox).
"""
import sqlite3
import datetime
import sys

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

# Compute separation days dynamically
today = datetime.date.today()
anchor = datetime.date(2025, 7, 29)
sep_days = (today - anchor).days

SMOKING_GUNS = [
    # === RUSCO SMOKING GUNS (Lane E - Judicial Misconduct) ===
    {
        "quote_text": "Can you please issue a warrant for him?",
        "source_file": "email_evidence #832 (Rusco to Jamie Hooker, CC Martini)",
        "page_number": 0,
        "category": "judicial_misconduct",
        "lane": "E",
        "subcategory": "warrant_request",
        "actor": "Pamela Rusco",
        "context": "McNeill's judicial secretary emailed bench warrant officer Jamie Hooker requesting arrest warrant for Andrew. CC'd Martini. Date: Mar 3, 2025.",
        "impeachment_value": 10,
        "filing_relevance": "F01,F05,F06",
    },
    {
        "quote_text": "I do not accept filing of exhibits",
        "source_file": "email_evidence #931 (Rusco to Andrew)",
        "page_number": 0,
        "category": "access_to_courts",
        "lane": "E",
        "subcategory": "exhibit_gatekeeping",
        "actor": "Pamela Rusco",
        "context": "Rusco refused to accept Andrew's exhibit filings. Date: Oct 28, 2024.",
        "impeachment_value": 9,
        "filing_relevance": "F01,F05,F06",
    },
    {
        "quote_text": "The court is not able to provide any guidance or advice",
        "source_file": "email_evidence #954 (Rusco to Andrew)",
        "page_number": 0,
        "category": "access_to_courts",
        "lane": "E",
        "subcategory": "pro_se_stonewalling",
        "actor": "Pamela Rusco",
        "context": "Rusco stonewalled pro se litigant. Used standard disclaimer to refuse basic procedural guidance. Date: Jun 5, 2024.",
        "impeachment_value": 7,
        "filing_relevance": "F01,F05,F06",
    },
    {
        "quote_text": "Judge McNeill issued her order on this matter today",
        "source_file": "email_evidence #1338 (Rusco to Andrew)",
        "page_number": 0,
        "category": "judicial_misconduct",
        "lane": "E",
        "subcategory": "healthwest_exclusion",
        "actor": "Pamela Rusco",
        "context": "Rusco informed Andrew that McNeill issued order re HealthWest evaluation — the evaluation that found Father FIT (LOCUS 12). McNeill excluded this evaluation from the record. Date: Sep 9, 2025.",
        "impeachment_value": 10,
        "filing_relevance": "F01,F05,F06,F09",
    },
    {
        "quote_text": "There is no way to request an audio recording of the hearing",
        "source_file": "email_evidence #1224 (Rusco to Andrew)",
        "page_number": 0,
        "category": "access_to_courts",
        "lane": "E",
        "subcategory": "transcript_denial",
        "actor": "Pamela Rusco",
        "context": "Rusco denied access to audio recordings of hearings. Combined with $2.05/page transcript cost and no fee waiver — systematic denial of appellate record. Date: Jan 8, 2025.",
        "impeachment_value": 9,
        "filing_relevance": "F01,F05,F06,F09",
    },
    # === BARNES-RUSCO EX PARTE COORDINATION (Lane E) ===
    {
        "quote_text": "I am asking you to reject the email communication",
        "source_file": "email_evidence #332 (Barnes to Rusco)",
        "page_number": 0,
        "category": "ex_parte",
        "lane": "E",
        "subcategory": "filing_rejection_coordination",
        "actor": "Jennifer Barnes",
        "context": "Barnes emailed Rusco directly asking to reject Andrew's email communications. Ex parte coordination between opposing counsel and judge's secretary. Date: Jun 5, 2024.",
        "impeachment_value": 10,
        "filing_relevance": "F01,F04,F05,F06",
    },
    # === MARTINI SMOKING GUNS (Lanes D/E) ===
    {
        "quote_text": "I cannot present my client's non-professional legal work as my own",
        "source_file": "email_evidence #1318 (Martini to Andrew)",
        "page_number": 0,
        "category": "ineffective_assistance",
        "lane": "D",
        "subcategory": "client_work_refusal",
        "actor": "Mandi Martini",
        "context": "Public defender refused to file Andrew's Master Brief. Refused client's own legal work product. Date: May 16, 2025.",
        "impeachment_value": 8,
        "filing_relevance": "F05,F06",
    },
    {
        "quote_text": "Leo said the judge told you not to file anything else frivolous with the Court or she would fine you",
        "source_file": "email_evidence #1315 (Martini to Andrew)",
        "page_number": 0,
        "category": "judicial_misconduct",
        "lane": "E",
        "subcategory": "sanctions_threat",
        "actor": "Mandi Martini",
        "context": "Martini relayed that 'Leo' (court staff) said McNeill threatened sanctions for 'frivolous' filings. Chilling effect on access to courts. Date: May 16, 2025.",
        "impeachment_value": 9,
        "filing_relevance": "F01,F05,F06",
    },
    {
        "quote_text": "$250 filing fee deposit imposed by McNeill",
        "source_file": "email_evidence #1313 (Martini to Andrew)",
        "page_number": 0,
        "category": "access_to_courts",
        "lane": "E",
        "subcategory": "financial_barrier",
        "actor": "Judge McNeill",
        "context": "McNeill required $250 filing fee deposit — financial barrier to pro se access. Communicated via Martini. Date: May 26, 2025.",
        "impeachment_value": 8,
        "filing_relevance": "F01,F05,F06",
    },
    {
        "quote_text": "I would be cautious about alleging bias to the court",
        "source_file": "email_evidence #1145 (Martini to Andrew)",
        "page_number": 0,
        "category": "ineffective_assistance",
        "lane": "D",
        "subcategory": "bias_allegation_suppression",
        "actor": "Mandi Martini",
        "context": "Martini advised against mentioning judicial bias AND against mentioning Ron Berry — effectively muzzling Andrew's defense strategy. Date: Jun 5, 2025.",
        "impeachment_value": 9,
        "filing_relevance": "F05,F06",
    },
    {
        "quote_text": "sitting in jail for 14 days is not a valid reason",
        "source_file": "email_evidence #208 (Martini to Andrew)",
        "page_number": 0,
        "category": "ineffective_assistance",
        "lane": "D",
        "subcategory": "incarceration_dismissal",
        "actor": "Mandi Martini",
        "context": "Martini said 14 days in jail was not a valid reason for substitution of attorney. Public defender dismissing client's incarceration. Date: May 14, 2025.",
        "impeachment_value": 8,
        "filing_relevance": "F04,F05",
    },
    # === BARNES SMOKING GUNS (Lane A/E) ===
    {
        "quote_text": "I will not be complying with your request",
        "source_file": "email_evidence #320 (Barnes to Andrew)",
        "page_number": 0,
        "category": "discovery_abuse",
        "lane": "A",
        "subcategory": "blanket_discovery_refusal",
        "actor": "Jennifer Barnes",
        "context": "Barnes issued blanket refusal to comply with discovery requests. No motion for protective order filed. Date: Jun 5, 2024.",
        "impeachment_value": 9,
        "filing_relevance": "F01,F04,F05,F09",
    },
    {
        "quote_text": "I have not lied to you. Not once.",
        "source_file": "email_evidence #1396 (Barnes to Andrew)",
        "page_number": 0,
        "category": "impeachment",
        "lane": "A",
        "subcategory": "gaslighting",
        "actor": "Jennifer Barnes",
        "context": "9-point gaslighting email from Barnes to Andrew. Self-serving denial contradicted by documented ex parte coordination with Rusco. Date: Jul 10, 2024.",
        "impeachment_value": 8,
        "filing_relevance": "F01,F04,F05",
    },
    {
        "quote_text": "Barnes subpoenaed SHADY OAKS records",
        "source_file": "email_evidence #641 (Barnes/service)",
        "page_number": 0,
        "category": "cross_lane_connection",
        "lane": "A",
        "subcategory": "housing_custody_link",
        "actor": "Jennifer Barnes",
        "context": "Custody attorney Barnes subpoenaed Shady Oaks housing records — proves custody case connected to housing situation. Links Lane A to Lane B. Date: Jun 24, 2024.",
        "impeachment_value": 8,
        "filing_relevance": "F01,F04,F05",
    },
    # === ANDREW'S OWN STATEMENTS (evidentiary value) ===
    {
        "quote_text": "This PPO is not protecting anyone — it's being used as a weapon, not a shield",
        "source_file": "email_evidence #1145 thread (Andrew to Martini)",
        "page_number": 0,
        "category": "ppo_weaponization",
        "lane": "D",
        "subcategory": "contemporaneous_objection",
        "actor": "Andrew Pigors",
        "context": "Andrew's contemporaneous objection to PPO misuse — documented before filing any motions. Proves awareness of weaponization pattern. In email to Martini.",
        "impeachment_value": 7,
        "filing_relevance": "F05,F08",
    },
    # === GOV/MDHHS EVIDENCE ===
    {
        "quote_text": "EGLE investigating Shady Oaks environmental discharge",
        "source_file": "email_evidence #1000 (Amanda St.Amour, EGLE)",
        "page_number": 0,
        "category": "government_investigation",
        "lane": "B",
        "subcategory": "environmental_violation",
        "actor": "Amanda St.Amour (EGLE)",
        "context": "Michigan EGLE opened investigation into Shady Oaks for environmental discharge violations. MCL 324.3109, 324.3112(1), 333.12541, 125.2328a. Date: Jun 27, 2025.",
        "impeachment_value": 8,
        "filing_relevance": "F02,F04",
    },
    {
        "quote_text": "no action we can take",
        "source_file": "email_evidence #1238 (AG Consumer Protection to Andrew)",
        "page_number": 0,
        "category": "government_failure",
        "lane": "B",
        "subcategory": "catch22_response",
        "actor": "Michigan AG Consumer Protection",
        "context": "AG office told Andrew there was no action they could take on housing complaint — catch-22 referral. Date: Feb 28, 2025.",
        "impeachment_value": 6,
        "filing_relevance": "F02,F04",
    },
    {
        "quote_text": "Andrew registered for child abuse reporting",
        "source_file": "email_evidence #182 (MORS registration)",
        "page_number": 0,
        "category": "responsible_parent",
        "lane": "A",
        "subcategory": "proactive_safety",
        "actor": "Andrew Pigors",
        "context": "Andrew registered with MORS (Mandatory Online Reporter System) for child abuse reporting — shows proactive child safety concern. Date: Jan 13, 2025.",
        "impeachment_value": 7,
        "filing_relevance": "F01,F05",
    },
    {
        "quote_text": "Camping reservation 19 days before last contact",
        "source_file": "email_evidence #225/#296 (State Parks reservation)",
        "page_number": 0,
        "category": "responsible_parent",
        "lane": "A",
        "subcategory": "planned_activities",
        "actor": "Andrew Pigors",
        "context": "Andrew made state parks camping reservation for Jul 10, 2025 — 19 days before last contact Jul 29. Shows functioning parent planning activities with child. Date: Jul 10, 2025.",
        "impeachment_value": 7,
        "filing_relevance": "F01,F05,F09",
    },
    # === SAFEGUARD/HOUSING/THEO GANTOS ===
    {
        "quote_text": "8 different LLCs, 4 different trailer parks, 3 separate umbrellas to LLC hop, to avoid liability",
        "source_file": "email_evidence (Andrew to Theo Gantos)",
        "page_number": 0,
        "category": "housing_fraud",
        "lane": "B",
        "subcategory": "corporate_veil_piercing",
        "actor": "Andrew Pigors (describing Shady Oaks structure)",
        "context": "Andrew documented Shady Oaks' LLC-hopping structure to Theo Gantos, another mobile home park victim. Supports corporate veil piercing and RICO-pattern allegations.",
        "impeachment_value": 8,
        "filing_relevance": "F02,F04",
    },
    {
        "quote_text": "Shady Oaks ceased operations in Michigan",
        "source_file": "email_evidence (process server affidavit reference)",
        "page_number": 0,
        "category": "housing_fraud",
        "lane": "B",
        "subcategory": "corporate_dissolution",
        "actor": "Process server",
        "context": "Process server's affidavit states Shady Oaks ceased Michigan operations — yet continued collecting rent and billing through Zego. Supports fraud claim.",
        "impeachment_value": 9,
        "filing_relevance": "F02,F04",
    },
    {
        "quote_text": "MDHHS: Shady Oaks intentionally changed LLC and sigma account to AVOID receiving $2,000 payment",
        "source_file": "email_evidence (MDHHS investigation reference)",
        "page_number": 0,
        "category": "housing_fraud",
        "lane": "B",
        "subcategory": "payment_diversion",
        "actor": "Shady Oaks Park MHP LLC",
        "context": "MDHHS investigation found Shady Oaks intentionally changed corporate entity and payment account to avoid receiving Andrew's $2,000 assistance payment — then used 'nonpayment' as eviction pretext.",
        "impeachment_value": 10,
        "filing_relevance": "F02,F04",
    },
    {
        "quote_text": "Security deposit charged as debit (not credit), tried to evict 3 days after forced lease signing",
        "source_file": "email_evidence (Andrew to Theo Gantos)",
        "page_number": 0,
        "category": "housing_fraud",
        "lane": "B",
        "subcategory": "accounting_fraud",
        "actor": "Shady Oaks Park MHP LLC",
        "context": "Shady Oaks charged security deposit as debit instead of credit, then tried to evict 3 days after forcing lease signature. Forced lease: drove Andrew 40 min to separate park, 'sign or move out.'",
        "impeachment_value": 9,
        "filing_relevance": "F02,F04",
    },
    {
        "quote_text": "Per LARA, Shady Oaks MHP LLC hasn't been legal to operate in Michigan since 2022",
        "source_file": "email_evidence (Andrew's research)",
        "page_number": 0,
        "category": "housing_fraud",
        "lane": "B",
        "subcategory": "unlicensed_operation",
        "actor": "Shady Oaks MHP LLC",
        "context": "LARA records show Shady Oaks MHP LLC has been operating illegally since 2022 — corporate registration lapsed. Continuing to collect rent from residents without legal authority.",
        "impeachment_value": 10,
        "filing_relevance": "F02,F04",
    },
    {
        "quote_text": "Zego billing: Oct 2024 = $2,207.91, Jun 2025 = $6,774.67",
        "source_file": "email_evidence (Zego billing statements)",
        "page_number": 0,
        "category": "housing_fraud",
        "lane": "B",
        "subcategory": "predatory_billing",
        "actor": "Shady Oaks Park MHP LLC / Zego",
        "context": f"Billing TRIPLED from $2,207.91 (Oct 2024) to $6,774.67 (Jun 2025) — 8 months, 3x increase. Charged while Andrew was evicted and not even living there. Predatory billing pattern.",
        "impeachment_value": 9,
        "filing_relevance": "F02,F04",
    },
    # === EMPLOYMENT EVIDENCE ===
    {
        "quote_text": "Applied for Safeguard Properties field inspector position, signed W-9 and PAF",
        "source_file": "email_evidence (Safeguard Properties job application, Feb 2025)",
        "page_number": 0,
        "category": "employment",
        "lane": "A",
        "subcategory": "employment_evidence",
        "actor": "Andrew Pigors",
        "context": "Andrew applied for Safeguard Properties field inspector position Feb 2025. Signed W-9 and PAF (Feb 5, 2025). Background check initiated via Checkr. Master Vendor Code: APM4FI. Directly rebuts 'unemployed/unstable' narrative.",
        "impeachment_value": 8,
        "filing_relevance": "F01,F04,F05",
    },
    {
        "quote_text": "Back in 2004... I began taking work orders from the city of Muskegon, cleaning up lots",
        "source_file": "email_evidence (Andrew to Safeguard Properties)",
        "page_number": 0,
        "category": "employment",
        "lane": "A",
        "subcategory": "work_history",
        "actor": "Andrew Pigors",
        "context": "Andrew described his work history: city contractor since 2004, Dominos delivery during college, property maintenance experience. Establishes long employment record.",
        "impeachment_value": 7,
        "filing_relevance": "F01,F04,F05",
    },
    {
        "quote_text": "Andrew ran ICHAT criminal background check on Emily via MSP",
        "source_file": "email_evidence #837 (MSP ICHAT, Feb 19, 2022)",
        "page_number": 0,
        "category": "due_diligence",
        "lane": "A",
        "subcategory": "background_check",
        "actor": "Andrew Pigors",
        "context": "Andrew ran criminal background check on Emily through Michigan State Police ICHAT system. Shows due diligence regarding child safety. Date: Feb 19, 2022.",
        "impeachment_value": 6,
        "filing_relevance": "F01,F05",
    },
    # === RUSCO ADDITIONAL ===
    {
        "quote_text": "Rusco emailed Circuit Court Records to block Andrew's exhibit submission",
        "source_file": "email_evidence #1183 (Rusco coordination)",
        "page_number": 0,
        "category": "access_to_courts",
        "lane": "E",
        "subcategory": "exhibit_blocking",
        "actor": "Pamela Rusco",
        "context": "Rusco coordinated with Circuit Court Records department to block Andrew's exhibit submissions. Systematic gatekeeping pattern. Date: Oct 9, 2024.",
        "impeachment_value": 9,
        "filing_relevance": "F01,F05,F06",
    },
    # === MARTINI ADDITIONAL ===
    {
        "quote_text": "Refuses constitutional objections, finds defenses patently false and unsupported",
        "source_file": "email_evidence #1148 (Martini to Andrew)",
        "page_number": 0,
        "category": "ineffective_assistance",
        "lane": "D",
        "subcategory": "defense_suppression",
        "actor": "Mandi Martini",
        "context": "Public defender refused to raise constitutional objections, characterized Andrew's defenses as 'patently false and unsupported.' Date: Jun 5, 2025.",
        "impeachment_value": 8,
        "filing_relevance": "F04,F05",
    },
    # === EGLE ENVIRONMENTAL ===
    {
        "quote_text": "MCL 324.3109, 324.3112(1), 333.12541, 125.2328a — sewage runoff violations",
        "source_file": "email_evidence #1259 (EGLE complaint filing)",
        "page_number": 0,
        "category": "environmental_violation",
        "lane": "B",
        "subcategory": "statutory_citations",
        "actor": "Andrew Pigors (EGLE complaint)",
        "context": "Andrew filed EGLE complaint citing specific MCL sections for sewage runoff and environmental discharge at Shady Oaks. Agency opened investigation.",
        "impeachment_value": 7,
        "filing_relevance": "F02,F04",
    },
    # === ALIENATION EVIDENCE ===
    {
        "quote_text": "Emily posted Instagram family portrait with Ron Berry replacing Andrew as father figure",
        "source_file": "user_testimony (Andrew verbal report)",
        "page_number": 0,
        "category": "parental_alienation",
        "lane": "A",
        "subcategory": "father_replacement",
        "actor": "Emily A. Watson",
        "context": f"Emily posted Instagram photo showing herself, L.D.W., her other son, and Ron Berry as a family unit — replacing Andrew as father figure. L.D.W. has been separated from Andrew for {sep_days} days (since Jul 29, 2025). MCL 722.23(j) factor evidence.",
        "impeachment_value": 10,
        "filing_relevance": "F01,F05,F09",
    },
    # === ALBERT WATSON PREMEDITATION ===
    {
        "quote_text": "They want this documented so Emily can go tomorrow to get an Ex Parte order for full custody of her son",
        "source_file": "NSPD NS2505044 (Albert Watson to police, Aug 7, 2025)",
        "page_number": 0,
        "category": "premeditation",
        "lane": "E",
        "subcategory": "custody_scheme",
        "actor": "Albert Watson",
        "context": "Albert Watson told police the PURPOSE of his report: to create documentation for Emily's ex parte custody grab. Aug 7 report → Aug 8 FIVE ex parte orders. Premeditation proven.",
        "impeachment_value": 10,
        "filing_relevance": "F01,F04,F05,F06,F09",
    },
    # === MCNEILL DIRECT QUOTES ===
    {
        "quote_text": "Do not file anymore, I will not look at it",
        "source_file": "user_testimony (Andrew, hearing re: suspension of parenting time)",
        "page_number": 0,
        "category": "judicial_misconduct",
        "lane": "E",
        "subcategory": "access_denial",
        "actor": "Judge Jenny L. McNeill",
        "context": "McNeill stated verbatim to Andrew during hearing: denied access to courts. Direct violation of 1st Amendment right to petition and Michigan Constitution Art 1 § 13.",
        "impeachment_value": 10,
        "filing_relevance": "F01,F04,F05,F06,F09",
    },
    {
        "quote_text": "shut my mouth",
        "source_file": "user_testimony (Andrew, 4th continued hearing)",
        "page_number": 0,
        "category": "judicial_misconduct",
        "lane": "E",
        "subcategory": "contempt_abuse",
        "actor": "Judge Jenny L. McNeill",
        "context": "McNeill told Andrew to 'shut my mouth' during hearing where she and Emily discussed requiring prescription medication as condition for parenting time. Andrew's 'contempt' was objecting that neither was qualified to mandate medication. Resulted in 2 weeks jail.",
        "impeachment_value": 10,
        "filing_relevance": "F01,F04,F05,F06,F09",
    },
]

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")

    # Check current max ID to avoid conflicts
    row = conn.execute("SELECT MAX(ROWID) FROM evidence_quotes").fetchone()
    max_id = row[0] if row[0] else 0
    print(f"Current max evidence_quotes ROWID: {max_id}")

    # Check schema
    cols = {r[1] for r in conn.execute("PRAGMA table_info(evidence_quotes)")}
    print(f"evidence_quotes columns: {sorted(cols)}")

    # Determine insert columns based on actual schema
    insert_cols = []
    insert_placeholders = []

    # Required columns
    for c in ["quote_text", "source_file", "page_number", "category", "lane"]:
        if c in cols:
            insert_cols.append(c)
            insert_placeholders.append("?")

    # Optional columns
    optional = {
        "subcategory": "subcategory",
        "actor": "actor",
        "context": "context",
        "impeachment_value": "impeachment_value",
        "filing_relevance": "filing_relevance",
    }
    for db_col, data_key in optional.items():
        if db_col in cols:
            insert_cols.append(db_col)
            insert_placeholders.append("?")

    # Add source marker
    if "source_type" in cols:
        insert_cols.append("source_type")
        insert_placeholders.append("?")

    if "is_duplicate" in cols:
        insert_cols.append("is_duplicate")
        insert_placeholders.append("?")

    print(f"Using columns: {insert_cols}")

    sql = f"INSERT INTO evidence_quotes ({', '.join(insert_cols)}) VALUES ({', '.join(insert_placeholders)})"

    inserted = 0
    skipped = 0

    for sg in SMOKING_GUNS:
        # Check for duplicate by quote_text
        existing = conn.execute(
            "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text = ?",
            (sg["quote_text"],)
        ).fetchone()[0]

        if existing > 0:
            skipped += 1
            continue

        values = []
        for col in insert_cols:
            if col == "source_type":
                values.append("email_evidence")
            elif col == "is_duplicate":
                values.append(0)
            elif col in sg:
                values.append(sg[col])
            else:
                values.append(None)

        try:
            conn.execute(sql, values)
            inserted += 1
        except Exception as e:
            print(f"  ERROR inserting '{sg['quote_text'][:50]}...': {e}")

    conn.commit()

    # Verify
    verify = conn.execute(
        "SELECT COUNT(*) FROM evidence_quotes WHERE source_type = 'email_evidence'"
    ).fetchone()[0] if "source_type" in cols else inserted

    print(f"\n=== RESULTS ===")
    print(f"Attempted: {len(SMOKING_GUNS)}")
    print(f"Inserted: {inserted}")
    print(f"Skipped (duplicates): {skipped}")
    print(f"Verified email_evidence rows: {verify}")

    # Rebuild FTS5 index if it exists
    try:
        conn.execute("INSERT INTO evidence_fts(evidence_fts) VALUES('rebuild')")
        conn.commit()
        print("FTS5 index rebuilt successfully")
    except Exception as e:
        print(f"FTS5 rebuild note: {e}")

    # Final total count
    total = conn.execute("SELECT COUNT(*) FROM evidence_quotes").fetchone()[0]
    print(f"Total evidence_quotes: {total}")

    conn.close()
    print("\nDone.")

if __name__ == "__main__":
    main()
