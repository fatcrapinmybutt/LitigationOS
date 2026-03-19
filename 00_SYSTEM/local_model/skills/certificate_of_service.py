#!/usr/bin/env python3
"""
MBP LitigationOS -- Certificate of Service Generator Skill
============================================================
Generate MCR 2.107-compliant Certificates of Service for any Michigan
court level, including circuit court, COA, MSC, and federal filings.

Case: Andrew Pigors v. Tiffany Watson
Lane A: 2024-001507-DC (14th Circuit, Muskegon County)
Lane F: COA 366810
Lane G: MSC Original Action

MCR 2.107 requirements:
  - Method of service
  - Date of service
  - Name and address of each person served
  - Signature of the person who served or caused service

For appellate filings (MCR 7.212(A)(3)):
  - Service on the Clerk of the lower court
  - Service on all parties who appeared below
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parent.parent
        if "skills" in str(Path(__file__))
        else Path(__file__).resolve().parent
    ),
)
try:
    from cycle_method import cycle_json, cycle_print
except ImportError:
    cycle_json = lambda obj, **kw: print(json.dumps(obj, default=str))
    cycle_print = print

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)

# ── Service method descriptors per MCR 2.107 ────────────────────────────────

SERVICE_METHOD_TEXT: Dict[str, str] = {
    "personal": "personal delivery",
    "mail": "first-class United States mail, postage prepaid",
    "efiling": "electronic filing and service via MiFILE",
    "email": "electronic mail with prior written consent of the recipient",
    "certified_mail": "certified mail, return receipt requested",
}

# MCR 2.107(C)(3): Mail service adds 3 days to response deadlines
MAIL_METHODS_ADDING_DAYS = {"mail", "certified_mail"}
MAIL_EXTRA_DAYS = 3

# ── Default parties for Pigors v Watson ──────────────────────────────────────

DEFAULT_PARTIES: List[Dict[str, Any]] = [
    {
        "name": "Emily Watson",
        "role": "Defendant/Appellee",
        "address": "[ADDRESS NEEDED]",
        "method": "mail",
    },
    {
        "name": "Clerk, 14th Circuit Court",
        "role": "Lower Court Clerk",
        "address": "990 Terrace Street, Muskegon, MI 49442",
        "method": "mail",
        "appellate_only": True,
    },
]

# ── Server (filer) information ───────────────────────────────────────────────

SERVER_INFO: Dict[str, str] = {
    "name": "Andrew Pigors",
    "role": "Pro Se",
    "address": "[ADDRESS ON FILE]",
    "phone": "[PHONE ON FILE]",
    "email": "[EMAIL ON FILE]",
}

# ── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class ServedParty:
    """Party receiving service."""
    name: str
    role: str = ""
    address: str = ""
    method: str = "mail"
    appellate_only: bool = False


# ── Core generator ───────────────────────────────────────────────────────────

def generate_cos(
    service_date: str,
    served_parties: List[Dict[str, str]],
    service_method: str = "mail",
    server_name: str = SERVER_INFO["name"],
    court_level: str = "circuit",
    document_title: str = "[DOCUMENT TITLE]",
) -> str:
    """Generate a MCR 2.107-compliant Certificate of Service.

    Args:
        service_date: Date of service (e.g. '2025-01-15' or 'January 15, 2025').
        served_parties: List of dicts with 'name', 'address', and optionally
            'role' and 'method' keys.
        service_method: Default service method for parties without individual
            methods.  One of: ``personal``, ``mail``, ``efiling``, ``email``,
            ``certified_mail``.
        server_name: Name of the person certifying service.
        court_level: One of ``circuit``, ``coa``, ``msc``, ``federal``.
            Controls whether lower-court clerk is auto-included.
        document_title: Title of the document being served.

    Returns:
        Formatted Certificate of Service text ready for filing.
    """
    is_appellate = court_level in ("coa", "msc", "federal")

    # Build the party list — include appellate-only parties when needed
    parties = _resolve_parties(served_parties, service_method, is_appellate)

    # Format the date nicely if it's ISO format
    display_date = _format_date(service_date)

    # Group parties by method for cleaner formatting
    method_groups: Dict[str, List[Dict[str, str]]] = {}
    for p in parties:
        m = p.get("method", service_method)
        method_groups.setdefault(m, []).append(p)

    # Build body
    lines: List[str] = [
        "CERTIFICATE OF SERVICE",
        "",
    ]

    if len(method_groups) == 1:
        # All same method — single paragraph
        method_key = list(method_groups.keys())[0]
        method_text = SERVICE_METHOD_TEXT.get(method_key, method_key)
        lines.append(
            f"    I, {server_name}, hereby certify that on {display_date}, "
            f"I served a true and\ncorrect copy of the foregoing "
            f"{document_title} upon the following parties\nby {method_text}:"
        )
        lines.append("")
        for p in parties:
            lines.extend(_format_party_block(p))
    else:
        # Mixed methods — separate sections per method
        lines.append(
            f"    I, {server_name}, hereby certify that on {display_date}, "
            f"I served a true and\ncorrect copy of the foregoing "
            f"{document_title} upon the following parties:"
        )
        lines.append("")
        for method_key, group in method_groups.items():
            method_text = SERVICE_METHOD_TEXT.get(method_key, method_key)
            lines.append(f"    By {method_text}:")
            lines.append("")
            for p in group:
                lines.extend(_format_party_block(p))

    # Signature block
    lines.extend([
        "",
        f"                                    /s/ {server_name}",
        f"                                    {server_name}, {SERVER_INFO['role']}",
        f"                                    {SERVER_INFO['address']}",
        f"                                    {SERVER_INFO['phone']}",
        f"                                    {SERVER_INFO['email']}",
        f"                                    Date: {display_date}",
    ])

    return "\n".join(lines)


def generate_cos_for_filing(
    filing_text: str,
    served_parties: Optional[List[Dict[str, str]]] = None,
    service_method: str = "mail",
    court_level: str = "circuit",
) -> str:
    """Extract document title from filing text and generate a matching CoS.

    Extracts the document title from the first recognizable heading
    (e.g. ``MOTION FOR ...``, ``BRIEF ON APPEAL``, etc.) and generates a
    Certificate of Service for it.

    Args:
        filing_text: Full text of the filing document.
        served_parties: Parties to serve; defaults to DEFAULT_PARTIES.
        service_method: Default service method.
        court_level: Court level for the filing.

    Returns:
        Formatted Certificate of Service text.
    """
    title = _extract_document_title(filing_text)
    if served_parties is None:
        served_parties = DEFAULT_PARTIES
    today = datetime.now().strftime("%B %d, %Y")
    return generate_cos(
        service_date=today,
        served_parties=served_parties,
        service_method=service_method,
        server_name=SERVER_INFO["name"],
        court_level=court_level,
        document_title=title,
    )


# ── Helpers ──────────────────────────────────────────────────────────────────

def _resolve_parties(
    served_parties: List[Dict[str, str]],
    default_method: str,
    is_appellate: bool,
) -> List[Dict[str, str]]:
    """Merge supplied parties with defaults, filtering by court level."""
    result: List[Dict[str, str]] = []

    # Add explicitly provided parties
    for p in served_parties:
        party = dict(p)
        if "method" not in party:
            party["method"] = default_method
        result.append(party)

    # For appellate filings, ensure lower-court clerk is included
    if is_appellate:
        clerk_names = {p.get("name", "").lower() for p in result}
        for dp in DEFAULT_PARTIES:
            if dp.get("appellate_only") and dp["name"].lower() not in clerk_names:
                result.append(dict(dp))

    return result


def _format_party_block(party: Dict[str, str]) -> List[str]:
    """Format a single party's name/address block for the CoS."""
    lines: List[str] = []
    name = party.get("name", "")
    role = party.get("role", "")
    address = party.get("address", "")

    if role:
        lines.append(f"    {name} ({role})")
    else:
        lines.append(f"    {name}")

    # Split multi-line addresses
    for addr_line in address.split("\n"):
        addr_line = addr_line.strip()
        if addr_line:
            lines.append(f"    {addr_line}")

    lines.append("")  # blank line between parties
    return lines


