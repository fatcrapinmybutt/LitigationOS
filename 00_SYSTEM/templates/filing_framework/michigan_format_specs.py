"""
Michigan Court Format Specifications
=====================================

Pre-loaded format specifications for Michigan state and federal courts.
Each spec dict maps to a row in the ``format_specs`` database table.

Supported courts:
    - circuit   — Michigan Circuit Court (MCR 2.113, 2.119)
    - coa       — Michigan Court of Appeals (MCR 7.212)
    - msc       — Michigan Supreme Court (MCR 7.306, 7.312)
    - wdmi      — US District Court, Western District of MI (LCivR 10.6)
    - district  — Michigan 60th District Court (MCR 4.002)
"""

from __future__ import annotations

from typing import Dict, List


# ── Michigan Circuit Court ───────────────────────────────────────────────────

CIRCUIT_COURT_SPECS: Dict[str, Dict[str, str]] = {
    "paper_size": {
        "spec_value": "8.5 x 11 inches (letter)",
        "authority": "MCR 2.113(C)(1)",
    },
    "top_margin": {
        "spec_value": "1 inch minimum (2.5 inches on first page for court stamp)",
        "authority": "MCR 2.113(C)(1)",
    },
    "bottom_margin": {
        "spec_value": "1 inch minimum",
        "authority": "MCR 2.113(C)(1)",
    },
    "left_margin": {
        "spec_value": "1 inch minimum",
        "authority": "MCR 2.113(C)(1)",
    },
    "right_margin": {
        "spec_value": "1 inch minimum",
        "authority": "MCR 2.113(C)(1)",
    },
    "font": {
        "spec_value": "12-point proportional font; Times New Roman preferred",
        "authority": "MCR 2.113(C)(1)",
    },
    "line_spacing": {
        "spec_value": "Double-spaced body text; single-spaced block quotes and footnotes",
        "authority": "MCR 2.113(C)(1)",
    },
    "page_limit_motion_brief": {
        "spec_value": "20 pages (brief in support of motion)",
        "authority": "MCR 2.119(A)(3)",
    },
    "page_limit_response_brief": {
        "spec_value": "20 pages (response brief)",
        "authority": "MCR 2.119(A)(3)",
    },
    "page_limit_reply_brief": {
        "spec_value": "10 pages (reply brief)",
        "authority": "MCR 2.119(A)(3)",
    },
    "caption_required": {
        "spec_value": "Yes — court name, case number, judge, parties, document title",
        "authority": "MCR 2.113(A)",
    },
    "signature_required": {
        "spec_value": "Yes — name, address, phone, bar number (or pro se designation)",
        "authority": "MCR 2.114(B)",
    },
    "cos_required": {
        "spec_value": "Yes — Certificate of Service on all parties per MCR 2.107(C)",
        "authority": "MCR 2.107(C)(3)",
    },
    "notice_of_hearing_required": {
        "spec_value": "Yes — for motions, unless ex parte per MCR 2.119(B)",
        "authority": "MCR 2.119(C)(1)",
    },
    "page_numbering": {
        "spec_value": "Required, consecutively numbered",
        "authority": "MCR 2.113(C)(1)",
    },
    "filing_method": {
        "spec_value": "Electronic filing via MiFILE; paper filing accepted if exempt",
        "authority": "MCR 1.109(G)(3)",
    },
    "proposed_order": {
        "spec_value": "Required with all motions unless impracticable",
        "authority": "MCR 2.119(A)(2)",
    },
}


# ── Michigan Court of Appeals ────────────────────────────────────────────────

