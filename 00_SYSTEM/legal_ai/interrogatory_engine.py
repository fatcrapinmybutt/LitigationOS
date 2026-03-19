# -*- coding: utf-8 -*-
"""
Interrogatory Engine — LitigationOS Legal AI Subsystem
========================================================
Written discovery via interrogatories under Michigan Court Rules.
Handles drafting, service, response tracking, objection generation,
response analysis, and motion-to-compel preparation per MCR 2.309,
MCR 2.313, and MCR 2.302(E).

Case Context
------------
    Plaintiff:  Andrew James Pigors (Pro Se)
    Defendant:  Emily A. Watson
    Child:      L.D.W. (per MCR 8.119(H)) — Male
    Judge:      Hon. Jenny L. McNeill — 14th Circuit Court
    Cases:      2024-001507-DC, 2025-002760-CZ, 2023-5907-PP, COA 366810

Michigan Rules & Statutes
-------------------------
    MCR 2.309(A)   – Interrogatories to parties
    MCR 2.309(A)(2)– Limit: 35 interrogatories including subparts (standard)
    MCR 2.309(B)   – Procedure for answering/objecting
    MCR 2.309(B)(2)– 28 days to respond after service
    MCR 2.302(E)   – Supplementation duty
    MCR 2.313      – Failure to provide discovery — sanctions / motion to compel
    MCR 2.313(A)   – Motion to compel
    MCR 2.313(B)   – Sanctions for failure to comply
    MCR 2.302(B)   – Scope of discovery
    MCR 2.302(C)   – Protective orders
    MCR 2.310      – Requests for production of documents

    Cabrera v Ekema, 265 Mich App 402 (2005):
      Discovery is to be liberally construed to further truthseeking.

    Domako v Rowe, 438 Mich 347 (1991):
      Evasive or incomplete answers treated as failure to answer.

Usage::

    from legal_ai.interrogatory_engine import InterrogatoryEngine

    engine = InterrogatoryEngine()
    rogs = engine.create_interrogatories(
        case_number="2024-001507-DC",
        case_type="custody",
    )
    engine.serve(rogs[0].number)

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

logger = logging.getLogger("legal_ai.interrogatory_engine")

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
# Michigan interrogatory constants
# ---------------------------------------------------------------------------
_STANDARD_LIMIT = 35       # MCR 2.309(A)(2) — including subparts
_LIMITED_LIMIT = 25         # Limited discovery track
_RESPONSE_DAYS = 28        # MCR 2.309(B)(2) — 28 days to respond
_SUPPLEMENTATION_DUTY = True  # MCR 2.302(E) — ongoing duty
_MOTION_TO_COMPEL_DAYS = 28   # Reasonable time to file after non-response
_MCR_2313_SANCTION_FEE = Decimal("0.00")  # Court-determined

_OBJECTION_BASES: Dict[str, str] = {
    "overbroad": "Objection: Interrogatory is overbroad and unduly burdensome",
    "vague": "Objection: Interrogatory is vague and ambiguous",
    "privilege": "Objection: Response calls for privileged information",
    "work_product": "Objection: Response calls for attorney work product",
    "relevance": "Objection: Interrogatory is not relevant to any claim or defense",
    "cumulative": "Objection: Information is cumulative and obtainable from other sources",
    "exceeds_limit": "Objection: Interrogatory exceeds the limit under MCR 2.309(A)(2)",
    "compound": "Objection: Interrogatory is compound and should be counted as multiple",
    "premature": "Objection: Discovery is premature — case not at issue",
    "harassment": "Objection: Interrogatory is designed to harass, not seek relevant information",
}

_AUTHORITY_REFS: Dict[str, str] = {
    "interrogatories": "MCR 2.309(A)",
    "limit": "MCR 2.309(A)(2)",
    "procedure": "MCR 2.309(B)",
    "response_time": "MCR 2.309(B)(2)",
    "supplementation": "MCR 2.302(E)",
    "motion_to_compel": "MCR 2.313(A)",
    "sanctions": "MCR 2.313(B)",
    "scope": "MCR 2.302(B)",
    "protective_orders": "MCR 2.302(C)",
    "cabrera": "Cabrera v Ekema, 265 Mich App 402 (2005)",
    "domako": "Domako v Rowe, 438 Mich 347 (1991)",
}

# ---------------------------------------------------------------------------
# Standard interrogatory templates by case type
# ---------------------------------------------------------------------------
_CUSTODY_INTERROGATORIES: List[Dict[str, str]] = [
    {
        "text": "State your full legal name, date of birth, current address, and all addresses at which you have resided during the past five (5) years.",
        "type": "identification",
        "target_info": "party identification",
    },
    {
        "text": "Identify all persons who currently reside in your household, including their names, ages, and relationship to you.",
        "type": "identification",
        "target_info": "household composition",
    },
    {
        "text": f"Describe in detail your current employment, including employer name, position, hours worked, and gross annual income.",
        "type": "standard",
        "target_info": "employment and income",
    },
    {
        "text": f"State all sources of income you have received in the past two (2) years, including employment, self-employment, government benefits, and any other sources.",
        "type": "standard",
        "target_info": "income sources",
    },
    {
        "text": f"Describe your proposed parenting time schedule for {_CHILD_INITIALS}, including weekdays, weekends, holidays, and summer vacation.",
        "type": "contention",
        "target_info": "parenting time proposal",
    },
    {
        "text": f"Identify all childcare providers who have cared for {_CHILD_INITIALS} during the past two (2) years, including names, addresses, and dates of service.",
        "type": "identification",
        "target_info": "childcare providers",
    },
    {
        "text": f"Describe any concerns you have regarding the other parent's ability to care for {_CHILD_INITIALS}, including specific incidents with dates and witnesses.",
        "type": "contention",
        "target_info": "parenting concerns",
    },
    {
        "text": "Identify all mental health professionals you have consulted in the past five (5) years, including names, dates, and reasons for treatment.",
        "type": "standard",
        "target_info": "mental health history",
    },
    {
        "text": "State whether you have ever been arrested, charged with, or convicted of any criminal offense, and if so, provide details.",
        "type": "standard",
        "target_info": "criminal history",
    },
    {
        "text": f"Identify all witnesses you intend to call at trial and state the subject matter of their expected testimony.",
        "type": "identification",
        "target_info": "witness identification",
    },
    {
        "text": "Describe all documents and tangible items you intend to offer as exhibits at trial.",
        "type": "identification",
        "target_info": "exhibit identification",
    },
    {
        "text": f"State whether you have ever used illegal drugs or abused alcohol, and if so, describe the circumstances, dates, and any treatment received.",
        "type": "standard",
        "target_info": "substance use history",
    },
    {
        "text": f"Describe your relationship with {_CHILD_INITIALS}, including the nature and frequency of your contact.",
        "type": "contention",
        "target_info": "parent-child relationship",
    },
    {
        "text": "Identify any expert witnesses you intend to call, their qualifications, and the subject matter of their expected testimony.",
        "type": "expert",
        "target_info": "expert witnesses",
    },
    {
        "text": f"State all facts supporting your position on each of the best-interest factors under MCL 722.23(a)-(l).",
        "type": "contention",
        "target_info": "best interest factors",
    },
]

_HOUSING_INTERROGATORIES: List[Dict[str, str]] = [
    {
        "text": "State your full legal name, current address, and all addresses at which you have resided during the past three (3) years.",
        "type": "identification",
        "target_info": "party identification",
    },
    {
        "text": "Identify all persons who own, manage, or have a financial interest in the property at issue.",
        "type": "identification",
        "target_info": "property ownership",
    },
    {
        "text": "Describe all maintenance requests or complaints you received regarding the property at issue during the past three (3) years.",
        "type": "standard",
        "target_info": "maintenance history",
    },
    {
        "text": "State all facts supporting your claim that the property complied with applicable housing codes.",
        "type": "contention",
        "target_info": "code compliance",
    },
    {
        "text": "Identify all inspections of the property conducted during the past three (3) years, including inspector name, date, and findings.",
        "type": "identification",
        "target_info": "inspection history",
    },
    {
        "text": "Describe all repairs, renovations, or improvements made to the property during the past three (3) years.",
        "type": "standard",
        "target_info": "repair history",
    },
    {
        "text": "State the total rent collected from the property during the past three (3) years.",
        "type": "standard",
        "target_info": "rental income",
    },
    {
        "text": "Identify all insurance policies covering the property, including carrier, policy number, and coverage amounts.",
        "type": "identification",
        "target_info": "insurance coverage",
    },
    {
        "text": "Describe any hazardous conditions that have existed on the property during the past three (3) years.",
        "type": "standard",
        "target_info": "hazardous conditions",
    },
    {
        "text": "Identify all documents supporting your defenses to the claims in this action.",
        "type": "identification",
        "target_info": "defense documents",
    },
]

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class InterrogatoryType(str, Enum):
    """Types of interrogatories under Michigan practice."""

    STANDARD = "standard"
    CONTENTION = "contention"
    IDENTIFICATION = "identification"
    EXPERT = "expert"
    SUPPLEMENTAL = "supplemental"

    @property
    def description(self) -> str:
        _descs = {
            "standard": "Standard factual interrogatory seeking specific information",
            "contention": "Contention interrogatory seeking facts supporting a claim or defense",
            "identification": "Identification interrogatory seeking names, addresses, documents",
            "expert": "Expert interrogatory seeking expert witness information",
            "supplemental": "Supplemental interrogatory updating prior responses per MCR 2.302(E)",
        }
        return _descs.get(self.value, "")


class InterrogatoryStatus(str, Enum):
    """Status progression of an interrogatory set."""

    DRAFTED = "drafted"
    SERVED = "served"
    RESPONSE_DUE = "response_due"
    ANSWERED = "answered"
    OBJECTED = "objected"
    OVERDUE = "overdue"
    MOTION_TO_COMPEL = "motion_to_compel"

    @property
    def is_terminal(self) -> bool:
        return self in (InterrogatoryStatus.ANSWERED,)

    @property
    def requires_action(self) -> bool:
        return self in (
            InterrogatoryStatus.OVERDUE,
            InterrogatoryStatus.OBJECTED,
            InterrogatoryStatus.MOTION_TO_COMPEL,
        )


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class Interrogatory:
    """A single interrogatory question."""

    number: int = 0
    text: str = ""
    interrogatory_type: InterrogatoryType = InterrogatoryType.STANDARD
    target_info: str = ""
    objection_basis: List[str] = field(default_factory=list)
    answer: str = ""
    status: InterrogatoryStatus = InterrogatoryStatus.DRAFTED
    subparts: int = 0
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "number": self.number,
            "text": self.text,
            "interrogatory_type": self.interrogatory_type.value,
            "target_info": self.target_info,
            "objection_basis": self.objection_basis,
            "answer": self.answer,
            "status": self.status.value,
            "subparts": self.subparts,
            "created_at": self.created_at,
        }


@dataclass
class InterrogatorySet:
    """A complete set of interrogatories served on a party."""

    set_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    case_number: str = ""
    propounding_party: str = ""
    responding_party: str = ""
    interrogatories: List[Interrogatory] = field(default_factory=list)
    service_date: str = ""
    response_deadline: str = ""
    status: InterrogatoryStatus = InterrogatoryStatus.DRAFTED
    set_number: int = 1
    is_supplemental: bool = False
    total_including_subparts: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "set_id": self.set_id,
            "case_number": self.case_number,
            "propounding_party": self.propounding_party,
            "responding_party": self.responding_party,
            "interrogatories": [i.to_dict() for i in self.interrogatories],
            "service_date": self.service_date,
            "response_deadline": self.response_deadline,
            "status": self.status.value,
            "set_number": self.set_number,
            "is_supplemental": self.is_supplemental,
            "total_including_subparts": self.total_including_subparts,
        }


@dataclass
class MotionToCompel:
    """A motion to compel discovery responses."""

    motion_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    set_id: str = ""
    case_number: str = ""
    deficient_interrogatories: List[int] = field(default_factory=list)
    grounds: List[str] = field(default_factory=list)
    sanctions_requested: bool = False
    good_faith_certification: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "motion_id": self.motion_id,
            "set_id": self.set_id,
            "case_number": self.case_number,
            "deficient_interrogatories": self.deficient_interrogatories,
            "grounds": self.grounds,
            "sanctions_requested": self.sanctions_requested,
            "good_faith_certification": self.good_faith_certification,
        }


# ---------------------------------------------------------------------------
# InterrogatoryDrafter
# ---------------------------------------------------------------------------


class InterrogatoryDrafter:
    """Draft interrogatories for Michigan litigation.

    MCR 2.309(A)(2) limits interrogatories to 35 including subparts
    for standard cases, 25 for limited-discovery track.
    """

    def __init__(self) -> None:
        self._drafted_sets: List[InterrogatorySet] = []

    def draft_standard_set(
        self,
        case_type: str = "custody",
        case_number: str = "",
        responding_party: str = "",
        limit: int = _STANDARD_LIMIT,
    ) -> List[Interrogatory]:
        """Draft a standard set of interrogatories based on case type.

        Returns a list of Interrogatory objects within the MCR limit.
        """
        case_num = case_number or LANE_CASES["A"]
        respondent = responding_party or _DEFENDANT

        templates = {
            "custody": _CUSTODY_INTERROGATORIES,
            "housing": _HOUSING_INTERROGATORIES,
        }
        raw = templates.get(case_type, _CUSTODY_INTERROGATORIES)

        interrogatories: List[Interrogatory] = []
        total_count = 0

        for i, tmpl in enumerate(raw, 1):
            if total_count >= limit:
                logger.warning(
                    "Reached %d-interrogatory limit (MCR 2.309(A)(2))",
                    limit,
                )
                break

            rog = Interrogatory(
                number=i,
                text=tmpl["text"],
                interrogatory_type=InterrogatoryType(tmpl.get("type", "standard")),
                target_info=tmpl.get("target_info", ""),
                subparts=0,
            )
            interrogatories.append(rog)
            total_count += 1 + rog.subparts

        iset = InterrogatorySet(
            case_number=case_num,
            propounding_party=_PLAINTIFF,
            responding_party=respondent,
            interrogatories=interrogatories,
            total_including_subparts=total_count,
        )
        self._drafted_sets.append(iset)

        logger.info(
            "Drafted %d interrogatories for %s (%s)",
            len(interrogatories), case_type, case_num,
        )
        return interrogatories

    def draft_contention_interrogatories(
        self,
        claims: List[str],
        defenses: Optional[List[str]] = None,
    ) -> List[Interrogatory]:
        """Draft contention interrogatories targeting specific claims."""
        defenses = defenses or []
        interrogatories: List[Interrogatory] = []
        number = 1

        for claim in claims:
            interrogatories.append(Interrogatory(
                number=number,
                text=(
                    f"State all facts supporting your contention that {claim}."
                ),
                interrogatory_type=InterrogatoryType.CONTENTION,
                target_info=f"contention: {claim}",
            ))
            number += 1

        for defense in defenses:
            interrogatories.append(Interrogatory(
                number=number,
                text=(
                    f"State all facts supporting your defense that {defense}."
                ),
                interrogatory_type=InterrogatoryType.CONTENTION,
                target_info=f"defense contention: {defense}",
            ))
            number += 1

        return interrogatories

    def draft_identification_requests(
        self,
        categories: Optional[List[str]] = None,
    ) -> List[Interrogatory]:
        """Draft identification interrogatories for witness/document ID."""
        cats = categories or [
            "fact witnesses",
            "expert witnesses",
            "documentary exhibits",
            "electronic communications",
        ]
        interrogatories: List[Interrogatory] = []

        for i, cat in enumerate(cats, 1):
            interrogatories.append(Interrogatory(
                number=i,
                text=(
                    f"Identify all {cat} relevant to the claims or defenses "
                    "in this action, including names, addresses, and a brief "
                    "description of expected testimony or content."
                ),
                interrogatory_type=InterrogatoryType.IDENTIFICATION,
                target_info=cat,
            ))

        return interrogatories

    def enforce_limits(
        self,
        interrogatories: List[Interrogatory],
        limit: int = _STANDARD_LIMIT,
    ) -> Dict[str, Any]:
        """Check whether a set of interrogatories exceeds the MCR limit."""
        total = sum(1 + i.subparts for i in interrogatories)
        exceeds = total > limit
        return {
            "total_including_subparts": total,
            "limit": limit,
            "exceeds_limit": exceeds,
            "overage": max(0, total - limit),
            "authority": _AUTHORITY_REFS["limit"],
            "recommendation": (
                f"Within the {limit}-interrogatory limit"
                if not exceeds
                else f"Exceeds limit by {total - limit} — reduce or seek leave of court"
            ),
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "InterrogatoryDrafter",
            "total_sets_drafted": len(self._drafted_sets),
        }


# ---------------------------------------------------------------------------
# ObjectionHandler
# ---------------------------------------------------------------------------


class ObjectionHandler:
    """Generate and analyze objections to interrogatories.

    Handles standard Michigan discovery objections including
    overbreadth, relevance, privilege, and burden.
    """

    def __init__(self) -> None:
        self._objections: List[Dict[str, Any]] = []

    def generate_objections(
        self,
        interrogatory: Interrogatory,
        grounds: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Generate objections to a specific interrogatory."""
        bases = grounds or []
        objections: List[Dict[str, Any]] = []

        for basis in bases:
            if basis in _OBJECTION_BASES:
                objections.append({
                    "interrogatory_number": interrogatory.number,
                    "basis": basis,
                    "objection_text": _OBJECTION_BASES[basis],
                    "authority": self._get_authority(basis),
                    "preserve_right": True,
                })

        self._objections.extend(objections)
        return objections

    def _get_authority(self, basis: str) -> str:
        """Return MCR authority for a given objection basis."""
        authorities = {
            "overbroad": "MCR 2.302(B); MCR 2.302(C)",
            "vague": "MCR 2.309(A)",
            "privilege": "MCR 2.302(B)(5); MRE 501",
            "work_product": "MCR 2.302(B)(3)",
            "relevance": "MCR 2.302(B)(1)",
            "cumulative": "MCR 2.302(B)(1)",
            "exceeds_limit": "MCR 2.309(A)(2)",
            "compound": "MCR 2.309(A)(2)",
            "premature": "MCR 2.301",
            "harassment": "MCR 2.302(C)",
        }
        return authorities.get(basis, "MCR 2.302")

    def check_overbroad(self, interrogatory: Interrogatory) -> Dict[str, Any]:
        """Analyze whether an interrogatory is overbroad."""
        text = interrogatory.text.lower()
        indicators = []

        if "all" in text and "ever" in text:
            indicators.append("Uses 'all' combined with 'ever' — unbounded time scope")
        if "any and all" in text:
            indicators.append("'Any and all' is inherently overbroad")
        if len(text) > 500:
            indicators.append("Interrogatory exceeds reasonable length")

        return {
            "interrogatory_number": interrogatory.number,
            "is_overbroad": len(indicators) > 0,
            "indicators": indicators,
            "authority": "MCR 2.302(B); MCR 2.302(C)",
        }

    def check_unduly_burdensome(
        self,
        interrogatory: Interrogatory,
        estimated_hours: Decimal = Decimal("0"),
    ) -> Dict[str, Any]:
        """Analyze whether an interrogatory is unduly burdensome."""
        is_burdensome = estimated_hours > Decimal("8")
        return {
            "interrogatory_number": interrogatory.number,
            "is_unduly_burdensome": is_burdensome,
            "estimated_hours": str(estimated_hours),
            "threshold_hours": "8",
            "authority": "MCR 2.302(C)",
            "recommendation": (
                "Consider motion for protective order under MCR 2.302(C)"
                if is_burdensome
                else "Burden appears proportional to needs of the case"
            ),
        }

    def check_privilege(
        self,
        interrogatory: Interrogatory,
        privilege_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Check whether response implicates privilege."""
        privs = privilege_types or []
        text = interrogatory.text.lower()
        detected: List[str] = []

        keywords = {
            "attorney_client": ["attorney", "lawyer", "counsel", "legal advice"],
            "work_product": ["preparation for trial", "litigation strategy"],
            "spousal": ["spouse", "marital communication"],
            "therapist_patient": ["therapist", "counselor", "mental health"],
        }

        for priv_type, kws in keywords.items():
            for kw in kws:
                if kw in text:
                    detected.append(priv_type)
                    break

        all_privs = list(set(privs + detected))
        return {
            "interrogatory_number": interrogatory.number,
            "privilege_implicated": len(all_privs) > 0,
            "privilege_types": all_privs,
            "authority": "MCR 2.302(B)(5); MRE 501",
        }

    def check_relevance(
        self,
        interrogatory: Interrogatory,
        claims_at_issue: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Analyze whether an interrogatory seeks relevant information."""
        claims = claims_at_issue or []
        text = interrogatory.text.lower()
        is_relevant = False

        for claim in claims:
            if any(word in text for word in claim.lower().split()):
                is_relevant = True
                break

        if not claims:
            is_relevant = True  # Cannot assess without knowing claims

        return {
            "interrogatory_number": interrogatory.number,
            "is_relevant": is_relevant,
            "claims_checked": claims,
            "authority": "MCR 2.302(B)(1)",
            "note": (
                "Discovery is to be liberally construed. "
                "Cabrera v Ekema, 265 Mich App 402 (2005)."
            ),
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "ObjectionHandler",
            "total_objections": len(self._objections),
        }


# ---------------------------------------------------------------------------
# ResponseDrafter
# ---------------------------------------------------------------------------


class ResponseDrafter:
    """Draft and manage interrogatory responses.

    MCR 2.309(B)(2) requires responses within 28 days of service.
    MCR 2.302(E) imposes a continuing duty to supplement.
    """

    def __init__(self) -> None:
        self._responses: List[Dict[str, Any]] = []

    def draft_response(
        self,
        interrogatory: Interrogatory,
        facts: List[str],
        objections: Optional[List[str]] = None,
    ) -> str:
        """Draft a response to a single interrogatory.

        If objections are present, state the objection first, then
        respond 'subject to and without waiving the objection.'
        """
        objs = objections or []
        parts: List[str] = []

        # State objections first
        for obj in objs:
            if obj in _OBJECTION_BASES:
                parts.append(f"OBJECTION: {_OBJECTION_BASES[obj]}")

        # Response with reservation if objections exist
        if objs and facts:
            parts.append(
                "Subject to and without waiving the foregoing objection(s), "
                f"{_PLAINTIFF} responds as follows:"
            )

        # Factual response
        if facts:
            for fact in facts:
                parts.append(fact)
        elif not objs:
            parts.append("Discovery and investigation are ongoing. "
                        "This response will be supplemented per MCR 2.302(E).")

        response_text = "\n\n".join(parts)
        self._responses.append({
            "interrogatory_number": interrogatory.number,
            "response": response_text,
            "has_objections": len(objs) > 0,
            "fact_count": len(facts),
        })

        return response_text

    def supplement_response(
        self,
        interrogatory: Interrogatory,
        new_facts: List[str],
        original_response: str = "",
    ) -> str:
        """Draft a supplemental response per MCR 2.302(E).

        Parties have a continuing duty to supplement interrogatory
        responses when new information becomes available.
        """
        supplemental = (
            f"SUPPLEMENTAL RESPONSE TO INTERROGATORY NO. {interrogatory.number}:\n\n"
            f"Pursuant to MCR 2.302(E), {_PLAINTIFF} supplements the prior response "
            "as follows:\n\n"
        )
        for fact in new_facts:
            supplemental += f"  {fact}\n"

        if original_response:
            supplemental += (
                f"\nThe original response is otherwise reaffirmed."
            )

        return supplemental

    def calculate_response_deadline(
        self,
        service_date: str,
        service_method: str = "personal",
    ) -> Dict[str, Any]:
        """Calculate the response deadline per MCR 2.309(B)(2)."""
        try:
            svc_date = date.fromisoformat(service_date)
            additional_days = 0
            if service_method == "mail":
                additional_days = 3  # MCR 2.107(C)(3) — 3 days added for mail
            elif service_method == "email":
                additional_days = 3

            deadline = svc_date + timedelta(days=_RESPONSE_DAYS + additional_days)
            return {
                "service_date": service_date,
                "service_method": service_method,
                "response_days": _RESPONSE_DAYS,
                "additional_days": additional_days,
                "total_days": _RESPONSE_DAYS + additional_days,
                "deadline": deadline.isoformat(),
                "authority": f"{_AUTHORITY_REFS['response_time']}",
            }
        except ValueError:
            return {
                "error": f"Invalid date: {service_date}",
                "authority": _AUTHORITY_REFS["response_time"],
            }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "ResponseDrafter",
            "total_responses": len(self._responses),
        }


