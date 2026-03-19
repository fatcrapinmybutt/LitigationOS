"""LitigationOS Subpoena Engine v1.0
====================================
Comprehensive subpoena generation, tracking, service logging,
and enforcement for Michigan family-law litigation.

Covers MCR 2.305 (production of documents), MCR 2.506 (witness
attendance), MCR 2.313 (sanctions), MCR 2.302(C) (protective orders),
MCR 3.606 (contempt), MCL 600.1455 (subpoena power),
MCL 600.1852 (UIDDA), and MCL 600.2552 (witness fees).

Case: Pigors v. Watson (19 defendants, 8 jurisdictions)
Plaintiff: Andrew James Pigors (Pro Se)
Defendant: Emily A. Watson
Child: Lincoln David Watson (L.D.W.) — MALE
Judge: Hon. Jenny L. McNeill

100 % local · zero-API · stdlib-only · Python 3.12+
"""
from __future__ import annotations

import json
import logging
import pathlib
import sqlite3
import sys
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_REPO = pathlib.Path(__file__).resolve().parent.parent.parent
_DB_PATH = _REPO / "litigation_context.db"

# ---------------------------------------------------------------------------
# Party constants
# ---------------------------------------------------------------------------
PLAINTIFF = "Andrew James Pigors"
PLAINTIFF_ROLE = "Pro Se Litigant"
DEFENDANT = "Emily A. Watson"
CHILD = "Lincoln David Watson"
CHILD_INITIALS = "L.D.W."
JUDGE = "Hon. Jenny L. McNeill"

CASE_LANES: Dict[str, Dict[str, str]] = {
    "A": {"subject": "Custody", "case_number": "2024-001507-DC"},
    "B": {"subject": "Housing", "case_number": "2025-002760-CZ"},
    "C": {"subject": "Convergence", "case_number": "Multi-lane"},
    "D": {"subject": "PPO", "case_number": "2023-5907-PP"},
    "E": {"subject": "Misconduct/JTC", "case_number": "Judge McNeill"},
    "F": {"subject": "Appellate", "case_number": "COA 366810"},
}

# ---------------------------------------------------------------------------
# Michigan legal constants
# ---------------------------------------------------------------------------
WITNESS_FEE_PER_DAY = Decimal("12.00")           # MCL 600.2552
IRS_MILEAGE_RATE = Decimal("0.67")                # Current IRS standard
SERVICE_FEE_PERSONAL = Decimal("35.00")
SERVICE_FEE_REGISTERED = Decimal("15.00")
SERVICE_FEE_CERTIFIED_MAIL = Decimal("8.50")

_PRAGMAS = """\
PRAGMA busy_timeout = 60000;
PRAGMA journal_mode = WAL;
PRAGMA cache_size  = -32000;
PRAGMA synchronous = NORMAL;
PRAGMA temp_store  = MEMORY;
"""

_SCHEMA = """\
CREATE TABLE IF NOT EXISTS subpoenas (
    subpoena_id      TEXT PRIMARY KEY,
    subpoena_type    TEXT NOT NULL,
    case_number      TEXT NOT NULL,
    case_lane        TEXT NOT NULL DEFAULT '',
    recipient_name   TEXT NOT NULL,
    recipient_address TEXT NOT NULL DEFAULT '',
    recipient_type   TEXT NOT NULL DEFAULT 'INDIVIDUAL',
    documents_requested TEXT NOT NULL DEFAULT '[]',
    testimony_topics TEXT NOT NULL DEFAULT '[]',
    date_issued      TEXT,
    date_due         TEXT,
    hearing_date     TEXT,
    hearing_location TEXT NOT NULL DEFAULT '',
    status           TEXT NOT NULL DEFAULT 'DRAFT',
    service_method   TEXT NOT NULL DEFAULT '',
    service_date     TEXT,
    server_name      TEXT NOT NULL DEFAULT '',
    response_date    TEXT,
    objection_details TEXT NOT NULL DEFAULT '',
    notes            TEXT NOT NULL DEFAULT '',
    created_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS subpoena_service_log (
    log_id           TEXT PRIMARY KEY,
    subpoena_id      TEXT NOT NULL,
    service_method   TEXT NOT NULL,
    service_date     TEXT NOT NULL,
    server_name      TEXT NOT NULL,
    recipient_response TEXT NOT NULL DEFAULT '',
    notes            TEXT NOT NULL DEFAULT '',
    created_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    FOREIGN KEY (subpoena_id) REFERENCES subpoenas(subpoena_id)
);

CREATE TABLE IF NOT EXISTS subpoena_enforcement (
    enforcement_id   TEXT PRIMARY KEY,
    subpoena_id      TEXT NOT NULL,
    action_type      TEXT NOT NULL,
    motion_text      TEXT NOT NULL DEFAULT '',
    filed_date       TEXT,
    status           TEXT NOT NULL DEFAULT 'PENDING',
    sanctions_amount TEXT NOT NULL DEFAULT '0.00',
    notes            TEXT NOT NULL DEFAULT '',
    created_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    FOREIGN KEY (subpoena_id) REFERENCES subpoenas(subpoena_id)
);

CREATE INDEX IF NOT EXISTS idx_subpoenas_case
    ON subpoenas(case_number, case_lane);
CREATE INDEX IF NOT EXISTS idx_subpoenas_status
    ON subpoenas(status);
CREATE INDEX IF NOT EXISTS idx_subpoenas_recipient
    ON subpoenas(recipient_name);
CREATE INDEX IF NOT EXISTS idx_service_log_subpoena
    ON subpoena_service_log(subpoena_id);
CREATE INDEX IF NOT EXISTS idx_enforcement_subpoena
    ON subpoena_enforcement(subpoena_id);
"""


# ═══════════════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════════════

class SubpoenaType(Enum):
    """Types of subpoenas available under Michigan Court Rules."""
    WITNESS = "WITNESS"
    DUCES_TECUM = "DUCES_TECUM"
    DEPOSITION = "DEPOSITION"
    TRIAL = "TRIAL"
    HEARING = "HEARING"
    RECORDS_ONLY = "RECORDS_ONLY"


class SubpoenaStatus(Enum):
    """Lifecycle states for a subpoena."""
    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    SERVED = "SERVED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    OBJECTED = "OBJECTED"
    QUASHED = "QUASHED"
    COMPLIED = "COMPLIED"
    NONCOMPLIANT = "NONCOMPLIANT"
    MOTION_TO_COMPEL = "MOTION_TO_COMPEL"


class RecipientType(Enum):
    """Subpoena recipient classification."""
    INDIVIDUAL = "INDIVIDUAL"
    ORGANIZATION = "ORGANIZATION"


class ServiceMethod(Enum):
    """Permitted service methods under MCR 2.105."""
    PERSONAL = "PERSONAL"
    REGISTERED_MAIL = "REGISTERED_MAIL"
    CERTIFIED_MAIL = "CERTIFIED_MAIL"
    FIRST_CLASS_MAIL = "FIRST_CLASS_MAIL"
    PROCESS_SERVER = "PROCESS_SERVER"
    SHERIFF = "SHERIFF"
    SUBSTITUTED = "SUBSTITUTED"
    PUBLICATION = "PUBLICATION"


