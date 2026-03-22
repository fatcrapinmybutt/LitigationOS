"""Domestic Relations Judgment and Order Forms — Michigan SCAO forms.

Complete registry of SCAO domestic relations forms with required fields,
action routing, MCR references, order templates, and MCR 3.201–3.219
summaries.  Designed for Pigors v Watson (Case 2024-001507-DC), 14th
Circuit Court, Family Division, Muskegon County.  All data is local-only
— no external API calls.

PPO forms (CC 375–383) are intentionally NOT duplicated here; they live
in ``ppo_forms.py``.  Use ``ppo_forms.get_ppo_forms()`` for PPO-specific
lookups.

Sources:
  - Michigan Court Rules MCR 3.201–3.219
  - Michigan Compiled Laws MCL 552.1–552.651, MCL 722.21–722.31
  - courts.michigan.gov/SCAO-forms/ (March 2026)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# =============================================================================
# Data classes
# =============================================================================

@dataclass(frozen=True)
class DomesticForm:
    """Immutable descriptor for a single Michigan SCAO domestic relations form."""

    form_number: str
    title: str
    purpose: str
    required_fields: list[str]
    filing_court: str
    mcr_references: list[str]
    mcl_references: list[str]
    category: str = "Domestic Relations"
    url: str = "https://courts.michigan.gov/SCAO-forms/"
    practice_tips: str = ""
    filing_use: list[str] = field(default_factory=lambda: ["A"])

    def to_dict(self) -> dict[str, Any]:
        """Serialize to plain dictionary for JSON/DB compatibility."""
        return {
            "form_number": self.form_number,
            "title": self.title,
            "purpose": self.purpose,
            "required_fields": list(self.required_fields),
            "filing_court": self.filing_court,
            "mcr_references": list(self.mcr_references),
            "mcl_references": list(self.mcl_references),
            "category": self.category,
            "url": self.url,
            "practice_tips": self.practice_tips,
            "filing_use": list(self.filing_use),
        }


# =============================================================================
# DOMESTIC FORM REGISTRY — authoritative list of Michigan domestic relations
# forms.  PPO forms (CC 375–383) are in ppo_forms.py — not duplicated here.
# =============================================================================

DOMESTIC_FORMS: list[DomesticForm] = [
    # ----- Judgments of Divorce -------------------------------------------
    DomesticForm(
        form_number="CC 350",
        title="Judgment of Divorce (No Children)",
        purpose=(
            "Final judgment dissolving marriage when there are no minor "
            "children.  Addresses property division, spousal support, "
            "name restoration, and debt allocation."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "county",
            "judge_name",
            "plaintiff_name",
            "plaintiff_address",
            "defendant_name",
            "defendant_address",
            "date_of_marriage",
            "date_of_separation",
            "grounds_for_divorce",
            "property_division",
            "spousal_support_provisions",
            "debt_allocation",
            "name_restoration",
            "date_of_judgment",
            "judge_signature",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.201", "MCR 3.210", "MCR 3.211"],
        mcl_references=["MCL 552.6", "MCL 552.13", "MCL 552.19"],
        practice_tips=(
            "Ensure the Verified Statement (MC 302) and all settlement "
            "exhibits are filed before requesting a default or consent "
            "judgment.  Both parties should appear unless a default is "
            "being entered."
        ),
    ),
    DomesticForm(
        form_number="CC 351",
        title="Judgment of Divorce (With Children)",
        purpose=(
            "Final judgment dissolving marriage when there are minor "
            "children.  Addresses custody, parenting time, child support, "
            "property division, spousal support, and insurance.  Must "
            "incorporate uniform custody, parenting time, and support "
            "orders (CC 352, CC 353, CC 354)."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "county",
            "judge_name",
            "plaintiff_name",
            "plaintiff_address",
            "defendant_name",
            "defendant_address",
            "date_of_marriage",
            "date_of_separation",
            "grounds_for_divorce",
            "children_names_dobs",
            "custody_determination",
            "parenting_time_schedule",
            "child_support_amount",
            "child_support_payer",
            "health_insurance_provider",
            "property_division",
            "spousal_support_provisions",
            "debt_allocation",
            "name_restoration",
            "foc_info",
            "date_of_judgment",
            "judge_signature",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.201", "MCR 3.210", "MCR 3.211"],
        mcl_references=[
            "MCL 552.6", "MCL 552.13", "MCL 552.16",
            "MCL 722.23", "MCL 722.27a",
        ],
        practice_tips=(
            "Must attach uniform orders (CC 352, CC 353, CC 354).  Court "
            "must make best-interest findings under the Child Custody Act "
            "(MCL 722.23) on the record or in writing.  Include FOC "
            "information sheet and Verified Statement."
        ),
    ),

    # ----- Uniform Orders ------------------------------------------------
    DomesticForm(
        form_number="CC 352",
        title="Uniform Child Custody Order",
        purpose=(
            "Standard-format custody order required by MCR 3.211 to "
            "accompany any domestic relations judgment or post-judgment "
            "order involving custody.  Specifies legal and physical "
            "custody, sole or joint, and change-of-domicile restrictions."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "county",
            "judge_name",
            "plaintiff_name",
            "defendant_name",
            "children_names_dobs",
            "legal_custody_type",
            "physical_custody_type",
            "custodial_parent",
            "domicile_restrictions",
            "change_of_domicile_notice_requirement",
            "prior_order_modified",
            "date_of_order",
            "judge_signature",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.211(B)", "MCR 3.211(C)"],
        mcl_references=["MCL 722.23", "MCL 722.27", "MCL 722.31"],
        practice_tips=(
            "Must be accompanied by CC 353 (parenting time) and CC 354 "
            "(support) when part of a judgment.  Court must address all "
            "12 best-interest factors under MCL 722.23.  Include 100-mile "
            "change-of-domicile restriction per MCL 722.31."
        ),
    ),
    DomesticForm(
        form_number="CC 353",
        title="Uniform Parenting Time Order",
        purpose=(
            "Standard-format parenting time order required by MCR 3.211.  "
            "Sets out regular schedule, holiday schedule, vacation, "
            "transportation responsibilities, and make-up time provisions."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "county",
            "judge_name",
            "plaintiff_name",
            "defendant_name",
            "children_names_dobs",
            "regular_parenting_time_schedule",
            "holiday_schedule",
            "summer_vacation_schedule",
            "school_break_schedule",
            "transportation_responsibility",
            "exchange_location",
            "right_of_first_refusal",
            "makeup_time_provisions",
            "communication_provisions",
            "prior_order_modified",
            "date_of_order",
            "judge_signature",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.211(B)", "MCR 3.211(D)"],
        mcl_references=["MCL 722.27a", "MCL 722.27b"],
        practice_tips=(
            "Be as specific as possible — vague schedules generate "
            "contempt disputes.  Include makeup time for denied or "
            "missed parenting time (MCL 722.27a(7)).  Specify holiday "
            "alternation (odd/even year) to prevent annual litigation."
        ),
    ),
    DomesticForm(
        form_number="CC 354",
        title="Uniform Support Order",
        purpose=(
            "Standard-format support order required by MCR 3.211.  "
            "Addresses child support amount, health insurance, medical "
            "expenses, childcare costs, and income withholding."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "county",
            "judge_name",
            "plaintiff_name",
            "plaintiff_income",
            "defendant_name",
            "defendant_income",
            "children_names_dobs",
            "child_support_amount",
            "child_support_payer",
            "effective_date",
            "health_insurance_provider",
            "health_insurance_cost_allocation",
            "uninsured_medical_expense_allocation",
            "childcare_cost_allocation",
            "income_withholding_order",
            "arrearage_amount",
            "prior_order_modified",
            "date_of_order",
            "judge_signature",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.211(B)", "MCR 3.214"],
        mcl_references=[
            "MCL 552.602", "MCL 552.605", "MCL 552.517",
            "MCL 552.519",
        ],
        practice_tips=(
            "Support must be calculated under the Michigan Child "
            "Support Formula.  Deviation requires specific written "
            "findings.  Attach completed Michigan Child Support "
            "Formula computation.  Income must be verified with pay "
            "stubs, tax returns, or employer verification."
        ),
    ),

    # ----- Post-Judgment Orders ------------------------------------------
    DomesticForm(
        form_number="CC 355",
        title="Order Regarding Custody/Parenting Time",
        purpose=(
            "Post-judgment order modifying or clarifying custody and/or "
            "parenting time after the original judgment has been entered.  "
            "Used when a motion to modify (CC 356/CC 357) is granted."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "county",
            "judge_name",
            "plaintiff_name",
            "defendant_name",
            "children_names_dobs",
            "current_custody_arrangement",
            "new_custody_arrangement",
            "reason_for_modification",
            "best_interest_findings",
            "effective_date",
            "prior_order_date",
            "date_of_order",
            "judge_signature",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.210", "MCR 3.211"],
        mcl_references=["MCL 722.27", "MCL 722.27a"],
        practice_tips=(
            "Court must find proper cause or change of circumstances "
            "before revisiting custody under MCL 722.27(1)(c).  The "
            "established custodial environment (ECE) determines the "
            "burden of proof: preponderance if no ECE change, clear "
            "and convincing if ECE would be altered."
        ),
    ),

    # ----- Motions -------------------------------------------------------
    DomesticForm(
        form_number="CC 356",
        title="Motion Regarding Custody",
        purpose=(
            "Motion to modify, clarify, or enforce an existing custody "
            "order.  Must allege proper cause or change of circumstances "
            "to justify revisiting custody.  May be filed by either party."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "county",
            "plaintiff_name",
            "defendant_name",
            "children_names_dobs",
            "current_custody_order_date",
            "current_custody_arrangement",
            "proper_cause_or_change_of_circumstances",
            "requested_custody_modification",
            "best_interest_factors_affected",
            "supporting_facts",
            "movant_signature",
            "date_filed",
            "certificate_of_service",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.210", "MCR 3.213"],
        mcl_references=["MCL 722.27(1)(c)", "MCL 722.23"],
        practice_tips=(
            "The threshold showing of proper cause / change of "
            "circumstances is a GATEKEEPING function — court must "
            "decide this before holding an evidentiary hearing on "
            "the merits.  Vodvarka v Grasmeyer (2002) governs the "
            "threshold.  Allege specific, concrete changes since "
            "the last order, not generalities."
        ),
    ),
    DomesticForm(
        form_number="CC 357",
        title="Motion Regarding Parenting Time",
        purpose=(
            "Motion to modify, clarify, or enforce an existing parenting "
            "time order.  Unlike custody, parenting-time modifications "
            "do not require the stringent 'proper cause / change of "
            "circumstances' threshold — the best-interest standard "
            "applies directly."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "county",
            "plaintiff_name",
            "defendant_name",
            "children_names_dobs",
            "current_parenting_time_order_date",
            "current_parenting_time_schedule",
            "requested_modification",
            "reason_for_modification",
            "best_interest_factors_affected",
            "supporting_facts",
            "movant_signature",
            "date_filed",
            "certificate_of_service",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.210", "MCR 3.213"],
        mcl_references=["MCL 722.27a", "MCL 722.27b"],
        practice_tips=(
            "Parenting-time motions have a LOWER threshold than custody "
            "motions.  MCL 722.27a(1) allows modification whenever the "
            "court finds it in the child's best interest.  Document "
            "every instance of denied or interfered-with parenting time "
            "— dates, times, witnesses.  Attach a proposed schedule."
        ),
    ),
    DomesticForm(
        form_number="CC 358",
        title="Motion Regarding Support",
        purpose=(
            "Motion to modify, terminate, or enforce child support or "
            "spousal support.  Must demonstrate a change of circumstances "
            "sufficient to justify recalculation under the Michigan "
            "Child Support Formula."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "county",
            "plaintiff_name",
            "defendant_name",
            "children_names_dobs",
            "current_support_order_date",
            "current_support_amount",
            "requested_modification",
            "change_of_circumstances",
            "current_income_plaintiff",
            "current_income_defendant",
            "supporting_documentation",
            "movant_signature",
            "date_filed",
            "certificate_of_service",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.214"],
        mcl_references=[
            "MCL 552.602", "MCL 552.605", "MCL 552.17",
        ],
        practice_tips=(
            "A change exceeding 10%% of the current support amount is "
            "generally sufficient to establish changed circumstances.  "
            "File promptly — modifications are retroactive only to the "
            "filing date of the motion, not the date circumstances "
            "changed.  Attach updated income documentation."
        ),
    ),

    # ----- General Motions & Responses ------------------------------------
    DomesticForm(
        form_number="MC 20",
        title="Motion (General)",
        purpose=(
            "Multipurpose motion form usable in any Michigan court.  In "
            "domestic relations, used for motions not covered by specific "
            "SCAO forms: motions to compel, motions for sanctions, motions "
            "in limine, motions to adjourn, and other procedural requests."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "county",
            "plaintiff_name",
            "defendant_name",
            "motion_title",
            "relief_requested",
            "supporting_facts",
            "legal_authority",
            "movant_signature",
            "date_filed",
            "certificate_of_service",
        ],
        filing_court="Any Michigan Court",
        mcr_references=["MCR 2.119"],
        mcl_references=[],
        category="General",
        practice_tips=(
            "Must be accompanied by a brief or supporting affidavit "
            "under MCR 2.119(A)(2).  Service at least 9 days before "
            "hearing for personally served motions, 14 days for mail "
            "service.  Response must be filed at least 5 days before "
            "hearing.  Reply: at least 3 days before hearing."
        ),
    ),
    DomesticForm(
        form_number="MC 21",
        title="Response to Motion",
        purpose=(
            "Response/answer to any motion filed in Michigan court.  "
            "Used to oppose or partially agree with the movant's request.  "
            "May include counter-arguments, supporting affidavits, and "
            "alternative relief requests."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "county",
            "plaintiff_name",
            "defendant_name",
            "motion_being_responded_to",
            "hearing_date",
            "response_arguments",
            "supporting_facts",
            "legal_authority",
            "relief_requested",
            "respondent_signature",
            "date_filed",
            "certificate_of_service",
        ],
        filing_court="Any Michigan Court",
        mcr_references=["MCR 2.119(C)"],
        mcl_references=[],
        category="General",
        practice_tips=(
            "Must be filed and served at least 5 days before the "
            "hearing date under MCR 2.119(C)(2).  If you fail to "
            "file a response, the court may grant the motion as "
            "unopposed.  Always attach supporting affidavits or "
            "documentary evidence."
        ),
    ),
    DomesticForm(
        form_number="MC 22",
        title="Notice of Hearing",
        purpose=(
            "Notifies all parties of a scheduled court hearing.  Must "
            "be served with the motion and comply with MCR 2.119 "
            "timing requirements."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "county",
            "judge_name",
            "plaintiff_name",
            "defendant_name",
            "hearing_date",
            "hearing_time",
            "hearing_location",
            "courtroom",
            "matter_to_be_heard",
            "requesting_party_signature",
            "date_filed",
            "certificate_of_service",
        ],
        filing_court="Any Michigan Court",
        mcr_references=["MCR 2.119(C)"],
        mcl_references=[],
        category="General",
        practice_tips=(
            "Serve with the motion.  Hearing must be at least 9 days "
            "after personal service or 14 days after mail service.  "
            "Confirm the hearing date and time with the court clerk "
            "BEFORE filing the notice."
        ),
    ),

    # ----- Financial / Verified Statements --------------------------------
    DomesticForm(
        form_number="MC 302",
        title="Verified Statement",
        purpose=(
            "Sworn financial disclosure required in all domestic "
            "relations actions under MCR 3.206(C).  Discloses income, "
            "assets, debts, monthly expenses, and other financial "
            "information to the court and opposing party."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "party_name",
            "party_address",
            "employer_name",
            "employer_address",
            "gross_income",
            "net_income",
            "other_income_sources",
            "monthly_expenses",
            "real_property",
            "personal_property",
            "debts_and_obligations",
            "insurance_coverage",
            "verification_signature",
            "notarization",
            "date_filed",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.206(C)"],
        mcl_references=["MCL 552.6(3)"],
        category="Financial",
        practice_tips=(
            "REQUIRED at filing of complaint and again before any "
            "support hearing.  Must be verified (signed under oath).  "
            "Failure to file may result in the court refusing to "
            "schedule hearings or entering orders adverse to the "
            "non-filing party.  Update whenever financial "
            "circumstances change."
        ),
    ),
    DomesticForm(
        form_number="MC 303",
        title="Fee Waiver Request",
        purpose=(
            "Request to waive court filing fees on the basis of "
            "indigency or inability to pay.  Must be supported by "
            "the Verified Statement (MC 302) showing income at or "
            "below 125%% of the federal poverty guidelines."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "party_name",
            "party_address",
            "monthly_income",
            "monthly_expenses",
            "dependents",
            "public_assistance_status",
            "reason_for_request",
            "applicant_signature",
            "date_filed",
        ],
        filing_court="Any Michigan Court",
        mcr_references=["MCR 2.002"],
        mcl_references=["MCL 600.2529"],
        category="Financial",
        practice_tips=(
            "File with the complaint or at any point during the case.  "
            "Attach MC 302 as supporting documentation.  The court "
            "must grant the waiver if the party demonstrates inability "
            "to pay.  If denied, you may request a hearing."
        ),
    ),

    # ----- Complaint / Case Initiation -----------------------------------
    DomesticForm(
        form_number="DC 100",
        title="Complaint (General Civil)",
        purpose=(
            "General civil complaint form usable in all Michigan trial "
            "courts.  In a domestic relations context, used for filing "
            "independent civil actions related to the family case — "
            "e.g., tort claims, property disputes (Shady Oaks housing), "
            "or fraud actions — separate from the divorce/custody docket."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "county",
            "plaintiff_name",
            "plaintiff_address",
            "defendant_name",
            "defendant_address",
            "jurisdiction_basis",
            "factual_allegations",
            "causes_of_action",
            "relief_requested",
            "demand_for_jury_trial",
            "plaintiff_signature",
            "date_filed",
        ],
        filing_court="Circuit Court / District Court",
        mcr_references=["MCR 2.111", "MCR 2.113"],
        mcl_references=["MCL 600.1605", "MCL 600.1629"],
        category="Civil Complaint",
        practice_tips=(
            "Verify proper court and jurisdiction before filing.  "
            "Circuit court has jurisdiction for amounts over $25,000 "
            "and equitable claims.  In Pigors v Watson, DC 100 is "
            "relevant for the Shady Oaks housing/title dispute "
            "(Lane B: 2025-002760-CZ) — not for custody matters."
        ),
    ),

    # ----- Guardianship / Conservatorship (GC forms) ----------------------
    DomesticForm(
        form_number="GC 100",
        title="Petition for Appointment of Guardian of Minor",
        purpose=(
            "Petition for appointment of a guardian for a minor child.  "
            "Used when a non-parent seeks guardianship or when the court "
            "determines that neither parent is fit.  Rare in standard "
            "custody disputes but relevant if custody is being removed "
            "from both parents."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "county",
            "petitioner_name",
            "petitioner_address",
            "petitioner_relationship_to_minor",
            "minor_name",
            "minor_dob",
            "minor_address",
            "parents_names_addresses",
            "reason_guardianship_needed",
            "proposed_guardian_name",
            "proposed_guardian_qualifications",
            "petitioner_signature",
            "date_filed",
        ],
        filing_court="Probate Court / Circuit Court — Family Division",
        mcr_references=["MCR 5.404"],
        mcl_references=["MCL 700.5204", "MCL 700.5205"],
        category="Guardianship",
        practice_tips=(
            "Guardianship of a minor is typically filed in probate "
            "court.  However, the circuit court family division has "
            "concurrent jurisdiction under MCL 722.26a when a "
            "domestic relations case is already pending.  Requires "
            "14-day notice to all interested parties."
        ),
    ),
    DomesticForm(
        form_number="GC 104",
        title="Petition for Appointment of Conservator of Minor",
        purpose=(
            "Petition for appointment of a conservator to manage a "
            "minor's property or estate.  Relevant when a minor has "
            "assets requiring professional management — e.g., settlement "
            "funds, inheritance, or insurance proceeds."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "county",
            "petitioner_name",
            "petitioner_address",
            "minor_name",
            "minor_dob",
            "minor_address",
            "parents_names_addresses",
            "description_of_estate",
            "reason_conservatorship_needed",
            "proposed_conservator_name",
            "petitioner_signature",
            "date_filed",
        ],
        filing_court="Probate Court",
        mcr_references=["MCR 5.404"],
        mcl_references=["MCL 700.5401", "MCL 700.5402"],
        category="Guardianship",
        practice_tips=(
            "Less common in standard domestic relations cases.  "
            "Relevant if the child receives a personal injury "
            "settlement, inheritance, or other assets exceeding "
            "$5,000.  Conservator must file annual accountings."
        ),
    ),

    # ----- Additional Domestic Relations Forms ----------------------------
    DomesticForm(
        form_number="CC 359",
        title="Domestic Relations Order (QDRO/EDRO)",
        purpose=(
            "Qualified Domestic Relations Order for division of "
            "retirement benefits, pensions, 401(k), and other employer- "
            "sponsored plans upon divorce.  Must comply with ERISA and "
            "the plan's specific requirements."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "county",
            "judge_name",
            "plaintiff_name",
            "defendant_name",
            "plan_name",
            "plan_administrator",
            "participant_name",
            "alternate_payee_name",
            "benefit_division_method",
            "percentage_or_amount",
            "survivor_benefit_election",
            "date_of_order",
            "judge_signature",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.211"],
        mcl_references=["MCL 552.101"],
        practice_tips=(
            "QDRO must be approved by the plan administrator BEFORE "
            "entry.  Draft the QDRO and submit to the plan for "
            "pre-approval.  Each retirement plan requires a separate "
            "QDRO.  Timing is critical — file promptly after judgment "
            "to avoid changes in benefit value."
        ),
    ),
    DomesticForm(
        form_number="CC 360",
        title="Ex Parte Order (Domestic Relations)",
        purpose=(
            "Emergency ex parte order in domestic relations cases.  "
            "Used for temporary custody, temporary parenting time "
            "suspension, asset freezes, or other emergency relief "
            "when waiting for a hearing would cause irreparable harm."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "county",
            "judge_name",
            "plaintiff_name",
            "defendant_name",
            "emergency_circumstances",
            "irreparable_harm_showing",
            "specific_relief_requested",
            "temporary_provisions",
            "hearing_date_for_full_hearing",
            "date_of_order",
            "judge_signature",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.207"],
        mcl_references=["MCL 722.27(1)"],
        practice_tips=(
            "Must demonstrate irreparable injury, loss, or damage "
            "from delay.  Ex parte orders are TEMPORARY — the court "
            "must schedule a full hearing within 14–21 days.  Serve "
            "the opposing party immediately after entry.  Failure to "
            "serve may result in the order being vacated."
        ),
    ),
    DomesticForm(
        form_number="MC 245",
        title="Order of Contempt / Conditional Sentence",
        purpose=(
            "Order holding a party in civil or criminal contempt of "
            "court.  In domestic relations, used to enforce custody, "
            "parenting-time, and support orders.  Includes purge "
            "conditions for civil contempt."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "county",
            "judge_name",
            "contemnor_name",
            "order_violated",
            "date_of_violation",
            "nature_of_violation",
            "finding_of_contempt",
            "civil_or_criminal",
            "purge_conditions",
            "sentence",
            "date_of_order",
            "judge_signature",
        ],
        filing_court="Any Michigan Court",
        mcr_references=["MCR 3.606"],
        mcl_references=["MCL 600.1701", "MCL 600.1715"],
        category="Enforcement",
        practice_tips=(
            "Civil contempt: coercive — contemnor can purge by "
            "complying.  Criminal contempt: punitive — up to 93 days "
            "and/or $7,500 fine per violation.  Due process rights "
            "attach: right to counsel for criminal contempt (MCR "
            "3.606(A)), right to a hearing, right to present evidence."
        ),
    ),
    DomesticForm(
        form_number="MC 280",
        title="Subpoena (Civil) — Domestic Relations",
        purpose=(
            "Subpoena to compel witness attendance or document "
            "production in domestic relations proceedings.  Used for "
            "depositions, hearings, and trial testimony."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "plaintiff_name",
            "defendant_name",
            "witness_name",
            "witness_address",
            "date_and_time_of_appearance",
            "location",
            "documents_to_produce",
            "issuing_party_signature",
            "date_issued",
        ],
        filing_court="Any Michigan Court",
        mcr_references=["MCR 2.506"],
        mcl_references=["MCL 600.1455", "MCL 600.1701"],
        category="General",
        practice_tips=(
            "Must be personally served.  Witness fees and mileage "
            "must be tendered at time of service.  Non-party "
            "witnesses may move to quash within a reasonable time.  "
            "In family-division matters, be cautious about subpoenaing "
            "the child or child's therapist — seek court guidance first."
        ),
    ),
    DomesticForm(
        form_number="CC 368",
        title="Affidavit of Parentage",
        purpose=(
            "Sworn statement establishing parentage.  Used in paternity "
            "cases or when custody/support must be established for a "
            "child born outside of marriage."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "county",
            "mother_name",
            "mother_address",
            "father_name",
            "father_address",
            "child_name",
            "child_dob",
            "child_birthplace",
            "acknowledgment_of_paternity",
            "affiant_signature",
            "notarization",
            "date_filed",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.201"],
        mcl_references=["MCL 722.1001", "MCL 722.1003"],
        category="Paternity",
        practice_tips=(
            "An acknowledged Affidavit of Parentage has the same "
            "legal effect as a court order of filiation.  Either "
            "parent may revoke within 60 days.  After 60 days, "
            "revocation requires clear and convincing evidence of "
            "fraud, duress, or material mistake of fact."
        ),
    ),
    DomesticForm(
        form_number="MC 290",
        title="Proof of Service",
        purpose=(
            "Certificate documenting that a document was properly "
            "served on the opposing party or other person.  Required "
            "for all filings under MCR 2.107.  Must state method, "
            "date, and manner of service."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "document_served",
            "person_served",
            "date_of_service",
            "method_of_service",
            "server_name",
            "server_address",
            "server_signature",
            "date_filed",
        ],
        filing_court="Any Michigan Court",
        mcr_references=["MCR 2.107"],
        mcl_references=[],
        category="Service",
        practice_tips=(
            "File proof of service with the court for EVERY document "
            "served.  Personal service: process server files the "
            "proof.  Mail service: certificate by the mailing party.  "
            "In Pigors v Watson, document EVERY service failure and "
            "nonservice event for the record."
        ),
    ),
]


# =============================================================================
# Internal lookup index — O(1) access by form number
# =============================================================================

_FORM_INDEX: dict[str, DomesticForm] = {f.form_number: f for f in DOMESTIC_FORMS}


# =============================================================================
# ACTION ROUTING MAP — maps litigation actions to form numbers
# =============================================================================

_ACTION_MAP: dict[str, list[str]] = {
    # --- custody ---
    "custody": ["CC 352", "CC 355", "CC 356"],
    "custody_modification": ["CC 356", "CC 352", "CC 355"],
    "custody_enforcement": ["CC 356", "MC 245"],
    "custody_order": ["CC 352", "CC 355"],
    "change_custody": ["CC 356", "CC 352"],

    # --- parenting time ---
    "parenting_time": ["CC 353", "CC 355", "CC 357"],
    "parenting_time_modification": ["CC 357", "CC 353", "CC 355"],
    "parenting_time_enforcement": ["CC 357", "MC 245"],
    "parenting_time_order": ["CC 353", "CC 355"],
    "visitation": ["CC 353", "CC 357"],
    "makeup_parenting_time": ["CC 357", "CC 353"],
    "denied_parenting_time": ["CC 357", "MC 245"],

    # --- support ---
    "support": ["CC 354", "CC 358"],
    "support_modification": ["CC 358", "CC 354"],
    "support_enforcement": ["CC 358", "MC 245"],
    "child_support": ["CC 354", "CC 358"],
    "spousal_support": ["CC 354", "CC 358"],
    "alimony": ["CC 354", "CC 358"],
    "support_order": ["CC 354"],

    # --- contempt / enforcement ---
    "contempt": ["MC 245", "MC 20"],
    "enforcement": ["MC 245", "MC 20"],
    "show_cause": ["MC 245", "MC 20"],
    "civil_contempt": ["MC 245"],
    "criminal_contempt": ["MC 245"],
    "sanctions": ["MC 20", "MC 245"],

    # --- divorce / judgment ---
    "divorce": ["CC 351", "CC 350"],
    "divorce_with_children": ["CC 351", "CC 352", "CC 353", "CC 354"],
    "divorce_no_children": ["CC 350"],
    "judgment": ["CC 351", "CC 350"],
    "property_division": ["CC 351", "CC 350"],
    "qdro": ["CC 359"],
    "retirement_division": ["CC 359"],

    # --- emergency / ex parte ---
    "emergency": ["CC 360", "MC 20"],
    "ex_parte": ["CC 360"],
    "temporary_custody": ["CC 360", "CC 352"],
    "temporary_order": ["CC 360"],

    # --- motions / responses ---
    "motion": ["MC 20"],
    "response": ["MC 21"],
    "response_to_motion": ["MC 21"],
    "notice_of_hearing": ["MC 22"],
    "hearing": ["MC 22"],
    "motion_to_compel": ["MC 20"],
    "motion_for_sanctions": ["MC 20"],
    "motion_in_limine": ["MC 20"],

    # --- financial ---
    "financial_disclosure": ["MC 302"],
    "verified_statement": ["MC 302"],
    "fee_waiver": ["MC 303"],
    "indigency": ["MC 303"],

    # --- service ---
    "proof_of_service": ["MC 290"],
    "service": ["MC 290"],

    # --- paternity / parentage ---
    "paternity": ["CC 368"],
    "parentage": ["CC 368"],

    # --- guardianship ---
    "guardianship": ["GC 100"],
    "conservatorship": ["GC 104"],
    "guardian_of_minor": ["GC 100"],
    "conservator_of_minor": ["GC 104"],

    # --- subpoena ---
    "subpoena": ["MC 280"],
    "witness": ["MC 280"],

    # --- general civil (Lane B — Shady Oaks) ---
    "civil_complaint": ["DC 100"],
    "general_civil": ["DC 100"],
    "property_dispute": ["DC 100"],
    "housing": ["DC 100"],

    # --- PPO (cross-reference to ppo_forms.py — NOT duplicated) ---
    "ppo": [],
    "personal_protection_order": [],
}


# =============================================================================
# MCR 3.201–3.219 REFERENCE TABLE — Domestic Relations rules
# =============================================================================

MCR_DOMESTIC_RULES: dict[str, dict[str, str]] = {
    "MCR 3.201": {
        "title": "Applicability of Rules — Domestic Relations Actions",
        "scope": (
            "Defines the scope of MCR Subchapter 3.200 rules.  Applies "
            "to actions for divorce, separate maintenance, annulment, "
            "paternity, custody, parenting time, and support."
        ),
        "key_provisions": (
            "Covers all domestic relations proceedings in circuit court "
            "family division.  General civil rules (MCR 2.xxx) also "
            "apply unless specifically superseded."
        ),
    },
    "MCR 3.203": {
        "title": "Venue in Domestic Relations Actions",
        "scope": (
            "Establishes proper venue for filing domestic relations "
            "actions: county where plaintiff or defendant resides."
        ),
        "key_provisions": (
            "Action may be filed in the county where either party "
            "resides.  Muskegon County is proper venue for Pigors v "
            "Watson.  Transfer of venue requires motion and good cause."
        ),
    },
    "MCR 3.205": {
        "title": "Prior and Subsequent Orders and Judgments",
        "scope": (
            "Governs disclosure of prior and pending actions affecting "
            "custody, parenting time, and personal protection orders."
        ),
        "key_provisions": (
            "Each party must disclose prior/pending actions in other "
            "courts (UCCJEA compliance).  Court may communicate with "
            "other jurisdictions."
        ),
    },
    "MCR 3.206": {
        "title": "Initiating a Domestic Relations Action",
        "scope": (
            "Procedures for filing the complaint, verified statement, "
            "summons, and initial disclosures in domestic relations."
        ),
        "key_provisions": (
            "Complaint must include jurisdictional allegations.  "
            "Verified Statement (MC 302) must be filed with complaint.  "
            "Ex parte relief available under MCR 3.207 upon showing "
            "of irreparable injury."
        ),
    },
    "MCR 3.207": {
        "title": "Ex Parte Orders in Domestic Relations",
        "scope": (
            "Standards and procedures for ex parte relief in domestic "
            "relations cases."
        ),
        "key_provisions": (
            "Must show irreparable injury, loss, or damage will result "
            "from delay.  Ex parte orders are temporary.  Subject to "
            "objection and hearing on 14 days' notice.  Party against "
            "whom order is entered may move to modify or dissolve."
        ),
    },
    "MCR 3.208": {
        "title": "Friend of the Court",
        "scope": (
            "Powers and duties of the Friend of the Court: investigation, "
            "recommendation, enforcement, and mediation."
        ),
        "key_provisions": (
            "FOC investigates and recommends on custody, parenting time, "
            "and support.  FOC may initiate contempt proceedings.  FOC "
            "mediates disputes before hearing.  Parties may opt out of "
            "FOC services under limited circumstances."
        ),
    },
    "MCR 3.210": {
        "title": "Hearing Procedures in Domestic Relations",
        "scope": (
            "Governs custody investigations, best-interest evaluations, "
            "and procedures for custody/parenting-time hearings."
        ),
        "key_provisions": (
            "Court may order investigation by FOC, GAL, or other "
            "professional.  Investigation must address best-interest "
            "factors (MCL 722.23).  Report provided to parties before "
            "hearing.  Parties may cross-examine investigator.  "
            "Attorney-evaluator may be appointed."
        ),
    },
    "MCR 3.211": {
        "title": "Judgment and Order Provisions",
        "scope": (
            "Required provisions in domestic relations judgments and "
            "post-judgment orders."
        ),
        "key_provisions": (
            "Judgment must address custody, parenting time, support, "
            "property division, insurance, and change-of-domicile "
            "restrictions.  Uniform orders (CC 352, 353, 354) required.  "
            "Income withholding must be included.  Specific findings "
            "required for any deviation from the Child Support Formula."
        ),
    },
    "MCR 3.212": {
        "title": "Post-Judgment Transfer of Domestic Relations Cases",
        "scope": (
            "Procedures for transferring a case to another county "
            "when both parties have relocated."
        ),
        "key_provisions": (
            "Court may transfer if parties and child no longer reside "
            "in the county.  Receiving court's FOC assumes enforcement.  "
            "Case file and all orders transfer."
        ),
    },
    "MCR 3.213": {
        "title": "Motions for Post-Judgment Modification",
        "scope": (
            "Governs motions to modify custody, parenting time, and "
            "support after the original judgment."
        ),
        "key_provisions": (
            "Custody modifications require proper cause or change of "
            "circumstances (Vodvarka threshold).  Parenting-time "
            "modifications: best-interest standard.  Support: change "
            "of circumstances or passage of time.  Must file motion "
            "and serve on opposing party and FOC."
        ),
    },
    "MCR 3.214": {
        "title": "Support Proceedings",
        "scope": (
            "Governs establishment, modification, and enforcement of "
            "child support and spousal support."
        ),
        "key_provisions": (
            "Michigan Child Support Formula is presumptively correct.  "
            "Deviation requires specific written findings on the record.  "
            "Income must be verified with documentation.  Support "
            "arrearages accrue interest.  Income withholding is mandatory."
        ),
    },
    "MCR 3.215": {
        "title": "Domestic Relations Mediation",
        "scope": (
            "Establishes mediation procedures for custody and "
            "parenting-time disputes."
        ),
        "key_provisions": (
            "Court may order mediation.  Mediator communications are "
            "confidential.  Mediation may not be ordered if there is "
            "a history of domestic violence.  Mediator may not make "
            "recommendations to the court."
        ),
    },
    "MCR 3.216": {
        "title": "Domestic Relations Arbitration",
        "scope": (
            "Voluntary arbitration of domestic relations disputes."
        ),
        "key_provisions": (
            "Parties may agree to binding arbitration.  Custody and "
            "parenting time are NOT subject to binding arbitration — "
            "court retains ultimate authority over child welfare."
        ),
    },
    "MCR 3.217": {
        "title": "Default in Domestic Relations",
        "scope": (
            "Procedures for entering default when a party fails to "
            "plead or otherwise defend."
        ),
        "key_provisions": (
            "Plaintiff may request entry of default.  Default judgment "
            "still requires testimony on the record.  Court must "
            "address custody, support, and property even in default.  "
            "Motion to set aside default under MCR 2.603(D)."
        ),
    },
    "MCR 3.218": {
        "title": "Referee Hearings — Recommendations and Objections",
        "scope": (
            "Governs proceedings before domestic relations referees "
            "and the objection process."
        ),
        "key_provisions": (
            "Referees make recommendations to the judge.  Parties have "
            "21 days from service to file written objections.  Objection "
            "triggers de novo hearing before the judge.  Failure to "
            "object = recommendation becomes binding order.  Judge owes "
            "NO deference to referee at de novo hearing."
        ),
    },
    "MCR 3.219": {
        "title": "Case Management in Domestic Relations",
        "scope": (
            "Case management procedures and scheduling in domestic "
            "relations actions."
        ),
        "key_provisions": (
            "Court must enter a scheduling order.  Discovery cutoffs, "
            "ADR deadlines, and trial date must be set.  Status "
            "conferences may be required.  Court may impose sanctions "
            "for failure to comply with the scheduling order."
        ),
    },
}


# =============================================================================
# ORDER TEMPLATES — proposed order skeletons for custody, parenting time,
# and support.  Plaintiff: Andrew James Pigors.  Defendant: Emily A. Watson.
# =============================================================================

_ORDER_TEMPLATES: dict[str, str] = {
    "custody_order": """\
