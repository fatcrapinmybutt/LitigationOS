"""Universal Proof of Service Generator — MCR 2.105 / 2.106 / 2.107 compliant.

Generates court-ready Proof of Service and Certificate of Service documents
for all filing types across Michigan courts (Circuit, COA, MSC, Federal, JTC).
Tracks service history in ``litigation_context.db`` and validates compliance
with Michigan Court Rules for service of process and service of papers.

Michigan Court Rules referenced:
    MCR 2.105      — Service of process
    MCR 2.106      — Proof of service requirements
    MCR 2.107      — Service of pleadings and other papers
    MCR 3.203      — Domestic relations service requirements
    SCAO Form MC 304 — Proof of Service
    SCAO Form MC 305 — Verification of Service by Mail

Usage::

    from litigationos.db.connection import DatabaseManager
    from litigationos.engines.service_generator import ServiceGenerator

    db = DatabaseManager("litigation_context.db")
    gen = ServiceGenerator(db)
    pos = gen.generate_proof_of_service("F3", "mail", ["defendant", "foc"])
    cert = gen.generate_certificate_of_service("F3")
    gen.track_service("F3", "defendant", "mail", "2025-01-15")
    history = gen.get_service_history("2024-001507-DC")
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from litigationos.db.connection import DatabaseManager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants — Verified party identity (SINGLE SOURCE OF TRUTH)
# ---------------------------------------------------------------------------

PARTIES: dict[str, dict[str, str]] = {
    "plaintiff": {
        "name": "Andrew James Pigors",
        "address": "1977 Whitehall Road, Lot 17, North Muskegon, MI 49445",
        "phone": "(231) 903-5690",
        "email": "andrewjpigors@gmail.com",
        "role": "Plaintiff, In Propria Persona",
    },
    "defendant": {
        "name": "Emily A. Watson",
        "address": "2160 Garland Drive, Norton Shores, MI 49441",
        "role": "Defendant",
    },
    "defendant_attorney": {
        "name": "Jennifer Barnes (P55406)",
        "firm": "Barnes Law Firm PLLC",
        "address": "880 Jefferson St Ste B, Muskegon, MI 49440",
        "status": "WITHDREW",
        "role": "Former Attorney for Defendant",
    },
    "foc": {
        "name": "Pamela Rusco",
        "title": "Friend of the Court",
        "address": "990 Terrace St, Muskegon, MI 49442",
        "role": "Friend of the Court",
    },
    "judge": {
        "name": "Hon. Jenny L. McNeill",
        "court": "14th Circuit Court, Family Division",
        "address": "990 Terrace St, Muskegon, MI 49442",
        "role": "Presiding Judge",
    },
    "coa_clerk": {
        "name": "Clerk of the Court",
        "court": "Michigan Court of Appeals",
        "address": "925 W. Ottawa St, Lansing, MI 48915",
        "role": "Clerk",
    },
    "msc_clerk": {
        "name": "Clerk of the Court",
        "court": "Michigan Supreme Court",
        "address": "925 W. Ottawa St, Lansing, MI 48915",
        "role": "Clerk",
    },
    "jtc": {
        "name": "Judicial Tenure Commission",
        "address": "3034 W. Grand Blvd, Suite 8-450, Detroit, MI 48202",
        "role": "Commission",
    },
}

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

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class ServiceMethodEnum(str, Enum):
    """Allowed service methods under Michigan Court Rules."""

    PERSONAL = "personal"
    MAIL = "mail"
    EMAIL = "email"
    EFILING = "efiling"


class ServiceMethod(BaseModel):
    """Describes a method of service and its MCR basis."""

    method_name: str
    mcr_rule: str
    requirements: list[str] = Field(default_factory=list)
    time_to_effective_service: int = 0  # days added for service effectiveness

    model_config = ConfigDict(from_attributes=True)


class ServiceRecord(BaseModel):
    """A single service event on a single party."""

    id: Optional[int] = None
    filing_id: str
    served_party: str
    method: str = "mail"
    date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    address: Optional[str] = None
    party_name: Optional[str] = None
    case_number: Optional[str] = None
    court: Optional[str] = None
    document_title: Optional[str] = None
    completed: bool = True
    notes: Optional[str] = None
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProofOfService(BaseModel):
    """A complete proof of service document for one filing."""

    case_number: str
    filing_title: str
    service_records: list[ServiceRecord] = Field(default_factory=list)
    signer: str = "Andrew James Pigors"
    date_signed: str = Field(
        default_factory=lambda: datetime.now().strftime("%B %d, %Y"),
    )
    court_rule_basis: str = "MCR 2.107"
    markdown: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Service method definitions — MCR-based
# ---------------------------------------------------------------------------

SERVICE_METHODS: dict[str, ServiceMethod] = {
    "personal": ServiceMethod(
        method_name="Personal Service",
        mcr_rule="MCR 2.105(A)",
        requirements=[
            "Delivered personally to the individual",
            "Server must be 18+ years old",
            "Server cannot be a party to the action",
        ],
        time_to_effective_service=0,
    ),
    "mail": ServiceMethod(
        method_name="First-Class Mail",
        mcr_rule="MCR 2.107(C)(1)",
        requirements=[
            "First-class mail, postage prepaid",
            "Addressed to last known address",
            "Service effective 3 days after mailing per MCR 2.107(C)(1)",
        ],
        time_to_effective_service=3,
    ),
    "email": ServiceMethod(
        method_name="Electronic Service (Email)",
        mcr_rule="MCR 2.107(C)(4)",
        requirements=[
            "Written consent of receiving party required",
            "Sent to email address designated in writing",
            "Electronic confirmation of delivery recommended",
        ],
        time_to_effective_service=0,
    ),
    "efiling": ServiceMethod(
        method_name="E-Filing Service (MiFILE)",
        mcr_rule="MCR 1.109(G)(6)(a)",
        requirements=[
            "Filed through MiFILE electronic filing system",
            "Automatic service on registered e-filers",
            "Service receipt generated by system",
        ],
        time_to_effective_service=0,
    ),
}

# ---------------------------------------------------------------------------
# DDL — service_tracking table
# ---------------------------------------------------------------------------

_DDL_SERVICE_TRACKING = """
CREATE TABLE IF NOT EXISTS service_tracking (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    filing_id       TEXT NOT NULL,
    served_party    TEXT NOT NULL,
    party_name      TEXT NOT NULL,
    party_address   TEXT,
    service_method  TEXT NOT NULL,
    service_date    TEXT NOT NULL,
    service_rule    TEXT,
    document_title  TEXT,
    case_number     TEXT,
    court           TEXT,
    completed       INTEGER NOT NULL DEFAULT 1,
    notes           TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);
