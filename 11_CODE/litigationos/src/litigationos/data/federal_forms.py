"""Federal Court Form Library for WDMI — Western District of Michigan.

Complete registry of federal court forms, FRCP rule summaries, §1983 claim
requirements, IFP (In Forma Pauperis) guidance, WDMI local-rule specifics,
and statute-of-limitations calculator.  Designed for Pigors v Watson §1983
civil rights action in the Western District of Michigan (Southern Division).

Complements ``federal_rules.py`` (raw rule text / statutes) by adding the
**form layer** — the actual documents a pro se litigant must prepare, plus
helper functions for deadline calculation and requirement lookup.

Sources:
  - uscourts.gov/forms (Administrative Office forms — AO / JS series)
  - miwd.uscourts.gov (WDMI-specific forms and local rules)
  - 42 USC §§ 1983, 1985, 1988
  - MCL 600.5805(2) — Michigan 3-year personal-injury SOL (governs §1983)
  - FRCP Rules 3, 4, 8, 12, 15, 26, 56, 65

All data is local-only — no external API calls.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any


# =========================================================================
# Data classes
# =========================================================================

@dataclass(frozen=True)
class FederalForm:
    """Immutable descriptor for a single federal court form."""

    form_number: str
    title: str
    purpose: str
    category: str
    required_fields: list[str]
    filing_court: str
    frcp_references: list[str]
    statute_references: list[str]
    url: str = "https://www.uscourts.gov/forms"
    practice_tips: str = ""
    filing_use: list[str] = field(default_factory=list)
    page_limit: int | None = None
    efiling_notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to plain dictionary for JSON / DB compatibility."""
        return {
            "form_number": self.form_number,
            "title": self.title,
            "purpose": self.purpose,
            "category": self.category,
            "required_fields": list(self.required_fields),
            "filing_court": self.filing_court,
            "frcp_references": list(self.frcp_references),
            "statute_references": list(self.statute_references),
            "url": self.url,
            "practice_tips": self.practice_tips,
            "filing_use": list(self.filing_use),
            "page_limit": self.page_limit,
            "efiling_notes": self.efiling_notes,
        }


# =========================================================================
# FEDERAL FORM REGISTRY
# =========================================================================

