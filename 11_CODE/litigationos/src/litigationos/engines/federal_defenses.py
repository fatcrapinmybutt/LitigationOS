"""Rooker-Feldman & Domestic Relations Exception Defense Prep Engine.

Pre-built analysis and counter-arguments for anticipated federal defenses
in a 42 U.S.C. § 1983 action (WDMI) challenging unconstitutional conduct
by state judges and court actors.  Covers Rooker-Feldman, the domestic
relations exception, judicial immunity, qualified immunity, Younger
abstention, and Heck v. Humphrey.

All party names, case numbers, and evidence references are sourced from
the verified identity table — the engine **never** fabricates names,
bar numbers, or statistics.

Designed for 100 % local / offline operation.  No external API calls.
"""

from __future__ import annotations

import logging
import textwrap
from datetime import datetime
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
    "judge_mcneill": "Hon. Jenny L. McNeill",
    "court": "14th Circuit Court, Family Division",
    "child": "L.D.W.",
    "state_case_number": "2024-001507-DC",
}

FEDERAL_COURT = {
    "court_name": "UNITED STATES DISTRICT COURT",
    "district": "WESTERN DISTRICT OF MICHIGAN",
    "division": "SOUTHERN DIVISION",
    "jurisdiction_statute": "28 U.S.C. §§ 1331, 1343(a)(3)",
    "cause_of_action_statute": "42 U.S.C. § 1983",
}


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class StrengthAssessment(str, Enum):
    """How likely a defense is to succeed against the plaintiff's claims."""

    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    INAPPLICABLE = "inapplicable"


class DefenseCategory(str, Enum):
    """Broad classification of the federal defense."""

    JURISDICTIONAL = "jurisdictional"
    ABSTENTION = "abstention"
    IMMUNITY = "immunity"
    PRECLUSION = "preclusion"


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class CaseAuthority(BaseModel):
    """A single judicial authority relevant to a defense analysis."""

    name: str = Field(..., description="Short case name")
    citation: str = Field(..., description="Full reporter citation")
    holding: str = Field(..., description="Key holding or rule extracted")
    relevance_to_pigors: str = Field(
        ...,
        description="How this authority supports or undermines the defense "
        "in the Pigors v. McNeill context",
    )

    model_config = ConfigDict(from_attributes=True)


class DefenseAnalysis(BaseModel):
    """Complete analysis of one anticipated federal defense."""

    defense_name: str = Field(..., description="Name of the defense doctrine")
    category: DefenseCategory = Field(
        ..., description="Jurisdictional, abstention, immunity, or preclusion"
    )
    definition: str = Field(..., description="Plain-language definition")
    elements: list[str] = Field(
        default_factory=list,
        description="Elements the defendant must prove for the defense to apply",
    )
    counter_arguments: list[str] = Field(
        default_factory=list,
        description="Plaintiff's arguments why the defense fails here",
    )
    key_cases: list[CaseAuthority] = Field(
        default_factory=list,
        description="Authorities supporting the counter-arguments",
    )
    strength_assessment: StrengthAssessment = Field(
        ...,
        description="Likelihood the defense succeeds against plaintiff's §1983 claims",
    )
    assessment_rationale: str = Field(
        default="",
        description="Explanation of the strength assessment",
    )
    created_at: Optional[datetime] = Field(default_factory=datetime.now)

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Authority database (local, no network)
# ---------------------------------------------------------------------------