# ═══════════════════════════════════════════════════════════════════════════
# Dataclasses
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class SubpoenaRecord:
    """Full record of a subpoena with service and compliance state."""

    subpoena_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    subpoena_type: SubpoenaType = SubpoenaType.WITNESS
    case_number: str = ""
    case_lane: str = ""
    recipient_name: str = ""
    recipient_address: str = ""
    recipient_type: RecipientType = RecipientType.INDIVIDUAL
    documents_requested: List[str] = field(default_factory=list)
    testimony_topics: List[str] = field(default_factory=list)
    date_issued: Optional[str] = None
    date_due: Optional[str] = None
    hearing_date: Optional[str] = None
    hearing_location: str = ""
    status: SubpoenaStatus = SubpoenaStatus.DRAFT
    service_method: str = ""
    service_date: Optional[str] = None
    server_name: str = ""
    response_date: Optional[str] = None
    objection_details: str = ""
    notes: str = ""

    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        """Serialise to plain dict (JSON-safe)."""
        return {
            "subpoena_id": self.subpoena_id,
            "subpoena_type": self.subpoena_type.value,
            "case_number": self.case_number,
            "case_lane": self.case_lane,
            "recipient_name": self.recipient_name,
            "recipient_address": self.recipient_address,
            "recipient_type": self.recipient_type.value,
            "documents_requested": list(self.documents_requested),
            "testimony_topics": list(self.testimony_topics),
            "date_issued": self.date_issued,
            "date_due": self.date_due,
            "hearing_date": self.hearing_date,
            "hearing_location": self.hearing_location,
            "status": self.status.value,
            "service_method": self.service_method,
            "service_date": self.service_date,
            "server_name": self.server_name,
            "response_date": self.response_date,
            "objection_details": self.objection_details,
            "notes": self.notes,
        }

    # ------------------------------------------------------------------
    def is_overdue(self) -> bool:
        """Return *True* if the due date has passed without compliance."""
        if not self.date_due:
            return False
        if self.status in (
            SubpoenaStatus.COMPLIED,
            SubpoenaStatus.QUASHED,
        ):
            return False
        try:
            due = date.fromisoformat(self.date_due)
            return date.today() > due
        except (ValueError, TypeError):
            return False

    # ------------------------------------------------------------------
    def days_until_due(self) -> Optional[int]:
        """Days remaining until the due date (negative = overdue)."""
        if not self.date_due:
            return None
        try:
            due = date.fromisoformat(self.date_due)
            return (due - date.today()).days
        except (ValueError, TypeError):
            return None

    # ------------------------------------------------------------------
    @classmethod
    def from_row(cls, row: sqlite3.Row) -> SubpoenaRecord:
        """Build a record from a DB row."""
        d = dict(row)
        docs = d.get("documents_requested", "[]")
        topics = d.get("testimony_topics", "[]")
        return cls(
            subpoena_id=d["subpoena_id"],
            subpoena_type=SubpoenaType(d.get("subpoena_type", "WITNESS")),
            case_number=d.get("case_number", ""),
            case_lane=d.get("case_lane", ""),
            recipient_name=d.get("recipient_name", ""),
            recipient_address=d.get("recipient_address", ""),
            recipient_type=RecipientType(
                d.get("recipient_type", "INDIVIDUAL")
            ),
            documents_requested=json.loads(docs) if isinstance(docs, str) else docs,
            testimony_topics=json.loads(topics) if isinstance(topics, str) else topics,
            date_issued=d.get("date_issued"),
            date_due=d.get("date_due"),
            hearing_date=d.get("hearing_date"),
            hearing_location=d.get("hearing_location", ""),
            status=SubpoenaStatus(d.get("status", "DRAFT")),
            service_method=d.get("service_method", ""),
            service_date=d.get("service_date"),
            server_name=d.get("server_name", ""),
            response_date=d.get("response_date"),
            objection_details=d.get("objection_details", ""),
            notes=d.get("notes", ""),
        )


# ═══════════════════════════════════════════════════════════════════════════
# Database helpers
# ═══════════════════════════════════════════════════════════════════════════

def _get_conn(db_path: Optional[pathlib.Path] = None) -> sqlite3.Connection:
    """Open a WAL-mode connection with EAGAIN-safe PRAGMAs."""
    p = db_path or _DB_PATH
    conn = sqlite3.connect(str(p), timeout=120)
    conn.executescript(_PRAGMAS)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    """Create tables/indexes if they do not exist."""
    conn.executescript(_SCHEMA)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today_iso() -> str:
    return date.today().isoformat()


# ═══════════════════════════════════════════════════════════════════════════
# SubpoenaGenerator
# ═══════════════════════════════════════════════════════════════════════════

