"""LitigationOS Court Order Tracker v1.0
========================================
Court order cataloging, compliance monitoring, violation detection,
conflict analysis, and contempt proceedings for Michigan family-law
litigation.

Covers MCR 3.606 (contempt), MCR 2.612 (relief from judgment/order),
MCR 3.211 (change of custody), MCR 3.706 (PPO proceedings),
MCL 600.1701 (contempt power), MCL 722.27 (custody modification),
and MCL 600.2950 (PPO statutes).

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
from decimal import Decimal, ROUND_HALF_UP
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
# DB
# ---------------------------------------------------------------------------
_PRAGMAS = """\
PRAGMA busy_timeout = 60000;
PRAGMA journal_mode = WAL;
PRAGMA cache_size  = -32000;
PRAGMA synchronous = NORMAL;
PRAGMA temp_store  = MEMORY;
"""

_SCHEMA = """\
CREATE TABLE IF NOT EXISTS court_orders (
    order_id        TEXT PRIMARY KEY,
    case_number     TEXT NOT NULL,
    case_lane       TEXT NOT NULL DEFAULT '',
    court           TEXT NOT NULL DEFAULT '',
    judge           TEXT NOT NULL DEFAULT '',
    order_type      TEXT NOT NULL DEFAULT 'TEMPORARY',
    date_entered    TEXT NOT NULL DEFAULT '',
    date_effective  TEXT NOT NULL DEFAULT '',
    date_expires    TEXT,
    status          TEXT NOT NULL DEFAULT 'ACTIVE',
    superseded_by   TEXT,
    related_orders  TEXT NOT NULL DEFAULT '[]',
    filing_ref      TEXT NOT NULL DEFAULT '',
    notes           TEXT NOT NULL DEFAULT '',
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS order_provisions (
    provision_id       TEXT PRIMARY KEY,
    order_id           TEXT NOT NULL,
    description        TEXT NOT NULL DEFAULT '',
    compliance_status  TEXT NOT NULL DEFAULT 'UNKNOWN',
    responsible_party  TEXT NOT NULL DEFAULT '',
    deadline           TEXT,
    evidence_of_compliance TEXT NOT NULL DEFAULT '[]',
    evidence_of_violation  TEXT NOT NULL DEFAULT '[]',
    last_checked       TEXT,
    created_at         TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at         TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    FOREIGN KEY (order_id) REFERENCES court_orders(order_id)
);

CREATE TABLE IF NOT EXISTS compliance_checks (
    check_id        TEXT PRIMARY KEY,
    order_id        TEXT NOT NULL,
    provision_id    TEXT,
    check_date      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    status_before   TEXT NOT NULL DEFAULT '',
    status_after    TEXT NOT NULL DEFAULT '',
    findings        TEXT NOT NULL DEFAULT '',
    evidence_refs   TEXT NOT NULL DEFAULT '[]',
    checked_by      TEXT NOT NULL DEFAULT 'SYSTEM',
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    FOREIGN KEY (order_id) REFERENCES court_orders(order_id)
);

CREATE TABLE IF NOT EXISTS contempt_actions (
    action_id       TEXT PRIMARY KEY,
    order_id        TEXT NOT NULL,
    provision_id    TEXT,
    action_type     TEXT NOT NULL DEFAULT 'CONTEMPT',
    motion_text     TEXT NOT NULL DEFAULT '',
    filed_date      TEXT,
    status          TEXT NOT NULL DEFAULT 'PENDING',
    purge_conditions TEXT NOT NULL DEFAULT '[]',
    notes           TEXT NOT NULL DEFAULT '',
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    FOREIGN KEY (order_id) REFERENCES court_orders(order_id)
);

CREATE INDEX IF NOT EXISTS idx_orders_case
    ON court_orders(case_number, case_lane);
CREATE INDEX IF NOT EXISTS idx_orders_type
    ON court_orders(order_type);
CREATE INDEX IF NOT EXISTS idx_orders_status
    ON court_orders(status);
CREATE INDEX IF NOT EXISTS idx_provisions_order
    ON order_provisions(order_id);
CREATE INDEX IF NOT EXISTS idx_provisions_status
    ON order_provisions(compliance_status);
CREATE INDEX IF NOT EXISTS idx_compliance_order
    ON compliance_checks(order_id);
CREATE INDEX IF NOT EXISTS idx_contempt_order
    ON contempt_actions(order_id);
"""


# ═══════════════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════════════

class OrderType(Enum):
    """Classification of court orders."""
    CUSTODY = "CUSTODY"
    PARENTING_TIME = "PARENTING_TIME"
    CHILD_SUPPORT = "CHILD_SUPPORT"
    PPO = "PPO"
    TEMPORARY = "TEMPORARY"
    FINAL = "FINAL"
    CONSENT = "CONSENT"
    EX_PARTE = "EX_PARTE"
    SHOW_CAUSE = "SHOW_CAUSE"
    STIPULATED = "STIPULATED"


class ComplianceStatus(Enum):
    """Status of compliance with an order provision."""
    COMPLIANT = "COMPLIANT"
    PARTIAL = "PARTIAL"
    NONCOMPLIANT = "NONCOMPLIANT"
    DISPUTED = "DISPUTED"
    UNKNOWN = "UNKNOWN"
    EXPIRED = "EXPIRED"
    SUPERSEDED = "SUPERSEDED"


class ViolationSeverity(Enum):
    """Severity classification for order violations."""
    MINOR = "MINOR"
    MODERATE = "MODERATE"
    SEVERE = "SEVERE"
    WILLFUL = "WILLFUL"


class OrderStatus(Enum):
    """Lifecycle state of a court order."""
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    SUPERSEDED = "SUPERSEDED"
    VACATED = "VACATED"
    MODIFIED = "MODIFIED"
    APPEALED = "APPEALED"


# ═══════════════════════════════════════════════════════════════════════════
# Dataclasses
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class OrderProvision:
    """Single enforceable provision within a court order."""

    provision_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str = ""
    description: str = ""
    compliance_status: ComplianceStatus = ComplianceStatus.UNKNOWN
    responsible_party: str = ""
    deadline: Optional[str] = None
    evidence_of_compliance: List[str] = field(default_factory=list)
    evidence_of_violation: List[str] = field(default_factory=list)
    last_checked: Optional[str] = None

    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "provision_id": self.provision_id,
            "order_id": self.order_id,
            "description": self.description,
            "compliance_status": self.compliance_status.value,
            "responsible_party": self.responsible_party,
            "deadline": self.deadline,
            "evidence_of_compliance": list(self.evidence_of_compliance),
            "evidence_of_violation": list(self.evidence_of_violation),
            "last_checked": self.last_checked,
        }

    # ------------------------------------------------------------------
    def is_violated(self) -> bool:
        """Return True if the provision is in a non-compliant state."""
        return self.compliance_status in (
            ComplianceStatus.NONCOMPLIANT,
            ComplianceStatus.PARTIAL,
        )

    # ------------------------------------------------------------------
    @classmethod
    def from_row(cls, row: sqlite3.Row) -> OrderProvision:
        d = dict(row)
        eoc = d.get("evidence_of_compliance", "[]")
        eov = d.get("evidence_of_violation", "[]")
        return cls(
            provision_id=d["provision_id"],
            order_id=d.get("order_id", ""),
            description=d.get("description", ""),
            compliance_status=ComplianceStatus(
                d.get("compliance_status", "UNKNOWN"),
            ),
            responsible_party=d.get("responsible_party", ""),
            deadline=d.get("deadline"),
            evidence_of_compliance=(
                json.loads(eoc) if isinstance(eoc, str) else eoc
            ),
            evidence_of_violation=(
                json.loads(eov) if isinstance(eov, str) else eov
            ),
            last_checked=d.get("last_checked"),
        )


@dataclass
class CourtOrder:
    """Full court order record with provisions and status tracking."""

    order_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    case_number: str = ""
    case_lane: str = ""
    court: str = ""
    judge: str = ""
    order_type: OrderType = OrderType.TEMPORARY
    date_entered: str = ""
    date_effective: str = ""
    date_expires: Optional[str] = None
    provisions: List[OrderProvision] = field(default_factory=list)
    status: OrderStatus = OrderStatus.ACTIVE
    superseded_by: Optional[str] = None
    related_orders: List[str] = field(default_factory=list)
    filing_ref: str = ""
    notes: str = ""

    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "order_id": self.order_id,
            "case_number": self.case_number,
            "case_lane": self.case_lane,
            "court": self.court,
            "judge": self.judge,
            "order_type": self.order_type.value,
            "date_entered": self.date_entered,
            "date_effective": self.date_effective,
            "date_expires": self.date_expires,
            "provisions": [p.to_dict() for p in self.provisions],
            "status": self.status.value,
            "superseded_by": self.superseded_by,
            "related_orders": list(self.related_orders),
            "filing_ref": self.filing_ref,
            "notes": self.notes,
        }

    # ------------------------------------------------------------------
    def is_active(self) -> bool:
        """Return True if the order is currently in effect."""
        if self.status != OrderStatus.ACTIVE:
            return False
        if self.date_expires:
            try:
                return date.today() <= date.fromisoformat(self.date_expires)
            except (ValueError, TypeError):
                pass
        return True

    # ------------------------------------------------------------------
    def is_expired(self) -> bool:
        """Return True if the order has passed its expiration date."""
        if not self.date_expires:
            return False
        try:
            return date.today() > date.fromisoformat(self.date_expires)
        except (ValueError, TypeError):
            return False

    # ------------------------------------------------------------------
    def days_since_entry(self) -> Optional[int]:
        """Days since the order was entered."""
        if not self.date_entered:
            return None
        try:
            entered = date.fromisoformat(self.date_entered)
            return (date.today() - entered).days
        except (ValueError, TypeError):
            return None

    # ------------------------------------------------------------------
    @classmethod
    def from_row(
        cls,
        row: sqlite3.Row,
        provisions: Optional[List[OrderProvision]] = None,
    ) -> CourtOrder:
        d = dict(row)
        rel = d.get("related_orders", "[]")
        return cls(
            order_id=d["order_id"],
            case_number=d.get("case_number", ""),
            case_lane=d.get("case_lane", ""),
            court=d.get("court", ""),
            judge=d.get("judge", ""),
            order_type=OrderType(d.get("order_type", "TEMPORARY")),
            date_entered=d.get("date_entered", ""),
            date_effective=d.get("date_effective", ""),
            date_expires=d.get("date_expires"),
            provisions=provisions or [],
            status=OrderStatus(d.get("status", "ACTIVE")),
            superseded_by=d.get("superseded_by"),
            related_orders=(
                json.loads(rel) if isinstance(rel, str) else rel
            ),
            filing_ref=d.get("filing_ref", ""),
            notes=d.get("notes", ""),
        )


@dataclass
class ViolationRecord:
    """Detailed violation record for reporting."""

    order_id: str = ""
    provision_id: str = ""
    order_type: str = ""
    provision_description: str = ""
    responsible_party: str = ""
    severity: ViolationSeverity = ViolationSeverity.MODERATE
    evidence: List[str] = field(default_factory=list)
    date_detected: str = ""
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "order_id": self.order_id,
            "provision_id": self.provision_id,
            "order_type": self.order_type,
            "provision_description": self.provision_description,
            "responsible_party": self.responsible_party,
            "severity": self.severity.value,
            "evidence": list(self.evidence),
            "date_detected": self.date_detected,
            "notes": self.notes,
        }


@dataclass
class ConflictRecord:
    """Record of a conflict between two order provisions."""

    order_a_id: str = ""
    order_b_id: str = ""
    provision_a: str = ""
    provision_b: str = ""
    conflict_type: str = ""
    description: str = ""
    recommendation: str = ""

    def to_dict(self) -> dict:
        return {
            "order_a_id": self.order_a_id,
            "order_b_id": self.order_b_id,
            "provision_a": self.provision_a,
            "provision_b": self.provision_b,
            "conflict_type": self.conflict_type,
            "description": self.description,
            "recommendation": self.recommendation,
        }


# ═══════════════════════════════════════════════════════════════════════════
# Database helpers
# ═══════════════════════════════════════════════════════════════════════════

def _get_conn(db_path: Optional[pathlib.Path] = None) -> sqlite3.Connection:
    p = db_path or _DB_PATH
    conn = sqlite3.connect(str(p), timeout=120)
    conn.executescript(_PRAGMAS)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(_SCHEMA)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today_iso() -> str:
    return date.today().isoformat()


# ═══════════════════════════════════════════════════════════════════════════
# ComplianceMonitor
# ═══════════════════════════════════════════════════════════════════════════

class ComplianceMonitor:
    """Monitor and assess compliance with court order provisions.

    Records compliance checks, detects violations, generates reports,
    and scores violation severity.
    """

    def __init__(self, conn: Optional[sqlite3.Connection] = None) -> None:
        self._conn = conn
        self._checks_count: int = 0

    def _db(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = _get_conn()
            _ensure_schema(self._conn)
        return self._conn

    # ------------------------------------------------------------------
    def check_compliance(
        self,
        order_id: str,
    ) -> List[Dict[str, Any]]:
        """Assess compliance of all provisions in an order.

        Returns a list of provision check results.
        """
        db = self._db()
        rows = db.execute(
            "SELECT * FROM order_provisions WHERE order_id = ?",
            (order_id,),
        ).fetchall()

        results: List[Dict[str, Any]] = []
        for row in rows:
            prov = OrderProvision.from_row(row)
            check_id = str(uuid.uuid4())

            result = {
                "check_id": check_id,
                "provision_id": prov.provision_id,
                "description": prov.description,
                "responsible_party": prov.responsible_party,
                "status_before": prov.compliance_status.value,
                "status_after": prov.compliance_status.value,
                "is_violated": prov.is_violated(),
                "evidence_of_compliance": prov.evidence_of_compliance,
                "evidence_of_violation": prov.evidence_of_violation,
            }

            if prov.deadline:
                try:
                    dl = date.fromisoformat(prov.deadline)
                    if date.today() > dl and prov.compliance_status not in (
                        ComplianceStatus.COMPLIANT,
                        ComplianceStatus.EXPIRED,
                        ComplianceStatus.SUPERSEDED,
                    ):
                        result["status_after"] = ComplianceStatus.NONCOMPLIANT.value
                        result["is_violated"] = True
                        result["deadline_passed"] = True
                except (ValueError, TypeError):
                    pass

            db.execute(
                "INSERT INTO compliance_checks "
                "(check_id, order_id, provision_id, status_before, "
                "status_after, findings, evidence_refs) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    check_id, order_id, prov.provision_id,
                    result["status_before"], result["status_after"],
                    json.dumps(result), "[]",
                ),
            )

            if result["status_after"] != result["status_before"]:
                db.execute(
                    "UPDATE order_provisions SET compliance_status = ?, "
                    "last_checked = ?, updated_at = ? WHERE provision_id = ?",
                    (result["status_after"], _now_iso(), _now_iso(),
                     prov.provision_id),
                )

            results.append(result)
            self._checks_count += 1

        db.commit()
        return results

    # ------------------------------------------------------------------
    def detect_violations(
        self,
        order_id: str,
    ) -> List[ViolationRecord]:
        """Find all violated provisions in an order."""
        db = self._db()
        order_row = db.execute(
            "SELECT * FROM court_orders WHERE order_id = ?",
            (order_id,),
        ).fetchone()

        if not order_row:
            return []

        prov_rows = db.execute(
            "SELECT * FROM order_provisions WHERE order_id = ? "
            "AND compliance_status IN (?, ?)",
            (order_id, ComplianceStatus.NONCOMPLIANT.value,
             ComplianceStatus.PARTIAL.value),
        ).fetchall()

        violations: List[ViolationRecord] = []
        for row in prov_rows:
            prov = OrderProvision.from_row(row)
            severity = self.calculate_violation_severity(prov)
            vr = ViolationRecord(
                order_id=order_id,
                provision_id=prov.provision_id,
                order_type=dict(order_row).get("order_type", ""),
                provision_description=prov.description,
                responsible_party=prov.responsible_party,
                severity=severity,
                evidence=list(prov.evidence_of_violation),
                date_detected=_today_iso(),
            )
            violations.append(vr)
        return violations

    # ------------------------------------------------------------------
    def generate_violation_report(
        self,
        order_id: str,
    ) -> str:
        """Generate a formatted violation report for a single order."""
        db = self._db()
        order_row = db.execute(
            "SELECT * FROM court_orders WHERE order_id = ?",
            (order_id,),
        ).fetchone()
        if not order_row:
            return f"Order {order_id} not found."

        od = dict(order_row)
        violations = self.detect_violations(order_id)

        lines: List[str] = []
        lines.append("VIOLATION REPORT")
        lines.append("=" * 60)
        lines.append(f"Order ID:     {order_id}")
        lines.append(f"Case:         {od.get('case_number', '')} (Lane {od.get('case_lane', '')})")
        lines.append(f"Type:         {od.get('order_type', '')}")
        lines.append(f"Judge:        {od.get('judge', '')}")
        lines.append(f"Date Entered: {od.get('date_entered', '')}")
        lines.append(f"Violations:   {len(violations)}")
        lines.append("")

        if not violations:
            lines.append("No violations detected.")
        else:
            for i, v in enumerate(violations, 1):
                lines.append(f"--- Violation #{i} ---")
                lines.append(f"  Provision: {v.provision_description}")
                lines.append(f"  Party:     {v.responsible_party}")
                lines.append(f"  Severity:  {v.severity.value}")
                lines.append(f"  Detected:  {v.date_detected}")
                if v.evidence:
                    lines.append(f"  Evidence:")
                    for ev in v.evidence:
                        lines.append(f"    • {ev}")
                lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    def track_compliance_over_time(
        self,
        order_id: str,
    ) -> List[Dict[str, Any]]:
        """Return the compliance check history for an order."""
        db = self._db()
        rows = db.execute(
            "SELECT * FROM compliance_checks WHERE order_id = ? "
            "ORDER BY check_date DESC",
            (order_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    def calculate_violation_severity(
        self,
        provision: OrderProvision,
    ) -> ViolationSeverity:
        """Classify the severity of a provision violation.

        Heuristic based on deadline lapse, evidence count, and party role.
        """
        score = 0

        if provision.compliance_status == ComplianceStatus.NONCOMPLIANT:
            score += 2
        elif provision.compliance_status == ComplianceStatus.PARTIAL:
            score += 1

        if provision.deadline:
            try:
                dl = date.fromisoformat(provision.deadline)
                days_past = (date.today() - dl).days
                if days_past > 30:
                    score += 3
                elif days_past > 14:
                    score += 2
                elif days_past > 0:
                    score += 1
            except (ValueError, TypeError):
                pass

        score += min(len(provision.evidence_of_violation), 3)

        desc_lower = provision.description.lower()
        high_priority_keywords = [
            "child", "custody", "safety", "emergency",
            "protection", "abuse", "neglect",
        ]
        if any(kw in desc_lower for kw in high_priority_keywords):
            score += 2

        if score >= 7:
            return ViolationSeverity.WILLFUL
        elif score >= 5:
            return ViolationSeverity.SEVERE
        elif score >= 3:
            return ViolationSeverity.MODERATE
        return ViolationSeverity.MINOR

    # ------------------------------------------------------------------
    def get_stats(self) -> dict:
        return {"compliance_checks_performed": self._checks_count}


# ═══════════════════════════════════════════════════════════════════════════
# OrderConflictDetector
# ═══════════════════════════════════════════════════════════════════════════

class OrderConflictDetector:
    """Detect conflicts, supersession gaps, and problematic ex parte orders.

    Analyses orders across case lanes to find contradictions and gaps.
    """

    _CONFLICT_KEYWORDS: Dict[str, List[str]] = {
        "custody": ["custody", "legal custody", "physical custody", "placement"],
        "parenting_time": ["parenting time", "visitation", "schedule", "overnight"],
        "support": ["child support", "support obligation", "payment"],
        "contact": ["no contact", "contact restriction", "communication"],
        "residence": ["residence", "primary residence", "domicile"],
    }

    # ------------------------------------------------------------------
    def detect_conflicts(
        self,
        orders: List[CourtOrder],
    ) -> List[ConflictRecord]:
        """Find conflicting provisions across active orders.

        Compares every pair of active orders for keyword overlap that
        suggests contradictory mandates.
        """
        active = [o for o in orders if o.is_active()]
        conflicts: List[ConflictRecord] = []

        for i, order_a in enumerate(active):
            for order_b in active[i + 1:]:
                pair_conflicts = self._check_pair(order_a, order_b)
                conflicts.extend(pair_conflicts)

        return conflicts

    # ------------------------------------------------------------------
    def _check_pair(
        self,
        order_a: CourtOrder,
        order_b: CourtOrder,
    ) -> List[ConflictRecord]:
        """Compare two orders for provision-level conflicts."""
        conflicts: List[ConflictRecord] = []

        for prov_a in order_a.provisions:
            for prov_b in order_b.provisions:
                conflict = self._provisions_conflict(
                    prov_a, prov_b, order_a, order_b,
                )
                if conflict:
                    conflicts.append(conflict)

        return conflicts

    # ------------------------------------------------------------------
    def _provisions_conflict(
        self,
        prov_a: OrderProvision,
        prov_b: OrderProvision,
        order_a: CourtOrder,
        order_b: CourtOrder,
    ) -> Optional[ConflictRecord]:
        """Check if two provisions are potentially conflicting."""
        desc_a = prov_a.description.lower()
        desc_b = prov_b.description.lower()

        for category, keywords in self._CONFLICT_KEYWORDS.items():
            kw_in_a = any(kw in desc_a for kw in keywords)
            kw_in_b = any(kw in desc_b for kw in keywords)

            if kw_in_a and kw_in_b:
                if prov_a.responsible_party and prov_b.responsible_party:
                    if prov_a.responsible_party != prov_b.responsible_party:
                        continue

                return ConflictRecord(
                    order_a_id=order_a.order_id,
                    order_b_id=order_b.order_id,
                    provision_a=prov_a.description,
                    provision_b=prov_b.description,
                    conflict_type=category,
                    description=(
                        f"Both orders address '{category}' — provisions may "
                        f"impose contradictory requirements."
                    ),
                    recommendation=(
                        f"Review and reconcile {category} provisions. The "
                        f"later-entered order (by date_entered) generally "
                        f"controls unless explicitly stated otherwise."
                    ),
                )
        return None

    # ------------------------------------------------------------------
    def detect_superseded_orders(
        self,
        orders: List[CourtOrder],
    ) -> List[Dict[str, Any]]:
        """Find orders that appear superseded but are still marked active.

        Two heuristics:
        1. Same case_number + same order_type but different dates → older
           should be superseded.
        2. A FINAL order supersedes a TEMPORARY of the same type/case.
        """
        issues: List[Dict[str, Any]] = []
        active = [o for o in orders if o.status == OrderStatus.ACTIVE]

        groups: Dict[Tuple[str, str], List[CourtOrder]] = {}
        for o in active:
            key = (o.case_number, o.order_type.value)
            groups.setdefault(key, []).append(o)

        for key, group in groups.items():
            if len(group) > 1:
                sorted_group = sorted(
                    group, key=lambda x: x.date_entered, reverse=True,
                )
                newest = sorted_group[0]
                for older in sorted_group[1:]:
                    issues.append({
                        "issue": "POSSIBLE_SUPERSESSION",
                        "newer_order": newest.order_id,
                        "older_order": older.order_id,
                        "case_number": key[0],
                        "order_type": key[1],
                        "recommendation": (
                            f"Order {older.order_id} (entered {older.date_entered}) "
                            f"may be superseded by {newest.order_id} "
                            f"(entered {newest.date_entered}). Mark older as "
                            f"SUPERSEDED if confirmed."
                        ),
                    })

        for o in active:
            if o.order_type == OrderType.TEMPORARY:
                for o2 in active:
                    if (o2.order_type == OrderType.FINAL
                            and o2.case_number == o.case_number
                            and o2.date_entered >= o.date_entered):
                        issues.append({
                            "issue": "TEMP_NOT_SUPERSEDED",
                            "temp_order": o.order_id,
                            "final_order": o2.order_id,
                            "recommendation": (
                                f"Temporary order {o.order_id} should be "
                                f"superseded by final order {o2.order_id}."
                            ),
                        })

        return issues

    # ------------------------------------------------------------------
    def detect_ex_parte_orders(
        self,
        orders: List[CourtOrder],
    ) -> List[Dict[str, Any]]:
        """Flag ex parte orders for potential challenge.

        Ex parte orders are issued without notice to the opposing party.
        Under MCR 3.207(B) and due-process principles, these are
        challengeable if entered without proper basis.
        """
        results: List[Dict[str, Any]] = []
        for o in orders:
            if o.order_type == OrderType.EX_PARTE:
                challenge_basis: List[str] = []
                challenge_basis.append(
                    "MCR 3.207(B): Ex parte orders in domestic relations "
                    "require showing of irreparable harm."
                )
                challenge_basis.append(
                    "Due Process (14th Amendment): Notice and opportunity "
                    "to be heard before deprivation of rights."
                )
                if o.judge and "mcneill" in o.judge.lower():
                    challenge_basis.append(
                        "Pattern concern: Judge McNeill — document for "
                        "Lane E (Misconduct/JTC) analysis."
                    )

                results.append({
                    "order_id": o.order_id,
                    "case_number": o.case_number,
                    "date_entered": o.date_entered,
                    "judge": o.judge,
                    "is_active": o.is_active(),
                    "challenge_basis": challenge_basis,
                    "recommendation": (
                        "File motion to vacate under MCR 2.612(C)(1)(c) "
                        "(fraud/misrepresentation) or MCR 2.612(C)(1)(f) "
                        "(any other reason justifying relief)."
                    ),
                })
        return results

    # ------------------------------------------------------------------
    def generate_conflict_matrix(
        self,
        orders: List[CourtOrder],
    ) -> str:
        """Generate a text-format conflict matrix."""
        conflicts = self.detect_conflicts(orders)
        lines: List[str] = []
        lines.append("ORDER CONFLICT MATRIX")
        lines.append("=" * 72)
        lines.append(f"Orders analysed: {len(orders)}")
        lines.append(f"Conflicts found: {len(conflicts)}")
        lines.append("")

        if not conflicts:
            lines.append("No conflicts detected among active orders.")
        else:
            for i, c in enumerate(conflicts, 1):
                lines.append(f"Conflict #{i}:")
                lines.append(f"  Type:        {c.conflict_type}")
                lines.append(f"  Order A:     {c.order_a_id[:12]}…")
                lines.append(f"  Provision A: {c.provision_a[:60]}")
                lines.append(f"  Order B:     {c.order_b_id[:12]}…")
                lines.append(f"  Provision B: {c.provision_b[:60]}")
                lines.append(f"  Issue:       {c.description}")
                lines.append(f"  Action:      {c.recommendation}")
                lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    def get_stats(self) -> dict:
        return {"module": "OrderConflictDetector", "version": "1.0.0"}


# ═══════════════════════════════════════════════════════════════════════════
# ContemptEngine
# ═══════════════════════════════════════════════════════════════════════════

class ContemptEngine:
    """Prepare and track contempt motions for order violations.

    Covers MCR 3.606 (contempt proceedings), MCL 600.1701 (contempt
    power), and purge-condition calculation.
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
    def evaluate_contempt_basis(
        self,
        order_id: str,
        violations: List[ViolationRecord],
    ) -> Dict[str, Any]:
        """Evaluate whether contempt proceedings are supportable.

        Contempt requires: (1) a clear and unambiguous order,
        (2) knowledge of the order, (3) wilful non-compliance.
        """
        if not violations:
            return {
                "supportable": False,
                "reason": "No violations to support contempt finding.",
            }

        severe = [v for v in violations
                  if v.severity in (ViolationSeverity.SEVERE,
                                    ViolationSeverity.WILLFUL)]
        moderate = [v for v in violations
                    if v.severity == ViolationSeverity.MODERATE]

        supportable = len(severe) > 0 or len(moderate) >= 2

        elements: List[Dict[str, Any]] = []
        elements.append({
            "element": "Clear and unambiguous order",
            "analysis": "Order provisions must be specific and definite.",
            "met": True,
        })
        elements.append({
            "element": "Knowledge of order",
            "analysis": (
                "Party must have been served with or have actual knowledge "
                "of the order."
            ),
            "met": True,
        })
        elements.append({
            "element": "Wilful non-compliance",
            "analysis": (
                f"{len(severe)} severe/willful violation(s), "
                f"{len(moderate)} moderate violation(s)."
            ),
            "met": supportable,
        })

        return {
            "supportable": supportable,
            "violation_count": len(violations),
            "severe_count": len(severe),
            "moderate_count": len(moderate),
            "elements": elements,
            "authority": ["MCR 3.606", "MCL 600.1701"],
            "recommendation": (
                "Proceed with contempt motion." if supportable
                else "Contempt may not be supportable. Consider motion "
                     "to compel under MCR 2.313 instead."
            ),
        }

    # ------------------------------------------------------------------
    def prepare_contempt_motion(
        self,
        order_id: str,
        violations: List[ViolationRecord],
    ) -> Dict[str, Any]:
        """Draft a contempt motion under MCR 3.606."""
        db = self._db()
        order_row = db.execute(
            "SELECT * FROM court_orders WHERE order_id = ?",
            (order_id,),
        ).fetchone()
        if not order_row:
            return {"error": f"Order {order_id} not found."}

        od = dict(order_row)
        case_number = od.get("case_number", "")

        lines: List[str] = []
        lines.append("STATE OF MICHIGAN")
        lines.append("IN THE CIRCUIT COURT FOR MUSKEGON COUNTY")
        lines.append("")
        lines.append(f"Case No.: {case_number}")
        lines.append(f"PIGORS v. WATSON, et al.")
        lines.append("")
        lines.append("MOTION FOR CONTEMPT OF COURT")
        lines.append("(MCR 3.606)")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"NOW COMES Plaintiff, {PLAINTIFF}, appearing pro se,")
        lines.append("and respectfully moves this Court to find the")
        lines.append("respondent in contempt for failure to comply with")
        lines.append(f"the Court's Order entered {od.get('date_entered', '')}.")
        lines.append("")
        lines.append("STATEMENT OF FACTS:")
        lines.append("")
        lines.append(f"1. This Court entered an Order on {od.get('date_entered', '')}.")
        lines.append(f"2. The Order is of type: {od.get('order_type', '')}.")
        lines.append(f"3. The respondent has knowledge of the Order.")
        lines.append(f"4. The following violations have been documented:")
        lines.append("")

        for i, v in enumerate(violations, 1):
            lines.append(f"   Violation {i}:")
            lines.append(f"   Provision: {v.provision_description}")
            lines.append(f"   Severity:  {v.severity.value}")
            lines.append(f"   Party:     {v.responsible_party}")
            if v.evidence:
                lines.append(f"   Evidence:")
                for ev in v.evidence:
                    lines.append(f"     • {ev}")
            lines.append("")

        lines.append("LEGAL BASIS:")
        lines.append(
            "MCR 3.606(A): The court may hold a person in contempt for "
            "disobedience of a lawful court order."
        )
        lines.append(
            "MCL 600.1701(a): Courts have inherent power to punish "
            "contempt of their authority."
        )
        lines.append("")
        lines.append("RELIEF REQUESTED:")
        lines.append(
            f"1. A finding of contempt against the violating party."
        )
        lines.append("2. Appropriate sanctions.")
        lines.append("3. Purge conditions as set forth below.")
        lines.append("4. Costs and fees incurred in this motion.")
        lines.append("")
        lines.append(f"Respectfully submitted,")
        lines.append(f"{PLAINTIFF}")
        lines.append(f"{PLAINTIFF_ROLE}")
        lines.append(f"Date: {_today_iso()}")

        motion_text = "\n".join(lines)

        action_id = str(uuid.uuid4())
        db.execute(
            "INSERT INTO contempt_actions "
            "(action_id, order_id, action_type, motion_text, status) "
            "VALUES (?, ?, ?, ?, ?)",
            (action_id, order_id, "CONTEMPT", motion_text, "PENDING"),
        )
        db.commit()
        self._actions_count += 1

        return {
            "action_id": action_id,
            "order_id": order_id,
            "motion_text": motion_text,
            "violation_count": len(violations),
        }

    # ------------------------------------------------------------------
    def calculate_purge_conditions(
        self,
        order_id: str,
    ) -> List[Dict[str, Any]]:
        """Determine conditions under which contempt can be purged.

        A contemnor may purge by demonstrating compliance.
        """
        db = self._db()
        rows = db.execute(
            "SELECT * FROM order_provisions WHERE order_id = ? "
            "AND compliance_status IN (?, ?)",
            (order_id, ComplianceStatus.NONCOMPLIANT.value,
             ComplianceStatus.PARTIAL.value),
        ).fetchall()

        conditions: List[Dict[str, Any]] = []
        for row in rows:
            prov = OrderProvision.from_row(row)
            cond: Dict[str, Any] = {
                "provision_id": prov.provision_id,
                "provision": prov.description,
                "purge_action": f"Comply fully with: {prov.description}",
                "deadline_suggested": (
                    date.today() + timedelta(days=14)
                ).isoformat(),
            }

            if prov.deadline:
                try:
                    dl = date.fromisoformat(prov.deadline)
                    days_past = (date.today() - dl).days
                    if days_past > 0:
                        cond["days_overdue"] = days_past
                        cond["retroactive_compliance_possible"] = days_past < 30
                except (ValueError, TypeError):
                    pass

            conditions.append(cond)

        return conditions

    # ------------------------------------------------------------------
    def prepare_show_cause(
        self,
        order_id: str,
    ) -> Dict[str, Any]:
        """Draft a request for Order to Show Cause."""
        db = self._db()
        order_row = db.execute(
            "SELECT * FROM court_orders WHERE order_id = ?",
            (order_id,),
        ).fetchone()
        if not order_row:
            return {"error": f"Order {order_id} not found."}

        od = dict(order_row)
        lines: List[str] = []
        lines.append("STATE OF MICHIGAN")
        lines.append("IN THE CIRCUIT COURT FOR MUSKEGON COUNTY")
        lines.append("")
        lines.append(f"Case No.: {od.get('case_number', '')}")
        lines.append(f"PIGORS v. WATSON, et al.")
        lines.append("")
        lines.append("REQUEST FOR ORDER TO SHOW CAUSE")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"Plaintiff, {PLAINTIFF}, requests that this Court issue")
        lines.append("an Order to Show Cause why the respondent should not")
        lines.append("be held in contempt for failure to comply with the")
        lines.append(f"Court's Order entered {od.get('date_entered', '')}.")
        lines.append("")
        lines.append(f"Order Type: {od.get('order_type', '')}")
        lines.append(f"Date Entered: {od.get('date_entered', '')}")
        lines.append("")
        lines.append(f"Respectfully submitted,")
        lines.append(f"{PLAINTIFF}")
        lines.append(f"{PLAINTIFF_ROLE}")
        lines.append(f"Date: {_today_iso()}")

        text = "\n".join(lines)
        action_id = str(uuid.uuid4())

        db.execute(
            "INSERT INTO contempt_actions "
            "(action_id, order_id, action_type, motion_text, status) "
            "VALUES (?, ?, ?, ?, ?)",
            (action_id, order_id, "SHOW_CAUSE", text, "PENDING"),
        )
        db.commit()
        self._actions_count += 1

        return {
            "action_id": action_id,
            "order_id": order_id,
            "text": text,
        }

    # ------------------------------------------------------------------
    def track_contempt_proceedings(
        self,
        order_id: str,
    ) -> List[Dict[str, Any]]:
        """Return the history of contempt actions for an order."""
        db = self._db()
        rows = db.execute(
            "SELECT * FROM contempt_actions WHERE order_id = ? "
            "ORDER BY created_at DESC",
            (order_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    def get_stats(self) -> dict:
        return {"contempt_actions_created": self._actions_count}


# ═══════════════════════════════════════════════════════════════════════════
# CourtOrderTracker  (main orchestrator)
# ═══════════════════════════════════════════════════════════════════════════

class CourtOrderTracker:
    """Top-level orchestrator for court order management.

    Provides cataloging, retrieval, compliance monitoring, conflict
    detection, and contempt management across all case lanes.
    """

    VERSION = "1.0.0"

    def __init__(
        self,
        db_path: Optional[pathlib.Path] = None,
    ) -> None:
        self._db_path = db_path or _DB_PATH
        self._conn: Optional[sqlite3.Connection] = None
        self.compliance_monitor: Optional[ComplianceMonitor] = None
        self.conflict_detector = OrderConflictDetector()
        self.contempt_engine: Optional[ContemptEngine] = None

    # ------------------------------------------------------------------
    def _init_db(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = _get_conn(self._db_path)
            _ensure_schema(self._conn)
            self.compliance_monitor = ComplianceMonitor(self._conn)
            self.contempt_engine = ContemptEngine(self._conn)
        return self._conn

    # ------------------------------------------------------------------
    def close(self) -> None:
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    # ------------------------------------------------------------------
    def catalog_order(
        self,
        order_data: Dict[str, Any],
    ) -> CourtOrder:
        """Catalog a new court order and persist to DB.

        Parameters
        ----------
        order_data : dict
            Must include at minimum: case_number, order_type,
            date_entered.  Optional: provisions (list of dicts),
            court, judge, date_effective, date_expires, notes, etc.
        """
        db = self._init_db()

        order = CourtOrder(
            case_number=order_data.get("case_number", ""),
            case_lane=order_data.get("case_lane", ""),
            court=order_data.get("court", "14th Circuit Court, Muskegon County"),
            judge=order_data.get("judge", JUDGE),
            order_type=OrderType(
                order_data.get("order_type", "TEMPORARY"),
            ),
            date_entered=order_data.get("date_entered", _today_iso()),
            date_effective=order_data.get(
                "date_effective",
                order_data.get("date_entered", _today_iso()),
            ),
            date_expires=order_data.get("date_expires"),
            status=OrderStatus(order_data.get("status", "ACTIVE")),
            superseded_by=order_data.get("superseded_by"),
            related_orders=order_data.get("related_orders", []),
            filing_ref=order_data.get("filing_ref", ""),
            notes=order_data.get("notes", ""),
        )

        db.execute(
            "INSERT OR REPLACE INTO court_orders "
            "(order_id, case_number, case_lane, court, judge, order_type, "
            "date_entered, date_effective, date_expires, status, "
            "superseded_by, related_orders, filing_ref, notes, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                order.order_id, order.case_number, order.case_lane,
                order.court, order.judge, order.order_type.value,
                order.date_entered, order.date_effective, order.date_expires,
                order.status.value, order.superseded_by,
                json.dumps(order.related_orders), order.filing_ref,
                order.notes, _now_iso(),
            ),
        )

        prov_data_list = order_data.get("provisions", [])
        for pd in prov_data_list:
            prov = OrderProvision(
                order_id=order.order_id,
                description=pd.get("description", ""),
                compliance_status=ComplianceStatus(
                    pd.get("compliance_status", "UNKNOWN"),
                ),
                responsible_party=pd.get("responsible_party", ""),
                deadline=pd.get("deadline"),
            )
            order.provisions.append(prov)
            db.execute(
                "INSERT OR REPLACE INTO order_provisions "
                "(provision_id, order_id, description, compliance_status, "
                "responsible_party, deadline, evidence_of_compliance, "
                "evidence_of_violation, last_checked, updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    prov.provision_id, prov.order_id, prov.description,
                    prov.compliance_status.value, prov.responsible_party,
                    prov.deadline, "[]", "[]", None, _now_iso(),
                ),
            )

        db.commit()
        logger.info(
            "Cataloged order %s (%s) with %d provisions",
            order.order_id, order.order_type.value, len(order.provisions),
        )
        return order

    # ------------------------------------------------------------------
    def _load_order_with_provisions(
        self, row: sqlite3.Row,
    ) -> CourtOrder:
        """Load an order and attach its provisions."""
        db = self._init_db()
        prov_rows = db.execute(
            "SELECT * FROM order_provisions WHERE order_id = ?",
            (dict(row)["order_id"],),
        ).fetchall()
        provisions = [OrderProvision.from_row(r) for r in prov_rows]
        return CourtOrder.from_row(row, provisions)

    # ------------------------------------------------------------------
    def get_all_orders(
        self,
        lane: Optional[str] = None,
    ) -> List[CourtOrder]:
        """Return all cataloged orders, optionally filtered by lane."""
        db = self._init_db()
        if lane:
            rows = db.execute(
                "SELECT * FROM court_orders WHERE case_lane = ? "
                "ORDER BY date_entered DESC",
                (lane,),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM court_orders ORDER BY date_entered DESC",
            ).fetchall()
        return [self._load_order_with_provisions(r) for r in rows]

    # ------------------------------------------------------------------
    def get_active_orders(
        self,
        lane: Optional[str] = None,
    ) -> List[CourtOrder]:
        """Return only currently active orders."""
        all_orders = self.get_all_orders(lane)
        return [o for o in all_orders if o.is_active()]

    # ------------------------------------------------------------------
    def get_order(self, order_id: str) -> Optional[CourtOrder]:
        """Retrieve a single order by ID."""
        db = self._init_db()
        row = db.execute(
            "SELECT * FROM court_orders WHERE order_id = ?",
            (order_id,),
        ).fetchone()
        if not row:
            return None
        return self._load_order_with_provisions(row)

    # ------------------------------------------------------------------
    def update_provision_compliance(
        self,
        provision_id: str,
        status: ComplianceStatus,
        *,
        evidence: Optional[List[str]] = None,
    ) -> None:
        """Update the compliance status of a single provision."""
        db = self._init_db()
        if evidence:
            if status in (ComplianceStatus.COMPLIANT,):
                db.execute(
                    "UPDATE order_provisions SET compliance_status = ?, "
                    "evidence_of_compliance = ?, last_checked = ?, updated_at = ? "
                    "WHERE provision_id = ?",
                    (status.value, json.dumps(evidence), _now_iso(),
                     _now_iso(), provision_id),
                )
            else:
                db.execute(
                    "UPDATE order_provisions SET compliance_status = ?, "
                    "evidence_of_violation = ?, last_checked = ?, updated_at = ? "
                    "WHERE provision_id = ?",
                    (status.value, json.dumps(evidence), _now_iso(),
                     _now_iso(), provision_id),
                )
        else:
            db.execute(
                "UPDATE order_provisions SET compliance_status = ?, "
                "last_checked = ?, updated_at = ? WHERE provision_id = ?",
                (status.value, _now_iso(), _now_iso(), provision_id),
            )
        db.commit()

    # ------------------------------------------------------------------
    def monitor_compliance(self) -> Dict[str, Any]:
        """Scan all active orders for violations.

        Returns a summary with total checks, violations found, and
        per-order breakdowns.
        """
        self._init_db()
        assert self.compliance_monitor is not None

        active = self.get_active_orders()
        total_checks = 0
        total_violations = 0
        order_summaries: List[Dict[str, Any]] = []

        for order in active:
            results = self.compliance_monitor.check_compliance(order.order_id)
            violations = [r for r in results if r.get("is_violated")]
            total_checks += len(results)
            total_violations += len(violations)
            order_summaries.append({
                "order_id": order.order_id,
                "case_number": order.case_number,
                "case_lane": order.case_lane,
                "order_type": order.order_type.value,
                "provisions_checked": len(results),
                "violations_found": len(violations),
            })

        return {
            "active_orders_scanned": len(active),
            "total_provisions_checked": total_checks,
            "total_violations_found": total_violations,
            "orders": order_summaries,
            "scan_date": _now_iso(),
        }

    # ------------------------------------------------------------------
    def detect_all_conflicts(self) -> Dict[str, Any]:
        """Run cross-order conflict detection on all active orders.

        Returns conflict matrix, supersession issues, and ex parte flags.
        """
        active = self.get_active_orders()

        conflicts = self.conflict_detector.detect_conflicts(active)
        supersession = self.conflict_detector.detect_superseded_orders(active)
        ex_parte = self.conflict_detector.detect_ex_parte_orders(active)

        return {
            "active_orders": len(active),
            "conflicts": [c.to_dict() for c in conflicts],
            "supersession_issues": supersession,
            "ex_parte_flags": ex_parte,
            "matrix_text": self.conflict_detector.generate_conflict_matrix(active),
        }

    # ------------------------------------------------------------------
    def generate_order_report(self) -> str:
        """Comprehensive order status report across all lanes."""
        orders = self.get_all_orders()
        active = [o for o in orders if o.is_active()]
        expired = [o for o in orders if o.is_expired()]

        by_lane: Dict[str, int] = {}
        by_type: Dict[str, int] = {}
        for o in orders:
            by_lane[o.case_lane] = by_lane.get(o.case_lane, 0) + 1
            by_type[o.order_type.value] = by_type.get(o.order_type.value, 0) + 1

        lines: List[str] = []
        lines.append("COURT ORDER STATUS REPORT — Pigors v. Watson")
        lines.append(f"Generated: {_now_iso()}")
        lines.append("=" * 72)
        lines.append(f"Total orders:   {len(orders)}")
        lines.append(f"Active orders:  {len(active)}")
        lines.append(f"Expired orders: {len(expired)}")
        lines.append("")

        lines.append("BY LANE:")
        for ln in sorted(by_lane.keys()):
            lane_info = CASE_LANES.get(ln, {})
            lines.append(
                f"  Lane {ln} ({lane_info.get('subject', '')}): "
                f"{by_lane[ln]}"
            )
        lines.append("")

        lines.append("BY TYPE:")
        for t, c in sorted(by_type.items()):
            lines.append(f"  {t}: {c}")
        lines.append("")

        lines.append("DETAIL:")
        lines.append("-" * 72)
        for o in orders:
            lines.append(f"Order:   {o.order_id}")
            lines.append(f"Type:    {o.order_type.value}")
            lines.append(f"Case:    {o.case_number} (Lane {o.case_lane})")
            lines.append(f"Judge:   {o.judge}")
            lines.append(f"Entered: {o.date_entered}")
            lines.append(f"Status:  {o.status.value}")
            lines.append(f"Active:  {o.is_active()}")
            prov_count = len(o.provisions)
            violated = sum(1 for p in o.provisions if p.is_violated())
            lines.append(f"Provisions: {prov_count} (violated: {violated})")
            days = o.days_since_entry()
            if days is not None:
                lines.append(f"Days since entry: {days}")
            lines.append("-" * 72)

        return "\n".join(lines)

    # ------------------------------------------------------------------
    def get_stats(self) -> dict:
        """Return engine-wide statistics."""
        db = self._init_db()
        row = db.execute(
            "SELECT "
            "  (SELECT COUNT(*) FROM court_orders) AS total_orders, "
            "  (SELECT COUNT(*) FROM court_orders WHERE status = 'ACTIVE') AS active_orders, "
            "  (SELECT COUNT(*) FROM court_orders WHERE status = 'EXPIRED') AS expired_orders, "
            "  (SELECT COUNT(*) FROM court_orders WHERE status = 'SUPERSEDED') AS superseded_orders, "
            "  (SELECT COUNT(*) FROM court_orders WHERE order_type = 'EX_PARTE') AS ex_parte_orders, "
            "  (SELECT COUNT(*) FROM order_provisions) AS total_provisions, "
            "  (SELECT COUNT(*) FROM order_provisions WHERE compliance_status = 'NONCOMPLIANT') AS noncompliant, "
            "  (SELECT COUNT(*) FROM order_provisions WHERE compliance_status = 'COMPLIANT') AS compliant, "
            "  (SELECT COUNT(*) FROM compliance_checks) AS total_checks, "
            "  (SELECT COUNT(*) FROM contempt_actions) AS contempt_actions"
        ).fetchone()
        d = dict(row)
        d["engine_version"] = self.VERSION
        if self.compliance_monitor:
            d["compliance_monitor"] = self.compliance_monitor.get_stats()
        d["conflict_detector"] = self.conflict_detector.get_stats()
        if self.contempt_engine:
            d["contempt_engine"] = self.contempt_engine.get_stats()
        return d


# ═══════════════════════════════════════════════════════════════════════════
# CLI / Demo
# ═══════════════════════════════════════════════════════════════════════════

def _cli_main() -> int:
    """Minimal CLI for court order tracking."""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="CourtOrderTracker — order management and compliance",
    )
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("stats", help="Print engine statistics")
    sub.add_parser("report", help="Print full order report")
    sub.add_parser("compliance", help="Run compliance scan")
    sub.add_parser("conflicts", help="Run conflict detection")
    sub.add_parser("demo", help="Run demo with sample data")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 0

    tracker = CourtOrderTracker()
    try:
        if args.command == "stats":
            stats = tracker.get_stats()
            print(json.dumps(stats, indent=2, default=str))

        elif args.command == "report":
            print(tracker.generate_order_report())

        elif args.command == "compliance":
            result = tracker.monitor_compliance()
            print(json.dumps(result, indent=2, default=str))

        elif args.command == "conflicts":
            result = tracker.detect_all_conflicts()
            print(result.get("matrix_text", ""))

        elif args.command == "demo":
            _run_demo(tracker)
    finally:
        tracker.close()

    return 0


