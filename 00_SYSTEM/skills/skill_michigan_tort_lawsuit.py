"""
Michigan Tort Lawsuit Builder Skill v1.0
=========================================
Comprehensive tort cause-of-action builder for Michigan Circuit Courts.

Covers: IIED, NIED, abuse of process, malicious prosecution, civil conspiracy,
tortious interference, fraud, defamation, conversion, custodial interference,
parental alienation torts, loss of parental companionship, invasion of privacy,
and negligence.

All outputs conform to MCR 2.111 pleading requirements, MCR 2.112(B)(1)
particularity requirements, and MCR 2.114 verification standards.

Author: LitigationOS / Andrew Pigors
License: Proprietary — litigation work product
"""

import json
import textwrap
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

# =============================================================================
# MICHIGAN TORT CAUSES OF ACTION
# Each entry: elements, authority, statute_of_limitations, damages, chess_mode
# =============================================================================

MICHIGAN_TORTS: Dict[str, Dict[str, Any]] = {
    "iied": {
        "name": "Intentional Infliction of Emotional Distress",
        "elements": [
            "1. Extreme and outrageous conduct",
            "2. Intent or recklessness — defendant intended to cause distress or acted with reckless disregard of the probability of causing distress",
            "3. Causation — the conduct caused the plaintiff's emotional distress",
            "4. Severe emotional distress — the distress suffered was so severe that no reasonable person could be expected to endure it",
        ],
        "authority": "Roberts v Auto-Owners Ins Co, 422 Mich 594, 602-603 (1985)",
        "standard": (
            "Conduct so outrageous in character, and so extreme in degree, "
            "as to go beyond all possible bounds of decency, and to be regarded "
            "as atrocious and utterly intolerable in a civilized community"
        ),
        "sol": "3 years (MCL 600.5805(2))",
        "sol_years": 3,
        "damages": [
            "compensatory (MCL 600.6301)",
            "emotional distress (non-economic per MCL 600.1483)",
            "punitive / exemplary (if malice shown, MCL 600.6304)",
        ],
        "jury_instruction": "M Civ JI 116.01",
        "chess_defenses": [
            "mere insults insufficient",
            "hypersensitivity defense",
            "protected speech / litigation privilege",
        ],
        "chess_rebuttals": [
            "Pattern of conduct over 329+ days of complete parental deprivation exceeds mere insults — systematic campaign",
            "Reasonable person standard met — any reasonable parent would suffer severe distress from total child separation",
            "Conduct aimed at destroying parent-child bond is not protected speech — it is tortious action",
        ],
    },
    "nied": {
        "name": "Negligent Infliction of Emotional Distress",
        "elements": [
            "1. Defendant owed a duty of care to the plaintiff",
            "2. Defendant breached that duty of care",
            "3. Plaintiff suffered serious, compensable emotional distress",
            "4. The emotional distress was a foreseeable result of defendant's breach",
        ],
        "authority": "Daley v LaCroix, 384 Mich 4, 12-13 (1970)",
        "standard": (
            "Where a definite and objective physical injury is produced as a result "
            "of emotional distress proximately caused by defendant's negligent conduct, "
            "the plaintiff may recover in tort for such emotional distress"
        ),
        "sol": "3 years (MCL 600.5805(2))",
        "sol_years": 3,
        "damages": [
            "compensatory (MCL 600.6301)",
            "emotional distress (non-economic)",
            "consequential damages",
            "medical expenses for treatment of distress",
        ],
        "jury_instruction": "M Civ JI 116.03",
        "chess_defenses": [
            "no physical manifestation of distress",
            "emotional distress not foreseeable",
            "no duty owed",
        ],
        "chess_rebuttals": [
            "Physical manifestations documented: insomnia, weight loss, anxiety, depression — medical records available",
            "Emotional distress from 329+ days parent-child separation is inherently foreseeable",
            "Co-parent owes duty not to negligently destroy other parent's relationship with child",
        ],
    },
    "abuse_of_process": {
        "name": "Abuse of Process",
        "elements": [
            "1. An ulterior purpose — defendant used the legal process for an improper objective",
            "2. An act in the use of process not proper in the regular prosecution of the proceeding — a willful act not authorized by the process or aimed at an objective not legitimate in the use of the process",
        ],
        "authority": "Friedman v Dozorc, 412 Mich 1, 30-31 (1981); Spear v Pendill, 164 Mich 620 (1911)",
        "standard": (
            "The gravamen of the tort is not the wrongful procurement of legal process "
            "or the wrongful initiation of criminal or civil proceedings; it is the misuse "
            "or misapplication of process legitimately issued for any purpose other than that "
            "which it was designed to accomplish"
        ),
        "sol": "3 years (MCL 600.5805(2))",
        "sol_years": 3,
        "damages": [
            "compensatory (MCL 600.6301)",
            "special damages — loss of custody/parenting time",
            "emotional distress",
            "punitive / exemplary (MCL 600.6304)",
            "attorney fees / litigation costs",
        ],
        "jury_instruction": "M Civ JI 117.01",
        "chess_defenses": [
            "legitimate use of legal process",
            "right to petition courts (First Amendment)",
            "probable cause existed",
        ],
        "chess_rebuttals": [
            "PPO used as custody weapon, not for genuine protection — no history of violence, no police reports",
            "Pattern of serial false allegations to FOC and court demonstrates ulterior motive to gain custody advantage",
            "Right to petition does not protect sham or bad-faith use of process — Professional Real Estate Investors v Columbia Pictures, 508 US 49 (1993)",
        ],
    },
    "malicious_prosecution": {
        "name": "Malicious Prosecution",
        "elements": [
            "1. Prior proceedings were terminated in plaintiff's favor",
            "2. Absence of probable cause for the prior proceedings",
            "3. Malice — the primary purpose was something other than bringing the offender to justice",
            "4. Special injury — plaintiff suffered damages beyond the ordinary burden of defending",
        ],
        "authority": "Walsh v Taylor, 263 Mich App 618, 622-623 (2004); Friedman v Dozorc, 412 Mich 1 (1981)",
        "standard": (
            "The plaintiff must show that the defendant initiated or procured the institution "
            "of criminal or civil proceedings against the plaintiff without probable cause and "
            "primarily for a purpose other than that of securing the proper adjudication of the claim"
        ),
        "sol": "3 years (MCL 600.5805(2))",
        "sol_years": 3,
        "damages": [
            "compensatory (MCL 600.6301)",
            "special damages — legal fees defending prior action",
            "emotional distress",
            "reputational harm",
            "punitive / exemplary (MCL 600.6304)",
        ],
        "jury_instruction": "M Civ JI 117.03",
        "chess_defenses": [
            "probable cause existed",
            "proceedings not terminated in plaintiff's favor",
            "no special injury shown",
        ],
        "chess_rebuttals": [
            "No credible evidence supported the allegations — no police reports, no medical evidence, no CPS findings",
            "PPO denied/dismissed = favorable termination; false FOC allegations not substantiated = favorable termination",
            "Special injury: 329+ days lost parenting time, legal costs, emotional devastation, reputational harm in community",
        ],
    },
    "civil_conspiracy": {
        "name": "Civil Conspiracy",
        "elements": [
            "1. A concerted action by two or more persons",
            "2. To accomplish an unlawful purpose or criminal act",
            "3. Or to accomplish a lawful purpose by unlawful means",
            "4. An overt act in furtherance of the conspiracy",
            "5. Resulting damages to the plaintiff",
        ],
        "authority": (
            "Advocacy Org for Patients & Providers v Auto Club Ins Assn, 176 Mich App 142, 158 (1989); "
            "Admiral Ins Co v Columbia Casualty Ins Co, 194 Mich App 300, 311-312 (1992)"
        ),
        "standard": (
            "A civil conspiracy is a combination of two or more persons, by some concerted action, "
            "to accomplish a criminal or unlawful purpose, or to accomplish a lawful purpose by criminal "
            "or unlawful means. Each conspirator is liable for the acts of co-conspirators done in "
            "furtherance of the conspiracy."
        ),
        "sol": "3 years (MCL 600.5805(2))",
        "sol_years": 3,
        "damages": [
            "compensatory (MCL 600.6301)",
            "joint and several liability (MCL 600.2956)",
            "punitive / exemplary (MCL 600.6304)",
        ],
        "jury_instruction": "M Civ JI 120.01",
        "note": "Each conspirator liable for acts of co-conspirators in furtherance of conspiracy — joint and several",
        "chess_defenses": [
            "no agreement existed between defendants",
            "intracorporate conspiracy doctrine",
            "each defendant acted independently",
        ],
        "chess_rebuttals": [
            "Coordinated pattern of conduct among Watson family members (Tiffany, Albert, Lori, Cody) demonstrates concerted action",
            "Intracorporate doctrine does not apply to individual family members — they are separate legal persons",
            "Temporal coordination of false allegations, evidence destruction, and child concealment proves agreement by conduct",
        ],
    },
    "tortious_interference_parental": {
        "name": "Tortious Interference with Parental Relationship",
        "elements": [
            "1. Existence of a parent-child relationship",
            "2. Defendant's intentional and improper interference with that relationship",
            "3. The interference was wrongful — independently tortious or otherwise unlawful",
            "4. Causation — defendant's acts caused the disruption",
            "5. Damages — loss of companionship, society, emotional distress",
        ],
        "authority": (
            "Sears v Ryder Truck Rental, 596 F Supp 1001, 1005 (ED Mich 1984); "
            "Restatement (Second) of Torts § 700; "
            "Berger v Weber, 411 Mich 1 (1981)"
        ),
        "standard": (
            "One who, with knowledge that the parent does not consent, abducts or otherwise "
            "compels or induces a minor child to leave a parent legally entitled to its custody "
            "or not to return to the parent after it has been left him, is subject to liability "
            "to the parent — Restatement (Second) of Torts § 700"
        ),
        "sol": "3 years (MCL 600.5805(2))",
        "sol_years": 3,
        "damages": [
            "loss of companionship and society",
            "emotional distress",
            "consequential damages",
            "punitive / exemplary (MCL 600.6304)",
        ],
        "jury_instruction": "M Civ JI 115.01 (by analogy)",
        "note": "Michigan recognizes this tort; particularly strong where third parties (grandparents, relatives) actively alienate",
        "chess_defenses": [
            "defendant had custodial rights",
            "actions were protective",
            "plaintiff's own conduct caused estrangement",
        ],
        "chess_rebuttals": [
            "Extended family members (Albert, Lori, Cody Watson) have NO custodial rights and no standing to interfere",
            "No court finding, CPS report, or police report ever found father posed a danger — 'protective' claim is pretextual",
            "329+ days of zero contact is manufactured by defendants, not the natural result of plaintiff's conduct",
        ],
    },
    "tortious_interference_custody": {
        "name": "Tortious Interference with Custody / Parenting Time Orders",
        "elements": [
            "1. Existence of a valid court order granting custody or parenting time",
            "2. Defendant's actual or constructive knowledge of the order",
            "3. Defendant's intentional interference with plaintiff's rights under the order",
            "4. The interference was without legal justification or excuse",
            "5. Resulting damages to plaintiff",
        ],
        "authority": (
            "MCL 722.27a(7) (court SHALL enforce parenting time); "
            "MCR 3.208; "
            "Restatement (Second) of Torts § 700"
        ),
        "standard": (
            "A party who deliberately violates or facilitates violation of a court-ordered "
            "parenting time schedule commits an independently tortious act. MCL 722.27a(7) "
            "mandates enforcement and creates the legal duty."
        ),
        "sol": "3 years (MCL 600.5805(2))",
        "sol_years": 3,
        "damages": [
            "compensatory — value of lost parenting time",
            "emotional distress",
            "make-up parenting time (MCL 722.27a(7)(b))",
            "attorney fees (MCL 722.27a(7)(c))",
            "punitive / exemplary (MCL 600.6304)",
        ],
        "jury_instruction": "No specific MI instruction — analogize to M Civ JI 115.01",
        "chess_defenses": [
            "order was ambiguous",
            "child refused visitation",
            "safety concerns justified interference",
        ],
        "chess_rebuttals": [
            "Order is clear and unambiguous — specific dates, times, and conditions stated",
            "Child's refusal engineered by alienating conduct — Factor J, MCL 722.23(j)",
            "No court finding, CPS investigation, or police report supports any safety concern",
        ],
    },
    "fraud": {
        "name": "Fraud / Fraudulent Misrepresentation",
        "elements": [
            "1. Defendant made a material representation",
            "2. The representation was false",
            "3. Defendant knew it was false when made, or made it recklessly without knowledge of its truth (scienter)",
            "4. Defendant made the representation with the intent that plaintiff or the court would act upon it",
            "5. Plaintiff or the court justifiably relied upon the representation",
            "6. Plaintiff suffered damages as a result of the reliance",
        ],
        "authority": "Hi-Way Motor Co v Int'l Harvester Co, 398 Mich 330, 336 (1976)",
        "standard": (
            "Fraud must be pled with particularity per MCR 2.112(B)(1) — "
            "the circumstances constituting fraud must be stated with particularity: "
            "WHO made the statement, WHAT was stated, WHEN, WHERE, and HOW it was false"
        ),
        "sol": "6 years (MCL 600.5813)",
        "sol_years": 6,
        "damages": [
            "compensatory — benefit of the bargain (MCL 600.6301)",
            "consequential damages",
            "punitive / exemplary (MCL 600.6304)",
            "attorney fees in exceptional cases",
        ],
        "jury_instruction": "M Civ JI 128.01",
        "pleading_note": "MCR 2.112(B)(1) requires fraud be pled with particularity — WHO, WHAT, WHEN, WHERE, HOW",
        "chess_defenses": [
            "statements were opinions, not facts",
            "no justifiable reliance",
            "no damages proximately caused",
        ],
        "chess_rebuttals": [
            "False allegations of abuse to FOC and court are representations of fact, not opinion",
            "Courts and FOC justifiably rely on parties' sworn statements — the system depends on truthfulness",
            "Direct causal chain: false statements → adverse custody rulings → 329+ days lost parenting time",
        ],
    },
    "defamation": {
        "name": "Defamation (Slander / Libel)",
        "elements": [
            "1. A false and defamatory statement concerning the plaintiff",
            "2. An unprivileged communication (publication) to a third party",
            "3. Fault amounting to at least negligence on the part of the publisher",
            "4. Either actionability per se or special damages",
        ],
        "authority": (
            "Mitan v Campbell, 474 Mich 21, 24 (2005); "
            "Smith v Anonymous Joint Enterprise, 487 Mich 102 (2010)"
        ),
        "standard": (
            "A communication is defamatory if it tends to lower the plaintiff's reputation "
            "in the community or deters third persons from associating or dealing with the plaintiff"
        ),
        "sol": "1 year (MCL 600.5805(2))",
        "sol_years": 1,
        "per_se_categories": [
            "imputation of a crime — e.g., false allegation of child abuse",
            "imputation of a loathsome disease",
            "imputation injurious to business, trade, or profession",
            "imputation of sexual misconduct — e.g., false allegations of being a danger",
        ],
        "damages": [
            "presumed damages (if per se — no proof of special damages required)",
            "compensatory (MCL 600.6301)",
            "emotional distress",
            "reputational harm",
            "punitive / exemplary (if actual malice shown, MCL 600.6304)",
        ],
        "jury_instruction": "M Civ JI 118.01",
        "note": "False statements to court or FOC about plaintiff being a danger to child = defamation per se (imputation of crime)",
        "chess_defenses": [
            "truth is an absolute defense",
            "litigation privilege — absolute immunity for statements in proceedings",
            "qualified privilege — good faith reporting to authorities",
        ],
        "chess_rebuttals": [
            "Statements were demonstrably false — no CPS findings, no police reports, no evidence of danger",
            "Litigation privilege is narrow — does not cover statements made outside proceedings (to school, family, community)",
            "Qualified privilege defeated by actual malice — statements made with knowledge of falsity or reckless disregard",
        ],
    },
    "custodial_interference": {
        "name": "Custodial Interference / Parental Kidnapping (Civil Action)",
        "elements": [
            "1. A valid custody or parenting time order exists",
            "2. Defendant intentionally concealed, detained, or removed child from plaintiff",
            "3. The concealment/detention/removal was in violation of the court order",
            "4. Defendant acted knowingly and willfully",
            "5. Resulting damages to plaintiff and to the parent-child relationship",
        ],
        "authority": (
            "MCL 750.350a (criminal custodial interference); "
            "MCL 600.2919a (civil remedy for damages from criminal acts)"
        ),
        "standard": (
            "A person shall not take a child under 14 from a parent entitled to custody "
            "or conceal a child from a parent with custody rights. Civil liability attaches "
            "under MCL 600.2919a for damages arising from criminal acts."
        ),
        "sol": "3 years (MCL 600.5805(2))",
        "sol_years": 3,
        "damages": [
            "compensatory (MCL 600.6301)",
            "treble damages (MCL 600.2919a(2) — three times actual damages for criminal acts)",
            "emotional distress",
            "loss of parent-child relationship",
        ],
        "jury_instruction": "M Civ JI 115.01 (by analogy); MCL 600.2919a",
        "note": "Civil action founded on criminal custodial interference statute — treble damages available",
        "chess_defenses": [
            "defendant had lawful custody",
            "child was not 'concealed' — defendant's address was known",
            "defendant acted in good faith belief of danger",
        ],
        "chess_rebuttals": [
            "Lawful custody does not authorize complete denial of court-ordered parenting time",
            "'Concealment' includes functional concealment — child systematically kept from any contact for 329+ days",
            "Good faith requires credible evidence of danger — none exists in record; no CPS, no police, no medical evidence",
        ],
    },
    "loss_of_consortium_parental": {
        "name": "Loss of Parental Companionship and Society",
        "elements": [
            "1. A parent-child relationship exists (biological, adoptive, or legal custodial)",
            "2. Defendant's wrongful or tortious conduct",
            "3. Plaintiff was deprived of the child's companionship, society, comfort, and guidance",
            "4. The deprivation was a proximate result of defendant's conduct",
            "5. Damages quantifiable or presumed",
        ],
        "authority": (
            "Berger v Weber, 411 Mich 1, 9-12 (1981); "
            "MCL 600.2922 (wrongful death context, by analogy)"
        ),
        "standard": (
            "A parent has a cause of action for loss of companionship and society of a child "
            "when such loss is caused by the tortious conduct of another. The loss need not be "
            "through death — the complete deprivation of a parent-child relationship through "
            "tortious interference is analogous."
        ),
        "sol": "3 years (MCL 600.5805(2))",
        "sol_years": 3,
        "damages": [
            "loss of companionship and society",
            "loss of comfort, care, and guidance",
            "emotional distress of parent",
            "emotional and developmental harm to child",
            "compensatory (MCL 600.6301)",
        ],
        "jury_instruction": "M Civ JI 50.01 (loss of consortium, by analogy)",
        "chess_defenses": [
            "tort recognized only in death/serious injury contexts",
            "no physical harm to child",
            "plaintiff caused his own estrangement",
        ],
        "chess_rebuttals": [
            "Berger v Weber extends consortium beyond death — principle applies to total deprivation of relationship",
            "329+ days of parental deprivation IS serious psychological harm to both parent and child — documented in developmental psychology",
            "No credible evidence plaintiff caused estrangement — no court finding, no expert opinion, no factual basis",
        ],
    },
    "conversion": {
        "name": "Conversion",
        "elements": [
            "1. Plaintiff had an ownership or possessory interest in the property",
            "2. Defendant took dominion or control over the property inconsistent with plaintiff's rights",
            "3. Defendant's interference was unauthorized",
            "4. Plaintiff demanded return or defendant's actions made demand futile",
            "5. Damages — value of the property or cost of deprivation",
        ],
        "authority": "Foremost Ins Co v Allstate Ins Co, 439 Mich 378, 390-391 (1992)",
        "standard": (
            "Conversion is any distinct act of domain wrongfully exerted over another's "
            "personal property in denial of or inconsistent with the rights therein"
        ),
        "sol": "3 years (MCL 600.5805(2))",
        "sol_years": 3,
        "damages": [
            "fair market value of property (MCL 600.6301)",
            "consequential damages",
            "emotional distress (if personal items of sentimental value)",
        ],
        "jury_instruction": "M Civ JI 119.01",
        "note": "Applicable if Watson family withheld child's belongings, photographs, records, heirlooms, or personal effects",
        "chess_defenses": [
            "property was jointly owned",
            "property was abandoned",
            "defendant had lawful possession",
        ],
        "chess_rebuttals": [
            "Personal items of child (photos, clothing, mementos) belong to custodial household — withheld from plaintiff",
            "No evidence of abandonment — plaintiff repeatedly demanded return of property",
            "Lawful possession does not authorize permanent deprivation from rightful owner",
        ],
    },
    "invasion_of_privacy": {
        "name": "Invasion of Privacy",
        "elements": [
            "1. Intrusion upon seclusion — intentional intrusion upon plaintiff's solitude or private affairs that would be highly offensive to a reasonable person, OR",
            "2. Public disclosure of private facts — public disclosure of embarrassing private facts not of legitimate public concern, OR",
            "3. False light — publicity placing plaintiff in a false light highly offensive to a reasonable person, OR",
            "4. Appropriation — use of plaintiff's name or likeness for defendant's advantage",
        ],
        "authority": "Tobin v Civil Service Comm, 416 Mich 661, 672-673 (1982); Doe v Mills, 212 Mich App 73 (1995)",
        "standard": (
            "Michigan recognizes four invasion of privacy torts as identified in "
            "Restatement (Second) of Torts §§ 652A-652E"
        ),
        "sol": "3 years (MCL 600.5805(2))",
        "sol_years": 3,
        "damages": [
            "compensatory (MCL 600.6301)",
            "emotional distress",
            "punitive / exemplary (MCL 600.6304)",
        ],
        "jury_instruction": "M Civ JI 118.30 (by analogy)",
        "chess_defenses": [
            "information was already public",
            "plaintiff has no reasonable expectation of privacy",
            "defendant had legitimate purpose",
        ],
        "chess_rebuttals": [
            "Private family matters and false abuse allegations were published to community, school, and extended family",
            "Parent has reasonable expectation of privacy in custody proceedings and family medical/psychological records",
            "No legitimate purpose in spreading false abuse allegations — purpose was alienation and reputational destruction",
        ],
    },
    "negligence": {
        "name": "Negligence",
        "elements": [
            "1. Defendant owed a duty of care to the plaintiff",
            "2. Defendant breached that duty of care",
            "3. The breach was the proximate cause of plaintiff's injury",
            "4. Plaintiff suffered actual damages",
        ],
        "authority": "Moning v Alfono, 400 Mich 425, 437 (1977); Case v Consumers Power Co, 463 Mich 1 (2000)",
        "standard": (
            "Every person who engages in the performance of an activity has a duty to use "
            "ordinary care to avoid injuring others. The duty may arise from statute, "
            "relationship, or the general obligation to exercise reasonable care."
        ),
        "sol": "3 years (MCL 600.5805(2))",
        "sol_years": 3,
        "damages": [
            "compensatory (MCL 600.6301)",
            "economic losses",
            "non-economic damages (MCL 600.1483)",
            "consequential damages",
        ],
        "jury_instruction": "M Civ JI 10.01",
        "chess_defenses": [
            "no duty owed",
            "comparative negligence (MCL 600.2959)",
            "superseding cause",
        ],
        "chess_rebuttals": [
            "Co-parent has affirmative duty to facilitate parent-child relationship — MCL 722.23(j)",
            "Plaintiff bears zero comparative fault — 329+ days of deprivation was entirely defendants' conduct",
            "No superseding cause — defendants' continuous, deliberate conduct was the sole proximate cause",
        ],
    },
}