class SubpoenaGenerator:
    """Generate subpoenas compliant with Michigan Court Rules.

    Produces formatted subpoena bodies for MCR 2.506 (witness attendance),
    MCR 2.305 (production), and MCR 2.306/2.305 (deposition).
    """

    # ------------------------------------------------------------------
    def __init__(self) -> None:
        self._generated_count: int = 0

    # ------------------------------------------------------------------
    def generate_witness_subpoena(
        self,
        recipient: str,
        hearing_date: str,
        court: str,
        case_number: str,
        *,
        case_lane: str = "A",
        hearing_location: str = "",
        testimony_topics: Optional[List[str]] = None,
    ) -> SubpoenaRecord:
        """Generate a witness subpoena under MCR 2.506.

        Parameters
        ----------
        recipient : str
            Full legal name of the witness.
        hearing_date : str
            ISO-8601 date of the hearing.
        court : str
            Full court name (e.g. "14th Circuit Court, Muskegon County").
        case_number : str
            Docket number.
        """
        rec = SubpoenaRecord(
            subpoena_type=SubpoenaType.WITNESS,
            case_number=case_number,
            case_lane=case_lane,
            recipient_name=recipient,
            hearing_date=hearing_date,
            hearing_location=hearing_location or court,
            testimony_topics=testimony_topics or [],
            date_issued=_today_iso(),
            status=SubpoenaStatus.DRAFT,
        )
        self._generated_count += 1
        logger.info("Generated WITNESS subpoena %s for %s", rec.subpoena_id, recipient)
        return rec

    # ------------------------------------------------------------------
    def generate_duces_tecum(
        self,
        recipient: str,
        documents: List[str],
        deadline: str,
        *,
        case_number: str = "",
        case_lane: str = "A",
        recipient_type: RecipientType = RecipientType.INDIVIDUAL,
        recipient_address: str = "",
    ) -> SubpoenaRecord:
        """Generate a subpoena duces tecum under MCR 2.305.

        Requests production of documents/records from the recipient.
        """
        rec = SubpoenaRecord(
            subpoena_type=SubpoenaType.DUCES_TECUM,
            case_number=case_number,
            case_lane=case_lane,
            recipient_name=recipient,
            recipient_address=recipient_address,
            recipient_type=recipient_type,
            documents_requested=list(documents),
            date_issued=_today_iso(),
            date_due=deadline,
            status=SubpoenaStatus.DRAFT,
        )
        self._generated_count += 1
        logger.info(
            "Generated DUCES_TECUM subpoena %s for %s (%d documents)",
            rec.subpoena_id, recipient, len(documents),
        )
        return rec

    # ------------------------------------------------------------------
    def generate_deposition_subpoena(
        self,
        witness: str,
        deposition_date: str,
        location: str,
        *,
        case_number: str = "",
        case_lane: str = "A",
        testimony_topics: Optional[List[str]] = None,
        documents: Optional[List[str]] = None,
    ) -> SubpoenaRecord:
        """Generate a deposition subpoena under MCR 2.306 / MCR 2.305.

        Combines witness attendance with optional document production.
        """
        rec = SubpoenaRecord(
            subpoena_type=SubpoenaType.DEPOSITION,
            case_number=case_number,
            case_lane=case_lane,
            recipient_name=witness,
            hearing_date=deposition_date,
            hearing_location=location,
            testimony_topics=testimony_topics or [],
            documents_requested=documents or [],
            date_issued=_today_iso(),
            status=SubpoenaStatus.DRAFT,
        )
        self._generated_count += 1
        logger.info("Generated DEPOSITION subpoena %s for %s", rec.subpoena_id, witness)
        return rec

    # ------------------------------------------------------------------
    def generate_third_party_records(
        self,
        entity_name: str,
        entity_type: str,
        records_list: List[str],
        *,
        case_number: str = "",
        case_lane: str = "A",
        deadline_days: int = 21,
        entity_address: str = "",
    ) -> SubpoenaRecord:
        """Generate a records-only subpoena for third-party entities.

        Supports: bank, employer, school, CPS, police, medical, insurance.
        MCR 2.305(A)(2) allows subpoena to non-party for records.
        21-day default response window per MCR 2.305(A)(4).
        """
        due = (date.today() + timedelta(days=deadline_days)).isoformat()
        entity_upper = entity_type.upper()

        type_notes = {
            "BANK": "Financial records — include all accounts, statements, and transaction history.",
            "EMPLOYER": "Employment records — pay stubs, HR file, attendance, benefits.",
            "SCHOOL": "Educational records — attendance, disciplinary, IEP/504 if applicable.",
            "CPS": "CPS/DHHS records — complaints, investigations, findings, case notes.",
            "POLICE": "Law enforcement records — incident reports, CAD logs, body-cam footage.",
            "MEDICAL": "Medical records — treatment notes, prescriptions, mental health.",
            "INSURANCE": "Insurance records — policies, claims history, coverage details.",
        }
        note_text = type_notes.get(entity_upper, f"Records subpoena to {entity_type}.")

        rec = SubpoenaRecord(
            subpoena_type=SubpoenaType.RECORDS_ONLY,
            case_number=case_number,
            case_lane=case_lane,
            recipient_name=entity_name,
            recipient_address=entity_address,
            recipient_type=RecipientType.ORGANIZATION,
            documents_requested=list(records_list),
            date_issued=_today_iso(),
            date_due=due,
            status=SubpoenaStatus.DRAFT,
            notes=note_text,
        )
        self._generated_count += 1
        logger.info(
            "Generated RECORDS_ONLY subpoena %s for %s (%s)",
            rec.subpoena_id, entity_name, entity_upper,
        )
        return rec

    # ------------------------------------------------------------------
    def format_subpoena_body(self, rec: SubpoenaRecord) -> str:
        """Render a human-readable subpoena document body.

        The output follows the general Michigan subpoena format but is
        NOT a substitute for an official SCAO form.
        """
        lines: List[str] = []
        lines.append("=" * 72)
        lines.append("STATE OF MICHIGAN")
        lines.append("IN THE CIRCUIT COURT FOR MUSKEGON COUNTY")
        lines.append("")
        lines.append(f"Case No.: {rec.case_number}")
        lines.append(f"Lane:     {rec.case_lane}")
        lines.append("")
        lines.append(f"PIGORS v. WATSON, et al.")
        lines.append(f"Plaintiff: {PLAINTIFF} ({PLAINTIFF_ROLE})")
        lines.append(f"Defendant: {DEFENDANT}")
        lines.append("")

        type_title = {
            SubpoenaType.WITNESS: "SUBPOENA — ATTENDANCE OF WITNESS (MCR 2.506)",
            SubpoenaType.DUCES_TECUM: "SUBPOENA DUCES TECUM (MCR 2.305)",
            SubpoenaType.DEPOSITION: "SUBPOENA FOR DEPOSITION (MCR 2.306 / 2.305)",
            SubpoenaType.TRIAL: "TRIAL SUBPOENA (MCR 2.506)",
            SubpoenaType.HEARING: "HEARING SUBPOENA (MCR 2.506)",
            SubpoenaType.RECORDS_ONLY: "SUBPOENA FOR PRODUCTION OF RECORDS (MCR 2.305)",
        }
        lines.append(type_title.get(rec.subpoena_type, "SUBPOENA"))
        lines.append("=" * 72)
        lines.append("")
        lines.append(f"TO: {rec.recipient_name}")
        if rec.recipient_address:
            lines.append(f"    {rec.recipient_address}")
        lines.append("")
        lines.append("YOU ARE COMMANDED:")
        lines.append("")

        if rec.subpoena_type in (SubpoenaType.WITNESS, SubpoenaType.TRIAL,
                                  SubpoenaType.HEARING):
            lines.append(
                f"  To appear and give testimony at the hearing/trial on "
                f"{rec.hearing_date or '[DATE]'}"
            )
            lines.append(f"  at {rec.hearing_location or '[LOCATION]'}.")
            if rec.testimony_topics:
                lines.append("")
                lines.append("  TOPICS OF TESTIMONY:")
                for i, topic in enumerate(rec.testimony_topics, 1):
                    lines.append(f"    {i}. {topic}")

        if rec.subpoena_type in (SubpoenaType.DUCES_TECUM,
                                  SubpoenaType.RECORDS_ONLY,
                                  SubpoenaType.DEPOSITION):
            lines.append(
                "  To produce the following documents and/or tangible things:"
            )
            lines.append("")
            for i, doc in enumerate(rec.documents_requested, 1):
                lines.append(f"    {i}. {doc}")
            lines.append("")
            if rec.date_due:
                lines.append(f"  RESPONSE DUE BY: {rec.date_due}")
            lines.append("")
            lines.append(
                "  Pursuant to MCR 2.305(A)(4), you may serve written "
                "objections within 14 days"
            )
            lines.append(
                "  of service. Failure to comply may result in sanctions "
                "under MCR 2.313."
            )

        if rec.subpoena_type == SubpoenaType.DEPOSITION:
            lines.append("")
            lines.append(
                f"  AND to appear for deposition on {rec.hearing_date or '[DATE]'}"
            )
            lines.append(f"  at {rec.hearing_location or '[LOCATION]'}.")
            if rec.testimony_topics:
                lines.append("")
                lines.append("  DEPOSITION TOPICS:")
                for i, topic in enumerate(rec.testimony_topics, 1):
                    lines.append(f"    {i}. {topic}")

        lines.append("")
        lines.append("WITNESS FEES:")
        lines.append(
            f"  Witness fee: ${WITNESS_FEE_PER_DAY}/day + mileage at "
            f"${IRS_MILEAGE_RATE}/mile (MCL 600.2552)"
        )
        lines.append("")
        lines.append("PENALTIES FOR NONCOMPLIANCE:")
        lines.append(
            "  Failure to obey this subpoena without adequate excuse may be "
            "deemed contempt"
        )
        lines.append(
            "  of court (MCR 3.606) and subject you to sanctions under "
            "MCR 2.313."
        )
        lines.append("")
        lines.append(f"Issued: {rec.date_issued or _today_iso()}")
        lines.append(f"Subpoena ID: {rec.subpoena_id}")
        lines.append("")
        lines.append(f"Respectfully submitted,")
        lines.append(f"{PLAINTIFF}")
        lines.append(f"{PLAINTIFF_ROLE}")
        lines.append("=" * 72)
        return "\n".join(lines)

    # ------------------------------------------------------------------
    def validate_mcr_compliance(self, rec: SubpoenaRecord) -> List[str]:
        """Return a list of MCR compliance issues (empty = compliant)."""
        issues: List[str] = []

        if not rec.recipient_name.strip():
            issues.append("MCR 2.506: Recipient name is required.")
        if not rec.case_number.strip():
            issues.append("MCR 2.506: Case number is required.")

        if rec.subpoena_type in (SubpoenaType.WITNESS, SubpoenaType.TRIAL,
                                  SubpoenaType.HEARING):
            if not rec.hearing_date:
                issues.append("MCR 2.506: Hearing date is required for witness subpoena.")
            if not rec.hearing_location:
                issues.append("MCR 2.506: Hearing location is required.")

        if rec.subpoena_type in (SubpoenaType.DUCES_TECUM, SubpoenaType.RECORDS_ONLY):
            if not rec.documents_requested:
                issues.append("MCR 2.305: At least one document must be requested.")
            if not rec.date_due:
                issues.append("MCR 2.305(A)(4): Response deadline is required.")

        if rec.subpoena_type == SubpoenaType.DEPOSITION:
            if not rec.hearing_date:
                issues.append("MCR 2.306: Deposition date is required.")
            if not rec.hearing_location:
                issues.append("MCR 2.306: Deposition location is required.")

        if rec.date_due and rec.date_issued:
            try:
                issued = date.fromisoformat(rec.date_issued)
                due = date.fromisoformat(rec.date_due)
                if (due - issued).days < 14:
                    issues.append(
                        "MCR 2.305(A)(4): At least 14 days must be allowed "
                        "for response to document subpoena."
                    )
            except (ValueError, TypeError):
                pass

        return issues

    # ------------------------------------------------------------------
    def get_stats(self) -> dict:
        """Return generator statistics."""
        return {
            "generated_count": self._generated_count,
        }


