# -*- coding: utf-8 -*-
"""
Evidence Authenticator — LitigationOS Legal AI Subsystem
=========================================================
Analyses exhibits for Michigan Rules of Evidence authentication
requirements (MRE 901/902), identifies hearsay exceptions (MRE 803/804),
documents chain-of-custody, builds foundation testimony templates, and
ensures best-evidence-rule compliance (MRE 1001-1008).

Case Context
------------
    Plaintiff:  Andrew James Pigors (Pro Se)
    Defendant:  Emily A. Watson
    Child:      L.D.W. (per MCR 8.119(H)) — Male
    Judge:      Hon. Jenny L. McNeill — 14th Circuit Court
    Cases:      2024-001507-DC, 2025-002760-CZ, 2023-5907-PP, COA 366810
    Lanes:      ALL (A through F)

Usage::

    from legal_ai.evidence_authenticator import EvidenceAuthenticator

    auth = EvidenceAuthenticator()
    auth.scan_exhibits()
    report = auth.generate_report()

Zero external dependencies.  CPU-first.  Local-only.
"""
from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import sys
import textwrap
import uuid
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

logger = logging.getLogger("legal_ai.evidence_authenticator")

# ---------------------------------------------------------------------------
# Path resolution
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
# Enumerations
# ---------------------------------------------------------------------------


class AuthenticationMethod(str, Enum):
    """Primary authentication methods under MRE 901/902."""

    WITNESS_TESTIMONY = "MRE 901(b)(1)"
    HANDWRITING_OPINION = "MRE 901(b)(2)"
    EXPERT_COMPARISON = "MRE 901(b)(3)"
    DISTINCTIVE_CHARACTERISTICS = "MRE 901(b)(4)"
    VOICE_IDENTIFICATION = "MRE 901(b)(5)"
    TELEPHONE_CONVERSATION = "MRE 901(b)(6)"
    PUBLIC_RECORDS = "MRE 901(b)(7)"
    ANCIENT_DOCUMENT = "MRE 901(b)(8)"
    PROCESS_OR_SYSTEM = "MRE 901(b)(9)"
    STATUTORY_METHOD = "MRE 901(b)(10)"
    SELF_AUTH_SEAL = "MRE 902(1)"
    SELF_AUTH_NO_SEAL = "MRE 902(2)"
    SELF_AUTH_FOREIGN = "MRE 902(3)"
    SELF_AUTH_CERTIFIED_COPY = "MRE 902(4)"
    SELF_AUTH_OFFICIAL_PUB = "MRE 902(5)"
    SELF_AUTH_NEWSPAPER = "MRE 902(6)"
    SELF_AUTH_TRADE = "MRE 902(7)"
    SELF_AUTH_ACKNOWLEDGED = "MRE 902(8)"
    SELF_AUTH_COMMERCIAL = "MRE 902(9)"
    SELF_AUTH_STATUTE = "MRE 902(10)"
    SELF_AUTH_CERTIFIED_RECORD = "MRE 902(11)"


class EvidenceType(str, Enum):
    """Common evidence categories in family-law litigation."""

    TEXT_MESSAGE = "text_message"
    EMAIL = "email"
    SCREENSHOT = "screenshot"
    SOCIAL_MEDIA = "social_media"
    PHOTOGRAPH = "photograph"
    VIDEO = "video"
    AUDIO_RECORDING = "audio_recording"
    BUSINESS_RECORD = "business_record"
    MEDICAL_RECORD = "medical_record"
    POLICE_REPORT = "police_report"
    COURT_FILING = "court_filing"
    GOVERNMENT_RECORD = "government_record"
    FINANCIAL_RECORD = "financial_record"
    PHYSICAL_DOCUMENT = "physical_document"
    WEBSITE_CONTENT = "website_content"
    OTHER = "other"


class HearsayException(str, Enum):
    """Hearsay exceptions under MRE 803 and 804."""

    PRESENT_SENSE_IMPRESSION = "MRE 803(1)"
    EXCITED_UTTERANCE = "MRE 803(2)"
    STATE_OF_MIND = "MRE 803(3)"
    MEDICAL_DIAGNOSIS = "MRE 803(4)"
    RECORDED_RECOLLECTION = "MRE 803(5)"
    BUSINESS_RECORDS = "MRE 803(6)"
    ABSENCE_OF_RECORD = "MRE 803(7)"
    PUBLIC_RECORDS = "MRE 803(8)"
    VITAL_STATISTICS = "MRE 803(9)"
    PRIOR_CONVICTION = "MRE 803(22)"
    FORMER_TESTIMONY = "MRE 804(b)(1)"
    DYING_DECLARATION = "MRE 804(b)(2)"
    STATEMENT_AGAINST_INTEREST = "MRE 804(b)(3)"
    FAMILY_HISTORY = "MRE 804(b)(4)"
    FORFEITURE_BY_WRONGDOING = "MRE 804(b)(6)"
    NONE = "none"
    NOT_HEARSAY = "not_hearsay"