FEDERAL_FORMS: list[FederalForm] = [
    # ------------------------------------------------------------------
    # INITIATING FORMS
    # ------------------------------------------------------------------
    FederalForm(
        form_number="JS 44",
        title="Civil Cover Sheet",
        purpose=(
            "Required cover sheet filed with every new civil complaint.  "
            "Identifies parties, basis of jurisdiction, nature of suit, "
            "cause of action, and requested jury demand.  For §1983: "
            "check 'Federal Question' (Box II) and 'Civil Rights — "
            "Other Civil Rights' (Nature of Suit code 440)."
        ),
        category="Initiating",
        required_fields=[
            "plaintiff_name",
            "plaintiff_address",
            "plaintiff_county",
            "defendant_name",
            "defendant_address",
            "defendant_county",
            "attorneys_for_plaintiff",
            "basis_of_jurisdiction",
            "citizenship_of_parties",
            "nature_of_suit",
            "cause_of_action",
            "brief_description",
            "demand_amount",
            "jury_demand",
            "related_case_judge",
            "date_signed",
            "signature",
        ],
        filing_court="USDC — Western District of Michigan",
        frcp_references=["FRCP Rule 3"],
        statute_references=[
            "28 USC § 1331",
            "28 USC § 1343",
            "42 USC § 1983",
        ],
        url="https://www.uscourts.gov/forms/civil-forms/civil-cover-sheet",
        practice_tips=(
            "Nature of Suit: 440 (Other Civil Rights) or 441 (Voting) or "
            "442 (Employment) — use 440 for §1983 due-process / equal-"
            "protection claims.  Jurisdiction: Box II — Federal Question.  "
            "Demand: enter estimated damages.  Must be filed simultaneously "
            "with the complaint and filing fee (or IFP application)."
        ),
        filing_use=["Complaint filing"],
        efiling_notes=(
            "Filed as an attachment to the complaint in CM/ECF.  "
            "Pro se litigants may file on paper with clerk's office."
        ),
    ),

    FederalForm(
        form_number="Pro Se 1",
        title="Complaint for Violation of Civil Rights (42 USC § 1983)",
        purpose=(
            "Standard pro se form for §1983 civil rights complaints in "
            "federal court.  Structured to capture: jurisdiction, parties, "
            "statement of claim (what each defendant did, when, and how it "
            "violated constitutional rights), injuries, and relief sought."
        ),
        category="Initiating",
        required_fields=[
            "plaintiff_name",
            "plaintiff_address",
            "plaintiff_phone",
            "defendant_names",
            "defendant_titles_positions",
            "defendant_addresses",
            "jurisdictional_basis",
            "statement_of_claim",
            "supporting_facts_per_defendant",
            "constitutional_rights_violated",
            "injuries_sustained",
            "relief_requested",
            "declaratory_relief_requested",
            "injunctive_relief_requested",
            "compensatory_damages",
            "punitive_damages",
            "date_signed",
            "signature",
            "verification_under_penalty_of_perjury",
        ],
        filing_court="USDC — Western District of Michigan",
        frcp_references=["FRCP Rule 8", "FRCP Rule 10", "FRCP Rule 11"],
        statute_references=[
            "42 USC § 1983",
            "42 USC § 1985",
            "42 USC § 1988",
            "28 USC § 1331",
            "28 USC § 1343",
        ],
        url="https://www.uscourts.gov/forms/pro-se-forms/complaint-violation-civil-rights",
        practice_tips=(
            "Must meet Iqbal/Twombly plausibility standard — each "
            "defendant must be identified individually with specific "
            "facts showing what THEY did.  Group pleading is insufficient.  "
            "For judicial defendants, allege non-judicial or administrative "
            "acts to overcome absolute judicial immunity.  For private "
            "actors (e.g., co-conspirators), allege joint action / "
            "conspiracy under color of state law (Dennis v Sparks)."
        ),
        filing_use=["Initiating §1983 action"],
        efiling_notes=(
            "Pro se litigants in WDMI may file on paper.  "
            "CM/ECF registration is optional for pro se."
        ),
    ),

    FederalForm(
        form_number="AO 440",
        title="Summons in a Civil Action",
        purpose=(
            "Official summons form issued by the clerk upon filing of "
            "a complaint.  Must be served on each defendant with a copy "
            "of the complaint within 90 days of filing (FRCP Rule 4(m))."
        ),
        category="Initiating",
        required_fields=[
            "plaintiff_name",
            "defendant_name",
            "civil_action_number",
            "defendant_address",
            "days_to_respond",
            "clerk_signature",
            "date_issued",
        ],
        filing_court="USDC — Western District of Michigan",
        frcp_references=["FRCP Rule 4"],
        statute_references=[],
        url="https://www.uscourts.gov/forms/notice-lawsuit-summons-subpoena/summons-civil-action",
        practice_tips=(
            "Clerk issues summons after complaint is filed.  Serve "
            "within 90 days or face dismissal without prejudice.  "
            "Government defendants (state officials in official capacity) "
            "must be served per FRCP 4(j) — deliver to chief executive "
            "officer or send by registered/certified mail.  Individual-"
            "capacity defendants: personal service, leaving at dwelling, "
            "or serving authorized agent (FRCP 4(e))."
        ),
        filing_use=["Service of process"],
    ),

    # ------------------------------------------------------------------
    # IN FORMA PAUPERIS (IFP)
    # ------------------------------------------------------------------
    FederalForm(
        form_number="AO 240",
        title="Application to Proceed in District Court Without Prepaying "
              "Fees or Costs (In Forma Pauperis)",
        purpose=(
            "Allows indigent litigants to file without paying the $405 "
            "civil filing fee.  Requires detailed financial disclosure: "
            "income, assets, debts, dependents, and monthly expenses.  "
            "Court reviews under 28 USC § 1915."
        ),
        category="IFP",
        required_fields=[
            "applicant_name",
            "employer_and_income",
            "income_last_12_months",
            "spouse_income",
            "assets_cash",
            "assets_bank_accounts",
            "assets_vehicles",
            "assets_real_estate",
            "assets_other",
            "monthly_expenses",
            "dependents",
            "debts_and_obligations",
            "previous_ifp_applications",
            "declaration_under_penalty_of_perjury",
            "date_signed",
            "signature",
        ],
        filing_court="USDC — Western District of Michigan",
        frcp_references=[],
        statute_references=["28 USC § 1915"],
        url="https://www.uscourts.gov/forms/fee-schedule/application-proceed-district-court-without-prepaying-fees-or-costs",
        practice_tips=(
            "File simultaneously with complaint (instead of filing fee).  "
            "If denied, court will order filing fee paid within a set "
            "period or case is dismissed.  28 USC § 1915(e)(2) allows "
            "court to screen IFP complaints and dismiss if frivolous, "
            "malicious, or fails to state a claim.  Be thorough and "
            "honest — false statements are perjury."
        ),
        filing_use=["Fee waiver"],
        efiling_notes=(
            "File as a separate document alongside the complaint.  "
            "Financial information is typically sealed from public "
            "docket under WDMI practice."
        ),
    ),

    # ------------------------------------------------------------------
    # SUBPOENA FORMS
    # ------------------------------------------------------------------
    FederalForm(
        form_number="AO 88",
        title="Subpoena to Appear and Testify at a Hearing or Trial "
              "in a Civil Action",
        purpose=(
            "Compels witness attendance at hearing or trial.  Must "
            "specify time, place, and whether testimony or documents "
            "are required.  Must be served with witness and mileage fees."
        ),
        category="Subpoena",
        required_fields=[
            "court_name",
            "case_caption",
            "civil_action_number",
            "witness_name",
            "witness_address",
            "testimony_date",
            "testimony_location",
            "issuing_officer_signature",
        ],
        filing_court="USDC — Western District of Michigan",
        frcp_references=["FRCP Rule 45"],
        statute_references=["28 USC § 1821"],
        url="https://www.uscourts.gov/forms/notice-lawsuit-summons-subpoena/subpoena-appear-and-testify-hearing-or-trial-civil",
        practice_tips=(
            "Must tender witness fee ($40/day) and mileage "
            "(IRS rate) at time of service.  100-mile rule: "
            "witness cannot be compelled to travel more than "
            "100 miles from where they reside, are employed, "
            "or regularly transact business."
        ),
        filing_use=["Witness compulsion", "Trial preparation"],
    ),

    FederalForm(
        form_number="AO 88A",
        title="Subpoena to Testify at a Deposition in a Civil Action",
        purpose=(
            "Compels witness attendance at a deposition.  May also "
            "require production of documents, ESI, or tangible things "
            "at the deposition."
        ),
        category="Subpoena",
        required_fields=[
            "court_name",
            "case_caption",
            "civil_action_number",
            "deponent_name",
            "deponent_address",
            "deposition_date",
            "deposition_location",
            "documents_requested",
            "issuing_officer_signature",
        ],
        filing_court="USDC — Western District of Michigan",
        frcp_references=["FRCP Rule 30", "FRCP Rule 45"],
        statute_references=["28 USC § 1821"],
        url="https://www.uscourts.gov/forms/notice-lawsuit-summons-subpoena/subpoena-testify-deposition-civil-action",
        practice_tips=(
            "Deposition limited to 7 hours / 1 day unless court "
            "orders otherwise.  Must give reasonable notice.  "
            "Deposition costs borne by the party taking it."
        ),
        filing_use=["Discovery", "Deposition"],
    ),

    FederalForm(
        form_number="AO 88B",
        title="Subpoena to Produce Documents, Information, or Objects "
              "or to Permit Inspection of Premises in a Civil Action",
        purpose=(
            "Compels non-party production of documents, ESI, or "
            "tangible things, or inspection of premises.  Does NOT "
            "require testimony — document production only."
        ),
        category="Subpoena",
        required_fields=[
            "court_name",
            "case_caption",
            "civil_action_number",
            "person_or_entity_name",
            "person_or_entity_address",
            "production_date",
            "production_location",
            "documents_esi_described",
            "issuing_officer_signature",
        ],
        filing_court="USDC — Western District of Michigan",
        frcp_references=["FRCP Rule 34", "FRCP Rule 45"],
        statute_references=[],
        url="https://www.uscourts.gov/forms/notice-lawsuit-summons-subpoena/subpoena-produce-documents-information-or-objects",
        practice_tips=(
            "Use for third-party records: CPS reports, police "
            "records, phone records, school records, hospital "
            "records.  Non-party may object within 14 days.  "
            "Must describe documents with reasonable particularity."
        ),
        filing_use=["Discovery", "Document production"],
    ),

    # ------------------------------------------------------------------
    # MOTION FORMS
    # ------------------------------------------------------------------
    FederalForm(
        form_number="WDMI Motion",
        title="Motion (General — WDMI Format)",
        purpose=(
            "General motion format for WDMI.  All motions require a "
            "separate brief in support.  WDMI LCivR 7.1 governs "
            "motion practice."
        ),
        category="Motion",
        required_fields=[
            "case_caption",
            "civil_action_number",
            "motion_title",
            "relief_requested",
            "brief_statement_of_grounds",
            "certification_of_conferral",
            "date_signed",
            "signature",
        ],
        filing_court="USDC — Western District of Michigan",
        frcp_references=["FRCP Rule 7"],
        statute_references=[],
        practice_tips=(
            "WDMI requires a SEPARATE brief in support — do NOT "
            "combine the motion and brief in one document.  "
            "Response: 14 days.  Reply: 7 days.  Brief limit: "
            "25 pages (opening/response), 10 pages (reply).  "
            "Must certify conferral with opposing party before filing "
            "any discovery or non-dispositive motion."
        ),
        filing_use=["Motion practice"],
        page_limit=25,
    ),

    FederalForm(
        form_number="WDMI TRO",
        title="Motion for Temporary Restraining Order",
        purpose=(
            "Emergency motion for TRO under FRCP 65(b).  Must show "
            "immediate and irreparable injury that will occur before "
            "the adverse party can be heard.  TRO expires in 14 days "
            "unless extended for good cause."
        ),
        category="Motion",
        required_fields=[
            "case_caption",
            "civil_action_number",
            "specific_facts_showing_irreparable_harm",
            "why_notice_not_required",
            "proposed_restraining_order",
            "security_bond_amount",
            "verification_or_affidavit",
            "date_signed",
            "signature",
        ],
        filing_court="USDC — Western District of Michigan",
        frcp_references=["FRCP Rule 65(b)"],
        statute_references=["42 USC § 1983"],
        practice_tips=(
            "Four factors: (1) substantial likelihood of success on "
            "the merits; (2) irreparable harm absent TRO; (3) balance "
            "of equities favors movant; (4) public interest served.  "
            "For §1983 against judicial officer: injunctive relief "
            "requires prior declaratory decree was violated or "
            "declaratory relief was unavailable.  Must post security "
            "bond unless court waives (common for IFP litigants)."
        ),
        filing_use=["Emergency relief", "Injunction"],
    ),

    FederalForm(
        form_number="WDMI PI",
        title="Motion for Preliminary Injunction",
        purpose=(
            "Motion for preliminary injunction under FRCP 65(a).  "
            "Requires notice to adverse party and hearing.  Same "
            "four-factor test as TRO but on fuller record."
        ),
        category="Motion",
        required_fields=[
            "case_caption",
            "civil_action_number",
            "statement_of_facts",
            "argument_on_four_factors",
            "proposed_injunction_order",
            "evidence_and_affidavits",
            "security_bond_amount",
            "date_signed",
            "signature",
        ],
        filing_court="USDC — Western District of Michigan",
        frcp_references=["FRCP Rule 65(a)"],
        statute_references=["42 USC § 1983"],
        practice_tips=(
            "6th Circuit standard (Certified Restoration Dry Cleaning "
            "Network v Tenke Corp, 511 F.3d 535): weighs all four "
            "factors; no single factor is dispositive.  For parenting-"
            "time cases: argue irreparable harm to parent-child "
            "relationship and child's best interest."
        ),
        filing_use=["Injunction"],
        page_limit=25,
    ),

    FederalForm(
        form_number="WDMI MSJ",
        title="Motion for Summary Judgment",
        purpose=(
            "Dispositive motion under FRCP 56.  Must include a "
            "Statement of Material Facts per WDMI LCivR 7.2.  "
            "Each fact must cite admissible evidence."
        ),
        category="Motion",
        required_fields=[
            "case_caption",
            "civil_action_number",
            "brief_in_support",
            "statement_of_material_facts",
            "evidence_citations_per_fact",
            "exhibits",
            "proposed_order",
            "date_signed",
            "signature",
        ],
        filing_court="USDC — Western District of Michigan",
        frcp_references=["FRCP Rule 56"],
        statute_references=[],
        url="https://www.miwd.uscourts.gov",
        practice_tips=(
            "WDMI LCivR 7.2: Statement of Material Facts is MANDATORY.  "
            "Each numbered fact must cite specific evidence (deposition, "
            "affidavit, document).  Opposing party must file Counter-"
            "Statement — facts not controverted are deemed admitted.  "
            "Standard: no genuine dispute of material fact, viewed in "
            "light most favorable to non-movant (Anderson v Liberty "
            "Lobby, 477 U.S. 242)."
        ),
        filing_use=["Dispositive motion"],
        page_limit=25,
    ),

    FederalForm(
        form_number="WDMI Discovery",
        title="Discovery Motion (Motion to Compel / Protective Order)",
        purpose=(
            "Motions related to discovery disputes under FRCP 26-37.  "
            "WDMI LCivR 26.1 requires meet-and-confer certification "
            "before filing any discovery motion."
        ),
        category="Motion",
        required_fields=[
            "case_caption",
            "civil_action_number",
            "discovery_request_at_issue",
            "meet_and_confer_certification",
            "grounds_for_relief",
            "proposed_order",
            "date_signed",
            "signature",
        ],
        filing_court="USDC — Western District of Michigan",
        frcp_references=["FRCP Rule 26", "FRCP Rule 37"],
        statute_references=[],
        practice_tips=(
            "Must certify in writing that you attempted to resolve "
            "the dispute with opposing counsel before filing.  "
            "Discovery sanctions under Rule 37 can be case-"
            "dispositive.  Discovery motions go to Magistrate Judge "
            "first (FRCP 72(a))."
        ),
        filing_use=["Discovery enforcement"],
    ),

    # ------------------------------------------------------------------
    # APPELLATE / POST-JUDGMENT
    # ------------------------------------------------------------------
    FederalForm(
        form_number="AO 450",
        title="Notice of Appeal to a Court of Appeals from a Judgment "
              "or Order of a District Court",
        purpose=(
            "Initiates appeal from USDC to the Sixth Circuit Court of "
            "Appeals.  Must be filed within 30 days of entry of "
            "judgment (60 days if US or officer is a party)."
        ),
        category="Appellate",
        required_fields=[
            "appellant_name",
            "appellee_name",
            "civil_action_number",
            "judgment_or_order_appealed",
            "date_of_judgment",
            "court_appealed_to",
            "date_signed",
            "signature",
        ],
        filing_court="USDC — Western District of Michigan (filed in district court)",
        frcp_references=["FRAP Rule 3", "FRAP Rule 4"],
        statute_references=["28 USC § 1291", "28 USC § 1292"],
        url="https://www.uscourts.gov/forms/appellate-forms/notice-appeal-court-appeals",
        practice_tips=(
            "FRAP 4(a)(1): 30-day deadline from entry of judgment "
            "(or 60 days if government party).  Deadline is "
            "jurisdictional — cannot be waived.  Filing fee: $505 "
            "(or IFP motion).  File in the district court, NOT the "
            "circuit court.  Must designate the judgment/order being "
            "appealed with specificity."
        ),
        filing_use=["Appeal"],
    ),

    # ------------------------------------------------------------------
    # CONSENT / MAGISTRATE JUDGE
    # ------------------------------------------------------------------
    FederalForm(
        form_number="AO 085",
        title="Consent to Proceed Before a United States Magistrate Judge",
        purpose=(
            "Voluntary consent form for all parties to have the case "
            "tried before a Magistrate Judge instead of a District "
            "Judge.  Both sides must consent; cannot be compelled."
        ),
        category="Administrative",
        required_fields=[
            "case_caption",
            "civil_action_number",
            "consenting_party_names",
            "date_signed",
            "signatures_of_all_parties",
        ],
        filing_court="USDC — Western District of Michigan",
        frcp_references=["FRCP Rule 72", "FRCP Rule 73"],
        statute_references=["28 USC § 636(c)"],
        url="https://www.uscourts.gov/forms/court-forms/consent-proceed-before-united-states-magistrate-judge",
        practice_tips=(
            "Consent is entirely voluntary.  Declining consent to a "
            "Magistrate Judge cannot be held against you.  In WDMI, "
            "the clerk typically sends this form to all parties after "
            "case assignment.  A Magistrate Judge handles pretrial "
            "matters by default — this form is only for TRIAL consent."
        ),
        filing_use=["Case administration"],
    ),

    FederalForm(
        form_number="WDMI Pro Se Info",
        title="WDMI Pro Se Litigant Information Sheet",
        purpose=(
            "Information sheet required by WDMI for pro se litigants.  "
            "Captures contact information, case type, and acknowledges "
            "obligation to follow all court rules."
        ),
        category="Administrative",
        required_fields=[
            "litigant_name",
            "mailing_address",
            "phone_number",
            "email_address",
            "case_number",
            "acknowledgment_signature",
        ],
        filing_court="USDC — Western District of Michigan",
        frcp_references=[],
        statute_references=[],
        url="https://www.miwd.uscourts.gov/pro-se-information",
        practice_tips=(
            "WDMI has a Pro Se Unit that assists with procedural "
            "questions (not legal advice).  Keep contact information "
            "current — failure to receive court orders due to outdated "
            "address is not grounds for relief."
        ),
        filing_use=["Pro se administration"],
    ),
]


