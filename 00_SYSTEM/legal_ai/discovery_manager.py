# -*- coding: utf-8 -*-
"""
Discovery Manager — LitigationOS Legal AI Subsystem
=====================================================
Comprehensive discovery tracking and management engine for Michigan
family-law litigation.  Tracks interrogatories, production requests,
admission requests, depositions, subpoenas, and inspections.  Calculates
response deadlines per MCR 2.309(B) (28 days), drafts responses and
objections, generates privilege logs, and prepares motions to compel
under MCR 2.313.

Case Context
------------
    Plaintiff:  Andrew James Pigors (Pro Se)
    Defendant:  Emily A. Watson
    Child:      L.D.W. (per MCR 8.119(H)) — Male
    Judge:      Hon. Jenny L. McNeill — 14th Circuit Court
    Cases:      2024-001507-DC, 2025-002760-CZ, 2023-5907-PP, COA 366810
    Lanes:      ALL (A through F)

Michigan Rules
--------------
    MCR 2.301 – General Discovery Provisions
    MCR 2.302 – Scope of Discovery
    MCR 2.309 – Interrogatories (28-day response window)
    MCR 2.310 – Requests for Production (28-day response window)
    MCR 2.312 – Requests for Admission (28-day response window)
    MCR 2.313 – Sanctions / Motion to Compel
    MCR 2.314 – Discovery Limitations and Protective Orders

Usage::

    from legal_ai.discovery_manager import DiscoveryManager

    dm = DiscoveryManager()
    dm.create_request(...)
    report = dm.generate_discovery_report()

Zero external dependencies.  CPU-first.  Local-only.
"""
from __future__ import annotations

import json
import logging
import sqlite3
import sys
import textwrap
import uuid
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger("legal_ai.discovery_manager")

# ---------------------------------------------------------------------------
# Path resolution  (never set CWD to repo root — shadow-module risk)
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[1]
_DB_PATH = _REPO / "litigation_context.db"

# ---------------------------------------------------------------------------
# Case constants
# ---------------------------------------------------------------------------
_PLAINTIFF = "Andrew James Pigors"
_DEFENDANT = "Emily A. Watson"
_CHILD_INITIALS = "L.D.W."
_JUDGE = "Hon. Jenny L. McNeill"
_COURT = "14th Circuit Court"

LANE_CASES: Dict[str, str] = {
    "A": "2024-001507-DC",
    "B": "2025-002760-CZ",
    "C": "Convergence",
    "D": "2023-5907-PP",
    "E": "JTC / Misconduct",
    "F": "COA 366810",
}

# ---------------------------------------------------------------------------
# Michigan discovery deadlines (days from service)
# ---------------------------------------------------------------------------
_MCR_2309_RESPONSE_DAYS = 28       # Interrogatories
_MCR_2310_RESPONSE_DAYS = 28       # Production requests
_MCR_2312_RESPONSE_DAYS = 28       # Admission requests
_DEPOSITION_NOTICE_DAYS = 14       # Reasonable notice for depositions
_SUBPOENA_NOTICE_DAYS = 14         # Subpoena compliance period
_MOTION_TO_COMPEL_DAYS = 21        # Time after overdue before MTC
_ADDITIONAL_MAIL_SERVICE_DAYS = 3  # MCR 2.107(C)(3) additional time for mail

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class DiscoveryType(str, Enum):
    """Categories of discovery under Michigan Court Rules."""

    INTERROGATORY = "interrogatory"
    REQUEST_PRODUCTION = "request_production"
    REQUEST_ADMISSION = "request_admission"
    DEPOSITION_NOTICE = "deposition_notice"
    SUBPOENA = "subpoena"
    INSPECTION = "inspection"

    @property
    def mcr_reference(self) -> str:
        _refs = {
            "interrogatory": "MCR 2.309",
            "request_production": "MCR 2.310",
            "request_admission": "MCR 2.312",
            "deposition_notice": "MCR 2.306",
            "subpoena": "MCR 2.305",
            "inspection": "MCR 2.310(B)",
        }
        return _refs.get(self.value, "MCR 2.301")

    @property
    def response_days(self) -> int:
        _days = {
            "interrogatory": _MCR_2309_RESPONSE_DAYS,
            "request_production": _MCR_2310_RESPONSE_DAYS,
            "request_admission": _MCR_2312_RESPONSE_DAYS,
            "deposition_notice": _DEPOSITION_NOTICE_DAYS,
            "subpoena": _SUBPOENA_NOTICE_DAYS,
            "inspection": _MCR_2310_RESPONSE_DAYS,
        }
        return _days.get(self.value, 28)