_ROOKER_FELDMAN_AUTHORITIES: list[CaseAuthority] = [
    CaseAuthority(
        name="D.C. Court of Appeals v. Feldman",
        citation="460 U.S. 462 (1983)",
        holding=(
            "Federal district courts lack jurisdiction to review final "
            "judgments of state courts; appellate review of state court "
            "decisions lies exclusively with the U.S. Supreme Court under "
            "28 U.S.C. § 1257."
        ),
        relevance_to_pigors=(
            "Establishes the doctrine, but Andrew's claims challenge the "
            "PROCESS and conduct of the judges, not the custody judgment "
            "itself.  Feldman is distinguishable."
        ),
    ),
    CaseAuthority(
        name="Rooker v. Fidelity Trust Co.",
        citation="263 U.S. 413 (1923)",
        holding=(
            "A federal district court may not exercise appellate jurisdiction "
            "over state court judgments."
        ),
        relevance_to_pigors=(
            "Andrew is not asking the federal court to reverse a state "
            "judgment; he seeks damages for independent constitutional "
            "violations that occurred during the proceedings."
        ),
    ),
    CaseAuthority(
        name="Exxon Mobil Corp. v. Saudi Basic Industries Corp.",
        citation="544 U.S. 280 (2005)",
        holding=(
            "Rooker-Feldman is confined to cases brought by state-court "
            "losers complaining of injuries caused by state-court judgments "
            "rendered before the federal suit commenced and inviting federal "
            "appellate review of those judgments.  The doctrine is narrow."
        ),
        relevance_to_pigors=(
            "The Supreme Court's narrow construction favors Andrew: his "
            "§ 1983 claims allege injuries caused by judicial conduct "
            "(denial of due process, ex parte contacts, biased proceedings) "
            "— not by the state-court judgment itself."
        ),
    ),
    CaseAuthority(
        name="Skinner v. Switzer",
        citation="562 U.S. 521 (2011)",
        holding=(
            "A § 1983 suit challenging the process used in state court, "
            "rather than the outcome, is not barred by Rooker-Feldman."
        ),
        relevance_to_pigors=(
            "Directly supports Andrew's position: his claims target the "
            "unconstitutional process (lack of notice, biased procedures, "
            "ex parte communications) rather than the custody outcome."
        ),
    ),
    CaseAuthority(
        name="McCormick v. Braverman",
        citation="451 F.3d 382 (6th Cir. 2006)",
        holding=(
            "Rooker-Feldman does not bar § 1983 claims that are independent "
            "of the state court judgment even when those claims are related "
            "to the state proceedings."
        ),
        relevance_to_pigors=(
            "Sixth Circuit authority confirming independent federal claims "
            "survive Rooker-Feldman even when they arise from the same "
            "state-court proceedings."
        ),
    ),
]

_DOMESTIC_RELATIONS_AUTHORITIES: list[CaseAuthority] = [
    CaseAuthority(
        name="Ankenbrandt v. Richards",
        citation="504 U.S. 689 (1992)",
        holding=(
            "The domestic relations exception divests federal courts of "
            "jurisdiction only over cases involving the issuance of a "
            "divorce, alimony, or child custody decree.  Tort claims "
            "between family members remain cognizable in federal court."
        ),
        relevance_to_pigors=(
            "Andrew's § 1983 claims are tort-like constitutional claims, "
            "not requests for custody decrees.  Ankenbrandt explicitly "
            "permits such claims in federal court."
        ),
    ),
    CaseAuthority(
        name="Marshall v. Marshall",
        citation="547 U.S. 293 (2006)",
        holding=(
            "The domestic relations exception is a narrow exception that "
            "does not apply simply because a case touches on family matters."
        ),
        relevance_to_pigors=(
            "Reinforces narrowness: that the underlying dispute involves "
            "custody does not automatically trigger the exception when the "
            "federal claims are for constitutional violations."
        ),
    ),
    CaseAuthority(
        name="Elk Grove Unified School Dist. v. Newdow",
        citation="542 U.S. 1 (2004)",
        holding=(
            "Federal courts should exercise caution in family-law-related "
            "cases but are not categorically barred from adjudicating "
            "constitutional claims that arise in a domestic context."
        ),
        relevance_to_pigors=(
            "Even under a cautious approach, constitutional claims remain "
            "justiciable.  Andrew seeks damages and declaratory relief for "
            "due process violations — not a custody determination."
        ),
    ),
    CaseAuthority(
        name="Catz v. Chalker",
        citation="142 F.3d 279 (6th Cir. 1998)",
        holding=(
            "The domestic relations exception does not bar § 1983 claims "
            "alleging constitutional violations in domestic relations "
            "proceedings."
        ),
        relevance_to_pigors=(
            "Sixth Circuit precedent directly holding that § 1983 claims "
            "challenging unconstitutional conduct in family court are not "
            "barred by the domestic relations exception."
        ),
    ),
]

_JUDICIAL_IMMUNITY_AUTHORITIES: list[CaseAuthority] = [
    CaseAuthority(
        name="Stump v. Sparkman",
        citation="435 U.S. 349 (1978)",
        holding=(
            "A judge is absolutely immune from damages liability for "
            "judicial acts performed within jurisdiction, even if the "
            "act was erroneous, malicious, or in excess of authority."
        ),
        relevance_to_pigors=(
            "Creates the highest barrier.  However, immunity does not "
            "extend to acts taken in the clear absence of all "
            "jurisdiction, and declaratory/injunctive relief under "
            "§ 1983 remains available against judges."
        ),
    ),
    CaseAuthority(
        name="Mireles v. Waco",
        citation="502 U.S. 9 (1991)",
        holding=(
            "Judicial immunity is overcome in only two circumstances: "
            "(1) non-judicial actions and (2) actions taken in the "
            "complete absence of all jurisdiction."
        ),
        relevance_to_pigors=(
            "Andrew should argue that certain acts by McNeill were "
            "non-judicial (e.g., ex parte communications, failure to "
            "provide notice) or taken without jurisdiction (e.g., "
            "proceeding without proper service)."
        ),
    ),
    CaseAuthority(
        name="Pulliam v. Allen",
        citation="466 U.S. 522 (1984)",
        holding=(
            "Judicial immunity does not bar prospective injunctive relief "
            "under § 1983."
        ),
        relevance_to_pigors=(
            "Even if damages are barred, Andrew can seek declaratory "
            "and injunctive relief against ongoing constitutional "
            "violations by state court actors."
        ),
    ),
    CaseAuthority(
        name="Forrester v. White",
        citation="484 U.S. 219 (1988)",
        holding=(
            "Administrative and executive acts by judges (e.g., hiring, "
            "firing, internal management) are not protected by judicial "
            "immunity."
        ),
        relevance_to_pigors=(
            "If McNeill's actions (e.g., directing FOC investigations, "
            "coordinating with parties ex parte) are characterized as "
            "administrative rather than adjudicative, immunity may "
            "not attach."
        ),
    ),
]