# =========================================================================
# FRCP RULE SUMMARIES (quick-reference for §1983 practitioners)
# =========================================================================

FRCP_KEY_RULES: dict[str, dict[str, str]] = {
    "Rule 4": {
        "title": "Summons / Service of Process",
        "summary": (
            "Serve each defendant within 90 days of filing.  "
            "Government officials (official capacity): serve per "
            "FRCP 4(j)(2) — certified mail to agency + DOJ if US.  "
            "Individual capacity: personal service, dwelling, or agent "
            "(FRCP 4(e)).  Waiver of service (FRCP 4(d)) saves costs "
            "and extends response time to 60 days."
        ),
        "deadline": "90 days from filing complaint",
    },
    "Rule 8": {
        "title": "General Rules of Pleading",
        "summary": (
            "Complaint must contain: (1) short and plain statement of "
            "jurisdiction; (2) short and plain statement of the claim "
            "showing entitlement to relief; (3) demand for relief.  "
            "Federal plausibility standard (Iqbal/Twombly) — must "
            "state enough facts to nudge claim across the line from "
            "'conceivable' to 'plausible.'"
        ),
        "deadline": "N/A — pleading standard, not deadline",
    },
    "Rule 12": {
        "title": "Defenses and Objections",
        "summary": (
            "12(b)(1) lack of subject-matter jurisdiction; "
            "12(b)(6) failure to state a claim.  Expect defendants "
            "to file 12(b)(6) motion in §1983 cases — must survive "
            "plausibility screening.  Response to 12(b)(6): 14 days "
            "(WDMI LCivR 7.1)."
        ),
        "deadline": "Must raise in responsive pleading or pre-answer motion",
    },
    "Rule 15": {
        "title": "Amended and Supplemental Pleadings",
        "summary": (
            "Amend once as of right within 21 days of serving, or "
            "21 days after responsive pleading / 12(b) motion.  "
            "After that, need consent or leave of court — court "
            "should 'freely give leave when justice so requires.'  "
            "Amendments relate back if same conduct / occurrence."
        ),
        "deadline": "21 days as of right; otherwise by leave of court",
    },
    "Rule 26": {
        "title": "Duty to Disclose; General Discovery",
        "summary": (
            "Mandatory initial disclosures without request: names of "
            "witnesses, copy/description of relevant documents, "
            "damages computation, insurance agreements.  Due within "
            "14 days of the Rule 26(f) conference.  Discovery scope: "
            "any nonprivileged matter relevant to claims or defenses."
        ),
        "deadline": "14 days after Rule 26(f) conference",
    },
    "Rule 56": {
        "title": "Summary Judgment",
        "summary": (
            "Grant if no genuine dispute of material fact and movant "
            "entitled to judgment as a matter of law.  Must cite "
            "specific evidence.  WDMI: Statement of Material Facts "
            "required (LCivR 7.2).  Evidence viewed in light most "
            "favorable to non-movant."
        ),
        "deadline": "At least 30 days before trial; per scheduling order",
    },
    "Rule 65": {
        "title": "Injunctions and Restraining Orders",
        "summary": (
            "TRO (65(b)): ex parte possible if irreparable injury "
            "shown, expires 14 days.  Preliminary injunction (65(a)): "
            "requires notice and hearing.  Four-factor test: "
            "likelihood of success, irreparable harm, balance of "
            "equities, public interest."
        ),
        "deadline": "TRO expires in 14 days; PI by motion at any time",
    },
}


