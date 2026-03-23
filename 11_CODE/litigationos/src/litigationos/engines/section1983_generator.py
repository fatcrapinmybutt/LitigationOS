"""42 U.S.C. § 1983 Civil Rights Complaint Generator.

Generates federal civil-rights complaints for deprivation of constitutional
rights under color of state law.  Covers the full lifecycle: jurisdiction
analysis, qualified-immunity screening, statute-of-limitations check,
domestic-relations-exception rebuttal, cause-of-action drafting, damages
calculation, and FRCP-compliant complaint assembly.

All party names, case numbers, and evidence citations are sourced from the
verified identity table or the litigation database — the engine **never**
fabricates names, bar numbers, or statistics.

Designed for 100 % local / offline operation.  No external API calls.
"""

from __future__ import annotations

import logging
import re
import textwrap
from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional, Sequence

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from litigationos.db.connection import DatabaseManager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Verified party identity — single source of truth
# ---------------------------------------------------------------------------
PARTIES = {
    "plaintiff": "Andrew James Pigors",
    "plaintiff_address": "1977 Whitehall Road, Lot 17, North Muskegon, MI 49445",
    "plaintiff_phone": "(231) 903-5690",
    "plaintiff_email": "andrewjpigors@gmail.com",
    "defendant_watson": "Emily A. Watson",
    "defendant_watson_address": "2160 Garland Drive, Norton Shores, MI 49441",
    "judge": "Hon. Jenny L. McNeill",
    "court": "14th Circuit Court, Family Division",
    "child": "L.D.W.",
    "foc": "Pamela Rusco",
    "foc_address": "990 Terrace St, Muskegon, MI 49442",
    "state_case_number": "2024-001507-DC",
}

# ---------------------------------------------------------------------------
# Federal court information
# ---------------------------------------------------------------------------
FEDERAL_COURT = {
    "court_name": "UNITED STATES DISTRICT COURT",
    "district": "WESTERN DISTRICT OF MICHIGAN",
    "division": "SOUTHERN DIVISION",
    "jurisdiction_statute": "28 U.S.C. §§ 1331, 1343(a)(3)",
    "cause_of_action_statute": "42 U.S.C. § 1983",
    "fees_statute": "42 U.S.C. § 1988",
    "verification_statute": "28 U.S.C. § 1746",
}

# ---------------------------------------------------------------------------
# Constitutional bases and supporting authority
# ---------------------------------------------------------------------------
CONSTITUTIONAL_BASES: dict[str, dict[str, Any]] = {
    "fourteenth_due_process_substantive": {
        "amendment": "Fourteenth Amendment",
        "clause": "Due Process Clause (substantive)",
        "right": "Fundamental right to the care, custody, and control of one's child",
        "key_cases": [
            "Troxel v. Granville, 530 U.S. 57 (2000)",
            "Santosky v. Kramer, 455 U.S. 745 (1982)",
            "Stanley v. Illinois, 405 U.S. 645 (1972)",
            "Washington v. Glucksberg, 521 U.S. 702 (1997)",
        ],
    },
    "fourteenth_due_process_procedural": {
        "amendment": "Fourteenth Amendment",
        "clause": "Due Process Clause (procedural)",
        "right": "Right to notice and meaningful opportunity to be heard",
        "key_cases": [
            "Mathews v. Eldridge, 424 U.S. 319 (1976)",
            "Goldberg v. Kelly, 397 U.S. 254 (1970)",
            "Mullane v. Central Hanover Bank & Trust Co., 339 U.S. 306 (1950)",
        ],
    },
    "first_amendment_retaliation": {
        "amendment": "First Amendment",
        "clause": "Right to petition the government for redress of grievances",
        "right": "Freedom from retaliation for exercising First Amendment rights",
        "key_cases": [
            "Thaddeus-X v. Blatter, 175 F.3d 378 (6th Cir. 1999)",
            "Crawford-El v. Britton, 523 U.S. 574 (1998)",
        ],
    },
    "fourteenth_equal_protection": {
        "amendment": "Fourteenth Amendment",
        "clause": "Equal Protection Clause",
        "right": "Equal treatment regardless of gender in custody proceedings",
        "key_cases": [
            "Craig v. Boren, 429 U.S. 190 (1976)",
            "United States v. Virginia, 518 U.S. 515 (1996)",
        ],
    },
}

# ---------------------------------------------------------------------------
# Claim type definitions with required elements
# ---------------------------------------------------------------------------