_YOUNGER_ABSTENTION_AUTHORITIES: list[CaseAuthority] = [
    CaseAuthority(
        name="Younger v. Harris",
        citation="401 U.S. 37 (1971)",
        holding=(
            "Federal courts should abstain from interfering with ongoing "
            "state court proceedings when the state provides an adequate "
            "forum to raise federal claims."
        ),
        relevance_to_pigors=(
            "If state custody proceedings are still pending, defendants "
            "may invoke Younger.  Counter: Andrew's claims allege the "
            "state forum is itself constitutionally deficient — the "
            "bad-faith / harassment exception applies."
        ),
    ),
    CaseAuthority(
        name="Middlesex County Ethics Comm. v. Garden State Bar Ass'n",
        citation="457 U.S. 423 (1982)",
        holding=(
            "Three conditions for Younger abstention: (1) ongoing state "
            "proceeding, (2) important state interest, (3) adequate "
            "opportunity to raise federal claims in state court."
        ),
        relevance_to_pigors=(
            "Andrew can argue he lacks an adequate opportunity to raise "
            "federal constitutional claims in a state court that is "
            "itself the source of the constitutional violations."
        ),
    ),
    CaseAuthority(
        name="Kugler v. Helfant",
        citation="421 U.S. 117 (1975)",
        holding=(
            "Younger abstention does not apply when the state tribunal "
            "is biased or when bad faith and harassment are shown."
        ),
        relevance_to_pigors=(
            "If Andrew demonstrates that Judge McNeill's conduct "
            "constitutes bad faith or that the state forum is biased, "
            "the bad-faith exception to Younger applies."
        ),
    ),
]

_QUALIFIED_IMMUNITY_AUTHORITIES: list[CaseAuthority] = [
    CaseAuthority(
        name="Harlow v. Fitzgerald",
        citation="457 U.S. 800 (1982)",
        holding=(
            "Government officials performing discretionary functions are "
            "shielded from liability unless their conduct violates clearly "
            "established statutory or constitutional rights."
        ),
        relevance_to_pigors=(
            "Applies to non-judicial defendants (FOC, clerk, etc.).  "
            "Andrew must show the violated rights were clearly "
            "established at the time of the conduct."
        ),
    ),
    CaseAuthority(
        name="Ashcroft v. al-Kidd",
        citation="563 U.S. 731 (2011)",
        holding=(
            "Qualified immunity protects all but the plainly incompetent "
            "or those who knowingly violate the law."
        ),
        relevance_to_pigors=(
            "Counter: the right to notice and a hearing before deprivation "
            "of parental rights has been clearly established for decades "
            "(Mathews v. Eldridge, Santosky v. Kramer).  No reasonable "
            "official could believe otherwise."
        ),
    ),
]

_HECK_AUTHORITIES: list[CaseAuthority] = [
    CaseAuthority(
        name="Heck v. Humphrey",
        citation="512 U.S. 477 (1994)",
        holding=(
            "A § 1983 claim is barred if a judgment in favor of the "
            "plaintiff would necessarily imply the invalidity of a "
            "criminal conviction or sentence that has not been reversed."
        ),
        relevance_to_pigors=(
            "Only relevant if Andrew has a related criminal conviction "
            "(e.g., contempt resulting in incarceration).  If no criminal "
            "conviction is at issue, Heck is inapplicable.  Even if "
            "contempt is implicated, claims challenging the PROCESS "
            "(not the conviction itself) may survive."
        ),
    ),
    CaseAuthority(
        name="Spencer v. Kemna",
        citation="523 U.S. 1 (1998)",
        holding=(
            "Heck applies only when success on the § 1983 claim would "
            "necessarily demonstrate the invalidity of a conviction or "
            "sentence."
        ),
        relevance_to_pigors=(
            "Andrew's claims seek damages for process violations.  "
            "A finding that McNeill violated due process does not "
            "necessarily invalidate any contempt finding — it "
            "demonstrates the procedure was unconstitutional."
        ),
    ),
]


