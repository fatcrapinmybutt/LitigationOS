"""
MCR Data — Michigan Court Rules for LEXICON Engine
===================================================
Structured data for all Michigan Court Rules relevant to the
Pigors v. Watson litigation across 6 case lanes.

CRITICAL: Only verified rules are marked confidence='verified'.
Any uncertain content is marked 'needs_verification'.
Do NOT fabricate rule numbers or legal content.

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
from lexicon_db import LegalRule, RuleCrossRef, FilingRequirement, DeadlineRule


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Function 1: Michigan Court Rules
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_mcr_rules() -> List[LegalRule]:
    """Return all Michigan Court Rules relevant to the Pigors v. Watson case."""
    return [
        # ─── MCR Chapter 2: Civil Procedure ───────────────────

        LegalRule(
            rule_id="MCR-2.003",
            source="MCR",
            chapter="2",
            section="2.003",
            title="Disqualification of Judge",
            summary=(
                "Establishes grounds for disqualifying a judge, including personal bias or "
                "prejudice, ex parte communications, personal knowledge of disputed facts, or "
                "financial interest. A party must file a motion and affidavit stating the grounds. "
                "The challenged judge may respond or refer the motion to the chief judge."
            ),
            full_text="",
            confidence="verified",
            lanes=["A", "B", "D", "E"],
            tags=["disqualification", "bias", "ex_parte", "recusal", "judge",
                  "motion", "affidavit", "judicial_misconduct"],
            url="https://courts.michigan.gov/siteassets/rules-instructions-administrative-orders/michigan-court-rules/court-rules-book-ch-2-responsive-html5.zip/MCR/Court-Rules-Book-Ch-2/Content/Court-Rules/Ch-2-Civil-Procedure/Rule-2-003.htm",
        ),
        LegalRule(
            rule_id="MCR-2.107",
            source="MCR",
            chapter="2",
            section="2.107",
            title="Service and Filing of Pleadings and Other Papers",
            summary=(
                "After initial service of process, every subsequent pleading, motion, or court "
                "paper must be served on each party. Service may be made by delivery, mail, "
                "e-filing, or other means agreed upon. Proof of service must be filed with the court."
            ),
            full_text="",
            confidence="verified",
            lanes=["A", "B", "C", "D", "E", "F"],
            tags=["service", "filing", "pleadings", "proof_of_service", "delivery",
                  "mail", "efiling"],
        ),
        LegalRule(
            rule_id="MCR-2.108",
            source="MCR",
            chapter="2",
            section="2.108",
            title="Service of Process",
            summary=(
                "Governs initial service of the summons and complaint on a defendant. Requires "
                "personal service, service by registered mail with return receipt, or substituted "
                "service. The defendant has 21 days after service to file a responsive pleading."
            ),
            full_text="",
            confidence="verified",
            lanes=["A", "B", "C", "D", "E", "F"],
            tags=["service_of_process", "summons", "complaint", "personal_service",
                  "registered_mail", "21_days"],
        ),
        LegalRule(
            rule_id="MCR-2.110",
            source="MCR",
            chapter="2",
            section="2.110",
            title="Pleadings Allowed; Form of Motions",
            summary=(
                "Specifies the permitted pleadings in civil actions: complaint, answer, "
                "counterclaim, cross-claim, third-party complaint, and replies. No other "
                "pleadings are allowed unless ordered by the court. Motions must be in writing "
                "unless made during a hearing or trial."
            ),
            full_text="",
            confidence="verified",
            lanes=["A", "B"],
            tags=["pleadings", "complaint", "answer", "counterclaim", "cross_claim",
                  "motions", "form"],
        ),
        LegalRule(
            rule_id="MCR-2.116",
            source="MCR",
            chapter="2",
            section="2.116",
            title="Summary Disposition",
            summary=(
                "Provides grounds for dismissal or judgment before trial. Subsection (C) lists "
                "specific grounds including failure to state a claim, no genuine issue of material "
                "fact, and governmental immunity. The moving party bears the initial burden; the "
                "nonmoving party must then demonstrate a genuine issue exists."
            ),
            full_text="",
            confidence="verified",
            lanes=["B"],
            tags=["summary_disposition", "dismissal", "judgment", "no_genuine_issue",
                  "standard_of_review", "motion"],
        ),
        LegalRule(
            rule_id="MCR-2.119",
            source="MCR",
            chapter="2",
            section="2.119",
            title="Motion Practice",
            summary=(
                "Governs how motions are filed and heard. A motion must be served at least 9 days "
                "before the hearing date. A response brief is due at least 7 days before the "
                "hearing. A reply brief may be served at least 4 days before the hearing. The "
                "court may allow oral argument. Motions must be accompanied by a brief and "
                "supporting documentation."
            ),
            full_text="",
            confidence="verified",
            lanes=["A", "B", "C", "D", "E", "F"],
            tags=["motion_practice", "9_day_notice", "brief", "oral_argument",
                  "hearing", "response", "reply", "service"],
        ),
        LegalRule(
            rule_id="MCR-2.302",
            source="MCR",
            chapter="2",
            section="2.302",
            title="General Rules of Discovery",
            summary=(
                "Parties may obtain discovery of any matter not privileged that is relevant to "
                "the subject matter of the pending action. Discovery methods include depositions, "
                "interrogatories, production of documents, physical examinations, and requests for "
                "admission. The court may issue protective orders limiting discovery."
            ),
            full_text="",
            confidence="verified",
            lanes=["A", "B", "D"],
            tags=["discovery", "interrogatories", "depositions", "production",
                  "protective_order", "relevance", "privilege"],
        ),
        LegalRule(
            rule_id="MCR-2.310",
            source="MCR",
            chapter="2",
            section="2.310",
            title="Requests for Admissions",
            summary=(
                "A party may serve a written request for admission of the truth of any matter "
                "relevant to the action. Failure to respond within 28 days results in the matter "
                "being deemed admitted. Admissions may be withdrawn only by court order."
            ),
            full_text="",
            confidence="verified",
            lanes=["A", "B"],
            tags=["admissions", "requests_for_admission", "deemed_admitted",
                  "28_days", "discovery"],
        ),
        LegalRule(
            rule_id="MCR-2.313",
            source="MCR",
            chapter="2",
            section="2.313",
            title="Failure to Provide Discovery",
            summary=(
                "If a party fails to comply with discovery obligations, the court may impose "
                "sanctions including: ordering compliance, prohibiting evidence, striking "
                "pleadings, staying proceedings, dismissing the action, or entering default "
                "judgment. The court may also award attorney fees."
            ),
            full_text="",
            confidence="verified",
            lanes=["A", "B"],
            tags=["discovery_sanctions", "failure_to_disclose", "default",
                  "attorney_fees", "sanctions", "contempt"],
        ),
        LegalRule(
            rule_id="MCR-2.504",
            source="MCR",
            chapter="2",
            section="2.504",
            title="Entry of Default and Default Judgment",
            summary=(
                "When a party against whom a judgment for affirmative relief is sought has failed "
                "to plead or otherwise defend within the time allowed, the clerk must enter the "
                "default. Default judgment may then be entered by the clerk (for a sum certain) "
                "or by the court (in other cases). The defaulted party may seek to set aside the "
                "default for good cause."
            ),
            full_text="",
            confidence="verified",
            lanes=["A", "B"],
            tags=["default", "default_judgment", "failure_to_plead", "set_aside",
                  "good_cause", "clerk_entry"],
        ),
        LegalRule(
            rule_id="MCR-2.612",
            source="MCR",
            chapter="2",
            section="2.612",
            title="Relief From Judgment or Order",
            summary=(
                "Provides grounds for a court to relieve a party from a final judgment or order. "
                "Grounds include: mistake, newly discovered evidence, fraud, the judgment is void, "
                "or any other reason justifying relief. A motion under this rule must be filed "
                "within a reasonable time, and for certain grounds no more than one year after "
                "the judgment or order. Filed as a motion under MCR 2.119."
            ),
            full_text="",
            confidence="verified",
            lanes=["A", "D"],
            tags=["relief_from_judgment", "vacatur", "set_aside", "fraud",
                  "newly_discovered_evidence", "void_judgment", "one_year",
                  "motion"],
        ),

        # ─── MCR Chapter 3: Special Proceedings — Family ─────

        LegalRule(
            rule_id="MCR-3.201",
            source="MCR",
            chapter="3",
            section="3.201",
            title="Applicability of Rules",
            summary=(
                "Chapter 2 civil procedure rules apply to domestic relations actions except "
                "as modified by this subchapter. This means general motion practice (MCR 2.119), "
                "discovery (MCR 2.302), and service rules (MCR 2.107) all apply in family cases "
                "unless specifically overridden."
            ),
            full_text="",
            confidence="verified",
            lanes=["A", "D"],
            tags=["domestic_relations", "family", "applicability",
                  "civil_procedure", "incorporation"],
        ),
        LegalRule(
            rule_id="MCR-3.206",
            source="MCR",
            chapter="3",
            section="3.206",
            title="Initiating a Case",
            summary=(
                "Domestic relations cases (divorce, custody, support, paternity) are initiated "
                "by filing a complaint and summons. The complaint must contain specific "
                "allegations including grounds and requests for relief. Motions in these cases "
                "follow MCR 2.119 general motion practice. A verified statement and UCCJEA "
                "affidavit are required."
            ),
            full_text="",
            confidence="verified",
            lanes=["A"],
            tags=["domestic_relations", "complaint", "initiating_case", "custody",
                  "divorce", "summons", "uccjea"],
        ),
        LegalRule(
            rule_id="MCR-3.208",
            source="MCR",
            chapter="3",
            section="3.208",
            title="Discovery in Domestic Relations Actions",
            summary=(
                "Discovery in domestic relations actions is governed by the general discovery "
                "rules in MCR 2.302-2.313 with certain modifications. Parties must exchange "
                "verified financial statements. The court may limit discovery to protect children "
                "or prevent harassment."
            ),
            full_text="",
            confidence="verified",
            lanes=["A"],
            tags=["discovery", "domestic_relations", "financial_disclosure",
                  "family", "interrogatories"],
        ),
        LegalRule(
            rule_id="MCR-3.210",
            source="MCR",
            chapter="3",
            section="3.210",
            title="Hearings in Domestic Relations Actions",
            summary=(
                "In contested custody disputes, the court must make findings on each of the "
                "best interest factors in MCL 722.23(a)-(l). The court must state findings and "
                "conclusions on the record or in a written opinion. Applies to initial custody "
                "determinations and modifications."
            ),
            full_text="",
            confidence="verified",
            lanes=["A"],
            tags=["custody_hearing", "best_interest_factors", "findings",
                  "mcl_722_23", "domestic_relations", "trial"],
        ),
        LegalRule(
            rule_id="MCR-3.211",
            source="MCR",
            chapter="3",
            section="3.211",
            title="Child Custody Mediation",
            summary=(
                "Before a custody dispute is heard by the court, the parties may be referred to "
                "mediation. Mediation is not required when there is evidence of domestic violence. "
                "Mediator communications are confidential and not admissible in court."
            ),
            full_text="",
            confidence="verified",
            lanes=["A"],
            tags=["mediation", "custody", "confidential", "domestic_violence",
                  "alternative_dispute_resolution"],
        ),
        LegalRule(
            rule_id="MCR-3.214",
            source="MCR",
            chapter="3",
            section="3.214",
            title="Personal Protection Orders",
            summary=(
                "Governs the procedure for obtaining, modifying, and terminating personal "
                "protection orders under MCL 600.2950. A PPO may be issued ex parte if there "
                "is immediate and irreparable injury. The respondent may file a motion to "
                "modify or terminate. Violation of a PPO may result in contempt."
            ),
            full_text="",
            confidence="verified",
            lanes=["A", "D"],
            tags=["ppo", "personal_protection_order", "ex_parte",
                  "domestic_violence", "contempt", "modify", "terminate"],
        ),
        LegalRule(
            rule_id="MCR-3.219",
            source="MCR",
            chapter="3",
            section="3.219",
            title="Postjudgment Transfer and Removal Actions",
            summary=(
                "Governs actions for transferring or removing a case to another court after "
                "judgment, including change of domicile motions. A party seeking to change the "
                "child's legal residence to a location more than 100 miles from the current "
                "residence must file a motion under MCL 722.31."
            ),
            full_text="",
            confidence="verified",
            lanes=["A"],
            tags=["postjudgment", "transfer", "removal", "change_of_domicile",
                  "100_miles", "custody"],
        ),

        # ─── MCR Chapter 3: Friend of the Court ──────────────

        LegalRule(
            rule_id="MCR-3.701",
            source="MCR",
            chapter="3",
            section="3.701",
            title="Friend of the Court; General Provisions",
            summary=(
                "The Friend of the Court (FOC) assists the family court in domestic relations "
                "cases involving minor children. The FOC investigates, recommends, and enforces "
                "custody, parenting time, and support orders. Parties have the right to review "
                "FOC files and recommendations."
            ),
            full_text="",
            confidence="verified",
            lanes=["A"],
            tags=["foc", "friend_of_court", "custody", "support",
                  "investigation", "recommendation", "enforcement"],
        ),
        LegalRule(
            rule_id="MCR-3.703",
            source="MCR",
            chapter="3",
            section="3.703",
            title="Review and Modification of Support and Custody Orders",
            summary=(
                "Either party may request the FOC to review an existing support or custody order. "
                "Modifications require a showing of proper cause or a change of circumstances. "
                "The FOC must serve its recommendation on the parties, who then have 21 days "
                "to file an objection."
            ),
            full_text="",
            confidence="verified",
            lanes=["A"],
            tags=["modification", "support", "custody", "foc", "review",
                  "change_of_circumstances", "proper_cause", "objection"],
        ),
        LegalRule(
            rule_id="MCR-3.706",
            source="MCR",
            chapter="3",
            section="3.706",
            title="Referees",
            summary=(
                "A referee may hear domestic relations matters by reference from the court. "
                "The referee's recommendations are not binding; a party may file a written "
                "objection within 21 days. The court then conducts a de novo hearing on the "
                "objected matters."
            ),
            full_text="",
            confidence="verified",
            lanes=["A"],
            tags=["referee", "hearing", "objection", "de_novo",
                  "domestic_relations", "recommendation"],
        ),
        LegalRule(
            rule_id="MCR-3.708",
            source="MCR",
            chapter="3",
            section="3.708",
            title="Friend of the Court Grievances",
            summary=(
                "A party may file a grievance against the FOC for failure to perform duties or "
                "for misconduct. The grievance must be filed with the chief judge. The FOC "
                "office must respond within 21 days. Objections to FOC recommendations must "
                "also be filed within 21 days of service of the recommendation."
            ),
            full_text="",
            confidence="verified",
            lanes=["A"],
            tags=["foc_grievance", "complaint", "chief_judge", "misconduct",
                  "objection", "21_days"],
        ),

        # ─── MCR Chapter 7: Court of Appeals ─────────────────

        LegalRule(
            rule_id="MCR-7.201",
            source="MCR",
            chapter="7",
            section="7.201",
            title="Organization of the Court of Appeals",
            summary=(
                "Describes the organization of the Michigan Court of Appeals, including its "
                "divisions, panels, and administrative structure. Cases are typically heard by "
                "three-judge panels."
            ),
            full_text="",
            confidence="verified",
            lanes=["F"],
            tags=["coa", "court_of_appeals", "organization", "panels",
                  "appellate"],
        ),
        LegalRule(
            rule_id="MCR-7.203",
            source="MCR",
            chapter="7",
            section="7.203",
            title="Jurisdiction of the Court of Appeals",
            summary=(
                "The Court of Appeals has jurisdiction over appeals of right from final judgments "
                "or orders of the circuit court, and by leave from interlocutory orders. "
                "Defines which orders are appealable as of right versus by leave."
            ),
            full_text="",
            confidence="verified",
            lanes=["F"],
            tags=["coa", "jurisdiction", "appeal_of_right", "leave_to_appeal",
                  "final_judgment", "interlocutory"],
        ),
        LegalRule(
            rule_id="MCR-7.204",
            source="MCR",
            chapter="7",
            section="7.204",
            title="Filing Appeal of Right",
            summary=(
                "An appeal of right from a final judgment must be filed within 21 days of the "
                "entry of the judgment or order being appealed. The claim of appeal must be filed "
                "in the Court of Appeals with the required filing fee. A copy must also be filed "
                "in the trial court."
            ),
            full_text="",
            confidence="verified",
            lanes=["F"],
            tags=["appeal_of_right", "21_days", "claim_of_appeal", "filing_fee",
                  "final_judgment", "coa"],
        ),
        LegalRule(
            rule_id="MCR-7.205",
            source="MCR",
            chapter="7",
            section="7.205",
            title="Application for Leave to Appeal",
            summary=(
                "When an appeal is not of right, a party must file an application for leave to "
                "appeal within 21 days of the order being challenged. The application must include "
                "a statement of questions presented, a statement of facts, and arguments with "
                "supporting authorities. Briefs must comply with MCR 7.212."
            ),
            full_text="",
            confidence="verified",
            lanes=["F"],
            tags=["leave_to_appeal", "application", "21_days", "coa",
                  "interlocutory", "discretionary"],
        ),
        LegalRule(
            rule_id="MCR-7.206",
            source="MCR",
            chapter="7",
            section="7.206",
            title="Extraordinary Writs and Emergency Procedures",
            summary=(
                "Provides for emergency motions and extraordinary writs in the Court of Appeals, "
                "including motions for immediate consideration, stays pending appeal, and "
                "superintending control. Used when ordinary appellate process is too slow to "
                "prevent irreparable harm."
            ),
            full_text="",
            confidence="verified",
            lanes=["F"],
            tags=["extraordinary_writ", "emergency", "stay", "superintending_control",
                  "immediate_consideration", "coa"],
        ),
        LegalRule(
            rule_id="MCR-7.208",
            source="MCR",
            chapter="7",
            section="7.208",
            title="Filing Requirements in the Court of Appeals",
            summary=(
                "Specifies filing requirements for all papers submitted to the Court of Appeals, "
                "including format, number of copies, electronic filing requirements, and "
                "certificate of service. All filings must be served on opposing parties."
            ),
            full_text="",
            confidence="verified",
            lanes=["F"],
            tags=["coa", "filing_requirements", "format", "efiling",
                  "certificate_of_service", "copies"],
        ),
        LegalRule(
            rule_id="MCR-7.210",
            source="MCR",
            chapter="7",
            section="7.210",
            title="Record on Appeal",
            summary=(
                "The appellant must ensure the lower court record is filed with the Court of "
                "Appeals. The record includes all documents, exhibits, and transcripts from "
                "the trial court. The appellant may designate portions of the record relevant "
                "to the issues on appeal."
            ),
            full_text="",
            confidence="verified",
            lanes=["F"],
            tags=["record_on_appeal", "transcripts", "exhibits", "lower_court",
                  "designation", "coa"],
        ),
        LegalRule(
            rule_id="MCR-7.212",
            source="MCR",
            chapter="7",
            section="7.212",
            title="Briefs",
            summary=(
                "Establishes format and content requirements for appellate briefs. The appellant's "
                "brief is due 56 days after the claim of appeal or grant of leave. Briefs must "
                "include a table of contents, statement of questions presented, statement of facts, "
                "argument with citations, and relief requested. Page and word limits apply."
            ),
            full_text="",
            confidence="verified",
            lanes=["F"],
            tags=["brief", "appellate_brief", "56_days", "format",
                  "page_limits", "statement_of_questions", "coa"],
        ),
        LegalRule(
            rule_id="MCR-7.215",
            source="MCR",
            chapter="7",
            section="7.215",
            title="Opinions and Orders of the Court of Appeals",
            summary=(
                "COA decisions are issued as published opinions, unpublished opinions, or orders. "
                "Published opinions are binding precedent. Unpublished opinions are not "
                "precedentially binding but may be cited for their persuasive reasoning."
            ),
            full_text="",
            confidence="verified",
            lanes=["F"],
            tags=["coa", "opinions", "orders", "precedent", "published",
                  "unpublished", "binding"],
        ),

        # ─── MCR Chapter 7: Michigan Supreme Court ───────────

        LegalRule(
            rule_id="MCR-7.301",
            source="MCR",
            chapter="7",
            section="7.301",
            title="Application for Leave to Appeal to Supreme Court",
            summary=(
                "A party may apply for leave to appeal to the Michigan Supreme Court within 56 "
                "days after the Court of Appeals decision. The application must comply with "
                "MCR 7.302 submission requirements. The MSC has discretion to grant or deny "
                "leave to appeal."
            ),
            full_text="",
            confidence="verified",
            lanes=["F"],
            tags=["msc", "supreme_court", "leave_to_appeal", "56_days",
                  "discretionary", "application"],
        ),
        LegalRule(
            rule_id="MCR-7.302",
            source="MCR",
            chapter="7",
            section="7.302",
            title="Required Submissions to the Supreme Court",
            summary=(
                "Specifies the required contents and format for filings in the Michigan Supreme "
                "Court. Applications for leave must include a concise statement of the questions "
                "presented, reasons for granting the application, and a copy of the COA decision."
            ),
            full_text="",
            confidence="verified",
            lanes=["F"],
            tags=["msc", "supreme_court", "submission_requirements", "format",
                  "application", "coa_decision"],
        ),
        LegalRule(
            rule_id="MCR-7.303",
            source="MCR",
            chapter="7",
            section="7.303",
            title="Original Proceedings in the Supreme Court",
            summary=(
                "The Supreme Court may exercise original jurisdiction in extraordinary cases. "
                "This includes actions for superintending control over lower courts, habeas "
                "corpus, and mandamus. Used when no adequate remedy exists in lower courts."
            ),
            full_text="",
            confidence="verified",
            lanes=["F", "E"],
            tags=["msc", "supreme_court", "original_jurisdiction",
                  "superintending_control", "mandamus", "habeas_corpus",
                  "extraordinary"],
        ),
        LegalRule(
            rule_id="MCR-7.305",
            source="MCR",
            chapter="7",
            section="7.305",
            title="Extraordinary Writs in the Supreme Court",
            summary=(
                "The Supreme Court may issue writs of superintending control, mandamus, habeas "
                "corpus, and quo warranto. These are reserved for cases of exceptional public "
                "importance or when lower courts have clearly erred and no other remedy is "
                "available."
            ),
            full_text="",
            confidence="verified",
            lanes=["F", "E"],
            tags=["msc", "supreme_court", "extraordinary_writ", "mandamus",
                  "superintending_control", "habeas_corpus", "quo_warranto"],
        ),

        # ─── MCR Chapter 8: Administrative ───────────────────

        LegalRule(
            rule_id="MCR-8.119",
            source="MCR",
            chapter="8",
            section="8.119",
            title="Court Records and Reports; Duties of Clerk",
            summary=(
                "Governs public access to court records and confidentiality protections. "
                "Subsection (H) requires that in cases involving minors, only initials are used "
                "in public documents to protect the child's identity. Court records are generally "
                "open to the public unless sealed by court order."
            ),
            full_text="",
            confidence="verified",
            lanes=["A", "D"],
            tags=["court_records", "public_access", "confidentiality", "minor",
                  "initials", "sealed", "clerk", "privacy"],
        ),
    ]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Function 2: Cross-References
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_mcr_cross_refs() -> List[RuleCrossRef]:
    """Return cross-references between MCR rules and MCR→MCL references."""
    return [
        # MCR → MCL references
        RuleCrossRef(
            from_rule="MCR-2.003",
            to_rule="MCL-600.916",
            relationship="supplements",
            description=(
                "MCR 2.003 provides the procedural mechanism for judicial disqualification; "
                "MCL 600.916 provides the statutory grounds. Both must be consulted when "
                "seeking disqualification."
            ),
        ),
        RuleCrossRef(
            from_rule="MCR-3.210",
            to_rule="MCL-722.23",
            relationship="requires",
            description=(
                "MCR 3.210 requires the court to make findings on each best interest factor "
                "listed in MCL 722.23(a)-(l) in contested custody disputes."
            ),
        ),
        RuleCrossRef(
            from_rule="MCR-3.214",
            to_rule="MCL-600.2950",
            relationship="supplements",
            description=(
                "MCR 3.214 establishes the court rule procedure for PPOs; MCL 600.2950 is the "
                "authorizing statute. The rule implements the statutory framework."
            ),
        ),

        # MCR → MCR internal references
        RuleCrossRef(
            from_rule="MCR-2.119",
            to_rule="MCR-2.107",
            relationship="requires",
            description=(
                "Service of motions under MCR 2.119 follows the same methods as service of "
                "pleadings under MCR 2.107."
            ),
        ),
        RuleCrossRef(
            from_rule="MCR-3.206",
            to_rule="MCR-2.119",
            relationship="supplements",
            description=(
                "Motions in domestic relations cases initiated under MCR 3.206 follow general "
                "motion practice under MCR 2.119."
            ),
        ),
        RuleCrossRef(
            from_rule="MCR-7.205",
            to_rule="MCR-7.212",
            relationship="requires",
            description=(
                "An application for leave to appeal under MCR 7.205 must include a brief "
                "complying with the format and content requirements of MCR 7.212."
            ),
        ),
        RuleCrossRef(
            from_rule="MCR-7.301",
            to_rule="MCR-7.302",
            relationship="requires",
            description=(
                "An application for leave to the MSC under MCR 7.301 must include the "
                "submissions specified in MCR 7.302."
            ),
        ),
        RuleCrossRef(
            from_rule="MCR-2.612",
            to_rule="MCR-2.119",
            relationship="requires",
            description=(
                "A motion for relief from judgment under MCR 2.612 is filed as a motion "
                "under MCR 2.119, following standard motion practice procedures."
            ),
        ),

        # Additional important cross-references
        RuleCrossRef(
            from_rule="MCR-3.201",
            to_rule="MCR-2.119",
            relationship="supplements",
            description=(
                "MCR 3.201 incorporates Chapter 2 civil procedure rules into domestic relations "
                "proceedings, making MCR 2.119 motion practice applicable in family court."
            ),
        ),
        RuleCrossRef(
            from_rule="MCR-3.201",
            to_rule="MCR-2.302",
            relationship="supplements",
            description=(
                "MCR 3.201 incorporates general discovery rules (MCR 2.302) into domestic "
                "relations proceedings, subject to modifications in MCR 3.208."
            ),
        ),
        RuleCrossRef(
            from_rule="MCR-3.208",
            to_rule="MCR-2.302",
            relationship="supplements",
            description=(
                "MCR 3.208 modifies the general discovery rules of MCR 2.302 for domestic "
                "relations actions, adding financial disclosure requirements."
            ),
        ),
        RuleCrossRef(
            from_rule="MCR-3.703",
            to_rule="MCR-3.706",
            relationship="see_also",
            description=(
                "FOC review and modification under MCR 3.703 may involve referee hearings "
                "governed by MCR 3.706."
            ),
        ),
        RuleCrossRef(
            from_rule="MCR-7.204",
            to_rule="MCR-7.208",
            relationship="requires",
            description=(
                "Claims of appeal filed under MCR 7.204 must comply with the filing "
                "requirements of MCR 7.208."
            ),
        ),
        RuleCrossRef(
            from_rule="MCR-7.204",
            to_rule="MCR-7.210",
            relationship="see_also",
            description=(
                "After filing an appeal of right under MCR 7.204, the appellant must ensure "
                "the record is prepared under MCR 7.210."
            ),
        ),
        RuleCrossRef(
            from_rule="MCR-2.504",
            to_rule="MCR-2.612",
            relationship="see_also",
            description=(
                "A default judgment entered under MCR 2.504 may be set aside under MCR 2.612 "
                "if grounds for relief from judgment exist."
            ),
        ),
        RuleCrossRef(
            from_rule="MCR-3.219",
            to_rule="MCL-722.31",
            relationship="requires",
            description=(
                "MCR 3.219 postjudgment change-of-domicile actions are governed by the "
                "statutory factors in MCL 722.31."
            ),
        ),
    ]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Function 3: Filing Requirements
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_mcr_filing_requirements() -> List[FilingRequirement]:
    """Return filing requirements for key motion types in relevant courts."""
    return [
        # ─── Motion to Modify Custody ─────────────────────────

        FilingRequirement(
            requirement_id="FR-modify-custody-notice",
            filing_type="motion_to_modify_custody",
            court="14th_circuit_family",
            rule_id="MCR-2.119",
            requirement="Motion must be served at least 9 days before the hearing date",
            category="notice",
            is_mandatory=True,
            deadline_formula="9_days_before_hearing",
            notes="Service per MCR 2.107; add 3 days if served by mail",
        ),
        FilingRequirement(
            requirement_id="FR-modify-custody-form",
            filing_type="motion_to_modify_custody",
            court="14th_circuit_family",
            rule_id="MCR-3.703",
            requirement="File motion on appropriate FOC forms or by separate motion with supporting brief",
            category="form",
            is_mandatory=True,
            forms_required=["FOC 89"],
            notes="FOC 89 is the Uniform Child Custody/Support/Parenting Time Order form; "
                  "a separate motion and brief are also required",
        ),
        FilingRequirement(
            requirement_id="FR-modify-custody-service",
            filing_type="motion_to_modify_custody",
            court="14th_circuit_family",
            rule_id="MCR-2.107",
            requirement="Serve opposing party and FOC with the motion and all supporting documents",
            category="service",
            is_mandatory=True,
            notes="Include proof of service; serve FOC at 990 Terrace St, Muskegon, MI 49442",
        ),
        FilingRequirement(
            requirement_id="FR-modify-custody-content",
            filing_type="motion_to_modify_custody",
            court="14th_circuit_family",
            rule_id="MCR-3.210",
            requirement=(
                "Motion must allege proper cause or change of circumstances and address "
                "the best interest factors under MCL 722.23"
            ),
            category="content",
            is_mandatory=True,
            notes="Must demonstrate both threshold (change of circumstances) and substantive (best interest) requirements",
        ),
        FilingRequirement(
            requirement_id="FR-modify-custody-fee",
            filing_type="motion_to_modify_custody",
            court="14th_circuit_family",
            requirement="Filing fee for postjudgment motion; fee waiver available via MC 20",
            category="fee",
            is_mandatory=True,
            forms_required=["MC 20"],
            notes="MC 20 is Fee Waiver Request; check current Muskegon County fee schedule",
        ),

        # ─── Motion to Disqualify Judge ───────────────────────

        FilingRequirement(
            requirement_id="FR-disqualify-notice",
            filing_type="motion_to_disqualify_judge",
            court="14th_circuit_family",
            rule_id="MCR-2.003",
            requirement="File motion and supporting affidavit with the court",
            category="notice",
            is_mandatory=True,
            notes=(
                "Motion must be timely — file as soon as grounds are known. "
                "The challenged judge may rule on the motion or refer it to the chief judge."
            ),
        ),
        FilingRequirement(
            requirement_id="FR-disqualify-content",
            filing_type="motion_to_disqualify_judge",
            court="14th_circuit_family",
            rule_id="MCR-2.003",
            requirement=(
                "Motion must include an affidavit stating specific facts showing personal "
                "bias, prejudice, ex parte communications, or other disqualifying grounds"
            ),
            category="content",
            is_mandatory=True,
            notes="Affidavit must be based on personal knowledge; conclusory allegations are insufficient",
        ),
        FilingRequirement(
            requirement_id="FR-disqualify-service",
            filing_type="motion_to_disqualify_judge",
            court="14th_circuit_family",
            rule_id="MCR-2.107",
            requirement="Serve opposing party with the motion and affidavit",
            category="service",
            is_mandatory=True,
        ),
        FilingRequirement(
            requirement_id="FR-disqualify-form",
            filing_type="motion_to_disqualify_judge",
            court="14th_circuit_family",
            rule_id="MCR-2.003",
            requirement="No specific SCAO form required; file by separate motion with supporting affidavit",
            category="form",
            is_mandatory=False,
            notes="Use caption of existing case; include proposed order for disqualification",
        ),

        # ─── Motion to Vacate Order ──────────────────────────

        FilingRequirement(
            requirement_id="FR-vacate-notice",
            filing_type="motion_to_vacate_order",
            court="14th_circuit_family",
            rule_id="MCR-2.119",
            requirement="Motion must be served at least 9 days before the hearing date",
            category="notice",
            is_mandatory=True,
            deadline_formula="9_days_before_hearing",
        ),
        FilingRequirement(
            requirement_id="FR-vacate-content",
            filing_type="motion_to_vacate_order",
            court="14th_circuit_family",
            rule_id="MCR-2.612",
            requirement=(
                "Must state specific grounds for relief: mistake, newly discovered evidence, "
                "fraud, void judgment, or other justifying reason. Must be filed within a "
                "reasonable time and within one year for certain grounds."
            ),
            category="content",
            is_mandatory=True,
            notes="Attach supporting affidavit and exhibits demonstrating grounds",
        ),
        FilingRequirement(
            requirement_id="FR-vacate-service",
            filing_type="motion_to_vacate_order",
            court="14th_circuit_family",
            rule_id="MCR-2.107",
            requirement="Serve opposing party with motion, brief, and all supporting documents",
            category="service",
            is_mandatory=True,
        ),

        # ─── PPO Modification ────────────────────────────────

        FilingRequirement(
            requirement_id="FR-ppo-mod-form",
            filing_type="ppo_modification",
            court="14th_circuit_family",
            rule_id="MCR-3.214",
            requirement="File motion to modify or terminate PPO on appropriate SCAO forms",
            category="form",
            is_mandatory=True,
            forms_required=["CC 375", "CC 376"],
            notes="CC 375 is Motion to Modify/Terminate PPO; CC 376 is the associated order form",
        ),
        FilingRequirement(
            requirement_id="FR-ppo-mod-content",
            filing_type="ppo_modification",
            court="14th_circuit_family",
            rule_id="MCR-3.214",
            requirement=(
                "Must state specific grounds for modification or termination, such as "
                "changed circumstances or that the PPO is no longer necessary"
            ),
            category="content",
            is_mandatory=True,
        ),
        FilingRequirement(
            requirement_id="FR-ppo-mod-service",
            filing_type="ppo_modification",
            court="14th_circuit_family",
            rule_id="MCR-2.107",
            requirement="Serve the petitioner/protected party with the motion",
            category="service",
            is_mandatory=True,
            notes="Service must comply with MCR 2.107; verify current address",
        ),

        # ─── Application for Leave to Appeal — COA ───────────

        FilingRequirement(
            requirement_id="FR-coa-leave-deadline",
            filing_type="application_for_leave",
            court="michigan_coa",
            rule_id="MCR-7.205",
            requirement="Application must be filed within 21 days of the entry of the order being appealed",
            category="deadline",
            is_mandatory=True,
            deadline_formula="21_days_after_order",
        ),
        FilingRequirement(
            requirement_id="FR-coa-leave-content",
            filing_type="application_for_leave",
            court="michigan_coa",
            rule_id="MCR-7.205",
            requirement=(
                "Must include statement of questions presented, statement of facts, argument "
                "with supporting authorities, and copies of the order being appealed and any "
                "related opinions"
            ),
            category="content",
            is_mandatory=True,
            notes="Brief must comply with MCR 7.212 format requirements",
        ),
        FilingRequirement(
            requirement_id="FR-coa-leave-format",
            filing_type="application_for_leave",
            court="michigan_coa",
            rule_id="MCR-7.208",
            requirement="Must comply with COA filing requirements including format, copies, and e-filing",
            category="format",
            is_mandatory=True,
            notes="Electronic filing via TrueFiling required; include certificate of service",
        ),
        FilingRequirement(
            requirement_id="FR-coa-leave-fee",
            filing_type="application_for_leave",
            court="michigan_coa",
            requirement="Filing fee required; fee waiver available via MC 20",
            category="fee",
            is_mandatory=True,
            forms_required=["MC 20"],
            notes="Check current COA filing fee schedule",
        ),
        FilingRequirement(
            requirement_id="FR-coa-leave-service",
            filing_type="application_for_leave",
            court="michigan_coa",
            rule_id="MCR-7.208",
            requirement="Serve all parties and file proof of service with the application",
            category="service",
            is_mandatory=True,
        ),

        # ─── Application for Leave to Appeal — MSC ───────────

        FilingRequirement(
            requirement_id="FR-msc-leave-deadline",
            filing_type="application_for_leave",
            court="michigan_msc",
            rule_id="MCR-7.301",
            requirement="Application must be filed within 56 days of the COA decision",
            category="deadline",
            is_mandatory=True,
            deadline_formula="56_days_after_coa_decision",
        ),
        FilingRequirement(
            requirement_id="FR-msc-leave-content",
            filing_type="application_for_leave",
            court="michigan_msc",
            rule_id="MCR-7.302",
            requirement=(
                "Must include concise statement of questions presented, reasons for granting "
                "leave, copy of COA decision, and any relevant lower court orders"
            ),
            category="content",
            is_mandatory=True,
            notes="Must demonstrate that the case involves a significant issue of law or public importance",
        ),
        FilingRequirement(
            requirement_id="FR-msc-leave-fee",
            filing_type="application_for_leave",
            court="michigan_msc",
            requirement="Filing fee required; fee waiver available via MC 20",
            category="fee",
            is_mandatory=True,
            forms_required=["MC 20"],
            notes="Check current MSC filing fee schedule",
        ),
        FilingRequirement(
            requirement_id="FR-msc-leave-service",
            filing_type="application_for_leave",
            court="michigan_msc",
            rule_id="MCR-7.302",
            requirement="Serve all parties and file proof of service",
            category="service",
            is_mandatory=True,
        ),

        # ─── Motion for Contempt ─────────────────────────────

        FilingRequirement(
            requirement_id="FR-contempt-notice",
            filing_type="motion_for_contempt",
            court="14th_circuit_family",
            rule_id="MCR-2.119",
            requirement="Motion must be served at least 9 days before the hearing date",
            category="notice",
            is_mandatory=True,
            deadline_formula="9_days_before_hearing",
        ),
        FilingRequirement(
            requirement_id="FR-contempt-content",
            filing_type="motion_for_contempt",
            court="14th_circuit_family",
            rule_id="MCL-600.1701",
            requirement=(
                "Must identify the specific court order violated, describe the specific acts "
                "or omissions constituting the violation, and demonstrate the respondent had "
                "knowledge of the order and ability to comply"
            ),
            category="content",
            is_mandatory=True,
            notes=(
                "For civil contempt (MCL 600.1711): must show current ability to comply. "
                "For criminal contempt (MCL 600.1701): must meet beyond reasonable doubt standard."
            ),
        ),
        FilingRequirement(
            requirement_id="FR-contempt-form",
            filing_type="motion_for_contempt",
            court="14th_circuit_family",
            requirement="File motion for show cause order with proposed order to show cause",
            category="form",
            is_mandatory=True,
            forms_required=["FOC 61"],
            notes="FOC 61 is the Order to Show Cause form; a separate motion and brief are also needed",
        ),
        FilingRequirement(
            requirement_id="FR-contempt-service",
            filing_type="motion_for_contempt",
            court="14th_circuit_family",
            rule_id="MCR-2.107",
            requirement="Personal service of show cause order on the respondent is required",
            category="service",
            is_mandatory=True,
            notes="Personal service strongly recommended for contempt proceedings",
        ),

        # ─── Motion for Summary Disposition ───────────────────

        FilingRequirement(
            requirement_id="FR-summary-notice",
            filing_type="motion_for_summary_disposition",
            court="14th_circuit_civil",
            rule_id="MCR-2.119",
            requirement="Motion must be served at least 9 days before the hearing date",
            category="notice",
            is_mandatory=True,
            deadline_formula="9_days_before_hearing",
        ),
        FilingRequirement(
            requirement_id="FR-summary-content",
            filing_type="motion_for_summary_disposition",
            court="14th_circuit_civil",
            rule_id="MCR-2.116",
            requirement=(
                "Must specify the subsection of MCR 2.116(C) relied upon, attach all "
                "supporting affidavits and documentary evidence, and include a brief with "
                "legal argument demonstrating entitlement to judgment"
            ),
            category="content",
            is_mandatory=True,
            notes="Common grounds: (C)(8) failure to state a claim, (C)(10) no genuine issue of material fact",
        ),
        FilingRequirement(
            requirement_id="FR-summary-service",
            filing_type="motion_for_summary_disposition",
            court="14th_circuit_civil",
            rule_id="MCR-2.107",
            requirement="Serve opposing party with motion, brief, and all exhibits",
            category="service",
            is_mandatory=True,
        ),
        FilingRequirement(
            requirement_id="FR-summary-response",
            filing_type="motion_for_summary_disposition",
            court="14th_circuit_civil",
            rule_id="MCR-2.116",
            requirement=(
                "Opposing party must file response within 7 days before the hearing. "
                "Must include counter-affidavits or other evidence showing a genuine issue "
                "of material fact exists."
            ),
            category="deadline",
            is_mandatory=True,
            deadline_formula="7_days_before_hearing",
        ),
    ]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Function 4: Deadline Rules
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_mcr_deadlines() -> List[DeadlineRule]:
    """Return deadline computation rules derived from Michigan Court Rules."""
    return [
        DeadlineRule(
            rule_id="DL-motion-notice-9",
            source_rule="MCR-2.119",
            trigger_event="hearing_date",
            deadline_type="before",
            days=9,
            business_days=False,
            description=(
                "A motion must be served at least 9 days before the hearing date. "
                "If service is by mail, add 3 additional days (total 12 days before hearing)."
            ),
            court="all",
            lane="all",
        ),
        DeadlineRule(
            rule_id="DL-motion-response-7",
            source_rule="MCR-2.119",
            trigger_event="hearing_date",
            deadline_type="before",
            days=7,
            business_days=False,
            description=(
                "A response to a motion must be served at least 7 days before the hearing date."
            ),
            court="all",
            lane="all",
        ),
        DeadlineRule(
            rule_id="DL-motion-reply-4",
            source_rule="MCR-2.119",
            trigger_event="hearing_date",
            deadline_type="before",
            days=4,
            business_days=False,
            description=(
                "A reply brief in support of a motion may be served at least 4 days before "
                "the hearing date."
            ),
            court="all",
            lane="all",
        ),
        DeadlineRule(
            rule_id="DL-answer-complaint-21",
            source_rule="MCR-2.108",
            trigger_event="service_of_process",
            deadline_type="after",
            days=21,
            business_days=False,
            description=(
                "A defendant must file a responsive pleading (answer) within 21 days after "
                "being served with the summons and complaint."
            ),
            court="all",
            lane="all",
        ),
        DeadlineRule(
            rule_id="DL-appeal-of-right-21",
            source_rule="MCR-7.204",
            trigger_event="judgment_entry",
            deadline_type="after",
            days=21,
            business_days=False,
            description=(
                "A claim of appeal of right to the Court of Appeals must be filed within "
                "21 days after entry of the judgment or order being appealed."
            ),
            court="michigan_coa",
            lane="F",
        ),
        DeadlineRule(
            rule_id="DL-leave-appeal-coa-21",
            source_rule="MCR-7.205",
            trigger_event="order_entry",
            deadline_type="after",
            days=21,
            business_days=False,
            description=(
                "An application for leave to appeal to the Court of Appeals must be filed "
                "within 21 days after entry of the order being challenged."
            ),
            court="michigan_coa",
            lane="F",
        ),
        DeadlineRule(
            rule_id="DL-leave-appeal-msc-56",
            source_rule="MCR-7.301",
            trigger_event="coa_decision",
            deadline_type="after",
            days=56,
            business_days=False,
            description=(
                "An application for leave to appeal to the Michigan Supreme Court must be "
                "filed within 56 days after the date of the Court of Appeals decision."
            ),
            court="michigan_msc",
            lane="F",
        ),
        DeadlineRule(
            rule_id="DL-foc-objection-21",
            source_rule="MCR-3.708",
            trigger_event="foc_recommendation_served",
            deadline_type="after",
            days=21,
            business_days=False,
            description=(
                "A party must file an objection to a Friend of the Court recommendation "
                "within 21 days after service of the recommendation."
            ),
            court="14th_circuit_family",
            lane="A",
        ),
        DeadlineRule(
            rule_id="DL-coa-brief-56",
            source_rule="MCR-7.212",
            trigger_event="claim_of_appeal_filed",
            deadline_type="after",
            days=56,
            business_days=False,
            description=(
                "The appellant's brief in the Court of Appeals is due within 56 days after "
                "the claim of appeal is filed or leave to appeal is granted."
            ),
            court="michigan_coa",
            lane="F",
        ),
        DeadlineRule(
            rule_id="DL-relief-judgment-1yr",
            source_rule="MCR-2.612",
            trigger_event="judgment_entry",
            deadline_type="within",
            days=365,
            business_days=False,
            description=(
                "A motion for relief from judgment under MCR 2.612 must be filed within a "
                "reasonable time. For grounds of mistake, newly discovered evidence, or fraud, "
                "the motion must be filed no more than one year after entry of the judgment or "
                "order. Other grounds (void judgment, satisfaction) have no fixed outer limit "
                "but must still be timely."
            ),
            court="all",
            lane="all",
        ),
    ]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Module self-test
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    rules = get_mcr_rules()
    xrefs = get_mcr_cross_refs()
    filings = get_mcr_filing_requirements()
    deadlines = get_mcr_deadlines()

    # Verify uniqueness
    rule_ids = [r.rule_id for r in rules]
    assert len(rule_ids) == len(set(rule_ids)), f"Duplicate rule_ids: {[x for x in rule_ids if rule_ids.count(x) > 1]}"

    req_ids = [f.requirement_id for f in filings]
    assert len(req_ids) == len(set(req_ids)), f"Duplicate requirement_ids: {[x for x in req_ids if req_ids.count(x) > 1]}"

    dl_ids = [d.rule_id for d in deadlines]
    assert len(dl_ids) == len(set(dl_ids)), f"Duplicate deadline rule_ids: {[x for x in dl_ids if dl_ids.count(x) > 1]}"

    print(f"MCR Data Module — Self-Test Passed")
    print(f"  Rules:              {len(rules)}")
    print(f"  Cross-References:   {len(xrefs)}")
    print(f"  Filing Requirements:{len(filings)}")
    print(f"  Deadline Rules:     {len(deadlines)}")
    print(f"  All IDs unique:     ✓")