# =============================================================================
# MCR 2.111 PLEADING REQUIREMENTS
# =============================================================================

MICHIGAN_COMPLAINT_STRUCTURE: Dict[str, str] = {
    "caption": (
        "Full court name (STATE OF MICHIGAN, IN THE CIRCUIT COURT FOR THE COUNTY OF ___), "
        "case number, parties with full names and addresses per MCR 2.111(B)"
    ),
    "jurisdictional_basis": (
        "MCL 600.601 (circuit court jurisdiction over civil claims); "
        "MCL 600.605 (circuit court original jurisdiction of all civil claims over $25,000)"
    ),
    "venue": (
        "MCR 2.221 — venue lies in the county where the cause of action arose "
        "or where the defendant resides or has a principal place of business"
    ),
    "parties": "Full legal names, residential addresses, relationship to action per MCR 2.111(B)(2)",
    "factual_allegations": (
        "Numbered paragraphs, each containing one discrete factual assertion, "
        "clear and concise per MCR 2.111(A)(1)"
    ),
    "counts": "Each tort as a separate count with IRAC structure, incorporating prior paragraphs by reference",
    "prayer_for_relief": (
        "Specific damages sought (compensatory, non-economic, exemplary, treble), "
        "injunctive relief, costs, prejudgment interest (MCL 600.6013)"
    ),
    "verification": "MCR 2.114 — signed under penalties of perjury; attorney/party certification",
    "certificate_of_service": "MCR 2.107 — method, date, recipient, address",
    "summons": "MCR 2.102 — summons issued by court clerk",
}