# ═══════════════════════════════════════════════════════════════════════════
# ServiceTracker
# ═══════════════════════════════════════════════════════════════════════════

class ServiceTracker:
    """Track service of subpoenas in accordance with MCR 2.105.

    Records service attempts, verifies compliance with service rules,
    and calculates fees per MCL 600.2552.
    """

    def __init__(self, conn: Optional[sqlite3.Connection] = None) -> None:
        self._conn = conn
        self._log_count: int = 0

    # ------------------------------------------------------------------
    def _db(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = _get_conn()
            _ensure_schema(self._conn)
        return self._conn

    # ------------------------------------------------------------------
    def record_service(
        self,
        subpoena_id: str,
        method: str,
        service_date: str,
        server_name: str,
        *,
        notes: str = "",
    ) -> str:
        """Record that a subpoena was served.

        Updates the subpoena record and creates a service log entry.

        Parameters
        ----------
        method : str
            One of ServiceMethod values (PERSONAL, CERTIFIED_MAIL, etc.).
        service_date : str
            ISO-8601 date of service.
        server_name : str
            Name of the person who performed service.

        Returns
        -------
        str
            The service log entry ID.
        """
        log_id = str(uuid.uuid4())
        db = self._db()

        db.execute(
            "UPDATE subpoenas SET status = ?, service_method = ?, "
            "service_date = ?, server_name = ?, updated_at = ? "
            "WHERE subpoena_id = ?",
            (SubpoenaStatus.SERVED.value, method, service_date,
             server_name, _now_iso(), subpoena_id),
        )

        db.execute(
            "INSERT INTO subpoena_service_log "
            "(log_id, subpoena_id, service_method, service_date, server_name, notes) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (log_id, subpoena_id, method, service_date, server_name, notes),
        )
        db.commit()
        self._log_count += 1
        logger.info("Recorded service for subpoena %s via %s", subpoena_id, method)
        return log_id

    # ------------------------------------------------------------------
    def track_response(
        self,
        subpoena_id: str,
        response_type: str,
        details: str = "",
    ) -> None:
        """Record a response (compliance, objection, etc.) to a subpoena.

        Parameters
        ----------
        response_type : str
            COMPLIED, OBJECTED, PARTIAL, ACKNOWLEDGED.
        details : str
            Description of the response.
        """
        status_map = {
            "COMPLIED": SubpoenaStatus.COMPLIED,
            "OBJECTED": SubpoenaStatus.OBJECTED,
            "PARTIAL": SubpoenaStatus.NONCOMPLIANT,
            "ACKNOWLEDGED": SubpoenaStatus.ACKNOWLEDGED,
        }
        new_status = status_map.get(
            response_type.upper(), SubpoenaStatus.ACKNOWLEDGED
        )
        db = self._db()
        db.execute(
            "UPDATE subpoenas SET status = ?, response_date = ?, "
            "objection_details = CASE WHEN ? != '' THEN ? ELSE objection_details END, "
            "updated_at = ? WHERE subpoena_id = ?",
            (new_status.value, _today_iso(), details, details, _now_iso(),
             subpoena_id),
        )
        db.commit()
        logger.info("Tracked %s response for subpoena %s", response_type, subpoena_id)

    # ------------------------------------------------------------------
    def check_overdue(self) -> List[SubpoenaRecord]:
        """Return all subpoenas whose due date has passed without compliance."""
        db = self._db()
        rows = db.execute(
            "SELECT * FROM subpoenas "
            "WHERE date_due IS NOT NULL AND date_due < ? "
            "AND status NOT IN (?, ?, ?)",
            (_today_iso(), SubpoenaStatus.COMPLIED.value,
             SubpoenaStatus.QUASHED.value,
             SubpoenaStatus.MOTION_TO_COMPEL.value),
        ).fetchall()
        return [SubpoenaRecord.from_row(r) for r in rows]

    # ------------------------------------------------------------------
    def generate_service_log(self, subpoena_id: Optional[str] = None) -> str:
        """Generate a formatted service log suitable for court filing.

        If *subpoena_id* is ``None`` all service entries are included.
        """
        db = self._db()
        if subpoena_id:
            rows = db.execute(
                "SELECT l.*, s.recipient_name, s.case_number "
                "FROM subpoena_service_log l "
                "JOIN subpoenas s ON l.subpoena_id = s.subpoena_id "
                "WHERE l.subpoena_id = ? ORDER BY l.service_date",
                (subpoena_id,),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT l.*, s.recipient_name, s.case_number "
                "FROM subpoena_service_log l "
                "JOIN subpoenas s ON l.subpoena_id = s.subpoena_id "
                "ORDER BY l.service_date",
            ).fetchall()

        lines: List[str] = []
        lines.append("SERVICE LOG — Pigors v. Watson")
        lines.append("=" * 60)
        for r in rows:
            d = dict(r)
            lines.append(f"Subpoena:  {d.get('subpoena_id', '')}")
            lines.append(f"Recipient: {d.get('recipient_name', '')}")
            lines.append(f"Case No.:  {d.get('case_number', '')}")
            lines.append(f"Method:    {d.get('service_method', '')}")
            lines.append(f"Date:      {d.get('service_date', '')}")
            lines.append(f"Server:    {d.get('server_name', '')}")
            if d.get("notes"):
                lines.append(f"Notes:     {d['notes']}")
            lines.append("-" * 60)

        if not rows:
            lines.append("(no service records found)")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    def calculate_service_fees(
        self,
        method: str,
        distance_miles: float = 0.0,
        days_of_attendance: int = 1,
    ) -> Dict[str, Decimal]:
        """Calculate service and witness fees per MCL 600.2552.

        Returns a breakdown: witness_fee, mileage, service_fee, total.
        """
        witness_fee = WITNESS_FEE_PER_DAY * Decimal(str(days_of_attendance))
        mileage = IRS_MILEAGE_RATE * Decimal(str(distance_miles))

        method_upper = method.upper()
        if method_upper in ("PERSONAL", "PROCESS_SERVER"):
            svc_fee = SERVICE_FEE_PERSONAL
        elif method_upper in ("REGISTERED_MAIL",):
            svc_fee = SERVICE_FEE_REGISTERED
        elif method_upper in ("CERTIFIED_MAIL",):
            svc_fee = SERVICE_FEE_CERTIFIED_MAIL
        else:
            svc_fee = Decimal("0.00")

        total = witness_fee + mileage + svc_fee
        return {
            "witness_fee": witness_fee,
            "mileage": mileage,
            "service_fee": svc_fee,
            "total": total,
        }

    # ------------------------------------------------------------------
    def validate_service(self, subpoena_id: str) -> List[str]:
        """Check if service of a subpoena was properly performed.

        Returns a list of issues (empty = valid service).
        """
        db = self._db()
        row = db.execute(
            "SELECT * FROM subpoenas WHERE subpoena_id = ?",
            (subpoena_id,),
        ).fetchone()
        if not row:
            return [f"Subpoena {subpoena_id} not found."]

        rec = SubpoenaRecord.from_row(row)
        issues: List[str] = []

        if rec.status == SubpoenaStatus.DRAFT:
            issues.append("Subpoena has not been served yet.")
            return issues

        if not rec.service_date:
            issues.append("MCR 2.105: Service date is not recorded.")
        if not rec.server_name:
            issues.append("MCR 2.105: Server name is not recorded.")
        if not rec.service_method:
            issues.append("MCR 2.105: Service method is not recorded.")

        if rec.service_date and rec.hearing_date:
            try:
                svc = date.fromisoformat(rec.service_date)
                hrg = date.fromisoformat(rec.hearing_date)
                if (hrg - svc).days < 2:
                    issues.append(
                        "MCR 2.506(G): Service must be made a reasonable "
                        "time before the hearing (at least 2 days recommended)."
                    )
            except (ValueError, TypeError):
                pass

        return issues

    # ------------------------------------------------------------------
    def get_stats(self) -> dict:
        """Return service tracker statistics."""
        return {"log_entries_created": self._log_count}


# ═══════════════════════════════════════════════════════════════════════════
# ComplianceEnforcer
# ═══════════════════════════════════════════════════════════════════════════

class ComplianceEnforcer:
    """Prepare enforcement motions for subpoena noncompliance.

    Covers MCR 2.313 (motion to compel / sanctions), MCR 3.606 (contempt),
    and show-cause proceedings.
    """

    def __init__(self, conn: Optional[sqlite3.Connection] = None) -> None:
        self._conn = conn
        self._actions_count: int = 0

    def _db(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = _get_conn()
            _ensure_schema(self._conn)
        return self._conn

    # ------------------------------------------------------------------
    def prepare_motion_to_compel(self, subpoena_id: str) -> Dict[str, Any]:
        """Draft a motion to compel compliance under MCR 2.313.

        Returns a dict with motion_text, legal_basis, and enforcement record.
        """
        db = self._db()
        row = db.execute(
            "SELECT * FROM subpoenas WHERE subpoena_id = ?",
            (subpoena_id,),
        ).fetchone()
        if not row:
            return {"error": f"Subpoena {subpoena_id} not found."}

        rec = SubpoenaRecord.from_row(row)
        lines: List[str] = []
        lines.append("STATE OF MICHIGAN")
        lines.append("IN THE CIRCUIT COURT FOR MUSKEGON COUNTY")
        lines.append("")
        lines.append(f"Case No.: {rec.case_number}")
        lines.append(f"PIGORS v. WATSON, et al.")
        lines.append("")
        lines.append("MOTION TO COMPEL COMPLIANCE WITH SUBPOENA")
        lines.append("(MCR 2.313)")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"NOW COMES Plaintiff, {PLAINTIFF}, appearing pro se,")
        lines.append("and respectfully moves this Court for an Order compelling")
        lines.append(f"{rec.recipient_name} to comply with the subpoena")
        lines.append(f"(ID: {rec.subpoena_id}) issued on {rec.date_issued},")
        lines.append("and in support states:")
        lines.append("")
        lines.append("FACTS:")
        lines.append(f"1. A subpoena ({rec.subpoena_type.value}) was issued on {rec.date_issued}.")
        lines.append(f"2. The subpoena was served on {rec.service_date or '[DATE]'}.")
        lines.append(f"3. Response was due by {rec.date_due or '[DATE]'}.")
        lines.append(f"4. Current status: {rec.status.value}.")
        if rec.objection_details:
            lines.append(f"5. Objection details: {rec.objection_details}")
        lines.append("")
        lines.append("LEGAL BASIS:")
        lines.append(
            "MCR 2.313(A) authorises a motion to compel discovery when a "
            "person fails to comply with a subpoena or discovery request."
        )
        lines.append(
            "MCR 2.313(B) permits the court to impose sanctions, including "
            "reasonable expenses and attorney fees."
        )
        lines.append("")
        lines.append("RELIEF REQUESTED:")
        lines.append(
            f"1. An Order compelling {rec.recipient_name} to comply with the subpoena."
        )
        lines.append(
            "2. Reasonable costs and fees incurred in bringing this motion."
        )
        lines.append("")
        lines.append(f"Respectfully submitted,")
        lines.append(f"{PLAINTIFF}")
        lines.append(f"{PLAINTIFF_ROLE}")
        lines.append(f"Date: {_today_iso()}")

        motion_text = "\n".join(lines)

        enforcement_id = str(uuid.uuid4())
        db.execute(
            "INSERT INTO subpoena_enforcement "
            "(enforcement_id, subpoena_id, action_type, motion_text, status) "
            "VALUES (?, ?, ?, ?, ?)",
            (enforcement_id, subpoena_id, "MOTION_TO_COMPEL",
             motion_text, "PENDING"),
        )
        db.execute(
            "UPDATE subpoenas SET status = ?, updated_at = ? "
            "WHERE subpoena_id = ?",
            (SubpoenaStatus.MOTION_TO_COMPEL.value, _now_iso(), subpoena_id),
        )
        db.commit()
        self._actions_count += 1

        return {
            "enforcement_id": enforcement_id,
            "subpoena_id": subpoena_id,
            "action_type": "MOTION_TO_COMPEL",
            "motion_text": motion_text,
            "legal_basis": ["MCR 2.313(A)", "MCR 2.313(B)"],
        }

    # ------------------------------------------------------------------
    def prepare_contempt_motion(self, subpoena_id: str) -> Dict[str, Any]:
        """Draft a contempt motion under MCR 3.606.

        Contempt is appropriate when a party wilfully disobeys a court
        order (which includes a properly served subpoena).
        """
        db = self._db()
        row = db.execute(
            "SELECT * FROM subpoenas WHERE subpoena_id = ?",
            (subpoena_id,),
        ).fetchone()
        if not row:
            return {"error": f"Subpoena {subpoena_id} not found."}

        rec = SubpoenaRecord.from_row(row)
        lines: List[str] = []
        lines.append("STATE OF MICHIGAN")
        lines.append("IN THE CIRCUIT COURT FOR MUSKEGON COUNTY")
        lines.append("")
        lines.append(f"Case No.: {rec.case_number}")
        lines.append(f"PIGORS v. WATSON, et al.")
        lines.append("")
        lines.append("MOTION FOR CONTEMPT OF COURT")
        lines.append("(MCR 3.606)")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"NOW COMES Plaintiff, {PLAINTIFF}, appearing pro se,")
        lines.append("and respectfully moves this Court to find")
        lines.append(f"{rec.recipient_name} in contempt of court for wilful")
        lines.append("failure to comply with a lawfully issued subpoena,")
        lines.append("and in support thereof states:")
        lines.append("")
        lines.append("FACTS:")
        lines.append(f"1. A subpoena was lawfully issued on {rec.date_issued}.")
        lines.append(f"2. Service was properly effected on {rec.service_date or '[DATE]'}.")
        lines.append(f"3. The subpoena commanded compliance by {rec.date_due or '[DATE]'}.")
        lines.append(f"4. The recipient has failed/refused to comply.")
        lines.append(f"5. Current status: {rec.status.value}.")
        lines.append("")
        lines.append("LEGAL BASIS:")
        lines.append(
            "MCR 3.606(A): A court may find a person in contempt for "
            "wilful disobedience of a lawful court order."
        )
        lines.append(
            "MCL 600.1701: Courts have inherent contempt power to enforce "
            "compliance with lawful process."
        )
        lines.append("")
        lines.append("RELIEF REQUESTED:")
        lines.append(
            f"1. A finding that {rec.recipient_name} is in contempt of court."
        )
        lines.append("2. Appropriate sanctions including fines and costs.")
        lines.append("3. An Order compelling immediate compliance.")
        lines.append("")
        lines.append(f"Respectfully submitted,")
        lines.append(f"{PLAINTIFF}")
        lines.append(f"{PLAINTIFF_ROLE}")
        lines.append(f"Date: {_today_iso()}")

        motion_text = "\n".join(lines)

        enforcement_id = str(uuid.uuid4())
        db.execute(
            "INSERT INTO subpoena_enforcement "
            "(enforcement_id, subpoena_id, action_type, motion_text, status) "
            "VALUES (?, ?, ?, ?, ?)",
            (enforcement_id, subpoena_id, "CONTEMPT", motion_text, "PENDING"),
        )
        db.commit()
        self._actions_count += 1

        return {
            "enforcement_id": enforcement_id,
            "subpoena_id": subpoena_id,
            "action_type": "CONTEMPT",
            "motion_text": motion_text,
            "legal_basis": ["MCR 3.606(A)", "MCL 600.1701"],
        }

    # ------------------------------------------------------------------
    def calculate_sanctions(
        self,
        noncompliance_type: str,
        *,
        attorney_hours: Decimal = Decimal("0"),
        hourly_rate: Decimal = Decimal("250.00"),
        filing_fees: Decimal = Decimal("0.00"),
        other_costs: Decimal = Decimal("0.00"),
    ) -> Dict[str, Decimal]:
        """Calculate potential sanctions for noncompliance.

        MCR 2.313(B) allows recovery of reasonable expenses including
        attorney fees (here: pro-se equivalent costs).
        """
        attorney_cost = attorney_hours * hourly_rate
        base_sanctions: Dict[str, Decimal] = {
            "FAILURE_TO_APPEAR": Decimal("500.00"),
            "FAILURE_TO_PRODUCE": Decimal("250.00"),
            "LATE_PRODUCTION": Decimal("100.00"),
            "INCOMPLETE_PRODUCTION": Decimal("150.00"),
            "WILFUL_DESTRUCTION": Decimal("5000.00"),
        }
        base = base_sanctions.get(
            noncompliance_type.upper(), Decimal("250.00")
        )
        total = base + attorney_cost + filing_fees + other_costs
        return {
            "base_sanction": base,
            "attorney_equivalent_cost": attorney_cost,
            "filing_fees": filing_fees,
            "other_costs": other_costs,
            "total_sanctions": total,
            "authority": "MCR 2.313(B)",
        }

    # ------------------------------------------------------------------
    def draft_show_cause_order(self, subpoena_id: str) -> Dict[str, Any]:
        """Draft a request for an Order to Show Cause for noncompliance."""
        db = self._db()
        row = db.execute(
            "SELECT * FROM subpoenas WHERE subpoena_id = ?",
            (subpoena_id,),
        ).fetchone()
        if not row:
            return {"error": f"Subpoena {subpoena_id} not found."}

        rec = SubpoenaRecord.from_row(row)
        lines: List[str] = []
        lines.append("STATE OF MICHIGAN")
        lines.append("IN THE CIRCUIT COURT FOR MUSKEGON COUNTY")
        lines.append("")
        lines.append(f"Case No.: {rec.case_number}")
        lines.append(f"PIGORS v. WATSON, et al.")
        lines.append("")
        lines.append("REQUEST FOR ORDER TO SHOW CAUSE")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"Plaintiff, {PLAINTIFF}, requests that this Court issue")
        lines.append(f"an Order requiring {rec.recipient_name} to appear and")
        lines.append("show cause why they should not be held in contempt for")
        lines.append("failure to comply with a lawfully issued subpoena.")
        lines.append("")
        lines.append(f"Subpoena issued: {rec.date_issued}")
        lines.append(f"Service date: {rec.service_date or 'N/A'}")
        lines.append(f"Response due: {rec.date_due or 'N/A'}")
        lines.append(f"Status: {rec.status.value}")
        lines.append("")
        lines.append(f"Respectfully submitted,")
        lines.append(f"{PLAINTIFF}")
        lines.append(f"{PLAINTIFF_ROLE}")
        lines.append(f"Date: {_today_iso()}")

        text = "\n".join(lines)

        enforcement_id = str(uuid.uuid4())
        db.execute(
            "INSERT INTO subpoena_enforcement "
            "(enforcement_id, subpoena_id, action_type, motion_text, status) "
            "VALUES (?, ?, ?, ?, ?)",
            (enforcement_id, subpoena_id, "SHOW_CAUSE", text, "PENDING"),
        )
        db.commit()
        self._actions_count += 1

        return {
            "enforcement_id": enforcement_id,
            "subpoena_id": subpoena_id,
            "action_type": "SHOW_CAUSE",
            "text": text,
        }

    # ------------------------------------------------------------------
    def get_stats(self) -> dict:
        """Return enforcer statistics."""
        return {"enforcement_actions_created": self._actions_count}


