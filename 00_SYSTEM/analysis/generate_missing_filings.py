#!/usr/bin/env python3
"""
Generate Missing Court Filings — Pigors v. Watson
===================================================
Reads the filing_analysis and gap_tickets tables from litigation_context.db,
identifies gaps from the viable_filings_report, and generates each document
using doc_templates.py helpers.

Output directory: LitigationOS/04_COURT_FILINGS/generated/
"""

from __future__ import annotations

import os
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── paths ────────────────────────────────────────────────────────────────
DB_PATH = Path(r"C:\Users\andre\litigation_context.db")
OUTPUT_DIR = Path(r"C:\Users\andre\LitigationOS\04_COURT_FILINGS\generated")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Make doc_templates importable
sys.path.insert(0, str(Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\local_model")))
from doc_templates import (
    PLAINTIFF, DEFENDANT, PLAINTIFF_FULL, DEFENDANT_FULL,
    JUDGE, CASE_NUMBERS, COURTS, COURT_ADDRESS,
    _today, _caption, _signature_block, _certificate_of_service,
    _proof_of_service, _numbered_paragraphs,
    motion_template, brief_template, affidavit_template,
)

# ── extended constants for MEEK4 / MEEK5 ────────────────────────────────
CASE_NUMBERS_EXT = {
    **CASE_NUMBERS,
    "MEEK4": "2024-001507-DC",
    "MEEK5": "USDC-WDMI (TBD)",
}

COURTS_EXT = {
    "MEEK1": "14TH JUDICIAL CIRCUIT COURT\nCOUNTY OF MUSKEGON",
    "MEEK2": "14TH JUDICIAL CIRCUIT COURT\nCOUNTY OF MUSKEGON",
    "MEEK3": "MICHIGAN COURT OF APPEALS",
    "MEEK4": "14TH JUDICIAL CIRCUIT COURT\nCOUNTY OF MUSKEGON\nFAMILY DIVISION — FRIEND OF THE COURT",
    "MEEK5": "UNITED STATES DISTRICT COURT\nWESTERN DISTRICT OF MICHIGAN\nSOUTHERN DIVISION",
}


# ── DB helpers ───────────────────────────────────────────────────────────
def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def query(sql: str, params: tuple = ()) -> List[sqlite3.Row]:
    conn = get_conn()
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def fetch_citations(keywords: List[str], limit: int = 15) -> List[str]:
    """Pull real citations from master_citations matching keywords."""
    conn = get_conn()
    clauses = " OR ".join(["citation LIKE ?" for _ in keywords])
    params = tuple(f"%{k}%" for k in keywords)
    rows = conn.execute(
        f"SELECT DISTINCT citation, substr(context,1,200) FROM master_citations "
        f"WHERE {clauses} LIMIT ?",
        (*params, limit),
    ).fetchall()
    conn.close()
    return [f"{r[0]}" for r in rows]


def fetch_forensic(categories: List[str], limit: int = 8) -> List[str]:
    """Pull forensic judicial analysis findings by category."""
    conn = get_conn()
    placeholders = ",".join("?" for _ in categories)
    rows = conn.execute(
        f"SELECT description, mcr_violations FROM forensic_judicial_analysis "
        f"WHERE category IN ({placeholders}) AND severity IN ('critical','high') "
        f"LIMIT ?",
        (*categories, limit),
    ).fetchall()
    conn.close()
    facts = []
    for r in rows:
        desc = r[0].strip().replace("\n", " ")[:250]
        if desc.startswith("**Event:**"):
            desc = desc[len("**Event:**"):].strip()
        facts.append(desc)
    return facts


def fetch_auth_rule_text(rule_id: str) -> str:
    """Get the full text of an auth rule."""
    rows = query("SELECT full_text FROM auth_rules WHERE id=?", (rule_id,))
    return rows[0][0][:600] if rows else ""


def fetch_evidence_quotes(keyword: str, limit: int = 5) -> List[str]:
    """Fetch evidence quotes matching keyword."""
    rows = query(
        "SELECT substr(quote_text,1,300), date_ref FROM evidence_quotes "
        "WHERE quote_text LIKE ? LIMIT ?",
        (f"%{keyword}%", limit),
    )
    return [r[0].strip().replace("\n", " ")[:200] for r in rows]


# ── gap registry ─────────────────────────────────────────────────────────
# Each gap from viable_filings_report.md with generation metadata
GAPS: List[Dict[str, Any]] = [
    {
        "id": "MEEK2_brief_terminate_ppo",
        "lane": "MEEK2",
        "title": "Brief Supporting Motion to Terminate PPO",
        "case_no": "2023-5907-PP",
        "court": "14th Circuit",
        "doc_type": "brief",
        "filename": "MEEK2_Brief_Supporting_Motion_Terminate_PPO.md",
    },
    {
        "id": "MEEK3_coa_affidavit_of_service",
        "lane": "MEEK3",
        "title": "COA Affidavit of Service",
        "case_no": "COA 366810",
        "court": "Michigan Court of Appeals",
        "doc_type": "affidavit",
        "filename": "MEEK3_COA_Affidavit_of_Service.md",
    },
    {
        "id": "MEEK3_coa_appendix",
        "lane": "MEEK3",
        "title": "COA Appendix / Record on Appeal",
        "case_no": "COA 366810",
        "court": "Michigan Court of Appeals",
        "doc_type": "appendix",
        "filename": "MEEK3_COA_Appendix_Record_on_Appeal.md",
    },
    {
        "id": "MEEK3_coa_docketing_statement",
        "lane": "MEEK3",
        "title": "COA Docketing Statement",
        "case_no": "COA 366810",
        "court": "Michigan Court of Appeals",
        "doc_type": "docketing",
        "filename": "MEEK3_COA_Docketing_Statement.md",
    },
    {
        "id": "MEEK4_foc_grievance",
        "lane": "MEEK4",
        "title": "FOC Grievance Formal Complaint",
        "case_no": "2024-001507-DC",
        "court": "14th Circuit — FOC",
        "doc_type": "complaint",
        "filename": "MEEK4_FOC_Grievance_Formal_Complaint.md",
    },
    {
        "id": "MEEK5_section_1983_affidavit",
        "lane": "MEEK5",
        "title": "Federal Section 1983 Affidavit",
        "case_no": "USDC-WDMI (TBD)",
        "court": "U.S. District Court, W.D. Michigan",
        "doc_type": "affidavit",
        "filename": "MEEK5_Federal_Section_1983_Affidavit.md",
    },
    {
        "id": "MEEK5_civil_cover_sheet",
        "lane": "MEEK5",
        "title": "Federal Civil Cover Sheet (JS-44)",
        "case_no": "USDC-WDMI (TBD)",
        "court": "U.S. District Court, W.D. Michigan",
        "doc_type": "cover_sheet",
        "filename": "MEEK5_Federal_Civil_Cover_Sheet_JS44.md",
    },
]


# ═══════════════════════════════════════════════════════════════════════
# DOCUMENT GENERATORS — one function per gap
# ═══════════════════════════════════════════════════════════════════════

def gen_meek2_brief_terminate_ppo() -> str:
    """MEEK2: Brief Supporting Motion to Terminate PPO (Case 2023-5907-PP)."""
    # Pull real data from DB
    ppo_facts = fetch_forensic(["PPO_WEAPONIZATION", "FALSE_ALLEGATIONS"], 6)
    ex_parte_facts = fetch_forensic(["EX_PARTE_VIOLATION"], 4)
    citations = fetch_citations(["3.707", "3.708", "600.2950", "722.23"], 10)

    facts = [
        "On or about November 16, 2023, Defendant Emily Watson obtained Personal "
        "Protection Order No. 2023-5907-PP against Plaintiff Andrew Pigors in the "
        "14th Judicial Circuit Court, Muskegon County.",
        "The PPO was obtained based on false and misleading allegations, including "
        "fabricated claims regarding poisoning (the 'Ozempic-to-Arsenic' chain) and "
        "staged photographs of a mason jar and webcam.",
        "Law enforcement investigated Watson's allegations and found them entirely "
        "without basis. No drug evidence was recovered; no criminal charges were filed.",
        "The PPO has been weaponized as an instrument of parental alienation, "
        "resulting in the complete severance of Plaintiff's relationship with the "
        "minor child, L.D.W. (DOB: November 9, 2022).",
        "Watson has filed seven show-cause motions under the PPO, each based on "
        "unsubstantiated or fabricated allegations — constituting a pattern of "
        "vexatious litigation designed to harass Plaintiff.",
        "Plaintiff has been denied ALL parenting time with his son for over 329 "
        "consecutive days as a direct consequence of the PPO's continued existence.",
    ]
    if ppo_facts:
        facts.extend(ppo_facts[:3])

    arguments = [
        {
            "issue": "The PPO Was Obtained Through False and Misleading Evidence "
                     "and Must Be Terminated Under MCR 3.707 and MCL 600.2950",
            "rule": "MCR 3.707(A) provides that a petitioner or respondent may file "
                    "a motion to modify or terminate a personal protection order at any "
                    "time. MCL 600.2950(12) authorizes termination where the PPO is no "
                    "longer necessary or was obtained through fraud or misrepresentation.",
            "application": "The PPO was obtained through Watson's fabricated allegations "
                          "of poisoning and staged evidence. Every allegation underlying the "
                          "PPO has been investigated and refuted. The continued enforcement of "
                          "a PPO based on disproven claims constitutes an abuse of the "
                          "protective order process and violates Plaintiff's constitutional "
                          "rights to parent his child.",
            "conclusion": "Because the factual basis for the PPO has been conclusively "
                         "disproven, the PPO must be terminated pursuant to MCR 3.707 "
                         "and MCL 600.2950.",
        },
        {
            "issue": "Continued Enforcement of the PPO Harms the Best Interests "
                     "of the Minor Child Under MCL 722.23",
            "rule": "MCL 722.23 enumerates twelve best-interest factors that courts "
                    "must consider in custody and parenting-time matters. Factor (j) — "
                    "the willingness of each parent to facilitate a close relationship "
                    "with the other parent — is directly implicated.",
            "application": "The PPO has been used as a tactical weapon to deny Plaintiff "
                          "all contact with L.D.W. for over 329 days. This prolonged "
                          "separation causes severe developmental and psychological harm to "
                          "a three-year-old child, including attachment disruption and "
                          "parental alienation. Watson's refusal to facilitate any "
                          "relationship violates Factor (j).",
            "conclusion": "Termination of the PPO is necessary to protect the child's "
                         "best interests and restore the parent-child bond.",
        },
        {
            "issue": "The PPO Constitutes an Unconstitutional Deprivation of "
                     "Parental Rights Without Due Process",
            "rule": "The Fourteenth Amendment to the U.S. Constitution and Const 1963, "
                    "Art. 1, § 17 protect a parent's fundamental right to the care, "
                    "custody, and companionship of their child. Troxel v Granville, "
                    "530 US 57 (2000); In re Sanders, 495 Mich 394 (2014).",
            "application": "The PPO, obtained through false evidence and without adequate "
                          "procedural safeguards, has operated as a de facto termination of "
                          "Plaintiff's parental rights. No court has found Plaintiff to be "
                          "an unfit parent. The PPO deprives Plaintiff of his fundamental "
                          "liberty interest without due process.",
            "conclusion": "The PPO must be terminated to vindicate Plaintiff's "
                         "constitutional rights to parent his child.",
        },
    ]

    relief = [
        "Terminate Personal Protection Order No. 2023-5907-PP in its entirety;",
        "Enter an order restoring Plaintiff's parenting time with L.D.W. "
        "consistent with the prior equal-parenting-time order;",
        "Award Plaintiff reasonable costs and attorney fees incurred in "
        "bringing this motion pursuant to MCR 2.625 and MCL 600.2591;",
        "Grant such other relief as this Court deems just and proper.",
    ]

    auth_list = [
        "MCR 3.707 — Modification, Termination, or Extension of PPO",
        "MCL 600.2950 — Personal Protection Orders",
        "MCL 722.23 — Best Interest of the Child Factors",
        "MCR 2.114 — Signing and Verification of Documents",
        "Troxel v Granville, 530 US 57 (2000)",
        "In re Sanders, 495 Mich 394 (2014)",
    ]
    if citations:
        for c in citations[:4]:
            if c not in auth_list:
                auth_list.append(c)

    return motion_template(
        title="BRIEF IN SUPPORT OF MOTION TO TERMINATE PERSONAL PROTECTION ORDER",
        lane="MEEK1",  # PPO lane uses MEEK1 case number
        statement_of_issues=[
            "Whether the PPO should be terminated where the factual basis has been "
            "disproven by law enforcement investigation?",
            "Whether continued enforcement of the PPO violates the best interests "
            "of the minor child under MCL 722.23?",
            "Whether the PPO constitutes an unconstitutional deprivation of "
            "parental rights without due process?",
        ],
        statement_of_facts=facts,
        arguments=arguments,
        relief_requested=relief,
        authorities_cited=auth_list,
    )


def gen_meek3_coa_affidavit_of_service() -> str:
    """MEEK3: COA Affidavit of Service (COA 366810)."""
    return f"""STATE OF MICHIGAN
IN THE MICHIGAN COURT OF APPEALS

{PLAINTIFF},                          COA Case No. {CASE_NUMBERS['MEEK3']}
        Plaintiff-Appellant,          Lower Court Case No. {CASE_NUMBERS['MEEK1']}

    v.                                {JUDGE}

{DEFENDANT},
        Defendant-Appellee.
__________________________________________/

AFFIDAVIT OF SERVICE

STATE OF MICHIGAN  )
                   ) ss.
COUNTY OF MUSKEGON )

    I, {PLAINTIFF_FULL}, being first duly sworn, depose and state:

    1. I am the Plaintiff-Appellant in the above-captioned matter and am over
the age of 18 years.

    2. On {_today()}, I served a true and correct copy of the following
documents upon the Defendant-Appellee:

        a. Claim of Appeal
        b. Appellant's Brief on Appeal
        c. Appendix / Record on Appeal
        d. Docketing Statement (SCAO Form MC 30)
        e. Proof of Service (this document)

    3. Service was made by the following method:

        [X] First-class United States mail, postage prepaid, addressed to:

            {DEFENDANT_FULL}
            [ADDRESS PLACEHOLDER]
            [CITY, STATE ZIP]

        [ ] Personal service
        [ ] Electronic service (e-Filing)

    4. Service was also made upon the Trial Court by first-class mail to:

            Clerk of the Court
            14th Judicial Circuit Court
            990 Terrace Street
            Muskegon, MI 49442

    5. I certify that a copy was also filed with the Michigan Court of Appeals:

            Clerk of the Court
            Michigan Court of Appeals
            Cadillac Place
            3020 W. Grand Blvd., Suite 14-300
            Detroit, MI 48202

    6. I declare under the penalties of perjury that the foregoing statements
are true and correct to the best of my information, knowledge, and belief.

FURTHER AFFIANT SAYETH NOT.

Date: {_today()}

____________________________________
{PLAINTIFF_FULL}
[ADDRESS PLACEHOLDER]
[CITY, STATE ZIP]
[PHONE]
[EMAIL]

Subscribed and sworn to before me
this _____ day of _____________, {time.strftime('%Y')}.

____________________________________
Notary Public, Muskegon County, Michigan
My Commission Expires: ______________
"""


def gen_meek3_coa_appendix() -> str:
    """MEEK3: COA Appendix / Record on Appeal (COA 366810) per MCR 7.212(H)."""
    # Pull chronological events from DB
    conn = get_conn()
    events = conn.execute(
        "SELECT date, substr(shortfact240,1,200), issue FROM global_chronology "
        "WHERE date != '' AND date >= '2023' ORDER BY date LIMIT 30"
    ).fetchall()

    # Pull list of existing filings from filing_analysis
    filings = conn.execute(
        "SELECT filename, court, title, completeness_score FROM filing_analysis "
        "ORDER BY filename LIMIT 40"
    ).fetchall()
    conn.close()

    # Build exhibit list from real filings
    exhibit_entries = []
    for i, f in enumerate(filings, 1):
        exhibit_entries.append(f"    {i:3d}. {f[0]:<55s} ({f[1]})")

    # Build chronology entries
    chrono_entries = []
    for e in events:
        if e[0] and len(e[0]) >= 8:
            fact = e[1].replace("\n", " ")[:120]
            chrono_entries.append(f"    {e[0]}  {fact}")

    return f"""STATE OF MICHIGAN
IN THE MICHIGAN COURT OF APPEALS

{PLAINTIFF},                          COA Case No. {CASE_NUMBERS['MEEK3']}
        Plaintiff-Appellant,          Lower Court Case No. {CASE_NUMBERS['MEEK1']}

    v.                                {JUDGE}

{DEFENDANT},
        Defendant-Appellee.
__________________________________________/

PLAINTIFF-APPELLANT'S APPENDIX / RECORD ON APPEAL
(Pursuant to MCR 7.212(H) and MCR 7.210)

TABLE OF CONTENTS

    I.   Register of Actions (Lower Court) ........................ Tab A
    II.  Orders Appealed From ...................................... Tab B
    III. Relevant Pleadings and Motions ............................ Tab C
    IV.  Transcripts of Relevant Proceedings ....................... Tab D
    V.   Exhibits Admitted or Offered Below ........................ Tab E
    VI.  Chronological Summary of Proceedings ...................... Tab F
    VII. Certificate of Appendix Compliance ........................ Tab G

═══════════════════════════════════════════════════════════════════════════
TAB A — REGISTER OF ACTIONS (LOWER COURT)
═══════════════════════════════════════════════════════════════════════════

    Case No. {CASE_NUMBERS['MEEK1']} (PPO): Pigors v. Watson
    Case No. {CASE_NUMBERS['MEEK2']} (Custody/DC): Pigors v. Watson
    Court: 14th Judicial Circuit Court, Muskegon County
    Judge: {JUDGE}

    [ATTACH: Certified copy of Register of Actions from Muskegon County Clerk]

═══════════════════════════════════════════════════════════════════════════
TAB B — ORDERS APPEALED FROM
═══════════════════════════════════════════════════════════════════════════

    1. Ex Parte Order Suspending Parenting Time (August 8, 2025)
       — Five (5) separate ex parte orders entered on a single day
       — No prior notice to Plaintiff
       — No factual findings of immediate harm

    2. Order Denying Motion for Disqualification of Judge McNeill
       — Denied September 25, 2024

    3. Order Denying Motion to Restore Parenting Time
       — Denied following November 26, 2025 hearing

    [ATTACH: Certified copies of each order]

═══════════════════════════════════════════════════════════════════════════
TAB C — RELEVANT PLEADINGS AND MOTIONS
═══════════════════════════════════════════════════════════════════════════

    Document Index (from case record):

{chr(10).join(exhibit_entries)}

═══════════════════════════════════════════════════════════════════════════
TAB D — TRANSCRIPTS OF RELEVANT PROCEEDINGS
═══════════════════════════════════════════════════════════════════════════

    1. Transcript — November 26, 2025 Evidentiary Hearing
       Reporter: [NAME — PLACEHOLDER]
       Pages: [NUMBER — PLACEHOLDER]

    2. Transcript — October 29, 2025 Status Conference
       Reporter: [NAME — PLACEHOLDER]
       Pages: [NUMBER — PLACEHOLDER]

    3. Transcript — September 25, 2024 Disqualification Hearing
       Reporter: [NAME — PLACEHOLDER]
       Pages: [NUMBER — PLACEHOLDER]

    [ATTACH: Certified transcripts or file motion under MCR 7.210(B)(2)
     if transcripts are unavailable]

═══════════════════════════════════════════════════════════════════════════
TAB E — EXHIBITS ADMITTED OR OFFERED BELOW
═══════════════════════════════════════════════════════════════════════════

    Exhibit A:  Police investigation reports (allegations unsubstantiated)
    Exhibit B:  CPS investigation reports (allegations unfounded)
    Exhibit C:  HealthWest psychological evaluation records
    Exhibit D:  Text messages / communications re: parenting time denial
    Exhibit E:  Fabrication timeline — seven allegations, none substantiated
    Exhibit F:  Watson family coordination evidence (Albert Watson messages)
    Exhibit G:  Financial disclosure discrepancies
    Exhibit H:  Parenting time log (365 days → 0 days trajectory)

    [ATTACH: Copies of each exhibit with authentication certificates]

═══════════════════════════════════════════════════════════════════════════
TAB F — CHRONOLOGICAL SUMMARY OF PROCEEDINGS
═══════════════════════════════════════════════════════════════════════════

{chr(10).join(chrono_entries) if chrono_entries else "    [Chronological entries from case database]"}

═══════════════════════════════════════════════════════════════════════════
TAB G — CERTIFICATE OF APPENDIX COMPLIANCE
═══════════════════════════════════════════════════════════════════════════

CERTIFICATE OF COMPLIANCE WITH MCR 7.212(H)

    I, {PLAINTIFF_FULL}, hereby certify that this Appendix complies with
MCR 7.212(H) and contains all documents, transcripts, and exhibits
necessary for the Court's review of the issues presented on appeal.

    I further certify that the documents contained herein are true and
accurate copies of the originals on file with the trial court.

Date: {_today()}

____________________________________
{PLAINTIFF_FULL}, Pro Se Plaintiff-Appellant
[ADDRESS PLACEHOLDER]
[CITY, STATE ZIP]
[PHONE]
[EMAIL]

{_certificate_of_service()}
"""


def gen_meek3_coa_docketing_statement() -> str:
    """MEEK3: COA Docketing Statement (MC 30 format) for COA 366810."""
    return f"""STATE OF MICHIGAN
IN THE MICHIGAN COURT OF APPEALS

DOCKETING STATEMENT
(SCAO Form MC 30 — Pursuant to MCR 7.204(B))

═══════════════════════════════════════════════════════════════════════════
SECTION 1 — CASE IDENTIFICATION
═══════════════════════════════════════════════════════════════════════════

    Court of Appeals Case No.:    {CASE_NUMBERS['MEEK3']}
    Lower Court Case No.:         {CASE_NUMBERS['MEEK1']} (PPO)
                                  {CASE_NUMBERS['MEEK2']} (Custody/DC)
    Lower Court:                  14th Judicial Circuit Court
    County:                       Muskegon
    Judge:                        {JUDGE}

═══════════════════════════════════════════════════════════════════════════
SECTION 2 — PARTIES
═══════════════════════════════════════════════════════════════════════════

    Plaintiff-Appellant:
        Name:       {PLAINTIFF_FULL}
        Address:    [ADDRESS PLACEHOLDER]
        City/Zip:   [CITY, STATE ZIP]
        Phone:      [PHONE]
        Email:      [EMAIL]
        Attorney:   Pro Se

    Defendant-Appellee:
        Name:       {DEFENDANT_FULL}
        Address:    [ADDRESS PLACEHOLDER]
        City/Zip:   [CITY, STATE ZIP]
        Phone:      [PHONE]
        Attorney:   Jennifer Barnes, Esq. (P-[BAR NO.])
                    [ADDRESS PLACEHOLDER]

═══════════════════════════════════════════════════════════════════════════
SECTION 3 — TYPE OF CASE AND JURISDICTION
═══════════════════════════════════════════════════════════════════════════

    Nature of Action:         Family — Custody / Parenting Time / PPO
    Basis for Jurisdiction:   MCR 7.203(A) — Appeal of Right from Final
                              Order; MCR 7.203(B) — Appeal from order
                              affecting substantial rights

    Is this case related to any other pending appeal?  [ ] Yes  [X] No

═══════════════════════════════════════════════════════════════════════════
SECTION 4 — ORDERS OR JUDGMENTS APPEALED FROM
═══════════════════════════════════════════════════════════════════════════

    1. Date of Order:    August 8, 2025
       Nature:           Ex Parte Order Suspending ALL Parenting Time
       Judge:            {JUDGE}
       Was a Motion for Reconsideration filed?  [X] Yes  [ ] No
       Date of ruling on reconsideration:       [DATE — PLACEHOLDER]

    2. Date of Order:    November 26, 2025
       Nature:           Order Denying Restoration of Parenting Time
       Judge:            {JUDGE}

    3. Date of Order:    September 25, 2024
       Nature:           Order Denying Motion for Disqualification
       Judge:            {JUDGE}

═══════════════════════════════════════════════════════════════════════════
SECTION 5 — ISSUES ON APPEAL
═══════════════════════════════════════════════════════════════════════════

    1. Whether the trial court erred in entering an ex parte order
       suspending all parenting time without factual findings of
       immediate and irreparable harm as required by MCR 3.207(B).

    2. Whether the trial court violated Plaintiff-Appellant's
       constitutional right to due process by entering five ex parte
       orders on a single day without prior notice or opportunity
       to be heard.

    3. Whether the trial court erred in denying Plaintiff-Appellant's
       Motion for Disqualification where documented bias and ex parte
       communications demonstrate disqualifying prejudice under
       MCR 2.003(C)(1).

    4. Whether the trial court's continued enforcement of the PPO,
       based on fabricated and disproven allegations, violates the
       best interests of the child under MCL 722.23.

    5. Whether the Friend of the Court's ex parte communications
       with third-party evaluators tainted the evidentiary record
       and deprived Plaintiff-Appellant of a fair hearing.

═══════════════════════════════════════════════════════════════════════════
SECTION 6 — PRIOR APPEALS
═══════════════════════════════════════════════════════════════════════════

    Have there been any prior appeals in this case?  [ ] Yes  [X] No

═══════════════════════════════════════════════════════════════════════════
SECTION 7 — COMPANION CASES
═══════════════════════════════════════════════════════════════════════════

    Are there companion or consolidated cases?
    [X] Yes — PPO Case No. {CASE_NUMBERS['MEEK1']} and Custody Case No.
    {CASE_NUMBERS['MEEK2']} arise from the same facts and involve the
    same parties and child.

═══════════════════════════════════════════════════════════════════════════
SECTION 8 — CERTIFICATION
═══════════════════════════════════════════════════════════════════════════

    I certify that the information in this Docketing Statement is true
and complete to the best of my knowledge, information, and belief,
formed after reasonable inquiry, pursuant to MCR 7.204(B).

Date: {_today()}

____________________________________
{PLAINTIFF_FULL}, Pro Se Plaintiff-Appellant
[ADDRESS PLACEHOLDER]
[CITY, STATE ZIP]
[PHONE]
[EMAIL]
"""


def gen_meek4_foc_grievance() -> str:
    """MEEK4: FOC Grievance Formal Complaint (14th Circuit Family Division)."""
    # Pull forensic findings on FOC / procedural misconduct
    foc_findings = fetch_forensic(
        ["PROCEDURAL_MISCONDUCT", "EX_PARTE_VIOLATION", "BENCHBOOK_DEVIATION"], 6
    )

    return f"""STATE OF MICHIGAN
IN THE {COURTS_EXT['MEEK4']}

{PLAINTIFF},                          Case No. {CASE_NUMBERS_EXT['MEEK4']}
        Plaintiff / Grievant,
                                      {JUDGE}
    v.

{DEFENDANT},
        Defendant.
__________________________________________/

FORMAL GRIEVANCE AGAINST FRIEND OF THE COURT
PURSUANT TO MCR 3.208 AND MCL 552.507

═══════════════════════════════════════════════════════════════════════════
I. GRIEVANT INFORMATION
═══════════════════════════════════════════════════════════════════════════

    Name:           {PLAINTIFF_FULL}
    Address:        [ADDRESS PLACEHOLDER]
    City/Zip:       [CITY, STATE ZIP]
    Phone:          [PHONE]
    Email:          [EMAIL]
    Case No.:       {CASE_NUMBERS_EXT['MEEK4']}
    FOC Officer:    Pamela Rusco

═══════════════════════════════════════════════════════════════════════════
II. NATURE OF GRIEVANCE
═══════════════════════════════════════════════════════════════════════════

    This formal grievance is filed against the Muskegon County Friend of
the Court ("FOC"), specifically FOC Officer Pamela Rusco, for violations
of MCR 3.208, MCR 3.218, MCJC Canon 3(A)(4), and the FOC's statutory
duties under MCL 552.503 et seq.

═══════════════════════════════════════════════════════════════════════════
III. SPECIFIC VIOLATIONS AND FACTUAL BASIS
═══════════════════════════════════════════════════════════════════════════

A.  PROHIBITED EX PARTE COMMUNICATION (MCJC Canon 3(A)(4), MCR 3.218)

    1. On October 29, 2025, FOC Officer Pamela Rusco initiated an ex parte
telephone call to HealthWest (Muskegon County Community Mental Health)
without notice to Plaintiff and outside the presence of any hearing.

    2. The purpose of this ex parte call was to arrange testimony from the
clinician who produced the psychological evaluation of Plaintiff — a
document central to the pending evidentiary hearing.

    3. This ex parte communication tainted the evidentiary record by
allowing the FOC to shape witness testimony and evaluation conclusions
outside the adversarial process.

    4. MCR 3.218 and MCJC Canon 3(A)(4) expressly prohibit ex parte
communications by court officers regarding substantive matters in
pending cases. The FOC is bound by these same ethical constraints.

B.  FAILURE TO ENFORCE PARENTING TIME ORDERS (MCL 552.511b)

    5. Despite Plaintiff's repeated requests and formal complaints, the
FOC failed to initiate any enforcement action for Defendant's continuous
violation of the court-ordered parenting time schedule.

    6. Defendant unilaterally withheld the minor child for approximately
39 consecutive days beginning March 28, 2024, and subsequently denied
an additional 27 days of court-ordered parenting time throughout 2024.

    7. MCL 552.511b mandates that the FOC "shall initiate a civil contempt
proceeding" when a party fails to comply with a parenting time order. The
FOC took no action despite documented and repeated violations.

    8. The FOC's inaction enabled Defendant's escalating pattern of
parenting time denial, culminating in the total suspension of Plaintiff's
parenting time on August 8, 2025.

C.  BIASED RECOMMENDATIONS AND FAILURE OF IMPARTIALITY (MCR 3.208)

    9. The FOC has consistently recommended against Plaintiff's interests
without adequate investigation of Defendant's documented parental
alienation tactics, false allegations, and contemptuous behavior.

    10. The FOC failed to investigate or report on:
        a. Seven false allegations by Defendant, all investigated and
           found unsubstantiated by law enforcement and CPS;
        b. Defendant's pattern of filing show-cause motions as a
           harassment tool;
        c. Evidence of coordinated Watson family interference with
           Plaintiff's parenting time.

D.  ADDITIONAL FINDINGS FROM FORENSIC ANALYSIS

{_numbered_paragraphs(foc_findings[:5]) if foc_findings else "    [Additional findings from forensic judicial analysis]"}

═══════════════════════════════════════════════════════════════════════════
IV. RULES AND STANDARDS VIOLATED
═══════════════════════════════════════════════════════════════════════════

    1. MCJC Canon 3(A)(4) — Prohibition on Ex Parte Communications
       "A judge [or court officer] shall not initiate, permit, or consider
       ex parte communications ... concerning a pending or impending
       proceeding."

    2. MCR 3.218 — Friend of the Court Records and Access
       The FOC must maintain impartiality and may not engage in ex parte
       communications regarding substantive case matters.

    3. MCR 3.208 — Friend of the Court
       The FOC must perform its duties impartially and in accordance with
       law, including enforcement of parenting time orders.

    4. MCL 552.503 — Duties of the Friend of the Court
       The FOC shall "investigate and make recommendations to the court
       in domestic relations matters" — investigations must be thorough,
       balanced, and based on verified evidence.

    5. MCL 552.511b — Enforcement of Parenting Time
       Mandatory enforcement provisions require the FOC to act when
       parenting time is denied.

═══════════════════════════════════════════════════════════════════════════
V. RELIEF REQUESTED
═══════════════════════════════════════════════════════════════════════════

    WHEREFORE, Grievant {PLAINTIFF_FULL} respectfully requests:

    1. A formal investigation into FOC Officer Pamela Rusco's conduct;

    2. Sanctions for the prohibited ex parte communication with HealthWest
       on October 29, 2025;

    3. Reassignment of this case to a different FOC officer who can
       provide impartial recommendations;

    4. An order directing the FOC to initiate contempt proceedings against
       Defendant for documented parenting time violations;

    5. A complete audit of the FOC's file in this matter to identify
       any additional ex parte communications or procedural irregularities;

    6. Such other relief as the Court deems just and proper.

═══════════════════════════════════════════════════════════════════════════
VI. VERIFICATION
═══════════════════════════════════════════════════════════════════════════

    I, {PLAINTIFF_FULL}, declare under the penalties of perjury that the
facts stated in this grievance are true and correct to the best of my
information, knowledge, and belief.

{_signature_block()}

{_certificate_of_service(recipient=f"Muskegon County Friend of the Court\\n990 Terrace Street\\nMuskegon, MI 49442")}

{_certificate_of_service(recipient=f"{DEFENDANT_FULL}\\n[ADDRESS PLACEHOLDER]\\n[CITY, STATE ZIP]")}
"""


def gen_meek5_section_1983_affidavit() -> str:
    """MEEK5: Federal Section 1983 Affidavit for USDC W.D. Michigan."""
    # Fetch due process / constitutional violation findings
    dp_findings = fetch_forensic(
        ["DUE_PROCESS_VIOLATION", "EX_PARTE_VIOLATION", "BIAS_INDICATOR",
         "CONSTITUTIONAL_VIOLATION"], 8
    )
    canon_findings = fetch_forensic(["MCJC_CANON_VIOLATION"], 4)

    statements = [
        "I am the Plaintiff in the above-captioned matter and make this "
        "Affidavit based upon my own personal knowledge in support of a "
        "complaint under 42 U.S.C. § 1983.",

        "I am the natural father of L.D.W. (DOB: November 9, 2022). I have "
        "been completely denied all parenting time with my son for over 329 "
        "consecutive days, beginning August 8, 2025.",

        "On August 8, 2025, Judge Jenny L. McNeill of the 14th Judicial "
        "Circuit Court entered FIVE (5) separate ex parte orders on a single "
        "day, all without prior notice to me, suspending ALL of my parenting "
        "time. No hearing was scheduled within 14 days as required by "
        "MCR 3.207(C)(5).",

        "The ex parte orders were based on an Emergency Ex Parte Motion filed "
        "by Defendant Emily Watson containing fabricated allegations. Every "
        "allegation underlying the motion has been investigated by law "
        "enforcement and Child Protective Services and found to be without "
        "basis.",

        "Judge McNeill has demonstrated a pattern of systematic bias against "
        "me, including: (a) denying my Motion for Disqualification on "
        "September 25, 2024, without referral to the Chief Judge as required "
        "by MCR 2.003(D); (b) entering ex parte orders without notice; "
        "(c) refusing to enforce Defendant's documented parenting time "
        "violations; (d) permitting FOC ex parte communications with "
        "third-party evaluators.",

        "The Friend of the Court, Pamela Rusco, initiated a prohibited ex "
        "parte communication with HealthWest on October 29, 2025, to arrange "
        "testimony from the clinician who evaluated me — tainting the "
        "evidentiary record in violation of MCJC Canon 3(A)(4).",

        "Defendant Emily Watson, acting under color of state law through her "
        "use of the court system and in coordination with court officers, has "
        "weaponized the Personal Protection Order (No. 2023-5907-PP) and "
        "false allegations to completely sever the parent-child bond.",

        "The Watson family — including Albert Watson, Cody Watson, and Lori "
        "Watson — have engaged in a coordinated campaign of parental "
        "alienation, false reporting, and interference with court-ordered "
        "parenting time.",

        "I have suffered concrete, particularized injuries including: "
        "(a) complete loss of parenting time for 329+ days; "
        "(b) destruction of the parent-child bond with my three-year-old son; "
        "(c) emotional distress and psychological harm; "
        "(d) financial harm from defending against serial frivolous filings; "
        "(e) reputational harm from false allegations.",

        "The constitutional violations I have suffered include: "
        "(a) deprivation of the fundamental right to parent under the "
        "Fourteenth Amendment (Troxel v Granville, 530 US 57 (2000)); "
        "(b) denial of procedural due process (Mathews v Eldridge, "
        "424 US 319 (1976)); "
        "(c) denial of substantive due process; "
        "(d) denial of equal protection.",

        "These deprivations were caused by persons acting under color of "
        "state law — specifically Judge McNeill and FOC Officer Rusco — "
        "who used their official positions to deprive me of constitutionally "
        "protected rights, satisfying the requirements of 42 U.S.C. § 1983.",

        "I have exhausted or been denied adequate state remedies. My Motion "
        "for Disqualification was denied. My emergency motions were denied. "
        "My appeal is pending before the Michigan Court of Appeals as "
        f"Case No. {CASE_NUMBERS['MEEK3']}.",
    ]

    return f"""IN THE UNITED STATES DISTRICT COURT
FOR THE WESTERN DISTRICT OF MICHIGAN
SOUTHERN DIVISION

{PLAINTIFF},                          Case No. [TO BE ASSIGNED]
        Plaintiff,
                                      JURY TRIAL DEMANDED
    v.

HON. JENNY L. McNEILL, in her
individual capacity;
PAMELA RUSCO, in her individual
capacity as FOC Officer;
{DEFENDANT}, individually and as
custodial parent,
        Defendants.
__________________________________________/

AFFIDAVIT OF {PLAINTIFF} IN SUPPORT OF
COMPLAINT UNDER 42 U.S.C. § 1983

STATE OF MICHIGAN  )
                   ) ss.
COUNTY OF MUSKEGON )

    I, {PLAINTIFF_FULL}, being first duly sworn, depose and state as follows:

{_numbered_paragraphs(statements)}

    {len(statements) + 1}. I declare under the penalties of perjury under the laws of the
United States that the foregoing statements are true and correct to the
best of my information, knowledge, and belief.

FURTHER AFFIANT SAYETH NOT.

Date: {_today()}

____________________________________
{PLAINTIFF_FULL}, Pro Se Plaintiff
[ADDRESS PLACEHOLDER]
[CITY, STATE ZIP]
[PHONE]
[EMAIL]

Subscribed and sworn to before me
this _____ day of _____________, {time.strftime('%Y')}.

____________________________________
Notary Public, Muskegon County, Michigan
My Commission Expires: ______________

{_certificate_of_service("first-class mail and CM/ECF electronic filing")}
"""


def gen_meek5_civil_cover_sheet() -> str:
    """MEEK5: Federal Civil Cover Sheet (JS-44 format reference)."""
    return f"""UNITED STATES DISTRICT COURT
WESTERN DISTRICT OF MICHIGAN

JS 44 (Rev. 04/21) — CIVIL COVER SHEET

═══════════════════════════════════════════════════════════════════════════
NOTE: This document provides the information required by the JS-44
Civil Cover Sheet in a text-based format. The actual filing must use
the official JS-44 form available from the USDC-WDMI Clerk's Office
or at https://www.miwd.uscourts.gov/forms.
═══════════════════════════════════════════════════════════════════════════

I. (a) PLAINTIFFS:
    {PLAINTIFF_FULL}
    [ADDRESS PLACEHOLDER]
    [CITY, STATE ZIP]

   (b) DEFENDANTS:
    Hon. Jenny L. McNeill (individual capacity)
    c/o 14th Judicial Circuit Court
    990 Terrace Street, Muskegon, MI 49442

    Pamela Rusco (individual capacity, FOC Officer)
    c/o 14th Judicial Circuit Court
    990 Terrace Street, Muskegon, MI 49442

    {DEFENDANT_FULL}
    [ADDRESS PLACEHOLDER]
    [CITY, STATE ZIP]

   (c) Attorneys (if known):
    Plaintiff:  Pro Se — {PLAINTIFF_FULL}
    Defendants: Unknown / to be determined

II. BASIS OF JURISDICTION:
    [X] 3. Federal Question (U.S. Government Not a Party)
        28 U.S.C. § 1331 — Civil Rights action under 42 U.S.C. § 1983

III. CITIZENSHIP OF PRINCIPAL PARTIES:
    Plaintiff:   (X) Citizen of this State (Michigan)
    Defendants:  (X) Citizens of this State (Michigan)

IV. NATURE OF SUIT:
    [X] 440 — Other Civil Rights
    (42 U.S.C. § 1983 — Deprivation of civil rights under color of
     state law)

V. ORIGIN:
    [X] 1. Original Proceeding

VI. CAUSE OF ACTION:
    42 U.S.C. § 1983 — Deprivation of constitutional rights under
    color of state law.

    Brief Description:
    Plaintiff, a pro se father, brings this action under 42 U.S.C.
    § 1983 alleging that a state court judge, a Friend of the Court
    officer, and the custodial parent conspired to and did deprive
    Plaintiff of his fundamental constitutional right to parent his
    minor child. Specifically: (1) the judge entered five ex parte
    orders on a single day suspending all parenting time without
    notice or hearing, in violation of the Fourteenth Amendment;
    (2) the FOC officer engaged in prohibited ex parte communications
    with third-party evaluators; (3) the custodial parent weaponized
    the court system through fabricated allegations to achieve total
    parental alienation. Plaintiff seeks declaratory and injunctive
    relief, compensatory and punitive damages, and attorney fees
    under 42 U.S.C. § 1988.

VII. REQUESTED IN COMPLAINT:
    [X] CHECK IF THIS IS A CLASS ACTION UNDER FRCP 23: [ ] No  [X] N/A
    DEMAND: $[AMOUNT — PLACEHOLDER] (exceeding $75,000)
    [X] JURY DEMAND: Yes

VIII. RELATED CASE(S) IF ANY:
    State Court Cases:
        {CASE_NUMBERS['MEEK1']} (14th Circuit, Muskegon County — PPO)
        {CASE_NUMBERS['MEEK2']} (14th Circuit, Muskegon County — Custody)
        {CASE_NUMBERS['MEEK3']} (Michigan Court of Appeals)

═══════════════════════════════════════════════════════════════════════════

Date: {_today()}

____________________________________
{PLAINTIFF_FULL}, Pro Se Plaintiff
[ADDRESS PLACEHOLDER]
[CITY, STATE ZIP]
[PHONE]
[EMAIL]
"""


# ═══════════════════════════════════════════════════════════════════════
# MAIN — orchestrate generation
# ═══════════════════════════════════════════════════════════════════════

GENERATORS = {
    "MEEK2_brief_terminate_ppo":     gen_meek2_brief_terminate_ppo,
    "MEEK3_coa_affidavit_of_service": gen_meek3_coa_affidavit_of_service,
    "MEEK3_coa_appendix":            gen_meek3_coa_appendix,
    "MEEK3_coa_docketing_statement": gen_meek3_coa_docketing_statement,
    "MEEK4_foc_grievance":           gen_meek4_foc_grievance,
    "MEEK5_section_1983_affidavit":  gen_meek5_section_1983_affidavit,
    "MEEK5_civil_cover_sheet":       gen_meek5_civil_cover_sheet,
}


def main() -> None:
    print("=" * 72)
    print("  PIGORS v. WATSON — Missing Filing Generator")
    print(f"  Database : {DB_PATH}")
    print(f"  Output   : {OUTPUT_DIR}")
    print(f"  Date     : {_today()}")
    print("=" * 72)

    # Verify DB connectivity
    try:
        conn = get_conn()
        count = conn.execute("SELECT COUNT(*) FROM filing_analysis").fetchone()[0]
        print(f"\n  filing_analysis rows: {count}")
        conn.close()
    except Exception as e:
        print(f"  [ERROR] Cannot read DB: {e}")
        sys.exit(1)

    generated: List[Tuple[str, str, int]] = []

    for gap in GAPS:
        gap_id = gap["id"]
        filename = gap["filename"]
        outpath = OUTPUT_DIR / filename

        print(f"\n  Generating: {gap['title']}")
        print(f"    Lane     : {gap['lane']}")
        print(f"    Case No. : {gap['case_no']}")
        print(f"    Court    : {gap['court']}")
        print(f"    File     : {filename}")

        gen_func = GENERATORS.get(gap_id)
        if not gen_func:
            print(f"    [SKIP] No generator for {gap_id}")
            continue

        try:
            content = gen_func()
            outpath.write_text(content, encoding="utf-8")
            size = outpath.stat().st_size
            generated.append((filename, gap["title"], size))
            print(f"    [OK] {size:,} bytes written")
        except Exception as e:
            print(f"    [ERROR] {e}")
            import traceback
            traceback.print_exc()

    # Summary
    print("\n" + "=" * 72)
    print("  GENERATION SUMMARY")
    print("=" * 72)
    print(f"  Total gaps identified : {len(GAPS)}")
    print(f"  Documents generated   : {len(generated)}")
    print(f"  Output directory      : {OUTPUT_DIR}")
    print()
    print(f"  {'#':<4} {'Filename':<55} {'Size':>10}")
    print(f"  {'-'*4} {'-'*55} {'-'*10}")
    for i, (fname, title, size) in enumerate(generated, 1):
        print(f"  {i:<4} {fname:<55} {size:>10,}")
    print()

    if len(generated) == len(GAPS):
        print("  ✓ All filings generated successfully.")
    else:
        missing = len(GAPS) - len(generated)
        print(f"  ⚠ {missing} filing(s) could not be generated.")

    print("=" * 72)


if __name__ == "__main__":
    main()