COA_SPECS: Dict[str, Dict[str, str]] = {
    "paper_size": {
        "spec_value": "8.5 x 11 inches (letter)",
        "authority": "MCR 7.212(B)",
    },
    "top_margin": {
        "spec_value": "1 inch minimum",
        "authority": "MCR 7.212(B)",
    },
    "bottom_margin": {
        "spec_value": "1 inch minimum",
        "authority": "MCR 7.212(B)",
    },
    "left_margin": {
        "spec_value": "1 inch minimum",
        "authority": "MCR 7.212(B)",
    },
    "right_margin": {
        "spec_value": "1 inch minimum",
        "authority": "MCR 7.212(B)",
    },
    "font": {
        "spec_value": "12-point proportional font; Times New Roman preferred",
        "authority": "MCR 7.212(B)",
    },
    "line_spacing": {
        "spec_value": "Double-spaced body text; single-spaced block quotes and footnotes",
        "authority": "MCR 7.212(B)",
    },
    "page_limit_appellant_brief": {
        "spec_value": "50 pages",
        "authority": "MCR 7.212(B)",
    },
    "page_limit_appellee_brief": {
        "spec_value": "50 pages",
        "authority": "MCR 7.212(B)",
    },
    "page_limit_reply_brief": {
        "spec_value": "25 pages (or half of appellant brief length)",
        "authority": "MCR 7.212(B)",
    },
    "required_sections": {
        "spec_value": (
            "Table of Contents, Index of Authorities, "
            "Jurisdictional Statement, Statement of Questions Presented, "
            "Statement of Facts, Argument, Relief Requested"
        ),
        "authority": "MCR 7.212(C)",
    },
    "table_of_contents": {
        "spec_value": "Required — with page references for each section",
        "authority": "MCR 7.212(C)(1)",
    },
    "index_of_authorities": {
        "spec_value": "Required — alphabetical list with page references",
        "authority": "MCR 7.212(C)(2)",
    },
    "statement_of_questions": {
        "spec_value": "Required — each question separately numbered",
        "authority": "MCR 7.212(C)(4)",
    },
    "appendix": {
        "spec_value": (
            "Required — must include relevant lower court opinions, orders, "
            "and portions of the record cited in the brief"
        ),
        "authority": "MCR 7.212(E)",
    },
    "cover_color_appellant": {
        "spec_value": "Blue",
        "authority": "MCR 7.212(B)",
    },
    "cover_color_appellee": {
        "spec_value": "Red",
        "authority": "MCR 7.212(B)",
    },
    "cover_color_reply": {
        "spec_value": "Gray",
        "authority": "MCR 7.212(B)",
    },
    "filing_method": {
        "spec_value": "Electronic filing via MiFILE",
        "authority": "MCR 7.202(4); MCR 1.109(G)(3)",
    },
    "cos_required": {
        "spec_value": "Yes — Certificate of Service on all parties",
        "authority": "MCR 7.212(H)",
    },
    "signature_required": {
        "spec_value": "Yes — name, address, phone, bar number (or pro se designation)",
        "authority": "MCR 7.212(H)",
    },
    "caption_required": {
        "spec_value": (
            "Yes — Court of Appeals case number, lower court case number, "
            "parties as appellant/appellee, lower court and judge"
        ),
        "authority": "MCR 7.212(A)",
    },
}


# ── Michigan Supreme Court ───────────────────────────────────────────────────