STATE OF MICHIGAN
IN THE 14TH JUDICIAL CIRCUIT COURT FOR MUSKEGON COUNTY
FAMILY DIVISION

Case No. {case_number}
Hon. {judge_name}

ANDREW JAMES PIGORS,
    Plaintiff,

v.

EMILY A. WATSON,
    Defendant.
______________________________________________/

ORDER REGARDING CUSTODY

    At a session of said Court held in the City of Muskegon,
County of Muskegon, State of Michigan, on _______________.

PRESENT: Hon. {judge_name}, Circuit Judge.

    This matter having come before the Court on Plaintiff's
Motion Regarding Custody, and the Court having reviewed the
pleadings, evidence, and arguments of the parties, and being
otherwise fully advised in the premises;

IT IS HEREBY ORDERED:

1.  LEGAL CUSTODY: [Joint / Sole to Plaintiff / Sole to Defendant]
    legal custody of the minor child, L.D.W., is awarded to
    _________________________.

2.  PHYSICAL CUSTODY: [Joint / Primary to Plaintiff / Primary to
    Defendant] physical custody of the minor child, L.D.W., is
    awarded to _________________________.

3.  BEST-INTEREST FINDINGS: The Court has considered the best-
    interest factors set forth in MCL 722.23 and finds as follows:

    (a) Factor (a) — Love, affection, and emotional ties:
        ________________________________________________

    (b) Factor (b) — Capacity to provide love, affection, guidance:
        ________________________________________________

    (c) Factor (c) — Capacity to provide food, clothing, medical:
        ________________________________________________

    (d) Factor (d) — Length of time in stable environment:
        ________________________________________________

    (e) Factor (e) — Permanence of family unit:
        ________________________________________________

    (f) Factor (f) — Moral fitness:
        ________________________________________________

    (g) Factor (g) — Mental and physical health:
        ________________________________________________

    (h) Factor (h) — Home, school, and community record:
        ________________________________________________

    (i) Factor (i) — Reasonable preference of the child:
        ________________________________________________

    (j) Factor (j) — Willingness to facilitate relationship:
        ________________________________________________

    (k) Factor (k) — Domestic violence:
        ________________________________________________

    (l) Factor (l) — Any other relevant factor:
        ________________________________________________

