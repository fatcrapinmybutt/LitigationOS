"""Discovery document generator engine.

Generates litigation discovery documents (interrogatories, requests for
production, requests for admission, subpoenas) from database evidence and
claims.  All output is Michigan-court-compliant markdown ready for
conversion to PDF via the pdf_production module.

Michigan Court Rules referenced:
    MCR 2.309(A)(2) — Interrogatories (25 limit including subparts)
    MCR 2.310       — Requests for Production of Documents
    MCR 2.312       — Requests for Admission
    MCR 2.506       — Subpoena Duces Tecum
    MCR 8.119(H)    — Minor initials only in filings
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from textwrap import dedent
from typing import Any, Optional

from litigationos.data.rule_lookup import get_rule_text, search_rules

logger = logging.getLogger(__name__)

# -- Constants ----------------------------------------------------------------

DEFAULT_DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

PARTIES: dict[str, Any] = {
    "plaintiff": {
        "name": "Andrew James Pigors",
        "address": "1977 Whitehall Road, Lot 17, North Muskegon, MI 49445",
        "phone": "(231) 903-5690",
        "email": "andrewjpigors@gmail.com",
    },
    "defendant": {
        "name": "Emily A. Watson",
        "address": "2160 Garland Drive, Norton Shores, MI 49441",
    },
    "child": "L.D.W.",  # MCR 8.119(H) — initials only
    "judge": "Hon. Jenny L. McNeill",
    "court": "14th Circuit Court, Family Division, Muskegon County",
    "foc": {
        "name": "Pamela Rusco",
        "address": "990 Terrace St, Muskegon, MI 49442",
    },
}

CASE_NUMBERS: dict[str, str] = {
    "A": "2024-001507-DC",
    "B": "2025-002760-CZ",
    "D": "2023-5907-PP",
}

# Discovery topic categories for auto-generation
DISCOVERY_TOPICS: dict[str, list[str]] = {
    "custody": [
        "Parenting time schedules and deviations",
        "Child welfare and safety concerns",
        "Living conditions at each residence",
        "School enrollment and academic performance",
        "Medical and dental care history",
        "Mental health treatment for the minor child",
        "Childcare arrangements during work hours",
        "Extracurricular activities and participation",
    ],
    "financial": [
        "Gross and net income from all sources",
        "Assets including real property and vehicles",
        "Outstanding debts and financial obligations",
        "Monthly living expenses",
        "Federal and state tax returns (3 years)",
        "Bank account statements (12 months)",
        "Retirement and investment accounts",
        "Child support payment history",
    ],
    "communications": [
        "Text messages between parties regarding the child",
        "Email correspondence regarding parenting time",
        "Social media posts referencing the child or litigation",
        "Phone call logs between parties",
        "Communications with third parties about custody",
        "Messages sent through parenting apps",
    ],
    "interference": [
        "Instances of denied parenting time",
        "Alienating statements made to or about the child",
        "Blocked communication attempts with the child",
        "Failure to follow court-ordered parenting schedules",
        "Unilateral decisions about the child without consultation",
        "Interference with parent-child telephone contact",
    ],
    "domestic_violence": [
        "Personal protection order history",
        "Police reports involving either party",
        "Documented injuries or medical treatment",
        "Witness statements regarding incidents",
        "Photographs of injuries or property damage",
        "Counseling or intervention program records",
    ],
    "housing": [
        "Current lease or mortgage agreements",
        "Housing conditions and safety inspections",
        "Persons residing in the household",
        "Plans for relocation or change of residence",
        "Child's sleeping arrangements and personal space",
        "Proximity to school and extracurricular activities",
    ],
    "employment": [
        "Current employment and work schedules",
        "Income verification from employer",
        "History of employment changes (2 years)",
        "Childcare arrangements during work hours",
        "Remote work availability and schedule flexibility",
        "Employer benefits including health insurance",
    ],
    "third_party": [
        "Ronald Berry's involvement in child's daily life",
        "Overnight guests at the child's residence",
        "New romantic partners introduced to the child",
        "Family members providing regular childcare",
        "Third-party witnesses to parenting practices",
        "Background or criminal history of household members",
    ],
}

# -- Helpers ------------------------------------------------------------------


def _today() -> str:
    """Return today's date formatted for court documents."""
    return datetime.now().strftime("%B %d, %Y")