# =============================================================================
# ADVANCED / HIGH-IQ TECHNIQUES
# =============================================================================

ADVANCED_TECHNIQUES: Dict[str, str] = {
    "particularity_pleading": (
        "Fraud and conspiracy must be pled with specificity per MCR 2.112(B)(1) — "
        "WHO made the misrepresentation, WHAT was stated, WHEN it was stated, "
        "WHERE it was stated, and HOW the statement was false"
    ),
    "res_ipsa_loquitur": (
        "Where applicable, invoke res ipsa for pattern conduct — the pattern of "
        "329+ days of total parental deprivation speaks for itself"
    ),
    "joint_and_several": (
        "MCL 600.2956 — joint tortfeasors each liable for full amount of damages "
        "if acting in concert; conspiracy makes all defendants jointly liable"
    ),
    "discovery_rule_tolling": (
        "SOL tolled until plaintiff discovered or should have discovered the injury — "
        "applicable where alienation was covert or gradual"
    ),
    "continuing_wrong_doctrine": (
        "Each day of parental alienation = fresh tort; SOL runs from last act, "
        "not first act — Trentadue v Buckler Automatic Lawn Sprinkler Co, 479 Mich 378 (2007)"
    ),
    "collateral_estoppel": (
        "Prior court findings (e.g., PPO denial, custody findings) bind parties "
        "in subsequent tort action — prevents re-litigation of established facts"
    ),
    "judicial_notice": (
        "MRE 201 — court may take judicial notice of its own records, prior orders, "
        "and docket entries without formal proof"
    ),
    "prima_facie_tort": (
        "Intentional infliction of harm without justification — catch-all where "
        "no specific tort perfectly fits but conduct was clearly wrongful"
    ),
    "per_se_negligence": (
        "Violation of MCL 750.350a (custodial interference) or MCL 722.27a "
        "(parenting time enforcement) = negligence per se if plaintiff is within "
        "the class the statute was designed to protect"
    ),
    "exemplary_damages": (
        "MCL 600.6304 — exemplary damages for willful, wanton, or malicious conduct; "
        "329+ days of deliberate parental deprivation qualifies"
    ),
    "treble_damages": (
        "MCL 600.2919a(2) — treble damages (three times actual damages) for civil actions "
        "arising from criminal conduct including custodial interference (MCL 750.350a)"
    ),
    "prejudgment_interest": (
        "MCL 600.6013 — prejudgment interest accrues from date complaint is filed; "
        "enhances recovery and incentivizes prompt resolution"
    ),
}

