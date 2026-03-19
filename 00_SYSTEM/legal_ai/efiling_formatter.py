# -*- coding: utf-8 -*-
"""
efiling_formatter.py — E-Filing Format Preparation Engine
==========================================================
Prepares filing packages for electronic filing across multiple Michigan
court systems (MiFILE, TrueFiling, PACER) and manual-submission tribunals
(JTC, AGC, LARA, HUD).

Each court system has distinct requirements for file naming, size limits,
accepted formats, bookmarks, text-searchability, and fee schedules.  This
module encapsulates those differences behind a unified ``EFilingFormatter``
class that validates, renames, and packages documents for submission.

Supported E-Filing Systems:
  - **MiFILE** — Michigan 14th Circuit Court, most circuit courts
  - **TrueFiling** — Michigan Court of Appeals, Supreme Court
  - **PACER / CM/ECF** — Federal Western District of Michigan
  - **Manual** — JTC, Attorney Grievance Commission, LARA, HUD

Six case lanes: A=Custody (2024-001507-DC), B=Housing (2025-002760-CZ),
C=Convergence, D=PPO (2023-5907-PP), E=Misconduct/JTC, F=Appellate
(COA 366810).

Zero external dependencies.  Local-only.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import sqlite3
import textwrap
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from html import escape as html_escape
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("legal_ai.efiling_formatter")

# ─── Constants ────────────────────────────────────────────────────────

_DB_DEFAULT: Path = Path(__file__).resolve().parents[2] / "litigation_context.db"

_VALID_LANES = {"A", "B", "C", "D", "E", "F"}

_LANE_LABELS: Dict[str, str] = {
    "A": "Custody (2024-001507-DC)",
    "B": "Housing (2025-002760-CZ)",
    "C": "Convergence (cross-lane)",
    "D": "PPO (2023-5907-PP)",
    "E": "Misconduct / JTC",
    "F": "Appellate (COA 366810)",
}

# Plaintiff contact (Pro Se)
_PLAINTIFF = {
    "name": "Andrew James Pigors",
    "address": "1977 Whitehall Road, Lot 17",
    "city_state_zip": "North Muskegon, MI 49445",
    "status": "Pro Se",
}


# ─── Enums ────────────────────────────────────────────────────────────

class EFilingSystem(Enum):
    """Supported electronic filing platforms."""

    MIFILE = "mifile"
    TRUEFILING = "truefiling"
    PACER = "pacer"
    MANUAL = "manual"


# ─── Data Classes ─────────────────────────────────────────────────────

@dataclass
class EFilingSpec:
    """Configuration for a single e-filing system endpoint.

    Encapsulates the technical and procedural requirements imposed by
    a specific court's electronic filing portal.
    """

    system: EFilingSystem
    max_file_size_mb: int
    accepted_formats: List[str]
    naming_convention: str
    requires_bookmarks: bool
    requires_text_searchable: bool
    requires_numbered_lines: bool
    fee_code: str
    payment_method: str

    def to_dict(self) -> dict:
        """Serialize to plain dictionary."""
        d = asdict(self)
        d["system"] = self.system.value
        return d


@dataclass
class EFilingPacket:
    """A fully-assembled e-filing submission packet.

    Represents every artefact, metadata field, and validation result
    needed to submit a filing electronically (or manually) to a court.
    """

    filing_id: str
    system: EFilingSystem
    court: str
    case_number: str
    filing_type: str
    main_document: str
    exhibits: List[str] = field(default_factory=list)
    proof_of_service: str = ""
    proposed_order: Optional[str] = None
    fee_amount: float = 0.0
    fee_waiver: bool = False
    naming_manifest: Dict[str, str] = field(default_factory=dict)
    validation_result: Dict[str, Any] = field(default_factory=dict)
    ready: bool = False
    issues: List[str] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        """Serialize to plain dictionary."""
        d = asdict(self)
        d["system"] = self.system.value
        return d


# ─── Fee Schedule ─────────────────────────────────────────────────────

_FEE_SCHEDULE: Dict[str, Dict[str, float]] = {
    "14th_circuit": {
        "motion": 20.0,
        "complaint": 175.0,
        "answer": 0.0,
        "response": 0.0,
        "objection": 0.0,
        "notice": 0.0,
        "stipulation": 0.0,
        "default": 20.0,
    },
    "coa": {
        "appeal": 375.0,
        "motion": 0.0,
        "brief": 0.0,
        "application": 75.0,
        "default": 0.0,
    },
    "msc": {
        "application": 375.0,
        "motion": 0.0,
        "brief": 0.0,
        "default": 0.0,
    },
    "wdmi": {
        "complaint": 405.0,
        "motion": 0.0,
        "notice": 0.0,
        "default": 0.0,
    },
    "jtc": {"default": 0.0},
    "agc": {"default": 0.0},
    "lara": {"default": 0.0},
    "hud": {"default": 0.0},
}


# ─── Court ↔ Case Number Mapping ─────────────────────────────────────

_COURT_CASE_NUMBERS: Dict[str, str] = {
    "14th_circuit": "2024-001507-DC",
    "14th_circuit_cz": "2025-002760-CZ",
    "14th_circuit_pp": "2023-5907-PP",
    "coa": "366810",
    "msc": "",
    "wdmi": "",
    "jtc": "",
    "agc": "",
    "lara": "",
    "hud": "",
}


# ─── System Specifications ────────────────────────────────────────────

_SYSTEM_SPECS: Dict[str, EFilingSpec] = {
    "14th_circuit": EFilingSpec(
        system=EFilingSystem.MIFILE,
        max_file_size_mb=35,
        accepted_formats=["pdf", "docx"],
        naming_convention="{case_number}_{filing_type}_{date}_{seq}.pdf",
        requires_bookmarks=False,
        requires_text_searchable=True,
        requires_numbered_lines=False,
        fee_code="MC-20",
        payment_method="credit_card",
    ),
    "coa": EFilingSpec(
        system=EFilingSystem.TRUEFILING,
        max_file_size_mb=25,
        accepted_formats=["pdf"],
        naming_convention="{docket}_{type}_{desc}.pdf",
        requires_bookmarks=True,
        requires_text_searchable=True,
        requires_numbered_lines=False,
        fee_code="COA-FILING",
        payment_method="credit_card",
    ),
    "msc": EFilingSpec(
        system=EFilingSystem.TRUEFILING,
        max_file_size_mb=25,
        accepted_formats=["pdf"],
        naming_convention="{docket}_{type}_{desc}.pdf",
        requires_bookmarks=True,
        requires_text_searchable=True,
        requires_numbered_lines=False,
        fee_code="MSC-FILING",
        payment_method="credit_card",
    ),
    "wdmi": EFilingSpec(
        system=EFilingSystem.PACER,
        max_file_size_mb=35,
        accepted_formats=["pdf"],
        naming_convention="Doc{num}_{type}.pdf",
        requires_bookmarks=False,
        requires_text_searchable=True,
        requires_numbered_lines=False,
        fee_code="PACER-FILING",
        payment_method="pacer_account",
    ),
    "jtc": EFilingSpec(
        system=EFilingSystem.MANUAL,
        max_file_size_mb=0,
        accepted_formats=["pdf", "docx"],
        naming_convention="{filing_type}_{date}.pdf",
        requires_bookmarks=False,
        requires_text_searchable=False,
        requires_numbered_lines=False,
        fee_code="NONE",
        payment_method="none",
    ),
    "agc": EFilingSpec(
        system=EFilingSystem.MANUAL,
        max_file_size_mb=0,
        accepted_formats=["pdf", "docx"],
        naming_convention="{filing_type}_{date}.pdf",
        requires_bookmarks=False,
        requires_text_searchable=False,
        requires_numbered_lines=False,
        fee_code="NONE",
        payment_method="none",
    ),
    "lara": EFilingSpec(
        system=EFilingSystem.MANUAL,
        max_file_size_mb=0,
        accepted_formats=["pdf", "docx"],
        naming_convention="{filing_type}_{date}.pdf",
        requires_bookmarks=False,
        requires_text_searchable=False,
        requires_numbered_lines=False,
        fee_code="NONE",
        payment_method="none",
    ),
    "hud": EFilingSpec(
        system=EFilingSystem.MANUAL,
        max_file_size_mb=0,
        accepted_formats=["pdf", "docx"],
        naming_convention="{filing_type}_{date}.pdf",
        requires_bookmarks=False,
        requires_text_searchable=False,
        requires_numbered_lines=False,
        fee_code="NONE",
        payment_method="none",
    ),
}


# ─── Main Formatter Class ────────────────────────────────────────────

class EFilingFormatter:
    """Prepare filing packages for electronic filing systems.

    Encapsulates the full lifecycle of e-filing preparation: validation,
    naming, fee estimation, cover-sheet generation, and submission
    checklist assembly.

    Features:
      - Multi-system support (MiFILE, TrueFiling, PACER, Manual)
      - Court-specific naming conventions and size limits
      - Fee estimation with MC-20 fee-waiver awareness
      - Cover-sheet and submission-checklist generation
      - Batch preparation for multi-filing workflows

    Usage::

        from legal_ai.efiling_formatter import EFilingFormatter
        fmt = EFilingFormatter()
        packet = fmt.prepare_packet(
            filing_id="MTN-DISQ-001",
            court="14th_circuit",
            filing_type="motion",
            documents=["motion.pdf"],
        )
        if packet.ready:
            print("Ready to file!")
    """

    SYSTEMS = _SYSTEM_SPECS

    def __init__(self, db_path: str | Path | None = None) -> None:
        """Initialise the formatter.

        Args:
            db_path: Optional path to the litigation SQLite database.
                     Defaults to ``litigation_context.db`` two levels
                     above this module.
        """
        self._db_path: Path = Path(db_path) if db_path else _DB_DEFAULT
        self._conn: Optional[sqlite3.Connection] = None
        self._packets_prepared: int = 0
        self._packets_valid: int = 0
        self._packets_invalid: int = 0
        logger.debug("EFilingFormatter initialised (db=%s)", self._db_path)

    # ── DB helpers ────────────────────────────────────────────────────

    def _get_conn(self) -> sqlite3.Connection:
        """Return a lazily-initialised database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self._db_path), timeout=60)
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA busy_timeout=60000")
            self._conn.execute("PRAGMA cache_size=-32000")
            self._conn.execute("PRAGMA synchronous=NORMAL")
            self._conn.execute("PRAGMA temp_store=MEMORY")
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _ensure_schema(self) -> None:
        """Create the efiling_packets table if it does not exist."""
        conn = self._get_conn()
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS efiling_packets (
                filing_id   TEXT PRIMARY KEY,
                system      TEXT NOT NULL,
                court       TEXT NOT NULL,
                case_number TEXT NOT NULL,
                filing_type TEXT NOT NULL,
                main_doc    TEXT NOT NULL,
                exhibits    TEXT DEFAULT '[]',
                pos_path    TEXT DEFAULT '',
                proposed_order TEXT DEFAULT '',
                fee_amount  REAL DEFAULT 0.0,
                fee_waiver  INTEGER DEFAULT 0,
                naming_json TEXT DEFAULT '{}',
                validation  TEXT DEFAULT '{}',
                ready       INTEGER DEFAULT 0,
                issues      TEXT DEFAULT '[]',
                created_at  TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_efp_court
                ON efiling_packets(court);
            CREATE INDEX IF NOT EXISTS idx_efp_ready
                ON efiling_packets(ready);
            """
        )
        conn.commit()

    def _save_packet(self, packet: EFilingPacket) -> None:
        """Persist a packet to the database."""
        try:
            self._ensure_schema()
            conn = self._get_conn()
            conn.execute(
                """
                INSERT OR REPLACE INTO efiling_packets
                    (filing_id, system, court, case_number, filing_type,
                     main_doc, exhibits, pos_path, proposed_order,
                     fee_amount, fee_waiver, naming_json, validation,
                     ready, issues, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    packet.filing_id,
                    packet.system.value,
                    packet.court,
                    packet.case_number,
                    packet.filing_type,
                    packet.main_document,
                    json.dumps(packet.exhibits),
                    packet.proof_of_service,
                    packet.proposed_order or "",
                    packet.fee_amount,
                    1 if packet.fee_waiver else 0,
                    json.dumps(packet.naming_manifest),
                    json.dumps(packet.validation_result),
                    1 if packet.ready else 0,
                    json.dumps(packet.issues),
                    packet.created_at,
                ),
            )
            conn.commit()
        except sqlite3.Error as exc:
            logger.error("Failed to save packet %s: %s", packet.filing_id, exc)

    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    # ── Court / System look-ups ───────────────────────────────────────

    def get_system_for_court(self, court: str) -> EFilingSystem:
        """Return the e-filing system used by *court*.

        Args:
            court: Court identifier (e.g. ``"14th_circuit"``, ``"coa"``).

        Returns:
            The ``EFilingSystem`` enum member for that court.

        Raises:
            ValueError: If *court* is not recognised.
        """
        spec = _SYSTEM_SPECS.get(court)
        if spec is None:
            raise ValueError(
                f"Unknown court '{court}'. "
                f"Valid courts: {', '.join(sorted(_SYSTEM_SPECS))}"
            )
        return spec.system

    def get_spec_for_court(self, court: str) -> EFilingSpec:
        """Return the full filing specification for *court*.

        Args:
            court: Court identifier.

        Returns:
            The ``EFilingSpec`` dataclass for the court.

        Raises:
            ValueError: If *court* is not recognised.
        """
        spec = _SYSTEM_SPECS.get(court)
        if spec is None:
            raise ValueError(f"Unknown court '{court}'.")
        return spec

    # ── File-level checks ─────────────────────────────────────────────

    def check_file_size(self, path: str | Path, court: str) -> bool:
        """Check whether *path* is within the size limit for *court*.

        Args:
            path: File path to check.
            court: Court identifier.

        Returns:
            ``True`` if the file is within limits or the court has no
            size limit (manual submissions).
        """
        spec = self.get_spec_for_court(court)
        if spec.max_file_size_mb == 0:
            return True
        p = Path(path)
        if not p.exists():
            logger.warning("File does not exist for size check: %s", path)
            return False
        size_mb = p.stat().st_size / (1024 * 1024)
        within = size_mb <= spec.max_file_size_mb
        if not within:
            logger.warning(
                "File %s is %.1f MB (limit %d MB for %s)",
                p.name,
                size_mb,
                spec.max_file_size_mb,
                court,
            )
        return within

    def check_format_compliance(
        self, path: str | Path, court: str
    ) -> List[str]:
        """Check format compliance of *path* for *court*.

        Args:
            path: File path to check.
            court: Court identifier.

        Returns:
            A list of compliance issues (empty if fully compliant).
        """
        issues: List[str] = []
        spec = self.get_spec_for_court(court)
        p = Path(path)

        if not p.exists():
            issues.append(f"File not found: {p}")
            return issues

        ext = p.suffix.lstrip(".").lower()
        if ext not in spec.accepted_formats:
            issues.append(
                f"Format '{ext}' not accepted by {court}. "
                f"Accepted: {', '.join(spec.accepted_formats)}"
            )

        if spec.max_file_size_mb > 0:
            size_mb = p.stat().st_size / (1024 * 1024)
            if size_mb > spec.max_file_size_mb:
                issues.append(
                    f"File size {size_mb:.1f} MB exceeds "
                    f"{spec.max_file_size_mb} MB limit"
                )

        if size_mb := (p.stat().st_size if p.exists() else 0):
            if size_mb == 0:
                issues.append("File is empty (0 bytes)")

        if spec.requires_text_searchable and ext == "pdf":
            issues.append(
                "WARN: Verify PDF is text-searchable (cannot auto-check)"
            )

        if spec.requires_bookmarks and ext == "pdf":
            issues.append(
                "WARN: Verify PDF contains bookmarks (cannot auto-check)"
            )

        return issues

    # ── Naming conventions ────────────────────────────────────────────

    def _generate_mifile_name(
        self,
        case_number: str,
        filing_type: str,
        description: str,
        date_str: str,
        seq: int,
    ) -> str:
        """Generate a MiFILE-compliant filename.

        Pattern: ``{CaseNumber}_{FilingType}_{Description}_{Date}_{Seq}.pdf``
        """
        safe_case = re.sub(r"[^A-Za-z0-9\-]", "", case_number)
        safe_type = re.sub(r"[^A-Za-z0-9]", "_", filing_type).title()
        safe_desc = re.sub(r"[^A-Za-z0-9]", "_", description).title()
        return f"{safe_case}_{safe_type}_{safe_desc}_{date_str}_{seq:03d}.pdf"

    def _generate_truefiling_name(
        self,
        docket_number: str,
        doc_type: str,
        description: str,
    ) -> str:
        """Generate a TrueFiling-compliant filename.

        Pattern: ``{Docket}_{Type}_{Desc}.pdf``
        """
        safe_docket = re.sub(r"[^A-Za-z0-9]", "", docket_number)
        safe_type = re.sub(r"[^A-Za-z0-9]", "_", doc_type).title()
        safe_desc = re.sub(r"[^A-Za-z0-9]", "_", description).title()
        return f"{safe_docket}_{safe_type}_{safe_desc}.pdf"

    def _generate_pacer_name(
        self, doc_number: int, doc_type: str
    ) -> str:
        """Generate a PACER / CM/ECF-compliant filename.

        Pattern: ``Doc{num}_{type}.pdf``
        """
        safe_type = re.sub(r"[^A-Za-z0-9]", "_", doc_type).title()
        return f"Doc{doc_number}_{safe_type}.pdf"

    def _generate_manual_name(
        self, filing_type: str, date_str: str
    ) -> str:
        """Generate a filename for manual-submission bodies.

        Pattern: ``{FilingType}_{Date}.pdf``
        """
        safe_type = re.sub(r"[^A-Za-z0-9]", "_", filing_type).title()
        return f"{safe_type}_{date_str}.pdf"

    def generate_naming_manifest(
        self, packet: EFilingPacket
    ) -> Dict[str, str]:
        """Build the original→e-filing name mapping for all documents.

        Args:
            packet: The filing packet whose documents to rename.

        Returns:
            Dict mapping original filenames to their e-filing names.
        """
        manifest: Dict[str, str] = {}
        spec = self.get_spec_for_court(packet.court)
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        seq = 1

        all_docs: List[str] = [packet.main_document]
        all_docs.extend(packet.exhibits)
        if packet.proof_of_service:
            all_docs.append(packet.proof_of_service)
        if packet.proposed_order:
            all_docs.append(packet.proposed_order)

        for doc_path in all_docs:
            original = Path(doc_path).name
            if spec.system == EFilingSystem.MIFILE:
                efiling_name = self._generate_mifile_name(
                    packet.case_number,
                    packet.filing_type,
                    Path(doc_path).stem,
                    date_str,
                    seq,
                )
            elif spec.system == EFilingSystem.TRUEFILING:
                efiling_name = self._generate_truefiling_name(
                    packet.case_number,
                    packet.filing_type,
                    Path(doc_path).stem,
                )
            elif spec.system == EFilingSystem.PACER:
                efiling_name = self._generate_pacer_name(
                    seq, packet.filing_type
                )
            else:
                efiling_name = self._generate_manual_name(
                    packet.filing_type, date_str
                )
            manifest[original] = efiling_name
            seq += 1

        return manifest

    # ── Fee estimation ────────────────────────────────────────────────

    def estimate_fees(
        self,
        court: str,
        filing_type: str,
        fee_waiver: bool = False,
    ) -> float:
        """Estimate the filing fee for *filing_type* at *court*.

        Args:
            court: Court identifier.
            filing_type: Type of filing (``"motion"``, ``"complaint"``, etc.).
            fee_waiver: Whether an MC-20 fee waiver has been granted.

        Returns:
            Estimated fee in US dollars (``0.0`` if waived).
        """
        if fee_waiver:
            return 0.0

        court_fees = _FEE_SCHEDULE.get(court, {})
        fee = court_fees.get(
            filing_type.lower(), court_fees.get("default", 0.0)
        )
        return float(fee)

    # ── Validation ────────────────────────────────────────────────────

    def validate_packet(self, packet: EFilingPacket) -> Dict[str, Any]:
        """Run all validation checks on *packet*.

        Args:
            packet: The filing packet to validate.

        Returns:
            Dict with ``valid`` bool, ``checks`` list, and ``issues`` list.
        """
        checks: List[Dict[str, Any]] = []
        issues: List[str] = []
        spec = self.get_spec_for_court(packet.court)

        # 1. Main document exists
        main_exists = Path(packet.main_document).exists()
        checks.append({
            "check": "main_document_exists",
            "passed": main_exists,
            "detail": packet.main_document,
        })
        if not main_exists:
            issues.append(f"Main document not found: {packet.main_document}")

        # 2. Main document format
        if main_exists:
            fmt_issues = self.check_format_compliance(
                packet.main_document, packet.court
            )
            fmt_ok = not any(
                i for i in fmt_issues if not i.startswith("WARN:")
            )
            checks.append({
                "check": "main_document_format",
                "passed": fmt_ok,
                "detail": fmt_issues,
            })
            if not fmt_ok:
                issues.extend(
                    i for i in fmt_issues if not i.startswith("WARN:")
                )

        # 3. Main document size
        if main_exists:
            size_ok = self.check_file_size(packet.main_document, packet.court)
            checks.append({
                "check": "main_document_size",
                "passed": size_ok,
                "detail": packet.main_document,
            })
            if not size_ok:
                issues.append(
                    f"Main document exceeds {spec.max_file_size_mb} MB limit"
                )

        # 4. Exhibit checks
        for i, exhibit in enumerate(packet.exhibits):
            ex_exists = Path(exhibit).exists()
            checks.append({
                "check": f"exhibit_{i+1}_exists",
                "passed": ex_exists,
                "detail": exhibit,
            })
            if not ex_exists:
                issues.append(f"Exhibit {i+1} not found: {exhibit}")
            elif not self.check_file_size(exhibit, packet.court):
                issues.append(
                    f"Exhibit {i+1} exceeds size limit: {exhibit}"
                )

        # 5. Proof of service
        if packet.proof_of_service:
            pos_exists = Path(packet.proof_of_service).exists()
            checks.append({
                "check": "proof_of_service_exists",
                "passed": pos_exists,
                "detail": packet.proof_of_service,
            })
            if not pos_exists:
                issues.append(
                    f"Proof of service not found: {packet.proof_of_service}"
                )
        else:
            checks.append({
                "check": "proof_of_service_exists",
                "passed": False,
                "detail": "No proof of service provided",
            })
            issues.append("Proof of service is required")

        # 6. Case number present
        has_case = bool(packet.case_number and packet.case_number.strip())
        checks.append({
            "check": "case_number_present",
            "passed": has_case,
            "detail": packet.case_number,
        })
        if not has_case:
            issues.append("Case number is missing")

        # 7. Filing type present
        has_type = bool(packet.filing_type and packet.filing_type.strip())
        checks.append({
            "check": "filing_type_present",
            "passed": has_type,
            "detail": packet.filing_type,
        })
        if not has_type:
            issues.append("Filing type is missing")

        # 8. Fee check
        if not packet.fee_waiver and packet.fee_amount > 0:
            checks.append({
                "check": "fee_payment_required",
                "passed": True,
                "detail": f"${packet.fee_amount:.2f} via {spec.payment_method}",
            })

        total_passed = sum(1 for c in checks if c["passed"])
        total_checks = len(checks)
        valid = len(issues) == 0

        return {
            "valid": valid,
            "checks": checks,
            "issues": issues,
            "passed": total_passed,
            "total": total_checks,
            "score": (total_passed / total_checks * 100) if total_checks else 0,
        }

    # ── Packet preparation ────────────────────────────────────────────

    def prepare_packet(
        self,
        filing_id: str,
        court: str,
        filing_type: str,
        documents: List[str],
        exhibits: Optional[List[str]] = None,
        proof_of_service: str = "",
        proposed_order: Optional[str] = None,
        case_number: Optional[str] = None,
        fee_waiver: bool = False,
    ) -> EFilingPacket:
        """Prepare a complete e-filing packet.

        Args:
            filing_id: Unique identifier for this filing.
            court: Court identifier (key in ``SYSTEMS``).
            filing_type: Type of filing (``"motion"``, ``"brief"``, etc.).
            documents: List of document paths; first is main document.
            exhibits: Optional list of exhibit file paths.
            proof_of_service: Path to proof-of-service document.
            proposed_order: Optional path to a proposed order.
            case_number: Override case number (auto-detected if omitted).
            fee_waiver: Whether an MC-20 fee waiver applies.

        Returns:
            A fully-populated ``EFilingPacket``.
        """
        try:
            spec = self.get_spec_for_court(court)
        except ValueError as exc:
            logger.error("prepare_packet failed: %s", exc)
            return EFilingPacket(
                filing_id=filing_id,
                system=EFilingSystem.MANUAL,
                court=court,
                case_number=case_number or "",
                filing_type=filing_type,
                main_document=documents[0] if documents else "",
                issues=[str(exc)],
                ready=False,
            )

        resolved_case = case_number or _COURT_CASE_NUMBERS.get(court, "")
        main_doc = documents[0] if documents else ""
        exhibit_list = list(exhibits) if exhibits else []

        fee = self.estimate_fees(court, filing_type, fee_waiver)

        packet = EFilingPacket(
            filing_id=filing_id,
            system=spec.system,
            court=court,
            case_number=resolved_case,
            filing_type=filing_type,
            main_document=main_doc,
            exhibits=exhibit_list,
            proof_of_service=proof_of_service,
            proposed_order=proposed_order,
            fee_amount=fee,
            fee_waiver=fee_waiver,
        )

        # Generate naming manifest
        packet.naming_manifest = self.generate_naming_manifest(packet)

        # Validate
        validation = self.validate_packet(packet)
        packet.validation_result = validation
        packet.issues = validation.get("issues", [])
        packet.ready = validation.get("valid", False)

        # Persist
        self._save_packet(packet)

        # Bookkeeping
        self._packets_prepared += 1
        if packet.ready:
            self._packets_valid += 1
        else:
            self._packets_invalid += 1

        logger.info(
            "Packet %s for %s: ready=%s issues=%d",
            filing_id,
            court,
            packet.ready,
            len(packet.issues),
        )
        return packet

    # ── Batch operations ──────────────────────────────────────────────

    def batch_prepare(
        self, filings: List[Dict[str, Any]]
    ) -> List[EFilingPacket]:
        """Prepare multiple filing packets in one call.

        Args:
            filings: List of dicts, each containing the keyword arguments
                     accepted by :meth:`prepare_packet`.

        Returns:
            List of ``EFilingPacket`` instances.
        """
        packets: List[EFilingPacket] = []
        for entry in filings:
            try:
                pkt = self.prepare_packet(
                    filing_id=entry.get("filing_id", f"BATCH-{len(packets)+1:03d}"),
                    court=entry.get("court", ""),
                    filing_type=entry.get("filing_type", ""),
                    documents=entry.get("documents", []),
                    exhibits=entry.get("exhibits"),
                    proof_of_service=entry.get("proof_of_service", ""),
                    proposed_order=entry.get("proposed_order"),
                    case_number=entry.get("case_number"),
                    fee_waiver=entry.get("fee_waiver", False),
                )
                packets.append(pkt)
            except Exception as exc:
                logger.error("Batch item failed: %s", exc)
                packets.append(
                    EFilingPacket(
                        filing_id=entry.get("filing_id", "ERROR"),
                        system=EFilingSystem.MANUAL,
                        court=entry.get("court", ""),
                        case_number=entry.get("case_number", ""),
                        filing_type=entry.get("filing_type", ""),
                        main_document="",
                        issues=[f"Batch preparation error: {exc}"],
                        ready=False,
                    )
                )
        return packets

    # ── Cover sheet generation ────────────────────────────────────────

    def generate_cover_sheet(self, packet: EFilingPacket) -> str:
        """Generate a court-specific cover sheet for the filing.

        Args:
            packet: The filing packet.

        Returns:
            Markdown-formatted cover sheet text.
        """
        spec = self.get_spec_for_court(packet.court)
        now = datetime.now(timezone.utc).strftime("%B %d, %Y")

        court_names = {
            "14th_circuit": "14th Circuit Court — Muskegon County, Michigan",
            "coa": "Michigan Court of Appeals",
            "msc": "Michigan Supreme Court",
            "wdmi": "United States District Court — Western District of Michigan",
            "jtc": "Michigan Judicial Tenure Commission",
            "agc": "Michigan Attorney Grievance Commission",
            "lara": "Michigan LARA",
            "hud": "U.S. Department of Housing and Urban Development",
        }
        court_display = court_names.get(packet.court, packet.court)

        exhibit_lines = ""
        if packet.exhibits:
            for i, ex in enumerate(packet.exhibits, 1):
                exhibit_lines += f"  {i}. {Path(ex).name}\n"

        fee_line = ""
        if packet.fee_waiver:
            fee_line = "Fee: WAIVED (MC 20 Fee Waiver granted)"
        elif packet.fee_amount > 0:
            fee_line = f"Fee: ${packet.fee_amount:.2f}"
        else:
            fee_line = "Fee: $0.00 (no fee required)"

        sheet = textwrap.dedent(f"""\
            # E-FILING COVER SHEET
            
            **Court:** {court_display}
            **Case Number:** {packet.case_number}
            **Filing System:** {spec.system.value.upper()}
            **Date:** {now}
            
            ---
            
            ## Filing Information
            
            | Field | Value |
            |-------|-------|
            | Filing ID | {packet.filing_id} |
            | Filing Type | {packet.filing_type.title()} |
            | Main Document | {Path(packet.main_document).name} |
            | Proof of Service | {Path(packet.proof_of_service).name if packet.proof_of_service else 'N/A'} |
            | Proposed Order | {Path(packet.proposed_order).name if packet.proposed_order else 'N/A'} |
            | {fee_line} | |
            
            ## Plaintiff (Pro Se)
            
            {_PLAINTIFF['name']}
            {_PLAINTIFF['address']}
            {_PLAINTIFF['city_state_zip']}
            
            ## Exhibits ({len(packet.exhibits)})
            
            {exhibit_lines if exhibit_lines else '  (none)'}
            
            ## Naming Manifest
            
        """)

        for original, efiling in packet.naming_manifest.items():
            sheet += f"  - `{original}` → `{efiling}`\n"

        sheet += f"\n---\n*Generated by LitigationOS EFilingFormatter*\n"
        return sheet

    # ── Submission checklist ──────────────────────────────────────────

    def generate_submission_checklist(self, packet: EFilingPacket) -> str:
        """Generate a pre-submission checklist for the filing.

        Args:
            packet: The filing packet.

        Returns:
            Markdown-formatted checklist text.
        """
        spec = self.get_spec_for_court(packet.court)
        items: List[Tuple[str, bool]] = []

        # Universal checks
        items.append((
            "Main document present and accessible",
            Path(packet.main_document).exists(),
        ))
        items.append((
            "Case number is set",
            bool(packet.case_number),
        ))
        items.append((
            "Filing type is specified",
            bool(packet.filing_type),
        ))

        # Format checks
        if packet.main_document and Path(packet.main_document).exists():
            ext = Path(packet.main_document).suffix.lstrip(".").lower()
            items.append((
                f"Main document format ({ext}) is accepted",
                ext in spec.accepted_formats,
            ))

        # Size checks
        if spec.max_file_size_mb > 0 and Path(packet.main_document).exists():
            items.append((
                f"Main document under {spec.max_file_size_mb} MB",
                self.check_file_size(packet.main_document, packet.court),
            ))

        # System-specific checks
        if spec.requires_bookmarks:
            items.append((
                "PDF contains bookmarks (manual verification required)",
                False,
            ))
        if spec.requires_text_searchable:
            items.append((
                "PDF is text-searchable (manual verification required)",
                False,
            ))
        if spec.requires_numbered_lines:
            items.append((
                "Document has numbered lines",
                False,
            ))

        # Proof of service
        items.append((
            "Proof of service attached",
            bool(packet.proof_of_service)
            and Path(packet.proof_of_service).exists(),
        ))

        # Exhibits
        if packet.exhibits:
            all_present = all(Path(e).exists() for e in packet.exhibits)
            items.append((
                f"All {len(packet.exhibits)} exhibit(s) present",
                all_present,
            ))

        # Fee
        if packet.fee_amount > 0 and not packet.fee_waiver:
            items.append((
                f"Filing fee of ${packet.fee_amount:.2f} ready ({spec.payment_method})",
                True,
            ))
        elif packet.fee_waiver:
            items.append((
                "MC 20 Fee Waiver on file",
                True,
            ))

        # Naming manifest generated
        items.append((
            "E-filing naming manifest generated",
            bool(packet.naming_manifest),
        ))

        # Build output
        total = len(items)
        passed = sum(1 for _, ok in items if ok)
        header = (
            f"# Pre-Submission Checklist — {packet.filing_id}\n\n"
            f"**Court:** {packet.court} | "
            f"**System:** {spec.system.value.upper()} | "
            f"**Score:** {passed}/{total}\n\n"
        )
        body = ""
        for label, ok in items:
            mark = "✅" if ok else "❌"
            body += f"- [{mark}] {label}\n"

        body += f"\n---\n"
        if passed == total:
            body += "**STATUS: READY TO FILE** ✅\n"
        else:
            body += (
                f"**STATUS: NOT READY** — {total - passed} item(s) "
                f"require attention ❌\n"
            )

        return header + body

    # ── Statistics ────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Return operational statistics for this formatter instance.

        Returns:
            Dict with packet counts, system distribution, and session data.
        """
        stats: Dict[str, Any] = {
            "packets_prepared": self._packets_prepared,
            "packets_valid": self._packets_valid,
            "packets_invalid": self._packets_invalid,
            "supported_courts": sorted(_SYSTEM_SPECS.keys()),
            "supported_systems": [s.value for s in EFilingSystem],
        }

        # Pull persisted stats if DB is available
        try:
            self._ensure_schema()
            conn = self._get_conn()
            row = conn.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM efiling_packets) AS total,
                    (SELECT COUNT(*) FROM efiling_packets WHERE ready = 1) AS ready,
                    (SELECT COUNT(*) FROM efiling_packets WHERE ready = 0) AS not_ready
                """
            ).fetchone()
            if row:
                stats["db_total_packets"] = row["total"]
                stats["db_ready"] = row["ready"]
                stats["db_not_ready"] = row["not_ready"]

            # Per-court breakdown
            rows = conn.execute(
                "SELECT court, COUNT(*) AS cnt FROM efiling_packets GROUP BY court"
            ).fetchall()
            stats["db_by_court"] = {r["court"]: r["cnt"] for r in rows}

            # Per-system breakdown
            rows = conn.execute(
                "SELECT system, COUNT(*) AS cnt FROM efiling_packets GROUP BY system"
            ).fetchall()
            stats["db_by_system"] = {r["system"]: r["cnt"] for r in rows}

        except sqlite3.Error as exc:
            logger.warning("Could not load DB stats: %s", exc)
            stats["db_error"] = str(exc)

        return stats

    # ── Dunder ────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return (
            f"<EFilingFormatter courts={len(_SYSTEM_SPECS)} "
            f"prepared={self._packets_prepared}>"
        )

    def __del__(self) -> None:
        self.close()
