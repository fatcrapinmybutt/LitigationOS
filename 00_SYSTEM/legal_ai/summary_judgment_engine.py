# -*- coding: utf-8 -*-
"""
Summary Judgment Engine — LitigationOS Legal AI Subsystem
===========================================================
Summary disposition motion practice under MCR 2.116.
Handles motion preparation, response drafting, burden-shifting
analysis, evidence organization, oral argument preparation,
and odds assessment for Michigan courts.

Case Context
------------
    Plaintiff:  Andrew James Pigors (Pro Se)
    Defendant:  Emily A. Watson
    Child:      L.D.W. (per MCR 8.119(H)) — Male
    Judge:      Hon. Jenny L. McNeill — 14th Circuit Court
    Cases:      2024-001507-DC, 2025-002760-CZ, 2023-5907-PP, COA 366810

Michigan Rules & Statutes
-------------------------
    MCR 2.116(C)(1)  – Lack of jurisdiction over subject matter
    MCR 2.116(C)(4)  – Prior pending action between same parties
    MCR 2.116(C)(5)  – Governmental immunity
    MCR 2.116(C)(7)  – Failure to state a claim (legal defense)
    MCR 2.116(C)(8)  – Affirmative defense established on face of pleadings
    MCR 2.116(C)(9)  – No genuine issue directed
    MCR 2.116(C)(10) – No genuine issue of material fact
    MCR 2.116(G)     – Affidavits, depositions, admissions supporting motion
    MCR 2.116(H)     – 21-day response period + 7-day reply
    MCR 2.116(I)     – Court discretion to order oral argument
    MCR 2.116(J)     – Partial summary disposition

    Maiden v Rozwood, 461 Mich 109 (1999):
      C(10) burden framework — movant must specifically identify the
      issues for which there is no genuine issue of material fact.
      If movant carries initial burden, nonmovant must come forward
      with specific facts showing a genuine issue for trial.

    Quinto v Cross & Peters, 451 Mich 358 (1996):
      C(10) affidavit requirements — affidavits must be based on
      personal knowledge and set forth specific facts admissible
      in evidence. Conclusory allegations are insufficient.

    Skinner v Square D Co, 445 Mich 153 (1994):
      Court must consider evidence in the light most favorable
      to the nonmoving party.

    Celotex Corp v Catrett, 477 US 317 (1986):
      Federal analog — burden of production (not persuasion)
      shifts to nonmovant after movant's prima facie showing.

Usage::

    from legal_ai.summary_judgment_engine import SummaryJudgmentEngine

    engine = SummaryJudgmentEngine()
    motion = engine.prepare_motion(
        grounds=["C10_NO_GENUINE_ISSUE"],
        claims_targeted=["negligent maintenance"],
    )
    odds = engine.analyze_odds(motion["motion_id"])

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

logger = logging.getLogger("legal_ai.summary_judgment_engine")

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
# Michigan summary disposition constants
# ---------------------------------------------------------------------------
_RESPONSE_PERIOD_DAYS = 21  # MCR 2.116(H) — 21 days to respond
_REPLY_PERIOD_DAYS = 7      # MCR 2.116(H) — 7 days to reply
_MAIL_ADDITIONAL_DAYS = 3   # MCR 2.107(C)(3)
_56F_CONTINUANCE_STANDARD = "specific reasons why opposing party cannot present essential facts"

# Grounds and their MCR references
_GROUNDS_INFO: Dict[str, Dict[str, str]] = {
    "C1_JURISDICTION": {
        "mcr": "MCR 2.116(C)(1)",
        "description": "The court lacks jurisdiction of the subject matter",
        "standard": "Legal determination — no genuine issue standard",
    },
    "C4_PRIOR_ACTION": {
        "mcr": "MCR 2.116(C)(4)",
        "description": "Another action has been initiated between the same parties involving the same claim",
        "standard": "Legal determination — same parties, same claims",
    },
    "C5_GOVERNMENTAL_IMMUNITY": {
        "mcr": "MCR 2.116(C)(5)",
        "description": "The party asserting the claim is not entitled to recovery because of immunity granted by law",
        "standard": "Legal determination — immunity as matter of law",
    },
    "C7_FAILURE_TO_STATE_CLAIM": {
        "mcr": "MCR 2.116(C)(7)",
        "description": "The claim is barred because of a legal defense (statute of limitations, immunity, etc.)",
        "standard": "Accept well-pleaded facts as true — legal sufficiency test",
    },
    "C8_AFFIRMATIVE_DEFENSE": {
        "mcr": "MCR 2.116(C)(8)",
        "description": "The opposing party has failed to state a claim on which relief can be granted",
        "standard": "Accept well-pleaded facts as true — legal sufficiency test",
    },
    "C9_NO_GENUINE_ISSUE_DIRECTED": {
        "mcr": "MCR 2.116(C)(9)",
        "description": "The opposing party has failed to state a valid defense to the claim and no material issue of fact exists",
        "standard": "Nonmovant has failed to allege facts that would constitute a defense",
    },
    "C10_NO_GENUINE_ISSUE": {
        "mcr": "MCR 2.116(C)(10)",
        "description": "There is no genuine issue as to any material fact, and the moving party is entitled to judgment as a matter of law",
        "standard": "Maiden v Rozwood burden-shifting framework",
    },
}

_AUTHORITY_REFS: Dict[str, str] = {
    "summary_disposition": "MCR 2.116",
    "grounds": "MCR 2.116(C)",
    "affidavits": "MCR 2.116(G)",
    "response_period": "MCR 2.116(H)",
    "oral_argument": "MCR 2.116(I)",
    "partial": "MCR 2.116(J)",
    "maiden": "Maiden v Rozwood, 461 Mich 109 (1999)",
    "quinto": "Quinto v Cross & Peters, 451 Mich 358 (1996)",
    "skinner": "Skinner v Square D Co, 445 Mich 153 (1994)",
    "celotex": "Celotex Corp v Catrett, 477 US 317 (1986)",
}


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class SJGrounds(str, Enum):
    """Grounds for summary disposition under MCR 2.116(C)."""

    C1_JURISDICTION = "C1_JURISDICTION"
    C4_PRIOR_ACTION = "C4_PRIOR_ACTION"
    C5_GOVERNMENTAL_IMMUNITY = "C5_GOVERNMENTAL_IMMUNITY"
    C7_FAILURE_TO_STATE_CLAIM = "C7_FAILURE_TO_STATE_CLAIM"
    C8_AFFIRMATIVE_DEFENSE = "C8_AFFIRMATIVE_DEFENSE"
    C9_NO_GENUINE_ISSUE_DIRECTED = "C9_NO_GENUINE_ISSUE_DIRECTED"
    C10_NO_GENUINE_ISSUE = "C10_NO_GENUINE_ISSUE"

    @property
    def mcr_reference(self) -> str:
        info = _GROUNDS_INFO.get(self.value, {})
        return info.get("mcr", "MCR 2.116(C)")

    @property
    def description(self) -> str:
        info = _GROUNDS_INFO.get(self.value, {})
        return info.get("description", "")

    @property
    def standard(self) -> str:
        info = _GROUNDS_INFO.get(self.value, {})
        return info.get("standard", "")

    @property
    def requires_factual_support(self) -> bool:
        """Whether this ground requires documentary evidence beyond pleadings."""
        return self in (
            SJGrounds.C9_NO_GENUINE_ISSUE_DIRECTED,
            SJGrounds.C10_NO_GENUINE_ISSUE,
        )


class SJRole(str, Enum):
    """Role of the party in summary disposition proceedings."""

    MOVANT = "movant"
    RESPONDENT = "respondent"

    @property
    def description(self) -> str:
        _descs = {
            "movant": "Party moving for summary disposition",
            "respondent": "Party responding to motion for summary disposition",
        }
        return _descs.get(self.value, "")


class SJStatus(str, Enum):
    """Status of a summary disposition motion."""

    DRAFTING = "drafting"
    FILED = "filed"
    RESPONSE_PERIOD = "response_period"
    REPLY_PERIOD = "reply_period"
    SUBMITTED = "submitted"
    HEARING_SCHEDULED = "hearing_scheduled"
    GRANTED = "granted"
    DENIED = "denied"
    PARTIAL = "partial"

    @property
    def is_terminal(self) -> bool:
        return self in (SJStatus.GRANTED, SJStatus.DENIED, SJStatus.PARTIAL)


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class SJMotion:
    """A summary disposition motion."""

    motion_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    grounds: List[SJGrounds] = field(default_factory=list)
    movant: str = ""
    respondent: str = ""
    claims_targeted: List[str] = field(default_factory=list)
    supporting_evidence: List[str] = field(default_factory=list)
    status: SJStatus = SJStatus.DRAFTING
    case_number: str = ""
    court: str = _COURT
    judge: str = _JUDGE
    filed_date: str = ""
    response_deadline: str = ""
    role: SJRole = SJRole.MOVANT
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "motion_id": self.motion_id,
            "grounds": [g.value for g in self.grounds],
            "movant": self.movant,
            "respondent": self.respondent,
            "claims_targeted": self.claims_targeted,
            "supporting_evidence": self.supporting_evidence,
            "status": self.status.value,
            "case_number": self.case_number,
            "court": self.court,
            "judge": self.judge,
            "filed_date": self.filed_date,
            "response_deadline": self.response_deadline,
            "role": self.role.value,
            "created_at": self.created_at,
        }


@dataclass
class BurdenAnalysis:
    """Analysis of burden-shifting in summary disposition."""

    analysis_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    motion_id: str = ""
    ground: str = ""
    initial_burden_met: bool = False
    burden_shifted: bool = False
    nonmovant_rebuttal_sufficient: bool = False
    elements_analyzed: List[Dict[str, Any]] = field(default_factory=list)
    recommendation: str = ""
    authority: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "motion_id": self.motion_id,
            "ground": self.ground,
            "initial_burden_met": self.initial_burden_met,
            "burden_shifted": self.burden_shifted,
            "nonmovant_rebuttal_sufficient": self.nonmovant_rebuttal_sufficient,
            "elements_analyzed": self.elements_analyzed,
            "recommendation": self.recommendation,
            "authority": self.authority,
        }


@dataclass
class SJBrief:
    """A brief in support of or opposition to summary disposition."""

    brief_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    motion_id: str = ""
    brief_type: str = ""  # supporting, response, reply
    case_number: str = ""
    sections: List[Dict[str, Any]] = field(default_factory=list)
    authorities_cited: List[str] = field(default_factory=list)
    exhibits_referenced: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "brief_id": self.brief_id,
            "motion_id": self.motion_id,
            "brief_type": self.brief_type,
            "case_number": self.case_number,
            "sections": self.sections,
            "authorities_cited": self.authorities_cited,
            "exhibits_referenced": self.exhibits_referenced,
        }


# ---------------------------------------------------------------------------
# BurdenShiftAnalyzer
# ---------------------------------------------------------------------------


class BurdenShiftAnalyzer:
    """Analyze burden-shifting in summary disposition proceedings.

    Under MCR 2.116(C)(10), the movant has the initial burden of
    specifically identifying the issues for which there is no genuine
    issue of material fact. Maiden v Rozwood, 461 Mich 109 (1999).

    Affidavits must be based on personal knowledge and set forth
    specific facts admissible in evidence. Quinto v Cross & Peters,
    451 Mich 358 (1996).
    """

    def __init__(self) -> None:
        self._analyses: List[BurdenAnalysis] = []

    def analyze_initial_burden(
        self,
        grounds: List[SJGrounds],
        evidence_offered: Optional[List[str]] = None,
        elements_addressed: Optional[Dict[str, bool]] = None,
    ) -> Dict[str, Any]:
        """Analyze whether the movant has met the initial burden.

        For C(10) motions, the movant must specifically identify
        issues where no genuine issue exists. Maiden v Rozwood.
        """
        evidence = evidence_offered or []
        elements = elements_addressed or {}

        ground_analyses: List[Dict[str, Any]] = []
        overall_met = True

        for ground in grounds:
            if ground == SJGrounds.C10_NO_GENUINE_ISSUE:
                analysis = self._analyze_c10_burden(evidence, elements)
            elif ground == SJGrounds.C8_AFFIRMATIVE_DEFENSE:
                analysis = self._analyze_c8_burden(elements)
            elif ground == SJGrounds.C7_FAILURE_TO_STATE_CLAIM:
                analysis = self._analyze_c7_burden(elements)
            elif ground == SJGrounds.C9_NO_GENUINE_ISSUE_DIRECTED:
                analysis = self._analyze_c9_burden(evidence, elements)
            else:
                analysis = self._analyze_legal_ground(ground, elements)

            if not analysis.get("burden_met", False):
                overall_met = False
            ground_analyses.append(analysis)

        result = {
            "grounds_analyzed": [g.value for g in grounds],
            "ground_analyses": ground_analyses,
            "overall_burden_met": overall_met,
            "evidence_count": len(evidence),
            "authority": _AUTHORITY_REFS["maiden"],
        }
        return result

    def _analyze_c10_burden(
        self,
        evidence: List[str],
        elements: Dict[str, bool],
    ) -> Dict[str, Any]:
        """Analyze C(10) burden — Maiden v Rozwood framework."""
        issues: List[str] = []

        if not evidence:
            issues.append(
                "No documentary evidence offered — C(10) requires "
                "affidavits, depositions, or admissions per MCR 2.116(G)"
            )

        unaddressed = [e for e, met in elements.items() if not met]
        if unaddressed:
            issues.append(
                f"Elements not specifically addressed: {', '.join(unaddressed)}"
            )

        burden_met = len(issues) == 0 and len(evidence) > 0
        return {
            "ground": "C10_NO_GENUINE_ISSUE",
            "mcr": "MCR 2.116(C)(10)",
            "burden_met": burden_met,
            "issues": issues,
            "framework": "Maiden v Rozwood, 461 Mich 109 (1999)",
            "affidavit_requirement": "Quinto v Cross & Peters, 451 Mich 358 (1996)",
            "description": (
                "Movant must specifically identify issues with no genuine "
                "issue of material fact and support with admissible evidence"
            ),
        }

    def _analyze_c8_burden(self, elements: Dict[str, bool]) -> Dict[str, Any]:
        """Analyze C(8) burden — failure to state a claim."""
        return {
            "ground": "C8_AFFIRMATIVE_DEFENSE",
            "mcr": "MCR 2.116(C)(8)",
            "burden_met": True,  # C(8) tests legal sufficiency of pleadings
            "issues": [],
            "framework": "Accept well-pleaded facts as true — test legal sufficiency",
            "description": (
                "Court accepts all well-pleaded facts as true and determines "
                "whether the claim is legally sufficient on its face"
            ),
        }

    def _analyze_c7_burden(self, elements: Dict[str, bool]) -> Dict[str, Any]:
        """Analyze C(7) burden — affirmative defense."""
        return {
            "ground": "C7_FAILURE_TO_STATE_CLAIM",
            "mcr": "MCR 2.116(C)(7)",
            "burden_met": True,
            "issues": [],
            "framework": "Legal defense (statute of limitations, immunity, etc.)",
            "description": (
                "Movant must demonstrate a legal defense that bars the claim "
                "as a matter of law"
            ),
        }

    def _analyze_c9_burden(
        self,
        evidence: List[str],
        elements: Dict[str, bool],
    ) -> Dict[str, Any]:
        """Analyze C(9) burden — no genuine issue directed."""
        issues: List[str] = []
        if not evidence:
            issues.append("C(9) requires supporting documentary evidence")

        return {
            "ground": "C9_NO_GENUINE_ISSUE_DIRECTED",
            "mcr": "MCR 2.116(C)(9)",
            "burden_met": len(issues) == 0,
            "issues": issues,
            "framework": "Nonmovant fails to allege valid defense",
            "description": (
                "The opposing party has failed to state a valid defense "
                "and no material issue of fact exists"
            ),
        }

    def _analyze_legal_ground(
        self,
        ground: SJGrounds,
        elements: Dict[str, bool],
    ) -> Dict[str, Any]:
        """Generic analysis for legal-question grounds."""
        return {
            "ground": ground.value,
            "mcr": ground.mcr_reference,
            "burden_met": True,
            "issues": [],
            "framework": ground.standard,
            "description": ground.description,
        }

    def analyze_shifted_burden(
        self,
        initial_analysis: Dict[str, Any],
        nonmovant_evidence: Optional[List[str]] = None,
        nonmovant_affidavits: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Analyze whether the nonmovant has met the shifted burden.

        Once the movant meets the initial burden, the nonmovant must
        come forward with specific facts showing a genuine issue for
        trial. Maiden v Rozwood.
        """
        evidence = nonmovant_evidence or []
        affidavits = nonmovant_affidavits or []

        if not initial_analysis.get("overall_burden_met", False):
            return {
                "burden_shifted": False,
                "reason": "Initial burden not met — no shifting occurs",
                "authority": _AUTHORITY_REFS["maiden"],
            }

        issues: List[str] = []
        if not evidence and not affidavits:
            issues.append(
                "Nonmovant offers no evidence or affidavits to rebut"
            )

        rebuttal_sufficient = len(issues) == 0 and (
            len(evidence) > 0 or len(affidavits) > 0
        )

        return {
            "burden_shifted": True,
            "nonmovant_evidence_count": len(evidence),
            "nonmovant_affidavit_count": len(affidavits),
            "rebuttal_sufficient": rebuttal_sufficient,
            "issues": issues,
            "authority": _AUTHORITY_REFS["maiden"],
            "standard": (
                "Nonmovant must come forward with specific facts showing "
                "a genuine issue for trial — Maiden v Rozwood"
            ),
        }

    def apply_quinto_framework(
        self,
        affidavits: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Apply Quinto v Cross & Peters affidavit requirements.

        Affidavits must be (1) based on personal knowledge, (2) set
        forth specific facts, and (3) admissible in evidence.
        """
        valid = []
        deficient = []

        for aff in affidavits:
            issues: List[str] = []
            if not aff.get("personal_knowledge", False):
                issues.append("Not based on personal knowledge")
            if not aff.get("specific_facts", False):
                issues.append("Does not set forth specific facts")
            if not aff.get("admissible", False):
                issues.append("Contains inadmissible matter")

            entry = {
                "affiant": aff.get("affiant", "Unknown"),
                "subject": aff.get("subject", ""),
                "issues": issues,
                "compliant": len(issues) == 0,
            }
            if len(issues) == 0:
                valid.append(entry)
            else:
                deficient.append(entry)

        return {
            "total_affidavits": len(affidavits),
            "valid_count": len(valid),
            "deficient_count": len(deficient),
            "valid": valid,
            "deficient": deficient,
            "authority": _AUTHORITY_REFS["quinto"],
            "recommendation": (
                "All affidavits meet Quinto requirements"
                if not deficient
                else f"{len(deficient)} affidavit(s) deficient under Quinto"
            ),
        }

    def apply_maiden_framework(
        self,
        ground: SJGrounds,
        movant_evidence: List[str],
        nonmovant_evidence: List[str],
        elements: Dict[str, bool],
    ) -> Dict[str, Any]:
        """Apply the full Maiden v Rozwood framework for C(10) analysis."""
        initial = self.analyze_initial_burden(
            [ground], movant_evidence, elements,
        )
        shifted = self.analyze_shifted_burden(initial, nonmovant_evidence)

        # Light-most-favorable analysis per Skinner
        genuine_issue_exists = shifted.get("rebuttal_sufficient", False)

        recommendation = (
            "Summary disposition should be DENIED — genuine issues of "
            "material fact exist when evidence is viewed in light most "
            "favorable to nonmovant (Skinner v Square D Co)"
            if genuine_issue_exists
            else "Summary disposition should be GRANTED — no genuine "
            "issue of material fact (Maiden v Rozwood)"
        )

        analysis = BurdenAnalysis(
            ground=ground.value,
            initial_burden_met=initial.get("overall_burden_met", False),
            burden_shifted=shifted.get("burden_shifted", False),
            nonmovant_rebuttal_sufficient=genuine_issue_exists,
            recommendation=recommendation,
            authority=f"{_AUTHORITY_REFS['maiden']}; {_AUTHORITY_REFS['skinner']}",
        )
        self._analyses.append(analysis)

        return {
            "analysis": analysis.to_dict(),
            "initial_burden": initial,
            "shifted_burden": shifted,
            "genuine_issue_exists": genuine_issue_exists,
            "recommendation": recommendation,
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "BurdenShiftAnalyzer",
            "total_analyses": len(self._analyses),
        }


# ---------------------------------------------------------------------------
# EvidenceOrganizer
# ---------------------------------------------------------------------------


class EvidenceOrganizer:
    """Organize evidence for summary disposition proceedings.

    MCR 2.116(G) requires that motions under (C)(10) be supported
    by affidavits, depositions, admissions, or other documentary
    evidence.
    """

    def __init__(self) -> None:
        self._organized: List[Dict[str, Any]] = []

    def organize_by_element(
        self,
        elements: List[str],
        evidence_map: Optional[Dict[str, List[str]]] = None,
    ) -> Dict[str, Any]:
        """Organize evidence by legal element to support/oppose motion."""
        emap = evidence_map or {}
        organized: List[Dict[str, Any]] = []
        gaps: List[str] = []

        for element in elements:
            evidence = emap.get(element, [])
            entry = {
                "element": element,
                "evidence_count": len(evidence),
                "evidence": evidence,
                "has_support": len(evidence) > 0,
            }
            organized.append(entry)
            if not evidence:
                gaps.append(element)

        result = {
            "total_elements": len(elements),
            "supported_count": len(elements) - len(gaps),
            "gap_count": len(gaps),
            "gaps": gaps,
            "organized": organized,
            "authority": "MCR 2.116(G)",
        }
        self._organized.append(result)
        return result

    def identify_gaps(
        self,
        elements: List[str],
        available_evidence: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Identify evidentiary gaps that need to be filled."""
        evidence = available_evidence or []
        gaps: List[Dict[str, Any]] = []

        for element in elements:
            matching = [e for e in evidence if element.lower() in e.lower()]
            if not matching:
                gaps.append({
                    "element": element,
                    "status": "unsupported",
                    "recommendation": (
                        f"Obtain evidence supporting element: {element}"
                    ),
                })

        return gaps

    def prepare_affidavits(
        self,
        facts: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Prepare affidavit outlines meeting Quinto requirements.

        Each affidavit must be: (1) based on personal knowledge,
        (2) set forth specific facts, (3) show affiant is competent
        to testify, and (4) contain admissible evidence only.
        """
        affidavits: List[Dict[str, Any]] = []

        for fact_group in facts:
            affidavits.append({
                "affiant": fact_group.get("affiant", _PLAINTIFF),
                "personal_knowledge": True,
                "specific_facts": fact_group.get("facts", []),
                "admissible": True,
                "competent_to_testify": True,
                "quinto_compliant": True,
                "subject": fact_group.get("subject", ""),
                "authority": _AUTHORITY_REFS["quinto"],
            })

        return affidavits

    def compile_exhibits_for_brief(
        self,
        evidence: List[str],
        starting_letter: str = "A",
    ) -> List[Dict[str, Any]]:
        """Compile an exhibit list for the summary disposition brief."""
        exhibits: List[Dict[str, Any]] = []
        letter_code = ord(starting_letter)

        for e in evidence:
            exhibits.append({
                "exhibit_label": chr(letter_code),
                "description": e,
                "admissible": True,
                "foundation": "Affidavit or deposition testimony",
            })
            letter_code += 1
            if letter_code > ord("Z"):
                break  # MCR doesn't limit but convention caps at Z + AA...

        return exhibits

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "EvidenceOrganizer",
            "total_organized": len(self._organized),
        }


# ---------------------------------------------------------------------------
# ResponseDrafter
# ---------------------------------------------------------------------------


class ResponseDrafter:
    """Draft responses to summary disposition motions.

    MCR 2.116(H) provides 21 days to respond. The response must
    include specific facts showing a genuine issue for trial.
    """

    def __init__(self) -> None:
        self._responses: List[Dict[str, Any]] = []

    def draft_response_brief(
        self,
        motion: SJMotion,
        counter_evidence: Optional[List[str]] = None,
        counter_arguments: Optional[List[str]] = None,
    ) -> SJBrief:
        """Draft a response brief to a summary disposition motion."""
        evidence = counter_evidence or []
        arguments = counter_arguments or []

        sections = [
            {
                "heading": "I. INTRODUCTION",
                "content": (
                    f"Plaintiff {_PLAINTIFF}, appearing pro se, respectfully "
                    "opposes Defendant's Motion for Summary Disposition. Genuine "
                    "issues of material fact preclude summary disposition."
                ),
            },
            {
                "heading": "II. COUNTER-STATEMENT OF FACTS",
                "content": (
                    "Viewing the evidence in the light most favorable to the "
                    "nonmoving party (Skinner v Square D Co, 445 Mich 153 "
                    "(1994)), the following material facts are genuinely disputed:"
                ),
                "evidence": evidence,
            },
            {
                "heading": "III. LEGAL STANDARD",
                "content": (
                    "Under MCR 2.116(C)(10), summary disposition is appropriate "
                    "only where there is no genuine issue of material fact and "
                    "the moving party is entitled to judgment as a matter of law. "
                    "The court must consider the evidence in the light most "
                    "favorable to the nonmoving party. Maiden v Rozwood, 461 "
                    "Mich 109, 120 (1999)."
                ),
            },
            {
                "heading": "IV. ARGUMENT",
                "content": (
                    "Genuine issues of material fact exist as to the following "
                    "claims targeted by Defendant's motion:"
                ),
                "arguments": arguments,
                "claims": motion.claims_targeted,
            },
            {
                "heading": "V. CONCLUSION",
                "content": (
                    "For the reasons stated above, Plaintiff respectfully "
                    "requests that the Court deny Defendant's Motion for "
                    "Summary Disposition."
                ),
            },
        ]

        brief = SJBrief(
            motion_id=motion.motion_id,
            brief_type="response",
            case_number=motion.case_number,
            sections=sections,
            authorities_cited=[
                _AUTHORITY_REFS["maiden"],
                _AUTHORITY_REFS["skinner"],
                _AUTHORITY_REFS["quinto"],
            ],
            exhibits_referenced=evidence,
        )
        self._responses.append(brief.to_dict())

        logger.info("Drafted response brief for motion %s", motion.motion_id)
        return brief

    def identify_genuine_issues(
        self,
        motion: SJMotion,
        disputed_facts: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Identify genuine issues of material fact to defeat summary disposition."""
        facts = disputed_facts or []
        issues: List[Dict[str, Any]] = []

        for i, fact in enumerate(facts, 1):
            issues.append({
                "number": i,
                "disputed_fact": fact,
                "materiality": "Material to claims at issue",
                "genuineness": (
                    "Reasonable minds could differ on this fact — "
                    "Skinner v Square D Co"
                ),
            })

        # Per-claim analysis
        for claim in motion.claims_targeted:
            issues.append({
                "number": len(issues) + 1,
                "disputed_fact": f"Elements of '{claim}' remain genuinely disputed",
                "materiality": f"Material to claim: {claim}",
                "genuineness": "Plaintiff has presented evidence creating triable issues",
            })

        return issues

    def prepare_counter_affidavits(
        self,
        facts: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Prepare counter-affidavits meeting Quinto requirements."""
        affidavits: List[Dict[str, Any]] = []
        for fg in facts:
            affidavits.append({
                "affiant": fg.get("affiant", _PLAINTIFF),
                "personal_knowledge": True,
                "specific_facts": fg.get("facts", []),
                "admissible": True,
                "purpose": "Rebut movant's showing of no genuine issue",
                "authority": _AUTHORITY_REFS["quinto"],
            })
        return affidavits

    def request_56f_continuance(
        self,
        motion: SJMotion,
        reasons: Optional[List[str]] = None,
        discovery_needed: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Request a continuance under MCR 2.116(H)(4) (analogous to Fed. R. 56(f)).

        If the nonmovant cannot present essential facts to justify
        opposition, the court may grant a continuance for discovery.
        """
        rsns = reasons or ["Discovery is ongoing and essential facts are not yet available"]
        disc = discovery_needed or []

        return {
            "motion_id": motion.motion_id,
            "document_type": "Motion for Continuance / MCR 2.116(H)",
            "case_number": motion.case_number,
            "reasons": rsns,
            "discovery_needed": disc,
            "legal_basis": "MCR 2.116(H); cf. Fed. R. Civ. P. 56(d)",
            "standard": _56F_CONTINUANCE_STANDARD,
            "sections": [
                {
                    "heading": "REQUEST FOR CONTINUANCE",
                    "content": (
                        f"{_PLAINTIFF} respectfully requests that the Court "
                        "grant a continuance of the response deadline for "
                        "Defendant's Motion for Summary Disposition to allow "
                        "completion of essential discovery."
                    ),
                },
                {
                    "heading": "REASONS",
                    "content": rsns,
                },
                {
                    "heading": "DISCOVERY NEEDED",
                    "content": disc,
                },
            ],
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "ResponseDrafter",
            "total_responses": len(self._responses),
        }


# ---------------------------------------------------------------------------
# OralArgumentPreparer
# ---------------------------------------------------------------------------


class OralArgumentPreparer:
    """Prepare for oral argument on summary disposition.

    MCR 2.116(I) permits the court to order oral argument on
    summary disposition motions.
    """

    def __init__(self) -> None:
        self._outlines: List[Dict[str, Any]] = []

    def prepare_argument_outline(
        self,
        motion: SJMotion,
        role: SJRole = SJRole.RESPONDENT,
        key_points: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Prepare an oral argument outline."""
        points = key_points or []

        if role == SJRole.RESPONDENT:
            structure = [
                {
                    "section": "Opening",
                    "duration_minutes": 2,
                    "content": (
                        "May it please the Court. This case presents genuine "
                        "issues of material fact that preclude summary disposition."
                    ),
                },
                {
                    "section": "Factual Summary",
                    "duration_minutes": 3,
                    "content": (
                        "The disputed facts, viewed in the light most favorable "
                        "to Plaintiff (Skinner v Square D Co), show..."
                    ),
                    "key_facts": points[:3] if points else [],
                },
                {
                    "section": "Legal Argument",
                    "duration_minutes": 5,
                    "content": (
                        "Under the Maiden v Rozwood framework, Defendant has "
                        "not met the initial burden of demonstrating no genuine "
                        "issue of material fact. Even if the burden shifts, "
                        "Plaintiff has presented sufficient evidence creating "
                        "triable issues."
                    ),
                },
                {
                    "section": "Conclusion",
                    "duration_minutes": 2,
                    "content": (
                        "For these reasons, Plaintiff respectfully requests "
                        "that the Court deny the motion and allow this case "
                        "to proceed to trial."
                    ),
                },
            ]
        else:
            structure = [
                {
                    "section": "Opening",
                    "duration_minutes": 2,
                    "content": (
                        "May it please the Court. There is no genuine issue "
                        "of material fact and judgment should be entered as "
                        "a matter of law."
                    ),
                },
                {
                    "section": "Burden Met",
                    "duration_minutes": 4,
                    "content": "Movant has met the initial burden under Maiden v Rozwood.",
                    "key_evidence": points[:3] if points else [],
                },
                {
                    "section": "No Genuine Issue",
                    "duration_minutes": 4,
                    "content": "Nonmovant has not come forward with specific facts.",
                },
                {
                    "section": "Conclusion",
                    "duration_minutes": 2,
                    "content": "Summary disposition should be granted.",
                },
            ]

        outline = {
            "motion_id": motion.motion_id,
            "role": role.value,
            "total_time_minutes": sum(s["duration_minutes"] for s in structure),
            "structure": structure,
            "key_points": points,
            "authority": f"{_AUTHORITY_REFS['maiden']}; {_AUTHORITY_REFS['skinner']}",
        }
        self._outlines.append(outline)
        return outline

    def anticipate_questions(
        self,
        motion: SJMotion,
        role: SJRole = SJRole.RESPONDENT,
    ) -> List[Dict[str, Any]]:
        """Anticipate likely questions from the bench."""
        questions = [
            {
                "question": "What specific evidence creates a genuine issue of material fact?",
                "preparation": (
                    "Point to specific affidavits, deposition testimony, or "
                    "documentary evidence — not conclusory allegations"
                ),
                "authority": _AUTHORITY_REFS["quinto"],
            },
            {
                "question": "Has the nonmovant had adequate opportunity for discovery?",
                "preparation": (
                    "If discovery is incomplete, reference MCR 2.116(H) "
                    "continuance request and specific discovery still needed"
                ),
                "authority": "MCR 2.116(H)",
            },
            {
                "question": "What are the material facts that are genuinely disputed?",
                "preparation": (
                    "List each disputed fact with record citations — "
                    "the court looks at evidence in light most favorable "
                    "to nonmovant (Skinner)"
                ),
                "authority": _AUTHORITY_REFS["skinner"],
            },
        ]

        if role == SJRole.MOVANT:
            questions.append({
                "question": "Has the movant specifically identified issues with no genuine dispute?",
                "preparation": (
                    "Reference Maiden requirement to specifically identify "
                    "issues and cite supporting evidence for each"
                ),
                "authority": _AUTHORITY_REFS["maiden"],
            })

        for claim in motion.claims_targeted:
            questions.append({
                "question": f"What evidence supports/defeats the claim of {claim}?",
                "preparation": f"Cite specific evidence related to {claim}",
                "authority": "MCR 2.116(G)",
            })

        return questions

    def prepare_authorities_for_bench(
        self,
        grounds: List[SJGrounds],
    ) -> List[Dict[str, Any]]:
        """Prepare authority list for the bench (courtesy copies)."""
        authorities = [
            {
                "citation": "Maiden v Rozwood, 461 Mich 109 (1999)",
                "relevance": "C(10) burden-shifting framework",
                "key_holding": (
                    "Movant must specifically identify issues for which there "
                    "is no genuine issue of material fact"
                ),
            },
            {
                "citation": "Quinto v Cross & Peters, 451 Mich 358 (1996)",
                "relevance": "Affidavit requirements for C(10) motions",
                "key_holding": (
                    "Affidavits must be based on personal knowledge and set "
                    "forth specific facts admissible in evidence"
                ),
            },
            {
                "citation": "Skinner v Square D Co, 445 Mich 153 (1994)",
                "relevance": "Light-most-favorable standard",
                "key_holding": (
                    "Court must consider evidence in the light most favorable "
                    "to the nonmoving party"
                ),
            },
        ]

        for g in grounds:
            authorities.append({
                "citation": g.mcr_reference,
                "relevance": g.description,
                "key_holding": g.standard,
            })

        return authorities

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "OralArgumentPreparer",
            "total_outlines": len(self._outlines),
        }


# ---------------------------------------------------------------------------
# SummaryJudgmentEngine  (main orchestrator)
# ---------------------------------------------------------------------------


class SummaryJudgmentEngine:
    """Top-level orchestrator for summary disposition practice.

    Combines :class:`BurdenShiftAnalyzer`, :class:`EvidenceOrganizer`,
    :class:`ResponseDrafter`, and :class:`OralArgumentPreparer` into a
    unified system for summary disposition under MCR 2.116.

    Michigan Authority:
        MCR 2.116, Maiden v Rozwood 461 Mich 109 (1999),
        Quinto v Cross & Peters 451 Mich 358 (1996)
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or _DB_PATH
        self._burden_analyzer = BurdenShiftAnalyzer()
        self._evidence_organizer = EvidenceOrganizer()
        self._response_drafter = ResponseDrafter()
        self._oral_preparer = OralArgumentPreparer()
        self._motions: Dict[str, SJMotion] = {}

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

    def prepare_motion(
        self,
        grounds: Optional[List[str]] = None,
        claims_targeted: Optional[List[str]] = None,
        supporting_evidence: Optional[List[str]] = None,
        case_number: str = "",
        movant: str = "",
        respondent: str = "",
        role: SJRole = SJRole.MOVANT,
    ) -> Dict[str, Any]:
        """Prepare a summary disposition motion."""
        case_num = case_number or LANE_CASES["B"]
        ground_enums = []
        for g in (grounds or ["C10_NO_GENUINE_ISSUE"]):
            try:
                ground_enums.append(SJGrounds(g))
            except ValueError:
                logger.warning("Unknown ground: %s", g)

        motion = SJMotion(
            grounds=ground_enums,
            movant=movant or _PLAINTIFF,
            respondent=respondent or _DEFENDANT,
            claims_targeted=claims_targeted or [],
            supporting_evidence=supporting_evidence or [],
            case_number=case_num,
            role=role,
        )
        self._motions[motion.motion_id] = motion

        # Generate brief outline
        brief_sections = []
        for ground in ground_enums:
            brief_sections.append({
                "ground": ground.value,
                "mcr": ground.mcr_reference,
                "standard": ground.standard,
                "description": ground.description,
            })

        logger.info(
            "Prepared motion %s (grounds: %s, claims: %s)",
            motion.motion_id,
            [g.value for g in ground_enums],
            claims_targeted,
        )

        return {
            "motion_id": motion.motion_id,
            "motion": motion.to_dict(),
            "brief_sections": brief_sections,
            "response_period": f"{_RESPONSE_PERIOD_DAYS} days (MCR 2.116(H))",
            "authority": _AUTHORITY_REFS["summary_disposition"],
        }

    def prepare_response(
        self,
        motion_id: str,
        counter_evidence: Optional[List[str]] = None,
        disputed_facts: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Prepare a response to a summary disposition motion."""
        motion = self._motions.get(motion_id)
        if not motion:
            return {"error": f"Motion {motion_id} not found"}

        brief = self._response_drafter.draft_response_brief(
            motion=motion,
            counter_evidence=counter_evidence,
        )
        issues = self._response_drafter.identify_genuine_issues(
            motion=motion,
            disputed_facts=disputed_facts,
        )

        return {
            "motion_id": motion_id,
            "brief": brief.to_dict(),
            "genuine_issues": issues,
            "issue_count": len(issues),
            "authority": _AUTHORITY_REFS["maiden"],
        }

    def analyze_odds(
        self,
        motion_id: str,
        movant_evidence_strength: int = 50,
        nonmovant_evidence_strength: int = 50,
    ) -> Dict[str, Any]:
        """Analyze odds of success for summary disposition motion.

        Uses a heuristic scoring model based on ground type, evidence
        strength, and burden-shifting analysis.
        """
        motion = self._motions.get(motion_id)
        if not motion:
            return {"error": f"Motion {motion_id} not found"}

        # Base probability by ground
        ground_probs: Dict[str, float] = {
            "C1_JURISDICTION": 0.30,
            "C4_PRIOR_ACTION": 0.40,
            "C5_GOVERNMENTAL_IMMUNITY": 0.50,
            "C7_FAILURE_TO_STATE_CLAIM": 0.45,
            "C8_AFFIRMATIVE_DEFENSE": 0.50,
            "C9_NO_GENUINE_ISSUE_DIRECTED": 0.55,
            "C10_NO_GENUINE_ISSUE": 0.35,
        }

        best_prob = 0.0
        ground_analysis: List[Dict[str, Any]] = []

        for ground in motion.grounds:
            base = ground_probs.get(ground.value, 0.30)
            # Adjust for evidence strength
            evidence_factor = (movant_evidence_strength - nonmovant_evidence_strength) / 200.0
            adjusted = max(0.05, min(0.95, base + evidence_factor))
            best_prob = max(best_prob, adjusted)

            ground_analysis.append({
                "ground": ground.value,
                "base_probability": base,
                "adjusted_probability": round(adjusted, 3),
                "evidence_factor": round(evidence_factor, 3),
            })

        return {
            "motion_id": motion_id,
            "overall_probability": round(best_prob, 3),
            "ground_analysis": ground_analysis,
            "movant_evidence_strength": movant_evidence_strength,
            "nonmovant_evidence_strength": nonmovant_evidence_strength,
            "recommendation": (
                "Motion has reasonable probability of success — "
                "consider filing" if best_prob >= 0.45
                else "Motion faces significant headwinds — "
                "strengthen evidence before filing"
            ),
            "caveat": (
                "This is a heuristic estimate only. Actual outcomes depend "
                "on the specific facts, evidence, and judicial temperament."
            ),
        }

    def generate_brief_outline(
        self,
        motion_id: str,
        role: SJRole = SJRole.MOVANT,
    ) -> Dict[str, Any]:
        """Generate a brief outline for summary disposition."""
        motion = self._motions.get(motion_id)
        if not motion:
            return {"error": f"Motion {motion_id} not found"}

        if role == SJRole.MOVANT:
            sections = [
                "I. INTRODUCTION",
                "II. STATEMENT OF UNDISPUTED FACTS",
                "III. LEGAL STANDARD",
                "IV. ARGUMENT",
            ]
            for ground in motion.grounds:
                sections.append(f"    A. {ground.mcr_reference}: {ground.description}")
            sections.extend([
                "V. CONCLUSION",
                "CERTIFICATE OF SERVICE",
            ])
        else:
            sections = [
                "I. INTRODUCTION",
                "II. COUNTER-STATEMENT OF FACTS",
                "III. LEGAL STANDARD",
                "IV. ARGUMENT — GENUINE ISSUES OF MATERIAL FACT EXIST",
                "V. CONCLUSION",
                "CERTIFICATE OF SERVICE",
            ]

        return {
            "motion_id": motion_id,
            "role": role.value,
            "sections": sections,
            "required_attachments": [
                "Affidavit(s) — MCR 2.116(G); Quinto v Cross & Peters",
                "Exhibits referenced in brief",
                "Proposed Order",
                "Proof of Service — MCR 2.107",
            ],
            "authority": _AUTHORITY_REFS["summary_disposition"],
        }

    def get_motion(self, motion_id: str) -> Optional[SJMotion]:
        """Retrieve a motion by ID."""
        return self._motions.get(motion_id)

    def list_motions(
        self,
        status: Optional[SJStatus] = None,
    ) -> List[SJMotion]:
        """List all motions, optionally filtered."""
        if status:
            return [m for m in self._motions.values() if m.status == status]
        return list(self._motions.values())

    def update_status(
        self,
        motion_id: str,
        new_status: SJStatus,
    ) -> Optional[SJMotion]:
        """Update the status of a motion."""
        motion = self._motions.get(motion_id)
        if motion:
            old_status = motion.status
            motion.status = new_status
            logger.info(
                "Motion %s: %s → %s",
                motion_id, old_status.value, new_status.value,
            )
        return motion

    def get_stats(self) -> Dict[str, Any]:
        """Return runtime statistics."""
        by_status: Dict[str, int] = {}
        by_ground: Dict[str, int] = {}
        for m in self._motions.values():
            by_status[m.status.value] = by_status.get(m.status.value, 0) + 1
            for g in m.grounds:
                by_ground[g.value] = by_ground.get(g.value, 0) + 1

        return {
            "module": "summary_judgment_engine",
            "total_motions": len(self._motions),
            "by_status": by_status,
            "by_ground": by_ground,
            "db_path": str(self._db_path),
            "burden_analyzer": self._burden_analyzer.get_stats(),
            "evidence_organizer": self._evidence_organizer.get_stats(),
            "response_drafter": self._response_drafter.get_stats(),
            "oral_preparer": self._oral_preparer.get_stats(),
        }

    def reset(self) -> None:
        """Clear all loaded motions."""
        self._motions.clear()


# ---------------------------------------------------------------------------
# CLI demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sys.stdout = open(  # noqa: SIM115
        sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace"
    )
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print("=" * 60)
    print("  Summary Judgment Engine — LitigationOS")
    print("=" * 60)
    print()

    engine = SummaryJudgmentEngine()

    # Prepare motion
    result = engine.prepare_motion(
        grounds=["C10_NO_GENUINE_ISSUE"],
        claims_targeted=["negligent maintenance", "breach of warranty"],
        supporting_evidence=["Affidavit of Pigors", "Inspection report"],
        case_number=LANE_CASES["B"],
    )
    print(f"Motion ID: {result['motion_id']}")
    print(f"  Grounds: {result['brief_sections']}")
    print()

    # Analyze odds
    odds = engine.analyze_odds(
        result["motion_id"],
        movant_evidence_strength=70,
        nonmovant_evidence_strength=40,
    )
    print(f"Odds: {odds['overall_probability']}")
    print(f"  Recommendation: {odds['recommendation']}")
    print()

    # Burden analysis
    analyzer = BurdenShiftAnalyzer()
    maiden = analyzer.apply_maiden_framework(
        ground=SJGrounds.C10_NO_GENUINE_ISSUE,
        movant_evidence=["Affidavit", "Inspection report"],
        nonmovant_evidence=[],
        elements={"duty": True, "breach": True, "causation": True, "damages": True},
    )
    print(f"Maiden analysis: genuine issue = {maiden['genuine_issue_exists']}")
    print(f"  Recommendation: {maiden['recommendation'][:80]}...")
    print()

    # Stats
    stats = engine.get_stats()
    print("Stats:")
    for k, v in stats.items():
        print(f"  {k}: {v}")
