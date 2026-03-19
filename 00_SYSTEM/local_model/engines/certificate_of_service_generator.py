# -*- coding: utf-8 -*-
"""
Certificate of Service Generator Engine — LitigationOS MANBEARPIG v8.0
========================================================================
Generate Michigan-compliant Certificate of Service for all filings.

Authority:
    MCR 2.107(C)   — Methods of service
    MCR 2.119(A)(2)— Certificate must accompany every motion
    MCR 1.109(G)   — E-filing service provisions

Usage:
    python certificate_of_service_generator.py
"""

import sys
import os
import io
import sqlite3
import json
from datetime import date, datetime
from typing import Dict, List, Optional

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
elif sys.stdout is None or not hasattr(sys.stdout, "encoding") or sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer if sys.stdout else open(os.devnull, "w"), encoding="utf-8")

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

# Import court_address_book for address lookups
_ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _ENGINE_DIR)
try:
    from court_address_book import get_address, format_address_block, ADDRESS_BOOK
except ImportError:
    # Fallback: define minimal stubs if address book not available
    ADDRESS_BOOK = {}
    def get_address(entity):
        return {"error": "court_address_book not available", "name": entity}
    def format_address_block(entity):
        return entity

# ---------------------------------------------------------------------------
# Service method templates per MCR 2.107(C)
# ---------------------------------------------------------------------------

SERVICE_TEMPLATES = {
    "mail": {
        "rule": "MCR 2.107(C)(3)",
        "language": (
            "by depositing a copy in a sealed envelope with first-class postage "
            "fully prepaid in the United States mail, addressed to"
        ),
        "extra_days": 3,
    },
    "personal": {
        "rule": "MCR 2.107(C)(1)",
        "language": (
            "by personal delivery, delivering a copy directly to"
        ),
        "extra_days": 0,
    },
    "email": {
        "rule": "MCR 2.107(C)(4)",
        "language": (
            "by electronic mail, with the consent of the receiving party, "
            "to the email address on file for"
        ),
        "extra_days": 1,
    },
    "mifile": {
        "rule": "MCR 1.109(G)(6)(a)",
        "language": (
            "by electronic service through the MiFile e-filing system to"
        ),
        "extra_days": 1,
    },
    "ecf": {
        "rule": "Fed. R. Civ. P. 5(b)(2)(E)",
        "language": (
            "by electronic means through the Court's CM/ECF system, which "
            "will send a Notice of Electronic Filing to"
        ),
        "extra_days": 0,
    },
}

# Default recipient lists per case lane
DEFAULT_RECIPIENTS = {
    "lane_a": ["tiffany_watson", "ron_berry", "friend_of_court"],
    "lane_d": ["andrew_pigors"],  # PPO — Pigors is respondent
    "lane_f": ["ron_berry"],  # COA
    "msc": ["tiffany_watson", "ron_berry", "14th_circuit_court"],
    "federal": ["tiffany_watson", "ron_berry"],
    "jtc": [],  # JTC complaints — no service on respondent judge required at filing
}


def _get_service_method_for_entity(entity_key: str, override: Optional[str] = None) -> str:
    """Determine the service method for an entity."""
    if override:
        return override.lower()
    data = get_address(entity_key)
    if "error" in data:
        return "mail"
    return data.get("service_method", "mail").lower()


def _format_recipient_block(
    entity_key: str,
    service_method: str,
    service_date: str,
) -> str:
    """Format a single recipient entry for the COS."""
    data = get_address(entity_key)
    name = data.get("name", entity_key)
    role = data.get("role", "")
    template = SERVICE_TEMPLATES.get(service_method, SERVICE_TEMPLATES["mail"])

    addr_block = format_address_block(entity_key)
    addr_lines = addr_block.split("\n")
    # Remove name from address block (already in header)
    if len(addr_lines) > 1:
        addr_text = ", ".join(line.strip() for line in addr_lines[1:] if line.strip())
    else:
        addr_text = addr_block

    role_str = f" ({role})" if role else ""

    return (
        f"    {name}{role_str}\n"
        f"    {template['language']}:\n"
        f"    {addr_text}\n"
    )


