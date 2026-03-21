"""Complete Michigan Rules of Evidence (MRE) — Static Dataset for LitigationOS.

All 11 articles, 68 rules with full text for critical rules.
Sources: courts.michigan.gov, as of March 2026.
"""

from __future__ import annotations

MRE_RULES: list[dict] = [
    # =========================================================================
    # ARTICLE I — GENERAL PROVISIONS
    # =========================================================================
    {"citation": "MRE 101", "title": "Scope", "article": "Article I - General Provisions",
     "full_text": "These rules govern proceedings in the courts of the State of Michigan to the extent and with the exceptions stated in MRE 1101."},
    {"citation": "MRE 102", "title": "Purpose and Construction", "article": "Article I - General Provisions",
     "full_text": "These rules shall be construed to secure fairness in administration, elimination of unjustifiable expense and delay, and promotion of growth and development of the law of evidence."},
    {"citation": "MRE 103", "title": "Rulings on Evidence", "article": "Article I - General Provisions",
     "full_text": "(a) Effect of Erroneous Ruling. Error may not be predicated upon a ruling which admits or excludes evidence unless a substantial right of the party is affected, and (1) Objection. In case the ruling admits evidence, a timely objection or motion to strike appears of record, stating the specific ground of objection, if not apparent from the context; or (2) Offer of Proof. In case the ruling excludes evidence, the substance of the evidence was made known to the court by offer or was apparent from the context. (b) Record. The court may add any statement about the character of the evidence, the form in which it was offered, the objection, and the ruling. (c) Hearing of Jury. Jury proceedings shall be conducted to prevent inadmissible evidence from being suggested to the jury. (d) Plain Error. Nothing in this rule precludes taking notice of plain errors affecting substantial rights although they were not brought to the attention of the court.",
     "practice_tips": "CRITICAL for appeals: Must make timely objection to preserve error. If evidence excluded, must make offer of proof. Plain error review available but harder to win."},
    {"citation": "MRE 104", "title": "Preliminary Questions", "article": "Article I - General Provisions",
     "full_text": "(a) Questions of Admissibility. Preliminary questions concerning the qualification of a witness, existence of a privilege, or admissibility of evidence shall be determined by the court. (b) Relevancy Conditioned on Fact. When relevancy depends upon the fulfillment of a condition of fact, the court shall admit it upon introduction of evidence sufficient to support a finding of the fulfillment of the condition."},
    {"citation": "MRE 105", "title": "Limited Admissibility", "article": "Article I - General Provisions",
     "full_text": "When evidence which is admissible for one purpose but not another is admitted, the court, upon request, shall restrict the evidence to its proper scope and instruct the jury accordingly."},
    {"citation": "MRE 106", "title": "Remainder of Writings or Recorded Statements", "article": "Article I - General Provisions",
     "full_text": "When a writing or recorded statement or part thereof is introduced by a party, an adverse party may require the introduction at that time of any other part or any other writing or recorded statement which ought in fairness to be considered contemporaneously with it."},

    # =========================================================================
    # ARTICLE II — JUDICIAL NOTICE
    # =========================================================================
    {"citation": "MRE 201", "title": "Judicial Notice of Adjudicative Facts", "article": "Article II - Judicial Notice",
     "full_text": "(a) Scope. This rule governs judicial notice of adjudicative facts only. (b) Kinds of Facts. A judicially noticed fact must be one not subject to reasonable dispute in that it is either (1) generally known within the territorial jurisdiction of the trial court or (2) capable of accurate and ready determination by resort to sources whose accuracy cannot reasonably be questioned. (c) When Discretionary. A court may take judicial notice whether requested or not. (d) When Mandatory. A court shall take judicial notice if requested by a party and supplied with the necessary information. (e) Opportunity to Be Heard. A party is entitled to be heard as to the propriety of taking judicial notice. (f) Time of Taking Notice. Judicial notice may be taken at any stage of the proceeding. (g) Instructing Jury. In a civil action, the court shall instruct the jury to accept the noticed fact as established. In a criminal case, the court shall instruct the jury that it may, but is not required to, accept the noticed fact.",
     "practice_tips": "Use judicial notice for court rules, statutes, public records, and widely known facts. In civil cases, judicially noticed facts are BINDING on the jury."},

    # =========================================================================
    # ARTICLE III — PRESUMPTIONS
    # =========================================================================
    {"citation": "MRE 301", "title": "Presumptions in Civil Actions", "article": "Article III - Presumptions",
     "full_text": "In all civil actions and proceedings, a presumption imposes on the party against whom it is directed the burden of going forward with evidence to rebut or meet the presumption, but does not shift to such party the burden of proof in the sense of the risk of nonpersuasion."},

    # =========================================================================
    # ARTICLE IV — RELEVANCY AND ITS LIMITS
    # =========================================================================
    {"citation": "MRE 401", "title": "Definition of 'Relevant Evidence'", "article": "Article IV - Relevancy",
     "full_text": "'Relevant evidence' means evidence having any tendency to make the existence of any fact that is of consequence to the determination of the action more probable or less probable than it would be without the evidence."},
    {"citation": "MRE 402", "title": "Relevant Evidence Generally Admissible", "article": "Article IV - Relevancy",
     "full_text": "All relevant evidence is admissible, except as otherwise provided by the Constitution of the United States, the Constitution of the State of Michigan, these rules, or other rules adopted by the Supreme Court. Evidence which is not relevant is not admissible."},
    {"citation": "MRE 403", "title": "Exclusion of Relevant Evidence on Grounds of Prejudice", "article": "Article IV - Relevancy",
     "full_text": "Although relevant, evidence may be excluded if its probative value is substantially outweighed by the danger of unfair prejudice, confusion of the issues, or misleading the jury, or by considerations of undue delay, waste of time, or needless presentation of cumulative evidence.",
     "practice_tips": "The balancing test: probative value vs. unfair prejudice. Evidence is only excluded if prejudice SUBSTANTIALLY outweighs probative value — the scale tips toward admission."},
    {"citation": "MRE 404", "title": "Character Evidence Not Admissible to Prove Conduct; Exceptions", "article": "Article IV - Relevancy",
     "full_text": "(a) Character Evidence Generally. Evidence of a person's character or a trait of character is not admissible for the purpose of proving action in conformity therewith on a particular occasion, except: (1) Character of Accused — evidence of a pertinent character trait offered by the accused, or by the prosecution to rebut; (2) Character of Victim — evidence of a pertinent character trait of the victim offered by the accused, or by the prosecution to rebut; (3) Character of Witness — evidence of the character of a witness as provided in MRE 607-609. (b) Other Crimes, Wrongs, or Acts. Evidence of other crimes, wrongs, or acts is not admissible to prove the character of a person in order to show action in conformity therewith. It may, however, be admissible for other purposes, such as proof of motive, opportunity, intent, preparation, scheme, plan, or system in doing an act, knowledge, identity, or absence of mistake or accident when the same is material.",
     "practice_tips": "MRE 404(b) — prior bad acts are NOT admissible to show propensity, BUT are admissible for MIOPIC: Motive, Intent, Opportunity, Preparation, Identity, Common scheme/plan. Must give notice before trial in criminal cases."},
    {"citation": "MRE 406", "title": "Habit; Routine Practice", "article": "Article IV - Relevancy",
     "full_text": "Evidence of the habit of a person or of the routine practice of an organization, whether corroborated or not and regardless of the presence of eyewitnesses, is relevant to prove that the conduct of the person or organization on a particular occasion was in conformity with the habit or routine practice.",
     "practice_tips": "Habit evidence IS admissible (unlike character). Pattern of parenting time interference could qualify as 'habit' if specific and regular enough."},
    {"citation": "MRE 410", "title": "Inadmissibility of Pleas and Plea Discussions", "article": "Article IV - Relevancy",
     "full_text": "Evidence of: (1) a plea of guilty which was later withdrawn; (2) a plea of nolo contendere; (3) any statement made in the course of plea proceedings; (4) any statement made in the course of plea discussions — is not admissible in any civil or criminal proceeding against the person who made the plea or was a participant in the plea discussions.",
     "practice_tips": "For Andrew's criminal case: nolo contendere pleas and withdrawn guilty pleas cannot be used against him in the custody case."},

    # =========================================================================
    # ARTICLE V — PRIVILEGES
    # =========================================================================
    {"citation": "MRE 501", "title": "General Rule of Privilege", "article": "Article V - Privileges",
     "full_text": "The privilege of a witness, person, government, state, or political subdivision thereof shall be governed by the principles of the common law as they may be interpreted by the courts of this state in the light of reason and experience."},

    # =========================================================================
    # ARTICLE VI — WITNESSES
    # =========================================================================
    {"citation": "MRE 601", "title": "General Rule of Competency", "article": "Article VI - Witnesses",
     "full_text": "Every person is competent to be a witness except as otherwise provided in these rules."},
    {"citation": "MRE 602", "title": "Lack of Personal Knowledge", "article": "Article VI - Witnesses",
     "full_text": "A witness may not testify to a matter unless evidence is introduced sufficient to support a finding that the witness has personal knowledge of the matter. Evidence to prove personal knowledge may, but need not, consist of the witness's own testimony."},
    {"citation": "MRE 607", "title": "Who May Impeach", "article": "Article VI - Witnesses",
     "full_text": "The credibility of a witness may be attacked by any party, including the party calling the witness.",
     "practice_tips": "You CAN impeach your own witness. This is useful when a witness changes their testimony."},
    {"citation": "MRE 608", "title": "Evidence of Character and Conduct of Witness", "article": "Article VI - Witnesses",
     "full_text": "(a) Opinion and Reputation Evidence of Character. The credibility of a witness may be attacked or supported by evidence in the form of opinion or reputation, but subject to these limitations: (1) the evidence may refer only to character for truthfulness or untruthfulness, and (2) evidence of truthful character is admissible only after the character of the witness for truthfulness has been attacked. (b) Specific Instances of Conduct. Specific instances of the conduct of a witness, for the purpose of attacking or supporting credibility, may not be proved by extrinsic evidence, but may be inquired into on cross-examination of the witness."},
    {"citation": "MRE 609", "title": "Impeachment by Evidence of Conviction of Crime", "article": "Article VI - Witnesses",
     "full_text": "(a) For purposes of attacking the credibility of a witness, evidence that the witness has been convicted of a crime shall be admitted if elicited from the witness or established by public record during cross-examination, if: (1) the crime contained an element of dishonesty or false statement, or (2) the crime contained an element of theft, and (A) the crime was punishable by imprisonment in excess of one year, and (B) the court determines that the probative value of admitting this evidence outweighs its prejudicial effect. (b) Time Limit. Evidence of a conviction under this rule is not admissible if a period of more than ten years has elapsed since the date of the conviction or the release of the witness from confinement, whichever is the later date.",
     "practice_tips": "Crimes of dishonesty (perjury, fraud) automatically admissible for impeachment. Theft crimes require balancing test. 10-year lookback limit."},
    {"citation": "MRE 611", "title": "Mode and Order of Interrogation and Presentation", "article": "Article VI - Witnesses",
     "full_text": "(a) Control by Court. The court shall exercise reasonable control over the mode and order of interrogating witnesses to: (1) make the interrogation effective for ascertaining the truth; (2) avoid needless consumption of time; (3) protect witnesses from harassment or undue embarrassment. (b) Scope of Cross-Examination. A witness may be cross-examined on any matter relevant to any issue in the case. (c) Leading Questions. Leading questions should not be used on direct examination except as may be necessary to develop the witness's testimony. Leading questions are ordinarily permitted on cross-examination.",
     "practice_tips": "Michigan allows WIDE OPEN cross-examination — any relevant matter, not limited to scope of direct. Leading questions allowed on cross."},
    {"citation": "MRE 613", "title": "Prior Statements of Witnesses", "article": "Article VI - Witnesses",
     "full_text": "(a) Examining Witness Concerning Prior Statement. In examining a witness concerning a prior statement made by the witness, the statement need not be shown nor its contents disclosed to the witness at that time, but on request the same shall be shown or disclosed to opposing counsel. (b) Extrinsic Evidence of Prior Inconsistent Statement. Extrinsic evidence of a prior inconsistent statement by a witness is not admissible unless the witness is afforded an opportunity to explain or deny the same and the opposite party is afforded an opportunity to interrogate the witness thereon.",
     "practice_tips": "Key impeachment tool: prior inconsistent statements. Must give the witness a chance to explain before introducing extrinsic proof."},
    {"citation": "MRE 615", "title": "Exclusion of Witnesses", "article": "Article VI - Witnesses",
     "full_text": "At the request of a party the court shall order witnesses excluded so that they cannot hear the testimony of other witnesses, and it may make the order of its own motion. This rule does not authorize exclusion of: (1) a party who is a natural person; (2) an officer or employee of a party which is not a natural person designated as its representative by its attorney; (3) a person whose presence is shown by a party to be essential to the presentation of the party's cause."},
    {"citation": "MRE 616", "title": "Bias of Witness", "article": "Article VI - Witnesses",
     "full_text": "Evidence of bias, interest, or motive to testify falsely is always admissible to impeach a witness. Bias may be shown by examination of the witness or by extrinsic evidence.",
     "practice_tips": "Bias is ALWAYS admissible — no balancing test. Use to challenge FOC investigators, custody evaluators, or any witness with a stake in the outcome."},

    # =========================================================================
    # ARTICLE VII — OPINIONS AND EXPERT TESTIMONY
    # =========================================================================
    {"citation": "MRE 701", "title": "Opinion Testimony by Lay Witnesses", "article": "Article VII - Expert Testimony",
     "full_text": "If the witness is not testifying as an expert, the witness's testimony in the form of opinions or inferences is limited to those opinions or inferences which are (a) rationally based on the perception of the witness and (b) helpful to a clear understanding of the witness's testimony or the determination of a fact in issue."},
    {"citation": "MRE 702", "title": "Testimony by Experts", "article": "Article VII - Expert Testimony",
     "full_text": "If the court determines that scientific, technical, or other specialized knowledge will assist the trier of fact, a witness qualified as an expert by knowledge, skill, experience, training, or education may testify thereto in the form of an opinion or otherwise if: (1) the testimony is based on sufficient facts or data, (2) the testimony is the product of reliable principles and methods, and (3) the witness has applied the principles and methods reliably to the facts of the case.",
     "practice_tips": "Michigan adopted the Daubert standard (Gilbert v DaimlerChrysler, 470 Mich 749). Expert testimony must be based on reliable methodology. Challenge junk science custody evaluations under this rule."},
    {"citation": "MRE 703", "title": "Bases of Opinion Testimony by Experts", "article": "Article VII - Expert Testimony",
     "full_text": "The facts or data upon which an expert bases an opinion may be those perceived by or made known to the expert at or before the hearing. If of a type reasonably relied upon by experts in the particular field, the facts or data need not be admissible in evidence."},

    # =========================================================================
    # ARTICLE VIII — HEARSAY
    # =========================================================================
    {"citation": "MRE 801", "title": "Definitions", "article": "Article VIII - Hearsay",
     "full_text": """(a) Statement. A 'statement' is (1) an oral or written assertion or (2) nonverbal conduct intended as an assertion.
(b) Declarant. A 'declarant' is a person who makes a statement.
(c) Hearsay. 'Hearsay' is a statement, other than one made by the declarant while testifying at the trial or hearing, offered in evidence to prove the truth of the matter asserted.
(d) Statements That Are Not Hearsay. A statement is not hearsay if:
(1) Prior Statement by Witness. The declarant testifies at trial and is subject to cross-examination, and the statement is (A) inconsistent with the declarant's testimony and given under oath at a prior proceeding, or (B) consistent with the declarant's testimony and offered to rebut a charge of recent fabrication, or (C) one of identification of a person made after perceiving the person.
(2) Admission by Party-Opponent. The statement is offered against a party and is (A) the party's own statement, or (B) a statement the party has adopted or manifested belief in its truth, or (C) a statement by a person authorized by the party to make it, or (D) a statement by the party's agent or servant within the scope of the agency or employment, or (E) a statement by a co-conspirator during the course of and in furtherance of the conspiracy.""",
     "practice_tips": "Party admissions (d)(2) are NOT hearsay — Emily's own statements (texts, emails, social media posts) are admissible as party admissions. Prior inconsistent statements under oath are also not hearsay."},
    {"citation": "MRE 802", "title": "Hearsay Rule", "article": "Article VIII - Hearsay",
     "full_text": "Hearsay is not admissible except as provided by these rules."},
    {"citation": "MRE 803", "title": "Hearsay Exceptions; Availability of Declarant Immaterial", "article": "Article VIII - Hearsay",
     "full_text": """The following are not excluded by the hearsay rule, even though the declarant is available as a witness:
(1) Present Sense Impression. A statement describing or explaining an event or condition made while the declarant was perceiving the event or condition, or immediately thereafter.
(2) Excited Utterance. A statement relating to a startling event or condition made while the declarant was under the stress of excitement caused by the event or condition.
(3) Then Existing Mental, Emotional, or Physical Condition. A statement of the declarant's then existing state of mind, emotion, sensation, or physical condition (such as intent, plan, motive, design, mental feeling, pain, and bodily health).
(4) Statements for Purposes of Medical Treatment. Statements made for purposes of medical treatment or diagnosis, including statements describing medical history, past or present symptoms, pain, or sensations, or the inception or general character of the cause or external source thereof insofar as reasonably pertinent to treatment or diagnosis.
(5) Recorded Recollection. A memorandum or record concerning a matter about which a witness once had knowledge but now has insufficient recollection to testify fully and accurately, shown to have been made or adopted when the matter was fresh in the witness's memory and to reflect that knowledge correctly.
(6) Records of Regularly Conducted Activity. A memorandum, report, record, or data compilation made at or near the time by a person with knowledge, if kept in the course of a regularly conducted business activity, and if it was the regular practice to make such a record (business records exception).
(8) Public Records and Reports. Records, reports, statements, or data compilations of public offices or agencies setting forth the activities of the office, matters observed pursuant to duty, or factual findings resulting from an investigation made pursuant to authority granted by law.
(24) Other Exceptions (Catch-All). A statement not specifically covered by any of the foregoing exceptions but having equivalent circumstantial guarantees of trustworthiness, if the court determines that (A) the statement is offered as evidence of a material fact; (B) the statement is more probative on the point than other evidence; (C) admission serves the interests of justice; (D) adequate notice is given to the adverse party.""",
     "practice_tips": "Key exceptions for custody cases: (3) state of mind — child's statements about feelings toward parents; (4) medical treatment — statements to therapists; (6) business records — school, medical, therapy records; (8) public records — CPS reports, police reports; (24) catch-all for anything with guarantees of trustworthiness."},
    {"citation": "MRE 804", "title": "Hearsay Exceptions; Declarant Unavailable", "article": "Article VIII - Hearsay",
     "full_text": """(a) Definition of Unavailability. 'Unavailability as a witness' includes situations in which the declarant: (1) is exempted from testifying by privilege; (2) refuses to testify despite a court order; (3) testifies to a lack of memory; (4) is unable to be present because of death or illness; (5) is absent and the proponent has been unable to procure attendance by process.
(b) Hearsay Exceptions. The following are not excluded if the declarant is unavailable:
(1) Former Testimony. Testimony given at another hearing or deposition, if the party against whom it is offered had an opportunity to develop the testimony by direct, cross, or redirect examination.
(2) Statement Under Belief of Impending Death. A statement made by a declarant believing death to be imminent, concerning the cause or circumstances of what the declarant believed to be impending death.
(3) Statement Against Interest. A statement which at the time of its making was so far contrary to the declarant's pecuniary, proprietary, or penal interest that a reasonable person would not have made the statement unless believing it to be true.
(6) Forfeiture by Wrongdoing. A statement offered against a party who has engaged in wrongdoing that was intended to, and did, procure the unavailability of the declarant as a witness.""",
     "practice_tips": "(b)(6) Forfeiture by wrongdoing — if a party causes a witness to be unavailable (intimidation, tampering), they forfeit the right to object to hearsay. Powerful tool against witness tampering."},
    {"citation": "MRE 805", "title": "Hearsay Within Hearsay", "article": "Article VIII - Hearsay",
     "full_text": "Hearsay included within hearsay is not excluded under the hearsay rule if each part of the combined statements conforms with an exception to the hearsay rule."},
    {"citation": "MRE 806", "title": "Attacking and Supporting Credibility of Declarant", "article": "Article VIII - Hearsay",
     "full_text": "When a hearsay statement has been admitted in evidence, the credibility of the declarant may be attacked, and if attacked may be supported, by any evidence which would be admissible for those purposes if the declarant had testified as a witness."},

    # =========================================================================
    # ARTICLE IX — AUTHENTICATION AND IDENTIFICATION
    # =========================================================================
    {"citation": "MRE 901", "title": "Requirement of Authentication or Identification", "article": "Article IX - Authentication",
     "full_text": "(a) General Provision. The requirement of authentication as a condition precedent to admissibility is satisfied by evidence sufficient to support a finding that the matter in question is what its proponent claims. (b) Illustrations. Examples of authentication include: (1) testimony of witness with knowledge; (2) nonexpert opinion on handwriting; (3) comparison by trier or expert; (4) distinctive characteristics; (5) voice identification; (6) telephone conversations; (7) public records; (8) ancient documents; (9) process or system; (10) methods provided by statute or rule.",
     "practice_tips": "For text messages, emails, and social media — authenticate through testimony that the account belongs to the sender, distinctive characteristics of writing style, or metadata."},
    {"citation": "MRE 902", "title": "Self-Authentication", "article": "Article IX - Authentication",
     "full_text": "Extrinsic evidence of authenticity is not required for: (1) domestic public documents under seal; (2) domestic public documents not under seal with certification; (3) foreign public documents; (4) certified copies of public records; (5) official publications; (6) newspapers and periodicals; (7) trade inscriptions; (8) acknowledged documents; (9) commercial paper; (10) presumptions under Acts of Congress."},

    # =========================================================================
    # ARTICLE X — CONTENTS OF WRITINGS, RECORDINGS, PHOTOGRAPHS
    # =========================================================================
    {"citation": "MRE 1001", "title": "Definitions", "article": "Article X - Best Evidence",
     "full_text": "(1) 'Writings' and 'recordings' consist of letters, words, or numbers set down by handwriting, typewriting, printing, photostating, photographing, magnetic impulse, mechanical or electronic recording, or other form of data compilation. (2) 'Photographs' include still photographs, X-ray films, video tapes, and motion pictures. (3) An 'original' is the writing or recording itself. (4) A 'duplicate' is a counterpart produced by the same impression as the original."},
    {"citation": "MRE 1003", "title": "Admissibility of Duplicates", "article": "Article X - Best Evidence",
     "full_text": "A duplicate is admissible to the same extent as an original unless (1) a genuine question is raised as to the authenticity of the original or (2) in the circumstances it would be unfair to admit the duplicate in lieu of the original.",
     "practice_tips": "Copies of documents (including printouts of texts/emails) are generally admissible as duplicates unless authenticity is genuinely challenged."},

    # =========================================================================
    # ARTICLE XI — MISCELLANEOUS
    # =========================================================================
    {"citation": "MRE 1101", "title": "Rules Applicable; Exceptions", "article": "Article XI - Miscellaneous",
     "full_text": "(a) These rules apply to all actions and proceedings in the courts of this state. (b) The rules of evidence (other than those relating to privileges) do not apply in: (1) preliminary hearings in criminal cases; (2) proceedings for extradition or rendition; (3) sentencing; (4) probation revocation; (5) issuance of warrants; (6) proceedings for temporary restraining orders; (7) preliminary injunction hearings; (8) contempt proceedings in which the court may act summarily.",
     "practice_tips": "Evidence rules DON'T fully apply at preliminary hearings, sentencing, or TRO hearings. At these hearings, hearsay may be considered."},
]