def _deadline_date(days: int = 28) -> str:
    """Return a response deadline date (default 28 days per MCR 2.309)."""
    return (datetime.now() + timedelta(days=days)).strftime("%B %d, %Y")


def _caption(case_number: str, title: str) -> str:
    """Build a standard Michigan court caption block."""
    return dedent(f"""\
        # STATE OF MICHIGAN
        ## IN THE {PARTIES["court"].upper()}

        ---

        **{PARTIES["plaintiff"]["name"]}**,
        Plaintiff,

        v. Case No. {case_number}

        **{PARTIES["defendant"]["name"]}**,
        Defendant.

        {PARTIES["judge"]}

        ---

        ## {title.upper()}

        ---
    """)


def _certificate_of_service(case_number: str) -> str:
    """Build a certificate of service block."""
    defendant = PARTIES["defendant"]
    return dedent(f"""\
        ---

        ## CERTIFICATE OF SERVICE

        I, {PARTIES["plaintiff"]["name"]}, hereby certify that on {_today()},
        I served a true and correct copy of this document upon:

        **{defendant["name"]}**
        {defendant["address"]}

        by first-class U.S. mail, postage prepaid, and/or by electronic means
        as permitted by the Court.

        Date: {_today()}

        ___________________________
        {PARTIES["plaintiff"]["name"]}, Plaintiff (Self-Represented)
        {PARTIES["plaintiff"]["address"]}
        {PARTIES["plaintiff"]["phone"]}
        {PARTIES["plaintiff"]["email"]}
    """)


# -- Engine -------------------------------------------------------------------