"""

_DDL_SERVICE_TRACKING_IDX = """
CREATE INDEX IF NOT EXISTS idx_service_tracking_filing
    ON service_tracking(filing_id);
"""

_DDL_SERVICE_TRACKING_CASE_IDX = """
CREATE INDEX IF NOT EXISTS idx_service_tracking_case
    ON service_tracking(case_number);
"""


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class ServiceGenerator:
    """Universal Proof of Service generator and service tracker.

    Generates MCR-compliant Proof of Service and Certificate of Service
    documents, tracks service history in the database, and validates
    service compliance against Michigan Court Rules.

    Args:
        db: A ``DatabaseManager`` instance for all persistence.
    """

    def __init__(self, db: "DatabaseManager") -> None:
        self._db = db
        self._ensure_tables()

    # -- Schema bootstrap ---------------------------------------------------

    def _ensure_tables(self) -> None:
        """Create the service_tracking table if it does not exist."""
        conn = self._db.connect()
        try:
            conn.execute(_DDL_SERVICE_TRACKING)
            conn.execute(_DDL_SERVICE_TRACKING_IDX)
            conn.execute(_DDL_SERVICE_TRACKING_CASE_IDX)
            conn.commit()
        except Exception:
            conn.rollback()
            logger.exception("Failed to bootstrap ServiceGenerator tables")
            raise
        finally:
            conn.close()

    # =====================================================================
    # SERVICE METHODS
    # =====================================================================

    def get_service_methods(self) -> list[ServiceMethod]:
        """Return all valid service methods with MCR rule references.

        Returns:
            List of ``ServiceMethod`` objects describing each method,
            its MCR basis, requirements, and time-to-effectiveness.
        """
        return list(SERVICE_METHODS.values())

    # =====================================================================
    # PROOF OF SERVICE GENERATION
    # =====================================================================

    def generate_proof_of_service(
        self,
        filing_id: str,
        service_method: str = "mail",
        served_parties: list[str] | None = None,
        *,
        service_date: str | None = None,
        document_title: str | None = None,
    ) -> ProofOfService:
        """Generate a complete Proof of Service document.

        Args:
            filing_id: Filing identifier (e.g., ``"F3"``).
            service_method: One of ``"personal"``, ``"mail"``, ``"email"``,
                ``"efiling"``.
            served_parties: Party keys to serve (defaults to filing map).
            service_date: Override service date (ISO or formatted).
            document_title: Override document title.

        Returns:
            A ``ProofOfService`` with generated markdown text.

        Raises:
            ValueError: If *filing_id* or *service_method* is invalid.
        """
        filing_id = filing_id.upper()
        self._validate_filing_id(filing_id)
        self._validate_method(service_method)

        court_info = FILING_COURTS[filing_id]
        method_info = SERVICE_METHODS[service_method]
        recipients = served_parties or FILING_SERVICE_MAP.get(filing_id, ["defendant"])
        svc_date_display = service_date or datetime.now().strftime("%B %d, %Y")
        doc_title = document_title or f"{court_info['type']} — Filing {filing_id}"

        # Build ServiceRecord per recipient
        records: list[ServiceRecord] = []
        for party_key in recipients:
            party = PARTIES.get(party_key, {})
            records.append(ServiceRecord(
                filing_id=filing_id,
                served_party=party_key,
                method=service_method,
                date=svc_date_display,
                address=party.get("address", ""),
                party_name=party.get("name", party_key),
                case_number=court_info.get("case_number", ""),
                court=court_info.get("court", ""),
                document_title=doc_title,
                completed=True,
            ))

        markdown = self._render_proof_of_service(
            filing_id=filing_id,
            court_info=court_info,
            method_info=method_info,
            records=records,
            svc_date=svc_date_display,
            doc_title=doc_title,
        )

        return ProofOfService(
            case_number=court_info.get("case_number", ""),
            filing_title=doc_title,
            service_records=records,
            signer="Andrew James Pigors",
            date_signed=svc_date_display,
            court_rule_basis=method_info.mcr_rule,
            markdown=markdown,
        )

    # =====================================================================
    # CERTIFICATE OF SERVICE GENERATION
    # =====================================================================

    def generate_certificate_of_service(
        self,
        filing_id: str,
        *,
        service_method: str = "mail",
        served_parties: list[str] | None = None,
        service_date: str | None = None,
        document_title: str | None = None,
    ) -> str:
        """Generate a Certificate of Service for attachment to a filing.

        This is a shorter form appended to the end of a motion or brief,
        as distinct from the standalone Proof of Service (MC 304).

        Args:
            filing_id: Filing identifier.
            service_method: Method of service.
            served_parties: Party keys to serve.
            service_date: Override date.
            document_title: Override title.

        Returns:
            Formatted markdown certificate text.

        Raises:
            ValueError: If inputs are invalid.
        """
        filing_id = filing_id.upper()
        self._validate_filing_id(filing_id)
        self._validate_method(service_method)

        court_info = FILING_COURTS[filing_id]
        method_info = SERVICE_METHODS[service_method]
        recipients = served_parties or FILING_SERVICE_MAP.get(filing_id, ["defendant"])
        svc_date = service_date or datetime.now().strftime("%B %d, %Y")
        doc_title = document_title or f"{court_info['type']} — Filing {filing_id}"

        recipient_lines = self._format_recipient_lines(recipients)

        effective_note = ""
        if service_method == "mail":
            effective_date = self._calculate_effective_date(svc_date)
            effective_note = (
                f"\n\nService by mail is effective three (3) days after mailing "
                f"per {method_info.mcr_rule}. Effective date of service: "
                f"**{effective_date}**."
            )

        certificate = f"""## CERTIFICATE OF SERVICE

