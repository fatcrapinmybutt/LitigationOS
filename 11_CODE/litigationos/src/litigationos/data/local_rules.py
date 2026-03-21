"""Local Court Rules — 14th Circuit, 60th District, and Administrative Orders.

Static dataset for LitigationOS covering Muskegon County courts,
Michigan Supreme Court admin orders, and jury instruction summaries.
"""

from __future__ import annotations

# =============================================================================
# 14th CIRCUIT COURT — MUSKEGON COUNTY (Family Division)
# =============================================================================
LOCAL_RULES_14TH_CIRCUIT: list[dict] = [
    {"citation": "14th Cir LAO 2024-01", "title": "E-Filing Requirements", "chapter": "14th Circuit - Muskegon",
     "full_text": "All filings in the 14th Circuit Court must be submitted electronically through the MiFILE e-filing system. Self-represented litigants may request exemption from e-filing and file paper documents at the clerk's office. Filing fees must be paid electronically at the time of filing.",
     "practice_tips": "MiFILE: mifile.courts.michigan.gov. Create an account, select 14th Circuit, and e-file. Fee waiver: file MC 20 (Fee Waiver Request)."},
    {"citation": "14th Cir LAO - Family Division", "title": "Family Division Case Management", "chapter": "14th Circuit - Muskegon",
     "full_text": "Family Division cases (DC docket) are assigned to judges on a rotating basis. Custody and parenting time matters require completion of the Friend of the Court intake process. Parties must attend SMILE (Start Making It Livable for Everyone) program within 28 days of filing. Mediation is required before trial for all contested custody and parenting time issues unless good cause shown.",
     "practice_tips": "SMILE program is mandatory. Mediation required before trial — request waiver if domestic violence or power imbalance exists."},
    {"citation": "14th Cir LAO - Motion Practice", "title": "Motion Practice - 14th Circuit", "chapter": "14th Circuit - Muskegon",
     "full_text": "Motions must comply with MCR 2.119. The moving party must serve the motion at least 9 days before the hearing. Response briefs are due 7 days before hearing. Motions are typically heard on Tuesday and Wednesday motion days. Ex parte motions require compliance with MCR 2.119(B) — emergency and specific factual showing required. Self-scheduling of motion hearings through the court's online scheduling system.",
     "practice_tips": "Tuesday/Wednesday motion days. Use online scheduling. 9-day service for regular motions. Ex parte: must show irreparable harm and no adequate remedy."},
    {"citation": "14th Cir LAO - FOC", "title": "Friend of the Court Procedures", "chapter": "14th Circuit - Muskegon",
     "full_text": "The Muskegon County Friend of the Court (FOC) office is located at 990 Terrace St, Muskegon, MI 49442. FOC handles: custody/parenting time investigations, support calculations, enforcement of court orders, mediation referrals. FOC recommendations are advisory — either party may object within 21 days and request a de novo hearing before the judge. FOC investigators prepare reports that become part of the court file.",
     "practice_tips": "FOC recommendation is NOT binding — ALWAYS object within 21 days if unfavorable. Request de novo hearing (fresh review by judge, not just review of FOC report). FOC office: Pamela Rusco, 990 Terrace St."},
    {"citation": "14th Cir LAO - Custody Evaluations", "title": "Custody Evaluation Procedures", "chapter": "14th Circuit - Muskegon",
     "full_text": "When a custody evaluation is ordered, the court may appoint a Guardian Ad Litem (GAL) under MCR 3.916 or order a professional custody evaluation. Evaluators must consider all 12 best interest factors under MCL 722.23. Reports must be provided to all parties at least 14 days before hearing. Parties may cross-examine the evaluator. Parties may retain their own expert to provide a competing evaluation.",
     "practice_tips": "Challenge biased evaluations: (1) cross-examine evaluator on methodology; (2) retain own expert; (3) file Daubert/MRE 702 challenge if evaluation lacks scientific basis."},
    {"citation": "14th Cir LAO - PPO", "title": "Personal Protection Orders", "chapter": "14th Circuit - Muskegon",
     "full_text": "PPO petitions are filed under MCR 3.219 and MCL 600.2950. Ex parte PPOs are issued without hearing if the petition shows immediate danger of harm. Respondent may request a hearing within 14 days of service. Hearing must be held within 14 days of the request. Violation of a PPO is a criminal offense (MCL 600.2950(23)) punishable by up to 93 days in jail.",
     "practice_tips": "If a PPO is issued against you: file motion to terminate/modify within 14 days. Request hearing. Prepare evidence that the PPO was obtained through false statements (perjury). False PPO petitions can be sanctioned."},

    # =============================================================================
    # 60th DISTRICT COURT — MUSKEGON COUNTY
    # =============================================================================
    {"citation": "60th Dist - General", "title": "60th District Court General Rules", "chapter": "60th District - Muskegon",
     "full_text": "The 60th District Court handles: misdemeanors, civil infractions, small claims ($6,500 limit), landlord-tenant, and preliminary examinations for felonies. Location: 990 Terrace St, Muskegon, MI 49442 (Michael E. Kobza Justice Center). Hours: 8:00 AM - 5:00 PM Monday through Friday.",
     "practice_tips": "Criminal cases (People v. Pigors, 2025-25245676SM-SM) are in 60th District Court. Misdemeanors carry max 93 days jail. Preliminary exam for felonies within 14 days of arraignment (MCR 6.110)."},
    {"citation": "60th Dist - Arraignment", "title": "Arraignment Procedures", "chapter": "60th District - Muskegon",
     "full_text": "Arraignment must occur within 48 hours of arrest (72 hours if arrested on weekend). At arraignment: charges read, rights advised, plea entered, bond set. Bond considerations: seriousness of offense, prior record, ties to community, employment, risk of flight. Personal recognizance (PR) bond may be requested.",
     "practice_tips": "Request PR bond at arraignment. Emphasize ties to community, employment, custody of child (L.D.W.), no prior record. If denied, request reduction at subsequent hearing."},
]