class CustodyStatus(str, Enum):
    """Chain-of-custody completeness."""

    COMPLETE = "complete"
    MINOR_GAP = "minor_gap"
    MODERATE_GAP = "moderate_gap"
    CRITICAL_GAP = "critical_gap"
    NOT_DOCUMENTED = "not_documented"
    NOT_APPLICABLE = "not_applicable"


class AuthStatus(str, Enum):
    """Overall authentication readiness."""

    READY = "ready"
    NEEDS_FOUNDATION = "needs_foundation"
    NEEDS_CUSTODY_CHAIN = "needs_custody_chain"
    NEEDS_HEARSAY_EXCEPTION = "needs_hearsay_exception"
    AT_RISK = "at_risk"
    EXCLUDED = "excluded"
    PENDING = "pending"


class BestEvidenceStatus(str, Enum):
    """Best evidence rule (MRE 1001-1008) compliance."""

    ORIGINAL = "original"
    DUPLICATE_OK = "duplicate_ok_mre_1003"
    EXCEPTION_LOST = "exception_mre_1004_lost"
    EXCEPTION_OPPONENT = "exception_mre_1004_opponent"
    EXCEPTION_COLLATERAL = "exception_mre_1004_collateral"
    NON_COMPLIANT = "non_compliant"
    NOT_APPLICABLE = "not_applicable"


# ---------------------------------------------------------------------------
# Default authentication-method mapping by evidence type
# ---------------------------------------------------------------------------

_DEFAULT_AUTH_METHODS: Dict[EvidenceType, List[AuthenticationMethod]] = {
    EvidenceType.TEXT_MESSAGE: [
        AuthenticationMethod.DISTINCTIVE_CHARACTERISTICS,
        AuthenticationMethod.WITNESS_TESTIMONY,
    ],
    EvidenceType.EMAIL: [
        AuthenticationMethod.DISTINCTIVE_CHARACTERISTICS,
        AuthenticationMethod.PROCESS_OR_SYSTEM,
    ],
    EvidenceType.SCREENSHOT: [
        AuthenticationMethod.WITNESS_TESTIMONY,
        AuthenticationMethod.PROCESS_OR_SYSTEM,
    ],
    EvidenceType.SOCIAL_MEDIA: [
        AuthenticationMethod.DISTINCTIVE_CHARACTERISTICS,
        AuthenticationMethod.WITNESS_TESTIMONY,
    ],
    EvidenceType.PHOTOGRAPH: [
        AuthenticationMethod.WITNESS_TESTIMONY,
    ],
    EvidenceType.VIDEO: [
        AuthenticationMethod.WITNESS_TESTIMONY,
        AuthenticationMethod.VOICE_IDENTIFICATION,
    ],
    EvidenceType.AUDIO_RECORDING: [
        AuthenticationMethod.VOICE_IDENTIFICATION,
        AuthenticationMethod.WITNESS_TESTIMONY,
    ],
    EvidenceType.BUSINESS_RECORD: [
        AuthenticationMethod.SELF_AUTH_CERTIFIED_RECORD,
        AuthenticationMethod.WITNESS_TESTIMONY,
    ],
    EvidenceType.MEDICAL_RECORD: [
        AuthenticationMethod.SELF_AUTH_CERTIFIED_RECORD,
    ],
    EvidenceType.POLICE_REPORT: [
        AuthenticationMethod.SELF_AUTH_CERTIFIED_COPY,
        AuthenticationMethod.PUBLIC_RECORDS,
    ],
    EvidenceType.COURT_FILING: [
        AuthenticationMethod.SELF_AUTH_SEAL,
        AuthenticationMethod.SELF_AUTH_CERTIFIED_COPY,
    ],
    EvidenceType.GOVERNMENT_RECORD: [
        AuthenticationMethod.SELF_AUTH_SEAL,
        AuthenticationMethod.PUBLIC_RECORDS,
    ],
    EvidenceType.FINANCIAL_RECORD: [
        AuthenticationMethod.SELF_AUTH_CERTIFIED_RECORD,
        AuthenticationMethod.WITNESS_TESTIMONY,
    ],
    EvidenceType.PHYSICAL_DOCUMENT: [
        AuthenticationMethod.WITNESS_TESTIMONY,
    ],
    EvidenceType.WEBSITE_CONTENT: [
        AuthenticationMethod.PROCESS_OR_SYSTEM,
        AuthenticationMethod.WITNESS_TESTIMONY,
    ],
    EvidenceType.OTHER: [
        AuthenticationMethod.WITNESS_TESTIMONY,
    ],
}

