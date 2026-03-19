# -*- coding: utf-8 -*-
"""
Default Judgment Engine — LitigationOS Legal AI Subsystem
==========================================================
Default judgment pursuit and defense for Michigan litigation.
Handles entry of default, default judgment, setting aside defaults,
void judgment analysis, and good-cause evaluation per Michigan
Court Rules and the Revised Judicature Act.

Case Context
------------
    Plaintiff:  Andrew James Pigors (Pro Se)
    Defendant:  Emily A. Watson
    Child:      L.D.W. (per MCR 8.119(H)) — Male
    Judge:      Hon. Jenny L. McNeill — 14th Circuit Court
    Cases:      2024-001507-DC, 2025-002760-CZ, 2023-5907-PP, COA 366810

Michigan Rules & Statutes
-------------------------
    MCR 2.603    – Default and Default Judgment
    MCR 2.603(A) – Entry of Default
    MCR 2.603(B) – Default Judgment (by clerk or court)
    MCR 2.603(D) – Setting Aside Default / Default Judgment
    MCR 2.612    – Relief from Judgment or Order
    MCR 2.612(C)(1)(d) – Void judgments (no time limit)
    MCL 600.2531 – Entry of judgment
    MCL 600.5735 – Service requirements
    MCR 2.105    – Service of process
    50 USC § 3931 – Servicemembers Civil Relief Act (military check)

    Shawl v Spence factors for setting aside default:
      (1) Whether the party has a meritorious defense
      (2) Whether the party has shown good cause
      (3) Whether the opposing party would be prejudiced

Usage::

    from legal_ai.default_judgment_engine import DefaultJudgmentEngine

    engine = DefaultJudgmentEngine()
    req = engine.pursue_default(
        case_number="2025-002760-CZ",
        defendant_name="Emily A. Watson",
        service_date="2025-03-15",
    )
    analysis = engine.move_to_set_aside(req.request_id, factors={...})

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

logger = logging.getLogger("legal_ai.default_judgment_engine")

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
# Michigan default judgment timelines
# ---------------------------------------------------------------------------
_ANSWER_DEADLINE_PERSONAL = 21    # MCR 2.108(A)(1) — personal service in Michigan
_ANSWER_DEADLINE_MAIL = 28        # MCR 2.105(A)(2) — service by mail
_ANSWER_DEADLINE_PUBLICATION = 28 # MCR 2.106(D)
_SET_ASIDE_DEFAULT_DEADLINE = None  # MCR 2.603(D)(1) — "reasonable time"
_VOID_JUDGMENT_NO_LIMIT = True    # MCR 2.612(C)(1)(d) — no time limit
_MCR_2612_C1_DEADLINE_DAYS = 365  # MCR 2.612(C)(2) — 1 year for (a)(b)(c)

# Service methods and their MCR references
_SERVICE_METHODS: Dict[str, Dict[str, Any]] = {
    "personal": {
        "mcr": "MCR 2.105(A)(1)",
        "answer_days": _ANSWER_DEADLINE_PERSONAL,
        "description": "Personal service — hand delivery to defendant",
    },
    "registered_mail": {
        "mcr": "MCR 2.105(A)(2)",
        "answer_days": _ANSWER_DEADLINE_MAIL,
        "description": "Registered or certified mail, return receipt requested",
    },
    "substituted": {
        "mcr": "MCR 2.105(A)(3)",
        "answer_days": _ANSWER_DEADLINE_PERSONAL,
        "description": "Substituted service at usual place of abode",
    },
    "publication": {
        "mcr": "MCR 2.106",
        "answer_days": _ANSWER_DEADLINE_PUBLICATION,
        "description": "Service by publication (last resort)",
    },
    "acknowledged": {
        "mcr": "MCR 2.105(A)(4)",
        "answer_days": _ANSWER_DEADLINE_PERSONAL,
        "description": "Acknowledged service — defendant signs acknowledgment",
    },
}


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class DefaultType(str, Enum):
    """Types of default under Michigan law."""

    ENTRY_OF_DEFAULT = "entry_of_default"      # MCR 2.603(A)
    DEFAULT_JUDGMENT = "default_judgment"        # MCR 2.603(B)
    CONSENT_JUDGMENT = "consent_judgment"        # MCR 2.602

    @property
    def mcr_reference(self) -> str:
        _refs = {
            "entry_of_default": "MCR 2.603(A)",
            "default_judgment": "MCR 2.603(B)",
            "consent_judgment": "MCR 2.602",
        }
        return _refs.get(self.value, "MCR 2.603")


class DefaultStatus(str, Enum):
    """Status progression of a default proceeding."""

    PENDING = "pending"
    ENTERED = "entered"
    JUDGMENT_ENTERED = "judgment_entered"
    SET_ASIDE = "set_aside"
    VACATED = "vacated"

    @property
    def is_final(self) -> bool:
        return self in (
            DefaultStatus.JUDGMENT_ENTERED,
            DefaultStatus.SET_ASIDE,
            DefaultStatus.VACATED,
        )


class GoodCauseFactor(str, Enum):
    """Shawl v Spence factors for setting aside default."""

    MERITORIOUS_DEFENSE = "meritorious_defense"
    GOOD_CAUSE = "good_cause"
    NO_PREJUDICE = "no_prejudice"

    @property
    def description(self) -> str:
        _descs = {
            "meritorious_defense": "Party has a meritorious defense to the claim",
            "good_cause": "Party has shown good cause for failure to timely respond",
            "no_prejudice": "Opposing party would not be unfairly prejudiced",
        }
        return _descs.get(self.value, "")


class VoidBasis(str, Enum):
    """Bases for declaring a judgment void."""

    LACK_OF_JURISDICTION = "lack_of_jurisdiction"
    DEFECTIVE_SERVICE = "defective_service"
    DUE_PROCESS_VIOLATION = "due_process_violation"
    FRAUD_ON_COURT = "fraud_on_court"

    @property
    def mcr_reference(self) -> str:
        _refs = {
            "lack_of_jurisdiction": "MCR 2.612(C)(1)(d)",
            "defective_service": "MCR 2.612(C)(1)(d)",
            "due_process_violation": "MCR 2.612(C)(1)(d); US Const Amend XIV",
            "fraud_on_court": "MCR 2.612(C)(1)(c)",
        }
        return _refs.get(self.value, "MCR 2.612(C)(1)(d)")


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class DefaultRequest:
    """A request for entry of default or default judgment."""

    request_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    case_number: str = ""
    defendant_name: str = ""
    default_type: DefaultType = DefaultType.ENTRY_OF_DEFAULT
    service_date: str = ""
    service_method: str = "personal"
    default_date: str = ""
    judgment_amount: Decimal = Decimal("0.00")
    status: DefaultStatus = DefaultStatus.PENDING
    court: str = _COURT
    judge: str = _JUDGE
    answer_deadline: str = ""
    military_status_checked: bool = False
    military_affidavit_filed: bool = False
    notes: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "case_number": self.case_number,
            "defendant_name": self.defendant_name,
            "default_type": self.default_type.value,
            "service_date": self.service_date,
            "service_method": self.service_method,
            "default_date": self.default_date,
            "judgment_amount": str(self.judgment_amount),
            "status": self.status.value,
            "court": self.court,
            "judge": self.judge,
            "answer_deadline": self.answer_deadline,
            "military_status_checked": self.military_status_checked,
            "military_affidavit_filed": self.military_affidavit_filed,
            "notes": self.notes,
            "created_at": self.created_at,
        }


@dataclass
class ServiceRecord:
    """Record of service for default judgment purposes."""

    service_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    case_number: str = ""
    served_party: str = ""
    service_method: str = "personal"
    service_date: str = ""
    server_name: str = ""
    proof_filed: bool = False
    proof_filed_date: str = ""
    is_valid: bool = True
    defects: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "service_id": self.service_id,
            "case_number": self.case_number,
            "served_party": self.served_party,
            "service_method": self.service_method,
            "service_date": self.service_date,
            "server_name": self.server_name,
            "proof_filed": self.proof_filed,
            "proof_filed_date": self.proof_filed_date,
            "is_valid": self.is_valid,
            "defects": self.defects,
        }


@dataclass
class GoodCauseResult:
    """Result of a good-cause analysis for setting aside default."""

    analysis_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    request_id: str = ""
    factors: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    overall_score: int = 0  # 0-100
    recommendation: str = ""
    legal_basis: str = ""
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "request_id": self.request_id,
            "factors": self.factors,
            "overall_score": self.overall_score,
            "recommendation": self.recommendation,
            "legal_basis": self.legal_basis,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
        }


@dataclass
class VoidJudgmentResult:
    """Result of a void-judgment analysis."""

    analysis_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    request_id: str = ""
    is_void: bool = False
    void_bases: List[str] = field(default_factory=list)
    evidence_needed: List[str] = field(default_factory=list)
    time_limit: str = ""
    legal_basis: str = ""
    recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "request_id": self.request_id,
            "is_void": self.is_void,
            "void_bases": self.void_bases,
            "evidence_needed": self.evidence_needed,
            "time_limit": self.time_limit,
            "legal_basis": self.legal_basis,
            "recommendation": self.recommendation,
        }


# ---------------------------------------------------------------------------
# ServiceVerifier
# ---------------------------------------------------------------------------


class ServiceVerifier:
    """Verify proper service for default judgment eligibility.

    MCR 2.603(A)(1) requires an affidavit showing that the party
    against whom default is sought has been properly served and has
    failed to plead or otherwise defend.
    """

    def __init__(self) -> None:
        self._records: List[ServiceRecord] = []

    def verify_proper_service(
        self,
        service_method: str,
        service_date: str,
        server_name: str = "",
        proof_filed: bool = False,
    ) -> Dict[str, Any]:
        """Verify whether service was proper under MCR 2.105.

        Parameters
        ----------
        service_method : str — personal, registered_mail, substituted, publication, acknowledged
        service_date : str — ISO date of service
        server_name : str — name of process server
        proof_filed : bool — whether proof of service was filed

        Returns
        -------
        dict with verification results
        """
        method_info = _SERVICE_METHODS.get(service_method, {})
        defects: List[str] = []

        # Check method validity
        if not method_info:
            defects.append(f"Unknown service method: {service_method}")

        # Check server qualifications
        if service_method == "personal" and not server_name:
            defects.append("Process server name required for personal service — MCR 2.103")

        # Check proof of service
        if not proof_filed:
            defects.append("Proof of service not filed — MCR 2.104")

        # Check service date
        try:
            svc_date = date.fromisoformat(service_date)
            if svc_date > date.today():
                defects.append("Service date is in the future")
        except ValueError:
            defects.append(f"Invalid service date: {service_date}")

        is_valid = len(defects) == 0

        record = ServiceRecord(
            service_method=service_method,
            service_date=service_date,
            server_name=server_name,
            proof_filed=proof_filed,
            is_valid=is_valid,
            defects=defects,
        )
        self._records.append(record)

        answer_days = method_info.get("answer_days", _ANSWER_DEADLINE_PERSONAL)
        try:
            svc_date = date.fromisoformat(service_date)
            answer_deadline = svc_date + timedelta(days=answer_days)
        except ValueError:
            answer_deadline = date.today() + timedelta(days=answer_days)

        return {
            "is_valid": is_valid,
            "service_method": service_method,
            "service_date": service_date,
            "mcr_reference": method_info.get("mcr", "MCR 2.105"),
            "answer_deadline": answer_deadline.isoformat(),
            "answer_days": answer_days,
            "defects": defects,
            "server_name": server_name,
            "proof_filed": proof_filed,
        }

    def check_mcr_2_105(
        self, service_method: str,
    ) -> Dict[str, Any]:
        """Check service compliance with MCR 2.105 requirements."""
        method_info = _SERVICE_METHODS.get(service_method, {})

        requirements: Dict[str, Any] = {
            "method": service_method,
            "mcr_reference": method_info.get("mcr", "MCR 2.105"),
            "description": method_info.get("description", "Unknown method"),
            "answer_days": method_info.get("answer_days", _ANSWER_DEADLINE_PERSONAL),
            "requirements": [],
        }

        if service_method == "personal":
            requirements["requirements"] = [
                "Must be served by person 18+ years of age — MCR 2.103(A)",
                "Must deliver summons and complaint to defendant personally — MCR 2.105(A)(1)",
                "Service valid anywhere in Michigan — MCR 2.105(B)",
            ]
        elif service_method == "registered_mail":
            requirements["requirements"] = [
                "Send via registered or certified mail, return receipt requested — MCR 2.105(A)(2)",
                "Must be addressed to defendant at last known address",
                "Delivery restricted to addressee only",
                "Must file return receipt with proof of service",
            ]
        elif service_method == "substituted":
            requirements["requirements"] = [
                "Leave at usual place of abode with person of suitable age — MCR 2.105(A)(3)",
                "Must also mail copy to defendant's last known address",
                "Only available after diligent attempt at personal service",
            ]
        elif service_method == "publication":
            requirements["requirements"] = [
                "Available only when defendant cannot be found — MCR 2.106",
                "Must first demonstrate diligent efforts to serve personally",
                "Publish in newspaper of general circulation in county — MCR 2.106(C)",
                "Publication for 3 consecutive weeks minimum",
                "Court order required before service by publication — MCR 2.106(B)",
            ]
        elif service_method == "acknowledged":
            requirements["requirements"] = [
                "Defendant acknowledges receipt of summons and complaint — MCR 2.105(A)(4)",
                "Acknowledgment must be in writing, signed, and dated",
            ]

        return requirements

    def check_military_status(
        self, defendant_name: str,
    ) -> Dict[str, Any]:
        """Generate military status check requirements.

        50 USC § 3931 (Servicemembers Civil Relief Act) requires
        verification that the defendant is not on active military
        duty before entry of default.
        """
        return {
            "defendant": defendant_name,
            "requirement": "Must verify non-military status before default entry",
            "legal_basis": "50 USC § 3931; MCR 2.603(A)(1)",
            "check_methods": [
                "Search the DoD Manpower Data Center (DMDC) online database",
                "File Affidavit of Non-Military Service with the court",
                "If unable to determine: state 'unable to determine' in affidavit",
            ],
            "consequences_if_military": [
                "Court must appoint attorney for defendant — 50 USC § 3931(b)(2)",
                "Court may stay proceedings for at least 90 days — 50 USC § 3932",
                "Default judgment entered without compliance may be set aside",
            ],
            "dmdc_url": "https://scra.dmdc.osd.mil/",
        }

    def verify_affidavit_of_non_military(
        self, affidavit_filed: bool = False, status_result: str = "non_military",
    ) -> Dict[str, Any]:
        """Verify the affidavit of non-military service status."""
        is_compliant = affidavit_filed and status_result in ("non_military", "unknown")

        result: Dict[str, Any] = {
            "affidavit_filed": affidavit_filed,
            "status_result": status_result,
            "is_compliant": is_compliant,
            "legal_basis": "50 USC § 3931; MCR 2.603(A)(1)",
            "issues": [],
        }

        if not affidavit_filed:
            result["issues"].append(
                "Affidavit of non-military service must be filed — 50 USC § 3931(b)(1)"
            )
        if status_result == "active_duty":
            result["issues"].append(
                "Defendant is on active duty — SCRA protections apply"
            )
            result["is_compliant"] = False

        return result

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "ServiceVerifier",
            "total_records": len(self._records),
            "valid_count": sum(1 for r in self._records if r.is_valid),
            "invalid_count": sum(1 for r in self._records if not r.is_valid),
        }


# ---------------------------------------------------------------------------
# DefaultEntryProcessor
# ---------------------------------------------------------------------------


class DefaultEntryProcessor:
    """Process requests for entry of default per MCR 2.603(A).

    Entry of default is a prerequisite to default judgment.  It
    establishes that the defendant has failed to plead or otherwise
    defend within the time allowed.
    """

    def __init__(self) -> None:
        self._service_verifier = ServiceVerifier()
        self._processed: List[Dict[str, Any]] = []

    def verify_eligibility(
        self,
        request: DefaultRequest,
    ) -> Dict[str, Any]:
        """Verify eligibility for entry of default.

        MCR 2.603(A) requirements:
        1. Defendant was properly served
        2. Time to answer has expired
        3. No answer or responsive pleading filed
        4. Non-military affidavit filed
        """
        issues: List[str] = []
        checks: Dict[str, bool] = {}

        # Check service
        method_info = _SERVICE_METHODS.get(request.service_method, {})
        answer_days = method_info.get("answer_days", _ANSWER_DEADLINE_PERSONAL)

        try:
            svc_date = date.fromisoformat(request.service_date)
            deadline = svc_date + timedelta(days=answer_days)
            checks["answer_deadline_passed"] = date.today() > deadline
            if not checks["answer_deadline_passed"]:
                issues.append(
                    f"Answer deadline ({deadline.isoformat()}) has not yet passed"
                )
        except ValueError:
            checks["answer_deadline_passed"] = False
            issues.append(f"Invalid service date: {request.service_date}")

        # Military status
        checks["military_status_checked"] = request.military_status_checked
        if not request.military_status_checked:
            issues.append(
                "Must check military status and file affidavit — 50 USC § 3931"
            )

        checks["military_affidavit_filed"] = request.military_affidavit_filed
        if not request.military_affidavit_filed:
            issues.append(
                "Affidavit of non-military service not filed — MCR 2.603(A)(1)"
            )

        is_eligible = len(issues) == 0

        result = {
            "request_id": request.request_id,
            "case_number": request.case_number,
            "defendant": request.defendant_name,
            "is_eligible": is_eligible,
            "checks": checks,
            "issues": issues,
            "service_method": request.service_method,
            "answer_deadline": request.answer_deadline,
            "legal_basis": "MCR 2.603(A)",
        }
        self._processed.append(result)
        return result

    def calculate_damages(
        self,
        principal: Decimal = Decimal("0.00"),
        interest_rate: Decimal = Decimal("0.05"),
        from_date: str = "",
        costs: Decimal = Decimal("0.00"),
        attorney_fees: Decimal = Decimal("0.00"),
    ) -> Dict[str, Any]:
        """Calculate damages for default judgment request.

        MCR 2.603(B)(1)(b): Clerk may enter judgment for a sum certain.
        MCR 2.603(B)(2): Court hearing required for unliquidated damages.
        """
        try:
            start = date.fromisoformat(from_date) if from_date else date.today()
        except ValueError:
            start = date.today()

        days_elapsed = (date.today() - start).days
        years_elapsed = Decimal(str(days_elapsed)) / Decimal("365.25")
        interest = (principal * interest_rate * years_elapsed).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        total = principal + interest + costs + attorney_fees

        is_sum_certain = attorney_fees == Decimal("0.00")

        return {
            "principal": str(principal),
            "interest_rate": str(interest_rate),
            "interest_accrued": str(interest),
            "days_elapsed": days_elapsed,
            "costs": str(costs),
            "attorney_fees": str(attorney_fees),
            "total_judgment": str(total),
            "is_sum_certain": is_sum_certain,
            "entry_method": "clerk" if is_sum_certain else "court hearing",
            "legal_basis": (
                "MCR 2.603(B)(1)(b)" if is_sum_certain
                else "MCR 2.603(B)(2)"
            ),
        }

    def prepare_affidavit(
        self,
        request: DefaultRequest,
    ) -> Dict[str, Any]:
        """Prepare the affidavit in support of entry of default.

        MCR 2.603(A)(1) requires an affidavit showing:
        - Service was made
        - Time to answer expired
        - Defendant has not answered or appeared
        - Military status
        """
        return {
            "document": "Affidavit in Support of Entry of Default",
            "case_number": request.case_number,
            "court": request.court,
            "plaintiff": _PLAINTIFF,
            "defendant": request.defendant_name,
            "affidavit_points": [
                f"1. The defendant, {request.defendant_name}, was served with the "
                f"summons and complaint on {request.service_date} via "
                f"{request.service_method} service.",
                f"2. The deadline for filing an answer or responsive pleading was "
                f"{request.answer_deadline}.",
                "3. To date, the defendant has not filed an answer, responsive "
                "pleading, or otherwise appeared in this action.",
                "4. I have verified the defendant's military status as required "
                "by 50 USC § 3931, and the defendant is not on active military duty "
                "(or military status is unknown).",
                "5. I respectfully request that the clerk enter a default against "
                f"the defendant pursuant to MCR 2.603(A).",
            ],
            "attachments": [
                "Proof of service",
                "Affidavit of non-military service",
                "Proposed entry of default",
            ],
            "legal_basis": "MCR 2.603(A)(1)",
        }

    def file_request(
        self, request: DefaultRequest,
    ) -> Dict[str, Any]:
        """Generate filing package for entry of default."""
        eligibility = self.verify_eligibility(request)

        return {
            "request_id": request.request_id,
            "is_eligible": eligibility["is_eligible"],
            "eligibility_issues": eligibility["issues"],
            "filing_documents": [
                {
                    "document": "Request for Entry of Default",
                    "form": "No specific SCAO form — local form or motion",
                    "mcr": "MCR 2.603(A)",
                },
                {
                    "document": "Affidavit of Proper Service",
                    "form": "MC 303 (Proof of Service)",
                    "mcr": "MCR 2.104",
                },
                {
                    "document": "Affidavit of Non-Military Service",
                    "form": "No SCAO form — prepare per 50 USC § 3931",
                    "mcr": "MCR 2.603(A)(1)",
                },
                {
                    "document": "Proposed Entry of Default",
                    "form": "No specific SCAO form — prepare per local rules",
                    "mcr": "MCR 2.603(A)",
                },
            ],
            "fee": "Varies by court — check local fee schedule",
            "legal_basis": "MCR 2.603(A); 50 USC § 3931",
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "DefaultEntryProcessor",
            "total_processed": len(self._processed),
            "eligible_count": sum(1 for p in self._processed if p.get("is_eligible")),
        }


# ---------------------------------------------------------------------------
# GoodCauseAnalyzer
# ---------------------------------------------------------------------------


class GoodCauseAnalyzer:
    """Analyze good cause for setting aside default.

    Applies the Shawl v Spence three-factor test:
    (1) Whether the party has a meritorious defense
    (2) Whether the party has shown good cause for failure to respond
    (3) Whether the opposing party would be unfairly prejudiced
    """

    def __init__(self) -> None:
        self._analyses: List[GoodCauseResult] = []

    def analyze_good_cause(
        self,
        factors: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Perform the three-factor Shawl v Spence analysis.

        Parameters
        ----------
        factors : dict with keys 'meritorious_defense', 'good_cause', 'no_prejudice'
            Each key maps to a dict with 'present' (bool), 'evidence' (list[str]),
            and optionally 'weight' (int 1-10).
        """
        factor_data = factors or {}
        scored_factors: Dict[str, Dict[str, Any]] = {}
        total_score = 0
        strengths: List[str] = []
        weaknesses: List[str] = []

        # Factor 1: Meritorious defense
        f1 = factor_data.get("meritorious_defense", {})
        f1_present = f1.get("present", False)
        f1_evidence = f1.get("evidence", [])
        f1_weight = f1.get("weight", 5)
        f1_score = f1_weight * 4 if f1_present else 0

        scored_factors["meritorious_defense"] = {
            "factor": "Whether the party has a meritorious defense",
            "present": f1_present,
            "evidence": f1_evidence,
            "score": f1_score,
            "max_score": 40,
            "legal_test": "Must show defense is not frivolous — Shawl v Spence",
        }
        if f1_present:
            strengths.append("Meritorious defense identified")
        else:
            weaknesses.append("No meritorious defense demonstrated")
        total_score += f1_score

        # Factor 2: Good cause
        f2 = factor_data.get("good_cause", {})
        f2_present = f2.get("present", False)
        f2_evidence = f2.get("evidence", [])
        f2_weight = f2.get("weight", 5)
        f2_score = f2_weight * 4 if f2_present else 0

        scored_factors["good_cause"] = {
            "factor": "Whether the party has shown good cause",
            "present": f2_present,
            "evidence": f2_evidence,
            "score": f2_score,
            "max_score": 40,
            "legal_test": (
                "Good cause = more than mere negligence; excusable neglect, "
                "mistake, or other justifiable reason — Shawl v Spence"
            ),
        }
        if f2_present:
            strengths.append("Good cause for delay demonstrated")
        else:
            weaknesses.append("No good cause shown for failure to respond")
        total_score += f2_score

        # Factor 3: No prejudice
        f3 = factor_data.get("no_prejudice", {})
        f3_present = f3.get("present", True)  # default: no prejudice
        f3_evidence = f3.get("evidence", [])
        f3_weight = f3.get("weight", 5)
        f3_score = f3_weight * 2 if f3_present else 0

        scored_factors["no_prejudice"] = {
            "factor": "Whether opposing party would be prejudiced",
            "present": f3_present,
            "evidence": f3_evidence,
            "score": f3_score,
            "max_score": 20,
            "legal_test": (
                "Delay alone is insufficient prejudice; must show "
                "actual harm such as lost evidence or witnesses — Shawl v Spence"
            ),
        }
        if f3_present:
            strengths.append("No prejudice to opposing party")
        else:
            weaknesses.append("Opposing party would be prejudiced by setting aside default")
        total_score += f3_score

        # Recommendation
        if total_score >= 70:
            recommendation = "Strong basis to set aside default — all factors favor relief"
        elif total_score >= 40:
            recommendation = "Moderate basis — some factors support relief, pursue cautiously"
        else:
            recommendation = "Weak basis — setting aside default unlikely without additional showing"

        result = GoodCauseResult(
            factors=scored_factors,
            overall_score=total_score,
            recommendation=recommendation,
            legal_basis="Shawl v Spence, 100 Mich App 380 (1980); MCR 2.603(D)(1)",
            strengths=strengths,
            weaknesses=weaknesses,
        )
        self._analyses.append(result)

        return result.to_dict()

    def check_meritorious_defense(
        self, defenses: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Evaluate whether claimed defenses are meritorious."""
        defense_list = defenses or []
        evaluated: List[Dict[str, Any]] = []

        recognized_defenses = {
            "statute_of_limitations": {
                "strength": "strong",
                "legal_basis": "MCL 600.5801 et seq.",
                "note": "If time-barred, default judgment may be vacated",
            },
            "lack_of_jurisdiction": {
                "strength": "strong",
                "legal_basis": "MCR 2.612(C)(1)(d)",
                "note": "Jurisdictional defects render judgment void",
            },
            "failure_to_state_claim": {
                "strength": "moderate",
                "legal_basis": "MCR 2.116(C)(8)",
                "note": "If complaint fails to state a claim, defense is meritorious",
            },
            "improper_service": {
                "strength": "strong",
                "legal_basis": "MCR 2.105; MCR 2.612(C)(1)(d)",
                "note": "Improper service voids the judgment",
            },
            "payment": {
                "strength": "strong",
                "legal_basis": "Common law defense",
                "note": "Evidence of payment extinguishes the claim",
            },
            "fraud": {
                "strength": "moderate",
                "legal_basis": "MCR 2.612(C)(1)(c)",
                "note": "Fraud must be proved by clear and convincing evidence",
            },
        }

        for defense in defense_list:
            defense_key = defense.lower().replace(" ", "_")
            info = recognized_defenses.get(defense_key, {})
            evaluated.append({
                "defense": defense,
                "is_recognized": bool(info),
                "strength": info.get("strength", "unknown"),
                "legal_basis": info.get("legal_basis", ""),
                "note": info.get("note", "Evaluate on the merits"),
            })

        meritorious = [e for e in evaluated if e.get("strength") in ("strong", "moderate")]
        return {
            "defenses_evaluated": len(evaluated),
            "meritorious_count": len(meritorious),
            "evaluations": evaluated,
            "has_meritorious_defense": len(meritorious) > 0,
        }

    def check_diligence(
        self,
        days_since_default: int = 0,
        reason_for_delay: str = "",
    ) -> Dict[str, Any]:
        """Evaluate diligence in seeking to set aside default."""
        is_prompt = days_since_default <= 30
        has_reason = bool(reason_for_delay)

        excusable_reasons = [
            "excusable_neglect",
            "medical_emergency",
            "never_received_service",
            "incorrect_address",
            "mental_incapacity",
            "military_service",
        ]

        reason_key = reason_for_delay.lower().replace(" ", "_")
        is_excusable = reason_key in excusable_reasons

        diligence_score = 0
        if is_prompt:
            diligence_score += 50
        if has_reason:
            diligence_score += 25
        if is_excusable:
            diligence_score += 25

        return {
            "days_since_default": days_since_default,
            "is_prompt": is_prompt,
            "reason_for_delay": reason_for_delay,
            "is_excusable": is_excusable,
            "diligence_score": diligence_score,
            "note": (
                "Prompt action after learning of default strongly favors relief"
                if is_prompt
                else "Significant delay weakens good-cause showing"
            ),
            "legal_basis": "Shawl v Spence; MCR 2.603(D)(1)",
        }

    def check_prejudice(
        self,
        days_since_default: int = 0,
        evidence_lost: bool = False,
        witnesses_unavailable: bool = False,
    ) -> Dict[str, Any]:
        """Evaluate whether opposing party would be prejudiced."""
        prejudice_factors: List[str] = []

        if evidence_lost:
            prejudice_factors.append("Evidence has been lost or destroyed")
        if witnesses_unavailable:
            prejudice_factors.append("Key witnesses are no longer available")
        if days_since_default > 365:
            prejudice_factors.append("Significant delay (>1 year) may prejudice opposing party")

        is_prejudiced = len(prejudice_factors) > 0

        return {
            "is_prejudiced": is_prejudiced,
            "prejudice_factors": prejudice_factors,
            "days_since_default": days_since_default,
            "note": (
                "Mere delay without actual prejudice is insufficient — "
                "Shawl v Spence"
            ),
            "legal_basis": "Shawl v Spence, 100 Mich App 380 (1980)",
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "GoodCauseAnalyzer",
            "total_analyses": len(self._analyses),
            "avg_score": (
                sum(a.overall_score for a in self._analyses) / len(self._analyses)
                if self._analyses else 0
            ),
        }


# ---------------------------------------------------------------------------
# VoidJudgmentChecker
# ---------------------------------------------------------------------------


class VoidJudgmentChecker:
    """Analyze whether a default judgment is void.

    MCR 2.612(C)(1)(d) provides relief from void judgments with
    NO time limit — a void judgment may be attacked at any time.
    """

    def __init__(self) -> None:
        self._analyses: List[VoidJudgmentResult] = []

    def check_jurisdiction(
        self,
        personal_jurisdiction: bool = True,
        subject_matter_jurisdiction: bool = True,
    ) -> Dict[str, Any]:
        """Check whether the court had jurisdiction.

        Lack of either personal or subject-matter jurisdiction
        renders the judgment void.
        """
        is_void = not personal_jurisdiction or not subject_matter_jurisdiction
        bases: List[str] = []

        if not personal_jurisdiction:
            bases.append(
                "Lack of personal jurisdiction — court had no authority "
                "over the defendant"
            )
        if not subject_matter_jurisdiction:
            bases.append(
                "Lack of subject-matter jurisdiction — court had no authority "
                "over this type of case"
            )

        return {
            "personal_jurisdiction": personal_jurisdiction,
            "subject_matter_jurisdiction": subject_matter_jurisdiction,
            "is_void": is_void,
            "void_bases": bases,
            "legal_basis": "MCR 2.612(C)(1)(d); US Const Amend XIV",
            "time_limit": "None — void judgments may be attacked at any time",
        }

    def check_service_defects(
        self,
        service_method: str = "",
        defects: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Check whether service defects render the judgment void.

        Fundamental service defects deprive the court of personal
        jurisdiction, making the judgment void.
        """
        defect_list = defects or []
        fundamental_defects: List[str] = []
        procedural_defects: List[str] = []

        fundamental_keywords = [
            "never served", "wrong person", "no jurisdiction",
            "no proof of service", "served after default",
        ]

        for defect in defect_list:
            defect_lower = defect.lower()
            if any(kw in defect_lower for kw in fundamental_keywords):
                fundamental_defects.append(defect)
            else:
                procedural_defects.append(defect)

        is_void = len(fundamental_defects) > 0

        return {
            "service_method": service_method,
            "total_defects": len(defect_list),
            "fundamental_defects": fundamental_defects,
            "procedural_defects": procedural_defects,
            "is_void": is_void,
            "legal_basis": "MCR 2.105; MCR 2.612(C)(1)(d)",
            "note": (
                "Fundamental service defects deprive the court of personal "
                "jurisdiction, rendering any judgment void"
                if is_void
                else "Procedural defects may support setting aside but do not render void"
            ),
        }

    def check_due_process(
        self,
        notice_given: bool = True,
        opportunity_to_respond: bool = True,
        hearing_held: bool = True,
    ) -> Dict[str, Any]:
        """Check for due process violations.

        The Fourteenth Amendment guarantees notice and an opportunity
        to be heard before deprivation of property.
        """
        violations: List[str] = []

        if not notice_given:
            violations.append("No notice given — fundamental due process violation")
        if not opportunity_to_respond:
            violations.append("No opportunity to respond — due process violation")
        if not hearing_held:
            violations.append(
                "No hearing held on damages — MCR 2.603(B)(2) may require hearing"
            )

        is_void = not notice_given or not opportunity_to_respond

        return {
            "notice_given": notice_given,
            "opportunity_to_respond": opportunity_to_respond,
            "hearing_held": hearing_held,
            "violations": violations,
            "is_void": is_void,
            "legal_basis": "US Const Amend XIV; Mich Const 1963, art I, § 17",
            "time_limit": "None for void judgments — MCR 2.612(C)(1)(d)",
        }

    def check_mcr_2_612(
        self,
        grounds: Optional[List[str]] = None,
        days_since_judgment: int = 0,
    ) -> Dict[str, Any]:
        """Analyze relief under MCR 2.612(C)(1) — all grounds.

        Grounds:
        (a) Mistake, inadvertence, surprise, or excusable neglect
        (b) Newly discovered evidence
        (c) Fraud, misrepresentation, or misconduct
        (d) Judgment is void
        (e) Judgment has been satisfied, released, or discharged
        (f) Any other reason justifying relief
        """
        ground_list = grounds or []
        evaluated: List[Dict[str, Any]] = []

        ground_details = {
            "mistake": {
                "subsection": "(a)",
                "time_limit_days": _MCR_2612_C1_DEADLINE_DAYS,
                "description": "Mistake, inadvertence, surprise, or excusable neglect",
            },
            "new_evidence": {
                "subsection": "(b)",
                "time_limit_days": _MCR_2612_C1_DEADLINE_DAYS,
                "description": "Newly discovered evidence",
            },
            "fraud": {
                "subsection": "(c)",
                "time_limit_days": _MCR_2612_C1_DEADLINE_DAYS,
                "description": "Fraud, misrepresentation, or misconduct",
            },
            "void": {
                "subsection": "(d)",
                "time_limit_days": None,  # no limit
                "description": "Judgment is void",
            },
            "satisfied": {
                "subsection": "(e)",
                "time_limit_days": None,
                "description": "Judgment satisfied, released, or discharged",
            },
            "other": {
                "subsection": "(f)",
                "time_limit_days": _MCR_2612_C1_DEADLINE_DAYS,
                "description": "Any other reason justifying relief",
            },
        }

        for ground in ground_list:
            ground_key = ground.lower().replace(" ", "_")
            info = ground_details.get(ground_key, {})
            time_limit = info.get("time_limit_days")
            is_timely = time_limit is None or days_since_judgment <= time_limit

            evaluated.append({
                "ground": ground,
                "subsection": info.get("subsection", "unknown"),
                "description": info.get("description", ""),
                "time_limit_days": time_limit,
                "is_timely": is_timely,
                "days_since_judgment": days_since_judgment,
            })

        viable = [e for e in evaluated if e.get("is_timely")]
        return {
            "grounds_evaluated": len(evaluated),
            "viable_grounds": len(viable),
            "evaluations": evaluated,
            "legal_basis": "MCR 2.612(C)(1)",
            "general_deadline": f"{_MCR_2612_C1_DEADLINE_DAYS} days for (a)-(c), (f)",
            "void_judgment_note": "No time limit for void judgments — (d)",
        }

    def full_analysis(
        self,
        personal_jurisdiction: bool = True,
        subject_matter_jurisdiction: bool = True,
        service_defects: Optional[List[str]] = None,
        notice_given: bool = True,
        opportunity_to_respond: bool = True,
    ) -> VoidJudgmentResult:
        """Run full void-judgment analysis combining all checks."""
        jurisdiction = self.check_jurisdiction(
            personal_jurisdiction, subject_matter_jurisdiction,
        )
        service = self.check_service_defects(defects=service_defects)
        due_process = self.check_due_process(
            notice_given, opportunity_to_respond,
        )

        is_void = (
            jurisdiction["is_void"]
            or service["is_void"]
            or due_process["is_void"]
        )

        void_bases: List[str] = []
        void_bases.extend(jurisdiction.get("void_bases", []))
        if service["is_void"]:
            void_bases.append("Service defects deprived court of jurisdiction")
        void_bases.extend(
            v for v in due_process.get("violations", [])
            if "fundamental" in v.lower() or "no notice" in v.lower()
        )

        evidence_needed: List[str] = []
        if not personal_jurisdiction:
            evidence_needed.append("Evidence showing lack of minimum contacts with Michigan")
        if service["is_void"]:
            evidence_needed.append("Proof of service defects (affidavit, return receipt)")
        if not notice_given:
            evidence_needed.append("Evidence that no notice was provided")

        result = VoidJudgmentResult(
            is_void=is_void,
            void_bases=void_bases,
            evidence_needed=evidence_needed,
            time_limit="None — MCR 2.612(C)(1)(d)",
            legal_basis="MCR 2.612(C)(1)(d); US Const Amend XIV",
            recommendation=(
                "Strong basis for relief — judgment is void and may be attacked at any time"
                if is_void
                else "Judgment does not appear void — consider other MCR 2.612 grounds"
            ),
        )
        self._analyses.append(result)
        return result

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "VoidJudgmentChecker",
            "total_analyses": len(self._analyses),
            "void_count": sum(1 for a in self._analyses if a.is_void),
        }


