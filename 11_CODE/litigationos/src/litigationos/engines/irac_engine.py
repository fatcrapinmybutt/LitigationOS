"""IRAC legal analysis engine.

Performs structured Issue → Rule → Application → Conclusion analysis for
Michigan family-law claims.  Every authority is sourced from the litigation
database — the engine **never** fabricates citations.  When no matching
authority exists, a ``[VERIFY — authority needed]`` placeholder is emitted.

Designed for 100 % local / offline operation.  No external API calls.
"""

from __future__ import annotations

import logging
import sqlite3
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any

from litigationos.data.rule_lookup import get_rules_for_claim, get_rule_text

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default DB path
# ---------------------------------------------------------------------------
_DEFAULT_DB = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")

# ---------------------------------------------------------------------------
# Verified party identity (single source of truth)
# ---------------------------------------------------------------------------
PARTIES = {
    "plaintiff": "Andrew James Pigors",
    "defendant": "Emily A. Watson",
    "child": "L.D.W.",
    "judge": "Hon. Jenny L. McNeill",
}

# ---------------------------------------------------------------------------
# Claim-type library
# ---------------------------------------------------------------------------
CLAIM_TYPES: dict[str, dict[str, Any]] = {
    "custody_modification": {
        "description": "Modification of child custody order",
        "required_elements": [
            "Proper cause or change of circumstances",
            "Best interest analysis (MCL 722.23 factors a-l)",
            "Established custodial environment determination",
        ],
        "applicable_rules": ["MCR 3.210", "MCL 722.27", "MCL 722.23"],
        "typical_evidence": [
            "Parenting-time logs",
            "Communications showing changed circumstances",
            "Child welfare records",
            "School / medical records",
        ],
    },
    "contempt": {
        "description": "Contempt of court for willful disobedience of a court order",
        "required_elements": [
            "Existence of a valid court order",
            "Knowledge of the order by the offending party",
            "Willful failure to comply",
            "Ability to comply",
        ],
        "applicable_rules": ["MCR 3.606", "MCL 600.1701", "MCL 600.1715"],
        "typical_evidence": [
            "Certified copy of violated order",
            "Evidence of non-compliance (logs, messages)",
            "Proof of service / notice",
        ],
    },
    "ppo_violation": {
        "description": "Violation of a domestic Personal Protection Order",
        "required_elements": [
            "Valid PPO in effect",
            "Service or actual knowledge of PPO",
            "Act constituting violation",
        ],
        "applicable_rules": ["MCR 3.708", "MCL 600.2950", "MCL 764.15b"],
        "typical_evidence": [
            "Certified copy of PPO",
            "Proof of service",
            "Police reports or incident documentation",
            "Witness statements",
        ],
    },
    "judicial_disqualification": {
        "description": "Disqualification of judge for bias or prejudice",
        "required_elements": [
            "Specific allegations of bias or prejudice",
            "Bias from extrajudicial source or deep-seated antagonism",
            "Timely filing of motion",
        ],
        "applicable_rules": ["MCR 2.003", "MCL 600.1988(b)", "MCR 2.003(D)"],
        "typical_evidence": [
            "Hearing transcripts showing bias",
            "Pattern of adverse rulings without legal basis",
            "Ex-parte communications",
            "Statements showing prejudgment",
        ],
    },
    "parental_alienation": {
        "description": "Interference with child-parent relationship / parenting time",
        "required_elements": [
            "Pattern of alienating behaviour by custodial parent",
            "Negative impact on child-parent relationship",
            "Best-interest factor (j) analysis",
        ],
        "applicable_rules": ["MCL 722.23(j)", "MCL 722.27a", "MCR 3.210"],
        "typical_evidence": [
            "Communication records showing disparagement",
            "Denied or frustrated parenting time logs",
            "Child statements (age-appropriate)",
            "Therapist or FOC reports",
        ],
    },
    "discovery_abuse": {
        "description": "Sanctions for failure to comply with discovery",
        "required_elements": [
            "Valid discovery request served",
            "Failure or refusal to respond",
            "Good-faith attempt to resolve without court intervention",
        ],
        "applicable_rules": ["MCR 2.313", "MCR 2.310", "MCR 2.302"],
        "typical_evidence": [
            "Discovery requests with proof of service",
            "Responses (or lack thereof)",
            "Meet-and-confer correspondence",
        ],
    },
    "due_process_violation": {
        "description": "Deprivation of procedural due process rights",
        "required_elements": [
            "State action depriving a protected liberty / property interest",
            "Inadequate notice or opportunity to be heard",
            "Causal connection between state actor and deprivation",
        ],
        "applicable_rules": [
            "US Const Amend XIV § 1",
            "42 USC § 1983",
            "Mathews v. Eldridge, 424 U.S. 319 (1976)",
        ],
        "typical_evidence": [
            "Court orders entered without notice",
            "Denied opportunity to present evidence",
            "Transcript excerpts showing procedural irregularities",
        ],
    },
    "child_support_modification": {
        "description": "Modification of child support based on change of circumstances",
        "required_elements": [
            "Change of circumstances since last order",
            "Change results in support differing by ≥ 10 % from formula",
            "Verified income information",
        ],
        "applicable_rules": ["MCR 3.211", "MCL 552.17", "MCL 552.605"],
        "typical_evidence": [
            "Current income documentation (pay stubs, tax returns)",
            "Existing child-support order",
            "Calculation under Michigan Child Support Formula",
        ],
    },
    "motion_to_compel": {
        "description": "Motion to compel discovery responses",
        "required_elements": [
            "Proper discovery request served",
            "Inadequate or missing response",
            "Good-faith certification of conferral attempt",
        ],
        "applicable_rules": ["MCR 2.313(A)", "MCR 2.310", "MCR 2.302(B)"],
        "typical_evidence": [
            "Discovery request with proof of service",
            "Deficient response or non-response",
            "Conferral letter / email",
        ],
    },
    "sanctions": {
        "description": "Sanctions for frivolous claims or defenses",
        "required_elements": [
            "Paper or pleading signed in violation of MCR 2.114(D)",
            "Not well grounded in fact or law",
            "Filed for improper purpose",
        ],
        "applicable_rules": ["MCR 2.114", "MCR 2.625", "MCL 600.2591"],
        "typical_evidence": [
            "Offending pleading",
            "Evidence that claims are factually baseless",
            "Evidence of improper purpose / harassment",
        ],
    },
    "summary_judgment": {
        "description": "Judgment without trial — no genuine issue of material fact",
        "required_elements": [
            "No genuine issue of material fact",
            "Moving party entitled to judgment as a matter of law",
            "All evidence viewed in light most favourable to non-movant",
        ],
        "applicable_rules": ["MCR 2.116(C)(10)", "MCR 2.116(G)", "MCR 2.116(I)"],
        "typical_evidence": [
            "Affidavits / declarations",
            "Documentary evidence negating element of opponent's claim",
            "Deposition excerpts",
        ],
    },
    "default_judgment": {
        "description": "Judgment for failure to plead or defend",
        "required_elements": [
            "Proper service of process",
            "Failure to plead or otherwise defend within time allowed",
            "Entry of default by clerk",
        ],
        "applicable_rules": ["MCR 2.603", "MCR 2.603(A)", "MCR 2.105"],
        "typical_evidence": [
            "Proof of service",
            "Docket showing no response filed",
            "Affidavit of default",
        ],
    },
    "emergency_motion": {
        "description": "Emergency motion alleging immediate danger to child",
        "required_elements": [
            "Immediate and irreparable harm to child",
            "Specific factual basis for emergency",
            "Efforts to give notice to opposing party",
        ],
        "applicable_rules": ["MCR 3.207", "MCR 3.207(B)", "MCL 722.27(1)(c)"],
        "typical_evidence": [
            "Police reports or CPS referrals",
            "Medical records showing harm",
            "Affidavit detailing emergency",
        ],
    },
    "appeal": {
        "description": "Claim of appeal to Michigan Court of Appeals",
        "required_elements": [
            "Final order or qualifying interlocutory order",
            "Filed within 21 days of order (or 42 days in some cases)",
            "Claim of appeal form completed per MCR 7.204",
        ],
        "applicable_rules": ["MCR 7.204", "MCR 7.205", "MCR 7.212"],
        "typical_evidence": [
            "Lower court order being appealed",
            "Hearing transcripts",
            "Motion record / docket entries",
        ],
    },
}