class DiscoveryGenerator:
    """Generate Michigan-compliant discovery documents from DB evidence.

    Connects to ``litigation_context.db`` and uses claims, evidence gaps,
    and case data to produce tailored interrogatories, document requests,
    requests for admission, subpoenas, and discovery plans.
    """

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path or DEFAULT_DB_PATH
        self._conn: sqlite3.Connection | None = None
        self._connect()

    # -- Connection management ------------------------------------------------

    def _connect(self) -> None:
        """Open a WAL-mode connection with LitigationOS PRAGMAs."""
        try:
            self._conn = sqlite3.connect(self._db_path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA busy_timeout = 60000")
            self._conn.execute("PRAGMA journal_mode = WAL")
            self._conn.execute("PRAGMA cache_size = -32000")
            self._conn.execute("PRAGMA temp_store = MEMORY")
            self._conn.execute("PRAGMA synchronous = NORMAL")
            logger.info("DiscoveryGenerator connected to %s", self._db_path)
        except sqlite3.Error:
            logger.exception("Failed to connect to %s", self._db_path)
            self._conn = None

    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def _query(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        """Execute a read query and return rows, or empty list on error."""
        if not self._conn:
            logger.warning("No DB connection — returning empty result set")
            return []
        try:
            return self._conn.execute(sql, params).fetchall()
        except sqlite3.Error:
            logger.exception("Query failed: %s", sql[:120])
            return []

    # -- Evidence / claims helpers -------------------------------------------

    def _get_claims(self, case_number: str) -> list[sqlite3.Row]:
        """Fetch claims associated with a case number."""
        for col in ("case_number", "vehicle_name"):
            rows = self._query(
                f"SELECT * FROM claims WHERE {col} = ?", (case_number,)
            )
            if rows:
                return rows
        return []

    def _get_evidence_gaps(self, lane: str) -> list[sqlite3.Row]:
        """Fetch evidence gaps for a lane, if the table exists."""
        rows = self._query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='evidence_gaps'"
        )
        if not rows:
            return []
        return self._query(
            "SELECT * FROM evidence_gaps WHERE vehicle_name = ?",
            (CASE_NUMBERS.get(lane, ""),),
        )

    def _get_deadlines(self, case_number: str) -> list[sqlite3.Row]:
        """Fetch active deadlines for a case."""
        return self._query(
            "SELECT * FROM deadlines WHERE vehicle_name = ? AND status != 'completed' "
            "ORDER BY due_date_iso ASC",
            (case_number,),
        )

    def _get_next_hearing(self, case_number: str) -> str | None:
        """Look up the next scheduled hearing date from the deadlines table."""
        rows = self._query(
            "SELECT due_date_iso FROM deadlines "
            "WHERE vehicle_name = ? AND status != 'completed' "
            "AND (description LIKE '%hearing%' OR description LIKE '%Hearing%' "
            "     OR category LIKE '%hearing%') "
            "AND due_date_iso >= date('now') "
            "ORDER BY due_date_iso ASC LIMIT 1",
            (case_number,),
        )
        if rows:
            return dict(rows[0]).get("due_date_iso")
        # Fallback: try docket_events table for scheduled hearings
        rows = self._query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='docket_events'"
        )
        if rows:
            hearing_rows = self._query(
                "SELECT event_date FROM docket_events "
                "WHERE case_number = ? AND event_type LIKE '%hearing%' "
                "AND event_date >= date('now') "
                "ORDER BY event_date ASC LIMIT 1",
                (case_number,),
            )
            if hearing_rows:
                return dict(hearing_rows[0]).get("event_date")
        return None

    # -- Document generators -------------------------------------------------

    def generate_interrogatories(
        self,
        case_number: str,
        topics: list[str] | None = None,
        max_count: int = 25,
        lane: str = "A",
    ) -> str:
        """Generate interrogatories under MCR 2.309(A)(2).

        Args:
            case_number: Case file number (e.g. ``2024-001507-DC``).
            topics: Topic keys from ``DISCOVERY_TOPICS`` to include.
                    Defaults to ``["custody", "financial", "interference"]``.
            max_count: Maximum number of interrogatories (Michigan cap is 25).
            lane: Case lane letter for DB lookups.

        Returns:
            Markdown document string.
        """
        if max_count > 25:
            logger.warning("MCR 2.309(A)(2) limits interrogatories to 25; capping")
            max_count = 25

        resolved_case = case_number or CASE_NUMBERS.get(lane, "")
        topics = topics or ["custody", "financial", "interference"]

        doc = _caption(resolved_case, "Plaintiff's First Set of Interrogatories")

        # Definitions
        doc += dedent("""\
            ## DEFINITIONS

            1. **"YOU"** or **"YOUR"** refers to Defendant, Emily A. Watson.
            2. **"DOCUMENT"** means any writing, recording, or electronically stored
               information as defined by MCR 2.310(B).
            3. **"COMMUNICATION"** includes oral, written, and electronic exchanges.
            4. **"THE CHILD"** refers to the minor child, L.D.W.
            5. **"INCIDENT"** means any event, occurrence, or circumstance relevant
               to the claims in this case.
            6. **"IDENTIFY"** means to state the full name, address, telephone number,
               and relationship to any party of each person.
            7. **"DESCRIBE"** means to provide a complete and detailed account.

        """)

        # Instructions
        doc += dedent(f"""\
            ## INSTRUCTIONS

            Pursuant to MCR 2.309, you are required to answer each interrogatory
            separately and fully, in writing, under oath, within twenty-eight (28)
            days of service — on or before **{_deadline_date(28)}**.

            If you object to any interrogatory, state the grounds for objection
            with specificity.  If you claim privilege, identify the privilege and
            the nature of the information withheld.

        """)

        # Build interrogatories from topics and DB data
        interrogatories: list[str] = []

        # Pull claim-based interrogatories
        claims = self._get_claims(resolved_case)
        for claim in claims:
            claim_type = dict(claim).get("claim_type", "")
            desc = dict(claim).get("description", claim_type)
            if desc and len(interrogatories) < max_count:
                interrogatories.append(
                    f"Describe in detail all facts known to you regarding: {desc}."
                )

        # Pull evidence-gap-based interrogatories
        gaps = self._get_evidence_gaps(lane)
        for gap in gaps:
            gap_desc = dict(gap).get("description", dict(gap).get("gap_type", ""))
            if gap_desc and len(interrogatories) < max_count:
                interrogatories.append(
                    f"Identify all documents and witnesses with knowledge of: {gap_desc}."
                )

        # Fill remaining slots from topic templates
        for topic_key in topics:
            topic_items = DISCOVERY_TOPICS.get(topic_key, [])
            for item in topic_items:
                if len(interrogatories) >= max_count:
                    break
                interrogatories.append(
                    f"Describe fully and identify all documents related to: {item}."
                )

        # Deduplicate while preserving order
        seen: set[str] = set()
        unique: list[str] = []
        for q in interrogatories:
            if q not in seen:
                seen.add(q)
                unique.append(q)
        interrogatories = unique[:max_count]

        doc += "## INTERROGATORIES\n\n"
        for idx, question in enumerate(interrogatories, 1):
            doc += f"**Interrogatory No. {idx}:** {question}\n\n"

        doc += _certificate_of_service(resolved_case)
        return doc

    def generate_rfp(
        self,
        case_number: str,
        categories: list[str] | None = None,
        lane: str = "A",
    ) -> str:
        """Generate Requests for Production under MCR 2.310.

        Args:
            case_number: Case file number.
            categories: Category keys from ``DISCOVERY_TOPICS``.
                        Defaults to all categories.
            lane: Case lane letter.

        Returns:
            Markdown document string.
        """
        resolved_case = case_number or CASE_NUMBERS.get(lane, "")
        categories = categories or list(DISCOVERY_TOPICS.keys())

        doc = _caption(
            resolved_case,
            "Plaintiff's First Request for Production of Documents",
        )

        doc += dedent("""\
            ## DEFINITIONS

            1. **"DOCUMENT"** includes all writings, drawings, graphs, charts,
               photographs, recordings, electronically stored information (ESI),
               and any other data compilations as defined by MCR 2.310(B) and
               MRE 1001.
            2. **"COMMUNICATION"** includes all oral, written, and electronic
               exchanges of information.
            3. **"YOU"** or **"YOUR"** refers to Defendant, Emily A. Watson,
               including agents, employees, and attorneys acting on your behalf.
            4. **"THE CHILD"** refers to the minor child, L.D.W.

        """)

        doc += dedent(f"""\
            ## INSTRUCTIONS

            Pursuant to MCR 2.310, you are requested to produce or make available
            for inspection and copying the following documents within thirty (30)
            days of service — on or before **{_deadline_date(30)}**.

            **Time Period:** Unless otherwise specified, each request covers the
            period from January 1, 2022, to the present date.

            **Production Format:** Documents may be produced in their native
            electronic format or as legible paper copies.  If privilege is
            claimed, provide a privilege log per MCR 2.302(C).

        """)

        doc += "## REQUESTS FOR PRODUCTION\n\n"

        request_num = 0
        category_labels: dict[str, str] = {
            "custody": "Custody & Parenting",
            "financial": "Financial Records",
            "communications": "Communications",
            "interference": "Parenting Time Interference",
            "domestic_violence": "Domestic Violence & Safety",
            "housing": "Housing & Living Conditions",
            "employment": "Employment & Income",
            "third_party": "Third-Party Involvement",
        }

        for cat in categories:
            items = DISCOVERY_TOPICS.get(cat, [])
            if not items:
                continue
            label = category_labels.get(cat, cat.replace("_", " ").title())
            doc += f"### Category: {label}\n\n"
            for item in items:
                request_num += 1
                doc += (
                    f"**Request No. {request_num}:** Produce all documents, "
                    f"records, and electronically stored information relating to: "
                    f"{item}.\n\n"
                )

        doc += _certificate_of_service(resolved_case)
        return doc

    def generate_rfa(
        self,
        case_number: str,
        facts: list[str] | None = None,
        lane: str = "A",
    ) -> str:
        """Generate Requests for Admission under MCR 2.312.

        Args:
            case_number: Case file number.
            facts: Specific facts to request admission of.
                   If ``None``, auto-generates from DB claims and evidence.
            lane: Case lane letter.

        Returns:
            Markdown document string.
        """
        resolved_case = case_number or CASE_NUMBERS.get(lane, "")

        doc = _caption(resolved_case, "Plaintiff's First Requests for Admission")

        doc += dedent(f"""\
            ## INSTRUCTIONS

            Pursuant to MCR 2.312, Defendant is requested to admit, for purposes
            of this action only, the truth of the following statements within
            twenty-eight (28) days of service — on or before **{_deadline_date(28)}**.

            If you deny a request, state in detail the reasons for the denial.
            If you cannot truthfully admit or deny, state so and explain why.
            Failure to respond within the required time period will result in
            each matter being deemed admitted pursuant to MCR 2.312(B)(1).

        """)

        # Build admission requests
        admissions: list[str] = []

        if facts:
            admissions.extend(facts)
        else:
            # Auto-generate from DB claims
            claims = self._get_claims(resolved_case)
            for claim in claims:
                desc = dict(claim).get("description", "")
                if desc:
                    admissions.append(desc)

            # Standard custody-related admissions
            standard_admissions = [
                (
                    "Admit that Plaintiff, Andrew James Pigors, is a fit and "
                    "proper parent."
                ),
                (
                    "Admit that the minor child, L.D.W., has a bonded and "
                    "loving relationship with Plaintiff."
                ),
                (
                    "Admit that you have, on one or more occasions, denied "
                    "Plaintiff court-ordered parenting time."
                ),
                (
                    "Admit that you have made decisions regarding the child's "
                    "medical care without consulting Plaintiff."
                ),
                (
                    "Admit that you have made disparaging remarks about "
                    "Plaintiff in the presence of the child."
                ),
                (
                    "Admit that Ronald Berry resides at or frequently stays "
                    "at your residence."
                ),
                (
                    "Admit that you have failed to provide Plaintiff with "
                    "the child's school records as required."
                ),
                (
                    "Admit that the child has expressed a desire to spend "
                    "more time with Plaintiff."
                ),
            ]
            admissions.extend(standard_admissions)

        # Deduplicate
        seen: set[str] = set()
        unique_admissions: list[str] = []
        for a in admissions:
            normalized = a.strip().rstrip(".")
            if normalized not in seen:
                seen.add(normalized)
                unique_admissions.append(a)

        doc += "## REQUESTS FOR ADMISSION\n\n"
        doc += "### Part A — Admission of Facts\n\n"

        fact_admissions = [
            a for a in unique_admissions if "document" not in a.lower()
        ]
        doc_admissions = [
            a for a in unique_admissions if "document" in a.lower()
        ]

        num = 0
        for admission in fact_admissions:
            num += 1
            if not admission.lower().startswith("admit"):
                admission = f"Admit that {admission}"
            doc += f"**Request No. {num}:** {admission}\n\n"

        if doc_admissions:
            doc += "### Part B — Genuineness of Documents\n\n"
            for admission in doc_admissions:
                num += 1
                if not admission.lower().startswith("admit"):
                    admission = f"Admit the genuineness of: {admission}"
                doc += f"**Request No. {num}:** {admission}\n\n"

        doc += _certificate_of_service(resolved_case)
        return doc

    def generate_subpoena(
        self,
        recipient: str,
        items: list[str],
        hearing_date: str | None = None,
    ) -> str:
        """Generate a Subpoena Duces Tecum template under MCR 2.506.

        Args:
            recipient: Name or entity to subpoena.
            items: List of documents/records to produce.
            hearing_date: Optional hearing date string.

        Returns:
            Markdown document template string.
        """
        case_number = CASE_NUMBERS.get("A", "")
        hearing_text = hearing_date or self._get_next_hearing(case_number) or "TO BE DETERMINED BY THE COURT"
        production_date = _deadline_date(14)

        doc = _caption(case_number, "Subpoena Duces Tecum")

        doc += dedent(f"""\
            ## TO: {recipient}

            **YOU ARE COMMANDED** to produce and permit inspection and copying
            of the following documents and tangible things at the place, date,
            and time specified below, pursuant to MCR 2.506.

            **Production Date:** {production_date}

            **Production Location:** {PARTIES["court"]}
            990 Terrace St, Muskegon, MI 49442

        """)

        if hearing_date:
            doc += dedent(f"""\
                **Hearing Date:** {hearing_text}

                You are further commanded to appear at the above hearing and
                bring the documents described below.

            """)

        doc += "## DOCUMENTS TO BE PRODUCED\n\n"
        for idx, item in enumerate(items, 1):
            doc += f"{idx}. {item}\n"
        doc += "\n"

        doc += dedent(f"""\
            ## COMPLIANCE NOTICE

            Failure to comply with this subpoena may be deemed contempt of
            court under MCR 2.506(G).

            A reasonable fee for copying and production is tendered herewith
            or will be paid upon request.

            **Issued by:**
            {PARTIES["plaintiff"]["name"]}, Plaintiff (Self-Represented)
            {PARTIES["plaintiff"]["address"]}
            {PARTIES["plaintiff"]["phone"]}

            Date: {_today()}
        """)

        return doc

    def generate_discovery_plan(
        self,
        case_number: str,
        lane: str = "A",
    ) -> dict[str, Any]:
        """Analyze the case and produce a structured discovery plan.

        Args:
            case_number: Case file number.
            lane: Case lane letter.

        Returns:
            Dictionary with ``phases``, ``timeline``, ``document_requests``,
            ``interrogatory_topics``, and ``priority_order``.
        """
        resolved_case = case_number or CASE_NUMBERS.get(lane, "")

        # Gather case intelligence
        claims = self._get_claims(resolved_case)
        gaps = self._get_evidence_gaps(lane)
        deadlines = self._get_deadlines(resolved_case)

        claim_types: list[str] = []
        for c in claims:
            ct = dict(c).get("claim_type", "")
            if ct:
                claim_types.append(ct)

        gap_types: list[str] = []
        for g in gaps:
            gt = dict(g).get("gap_type", dict(g).get("description", ""))
            if gt:
                gap_types.append(gt)

        # Determine priority topics based on claims and gaps
        priority_topics: list[str] = []
        topic_priority_map: dict[str, list[str]] = {
            "custody": ["custody", "parenting", "child", "visitation"],
            "financial": ["income", "support", "financial", "asset"],
            "interference": ["interference", "alienat", "denial", "blocking"],
            "communications": ["communication", "text", "email", "message"],
            "domestic_violence": ["violence", "ppo", "protection", "assault"],
            "housing": ["housing", "residence", "living", "lease"],
            "employment": ["employ", "work", "income", "job"],
            "third_party": ["berry", "third", "partner", "boyfriend"],
        }

        all_signals = " ".join(claim_types + gap_types).lower()
        for topic, keywords in topic_priority_map.items():
            if any(kw in all_signals for kw in keywords):
                priority_topics.append(topic)

        # Default priorities when DB yields nothing
        if not priority_topics:
            priority_topics = ["custody", "financial", "interference"]

        # Build phased plan
        today = datetime.now()
        phases: list[dict[str, Any]] = [
            {
                "phase": 1,
                "name": "Initial Written Discovery",
                "deadline": (today + timedelta(days=7)).strftime("%Y-%m-%d"),
                "actions": [
                    "Serve First Set of Interrogatories (MCR 2.309)",
                    "Serve First Request for Production (MCR 2.310)",
                    "Serve First Requests for Admission (MCR 2.312)",
                ],
                "topics": priority_topics[:3],
            },
            {
                "phase": 2,
                "name": "Third-Party Discovery",
                "deadline": (today + timedelta(days=21)).strftime("%Y-%m-%d"),
                "actions": [
                    "Subpoena school records for L.D.W.",
                    "Subpoena medical records for L.D.W.",
                    "Subpoena phone records if relevant",
                ],
                "topics": ["third_party", "communications"],
            },
            {
                "phase": 3,
                "name": "Follow-Up Discovery",
                "deadline": (today + timedelta(days=42)).strftime("%Y-%m-%d"),
                "actions": [
                    "Supplemental interrogatories based on responses",
                    "Motion to compel if discovery responses inadequate",
                    "Deposition notices if warranted",
                ],
                "topics": priority_topics,
            },
        ]

        # Upcoming deadline context
        timeline: list[dict[str, str]] = []
        for d in deadlines[:5]:
            dd = dict(d)
            timeline.append({
                "event": dd.get("description", dd.get("title", "Unknown")),
                "date": dd.get("due_date_iso", "Unknown"),
                "status": dd.get("status", "pending"),
            })

        return {
            "case_number": resolved_case,
            "lane": lane,
            "generated": today.isoformat(),
            "phases": phases,
            "timeline": timeline,
            "priority_topics": priority_topics,
            "claim_count": len(claims),
            "gap_count": len(gaps),
            "document_requests": [
                f"RFP category: {t}" for t in priority_topics
            ],
            "interrogatory_topics": priority_topics[:3],
        }

    def get_discovery_templates(self) -> list[dict[str, str]]:
        """Return metadata for all available discovery templates.

        Returns:
            List of dicts with ``name``, ``mcr_rule``, and ``description``.
        """
        return [
            {
                "name": "Interrogatories",
                "mcr_rule": "MCR 2.309(A)(2)",
                "description": (
                    "Written questions to the opposing party, limited to 25 "
                    "including subparts. Responses due within 28 days."
                ),
            },
            {
                "name": "Request for Production",
                "mcr_rule": "MCR 2.310",
                "description": (
                    "Requests to produce documents, ESI, and tangible things "
                    "for inspection and copying. Responses due within 30 days."
                ),
            },
            {
                "name": "Request for Admission",
                "mcr_rule": "MCR 2.312",
                "description": (
                    "Requests to admit facts, genuineness of documents, or "
                    "application of law to fact. Deemed admitted if not "
                    "responded to within 28 days."
                ),
            },
            {
                "name": "Subpoena Duces Tecum",
                "mcr_rule": "MCR 2.506",
                "description": (
                    "Court order compelling a non-party to produce documents "
                    "or appear with records at a hearing or deposition."
                ),
            },
            {
                "name": "Discovery Plan",
                "mcr_rule": "MCR 2.301",
                "description": (
                    "Comprehensive phased plan for all discovery activities "
                    "including timelines, topics, and priority order."
                ),
            },
        ]

    def get_rule_context(self, mcr_citation: str) -> str:
        """Return full rule text for an MCR citation from static data.

        Useful for enriching discovery documents with governing rule text.
        Falls back to an empty string if the rule is not found.
        """
        return get_rule_text(mcr_citation)