# ---------------------------------------------------------------------------
# InterrogatoryAnalyzer
# ---------------------------------------------------------------------------


class InterrogatoryAnalyzer:
    """Analyze opposing party's interrogatory responses.

    Identifies evasive answers, incomplete responses, and grounds
    for a motion to compel under MCR 2.313.
    """

    def __init__(self) -> None:
        self._analyses: List[Dict[str, Any]] = []

    def analyze_opposing_responses(
        self,
        interrogatories: List[Interrogatory],
    ) -> Dict[str, Any]:
        """Analyze a set of responses for adequacy."""
        answered = 0
        objected = 0
        evasive = 0
        unanswered = 0

        issues: List[Dict[str, Any]] = []

        for rog in interrogatories:
            if rog.answer and not rog.objection_basis:
                answered += 1
            elif rog.objection_basis and not rog.answer:
                objected += 1
                issues.append({
                    "number": rog.number,
                    "issue": "Full objection with no response",
                    "objections": rog.objection_basis,
                })
            elif rog.answer and rog.objection_basis:
                answered += 1  # Answered subject to objection
            else:
                unanswered += 1
                issues.append({
                    "number": rog.number,
                    "issue": "No response provided",
                })

        result = {
            "total_interrogatories": len(interrogatories),
            "answered": answered,
            "objected_only": objected,
            "evasive": evasive,
            "unanswered": unanswered,
            "issues": issues,
            "adequacy_score": (
                int(answered / len(interrogatories) * 100) if interrogatories else 0
            ),
            "motion_to_compel_warranted": (objected + unanswered) > 0,
            "authority": _AUTHORITY_REFS["domako"],
        }
        self._analyses.append(result)
        return result

    def identify_evasive_answers(
        self,
        interrogatories: List[Interrogatory],
    ) -> List[Dict[str, Any]]:
        """Identify evasive or incomplete answers per Domako v Rowe.

        Domako: Evasive or incomplete answers are treated as a
        failure to answer for purposes of MCR 2.313.
        """
        evasive: List[Dict[str, Any]] = []
        evasion_indicators = [
            "i don't recall",
            "i don't remember",
            "to the best of my knowledge",
            "not applicable",
            "n/a",
            "see attached",
            "see prior response",
            "objection",
        ]

        for rog in interrogatories:
            if not rog.answer:
                continue
            answer_lower = rog.answer.lower().strip()
            found_indicators: List[str] = []

            for indicator in evasion_indicators:
                if indicator in answer_lower:
                    found_indicators.append(indicator)

            # Very short answers to complex questions
            if len(answer_lower) < 20 and rog.interrogatory_type == InterrogatoryType.CONTENTION:
                found_indicators.append("response too brief for contention interrogatory")

            if found_indicators:
                evasive.append({
                    "interrogatory_number": rog.number,
                    "answer": rog.answer,
                    "evasion_indicators": found_indicators,
                    "authority": "Domako v Rowe, 438 Mich 347 (1991)",
                    "remedy": "MCR 2.313(A) motion to compel",
                })

        return evasive

    def prepare_motion_to_compel(
        self,
        rog_set: InterrogatorySet,
        deficient_numbers: List[int],
        good_faith_effort: bool = True,
    ) -> MotionToCompel:
        """Prepare a motion to compel under MCR 2.313(A).

        MCR 2.313(A)(2)(b) requires certification that the movant
        has in good faith conferred or attempted to confer with the
        opposing party before filing.
        """
        grounds: List[str] = []
        for num in deficient_numbers:
            matching = [r for r in rog_set.interrogatories if r.number == num]
            if matching:
                rog = matching[0]
                if not rog.answer:
                    grounds.append(
                        f"Interrogatory No. {num}: No response provided"
                    )
                elif rog.objection_basis:
                    grounds.append(
                        f"Interrogatory No. {num}: Objection without merit — "
                        f"objection basis: {', '.join(rog.objection_basis)}"
                    )

        motion = MotionToCompel(
            set_id=rog_set.set_id,
            case_number=rog_set.case_number,
            deficient_interrogatories=deficient_numbers,
            grounds=grounds,
            sanctions_requested=True,
            good_faith_certification=good_faith_effort,
        )

        logger.info(
            "Prepared motion to compel for %d deficient interrogatories",
            len(deficient_numbers),
        )
        return motion

    def track_supplementation_duty(
        self,
        original_responses: List[Interrogatory],
        new_information_available: bool = False,
    ) -> Dict[str, Any]:
        """Track supplementation duty under MCR 2.302(E)."""
        needs_supplementation: List[int] = []
        if new_information_available:
            for rog in original_responses:
                if rog.answer:
                    needs_supplementation.append(rog.number)

        return {
            "total_responses": len(original_responses),
            "new_information_available": new_information_available,
            "needs_supplementation": needs_supplementation,
            "supplementation_count": len(needs_supplementation),
            "authority": _AUTHORITY_REFS["supplementation"],
            "duty": (
                "Supplementation required — MCR 2.302(E) imposes a continuing "
                "duty to supplement when new information is obtained"
                if needs_supplementation
                else "No supplementation currently required"
            ),
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "InterrogatoryAnalyzer",
            "total_analyses": len(self._analyses),
        }


