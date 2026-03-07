"""
DELTA9 — Court Document Generator · MAX LEVEL 9999++
═══════════════════════════════════════════════════════

Takes scored actions + atoms from master_index.db and produces
ACTUAL Michigan court-formatted legal documents ready for filing.

Output: Markdown files with proper captions, numbered paragraphs,
verification language, certificate of service, and exhibit lists.

Usage:
    python court_document_generator.py                  # Generate all ready actions
    python court_document_generator.py --action A3      # Generate specific action
    python court_document_generator.py --lane A         # Generate all Lane A
    python court_document_generator.py --top 7          # Generate top 7 by score
    python court_document_generator.py --list           # List available actions

Author: LitigationOS DELTA9 Fleet
"""
import json
import os
import re
import sqlite3
import sys
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ═══════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════

MASTER_DB = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\agents\master_index.db")
OUTPUT_DIR = Path(r"C:\Users\andre\LitigationOS\04_COURT_FILINGS\GENERATED")
CASE_FILES = Path(r"C:\Users\andre\LitigationOS\01_CASE_FILES")

# Party Information
PLAINTIFF = {
    "name": "ANDREW J. PIGORS",
    "role": "Plaintiff/Counter-Defendant",
    "address": "[Address]",
    "city_state_zip": "Muskegon, Michigan [ZIP]",
    "phone": "[Phone]",
    "email": "[Email]",
    "pro_se": True,
}

# Case Information by Lane
CASES = {
    "A": {
        "court": "14TH JUDICIAL CIRCUIT COURT",
        "county": "MUSKEGON",
        "state": "MICHIGAN",
        "case_no": "2024-001507-DC",
        "related_case": "2023-5907-PP",
        "judge": "Hon. Jenny L. McNeill",
        "plaintiff_label": "Plaintiff",  # Watson is plaintiff in custody
        "defendant_label": "Defendant",
        "opposing_party": "EMILY A. WATSON",
        "opposing_counsel": "David Rusco (P_______)",
        "opposing_address": "[Address]\n[City, State ZIP]",
    },
    "B": {
        "court": "14TH JUDICIAL CIRCUIT COURT",
        "county": "MUSKEGON",
        "state": "MICHIGAN",
        "case_no": "2025-002760-CZ",
        "judge": "Hon. Hoopes",
        "plaintiff_label": "Plaintiff",
        "defendant_label": "Defendants",
        "opposing_party": "SHADY OAKS MHP LLC, HOMES OF AMERICA LLC,\nand ALDEN GLOBAL CAPITAL LLC",
        "opposing_counsel": "[Defendants' Counsel]",
        "opposing_address": "[Address]\n[City, State ZIP]",
    },
    "C_STATE": {
        "court": "14TH JUDICIAL CIRCUIT COURT",
        "county": "MUSKEGON",
        "state": "MICHIGAN",
        "case_no": "[New Case Number]",
        "judge": "[To Be Assigned]",
        "plaintiff_label": "Plaintiff",
        "defendant_label": "Defendants",
        "opposing_party": "MUSKEGON COUNTY et al.",
        "opposing_counsel": "[County Counsel]",
        "opposing_address": "[Address]\n[City, State ZIP]",
    },
    "C_FEDERAL": {
        "court": "UNITED STATES DISTRICT COURT\nFOR THE WESTERN DISTRICT OF MICHIGAN\nSOUTHERN DIVISION",
        "case_no": "[New Case Number]",
        "judge": "[To Be Assigned]",
        "plaintiff_label": "Plaintiff",
        "defendant_label": "Defendants",
        "opposing_party": "EMILY WATSON, individually;\nHON. JENNY L. McNEILL, in her official capacity",
        "opposing_counsel": "[Defendants' Counsel]",
        "opposing_address": "[Address]\n[City, State ZIP]",
    },
    "D": {
        "court": "14TH JUDICIAL CIRCUIT COURT",
        "county": "MUSKEGON",
        "state": "MICHIGAN",
        "case_no": "2023-5907-PP",
        "judge": "Hon. Jenny L. McNeill",
        "plaintiff_label": "Petitioner",
        "defendant_label": "Respondent",
        "opposing_party": "EMILY A. WATSON",
        "opposing_counsel": "David Rusco (P_______)",
        "opposing_address": "[Address]\n[City, State ZIP]",
    },
    "E": {
        "court": "MICHIGAN JUDICIAL TENURE COMMISSION",
        "state": "MICHIGAN",
        "case_no": "[JTC File Number]",
        "judge": "Hon. Jenny L. McNeill",   # Subject of complaint
        "plaintiff_label": "Complainant",
        "defendant_label": "Respondent Judge",
        "opposing_party": "HON. JENNY L. McNEILL",
        "opposing_counsel": "N/A",
        "opposing_address": "14th Judicial Circuit Court\nMuskegon, Michigan",
    },
    "F": {
        "court": "MICHIGAN COURT OF APPEALS",
        "state": "MICHIGAN",
        "case_no": "[COA Docket Number]",
        "lower_court_case": "2024-001507-DC",
        "judge": "[Panel TBD]",
        "plaintiff_label": "Appellant",
        "defendant_label": "Appellee",
        "opposing_party": "EMILY A. WATSON",
        "opposing_counsel": "David Rusco (P_______)",
        "opposing_address": "[Address]\n[City, State ZIP]",
    },
    "JTC": {
        "body": "MICHIGAN JUDICIAL TENURE COMMISSION",
        "address": "3034 W. Grand Blvd., Suite 8-450\nDetroit, Michigan 48202",
    },
    "AGC": {
        "body": "ATTORNEY GRIEVANCE COMMISSION",
        "address": "Marquette Building\n243 W. Congress, Suite 256\nDetroit, Michigan 48226",
    },
}

