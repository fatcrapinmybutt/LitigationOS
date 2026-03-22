"""FOC Form Automation System — Michigan Friend of the Court forms.

Complete registry of SCAO FOC-related forms with required fields, issue
routing, MCR references, deadline tracking, and FOC officer information.
Designed for Pigors v Watson (Case 2024-001507-DC), 14th Circuit Court,
Family Division, Muskegon County.  All data is local-only — no external
API calls.

Sources:
  - Michigan Court Rules MCR 3.208, 3.210, 3.214, 3.218
  - Michigan Compiled Laws MCL 552.501–552.535 (FOC Act)
  - courts.michigan.gov/SCAO-forms/ (March 2026)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# =============================================================================
# Data classes
# =============================================================================

@dataclass(frozen=True)
class FOCForm:
    """Immutable descriptor for a single Michigan SCAO FOC-related form."""

    form_number: str
    title: str
    purpose: str
    required_fields: list[str]
    filing_court: str
    mcr_references: list[str]
    mcl_references: list[str]
    category: str = "FOC"
    url: str = "https://courts.michigan.gov/SCAO-forms/"
    practice_tips: str = ""
    filing_use: list[str] = field(default_factory=lambda: ["F1"])

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
# FOC FORM REGISTRY — authoritative list of Michigan FOC-related forms
# =============================================================================

FOC_FORMS: list[FOCForm] = [
    # ----- Case initiation / questionnaire ---------------------------------
    FOCForm(
        form_number="FOC 1",
        title="Friend of the Court Case Questionnaire",
        purpose=(
            "Initial intake form completed by both parties at the start of "
            "a domestic relations case.  Provides the FOC with background "
            "information on income, employment, childcare, insurance, and "
            "parenting arrangements to inform custody, support, and "
            "parenting-time recommendations."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "plaintiff_name",
            "defendant_name",
            "children_names_dobs",
            "current_custody_arrangement",
            "employment_info_plaintiff",
            "employment_info_defendant",
            "income_plaintiff",
            "income_defendant",
            "childcare_expenses",
            "health_insurance_info",
            "parenting_time_proposal",
            "domestic_violence_history",
            "substance_abuse_history",
            "other_relevant_info",
            "date_completed",
            "signature",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.208(B)"],
        mcl_references=["MCL 552.505"],
        practice_tips=(
            "Complete thoroughly — the FOC relies heavily on this "
            "questionnaire for initial recommendations.  Omissions may "
            "result in unfavorable default assumptions."
        ),
    ),

    # ----- Verified Statement ----------------------------------------------
    FOCForm(
        form_number="FOC 2",
        title="Verified Statement",
        purpose=(
            "Sworn financial disclosure form required in all FOC "
            "proceedings involving support.  Details income, assets, "
            "debts, and expenses for child support and spousal support "
            "calculations under the Michigan Child Support Formula."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "party_name",
            "employer_name",
            "employer_address",
            "gross_income",
            "pay_frequency",
            "deductions",
            "net_income",
            "other_income_sources",
            "assets",
            "debts",
            "monthly_expenses",
            "children_supported",
            "health_insurance_cost",
            "childcare_cost",
            "date_signed",
            "signature",
            "notarization",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.206(B)", "MCR 3.214"],
        mcl_references=["MCL 552.505(1)(h)", "MCL 552.517"],
        practice_tips=(
            "Must be sworn under oath or verified.  False statements "
            "constitute perjury.  Attach supporting documentation "
            "(pay stubs, tax returns, W-2s) wherever possible."
        ),
    ),

    # ----- Uniform Domestic Relations Order --------------------------------
    FOCForm(
        form_number="FOC 3",
        title="Uniform Domestic Relations Order",
        purpose=(
            "Standard order form used in divorce, separate maintenance, "
            "and family support proceedings.  Covers custody, parenting "
            "time, child support, spousal support, and property division "
            "provisions in a single unified order."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "judge_name",
            "plaintiff_name",
            "defendant_name",
            "children_names_dobs",
            "custody_determination",
            "parenting_time_schedule",
            "child_support_amount",
            "support_effective_date",
            "health_insurance_provisions",
            "tax_exemptions",
            "property_division",
            "spousal_support_provisions",
            "other_provisions",
            "judge_signature",
            "date_entered",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.211"],
        mcl_references=["MCL 552.14", "MCL 552.517"],
        practice_tips=(
            "Review every provision carefully before entry.  Once "
            "entered, modification requires showing proper cause or "
            "change of circumstances.  Object within 21 days if the "
            "order does not match the court's ruling."
        ),
    ),

    # ----- Motion Regarding Support ----------------------------------------
    FOCForm(
        form_number="FOC 10",
        title="Motion Regarding Support",
        purpose=(
            "Motion to establish, modify, or enforce child support or "
            "medical support.  May be filed by either party or the FOC.  "
            "Modification requires a showing of changed circumstances "
            "sufficient to justify a support recalculation under the "
            "Michigan Child Support Formula."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "moving_party_name",
            "opposing_party_name",
            "current_support_amount",
            "requested_change",
            "reason_for_change",
            "income_change_details",
            "children_affected",
            "proposed_new_amount",
            "date_signed",
            "signature",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.214"],
        mcl_references=["MCL 552.517", "MCL 552.605"],
        category="FOC — Support",
        practice_tips=(
            "Attach current Verified Statement (FOC 2) and income "
            "documentation.  A support change of 10%+ or more from "
            "the current order generally meets the threshold for "
            "modification."
        ),
    ),

    # ----- Response to Motion Regarding Support ----------------------------
    FOCForm(
        form_number="FOC 11",
        title="Response to Motion Regarding Support",
        purpose=(
            "Response form for the opposing party to respond to a "
            "Motion Regarding Support (FOC 10).  Must be filed within "
            "the time specified in the notice of hearing."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "responding_party_name",
            "moving_party_name",
            "response_to_allegations",
            "counter_proposal",
            "income_information",
            "date_signed",
            "signature",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.214"],
        mcl_references=["MCL 552.517"],
        category="FOC — Support",
        practice_tips=(
            "File your own Verified Statement (FOC 2) with the "
            "response.  Challenge any imputed income figures with "
            "actual documentation."
        ),
    ),

    # ----- Motion Regarding Parenting Time ---------------------------------
    FOCForm(
        form_number="FOC 59",
        title="Motion Regarding Parenting Time",
        purpose=(
            "Motion to establish, modify, or enforce a parenting time "
            "order.  May allege denial or interference with court-ordered "
            "parenting time.  The court must consider the best interests "
            "of the child under the statutory factors."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "moving_party_name",
            "opposing_party_name",
            "current_parenting_time_order",
            "requested_change",
            "reason_for_motion",
            "specific_denials_or_interference",
            "dates_of_denial",
            "best_interest_factors",
            "proposed_schedule",
            "date_signed",
            "signature",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.208"],
        mcl_references=["MCL 722.27a", "MCL 722.27b"],
        category="FOC — Parenting Time",
        practice_tips=(
            "Document every denied visit with date, time, and "
            "circumstances.  Attach evidence (text messages, emails, "
            "screenshots).  The FOC must investigate and make a "
            "recommendation under MCL 552.505."
        ),
    ),

    # ----- Response to Motion Regarding Parenting Time ---------------------
    FOCForm(
        form_number="FOC 60",
        title="Response to Motion Regarding Parenting Time",
        purpose=(
            "Response form for the opposing party to respond to a "
            "Motion Regarding Parenting Time (FOC 59)."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "responding_party_name",
            "moving_party_name",
            "response_to_allegations",
            "counter_proposal",
            "date_signed",
            "signature",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.208"],
        mcl_references=["MCL 722.27a"],
        category="FOC — Parenting Time",
        practice_tips=(
            "Address each specific allegation of denial.  Provide "
            "your own counter-proposal for a parenting time schedule "
            "if appropriate."
        ),
    ),

    # ----- Order Regarding Parenting Time ----------------------------------
    FOCForm(
        form_number="FOC 61",
        title="Order Regarding Parenting Time",
        purpose=(
            "Court order establishing or modifying a parenting time "
            "schedule.  May include make-up time provisions for denied "
            "parenting time and specific holiday/vacation schedules."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "judge_name",
            "plaintiff_name",
            "defendant_name",
            "children_names_dobs",
            "parenting_time_schedule",
            "holiday_schedule",
            "vacation_provisions",
            "makeup_time_provisions",
            "transportation_provisions",
            "communication_provisions",
            "other_provisions",
            "judge_signature",
            "date_entered",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.208"],
        mcl_references=["MCL 722.27a"],
        category="FOC — Parenting Time",
        practice_tips=(
            "Ensure the order is specific enough to be enforceable.  "
            "Vague orders like 'reasonable parenting time' are nearly "
            "impossible to enforce via contempt."
        ),
    ),

    # ----- Motion Regarding Custody ----------------------------------------
    FOCForm(
        form_number="FOC 62",
        title="Motion Regarding Custody",
        purpose=(
            "Motion to establish, modify, or enforce custody.  "
            "Modification requires showing proper cause or a change of "
            "circumstances under Vodvarka v Grasmeyer, 259 Mich App 499 "
            "(2003).  If the threshold is met, the court applies the "
            "best-interest factors of MCL 722.23."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "moving_party_name",
            "opposing_party_name",
            "current_custody_order",
            "type_of_custody_sought",
            "proper_cause_or_change",
            "best_interest_factors",
            "supporting_facts",
            "children_affected",
            "proposed_custody_arrangement",
            "date_signed",
            "signature",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.210"],
        mcl_references=["MCL 722.23", "MCL 722.27"],
        category="FOC — Custody",
        practice_tips=(
            "Must meet the Vodvarka threshold: proper cause (relevant "
            "legal event since the last order) OR change of "
            "circumstances (conditions affecting the child since the "
            "last order).  Changes affecting only the parent are "
            "generally insufficient."
        ),
    ),

    # ----- Response to Motion Regarding Custody ----------------------------
    FOCForm(
        form_number="FOC 63",
        title="Response to Motion Regarding Custody",
        purpose=(
            "Response form for the opposing party to respond to a "
            "Motion Regarding Custody (FOC 62)."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "responding_party_name",
            "moving_party_name",
            "response_to_allegations",
            "response_to_proper_cause",
            "response_to_best_interest_factors",
            "counter_proposal",
            "date_signed",
            "signature",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.210"],
        mcl_references=["MCL 722.23", "MCL 722.27"],
        category="FOC — Custody",
        practice_tips=(
            "Challenge the Vodvarka threshold argument.  If the "
            "threshold is not met, the court should not proceed to "
            "the best-interest analysis at all."
        ),
    ),

    # ----- Objection to Referee Recommendation -----------------------------
    FOCForm(
        form_number="FOC 65",
        title="Objection to Referee Recommendation",
        purpose=(
            "Filed within 21 days of service of a referee's "
            "recommendation to request a de novo hearing before the "
            "judge.  If no objection is filed, the recommendation "
            "becomes a court order.  MCR 3.218(D)."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "objecting_party_name",
            "date_of_recommendation",
            "referee_name",
            "specific_objections",
            "relief_requested",
            "factual_basis",
            "legal_basis",
            "date_signed",
            "signature",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.218(D)"],
        mcl_references=["MCL 552.507(5)"],
        category="FOC — Objection",
        practice_tips=(
            "CRITICAL: 21-day deadline from service of the "
            "recommendation.  Missing this deadline means the referee "
            "recommendation becomes a binding court order.  ALWAYS "
            "object to unfavorable recommendations."
        ),
    ),

    # ----- Objection to Proposed Order -------------------------------------
    FOCForm(
        form_number="FOC 67",
        title="Objection to Proposed Order",
        purpose=(
            "Objection to a proposed order prepared by the FOC or "
            "opposing party.  Filed within 21 days of service.  "
            "Requests the judge to review and reject or modify the "
            "proposed order before entry."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "objecting_party_name",
            "date_of_proposed_order",
            "specific_objections",
            "proposed_changes",
            "supporting_facts",
            "date_signed",
            "signature",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.218(D)", "MCR 2.602"],
        mcl_references=["MCL 552.507(5)"],
        category="FOC — Objection",
        practice_tips=(
            "Compare the proposed order line-by-line with the court's "
            "oral ruling (if any).  Object to any discrepancy.  The "
            "21-day clock starts on SERVICE, not entry."
        ),
    ),

    # ----- Motion/Stipulation for Joint Physical Custody -------------------
    FOCForm(
        form_number="FOC 70",
        title="Motion/Stipulation for Joint Physical Custody",
        purpose=(
            "Motion or stipulation requesting joint physical custody.  "
            "May be filed by agreement (stipulation) or contested "
            "(motion).  The court must still find that joint custody "
            "is in the child's best interests."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "plaintiff_name",
            "defendant_name",
            "children_names_dobs",
            "proposed_custody_schedule",
            "proposed_parenting_time_plan",
            "transportation_plan",
            "decision_making_provisions",
            "support_implications",
            "stipulation_or_motion",
            "date_signed",
            "signatures_both_parties",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.210"],
        mcl_references=["MCL 722.26a", "MCL 722.27"],
        category="FOC — Custody",
        practice_tips=(
            "Joint physical custody does not necessarily mean equal "
            "time — it means both parents have significant periods of "
            "physical custody.  The support formula adjusts for "
            "overnights."
        ),
    ),

    # ----- Uniform Spousal Support Order -----------------------------------
    FOCForm(
        form_number="FOC 78",
        title="Uniform Spousal Support Order",
        purpose=(
            "Standard order form for spousal support (alimony).  Sets "
            "out the amount, duration, payment method, and conditions "
            "for termination of spousal support."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "judge_name",
            "payer_name",
            "payee_name",
            "support_amount",
            "payment_frequency",
            "effective_date",
            "termination_date_or_conditions",
            "payment_method",
            "income_withholding_provisions",
            "tax_treatment",
            "modification_provisions",
            "judge_signature",
            "date_entered",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.214"],
        mcl_references=["MCL 552.23", "MCL 552.28"],
        category="FOC — Support",
        practice_tips=(
            "Spousal support is modifiable unless the judgment "
            "expressly provides otherwise.  Termination upon "
            "cohabitation, remarriage, or death should be specified."
        ),
    ),

    # ----- Objection to Ex Parte Order -------------------------------------
    FOCForm(
        form_number="FOC 84",
        title="Objection to Ex Parte Order",
        purpose=(
            "Objection to an order entered without a hearing (ex parte).  "
            "The objecting party must file within 14 days of service "
            "of the ex parte order and is entitled to a hearing before "
            "the judge."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "objecting_party_name",
            "date_of_ex_parte_order",
            "order_objected_to",
            "grounds_for_objection",
            "factual_basis",
            "prejudice_to_objecting_party",
            "relief_requested",
            "date_signed",
            "signature",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.207(B)", "MCR 2.119(B)"],
        mcl_references=["MCL 552.14"],
        category="FOC — Objection",
        practice_tips=(
            "Ex parte orders are disfavored except in genuine "
            "emergencies.  Challenge the emergency basis and demand "
            "a hearing.  Due process requires notice and an "
            "opportunity to be heard before deprivation of rights."
        ),
    ),

    # ----- Motion and Affidavit for Contempt -------------------------------
    FOCForm(
        form_number="FOC 89",
        title="Motion and Affidavit for Contempt",
        purpose=(
            "Motion requesting the court to hold the opposing party in "
            "contempt for willful violation of a court order.  "
            "Accompanied by an affidavit detailing the specific "
            "violations.  Used for enforcement of custody, parenting "
            "time, support, and other domestic relations orders."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "moving_party_name",
            "party_in_contempt",
            "order_allegedly_violated",
            "date_of_order",
            "specific_violations",
            "dates_of_violations",
            "facts_supporting_willfulness",
            "relief_requested",
            "affidavit_text",
            "date_signed",
            "signature",
            "notarization",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.208(B)", "MCR 3.606"],
        mcl_references=["MCL 552.511(1)", "MCL 600.1701", "MCL 600.1715"],
        category="FOC — Contempt",
        practice_tips=(
            "Must prove: (1) a clear and definite court order; "
            "(2) the contemnor knew of the order; (3) willful "
            "violation.  Criminal contempt = up to 93 days per "
            "violation.  Civil contempt = purge conditions + "
            "possible jail until compliance."
        ),
    ),

    # ----- Domestic Relations Judgment Information --------------------------
    FOCForm(
        form_number="FOC 100",
        title="Domestic Relations Judgment Information",
        purpose=(
            "Information form required to be filed with any domestic "
            "relations judgment or order that establishes, modifies, "
            "or terminates support, custody, or parenting time.  "
            "Provides the FOC with key information for enforcement."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "plaintiff_name",
            "plaintiff_address",
            "plaintiff_ssn_last_four",
            "plaintiff_dob",
            "defendant_name",
            "defendant_address",
            "defendant_ssn_last_four",
            "defendant_dob",
            "children_names_dobs",
            "custody_provisions",
            "parenting_time_provisions",
            "support_provisions",
            "date_of_judgment",
            "signature",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.211"],
        mcl_references=["MCL 552.505(1)(h)"],
        category="FOC — Judgment",
        practice_tips=(
            "Required with every judgment and order affecting "
            "custody, support, or parenting time.  Failure to file "
            "may delay enforcement by the FOC."
        ),
    ),

    # ----- Income Information Form -----------------------------------------
    FOCForm(
        form_number="FOC 101",
        title="Income Information Form",
        purpose=(
            "Detailed income disclosure form required for support "
            "calculations.  Used in conjunction with the Verified "
            "Statement (FOC 2) to run the Michigan Child Support "
            "Formula."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "party_name",
            "employer_name",
            "employer_address",
            "employer_phone",
            "hourly_rate_or_salary",
            "hours_per_week",
            "overtime_income",
            "bonuses",
            "commissions",
            "self_employment_income",
            "rental_income",
            "investment_income",
            "government_benefits",
            "other_income",
            "total_gross_income",
            "date_signed",
            "signature",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.206(B)", "MCR 3.214"],
        mcl_references=["MCL 552.517", "MCL 552.519"],
        category="FOC — Support",
        practice_tips=(
            "All income sources must be disclosed.  Attach at least "
            "6 months of pay stubs, most recent tax return, and W-2s.  "
            "Challenge imputed income with actual employment evidence."
        ),
    ),

    # ----- Uniform Child Support Order -------------------------------------
    FOCForm(
        form_number="FOC 102",
        title="Uniform Child Support Order",
        purpose=(
            "Standard child support order form.  Sets out base support, "
            "health-care obligations, childcare expenses, arrearage "
            "provisions, and income-withholding provisions.  Must "
            "conform to the Michigan Child Support Formula."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "judge_name",
            "plaintiff_name",
            "defendant_name",
            "children_names_dobs",
            "base_support_amount",
            "payer_name",
            "payee_name",
            "effective_date",
            "health_insurance_responsibility",
            "uninsured_health_care_split",
            "childcare_expenses",
            "arrearage_amount",
            "arrearage_payment_schedule",
            "income_withholding_amount",
            "judge_signature",
            "date_entered",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.214"],
        mcl_references=["MCL 552.517", "MCL 552.605"],
        category="FOC — Support",
        practice_tips=(
            "Verify all calculations against the Michigan Child "
            "Support Formula manual.  Challenge imputed income, "
            "incorrect overnights counts, and unsupported childcare "
            "costs.  Always insist on deviation findings if the "
            "order deviates from the formula."
        ),
    ),

    # ----- Additional commonly-used FOC forms ------------------------------
    FOCForm(
        form_number="FOC 4",
        title="Uniform Support Order",
        purpose=(
            "Alternative unified support order covering both child "
            "support and spousal support in a single instrument."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "judge_name",
            "plaintiff_name",
            "defendant_name",
            "child_support_amount",
            "spousal_support_amount",
            "effective_date",
            "payment_method",
            "judge_signature",
            "date_entered",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.214"],
        mcl_references=["MCL 552.517"],
        category="FOC — Support",
    ),

    FOCForm(
        form_number="FOC 29",
        title="Advice of Rights Regarding Friend of the Court",
        purpose=(
            "Notice of rights regarding FOC procedures.  Explains "
            "right to object to FOC recommendations, right to request "
            "a de novo hearing, and right to opt out of FOC services "
            "by agreement."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "party_name",
            "date_provided",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.208(A)"],
        mcl_references=["MCL 552.505"],
        category="FOC — Administrative",
        practice_tips=(
            "Issued by the court/FOC.  Review carefully to understand "
            "your rights — especially the objection deadlines."
        ),
    ),

    FOCForm(
        form_number="FOC 109",
        title="Motion and Affidavit for Show Cause",
        purpose=(
            "Motion requesting the court to issue a show cause order "
            "compelling the opposing party to appear and explain why "
            "they should not be held in contempt.  Used for "
            "enforcement of all domestic relations orders."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "moving_party_name",
            "party_to_show_cause",
            "order_violated",
            "date_of_order",
            "specific_violations",
            "dates_of_violations",
            "affidavit_of_facts",
            "relief_requested",
            "date_signed",
            "signature",
            "notarization",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.606"],
        mcl_references=["MCL 600.1701"],
        category="FOC — Contempt",
        practice_tips=(
            "The show cause order compels appearance.  Failure to "
            "appear may result in a bench warrant.  Prepare a "
            "detailed chronology of violations."
        ),
    ),
]


# =============================================================================
# Internal lookup index  (built once at import time)
# =============================================================================

_FORM_INDEX: dict[str, FOCForm] = {f.form_number: f for f in FOC_FORMS}


# =============================================================================
# ISSUE → FORM(S) routing table
# =============================================================================

_ISSUE_MAP: dict[str, list[str]] = {
    # --- custody ---
    "custody": ["FOC 62", "FOC 63", "FOC 70", "FOC 1"],
    "modify_custody": ["FOC 62"],
    "custody_response": ["FOC 63"],
    "joint_custody": ["FOC 70"],
    "custody_investigation": ["FOC 1", "FOC 62"],

    # --- parenting time ---
    "parenting_time": ["FOC 59", "FOC 60", "FOC 61"],
    "parenting_time_motion": ["FOC 59"],
    "parenting_time_response": ["FOC 60"],
    "parenting_time_order": ["FOC 61"],
    "parenting_time_denial": ["FOC 59", "FOC 89"],
    "parenting_time_enforcement": ["FOC 59", "FOC 89", "FOC 109"],
    "visitation": ["FOC 59", "FOC 60", "FOC 61"],

    # --- support ---
    "support": ["FOC 10", "FOC 11", "FOC 102", "FOC 2", "FOC 101"],
    "child_support": ["FOC 10", "FOC 11", "FOC 102"],
    "modify_support": ["FOC 10", "FOC 2", "FOC 101"],
    "support_response": ["FOC 11"],
    "support_order": ["FOC 102", "FOC 4"],
    "spousal_support": ["FOC 78"],
    "alimony": ["FOC 78"],
    "income_disclosure": ["FOC 2", "FOC 101"],

    # --- contempt / enforcement ---
    "contempt": ["FOC 89", "FOC 109"],
    "enforcement": ["FOC 89", "FOC 109"],
    "show_cause": ["FOC 109"],
    "violation": ["FOC 89"],

    # --- objection ---
    "objection": ["FOC 65", "FOC 67", "FOC 84"],
    "objection_referee": ["FOC 65"],
    "objection_proposed_order": ["FOC 67"],
    "objection_ex_parte": ["FOC 84"],
    "referee": ["FOC 65"],
    "de_novo_hearing": ["FOC 65"],

    # --- judgment / intake ---
    "judgment": ["FOC 100", "FOC 3"],
    "judgment_information": ["FOC 100"],
    "intake": ["FOC 1"],
    "questionnaire": ["FOC 1"],
    "case_initiation": ["FOC 1", "FOC 2", "FOC 100"],
    "verified_statement": ["FOC 2"],
    "financial_disclosure": ["FOC 2", "FOC 101"],
    "domestic_relations_order": ["FOC 3"],

    # --- administrative ---
    "advice_of_rights": ["FOC 29"],
    "foc_rights": ["FOC 29"],
}


# =============================================================================
# MCR REFERENCE TABLE — FOC-relevant Michigan Court Rules
# =============================================================================

MCR_REFERENCES: dict[str, dict[str, str]] = {
    "MCR 3.208": {
        "title": "Friend of the Court",
        "scope": (
            "Powers and duties of the FOC: investigation, recommendation, "
            "enforcement of custody, parenting time, and support orders."
        ),
        "key_provisions": (
            "FOC must investigate and make recommendations on custody, "
            "parenting time, and support.  FOC may initiate contempt "
            "proceedings.  FOC mediates disputes before hearing."
        ),
    },
    "MCR 3.210": {
        "title": "Custody and Parenting Time — Investigation and Report",
        "scope": (
            "Governs custody investigations.  Court may order investigation "
            "by FOC, guardian ad litem, or other professional."
        ),
        "key_provisions": (
            "Investigation must address best-interest factors (MCL 722.23).  "
            "Report must be provided to parties before hearing.  Parties "
            "may cross-examine the investigator."
        ),
    },
    "MCR 3.214": {
        "title": "Support Proceedings",
        "scope": (
            "Governs establishment, modification, and enforcement of "
            "child support and spousal support.  Michigan Child Support "
            "Formula is presumptively correct."
        ),
        "key_provisions": (
            "Support calculated under the Michigan Child Support Formula.  "
            "Deviation requires specific findings.  Income must be "
            "verified with documentation."
        ),
    },
    "MCR 3.218": {
        "title": "Referee Hearings — Recommendations and Objections",
        "scope": (
            "Governs proceedings before FOC referees and the objection "
            "process.  Referees make recommendations; judges make orders."
        ),
        "key_provisions": (
            "Parties have 21 days from service of recommendation to "
            "file written objections.  Objection triggers de novo "
            "hearing before the judge.  Failure to object = "
            "recommendation becomes order."
        ),
    },
    "MCR 3.206": {
        "title": "Initiating a Domestic Relations Action",
        "scope": (
            "Procedures for initiating domestic relations cases.  "
            "Verified Statement required.  Ex parte relief limited."
        ),
        "key_provisions": (
            "Verified financial statement required with initial filing.  "
            "Ex parte orders require showing of irreparable injury."
        ),
    },
    "MCR 3.207": {
        "title": "Ex Parte Orders",
        "scope": (
            "Standards for ex parte relief in domestic relations cases."
        ),
        "key_provisions": (
            "Must show irreparable injury, loss, or damage will result "
            "from delay.  Subject to objection and hearing on short notice."
        ),
    },
    "MCR 3.211": {
        "title": "Judgment Provisions",
        "scope": (
            "Required provisions in domestic relations judgments."
        ),
        "key_provisions": (
            "Judgment must address custody, parenting time, support, "
            "property division, and insurance.  Uniform orders required."
        ),
    },
    "MCR 3.606": {
        "title": "Contempt of Court",
        "scope": (
            "Procedures for civil and criminal contempt proceedings."
        ),
        "key_provisions": (
            "Civil contempt: remedial, purge conditions.  Criminal "
            "contempt: punitive, up to 93 days per violation.  Due "
            "process protections apply."
        ),
    },
}


# =============================================================================
# FOC DEADLINE TABLE — standard procedural deadlines
# =============================================================================

_FOC_DEADLINES: dict[str, dict[str, str]] = {
    "objection_to_referee_recommendation": {
        "deadline": "21 days from service",
        "mcr_reference": "MCR 3.218(D)",
        "form": "FOC 65",
        "consequence": (
            "Failure to object within 21 days means the referee "
            "recommendation becomes a binding court order."
        ),
        "practice_tip": (
            "Calendar this immediately upon receipt.  Count 21 DAYS "
            "(not business days) from the date of SERVICE, not the "
            "date of the recommendation itself."
        ),
    },
    "objection_to_proposed_order": {
        "deadline": "21 days from service",
        "mcr_reference": "MCR 3.218(D)",
        "form": "FOC 67",
        "consequence": (
            "Proposed order may be entered without modification "
            "if no objection is filed."
        ),
        "practice_tip": (
            "Compare the proposed order against the court's oral "
            "ruling or referee recommendation.  Object to any "
            "discrepancy, however minor."
        ),
    },
    "objection_to_ex_parte_order": {
        "deadline": "14 days from service",
        "mcr_reference": "MCR 3.207(B)",
        "form": "FOC 84",
        "consequence": (
            "Ex parte order remains in effect if no objection is "
            "filed.  Objection triggers a hearing."
        ),
        "practice_tip": (
            "Always object to ex parte orders — they bypass your "
            "due process right to be heard."
        ),
    },
    "response_to_motion": {
        "deadline": "21 days from service (or as specified in notice of hearing)",
        "mcr_reference": "MCR 2.119(C)(1)",
        "form": "FOC 11 / FOC 60 / FOC 63",
        "consequence": (
            "Court may grant the motion unopposed if no response "
            "is filed."
        ),
        "practice_tip": (
            "Even if the hearing date is before the response "
            "deadline, file early so the judge has your position."
        ),
    },
    "foc_investigation_completion": {
        "deadline": "No fixed statutory deadline; typically 30–90 days",
        "mcr_reference": "MCR 3.210",
        "form": "N/A",
        "consequence": (
            "Delays in FOC investigation may delay hearing scheduling."
        ),
        "practice_tip": (
            "Follow up with the FOC office regularly.  If the "
            "investigation is unreasonably delayed, file a motion "
            "to compel the FOC to act."
        ),
    },
    "support_modification_effective_date": {
        "deadline": "Retroactive to date of filing the motion",
        "mcr_reference": "MCR 3.214",
        "form": "FOC 10",
        "consequence": (
            "Support modifications are generally retroactive to the "
            "date the motion was filed — file promptly."
        ),
        "practice_tip": (
            "File support modification motions immediately when "
            "circumstances change.  Delay = lost retroactive credit."
        ),
    },
    "contempt_hearing": {
        "deadline": "Must be set for hearing within a reasonable time",
        "mcr_reference": "MCR 3.606",
        "form": "FOC 89 / FOC 109",
        "consequence": (
            "Unreasonable delay may prejudice the moving party's case."
        ),
        "practice_tip": (
            "Request an expedited hearing if ongoing violations "
            "are causing immediate harm to the child."
        ),
    },
    "de_novo_hearing_after_objection": {
        "deadline": "Court must schedule within 21 days of objection",
        "mcr_reference": "MCR 3.218(D)",
        "form": "FOC 65",
        "consequence": (
            "The referee recommendation is stayed pending the "
            "de novo hearing.  The judge hears the matter fresh."
        ),
        "practice_tip": (
            "Prepare for de novo hearing as a full evidentiary "
            "hearing — the judge owes no deference to the referee."
        ),
    },
}


# =============================================================================
# FOC OFFICER INFO — Muskegon County (14th Circuit)
# =============================================================================

_FOC_OFFICER_INFO: dict[str, Any] = {
    "county": "Muskegon",
    "circuit": "14th Circuit Court",
    "division": "Family Division",
    "foc_officer": "Pamela Rusco",
    "office_address": "990 Terrace St, Muskegon, MI 49442",
    "office_phone": "(231) 724-6241",
    "website": "https://www.co.muskegon.mi.us/787/Friend-of-the-Court",
    "judge": "Hon. Jenny L. McNeill",
    "case_number": "2024-001507-DC",
    "case_caption": "Pigors v Watson",
    "plaintiff": "Andrew James Pigors",
    "defendant": "Emily A. Watson",
    "child_initials": "L.D.W.",
    "notes": (
        "FOC officer Pamela Rusco handles all custody, parenting time, "
        "and support matters in this case.  All FOC filings should be "
        "served on the FOC office in addition to the opposing party."
    ),
}


# =============================================================================
# Public API
# =============================================================================

def get_foc_forms() -> dict[str, dict[str, Any]]:
    """Return all FOC forms with metadata, keyed by form number.

    Returns
    -------
    dict[str, dict[str, Any]]
        Dictionary mapping form number (e.g. ``"FOC 59"``) to its full
        metadata dict including title, purpose, required_fields, MCR
        references, and practice tips.
    """
    return {f.form_number: f.to_dict() for f in FOC_FORMS}


def get_form_for_issue(issue: str) -> list[dict[str, Any]]:
    """Map a litigation issue keyword to the relevant FOC form(s).

    Parameters
    ----------
    issue : str
        One of: ``"custody"``, ``"support"``, ``"parenting_time"``,
        ``"contempt"``, ``"objection"``, ``"enforcement"``,
        ``"visitation"``, ``"alimony"``, etc.  Case-insensitive;
        spaces and hyphens are normalised to underscores.

    Returns
    -------
    list[dict[str, Any]]
        Form metadata dicts for every matching form.  Empty list when
        the issue is not recognised.

    Examples
    --------
    >>> forms = get_form_for_issue("custody")
    >>> any(f["form_number"] == "FOC 62" for f in forms)
    True
    """
    key = issue.strip().lower().replace("-", "_").replace(" ", "_")
    form_numbers = _ISSUE_MAP.get(key, [])
    return [_FORM_INDEX[fn].to_dict() for fn in form_numbers if fn in _FORM_INDEX]


def get_required_fields(form_number: str) -> list[str]:
    """Return the list of required fields for a given FOC form.

    Parameters
    ----------
    form_number : str
        Exact form number (e.g. ``"FOC 59"``, ``"FOC 102"``).

    Returns
    -------
    list[str]
        Ordered list of field names.  Empty list if the form number
        is unknown.

    Examples
    --------
    >>> "case_number" in get_required_fields("FOC 89")
    True
    """
    form = _FORM_INDEX.get(form_number.strip())
    if form is None:
        for f in FOC_FORMS:
            if f.form_number.upper() == form_number.strip().upper():
                return list(f.required_fields)
        return []
    return list(form.required_fields)


def get_foc_deadlines() -> dict[str, dict[str, str]]:
    """Return all standard FOC deadlines with MCR references.

    Returns
    -------
    dict[str, dict[str, str]]
        Keyed by deadline identifier (e.g.
        ``"objection_to_referee_recommendation"``).  Each value
        contains ``deadline``, ``mcr_reference``, ``form``,
        ``consequence``, and ``practice_tip``.
    """
    return dict(_FOC_DEADLINES)


def get_foc_officer_info() -> dict[str, Any]:
    """Return Muskegon County FOC office information.

    Returns the FOC officer info for Pigors v Watson,
    14th Circuit Court, Muskegon County.

    Returns
    -------
    dict[str, Any]
        Contains ``foc_officer``, ``office_address``, ``judge``,
        ``case_number``, ``case_caption``, and other identifying
        information.
    """
    return dict(_FOC_OFFICER_INFO)


def get_mcr_references() -> dict[str, dict[str, str]]:
    """Return all FOC-relevant Michigan Court Rule references.

    Returns
    -------
    dict[str, dict[str, str]]
        Keyed by MCR number (e.g. ``"MCR 3.218"``).  Each value
        contains ``title``, ``scope``, and ``key_provisions``.
    """
    return dict(MCR_REFERENCES)


def get_form_detail(form_number: str) -> dict[str, Any] | None:
    """Return full metadata for a single FOC form, or ``None`` if not found.

    Parameters
    ----------
    form_number : str
        Exact form number (e.g. ``"FOC 62"``).

    Returns
    -------
    dict[str, Any] | None
    """
    form = _FORM_INDEX.get(form_number.strip())
    return form.to_dict() if form else None


def list_issues() -> list[str]:
    """Return every recognised issue keyword for :func:`get_form_for_issue`."""
    return sorted(_ISSUE_MAP.keys())
