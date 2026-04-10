"""
Persist smoking-gun email evidence to impeachment_matrix for cross-exam use.
Adds actor, context, impeachment_value, and filing_relevance data.
"""
import sqlite3
import datetime

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

today = datetime.date.today()
anchor = datetime.date(2025, 7, 29)
sep_days = (today - anchor).days

IMPEACHMENT_ENTRIES = [
    # Rusco
    ("Pamela Rusco", "Requested bench warrant officer issue arrest warrant for Andrew", "email_evidence #832", "Can you please issue a warrant for him?", 10, "Warrant request to Jamie Hooker, CC'd Martini. McNeill's secretary pursuing criminal action against pro se litigant. Mar 3, 2025.", "F01,F05,F06", "Mar 3, 2025"),
    ("Pamela Rusco", "Refused to accept Andrew's exhibit filings", "email_evidence #931", "I do not accept filing of exhibits", 9, "Gatekeeping evidence from the record. Pattern of blocking pro se access. Oct 28, 2024.", "F01,F05,F06", "Oct 28, 2024"),
    ("Pamela Rusco", "Coordinated with Circuit Court Records to block exhibits", "email_evidence #1183", "Blocked exhibit submission through records department", 9, "Systematic coordination to prevent Andrew's evidence from entering the court record. Oct 9, 2024.", "F01,F05,F06", "Oct 9, 2024"),
    ("Pamela Rusco", "Denied access to hearing audio recordings", "email_evidence #1224", "There is no way to request an audio recording of the hearing", 9, "Combined with $2.05/page transcript cost and no fee waiver — systematic denial of appellate record. Jan 8, 2025.", "F01,F05,F06,F09", "Jan 8, 2025"),
    ("Pamela Rusco", "Communicated HealthWest exclusion order", "email_evidence #1338", "Judge McNeill issued her order on this matter today", 10, "McNeill excluded court-ordered HealthWest evaluation that found Father FIT (LOCUS 12). Rusco was the conduit. Sep 9, 2025.", "F01,F05,F06,F09", "Sep 9, 2025"),

    # Barnes
    ("Jennifer Barnes", "Ex parte coordination with Rusco to reject Andrew's filings", "email_evidence #332", "I am asking you to reject the email communication", 10, "Barnes emailed Rusco directly asking to reject Andrew's communications. Opposing counsel coordinating with judge's secretary. Jun 5, 2024.", "F01,F04,F05,F06", "Jun 5, 2024"),
    ("Jennifer Barnes", "Blanket discovery refusal — no motion for protective order", "email_evidence #320", "I will not be complying with your request", 9, "Refused all discovery without filing proper MCR 2.302 protective order motion. Jun 5, 2024.", "F01,F04,F05,F09", "Jun 5, 2024"),
    ("Jennifer Barnes", "Gaslighting denial after documented ex parte coordination", "email_evidence #1396", "I have not lied to you. Not once.", 8, "9-point gaslighting email contradicted by her own email #332 to Rusco. Jul 10, 2024.", "F01,F04,F05", "Jul 10, 2024"),
    ("Jennifer Barnes", "Subpoenaed Shady Oaks — connects custody to housing", "email_evidence #641", "Subpoena of Shady Oaks records by custody attorney", 8, "Custody attorney subpoenaed housing records — proves cross-lane connection between custody and housing cases. Jun 24, 2024.", "F01,F04,F05", "Jun 24, 2024"),

    # Martini
    ("Mandi Martini", "Refused to file client's legal work product", "email_evidence #1318", "I cannot present my client's non-professional legal work as my own", 8, "Public defender refused Andrew's Master Brief. Deprived client of effective representation. May 16, 2025.", "F04,F05", "May 16, 2025"),
    ("Mandi Martini", "Relayed McNeill's sanctions threat via court staff", "email_evidence #1315", "Leo said the judge told you not to file anything else frivolous with the Court or she would fine you", 9, "Secondhand relay of McNeill's threat to sanction for filing. Chilling effect on 1st Amendment access to courts. May 16, 2025.", "F01,F05,F06", "May 16, 2025"),
    ("Mandi Martini", "Advised against alleging judicial bias AND mentioning Ron Berry", "email_evidence #1145", "I would be cautious about alleging bias to the court", 9, "Muzzled Andrew's defense strategy. Also said not to mention Ron Berry. Effectively suppressed key arguments. Jun 5, 2025.", "F05,F06", "Jun 5, 2025"),
    ("Mandi Martini", "Dismissed 14 days incarceration as invalid reason for attorney change", "email_evidence #208", "sitting in jail for 14 days is not a valid reason", 8, "Public defender dismissed client's incarceration as basis for substitution. May 14, 2025.", "F04,F05", "May 14, 2025"),
    ("Mandi Martini", "Refused constitutional objections, called defenses 'patently false'", "email_evidence #1148", "Refuses constitutional objections, finds defenses patently false and unsupported", 8, "PD characterized client's constitutional arguments as unsupported. Jun 5, 2025.", "F04,F05", "Jun 5, 2025"),

    # McNeill direct
    ("Judge Jenny L. McNeill", "Denied access to courts", "user_testimony (hearing)", "Do not file anymore, I will not look at it", 10, "Direct denial of 1st Amendment right to petition. Said verbatim during hearing on parenting time suspension.", "F01,F04,F05,F06,F09", None),
    ("Judge Jenny L. McNeill", "Contempt for objecting to medication coercion", "user_testimony (4th continued hearing)", "shut my mouth", 10, f"Told Andrew to shut his mouth when he objected to McNeill and Emily discussing mandatory medication as condition for seeing L.D.W. Jailed 2 weeks for contempt of this.", "F01,F04,F05,F06,F09", None),
    ("Judge Jenny L. McNeill", "Imposed $250 filing deposit on pro se litigant", "email_evidence #1313 (via Martini)", "$250 filing fee deposit", 8, "Financial barrier to court access for indigent pro se party. May 26, 2025.", "F01,F05,F06", "May 26, 2025"),

    # Albert Watson
    ("Albert Watson", "Premeditated ex parte custody grab — admitted to police", "NSPD NS2505044", "They want this documented so Emily can go tomorrow to get an Ex Parte order for full custody of her son", 10, "Aug 7, 2025 report to police → Aug 8, 2025 FIVE ex parte orders. Premeditation proven on the record.", "F01,F04,F05,F06,F09", "Aug 7, 2025"),

    # Emily
    ("Emily A. Watson", "Father replacement — Instagram family portrait with Ron Berry", "user_testimony (Instagram post)", f"Family portrait: Emily, L.D.W., her other son, and Ron Berry — replacing Andrew as father figure. Separation: {sep_days} days.", 10, f"Parental alienation evidence. MCL 722.23(j). L.D.W. separated from father for {sep_days} days while Emily publicly presents Berry as replacement.", "F01,F05,F09", None),

    # Housing
    ("Shady Oaks Park MHP LLC", "Intentionally diverted MDHHS payment to create eviction pretext", "email_evidence (MDHHS investigation)", "Changed LLC and sigma account to AVOID receiving $2,000 payment", 10, "MDHHS found Shady Oaks deliberately changed corporate entity and payment account so Andrew's assistance payment couldn't be received — then evicted for 'nonpayment.'", "F02,F04", None),
    ("Shady Oaks Park MHP LLC", "Predatory billing — charges tripled while evicted", "email_evidence (Zego statements)", "Oct 2024: $2,207.91 → Jun 2025: $6,774.67 — 3x increase in 8 months", 9, "Continued billing and tripling charges after eviction. Andrew not even living there.", "F02,F04", None),
    ("Shady Oaks Park MHP LLC", "Illegally operating since 2022 per LARA", "email_evidence (LARA research)", "Shady Oaks MHP LLC hasn't been legal to operate in Michigan since 2022", 10, "Corporate registration lapsed 2022. Continued collecting rent without legal authority to operate.", "F02,F04", None),
]

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")

    # Check impeachment_matrix schema
    cols = {r[1] for r in conn.execute("PRAGMA table_info(impeachment_matrix)")}
    print(f"impeachment_matrix columns: {sorted(cols)}")

    if not cols:
        print("ERROR: impeachment_matrix table not found!")
        conn.close()
        return

    # Build insert based on available columns
    # Standard impeachment_matrix columns from prior sessions
    inserted = 0
    skipped = 0

    for entry in IMPEACHMENT_ENTRIES:
        target, evidence_summary, source_file, quote_text, imp_value, cross_exam_q, filing_rel, event_date = entry

        # Check for duplicate
        existing = conn.execute(
            "SELECT COUNT(*) FROM impeachment_matrix WHERE quote_text = ? AND category = ?",
            (quote_text, target)
        ).fetchone()[0]

        if existing > 0:
            skipped += 1
            continue

        try:
            conn.execute("""
                INSERT INTO impeachment_matrix 
                (category, evidence_summary, source_file, quote_text, impeachment_value, 
                 cross_exam_question, filing_relevance, event_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (target, evidence_summary, source_file, quote_text, imp_value, cross_exam_q, filing_rel, event_date))
            inserted += 1
        except Exception as e:
            print(f"  ERROR: {e} for '{quote_text[:40]}...'")

    conn.commit()

    # Verify
    total = conn.execute("SELECT COUNT(*) FROM impeachment_matrix").fetchone()[0]
    print(f"\n=== RESULTS ===")
    print(f"Attempted: {len(IMPEACHMENT_ENTRIES)}")
    print(f"Inserted: {inserted}")
    print(f"Skipped (duplicates): {skipped}")
    print(f"Total impeachment_matrix: {total}")

    conn.close()
    print("\nDone.")

if __name__ == "__main__":
    main()
