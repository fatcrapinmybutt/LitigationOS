"""Federal Rules and Statutes — Static Dataset for LitigationOS.

FRCP (Federal Rules of Civil Procedure), FRE (Federal Rules of Evidence summary),
42 USC §1983/1985/1988, 28 USC jurisdiction, WDMI Local Rules.
Sources: law.cornell.edu, uscode.house.gov, miwd.uscourts.gov — March 2026.
"""

from __future__ import annotations

# =============================================================================
# FEDERAL RULES OF CIVIL PROCEDURE (FRCP) — Key Rules
# =============================================================================
FRCP_RULES: list[dict] = [
    # TITLE II — COMMENCING AN ACTION; SERVICE OF PROCESS
    {"citation": "FRCP Rule 3", "title": "Commencing an Action", "chapter": "Title II - Commencement",
     "full_text": "A civil action is commenced by filing a complaint with the court."},
    {"citation": "FRCP Rule 4", "title": "Summons", "chapter": "Title II - Commencement",
     "full_text": "(a) Contents; Amendments. (b) Issuance. On presentation of a complaint, the clerk must issue a summons. (c) Service. A summons must be served with a copy of the complaint within 90 days after the complaint is filed. (m) Time Limit for Service. If a defendant is not served within 90 days, the court must dismiss the action without prejudice or order that service be made within a specified time.",
     "practice_tips": "90-day service deadline is critical. Failure to serve within 90 days = dismissal without prejudice (but you can re-file)."},
    {"citation": "FRCP Rule 5", "title": "Serving and Filing Pleadings and Other Papers", "chapter": "Title II - Commencement",
     "full_text": "(a) Service: When Required. Every pleading, written motion, and notice filed after the original complaint must be served on every party. (b) Service: How Made. By delivering, mailing, electronic means if consented to, or leaving at the office of the attorney."},

    # TITLE III — PLEADINGS AND MOTIONS
    {"citation": "FRCP Rule 7", "title": "Pleadings Allowed; Motions", "chapter": "Title III - Pleadings",
     "full_text": "(a) Pleadings: (1) complaint; (2) answer to a complaint; (3) answer to a counterclaim; (4) answer to a crossclaim; (5) third-party complaint; (6) answer to a third-party complaint; (7) reply to an answer if ordered. (b) Motions and Other Papers. A request for a court order must be made by motion."},
    {"citation": "FRCP Rule 8", "title": "General Rules of Pleading", "chapter": "Title III - Pleadings",
     "full_text": "(a) Claim for Relief. A pleading that states a claim must contain: (1) a short and plain statement of the grounds for jurisdiction; (2) a short and plain statement of the claim showing that the pleader is entitled to relief; (3) a demand for the relief sought. (d) Pleading to Be Concise and Direct. Each allegation must be simple, concise, and direct.",
     "practice_tips": "Federal pleading standard: must state enough facts to state a claim 'plausible on its face' (Ashcroft v. Iqbal, 556 U.S. 662). Higher than Michigan notice pleading."},
    {"citation": "FRCP Rule 11", "title": "Signing Pleadings; Sanctions", "chapter": "Title III - Pleadings",
     "full_text": "(b) Representations to the Court. By presenting a pleading, motion, or other paper, an attorney or unrepresented party certifies that to the best of the person's knowledge: (1) it is not being presented for any improper purpose; (2) the claims are warranted by existing law or nonfrivolous argument for extension; (3) the factual contentions have evidentiary support; (4) the denials are warranted on the evidence. (c) Sanctions. If the court determines that Rule 11(b) has been violated, it may impose appropriate sanctions.",
     "practice_tips": "Rule 11 sanctions apply to ALL parties — including Emily's attorney. Filing frivolous motions, misrepresenting facts, or pursuing improper purposes violates Rule 11."},
    {"citation": "FRCP Rule 12", "title": "Defenses and Objections", "chapter": "Title III - Pleadings",
     "full_text": "(b) How to Present Defenses. Every defense to a claim must be asserted in the responsive pleading, except: (1) lack of subject-matter jurisdiction; (2) lack of personal jurisdiction; (3) improper venue; (4) insufficient process; (5) insufficient service of process; (6) failure to state a claim upon which relief can be granted; (7) failure to join a party. (c) Motion for Judgment on the Pleadings. (e) Motion for a More Definite Statement. (f) Motion to Strike.",
     "practice_tips": "12(b)(6) = failure to state a claim. Must be plausible on its face (Iqbal/Twombly). For §1983, must identify: (1) person acting under color of state law; (2) deprivation of constitutional right."},
    {"citation": "FRCP Rule 15", "title": "Amended and Supplemental Pleadings", "chapter": "Title III - Pleadings",
     "full_text": "(a) Amendments Before Trial. (1) Amending as a Matter of Course — a party may amend once within 21 days after serving it, or within 21 days after service of a responsive pleading or 12(b) motion. (2) Other Amendments — only with the opposing party's written consent or the court's leave. The court should freely give leave when justice so requires. (c) Relation Back of Amendments — an amendment relates back to the date of the original pleading if it arose out of the same conduct."},

    # TITLE IV — PARTIES
    {"citation": "FRCP Rule 17", "title": "Plaintiff and Defendant; Capacity", "chapter": "Title IV - Parties",
     "full_text": "(a) Real Party in Interest. An action must be prosecuted in the name of the real party in interest."},
    {"citation": "FRCP Rule 20", "title": "Permissive Joinder of Parties", "chapter": "Title IV - Parties",
     "full_text": "(a) Persons Who May Join or Be Joined. Persons may join as plaintiffs or be joined as defendants if: (A) they assert any right to relief jointly, severally, or in the alternative arising out of the same transaction, occurrence, or series of transactions or occurrences; AND (B) any question of law or fact common to all plaintiffs/defendants will arise in the action."},

    # TITLE V — DISCLOSURES AND DISCOVERY
    {"citation": "FRCP Rule 26", "title": "Duty to Disclose; General Discovery Provisions", "chapter": "Title V - Discovery",
     "full_text": "(a) Required Disclosures. (1) Initial Disclosures — each party must disclose: (A) name/contact of individuals likely to have discoverable information; (B) copy or description of documents the party has; (C) computation of damages; (D) insurance agreements. (b) Discovery Scope and Limits. Parties may obtain discovery regarding any nonprivileged matter relevant to any party's claim or defense. (c) Protective Orders. The court may issue protective orders for good cause.",
     "practice_tips": "Federal discovery is BROADER than state. Initial disclosures are mandatory without a request. Relevance is broadly construed."},
    {"citation": "FRCP Rule 30", "title": "Depositions by Oral Examination", "chapter": "Title V - Discovery",
     "full_text": "(a) When a Deposition May Be Taken. A party may depose any person, including a party, without leave of court except as provided in Rule 30(a)(2). (d) Duration. A deposition is limited to 1 day of 7 hours."},
    {"citation": "FRCP Rule 33", "title": "Interrogatories to Parties", "chapter": "Title V - Discovery",
     "full_text": "(a) In General. A party may serve on any other party no more than 25 written interrogatories, including discrete subparts, unless the court orders otherwise. The responding party must answer under oath within 30 days."},
    {"citation": "FRCP Rule 34", "title": "Producing Documents and Tangible Things", "chapter": "Title V - Discovery",
     "full_text": "(a) A party may serve on any other party a request to produce documents, electronically stored information, or tangible things. (b) Procedure. The responding party must respond in writing within 30 days."},
    {"citation": "FRCP Rule 36", "title": "Requests for Admission", "chapter": "Title V - Discovery",
     "full_text": "(a) A party may serve on any other party a request to admit the truth of matters relating to facts, application of law to fact, or opinions about either. (a)(3) The matter is admitted unless, within 30 days, the party serves a written answer or objection."},
    {"citation": "FRCP Rule 37", "title": "Failure to Make Disclosures or to Cooperate in Discovery; Sanctions", "chapter": "Title V - Discovery",
     "full_text": "(a) Motion for an Order Compelling Disclosure or Discovery. If a party fails to make a disclosure or answer a discovery request, the discovering party may move for an order compelling. (b) Failure to Comply with a Court Order — sanctions including: (A) directing matters be taken as established; (B) prohibiting claims or defenses; (C) striking pleadings; (D) staying proceedings; (E) dismissing the action; (F) rendering default judgment; (G) contempt.",
     "practice_tips": "Discovery sanctions can be case-dispositive: default judgment, dismissal, or facts deemed admitted. Powerful enforcement tool."},

    # TITLE VI — TRIALS
    {"citation": "FRCP Rule 50", "title": "Judgment as a Matter of Law", "chapter": "Title VI - Trials",
     "full_text": "(a) After a party has been fully heard on an issue during a jury trial, the court may grant judgment as a matter of law if no legally sufficient evidentiary basis exists for a reasonable jury to find for that party. (b) Renewing the Motion After Trial — within 28 days after entry of judgment."},
    {"citation": "FRCP Rule 52", "title": "Findings and Conclusions by the Court", "chapter": "Title VI - Trials",
     "full_text": "(a) In an action tried on the facts without a jury, the court must find the facts specially and state its conclusions of law separately. Findings of fact must not be set aside unless clearly erroneous."},
    {"citation": "FRCP Rule 56", "title": "Summary Judgment", "chapter": "Title VI - Trials",
     "full_text": "(a) A party may move for summary judgment on all or part of the claim or defense. The court shall grant summary judgment if the movant shows that there is no genuine dispute as to any material fact and the movant is entitled to judgment as a matter of law. (c) Procedures. The motion must be filed at least 30 days before trial.",
     "practice_tips": "Summary judgment in federal court = no genuine dispute of material fact. Standard: evidence viewed in light most favorable to non-movant (Anderson v. Liberty Lobby, 477 U.S. 242)."},

    # TITLE VII — JUDGMENT
    {"citation": "FRCP Rule 59", "title": "New Trial; Altering or Amending a Judgment", "chapter": "Title VII - Judgment",
     "full_text": "(a) After a jury trial, the court may grant a new trial on all or some issues for any reason a new trial has heretofore been granted. (b) Time to File a Motion. A motion for a new trial must be filed no later than 28 days after entry of judgment. (e) Motion to Alter or Amend. A motion to alter or amend a judgment must be filed no later than 28 days after entry."},
    {"citation": "FRCP Rule 60", "title": "Relief from a Judgment or Order", "chapter": "Title VII - Judgment",
     "full_text": "(b) Grounds for Relief. The court may relieve a party from a final judgment for: (1) mistake, inadvertence, surprise, or excusable neglect; (2) newly discovered evidence that could not have been discovered earlier; (3) fraud, misrepresentation, or other misconduct by an opposing party; (4) the judgment is void; (5) the judgment has been satisfied or is based on an earlier judgment that has been reversed; (6) any other reason that justifies relief. (c) Timing. Motions under (1)-(3) must be made within a reasonable time and no more than one year after judgment.",
     "practice_tips": "Federal Rule 60(b)(3) fraud on the court — parallel to MCR 2.612(C)(1)(c). No time limit for fraud on the court (independent action). (4) void judgment — for jurisdictional challenges."},

    # TITLE VIII — PROVISIONAL AND FINAL REMEDIES
    {"citation": "FRCP Rule 65", "title": "Injunctions and Restraining Orders", "chapter": "Title VIII - Remedies",
     "full_text": "(a) Preliminary Injunction. The court may issue a preliminary injunction only on notice to the adverse party. (b) Temporary Restraining Order. The court may issue a TRO without written or oral notice to the adverse party only if specific facts show immediate and irreparable injury. Must state why notice should not be required. Expires in 14 days unless extended."},

    # TITLE IX — SPECIAL PROCEEDINGS
    {"citation": "FRCP Rule 72", "title": "Magistrate Judges", "chapter": "Title IX - Special Proceedings",
     "full_text": "(a) Nondispositive Matters. A magistrate judge may hear pretrial matters not dispositive of a party's claim or defense. The district judge must review de novo any objection. (b) Dispositive Motions. A magistrate judge may only recommend action on dispositive motions. Parties have 14 days to object; district judge reviews de novo."},
]