# ═══════════════════════════════════════════════════════
# ACTION DEFINITIONS — All 56 Legal Actions
# ═══════════════════════════════════════════════════════

ACTION_REGISTRY: Dict[str, Dict] = {
    # ── LANE A: Watson / Custody ──
    "A1": {
        "title": "EMERGENCY MOTION TO RESTORE PARENTING TIME",
        "type": "motion",
        "lane": "A",
        "case_key": "A",
        "authority": ["MCR 3.207(C)", "MCL 722.27", "MCL 722.27a"],
        "description": "Emergency motion to restore parenting time unlawfully suspended without hearing",
        "relief": "Immediate restoration of parenting time; makeup parenting time; sanctions for interference",
    },
    "A2": {
        "title": "MOTION TO MODIFY/TERMINATE PERSONAL PROTECTION ORDER",
        "type": "motion",
        "lane": "A",
        "case_key": "A",
        "authority": ["MCR 3.707(A)", "MCL 600.2950(12)", "MCL 600.2950(13)"],
        "description": "Motion to modify or terminate PPO based on changed circumstances and due process violations",
        "relief": "Termination of PPO; alternatively, modification to remove overbroad restrictions",
    },
    "A3": {
        "title": "MOTION FOR DISQUALIFICATION OF JUDGE",
        "type": "motion",
        "lane": "A",
        "case_key": "A",
        "authority": ["MCR 2.003(C)(1)", "MCR 2.003(D)", "Caperton v. A.T. Massey Coal Co., 556 U.S. 868 (2009)"],
        "description": "Motion for disqualification based on personal bias, ex parte contacts, and pattern of prejudgment",
        "relief": "Disqualification of Hon. Jenny L. McNeill; reassignment to neutral judge",
    },
    "A9": {
        "title": "MOTION FOR BEST INTEREST RE-EVALUATION",
        "type": "motion",
        "lane": "A",
        "case_key": "A",
        "authority": ["MCL 722.23(a)-(l)", "MCL 722.27(1)(c)", "Vodvarka v. Grasmeyer, 259 Mich App 499 (2003)"],
        "description": "Motion for re-evaluation of all 12 best interest factors under MCL 722.23",
        "relief": "Full evidentiary hearing on all 12 best interest factors; modification of custody order",
    },
    "A10": {
        "title": "MOTION REGARDING PARENTAL ALIENATION",
        "type": "motion",
        "lane": "A",
        "case_key": "A",
        "authority": ["MCL 722.23(j)", "MCL 722.27(1)(c)", "Berger v. Berger, 277 Mich App 700 (2008)"],
        "description": "Motion addressing willful interference with parental relationship (Factor J alienation)",
        "relief": "Finding of parental alienation; custody modification; therapeutic intervention",
    },
    "A11": {
        "title": "COMPLAINT FOR MANDAMUS",
        "type": "complaint",
        "lane": "A",
        "case_key": "A",
        "authority": ["MCR 3.305", "Const 1963, art 6, § 13"],
        "description": "Complaint for mandamus to compel hearing on pending motions denied without cause",
        "relief": "Writ of mandamus compelling court to hold evidentiary hearing",
    },
    "A18": {
        "title": "COMPLAINT UNDER 42 U.S.C. § 1983 — SUBSTANTIVE DUE PROCESS",
        "type": "complaint",
        "lane": "A",
        "case_key": "C_FEDERAL",
        "authority": ["42 U.S.C. § 1983", "U.S. Const. amend. XIV", "Troxel v. Granville, 530 U.S. 57 (2000)"],
        "description": "Federal civil rights complaint for deprivation of fundamental parental rights",
        "relief": "Declaratory judgment; injunctive relief; compensatory damages; prospective relief under Ex parte Young",
    },
    "A23": {
        "title": "COMPLAINT FOR TORTIOUS INTERFERENCE WITH PARENTAL RELATIONSHIP",
        "type": "complaint",
        "lane": "A",
        "case_key": "A",
        "authority": ["Hester v. Barnett, 723 S.W.2d 544 (Mo. Ct. App. 1987)", "Restatement (Second) of Torts § 700"],
        "description": "Common law tort complaint for intentional interference with parent-child relationship",
        "relief": "Compensatory damages; punitive damages; injunctive relief",
    },
    "A24": {
        "title": "COMPLAINT FOR INTENTIONAL INFLICTION OF EMOTIONAL DISTRESS",
        "type": "complaint",
        "lane": "A",
        "case_key": "A",
        "authority": ["Roberts v. Auto-Owners Ins Co, 422 Mich 594 (1985)", "Haverbush v. Powelson, 217 Mich App 228 (1996)"],
        "description": "IIED complaint based on 329+ days forced separation from child",
        "relief": "Compensatory damages for emotional distress; punitive damages",
    },
    "A33": {
        "title": "COMPLAINT TO JUDICIAL TENURE COMMISSION",
        "type": "jtc_complaint",
        "lane": "A",
        "case_key": "JTC",
        "authority": ["MCR 9.200 et seq.", "Michigan Code of Judicial Conduct, Canons 1-3"],
        "description": "Formal complaint against Hon. McNeill for judicial misconduct spanning both case lanes",
        "relief": "Investigation; discipline; removal from bench",
    },
    "A34": {
        "title": "COMPLAINT TO ATTORNEY GRIEVANCE COMMISSION",
        "type": "bar_complaint",
        "lane": "A",
        "case_key": "AGC",
        "authority": ["Michigan Rules of Professional Conduct 1.1-8.4", "MCR 9.100 et seq."],
        "description": "Complaint against David Rusco for ethical violations in custody proceedings",
        "relief": "Investigation; discipline; suspension or disbarment",
    },
    # ── LANE B: Shady Oaks / Housing ──
    "B1": {
        "title": "COMPLAINT FOR BREACH OF WARRANTY OF HABITABILITY",
        "type": "complaint",
        "lane": "B",
        "case_key": "B",
        "authority": ["MCL 554.139(1)", "MCL 554.139(2)", "Teufel v. Watkins, 267 Mich App 425 (2005)"],
        "description": "Civil complaint for breach of statutory warranty of habitability",
        "relief": "Damages; rent abatement; injunctive relief requiring repairs; attorney fees",
    },
    "B3": {
        "title": "COMPLAINT FOR VIOLATION OF MICHIGAN CONSUMER PROTECTION ACT",
        "type": "complaint",
        "lane": "B",
        "case_key": "B",
        "authority": ["MCL 445.903", "MCL 445.911", "Dix v. Am. Bankers Life Assurance Co, 429 Mich 410 (1987)"],
        "description": "Consumer protection complaint against all three corporate defendants",
        "relief": "Actual damages; $250 minimum statutory damages; treble damages; attorney fees; costs",
    },
    "B7": {
        "title": "COMPLAINT FOR SECURITY DEPOSIT VIOLATIONS",
        "type": "complaint",
        "lane": "B",
        "case_key": "B",
        "authority": ["MCL 554.602", "MCL 554.609", "MCL 554.612"],
        "description": "Complaint for security deposit law violations",
        "relief": "Double the security deposit amount; actual damages; costs",
    },
    # ── LANE C: Convergence ──
    "C1": {
        "title": "COMPLAINT UNDER 42 U.S.C. § 1983 — MONELL COUNTY LIABILITY",
        "type": "complaint",
        "lane": "C",
        "case_key": "C_FEDERAL",
        "authority": ["42 U.S.C. § 1983", "Monell v. Dept of Social Services, 436 U.S. 658 (1978)"],
        "description": "Federal civil rights complaint against Muskegon County for policy/custom causing constitutional harm",
        "relief": "Declaratory judgment; injunctive relief; compensatory damages; policy reform",
    },
    "C5": {
        "title": "COMPLAINT UNDER 42 U.S.C. §§ 1983, 1985 — CONSOLIDATED CIVIL RIGHTS",
        "type": "complaint",
        "lane": "C",
        "case_key": "C_FEDERAL",
        "authority": ["42 U.S.C. § 1983", "42 U.S.C. § 1985(3)", "42 U.S.C. § 1986"],
        "description": "Consolidated federal civil rights complaint — conspiracy spanning custody and housing cases",
        "relief": "Declaratory judgment; injunctive relief; compensatory and punitive damages",
    },
}