I, **Andrew James Pigors**, hereby certify that on **{svc_date}**, I served
a true and correct copy of the foregoing **{doc_title}** upon the following
parties by **{method_info.method_name}** pursuant to **{method_info.mcr_rule}**:

{chr(10).join(recipient_lines)}
{effective_note}

_________________________________
Andrew James Pigors
1977 Whitehall Road, Lot 17
North Muskegon, MI 49445
(231) 903-5690
andrewjpigors@gmail.com
Dated: {svc_date}
"""
        return certificate

    # =====================================================================
    # VALIDATION
    # =====================================================================

    def validate_service(self, service_record: ServiceRecord) -> list[str]:
        """Check a service record for compliance with MCR requirements.

        Args:
            service_record: The ``ServiceRecord`` to validate.

        Returns:
            List of compliance issues (empty if compliant).
        """
        issues: list[str] = []

        # Method must be valid
        if service_record.method not in SERVICE_METHODS:
            issues.append(
                f"Invalid service method '{service_record.method}'. "
                f"Must be one of: {list(SERVICE_METHODS.keys())}"
            )
            return issues  # can't check further with invalid method

        method_info = SERVICE_METHODS[service_record.method]

        # Must have a served party
        if not service_record.served_party:
            issues.append("served_party is required per MCR 2.106")

        # Address required for mail / personal
        if service_record.method in ("mail", "personal"):
            if not service_record.address or not service_record.address.strip():
                issues.append(
                    f"Address required for {method_info.method_name} "
                    f"under {method_info.mcr_rule}"
                )

        # Email method requires consent verification
        if service_record.method == "email":
            if not service_record.notes or "consent" not in service_record.notes.lower():
                issues.append(
                    "Email service requires documented written consent "
                    "per MCR 2.107(C)(4)"
                )

        # Date must be present and parseable
        if not service_record.date:
            issues.append("Service date is required per MCR 2.106")
        else:
            try:
                self._parse_date(service_record.date)
            except ValueError:
                issues.append(
                    f"Cannot parse service date '{service_record.date}'. "
                    "Use YYYY-MM-DD or 'Month DD, YYYY' format."
                )

        # Filing ID required
        if not service_record.filing_id:
            issues.append("filing_id is required to track service")

        # Completion check
        if not service_record.completed:
            issues.append("Service is marked as incomplete")

        return issues

    # =====================================================================
    # SERVICE TRACKING (DB)
    # =====================================================================

    def track_service(
        self,
        filing_id: str,
        served_party: str,
        method: str,
        date: str,
        *,
        document_title: str | None = None,
        notes: str | None = None,
    ) -> int:
        """Record a service event in the database.

        Args:
            filing_id: Filing identifier.
            served_party: Party key (e.g., ``"defendant"``).
            method: Service method key.
            date: Service date (ISO or formatted).
            document_title: Title of served document.
            notes: Additional notes.

        Returns:
            Row ID of the inserted record.

        Raises:
            ValueError: If method is invalid.
        """
        filing_id = filing_id.upper()
        self._validate_method(method)

        party = PARTIES.get(served_party, {})
        party_name = party.get("name", served_party)
        party_address = party.get("address", "")
        method_info = SERVICE_METHODS[method]

        court_info = FILING_COURTS.get(filing_id, {})
        case_number = court_info.get("case_number", "")
        court = court_info.get("court", "")
        doc_title = document_title or f"Filing {filing_id}"

        conn = self._db.connect()
        try:
            cursor = conn.execute(
                """INSERT INTO service_tracking
                   (filing_id, served_party, party_name, party_address,
                    service_method, service_date, service_rule,
                    document_title, case_number, court, completed, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)""",
                (
                    filing_id, served_party, party_name, party_address,
                    method, date, method_info.mcr_rule,
                    doc_title, case_number, court, notes,
                ),
            )
            conn.commit()
            row_id = cursor.lastrowid
            logger.info(
                "Tracked service: %s → %s via %s on %s (row %d)",
                filing_id, served_party, method, date, row_id,
            )
            return row_id
        except Exception:
            conn.rollback()
            logger.exception("Failed to track service for %s", filing_id)
            raise
        finally:
            conn.close()

    def get_service_history(
        self,
        case_number: str | None = None,
    ) -> list[ServiceRecord]:
        """Return service records, optionally filtered by case number.

        Args:
            case_number: Filter by court case number. If ``None``, returns
                all records.

        Returns:
            List of ``ServiceRecord`` objects ordered by date descending.
        """
        conn = self._db.connect()
        try:
            if case_number:
                rows = conn.execute(
                    "SELECT * FROM service_tracking "
                    "WHERE case_number = ? "
                    "ORDER BY service_date DESC",
                    (case_number,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM service_tracking ORDER BY service_date DESC"
                ).fetchall()
            return [self._row_to_record(r) for r in rows]
        finally:
            conn.close()

    def get_service_history_by_filing(
        self,
        filing_id: str,
    ) -> list[ServiceRecord]:
        """Return service records for a specific filing.

        Args:
            filing_id: Filing identifier.

        Returns:
            List of ``ServiceRecord`` objects for the filing.
        """
        filing_id = filing_id.upper()
        conn = self._db.connect()
        try:
            rows = conn.execute(
                "SELECT * FROM service_tracking "
                "WHERE filing_id = ? "
                "ORDER BY service_date DESC",
                (filing_id,),
            ).fetchall()
            return [self._row_to_record(r) for r in rows]
        finally:
            conn.close()

    # =====================================================================
    # SERVICE LIST
    # =====================================================================

    def generate_service_list(
        self,
        case_number: str | None = None,
    ) -> str:
        """Generate a formatted service list for all parties in a case.

        Lists all parties who must receive service on filings, along
        with their current contact information.

        Args:
            case_number: Optional case number to scope the list.

        Returns:
            Formatted markdown service list.
        """
        lines: list[str] = ["# SERVICE LIST", ""]

        if case_number:
            lines.append(f"**Case No.:** {case_number}")
            lines.append("")

        lines.append(
            "The following parties are entitled to service of all "
            "pleadings and papers in this matter:\n"
        )

        # Determine parties to list based on case number
        party_keys = self._parties_for_case(case_number)

        for idx, key in enumerate(party_keys, start=1):
            party = PARTIES.get(key, {})
            if not party:
                continue
            name = party.get("name", key)
            address = party.get("address", "[ADDRESS REQUIRED]")
            role = party.get("role", key.replace("_", " ").title())

            status_note = ""
            if party.get("status") == "WITHDREW":
                status_note = " **(WITHDRAWN)**"

            lines.append(f"**{idx}. {name}**{status_note}")
            lines.append(f"   {role}")
            lines.append(f"   {address}")
            if party.get("email"):
                lines.append(f"   Email: {party['email']}")
            if party.get("phone"):
                lines.append(f"   Phone: {party['phone']}")
            lines.append("")

        lines.append("---")
        lines.append(
            f"*Service list generated on "
            f"{datetime.now().strftime('%B %d, %Y')}.*"
        )
        return "\n".join(lines)

    # =====================================================================
    # INTERNAL HELPERS
    # =====================================================================

    @staticmethod
    def _validate_filing_id(filing_id: str) -> None:
        if filing_id not in FILING_COURTS:
            raise ValueError(
                f"Unknown filing: {filing_id}. "
                f"Valid: {list(FILING_COURTS.keys())}"
            )

    @staticmethod
    def _validate_method(method: str) -> None:
        if method not in SERVICE_METHODS:
            raise ValueError(
                f"Unknown service method: {method}. "
                f"Valid: {list(SERVICE_METHODS.keys())}"
            )

    @staticmethod
    def _format_recipient_lines(recipients: list[str]) -> list[str]:
        """Build formatted recipient lines for document rendering."""
        lines: list[str] = []
        for party_key in recipients:
            party = PARTIES.get(party_key, {})
            if not party:
                lines.append(f"- {party_key}: [ADDRESS REQUIRED]")
                continue
            name = party.get("name", party_key)
            addr = party.get("address", "[ADDRESS REQUIRED]")
            role = party.get("role", "")
            role_str = f" ({role})" if role else ""
            lines.append(f"- **{name}**{role_str}")
            lines.append(f"  {addr}")
        return lines

    @staticmethod
    def _calculate_effective_date(service_date_str: str) -> str:
        """Calculate effective date for mail service (+3 days)."""
        try:
            dt = datetime.strptime(service_date_str, "%B %d, %Y")
        except ValueError:
            try:
                dt = datetime.strptime(service_date_str, "%Y-%m-%d")
            except ValueError:
                dt = datetime.now()
        effective = dt + timedelta(days=3)
        return effective.strftime("%B %d, %Y")

    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        """Parse a date string in common formats."""
        for fmt in ("%Y-%m-%d", "%B %d, %Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        raise ValueError(f"Unparseable date: {date_str}")

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> ServiceRecord:
        """Convert a DB row to a ServiceRecord."""
        d = dict(row)
        return ServiceRecord(
            id=d.get("id"),
            filing_id=d.get("filing_id", ""),
            served_party=d.get("served_party", ""),
            method=d.get("service_method", "mail"),
            date=d.get("service_date", ""),
            address=d.get("party_address", ""),
            party_name=d.get("party_name", ""),
            case_number=d.get("case_number", ""),
            court=d.get("court", ""),
            document_title=d.get("document_title", ""),
            completed=bool(d.get("completed", 1)),
            notes=d.get("notes"),
            created_at=d.get("created_at"),
        )

    @staticmethod
    def _parties_for_case(case_number: str | None) -> list[str]:
        """Determine relevant party keys for a case number."""
        if not case_number:
            return ["plaintiff", "defendant", "foc", "judge"]

        # Map case numbers to relevant parties
        case_party_map: dict[str, list[str]] = {
            "2024-001507-DC": ["plaintiff", "defendant", "foc", "judge"],
            "2025-002760-CZ": ["plaintiff", "defendant"],
            "2023-5907-PP": ["plaintiff", "defendant"],
            "366810": ["plaintiff", "defendant", "coa_clerk"],
        }
        return case_party_map.get(case_number, ["plaintiff", "defendant", "foc"])

    def _render_proof_of_service(
        self,
        filing_id: str,
        court_info: dict[str, str],
        method_info: ServiceMethod,
        records: list[ServiceRecord],
        svc_date: str,
        doc_title: str,
    ) -> str:
        """Render the full proof of service markdown document."""
        caption = self._build_caption(filing_id, court_info)
        recipients = [r.served_party for r in records]
        recipient_lines = self._format_recipient_lines(recipients)

        effective_note = ""
        if method_info.time_to_effective_service > 0:
            effective_date = self._calculate_effective_date(svc_date)
            effective_note = (
                f"\n\n**Note:** Per {method_info.mcr_rule}, service by mail "
                f"adds three (3) days to any prescribed response period. "
                f"Effective date of service: **{effective_date}**."
            )

        doc = f"""{caption}