# =========================================================================
# §1983 CLAIM REQUIREMENTS
# =========================================================================

SECTION_1983_REQUIREMENTS: dict[str, Any] = {
    "statute": "42 USC § 1983",
    "elements": [
        {
            "number": 1,
            "element": "Person",
            "description": (
                "Defendant must be a 'person' within the meaning of "
                "§1983.  Includes state officials (sued in individual "
                "or official capacity), municipal employees, and private "
                "actors who conspire with state actors.  Does NOT "
                "include the state itself (Eleventh Amendment immunity) "
                "or federal officials (use Bivens instead)."
            ),
        },
        {
            "number": 2,
            "element": "Acting Under Color of State Law",
            "description": (
                "Defendant must have acted under color of any statute, "
                "ordinance, regulation, custom, or usage of a state.  "
                "State judges acting in judicial capacity — YES (color "
                "of law) but may have absolute immunity.  Private "
                "actors — only if conspiring with or acting jointly "
                "with state actor (Dennis v Sparks, 449 U.S. 24)."
            ),
        },
        {
            "number": 3,
            "element": "Subjects Plaintiff to Deprivation",
            "description": (
                "Defendant's action must have actually deprived "
                "plaintiff of a right.  Causation required — must "
                "show that the specific defendant's conduct caused "
                "the deprivation.  Supervisory liability requires "
                "personal involvement — respondeat superior alone "
                "is insufficient (Iqbal)."
            ),
        },
        {
            "number": 4,
            "element": "Of Rights Secured by the Constitution or Federal Law",
            "description": (
                "The right violated must be one protected by the "
                "Constitution or federal law.  Common bases: "
                "14th Amendment Due Process (procedural and "
                "substantive), 14th Amendment Equal Protection, "
                "1st Amendment (retaliation for exercising rights), "
                "4th Amendment (unreasonable seizure of person/property)."
            ),
        },
    ],
    "immunity_defenses": {
        "absolute_judicial_immunity": (
            "Judges have absolute immunity for acts performed in their "
            "judicial capacity — UNLESS: (1) the act was not a judicial "
            "act (administrative/executive function); or (2) the judge "
            "acted in complete absence of all jurisdiction.  Stump v "
            "Sparkman, 435 U.S. 349.  §1983 expressly limits injunctive "
            "relief against judges unless a declaratory decree was "
            "violated or declaratory relief was unavailable."
        ),
        "qualified_immunity": (
            "Non-judicial government officials have qualified immunity "
            "unless they violated a 'clearly established' constitutional "
            "right that a reasonable official would have known.  "
            "Two-step analysis: (1) was a right violated? (2) was the "
            "right clearly established at the time?  Harlow v Fitzgerald, "
            "457 U.S. 800.  Overcome by citing specific, on-point "
            "precedent showing the right was clearly established."
        ),
        "eleventh_amendment": (
            "States (and state agencies) cannot be sued for damages "
            "under §1983 — sovereign immunity.  Exception: sue state "
            "officials in their INDIVIDUAL capacity for damages, or in "
            "OFFICIAL capacity for prospective injunctive relief only "
            "(Ex parte Young, 209 U.S. 123)."
        ),
    },
    "statute_of_limitations": {
        "rule": (
            "§1983 borrows the state personal-injury SOL.  In Michigan: "
            "MCL 600.5805(2) = 3 years from accrual of the claim."
        ),
        "accrual": (
            "Federal accrual rules apply (not state).  Claim accrues "
            "when plaintiff knows or has reason to know of the injury.  "
            "Wallace v Kato, 549 U.S. 384.  Continuing-violation "
            "doctrine may extend accrual for ongoing constitutional "
            "violations."
        ),
        "tolling": (
            "Equitable tolling available in extraordinary circumstances: "
            "incarceration, mental incapacity, fraudulent concealment.  "
            "Michigan minority tolling (MCL 600.5851) may also apply."
        ),
        "michigan_sol_years": 3,
    },
    "damages_available": {
        "compensatory": "Actual damages for injury caused by the violation.",
        "punitive": (
            "Available against individual defendants (not municipalities) "
            "if conduct was motivated by evil motive or intent, or "
            "involved reckless or callous indifference to rights.  "
            "Smith v Wade, 461 U.S. 30."
        ),
        "nominal": "Available even without proof of actual injury — useful for establishing the violation.",
        "declaratory": "Declaration that defendant's conduct violated the Constitution.",
        "injunctive": (
            "Prospective injunctive relief — order defendant to stop "
            "the unconstitutional conduct.  Available against officials "
            "in official capacity (Ex parte Young)."
        ),
        "attorneys_fees": (
            "42 USC § 1988 — prevailing party may recover reasonable "
            "attorney's fees.  Pro se litigants generally cannot recover "
            "attorney's fees but can recover costs."
        ),
    },
    "key_cases_6th_circuit": [
        "Catz v Chalker, 142 F.3d 279 (6th Cir. 1998) — domestic "
        "relations exception does not bar §1983 claims",
        "Ashcroft v Iqbal, 556 U.S. 662 (2009) — plausibility pleading standard",
        "Bell Atlantic Corp v Twombly, 550 U.S. 544 (2007) — plausibility standard",
        "Dennis v Sparks, 449 U.S. 24 (1980) — private actor conspiracy under color of law",
        "Stump v Sparkman, 435 U.S. 349 (1978) — judicial immunity scope",
        "Ex parte Young, 209 U.S. 123 (1908) — official-capacity injunctive relief",
        "Harlow v Fitzgerald, 457 U.S. 800 (1982) — qualified immunity standard",
        "Anderson v Liberty Lobby, 477 U.S. 242 (1986) — summary judgment standard",
    ],
}


