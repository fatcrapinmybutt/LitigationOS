# -*- coding: utf-8 -*-
"""
Contempt Engine — LitigationOS Legal AI Subsystem
====================================================
Civil and criminal contempt prosecution per Michigan law.
Handles identification, documentation, motion drafting, purge
condition analysis, sanction calculation, and proceeding tracking
under MCL 600.1701-1775, MCR 3.606, and related authorities.

Case Context
------------
    Plaintiff:  Andrew James Pigors (Pro Se)
    Defendant:  Emily A. Watson
    Child:      L.D.W. (per MCR 8.119(H)) — Male
    Judge:      Hon. Jenny L. McNeill — 14th Circuit Court
    Cases:      2024-001507-DC, 2025-002760-CZ, 2023-5907-PP, COA 366810

Michigan Rules & Statutes
-------------------------
    MCL 600.1701   – Powers of courts (civil contempt)
    MCL 600.1711   – Contempt power enumeration
    MCL 600.1715   – Criminal contempt procedure
    MCL 600.1721   – Punishment for criminal contempt
    MCL 600.1745   – Civil contempt — coercive sanctions
    MCL 600.1775   – Appellate review of contempt
    MCR 3.606      – Contempt proceedings in domestic relations
    MCR 3.606(A)   – Motion for contempt
    MCR 3.606(B)   – Show cause order
    MCR 3.606(C)   – Hearing procedure

    In re Contempt of Dougherty, 429 Mich 81 (1987):
      Purge conditions must be achievable; contemnor must have
      present ability to comply.

    DeGeorge v Warwick, 404 Mich 89 (1978):
      Distinction between civil and criminal contempt depends on
      character and purpose of the sanction.

    In re Contempt of Henry, 282 Mich App 656 (2009):
      Criminal contempt requires proof beyond a reasonable doubt.

    Sword v Sword, 399 Mich 367 (1976):
      Court must find willful and contumacious disregard of court order.

Usage::

    from legal_ai.contempt_engine import ContemptEngine

    engine = ContemptEngine()
    violation = engine.identify_violations(
        order_violated="Custody Order 2024-001507-DC ¶ 12",
        violation_description="Denied scheduled parenting time on 2025-07-04",
        evidence_refs=["Exhibit A — text messages"],
    )
    motion = engine.file_contempt(violation.violation_id)

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
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger("legal_ai.contempt_engine")

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
# Michigan contempt timelines / constants
# ---------------------------------------------------------------------------
_SHOW_CAUSE_RESPONSE_DAYS = 14       # MCR 3.606(B) — typical show-cause return
_CRIMINAL_CONTEMPT_MAX_JAIL = 93     # MCL 600.1715 — 93 days maximum
_CIVIL_COERCIVE_REVIEW_DAYS = 180    # Review of civil coercive confinement
_PURGE_COMPLIANCE_WINDOW_DAYS = 14   # Default purge-condition compliance window
_MCR_3606_FILING_FEE = Decimal("20.00")  # SCAO fee schedule

# Standard of proof thresholds
_CLEAR_AND_CONVINCING = 0.75   # Civil contempt standard
_BEYOND_REASONABLE_DOUBT = 0.90  # Criminal contempt standard

# Michigan authority references
_AUTHORITY_REFS: Dict[str, str] = {
    "civil_contempt_power": "MCL 600.1701",
    "contempt_enumeration": "MCL 600.1711",
    "criminal_procedure": "MCL 600.1715",
    "criminal_punishment": "MCL 600.1721",
    "civil_coercive": "MCL 600.1745",
    "appellate_review": "MCL 600.1775",
    "domestic_contempt": "MCR 3.606",
    "motion_requirements": "MCR 3.606(A)",
    "show_cause_order": "MCR 3.606(B)",
    "hearing_procedure": "MCR 3.606(C)",
    "dougherty": "In re Contempt of Dougherty, 429 Mich 81 (1987)",
    "degeorge": "DeGeorge v Warwick, 404 Mich 89 (1978)",
    "henry": "In re Contempt of Henry, 282 Mich App 656 (2009)",
    "sword": "Sword v Sword, 399 Mich 367 (1976)",
}

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class ContemptType(str, Enum):
    """Types of contempt under Michigan law.

    Michigan distinguishes civil from criminal contempt based on the
    purpose of the sanction (DeGeorge v Warwick), and direct from
    constructive based on whether the contempt occurred in the
    court's presence.
    """

    CIVIL_DIRECT = "civil_direct"
    CIVIL_CONSTRUCTIVE = "civil_constructive"
    CRIMINAL_DIRECT = "criminal_direct"
    CRIMINAL_CONSTRUCTIVE = "criminal_constructive"

    @property
    def is_civil(self) -> bool:
        return self in (ContemptType.CIVIL_DIRECT, ContemptType.CIVIL_CONSTRUCTIVE)

    @property
    def is_criminal(self) -> bool:
        return self in (ContemptType.CRIMINAL_DIRECT, ContemptType.CRIMINAL_CONSTRUCTIVE)

    @property
    def is_direct(self) -> bool:
        return self in (ContemptType.CIVIL_DIRECT, ContemptType.CRIMINAL_DIRECT)

    @property
    def standard_of_proof(self) -> str:
        if self.is_civil:
            return "clear and convincing evidence"
        return "beyond a reasonable doubt"

    @property
    def mcl_reference(self) -> str:
        _refs = {
            "civil_direct": "MCL 600.1701; MCL 600.1745",
            "civil_constructive": "MCL 600.1701; MCL 600.1745",
            "criminal_direct": "MCL 600.1715; MCL 600.1721",
            "criminal_constructive": "MCL 600.1715; MCL 600.1721",
        }
        return _refs.get(self.value, "MCL 600.1701")


class ContemptStatus(str, Enum):
    """Status progression of a contempt proceeding."""

    IDENTIFIED = "identified"
    DOCUMENTED = "documented"
    MOTION_FILED = "motion_filed"
    SHOW_CAUSE_ISSUED = "show_cause_issued"
    HEARING_SCHEDULED = "hearing_scheduled"
    FOUND_IN_CONTEMPT = "found_in_contempt"
    PURGED = "purged"
    DISMISSED = "dismissed"

    @property
    def is_terminal(self) -> bool:
        return self in (
            ContemptStatus.FOUND_IN_CONTEMPT,
            ContemptStatus.PURGED,
            ContemptStatus.DISMISSED,
        )

    @property
    def next_statuses(self) -> List[str]:
        _transitions: Dict[str, List[str]] = {
            "identified": ["documented", "dismissed"],
            "documented": ["motion_filed", "dismissed"],
            "motion_filed": ["show_cause_issued", "dismissed"],
            "show_cause_issued": ["hearing_scheduled", "dismissed"],
            "hearing_scheduled": ["found_in_contempt", "dismissed"],
            "found_in_contempt": ["purged"],
            "purged": [],
            "dismissed": [],
        }
        return _transitions.get(self.value, [])


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class ContemptViolation:
    """A single violation that may form the basis of a contempt proceeding."""

    violation_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    order_violated: str = ""
    violation_date: str = ""
    violation_description: str = ""
    evidence_refs: List[str] = field(default_factory=list)
    contempt_type: ContemptType = ContemptType.CIVIL_CONSTRUCTIVE
    status: ContemptStatus = ContemptStatus.IDENTIFIED
    willfulness_score: int = 0  # 0-100
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "violation_id": self.violation_id,
            "order_violated": self.order_violated,
            "violation_date": self.violation_date,
            "violation_description": self.violation_description,
            "evidence_refs": self.evidence_refs,
            "contempt_type": self.contempt_type.value,
            "status": self.status.value,
            "willfulness_score": self.willfulness_score,
            "created_at": self.created_at,
        }


@dataclass
class ShowCauseOrder:
    """A show-cause order issued by the court."""

    order_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    violation_id: str = ""
    case_number: str = ""
    respondent: str = ""
    return_date: str = ""
    violations_cited: List[str] = field(default_factory=list)
    purge_conditions: List[str] = field(default_factory=list)
    issued_date: str = ""
    court: str = _COURT
    judge: str = _JUDGE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "violation_id": self.violation_id,
            "case_number": self.case_number,
            "respondent": self.respondent,
            "return_date": self.return_date,
            "violations_cited": self.violations_cited,
            "purge_conditions": self.purge_conditions,
            "issued_date": self.issued_date,
            "court": self.court,
            "judge": self.judge,
        }


@dataclass
class ContemptSanction:
    """Sanctions imposed for contempt."""

    sanction_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    violation_id: str = ""
    sanction_type: str = ""  # compensatory, coercive, punitive
    amount: Decimal = Decimal("0.00")
    jail_days: int = 0
    attorney_fees: Decimal = Decimal("0.00")
    conditions: List[str] = field(default_factory=list)
    legal_basis: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sanction_id": self.sanction_id,
            "violation_id": self.violation_id,
            "sanction_type": self.sanction_type,
            "amount": str(self.amount),
            "jail_days": self.jail_days,
            "attorney_fees": str(self.attorney_fees),
            "conditions": self.conditions,
            "legal_basis": self.legal_basis,
        }


@dataclass
class PurgeCondition:
    """A condition that, if satisfied, purges the contempt."""

    condition_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    violation_id: str = ""
    description: str = ""
    deadline: str = ""
    is_achievable: bool = True
    is_satisfied: bool = False
    satisfaction_date: str = ""
    evidence_of_compliance: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "condition_id": self.condition_id,
            "violation_id": self.violation_id,
            "description": self.description,
            "deadline": self.deadline,
            "is_achievable": self.is_achievable,
            "is_satisfied": self.is_satisfied,
            "satisfaction_date": self.satisfaction_date,
            "evidence_of_compliance": self.evidence_of_compliance,
        }


# ---------------------------------------------------------------------------
# ShowCauseGenerator
# ---------------------------------------------------------------------------


class ShowCauseGenerator:
    """Generate show-cause motions and orders for contempt proceedings.

    MCR 3.606(A) requires that a motion for contempt in domestic-
    relations cases be supported by an affidavit stating the facts
    on which the claim of contempt is based.

    MCL 600.1701 grants courts power to punish civil contempt.
    MCL 600.1715 governs criminal contempt procedure.
    """

    def __init__(self) -> None:
        self._motions: List[Dict[str, Any]] = []
        self._orders: List[ShowCauseOrder] = []

    def draft_motion(
        self,
        violation: ContemptViolation,
        case_number: str = "",
        additional_facts: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Draft a motion for contempt / show cause per MCR 3.606(A).

        Returns a structured motion document ready for formatting.
        """
        case_num = case_number or LANE_CASES["A"]
        facts = additional_facts or []

        motion: Dict[str, Any] = {
            "document_type": "Motion and Order to Show Cause",
            "case_number": case_num,
            "court": _COURT,
            "judge": _JUDGE,
            "movant": _PLAINTIFF,
            "respondent": _DEFENDANT,
            "contempt_type": violation.contempt_type.value,
            "legal_basis": (
                f"{violation.contempt_type.mcl_reference}; MCR 3.606(A)"
                if violation.contempt_type.is_civil
                else f"{violation.contempt_type.mcl_reference}; MCR 3.606"
            ),
            "sections": [
                {
                    "heading": "I. INTRODUCTION",
                    "content": (
                        f"Plaintiff {_PLAINTIFF}, appearing pro se, respectfully "
                        "moves this Court for an Order to Show Cause why Defendant "
                        f"{_DEFENDANT} should not be held in contempt of court for "
                        f"violating this Court's order: {violation.order_violated}."
                    ),
                },
                {
                    "heading": "II. FACTUAL BASIS",
                    "content": (
                        f"On or about {violation.violation_date}, Defendant "
                        f"{violation.violation_description}. "
                        f"This conduct directly violates the Court's order "
                        f"({violation.order_violated})."
                    ),
                    "supporting_facts": facts,
                },
                {
                    "heading": "III. EVIDENCE",
                    "content": (
                        "The following evidence supports the claimed violation:"
                    ),
                    "exhibits": violation.evidence_refs,
                },
                {
                    "heading": "IV. LEGAL STANDARD",
                    "content": self._get_legal_standard(violation.contempt_type),
                },
                {
                    "heading": "V. ARGUMENT",
                    "content": (
                        "Defendant's conduct constitutes willful and contumacious "
                        "disregard of this Court's order. Sword v Sword, 399 Mich "
                        "367, 375 (1976). The Court should issue an order requiring "
                        "Defendant to show cause why she should not be held in "
                        "contempt."
                    ),
                },
                {
                    "heading": "VI. RELIEF REQUESTED",
                    "content": (
                        "Plaintiff respectfully requests that this Court: "
                        "(1) issue an Order to Show Cause directing Defendant to "
                        "appear and show cause why she should not be held in "
                        "contempt; (2) find Defendant in contempt; and "
                        "(3) impose appropriate sanctions including compensatory "
                        "damages, attorney fees, and such other relief as the "
                        "Court deems just."
                    ),
                },
            ],
            "attachments": [
                "Affidavit in Support of Motion for Contempt",
                "Copy of Court Order Violated",
                "Proposed Order to Show Cause",
            ] + [f"Exhibit: {ref}" for ref in violation.evidence_refs],
            "sha256": hashlib.sha256(
                json.dumps(violation.to_dict(), sort_keys=True).encode()
            ).hexdigest()[:16],
        }

        self._motions.append(motion)
        logger.info(
            "Drafted contempt motion for violation %s (type: %s)",
            violation.violation_id, violation.contempt_type.value,
        )
        return motion

    def _get_legal_standard(self, contempt_type: ContemptType) -> str:
        """Return the legal standard section based on contempt type."""
        if contempt_type.is_civil:
            return (
                "Civil contempt is remedial in nature and designed to coerce "
                "compliance with the court's order or to compensate the injured "
                "party. DeGeorge v Warwick, 404 Mich 89, 100 (1978). The movant "
                "must prove by clear and convincing evidence that (1) a court order "
                "existed, (2) the respondent knew of the order, (3) the respondent "
                "violated the order, and (4) the violation was willful. "
                "Sword v Sword, 399 Mich 367, 375 (1976)."
            )
        return (
            "Criminal contempt is punitive in nature and is designed to vindicate "
            "the authority of the court. In re Contempt of Henry, 282 Mich App "
            "656, 666 (2009). The prosecution must prove beyond a reasonable doubt "
            "that the respondent willfully and contumaciously violated a clear and "
            "unambiguous court order. MCL 600.1715; In re Contempt of Dougherty, "
            "429 Mich 81, 97 (1987)."
        )

    def cite_specific_violations(
        self,
        violations: List[ContemptViolation],
    ) -> List[Dict[str, Any]]:
        """Generate violation-by-violation citation list for a motion."""
        citations = []
        for i, v in enumerate(violations, 1):
            citations.append({
                "number": i,
                "date": v.violation_date,
                "order_violated": v.order_violated,
                "description": v.violation_description,
                "evidence": v.evidence_refs,
                "contempt_type": v.contempt_type.value,
                "authority": v.contempt_type.mcl_reference,
            })
        return citations

    def calculate_purge_conditions(
        self,
        violation: ContemptViolation,
        requested_relief: Optional[List[str]] = None,
    ) -> List[PurgeCondition]:
        """Propose purge conditions per In re Contempt of Dougherty.

        Purge conditions must be achievable — the contemnor must have
        the present ability to comply.
        """
        relief = requested_relief or []
        conditions: List[PurgeCondition] = []

        # Default purge conditions based on violation type
        default_conditions = [
            f"Comply with the Court's order: {violation.order_violated}",
            "Pay compensatory damages for harm caused by the violation",
            "Pay movant's reasonable costs in bringing the contempt motion",
        ]

        for desc in default_conditions + relief:
            try:
                deadline_date = date.fromisoformat(violation.violation_date)
                deadline = (
                    deadline_date + timedelta(days=_PURGE_COMPLIANCE_WINDOW_DAYS)
                ).isoformat()
            except ValueError:
                deadline = ""

            conditions.append(PurgeCondition(
                violation_id=violation.violation_id,
                description=desc,
                deadline=deadline,
                is_achievable=True,
            ))

        logger.info(
            "Generated %d purge conditions for violation %s",
            len(conditions), violation.violation_id,
        )
        return conditions

    def draft_proposed_order(
        self,
        violation: ContemptViolation,
        case_number: str = "",
        return_date: str = "",
    ) -> ShowCauseOrder:
        """Draft a proposed Order to Show Cause for judge's signature."""
        case_num = case_number or LANE_CASES["A"]

        if not return_date:
            try:
                today = date.today()
                return_date = (today + timedelta(days=_SHOW_CAUSE_RESPONSE_DAYS)).isoformat()
            except ValueError:
                return_date = ""

        order = ShowCauseOrder(
            violation_id=violation.violation_id,
            case_number=case_num,
            respondent=_DEFENDANT,
            return_date=return_date,
            violations_cited=[violation.violation_description],
            issued_date=date.today().isoformat(),
        )
        self._orders.append(order)

        logger.info(
            "Drafted show-cause order for violation %s, return date %s",
            violation.violation_id, return_date,
        )
        return order

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "ShowCauseGenerator",
            "total_motions": len(self._motions),
            "total_orders": len(self._orders),
        }