# =============================================================================
# MICHIGAN SUPREME COURT ADMINISTRATIVE ORDERS — Key Orders
# =============================================================================
ADMIN_ORDERS: list[dict] = [
    {"citation": "AO 2019-6", "title": "E-Filing in Michigan Courts", "chapter": "Administrative Orders",
     "full_text": "Administrative Order 2019-6 establishes the statewide electronic filing system (MiFILE) for Michigan courts. All courts must accept electronic filings. Self-represented litigants may request exemption. Electronic filing has the same legal effect as paper filing. Filing is complete when the document is submitted through MiFILE.",
     "practice_tips": "MiFILE is mandatory for most filers. Pro se exemption available. Filing timestamp is when submitted, not when clerk reviews."},
    {"citation": "AO 2020-17", "title": "Remote Hearings", "chapter": "Administrative Orders",
     "full_text": "Courts may conduct proceedings remotely using two-way interactive video technology. Parties must be able to see and hear the proceedings. Courts must ensure remote access for the public. A party may object to remote proceedings and request in-person hearing.",
     "practice_tips": "You have the right to request in-person hearings. Object to remote hearings if you believe it disadvantages your case (e.g., inability to observe witness demeanor)."},
    {"citation": "AO 2021-1", "title": "Access to Court Records", "chapter": "Administrative Orders",
     "full_text": "Court records are public records subject to disclosure unless sealed or restricted. Personal identifying information (SSN, DOB) must be redacted from public filings per MCR 8.119(H). Minor children must be identified by initials only in publicly accessible documents.",
     "practice_tips": "L.D.W. must be referred to by initials only in all public filings per MCR 8.119(H). Redact SSN, DOB, and other PII before filing."},
    {"citation": "AO 2023-2", "title": "Case Evaluation and Mediation", "chapter": "Administrative Orders",
     "full_text": "Courts shall promote alternative dispute resolution. Case evaluation panels consist of 3 attorneys who review the case and issue an award. If a party rejects the award and fails to improve their position at trial by more than 10%, they must pay the other side's costs from the date of rejection.",
     "practice_tips": "Case evaluation rejection penalty: if you reject and don't improve by >10% at trial, you pay opposing costs. Consider carefully before rejecting."},
    {"citation": "AO - Judicial Conduct", "title": "Judicial Conduct Standards", "chapter": "Administrative Orders",
     "full_text": "Michigan judges are bound by the Michigan Code of Judicial Conduct. Canon 1: Maintain high standards of conduct. Canon 2: Avoid impropriety and appearance of impropriety. Canon 3: Perform duties impartially and diligently — including (A) adjudicative responsibilities: decide matters promptly, maintain order, be patient, accord every person the right to be heard. Canon 4: Regulate extrajudicial activities. Canon 5: Refrain from political activity. Complaints filed with Judicial Tenure Commission (JTC).",
     "practice_tips": "Judicial misconduct complaints → JTC (3034 W Grand Blvd, Suite 8-450, Detroit, MI 48202). Canon 2 (appearance of impropriety) and Canon 3(A) (right to be heard) are most common bases for complaints."},
]