4.  CHANGE OF DOMICILE: Neither party shall move the minor child's
    legal residence more than 100 miles from the child's current
    residence without prior court approval, pursuant to MCL 722.31.

5.  This Order supersedes all prior custody orders in this matter.

IT IS SO ORDERED.

Dated: _______________

                        ________________________________
                        Hon. {judge_name}
                        14th Circuit Court, Family Division
""",

    "parenting_time_order": """\
STATE OF MICHIGAN
IN THE 14TH JUDICIAL CIRCUIT COURT FOR MUSKEGON COUNTY
FAMILY DIVISION

Case No. {case_number}
Hon. {judge_name}

ANDREW JAMES PIGORS,
    Plaintiff,

v.

EMILY A. WATSON,
    Defendant.
______________________________________________/

ORDER REGARDING PARENTING TIME

    At a session of said Court held in the City of Muskegon,
County of Muskegon, State of Michigan, on _______________.

PRESENT: Hon. {judge_name}, Circuit Judge.

    This matter having come before the Court on Plaintiff's
Motion Regarding Parenting Time, and the Court having reviewed
the pleadings, evidence, and arguments of the parties;

IT IS HEREBY ORDERED:

1.  REGULAR PARENTING TIME SCHEDULE:
    The [non-custodial parent / Plaintiff / Defendant] shall have
    parenting time with the minor child, L.D.W., as follows:

    a. Every other weekend from Friday at _____ p.m. to Sunday
       at _____ p.m.
    b. One weekday evening per week from _____ p.m. to _____ p.m.
    c. [Additional regular parenting time provisions]

