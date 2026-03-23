"""Proof of Service Generator — MCR 2.107 compliant service certificates.

Generates court-ready Proof/Certificate of Service documents for all filing
types across all Michigan courts (Circuit, COA, MSC, Federal, JTC).

Usage::

    pos = ProofOfServiceEngine(db_path="litigation_context.db")
    doc = pos.generate(filing_id="F3", method="mail", served_on=["defendant", "foc"])
    pos.generate_batch(filing_ids=["F1","F3","F7"], method="efiling")
    history = pos.get_service_history("F3")
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

_DEFAULT_DB = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")

# Verified party identity — SINGLE SOURCE OF TRUTH
PARTIES: dict[str, dict[str, str]] = {
    "plaintiff": {
        "name": "Andrew James Pigors",
        "address": "1977 Whitehall Road, Lot 17, North Muskegon, MI 49445",
        "phone": "(231) 903-5690",
        "email": "andrewjpigors@gmail.com",
    },
    "defendant": {
        "name": "Emily A. Watson",
        "address": "2160 Garland Drive, Norton Shores, MI 49441",
    },
    "defendant_attorney": {
        "name": "Jennifer Barnes (P55406)",
        "firm": "Barnes Law Firm PLLC",
        "address": "880 Jefferson St Ste B, Muskegon, MI 49440",
        "status": "WITHDREW",
    },
    "foc": {
        "name": "Pamela Rusco",
        "title": "Friend of the Court",
        "address": "990 Terrace St, Muskegon, MI 49442",
    },
    "judge": {
        "name": "Hon. Jenny L. McNeill",
        "court": "14th Circuit Court, Family Division",
        "address": "990 Terrace St, Muskegon, MI 49442",
    },
    "coa_clerk": {
        "name": "Clerk of the Court",
        "court": "Michigan Court of Appeals",
        "address": "925 W. Ottawa St, Lansing, MI 48915",
    },
    "msc_clerk": {
        "name": "Clerk of the Court",
        "court": "Michigan Supreme Court",
        "address": "925 W. Ottawa St, Lansing, MI 48915",
    },
    "jtc": {
        "name": "Judicial Tenure Commission",
        "address": "3034 W. Grand Blvd, Suite 8-450, Detroit, MI 48202",
    },
    "federal_clerk": {
        "name": "Clerk of the Court",
        "court": "U.S. District Court, Western District of Michigan",
        "address": "110 Michigan St NW, Grand Rapids, MI 49503",
    },
}

# Filing → court mapping
FILING_COURTS: dict[str, dict[str, str]] = {
    "F1": {"court": "14th Circuit", "case_number": "2024-001507-DC", "type": "TRO"},
    "F2": {"court": "14th Circuit", "case_number": "2025-002760-CZ", "type": "Housing"},
    "F3": {"court": "14th Circuit", "case_number": "2024-001507-DC", "type": "Disqualification"},
    "F4": {"court": "Federal WDMI", "case_number": "[PENDING]", "type": "§1983"},
    "F5": {"court": "Michigan Supreme Court", "case_number": "[PENDING]", "type": "MSC Bypass"},
    "F6": {"court": "JTC", "case_number": "[PENDING]", "type": "Judicial Misconduct"},
    "F7": {"court": "14th Circuit", "case_number": "2024-001507-DC", "type": "Custody Modification"},
    "F8": {"court": "14th Circuit", "case_number": "2023-5907-PP", "type": "PPO"},
    "F9": {"court": "COA", "case_number": "366810", "type": "Appeal Brief"},
    "F10": {"court": "COA", "case_number": "366810", "type": "Emergency Motion"},
}

# Service method → MCR rule
SERVICE_METHODS: dict[str, dict[str, str]] = {
    "personal": {
        "rule": "MCR 2.107(C)(1)",
        "description": "Personal service — hand-delivered to recipient",
    },
    "mail": {
        "rule": "MCR 2.107(C)(3)",
        "description": "First-class mail, postage prepaid",
        "add_days": "3",  # MCR 2.107(C)(3) adds 3 days for mail service
    },
    "efiling": {
        "rule": "MCR 1.109(G)(6)(a)",
        "description": "Electronic filing and service via MiFile/TrueFiling",
    },
    "email": {
        "rule": "MCR 2.107(C)(4)",
        "description": "Electronic service by email with written consent",
    },
    "fax": {
        "rule": "MCR 2.107(C)(4)",
        "description": "Facsimile transmission",
    },
}

# Filing → required service recipients
FILING_SERVICE_MAP: dict[str, list[str]] = {
    "F1": ["defendant", "foc"],
    "F2": ["defendant"],
    "F3": ["defendant", "foc"],
    "F4": ["defendant", "judge", "foc"],
    "F5": ["defendant", "foc", "coa_clerk"],
    "F6": ["judge"],
    "F7": ["defendant", "foc"],
    "F8": ["defendant"],
    "F9": ["defendant", "coa_clerk"],
    "F10": ["defendant", "coa_clerk"],
}


class ProofOfServiceEngine:
    """Generate and track Proof of Service documents for all filings."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path else _DEFAULT_DB
        self._ensure_table()
        logger.info("ProofOfServiceEngine ready  db=%s", self.db_path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=60)
        conn.execute("PRAGMA busy_timeout = 60000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA cache_size = -32000")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_table(self) -> None:
        conn = self._connect()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS service_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filing_id TEXT NOT NULL,
                    served_party TEXT NOT NULL,
                    party_name TEXT NOT NULL,
                    party_address TEXT,
                    service_method TEXT NOT NULL,
                    service_date TEXT NOT NULL,
                    service_rule TEXT,
                    document_title TEXT,
                    case_number TEXT,
                    court TEXT,
                    notes TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def generate(
        self,
        filing_id: str,
        method: str = "mail",
        served_on: list[str] | None = None,
        service_date: str | None = None,
        document_title: str | None = None,
    ) -> str:
        """Generate a Proof of Service document for a filing.

        Returns the formatted markdown text.
        """
        filing_id = filing_id.upper()
        if filing_id not in FILING_COURTS:
            raise ValueError(f"Unknown filing: {filing_id}. Valid: {list(FILING_COURTS)}")

        if method not in SERVICE_METHODS:
            raise ValueError(f"Unknown method: {method}. Valid: {list(SERVICE_METHODS)}")

        court_info = FILING_COURTS[filing_id]
        method_info = SERVICE_METHODS[method]
        recipients = served_on or FILING_SERVICE_MAP.get(filing_id, ["defendant"])
        svc_date = service_date or datetime.now().strftime("%B %d, %Y")
        doc_title = document_title or f"{court_info['type']} — Filing {filing_id}"

        # Build recipient list
        recipient_lines = []
        for party_key in recipients:
            party = PARTIES.get(party_key, {})
            if not party:
                recipient_lines.append(f"- {party_key}: [ADDRESS REQUIRED]")
                continue
            name = party.get("name", party_key)
            addr = party.get("address", "[ADDRESS REQUIRED]")
            recipient_lines.append(f"- **{name}**\n  {addr}")

        # Calculate effective date for mail service
        effective_note = ""
        if method == "mail":
            effective_note = (
                "\n\n**Note:** Per MCR 2.107(C)(3), service by mail adds three (3) "
                "days to any prescribed response period."
            )

        caption = self._build_caption(filing_id, court_info)

        doc = f"""{caption}

# PROOF OF SERVICE

I, **Andrew James Pigors**, hereby certify that on **{svc_date}**, I served
a true and correct copy of the following document(s):

**{doc_title}**

upon the following parties by **{method_info['description']}** pursuant to
**{method_info['rule']}**:

{chr(10).join(recipient_lines)}

I declare under the penalties of perjury that the foregoing is true and correct.

{effective_note}

Dated: {svc_date}

_________________________________
Andrew James Pigors
1977 Whitehall Road, Lot 17
North Muskegon, MI 49445
(231) 903-5690
andrewjpigors@gmail.com
"""
        return doc

    def record_service(
        self,
        filing_id: str,
        method: str = "mail",
        served_on: list[str] | None = None,
        service_date: str | None = None,
        document_title: str | None = None,
    ) -> int:
        """Record service in the tracking database. Returns count of records inserted."""
        filing_id = filing_id.upper()
        court_info = FILING_COURTS.get(filing_id, {})
        method_info = SERVICE_METHODS.get(method, {})
        recipients = served_on or FILING_SERVICE_MAP.get(filing_id, ["defendant"])
        svc_date = service_date or datetime.now().strftime("%Y-%m-%d")
        doc_title = document_title or f"{court_info.get('type', filing_id)} — Filing {filing_id}"

        conn = self._connect()
        try:
            rows = []
            for party_key in recipients:
                party = PARTIES.get(party_key, {})
                rows.append((
                    filing_id,
                    party_key,
                    party.get("name", party_key),
                    party.get("address", ""),
                    method,
                    svc_date,
                    method_info.get("rule", ""),
                    doc_title,
                    court_info.get("case_number", ""),
                    court_info.get("court", ""),
                ))
            conn.executemany(
                """INSERT INTO service_tracking
                   (filing_id, served_party, party_name, party_address,
                    service_method, service_date, service_rule,
                    document_title, case_number, court)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                rows,
            )
            conn.commit()
            return len(rows)
        finally:
            conn.close()

    def generate_batch(
        self,
        filing_ids: list[str],
        method: str = "mail",
        service_date: str | None = None,
    ) -> dict[str, str]:
        """Generate Proof of Service for multiple filings. Returns {filing_id: markdown}."""
        results: dict[str, str] = {}
        for fid in filing_ids:
            results[fid] = self.generate(filing_id=fid, method=method, service_date=service_date)
        return results

    def get_service_history(self, filing_id: str | None = None) -> list[dict[str, Any]]:
        """Return service history, optionally filtered by filing_id."""
        conn = self._connect()
        try:
            if filing_id:
                rows = conn.execute(
                    "SELECT * FROM service_tracking WHERE filing_id = ? ORDER BY service_date DESC",
                    (filing_id.upper(),),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM service_tracking ORDER BY service_date DESC"
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_unserved_filings(self) -> list[str]:
        """Return filing IDs that have NOT been recorded as served."""
        conn = self._connect()
        try:
            served = {
                r[0]
                for r in conn.execute(
                    "SELECT DISTINCT filing_id FROM service_tracking"
                ).fetchall()
            }
            return [fid for fid in FILING_COURTS if fid not in served]
        finally:
            conn.close()

    def service_dashboard(self) -> dict[str, Any]:
        """Return a service status dashboard for all filings."""
        conn = self._connect()
        try:
            served = {}
            for row in conn.execute(
                "SELECT filing_id, COUNT(*) as cnt, MAX(service_date) as last_date "
                "FROM service_tracking GROUP BY filing_id"
            ).fetchall():
                served[row["filing_id"]] = {
                    "served_count": row["cnt"],
                    "last_service": row["last_date"],
                }

            dashboard = {}
            for fid, info in FILING_COURTS.items():
                required = FILING_SERVICE_MAP.get(fid, ["defendant"])
                svc = served.get(fid, {})
                dashboard[fid] = {
                    "filing": info["type"],
                    "court": info["court"],
                    "required_parties": len(required),
                    "served_count": svc.get("served_count", 0),
                    "last_service": svc.get("last_service"),
                    "status": "SERVED" if fid in served else "PENDING",
                }
            return dashboard
        finally:
            conn.close()

    def _build_caption(self, filing_id: str, court_info: dict[str, str]) -> str:
        court = court_info.get("court", "14th Circuit")
        case_num = court_info.get("case_number", "")

        if court == "Federal WDMI":
            return f"""STATE OF MICHIGAN
UNITED STATES DISTRICT COURT
WESTERN DISTRICT OF MICHIGAN, SOUTHERN DIVISION

ANDREW JAMES PIGORS,
    Plaintiff,                          Case No. {case_num}
v.

HON. JENNY L. McNEILL, et al.,
    Defendants.
________________________________/"""

        if court in ("COA", "Michigan Court of Appeals"):
            return f"""STATE OF MICHIGAN
IN THE COURT OF APPEALS

ANDREW JAMES PIGORS,
    Plaintiff-Appellant,                COA Case No. {case_num}
v.                                      LC No. 2024-001507-DC

EMILY A. WATSON,
    Defendant-Appellee.
________________________________/"""

        if court == "Michigan Supreme Court":
            return f"""STATE OF MICHIGAN
IN THE SUPREME COURT

ANDREW JAMES PIGORS,
    Plaintiff-Appellant,                SC No. {case_num}
v.                                      COA No. 366810
                                        LC No. 2024-001507-DC
EMILY A. WATSON,
    Defendant-Appellee.
________________________________/"""

        if court == "JTC":
            return f"""STATE OF MICHIGAN
JUDICIAL TENURE COMMISSION

IN THE MATTER OF
HON. JENNY L. McNEILL,                 JTC File No. {case_num}
14th Circuit Court Judge.
________________________________/"""

        # Default: Circuit Court
        return f"""STATE OF MICHIGAN
IN THE {court.upper()} COURT FOR THE COUNTY OF MUSKEGON

ANDREW JAMES PIGORS,
    Plaintiff,                          Case No. {case_num}
v.                                      Hon. Jenny L. McNeill

EMILY A. WATSON,
    Defendant.
________________________________/"""