class DiscoveryStatus(str, Enum):
    """Lifecycle statuses for a discovery request."""

    DRAFT = "draft"
    SERVED = "served"
    RESPONSE_DUE = "response_due"
    RESPONDED = "responded"
    OBJECTED = "objected"
    OVERDUE = "overdue"
    MOTION_TO_COMPEL = "motion_to_compel"
    COMPLETED = "completed"


class ObjectionType(str, Enum):
    """Standard discovery objection categories."""

    VAGUE_AND_AMBIGUOUS = "vague_and_ambiguous"
    OVERLY_BROAD = "overly_broad"
    UNDULY_BURDENSOME = "unduly_burdensome"
    PRIVILEGE = "privilege"
    WORK_PRODUCT = "work_product"
    NOT_RELEVANT = "not_relevant"
    NOT_PROPORTIONAL = "not_proportional"
    ALREADY_PROVIDED = "already_provided"
    SEEKS_LEGAL_CONCLUSION = "seeks_legal_conclusion"
    COMPOUND = "compound"

    @property
    def template(self) -> str:
        _templates: Dict[str, str] = {
            "vague_and_ambiguous": (
                "Plaintiff objects to this request as vague, ambiguous, and "
                "incapable of reasoned response in its current form."
            ),
            "overly_broad": (
                "Plaintiff objects to this request as overly broad in scope, "
                "seeking information beyond the issues in this matter."
            ),
            "unduly_burdensome": (
                "Plaintiff objects as unduly burdensome, requiring an "
                "unreasonable expenditure of time and resources."
            ),
            "privilege": (
                "Plaintiff objects on the ground of privilege, including but "
                "not limited to attorney-client privilege, as applicable."
            ),
            "work_product": (
                "Plaintiff objects that this request seeks attorney work "
                "product protected under MCR 2.302(B)(3)."
            ),
            "not_relevant": (
                "Plaintiff objects as the information sought is not relevant "
                "to any claim or defense in this matter per MCR 2.302(B)."
            ),
            "not_proportional": (
                "Plaintiff objects as the burden of producing the requested "
                "information outweighs its potential relevance per MCR 2.302(B)."
            ),
            "already_provided": (
                "Plaintiff objects that the information requested has already "
                "been provided in prior discovery responses."
            ),
            "seeks_legal_conclusion": (
                "Plaintiff objects that this interrogatory calls for a "
                "legal conclusion rather than factual information."
            ),
            "compound": (
                "Plaintiff objects that this request is compound, containing "
                "multiple discrete sub-parts that should be separately stated."
            ),
        }
        return _templates.get(self.value, "Objection noted.")


class ServiceMethod(str, Enum):
    """Service methods under MCR 2.107."""

    PERSONAL = "personal"
    MAIL = "mail"
    EMAIL = "email"
    FAX = "fax"
    COURTHOUSE_BOX = "courthouse_box"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class DiscoveryItem:
    """A single numbered item within a discovery request."""

    item_number: int = 0
    text: str = ""
    response: str = ""
    objections: List[ObjectionType] = field(default_factory=list)
    is_answered: bool = False

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["objections"] = [o.value for o in self.objections]
        return d