2.  HOLIDAY SCHEDULE (alternating odd/even years):
    a. Thanksgiving: [Odd years with Plaintiff / Even years with
       Defendant], Wednesday at 6:00 p.m. through Sunday at 6:00 p.m.
    b. Christmas/Winter Break: [First half / Second half alternating]
    c. Spring Break: [Alternating by year]
    d. Mother's Day/Father's Day: With the respective parent
    e. Child's Birthday: [Provisions]
    f. [Additional holidays]

3.  SUMMER VACATION:
    Each parent shall have _____ consecutive weeks during the
    summer.  Written notice of intended dates at least 30 days
    in advance.

4.  TRANSPORTATION:
    [Plaintiff / Defendant / Both parties equally] shall be
    responsible for transportation.  Exchange location:
    _________________________.

5.  RIGHT OF FIRST REFUSAL:
    If the custodial parent will be unavailable for more than
    _____ hours, the other parent shall have the first right to
    care for the child during that period.

6.  MAKEUP PARENTING TIME:
    Pursuant to MCL 722.27a(7), if parenting time is wrongfully
    denied, the aggrieved parent is entitled to makeup time of
    at least the same duration.

7.  COMMUNICATION:
    Each parent shall have reasonable telephone/video contact with
    the child during the other parent's parenting time.