# Hearsay exceptions commonly applicable per evidence type
_DEFAULT_HEARSAY: Dict[EvidenceType, List[HearsayException]] = {
    EvidenceType.TEXT_MESSAGE: [
        HearsayException.PRESENT_SENSE_IMPRESSION,
        HearsayException.EXCITED_UTTERANCE,
        HearsayException.STATE_OF_MIND,
    ],
    EvidenceType.EMAIL: [
        HearsayException.BUSINESS_RECORDS,
        HearsayException.STATE_OF_MIND,
    ],
    EvidenceType.BUSINESS_RECORD: [HearsayException.BUSINESS_RECORDS],
    EvidenceType.MEDICAL_RECORD: [
        HearsayException.BUSINESS_RECORDS,
        HearsayException.MEDICAL_DIAGNOSIS,
    ],
    EvidenceType.POLICE_REPORT: [HearsayException.PUBLIC_RECORDS],
    EvidenceType.COURT_FILING: [HearsayException.PUBLIC_RECORDS],
    EvidenceType.GOVERNMENT_RECORD: [HearsayException.PUBLIC_RECORDS],
}


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class ChainOfCustodyEntry:
    """Single entry in a chain-of-custody log."""

    entry_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    date: str = ""
    person: str = ""
    action: str = ""
    reason: str = ""
    location: str = ""
    hash_sha256: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EvidenceItem:
    """An exhibit or evidence item requiring authentication."""

    item_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    exhibit_number: str = ""
    title: str = ""
    description: str = ""
    evidence_type: EvidenceType = EvidenceType.OTHER
    lane: str = ""
    case_number: str = ""
    source: str = ""
    date_obtained: str = ""
    obtained_by: str = _PLAINTIFF
    storage_location: str = ""
    file_path: str = ""
    file_hash: str = ""
    is_original: bool = True
    metadata: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["evidence_type"] = self.evidence_type.value
        return d


@dataclass
class AuthenticationRequirement:
    """Authentication analysis result for a single exhibit."""

    item_id: str = ""
    exhibit_number: str = ""
    title: str = ""
    evidence_type: EvidenceType = EvidenceType.OTHER
    primary_method: AuthenticationMethod = AuthenticationMethod.WITNESS_TESTIMONY
    alternative_methods: List[AuthenticationMethod] = field(default_factory=list)
    custody_chain: List[ChainOfCustodyEntry] = field(default_factory=list)
    custody_status: CustodyStatus = CustodyStatus.NOT_DOCUMENTED
    hearsay_issues: List[HearsayException] = field(default_factory=list)
    hearsay_resolved: bool = True
    best_evidence: BestEvidenceStatus = BestEvidenceStatus.NOT_APPLICABLE
    foundation_witness: str = ""
    foundation_witness_available: bool = False
    foundation_notes: str = ""
    overall_status: AuthStatus = AuthStatus.PENDING
    lane: str = ""
    case_number: str = ""
    issues: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "exhibit_number": self.exhibit_number,
            "title": self.title,
            "evidence_type": self.evidence_type.value,
            "primary_method": self.primary_method.value,
            "alternative_methods": [m.value for m in self.alternative_methods],
            "custody_chain": [c.to_dict() for c in self.custody_chain],
            "custody_status": self.custody_status.value,
            "hearsay_issues": [h.value for h in self.hearsay_issues],
            "hearsay_resolved": self.hearsay_resolved,
            "best_evidence": self.best_evidence.value,
            "foundation_witness": self.foundation_witness,
            "foundation_witness_available": self.foundation_witness_available,
            "overall_status": self.overall_status.value,
            "lane": self.lane,
            "case_number": self.case_number,
            "issues": self.issues,
            "foundation_notes": self.foundation_notes,
        }


@dataclass
class AuthenticationReport:
    """Complete authentication readiness report."""

    report_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    total_exhibits: int = 0
    ready_count: int = 0
    needs_work_count: int = 0
    at_risk_count: int = 0
    custody_gap_count: int = 0
    hearsay_issue_count: int = 0
    requirements: List[AuthenticationRequirement] = field(default_factory=list)
    priority_actions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at,
            "total_exhibits": self.total_exhibits,
            "ready_count": self.ready_count,
            "needs_work_count": self.needs_work_count,
            "at_risk_count": self.at_risk_count,
            "custody_gap_count": self.custody_gap_count,
            "hearsay_issue_count": self.hearsay_issue_count,
            "requirements": [r.to_dict() for r in self.requirements],
            "priority_actions": self.priority_actions,
        }


# ---------------------------------------------------------------------------
# Foundation templates
# ---------------------------------------------------------------------------

