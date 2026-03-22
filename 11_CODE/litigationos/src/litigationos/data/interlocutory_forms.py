"""Interlocutory Appeal Form Suite — COA filings before final judgment.

Complete registry of Michigan Court of Appeals interlocutory appeal forms,
MCR 7.200-series rules, deadline calculators, eligibility assessments, and
stay-analysis tools.  Designed for Pigors v Watson (Case 2024-001507-DC),
14th Circuit Court to Michigan Court of Appeals.

Interlocutory appeals allow review of non-final trial court orders when
waiting for a final judgment would cause irreparable harm or the order
involves a controlling question of law.

Sources:
  - Michigan Court Rules MCR 7.202, 7.203, 7.205, 7.209, 7.211, 7.215
  - courts.michigan.gov/courts/coa — March 2026
  - Michigan Court of Appeals Internal Operating Procedures

Local-only module — no network calls, no API dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any


# =========================================================================
# Data classes
# =========================================================================

@dataclass(frozen=True)
class InterlocutoryForm:
    """Immutable descriptor for a Michigan COA interlocutory appeal form."""

    form_id: str
    title: str
    category: str
    mcr_rule: str
    description: str
    filing_fee: str
    page_limit: int | None
    deadline_days: int | None
    deadline_basis: str
    required_contents: list[str]
    efiling: bool = True
    service_required: bool = True
    copies_required: int = 1
    fee_waiver_form: str = "MC 20"
    practice_tips: str = ""
    pigors_relevance: str = ""
    filing_use: list[str] = field(default_factory=lambda: ["F10"])

    def to_dict(self) -> dict[str, Any]:
        """Serialize to plain dictionary for JSON/DB compatibility."""
        return {
            "form_id": self.form_id,
            "title": self.title,
            "category": self.category,
            "mcr_rule": self.mcr_rule,
            "description": self.description,
            "filing_fee": self.filing_fee,
            "page_limit": self.page_limit,
            "deadline_days": self.deadline_days,
            "deadline_basis": self.deadline_basis,
            "required_contents": list(self.required_contents),
            "efiling": self.efiling,
            "service_required": self.service_required,
            "copies_required": self.copies_required,
            "fee_waiver_form": self.fee_waiver_form,
            "practice_tips": self.practice_tips,
            "pigors_relevance": self.pigors_relevance,
            "filing_use": list(self.filing_use),
        }


# =========================================================================
# INTERLOCUTORY FORM REGISTRY
# =========================================================================

INTERLOCUTORY_FORMS: list[InterlocutoryForm] = [
    # ----- Application for Leave to Appeal (MCR 7.205) ------------------
    InterlocutoryForm(
        form_id="COA-LEAVE",
        title="Application for Leave to Appeal",
        category="Application",
        mcr_rule="MCR 7.205",
        description=(
            "Requests the Court of Appeals to exercise discretionary "
            "jurisdiction over a non-final trial court order.  This is "
            "the primary vehicle for interlocutory appeals when no appeal "
            "of right exists.  The applicant must show that review is needed "
            "to prevent irreparable harm, involves a controlling question of "
            "law on which there is substantial ground for difference of "
            "opinion, or that immediate appeal would materially advance the "
            "ultimate termination of the litigation."
        ),
        filing_fee="$375.00",
        page_limit=50,
        deadline_days=21,
        deadline_basis="Date of entry of the order being appealed",
        required_contents=[
            "Statement of jurisdiction — why COA has authority to hear this "
            "interlocutory appeal",
            "Statement of the questions presented",
            "Statement of facts material to the questions presented",
            "Argument in support — why leave should be granted",
            "Copy of the order being appealed (attached as exhibit)",
            "Copy of any opinion or findings of the trial court",
            "Proof of service on all parties",
            "Certificate of compliance with page/word limits",
            "Filing fee ($375) or fee waiver request (MC 20)",
        ],
        practice_tips=(
            "The 21-day deadline is jurisdictional — late applications are "
            "rejected.  Focus on WHY interlocutory review is necessary now: "
            "irreparable harm if review is delayed, controlling question of "
            "law, or material advancement of the case.  The COA grants leave "
            "in roughly 15-20% of applications.  Pair with a Motion for "
            "Immediate Consideration if urgency exists.  The trial court "
            "order being appealed must be attached as an exhibit."
        ),
        pigors_relevance=(
            "Primary vehicle for challenging McNeill's interlocutory orders "
            "— parenting time suspensions, mental health evaluations, custody "
            "modifications — before a final judgment.  The 21-day clock "
            "starts on entry of each order."
        ),
    ),

    # ----- Emergency Application for Leave to Appeal --------------------
    InterlocutoryForm(
        form_id="COA-EMERGENCY-LEAVE",
        title="Emergency Application for Leave to Appeal",
        category="Application",
        mcr_rule="MCR 7.205",
        description=(
            "An expedited application for leave to appeal filed when the "
            "standard briefing timeline would result in irreparable harm.  "
            "Must be accompanied by a Motion for Immediate Consideration "
            "under MCR 7.211(C)(6).  The COA may decide the application on "
            "an expedited basis without waiting for a response."
        ),
        filing_fee="$375.00",
        page_limit=50,
        deadline_days=21,
        deadline_basis="Date of entry of the order being appealed",
        required_contents=[
            "Application for Leave to Appeal (standard requirements)",
            "Motion for Immediate Consideration (MCR 7.211(C)(6))",
            "Affidavit or verified statement of emergency facts",
            "Explanation of irreparable harm if standard timeline is followed",
            "Statement of efforts to obtain relief in the trial court",
            "Copy of the order being appealed",
            "Copy of any emergency motion filed in the trial court",
            "Proof of service on all parties (or explanation of inability "
            "to serve before filing)",
            "Proposed order",
            "Filing fee ($375) or fee waiver request (MC 20)",
        ],
        practice_tips=(
            "File the application and the Motion for Immediate Consideration "
            "simultaneously.  Call the COA Clerk's Office at (517) 373-0786 "
            "to notify them of the emergency filing.  Include specific, "
            "time-sensitive facts — e.g., imminent incarceration, scheduled "
            "custody transfer, child safety risk.  The COA may issue a "
            "temporary stay or order on the same day.  Always demonstrate "
            "that relief was first sought in the trial court."
        ),
        pigors_relevance=(
            "Critical if McNeill issues an order requiring immediate "
            "compliance (e.g., contempt commitment, emergency custody "
            "transfer) that would cause irreparable harm to Andrew or "
            "L.D.W. before normal appellate review."
        ),
    ),

    # ----- Motion for Immediate Consideration ---------------------------
    InterlocutoryForm(
        form_id="COA-IMMEDIATE",
        title="Motion for Immediate Consideration",
        category="Motion",
        mcr_rule="MCR 7.211(C)(6)",
        description=(
            "Requests the Court of Appeals to expedite consideration of a "
            "pending application, motion, or appeal.  Must demonstrate "
            "that delay will cause irreparable harm, safety risk, or that "
            "the matter involves an issue of significant public importance "
            "requiring urgent resolution.  Filed alongside the substantive "
            "application or motion."
        ),
        filing_fee="None (filed with pending application or motion)",
        page_limit=5,
        deadline_days=None,
        deadline_basis="Filed concurrently with the substantive motion or application",
        required_contents=[
            "Statement of the specific emergency or urgency",
            "Facts establishing irreparable harm from delay",
            "Statement of relief sought in the underlying motion/application",
            "Statement of efforts to obtain relief in the trial court",
            "Proposed expedited briefing schedule",
            "Proof of service (or explanation of impossibility)",
        ],
        practice_tips=(
            "Keep the motion short and factual — 5 pages max.  Lead with "
            "the time-sensitive fact (hearing date, incarceration date, "
            "custody transfer deadline).  The COA may act within 24-48 "
            "hours on genuine emergencies.  Always explain what will happen "
            "if the court does NOT act immediately.  If the trial court "
            "refused to grant a stay, say so explicitly."
        ),
        pigors_relevance=(
            "Essential companion to the Emergency Application for Leave.  "
            "Use when McNeill's orders require immediate compliance and "
            "waiting for normal briefing would moot the issue."
        ),
    ),

    # ----- Motion for Stay Pending Appeal -------------------------------
    InterlocutoryForm(
        form_id="COA-STAY",
        title="Motion for Stay Pending Appeal",
        category="Motion",
        mcr_rule="MCR 7.209",
        description=(
            "Requests the Court of Appeals to stay (suspend enforcement of) "
            "a trial court order while the appeal is pending.  The movant "
            "must demonstrate the four-factor test: (1) likelihood of "
            "success on the merits, (2) irreparable harm absent a stay, "
            "(3) balance of equities favours the movant, and (4) the stay "
            "serves the public interest.  Ordinarily, a stay must first be "
            "sought in the trial court under MCR 7.209(A)(1)."
        ),
        filing_fee="None (filed with pending appeal or application)",
        page_limit=20,
        deadline_days=None,
        deadline_basis="Filed after filing the appeal or application for leave",
        required_contents=[
            "Motion for Stay Pending Appeal",
            "Brief addressing the four-factor test in detail",
            "Statement that a stay was first sought in the trial court, "
            "OR explanation of why seeking a stay there would be futile",
            "Copy of the trial court's order denying the stay (if applicable)",
            "Copy of the order sought to be stayed",
            "Affidavit or verified statement of facts supporting irreparable harm",
            "Proposed order granting the stay",
            "Proof of service on all parties",
        ],
        practice_tips=(
            "The COA almost always requires you to seek a stay from the "
            "trial court first — MCR 7.209(A)(1).  If the trial court "
            "denies the stay, attach that order.  If seeking a trial court "
            "stay is futile (e.g., judge is hostile), explain WHY in detail.  "
            "The four-factor test is conjunctive — address ALL four factors.  "
            "The strongest factor is usually irreparable harm — focus on "
            "what cannot be undone if the order takes effect."
        ),
        pigors_relevance=(
            "Critical for preventing enforcement of harmful orders during "
            "appeal — parenting time suspensions, mandatory psychological "
            "evaluations, contempt sanctions.  McNeill's pattern of hostile "
            "rulings may support a futility argument for bypassing the "
            "trial court stay requirement."
        ),
    ),

    # ----- Motion for Peremptory Reversal --------------------------------
    InterlocutoryForm(
        form_id="COA-PEREMPTORY",
        title="Motion for Peremptory Reversal",
        category="Motion",
        mcr_rule="MCR 7.211(C)(4)",
        description=(
            "Requests that the Court of Appeals summarily reverse the trial "
            "court without full briefing or oral argument because the legal "
            "error is so clear and well-established that extended proceedings "
            "are unnecessary.  The movant must show that the trial court's "
            "decision is clearly erroneous and contrary to controlling "
            "authority.  Governed by MCR 7.215(F)(2) for peremptory "
            "disposition standards."
        ),
        filing_fee="None (filed with pending appeal or application)",
        page_limit=20,
        deadline_days=None,
        deadline_basis="Filed after filing the appeal or application for leave",
        required_contents=[
            "Motion for Peremptory Reversal",
            "Brief demonstrating the legal error is clear and well-established",
            "Citation to controlling authority directly on point",
            "Explanation of why full briefing is unnecessary",
            "Copy of the trial court order to be reversed",
            "Proposed order",
            "Proof of service on all parties",
        ],
        practice_tips=(
            "Peremptory reversal is rare — the COA uses it only when the "
            "error is essentially indisputable.  Best cases: trial court "
            "applied a statute that was already held unconstitutional, "
            "ignored binding published authority directly on point, or "
            "committed a clear jurisdictional error.  Do NOT use this for "
            "fact-intensive disputes or close legal questions.  Pair with "
            "an Application for Leave if the appeal is interlocutory."
        ),
        pigors_relevance=(
            "Potential use if McNeill issues an order that directly "
            "contradicts published COA or MSC authority — e.g., suspending "
            "parenting time without the findings required by statute or "
            "refusing to apply mandatory MCR procedures."
        ),
    ),

    # ----- Bypass Application (Extraordinary Circumstances) ---------------
    InterlocutoryForm(
        form_id="COA-BYPASS",
        title="Bypass Application — Extraordinary Circumstances",
        category="Application",
        mcr_rule="MCR 7.205",
        description=(
            "An application for leave to appeal filed under extraordinary "
            "circumstances that may justify bypassing normal procedural "
            "requirements.  Used when the standard interlocutory appeal "
            "process is inadequate to address the urgency or severity of "
            "the situation — such as imminent incarceration, child safety "
            "emergencies, or systemic due process violations."
        ),
        filing_fee="$375.00",
        page_limit=50,
        deadline_days=21,
        deadline_basis="Date of entry of the order being appealed",
        required_contents=[
            "Application for Leave to Appeal (standard requirements)",
            "Supplemental brief explaining extraordinary circumstances",
            "Affidavit of emergency facts",
            "Timeline showing why normal process is inadequate",
            "All supporting documentation (orders, transcripts, exhibits)",
            "Motion for Immediate Consideration (if time-critical)",
            "Proof of service on all parties",
            "Filing fee ($375) or fee waiver request (MC 20)",
        ],
        practice_tips=(
            "This is not a separate formal filing type — it is a standard "
            "leave application augmented with extraordinary-circumstances "
            "arguments.  The key is demonstrating that the harm is "
            "irreparable AND imminent, and that ordinary interlocutory "
            "review timelines would render relief meaningless.  Include a "
            "detailed factual chronology showing escalating harm."
        ),
        pigors_relevance=(
            "Use when multiple orders compound to create an emergency — "
            "e.g., parenting time suspension + contempt threat + mandatory "
            "evaluation creates coercive pressure requiring immediate COA "
            "intervention."
        ),
    ),

    # ----- Motion to Expedite -------------------------------------------
    InterlocutoryForm(
        form_id="COA-EXPEDITE",
        title="Motion to Expedite",
        category="Motion",
        mcr_rule="MCR 7.211(C)(6)",
        description=(
            "Requests that the Court of Appeals accelerate the briefing "
            "schedule and decision timeline for a pending appeal or "
            "application.  Unlike the Motion for Immediate Consideration "
            "(which seeks immediate action), this motion asks for a "
            "compressed but orderly schedule — shorter briefing deadlines "
            "and priority in the decisional queue."
        ),
        filing_fee="None (filed with pending appeal or application)",
        page_limit=5,
        deadline_days=None,
        deadline_basis="Filed after the appeal or application is docketed",
        required_contents=[
            "Motion to Expedite",
            "Statement of why expedition is warranted",
            "Proposed expedited briefing schedule with specific dates",
            "Statement of opposing party's position on expedition",
            "Proof of service on all parties",
        ],
        practice_tips=(
            "Less drastic than a Motion for Immediate Consideration — use "
            "when the case needs faster resolution but is not a true "
            "emergency.  Common in custody cases where the child's best "
            "interests are affected by delay.  Propose a specific briefing "
            "schedule (e.g., 14 days for brief, 14 days for response) "
            "rather than leaving it open-ended.  Consult with opposing "
            "counsel first if possible — a stipulated motion is more "
            "likely to be granted."
        ),
        pigors_relevance=(
            "Appropriate when Andrew's appeal involves ongoing deprivation "
            "of parenting time — every week of delay is a week of lost "
            "contact with L.D.W. that cannot be recovered."
        ),
    ),

    # ----- Interlocutory Claim of Appeal (MCR 7.202, 7.203) ---------------
    InterlocutoryForm(
        form_id="COA-CLAIM-INTERLOCUTORY",
        title="Interlocutory Claim of Appeal (Appeal of Right)",
        category="Appeal of Right",
        mcr_rule="MCR 7.203(B)",
        description=(
            "A claim of appeal filed as of right from an interlocutory "
            "order that falls within the statutory or rule-based categories "
            "granting automatic appellate jurisdiction.  Under MCR 7.203(B), "
            "certain interlocutory orders are immediately appealable without "
            "leave — including orders granting a new trial, orders denying "
            "governmental immunity, and orders appointing a receiver.  "
            "Filed under the claim of appeal procedures of MCR 7.204."
        ),
        filing_fee="$375.00",
        page_limit=None,
        deadline_days=21,
        deadline_basis="Date of entry of the qualifying interlocutory order",
        required_contents=[
            "Claim of Appeal (court form or equivalent)",
            "Statement of jurisdiction — citation to MCR 7.203(B) provision "
            "granting appeal of right",
            "Copy of the order being appealed",
            "Designation of the record on appeal",
            "Statement of the issues to be raised",
            "Filing fee ($375) or fee waiver request (MC 20)",
            "Proof of service on all parties and the trial court clerk",
        ],
        practice_tips=(
            "Appeal of right from an interlocutory order is rare in family "
            "law — most interlocutory orders require leave (MCR 7.205).  "
            "Double-check that the specific order type qualifies under "
            "MCR 7.203(B) before filing a claim of appeal.  If the order "
            "does not qualify, file an Application for Leave instead.  "
            "Filing a claim of appeal for a non-qualifying order wastes "
            "time and the filing fee.  The 21-day deadline applies."
        ),
        pigors_relevance=(
            "Limited applicability — most of McNeill's orders in the "
            "custody case are not within the MCR 7.203(B) categories.  "
            "However, if an order involves governmental immunity or other "
            "qualifying provisions, this is the faster path (no need to "
            "persuade the COA to grant leave)."
        ),
    ),
]


# =========================================================================
# Internal lookup index (built once at import time)
# =========================================================================

_FORM_INDEX: dict[str, InterlocutoryForm] = {
    f.form_id: f for f in INTERLOCUTORY_FORMS
}


# =========================================================================
# MCR RULES FOR INTERLOCUTORY APPEALS
# =========================================================================

INTERLOCUTORY_RULES: dict[str, dict[str, Any]] = {
    "MCR 7.203(B)": {
        "title": "Appeals of Right — Interlocutory Orders",
        "summary": (
            "Defines the narrow categories of interlocutory orders that "
            "are immediately appealable as of right to the Court of "
            "Appeals, without needing leave.  Most family law interlocutory "
            "orders do NOT qualify — leave under MCR 7.205 is required."
        ),
        "key_provisions": [
            "Order granting or denying a motion for a new trial",
            "Order granting or denying a motion for summary disposition "
            "under MCR 2.116(C)(8), (9), or (10)",
            "Order denying governmental immunity to a governmental party",
            "Order granting or denying appointment of a receiver",
            "Order in supplementary proceedings under MCR 2.621",
            "Other orders as specifically provided by statute or court rule",
        ],
        "family_law_applicability": (
            "Most custody, parenting time, and support orders are NOT "
            "appealable of right under MCR 7.203(B).  The standard path "
            "for family law interlocutory appeals is an Application for "
            "Leave under MCR 7.205.  An exception may exist if a family "
            "law order also resolves a governmental immunity claim."
        ),
        "pigors_relevance": (
            "McNeill's custody and parenting time orders generally require "
            "leave to appeal (MCR 7.205).  Andrew should verify whether "
            "any specific order falls within the MCR 7.203(B) categories "
            "before deciding between claim of appeal and leave application."
        ),
    },
    "MCR 7.205": {
        "title": "Application for Leave to Appeal",
        "summary": (
            "Governs discretionary interlocutory appeals.  The applicant "
            "must file within 21 days of the order and demonstrate that "
            "interlocutory review is warranted.  The COA has full "
            "discretion to grant or deny leave."
        ),
        "key_provisions": [
            "21-day deadline from entry of the order being appealed",
            "Application must include: statement of facts, questions "
            "presented, and argument for why leave should be granted",
            "A copy of the order being appealed must be attached",
            "Answer due within 21 days of service of the application",
            "The COA may grant or deny leave, or grant leave limited to "
            "specific issues",
            "The COA may treat the application as the brief on appeal",
            "Filing does NOT automatically stay the trial court order",
            "Emergency applications may be filed with a Motion for "
            "Immediate Consideration",
        ],
        "leave_criteria": [
            "The order involves a controlling question of law on which "
            "there is substantial ground for difference of opinion",
            "Immediate appeal may materially advance the ultimate "
            "termination of the litigation",
            "Delay of review would cause irreparable harm",
            "The issue is of significant public importance",
        ],
        "pigors_relevance": (
            "This is Andrew's PRIMARY interlocutory appeal vehicle.  The "
            "21-day deadline runs from EACH appealable order separately.  "
            "For every significant McNeill order, Andrew must assess within "
            "21 days whether interlocutory appeal is warranted."
        ),
    },
    "MCR 7.209": {
        "title": "Stays and Injunctions Pending Appeal",
        "summary": (
            "Governs motions for stay or injunctive relief while an appeal "
            "is pending.  Requires the movant to first seek a stay from "
            "the trial court, and applies a four-factor balancing test."
        ),
        "key_provisions": [
            "Stay must first be sought from the trial court, unless "
            "seeking a stay there would be impracticable",
            "Four-factor test: (1) likelihood of success on the merits, "
            "(2) irreparable harm without the stay, (3) balance of "
            "hardships favours the movant, (4) stay serves public interest",
            "A bond or security may be required as a condition of the stay",
            "The COA may grant a temporary stay pending a ruling on the "
            "stay motion itself",
            "In custody cases, the court considers the best interest of "
            "the child in addition to the four factors",
            "An automatic stay under MCR 7.209(B) applies only to money "
            "judgments — NOT to custody or parenting time orders",
        ],
        "pigors_relevance": (
            "No automatic stay for custody/parenting time orders — Andrew "
            "must affirmatively move for a stay.  The strongest arguments "
            "are irreparable harm (lost parenting time cannot be recovered) "
            "and the best interest of L.D.W. in maintaining the parent-"
            "child relationship during appeal."
        ),
    },
    "MCR 7.211(C)(6)": {
        "title": "Immediate Consideration",
        "summary": (
            "Authorises a motion requesting the Court of Appeals to give "
            "immediate attention to a pending motion or application.  The "
            "movant must demonstrate genuine urgency — that normal "
            "processing time would result in irreparable harm."
        ),
        "key_provisions": [
            "Filed as a separate motion accompanying the substantive "
            "motion or application",
            "Must demonstrate genuine emergency or urgency",
            "The COA may act within 24-48 hours on genuine emergencies",
            "Does not change the substantive standard — only the timeline",
            "The clerk may contact the movant for additional information",
            "Abusive use may result in sanctions",
        ],
        "when_appropriate": [
            "Imminent incarceration from civil contempt",
            "Imminent change in custody that would harm the child",
            "Scheduled hearing that would moot the appeal",
            "Expiration of a deadline that cannot be extended",
            "Risk of irreparable physical or emotional harm to a child",
        ],
        "pigors_relevance": (
            "Essential when McNeill's orders create time-critical harm — "
            "contempt commitment, emergency custody changes, or deadlines "
            "that would moot the appeal if normal processing time applies."
        ),
    },
    "MCR 7.215(F)(2)": {
        "title": "Peremptory Disposition",
        "summary": (
            "Authorises the Court of Appeals to issue a peremptory order "
            "(reversal, affirmance, or other disposition) without full "
            "briefing, oral argument, or an opinion when the result is "
            "so clear that extended proceedings are unnecessary."
        ),
        "key_provisions": [
            "May be initiated by the court sua sponte or by motion",
            "Used when the legal issue is controlled by clearly "
            "applicable authority",
            "No opinion is issued — the order simply cites the controlling "
            "authority and disposes of the case",
            "Either party may request peremptory disposition by motion "
            "under MCR 7.211(C)(4)",
            "The court will not grant peremptory reversal if the facts "
            "are in genuine dispute",
        ],
        "pigors_relevance": (
            "Strongest when McNeill's order directly contradicts published "
            "authority — e.g., failing to make findings required by MCL "
            "722.27 or ignoring mandatory MCR service requirements."
        ),
    },
}


# =========================================================================
# ORDER TYPE → INTERLOCUTORY ELIGIBILITY MAPPING
# =========================================================================

_ELIGIBILITY_MAP: dict[str, dict[str, Any]] = {
    "custody_modification": {
        "label": "Custody Modification Order",
        "appeal_of_right": False,
        "leave_required": True,
        "primary_vehicle": "COA-LEAVE",
        "mcr_basis": "MCR 7.205",
        "strength": "MODERATE",
        "rationale": (
            "Custody modifications are not appealable of right under "
            "MCR 7.203(B).  Leave is required under MCR 7.205.  However, "
            "custody orders that deprive a parent of fundamental rights "
            "are strong candidates for interlocutory review, especially "
            "when the order lacks required findings under MCL 722.27."
        ),
        "recommended_filings": [
            "Application for Leave to Appeal (MCR 7.205)",
            "Motion for Stay Pending Appeal (MCR 7.209)",
        ],
    },
    "parenting_time_suspension": {
        "label": "Parenting Time Suspension Order",
        "appeal_of_right": False,
        "leave_required": True,
        "primary_vehicle": "COA-LEAVE",
        "mcr_basis": "MCR 7.205",
        "strength": "STRONG",
        "rationale": (
            "Suspension of parenting time implicates fundamental parental "
            "rights and causes irreparable harm — lost time with a child "
            "cannot be recovered.  This is one of the strongest bases for "
            "interlocutory leave, especially without an evidentiary hearing "
            "or proper findings.  The COA recognises that delay in review "
            "effectively denies the remedy."
        ),
        "recommended_filings": [
            "Application for Leave to Appeal (MCR 7.205)",
            "Motion for Stay Pending Appeal (MCR 7.209)",
            "Motion for Immediate Consideration (MCR 7.211(C)(6))",
        ],
    },
    "contempt_finding": {
        "label": "Civil Contempt Finding / Sanction",
        "appeal_of_right": False,
        "leave_required": True,
        "primary_vehicle": "COA-EMERGENCY-LEAVE",
        "mcr_basis": "MCR 7.205",
        "strength": "STRONG",
        "rationale": (
            "Civil contempt sanctions — especially incarceration — are "
            "immediately reviewable because the harm is irreparable.  "
            "If the contemnor is jailed or faces imminent jailing, an "
            "emergency application with a Motion for Immediate "
            "Consideration is appropriate.  Due process challenges to "
            "the contempt procedure are particularly strong grounds."
        ),
        "recommended_filings": [
            "Emergency Application for Leave to Appeal",
            "Motion for Immediate Consideration (MCR 7.211(C)(6))",
            "Motion for Stay Pending Appeal (MCR 7.209)",
        ],
    },
    "mental_health_evaluation_order": {
        "label": "Order Requiring Mental Health Evaluation",
        "appeal_of_right": False,
        "leave_required": True,
        "primary_vehicle": "COA-LEAVE",
        "mcr_basis": "MCR 7.205",
        "strength": "MODERATE",
        "rationale": (
            "Orders requiring mental health evaluations can be challenged "
            "interlocutorily if they lack a factual basis, are overly "
            "broad, or are used as a coercive tool rather than a genuine "
            "inquiry.  The argument is strongest when the order conditions "
            "parenting time on compliance, creating de facto suspension."
        ),
        "recommended_filings": [
            "Application for Leave to Appeal (MCR 7.205)",
            "Motion for Stay Pending Appeal if evaluation deadline is imminent",
        ],
    },
    "discovery_order": {
        "label": "Discovery Order (Compelling or Protective)",
        "appeal_of_right": False,
        "leave_required": True,
        "primary_vehicle": "COA-LEAVE",
        "mcr_basis": "MCR 7.205",
        "strength": "WEAK",
        "rationale": (
            "Discovery orders are rarely reviewed interlocutorily — the "
            "COA generally views them as non-final and correctable on "
            "appeal from the final judgment.  Exceptions exist for orders "
            "involving privilege (attorney-client, therapist-patient) or "
            "constitutional rights (Fifth Amendment)."
        ),
        "recommended_filings": [
            "Application for Leave to Appeal (MCR 7.205)",
        ],
    },
    "motion_to_disqualify_judge": {
        "label": "Order Denying Judicial Disqualification",
        "appeal_of_right": False,
        "leave_required": True,
        "primary_vehicle": "COA-LEAVE",
        "mcr_basis": "MCR 7.205",
        "strength": "MODERATE-STRONG",
        "rationale": (
            "Denial of a motion to disqualify under MCR 2.003 is "
            "immediately reviewable by interlocutory leave because the "
            "harm from proceeding before a biased judge is irreparable "
            "and taints all subsequent proceedings.  The COA is receptive "
            "to these applications when the disqualification motion was "
            "properly supported."
        ),
        "recommended_filings": [
            "Application for Leave to Appeal (MCR 7.205)",
            "Motion for Stay Pending Appeal (MCR 7.209)",
        ],
    },
    "support_order": {
        "label": "Child Support or Spousal Support Order",
        "appeal_of_right": False,
        "leave_required": True,
        "primary_vehicle": "COA-LEAVE",
        "mcr_basis": "MCR 7.205",
        "strength": "WEAK",
        "rationale": (
            "Support orders are generally not strong candidates for "
            "interlocutory appeal because the harm is financial (not "
            "irreparable) and can be corrected retroactively on appeal "
            "from the final judgment.  An exception exists if the order "
            "creates an impossible compliance requirement that triggers "
            "contempt exposure."
        ),
        "recommended_filings": [
            "Application for Leave to Appeal (MCR 7.205)",
        ],
    },
    "protective_order_ppo": {
        "label": "Personal Protection Order / Restraining Order",
        "appeal_of_right": False,
        "leave_required": True,
        "primary_vehicle": "COA-LEAVE",
        "mcr_basis": "MCR 7.205",
        "strength": "MODERATE-STRONG",
        "rationale": (
            "PPOs restrict fundamental liberties (speech, movement, "
            "association) and are strong candidates for interlocutory "
            "review when issued without proper procedural safeguards "
            "or factual basis.  The 14-day period for MCR 3.707 hearing "
            "requests creates urgency."
        ),
        "recommended_filings": [
            "Application for Leave to Appeal (MCR 7.205)",
            "Motion for Immediate Consideration (MCR 7.211(C)(6))",
            "Motion for Stay Pending Appeal (MCR 7.209)",
        ],
    },
    "new_trial_order": {
        "label": "Order Granting or Denying New Trial",
        "appeal_of_right": True,
        "leave_required": False,
        "primary_vehicle": "COA-CLAIM-INTERLOCUTORY",
        "mcr_basis": "MCR 7.203(B)",
        "strength": "STRONG",
        "rationale": (
            "Orders granting or denying a new trial are among the "
            "enumerated interlocutory orders appealable of right under "
            "MCR 7.203(B).  No leave is required — file a claim of appeal."
        ),
        "recommended_filings": [
            "Claim of Appeal (MCR 7.204)",
        ],
    },
    "summary_disposition": {
        "label": "Order Granting/Denying Summary Disposition",
        "appeal_of_right": True,
        "leave_required": False,
        "primary_vehicle": "COA-CLAIM-INTERLOCUTORY",
        "mcr_basis": "MCR 7.203(B)",
        "strength": "STRONG",
        "rationale": (
            "Certain summary disposition orders under MCR 2.116(C)(8), "
            "(9), or (10) are appealable of right under MCR 7.203(B).  "
            "No leave is required.  File a claim of appeal within 21 days."
        ),
        "recommended_filings": [
            "Claim of Appeal (MCR 7.204)",
        ],
    },
}


# =========================================================================
# EMERGENCY CRITERIA
# =========================================================================

_EMERGENCY_CRITERIA: dict[str, Any] = {
    "overview": (
        "An emergency application for leave to appeal is appropriate when "
        "the standard 21-day application + response + decision timeline "
        "would render relief meaningless.  The COA considers the following "
        "criteria when deciding whether to give immediate attention."
    ),
    "criteria": [
        {
            "criterion": "imminent_incarceration",
            "label": "Imminent Incarceration from Civil Contempt",
            "severity": "CRITICAL",
            "description": (
                "The appellant faces imminent jailing from a civil contempt "
                "order.  This is the highest-priority emergency because "
                "incarceration cannot be undone retroactively."
            ),
            "pigors_application": (
                "If McNeill issues a contempt commitment order based on "
                "Andrew's non-compliance with conditions he cannot meet, "
                "this criterion is satisfied."
            ),
        },
        {
            "criterion": "imminent_custody_change",
            "label": "Imminent Change in Physical Custody",
            "severity": "CRITICAL",
            "description": (
                "An order transfers physical custody or suspends all "
                "parenting time effective immediately or within days.  "
                "The disruption to the child and parent-child bond is "
                "irreparable."
            ),
            "pigors_application": (
                "Any order further restricting or eliminating Andrew's "
                "contact with L.D.W. warrants emergency treatment."
            ),
        },
        {
            "criterion": "child_safety_risk",
            "label": "Immediate Risk to Child Safety",
            "severity": "CRITICAL",
            "description": (
                "Evidence that the child faces imminent physical or "
                "emotional harm in the current custodial arrangement.  "
                "The COA prioritises child safety above all other factors."
            ),
        },
        {
            "criterion": "mootness_risk",
            "label": "Appeal Would Become Moot",
            "severity": "HIGH",
            "description": (
                "A scheduled hearing, deadline, or event will occur before "
                "normal appellate review, rendering the appeal moot.  "
                "The COA recognises that some orders self-execute before "
                "review is possible without expedition."
            ),
        },
        {
            "criterion": "constitutional_deprivation",
            "label": "Ongoing Constitutional Deprivation",
            "severity": "HIGH",
            "description": (
                "A fundamental constitutional right (parental rights, "
                "liberty, due process) is being continuously violated "
                "while the appeal is pending.  Each day without review "
                "compounds the deprivation."
            ),
            "pigors_application": (
                "Andrew's parental rights as fundamental constitutional "
                "rights are being deprived every day that parenting time "
                "is suspended — Troxel v Granville, 530 U.S. 57 (2000)."
            ),
        },
        {
            "criterion": "compliance_deadline",
            "label": "Imminent Compliance Deadline with Severe Consequences",
            "severity": "MODERATE",
            "description": (
                "An order requires compliance by a specific date, and "
                "non-compliance triggers severe sanctions (contempt, "
                "default, loss of rights).  Review must occur before "
                "the compliance deadline."
            ),
        },
    ],
    "filing_procedure": [
        "File the Application for Leave to Appeal (MCR 7.205)",
        "File the Motion for Immediate Consideration (MCR 7.211(C)(6)) "
        "simultaneously",
        "Include an Affidavit or Verified Statement of Emergency Facts",
        "Call the COA Clerk's Office at (517) 373-0786 to notify staff",
        "Serve all parties immediately — explain any inability to serve "
        "before filing in the motion",
        "If seeking a stay, file the Motion for Stay (MCR 7.209) at the "
        "same time",
    ],
    "timing_notes": (
        "The COA can act within 24-48 hours on genuine emergencies.  "
        "Filing early in the day maximises the chance of same-day action.  "
        "If the emergency arises after business hours, file electronically "
        "and call the Clerk's Office first thing the next morning."
    ),
}


# =========================================================================
# STAY REQUIREMENTS (four-factor test)
# =========================================================================

_STAY_FACTORS: dict[str, Any] = {
    "overview": (
        "A stay pending appeal under MCR 7.209 requires the movant to "
        "demonstrate all four factors of the balancing test.  In custody "
        "cases, the court also considers the best interest of the child.  "
        "The movant bears the burden on all factors."
    ),
    "factors": [
        {
            "factor": "likelihood_of_success",
            "label": "Likelihood of Success on the Merits",
            "description": (
                "The movant must show a strong likelihood of prevailing on "
                "appeal.  This does not require certainty — a substantial "
                "question of law or a clearly erroneous factual finding "
                "may suffice.  The court examines the strength of the legal "
                "arguments and whether controlling authority supports reversal."
            ),
            "analysis_questions": [
                "Does the trial court order contradict published authority?",
                "Did the trial court apply the wrong legal standard?",
                "Are the required findings absent or clearly erroneous?",
                "Is there a substantial question of law that the COA is "
                "likely to resolve in the movant's favour?",
            ],
            "pigors_application": (
                "Andrew should identify the specific legal error — e.g., "
                "suspension without MCL 722.27a findings, denial of due "
                "process, ex parte proceedings — and cite controlling "
                "authority that the trial court ignored or misapplied."
            ),
        },
        {
            "factor": "irreparable_harm",
            "label": "Irreparable Harm Absent a Stay",
            "description": (
                "The movant must show that enforcement of the order during "
                "appeal will cause harm that cannot be adequately remedied "
                "if the appeal succeeds.  In family law, lost parenting "
                "time is the quintessential irreparable harm — no court "
                "order can restore missed days with a child."
            ),
            "analysis_questions": [
                "Will enforcement cause loss of parenting time?",
                "Is there a risk of incarceration?",
                "Will the parent-child bond be damaged by continued "
                "separation?",
                "Can the harm be remedied by a money judgment or future "
                "modification?",
                "Will the child's developmental milestones be missed?",
            ],
            "pigors_application": (
                "Andrew's strongest factor.  Every day of suspended "
                "parenting time is a day lost with L.D.W. that no "
                "appellate reversal can restore.  Cite developmental "
                "psychology research on the importance of consistent "
                "parent-child contact."
            ),
        },
        {
            "factor": "balance_of_equities",
            "label": "Balance of Hardships / Equities",
            "description": (
                "The court weighs the harm to the movant from denial of a "
                "stay against the harm to the opposing party from granting "
                "one.  If the movant's harm is severe and the opposing "
                "party's harm from a stay is minimal, this factor favours "
                "the movant."
            ),
            "analysis_questions": [
                "What harm does the movant face without a stay?",
                "What harm does the opposing party face WITH a stay?",
                "Are there conditions that can mitigate either side's harm?",
                "Can a modified stay address both parties' concerns?",
            ],
            "pigors_application": (
                "Andrew's harm (total loss of parenting time, potential "
                "incarceration) substantially outweighs any harm to Watson "
                "from a stay.  If a stay simply restores status quo "
                "parenting time, Watson is not harmed — L.D.W. benefits "
                "from contact with both parents."
            ),
        },
        {
            "factor": "public_interest",
            "label": "Public Interest",
            "description": (
                "The court considers whether the stay serves the broader "
                "public interest.  In family law cases, this factor often "
                "merges with the child's best interest — the public has an "
                "interest in protecting children and preserving family bonds."
            ),
            "analysis_questions": [
                "Does the public interest favour preserving the parent-"
                "child relationship?",
                "Does the case raise systemic due process concerns that "
                "affect other litigants?",
                "Does the stay serve the child's best interest?",
                "Is there a public interest in ensuring proper legal "
                "procedures were followed?",
            ],
            "pigors_application": (
                "The public interest favours: (1) protecting L.D.W.'s "
                "right to a relationship with both parents, (2) ensuring "
                "due process in family courts, and (3) maintaining judicial "
                "accountability.  Michigan public policy recognises the "
                "importance of both parents in a child's life — MCL 722.23."
            ),
        },
    ],
    "custody_overlay": {
        "label": "Best Interest of the Child (Custody-Specific)",
        "description": (
            "In custody and parenting time cases, the court applies an "
            "additional overlay: the best interest of the child under MCL "
            "722.23.  This factor can independently support or defeat a "
            "stay request, regardless of how the four standard factors "
            "balance out."
        ),
        "analysis_questions": [
            "Is the child better served by maintaining the status quo "
            "during appeal?",
            "Would enforcement of the order disrupt the child's "
            "established routines?",
            "Does the child have a meaningful bond with the movant parent?",
            "Are there safety concerns that the stay must address?",
        ],
    },
    "procedural_requirements": {
        "trial_court_first": (
            "MCR 7.209(A)(1) requires the movant to first seek a stay "
            "from the trial court before requesting one from the COA.  "
            "If the trial court denies the stay, attach that order.  "
            "If seeking a trial court stay would be impracticable, explain "
            "why in the motion to the COA."
        ),
        "bond_or_security": (
            "The court may require the movant to post a bond or other "
            "security as a condition of the stay.  In family law cases, "
            "bond is less common but may be required for financial orders."
        ),
        "temporary_stay": (
            "The COA may grant a temporary stay pending its ruling on "
            "the stay motion.  Request this explicitly if the underlying "
            "order takes effect before the COA can fully brief the stay."
        ),
    },
}


# =========================================================================
# Public API
# =========================================================================


def get_interlocutory_forms() -> dict[str, Any]:
    """Return all interlocutory appeal forms with full metadata.

    Returns
    -------
    dict[str, Any]
        Dictionary with ``forms`` (list of form dicts), ``total_count``,
        and ``categories`` breakdown.
    """
    categories: dict[str, int] = {}
    for form in INTERLOCUTORY_FORMS:
        categories[form.category] = categories.get(form.category, 0) + 1

    return {
        "forms": [f.to_dict() for f in INTERLOCUTORY_FORMS],
        "total_count": len(INTERLOCUTORY_FORMS),
        "categories": categories,
        "source": "Michigan Court Rules — MCR 7.200-series (Interlocutory)",
        "court": "Michigan Court of Appeals",
        "origin_court": "14th Circuit Court — Family Division, Muskegon County",
    }


def get_interlocutory_rules() -> dict[str, dict[str, Any]]:
    """Return MCR rule summaries for interlocutory appeals.

    Returns
    -------
    dict[str, dict[str, Any]]
        Dictionary keyed by rule citation (e.g. ``"MCR 7.205"``), each
        containing ``title``, ``summary``, and ``key_provisions``.
    """
    return INTERLOCUTORY_RULES


def assess_interlocutory_eligibility(order_type: str) -> dict[str, Any]:
    """Assess whether an order type qualifies for interlocutory appeal.

    Parameters
    ----------
    order_type : str
        Type of trial court order, e.g. ``"custody_modification"``,
        ``"parenting_time_suspension"``, ``"contempt_finding"``.
        Case-insensitive; spaces and hyphens normalised to underscores.

    Returns
    -------
    dict[str, Any]
        Assessment with ``appeal_of_right``, ``leave_required``,
        ``primary_vehicle``, ``strength``, ``rationale``, and
        ``recommended_filings``.  If the order type is not recognised,
        returns ``status: "not_found"`` with available types.

    Examples
    --------
    >>> result = assess_interlocutory_eligibility("parenting_time_suspension")
    >>> result["strength"]
    'STRONG'
    """
    key = order_type.strip().lower().replace("-", "_").replace(" ", "_")

    if key in _ELIGIBILITY_MAP:
        entry = _ELIGIBILITY_MAP[key]
        return {
            "order_type": key,
            "status": "found",
            **entry,
        }

    return {
        "order_type": order_type,
        "status": "not_found",
        "available_types": sorted(_ELIGIBILITY_MAP.keys()),
        "default_guidance": (
            "Most interlocutory orders in family law require an Application "
            "for Leave to Appeal under MCR 7.205.  File within 21 days of "
            "the order.  Consider pairing with a Motion for Stay (MCR 7.209) "
            "and/or Motion for Immediate Consideration (MCR 7.211(C)(6)) "
            "depending on urgency."
        ),
    }


def calculate_leave_deadline(order_date: str) -> dict[str, Any]:
    """Calculate the 21-day deadline for filing an interlocutory appeal.

    Parameters
    ----------
    order_date : str
        Date the trial court order was entered, in ``YYYY-MM-DD`` format.

    Returns
    -------
    dict[str, Any]
        Dictionary with ``deadline_date``, ``days_remaining``, ``status``,
        and ``warnings`` for the 21-day leave application deadline.  Also
        includes related deadlines (answer, reply).

    Examples
    --------
    >>> result = calculate_leave_deadline("2025-06-01")
    >>> result["deadlines"]["application_for_leave"]["deadline_days"]
    21
    """
    try:
        order_dt = datetime.strptime(order_date, "%Y-%m-%d").date()
    except ValueError:
        return {
            "error": (
                f"Invalid date format: '{order_date}'. "
                "Use YYYY-MM-DD (e.g. 2025-06-15)."
            ),
        }

    today = datetime.now().date()
    deadlines: dict[str, Any] = {}
    warnings: list[str] = []

    # Primary deadline: 21 days for leave application
    entries: list[tuple[str, int, str]] = [
        (
            "application_for_leave",
            21,
            "Application for Leave to Appeal (MCR 7.205)",
        ),
        (
            "claim_of_appeal",
            21,
            "Claim of Appeal — if order qualifies under MCR 7.203(B)",
        ),
    ]

    for key, days, label in entries:
        deadline_date = order_dt + timedelta(days=days)
        days_remaining = (deadline_date - today).days

        if days_remaining < 0:
            status = "EXPIRED"
            warnings.append(
                f"\u26a0 {label} deadline EXPIRED {abs(days_remaining)} day(s) ago."
            )
        elif days_remaining <= 3:
            status = "CRITICAL"
            warnings.append(
                f"\U0001f534 {label} deadline is CRITICAL — {days_remaining} day(s) left!"
            )
        elif days_remaining <= 7:
            status = "IMMINENT"
            warnings.append(
                f"\U0001f534 {label} deadline is IMMINENT — {days_remaining} day(s) left."
            )
        elif days_remaining <= 14:
            status = "APPROACHING"
        else:
            status = "OK"

        deadlines[key] = {
            "label": label,
            "deadline_days": days,
            "deadline_date": deadline_date.isoformat(),
            "days_remaining": days_remaining,
            "status": status,
        }

    # Derived deadlines (depend on service, not order date)
    deadlines["answer_to_application"] = {
        "label": "Answer in Opposition (MCR 7.205(E))",
        "deadline_rule": "21 days after SERVICE of the application",
        "note": "Cannot compute without service date — track manually.",
    }
    deadlines["reply_to_answer"] = {
        "label": "Reply to Answer",
        "deadline_rule": "7 days after service of the answer (if permitted)",
        "note": "Replies are not automatically permitted — check local rules.",
    }
    deadlines["stay_motion"] = {
        "label": "Motion for Stay Pending Appeal (MCR 7.209)",
        "deadline_rule": "File as soon as possible after filing the appeal",
        "note": (
            "No fixed deadline, but delay weakens the argument for "
            "irreparable harm.  File simultaneously with the leave "
            "application if possible."
        ),
    }

    return {
        "order_date": order_date,
        "computed_as_of": today.isoformat(),
        "deadlines": deadlines,
        "warnings": warnings,
        "critical_note": (
            "The 21-day deadline under MCR 7.205 is JURISDICTIONAL.  "
            "Late applications are rejected — there is no good-cause "
            "exception.  If the deadline has passed, the only option is "
            "to wait for a final judgment and appeal at that time."
        ),
    }


def get_emergency_criteria() -> dict[str, Any]:
    """Return criteria for when an emergency application is appropriate.

    Returns
    -------
    dict[str, Any]
        Dictionary with ``criteria`` list, ``filing_procedure``, and
        ``timing_notes`` for emergency interlocutory appeals.
    """
    return _EMERGENCY_CRITERIA


def get_stay_requirements() -> dict[str, Any]:
    """Return the four-factor stay analysis framework.

    Returns
    -------
    dict[str, Any]
        Dictionary with ``factors`` list (likelihood of success,
        irreparable harm, balance of equities, public interest),
        ``custody_overlay``, and ``procedural_requirements``.
    """
    return _STAY_FACTORS
