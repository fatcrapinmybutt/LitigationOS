"""Motion Template Library for LitigationOS.

Generates motion documents with proper legal formatting and Michigan Court Rule
(MCR) compliance.  Produces markdown-formatted motions, supporting briefs,
proposed orders, and certificates of service for the six litigation lanes.
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# -- Party & Court Constants (verified identity — never fabricate) -------------

PARTIES = {
    "plaintiff": {
        "name": "Andrew James Pigors",
        "address": "1977 Whitehall Road, Lot 17, North Muskegon, MI 49445",
    },
    "defendant": {
        "name": "Emily A. Watson",
        "address": "2160 Garland Drive, Norton Shores, MI 49441",
    },
    "child": "L.D.W.",
    "judge": "Hon. Jenny L. McNeill",
    "court": "14th Circuit Court, Family Division, Muskegon County, Michigan",
}

CASE_NUMBERS: dict[str, str] = {
    "A": "2024-001507-DC",
    "B": "2025-002760-CZ",
    "D": "2023-5907-PP",
}

DEFAULT_DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

# -- Motion Templates ---------------------------------------------------------

MOTION_TEMPLATES: dict[str, dict] = {
    "dismiss": {
        "title": "Motion to Dismiss",
        "mcr": "MCR 2.116(C)",
        "description": "Motion to dismiss the action for failure to state a claim or other grounds under MCR 2.116(C).",
        "required_elements": [
            "statement_of_issues",
            "statement_of_facts",
            "legal_argument",
            "prayer_for_relief",
            "verification",
            "certificate_of_service",
        ],
        "typical_exhibits": [
            "Relevant pleadings",
            "Supporting affidavits",
            "Documentary evidence",
        ],
        "prayer_for_relief_options": [
            "Dismiss the action with prejudice.",
            "Dismiss the action without prejudice.",
            "Award costs and attorney fees.",
        ],
        "applicable_statutes": ["MCR 2.116(C)(1)-(10)", "MCR 2.116(G)"],
    },
    "summary_judgment": {
        "title": "Motion for Summary Disposition",
        "mcr": "MCR 2.116(C)(10)",
        "description": "Motion for summary disposition where there is no genuine issue of material fact.",
        "required_elements": [
            "statement_of_issues",
            "statement_of_facts",
            "statement_of_undisputed_facts",
            "legal_argument",
            "prayer_for_relief",
            "verification",
            "certificate_of_service",
        ],
        "typical_exhibits": [
            "Affidavits of fact",
            "Deposition transcripts",
            "Documentary evidence",
            "Admissions",
        ],
        "prayer_for_relief_options": [
            "Grant summary disposition in favor of Plaintiff.",
            "Enter judgment as a matter of law.",
        ],
        "applicable_statutes": ["MCR 2.116(C)(10)", "MCR 2.116(G)(4)"],
    },
    "compel_discovery": {
        "title": "Motion to Compel Discovery",
        "mcr": "MCR 2.313(A)",
        "description": "Motion to compel a party to respond to discovery requests.",
        "required_elements": [
            "statement_of_issues",
            "description_of_discovery_requests",
            "good_faith_efforts",
            "legal_argument",
            "prayer_for_relief",
            "certificate_of_service",
        ],
        "typical_exhibits": [
            "Discovery requests served",
            "Proof of service of discovery",
            "Correspondence regarding discovery",
            "Incomplete or deficient responses",
        ],
        "prayer_for_relief_options": [
            "Compel Defendant to fully respond to discovery requests within 14 days.",
            "Award reasonable expenses including attorney fees under MCR 2.313(A)(5).",
            "Impose sanctions for failure to comply.",
        ],
        "applicable_statutes": ["MCR 2.313(A)", "MCR 2.313(B)", "MCR 2.310"],
    },
    "sanctions": {
        "title": "Motion for Sanctions",
        "mcr": "MCR 2.114(E)",
        "description": "Motion for sanctions for frivolous filings or litigation misconduct.",
        "required_elements": [
            "statement_of_issues",
            "description_of_sanctionable_conduct",
            "legal_argument",
            "prayer_for_relief",
            "certificate_of_service",
        ],
        "typical_exhibits": [
            "Offending pleading or filing",
            "Evidence of bad faith",
            "Cost documentation",
        ],
        "prayer_for_relief_options": [
            "Impose sanctions under MCR 2.114(E).",
            "Award costs and reasonable attorney fees.",
            "Strike the offending pleading.",
        ],
        "applicable_statutes": ["MCR 2.114(D)-(E)", "MCL 600.2591"],
    },
    "disqualify_judge": {
        "title": "Motion to Disqualify Judge",
        "mcr": "MCR 2.003(C)",
        "description": "Motion to disqualify the assigned judge for bias, prejudice, or other disqualifying grounds.",
        "required_elements": [
            "statement_of_issues",
            "factual_basis_for_disqualification",
            "legal_argument",
            "affidavit_of_bias",
            "prayer_for_relief",
            "certificate_of_service",
        ],
        "typical_exhibits": [
            "Affidavit of prejudice",
            "Hearing transcripts showing bias",
            "Orders demonstrating pattern of prejudice",
            "Judicial conduct code violations",
        ],
        "prayer_for_relief_options": [
            "Disqualify Hon. Jenny L. McNeill from further proceedings.",
            "Reassign the case to a different judge.",
            "Vacate orders entered by the disqualified judge.",
        ],
        "applicable_statutes": [
            "MCR 2.003(C)(1)",
            "MCL 600.1401-1427",
            "Michigan Code of Judicial Conduct Canon 2",
        ],
    },
    "contempt": {
        "title": "Motion for Contempt",
        "mcr": "MCR 3.606",
        "description": "Motion to hold a party in contempt for violating a court order.",
        "required_elements": [
            "identification_of_order_violated",
            "statement_of_facts",
            "description_of_violations",
            "legal_argument",
            "prayer_for_relief",
            "certificate_of_service",
        ],
        "typical_exhibits": [
            "Court order allegedly violated",
            "Evidence of violation",
            "Communication records",
            "Timeline of violations",
        ],
        "prayer_for_relief_options": [
            "Hold Defendant in contempt of court.",
            "Impose appropriate sanctions.",
            "Award compensatory damages.",
            "Award reasonable attorney fees.",
        ],
        "applicable_statutes": ["MCR 3.606", "MCL 600.1701", "MCL 600.1715"],
    },
    "modify_custody": {
        "title": "Motion to Modify Custody",
        "mcr": "MCR 3.210",
        "description": "Motion to modify the existing custody order based on change in circumstances.",
        "required_elements": [
            "statement_of_issues",
            "current_custody_arrangement",
            "change_in_circumstances",
            "best_interest_factors",
            "legal_argument",
            "prayer_for_relief",
            "certificate_of_service",
        ],
        "typical_exhibits": [
            "Current custody order",
            "Evidence of changed circumstances",
            "Best interest factor documentation",
            "School records",
            "Medical records",
        ],
        "prayer_for_relief_options": [
            "Modify custody in the best interests of L.D.W.",
            "Award sole legal custody to Plaintiff.",
            "Award sole physical custody to Plaintiff.",
            "Order a custody evaluation.",
        ],
        "applicable_statutes": [
            "MCR 3.210",
            "MCL 722.23 (best interest factors)",
            "MCL 722.27",
        ],
    },
    "modify_parenting_time": {
        "title": "Motion to Modify Parenting Time",
        "mcr": "MCR 3.210",
        "description": "Motion to modify the existing parenting time order.",
        "required_elements": [
            "statement_of_issues",
            "current_parenting_time_schedule",
            "reasons_for_modification",
            "proposed_schedule",
            "legal_argument",
            "prayer_for_relief",
            "certificate_of_service",
        ],
        "typical_exhibits": [
            "Current parenting time order",
            "Proposed parenting time schedule",
            "Communication logs",
            "Documentation of denied parenting time",
        ],
        "prayer_for_relief_options": [
            "Modify parenting time to the proposed schedule.",
            "Award make-up parenting time.",
            "Order supervised parenting time.",
            "Impose specific enforcement provisions.",
        ],
        "applicable_statutes": [
            "MCR 3.210",
            "MCL 722.27a",
            "MCL 722.27b (parenting time)",
        ],
    },
    "modify_support": {
        "title": "Motion to Modify Child Support",
        "mcr": "MCR 3.211",
        "description": "Motion to modify child support based on a change in financial circumstances.",
        "required_elements": [
            "statement_of_issues",
            "current_support_order",
            "change_in_circumstances",
            "income_documentation",
            "legal_argument",
            "prayer_for_relief",
            "certificate_of_service",
        ],
        "typical_exhibits": [
            "Current support order",
            "Pay stubs / income verification",
            "Tax returns",
            "UIFSA uniform support calculation",
        ],
        "prayer_for_relief_options": [
            "Modify child support consistent with the Michigan Child Support Formula.",
            "Order income verification from both parties.",
            "Award retroactive support modification.",
        ],
        "applicable_statutes": [
            "MCR 3.211",
            "MCL 552.517",
            "Michigan Child Support Formula",
        ],
    },
    "emergency_custody": {
        "title": "Ex Parte Motion for Emergency Custody",
        "mcr": "MCR 3.207(B)",
        "description": "Emergency ex parte motion for temporary custody when the child faces immediate harm.",
        "required_elements": [
            "statement_of_emergency",
            "irreparable_harm_showing",
            "statement_of_facts",
            "legal_argument",
            "prayer_for_relief",
            "verification",
            "certificate_of_service",
        ],
        "typical_exhibits": [
            "Affidavit of emergency",
            "Police reports",
            "CPS reports",
            "Medical records",
            "Photographs",
        ],
        "prayer_for_relief_options": [
            "Grant immediate temporary custody to Plaintiff.",
            "Suspend Defendant's parenting time pending hearing.",
            "Order supervised visitation only.",
            "Schedule an emergency hearing within 14 days.",
        ],
        "applicable_statutes": [
            "MCR 3.207(B)",
            "MCL 722.27(1)(c)",
            "MCL 722.23",
        ],
    },
    "ppo": {
        "title": "Petition for Personal Protection Order",
        "mcr": "MCR 3.703",
        "description": "Petition for a personal protection order based on domestic violence or stalking.",
        "required_elements": [
            "petition_form",
            "statement_of_facts",
            "specific_incidents",
            "prayer_for_relief",
        ],
        "typical_exhibits": [
            "Police reports",
            "Medical records",
            "Photographs of injuries",
            "Threatening communications",
            "Witness statements",
        ],
        "prayer_for_relief_options": [
            "Enter a personal protection order.",
            "Prohibit contact with Plaintiff.",
            "Prohibit entering Plaintiff's residence.",
            "Other relief as the Court deems appropriate.",
        ],
        "applicable_statutes": [
            "MCR 3.703",
            "MCR 3.705",
            "MCL 600.2950",
            "MCL 600.2950a",
        ],
    },
    "ppo_violation": {
        "title": "Motion for PPO Violation",
        "mcr": "MCR 3.708",
        "description": "Motion alleging violation of an existing personal protection order.",
        "required_elements": [
            "identification_of_ppo",
            "description_of_violations",
            "statement_of_facts",
            "legal_argument",
            "prayer_for_relief",
            "certificate_of_service",
        ],
        "typical_exhibits": [
            "Existing PPO",
            "Evidence of violation (messages, photos, police reports)",
            "Timeline of violations",
            "Witness statements",
        ],
        "prayer_for_relief_options": [
            "Find Defendant in violation of the PPO.",
            "Hold Defendant in criminal contempt.",
            "Extend the duration of the PPO.",
            "Impose additional restrictions.",
        ],
        "applicable_statutes": ["MCR 3.708", "MCL 600.2950(23)", "MCL 750.411h"],
    },
    "default_judgment": {
        "title": "Motion for Default Judgment",
        "mcr": "MCR 2.603",
        "description": "Motion for default judgment when the opposing party fails to plead or defend.",
        "required_elements": [
            "proof_of_service",
            "affidavit_of_default",
            "statement_of_claim",
            "prayer_for_relief",
            "proposed_judgment",
            "certificate_of_service",
        ],
        "typical_exhibits": [
            "Proof of service of summons and complaint",
            "Affidavit of non-answer",
            "Affidavit of damages",
        ],
        "prayer_for_relief_options": [
            "Enter default judgment against Defendant.",
            "Award damages as set forth in the Complaint.",
            "Award costs of suit.",
        ],
        "applicable_statutes": ["MCR 2.603(A)", "MCR 2.603(B)"],
    },
    "reconsideration": {
        "title": "Motion for Reconsideration",
        "mcr": "MCR 2.119(F)",
        "description": (
            "Motion for reconsideration of a prior order.  Must be filed within "
            "21 days and demonstrate a palpable error."
        ),
        "required_elements": [
            "identification_of_order",
            "palpable_error_showing",
            "legal_argument",
            "prayer_for_relief",
            "certificate_of_service",
        ],
        "typical_exhibits": [
            "Order subject to reconsideration",
            "New evidence (if applicable)",
            "Transcript of hearing",
        ],
        "prayer_for_relief_options": [
            "Reconsider and vacate the order entered on [date].",
            "Enter a corrected order consistent with this motion.",
        ],
        "applicable_statutes": ["MCR 2.119(F)(1)-(3)"],
    },
    "stay": {
        "title": "Motion for Stay Pending Appeal",
        "mcr": "MCR 7.209",
        "description": "Motion to stay enforcement of a judgment or order pending appellate review.",
        "required_elements": [
            "identification_of_order",
            "likelihood_of_success_on_merits",
            "irreparable_harm",
            "balance_of_equities",
            "legal_argument",
            "prayer_for_relief",
            "certificate_of_service",
        ],
        "typical_exhibits": [
            "Order or judgment to be stayed",
            "Notice of appeal (if filed)",
            "Evidence of irreparable harm",
        ],
        "prayer_for_relief_options": [
            "Stay enforcement of the order pending appeal.",
            "Waive or reduce the bond requirement.",
        ],
        "applicable_statutes": ["MCR 7.209(A)", "MCR 7.209(E)"],
    },
    "new_trial": {
        "title": "Motion for New Trial",
        "mcr": "MCR 2.611",
        "description": "Motion for a new trial based on irregularity, misconduct, or newly discovered evidence.",
        "required_elements": [
            "statement_of_issues",
            "grounds_for_new_trial",
            "legal_argument",
            "prayer_for_relief",
            "certificate_of_service",
        ],
        "typical_exhibits": [
            "Trial transcript",
            "Newly discovered evidence",
            "Affidavits",
        ],
        "prayer_for_relief_options": [
            "Grant a new trial on all issues.",
            "Grant a new trial limited to [specific issue].",
        ],
        "applicable_statutes": ["MCR 2.611(A)(1)", "MCR 2.611(B)"],
    },
    "relief_from_judgment": {
        "title": "Motion for Relief from Judgment",
        "mcr": "MCR 2.612",
        "description": "Motion for relief from a final judgment or order under MCR 2.612(C).",
        "required_elements": [
            "identification_of_judgment",
            "grounds_for_relief",
            "legal_argument",
            "prayer_for_relief",
            "certificate_of_service",
        ],
        "typical_exhibits": [
            "Judgment or order at issue",
            "Evidence supporting grounds for relief",
            "Affidavits",
        ],
        "prayer_for_relief_options": [
            "Set aside the judgment entered on [date].",
            "Reopen the case for further proceedings.",
        ],
        "applicable_statutes": ["MCR 2.612(C)(1)(a)-(f)"],
    },
}

# -- Helper: Caption Block ----------------------------------------------------


def _build_caption(case_number: str, title: str) -> str:
    """Return the Michigan standard caption block as a markdown string."""
    return (
        "STATE OF MICHIGAN\n"
        "IN THE 14TH JUDICIAL CIRCUIT COURT\n"
        "FOR THE COUNTY OF MUSKEGON\n"
        "FAMILY DIVISION\n"
        "\n"
        f"ANDREW JAMES PIGORS,{' ' * 8}Case No. {case_number}\n"
        f"    Plaintiff,{' ' * 15}Hon. Jenny L. McNeill\n"
        "v.\n"
        "EMILY A. WATSON,\n"
        "    Defendant.\n"
        "_________________________________/\n"
        "\n"
        f"{'':>16}{title.upper()}\n"
    )


# -- Engine -------------------------------------------------------------------


class MotionTemplateEngine:
    """Generate court-ready motion documents with MCR compliance.

    Parameters
    ----------
    db_path : str | None
        Path to ``litigation_context.db``.  Falls back to the canonical repo
        location when *None*.
    """

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path or DEFAULT_DB_PATH
        self._conn: sqlite3.Connection | None = None
        self._connect()

    # -- DB lifecycle ----------------------------------------------------------

    def _connect(self) -> None:
        """Open a WAL-mode connection with LitigationOS PRAGMAs."""
        try:
            self._conn = sqlite3.connect(self._db_path, timeout=60)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA busy_timeout = 60000")
            self._conn.execute("PRAGMA journal_mode = WAL")
            self._conn.execute("PRAGMA cache_size = -32000")
            self._conn.execute("PRAGMA temp_store = MEMORY")
            self._conn.execute("PRAGMA synchronous = NORMAL")
        except sqlite3.Error:
            logger.warning("Could not open DB at %s — running template-only mode.", self._db_path)
            self._conn = None

    def close(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    # -- Template catalogue ----------------------------------------------------

    def get_templates(self) -> list[dict]:
        """Return every available motion template.

        Each dict contains: *id*, *title*, *description*, *mcr_authority*,
        *required_elements*, and *typical_exhibits*.
        """
        templates: list[dict] = []
        for tid, tpl in MOTION_TEMPLATES.items():
            templates.append(
                {
                    "id": tid,
                    "title": tpl["title"],
                    "description": tpl["description"],
                    "mcr_authority": tpl["mcr"],
                    "required_elements": list(tpl["required_elements"]),
                    "typical_exhibits": list(tpl["typical_exhibits"]),
                }
            )
        return templates

    def get_required_exhibits(self, template_id: str) -> list[dict]:
        """Return required and recommended exhibits for *template_id*.

        Each dict: ``{"exhibit": str, "required": bool}``.
        """
        tpl = MOTION_TEMPLATES.get(template_id)
        if tpl is None:
            logger.error("Unknown template_id: %s", template_id)
            return []
        return [{"exhibit": ex, "required": True} for ex in tpl["typical_exhibits"]]

    # -- Generation: full motion -----------------------------------------------

    def generate_motion(
        self,
        template_id: str,
        case_number: str,
        facts: list[str] | None = None,
        authorities: list[str] | None = None,
        exhibits: list[str] | None = None,
        lane: str = "A",
    ) -> str:
        """Generate a complete motion document in markdown.

        Returns a single string containing caption, title, statement of issues,
        statement of facts, IRAC-structured legal argument, prayer for relief,
        verification / signature block, certificate of service, and proposed
        order.
        """
        tpl = MOTION_TEMPLATES.get(template_id)
        if tpl is None:
            return f"<!-- ERROR: Unknown template '{template_id}' -->"

        case_no = case_number or CASE_NUMBERS.get(lane, "UNKNOWN")
        today = datetime.now().strftime("%B %d, %Y")
        facts = facts or ["[FACTS TO BE SUPPLIED]"]
        authorities = authorities or [tpl["mcr"]]
        exhibits = exhibits or tpl["typical_exhibits"]

        sections: list[str] = []

        # Caption
        sections.append(_build_caption(case_no, tpl["title"]))

        # Statement of Issues
        sections.append("## STATEMENT OF ISSUES\n")
        sections.append(
            f"Whether the Court should grant {tpl['title']} pursuant to {tpl['mcr']}.\n"
        )

        # Statement of Facts
        sections.append("## STATEMENT OF FACTS\n")
        for idx, fact in enumerate(facts, 1):
            sections.append(f"{idx}. {fact}\n")
        sections.append("")

        # Legal Argument (IRAC structure per authority)
        sections.append("## LEGAL ARGUMENT\n")
        for auth in authorities:
            sections.append(f"### Authority: {auth}\n")
            sections.append(f"**Issue:** Whether relief is warranted under {auth}.\n")
            sections.append(
                f"**Rule:** {auth} provides the legal standard applicable to this motion.\n"
            )
            sections.append(
                "**Application:** The facts set forth above satisfy the requirements of "
                f"{auth} because:\n"
            )
            for idx, fact in enumerate(facts, 1):
                sections.append(f"  {idx}. {fact}\n")
            sections.append(
                f"\n**Conclusion:** The Court should grant the requested relief under {auth}.\n"
            )

        # Prayer for Relief
        sections.append("## PRAYER FOR RELIEF\n")
        sections.append("WHEREFORE, Plaintiff respectfully requests that this Court:\n")
        for idx, prayer in enumerate(tpl["prayer_for_relief_options"], 1):
            sections.append(f"{idx}. {prayer}\n")
        sections.append(
            f"{len(tpl['prayer_for_relief_options']) + 1}. "
            "Grant such other and further relief as this Court deems just and equitable.\n"
        )

        # Exhibit List
        if exhibits:
            sections.append("\n## EXHIBIT LIST\n")
            for idx, ex in enumerate(exhibits, 1):
                sections.append(f"Exhibit {idx}: {ex}\n")

        # Verification / Signature Block
        sections.append("\n## VERIFICATION\n")
        sections.append(
            "I, Andrew James Pigors, declare under the penalties of perjury that the "
            "statements in this motion are true to the best of my information, knowledge, "
            "and belief.\n"
        )
        sections.append(f"\nDated: {today}\n")
        sections.append("\nRespectfully submitted,\n")
        sections.append(f"\n_____________________________\n{PARTIES['plaintiff']['name']}")
        sections.append(f"\n{PARTIES['plaintiff']['address']}\n")
        sections.append("Pro Se Plaintiff\n")

        # Certificate of Service
        sections.append(
            self.generate_certificate_of_service(
                case_no,
                documents=[tpl["title"]],
                service_method="first-class mail",
            )
        )

        # Proposed Order
        sections.append(
            self.generate_proposed_order(
                template_id,
                case_no,
                relief=tpl["prayer_for_relief_options"],
            )
        )

        return "\n".join(sections)

    # -- Generation: supporting brief ------------------------------------------

    def generate_brief(
        self,
        template_id: str,
        case_number: str,
        facts: list[str] | None = None,
        lane: str = "A",
    ) -> str:
        """Generate a supporting brief / memorandum of law for the motion."""
        tpl = MOTION_TEMPLATES.get(template_id)
        if tpl is None:
            return f"<!-- ERROR: Unknown template '{template_id}' -->"

        case_no = case_number or CASE_NUMBERS.get(lane, "UNKNOWN")
        today = datetime.now().strftime("%B %d, %Y")
        facts = facts or ["[FACTS TO BE SUPPLIED]"]
        statutes = tpl.get("applicable_statutes", [tpl["mcr"]])

        parts: list[str] = []

        parts.append(
            _build_caption(case_no, f"Brief in Support of {tpl['title']}")
        )

        # Introduction
        parts.append("## INTRODUCTION\n")
        parts.append(
            f"Plaintiff, Andrew James Pigors, by and through himself, pro se, "
            f"submits this Brief in Support of his {tpl['title']} and states as follows.\n"
        )

        # Statement of Facts
        parts.append("## STATEMENT OF FACTS\n")
        for idx, fact in enumerate(facts, 1):
            parts.append(f"{idx}. {fact}\n")
        parts.append("")

        # Legal Standard
        parts.append("## LEGAL STANDARD\n")
        parts.append(
            f"The legal standard governing this motion is set forth in {tpl['mcr']}.\n"
        )
        for statute in statutes:
            parts.append(f"- {statute}\n")
        parts.append("")

        # Argument
        parts.append("## ARGUMENT\n")
        parts.append(
            f"The facts of this case satisfy the requirements of {tpl['mcr']}.\n"
        )
        for idx, fact in enumerate(facts, 1):
            parts.append(
                f"{idx}. Regarding fact {idx}: {fact} — This satisfies the applicable standard.\n"
            )
        parts.append("")

        # Conclusion
        parts.append("## CONCLUSION\n")
        parts.append(
            f"For the foregoing reasons, Plaintiff respectfully requests that this "
            f"Court grant the {tpl['title']}.\n"
        )

        parts.append(f"\nDated: {today}\n")
        parts.append("\nRespectfully submitted,\n")
        parts.append(f"\n_____________________________\n{PARTIES['plaintiff']['name']}")
        parts.append(f"\n{PARTIES['plaintiff']['address']}\n")
        parts.append("Pro Se Plaintiff\n")

        return "\n".join(parts)

    # -- Generation: proposed order --------------------------------------------

    def generate_proposed_order(
        self,
        template_id: str,
        case_number: str,
        relief: list[str] | None = None,
    ) -> str:
        """Generate a proposed order for judge signature."""
        tpl = MOTION_TEMPLATES.get(template_id)
        if tpl is None:
            return f"<!-- ERROR: Unknown template '{template_id}' -->"

        relief = relief or tpl["prayer_for_relief_options"]
        today = datetime.now().strftime("%B %d, %Y")

        parts: list[str] = [
            "\n---\n",
            _build_caption(case_number, f"Order on {tpl['title']}"),
            "At a session of said Court held in the\n"
            "Courthouse in the City of Muskegon,\n"
            f"County of Muskegon, State of Michigan\n"
            f"on {today}.\n",
            f"\nPRESENT: {PARTIES['judge']}\n",
            "## ORDER\n",
            (
                f"This matter having come before the Court on Plaintiff's {tpl['title']}, "
                "and the Court being fully advised in the premises,\n"
            ),
            "IT IS HEREBY ORDERED:\n",
        ]

        for idx, item in enumerate(relief, 1):
            parts.append(f"{idx}. {item}\n")
        parts.append("")

        parts.append(
            "IT IS SO ORDERED.\n"
            "\n"
            f"Dated: _______________\n"
            "\n"
            "_____________________________\n"
            f"{PARTIES['judge']}\n"
            "14th Circuit Court Judge\n"
        )
        return "\n".join(parts)

    # -- Generation: certificate of service ------------------------------------

    def generate_certificate_of_service(
        self,
        case_number: str,
        documents: list[str] | None = None,
        service_method: str = "first-class mail",
    ) -> str:
        """Generate a certificate of service per MCR 2.107.

        Parameters
        ----------
        case_number : str
            The case number to reference.
        documents : list[str] | None
            List of document names served.
        service_method : str
            Method of service (default: first-class mail).
        """
        today = datetime.now().strftime("%B %d, %Y")
        docs = documents or ["the foregoing documents"]
        doc_list = ", ".join(docs)

        return (
            "\n## CERTIFICATE OF SERVICE\n\n"
            "I, Andrew James Pigors, certify that on "
            f"{today}, I served a true copy of {doc_list} upon:\n\n"
            f"  {PARTIES['defendant']['name']}\n"
            f"  {PARTIES['defendant']['address']}\n\n"
            f"by {service_method}, postage prepaid, in compliance with MCR 2.107.\n\n"
            f"_____________________________\n"
            f"{PARTIES['plaintiff']['name']}\n"
        )

    # -- Validation ------------------------------------------------------------

    def validate_motion(self, motion_text: str, template_id: str) -> dict:
        """Check whether *motion_text* includes all required elements.

        Returns
        -------
        dict
            ``is_valid`` (bool), ``missing_elements`` (list[str]),
            ``warnings`` (list[str]).
        """
        tpl = MOTION_TEMPLATES.get(template_id)
        if tpl is None:
            return {
                "is_valid": False,
                "missing_elements": [],
                "warnings": [f"Unknown template '{template_id}'."],
            }

        lowered = motion_text.lower()
        missing: list[str] = []
        warnings: list[str] = []

        # Element → text markers mapping
        element_markers: dict[str, list[str]] = {
            "statement_of_issues": ["statement of issues"],
            "statement_of_facts": ["statement of facts"],
            "legal_argument": ["legal argument", "argument"],
            "prayer_for_relief": ["prayer for relief", "wherefore"],
            "verification": ["verification", "penalties of perjury"],
            "certificate_of_service": ["certificate of service"],
            "affidavit_of_bias": ["affidavit", "bias", "prejudice"],
            "identification_of_order": ["order entered", "order dated"],
            "identification_of_order_violated": ["order", "violated"],
            "description_of_violations": ["violation"],
            "palpable_error_showing": ["palpable error"],
            "good_faith_efforts": ["good faith"],
            "statement_of_emergency": ["emergency", "immediate harm"],
            "irreparable_harm_showing": ["irreparable harm"],
            "irreparable_harm": ["irreparable harm"],
            "likelihood_of_success_on_merits": ["likelihood of success", "merits"],
            "balance_of_equities": ["balance of equities", "balance of harm"],
            "description_of_discovery_requests": ["discovery request"],
            "description_of_sanctionable_conduct": ["sanction"],
            "factual_basis_for_disqualification": ["disqualif"],
            "identification_of_ppo": ["protection order", "ppo"],
            "identification_of_judgment": ["judgment"],
            "grounds_for_relief": ["grounds", "relief"],
            "grounds_for_new_trial": ["new trial", "grounds"],
            "current_custody_arrangement": ["custody", "current"],
            "change_in_circumstances": ["change", "circumstance"],
            "best_interest_factors": ["best interest"],
            "current_parenting_time_schedule": ["parenting time", "schedule"],
            "reasons_for_modification": ["modif"],
            "proposed_schedule": ["proposed schedule", "proposed"],
            "current_support_order": ["support order", "current"],
            "income_documentation": ["income"],
            "proof_of_service": ["proof of service"],
            "affidavit_of_default": ["default", "affidavit"],
            "statement_of_claim": ["claim"],
            "proposed_judgment": ["proposed judgment", "judgment"],
            "petition_form": ["petition"],
            "specific_incidents": ["incident"],
            "statement_of_undisputed_facts": ["undisputed fact"],
        }

        for element in tpl["required_elements"]:
            markers = element_markers.get(element, [element.replace("_", " ")])
            if not any(m in lowered for m in markers):
                missing.append(element)

        # Additional quality checks
        if PARTIES["plaintiff"]["name"].lower() not in lowered:
            warnings.append("Plaintiff's full name not found in motion text.")
        if "case no." not in lowered and "case number" not in lowered:
            warnings.append("Case number reference not found.")
        if "mcr" not in lowered:
            warnings.append("No Michigan Court Rule citation found.")

        return {
            "is_valid": len(missing) == 0,
            "missing_elements": missing,
            "warnings": warnings,
        }

    # -- DB helpers (query supporting data) ------------------------------------

    def _query_db(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        """Run a read query against the DB, returning rows or empty list."""
        if self._conn is None:
            return []
        try:
            return self._conn.execute(sql, params).fetchall()
        except sqlite3.Error:
            logger.exception("DB query failed: %s", sql[:120])
            return []

    def get_case_facts(self, case_number: str, limit: int = 20) -> list[str]:
        """Retrieve fact summaries from the DB for *case_number*."""
        rows = self._query_db(
            "SELECT fact_text FROM case_facts WHERE case_number = ? ORDER BY fact_date LIMIT ?",
            (case_number, limit),
        )
        return [str(r["fact_text"]) for r in rows]

    def get_evidence_for_motion(self, template_id: str, case_number: str) -> list[dict]:
        """Retrieve evidence items that may support *template_id* for *case_number*."""
        tpl = MOTION_TEMPLATES.get(template_id)
        if tpl is None:
            return []
        keyword = tpl["title"].split()[-1].lower()
        rows = self._query_db(
            "SELECT evidence_id, description, source_file FROM evidence "
            "WHERE case_number = ? AND description LIKE ? LIMIT 50",
            (case_number, f"%{keyword}%"),
        )
        return [dict(r) for r in rows]
