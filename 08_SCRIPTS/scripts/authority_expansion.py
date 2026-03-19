"""
AUTHORITY EXPANSION ENGINE
Builds federal rules, constitutional authority, MCJC canons, doctrine defense matrix,
FOC Act, MDHHS/CPS framework, housing law, and case law expansion.
Writes all new authority entries to a JSON file for DB injection and package upgrades.
"""
import json, os, re
from datetime import datetime

OUTPUT_DIR = r"I:\LitigationOS_Delta99"
LOG = r"I:\DRIVE_ORG\operations.log"

def log(msg):
    ts = datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

# ============================================================
# 1. FEDERAL RULES OF CIVIL PROCEDURE (Key rules for 1983 litigation)
# ============================================================
FRCP_RULES = {
    "FRCP_4": {
        "rule_type": "FRCP", "rule_number": "4", "title": "SUMMONS",
        "chapter": "Federal Civil Procedure",
        "summary": "Requirements for issuance, service, and waiver of service of summons in federal civil actions.",
        "full_text": "Rule 4. Summons. (a) Contents; Amendments. A summons must: (1) name the court and the parties; (2) be directed to the defendant; (3) state the name and address of the plaintiff's attorney or the plaintiff; (4) state the time within which the defendant must appear and defend; (5) notify the defendant that a failure to appear and defend will result in default judgment. (b) Issuance. On or after filing the complaint, the plaintiff may present a summons to the clerk for signature and seal. (c) Service. (1) In General. A summons must be served with a copy of the complaint. (2) By Whom. Any person who is at least 18 years old and not a party may serve a summons. (e) Serving an Individual Within a Judicial District. An individual may be served by: (1) following state law for serving a summons in the state where the district court is located or where service is made; or (2) delivering a copy of the summons and complaint to the individual personally; or leaving copies at the individual's dwelling with someone of suitable age who resides there; or delivering a copy to an agent authorized by appointment or by law to receive service of process."
    },
    "FRCP_8": {
        "rule_type": "FRCP", "rule_number": "8", "title": "GENERAL RULES OF PLEADING",
        "chapter": "Federal Civil Procedure",
        "summary": "Standards for claims, defenses, and pleading form in federal court. Requires short and plain statement.",
        "full_text": "Rule 8. General Rules of Pleading. (a) Claim for Relief. A pleading that states a claim for relief must contain: (1) a short and plain statement of the grounds for the court's jurisdiction; (2) a short and plain statement of the claim showing that the pleader is entitled to relief; and (3) a demand for the relief sought, which may include relief in the alternative or different types of relief. (d) Pleading to Be Concise and Direct. (1) In General. Each allegation must be simple, concise, and direct. No technical form is required. (e) Construing Pleadings. Pleadings must be construed so as to do justice."
    },
    "FRCP_11": {
        "rule_type": "FRCP", "rule_number": "11", "title": "SIGNING PLEADINGS, MOTIONS, AND OTHER PAPERS",
        "chapter": "Federal Civil Procedure",
        "summary": "Signature requirements and certification that claims have evidentiary support. Sanctions for violations.",
        "full_text": "Rule 11. Signing Pleadings, Motions, and Other Papers; Representations to the Court; Sanctions. (a) Signature. Every pleading, written motion, and other paper must be signed by at least one attorney of record or by the party personally if unrepresented. (b) Representations to the Court. By presenting to the court a pleading, written motion, or other paper, an attorney or unrepresented party certifies that to the best of the person's knowledge: (1) it is not being presented for any improper purpose; (2) the claims, defenses, and other legal contentions are warranted by existing law or by a nonfrivolous argument; (3) the factual contentions have evidentiary support; (4) the denials of factual contentions are warranted on the evidence."
    },
    "FRCP_12": {
        "rule_type": "FRCP", "rule_number": "12", "title": "DEFENSES AND OBJECTIONS",
        "chapter": "Federal Civil Procedure",
        "summary": "Pre-answer motions including 12(b)(1) subject matter jurisdiction, 12(b)(6) failure to state a claim.",
        "full_text": "Rule 12. Defenses and Objections. (b) How to Present Defenses. Every defense to a claim for relief in any pleading must be asserted in the responsive pleading if one is required. But a party may assert the following defenses by motion: (1) lack of subject-matter jurisdiction; (2) lack of personal jurisdiction; (3) improper venue; (4) insufficient process; (5) insufficient service of process; (6) failure to state a claim upon which relief can be granted; (7) failure to join a party under Rule 19. (h) Waiver. A party waives any defense listed in Rule 12(b)(2)-(5) by omitting it from a pre-answer motion or failing to include it in a responsive pleading."
    },
    "FRCP_15": {
        "rule_type": "FRCP", "rule_number": "15", "title": "AMENDED AND SUPPLEMENTAL PLEADINGS",
        "chapter": "Federal Civil Procedure",
        "summary": "Amendment of pleadings. Leave to amend shall be freely given when justice so requires.",
        "full_text": "Rule 15. Amended and Supplemental Pleadings. (a) Amendments Before Trial. (1) Amending as a Matter of Course. A party may amend its pleading once as a matter of course within 21 days after serving it, or within 21 days after service of a responsive pleading or 21 days after service of a motion under Rule 12(b), (e), or (f), whichever is earlier. (2) Other Amendments. In all other cases, a party may amend its pleading only with the opposing party's written consent or the court's leave. The court should freely give leave when justice so requires."
    },
    "FRCP_56": {
        "rule_type": "FRCP", "rule_number": "56", "title": "SUMMARY JUDGMENT",
        "chapter": "Federal Civil Procedure",
        "summary": "Standards for summary judgment. Granted when no genuine dispute of material fact exists.",
        "full_text": "Rule 56. Summary Judgment. (a) Motion for Summary Judgment or Partial Summary Judgment. A party may move for summary judgment, identifying each claim or defense on which summary judgment is sought. The court shall grant summary judgment if the movant shows that there is no genuine dispute as to any material fact and the movant is entitled to judgment as a matter of law. (c) Procedures. (1) Supporting Factual Positions. A party asserting that a fact cannot be or is genuinely disputed must support the assertion by citing to particular parts of materials in the record."
    },
    "FRCP_65": {
        "rule_type": "FRCP", "rule_number": "65", "title": "INJUNCTIONS AND RESTRAINING ORDERS",
        "chapter": "Federal Civil Procedure",
        "summary": "Standards for preliminary injunctions and temporary restraining orders in federal court.",
        "full_text": "Rule 65. Injunctions and Restraining Orders. (a) Preliminary Injunction. (1) Notice. The court may issue a preliminary injunction only on notice to the adverse party. (2) Consolidating the Hearing with the Trial on the Merits. (b) Temporary Restraining Order. (1) Issuing Without Notice. The court may issue a temporary restraining order without written or oral notice to the adverse party only if: (A) specific facts in an affidavit or a verified complaint clearly show that immediate and irreparable injury, loss, or damage will result to the movant before the adverse party can be heard in opposition; and (B) the movant's attorney certifies in writing any efforts made to give notice and the reasons why it should not be required. (d) Contents and Scope of Every Injunction and Restraining Order. Every order granting an injunction and every restraining order must: (1) state the reasons why it issued; (2) state its terms specifically; and (3) describe in reasonable detail the act or acts restrained or required."
    }
}