# =============================================================================
# CHESS MODE: Anticipated defenses for family tort claims
# =============================================================================

FAMILY_TORT_CHESS_MODE: Dict[str, Dict[str, str]] = {
    "defense_parental_immunity": {
        "their_argument": (
            "Parental immunity doctrine bars tort claims between family members"
        ),
        "our_counter": (
            "Parental immunity abrogated in Michigan — Plumley v Klein, 388 Mich 1 (1972). "
            "Doctrine does not apply to intentional torts. Third-party family members "
            "(Albert Watson, Lori Watson, Cody Watson) have NO parental immunity as they "
            "are not the child's parents."
        ),
        "authority": "Plumley v Klein, 388 Mich 1 (1972)",
    },
    "defense_litigation_privilege": {
        "their_argument": (
            "Statements made in litigation are absolutely privileged and cannot be basis for tort liability"
        ),
        "our_counter": (
            "Litigation privilege applies ONLY to statements relevant to the proceedings and "
            "made in the course of those proceedings. Fraud on the court is never privileged. "
            "Abuse of process claims survive the privilege entirely. Statements made outside court "
            "(to family, school, community, FOC) are NOT privileged."
        ),
        "authority": "Maiden v Rozwood, 461 Mich 109, 134-135 (1999)",
    },
    "defense_right_to_petition": {
        "their_argument": (
            "First Amendment protects the right to petition courts; tort claims chill access to justice"
        ),
        "our_counter": (
            "Michigan has NO anti-SLAPP statute. The right to petition does not protect bad-faith "
            "or sham litigation. Abuse of process specifically addresses misuse of legal procedures. "
            "The Noerr-Pennington doctrine's sham exception applies — Professional Real Estate "
            "Investors v Columbia Pictures, 508 US 49 (1993)."
        ),
        "authority": "No Michigan anti-SLAPP; Professional Real Estate Investors v Columbia Pictures, 508 US 49 (1993)",
    },
    "defense_discretion": {
        "their_argument": (
            "Custody decisions are within the custodial parent's reasonable discretion"
        ),
        "our_counter": (
            "Parental discretion does NOT extend to: (1) violating court orders; "
            "(2) alienating child from other parent; (3) denying court-ordered parenting time "
            "for 329+ days; (4) making false allegations. MCL 722.27a(7) mandates that courts "
            "SHALL enforce parenting time orders."
        ),
        "authority": "MCL 722.27a(7) — court SHALL enforce parenting time orders",
    },
    "defense_best_interest": {
        "their_argument": (
            "All actions were taken in the best interest of the child"
        ),
        "our_counter": (
            "329+ days of TOTAL parental deprivation is NEVER in a child's best interest. "
            "Violates MCL 722.23(j) — willingness to facilitate parent-child relationship. "
            "No court ever found father posed any danger. Child development research unanimously "
            "holds that severing the parent-child bond causes severe harm."
        ),
        "authority": "MCL 722.23(a)-(l); Vodvarka v Grasher, 259 Mich App 1 (2003)",
    },
    "defense_statute_of_limitations": {
        "their_argument": (
            "One or more claims are time-barred under the applicable statute of limitations"
        ),
        "our_counter": (
            "Continuing wrong doctrine — each day of alienation is a fresh tort, and the SOL "
            "runs from the LAST act, not the first. Discovery rule tolls SOL where harm was covert. "
            "Most recent violations occurred within months. Fraudulent concealment tolls SOL "
            "under MCL 600.5855."
        ),
        "authority": "Trentadue v Buckler Automatic Lawn Sprinkler Co, 479 Mich 378 (2007); MCL 600.5855",
    },
    "defense_failure_to_mitigate": {
        "their_argument": (
            "Plaintiff failed to mitigate damages by not seeking timely court intervention"
        ),
        "our_counter": (
            "Plaintiff did seek court intervention — multiple motions filed, FOC involvement, "
            "contempt proceedings. System failures do not constitute failure to mitigate. "
            "Pro se litigant facing coordinated opposition from multiple adverse parties "
            "cannot be faulted for the pace of judicial proceedings."
        ),
        "authority": "MCR 2.613(A) — duty to mitigate is reasonable, not absolute",
    },
    "defense_unclean_hands": {
        "their_argument": (
            "Plaintiff comes to equity with unclean hands"
        ),
        "our_counter": (
            "Unclean hands is an equitable defense — not applicable to legal tort claims for damages. "
            "Even if applicable, plaintiff's conduct must relate to the SAME transaction — "
            "plaintiff's alleged misconduct is unrelated to defendants' tortious interference "
            "with the parent-child relationship."
        ),
        "authority": "Rose v National Auction Group, 466 Mich 453, 462 (2002)",
    },
}

# =============================================================================
# DAMAGES CATALOG — MCL citations for each damage type
# =============================================================================

DAMAGES_CATALOG: Dict[str, Dict[str, Any]] = {
    "compensatory": {
        "description": "Actual, provable financial losses",
        "authority": "MCL 600.6301",
        "components": [
            "lost wages / income",
            "legal fees incurred defending against false allegations",
            "therapy / counseling costs",
            "relocation costs",
            "travel costs for parenting time attempts",
        ],
    },
    "non_economic": {
        "description": "Pain, suffering, emotional distress, humiliation, loss of enjoyment of life",
        "authority": "MCL 600.1483 (cap does NOT apply to intentional torts)",
        "note": "Non-economic damage cap under tort reform does NOT apply to intentional torts",
    },
    "emotional_distress": {
        "description": "Mental anguish, psychological suffering, anxiety, depression, PTSD symptoms",
        "authority": "Roberts v Auto-Owners Ins Co, 422 Mich 594 (1985)",
        "proof": "Medical records, therapy records, testimony, documented symptoms",
    },
    "loss_of_companionship": {
        "description": "Loss of child's companionship, society, comfort, and guidance",
        "authority": "Berger v Weber, 411 Mich 1 (1981)",
        "calculation": "329+ days × value of daily parent-child interaction",
    },
    "punitive_exemplary": {
        "description": "Exemplary damages to punish willful/wanton/malicious conduct and deter future misconduct",
        "authority": "MCL 600.6304",
        "standard": "Conduct must be willful, wanton, or malicious — 329+ days deliberate deprivation qualifies",
    },
    "treble_damages": {
        "description": "Three times actual damages for civil actions arising from criminal conduct",
        "authority": "MCL 600.2919a(2)",
        "applicability": "Custodial interference (MCL 750.350a) is a criminal act triggering treble damages",
    },
    "prejudgment_interest": {
        "description": "Interest on damages from date complaint filed until judgment",
        "authority": "MCL 600.6013",
        "rate": "Statutory rate per MCL 600.6013(8)",
    },
    "attorney_fees": {
        "description": "Attorney fees and costs of litigation",
        "authority": "MCL 722.27a(7)(c) (parenting time enforcement); MCR 2.625 (costs)",
        "note": "Available in parenting time enforcement; also recoverable in some tort claims",
    },
    "injunctive_relief": {
        "description": "Court order requiring/prohibiting specific conduct",
        "authority": "MCR 3.310 (injunctions)",
        "examples": [
            "Order prohibiting defendants from interfering with parenting time",
            "Order requiring immediate resumption of parenting time schedule",
            "No-contact order between non-party interferers and child during plaintiff's time",
        ],
    },
}