# =========================================================================
# IFP REQUIREMENTS
# =========================================================================

IFP_REQUIREMENTS: dict[str, Any] = {
    "statute": "28 USC § 1915",
    "filing_fee_waived": "$405 civil filing fee",
    "form": "AO 240",
    "requirements": [
        "Complete financial affidavit under penalty of perjury",
        "Disclose all income sources (employment, benefits, support)",
        "Disclose all assets (bank accounts, vehicles, real estate, investments)",
        "Disclose all debts and monthly expenses",
        "Disclose dependents",
        "Disclose prior IFP applications in any court",
    ],
    "standard": (
        "Court grants IFP if applicant demonstrates inability to pay "
        "filing fees without undue hardship.  No specific income "
        "threshold — court exercises discretion based on totality of "
        "financial circumstances."
    ),
    "screening": {
        "1915_e_2": (
            "Court must screen IFP complaints and dismiss if: "
            "(i) frivolous or malicious; (ii) fails to state a claim; "
            "(iii) seeks damages from immune defendant.  This screening "
            "is a preliminary merits review — complaint must state a "
            "plausible claim to survive."
        ),
    },
    "partial_payment": (
        "Court may grant IFP but order partial payment of filing fee "
        "in installments.  Common in prisoner litigation; less common "
        "for non-prisoner pro se litigants."
    ),
    "appeal_if_denied": (
        "If IFP denied, can: (1) pay the filing fee within the time "
        "set by court; (2) appeal denial to the district judge (if "
        "denied by magistrate judge); (3) file a motion for "
        "reconsideration with additional financial information."
    ),
    "practice_tips": (
        "File IFP application simultaneously with complaint.  Be "
        "completely honest — inaccurate financial information is "
        "perjury and grounds for sanctions.  If financial situation "
        "changes during litigation, update the court."
    ),
}