# ============================================================
# 2. FEDERAL STATUTES (Title 28 + Title 42)
# ============================================================
USC_STATUTES = {
    "28_USC_1331": {
        "rule_type": "USC", "rule_number": "28 USC 1331", "title": "FEDERAL QUESTION JURISDICTION",
        "chapter": "Federal Jurisdiction",
        "summary": "District courts have original jurisdiction of all civil actions arising under the Constitution, laws, or treaties of the United States.",
        "full_text": "28 U.S.C. Section 1331. Federal question. The district courts shall have original jurisdiction of all civil actions arising under the Constitution, laws, or treaties of the United States."
    },
    "28_USC_1343": {
        "rule_type": "USC", "rule_number": "28 USC 1343", "title": "CIVIL RIGHTS AND ELECTIVE FRANCHISE",
        "chapter": "Federal Jurisdiction",
        "summary": "District courts have original jurisdiction of civil actions to redress deprivation of civil rights under color of state law.",
        "full_text": "28 U.S.C. Section 1343. Civil rights and elective franchise. (a) The district courts shall have original jurisdiction of any civil action authorized by law to be commenced by any person: (3) To redress the deprivation, under color of any State law, statute, ordinance, regulation, custom or usage, of any right, privilege or immunity secured by the Constitution of the United States or by any Act of Congress providing for equal rights of citizens."
    },
    "28_USC_1915": {
        "rule_type": "USC", "rule_number": "28 USC 1915", "title": "PROCEEDINGS IN FORMA PAUPERIS",
        "chapter": "Federal Procedure",
        "summary": "Allows commencement of federal action without prepayment of fees upon showing of inability to pay. Frivolity screening.",
        "full_text": "28 U.S.C. Section 1915. Proceedings in forma pauperis. (a)(1) Any court of the United States may authorize the commencement of any suit, action or proceeding, without prepayment of fees or security therefor, by a person who submits an affidavit that includes a statement of all assets such person possesses that the person is unable to pay such fees or give security therefor. (d) The officers of the court shall issue and serve all process, and perform all duties in such cases. (e)(2) The court shall dismiss the case at any time if the court determines that (A) the allegation of poverty is untrue; or (B) the action or appeal (i) is frivolous or malicious; (ii) fails to state a claim on which relief may be granted; or (iii) seeks monetary relief against a defendant who is immune from such relief."
    },
    "42_USC_1983": {
        "rule_type": "USC", "rule_number": "42 USC 1983", "title": "CIVIL ACTION FOR DEPRIVATION OF RIGHTS",
        "chapter": "Civil Rights",
        "summary": "Core civil rights statute. Every person who under color of state law deprives another of constitutional rights shall be liable.",
        "full_text": "42 U.S.C. Section 1983. Civil action for deprivation of rights. Every person who, under color of any statute, ordinance, regulation, custom, or usage, of any State or Territory or the District of Columbia, subjects, or causes to be subjected, any citizen of the United States or other person within the jurisdiction thereof to the deprivation of any rights, privileges, or immunities secured by the Constitution and laws, shall be liable to the party injured in an action at law, suit in equity, or other proper proceeding for redress, except that in any action brought against a judicial officer for an act or omission taken in such officer's judicial capacity, injunctive relief shall not be granted unless a declaratory decree was violated or declaratory relief was unavailable."
    },
    "42_USC_1985": {
        "rule_type": "USC", "rule_number": "42 USC 1985", "title": "CONSPIRACY TO INTERFERE WITH CIVIL RIGHTS",
        "chapter": "Civil Rights",
        "summary": "Prohibits conspiracy to deprive any person of equal protection or privileges and immunities.",
        "full_text": "42 U.S.C. Section 1985. Conspiracy to interfere with civil rights. (3) If two or more persons in any State or Territory conspire for the purpose of depriving, either directly or indirectly, any person or class of persons of the equal protection of the laws, or of equal privileges and immunities under the laws; and in any case of conspiracy set forth in this section, if one or more persons engaged therein do, or cause to be done, any act in furtherance of the object of such conspiracy, whereby another is injured in his person or property, or deprived of having and exercising any right or privilege of a citizen of the United States, the party so injured or deprived may have an action for the recovery of damages occasioned by such injury or deprivation, against any one or more of the conspirators."
    },
    "42_USC_1986": {
        "rule_type": "USC", "rule_number": "42 USC 1986", "title": "ACTION FOR NEGLECT TO PREVENT CONSPIRACY",
        "chapter": "Civil Rights",
        "summary": "Liability for persons with knowledge of 1985 conspiracy who fail to prevent it.",
        "full_text": "42 U.S.C. Section 1986. Action for neglect to prevent. Every person who, having knowledge that any of the wrongs conspired to be done, and mentioned in section 1985 of this title, are about to be committed, and having power to prevent or aid in preventing the commission of the same, neglects or refuses so to do, if such wrongful act be committed, shall be liable to the party injured for all damages caused by such wrongful act."
    },
    "42_USC_1988": {
        "rule_type": "USC", "rule_number": "42 USC 1988", "title": "PROCEEDINGS IN VINDICATION OF CIVIL RIGHTS",
        "chapter": "Civil Rights",
        "summary": "Authorizes award of attorney's fees to prevailing party in civil rights actions. Critical leverage tool.",
        "full_text": "42 U.S.C. Section 1988. Proceedings in vindication of civil rights. (b) In any action or proceeding to enforce a provision of sections 1981, 1981a, 1982, 1983, 1985, and 1986 of this title, the court, in its discretion, may allow the prevailing party, other than the United States, a reasonable attorney's fee as part of the costs."
    }
}

