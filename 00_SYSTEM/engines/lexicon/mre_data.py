"""
MRE Data — Michigan Rules of Evidence for LEXICON Engine
=========================================================
Structured data for Michigan evidentiary rules relevant to the
Pigors v. Watson litigation across 6 case lanes.

Michigan Rules of Evidence (MRE) closely mirror the Federal Rules of
Evidence (FRE) in numbering and substance.  Michigan adopted the
Daubert standard for expert testimony (MRE 702).

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
from typing import List, Dict

sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from lexicon_db import LegalRule, RuleCrossRef, EvidenceRule, CanonViolation, DeadlineRule

ALL_LANES = ["A", "B", "C", "D", "E", "F"]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Function 1: Michigan Rules of Evidence — LegalRule entries
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_mre_rules() -> List[LegalRule]:
    """Return all Michigan Rules of Evidence relevant to the Pigors v. Watson case."""
    return [
        # ─── Article I — General Provisions ──────────────────

        LegalRule(
            rule_id="MRE-101",
            source="MRE",
            chapter="1",
            section="101",
            title="Scope",
            summary=(
                "The Michigan Rules of Evidence govern proceedings in Michigan "
                "courts, including circuit court family division.  They apply to "
                "all stages: motions, hearings, and trials."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["scope", "general"],
        ),
        LegalRule(
            rule_id="MRE-102",
            source="MRE",
            chapter="1",
            section="102",
            title="Purpose and Construction",
            summary=(
                "The rules shall be construed to secure fairness in "
                "administration, eliminate unjustifiable expense and delay, and "
                "promote growth and development of the law of evidence to the "
                "end that the truth may be ascertained and proceedings justly "
                "determined."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["purpose", "construction"],
        ),
        LegalRule(
            rule_id="MRE-103",
            source="MRE",
            chapter="1",
            section="103",
            title="Rulings on Evidence",
            summary=(
                "To preserve error for appeal: (1) if evidence is ADMITTED over "
                "objection — make a timely objection or motion to strike AND "
                "state the specific ground; (2) if evidence is EXCLUDED — make "
                "an offer of proof (state what the evidence would have shown).  "
                "Without proper preservation, appellate review is limited to "
                "plain error.  KEY for Lane F appellate strategy."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["error_preservation", "objection", "offer_of_proof", "appeal"],
        ),
        LegalRule(
            rule_id="MRE-104",
            source="MRE",
            chapter="1",
            section="104",
            title="Preliminary Questions",
            summary=(
                "The court decides preliminary questions concerning the "
                "qualification of a witness, the existence of a privilege, or "
                "the admissibility of evidence.  In making its determination the "
                "court is not bound by the rules of evidence except those with "
                "respect to privileges."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["preliminary", "foundation", "admissibility"],
        ),
        LegalRule(
            rule_id="MRE-106",
            source="MRE",
            chapter="1",
            section="106",
            title="Remainder of or Related Writings or Recorded Statements",
            summary=(
                "Rule of completeness: when an adverse party introduces part of "
                "a writing or recorded statement, any other party may require "
                "the introduction of any other part — or any other writing or "
                "recorded statement — that in fairness ought to be considered "
                "contemporaneously with it.  Use this to prevent cherry-picking."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["completeness", "writings", "fairness"],
        ),

        # ─── Article IV — Relevancy ─────────────────────────

        LegalRule(
            rule_id="MRE-401",
            source="MRE",
            chapter="4",
            section="401",
            title="Definition of Relevant Evidence",
            summary=(
                "Evidence is relevant if it has any tendency to make a fact of "
                "consequence to the determination of the action more probable or "
                "less probable than it would be without the evidence.  Very low "
                "threshold — almost anything with logical bearing qualifies."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["relevance", "definition"],
        ),
        LegalRule(
            rule_id="MRE-402",
            source="MRE",
            chapter="4",
            section="402",
            title="Relevant Evidence Generally Admissible",
            summary=(
                "All relevant evidence is admissible except as otherwise "
                "provided by the Constitution, statutes, these rules, or other "
                "rules adopted by the Supreme Court.  Evidence that is not "
                "relevant is not admissible."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["relevance", "admissibility"],
        ),
        LegalRule(
            rule_id="MRE-403",
            source="MRE",
            chapter="4",
            section="403",
            title="Exclusion of Relevant Evidence on Grounds of Prejudice, Confusion, or Waste of Time",
            summary=(
                "Court MAY exclude relevant evidence if its probative value is "
                "SUBSTANTIALLY outweighed by the danger of unfair prejudice, "
                "confusion of the issues, misleading the jury, undue delay, "
                "waste of time, or needless presentation of cumulative evidence.  "
                "KEY: the bar is 'substantially outweighed' — a high threshold "
                "that favors admission.  Evidence is not excluded merely because "
                "it is prejudicial; it must be UNFAIRLY prejudicial."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["prejudice", "probative_value", "balancing_test", "exclusion"],
        ),
        LegalRule(
            rule_id="MRE-404",
            source="MRE",
            chapter="4",
            section="404",
            title="Character Evidence Not Admissible to Prove Conduct; Exceptions",
            summary=(
                "Evidence of a person's character or character trait is not "
                "admissible to prove that the person acted in conformity with "
                "that character on a particular occasion.  However, character of "
                "a witness may be attacked or supported under MRE 607-609."
            ),
            confidence="verified",
            lanes=["A", "D"],
            tags=["character", "conduct", "propensity"],
        ),
        LegalRule(
            rule_id="MRE-404B",
            source="MRE",
            chapter="4",
            section="404",
            subsection="(b)",
            title="Other Acts Evidence",
            summary=(
                "Evidence of other crimes, wrongs, or acts is NOT admissible to "
                "prove character/propensity, BUT IS admissible for proof of "
                "motive, opportunity, intent, preparation, scheme, plan, "
                "knowledge, identity, or absence of mistake/accident.  KEY: "
                "must identify a proper non-propensity purpose AND the probative "
                "value must not be substantially outweighed by prejudice under "
                "MRE 403.  Use to demonstrate Emily Watson's pattern of false "
                "accusations and weaponized process."
            ),
            confidence="verified",
            lanes=["A", "D"],
            tags=["other_acts", "pattern", "motive", "plan", "scheme"],
        ),
        LegalRule(
            rule_id="MRE-405",
            source="MRE",
            chapter="4",
            section="405",
            title="Methods of Proving Character",
            summary=(
                "When character evidence is admissible, it may be proved by "
                "reputation or opinion testimony.  On cross-examination, inquiry "
                "into relevant specific instances of conduct is allowed.  When "
                "character is an essential element of a claim or defense, proof "
                "may also be made by specific instances."
            ),
            confidence="verified",
            lanes=["A", "D"],
            tags=["character", "reputation", "opinion", "specific_instances"],
        ),
        LegalRule(
            rule_id="MRE-406",
            source="MRE",
            chapter="4",
            section="406",
            title="Habit; Routine Practice",
            summary=(
                "Evidence of a person's habit or an organization's routine "
                "practice is admissible to prove that the conduct of the person "
                "or organization on a particular occasion was in conformity with "
                "the habit or routine practice.  Unlike character evidence, "
                "habit evidence is admissible regardless of whether "
                "corroborating evidence is available."
            ),
            confidence="verified",
            lanes=["A", "D"],
            tags=["habit", "routine", "practice"],
        ),
        LegalRule(
            rule_id="MRE-407",
            source="MRE",
            chapter="4",
            section="407",
            title="Subsequent Remedial Measures",
            summary=(
                "When measures are taken after an event that would have made the "
                "event less likely to occur, evidence of the subsequent measures "
                "is not admissible to prove negligence or culpable conduct.  May "
                "be admissible for other purposes such as ownership, control, or "
                "feasibility of precautionary measures."
            ),
            confidence="verified",
            lanes=["B"],
            tags=["remedial_measures", "repairs", "housing"],
        ),
        LegalRule(
            rule_id="MRE-410",
            source="MRE",
            chapter="4",
            section="410",
            title="Inadmissibility of Pleas, Plea Discussions, and Related Statements",
            summary=(
                "Withdrawn guilty pleas, nolo contendere pleas, and statements "
                "made during plea discussions are generally not admissible "
                "against the defendant who made the plea or participated in the "
                "discussions."
            ),
            confidence="verified",
            lanes=["A"],
            tags=["plea", "criminal", "inadmissible"],
        ),
        LegalRule(
            rule_id="MRE-412",
            source="MRE",
            chapter="4",
            section="412",
            title="Victim's Sexual Behavior or Sexual Predisposition",
            summary=(
                "Michigan's evidentiary rape-shield rule.  In a proceeding "
                "involving alleged sexual misconduct, evidence offered to prove "
                "the victim's past sexual behavior or sexual predisposition is "
                "generally inadmissible, subject to narrow exceptions.  The "
                "statutory counterpart is MCL 750.520j."
            ),
            confidence="verified",
            lanes=["D"],
            tags=["rape_shield", "sexual_behavior", "ppo"],
        ),

        # ─── Article V — Privileges ─────────────────────────

        LegalRule(
            rule_id="MRE-501",
            source="MRE",
            chapter="5",
            section="501",
            title="General Rule of Privilege",
            summary=(
                "Privileges are governed by the common law as interpreted by "
                "Michigan courts in light of reason and experience.  No person "
                "has a privilege to refuse to be a witness, refuse to disclose "
                "any matter, or prevent another from being a witness or "
                "disclosing any matter, except as provided by these rules or "
                "other law."
            ),
            confidence="verified",
            lanes=["A", "D"],
            tags=["privilege", "general"],
        ),
        LegalRule(
            rule_id="MRE-504",
            source="MRE",
            chapter="5",
            section="504",
            title="Husband-Wife Privilege",
            summary=(
                "Spousal privilege protects confidential communications made "
                "during marriage.  NOTE: This privilege does NOT apply in "
                "Pigors v. Watson because Andrew Pigors and Emily Watson were "
                "never married to each other.  Only relevant if a married "
                "witness's spousal communications are at issue."
            ),
            confidence="verified",
            lanes=["A"],
            tags=["privilege", "spousal", "marriage"],
        ),

        # ─── Article VI — Witnesses ─────────────────────────

        LegalRule(
            rule_id="MRE-601",
            source="MRE",
            chapter="6",
            section="601",
            title="General Rule of Competency",
            summary=(
                "Every person is competent to be a witness except as otherwise "
                "provided in these rules.  Michigan has abolished most common-"
                "law incompetency grounds."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["competency", "witness"],
        ),
        LegalRule(
            rule_id="MRE-602",
            source="MRE",
            chapter="6",
            section="602",
            title="Lack of Personal Knowledge",
            summary=(
                "A witness may not testify to a matter unless the witness has "
                "personal knowledge of the matter.  Evidence to prove personal "
                "knowledge may consist of the witness's own testimony.  "
                "Foundation requirement: testimony sufficient to support a "
                "finding that the witness has personal knowledge."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["personal_knowledge", "foundation"],
        ),
        LegalRule(
            rule_id="MRE-607",
            source="MRE",
            chapter="6",
            section="607",
            title="Who May Impeach",
            summary=(
                "The credibility of a witness may be attacked by ANY party, "
                "including the party who called the witness.  This means Andrew "
                "Pigors can impeach his own witnesses if their testimony is "
                "unexpectedly unfavorable."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["impeachment", "credibility"],
        ),
        LegalRule(
            rule_id="MRE-608",
            source="MRE",
            chapter="6",
            section="608",
            title="Evidence of Character and Conduct of Witness",
            summary=(
                "A witness's credibility may be attacked or supported by "
                "opinion or reputation evidence concerning the witness's "
                "character for truthfulness or untruthfulness.  Specific "
                "instances of conduct (not resulting in conviction) may be "
                "inquired into on cross-examination if probative of truthfulness "
                "or untruthfulness."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["truthfulness", "character", "impeachment"],
        ),
        LegalRule(
            rule_id="MRE-609",
            source="MRE",
            chapter="6",
            section="609",
            title="Impeachment by Evidence of Conviction of Crime",
            summary=(
                "A witness may be impeached with evidence of: (1) a felony "
                "conviction — admissible subject to MRE 403 balancing; "
                "(2) any crime involving dishonesty or false statement — "
                "admissible WITHOUT balancing.  A 10-year time limit generally "
                "applies from the date of conviction or release from "
                "confinement, whichever is later."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["conviction", "impeachment", "felony", "crime"],
        ),
        LegalRule(
            rule_id="MRE-611",
            source="MRE",
            chapter="6",
            section="611",
            title="Mode and Order of Interrogation and Presentation",
            summary=(
                "The court exercises reasonable control over the mode and order "
                "of interrogating witnesses and presenting evidence.  Leading "
                "questions are generally not permitted on direct examination but "
                "are allowed on cross-examination and when a party calls a "
                "hostile witness."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["examination", "cross_examination", "leading_questions"],
        ),
        LegalRule(
            rule_id="MRE-612",
            source="MRE",
            chapter="6",
            section="612",
            title="Writing Used to Refresh Memory",
            summary=(
                "If a witness uses a writing to refresh memory while testifying "
                "(or before testifying if justice requires), the adverse party "
                "is entitled to have the writing produced, to inspect it, to "
                "cross-examine the witness about it, and to introduce relevant "
                "portions into evidence."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["refresh_memory", "writing", "inspection"],
        ),
        LegalRule(
            rule_id="MRE-613",
            source="MRE",
            chapter="6",
            section="613",
            title="Prior Statements of Witnesses",
            summary=(
                "KEY IMPEACHMENT TOOL.  A witness may be impeached with prior "
                "inconsistent statements.  The examiner must give the witness "
                "an opportunity to explain or deny the statement.  If extrinsic "
                "evidence of the prior statement is used, proper foundation "
                "must be laid.  Critical for impeaching Emily Watson and her "
                "witnesses with their own prior sworn or written statements."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["prior_inconsistent", "impeachment", "confrontation"],
        ),
        LegalRule(
            rule_id="MRE-614",
            source="MRE",
            chapter="6",
            section="614",
            title="Calling and Interrogation of Witnesses by Court",
            summary=(
                "The court may call witnesses on its own and interrogate any "
                "witness.  All parties may cross-examine court-called witnesses.  "
                "Objections to court questioning may be made at the next "
                "available opportunity when the jury is not present."
            ),
            confidence="verified",
            lanes=["A"],
            tags=["court_witness", "judge_questions"],
        ),
        LegalRule(
            rule_id="MRE-615",
            source="MRE",
            chapter="6",
            section="615",
            title="Exclusion of Witnesses",
            summary=(
                "At a party's request, the court SHALL order witnesses excluded "
                "so they cannot hear other witnesses' testimony.  This rule "
                "does not authorize exclusion of: (1) a party who is a natural "
                "person, (2) a designated representative of an entity party, "
                "(3) a person whose presence is essential to the presentation "
                "of a party's case."
            ),
            confidence="verified",
            lanes=["A", "D"],
            tags=["witness_exclusion", "sequestration"],
        ),
        LegalRule(
            rule_id="MRE-616",
            source="MRE",
            chapter="6",
            section="616",
            title="Bias of Witness",
            summary=(
                "KEY RULE.  A witness's credibility may always be attacked by "
                "showing bias, prejudice, interest, or motive to misrepresent.  "
                "No specific foundation is required — wide latitude is permitted "
                "on cross-examination to explore bias.  Critical for showing "
                "bias of adverse witnesses and for documenting potential "
                "judicial bias under Lane E."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["bias", "interest", "prejudice", "impeachment"],
        ),

        # ─── Article VII — Opinions and Expert Testimony ────

        LegalRule(
            rule_id="MRE-701",
            source="MRE",
            chapter="7",
            section="701",
            title="Opinion Testimony by Lay Witnesses",
            summary=(
                "A lay witness may give opinion testimony if it is rationally "
                "based on the witness's perception and helpful to understanding "
                "the witness's testimony or determining a fact in issue."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["lay_opinion", "perception", "helpful"],
        ),
        LegalRule(
            rule_id="MRE-702",
            source="MRE",
            chapter="7",
            section="702",
            title="Testimony by Experts (Daubert Standard)",
            summary=(
                "Expert testimony is admissible if: (1) the expert is qualified "
                "by knowledge, skill, experience, training, or education; "
                "(2) testimony is based on sufficient facts or data; "
                "(3) testimony is the product of reliable principles and "
                "methods; (4) the expert has reliably applied the principles to "
                "the facts.  Michigan adopted the Daubert standard.  Used to "
                "challenge or support expert witnesses in custody evaluations."
            ),
            confidence="verified",
            lanes=["A", "B"],
            tags=["expert", "daubert", "scientific", "qualification"],
        ),
        LegalRule(
            rule_id="MRE-703",
            source="MRE",
            chapter="7",
            section="703",
            title="Bases of Opinion Testimony by Experts",
            summary=(
                "An expert may base an opinion on facts or data that the expert "
                "has been made aware of or personally observed.  If experts in "
                "the field would reasonably rely on such facts or data in "
                "forming an opinion, the facts or data need not be admissible "
                "for the opinion to be admitted."
            ),
            confidence="verified",
            lanes=["A"],
            tags=["expert", "basis", "facts", "data"],
        ),
        LegalRule(
            rule_id="MRE-705",
            source="MRE",
            chapter="7",
            section="705",
            title="Disclosure of Facts or Data Underlying Expert Opinion",
            summary=(
                "The expert may testify in terms of opinion or inference and "
                "give reasons without first testifying to the underlying facts "
                "or data, unless the court requires otherwise.  The expert may "
                "be required to disclose the underlying facts on "
                "cross-examination."
            ),
            confidence="verified",
            lanes=["A"],
            tags=["expert", "disclosure", "underlying_facts"],
        ),

        # ─── Article VIII — Hearsay ─────────────────────────

        LegalRule(
            rule_id="MRE-801",
            source="MRE",
            chapter="8",
            section="801",
            title="Definitions",
            summary=(
                "Hearsay = an out-of-court statement offered to prove the truth "
                "of the matter asserted.  'Statement' = an oral or written "
                "assertion, or nonverbal conduct intended as an assertion.  "
                "'Declarant' = the person who made the statement."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["hearsay", "definition", "statement", "declarant"],
        ),
        LegalRule(
            rule_id="MRE-801D1",
            source="MRE",
            chapter="8",
            section="801",
            subsection="(d)(1)",
            title="Prior Statements by Witness (Not Hearsay)",
            summary=(
                "NOT hearsay if the declarant testifies at trial and is subject "
                "to cross-examination concerning the statement, and the "
                "statement is: (A) inconsistent with the declarant's testimony "
                "and was given under oath at a prior proceeding; or "
                "(B) consistent with the declarant's testimony and offered to "
                "rebut an express or implied charge of recent fabrication or "
                "improper influence or motive; or (C) one of identification."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["prior_statement", "not_hearsay", "witness"],
        ),
        LegalRule(
            rule_id="MRE-801D2",
            source="MRE",
            chapter="8",
            section="801",
            subsection="(d)(2)",
            title="Admissions by Party-Opponent (Not Hearsay)",
            summary=(
                "KEY RULE.  NOT hearsay when offered against a party and is: "
                "(A) the party's own statement; (B) a statement the party "
                "adopted or manifested belief in; (C) a statement by an "
                "authorized person; (D) a statement by the party's agent or "
                "servant within the scope of agency/employment; (E) a statement "
                "by a co-conspirator during and in furtherance of the "
                "conspiracy.  Emily Watson's own statements in texts, emails, "
                "court filings, and social media are admissions — no hearsay "
                "objection is possible when offered against her."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["admission", "party_opponent", "not_hearsay"],
        ),
        LegalRule(
            rule_id="MRE-802",
            source="MRE",
            chapter="8",
            section="802",
            title="Hearsay Rule",
            summary=(
                "Hearsay is not admissible except as provided by these rules or "
                "by other rules prescribed by the Supreme Court."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["hearsay", "exclusion", "inadmissible"],
        ),
        LegalRule(
            rule_id="MRE-803-1",
            source="MRE",
            chapter="8",
            section="803",
            subsection="(1)",
            title="Present Sense Impression",
            summary=(
                "A statement describing or explaining an event or condition, "
                "made while or immediately after the declarant perceived it.  "
                "Admissible regardless of declarant's availability."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["hearsay_exception", "present_sense_impression"],
        ),
        LegalRule(
            rule_id="MRE-803-2",
            source="MRE",
            chapter="8",
            section="803",
            subsection="(2)",
            title="Excited Utterance",
            summary=(
                "A statement relating to a startling event or condition, made "
                "while the declarant was under the stress of excitement that it "
                "caused.  Admissible regardless of declarant's availability."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["hearsay_exception", "excited_utterance", "startling_event"],
        ),
        LegalRule(
            rule_id="MRE-803-3",
            source="MRE",
            chapter="8",
            section="803",
            subsection="(3)",
            title="Then-Existing Mental, Emotional, or Physical Condition",
            summary=(
                "A statement of the declarant's then-existing state of mind, "
                "emotion, sensation, or physical condition (such as intent, "
                "plan, motive, design, mental feeling, pain, or bodily health).  "
                "Admissible regardless of declarant's availability."
            ),
            confidence="verified",
            lanes=["A", "D"],
            tags=["hearsay_exception", "state_of_mind", "emotion", "physical_condition"],
        ),
        LegalRule(
            rule_id="MRE-803-4",
            source="MRE",
            chapter="8",
            section="803",
            subsection="(4)",
            title="Statements for Purposes of Medical Treatment or Diagnosis",
            summary=(
                "Statements made for purposes of medical treatment or "
                "diagnosis, describing medical history, past or present "
                "symptoms, pain, sensations, or the inception or general "
                "character of the cause or external source thereof, insofar as "
                "reasonably pertinent to treatment or diagnosis."
            ),
            confidence="verified",
            lanes=["A"],
            tags=["hearsay_exception", "medical", "diagnosis", "treatment"],
        ),
        LegalRule(
            rule_id="MRE-803-5",
            source="MRE",
            chapter="8",
            section="803",
            subsection="(5)",
            title="Recorded Recollection",
            summary=(
                "A memorandum or record concerning a matter about which a "
                "witness once had knowledge but now has insufficient "
                "recollection.  Must be shown to have been made or adopted by "
                "the witness when the matter was fresh in memory and to reflect "
                "that knowledge correctly.  If admitted, the memorandum may be "
                "read into evidence but may not itself be received as an "
                "exhibit unless offered by an adverse party."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["hearsay_exception", "recorded_recollection", "memory"],
        ),
        LegalRule(
            rule_id="MRE-803-6",
            source="MRE",
            chapter="8",
            section="803",
            subsection="(6)",
            title="Records of Regularly Conducted Activity (Business Records)",
            summary=(
                "KEY EXCEPTION.  A record of a regularly conducted activity is "
                "admissible if: (1) made at or near the time of the event; "
                "(2) by or from information transmitted by a person with "
                "knowledge; (3) kept in the course of a regularly conducted "
                "business activity; (4) it was the regular practice of the "
                "business to make such a record; (5) shown by testimony of the "
                "custodian or other qualified witness.  Critical for police "
                "reports, CPS records, FOC records, medical records, school "
                "records, and phone/bank records."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["hearsay_exception", "business_records", "regular_practice"],
        ),
        LegalRule(
            rule_id="MRE-803-8",
            source="MRE",
            chapter="8",
            section="803",
            subsection="(8)",
            title="Public Records and Reports",
            summary=(
                "KEY EXCEPTION.  Records, reports, statements, or data "
                "compilations of public offices or agencies setting forth: "
                "(A) the activities of the office or agency; (B) matters "
                "observed pursuant to a duty imposed by law as to which there "
                "was a duty to report; (C) in civil actions, factual findings "
                "resulting from an investigation made pursuant to authority "
                "granted by law.  Critical for court orders, government "
                "investigation reports, and FOC recommendations."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["hearsay_exception", "public_records", "government"],
        ),
        LegalRule(
            rule_id="MRE-803-10",
            source="MRE",
            chapter="8",
            section="803",
            subsection="(10)",
            title="Absence of Public Record or Entry",
            summary=(
                "Evidence in the form of certification or testimony from the "
                "custodian of a public record that a diligent search failed to "
                "disclose a record, report, statement, or data compilation is "
                "admissible to prove the nonexistence or nonoccurrence of a "
                "matter.  KEY for proving non-service of process: if the court "
                "file has no proof of service, a certification of absence "
                "proves non-service."
            ),
            confidence="verified",
            lanes=["E"],
            tags=["hearsay_exception", "absence", "public_record", "non_service"],
        ),
        LegalRule(
            rule_id="MRE-803-18",
            source="MRE",
            chapter="8",
            section="803",
            subsection="(18)",
            title="Learned Treatises",
            summary=(
                "Statements from published treatises, periodicals, or pamphlets "
                "established as reliable authority by expert testimony or "
                "judicial notice may be read into evidence for use with expert "
                "testimony.  If admitted, the statements may be read into "
                "evidence but may not be received as exhibits.  Useful for "
                "challenging custody evaluator methodologies."
            ),
            confidence="verified",
            lanes=["A"],
            tags=["hearsay_exception", "learned_treatise", "expert", "psychology"],
        ),
        LegalRule(
            rule_id="MRE-804B1",
            source="MRE",
            chapter="8",
            section="804",
            subsection="(b)(1)",
            title="Former Testimony (Declarant Unavailable)",
            summary=(
                "Testimony given at another hearing of the same or a different "
                "proceeding, if the party against whom the testimony is now "
                "offered had an opportunity and similar motive to develop the "
                "testimony by direct, cross, or redirect examination.  Requires "
                "that the declarant be unavailable."
            ),
            confidence="verified",
            lanes=["F"],
            tags=["hearsay_exception", "former_testimony", "unavailable"],
        ),
        LegalRule(
            rule_id="MRE-804B3",
            source="MRE",
            chapter="8",
            section="804",
            subsection="(b)(3)",
            title="Statement Against Interest (Declarant Unavailable)",
            summary=(
                "A statement that was, at the time of its making, so far "
                "contrary to the declarant's pecuniary or proprietary interest, "
                "or so far tended to subject the declarant to civil or criminal "
                "liability, that a reasonable person in the declarant's "
                "position would not have made the statement unless believing it "
                "to be true.  Requires declarant unavailability."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["hearsay_exception", "against_interest"],
        ),
        LegalRule(
            rule_id="MRE-805",
            source="MRE",
            chapter="8",
            section="805",
            title="Hearsay Within Hearsay",
            summary=(
                "Hearsay within hearsay (double or layered hearsay) is not "
                "excluded under the hearsay rule if each part of the combined "
                "statements conforms with an exception to the hearsay rule.  "
                "Each layer must independently satisfy an exception."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["hearsay", "layered", "double_hearsay"],
        ),
        LegalRule(
            rule_id="MRE-806",
            source="MRE",
            chapter="8",
            section="806",
            title="Attacking and Supporting Credibility of Declarant",
            summary=(
                "When a hearsay statement has been admitted, the credibility of "
                "the declarant may be attacked (and if attacked, supported) by "
                "any evidence that would be admissible for those purposes if "
                "the declarant had testified as a witness.  The declarant need "
                "not be given an opportunity to explain or deny."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["hearsay", "credibility", "impeachment", "declarant"],
        ),
        LegalRule(
            rule_id="MRE-807",
            source="MRE",
            chapter="8",
            section="807",
            title="Residual Exception",
            summary=(
                "A statement not specifically covered by any other exception "
                "but having equivalent circumstantial guarantees of "
                "trustworthiness is admissible if: (1) it is offered as "
                "evidence of a material fact; (2) it is more probative on the "
                "point than any other reasonably available evidence; (3) the "
                "interests of justice will be served.  Must give the adverse "
                "party advance notice of intent to offer the statement."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["hearsay_exception", "residual", "catchall"],
        ),

        # ─── Article IX — Authentication and Identification ─

        LegalRule(
            rule_id="MRE-901",
            source="MRE",
            chapter="9",
            section="901",
            title="Requirement of Authentication or Identification",
            summary=(
                "Evidence must be authenticated or identified as a condition "
                "precedent to admissibility.  Authentication requires evidence "
                "sufficient to support a finding that the matter in question is "
                "what the proponent claims it is."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["authentication", "identification", "foundation"],
        ),
        LegalRule(
            rule_id="MRE-901B1",
            source="MRE",
            chapter="9",
            section="901",
            subsection="(b)(1)",
            title="Testimony of Witness with Knowledge",
            summary=(
                "Authentication may be established by testimony of a witness "
                "with knowledge that a matter is what it is claimed to be.  The "
                "most straightforward authentication method."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["authentication", "witness", "knowledge"],
        ),
        LegalRule(
            rule_id="MRE-901B4",
            source="MRE",
            chapter="9",
            section="901",
            subsection="(b)(4)",
            title="Distinctive Characteristics and the Like",
            summary=(
                "KEY for digital evidence.  Appearance, contents, substance, "
                "internal patterns, or other distinctive characteristics, taken "
                "in conjunction with circumstances, can authenticate a "
                "document.  Used to authenticate text messages, emails, and "
                "social media posts where the content itself identifies the "
                "author (writing style, specific references, phone number, "
                "account details)."
            ),
            confidence="verified",
            lanes=["A", "D"],
            tags=["authentication", "distinctive", "texts", "emails", "digital"],
        ),
        LegalRule(
            rule_id="MRE-901B5",
            source="MRE",
            chapter="9",
            section="901",
            subsection="(b)(5)",
            title="Voice Identification",
            summary=(
                "Identification of a voice, whether heard firsthand or through "
                "mechanical or electronic transmission or recording, by the "
                "opinion of a person who has heard the voice at any time under "
                "circumstances connecting it with the alleged speaker.  Used to "
                "authenticate audio and voicemail recordings."
            ),
            confidence="verified",
            lanes=["A", "D"],
            tags=["authentication", "voice", "recording", "identification"],
        ),
        LegalRule(
            rule_id="MRE-901B7",
            source="MRE",
            chapter="9",
            section="901",
            subsection="(b)(7)",
            title="Public Records or Reports",
            summary=(
                "Evidence that a writing authorized by law to be recorded or "
                "filed and in fact recorded or filed in a public office, or a "
                "purported public record or report, is from the public office "
                "where items of this nature are kept."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["authentication", "public_records"],
        ),
        LegalRule(
            rule_id="MRE-901B9",
            source="MRE",
            chapter="9",
            section="901",
            subsection="(b)(9)",
            title="Process or System",
            summary=(
                "Evidence describing a process or system used to produce a "
                "result, and showing that the process or system produces an "
                "accurate result.  Relevant for authenticating computer-"
                "generated records, metadata, and digital forensic output."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["authentication", "process", "system", "digital"],
        ),
        LegalRule(
            rule_id="MRE-902",
            source="MRE",
            chapter="9",
            section="902",
            title="Self-Authentication",
            summary=(
                "Certain documents are self-authenticating and require no "
                "extrinsic evidence of authenticity: domestic public documents "
                "under seal, certified copies of public records, official "
                "publications, newspapers and periodicals, trade inscriptions, "
                "acknowledged documents, and commercial paper.  Always obtain "
                "certified copies of court records and government documents to "
                "invoke self-authentication."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["self_authentication", "no_foundation"],
        ),
        LegalRule(
            rule_id="MRE-902-4",
            source="MRE",
            chapter="9",
            section="902",
            subsection="(4)",
            title="Certified Copies of Public Records",
            summary=(
                "A copy of an official record — or a copy of a document that "
                "was recorded or filed in a public office — certified as "
                "correct by the custodian or other person authorized to make "
                "the certification, is self-authenticating.  KEY: get certified "
                "copies of court records, docket entries, and government "
                "documents to avoid authentication challenges."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["self_authentication", "certified", "public_record"],
        ),

        # ─── Article X — Contents of Writings, Recordings, and Photographs ─

        LegalRule(
            rule_id="MRE-1001",
            source="MRE",
            chapter="10",
            section="1001",
            title="Definitions",
            summary=(
                "Defines 'writings,' 'recordings,' 'photographs,' 'original,' "
                "and 'duplicate' for purposes of the best evidence rule.  An "
                "'original' of a writing or recording is the writing or "
                "recording itself.  A 'duplicate' is a counterpart produced by "
                "a process that accurately reproduces the original."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["best_evidence", "definitions", "original", "duplicate"],
        ),
        LegalRule(
            rule_id="MRE-1002",
            source="MRE",
            chapter="10",
            section="1002",
            title="Requirement of Original (Best Evidence Rule)",
            summary=(
                "To prove the content of a writing, recording, or photograph, "
                "the original is required, except as otherwise provided in "
                "these rules or by statute."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["best_evidence", "original", "contents"],
        ),
        LegalRule(
            rule_id="MRE-1003",
            source="MRE",
            chapter="10",
            section="1003",
            title="Admissibility of Duplicates",
            summary=(
                "A duplicate is admissible to the same extent as an original "
                "unless: (1) a genuine question is raised as to the "
                "authenticity of the original; or (2) under the circumstances "
                "it would be unfair to admit the duplicate in lieu of the "
                "original."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["duplicate", "admissible", "copy"],
        ),
        LegalRule(
            rule_id="MRE-1005",
            source="MRE",
            chapter="10",
            section="1005",
            title="Public Records",
            summary=(
                "The contents of an official record, or of a document "
                "authorized to be recorded or filed, may be proved by a copy "
                "certified as correct or testified to be correct by a witness "
                "who has compared it with the original.  If no such copy can be "
                "obtained by reasonable diligence, then other evidence of the "
                "contents may be given."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["public_records", "copy", "certified"],
        ),
        LegalRule(
            rule_id="MRE-1006",
            source="MRE",
            chapter="10",
            section="1006",
            title="Summaries",
            summary=(
                "The contents of voluminous writings, recordings, or "
                "photographs that cannot conveniently be examined in court may "
                "be presented in the form of a chart, summary, or calculation.  "
                "The originals or duplicates must be made available for "
                "examination or copying by other parties.  KEY for presenting "
                "large volumes of text messages, emails, or financial records "
                "as organized summaries or chronological exhibits."
            ),
            confidence="verified",
            lanes=ALL_LANES,
            tags=["summary", "voluminous", "charts", "calculations"],
        ),
    ]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Function 2: Evidence-Specific Decision-Tree Rules
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_mre_evidence_rules() -> List[EvidenceRule]:
    """Return evidence-specific decision-tree rules for the Pigors v. Watson case."""
    return [
        # 1 — Hearsay Analysis Decision Tree
        EvidenceRule(
            rule_id="MRE-HEARSAY-TREE",
            mre_number="801-807",
            rule_name="Hearsay Analysis Decision Tree",
            category="hearsay_exception",
            prerequisites=[
                "Identify the statement",
                "Identify the declarant",
                "Determine purpose of offering",
            ],
            applies_when=(
                "Any out-of-court statement offered at trial or hearing"
            ),
            excludes_when=(
                "Statement not offered for truth of matter asserted (e.g., "
                "offered to show effect on listener, verbal acts, impeachment)"
            ),
            decision_tree={
                "step_1": {
                    "question": (
                        "Is it a 'statement' (oral/written assertion or "
                        "assertive conduct)?"
                    ),
                    "if_no": "Not hearsay — admissible",
                    "if_yes": "Go to step 2",
                },
                "step_2": {
                    "question": "Was it made out of court?",
                    "if_no": "Not hearsay — admissible",
                    "if_yes": "Go to step 3",
                },
                "step_3": {
                    "question": (
                        "Is it offered to prove the truth of the matter "
                        "asserted?"
                    ),
                    "if_no": (
                        "Not hearsay — admissible (e.g., verbal act, effect "
                        "on listener, impeachment)"
                    ),
                    "if_yes": "Go to step 4",
                },
                "step_4": {
                    "question": (
                        "Is the declarant a party-opponent? (MRE 801(d)(2))"
                    ),
                    "if_yes": (
                        "NOT hearsay — admission by party-opponent — ADMISSIBLE"
                    ),
                    "if_no": "Go to step 5",
                },
                "step_5": {
                    "question": (
                        "Is it a prior statement by a testifying witness? "
                        "(MRE 801(d)(1))"
                    ),
                    "if_yes": (
                        "NOT hearsay if witness testifies and subject to "
                        "cross — ADMISSIBLE"
                    ),
                    "if_no": "Go to step 6",
                },
                "step_6": {
                    "question": (
                        "IT IS HEARSAY. Does a Rule 803 exception apply "
                        "(declarant availability immaterial)?"
                    ),
                    "if_yes": (
                        "Admissible under exception — identify specific "
                        "exception"
                    ),
                    "if_no": "Go to step 7",
                },
                "step_7": {
                    "question": (
                        "Is the declarant unavailable? Does a Rule 804 "
                        "exception apply?"
                    ),
                    "if_yes": "Admissible under 804 exception",
                    "if_no": "Go to step 8",
                },
                "step_8": {
                    "question": (
                        "Does the residual exception (MRE 807) apply?"
                    ),
                    "if_yes": (
                        "Admissible if equivalent guarantees of "
                        "trustworthiness + notice given"
                    ),
                    "if_no": (
                        "INADMISSIBLE HEARSAY — object or move to strike"
                    ),
                },
            },
            lane_relevance=["A", "B", "C", "D", "E", "F"],
        ),

        # 2 — Authenticating Digital Evidence
        EvidenceRule(
            rule_id="MRE-AUTH-DIGITAL",
            mre_number="901(b)(4)",
            rule_name="Authenticating Digital Evidence",
            category="authentication",
            prerequisites=[
                "Witness who can identify the account/device owner",
                (
                    "Evidence of distinctive characteristics (writing style, "
                    "content references, phone number)"
                ),
                "Chain of custody of device or screenshots",
                (
                    "Testimony that screenshots accurately depict what "
                    "appeared on screen"
                ),
            ],
            applies_when=(
                "Offering text messages, emails, social media posts, or other "
                "digital communications as evidence"
            ),
            excludes_when=(
                "When digital evidence is self-authenticating (e.g., certified "
                "records from service provider) or when authenticity is "
                "stipulated"
            ),
            decision_tree={
                "step_1": (
                    "Can a witness with personal knowledge testify they "
                    "sent/received the message?"
                ),
                "step_2": (
                    "Do the contents contain distinctive characteristics "
                    "linking to the claimed author?"
                ),
                "step_3": (
                    "Is there corroborating evidence (reply context, phone "
                    "records, IP logs)?"
                ),
                "step_4": (
                    "Can chain of custody be established (who took screenshot, "
                    "when, from what device)?"
                ),
            },
            lane_relevance=["A", "D"],
        ),

        # 3 — Authenticating Audio/Video Recordings
        EvidenceRule(
            rule_id="MRE-AUTH-RECORDING",
            mre_number="901(b)(5)",
            rule_name="Authenticating Audio/Video Recordings",
            category="authentication",
            prerequisites=[
                "Voice identification by person familiar with the voice",
                "Testimony that recording is accurate and unaltered",
                "Chain of custody of recording device/file",
                "Testimony about recording conditions",
            ],
            applies_when=(
                "Offering audio recordings, video recordings, or voicemail "
                "as evidence"
            ),
            excludes_when=(
                "Recording obtained in violation of Michigan's one-party "
                "consent law (MCL 750.539c) — Michigan allows one-party consent"
            ),
            decision_tree={
                "step_1": (
                    "Can someone identify the voices on the recording?"
                ),
                "step_2": (
                    "Can someone testify the recording accurately captures "
                    "the conversation?"
                ),
                "step_3": (
                    "Is there evidence the recording has not been altered?"
                ),
                "step_4": (
                    "Was the recording legally obtained (one-party consent "
                    "in Michigan)?"
                ),
            },
            lane_relevance=["A", "D"],
        ),

        # 4 — Authenticating Public/Government Records
        EvidenceRule(
            rule_id="MRE-AUTH-PUBLIC-RECORD",
            mre_number="902(4)",
            rule_name="Authenticating Public/Government Records",
            category="authentication",
            prerequisites=[
                "Certified copy from records custodian",
                "OR testimony of person familiar with record-keeping practices",
            ],
            applies_when=(
                "Offering court orders, docket entries, police reports, CPS "
                "records, FOC reports, or other government records"
            ),
            excludes_when=(
                "Uncertified copies without custodian testimony (request "
                "certified copies to avoid this issue)"
            ),
            decision_tree={
                "step_1": (
                    "Is the document a certified copy under seal? → "
                    "Self-authenticating under MRE 902(4)"
                ),
                "step_2": (
                    "If not certified, can a records custodian testify to "
                    "authenticity?"
                ),
                "step_3": (
                    "Does MRE 803(8) public records exception also apply "
                    "for hearsay?"
                ),
            },
            lane_relevance=["A", "B", "C", "D", "E", "F"],
        ),

        # 5 — Impeachment with Prior Inconsistent Statements
        EvidenceRule(
            rule_id="MRE-IMPEACH-PRIOR-INCONSISTENT",
            mre_number="613",
            rule_name="Impeachment with Prior Inconsistent Statements",
            category="impeachment",
            prerequisites=[
                "Identify the prior inconsistent statement",
                (
                    "Have the statement available (document, transcript, "
                    "recording)"
                ),
                "Be prepared to confront the witness with the statement",
                (
                    "If using extrinsic evidence, must give witness opportunity "
                    "to explain or deny"
                ),
            ],
            applies_when=(
                "Witness testifies to something contradicted by their own "
                "prior statement in deposition, affidavit, text, email, social "
                "media post, or prior hearing"
            ),
            excludes_when=(
                "When the statement is not actually inconsistent, or when the "
                "inconsistency is trivial and collateral"
            ),
            decision_tree={
                "step_1": "Did the witness make a prior statement?",
                "step_2": (
                    "Is the prior statement inconsistent with current "
                    "testimony?"
                ),
                "step_3": (
                    "Cross-examine: direct witness's attention to the prior "
                    "statement"
                ),
                "step_4": "Give witness opportunity to explain or deny",
                "step_5": (
                    "If witness denies, may introduce extrinsic proof of the "
                    "prior statement"
                ),
            },
            lane_relevance=["A", "B", "C", "D", "E", "F"],
        ),

        # 6 — Impeachment by Showing Bias
        EvidenceRule(
            rule_id="MRE-IMPEACH-BIAS",
            mre_number="616",
            rule_name="Impeachment by Showing Bias",
            category="impeachment",
            prerequisites=[
                (
                    "Evidence of relationship, interest, or motive to "
                    "misrepresent"
                ),
                (
                    "No specific foundation requirement — wide latitude "
                    "allowed"
                ),
            ],
            applies_when=(
                "Witness has a relationship with a party, financial interest "
                "in the outcome, motive to lie, or other source of bias or "
                "prejudice"
            ),
            excludes_when=(
                "Alleged bias is speculative with no factual basis"
            ),
            decision_tree={
                "step_1": (
                    "Does the witness have a personal relationship with a "
                    "party?"
                ),
                "step_2": (
                    "Does the witness have a financial or personal interest "
                    "in the outcome?"
                ),
                "step_3": (
                    "Has the witness shown hostility or favoritism?"
                ),
                "step_4": (
                    "Cross-examine on the bias — wide latitude permitted, no "
                    "specific foundation needed"
                ),
            },
            lane_relevance=["A", "B", "C", "D", "E", "F"],
        ),

        # 7 — Business Records Exception
        EvidenceRule(
            rule_id="MRE-BUSINESS-RECORDS",
            mre_number="803(6)",
            rule_name="Business Records Exception",
            category="hearsay_exception",
            prerequisites=[
                "Record made at or near time of event",
                "Made by or from information of person with knowledge",
                "Kept in course of regularly conducted business activity",
                "It was regular practice of business to make such record",
                (
                    "Foundation testimony from custodian or qualified witness "
                    "OR certification under MCR 2.506"
                ),
            ],
            applies_when=(
                "Offering police reports, CPS investigation notes, FOC "
                "records, medical records, school records, phone records, bank "
                "records, employment records as evidence"
            ),
            excludes_when=(
                "When source of information or method/circumstances of "
                "preparation indicate lack of trustworthiness, or when record "
                "was prepared specifically for litigation"
            ),
            decision_tree={
                "step_1": (
                    "Is this a record of a regularly conducted activity?"
                ),
                "step_2": (
                    "Was it made at or near the time of the event by someone "
                    "with knowledge?"
                ),
                "step_3": (
                    "Was it the regular practice to make this type of record?"
                ),
                "step_4": (
                    "Can a custodian or qualified witness provide foundation "
                    "testimony?"
                ),
                "step_5": (
                    "Does anything suggest lack of trustworthiness?"
                ),
            },
            lane_relevance=["A", "B", "C", "D", "E", "F"],
        ),

        # 8 — Public Records Exception
        EvidenceRule(
            rule_id="MRE-PUBLIC-RECORDS",
            mre_number="803(8)",
            rule_name="Public Records Exception",
            category="hearsay_exception",
            prerequisites=[
                "Record created by public office or agency",
                (
                    "Sets forth activities of the office, OR matters observed "
                    "pursuant to legal duty, OR factual findings from "
                    "authorized investigation"
                ),
                "No indication of untrustworthiness",
            ],
            applies_when=(
                "Offering court orders, government investigation reports, FOC "
                "recommendations, vital records, property records, official "
                "correspondence"
            ),
            excludes_when=(
                "When the record reflects matters observed by law enforcement "
                "in criminal cases (limited applicability), or when "
                "circumstances indicate untrustworthiness"
            ),
            decision_tree={
                "step_1": (
                    "Was this record created by a government office?"
                ),
                "step_2": (
                    "Does it record (a) office activities, (b) observed "
                    "matters under legal duty, or (c) factual findings from "
                    "investigation?"
                ),
                "step_3": (
                    "Is there any indication of untrustworthiness?"
                ),
                "step_4": (
                    "If certified copy available → also self-authenticating "
                    "under MRE 902"
                ),
            },
            lane_relevance=["A", "B", "C", "D", "E", "F"],
        ),

        # 9 — Party-Opponent Admissions
        EvidenceRule(
            rule_id="MRE-PARTY-ADMISSIONS",
            mre_number="801(d)(2)",
            rule_name="Party-Opponent Admissions",
            category="hearsay_exception",
            prerequisites=[
                (
                    "Identify the declarant as a party to the case (or party's "
                    "agent/servant/co-conspirator)"
                ),
                "Statement offered against that party",
            ],
            applies_when=(
                "Offering Emily Watson's own statements from texts, emails, "
                "social media, court filings, testimony, voicemails, or "
                "statements to third parties.  Also applies to statements by "
                "Emily's agents (attorney letters, authorized representatives)."
            ),
            excludes_when=(
                "Statement is offered by the party who made it (you cannot use "
                "your own prior statements as admissions — only opponent's "
                "statements qualify)"
            ),
            decision_tree={
                "step_1": (
                    "Is the declarant a party-opponent (or agent/servant/"
                    "co-conspirator)?"
                ),
                "step_2": (
                    "Is the statement being offered against that party?"
                ),
                "step_3": (
                    "NOT HEARSAY under MRE 801(d)(2) — no exception needed, "
                    "no foundation beyond identifying declarant as party"
                ),
                "step_4": (
                    "No trustworthiness requirement — admissions are admissible "
                    "even if self-serving when made"
                ),
            },
            lane_relevance=["A", "B", "C", "D", "E", "F"],
        ),

        # 10 — Other Acts Evidence Analysis
        EvidenceRule(
            rule_id="MRE-CHARACTER-OTHER-ACTS",
            mre_number="404(b)",
            rule_name="Other Acts Evidence Analysis",
            category="relevance",
            prerequisites=[
                "Identify the other act",
                (
                    "Identify a proper purpose (not propensity): motive, "
                    "opportunity, intent, preparation, scheme, plan, knowledge, "
                    "identity, absence of mistake"
                ),
                "Demonstrate relevance to a fact of consequence",
                (
                    "Probative value must not be substantially outweighed by "
                    "prejudice (MRE 403 balancing)"
                ),
            ],
            applies_when=(
                "Seeking to introduce evidence of Emily Watson's prior false "
                "accusations, pattern of weaponizing legal process, or other "
                "acts showing scheme/plan/motive"
            ),
            excludes_when=(
                "Evidence offered solely to show bad character or propensity "
                "to act in conformity — must have a proper non-propensity "
                "purpose"
            ),
            decision_tree={
                "step_1": "What is the other act?",
                "step_2": (
                    "Is there a proper non-propensity purpose? (motive, plan, "
                    "scheme, pattern, intent, knowledge, identity, absence of "
                    "mistake)"
                ),
                "step_3": (
                    "Is the act relevant to a fact of consequence in this case?"
                ),
                "step_4": (
                    "Does probative value substantially outweigh unfair "
                    "prejudice? (MRE 403 balancing)"
                ),
                "step_5": (
                    "If admissible, request/prepare limiting instruction for "
                    "the factfinder"
                ),
            },
            lane_relevance=["A", "D"],
        ),
    ]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Module self-test
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    rules = get_mre_rules()
    evidence_rules = get_mre_evidence_rules()

    # Verify uniqueness across both collections
    rule_ids = [r.rule_id for r in rules]
    ev_ids = [e.rule_id for e in evidence_rules]
    all_ids = rule_ids + ev_ids

    assert len(rule_ids) == len(set(rule_ids)), (
        f"Duplicate rule_ids in get_mre_rules(): "
        f"{[x for x in rule_ids if rule_ids.count(x) > 1]}"
    )
    assert len(ev_ids) == len(set(ev_ids)), (
        f"Duplicate rule_ids in get_mre_evidence_rules(): "
        f"{[x for x in ev_ids if ev_ids.count(x) > 1]}"
    )
    assert len(all_ids) == len(set(all_ids)), (
        f"Duplicate rule_ids across both functions: "
        f"{[x for x in all_ids if all_ids.count(x) > 1]}"
    )

    # Verify all rule_ids follow MRE-XXX pattern
    for rid in rule_ids:
        assert rid.startswith("MRE-"), f"Rule ID {rid} does not start with 'MRE-'"
    for rid in ev_ids:
        assert rid.startswith("MRE-"), f"Evidence rule ID {rid} does not start with 'MRE-'"

    # Verify all LegalRules have source="MRE"
    for r in rules:
        assert r.source == "MRE", f"Rule {r.rule_id} has source={r.source!r}, expected 'MRE'"

    print("MRE Data Module — Self-Test Passed")
    print(f"  Legal Rules:    {len(rules)}")
    print(f"  Evidence Rules: {len(evidence_rules)}")
    print(f"  All IDs unique: \u2713")
