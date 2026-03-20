"""Universal Case Engine — core case management for LitigationOS.

Provides unified CRUD and orchestration for the full case lifecycle:
case creation, party management, lane routing, evidence-to-claim linkage,
claims tracking with statutory basis, deadline management, and the filing
workflow state machine (draft → review → QA → ready → filed → served).

Michigan court rules are loaded as the default jurisdiction plugin, but
the design is jurisdiction-agnostic — swap the ``JurisdictionPlugin`` to
support any state or federal court system.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional, Sequence

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from litigationos.db.connection import DatabaseManager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_CASE_TYPES = (
    "family", "civil", "criminal", "appellate", "federal", "housing", "ppo",
)

VALID_CASE_STATUSES = ("active", "closed", "appealed", "settled", "dismissed")

VALID_PARTY_ROLES = (
    "plaintiff", "defendant", "petitioner", "respondent",
    "judge", "attorney", "witness", "guardian_ad_litem", "friend_of_court",
)

VALID_CLAIM_STATUSES = ("active", "dismissed", "settled", "withdrawn")

VALID_EVIDENCE_STRENGTHS = ("strong", "moderate", "weak", "inadmissible")

FILING_STATUS_ORDER: tuple[str, ...] = (
    "draft", "review", "qa", "ready", "filed", "served",
)

# Lane routing — IRON LAW: never cross-contaminate
CASE_LANES: dict[str, dict[str, str]] = {
    "A": {"name": "Custody", "meek": "MEEK2", "pattern": r"custody|parenting|visitation|child"},
    "B": {"name": "Housing", "meek": "MEEK1", "pattern": r"housing|hoa|habitability|landlord"},
    "C": {"name": "Convergence", "meek": "",     "pattern": r"convergence|cross.lane|multi"},
    "D": {"name": "PPO", "meek": "MEEK3", "pattern": r"ppo|protection.order|stalking|harassment"},
    "E": {"name": "Misconduct", "meek": "MEEK4", "pattern": r"misconduct|jtc|judicial|bias|recusal"},
    "F": {"name": "Appellate", "meek": "MEEK5", "pattern": r"appell|coa|msc|supreme.court"},
}

# Detection priority (highest first)
LANE_PRIORITY = ("E", "D", "F", "C", "A", "B")


# ---------------------------------------------------------------------------
# Pydantic models — lightweight views returned by the engine
# ---------------------------------------------------------------------------

class CaseSummary(BaseModel):
    """Read-only snapshot of a case with aggregated counts."""

    id: int
    case_number: Optional[str] = None
    title: str
    case_type: Optional[str] = None
    status: str = "active"
    lane: Optional[str] = None
    party_count: int = 0
    claim_count: int = 0
    evidence_count: int = 0
    filing_count: int = 0
    deadline_count: int = 0
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class EvidenceLink(BaseModel):
    """Associates an evidence item with a claim and a strength score."""

    evidence_id: int
    claim_id: int
    strength: str = "moderate"
    notes: Optional[str] = None
    linked_at: Optional[datetime] = Field(default_factory=datetime.now)

    model_config = ConfigDict(from_attributes=True)


class FilingTransition(BaseModel):
    """Audit-trail entry for a filing status change."""

    filing_id: int
    from_status: str
    to_status: str
    changed_by: Optional[str] = None
    notes: Optional[str] = None
    changed_at: Optional[datetime] = Field(default_factory=datetime.now)

    model_config = ConfigDict(from_attributes=True)


class CaseTimeline(BaseModel):
    """Chronological view of all events in a case."""

    case_id: int
    events: list[dict[str, Any]] = Field(default_factory=list)
    generated_at: Optional[datetime] = Field(default_factory=datetime.now)

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Filing state machine
# ---------------------------------------------------------------------------

class FilingStatus(str, Enum):
    """Allowed filing statuses in lifecycle order."""

    DRAFT = "draft"
    REVIEW = "review"
    QA = "qa"
    READY = "ready"
    FILED = "filed"
    SERVED = "served"


# Valid forward transitions.  Backward moves are allowed only to "draft".
_FORWARD_TRANSITIONS: dict[str, tuple[str, ...]] = {
    "draft":  ("review",),
    "review": ("qa", "draft"),
    "qa":     ("ready", "review", "draft"),
    "ready":  ("filed", "draft"),
    "filed":  ("served",),
    "served": (),
}


# ---------------------------------------------------------------------------
# Jurisdiction plugin protocol
# ---------------------------------------------------------------------------

@dataclass
class JurisdictionPlugin:
    """Jurisdiction-specific defaults loaded into the engine."""

    jurisdiction_id: str = "MI"
    jurisdiction_name: str = "Michigan"
    default_court_rules: str = "MCR"
    default_bates_prefix: str = "PIGORS"
    # Mapping: filing_type -> (calendar_days, rule_basis, description)
    deadline_rules: dict[str, tuple[int, str, str]] = field(default_factory=dict)

    @staticmethod
    def michigan() -> JurisdictionPlugin:
        """Create a plugin pre-loaded with Michigan defaults."""
        return JurisdictionPlugin(
            jurisdiction_id="MI",
            jurisdiction_name="Michigan",
            default_court_rules="MCR",
            default_bates_prefix="PIGORS",
            deadline_rules={
                "answer":          (21, "MCR 2.108(A)(1)",  "Answer to complaint"),
                "response_motion": (21, "MCR 2.119(F)(1)",  "Response to motion"),
                "reply_brief":     (7,  "MCR 2.119(F)(2)",  "Reply brief"),
                "discovery":       (28, "MCR 2.302(B)",     "Discovery response"),
                "appeal_claim":    (21, "MCR 7.204(A)(1)",  "Claim of appeal"),
                "appeal_brief":    (56, "MCR 7.212(A)(1)",  "Appellant brief"),
                "cross_appeal":    (21, "MCR 7.207(A)(1)",  "Cross-appeal"),
                "motion_hearing":  (9,  "MCR 2.119(C)(1)",  "Motion hearing notice"),
                "ppo_response":    (14, "MCL 600.2950(12)", "PPO response"),
                "ppo_appeal":      (21, "MCL 600.2950(11)", "PPO appeal"),
            },
        )


# ---------------------------------------------------------------------------
# Supplementary table DDL (engine-managed, idempotent)
# ---------------------------------------------------------------------------

_DDL_CASE_LANES = """
CREATE TABLE IF NOT EXISTS case_lanes (
    case_id     INTEGER PRIMARY KEY REFERENCES cases(id),
    lane        TEXT NOT NULL,
    meek_signal TEXT,
    assigned_at TEXT NOT NULL DEFAULT (datetime('now')),
    notes       TEXT
);
"""

_DDL_EVIDENCE_CLAIMS = """
CREATE TABLE IF NOT EXISTS evidence_claims (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    evidence_id INTEGER NOT NULL REFERENCES evidence(id),
    claim_id    INTEGER NOT NULL REFERENCES claims(id),
    strength    TEXT NOT NULL DEFAULT 'moderate',
    notes       TEXT,
    linked_at   TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(evidence_id, claim_id)
);
"""

_DDL_FILING_TRANSITIONS = """
CREATE TABLE IF NOT EXISTS filing_transitions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    filing_id   INTEGER NOT NULL REFERENCES filings(id),
    from_status TEXT NOT NULL,
    to_status   TEXT NOT NULL,
    changed_by  TEXT,
    notes       TEXT,
    changed_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