# ---------------------------------------------------------------------------
# PurgeConditionAnalyzer
# ---------------------------------------------------------------------------


class PurgeConditionAnalyzer:
    """Analyze and track purge conditions for contempt proceedings.

    Per In re Contempt of Dougherty, 429 Mich 81 (1987), purge
    conditions must be achievable and the contemnor must have the
    present ability to comply. Imprisoning a contemnor for failure
    to comply with an impossible condition is unconstitutional.
    """

    def __init__(self) -> None:
        self._analyses: List[Dict[str, Any]] = []
        self._conditions: Dict[str, PurgeCondition] = {}

    def analyze_ability_to_comply(
        self,
        condition: PurgeCondition,
        financial_capacity: Optional[Decimal] = None,
        physical_ability: bool = True,
        legal_impediments: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Analyze whether contemnor has present ability to comply.

        Dougherty requires that the contemnor have the present ability
        to comply with purge conditions. If the contemnor cannot comply
        (e.g., lacks financial resources), continued coercive
        confinement is improper.
        """
        impediments = legal_impediments or []
        issues: List[str] = []
        achievable = True

        if financial_capacity is not None and financial_capacity <= Decimal("0"):
            issues.append(
                "Contemnor lacks financial capacity — purge condition may be "
                "unachievable per Dougherty"
            )
            achievable = False

        if not physical_ability:
            issues.append(
                "Physical inability to comply — condition is not achievable"
            )
            achievable = False

        for imp in impediments:
            issues.append(f"Legal impediment: {imp}")
            achievable = False

        result = {
            "condition_id": condition.condition_id,
            "description": condition.description,
            "is_achievable": achievable,
            "issues": issues,
            "financial_capacity": str(financial_capacity) if financial_capacity else "N/A",
            "physical_ability": physical_ability,
            "legal_impediments": impediments,
            "authority": _AUTHORITY_REFS["dougherty"],
            "recommendation": (
                "Condition is achievable — contemnor has present ability to comply"
                if achievable
                else "Condition may be unachievable — challenge under Dougherty"
            ),
        }
        self._analyses.append(result)
        return result

    def propose_conditions(
        self,
        violation: ContemptViolation,
        monetary_relief: Decimal = Decimal("0.00"),
        behavioral_requirements: Optional[List[str]] = None,
    ) -> List[PurgeCondition]:
        """Propose reasonable purge conditions for the contempt."""
        behaviors = behavioral_requirements or []
        conditions: List[PurgeCondition] = []

        # Behavioral compliance
        conditions.append(PurgeCondition(
            violation_id=violation.violation_id,
            description=(
                f"Full compliance with the Court's order: {violation.order_violated}"
            ),
            is_achievable=True,
        ))

        # Monetary purge condition
        if monetary_relief > Decimal("0"):
            conditions.append(PurgeCondition(
                violation_id=violation.violation_id,
                description=(
                    f"Payment of ${monetary_relief} in compensatory damages "
                    "within the purge period"
                ),
                is_achievable=True,
            ))

        # Additional behavioral requirements
        for req in behaviors:
            conditions.append(PurgeCondition(
                violation_id=violation.violation_id,
                description=req,
                is_achievable=True,
            ))

        for c in conditions:
            self._conditions[c.condition_id] = c

        return conditions

    def check_reasonableness(
        self,
        conditions: List[PurgeCondition],
    ) -> Dict[str, Any]:
        """Evaluate whether proposed purge conditions are reasonable.

        Dougherty requires that conditions be within the contemnor's
        present ability to perform.
        """
        total = len(conditions)
        achievable_count = sum(1 for c in conditions if c.is_achievable)
        unreasonable: List[str] = []

        for c in conditions:
            if not c.is_achievable:
                unreasonable.append(
                    f"Condition '{c.description}' may not be achievable"
                )

        return {
            "total_conditions": total,
            "achievable_count": achievable_count,
            "unreasonable_conditions": unreasonable,
            "all_reasonable": len(unreasonable) == 0,
            "authority": _AUTHORITY_REFS["dougherty"],
            "recommendation": (
                "All conditions appear reasonable and achievable"
                if len(unreasonable) == 0
                else f"{len(unreasonable)} condition(s) may be unachievable — "
                "review under Dougherty before submission"
            ),
        }

    def document_willfulness(
        self,
        violation: ContemptViolation,
        knowledge_of_order: bool = True,
        ability_to_comply: bool = True,
        prior_violations: int = 0,
        explanations_offered: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Document willfulness elements per Sword v Sword.

        Sword requires proof of willful and contumacious disregard
        of the court order.
        """
        explanations = explanations_offered or []
        score = 0
        factors: List[Dict[str, Any]] = []

        # Knowledge of order
        if knowledge_of_order:
            score += 30
            factors.append({
                "factor": "Knowledge of order",
                "present": True,
                "weight": 30,
                "note": "Respondent was aware of the court order",
            })
        else:
            factors.append({
                "factor": "Knowledge of order",
                "present": False,
                "weight": 0,
                "note": "Must prove respondent had notice of the order",
            })

        # Ability to comply
        if ability_to_comply:
            score += 30
            factors.append({
                "factor": "Ability to comply",
                "present": True,
                "weight": 30,
                "note": "Respondent had the ability to comply but chose not to",
            })
        else:
            factors.append({
                "factor": "Ability to comply",
                "present": False,
                "weight": 0,
                "note": "Inability to comply negates willfulness per Dougherty",
            })

        # Prior violations (pattern of contempt)
        if prior_violations > 0:
            prior_weight = min(prior_violations * 10, 20)
            score += prior_weight
            factors.append({
                "factor": "Prior violations",
                "present": True,
                "weight": prior_weight,
                "note": f"{prior_violations} prior violation(s) demonstrate pattern",
            })

        # Explanations offered (mitigating)
        if explanations:
            explanation_deduction = min(len(explanations) * 5, 15)
            score = max(score - explanation_deduction, 0)
            factors.append({
                "factor": "Explanations offered",
                "present": True,
                "weight": -explanation_deduction,
                "note": f"{len(explanations)} explanation(s) may mitigate willfulness",
            })

        # No explanation at all — increases willfulness
        if not explanations and knowledge_of_order and ability_to_comply:
            score += 20
            factors.append({
                "factor": "No explanation offered",
                "present": True,
                "weight": 20,
                "note": "Failure to explain conduct supports willfulness finding",
            })

        result = {
            "violation_id": violation.violation_id,
            "willfulness_score": min(score, 100),
            "factors": factors,
            "standard": violation.contempt_type.standard_of_proof,
            "threshold": (
                _BEYOND_REASONABLE_DOUBT if violation.contempt_type.is_criminal
                else _CLEAR_AND_CONVINCING
            ),
            "meets_standard": (
                (score / 100.0) >= _BEYOND_REASONABLE_DOUBT
                if violation.contempt_type.is_criminal
                else (score / 100.0) >= _CLEAR_AND_CONVINCING
            ),
            "authority": f"{_AUTHORITY_REFS['sword']}; {_AUTHORITY_REFS['henry']}",
        }
        self._analyses.append(result)
        return result

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "PurgeConditionAnalyzer",
            "total_analyses": len(self._analyses),
            "tracked_conditions": len(self._conditions),
        }