# ═══════════════════════════════════════════════════════
# DOCUMENT TEMPLATES
# ═══════════════════════════════════════════════════════

def michigan_state_caption(case_info: dict, title: str) -> str:
    """Generate Michigan state court caption per MCR 2.113."""
    opp = case_info.get("opposing_party", "UNKNOWN")
    judge_line = f"                                        {case_info.get('judge', '')}"
    return f"""STATE OF {case_info.get('state', 'MICHIGAN')}
IN THE {case_info['court']}
COUNTY OF {case_info.get('county', 'MUSKEGON')}
{'─' * 50}

{case_info.get('opposing_party', opp)},
        {case_info['plaintiff_label']},
                                        Case No. {case_info['case_no']}
v.{judge_line}

{PLAINTIFF['name']},
        {case_info['defendant_label']},
        In Propria Persona.

{'─' * 50}

{title}

{'─' * 50}
"""


def michigan_state_caption_pigors_plaintiff(case_info: dict, title: str) -> str:
    """Caption where Pigors IS the plaintiff (B lane, new complaints)."""
    return f"""STATE OF {case_info.get('state', 'MICHIGAN')}
IN THE {case_info['court']}
COUNTY OF {case_info.get('county', 'MUSKEGON')}
{'─' * 50}

{PLAINTIFF['name']},
        {case_info['plaintiff_label']},
        In Propria Persona,
                                        Case No. {case_info['case_no']}
v.{' ' * 32}{case_info.get('judge', '')}

{case_info.get('opposing_party', 'DEFENDANTS')},
        {case_info['defendant_label']}.

{'─' * 50}

{title}

{'─' * 50}
"""


def federal_caption(case_info: dict, title: str) -> str:
    """Generate federal court caption."""
    return f"""IN THE {case_info['court']}

{PLAINTIFF['name']},
        {case_info['plaintiff_label']},
                                        Case No. {case_info.get('case_no', '___________')}
v.

{case_info.get('opposing_party', 'DEFENDANTS')},
        {case_info['defendant_label']}.
{'_' * 50}/

{title}
"""


def jtc_header(case_info: dict, judge_name: str = "Hon. Jenny L. McNeill") -> str:
    """JTC complaint header."""
    return f"""COMPLAINT TO THE {case_info['body']}

Date: {datetime.now().strftime('%B %d, %Y')}

TO:     {case_info['body']}
        {case_info['address']}

FROM:   {PLAINTIFF['name']}
        {PLAINTIFF['address']}
        {PLAINTIFF['city_state_zip']}
        {PLAINTIFF.get('phone', '[Phone]')} | {PLAINTIFF.get('email', '[Email]')}

RE:     Complaint Against {judge_name}
        14th Judicial Circuit Court, Muskegon County, Michigan
"""