# =========================================================================
# WDMI LOCAL RULES — Filing Specifics
# =========================================================================

WDMI_LOCAL_RULES_DETAIL: dict[str, Any] = {
    "court": "United States District Court — Western District of Michigan",
    "divisions": {
        "southern": {
            "location": "110 Michigan St NW, Grand Rapids, MI 49503",
            "phone": "(616) 456-2381",
            "counties": [
                "Allegan", "Antrim", "Barry", "Benzie", "Berrien",
                "Branch", "Calhoun", "Cass", "Charlevoix", "Eaton",
                "Emmet", "Grand Traverse", "Ionia", "Kalamazoo",
                "Kalkaska", "Kent", "Lake", "Leelanau", "Manistee",
                "Mason", "Mecosta", "Missaukee", "Montcalm", "Muskegon",
                "Newaygo", "Oceana", "Osceola", "Ottawa", "St. Joseph",
                "Van Buren", "Wexford",
            ],
        },
        "northern": {
            "location": "401 S. Front St, Marquette, MI 49855",
            "phone": "(906) 226-2117",
            "counties": [
                "Alger", "Baraga", "Chippewa", "Delta", "Dickinson",
                "Gogebic", "Houghton", "Iron", "Keweenaw", "Luce",
                "Mackinac", "Marquette", "Menominee", "Ontonagon",
                "Schoolcraft",
            ],
        },
    },
    "andrew_division": "Southern Division (Muskegon County)",
    "efiling": {
        "system": "CM/ECF (Case Management / Electronic Case Files)",
        "url": "https://ecf.miwd.uscourts.gov",
        "pro_se_policy": (
            "Pro se litigants are NOT required to use CM/ECF.  "
            "May file documents on paper at the clerk's office.  "
            "Pro se litigants may voluntarily register for CM/ECF "
            "with clerk approval."
        ),
        "paper_filing": (
            "Paper filings accepted at clerk's office during "
            "business hours (8:30 AM — 4:30 PM, M-F).  Original "
            "plus one copy for judge.  Include certificate of "
            "service for all documents served on opposing parties."
        ),
        "pdf_requirements": (
            "If filing electronically: PDF format, text-searchable "
            "preferred, max 35 MB per document.  Oversized documents "
            "must be split into volumes."
        ),
    },
    "page_limits": {
        "opening_brief": {"pages": 25, "rule": "WDMI LCivR 10.6"},
        "response_brief": {"pages": 25, "rule": "WDMI LCivR 10.6"},
        "reply_brief": {"pages": 10, "rule": "WDMI LCivR 10.6"},
        "excluded_from_count": [
            "Cover page",
            "Table of contents",
            "Table of authorities",
            "Certificate of service",
            "Signature block",
            "Exhibits / attachments (filed separately)",
        ],
        "excess_pages": (
            "Requires prior leave of court via motion.  "
            "Motions to exceed page limits are disfavored."
        ),
    },
    "service_requirements": {
        "government_defendants_official_capacity": (
            "FRCP 4(j)(2): Serve by delivering a copy of summons "
            "and complaint to the chief executive officer of the "
            "governmental entity, or by sending a copy by registered "
            "or certified mail to the chief executive officer.  "
            "Also serve the Michigan Attorney General per state law."
        ),
        "individual_capacity": (
            "FRCP 4(e): (1) Following state law for the state where "
            "the district court is located (Michigan) — MCR 2.105; "
            "(2) Delivering to the individual personally; "
            "(3) Leaving at the individual's dwelling with someone "
            "of suitable age and discretion; (4) Delivering to an "
            "authorized agent."
        ),
        "waiver_of_service": (
            "FRCP 4(d): Send waiver request by first-class mail.  "
            "Defendant has 30 days to return waiver (60 days if "
            "outside US).  If waiver returned, defendant gets 60 days "
            "to answer (instead of 21).  If defendant refuses to waive "
            "without good cause, defendant pays service costs."
        ),
        "us_marshal_service": (
            "IFP litigants may request that the US Marshal serve "
            "defendants at government expense.  Submit USM-285 form "
            "for each defendant to be served."
        ),
    },
    "filing_fee": {
        "civil_complaint": "$405",
        "notice_of_appeal": "$505",
        "ifp_alternative": "AO 240 application to proceed IFP",
    },
    "response_deadlines": {
        "answer_to_complaint": "21 days after service (60 days if waiver of service)",
        "response_to_motion": "14 days (WDMI LCivR 7.1(b))",
        "reply_brief": "7 days after response (WDMI LCivR 7.1(c))",
        "objection_to_magistrate_report": "14 days (FRCP 72(b))",
        "notice_of_appeal": "30 days from entry of judgment (FRAP 4(a)(1))",
    },
    "jury_demand": (
        "Must be made in the complaint or within 14 days after service "
        "of the last pleading directed to the issue.  FRCP Rule 38.  "
        "§1983 claims: right to jury trial on damages claims."
    ),
}