@dataclass
class DiscoveryRequest:
    """A complete discovery request (set of interrogatories, RFP, etc.)."""

    request_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    discovery_type: DiscoveryType = DiscoveryType.INTERROGATORY
    case_number: str = ""
    lane: str = ""
    propounding_party: str = _PLAINTIFF
    responding_party: str = _DEFENDANT
    set_number: int = 1
    date_served: str = ""
    date_due: str = ""
    service_method: ServiceMethod = ServiceMethod.MAIL
    items: List[DiscoveryItem] = field(default_factory=list)
    status: DiscoveryStatus = DiscoveryStatus.DRAFT
    response_text: str = ""
    objections: List[str] = field(default_factory=list)
    notes: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "discovery_type": self.discovery_type.value,
            "case_number": self.case_number,
            "lane": self.lane,
            "propounding_party": self.propounding_party,
            "responding_party": self.responding_party,
            "set_number": self.set_number,
            "date_served": self.date_served,
            "date_due": self.date_due,
            "service_method": self.service_method.value,
            "items": [i.to_dict() for i in self.items],
            "status": self.status.value,
            "response_text": self.response_text,
            "objections": self.objections,
            "notes": self.notes,
            "created_at": self.created_at,
        }


@dataclass
class PrivilegeLogEntry:
    """A single entry in a privilege log."""

    entry_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    document_description: str = ""
    date_of_document: str = ""
    author: str = ""
    recipients: List[str] = field(default_factory=list)
    privilege_type: str = ""
    basis: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MeetAndConferRecord:
    """Documentation of a meet-and-confer attempt before MTC."""

    record_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    date: str = ""
    method: str = ""
    participants: List[str] = field(default_factory=list)
    issues_discussed: List[str] = field(default_factory=list)
    outcome: str = ""
    good_faith_effort: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MotionToCompel:
    """A motion to compel under MCR 2.313."""

    motion_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    case_number: str = ""
    lane: str = ""
    discovery_request_ids: List[str] = field(default_factory=list)
    overdue_items: List[str] = field(default_factory=list)
    meet_and_confer: Optional[MeetAndConferRecord] = None
    sanctions_requested: bool = False
    sanctions_amount: float = 0.0
    sanctions_basis: str = ""
    filing_date: str = ""
    hearing_date: str = ""
    mcr_authority: str = "MCR 2.313(A)"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["meet_and_confer"] = (
            self.meet_and_confer.to_dict() if self.meet_and_confer else None
        )
        return d


@dataclass
class DiscoveryReport:
    """Summary report of all discovery activity."""

    report_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    total_requests: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)
    by_status: Dict[str, int] = field(default_factory=dict)
    overdue_count: int = 0
    overdue_requests: List[str] = field(default_factory=list)
    upcoming_deadlines: List[Dict[str, str]] = field(default_factory=list)
    motions_to_compel: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# DiscoveryCalendar
# ---------------------------------------------------------------------------