def _run_demo(tracker: CourtOrderTracker) -> None:
    """Demonstrate court order tracking capabilities."""
    print("=" * 60)
    print("CourtOrderTracker Demo — Pigors v. Watson")
    print("=" * 60)

    # 1. Custody order (Lane A)
    order1 = tracker.catalog_order({
        "case_number": "2024-001507-DC",
        "case_lane": "A",
        "order_type": "TEMPORARY",
        "date_entered": "2024-06-15",
        "judge": JUDGE,
        "notes": "Temporary custody order pending final hearing.",
        "provisions": [
            {
                "description": "Father shall have parenting time every other weekend Friday 6pm to Sunday 6pm.",
                "responsible_party": DEFENDANT,
                "compliance_status": "NONCOMPLIANT",
            },
            {
                "description": "Mother shall not relocate child more than 25 miles from current residence.",
                "responsible_party": DEFENDANT,
                "compliance_status": "COMPLIANT",
            },
            {
                "description": "Both parties shall communicate regarding child's education and medical care.",
                "responsible_party": "BOTH",
                "compliance_status": "PARTIAL",
            },
        ],
    })
    print(f"\n[1] Cataloged TEMPORARY custody order: {order1.order_id[:12]}…")
    print(f"    Provisions: {len(order1.provisions)}")

    # 2. PPO order (Lane D)
    order2 = tracker.catalog_order({
        "case_number": "2023-5907-PP",
        "case_lane": "D",
        "order_type": "PPO",
        "date_entered": "2023-11-01",
        "judge": JUDGE,
        "notes": "Personal Protection Order — dispute regarding basis.",
        "provisions": [
            {
                "description": "Respondent shall not contact petitioner except through attorney.",
                "responsible_party": PLAINTIFF,
                "compliance_status": "COMPLIANT",
            },
            {
                "description": "Respondent shall not come within 500 feet of petitioner's residence.",
                "responsible_party": PLAINTIFF,
                "compliance_status": "COMPLIANT",
            },
        ],
    })
    print(f"\n[2] Cataloged PPO order: {order2.order_id[:12]}…")

    # 3. Ex parte order (Lane E)
    order3 = tracker.catalog_order({
        "case_number": "2024-001507-DC",
        "case_lane": "E",
        "order_type": "EX_PARTE",
        "date_entered": "2024-08-01",
        "judge": JUDGE,
        "notes": "Ex parte order modifying custody without notice to father.",
        "provisions": [
            {
                "description": "Temporary sole custody awarded to mother pending hearing.",
                "responsible_party": DEFENDANT,
                "compliance_status": "UNKNOWN",
            },
        ],
    })
    print(f"\n[3] Cataloged EX_PARTE order: {order3.order_id[:12]}…")

    # 4. Compliance monitoring
    print("\n[4] Running compliance scan…")
    compliance = tracker.monitor_compliance()
    print(f"    Orders scanned: {compliance['active_orders_scanned']}")
    print(f"    Provisions checked: {compliance['total_provisions_checked']}")
    print(f"    Violations found: {compliance['total_violations_found']}")

    # 5. Violation detection
    assert tracker.compliance_monitor is not None
    print("\n[5] Detecting violations for custody order…")
    violations = tracker.compliance_monitor.detect_violations(order1.order_id)
    for v in violations:
        print(f"    {v.severity.value}: {v.provision_description[:60]}…")

    # 6. Violation report
    print("\n[6] Violation Report:")
    report = tracker.compliance_monitor.generate_violation_report(order1.order_id)
    for line in report.split("\n")[:15]:
        print(f"    {line}")
    if report.count("\n") > 15:
        print("    …(truncated)")

    # 7. Conflict detection
    print("\n[7] Conflict Detection:")
    conflict_result = tracker.detect_all_conflicts()
    print(f"    Conflicts: {len(conflict_result['conflicts'])}")
    print(f"    Supersession issues: {len(conflict_result['supersession_issues'])}")
    print(f"    Ex parte flags: {len(conflict_result['ex_parte_flags'])}")
    for ep in conflict_result["ex_parte_flags"]:
        print(f"    EX PARTE: {ep['order_id'][:12]}… — {ep['judge']}")
        for basis in ep.get("challenge_basis", [])[:2]:
            print(f"      • {basis[:70]}…")

    # 8. Contempt evaluation
    assert tracker.contempt_engine is not None
    print("\n[8] Contempt Evaluation for custody order:")
    eval_result = tracker.contempt_engine.evaluate_contempt_basis(
        order1.order_id, violations,
    )
    print(f"    Supportable: {eval_result['supportable']}")
    print(f"    Recommendation: {eval_result['recommendation'][:80]}…")

    # 9. Purge conditions
    print("\n[9] Purge Conditions:")
    conditions = tracker.contempt_engine.calculate_purge_conditions(order1.order_id)
    for cond in conditions:
        print(f"    • {cond['purge_action'][:60]}…")
        print(f"      Deadline: {cond['deadline_suggested']}")

    # 10. Full order report
    print("\n[10] Full Order Report (first 20 lines):")
    full_report = tracker.generate_order_report()
    for line in full_report.split("\n")[:20]:
        print(f"    {line}")
    print("    …(truncated)")

    # 11. Stats
    print("\n[11] Engine Stats:")
    stats = tracker.get_stats()
    print(json.dumps(stats, indent=2, default=str))

    print("\nDemo complete.")


if __name__ == "__main__":
    sys.exit(_cli_main())