def bar_complaint_header(case_info: dict, attorney_name: str = "David Rusco") -> str:
    """Attorney Grievance Commission complaint header."""
    return f"""COMPLAINT TO THE {case_info['body']}

Date: {datetime.now().strftime('%B %d, %Y')}

TO:     {case_info['body']}
        {case_info['address']}

FROM:   {PLAINTIFF['name']}
        {PLAINTIFF['address']}
        {PLAINTIFF['city_state_zip']}
        {PLAINTIFF.get('phone', '[Phone]')} | {PLAINTIFF.get('email', '[Email]')}

RE:     Request for Investigation of {attorney_name}
        Attorney at Law, State Bar No. P_______
"""


def verification_block() -> str:
    """Verification language for verified complaints/motions."""
    return f"""
---

## VERIFICATION

I, {PLAINTIFF['name']}, declare under the penalties of perjury under the laws of the
State of Michigan that the foregoing statements are true and correct to the best of
my knowledge, information, and belief.

Dated: ____________________

________________________________________
{PLAINTIFF['name']}, In Propria Persona
{PLAINTIFF['address']}
{PLAINTIFF['city_state_zip']}
{PLAINTIFF.get('phone', '[Phone]')}
"""


def certificate_of_service(parties: List[Dict]) -> str:
    """Certificate of service per MCR 2.107."""
    lines = [f"""
---

## CERTIFICATE OF SERVICE

I hereby certify that on _________________, I served a true copy of the foregoing
document upon all parties or their attorneys of record by:

☐ First-class U.S. mail, postage prepaid
☐ Personal delivery
☐ Electronic service via TrueFiling/MiFile

upon the following:
"""]
    for party in parties:
        lines.append(f"""
{party.get('name', '[Name]')}
{party.get('address', '[Address]')}
{party.get('city_state_zip', '[City, State ZIP]')}
""")

    lines.append(f"""
________________________________________
{PLAINTIFF['name']}, In Propria Persona
""")
    return "\n".join(lines)


def proposed_order_block(case_info: dict, relief: str) -> str:
    """Proposed order block."""
    return f"""
---

## PROPOSED ORDER

STATE OF {case_info.get('state', 'MICHIGAN')}
IN THE {case_info['court']}
COUNTY OF {case_info.get('county', 'MUSKEGON')}
Case No. {case_info['case_no']}

ORDER

At a session of said Court held in the City of Muskegon,
County of Muskegon, State of Michigan on _________________.

PRESENT: {case_info.get('judge', 'HONORABLE ________________')}

This matter having come before the Court on {PLAINTIFF['name']}'s Motion,
and the Court being otherwise fully advised in the premises:

IT IS HEREBY ORDERED that:

{relief}

IT IS SO ORDERED.

Dated: ____________________

________________________________________
{case_info.get('judge', 'Circuit Court Judge')}
"""


# ═══════════════════════════════════════════════════════
# DATABASE QUERIES
# ═══════════════════════════════════════════════════════

def connect_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(MASTER_DB), timeout=180)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=180000")
    conn.execute("PRAGMA query_only=ON")
    conn.execute("PRAGMA cache_size=-131072")  # 128MB page cache (Δ∞)
    conn.execute("PRAGMA mmap_size=12884901888")  # 12GB mmap
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def get_scored_actions(conn: sqlite3.Connection, lane: str = None, action_id: str = None) -> List[dict]:
    """Get scored actions from action_scores table."""
    query = "SELECT * FROM action_scores WHERE composite_score > 0"
    params = []
    if lane:
        query += " AND lane = ?"
        params.append(lane)
    if action_id:
        query += " AND action_id = ?"
        params.append(action_id)
    query += " ORDER BY composite_score DESC"
    rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def get_judicial_findings(conn: sqlite3.Connection, judge: str = None, limit: int = 50) -> List[dict]:
    """Get judicial findings for document population."""
    query = "SELECT * FROM judicial_findings"
    params = []
    if judge:
        query += " WHERE judge LIKE ?"
        params.append(f"%{judge}%")
    query += " ORDER BY severity DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def get_atoms_by_type(conn: sqlite3.Connection, atom_type: str, lane: str = None, limit: int = 100) -> List[dict]:
    """Get atoms by type for document population."""
    query = "SELECT * FROM atoms WHERE atom_type = ?"
    params = [atom_type]
    if lane:
        query += " AND meek_lane LIKE ?"
        params.append(f"%{lane}%")
    query += " ORDER BY CAST(confidence AS REAL) DESC LIMIT ?"
    params.append(limit)
    try:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []


def get_citations_for_authority(conn: sqlite3.Connection, authority_pattern: str, limit: int = 20) -> List[dict]:
    """Get citation atoms matching an authority pattern."""
    query = """SELECT * FROM atoms 
               WHERE atom_type IN ('citation', 'citation_validation') 
               AND content LIKE ? 
               ORDER BY CAST(confidence AS REAL) DESC LIMIT ?"""
    try:
        rows = conn.execute(query, (f"%{authority_pattern}%", limit)).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []


