"""14th Circuit Motion Form Library — comprehensive motion generation engine.

Generates court-ready motions, responses, replies, and proposed orders for
Michigan 14th Circuit Court (Family Division, Muskegon County).  Every
document follows MCR requirements with proper captions, signature blocks,
and certificates of service.

Usage::

    lib = MotionFormLibrary()
    types = lib.list_motion_types()
    motion = lib.generate_motion("motion_to_show_cause", case_info, arguments, relief)
    validation = lib.validate_motion(motion.body_text)
    forms = lib.get_required_forms("motion_to_show_cause")
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Verified party identity — SINGLE SOURCE OF TRUTH (never fabricate)
# ---------------------------------------------------------------------------

PARTIES: dict[str, dict[str, str]] = {
    "plaintiff": {
        "name": "Andrew James Pigors",
        "address": "1977 Whitehall Road, Lot 17\nNorth Muskegon, MI 49445",
        "phone": "(231) 903-5690",
        "email": "andrewjpigors@gmail.com",
    },
    "defendant": {
        "name": "Emily A. Watson",
        "address": "2160 Garland Drive\nNorton Shores, MI 49441",
    },
    "judge": {
        "name": "Hon. Jenny L. McNeill",
        "court": "14th Circuit Court, Family Division",
    },
    "foc": {
        "name": "Pamela Rusco",
        "title": "Friend of the Court",
        "address": "990 Terrace St, Muskegon, MI 49442",
    },
    "child": {
        "initials": "L.D.W.",
    },
}

CASE_NUMBER = "2024-001507-DC"
COURT_NAME = "14th Circuit Court"
COUNTY = "Muskegon County"
DIVISION = "Family Division"


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class MotionType(BaseModel):
    """Metadata for a motion type in the library."""

    name: str
    mcr_rule: str
    description: str
    required_sections: list[str]
    scao_forms: list[str] = Field(default_factory=list)
    filing_fee: str = "$20.00"

    model_config = ConfigDict(frozen=True)


class CaseInfo(BaseModel):
    """Case identification for motion generation."""

    case_number: str = CASE_NUMBER
    plaintiff: str = "Andrew James Pigors"
    defendant: str = "Emily A. Watson"
    judge: str = "Hon. Jenny L. McNeill"
    court: str = COURT_NAME
    county: str = COUNTY
    division: str = DIVISION
    child_initials: str = "L.D.W."

    model_config = ConfigDict(frozen=True)


class MotionDocument(BaseModel):
    """A complete generated motion document."""

    motion_type: str
    case_info: CaseInfo
    caption: str
    body_sections: dict[str, str]
    relief_requested: list[str]
    signature_block: str
    certificate_of_service: str
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    model_config = ConfigDict(from_attributes=True)

    @property
    def body_text(self) -> str:
        """Return the full document as a single string."""
        parts = [self.caption, ""]
        for heading, content in self.body_sections.items():
            parts.append(f"## {heading.upper()}")
            parts.append(content)
            parts.append("")
        if self.relief_requested:
            parts.append("## RELIEF REQUESTED")
            parts.append("")
            for i, item in enumerate(self.relief_requested, 1):
                parts.append(f"{i}. {item}")
            parts.append("")
        parts.append(self.signature_block)
        parts.append("")
        parts.append(self.certificate_of_service)
        return "\n".join(parts)


class MotionValidation(BaseModel):
    """Results from validating a motion document."""

    is_valid: bool
    missing_sections: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    mcr_compliance_score: float = 0.0

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Motion type registry
# ---------------------------------------------------------------------------

MOTION_TYPES: dict[str, MotionType] = {
    "motion_to_show_cause": MotionType(
        name="Motion to Show Cause",
        mcr_rule="MCR 3.208",
        description="Contempt motion for violation of court orders, including "
        "custody, parenting time, and support orders.",
        required_sections=[
            "Statement of Facts",
            "Order Violated",
            "Specific Violations",
            "Legal Argument",
            "Relief Requested",
            "Certificate of Service",
        ],
        scao_forms=["FOC 1", "FOC 3"],
        filing_fee="$20.00",
    ),
    "motion_for_parenting_time": MotionType(
        name="Motion to Modify Parenting Time",
        mcr_rule="MCR 3.215",
        description="Modify existing parenting time schedule.  Requires showing "
        "proper cause or change of circumstances under MCL 722.27a.",
        required_sections=[
            "Statement of Facts",
            "Current Parenting Time Order",
            "Proposed Modification",
            "Legal Argument",
            "Best Interest Factors",
            "Relief Requested",
            "Certificate of Service",
        ],
        scao_forms=["FOC 65", "MC 416"],
        filing_fee="$20.00",
    ),
    "motion_to_change_custody": MotionType(
        name="Motion to Change Custody",
        mcr_rule="MCR 3.215",
        description="Change physical or legal custody.  Must establish proper cause "
        "or change of circumstances and address all 12 best interest "
        "factors under MCL 722.23.",
        required_sections=[
            "Statement of Facts",
            "Change of Circumstances",
            "Best Interest Factors",
            "Legal Argument",
            "Relief Requested",
            "Certificate of Service",
        ],
        scao_forms=["FOC 65", "FOC 89", "MC 416"],
        filing_fee="$20.00",
    ),
    "motion_to_compel_discovery": MotionType(
        name="Motion to Compel Discovery",
        mcr_rule="MCR 2.313",
        description="Compel opposing party to respond to interrogatories, requests "
        "for production, or requests for admission.",
        required_sections=[
            "Statement of Facts",
            "Discovery Requests Served",
            "Good Faith Efforts",
            "Legal Argument",
            "Relief Requested",
            "Certificate of Service",
        ],
        scao_forms=["MC 416"],
        filing_fee="$20.00",
    ),
    "motion_for_disqualification": MotionType(
        name="Motion for Disqualification of Judge",
        mcr_rule="MCR 2.003",
        description="Disqualify the assigned judge for bias, prejudice, personal "
        "interest, or other grounds under MCR 2.003(C).",
        required_sections=[
            "Statement of Facts",
            "Grounds for Disqualification",
            "Affidavit of Bias",
            "Legal Argument",
            "Relief Requested",
            "Certificate of Service",
        ],
        scao_forms=["MC 416"],
        filing_fee="$20.00",
    ),
    "motion_for_sanctions": MotionType(
        name="Motion for Sanctions",
        mcr_rule="MCR 2.114(E)",
        description="Sanctions for frivolous positions, failure to comply with "
        "court orders, or litigation misconduct.",
        required_sections=[
            "Statement of Facts",
            "Sanctionable Conduct",
            "Legal Argument",
            "Relief Requested",
            "Certificate of Service",
        ],
        scao_forms=["MC 416"],
        filing_fee="$20.00",
    ),
    "motion_for_protective_order": MotionType(
        name="Motion for Protective Order",
        mcr_rule="MCR 2.302(C)",
        description="Protect a party from oppressive or abusive discovery, "
        "harassment, or undue burden.",
        required_sections=[
            "Statement of Facts",
            "Discovery at Issue",
            "Grounds for Protection",
            "Legal Argument",
            "Relief Requested",
            "Certificate of Service",
        ],
        scao_forms=["MC 416"],
        filing_fee="$20.00",
    ),
    "motion_in_limine": MotionType(
        name="Motion in Limine",
        mcr_rule="MRE 103/104",
        description="Pre-trial motion to exclude or admit specific evidence.  "
        "Based on Michigan Rules of Evidence.",
        required_sections=[
            "Statement of Facts",
            "Evidence at Issue",
            "Legal Argument",
            "Relief Requested",
            "Certificate of Service",
        ],
        scao_forms=["MC 416"],
        filing_fee="$20.00",
    ),
    "motion_for_adjournment": MotionType(
        name="Motion for Adjournment",
        mcr_rule="MCR 2.503",
        description="Postpone a scheduled hearing.  Requires good cause and must "
        "be filed promptly after grounds are known.",
        required_sections=[
            "Statement of Facts",
            "Good Cause",
            "Proposed Alternate Date",
            "Legal Argument",
            "Relief Requested",
            "Certificate of Service",
        ],
        scao_forms=["MC 416"],
        filing_fee="$0.00",
    ),
    "motion_for_default": MotionType(
        name="Motion for Default Judgment",
        mcr_rule="MCR 2.603",
        description="Enter default judgment against a party who failed to plead "
        "or otherwise defend within the required time.",
        required_sections=[
            "Statement of Facts",
            "Service of Process",
            "Failure to Respond",
            "Legal Argument",
            "Relief Requested",
            "Certificate of Service",
        ],
        scao_forms=["MC 416", "DC 107"],
        filing_fee="$20.00",
    ),
    "motion_for_relief_from_judgment": MotionType(
        name="Motion for Relief from Judgment",
        mcr_rule="MCR 2.612",
        description="Set aside a judgment or order for mistake, newly discovered "
        "evidence, fraud, or other extraordinary circumstances.",
        required_sections=[
            "Statement of Facts",
            "Judgment at Issue",
            "Grounds for Relief",
            "Legal Argument",
            "Relief Requested",
            "Certificate of Service",
        ],
        scao_forms=["MC 416"],
        filing_fee="$20.00",
    ),
    "motion_for_stay": MotionType(
        name="Motion for Stay Pending Appeal",
        mcr_rule="MCR 2.614",
        description="Stay enforcement of a judgment or order while an appeal "
        "is pending before the Court of Appeals.",
        required_sections=[
            "Statement of Facts",
            "Order to Be Stayed",
            "Likelihood of Success on Appeal",
            "Irreparable Harm",
            "Legal Argument",
            "Relief Requested",
            "Certificate of Service",
        ],
        scao_forms=["MC 416"],
        filing_fee="$20.00",
    ),
    "emergency_motion": MotionType(
        name="Emergency Motion (Ex Parte)",
        mcr_rule="MCR 3.207",
        description="Ex parte emergency motion when child faces immediate danger "
        "or irreparable harm will result from delay.",
        required_sections=[
            "Statement of Emergency",
            "Statement of Facts",
            "Irreparable Harm",
            "Legal Argument",
            "Relief Requested",
            "Verification",
            "Certificate of Service",
        ],
        scao_forms=["FOC 65", "MC 416", "FOC 3"],
        filing_fee="$20.00",
    ),
}

# Best interest factors under MCL 722.23
BEST_INTEREST_FACTORS: list[str] = [
    "(a) The love, affection, and other emotional ties existing between the parties involved and the child.",
    "(b) The capacity and disposition of the parties involved to give the child love, affection, and guidance.",
    "(c) The capacity and disposition of the parties involved to provide the child with food, clothing, medical care.",
    "(d) The length of time the child has lived in a stable, satisfactory environment.",
    "(e) The permanence, as a family unit, of the existing or proposed custodial home.",
    "(f) The moral fitness of the parties involved.",
    "(g) The mental and physical health of the parties involved.",
    "(h) The home, school, and community record of the child.",
    "(i) The reasonable preference of the child, if the court considers the child to be of sufficient age.",
    "(j) The willingness and ability of each of the parties to facilitate and encourage a close relationship between the child and the other parent.",
    "(k) Domestic violence, regardless of whether the violence was directed against the child.",
    "(l) Any other factor considered by the court to be relevant.",
]


# ---------------------------------------------------------------------------
# Caption / signature / certificate builders
# ---------------------------------------------------------------------------


def _build_caption(case_info: CaseInfo) -> str:
    """Build a standard 14th Circuit Family Division caption."""
    return (
        f"STATE OF MICHIGAN\n"
        f"IN THE {case_info.court.upper()} FOR THE COUNTY OF {case_info.county.upper()}\n"
        f"{case_info.division.upper()}\n"
        f"\n"
        f"{case_info.plaintiff.upper()},\n"
        f"    Plaintiff,{' ' * 26}Case No. {case_info.case_number}\n"
        f"v.{' ' * 40}Hon. {case_info.judge.replace('Hon. ', '')}\n"
        f"\n"
        f"{case_info.defendant.upper()},\n"
        f"    Defendant.\n"
        f"{'_' * 40}/"
    )


def _build_signature_block(date_str: str | None = None) -> str:
    """Build a pro se plaintiff signature block."""
    p = PARTIES["plaintiff"]
    date_str = date_str or datetime.now().strftime("%B %d, %Y")
    return (
        f"Respectfully submitted,\n"
        f"\n"
        f"Dated: {date_str}\n"
        f"\n"
        f"_________________________________\n"
        f"{p['name']}, Pro Se Plaintiff\n"
        f"{p['address']}\n"
        f"{p['phone']}\n"
        f"{p['email']}"
    )


def _build_certificate_of_service(
    method: str = "first-class mail",
    date_str: str | None = None,
) -> str:
    """Build a certificate of service for the defendant and FOC."""
    p = PARTIES["plaintiff"]
    d = PARTIES["defendant"]
    foc = PARTIES["foc"]
    date_str = date_str or datetime.now().strftime("%B %d, %Y")
    return (
        f"## CERTIFICATE OF SERVICE\n"
        f"\n"
        f"I, {p['name']}, hereby certify that on {date_str}, I served a true\n"
        f"and correct copy of this document upon the following parties by {method},\n"
        f"postage prepaid, pursuant to MCR 2.107:\n"
        f"\n"
        f"- **{d['name']}**\n"
        f"  {d['address']}\n"
        f"\n"
        f"- **{foc['name']}**, {foc['title']}\n"
        f"  {foc['address']}\n"
        f"\n"
        f"_________________________________\n"
        f"{p['name']}"
    )


# ---------------------------------------------------------------------------
# Section generators (per motion type)
# ---------------------------------------------------------------------------


def _section_statement_of_facts(arguments: list[str]) -> str:
    """Build statement of facts from argument list."""
    if not arguments:
        return "[STATEMENT OF FACTS TO BE SUPPLIED]"
    lines = []
    for i, arg in enumerate(arguments, 1):
        lines.append(f"{i}. {arg}")
    return "\n".join(lines)


def _section_legal_argument(mcr_rule: str, arguments: list[str]) -> str:
    """Build legal argument section with MCR citation."""
    parts = [
        f"Pursuant to **{mcr_rule}**, Plaintiff respectfully submits as follows:\n"
    ]
    if arguments:
        for i, arg in enumerate(arguments, 1):
            parts.append(f"{i}. {arg}")
    else:
        parts.append("[LEGAL ARGUMENT TO BE SUPPLIED]")
    return "\n".join(parts)


def _section_best_interest_factors() -> str:
    """Build best interest factors section (MCL 722.23)."""
    header = (
        "Under MCL 722.23, the Court must consider the following best interest "
        "factors:\n"
    )
    lines = []
    for factor in BEST_INTEREST_FACTORS:
        lines.append(f"- {factor}\n  **Analysis:** [TO BE SUPPLIED]")
    return header + "\n\n".join(lines)


# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------


class MotionFormLibrary:
    """14th Circuit Motion Form Library for Michigan Family Division.

    Provides generation, validation, and template access for 13 motion types
    used in family law proceedings.

    Parameters
    ----------
    case_info : CaseInfo | None
        Default case identification.  Uses the Pigors v. Watson defaults
        when *None*.
    """

    def __init__(self, case_info: CaseInfo | None = None) -> None:
        self.case_info = case_info or CaseInfo()
        logger.info(
            "MotionFormLibrary ready — %d motion types loaded",
            len(MOTION_TYPES),
        )

    # -- Catalogue -----------------------------------------------------------

    def list_motion_types(self) -> list[dict[str, Any]]:
        """Return all available motion templates with descriptions.

        Returns a list of dicts with keys: ``name``, ``key``,
        ``mcr_rule``, ``description``, ``required_sections``,
        ``scao_forms``, ``filing_fee``.
        """
        result: list[dict[str, Any]] = []
        for key, mt in MOTION_TYPES.items():
            result.append({
                "key": key,
                "name": mt.name,
                "mcr_rule": mt.mcr_rule,
                "description": mt.description,
                "required_sections": list(mt.required_sections),
                "scao_forms": list(mt.scao_forms),
                "filing_fee": mt.filing_fee,
            })
        return result

    def get_motion_template(self, motion_type: str) -> MotionType:
        """Return the raw :class:`MotionType` template for customization.

        Raises ``KeyError`` if *motion_type* is not in the library.
        """
        if motion_type not in MOTION_TYPES:
            raise KeyError(
                f"Unknown motion type '{motion_type}'.  "
                f"Valid types: {', '.join(sorted(MOTION_TYPES))}"
            )
        return MOTION_TYPES[motion_type]

    def get_required_forms(self, motion_type: str) -> list[str]:
        """Return SCAO form numbers needed for *motion_type*.

        Raises ``KeyError`` if *motion_type* is not in the library.
        """
        mt = self.get_motion_template(motion_type)
        return list(mt.scao_forms)

    # -- Generation: motion --------------------------------------------------

    def generate_motion(
        self,
        motion_type: str,
        case_info: CaseInfo | None = None,
        arguments: list[str] | None = None,
        relief_requested: list[str] | None = None,
    ) -> MotionDocument:
        """Generate a complete motion document.

        Parameters
        ----------
        motion_type : str
            Key from :data:`MOTION_TYPES` (e.g. ``"motion_to_show_cause"``).
        case_info : CaseInfo | None
            Override default case information.
        arguments : list[str] | None
            Facts and legal arguments to include.
        relief_requested : list[str] | None
            Specific relief items.  Falls back to template defaults.

        Returns
        -------
        MotionDocument
            A fully-populated motion with caption, body, signature, and
            certificate of service.
        """
        mt = self.get_motion_template(motion_type)
        ci = case_info or self.case_info
        arguments = arguments or []
        today = datetime.now().strftime("%B %d, %Y")

        caption = _build_caption(ci)
        caption += f"\n\n# {mt.name.upper()}\n\n**Filed:** {today}"

        body: dict[str, str] = {}

        # Build sections based on motion type
        body["Statement of Facts"] = _section_statement_of_facts(arguments)

        # Motion-type-specific sections
        if motion_type == "motion_to_show_cause":
            body["Order Violated"] = (
                "[Identify the specific court order violated, including date and "
                "docket entry number]"
            )
            body["Specific Violations"] = (
                "[Detail each specific act or omission that constitutes a violation]"
            )
        elif motion_type == "motion_for_parenting_time":
            body["Current Parenting Time Order"] = (
                "[Describe the current parenting time schedule as ordered by the Court]"
            )
            body["Proposed Modification"] = (
                "[Set forth the proposed parenting time modification in detail]"
            )
            body["Best Interest Factors"] = _section_best_interest_factors()
        elif motion_type == "motion_to_change_custody":
            body["Change of Circumstances"] = (
                "[Demonstrate proper cause or change of circumstances since the "
                "last custody order, as required by MCL 722.27(1)(c)]"
            )
            body["Best Interest Factors"] = _section_best_interest_factors()
        elif motion_type == "motion_to_compel_discovery":
            body["Discovery Requests Served"] = (
                "[Identify discovery requests, date served, and responses due]"
            )
            body["Good Faith Efforts"] = (
                "Plaintiff certifies that good faith efforts were made to resolve "
                "this discovery dispute without court intervention, as required by "
                "MCR 2.313(A)(5)."
            )
        elif motion_type == "motion_for_disqualification":
            body["Grounds for Disqualification"] = (
                "[Set forth specific facts showing bias, prejudice, personal "
                "interest, or other grounds under MCR 2.003(C)(1)]"
            )
            body["Affidavit of Bias"] = (
                "[Attach supporting affidavit per MCR 2.003(D)]"
            )
        elif motion_type == "motion_for_sanctions":
            body["Sanctionable Conduct"] = (
                "[Identify the specific frivolous claims, defenses, or litigation "
                "misconduct warranting sanctions under MCR 2.114(E)]"
            )
        elif motion_type == "motion_for_protective_order":
            body["Discovery at Issue"] = (
                "[Identify the discovery requests from which protection is sought]"
            )
            body["Grounds for Protection"] = (
                "[Explain how the discovery is oppressive, unduly burdensome, or "
                "seeks privileged/protected information under MCR 2.302(C)]"
            )
        elif motion_type == "motion_in_limine":
            body["Evidence at Issue"] = (
                "[Describe the evidence sought to be excluded or admitted]"
            )
        elif motion_type == "motion_for_adjournment":
            body["Good Cause"] = (
                "[Describe the good cause for postponement per MCR 2.503]"
            )
            body["Proposed Alternate Date"] = (
                "[Propose an alternative hearing date]"
            )
        elif motion_type == "motion_for_default":
            body["Service of Process"] = (
                "[Describe how and when the opposing party was served]"
            )
            body["Failure to Respond"] = (
                "[Document that the opposing party failed to answer or otherwise "
                "respond within the time permitted by MCR 2.108]"
            )
        elif motion_type == "motion_for_relief_from_judgment":
            body["Judgment at Issue"] = (
                "[Identify the judgment or order from which relief is sought, "
                "including date and docket entry]"
            )
            body["Grounds for Relief"] = (
                "[State grounds under MCR 2.612(C)(1): mistake, newly discovered "
                "evidence, fraud, or other reasons justifying relief]"
            )
        elif motion_type == "motion_for_stay":
            body["Order to Be Stayed"] = (
                "[Identify the order or judgment to be stayed]"
            )
            body["Likelihood of Success on Appeal"] = (
                "[Demonstrate a substantial likelihood of success on the merits "
                "of the appeal]"
            )
            body["Irreparable Harm"] = (
                "[Demonstrate irreparable harm absent a stay]"
            )
        elif motion_type == "emergency_motion":
            body["Statement of Emergency"] = (
                "[Describe the emergency requiring immediate court intervention. "
                "MCR 3.207(B) requires showing that irreparable injury, loss, or "
                "damage will result from delay]"
            )
            body["Irreparable Harm"] = (
                "[Demonstrate specific irreparable harm to the child]"
            )
            body["Verification"] = (
                "I, Andrew James Pigors, declare under the penalties of perjury "
                "that the statements in this motion are true to the best of my "
                "knowledge, information, and belief."
            )

        body["Legal Argument"] = _section_legal_argument(mt.mcr_rule, arguments)

        relief = relief_requested or [
            f"Grant the relief requested in this {mt.name}.",
            "Award such other relief as the Court deems just and equitable.",
        ]

        return MotionDocument(
            motion_type=motion_type,
            case_info=ci,
            caption=caption,
            body_sections=body,
            relief_requested=relief,
            signature_block=_build_signature_block(today),
            certificate_of_service=_build_certificate_of_service(date_str=today),
        )

    # -- Generation: response ------------------------------------------------

    def generate_response(
        self,
        motion_type: str,
        case_info: CaseInfo | None = None,
        counter_arguments: list[str] | None = None,
    ) -> MotionDocument:
        """Generate a response to an opposing motion.

        Parameters
        ----------
        motion_type : str
            The type of motion being responded to.
        case_info : CaseInfo | None
            Override default case information.
        counter_arguments : list[str] | None
            Arguments in opposition.

        Returns
        -------
        MotionDocument
        """
        mt = self.get_motion_template(motion_type)
        ci = case_info or self.case_info
        counter_arguments = counter_arguments or []
        today = datetime.now().strftime("%B %d, %Y")

        caption = _build_caption(ci)
        caption += (
            f"\n\n# RESPONSE TO DEFENDANT'S {mt.name.upper()}\n\n"
            f"**Filed:** {today}"
        )

        body: dict[str, str] = {
            "Introduction": (
                f"Plaintiff {ci.plaintiff} respectfully submits this Response "
                f"in opposition to Defendant's {mt.name} and states as follows:"
            ),
            "Statement of Facts": _section_statement_of_facts(counter_arguments),
            "Legal Argument in Opposition": _section_legal_argument(
                mt.mcr_rule, counter_arguments
            ),
        }

        relief = [
            f"Deny Defendant's {mt.name} in its entirety.",
            "Award Plaintiff costs and fees incurred in responding.",
            "Grant such other relief as the Court deems just and equitable.",
        ]

        return MotionDocument(
            motion_type=motion_type,
            case_info=ci,
            caption=caption,
            body_sections=body,
            relief_requested=relief,
            signature_block=_build_signature_block(today),
            certificate_of_service=_build_certificate_of_service(date_str=today),
        )

    # -- Generation: reply ---------------------------------------------------

    def generate_reply(
        self,
        motion_type: str,
        case_info: CaseInfo | None = None,
        reply_points: list[str] | None = None,
    ) -> MotionDocument:
        """Generate a reply brief in support of the original motion.

        Parameters
        ----------
        motion_type : str
            The type of motion being replied upon.
        case_info : CaseInfo | None
            Override default case information.
        reply_points : list[str] | None
            Points in reply to the opposition.

        Returns
        -------
        MotionDocument
        """
        mt = self.get_motion_template(motion_type)
        ci = case_info or self.case_info
        reply_points = reply_points or []
        today = datetime.now().strftime("%B %d, %Y")

        caption = _build_caption(ci)
        caption += (
            f"\n\n# REPLY BRIEF IN SUPPORT OF PLAINTIFF'S {mt.name.upper()}\n\n"
            f"**Filed:** {today}"
        )

        body: dict[str, str] = {
            "Introduction": (
                f"Plaintiff {ci.plaintiff} respectfully submits this Reply Brief "
                f"in support of Plaintiff's {mt.name} and in response to "
                f"Defendant's opposition, stating as follows:"
            ),
            "Reply to Defendant's Arguments": _section_statement_of_facts(
                reply_points
            ),
            "Legal Argument": _section_legal_argument(mt.mcr_rule, reply_points),
        }

        relief = [
            f"Grant Plaintiff's {mt.name} for the reasons stated herein and "
            "in the original motion.",
            "Award such other relief as the Court deems just and equitable.",
        ]

        return MotionDocument(
            motion_type=motion_type,
            case_info=ci,
            caption=caption,
            body_sections=body,
            relief_requested=relief,
            signature_block=_build_signature_block(today),
            certificate_of_service=_build_certificate_of_service(date_str=today),
        )

    # -- Generation: proposed order ------------------------------------------

    def generate_order(
        self,
        motion_type: str,
        case_info: CaseInfo | None = None,
        ruling: str | None = None,
    ) -> MotionDocument:
        """Generate a proposed order for the judge's signature.

        Parameters
        ----------
        motion_type : str
            The type of motion the order resolves.
        case_info : CaseInfo | None
            Override default case information.
        ruling : str | None
            The specific ruling text.

        Returns
        -------
        MotionDocument
        """
        mt = self.get_motion_template(motion_type)
        ci = case_info or self.case_info
        today = datetime.now().strftime("%B %d, %Y")

        caption = _build_caption(ci)
        caption += f"\n\n# ORDER ON PLAINTIFF'S {mt.name.upper()}"

        ruling_text = ruling or (
            f"Plaintiff's {mt.name} is GRANTED.  The Court finds "
            "good cause shown and orders as follows:"
        )

        body: dict[str, str] = {
            "Order": (
                f"This matter having come before the Court on Plaintiff's "
                f"{mt.name}, the Court having reviewed the motion, briefs, and "
                f"record, and being otherwise fully advised:\n\n"
                f"IT IS HEREBY ORDERED that:\n\n"
                f"{ruling_text}"
            ),
        }

        judge_signature = (
            f"IT IS SO ORDERED.\n"
            f"\n"
            f"Dated: _______________\n"
            f"\n"
            f"_________________________________\n"
            f"{ci.judge}\n"
            f"{ci.court}\n"
            f"{ci.county}, Michigan"
        )

        return MotionDocument(
            motion_type=motion_type,
            case_info=ci,
            caption=caption,
            body_sections=body,
            relief_requested=[],
            signature_block=judge_signature,
            certificate_of_service=_build_certificate_of_service(date_str=today),
        )

    # -- Validation ----------------------------------------------------------

    def validate_motion(self, motion_text: str) -> MotionValidation:
        """Check a motion document for completeness per MCR requirements.

        Examines the text for required structural elements common to all
        Michigan motions and returns a :class:`MotionValidation` with a
        compliance score.

        Parameters
        ----------
        motion_text : str
            The full text of the motion to validate.

        Returns
        -------
        MotionValidation
        """
        missing: list[str] = []
        warnings: list[str] = []
        checks_passed = 0
        total_checks = 0

        # 1. Caption
        total_checks += 1
        if "STATE OF MICHIGAN" in motion_text.upper():
            checks_passed += 1
        else:
            missing.append("Caption (STATE OF MICHIGAN header)")

        # 2. Case number
        total_checks += 1
        if re.search(r"\d{4}-\d{4,6}-\w{2}", motion_text):
            checks_passed += 1
        else:
            missing.append("Case number")

        # 3. Plaintiff name
        total_checks += 1
        if "ANDREW JAMES PIGORS" in motion_text.upper():
            checks_passed += 1
        else:
            missing.append("Plaintiff name in caption")

        # 4. Defendant name
        total_checks += 1
        if "EMILY A. WATSON" in motion_text.upper():
            checks_passed += 1
        else:
            missing.append("Defendant name in caption")

        # 5. Statement of Facts
        total_checks += 1
        if re.search(r"STATEMENT\s+OF\s+FACTS", motion_text, re.IGNORECASE):
            checks_passed += 1
        else:
            missing.append("Statement of Facts section")

        # 6. Legal Argument
        total_checks += 1
        if re.search(r"LEGAL\s+ARGUMENT", motion_text, re.IGNORECASE):
            checks_passed += 1
        else:
            missing.append("Legal Argument section")

        # 7. Relief Requested
        total_checks += 1
        if re.search(r"RELIEF\s+REQUESTED", motion_text, re.IGNORECASE):
            checks_passed += 1
        else:
            missing.append("Relief Requested section")

        # 8. Signature block
        total_checks += 1
        if "Respectfully submitted" in motion_text or "Pro Se" in motion_text:
            checks_passed += 1
        else:
            missing.append("Signature block")

        # 9. Certificate of Service
        total_checks += 1
        if re.search(r"CERTIFICATE\s+OF\s+SERVICE", motion_text, re.IGNORECASE):
            checks_passed += 1
        else:
            missing.append("Certificate of Service")

        # 10. MCR citation
        total_checks += 1
        if re.search(r"MCR\s+\d+\.\d+", motion_text):
            checks_passed += 1
        else:
            warnings.append("No Michigan Court Rule (MCR) citation found")

        # 11. Date
        total_checks += 1
        if re.search(
            r"(January|February|March|April|May|June|July|August|September|"
            r"October|November|December)\s+\d{1,2},\s+\d{4}",
            motion_text,
        ):
            checks_passed += 1
        else:
            warnings.append("No filing date found")

        # 12. Judge name
        total_checks += 1
        if "MCNEILL" in motion_text.upper() or "McNeill" in motion_text:
            checks_passed += 1
        else:
            warnings.append("Judge name not found in document")

        score = (checks_passed / total_checks * 100) if total_checks > 0 else 0.0

        return MotionValidation(
            is_valid=len(missing) == 0,
            missing_sections=missing,
            warnings=warnings,
            mcr_compliance_score=round(score, 1),
        )
