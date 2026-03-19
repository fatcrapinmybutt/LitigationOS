#!/usr/bin/env python3
"""
MBP LitigationOS -- Michigan Court Document Templates
======================================================
MCR 2.113 compliant document templates for all major filing types.
Each template is a function that accepts parameters and returns formatted text.

Case: Andrew Pigors v. Tiffany Watson
Courts: 14th Circuit (Muskegon), Michigan COA (366810)
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional


# ── Case Constants ────────────────────────────────────────────────────
PLAINTIFF = "ANDREW PIGORS"
DEFENDANT = "TIFFANY WATSON"
PLAINTIFF_FULL = "Andrew Pigors"
DEFENDANT_FULL = "Tiffany Watson"
JUDGE = "Hon. Jenny L. McNeill"

CASE_NUMBERS = {
    "MEEK1": "2023-5907-PP",
    "MEEK2": "2024-001507-DC",
    "MEEK3": "COA 366810",
}

COURTS = {
    "MEEK1": "14TH JUDICIAL CIRCUIT COURT\nCOUNTY OF MUSKEGON",
    "MEEK2": "14TH JUDICIAL CIRCUIT COURT\nCOUNTY OF MUSKEGON",
    "MEEK3": "MICHIGAN COURT OF APPEALS",
}

COURT_ADDRESS = {
    "circuit": "990 Terrace Street, Muskegon, MI 49442",
    "coa": "Cadillac Place, 3020 W. Grand Blvd., Suite 14-300, Detroit, MI 48202",
}


# ── Helper Functions ──────────────────────────────────────────────────

def _today() -> str:
    """Return today's date formatted for filings."""
    return time.strftime("%B %d, %Y")


def _caption(lane: str = "MEEK1", doc_title: str = "") -> str:
    """Generate standard MCR 2.113 caption block."""
    court = COURTS.get(lane, COURTS["MEEK1"])
    case_no = CASE_NUMBERS.get(lane, CASE_NUMBERS["MEEK1"])

    if lane == "MEEK3":
        # COA caption format
        return f"""STATE OF MICHIGAN
IN THE {court}

{PLAINTIFF},                          COA Case No. {case_no}
        Plaintiff-Appellant,          Lower Court Case No. {CASE_NUMBERS['MEEK1']}

    v.                                {JUDGE}

{DEFENDANT},
        Defendant-Appellee.
__________________________________________/

{doc_title}
"""
    else:
        return f"""STATE OF MICHIGAN
IN THE {court}

{PLAINTIFF},                          Case No. {case_no}
        Plaintiff,
                                      {JUDGE}
    v.

{DEFENDANT},
        Defendant.
__________________________________________/

{doc_title}
"""


def _signature_block() -> str:
    """Generate pro se signature block."""
    return f"""Respectfully submitted,

Date: {_today()}

____________________________________
{PLAINTIFF_FULL}, Pro Se Plaintiff
[Address]
[City, State ZIP]
[Phone]
[Email]
"""


def _certificate_of_service(method: str = "first-class mail",
                             recipient: str = "") -> str:
    """Generate certificate of service per MCR 2.107."""
    if not recipient:
        recipient = f"{DEFENDANT_FULL}\n[Address]\n[City, State ZIP]"
    return f"""
CERTIFICATE OF SERVICE

    I hereby certify that on {_today()}, I served a true and correct copy of the
foregoing document upon the following by {method}:

    {recipient}

____________________________________
{PLAINTIFF_FULL}, Pro Se Plaintiff
"""


def _proof_of_service(method: str = "first-class mail",
                       recipient: str = "") -> str:
    """Generate proof of service per MCR 2.104."""
    if not recipient:
        recipient = f"{DEFENDANT_FULL}\n[Address]\n[City, State ZIP]"
    return f"""
PROOF OF SERVICE

STATE OF MICHIGAN  )
                   ) ss.
COUNTY OF MUSKEGON )

    I, {PLAINTIFF_FULL}, being duly sworn, depose and state that on {_today()},
I served a true and correct copy of the foregoing document upon the following party
by {method}:

    {recipient}

____________________________________
{PLAINTIFF_FULL}

Subscribed and sworn to before me
this _____ day of _____________, {time.strftime('%Y')}.

____________________________________
Notary Public, Muskegon County, Michigan
My Commission Expires: ______________
"""