# ---------------------------------------------------------------------------
# InterrogatoryEngine  (main orchestrator)
# ---------------------------------------------------------------------------


class InterrogatoryEngine:
    """Top-level orchestrator for interrogatory practice.

    Combines :class:`InterrogatoryDrafter`, :class:`ObjectionHandler`,
    :class:`ResponseDrafter`, and :class:`InterrogatoryAnalyzer` into a
    unified system for written discovery in Michigan courts.

    Michigan Authority:
        MCR 2.309, MCR 2.313, MCR 2.302(E)
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or _DB_PATH
        self._drafter = InterrogatoryDrafter()
        self._objection_handler = ObjectionHandler()
        self._response_drafter = ResponseDrafter()
        self._analyzer = InterrogatoryAnalyzer()
        self._sets: Dict[str, InterrogatorySet] = {}
        self._service_log: List[Dict[str, Any]] = []

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

    def create_interrogatories(
        self,
        case_number: str = "",
        case_type: str = "custody",
        responding_party: str = "",
        limit: int = _STANDARD_LIMIT,
    ) -> List[Interrogatory]:
        """Create a set of interrogatories for the case."""
        case_num = case_number or LANE_CASES["A"]
        respondent = responding_party or _DEFENDANT

        rogs = self._drafter.draft_standard_set(
            case_type=case_type,
            case_number=case_num,
            responding_party=respondent,
            limit=limit,
        )

        iset = InterrogatorySet(
            case_number=case_num,
            propounding_party=_PLAINTIFF,
            responding_party=respondent,
            interrogatories=rogs,
            total_including_subparts=sum(1 + r.subparts for r in rogs),
        )
        self._sets[iset.set_id] = iset

        logger.info(
            "Created %d interrogatories for %s (case %s, type %s)",
            len(rogs), respondent, case_num, case_type,
        )
        return rogs

    def serve(
        self,
        set_id: str,
        service_date: str = "",
        service_method: str = "personal",
    ) -> Dict[str, Any]:
        """Record service of interrogatories."""
        iset = self._sets.get(set_id)
        if not iset:
            return {"error": f"Set {set_id} not found"}

        svc_date = service_date or date.today().isoformat()
        deadline_info = self._response_drafter.calculate_response_deadline(
            svc_date, service_method,
        )

        iset.service_date = svc_date
        iset.response_deadline = deadline_info.get("deadline", "")
        iset.status = InterrogatoryStatus.SERVED

        for rog in iset.interrogatories:
            rog.status = InterrogatoryStatus.SERVED

        svc_record = {
            "set_id": set_id,
            "case_number": iset.case_number,
            "propounding_party": iset.propounding_party,
            "responding_party": iset.responding_party,
            "service_date": svc_date,
            "service_method": service_method,
            "response_deadline": iset.response_deadline,
            "interrogatory_count": len(iset.interrogatories),
            "status": "served",
        }
        self._service_log.append(svc_record)

        logger.info(
            "Served interrogatory set %s on %s (deadline: %s)",
            set_id, svc_date, iset.response_deadline,
        )
        return svc_record

    def track_responses(
        self,
        set_id: str,
        responses: Optional[Dict[int, str]] = None,
        objections: Optional[Dict[int, List[str]]] = None,
    ) -> Dict[str, Any]:
        """Track responses and objections received."""
        iset = self._sets.get(set_id)
        if not iset:
            return {"error": f"Set {set_id} not found"}

        resp = responses or {}
        objs = objections or {}
        updated = 0

        for rog in iset.interrogatories:
            if rog.number in resp:
                rog.answer = resp[rog.number]
                rog.status = InterrogatoryStatus.ANSWERED
                updated += 1
            if rog.number in objs:
                rog.objection_basis = objs[rog.number]
                if not rog.answer:
                    rog.status = InterrogatoryStatus.OBJECTED

        return {
            "set_id": set_id,
            "updated_count": updated,
            "total_interrogatories": len(iset.interrogatories),
            "answered": sum(1 for r in iset.interrogatories if r.answer),
            "objected": sum(1 for r in iset.interrogatories if r.objection_basis),
        }

    def analyze_answers(
        self,
        set_id: str,
    ) -> Dict[str, Any]:
        """Analyze the opposing party's responses."""
        iset = self._sets.get(set_id)
        if not iset:
            return {"error": f"Set {set_id} not found"}

        analysis = self._analyzer.analyze_opposing_responses(iset.interrogatories)
        evasive = self._analyzer.identify_evasive_answers(iset.interrogatories)

        return {
            "set_id": set_id,
            "analysis": analysis,
            "evasive_answers": evasive,
            "evasive_count": len(evasive),
        }

    def get_set(self, set_id: str) -> Optional[InterrogatorySet]:
        """Retrieve an interrogatory set by ID."""
        return self._sets.get(set_id)

    def list_sets(
        self,
        status: Optional[InterrogatoryStatus] = None,
    ) -> List[InterrogatorySet]:
        """List all interrogatory sets, optionally filtered."""
        if status:
            return [s for s in self._sets.values() if s.status == status]
        return list(self._sets.values())

    def get_stats(self) -> Dict[str, Any]:
        """Return runtime statistics."""
        by_status: Dict[str, int] = {}
        total_rogs = 0
        for s in self._sets.values():
            by_status[s.status.value] = by_status.get(s.status.value, 0) + 1
            total_rogs += len(s.interrogatories)

        return {
            "module": "interrogatory_engine",
            "total_sets": len(self._sets),
            "total_interrogatories": total_rogs,
            "total_service_events": len(self._service_log),
            "by_status": by_status,
            "db_path": str(self._db_path),
            "drafter": self._drafter.get_stats(),
            "objection_handler": self._objection_handler.get_stats(),
            "response_drafter": self._response_drafter.get_stats(),
            "analyzer": self._analyzer.get_stats(),
        }

    def reset(self) -> None:
        """Clear all loaded sets and logs."""
        self._sets.clear()
        self._service_log.clear()


# ---------------------------------------------------------------------------
# CLI demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sys.stdout = open(  # noqa: SIM115
        sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace"
    )
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print("=" * 60)
    print("  Interrogatory Engine — LitigationOS")
    print("=" * 60)
    print()

    engine = InterrogatoryEngine()

    # Create interrogatories
    rogs = engine.create_interrogatories(
        case_number=LANE_CASES["A"],
        case_type="custody",
    )
    print(f"Created {len(rogs)} interrogatories")
    for r in rogs[:3]:
        print(f"  #{r.number}: {r.text[:60]}...")
    print()

    # Check limits
    drafter = InterrogatoryDrafter()
    limits = drafter.enforce_limits(rogs)
    print(f"Limit check: {limits['total_including_subparts']}/{limits['limit']}")
    print(f"  Exceeds: {limits['exceeds_limit']}")
    print()

    # Analyze objections
    handler = ObjectionHandler()
    obj = handler.check_overbroad(rogs[0])
    print(f"Overbroad check on #{rogs[0].number}: {obj['is_overbroad']}")
    print()

    # Stats
    stats = engine.get_stats()
    print("Stats:")
    for k, v in stats.items():
        print(f"  {k}: {v}")