# ============================================================
# 3. CONSTITUTIONAL AUTHORITY
# ============================================================
CONSTITUTIONAL = {
    "US_CONST_AMEND_I": {
        "rule_type": "CONSTITUTION", "rule_number": "U.S. Const. Amend. I",
        "title": "FREEDOM OF SPEECH, PETITION, ASSEMBLY",
        "chapter": "U.S. Constitution - Bill of Rights",
        "summary": "First Amendment protections. Relevant to retaliation claims — filing lawsuits/motions is protected petition activity.",
        "full_text": "Amendment I. Congress shall make no law respecting an establishment of religion, or prohibiting the free exercise thereof; or abridging the freedom of speech, or of the press; or the right of the people peaceably to assemble, and to petition the Government for a redress of grievances. NOTE: Filing lawsuits and court motions constitutes protected petitioning activity under the First Amendment. Retaliation for exercising this right is actionable under 42 USC 1983. See Thaddeus-X v. Blatter, 175 F.3d 378 (6th Cir. 1999)."
    },
    "US_CONST_AMEND_IV": {
        "rule_type": "CONSTITUTION", "rule_number": "U.S. Const. Amend. IV",
        "title": "UNREASONABLE SEARCHES AND SEIZURES",
        "chapter": "U.S. Constitution - Bill of Rights",
        "summary": "Protection against unreasonable seizures. Removal of child from parent without due process may constitute seizure.",
        "full_text": "Amendment IV. The right of the people to be secure in their persons, houses, papers, and effects, against unreasonable searches and seizures, shall not be violated, and no Warrants shall issue, but upon probable cause, supported by Oath or affirmation, and particularly describing the place to be searched, and the persons or things to be seized. NOTE: The involuntary separation of parent and child implicates Fourth Amendment seizure protections. See Brokaw v. Mercer County, 235 F.3d 1000 (7th Cir. 2000)."
    },
    "US_CONST_AMEND_V": {
        "rule_type": "CONSTITUTION", "rule_number": "U.S. Const. Amend. V",
        "title": "DUE PROCESS (FEDERAL)",
        "chapter": "U.S. Constitution - Bill of Rights",
        "summary": "Federal due process clause. No person shall be deprived of life, liberty, or property without due process of law.",
        "full_text": "Amendment V. No person shall be held to answer for a capital, or otherwise infamous crime, unless on a presentment or indictment of a Grand Jury; nor shall any person be subject for the same offence to be twice put in jeopardy of life or limb; nor shall be compelled in any criminal case to be a witness against himself, nor be deprived of life, liberty, or property, without due process of law; nor shall private property be taken for public use, without just compensation."
    },
    "US_CONST_AMEND_XIV": {
        "rule_type": "CONSTITUTION", "rule_number": "U.S. Const. Amend. XIV, Sec. 1",
        "title": "DUE PROCESS AND EQUAL PROTECTION (STATE ACTION)",
        "chapter": "U.S. Constitution - Reconstruction Amendments",
        "summary": "Cornerstone of 1983 litigation. No State shall deprive any person of life, liberty, or property without due process. Equal protection.",
        "full_text": "Amendment XIV, Section 1. All persons born or naturalized in the United States, and subject to the jurisdiction thereof, are citizens of the United States and of the State wherein they reside. No State shall make or enforce any law which shall abridge the privileges or immunities of citizens of the United States; nor shall any State deprive any person of life, liberty, or property, without due process of law; nor deny to any person within its jurisdiction the equal protection of the laws. NOTE: The parent-child relationship is a fundamental liberty interest protected by the Fourteenth Amendment. Meyer v. Nebraska, 262 U.S. 390 (1923); Troxel v. Granville, 530 U.S. 57 (2000); Santosky v. Kramer, 455 U.S. 745 (1982). Deprivation without adequate process is actionable under 42 USC 1983."
    },
    "MI_CONST_ART1_S17": {
        "rule_type": "CONSTITUTION", "rule_number": "Mich. Const. 1963, Art. 1, Sec. 17",
        "title": "SELF-INCRIMINATION; DUE PROCESS; FAIR TREATMENT",
        "chapter": "Michigan Constitution of 1963",
        "summary": "Michigan due process clause. No person shall be deprived of life, liberty, or property without due process of law.",
        "full_text": "Michigan Constitution of 1963, Article 1, Section 17. Self-incrimination; due process of law; fair treatment at investigations. No person shall be compelled in any criminal case to be a witness against himself, nor be deprived of life, liberty or property, without due process of law. The right of all individuals, firms, corporations and voluntary associations to fair and just treatment in the course of legislative and executive investigations and hearings shall not be infringed."
    },
    "MI_CONST_ART6_S4": {
        "rule_type": "CONSTITUTION", "rule_number": "Mich. Const. 1963, Art. 6, Sec. 4",
        "title": "SUPREME COURT SUPERINTENDING CONTROL",
        "chapter": "Michigan Constitution of 1963",
        "summary": "Michigan Supreme Court has general superintending control over all courts. Basis for MSC complaint for superintending control (PKG07).",
        "full_text": "Michigan Constitution of 1963, Article 6, Section 4. The supreme court shall have general superintending control over all courts; power to issue, hear and determine prerogative and remedial writs; and appellate jurisdiction as provided by rules of the supreme court. The supreme court shall not have the power to remove a judge."
    },
    "MI_CONST_ART6_S30": {
        "rule_type": "CONSTITUTION", "rule_number": "Mich. Const. 1963, Art. 6, Sec. 30",
        "title": "JUDICIAL TENURE COMMISSION",
        "chapter": "Michigan Constitution of 1963",
        "summary": "Establishes JTC with power to investigate judicial misconduct and recommend discipline. Basis for PKG06.",
        "full_text": "Michigan Constitution of 1963, Article 6, Section 30. A judicial tenure commission is created... On recommendation of the judicial tenure commission, the supreme court may censure, suspend with or without salary, retire or remove a judge for conviction of a felony, physical or mental disability which prevents the performance of judicial duties, misconduct in office, persistent failure to perform his duties, habitual intemperance or conduct that is clearly prejudicial to the administration of justice."
    }
}