# ---------------------------------------------------------------------------
# Analysis functions
# ---------------------------------------------------------------------------

def analyze_rooker_feldman(claims: list[str] | None = None) -> DefenseAnalysis:
    """Analyze Rooker-Feldman doctrine applicability to Andrew's § 1983 claims.

    Args:
        claims: Optional list of specific claim descriptions.  If not
            provided, uses default § 1983 claims for Pigors v. McNeill.

    Returns:
        A ``DefenseAnalysis`` with elements, counter-arguments, and case
        authorities explaining why Rooker-Feldman likely does not bar the
        federal action.
    """
    if not claims:
        claims = [
            "Deprivation of parental rights without due process",
            "Ex parte communications and biased proceedings",
            "Failure to provide constitutionally adequate notice",
            "Retaliation for exercise of First Amendment rights",
        ]

    claim_label = "; ".join(claims)
    logger.info("Analyzing Rooker-Feldman for claims: %s", claim_label)

    return DefenseAnalysis(
        defense_name="Rooker-Feldman Doctrine",
        category=DefenseCategory.JURISDICTIONAL,
        definition=(
            "The Rooker-Feldman doctrine bars federal district courts from "
            "exercising appellate jurisdiction over state court judgments.  "
            "It derives from D.C. Court of Appeals v. Feldman, 460 U.S. 462 "
            "(1983) and Rooker v. Fidelity Trust Co., 263 U.S. 413 (1923)."
        ),
        elements=[
            (
                "The federal plaintiff lost in state court (state-court loser "
                "requirement)"
            ),
            (
                "The plaintiff's injuries were caused BY the state court "
                "judgment itself"
            ),
            (
                "The state court judgment was rendered BEFORE the federal "
                "suit was filed"
            ),
            (
                "The federal suit effectively invites the district court to "
                "review and reject the state court judgment (appellate review "
                "requirement)"
            ),
        ],
        counter_arguments=[
            (
                "INDEPENDENT FEDERAL CLAIMS: Andrew's § 1983 claims are "
                "independent of the state custody judgment.  He alleges "
                "constitutional violations in how the proceedings were "
                "conducted, not that the custody outcome was wrong.  "
                "Exxon Mobil, 544 U.S. at 284 (doctrine is 'narrow')."
            ),
            (
                "CHALLENGING PROCESS, NOT JUDGMENT: Under Skinner v. "
                "Switzer, 562 U.S. 521 (2011), a § 1983 action challenging "
                "the constitutionality of the process used — rather than "
                "seeking reversal of the judgment — is not barred."
            ),
            (
                "CONSTITUTIONAL VIOLATION CLAIMS ARE FEDERAL QUESTIONS: "
                "Claims that a state judge violated the Fourteenth Amendment "
                "arise under the Constitution, not state domestic law.  "
                "Federal courts have original jurisdiction under 28 U.S.C. "
                "§ 1331."
            ),
            (
                "JUDICIAL CONDUCT DURING PROCEEDINGS: Andrew's injuries "
                "were caused by judicial conduct (ex parte contacts, denial "
                "of hearings, biased rulings) that occurred DURING the "
                "proceedings — not by the judgment itself.  McCormick v. "
                "Braverman, 451 F.3d 382 (6th Cir. 2006)."
            ),
            (
                f"CLAIMS ARE SPECIFIC TO PROCESS FAILURES: {claim_label}.  "
                "None of these claims ask the federal court to reverse the "
                "state custody order — they seek damages for independently "
                "actionable constitutional violations."
            ),
        ],
        key_cases=_ROOKER_FELDMAN_AUTHORITIES,
        strength_assessment=StrengthAssessment.WEAK,
        assessment_rationale=(
            "After Exxon Mobil's narrow construction and Skinner's "
            "process-vs-outcome distinction, Rooker-Feldman is unlikely "
            "to bar Andrew's independent § 1983 claims.  The Sixth "
            "Circuit in McCormick confirmed that related-but-independent "
            "claims survive.  Defense is WEAK."
        ),
    )


