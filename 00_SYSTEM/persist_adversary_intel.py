"""Persist user testimony + adversary intelligence to litigation_context.db.
Run via: python -I D:\LitigationOS_tmp\persist_adversary_intel.py
"""
import sqlite3, datetime, hashlib

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"

def connect():
    conn = sqlite3.connect(DB, timeout=60)
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    conn.text_factory = lambda b: b.decode('utf-8', errors='replace')
    return conn

def content_hash(text):
    return hashlib.sha256(text.encode('utf-8', errors='replace')).hexdigest()[:16]

ROWS = [
    # === USER TESTIMONY (Rule 13 — persist IMMEDIATELY) ===
    {
        "source_file": "USER_TESTIMONY_SESSION_2026-04-14",
        "quote_text": (
            "Andrew Pigors testimony: I failed to turn myself in because the jail date "
            "landed on my parenting time week, and I wanted to see my son, because I knew "
            "that Emily was trying to take him away from me. I wanted to spend as much time "
            "as I could with him. This was the basis for Rusco requesting the arrest warrant "
            "from Prosecutor Jamie Hooker on March 3, 2025."
        ),
        "category": "testimony",
        "lane": "A",
        "relevance_score": 1.0,
        "tags": "parenting_time,contempt,jail,warrant,rusco,self_surrender,custody_fear,user_testimony",
    },
    {
        "source_file": "USER_TESTIMONY_SESSION_2026-04-14",
        "quote_text": (
            "Andrew Pigors testimony: All of the filings that Judge McNeill labeled 'frivolous' "
            "detailed the things Emily Watson had done and was going to do, and that I had "
            "evidence proving it and wanted to show the evidence. The filings were substantive "
            "motions with evidentiary support, not frivolous. McNeill used the 'frivolous' label "
            "to suppress legitimate complaints about Emily Watson's misconduct and to threaten "
            "sanctions against Andrew for exercising his right to access the courts."
        ),
        "category": "testimony",
        "lane": "E",
        "relevance_score": 1.0,
        "tags": "frivolous_label,access_to_courts,mcneill,suppression,evidence_exclusion,sanctions_threat,user_testimony",
    },
    {
        "source_file": "USER_TESTIMONY_SESSION_2026-04-14",
        "quote_text": (
            "Andrew Pigors testimony: I got 2 evidentiary hearings total, and each time the "
            "judge COMPLETELY ignored my evidence, did not even mention anything in her orders, "
            "only twisted my words to fit her narrative. Despite presenting evidence at both "
            "hearings, Judge McNeill's orders contained zero reference to Father's exhibits or "
            "testimony, while selectively citing Mother's claims. The orders recharacterized "
            "Andrew's statements to support predetermined conclusions."
        ),
        "category": "testimony",
        "lane": "E",
        "relevance_score": 1.0,
        "tags": "evidentiary_hearing,evidence_exclusion,mcneill,twisted_words,biased_orders,selective_citation,user_testimony",
    },

    # === ADVERSARY INTELLIGENCE: RUSCO (harvested this session) ===
    {
        "source_file": "ADVERSARY_INTEL_SESSION_2026-04-14_RUSCO",
        "quote_text": (
            "RUSCO WARRANT EMAIL VERBATIM (March 3, 2025, 8:51 AM): From: Rusco, Pamela. "
            "To: Hooker, Jamie. CC: Duguid, Lauren; Bramble, Kevin; Martini, Mandi. "
            "Subject: Andrew Pigors. 'Good Morning Jamie, Andrew Pigors was ordered to turn "
            "himself in to the Jail by 5pm on Friday to serve his 14 days in jail for the PPO "
            "Violation. I confirmed with the jail this morning and he did not turn himself in. "
            "Can you please issue a warrant for him? Attached are both the order after hearing "
            "and the jail mittimus.' — This warrant was FOR ANDREW. Rusco (judge's secretary) "
            "initiated criminal proceedings against a pro se litigant. Martini (Andrew's own "
            "appointed attorney) was CC'd and did NOTHING to protect her client."
        ),
        "category": "judicial_violation",
        "lane": "E",
        "relevance_score": 1.0,
        "tags": "rusco,warrant,hooker,martini,canon3,ex_parte,enforcement,arrest,critical_evidence",
    },
    {
        "source_file": "ADVERSARY_INTEL_SESSION_2026-04-14_RUSCO",
        "quote_text": (
            "RUSCO TWO-TRACK EVIDENCE SYSTEM: Pamela Rusco told Andrew 3 times that evidence "
            "must be presented at hearings only and cannot be filed with the clerk. However, on "
            "August 8, 2025, Emily Watson filed an ex parte motion through the clerk and it was "
            "accepted and signed by Judge McNeill the same day. This constitutes a critical "
            "MCL 552.507 violation — FOC referee maintaining a double standard that favors one "
            "party while blocking the other's access to the court record."
        ),
        "category": "judicial_violation",
        "lane": "E",
        "relevance_score": 1.0,
        "tags": "rusco,two_track,evidence_blocking,mcl_552_507,foc_bias,double_standard",
    },
    {
        "source_file": "ADVERSARY_INTEL_SESSION_2026-04-14_RUSCO",
        "quote_text": (
            "RUSCO HEALTHWEST SABOTAGE: (1) Oct 29, 2025: Rusco called HealthWest clinician to "
            "coordinate testimony BEFORE hearing — undermining clinical independence. (2) Sep 9, "
            "2025: Rusco communicated McNeill's order EXCLUDING the court-ordered HealthWest "
            "evaluation that found Andrew FIT (Psychosis=0, Substance=0, Danger=0, LOCUS=12/Level "
            "One). (3) Oct 28, 2024: 'I do not accept filing of exhibits.' (4) Oct 9, 2024: "
            "Coordinated with Circuit Court Records to block Andrew's exhibits. (5) Jan 8, 2025: "
            "'There is no way to request an audio recording of the hearing' — blocking appellate "
            "record access."
        ),
        "category": "judicial_violation",
        "lane": "E",
        "relevance_score": 1.0,
        "tags": "rusco,healthwest,evidence_gatekeeping,clinical_coordination,audio_denied,foc_misconduct",
    },
    {
        "source_file": "ADVERSARY_INTEL_SESSION_2026-04-14_RUSCO",
        "quote_text": (
            "RUSCO MCL 552.507 INDEPENDENCE VIOLATIONS: FOC referees must maintain independence "
            "and impartiality per MCL 552.507. Rusco: (1) operates from 990 Terrace St — same "
            "address as Judge McNeill's spouse Cavan Berry (attorney/magistrate, 60th District), "
            "(2) blocked father's evidence 3 times while accepting mother's same-day filings, "
            "(3) routed father to chambers/off-record instead of formal filings, (4) called "
            "HealthWest to coordinate testimony against father, (5) initiated arrest warrant "
            "against father via prosecutor, (6) denied hearing audio recordings to block appeal. "
            "Pattern: FOC acting as McNeill's enforcement arm, not independent referee."
        ),
        "category": "judicial_violation",
        "lane": "E",
        "relevance_score": 1.0,
        "tags": "rusco,mcl_552_507,foc_independence,990_terrace,cavan_berry,enforcement_arm,pattern",
    },

    # === ADVERSARY INTELLIGENCE: MARTINI (harvested this session) ===
    {
        "source_file": "ADVERSARY_INTEL_SESSION_2026-04-14_MARTINI",
        "quote_text": (
            "MARTINI SILENCING VERBATIM (Feb 28, 2025 email): 'You will not interrupt. Got it? "
            "I'm pretty sure Judge McNeil is not in a good mood today and she doesn't want to "
            "hear from you unless asked. I'm sure you do not want to spend the next week in jail "
            "on a contempt charge for speaking out in court.' — Martini silenced her own client "
            "before the hearing, using threats of additional jail time. At the SAME hearing, "
            "Martini acknowledged charges were baseless: 'she knows there is nothing substantive "
            "in the motion.' Despite this, Andrew was found guilty and sentenced to 14 days jail."
        ),
        "category": "ineffective_counsel",
        "lane": "D",
        "relevance_score": 1.0,
        "tags": "martini,silencing,contempt_threat,baseless_charges,14_days_jail,duguid_hearing,ppo",
    },
    {
        "source_file": "ADVERSARY_INTEL_SESSION_2026-04-14_MARTINI",
        "quote_text": (
            "MARTINI PATTERN OF WORKING AGAINST CLIENT: (1) CC'd on Rusco's arrest warrant "
            "request for Andrew (Mar 3, 2025) — did NOTHING to oppose. (2) Refused client's "
            "legal work product (May 16, 2025): 'I cannot present my client's non-professional "
            "legal work as my own.' (3) Relayed judge's sanctions threats (May 16): 'Leo said the "
            "judge told you not to file anything else frivolous.' (4) Suppressed bias defense "
            "(Jun 5, 2025): 'I would be cautious about alleging bias to the court.' (5) Called "
            "constitutional defenses 'patently false and unsupported.' (6) Dismissed 14 days "
            "incarceration as 'not a valid reason' for attorney change. (7) Advised client to "
            "'move out of state and find a new place to live.' (8) All 3 hearings resulted in "
            "guilty: 15d abeyance + 14d jail + 45d jail = 59 days total. Martini is Muskegon "
            "County employee (MartiniMa@co.muskegon.mi.us) — same county as McNeill's court."
        ),
        "category": "ineffective_counsel",
        "lane": "D",
        "relevance_score": 1.0,
        "tags": "martini,ineffective_counsel,warrant_cc,sanctions_relay,bias_suppression,county_employee,pattern",
    },

    # === USER TESTIMONY: CONTEXT FOR WARRANT ===
    {
        "source_file": "USER_TESTIMONY_SESSION_2026-04-14",
        "quote_text": (
            "Andrew Pigors testimony — context for the March 3, 2025 warrant: The jail self-surrender "
            "date landed on Andrew's parenting time week. Andrew chose to spend time with his son L.D.W. "
            "because he knew Emily was actively trying to take L.D.W. away permanently. Andrew wanted "
            "to spend as much time as he could with his son before the inevitable separation. This "
            "context — a father choosing his child over compliance with an unjust contempt order — "
            "is critical for the §1983 claim and the JTC complaint. The contempt itself was based on "
            "PPO violations that Martini acknowledged had 'nothing substantive' supporting them."
        ),
        "category": "testimony",
        "lane": "A",
        "relevance_score": 1.0,
        "tags": "warrant_context,parenting_time,self_surrender,custody_fear,section_1983,user_testimony",
    },
    {
        "source_file": "USER_TESTIMONY_SESSION_2026-04-14",
        "quote_text": (
            "Andrew Pigors testimony — McNeill 'frivolous' labeling and evidentiary hearings: Every "
            "filing McNeill called 'frivolous' contained documented evidence of Emily Watson's "
            "misconduct that Andrew was trying to present to the court. Andrew received only 2 "
            "evidentiary hearings total across the entire case. At BOTH hearings, Judge McNeill "
            "COMPLETELY ignored Andrew's evidence — her orders contain zero reference to any exhibits "
            "or testimony Andrew presented. Instead, McNeill's orders twisted Andrew's own words to "
            "fit a predetermined narrative favoring Emily. This pattern — labeling evidence-backed "
            "filings as 'frivolous' while ignoring evidence at the only 2 hearings granted — "
            "demonstrates systematic denial of due process and access to courts."
        ),
        "category": "testimony",
        "lane": "E",
        "relevance_score": 1.0,
        "tags": "frivolous,evidentiary_hearing,evidence_ignored,twisted_words,due_process,access_to_courts,mcneill,pattern,user_testimony",
    },
]

