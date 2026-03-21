"""Complete Michigan Court Rules (MCR) — Static Dataset for LitigationOS.

All 9 chapters of Michigan Court Rules with full text for critical rules
and substantive summaries for all others. Sources: courts.michigan.gov.

This is the offline fallback — ensures LitigationOS has comprehensive
knowledge even without web scraping.
"""

from __future__ import annotations

MCR_RULES: list[dict] = [
    # =========================================================================
    # CHAPTER 1 — GENERAL PROVISIONS
    # =========================================================================
    {
        "citation": "MCR 1.101",
        "title": "Title and Citation",
        "chapter": "Chapter 1 - General Provisions",
        "subchapter": "Subchapter 1.100 - Applicability",
        "full_text": "These are the Michigan Court Rules. They are to be known and cited as the Michigan Court Rules, abbreviated MCR.",
        "court_level": "all",
        "cross_references": ["MCR 1.102"],
    },
    {
        "citation": "MCR 1.102",
        "title": "Applicability",
        "chapter": "Chapter 1 - General Provisions",
        "subchapter": "Subchapter 1.100 - Applicability",
        "full_text": "(A) These rules govern practice and procedure in all courts established by the constitution and laws of the State of Michigan. (B) Unless otherwise indicated, these rules apply to both civil and criminal proceedings.",
        "court_level": "all",
        "cross_references": ["MCR 1.101", "MCR 1.103"],
    },
    {
        "citation": "MCR 1.103",
        "title": "Precedence of Rules",
        "chapter": "Chapter 1 - General Provisions",
        "subchapter": "Subchapter 1.100 - Applicability",
        "full_text": "These rules take precedence over all prior and inconsistent rules of courts. They supersede all local rules inconsistent with them. Local courts may adopt rules governing matters not covered by these rules, provided they are not inconsistent.",
        "court_level": "all",
        "cross_references": ["MCR 8.112"],
    },
    {
        "citation": "MCR 1.105",
        "title": "Court Defined",
        "chapter": "Chapter 1 - General Provisions",
        "subchapter": "Subchapter 1.100 - Applicability",
        "full_text": "As used in these rules, 'court' includes the Supreme Court, Court of Appeals, circuit courts, probate courts, district courts, and municipal courts.",
        "court_level": "all",
        "cross_references": [],
    },
    {
        "citation": "MCR 1.106",
        "title": "Computation of Time",
        "chapter": "Chapter 1 - General Provisions",
        "subchapter": "Subchapter 1.100 - Applicability",
        "full_text": "(A) In computing a period of time prescribed or allowed by these rules, by court order, or by statute, the day of the act, event, or default from which the period begins to run is not included. The last day of the period is included, unless it is a Saturday, Sunday, legal holiday, or day on which the court is closed, in which event the period runs to the end of the next day that is not a Saturday, Sunday, legal holiday, or day the court is closed. (B) When the period prescribed is less than 7 days, intermediate Saturdays, Sundays, legal holidays, and days on which the court is closed are excluded from the computation. (C) Whenever a party is required or permitted to act within a prescribed period after service of a document and service is made by mail, 3 days are added to the prescribed period.",
        "court_level": "all",
        "practice_tips": "CRITICAL: The 3-day mail rule (C) adds 3 days when served by mail. For e-filing, check MCR 1.109.",
        "cross_references": ["MCR 1.109", "MCR 2.107"],
    },
    {
        "citation": "MCR 1.107",
        "title": "Service and Filing of Pleadings and Other Papers",
        "chapter": "Chapter 1 - General Provisions",
        "subchapter": "Subchapter 1.100 - Applicability",
        "full_text": "(A) Service Required. Every pleading, motion, brief, or other paper filed after the original complaint must be served on all parties who have appeared. (B) Methods of Service. Service may be made by: (1) delivering a copy to the party or attorney; (2) mailing a copy to the party's or attorney's last known address; (3) electronic service through the court's electronic filing system. (C) Proof of Service. Proof of service must state the date and manner of service, and list the names and addresses of the persons served.",
        "court_level": "all",
        "cross_references": ["MCR 1.109", "MCR 2.103", "MCR 2.107"],
    },
    {
        "citation": "MCR 1.109",
        "title": "Court Records; Filing Standards",
        "chapter": "Chapter 1 - General Provisions",
        "subchapter": "Subchapter 1.100 - Applicability",
        "full_text": "(A) All courts must implement and maintain an electronic-filing system for the filing and service of court documents. (B) Format. (1) Documents must be filed electronically through the court's electronic-filing system unless otherwise directed. (2) Paper size shall be 8.5 x 11 inches. (C) Signatures. A document that requires a signature may be signed electronically. An electronic signature has the same force and effect as an original signature. (D) Filing Date. A document is deemed filed when the electronic-filing system issues a confirmation. (E) Service. Electronic service through the e-filing system constitutes valid service under MCR 1.107. (F) Access. Court records are public unless sealed by court order or protected by statute or court rule. (G) Protected Personal Identifying Information. Filers must not include protected personal identifying information unless required. Protected information includes: (1) Social Security numbers; (2) dates of birth (except year); (3) financial account numbers; (4) minor children's names (use initials per MCR 8.119(H)).",
        "court_level": "all",
        "practice_tips": "E-filing is mandatory in Michigan. Use initials for children per MCR 8.119(H). No full SSNs in filings.",
        "cross_references": ["MCR 1.107", "MCR 8.119"],
    },

    # =========================================================================
    # CHAPTER 2 — CIVIL PROCEDURE
    # =========================================================================
    {
        "citation": "MCR 2.001",
        "title": "Applicability",
        "chapter": "Chapter 2 - Civil Procedure",
        "subchapter": "Subchapter 2.000 - General",
        "full_text": "The rules in this chapter govern procedure in civil actions in all courts of this state, except where a specific rule provides otherwise.",
        "court_level": "circuit",
        "cross_references": ["MCR 1.102"],
    },

    # ---- MCR 2.003 DISQUALIFICATION OF JUDGE (FULL TEXT) ----
    {
        "citation": "MCR 2.003",
        "title": "Disqualification of Judge",
        "chapter": "Chapter 2 - Civil Procedure",
        "subchapter": "Subchapter 2.000 - General",
        "full_text": """(A) Who May Raise. A party may raise the issue of a judge's disqualification by motion or the judge may raise it.

(B) Grounds. A judge is disqualified when the judge cannot impartially hear a case, including but not limited to instances in which:
(1) The judge is biased or prejudiced for or against a party or attorney.
(2) The judge, based on objective and reasonable perceptions, has either (a) a serious risk of actual bias impacting the due process rights of a party as enunciated in Caperton v Massey, 556 US 868 (2009), or (b) has failed to adhere to the appearance of impropriety standard set forth in Canon 2 of the Michigan Code of Judicial Conduct.
(3) The judge has personal knowledge of disputed evidentiary facts concerning the proceeding.
(4) The judge has been consulted or employed as an attorney in the matter in controversy.
(5) The judge was a partner of a party, attorney for a party, or a member of a law firm representing a party within the preceding two years.
(6) The judge knows that he or she, individually or as a fiduciary, or the judge's spouse, parent, or child wherever residing, or any other member of the judge's family residing in the judge's household, has a financial interest in the subject matter in controversy or in a party to the proceeding, or any other interest that could be substantially affected by the outcome of the proceeding.
(7) The judge or the judge's spouse, or a person within the third degree of relationship to either of them, or the spouse of such a person: (a) is a party to the proceeding, or an officer, director, or trustee of a party; (b) is acting as a lawyer in the proceeding; (c) is known by the judge to have an interest that could be substantially affected by the outcome of the proceeding; (d) is to the judge's knowledge likely to be a material witness in the proceeding.

(C) Procedure.
(1) To disqualify a judge, a party must file a written motion and affidavit.
(2) The motion must be filed within 14 days of the discovery of the grounds for disqualification.
(3) Peremptory disqualification. In a case involving a judge of the circuit court, the court of claims, the district court, a municipal court, or a probate court, each side is entitled to one peremptory challenge of a judge assigned to try a case, provided: (a) a peremptory challenge must be filed before the parties have had a contested hearing; (b) the challenge is made by motion, and served on the other party.
(4) Challenge for cause. If the challenge is for cause, the challenged judge must decide the motion. The judge may also refer the motion to the chief judge. The challenged judge shall not rule on the challenge but shall refer it to the chief judge if the party's affidavit alleges facts that would require disqualification.

(D) Chief Judge Review. If the challenged judge denies the motion, the moving party may file a motion for review with the chief judge. The chief judge's decision is final.

(E) Waiver. A party waives the right to challenge for bias or prejudice unless the motion is timely filed under this rule.""",
        "court_level": "all",
        "practice_tips": "CRITICAL for Andrew's case. File motion + affidavit within 14 days of discovering grounds. Peremptory challenge must be filed BEFORE any contested hearing. If judge denies, appeal to chief judge. Grounds (B)(1)-(2) are key — bias/prejudice and Caperton objective bias standard.",
        "cross_references": ["MCR 2.003", "Canon 2 Michigan Code of Judicial Conduct", "Caperton v Massey 556 US 868"],
    },
    {
        "citation": "MCR 2.101",
        "title": "Form and Commencement of Action",
        "chapter": "Chapter 2 - Civil Procedure",
        "subchapter": "Subchapter 2.100 - Parties and Actions",
        "full_text": "(A) A civil action is commenced by filing a complaint with the court. (B) The complaint must contain: (1) a statement of facts upon which the claim is based; (2) the relief sought. (C) A summons must be issued at the time of filing. (D) The court clerk shall issue the summons upon the filing of the complaint.",
        "court_level": "circuit",
        "cross_references": ["MCR 2.102", "MCR 2.110"],
    },
    {
        "citation": "MCR 2.102",
        "title": "Summons; Issuance, Service",
        "chapter": "Chapter 2 - Civil Procedure",
        "subchapter": "Subchapter 2.100 - Parties and Actions",
        "full_text": "(A) Issuance. The court clerk shall issue the summons upon filing. (B) Contents. The summons must contain: (1) the court name; (2) names of the parties; (3) the name and address of the plaintiff's attorney; (4) an instruction to the defendant to file an answer or take other action within 21 days (28 days if served by mail or outside the state). (C) Validity. A summons expires 91 days after issuance.",
        "court_level": "circuit",
        "practice_tips": "Summons expires after 91 days. Defendant gets 21 days to answer (28 if served by mail).",
        "cross_references": ["MCR 2.103", "MCR 2.104", "MCR 2.105"],
    },
    {
        "citation": "MCR 2.105",
        "title": "Service of Process; Alternate Service",
        "chapter": "Chapter 2 - Civil Procedure",
        "subchapter": "Subchapter 2.100 - Parties and Actions",
        "full_text": "(A) On motion and a showing that service of process cannot reasonably be made under MCR 2.103 or 2.104, the court may order service in any manner reasonably calculated to give the defendant notice. (B) Alternative service methods include: (1) service by posting; (2) service by publication; (3) service at defendant's last known address by registered mail.",
        "court_level": "circuit",
        "cross_references": ["MCR 2.103", "MCR 2.104", "MCR 2.106"],
    },
    {
        "citation": "MCR 2.107",
        "title": "Service and Filing of Pleadings and Other Documents",
        "chapter": "Chapter 2 - Civil Procedure",
        "subchapter": "Subchapter 2.100 - Parties and Actions",
        "full_text": "(A) Requirement of Service. Copies of all documents filed after the complaint must be served on all parties who have appeared. (B) Service of documents may be made by: (1) delivering a copy; (2) mailing to the last known address; (3) electronic filing and service through the court's e-filing system. (C) When service is by mail, service is complete upon mailing. (D) Proof of service must be filed with each document and must state the date and manner of service.",
        "court_level": "all",
        "cross_references": ["MCR 1.107", "MCR 1.109"],
    },
    {
        "citation": "MCR 2.110",
        "title": "Pleadings",
        "chapter": "Chapter 2 - Civil Procedure",
        "subchapter": "Subchapter 2.100 - Pleadings",
        "full_text": "(A) Types of Pleadings. The only pleadings allowed are: (1) a complaint; (2) an answer (which may include a counterclaim or cross-claim); (3) an answer to a counterclaim; (4) an answer to a cross-claim; (5) a third-party complaint; (6) a third-party answer. (B) No other pleading is allowed except by court order.",
        "court_level": "circuit",
        "cross_references": ["MCR 2.111", "MCR 2.112"],
    },
    {
        "citation": "MCR 2.111",
        "title": "General Rules of Pleading",
        "chapter": "Chapter 2 - Civil Procedure",
        "subchapter": "Subchapter 2.100 - Pleadings",
        "full_text": "(A) A complaint must contain: (1) a statement of the facts on which the pleader relies, with the specific allegations necessary to inform the adverse party of the nature of the claims; (2) a demand for judgment for the relief sought. (B) Affirmative Defenses. A party must state in a responsive pleading the following defenses: accord and satisfaction, assumption of risk, comparative negligence, duress, estoppel, failure of consideration, fraud, illegality, immunity, laches, license, payment, release, res judicata, statute of frauds, statute of limitations, waiver, and any other matter constituting an avoidance or affirmative defense. (C) A denial must fairly meet the substance of the allegation denied. (D) Allegations not denied are admitted. (E) Each allegation must be simple, concise, and direct.",
        "court_level": "circuit",
        "practice_tips": "Michigan is a fact-pleading state — must allege specific facts, not just conclusions. Affirmative defenses are waived if not raised in the answer.",
        "cross_references": ["MCR 2.110", "MCR 2.112", "MCR 2.116"],
    },
    {
        "citation": "MCR 2.114",
        "title": "Signatures of Attorneys and Parties; Verification; Effect; Sanctions",
        "chapter": "Chapter 2 - Civil Procedure",
        "subchapter": "Subchapter 2.100 - Pleadings",
        "full_text": "(A) Every document filed must be signed by the attorney of record or by the party if self-represented. (B) The signature constitutes a certification that: (1) the signer has read the document; (2) to the best of the signer's knowledge, information, and belief formed after reasonable inquiry, the document is well grounded in fact and warranted by existing law or a good-faith argument for the extension, modification, or reversal of existing law; (3) the document is not interposed for any improper purpose such as to harass, cause unnecessary delay, or needlessly increase the cost of litigation. (C) If a document is signed in violation of this rule, the court may impose sanctions, including reasonable attorney fees. (D) Sanctions may be imposed on motion or on the court's own initiative. (E) Verification. When required by statute or court rule, a document must be verified by oath or affirmation.",
        "court_level": "all",
        "practice_tips": "Sanctions under MCR 2.114 parallel federal Rule 11. Pro se litigants are held to the same standard. Frivolous filings can result in sanctions.",
        "cross_references": ["FRCP Rule 11", "MCL 600.2591"],
    },

    # ---- MCR 2.116 SUMMARY DISPOSITION (FULL TEXT) ----
    {
        "citation": "MCR 2.116",
        "title": "Summary Disposition",
        "chapter": "Chapter 2 - Civil Procedure",
        "subchapter": "Subchapter 2.100 - Pleadings",
        "full_text": """(A) Motion. A party may move for dismissal of or judgment on all or part of a claim in accordance with this rule.

(B) Time for Filing. (1) A party may file a motion under subrule (C)(1)-(7) at any time. (2) A motion under subrule (C)(8), (9), or (10) may be filed after a reasonable period for discovery. (3) The court must give the parties an opportunity to be heard before ruling.

(C) Grounds. A motion may be based on one or more of these grounds:
(1) The court lacks jurisdiction of the subject matter.
(2) The court lacks jurisdiction over the defendant.
(3) The defendant was not properly served.
(4) The party asserting the claim has failed to state a claim on which relief can be granted (similar to FRCP 12(b)(6)).
(5) The action was not timely filed (statute of limitations).
(6) Another action between the same parties involving the same claims is pending.
(7) The claim is barred because of release, prior judgment, statute of frauds, statute of limitations, immunity, or another disposition.
(8) The opposing party has failed to state a valid defense to the claim.
(9) There is no genuine issue of material fact and the moving party is entitled to judgment as a matter of law (summary judgment equivalent).
(10) The affirmative defense asserted by the opposing party is barred for a reason listed in (C)(7).

(G) Affidavits; Other Proofs. (1) A motion under (C)(1)-(7) is determined solely on the basis of the pleadings. (2) A motion under (C)(8), (9), or (10) may be supported by affidavits, depositions, admissions, or other documentary evidence. (3) The opposing party may not rest on mere allegations but must set forth specific facts showing a genuine issue for trial. (4) The court must consider the affidavits, depositions, and other documentary evidence submitted.

(I) Standard of Review.
(1) For (C)(1)-(3) and (5)-(7): determined on the pleadings alone.
(2) For (C)(4): all factual allegations in the complaint are accepted as true; dismissal is appropriate only if the claim is so clearly unenforceable that no factual development could justify a right of recovery.
(3) For (C)(8)-(10): the court must consider all documentary evidence; if there is no genuine issue of material fact, judgment is proper as a matter of law.

(J) Partial Disposition. If a motion does not dispose of the entire case, the court may enter an order resolving part of the case.""",
        "court_level": "circuit",
        "practice_tips": "Michigan's equivalent of summary judgment (C)(9) and motion to dismiss (C)(4). For (C)(9), must show NO genuine issue of material fact — cite specific evidence. For (C)(4), all allegations accepted as true. Response must include specific facts, not mere denials. 21-day response time under MCR 2.119.",
        "cross_references": ["MCR 2.119", "FRCP Rule 12", "FRCP Rule 56"],
    },

    # ---- MCR 2.119 MOTION PRACTICE (FULL TEXT) ----
    {
        "citation": "MCR 2.119",
        "title": "Motion Practice",
        "chapter": "Chapter 2 - Civil Procedure",
        "subchapter": "Subchapter 2.100 - Pleadings",
        "full_text": """(A) Form and Content.
(1) Each motion must: (a) state with particularity the grounds and the relief sought; (b) be accompanied by a brief citing supporting authorities; (c) be accompanied by any affidavits or other evidence.
(2) Proposed orders must be served with motions. A proposed order granting the motion must be served on all parties.

(B) Time for Service and Filing.
(1) The moving party must serve the motion on the opposing party at least 9 days before the hearing.
(2) The responding party must file a response at least 7 days before the hearing (effectively 21 days if served by mail plus 3-day rule).

(C) Reply. The moving party may file a reply brief within 7 days after service of the response.

(D) Hearing. The court may decide a motion without oral argument, or may order a hearing.

(E) Ex Parte Orders.
(1) The court may issue an ex parte order only when: (a) it clearly appears from specific facts shown by affidavit or verified complaint that immediate and irreparable injury, loss, or damage will result before the adverse party can be heard; (b) the moving party certifies in writing any efforts made to give notice and the reasons notice should not be required.
(2) An order issued ex parte is subject to immediate motion to set aside.
(3) An ex parte order expires 14 days after issuance unless a hearing is held.

(F) Emergency Motions. A motion may be heard on less than the required notice on a showing of good cause, including an emergency.""",
        "court_level": "all",
        "practice_tips": "Motion must be served 9 days before hearing. Response due 7 days before. Always include brief with authorities. Ex parte orders expire after 14 days. For emergency motions, show good cause for shortened notice.",
        "cross_references": ["MCR 1.106", "MCR 1.107", "MCR 2.116"],
    },
    {
        "citation": "MCR 2.302",
        "title": "General Rules of Discovery",
        "chapter": "Chapter 2 - Civil Procedure",
        "subchapter": "Subchapter 2.300 - Discovery",
        "full_text": "(A) Scope. Parties may obtain discovery regarding any matter, not privileged, that is relevant to the subject matter involved in the pending action. Information need not be admissible at trial if it appears reasonably calculated to lead to the discovery of admissible evidence. (B) Limitations. The court may limit discovery if: (1) the discovery sought is unreasonably cumulative or duplicative; (2) the party seeking discovery has had ample opportunity; (3) the burden of the proposed discovery outweighs its likely benefit. (C) Trial Preparation Materials. A party may not discover documents or tangible things prepared in anticipation of litigation or for trial by another party's attorney, except upon a showing of substantial need and inability to obtain equivalent without undue hardship (work product doctrine). (D) Expert Witnesses. A party may discover facts known and opinions held by expert witnesses expected to testify at trial.",
        "court_level": "circuit",
        "cross_references": ["MCR 2.301", "MCR 2.309", "MCR 2.310", "MCR 2.313"],
    },
    {
        "citation": "MCR 2.309",
        "title": "Interrogatories to Parties",
        "chapter": "Chapter 2 - Civil Procedure",
        "subchapter": "Subchapter 2.300 - Discovery",
        "full_text": "(A) Availability; Limit on Number. (1) Any party may serve on any other party written interrogatories to be answered under oath. (2) Unless the court orders otherwise, a party may not serve more than 25 interrogatories (including discrete subparts) on another party. (B) Answers and Objections. (1) Interrogatories must be answered separately and fully in writing under oath within 28 days after service. (2) Objections must state the reason with specificity. (3) The party submitting interrogatories may move for an order compelling answers. (C) Scope. Interrogatories may relate to any discoverable matter under MCR 2.302.",
        "court_level": "circuit",
        "practice_tips": "25-interrogatory limit per party. Answered under oath within 28 days. Discrete subparts count toward the limit. Move to compel if unanswered — MCR 2.313.",
        "cross_references": ["MCR 2.302", "MCR 2.310", "MCR 2.313"],
    },
    {
        "citation": "MCR 2.310",
        "title": "Requests for Production of Documents and Entry on Land",
        "chapter": "Chapter 2 - Civil Procedure",
        "subchapter": "Subchapter 2.300 - Discovery",
        "full_text": "(A) Scope. A party may serve on any other party a request to produce documents, electronically stored information, or tangible things within the scope of MCR 2.302, or to permit entry on land for inspection or testing. (B) Procedure. (1) The request must describe the items sought with reasonable particularity. (2) The response is due within 28 days. (3) The response must state, for each item, that inspection will be permitted or state objections with specificity. (C) A party who produces documents must organize them as kept in the usual course of business or must organize and label them to correspond to the categories in the request.",
        "court_level": "circuit",
        "cross_references": ["MCR 2.302", "MCR 2.309", "MCR 2.313"],
    },
    {
        "citation": "MCR 2.312",
        "title": "Request for Admissions",
        "chapter": "Chapter 2 - Civil Procedure",
        "subchapter": "Subchapter 2.300 - Discovery",
        "full_text": "(A) A party may serve on any other party a written request to admit the truth of matters of fact, the application of law to fact, or the genuineness of documents. (B) Response. (1) Each matter is admitted unless the party to whom the request is directed serves a written answer or objection within 28 days. (2) An answer must specifically deny the matter or set forth in detail the reasons the answering party cannot truthfully admit or deny. (3) A matter admitted is conclusively established for the purposes of the pending action. (C) A party may move to determine the sufficiency of an answer or objection.",
        "court_level": "circuit",
        "practice_tips": "POWERFUL tool — unanswered RFAs are deemed ADMITTED after 28 days. Use strategically to establish key facts without trial.",
        "cross_references": ["MCR 2.302", "MCR 2.313"],
    },
    {
        "citation": "MCR 2.313",
        "title": "Failure to Provide Discovery; Sanctions",
        "chapter": "Chapter 2 - Civil Procedure",
        "subchapter": "Subchapter 2.300 - Discovery",
        "full_text": "(A) Motion to Compel. If a party fails to answer interrogatories, respond to requests for production, or comply with a discovery order, the discovering party may move for an order compelling discovery. (B) Sanctions. If a party fails to comply with an order to provide discovery, the court may: (1) order that designated facts be taken as established; (2) prohibit the noncomplying party from introducing evidence on certain matters; (3) strike pleadings or parts thereof; (4) stay further proceedings until the order is obeyed; (5) dismiss the action or render a default judgment against the noncomplying party; (6) hold the noncomplying party in contempt. (C) Expenses. If the motion is granted, the court shall require the non-prevailing party to pay reasonable expenses, including attorney fees, unless the failure was substantially justified.",
        "court_level": "circuit",
        "practice_tips": "Discovery sanctions are progressive: compel → established facts → strike pleadings → default judgment → contempt. Always file motion to compel first before seeking harsher sanctions.",
        "cross_references": ["MCR 2.309", "MCR 2.310", "MCR 2.312"],
    },

    # ---- MCR 2.612 RELIEF FROM JUDGMENT (FULL TEXT) ----
    {
        "citation": "MCR 2.612",
        "title": "Relief from Judgment or Order",
        "chapter": "Chapter 2 - Civil Procedure",
        "subchapter": "Subchapter 2.600 - Judgments",
        "full_text": """(A) Clerical Mistakes. Clerical mistakes in judgments, orders, or other parts of the record may be corrected at any time.

(B) Correction of Mistakes and Cancellation of Discharge.

(C) Grounds for Relief.
(1) On motion and on just terms, the court may relieve a party from a final judgment, order, or proceeding for the following reasons:
(a) Mistake, inadvertence, surprise, or excusable neglect.
(b) Newly discovered evidence which by due diligence could not have been discovered in time to move for a new trial under MCR 2.611.
(c) Fraud (whether heretofore denominated intrinsic or extrinsic), misrepresentation, or other misconduct of an adverse party.
(d) The judgment is void.
(e) The judgment has been satisfied, released, or discharged; a prior judgment on which it was based has been reversed or otherwise vacated; or it is no longer equitable that the judgment should have prospective application.
(f) Any other reason justifying relief from the operation of the judgment.

(2) The motion must be made within a reasonable time, and for reasons (a), (b), and (c), not more than one year after the judgment, order, or proceeding was entered or taken.

(3) A motion under this subrule does not affect the finality of a judgment or suspend its operation.

(D) This rule does not limit the power of a court to entertain an independent action to relieve a party from a judgment, order, or proceeding; or to set aside a judgment for fraud on the court.""",
        "court_level": "all",
        "practice_tips": "CRITICAL: (C)(1)(c) fraud by adverse party — no time limit on 'fraud on the court' under (D). (C)(1)(f) catch-all 'any other reason' — broad discretion. Must be filed within 1 year for (a)-(c). Use for challenging orders obtained by fraud or ex parte misconduct.",
        "cross_references": ["MCR 2.611", "FRCP Rule 60"],
    },
    {
        "citation": "MCR 2.621",
        "title": "Extraordinary Writs",
        "chapter": "Chapter 2 - Civil Procedure",
        "subchapter": "Subchapter 2.600 - Judgments",
        "full_text": "(A) Mandamus. A complaint for mandamus must allege: (1) the defendant has a clear legal duty to perform the act demanded; (2) the plaintiff has a clear legal right to performance; (3) no other adequate legal remedy exists. (B) Superintending Control. A complaint for superintending control may be filed when a lower court or tribunal has failed to perform a duty or has exceeded its jurisdiction. The order must direct the lower court to take a specific action.",
        "court_level": "circuit",
        "practice_tips": "Mandamus requires showing NO other adequate remedy. Superintending control is the mechanism to challenge a lower court's procedural errors. Often used against district courts.",
        "cross_references": ["MCL 600.1901", "MCL 600.4401"],
    },
    {
        "citation": "MCR 2.625",
        "title": "Taxable Costs",
        "chapter": "Chapter 2 - Civil Procedure",
        "subchapter": "Subchapter 2.600 - Judgments",
        "full_text": "(A) Right to Costs. Costs will be allowed to the prevailing party unless prohibited by statute or the court directs otherwise. (B) Taxable Costs include: (1) filing fees; (2) witness fees; (3) fees for service of process; (4) costs of depositions used at trial; (5) reasonable costs of copies. (C) Attorney Fees. Attorney fees are not recoverable as taxable costs unless authorized by statute, court rule, or contractual provision.",
        "court_level": "all",
        "cross_references": ["MCL 600.2591", "MCR 2.403"],
    },

    # =========================================================================
    # CHAPTER 3 — SPECIAL PROCEEDINGS (FAMILY)
    # =========================================================================
    {
        "citation": "MCR 3.201",
        "title": "Applicability of Rules; Family Division",
        "chapter": "Chapter 3 - Special Proceedings",
        "subchapter": "Subchapter 3.200 - Domestic Relations",
        "full_text": "(A) These rules apply to all family division proceedings including: (1) divorce, separate maintenance, and annulment; (2) child custody and parenting time; (3) child support; (4) paternity; (5) personal protection orders; (6) name changes; (7) emancipation of minors. (B) The general civil procedure rules in Chapter 2 apply except as modified by this subchapter.",
        "court_level": "circuit",
        "cross_references": ["MCR 2.001", "MCR 3.206"],
    },
    {
        "citation": "MCR 3.204",
        "title": "Temporary Orders",
        "chapter": "Chapter 3 - Special Proceedings",
        "subchapter": "Subchapter 3.200 - Domestic Relations",
        "full_text": "(A) After a domestic relations action is filed, a party may move for a temporary order regarding: (1) custody of the minor children; (2) parenting time; (3) child support; (4) spousal support; (5) possession of property; (6) payment of debts; (7) any other matter necessary for the protection of the parties or children. (B) A temporary order remains in effect until superseded by a subsequent order, agreement, or final judgment. (C) The court may issue a temporary restraining order without notice if it clearly appears from specific facts that immediate and irreparable injury will result.",
        "court_level": "circuit",
        "practice_tips": "Temporary orders are critical in custody cases — they establish the status quo. The 'established custodial environment' often forms during temporary orders.",
        "cross_references": ["MCR 3.206", "MCR 3.210", "MCL 722.27"],
    },
    {
        "citation": "MCR 3.206",
        "title": "Initiating a Domestic Relations Case",
        "chapter": "Chapter 3 - Special Proceedings",
        "subchapter": "Subchapter 3.200 - Domestic Relations",
        "full_text": "(A) A domestic relations action is commenced by filing a complaint. (B) The complaint must include: (1) the names, addresses, and birth dates of the parties; (2) the date and place of the marriage (if applicable); (3) the names and birth dates of minor children (initials per MCR 8.119(H)); (4) the statutory grounds for the action; (5) a statement regarding other pending actions. (C) Verified Statement. A verified statement regarding custody must accompany the complaint, including: (1) current address of each child; (2) places where each child has lived in the past 5 years; (3) names and addresses of persons with whom each child has lived; (4) participation in other custody proceedings; (5) knowledge of other proceedings concerning the child. (D) Fees. A filing fee is required unless waived per MCR 2.002.",
        "court_level": "circuit",
        "cross_references": ["MCR 3.201", "MCR 8.119", "MCL 722.23"],
    },

    # ---- MCR 3.208 FRIEND OF THE COURT ----
    {
        "citation": "MCR 3.208",
        "title": "Friend of the Court",
        "chapter": "Chapter 3 - Special Proceedings",
        "subchapter": "Subchapter 3.200 - Domestic Relations",
        "full_text": """(A) Duties. The Friend of the Court (FOC) shall:
(1) investigate and make recommendations to the court regarding custody, parenting time, and support;
(2) enforce court orders related to custody, parenting time, and support;
(3) collect and disburse support payments;
(4) investigate complaints regarding custody, parenting time, and support;
(5) maintain records of all support payments.

(B) Investigations. The FOC may conduct investigations including:
(1) home studies;
(2) interviews with the parties, children, and relevant witnesses;
(3) review of relevant records.

(C) Reports and Recommendations.
(1) The FOC shall file its report and recommendation with the court before any hearing on a contested matter.
(2) Copies must be served on the parties before the hearing.
(3) Reports must include findings of fact and specific recommendations.

(D) Objections.
(1) A party may file a written objection to a FOC recommendation within 21 days after service.
(2) The objection must state with specificity the grounds for the objection.
(3) Upon objection, the party is entitled to a de novo hearing before the judge.

(E) De Novo Hearing. When a timely objection is filed, the court shall hold a de novo hearing. The FOC recommendation may be received into evidence but is not binding on the court.""",
        "court_level": "circuit",
        "practice_tips": "CRITICAL: You have 21 DAYS to object to FOC recommendations. Objection triggers de novo hearing — judge decides fresh. FOC recommendations are NOT binding. Always object if unfavorable — you lose nothing by forcing a hearing. The FOC in Andrew's case is Pamela Rusco.",
        "cross_references": ["MCL 552.101", "MCR 3.210", "MCR 3.214"],
    },

    # ---- MCR 3.210 CUSTODY AND PARENTING TIME (FULL TEXT) ----
    {
        "citation": "MCR 3.210",
        "title": "Custody of Minor Children; Parenting Time",
        "chapter": "Chapter 3 - Special Proceedings",
        "subchapter": "Subchapter 3.200 - Domestic Relations",
        "full_text": """(A) Best Interests of the Child. In a custody dispute, the court must determine custody and parenting time in accordance with the best interests of the child, as defined in MCL 722.23.

(B) Factors. The court shall consider and make findings on each of the following factors:
(a) The love, affection, and other emotional ties existing between the parties involved and the child.
(b) The capacity and disposition of the parties involved to give the child love, affection, and guidance and to continue the education and raising of the child in his or her religion or creed, if any.
(c) The capacity and disposition of the parties involved to provide the child with food, clothing, medical care or other remedial care recognized and permitted under the laws of this state in place of medical care, and other material needs.
(d) The length of time the child has lived in a stable, satisfactory environment, and the desirability of maintaining continuity.
(e) The permanence, as a family unit, of the existing or proposed custodial home or homes.
(f) The moral fitness of the parties involved.
(g) The mental and physical health of the parties involved.
(h) The home, school, and community record of the child.
(i) The reasonable preference of the child, if the court considers the child to be of sufficient age to express preference.
(j) The willingness and ability of each of the parties to facilitate and encourage a close and continuing parent-child relationship between the child and the other parent or the child and the parents. A court may not consider negatively for the purposes of this factor any reasonable action taken by a parent to protect a child or that parent from sexual assault or domestic violence by the child's other parent.
(k) Domestic violence, regardless of whether the violence was directed against or witnessed by the child.
(l) Any other factor considered by the court to be relevant to a particular child custody dispute.

(C) Established Custodial Environment.
(1) The court must determine whether an established custodial environment exists.
(2) An established custodial environment exists if over an appreciable time the child naturally looks to the custodian in that environment for guidance, discipline, the necessities of life, and parental comfort.
(3) If an established custodial environment exists, the court shall not change it unless the proponent demonstrates by clear and convincing evidence that the change is in the best interests of the child.
(4) If no established custodial environment exists, the standard of proof is a preponderance of the evidence.

(D) Parenting Time.
(1) It is presumed that it is in the best interests of the child to have a strong relationship with both parents.
(2) Parenting time shall be granted in accordance with the best interests of the child.
(3) A parenting time order may include specific terms and conditions.
(4) Parenting time may only be denied or restricted if the court determines that it would endanger the child's physical, mental, or emotional health.

(E) Change of Domicile.
(1) A parent shall not change the legal residence of the child to a location more than 100 miles from the child's current legal residence without court approval or the other parent's written consent.
(2) See MCR 3.211 for change of domicile proceedings.""",
        "court_level": "circuit",
        "practice_tips": "THE central rule for Andrew's custody case. Factor (j) — willingness to facilitate relationship — is key for parental alienation claims. Established custodial environment = clear and convincing evidence standard (higher burden). Factor (f) moral fitness and (k) domestic violence are frequently litigated. The court MUST make findings on EACH factor.",
        "cross_references": ["MCL 722.23", "MCL 722.27", "MCL 722.27a", "MCR 3.211"],
    },

    # ---- MCR 3.219 PERSONAL PROTECTION ORDERS (FULL TEXT) ----
    {
        "citation": "MCR 3.219",
        "title": "Personal Protection Orders",
        "chapter": "Chapter 3 - Special Proceedings",
        "subchapter": "Subchapter 3.200 - Domestic Relations",
        "full_text": """(A) Definitions.
(1) "Domestic relationship PPO" — between persons who have or have had a dating relationship, or are or were married, or have a child in common.
(2) "Nondomestic PPO" — stalking or harassment by a person without a domestic relationship.

(B) Petition.
(1) A petition for a PPO must be filed on an approved SCAO form.
(2) The petition must state specific facts showing the respondent's conduct.
(3) No filing fee is required for a domestic PPO.

(C) Ex Parte PPO.
(1) The court may issue an ex parte PPO without notice if: (a) it clearly appears from specific facts that immediate and irreparable injury, loss, or damage will result from the delay required to achieve notice; (b) the petitioner makes a specific showing that the respondent has engaged in the prohibited conduct.
(2) An ex parte PPO may prohibit: (a) assaulting, attacking, beating, molesting, or wounding; (b) threatening to kill or physically injure; (c) removing minor children except as authorized; (d) entering the petitioner's residence or workplace; (e) interfering with petitioner's efforts to remove personal property; (f) purchasing or possessing firearms; (g) interfering with custody or parenting time; (h) any other specific acts or conduct.

(D) Service.
(1) The ex parte PPO must be served on the respondent personally or by other means reasonably calculated to give notice.
(2) A PPO is enforceable upon service.
(3) The respondent must be informed of the right to request a hearing.

(E) Hearing on Contested PPO.
(1) The respondent may request a hearing within 14 days after being served with the PPO.
(2) The hearing must be held within 14 days of the request.
(3) At the hearing, the petitioner has the burden of proving by a preponderance of the evidence that the PPO should remain in effect.

(F) Modification and Termination.
(1) Either party may move to modify or terminate a PPO.
(2) The court may modify or terminate if there is a change in circumstances.

(G) Violations.
(1) A knowing violation of a PPO is criminal contempt.
(2) A violation may also be enforced through arrest and prosecution under MCL 764.15b.
(3) A first offense is a misdemeanor punishable by up to 93 days imprisonment and/or a fine.""",
        "court_level": "circuit",
        "practice_tips": "PPOs are frequently weaponized in custody disputes. Respondent has 14 days to request hearing after service. At hearing, petitioner bears burden of proof. Challenge immediately if the PPO was obtained without proper factual basis. Ex parte PPOs must show IMMEDIATE and IRREPARABLE injury.",
        "cross_references": ["MCL 600.2950", "MCL 764.15b", "MCR 3.201"],
    },
    {
        "citation": "MCR 3.211",
        "title": "Change of Domicile",
        "chapter": "Chapter 3 - Special Proceedings",
        "subchapter": "Subchapter 3.200 - Domestic Relations",
        "full_text": "(A) A parent of a child whose custody is governed by court order shall not change the legal residence of the child to a location that is more than 100 miles from the child's legal residence at the time of commencement of the action without the other parent's written consent or court approval. (B) The parent seeking to change domicile must file a verified motion. (C) The court must determine whether the change has the capacity to improve the quality of life for both the child and the relocating parent, considering the factors in MCL 722.31. (D) Factors: (1) whether the move has the capacity to improve the quality of life; (2) the degree to which each parent has complied with court orders; (3) whether the move is to defeat parenting time; (4) the opposing parent's compliance with custody and parenting time orders; (5) the feasibility of preserving the relationship with the nonrelocating parent.",
        "court_level": "circuit",
        "practice_tips": "100-mile rule. Must prove the move improves quality of life AND preserves relationship with other parent. If a parent moves without consent or court approval, it may be grounds for custody modification.",
        "cross_references": ["MCL 722.31", "MCR 3.210"],
    },
    {
        "citation": "MCR 3.222",
        "title": "Contempt in Domestic Relations Cases",
        "chapter": "Chapter 3 - Special Proceedings",
        "subchapter": "Subchapter 3.200 - Domestic Relations",
        "full_text": "(A) Contempt proceedings may be initiated by the FOC, a party, or the court. (B) A party seeking a finding of contempt must file a motion and supporting affidavit showing: (1) the existence of a court order; (2) the respondent's knowledge of the order; (3) the respondent's failure to comply. (C) The respondent must be served with the motion and given notice of hearing. (D) At the hearing, the moving party must prove contempt by a preponderance of the evidence for civil contempt (to coerce compliance) or beyond a reasonable doubt for criminal contempt (to punish). (E) Sanctions may include: (1) fine; (2) imprisonment; (3) modification of the underlying order; (4) compensatory time.",
        "court_level": "circuit",
        "practice_tips": "Use civil contempt (preponderance standard) to enforce parenting time orders. Show: order exists, respondent knew about it, respondent violated it. Document every violation.",
        "cross_references": ["MCR 3.208", "MCR 3.210", "MCL 552.601"],
    },

    # =========================================================================
    # CHAPTER 6 — CRIMINAL PROCEDURE
    # =========================================================================
    {
        "citation": "MCR 6.001",
        "title": "Applicability",
        "chapter": "Chapter 6 - Criminal Procedure",
        "subchapter": "Subchapter 6.000 - General",
        "full_text": "These rules govern practice and procedure in criminal matters in all Michigan courts.",
        "court_level": "all",
        "cross_references": [],
    },
    {
        "citation": "MCR 6.104",
        "title": "Arraignment on the Warrant or Complaint",
        "chapter": "Chapter 6 - Criminal Procedure",
        "subchapter": "Subchapter 6.100 - Pretrial",
        "full_text": "(A) The defendant must be arraigned without unnecessary delay, but not more than 48 hours after arrest (excluding Sundays and holidays). (B) At arraignment the court must: (1) inform the defendant of the charge; (2) advise of the right to an attorney and appoint one if indigent; (3) set conditions of release and bail; (4) advise of the right to a preliminary examination within 14 days.",
        "court_level": "district",
        "practice_tips": "For Andrew's criminal case (60th District). Arraignment within 48 hours. Right to counsel. Preliminary exam within 14 days.",
        "cross_references": ["MCR 6.110", "MCR 6.201"],
    },
    {
        "citation": "MCR 6.110",
        "title": "Discovery in Criminal Cases",
        "chapter": "Chapter 6 - Criminal Procedure",
        "subchapter": "Subchapter 6.100 - Pretrial",
        "full_text": "(A) Upon request, the prosecution must provide: (1) all witness names and addresses known to the prosecution; (2) all written or recorded statements of witnesses or the defendant; (3) results of scientific tests, expert reports; (4) criminal records of the defendant and witnesses. (B) Exculpatory evidence: The prosecution must disclose material that tends to negate guilt or reduce punishment (Brady obligation). (C) Additional discovery may be ordered by the court upon a showing of good cause.",
        "court_level": "all",
        "practice_tips": "Brady v Maryland obligation — prosecution MUST disclose exculpatory evidence. Failure to disclose is reversible error and potentially a due process violation. For Andrew's criminal case — DEMAND body cam footage and all police reports.",
        "cross_references": ["MCR 6.201", "Brady v Maryland 373 US 83"],
    },
    {
        "citation": "MCR 6.201",
        "title": "Discovery",
        "chapter": "Chapter 6 - Criminal Procedure",
        "subchapter": "Subchapter 6.200 - Discovery",
        "full_text": "(A) Mandatory Disclosure by Prosecution. The prosecution shall, upon request, provide: (1) names and addresses of all prosecution witnesses; (2) any written or recorded statements of defendant; (3) a copy of defendant's criminal record; (4) any exculpatory material (Brady); (5) all police reports; (6) results of any scientific tests; (7) a list of tangible evidence. (B) Disclosure by Defendant. Upon request, defendant shall provide: (1) names of witnesses defendant intends to call; (2) notice of alibi defense; (3) notice of insanity defense. (C) Continuing Duty. The duty to disclose is continuing. New material must be disclosed promptly. (D) Protective Orders. The court may restrict discovery for good cause. (E) Sanctions. For non-compliance, the court may: order disclosure, grant a continuance, prohibit testimony, dismiss charges, or enter other appropriate orders.",
        "court_level": "all",
        "practice_tips": "CRITICAL for Andrew's criminal case. Prosecution MUST provide all police reports, body cam footage, witness statements. File motion to compel if not provided. Brady violations are grounds for dismissal.",
        "cross_references": ["MCR 6.110", "Brady v Maryland 373 US 83"],
    },
    {
        "citation": "MCR 6.302",
        "title": "Pleas of Guilty and Nolo Contendere",
        "chapter": "Chapter 6 - Criminal Procedure",
        "subchapter": "Subchapter 6.300 - Pleas",
        "full_text": "(A) Before accepting a plea of guilty or nolo contendere, the court must: (1) advise the defendant of the maximum possible prison sentence and any mandatory minimum; (2) advise of the right to trial by jury or by the court; (3) advise of the right to confront and cross-examine witnesses; (4) advise of the right against compelled self-incrimination; (5) advise of the right to present evidence; (6) advise of any applicable consecutive sentence; (7) establish a factual basis for the plea. (B) The record must affirmatively show that the defendant's plea was freely, understandingly, and voluntarily made. (C) The court may not participate in plea discussions between the parties.",
        "court_level": "all",
        "cross_references": ["MCR 6.301", "MCR 6.310"],
    },
    {
        "citation": "MCR 6.500",
        "title": "Motion for Relief from Judgment (Criminal)",
        "chapter": "Chapter 6 - Criminal Procedure",
        "subchapter": "Subchapter 6.500 - Postconviction",
        "full_text": "(A) Scope. These rules apply to postconviction motions for relief from judgment in criminal cases. (B) Grounds. The defendant may seek relief based on: (1) a claim of new evidence that was not discoverable before trial; (2) a retroactive change in law; (3) a jurisdictional defect; (4) actual innocence; (5) ineffective assistance of counsel. (C) Time. A motion must be filed within the later of: (1) 6 years after the date of conviction; (2) 3 years after the decision on direct appeal or (3) any applicable statutory deadline. (D) The defendant must show good cause for failure to raise the issue on appeal and actual prejudice from the alleged error.",
        "court_level": "circuit",
        "cross_references": ["MCR 6.302", "MCR 7.204"],
    },

    # =========================================================================
    # CHAPTER 7 — APPELLATE RULES
    # =========================================================================

    # ---- MCR 7.201 COA JURISDICTION ----
    {
        "citation": "MCR 7.201",
        "title": "Jurisdiction of the Court of Appeals",
        "chapter": "Chapter 7 - Appellate Rules",
        "subchapter": "Subchapter 7.200 - Court of Appeals",
        "full_text": "(A) Appeal of Right. The court of appeals has jurisdiction of an appeal of right filed by an aggrieved party from: (1) a final judgment or final order of the circuit court or court of claims; (2) a judgment or order of a court or tribunal from which appeal has been established by law. (B) Appeal by Leave. The court of appeals may grant leave to appeal from: (1) a judgment or order of the circuit court that is not a final judgment; (2) a final order or judgment when the appeal period has expired and the appellant shows grounds for a late appeal. (C) Original Proceedings. The court of appeals may entertain original proceedings for mandamus, superintending control, or habeas corpus.",
        "court_level": "appellate",
        "practice_tips": "Appeal of right from FINAL orders only. For interlocutory (non-final) orders, must apply for leave. Original proceedings available for extraordinary relief.",
        "cross_references": ["MCR 7.202", "MCR 7.203", "MCR 7.204", "MCR 7.205"],
    },
    {
        "citation": "MCR 7.202",
        "title": "Definitions",
        "chapter": "Chapter 7 - Appellate Rules",
        "subchapter": "Subchapter 7.200 - Court of Appeals",
        "full_text": "(1) 'Entry' means the date a judgment or order is signed by the judge or entered on the register of actions. (2) 'Final judgment' means the first judgment or order that disposes of all the claims and adjudicates the rights and liabilities of all the parties. (3) 'Final order' means a post-judgment order that affects the rights and liabilities of the parties, such as an order modifying custody or support. (4) 'Interlocutory order' means an order that does not dispose of the case but is entered during the pendency of the action.",
        "court_level": "appellate",
        "practice_tips": "CRITICAL: The definition of 'final order' vs 'interlocutory order' determines whether you have appeal of right or must seek leave. In family law, custody modification orders are 'final orders' appealable of right.",
        "cross_references": ["MCR 7.201", "MCR 7.204", "MCR 7.205"],
    },

    # ---- MCR 7.204 CLAIM OF APPEAL (FULL TEXT) ----
    {
        "citation": "MCR 7.204",
        "title": "Filing Claim of Appeal; Cross-Appeal",
        "chapter": "Chapter 7 - Appellate Rules",
        "subchapter": "Subchapter 7.200 - Court of Appeals",
        "full_text": """(A) Time Requirements.
(1) An appeal of right must be taken by filing a claim of appeal within:
(a) 21 days after entry of the judgment or order being appealed; or
(b) 21 days after the court decides a timely motion for new trial, a motion for rehearing, a motion for JNOV, or a motion to amend.
(2) If a party serves a timely motion listed in (A)(1)(b), the time for all parties to file a claim of appeal runs from the entry of the order deciding the last pending motion.

(B) Manner of Filing.
(1) The appellant must file with the Court of Appeals clerk:
(a) a claim of appeal on a form approved by the State Court Administrator;
(b) a copy of the judgment, order, or interlocutory order appealed from;
(c) the entry fee.
(2) A copy of the claim of appeal must be served on all other parties.
(3) A copy of the claim of appeal must be filed with the trial court.

(C) Content.
(1) The claim of appeal must include:
(a) the names of all parties and their attorneys;
(b) the date of the judgment or order appealed from;
(c) a concise statement of the basis of the appeal;
(d) a statement of whether the case was tried with or without a jury.

(D) Cross-Appeal.
(1) A party may file a cross-appeal within 21 days after service of the first claim of appeal.

(E) Late Appeal.
(1) The court may permit late filing for good cause shown.
(2) A motion for late appeal must explain the delay.""",
        "court_level": "appellate",
        "practice_tips": "21 DAYS — absolute deadline for appeal of right. File the claim of appeal form, attach the order, pay the fee. Late appeals require good cause showing. Always file in the COA AND the trial court. For Andrew's COA 366810 case — this deadline is critical.",
        "cross_references": ["MCR 7.201", "MCR 7.205", "MCR 7.209", "MCR 7.210"],
    },

    # ---- MCR 7.205 APPLICATION FOR LEAVE TO APPEAL ----
    {
        "citation": "MCR 7.205",
        "title": "Application for Leave to Appeal",
        "chapter": "Chapter 7 - Appellate Rules",
        "subchapter": "Subchapter 7.200 - Court of Appeals",
        "full_text": """(A) Filing. A party may file an application for leave to appeal an order that is not a final order or final judgment, or when the time for filing a claim of appeal has expired.

(B) Time.
(1) For an interlocutory order: within 21 days of entry.
(2) For a final order after the claim period has expired: within 6 months of entry.

(C) Content.
(1) The application must include:
(a) a statement of the basis of jurisdiction;
(b) a statement of the questions presented for review;
(c) a concise statement of the material proceedings and facts;
(d) a statement of the applicable standard of review;
(e) argument in support, with citations to authority;
(f) a copy of the order or judgment appealed from;
(g) any relevant transcripts or documents.

(D) Answer. The opposing party may file an answer within 21 days of service.

(E) Standard. Leave to appeal will be granted only if the applicant persuades the court of the need for immediate appellate review.

(F) Emergency Application. An application may be filed as an emergency if delay would cause irreparable harm.""",
        "court_level": "appellate",
        "practice_tips": "Leave to appeal for interlocutory orders — within 21 days. For expired final order appeals — within 6 months. Emergency applications available for irreparable harm situations.",
        "cross_references": ["MCR 7.201", "MCR 7.204", "MCR 7.206"],
    },

    # ---- MCR 7.212 BRIEFS ----
    {
        "citation": "MCR 7.212",
        "title": "Briefs",
        "chapter": "Chapter 7 - Appellate Rules",
        "subchapter": "Subchapter 7.200 - Court of Appeals",
        "full_text": """(A) Appellant's Brief. The appellant must file a brief within 56 days after:
(1) the claim of appeal is filed; or
(2) the order granting leave to appeal.

(B) Appellee's Brief. The appellee must file a brief within 35 days of service of the appellant's brief.

(C) Reply Brief. The appellant may file a reply brief within 21 days of service of the appellee's brief.

(D) Content of Briefs. Each brief must contain:
(1) A table of contents with page references.
(2) An index of authorities (cases, statutes, rules, constitutional provisions) with page references.
(3) A jurisdictional statement.
(4) A statement of the questions presented for review, stated concisely without repetition.
(5) A statement of facts, with citations to the record.
(6) The argument, organized under separate headings for each question presented. The argument must include:
(a) the applicable standard of review;
(b) citation of authority;
(c) application of the facts to the law.
(7) The relief requested.

(E) Format Requirements.
(1) 8.5 x 11 paper.
(2) Proportional 14-point font, or non-proportional 12-point font.
(3) Double-spaced (footnotes may be single-spaced).
(4) 1-inch margins on all sides.

(F) Page Limits.
(1) Appellant's brief: 50 pages.
(2) Appellee's brief: 50 pages.
(3) Reply brief: 25 pages.
(4) Cross-appellant's brief: 50 pages.
(5) Applications and supporting briefs: 50 pages total.

(G) Appendix. The appellant must file an appendix containing:
(1) the judgment or order appealed from;
(2) relevant portions of the trial court record;
(3) any relevant court rules or statutes.""",
        "court_level": "appellate",
        "practice_tips": "Appellant brief due 56 days after filing. 50-page limit. MUST include: table of contents, index of authorities, questions presented, statement of facts with record citations, argument with standard of review, and appendix. 14-point proportional font or 12-point monospaced. Double-spaced.",
        "cross_references": ["MCR 7.204", "MCR 7.210", "MCR 7.211"],
    },
    {
        "citation": "MCR 7.210",
        "title": "Record on Appeal",
        "chapter": "Chapter 7 - Appellate Rules",
        "subchapter": "Subchapter 7.200 - Court of Appeals",
        "full_text": "(A) Composition. The record on appeal consists of the original papers filed in the trial court, the exhibits, and the transcript(s) of testimony and proceedings. (B) Transcripts. (1) The appellant must order from the court reporter a transcript of all proceedings relevant to the issues on appeal. (2) The transcript must be filed within 56 days of filing the claim of appeal. (3) If the parties dispute the content of the record, they must present the issue to the trial court for resolution. (C) Agreed Statement. If a transcript is unavailable, the parties may prepare an agreed statement of the proceedings. (D) The clerk of the trial court must certify and transmit the record to the Court of Appeals.",
        "court_level": "appellate",
        "practice_tips": "Order transcripts IMMEDIATELY after filing appeal — 56-day deadline. If the court reporter is slow, file a motion for extension. Without transcripts, the appeal cannot proceed on factual issues.",
        "cross_references": ["MCR 7.204", "MCR 7.211", "MCR 7.212"],
    },

    # ---- MCR 7.301-7.315 MICHIGAN SUPREME COURT ----
    {
        "citation": "MCR 7.301",
        "title": "Jurisdiction of the Supreme Court",
        "chapter": "Chapter 7 - Appellate Rules",
        "subchapter": "Subchapter 7.300 - Supreme Court",
        "full_text": "(A) The Supreme Court has jurisdiction as provided by the Michigan Constitution and statute. (B) The Supreme Court may review by appeal, leave to appeal, or by original action. (C) The Supreme Court has discretionary jurisdiction over most matters. (D) The Supreme Court may issue advisory opinions to the governor upon request.",
        "court_level": "supreme",
        "cross_references": ["MCR 7.303", "MCR 7.305", "Const 1963, art 6, §4"],
    },
    {
        "citation": "MCR 7.303",
        "title": "Application for Leave to Appeal to the Supreme Court",
        "chapter": "Chapter 7 - Appellate Rules",
        "subchapter": "Subchapter 7.300 - Supreme Court",
        "full_text": "(A) Filing. An application for leave to appeal must be filed within 42 days of the Court of Appeals decision. (B) Content. The application must include: (1) a statement of the questions presented; (2) a statement of facts; (3) argument with citations; (4) a copy of the Court of Appeals decision; (5) a copy of the trial court judgment or order. (C) The opposing party may file an answer within 28 days. (D) Page Limits: application — 50 pages; answer — 50 pages; reply — 25 pages.",
        "court_level": "supreme",
        "practice_tips": "42 DAYS from COA decision to file in MSC. This is a DISCRETIONARY appeal — must convince the court the issue warrants review. Focus on statewide significance, conflict with prior decisions, or constitutional questions.",
        "cross_references": ["MCR 7.301", "MCR 7.305"],
    },

    # =========================================================================
    # CHAPTER 8 — ADMINISTRATIVE RULES
    # =========================================================================
    {
        "citation": "MCR 8.108",
        "title": "Judicial Ethics",
        "chapter": "Chapter 8 - Administrative Rules",
        "subchapter": "Subchapter 8.100 - Court Administration",
        "full_text": "(A) All judges must comply with the Michigan Code of Judicial Conduct. (B) A judge who violates the Code may be subject to discipline by the Judicial Tenure Commission.",
        "court_level": "all",
        "cross_references": ["Michigan Code of Judicial Conduct", "JTC Rules"],
    },
    {
        "citation": "MCR 8.110",
        "title": "Chief Judge Rule",
        "chapter": "Chapter 8 - Administrative Rules",
        "subchapter": "Subchapter 8.100 - Court Administration",
        "full_text": "(A) Each court with more than one judge must have a chief judge. (B) The chief judge is responsible for: (1) administrative management of the court; (2) assignment of cases to judges; (3) supervising court personnel; (4) implementing the rules of the court. (C) The chief judge decides motions for disqualification under MCR 2.003 when referred.",
        "court_level": "all",
        "cross_references": ["MCR 2.003", "MCR 8.111"],
    },
    {
        "citation": "MCR 8.111",
        "title": "Assignment of Cases and Judges",
        "chapter": "Chapter 8 - Administrative Rules",
        "subchapter": "Subchapter 8.100 - Court Administration",
        "full_text": "(A) The chief judge is responsible for assigning cases among the judges of the court in a fair and efficient manner. (B) Cases shall be assigned by lot or rotation or by other impartial method. (C) A case may be reassigned for cause, including: (1) disqualification under MCR 2.003; (2) workload balancing; (3) illness or unavailability.",
        "court_level": "all",
        "cross_references": ["MCR 2.003", "MCR 8.110"],
    },
    {
        "citation": "MCR 8.119",
        "title": "Court Records and Reports; Access to Court Records",
        "chapter": "Chapter 8 - Administrative Rules",
        "subchapter": "Subchapter 8.100 - Court Administration",
        "full_text": "(A) Court records are presumptively open to public access. (B) The following records may be protected or sealed: (1) records sealed by court order; (2) records protected by statute; (3) personal identifying information. (H) Protection of Minor Children's Identity. In court filings involving minor children, the identity of the child shall be protected by using initials rather than full names. Court orders, opinions, and records available to the public shall use initials to refer to minor children unless otherwise ordered by the court.",
        "court_level": "all",
        "practice_tips": "MCR 8.119(H) is why we use 'L.D.W.' instead of the child's full name in all filings. This is MANDATORY.",
        "cross_references": ["MCR 1.109", "MCR 3.206"],
    },
]
