"""Michigan Court Rules lookup, search, and filing-validation engine.

Provides rule lookup by MCR number, FTS5 full-text search, filing format
validation, and applicable-rule resolution.  Seeds key MCR rules on first
use so the database always contains a working baseline.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from litigationos.db.connection import DatabaseManager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Seed data — key Michigan Court Rules
# ---------------------------------------------------------------------------

_MCR_SEED: list[dict] = [
    {
        "rule_number": "MCR 2.105",
        "title": "Summons; Expiration, Reissuance, or Replacement",
        "full_text": (
            "A summons expires 91 days after the date the complaint is filed. "
            "The court may reissue or replace an expired summons on motion and "
            "payment of the required fee. A reissued or replacement summons "
            "expires 91 days after the date of reissuance or replacement."
        ),
        "category": "service",
        "court_type": "circuit",
        "requirements_json": json.dumps({
            "service_within_days": 91,
            "reissue_allowed": True,
        }),
    },
    {
        "rule_number": "MCR 2.107",
        "title": "Service and Filing of Pleadings and Other Papers",
        "full_text": (
            "Every pleading subsequent to the original complaint, every written "
            "motion, and every paper required or permitted to be filed and not "
            "required to be served by statute or court rule must be served on "
            "each party. Service must be made by delivery or by mailing a copy "
            "to the party's last known address."
        ),
        "category": "service",
        "court_type": "circuit",
        "requirements_json": json.dumps({
            "serve_on_all_parties": True,
            "methods": ["delivery", "mail", "electronic"],
        }),
    },
    {
        "rule_number": "MCR 2.108",
        "title": "Time to Answer or Otherwise Respond",
        "full_text": (
            "A defendant must serve and file an answer or take other action "
            "permitted by law or these rules within 21 days after being served "
            "with the summons and a copy of the complaint, unless a different "
            "time is prescribed by statute or court rule."
        ),
        "category": "response",
        "court_type": "circuit",
        "requirements_json": json.dumps({
            "answer_days": 21,
            "trigger": "service_of_complaint",
        }),
    },
    {
        "rule_number": "MCR 2.119",
        "title": "Motion Practice",
        "full_text": (
            "Unless a different period is set by these rules or by the court, "
            "a written motion (other than one that may be heard ex parte), "
            "notice of hearing on the motion, and any supporting brief or "
            "affidavits must be served on the opposing party at least 9 days "
            "before the hearing. A response to the motion and any supporting "
            "brief or affidavits must be served at least 5 days before the "
            "hearing. The moving party may serve a reply brief at least 3 "
            "days before the hearing."
        ),
        "category": "motion",
        "court_type": "circuit",
        "requirements_json": json.dumps({
            "motion_service_days_before_hearing": 9,
            "response_days_before_hearing": 5,
            "reply_days_before_hearing": 3,
            "brief_required": True,
        }),
    },
    {
        "rule_number": "MCR 3.206",
        "title": "Initiating a Domestic Relations Action",
        "full_text": (
            "An action for divorce, separate maintenance, annulment, or "
            "affirmation of marriage is commenced by filing a complaint and "
            "a verified statement. A summons and a copy of the complaint and "
            "verified statement must be served on the defendant as provided "
            "in MCR 2.105. There is a statutory waiting period of 60 days "
            "(or 6 months if minor children are involved) before a judgment "
            "of divorce may be entered."
        ),
        "category": "family",
        "court_type": "circuit",
        "requirements_json": json.dumps({
            "verified_statement_required": True,
            "waiting_period_no_children_days": 60,
            "waiting_period_with_children_days": 180,
        }),
    },
    {
        "rule_number": "MCR 7.212",
        "title": "Briefs in Court of Appeals",
        "full_text": (
            "Within 56 days after the claim of appeal is filed or the order "
            "granting leave to appeal is certified, the appellant must file a "
            "brief conforming to MCR 7.212(B)-(D). The appellee's brief is "
            "due within 35 days after service of the appellant's brief. An "
            "appellant's reply brief, if any, must be filed within 21 days "
            "after service of the appellee's brief."
        ),
        "category": "appeal",
        "court_type": "coa",
        "requirements_json": json.dumps({
            "appellant_brief_days": 56,
            "appellee_brief_days": 35,
            "reply_brief_days": 21,
            "trigger": "claim_of_appeal_filed",
            "format": {
                "font": "Times New Roman 12pt or similar proportional",
                "margins": "1 inch all sides",
                "spacing": "double",
                "page_limit": 50,
            },
        }),
    },
    {
        "rule_number": "MCR 7.301",
        "title": "Organization of the Supreme Court",
        "full_text": (
            "The Supreme Court consists of seven justices elected at "
            "nonpartisan general elections. The justice with the longest "
            "continuous service is the Chief Justice. The Supreme Court has "
            "superintending control over all state courts as provided in the "
            "Michigan Constitution."
        ),
        "category": "appeal",
        "court_type": "supreme",
        "requirements_json": json.dumps({}),
    },
    {
        "rule_number": "MCR 7.302",
        "title": "Application for Leave to Appeal to Supreme Court",
        "full_text": (
            "An application for leave to appeal to the Supreme Court from a "
            "decision of the Court of Appeals must be filed within 42 days "
            "after the date of the Court of Appeals decision or order. The "
            "application must include the questions presented, a concise "
            "statement of facts, and argument in support of granting leave."
        ),
        "category": "appeal",
        "court_type": "supreme",
        "requirements_json": json.dumps({
            "application_days": 42,
            "trigger": "coa_decision",
        }),
    },
    {
        "rule_number": "MCR 7.303",
        "title": "Cross-Applications for Leave to Appeal",
        "full_text": (
            "A cross-application for leave to appeal must be filed within "
            "21 days after the application for leave to appeal is served on "
            "the cross-applicant. The cross-application must conform to the "
            "requirements of MCR 7.302."
        ),
        "category": "appeal",
        "court_type": "supreme",
        "requirements_json": json.dumps({
            "cross_application_days": 21,
            "trigger": "application_served",
        }),
    },
    {
        "rule_number": "MCR 7.304",
        "title": "Responses and Replies; Supreme Court Applications",
        "full_text": (
            "A response to an application for leave to appeal must be filed "
            "within 28 days after the application is served. A reply to a "
            "response may be filed within 14 days after the response is served."
        ),
        "category": "appeal",
        "court_type": "supreme",
        "requirements_json": json.dumps({
            "response_days": 28,
            "reply_days": 14,
        }),
    },
    {
        "rule_number": "MCR 7.305",
        "title": "Application for Leave to Appeal; Bypass",
        "full_text": (
            "Before decision by the Court of Appeals, a party may apply for "
            "leave to appeal directly to the Supreme Court. An application "
            "must be filed within 56 days of the order or judgment being "
            "appealed unless a different time is specified. The application "
            "must demonstrate that the issue involves a significant public "
            "question or that delay would cause material injustice."
        ),
        "category": "appeal",
        "court_type": "supreme",
        "requirements_json": json.dumps({
            "bypass_application_days": 56,
            "trigger": "order_or_judgment",
            "requires_significant_public_question": True,
        }),
    },
    {
        "rule_number": "MCR 7.306",
        "title": "Original Proceedings in Supreme Court",
        "full_text": (
            "The Supreme Court may entertain an original action in mandamus, "
            "habeas corpus, or superintending control, or may issue other "
            "extraordinary writs. A complaint initiating an original action "
            "must be filed with the clerk and comply with the formatting "
            "requirements of MCR 7.212(B)."
        ),
        "category": "appeal",
        "court_type": "supreme",
        "requirements_json": json.dumps({
            "original_actions": [
                "mandamus",
                "habeas_corpus",
                "superintending_control",
            ],
            "format_rule": "MCR 7.212(B)",
        }),
    },
    {
        "rule_number": "MCR 3.310",
        "title": "Proceedings Affecting Children — Parenting Time",
        "full_text": (
            "Unless otherwise ordered by the court, parenting-time disputes "
            "must first be submitted to the Friend of the Court for "
            "conciliation or mediation. A motion to modify parenting time "
            "must be filed in the circuit court and supported by facts "
            "showing proper cause or a change of circumstances."
        ),
        "category": "family",
        "court_type": "circuit",
        "requirements_json": json.dumps({
            "conciliation_required": True,
            "proper_cause_or_change_required": True,
        }),
    },
]


class CourtRulesEngine:
    """Michigan Court Rules engine — lookup, FTS5 search, and filing validation.

    Attributes:
        _db: The :class:`DatabaseManager` used for all queries.
    """

    def __init__(self, db: "DatabaseManager") -> None:
        self._db = db
        self._ensure_schema()
        self._seed_rules()

    # ------------------------------------------------------------------
    # Schema bootstrapping
    # ------------------------------------------------------------------

    def _ensure_schema(self) -> None:
        """Add ``court_type`` and ``requirements_json`` columns if missing."""
        conn = self._db.connect()
        try:
            cols = {
                row["name"]
                for row in conn.execute("PRAGMA table_info(court_rules)").fetchall()
            }
            if "court_type" not in cols:
                conn.execute(
                    "ALTER TABLE court_rules ADD COLUMN court_type TEXT"
                )
            if "requirements_json" not in cols:
                conn.execute(
                    "ALTER TABLE court_rules ADD COLUMN requirements_json TEXT"
                )
            conn.commit()
        finally:
            conn.close()

    def _seed_rules(self) -> None:
        """Insert baseline MCR rules if the table is empty for MI."""
        existing = self._db.fetchone(
            "SELECT COUNT(*) AS cnt FROM court_rules WHERE jurisdiction_id = 'MI'",
        )
        if existing and existing["cnt"] > 0:
            return

        conn = self._db.connect()
        try:
            for rule in _MCR_SEED:
                conn.execute(
                    "INSERT INTO court_rules "
                    "(jurisdiction_id, rule_number, title, full_text, category, "
                    " court_type, requirements_json) "
                    "VALUES ('MI', :rule_number, :title, :full_text, :category, "
                    " :court_type, :requirements_json)",
                    rule,
                )
            conn.commit()
            logger.info("Seeded %d Michigan Court Rules.", len(_MCR_SEED))
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_rule(
        self, rule_number: str, jurisdiction_id: str = "MI"
    ) -> Optional[dict]:
        """Retrieve a single court rule by its MCR number.

        Args:
            rule_number: The MCR rule identifier (e.g. ``"MCR 2.119"``).
            jurisdiction_id: Jurisdiction code (default ``"MI"``).

        Returns:
            A dict of the rule row, or ``None`` if not found.
        """
        row = self._db.fetchone(
            "SELECT * FROM court_rules "
            "WHERE rule_number = ? AND jurisdiction_id = ?",
            (rule_number, jurisdiction_id),
        )
        if row is None:
            return None
        result = dict(row)
        if result.get("requirements_json"):
            try:
                result["requirements"] = json.loads(result["requirements_json"])
            except json.JSONDecodeError:
                result["requirements"] = {}
        return result

    def search_rules(
        self,
        query: str,
        jurisdiction_id: str = "MI",
        category: Optional[str] = None,
    ) -> list[dict]:
        """Full-text search across the ``court_rules_fts`` FTS5 index.

        Args:
            query: FTS5 search expression (e.g. ``"motion hearing"``).
            jurisdiction_id: Limit results to this jurisdiction.
            category: Optional category filter applied post-search.

        Returns:
            List of matching rule dicts ordered by FTS5 rank.
        """
        try:
            rows = self._db.fetchall(
                "SELECT cr.* FROM court_rules_fts fts "
                "JOIN court_rules cr ON fts.rowid = cr.id "
                "WHERE court_rules_fts MATCH ? AND cr.jurisdiction_id = ? "
                "ORDER BY fts.rank",
                (query, jurisdiction_id),
            )
        except Exception:
            logger.exception("FTS5 search failed for query: %s", query)
            return []

        results = [dict(r) for r in rows]
        if category:
            results = [r for r in results if r.get("category") == category]
        return results

    def validate_filing_format(
        self, filing: dict, rule_number: str
    ) -> dict:
        """Check a filing dict against MCR format requirements.

        Args:
            filing: Dict with filing metadata (keys vary by filing type).
                    Expected keys may include ``word_count``, ``font``,
                    ``margins``, ``spacing``, ``page_count``, etc.
            rule_number: The MCR rule to validate against.

        Returns:
            ``{"valid": bool, "score": float, "errors": [], "warnings": []}``
        """
        rule = self.get_rule(rule_number)
        errors: list[str] = []
        warnings: list[str] = []

        if rule is None:
            return {
                "valid": False,
                "score": 0.0,
                "errors": [f"Rule {rule_number} not found in database."],
                "warnings": [],
            }

        reqs = rule.get("requirements", {})
        fmt = reqs.get("format", {})

        # --- Word / page limit checks ---
        page_limit = fmt.get("page_limit")
        if page_limit and filing.get("page_count"):
            if filing["page_count"] > page_limit:
                errors.append(
                    f"Page count {filing['page_count']} exceeds limit of "
                    f"{page_limit} per {rule_number}."
                )

        # --- Font check ---
        required_font = fmt.get("font")
        if required_font and filing.get("font"):
            if required_font.lower() not in filing["font"].lower():
                warnings.append(
                    f"Font '{filing['font']}' may not comply with "
                    f"{rule_number} requirement: {required_font}."
                )

        # --- Margin check ---
        required_margins = fmt.get("margins")
        if required_margins and filing.get("margins"):
            if filing["margins"] != required_margins:
                warnings.append(
                    f"Margins '{filing['margins']}' may not match "
                    f"required '{required_margins}'."
                )

        # --- Spacing check ---
        required_spacing = fmt.get("spacing")
        if required_spacing and filing.get("spacing"):
            if filing["spacing"].lower() != required_spacing.lower():
                errors.append(
                    f"Spacing '{filing['spacing']}' does not match "
                    f"required '{required_spacing}'."
                )

        # --- Service-related checks ---
        if reqs.get("serve_on_all_parties") and not filing.get("served_all"):
            warnings.append(
                f"{rule_number} requires service on all parties."
            )

        if reqs.get("brief_required") and not filing.get("brief_attached"):
            errors.append(
                f"{rule_number} requires a supporting brief or affidavit."
            )

        if reqs.get("verified_statement_required") and not filing.get(
            "verified_statement"
        ):
            errors.append(
                f"{rule_number} requires a verified statement."
            )

        total_checks = max(len(errors) + len(warnings) + 3, 1)
        passed = total_checks - len(errors) - (len(warnings) * 0.5)
        score = round(max(passed / total_checks, 0.0), 2)

        return {
            "valid": len(errors) == 0,
            "score": score,
            "errors": errors,
            "warnings": warnings,
        }

    def get_applicable_rules(
        self,
        filing_type: str,
        court_type: str = "circuit",
        jurisdiction_id: str = "MI",
    ) -> list[dict]:
        """Return all rules relevant to a given filing type and court.

        The mapping uses category tags aligned to filing types:
          - complaint / response → service, response
          - motion / reply        → motion
          - brief                 → appeal
          - family filings        → family

        Args:
            filing_type: e.g. ``"complaint"``, ``"motion"``, ``"brief"``.
            court_type: e.g. ``"circuit"``, ``"coa"``, ``"supreme"``.
            jurisdiction_id: Jurisdiction code.

        Returns:
            List of matching rule dicts.
        """
        category_map: dict[str, list[str]] = {
            "complaint": ["service", "response"],
            "response": ["response", "service"],
            "motion": ["motion"],
            "reply": ["motion"],
            "brief": ["appeal"],
            "notice": ["service"],
            "order": ["motion"],
            "divorce": ["family", "service"],
            "custody": ["family"],
        }
        categories = category_map.get(filing_type, [])
        if not categories:
            logger.warning("No category mapping for filing_type=%s", filing_type)
            return []

        placeholders = ",".join("?" for _ in categories)
        sql = (
            "SELECT * FROM court_rules "
            f"WHERE jurisdiction_id = ? AND category IN ({placeholders}) "
            "AND (court_type IS NULL OR court_type = ?) "
            "ORDER BY rule_number"
        )
        params = (jurisdiction_id, *categories, court_type)
        rows = self._db.fetchall(sql, params)
        return [dict(r) for r in rows]

    def get_rules_by_category(
        self, category: str, jurisdiction_id: str = "MI"
    ) -> list[dict]:
        """Get all rules in a category for a jurisdiction."""
        rows = self._db.fetchall(
            "SELECT * FROM court_rules WHERE category = ? AND jurisdiction_id = ?",
            (category, jurisdiction_id),
        )
        return [dict(r) for r in rows]