def _format_date(date_str: str) -> str:
    """Convert ISO date to long form if possible; pass through otherwise."""
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%B %d, %Y")
        except ValueError:
            continue
    return date_str


def _extract_document_title(text: str) -> str:
    """Extract document title from filing text via common heading patterns."""
    # Look for all-caps lines that are likely the title
    patterns = [
        r"^((?:EMERGENCY\s+)?MOTION\s+.+?)$",
        r"^(BRIEF\s+.+?)$",
        r"^(COMPLAINT\s+.+?)$",
        r"^(PETITION\s+.+?)$",
        r"^(APPLICATION\s+.+?)$",
        r"^(RESPONSE\s+.+?)$",
        r"^(REPLY\s+.+?)$",
        r"^(OBJECTION\s+.+?)$",
        r"^(NOTICE\s+.+?)$",
        r"^(AFFIDAVIT\s+.+?)$",
        r"^(APPELLANT(?:'?S)?\s+BRIEF.*)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
        if match:
            title = match.group(1).strip()
            # Clean up: remove trailing punctuation, limit length
            title = re.sub(r"[.;:]+$", "", title)
            if len(title) > 100:
                title = title[:97] + "..."
            return title.upper()

    return "[DOCUMENT TITLE]"


# ── Class interface (for SkillBase / registry compatibility) ─────────────────

class CertificateOfService:
    """MCR 2.107 Certificate of Service Generator — class interface.

    Wraps the module-level functions for use with ``load_skill()`` and
    ``get_skill_class()``.
    """

    SERVICE_METHODS = list(SERVICE_METHOD_TEXT.keys())
    DEFAULT_PARTIES = DEFAULT_PARTIES
    SERVER_INFO = SERVER_INFO

    def generate(
        self,
        service_date: str,
        served_parties: List[Dict[str, str]],
        service_method: str = "mail",
        server_name: str = SERVER_INFO["name"],
        court_level: str = "circuit",
        document_title: str = "[DOCUMENT TITLE]",
    ) -> str:
        """Generate CoS.  See :func:`generate_cos`."""
        return generate_cos(
            service_date, served_parties, service_method,
            server_name, court_level, document_title,
        )

    def generate_for_filing(
        self,
        filing_text: str,
        served_parties: Optional[List[Dict[str, str]]] = None,
        service_method: str = "mail",
        court_level: str = "circuit",
    ) -> str:
        """Generate CoS from filing text.  See :func:`generate_cos_for_filing`."""
        return generate_cos_for_filing(
            filing_text, served_parties, service_method, court_level,
        )


# ── CLI entry point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate MCR 2.107 Certificate of Service"
    )
    parser.add_argument(
        "--date",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="Service date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--title",
        default="[DOCUMENT TITLE]",
        help="Document title",
    )
    parser.add_argument(
        "--court",
        default="circuit",
        choices=["circuit", "coa", "msc", "federal"],
        help="Court level",
    )
    parser.add_argument(
        "--method",
        default="mail",
        choices=list(SERVICE_METHOD_TEXT.keys()),
        help="Service method",
    )
    args = parser.parse_args()

    result = generate_cos(
        service_date=args.date,
        served_parties=DEFAULT_PARTIES,
        service_method=args.method,
        court_level=args.court,
        document_title=args.title,
    )
    print(result)