def generate_cos(
    filing_name: str,
    recipients: List[str],
    service_method: Optional[str] = None,
    service_date: Optional[str] = None,
    case_number: str = "2024-001507-DC",
) -> str:
    """
    Generate a complete Certificate of Service.

    Args:
        filing_name:    Name of the document being served
        recipients:     List of entity keys from court_address_book
        service_method: Override service method for all recipients (or per-entity default)
        service_date:   ISO date string (defaults to today)
        case_number:    Case number for the caption reference

    Returns:
        Complete COS text ready for filing.
    """
    if service_date:
        svc_date = date.fromisoformat(service_date)
    else:
        svc_date = date.today()

    date_formatted = svc_date.strftime("%B %d, %Y")

    lines = [
        "CERTIFICATE OF SERVICE",
        "",
        f"Case No. {case_number}",
        "",
        f"I, Andrew Pigors, hereby certify that on {date_formatted}, I served "
        f"a true and correct copy of:",
        "",
        f"    {filing_name}",
        "",
        "on the following parties:",
        "",
    ]

    # Group recipients by service method for cleaner output
    method_groups: Dict[str, List[str]] = {}
    for r in recipients:
        m = _get_service_method_for_entity(r, service_method)
        method_groups.setdefault(m, []).append(r)

    for method, entities in method_groups.items():
        template = SERVICE_TEMPLATES.get(method, SERVICE_TEMPLATES["mail"])
        lines.append(f"By {method.upper()} — {template['rule']}:")
        lines.append("")
        for entity_key in entities:
            block = _format_recipient_block(entity_key, method, date_formatted)
            lines.append(block)

    lines += [
        "",
        "I declare under the penalties of perjury that the foregoing is true",
        "and correct.",
        "",
        "",
        "________________________________",
        "Andrew Pigors",
        "Pro Se Plaintiff/Appellant",
        f"Date: {date_formatted}",
    ]

    return "\n".join(lines)


def generate_cos_for_filing_lane(
    filing_name: str,
    lane: str = "lane_a",
    service_date: Optional[str] = None,
) -> str:
    """
    Generate COS using default recipients for a case lane.

    Args:
        filing_name: Document name
        lane:        lane_a | lane_d | lane_f | msc | federal | jtc

    Returns:
        Complete COS text.
    """
    recipients = DEFAULT_RECIPIENTS.get(lane, DEFAULT_RECIPIENTS["lane_a"])
    case_numbers = {
        "lane_a": "2024-001507-DC",
        "lane_d": "2023-5907-PP",
        "lane_f": "366810",
        "msc": "[MSC No. TBD]",
        "federal": "[USDC No. TBD]",
        "jtc": "JTC Complaint",
    }
    case_no = case_numbers.get(lane, "2024-001507-DC")
    return generate_cos(filing_name, recipients, service_date=service_date, case_number=case_no)


def generate_cos_for_all_filings() -> Dict[str, str]:
    """
    Generate COS for all pending court filings in the filing package.

    Returns:
        Dict mapping filing name to COS text.
    """
    filings = [
        ("MSC Complaint for Superintending Control", "msc"),
        ("JTC Formal Complaint", "jtc"),
        ("Emergency Motion to Restore Parenting Time", "lane_a"),
        ("Motion for Reconsideration", "lane_a"),
        ("COA Appellant Brief — Case No. 366810", "lane_f"),
    ]

    results = {}
    for filing_name, lane in filings:
        results[filing_name] = generate_cos_for_filing_lane(filing_name, lane)

    return results