class DiscoveryCalendar:
    """Calculates and tracks discovery deadlines."""

    @staticmethod
    def calculate_due_date(
        date_served: str,
        discovery_type: DiscoveryType,
        service_method: ServiceMethod = ServiceMethod.MAIL,
    ) -> str:
        """Calculate response due date per MCR."""
        try:
            served = datetime.strptime(date_served, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            logger.warning("Invalid date_served: %s", date_served)
            return ""

        base_days = discovery_type.response_days
        if service_method == ServiceMethod.MAIL:
            base_days += _ADDITIONAL_MAIL_SERVICE_DAYS

        due = served + timedelta(days=base_days)
        # Skip weekends for court deadlines
        while due.weekday() >= 5:  # Saturday=5, Sunday=6
            due += timedelta(days=1)
        return due.isoformat()

    @staticmethod
    def is_overdue(date_due: str) -> bool:
        """Check if a discovery response is overdue."""
        try:
            due = datetime.strptime(date_due, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return False
        return date.today() > due

    @staticmethod
    def days_until_due(date_due: str) -> int:
        """Return number of days until deadline (negative if past)."""
        try:
            due = datetime.strptime(date_due, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return 0
        return (due - date.today()).days

    def generate_calendar_view(
        self, requests: Sequence[DiscoveryRequest]
    ) -> List[Dict[str, Any]]:
        """Generate a calendar view of all discovery deadlines."""
        entries: List[Dict[str, Any]] = []
        for req in requests:
            if not req.date_due:
                continue
            days_left = self.days_until_due(req.date_due)
            urgency = "critical" if days_left < 0 else (
                "urgent" if days_left <= 7 else (
                    "upcoming" if days_left <= 14 else "normal"
                )
            )
            entries.append({
                "request_id": req.request_id,
                "type": req.discovery_type.value,
                "case_number": req.case_number,
                "date_due": req.date_due,
                "days_remaining": days_left,
                "urgency": urgency,
                "status": req.status.value,
                "responding_party": req.responding_party,
            })
        return sorted(entries, key=lambda e: e["days_remaining"])

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "DiscoveryCalendar",
            "response_days_interrogatory": _MCR_2309_RESPONSE_DAYS,
            "response_days_production": _MCR_2310_RESPONSE_DAYS,
            "response_days_admission": _MCR_2312_RESPONSE_DAYS,
            "mail_service_addition": _ADDITIONAL_MAIL_SERVICE_DAYS,
        }


# ---------------------------------------------------------------------------
# ResponseDrafter
# ---------------------------------------------------------------------------


class ResponseDrafter:
    """Drafts discovery responses and objections."""

    _VERIFICATION_TEXT = (
        "I, {party}, verify under penalty of perjury that the answers "
        "to the foregoing interrogatories are true and complete to the "
        "best of my knowledge, information, and belief."
    )

    def draft_response_header(
        self,
        request: DiscoveryRequest,
        responding_as: str = _PLAINTIFF,
    ) -> str:
        """Generate the header for a discovery response document."""
        type_label = {
            DiscoveryType.INTERROGATORY: "ANSWERS TO INTERROGATORIES",
            DiscoveryType.REQUEST_PRODUCTION: "RESPONSES TO REQUESTS FOR PRODUCTION",
            DiscoveryType.REQUEST_ADMISSION: "RESPONSES TO REQUESTS FOR ADMISSION",
        }.get(request.discovery_type, "DISCOVERY RESPONSES")

        lines = [
            "STATE OF MICHIGAN",
            f"IN THE {_COURT.upper()}",
            f"COUNTY OF MUSKEGON",
            "",
            f"{_PLAINTIFF},".ljust(40) + f"Case No. {request.case_number}",
            "    Plaintiff,".ljust(40) + f"Hon. {_JUDGE}",
            "v.",
            f"{_DEFENDANT},",
            "    Defendant.",
            "_" * 60,
            "",
            f"{responding_as.upper()}'S {type_label}",
            f"(Set No. {request.set_number})",
            "",
        ]
        return "\n".join(lines)

    def draft_item_response(
        self,
        item: DiscoveryItem,
        objection_types: Optional[List[ObjectionType]] = None,
        answer: str = "",
    ) -> str:
        """Draft a response for a single discovery item."""
        lines: List[str] = []
        lines.append(f"REQUEST NO. {item.item_number}:")
        lines.append(f"    {item.text}")
        lines.append("")

        if objection_types:
            lines.append("OBJECTION:")
            for obj in objection_types:
                lines.append(f"    {obj.template}")
            lines.append("")

        lines.append("RESPONSE:")
        if answer:
            lines.append(f"    {answer}")
        else:
            lines.append("    Subject to and without waiving the foregoing "
                         "objections, Plaintiff responds as follows:")
            lines.append("    [RESPONSE]")
        lines.append("")
        return "\n".join(lines)

    def draft_privilege_log(
        self, entries: Sequence[PrivilegeLogEntry]
    ) -> str:
        """Generate a formatted privilege log."""
        lines = [
            "PRIVILEGE LOG",
            "=" * 60,
            "",
            "Pursuant to MCR 2.302(B)(1) and MCR 2.302(B)(3), the "
            "following documents are withheld on grounds of privilege:",
            "",
        ]
        for i, entry in enumerate(entries, 1):
            lines.append(f"{i}. Document: {entry.document_description}")
            lines.append(f"   Date: {entry.date_of_document}")
            lines.append(f"   Author: {entry.author}")
            if entry.recipients:
                lines.append(f"   Recipients: {', '.join(entry.recipients)}")
            lines.append(f"   Privilege: {entry.privilege_type}")
            lines.append(f"   Basis: {entry.basis}")
            lines.append("")
        return "\n".join(lines)

    def draft_verification(self, party_name: str = _PLAINTIFF) -> str:
        """Generate a verification statement for interrogatory answers."""
        return textwrap.dedent(f"""\
            VERIFICATION

            {self._VERIFICATION_TEXT.format(party=party_name)}

            Date: ____________

            ________________________________________
            {party_name}""")

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "ResponseDrafter",
            "objection_types": len(ObjectionType),
            "service_methods": len(ServiceMethod),
        }


# ---------------------------------------------------------------------------
# MotionToCompelGenerator
# ---------------------------------------------------------------------------


class MotionToCompelGenerator:
    """Prepares motions to compel under MCR 2.313."""

    def prepare_motion(
        self,
        overdue_requests: Sequence[DiscoveryRequest],
        meet_confer: Optional[MeetAndConferRecord] = None,
        request_sanctions: bool = False,
    ) -> MotionToCompel:
        """Generate a motion to compel from overdue requests."""
        request_ids = [r.request_id for r in overdue_requests]
        overdue_items: List[str] = []
        case_numbers = set()
        lanes = set()

        for req in overdue_requests:
            case_numbers.add(req.case_number)
            lanes.add(req.lane)
            for item in req.items:
                if not item.is_answered:
                    overdue_items.append(
                        f"{req.discovery_type.value} Set {req.set_number}, "
                        f"Item {item.item_number}"
                    )

        motion = MotionToCompel(
            case_number=next(iter(case_numbers), ""),
            lane=next(iter(lanes), ""),
            discovery_request_ids=request_ids,
            overdue_items=overdue_items,
            meet_and_confer=meet_confer,
            sanctions_requested=request_sanctions,
        )

        if request_sanctions:
            motion.sanctions_basis = (
                "MCR 2.313(B)(2) — reasonable expenses including attorney "
                "fees caused by the failure to respond to discovery."
            )

        return motion

    def render_motion_text(self, motion: MotionToCompel) -> str:
        """Render the motion to compel as text."""
        lines = [
            "STATE OF MICHIGAN",
            f"IN THE {_COURT.upper()}",
            "COUNTY OF MUSKEGON",
            "",
            f"Case No. {motion.case_number}",
            f"Hon. {_JUDGE}",
            "",
            "PLAINTIFF'S MOTION TO COMPEL DISCOVERY",
            "UNDER MCR 2.313",
            "=" * 60,
            "",
            "NOW COMES Plaintiff, Andrew James Pigors, Pro Se, and "
            "respectfully moves this Honorable Court for an Order "
            "compelling Defendant to respond to outstanding discovery "
            "requests, and in support thereof states:",
            "",
            "I. FACTUAL BACKGROUND",
            "",
        ]

        for i, item_desc in enumerate(motion.overdue_items, 1):
            lines.append(f"    {i}. {item_desc} — response overdue")

        lines.extend([
            "",
            "II. LEGAL AUTHORITY",
            "",
            "    Under MCR 2.313(A), when a party fails to answer "
            "interrogatories submitted under MCR 2.309 or to respond "
            "to requests for production under MCR 2.310, the "
            "discovering party may move for an order compelling "
            "discovery.",
            "",
        ])

        if motion.meet_and_confer:
            mc = motion.meet_and_confer
            lines.extend([
                "III. MEET AND CONFER",
                "",
                f"    On {mc.date}, Plaintiff attempted to resolve this "
                f"dispute via {mc.method}.",
                f"    Outcome: {mc.outcome}",
                "",
            ])

        if motion.sanctions_requested:
            lines.extend([
                "IV. REQUEST FOR SANCTIONS",
                "",
                f"    {motion.sanctions_basis}",
                "",
            ])

        lines.extend([
            "WHEREFORE, Plaintiff respectfully requests this Court:",
            "",
            "    1. Order Defendant to provide complete responses to "
            "all outstanding discovery within 14 days;",
            "",
        ])

        if motion.sanctions_requested:
            lines.append(
                "    2. Award Plaintiff reasonable expenses, including "
                "filing fees, incurred in bringing this motion;"
            )
            lines.append("")

        lines.extend([
            "Respectfully submitted,",
            "",
            f"{'_' * 40}",
            f"{_PLAINTIFF}",
            "Pro Se",
        ])

        return "\n".join(lines)

    def calculate_sanctions(
        self, filing_fee: float = 20.0, copy_costs: float = 0.0,
        hours_spent: float = 0.0,
    ) -> Dict[str, float]:
        """Estimate sanctions under MCR 2.313(B)(2)."""
        total = filing_fee + copy_costs
        return {
            "filing_fee": filing_fee,
            "copy_costs": copy_costs,
            "hours_spent": hours_spent,
            "total_requested": round(total, 2),
            "mcr_authority": "MCR 2.313(B)(2)",
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "MotionToCompelGenerator",
            "mcr_authority": "MCR 2.313",
        }


# ---------------------------------------------------------------------------
# Database layer
# ---------------------------------------------------------------------------

_PRAGMAS = textwrap.dedent("""\
    PRAGMA busy_timeout = 60000;
    PRAGMA journal_mode = WAL;
    PRAGMA cache_size = -32000;
    PRAGMA temp_store = MEMORY;
    PRAGMA synchronous = NORMAL;
""")

_CREATE_REQUESTS_SQL = textwrap.dedent("""\
    CREATE TABLE IF NOT EXISTS discovery_requests (
        request_id        TEXT PRIMARY KEY,
        discovery_type    TEXT NOT NULL,
        case_number       TEXT,
        lane              TEXT,
        propounding_party TEXT,
        responding_party  TEXT,
        set_number        INTEGER DEFAULT 1,
        date_served       TEXT,
        date_due          TEXT,
        service_method    TEXT DEFAULT 'mail',
        items_json        TEXT,
        status            TEXT DEFAULT 'draft',
        response_text     TEXT,
        objections_json   TEXT,
        notes             TEXT,
        created_at        TEXT DEFAULT (datetime('now')),
        updated_at        TEXT DEFAULT (datetime('now'))
    )
""")

_CREATE_RESPONSES_SQL = textwrap.dedent("""\
    CREATE TABLE IF NOT EXISTS discovery_responses (
        response_id    TEXT PRIMARY KEY,
        request_id     TEXT NOT NULL,
        item_number    INTEGER,
        response_text  TEXT,
        objections     TEXT,
        is_answered    INTEGER DEFAULT 0,
        created_at     TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (request_id) REFERENCES discovery_requests(request_id)
    )
""")

_CREATE_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_disc_req_status "
    "ON discovery_requests(status, lane)",
    "CREATE INDEX IF NOT EXISTS idx_disc_req_due "
    "ON discovery_requests(date_due, status)",
    "CREATE INDEX IF NOT EXISTS idx_disc_resp_req "
    "ON discovery_responses(request_id, item_number)",
]