def get_fact_atoms(conn: sqlite3.Connection, lane: str, keywords: List[str] = None, limit: int = 50) -> List[dict]:
    """Get fact atoms for a lane, optionally filtered by keywords."""
    query = "SELECT * FROM atoms WHERE atom_type = 'fact' AND meek_lane LIKE ?"
    params = [f"%{lane}%"]
    if keywords:
        kw_clauses = " OR ".join(["content LIKE ?" for _ in keywords])
        query += f" AND ({kw_clauses})"
        params.extend([f"%{kw}%" for kw in keywords])
    query += " ORDER BY CAST(confidence AS REAL) DESC LIMIT ?"
    params.append(limit)
    try:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []


def get_timeline_events(conn: sqlite3.Connection, lane: str = None, limit: int = 30) -> List[dict]:
    """Get timeline/event atoms."""
    query = "SELECT * FROM atoms WHERE atom_type = 'event'"
    params = []
    if lane:
        query += " AND meek_lane LIKE ?"
        params.append(f"%{lane}%")
    query += " LIMIT ?"
    params.append(limit)
    try:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []


# ═══════════════════════════════════════════════════════
# DOCUMENT GENERATORS
# ═══════════════════════════════════════════════════════

class DocumentGenerator:
    """Generates court documents from scored actions and database atoms."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.paragraph_num = 0

    def _p(self, text: str) -> str:
        """Numbered paragraph."""
        self.paragraph_num += 1
        return f"{self.paragraph_num}. {text}"

    def _reset_paragraphs(self):
        self.paragraph_num = 0

    def generate_motion(self, action_id: str, action_def: dict, score_data: dict) -> str:
        """Generate a motion document."""
        self._reset_paragraphs()
        case_info = CASES[action_def["case_key"]]
        findings = get_judicial_findings(self.conn, limit=30)
        facts = get_fact_atoms(self.conn, action_def["lane"], limit=40)
        events = get_timeline_events(self.conn, action_def["lane"], limit=20)

        # Determine caption style
        if action_def["lane"] == "B":
            caption = michigan_state_caption_pigors_plaintiff(case_info, action_def["title"])
        else:
            caption = michigan_state_caption(case_info, action_def["title"])

        sections = [caption]

        # Introduction
        sections.append(f"""
**NOW COMES** {PLAINTIFF['name']}, appearing In Propria Persona, and respectfully
moves this Honorable Court for an Order granting the relief described herein,
and in support thereof states as follows:

---

## I. INTRODUCTION

{self._p(action_def['description'] + '.')}

{self._p('This motion is brought pursuant to ' + ', '.join(action_def['authority']) + '.')}

---

## II. STATEMENT OF FACTS
""")

        # Populate facts from database
        if facts:
            for fact in facts[:15]:
                content = fact.get("content", "")
                if content and len(content) > 20:
                    clean = content.replace("\n", " ").strip()[:500]
                    sections.append(self._p(clean))
        else:
            sections.append(self._p("[Factual allegations to be inserted from case record.]"))

        # Timeline events
        if events:
            sections.append("\n---\n\n## III. CHRONOLOGY OF RELEVANT EVENTS\n")
            for evt in events[:10]:
                content = evt.get("content", "")
                if content:
                    sections.append(self._p(content.replace("\n", " ").strip()[:400]))

        # Legal argument
        sections.append(f"""
---

## {'IV' if events else 'III'}. LEGAL ARGUMENT
""")
        for auth in action_def["authority"]:
            citations = get_citations_for_authority(self.conn, auth.split(",")[0].strip(), limit=5)
            sections.append(f"\n### {auth}\n")
            if citations:
                for cite in citations[:3]:
                    content = cite.get("content", "")
                    if content:
                        sections.append(self._p(content.replace("\n", " ").strip()[:400]))
            else:
                sections.append(self._p(f"[Insert argument under {auth}.]"))

        # Judicial findings (for disqualification/misconduct motions)
        if action_id in ("A3", "A6", "A7", "A11", "A12"):
            if findings:
                sections.append("\n---\n\n## JUDICIAL MISCONDUCT EVIDENCE\n")
                for f in findings[:20]:
                    desc = f.get("description", "")
                    severity = f.get("severity", 0)
                    canon = f.get("canon_ref", "")
                    mcr = f.get("mcr_ref", "")
                    if desc:
                        ref_parts = []
                        if canon:
                            ref_parts.append(f"Canon {canon}")
                        if mcr:
                            ref_parts.append(mcr)
                        ref_str = f" ({', '.join(ref_parts)})" if ref_parts else ""
                        sections.append(self._p(f"{desc.strip()[:400]}{ref_str} [Severity: {severity}/10]"))

        # Relief
        sections.append(f"""
---

## RELIEF REQUESTED

**WHEREFORE**, {PLAINTIFF['name']} respectfully requests that this Court:

1. {action_def['relief']};

2. Grant such other and further relief as this Court deems just and equitable.

---

Respectfully submitted,

Dated: ____________________

________________________________________
{PLAINTIFF['name']}, In Propria Persona
{PLAINTIFF['address']}
{PLAINTIFF['city_state_zip']}
{PLAINTIFF.get('phone', '[Phone]')}
""")

        # Add verification
        sections.append(verification_block())

        # Add proposed order for motions
        sections.append(proposed_order_block(case_info, action_def["relief"]))

        # Add certificate of service
        parties = [{
            "name": case_info.get("opposing_counsel", "[Opposing Party]"),
            "address": case_info.get("opposing_address", "[Address]"),
        }]
        sections.append(certificate_of_service(parties))

        return "\n".join(str(s) for s in sections)

    def generate_complaint(self, action_id: str, action_def: dict, score_data: dict) -> str:
        """Generate a complaint document."""
        self._reset_paragraphs()
        case_info = CASES[action_def["case_key"]]
        facts = get_fact_atoms(self.conn, action_def["lane"], limit=50)
        findings = get_judicial_findings(self.conn, limit=30)

        is_federal = "FEDERAL" in action_def.get("case_key", "")
        if is_federal:
            cap = federal_caption(case_info, action_def["title"])
        elif action_def["lane"] == "B" or action_def["lane"] == "C":
            cap = michigan_state_caption_pigors_plaintiff(case_info, action_def["title"])
        else:
            cap = michigan_state_caption(case_info, action_def["title"])

        sections = [cap]

        sections.append(f"""