def _numbered_paragraphs(paragraphs: List[str]) -> str:
    """Format paragraphs with sequential numbering."""
    lines = []
    for i, p in enumerate(paragraphs, 1):
        lines.append(f"    {i}. {p}")
        lines.append("")
    return "\n".join(lines)


# ── Document Templates ────────────────────────────────────────────────

def motion_template(
    title: str = "MOTION",
    lane: str = "MEEK1",
    statement_of_issues: List[str] = None,
    statement_of_facts: List[str] = None,
    arguments: List[Dict[str, str]] = None,
    relief_requested: List[str] = None,
    verification: bool = True,
    service_method: str = "first-class mail",
    authorities_cited: List[str] = None,
) -> str:
    """
    Generate MCR 2.113 compliant motion.

    arguments: list of dicts with keys: issue, rule, application, conclusion (IRAC)
    """
    doc_title = f"PLAINTIFF'S {title.upper()}"
    parts = [_caption(lane, doc_title)]

    # Statement of Issues Presented
    if statement_of_issues:
        parts.append("STATEMENT OF ISSUES PRESENTED\n")
        for i, issue in enumerate(statement_of_issues, 1):
            parts.append(f"    {i}. {issue}")
            parts.append("       Plaintiff answers: Yes.\n")

    # Controlling Authority
    if authorities_cited:
        parts.append("CONTROLLING AUTHORITY\n")
        for auth in authorities_cited:
            parts.append(f"    - {auth}")
        parts.append("")

    # Statement of Facts
    parts.append("STATEMENT OF FACTS\n")
    if statement_of_facts:
        parts.append(_numbered_paragraphs(statement_of_facts))
    else:
        parts.append("    1. [State relevant facts with record citations.]\n")

    # Argument
    parts.append("ARGUMENT\n")
    if arguments:
        for i, arg in enumerate(arguments, 1):
            section_letter = chr(64 + i)  # A, B, C...
            parts.append(f"    {section_letter}. {arg.get('issue', '[Issue]')}\n")
            parts.append(f"    RULE: {arg.get('rule', '[Cite governing authority]')}\n")
            parts.append(f"    APPLICATION: {arg.get('application', '[Apply rule to facts]')}\n")
            parts.append(f"    CONCLUSION: {arg.get('conclusion', '[State conclusion]')}\n")
    else:
        parts.append("    A. [Issue Heading]\n")
        parts.append("    RULE: [Cite governing rule, statute, or case law]\n")
        parts.append("    APPLICATION: [Apply the rule to the facts of this case]\n")
        parts.append("    CONCLUSION: [State the legal conclusion]\n")

    # Relief Requested
    parts.append("RELIEF REQUESTED\n")
    parts.append(f"    WHEREFORE, Plaintiff {PLAINTIFF_FULL} respectfully requests "
                 "that this Honorable Court:\n")
    if relief_requested:
        for i, relief in enumerate(relief_requested, 1):
            parts.append(f"    {i}. {relief}")
    else:
        parts.append("    1. [Specific relief requested]")
    parts.append("")
    parts.append("    And for such other and further relief as this Court deems just and proper.\n")

    # Verification
    if verification:
        parts.append("VERIFICATION\n")
        parts.append(f"    I, {PLAINTIFF_FULL}, declare under the penalties of perjury that the "
                     "facts stated in this motion are true to the best of my information, "
                     "knowledge, and belief.\n")

    # Signature
    parts.append(_signature_block())

    # Certificate + Proof of Service
    parts.append(_certificate_of_service(service_method))
    parts.append(_proof_of_service(service_method))

    return "\n".join(parts)