# =========================================================================
# PUBLIC API — Functions
# =========================================================================

def get_federal_forms() -> dict[str, Any]:
    """Return all federal court forms with metadata.

    Returns a dictionary keyed by form number, with each value being
    the serialized form data.
    """
    return {f.form_number: f.to_dict() for f in FEDERAL_FORMS}


def get_frcp_rules() -> dict[str, dict[str, str]]:
    """Return key FRCP rule summaries for §1983 practitioners.

    Returns ``FRCP_KEY_RULES`` — a dict keyed by rule number
    (e.g. ``"Rule 8"``) with title, summary, and deadline info.
    """
    return dict(FRCP_KEY_RULES)


def get_section_1983_requirements() -> dict[str, Any]:
    """Return elements, defenses, SOL, and damages for §1983 claims.

    Includes the four elements, immunity defenses (judicial, qualified,
    Eleventh Amendment), statute of limitations (3 years in Michigan),
    available damages, and key 6th Circuit precedent.
    """
    return dict(SECTION_1983_REQUIREMENTS)


def get_ifp_requirements() -> dict[str, Any]:
    """Return IFP (In Forma Pauperis) filing requirements.

    Covers AO 240 form, financial-disclosure obligations,
    §1915(e)(2) screening, and appeal options if denied.
    """
    return dict(IFP_REQUIREMENTS)


def get_wdmi_local_rules() -> dict[str, Any]:
    """Return WDMI-specific filing requirements.

    Covers CM/ECF e-filing, page limits, service requirements for
    government defendants, filing fees, response deadlines, and
    divisional information (Southern Division for Muskegon County).
    """
    return dict(WDMI_LOCAL_RULES_DETAIL)