def main():
    conn = connect()
    inserted = 0
    skipped = 0

    for row in ROWS:
        # Check for exact duplicate
        existing = conn.execute(
            "SELECT id FROM evidence_quotes WHERE quote_text = ? LIMIT 1",
            (row["quote_text"],)
        ).fetchone()
        if existing:
            skipped += 1
            continue

        conn.execute(
            """INSERT INTO evidence_quotes 
               (source_file, quote_text, category, lane, relevance_score, tags, created_at, is_duplicate)
               VALUES (?, ?, ?, ?, ?, ?, ?, 0)""",
            (
                row["source_file"],
                row["quote_text"],
                row["category"],
                row["lane"],
                row["relevance_score"],
                row["tags"],
                datetime.datetime.now().isoformat(),
            )
        )
        inserted += 1

    conn.commit()

    # Verify
    count = conn.execute(
        "SELECT COUNT(*) FROM evidence_quotes WHERE source_file LIKE '%SESSION_2026-04-14%'"
    ).fetchone()[0]

    testimony_count = conn.execute(
        "SELECT COUNT(*) FROM evidence_quotes WHERE source_file LIKE '%USER_TESTIMONY%SESSION_2026-04-14%'"
    ).fetchone()[0]

    rusco_count = conn.execute(
        "SELECT COUNT(*) FROM evidence_quotes WHERE source_file LIKE '%RUSCO%SESSION_2026-04-14%'"
    ).fetchone()[0]

    martini_count = conn.execute(
        "SELECT COUNT(*) FROM evidence_quotes WHERE source_file LIKE '%MARTINI%SESSION_2026-04-14%'"
    ).fetchone()[0]

    total = conn.execute("SELECT COUNT(*) FROM evidence_quotes").fetchone()[0]
    active = conn.execute("SELECT COUNT(*) FROM evidence_quotes WHERE is_duplicate = 0").fetchone()[0]

    conn.close()

    print(f"=== PERSISTENCE COMPLETE ===")
    print(f"Inserted: {inserted} | Skipped (dup): {skipped}")
    print(f"Verified session rows: {count}")
    print(f"  - User testimony: {testimony_count}")
    print(f"  - Rusco intel: {rusco_count}")
    print(f"  - Martini intel: {martini_count}")
    print(f"DB totals: {total} total / {active} active")

if __name__ == "__main__":
    main()