def analyze_domestic_exception(claims: list[str] | None = None) -> DefenseAnalysis:
    """Analyze the domestic relations exception's applicability.

    Args:
        claims: Optional list of specific claim descriptions.

    Returns:
        A ``DefenseAnalysis`` explaining why the domestic relations
        exception does not strip federal jurisdiction over § 1983 claims.
    """
    if not claims:
        claims = [
            "42 U.S.C. § 1983 — due process deprivation",
            "42 U.S.C. § 1983 — equal protection violation",
            "Constitutional tort — denial of parental rights",
        ]

    logger.info("Analyzing domestic relations exception for claims: %s", claims)

    return DefenseAnalysis(
        defense_name="Domestic Relations Exception",
        category=DefenseCategory.JURISDICTIONAL,
        definition=(
            "The domestic relations exception is a judicially created "
            "limitation on federal diversity jurisdiction.  Under "
            "Ankenbrandt v. Richards, 504 U.S. 689 (1992), federal "
            "courts abstain only from issuing divorce, alimony, or child "
            "custody decrees."
        ),
        elements=[
            "The case is essentially a suit for divorce",
            "The case is essentially a suit for alimony",
            "The case is essentially a suit for child custody",
            (
                "The federal court would need to issue or modify a domestic "
                "relations decree to grant relief"
            ),
        ],
        counter_arguments=[
            (
                "SECTION 1983 CLAIMS ARE NOT DOMESTIC DISPUTES: Andrew's "
                "claims sound in constitutional tort under § 1983.  He seeks "
                "damages for due process violations — not a custody decree.  "
                "Ankenbrandt, 504 U.S. at 704 (tort claims between family "
                "members are cognizable in federal court)."
            ),
            (
                "FEDERAL QUESTION JURISDICTION (NOT DIVERSITY): Andrew's "
                "claims arise under the Constitution and federal statute "
                "(28 U.S.C. § 1331).  The domestic relations exception has "
                "historically been framed as a limitation on DIVERSITY "
                "jurisdiction.  Marshall v. Marshall, 547 U.S. 293 (2006)."
            ),
            (
                "NO CUSTODY DECREE REQUESTED: The complaint does not ask "
                "the federal court to issue, modify, or enforce a custody "
                "order.  Andrew seeks compensatory and punitive damages, "
                "plus declaratory relief that his constitutional rights "
                "were violated."
            ),
            (
                "TORT CLAIMS IN DOMESTIC CONTEXT ARE COGNIZABLE: Ankenbrandt "
                "explicitly held that tort claims between persons in domestic "
                "relationships are within federal jurisdiction.  A § 1983 "
                "constitutional tort claim is the archetype of a cognizable "
                "federal tort.  Catz v. Chalker, 142 F.3d 279 (6th Cir. "
                "1998)."
            ),
            (
                "NARROW EXCEPTION — NOT A BROAD BAR: The Supreme Court has "
                "repeatedly emphasized the exception's narrowness.  It does "
                "not apply merely because the underlying facts involve a "
                "family dispute.  Marshall, 547 U.S. at 307-08."
            ),
        ],
        key_cases=_DOMESTIC_RELATIONS_AUTHORITIES,
        strength_assessment=StrengthAssessment.WEAK,
        assessment_rationale=(
            "The domestic relations exception is narrow and applies to "
            "diversity-based suits seeking issuance of domestic decrees.  "
            "Andrew's § 1983 claims arise under federal-question "
            "jurisdiction and seek damages, not a custody order.  Both "
            "the Supreme Court (Ankenbrandt) and the Sixth Circuit (Catz) "
            "confirm these claims are cognizable.  Defense is WEAK."
        ),
    )