def _ensure_tables(conn: sqlite3.Connection) -> None:
    conn.execute(_CREATE_REQUESTS_SQL)
    conn.execute(_CREATE_RESPONSES_SQL)
    for idx in _CREATE_INDEXES_SQL:
        conn.execute(idx)
    conn.commit()


# ---------------------------------------------------------------------------
# DiscoveryManager — orchestrator
# ---------------------------------------------------------------------------


class DiscoveryManager:
    """Top-level orchestrator for discovery management.

    Combines :class:`DiscoveryCalendar`, :class:`ResponseDrafter`, and
    :class:`MotionToCompelGenerator` into a unified workflow.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or _DB_PATH
        self._calendar = DiscoveryCalendar()
        self._drafter = ResponseDrafter()
        self._mtc_generator = MotionToCompelGenerator()
        self._requests: List[DiscoveryRequest] = []

    # -- request management --

    def create_request(
        self,
        discovery_type: DiscoveryType,
        case_number: str,
        lane: str,
        items: Optional[List[DiscoveryItem]] = None,
        propounding_party: str = _PLAINTIFF,
        responding_party: str = _DEFENDANT,
        set_number: int = 1,
        date_served: str = "",
        service_method: ServiceMethod = ServiceMethod.MAIL,
    ) -> DiscoveryRequest:
        """Create and register a new discovery request."""
        req = DiscoveryRequest(
            discovery_type=discovery_type,
            case_number=case_number,
            lane=lane,
            propounding_party=propounding_party,
            responding_party=responding_party,
            set_number=set_number,
            date_served=date_served,
            service_method=service_method,
            items=items or [],
        )

        if date_served:
            req.date_due = self._calendar.calculate_due_date(
                date_served, discovery_type, service_method
            )
            req.status = DiscoveryStatus.SERVED
        else:
            req.status = DiscoveryStatus.DRAFT

        self._requests.append(req)
        return req

    def add_request(self, request: DiscoveryRequest) -> None:
        """Add an existing request object."""
        self._requests.append(request)

    def get_request(self, request_id: str) -> Optional[DiscoveryRequest]:
        """Retrieve a request by ID."""
        for req in self._requests:
            if req.request_id == request_id:
                return req
        return None

    # -- tracking --

    def track_response(
        self,
        request_id: str,
        item_number: int,
        response_text: str,
        objections: Optional[List[ObjectionType]] = None,
    ) -> bool:
        """Record a response to a specific discovery item."""
        req = self.get_request(request_id)
        if not req:
            return False

        for item in req.items:
            if item.item_number == item_number:
                item.response = response_text
                item.objections = objections or []
                item.is_answered = True
                break
        else:
            return False

        if all(i.is_answered for i in req.items):
            req.status = DiscoveryStatus.RESPONDED
        return True

    def update_status(self, request_id: str, status: DiscoveryStatus) -> bool:
        """Manually update a request's status."""
        req = self.get_request(request_id)
        if not req:
            return False
        req.status = status
        return True

    def get_overdue(self) -> List[DiscoveryRequest]:
        """Return all overdue discovery requests."""
        overdue: List[DiscoveryRequest] = []
        for req in self._requests:
            if req.status in (DiscoveryStatus.SERVED, DiscoveryStatus.RESPONSE_DUE):
                if req.date_due and self._calendar.is_overdue(req.date_due):
                    req.status = DiscoveryStatus.OVERDUE
                    overdue.append(req)
            elif req.status == DiscoveryStatus.OVERDUE:
                overdue.append(req)
        return overdue

    # -- reporting --

    def generate_discovery_report(self) -> DiscoveryReport:
        """Generate a comprehensive discovery status report."""
        report = DiscoveryReport(total_requests=len(self._requests))

        by_type: Dict[str, int] = defaultdict(int)
        by_status: Dict[str, int] = defaultdict(int)
        overdue_ids: List[str] = []
        upcoming: List[Dict[str, str]] = []

        for req in self._requests:
            by_type[req.discovery_type.value] += 1
            by_status[req.status.value] += 1

            if req.status == DiscoveryStatus.OVERDUE:
                overdue_ids.append(req.request_id)
            elif req.date_due:
                days = self._calendar.days_until_due(req.date_due)
                if 0 <= days <= 14:
                    upcoming.append({
                        "request_id": req.request_id,
                        "type": req.discovery_type.value,
                        "date_due": req.date_due,
                        "days_remaining": str(days),
                    })

        report.by_type = dict(by_type)
        report.by_status = dict(by_status)
        report.overdue_count = len(overdue_ids)
        report.overdue_requests = overdue_ids
        report.upcoming_deadlines = sorted(
            upcoming, key=lambda u: int(u["days_remaining"])
        )
        report.motions_to_compel = sum(
            1 for r in self._requests
            if r.status == DiscoveryStatus.MOTION_TO_COMPEL
        )
        return report

    def to_markdown(self) -> str:
        """Render discovery report as Markdown."""
        report = self.generate_discovery_report()
        lines = [
            "## Discovery Status Report",
            f"### Generated: {report.generated_at[:10]} | "
            f"Total Requests: {report.total_requests}",
            "",
            "#### By Type",
        ]
        for dtype, count in sorted(report.by_type.items()):
            lines.append(f"- {dtype}: {count}")
        lines.append("")
        lines.append("#### By Status")
        for status, count in sorted(report.by_status.items()):
            lines.append(f"- {status}: {count}")
        lines.append("")

        if report.overdue_count > 0:
            lines.append(f"#### ⚠ OVERDUE: {report.overdue_count} request(s)")
            for rid in report.overdue_requests:
                lines.append(f"- {rid}")
            lines.append("")

        if report.upcoming_deadlines:
            lines.append("#### Upcoming Deadlines")
            for dl in report.upcoming_deadlines:
                lines.append(
                    f"- {dl['type']} ({dl['request_id']}): "
                    f"due {dl['date_due']} ({dl['days_remaining']} days)"
                )
        return "\n".join(lines)

    # -- persistence --

    def persist(self) -> int:
        """Write discovery requests to the database."""
        if not self._db_path.exists():
            logger.warning("Database not found — cannot persist")
            return 0

        try:
            conn = sqlite3.connect(str(self._db_path), timeout=60)
            conn.executescript(_PRAGMAS)
        except sqlite3.Error as exc:
            logger.error("DB connection failed: %s", exc)
            return 0

        try:
            _ensure_tables(conn)
            rows: List[Tuple[Any, ...]] = []
            for req in self._requests:
                rows.append((
                    req.request_id,
                    req.discovery_type.value,
                    req.case_number,
                    req.lane,
                    req.propounding_party,
                    req.responding_party,
                    req.set_number,
                    req.date_served,
                    req.date_due,
                    req.service_method.value,
                    json.dumps([i.to_dict() for i in req.items]),
                    req.status.value,
                    req.response_text,
                    json.dumps(req.objections),
                    req.notes,
                ))
            conn.executemany(
                "INSERT OR REPLACE INTO discovery_requests "
                "(request_id, discovery_type, case_number, lane, "
                "propounding_party, responding_party, set_number, "
                "date_served, date_due, service_method, items_json, "
                "status, response_text, objections_json, notes) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                rows,
            )
            conn.commit()
            return len(rows)
        except sqlite3.Error as exc:
            logger.error("Persist failed: %s", exc)
            return 0
        finally:
            conn.close()

    # -- stats --

    def get_stats(self) -> Dict[str, Any]:
        """Return runtime statistics."""
        return {
            "module": "discovery_manager",
            "requests_loaded": len(self._requests),
            "overdue_count": len(self.get_overdue()),
            "db_path": str(self._db_path),
            "calendar": self._calendar.get_stats(),
            "drafter": self._drafter.get_stats(),
            "mtc_generator": self._mtc_generator.get_stats(),
        }

    def reset(self) -> None:
        """Clear all loaded requests."""
        self._requests.clear()


# ---------------------------------------------------------------------------
# CLI demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sys.stdout = open(  # noqa: SIM115
        sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace"
    )
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print("=" * 60)
    print("  Discovery Manager — LitigationOS")
    print("=" * 60)
    print()

    dm = DiscoveryManager()
    req = dm.create_request(
        discovery_type=DiscoveryType.INTERROGATORY,
        case_number="2024-001507-DC",
        lane="A",
        date_served="2025-01-15",
        items=[
            DiscoveryItem(item_number=1, text="State your full legal name and address."),
            DiscoveryItem(item_number=2, text="Describe all contact with L.D.W. in the past 90 days."),
            DiscoveryItem(item_number=3, text="Identify all witnesses to parenting-time exchanges."),
        ],
    )

    print(f"Request created: {req.request_id}")
    print(f"Type: {req.discovery_type.value} (Set {req.set_number})")
    print(f"Date served: {req.date_served}")
    print(f"Due date: {req.date_due}")
    print(f"MCR reference: {req.discovery_type.mcr_reference}")
    print()

    print(dm.to_markdown())
    print()
    print("--- Stats ---")
    import pprint

    pprint.pprint(dm.get_stats())
