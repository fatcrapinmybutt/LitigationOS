# -*- coding: utf-8 -*-
"""
filing_state_machine.py — Filing Lifecycle State Machine
=========================================================
Seven-phase filing lifecycle manager with transition rules, rollback
capability, and complete audit logging.  Every court filing in
LitigationOS moves through a deterministic pipeline:

    DRAFT → REVIEW → QA → APPROVED → FORMATTED → FILED → SERVED

Backward transitions (rollbacks) are allowed except from the terminal
SERVED phase.  Each transition is gated by phase-specific requirements
and recorded in an immutable audit log persisted to SQLite.

Phases & Michigan Court Rules:
  - DRAFT      : Initial authoring (no MCR gate)
  - REVIEW     : Caption, case number, content present
  - QA         : No placeholders, reviewer sign-off
  - APPROVED   : QA score ≥ 80, citations verified, party names correct
  - FORMATTED  : PDF generated, format compliant (MCR 7.212, 2.119)
  - FILED      : E-filed / hand-delivered, fee paid or waived
  - SERVED     : Proof of service complete (MCR 2.105 / 2.107)

Six case lanes: A=Custody, B=Housing, C=Convergence, D=PPO,
E=Misconduct/JTC, F=Appellate.

Zero external dependencies.  Local-only.
"""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("legal_ai.filing_state_machine")

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


# ─── Enums ────────────────────────────────────────────────────────────

class FilingPhase(Enum):
    """Seven lifecycle phases of a court filing."""

    DRAFT = "draft"
    REVIEW = "review"
    QA = "qa"
    APPROVED = "approved"
    FORMATTED = "formatted"
    FILED = "filed"
    SERVED = "served"


# ─── Data Classes ─────────────────────────────────────────────────────