def analyze_judicial_immunity(
    defendants: list[str] | None = None,
) -> DefenseAnalysis:
    """Analyze judicial immunity as applied to each defendant.

    Args:
        defendants: Optional list of defendant names / roles.  Defaults
            to the known judicial defendants in Pigors v. McNeill.

    Returns:
        A ``DefenseAnalysis`` addressing absolute judicial immunity and
        the narrow exceptions that may apply.
    """
    if not defendants:
        defendants = [
            "Hon. Jenny L. McNeill — 14th Circuit Court",
            "Other judicial officers as identified in discovery",
        ]

    logger.info("Analyzing judicial immunity for defendants: %s", defendants)

    defendant_label = "; ".join(defendants)

    return DefenseAnalysis(
        defense_name="Judicial Immunity (Absolute)",
        category=DefenseCategory.IMMUNITY,
        definition=(
            "Judges are absolutely immune from damages liability for acts "
            "performed in their judicial capacity, even if the acts were "
            "erroneous, malicious, or corrupt.  Stump v. Sparkman, 435 "
            "U.S. 349 (1978)."
        ),
        elements=[
            "The defendant was acting in a judicial capacity",
            "The act was a function normally performed by a judge",
            "The parties dealt with the judge in a judicial capacity",
            "The judge had subject-matter jurisdiction (or at least the expectation of it)",
        ],
        counter_arguments=[
            (
                "ABSENCE OF JURISDICTION EXCEPTION: Judicial immunity does "
                "not apply to acts taken in the clear absence of all "
                "jurisdiction.  Mireles v. Waco, 502 U.S. 9, 12 (1991).  "
                "If McNeill proceeded without proper service or notice, she "
                "arguably acted without jurisdiction over the person."
            ),
            (
                "NON-JUDICIAL ACTS EXCEPTION: Ex parte communications with "
                "one party, directing FOC investigations outside proper "
                "procedure, and administrative coordination are not "
                "judicial acts.  Forrester v. White, 484 U.S. 219 (1988) "
                "(administrative acts not protected)."
            ),
            (
                "DECLARATORY AND INJUNCTIVE RELIEF SURVIVES: Even where "
                "damages are barred, § 1983 permits declaratory and "
                "injunctive relief against judges.  Pulliam v. Allen, "
                "466 U.S. 522 (1984).  Andrew can seek a declaration "
                "that his rights were violated and an injunction against "
                "continuing violations."
            ),
            (
                "PATTERN OF CONDUCT UNDERMINES JUDICIAL CHARACTER: A "
                "pattern of biased, retaliatory conduct coupled with ex "
                "parte contacts may be characterized as non-judicial "
                "enforcement activity rather than adjudication.  The "
                "functional analysis in Forrester focuses on the NATURE "
                "of the act, not the actor's title."
            ),
            (
                f"DEFENDANTS: {defendant_label}.  Each defendant's acts "
                "must be individually assessed under the functional "
                "test — blanket immunity is not automatic."
            ),
        ],
        key_cases=_JUDICIAL_IMMUNITY_AUTHORITIES,
        strength_assessment=StrengthAssessment.STRONG,
        assessment_rationale=(
            "Judicial immunity is the most formidable defense.  Courts "
            "apply it broadly.  However, the absence-of-jurisdiction "
            "and non-judicial-acts exceptions provide narrow openings, "
            "and declaratory/injunctive relief remains available.  "
            "Defense is STRONG against damages claims but weaker "
            "against declaratory/injunctive claims."
        ),
    )


def _analyze_qualified_immunity() -> DefenseAnalysis:
    """Analyze qualified immunity for non-judicial government defendants."""
    return DefenseAnalysis(
        defense_name="Qualified Immunity",
        category=DefenseCategory.IMMUNITY,
        definition=(
            "Government officials performing discretionary functions are "
            "shielded from civil damages unless their conduct violates "
            "clearly established statutory or constitutional rights of "
            "which a reasonable person would have known.  Harlow v. "
            "Fitzgerald, 457 U.S. 800 (1982)."
        ),
        elements=[
            "The defendant is a government official acting in a discretionary role",
            "The plaintiff must show a constitutional violation occurred",
            "The right violated must have been 'clearly established' at the time",
            (
                "Existing precedent must have placed the constitutional "
                "question beyond debate"
            ),
        ],
        counter_arguments=[
            (
                "CLEARLY ESTABLISHED RIGHTS: The right to notice and a "
                "meaningful hearing before deprivation of parental rights "
                "has been clearly established since at least Santosky v. "
                "Kramer, 455 U.S. 745 (1982), and Mathews v. Eldridge, "
                "424 U.S. 319 (1976).  No reasonable official could "
                "believe otherwise."
            ),
            (
                "DUE PROCESS IS BEDROCK LAW: The Fourteenth Amendment's "
                "procedural protections are among the most clearly "
                "established rights in American jurisprudence.  Denying "
                "notice, conducting ex parte proceedings, and retaliating "
                "for exercising legal rights violate rights that are "
                "beyond debate."
            ),
            (
                "APPLIES ONLY TO NON-JUDICIAL DEFENDANTS: Qualified "
                "immunity is separate from judicial immunity and applies "
                "to FOC officers, clerks, and other government actors "
                "who participated in the violations."
            ),
        ],
        key_cases=_QUALIFIED_IMMUNITY_AUTHORITIES,
        strength_assessment=StrengthAssessment.MODERATE,
        assessment_rationale=(
            "Qualified immunity is a serious defense for non-judicial "
            "defendants but the rights at issue (notice, hearing, "
            "impartial tribunal) are clearly established.  The defense "
            "is MODERATE — it will require careful factual briefing "
            "but should not prevail on clearly established rights."
        ),
    )


