# -*- coding: utf-8 -*-
"""
Appellate Record Builder — LitigationOS Legal AI Subsystem
============================================================
Appellate record compilation and organization for Michigan Court
of Appeals.  Handles register of actions, transcript management,
exhibit compilation, record pagination, and completeness verification
per Michigan Court Rules.

Case Context
------------
    Plaintiff:  Andrew James Pigors (Pro Se)
    Defendant:  Emily A. Watson
    Child:      L.D.W. (per MCR 8.119(H)) — Male
    Judge:      Hon. Jenny L. McNeill — 14th Circuit Court
    Cases:      2024-001507-DC, 2025-002760-CZ, 2023-5907-PP, COA 366810

Michigan Rules
--------------
    MCR 7.210  – The Record on Appeal
    MCR 7.210(A) – Record must be paginated consecutively
    MCR 7.210(B) – 7 days to order transcripts after claim of appeal
    MCR 7.212(C) – Appendix requirements for briefs
    MCR 7.204(A) – Time for filing claim of appeal (21 days)
    MCR 7.204(D) – Entry requirements for claim of appeal
    MCR 7.208  – Motions in the Court of Appeals
    MCR 7.209  – Stays and injunctions pending appeal
    COA Internal Operating Procedures (IOPs)

Usage::

    from legal_ai.appellate_record_builder import AppellateRecordBuilder

    builder = AppellateRecordBuilder()
    record = builder.build_record(case_number="COA 366810")
    index = builder.generate_index()

Zero external dependencies.  CPU-first.  Local-only.
"""
from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import sys
import uuid
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

logger = logging.getLogger("legal_ai.appellate_record_builder")

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
_COA_CASE = "COA 366810"

LANE_CASES: Dict[str, str] = {
    "A": "2024-001507-DC",
    "B": "2025-002760-CZ",
    "C": "Convergence",
    "D": "2023-5907-PP",
    "E": "JTC / Misconduct",
    "F": "COA 366810",
}

# ---------------------------------------------------------------------------
# MCR deadlines and limits
# ---------------------------------------------------------------------------
_TRANSCRIPT_ORDER_DAYS = 7      # MCR 7.210(B)(1)
_CLAIM_OF_APPEAL_DAYS = 21      # MCR 7.204(A)(1)
_RECORD_PREPARATION_DAYS = 56   # MCR 7.210(C)(1) — 56 days for record prep
_APPENDIX_PAGE_LIMIT = 50       # MCR 7.212(C)(8) — unless leave granted
_VOLUME_PAGE_LIMIT = 200        # recommended pages per volume

# ---------------------------------------------------------------------------
# Record organization constants
# ---------------------------------------------------------------------------
_RECORD_SECTIONS: Dict[str, int] = {
    "register_of_actions": 1,
    "pleadings": 2,
    "motions": 3,
    "orders": 4,
    "transcripts": 5,
    "exhibits": 6,
    "briefs": 7,
    "other": 8,
}


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class RecordType(str, Enum):
    """Types of documents in the appellate record."""

    REGISTER_OF_ACTIONS = "register_of_actions"
    TRANSCRIPT = "transcript"
    EXHIBIT = "exhibit"
    PLEADING = "pleading"
    ORDER = "order"
    MOTION = "motion"
    BRIEF = "brief"

    @property
    def mcr_reference(self) -> str:
        _refs = {
            "register_of_actions": "MCR 7.210(A)(1)",
            "transcript": "MCR 7.210(B)",
            "exhibit": "MCR 7.210(A)(3)",
            "pleading": "MCR 7.210(A)(1)",
            "order": "MCR 7.210(A)(1)",
            "motion": "MCR 7.210(A)(1)",
            "brief": "MCR 7.212(C)",
        }
        return _refs.get(self.value, "MCR 7.210")


class TranscriptStatus(str, Enum):
    """Status of transcript ordering and production."""

    NOT_ORDERED = "not_ordered"
    ORDERED = "ordered"
    RECEIVED = "received"
    CERTIFIED = "certified"
    MISSING = "missing"
    WAIVED = "waived"


class RecordBuildStatus(str, Enum):
    """Overall record build status."""

    PLANNING = "planning"
    COLLECTING = "collecting"
    PAGINATING = "paginating"
    REVIEWING = "reviewing"
    CERTIFIED = "certified"
    FILED = "filed"
    DEFICIENT = "deficient"


class CompletionIssue(str, Enum):
    """Types of record completion issues."""

    MISSING_TRANSCRIPT = "missing_transcript"
    MISSING_EXHIBIT = "missing_exhibit"
    MISSING_ORDER = "missing_order"
    PAGINATION_GAP = "pagination_gap"
    CERTIFICATION_MISSING = "certification_missing"
    REGISTER_INCOMPLETE = "register_incomplete"
    BATES_ERROR = "bates_error"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class RecordEntry:
    """A single entry in the appellate record."""

    entry_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    record_type: RecordType = RecordType.PLEADING
    title: str = ""
    date: str = ""
    page_start: int = 0
    page_end: int = 0
    volume: int = 1
    bates_number: str = ""
    original_path: str = ""
    description: str = ""
    filed_by: str = ""
    is_certified: bool = False
    content_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "record_type": self.record_type.value,
            "title": self.title,
            "date": self.date,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "volume": self.volume,
            "bates_number": self.bates_number,
            "original_path": self.original_path,
            "description": self.description,
            "filed_by": self.filed_by,
            "is_certified": self.is_certified,
            "content_hash": self.content_hash,
        }

    @property
    def page_count(self) -> int:
        if self.page_end >= self.page_start > 0:
            return self.page_end - self.page_start + 1
        return 0