def brief_template(
    title: str = "BRIEF IN SUPPORT",
    lane: str = "MEEK3",
    table_of_contents: List[str] = None,
    index_of_authorities: List[Dict[str, str]] = None,
    jurisdictional_statement: str = "",
    questions_presented: List[str] = None,
    statement_of_facts: List[str] = None,
    arguments: List[Dict[str, str]] = None,
    conclusion: str = "",
    standard_of_review: str = "",
) -> str:
    """
    Generate appellate brief template per MCR 7.212.

    index_of_authorities: list of dicts {authority, pages}
    arguments: list of dicts {issue, rule, application, conclusion} (IRAC)
    """
    doc_title = f"PLAINTIFF-APPELLANT'S {title.upper()}"
    parts = [_caption(lane, doc_title)]

    # Table of Contents
    parts.append("TABLE OF CONTENTS\n")
    if table_of_contents:
        for entry in table_of_contents:
            parts.append(f"    {entry}")
    else:
        parts.append("    Table of Authorities .......................... ii")
        parts.append("    Jurisdictional Statement ...................... 1")
        parts.append("    Questions Presented ........................... 2")
        parts.append("    Statement of Facts ............................ 3")
        parts.append("    Standard of Review ............................ 5")
        parts.append("    Argument ...................................... 6")
        parts.append("    Conclusion .................................... 15")
    parts.append("")

    # Index of Authorities
    parts.append("INDEX OF AUTHORITIES\n")
    parts.append("Cases:\n")
    if index_of_authorities:
        for auth in index_of_authorities:
            if auth.get("type", "case") == "case":
                parts.append(f"    {auth['authority']} .......... {auth.get('pages', '')}")
        parts.append("\nStatutes:\n")
        for auth in index_of_authorities:
            if auth.get("type") == "statute":
                parts.append(f"    {auth['authority']} .......... {auth.get('pages', '')}")
        parts.append("\nCourt Rules:\n")
        for auth in index_of_authorities:
            if auth.get("type") == "rule":
                parts.append(f"    {auth['authority']} .......... {auth.get('pages', '')}")
    else:
        parts.append("    [Case citations with page references]")
        parts.append("\nStatutes:\n")
        parts.append("    [Statutory citations with page references]")
        parts.append("\nCourt Rules:\n")
        parts.append("    [Court rule citations with page references]")
    parts.append("")

    # Jurisdictional Statement
    parts.append("JURISDICTIONAL STATEMENT\n")
    if jurisdictional_statement:
        parts.append(f"    {jurisdictional_statement}\n")
    else:
        parts.append(f"    This Court has jurisdiction pursuant to MCR 7.203 and MCR 7.204. "
                     f"The trial court entered its order on [DATE]. Plaintiff-Appellant "
                     f"timely filed a Claim of Appeal on [DATE], within the 21-day period "
                     f"prescribed by MCR 7.204(A)(1).\n")

    # Questions Presented
    parts.append("QUESTIONS PRESENTED\n")
    if questions_presented:
        for i, q in enumerate(questions_presented, 1):
            parts.append(f"    {i}. {q}")
            parts.append("       Plaintiff-Appellant answers: Yes.\n")
    else:
        parts.append("    1. [State the question]\n")

    # Statement of Facts
    parts.append("STATEMENT OF FACTS\n")
    if statement_of_facts:
        parts.append(_numbered_paragraphs(statement_of_facts))
    else:
        parts.append("    [Provide factual background with record citations.]\n")

    # Standard of Review
    parts.append("STANDARD OF REVIEW\n")
    if standard_of_review:
        parts.append(f"    {standard_of_review}\n")
    else:
        parts.append("    Questions of law are reviewed de novo. Malczewski v Hofmann, "
                     "270 Mich App 455, 457 (2006). A trial court's findings of fact are "
                     "reviewed for clear error. MCR 2.613(C). Discretionary rulings are "
                     "reviewed for abuse of discretion. Berger v Berger, 277 Mich App 700, "
                     "705 (2008).\n")

    # Argument
    parts.append("ARGUMENT\n")
    if arguments:
        for i, arg in enumerate(arguments, 1):
            parts.append(f"    {i}. {arg.get('issue', '[Issue Heading]')}\n")
            parts.append(f"    Rule: {arg.get('rule', '[Governing authority]')}\n")
            parts.append(f"    Application: {arg.get('application', '[Apply to facts]')}\n")
            parts.append(f"    Conclusion: {arg.get('conclusion', '[Legal conclusion]')}\n")
    else:
        parts.append("    [IRAC structure for each issue]\n")

    # Conclusion
    parts.append("CONCLUSION\n")
    if conclusion:
        parts.append(f"    {conclusion}\n")
    else:
        parts.append(f"    For the foregoing reasons, Plaintiff-Appellant {PLAINTIFF_FULL} "
                     "respectfully requests that this Honorable Court reverse the trial "
                     "court's order and remand for further proceedings consistent with this "
                     "Court's opinion.\n")

    parts.append(_signature_block())
    parts.append(_certificate_of_service())

    return "\n".join(parts)