def _analyze_younger_abstention() -> DefenseAnalysis:
    """Analyze Younger abstention doctrine."""
    return DefenseAnalysis(
        defense_name="Younger Abstention",
        category=DefenseCategory.ABSTENTION,
        definition=(
            "Under Younger v. Harris, 401 U.S. 37 (1971), federal "
            "courts abstain from enjoining ongoing state judicial "
            "proceedings when the state provides an adequate forum to "
            "raise federal claims."
        ),
        elements=[
            "There is an ongoing state judicial proceeding",
            "The state proceedings implicate important state interests",
            (
                "There is an adequate opportunity in the state proceedings "
                "to raise constitutional challenges"
            ),
        ],
        counter_arguments=[
            (
                "BAD FAITH / HARASSMENT EXCEPTION: Younger abstention "
                "does not apply when the state proceedings are conducted "
                "in bad faith or to harass.  Kugler v. Helfant, 421 U.S. "
                "117 (1975).  Andrew's allegations of ex parte contacts, "
                "biased proceedings, and retaliatory conduct squarely "
                "implicate this exception."
            ),
            (
                "INADEQUATE STATE FORUM: The state court is itself the "
                "source of the constitutional violations.  Requiring "
                "Andrew to raise due process claims before the very "
                "judge accused of violating due process is inherently "
                "inadequate.  Middlesex County, 457 U.S. at 437."
            ),
            (
                "PATENTLY UNCONSTITUTIONAL PROCEEDINGS: Younger yields "
                "when the state proceeding is 'flagrantly and patently "
                "violative of express constitutional prohibitions.'  "
                "Proceedings conducted without notice, with ex parte "
                "contacts, and with predetermined outcomes may qualify."
            ),
            (
                "DAMAGES CLAIMS NOT SUBJECT TO YOUNGER: Younger's "
                "equitable restraint applies primarily to injunctive "
                "relief against ongoing proceedings.  Claims for "
                "damages for past constitutional violations are "
                "generally not subject to Younger abstention."
            ),
        ],
        key_cases=_YOUNGER_ABSTENTION_AUTHORITIES,
        strength_assessment=StrengthAssessment.MODERATE,
        assessment_rationale=(
            "Younger abstention is a credible defense if state "
            "proceedings are ongoing.  However, the bad-faith "
            "exception is directly applicable to Andrew's case, "
            "and damages claims are generally not subject to "
            "abstention.  Defense is MODERATE."
        ),
    )


def _analyze_heck() -> DefenseAnalysis:
    """Analyze Heck v. Humphrey preclusion doctrine."""
    return DefenseAnalysis(
        defense_name="Heck v. Humphrey Preclusion",
        category=DefenseCategory.PRECLUSION,
        definition=(
            "Under Heck v. Humphrey, 512 U.S. 477 (1994), a § 1983 "
            "claim is not cognizable if a judgment in favor of the "
            "plaintiff would necessarily imply the invalidity of an "
            "outstanding criminal conviction or sentence."
        ),
        elements=[
            "The plaintiff has an outstanding criminal conviction or sentence",
            (
                "Success on the § 1983 claim would NECESSARILY imply the "
                "invalidity of that conviction"
            ),
            "The conviction has not been reversed, expunged, or otherwise invalidated",
        ],
        counter_arguments=[
            (
                "NO CRIMINAL CONVICTION AT ISSUE: If Andrew does not have "
                "an outstanding criminal conviction arising from the same "
                "proceedings, Heck is entirely inapplicable."
            ),
            (
                "PROCESS CLAIMS DO NOT IMPLY INVALIDITY: Even if contempt "
                "of court resulted in incarceration, Andrew's claims "
                "challenge the DUE PROCESS used in the proceedings — not "
                "the underlying contempt finding.  A court can find that "
                "procedures were unconstitutional without necessarily "
                "invalidating the contempt.  Spencer v. Kemna, 523 U.S. "
                "1 (1998)."
            ),
            (
                "CIVIL CONTEMPT IS DISTINGUISHABLE: Civil contempt "
                "sanctions (designed to coerce compliance) are generally "
                "not 'convictions' for Heck purposes.  Only criminal "
                "contempt findings may implicate Heck."
            ),
        ],
        key_cases=_HECK_AUTHORITIES,
        strength_assessment=StrengthAssessment.WEAK,
        assessment_rationale=(
            "Heck is unlikely to apply unless there is an outstanding "
            "criminal conviction directly at issue.  Even then, process-"
            "based claims survive because they do not necessarily imply "
            "the invalidity of any conviction.  Defense is WEAK."
        ),
    )


# ---------------------------------------------------------------------------
# Public API — aggregate functions
# ---------------------------------------------------------------------------

def get_all_anticipated_defenses() -> list[DefenseAnalysis]:
    """Return analyses for ALL anticipated federal defenses.

    Returns:
        A list of six ``DefenseAnalysis`` objects covering every major
        defense a federal defendant is likely to raise in Pigors v.
        McNeill et al.
    """
    logger.info("Generating all anticipated federal defense analyses")
    return [
        analyze_rooker_feldman(),
        analyze_domestic_exception(),
        analyze_judicial_immunity(),
        _analyze_qualified_immunity(),
        _analyze_younger_abstention(),
        _analyze_heck(),
    ]