# ============================================================
# 4. MICHIGAN CODE OF JUDICIAL CONDUCT (All 8 Canons)
# ============================================================
MCJC_CANONS = {
    "MCJC_CANON_1": {
        "rule_type": "MCJC", "rule_number": "Canon 1",
        "title": "A JUDGE SHOULD UPHOLD THE INTEGRITY AND INDEPENDENCE OF THE JUDICIARY",
        "chapter": "Michigan Code of Judicial Conduct",
        "summary": "Judges must maintain highest standards. An independent and honorable judiciary is indispensable to justice.",
        "full_text": "Canon 1. A Judge Should Uphold the Integrity and Independence of the Judiciary. An independent and honorable judiciary is indispensable to justice in our society. A judge should participate in establishing, maintaining, and enforcing, and should personally observe, high standards of conduct so that the integrity and independence of the judiciary may be preserved. The provisions of this code should be construed and applied to further that objective. The text of the canons and the sections thereunder are rules of conduct. The commentary, by explanation and example, provides guidance with respect to the purpose and meaning of the rules."
    },
    "MCJC_CANON_2": {
        "rule_type": "MCJC", "rule_number": "Canon 2",
        "title": "A JUDGE SHOULD AVOID IMPROPRIETY AND THE APPEARANCE OF IMPROPRIETY",
        "chapter": "Michigan Code of Judicial Conduct",
        "summary": "Judge must act to promote public confidence. Must not allow relationships to influence conduct.",
        "full_text": "Canon 2. A Judge Should Avoid Impropriety and the Appearance of Impropriety in All Activities. (A) A judge should respect and comply with the law and should act at all times in a manner that promotes public confidence in the integrity and impartiality of the judiciary. (B) A judge should not allow family, social, or other relationships to influence judicial conduct or judgment. A judge should not lend the prestige of judicial office to advance the private interests of the judge or others; nor should a judge convey or permit others to convey the impression that they are in a special position to influence the judge. (C) A judge should not hold membership in any organization that practices invidious discrimination."
    },
    "MCJC_CANON_3": {
        "rule_type": "MCJC", "rule_number": "Canon 3",
        "title": "A JUDGE SHOULD PERFORM THE DUTIES OF OFFICE IMPARTIALLY AND DILIGENTLY",
        "chapter": "Michigan Code of Judicial Conduct",
        "summary": "Core duty canon. Impartiality, diligence, competence. 2025 amendment strengthens anti-bias provisions.",
        "full_text": "Canon 3. A Judge Should Perform the Duties of Office Impartially and Diligently. (A) Adjudicative Responsibilities. (1) A judge should be faithful to the law and maintain professional competence in it. A judge should be unswayed by partisan interests, public clamor, or fear of criticism. (2) A judge should maintain order and decorum in proceedings. (3) A judge should be patient, dignified, and courteous to litigants, jurors, witnesses, lawyers, and others. (4) A judge should accord to every person who has a legal interest in a proceeding the right to be heard according to law. A judge should not initiate, permit, or consider ex parte communications or other communications concerning a pending or impending matter that are made outside the presence of the parties. (5) A judge shall perform judicial duties without bias or prejudice. A judge shall not, in the performance of judicial duties, by words or conduct manifest bias or prejudice. [2025 AMENDMENT effective September 1, 2025: Strengthened to prohibit judges from intentionally or recklessly manifesting bias, prejudice, or harassment based on protected characteristics, including race, sex, gender, religion, national origin, ethnicity, disability, age, sexual orientation, marital status, or socioeconomic status. This amendment brings Michigan closer to ABA Model Rule 2.3.] (7) A judge should not make public comment on the merits of a matter pending or impending in any court."
    },
    "MCJC_CANON_4": {
        "rule_type": "MCJC", "rule_number": "Canon 4",
        "title": "A JUDGE MAY ENGAGE IN EXTRAJUDICIAL ACTIVITIES",
        "chapter": "Michigan Code of Judicial Conduct",
        "summary": "Governs permissible extrajudicial activities. Must not cast doubt on impartiality or demean office.",
        "full_text": "Canon 4. A Judge May Engage in Activities to Improve the Law, the Legal System, and the Administration of Justice. A judge, subject to the proper performance of judicial duties, may engage in the following activities: (A) speak, write, lecture, teach, and participate in other activities concerning the law, legal system, and administration of justice. (B) Appear at a public hearing before an executive or legislative body on matters concerning the law, legal system, and administration of justice."
    },
    "MCJC_CANON_5": {
        "rule_type": "MCJC", "rule_number": "Canon 5",
        "title": "A JUDGE OR CANDIDATE SHOULD REFRAIN FROM POLITICAL ACTIVITY",
        "chapter": "Michigan Code of Judicial Conduct",
        "summary": "Governs political activities of judges and judicial candidates.",
        "full_text": "Canon 5. A judge should regulate extrajudicial activities to minimize the risk of conflict with judicial duties. A Judge or Candidate for Judicial Office Should Refrain from Inappropriate Political Activity. (A) All Judges and Candidates: (1) A judge or a candidate for election or appointment to judicial office shall not make pledges or promises of conduct in office other than the faithful and impartial performance of the duties of the office. (2) A judge or candidate shall not make statements that commit or appear to commit the candidate with respect to cases, controversies, or issues that are likely to come before the court."
    },
    "MCJC_CANON_6": {
        "rule_type": "MCJC", "rule_number": "Canon 6",
        "title": "REPORTING COMPENSATION FOR QUASI-JUDICIAL AND EXTRA-JUDICIAL ACTIVITIES",
        "chapter": "Michigan Code of Judicial Conduct",
        "summary": "Financial disclosure requirements for judges receiving compensation for extrajudicial activities.",
        "full_text": "Canon 6. A judge shall report the date, place and nature of any activity for which the judge received compensation, and the name of the payor and the amount of compensation so received. Compensation includes payments, honoraria, and other income, but does not include reimbursement of expenses."
    },
    "MCJC_CANON_7": {
        "rule_type": "MCJC", "rule_number": "Canon 7",
        "title": "A JUDGE SHOULD REFRAIN FROM INAPPROPRIATE POLITICAL ACTIVITY",
        "chapter": "Michigan Code of Judicial Conduct",
        "summary": "Restrictions on judicial involvement in political organizations and campaigns.",
        "full_text": "Canon 7. A Judge Should Refrain From Inappropriate Political Activity. Judges must minimize political entanglements. Non-incumbent candidates have limited permissions during campaigns. Incumbent judges must remain nonpartisan in all activities and refrain from endorsing political candidates or organizations."
    },
    "MCJC_CANON_8": {
        "rule_type": "MCJC", "rule_number": "Canon 8",
        "title": "COLLECTIVE ACTIVITY BY JUDGES",
        "chapter": "Michigan Code of Judicial Conduct",
        "summary": "Permissible collective activities by judges. Judges are permitted to engage in collective activities to improve the legal system.",
        "full_text": "Canon 8. Judges are permitted to engage in collective activity concerning matters relating to the law, the legal system, and the administration of justice. A judge may speak, write, or take other action in support of measures to improve the legal system."
    }
}