def affidavit_template(
    title: str = "AFFIDAVIT",
    lane: str = "MEEK1",
    statements: List[str] = None,
    affiant: str = PLAINTIFF_FULL,
) -> str:
    """Generate affidavit with numbered paragraphs and jurat."""
    doc_title = f"AFFIDAVIT OF {affiant.upper()}"
    parts = [_caption(lane, doc_title)]

    parts.append("STATE OF MICHIGAN  )")
    parts.append("                   ) ss.")
    parts.append("COUNTY OF MUSKEGON )\n")

    parts.append(f"    I, {affiant}, being first duly sworn, depose and state as follows:\n")

    if statements:
        parts.append(_numbered_paragraphs(statements))
    else:
        parts.append("    1. I am the Plaintiff in the above-captioned matter and I make this "
                     "Affidavit based upon my own personal knowledge.\n")
        parts.append("    2. [State facts.]\n")

    # Add standard closing paragraph
    para_num = len(statements) + 1 if statements else 3
    parts.append(f"    {para_num}. I declare under the penalties of perjury that the "
                 "foregoing statements are true and correct to the best of my "
                 "information, knowledge, and belief.\n")

    # Jurat
    parts.append("FURTHER AFFIANT SAYETH NOT.\n")
    parts.append(f"____________________________________")
    parts.append(f"{affiant}")
    parts.append("")
    parts.append(f"Subscribed and sworn to before me")
    parts.append(f"this _____ day of _____________, {time.strftime('%Y')}.\n")
    parts.append(f"____________________________________")
    parts.append(f"Notary Public, Muskegon County, Michigan")
    parts.append(f"My Commission Expires: ______________\n")

    parts.append(_certificate_of_service())

    return "\n".join(parts)


def response_template(
    title: str = "RESPONSE",
    lane: str = "MEEK1",
    responding_to: str = "",
    statement_of_facts: List[str] = None,
    responses_to_claims: List[Dict[str, str]] = None,
    arguments: List[Dict[str, str]] = None,
    relief_requested: List[str] = None,
    service_method: str = "first-class mail",
) -> str:
    """
    Generate response to opposing party's motion/filing.

    responses_to_claims: list of dicts {claim, response, authority}
    arguments: list of dicts {issue, rule, application, conclusion} (IRAC)
    """
    if responding_to:
        doc_title = f"PLAINTIFF'S {title.upper()} TO DEFENDANT'S {responding_to.upper()}"
    else:
        doc_title = f"PLAINTIFF'S {title.upper()}"
    parts = [_caption(lane, doc_title)]

    # Introduction
    parts.append("INTRODUCTION\n")
    parts.append(f"    NOW COMES Plaintiff {PLAINTIFF_FULL}, pro se, and respectfully files "
                 f"this Response to Defendant's {responding_to or '[Filing]'}, and in support "
                 f"thereof states as follows:\n")

    # Statement of Facts
    parts.append("STATEMENT OF FACTS\n")
    if statement_of_facts:
        parts.append(_numbered_paragraphs(statement_of_facts))
    else:
        parts.append("    1. [Relevant facts with record citations.]\n")

    # Responses to Specific Claims
    if responses_to_claims:
        parts.append("RESPONSE TO DEFENDANT'S CLAIMS\n")
        for i, rc in enumerate(responses_to_claims, 1):
            parts.append(f"    {i}. CLAIM: {rc.get('claim', '[Defendant claim]')}")
            parts.append(f"       RESPONSE: {rc.get('response', '[Response]')}")
            if rc.get("authority"):
                parts.append(f"       AUTHORITY: {rc['authority']}")
            parts.append("")

    # Argument
    parts.append("ARGUMENT\n")
    if arguments:
        for i, arg in enumerate(arguments, 1):
            section_letter = chr(64 + i)
            parts.append(f"    {section_letter}. {arg.get('issue', '[Issue]')}\n")
            parts.append(f"    RULE: {arg.get('rule', '[Authority]')}\n")
            parts.append(f"    APPLICATION: {arg.get('application', '[Application]')}\n")
            parts.append(f"    CONCLUSION: {arg.get('conclusion', '[Conclusion]')}\n")
    else:
        parts.append("    [IRAC structure for each argument]\n")

    # Relief
    parts.append("RELIEF REQUESTED\n")
    parts.append(f"    WHEREFORE, Plaintiff {PLAINTIFF_FULL} respectfully requests "
                 "that this Honorable Court:\n")
    if relief_requested:
        for i, relief in enumerate(relief_requested, 1):
            parts.append(f"    {i}. {relief}")
    else:
        parts.append(f"    1. Deny Defendant's {responding_to or '[Filing]'} in its entirety.")
    parts.append("")
    parts.append("    And for such other and further relief as this Court deems just and proper.\n")

    parts.append(_signature_block())
    parts.append(_certificate_of_service(service_method))
    parts.append(_proof_of_service(service_method))

    return "\n".join(parts)