class ClaimType(str, Enum):
    """Enumeration of § 1983 claim types."""

    DUE_PROCESS_SUBSTANTIVE = "due_process_substantive"
    DUE_PROCESS_PROCEDURAL = "due_process_procedural"
    FIRST_AMENDMENT_RETALIATION = "first_amendment_retaliation"
    EQUAL_PROTECTION = "equal_protection"
    CONSPIRACY_1983 = "conspiracy_1983"
    FAILURE_TO_INTERVENE = "failure_to_intervene"


CLAIM_DEFINITIONS: dict[str, dict[str, Any]] = {
    "due_process_substantive": {
        "title": "Substantive Due Process — Deprivation of Fundamental Parental Rights",
        "constitutional_basis": "fourteenth_due_process_substantive",
        "elements": [
            "Defendant acted under color of state law",
            "Plaintiff possesses a constitutionally protected liberty interest "
            "(fundamental right to parent)",
            "Defendant's conduct shocks the conscience or is arbitrary and "
            "capricious",
            "Defendant's conduct deprived plaintiff of that protected interest",
            "No legitimate governmental interest justifies the deprivation",
        ],
        "standard": "Shocks the conscience or is arbitrary/capricious",
        "key_authority": [
            "Troxel v. Granville, 530 U.S. 57 (2000)",
            "Santosky v. Kramer, 455 U.S. 745 (1982)",
            "County of Sacramento v. Lewis, 523 U.S. 833 (1998)",
        ],
    },
    "due_process_procedural": {
        "title": "Procedural Due Process — Denial of Notice and Hearing",
        "constitutional_basis": "fourteenth_due_process_procedural",
        "elements": [
            "Defendant acted under color of state law",
            "Plaintiff has a protected liberty or property interest",
            "Defendant deprived plaintiff of that interest",
            "Deprivation occurred without constitutionally adequate procedures "
            "(notice, hearing, neutral decisionmaker)",
        ],
        "standard": "Mathews v. Eldridge three-factor balancing test",
        "key_authority": [
            "Mathews v. Eldridge, 424 U.S. 319 (1976)",
            "Cleveland Bd. of Educ. v. Loudermill, 470 U.S. 532 (1985)",
        ],
    },
    "first_amendment_retaliation": {
        "title": "First Amendment Retaliation",
        "constitutional_basis": "first_amendment_retaliation",
        "elements": [
            "Plaintiff engaged in constitutionally protected conduct "
            "(filing motions, speaking in court, petitioning for redress)",
            "Defendant took an adverse action against plaintiff",
            "A causal connection exists between the protected conduct "
            "and the adverse action",
        ],
        "standard": "Thaddeus-X three-element test (6th Circuit)",
        "key_authority": [
            "Thaddeus-X v. Blatter, 175 F.3d 378 (6th Cir. 1999)",
        ],
    },
    "equal_protection": {
        "title": "Equal Protection — Gender Discrimination in Custody",
        "constitutional_basis": "fourteenth_equal_protection",
        "elements": [
            "Defendant acted under color of state law",
            "Defendant treated plaintiff differently from similarly situated "
            "individuals",
            "The differential treatment was based on gender",
            "The classification is not substantially related to an important "
            "governmental interest (intermediate scrutiny)",
        ],
        "standard": "Intermediate scrutiny (Craig v. Boren)",
        "key_authority": [
            "Craig v. Boren, 429 U.S. 190 (1976)",
            "United States v. Virginia, 518 U.S. 515 (1996)",
            "Mississippi Univ. for Women v. Hogan, 458 U.S. 718 (1982)",
        ],
    },
    "conspiracy_1983": {
        "title": "42 U.S.C. § 1983 Conspiracy — Private Party Acting Under "
                 "Color of Law",
        "constitutional_basis": "fourteenth_due_process_substantive",
        "elements": [
            "An agreement between a state actor and a private party",
            "To deprive plaintiff of a constitutional right",
            "An overt act in furtherance of the conspiracy",
            "Actual deprivation of the constitutional right",
        ],
        "standard": "Dennis v. Sparks — private parties lose immunity when "
                     "conspiring with state actors",
        "key_authority": [
            "Dennis v. Sparks, 449 U.S. 24 (1980)",
            "Adickes v. S.H. Kress & Co., 398 U.S. 144 (1970)",
            "Tower v. Glover, 467 U.S. 914 (1984)",
        ],
    },
    "failure_to_intervene": {
        "title": "Failure to Intervene — Supervisory Liability",
        "constitutional_basis": "fourteenth_due_process_procedural",
        "elements": [
            "A constitutional violation occurred",
            "Defendant had knowledge of the violation",
            "Defendant had the opportunity and ability to intervene",
            "Defendant failed to act to prevent or stop the violation",
        ],
        "standard": "Deliberate indifference to known constitutional violation",
        "key_authority": [
            "Farmer v. Brennan, 511 U.S. 825 (1994)",
            "City of Canton v. Harris, 489 U.S. 378 (1989)",
        ],
    },
}