# =============================================================================
# MICHIGAN STANDARD JURY INSTRUCTIONS — Key Civil/Criminal
# =============================================================================
JURY_INSTRUCTIONS: list[dict] = [
    # Civil Jury Instructions (M Civ JI)
    {"citation": "M Civ JI 10.01", "title": "Negligence - Definition", "chapter": "M Civ JI - Negligence",
     "full_text": "Negligence is the failure to use ordinary care. Ordinary care is the care a reasonably careful person would use under the circumstances. Negligence may consist of doing something that a reasonably careful person would not do, or failing to do something that a reasonably careful person would do."},
    {"citation": "M Civ JI 50.01", "title": "Civil Rights - 42 USC 1983", "chapter": "M Civ JI - Civil Rights",
     "full_text": "The plaintiff claims that the defendant, while acting under color of state law, deprived the plaintiff of rights secured by the United States Constitution. To establish this claim, the plaintiff must prove: (1) the defendant acted under color of state law; (2) the defendant's conduct deprived the plaintiff of a right, privilege, or immunity secured by the Constitution or laws of the United States.",
     "practice_tips": "Federal jury instruction for §1983 — the two-element test. Must prove: (1) state action (judge, FOC = state actors); (2) constitutional deprivation (14th Amendment due process, 1st Amendment access to courts)."},
    {"citation": "M Civ JI 50.04", "title": "Civil Rights - Damages", "chapter": "M Civ JI - Civil Rights",
     "full_text": "If you find that the defendant violated the plaintiff's constitutional rights, you must determine the amount of damages. You may award: (1) compensatory damages for injuries actually suffered, including emotional distress, humiliation, and loss of enjoyment of life; (2) nominal damages if constitutional rights were violated but no actual injury is proven; (3) punitive damages if the defendant's conduct was motivated by evil motive or intent, or involved reckless or callous indifference to the plaintiff's constitutional rights.",
     "practice_tips": "§1983 damages: compensatory (emotional distress, lost parenting time), nominal ($1 if no actual damages proven but rights violated), punitive (if reckless disregard). Punitive damages NOT available against municipalities."},

    # Criminal Jury Instructions (M Crim JI)
    {"citation": "M Crim JI 3.2", "title": "Presumption of Innocence / Burden of Proof", "chapter": "M Crim JI - General",
     "full_text": "A person accused of a crime is presumed to be innocent. This presumption continues throughout the trial and entitles the defendant to a verdict of not guilty unless you are satisfied beyond a reasonable doubt that the defendant is guilty. The defendant is not required to prove innocence or to do anything. The prosecution must prove each element of the crime beyond a reasonable doubt."},
    {"citation": "M Crim JI 4.1", "title": "Credibility of Witnesses", "chapter": "M Crim JI - General",
     "full_text": "You may consider the following when judging a witness's credibility: (1) the witness's interest in the outcome; (2) the witness's relationship with the parties; (3) the witness's opportunity to observe; (4) the reasonableness of the testimony; (5) the witness's manner while testifying; (6) whether the testimony was contradicted; (7) any bias, prejudice, or other motive; (8) any prior inconsistent statements."},
    {"citation": "M Crim JI 17.16", "title": "Domestic Violence", "chapter": "M Crim JI - Specific Offenses",
     "full_text": "To prove domestic assault, the prosecution must prove: (1) the defendant assaulted or battered (household member); (2) at the time, the defendant and (victim) were: spouses, former spouses, persons with a child in common, or residents/former residents of the same household. An assault is an attempt to commit a battery or an act that would cause a reasonable person to fear an imminent battery. A battery is a forceful, violent, or offensive touching of the person or something closely connected with the person.",
     "practice_tips": "For Andrew's criminal case: prosecution must prove EACH element beyond reasonable doubt. Self-defense is an affirmative defense (M Crim JI 7.15). Lack of injury doesn't negate assault but weakens the case."},
    {"citation": "M Crim JI 7.15", "title": "Self-Defense", "chapter": "M Crim JI - Defenses",
     "full_text": "The defendant claims to have acted in lawful self-defense. A person may use force to defend themselves if: (1) they honestly and reasonably believed they were in danger of being injured; (2) they honestly and reasonably believed it was necessary to use force to defend themselves; (3) the amount of force used was reasonable. The defendant does not have to prove self-defense. The prosecution must prove beyond a reasonable doubt that the defendant did not act in self-defense."},
]

