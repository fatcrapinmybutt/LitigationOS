"""
Court Caption / Header Generator
==================================

Generates properly formatted captions for Michigan state courts and
Western District of Michigan federal court.

Supported court types: ``circuit``, ``coa``, ``msc``, ``wdmi``, ``district``.

Usage::

    from caption_generator import generate_caption

    case = {
        "case_number": "2024-001234-DC",
        "court": "14th Judicial Circuit Court",
        "county": "Muskegon",
        "judge": "Hon. Jane Doe",
        "plaintiff": "John Smith",
        "defendant": "Jane Smith",
        "division": "Family",
    }
    caption = generate_caption(case, "Motion to Compel Discovery", "circuit")
    print(caption)
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional


def generate_caption(
    case_info: Dict[str, Any],
    document_title: str,
    court_type: str = "circuit",
    *,
    filing_date: Optional[date] = None,
) -> str:
    """Generate a court caption/header for the specified court.

    Args:
        case_info: Dict with keys:

            - ``case_number`` (str): Case number.
            - ``court`` (str): Full court name.
            - ``county`` (str, optional): County name.
            - ``judge`` (str, optional): Assigned judge.
            - ``plaintiff`` (str): Plaintiff's name.
            - ``defendant`` (str): Defendant's name.
            - ``division`` (str, optional): Division (Family, Civil, etc.).
            - ``pro_se`` (bool, optional): Whether plaintiff is pro se.
            - ``coa_case_number`` (str, optional): COA/MSC docket number.
            - ``lower_court_case_number`` (str, optional): Lower court number.
            - ``lower_court`` (str, optional): Lower court name.
            - ``lower_court_judge`` (str, optional): Lower court judge.
            - ``appellant`` (str, optional): Appellant name (appellate).
            - ``appellee`` (str, optional): Appellee name (appellate).

        document_title: Title of the document (e.g., "Motion to Compel").
        court_type: One of ``circuit``, ``coa``, ``msc``, ``wdmi``, ``district``.
        filing_date: Date for the caption; defaults to today.

    Returns:
        Formatted caption as a plain-text string.

    Raises:
        ValueError: If *court_type* is not recognized.
    """
    court_type = court_type.lower().strip()
    if filing_date is None:
        filing_date = date.today()

    generators = {
        "circuit": _circuit_caption,
        "district": _circuit_caption,  # same format, different court name
        "coa": _coa_caption,
        "msc": _msc_caption,
        "wdmi": _wdmi_caption,
    }

    if court_type not in generators:
        raise ValueError(
            f"Unknown court type '{court_type}'. "
            f"Choose from: {', '.join(generators)}"
        )

    return generators[court_type](case_info, document_title, filing_date)


# ── Michigan Circuit / District Court ────────────────────────────────────────

def _circuit_caption(
    info: Dict[str, Any],
    title: str,
    filing_date: date,
) -> str:
    """MCR 2.113(A) caption for Circuit and District courts."""
    court_name = info.get("court", "Circuit Court")
    county = info.get("county", "")
    case_number = info.get("case_number", "")
    judge = info.get("judge", "")
    division = info.get("division", "")
    plaintiff = info.get("plaintiff", "")
    defendant = info.get("defendant", "")
    pro_se = info.get("pro_se", False)

    divider = "-" * 40

    lines = [
        f"STATE OF MICHIGAN",
        f"IN THE {court_name.upper()}",
    ]
    if county:
        lines.append(f"COUNTY OF {county.upper()}")
    if division:
        lines.append(f"{division.upper()} DIVISION")
    lines.append("")

    # Parties block
    plaintiff_line = plaintiff
    if pro_se:
        plaintiff_line += ","
    lines.append(f"{plaintiff_line}")
    lines.append(f"    Plaintiff,")
    if pro_se:
        lines.append(f"    appearing pro se,")
    lines.append(f"")
    lines.append(f"        v.                                  Case No. {case_number}")
    if judge:
        lines.append(f"                                            {judge}")
    lines.append(f"")
    lines.append(f"{defendant},")
    lines.append(f"    Defendant.")
    lines.append(f"{divider}")

    # Document title
    lines.append("")
    lines.append(f"{title.upper()}")
    lines.append("")

    return "\n".join(lines)


# ── Michigan Court of Appeals ────────────────────────────────────────────────

def _coa_caption(
    info: Dict[str, Any],
    title: str,
    filing_date: date,
) -> str:
    """MCR 7.212(A) caption for Court of Appeals."""
    coa_number = info.get("coa_case_number", info.get("case_number", ""))
    lc_number = info.get("lower_court_case_number", "")
    lc_court = info.get("lower_court", "")
    lc_judge = info.get("lower_court_judge", "")
    appellant = info.get("appellant", info.get("plaintiff", ""))
    appellee = info.get("appellee", info.get("defendant", ""))
    pro_se = info.get("pro_se", False)

    lines = [
        "STATE OF MICHIGAN",
        "IN THE COURT OF APPEALS",
        "",
    ]

    # Parties
    appellant_line = appellant
    if pro_se:
        appellant_line += ","
    lines.append(f"{appellant_line}")
    lines.append(f"    Appellant,")
    if pro_se:
        lines.append(f"    appearing pro se,")
    lines.append(f"")
    lines.append(f"        v.                                  Court of Appeals No. {coa_number}")
    lines.append(f"")
    lines.append(f"{appellee},")
    lines.append(f"    Appellee.")
    lines.append("-" * 40)

    # Lower court info
    if lc_court or lc_number:
        lines.append(f"")
        if lc_court:
            lines.append(f"Lower Court: {lc_court}")
        if lc_number:
            lines.append(f"LC Case No.: {lc_number}")
        if lc_judge:
            lines.append(f"LC Judge:    {lc_judge}")

    lines.append(f"")
    lines.append(f"{title.upper()}")
    lines.append(f"")

    return "\n".join(lines)


# ── Michigan Supreme Court ───────────────────────────────────────────────────

def _msc_caption(
    info: Dict[str, Any],
    title: str,
    filing_date: date,
) -> str:
    """MCR 7.306/7.312 caption for Michigan Supreme Court."""
    msc_number = info.get("msc_case_number", info.get("case_number", ""))
    coa_number = info.get("coa_case_number", "")
    lc_number = info.get("lower_court_case_number", "")
    lc_court = info.get("lower_court", "")
    lc_judge = info.get("lower_court_judge", "")
    appellant = info.get("appellant", info.get("plaintiff", ""))
    appellee = info.get("appellee", info.get("defendant", ""))
    pro_se = info.get("pro_se", False)

    lines = [
        "STATE OF MICHIGAN",
        "IN THE SUPREME COURT",
        "",
    ]

    appellant_line = appellant
    if pro_se:
        appellant_line += ","
    lines.append(f"{appellant_line}")
    lines.append(f"    Appellant,")
    if pro_se:
        lines.append(f"    appearing pro se,")
    lines.append(f"")
    lines.append(f"        v.                                  Supreme Court No. {msc_number}")
    if coa_number:
        lines.append(f"                                            COA No. {coa_number}")
    lines.append(f"")
    lines.append(f"{appellee},")
    lines.append(f"    Appellee.")
    lines.append("-" * 40)

    if lc_court or lc_number:
        lines.append(f"")
        if lc_court:
            lines.append(f"Lower Court:     {lc_court}")
        if lc_number:
            lines.append(f"LC Case No.:     {lc_number}")
        if lc_judge:
            lines.append(f"LC Judge:        {lc_judge}")
        if coa_number:
            lines.append(f"COA Case No.:    {coa_number}")

    lines.append(f"")
    lines.append(f"{title.upper()}")
    lines.append(f"")

    return "\n".join(lines)


# ── WDMI Federal Court ───────────────────────────────────────────────────────

def _wdmi_caption(
    info: Dict[str, Any],
    title: str,
    filing_date: date,
) -> str:
    """FRCP 10(a) / LCivR 10.6 caption for WDMI Federal Court."""
    case_number = info.get("case_number", "")
    judge = info.get("judge", "")
    plaintiff = info.get("plaintiff", "")
    defendant = info.get("defendant", "")
    pro_se = info.get("pro_se", False)

    lines = [
        "UNITED STATES DISTRICT COURT",
        "WESTERN DISTRICT OF MICHIGAN",
        "SOUTHERN DIVISION",
        "",
    ]

    plaintiff_line = plaintiff
    if pro_se:
        plaintiff_line += ","
    lines.append(f"{plaintiff_line}")
    lines.append(f"    Plaintiff,")
    if pro_se:
        lines.append(f"    appearing pro se,")
    lines.append(f"")
    lines.append(f"        v.                                  Case No. {case_number}")
    if judge:
        lines.append(f"                                            {judge}")
    lines.append(f"")
    lines.append(f"{defendant},")
    lines.append(f"    Defendant.")
    lines.append("-" * 40)
    lines.append(f"")
    lines.append(f"{title.upper()}")
    lines.append(f"")

    return "\n".join(lines)


if __name__ == "__main__":
    # Demo with sample data
    sample = {
        "case_number": "2024-001234-DC",
        "court": "14th Judicial Circuit Court",
        "county": "Muskegon",
        "judge": "Hon. Jane Doe",
        "plaintiff": "John Smith",
        "defendant": "Jane Smith",
        "division": "Family",
        "pro_se": True,
    }

    for ct in ("circuit", "coa", "msc", "wdmi"):
        print(f"{'=' * 60}")
        print(f"  {ct.upper()} CAPTION")
        print(f"{'=' * 60}")
        print(generate_caption(sample, "Motion to Compel Discovery", ct))
        print()
