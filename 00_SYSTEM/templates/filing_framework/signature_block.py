"""
Signature Block Generator
==========================

Generates properly formatted signature blocks for Michigan court filings,
supporting both pro se litigants and attorney signatures.

Usage::

    from signature_block import generate_signature

    party = {
        "name": "John Smith",
        "address": "123 Main St",
        "city": "Anytown",
        "state": "MI",
        "zip": "49000",
        "phone": "(231) 555-1234",
        "email": "john@example.com",
    }
    sig = generate_signature(party, pro_se=True)
    print(sig)
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional


def generate_signature(
    party_info: Dict[str, Any],
    pro_se: bool = True,
    *,
    party_role: str = "Plaintiff",
    electronic: bool = False,
    filing_date: Optional[date] = None,
) -> str:
    """Generate a formatted signature block.

    Args:
        party_info: Dict with keys:

            - ``name`` (str): Full legal name.
            - ``address`` (str, optional): Street address.
            - ``city`` (str, optional): City.
            - ``state`` (str, optional): State (default ``MI``).
            - ``zip`` (str, optional): ZIP code.
            - ``phone`` (str, optional): Telephone number.
            - ``email`` (str, optional): Email address.
            - ``bar_number`` (str, optional): Bar number (attorneys only).
            - ``firm`` (str, optional): Law firm name (attorneys only).

        pro_se: If True, generates a pro se signature block.
            If False, generates an attorney signature block.
        party_role: Designation for the signing party. Common values:
            ``Plaintiff``, ``Defendant``, ``Appellant``, ``Appellee``.
            When *pro_se* is True, appends ", appearing pro se" for
            ``Plaintiff`` and ``Defendant`` roles.
        electronic: If True, uses ``/s/`` electronic signature format
            (required for federal CM/ECF filings).
        filing_date: Date for the signature line; defaults to today.

    Returns:
        Formatted signature block as a plain-text string.
    """
    if filing_date is None:
        filing_date = date.today()

    name = party_info.get("name", "")
    address = party_info.get("address", "")
    city = party_info.get("city", "")
    state = party_info.get("state", "MI")
    zip_code = party_info.get("zip", "")
    phone = party_info.get("phone", "")
    email = party_info.get("email", "")
    bar_number = party_info.get("bar_number", "")
    firm = party_info.get("firm", "")

    # Build address line
    city_state_zip = ""
    if city:
        city_state_zip = city
        if state:
            city_state_zip += f", {state}"
        if zip_code:
            city_state_zip += f" {zip_code}"

    lines = [
        f"Respectfully submitted,",
        "",
        f"Date: {filing_date.strftime('%B %d, %Y')}",
        "",
    ]

    # Signature line
    if electronic:
        lines.append(f"/s/ {name}")
    else:
        lines.append("_________________________________")
        lines.append(f"{name}")

    # Designation
    if pro_se:
        role = party_role.strip() if party_role else "Plaintiff"
        role_lower = role.lower()
        if role_lower in ("plaintiff", "defendant"):
            lines.append(f"{role}, appearing pro se")
        elif role_lower in ("appellant", "appellee",
                            "petitioner", "respondent"):
            lines.append(role)
        else:
            lines.append(role)
    else:
        if firm:
            lines.append(f"{firm}")
        if bar_number:
            lines.append(f"{bar_number}")

    # Contact info
    if address:
        lines.append(f"{address}")
    if city_state_zip:
        lines.append(f"{city_state_zip}")
    if phone:
        lines.append(f"Phone: {phone}")
    if email:
        lines.append(f"Email: {email}")

    return "\n".join(lines)


def generate_attorney_signature(
    attorney_info: Dict[str, Any],
    client_name: str,
    *,
    electronic: bool = False,
    filing_date: Optional[date] = None,
) -> str:
    """Generate an attorney signature block with client reference.

    This is a convenience wrapper around :func:`generate_signature`
    for attorneys representing clients.

    Args:
        attorney_info: Attorney details (same keys as *party_info*
            in :func:`generate_signature`).
        client_name: Name of the client being represented.
        electronic: If True, uses ``/s/`` format.
        filing_date: Date for the signature; defaults to today.

    Returns:
        Formatted attorney signature block.
    """
    if filing_date is None:
        filing_date = date.today()

    sig = generate_signature(
        attorney_info,
        pro_se=False,
        electronic=electronic,
        filing_date=filing_date,
    )
    sig += f"\nAttorney for {client_name}"
    return sig


if __name__ == "__main__":
    sample_pro_se = {
        "name": "John Smith",
        "address": "123 Main St, Lot 17",
        "city": "North Muskegon",
        "state": "MI",
        "zip": "49445",
        "phone": "(231) 555-1234",
        "email": "john@example.com",
    }

    sample_attorney = {
        "name": "Jane Attorney",
        "bar_number": "P12345",
        "firm": "Smith & Associates PLLC",
        "address": "456 Legal Ave",
        "city": "Grand Rapids",
        "state": "MI",
        "zip": "49503",
        "phone": "(616) 555-9876",
        "email": "jane@smithlaw.com",
    }

    print("=== PRO SE SIGNATURE ===")
    print(generate_signature(sample_pro_se, pro_se=True))
    print()
    print("=== PRO SE (ELECTRONIC) ===")
    print(generate_signature(sample_pro_se, pro_se=True, electronic=True))
    print()
    print("=== ATTORNEY SIGNATURE ===")
    print(generate_attorney_signature(sample_attorney, "John Smith"))
    print()
    print("=== ATTORNEY (ELECTRONIC) ===")
    print(generate_attorney_signature(sample_attorney, "John Smith", electronic=True))