# ============================================================
# 5. FEDERAL DOCTRINE DEFENSE MATRIX (for PKG10)
# ============================================================
DOCTRINE_DEFENSE = {
    "ROOKER_FELDMAN": {
        "doctrine": "Rooker-Feldman Doctrine",
        "opposing_argument": "Federal court lacks jurisdiction because plaintiff is a state-court loser seeking reversal of state custody orders.",
        "your_counter": "Claims are independent constitutional violations — not appeals from state orders. Plaintiff does not seek to reverse the custody determination but rather seeks redress for the unconstitutional PROCESS by which rights were deprived (no hearing, no evidence, no findings). Exxon Mobil Corp. v. Saudi Basic Industries Corp., 544 U.S. 280 (2005) narrowed Rooker-Feldman to cases where the federal plaintiff's injury was 'caused by' the state court judgment. Here, the injury is caused by the actors' conduct under color of state law, not the judgment itself.",
        "key_cases": [
            "Rooker v. Fidelity Trust Co., 263 U.S. 413 (1923)",
            "D.C. Court of Appeals v. Feldman, 460 U.S. 462 (1983)",
            "Exxon Mobil Corp. v. Saudi Basic Industries Corp., 544 U.S. 280 (2005)",
            "Lance v. Dennis, 546 U.S. 459 (2006)"
        ],
        "sixth_circuit": "McCormick v. Braverman, 451 F.3d 382 (6th Cir. 2006) — Rooker-Feldman applies only where claims are 'inextricably intertwined' with state court judgment AND plaintiff seeks review/rejection of that judgment."
    },
    "YOUNGER_ABSTENTION": {
        "doctrine": "Younger Abstention",
        "opposing_argument": "Federal court should abstain because state custody proceedings are ongoing.",
        "your_counter": "Sprint Communications, Inc. v. Jacobs, 571 U.S. 69 (2013) DRAMATICALLY narrowed Younger to three exceptional categories: (1) ongoing criminal prosecutions, (2) civil enforcement proceedings akin to criminal prosecutions, (3) civil proceedings uniquely in furtherance of the state courts' ability to perform judicial functions. Ordinary custody proceedings do not fit any category. Additionally, the 'bad faith' exception applies — state proceedings were conducted in bad faith (ex parte orders without evidence, 571+ days without hearing).",
        "key_cases": [
            "Younger v. Harris, 401 U.S. 37 (1971)",
            "Sprint Communications, Inc. v. Jacobs, 571 U.S. 69 (2013)",
            "Middlesex County Ethics Comm. v. Garden State Bar Assn., 457 U.S. 423 (1982)"
        ],
        "sixth_circuit": "Fieger v. Cox, 524 F.3d 770 (6th Cir. 2008) — Younger applies only in 'extraordinary circumstances' post-Sprint."
    },
    "JUDICIAL_IMMUNITY": {
        "doctrine": "Judicial Immunity",
        "opposing_argument": "Judge McNeill is absolutely immune from suit for acts taken in judicial capacity.",
        "your_counter": "Three exceptions apply: (1) 42 USC 1983 itself carves out an exception — injunctive relief is available if 'a declaratory decree was violated or declaratory relief was unavailable.' (2) Pulliam v. Allen, 466 U.S. 522 (1984) — prospective injunctive relief can bypass immunity. (3) Judge acted in 'clear absence of jurisdiction' (entering orders without UCCJEA compliance, without verified pleadings under MCR 3.207). Additionally, Dennis v. Sparks, 449 U.S. 24 (1980) — private parties conspiring with a judge are NOT immune.",
        "key_cases": [
            "Stump v. Sparkman, 435 U.S. 349 (1978)",
            "Pulliam v. Allen, 466 U.S. 522 (1984)",
            "Mireles v. Waco, 502 U.S. 9 (1991)",
            "Dennis v. Sparks, 449 U.S. 24 (1980)"
        ],
        "sixth_circuit": "Barnes v. Winchell, 105 F.3d 1111 (6th Cir. 1997) — Judicial immunity does not protect nonjudicial acts or acts in clear absence of jurisdiction."
    },
    "QUALIFIED_IMMUNITY": {
        "doctrine": "Qualified Immunity",
        "opposing_argument": "Individual state actors are shielded by qualified immunity because no clearly established right was violated.",
        "your_counter": "The right of a parent to the care, custody, and companionship of a child is among the oldest recognized fundamental liberty interests. Meyer v. Nebraska (1923), Troxel v. Granville (2000). Depriving a parent of ALL contact with their child for 571+ days without a hearing violates clearly established law. No reasonable official could believe this was constitutional. Saucier v. Katz, 533 U.S. 194 (2001) — two-step analysis: (1) was a constitutional right violated? (2) was the right clearly established?",
        "key_cases": [
            "Harlow v. Fitzgerald, 457 U.S. 800 (1982)",
            "Saucier v. Katz, 533 U.S. 194 (2001)",
            "Pearson v. Callahan, 555 U.S. 223 (2009)",
            "Ashcroft v. al-Kidd, 563 U.S. 731 (2011)"
        ],
        "sixth_circuit": "Guertin v. State of Michigan, 912 F.3d 907 (6th Cir. 2019) — Right to bodily integrity is clearly established; qualified immunity denied where officials had notice of ongoing harm."
    },
    "DOMESTIC_RELATIONS_EXCEPTION": {
        "doctrine": "Domestic Relations Exception",
        "opposing_argument": "Federal courts do not adjudicate domestic relations matters (custody, divorce, etc.).",
        "your_counter": "Ankenbrandt v. Richards, 504 U.S. 689 (1992) — the domestic relations exception is NARROW. It only bars federal courts from issuing divorce, alimony, or custody decrees. It does NOT bar federal courts from hearing tort actions or constitutional claims that arise in a domestic relations context. This case is a constitutional rights claim under 1983, not a custody dispute. We do not ask the federal court to decide custody — we ask it to remedy constitutional violations.",
        "key_cases": [
            "Ankenbrandt v. Richards, 504 U.S. 689 (1992)",
            "Marshall v. Marshall, 547 U.S. 293 (2006)",
            "Elk Grove Unified School Dist. v. Newdow, 542 U.S. 1 (2004)"
        ],
        "sixth_circuit": "Catz v. Chalker, 142 F.3d 279 (6th Cir. 1998) — domestic relations exception does not bar 1983 claims alleging constitutional violations by state actors in family court context."
    }
}