def generate_defense_brief_outline() -> str:
    """Generate an outline for an Opposition to Motion to Dismiss.

    Produces a structured brief outline addressing each anticipated
    defense, suitable for use in drafting Andrew's opposition to an
    expected 12(b)(1) / 12(b)(6) motion.

    Returns:
        A multi-section string outline ready for expansion into a full
        brief.
    """
    logger.info("Generating defense brief outline")

    analyses = get_all_anticipated_defenses()

    sections: list[str] = []
    sections.append(
        textwrap.dedent("""\
        ================================================================
        PLAINTIFF'S OPPOSITION TO DEFENDANTS' MOTION TO DISMISS
        ================================================================

        Case: Pigors v. McNeill et al.
        Court: United States District Court, Western District of Michigan
        Jurisdiction: 28 U.S.C. §§ 1331, 1343(a)(3)
        Cause of Action: 42 U.S.C. § 1983

        ----------------------------------------------------------------
        TABLE OF CONTENTS
        ----------------------------------------------------------------
        I.    INTRODUCTION
        II.   STATEMENT OF FACTS
        III.  STANDARD OF REVIEW — Rule 12(b)(1) & 12(b)(6)
        IV.   ARGUMENT
              A. Rooker-Feldman Does Not Bar This Action
              B. The Domestic Relations Exception Is Inapplicable
              C. Judicial Immunity Does Not Shield All Defendants or Claims
              D. Qualified Immunity Fails on Clearly Established Rights
              E. Younger Abstention Is Inappropriate
              F. Heck v. Humphrey Does Not Apply
        V.    CONCLUSION
        """)
    )

    section_labels = [
        "A", "B", "C", "D", "E", "F",
    ]

    for idx, analysis in enumerate(analyses):
        label = section_labels[idx] if idx < len(section_labels) else str(idx + 1)
        section_lines = [
            f"\n{'=' * 64}",
            f"IV-{label}. {analysis.defense_name.upper()}",
            f"{'=' * 64}",
            "",
            f"Defense Strength Assessment: {analysis.strength_assessment.value.upper()}",
            f"Category: {analysis.category.value}",
            "",
            "DEFINITION:",
            f"  {analysis.definition}",
            "",
            "ELEMENTS DEFENDANT MUST PROVE:",
        ]
        for i, element in enumerate(analysis.elements, 1):
            section_lines.append(f"  {i}. {element}")

        section_lines.append("")
        section_lines.append("PLAINTIFF'S COUNTER-ARGUMENTS:")
        for i, arg in enumerate(analysis.counter_arguments, 1):
            section_lines.append(f"  {i}. {arg}")

        section_lines.append("")
        section_lines.append("KEY AUTHORITIES:")
        for case in analysis.key_cases:
            section_lines.append(f"  - {case.name}, {case.citation}")
            section_lines.append(f"    Holding: {case.holding[:120]}...")
            section_lines.append(
                f"    Application: {case.relevance_to_pigors[:120]}..."
            )

        section_lines.append("")
        section_lines.append(f"ASSESSMENT: {analysis.assessment_rationale}")
        sections.append("\n".join(section_lines))

    sections.append(
        textwrap.dedent("""\

        ================================================================
        V.  CONCLUSION
        ================================================================

        For the foregoing reasons, Plaintiff respectfully requests that
        Defendants' Motion to Dismiss be DENIED in its entirety.

        None of the anticipated defenses — Rooker-Feldman, the domestic
        relations exception, judicial immunity, qualified immunity,
        Younger abstention, or Heck preclusion — bars Plaintiff's
        independent § 1983 claims for constitutional violations committed
        under color of state law.

        Respectfully submitted,

        Andrew James Pigors, Pro Se
        1977 Whitehall Road, Lot 17
        North Muskegon, MI 49445
        (231) 903-5690
        andrewjpigors@gmail.com
        """)
    )

    return "\n".join(sections)


# ---------------------------------------------------------------------------
# Convenience — summary for dashboard / quick reference
# ---------------------------------------------------------------------------

def get_defense_summary() -> list[dict[str, str]]:
    """Return a compact summary suitable for dashboard display.

    Returns:
        A list of dicts with keys ``defense``, ``strength``, and
        ``one_liner`` for each anticipated defense.
    """
    analyses = get_all_anticipated_defenses()
    return [
        {
            "defense": a.defense_name,
            "strength": a.strength_assessment.value,
            "one_liner": a.assessment_rationale[:200],
        }
        for a in analyses
    ]