8.  This Order supersedes all prior parenting time orders.

IT IS SO ORDERED.

Dated: _______________

                        ________________________________
                        Hon. {judge_name}
                        14th Circuit Court, Family Division
""",

    "support_order": """\
STATE OF MICHIGAN
IN THE 14TH JUDICIAL CIRCUIT COURT FOR MUSKEGON COUNTY
FAMILY DIVISION

Case No. {case_number}
Hon. {judge_name}

ANDREW JAMES PIGORS,
    Plaintiff,

v.

EMILY A. WATSON,
    Defendant.
______________________________________________/

ORDER REGARDING SUPPORT

    At a session of said Court held in the City of Muskegon,
County of Muskegon, State of Michigan, on _______________.

PRESENT: Hon. {judge_name}, Circuit Judge.

    This matter having come before the Court on [Plaintiff's /
Defendant's] Motion Regarding Support, and the Court having
reviewed the pleadings, financial documentation, and Michigan
Child Support Formula computation;

IT IS HEREBY ORDERED:

1.  CHILD SUPPORT:
    [Payer] shall pay child support in the amount of $_______ per
    month for the minor child, L.D.W., effective _______________.
    This amount was calculated under the Michigan Child Support
    Formula based on the following incomes:
      Plaintiff net income: $_______/month
      Defendant net income: $_______/month

2.  HEALTH INSURANCE:
    [Plaintiff / Defendant] shall maintain health insurance coverage
    for the minor child.  Cost of premiums shall be allocated:
      Plaintiff: _____%
      Defendant: _____%

3.  UNINSURED MEDICAL EXPENSES:
    Uninsured and unreimbursed medical, dental, optical, and
    mental health expenses shall be allocated:
      Plaintiff: _____%
      Defendant: _____%

4.  CHILDCARE COSTS:
    Work-related childcare costs shall be allocated:
      Plaintiff: _____%
      Defendant: _____%

5.  INCOME WITHHOLDING:
    An income withholding order shall issue to the payer's
    employer pursuant to MCL 552.604.

6.  ARREARAGES:
    [If applicable] Support arrearages in the amount of
    $_______ are found to be owing.  Arrearages shall be
    paid at $_______ per month in addition to current support.

7.  This Order supersedes all prior support orders.

IT IS SO ORDERED.

Dated: _______________

                        ________________________________
                        Hon. {judge_name}
                        14th Circuit Court, Family Division
""",
}


# =============================================================================
# Public API
# =============================================================================

def get_domestic_forms() -> dict[str, dict[str, Any]]:
    """Return all domestic relations forms with metadata, keyed by form number.

    Returns
    -------
    dict[str, dict[str, Any]]
        Dictionary mapping form number (e.g. ``"CC 352"``) to its full
        metadata dict including title, purpose, required_fields, MCR
        references, and practice tips.

    Notes
    -----
    PPO forms (CC 375–383) are NOT included here.  Use
    ``ppo_forms.get_ppo_forms()`` for PPO-specific lookups.
    """
    return {f.form_number: f.to_dict() for f in DOMESTIC_FORMS}


def get_form_for_action(action: str) -> list[dict[str, Any]]:
    """Map a litigation action keyword to the relevant domestic form(s).

    Parameters
    ----------
    action : str
        One of: ``"custody_modification"``, ``"parenting_time"``,
        ``"support"``, ``"contempt"``, ``"enforcement"``,
        ``"divorce"``, ``"ex_parte"``, ``"motion"``, etc.
        Case-insensitive; spaces and hyphens are normalised to
        underscores.

    Returns
    -------
    list[dict[str, Any]]
        Form metadata dicts for every matching form.  Empty list when
        the action is not recognised.  For PPO actions, returns an
        empty list — use ``ppo_forms.get_form_for_action()`` instead.

    Examples
    --------
    >>> forms = get_form_for_action("custody_modification")
    >>> any(f["form_number"] == "CC 356" for f in forms)
    True
    """
    key = action.strip().lower().replace("-", "_").replace(" ", "_")
    form_numbers = _ACTION_MAP.get(key, [])
    return [_FORM_INDEX[fn].to_dict() for fn in form_numbers if fn in _FORM_INDEX]


def get_required_fields(form_number: str) -> list[str]:
    """Return the list of required fields for a given domestic form.

    Parameters
    ----------
    form_number : str
        Exact form number (e.g. ``"CC 352"``, ``"MC 20"``).

    Returns
    -------
    list[str]
        Ordered list of field names.  Empty list if the form number
        is unknown.

    Examples
    --------
    >>> "case_number" in get_required_fields("CC 352")
    True
    """
    form = _FORM_INDEX.get(form_number.strip())
    if form is None:
        for f in DOMESTIC_FORMS:
            if f.form_number.upper() == form_number.strip().upper():
                return list(f.required_fields)
        return []
    return list(form.required_fields)


def get_order_templates() -> dict[str, str]:
    """Return proposed order templates for custody, parenting time, and support.

    Templates contain ``{case_number}`` and ``{judge_name}`` placeholders
    for ``.format()`` substitution.

    Returns
    -------
    dict[str, str]
        Keyed by template name: ``"custody_order"``,
        ``"parenting_time_order"``, ``"support_order"``.

    Examples
    --------
    >>> templates = get_order_templates()
    >>> "custody_order" in templates
    True
    >>> "{case_number}" in templates["custody_order"]
    True
    """
    return dict(_ORDER_TEMPLATES)


def get_domestic_mcr_rules() -> dict[str, dict[str, str]]:
    """Return MCR 3.201–3.219 domestic relations rule summaries.

    Returns
    -------
    dict[str, dict[str, str]]
        Keyed by MCR number (e.g. ``"MCR 3.211"``).  Each value
        contains ``title``, ``scope``, and ``key_provisions``.
    """
    return dict(MCR_DOMESTIC_RULES)


def get_form_detail(form_number: str) -> dict[str, Any] | None:
    """Return full metadata for a single domestic form, or ``None``.

    Parameters
    ----------
    form_number : str
        Exact form number (e.g. ``"CC 356"``).

    Returns
    -------
    dict[str, Any] | None
    """
    form = _FORM_INDEX.get(form_number.strip())
    return form.to_dict() if form else None


def list_actions() -> list[str]:
    """Return every recognised action keyword for :func:`get_form_for_action`."""
    return sorted(_ACTION_MAP.keys())