_FOUNDATION_TEMPLATES: Dict[EvidenceType, str] = {
    EvidenceType.PHOTOGRAPH: textwrap.dedent("""\
        Q: I'm showing you what has been marked as Exhibit [#]. Do you recognise it?
        A: Yes.
        Q: What is it?
        A: It is a photograph of [description].
        Q: Does this photograph fairly and accurately depict [subject] as it appeared on [date]?
        A: Yes.
        PROPONENT: Your Honour, I move to admit Exhibit [#]."""),
    EvidenceType.TEXT_MESSAGE: textwrap.dedent("""\
        Q: I'm showing you Exhibit [#]. Do you recognise it?
        A: Yes, these are text messages between myself and [person].
        Q: How do you recognise them?
        A: I recognise the phone numbers and the content of the conversation.
        Q: Did you take these screenshots from your phone?
        A: Yes, on [date].
        Q: Do they fairly and accurately represent the text conversation?
        A: Yes.
        PROPONENT: Your Honour, I move to admit Exhibit [#]."""),
    EvidenceType.EMAIL: textwrap.dedent("""\
        Q: I'm showing you Exhibit [#]. Do you recognise this document?
        A: Yes, it is a printout of an email.
        Q: Who sent this email?
        A: It was sent by [sender] to [recipient].
        Q: How do you know?
        A: I recognise the email addresses, and the content is consistent with our correspondence.
        Q: Is this a true and correct copy of the email?
        A: Yes.
        PROPONENT: Your Honour, I move to admit Exhibit [#]."""),
    EvidenceType.BUSINESS_RECORD: textwrap.dedent("""\
        Q: What is your position at [organisation]?
        A: I am the [title].
        Q: Are you the custodian of records for [record type]?
        A: Yes.
        Q: I'm showing you Exhibit [#]. Do you recognise it?
        A: Yes, it is a [description] from our records.
        Q: Was this record made at or near the time of the events described?
        A: Yes.
        Q: Was it made by a person with knowledge?
        A: Yes.
        Q: Is it the regular practice of [organisation] to make this type of record?
        A: Yes.
        Q: Was this record kept in the regular course of business?
        A: Yes.
        PROPONENT: Your Honour, I move to admit Exhibit [#] under MRE 803(6)."""),
    EvidenceType.AUDIO_RECORDING: textwrap.dedent("""\
        Q: I'm showing you Exhibit [#]. Can you identify this?
        A: Yes, it is an audio recording.
        Q: Do you recognise the voices?
        A: Yes, I recognise [persons].
        Q: When was this recording made?
        A: On [date].
        Q: Is this a complete and accurate recording?
        A: Yes.
        PROPONENT: Your Honour, I move to admit Exhibit [#]."""),
    EvidenceType.VIDEO: textwrap.dedent("""\
        Q: Exhibit [#] is a video. Do you recognise it?
        A: Yes.
        Q: What does it show?
        A: It shows [description].
        Q: Does this video fairly and accurately depict the events as they occurred?
        A: Yes.
        PROPONENT: Your Honour, I move to admit Exhibit [#]."""),
    EvidenceType.SCREENSHOT: textwrap.dedent("""\
        Q: I'm showing you Exhibit [#]. What is this?
        A: It is a screenshot taken from [device/application].
        Q: Who took this screenshot?
        A: I did, on [date].
        Q: Does it accurately show what appeared on screen at that time?
        A: Yes.
        PROPONENT: Your Honour, I move to admit Exhibit [#]."""),
    EvidenceType.SOCIAL_MEDIA: textwrap.dedent("""\
        Q: I'm showing you Exhibit [#]. What is this?
        A: It is a printout of a social-media post from [platform].
        Q: Whose account posted this?
        A: [Account holder].
        Q: How do you know?
        A: I recognise the account name, profile picture, and the content is consistent with [context].
        Q: When was this captured?
        A: On [date].
        PROPONENT: Your Honour, I move to admit Exhibit [#]."""),
}


# ---------------------------------------------------------------------------
# AuthenticationAnalyzer
# ---------------------------------------------------------------------------