@dataclass
class TranscriptRecord:
    """Tracking record for a hearing transcript."""

    transcript_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    hearing_date: str = ""
    hearing_type: str = ""
    judge: str = _JUDGE
    court_reporter: str = ""
    status: TranscriptStatus = TranscriptStatus.NOT_ORDERED
    ordered_date: str = ""
    received_date: str = ""
    page_count: int = 0
    cost: str = "0.00"
    certification_date: str = ""
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transcript_id": self.transcript_id,
            "hearing_date": self.hearing_date,
            "hearing_type": self.hearing_type,
            "judge": self.judge,
            "court_reporter": self.court_reporter,
            "status": self.status.value,
            "ordered_date": self.ordered_date,
            "received_date": self.received_date,
            "page_count": self.page_count,
            "cost": self.cost,
            "certification_date": self.certification_date,
            "notes": self.notes,
        }

    @property
    def is_overdue(self) -> bool:
        """Check if transcript order deadline has passed."""
        if self.status == TranscriptStatus.NOT_ORDERED and self.hearing_date:
            try:
                hd = date.fromisoformat(self.hearing_date)
                return (date.today() - hd).days > _TRANSCRIPT_ORDER_DAYS
            except ValueError:
                return False
        return False


@dataclass
class VolumeInfo:
    """Metadata for a single volume of the record."""

    volume_number: int = 1
    page_start: int = 1
    page_end: int = 0
    entry_count: int = 0
    title: str = ""
    entries: List[str] = field(default_factory=list)  # entry_ids

    def to_dict(self) -> Dict[str, Any]:
        return {
            "volume_number": self.volume_number,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "entry_count": self.entry_count,
            "title": self.title,
            "entries": self.entries,
        }


@dataclass
class CompletionReport:
    """Report on record completeness."""

    report_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    case_number: str = ""
    is_complete: bool = False
    issues: List[Dict[str, Any]] = field(default_factory=list)
    total_entries: int = 0
    total_pages: int = 0
    total_volumes: int = 0
    missing_items: List[str] = field(default_factory=list)
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "case_number": self.case_number,
            "is_complete": self.is_complete,
            "issues": self.issues,
            "total_entries": self.total_entries,
            "total_pages": self.total_pages,
            "total_volumes": self.total_volumes,
            "missing_items": self.missing_items,
            "generated_at": self.generated_at,
        }


# ---------------------------------------------------------------------------
# RegisterOfActions
# ---------------------------------------------------------------------------