# ---------------------------------------------------------------------------
# DefaultJudgmentEngine  (main orchestrator)
# ---------------------------------------------------------------------------


class DefaultJudgmentEngine:
    """Top-level orchestrator for default judgment proceedings.

    Combines :class:`ServiceVerifier`, :class:`DefaultEntryProcessor`,
    :class:`GoodCauseAnalyzer`, and :class:`VoidJudgmentChecker` into
    a unified system for pursuing and defending against default
    judgments in Michigan courts.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or _DB_PATH
        self._service_verifier = ServiceVerifier()
        self._entry_processor = DefaultEntryProcessor()
        self._good_cause_analyzer = GoodCauseAnalyzer()
        self._void_checker = VoidJudgmentChecker()
        self._requests: Dict[str, DefaultRequest] = {}

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

    # -- pursue default --

    def pursue_default(
        self,
        case_number: str = "",
        defendant_name: str = "",
        service_date: str = "",
        service_method: str = "personal",
        judgment_amount: Decimal = Decimal("0.00"),
        military_status_checked: bool = False,
        military_affidavit_filed: bool = False,
    ) -> DefaultRequest:
        """Initiate pursuit of a default judgment.

        Creates a DefaultRequest and verifies initial eligibility.
        """
        method_info = _SERVICE_METHODS.get(service_method, {})
        answer_days = method_info.get("answer_days", _ANSWER_DEADLINE_PERSONAL)

        try:
            svc_date = date.fromisoformat(service_date)
            answer_deadline = (svc_date + timedelta(days=answer_days)).isoformat()
        except ValueError:
            answer_deadline = ""

        request = DefaultRequest(
            case_number=case_number or LANE_CASES["B"],
            defendant_name=defendant_name or _DEFENDANT,
            default_type=DefaultType.ENTRY_OF_DEFAULT,
            service_date=service_date,
            service_method=service_method,
            court=_COURT,
            judge=_JUDGE,
            answer_deadline=answer_deadline,
            judgment_amount=judgment_amount,
            military_status_checked=military_status_checked,
            military_affidavit_filed=military_affidavit_filed,
        )
        self._requests[request.request_id] = request

        logger.info(
            "Pursuing default against %s in %s (served %s via %s)",
            defendant_name,
            case_number,
            service_date,
            service_method,
        )
        return request

    def defend_against_default(
        self,
        request_id: str,
        defenses: Optional[List[str]] = None,
        reason_for_delay: str = "",
        days_since_default: int = 0,
    ) -> Dict[str, Any]:
        """Analyze options for defending against a default.

        Evaluates meritorious defenses, good cause, and prejudice
        to determine the strength of a motion to set aside.
        """
        request = self._requests.get(request_id)
        if not request:
            return {"error": f"Request {request_id} not found"}

        # Check meritorious defenses
        defense_check = self._good_cause_analyzer.check_meritorious_defense(defenses)

        # Check diligence
        diligence = self._good_cause_analyzer.check_diligence(
            days_since_default, reason_for_delay,
        )

        # Check prejudice
        prejudice = self._good_cause_analyzer.check_prejudice(
            days_since_default=days_since_default,
        )

        # Check if void
        void_check = self._void_checker.check_jurisdiction()

        return {
            "request_id": request_id,
            "defense_analysis": defense_check,
            "diligence_analysis": diligence,
            "prejudice_analysis": prejudice,
            "void_judgment_check": void_check,
            "recommended_approach": (
                "void_judgment_motion" if void_check["is_void"]
                else "set_aside_motion" if defense_check["has_meritorious_defense"]
                else "evaluate_further"
            ),
            "legal_basis": "MCR 2.603(D)(1); MCR 2.612(C)(1)",
        }

    def move_to_set_aside(
        self,
        request_id: str,
        factors: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Prepare a motion to set aside default.

        Applies the Shawl v Spence three-factor test.
        """
        request = self._requests.get(request_id)
        if not request:
            return {"error": f"Request {request_id} not found"}

        analysis = self._good_cause_analyzer.analyze_good_cause(factors)

        motion: Dict[str, Any] = {
            "document": "Motion to Set Aside Entry of Default",
            "case_number": request.case_number,
            "court": request.court,
            "defendant": request.defendant_name,
            "analysis": analysis,
            "motion_elements": [
                {
                    "section": "Introduction",
                    "content": (
                        f"Defendant {request.defendant_name} respectfully moves "
                        "this Court for an order setting aside the entry of default "
                        "pursuant to MCR 2.603(D)(1)."
                    ),
                },
                {
                    "section": "Statement of Facts",
                    "content": (
                        f"Service was made on {request.service_date} via "
                        f"{request.service_method} service. The entry of default "
                        f"was entered on {request.default_date or 'date to be determined'}."
                    ),
                },
                {
                    "section": "Legal Standard",
                    "content": (
                        "Under MCR 2.603(D)(1), the court may set aside an entry of "
                        "default for good cause shown. The three-factor test from "
                        "Shawl v Spence, 100 Mich App 380 (1980), requires: "
                        "(1) meritorious defense, (2) good cause, and (3) no prejudice."
                    ),
                },
                {
                    "section": "Argument",
                    "content": (
                        "The Shawl v Spence factors all favor setting aside the default."
                    ),
                },
                {
                    "section": "Relief Requested",
                    "content": (
                        "For the reasons stated above, Defendant requests that this "
                        "Court set aside the entry of default and allow Defendant to "
                        "file a responsive pleading within 14 days."
                    ),
                },
            ],
            "attachments": [
                "Proposed Answer / Responsive Pleading",
                "Affidavit in Support of Motion",
                "Brief in Support of Motion",
            ],
            "legal_basis": "MCR 2.603(D)(1); Shawl v Spence, 100 Mich App 380 (1980)",
        }

        return motion

    def calculate_damages(
        self,
        request_id: str,
        principal: Decimal = Decimal("0.00"),
        interest_rate: Decimal = Decimal("0.05"),
        from_date: str = "",
        costs: Decimal = Decimal("0.00"),
    ) -> Dict[str, Any]:
        """Calculate damages for a default judgment request."""
        request = self._requests.get(request_id)
        if not request:
            return {"error": f"Request {request_id} not found"}

        return self._entry_processor.calculate_damages(
            principal=principal or request.judgment_amount,
            interest_rate=interest_rate,
            from_date=from_date or request.service_date,
            costs=costs,
        )

    def get_request(self, request_id: str) -> Optional[DefaultRequest]:
        """Retrieve a default request by ID."""
        return self._requests.get(request_id)

    def list_requests(
        self, status: Optional[DefaultStatus] = None,
    ) -> List[DefaultRequest]:
        """List all requests, optionally filtered by status."""
        if status:
            return [r for r in self._requests.values() if r.status == status]
        return list(self._requests.values())

    def update_status(
        self, request_id: str, new_status: DefaultStatus,
    ) -> Optional[DefaultRequest]:
        """Update the status of a default request."""
        request = self._requests.get(request_id)
        if request:
            old_status = request.status
            request.status = new_status
            logger.info(
                "Default %s: %s → %s",
                request_id, old_status.value, new_status.value,
            )
        return request

    def get_stats(self) -> Dict[str, Any]:
        """Return runtime statistics."""
        by_type: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        for r in self._requests.values():
            by_type[r.default_type.value] = by_type.get(r.default_type.value, 0) + 1
            by_status[r.status.value] = by_status.get(r.status.value, 0) + 1

        return {
            "module": "default_judgment_engine",
            "total_requests": len(self._requests),
            "by_type": by_type,
            "by_status": by_status,
            "db_path": str(self._db_path),
            "service_verifier": self._service_verifier.get_stats(),
            "entry_processor": self._entry_processor.get_stats(),
            "good_cause_analyzer": self._good_cause_analyzer.get_stats(),
            "void_checker": self._void_checker.get_stats(),
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
    print("  Default Judgment Engine — LitigationOS")
    print("=" * 60)
    print()

    engine = DefaultJudgmentEngine()

    # Pursue a default
    req = engine.pursue_default(
        case_number=LANE_CASES["B"],
        defendant_name=_DEFENDANT,
        service_date="2025-03-15",
        service_method="personal",
        judgment_amount=Decimal("25000.00"),
        military_status_checked=True,
        military_affidavit_filed=True,
    )
    print(f"Created default request: {req.request_id}")
    print(f"  Case: {req.case_number}")
    print(f"  Defendant: {req.defendant_name}")
    print(f"  Answer deadline: {req.answer_deadline}")
    print()

    # Calculate damages
    damages = engine.calculate_damages(
        request_id=req.request_id,
        principal=Decimal("25000.00"),
        interest_rate=Decimal("0.05"),
        from_date="2025-01-01",
    )
    print("Damages Calculation:")
    for k, v in damages.items():
        print(f"  {k}: {v}")
    print()

    # Good cause analysis
    analyzer = GoodCauseAnalyzer()
    result = analyzer.analyze_good_cause({
        "meritorious_defense": {
            "present": True,
            "evidence": ["Statute of limitations expired"],
            "weight": 7,
        },
        "good_cause": {
            "present": True,
            "evidence": ["Never received service — was at different address"],
            "weight": 6,
        },
        "no_prejudice": {
            "present": True,
            "evidence": ["All evidence still available, no witnesses lost"],
            "weight": 8,
        },
    })
    print(f"Good Cause Score: {result['overall_score']}/100")
    print(f"Recommendation: {result['recommendation']}")
    print()

    # Void judgment check
    checker = VoidJudgmentChecker()
    void_result = checker.full_analysis(
        personal_jurisdiction=False,
        service_defects=["never served — defendant was out of state"],
    )
    print(f"Void Judgment: {void_result.is_void}")
    for basis in void_result.void_bases:
        print(f"  • {basis}")
    print()

    # Stats
    stats = engine.get_stats()
    print("Stats:")
    for k, v in stats.items():
        print(f"  {k}: {v}")