# =============================================================================
# FEDERAL RULES OF EVIDENCE (FRE) — Key Differences from MRE
# =============================================================================
FRE_RULES: list[dict] = [
    {"citation": "FRE 702", "title": "Expert Testimony (Federal)", "chapter": "FRE",
     "full_text": "A witness who is qualified as an expert may testify in the form of an opinion if the proponent demonstrates to the court that it is more likely than not that: (a) the expert's scientific, technical, or other specialized knowledge will help the trier of fact; (b) the testimony is based on sufficient facts or data; (c) the testimony is the product of reliable principles and methods; (d) the expert's opinion reflects a reliable application of the principles and methods to the facts of the case.",
     "practice_tips": "2023 amendment codified the Daubert standard and added 'more likely than not' burden on proponent. Michigan's MRE 702 adopted Daubert via Gilbert v DaimlerChrysler."},
    {"citation": "FRE 803(6)", "title": "Business Records (Federal)", "chapter": "FRE",
     "full_text": "Records of a regularly conducted activity. A record made at or near the time by a person with knowledge, if kept in the course of a regularly conducted business activity, as shown by a custodian or qualified witness, or by a certification that complies with Rule 902(11) or 902(12).",
     "practice_tips": "Federal allows certification (affidavit) to lay business record foundation — no live witness needed. Use for hospital records, phone records, bank records."},
]