# =============================================================================
# FUNCTIONS
# =============================================================================


def build_complaint(
    plaintiff: Dict[str, str],
    defendants: List[Dict[str, str]],
    torts: List[str],
    facts: List[str],
    court_info: Dict[str, str],
) -> str:
    """
    Generate a complete Michigan tort complaint compliant with MCR 2.111.

    Args:
        plaintiff: {"name": ..., "address": ..., "phone": ..., "email": ...}
        defendants: [{"name": ..., "address": ..., "role": ...}, ...]
        torts: list of tort keys from MICHIGAN_TORTS (e.g., ["iied", "abuse_of_process"])
        facts: list of factual allegations (strings)
        court_info: {"court": ..., "county": ..., "case_number": ...}

    Returns:
        Complete complaint text as a string.
    """
    lines: List[str] = []
    now = datetime.now()

    # ── CAPTION ──
    lines.append("=" * 72)
    lines.append("STATE OF MICHIGAN")
    lines.append(f"IN THE CIRCUIT COURT FOR THE COUNTY OF {court_info.get('county', '___').upper()}")
    lines.append("=" * 72)
    lines.append("")
    lines.append(f"{plaintiff['name'].upper()},")
    lines.append(f"    Plaintiff,")
    lines.append("")
    lines.append(f"    v.                                   Case No. {court_info.get('case_number', '____________')}")
    lines.append("")
    for i, d in enumerate(defendants):
        comma = "," if i < len(defendants) - 1 else "."
        lines.append(f"{d['name'].upper()}{comma}")
    if len(defendants) == 1:
        lines.append(f"    Defendant.")
    else:
        lines.append(f"    Defendants.")
    lines.append("")
    lines.append(f"    Hon. {court_info.get('judge', '________________')}")
    lines.append("=" * 72)
    lines.append("")

    # ── TITLE ──
    lines.append("COMPLAINT FOR DAMAGES")
    lines.append("(Jury Trial Demanded)")
    lines.append("")

    # ── INTRODUCTION ──
    lines.append("    NOW COMES Plaintiff, {}, {} and states as follows:".format(
        plaintiff["name"],
        "appearing pro se," if plaintiff.get("pro_se", True) else "by and through counsel,"
    ))
    lines.append("")

    # ── JURISDICTIONAL STATEMENT ──
    para = 1
    lines.append("I. JURISDICTION AND VENUE")
    lines.append("")
    lines.append(f"    {para}. This Court has subject matter jurisdiction over this action pursuant")
    lines.append(f"to MCL 600.601 and MCL 600.605, as this is a civil action for damages")
    lines.append(f"exceeding $25,000.00.")
    para += 1
    lines.append("")
    lines.append(f"    {para}. Venue is proper in {court_info.get('county', '___')} County pursuant")
    lines.append(f"to MCR 2.221, as the cause of action arose in this county and the")
    lines.append(f"Defendant(s) reside(s) in this county.")
    para += 1
    lines.append("")

    # ── PARTIES ──
    lines.append("II. PARTIES")
    lines.append("")
    lines.append(f"    {para}. Plaintiff {plaintiff['name']} is an adult individual residing at")
    lines.append(f"{plaintiff.get('address', '[ADDRESS]')}, {court_info.get('county', '___')} County, Michigan.")
    para += 1
    lines.append("")
    for d in defendants:
        lines.append(f"    {para}. Defendant {d['name']} is an adult individual residing at")
        lines.append(f"{d.get('address', '[ADDRESS]')}, {court_info.get('county', '___')} County, Michigan.")
        if d.get("role"):
            lines.append(f"Defendant {d['name']} is {d['role']}.")
        para += 1
        lines.append("")

    # ── FACTUAL ALLEGATIONS ──
    lines.append("III. FACTUAL ALLEGATIONS COMMON TO ALL COUNTS")
    lines.append("")
    for fact in facts:
        lines.append(f"    {para}. {fact}")
        para += 1
        lines.append("")

    # ── COUNTS ──
    count_num = 1
    for tort_key in torts:
        if tort_key not in MICHIGAN_TORTS:
            lines.append(f"[ERROR: Unknown tort key '{tort_key}' — skipped]")
            continue
        count_text, para = build_count(tort_key, facts, defendants, para_start=para, count_num=count_num)
        lines.append(count_text)
        lines.append("")
        para = para
        count_num += 1

    # ── PRAYER FOR RELIEF ──
    lines.append(build_prayer_for_relief(torts, list(DAMAGES_CATALOG.keys())))
    lines.append("")

    # ── JURY DEMAND ──
    lines.append("DEMAND FOR JURY TRIAL")
    lines.append("")
    lines.append(f"    Plaintiff demands a trial by jury on all issues so triable pursuant to")
    lines.append(f"MCR 2.508 and Const 1963, art 1, § 14.")
    lines.append("")

    # ── VERIFICATION ──
    lines.append("VERIFICATION UNDER MCR 2.114")
    lines.append("")
    lines.append(f"    I, {plaintiff['name']}, declare under the penalties of perjury that the")
    lines.append(f"facts stated in this Complaint are true to the best of my information,")
    lines.append(f"knowledge, and belief.")
    lines.append("")
    lines.append("    Respectfully submitted,")
    lines.append("")
    lines.append("")
    lines.append(f"    ____________________________________")
    lines.append(f"    {plaintiff['name']}, Plaintiff {'(Pro Se)' if plaintiff.get('pro_se', True) else ''}")
    lines.append(f"    {plaintiff.get('address', '[ADDRESS]')}")
    lines.append(f"    {plaintiff.get('phone', '[PHONE]')}")
    lines.append(f"    {plaintiff.get('email', '[EMAIL]')}")
    lines.append(f"    Date: {now.strftime('%B %d, %Y')}")
    lines.append("")

    # ── CERTIFICATE OF SERVICE ──
    lines.append("CERTIFICATE OF SERVICE")
    lines.append("")
    lines.append(f"    I hereby certify that on {now.strftime('%B %d, %Y')}, I served a true and")
    lines.append(f"correct copy of the foregoing Complaint for Damages on the following")
    lines.append(f"parties by [first class mail / personal service / electronic service]:")
    lines.append("")
    for d in defendants:
        lines.append(f"    {d['name']}")
        lines.append(f"    {d.get('address', '[ADDRESS]')}")
        lines.append("")
    lines.append(f"    ____________________________________")
    lines.append(f"    {plaintiff['name']}")
    lines.append("")

    return "\n".join(lines)


