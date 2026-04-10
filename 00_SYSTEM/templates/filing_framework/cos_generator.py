"""
Certificate of Service Generator
==================================

Generates a properly formatted Certificate of Service for any Michigan
court filing, as well as federal (CM/ECF) filings.

Supports service methods: ``electronic``, ``personal``, ``mail``, ``ECF``,
``facsimile``, and ``hand_delivery``.

Usage::

    from cos_generator import generate_cos
    from datetime import date

    parties = [
        {"name": "Jane Smith", "address": "123 Main St, Anytown, MI 49000",
         "via": "Attorney: John Doe (P12345)"},
        {"name": "Friend of the Court", "address": "990 Terrace St, Muskegon, MI 49442"},
    ]
    cos = generate_cos(parties, "electronic", date.today(), case_info)
    print(cos)
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional


def generate_cos(
    parties_served: List[Dict[str, str]],
    method: str = "electronic",
    service_date: Optional[date] = None,
    case_info: Optional[Dict[str, Any]] = None,
    *,
    filer_name: Optional[str] = None,
) -> str:
    """Generate a Certificate of Service.

    Args:
        parties_served: List of dicts, each with:

            - ``name`` (str): Name of the party served.
            - ``address`` (str, optional): Address for service.
            - ``via`` (str, optional): Attorney or agent (e.g., "Attorney: J. Doe P12345").
            - ``email`` (str, optional): Email if electronic service.
            - ``fax`` (str, optional): Fax number if facsimile service.

        method: Service method — ``electronic``, ``personal``, ``mail``,
            ``ECF``, ``facsimile``, or ``hand_delivery``.
        service_date: Date of service; defaults to today.
        case_info: Optional case dict for context (used for filer name).
        filer_name: Override for the certifying party's name.

    Returns:
        Formatted Certificate of Service as a plain-text string.
    """
    if service_date is None:
        service_date = date.today()

    # Determine filer name
    if filer_name is None and case_info:
        filer_name = case_info.get("plaintiff", case_info.get("filer", ""))

    method_lower = method.lower().strip()
    method_text = _method_description(method_lower)
    date_str = service_date.strftime("%B %d, %Y")

    lines: List[str] = [
        "CERTIFICATE OF SERVICE",
        "",
        f"I hereby certify that on {date_str}, I served a copy of the foregoing",
        f"document upon the following parties by {method_text}:",
        "",
    ]

    for party in parties_served:
        name = party.get("name", "Unknown Party")
        address = party.get("address", "")
        via = party.get("via", "")
        email = party.get("email", "")
        fax = party.get("fax", "")

        lines.append(f"    {name}")
        if via:
            lines.append(f"    c/o {via}")
        if address:
            lines.append(f"    {address}")
        if email and method_lower in ("electronic", "ecf"):
            lines.append(f"    {email}")
        if fax and method_lower == "facsimile":
            lines.append(f"    Fax: {fax}")
        lines.append("")

    # Rule citation
    if method_lower == "ecf":
        lines.append(
            "Service was accomplished through the Court's CM/ECF electronic "
            "filing system, which will send notification of electronic filing "
            "to all registered counsel of record."
        )
        lines.append("")
        lines.append("FRCP 5(b)(2)(E); LCivR 5.7")
    elif method_lower == "electronic":
        lines.append(
            "Service was accomplished by electronic filing through the "
            "MiFILE e-filing system, which will send notification to all "
            "registered parties."
        )
        lines.append("")
        lines.append("MCR 2.107(C)(4)")
    elif method_lower == "mail":
        lines.append(
            "Service was accomplished by placing a copy in a sealed envelope "
            "with first-class postage prepaid, addressed as indicated above, "
            "and depositing the same in the United States mail."
        )
        lines.append("")
        lines.append("MCR 2.107(C)(3)")
    elif method_lower == "personal":
        lines.append(
            "Service was accomplished by personally delivering a copy to "
            "the above-named parties at the addresses indicated."
        )
        lines.append("")
        lines.append("MCR 2.107(C)(1)")
    elif method_lower == "facsimile":
        lines.append(
            "Service was accomplished by facsimile transmission to the "
            "above-named parties at the facsimile numbers indicated."
        )
        lines.append("")
        lines.append("MCR 2.107(C)(3)")
    elif method_lower == "hand_delivery":
        lines.append(
            "Service was accomplished by hand delivery to the "
            "above-named parties at the addresses indicated."
        )
        lines.append("")
        lines.append("MCR 2.107(C)(1)")

    # Signature
    lines.append("")
    lines.append(f"Date: {date_str}")
    lines.append("")
    lines.append("_________________________________")
    if filer_name:
        lines.append(f"{filer_name}")
        if case_info and case_info.get("pro_se", False):
            lines.append("Plaintiff, appearing pro se")

    return "\n".join(lines)


def _method_description(method: str) -> str:
    """Return a human-readable description of the service method."""
    descriptions = {
        "electronic": "electronic filing (MiFILE)",
        "personal": "personal service",
        "mail": "first-class United States mail, postage prepaid",
        "ecf": "the Court's CM/ECF electronic filing system",
        "facsimile": "facsimile transmission",
        "hand_delivery": "hand delivery",
    }
    return descriptions.get(method, method)


if __name__ == "__main__":
    sample_parties = [
        {
            "name": "Jane Smith",
            "address": "123 Main St, Anytown, MI 49000",
            "via": "Attorney: John Doe (P12345)",
        },
        {
            "name": "Friend of the Court",
            "address": "990 Terrace St, Muskegon, MI 49442",
        },
    ]
    sample_case = {
        "plaintiff": "John Smith",
        "pro_se": True,
    }
    print(generate_cos(sample_parties, "electronic", date.today(), sample_case))
