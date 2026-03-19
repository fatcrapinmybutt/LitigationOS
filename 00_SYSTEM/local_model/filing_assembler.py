#!/usr/bin/env python3
"""
MBP LitigationOS — MCR-Compliant Filing Package Assembler
==========================================================
Generates court-ready filing packages for Pigors v. Watson litigation.
All documents comply with MCR 2.113 formatting, MCR 2.107 service
requirements, and Michigan citation standards.

Case:   Andrew Pigors v. Tiffany Watson (fka Pigors)
Courts: 14th Circuit (Muskegon), Michigan COA (366810)
System: THE MANBEARPIG Litigation AI
"""

from __future__ import annotations

import json
import re
import sqlite3
import textwrap
from collections import OrderedDict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# ── Case Constants ────────────────────────────────────────────────────────────

PLAINTIFF = "ANDREW PIGORS"
PLAINTIFF_FULL = "Andrew Pigors"
DEFENDANT = "TIFFANY WATSON"
DEFENDANT_FULL = "Tiffany Watson (fka Pigors)"
JUDGE = "Hon. Jenny L. McNeill"

CASE_NUMBERS: Dict[str, str] = {
    "custody": "2024-001507-DC",
    "ppo": "2023-5907-PP",
    "appeal": "COA 366810",
}

COURTS: Dict[str, str] = {
    "custody": "14TH JUDICIAL CIRCUIT COURT",
    "ppo": "14TH JUDICIAL CIRCUIT COURT",
    "appeal": "COURT OF APPEALS",
}

COUNTY = "MUSKEGON"

# Filing type templates with governing authority
FILING_TEMPLATES: Dict[str, Dict[str, str]] = {
    "motion_to_compel": {
        "title": "Motion to Compel Discovery",
        "authority": "MCR 2.313",
        "type": "motion",
    },
    "motion_summary_disposition": {
        "title": "Motion for Summary Disposition",
        "authority": "MCR 2.116",
        "type": "motion",
    },
    "motion_disqualification": {
        "title": "Motion for Disqualification",
        "authority": "MCR 2.003",
        "type": "motion",
    },
    "motion_reconsideration": {
        "title": "Motion for Reconsideration",
        "authority": "MCR 2.119(F)",
        "type": "motion",
    },
    "response_to_motion": {
        "title": "Response to Motion",
        "authority": "MCR 2.119",
        "type": "response",
    },
    "appellate_brief": {
        "title": "Appellate Brief",
        "authority": "MCR 7.212",
        "type": "brief",
    },
    "application_leave_appeal": {
        "title": "Application for Leave to Appeal",
        "authority": "MCR 7.205",
        "type": "brief",
    },
    "complaint_superintending_control": {
        "title": "Complaint for Superintending Control",
        "authority": "MCR 3.302",
        "type": "motion",
    },
}


# ── Filing Assembler ──────────────────────────────────────────────────────────

