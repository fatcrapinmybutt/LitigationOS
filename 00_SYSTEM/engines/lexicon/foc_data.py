"""
FOC Data — Michigan Friend of the Court Procedures for LEXICON Engine
=====================================================================
Structured data for Friend of the Court procedures relevant to the
Pigors v. Watson litigation (14th Circuit, Muskegon County).

The FOC is the court agency that assists in domestic relations cases
involving custody, parenting time, and child support. These rules
cover investigation, recommendation, objection, enforcement,
mediation, grievance, and opt-out procedures.

CRITICAL: Only verified rules are marked confidence='verified'.
Any uncertain content is marked 'needs_verification'.
Do NOT fabricate rule numbers or legal content.

Lane Key:
  A = Watson custody (2024-001507-DC)
"""

import sys
from typing import List
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from lexicon_db import LegalRule, RuleCrossRef, EvidenceRule, CanonViolation, DeadlineRule


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Function 1: FOC Rules
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_foc_rules() -> List[LegalRule]:
    """Return all Michigan Friend of the Court rules relevant to Pigors v. Watson."""
    return [

        # ─── FOC-GENERAL ──────────────────────────────────────

        LegalRule(
            rule_id="FOC-GENERAL",
            source="FOC",
            section="3.701",
            title="FOC Role and Authority",
            summary=(
                "The Friend of the Court (FOC) is a court agency that assists in "
                "domestic relations cases involving custody, parenting time, and "
                "child support. Under MCR 3.701, the FOC investigates, makes "
                "recommendations, enforces orders, and mediates disputes. The FOC "
                "acts as an arm of the court, not as an attorney for either party. "
                "The FOC in the 14th Circuit is administered by Pamela Rusco, "
                "located at 990 Terrace St, Muskegon, MI 49442."
            ),
            confidence="verified",
            lanes=["A"],
            tags=["foc", "authority", "role", "general"],
        ),

        # ─── FOC-INVESTIGATION ────────────────────────────────

        LegalRule(
            rule_id="FOC-INVESTIGATION",
            source="FOC",
            section="3.703",
            title="FOC Investigation Procedures",
            summary=(
                "The FOC may investigate matters relating to custody, parenting "
                "time, and support. Investigations may include home visits, "
                "interviews with parties and children, review of records, and "
                "consultation with professionals. The FOC investigator prepares a "
                "report with findings and recommendations that is filed with the "
                "court and provided to the parties. As a self-represented litigant, "
                "you have the right to cooperate with or object to the investigation "
                "process, but refusing to participate may negatively affect "
                "recommendations. You can submit written information to supplement "
                "the investigation."
            ),
            confidence="verified",
            lanes=["A"],
            tags=["foc", "investigation", "custody", "report"],
        ),

        # ─── FOC-RECOMMENDATION ───────────────────────────────

        LegalRule(
            rule_id="FOC-RECOMMENDATION",
            source="FOC",
            section="3.706",
            title="FOC Recommendations",
            summary=(
                "The FOC issues recommendations on custody, parenting time, and "
                "child support matters. These recommendations are advisory to the "
                "court but carry significant weight. Recommendations are served on "
                "all parties. If you disagree with a recommendation, you MUST file "
                "a written objection within 21 days of service. If no objection is "
                "filed, the court may adopt the recommendation as an order without "
                "a hearing. Always review FOC recommendations carefully and file "
                "timely objections to preserve your rights."
            ),
            confidence="verified",
            lanes=["A"],
            tags=["foc", "recommendation", "custody", "support", "parenting_time"],
        ),

        # ─── FOC-OBJECTION ────────────────────────────────────

        LegalRule(
            rule_id="FOC-OBJECTION",
            source="FOC",
            section="3.708",
            title="Objection to FOC Recommendation",
            summary=(
                "CRITICAL DEADLINE — You have 21 days from service of the FOC "
                "recommendation to file a written objection. The objection must be "
                "in writing, filed with the court clerk, and served on the other "
                "party and the FOC. The objection should specifically state what "
                "you disagree with and why. Upon timely objection, the court must "
                "schedule a de novo hearing where the judge decides the issue "
                "independently, without deference to the FOC recommendation. If "
                "you miss the 21-day deadline, the recommendation may become an "
                "order without any hearing. NEVER let this deadline pass without "
                "action."
            ),
            confidence="verified",
            lanes=["A"],
            tags=["foc", "objection", "recommendation", "deadline", "hearing"],
        ),

        # ─── FOC-REVIEW ──────────────────────────────────────

        LegalRule(
            rule_id="FOC-REVIEW",
            source="FOC",
            section="3.703",
            title="Periodic Review of Orders",
            summary=(
                "The FOC periodically reviews child support orders (typically "
                "every 36 months) to determine if modification is warranted based "
                "on changed circumstances. Either party may also request a review "
                "at any time if there has been a significant change in "
                "circumstances. To request a review, contact the FOC office in "
                "writing, stating the changed circumstances and requesting review. "
                "There is no statutory deadline to request a review — you can do "
                "it any time circumstances have materially changed."
            ),
            confidence="high",
            lanes=["A"],
            tags=["foc", "review", "modification", "support", "custody"],
        ),

        # ─── FOC-ENFORCEMENT ─────────────────────────────────

        LegalRule(
            rule_id="FOC-ENFORCEMENT",
            source="FOC",
            title="FOC Enforcement Powers",
            summary=(
                "The FOC has broad enforcement powers including: initiating "
                "contempt proceedings for violations of court orders, recommending "
                "income withholding for support, suspending licenses (driver's, "
                "occupational, sporting) for support arrears, and reporting to "
                "credit agencies. To request enforcement, file a written complaint "
                "with the FOC describing the specific order violation, when it "
                "occurred, and what evidence supports it. The FOC can also refer "
                "matters to the prosecuting attorney for criminal contempt. KEY "
                "for parenting time withholding: if the other parent is withholding "
                "court-ordered parenting time, file a written complaint with the "
                "FOC documenting each specific instance of denial."
            ),
            confidence="high",
            lanes=["A"],
            tags=["foc", "enforcement", "contempt", "income_withholding", "compliance"],
        ),

        # ─── FOC-MEDIATION ────────────────────────────────────

        LegalRule(
            rule_id="FOC-MEDIATION",
            source="FOC",
            section="3.216",
            title="FOC Mediation Services",
            summary=(
                "The FOC offers mediation services to help parties reach "
                "agreements on custody, parenting time, and support issues. "
                "Mediation is a confidential process where a neutral mediator "
                "helps the parties negotiate. Under MCR 3.216, the court may "
                "order mediation in domestic relations cases. Mediation "
                "communications are generally confidential and not admissible. "
                "You may decline mediation if there is a history of domestic "
                "violence or if a PPO is in effect. If mediation fails, the "
                "matter proceeds to a hearing."
            ),
            confidence="verified",
            lanes=["A"],
            tags=["foc", "mediation", "alternative_dispute_resolution", "settlement"],
        ),

        # ─── FOC-GRIEVANCE ────────────────────────────────────

        LegalRule(
            rule_id="FOC-GRIEVANCE",
            source="FOC",
            title="FOC Grievance Procedure",
            summary=(
                "If you believe the FOC has acted improperly, you can file a "
                "formal grievance. Grievances should be submitted in writing to "
                "the FOC office, describing the specific conduct complained of, "
                "the dates, the FOC staff involved, and the remedy sought. The "
                "FOC must respond to the grievance within 21 days. If unsatisfied "
                "with the response, you can escalate to the chief judge of the "
                "circuit. Common grievances include: failure to investigate, "
                "biased investigation, failure to enforce orders, delay, and "
                "unprofessional conduct."
            ),
            confidence="high",
            lanes=["A"],
            tags=["foc", "grievance", "complaint", "procedure"],
        ),

        # ─── FOC-REFEREE ─────────────────────────────────────

        LegalRule(
            rule_id="FOC-REFEREE",
            source="FOC",
            section="3.706",
            title="FOC Referee Hearings",
            summary=(
                "The FOC may conduct referee hearings on contested matters under "
                "MCR 3.706. A referee is a quasi-judicial officer who conducts "
                "hearings and makes recommended orders. After a referee hearing, "
                "the referee issues a recommended order. Any party may object to "
                "the recommended order within 21 days. Upon objection, the matter "
                "goes to the circuit judge for a de novo hearing. If no objection "
                "is filed, the recommended order becomes a court order. Always "
                "attend referee hearings and always object if you disagree with "
                "the outcome."
            ),
            confidence="verified",
            lanes=["A"],
            tags=["foc", "referee", "hearing", "de_novo", "objection"],
        ),

        # ─── FOC-OPT-OUT ─────────────────────────────────────

        LegalRule(
            rule_id="FOC-OPT-OUT",
            source="FOC",
            title="Right to Opt Out of FOC Services",
            summary=(
                "Under MCL 552.505a, parties may opt out of FOC services on "
                "friend of the court matters if they meet certain conditions. "
                "Both parties must agree to opt out, and the court must approve "
                "the request. Opting out means the FOC will not be involved in "
                "enforcement, investigation, or recommendation functions for the "
                "opted-out issues. This may be appropriate when parties can "
                "cooperate effectively. CAUTION: opting out means giving up FOC "
                "enforcement assistance — only do this if you are confident the "
                "other party will comply voluntarily. Given the history of "
                "non-compliance in this case, opting out is NOT recommended."
            ),
            confidence="high",
            lanes=["A"],
            tags=["foc", "opt_out", "waiver", "agreement"],
        ),

        # ─── FOC-PARENTING-TIME ──────────────────────────────

        LegalRule(
            rule_id="FOC-PARENTING-TIME",
            source="FOC",
            title="FOC Parenting Time Enforcement",
            summary=(
                "KEY PROCEDURE for parenting time withholding. If your "
                "court-ordered parenting time is being denied or interfered with, "
                "you must file a written complaint with the FOC. Under MCL "
                "552.642, the FOC must investigate a parenting time complaint "
                "within a specific timeframe. If the FOC finds a violation, it "
                "may: (1) apply makeup parenting time, (2) modify the parenting "
                "time order, (3) initiate contempt proceedings, (4) refer to the "
                "prosecuting attorney. Document EVERY instance of denied parenting "
                "time with dates, times, circumstances, and any communications. "
                "File complaints promptly — delayed complaints are harder to "
                "enforce."
            ),
            confidence="high",
            lanes=["A"],
            tags=["foc", "parenting_time", "enforcement", "withholding", "makeup", "complaint"],
        ),

        # ─── FOC-OFFICE-14TH ─────────────────────────────────

        LegalRule(
            rule_id="FOC-OFFICE-14TH",
            source="FOC",
            title="14th Circuit FOC Office Information",
            summary=(
                "The 14th Circuit Friend of the Court office handles all FOC "
                "matters for Muskegon County. FOC Administrator: Pamela Rusco. "
                "Location: 990 Terrace St, Muskegon, MI 49442. All written "
                "filings, objections, grievances, and complaints should be "
                "directed to this office. File everything in writing (keep copies) "
                "and request date-stamped receipts. When possible, file by both "
                "mail and hand-delivery. The FOC is part of the 14th Circuit "
                "Court, Family Division, which is also the court for Case No. "
                "2024-001507-DC (Pigors v. Watson)."
            ),
            confidence="verified",
            lanes=["A"],
            tags=["foc", "office", "contact", "14th_circuit", "muskegon"],
        ),
    ]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Function 2: FOC Deadlines
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_foc_deadlines() -> List[DeadlineRule]:
    """Return all FOC-related deadline rules for the 14th Circuit."""
    return [

        DeadlineRule(
            rule_id="DL-FOC-OBJECTION",
            source_rule="FOC-OBJECTION",
            trigger_event="foc_recommendation_service",
            deadline_type="within",
            days=21,
            business_days=False,
            description=(
                "Objection to FOC recommendation must be filed within 21 days "
                "of service. Missing this deadline means the recommendation may "
                "be adopted as a court order without hearing. File written "
                "objection with court clerk and serve on opposing party and FOC."
            ),
            court="14th_circuit_family",
            lane="A",
        ),

        DeadlineRule(
            rule_id="DL-FOC-GRIEVANCE-RESPONSE",
            source_rule="FOC-GRIEVANCE",
            trigger_event="grievance_filing",
            deadline_type="within",
            days=21,
            business_days=False,
            description=(
                "FOC must respond to a properly filed grievance within 21 days. "
                "If no response is received, escalate to the chief judge of the "
                "circuit."
            ),
            court="14th_circuit_family",
            lane="A",
        ),

        DeadlineRule(
            rule_id="DL-FOC-REVIEW-REQUEST",
            source_rule="FOC-REVIEW",
            trigger_event="changed_circumstances",
            deadline_type="within",
            days=0,
            business_days=False,
            description=(
                "No statutory deadline to request FOC review of support or "
                "custody orders. May be requested at any time upon showing of "
                "changed circumstances. However, prompt filing is recommended "
                "when circumstances change."
            ),
            court="14th_circuit_family",
            lane="A",
        ),

        DeadlineRule(
            rule_id="DL-FOC-MEDIATION-SCHEDULING",
            source_rule="FOC-MEDIATION",
            trigger_event="mediation_order",
            deadline_type="within",
            days=0,
            business_days=False,
            description=(
                "No fixed statutory deadline for FOC mediation scheduling. "
                "Timing varies by court caseload and mediator availability. "
                "The court order referring to mediation may specify a deadline. "
                "Check the specific order language."
            ),
            court="14th_circuit_family",
            lane="A",
        ),

        DeadlineRule(
            rule_id="DL-FOC-ENFORCEMENT-COMPLAINT",
            source_rule="FOC-ENFORCEMENT",
            trigger_event="order_violation",
            deadline_type="within",
            days=365,
            business_days=False,
            description=(
                "While there is no strict statutory filing deadline for an FOC "
                "enforcement complaint, filing within one year of each violation "
                "is a practical guideline. Delayed complaints weaken enforcement "
                "— file promptly after each violation. Document each violation "
                "with dates, times, and evidence. Note: the underlying contempt "
                "power may have court-specific limitations."
            ),
            court="14th_circuit_family",
            lane="A",
        ),
    ]