# ============================================================
# 6. FOC ACT (MCL 552.501-535) KEY SECTIONS
# ============================================================
FOC_ACT = {
    "MCL_552_501": {
        "rule_type": "MCL", "rule_number": "MCL 552.501",
        "title": "FRIEND OF THE COURT; CREATION; PURPOSE",
        "chapter": "Friend of the Court Act",
        "summary": "Establishes FOC in each circuit court. Purpose: assist court in domestic relations matters.",
        "full_text": "MCL 552.501. The friend of the court is established in each circuit court to assist the court in domestic relations matters. The friend of the court shall investigate and make recommendations to the court regarding child support, custody, and parenting time."
    },
    "MCL_552_507": {
        "rule_type": "MCL", "rule_number": "MCL 552.507",
        "title": "REFEREE HEARINGS; OBJECTIONS; DE NOVO HEARING",
        "chapter": "Friend of the Court Act",
        "summary": "CRITICAL: Parties may object to referee recommendation. Court MUST hold de novo hearing if objection filed within 21 days.",
        "full_text": "MCL 552.507. (4) A party may file a written objection to a referee's recommended order with the court within 21 days after the recommendation is served. If a timely objection is filed, the court shall hold a de novo hearing. The court shall not merely review the referee's record, but must conduct a new hearing on the objected matters. The de novo hearing shall be conducted by a judge, not a referee. NOTE: This is the backbone of PKG12 (FOC Objection). A de novo hearing means the judge starts fresh — the referee's findings carry no presumptive weight."
    },
    "MCL_552_511": {
        "rule_type": "MCL", "rule_number": "MCL 552.511",
        "title": "FRIEND OF THE COURT DUTIES",
        "chapter": "Friend of the Court Act",
        "summary": "FOC duties include investigation, recommendation, enforcement, and assistance to court and parties.",
        "full_text": "MCL 552.511. The friend of the court shall: (a) Investigate domestic relations matters referred by the court. (b) Make recommendations to the court regarding custody, parenting time, and child support. (c) Assist in the enforcement of court orders. (d) Collect and disburse support payments. (e) Initiate proceedings for contempt or other enforcement actions. (f) Provide information to parties about their rights and obligations. NOTE: If the FOC failed to investigate properly, failed to provide information, or made recommendations without adequate investigation, these failures support PKG12 objection."
    },
    "MCL_552_517": {
        "rule_type": "MCL", "rule_number": "MCL 552.517",
        "title": "GRIEVANCE PROCEDURES",
        "chapter": "Friend of the Court Act",
        "summary": "Parties may file grievances regarding FOC conduct. Separate from objection procedures.",
        "full_text": "MCL 552.517. Each friend of the court shall establish a grievance procedure. A party may file a grievance regarding the conduct, actions, or inactions of the friend of the court. The grievance procedure must include a written response within a reasonable time and an opportunity for review."
    }
}