# =============================================================================
# 42 USC §1983 — CIVIL RIGHTS ACT (Primary Federal Claim)
# =============================================================================
FEDERAL_STATUTES: list[dict] = [
    {"citation": "42 USC § 1983", "title": "Civil Action for Deprivation of Rights", "chapter": "Civil Rights",
     "full_text": """Every person who, under color of any statute, ordinance, regulation, custom, or usage, of any State or Territory or the District of Columbia, subjects, or causes to be subjected, any citizen of the United States or other person within the jurisdiction thereof to the deprivation of any rights, privileges, or immunities secured by the Constitution and laws, shall be liable to the party injured in an action at law, suit in equity, or other proper proceeding for redress, except that in any action brought against a judicial officer for an act or omission taken in such officer's judicial capacity, injunctive relief shall not be granted unless a declaratory decree was violated or declaratory relief was unavailable. For the purposes of this section, any Act of Congress applicable exclusively to the District of Columbia shall be considered to be a statute of the District of Columbia.""",
     "practice_tips": "Four elements: (1) person; (2) acting under color of state law; (3) subjects plaintiff to deprivation; (4) of constitutional rights. Judges have absolute immunity for judicial acts but NOT for administrative or non-judicial acts. Conspiracy with private actors (Dennis v Sparks, 449 US 24) pierces immunity."},
    {"citation": "42 USC § 1985", "title": "Conspiracy to Interfere with Civil Rights", "chapter": "Civil Rights",
     "full_text": """(2) Obstructing justice; intimidating party, witness, or juror. If two or more persons in any State or Territory conspire to deter, by force, intimidation, or threat, any party or witness in any court of the United States from attending such court, or from testifying to any matter pending therein, freely, fully, and truthfully, or to injure such party or witness in his person or property on account of his having so attended or testified.
(3) Depriving persons of rights or privileges. If two or more persons in any State or Territory conspire for the purpose of depriving, either directly or indirectly, any person or class of persons of the equal protection of the laws, or of equal privileges and immunities under the laws; the party so injured or deprived may have an action for the recovery of damages against any one or more of the conspirators.""",
     "practice_tips": "§1985(3) conspiracy to deprive civil rights. Elements: (1) conspiracy; (2) for purpose of depriving equal protection; (3) act in furtherance; (4) injury or deprivation. Requires class-based discriminatory animus (gender/race). Father's rights = gender-based discrimination."},
    {"citation": "42 USC § 1988", "title": "Attorney's Fees", "chapter": "Civil Rights",
     "full_text": "(b) In any action or proceeding to enforce a provision of sections 1981, 1981a, 1982, 1983, 1985, and 1986, the court, in its discretion, may allow the prevailing party, other than the United States, a reasonable attorney's fee as part of the costs.",
     "practice_tips": "Prevailing party in §1983 action can recover attorney's fees. Pro se litigants cannot recover 'attorney fees' but can recover costs. Some circuits allow pro se fees at reduced rates."},
    {"citation": "28 USC § 1331", "title": "Federal Question Jurisdiction", "chapter": "Jurisdiction",
     "full_text": "The district courts shall have original jurisdiction of all civil actions arising under the Constitution, laws, or treaties of the United States.",
     "practice_tips": "§1983 claims arise under federal law = automatic federal question jurisdiction. No amount-in-controversy requirement."},
    {"citation": "28 USC § 1332", "title": "Diversity Jurisdiction", "chapter": "Jurisdiction",
     "full_text": "(a) The district courts shall have original jurisdiction of all civil actions where the matter in controversy exceeds the sum or value of $75,000, exclusive of interest and costs, and is between: (1) citizens of different States."},
    {"citation": "28 USC § 1343", "title": "Civil Rights and Elective Franchise", "chapter": "Jurisdiction",
     "full_text": "(a) The district courts shall have original jurisdiction of any civil action authorized by law to be commenced by any person: (3) To redress the deprivation, under color of any State law, statute, ordinance, regulation, custom or usage, of any right, privilege or immunity secured by the Constitution of the United States or by any Act of Congress providing for equal rights of citizens.",
     "practice_tips": "Companion to §1331 for §1983 actions. No amount-in-controversy requirement."},
    {"citation": "28 USC § 1367", "title": "Supplemental Jurisdiction", "chapter": "Jurisdiction",
     "full_text": "(a) In any civil action of which the district courts have original jurisdiction, they shall have supplemental jurisdiction over all other claims that are so related as to form part of the same case or controversy. (c) The district courts may decline supplemental jurisdiction if: (1) the claim raises a novel or complex issue of State law; (2) the State claim substantially predominates; (3) the district court has dismissed all claims over which it has original jurisdiction; (4) in exceptional circumstances, there are other compelling reasons for declining.",
     "practice_tips": "Supplemental jurisdiction allows state-law claims to be heard alongside §1983 claims if they arise from the same facts. Court may decline if state issues predominate."},
    {"citation": "28 USC § 1441", "title": "Removal of Civil Actions", "chapter": "Jurisdiction",
     "full_text": "(a) Any civil action brought in a State court of which the district courts have original jurisdiction, may be removed by the defendant to the district court. (b) Removal based on diversity: must be filed within 30 days of service."},

    # Domestic Relations Exception to Federal Jurisdiction
    {"citation": "Ankenbrandt v Richards, 504 US 689 (1992)", "title": "Domestic Relations Exception", "chapter": "Jurisdiction",
     "full_text": "The domestic relations exception divests federal courts of jurisdiction over cases involving divorce, alimony, and child custody decrees. However, the exception does NOT bar federal courts from hearing tort claims (including §1983) that arise in a domestic relations context. The Supreme Court held that Ankenbrandt's tort and §1983 claims were properly before the federal court despite involving family members.",
     "practice_tips": "CRITICAL: The domestic relations exception does NOT bar §1983 claims against judges or state actors who violate constitutional rights in family court proceedings. Catz v Chalker (6th Cir) confirms: §1983 claims are about constitutional violations, not domestic relations."},
]