def order_template(
    title: str = "PROPOSED ORDER",
    lane: str = "MEEK1",
    preamble: str = "",
    findings: List[str] = None,
    orders: List[str] = None,
) -> str:
    """Generate proposed order format for court submission."""
    doc_title = title.upper()
    parts = [_caption(lane, doc_title)]

    # Preamble
    parts.append(f"    At a session of said Court, held in the Courthouse in the")
    parts.append(f"City of Muskegon, County of Muskegon, State of Michigan on")
    parts.append(f"the _____ day of _____________, {time.strftime('%Y')}.\n")
    parts.append(f"    PRESENT: {JUDGE}\n")

    if preamble:
        parts.append(f"    {preamble}\n")
    else:
        parts.append(f"    This matter having come before the Court on Plaintiff's "
                     f"[Motion/Petition], and the Court having reviewed the file, "
                     f"pleadings, and arguments of the parties,\n")

    # Findings
    if findings:
        parts.append("    THE COURT FINDS:\n")
        for i, finding in enumerate(findings, 1):
            parts.append(f"    {i}. {finding}")
        parts.append("")

    # Orders
    parts.append("    IT IS HEREBY ORDERED:\n")
    if orders:
        for i, order in enumerate(orders, 1):
            parts.append(f"    {i}. {order}")
    else:
        parts.append("    1. [Specific order provisions]")
    parts.append("")

    parts.append("    IT IS SO ORDERED.\n")

    parts.append(f"Date: _______________\n")
    parts.append(f"____________________________________")
    parts.append(f"{JUDGE}")
    parts.append(f"14th Circuit Court Judge\n")

    return "\n".join(parts)


# ── Template Registry ─────────────────────────────────────────────────

TEMPLATES = {
    "motion": motion_template,
    "brief": brief_template,
    "affidavit": affidavit_template,
    "response": response_template,
    "objection": response_template,  # Objections use response format
    "complaint": motion_template,     # Complaints use motion format base
    "petition": motion_template,      # Petitions use motion format base
    "notice": motion_template,        # Notices use simplified motion format
    "order": order_template,
}


def get_template(doc_type: str, **kwargs) -> str:
    """Get filled template by document type."""
    try:
        func = TEMPLATES.get(doc_type.lower())
        if func:
            return func(**kwargs)
        return f"Unknown document type: {doc_type}. Available: {', '.join(TEMPLATES.keys())}"
    except Exception as e:
        return f"Template error: {str(e)[:200]}"


# ── CLI ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        doc_type = sys.argv[1].lower()
        output = get_template(doc_type)
        sys.stdout.buffer.write(output.encode("ascii", errors="replace"))
        sys.stdout.buffer.write(b"\n")
    else:
        print("Document Templates CLI")
        print(f"Available types: {', '.join(TEMPLATES.keys())}")
        print("Usage: python doc_templates.py <type>")
        print("Example: python doc_templates.py motion")