**NOW COMES** {PLAINTIFF['name']}, appearing pro se, and for his Complaint against
Defendant(s) states as follows:

---

## I. PRELIMINARY STATEMENT

{self._p(action_def['description'] + '.')}

{self._p('Plaintiff brings this action pursuant to ' + ', '.join(action_def['authority']) + '.')}

---

## II. JURISDICTION AND VENUE
""")

        if is_federal:
            sections.append(f"""
{self._p('This Court has subject matter jurisdiction pursuant to 28 U.S.C. § 1331 (federal question), 28 U.S.C. § 1343(a)(3) (civil rights), and 42 U.S.C. § 1983.')}

{self._p('Venue is proper in this district pursuant to 28 U.S.C. § 1391(b) because the events giving rise to this action occurred in Muskegon County, Michigan, within the Western District of Michigan.')}
""")
        else:
            sections.append(f"""
{self._p('This Court has jurisdiction over this matter pursuant to MCL 600.605 (circuit court general jurisdiction) and the Michigan Constitution, Article VI, § 13.')}

{self._p('Venue is proper in Muskegon County pursuant to MCL 600.1629 because the events giving rise to this action occurred in Muskegon County.')}
""")

        # Parties
        sections.append(f"""
---

## III. PARTIES

{self._p(f'Plaintiff {PLAINTIFF["name"]} is a citizen of the State of Michigan, residing in Muskegon County.')}

{self._p(f'Defendant(s): {case_info.get("opposing_party", "[DEFENDANTS]")}.')}
""")

        # Statement of Facts
        sections.append("\n---\n\n## IV. STATEMENT OF FACTS\n")
        if facts:
            for fact in facts[:25]:
                content = fact.get("content", "")
                if content and len(content) > 20:
                    sections.append(self._p(content.replace("\n", " ").strip()[:500]))
        else:
            sections.append(self._p("[Factual allegations to be developed from case record.]"))

        # Counts
        sections.append(f"\n---\n\n## V. COUNT I — {action_def['title']}\n")
        sections.append(self._p("Plaintiff re-alleges and incorporates by reference all preceding paragraphs."))

        for auth in action_def["authority"]:
            citations = get_citations_for_authority(self.conn, auth.split(",")[0].strip(), limit=5)
            sections.append(f"\n### Authority: {auth}\n")
            if citations:
                for cite in citations[:3]:
                    content = cite.get("content", "")
                    if content:
                        sections.append(self._p(content.replace("\n", " ").strip()[:400]))
            sections.append(self._p(f"Defendants' conduct violated {auth} as described herein."))

        # Federal-specific sections
        if is_federal:
            sections.append(f"""
---

## VI. CONSTITUTIONAL VIOLATIONS

{self._p('The actions described herein deprived Plaintiff of rights, privileges, and immunities secured by the Constitution and laws of the United States, specifically:')}

- The right to substantive due process under the Fourteenth Amendment (fundamental parental rights);
- The right to procedural due process under the Fourteenth Amendment (no hearing for 329+ days);
- The right to equal protection under the Fourteenth Amendment.

{self._p('These deprivations were committed under color of state law within the meaning of 42 U.S.C. § 1983.')}
""")

        # Judicial findings for misconduct-related complaints
        if action_id in ("A18", "A19", "A20", "C1", "C2", "C5"):
            if findings:
                sections.append("\n---\n\n## PATTERN OF JUDICIAL MISCONDUCT\n")
                sections.append(self._p("The following documented findings establish a pattern of unconstitutional conduct:"))
                for f in findings[:15]:
                    desc = f.get("description", "")
                    if desc:
                        sections.append(f"- {desc.strip()[:300]}")

        # Prayer for Relief
        sections.append(f"""
---

## PRAYER FOR RELIEF

**WHEREFORE**, Plaintiff {PLAINTIFF['name']} respectfully prays this Court:

1. Enter judgment in Plaintiff's favor and against Defendant(s);

2. {action_def['relief']};

3. Award Plaintiff his costs of suit;

4. Grant such other and further relief as this Court deems just and equitable.
""")

        # Verification
        sections.append(verification_block())

        # Certificate of service
        parties = [{
            "name": case_info.get("opposing_counsel", "[Opposing Counsel]"),
            "address": case_info.get("opposing_address", "[Address]"),
        }]
        sections.append(certificate_of_service(parties))

        return "\n".join(str(s) for s in sections)

    def generate_jtc_complaint(self, action_id: str, action_def: dict, score_data: dict) -> str:
        """Generate JTC complaint document."""
        self._reset_paragraphs()
        case_info = CASES["JTC"]
        findings = get_judicial_findings(self.conn, judge="McNeill", limit=50)

        sections = [jtc_header(case_info)]

        sections.append(f"""
---

## I. IDENTIFICATION OF JUDGE

{self._p('**Name:** Hon. Jenny L. McNeill')}
{self._p('**Court:** 14th Judicial Circuit Court')}
{self._p('**County:** Muskegon County, Michigan')}
{self._p('**Related Cases:** 2024-001507-DC (Custody); 2023-5907-PP (PPO)')}