def build_count(
    tort_key: str,
    facts: List[str],
    defendants: List[Dict[str, str]],
    para_start: int = 1,
    count_num: int = 1,
) -> Tuple[str, int]:
    """
    Generate a single IRAC-structured count for a specific tort.

    Returns:
        Tuple of (count_text, next_paragraph_number)
    """
    tort = MICHIGAN_TORTS.get(tort_key)
    if not tort:
        return (f"[ERROR: Unknown tort '{tort_key}']", para_start)

    lines: List[str] = []
    para = para_start
    defendant_names = ", ".join(d["name"] for d in defendants) if defendants else "Defendant(s)"

    lines.append(f"COUNT {_roman(count_num)}: {tort['name'].upper()}")
    lines.append(f"(Against {defendant_names})")
    lines.append("")

    # Incorporate prior paragraphs
    lines.append(f"    {para}. Plaintiff incorporates by reference all preceding paragraphs as")
    lines.append(f"though fully set forth herein.")
    para += 1
    lines.append("")

    # ISSUE
    lines.append(f"    [ISSUE]")
    lines.append(f"    {para}. The legal issue is whether {defendant_names} committed the tort of")
    lines.append(f"{tort['name']} against Plaintiff under Michigan law.")
    para += 1
    lines.append("")

    # RULE
    lines.append(f"    [RULE]")
    lines.append(f"    {para}. Under Michigan law, {tort['name']} requires proof of the following")
    lines.append(f"elements: {tort['authority']}.")
    para += 1
    lines.append("")
    for element in tort["elements"]:
        lines.append(f"    {para}. {element}.")
        para += 1
    lines.append("")

    if tort.get("standard"):
        lines.append(f"    {para}. The applicable standard is: \"{tort['standard']}\"")
        lines.append(f"    {tort['authority']}.")
        para += 1
        lines.append("")

    # APPLICATION
    lines.append(f"    [APPLICATION]")
    lines.append(f"    {para}. Applying the law to the facts of this case, {defendant_names}")
    lines.append(f"committed {tort['name']} in that:")
    para += 1
    lines.append("")

    # Map elements to application paragraphs
    for i, element in enumerate(tort["elements"]):
        elem_text = element.split(". ", 1)[-1] if ". " in element else element
        lines.append(f"    {para}. As to Element {i + 1} ({elem_text}): [SPECIFIC FACTS FROM RECORD")
        lines.append(f"    DEMONSTRATING THIS ELEMENT IS MET — cite exhibits, dates, witnesses].")
        para += 1
        lines.append("")

    # CONCLUSION
    lines.append(f"    [CONCLUSION]")
    lines.append(f"    {para}. Accordingly, Plaintiff has established all elements of {tort['name']}.")
    lines.append(f"Defendant(s) are liable to Plaintiff for compensatory damages, emotional distress")
    lines.append(f"damages, and such other relief as this Court deems just and proper.")
    para += 1
    lines.append("")

    # Damages for this count
    if tort.get("damages"):
        lines.append(f"    {para}. As a direct and proximate result of Defendant(s)' conduct,")
        lines.append(f"Plaintiff has suffered the following damages:")
        para += 1
        for dmg in tort["damages"]:
            lines.append(f"        a. {dmg};")
        lines.append(f"    all in an amount to be determined at trial, but in no event less than")
        lines.append(f"$25,000.00.")
        lines.append("")

    # SOL compliance
    lines.append(f"    {para}. This claim is timely filed within the applicable statute of")
    lines.append(f"limitations ({tort.get('sol', '3 years')}). To the extent any act occurred")
    lines.append(f"outside the limitations period, the continuing wrong doctrine applies —")
    lines.append(f"each day of ongoing tortious conduct constitutes a fresh tort.")
    para += 1
    lines.append("")

    return ("\n".join(lines), para)


def build_prayer_for_relief(
    torts: List[str],
    damages_requested: Optional[List[str]] = None,
) -> str:
    """Generate comprehensive prayer for relief based on selected torts."""
    lines: List[str] = []
    lines.append("PRAYER FOR RELIEF")
    lines.append("")
    lines.append("    WHEREFORE, Plaintiff respectfully requests that this Honorable Court")
    lines.append("enter judgment in Plaintiff's favor and against Defendant(s) as follows:")
    lines.append("")

    item = "A"
    lines.append(f"    {item}. Compensatory damages in an amount to be proven at trial for all")
    lines.append(f"       actual losses suffered, pursuant to MCL 600.6301;")
    item = chr(ord(item) + 1)

    lines.append(f"    {item}. Non-economic damages for pain, suffering, emotional distress,")
    lines.append(f"       humiliation, and loss of enjoyment of life;")
    item = chr(ord(item) + 1)

    lines.append(f"    {item}. Damages for loss of parental companionship and society pursuant")
    lines.append(f"       to Berger v Weber, 411 Mich 1 (1981);")
    item = chr(ord(item) + 1)

    # Punitive if any intentional tort
    intentional_torts = {"iied", "abuse_of_process", "malicious_prosecution",
                         "civil_conspiracy", "tortious_interference_parental",
                         "tortious_interference_custody", "fraud", "custodial_interference"}
    if any(t in intentional_torts for t in torts):
        lines.append(f"    {item}. Exemplary / punitive damages for Defendant(s)' willful, wanton,")
        lines.append(f"       and malicious conduct pursuant to MCL 600.6304;")
        item = chr(ord(item) + 1)

    # Treble if custodial interference
    if "custodial_interference" in torts:
        lines.append(f"    {item}. Treble damages pursuant to MCL 600.2919a(2) for civil action")
        lines.append(f"       arising from criminal custodial interference (MCL 750.350a);")
        item = chr(ord(item) + 1)

    # Prejudgment interest
    lines.append(f"    {item}. Prejudgment interest from the date of filing pursuant to")
    lines.append(f"       MCL 600.6013;")
    item = chr(ord(item) + 1)

    # Costs
    lines.append(f"    {item}. Taxable costs and attorney fees as allowed by law pursuant to")
    lines.append(f"       MCR 2.625 and MCL 722.27a(7)(c);")
    item = chr(ord(item) + 1)

    # Injunctive
    lines.append(f"    {item}. Injunctive relief prohibiting Defendant(s) from further interference")
    lines.append(f"       with Plaintiff's parental relationship pursuant to MCR 3.310;")
    item = chr(ord(item) + 1)

    # Joint and several
    if "civil_conspiracy" in torts or len(torts) > 1:
        lines.append(f"    {item}. Joint and several liability against all Defendants pursuant to")
        lines.append(f"       MCL 600.2956;")
        item = chr(ord(item) + 1)

    lines.append(f"    {item}. Such other and further relief as this Court deems just and")
    lines.append(f"       equitable.")
    lines.append("")

    return "\n".join(lines)


