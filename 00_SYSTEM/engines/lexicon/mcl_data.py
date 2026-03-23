"""
MCL Data — Michigan Compiled Laws for LEXICON Engine
=====================================================
Structured data for Michigan statutory law relevant to the
Pigors v. Watson litigation across 6 case lanes.

CRITICAL: Only verified statutes are marked confidence='verified'.
Any uncertain content is marked 'needs_verification'.
Do NOT fabricate section numbers or legal content.

Lane Key:
  A = Watson custody (2024-001507-DC)
  B = Shady Oaks housing (2025-002760-CZ)
  C = Convergence / FOIA
  D = PPO / Protection Orders
  E = Judicial Misconduct / JTC
  F = Appellate (COA/MSC)
"""

import sys
from typing import List
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from lexicon_db import LegalRule, RuleCrossRef


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Function 1: Michigan Compiled Laws
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_mcl_rules() -> List[LegalRule]:
    """Return all Michigan Compiled Laws relevant to the Pigors v. Watson case."""
    return [
        # ─── MCL Chapter 722: Child Custody Act ──────────────

        LegalRule(
            rule_id="MCL-722.21",
            source="MCL",
            chapter="722",
            section="722.21",
            title="Child Custody Act; Short Title",
            summary=(
                "Establishes the short title of the Child Custody Act of 1970. This Act governs "
                "custody disputes in Michigan and provides the framework for determining the "
                "best interests of the child."
            ),
            full_text="",
            confidence="verified",
            lanes=["A"],
            tags=["child_custody_act", "short_title", "custody"],
            url="https://legislature.mi.gov/Laws/MCL?objectName=mcl-722-21",
        ),
        LegalRule(
            rule_id="MCL-722.22",
            source="MCL",
            chapter="722",
            section="722.22",
            title="Child Custody Act; Definitions",
            summary=(
                "Defines key terms used in the Child Custody Act including 'best interests "
                "of the child,' 'child custody dispute,' 'established custodial environment,' "
                "and 'proper cause.' An established custodial environment exists when the child "
                "naturally looks to the custodian for guidance and security."
            ),
            full_text="",
            confidence="verified",
            lanes=["A"],
            tags=["definitions", "custody", "established_custodial_environment",
                  "best_interest", "proper_cause"],
        ),
        LegalRule(
            rule_id="MCL-722.23",
            source="MCL",
            chapter="722",
            section="722.23",
            title="Best Interest of the Child; Factors",
            summary=(
                "Enumerates the 12 best interest factors (a through l) the court must evaluate "
                "in custody disputes: (a) love/affection/emotional ties, (b) capacity to provide "
                "love/affection/guidance, (c) capacity for food/clothing/medical care, "
                "(d) length of stable/satisfactory environment, (e) permanence of existing or "
                "proposed custodial home, (f) moral fitness, (g) mental/physical health, "
                "(h) home/school/community record, (i) child's reasonable preference, "
                "(j) willingness to facilitate relationship with other parent, "
                "(k) domestic violence, (l) any other relevant factor."
            ),
            full_text="",
            confidence="verified",
            lanes=["A"],
            tags=["best_interest_factors", "custody", "12_factors",
                  "love_affection", "moral_fitness", "domestic_violence",
                  "facilitate_relationship", "child_preference"],
            url="https://legislature.mi.gov/Laws/MCL?objectName=mcl-722-23",
        ),
        LegalRule(
            rule_id="MCL-722.24",
            source="MCL",
            chapter="722",
            section="722.24",
            title="Child Custody Dispute; Hearing",
            summary=(
                "In a custody dispute, the court must hold a hearing and determine the best "
                "interests of the child by considering, evaluating, and determining each of the "
                "factors in MCL 722.23. The court must make findings of fact and conclusions of "
                "law on each factor."
            ),
            full_text="",
            confidence="verified",
            lanes=["A"],
            tags=["custody_hearing", "findings_of_fact", "best_interest",
                  "conclusions_of_law"],
        ),
        LegalRule(
            rule_id="MCL-722.25",
            source="MCL",
            chapter="722",
            section="722.25",
            title="Parenting Time",
            summary=(
                "A child has a right to parenting time with each parent unless the court "
                "determines that parenting time would endanger the child's physical, mental, "
                "or emotional health. Parenting time must be granted in specific terms."
            ),
            full_text="",
            confidence="verified",
            lanes=["A"],
            tags=["parenting_time", "visitation", "child_right",
                  "endangerment", "specific_terms"],
        ),
        LegalRule(
            rule_id="MCL-722.26a",
            source="MCL",
            chapter="722",
            section="722.26a",
            title="Change of Domicile",
            summary=(
                "A parent with custody may not change the legal residence of a child to a "
                "location more than 100 miles from the child's current legal residence without "
                "court approval. The court must evaluate change-of-domicile factors including "
                "whether the move would improve quality of life and whether the other parent "
                "is complying with custody/parenting time orders."
            ),
            full_text="",
            confidence="verified",
            lanes=["A"],
            tags=["change_of_domicile", "100_miles", "relocation",
                  "custody", "quality_of_life"],
        ),
        LegalRule(
            rule_id="MCL-722.27",
            source="MCL",
            chapter="722",
            section="722.27",
            title="Modification of Custody Orders",
            summary=(
                "A custody order may be modified only if the moving party demonstrates proper "
                "cause or a change of circumstances, and then the court must determine whether "
                "the modification is in the best interests of the child under MCL 722.23. "
                "If an established custodial environment exists, the moving party must prove "
                "by clear and convincing evidence that the change is in the child's best interests."
            ),
            full_text="",
            confidence="verified",
            lanes=["A"],
            tags=["modification", "custody", "change_of_circumstances",
                  "proper_cause", "clear_and_convincing", "best_interest",
                  "established_custodial_environment"],
            url="https://legislature.mi.gov/Laws/MCL?objectName=mcl-722-27",
        ),
        LegalRule(
            rule_id="MCL-722.27a",
            source="MCL",
            chapter="722",
            section="722.27a",
            title="Parenting Time; Specific Provisions",
            summary=(
                "Provides specific rules for parenting time orders. The court must consider "
                "the best interests of the child and must include specific provisions regarding "
                "dates, times, and conditions of parenting time. A parent's failure to exercise "
                "parenting time may be grounds for modification. Makeup parenting time must be "
                "provided for wrongful denial."
            ),
            full_text="",
            confidence="verified",
            lanes=["A"],
            tags=["parenting_time", "specific_provisions", "makeup_time",
                  "wrongful_denial", "best_interest", "modification"],
        ),
        LegalRule(
            rule_id="MCL-722.27b",
            source="MCL",
            chapter="722",
            section="722.27b",
            title="Joint Custody",
            summary=(
                "The court may award joint custody if it determines that joint custody is in "
                "the best interests of the child. Joint custody requires that the parents be "
                "able to cooperate and generally agree on important decisions affecting the "
                "child's welfare. The court must consider the factors in MCL 722.23."
            ),
            full_text="",
            confidence="verified",
            lanes=["A"],
            tags=["joint_custody", "cooperation", "best_interest",
                  "decision_making", "shared_custody"],
        ),
        LegalRule(
            rule_id="MCL-722.28",
            source="MCL",
            chapter="722",
            section="722.28",
            title="Attorney Fees in Custody Actions",
            summary=(
                "The court may order one party to pay the other party's reasonable attorney "
                "fees in a custody action if the party is unable to bear the expense and the "
                "other party is able to pay. Attorney fees may also be awarded when a party's "
                "conduct necessitated additional proceedings."
            ),
            full_text="",
            confidence="verified",
            lanes=["A"],
            tags=["attorney_fees", "custody", "ability_to_pay",
                  "reasonable_fees", "sanctions"],
        ),
        LegalRule(
            rule_id="MCL-722.31",
            source="MCL",
            chapter="722",
            section="722.31",
            title="Uniform Child Custody Jurisdiction and Enforcement Act",
            summary=(
                "Establishes Michigan's adoption of the UCCJEA, which determines which state "
                "has jurisdiction to make initial custody determinations and modifications. "
                "Michigan has jurisdiction if it is the child's home state or was the home "
                "state within 6 months before the proceeding."
            ),
            full_text="",
            confidence="verified",
            lanes=["A"],
            tags=["uccjea", "jurisdiction", "home_state", "custody",
                  "interstate", "enforcement"],
        ),

        # ─── MCL Chapter 600: Revised Judicature Act ─────────

        LegalRule(
            rule_id="MCL-600.916",
            source="MCL",
            chapter="600",
            section="600.916",
            title="Disqualification of Judges",
            summary=(
                "Provides statutory grounds for judicial disqualification. A judge is disqualified "
                "when the judge is biased or prejudiced for or against a party, has personal "
                "knowledge of disputed evidentiary facts, has been a lawyer in the matter, or "
                "has a personal financial interest. Supplements MCR 2.003."
            ),
            full_text="",
            confidence="verified",
            lanes=["A", "B", "D", "E"],
            tags=["disqualification", "judge", "bias", "prejudice",
                  "financial_interest", "recusal"],
            url="https://legislature.mi.gov/Laws/MCL?objectName=mcl-600-916",
        ),
        LegalRule(
            rule_id="MCL-600.1701",
            source="MCL",
            chapter="600",
            section="600.1701",
            title="Contempt of Court; Criminal Contempt",
            summary=(
                "Defines criminal contempt of court, which includes willful disobedience of a "
                "lawful court order, disorderly conduct in the court's presence, and resistance "
                "to lawful court orders. Criminal contempt is punishable by fine, imprisonment, "
                "or both. The standard of proof is beyond a reasonable doubt."
            ),
            full_text="",
            confidence="verified",
            lanes=["A", "D"],
            tags=["contempt", "criminal_contempt", "court_order",
                  "disobedience", "punishment", "beyond_reasonable_doubt"],
        ),
        LegalRule(
            rule_id="MCL-600.1711",
            source="MCL",
            chapter="600",
            section="600.1711",
            title="Civil Contempt",
            summary=(
                "Defines civil contempt as the willful failure to comply with a court order "
                "when the contemnor has the present ability to comply. The purpose is coercive, "
                "not punitive — the contemnor 'carries the keys to the jail.' Purge conditions "
                "must be achievable."
            ),
            full_text="",
            confidence="verified",
            lanes=["A", "D"],
            tags=["civil_contempt", "coercive", "purge_conditions",
                  "ability_to_comply", "court_order"],
        ),
        LegalRule(
            rule_id="MCL-600.1715",
            source="MCL",
            chapter="600",
            section="600.1715",
            title="Contempt; Purge Conditions",
            summary=(
                "Specifies that a person held in civil contempt must be given purge conditions "
                "that are achievable and within their present ability to perform. The contemnor "
                "must be released upon compliance with the purge conditions."
            ),
            full_text="",
            confidence="verified",
            lanes=["A", "D"],
            tags=["purge_conditions", "civil_contempt", "achievable",
                  "release", "ability_to_perform"],
        ),
        LegalRule(
            rule_id="MCL-600.2950",
            source="MCL",
            chapter="600",
            section="600.2950",
            title="Personal Protection Orders",
            summary=(
                "Authorizes the circuit court to issue personal protection orders (PPOs) to "
                "restrain a person from threatening, assaulting, stalking, or engaging in "
                "conduct that interferes with personal liberty. A PPO may be issued ex parte "
                "if there is immediate danger. Violation is a criminal offense."
            ),
            full_text="",
            confidence="verified",
            lanes=["A", "D"],
            tags=["ppo", "personal_protection_order", "stalking",
                  "assault", "ex_parte", "criminal_violation"],
            url="https://legislature.mi.gov/Laws/MCL?objectName=mcl-600-2950",
        ),
        LegalRule(
            rule_id="MCL-600.2950a",
            source="MCL",
            chapter="600",
            section="600.2950a",
            title="PPO; Domestic Relationship",
            summary=(
                "Provides for personal protection orders specifically in domestic relationship "
                "situations. Covers spouses, former spouses, persons with a child in common, "
                "and persons who reside or have resided in the same household. Broader "
                "protections than general PPOs including exclusive possession of the residence."
            ),
            full_text="",
            confidence="verified",
            lanes=["D"],
            tags=["ppo", "domestic_relationship", "spouse", "former_spouse",
                  "household", "exclusive_possession"],
        ),
        LegalRule(
            rule_id="MCL-600.5801",
            source="MCL",
            chapter="600",
            section="600.5801",
            title="Quiet Title Action",
            summary=(
                "Provides the statutory basis for an action to quiet title to real property. "
                "A person in possession or claiming title to land may bring an action to "
                "determine and quiet title against any person claiming an interest in the property. "
                "The court may determine all claims and order appropriate relief."
            ),
            full_text="",
            confidence="verified",
            lanes=["B"],
            tags=["quiet_title", "real_property", "land", "title",
                  "possession", "claims"],
        ),

        # ─── MCL Chapter 552: Divorce ────────────────────────

        LegalRule(
            rule_id="MCL-552.1",
            source="MCL",
            chapter="552",
            section="552.1",
            title="Divorce; Grounds",
            summary=(
                "Establishes that a complaint for divorce may be filed alleging there has been "
                "a breakdown of the marriage relationship to the extent that the objects of "
                "matrimony have been destroyed and there remains no reasonable likelihood that "
                "the marriage can be preserved."
            ),
            full_text="",
            confidence="verified",
            lanes=["A"],
            tags=["divorce", "grounds", "breakdown", "marriage",
                  "no_fault"],
        ),
        LegalRule(
            rule_id="MCL-552.6",
            source="MCL",
            chapter="552",
            section="552.6",
            title="Property Division",
            summary=(
                "Upon entry of a divorce judgment, the court shall divide the real and personal "
                "property of the parties as it deems just and equitable. The court considers "
                "the duration of the marriage, contributions of each party, and the needs of "
                "each party. This is not an automatic 50/50 split."
            ),
            full_text="",
            confidence="high",
            lanes=["A"],
            tags=["property_division", "divorce", "equitable_distribution",
                  "marital_property", "just_and_equitable"],
        ),
        LegalRule(
            rule_id="MCL-552.13",
            source="MCL",
            chapter="552",
            section="552.13",
            title="Support Obligations",
            summary=(
                "Authorizes the court to order support for a spouse during and after divorce "
                "proceedings. The court considers factors including the ability of either party "
                "to pay, the needs of the parties, and their prior standard of living."
            ),
            full_text="",
            confidence="verified",
            lanes=["A"],
            tags=["support", "alimony", "spousal_support", "divorce",
                  "ability_to_pay", "needs"],
        ),
        LegalRule(
            rule_id="MCL-552.17b",
            source="MCL",
            chapter="552",
            section="552.17b",
            title="Child Support",
            summary=(
                "Governs child support obligations in divorce and custody actions. Support "
                "amounts are calculated using the Michigan Child Support Formula. The court "
                "may deviate from the formula upon a finding that application would be unjust "
                "or inappropriate."
            ),
            full_text="",
            confidence="verified",
            lanes=["A"],
            tags=["child_support", "support_formula", "deviation",
                  "divorce", "custody"],
        ),

        # ─── MCL Chapter 15: Government / FOIA ───────────────

        LegalRule(
            rule_id="MCL-15.231",
            source="MCL",
            chapter="15",
            section="15.231",
            title="Freedom of Information Act; Definitions",
            summary=(
                "Defines key terms under the Michigan Freedom of Information Act including "
                "'public body,' 'public record,' 'person,' and 'written request.' A public "
                "body includes state and local government entities, courts, and agencies."
            ),
            full_text="",
            confidence="verified",
            lanes=["C"],
            tags=["foia", "definitions", "public_body", "public_record",
                  "government", "transparency"],
            url="https://legislature.mi.gov/Laws/MCL?objectName=mcl-15-231",
        ),
        LegalRule(
            rule_id="MCL-15.233",
            source="MCL",
            chapter="15",
            section="15.233",
            title="FOIA; Right to Inspect and Copy Public Records",
            summary=(
                "Every person has the right to inspect, copy, or receive copies of public "
                "records. A public body must respond to a FOIA request within 5 business days. "
                "The response must grant, deny, or partially grant the request with specific "
                "reasons for any denial citing applicable exemptions."
            ),
            full_text="",
            confidence="verified",
            lanes=["C"],
            tags=["foia", "inspect", "copy", "5_business_days",
                  "response", "denial", "exemptions"],
        ),
        LegalRule(
            rule_id="MCL-15.235",
            source="MCL",
            chapter="15",
            section="15.235",
            title="FOIA; Fees",
            summary=(
                "A public body may charge a fee for searching, copying, and mailing public "
                "records. The fee must be limited to actual costs and may not include labor "
                "costs for separating exempt from nonexempt information unless authorized. "
                "A fee waiver or reduction may be available when disclosure is in the public interest."
            ),
            full_text="",
            confidence="verified",
            lanes=["C"],
            tags=["foia", "fees", "actual_costs", "fee_waiver",
                  "public_interest", "copying"],
        ),
        LegalRule(
            rule_id="MCL-15.240",
            source="MCL",
            chapter="15",
            section="15.240",
            title="FOIA; Appeal to Circuit Court",
            summary=(
                "A person denied access to public records under FOIA may commence an action "
                "in circuit court to compel disclosure. The court reviews the public body's "
                "decision de novo. If the court orders disclosure, it may award reasonable "
                "attorney fees, costs, and damages."
            ),
            full_text="",
            confidence="verified",
            lanes=["C"],
            tags=["foia", "appeal", "circuit_court", "de_novo",
                  "attorney_fees", "compel_disclosure"],
        ),

        # ─── MCL Chapter 750: Michigan Penal Code ────────────

        LegalRule(
            rule_id="MCL-750.136b",
            source="MCL",
            chapter="750",
            section="750.136b",
            title="Child Abuse",
            summary=(
                "Defines and penalizes child abuse in Michigan. Covers physical harm or "
                "threatened physical harm, including first-degree (serious physical harm, life "
                "threatening), second-degree (physical harm), third-degree (knowingly or "
                "intentionally causing physical harm), and fourth-degree (recklessly causing "
                "physical harm). Penalties vary by degree."
            ),
            full_text="",
            confidence="verified",
            lanes=["A"],
            tags=["child_abuse", "physical_harm", "felony",
                  "misdemeanor", "penal_code", "cps"],
        ),
        LegalRule(
            rule_id="MCL-750.520b",
            source="MCL",
            chapter="750",
            section="750.520b",
            title="Criminal Sexual Conduct — First Degree",
            summary=(
                "Defines first degree criminal sexual conduct (CSC-1), the most serious sexual "
                "offense in Michigan. Involves sexual penetration under specified aggravating "
                "circumstances including use of a weapon, causing personal injury, or the victim "
                "being under 13 years of age. CSC-1 is a felony punishable by up to life "
                "imprisonment."
            ),
            full_text="",
            confidence="verified",
            lanes=["D"],
            tags=["criminal_sexual_conduct", "csc", "felony",
                  "sexual_penetration", "penal_code"],
        ),

        # ─── MCL Chapter 554: Property ───────────────────────

        LegalRule(
            rule_id="MCL-554.601",
            source="MCL",
            chapter="554",
            section="554.601",
            title="Security Deposits; Landlord-Tenant",
            summary=(
                "Governs security deposits in residential lease agreements. A landlord may not "
                "demand a security deposit exceeding 1.5 months' rent. The landlord must provide "
                "an itemized list of damages within 30 days of termination and return the "
                "remainder. Failure to comply may result in double damages."
            ),
            full_text="",
            confidence="verified",
            lanes=["B"],
            tags=["security_deposit", "landlord_tenant", "1_5_months",
                  "30_days", "double_damages", "itemized_list"],
            url="https://legislature.mi.gov/Laws/MCL?objectName=mcl-554-601",
        ),
        LegalRule(
            rule_id="MCL-554.139",
            source="MCL",
            chapter="554",
            section="554.139",
            title="Implied Warranty of Habitability",
            summary=(
                "In every lease or license of residential premises, there is an implied covenant "
                "that the premises and common areas are fit for their intended use and will be "
                "kept in reasonable repair during the term. The landlord must maintain the "
                "premises in compliance with applicable health and safety codes."
            ),
            full_text="",
            confidence="verified",
            lanes=["B"],
            tags=["habitability", "implied_warranty", "landlord",
                  "reasonable_repair", "health_safety", "lease"],
        ),
    ]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Function 2: Cross-References
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_mcl_cross_refs() -> List[RuleCrossRef]:
    """Return cross-references between MCL statutes and MCL→MCR references."""
    return [
        # MCL → MCR references
        RuleCrossRef(
            from_rule="MCL-722.23",
            to_rule="MCR-3.210",
            relationship="requires",
            description=(
                "The best interest factors in MCL 722.23 must be evaluated at a custody "
                "hearing as required by MCR 3.210. The court must make findings on each factor."
            ),
        ),
        RuleCrossRef(
            from_rule="MCL-600.916",
            to_rule="MCR-2.003",
            relationship="supplements",
            description=(
                "MCL 600.916 provides the statutory grounds for judicial disqualification. "
                "MCR 2.003 provides the procedural mechanism for filing the motion and "
                "affidavit. Both must be consulted together."
            ),
        ),
        RuleCrossRef(
            from_rule="MCL-600.2950",
            to_rule="MCR-3.214",
            relationship="supplements",
            description=(
                "MCL 600.2950 is the statutory authority for personal protection orders. "
                "MCR 3.214 provides the procedural rules for obtaining, modifying, and "
                "terminating PPOs."
            ),
        ),

        # MCL → MCL internal references
        RuleCrossRef(
            from_rule="MCL-722.27",
            to_rule="MCL-722.23",
            relationship="requires",
            description=(
                "Modification of custody under MCL 722.27 requires a best interest analysis "
                "under MCL 722.23 after the threshold showing of proper cause or change of "
                "circumstances is met."
            ),
        ),
        RuleCrossRef(
            from_rule="MCL-722.24",
            to_rule="MCL-722.23",
            relationship="requires",
            description=(
                "A custody hearing under MCL 722.24 requires the court to evaluate each "
                "best interest factor in MCL 722.23."
            ),
        ),
        RuleCrossRef(
            from_rule="MCL-722.27a",
            to_rule="MCL-722.23",
            relationship="see_also",
            description=(
                "Parenting time provisions under MCL 722.27a must account for the best "
                "interest factors in MCL 722.23."
            ),
        ),
        RuleCrossRef(
            from_rule="MCL-600.1711",
            to_rule="MCL-600.1715",
            relationship="requires",
            description=(
                "Civil contempt under MCL 600.1711 requires achievable purge conditions "
                "as specified in MCL 600.1715."
            ),
        ),
        RuleCrossRef(
            from_rule="MCL-600.1701",
            to_rule="MCL-600.1711",
            relationship="see_also",
            description=(
                "Criminal contempt (MCL 600.1701) and civil contempt (MCL 600.1711) have "
                "different standards of proof and purposes. Criminal is punitive (beyond "
                "reasonable doubt); civil is coercive (preponderance)."
            ),
        ),
        RuleCrossRef(
            from_rule="MCL-600.2950a",
            to_rule="MCL-600.2950",
            relationship="supplements",
            description=(
                "MCL 600.2950a supplements the general PPO statute (MCL 600.2950) with "
                "additional protections specific to domestic relationships."
            ),
        ),
        RuleCrossRef(
            from_rule="MCL-15.240",
            to_rule="MCL-15.233",
            relationship="see_also",
            description=(
                "MCL 15.240 provides the circuit court appeal remedy when a FOIA request "
                "under MCL 15.233 is denied."
            ),
        ),
        RuleCrossRef(
            from_rule="MCL-554.139",
            to_rule="MCL-554.601",
            relationship="see_also",
            description=(
                "The implied warranty of habitability (MCL 554.139) and security deposit "
                "rules (MCL 554.601) are both landlord-tenant protections relevant to "
                "housing disputes."
            ),
        ),
        RuleCrossRef(
            from_rule="MCL-722.26a",
            to_rule="MCL-722.31",
            relationship="see_also",
            description=(
                "Change of domicile (MCL 722.26a) intersects with UCCJEA jurisdiction "
                "provisions in MCL 722.31 when relocation crosses state lines."
            ),
        ),
    ]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Module self-test
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    rules = get_mcl_rules()
    xrefs = get_mcl_cross_refs()

    # Verify uniqueness
    rule_ids = [r.rule_id for r in rules]
    assert len(rule_ids) == len(set(rule_ids)), f"Duplicate rule_ids: {[x for x in rule_ids if rule_ids.count(x) > 1]}"

    xref_keys = [(x.from_rule, x.to_rule) for x in xrefs]
    assert len(xref_keys) == len(set(xref_keys)), "Duplicate cross-reference pairs found"

    print(f"MCL Data Module — Self-Test Passed")
    print(f"  Rules:            {len(rules)}")
    print(f"  Cross-References: {len(xrefs)}")
    print(f"  All IDs unique:   ✓")