MSC_SPECS: Dict[str, Dict[str, str]] = {
    "paper_size": {
        "spec_value": "8.5 x 11 inches (letter)",
        "authority": "MCR 7.312(A)",
    },
    "top_margin": {
        "spec_value": "1 inch minimum",
        "authority": "MCR 7.312(A)",
    },
    "bottom_margin": {
        "spec_value": "1 inch minimum",
        "authority": "MCR 7.312(A)",
    },
    "left_margin": {
        "spec_value": "1 inch minimum",
        "authority": "MCR 7.312(A)",
    },
    "right_margin": {
        "spec_value": "1 inch minimum",
        "authority": "MCR 7.312(A)",
    },
    "font": {
        "spec_value": "12-point proportional font; Times New Roman preferred",
        "authority": "MCR 7.312(A)",
    },
    "line_spacing": {
        "spec_value": "Double-spaced body text; single-spaced block quotes and footnotes",
        "authority": "MCR 7.312(A)",
    },
    "page_limit_application": {
        "spec_value": "50 pages for application for leave to appeal",
        "authority": "MCR 7.312(A)",
    },
    "page_limit_response": {
        "spec_value": "50 pages for answer in opposition",
        "authority": "MCR 7.312(A)",
    },
    "page_limit_reply": {
        "spec_value": "25 pages for reply",
        "authority": "MCR 7.312(A)",
    },
    "page_limit_amicus": {
        "spec_value": "25 pages for amicus brief",
        "authority": "MCR 7.312(H)(4)",
    },
    "required_sections_application": {
        "spec_value": (
            "Questions Presented, Table of Contents, Index of Authorities, "
            "Jurisdictional Statement, Statement of Facts, Argument, Relief Requested"
        ),
        "authority": "MCR 7.306(D)",
    },
    "superintendent_control": {
        "spec_value": (
            "Complaint for superintending control under MCR 7.306 — "
            "must demonstrate extraordinary circumstances and no adequate legal remedy"
        ),
        "authority": "MCR 7.306; Const 1963, art 6, § 4",
    },
    "emergency_application": {
        "spec_value": (
            "Emergency application under MCR 7.315(C) — must show "
            "irreparable harm and need for immediate action"
        ),
        "authority": "MCR 7.315(C)",
    },
    "cover_color": {
        "spec_value": "White",
        "authority": "MCR 7.312(A)",
    },
    "filing_method": {
        "spec_value": "Electronic filing via MiFILE",
        "authority": "MCR 1.109(G)(3)",
    },
    "cos_required": {
        "spec_value": "Yes — Certificate of Service on all parties",
        "authority": "MCR 7.312(F)",
    },
    "signature_required": {
        "spec_value": "Yes — name, address, phone, bar number (or pro se designation)",
        "authority": "MCR 7.312(F)",
    },
}


# ── WDMI Federal Court ───────────────────────────────────────────────────────

WDMI_SPECS: Dict[str, Dict[str, str]] = {
    "paper_size": {
        "spec_value": "8.5 x 11 inches (letter)",
        "authority": "LCivR 10.6(a)",
    },
    "top_margin": {
        "spec_value": "1 inch minimum",
        "authority": "LCivR 10.6(a)",
    },
    "bottom_margin": {
        "spec_value": "1 inch minimum",
        "authority": "LCivR 10.6(a)",
    },
    "left_margin": {
        "spec_value": "1 inch minimum",
        "authority": "LCivR 10.6(a)",
    },
    "right_margin": {
        "spec_value": "1 inch minimum",
        "authority": "LCivR 10.6(a)",
    },
    "font": {
        "spec_value": "14-point proportional font (12-point minimum for body); Times New Roman preferred",
        "authority": "LCivR 10.6(a)",
    },
    "line_spacing": {
        "spec_value": "Double-spaced body text; single-spaced block quotes and footnotes",
        "authority": "LCivR 10.6(a)",
    },
    "page_limit_motion_brief": {
        "spec_value": "25 pages",
        "authority": "LCivR 7.2(b)",
    },
    "page_limit_response_brief": {
        "spec_value": "25 pages",
        "authority": "LCivR 7.2(b)",
    },
    "page_limit_reply_brief": {
        "spec_value": "10 pages",
        "authority": "LCivR 7.2(b)",
    },
    "caption_required": {
        "spec_value": (
            "Yes — court name, case number, judge, parties with designations, "
            "document title"
        ),
        "authority": "FRCP 10(a); LCivR 10.6",
    },
    "signature_required": {
        "spec_value": "Yes — /s/ electronic signature, name, address, phone, bar number",
        "authority": "FRCP 11(a); LCivR 10.6(d)",
    },
    "cos_required": {
        "spec_value": "Yes — Certificate of Service via CM/ECF, or personal/mail if unregistered",
        "authority": "FRCP 5(d)(1); LCivR 5.7",
    },
    "filing_method": {
        "spec_value": "Electronic filing via CM/ECF",
        "authority": "LCivR 5.7",
    },
    "page_numbering": {
        "spec_value": "Required, consecutively numbered at bottom center",
        "authority": "LCivR 10.6(a)",
    },
}


# ── Michigan 60th District Court ─────────────────────────────────────────────