# ---------------------------------------------------------------------------
# ContemptSanctionCalculator
# ---------------------------------------------------------------------------


class ContemptSanctionCalculator:
    """Calculate appropriate sanctions for contempt proceedings.

    Civil contempt sanctions are coercive (designed to compel compliance)
    or compensatory (designed to make the injured party whole).
    Criminal contempt sanctions are punitive (designed to vindicate
    the court's authority). DeGeorge v Warwick, 404 Mich 89 (1978).
    """

    def __init__(self) -> None:
        self._sanctions: List[ContemptSanction] = []

    def calculate_compensatory_damages(
        self,
        violation: ContemptViolation,
        direct_costs: Decimal = Decimal("0.00"),
        lost_income: Decimal = Decimal("0.00"),
        childcare_costs: Decimal = Decimal("0.00"),
        transportation_costs: Decimal = Decimal("0.00"),
        other_costs: Decimal = Decimal("0.00"),
    ) -> Dict[str, Any]:
        """Calculate compensatory damages arising from the contempt.

        Compensatory civil contempt sanctions reimburse the injured
        party for losses suffered due to the violation.
        """
        total = (
            direct_costs + lost_income + childcare_costs
            + transportation_costs + other_costs
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        breakdown: Dict[str, str] = {}
        if direct_costs > 0:
            breakdown["direct_costs"] = str(direct_costs)
        if lost_income > 0:
            breakdown["lost_income"] = str(lost_income)
        if childcare_costs > 0:
            breakdown["childcare_costs"] = str(childcare_costs)
        if transportation_costs > 0:
            breakdown["transportation_costs"] = str(transportation_costs)
        if other_costs > 0:
            breakdown["other_costs"] = str(other_costs)

        sanction = ContemptSanction(
            violation_id=violation.violation_id,
            sanction_type="compensatory",
            amount=total,
            legal_basis="MCL 600.1701; MCL 600.1745",
        )
        self._sanctions.append(sanction)

        return {
            "sanction_id": sanction.sanction_id,
            "violation_id": violation.violation_id,
            "type": "compensatory",
            "total": str(total),
            "breakdown": breakdown,
            "legal_basis": sanction.legal_basis,
            "authority": _AUTHORITY_REFS["degeorge"],
        }

    def calculate_attorney_fees(
        self,
        hours_spent: Decimal = Decimal("0.00"),
        hourly_rate: Decimal = Decimal("0.00"),
        filing_fees: Decimal = Decimal("0.00"),
        service_costs: Decimal = Decimal("0.00"),
        is_pro_se: bool = True,
    ) -> Dict[str, Any]:
        """Calculate attorney/litigation fees for contempt proceeding.

        Pro se litigants may recover costs but not attorney fees in
        most circumstances. Filing fees and service costs are
        recoverable as compensatory damages.
        """
        if is_pro_se:
            fees = Decimal("0.00")
            costs = (filing_fees + service_costs).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            total = costs
            note = (
                "Pro se litigant — attorney fees not recoverable, "
                "but filing fees and costs are compensable"
            )
        else:
            fees = (hours_spent * hourly_rate).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            costs = (filing_fees + service_costs).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            total = fees + costs
            note = "Attorney fees calculated via lodestar method"

        return {
            "attorney_fees": str(fees),
            "costs": str(costs),
            "total": str(total),
            "is_pro_se": is_pro_se,
            "note": note,
            "breakdown": {
                "hours": str(hours_spent),
                "rate": str(hourly_rate),
                "filing_fees": str(filing_fees),
                "service_costs": str(service_costs),
            },
        }

    def recommend_incarceration_period(
        self,
        contempt_type: ContemptType,
        severity: int = 50,
        prior_contempts: int = 0,
        ongoing_harm: bool = False,
    ) -> Dict[str, Any]:
        """Recommend incarceration period for contempt.

        Civil: coercive confinement until purge (no fixed term).
        Criminal: up to 93 days per MCL 600.1715.
        """
        if contempt_type.is_civil:
            return {
                "type": "coercive",
                "fixed_term": False,
                "description": (
                    "Coercive civil confinement until purge conditions are met. "
                    "Contemnor holds the keys to the jail — compliance ends "
                    "confinement. Must be reviewed periodically."
                ),
                "review_period_days": _CIVIL_COERCIVE_REVIEW_DAYS,
                "legal_basis": "MCL 600.1745; In re Contempt of Dougherty",
                "max_days": None,
            }

        # Criminal contempt — fixed term
        base_days = max(1, int(severity * _CRIMINAL_CONTEMPT_MAX_JAIL / 100))
        multiplier = 1.0 + (prior_contempts * 0.25)
        if ongoing_harm:
            multiplier += 0.5
        recommended = min(
            int(base_days * multiplier),
            _CRIMINAL_CONTEMPT_MAX_JAIL,
        )

        return {
            "type": "punitive",
            "fixed_term": True,
            "recommended_days": recommended,
            "max_days": _CRIMINAL_CONTEMPT_MAX_JAIL,
            "severity_score": severity,
            "prior_contempts": prior_contempts,
            "ongoing_harm": ongoing_harm,
            "legal_basis": "MCL 600.1715; MCL 600.1721",
            "description": (
                f"Recommended {recommended} days incarceration. "
                f"Maximum under MCL 600.1715: {_CRIMINAL_CONTEMPT_MAX_JAIL} days."
            ),
        }

    def assess_coercive_vs_punitive(
        self,
        contempt_type: ContemptType,
        sanction_purpose: str = "",
    ) -> Dict[str, Any]:
        """Assess whether a proposed sanction is coercive or punitive.

        DeGeorge v Warwick: The distinction depends on the character
        and purpose of the sanction, not its label.
        """
        is_coercive = contempt_type.is_civil
        is_punitive = contempt_type.is_criminal

        return {
            "contempt_type": contempt_type.value,
            "sanction_character": "coercive" if is_coercive else "punitive",
            "purpose": (
                "To coerce compliance with court order or compensate injured party"
                if is_coercive
                else "To punish contemnor and vindicate authority of the court"
            ),
            "standard_of_proof": contempt_type.standard_of_proof,
            "procedural_protections": (
                "Right to jury trial; proof beyond reasonable doubt; "
                "right to counsel per MCL 600.1715"
                if is_punitive
                else "Clear and convincing evidence; no jury right; "
                "contemnor bears no criminal due-process protections"
            ),
            "legal_basis": _AUTHORITY_REFS["degeorge"],
            "stated_purpose": sanction_purpose,
        }

    def get_stats(self) -> Dict[str, Any]:
        by_type: Dict[str, int] = {}
        for s in self._sanctions:
            by_type[s.sanction_type] = by_type.get(s.sanction_type, 0) + 1
        return {
            "component": "ContemptSanctionCalculator",
            "total_sanctions": len(self._sanctions),
            "by_type": by_type,
        }


# ---------------------------------------------------------------------------
# ContemptDocumenter
# ---------------------------------------------------------------------------


class ContemptDocumenter:
    """Document contempt violations for court proceedings.

    Builds violation timelines, catalogs evidence, generates exhibit
    lists, and creates contempt briefs for filing.
    """

    def __init__(self) -> None:
        self._timelines: List[Dict[str, Any]] = []
        self._briefs: List[Dict[str, Any]] = []

    def build_violation_timeline(
        self,
        violations: List[ContemptViolation],
    ) -> List[Dict[str, Any]]:
        """Build a chronological timeline of violations for the court."""
        sorted_violations = sorted(
            violations,
            key=lambda v: v.violation_date or "",
        )
        timeline = []
        for i, v in enumerate(sorted_violations, 1):
            timeline.append({
                "sequence": i,
                "date": v.violation_date,
                "order_violated": v.order_violated,
                "description": v.violation_description,
                "type": v.contempt_type.value,
                "evidence_count": len(v.evidence_refs),
                "status": v.status.value,
            })

        self._timelines.append({
            "entry_count": len(timeline),
            "date_range": (
                f"{sorted_violations[0].violation_date} to "
                f"{sorted_violations[-1].violation_date}"
                if sorted_violations
                else "N/A"
            ),
        })
        return timeline

    def catalog_evidence(
        self,
        violations: List[ContemptViolation],
    ) -> Dict[str, Any]:
        """Catalog all evidence across violations for exhibit preparation."""
        evidence_map: Dict[str, List[str]] = {}
        total_refs = 0

        for v in violations:
            for ref in v.evidence_refs:
                total_refs += 1
                if v.violation_id not in evidence_map:
                    evidence_map[v.violation_id] = []
                evidence_map[v.violation_id].append(ref)

        return {
            "total_violations": len(violations),
            "total_evidence_refs": total_refs,
            "evidence_by_violation": evidence_map,
            "unique_exhibits": list(set(
                ref for v in violations for ref in v.evidence_refs
            )),
        }

    def generate_exhibit_list(
        self,
        violations: List[ContemptViolation],
        starting_number: int = 1,
    ) -> List[Dict[str, Any]]:
        """Generate a numbered exhibit list for court filing."""
        exhibits: List[Dict[str, Any]] = []
        seen: set = set()
        number = starting_number

        for v in violations:
            for ref in v.evidence_refs:
                if ref not in seen:
                    seen.add(ref)
                    exhibits.append({
                        "exhibit_number": number,
                        "description": ref,
                        "violation_id": v.violation_id,
                        "violation_date": v.violation_date,
                    })
                    number += 1

        return exhibits

    def create_contempt_brief(
        self,
        violations: List[ContemptViolation],
        case_number: str = "",
        additional_arguments: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a brief in support of contempt motion."""
        case_num = case_number or LANE_CASES["A"]
        args = additional_arguments or []

        timeline = self.build_violation_timeline(violations)
        evidence_catalog = self.catalog_evidence(violations)
        exhibit_list = self.generate_exhibit_list(violations)

        brief: Dict[str, Any] = {
            "document_type": "Brief in Support of Motion for Contempt",
            "case_number": case_num,
            "court": _COURT,
            "judge": _JUDGE,
            "movant": _PLAINTIFF,
            "respondent": _DEFENDANT,
            "sections": [
                {
                    "heading": "TABLE OF CONTENTS",
                    "content": "See separate Table of Contents page",
                },
                {
                    "heading": "TABLE OF AUTHORITIES",
                    "authorities": [
                        "MCL 600.1701 — Powers of courts (civil contempt)",
                        "MCL 600.1715 — Criminal contempt procedure",
                        "MCL 600.1745 — Civil contempt, coercive sanctions",
                        "MCR 3.606 — Contempt proceedings in domestic relations",
                        "In re Contempt of Dougherty, 429 Mich 81 (1987)",
                        "DeGeorge v Warwick, 404 Mich 89 (1978)",
                        "Sword v Sword, 399 Mich 367 (1976)",
                        "In re Contempt of Henry, 282 Mich App 656 (2009)",
                    ],
                },
                {
                    "heading": "STATEMENT OF FACTS",
                    "content": (
                        f"This action involves {len(violations)} violation(s) "
                        f"of court orders in case {case_num}."
                    ),
                    "timeline": timeline,
                },
                {
                    "heading": "ARGUMENT",
                    "content": (
                        "Respondent's conduct demonstrates a willful and "
                        "contumacious disregard of this Court's orders."
                    ),
                    "additional_arguments": args,
                },
                {
                    "heading": "CONCLUSION",
                    "content": (
                        "For the reasons stated above, the Court should find "
                        "Respondent in contempt and impose appropriate sanctions."
                    ),
                },
            ],
            "evidence_catalog": evidence_catalog,
            "exhibit_list": exhibit_list,
            "total_violations": len(violations),
            "sha256": hashlib.sha256(
                json.dumps([v.to_dict() for v in violations], sort_keys=True).encode()
            ).hexdigest()[:16],
        }

        self._briefs.append(brief)
        logger.info(
            "Created contempt brief for %d violation(s) in %s",
            len(violations), case_num,
        )
        return brief

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "ContemptDocumenter",
            "total_timelines": len(self._timelines),
            "total_briefs": len(self._briefs),
        }


# ---------------------------------------------------------------------------
# ContemptEngine  (main orchestrator)
# ---------------------------------------------------------------------------


class ContemptEngine:
    """Top-level orchestrator for contempt proceedings.

    Combines :class:`ShowCauseGenerator`, :class:`PurgeConditionAnalyzer`,
    :class:`ContemptSanctionCalculator`, and :class:`ContemptDocumenter`
    into a unified system for prosecuting civil and criminal contempt
    in Michigan courts.

    Michigan Authority:
        MCL 600.1701-1775, MCR 3.606, In re Contempt of Dougherty,
        DeGeorge v Warwick, Sword v Sword
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or _DB_PATH
        self._show_cause_gen = ShowCauseGenerator()
        self._purge_analyzer = PurgeConditionAnalyzer()
        self._sanction_calc = ContemptSanctionCalculator()
        self._documenter = ContemptDocumenter()
        self._violations: Dict[str, ContemptViolation] = {}
        self._proceedings: Dict[str, Dict[str, Any]] = {}

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

    # -- Core operations --

    def identify_violations(
        self,
        order_violated: str = "",
        violation_date: str = "",
        violation_description: str = "",
        evidence_refs: Optional[List[str]] = None,
        contempt_type: ContemptType = ContemptType.CIVIL_CONSTRUCTIVE,
    ) -> ContemptViolation:
        """Identify and record a contempt violation."""
        refs = evidence_refs or []
        violation = ContemptViolation(
            order_violated=order_violated,
            violation_date=violation_date,
            violation_description=violation_description,
            evidence_refs=refs,
            contempt_type=contempt_type,
            status=ContemptStatus.IDENTIFIED,
        )
        self._violations[violation.violation_id] = violation
        logger.info(
            "Identified violation %s: %s",
            violation.violation_id, violation_description[:80],
        )
        return violation

    def file_contempt(
        self,
        violation_id: str,
        case_number: str = "",
        additional_facts: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Prepare and file a contempt motion for a violation."""
        violation = self._violations.get(violation_id)
        if not violation:
            return {"error": f"Violation {violation_id} not found"}

        motion = self._show_cause_gen.draft_motion(
            violation=violation,
            case_number=case_number,
            additional_facts=additional_facts,
        )
        proposed_order = self._show_cause_gen.draft_proposed_order(
            violation=violation,
            case_number=case_number,
        )
        purge_conditions = self._show_cause_gen.calculate_purge_conditions(violation)

        violation.status = ContemptStatus.MOTION_FILED
        self._violations[violation_id] = violation

        proceeding: Dict[str, Any] = {
            "violation_id": violation_id,
            "motion": motion,
            "proposed_order": proposed_order.to_dict(),
            "purge_conditions": [c.to_dict() for c in purge_conditions],
            "status": ContemptStatus.MOTION_FILED.value,
            "filed_date": date.today().isoformat(),
        }
        self._proceedings[violation_id] = proceeding

        logger.info("Filed contempt for violation %s", violation_id)
        return proceeding

    def track_proceedings(
        self,
        violation_id: str,
    ) -> Dict[str, Any]:
        """Track the status of a contempt proceeding."""
        proceeding = self._proceedings.get(violation_id)
        if not proceeding:
            return {"error": f"No proceeding found for {violation_id}"}

        violation = self._violations.get(violation_id)
        return {
            "violation_id": violation_id,
            "current_status": violation.status.value if violation else "unknown",
            "next_steps": violation.status.next_statuses if violation else [],
            "proceeding": proceeding,
        }

    def update_status(
        self,
        violation_id: str,
        new_status: ContemptStatus,
    ) -> Optional[ContemptViolation]:
        """Update the status of a contempt violation."""
        violation = self._violations.get(violation_id)
        if violation:
            old_status = violation.status
            if new_status.value in old_status.next_statuses:
                violation.status = new_status
                logger.info(
                    "Contempt %s: %s → %s",
                    violation_id, old_status.value, new_status.value,
                )
            else:
                logger.warning(
                    "Invalid transition %s → %s for violation %s",
                    old_status.value, new_status.value, violation_id,
                )
        return violation

    def monitor_purge(
        self,
        violation_id: str,
        conditions_met: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Monitor purge condition compliance for a contempt finding."""
        met_ids = set(conditions_met or [])
        proceeding = self._proceedings.get(violation_id, {})
        purge_list = proceeding.get("purge_conditions", [])

        total = len(purge_list)
        satisfied = 0
        details: List[Dict[str, Any]] = []

        for pc in purge_list:
            is_met = pc.get("condition_id", "") in met_ids
            if is_met:
                satisfied += 1
            details.append({
                "condition_id": pc.get("condition_id", ""),
                "description": pc.get("description", ""),
                "is_satisfied": is_met,
            })

        all_purged = satisfied == total and total > 0
        if all_purged:
            violation = self._violations.get(violation_id)
            if violation:
                violation.status = ContemptStatus.PURGED

        return {
            "violation_id": violation_id,
            "total_conditions": total,
            "satisfied": satisfied,
            "remaining": total - satisfied,
            "all_purged": all_purged,
            "details": details,
        }

    def get_violation(self, violation_id: str) -> Optional[ContemptViolation]:
        """Retrieve a violation by ID."""
        return self._violations.get(violation_id)

    def list_violations(
        self,
        status: Optional[ContemptStatus] = None,
        contempt_type: Optional[ContemptType] = None,
    ) -> List[ContemptViolation]:
        """List violations with optional filters."""
        results = list(self._violations.values())
        if status:
            results = [v for v in results if v.status == status]
        if contempt_type:
            results = [v for v in results if v.contempt_type == contempt_type]
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Return runtime statistics."""
        by_type: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        for v in self._violations.values():
            by_type[v.contempt_type.value] = by_type.get(v.contempt_type.value, 0) + 1
            by_status[v.status.value] = by_status.get(v.status.value, 0) + 1

        return {
            "module": "contempt_engine",
            "total_violations": len(self._violations),
            "total_proceedings": len(self._proceedings),
            "by_type": by_type,
            "by_status": by_status,
            "db_path": str(self._db_path),
            "show_cause_generator": self._show_cause_gen.get_stats(),
            "purge_condition_analyzer": self._purge_analyzer.get_stats(),
            "sanction_calculator": self._sanction_calc.get_stats(),
            "documenter": self._documenter.get_stats(),
        }

    def reset(self) -> None:
        """Clear all loaded violations and proceedings."""
        self._violations.clear()
        self._proceedings.clear()


# ---------------------------------------------------------------------------
# CLI demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sys.stdout = open(  # noqa: SIM115
        sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace"
    )
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print("=" * 60)
    print("  Contempt Engine — LitigationOS")
    print("=" * 60)
    print()

    engine = ContemptEngine()

    # Identify a violation
    v = engine.identify_violations(
        order_violated="Custody Order 2024-001507-DC ¶ 12",
        violation_date="2025-07-04",
        violation_description="Denied scheduled parenting time on July 4th holiday",
        evidence_refs=["Exhibit A — text messages", "Exhibit B — calendar"],
        contempt_type=ContemptType.CIVIL_CONSTRUCTIVE,
    )
    print(f"Violation ID: {v.violation_id}")
    print(f"  Type: {v.contempt_type.value}")
    print(f"  Status: {v.status.value}")
    print()

    # File contempt
    proceeding = engine.file_contempt(v.violation_id, case_number=LANE_CASES["A"])
    print(f"Contempt filed: {proceeding.get('status')}")
    print(f"  Purge conditions: {len(proceeding.get('purge_conditions', []))}")
    print()

    # Calculate sanctions
    calc = ContemptSanctionCalculator()
    damages = calc.calculate_compensatory_damages(
        violation=v,
        direct_costs=Decimal("500.00"),
        childcare_costs=Decimal("200.00"),
    )
    print(f"Compensatory damages: ${damages['total']}")
    print()

    # Stats
    stats = engine.get_stats()
    print("Stats:")
    for k, val in stats.items():
        print(f"  {k}: {val}")