def calculate_filing_deadlines(
    incident_dates: list[str | date | datetime],
) -> dict[str, Any]:
    """Calculate statute-of-limitations deadlines for §1983 claims.

    §1983 borrows Michigan's 3-year personal-injury SOL
    (MCL 600.5805(2)).  Federal accrual rules apply: the claim
    accrues when the plaintiff knows or has reason to know of the
    injury (Wallace v Kato, 549 U.S. 384).

    Parameters
    ----------
    incident_dates:
        Dates of the incidents giving rise to §1983 claims.
        Accepts ``"YYYY-MM-DD"`` strings, ``date``, or ``datetime``.

    Returns
    -------
    dict with:
      - ``deadlines`` — per-incident SOL deadline and urgency
      - ``sol_years`` — the applicable SOL period (3)
      - ``governing_law`` — citation to MCL and Wallace
      - ``notes`` — continuing-violation and tolling guidance
    """
    sol_years = 3
    today = date.today()
    deadlines: list[dict[str, Any]] = []

    for raw in incident_dates:
        if isinstance(raw, str):
            incident = date.fromisoformat(raw)
        elif isinstance(raw, datetime):
            incident = raw.date()
        elif isinstance(raw, date):
            incident = raw
        else:
            deadlines.append({
                "incident_date": str(raw),
                "error": f"Unsupported date type: {type(raw).__name__}",
            })
            continue

        sol_deadline = date(
            incident.year + sol_years,
            incident.month,
            incident.day,
        )
        days_remaining = (sol_deadline - today).days

        if days_remaining < 0:
            urgency = "EXPIRED"
        elif days_remaining <= 90:
            urgency = "CRITICAL"
        elif days_remaining <= 180:
            urgency = "URGENT"
        elif days_remaining <= 365:
            urgency = "APPROACHING"
        else:
            urgency = "OK"

        deadlines.append({
            "incident_date": incident.isoformat(),
            "sol_deadline": sol_deadline.isoformat(),
            "days_remaining": days_remaining,
            "urgency": urgency,
            "expired": days_remaining < 0,
        })

    return {
        "deadlines": deadlines,
        "sol_years": sol_years,
        "governing_law": (
            "MCL 600.5805(2) (Michigan 3-year personal injury SOL); "
            "Wallace v Kato, 549 U.S. 384 (2007) (federal accrual rules)"
        ),
        "notes": {
            "continuing_violation": (
                "If the constitutional violation is ongoing (not a "
                "discrete act), the continuing-violation doctrine may "
                "extend the accrual date to the last act in the series.  "
                "6th Cir: Sharpe v Cureton, 319 F.3d 259 (6th Cir. 2003)."
            ),
            "equitable_tolling": (
                "SOL may be tolled for extraordinary circumstances: "
                "incarceration, mental incapacity, fraudulent concealment "
                "by defendant.  Plaintiff bears burden of showing "
                "diligence and extraordinary circumstances."
            ),
            "discovery_rule": (
                "Claim accrues when plaintiff knows or should know of "
                "the injury — not when legal significance is understood.  "
                "For due-process claims: accrual when denied the process, "
                "not when final outcome is reached."
            ),
        },
    }


def get_form_by_number(form_number: str) -> dict[str, Any] | None:
    """Look up a single federal form by its form number.

    Returns the serialized form dict, or ``None`` if not found.
    Case-insensitive matching with whitespace normalization.
    """
    normalized = form_number.strip().upper()
    for f in FEDERAL_FORMS:
        if f.form_number.strip().upper() == normalized:
            return f.to_dict()
    return None


def get_forms_by_category(category: str) -> list[dict[str, Any]]:
    """Return all federal forms matching the given category.

    Category matching is case-insensitive.

    Common categories: ``"Initiating"``, ``"IFP"``, ``"Subpoena"``,
    ``"Motion"``, ``"Appellate"``, ``"Administrative"``.
    """
    cat = category.strip().lower()
    return [f.to_dict() for f in FEDERAL_FORMS if f.category.lower() == cat]


def get_filing_checklist() -> list[dict[str, str]]:
    """Return a step-by-step filing checklist for a §1983 action in WDMI.

    Ordered sequence of steps from complaint preparation through service.
    """
    return [
        {
            "step": "1",
            "action": "Prepare Complaint (Pro Se 1 or custom)",
            "form": "Pro Se 1",
            "details": (
                "Draft complaint identifying each defendant individually, "
                "the constitutional right violated, specific facts, and "
                "relief sought.  Must meet Iqbal/Twombly plausibility."
            ),
        },
        {
            "step": "2",
            "action": "Complete Civil Cover Sheet",
            "form": "JS 44",
            "details": (
                "Nature of Suit: 440.  Jurisdiction: Federal Question.  "
                "Complete all fields.  File with complaint."
            ),
        },
        {
            "step": "3",
            "action": "Prepare IFP Application (or pay $405 fee)",
            "form": "AO 240",
            "details": (
                "Complete financial affidavit honestly.  File with "
                "complaint if seeking fee waiver."
            ),
        },
        {
            "step": "4",
            "action": "File with Clerk — WDMI Southern Division",
            "form": "N/A",
            "details": (
                "File complaint + JS 44 + AO 240 (or filing fee) at "
                "WDMI Clerk's Office, 399 Federal Building, "
                "110 Michigan St NW, Grand Rapids, MI 49503.  "
                "Pro se may file on paper."
            ),
        },
        {
            "step": "5",
            "action": "Obtain Summons from Clerk",
            "form": "AO 440",
            "details": (
                "Clerk issues summons for each defendant after "
                "complaint is filed.  If IFP granted, request "
                "US Marshal service."
            ),
        },
        {
            "step": "6",
            "action": "Serve All Defendants Within 90 Days",
            "form": "AO 440",
            "details": (
                "Serve summons + complaint on each defendant per "
                "FRCP 4.  Government officials: certified mail to "
                "agency head + AG.  File proof of service (or waiver "
                "of service) with the court."
            ),
        },
        {
            "step": "7",
            "action": "File Proof of Service / Waiver",
            "form": "N/A",
            "details": (
                "File return of service (AO 440) or waiver of service "
                "(FRCP 4(d)) for each defendant.  Deadline for "
                "defendant's answer: 21 days after service (60 days "
                "if waiver accepted)."
            ),
        },
        {
            "step": "8",
            "action": "Attend Rule 16 Scheduling Conference",
            "form": "N/A",
            "details": (
                "Within 21 days after all defendants served, parties "
                "confer on case management plan (WDMI LCivR 16.1).  "
                "Court sets discovery deadlines, motion deadlines, "
                "and trial date."
            ),
        },
    ]