class RegisterOfActions:
    """Build and verify the Register of Actions (docket sheet).

    MCR 7.210(A)(1) requires the register of actions as the first
    document in the appellate record.  It lists every filing in
    chronological order.
    """

    def __init__(self) -> None:
        self._entries: List[Dict[str, Any]] = []

    def build_from_docket(
        self,
        docket_entries: Optional[List[Dict[str, str]]] = None,
    ) -> List[Dict[str, Any]]:
        """Build the register from raw docket entries.

        Each docket entry should have: date, description, filed_by, document_type.
        """
        entries = docket_entries or []
        register: List[Dict[str, Any]] = []

        for idx, entry in enumerate(entries, 1):
            reg_entry = {
                "line_number": idx,
                "date": entry.get("date", ""),
                "description": entry.get("description", ""),
                "filed_by": entry.get("filed_by", ""),
                "document_type": entry.get("document_type", ""),
                "entry_id": uuid.uuid4().hex[:10],
            }
            register.append(reg_entry)

        # Sort by date
        register.sort(key=lambda x: x.get("date", ""))
        self._entries = register
        logger.info("Built register of actions with %d entries", len(register))
        return register

    def verify_completeness(
        self,
        expected_filings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Verify the register against expected filings."""
        expected = expected_filings or []
        descriptions = {e["description"].lower() for e in self._entries}
        missing: List[str] = []

        for filing in expected:
            if not any(filing.lower() in d for d in descriptions):
                missing.append(filing)

        return {
            "total_entries": len(self._entries),
            "expected_filings": len(expected),
            "missing_filings": missing,
            "is_complete": len(missing) == 0,
            "legal_basis": "MCR 7.210(A)(1)",
        }

    def identify_missing_entries(
        self,
        orders: List[str],
        motions: List[str],
    ) -> List[Dict[str, Any]]:
        """Identify entries that should appear but are missing."""
        missing: List[Dict[str, Any]] = []
        descriptions = {e["description"].lower() for e in self._entries}

        for order in orders:
            if not any(order.lower() in d for d in descriptions):
                missing.append({
                    "type": "order",
                    "description": order,
                    "severity": "high",
                    "note": "All orders must appear in the register — MCR 7.210(A)(1)",
                })

        for motion in motions:
            if not any(motion.lower() in d for d in descriptions):
                missing.append({
                    "type": "motion",
                    "description": motion,
                    "severity": "medium",
                    "note": "Contested motions should appear in the register",
                })

        return missing

    def generate_certified_copy(self) -> Dict[str, Any]:
        """Generate metadata for a certified copy of the register."""
        content = json.dumps(self._entries, sort_keys=True)
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

        return {
            "document": "Certified Register of Actions",
            "entry_count": len(self._entries),
            "content_hash": content_hash,
            "certification_text": (
                "I hereby certify that this is a true and complete copy "
                "of the Register of Actions in the above-captioned case."
            ),
            "court": _COURT,
            "legal_basis": "MCR 7.210(A)(1)",
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "RegisterOfActions",
            "total_entries": len(self._entries),
        }


# ---------------------------------------------------------------------------
# TranscriptManager
# ---------------------------------------------------------------------------


class TranscriptManager:
    """Manage hearing transcript ordering, tracking, and verification.

    MCR 7.210(B)(1): Within 7 days after filing a claim of appeal,
    the appellant must order the full transcript of testimony or file
    a description of the issues to be raised and order the relevant
    portions.
    """

    def __init__(self) -> None:
        self._transcripts: List[TranscriptRecord] = []

    def inventory_transcripts(
        self,
        hearings: Optional[List[Dict[str, str]]] = None,
    ) -> List[TranscriptRecord]:
        """Create an inventory of required transcripts.

        Parameters
        ----------
        hearings : list of dicts with hearing_date, hearing_type, judge, reporter
        """
        hearing_list = hearings or []
        transcripts: List[TranscriptRecord] = []

        for h in hearing_list:
            tr = TranscriptRecord(
                hearing_date=h.get("hearing_date", ""),
                hearing_type=h.get("hearing_type", ""),
                judge=h.get("judge", _JUDGE),
                court_reporter=h.get("court_reporter", ""),
            )
            transcripts.append(tr)

        self._transcripts.extend(transcripts)
        logger.info("Inventoried %d transcripts", len(transcripts))
        return transcripts

    def order_missing(self) -> List[Dict[str, Any]]:
        """Generate ordering instructions for un-ordered transcripts.

        MCR 7.210(B)(1) requires ordering within 7 days of claim of appeal.
        """
        to_order: List[Dict[str, Any]] = []

        for tr in self._transcripts:
            if tr.status == TranscriptStatus.NOT_ORDERED:
                to_order.append({
                    "transcript_id": tr.transcript_id,
                    "hearing_date": tr.hearing_date,
                    "hearing_type": tr.hearing_type,
                    "court_reporter": tr.court_reporter,
                    "is_overdue": tr.is_overdue,
                    "instructions": [
                        f"Contact court reporter ({tr.court_reporter or 'TBD'}) "
                        f"to order transcript of {tr.hearing_type} hearing "
                        f"on {tr.hearing_date}.",
                        "Pay deposit as required by court reporter.",
                        f"Deadline: {_TRANSCRIPT_ORDER_DAYS} days from claim of appeal — MCR 7.210(B)(1).",
                    ],
                    "legal_basis": "MCR 7.210(B)(1)",
                })

        return to_order

    def verify_certification(self) -> List[Dict[str, Any]]:
        """Verify all transcripts are properly certified.

        MCR 7.210(B)(2) requires certification by the court reporter.
        """
        issues: List[Dict[str, Any]] = []

        for tr in self._transcripts:
            if tr.status == TranscriptStatus.RECEIVED and not tr.certification_date:
                issues.append({
                    "transcript_id": tr.transcript_id,
                    "hearing_date": tr.hearing_date,
                    "issue": "Transcript received but not certified",
                    "action": "Request certification from court reporter",
                    "legal_basis": "MCR 7.210(B)(2)",
                })
            elif tr.status == TranscriptStatus.MISSING:
                issues.append({
                    "transcript_id": tr.transcript_id,
                    "hearing_date": tr.hearing_date,
                    "issue": "Transcript missing — not produced",
                    "action": "File motion for settled statement per MCR 7.210(B)(4)",
                    "legal_basis": "MCR 7.210(B)(4)",
                })

        return issues

    def calculate_costs(self) -> Dict[str, Any]:
        """Calculate total transcript costs."""
        from decimal import Decimal

        total = Decimal("0")
        breakdown: List[Dict[str, str]] = []

        for tr in self._transcripts:
            cost = Decimal(tr.cost) if tr.cost else Decimal("0")
            total += cost
            if cost > 0:
                breakdown.append({
                    "hearing_date": tr.hearing_date,
                    "hearing_type": tr.hearing_type,
                    "pages": str(tr.page_count),
                    "cost": str(cost),
                })

        return {
            "total_cost": str(total),
            "transcript_count": len(self._transcripts),
            "breakdown": breakdown,
            "note": "Costs recoverable as taxable costs if prevailing — MCR 7.219",
        }

    def track_ordering_deadlines(
        self, claim_of_appeal_date: str = "",
    ) -> List[Dict[str, Any]]:
        """Track transcript ordering deadlines from claim of appeal.

        MCR 7.210(B)(1): 7 days from filing claim of appeal.
        """
        deadlines: List[Dict[str, Any]] = []

        if claim_of_appeal_date:
            try:
                coa_date = date.fromisoformat(claim_of_appeal_date)
            except ValueError:
                coa_date = date.today()
        else:
            coa_date = date.today()

        order_deadline = coa_date + timedelta(days=_TRANSCRIPT_ORDER_DAYS)

        for tr in self._transcripts:
            if tr.status == TranscriptStatus.NOT_ORDERED:
                days_remaining = (order_deadline - date.today()).days
                deadlines.append({
                    "transcript_id": tr.transcript_id,
                    "hearing_date": tr.hearing_date,
                    "order_deadline": order_deadline.isoformat(),
                    "days_remaining": days_remaining,
                    "is_overdue": days_remaining < 0,
                    "urgency": "critical" if days_remaining < 0 else (
                        "high" if days_remaining <= 2 else "normal"
                    ),
                    "legal_basis": "MCR 7.210(B)(1)",
                })

        return deadlines

    def update_status(
        self, transcript_id: str, new_status: TranscriptStatus,
        received_date: str = "", certification_date: str = "",
        page_count: int = 0, cost: str = "0.00",
    ) -> Optional[TranscriptRecord]:
        """Update status of a transcript."""
        for tr in self._transcripts:
            if tr.transcript_id == transcript_id:
                tr.status = new_status
                if received_date:
                    tr.received_date = received_date
                if certification_date:
                    tr.certification_date = certification_date
                if page_count:
                    tr.page_count = page_count
                if cost != "0.00":
                    tr.cost = cost
                return tr
        return None

    def get_stats(self) -> Dict[str, Any]:
        by_status: Dict[str, int] = {}
        for tr in self._transcripts:
            by_status[tr.status.value] = by_status.get(tr.status.value, 0) + 1
        return {
            "component": "TranscriptManager",
            "total_transcripts": len(self._transcripts),
            "by_status": by_status,
        }


# ---------------------------------------------------------------------------
# ExhibitCompiler
# ---------------------------------------------------------------------------


class ExhibitCompiler:
    """Compile and organize exhibits for the appellate record.

    Applies Bates numbering, creates exhibit indexes, and verifies
    that all exhibits marked as admitted are included.
    """

    def __init__(self, bates_prefix: str = "PIGORS") -> None:
        self._prefix = bates_prefix
        self._exhibits: List[RecordEntry] = []
        self._next_bates: int = 1

    def collect_exhibits(
        self,
        exhibits: Optional[List[Dict[str, str]]] = None,
    ) -> List[RecordEntry]:
        """Collect exhibits from a list of metadata dicts.

        Each dict: title, date, original_path, filed_by, description.
        """
        exhibit_list = exhibits or []
        collected: List[RecordEntry] = []

        for ex in exhibit_list:
            entry = RecordEntry(
                record_type=RecordType.EXHIBIT,
                title=ex.get("title", ""),
                date=ex.get("date", ""),
                original_path=ex.get("original_path", ""),
                filed_by=ex.get("filed_by", _PLAINTIFF),
                description=ex.get("description", ""),
            )
            collected.append(entry)

        self._exhibits.extend(collected)
        logger.info("Collected %d exhibits", len(collected))
        return collected

    def apply_bates_numbers(self) -> List[RecordEntry]:
        """Apply sequential Bates numbers to all exhibits.

        Format: {PREFIX}-{NNNN} (e.g., PIGORS-0001).
        """
        for exhibit in self._exhibits:
            if not exhibit.bates_number:
                exhibit.bates_number = f"{self._prefix}-{self._next_bates:04d}"
                self._next_bates += 1

        logger.info(
            "Applied Bates numbers: %s-0001 through %s-%04d",
            self._prefix, self._prefix, self._next_bates - 1,
        )
        return list(self._exhibits)

    def create_exhibit_index(self) -> List[Dict[str, Any]]:
        """Create an exhibit index (table of exhibits).

        Returns a list suitable for inclusion in the appellate brief
        per MCR 7.212(C).
        """
        index: List[Dict[str, Any]] = []
        for exhibit in sorted(self._exhibits, key=lambda e: e.bates_number):
            index.append({
                "bates_number": exhibit.bates_number,
                "title": exhibit.title,
                "date": exhibit.date,
                "filed_by": exhibit.filed_by,
                "page_start": exhibit.page_start,
                "page_end": exhibit.page_end,
                "description": exhibit.description,
            })
        return index

    def verify_admitted_status(
        self,
        admitted_exhibit_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Verify that all admitted exhibits are in the record.

        Compares list of exhibits marked admitted at trial against
        those compiled in the record.
        """
        admitted = admitted_exhibit_ids or []
        compiled_ids = {e.entry_id for e in self._exhibits}
        missing = [eid for eid in admitted if eid not in compiled_ids]

        return {
            "total_compiled": len(self._exhibits),
            "total_admitted": len(admitted),
            "missing_from_record": missing,
            "is_complete": len(missing) == 0,
            "note": "All admitted exhibits must be in the record — MCR 7.210(A)(3)",
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "ExhibitCompiler",
            "total_exhibits": len(self._exhibits),
            "next_bates": self._next_bates,
            "bates_prefix": self._prefix,
        }


# ---------------------------------------------------------------------------
# RecordPaginator
# ---------------------------------------------------------------------------


class RecordPaginator:
    """Paginate the appellate record into consecutively numbered volumes.

    MCR 7.210(A) requires the record to be paginated consecutively.
    This engine assigns page numbers and divides the record into
    manageable volumes.
    """

    def __init__(self, pages_per_volume: int = _VOLUME_PAGE_LIMIT) -> None:
        self._pages_per_volume = pages_per_volume
        self._entries: List[RecordEntry] = []
        self._volumes: List[VolumeInfo] = []
        self._next_page: int = 1

    def paginate_record(
        self,
        entries: List[RecordEntry],
    ) -> List[RecordEntry]:
        """Assign consecutive page numbers to all record entries.

        Entries are sorted by: section order, then date, then title.
        Page numbers are assigned sequentially across the entire record.
        """
        # Sort by section order → date → title
        def sort_key(e: RecordEntry) -> Tuple[int, str, str]:
            section = _RECORD_SECTIONS.get(e.record_type.value, 8)
            return (section, e.date, e.title)

        sorted_entries = sorted(entries, key=sort_key)
        current_page = 1

        for entry in sorted_entries:
            if entry.page_count > 0:
                entry.page_start = current_page
                entry.page_end = current_page + entry.page_count - 1
                current_page = entry.page_end + 1
            elif entry.page_start == 0:
                # Single-page entry
                entry.page_start = current_page
                entry.page_end = current_page
                current_page += 1

        self._entries = sorted_entries
        self._next_page = current_page
        logger.info("Paginated %d entries: pages 1–%d", len(sorted_entries), current_page - 1)
        return sorted_entries

    def create_volumes(self) -> List[VolumeInfo]:
        """Divide paginated entries into volumes.

        Each volume contains up to ``pages_per_volume`` pages.
        """
        if not self._entries:
            return []

        volumes: List[VolumeInfo] = []
        vol_num = 1
        vol_start = 1
        vol_entries: List[str] = []
        vol_page_end = 0

        for entry in self._entries:
            # Check if this entry would push us over the volume limit
            if entry.page_start > vol_start + self._pages_per_volume - 1 and vol_entries:
                vol = VolumeInfo(
                    volume_number=vol_num,
                    page_start=vol_start,
                    page_end=vol_page_end,
                    entry_count=len(vol_entries),
                    title=f"Volume {vol_num}",
                    entries=list(vol_entries),
                )
                volumes.append(vol)
                vol_num += 1
                vol_start = entry.page_start
                vol_entries = []

            entry.volume = vol_num
            vol_entries.append(entry.entry_id)
            vol_page_end = entry.page_end

        # Final volume
        if vol_entries:
            vol = VolumeInfo(
                volume_number=vol_num,
                page_start=vol_start,
                page_end=vol_page_end,
                entry_count=len(vol_entries),
                title=f"Volume {vol_num}",
                entries=list(vol_entries),
            )
            volumes.append(vol)

        self._volumes = volumes
        logger.info("Created %d volume(s)", len(volumes))
        return volumes

    def generate_toc(self) -> List[Dict[str, Any]]:
        """Generate table of contents for the record."""
        toc: List[Dict[str, Any]] = []

        for entry in self._entries:
            toc.append({
                "title": entry.title,
                "record_type": entry.record_type.value,
                "date": entry.date,
                "page_start": entry.page_start,
                "page_end": entry.page_end,
                "volume": entry.volume,
                "bates_number": entry.bates_number,
            })

        return toc

    def create_cover_pages(self) -> List[Dict[str, Any]]:
        """Generate cover page data for each volume."""
        covers: List[Dict[str, Any]] = []

        for vol in self._volumes:
            cover = {
                "volume_number": vol.volume_number,
                "total_volumes": len(self._volumes),
                "title": f"Record on Appeal — Volume {vol.volume_number} of {len(self._volumes)}",
                "case_number": _COA_CASE,
                "court": "Michigan Court of Appeals",
                "lower_court": _COURT,
                "lower_court_case": LANE_CASES["A"],
                "appellant": _PLAINTIFF,
                "appellee": _DEFENDANT,
                "judge": _JUDGE,
                "page_range": f"pp. {vol.page_start}–{vol.page_end}",
                "mcr_reference": "MCR 7.210(A)",
            }
            covers.append(cover)

        return covers

    def get_stats(self) -> Dict[str, Any]:
        total_pages = self._next_page - 1 if self._next_page > 1 else 0
        return {
            "component": "RecordPaginator",
            "total_entries": len(self._entries),
            "total_pages": total_pages,
            "total_volumes": len(self._volumes),
            "pages_per_volume": self._pages_per_volume,
        }


# ---------------------------------------------------------------------------
# RecordCompletionChecker
# ---------------------------------------------------------------------------


class RecordCompletionChecker:
    """Verify the appellate record for completeness.

    Checks against the register of actions, identifies gaps in
    pagination, and ensures all required certifications exist.
    """

    def __init__(self) -> None:
        self._issues: List[Dict[str, Any]] = []

    def verify_against_register(
        self,
        record_entries: List[RecordEntry],
        register_entries: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Verify record entries against the register of actions.

        Every item in the register that is relevant to the appeal
        should appear in the record.
        """
        record_titles = {e.title.lower() for e in record_entries}
        missing: List[Dict[str, Any]] = []

        for reg in register_entries:
            desc = reg.get("description", "").lower()
            if desc and not any(desc in rt or rt in desc for rt in record_titles):
                missing.append({
                    "register_entry": reg.get("description", ""),
                    "date": reg.get("date", ""),
                    "issue": CompletionIssue.REGISTER_INCOMPLETE.value,
                    "severity": "medium",
                })

        if missing:
            self._issues.extend(missing)

        return {
            "record_entries": len(record_entries),
            "register_entries": len(register_entries),
            "missing_from_record": len(missing),
            "missing_items": missing,
            "is_complete": len(missing) == 0,
        }

    def identify_gaps(
        self, entries: List[RecordEntry],
    ) -> List[Dict[str, Any]]:
        """Identify pagination gaps in the record."""
        if not entries:
            return []

        sorted_entries = sorted(entries, key=lambda e: e.page_start)
        gaps: List[Dict[str, Any]] = []
        expected_next = 1

        for entry in sorted_entries:
            if entry.page_start > expected_next:
                gap = {
                    "gap_start": expected_next,
                    "gap_end": entry.page_start - 1,
                    "missing_pages": entry.page_start - expected_next,
                    "issue": CompletionIssue.PAGINATION_GAP.value,
                    "before_entry": entry.title,
                    "severity": "high",
                }
                gaps.append(gap)
                self._issues.append(gap)
            expected_next = entry.page_end + 1

        return gaps

    def generate_certification(
        self, case_number: str = "",
    ) -> Dict[str, Any]:
        """Generate record certification per MCR 7.210(C)."""
        has_issues = len(self._issues) > 0
        return {
            "document": "Certification of Record on Appeal",
            "case_number": case_number or _COA_CASE,
            "court": "Michigan Court of Appeals",
            "lower_court": _COURT,
            "lower_court_judge": _JUDGE,
            "certifier": "Clerk of the Court",
            "certification_text": (
                "I hereby certify that the foregoing record on appeal "
                "is a true, complete, and accurate copy of the documents, "
                "transcripts, and exhibits filed in the lower court in the "
                "above-captioned matter."
            ),
            "has_issues": has_issues,
            "issue_count": len(self._issues),
            "legal_basis": "MCR 7.210(C)",
        }

    def create_settled_statement(
        self,
        missing_transcripts: Optional[List[str]] = None,
        proposed_narrative: str = "",
    ) -> Dict[str, Any]:
        """Create a settled statement when transcripts are unavailable.

        MCR 7.210(B)(4): If a transcript is unavailable, the appellant
        may prepare a settled statement of facts.
        """
        return {
            "document": "Settled Statement of Facts",
            "case_number": _COA_CASE,
            "missing_transcripts": missing_transcripts or [],
            "proposed_narrative": proposed_narrative,
            "instructions": [
                "Prepare a proposed statement of facts from memory, notes, and exhibits.",
                "Serve the proposed statement on opposing counsel.",
                "Opposing counsel has 14 days to object or propose amendments.",
                "If no agreement, submit to the trial court for settlement.",
                "The settled statement replaces the missing transcript in the record.",
            ],
            "legal_basis": "MCR 7.210(B)(4)",
            "filing_deadline": "Within 28 days of notice that transcript is unavailable",
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "RecordCompletionChecker",
            "total_issues_found": len(self._issues),
        }


# ---------------------------------------------------------------------------
# AppellateRecordBuilder  (main orchestrator)
# ---------------------------------------------------------------------------


class AppellateRecordBuilder:
    """Top-level orchestrator for building the appellate record.

    Combines :class:`RegisterOfActions`, :class:`TranscriptManager`,
    :class:`ExhibitCompiler`, :class:`RecordPaginator`, and
    :class:`RecordCompletionChecker` into a unified record-building
    system for Michigan Court of Appeals proceedings.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or _DB_PATH
        self._register = RegisterOfActions()
        self._transcript_mgr = TranscriptManager()
        self._exhibit_compiler = ExhibitCompiler()
        self._paginator = RecordPaginator()
        self._checker = RecordCompletionChecker()
        self._entries: List[RecordEntry] = []
        self._build_status: RecordBuildStatus = RecordBuildStatus.PLANNING
        self._case_number: str = _COA_CASE

    # -- DB helpers --

    def _get_db(self) -> sqlite3.Connection:
        """Open a WAL-mode connection with safe PRAGMAs."""
        conn = sqlite3.connect(str(self._db_path), timeout=60)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("PRAGMA cache_size=-32000")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.row_factory = sqlite3.Row
        return conn

    # -- record construction --

    def build_record(
        self,
        case_number: str = "",
        docket_entries: Optional[List[Dict[str, str]]] = None,
        hearings: Optional[List[Dict[str, str]]] = None,
        exhibits: Optional[List[Dict[str, str]]] = None,
        claim_of_appeal_date: str = "",
    ) -> Dict[str, Any]:
        """Build the complete appellate record.

        Parameters
        ----------
        case_number : str
        docket_entries : list of docket entry dicts
        hearings : list of hearing dicts for transcript tracking
        exhibits : list of exhibit metadata dicts
        claim_of_appeal_date : str — ISO date of claim of appeal

        Returns
        -------
        dict with record summary
        """
        self._case_number = case_number or _COA_CASE
        self._build_status = RecordBuildStatus.COLLECTING

        # 1. Build register of actions
        register = self._register.build_from_docket(docket_entries)

        # 2. Inventory transcripts
        transcripts = self._transcript_mgr.inventory_transcripts(hearings)

        # 3. Collect exhibits
        collected_exhibits = self._exhibit_compiler.collect_exhibits(exhibits)
        self._exhibit_compiler.apply_bates_numbers()

        # 4. Convert all to RecordEntry list
        all_entries: List[RecordEntry] = []

        # Register of actions as single entry
        if register:
            roa_entry = RecordEntry(
                record_type=RecordType.REGISTER_OF_ACTIONS,
                title="Register of Actions",
                date=date.today().isoformat(),
                description=f"Register of Actions — {len(register)} entries",
            )
            all_entries.append(roa_entry)

        # Transcripts as entries
        for tr in transcripts:
            tr_entry = RecordEntry(
                record_type=RecordType.TRANSCRIPT,
                title=f"Transcript — {tr.hearing_type} ({tr.hearing_date})",
                date=tr.hearing_date,
                description=f"Transcript of {tr.hearing_type} before {tr.judge}",
            )
            if tr.page_count > 0:
                tr_entry.page_end = tr_entry.page_start + tr.page_count - 1
            all_entries.append(tr_entry)

        # Exhibits
        all_entries.extend(collected_exhibits)

        # 5. Paginate
        self._build_status = RecordBuildStatus.PAGINATING
        paginated = self._paginator.paginate_record(all_entries)
        volumes = self._paginator.create_volumes()

        self._entries = paginated
        self._build_status = RecordBuildStatus.REVIEWING

        # 6. Track transcript deadlines
        deadlines = self._transcript_mgr.track_ordering_deadlines(claim_of_appeal_date)

        result = {
            "case_number": self._case_number,
            "status": self._build_status.value,
            "total_entries": len(paginated),
            "total_pages": self._paginator.get_stats()["total_pages"],
            "total_volumes": len(volumes),
            "transcript_count": len(transcripts),
            "exhibit_count": len(collected_exhibits),
            "transcript_deadlines": deadlines,
            "mcr_reference": "MCR 7.210",
        }

        logger.info(
            "Built record for %s: %d entries, %d pages, %d volumes",
            self._case_number,
            len(paginated),
            result["total_pages"],
            len(volumes),
        )
        return result

    def compile_appendix(
        self,
        key_documents: Optional[List[RecordEntry]] = None,
    ) -> Dict[str, Any]:
        """Compile the brief appendix per MCR 7.212(C).

        The appendix to the brief must contain the relevant portions
        of the record cited in the brief, subject to the page limit
        unless leave is granted.
        """
        docs = key_documents or self._entries[:10]

        appendix_entries: List[Dict[str, Any]] = []
        total_pages = 0

        for doc in docs:
            pages = doc.page_count if doc.page_count > 0 else 1
            if total_pages + pages > _APPENDIX_PAGE_LIMIT:
                logger.warning(
                    "Appendix page limit (%d) reached — truncating",
                    _APPENDIX_PAGE_LIMIT,
                )
                break

            appendix_entries.append({
                "title": doc.title,
                "record_type": doc.record_type.value,
                "page_start": doc.page_start,
                "page_end": doc.page_end,
                "bates_number": doc.bates_number,
            })
            total_pages += pages

        return {
            "appendix_title": f"Appendix — {self._case_number}",
            "total_entries": len(appendix_entries),
            "total_pages": total_pages,
            "page_limit": _APPENDIX_PAGE_LIMIT,
            "within_limit": total_pages <= _APPENDIX_PAGE_LIMIT,
            "entries": appendix_entries,
            "legal_basis": "MCR 7.212(C)",
            "note": (
                "If appendix exceeds 50 pages, file motion for leave "
                "to file expanded appendix — MCR 7.212(C)(8)"
            ),
        }

    def generate_index(self) -> Dict[str, Any]:
        """Generate the master index of the appellate record."""
        toc = self._paginator.generate_toc()
        exhibit_index = self._exhibit_compiler.create_exhibit_index()
        covers = self._paginator.create_cover_pages()

        return {
            "case_number": self._case_number,
            "table_of_contents": toc,
            "exhibit_index": exhibit_index,
            "volume_covers": covers,
            "total_entries": len(toc),
            "total_exhibits": len(exhibit_index),
            "total_volumes": len(covers),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "legal_basis": "MCR 7.210(A); MCR 7.212(C)",
        }

    def verify_completeness(self) -> CompletionReport:
        """Run full completeness verification on the record."""
        register_entries = self._register._entries
        gaps = self._checker.identify_gaps(self._entries)
        reg_check = self._checker.verify_against_register(
            self._entries, register_entries,
        )
        transcript_issues = self._transcript_mgr.verify_certification()

        all_issues: List[Dict[str, Any]] = []
        all_issues.extend(gaps)
        all_issues.extend(reg_check.get("missing_items", []))
        all_issues.extend(transcript_issues)

        total_pages = self._paginator.get_stats()["total_pages"]
        total_volumes = self._paginator.get_stats()["total_volumes"]

        is_complete = len(all_issues) == 0

        if is_complete:
            self._build_status = RecordBuildStatus.CERTIFIED
        else:
            self._build_status = RecordBuildStatus.DEFICIENT

        missing_items = [
            issue.get("register_entry", issue.get("hearing_date", "unknown"))
            for issue in all_issues
        ]

        report = CompletionReport(
            case_number=self._case_number,
            is_complete=is_complete,
            issues=all_issues,
            total_entries=len(self._entries),
            total_pages=total_pages,
            total_volumes=total_volumes,
            missing_items=missing_items,
        )

        logger.info(
            "Completeness check: %s — %d issues",
            "COMPLETE" if is_complete else "DEFICIENT",
            len(all_issues),
        )
        return report

    def get_stats(self) -> Dict[str, Any]:
        """Return runtime statistics."""
        return {
            "module": "appellate_record_builder",
            "case_number": self._case_number,
            "build_status": self._build_status.value,
            "total_entries": len(self._entries),
            "db_path": str(self._db_path),
            "register": self._register.get_stats(),
            "transcript_mgr": self._transcript_mgr.get_stats(),
            "exhibit_compiler": self._exhibit_compiler.get_stats(),
            "paginator": self._paginator.get_stats(),
            "checker": self._checker.get_stats(),
        }

    def reset(self) -> None:
        """Clear all loaded record data."""
        self._entries.clear()
        self._build_status = RecordBuildStatus.PLANNING


# ---------------------------------------------------------------------------
# CLI demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sys.stdout = open(  # noqa: SIM115
        sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace"
    )
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print("=" * 60)
    print("  Appellate Record Builder — LitigationOS")
    print("=" * 60)
    print()

    builder = AppellateRecordBuilder()

    # Build record with sample data
    result = builder.build_record(
        case_number=_COA_CASE,
        docket_entries=[
            {"date": "2024-06-01", "description": "Complaint filed", "filed_by": _PLAINTIFF, "document_type": "pleading"},
            {"date": "2024-06-15", "description": "Answer filed", "filed_by": _DEFENDANT, "document_type": "pleading"},
            {"date": "2024-09-10", "description": "Motion for Summary Disposition", "filed_by": _DEFENDANT, "document_type": "motion"},
            {"date": "2024-10-01", "description": "Order Denying Summary Disposition", "filed_by": "Court", "document_type": "order"},
            {"date": "2025-01-15", "description": "Final Order", "filed_by": "Court", "document_type": "order"},
        ],
        hearings=[
            {"hearing_date": "2024-09-25", "hearing_type": "Motion Hearing", "judge": _JUDGE, "court_reporter": "Smith Reporting"},
            {"hearing_date": "2025-01-10", "hearing_type": "Bench Trial", "judge": _JUDGE, "court_reporter": "Smith Reporting"},
        ],
        exhibits=[
            {"title": "Exhibit A — Lease Agreement", "date": "2023-01-15", "filed_by": _PLAINTIFF},
            {"title": "Exhibit B — Photographs", "date": "2024-03-20", "filed_by": _PLAINTIFF},
            {"title": "Exhibit C — Financial Records", "date": "2024-07-01", "filed_by": _PLAINTIFF},
        ],
        claim_of_appeal_date="2025-02-05",
    )

    print("Record Build Result:")
    for k, v in result.items():
        if isinstance(v, list):
            print(f"  {k}: [{len(v)} items]")
        else:
            print(f"  {k}: {v}")
    print()

    # Verify completeness
    report = builder.verify_completeness()
    print(f"Completeness: {'COMPLETE' if report.is_complete else 'DEFICIENT'}")
    print(f"  Issues: {len(report.issues)}")
    print(f"  Total entries: {report.total_entries}")
    print(f"  Total pages: {report.total_pages}")
    print()

    # Generate index
    index = builder.generate_index()
    print(f"Index: {index['total_entries']} entries, {index['total_exhibits']} exhibits")
    print()

    # Stats
    stats = builder.get_stats()
    print("Stats:")
    for k, v in stats.items():
        print(f"  {k}: {v}")