DISTRICT_COURT_SPECS: Dict[str, Dict[str, str]] = {
    "paper_size": {
        "spec_value": "8.5 x 11 inches (letter)",
        "authority": "MCR 2.113(C)(1)",
    },
    "top_margin": {
        "spec_value": "1 inch minimum (2.5 inches on first page for court stamp)",
        "authority": "MCR 2.113(C)(1)",
    },
    "bottom_margin": {
        "spec_value": "1 inch minimum",
        "authority": "MCR 2.113(C)(1)",
    },
    "left_margin": {
        "spec_value": "1 inch minimum",
        "authority": "MCR 2.113(C)(1)",
    },
    "right_margin": {
        "spec_value": "1 inch minimum",
        "authority": "MCR 2.113(C)(1)",
    },
    "font": {
        "spec_value": "12-point proportional font; Times New Roman preferred",
        "authority": "MCR 2.113(C)(1)",
    },
    "line_spacing": {
        "spec_value": "Double-spaced body text; single-spaced block quotes and footnotes",
        "authority": "MCR 2.113(C)(1)",
    },
    "page_limit_motion_brief": {
        "spec_value": "20 pages (brief in support of motion)",
        "authority": "MCR 2.119(A)(3)",
    },
    "caption_required": {
        "spec_value": "Yes — court name, case number, judge, parties, document title",
        "authority": "MCR 2.113(A)",
    },
    "signature_required": {
        "spec_value": "Yes — name, address, phone, bar number (or pro se designation)",
        "authority": "MCR 2.114(B)",
    },
    "cos_required": {
        "spec_value": "Yes — Certificate of Service on all parties",
        "authority": "MCR 2.107(C)(3)",
    },
    "filing_method": {
        "spec_value": "Electronic filing via MiFILE; paper filing accepted if exempt",
        "authority": "MCR 1.109(G)(3)",
    },
}


# ── Aggregate access ─────────────────────────────────────────────────────────

ALL_SPECS: Dict[str, Dict[str, Dict[str, str]]] = {
    "circuit": CIRCUIT_COURT_SPECS,
    "coa": COA_SPECS,
    "msc": MSC_SPECS,
    "wdmi": WDMI_SPECS,
    "district": DISTRICT_COURT_SPECS,
}


def get_specs(court: str) -> Dict[str, Dict[str, str]]:
    """Return format specs for the given court identifier.

    Args:
        court: One of ``circuit``, ``coa``, ``msc``, ``wdmi``, ``district``.

    Returns:
        Dict mapping spec names to ``{spec_value, authority}`` dicts.

    Raises:
        ValueError: If *court* is not a recognized identifier.
    """
    court_key = court.lower().strip()
    if court_key not in ALL_SPECS:
        raise ValueError(
            f"Unknown court '{court}'. Choose from: {', '.join(ALL_SPECS)}"
        )
    return ALL_SPECS[court_key]


def get_all_specs() -> Dict[str, Dict[str, Dict[str, str]]]:
    """Return the complete specs dictionary keyed by court."""
    return ALL_SPECS


def specs_as_flat_rows() -> List[Dict[str, str]]:
    """Return specs as a flat list of row dicts suitable for DB insertion.

    Each dict has keys: ``court``, ``spec_name``, ``spec_value``, ``authority``.
    """
    rows: List[Dict[str, str]] = []
    for court_key, specs in ALL_SPECS.items():
        for spec_name, spec_data in specs.items():
            rows.append({
                "court": court_key,
                "spec_name": spec_name,
                "spec_value": spec_data["spec_value"],
                "authority": spec_data.get("authority", ""),
            })
    return rows


if __name__ == "__main__":
    import json
    import sys

    court_arg = sys.argv[1] if len(sys.argv) > 1 else None

    if court_arg:
        specs = get_specs(court_arg)
        print(f"=== {court_arg.upper()} Format Specs ===")
        print(json.dumps(specs, indent=2))
    else:
        print("Available courts:", ", ".join(ALL_SPECS))
        for court_name, specs in ALL_SPECS.items():
            print(f"\n=== {court_name.upper()} ({len(specs)} specs) ===")
            for name, data in specs.items():
                print(f"  {name}: {data['spec_value'][:70]}...")
