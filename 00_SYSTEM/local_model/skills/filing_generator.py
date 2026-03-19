#!/usr/bin/env python3
"""
MBP LitigationOS — Filing Generator Skill (m42)
=================================================
Generate court-ready filings from templates for all Michigan forums.
MCR 2.113 compliant: caption, numbered paragraphs, signature block, CoS.

Courts: 14th Circuit, COA (366810), MSC, JTC, USDC Western MI.
Case: Pigors v. Watson — All Lanes (A-G).

Authority:
    MCR 2.113 — Form of pleadings, motions
    MCR 7.212 — Appellate briefs
    MCR 7.306 — Original proceedings (MSC)
    FRCP 10, 11 — Federal form requirements
    MCR 9.220 — JTC complaints

Usage:
    from skills.filing_generator import FilingGenerator
    gen = FilingGenerator()
    md = gen.generate_motion('emergency_parenting_time', '14th_circuit', ...)
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent
    if "skills" in str(Path(__file__)) else Path(__file__).resolve().parent))
try:
    from cycle_method import cycle_json, cycle_print
except ImportError:
    cycle_json = lambda obj, **kw: print(json.dumps(obj, default=str))
    cycle_print = print

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)

# ── Court configurations ──────────────────────────────────────────────

COURTS = {
    "14th_circuit": {
        "name": "14TH CIRCUIT COURT FOR THE COUNTY OF MUSKEGON",
        "state_header": "STATE OF MICHIGAN",
        "case_no": "2024-001507-DC",
        "judge": "Hon. Jenny L. McNeill",
        "plaintiff_role": "Plaintiff",
        "defendant_role": "Defendant",
        "rule_set": "MCR",
    },
    "coa": {
        "name": "MICHIGAN COURT OF APPEALS",
        "state_header": "STATE OF MICHIGAN",
        "case_no": "366810",
        "judge": "Panel TBD",
        "plaintiff_role": "Plaintiff-Appellant",
        "defendant_role": "Defendant-Appellee",
        "rule_set": "MCR 7.2xx",
    },
    "msc": {
        "name": "MICHIGAN SUPREME COURT",
        "state_header": "STATE OF MICHIGAN",
        "case_no": "[To Be Assigned]",
        "judge": "",
        "plaintiff_role": "Plaintiff-Appellant",
        "defendant_role": "Defendant-Appellee",
        "rule_set": "MCR 7.3xx",
    },
    "jtc": {
        "name": "JUDICIAL TENURE COMMISSION",
        "state_header": "STATE OF MICHIGAN",
        "case_no": "[To Be Assigned]",
        "judge": "",
        "plaintiff_role": "Complainant",
        "defendant_role": "Respondent Judge",
        "rule_set": "MCR 9.2xx",
    },
    "usdc": {
        "name": "UNITED STATES DISTRICT COURT\nWESTERN DISTRICT OF MICHIGAN — SOUTHERN DIVISION",
        "state_header": "",
        "case_no": "[To Be Assigned]",
        "judge": "",
        "plaintiff_role": "Plaintiff",
        "defendant_role": "Defendant",
        "rule_set": "FRCP / LCivR",
    },
}

PLAINTIFF_BLOCK = """ANDREW M. PIGORS, Pro Se
[Address Line 1]
Muskegon, MI 49XXX
Phone: [Phone]
Email: [Email]"""

DEFENDANT_INFO = {
    "name": "TIFFANY WATSON (fka PIGORS)",
    "attorney": "Ronald E. Berry (P27889)",
}


def _get_db() -> Optional[sqlite3.Connection]:
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA query_only=ON")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        return None


def _today() -> str:
    return datetime.now().strftime("%B %d, %Y")


# ── Caption generator ─────────────────────────────────────────────────

def _build_caption(court_key: str, title: str, case_number: str = "") -> str:
    court = COURTS.get(court_key, COURTS["14th_circuit"])
    cn = case_number or court["case_no"]
    header = court["state_header"]
    lines = []
    lines.append("=" * 80)
    if header:
        lines.append(header)
    lines.append(f"IN THE {court['name']}")
    lines.append("")
    lines.append(f"ANDREW PIGORS,{' ' * 30}Case No. {cn}")
    lines.append(f"    {court['plaintiff_role']},{' ' * 25}{court['judge']}")
    lines.append("")
    lines.append("v.")
    lines.append("")
    lines.append(f"{DEFENDANT_INFO['name']},")
    lines.append(f"    {court['defendant_role']}.")
    lines.append("_" * 80)
    lines.append("")
    lines.append(f"**{title.upper()}**")
    lines.append("")
    return "\n".join(lines)


# ── Signature block ───────────────────────────────────────────────────

def _signature_block() -> str:
    return f"""