# PROOF OF SERVICE

I, **Andrew James Pigors**, hereby certify that on **{svc_date}**, I served
a true and correct copy of the following document(s):

**{doc_title}**

upon the following parties by **{method_info.method_name}** pursuant to
**{method_info.mcr_rule}**:

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

    @staticmethod
    def _build_caption(filing_id: str, court_info: dict[str, str]) -> str:
        """Build court caption header based on filing court."""
        court = court_info.get("court", "14th Circuit")
        case_num = court_info.get("case_number", "")

        if court == "Federal WDMI":
            return (
                "STATE OF MICHIGAN\n"
                "UNITED STATES DISTRICT COURT\n"
                "WESTERN DISTRICT OF MICHIGAN, SOUTHERN DIVISION\n\n"
                "ANDREW JAMES PIGORS,\n"
                f"    Plaintiff,                          Case No. {case_num}\n"
                "v.\n\n"
                "HON. JENNY L. McNEILL, et al.,\n"
                "    Defendants.\n"
                "________________________________/"
            )

        if court in ("COA", "Michigan Court of Appeals"):
            return (
                "STATE OF MICHIGAN\n"
                "IN THE COURT OF APPEALS\n\n"
                "ANDREW JAMES PIGORS,\n"
                f"    Plaintiff-Appellant,                COA Case No. {case_num}\n"
                "v.                                      LC No. 2024-001507-DC\n\n"
                "EMILY A. WATSON,\n"
                "    Defendant-Appellee.\n"
                "________________________________/"
            )

        if court == "Michigan Supreme Court":
            return (
                "STATE OF MICHIGAN\n"
                "IN THE SUPREME COURT\n\n"
                "ANDREW JAMES PIGORS,\n"
                f"    Plaintiff-Appellant,                SC No. {case_num}\n"
                "v.                                      COA No. 366810\n"
                "                                        LC No. 2024-001507-DC\n"
                "EMILY A. WATSON,\n"
                "    Defendant-Appellee.\n"
                "________________________________/"
            )

        if court == "JTC":
            return (
                "STATE OF MICHIGAN\n"
                "JUDICIAL TENURE COMMISSION\n\n"
                "IN THE MATTER OF\n"
                f"HON. JENNY L. McNEILL,                 JTC File No. {case_num}\n"
                "14th Circuit Court Judge.\n"
                "________________________________/"
            )

        # Default: Circuit Court
        return (
            "STATE OF MICHIGAN\n"
            f"IN THE {court.upper()} COURT FOR THE COUNTY OF MUSKEGON\n\n"
            "ANDREW JAMES PIGORS,\n"
            f"    Plaintiff,                          Case No. {case_num}\n"
            "v.                                      Hon. Jenny L. McNeill\n\n"
            "EMILY A. WATSON,\n"
            "    Defendant.\n"
            "________________________________/"
        )