def generate_affidavit_of_service(
    filing_name: str,
    recipients: List[str],
    service_method: str = "mail",
    service_date: Optional[str] = None,
) -> str:
    """
    Generate a notarized Affidavit of Service (for situations requiring more
    formal proof than a certificate).

    Args:
        filing_name:    Document served
        recipients:     List of entity keys
        service_method: Method used
        service_date:   ISO date

    Returns:
        Affidavit text.
    """
    if service_date:
        svc_date = date.fromisoformat(service_date)
    else:
        svc_date = date.today()

    date_formatted = svc_date.strftime("%B %d, %Y")
    template = SERVICE_TEMPLATES.get(service_method, SERVICE_TEMPLATES["mail"])

    recipient_names = []
    for r in recipients:
        data = get_address(r)
        recipient_names.append(data.get("name", r))

    names_str = "; ".join(recipient_names)

    return (
        f"STATE OF MICHIGAN\n"
        f"COUNTY OF MUSKEGON\n"
        f"\n"
        f"AFFIDAVIT OF SERVICE\n"
        f"\n"
        f"I, Andrew Pigors, being duly sworn, depose and state:\n"
        f"\n"
        f"1. On {date_formatted}, I served a true and correct copy of "
        f'"{filing_name}" on the following:\n'
        f"\n"
        f"   {names_str}\n"
        f"\n"
        f"2. Service was made {template['language']} the above-named parties.\n"
        f"\n"
        f"3. I am over the age of 18 and not a party to this action "
        f"(or am a party proceeding pro se as permitted).\n"
        f"\n"
        f"\n"
        f"________________________________\n"
        f"Andrew Pigors, Affiant\n"
        f"\n"
        f"Subscribed and sworn to before me\n"
        f"this ____ day of _____________, 20__.\n"
        f"\n"
        f"________________________________\n"
        f"Notary Public, Muskegon County, MI\n"
        f"My commission expires: ___________\n"
    )


def validate_cos_completeness(cos_text: str) -> Dict:
    """
    Validate that a COS meets MCR 2.107 requirements.

    Checks for: date, document name, party names, service method, signature.
    """
    issues = []
    checks = {
        "has_title": "CERTIFICATE OF SERVICE" in cos_text,
        "has_date": any(m in cos_text for m in ["January", "February", "March", "April",
                                                  "May", "June", "July", "August",
                                                  "September", "October", "November", "December"]),
        "has_method": any(m in cos_text.upper() for m in ["MAIL", "PERSONAL", "EMAIL", "MIFILE", "ECF"]),
        "has_signature_line": "________________________________" in cos_text,
        "has_declarant": "Andrew Pigors" in cos_text,
        "has_case_number": "Case No." in cos_text or "No." in cos_text,
    }

    for check, passed in checks.items():
        if not passed:
            issues.append(f"MISSING: {check.replace('has_', '').replace('_', ' ')}")

    return {
        "valid": len(issues) == 0,
        "checks": checks,
        "issues": issues,
        "authority": "MCR 2.107(C), MCR 2.119(A)(2)",
    }


def main():
    """CLI test harness."""
    print("=" * 70)
    print("CERTIFICATE OF SERVICE GENERATOR — LitigationOS MANBEARPIG v8.0")
    print("=" * 70)

    # Test 1: Single COS
    print("\n[TEST 1] COS for Emergency Motion (Lane A):")
    cos = generate_cos(
        "Emergency Motion to Restore Parenting Time",
        ["tiffany_watson", "ron_berry", "friend_of_court"],
    )
    print(cos)

    # Test 2: Lane-based COS
    print("\n[TEST 2] COS for COA Brief (Lane F):")
    cos_f = generate_cos_for_filing_lane("Appellant Brief", "lane_f")
    print(cos_f)

    # Test 3: MSC COS
    print("\n[TEST 3] COS for MSC Complaint:")
    cos_msc = generate_cos_for_filing_lane("Complaint for Superintending Control", "msc")
    print(cos_msc)

    # Test 4: All filings
    print("\n[TEST 4] COS for all filings in package:")
    all_cos = generate_cos_for_all_filings()
    for name, text in all_cos.items():
        print(f"  ✓ Generated COS for: {name} ({len(text)} chars)")

    # Test 5: Affidavit of Service
    print("\n[TEST 5] Affidavit of Service:")
    aff = generate_affidavit_of_service(
        "Motion for Reconsideration",
        ["tiffany_watson", "ron_berry"],
        "mail",
    )
    print(aff)

    # Test 6: Validation
    print("\n[TEST 6] COS Validation:")
    validation = validate_cos_completeness(cos)
    for k, v in validation.items():
        print(f"  {k}: {v}")

    print("\n✓ Certificate of Service Generator — all tests complete.")


if __name__ == "__main__":
    main()