Respectfully submitted,

Date: {_today()}

_______________________________
Andrew M. Pigors, Pro Se
[Address]
Muskegon, MI 49XXX
Phone: [Phone]
Email: [Email]
"""


# ── Certificate of Service ────────────────────────────────────────────

def _certificate_of_service(court_key: str) -> str:
    lines = [
        "",
        "## CERTIFICATE OF SERVICE",
        "",
        f"I, Andrew M. Pigors, certify that on {_today()}, I served a true copy",
        "of this document upon all parties and the Court by the following method:",
        "",
        f"**{DEFENDANT_INFO['attorney']}**",
        "Attorney for Defendant",
        "[Address]",
        "Method: ☐ First-Class Mail  ☐ Email  ☐ MiFile  ☐ Personal Service",
        "",
    ]
    if court_key in ("coa", "msc"):
        lines.extend([
            "**Clerk of the 14th Circuit Court**",
            "990 Terrace Street, Muskegon, MI 49442",
            "Method: ☐ First-Class Mail  ☐ Email",
            "",
        ])
    lines.extend([
        "_______________________________",
        "Andrew M. Pigors, Pro Se",
        f"Date: {_today()}",
    ])
    return "\n".join(lines)


# ── Numbered paragraphs formatter ─────────────────────────────────────

def _number_paragraphs(paragraphs: List[str], start: int = 1) -> str:
    lines = []
    for i, p in enumerate(paragraphs, start=start):
        lines.append(f"{i}. {p}")
        lines.append("")
    return "\n".join(lines)


# ── Authority fetcher ─────────────────────────────────────────────────

def _fetch_authorities(keywords: List[str], limit: int = 5) -> List[Dict]:
    conn = _get_db()
    if not conn:
        return []
    results = []
    try:
        for kw in keywords:
            rows = conn.execute(
                "SELECT rule_id, rule_text, source FROM auth_rules "
                "WHERE rule_text LIKE ? LIMIT ?",
                (f"%{kw}%", limit),
            ).fetchall()
            for r in rows:
                results.append(dict(r))
    except Exception:
        pass
    finally:
        conn.close()
    return results


# ══════════════════════════════════════════════════════════════════════
#  PUBLIC API
# ══════════════════════════════════════════════════════════════════════


class FilingGenerator:
    """Generate complete court filings from templates."""

    def generate_motion(
        self,
        motion_type: str,
        court: str = "14th_circuit",
        case_number: str = "",
        facts: Optional[List[str]] = None,
        relief_requested: Optional[List[str]] = None,
        legal_basis: Optional[List[str]] = None,
        exhibits: Optional[List[str]] = None,
    ) -> str:
        """
        Generate a complete motion per MCR 2.113.

        Args:
            motion_type: e.g. 'emergency_parenting_time', 'reconsideration',
                         'compel_discovery', 'disqualification'
            court: Court key from COURTS dict
            case_number: Override case number
            facts: List of factual paragraphs
            relief_requested: List of relief items
            legal_basis: List of legal authority strings
            exhibits: List of exhibit references
        Returns:
            Complete motion in markdown format
        """
        title_map = {
            "emergency_parenting_time": "EMERGENCY MOTION TO RESTORE PARENTING TIME",
            "reconsideration": "MOTION FOR RECONSIDERATION",
            "compel_discovery": "MOTION TO COMPEL DISCOVERY",
            "disqualification": "MOTION FOR DISQUALIFICATION OF JUDGE",
            "vacate_ex_parte": "MOTION TO VACATE EX PARTE ORDER",
            "summary_disposition": "MOTION FOR SUMMARY DISPOSITION",
            "contempt": "MOTION FOR CONTEMPT",
            "change_custody": "MOTION TO CHANGE CUSTODY",
        }
        title = title_map.get(motion_type, f"MOTION: {motion_type.upper()}")

        facts = facts or ["[Insert factual allegations here]"]
        relief_requested = relief_requested or ["[Specify relief requested]"]
        legal_basis = legal_basis or ["[Cite applicable authority]"]

        sections = []
        sections.append(_build_caption(court, title, case_number))

        # Introduction
        sections.append("## INTRODUCTION\n")
        sections.append(
            "Plaintiff Andrew M. Pigors, appearing pro se, respectfully moves this "
            f"Honorable Court for the relief described herein and states as follows:\n"
        )

        # Statement of Facts
        sections.append("## STATEMENT OF FACTS\n")
        sections.append(_number_paragraphs(facts))

        # Legal Authority (IRAC: Rule)
        sections.append("## LEGAL AUTHORITY\n")
        for basis in legal_basis:
            sections.append(f"- {basis}\n")

        # Argument (IRAC: Application)
        sections.append("## ARGUMENT\n")
        sections.append(
            "### I. THIS COURT SHOULD GRANT THE REQUESTED RELIEF\n\n"
            "[Apply the legal authority to the facts of this case. "
            "Each argument should follow IRAC: Issue → Rule → Application → Conclusion.]\n"
        )

        # Relief Requested (IRAC: Conclusion)
        sections.append("## RELIEF REQUESTED\n")
        sections.append("WHEREFORE, Plaintiff respectfully requests this Court:\n")
        for i, relief in enumerate(relief_requested, 1):
            sections.append(f"{i}. {relief}\n")
        sections.append(
            f"{len(relief_requested) + 1}. Grant such other and further relief "
            "as this Court deems just and proper.\n"
        )

        # Exhibits
        if exhibits:
            sections.append("## EXHIBITS\n")
            for i, ex in enumerate(exhibits, 1):
                sections.append(f"Exhibit {chr(64+i)}: {ex}\n")

        sections.append(_signature_block())
        sections.append(_certificate_of_service(court))

        return "\n".join(sections)

    def generate_brief(
        self,
        brief_type: str = "appellant",
        court: str = "coa",
        issues: Optional[List[str]] = None,
        arguments: Optional[List[Dict[str, str]]] = None,
        standard_of_review: str = "de novo",
    ) -> str:
        """
        Generate an appellate brief per MCR 7.212 / MCR 7.306.

        Args:
            brief_type: 'appellant', 'appellee', 'reply', 'amicus', 'msc_application'
            court: 'coa' or 'msc'
            issues: List of issues presented
            arguments: List of dicts with 'heading', 'rule', 'application', 'conclusion'
            standard_of_review: 'de novo', 'clear_error', 'abuse_of_discretion', 'plain_error'
        Returns:
            Complete brief in markdown format
        """
        title_map = {
            "appellant": "BRIEF OF PLAINTIFF-APPELLANT",
            "appellee": "BRIEF OF DEFENDANT-APPELLEE",
            "reply": "REPLY BRIEF OF PLAINTIFF-APPELLANT",
            "amicus": "BRIEF OF AMICUS CURIAE",
            "msc_application": "APPLICATION FOR LEAVE TO APPEAL",
        }
        title = title_map.get(brief_type, f"BRIEF: {brief_type.upper()}")
        issues = issues or ["[State each issue presented for review]"]
        arguments = arguments or [
            {"heading": "[Argument Heading]", "rule": "[Rule]",
             "application": "[Application]", "conclusion": "[Conclusion]"}
        ]

        review_map = {
            "de novo": "Questions of law are reviewed de novo. *Mahaffey v Att'y Gen*, "
                       "222 Mich App 325, 334 (1997).",
            "clear_error": "Findings of fact are reviewed for clear error. MCR 2.613(C).",
            "abuse_of_discretion": "The trial court's decision is reviewed for abuse of "
                                   "discretion. *Vodvarka v Grasmeyer*, 259 Mich App 499, 508 (2003).",
            "plain_error": "Unpreserved issues are reviewed for plain error affecting "
                          "substantial rights. *People v Carines*, 460 Mich 750, 763 (1999).",
        }

        sections = []
        sections.append(_build_caption(court, title))

        # Table of Contents
        sections.append("## TABLE OF CONTENTS\n")
        sections.append("Index of Authorities .................. ii")
        sections.append("Statement of Jurisdiction ............. 1")
        sections.append("Statement of Questions Presented ...... 2")
        sections.append("Statement of Facts ................... 3")
        sections.append("Standard of Review ................... 5")
        sections.append("Argument ............................. 6")
        sections.append("Relief Requested ..................... 20")
        sections.append("")

        # Index of Authorities
        sections.append("## INDEX OF AUTHORITIES\n")
        sections.append("*[To be completed with all cited authorities]*\n")

        # Jurisdictional Statement
        sections.append("## STATEMENT OF JURISDICTION\n")
        if court == "coa":
            sections.append(
                "This Court has jurisdiction under MCR 7.203(A)(1) as an appeal of right "
                "from a final order of the 14th Circuit Court.\n"
            )
        elif court == "msc":
            sections.append(
                "This Court has original and superintending jurisdiction under "
                "Const 1963, art 6, § 4 and MCR 7.306.\n"
            )

        # Issues Presented
        sections.append("## STATEMENT OF QUESTIONS PRESENTED\n")
        for i, issue in enumerate(issues, 1):
            sections.append(f"**{i}.** {issue}\n")
            sections.append("Plaintiff-Appellant answers: **Yes.**\n")

        # Statement of Facts
        sections.append("## STATEMENT OF FACTS\n")
        sections.append("[Comprehensive factual recitation with record citations]\n")

        # Standard of Review
        sections.append("## STANDARD OF REVIEW\n")
        sections.append(review_map.get(standard_of_review, review_map["de novo"]))
        sections.append("")

        # Arguments
        sections.append("## ARGUMENT\n")
        for i, arg in enumerate(arguments, 1):
            roman = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"][i - 1] if i <= 8 else str(i)
            sections.append(f"### {roman}. {arg['heading'].upper()}\n")
            sections.append(f"**Rule:** {arg['rule']}\n")
            sections.append(f"**Application:** {arg['application']}\n")
            sections.append(f"**Conclusion:** {arg['conclusion']}\n")

        # Relief
        sections.append("## RELIEF REQUESTED\n")
        sections.append(
            "WHEREFORE, Plaintiff-Appellant respectfully requests this Court "
            "reverse the trial court's orders, vacate all ex parte orders entered "
            "without proper notice, and remand for proceedings consistent with due "
            "process and the best interest factors under MCL 722.23.\n"
        )

        sections.append(_signature_block())
        sections.append(_certificate_of_service(court))

        return "\n".join(sections)

    def generate_response(
        self,
        original_motion: str,
        our_position: str,
        court: str = "14th_circuit",
        counter_arguments: Optional[List[Dict[str, str]]] = None,
        exhibits: Optional[List[str]] = None,
    ) -> str:
        """
        Generate a response/opposition to an opposing motion.

        Args:
            original_motion: Title/description of the motion being opposed
            our_position: Summary of our opposition stance
            court: Court key
            counter_arguments: List of dicts with 'their_claim', 'our_response', 'authority'
            exhibits: List of exhibit references
        Returns:
            Complete response in markdown format
        """
        title = f"RESPONSE IN OPPOSITION TO {original_motion.upper()}"
        counter_arguments = counter_arguments or [
            {"their_claim": "[Opposing claim]",
             "our_response": "[Our rebuttal]",
             "authority": "[Supporting authority]"}
        ]

        sections = []
        sections.append(_build_caption(court, title))

        sections.append("## INTRODUCTION\n")
        sections.append(
            f"Plaintiff Andrew M. Pigors, appearing pro se, respectfully submits this "
            f"Response in Opposition and states:\n"
        )

        sections.append("## STATEMENT OF POSITION\n")
        sections.append(f"{our_position}\n")

        sections.append("## COUNTER-ARGUMENTS\n")
        for i, ca in enumerate(counter_arguments, 1):
            sections.append(f"### {i}. Re: {ca['their_claim']}\n")
            sections.append(f"{ca['our_response']}\n")
            sections.append(f"**Authority:** {ca['authority']}\n")

        sections.append("## CONCLUSION\n")
        sections.append(
            "For the reasons stated above, Defendant's motion should be DENIED.\n"
        )

        if exhibits:
            sections.append("## EXHIBITS\n")
            for i, ex in enumerate(exhibits, 1):
                sections.append(f"Exhibit {chr(64+i)}: {ex}\n")

        sections.append(_signature_block())
        sections.append(_certificate_of_service(court))

        return "\n".join(sections)

    def list_courts(self) -> Dict[str, Dict]:
        """Return available court configurations."""
        return {k: {"name": v["name"], "case_no": v["case_no"], "rule_set": v["rule_set"]}
                for k, v in COURTS.items()}

    def list_motion_types(self) -> List[str]:
        """Return available motion templates."""
        return [
            "emergency_parenting_time", "reconsideration", "compel_discovery",
            "disqualification", "vacate_ex_parte", "summary_disposition",
            "contempt", "change_custody",
        ]


# ── CLI / JSON-RPC entry ──────────────────────────────────────────────

def handle_rpc(method: str, params: Dict[str, Any] = None) -> Dict:
    """JSON-RPC dispatch for filing_generator methods."""
    params = params or {}
    gen = FilingGenerator()
    dispatch = {
        "generate_motion": gen.generate_motion,
        "generate_brief": gen.generate_brief,
        "generate_response": gen.generate_response,
        "list_courts": gen.list_courts,
        "list_motion_types": gen.list_motion_types,
    }
    fn = dispatch.get(method)
    if not fn:
        return {"error": f"Unknown method: {method}", "available": list(dispatch.keys())}
    try:
        result = fn(**params)
        return {"result": result, "method": method, "status": "ok"}
    except Exception as e:
        return {"error": str(e), "method": method}


if __name__ == "__main__":
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    gen = FilingGenerator()
    print("=== Filing Generator Skill (m42) ===")
    print(f"Courts: {list(COURTS.keys())}")
    print(f"Motion types: {gen.list_motion_types()}")
    sample = gen.generate_motion(
        "emergency_parenting_time",
        "14th_circuit",
        facts=["On August 8, 2025, five ex parte orders suspended ALL parenting time.",
               "567+ days of parent-child separation have elapsed."],
        relief_requested=["Immediately restore parenting time per MCL 722.27a.",
                         "Vacate the August 8, 2025 ex parte orders."],
        legal_basis=["MCR 3.207(C)(2) — ex parte order requirements",
                    "MCL 722.27a(3) — parenting time presumption",
                    "Troxel v Granville, 530 US 57 (2000) — fundamental right"],
    )
    print(f"\nSample motion length: {len(sample)} chars")
    print("✅ Filing Generator operational")