---

## II. SUMMARY OF MISCONDUCT

{self._p('This complaint is filed pursuant to MCR 9.200 et seq. and documents a pattern of judicial misconduct by Hon. Jenny L. McNeill including but not limited to:')}

- Ex parte communications with parties and/or counsel (Canon 3(A)(4));
- Failure to provide due process hearings (Canon 3(B)(7));
- Bias and prejudgment of proceedings (Canon 3(B)(5));
- Administrative failures in case management (Canon 3(C)(1));
- Conduct prejudicial to the administration of justice (Canon 2(A)).

---

## III. DETAILED FINDINGS
""")

        if findings:
            # Group by finding type
            by_type: Dict[str, list] = {}
            for f in findings:
                ft = f.get("finding_type", "general")
                by_type.setdefault(ft, []).append(f)

            for ftype, items in by_type.items():
                sections.append(f"\n### {ftype.replace('_', ' ').title()} ({len(items)} instances)\n")
                for item in items[:10]:
                    desc = item.get("description", "")
                    severity = item.get("severity", 0)
                    canon = item.get("canon_ref", "")
                    if desc:
                        ref = f" — Canon {canon}" if canon else ""
                        sections.append(self._p(f"{desc.strip()[:400]}{ref} [Severity: {severity}/10]"))
        else:
            sections.append(self._p("[Detailed findings to be inserted from judicial analysis database.]"))

        sections.append(f"""
---

## IV. CANON VIOLATIONS

{self._p('The foregoing conduct violates the following provisions of the Michigan Code of Judicial Conduct:')}

- **Canon 1** (Integrity): Judge McNeill's pattern of ex parte conduct and procedural irregularities undermines public confidence in the judiciary.

- **Canon 2(A)** (Appearance of Impropriety): The cumulative pattern of one-sided proceedings and denial of due process creates an appearance of partiality.

- **Canon 3(A)(4)** (Ex Parte Communications): Judge McNeill conducted proceedings and issued orders without proper notice to all parties.

- **Canon 3(B)(5)** (Impartiality): Judge McNeill demonstrated bias through systematic exclusion of Plaintiff from proceedings affecting his fundamental rights.

- **Canon 3(B)(7)** (Due Process): Judge McNeill failed to afford Plaintiff the opportunity to be heard on matters directly affecting his parental rights for 329+ consecutive days.

---

## V. RELIEF REQUESTED

{self._p('Complainant respectfully requests that the Judicial Tenure Commission:')}

1. Investigate the conduct described herein;
2. Take appropriate disciplinary action;
3. Consider the pattern and severity of misconduct in determining appropriate sanctions.

---

## VI. SUPPORTING DOCUMENTATION

The following exhibits are attached or available upon request:

[Exhibit list to be compiled from evidence database — {len(findings)} findings documented]
""")

        sections.append(f"""
---

Respectfully submitted,

Dated: {datetime.now().strftime('%B %d, %Y')}

________________________________________
{PLAINTIFF['name']}
{PLAINTIFF['address']}
{PLAINTIFF['city_state_zip']}
{PLAINTIFF.get('phone', '[Phone]')}
{PLAINTIFF.get('email', '[Email]')}
""")

        return "\n".join(str(s) for s in sections)

    def generate_bar_complaint(self, action_id: str, action_def: dict, score_data: dict) -> str:
        """Generate Attorney Grievance Commission complaint."""
        self._reset_paragraphs()
        case_info = CASES["AGC"]
        facts = get_fact_atoms(self.conn, "A", keywords=["rusco", "attorney", "counsel"], limit=30)

        sections = [bar_complaint_header(case_info)]
        sections.append(f"""
---

## I. IDENTIFICATION OF ATTORNEY

{self._p('**Name:** David Rusco')}
{self._p('**State Bar Number:** P_______')}
{self._p('**Office Address:** [Address]')}
{self._p('**Related Cases:** 2024-001507-DC (Custody, 14th Judicial Circuit, Muskegon County)')}

---

## II. SUMMARY OF ETHICAL VIOLATIONS

{self._p('This complaint requests investigation of Attorney David Rusco for violations of the Michigan Rules of Professional Conduct in connection with custody proceedings in the above-referenced case.')}

The following Rules of Professional Conduct are implicated:

- **MRPC 3.1** — Meritorious Claims: Filing or maintaining frivolous claims;
- **MRPC 3.3** — Candor Toward the Tribunal: Misrepresentations to the court;
- **MRPC 3.4** — Fairness to Opposing Party: Obstruction of access to evidence;
- **MRPC 4.1** — Truthfulness in Statements: False statements of material fact;
- **MRPC 8.4(b)-(d)** — Misconduct: Conduct prejudicial to the administration of justice.

---

## III. FACTUAL BASIS
""")

        if facts:
            for fact in facts[:15]:
                content = fact.get("content", "")
                if content and len(content) > 20:
                    sections.append(self._p(content.replace("\n", " ").strip()[:500]))
        else:
            sections.append(self._p("[Factual basis to be developed from case record.]"))

        sections.append(f"""
---

## IV. RELIEF REQUESTED

{self._p('Complainant respectfully requests that the Attorney Grievance Commission:')}

1. Investigate the conduct described herein;
2. Take appropriate disciplinary action pursuant to MCR 9.100 et seq.;
3. Ensure that Attorney Rusco's conduct does not continue to harm the administration of justice.

---

Respectfully submitted,

Dated: {datetime.now().strftime('%B %d, %Y')}

