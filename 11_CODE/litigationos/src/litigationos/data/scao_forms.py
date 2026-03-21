"""SCAO Court Forms Catalog — Complete Michigan State Court Administrative Office forms.

All SCAO forms needed for family, civil, criminal, and appellate proceedings.
Sources: courts.michigan.gov/SCAO-forms/ — March 2026.
"""

from __future__ import annotations

SCAO_FORMS: list[dict] = [
    # =========================================================================
    # GENERAL / ADMINISTRATIVE FORMS
    # =========================================================================
    {"form_number": "MC 01", "title": "Case Inventory Addendum", "category": "General",
     "description": "Additional case information sheet for filings with multiple counts or claims.",
     "url": "https://courts.michigan.gov/SCAO-forms/", "filing_use": []},
    {"form_number": "MC 20", "title": "Fee Waiver Request", "category": "General",
     "description": "Request to waive court filing fees based on inability to pay. Must demonstrate income below 125% of federal poverty guidelines or receipt of public assistance.",
     "url": "https://courts.michigan.gov/SCAO-forms/", "filing_use": ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10"],
     "practice_tips": "File with EVERY new action. Attach proof of income/benefits. Approved = all fees waived including service costs."},
    {"form_number": "MC 97", "title": "Request and Order for Adjournment", "category": "General",
     "description": "Request to postpone a scheduled hearing or trial date. Must show good cause.",
     "url": "https://courts.michigan.gov/SCAO-forms/", "filing_use": []},

    # =========================================================================
    # FAMILY DIVISION (DC/FC) — CUSTODY, PARENTING TIME, SUPPORT
    # =========================================================================
    {"form_number": "FOC 10", "title": "Uniform Child Support Order", "category": "Family",
     "description": "Standard child support order form. Includes base support, health insurance, child care, and arrearage provisions.",
     "url": "https://courts.michigan.gov/SCAO-forms/", "filing_use": ["F1"],
     "practice_tips": "Verify support calculations against Michigan Child Support Formula (MCSF). Challenge imputed income if based on assumptions rather than actual earnings."},
    {"form_number": "FOC 29", "title": "Advice of Rights Regarding Friend of the Court", "category": "Family",
     "description": "Notice of rights regarding FOC procedures, including right to object to FOC recommendations and request de novo hearing.",
     "url": "https://courts.michigan.gov/SCAO-forms/", "filing_use": ["F1"]},
    {"form_number": "FOC 39", "title": "Uniform Spousal Support Order", "category": "Family",
     "description": "Standard alimony/spousal support order form.",
     "url": "https://courts.michigan.gov/SCAO-forms/", "filing_use": []},
    {"form_number": "FOC 40", "title": "Objection to Friend of the Court Recommendation", "category": "Family",
     "description": "Filed within 21 days of service of FOC recommendation. Requests de novo hearing before the judge.",
     "url": "https://courts.michigan.gov/SCAO-forms/", "filing_use": ["F1", "F2"],
     "practice_tips": "CRITICAL: File within 21 days or FOC recommendation becomes a court order. Always object to unfavorable recommendations."},
    {"form_number": "FOC 65", "title": "Motion Regarding Support", "category": "Family",
     "description": "Motion to modify, enforce, or terminate child support.",
     "url": "https://courts.michigan.gov/SCAO-forms/", "filing_use": ["F1"]},
    {"form_number": "FOC 67", "title": "Motion Regarding Custody", "category": "Family",
     "description": "Motion to modify, enforce, or establish custody. Must show proper cause or change of circumstances (Vodvarka standard).",
     "url": "https://courts.michigan.gov/SCAO-forms/", "filing_use": ["F1", "F2"],
     "practice_tips": "Must meet threshold: proper cause (relevant legal event) or change of circumstances (affecting child, not just parent). Vodvarka v Grasmeyer, 259 Mich App 499."},
    {"form_number": "FOC 68", "title": "Motion Regarding Parenting Time", "category": "Family",
     "description": "Motion to modify, enforce, or establish parenting time schedule.",
     "url": "https://courts.michigan.gov/SCAO-forms/", "filing_use": ["F1", "F2"]},
    {"form_number": "FOC 89", "title": "Verified Statement of Parenting Time Violations", "category": "Family",
     "description": "Sworn statement documenting specific instances of parenting time interference. Must include dates, times, and nature of each violation.",
     "url": "https://courts.michigan.gov/SCAO-forms/", "filing_use": ["F1", "F2"],
     "practice_tips": "Document EVERY denied visit with date, time, what was supposed to happen, what actually happened. Attach evidence (texts, screenshots). Used for contempt proceedings."},
    {"form_number": "FOC 100", "title": "Friend of the Court Recommendation", "category": "Family",
     "description": "FOC's written recommendation to the court regarding custody, parenting time, or support. Advisory only — parties may object.",
     "url": "https://courts.michigan.gov/SCAO-forms/", "filing_use": []},
    {"form_number": "FOC 101", "title": "Response to Motion", "category": "Family",
     "description": "Response form for opposing party to respond to any family division motion.",
     "url": "https://courts.michigan.gov/SCAO-forms/", "filing_use": ["F1", "F2"]},
    {"form_number": "FOC 115", "title": "Motion and Order for Show Cause (Contempt)", "category": "Family",
     "description": "Motion requesting the court to issue an order directing the other party to appear and show cause why they should not be held in contempt for violating a court order.",
     "url": "https://courts.michigan.gov/SCAO-forms/", "filing_use": ["F1", "F2"],
     "practice_tips": "For enforcing parenting time orders. Must show: (1) clear court order; (2) knowledge of order; (3) willful violation. Criminal contempt = up to 93 days jail per violation."},

    # =========================================================================
    # PERSONAL PROTECTION ORDERS (PPO)
    # =========================================================================
    {"form_number": "CC 375", "title": "Petition for Personal Protection Order (Domestic)", "category": "PPO",
     "description": "Petition for PPO against a spouse, former spouse, dating partner, or co-parent. Must allege assault, threat, harassment, or other specified conduct under MCL 600.2950.",
     "url": "https://courts.michigan.gov/SCAO-forms/", "filing_use": ["F5"]},
    {"form_number": "CC 376", "title": "Personal Protection Order (Domestic)", "category": "PPO",
     "description": "The actual PPO order form issued by the court.",
     "url": "https://courts.michigan.gov/SCAO-forms/", "filing_use": ["F5"]},
    {"form_number": "CC 377", "title": "Motion to Terminate/Modify PPO", "category": "PPO",
     "description": "Motion to terminate or modify a personal protection order. Must be filed within 14 days of service.",
     "url": "https://courts.michigan.gov/SCAO-forms/", "filing_use": ["F5"],
     "practice_tips": "14-DAY DEADLINE from service of PPO to request hearing. Missing this deadline does not waive right to file later, but earlier is better."},
    {"form_number": "CC 381", "title": "Petition for PPO (Non-Domestic / Stalking)", "category": "PPO",
     "description": "Petition for PPO based on stalking or harassment by a non-domestic person.",
     "url": "https://courts.michigan.gov/SCAO-forms/", "filing_use": []},

    # =========================================================================
    # CIVIL PROCEEDINGS
    # =========================================================================
    {"form_number": "MC 01a", "title": "Summons and Complaint", "category": "Civil",
     "description": "Initiates a civil action. Complaint must include: jurisdiction, statement of claim, relief demanded.",
     "url": "https://courts.michigan.gov/SCAO-forms/", "filing_use": ["F4"]},
    {"form_number": "MC 11", "title": "Proof of Service", "category": "Civil",
     "description": "Certification that a document was properly served on the opposing party. Must include: method of service, date, person served.",
     "url": "https://courts.michigan.gov/SCAO-forms/", "filing_use": ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10"],
     "practice_tips": "File proof of service for EVERY document served. Without it, the court cannot verify service. Personal service, mail, or e-service (if consented)."},
    {"form_number": "MC 14", "title": "Affidavit of Service (Process Server)", "category": "Civil",
     "description": "Affidavit from a process server certifying personal service of the summons and complaint.",
     "url": "https://courts.michigan.gov/SCAO-forms/", "filing_use": ["F3", "F4"]},

    # =========================================================================
    # APPELLATE FORMS (COA / MSC)
    # =========================================================================
    {"form_number": "COA Claim of Appeal", "title": "Claim of Appeal", "category": "Appellate",
     "description": "Initiates appeal of right to the Michigan Court of Appeals. Must be filed within 21 days of entry of final order (MCR 7.204).",
     "url": "https://courts.michigan.gov/SCAO-forms/", "filing_use": ["F9"],
     "practice_tips": "21-DAY DEADLINE from entry of final order. File in COA with $375 filing fee (or fee waiver MC 20). Must include: order appealed, statement of jurisdiction, questions presented."},
    {"form_number": "COA Application for Leave", "title": "Application for Leave to Appeal", "category": "Appellate",
     "description": "Requests discretionary review by the COA for interlocutory orders. Filed within 21 days of order (MCR 7.205).",
     "url": "https://courts.michigan.gov/SCAO-forms/", "filing_use": ["F9"],
     "practice_tips": "For non-final orders (interlocutory appeals). COA has discretion to accept or deny. Must show: significant question of law, substantial public interest, or clear error."},
    {"form_number": "COA Docket Statement", "title": "Docket Statement", "category": "Appellate",
     "description": "Required within 28 days of filing claim of appeal. Identifies: parties, attorneys, lower court, issues on appeal, proposed length of brief.",
     "url": "https://courts.michigan.gov/SCAO-forms/", "filing_use": ["F9"]},
    {"form_number": "MSC Application", "title": "Application for Leave to Appeal to MSC", "category": "Appellate",
     "description": "Requests Michigan Supreme Court review of COA decision. Filed within 42 days of COA order (MCR 7.305). $375 filing fee.",
     "url": "https://courts.michigan.gov/SCAO-forms/", "filing_use": ["F10"],
     "practice_tips": "42-day deadline from COA decision. MSC is highly discretionary — takes ~5% of applications. Must present significant constitutional question or conflict with prior decisions."},

    # =========================================================================
    # CRIMINAL / DISTRICT COURT FORMS
    # =========================================================================
    {"form_number": "MC 225", "title": "Bond / Recognizance Form", "category": "Criminal",
     "description": "Bond conditions and recognizance form set at arraignment.",
     "url": "https://courts.michigan.gov/SCAO-forms/", "filing_use": []},
    {"form_number": "MC 231", "title": "Complaint (Criminal)", "category": "Criminal",
     "description": "Criminal complaint charging document.",
     "url": "https://courts.michigan.gov/SCAO-forms/", "filing_use": []},
    {"form_number": "MC 234", "title": "Felony Information", "category": "Criminal",
     "description": "Formal felony charging document filed after bindover from district court.",
     "url": "https://courts.michigan.gov/SCAO-forms/", "filing_use": []},
    {"form_number": "MC 255", "title": "Judgment of Sentence", "category": "Criminal",
     "description": "Final sentencing form for criminal cases.",
     "url": "https://courts.michigan.gov/SCAO-forms/", "filing_use": []},

    # =========================================================================
    # JUDICIAL TENURE COMMISSION (JTC)
    # =========================================================================
    {"form_number": "JTC Complaint Form", "title": "Judicial Misconduct Complaint", "category": "JTC",
     "description": "Filed with the Judicial Tenure Commission (JTC) to report judicial misconduct, disability, or other conduct violating the Michigan Code of Judicial Conduct. JTC investigates and may recommend discipline to the Supreme Court.",
     "url": "https://jtc.courts.mi.gov/", "filing_use": ["F7"],
     "practice_tips": "JTC: 3034 W Grand Blvd, Suite 8-450, Detroit, MI 48202. Include: judge's name, case number, specific conduct, dates, witnesses, supporting documents. JTC review is confidential until formal proceedings."},
]