# ═══════════════════════════════════════════════════════════════════════════
# SubpoenaEngine  (main orchestrator)
# ═══════════════════════════════════════════════════════════════════════════

class SubpoenaEngine:
    """Top-level orchestrator for all subpoena operations.

    Provides a single-entry-point API for creating, tracking, enforcing,
    and reporting on subpoenas across all case lanes.
    """

    VERSION = "1.0.0"

    def __init__(
        self,
        db_path: Optional[pathlib.Path] = None,
    ) -> None:
        self._db_path = db_path or _DB_PATH
        self._conn: Optional[sqlite3.Connection] = None
        self.generator = SubpoenaGenerator()
        self.service_tracker: Optional[ServiceTracker] = None
        self.enforcer: Optional[ComplianceEnforcer] = None
        self._initialised = False

    # ------------------------------------------------------------------
    def _init_db(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = _get_conn(self._db_path)
            _ensure_schema(self._conn)
            self.service_tracker = ServiceTracker(self._conn)
            self.enforcer = ComplianceEnforcer(self._conn)
        self._initialised = True
        return self._conn

    # ------------------------------------------------------------------
    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    # ------------------------------------------------------------------
    def create_subpoena(
        self,
        subpoena_type: SubpoenaType,
        recipient: str,
        details: Dict[str, Any],
    ) -> SubpoenaRecord:
        """Create a subpoena and persist to DB.

        Parameters
        ----------
        subpoena_type : SubpoenaType
        recipient : str
            Full name of recipient.
        details : dict
            Type-dependent extras: documents, hearing_date, location, etc.

        Returns
        -------
        SubpoenaRecord
        """
        db = self._init_db()

        case_number = details.get("case_number", "")
        case_lane = details.get("case_lane", "A")

        if subpoena_type == SubpoenaType.WITNESS:
            rec = self.generator.generate_witness_subpoena(
                recipient=recipient,
                hearing_date=details.get("hearing_date", ""),
                court=details.get("court", "14th Circuit Court, Muskegon County"),
                case_number=case_number,
                case_lane=case_lane,
                hearing_location=details.get("hearing_location", ""),
                testimony_topics=details.get("testimony_topics"),
            )
        elif subpoena_type == SubpoenaType.DUCES_TECUM:
            rec = self.generator.generate_duces_tecum(
                recipient=recipient,
                documents=details.get("documents", []),
                deadline=details.get("deadline", ""),
                case_number=case_number,
                case_lane=case_lane,
                recipient_type=RecipientType(
                    details.get("recipient_type", "INDIVIDUAL")
                ),
                recipient_address=details.get("recipient_address", ""),
            )
        elif subpoena_type == SubpoenaType.DEPOSITION:
            rec = self.generator.generate_deposition_subpoena(
                witness=recipient,
                deposition_date=details.get("deposition_date", ""),
                location=details.get("location", ""),
                case_number=case_number,
                case_lane=case_lane,
                testimony_topics=details.get("testimony_topics"),
                documents=details.get("documents"),
            )
        elif subpoena_type == SubpoenaType.RECORDS_ONLY:
            rec = self.generator.generate_third_party_records(
                entity_name=recipient,
                entity_type=details.get("entity_type", "ORGANIZATION"),
                records_list=details.get("records_list", []),
                case_number=case_number,
                case_lane=case_lane,
                deadline_days=details.get("deadline_days", 21),
                entity_address=details.get("entity_address", ""),
            )
        else:
            rec = SubpoenaRecord(
                subpoena_type=subpoena_type,
                case_number=case_number,
                case_lane=case_lane,
                recipient_name=recipient,
                date_issued=_today_iso(),
                **{k: v for k, v in details.items()
                   if k in ("hearing_date", "hearing_location",
                            "documents_requested", "testimony_topics",
                            "date_due")},
            )

        self._persist_record(db, rec)
        return rec

    # ------------------------------------------------------------------
    def _persist_record(
        self, conn: sqlite3.Connection, rec: SubpoenaRecord,
    ) -> None:
        conn.execute(
            "INSERT OR REPLACE INTO subpoenas "
            "(subpoena_id, subpoena_type, case_number, case_lane, "
            "recipient_name, recipient_address, recipient_type, "
            "documents_requested, testimony_topics, date_issued, "
            "date_due, hearing_date, hearing_location, status, "
            "service_method, service_date, server_name, response_date, "
            "objection_details, notes, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                rec.subpoena_id,
                rec.subpoena_type.value,
                rec.case_number,
                rec.case_lane,
                rec.recipient_name,
                rec.recipient_address,
                rec.recipient_type.value,
                json.dumps(rec.documents_requested),
                json.dumps(rec.testimony_topics),
                rec.date_issued,
                rec.date_due,
                rec.hearing_date,
                rec.hearing_location,
                rec.status.value,
                rec.service_method,
                rec.service_date,
                rec.server_name,
                rec.response_date,
                rec.objection_details,
                rec.notes,
                _now_iso(),
            ),
        )
        conn.commit()

    # ------------------------------------------------------------------
    def track_all_subpoenas(
        self, *, lane: Optional[str] = None,
    ) -> List[SubpoenaRecord]:
        """Return all tracked subpoenas, optionally filtered by lane."""
        db = self._init_db()
        if lane:
            rows = db.execute(
                "SELECT * FROM subpoenas WHERE case_lane = ? "
                "ORDER BY date_issued DESC",
                (lane,),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM subpoenas ORDER BY date_issued DESC",
            ).fetchall()
        return [SubpoenaRecord.from_row(r) for r in rows]

    # ------------------------------------------------------------------
    def get_overdue_subpoenas(self) -> List[SubpoenaRecord]:
        """Return subpoenas that are past due and not yet complied."""
        assert self.service_tracker is not None or self._init_db()
        return self.service_tracker.check_overdue()  # type: ignore[union-attr]

    # ------------------------------------------------------------------
    def enforce_noncompliance(
        self,
        subpoena_id: str,
        *,
        action: str = "MOTION_TO_COMPEL",
    ) -> Dict[str, Any]:
        """Initiate an enforcement action for a noncompliant subpoena.

        Parameters
        ----------
        action : str
            MOTION_TO_COMPEL, CONTEMPT, or SHOW_CAUSE.
        """
        self._init_db()
        assert self.enforcer is not None

        if action.upper() == "CONTEMPT":
            return self.enforcer.prepare_contempt_motion(subpoena_id)
        if action.upper() == "SHOW_CAUSE":
            return self.enforcer.draft_show_cause_order(subpoena_id)
        return self.enforcer.prepare_motion_to_compel(subpoena_id)

    # ------------------------------------------------------------------
    def generate_subpoena_report(self) -> str:
        """Generate a comprehensive text report of all subpoenas."""
        records = self.track_all_subpoenas()
        lines: List[str] = []
        lines.append("SUBPOENA STATUS REPORT — Pigors v. Watson")
        lines.append(f"Generated: {_now_iso()}")
        lines.append("=" * 72)
        lines.append(f"Total subpoenas: {len(records)}")

        by_status: Dict[str, int] = {}
        by_lane: Dict[str, int] = {}
        overdue_count = 0
        for r in records:
            by_status[r.status.value] = by_status.get(r.status.value, 0) + 1
            by_lane[r.case_lane] = by_lane.get(r.case_lane, 0) + 1
            if r.is_overdue():
                overdue_count += 1

        lines.append(f"Overdue: {overdue_count}")
        lines.append("")
        lines.append("BY STATUS:")
        for s, c in sorted(by_status.items()):
            lines.append(f"  {s}: {c}")
        lines.append("")
        lines.append("BY LANE:")
        for ln, c in sorted(by_lane.items()):
            lane_info = CASE_LANES.get(ln, {})
            lines.append(
                f"  Lane {ln} ({lane_info.get('subject', '')}): {c}"
            )
        lines.append("")

        lines.append("DETAIL:")
        lines.append("-" * 72)
        for r in records:
            lines.append(f"ID:        {r.subpoena_id}")
            lines.append(f"Type:      {r.subpoena_type.value}")
            lines.append(f"Recipient: {r.recipient_name}")
            lines.append(f"Case:      {r.case_number} (Lane {r.case_lane})")
            lines.append(f"Status:    {r.status.value}")
            lines.append(f"Issued:    {r.date_issued or 'N/A'}")
            lines.append(f"Due:       {r.date_due or 'N/A'}")
            days = r.days_until_due()
            if days is not None:
                label = "OVERDUE" if days < 0 else "remaining"
                lines.append(f"Days:      {abs(days)} {label}")
            lines.append("-" * 72)

        return "\n".join(lines)

    # ------------------------------------------------------------------
    def get_stats(self) -> dict:
        """Return engine-wide statistics."""
        db = self._init_db()
        row = db.execute(
            "SELECT "
            "  (SELECT COUNT(*) FROM subpoenas) AS total, "
            "  (SELECT COUNT(*) FROM subpoenas WHERE status = 'DRAFT') AS draft, "
            "  (SELECT COUNT(*) FROM subpoenas WHERE status = 'ISSUED') AS issued, "
            "  (SELECT COUNT(*) FROM subpoenas WHERE status = 'SERVED') AS served, "
            "  (SELECT COUNT(*) FROM subpoenas WHERE status = 'COMPLIED') AS complied, "
            "  (SELECT COUNT(*) FROM subpoenas WHERE status = 'NONCOMPLIANT') AS noncompliant, "
            "  (SELECT COUNT(*) FROM subpoenas WHERE status = 'OBJECTED') AS objected, "
            "  (SELECT COUNT(*) FROM subpoenas WHERE status = 'MOTION_TO_COMPEL') AS mtc, "
            "  (SELECT COUNT(*) FROM subpoena_service_log) AS service_logs, "
            "  (SELECT COUNT(*) FROM subpoena_enforcement) AS enforcement_actions"
        ).fetchone()
        d = dict(row)
        d["engine_version"] = self.VERSION
        d["generator"] = self.generator.get_stats()
        if self.service_tracker:
            d["service_tracker"] = self.service_tracker.get_stats()
        if self.enforcer:
            d["enforcer"] = self.enforcer.get_stats()
        return d