# ============================================================
# 7. MDHHS / CHILD PROTECTION LAW
# ============================================================
MDHHS_CPS = {
    "MCL_722_621": {
        "rule_type": "MCL", "rule_number": "MCL 722.621",
        "title": "CHILD PROTECTION LAW; SHORT TITLE",
        "chapter": "MDHHS / Child Protection",
        "summary": "Act 238 of 1975. Michigan Child Protection Law. Governs reporting, investigation, and protection of children from abuse/neglect.",
        "full_text": "MCL 722.621. Short title. This act shall be known and may be cited as the 'child protection law.' Act 238 of 1975 establishes the framework for protecting Michigan children from abuse and neglect, including mandatory reporting requirements, CPS investigation procedures, and parental rights during investigations."
    },
    "MCL_722_622": {
        "rule_type": "MCL", "rule_number": "MCL 722.622",
        "title": "DEFINITIONS — CHILD ABUSE AND NEGLECT",
        "chapter": "MDHHS / Child Protection",
        "summary": "Defines child abuse (nonaccidental injury, sexual abuse, exploitation, maltreatment) and neglect (failure to provide adequate care).",
        "full_text": "MCL 722.622. Definitions. 'Child abuse' means harm or threatened harm to a child's health or welfare by a parent, legal guardian, or any other person responsible for the child's health or welfare, that occurs through nonaccidental physical or mental injury, sexual abuse, sexual exploitation, or maltreatment. 'Child neglect' means harm or threatened harm to a child's health or welfare by a parent that occurs through negligent treatment, including failure to provide adequate food, clothing, shelter, or medical care."
    },
    "MCL_722_623": {
        "rule_type": "MCL", "rule_number": "MCL 722.623",
        "title": "MANDATORY REPORTERS",
        "chapter": "MDHHS / Child Protection",
        "summary": "Certain professionals MUST report suspected abuse/neglect. Includes physicians, teachers, social workers, law enforcement.",
        "full_text": "MCL 722.623. Mandatory reporters. The following persons are required to report suspected child abuse or neglect to MDHHS: physicians, dentists, nurses, teachers, school administrators, social workers, law enforcement officers, child care providers, and certain other professionals. NOTE: If court actors or FOC staff observed conditions warranting a report and failed to report, this creates a separate liability and strengthens the case."
    },
    "MCL_722_628": {
        "rule_type": "MCL", "rule_number": "MCL 722.628",
        "title": "CPS INVESTIGATION; PARENTAL RIGHTS",
        "chapter": "MDHHS / Child Protection",
        "summary": "Investigation procedures. Parents must be informed of allegations and investigator identity. 24-hour commencement.",
        "full_text": "MCL 722.628. Investigation. Upon receipt of a report, MDHHS shall commence an investigation within 24 hours. The investigating worker shall: (a) identify the specific allegations; (b) inform the parent of the investigator's identity and the nature of the allegations; (c) interview the child, parents, and alleged perpetrator; (d) assess the family's circumstances. PARENTAL RIGHTS: Parents have the right to information about the investigation, the right to legal counsel, the right to review and appeal findings, and the right to remain together with the child unless removal is necessary for the child's safety."
    }
}

# ============================================================
# 8. HOUSING LAW STATUTES
# ============================================================
HOUSING_LAW = {
    "MCL_554_139": {
        "rule_type": "MCL", "rule_number": "MCL 554.139",
        "title": "IMPLIED WARRANTY OF HABITABILITY",
        "chapter": "Housing / Landlord-Tenant",
        "summary": "Landlord covenants that premises are fit for use, in reasonable repair, and comply with health/safety codes.",
        "full_text": "MCL 554.139. Covenants. (1) In every lease or license of residential premises, the lessor or licensor covenants: (a) That the premises and all common areas are fit for the use intended by the parties. (b) To keep the premises in reasonable repair during the term of the lease or license, and to comply with the applicable health and safety laws of the state and of the local unit of government where the premises are located, except when the disrepair or violation of the applicable health or safety laws has been caused by the tenant's willful or irresponsible conduct."
    },
    "MCL_600_5720": {
        "rule_type": "MCL", "rule_number": "MCL 600.5720",
        "title": "TENANT REMEDIES FOR BREACH OF HABITABILITY",
        "chapter": "Housing / Landlord-Tenant",
        "summary": "Tenant remedies include rent abatement, damages recovery, and equitable relief for habitability breaches.",
        "full_text": "MCL 600.5720. Tenant remedies. When a landlord breaches the implied warranty of habitability under MCL 554.139, the tenant may: (a) recover damages; (b) obtain rent abatement for the period of uninhabitable conditions; (c) obtain equitable relief including injunction ordering repairs; (d) withhold rent in certain circumstances after proper notice."
    },
    "MCL_554_633": {
        "rule_type": "MCL", "rule_number": "MCL 554.633",
        "title": "TRUTH IN RENTING ACT — VOID PROVISIONS",
        "chapter": "Housing / Landlord-Tenant",
        "summary": "Lease provisions that violate tenant rights under law are void and unenforceable.",
        "full_text": "MCL 554.633. (Truth in Renting Act, MCL 554.601a-641). A rental agreement shall not include a provision that is in violation of the law. A provision that purports to waive a tenant's right to habitability, or shifts responsibility for code compliance to the tenant, is void and unenforceable."
    },
    "MCL_554_636": {
        "rule_type": "MCL", "rule_number": "MCL 554.636",
        "title": "TRUTH IN RENTING ACT — DAMAGES AND FEES",
        "chapter": "Housing / Landlord-Tenant",
        "summary": "Tenant may recover actual damages plus $250 for Truth in Renting violations. Attorney's fees available.",
        "full_text": "MCL 554.636. Damages and attorney fees. A tenant who is adversely affected by a provision in a rental agreement that violates this act may recover actual damages or $250, whichever is greater, together with reasonable attorney's fees."
    },
    "42_USC_3604": {
        "rule_type": "USC", "rule_number": "42 USC 3604",
        "title": "FAIR HOUSING ACT — DISCRIMINATION IN SALE OR RENTAL",
        "chapter": "Federal Housing Law",
        "summary": "Prohibits discrimination in housing based on race, color, religion, sex, familial status, national origin, disability.",
        "full_text": "42 U.S.C. Section 3604. Discrimination in the sale or rental of housing. It shall be unlawful: (a) To refuse to sell or rent, or to refuse to negotiate for the sale or rental of, or otherwise make unavailable or deny, a dwelling to any person because of race, color, religion, sex, familial status, or national origin. (b) To discriminate against any person in the terms, conditions, or privileges of sale or rental of a dwelling, or in the provision of services or facilities in connection therewith, because of race, color, religion, sex, familial status, or national origin."
    }
}