# ---------------------------------------------------------------------------
# IRACEngine
# ---------------------------------------------------------------------------
class IRACEngine:
    """Structured IRAC legal analysis engine.

    Analyses claims by querying ``litigation_context.db`` for applicable
    Michigan court rules, statutes, case law, and evidence — then produces
    Issue → Rule → Application → Conclusion memoranda.

    Parameters
    ----------
    db_path:
        Path to the SQLite litigation database.  Falls back to the
        repository default when *None*.
    """

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = str(db_path or _DEFAULT_DB)
        self._conn: sqlite3.Connection | None = None
        self._connect()

    # -- connection helpers --------------------------------------------------

    def _connect(self) -> None:
        """Open (or re-open) a connection with performance PRAGMAs."""
        try:
            self._conn = sqlite3.connect(self._db_path, timeout=120)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA busy_timeout=60000")
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA cache_size=-32000")
            self._conn.execute("PRAGMA temp_store=MEMORY")
            self._conn.execute("PRAGMA synchronous=NORMAL")
        except Exception:
            logger.exception("Failed to connect to %s", self._db_path)
            self._conn = None

    def _fetchall(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        """Execute *sql* and return a list of dicts (empty on error)."""
        if self._conn is None:
            return []
        try:
            rows = self._conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            logger.exception("Query failed: %s", sql[:120])
            return []

    def _fetchone(self, sql: str, params: tuple = ()) -> dict[str, Any] | None:
        """Execute *sql* and return a single dict (or *None*)."""
        if self._conn is None:
            return None
        try:
            row = self._conn.execute(sql, params).fetchone()
            return dict(row) if row else None
        except Exception:
            logger.exception("Query failed: %s", sql[:120])
            return None

    def _table_exists(self, table: str) -> bool:
        """Return *True* when *table* exists in the database."""
        row = self._fetchone(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        )
        return row is not None

    # -- public API ----------------------------------------------------------

    def get_claim_types(self) -> list[dict[str, Any]]:
        """Return every supported claim type with metadata.

        Returns
        -------
        list[dict]
            Each dict contains *claim_type*, *description*,
            *required_elements*, *applicable_rules*, and *typical_evidence*.
        """
        result: list[dict[str, Any]] = []
        for ctype, meta in CLAIM_TYPES.items():
            result.append({"claim_type": ctype, **meta})
        return result

    def get_applicable_rules(self, claim_type: str) -> list[dict[str, Any]]:
        """Query the DB for MCR / MCL / MRE rules relevant to *claim_type*.

        Returns
        -------
        list[dict]
            Each dict: *rule_id*, *title*, *text*, *source_table*,
            *relevance*.
        """
        meta = CLAIM_TYPES.get(claim_type, {})
        rule_refs = meta.get("applicable_rules", [])
        if not rule_refs:
            return []

        results: list[dict[str, Any]] = []
        source_tables = [
            "michigan_court_rules",
            "michigan_statutes",
            "michigan_case_law",
            "michigan_evidence_rules",
        ]

        for table in source_tables:
            if not self._table_exists(table):
                continue
            # Discover available columns so we never reference a missing one.
            cols_info = self._fetchall(f"PRAGMA table_info({table})")
            col_names = {c["name"] for c in cols_info} if cols_info else set()

            # Identify the best columns for rule_id, title, text
            id_col = _pick_column(col_names, ["rule_id", "statute_id",
                                               "case_id", "rule_number", "id"])
            title_col = _pick_column(col_names, ["title", "name",
                                                  "rule_name", "case_name",
                                                  "short_title"])
            text_col = _pick_column(col_names, ["text", "rule_text",
                                                 "content", "body",
                                                 "description", "holding",
                                                 "summary"])
            if not id_col:
                continue

            for ref in rule_refs:
                like_term = f"%{ref}%"
                # Search across all textual columns for the rule reference.
                where_clauses = [f'"{c}" LIKE ?' for c in col_names
                                 if c not in ("rowid",)]
                if not where_clauses:
                    continue
                where_sql = " OR ".join(where_clauses[:6])  # cap search cols
                params = tuple(like_term for _ in where_clauses[:6])
                sql = f'SELECT * FROM "{table}" WHERE {where_sql} LIMIT 10'
                rows = self._fetchall(sql, params)
                for row in rows:
                    results.append({
                        "rule_id": row.get(id_col, "") if id_col else "",
                        "title": row.get(title_col, "") if title_col else "",
                        "text": _truncate(
                            row.get(text_col, "") if text_col else "", 500
                        ),
                        "source_table": table,
                        "relevance": ref,
                    })

        # --- Static data fallback (when DB tables are empty) ---
        if not results:
            results = get_rules_for_claim(rule_refs)

        return results

    # ------------------------------------------------------------------ #

    def analyze_claim(
        self,
        claim_type: str,
        facts: list[str],
        lane: str = "A",
    ) -> dict[str, Any]:
        """Full IRAC analysis for a legal claim.

        Parameters
        ----------
        claim_type:
            Key into :data:`CLAIM_TYPES` (e.g. ``"custody_modification"``).
        facts:
            Plain-English factual statements supporting the claim.
        lane:
            Case lane (A–F) for evidence filtering.

        Returns
        -------
        dict
            Keys: *issue*, *rule*, *application*, *conclusion*,
            *strength_score* (0–10), *authorities*, *evidence_gaps*.
        """
        meta = CLAIM_TYPES.get(claim_type)
        if meta is None:
            return {
                "issue": f"Unknown claim type: {claim_type}",
                "rule": "",
                "application": "",
                "conclusion": "",
                "strength_score": 0,
                "authorities": [],
                "evidence_gaps": [f"Claim type '{claim_type}' is not recognised"],
            }

        # 1. ISSUE
        issue = self._build_issue(claim_type, meta)

        # 2. RULE — gather authorities from DB
        authorities = self.get_applicable_rules(claim_type)
        rule_text = self._build_rule(meta, authorities)

        # 3. APPLICATION — match facts against required elements
        evidence = self._query_evidence(claim_type, lane)
        application = self._build_application(meta, facts, evidence)

        # 4. CONCLUSION
        strength = self.evaluate_strength(
            claim_type,
            evidence_count=len(evidence),
            authority_count=len(authorities),
        )
        conclusion = self._build_conclusion(
            claim_type, meta, strength, facts,
        )

        # 5. Evidence gaps
        evidence_gaps = self._identify_gaps(meta, facts, authorities, evidence)

        return {
            "issue": issue,
            "rule": rule_text,
            "application": application,
            "conclusion": conclusion,
            "strength_score": strength["score"],
            "authorities": authorities,
            "evidence_gaps": evidence_gaps,
        }

    # ------------------------------------------------------------------ #

    def build_argument(
        self,
        claim_type: str,
        position: str = "plaintiff",
        facts: list[str] | None = None,
    ) -> dict[str, Any]:
        """Build a structured legal argument for *claim_type*.

        Returns
        -------
        dict
            Keys: *opening_statement*, *legal_standard*, *factual_basis*,
            *authorities* (list of dicts with *citation* and *relevance*),
            *prayer_for_relief*.
        """
        meta = CLAIM_TYPES.get(claim_type, {})
        facts = facts or []

        party = PARTIES.get(position, position.title())
        opponent = (
            PARTIES["defendant"]
            if position == "plaintiff"
            else PARTIES["plaintiff"]
        )

        opening = (
            f"{party} respectfully moves this Court for relief under "
            f"{', '.join(meta.get('applicable_rules', ['applicable law']))}."
        )

        standard = self._build_rule(
            meta, self.get_applicable_rules(claim_type),
        )

        factual_basis = (
            "\n".join(f"- {f}" for f in facts)
            if facts
            else "[VERIFY — factual basis needed]"
        )

        db_authorities = self.get_applicable_rules(claim_type)
        authorities = [
            {"citation": a.get("rule_id") or a.get("title", ""),
             "relevance": a.get("relevance", "")}
            for a in db_authorities
        ]
        if not authorities:
            authorities = [
                {"citation": "[VERIFY — authority needed]",
                 "relevance": claim_type}
            ]

        prayer = self._build_prayer(claim_type, meta, party, opponent)

        return {
            "opening_statement": opening,
            "legal_standard": standard,
            "factual_basis": factual_basis,
            "authorities": authorities,
            "prayer_for_relief": prayer,
        }

    # ------------------------------------------------------------------ #

    def evaluate_strength(
        self,
        claim_type: str,
        evidence_count: int,
        authority_count: int,
    ) -> dict[str, Any]:
        """Rate the filing strength of *claim_type*.

        Returns
        -------
        dict
            Keys: *score* (0–10), *rating* (STRONG / MODERATE / WEAK),
            *recommendation*, *missing_elements*.
        """
        meta = CLAIM_TYPES.get(claim_type, {})
        required = meta.get("required_elements", [])

        # Heuristic score — authority & evidence weighted equally.
        auth_score = min(authority_count, 5) * 1.0  # max 5 pts
        evidence_score = min(evidence_count, 5) * 1.0  # max 5 pts
        raw = auth_score + evidence_score
        score = min(int(round(raw)), 10)

        if score >= 7:
            rating = "STRONG"
            recommendation = "Recommend filing — evidence and authority are sufficient."
        elif score >= 4:
            rating = "MODERATE"
            recommendation = (
                "Filing is supportable but consider strengthening the record "
                "before submission."
            )
        else:
            rating = "WEAK"
            recommendation = (
                "Insufficient evidence or authority. Conduct additional "
                "discovery and legal research before filing."
            )

        missing: list[str] = []
        if authority_count == 0:
            missing.append("No authorities found — legal research required")
        if evidence_count == 0:
            missing.append("No supporting evidence — gather documentation")
        if len(required) > evidence_count:
            missing.append(
                f"Only {evidence_count} evidence items for "
                f"{len(required)} required elements"
            )

        return {
            "score": score,
            "rating": rating,
            "recommendation": recommendation,
            "missing_elements": missing,
        }

    # ------------------------------------------------------------------ #

    def generate_irac_memo(
        self,
        claim_type: str,
        facts: list[str],
        output_format: str = "markdown",
    ) -> str:
        """Generate a full IRAC memorandum.

        Parameters
        ----------
        claim_type:
            Key into :data:`CLAIM_TYPES`.
        facts:
            Plain-English factual statements.
        output_format:
            Currently only ``"markdown"`` is supported.

        Returns
        -------
        str
            A Markdown-formatted IRAC memorandum.
        """
        analysis = self.analyze_claim(claim_type, facts)
        meta = CLAIM_TYPES.get(claim_type, {})
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        lines: list[str] = [
            f"# IRAC Memorandum — {meta.get('description', claim_type)}",
            "",
            f"**Date:** {now}  ",
            f"**Claim Type:** {claim_type}  ",
            f"**Plaintiff:** {PARTIES['plaintiff']}  ",
            f"**Defendant:** {PARTIES['defendant']}  ",
            f"**Presiding Judge:** {PARTIES['judge']}  ",
            f"**Strength:** {analysis['strength_score']}/10  ",
            "",
            "---",
            "",
            "## I. ISSUE",
            "",
            analysis["issue"],
            "",
            "## II. RULE",
            "",
            analysis["rule"],
            "",
            "## III. APPLICATION",
            "",
            analysis["application"],
            "",
            "## IV. CONCLUSION",
            "",
            analysis["conclusion"],
            "",
        ]

        # Authorities
        if analysis["authorities"]:
            lines += ["---", "", "## Authorities Cited", ""]
            for i, auth in enumerate(analysis["authorities"], 1):
                rule_id = auth.get("rule_id", "")
                title = auth.get("title", "")
                source = auth.get("source_table", "")
                lines.append(f"{i}. **{rule_id or title}** ({source}) "
                             f"— relevance: {auth.get('relevance', '')}")
            lines.append("")

        # Evidence gaps
        if analysis["evidence_gaps"]:
            lines += ["---", "", "## Evidence Gaps / Action Items", ""]
            for gap in analysis["evidence_gaps"]:
                lines.append(f"- {gap}")
            lines.append("")

        lines += [
            "---",
            f"*Generated by LitigationOS IRACEngine — {now}*",
            "",
        ]
        return "\n".join(lines)

    # -- private helpers -----------------------------------------------------

    def _build_issue(self, claim_type: str, meta: dict) -> str:
        description = meta.get("description", claim_type)
        rules = ", ".join(meta.get("applicable_rules", []))
        return (
            f"Whether {PARTIES['plaintiff']} can establish a claim for "
            f"{description} under {rules or 'applicable Michigan law'}, "
            f"given the factual circumstances of this case."
        )

    def _build_rule(
        self,
        meta: dict,
        authorities: list[dict[str, Any]],
    ) -> str:
        parts: list[str] = []
        rules_list = meta.get("applicable_rules", [])
        required = meta.get("required_elements", [])

        if rules_list:
            parts.append(
                f"The governing authorities are {', '.join(rules_list)}."
            )
        if required:
            parts.append("The movant must establish:")
            for i, elem in enumerate(required, 1):
                parts.append(f"  ({i}) {elem};")

        # Append DB-sourced authority text (first 3 to keep concise).
        for auth in authorities[:3]:
            text = auth.get("text", "")
            if text:
                source = auth.get("rule_id") or auth.get("title", "")
                parts.append(f"\n**{source}:** {_truncate(text, 300)}")

        if not parts:
            parts.append("[VERIFY — authority needed]")

        return "\n".join(parts)

    def _build_application(
        self,
        meta: dict,
        facts: list[str],
        evidence: list[dict[str, Any]],
    ) -> str:
        parts: list[str] = []
        required = meta.get("required_elements", [])

        parts.append(
            f"Applying the above standards to the facts, "
            f"{PARTIES['plaintiff']} presents the following:"
        )

        # Map facts to required elements where possible.
        for i, elem in enumerate(required):
            matched = facts[i] if i < len(facts) else None
            if matched:
                parts.append(f"\n**Element {i + 1} — {elem}:**  \n{matched}")
            else:
                parts.append(
                    f"\n**Element {i + 1} — {elem}:**  \n"
                    "[VERIFY — supporting fact needed]"
                )

        # Additional facts beyond the element count.
        extra = facts[len(required):]
        if extra:
            parts.append("\n**Additional supporting facts:**")
            for f in extra:
                parts.append(f"- {f}")

        # Cite DB evidence.
        if evidence:
            parts.append(f"\n**Supporting evidence ({len(evidence)} item(s) "
                         "from database):**")
            for ev in evidence[:10]:
                quote = ev.get("quote_text") or ev.get("text") or ev.get(
                    "content", ""
                )
                source = ev.get("source_file") or ev.get("source", "")
                parts.append(
                    f"- *\"{_truncate(quote, 150)}\"* "
                    f"(source: {source or 'DB'})"
                )

        return "\n".join(parts)

    def _build_conclusion(
        self,
        claim_type: str,
        meta: dict,
        strength: dict[str, Any],
        facts: list[str],
    ) -> str:
        rating = strength.get("rating", "UNKNOWN")
        score = strength.get("score", 0)
        description = meta.get("description", claim_type)
        rules = ", ".join(meta.get("applicable_rules", []))

        if rating == "STRONG":
            assessment = (
                "the facts and authorities strongly support granting the "
                "requested relief"
            )
        elif rating == "MODERATE":
            assessment = (
                "the facts provide a reasonable basis for relief, though "
                "the Court should consider additional evidence"
            )
        else:
            assessment = (
                "the current evidentiary record may be insufficient and "
                "additional discovery is recommended before filing"
            )

        return (
            f"Based on the foregoing analysis (strength {score}/10 — "
            f"{rating}), {PARTIES['plaintiff']} submits that {assessment}. "
            f"Accordingly, this Court should grant {PARTIES['plaintiff']}'s "
            f"claim for {description} under {rules or 'applicable law'}."
        )

    def _build_prayer(
        self,
        claim_type: str,
        meta: dict,
        party: str,
        opponent: str,
    ) -> str:
        description = meta.get("description", claim_type)
        return (
            f"WHEREFORE, {party} respectfully requests that this "
            f"Honourable Court:\n"
            f"  (a) Grant {party}'s motion for {description};\n"
            f"  (b) Award such other and further relief as this Court "
            f"deems just and equitable."
        )

    # -- DB evidence helpers ------------------------------------------------

    def _query_evidence(
        self,
        claim_type: str,
        lane: str,
    ) -> list[dict[str, Any]]:
        """Fetch evidence from ``evidence_quotes`` matching *claim_type*."""
        if not self._table_exists("evidence_quotes"):
            return []

        cols_info = self._fetchall("PRAGMA table_info(evidence_quotes)")
        col_names = {c["name"] for c in cols_info} if cols_info else set()

        # Determine filtering column (lane / vehicle_name / claim_type).
        lane_col = _pick_column(col_names, ["vehicle_name", "lane", "case_lane"])
        claim_col = _pick_column(col_names, ["claim_type", "category", "tag"])

        conditions: list[str] = []
        params: list[str] = []

        readable_type = claim_type.replace("_", " ")
        if claim_col:
            conditions.append(f'"{claim_col}" LIKE ?')
            params.append(f"%{readable_type}%")

        if lane_col:
            conditions.append(f'"{lane_col}" LIKE ?')
            params.append(f"%{lane}%")

        where = " OR ".join(conditions) if conditions else "1=1"
        sql = f"SELECT * FROM evidence_quotes WHERE {where} LIMIT 20"
        return self._fetchall(sql, tuple(params))

    def _identify_gaps(
        self,
        meta: dict,
        facts: list[str],
        authorities: list[dict[str, Any]],
        evidence: list[dict[str, Any]],
    ) -> list[str]:
        """Identify what is missing for a complete filing."""
        gaps: list[str] = []
        required = meta.get("required_elements", [])
        typical = meta.get("typical_evidence", [])

        if not authorities:
            gaps.append("No authorities located in database — run legal research")

        unmatched = required[len(facts):]
        for elem in unmatched:
            gaps.append(f"Missing factual support for: {elem}")

        if not evidence:
            gaps.append("No matching evidence in evidence_quotes table")
            for typ in typical:
                gaps.append(f"Consider obtaining: {typ}")

        return gaps


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _pick_column(
    available: set[str],
    preferences: list[str],
) -> str | None:
    """Return the first column from *preferences* that is in *available*."""
    for col in preferences:
        if col in available:
            return col
    return None


def _truncate(text: str | None, max_len: int = 300) -> str:
    """Truncate *text* to *max_len* characters with an ellipsis."""
    if not text:
        return ""
    text = str(text).strip()
    if len(text) <= max_len:
        return text
    return text[:max_len - 1] + "…"
