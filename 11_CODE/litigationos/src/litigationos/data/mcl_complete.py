"""Complete Michigan Compiled Laws (MCL) — Static Dataset for LitigationOS.

Key chapters for family law, civil procedure, criminal, and FOIA litigation.
Sources: legislature.mi.gov, as of March 2026.
"""

from __future__ import annotations

MCL_STATUTES: list[dict] = [
    # =========================================================================
    # MCL CHAPTER 722 — CHILDREN (Child Custody Act of 1970)
    # =========================================================================
    {
        "citation": "MCL 722.21",
        "title": "Short Title",
        "chapter": "Chapter 722 - Children",
        "act": "Child Custody Act of 1970 (Act 91)",
        "full_text": "This act shall be known and may be cited as the 'child custody act of 1970'.",
        "cross_references": ["MCL 722.22", "MCR 3.210"],
    },
    {
        "citation": "MCL 722.22",
        "title": "Definitions",
        "chapter": "Chapter 722 - Children",
        "act": "Child Custody Act of 1970 (Act 91)",
        "full_text": """As used in this act:
(a) 'Best interests of the child' means the sum total of the following factors to be considered, evaluated, and determined by the court:
(i) The love, affection, and other emotional ties existing between the parties involved and the child.
(ii) The capacity and disposition of the parties involved to give the child love, affection, and guidance and to continue the education and raising of the child in his or her religion or creed, if any.
(iii) The capacity and disposition of the parties involved to provide the child with food, clothing, medical care or other remedial care.
(iv) The length of time the child has lived in a stable, satisfactory environment, and the desirability of maintaining continuity.
(v) The permanence, as a family unit, of the existing or proposed custodial home or homes.
(vi) The moral fitness of the parties involved.
(vii) The mental and physical health of the parties involved.
(viii) The home, school, and community record of the child.
(ix) The reasonable preference of the child, if the court considers the child to be of sufficient age to express preference.
(x) The willingness and ability of each of the parties to facilitate and encourage a close and continuing parent-child relationship between the child and the other parent or the child and the parents.
(xi) Domestic violence, regardless of whether the violence was directed against or witnessed by the child.
(xii) Any other factor considered by the court to be relevant to a particular child custody dispute.
(b) 'Child' means a minor.
(c) 'Custody' means the physical care, custody, and control of a child.
(d) 'Party' means a parent, guardian, or other person having legal custody or claiming the right to legal custody.""",
        "practice_tips": "These definitions mirror MCL 722.23 best interest factors. Factor (x) is the 'friendly parent' factor — key for parental alienation claims.",
        "cross_references": ["MCL 722.23", "MCR 3.210"],
    },
    {
        "citation": "MCL 722.23",
        "title": "Best Interests of the Child; Factors",
        "chapter": "Chapter 722 - Children",
        "act": "Child Custody Act of 1970 (Act 91)",
        "full_text": """As used in this act, 'best interests of the child' means the sum total of the following factors to be considered, evaluated, and determined by the court:

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

(l) Any other factor considered by the court to be relevant to a particular child custody dispute.""",
        "practice_tips": "THE most important statute in Michigan family law. Court MUST evaluate ALL 12 factors and make findings on each. Factor (j) is the 'friendly parent' / parental alienation factor — willingness to facilitate relationship with the other parent. Factor (f) moral fitness and (k) domestic violence are commonly litigated. Factor (l) is the catch-all. Failure to address all factors is reversible error.",
        "cross_references": ["MCL 722.27", "MCL 722.27a", "MCR 3.210", "Vodvarka v Grasmeyer 259 Mich App 499"],
    },
    {
        "citation": "MCL 722.24",
        "title": "Jurisdiction",
        "chapter": "Chapter 722 - Children",
        "act": "Child Custody Act of 1970 (Act 91)",
        "full_text": "In actions involving dispute of the custody of a minor child, the circuit court shall have jurisdiction. The court may enter orders it considers just, including but not limited to orders concerning: (a) granting custody to one or both parents; (b) establishing conditions of custody; (c) establishing parenting time schedules.",
        "cross_references": ["MCL 722.26", "MCR 3.201"],
    },
    {
        "citation": "MCL 722.25",
        "title": "Custody to Third Person",
        "chapter": "Chapter 722 - Children",
        "act": "Child Custody Act of 1970 (Act 91)",
        "full_text": "If the court finds that neither parent is fit and proper to have custody, the court may award custody to a third person if the court finds that granting custody to the third person is in the best interests of the child.",
        "cross_references": ["MCL 722.23"],
    },
    {
        "citation": "MCL 722.26a",
        "title": "Joint Custody",
        "chapter": "Chapter 722 - Children",
        "act": "Child Custody Act of 1970 (Act 91)",
        "full_text": "(1) In custody disputes between parents, the parents shall be advised of joint custody. At the request of either parent, the court shall consider an award of joint custody. The court shall determine whether joint custody is in the best interests of the child by considering the factors in section 3 [MCL 722.23]. (2) The court shall not award joint custody unless the court is satisfied that the parents are able to agree and cooperate. (7) 'Joint custody' means an order of the court in which the parents share decision-making authority for the child and in which the child's time is divided between the parents' homes in a manner determined to be in the best interests of the child.",
        "practice_tips": "Joint custody requires cooperative parents. If the parents cannot communicate or agree, joint custody is inappropriate. Court considers MCL 722.23 factors.",
        "cross_references": ["MCL 722.23", "MCL 722.27"],
    },
    {
        "citation": "MCL 722.27",
        "title": "Powers of the Court; Custody Orders",
        "chapter": "Chapter 722 - Children",
        "act": "Child Custody Act of 1970 (Act 91)",
        "full_text": """(1) If a child custody dispute has been submitted to the circuit court as an original action or has arisen incidentally from another action, the court shall declare the child's inherent rights and establish the rights and duties as to the child's custody, support, and parenting time in accordance with this act.

(a) The court shall not modify or amend its previous judgments or orders or make new orders so as to change the established custodial environment of a child unless there is presented clear and convincing evidence that it is in the best interest of the child. The custodial environment of a child is established if over an appreciable time the child naturally looks to the custodian for guidance, discipline, the necessities of life, and parental comfort. The age of the child, the physical environment, and the inclination of the custodian and the child as to permanency of the relationship shall also be considered.

(b) If a motion is filed to change custody and the movant has not established a custodial environment, the court shall determine custody based on the preponderance of the evidence standard.

(c) Before the court enters an order modifying custody, the court shall determine whether proper cause or a change of circumstances exists. If the court determines that either exists, the court shall then consider the best interest factors in MCL 722.23.

(d) 'Proper cause' means one or more appropriate grounds that have or could have a significant effect on the child's life sufficient to warrant a reevaluation of the custody order.

(e) 'Change of circumstances' means that since the entry of the last custody order, the conditions surrounding custody have materially changed.""",
        "practice_tips": "KEY: To modify custody, must show (1) proper cause or change of circumstances, THEN (2) best interests analysis. If established custodial environment exists, standard is CLEAR AND CONVINCING evidence. If no ECE, standard is PREPONDERANCE. Vodvarka v Grasmeyer defines 'proper cause' and 'change of circumstances'.",
        "cross_references": ["MCL 722.23", "MCL 722.27a", "MCR 3.210", "Vodvarka v Grasmeyer 259 Mich App 499"],
    },
    {
        "citation": "MCL 722.27a",
        "title": "Parenting Time",
        "chapter": "Chapter 722 - Children",
        "act": "Child Custody Act of 1970 (Act 91)",
        "full_text": """(1) A child has a right to parenting time with a parent unless it is shown on the record by clear and convincing evidence that it would endanger the child's physical, mental, or emotional health.

(2) The court may modify a parenting time order at any time upon a showing of proper cause or a change of circumstances.

(3) In determining the frequency, duration, and type of parenting time, the court shall consider:
(a) The existence of any special circumstances or needs of the child.
(b) Whether the child is a nursing child less than 6 months of age, or less than 1 year of age if the child receives substantial nutrition through nursing.
(c) The reasonable likelihood of abuse or neglect of the child during parenting time.
(d) The reasonable likelihood of abuse of a parent resulting from the exercise of parenting time.
(e) The inconvenience to, and burdensome impact or effect on, the child of traveling for purposes of parenting time.
(f) Whether a parent can reasonably be expected to exercise parenting time in accordance with the court order.
(g) Whether a parent has frequently failed to exercise reasonable parenting time.
(h) The threatened or actual detention of the child with the intent to retain or conceal the child from the other parent or from a third person who has legal custody.
(i) Any other relevant factors.

(4) Parenting time shall be granted in specific terms in order to avoid conflict and confusion.

(5) If a parent fails to exercise parenting time, the other parent may seek make-up parenting time.

(6) Make-up parenting time shall be: (a) of the same type and duration; (b) within 1 year of the missed parenting time.

(7) Parenting time is independent of child support. A parent shall not be denied parenting time for failure to pay support, and support shall not be withheld for failure to provide parenting time.

(8) The court may restrict or deny parenting time only if the court determines by a preponderance of the evidence that parenting time would endanger the child's physical, mental, or emotional health.

(9) If supervised parenting time is ordered, the court shall state the reasons on the record.""",
        "practice_tips": "CRITICAL: Parenting time is a RIGHT of the child — can only be denied by clear and convincing evidence of endangerment. Factor (g) — failure to exercise parenting time can be used against the non-exercising parent. Factor (h) — detention/concealment of child is a serious factor. Parenting time and child support are INDEPENDENT — cannot withhold one for the other. Make-up time available within 1 year.",
        "cross_references": ["MCL 722.23", "MCL 722.27", "MCR 3.210", "Shade v Wright 291 Mich App 17"],
    },
    {
        "citation": "MCL 722.27b",
        "title": "Change of Domicile",
        "chapter": "Chapter 722 - Children",
        "act": "Child Custody Act of 1970 (Act 91)",
        "full_text": "(1) A parent of a child whose custody is governed by court order shall not change the legal residence of the child to a location that is more than 100 miles from the child's legal residence at the time of commencement of the action in which the custody order was issued. (2) A parent who wishes to change the legal residence must seek court approval or obtain the other parent's written consent. (3) The court shall consider the following factors: (a) whether the move has the capacity to improve the quality of life for both the child and the relocating parent; (b) the degree to which each parent has complied with court orders; (c) whether the relocating parent is seeking the move to defeat the other parent's right to parenting time; (d) the feasibility of preserving the relationship between the child and the non-relocating parent.",
        "practice_tips": "100-mile rule. Moving without consent or court approval is a violation. Court examines whether the move improves quality of life AND preserves the relationship with the other parent.",
        "cross_references": ["MCL 722.31", "MCR 3.211"],
    },
    {
        "citation": "MCL 722.28",
        "title": "Attorney Fees",
        "chapter": "Chapter 722 - Children",
        "act": "Child Custody Act of 1970 (Act 91)",
        "full_text": "The court may order a party to pay the reasonable attorney fees and expenses of the other party if the court finds that the party's actions in the case were frivolous. The court may also order attorney fees when a party's financial circumstances make it necessary.",
        "cross_references": ["MCL 600.2591", "MCR 2.625"],
    },
    {
        "citation": "MCL 722.30",
        "title": "Established Custodial Environment",
        "chapter": "Chapter 722 - Children",
        "act": "Child Custody Act of 1970 (Act 91)",
        "full_text": "The custodial environment of a child is established if over an appreciable time the child naturally looks to the custodian in that environment for guidance, discipline, the necessities of life, and parental comfort. The age of the child, the physical environment, and the inclination of the custodian and the child as to permanency of the relationship shall also be considered. An established custodial environment may exist with both parents simultaneously.",
        "practice_tips": "If an ECE exists, it cannot be changed without CLEAR AND CONVINCING evidence that the change is in the child's best interests. This is a HIGHER standard than preponderance. ECE can exist with BOTH parents (dual ECE).",
        "cross_references": ["MCL 722.27", "MCR 3.210"],
    },

    # =========================================================================
    # MCL CHAPTER 552 — DIVORCE
    # =========================================================================
    {
        "citation": "MCL 552.6",
        "title": "No-Fault Divorce; Breakdown of Marriage",
        "chapter": "Chapter 552 - Divorce",
        "act": "Divorce Act",
        "full_text": "A complaint for divorce may be filed on the grounds that there has been a breakdown of the marriage relationship to the extent that the objects of matrimony have been destroyed and there remains no reasonable likelihood that the marriage can be preserved.",
        "practice_tips": "Michigan is a no-fault divorce state. Only one ground needed: breakdown of the marriage relationship. No need to prove adultery, cruelty, etc.",
        "cross_references": ["MCL 552.1", "MCR 3.206"],
    },
    {
        "citation": "MCL 552.9f",
        "title": "Temporary Orders; Domestic Relations",
        "chapter": "Chapter 552 - Divorce",
        "act": "Divorce Act",
        "full_text": "After commencement of a divorce action, the court may enter temporary orders regarding custody, parenting time, child support, spousal support, possession of property, and payment of debts. These orders remain in effect until superseded by subsequent order or final judgment.",
        "cross_references": ["MCR 3.204", "MCL 722.27"],
    },
    {
        "citation": "MCL 552.101",
        "title": "Friend of the Court; Establishment",
        "chapter": "Chapter 552 - Divorce",
        "act": "Friend of the Court Act",
        "full_text": "(1) Each circuit court that exercises jurisdiction over domestic relations matters shall have a Friend of the Court office. (2) The Friend of the Court shall: (a) investigate and make recommendations regarding custody, parenting time, and support; (b) enforce court orders; (c) collect and disburse support payments; (d) maintain records. (3) The Friend of the Court is an arm of the court, not an advocate for either party.",
        "practice_tips": "The FOC is supposed to be NEUTRAL — an arm of the court. If the FOC shows bias, document it and raise with the judge. FOC in Muskegon County: Pamela Rusco.",
        "cross_references": ["MCR 3.208", "MCL 552.103"],
    },
    {
        "citation": "MCL 552.505",
        "title": "Child Support Formula",
        "chapter": "Chapter 552 - Divorce",
        "act": "Support and Parenting Time Enforcement Act",
        "full_text": "(1) The state Friend of the Court bureau shall establish a child support formula. (2) The formula shall be based on the relative income of the parents and the needs of the child. (3) The court shall apply the child support formula unless the court determines that application would be unjust or inappropriate. (4) If the court deviates from the formula, it must state reasons on the record.",
        "cross_references": ["MCL 552.517", "MCR 3.209"],
    },
    {
        "citation": "MCL 552.602",
        "title": "Support and Parenting Time Enforcement Act; Enforcement",
        "chapter": "Chapter 552 - Divorce",
        "act": "Support and Parenting Time Enforcement Act (SPTEA)",
        "full_text": "(1) The Friend of the Court shall take appropriate action to enforce support orders and parenting time orders. (2) Enforcement actions include: (a) initiating contempt proceedings; (b) income withholding; (c) intercepting tax refunds; (d) suspending licenses (driver's, professional, recreational); (e) reporting to credit agencies. (3) A party may also independently file a motion for contempt for violation of support or parenting time orders.",
        "practice_tips": "SPTEA provides powerful enforcement tools for parenting time violations — not just support. If the other parent is violating parenting time, file a motion for contempt AND complain to the FOC.",
        "cross_references": ["MCL 552.601", "MCR 3.222"],
    },

    # =========================================================================
    # MCL CHAPTER 600 — REVISED JUDICATURE ACT (Key Sections)
    # =========================================================================
    {
        "citation": "MCL 600.1001",
        "title": "Circuit Court Jurisdiction",
        "chapter": "Chapter 600 - Revised Judicature Act",
        "act": "Revised Judicature Act of 1961",
        "full_text": "The circuit court has original jurisdiction in all civil cases and claims, except as otherwise provided by statute. This includes jurisdiction over: (a) all civil claims exceeding $25,000; (b) equity matters; (c) domestic relations; (d) criminal matters.",
        "cross_references": ["MCL 600.8301", "MCR 2.001"],
    },
    {
        "citation": "MCL 600.1200",
        "title": "Contempt of Court; Powers",
        "chapter": "Chapter 600 - Revised Judicature Act",
        "act": "Revised Judicature Act of 1961",
        "full_text": "(1) Courts have inherent power to punish contempt. (2) Contempt may be civil (to coerce compliance) or criminal (to punish). (3) Civil contempt: the contemnor must have the present ability to comply and willfully refuse to do so. The burden is on the moving party to prove by a preponderance of the evidence. (4) Criminal contempt: must be proven beyond a reasonable doubt. (5) Sanctions may include fine, imprisonment, or both.",
        "practice_tips": "For civil contempt (parenting time enforcement), show: (1) clear order exists, (2) respondent knew of order, (3) respondent violated order, (4) respondent had ability to comply. Civil contempt standard = preponderance.",
        "cross_references": ["MCR 3.222", "MCL 552.602"],
    },
    {
        "citation": "MCL 600.1701",
        "title": "Mandamus; When Issued",
        "chapter": "Chapter 600 - Revised Judicature Act",
        "act": "Revised Judicature Act of 1961",
        "full_text": "Mandamus may be issued from any court of record to any inferior court, corporation, or officer, commanding the performance of an act which the law specifically requires to be performed. Mandamus lies when: (1) there is a clear legal duty to perform; (2) the plaintiff has a clear legal right to performance; (3) no other adequate legal remedy exists.",
        "cross_references": ["MCR 2.621", "MCL 600.1901"],
    },
    {
        "citation": "MCL 600.1901",
        "title": "Superintending Control",
        "chapter": "Chapter 600 - Revised Judicature Act",
        "act": "Revised Judicature Act of 1961",
        "full_text": "The circuit court has general superintending control over all inferior courts and tribunals within its jurisdiction. The circuit court may issue writs and orders necessary to carry into effect its jurisdiction.",
        "cross_references": ["MCR 2.621", "MCL 600.1701"],
    },
    {
        "citation": "MCL 600.2591",
        "title": "Frivolous Actions; Costs and Fees",
        "chapter": "Chapter 600 - Revised Judicature Act",
        "act": "Revised Judicature Act of 1961",
        "full_text": "(1) Upon motion, if a court finds that a civil action or defense was frivolous, the court shall award costs and reasonable attorney fees to the prevailing party. (2) 'Frivolous' means: (a) the party's primary purpose was to harass, embarrass, or injure the other party; (b) the party had no reasonable basis to believe the facts were true; (c) the party's legal position was devoid of arguable legal merit.",
        "practice_tips": "This statute can be used defensively (against frivolous claims by opposing party) or as a deterrent. Also applies to frivolous motions, not just entire actions.",
        "cross_references": ["MCR 2.114", "MCR 2.625"],
    },
    {
        "citation": "MCL 600.2950",
        "title": "Personal Protection Orders",
        "chapter": "Chapter 600 - Revised Judicature Act",
        "act": "Revised Judicature Act of 1961",
        "full_text": "(1) By commencing an independent action, an individual may petition the family division of the circuit court for a personal protection order against: (a) a spouse or former spouse; (b) an individual with whom the petitioner has a child in common; (c) an individual with whom the petitioner has had a dating relationship. (2) The court may enter a PPO to: (a) restrain the respondent from assaulting, threatening, or harassing; (b) exclude the respondent from the petitioner's residence; (c) prohibit interference with custody or parenting time; (d) prohibit stalking. (3) No filing fee for domestic PPOs.",
        "cross_references": ["MCR 3.219", "MCL 764.15b"],
    },

    # =========================================================================
    # MCL CHAPTER 750 — MICHIGAN PENAL CODE (Key Sections)
    # =========================================================================
    {
        "citation": "MCL 750.81",
        "title": "Assault and Battery",
        "chapter": "Chapter 750 - Michigan Penal Code",
        "act": "Michigan Penal Code (Act 328 of 1931)",
        "full_text": "(1) A person who assaults or assaults and batters an individual is guilty of a misdemeanor punishable by imprisonment for not more than 93 days or a fine of not more than $500.00, or both.",
        "cross_references": ["MCL 750.81a", "MCL 750.82"],
    },
    {
        "citation": "MCL 750.81a",
        "title": "Aggravated Assault",
        "chapter": "Chapter 750 - Michigan Penal Code",
        "act": "Michigan Penal Code (Act 328 of 1931)",
        "full_text": "A person who assaults an individual without a weapon and inflicts serious or aggravated injury upon that individual without intending to commit murder or to inflict great bodily harm less than murder is guilty of a misdemeanor punishable by imprisonment for not more than 1 year or a fine of not more than $1,000.00, or both.",
        "cross_references": ["MCL 750.81", "MCL 750.84"],
    },
    {
        "citation": "MCL 750.136b",
        "title": "Child Abuse",
        "chapter": "Chapter 750 - Michigan Penal Code",
        "act": "Michigan Penal Code (Act 328 of 1931)",
        "full_text": "(1) A person is guilty of child abuse in the first degree if the person knowingly or intentionally causes serious physical or serious mental harm to a child. First degree child abuse is a felony punishable by imprisonment for life or any term of years. (2) Second degree: knowingly or intentionally commits an act that is cruel to a child regardless of whether harm results — felony, up to 10 years. (3) Third degree: knowingly or intentionally causes physical harm — misdemeanor, up to 2 years. (4) Fourth degree: by omission, places a child at unreasonable risk of harm — misdemeanor, up to 1 year.",
        "cross_references": ["MCL 722.621", "MCL 712A.2"],
    },
    {
        "citation": "MCL 750.411h",
        "title": "Stalking",
        "chapter": "Chapter 750 - Michigan Penal Code",
        "act": "Michigan Penal Code (Act 328 of 1931)",
        "full_text": "(1) 'Stalking' means a willful course of conduct involving repeated or continuing harassment that would cause a reasonable person to feel terrorized, frightened, intimidated, threatened, harassed, or molested. (2) A person who engages in stalking is guilty of a misdemeanor punishable by imprisonment for not more than 1 year or a fine of not more than $1,000.00, or both. (3) 'Course of conduct' means a pattern of conduct composed of a series of 2 or more separate noncontinuous acts evidencing a continuity of purpose.",
        "cross_references": ["MCL 750.411i", "MCL 600.2950a"],
    },

    # =========================================================================
    # MCL CHAPTER 780 — CRIMINAL PROCEDURE (Key Sections)
    # =========================================================================
    {
        "citation": "MCL 780.131",
        "title": "Right to Speedy Trial",
        "chapter": "Chapter 780 - Criminal Procedure",
        "act": "Speedy Trial Act",
        "full_text": "(1) A criminal defendant has the right to a speedy trial. (2) The defendant must be brought to trial within 180 days after the date of the arrest. (3) The 180-day period may be tolled for: (a) delay caused by the defendant; (b) reasonable continuances granted by the court; (c) delay caused by complexity of the case.",
        "practice_tips": "180-day speedy trial clock. For Andrew's criminal case — track the arrest date and count 180 days. Delays caused by the defense don't count.",
        "cross_references": ["US Const Amend VI", "Mich Const art 1 §20"],
    },
    {
        "citation": "MCL 780.811",
        "title": "Crime Victim's Rights",
        "chapter": "Chapter 780 - Criminal Procedure",
        "act": "Crime Victim's Rights Act (Act 87 of 1985)",
        "full_text": "(1) As used in this article, 'victim' means an individual who suffers direct or threatened physical, financial, or emotional harm as a result of the commission of a crime. (2) A victim has the right to: (a) be treated with fairness, dignity, and respect; (b) be informed of the progress of the case; (c) be present at all court proceedings; (d) be heard at sentencing; (e) restitution from the defendant; (f) a speedy trial or disposition; (g) protection from intimidation.",
        "cross_references": ["MCL 780.766", "Mich Const art 1 §24"],
    },

    # =========================================================================
    # MCL CHAPTER 15 — FOIA (Freedom of Information Act)
    # =========================================================================
    {
        "citation": "MCL 15.231",
        "title": "Freedom of Information Act; Short Title",
        "chapter": "Chapter 15 - FOIA",
        "act": "Freedom of Information Act (Act 442 of 1976)",
        "full_text": "This act shall be known and may be cited as the 'freedom of information act'.",
        "cross_references": ["MCL 15.232"],
    },
    {
        "citation": "MCL 15.232",
        "title": "FOIA Definitions",
        "chapter": "Chapter 15 - FOIA",
        "act": "Freedom of Information Act (Act 442 of 1976)",
        "full_text": "As used in this act: (a) 'Public body' means a state officer, employee, agency, department, division, bureau, board, commission, council, authority, or other body in the executive branch; a county, city, township, village, intercounty, intercity, or regional governing body; a school district; or any other body which is created by state or local authority or funded primarily by public funds. (b) 'Public record' means a writing prepared, owned, used, in the possession of, or retained by a public body in the performance of an official function, from the time it is created.",
        "cross_references": ["MCL 15.233", "MCL 15.234"],
    },
    {
        "citation": "MCL 15.233",
        "title": "FOIA; Right to Inspect, Copy, or Receive Public Records",
        "chapter": "Chapter 15 - FOIA",
        "act": "Freedom of Information Act (Act 442 of 1976)",
        "full_text": "(1) Every person has the right to inspect, copy, or receive copies of public records, except as otherwise provided. (2) A person who desires to inspect or receive a copy of a public record shall make a written request to the public body. (3) The request must describe the record sufficiently to enable the public body to identify it. (4) The public body must respond within 5 business days. (5) The public body may charge reasonable fees for copies (not for inspection). (6) If the request is denied, the denial must cite the specific exemption and provide notice of the right to appeal.",
        "practice_tips": "CRITICAL for Andrew's body cam FOIA. Written request, 5-business-day response deadline. If denied, can appeal to circuit court. Keep copies of all FOIA requests as evidence of government compliance/non-compliance.",
        "cross_references": ["MCL 15.234", "MCL 15.240"],
    },
    {
        "citation": "MCL 15.240",
        "title": "FOIA; Right to Appeal Denial",
        "chapter": "Chapter 15 - FOIA",
        "act": "Freedom of Information Act (Act 442 of 1976)",
        "full_text": "(1) If a public body denies a FOIA request in whole or in part, the requesting person may: (a) file a written appeal to the head of the public body within 180 days; (b) commence an action in circuit court within 180 days. (2) In court proceedings, the public body has the burden of proof to justify any denial. (3) If the court determines the denial was improper, the court may award reasonable attorney fees, costs, and disbursements. (4) If the court determines the public body willfully and intentionally failed to comply, it may award punitive damages of $1,000.",
        "practice_tips": "File appeal within 180 days of denial. In court, the PUBLIC BODY bears the burden — not you. Attorney fees and punitive damages available for willful non-compliance.",
        "cross_references": ["MCL 15.233", "MCL 15.241"],
    },

    # =========================================================================
    # MCL CHAPTER 691 — GOVERNMENT TORT LIABILITY
    # =========================================================================
    {
        "citation": "MCL 691.1407",
        "title": "Governmental Immunity; Exceptions",
        "chapter": "Chapter 691 - Government Tort Liability",
        "act": "Government Tort Liability Act",
        "full_text": "(1) A governmental agency is immune from tort liability if it is engaged in the exercise or discharge of a governmental function. (2) Exceptions: (a) highway exception — defective condition of a public highway; (b) motor vehicle exception — negligent operation of a motor vehicle; (c) public building exception — dangerous or defective condition of a public building; (d) proprietary function exception — government acting in a proprietary capacity. (3) Individual government employees are immune from tort liability when acting within the scope of their authority, unless their conduct amounts to gross negligence.",
        "practice_tips": "Government immunity does NOT protect against constitutional violations under 42 USC 1983. Immunity is a state tort concept; §1983 is federal. Also does not protect against intentional misconduct or gross negligence.",
        "cross_references": ["42 USC 1983", "MCL 691.1401"],
    },
]