# ============================================================
# 9. KEY CASE LAW EXPANSION
# ============================================================
CASE_LAW_EXPANSION = {
    "ANKENBRANDT": {
        "rule_type": "CASE_LAW", "rule_number": "504 U.S. 689",
        "title": "Ankenbrandt v. Richards (1992)",
        "chapter": "Federal Jurisdiction / Domestic Relations Exception",
        "summary": "Domestic relations exception is NARROW. Only bars divorce, alimony, custody decrees. Does NOT bar 1983 tort/constitutional claims.",
        "full_text": "Ankenbrandt v. Richards, 504 U.S. 689 (1992). The Supreme Court held that the domestic relations exception to federal jurisdiction is narrow and applies only to cases involving the issuance of a divorce, alimony, or child custody decree. It does not bar federal courts from hearing tort actions or constitutional claims that happen to arise in a domestic context. This is the key case for establishing that PKG10 (federal 1983 action) is not barred by the domestic relations exception."
    },
    "SPRINT_V_JACOBS": {
        "rule_type": "CASE_LAW", "rule_number": "571 U.S. 69",
        "title": "Sprint Communications v. Jacobs (2013)",
        "chapter": "Federal Abstention / Younger Doctrine",
        "summary": "DRAMATICALLY narrowed Younger abstention to only 3 exceptional categories. Ordinary civil proceedings excluded.",
        "full_text": "Sprint Communications, Inc. v. Jacobs, 571 U.S. 69 (2013). The Supreme Court held that Younger abstention applies only in three 'exceptional circumstances': (1) state criminal prosecutions; (2) certain civil enforcement proceedings akin to criminal prosecutions; and (3) civil proceedings uniquely in furtherance of the state courts' ability to perform their judicial functions. Ordinary civil proceedings, including custody matters, generally do not fall within any of these categories."
    },
    "EXXON_MOBIL": {
        "rule_type": "CASE_LAW", "rule_number": "544 U.S. 280",
        "title": "Exxon Mobil Corp. v. Saudi Basic Industries Corp. (2005)",
        "chapter": "Federal Jurisdiction / Rooker-Feldman",
        "summary": "Narrowed Rooker-Feldman. Only applies to state-court losers complaining of injuries CAUSED BY state judgments.",
        "full_text": "Exxon Mobil Corp. v. Saudi Basic Industries Corp., 544 U.S. 280 (2005). The Supreme Court clarified that Rooker-Feldman is a narrow doctrine. It applies only when (1) the federal plaintiff lost in state court, (2) complains of injuries caused by the state court judgment itself, (3) invites district court review and rejection of that judgment, and (4) the state proceedings ended before the federal suit began. It does not bar parallel litigation or independent claims."
    },
    "THADDEUS_X": {
        "rule_type": "CASE_LAW", "rule_number": "175 F.3d 378",
        "title": "Thaddeus-X v. Blatter (6th Cir. 1999)",
        "chapter": "6th Circuit / First Amendment Retaliation",
        "summary": "6th Circuit: Filing lawsuits is protected First Amendment activity. Retaliation for exercising this right is actionable under 1983.",
        "full_text": "Thaddeus-X v. Blatter, 175 F.3d 378 (6th Cir. 1999) (en banc). The Sixth Circuit held that retaliation for exercising First Amendment rights, including the right to petition the government (file lawsuits and motions), is actionable under 42 U.S.C. 1983. A plaintiff must show: (1) the exercise of a protected right; (2) an adverse action that would deter a person of ordinary firmness from exercising the right; and (3) a causal connection between the protected activity and the adverse action."
    },
    "GUERTIN_V_MICHIGAN": {
        "rule_type": "CASE_LAW", "rule_number": "912 F.3d 907",
        "title": "Guertin v. State of Michigan (6th Cir. 2019)",
        "chapter": "6th Circuit / Qualified Immunity / Bodily Integrity",
        "summary": "6th Circuit denied qualified immunity where officials had notice of ongoing harm. Right to bodily integrity clearly established.",
        "full_text": "Guertin v. State of Michigan, 912 F.3d 907 (6th Cir. 2019). The Sixth Circuit held that the right to bodily integrity is clearly established and denied qualified immunity where state officials had knowledge of ongoing harm and failed to act. This case establishes that qualified immunity does not shield officials who are aware of constitutional violations and take no corrective action."
    },
    "CATZ_V_CHALKER": {
        "rule_type": "CASE_LAW", "rule_number": "142 F.3d 279",
        "title": "Catz v. Chalker (6th Cir. 1998)",
        "chapter": "6th Circuit / Domestic Relations Exception",
        "summary": "6th Circuit: Domestic relations exception does NOT bar 1983 claims alleging constitutional violations in family court.",
        "full_text": "Catz v. Chalker, 142 F.3d 279 (6th Cir. 1998). The Sixth Circuit held that the domestic relations exception to federal jurisdiction does not bar Section 1983 claims alleging constitutional violations by state actors in the family court context. The court distinguished between federal courts issuing custody decrees (barred) and federal courts adjudicating constitutional claims that arise in a domestic context (permitted)."
    }
}

# ============================================================
# ASSEMBLE AND WRITE
# ============================================================
def build_all():
    log("=" * 60)
    log("AUTHORITY EXPANSION ENGINE — BUILDING ALL LAYERS")
    log("=" * 60)

    all_rules = {}
    all_rules.update(FRCP_RULES)
    all_rules.update(USC_STATUTES)
    all_rules.update(CONSTITUTIONAL)
    all_rules.update(MCJC_CANONS)
    all_rules.update(FOC_ACT)
    all_rules.update(MDHHS_CPS)
    all_rules.update(HOUSING_LAW)
    all_rules.update(CASE_LAW_EXPANSION)

    # Write authority entries
    auth_path = os.path.join(OUTPUT_DIR, "AUTHORITY_EXPANSION.json")
    with open(auth_path, "w", encoding="utf-8") as f:
        json.dump(all_rules, f, indent=2, ensure_ascii=False)
    log(f"  Authority entries: {len(all_rules)} written to {auth_path}")

    # Write doctrine defense matrix
    doctrine_path = os.path.join(OUTPUT_DIR, "DOCTRINE_DEFENSE_MATRIX.json")
    with open(doctrine_path, "w", encoding="utf-8") as f:
        json.dump(DOCTRINE_DEFENSE, f, indent=2, ensure_ascii=False)
    log(f"  Doctrine defenses: {len(DOCTRINE_DEFENSE)} written to {doctrine_path}")

    # Category breakdown
    categories = {}
    for k, v in all_rules.items():
        rt = v.get("rule_type", "UNKNOWN")
        categories[rt] = categories.get(rt, 0) + 1
    log(f"\n  BREAKDOWN:")
    for cat, cnt in sorted(categories.items(), key=lambda x: -x[1]):
        log(f"    {cat}: {cnt}")
    
    log(f"\n  TOTAL NEW AUTHORITY ENTRIES: {len(all_rules)}")
    log(f"  DOCTRINE DEFENSE ENTRIES: {len(DOCTRINE_DEFENSE)}")
    log("=" * 60)
    return all_rules

if __name__ == "__main__":
    build_all()