# ═══════════════════════════════════════════════════════════════════════════
# CLI / Demo
# ═══════════════════════════════════════════════════════════════════════════

def _cli_main() -> int:
    """Minimal CLI for subpoena engine operations."""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="SubpoenaEngine — Michigan subpoena management",
    )
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("stats", help="Print engine statistics")
    sub.add_parser("report", help="Print full subpoena report")
    sub.add_parser("overdue", help="List overdue subpoenas")
    sub.add_parser("demo", help="Run demo with sample data")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 0

    engine = SubpoenaEngine()
    try:
        if args.command == "stats":
            stats = engine.get_stats()
            print(json.dumps(stats, indent=2, default=str))

        elif args.command == "report":
            print(engine.generate_subpoena_report())

        elif args.command == "overdue":
            overdue = engine.get_overdue_subpoenas()
            if not overdue:
                print("No overdue subpoenas.")
            else:
                for r in overdue:
                    print(
                        f"  {r.subpoena_id[:12]}… | {r.recipient_name} | "
                        f"Due: {r.date_due} | Status: {r.status.value}"
                    )

        elif args.command == "demo":
            _run_demo(engine)
    finally:
        engine.close()

    return 0


def _run_demo(engine: SubpoenaEngine) -> None:
    """Demonstrate subpoena creation, tracking, and enforcement."""
    print("=" * 60)
    print("SubpoenaEngine Demo — Pigors v. Watson")
    print("=" * 60)

    # 1. Witness subpoena
    rec1 = engine.create_subpoena(
        SubpoenaType.WITNESS,
        "Jane Doe, LCSW",
        {
            "case_number": "2024-001507-DC",
            "case_lane": "A",
            "hearing_date": (date.today() + timedelta(days=30)).isoformat(),
            "hearing_location": "14th Circuit Court, Muskegon County",
            "testimony_topics": [
                "Observations of parenting by both parties",
                "Recommendations regarding custody",
            ],
        },
    )
    print(f"\n[1] Created WITNESS subpoena: {rec1.subpoena_id[:12]}…")
    print(f"    Recipient: {rec1.recipient_name}")
    body = engine.generator.format_subpoena_body(rec1)
    print(f"    Body length: {len(body)} chars")

    issues = engine.generator.validate_mcr_compliance(rec1)
    print(f"    MCR compliance issues: {len(issues)}")
    for iss in issues:
        print(f"      - {iss}")

    # 2. Records subpoena (bank)
    rec2 = engine.create_subpoena(
        SubpoenaType.RECORDS_ONLY,
        "First National Bank",
        {
            "case_number": "2024-001507-DC",
            "case_lane": "A",
            "entity_type": "BANK",
            "records_list": [
                "All account statements for Emily A. Watson (2022-2025)",
                "Wire transfer records exceeding $500",
                "Safe deposit box access logs",
            ],
            "deadline_days": 21,
        },
    )
    print(f"\n[2] Created RECORDS_ONLY subpoena: {rec2.subpoena_id[:12]}…")
    print(f"    Recipient: {rec2.recipient_name}")

    # 3. Duces tecum
    due_date = (date.today() + timedelta(days=28)).isoformat()
    rec3 = engine.create_subpoena(
        SubpoenaType.DUCES_TECUM,
        DEFENDANT,
        {
            "case_number": "2024-001507-DC",
            "case_lane": "A",
            "documents": [
                "All text messages referencing L.D.W. (2023-present)",
                "Employment records and pay stubs (2022-present)",
                "Social media posts referencing custody or parenting",
            ],
            "deadline": due_date,
        },
    )
    print(f"\n[3] Created DUCES_TECUM subpoena: {rec3.subpoena_id[:12]}…")

    # 4. Service fees
    assert engine.service_tracker is not None
    fees = engine.service_tracker.calculate_service_fees(
        method="PERSONAL", distance_miles=25.0, days_of_attendance=2,
    )
    print(f"\n[4] Service fee calculation (PERSONAL, 25 mi, 2 days):")
    for k, v in fees.items():
        print(f"    {k}: ${v}")

    # 5. Sanctions
    assert engine.enforcer is not None
    sanctions = engine.enforcer.calculate_sanctions(
        "FAILURE_TO_PRODUCE",
        filing_fees=Decimal("20.00"),
    )
    print(f"\n[5] Sanctions (FAILURE_TO_PRODUCE):")
    for k, v in sanctions.items():
        print(f"    {k}: {v}")

    # 6. Report
    print(f"\n[6] Subpoena report:")
    report = engine.generate_subpoena_report()
    for line in report.split("\n")[:25]:
        print(f"    {line}")
    print("    …(truncated)")

    # 7. Stats
    stats = engine.get_stats()
    print(f"\n[7] Engine stats:")
    print(json.dumps(stats, indent=2, default=str))

    print("\nDemo complete.")


if __name__ == "__main__":
    sys.exit(_cli_main())