_DDL_CLAIMS_FTS = """
CREATE VIRTUAL TABLE IF NOT EXISTS claims_fts USING fts5(
    title, legal_basis, notes,
    content=claims,
    content_rowid=id
);
"""

_DDL_CLAIMS_FTS_TRIGGERS = [
    """
    CREATE TRIGGER IF NOT EXISTS claims_ai AFTER INSERT ON claims BEGIN
        INSERT INTO claims_fts(rowid, title, legal_basis, notes)
        VALUES (new.id, new.title, new.legal_basis, new.notes);
    END;
    """,
    """
    CREATE TRIGGER IF NOT EXISTS claims_ad AFTER DELETE ON claims BEGIN
        INSERT INTO claims_fts(claims_fts, rowid, title, legal_basis, notes)
        VALUES ('delete', old.id, old.title, old.legal_basis, old.notes);
    END;
    """,
    """
    CREATE TRIGGER IF NOT EXISTS claims_au AFTER UPDATE ON claims BEGIN
        INSERT INTO claims_fts(claims_fts, rowid, title, legal_basis, notes)
        VALUES ('delete', old.id, old.title, old.legal_basis, old.notes);
        INSERT INTO claims_fts(rowid, title, legal_basis, notes)
        VALUES (new.id, new.title, new.legal_basis, new.notes);
    END;
    """,
]


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class CaseEngine:
    """Universal case management engine.

    Orchestrates the full case lifecycle — creation, party management,
    lane routing, evidence chain linkage, claims tracking, deadline
    management, and filing workflow state transitions.

    Args:
        db: A ``DatabaseManager`` instance for all persistence.
        jurisdiction: Jurisdiction plugin (defaults to Michigan).
    """

    def __init__(
        self,
        db: "DatabaseManager",
        *,
        jurisdiction: Optional[JurisdictionPlugin] = None,
    ) -> None:
        self._db = db
        self.jurisdiction = jurisdiction or JurisdictionPlugin.michigan()
        self._ensure_tables()

    # -- Schema bootstrap -----------------------------------------------------

    def _ensure_tables(self) -> None:
        """Create supplementary tables if they do not yet exist."""
        conn = self._db.connect()
        try:
            conn.execute(_DDL_CASE_LANES)
            conn.execute(_DDL_EVIDENCE_CLAIMS)
            conn.execute(_DDL_FILING_TRANSITIONS)
            # FTS5 for claims — wrapped in try/except because the content
            # table may not exist yet during first-time init.
            try:
                conn.execute(_DDL_CLAIMS_FTS)
                for trigger_sql in _DDL_CLAIMS_FTS_TRIGGERS:
                    conn.execute(trigger_sql)
            except Exception:
                logger.debug("Claims FTS setup deferred (content table may be pending)")
            conn.commit()
        except Exception:
            conn.rollback()
            logger.exception("Failed to bootstrap CaseEngine tables")
            raise
        finally:
            conn.close()

    # =====================================================================
    # CASE CRUD
    # =====================================================================

    def create_case(
        self,
        title: str,
        *,
        case_number: Optional[str] = None,
        case_type: Optional[str] = None,
        court_id: Optional[int] = None,
        filed_date: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> int:
        """Create a new case and auto-assign its lane.

        Args:
            title: Descriptive case title (required).
            case_number: Court-assigned case number.
            case_type: One of ``VALID_CASE_TYPES``.
            court_id: FK into the ``courts`` table.
            filed_date: ISO-8601 date the case was filed.
            notes: Free-text notes.

        Returns:
            The new case row ID.

        Raises:
            ValueError: If *case_type* is not recognised.
        """
        if case_type and case_type not in VALID_CASE_TYPES:
            raise ValueError(
                f"Invalid case_type '{case_type}'. "
                f"Must be one of {VALID_CASE_TYPES}"
            )

        conn = self._db.connect()
        try:
            cursor = conn.execute(
                "INSERT INTO cases "
                "(case_number, court_id, case_type, title, filed_date, "
                " status, notes, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, 'active', ?, datetime('now'), datetime('now'))",
                (case_number, court_id, case_type, title, filed_date, notes),
            )
            conn.commit()
            case_id = cursor.lastrowid
            logger.info("Created case %d: %s", case_id, title)
        except Exception:
            conn.rollback()
            logger.exception("Failed to create case: %s", title)
            raise
        finally:
            conn.close()

        # Auto-assign lane from title + case_type + notes
        self._auto_assign_lane(case_id, title, case_type, notes)
        return case_id

    def get_case(self, case_id: int) -> dict:
        """Fetch a single case by ID.

        Raises:
            LookupError: If the case does not exist.
        """
        row = self._db.fetchone("SELECT * FROM cases WHERE id = ?", (case_id,))
        if row is None:
            raise LookupError(f"Case {case_id} not found.")
        return dict(row)

    def list_cases(
        self,
        *,
        status: Optional[str] = None,
        case_type: Optional[str] = None,
        lane: Optional[str] = None,
    ) -> list[dict]:
        """List cases with optional filters.

        Args:
            status: Filter by case status.
            case_type: Filter by case type.
            lane: Filter by assigned lane letter (A-F).

        Returns:
            List of case dicts.
        """
        clauses: list[str] = []
        params: list[Any] = []

        if status:
            clauses.append("c.status = ?")
            params.append(status)
        if case_type:
            clauses.append("c.case_type = ?")
            params.append(case_type)

        sql = "SELECT c.* FROM cases c"
        if lane:
            sql += " LEFT JOIN case_lanes cl ON cl.case_id = c.id"
            clauses.append("cl.lane = ?")
            params.append(lane)

        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY c.created_at DESC"

        rows = self._db.fetchall(sql, tuple(params))
        return [dict(r) for r in rows]

    def update_case(
        self,
        case_id: int,
        *,
        title: Optional[str] = None,
        status: Optional[str] = None,
        case_type: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> None:
        """Update mutable fields on a case.

        Only non-``None`` arguments are written; others are left unchanged.

        Raises:
            ValueError: If *status* or *case_type* is invalid.
            LookupError: If the case does not exist.
        """
        if status and status not in VALID_CASE_STATUSES:
            raise ValueError(f"Invalid status '{status}'.")
        if case_type and case_type not in VALID_CASE_TYPES:
            raise ValueError(f"Invalid case_type '{case_type}'.")

        # Verify existence
        self.get_case(case_id)

        sets: list[str] = ["updated_at = datetime('now')"]
        params: list[Any] = []
        if title is not None:
            sets.append("title = ?")
            params.append(title)
        if status is not None:
            sets.append("status = ?")
            params.append(status)
        if case_type is not None:
            sets.append("case_type = ?")
            params.append(case_type)
        if notes is not None:
            sets.append("notes = ?")
            params.append(notes)

        params.append(case_id)
        self._db.execute(
            f"UPDATE cases SET {', '.join(sets)} WHERE id = ?",
            tuple(params),
        )
        logger.info("Updated case %d", case_id)

    def get_case_summary(self, case_id: int) -> CaseSummary:
        """Build a rich summary with aggregated entity counts.

        Uses a single consolidated query for efficiency (see SQLite memory
        instructions — consolidate COUNT(*) calls).
        """
        case = self.get_case(case_id)

        row = self._db.fetchone(
            """
            SELECT
                (SELECT COUNT(*) FROM parties   WHERE case_id = ?) AS party_count,
                (SELECT COUNT(*) FROM claims    WHERE case_id = ?) AS claim_count,
                (SELECT COUNT(*) FROM evidence  WHERE case_id = ?) AS evidence_count,
                (SELECT COUNT(*) FROM filings   WHERE case_id = ?) AS filing_count,
                (SELECT COUNT(*) FROM deadlines WHERE case_id = ?) AS deadline_count
            """,
            (case_id, case_id, case_id, case_id, case_id),
        )
        counts = dict(row) if row else {}

        lane_row = self._db.fetchone(
            "SELECT lane FROM case_lanes WHERE case_id = ?", (case_id,),
        )
        lane = dict(lane_row)["lane"] if lane_row else None

        return CaseSummary(
            id=case["id"],
            case_number=case.get("case_number"),
            title=case["title"],
            case_type=case.get("case_type"),
            status=case.get("status", "active"),
            lane=lane,
            party_count=counts.get("party_count", 0),
            claim_count=counts.get("claim_count", 0),
            evidence_count=counts.get("evidence_count", 0),
            filing_count=counts.get("filing_count", 0),
            deadline_count=counts.get("deadline_count", 0),
            created_at=case.get("created_at"),
        )

    # =====================================================================
    # LANE ROUTING
    # =====================================================================

    def detect_lane(self, text: str) -> str:
        """Determine the best lane letter for arbitrary text.

        Detection priority: E → D → F → C → A → B (highest risk first).

        Args:
            text: Free-text to classify (title, notes, claims, etc.).

        Returns:
            Single-letter lane identifier (``'A'`` through ``'F'``).
        """
        text_lower = text.lower()
        for lane_letter in LANE_PRIORITY:
            pattern = CASE_LANES[lane_letter]["pattern"]
            if re.search(pattern, text_lower):
                return lane_letter
        return "A"  # default to custody (highest volume)

    def assign_lane(
        self,
        case_id: int,
        lane: str,
        *,
        notes: Optional[str] = None,
    ) -> None:
        """Explicitly assign a case to a lane.

        Args:
            case_id: The case to assign.
            lane: Lane letter (``'A'`` through ``'F'``).
            notes: Optional reason for the assignment.

        Raises:
            ValueError: If *lane* is not a valid lane letter.
        """
        if lane not in CASE_LANES:
            raise ValueError(
                f"Invalid lane '{lane}'. Must be one of {list(CASE_LANES.keys())}"
            )
        meek = CASE_LANES[lane]["meek"]
        conn = self._db.connect()
        try:
            conn.execute(
                "INSERT INTO case_lanes (case_id, lane, meek_signal, notes) "
                "VALUES (?, ?, ?, ?) "
                "ON CONFLICT(case_id) DO UPDATE SET "
                "  lane = excluded.lane, meek_signal = excluded.meek_signal, "
                "  notes = excluded.notes, assigned_at = datetime('now')",
                (case_id, lane, meek, notes),
            )
            conn.commit()
            logger.info("Case %d assigned to lane %s (%s)", case_id, lane,
                        CASE_LANES[lane]["name"])
        except Exception:
            conn.rollback()
            logger.exception("Failed to assign lane for case %d", case_id)
            raise
        finally:
            conn.close()

    def get_lane(self, case_id: int) -> Optional[str]:
        """Return the lane letter for a case, or ``None`` if unassigned."""
        row = self._db.fetchone(
            "SELECT lane FROM case_lanes WHERE case_id = ?", (case_id,),
        )
        return dict(row)["lane"] if row else None

    def _auto_assign_lane(
        self,
        case_id: int,
        title: str,
        case_type: Optional[str],
        notes: Optional[str],
    ) -> None:
        """Heuristically assign a lane from case metadata."""
        combined = f"{title} {case_type or ''} {notes or ''}"
        lane = self.detect_lane(combined)
        self.assign_lane(case_id, lane, notes="auto-detected on creation")

    # =====================================================================
    # PARTY MANAGEMENT
    # =====================================================================

    def add_party(
        self,
        case_id: int,
        name: str,
        role: str,
        *,
        party_type: Optional[str] = None,
        bar_number: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
    ) -> int:
        """Add a party to a case.

        Args:
            case_id: The case to add the party to.
            name: Full legal name.
            role: One of ``VALID_PARTY_ROLES``.
            party_type: ``'individual'``, ``'corporation'``, etc.
            bar_number: Attorney bar number (if applicable).
            email: Contact email.
            phone: Contact phone.
            address: Mailing address.

        Returns:
            The new party row ID.

        Raises:
            ValueError: If *role* is not recognised.
        """
        if role not in VALID_PARTY_ROLES:
            raise ValueError(
                f"Invalid role '{role}'. Must be one of {VALID_PARTY_ROLES}"
            )

        conn = self._db.connect()
        try:
            cursor = conn.execute(
                "INSERT INTO parties "
                "(case_id, name, role, party_type, bar_number, email, phone, address) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (case_id, name, role, party_type, bar_number, email, phone, address),
            )
            conn.commit()
            party_id = cursor.lastrowid
            logger.info("Added party %d (%s) as %s to case %d",
                        party_id, name, role, case_id)
            return party_id
        except Exception:
            conn.rollback()
            logger.exception("Failed to add party %s to case %d", name, case_id)
            raise
        finally:
            conn.close()

    def get_parties(
        self,
        case_id: int,
        *,
        role: Optional[str] = None,
    ) -> list[dict]:
        """List parties in a case, optionally filtered by role."""
        if role:
            rows = self._db.fetchall(
                "SELECT * FROM parties WHERE case_id = ? AND role = ? ORDER BY name",
                (case_id, role),
            )
        else:
            rows = self._db.fetchall(
                "SELECT * FROM parties WHERE case_id = ? ORDER BY role, name",
                (case_id,),
            )
        return [dict(r) for r in rows]

    def remove_party(self, party_id: int) -> None:
        """Remove a party from a case.

        Raises:
            LookupError: If the party does not exist.
        """
        row = self._db.fetchone("SELECT id FROM parties WHERE id = ?", (party_id,))
        if row is None:
            raise LookupError(f"Party {party_id} not found.")
        self._db.execute("DELETE FROM parties WHERE id = ?", (party_id,))
        logger.info("Removed party %d", party_id)

    # =====================================================================
    # CLAIMS / COUNTS
    # =====================================================================

    def add_claim(
        self,
        case_id: int,
        title: str,
        *,
        count_number: Optional[int] = None,
        legal_basis: Optional[str] = None,
        against_party_id: Optional[int] = None,
        damages_sought: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> int:
        """Add a legal claim or count to a case.

        Args:
            case_id: The case this claim belongs to.
            title: Short descriptive title (e.g. "Breach of Fiduciary Duty").
            count_number: Count number in the complaint.
            legal_basis: Statutory or rule citation (e.g. ``'MCL 600.2911'``).
            against_party_id: FK to the party this claim is against.
            damages_sought: Dollar amount of damages sought.
            notes: Free-text notes.

        Returns:
            The new claim row ID.
        """
        conn = self._db.connect()
        try:
            cursor = conn.execute(
                "INSERT INTO claims "
                "(case_id, count_number, title, legal_basis, against_party_id, "
                " status, damages_sought, notes) "
                "VALUES (?, ?, ?, ?, ?, 'active', ?, ?)",
                (case_id, count_number, title, legal_basis,
                 against_party_id, damages_sought, notes),
            )
            conn.commit()
            claim_id = cursor.lastrowid
            logger.info("Added claim %d (Count %s) to case %d",
                        claim_id, count_number, case_id)
            return claim_id
        except Exception:
            conn.rollback()
            logger.exception("Failed to add claim to case %d", case_id)
            raise
        finally:
            conn.close()

    def get_claims(
        self,
        case_id: int,
        *,
        status: Optional[str] = None,
    ) -> list[dict]:
        """List claims for a case, optionally filtered by status."""
        if status:
            if status not in VALID_CLAIM_STATUSES:
                raise ValueError(f"Invalid claim status '{status}'.")
            rows = self._db.fetchall(
                "SELECT * FROM claims WHERE case_id = ? AND status = ? "
                "ORDER BY count_number",
                (case_id, status),
            )
        else:
            rows = self._db.fetchall(
                "SELECT * FROM claims WHERE case_id = ? ORDER BY count_number",
                (case_id,),
            )
        return [dict(r) for r in rows]

    def update_claim_status(self, claim_id: int, new_status: str) -> None:
        """Transition a claim to a new status.

        Raises:
            ValueError: If *new_status* is not valid.
        """
        if new_status not in VALID_CLAIM_STATUSES:
            raise ValueError(
                f"Invalid status '{new_status}'. "
                f"Must be one of {VALID_CLAIM_STATUSES}"
            )
        self._db.execute(
            "UPDATE claims SET status = ? WHERE id = ?",
            (new_status, claim_id),
        )
        logger.info("Claim %d status → %s", claim_id, new_status)

    def search_claims(self, query: str, case_id: Optional[int] = None) -> list[dict]:
        """Full-text search across claims using FTS5.

        Args:
            query: FTS5 search expression.
            case_id: Optional case filter.

        Returns:
            List of matching claim dicts.
        """
        if case_id is not None:
            rows = self._db.fetchall(
                "SELECT cl.* FROM claims_fts fts "
                "JOIN claims cl ON fts.rowid = cl.id "
                "WHERE claims_fts MATCH ? AND cl.case_id = ?",
                (query, case_id),
            )
        else:
            rows = self._db.fetchall(
                "SELECT cl.* FROM claims_fts fts "
                "JOIN claims cl ON fts.rowid = cl.id "
                "WHERE claims_fts MATCH ?",
                (query,),
            )
        return [dict(r) for r in rows]

    # =====================================================================
    # EVIDENCE CHAIN
    # =====================================================================

    def link_evidence_to_claim(
        self,
        evidence_id: int,
        claim_id: int,
        *,
        strength: str = "moderate",
        notes: Optional[str] = None,
    ) -> int:
        """Link an evidence item to a claim with a strength score.

        Args:
            evidence_id: FK to the evidence table.
            claim_id: FK to the claims table.
            strength: One of ``VALID_EVIDENCE_STRENGTHS``.
            notes: Optional notes about the linkage.

        Returns:
            The evidence_claims row ID.

        Raises:
            ValueError: If *strength* is invalid.
        """
        if strength not in VALID_EVIDENCE_STRENGTHS:
            raise ValueError(
                f"Invalid strength '{strength}'. "
                f"Must be one of {VALID_EVIDENCE_STRENGTHS}"
            )

        conn = self._db.connect()
        try:
            cursor = conn.execute(
                "INSERT INTO evidence_claims (evidence_id, claim_id, strength, notes) "
                "VALUES (?, ?, ?, ?) "
                "ON CONFLICT(evidence_id, claim_id) DO UPDATE SET "
                "  strength = excluded.strength, notes = excluded.notes, "
                "  linked_at = datetime('now')",
                (evidence_id, claim_id, strength, notes),
            )
            conn.commit()
            link_id = cursor.lastrowid
            logger.info("Linked evidence %d → claim %d (strength=%s)",
                        evidence_id, claim_id, strength)
            return link_id
        except Exception:
            conn.rollback()
            logger.exception("Failed to link evidence %d to claim %d",
                             evidence_id, claim_id)
            raise
        finally:
            conn.close()

    def get_evidence_for_claim(self, claim_id: int) -> list[dict]:
        """Return all evidence linked to a claim with strength scores."""
        rows = self._db.fetchall(
            "SELECT e.*, ec.strength, ec.notes AS link_notes, ec.linked_at "
            "FROM evidence_claims ec "
            "JOIN evidence e ON e.id = ec.evidence_id "
            "WHERE ec.claim_id = ? "
            "ORDER BY ec.strength DESC, ec.linked_at ASC",
            (claim_id,),
        )
        return [dict(r) for r in rows]

    def get_claims_for_evidence(self, evidence_id: int) -> list[dict]:
        """Return all claims linked to an evidence item."""
        rows = self._db.fetchall(
            "SELECT cl.*, ec.strength, ec.notes AS link_notes "
            "FROM evidence_claims ec "
            "JOIN claims cl ON cl.id = ec.claim_id "
            "WHERE ec.evidence_id = ? "
            "ORDER BY cl.count_number",
            (evidence_id,),
        )
        return [dict(r) for r in rows]

    def score_evidence_strength(self, case_id: int) -> list[dict]:
        """Score evidence sufficiency per claim.

        Returns a list of ``{"claim_id", "claim_title", "evidence_count",
        "strong_count", "score"}`` dicts.  Score is 0–100.
        """
        claims = self.get_claims(case_id, status="active")
        results: list[dict] = []

        for claim in claims:
            linked = self.get_evidence_for_claim(claim["id"])
            strong = sum(1 for e in linked if e.get("strength") == "strong")
            moderate = sum(1 for e in linked if e.get("strength") == "moderate")
            total = len(linked)

            # Weighted score: strong=40pts, moderate=20pts, weak=5pts each, cap 100
            score = min(100, strong * 40 + moderate * 20 + (total - strong - moderate) * 5)

            results.append({
                "claim_id": claim["id"],
                "claim_title": claim.get("title"),
                "evidence_count": total,
                "strong_count": strong,
                "score": score,
            })

        return results

    # =====================================================================
    # DEADLINE MANAGEMENT
    # =====================================================================

    def add_deadline(
        self,
        case_id: int,
        title: str,
        due_date: str,
        *,
        rule_basis: Optional[str] = None,
        priority: str = "normal",
        filing_id: Optional[int] = None,
        reminder_days: int = 7,
        notes: Optional[str] = None,
    ) -> int:
        """Add a deadline to a case.

        Args:
            case_id: The case this deadline belongs to.
            title: Description of what is due.
            due_date: ISO-8601 date string.
            rule_basis: Court rule citation (e.g. ``'MCR 2.108(A)(1)'``).
            priority: ``'critical'``, ``'high'``, ``'normal'``, or ``'low'``.
            filing_id: Optional FK to the filing this deadline is for.
            reminder_days: Days before due date to trigger reminders.
            notes: Free-text notes.

        Returns:
            The new deadline row ID.
        """
        conn = self._db.connect()
        try:
            cursor = conn.execute(
                "INSERT INTO deadlines "
                "(case_id, filing_id, title, due_date, rule_basis, "
                " status, priority, reminder_days, notes) "
                "VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?)",
                (case_id, filing_id, title, due_date, rule_basis,
                 priority, reminder_days, notes),
            )
            conn.commit()
            dl_id = cursor.lastrowid
            logger.info("Added deadline %d for case %d: %s (due %s)",
                        dl_id, case_id, title, due_date)
            return dl_id
        except Exception:
            conn.rollback()
            logger.exception("Failed to add deadline for case %d", case_id)
            raise
        finally:
            conn.close()

    def get_upcoming_deadlines(
        self,
        case_id: int,
        days: int = 30,
    ) -> list[dict]:
        """Return deadlines due within *days* from today."""
        cutoff = (date.today() + __import__("datetime").timedelta(days=days)).isoformat()
        rows = self._db.fetchall(
            "SELECT * FROM deadlines "
            "WHERE case_id = ? AND status = 'pending' AND due_date <= ? "
            "ORDER BY due_date ASC",
            (case_id, cutoff),
        )
        return [dict(r) for r in rows]

    def get_overdue_deadlines(self, case_id: int) -> list[dict]:
        """Return all overdue, still-pending deadlines."""
        today = date.today().isoformat()
        rows = self._db.fetchall(
            "SELECT * FROM deadlines "
            "WHERE case_id = ? AND status = 'pending' AND due_date < ? "
            "ORDER BY due_date ASC",
            (case_id, today),
        )
        return [dict(r) for r in rows]

    def calculate_deadline(
        self,
        filing_type: str,
        trigger_date: str,
    ) -> Optional[dict]:
        """Calculate a deadline using jurisdiction-specific rules.

        Args:
            filing_type: Key into the jurisdiction's ``deadline_rules``.
            trigger_date: ISO-8601 date the clock started.

        Returns:
            Dict with ``due_date``, ``rule_basis``, ``description``, and
            ``calendar_days``, or ``None`` if no rule is registered.
        """
        rule = self.jurisdiction.deadline_rules.get(filing_type)
        if rule is None:
            return None

        cal_days, rule_basis, description = rule
        trigger = date.fromisoformat(trigger_date)
        due = trigger + __import__("datetime").timedelta(days=cal_days)

        # Push weekends forward
        while due.weekday() >= 5:
            due += __import__("datetime").timedelta(days=1)

        return {
            "due_date": due.isoformat(),
            "rule_basis": rule_basis,
            "description": description,
            "calendar_days": cal_days,
        }

    # =====================================================================
    # FILING WORKFLOW STATE MACHINE
    # =====================================================================

    def advance_filing(
        self,
        filing_id: int,
        to_status: str,
        *,
        changed_by: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> None:
        """Transition a filing through the state machine.

        Allowed transitions::

            draft → review → qa → ready → filed → served
            (any intermediate state may retreat back to draft)

        Args:
            filing_id: The filing to transition.
            to_status: Target status.
            changed_by: Who initiated the change.
            notes: Reason for the transition.

        Raises:
            ValueError: If the transition is invalid.
            LookupError: If the filing does not exist.
        """
        if to_status not in FILING_STATUS_ORDER:
            raise ValueError(
                f"Invalid status '{to_status}'. "
                f"Must be one of {FILING_STATUS_ORDER}"
            )

        row = self._db.fetchone("SELECT * FROM filings WHERE id = ?", (filing_id,))
        if row is None:
            raise LookupError(f"Filing {filing_id} not found.")

        current = dict(row).get("status", "draft")
        allowed = _FORWARD_TRANSITIONS.get(current, ())
        if to_status not in allowed:
            raise ValueError(
                f"Cannot transition filing {filing_id} from '{current}' to "
                f"'{to_status}'. Allowed: {allowed}"
            )

        conn = self._db.connect()
        try:
            # Update the filing status
            update_cols = "status = ?"
            update_params: list[Any] = [to_status]
            if to_status == "filed":
                update_cols += ", filed_date = date('now')"
            if to_status == "served":
                update_cols += ", served_date = date('now')"
            update_params.append(filing_id)

            conn.execute(
                f"UPDATE filings SET {update_cols} WHERE id = ?",
                tuple(update_params),
            )

            # Record the transition in the audit trail
            conn.execute(
                "INSERT INTO filing_transitions "
                "(filing_id, from_status, to_status, changed_by, notes) "
                "VALUES (?, ?, ?, ?, ?)",
                (filing_id, current, to_status, changed_by, notes),
            )
            conn.commit()
            logger.info("Filing %d: %s → %s (by %s)",
                        filing_id, current, to_status, changed_by or "system")
        except Exception:
            conn.rollback()
            logger.exception("Failed to advance filing %d", filing_id)
            raise
        finally:
            conn.close()

    def get_filing_history(self, filing_id: int) -> list[dict]:
        """Return the full audit trail for a filing's status changes."""
        rows = self._db.fetchall(
            "SELECT * FROM filing_transitions "
            "WHERE filing_id = ? ORDER BY changed_at ASC",
            (filing_id,),
        )
        return [dict(r) for r in rows]

    # =====================================================================
    # TIMELINE
    # =====================================================================

    def add_timeline_event(
        self,
        case_id: int,
        event_date: str,
        title: str,
        *,
        description: Optional[str] = None,
        event_type: Optional[str] = None,
        evidence_ids: Optional[Sequence[int]] = None,
        filing_id: Optional[int] = None,
        importance: str = "normal",
    ) -> int:
        """Record a timeline event for a case.

        Args:
            case_id: The case this event belongs to.
            event_date: ISO-8601 date string.
            title: Short event title.
            description: Detailed description.
            event_type: Category (``'filing'``, ``'hearing'``, ``'order'``, etc.).
            evidence_ids: List of evidence IDs linked to this event.
            filing_id: Optional FK to a filing.
            importance: ``'critical'``, ``'high'``, ``'normal'``, or ``'low'``.

        Returns:
            The new timeline_events row ID.
        """
        ev_json = json.dumps(evidence_ids) if evidence_ids else None

        conn = self._db.connect()
        try:
            cursor = conn.execute(
                "INSERT INTO timeline_events "
                "(case_id, event_date, title, description, event_type, "
                " evidence_ids, filing_id, importance) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (case_id, event_date, title, description, event_type,
                 ev_json, filing_id, importance),
            )
            conn.commit()
            event_id = cursor.lastrowid
            logger.info("Added timeline event %d for case %d: %s",
                        event_id, case_id, title)
            return event_id
        except Exception:
            conn.rollback()
            logger.exception("Failed to add timeline event for case %d", case_id)
            raise
        finally:
            conn.close()

    def get_timeline(self, case_id: int) -> CaseTimeline:
        """Build a complete chronological timeline for a case."""
        rows = self._db.fetchall(
            "SELECT * FROM timeline_events "
            "WHERE case_id = ? ORDER BY event_date ASC",
            (case_id,),
        )
        events: list[dict[str, Any]] = []
        for r in rows:
            ev = dict(r)
            # Deserialise evidence_ids from JSON
            if ev.get("evidence_ids"):
                try:
                    ev["evidence_ids"] = json.loads(ev["evidence_ids"])
                except (json.JSONDecodeError, TypeError):
                    pass
            events.append(ev)

        return CaseTimeline(case_id=case_id, events=events)

    # =====================================================================
    # SEARCH
    # =====================================================================

    def search(self, query: str, *, case_id: Optional[int] = None) -> dict:
        """Unified full-text search across evidence and claims.

        Args:
            query: FTS5 search expression.
            case_id: Optional case filter.

        Returns:
            Dict with ``evidence`` and ``claims`` result lists.
        """
        evidence_results: list[dict] = []
        claims_results: list[dict] = []

        # Search evidence FTS
        try:
            if case_id is not None:
                ev_rows = self._db.fetchall(
                    "SELECT e.* FROM evidence_fts fts "
                    "JOIN evidence e ON fts.rowid = e.id "
                    "WHERE evidence_fts MATCH ? AND e.case_id = ?",
                    (query, case_id),
                )
            else:
                ev_rows = self._db.fetchall(
                    "SELECT e.* FROM evidence_fts fts "
                    "JOIN evidence e ON fts.rowid = e.id "
                    "WHERE evidence_fts MATCH ?",
                    (query,),
                )
            evidence_results = [dict(r) for r in ev_rows]
        except Exception:
            logger.debug("Evidence FTS search failed (table may not exist)")

        # Search claims FTS
        try:
            if case_id is not None:
                cl_rows = self._db.fetchall(
                    "SELECT cl.* FROM claims_fts fts "
                    "JOIN claims cl ON fts.rowid = cl.id "
                    "WHERE claims_fts MATCH ? AND cl.case_id = ?",
                    (query, case_id),
                )
            else:
                cl_rows = self._db.fetchall(
                    "SELECT cl.* FROM claims_fts fts "
                    "JOIN claims cl ON fts.rowid = cl.id "
                    "WHERE claims_fts MATCH ?",
                    (query,),
                )
            claims_results = [dict(r) for r in cl_rows]
        except Exception:
            logger.debug("Claims FTS search failed (table may not exist)")

        return {"evidence": evidence_results, "claims": claims_results}
