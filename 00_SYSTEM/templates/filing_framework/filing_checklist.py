"""
Pre-Filing QA Checklist Generator
==================================

Generates court-specific, filing-type-specific checklists of every item
that must be verified before a document is filed.

Usage::

    from filing_checklist import generate_checklist

    items = generate_checklist("motion", "circuit", case_info)
    for item in items:
        print(f"[{'MANDATORY' if item['mandatory'] else 'OPTIONAL'}] "
              f"{item['item']} — {item['rule']}")
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


ChecklistItem = Dict[str, Any]  # item, rule, mandatory, description


# ── Base checklists by filing type ───────────────────────────────────────────

def _common_items() -> List[ChecklistItem]:
    """Items required for ALL Michigan court filings."""
    return [
        {
            "item": "Caption present and accurate",
            "rule": "MCR 2.113(A)",
            "mandatory": True,
            "description": (
                "Court name, case number, judge name, parties with designations, "
                "and document title must appear on the first page."
            ),
        },
        {
            "item": "Signature block complete",
            "rule": "MCR 2.114(B)",
            "mandatory": True,
            "description": (
                "Filing party's name, address, telephone number, and bar number "
                "(or pro se designation) must appear."
            ),
        },
        {
            "item": "Certificate of Service attached",
            "rule": "MCR 2.107(C)(3)",
            "mandatory": True,
            "description": (
                "Proof of service on all parties must accompany the filing. "
                "Must state method and date of service."
            ),
        },
        {
            "item": "Paper size 8.5 x 11 inches",
            "rule": "MCR 2.113(C)(1)",
            "mandatory": True,
            "description": "All pages must be standard letter size.",
        },
        {
            "item": "Margins at least 1 inch",
            "rule": "MCR 2.113(C)(1)",
            "mandatory": True,
            "description": "Top, bottom, left, and right margins must be at least 1 inch.",
        },
        {
            "item": "Font 12-point proportional",
            "rule": "MCR 2.113(C)(1)",
            "mandatory": True,
            "description": "Body text must be at least 12-point proportional font.",
        },
        {
            "item": "Double-spaced body text",
            "rule": "MCR 2.113(C)(1)",
            "mandatory": True,
            "description": (
                "Body text must be double-spaced. Block quotes and footnotes "
                "may be single-spaced."
            ),
        },
        {
            "item": "Pages consecutively numbered",
            "rule": "MCR 2.113(C)(1)",
            "mandatory": True,
            "description": "All pages must be numbered sequentially.",
        },
        {
            "item": "No AI/database references in text",
            "rule": "Professional standard",
            "mandatory": True,
            "description": (
                "Filing must not reference AI tools, databases, or scoring "
                "systems. All content must appear as attorney/pro se work product."
            ),
        },
        {
            "item": "Child referred to by initials only",
            "rule": "MCR 8.119(H)",
            "mandatory": True,
            "description": (
                "In family cases, minor children must be referred to by "
                "initials only per MCR 8.119(H)."
            ),
        },
        {
            "item": "Filing fee paid or fee waiver attached",
            "rule": "MCR 2.002",
            "mandatory": True,
            "description": (
                "Filing fee must be paid or an affidavit of indigency / "
                "fee waiver must accompany the filing."
            ),
        },
    ]


def _motion_items() -> List[ChecklistItem]:
    """Additional items for motions."""
    return [
        {
            "item": "Notice of hearing included",
            "rule": "MCR 2.119(C)(1)",
            "mandatory": True,
            "description": (
                "Motion must include notice of hearing specifying date, time, "
                "and location, served at least 9 days before hearing."
            ),
        },
        {
            "item": "Brief in support attached",
            "rule": "MCR 2.119(A)(2)",
            "mandatory": True,
            "description": (
                "A brief citing supporting authority must accompany the motion."
            ),
        },
        {
            "item": "Proposed order attached",
            "rule": "MCR 2.119(A)(2)",
            "mandatory": True,
            "description": "A proposed order granting the requested relief must be included.",
        },
        {
            "item": "Brief does not exceed 20 pages",
            "rule": "MCR 2.119(A)(3)",
            "mandatory": True,
            "description": "Motion briefs must not exceed 20 pages without leave of court.",
        },
        {
            "item": "Exhibits labeled and indexed",
            "rule": "MCR 2.113(F)",
            "mandatory": True,
            "description": (
                "All exhibits must be labeled (Exhibit A, B, etc.) and referenced "
                "in the text of the motion or brief."
            ),
        },
        {
            "item": "MCR 2.119 concise statement of issues",
            "rule": "MCR 2.119(A)(2)",
            "mandatory": True,
            "description": "Motion must contain a concise statement of the issues presented.",
        },
        {
            "item": "Verification/affidavit if facts outside record",
            "rule": "MCR 2.119(B)",
            "mandatory": False,
            "description": (
                "If the motion relies on facts not in the record, supporting "
                "affidavits should be attached."
            ),
        },
    ]


def _complaint_items() -> List[ChecklistItem]:
    """Additional items for complaints."""
    return [
        {
            "item": "Jurisdictional statement included",
            "rule": "MCR 2.111(B)(1)",
            "mandatory": True,
            "description": "Complaint must allege facts showing the court has jurisdiction.",
        },
        {
            "item": "Numbered paragraphs with factual allegations",
            "rule": "MCR 2.111(A)(1)",
            "mandatory": True,
            "description": (
                "Each factual allegation must be in a separately numbered paragraph."
            ),
        },
        {
            "item": "Each count states a separate claim",
            "rule": "MCR 2.111(A)(2)",
            "mandatory": True,
            "description": "Each cause of action must be stated in a separate count.",
        },
        {
            "item": "Demand for relief / prayer for relief",
            "rule": "MCR 2.111(B)(2)",
            "mandatory": True,
            "description": "Complaint must include a demand for judgment specifying relief sought.",
        },
        {
            "item": "Summons prepared for issuance",
            "rule": "MCR 2.102",
            "mandatory": True,
            "description": "Summons must be prepared for the clerk to issue upon filing.",
        },
        {
            "item": "Verified if required by statute",
            "rule": "MCR 2.114(A)",
            "mandatory": False,
            "description": (
                "Some claims require a verified complaint (sworn under oath). "
                "Check applicable statute."
            ),
        },
        {
            "item": "Civil case cover sheet",
            "rule": "MCR 2.113",
            "mandatory": True,
            "description": "A civil case cover sheet (MC 01) must accompany new complaints.",
        },
    ]


def _brief_items() -> List[ChecklistItem]:
    """Additional items for standalone briefs."""
    return [
        {
            "item": "Table of contents (if over 5 pages)",
            "rule": "Best practice",
            "mandatory": False,
            "description": "For longer briefs, a table of contents aids readability.",
        },
        {
            "item": "Index of authorities",
            "rule": "Best practice",
            "mandatory": False,
            "description": "Alphabetical list of all cases, statutes, and rules cited.",
        },
        {
            "item": "Does not exceed page limit",
            "rule": "MCR 2.119(A)(3)",
            "mandatory": True,
            "description": "Brief must not exceed the applicable page limit.",
        },
        {
            "item": "IRAC structure for each argument",
            "rule": "Professional standard",
            "mandatory": False,
            "description": (
                "Each argument should follow Issue-Rule-Application-Conclusion structure."
            ),
        },
        {
            "item": "All citations verified and accurate",
            "rule": "MCR 2.114(D)",
            "mandatory": True,
            "description": (
                "Every case, statute, and rule citation must be accurate and verifiable."
            ),
        },
    ]


def _emergency_motion_items() -> List[ChecklistItem]:
    """Additional items for emergency motions."""
    return [
        {
            "item": "Emergency designation clearly stated",
            "rule": "MCR 2.119(B)",
            "mandatory": True,
            "description": (
                "Document title and body must clearly designate the filing as "
                "an emergency motion."
            ),
        },
        {
            "item": "Irreparable harm alleged",
            "rule": "MCR 2.119(B)",
            "mandatory": True,
            "description": (
                "Motion must demonstrate that irreparable harm will occur "
                "without immediate relief."
            ),
        },
        {
            "item": "Explanation of why normal scheduling is inadequate",
            "rule": "MCR 2.119(B)",
            "mandatory": True,
            "description": (
                "Must explain why the matter cannot wait for regular motion scheduling."
            ),
        },
        {
            "item": "Efforts to notify opposing party documented",
            "rule": "MCR 2.119(B)",
            "mandatory": True,
            "description": (
                "Must describe efforts made to give opposing party notice "
                "or why notice was not possible."
            ),
        },
        {
            "item": "Proposed order for ex parte relief (if applicable)",
            "rule": "MCR 2.119(B)",
            "mandatory": True,
            "description": "If seeking ex parte relief, a proposed order must be included.",
        },
    ]


def _appellate_brief_items() -> List[ChecklistItem]:
    """Additional items for COA appellate briefs."""
    return [
        {
            "item": "Table of Contents with page references",
            "rule": "MCR 7.212(C)(1)",
            "mandatory": True,
            "description": "Must list all sections with corresponding page numbers.",
        },
        {
            "item": "Index of Authorities with page references",
            "rule": "MCR 7.212(C)(2)",
            "mandatory": True,
            "description": (
                "Alphabetical list of all authorities cited with page numbers "
                "where each is referenced."
            ),
        },
        {
            "item": "Jurisdictional statement",
            "rule": "MCR 7.212(C)(3)",
            "mandatory": True,
            "description": (
                "Must state the basis for the Court of Appeals' jurisdiction, "
                "including the order or judgment appealed and the date of entry."
            ),
        },
        {
            "item": "Statement of Questions Presented",
            "rule": "MCR 7.212(C)(4)",
            "mandatory": True,
            "description": "Each question must be separately numbered and concisely stated.",
        },
        {
            "item": "Statement of Facts with record citations",
            "rule": "MCR 7.212(C)(6)",
            "mandatory": True,
            "description": (
                "Facts must be supported by specific references to the lower court record."
            ),
        },
        {
            "item": "Standard of review identified for each issue",
            "rule": "MCR 7.212(C)(7)",
            "mandatory": True,
            "description": "Each issue must state the applicable standard of review.",
        },
        {
            "item": "Appendix with required documents",
            "rule": "MCR 7.212(E)",
            "mandatory": True,
            "description": (
                "Must include the order/judgment appealed, relevant register of "
                "actions, and cited portions of the record."
            ),
        },
        {
            "item": "Does not exceed 50 pages",
            "rule": "MCR 7.212(B)",
            "mandatory": True,
            "description": "Appellant and appellee briefs must not exceed 50 pages.",
        },
        {
            "item": "Proof of filing claim of appeal timely",
            "rule": "MCR 7.204(A)",
            "mandatory": True,
            "description": "Claim of appeal must have been filed within 21 days of the order.",
        },
    ]


def _msc_application_items() -> List[ChecklistItem]:
    """Additional items for MSC applications."""
    return [
        {
            "item": "Questions Presented prominently placed",
            "rule": "MCR 7.306(D)(1)",
            "mandatory": True,
            "description": (
                "Questions presented must appear on the first page after the cover."
            ),
        },
        {
            "item": "Table of Contents with page references",
            "rule": "MCR 7.306(D)",
            "mandatory": True,
            "description": "All sections listed with page numbers.",
        },
        {
            "item": "Index of Authorities",
            "rule": "MCR 7.306(D)",
            "mandatory": True,
            "description": "Alphabetical list of all cited authorities with page references.",
        },
        {
            "item": "Jurisdictional statement (MSC)",
            "rule": "MCR 7.306(D)(2)",
            "mandatory": True,
            "description": (
                "Must establish that the MSC has jurisdiction, identifying the "
                "COA decision or other basis."
            ),
        },
        {
            "item": "Statement of Facts",
            "rule": "MCR 7.306(D)(3)",
            "mandatory": True,
            "description": (
                "Concise statement of material facts with record citations."
            ),
        },
        {
            "item": "Argument section with reasons to grant leave",
            "rule": "MCR 7.306(D)(4)",
            "mandatory": True,
            "description": (
                "Must explain why the case involves a significant question of law "
                "or conflict with published decisions."
            ),
        },
        {
            "item": "Appendix with COA decision and relevant orders",
            "rule": "MCR 7.306(D)(5)",
            "mandatory": True,
            "description": (
                "Must include the COA opinion/order, lower court orders, and "
                "key portions of the record."
            ),
        },
        {
            "item": "Does not exceed 50 pages",
            "rule": "MCR 7.312(A)",
            "mandatory": True,
            "description": "Application for leave to appeal must not exceed 50 pages.",
        },
        {
            "item": "Filed within 56 days of COA decision",
            "rule": "MCR 7.305(C)(2)",
            "mandatory": True,
            "description": "Application must be filed within 56 days of the COA decision.",
        },
        {
            "item": "Emergency designation if applicable",
            "rule": "MCR 7.315(C)",
            "mandatory": False,
            "description": (
                "If irreparable harm is imminent, emergency application may be "
                "filed with expedited review request."
            ),
        },
    ]


def _federal_complaint_items() -> List[ChecklistItem]:
    """Additional items for federal court complaints."""
    return [
        {
            "item": "Subject-matter jurisdiction alleged",
            "rule": "FRCP 8(a)(1)",
            "mandatory": True,
            "description": (
                "Must state the grounds for federal jurisdiction "
                "(28 USC § 1331 federal question, § 1332 diversity, § 1343 civil rights)."
            ),
        },
        {
            "item": "Short and plain statement of the claim",
            "rule": "FRCP 8(a)(2)",
            "mandatory": True,
            "description": (
                "Complaint must contain a short and plain statement of the claim "
                "showing the pleader is entitled to relief."
            ),
        },
        {
            "item": "Demand for judgment / relief sought",
            "rule": "FRCP 8(a)(3)",
            "mandatory": True,
            "description": "Must include a demand for the relief sought.",
        },
        {
            "item": "Civil cover sheet (JS 44) attached",
            "rule": "LCivR 3.1",
            "mandatory": True,
            "description": "Civil Cover Sheet form JS 44 must accompany the complaint.",
        },
        {
            "item": "Summons prepared (Form AO 440)",
            "rule": "FRCP 4(b)",
            "mandatory": True,
            "description": "Summons in the form prescribed by AO 440 for clerk issuance.",
        },
        {
            "item": "14-point font for WDMI",
            "rule": "LCivR 10.6(a)",
            "mandatory": True,
            "description": (
                "Western District of Michigan requires 14-point proportional font."
            ),
        },
        {
            "item": "Service within 90 days of filing",
            "rule": "FRCP 4(m)",
            "mandatory": True,
            "description": "Defendant must be served within 90 days of filing.",
        },
        {
            "item": "Plausibility standard met (Twombly/Iqbal)",
            "rule": "FRCP 8(a)(2); Bell Atlantic v. Twombly, 550 U.S. 544 (2007)",
            "mandatory": True,
            "description": (
                "Factual allegations must be sufficient to state a plausible claim "
                "for relief — not merely possible."
            ),
        },
        {
            "item": "Qualified immunity analysis if suing officials",
            "rule": "42 USC § 1983; Harlow v. Fitzgerald, 457 U.S. 800 (1982)",
            "mandatory": False,
            "description": (
                "If suing government officials under § 1983, must address "
                "qualified immunity in anticipation of defense."
            ),
        },
    ]


# ── Filing-type registry ─────────────────────────────────────────────────────

_FILING_TYPE_ITEMS = {
    "motion": _motion_items,
    "complaint": _complaint_items,
    "brief": _brief_items,
    "emergency_motion": _emergency_motion_items,
    "appellate_brief": _appellate_brief_items,
    "msc_application": _msc_application_items,
    "federal_complaint": _federal_complaint_items,
}


# ── Court-specific overrides ─────────────────────────────────────────────────

def _court_overrides(court: str, division: str = "Southern") -> List[ChecklistItem]:
    """Return additional or modified items for specific courts."""
    court = court.lower().strip()

    if court == "wdmi":
        return [
            {
                "item": "Font is 14-point per LCivR 10.6(a)",
                "rule": "LCivR 10.6(a)",
                "mandatory": True,
                "description": (
                    f"WDMI {division} Division requires 14-point font "
                    f"(not 12-point)."
                ),
            },
            {
                "item": "Filed via CM/ECF",
                "rule": "LCivR 5.7",
                "mandatory": True,
                "description": (
                    f"All filings in the {division} Division must be "
                    f"submitted electronically via CM/ECF."
                ),
            },
        ]

    if court == "coa":
        return [
            {
                "item": "Filed via MiFILE",
                "rule": "MCR 7.202(4)",
                "mandatory": True,
                "description": "All COA filings must be submitted via MiFILE.",
            },
        ]

    if court == "msc":
        return [
            {
                "item": "Filed via MiFILE",
                "rule": "MCR 1.109(G)(3)",
                "mandatory": True,
                "description": "All MSC filings must be submitted via MiFILE.",
            },
        ]

    return []


# ── Public API ───────────────────────────────────────────────────────────────

def generate_checklist(
    filing_type: str,
    court: str = "circuit",
    case_info: Optional[Dict[str, Any]] = None,
    division: str = "Southern",
) -> List[ChecklistItem]:
    """Generate a pre-filing QA checklist.

    Args:
        filing_type: One of ``motion``, ``complaint``, ``brief``,
            ``emergency_motion``, ``appellate_brief``, ``msc_application``,
            ``federal_complaint``.
        court: Target court — ``circuit``, ``coa``, ``msc``, ``wdmi``,
            ``district``.
        case_info: Optional dict with case metadata for context-aware checks.
        division: WDMI division name (default ``"Southern"``).

    Returns:
        List of checklist items, each a dict with keys:
        ``item``, ``rule``, ``mandatory``, ``description``.

    Raises:
        ValueError: If *filing_type* is not recognized.
    """
    filing_type = filing_type.lower().strip()
    if filing_type not in _FILING_TYPE_ITEMS:
        raise ValueError(
            f"Unknown filing type '{filing_type}'. "
            f"Choose from: {', '.join(_FILING_TYPE_ITEMS)}"
        )

    # Build checklist: common + type-specific + court overrides
    checklist: List[ChecklistItem] = []

    # Common items (skip for federal — they have their own baseline)
    if court.lower().strip() != "wdmi":
        checklist.extend(_common_items())
    else:
        # Federal common items (adjusted rules)
        for item in _common_items():
            federal_item = item.copy()
            # Adjust MI-specific rules to federal equivalents
            if item["rule"] == "MCR 2.113(A)":
                federal_item["rule"] = "FRCP 10(a)"
            elif item["rule"] == "MCR 2.114(B)":
                federal_item["rule"] = "FRCP 11(a)"
            elif item["rule"] == "MCR 2.107(C)(3)":
                federal_item["rule"] = "FRCP 5(d)(1)"
            elif item["rule"] == "MCR 2.113(C)(1)":
                federal_item["rule"] = "LCivR 10.6(a)"
                # Override 12pt → 14pt for WDMI per LCivR 10.6(a)
                if "Font" in item["item"] or "font" in item["item"].lower():
                    federal_item["item"] = "Font 14-point proportional"
                    federal_item["description"] = (
                        "Body text must be at least 14-point proportional "
                        "font per LCivR 10.6(a)."
                    )
            checklist.append(federal_item)

    # Type-specific items
    checklist.extend(_FILING_TYPE_ITEMS[filing_type]())

    # Court-specific overrides
    checklist.extend(_court_overrides(court, division=division))

    return checklist


def get_supported_filing_types() -> List[str]:
    """Return list of supported filing type identifiers."""
    return list(_FILING_TYPE_ITEMS.keys())


if __name__ == "__main__":
    import sys

    filing = sys.argv[1] if len(sys.argv) > 1 else "motion"
    court = sys.argv[2] if len(sys.argv) > 2 else "circuit"

    items = generate_checklist(filing, court)
    print(f"=== Pre-Filing QA Checklist: {filing.upper()} ({court.upper()}) ===")
    print(f"Total items: {len(items)}\n")

    mandatory = [i for i in items if i["mandatory"]]
    optional = [i for i in items if not i["mandatory"]]

    print(f"MANDATORY ({len(mandatory)}):")
    for i, item in enumerate(mandatory, 1):
        print(f"  {i:2d}. [{item['rule']}] {item['item']}")
        print(f"      {item['description']}")

    if optional:
        print(f"\nOPTIONAL ({len(optional)}):")
        for i, item in enumerate(optional, 1):
            print(f"  {i:2d}. [{item['rule']}] {item['item']}")
            print(f"      {item['description']}")
