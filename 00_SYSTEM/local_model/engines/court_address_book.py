# -*- coding: utf-8 -*-
"""
Court Address Book Engine — LitigationOS MANBEARPIG v8.0
=========================================================
Maintain addresses for all parties, courts, and agencies in Pigors v Watson.

Stores addresses both in-module (for offline use) and in litigation_context.db
(court_address_book table) for cross-engine queries.

Authority:
    MCR 2.107  — Service of process
    MCR 2.113  — Form of papers (caption requirements)
    MCR 1.109  — MiFile e-filing

Usage:
    python court_address_book.py
"""

import sys
import os
import io
import sqlite3
import json
from datetime import date
from typing import Dict, List, Optional

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
elif sys.stdout is None or not hasattr(sys.stdout, "encoding") or sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer if sys.stdout else open(os.devnull, "w"), encoding="utf-8")

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

# ---------------------------------------------------------------------------
# In-module address registry
# ---------------------------------------------------------------------------

ADDRESS_BOOK: Dict[str, Dict] = {
    # --- COURTS ---
    "14th_circuit_court": {
        "entity_type": "court",
        "name": "14th Circuit Court — Muskegon County",
        "address_line1": "990 Terrace Street",
        "address_line2": "Hall of Justice",
        "city": "Muskegon",
        "state": "MI",
        "zip": "49442",
        "phone": "(231) 724-6251",
        "judge": "Hon. Jenny L. McNeill",
        "case_number": "2024-001507-DC",
        "mifile": True,
        "mifile_url": "https://mifile.courts.michigan.gov",
        "service_method": "mifile",
    },
    "mi_court_of_appeals": {
        "entity_type": "court",
        "name": "Michigan Court of Appeals — Grand Rapids",
        "address_line1": "300 Ottawa Avenue NW",
        "address_line2": "Suite 453",
        "city": "Grand Rapids",
        "state": "MI",
        "zip": "49503",
        "phone": "(616) 456-1167",
        "case_number": "366810",
        "mifile": True,
        "mifile_url": "https://mifile.courts.michigan.gov",
        "service_method": "mifile",
    },
    "mi_supreme_court": {
        "entity_type": "court",
        "name": "Michigan Supreme Court",
        "address_line1": "925 West Ottawa Street",
        "address_line2": "P.O. Box 30052",
        "city": "Lansing",
        "state": "MI",
        "zip": "48909",
        "phone": "(517) 373-0120",
        "mifile": True,
        "mifile_url": "https://mifile.courts.michigan.gov",
        "filing_note": "13 copies required for original actions per MCR 7.306(B)(2)",
        "service_method": "mail",
    },
    "usdc_western_mi": {
        "entity_type": "court",
        "name": "U.S. District Court — Western District of Michigan",
        "address_line1": "110 Michigan Street NW",
        "address_line2": "Suite 399",
        "city": "Grand Rapids",
        "state": "MI",
        "zip": "49503",
        "phone": "(616) 456-2381",
        "ecf_url": "https://ecf.miwd.uscourts.gov",
        "mifile": False,
        "service_method": "ecf",
    },
    "jtc": {
        "entity_type": "agency",
        "name": "Judicial Tenure Commission",
        "address_line1": "3034 West Grand Boulevard",
        "address_line2": "Suite 8-450",
        "city": "Detroit",
        "state": "MI",
        "zip": "48202",
        "phone": "(313) 875-5110",
        "mifile": False,
        "service_method": "mail",
        "filing_note": "Complaints per MCR 9.200–9.252",
    },
    # --- PARTIES ---
    "andrew_pigors": {
        "entity_type": "party",
        "role": "Plaintiff/Appellant (Pro Se)",
        "name": "Andrew Pigors",
        "address_line1": "[ADDRESS ON FILE]",
        "city": "Muskegon",
        "state": "MI",
        "zip": "[ZIP]",
        "phone": "[PHONE]",
        "email": "[EMAIL ON FILE]",
        "bar_number": "N/A — Pro Se",
        "service_method": "mail",
    },
    "tiffany_watson": {
        "entity_type": "party",
        "role": "Defendant/Appellee",
        "name": "Tiffany Watson",
        "address_line1": "[ADDRESS ON FILE WITH COURT]",
        "city": "Muskegon",
        "state": "MI",
        "zip": "[ZIP]",
        "service_method": "mail",
        "notes": "Represented by Ron Berry on appeal",
    },
    "emily_watson": {
        "entity_type": "party",
        "role": "Non-party / Interested Person",
        "name": "Emily Watson",
        "address_line1": "[ADDRESS ON FILE WITH COURT]",
        "city": "Muskegon",
        "state": "MI",
        "zip": "[ZIP]",
        "service_method": "mail",
        "notes": "Non-attorney filing legal documents — UPL concern under MCR 8.120",
    },
    "ron_berry": {
        "entity_type": "attorney",
        "role": "Appellee Attorney",
        "name": "Ron Berry",
        "firm": "[FIRM NAME]",
        "address_line1": "[ADDRESS ON FILE]",
        "city": "[CITY]",
        "state": "MI",
        "zip": "[ZIP]",
        "phone": "[PHONE]",
        "email": "[EMAIL ON FILE]",
        "bar_number": "[BAR #]",
        "service_method": "mail",
        "notes": "Appellate attorney for Tiffany Watson; coordination pattern documented",
    },
    # --- AGENCIES ---
    "friend_of_court": {
        "entity_type": "agency",
        "role": "Friend of the Court — Muskegon County",
        "name": "Muskegon County Friend of the Court",
        "address_line1": "990 Terrace Street",
        "address_line2": "Hall of Justice",
        "city": "Muskegon",
        "state": "MI",
        "zip": "49442",
        "phone": "(231) 724-6289",
        "service_method": "mail",
        "contact": "Jennifer Barnes",
    },
    "scao": {
        "entity_type": "agency",
        "name": "State Court Administrative Office",
        "address_line1": "925 West Ottawa Street",
        "address_line2": "P.O. Box 30048",
        "city": "Lansing",
        "state": "MI",
        "zip": "48909",
        "phone": "(517) 373-0128",
        "service_method": "mail",
    },
    "healthwest": {
        "entity_type": "agency",
        "name": "HealthWest (Muskegon County CMH)",
        "address_line1": "376 E. Apple Avenue",
        "city": "Muskegon",
        "state": "MI",
        "zip": "49442",
        "phone": "(231) 724-1111",
        "service_method": "mail",
    },
}