________________________________________
{PLAINTIFF['name']}
{PLAINTIFF['address']}
{PLAINTIFF['city_state_zip']}
""")

        return "\n".join(str(s) for s in sections)

    def generate(self, action_id: str) -> Optional[str]:
        """Generate document for a given action ID."""
        action_def = ACTION_REGISTRY.get(action_id)
        if not action_def:
            print(f"  ⚠ Action {action_id} not in registry (may need template)")
            return None

        # Get score data
        scores = get_scored_actions(self.conn, action_id=action_id)
        score_data = scores[0] if scores else {}

        doc_type = action_def.get("type", "motion")
        if doc_type == "motion":
            return self.generate_motion(action_id, action_def, score_data)
        elif doc_type == "complaint":
            return self.generate_complaint(action_id, action_def, score_data)
        elif doc_type == "jtc_complaint":
            return self.generate_jtc_complaint(action_id, action_def, score_data)
        elif doc_type == "bar_complaint":
            return self.generate_bar_complaint(action_id, action_def, score_data)
        else:
            print(f"  ⚠ Unknown document type: {doc_type}")
            return None


# ═══════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description="DELTA9 Court Document Generator")
    parser.add_argument("--action", help="Generate specific action (e.g., A3)")
    parser.add_argument("--lane", help="Generate all actions for a lane (A, B, C)")
    parser.add_argument("--top", type=int, help="Generate top N actions by score")
    parser.add_argument("--list", action="store_true", help="List available actions")
    parser.add_argument("--all", action="store_true", help="Generate all registered actions")
    args = parser.parse_args()

    print("═" * 60)
    print("  DELTA9 COURT DOCUMENT GENERATOR · MAX LEVEL 9999++")
    print("═" * 60)

    if args.list:
        print(f"\n{'ID':<6} {'Type':<12} {'Lane':<6} {'Title'}")
        print("─" * 70)
        for aid, adef in sorted(ACTION_REGISTRY.items()):
            print(f"{aid:<6} {adef['type']:<12} {adef['lane']:<6} {adef['title']}")
        print(f"\nTotal: {len(ACTION_REGISTRY)} registered actions")
        return

    # Connect to database
    if not MASTER_DB.exists():
        print(f"❌ Database not found: {MASTER_DB}")
        sys.exit(1)

    conn = connect_db()
    gen = DocumentGenerator(conn)

    # Determine which actions to generate
    actions_to_gen = []
    if args.action:
        actions_to_gen = [args.action.upper()]
    elif args.lane:
        lane = args.lane.upper()
        actions_to_gen = [aid for aid, adef in ACTION_REGISTRY.items() if adef["lane"] == lane]
    elif args.top:
        scored = get_scored_actions(conn)
        actions_to_gen = [s["action_id"] for s in scored[:args.top] if s["action_id"] in ACTION_REGISTRY]
    elif args.all:
        actions_to_gen = list(ACTION_REGISTRY.keys())
    else:
        # Default: generate all registered actions
        actions_to_gen = list(ACTION_REGISTRY.keys())

    if not actions_to_gen:
        print("⚠ No actions to generate. Use --list to see available actions.")
        conn.close()
        return

    # Create output directories
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for subdir in ["LANE_A", "LANE_B", "LANE_C", "LANE_D", "LANE_E", "LANE_F", "ADMINISTRATIVE"]:
        (OUTPUT_DIR / subdir).mkdir(parents=True, exist_ok=True)

    print(f"\n📄 Generating {len(actions_to_gen)} court documents...\n")

    generated = 0
    for action_id in sorted(actions_to_gen):
        action_def = ACTION_REGISTRY.get(action_id)
        if not action_def:
            print(f"  ⚠ {action_id}: not in registry, skipping")
            continue

        print(f"  📝 {action_id}: {action_def['title']}...", end=" ")

        doc = gen.generate(action_id)
        if doc:
            # Determine output path
            lane = action_def["lane"]
            doc_type = action_def["type"]
            if doc_type in ("jtc_complaint", "bar_complaint"):
                subdir = "ADMINISTRATIVE"
            elif lane == "A":
                subdir = "LANE_A"
            elif lane == "B":
                subdir = "LANE_B"
            elif lane == "D":
                subdir = "LANE_D"           # PPO / Protection Order documents
            elif lane == "E":
                subdir = "LANE_E"           # Judicial misconduct documents
            elif lane == "F":
                subdir = "LANE_F"           # Appellate documents
            else:
                subdir = "LANE_C"

            filename = f"{action_id}_{action_def['title'].replace(' ', '_').replace('/', '_')}.md"
            filepath = OUTPUT_DIR / subdir / filename
            filepath.write_text(doc, encoding="utf-8")
            generated += 1
            print(f"✅ ({len(doc):,} chars)")
        else:
            print("⚠ skipped")

    conn.close()

    print(f"\n{'═' * 60}")
    print(f"  ✅ Generated {generated}/{len(actions_to_gen)} court documents")
    print(f"  📁 Output: {OUTPUT_DIR}")
    print(f"{'═' * 60}")
    print(f"\n⚠ IMPORTANT: These documents contain real evidence from the database")
    print(f"  but require HUMAN REVIEW before filing:")
    print(f"  - Fill in placeholder fields ([Address], [Phone], etc.)")
    print(f"  - Verify all factual assertions")
    print(f"  - Check citation accuracy")
    print(f"  - Ensure compliance with MCR formatting requirements")
    print(f"  - Have reviewed by licensed attorney if possible")


if __name__ == "__main__":
    main()