# =============================================================================
# WESTERN DISTRICT OF MICHIGAN (WDMI) LOCAL RULES — Key Rules
# =============================================================================
WDMI_LOCAL_RULES: list[dict] = [
    {"citation": "WDMI LCivR 5.7", "title": "Electronic Filing", "chapter": "WDMI Local Rules",
     "full_text": "All documents shall be filed electronically through the CM/ECF system. Pro se litigants may request exemption from electronic filing requirements."},
    {"citation": "WDMI LCivR 7.1", "title": "Motion Practice", "chapter": "WDMI Local Rules",
     "full_text": "(a) The moving party must file a brief in support of the motion. (b) The opposing party has 14 days to respond. (c) The moving party may file a reply within 7 days of the response. (d) Briefs must not exceed 25 pages without leave of court. (e) Motions for summary judgment: response brief limit is 25 pages; reply is 10 pages.",
     "practice_tips": "WDMI: 14-day response to motions (vs MCR's 7-day). 25-page brief limit (vs MCR's no specific limit). Must file separate brief — not combined with motion."},
    {"citation": "WDMI LCivR 7.2", "title": "Motions for Summary Judgment", "chapter": "WDMI Local Rules",
     "full_text": "(a) A motion for summary judgment must include a Statement of Material Facts. Each fact must be supported by citation to admissible evidence. (b) The opposing party must file a Counter-Statement responding to each fact. Facts not properly controverted will be deemed admitted."},
    {"citation": "WDMI LCivR 10.6", "title": "Page Limitations for Briefs", "chapter": "WDMI Local Rules",
     "full_text": "Opening briefs: 25 pages. Response briefs: 25 pages. Reply briefs: 10 pages. Excess pages require leave of court. Page limits do not include cover page, table of contents, table of authorities, or certificates."},
    {"citation": "WDMI LCivR 16.1", "title": "Scheduling and Case Management", "chapter": "WDMI Local Rules",
     "full_text": "Within 21 days after all defendants have been served, or at such time as the court may direct, the parties shall confer regarding a case management plan and propose a discovery schedule, dispositive motion deadline, and trial date."},
    {"citation": "WDMI LCivR 26.1", "title": "Discovery", "chapter": "WDMI Local Rules",
     "full_text": "Parties must complete discovery within the time set by the scheduling order. Discovery disputes should be resolved by meet-and-confer before filing a motion to compel. Discovery motions must include a certification that the parties have attempted to resolve the dispute."},
]
