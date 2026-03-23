"""
Canons Data — Michigan Code of Judicial Conduct for LEXICON Engine
===================================================================
Structured data for all 7 Canons of the Michigan Code of Judicial
Conduct, plus JTC complaint violation templates.

CRITICAL: Only verified canons are included. Do NOT fabricate canon
numbers, violation elements, or complaint language.

Lane Key:
  E = Judicial Misconduct / JTC
"""

import sys
from typing import List
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from lexicon_db import LegalRule, RuleCrossRef, EvidenceRule, CanonViolation, DeadlineRule


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Function 1: Michigan Code of Judicial Conduct — 7 Canons
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_canon_rules() -> List[LegalRule]:
    """Return all 7 Canons of the Michigan Code of Judicial Conduct."""
    return [
        # ── Canon 1: Integrity and Independence ──────────────
        LegalRule(
            rule_id="CANON-1",
            source="CANON",
            section="1",
            title="Integrity and Independence of the Judiciary",
            summary=(
                "A judge should uphold the integrity and independence of the "
                "judiciary. Violations include conduct that undermines public "
                "confidence in the judiciary, failing to maintain high standards "
                "of conduct, or acting in a manner that brings the judicial "
                "office into disrepute."
            ),
            confidence="verified",
            lanes=["E"],
            tags=["integrity", "independence", "judiciary", "public_confidence"],
        ),

        # ── Canon 2: Avoiding Impropriety ────────────────────
        LegalRule(
            rule_id="CANON-2",
            source="CANON",
            section="2",
            title="Avoiding Impropriety and Appearance of Impropriety",
            summary=(
                "A judge should avoid impropriety and the appearance of "
                "impropriety in ALL activities. A judge must act at all times "
                "in a manner that promotes public confidence in the integrity "
                "and impartiality of the judiciary. KEY for McNeill situation "
                "— her former partnership at Ladas, Hoopes & McNeill creates "
                "an appearance of impropriety when ruling on cases where "
                "Kenneth Hoopes (Chief Judge, same former firm) would handle "
                "any reassignment after disqualification. The test is whether "
                "a reasonable person would question the judge's impartiality."
            ),
            confidence="verified",
            lanes=["E"],
            tags=["impropriety", "appearance", "public_perception", "conduct"],
        ),

        # ── Canon 3: Impartiality and Diligence ─────────────
        LegalRule(
            rule_id="CANON-3",
            source="CANON",
            section="3",
            title="Performing Duties Impartially and Diligently",
            summary=(
                "A judge should perform the duties of judicial office "
                "impartially and diligently. This includes: giving every "
                "person legally interested the right to be heard; not "
                "initiating, permitting, or considering ex parte "
                "communications; disposing of matters fairly, promptly, and "
                "efficiently; being patient, dignified, and courteous; not "
                "engaging in conduct manifesting bias or prejudice; ensuring "
                "the right to be heard. KEY for bias claims — Canon 3 is the "
                "primary standard for evaluating whether Judge McNeill has "
                "treated parties equally and allowed Andrew to present his "
                "case."
            ),
            confidence="verified",
            lanes=["E"],
            tags=["impartiality", "diligence", "duties", "fairness", "ex_parte", "bias"],
        ),

        # ── Canon 4: Extra-Judicial Activities to Improve Law
        LegalRule(
            rule_id="CANON-4",
            source="CANON",
            section="4",
            title="Extra-Judicial Activities to Improve the Law",
            summary=(
                "A judge may engage in extra-judicial activities to improve "
                "the law, the legal system, and the administration of justice, "
                "subject to the requirements of this Code. A judge may speak, "
                "write, lecture, teach, and participate in other activities "
                "concerning the law, the legal system, and the administration "
                "of justice."
            ),
            confidence="verified",
            lanes=["E"],
            tags=["extra_judicial", "law_improvement", "teaching", "speaking"],
        ),

        # ── Canon 5: Regulating Extra-Judicial Activities ────
        LegalRule(
            rule_id="CANON-5",
            source="CANON",
            section="5",
            title="Regulating Extra-Judicial Activities",
            summary=(
                "A judge should regulate extra-judicial activities to minimize "
                "the risk of conflict with judicial duties. KEY for "
                "Ladas-Hoopes-McNeill firm connection — if McNeill maintains "
                "any financial or professional connection to the former firm, "
                "or if the former partnership creates ongoing conflicts, "
                "Canon 5 is implicated. A judge must not serve as officer, "
                "director, or advisor of a business if it is likely to come "
                "before the court."
            ),
            confidence="verified",
            lanes=["E"],
            tags=["extra_judicial", "conflict", "financial", "business", "fiduciary"],
        ),

        # ── Canon 6: Compensation and Financial Reporting ────
        LegalRule(
            rule_id="CANON-6",
            source="CANON",
            section="6",
            title="Compensation and Financial Reporting",
            summary=(
                "A judge should regularly file reports of compensation "
                "received for law-related and extra-judicial activities. A "
                "judge may receive reasonable compensation for permitted "
                "extra-judicial activities provided it does not appear to a "
                "reasonable person to compromise the judge's integrity."
            ),
            confidence="verified",
            lanes=["E"],
            tags=["compensation", "financial", "reporting", "disclosure"],
        ),

        # ── Canon 7: Political Activity ──────────────────────
        LegalRule(
            rule_id="CANON-7",
            source="CANON",
            section="7",
            title="Refraining from Inappropriate Political Activity",
            summary=(
                "A judge should refrain from political activity inappropriate "
                "to judicial office. Includes restrictions on political "
                "endorsements, campaign conduct, and fundraising."
            ),
            confidence="verified",
            lanes=["E"],
            tags=["political", "campaign", "endorsement", "fundraising"],
        ),
    ]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Function 2: Canon Violation Templates for JTC Complaints
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_canon_violations() -> List[CanonViolation]:
    """Return JTC complaint violation templates for each canon violation type."""
    return [
        # ── CV-1: Appearance of Impropriety (Canon 2) ────────
        CanonViolation(
            violation_id="CV-APPEARANCE-OF-IMPROPRIETY",
            canon_number=2,
            canon_title="Avoiding Impropriety and Appearance of Impropriety",
            violation_type="Appearance of Impropriety",
            elements=[
                "Judge had or has a professional, personal, or financial "
                "relationship that could affect impartiality",
                "A reasonable person, knowing all the circumstances, would "
                "question the judge's ability to be impartial",
                "The relationship or conduct creates the appearance that the "
                "judge's decisions may be influenced by factors other than "
                "the merits",
                "The judge failed to disclose the relationship or recuse "
                "sua sponte",
            ],
            evidence_needed=[
                "Documentation of prior professional relationship (firm "
                "records, bar records, partnership agreements)",
                "Evidence of the relationship between Judge McNeill and "
                "Kenneth Hoopes (Chief Judge) through Ladas, Hoopes & "
                "McNeill",
                "Docket entries showing reassignment procedures that route "
                "through Chief Judge Hoopes",
                "Any continued professional or social connections between "
                "the judge and former firm partners",
                "Public records of the law firm (LARA filings, bar "
                "association records)",
            ],
            complaint_language=(
                "Judge [NAME] previously served as a partner at Ladas, "
                "Hoopes & McNeill alongside Kenneth Hoopes, who currently "
                "serves as Chief Judge of the [COURT]. This prior "
                "professional relationship creates an appearance of "
                "impropriety under Canon 2 of the Michigan Code of Judicial "
                "Conduct, as a reasonable person with knowledge of these "
                "facts would question whether the judge's impartiality is "
                "compromised. This concern is heightened by the fact that "
                "any disqualification motion would be reviewed by Chief "
                "Judge Hoopes, the judge's former law partner, creating a "
                "structural conflict that undermines public confidence in "
                "the judiciary."
            ),
            lane="E",
        ),

        # ── CV-2: Impartiality Failure (Canon 3) ─────────────
        CanonViolation(
            violation_id="CV-IMPARTIALITY-FAILURE",
            canon_number=3,
            canon_title="Performing Duties Impartially and Diligently",
            violation_type="Failure of Impartiality",
            elements=[
                "Judge treated the parties unequally in proceedings",
                "One party was denied the opportunity to be heard or present "
                "evidence while the other was afforded full opportunity",
                "Rulings demonstrate a pattern of favoring one party over "
                "the other without adequate legal basis",
                "The judge's conduct manifested bias or prejudice based on "
                "impermissible factors",
            ],
            evidence_needed=[
                "Hearing transcripts showing unequal treatment (interrupting "
                "one party, extended time for other)",
                "Orders that consistently favor one party without adequate "
                "legal reasoning",
                "Docket entries showing procedural irregularities (ex parte "
                "hearings, hearings without notice)",
                "Pattern analysis of rulings (percentage of motions "
                "granted/denied by party)",
                "Comparison of sanctions or contempt imposed on each party",
            ],
            complaint_language=(
                "Judge [NAME] has demonstrated a pattern of unequal "
                "treatment of the parties in Case No. [CASE_NO]. "
                "Specifically, [PARTY] has been denied the opportunity to "
                "be heard, present evidence, and receive fair consideration "
                "of motions, while the opposing party has been afforded "
                "full procedural protections. This conduct violates Canon 3 "
                "of the Michigan Code of Judicial Conduct, which requires "
                "judges to perform their duties impartially and ensure "
                "every person legally interested has the right to be heard "
                "according to law."
            ),
            lane="E",
        ),

        # ── CV-3: Ex Parte Communication (Canon 3) ───────────
        CanonViolation(
            violation_id="CV-EX-PARTE-COMMUNICATION",
            canon_number=3,
            canon_title="Performing Duties Impartially and Diligently",
            violation_type="Ex Parte Communication",
            elements=[
                "Communication occurred outside the presence of all parties "
                "or their counsel",
                "The communication was substantive (addressed the merits or "
                "procedural aspects of a pending matter)",
                "The judge initiated, permitted, or considered the ex parte "
                "communication",
                "The judge failed to promptly disclose the communication to "
                "all parties and give them opportunity to respond",
            ],
            evidence_needed=[
                "Docket entries showing orders entered without notice of "
                "hearing to all parties",
                "Records of communications between judge's staff and one "
                "party",
                "Evidence of meetings, phone calls, or correspondence not "
                "disclosed to all parties",
                "Orders that reference information not in the record or not "
                "presented at a noticed hearing",
                "Testimony from court staff or witnesses to the "
                "communication",
            ],
            complaint_language=(
                "Judge [NAME] engaged in or permitted ex parte "
                "communications regarding substantive matters in Case No. "
                "[CASE_NO]. On [DATE], [DESCRIPTION OF EX PARTE "
                "COMMUNICATION]. This communication occurred without notice "
                "to [PARTY] and without opportunity to respond, in "
                "violation of Canon 3 of the Michigan Code of Judicial "
                "Conduct, which prohibits a judge from initiating, "
                "permitting, or considering ex parte communications "
                "concerning a pending or impending proceeding."
            ),
            lane="E",
        ),

        # ── CV-4: Failure to Disclose (Canon 3) ──────────────
        CanonViolation(
            violation_id="CV-FAILURE-TO-DISCLOSE",
            canon_number=3,
            canon_title="Performing Duties Impartially and Diligently",
            violation_type="Failure to Disclose Disqualifying Information",
            elements=[
                "The judge possessed knowledge of facts that a reasonable "
                "person would consider relevant to the question of "
                "disqualification",
                "The judge had a duty to disclose these facts to the "
                "parties",
                "The judge failed to disclose the information sua sponte "
                "or upon inquiry",
                "The undisclosed information was material to the question "
                "of the judge's impartiality",
            ],
            evidence_needed=[
                "Evidence of the undisclosed relationship or fact (bar "
                "records, firm history, financial records)",
                "Docket entries showing no disclosure was made on the "
                "record",
                "Hearing transcripts showing no disclosure when "
                "disqualification was raised",
                "Comparison of what was disclosed vs. what should have "
                "been disclosed",
                "Evidence that the judge was aware of the disqualifying "
                "facts",
            ],
            complaint_language=(
                "Judge [NAME] failed to disclose facts relevant to "
                "disqualification in Case No. [CASE_NO]. Specifically, "
                "[DESCRIPTION OF UNDISCLOSED FACTS]. Despite having "
                "knowledge of these facts and a duty to disclose them "
                "under Canon 3 of the Michigan Code of Judicial Conduct, "
                "Judge [NAME] failed to make any disclosure to the "
                "parties, either sua sponte or in response to inquiry, "
                "thereby depriving the parties of the ability to make an "
                "informed decision regarding disqualification."
            ),
            lane="E",
        ),

        # ── CV-5: Failure to Recuse (Canon 3) ────────────────
        CanonViolation(
            violation_id="CV-FAILURE-TO-RECUSE",
            canon_number=3,
            canon_title="Performing Duties Impartially and Diligently",
            violation_type="Failure to Recuse Despite Grounds for Disqualification",
            elements=[
                "Grounds for disqualification existed under MCR 2.003(C)",
                "A motion for disqualification was properly filed under "
                "MCR 2.003(D)",
                "The judge denied the motion without adequate legal basis",
                "The judge continued to preside over the case despite the "
                "existence of disqualifying grounds",
            ],
            evidence_needed=[
                "The disqualification motion and supporting affidavit",
                "The judge's order denying disqualification with (or "
                "without) reasons stated",
                "Evidence supporting each ground for disqualification "
                "cited in the motion",
                "Subsequent rulings by the judge that demonstrate "
                "continued bias or conflict",
                "Chief Judge's ruling on appeal of disqualification "
                "denial (if applicable)",
            ],
            complaint_language=(
                "Judge [NAME] denied a properly filed motion for "
                "disqualification in Case No. [CASE_NO] despite the "
                "existence of grounds for disqualification under MCR "
                "2.003(C). The motion established [GROUNDS], supported by "
                "[EVIDENCE]. Judge [NAME]'s denial of this motion, and "
                "continued participation in the case, violated Canons 2 "
                "and 3 of the Michigan Code of Judicial Conduct, which "
                "require a judge to avoid the appearance of impropriety "
                "and to perform judicial duties impartially."
            ),
            lane="E",
        ),

        # ── CV-6: Bias in Proceedings (Canon 3) ──────────────
        CanonViolation(
            violation_id="CV-BIAS-IN-PROCEEDINGS",
            canon_number=3,
            canon_title="Performing Duties Impartially and Diligently",
            violation_type="Demonstrable Bias in Proceedings",
            elements=[
                "A pattern of rulings consistently adverse to one party "
                "without adequate legal basis",
                "Denial of procedural rights to one party (right to be "
                "heard, present evidence, cross-examine)",
                "Hostile demeanor, tone, or conduct directed at one party "
                "or their position",
                "Application of different standards to similarly situated "
                "parties",
                "Exclusion of evidence favorable to one party while "
                "admitting similar evidence from the other",
            ],
            evidence_needed=[
                "Hearing transcripts showing hostile demeanor, "
                "interruptions, or unequal treatment",
                "Statistical analysis of rulings (motions granted/denied "
                "by party)",
                "Orders denying fundamental procedural rights (right to "
                "present evidence, cross-examine witnesses)",
                "Comparison of how similar requests by each party were "
                "handled",
                "Audio/video recordings of proceedings (if available)",
                "Testimony of observers present at hearings",
            ],
            complaint_language=(
                "Judge [NAME] has demonstrated a pattern of bias against "
                "[PARTY] in Case No. [CASE_NO]. This bias is evidenced "
                "by: [LIST SPECIFIC EXAMPLES OF BIASED CONDUCT]. This "
                "pattern of conduct constitutes a violation of Canon 3 of "
                "the Michigan Code of Judicial Conduct, which requires "
                "judges to perform their duties without bias or prejudice "
                "and to ensure that every person has the right to be "
                "heard. The cumulative effect of these actions demonstrates "
                "that [PARTY] cannot receive a fair proceeding before this "
                "judge."
            ),
            lane="E",
        ),

        # ── CV-7: Professional Relationship Conflict (Canon 2)
        CanonViolation(
            violation_id="CV-PROFESSIONAL-RELATIONSHIP-CONFLICT",
            canon_number=2,
            canon_title="Avoiding Impropriety and Appearance of Impropriety",
            violation_type="Conflict from Prior Professional Association",
            elements=[
                "Judge had a prior professional partnership, employment, "
                "or close professional association with a person whose "
                "impartiality would be relevant",
                "The prior association was significant (not merely casual "
                "acquaintance)",
                "The prior associate is now in a position to affect the "
                "proceedings (e.g., Chief Judge handling reassignment, "
                "opposing counsel, party, or witness)",
                "The judge failed to disclose the prior professional "
                "relationship",
                "A reasonable person would question whether the prior "
                "relationship affects the judge's impartiality or creates "
                "structural conflicts",
            ],
            evidence_needed=[
                "Bar association records showing partnership or employment "
                "at the same firm",
                "Firm letterhead, website archives, or LARA filings "
                "showing the professional association",
                "Duration and nature of the professional relationship",
                "Current role of the former associate (e.g., Chief Judge, "
                "counsel, party)",
                "Evidence of any ongoing personal or professional "
                "connection",
                "Court administrative records showing how the former "
                "associate's current role intersects with the case",
            ],
            complaint_language=(
                "Judge [NAME] has a prior professional association with "
                "[ASSOCIATE NAME], who currently serves as [CURRENT ROLE]. "
                "Judge [NAME] and [ASSOCIATE NAME] were partners at [FIRM "
                "NAME] during [TIME PERIOD]. This prior professional "
                "relationship creates a structural conflict under Canons 2 "
                "and 5 of the Michigan Code of Judicial Conduct, "
                "particularly because [ASSOCIATE NAME]'s current role as "
                "[CURRENT ROLE] directly affects the administration of "
                "this case. A reasonable person, knowing of this prior "
                "partnership, would question whether Judge [NAME]'s "
                "impartiality is compromised and whether the structural "
                "relationship between the judge and [CURRENT ROLE] "
                "undermines the integrity of the proceedings."
            ),
            lane="E",
        ),
    ]