class AuthenticationAnalyzer:
    """Determines MRE 901/902 authentication requirements per exhibit."""

    def analyse(self, item: EvidenceItem) -> AuthenticationRequirement:
        """Produce an :class:`AuthenticationRequirement` for *item*."""
        methods = _DEFAULT_AUTH_METHODS.get(
            item.evidence_type, [AuthenticationMethod.WITNESS_TESTIMONY]
        )
        primary = methods[0] if methods else AuthenticationMethod.WITNESS_TESTIMONY
        alternatives = methods[1:] if len(methods) > 1 else []

        best_ev = self._best_evidence(item)
        custody = self._assess_custody(item)

        req = AuthenticationRequirement(
            item_id=item.item_id,
            exhibit_number=item.exhibit_number,
            title=item.title,
            evidence_type=item.evidence_type,
            primary_method=primary,
            alternative_methods=alternatives,
            custody_status=custody,
            best_evidence=best_ev,
            foundation_witness=item.obtained_by or _PLAINTIFF,
            foundation_witness_available=True,
            lane=item.lane,
            case_number=item.case_number,
        )
        return req

    @staticmethod
    def _best_evidence(item: EvidenceItem) -> BestEvidenceStatus:
        if item.evidence_type in (
            EvidenceType.PHOTOGRAPH,
            EvidenceType.VIDEO,
            EvidenceType.AUDIO_RECORDING,
        ):
            return BestEvidenceStatus.NOT_APPLICABLE
        if item.is_original:
            return BestEvidenceStatus.ORIGINAL
        return BestEvidenceStatus.DUPLICATE_OK

    @staticmethod
    def _assess_custody(item: EvidenceItem) -> CustodyStatus:
        if item.evidence_type in (
            EvidenceType.COURT_FILING,
            EvidenceType.GOVERNMENT_RECORD,
        ):
            return CustodyStatus.NOT_APPLICABLE
        if item.date_obtained and item.obtained_by and item.storage_location:
            return CustodyStatus.COMPLETE
        if item.date_obtained or item.obtained_by:
            return CustodyStatus.MINOR_GAP
        return CustodyStatus.NOT_DOCUMENTED

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "AuthenticationAnalyzer",
            "evidence_types_mapped": len(_DEFAULT_AUTH_METHODS),
            "auth_methods_available": len(AuthenticationMethod),
        }


# ---------------------------------------------------------------------------
# HearsayAnalyzer
# ---------------------------------------------------------------------------


class HearsayAnalyzer:
    """Identifies hearsay issues and matches exceptions."""

    _TYPE_KEYWORDS: Dict[HearsayException, List[str]] = {
        HearsayException.PRESENT_SENSE_IMPRESSION: [
            "right now", "just happened", "happening now", "as it happens",
        ],
        HearsayException.EXCITED_UTTERANCE: [
            "oh my god", "help", "911", "scared", "terrified", "emergency",
        ],
        HearsayException.STATE_OF_MIND: [
            "I feel", "I'm afraid", "I believe", "I think", "I want",
            "I intend", "I plan",
        ],
        HearsayException.MEDICAL_DIAGNOSIS: [
            "doctor", "therapist", "counselor", "diagnosis", "treatment",
            "prescribed", "medical",
        ],
        HearsayException.BUSINESS_RECORDS: [
            "invoice", "receipt", "statement", "account", "ledger", "log",
            "record of", "kept in the regular course",
        ],
        HearsayException.PUBLIC_RECORDS: [
            "police report", "court order", "government record", "vital record",
            "official report", "filed with",
        ],
    }

    def analyse(
        self, item: EvidenceItem, content_preview: str = ""
    ) -> List[HearsayException]:
        """Return applicable hearsay exceptions for *item*."""
        applicable: List[HearsayException] = []

        # Type-based defaults
        defaults = _DEFAULT_HEARSAY.get(item.evidence_type, [])
        applicable.extend(defaults)

        # Content-based detection
        lower = content_preview.lower()
        for exc, keywords in self._TYPE_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in lower:
                    if exc not in applicable:
                        applicable.append(exc)
                    break

        return applicable if applicable else [HearsayException.NONE]

    def is_hearsay_risk(self, item: EvidenceItem) -> bool:
        """Return True if the evidence type commonly raises hearsay issues."""
        risky = {
            EvidenceType.TEXT_MESSAGE,
            EvidenceType.EMAIL,
            EvidenceType.SOCIAL_MEDIA,
            EvidenceType.AUDIO_RECORDING,
        }
        return item.evidence_type in risky

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "HearsayAnalyzer",
            "exceptions_tracked": len(HearsayException),
            "keyword_categories": len(self._TYPE_KEYWORDS),
        }


# ---------------------------------------------------------------------------
# FoundationBuilder
# ---------------------------------------------------------------------------