class FilingAssembler:
    """MCR-compliant filing package assembler backed by litigation_context.db."""

    # Retry constants for self-healing DB connections
    _MAX_RETRIES = 3
    _BACKOFF_SECONDS = [1, 2, 4]

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._error_log: List[Dict[str, Any]] = []
        self._connect()

    # ── DB Connection (self-healing) ──────────────────────────────────────

    def _connect(self) -> None:
        """Establish DB connection with retry logic."""
        for attempt in range(self._MAX_RETRIES):
            try:
                self._conn = sqlite3.connect(self.db_path)
                self._conn.row_factory = sqlite3.Row
                return
            except sqlite3.Error as exc:
                self._log_error("db_connect", str(exc), attempt=attempt)
                if attempt < self._MAX_RETRIES - 1:
                    import time
                    time.sleep(self._BACKOFF_SECONDS[attempt])
        self._conn = None

    def _execute(
        self,
        query: str,
        params: Tuple = (),
        fallback: Optional[str] = None,
    ) -> List[sqlite3.Row]:
        """Execute a parameterised query with retry and fallback."""
        if self._conn is None:
            self._connect()
        for attempt in range(2):
            try:
                if self._conn is None:
                    raise sqlite3.Error("No database connection")
                cur = self._conn.cursor()
                cur.execute(query, params)
                return cur.fetchall()
            except sqlite3.Error as exc:
                self._log_error("db_execute", str(exc), query=query)
                if attempt == 0 and fallback:
                    query = fallback
                    continue
                if attempt == 0:
                    self._connect()
                    continue
        return []

    def _log_error(self, category: str, message: str, **extra: Any) -> None:
        entry = {
            "ts": datetime.now().isoformat(),
            "category": category,
            "message": message,
            **extra,
        }
        self._error_log.append(entry)

    def close(self) -> None:
        if self._conn:
            try:
                self._conn.close()
            except sqlite3.Error:
                pass
            self._conn = None

    # ── Authority / Evidence Queries ──────────────────────────────────────

    def _fetch_authority(self, rule_number: str) -> Optional[Dict[str, str]]:
        """Retrieve a court rule by rule_number from auth_rules."""
        rows = self._execute(
            "SELECT rule_number, title, full_text, rule_type "
            "FROM auth_rules WHERE rule_number = ?",
            (rule_number,),
        )
        if rows:
            r = rows[0]
            return {
                "rule_number": r["rule_number"],
                "title": r["title"],
                "full_text": r["full_text"] or "",
                "rule_type": r["rule_type"] or "",
            }
        # Fallback: prefix match
        rows = self._execute(
            "SELECT rule_number, title, full_text, rule_type "
            "FROM auth_rules WHERE rule_number LIKE ? LIMIT 5",
            (rule_number + "%",),
        )
        if rows:
            r = rows[0]
            return {
                "rule_number": r["rule_number"],
                "title": r["title"],
                "full_text": r["full_text"] or "",
                "rule_type": r["rule_type"] or "",
            }
        return None

    def _search_authority(self, topic: str, limit: int = 5) -> List[Dict[str, str]]:
        """FTS search across auth_rules for a topic."""
        results: List[Dict[str, str]] = []
        rows = self._execute(
            "SELECT rule_number, title, full_text FROM auth_rules_fts "
            "WHERE auth_rules_fts MATCH ? LIMIT ?",
            (topic, limit),
            fallback=(
                "SELECT rule_number, title, full_text FROM auth_rules "
                "WHERE full_text LIKE ? LIMIT ?"
            ),
        )
        # Fallback params differ; handle gracefully
        if not rows:
            rows = self._execute(
                "SELECT rule_number, title, full_text FROM auth_rules "
                "WHERE full_text LIKE ? OR title LIKE ? LIMIT ?",
                (f"%{topic}%", f"%{topic}%", limit),
            )
        for r in rows:
            results.append({
                "rule_number": r["rule_number"] if r["rule_number"] else "",
                "title": r["title"] if r["title"] else "",
                "full_text": r["full_text"] if r["full_text"] else "",
            })
        return results

    def _fetch_evidence(self, evidence_ids: List[int]) -> List[Dict[str, Any]]:
        """Retrieve evidence quotes by ID list."""
        if not evidence_ids:
            return []
        placeholders = ",".join("?" for _ in evidence_ids)
        rows = self._execute(
            f"SELECT id, quote_text, speaker, legal_significance, "
            f"evidence_category, date_ref FROM evidence_quotes "
            f"WHERE id IN ({placeholders})",
            tuple(evidence_ids),
        )
        return [dict(r) for r in rows]

    def _fetch_citations(
        self, authority_ids: Optional[List[str]] = None, topic: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Retrieve citations from master_citations by cite_type or topic."""
        if authority_ids:
            placeholders = ",".join("?" for _ in authority_ids)
            rows = self._execute(
                f"SELECT citation, cite_type, context FROM master_citations "
                f"WHERE citation IN ({placeholders})",
                tuple(authority_ids),
            )
        elif topic:
            rows = self._execute(
                "SELECT citation, cite_type, context FROM master_citations "
                "WHERE context LIKE ? LIMIT 10",
                (f"%{topic}%",),
            )
        else:
            return []
        return [dict(r) for r in rows]

    def _fetch_claims(self, issue_keywords: List[str]) -> List[Dict[str, str]]:
        """Retrieve claims matching issue keywords."""
        conditions = " OR ".join(["proposition LIKE ?"] * len(issue_keywords))
        params = tuple(f"%{kw}%" for kw in issue_keywords)
        rows = self._execute(
            f"SELECT claim_id, classification, actor, proposition, status "
            f"FROM claims WHERE {conditions} LIMIT 20",
            params,
        )
        return [dict(r) for r in rows]

    # ── Caption Generation (MCR 2.113) ────────────────────────────────────

    def generate_caption(
        self,
        case_number: str,
        case_type: str = "custody",
        document_title: str = "",
    ) -> str:
        """
        Generate an MCR 2.113 compliant case caption.

        Parameters
        ----------
        case_number : str
            Case number (e.g. "2024-001507-DC").
        case_type : str
            One of "custody", "ppo", "appeal".
        document_title : str
            Document title line (e.g. "PLAINTIFF'S MOTION TO COMPEL").
        """
        court_name = COURTS.get(case_type, COURTS["custody"])
        is_appellate = case_type == "appeal"

        if is_appellate:
            lower_case_no = CASE_NUMBERS.get("custody", "")
            caption = (
                f"STATE OF MICHIGAN\n"
                f"IN THE {court_name}\n"
                f"\n"
                f"{PLAINTIFF},{'':>30}COA Case No. {case_number}\n"
                f"        Plaintiff-Appellant,{'':>10}Lower Court Case No. {lower_case_no}\n"
                f"\n"
                f"    v.{'':>36}{JUDGE}\n"
                f"\n"
                f"{DEFENDANT},\n"
                f"        Defendant-Appellee.\n"
                f"{'_' * 50}/\n"
            )
        else:
            county_line = f"FOR THE COUNTY OF {COUNTY}"
            caption = (
                f"STATE OF MICHIGAN\n"
                f"IN THE {court_name}\n"
                f"{county_line}\n"
                f"\n"
                f"{PLAINTIFF},{'':>30}Case No. {case_number}\n"
                f"        Plaintiff,\n"
                f"{'':>40}{JUDGE}\n"
                f"    v.\n"
                f"\n"
                f"{DEFENDANT},\n"
                f"        Defendant.\n"
                f"{'_' * 50}/\n"
            )

        if document_title:
            caption += f"\n{document_title}\n"

        return caption

    # ── IRAC Section ──────────────────────────────────────────────────────

    def generate_irac_section(
        self,
        issue: str,
        rule_citations: List[str],
        facts: List[str],
        conclusion: str,
    ) -> str:
        """
        Generate a single IRAC argument section.

        Parameters
        ----------
        issue : str
            Precise legal question.
        rule_citations : list[str]
            Governing rules/statutes (e.g. ["MCR 2.313(A)", "MCL 722.23"]).
        facts : list[str]
            Case-specific facts to apply.
        conclusion : str
            Legal conclusion and relief sought.
        """
        # Attempt to look up each citation in the DB for full text
        rule_texts: List[str] = []
        for cite in rule_citations:
            auth = self._fetch_authority(cite)
            if auth and auth["full_text"]:
                excerpt = auth["full_text"][:500]
                rule_texts.append(f"    {cite} provides: \"{excerpt}\"")
            else:
                rule_texts.append(f"    {cite}.")

        facts_block = "\n".join(
            f"    {i + 1}. {fact}" for i, fact in enumerate(facts)
        )

        rules_block = "\n\n".join(rule_texts) if rule_texts else "    [Authority to be inserted]"

        section = (
            f"I. ISSUE\n\n"
            f"    {issue}\n\n"
            f"II. RULE\n\n"
            f"{rules_block}\n\n"
            f"III. APPLICATION\n\n"
            f"    Applying the foregoing authority to the facts of this case:\n\n"
            f"{facts_block}\n\n"
            f"IV. CONCLUSION\n\n"
            f"    {conclusion}\n"
        )
        return section

    # ── Certificate of Service (MCR 2.107) ────────────────────────────────

    def generate_certificate_of_service(
        self,
        served_parties: List[str],
        method: str = "email",
        date: Optional[str] = None,
    ) -> str:
        """
        Generate MCR 2.107 compliant certificate of service.

        Parameters
        ----------
        served_parties : list[str]
            Names (and optionally addresses) of served parties.
        method : str
            Service method — "email", "first-class mail", "personal", "efiling".
        date : str or None
            Service date (defaults to today).
        """
        service_date = date or datetime.now().strftime("%B %d, %Y")

        method_map = {
            "email": "electronic mail (email)",
            "first-class mail": "first-class United States mail, postage prepaid",
            "personal": "personal service (hand delivery)",
            "efiling": "electronic filing through the Court's e-Filing system",
        }
        method_text = method_map.get(method, method)

        parties_block = "\n".join(
            f"        {party}" for party in served_parties
        )

        cert = (
            f"\nCERTIFICATE OF SERVICE\n\n"
            f"    I, {PLAINTIFF_FULL}, hereby certify that on {service_date}, "
            f"I served a true\nand correct copy of the foregoing document upon "
            f"the following party(ies) by\n{method_text}:\n\n"
            f"{parties_block}\n\n"
            f"{'_' * 40}\n"
            f"{PLAINTIFF_FULL}, Pro Se Plaintiff\n"
            f"Dated: {service_date}\n"
        )
        return cert

    # ── Signature Block ───────────────────────────────────────────────────

    def generate_signature_block(self) -> str:
        """Generate pro se signature block for Andrew Pigors."""
        today = datetime.now().strftime("%B %d, %Y")
        return (
            f"\nRespectfully submitted,\n\n"
            f"/s/ {PLAINTIFF_FULL}\n"
            f"{'_' * 40}\n"
            f"{PLAINTIFF_FULL}, Pro Se Plaintiff\n"
            f"Muskegon County, Michigan\n"
            f"[Address]\n"
            f"[Phone]\n"
            f"[Email]\n"
            f"Dated: {today}\n"
        )

    # ── Motion Generator ──────────────────────────────────────────────────

    def generate_motion(
        self,
        title: str,
        issues: List[str],
        evidence_ids: Optional[List[int]] = None,
        authority_ids: Optional[List[str]] = None,
        case_type: str = "custody",
    ) -> str:
        """
        Generate a complete MCR-compliant motion.

        Parameters
        ----------
        title : str
            Motion title (e.g. "PLAINTIFF'S MOTION TO COMPEL DISCOVERY").
        issues : list[str]
            Legal issues to argue (each becomes an IRAC section).
        evidence_ids : list[int] or None
            IDs into evidence_quotes table.
        authority_ids : list[str] or None
            Specific citations to include.
        case_type : str
            "custody", "ppo", or "appeal".
        """
        case_number = CASE_NUMBERS.get(case_type, CASE_NUMBERS["custody"])

        # 1. Caption
        doc = self.generate_caption(case_number, case_type, title)

        # 2. Introduction
        doc += (
            f"\n    NOW COMES Plaintiff, {PLAINTIFF_FULL}, appearing pro se, "
            f"and respectfully\nmoves this Honorable Court for the relief "
            f"described herein. In support thereof,\nPlaintiff states as follows:\n\n"
        )

        # 3. Statement of Facts
        doc += "STATEMENT OF FACTS\n\n"
        evidence = self._fetch_evidence(evidence_ids or [])
        if evidence:
            for idx, ev in enumerate(evidence, 1):
                quote = ev.get("quote_text", "[Evidence text unavailable]")
                significance = ev.get("legal_significance", "")
                doc += f"    {idx}. {quote}"
                if significance:
                    doc += f" ({significance})"
                doc += "\n\n"
        else:
            doc += "    1. [Statement of facts to be completed from the record.]\n\n"

        # 4. Legal Standard
        doc += "LEGAL STANDARD\n\n"
        authorities = self._fetch_citations(authority_ids) if authority_ids else []
        if authorities:
            for auth in authorities:
                cite = auth.get("citation", "")
                ctx = auth.get("context", "")
                if cite:
                    doc += f"    {cite}"
                    if ctx:
                        doc += f": {ctx[:300]}"
                    doc += "\n\n"
        else:
            # Search for authority related to the first issue
            if issues:
                found = self._search_authority(issues[0], limit=2)
                for auth in found:
                    rn = auth.get("rule_number", "")
                    tt = auth.get("title", "")
                    ft = auth.get("full_text", "")
                    if rn:
                        doc += f"    {rn}"
                        if tt:
                            doc += f" — {tt}"
                        doc += "\n"
                        if ft:
                            doc += f"    {ft[:400]}\n"
                        doc += "\n"
            if not authorities and not issues:
                doc += "    [Legal standard to be inserted.]\n\n"

        # 5. Argument (IRAC per issue)
        doc += "ARGUMENT\n\n"
        for i, issue in enumerate(issues, 1):
            doc += f"{'=' * 60}\n"
            doc += f"ARGUMENT {_roman(i)}: {issue.upper()}\n"
            doc += f"{'=' * 60}\n\n"

            # Gather rule citations from DB
            rule_cites = []
            if authority_ids:
                rule_cites = authority_ids
            else:
                found = self._search_authority(issue, limit=3)
                rule_cites = [a["rule_number"] for a in found if a.get("rule_number")]

            # Gather facts from evidence
            facts = []
            if evidence:
                for ev in evidence:
                    qt = ev.get("quote_text", "")
                    if qt:
                        facts.append(qt[:200])
            if not facts:
                facts = ["[Facts to be inserted from the record.]"]

            conclusion = (
                f"For the foregoing reasons, this Court should grant "
                f"Plaintiff's request regarding {issue}."
            )

            doc += self.generate_irac_section(issue, rule_cites, facts, conclusion)
            doc += "\n"

        # 6. Relief Requested
        doc += "RELIEF REQUESTED\n\n"
        doc += (
            f"    WHEREFORE, Plaintiff {PLAINTIFF_FULL} respectfully requests "
            f"that this\nHonorable Court:\n\n"
        )
        for i, issue in enumerate(issues, 1):
            doc += f"    {i}. Grant Plaintiff's request regarding {issue};\n\n"
        doc += (
            f"    {len(issues) + 1}. Grant such other and further relief as "
            f"this Court deems just\nand equitable.\n"
        )

        # 7. Signature block
        doc += self.generate_signature_block()

        # 8. Certificate of Service
        doc += self.generate_certificate_of_service(
            served_parties=[DEFENDANT_FULL],
        )

        return doc

    # ── Brief Generator ───────────────────────────────────────────────────

    def generate_brief(
        self,
        title: str,
        issues: List[str],
        is_appellate: bool = False,
        case_type: str = "custody",
    ) -> str:
        """
        Generate a complete MCR-compliant brief.

        Parameters
        ----------
        title : str
            Brief title.
        issues : list[str]
            Legal issues / questions presented.
        is_appellate : bool
            If True, uses appellate format per MCR 7.212.
        case_type : str
            "custody", "ppo", or "appeal".
        """
        if is_appellate:
            case_type = "appeal"
        case_number = CASE_NUMBERS.get(case_type, CASE_NUMBERS["custody"])

        # 1. Caption
        doc = self.generate_caption(case_number, case_type, title)

        # 2. Table of Contents
        doc += "\nTABLE OF CONTENTS\n\n"
        toc_items = [
            ("Table of Authorities", "ii"),
            ("Statement of Jurisdiction", "1"),
            ("Statement of Questions Presented", "2"),
            ("Statement of Facts", "3"),
        ]
        for i, issue in enumerate(issues, 1):
            toc_items.append((f"Argument {_roman(i)}: {issue}", str(3 + i)))
        toc_items.append(("Relief Requested", str(4 + len(issues))))
        for label, page in toc_items:
            doc += f"    {label} {'.' * max(1, 58 - len(label))} {page}\n"
        doc += "\n"

        # 3. Table of Authorities
        doc += "TABLE OF AUTHORITIES\n\n"
        doc += "Cases:\n\n"
        doc += "    [Case authorities to be completed]\n\n"
        doc += "Statutes and Court Rules:\n\n"
        # Pull authorities from DB based on issues
        seen_rules: List[str] = []
        for issue in issues:
            found = self._search_authority(issue, limit=3)
            for auth in found:
                rn = auth.get("rule_number", "")
                tt = auth.get("title", "")
                if rn and rn not in seen_rules:
                    seen_rules.append(rn)
                    doc += f"    {rn}"
                    if tt:
                        doc += f" — {tt}"
                    doc += " .... passim\n"
        if not seen_rules:
            doc += "    [Authorities to be completed]\n"
        doc += "\n"

        # 4. Statement of Jurisdiction
        doc += "STATEMENT OF JURISDICTION\n\n"
        if is_appellate:
            doc += (
                f"    This Court has jurisdiction pursuant to MCR 7.203 and "
                f"MCR 7.204.\n"
                f"    Plaintiff-Appellant appeals as of right from the order(s) of "
                f"the\n14th Judicial Circuit Court, County of Muskegon, the "
                f"Honorable {JUDGE}\npresiding, entered in Case No. "
                f"{CASE_NUMBERS['custody']}.\n\n"
            )
        else:
            doc += (
                f"    This Court has jurisdiction pursuant to MCL 600.601 et seq.\n\n"
            )

        # 5. Statement of Questions Presented
        doc += "STATEMENT OF QUESTIONS PRESENTED\n\n"
        for i, issue in enumerate(issues, 1):
            doc += f"    {_roman(i)}. {issue}\n\n"
            doc += "        Plaintiff-Appellant answers: Yes.\n\n"

        # 6. Statement of Facts
        doc += "STATEMENT OF FACTS\n\n"
        doc += (
            "    [Statement of facts to be completed from the record. "
            "All factual\nassertions must include pinpoint record citations.]\n\n"
        )

        # 7. Argument (IRAC per issue)
        doc += "ARGUMENT\n\n"
        for i, issue in enumerate(issues, 1):
            doc += f"{'=' * 60}\n"
            doc += f"ARGUMENT {_roman(i)}: {issue.upper()}\n"
            doc += f"{'=' * 60}\n\n"

            # Standard of review
            if is_appellate:
                doc += (
                    "    Standard of Review: [Abuse of discretion / de novo / "
                    "clear error —\n    to be specified per issue.]\n\n"
                )

            rule_cites: List[str] = []
            found = self._search_authority(issue, limit=3)
            rule_cites = [a["rule_number"] for a in found if a.get("rule_number")]

            facts = ["[Facts to be inserted from the record with citations.]"]
            conclusion = (
                f"This Court should find in Plaintiff's favor on the issue of "
                f"{issue}."
            )

            doc += self.generate_irac_section(issue, rule_cites, facts, conclusion)
            doc += "\n"

        # 8. Relief Requested
        doc += "RELIEF REQUESTED\n\n"
        doc += (
            f"    WHEREFORE, {'Plaintiff-Appellant' if is_appellate else 'Plaintiff'} "
            f"{PLAINTIFF_FULL}\nrespectfully requests that this Court:\n\n"
        )
        for i, issue in enumerate(issues, 1):
            doc += f"    {i}. Grant relief regarding {issue};\n\n"
        doc += (
            f"    {len(issues) + 1}. Grant such other and further relief as "
            f"this Court deems just\nand equitable.\n"
        )

        # 9. Signature block
        doc += self.generate_signature_block()

        # 10. Certificate of Service
        doc += self.generate_certificate_of_service(
            served_parties=[DEFENDANT_FULL],
        )

        return doc

    # ── Filing Validation ─────────────────────────────────────────────────

    def validate_filing(self, document_text: str) -> Dict[str, Any]:
        """
        Validate a filing document against MCR requirements.

        Returns dict with 'score' (0-100), 'passed' list, 'issues' list.
        """
        checks: List[Tuple[str, bool]] = []
        issues: List[str] = []

        # 1. Caption present
        has_caption = "STATE OF MICHIGAN" in document_text
        checks.append(("caption_present", has_caption))
        if not has_caption:
            issues.append("Missing caption — MCR 2.113(A) requires a proper caption.")

        # 2. Case number present
        has_case_no = bool(re.search(
            r"Case No\.\s*[\w\-]+|COA Case No\.\s*[\w\-]+", document_text
        ))
        checks.append(("case_number_present", has_case_no))
        if not has_case_no:
            issues.append("Missing case number in caption — MCR 2.113(A).")

        # 3. Certificate of Service
        has_cos = "CERTIFICATE OF SERVICE" in document_text
        checks.append(("certificate_of_service", has_cos))
        if not has_cos:
            issues.append(
                "Missing Certificate of Service — MCR 2.107 requires proof of service."
            )

        # 4. Signature block
        has_sig = bool(re.search(r"/s/|Respectfully submitted", document_text))
        checks.append(("signature_block", has_sig))
        if not has_sig:
            issues.append("Missing signature block.")

        # 5. Numbered paragraphs or structured sections
        has_numbered = bool(re.search(r"^\s*\d+\.\s+", document_text, re.MULTILINE))
        checks.append(("numbered_paragraphs", has_numbered))
        if not has_numbered:
            issues.append("No numbered paragraphs found — MCR 2.113(A) recommended.")

        # 6. Citations present (MCR, MCL, MRE, or case law)
        has_citations = bool(re.search(
            r"MCR\s+\d+\.\d+|MCL\s+\d+\.\d+|MRE\s+\d+|"
            r"\d+\s+Mich\s+(App\s+)?\d+",
            document_text,
        ))
        checks.append(("citations_present", has_citations))
        if not has_citations:
            issues.append(
                "No legal citations found — every legal assertion must cite authority."
            )

        # 7. Judge name
        has_judge = JUDGE in document_text
        checks.append(("judge_name", has_judge))
        if not has_judge:
            issues.append(f"Judge name ({JUDGE}) not found in document.")

        # 8. Page count estimate (approx 250 words/page, 50-page limit for briefs)
        word_count = len(document_text.split())
        page_estimate = max(1, word_count // 250)
        within_limits = page_estimate <= 50
        checks.append(("page_limit", within_limits))
        if not within_limits:
            issues.append(
                f"Estimated {page_estimate} pages — may exceed MCR page limits."
            )

        # 9. Parties named
        has_parties = PLAINTIFF in document_text and (
            "WATSON" in document_text.upper()
        )
        checks.append(("parties_named", has_parties))
        if not has_parties:
            issues.append("One or both parties not named in document.")

        # 10. IRAC structure (for motions/briefs)
        has_irac = any(
            heading in document_text
            for heading in ["ISSUE", "RULE", "APPLICATION", "CONCLUSION", "ARGUMENT"]
        )
        checks.append(("argument_structure", has_irac))
        if not has_irac:
            issues.append("No IRAC argument structure detected.")

        passed = [name for name, ok in checks if ok]
        failed = [name for name, ok in checks if not ok]
        score = int((len(passed) / max(len(checks), 1)) * 100)

        return {
            "score": score,
            "passed": passed,
            "failed": failed,
            "issues": issues,
            "word_count": word_count,
            "page_estimate": page_estimate,
            "total_checks": len(checks),
        }

    # ── Proposed Order ────────────────────────────────────────────────────

    def _generate_proposed_order(
        self,
        title: str,
        issues: List[str],
        case_type: str = "custody",
    ) -> str:
        """Generate a proposed order for a motion."""
        case_number = CASE_NUMBERS.get(case_type, CASE_NUMBERS["custody"])
        doc = self.generate_caption(case_number, case_type, f"ORDER — {title}")
        today = datetime.now().strftime("%B %d, %Y")

        doc += (
            f"\n    At a session of said Court held in the City of Muskegon,\n"
            f"County of Muskegon, State of Michigan, on {today}.\n\n"
            f"    PRESENT: {JUDGE}\n\n"
            f"    This matter having come before the Court on Plaintiff's "
            f"{title},\nand the Court being fully advised in the premises;\n\n"
            f"    IT IS HEREBY ORDERED that:\n\n"
        )
        for i, issue in enumerate(issues, 1):
            doc += f"    {i}. [Relief regarding: {issue}].\n\n"

        doc += (
            f"\n    IT IS SO ORDERED.\n\n"
            f"    {'_' * 40}\n"
            f"    {JUDGE}\n"
            f"    {COURTS.get(case_type, COURTS['custody'])}\n"
        )
        return doc

    # ── Proof of Service ──────────────────────────────────────────────────

    def _generate_proof_of_service(
        self,
        document_title: str,
        served_parties: List[str],
        method: str = "email",
    ) -> str:
        """Generate a separate proof of service document."""
        today = datetime.now().strftime("%B %d, %Y")
        method_map = {
            "email": "electronic mail (email)",
            "first-class mail": "first-class United States mail, postage prepaid",
            "personal": "personal service (hand delivery)",
            "efiling": "electronic filing through the Court's e-Filing system",
        }
        method_text = method_map.get(method, method)
        parties_block = "\n".join(f"        {p}" for p in served_parties)

        return (
            f"PROOF OF SERVICE\n\n"
            f"    I, {PLAINTIFF_FULL}, being duly sworn, depose and state that "
            f"on\n{today}, I served a true and correct copy of:\n\n"
            f"        {document_title}\n\n"
            f"upon the following by {method_text}:\n\n"
            f"{parties_block}\n\n"
            f"    I declare under the penalties of perjury that the foregoing is "
            f"true and\ncorrect.\n\n"
            f"{'_' * 40}\n"
            f"{PLAINTIFF_FULL}\n"
            f"Dated: {today}\n"
        )

    # ── Complete Filing Package ───────────────────────────────────────────

    def assemble_filing_package(
        self,
        filing_type: str,
        title: str,
        issues: List[str],
        evidence_ids: Optional[List[int]] = None,
        case_type: str = "custody",
    ) -> Dict[str, str]:
        """
        Assemble a complete filing package with all required components.

        Parameters
        ----------
        filing_type : str
            "motion", "brief", or "response".
        title : str
            Document title.
        issues : list[str]
            Legal issues.
        evidence_ids : list[int] or None
            Evidence quote IDs.
        case_type : str
            "custody", "ppo", or "appeal".

        Returns
        -------
        dict
            Keys: 'main_document', 'certificate_of_service',
                  'proposed_order' (if motion), 'proof_of_service',
                  'validation'.
        """
        package: Dict[str, Any] = {}

        # Main document
        if filing_type == "brief":
            is_appellate = case_type == "appeal"
            package["main_document"] = self.generate_brief(
                title, issues, is_appellate=is_appellate, case_type=case_type,
            )
        else:
            # motion or response
            package["main_document"] = self.generate_motion(
                title, issues, evidence_ids=evidence_ids, case_type=case_type,
            )

        # Certificate of Service (standalone copy)
        package["certificate_of_service"] = self.generate_certificate_of_service(
            served_parties=[DEFENDANT_FULL],
        )

        # Proposed Order (motions only)
        if filing_type in ("motion", "response"):
            package["proposed_order"] = self._generate_proposed_order(
                title, issues, case_type=case_type,
            )

        # Proof of Service
        package["proof_of_service"] = self._generate_proof_of_service(
            document_title=title,
            served_parties=[DEFENDANT_FULL],
        )

        # Validation
        package["validation"] = self.validate_filing(package["main_document"])

        return package

    # ── Filing Templates ──────────────────────────────────────────────────

    def get_filing_templates(self) -> List[Dict[str, str]]:
        """Return available filing type templates with governing authority."""
        return [
            {"key": key, **value} for key, value in FILING_TEMPLATES.items()
        ]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _roman(num: int) -> str:
    """Convert integer to Roman numeral (1-20 range)."""
    vals = [
        (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
    ]
    result = ""
    for value, numeral in vals:
        while num >= value:
            result += numeral
            num -= value
    return result


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import os
    import sys

    DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database not found at {DB_PATH}")
        sys.exit(1)

    assembler = FilingAssembler(DB_PATH)

    print("=" * 60)
    print("MBP LitigationOS — Filing Assembler Self-Test")
    print("=" * 60)

    # 1. Show available templates
    print("\n--- Available Filing Templates ---")
    for tmpl in assembler.get_filing_templates():
        print(f"  {tmpl['key']:40s} {tmpl['authority']:20s} ({tmpl['type']})")

    # 2. Generate a sample caption
    print("\n--- Sample Caption (Custody) ---")
    caption = assembler.generate_caption(
        case_number=CASE_NUMBERS["custody"],
        case_type="custody",
        document_title="PLAINTIFF'S MOTION TO COMPEL DISCOVERY",
    )
    print(caption)

    # 3. Generate a sample appellate caption
    print("\n--- Sample Caption (Appellate) ---")
    appeal_caption = assembler.generate_caption(
        case_number=CASE_NUMBERS["appeal"],
        case_type="appeal",
        document_title="APPELLANT'S BRIEF ON APPEAL",
    )
    print(appeal_caption)

    # 4. Validate the caption
    print("\n--- Validation Results ---")
    validation = assembler.validate_filing(caption)
    print(f"  Score:       {validation['score']}%")
    print(f"  Passed:      {', '.join(validation['passed'])}")
    if validation["issues"]:
        print(f"  Issues:      {len(validation['issues'])}")
        for issue in validation["issues"]:
            print(f"    - {issue}")
    else:
        print("  Issues:      None — fully compliant")

    # 5. Generate a sample IRAC section
    print("\n--- Sample IRAC Section ---")
    irac = assembler.generate_irac_section(
        issue="Whether the trial court erred in failing to conduct an evidentiary hearing",
        rule_citations=["MCR 2.119", "MCL 722.27"],
        facts=[
            "Plaintiff filed a timely motion requesting an evidentiary hearing.",
            "The court denied the motion without oral argument or hearing.",
            "329+ days of parent-child separation have resulted from this denial.",
        ],
        conclusion=(
            "The trial court abused its discretion by denying Plaintiff's motion "
            "without an evidentiary hearing as required by Michigan law."
        ),
    )
    print(irac[:500] + "..." if len(irac) > 500 else irac)

    assembler.close()
    print("\n[OK] Filing assembler self-test complete.")