def calculate_damages(
    tort_key: str,
    facts: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Calculate and justify damages for a specific tort with MCL citations.

    Args:
        tort_key: key from MICHIGAN_TORTS
        facts: optional dict with keys like "days_separated", "therapy_costs",
               "lost_wages", "legal_fees", etc.

    Returns:
        Dict with damage categories, authorities, and calculations.
    """
    tort = MICHIGAN_TORTS.get(tort_key)
    if not tort:
        return {"error": f"Unknown tort: {tort_key}"}

    facts = facts or {}
    days_separated = facts.get("days_separated", 329)
    therapy_costs = facts.get("therapy_costs", 0)
    lost_wages = facts.get("lost_wages", 0)
    legal_fees = facts.get("legal_fees", 0)
    travel_costs = facts.get("travel_costs", 0)

    result: Dict[str, Any] = {
        "tort": tort["name"],
        "authority": tort["authority"],
        "damage_categories": {},
    }

    # Economic / compensatory
    economic_total = therapy_costs + lost_wages + legal_fees + travel_costs
    result["damage_categories"]["economic_compensatory"] = {
        "authority": "MCL 600.6301",
        "components": {
            "therapy_counseling": therapy_costs,
            "lost_wages": lost_wages,
            "legal_fees_defending": legal_fees,
            "travel_costs": travel_costs,
        },
        "subtotal": economic_total,
        "note": "Actual, provable out-of-pocket losses",
    }

    # Non-economic
    result["damage_categories"]["non_economic"] = {
        "authority": "MCL 600.1483 — cap does NOT apply to intentional torts",
        "components": {
            "pain_and_suffering": "To be determined at trial",
            "emotional_distress": "To be determined at trial — 329+ days of parental deprivation",
            "humiliation": "To be determined at trial",
            "loss_of_enjoyment_of_life": "To be determined at trial",
        },
        "note": (
            "Non-economic damage cap under Michigan tort reform (MCL 600.1483) "
            "does NOT apply to intentional torts. Jury has full discretion."
        ),
    }

    # Loss of companionship
    result["damage_categories"]["loss_of_companionship"] = {
        "authority": "Berger v Weber, 411 Mich 1 (1981)",
        "days_separated": days_separated,
        "description": (
            f"{days_separated} days of complete parental deprivation. "
            f"Lost: daily interaction, bedtime routines, school events, holidays, "
            f"birthdays, milestones, comfort during illness, guidance and mentoring."
        ),
        "note": "Each day of separation is independently compensable",
    }

    # Punitive / exemplary
    intentional_torts = {"iied", "abuse_of_process", "malicious_prosecution",
                         "civil_conspiracy", "tortious_interference_parental",
                         "tortious_interference_custody", "fraud", "custodial_interference"}
    if tort_key in intentional_torts:
        result["damage_categories"]["punitive_exemplary"] = {
            "authority": "MCL 600.6304",
            "standard": "Willful, wanton, or malicious conduct",
            "justification": (
                f"Defendants' conduct was willful and malicious — deliberate deprivation "
                f"of parental relationship over {days_separated}+ days demonstrates wanton "
                f"disregard for Plaintiff's fundamental rights."
            ),
        }

    # Treble damages (custodial interference)
    if tort_key == "custodial_interference":
        result["damage_categories"]["treble_damages"] = {
            "authority": "MCL 600.2919a(2)",
            "calculation": f"3 × actual damages (${economic_total:,.2f}) = ${economic_total * 3:,.2f}" if economic_total > 0 else "3 × actual damages (to be determined at trial)",
            "basis": "Civil action arising from criminal custodial interference (MCL 750.350a)",
        }

    # Prejudgment interest
    result["damage_categories"]["prejudgment_interest"] = {
        "authority": "MCL 600.6013",
        "accrual": "From date complaint is filed until judgment",
        "rate": "Statutory rate per MCL 600.6013(8)",
    }

    # Attorney fees
    if tort_key in {"tortious_interference_custody", "tortious_interference_parental"}:
        result["damage_categories"]["attorney_fees"] = {
            "authority": "MCL 722.27a(7)(c)",
            "basis": "Parenting time enforcement — reasonable attorney fees and costs",
        }

    result["total_economic"] = economic_total
    result["total_note"] = "Non-economic, punitive, and treble damages to be determined at trial"

    return result


def chess_mode_analysis(
    tort_key: str,
    facts: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Predict defense arguments and pre-build rebuttals for a specific tort.

    Combines the tort-specific chess_defenses/chess_rebuttals with the
    global FAMILY_TORT_CHESS_MODE defenses applicable to all family torts.

    Returns:
        Dict with tort-specific and global defense/rebuttal pairs.
    """
    tort = MICHIGAN_TORTS.get(tort_key)
    if not tort:
        return {"error": f"Unknown tort: {tort_key}"}

    facts = facts or {}
    days_separated = facts.get("days_separated", 329)
    result: Dict[str, Any] = {
        "tort": tort["name"],
        "authority": tort["authority"],
        "tort_specific_chess": [],
        "global_family_chess": [],
        "strategic_notes": [],
    }

    # Tort-specific defenses and rebuttals
    defenses = tort.get("chess_defenses", [])
    rebuttals = tort.get("chess_rebuttals", [])
    for i, defense in enumerate(defenses):
        rebuttal = rebuttals[i] if i < len(rebuttals) else "[Rebuttal to be developed based on record]"
        result["tort_specific_chess"].append({
            "defense_number": i + 1,
            "their_argument": defense,
            "our_rebuttal": rebuttal,
        })

    # Global family tort chess mode
    for key, chess in FAMILY_TORT_CHESS_MODE.items():
        result["global_family_chess"].append({
            "defense_id": key,
            "their_argument": chess["their_argument"],
            "our_counter": chess["our_counter"],
            "authority": chess["authority"],
        })

    # Strategic notes
    result["strategic_notes"] = [
        f"Continuing wrong doctrine: each of {days_separated}+ days is a fresh tort — "
        f"Trentadue v Buckler, 479 Mich 378 (2007)",
        "Plead with particularity for fraud counts — MCR 2.112(B)(1)",
        "Joint and several liability for conspiracy — MCL 600.2956",
        "Preserve all arguments for appeal — MCR 2.517(A)(7)",
        "Consider motion in limine to exclude 'best interest' defense in tort action — "
        "custody factors are for custody proceedings, not tort liability",
        "Request judicial notice of family court docket — MRE 201",
    ]

    return result


def build_timeline_exhibits(
    events: List[Dict[str, str]],
) -> str:
    """
    Build chronological timeline exhibits for complaint.

    Args:
        events: list of {"date": "YYYY-MM-DD", "description": ..., "source": ..., "significance": ...}

    Returns:
        Formatted timeline exhibit text.
    """
    lines: List[str] = []
    lines.append("=" * 72)
    lines.append("EXHIBIT __: CHRONOLOGICAL TIMELINE OF EVENTS")
    lines.append("=" * 72)
    lines.append("")
    lines.append("    The following chronological timeline sets forth the key events")
    lines.append("    relevant to Plaintiff's claims, with source citations for each entry.")
    lines.append("")
    lines.append("-" * 72)
    lines.append(f"{'DATE':<14} {'EVENT':<58}")
    lines.append("-" * 72)

    # Sort by date
    sorted_events = sorted(events, key=lambda e: e.get("date", "9999-99-99"))

    for i, event in enumerate(sorted_events, 1):
        date_str = event.get("date", "[UNKNOWN]")
        desc = event.get("description", "[No description]")
        source = event.get("source", "")
        significance = event.get("significance", "")

        lines.append("")
        lines.append(f"  {i:>3}. [{date_str}]")
        # Wrap description
        wrapped = textwrap.wrap(desc, width=64)
        for line in wrapped:
            lines.append(f"       {line}")
        if source:
            lines.append(f"       Source: {source}")
        if significance:
            lines.append(f"       Significance: {significance}")

    lines.append("")
    lines.append("-" * 72)
    lines.append(f"TOTAL EVENTS: {len(sorted_events)}")

    # Calculate separation days if possible
    dates = []
    for e in sorted_events:
        try:
            dates.append(datetime.strptime(e["date"], "%Y-%m-%d"))
        except (ValueError, KeyError):
            pass
    if len(dates) >= 2:
        span = (dates[-1] - dates[0]).days
        lines.append(f"TIMESPAN: {span} days ({dates[0].strftime('%B %d, %Y')} to {dates[-1].strftime('%B %d, %Y')})")

    lines.append("-" * 72)
    lines.append("")
    lines.append("    I certify that the foregoing timeline is true and accurate to the")
    lines.append("    best of my information, knowledge, and belief.")
    lines.append("")
    lines.append("    ____________________________________")
    lines.append("    [Plaintiff Signature]")
    lines.append(f"    Date: {datetime.now().strftime('%B %d, %Y')}")
    lines.append("")

    return "\n".join(lines)


def get_tort_summary(tort_key: str) -> Optional[Dict[str, Any]]:
    """Return a concise summary of a tort for quick reference."""
    tort = MICHIGAN_TORTS.get(tort_key)
    if not tort:
        return None
    return {
        "name": tort["name"],
        "elements_count": len(tort["elements"]),
        "authority": tort["authority"],
        "sol": tort.get("sol", "Unknown"),
        "damages": tort.get("damages", []),
        "has_chess_mode": bool(tort.get("chess_defenses")),
    }


def list_all_torts() -> List[Dict[str, str]]:
    """Return a list of all available tort types with names and SOLs."""
    return [
        {"key": k, "name": v["name"], "sol": v.get("sol", "Unknown")}
        for k, v in MICHIGAN_TORTS.items()
    ]


def get_applicable_torts(scenario: str) -> List[str]:
    """
    Given a scenario keyword, return applicable tort keys.

    Supported scenarios:
        "parental_alienation", "false_allegations", "custody_interference",
        "property_dispute", "reputation_attack", "all"
    """
    scenarios: Dict[str, List[str]] = {
        "parental_alienation": [
            "iied", "nied", "tortious_interference_parental",
            "tortious_interference_custody", "civil_conspiracy",
            "loss_of_consortium_parental", "custodial_interference",
        ],
        "false_allegations": [
            "iied", "abuse_of_process", "malicious_prosecution",
            "fraud", "defamation", "civil_conspiracy",
        ],
        "custody_interference": [
            "tortious_interference_custody", "tortious_interference_parental",
            "custodial_interference", "loss_of_consortium_parental",
            "iied", "civil_conspiracy",
        ],
        "property_dispute": [
            "conversion",
        ],
        "reputation_attack": [
            "defamation", "invasion_of_privacy", "iied",
        ],
        "all": list(MICHIGAN_TORTS.keys()),
    }
    return scenarios.get(scenario, [])


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def _roman(num: int) -> str:
    """Convert integer to Roman numeral string."""
    vals = [
        (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
        (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
        (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
    ]
    result = ""
    for value, numeral in vals:
        while num >= value:
            result += numeral
            num -= value
    return result


# =============================================================================
# SELF-TEST
# =============================================================================


def self_test() -> bool:
    """Run comprehensive self-test to verify all tort definitions and functions."""
    results: List[str] = []
    errors: List[str] = []

    print("=" * 60)
    print("Michigan Tort Lawsuit Builder — Self-Test v1.0")
    print("=" * 60)
    print()

    # ── Test 1: Validate all tort definitions ──
    print("[1/7] Validating tort definitions...")
    for key, tort in MICHIGAN_TORTS.items():
        try:
            assert "name" in tort, f"Missing 'name'"
            assert "elements" in tort, f"Missing 'elements'"
            assert "authority" in tort, f"Missing 'authority'"
            assert "sol" in tort, f"Missing 'sol'"
            assert len(tort["elements"]) >= 2, f"Too few elements ({len(tort['elements'])})"
            assert isinstance(tort["elements"], list), f"Elements not a list"
            results.append(f"  PASS: {key} — {tort['name']} ({len(tort['elements'])} elements)")
        except AssertionError as e:
            errors.append(f"  FAIL: {key} — {e}")
    print(f"  Torts validated: {len(results)}/{len(MICHIGAN_TORTS)}")
    print()

    # ── Test 2: Validate chess mode coverage ──
    print("[2/7] Validating chess mode coverage...")
    chess_count = 0
    for key, tort in MICHIGAN_TORTS.items():
        if "chess_defenses" in tort and "chess_rebuttals" in tort:
            n_def = len(tort["chess_defenses"])
            n_reb = len(tort["chess_rebuttals"])
            assert n_def == n_reb, f"{key}: defense/rebuttal count mismatch ({n_def} vs {n_reb})"
            chess_count += 1
            results.append(f"  PASS: {key} chess mode — {n_def} defense/rebuttal pairs")
        else:
            results.append(f"  INFO: {key} — no tort-specific chess mode (global still applies)")
    print(f"  Torts with chess mode: {chess_count}/{len(MICHIGAN_TORTS)}")
    print(f"  Global defenses: {len(FAMILY_TORT_CHESS_MODE)}")
    print()

    # ── Test 3: Validate global chess mode ──
    print("[3/7] Validating global family chess mode...")
    for key, chess in FAMILY_TORT_CHESS_MODE.items():
        assert "their_argument" in chess, f"Missing their_argument in {key}"
        assert "our_counter" in chess, f"Missing our_counter in {key}"
        assert "authority" in chess, f"Missing authority in {key}"
        results.append(f"  PASS: {key}")
    print(f"  Global defenses validated: {len(FAMILY_TORT_CHESS_MODE)}")
    print()

    # ── Test 4: Test build_count() ──
    print("[4/7] Testing build_count()...")
    test_defendants = [{"name": "Test Defendant", "address": "123 Test St"}]
    test_facts = ["Fact one.", "Fact two."]
    for key in MICHIGAN_TORTS:
        count_text, next_para = build_count(key, test_facts, test_defendants, para_start=1, count_num=1)
        assert len(count_text) > 100, f"Count too short for {key}"
        assert "COUNT" in count_text, f"Missing COUNT header for {key}"
        assert "[ISSUE]" in count_text, f"Missing ISSUE section for {key}"
        assert "[RULE]" in count_text, f"Missing RULE section for {key}"
        assert "[APPLICATION]" in count_text, f"Missing APPLICATION section for {key}"
        assert "[CONCLUSION]" in count_text, f"Missing CONCLUSION section for {key}"
        results.append(f"  PASS: build_count('{key}') — {len(count_text)} chars, IRAC complete")
    print(f"  Counts generated: {len(MICHIGAN_TORTS)}/{len(MICHIGAN_TORTS)}")
    print()

    # ── Test 5: Test build_complaint() ──
    print("[5/7] Testing build_complaint()...")
    test_plaintiff = {
        "name": "Andrew Pigors",
        "address": "123 Main St, Muskegon, MI 49441",
        "phone": "231-555-0100",
        "email": "test@example.com",
        "pro_se": True,
    }
    test_court = {
        "court": "14th Circuit Court",
        "county": "Muskegon",
        "case_number": "2025-000001-NZ",
        "judge": "Jenny L. McNeill",
    }
    complaint = build_complaint(
        plaintiff=test_plaintiff,
        defendants=test_defendants,
        torts=["iied", "abuse_of_process", "civil_conspiracy"],
        facts=test_facts,
        court_info=test_court,
    )
    assert len(complaint) > 1000, "Complaint too short"
    assert "STATE OF MICHIGAN" in complaint, "Missing state header"
    assert "MUSKEGON" in complaint, "Missing county"
    assert "PRAYER FOR RELIEF" in complaint, "Missing prayer"
    assert "CERTIFICATE OF SERVICE" in complaint, "Missing certificate of service"
    assert "MCR 2.114" in complaint, "Missing verification reference"
    assert "MCL 600.601" in complaint, "Missing jurisdictional basis"
    results.append(f"  PASS: build_complaint() — {len(complaint)} chars, all sections present")
    print(f"  Complaint generated: {len(complaint)} characters")
    print()

    # ── Test 6: Test calculate_damages() ──
    print("[6/7] Testing calculate_damages()...")
    test_facts_dict = {
        "days_separated": 329,
        "therapy_costs": 5000,
        "lost_wages": 15000,
        "legal_fees": 8000,
        "travel_costs": 2000,
    }
    for key in MICHIGAN_TORTS:
        dmg = calculate_damages(key, test_facts_dict)
        assert "error" not in dmg, f"Error calculating damages for {key}: {dmg.get('error')}"
        assert "damage_categories" in dmg, f"Missing damage_categories for {key}"
        assert "economic_compensatory" in dmg["damage_categories"], f"Missing economic for {key}"
        results.append(f"  PASS: calculate_damages('{key}') — {len(dmg['damage_categories'])} categories")
    print(f"  Damage calculations: {len(MICHIGAN_TORTS)}/{len(MICHIGAN_TORTS)}")
    print()

    # ── Test 7: Test chess_mode_analysis() ──
    print("[7/7] Testing chess_mode_analysis()...")
    for key in MICHIGAN_TORTS:
        chess = chess_mode_analysis(key, test_facts_dict)
        assert "error" not in chess, f"Error in chess mode for {key}"
        assert "global_family_chess" in chess, f"Missing global chess for {key}"
        assert len(chess["global_family_chess"]) == len(FAMILY_TORT_CHESS_MODE), (
            f"Incomplete global chess for {key}"
        )
        results.append(f"  PASS: chess_mode_analysis('{key}') — "
                        f"{len(chess['tort_specific_chess'])} specific + "
                        f"{len(chess['global_family_chess'])} global")
    print(f"  Chess analyses: {len(MICHIGAN_TORTS)}/{len(MICHIGAN_TORTS)}")
    print()

    # ── Test build_timeline_exhibits ──
    print("[BONUS] Testing build_timeline_exhibits()...")
    test_events = [
        {"date": "2024-01-15", "description": "Last contact with child", "source": "Text messages", "significance": "Beginning of separation"},
        {"date": "2024-06-01", "description": "Motion to enforce parenting time filed", "source": "Court docket", "significance": "Attempted legal remedy"},
        {"date": "2024-12-10", "description": "329th day of separation", "source": "Calendar", "significance": "Ongoing deprivation"},
    ]
    timeline = build_timeline_exhibits(test_events)
    assert len(timeline) > 200, "Timeline too short"
    assert "CHRONOLOGICAL TIMELINE" in timeline, "Missing timeline header"
    assert "2024-01-15" in timeline, "Missing first date"
    results.append(f"  PASS: build_timeline_exhibits() — {len(timeline)} chars, {len(test_events)} events")
    print(f"  Timeline generated: {len(timeline)} characters")
    print()

    # ── Test utility functions ──
    print("[BONUS] Testing utility functions...")
    assert list_all_torts() and len(list_all_torts()) == len(MICHIGAN_TORTS)
    assert get_tort_summary("iied") is not None
    assert get_tort_summary("nonexistent") is None
    assert len(get_applicable_torts("parental_alienation")) > 0
    assert len(get_applicable_torts("all")) == len(MICHIGAN_TORTS)
    assert _roman(1) == "I" and _roman(4) == "IV" and _roman(14) == "XIV"
    results.append("  PASS: utility functions (list_all_torts, get_tort_summary, get_applicable_torts, _roman)")
    print("  All utility functions passed")
    print()

    # ── Summary ──
    print("=" * 60)
    total_pass = sum(1 for r in results if "PASS" in r)
    total_fail = len(errors)
    print(f"RESULTS: {total_pass} passed, {total_fail} failed")
    print(f"TORTS: {len(MICHIGAN_TORTS)} defined")
    print(f"CHESS DEFENSES: {chess_count} tort-specific + {len(FAMILY_TORT_CHESS_MODE)} global")
    print(f"DAMAGE TYPES: {len(DAMAGES_CATALOG)} categories")
    print(f"ADVANCED TECHNIQUES: {len(ADVANCED_TECHNIQUES)}")
    print(f"COMPLAINT SECTIONS: {len(MICHIGAN_COMPLAINT_STRUCTURE)}")

    if errors:
        print("\nERRORS:")
        for e in errors:
            print(e)
        return False

    print("\n*** ALL TESTS PASSED — SKILL FULLY OPERATIONAL ***")
    print("=" * 60)
    return True


if __name__ == "__main__":
    self_test()