class FoundationBuilder:
    """Generates foundation Q&A testimony templates per evidence type."""

    def build_foundation(
        self,
        item: EvidenceItem,
        req: AuthenticationRequirement,
    ) -> str:
        """Return a foundation-testimony template for *item*."""
        template = _FOUNDATION_TEMPLATES.get(item.evidence_type)
        if not template:
            return self._generic_foundation(item)

        filled = template.replace("[#]", item.exhibit_number or "[#]")
        filled = filled.replace("[description]", item.description or "[description]")
        filled = filled.replace("[date]", item.date_obtained or "[date]")
        filled = filled.replace("[person]", _DEFENDANT)
        filled = filled.replace("[sender]", "[sender]")
        filled = filled.replace("[recipient]", "[recipient]")
        return filled

    @staticmethod
    def _generic_foundation(item: EvidenceItem) -> str:
        return textwrap.dedent(f"""\
            Q: I'm showing you Exhibit [{item.exhibit_number or '#'}]. Do you recognise it?
            A: Yes.
            Q: What is it?
            A: It is {item.description or '[description]'}.
            Q: How do you know what this document is?
            A: [Explain basis of knowledge].
            Q: Is this a true and correct copy?
            A: Yes.
            PROPONENT: Your Honour, I move to admit Exhibit [{item.exhibit_number or '#'}].""")

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "FoundationBuilder",
            "templates_available": len(_FOUNDATION_TEMPLATES),
            "evidence_types_covered": list(_FOUNDATION_TEMPLATES.keys()),
        }


# ---------------------------------------------------------------------------
# Database layer
# ---------------------------------------------------------------------------

_CREATE_TABLE_SQL = textwrap.dedent("""\
    CREATE TABLE IF NOT EXISTS evidence_authentication (
        auth_id           TEXT PRIMARY KEY,
        exhibit_id        TEXT NOT NULL,
        exhibit_number    TEXT,
        exhibit_desc      TEXT,
        evidence_type     TEXT,
        auth_method       TEXT NOT NULL,
        mre_section       TEXT NOT NULL,
        chain_of_custody  TEXT,
        hearsay_exception TEXT,
        best_evidence     TEXT,
        foundation_notes  TEXT,
        status            TEXT CHECK(status IN (
            'pending','ready','needs_foundation','needs_custody_chain',
            'needs_hearsay_exception','at_risk','excluded'
        )),
        lane              TEXT,
        case_number       TEXT,
        created_at        TEXT DEFAULT (datetime('now')),
        updated_at        TEXT DEFAULT (datetime('now'))
    )
""")

_CREATE_INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_evidence_auth_exhibit "
    "ON evidence_authentication(exhibit_id)",
    "CREATE INDEX IF NOT EXISTS idx_evidence_auth_status "
    "ON evidence_authentication(status, lane)",
]


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(_CREATE_TABLE_SQL)
    for idx in _CREATE_INDEX_SQL:
        conn.execute(idx)
    conn.commit()


# ---------------------------------------------------------------------------
# EvidenceAuthenticator — orchestrator
# ---------------------------------------------------------------------------