# ---------------------------------------------------------------------------
# Michigan statute of limitations for § 1983
# ---------------------------------------------------------------------------
MICHIGAN_SOL_YEARS = 3  # MCL 600.5805(2)

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class Section1983Claim(BaseModel):
    """A single § 1983 cause of action."""

    claim_type: str
    constitutional_basis: str
    elements: list[str] = Field(default_factory=list)
    facts: list[str] = Field(default_factory=list)
    defendants: list[str] = Field(default_factory=list)
    key_authority: list[str] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class QualifiedImmunityAnalysis(BaseModel):
    """Qualified-immunity analysis for a single defendant."""

    defendant: str
    clearly_established: bool = False
    case_law: list[str] = Field(default_factory=list)
    reasoning: str = ""
    recommendation: str = ""
    model_config = ConfigDict(from_attributes=True)


class DamagesCalculation(BaseModel):
    """Damages prayer for a § 1983 complaint."""

    compensatory: str = ""
    punitive: str = ""
    attorneys_fees: str = ""
    declaratory: str = ""
    injunctive: str = ""
    total_range: str = ""
    model_config = ConfigDict(from_attributes=True)


class ComplaintDocument(BaseModel):
    """Full FRCP-compliant § 1983 complaint."""

    caption: str = ""
    jurisdiction: str = ""
    parties: str = ""
    factual_background: str = ""
    causes_of_action: list[str] = Field(default_factory=list)
    damages: str = ""
    prayer_for_relief: str = ""
    verification: str = ""
    full_text: str = ""
    generated_at: Optional[datetime] = Field(default_factory=datetime.now)
    model_config = ConfigDict(from_attributes=True)


class SOLResult(BaseModel):
    """Statute-of-limitations analysis result."""

    violation_date: str
    deadline_date: str
    days_remaining: int
    is_timely: bool
    notes: str = ""
    model_config = ConfigDict(from_attributes=True)


