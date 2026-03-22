"""Michigan Supreme Court Filing Form Library — Complete MSC form registry and rules.

Covers all Michigan Supreme Court filing types under MCR 7.300-series:
applications for leave to appeal, original proceedings, motions, amicus briefs,
and supplemental authority. Includes deadline calculators, formatting requirements,
and strength-assessment criteria.

Case context: Pigors v Watson — potential MSC appeal from COA or original action.
Sources: Michigan Court Rules (MCR 7.300-series), courts.michigan.gov — June 2025.

Local-only module — no network calls, no API dependencies.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

# =============================================================================
# MSC FORM REGISTRY
# =============================================================================

MSC_FORMS: list[dict[str, Any]] = [
    # =========================================================================
    # APPLICATIONS FOR LEAVE TO APPEAL (MCR 7.305)
    # =========================================================================
    {
        "form_id": "MSC-ALA",
        "form_number": "MSC Application for Leave",
        "title": "Application for Leave to Appeal",
        "category": "Application",
        "mcr_rule": "MCR 7.305",
        "description": (
            "Requests Michigan Supreme Court discretionary review of a "
            "Court of Appeals decision. The MSC grants leave only when the "
            "application involves a significant question of law, a conflict "
            "with Supreme Court or COA precedent, or an issue of major public "
            "significance. Filed within 42 days of the COA order."
        ),
        "filing_fee": "$375.00",
        "fee_waiver_form": "MC 20",
        "page_limit": 50,
        "page_limit_rule": "MCR 7.305(A)(1)",
        "deadline_days": 42,
        "deadline_basis": "Date of COA order or denial of rehearing",
        "copies_required": 1,
        "efiling": True,
        "service_required": True,
        "service_parties": "All parties in the COA proceeding",
        "required_contents": [
            "Statement of the basis for jurisdiction",
            "Statement of questions presented for review",
            "Statement of facts material to consideration of the questions presented",
            "Argument in support of the application — why MSC should grant leave",
            "Appendix containing: COA opinion/order, trial court order(s), "
            "relevant portions of the record",
        ],
        "appendix_requirements": [
            "COA opinion or order being appealed",
            "Trial court opinion(s) or order(s)",
            "Relevant pleadings from lower courts",
            "Relevant portions of transcript (if applicable)",
            "Any other documents essential to understanding the questions presented",
        ],
        "formatting": {
            "paper_size": "8.5 x 11 inches",
            "margins": "1 inch on all sides",
            "font": "12-point proportional or 10-point monospaced",
            "line_spacing": "Double-spaced (footnotes may be single-spaced)",
            "page_numbering": "Bottom center",
            "binding": "Bound on the left side or stapled in upper-left corner",
        },
        "practice_tips": (
            "MSC accepts roughly 3-5% of leave applications. Frame issues as "
            "conflicts with existing Supreme Court precedent or questions of "
            "first impression with broad public impact. Avoid re-arguing facts. "
            "Focus on why the legal question MATTERS beyond this case. If COA "
            "issued a published opinion, explain why it was wrongly decided. "
            "If unpublished, explain why the issue still warrants MSC review."
        ),
        "filing_use": ["F10"],
        "url": "https://courts.michigan.gov/courts/supreme-court",
        "pigors_relevance": (
            "Primary vehicle for MSC review if COA denies relief. "
            "42-day deadline is critical — calendar immediately on COA decision."
        ),
    },
    {
        "form_id": "MSC-XALA",
        "form_number": "MSC Cross-Application",
        "title": "Cross-Application for Leave to Appeal",
        "category": "Application",
        "mcr_rule": "MCR 7.305(H)",
        "description": (
            "Filed by an appellee who also seeks MSC review of the COA "
            "decision on different grounds. Must be filed within 21 days "
            "after service of the application for leave to appeal, or within "
            "the 42-day filing period, whichever is later."
        ),
        "filing_fee": "$375.00",
        "fee_waiver_form": "MC 20",
        "page_limit": 50,
        "page_limit_rule": "MCR 7.305(A)(1)",
        "deadline_days_after_service": 21,
        "deadline_basis": (
            "21 days after service of the application for leave, "
            "or within the original 42-day period, whichever is later"
        ),
        "copies_required": 1,
        "efiling": True,
        "service_required": True,
        "required_contents": [
            "Statement of jurisdiction",
            "Statement of questions presented (different from applicant's)",
            "Statement of facts",
            "Argument for granting the cross-application",
            "Appendix (may incorporate applicant's appendix by reference)",
        ],
        "practice_tips": (
            "Filed when both sides are unhappy with the COA result. "
            "If Watson appeals to MSC, Andrew should evaluate whether "
            "a cross-application on different issues is warranted."
        ),
        "filing_use": ["F10"],
        "url": "https://courts.michigan.gov/courts/supreme-court",
    },
    {
        "form_id": "MSC-BYPASS",
        "form_number": "MSC Bypass Application",
        "title": "Application for Leave to Appeal Before COA Decision (Bypass)",
        "category": "Application",
        "mcr_rule": "MCR 7.305(B)(2)",
        "description": (
            "Requests MSC to bypass the Court of Appeals entirely and take "
            "direct review of a trial court decision. Extremely rare — granted "
            "only when the case involves issues of major public significance "
            "that require immediate resolution by the Supreme Court."
        ),
        "filing_fee": "$375.00",
        "fee_waiver_form": "MC 20",
        "page_limit": 50,
        "page_limit_rule": "MCR 7.305(A)(1)",
        "deadline_days": None,
        "deadline_basis": "No fixed deadline — file while COA appeal is pending",
        "copies_required": 1,
        "efiling": True,
        "service_required": True,
        "required_contents": [
            "All requirements for standard application for leave",
            "Explanation of why bypass is warranted",
            "Demonstration that the issue has major public significance",
            "Explanation of why waiting for COA decision would be harmful",
        ],
        "practice_tips": (
            "Almost never granted in family law cases. Consider only if "
            "constitutional due process issues are so severe that delay "
            "through COA would cause irreparable harm to L.D.W."
        ),
        "filing_use": ["F10"],
        "url": "https://courts.michigan.gov/courts/supreme-court",
        "pigors_relevance": (
            "Potential bypass if judicial misconduct or due process violations "
            "are severe enough to warrant immediate MSC intervention."
        ),
    },

    # =========================================================================
    # ORIGINAL PROCEEDINGS (MCR 7.304, 7.306)
    # =========================================================================
    {
        "form_id": "MSC-SC",
        "form_number": "MSC Complaint for Superintending Control",
        "title": "Complaint for Superintending Control",
        "category": "Original Proceeding",
        "mcr_rule": "MCR 7.304",
        "description": (
            "Invokes the MSC's constitutional superintending control over "
            "all state courts (Const 1963, art 6, §4). Used when a lower "
            "court has acted beyond its jurisdiction, failed to perform a "
            "clear legal duty, or committed a clear error that cannot be "
            "adequately remedied by appeal. This is an extraordinary remedy."
        ),
        "filing_fee": "$375.00",
        "fee_waiver_form": "MC 20",
        "page_limit": 50,
        "deadline_days": None,
        "deadline_basis": "No fixed deadline — file when extraordinary circumstances warrant",
        "copies_required": 1,
        "efiling": True,
        "service_required": True,
        "service_parties": "All parties and the lower court judge",
        "required_contents": [
            "Complaint setting forth the facts giving rise to jurisdiction",
            "Statement of the relief sought",
            "Brief in support of the complaint",
            "Appendix with relevant lower court orders and record excerpts",
            "Proof that no adequate legal remedy exists (appeal is inadequate)",
        ],
        "standard_of_review": (
            "Petitioner must demonstrate: (1) the lower court acted beyond "
            "its jurisdiction or failed to perform a clear legal duty; "
            "(2) the petitioner has no adequate legal remedy (i.e., appeal "
            "is insufficient); and (3) the resulting harm is significant."
        ),
        "practice_tips": (
            "Superintending control is a LAST RESORT — MSC will deny if "
            "normal appeal could fix the problem. Best used when a judge "
            "refuses to act on a mandatory duty (e.g., refusing to rule on "
            "a motion, refusing to follow a clear MCR requirement). "
            "Document exhaustion of all other remedies before filing."
        ),
        "filing_use": ["F10"],
        "url": "https://courts.michigan.gov/courts/supreme-court",
        "pigors_relevance": (
            "Potential vehicle for judicial misconduct claims if McNeill "
            "refuses to perform clear legal duties (e.g., hearing motions, "
            "following MCR service requirements)."
        ),
    },
    {
        "form_id": "MSC-MAND",
        "form_number": "MSC Mandamus",
        "title": "Application for Extraordinary Writ — Mandamus",
        "category": "Original Proceeding",
        "mcr_rule": "MCR 7.306",
        "description": (
            "Requests the MSC to issue a writ of mandamus compelling a "
            "lower court or public officer to perform a clear legal duty. "
            "Available only when: (1) there is a clear legal right to the "
            "performance sought; (2) the defendant has a clear legal duty "
            "to perform; (3) the act is ministerial (not discretionary); "
            "and (4) no other adequate legal remedy exists."
        ),
        "filing_fee": "$375.00",
        "fee_waiver_form": "MC 20",
        "page_limit": 50,
        "deadline_days": None,
        "deadline_basis": "No fixed deadline — extraordinary remedy",
        "copies_required": 1,
        "efiling": True,
        "service_required": True,
        "service_parties": "All parties and the respondent (court/officer)",
        "required_contents": [
            "Application describing the clear legal duty owed",
            "Brief in support demonstrating the four mandamus elements",
            "Appendix with relevant orders, statutes, and record excerpts",
            "Proof of demand on the respondent and refusal to act",
            "Proof that no other adequate legal remedy exists",
        ],
        "four_elements": [
            "Clear legal right to the performance sought",
            "Clear legal duty of the respondent to perform",
            "The act requested is ministerial, not discretionary",
            "No other adequate legal remedy exists",
        ],
        "practice_tips": (
            "Mandamus is extremely narrow. The duty must be ministerial "
            "(non-discretionary). If the judge has ANY discretion in the "
            "matter, mandamus will be denied. Best for situations where "
            "a statute or court rule REQUIRES a specific action and the "
            "judge simply refuses."
        ),
        "filing_use": ["F10"],
        "url": "https://courts.michigan.gov/courts/supreme-court",
    },
    {
        "form_id": "MSC-HC",
        "form_number": "MSC Habeas Corpus",
        "title": "Application for Extraordinary Writ — Habeas Corpus",
        "category": "Original Proceeding",
        "mcr_rule": "MCR 7.306",
        "description": (
            "Requests the MSC to issue a writ of habeas corpus challenging "
            "unlawful detention or restraint. In the family law context, "
            "may be relevant if a party is jailed for contempt without "
            "proper procedural safeguards."
        ),
        "filing_fee": "$375.00",
        "fee_waiver_form": "MC 20",
        "page_limit": 50,
        "deadline_days": None,
        "deadline_basis": "No fixed deadline — file while detention is ongoing",
        "copies_required": 1,
        "efiling": True,
        "service_required": True,
        "required_contents": [
            "Petition describing the detention and its unlawful basis",
            "Brief demonstrating that detention violates constitutional rights",
            "Appendix with contempt order, hearing transcripts, and record",
            "Proof that lower court remedies have been exhausted or are futile",
        ],
        "practice_tips": (
            "Habeas is the remedy of last resort for unlawful jailing. "
            "In family contempt cases, the key arguments are: (1) lack of "
            "ability to pay / comply with purge conditions; (2) failure to "
            "appoint counsel for contempt facing jail; (3) procedural due "
            "process violations in the contempt hearing."
        ),
        "filing_use": ["F10"],
        "url": "https://courts.michigan.gov/courts/supreme-court",
        "pigors_relevance": (
            "Relevant if Andrew faces contempt incarceration without proper "
            "due process safeguards — ability-to-comply hearing, right to "
            "counsel, adequate notice."
        ),
    },

    # =========================================================================
    # MOTIONS IN THE MSC (MCR 7.308)
    # =========================================================================
    {
        "form_id": "MSC-MOT-STAY",
        "form_number": "MSC Motion for Stay",
        "title": "Motion for Stay Pending Appeal",
        "category": "Motion",
        "mcr_rule": "MCR 7.308",
        "description": (
            "Requests the MSC to stay enforcement of a lower court order "
            "while the application for leave to appeal is pending. Must "
            "show: (1) likelihood of success on the merits; (2) irreparable "
            "harm without a stay; (3) no substantial harm to other parties; "
            "(4) stay serves the public interest."
        ),
        "filing_fee": "No additional fee if filed with pending application",
        "page_limit": 20,
        "page_limit_rule": "MCR 7.308(A)",
        "deadline_days": None,
        "deadline_basis": "File while application for leave is pending",
        "copies_required": 1,
        "efiling": True,
        "service_required": True,
        "required_contents": [
            "Motion stating the stay factors",
            "Brief in support (max 20 pages)",
            "Appendix with lower court order sought to be stayed",
            "Proof that stay was first sought in lower courts",
            "Proposed order",
        ],
        "stay_factors": [
            "Likelihood of success on the merits",
            "Irreparable harm to movant without a stay",
            "No substantial harm to opposing party if stay granted",
            "Stay serves the public interest",
        ],
        "practice_tips": (
            "Must FIRST seek stay from the trial court and COA before "
            "requesting MSC stay. Document those denials. In custody "
            "context, irreparable harm = ongoing deprivation of parenting "
            "time during pendency of appeal."
        ),
        "filing_use": ["F10"],
        "url": "https://courts.michigan.gov/courts/supreme-court",
        "pigors_relevance": (
            "Critical if parenting time remains suspended during appeal. "
            "Every day without contact is irreparable harm to parent-child "
            "relationship."
        ),
    },
    {
        "form_id": "MSC-MOT-IMM",
        "form_number": "MSC Motion for Immediate Consideration",
        "title": "Motion for Immediate Consideration",
        "category": "Motion",
        "mcr_rule": "MCR 7.308(A)",
        "description": (
            "Requests the MSC to expedite consideration of a pending "
            "application for leave or motion. Must demonstrate that delay "
            "would cause significant, irreversible harm."
        ),
        "filing_fee": "No additional fee",
        "page_limit": 5,
        "deadline_days": None,
        "deadline_basis": "File with or after the underlying application/motion",
        "copies_required": 1,
        "efiling": True,
        "service_required": True,
        "required_contents": [
            "Motion explaining the emergency or urgency",
            "Specific harm that will result from normal processing time",
            "Proposed expedited briefing schedule",
        ],
        "practice_tips": (
            "MSC normally takes 4-6 months to act on leave applications. "
            "Immediate consideration is for genuine emergencies — child "
            "safety, imminent incarceration, or irreversible loss of rights. "
            "File concurrently with the underlying application."
        ),
        "filing_use": ["F10"],
        "url": "https://courts.michigan.gov/courts/supreme-court",
    },
    {
        "form_id": "MSC-MOT-EXT",
        "form_number": "MSC Motion for Extension of Time",
        "title": "Motion for Extension of Time",
        "category": "Motion",
        "mcr_rule": "MCR 7.308(A)",
        "description": (
            "Requests additional time to file an application for leave to "
            "appeal or other MSC filing. Must demonstrate good cause for "
            "the extension."
        ),
        "filing_fee": "No additional fee",
        "page_limit": 5,
        "deadline_days": None,
        "deadline_basis": "File BEFORE the original deadline expires",
        "copies_required": 1,
        "efiling": True,
        "service_required": True,
        "required_contents": [
            "Motion explaining the reason for the extension",
            "Proposed new deadline",
            "Statement of the current deadline and time remaining",
            "Statement of opponent's position (consent or objection)",
        ],
        "practice_tips": (
            "File BEFORE the deadline expires. Extensions of the 42-day "
            "leave application deadline are disfavored but may be granted "
            "for good cause (e.g., voluminous record, newly retained "
            "counsel, medical emergency). Consent of opposing party helps."
        ),
        "filing_use": ["F10"],
        "url": "https://courts.michigan.gov/courts/supreme-court",
    },
    {
        "form_id": "MSC-MOT-GEN",
        "form_number": "MSC General Motion",
        "title": "General Motion",
        "category": "Motion",
        "mcr_rule": "MCR 7.308",
        "description": (
            "General-purpose motion form for any relief not covered by a "
            "specific motion type. Includes motions for reconsideration, "
            "motions to file overlength brief, motions to supplement the "
            "record, and similar procedural requests."
        ),
        "filing_fee": "No additional fee",
        "page_limit": 20,
        "page_limit_rule": "MCR 7.308(A)",
        "deadline_days": None,
        "copies_required": 1,
        "efiling": True,
        "service_required": True,
        "required_contents": [
            "Motion stating the specific relief requested",
            "Brief in support",
            "Proposed order",
        ],
        "practice_tips": (
            "Common motions: to file overlength brief, to supplement "
            "appendix, to consolidate cases, to file late response. "
            "Always include a proposed order."
        ),
        "filing_use": ["F10"],
        "url": "https://courts.michigan.gov/courts/supreme-court",
    },

    # =========================================================================
    # AMICUS CURIAE AND SUPPLEMENTAL AUTHORITY (MCR 7.309)
    # =========================================================================
    {
        "form_id": "MSC-AMICUS",
        "form_number": "MSC Amicus Brief",
        "title": "Amicus Curiae Brief",
        "category": "Amicus",
        "mcr_rule": "MCR 7.309",
        "description": (
            "Brief filed by a non-party (friend of the court) offering "
            "additional perspective on the legal issues. Requires motion "
            "for leave to file amicus brief unless invited by the Court."
        ),
        "filing_fee": "None",
        "page_limit": 25,
        "page_limit_rule": "MCR 7.309",
        "deadline_days": None,
        "deadline_basis": "Per Court order or briefing schedule",
        "copies_required": 1,
        "efiling": True,
        "service_required": True,
        "required_contents": [
            "Motion for leave to file (unless Court-invited)",
            "Statement of interest of the amicus curiae",
            "Statement identifying whether any party's counsel authored "
            "the brief or contributed money to its preparation",
            "Argument limited to issues raised by the parties",
        ],
        "practice_tips": (
            "Amicus briefs from fathers' rights organizations, family law "
            "reform groups, or due process advocates can strengthen Andrew's "
            "position. Contact Michigan Family Law Section or national "
            "organizations well before the deadline."
        ),
        "filing_use": ["F10"],
        "url": "https://courts.michigan.gov/courts/supreme-court",
    },
    {
        "form_id": "MSC-SUPP",
        "form_number": "MSC Supplemental Authority",
        "title": "Supplemental Authority Letter",
        "category": "Supplemental",
        "mcr_rule": "MCR 7.305",
        "description": (
            "Letter to the Court citing newly decided cases or enacted "
            "statutes relevant to a pending matter. Limited to citation "
            "and a brief statement of relevance — no argument permitted."
        ),
        "filing_fee": "None",
        "page_limit": 2,
        "deadline_days": None,
        "deadline_basis": "File promptly when new authority becomes available",
        "copies_required": 1,
        "efiling": True,
        "service_required": True,
        "required_contents": [
            "Citation to the new authority",
            "Brief statement of relevance to the pending case (no argument)",
            "Copy of the cited authority as an attachment",
        ],
        "practice_tips": (
            "Monitor Michigan Lawyers Weekly, SCOTUS decisions, and COA "
            "published opinions for cases touching the same issues. "
            "File promptly — do not wait until a ruling is imminent."
        ),
        "filing_use": ["F10"],
        "url": "https://courts.michigan.gov/courts/supreme-court",
    },

    # =========================================================================
    # CERTIFICATE OF COMPLIANCE
    # =========================================================================
    {
        "form_id": "MSC-CERT",
        "form_number": "MSC Certificate of Compliance",
        "title": "Certificate of Compliance",
        "category": "Certificate",
        "mcr_rule": "MCR 7.305(A)(1)",
        "description": (
            "Certifies that a filing complies with page limits, formatting "
            "requirements, and word-count restrictions imposed by the Court "
            "Rules. Must be included with every substantive filing."
        ),
        "filing_fee": "None",
        "page_limit": 1,
        "deadline_days": None,
        "deadline_basis": "Filed as part of any substantive filing",
        "copies_required": 1,
        "efiling": True,
        "service_required": False,
        "required_contents": [
            "Title of the filing being certified",
            "Statement of page count or word count",
            "Statement of compliance with formatting requirements",
            "Signature of attorney or self-represented litigant",
            "Date",
        ],
        "practice_tips": (
            "Include with EVERY substantive filing. Some practitioners "
            "include both page count and word count for completeness."
        ),
        "filing_use": ["F10"],
        "url": "https://courts.michigan.gov/courts/supreme-court",
    },

    # =========================================================================
    # RESPONSE / ANSWER FILINGS
    # =========================================================================
    {
        "form_id": "MSC-RESP",
        "form_number": "MSC Answer to Application",
        "title": "Answer in Opposition to Application for Leave to Appeal",
        "category": "Response",
        "mcr_rule": "MCR 7.305(H)(1)",
        "description": (
            "Filed by the appellee opposing the application for leave to "
            "appeal. Must be filed within 21 days after service of the "
            "application."
        ),
        "filing_fee": "None",
        "page_limit": 50,
        "page_limit_rule": "MCR 7.305(A)(1)",
        "deadline_days_after_service": 21,
        "deadline_basis": "21 days after service of the application",
        "copies_required": 1,
        "efiling": True,
        "service_required": True,
        "required_contents": [
            "Statement of questions presented (may restate applicant's)",
            "Counter-statement of facts",
            "Argument opposing leave — why MSC should decline review",
            "Appendix (if additional record excerpts are needed)",
        ],
        "practice_tips": (
            "If Watson files for leave, Andrew has 21 days to respond. "
            "Focus on: (1) COA correctly decided; (2) no conflict with "
            "MSC precedent; (3) issue is fact-bound, not a question of "
            "law warranting MSC review."
        ),
        "filing_use": ["F10"],
        "url": "https://courts.michigan.gov/courts/supreme-court",
    },
    {
        "form_id": "MSC-REPLY",
        "form_number": "MSC Reply Brief",
        "title": "Reply Brief in Support of Application for Leave to Appeal",
        "category": "Response",
        "mcr_rule": "MCR 7.305(H)(2)",
        "description": (
            "Optional reply to the answer in opposition. Filed within 14 "
            "days after service of the answer. Should address only new "
            "arguments raised in the answer."
        ),
        "filing_fee": "None",
        "page_limit": 25,
        "deadline_days_after_service": 14,
        "deadline_basis": "14 days after service of the answer",
        "copies_required": 1,
        "efiling": True,
        "service_required": True,
        "required_contents": [
            "Reply limited to issues raised in the answer",
            "No new arguments not raised in the application",
        ],
        "practice_tips": (
            "Keep the reply focused and short. Do not repeat the "
            "application. Address only the strongest points in the answer "
            "and any mischaracterizations of the record."
        ),
        "filing_use": ["F10"],
        "url": "https://courts.michigan.gov/courts/supreme-court",
    },

    # =========================================================================
    # REHEARING (MCR 7.317)
    # =========================================================================
    {
        "form_id": "MSC-REHEAR",
        "form_number": "MSC Motion for Rehearing",
        "title": "Motion for Rehearing",
        "category": "Post-Decision",
        "mcr_rule": "MCR 7.317",
        "description": (
            "Requests the MSC to reconsider its decision. Must be filed "
            "within 21 days after the MSC's order. Rehearing is granted "
            "only if the Court misapprehended the facts or law, or if "
            "there has been a significant change in the law."
        ),
        "filing_fee": "None",
        "page_limit": 20,
        "deadline_days": 21,
        "deadline_basis": "21 days after the MSC order",
        "copies_required": 1,
        "efiling": True,
        "service_required": True,
        "required_contents": [
            "Statement of what the Court misapprehended",
            "Brief argument (no reargument of original points)",
            "Citation to specific factual or legal errors",
        ],
        "practice_tips": (
            "Rehearing is almost never granted. Reserve for genuine "
            "misapprehension of fact or law — not mere disagreement. "
            "The 21-day deadline is jurisdictional."
        ),
        "filing_use": ["F10"],
        "url": "https://courts.michigan.gov/courts/supreme-court",
    },
]


# =============================================================================
# MSC RULES REFERENCE (MCR 7.300-series)
# =============================================================================

MSC_RULES: dict[str, dict[str, Any]] = {
    "MCR 7.301": {
        "title": "Applicability; Definitions",
        "summary": (
            "Defines the scope of the 7.300-series rules and key terms. "
            "These rules govern all proceedings in the Michigan Supreme Court."
        ),
        "key_provisions": [
            "Rules apply to all MSC proceedings",
            "Definitions for 'application,' 'brief,' 'appendix,' etc.",
            "Cross-reference to MCR 7.200-series for COA rules",
        ],
    },
    "MCR 7.303": {
        "title": "Jurisdiction of the Supreme Court — Appeal of Right",
        "summary": (
            "Defines the narrow category of cases where MSC has mandatory "
            "jurisdiction (appeal of right). Primarily cases where the COA "
            "declared a statute unconstitutional."
        ),
        "key_provisions": [
            "Appeal of right when COA declares statute unconstitutional",
            "Appeal of right from certain Election Commission decisions",
            "21-day deadline to file claim of appeal",
            "Most family law cases do NOT qualify for appeal of right",
        ],
        "pigors_relevance": (
            "Unlikely to apply unless COA decision involves a statute "
            "declared unconstitutional. Andrew's path is almost certainly "
            "via MCR 7.305 (leave to appeal)."
        ),
    },
    "MCR 7.304": {
        "title": "Original Proceedings — Superintending Control",
        "summary": (
            "Governs complaints for superintending control — the MSC's "
            "constitutional power to oversee lower courts. Available when "
            "a lower court exceeds its jurisdiction or fails to perform a "
            "clear legal duty, and no adequate appellate remedy exists."
        ),
        "key_provisions": [
            "Const 1963, art 6, §4 — source of superintending control power",
            "Must show no adequate legal remedy (appeal insufficient)",
            "Lower court must have acted beyond jurisdiction or failed clear duty",
            "MSC may issue any order necessary to effectuate superintending control",
            "Filing does NOT automatically stay lower court proceedings",
        ],
        "pigors_relevance": (
            "Potential vehicle for addressing judicial misconduct by McNeill "
            "that cannot be adequately remedied through normal appeal. "
            "Requires exhaustion of other remedies first."
        ),
    },
    "MCR 7.305": {
        "title": "Application for Leave to Appeal",
        "summary": (
            "Primary mechanism for seeking MSC review. The Court has "
            "discretion to grant or deny leave. Applications must be filed "
            "within 42 days of the COA decision."
        ),
        "key_provisions": [
            "42-day filing deadline from COA order",
            "50-page limit for applications",
            "MSC considers: conflict with precedent, significant legal question, "
            "major public significance",
            "Answer due 21 days after service of application",
            "Reply due 14 days after service of answer",
            "Cross-application due 21 days after service of application",
            "Bypass of COA available under MCR 7.305(B)(2)",
        ],
        "leave_criteria": [
            "The case involves a significant question of state or federal law",
            "The COA decision conflicts with MSC or other COA precedent",
            "The issue is one of major public significance",
            "The COA decision is clearly erroneous and will cause material injustice",
        ],
        "pigors_relevance": (
            "PRIMARY filing vehicle for Andrew if COA denies relief. "
            "The 42-day deadline is the most critical timeline item. "
            "Frame issues around due process, parental rights as "
            "fundamental constitutional rights, and conflict with "
            "Troxel v Granville."
        ),
    },
    "MCR 7.306": {
        "title": "Original Actions — Extraordinary Writs",
        "summary": (
            "Governs applications for extraordinary writs: mandamus, "
            "habeas corpus, quo warranto, and other original actions. "
            "These are emergency remedies available only when no other "
            "adequate legal remedy exists."
        ),
        "key_provisions": [
            "Mandamus: compel performance of clear legal duty",
            "Habeas corpus: challenge unlawful detention",
            "Quo warranto: challenge unauthorized exercise of power",
            "Must demonstrate exhaustion of other remedies",
            "Filing does NOT automatically stay lower court proceedings",
        ],
        "pigors_relevance": (
            "Habeas corpus is the emergency remedy if Andrew faces "
            "contempt incarceration without due process. Mandamus if "
            "McNeill refuses to perform a clear legal duty under MCR."
        ),
    },
    "MCR 7.308": {
        "title": "Motions in the Supreme Court",
        "summary": (
            "Governs all motions filed in MSC proceedings. Includes "
            "procedural requirements, page limits, and response deadlines."
        ),
        "key_provisions": [
            "Motions must state grounds with particularity",
            "20-page limit for motion briefs",
            "Response due 14 days after service of motion",
            "Motions for immediate consideration must show genuine emergency",
            "All motions must include proposed order",
            "Oral argument on motions is rare",
        ],
    },
    "MCR 7.309": {
        "title": "Amicus Curiae Briefs",
        "summary": (
            "Governs the filing of friend-of-the-court briefs. Requires "
            "either Court invitation or a motion for leave to file."
        ),
        "key_provisions": [
            "Must file motion for leave unless Court-invited",
            "25-page limit for amicus briefs",
            "Must disclose whether any party's counsel authored the brief",
            "Must disclose any financial contributions to the brief",
            "Argument limited to issues raised by the parties",
        ],
    },
    "MCR 7.312": {
        "title": "Oral Argument",
        "summary": (
            "Governs oral argument before the MSC. Oral argument is not "
            "guaranteed — the Court decides whether to hear argument after "
            "granting leave to appeal."
        ),
        "key_provisions": [
            "Court determines whether oral argument will be heard",
            "Typically 30 minutes per side",
            "Court may modify time limits",
            "Arguments are open to the public",
            "Appellants argue first, then appellees, then rebuttal",
        ],
    },
    "MCR 7.316": {
        "title": "Miscellaneous Relief",
        "summary": (
            "Catch-all provision for relief not covered by other MCR 7.300 "
            "rules. The MSC has broad discretion to fashion appropriate "
            "relief in the interests of justice."
        ),
        "key_provisions": [
            "MSC may issue any order in the interests of justice",
            "Includes power to remand with instructions",
            "May modify or vacate lower court orders",
            "May grant any relief a lower court could have granted",
        ],
    },
    "MCR 7.317": {
        "title": "Rehearings",
        "summary": (
            "Governs motions for rehearing of MSC decisions. Available "
            "only when the Court misapprehended the facts or law."
        ),
        "key_provisions": [
            "21-day deadline from MSC order (jurisdictional)",
            "20-page limit",
            "Must identify specific factual or legal misapprehension",
            "No mere reargument of points already considered",
            "Granted only in exceptional circumstances",
        ],
    },
}


# =============================================================================
# FILING TYPE REGISTRY (maps filing types to requirements)
# =============================================================================

_FILING_TYPES: dict[str, dict[str, Any]] = {
    "application_for_leave": {
        "form_id": "MSC-ALA",
        "display_name": "Application for Leave to Appeal",
        "mcr_rule": "MCR 7.305",
        "filing_fee": "$375.00",
        "page_limit": 50,
        "deadline_days_from_coa": 42,
        "required_documents": [
            "Application for Leave to Appeal (50-page limit)",
            "Record appendix (COA opinion, trial court orders, relevant record)",
            "Certificate of compliance",
            "Proof of service on all parties",
            "Filing fee ($375) or fee waiver (MC 20)",
        ],
        "formatting_requirements": {
            "paper_size": "8.5 x 11 inches",
            "margins": "1 inch on all sides",
            "font": "12-point proportional or 10-point monospaced",
            "line_spacing": "Double-spaced (footnotes single-spaced)",
            "page_numbering": "Bottom center, consecutively numbered",
            "cover_page": "Required — include case caption, title, and author info",
            "table_of_contents": "Required for filings over 10 pages",
            "table_of_authorities": "Required for filings over 10 pages",
        },
        "efiling_details": {
            "system": "Michigan Courts E-Filing System (MiFILE)",
            "format": "PDF",
            "max_file_size": "25 MB per document",
            "naming_convention": "CaseNumber_DocumentType_PartyName",
        },
        "service_requirements": {
            "method": "First-class mail or electronic service (if consented)",
            "parties": "All parties who appeared in the COA proceeding",
            "proof": "Certificate of service filed with the application",
            "timing": "Same day as filing or next business day",
        },
    },
    "cross_application": {
        "form_id": "MSC-XALA",
        "display_name": "Cross-Application for Leave to Appeal",
        "mcr_rule": "MCR 7.305(H)",
        "filing_fee": "$375.00",
        "page_limit": 50,
        "deadline_days_after_service": 21,
        "required_documents": [
            "Cross-Application for Leave to Appeal",
            "Supplemental appendix (if needed beyond applicant's)",
            "Certificate of compliance",
            "Proof of service",
            "Filing fee ($375) or fee waiver (MC 20)",
        ],
    },
    "bypass_application": {
        "form_id": "MSC-BYPASS",
        "display_name": "Bypass Application (Before COA Decision)",
        "mcr_rule": "MCR 7.305(B)(2)",
        "filing_fee": "$375.00",
        "page_limit": 50,
        "deadline_days_from_coa": None,
        "required_documents": [
            "Application for Leave to Appeal (bypass) with justification",
            "Explanation of major public significance",
            "Record appendix (trial court orders and record)",
            "Certificate of compliance",
            "Proof of service",
            "Filing fee ($375) or fee waiver (MC 20)",
        ],
    },
    "superintending_control": {
        "form_id": "MSC-SC",
        "display_name": "Complaint for Superintending Control",
        "mcr_rule": "MCR 7.304",
        "filing_fee": "$375.00",
        "page_limit": 50,
        "deadline_days_from_coa": None,
        "required_documents": [
            "Complaint for Superintending Control",
            "Brief in support",
            "Appendix (lower court orders, relevant record)",
            "Proof of exhaustion of other remedies",
            "Certificate of compliance",
            "Proof of service on ALL parties AND the lower court judge",
            "Filing fee ($375) or fee waiver (MC 20)",
        ],
    },
    "mandamus": {
        "form_id": "MSC-MAND",
        "display_name": "Application for Writ of Mandamus",
        "mcr_rule": "MCR 7.306",
        "filing_fee": "$375.00",
        "page_limit": 50,
        "deadline_days_from_coa": None,
        "required_documents": [
            "Application for Extraordinary Writ (Mandamus)",
            "Brief demonstrating the four mandamus elements",
            "Appendix (orders, statutes, record excerpts)",
            "Proof of demand on respondent and refusal",
            "Proof of exhaustion of other remedies",
            "Certificate of compliance",
            "Proof of service",
            "Filing fee ($375) or fee waiver (MC 20)",
        ],
    },
    "habeas_corpus": {
        "form_id": "MSC-HC",
        "display_name": "Application for Writ of Habeas Corpus",
        "mcr_rule": "MCR 7.306",
        "filing_fee": "$375.00",
        "page_limit": 50,
        "deadline_days_from_coa": None,
        "required_documents": [
            "Petition for Writ of Habeas Corpus",
            "Brief demonstrating unlawful detention",
            "Appendix (contempt order, hearing transcripts, record)",
            "Proof of exhaustion of lower court remedies (or futility)",
            "Certificate of compliance",
            "Proof of service",
            "Filing fee ($375) or fee waiver (MC 20)",
        ],
    },
    "motion_for_stay": {
        "form_id": "MSC-MOT-STAY",
        "display_name": "Motion for Stay Pending Appeal",
        "mcr_rule": "MCR 7.308",
        "filing_fee": "None (filed with pending application)",
        "page_limit": 20,
        "deadline_days_from_coa": None,
        "required_documents": [
            "Motion for Stay Pending Appeal",
            "Brief in support (20-page limit)",
            "Appendix (order sought to be stayed, lower court denials)",
            "Proof that stay was first sought in lower courts",
            "Proposed order",
            "Proof of service",
        ],
    },
    "motion_immediate_consideration": {
        "form_id": "MSC-MOT-IMM",
        "display_name": "Motion for Immediate Consideration",
        "mcr_rule": "MCR 7.308(A)",
        "filing_fee": "None",
        "page_limit": 5,
        "deadline_days_from_coa": None,
        "required_documents": [
            "Motion for Immediate Consideration",
            "Statement of emergency or urgency",
            "Proposed expedited briefing schedule",
            "Proof of service",
        ],
    },
    "motion_extension_of_time": {
        "form_id": "MSC-MOT-EXT",
        "display_name": "Motion for Extension of Time",
        "mcr_rule": "MCR 7.308(A)",
        "filing_fee": "None",
        "page_limit": 5,
        "deadline_days_from_coa": None,
        "required_documents": [
            "Motion for Extension of Time",
            "Statement of good cause",
            "Statement of current deadline",
            "Statement of opposing party's position",
            "Proposed order",
            "Proof of service",
        ],
    },
    "amicus_brief": {
        "form_id": "MSC-AMICUS",
        "display_name": "Amicus Curiae Brief",
        "mcr_rule": "MCR 7.309",
        "filing_fee": "None",
        "page_limit": 25,
        "deadline_days_from_coa": None,
        "required_documents": [
            "Motion for leave to file amicus brief (unless Court-invited)",
            "Amicus brief (25-page limit)",
            "Statement of interest",
            "Authorship and funding disclosure",
            "Proof of service",
        ],
    },
    "supplemental_authority": {
        "form_id": "MSC-SUPP",
        "display_name": "Supplemental Authority Letter",
        "mcr_rule": "MCR 7.305",
        "filing_fee": "None",
        "page_limit": 2,
        "deadline_days_from_coa": None,
        "required_documents": [
            "Letter citing new authority (2-page limit)",
            "Copy of the cited authority attached",
            "Proof of service",
        ],
    },
    "rehearing": {
        "form_id": "MSC-REHEAR",
        "display_name": "Motion for Rehearing",
        "mcr_rule": "MCR 7.317",
        "filing_fee": "None",
        "page_limit": 20,
        "deadline_days_from_msc_order": 21,
        "required_documents": [
            "Motion for Rehearing (20-page limit)",
            "Brief identifying specific misapprehension of fact or law",
            "Certificate of compliance",
            "Proof of service",
        ],
    },
}


# =============================================================================
# LEAVE-TO-APPEAL STRENGTH CRITERIA
# =============================================================================

_LEAVE_CRITERIA: list[dict[str, Any]] = [
    {
        "criterion": "conflict_with_msc_precedent",
        "label": "Conflict with Michigan Supreme Court Precedent",
        "weight": "Very High",
        "description": (
            "The COA decision directly conflicts with a published MSC opinion. "
            "This is the strongest basis for leave — the MSC's primary function "
            "is ensuring uniformity of law across the state."
        ),
        "examples": [
            "COA applied incorrect standard of review after MSC clarified it",
            "COA holding contradicts MSC constitutional interpretation",
            "COA declined to follow binding MSC precedent",
        ],
    },
    {
        "criterion": "conflict_with_coa_precedent",
        "label": "Conflict Between COA Panels",
        "weight": "High",
        "description": (
            "The COA decision conflicts with another published COA opinion, "
            "creating a split of authority. The MSC resolves inter-panel "
            "conflicts to ensure consistent application of law."
        ),
        "examples": [
            "Different COA panels reached opposite conclusions on the same legal issue",
            "COA holding contradicts prior published COA opinion",
        ],
    },
    {
        "criterion": "significant_constitutional_question",
        "label": "Significant Constitutional Question",
        "weight": "Very High",
        "description": (
            "The case raises an unresolved constitutional question of state "
            "or federal law. Due process and fundamental rights issues "
            "(including parental rights) fit this criterion."
        ),
        "examples": [
            "Whether due process requires specific procedures before terminating parenting time",
            "Whether parental rights as fundamental rights under Troxel require strict scrutiny",
            "Whether ex parte proceedings violate constitutional due process",
        ],
        "pigors_relevance": (
            "Andrew's strongest basis — parental rights are fundamental "
            "constitutional rights. If COA ignores Troxel v Granville or "
            "fails to apply strict scrutiny to parenting time suspension, "
            "this is a significant constitutional question."
        ),
    },
    {
        "criterion": "major_public_significance",
        "label": "Issue of Major Public Significance",
        "weight": "High",
        "description": (
            "The legal question affects a broad class of people beyond the "
            "parties. Family law issues affecting parental rights, due process "
            "in domestic proceedings, or judicial accountability can qualify."
        ),
        "examples": [
            "Systemic denial of due process in family courts",
            "Standards for suspending parenting time without evidentiary hearing",
            "Scope of judicial immunity in family court proceedings",
        ],
    },
    {
        "criterion": "clear_legal_error",
        "label": "Clear Legal Error Causing Material Injustice",
        "weight": "Medium",
        "description": (
            "The COA committed a clear, outcome-determinative legal error. "
            "This alone is usually insufficient — the MSC is not an error-"
            "correction court. Must be combined with broader significance."
        ),
        "examples": [
            "COA applied wrong standard of review",
            "COA misinterpreted a statute",
            "COA failed to consider a controlling legal authority",
        ],
    },
    {
        "criterion": "question_of_first_impression",
        "label": "Question of First Impression",
        "weight": "High",
        "description": (
            "The case raises a legal question that has not been addressed "
            "by the MSC before. The MSC is more likely to grant leave when "
            "it can establish new precedent."
        ),
        "examples": [
            "Novel intersection of parental rights and mental health conditions",
            "Scope of a parent's right to due process in ex parte custody modifications",
        ],
    },
    {
        "criterion": "development_of_law",
        "label": "Need for Development or Clarification of the Law",
        "weight": "Medium-High",
        "description": (
            "Existing law is unclear or outdated, and the MSC should provide "
            "guidance. Common when statutes or rules have been interpreted "
            "inconsistently across circuits."
        ),
        "examples": [
            "MCR provisions that are ambiguous as applied to modern circumstances",
            "Standards that vary by circuit and need statewide uniformity",
        ],
    },
]


# =============================================================================
# PUBLIC API FUNCTIONS
# =============================================================================


def get_msc_forms() -> dict[str, Any]:
    """Return all MSC filing forms with full metadata.

    Returns:
        Dictionary with ``forms`` (list of form dicts), ``total_count``,
        and ``categories`` summary.
    """
    categories: dict[str, int] = {}
    for form in MSC_FORMS:
        cat = form.get("category", "Unknown")
        categories[cat] = categories.get(cat, 0) + 1

    return {
        "forms": MSC_FORMS,
        "total_count": len(MSC_FORMS),
        "categories": categories,
        "source": "Michigan Court Rules — MCR 7.300-series",
    }


def get_msc_rules() -> dict[str, dict[str, Any]]:
    """Return MSC rule summaries for the MCR 7.300-series.

    Returns:
        Dictionary keyed by rule number (e.g. ``"MCR 7.305"``), each
        containing ``title``, ``summary``, and ``key_provisions``.
    """
    return MSC_RULES


def get_filing_requirements(filing_type: str) -> dict[str, Any]:
    """Return detailed requirements for a specific MSC filing type.

    Args:
        filing_type: One of the registered filing-type keys, e.g.
            ``"application_for_leave"``, ``"superintending_control"``,
            ``"motion_for_stay"``.  Case-insensitive; spaces and hyphens
            are normalised to underscores.

    Returns:
        Dictionary with all requirements for the filing type, or an
        error dictionary if the type is not found.
    """
    key = filing_type.strip().lower().replace("-", "_").replace(" ", "_")
    if key in _FILING_TYPES:
        return {
            "filing_type": key,
            **_FILING_TYPES[key],
            "status": "found",
        }

    return {
        "filing_type": filing_type,
        "status": "not_found",
        "available_types": sorted(_FILING_TYPES.keys()),
        "error": f"Filing type '{filing_type}' not recognised.",
    }


def check_msc_deadlines(coa_decision_date: str) -> dict[str, Any]:
    """Calculate critical MSC filing deadlines from a COA decision date.

    Args:
        coa_decision_date: Date of the COA order in ``YYYY-MM-DD`` format.

    Returns:
        Dictionary of deadline names to computed dates and day counts,
        plus warnings for imminent or past deadlines.
    """
    try:
        coa_date = datetime.strptime(coa_decision_date, "%Y-%m-%d").date()
    except ValueError:
        return {
            "error": (
                f"Invalid date format: '{coa_decision_date}'. "
                "Use YYYY-MM-DD (e.g. 2025-06-15)."
            ),
        }

    today = datetime.now().date()
    deadlines: dict[str, Any] = {}

    entries: list[tuple[str, int, str]] = [
        (
            "application_for_leave",
            42,
            "Application for Leave to Appeal (MCR 7.305)",
        ),
        (
            "rehearing_of_coa_decision",
            21,
            "Motion for Rehearing in COA (MCR 7.215)",
        ),
    ]

    warnings: list[str] = []

    for key, days, label in entries:
        deadline_date = coa_date + timedelta(days=days)
        days_remaining = (deadline_date - today).days

        status: str
        if days_remaining < 0:
            status = "EXPIRED"
            warnings.append(
                f"⚠ {label} deadline EXPIRED {abs(days_remaining)} day(s) ago."
            )
        elif days_remaining <= 7:
            status = "IMMINENT"
            warnings.append(
                f"🔴 {label} deadline is IMMINENT — {days_remaining} day(s) left."
            )
        elif days_remaining <= 14:
            status = "APPROACHING"
        else:
            status = "OK"

        deadlines[key] = {
            "label": label,
            "deadline_date": deadline_date.isoformat(),
            "days_remaining": days_remaining,
            "status": status,
        }

    # Derived deadlines (response / reply — depend on service, not COA date)
    deadlines["answer_to_application"] = {
        "label": "Answer in Opposition (MCR 7.305(H)(1))",
        "deadline_rule": "21 days after SERVICE of the application",
        "note": "Cannot compute without service date — track manually.",
    }
    deadlines["reply_brief"] = {
        "label": "Reply Brief (MCR 7.305(H)(2))",
        "deadline_rule": "14 days after SERVICE of the answer",
        "note": "Cannot compute without answer-service date — track manually.",
    }
    deadlines["msc_rehearing"] = {
        "label": "Motion for Rehearing of MSC Order (MCR 7.317)",
        "deadline_rule": "21 days after MSC order",
        "note": "Cannot compute until MSC rules — track manually.",
    }

    return {
        "coa_decision_date": coa_decision_date,
        "computed_as_of": today.isoformat(),
        "deadlines": deadlines,
        "warnings": warnings,
    }


def get_original_action_requirements() -> dict[str, Any]:
    """Return consolidated requirements for MSC original proceedings.

    Covers superintending control (MCR 7.304), mandamus, and habeas corpus
    (MCR 7.306).  These are the extraordinary-writ vehicles relevant if
    Andrew needs to bypass the normal appellate path.

    Returns:
        Dictionary with requirements for each original-action type,
        threshold elements, and strategic considerations.
    """
    return {
        "overview": (
            "Original proceedings allow direct MSC intervention without "
            "going through COA. They are extraordinary remedies available "
            "only when no adequate appellate remedy exists."
        ),
        "vehicles": {
            "superintending_control": {
                "rule": "MCR 7.304",
                "constitutional_basis": "Const 1963, art 6, §4",
                "threshold": [
                    "Lower court acted beyond its jurisdiction",
                    "OR lower court failed to perform a clear legal duty",
                    "AND no adequate legal remedy (appeal) exists",
                    "AND the resulting harm is significant",
                ],
                "best_for": (
                    "Judge refuses to act on mandatory duty — refusing to "
                    "rule on motions, refusing to follow MCR service "
                    "requirements, systemic due process violations."
                ),
                "pigors_application": (
                    "If McNeill refuses to follow MCR requirements for "
                    "service, hearing procedures, or other mandatory duties, "
                    "superintending control may compel compliance."
                ),
            },
            "mandamus": {
                "rule": "MCR 7.306",
                "four_elements": [
                    "Clear legal right to the performance sought",
                    "Clear legal duty of the respondent to perform",
                    "The act requested is ministerial (not discretionary)",
                    "No other adequate legal remedy exists",
                ],
                "best_for": (
                    "Compelling a specific, non-discretionary act — e.g., "
                    "entering an order required by statute or court rule."
                ),
            },
            "habeas_corpus": {
                "rule": "MCR 7.306",
                "threshold": [
                    "Petitioner is in custody or subject to restraint",
                    "Custody or restraint is unlawful",
                    "Lower court remedies exhausted or futile",
                ],
                "best_for": (
                    "Challenging unlawful incarceration from civil contempt "
                    "without proper procedural safeguards."
                ),
                "pigors_application": (
                    "If Andrew faces contempt jailing without ability-to-"
                    "comply determination, right to counsel, or adequate "
                    "notice, habeas corpus is the emergency vehicle."
                ),
            },
        },
        "common_requirements": {
            "filing_fee": "$375.00 (or MC 20 fee waiver)",
            "page_limit": 50,
            "service": "All parties AND the respondent judge/officer",
            "key_showing": (
                "No adequate legal remedy — must prove that normal appeal "
                "is insufficient to address the harm."
            ),
        },
        "strategic_notes": (
            "Original actions are high-risk, high-reward. The MSC rarely "
            "grants them, but when it does the relief is immediate and "
            "powerful. Best strategy: exhaust all lower court and COA "
            "remedies first (or demonstrate their futility), then present "
            "a clear, focused complaint showing why only MSC intervention "
            "can prevent ongoing constitutional harm."
        ),
    }


def assess_leave_to_appeal_strength(issues: list[str]) -> dict[str, Any]:
    """Assess the strength of a potential MSC leave application.

    Maps the submitted issues against the known criteria the MSC uses
    when deciding whether to grant leave.  Returns a per-criterion
    assessment plus an overall recommendation.

    Args:
        issues: List of short descriptions of the legal issues Andrew
            would present (e.g. ``["due process violation in ex parte
            hearing", "conflict with Troxel v Granville"]``).

    Returns:
        Dictionary with ``criteria`` (list of assessments), ``overall``
        strength rating, and ``recommendations``.
    """
    if not issues:
        return {
            "error": "No issues provided. Supply a list of legal issue descriptions.",
            "example_issues": [
                "Due process violation — parenting time suspended without evidentiary hearing",
                "Conflict with Troxel v Granville — parental rights not treated as fundamental",
                "Ex parte proceedings without proper notice or service",
                "Judicial bias in application of custody factors",
            ],
        }

    issues_lower = [i.lower() for i in issues]
    all_text = " ".join(issues_lower)

    # Keyword mapping for rough criterion matching
    _criterion_keywords: dict[str, list[str]] = {
        "conflict_with_msc_precedent": [
            "conflict", "contradicts", "supreme court precedent",
            "msc precedent", "binding precedent", "departed from",
        ],
        "conflict_with_coa_precedent": [
            "coa conflict", "panel conflict", "split", "inconsistent",
            "different panels",
        ],
        "significant_constitutional_question": [
            "constitutional", "due process", "fundamental right",
            "equal protection", "first amendment", "parental right",
            "troxel", "liberty interest",
        ],
        "major_public_significance": [
            "public significance", "systemic", "widespread", "statewide",
            "affects many", "broad impact", "public interest",
        ],
        "clear_legal_error": [
            "error", "wrong standard", "misapplied", "misinterpreted",
            "ignored", "failed to consider",
        ],
        "question_of_first_impression": [
            "first impression", "novel", "never addressed", "no precedent",
            "unresolved", "new question",
        ],
        "development_of_law": [
            "clarification", "unclear", "ambiguous", "outdated",
            "inconsistent application", "needs guidance",
        ],
    }

    criteria_results: list[dict[str, Any]] = []
    matched_count = 0

    for crit in _LEAVE_CRITERIA:
        crit_id = crit["criterion"]
        keywords = _criterion_keywords.get(crit_id, [])
        matched_keywords = [kw for kw in keywords if kw in all_text]
        is_matched = len(matched_keywords) > 0

        if is_matched:
            matched_count += 1

        criteria_results.append({
            "criterion": crit["label"],
            "weight": crit["weight"],
            "matched": is_matched,
            "matched_keywords": matched_keywords,
            "description": crit["description"],
        })

    # Overall strength
    total = len(_LEAVE_CRITERIA)
    ratio = matched_count / total if total > 0 else 0

    if matched_count >= 4:
        overall = "STRONG"
        recommendation = (
            "Multiple strong criteria are met. This application has a "
            "realistic chance of being granted leave. Prioritise framing "
            "constitutional issues and any conflicts with existing MSC "
            "precedent."
        )
    elif matched_count >= 2:
        overall = "MODERATE"
        recommendation = (
            "Some criteria are met but the application would benefit from "
            "stronger framing. Look for additional conflicts with MSC or "
            "COA precedent, and emphasise the broader public significance "
            "of the issues."
        )
    elif matched_count == 1:
        overall = "MARGINAL"
        recommendation = (
            "Only one criterion is clearly met. Consider whether the issue "
            "can be reframed to satisfy additional criteria, or whether an "
            "alternative vehicle (original action, federal §1983) might be "
            "more effective."
        )
    else:
        overall = "WEAK"
        recommendation = (
            "No clear criteria are matched by the provided issues. The MSC "
            "is unlikely to grant leave. Consider: (1) reframing issues to "
            "highlight constitutional dimensions; (2) identifying conflicts "
            "with existing precedent; (3) pursuing alternative remedies."
        )

    return {
        "issues_evaluated": issues,
        "criteria": criteria_results,
        "matched_criteria_count": matched_count,
        "total_criteria": total,
        "match_ratio": round(ratio, 2),
        "overall_strength": overall,
        "recommendation": recommendation,
        "note": (
            "This is a heuristic assessment based on keyword matching. "
            "Actual MSC decisions depend on the quality of legal argument, "
            "the specific record, and the current composition of the Court."
        ),
    }