class EvidenceAuthenticator:
    """Top-level orchestrator: scans exhibits, analyses authentication
    requirements, and generates readiness reports.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or _DB_PATH
        self._auth_analyzer = AuthenticationAnalyzer()
        self._hearsay_analyzer = HearsayAnalyzer()
        self._foundation_builder = FoundationBuilder()
        self._items: List[EvidenceItem] = []
        self._requirements: List[AuthenticationRequirement] = []
        self._report: Optional[AuthenticationReport] = None

    # -- item management --

    def add_item(self, item: EvidenceItem) -> None:
        self._items.append(item)

    def add_items(self, items: Sequence[EvidenceItem]) -> None:
        self._items.extend(items)

    # -- database scan --

    def scan_exhibits(self, lanes: Optional[List[str]] = None, limit: int = 500) -> int:
        """Scan litigation_context.db for exhibits and load them."""
        if not self._db_path.exists():
            logger.warning("Database not found at %s", self._db_path)
            return 0

        try:
            conn = sqlite3.connect(str(self._db_path), timeout=60)
            conn.execute("PRAGMA busy_timeout=60000")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA cache_size=-32000")
            conn.row_factory = sqlite3.Row
        except sqlite3.Error as exc:
            logger.error("DB connection failed: %s", exc)
            return 0

        count = 0
        try:
            tables = {
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            if "documents" not in tables:
                logger.info("documents table not found")
                return 0

            cols = [
                r[1]
                for r in conn.execute("PRAGMA table_info(documents)").fetchall()
            ]

            query = "SELECT * FROM documents"
            params: List[Any] = []
            conditions: List[str] = []

            if "doc_type" in cols:
                conditions.append(
                    "doc_type IN ('exhibit','evidence','attachment','document')"
                )
            if lanes and "lane" in cols:
                placeholders = ",".join("?" for _ in lanes)
                conditions.append(f"lane IN ({placeholders})")
                params.extend(lanes)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += f" LIMIT {int(limit)}"

            rows = conn.execute(query, params).fetchall()
            for row in rows:
                item = EvidenceItem(
                    item_id=str(row.get("doc_id", "") or row.get("id", "") or uuid.uuid4().hex[:12]),
                    title=str(row.get("title", "") or ""),
                    description=str(row.get("content_preview", "") or ""),
                    lane=str(row.get("lane", "") or ""),
                    case_number=str(row.get("case_number", "") or ""),
                    source=str(row.get("source", "") or ""),
                )
                etype = str(row.get("doc_type", "") or "").lower()
                type_map = {
                    "email": EvidenceType.EMAIL,
                    "text": EvidenceType.TEXT_MESSAGE,
                    "photo": EvidenceType.PHOTOGRAPH,
                    "screenshot": EvidenceType.SCREENSHOT,
                    "video": EvidenceType.VIDEO,
                    "audio": EvidenceType.AUDIO_RECORDING,
                    "medical": EvidenceType.MEDICAL_RECORD,
                    "police": EvidenceType.POLICE_REPORT,
                    "court": EvidenceType.COURT_FILING,
                    "financial": EvidenceType.FINANCIAL_RECORD,
                }
                for key, val in type_map.items():
                    if key in etype:
                        item.evidence_type = val
                        break

                self._items.append(item)
                count += 1
        except sqlite3.Error as exc:
            logger.error("Exhibit scan failed: %s", exc)
        finally:
            conn.close()

        return count

    # -- analysis --

    def analyse_all(self) -> List[AuthenticationRequirement]:
        """Analyse every loaded item."""
        self._requirements.clear()
        for item in self._items:
            req = self._auth_analyzer.analyse(item)

            # hearsay
            hearsay = self._hearsay_analyzer.analyse(item, item.description)
            req.hearsay_issues = hearsay
            req.hearsay_resolved = all(
                h in (HearsayException.NONE, HearsayException.NOT_HEARSAY)
                for h in hearsay
            )

            # foundation
            req.foundation_notes = self._foundation_builder.build_foundation(item, req)

            # determine overall status
            req.overall_status = self._determine_status(req)
            self._requirements.append(req)
        return self._requirements

    @staticmethod
    def _determine_status(req: AuthenticationRequirement) -> AuthStatus:
        issues: List[str] = []
        if req.custody_status in (
            CustodyStatus.CRITICAL_GAP,
            CustodyStatus.NOT_DOCUMENTED,
        ):
            issues.append("Chain of custody not documented")
        if not req.hearsay_resolved:
            issues.append("Hearsay exception needed")
        if req.best_evidence == BestEvidenceStatus.NON_COMPLIANT:
            issues.append("Best evidence rule not satisfied")
        if not req.foundation_witness:
            issues.append("No foundation witness identified")

        req.issues = issues
        if not issues:
            return AuthStatus.READY
        if len(issues) >= 3:
            return AuthStatus.AT_RISK
        if any("custody" in i.lower() for i in issues):
            return AuthStatus.NEEDS_CUSTODY_CHAIN
        if any("hearsay" in i.lower() for i in issues):
            return AuthStatus.NEEDS_HEARSAY_EXCEPTION
        return AuthStatus.NEEDS_FOUNDATION

    # -- report --

    def generate_report(self) -> AuthenticationReport:
        """Run analysis and produce a report."""
        if not self._requirements:
            self.analyse_all()

        report = AuthenticationReport(
            total_exhibits=len(self._requirements),
        )
        for req in self._requirements:
            report.requirements.append(req)
            if req.overall_status == AuthStatus.READY:
                report.ready_count += 1
            elif req.overall_status == AuthStatus.AT_RISK:
                report.at_risk_count += 1
            else:
                report.needs_work_count += 1
            if req.custody_status in (
                CustodyStatus.CRITICAL_GAP,
                CustodyStatus.MODERATE_GAP,
                CustodyStatus.NOT_DOCUMENTED,
            ):
                report.custody_gap_count += 1
            if not req.hearsay_resolved:
                report.hearsay_issue_count += 1

        # priority actions
        for req in self._requirements:
            if req.overall_status == AuthStatus.AT_RISK:
                report.priority_actions.append(
                    f"Exhibit {req.exhibit_number or req.item_id}: "
                    f"AT RISK — {'; '.join(req.issues)}"
                )

        self._report = report
        return report

    def to_markdown(self) -> str:
        """Render the report as Markdown."""
        if not self._report:
            self.generate_report()
        assert self._report is not None
        r = self._report

        lines: List[str] = [
            "## Evidence Authentication Report",
            f"### Generated: {r.generated_at[:10]} | Exhibits: {r.total_exhibits}",
            "",
            "#### Summary",
            f"- Ready for admission: {r.ready_count}",
            f"- Needs additional work: {r.needs_work_count}",
            f"- At risk of exclusion: {r.at_risk_count}",
            f"- Chain-of-custody gaps: {r.custody_gap_count}",
            f"- Hearsay challenges: {r.hearsay_issue_count}",
            "",
            "| # | Exhibit | Type | Auth Method | CoC | Hearsay | Status |",
            "|---|---------|------|------------|-----|---------|--------|",
        ]
        for i, req in enumerate(r.requirements, 1):
            hearsay_str = (
                "None"
                if req.hearsay_resolved
                else ", ".join(h.value for h in req.hearsay_issues)
            )
            lines.append(
                f"| {i} | {req.exhibit_number or req.item_id} | "
                f"{req.evidence_type.value} | {req.primary_method.value} | "
                f"{req.custody_status.value} | {hearsay_str} | "
                f"{req.overall_status.value} |"
            )
        lines.append("")

        if r.priority_actions:
            lines.append("#### Priority Actions")
            for action in r.priority_actions:
                lines.append(f"- {action}")

        return "\n".join(lines)

    # -- persistence --

    def persist(self) -> int:
        """Write authentication requirements to the database."""
        if not self._db_path.exists():
            logger.warning("Database not found — cannot persist")
            return 0

        try:
            conn = sqlite3.connect(str(self._db_path), timeout=60)
            conn.execute("PRAGMA busy_timeout=60000")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA cache_size=-32000")
        except sqlite3.Error as exc:
            logger.error("DB connection failed: %s", exc)
            return 0

        try:
            _ensure_table(conn)
            rows: List[Tuple[Any, ...]] = []
            for req in self._requirements:
                rows.append((
                    uuid.uuid4().hex[:12],
                    req.item_id,
                    req.exhibit_number,
                    req.title,
                    req.evidence_type.value,
                    req.primary_method.value,
                    req.primary_method.value,
                    json.dumps([c.to_dict() for c in req.custody_chain]),
                    json.dumps([h.value for h in req.hearsay_issues]),
                    req.best_evidence.value,
                    req.foundation_notes[:500] if req.foundation_notes else "",
                    req.overall_status.value,
                    req.lane,
                    req.case_number,
                ))
            conn.executemany(
                "INSERT OR IGNORE INTO evidence_authentication "
                "(auth_id, exhibit_id, exhibit_number, exhibit_desc, "
                "evidence_type, auth_method, mre_section, chain_of_custody, "
                "hearsay_exception, best_evidence, foundation_notes, status, "
                "lane, case_number) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
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
        return {
            "module": "evidence_authenticator",
            "items_loaded": len(self._items),
            "requirements_analysed": len(self._requirements),
            "report_generated": self._report is not None,
            "ready": self._report.ready_count if self._report else 0,
            "at_risk": self._report.at_risk_count if self._report else 0,
            "db_path": str(self._db_path),
            "auth_analyzer": self._auth_analyzer.get_stats(),
            "hearsay_analyzer": self._hearsay_analyzer.get_stats(),
            "foundation_builder": self._foundation_builder.get_stats(),
        }

    def reset(self) -> None:
        self._items.clear()
        self._requirements.clear()
        self._report = None


# ---------------------------------------------------------------------------
# CLI demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sys.stdout = open(  # noqa: SIM115
        sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace"
    )
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print("=" * 60)
    print("  Evidence Authenticator — LitigationOS")
    print("=" * 60)
    print()

    demo_items = [
        EvidenceItem(
            exhibit_number="A-001",
            title="Text messages re: parenting time — June 2024",
            description="Screenshots of text messages between Plaintiff and Defendant",
            evidence_type=EvidenceType.TEXT_MESSAGE,
            lane="A",
            case_number="2024-001507-DC",
            date_obtained="2024-06-20",
            obtained_by=_PLAINTIFF,
            storage_location="C:\\Users\\andre\\LitigationOS\\10_Exhibits",
        ),
        EvidenceItem(
            exhibit_number="A-002",
            title="FOC Recommendation — August 2024",
            description="Friend of Court custody recommendation",
            evidence_type=EvidenceType.GOVERNMENT_RECORD,
            lane="A",
            case_number="2024-001507-DC",
            date_obtained="2024-08-15",
        ),
        EvidenceItem(
            exhibit_number="D-001",
            title="Police report — PPO incident",
            description="North Muskegon PD incident report",
            evidence_type=EvidenceType.POLICE_REPORT,
            lane="D",
            case_number="2023-5907-PP",
        ),
        EvidenceItem(
            exhibit_number="B-001",
            title="Shady Oaks lease agreement",
            description="Lease agreement for Lot 17, Shady Oaks",
            evidence_type=EvidenceType.BUSINESS_RECORD,
            lane="B",
            case_number="2025-002760-CZ",
            is_original=False,
        ),
    ]

    authenticator = EvidenceAuthenticator()
    authenticator.add_items(demo_items)
    authenticator.analyse_all()

    print(authenticator.to_markdown())
    print()
    print("--- Stats ---")
    import pprint

    pprint.pprint(authenticator.get_stats())