# =============================================================================
# MICHIGAN BENCH BOOK SUMMARIES (from MJI Civil Proceedings Benchbook)
# =============================================================================
BENCH_BOOK_ENTRIES: list[dict] = [
    {"citation": "Benchbook Ch 1", "title": "Jurisdiction and Venue", "chapter": "Civil Benchbook",
     "full_text": "Circuit courts have original jurisdiction in all civil cases with amount in controversy over $25,000. Venue proper where defendant resides, where cause of action arose, or where property is situated (MCL 600.1621-1645). Forum non conveniens: court may dismiss/transfer if another forum is more convenient."},
    {"citation": "Benchbook Ch 3", "title": "Parties and Joinder", "chapter": "Civil Benchbook",
     "full_text": "Real party in interest (MCR 2.201). Capacity of minors (next friend or guardian). Joinder of parties (MCR 2.206-2.207). Intervention (MCR 2.209). Class actions (MCR 3.501). Substitution of parties (MCR 2.202)."},
    {"citation": "Benchbook Ch 5", "title": "Discovery", "chapter": "Civil Benchbook",
     "full_text": "Michigan discovery governed by MCR 2.301-2.316. Scope: any non-privileged matter relevant to the subject matter. Interrogatories (MCR 2.309): limited to 35 including subparts. Depositions (MCR 2.306): 7-hour limit per deponent. Document requests (MCR 2.310): 28-day response time. Requests for admission (MCR 2.312): deemed admitted if not answered within 28 days. Protective orders (MCR 2.302(C)): for good cause shown.",
     "practice_tips": "Michigan limits: 35 interrogatories, 7-hour depositions, 28-day response time. RFAs are powerful — unanswered = admitted. Always answer timely."},
    {"citation": "Benchbook Ch 7", "title": "Summary Disposition", "chapter": "Civil Benchbook",
     "full_text": "MCR 2.116 governs summary disposition (Michigan's summary judgment). 10 grounds (C)(1)-(10). Most common: (C)(8) no genuine issue of material fact — evidence viewed in light most favorable to non-movant. (C)(10) failure to state a claim. 21-day response period. Court must consider affidavits, pleadings, depositions, admissions, and other documentary evidence."},
    {"citation": "Benchbook Ch 9", "title": "Trial Procedures", "chapter": "Civil Benchbook",
     "full_text": "Jury selection (MCR 2.511): peremptory challenges — 5 per side in civil. Batson challenges for discriminatory strikes. Opening statements. Plaintiff presents case-in-chief. Directed verdict (MCR 2.516). Defense case. Closing arguments. Jury instructions. Verdict. Post-trial motions (MCR 2.611-2.612)."},
    {"citation": "Benchbook - Family Ch 1", "title": "Custody Proceedings Overview", "chapter": "Family Benchbook",
     "full_text": "Custody determinations governed by Child Custody Act (MCL 722.21-722.31) and MCR 3.210. Best interest factors (MCL 722.23(a)-(l)) are the paramount consideration. Established custodial environment (ECE) determines burden of proof: if ECE exists with one parent, party seeking change bears clear and convincing evidence burden. If no ECE, preponderance of evidence. Change of custody requires proper cause or change of circumstances as threshold (Vodvarka v Grasmeyer, 259 Mich App 499)."},
    {"citation": "Benchbook - Family Ch 2", "title": "Parenting Time", "chapter": "Family Benchbook",
     "full_text": "Parenting time governed by MCL 722.27a. Parenting time is the right of the child, not just the parent. Court must consider factors in MCL 722.27a(7) when determining parenting time frequency and conditions. Denial of parenting time only for endangerment. Make-up time must be granted for wrongful denial. Parenting time orders should be specific enough to be enforceable."},
    {"citation": "Benchbook - Family Ch 3", "title": "Child Support", "chapter": "Family Benchbook",
     "full_text": "Child support calculated using Michigan Child Support Formula (MCSF). Based on: income of both parents, number of overnights, number of children, health insurance costs, child care costs. Deviation from formula requires specific findings on the record. Support continues until age 18 (or 19.5 if enrolled in high school). Modification requires change in circumstances."},
]