# Case information for captions
CASE_INFO = {
    "lane_a": {
        "case_number": "2024-001507-DC",
        "court": "14th Circuit Court — Muskegon County",
        "judge": "Hon. Jenny L. McNeill",
        "plaintiff": "ANDREW PIGORS",
        "defendant": "TIFFANY WATSON",
    },
    "lane_d": {
        "case_number": "2023-5907-PP",
        "court": "14th Circuit Court — Muskegon County",
        "judge": "Hon. Jenny L. McNeill",
        "plaintiff": "TIFFANY WATSON",
        "defendant": "ANDREW PIGORS",
    },
    "lane_f": {
        "case_number": "366810",
        "court": "Michigan Court of Appeals",
        "appellant": "ANDREW PIGORS",
        "appellee": "TIFFANY WATSON",
        "lower_court_no": "2024-001507-DC",
    },
    "msc": {
        "case_number": "[TO BE ASSIGNED]",
        "court": "Michigan Supreme Court",
        "plaintiff": "ANDREW PIGORS",
        "defendant": "HON. JENNY L. McNEILL, 14th Circuit Court Judge",
    },
}


def _init_db_table():
    """Create the court_address_book table in the litigation DB if it doesn't exist."""
    if not os.path.exists(DB_PATH):
        return
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS court_address_book (
            entity_id TEXT PRIMARY KEY,
            entity_type TEXT NOT NULL,
            name TEXT NOT NULL,
            role TEXT,
            address_line1 TEXT,
            address_line2 TEXT,
            city TEXT,
            state TEXT,
            zip TEXT,
            phone TEXT,
            email TEXT,
            service_method TEXT,
            mifile INTEGER DEFAULT 0,
            notes TEXT,
            extra_json TEXT,
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


def sync_to_db():
    """Write the in-module address book to litigation_context.db."""
    if not os.path.exists(DB_PATH):
        return {"error": f"Database not found: {DB_PATH}"}
    _init_db_table()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    count = 0
    for entity_id, data in ADDRESS_BOOK.items():
        extra = {k: v for k, v in data.items()
                 if k not in ("entity_type", "name", "role", "address_line1",
                              "address_line2", "city", "state", "zip", "phone",
                              "email", "service_method", "mifile", "notes")}
        cur.execute("""
            INSERT OR REPLACE INTO court_address_book
            (entity_id, entity_type, name, role, address_line1, address_line2,
             city, state, zip, phone, email, service_method, mifile, notes, extra_json, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            entity_id,
            data.get("entity_type", ""),
            data.get("name", ""),
            data.get("role", ""),
            data.get("address_line1", ""),
            data.get("address_line2", ""),
            data.get("city", ""),
            data.get("state", ""),
            data.get("zip", ""),
            data.get("phone", ""),
            data.get("email", ""),
            data.get("service_method", ""),
            1 if data.get("mifile") else 0,
            data.get("notes", ""),
            json.dumps(extra) if extra else None,
        ))
        count += 1
    conn.commit()
    conn.close()
    return {"synced": count, "table": "court_address_book"}


def get_address(entity: str) -> Dict:
    """
    Look up an entity by key or partial name match.

    Args:
        entity: Entity key (e.g. 'ron_berry') or partial name (e.g. 'Berry')

    Returns:
        Dict with address data or error.
    """
    key = entity.lower().replace(" ", "_")
    if key in ADDRESS_BOOK:
        return ADDRESS_BOOK[key]
    # Partial name match
    for k, v in ADDRESS_BOOK.items():
        if entity.lower() in v.get("name", "").lower():
            return v
    return {"error": f"Entity not found: {entity}"}


def format_address_block(entity: str) -> str:
    """Format a mailing address block for an entity."""
    data = get_address(entity)
    if "error" in data:
        return data["error"]
    lines = [data.get("name", "")]
    if data.get("firm"):
        lines.append(data["firm"])
    if data.get("address_line1"):
        lines.append(data["address_line1"])
    if data.get("address_line2"):
        lines.append(data["address_line2"])
    city_line = f"{data.get('city', '')}, {data.get('state', '')} {data.get('zip', '')}"
    lines.append(city_line.strip())
    return "\n".join(lines)


def format_certificate_of_service(recipients: List[str]) -> str:
    """
    Generate a Certificate of Service block listing all recipients.

    Args:
        recipients: List of entity keys or names

    Returns:
        Formatted COS recipient list.
    """
    today = date.today().strftime("%B %d, %Y")
    lines = [
        "CERTIFICATE OF SERVICE",
        "",
        f"I certify that on {today}, I served a copy of the foregoing on the",
        "following parties by the method indicated:",
        "",
    ]
    for i, recipient in enumerate(recipients, 1):
        data = get_address(recipient)
        if "error" in data:
            lines.append(f"  {i}. {recipient} — ADDRESS NOT FOUND")
            continue
        method = data.get("service_method", "mail").upper()
        if method == "MIFILE":
            method_str = "MiFile e-service"
        elif method == "ECF":
            method_str = "ECF electronic filing"
        elif method == "MAIL":
            method_str = "First-class U.S. Mail, postage prepaid"
        elif method == "EMAIL":
            method_str = "Electronic mail"
        else:
            method_str = f"Service by {method}"

        addr = format_address_block(recipient)
        addr_indented = "\n".join(f"     {line}" for line in addr.split("\n"))
        lines.append(f"  {i}. {data.get('name', recipient)}")
        lines.append(f"     Method: {method_str}")
        lines.append(addr_indented)
        lines.append("")

    lines += [
        "",
        "________________________________",
        "Andrew Pigors, Pro Se Plaintiff",
        f"Date: {today}",
    ]
    return "\n".join(lines)


def format_caption(case_number: str = "2024-001507-DC", court: str = "trial") -> str:
    """
    Generate a Michigan-compliant case caption per MCR 2.113.

    Args:
        case_number: Case number string
        court: trial | coa | msc | federal
    """
    if court in ("trial", "14th"):
        info = CASE_INFO.get("lane_a", {})
        return (
            f"STATE OF MICHIGAN\n"
            f"IN THE CIRCUIT COURT FOR THE COUNTY OF MUSKEGON\n"
            f"FAMILY DIVISION\n"
            f"\n"
            f"{info.get('plaintiff', 'ANDREW PIGORS')},\n"
            f"    Plaintiff,                           Case No. {case_number}\n"
            f"                                         {info.get('judge', 'Hon. Jenny L. McNeill')}\n"
            f"v.\n"
            f"\n"
            f"{info.get('defendant', 'TIFFANY WATSON')},\n"
            f"    Defendant.\n"
            f"{'_'*50}/\n"
        )
    elif court == "coa":
        info = CASE_INFO.get("lane_f", {})
        return (
            f"STATE OF MICHIGAN\n"
            f"IN THE COURT OF APPEALS\n"
            f"\n"
            f"{info.get('appellant', 'ANDREW PIGORS')},\n"
            f"    Plaintiff-Appellant,                 COA Case No. {case_number}\n"
            f"                                         LC No. {info.get('lower_court_no', '2024-001507-DC')}\n"
            f"v.\n"
            f"\n"
            f"{info.get('appellee', 'TIFFANY WATSON')},\n"
            f"    Defendant-Appellee.\n"
            f"{'_'*50}/\n"
        )
    elif court == "msc":
        info = CASE_INFO.get("msc", {})
        return (
            f"STATE OF MICHIGAN\n"
            f"IN THE SUPREME COURT\n"
            f"\n"
            f"{info.get('plaintiff', 'ANDREW PIGORS')},\n"
            f"    Plaintiff,                           MSC No. {case_number}\n"
            f"\n"
            f"v.\n"
            f"\n"
            f"{info.get('defendant', 'HON. JENNY L. McNEILL')},\n"
            f"    Respondent.\n"
            f"{'_'*50}/\n"
        )
    elif court == "federal":
        return (
            f"UNITED STATES DISTRICT COURT\n"
            f"WESTERN DISTRICT OF MICHIGAN\n"
            f"SOUTHERN DIVISION\n"
            f"\n"
            f"ANDREW PIGORS,\n"
            f"    Plaintiff,                           Case No. {case_number}\n"
            f"\n"
            f"v.\n"
            f"\n"
            f"JENNY L. McNEILL, et al.,\n"
            f"    Defendants.\n"
            f"{'_'*50}/\n"
        )
    return f"[Unknown court type: {court}]"


def list_entities(entity_type: Optional[str] = None) -> List[Dict]:
    """List all entities, optionally filtered by type."""
    results = []
    for key, data in ADDRESS_BOOK.items():
        if entity_type and data.get("entity_type") != entity_type:
            continue
        results.append({"key": key, **data})
    return results


def main():
    """CLI test harness."""
    print("=" * 70)
    print("COURT ADDRESS BOOK ENGINE — LitigationOS MANBEARPIG v8.0")
    print("=" * 70)

    # Test 1: Sync to DB
    print("\n[TEST 1] Syncing address book to DB:")
    result = sync_to_db()
    print(f"  {result}")

    # Test 2: Look up entities
    print("\n[TEST 2] Address lookups:")
    for entity in ["14th_circuit_court", "ron_berry", "mi_supreme_court"]:
        data = get_address(entity)
        print(f"  {entity}: {data.get('name', 'N/A')} — {data.get('city', 'N/A')}, {data.get('state', 'N/A')}")

    # Test 3: Address block
    print("\n[TEST 3] Formatted address block:")
    print(format_address_block("mi_court_of_appeals"))

    # Test 4: Certificate of service
    print("\n[TEST 4] Certificate of Service:")
    print(format_certificate_of_service(["tiffany_watson", "ron_berry", "friend_of_court"]))

    # Test 5: Captions
    for court in ["trial", "coa", "msc", "federal"]:
        print(f"\n[TEST 5-{court}] Caption — {court.upper()}:")
        print(format_caption(court=court))

    # Test 6: List all entities
    print("\n[TEST 6] All entities:")
    for e in list_entities():
        print(f"  [{e['entity_type']:8s}] {e['key']:25s} — {e['name']}")

    print("\n✓ Court Address Book Engine — all tests complete.")


if __name__ == "__main__":
    main()