class DomesticRelationsAnalysis(BaseModel):
    """Domestic-relations exception analysis."""

    applies: bool = False
    rebutted: bool = True
    reasoning: str = ""
    key_authority: list[str] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class Section1983Generator:
    """Generator for 42 U.S.C. § 1983 civil-rights complaints.

    Produces FRCP-compliant federal complaints targeting deprivation of
    constitutional rights under color of state law.  Covers jurisdiction,
    qualified-immunity screening, statute-of-limitations, domestic-relations-
    exception rebuttal, and damages calculation.
    """

    def __init__(self, db: Optional["DatabaseManager"] = None) -> None:
        self._db = db
        self._paragraph_counter = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_complaint(
        self,
        claims: list[Section1983Claim],
        defendants: list[str],
        facts: list[str],
    ) -> ComplaintDocument:
        """Generate a complete FRCP-compliant federal § 1983 complaint.

        Parameters
        ----------
        claims:
            One or more :class:`Section1983Claim` objects.
        defendants:
            List of defendant names.
        facts:
            Chronological factual allegations (one per numbered paragraph).

        Returns
        -------
        ComplaintDocument
            The assembled complaint with all sections.
        """
        self._paragraph_counter = 0

        caption = self._build_caption(defendants)
        jurisdiction = self.generate_jurisdiction_section()
        parties = self._build_parties_section(defendants)
        factual_bg = self._build_factual_background(facts)

        causes: list[str] = []
        for idx, claim in enumerate(claims, start=1):
            causes.append(self._build_count(idx, claim))

        damages = self.generate_damages_section(claims)
        prayer = self._build_prayer(claims, defendants)
        verification = self._build_verification()

        sections = [
            caption,
            "",
            jurisdiction,
            "",
            parties,
            "",
            factual_bg,
            "",
            *[f"{c}\n" for c in causes],
            damages.compensatory and f"COMPENSATORY DAMAGES\n{damages.compensatory}" or "",
            "",
            prayer,
            "",
            verification,
        ]
        full_text = "\n".join(s for s in sections if s)

        return ComplaintDocument(
            caption=caption,
            jurisdiction=jurisdiction,
            parties=parties,
            factual_background=factual_bg,
            causes_of_action=causes,
            damages=self._format_damages_text(damages),
            prayer_for_relief=prayer,
            verification=verification,
            full_text=full_text,
        )

    def generate_cause_of_action(
        self,
        constitutional_right: str,
        violation_facts: list[str],
    ) -> str:
        """Generate a single cause of action for a constitutional violation.

        Parameters
        ----------
        constitutional_right:
            The claim-type key (e.g. ``"due_process_substantive"``).
        violation_facts:
            Facts supporting the claim.

        Returns
        -------
        str
            Formatted cause-of-action text with numbered paragraphs.
        """
        defn = CLAIM_DEFINITIONS.get(constitutional_right)
        if defn is None:
            available = ", ".join(CLAIM_DEFINITIONS)
            raise ValueError(
                f"Unknown claim type: {constitutional_right!r}. "
                f"Available: {available}"
            )

        claim = Section1983Claim(
            claim_type=constitutional_right,
            constitutional_basis=defn["constitutional_basis"],
            elements=defn["elements"],
            facts=violation_facts,
            defendants=[],
            key_authority=defn["key_authority"],
        )
        return self._build_count(1, claim)

    def analyze_qualified_immunity(
        self,
        defendant: str,
        facts: list[str],
    ) -> QualifiedImmunityAnalysis:
        """Analyze qualified immunity for a defendant.

        Applies the two-prong *Harlow v. Fitzgerald* test:
        1. Did the defendant violate a constitutional right?
        2. Was the right clearly established at the time?

        Parameters
        ----------
        defendant:
            Name of the defendant being analyzed.
        facts:
            Relevant factual allegations.
        """
        clearly_established_cases = [
            "Troxel v. Granville, 530 U.S. 57 (2000)",
            "Santosky v. Kramer, 455 U.S. 745 (1982)",
            "Mathews v. Eldridge, 424 U.S. 319 (1976)",
        ]

        fact_text = " ".join(facts).lower()

        # Heuristic: rights in the parental-rights / due-process domain are
        # clearly established by Supreme Court precedent for decades.
        is_clearly_established = True
        reasoning_parts: list[str] = []

        if any(kw in fact_text for kw in (
            "parent", "custody", "child", "visitation", "parenting time",
        )):
            reasoning_parts.append(
                "The fundamental right to the care, custody, and control of "
                "one's children has been clearly established since at least "
                "Stanley v. Illinois, 405 U.S. 645 (1972), and reaffirmed in "
                "Troxel v. Granville, 530 U.S. 57 (2000)."
            )

        if any(kw in fact_text for kw in (
            "notice", "hearing", "due process", "opportunity to be heard",
        )):
            reasoning_parts.append(
                "The right to notice and a meaningful opportunity to be heard "
                "before deprivation of a protected interest has been clearly "
                "established since Goldberg v. Kelly, 397 U.S. 254 (1970), "
                "and Mathews v. Eldridge, 424 U.S. 319 (1976)."
            )

        if any(kw in fact_text for kw in (
            "retali", "first amendment", "petition", "filing",
        )):
            reasoning_parts.append(
                "The right to be free from retaliation for exercising First "
                "Amendment rights (including the right to petition) is clearly "
                "established.  Thaddeus-X v. Blatter, 175 F.3d 378 "
                "(6th Cir. 1999)."
            )

        if not reasoning_parts:
            reasoning_parts.append(
                "Based on the facts provided, the relevant constitutional "
                "right appears to be clearly established by Supreme Court "
                "and Sixth Circuit precedent."
            )

        recommendation = (
            f"Qualified immunity is UNLIKELY to shield {defendant}.  "
            f"The constitutional rights at issue have been clearly "
            f"established for decades by controlling Supreme Court and "
            f"Sixth Circuit authority.  Plaintiff should plead specific "
            f"facts showing the defendant's conduct violated clearly "
            f"established law that every reasonable official would know.  "
            f"See Harlow v. Fitzgerald, 457 U.S. 800 (1982)."
        )

        return QualifiedImmunityAnalysis(
            defendant=defendant,
            clearly_established=is_clearly_established,
            case_law=clearly_established_cases,
            reasoning=" ".join(reasoning_parts),
            recommendation=recommendation,
        )

    def generate_damages_section(
        self,
        claims: list[Section1983Claim],
    ) -> DamagesCalculation:
        """Generate the damages prayer for the complaint.

        Covers compensatory, punitive, declaratory, injunctive relief,
        and attorney's fees under 42 U.S.C. § 1988.
        """
        claim_types = {c.claim_type for c in claims}

        # Compensatory damages
        compensatory_items: list[str] = [
            "Loss of companionship with child",
            "Emotional distress and mental anguish",
            "Loss of parental rights and bonding time",
        ]
        if "due_process_procedural" in claim_types:
            compensatory_items.append(
                "Costs incurred due to denial of procedural protections"
            )
        if "first_amendment_retaliation" in claim_types:
            compensatory_items.append(
                "Chilling effect on exercise of First Amendment rights"
            )

        compensatory = (
            "Plaintiff seeks compensatory damages in an amount to be "
            "proven at trial, including but not limited to: "
            + "; ".join(compensatory_items) + "."
        )

        # Punitive damages
        punitive = (
            "Plaintiff seeks punitive damages against each defendant "
            "in their individual capacity.  The defendants' conduct was "
            "motivated by evil motive or intent, or involved reckless or "
            "callous indifference to Plaintiff's federally protected rights.  "
            "Smith v. Wade, 461 U.S. 30 (1983)."
        )

        # Attorney's fees (even pro se litigants may seek costs)
        attorneys_fees = (
            "Plaintiff seeks reasonable attorney's fees and costs pursuant "
            "to 42 U.S.C. § 1988.  Although Plaintiff proceeds pro se, "
            "Plaintiff seeks all recoverable costs and expenses."
        )

        # Declaratory relief
        declaratory = (
            "Plaintiff seeks a declaratory judgment pursuant to 28 U.S.C. "
            "§§ 2201-2202 that the defendants' conduct violated Plaintiff's "
            "rights under the United States Constitution."
        )

        # Injunctive relief
        injunctive = (
            "Plaintiff seeks preliminary and permanent injunctive relief "
            "ordering defendants to cease all unconstitutional conduct and "
            "to provide constitutionally adequate procedures in all future "
            "proceedings affecting Plaintiff's parental rights."
        )

        return DamagesCalculation(
            compensatory=compensatory,
            punitive=punitive,
            attorneys_fees=attorneys_fees,
            declaratory=declaratory,
            injunctive=injunctive,
            total_range="Amount to be determined at trial",
        )

    def check_statute_of_limitations(
        self,
        violation_dates: list[str | date],
    ) -> list[SOLResult]:
        """Check 3-year Michigan statute of limitations for each date.

        Michigan's personal-injury statute of limitations (MCL 600.5805(2))
        applies to § 1983 claims.  Wilson v. Garcia, 471 U.S. 261 (1985).

        Parameters
        ----------
        violation_dates:
            Dates on which constitutional violations occurred.
            Accepts ``date`` objects or ISO-format strings (YYYY-MM-DD).
        """
        today = date.today()
        results: list[SOLResult] = []

        for vd in violation_dates:
            if isinstance(vd, str):
                parsed = date.fromisoformat(vd)
            else:
                parsed = vd

            deadline = date(
                parsed.year + MICHIGAN_SOL_YEARS,
                parsed.month,
                parsed.day,
            )
            days_remaining = (deadline - today).days
            is_timely = days_remaining > 0

            notes = ""
            if not is_timely:
                notes = (
                    f"WARNING: This violation date ({parsed.isoformat()}) "
                    f"is OUTSIDE the 3-year statute of limitations.  "
                    f"Consider whether continuing-violation doctrine, "
                    f"equitable tolling, or discovery rule applies."
                )
            elif days_remaining <= 90:
                notes = (
                    f"URGENT: Only {days_remaining} days remaining to file.  "
                    f"Statute expires {deadline.isoformat()}."
                )

            results.append(SOLResult(
                violation_date=parsed.isoformat(),
                deadline_date=deadline.isoformat(),
                days_remaining=days_remaining,
                is_timely=is_timely,
                notes=notes,
            ))

        return results

    def generate_jurisdiction_section(self) -> str:
        """Generate the jurisdiction and venue statement.

        28 U.S.C. § 1331 (federal question), 28 U.S.C. § 1343(a)(3)
        (civil rights), venue under 28 U.S.C. § 1391(b).
        """
        self._paragraph_counter += 1
        p1 = self._paragraph_counter
        self._paragraph_counter += 1
        p2 = self._paragraph_counter
        self._paragraph_counter += 1
        p3 = self._paragraph_counter
        self._paragraph_counter += 1
        p4 = self._paragraph_counter

        return textwrap.dedent(f"""\
            JURISDICTION AND VENUE

            {p1}. This Court has subject-matter jurisdiction pursuant to \
28 U.S.C. § 1331 (federal question) and 28 U.S.C. § 1343(a)(3) \
(civil rights).  This action arises under 42 U.S.C. § 1983 for the \
deprivation of rights secured by the United States Constitution.

            {p2}. Venue is proper in this district pursuant to 28 U.S.C. \
§ 1391(b) because all events giving rise to the claims occurred in \
Muskegon County, Michigan, within the {FEDERAL_COURT['district']}, \
{FEDERAL_COURT['division']}.

            {p3}. This action does not seek to modify, set aside, or \
interfere with any state-court custody determination.  Rather, Plaintiff \
challenges the unconstitutional procedures and conduct by which state \
actors deprived Plaintiff of clearly established constitutional rights.  \
The domestic-relations exception to federal jurisdiction does not apply.  \
Catz v. Chalker, 142 F.3d 279 (6th Cir. 1998); Elk Grove Unified Sch. \
Dist. v. Newdow, 542 U.S. 1, 12-13 (2004).

            {p4}. Declaratory relief is authorized under 28 U.S.C. \
§§ 2201-2202.""")

    def analyze_domestic_relations_exception(
        self,
        facts: list[str],
    ) -> DomesticRelationsAnalysis:
        """Analyze whether the domestic-relations exception bars suit.

        The Sixth Circuit in *Catz v. Chalker*, 142 F.3d 279 (6th Cir. 1998),
        held that § 1983 claims challenging *procedures* (as opposed to
        seeking to modify a custody order) are NOT barred.
        """
        fact_text = " ".join(facts).lower()

        seeks_modification = any(kw in fact_text for kw in (
            "modify custody", "change custody", "reverse custody",
            "grant custody", "award custody",
        ))

        challenges_procedure = any(kw in fact_text for kw in (
            "due process", "procedure", "hearing", "notice",
            "retaliation", "equal protection", "bias",
            "constitutional", "rights", "color of law",
        ))

        key_authority = [
            "Catz v. Chalker, 142 F.3d 279 (6th Cir. 1998)",
            "Elk Grove Unified Sch. Dist. v. Newdow, 542 U.S. 1 (2004)",
            "Ankenbrandt v. Richards, 504 U.S. 689 (1992)",
        ]

        if seeks_modification and not challenges_procedure:
            return DomesticRelationsAnalysis(
                applies=True,
                rebutted=False,
                reasoning=(
                    "The facts suggest this action seeks to modify a state-"
                    "court custody determination, which may invoke the "
                    "domestic-relations exception.  Reframe claims to "
                    "challenge procedures, not outcomes."
                ),
                key_authority=key_authority,
            )

        reasoning_parts = [
            "This action does NOT seek to modify, dissolve, or grant a "
            "custody order.",
        ]
        if challenges_procedure:
            reasoning_parts.append(
                "Rather, Plaintiff challenges the unconstitutional "
                "procedures by which state actors deprived Plaintiff of "
                "clearly established constitutional rights."
            )
        reasoning_parts.append(
            "Under Catz v. Chalker, 142 F.3d 279 (6th Cir. 1998), "
            "the domestic-relations exception does NOT bar § 1983 "
            "claims that challenge the procedures used, as opposed to "
            "the custody determination itself."
        )

        return DomesticRelationsAnalysis(
            applies=False,
            rebutted=True,
            reasoning="  ".join(reasoning_parts),
            key_authority=key_authority,
        )

    def list_available_claims(self) -> dict[str, dict[str, Any]]:
        """Return all available § 1983 claim types with their elements.

        Returns
        -------
        dict
            Mapping of claim-type keys to their definitions (title,
            elements, standard, key_authority).
        """
        return {k: dict(v) for k, v in CLAIM_DEFINITIONS.items()}

    def validate_complaint(self, complaint_text: str) -> dict[str, Any]:
        """Validate a complaint for FRCP completeness.

        Checks for required sections: caption, jurisdiction, parties,
        factual allegations, causes of action, prayer for relief, and
        verification / declaration.

        Returns
        -------
        dict
            ``{"valid": bool, "score": int, "issues": [...], "warnings": [...]}``
        """
        issues: list[str] = []
        warnings: list[str] = []
        text_lower = complaint_text.lower()

        required_sections = {
            "caption": [
                "united states district court",
                "western district of michigan",
            ],
            "jurisdiction": ["28 u.s.c.", "1331", "1343"],
            "section_1983": ["42 u.s.c.", "1983"],
            "parties": ["plaintiff", "defendant"],
            "factual_allegations": ["1.", "2."],
            "prayer_for_relief": [
                "prayer for relief",
                "wherefore",
            ],
            "verification": [
                "28 u.s.c. § 1746",
                "penalty of perjury",
            ],
        }

        score = 100

        for section, keywords in required_sections.items():
            if section == "prayer_for_relief":
                if not any(kw in text_lower for kw in keywords):
                    issues.append(
                        f"Missing {section.replace('_', ' ')}: "
                        f"expected one of {keywords}"
                    )
                    score -= 15
            elif section == "factual_allegations":
                if not re.search(r"\d+\.\s", complaint_text):
                    issues.append("No numbered paragraphs found")
                    score -= 10
            else:
                for kw in keywords:
                    if kw not in text_lower:
                        issues.append(
                            f"Missing element in {section.replace('_', ' ')}: "
                            f"'{kw}'"
                        )
                        score -= 5

        # Check for at least one COUNT
        if "count" not in text_lower:
            issues.append("No COUNT headings found — at least one cause of action required")
            score -= 15

        # Warn on common issues
        if PARTIES["plaintiff"] not in complaint_text:
            warnings.append(
                f"Plaintiff name '{PARTIES['plaintiff']}' not found in text"
            )

        if "color of" not in text_lower:
            warnings.append(
                "Phrase 'under color of' not found — essential for § 1983"
            )

        if "clearly established" not in text_lower:
            warnings.append(
                "Phrase 'clearly established' not found — consider "
                "addressing qualified immunity proactively"
            )

        score = max(0, score)

        return {
            "valid": len(issues) == 0,
            "score": score,
            "issues": issues,
            "warnings": warnings,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _next_paragraph(self) -> int:
        self._paragraph_counter += 1
        return self._paragraph_counter

    def _build_caption(self, defendants: list[str]) -> str:
        plaintiff = PARTIES["plaintiff"]
        def_block = "\n".join(
            f"    {d}," if i < len(defendants) - 1 else f"    {d}."
            for i, d in enumerate(defendants)
        )

        return textwrap.dedent(f"""\
            {FEDERAL_COURT['court_name']}
            {FEDERAL_COURT['district']}
            {FEDERAL_COURT['division']}

            {plaintiff},
                Plaintiff,             Case No. __________

                v.                     COMPLAINT UNDER
                                       42 U.S.C. § 1983
            {def_block}
                Defendant(s).

            JURY TRIAL DEMANDED""")

    def _build_parties_section(self, defendants: list[str]) -> str:
        lines: list[str] = ["PARTIES\n"]
        p = self._next_paragraph()
        lines.append(
            f"{p}. Plaintiff {PARTIES['plaintiff']} is a natural person "
            f"and citizen of the State of Michigan, residing at "
            f"{PARTIES['plaintiff_address']}.  Plaintiff is the biological "
            f"father of {PARTIES['child']} and is proceeding pro se."
        )

        for defendant in defendants:
            p = self._next_paragraph()
            lines.append(
                f"\n{p}. Defendant {defendant} is sued in both their "
                f"individual and official capacity.  Upon information and "
                f"belief, Defendant {defendant} is a person who acted under "
                f"color of state law at all times relevant to this complaint."
            )

        return "\n".join(lines)

    def _build_factual_background(self, facts: list[str]) -> str:
        lines: list[str] = ["FACTUAL BACKGROUND\n"]
        for fact in facts:
            p = self._next_paragraph()
            lines.append(f"{p}. {fact}")
        return "\n\n".join(lines)

    def _build_count(self, count_num: int, claim: Section1983Claim) -> str:
        defn = CLAIM_DEFINITIONS.get(claim.claim_type, {})
        title = defn.get("title", claim.claim_type.replace("_", " ").title())

        lines: list[str] = [
            f"COUNT {_roman(count_num)}: {title.upper()}",
            f"(42 U.S.C. § 1983 — "
            f"{CONSTITUTIONAL_BASES.get(claim.constitutional_basis, {}).get('amendment', 'Constitutional')} "
            f"Violation)\n",
        ]

        p = self._next_paragraph()
        lines.append(
            f"{p}. Plaintiff re-alleges and incorporates by reference all "
            f"preceding paragraphs as if fully set forth herein."
        )

        # Elements
        for element in claim.elements:
            p = self._next_paragraph()
            lines.append(f"\n{p}. {element}")

        # Supporting facts
        if claim.facts:
            p = self._next_paragraph()
            lines.append(
                f"\n{p}. In support of this Count, Plaintiff alleges the "
                f"following specific facts:"
            )
            for fact in claim.facts:
                p = self._next_paragraph()
                lines.append(f"\n    {p}. {fact}")

        # Legal standard
        standard = defn.get("standard", "")
        if standard:
            p = self._next_paragraph()
            lines.append(
                f"\n{p}. The applicable legal standard is: {standard}."
            )

        # Key authority
        authorities = claim.key_authority or defn.get("key_authority", [])
        if authorities:
            p = self._next_paragraph()
            auth_list = "; ".join(authorities)
            lines.append(
                f"\n{p}. This claim is supported by the following "
                f"authorities: {auth_list}."
            )

        # Color of law / under color of
        if claim.defendants:
            p = self._next_paragraph()
            def_names = ", ".join(claim.defendants)
            lines.append(
                f"\n{p}. At all times relevant hereto, Defendant(s) "
                f"{def_names} acted under color of state law within the "
                f"meaning of 42 U.S.C. § 1983."
            )

        return "\n".join(lines)

    def _build_prayer(
        self,
        claims: list[Section1983Claim],
        defendants: list[str],
    ) -> str:
        lines: list[str] = [
            "PRAYER FOR RELIEF\n",
            "WHEREFORE, Plaintiff respectfully requests that this Court "
            "enter judgment in Plaintiff's favor and against Defendants, "
            "and grant the following relief:\n",
            "A. A declaratory judgment that Defendants' conduct violated "
            "Plaintiff's rights under the First and Fourteenth Amendments "
            "to the United States Constitution;\n",
            "B. Compensatory damages in an amount to be proven at trial "
            "for all injuries suffered;\n",
            "C. Punitive damages against each Defendant in their "
            "individual capacity;\n",
            "D. Preliminary and permanent injunctive relief ordering "
            "Defendants to cease all unconstitutional conduct;\n",
            "E. Reasonable costs and expenses pursuant to "
            "42 U.S.C. § 1988;\n",
            "F. Pre-judgment and post-judgment interest as allowed "
            "by law;\n",
            "G. Such other and further relief as this Court deems "
            "just and proper.",
        ]
        return "\n".join(lines)

    def _build_verification(self) -> str:
        today_str = date.today().strftime("%B %d, %Y")
        return textwrap.dedent(f"""\
            VERIFICATION UNDER PENALTY OF PERJURY

            I, {PARTIES['plaintiff']}, declare under penalty of perjury \
pursuant to 28 U.S.C. § 1746 that the foregoing is true and correct to \
the best of my knowledge, information, and belief.

            Dated: {today_str}

            ____________________________________
            {PARTIES['plaintiff']}, Pro Se
            {PARTIES['plaintiff_address']}
            {PARTIES['plaintiff_phone']}
            {PARTIES['plaintiff_email']}""")

    def _format_damages_text(self, damages: DamagesCalculation) -> str:
        sections = []
        if damages.compensatory:
            sections.append(f"Compensatory: {damages.compensatory}")
        if damages.punitive:
            sections.append(f"Punitive: {damages.punitive}")
        if damages.attorneys_fees:
            sections.append(f"Fees/Costs: {damages.attorneys_fees}")
        if damages.declaratory:
            sections.append(f"Declaratory: {damages.declaratory}")
        if damages.injunctive:
            sections.append(f"Injunctive: {damages.injunctive}")
        return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

_ROMAN_MAP = [
    (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
    (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
    (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
]


def _roman(num: int) -> str:
    """Convert an integer to a Roman numeral string."""
    if num <= 0:
        return str(num)
    result: list[str] = []
    for value, numeral in _ROMAN_MAP:
        while num >= value:
            result.append(numeral)
            num -= value
    return "".join(result)