@dataclass
class PhaseTransition:
    """Record of a single phase transition in the filing lifecycle.

    Attributes:
        from_phase: Phase the filing was in before the transition.
        to_phase: Phase the filing moved to.
        timestamp: ISO-8601 UTC timestamp of the transition.
        agent_id: Identifier of the agent/user that triggered the move.
        reason: Human-readable justification for the transition.
        checks_passed: List of check IDs that passed for this transition.
        checks_failed: List of check IDs that failed (empty on success).
        rollback_data: Optional snapshot for undo capability.
    """

    from_phase: FilingPhase
    to_phase: FilingPhase
    timestamp: str
    agent_id: str
    reason: str
    checks_passed: List[str] = field(default_factory=list)
    checks_failed: List[str] = field(default_factory=list)
    rollback_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dictionary suitable for JSON export."""
        return {
            "from_phase": self.from_phase.value,
            "to_phase": self.to_phase.value,
            "timestamp": self.timestamp,
            "agent_id": self.agent_id,
            "reason": self.reason,
            "checks_passed": list(self.checks_passed),
            "checks_failed": list(self.checks_failed),
            "rollback_data": self.rollback_data,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PhaseTransition:
        """Reconstruct a PhaseTransition from a dictionary."""
        return cls(
            from_phase=FilingPhase(data["from_phase"]),
            to_phase=FilingPhase(data["to_phase"]),
            timestamp=data["timestamp"],
            agent_id=data["agent_id"],
            reason=data["reason"],
            checks_passed=data.get("checks_passed", []),
            checks_failed=data.get("checks_failed", []),
            rollback_data=data.get("rollback_data"),
        )


@dataclass
class FilingRecord:
    """Complete state record for a single court filing.

    Attributes:
        filing_id: Unique identifier (e.g. ``custody-disq-motion-001``).
        vehicle_name: Human-readable filing name (e.g. "Disqualification Motion").
        lane: One of A–F per LitigationOS lane classification.
        current_phase: Current lifecycle phase.
        history: Ordered list of all phase transitions.
        metadata: Arbitrary key-value pairs (filing_type, court, etc.).
        created_at: ISO-8601 UTC creation timestamp.
        updated_at: ISO-8601 UTC last-modification timestamp.
    """

    filing_id: str
    vehicle_name: str
    lane: str
    current_phase: FilingPhase = FilingPhase.DRAFT
    history: List[PhaseTransition] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the full filing record to a plain dictionary."""
        return {
            "filing_id": self.filing_id,
            "vehicle_name": self.vehicle_name,
            "lane": self.lane,
            "current_phase": self.current_phase.value,
            "history": [t.to_dict() for t in self.history],
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FilingRecord:
        """Reconstruct a FilingRecord from a dictionary."""
        return cls(
            filing_id=data["filing_id"],
            vehicle_name=data["vehicle_name"],
            lane=data["lane"],
            current_phase=FilingPhase(data["current_phase"]),
            history=[
                PhaseTransition.from_dict(t) for t in data.get("history", [])
            ],
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )

    @property
    def content_hash(self) -> str:
        """SHA-256 digest of the filing's serialised state."""
        blob = json.dumps(self.to_dict(), sort_keys=True).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()


# ─── Exceptions ───────────────────────────────────────────────────────

class FilingStateError(Exception):
    """Raised when a filing state operation is invalid."""


class InvalidTransitionError(FilingStateError):
    """Raised when a requested phase transition is not allowed."""


class FilingNotFoundError(FilingStateError):
    """Raised when a filing_id does not exist in the store."""


# ─── State Machine ────────────────────────────────────────────────────

class FilingStateMachine:
    """Seven-phase filing lifecycle manager with rollback and audit.

    The state machine enforces deterministic transitions, validates
    phase-specific requirements, and maintains an immutable audit trail
    of every state change.  Data is stored in-memory with optional
    SQLite persistence to ``litigation_context.db``.

    Example::

        fsm = FilingStateMachine()
        rec = fsm.create_filing("mot-001", "Disqualification Motion", "A")
        fsm.advance("mot-001", FilingPhase.REVIEW, "agent-qa", "Ready for review",
                     {"has_content": True, "has_caption": True, "has_case_number": True})
    """

    # ── Allowed transitions (forward + rollback) ──

    VALID_TRANSITIONS: Dict[FilingPhase, List[FilingPhase]] = {
        FilingPhase.DRAFT: [FilingPhase.REVIEW],
        FilingPhase.REVIEW: [FilingPhase.QA, FilingPhase.DRAFT],
        FilingPhase.QA: [FilingPhase.APPROVED, FilingPhase.REVIEW],
        FilingPhase.APPROVED: [FilingPhase.FORMATTED, FilingPhase.QA],
        FilingPhase.FORMATTED: [FilingPhase.FILED, FilingPhase.APPROVED],
        FilingPhase.FILED: [FilingPhase.SERVED],
        FilingPhase.SERVED: [],
    }

    # ── Phase-entry requirements (check IDs) ──

    PHASE_REQUIREMENTS: Dict[FilingPhase, List[str]] = {
        FilingPhase.REVIEW: [
            "has_content",
            "has_caption",
            "has_case_number",
        ],
        FilingPhase.QA: [
            "reviewer_approved",
            "no_placeholders",
        ],
        FilingPhase.APPROVED: [
            "qa_score_above_80",
            "citations_verified",
            "party_names_correct",
        ],
        FilingPhase.FORMATTED: [
            "approved_by_qa",
            "format_compliant",
        ],
        FilingPhase.FILED: [
            "pdf_generated",
            "e_filing_ready",
            "fee_paid_or_waived",
        ],
        FilingPhase.SERVED: [
            "filed_with_court",
            "proof_of_service_complete",
        ],
    }

    # ── Forward-only phases (for advance vs rollback detection) ──

    _FORWARD_ORDER: List[FilingPhase] = [
        FilingPhase.DRAFT,
        FilingPhase.REVIEW,
        FilingPhase.QA,
        FilingPhase.APPROVED,
        FilingPhase.FORMATTED,
        FilingPhase.FILED,
        FilingPhase.SERVED,
    ]

    # ----------------------------------------------------------------
    # Construction
    # ----------------------------------------------------------------

    def __init__(
        self,
        db_path: Optional[str] = None,
        persist: bool = True,
    ) -> None:
        """Initialise the state machine.

        Args:
            db_path: Path to the SQLite database.  Defaults to the
                     central ``litigation_context.db``.
            persist: If *True* (default), changes are written to SQLite
                     in addition to the in-memory store.
        """
        self._filings: Dict[str, FilingRecord] = {}
        self._db_path: Path = Path(db_path) if db_path else _DB_DEFAULT
        self._db_available: bool = self._db_path.exists()
        self._persist: bool = persist and self._db_available

        # Stats counters
        self._stats_created: int = 0
        self._stats_advances: int = 0
        self._stats_rollbacks: int = 0
        self._stats_errors: int = 0

        if self._persist:
            try:
                self._ensure_table()
            except sqlite3.Error as exc:
                logger.error("Failed to initialise filing_states table: %s", exc)
                self._persist = False

        if not self._db_available:
            logger.warning(
                "Database not found at %s — SQLite persistence disabled.",
                self._db_path,
            )

    # ----------------------------------------------------------------
    # Public API — CRUD
    # ----------------------------------------------------------------

    def create_filing(
        self,
        filing_id: str,
        vehicle_name: str,
        lane: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FilingRecord:
        """Create a new filing in DRAFT phase.

        Args:
            filing_id: Unique identifier for the filing.
            vehicle_name: Human-readable name (e.g. "Disqualification Motion").
            lane: Case lane A–F.
            metadata: Optional extra key-value data.

        Returns:
            The newly created FilingRecord.

        Raises:
            FilingStateError: If the filing_id already exists or lane is invalid.
        """
        if filing_id in self._filings:
            raise FilingStateError(
                f"Filing '{filing_id}' already exists."
            )

        lane_upper = lane.upper()
        if lane_upper not in _VALID_LANES:
            raise FilingStateError(
                f"Invalid lane '{lane}'. Must be one of {sorted(_VALID_LANES)}."
            )

        now = datetime.now(timezone.utc).isoformat()
        record = FilingRecord(
            filing_id=filing_id,
            vehicle_name=vehicle_name,
            lane=lane_upper,
            current_phase=FilingPhase.DRAFT,
            history=[],
            metadata=metadata or {},
            created_at=now,
            updated_at=now,
        )
        self._filings[filing_id] = record
        self._stats_created += 1

        if self._persist:
            self._save_to_db(record)

        logger.info(
            "Created filing %s (%s) in lane %s",
            filing_id,
            vehicle_name,
            lane_upper,
        )
        return record

    def get_filing(self, filing_id: str) -> FilingRecord:
        """Retrieve a filing by its ID.

        Args:
            filing_id: The unique filing identifier.

        Returns:
            The matching FilingRecord.

        Raises:
            FilingNotFoundError: If the filing does not exist.
        """
        record = self._filings.get(filing_id)
        if record is not None:
            return record

        # Try loading from DB
        if self._persist:
            loaded = self._load_from_db(filing_id)
            if loaded is not None:
                self._filings[filing_id] = loaded
                return loaded

        raise FilingNotFoundError(f"Filing '{filing_id}' not found.")

    def get_filings_by_phase(self, phase: FilingPhase) -> List[FilingRecord]:
        """Return all filings currently in the given phase.

        Args:
            phase: The target FilingPhase to filter by.

        Returns:
            List of matching FilingRecord objects (may be empty).
        """
        return [
            r for r in self._filings.values() if r.current_phase == phase
        ]

    def get_filings_by_lane(self, lane: str) -> List[FilingRecord]:
        """Return all filings belonging to the given case lane.

        Args:
            lane: Case lane letter (A–F), case-insensitive.

        Returns:
            List of matching FilingRecord objects (may be empty).
        """
        lane_upper = lane.upper()
        return [r for r in self._filings.values() if r.lane == lane_upper]

    # ----------------------------------------------------------------
    # Public API — Transitions
    # ----------------------------------------------------------------

    def validate_transition(
        self,
        filing_id: str,
        to_phase: FilingPhase,
    ) -> Tuple[bool, List[str]]:
        """Check whether a transition is structurally valid.

        Does **not** evaluate phase requirements — only checks whether
        the graph edge exists.

        Args:
            filing_id: Filing to check.
            to_phase: Desired target phase.

        Returns:
            Tuple of (is_valid, list_of_issues).  An empty issue list
            means the transition is allowed.
        """
        issues: List[str] = []

        try:
            record = self.get_filing(filing_id)
        except FilingNotFoundError:
            return False, [f"Filing '{filing_id}' not found."]

        current = record.current_phase
        allowed = self.VALID_TRANSITIONS.get(current, [])

        if to_phase not in allowed:
            issues.append(
                f"Transition {current.value} → {to_phase.value} is not allowed. "
                f"Valid targets: {[p.value for p in allowed]}"
            )

        return len(issues) == 0, issues

    def advance(
        self,
        filing_id: str,
        to_phase: FilingPhase,
        agent_id: str,
        reason: str,
        check_results: Optional[Dict[str, bool]] = None,
    ) -> PhaseTransition:
        """Advance a filing to the next phase.

        All phase-entry requirements must be satisfied (passed as
        ``check_results``).  Missing checks are treated as failed.

        Args:
            filing_id: Filing to advance.
            to_phase: Target phase (must be forward from current).
            agent_id: Agent or user performing the advance.
            reason: Human-readable justification.
            check_results: Dict mapping check_id → bool for each
                           required check.

        Returns:
            The recorded PhaseTransition.

        Raises:
            FilingNotFoundError: If the filing does not exist.
            InvalidTransitionError: If the transition is not allowed
                                    or requirements are not met.
        """
        record = self.get_filing(filing_id)
        current = record.current_phase

        # Structural validity
        valid, issues = self.validate_transition(filing_id, to_phase)
        if not valid:
            self._stats_errors += 1
            raise InvalidTransitionError("; ".join(issues))

        # Must be a forward move (rollback has its own method)
        if self._phase_index(to_phase) <= self._phase_index(current):
            self._stats_errors += 1
            raise InvalidTransitionError(
                f"Cannot advance backwards from {current.value} to "
                f"{to_phase.value}.  Use rollback() instead."
            )

        # Evaluate phase requirements
        check_results = check_results or {}
        required = self.PHASE_REQUIREMENTS.get(to_phase, [])
        checks_passed: List[str] = []
        checks_failed: List[str] = []

        for req in required:
            if check_results.get(req, False):
                checks_passed.append(req)
            else:
                checks_failed.append(req)

        if checks_failed:
            self._stats_errors += 1
            raise InvalidTransitionError(
                f"Phase requirements not met for {to_phase.value}: "
                f"failed={checks_failed}"
            )

        # Build rollback snapshot
        rollback_data = {
            "previous_phase": current.value,
            "previous_metadata": dict(record.metadata),
        }

        now = datetime.now(timezone.utc).isoformat()
        transition = PhaseTransition(
            from_phase=current,
            to_phase=to_phase,
            timestamp=now,
            agent_id=agent_id,
            reason=reason,
            checks_passed=checks_passed,
            checks_failed=[],
            rollback_data=rollback_data,
        )

        record.current_phase = to_phase
        record.history.append(transition)
        record.updated_at = now
        self._stats_advances += 1

        if self._persist:
            self._save_to_db(record)

        logger.info(
            "Filing %s advanced: %s → %s (agent=%s)",
            filing_id,
            current.value,
            to_phase.value,
            agent_id,
        )
        return transition

    def rollback(
        self,
        filing_id: str,
        to_phase: FilingPhase,
        agent_id: str,
        reason: str,
    ) -> PhaseTransition:
        """Roll a filing back to an earlier phase.

        Args:
            filing_id: Filing to roll back.
            to_phase: Target earlier phase.
            agent_id: Agent or user performing the rollback.
            reason: Human-readable justification.

        Returns:
            The recorded PhaseTransition.

        Raises:
            FilingNotFoundError: If the filing does not exist.
            InvalidTransitionError: If the rollback is not allowed.
        """
        record = self.get_filing(filing_id)
        current = record.current_phase

        # Structural validity
        valid, issues = self.validate_transition(filing_id, to_phase)
        if not valid:
            self._stats_errors += 1
            raise InvalidTransitionError("; ".join(issues))

        # Must be a backward move
        if self._phase_index(to_phase) >= self._phase_index(current):
            self._stats_errors += 1
            raise InvalidTransitionError(
                f"Cannot roll back forward from {current.value} to "
                f"{to_phase.value}.  Use advance() instead."
            )

        rollback_data = {
            "previous_phase": current.value,
            "previous_metadata": dict(record.metadata),
        }

        now = datetime.now(timezone.utc).isoformat()
        transition = PhaseTransition(
            from_phase=current,
            to_phase=to_phase,
            timestamp=now,
            agent_id=agent_id,
            reason=f"[ROLLBACK] {reason}",
            checks_passed=[],
            checks_failed=[],
            rollback_data=rollback_data,
        )

        record.current_phase = to_phase
        record.history.append(transition)
        record.updated_at = now
        self._stats_rollbacks += 1

        if self._persist:
            self._save_to_db(record)

        logger.info(
            "Filing %s rolled back: %s → %s (agent=%s, reason=%s)",
            filing_id,
            current.value,
            to_phase.value,
            agent_id,
            reason,
        )
        return transition

    # ----------------------------------------------------------------
    # Public API — Audit & Reporting
    # ----------------------------------------------------------------

    def get_audit_log(self, filing_id: str) -> List[PhaseTransition]:
        """Return the complete transition history for a filing.

        Args:
            filing_id: The filing to retrieve the audit log for.

        Returns:
            List of PhaseTransition records in chronological order.

        Raises:
            FilingNotFoundError: If the filing does not exist.
        """
        record = self.get_filing(filing_id)
        return list(record.history)

    def get_dashboard(self) -> Dict[str, Any]:
        """Generate a summary dashboard of all filings.

        Returns:
            Dict with ``by_phase`` counts, ``by_lane`` counts,
            ``total`` count, and ``terminal`` count.
        """
        by_phase: Dict[str, int] = {p.value: 0 for p in FilingPhase}
        by_lane: Dict[str, int] = {lane: 0 for lane in sorted(_VALID_LANES)}
        phase_lane: Dict[str, Dict[str, int]] = {
            p.value: {lane: 0 for lane in sorted(_VALID_LANES)}
            for p in FilingPhase
        }

        for record in self._filings.values():
            phase_val = record.current_phase.value
            by_phase[phase_val] += 1
            by_lane[record.lane] += 1
            phase_lane[phase_val][record.lane] += 1

        total = len(self._filings)
        terminal = by_phase.get(FilingPhase.SERVED.value, 0)

        return {
            "total_filings": total,
            "terminal_filings": terminal,
            "active_filings": total - terminal,
            "by_phase": by_phase,
            "by_lane": by_lane,
            "phase_by_lane": phase_lane,
            "lane_labels": dict(_LANE_LABELS),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    # ----------------------------------------------------------------
    # Public API — Import / Export
    # ----------------------------------------------------------------

    def export_state(self, filepath: str) -> None:
        """Export all filings to a JSON file.

        Args:
            filepath: Destination file path.

        Raises:
            OSError: If the file cannot be written.
        """
        data = {
            "version": "1.0.0",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "filings": {
                fid: rec.to_dict() for fid, rec in self._filings.items()
            },
        }
        out_path = Path(filepath)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Exported %d filings to %s", len(self._filings), filepath)

    def import_state(self, filepath: str) -> int:
        """Import filings from a JSON file.

        Existing filings with the same ID are **overwritten**.

        Args:
            filepath: Source JSON file path.

        Returns:
            Number of filings imported.

        Raises:
            FileNotFoundError: If the file does not exist.
            json.JSONDecodeError: If the file is not valid JSON.
        """
        in_path = Path(filepath)
        raw = json.loads(in_path.read_text(encoding="utf-8"))
        filings_data = raw.get("filings", {})

        count = 0
        for fid, rec_data in filings_data.items():
            try:
                record = FilingRecord.from_dict(rec_data)
                self._filings[fid] = record
                if self._persist:
                    self._save_to_db(record)
                count += 1
            except (KeyError, ValueError) as exc:
                logger.warning("Skipping malformed filing '%s': %s", fid, exc)

        logger.info("Imported %d filings from %s", count, filepath)
        return count

    # ----------------------------------------------------------------
    # Public API — Statistics
    # ----------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Return operational statistics for this state machine instance.

        Returns:
            Dict with counters, DB status, and phase/lane breakdowns.
        """
        return {
            "version": "1.0.0",
            "total_filings": len(self._filings),
            "filings_created": self._stats_created,
            "advances": self._stats_advances,
            "rollbacks": self._stats_rollbacks,
            "errors": self._stats_errors,
            "db_path": str(self._db_path),
            "db_available": self._db_available,
            "persist_enabled": self._persist,
            "phases": [p.value for p in FilingPhase],
            "lanes": sorted(_VALID_LANES),
            "lane_labels": dict(_LANE_LABELS),
            "phase_counts": {
                p.value: sum(
                    1
                    for r in self._filings.values()
                    if r.current_phase == p
                )
                for p in FilingPhase
            },
        }

    # ----------------------------------------------------------------
    # Internal — SQLite Persistence
    # ----------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        """Open a WAL-mode connection with standard LitigationOS PRAGMAs."""
        conn = sqlite3.connect(str(self._db_path), timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("PRAGMA cache_size=-32000")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_table(self) -> None:
        """Create the ``filing_states`` table if it does not exist."""
        conn = self._connect()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS filing_states (
                    filing_id   TEXT PRIMARY KEY,
                    vehicle_name TEXT NOT NULL,
                    lane        TEXT NOT NULL,
                    phase       TEXT NOT NULL,
                    history     TEXT NOT NULL DEFAULT '[]',
                    metadata    TEXT NOT NULL DEFAULT '{}',
                    content_hash TEXT NOT NULL DEFAULT '',
                    created_at  TEXT NOT NULL,
                    updated_at  TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_filing_states_phase
                ON filing_states(phase)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_filing_states_lane
                ON filing_states(lane)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_filing_states_lane_phase
                ON filing_states(lane, phase)
            """)
            conn.commit()
        finally:
            conn.close()

    def _save_to_db(self, filing: FilingRecord) -> None:
        """Persist a FilingRecord to the ``filing_states`` table.

        Uses INSERT OR REPLACE so both new and updated records are
        handled in a single statement.

        Args:
            filing: The record to persist.
        """
        if not self._persist:
            return

        try:
            conn = self._connect()
            try:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO filing_states
                        (filing_id, vehicle_name, lane, phase, history,
                         metadata, content_hash, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        filing.filing_id,
                        filing.vehicle_name,
                        filing.lane,
                        filing.current_phase.value,
                        json.dumps(
                            [t.to_dict() for t in filing.history],
                            ensure_ascii=False,
                        ),
                        json.dumps(filing.metadata, ensure_ascii=False),
                        filing.content_hash,
                        filing.created_at,
                        filing.updated_at,
                    ),
                )
                conn.commit()
            finally:
                conn.close()
        except sqlite3.Error as exc:
            logger.error(
                "Failed to save filing '%s' to DB: %s",
                filing.filing_id,
                exc,
            )

    def _load_from_db(self, filing_id: str) -> Optional[FilingRecord]:
        """Load a single FilingRecord from the database.

        Args:
            filing_id: The record to retrieve.

        Returns:
            A FilingRecord if found, otherwise ``None``.
        """
        if not self._persist:
            return None

        try:
            conn = self._connect()
            try:
                row = conn.execute(
                    "SELECT * FROM filing_states WHERE filing_id = ?",
                    (filing_id,),
                ).fetchone()
                if row is None:
                    return None
                return self._row_to_record(row)
            finally:
                conn.close()
        except sqlite3.Error as exc:
            logger.error(
                "Failed to load filing '%s' from DB: %s",
                filing_id,
                exc,
            )
            return None

    def _load_all_from_db(self) -> List[FilingRecord]:
        """Load every FilingRecord from the database into memory.

        Returns:
            List of all persisted FilingRecords.
        """
        records: List[FilingRecord] = []
        if not self._persist:
            return records

        try:
            conn = self._connect()
            try:
                cursor = conn.execute("SELECT * FROM filing_states")
                for row in cursor:
                    try:
                        records.append(self._row_to_record(row))
                    except (KeyError, ValueError, json.JSONDecodeError) as exc:
                        logger.warning(
                            "Skipping corrupt DB row '%s': %s",
                            row["filing_id"] if "filing_id" in row.keys() else "?",
                            exc,
                        )
            finally:
                conn.close()
        except sqlite3.Error as exc:
            logger.error("Failed to load filings from DB: %s", exc)

        return records

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> FilingRecord:
        """Convert a sqlite3.Row to a FilingRecord."""
        history_raw = json.loads(row["history"]) if row["history"] else []
        metadata_raw = json.loads(row["metadata"]) if row["metadata"] else {}

        return FilingRecord(
            filing_id=row["filing_id"],
            vehicle_name=row["vehicle_name"],
            lane=row["lane"],
            current_phase=FilingPhase(row["phase"]),
            history=[PhaseTransition.from_dict(t) for t in history_raw],
            metadata=metadata_raw,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    # ----------------------------------------------------------------
    # Internal — Helpers
    # ----------------------------------------------------------------

    def _phase_index(self, phase: FilingPhase) -> int:
        """Return the ordinal index of a phase in the lifecycle.

        Args:
            phase: The phase to look up.

        Returns:
            Zero-based integer index.
        """
        return self._FORWARD_ORDER.index(phase)


# ─── Module-level convenience ─────────────────────────────────────────

_DEFAULT_INSTANCE: Optional[FilingStateMachine] = None


def get_machine(
    db_path: Optional[str] = None,
    persist: bool = True,
) -> FilingStateMachine:
    """Return (and lazily create) the module-level state machine singleton.

    Args:
        db_path: Optional override for the database path.
        persist: Whether to enable SQLite persistence.

    Returns:
        The shared FilingStateMachine instance.
    """
    global _DEFAULT_INSTANCE  # noqa: PLW0603
    if _DEFAULT_INSTANCE is None:
        _DEFAULT_INSTANCE = FilingStateMachine(
            db_path=db_path, persist=persist
        )
    return _DEFAULT_INSTANCE


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    machine = FilingStateMachine(persist=False)

    # Quick smoke test
    rec = machine.create_filing(
        "smoke-001", "Test Motion", "A", {"test": True}
    )
    machine.advance(
        "smoke-001",
        FilingPhase.REVIEW,
        "cli",
        "Smoke test",
        {"has_content": True, "has_caption": True, "has_case_number": True},
    )
    dashboard = machine.get_dashboard()
    stats = machine.get_stats()
    print(json.dumps({"dashboard": dashboard, "stats": stats}, indent=2))
