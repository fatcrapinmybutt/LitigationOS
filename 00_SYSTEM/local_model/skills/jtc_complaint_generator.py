#!/usr/bin/env python3
"""
MBP LitigationOS -- JTC Complaint Generator Skill
===================================================
Drafts Judicial Tenure Commission complaints from database evidence.
Queries judicial_violations, benchbook findings, chronological misconduct,
and forensic analysis to produce a court-ready JTC complaint.

Authority: Const 1963 art 6 § 30; MCR 9.200-9.252.
Respondent: Hon. Jenny L. McNeill, 14th Circuit Court, Muskegon County.
Complainant: Andrew Pigors (pro se).

STATUS: COMPLAINT NOT YET FILED.
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import textwrap
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parent.parent
        if "skills" in str(Path(__file__))
        else Path(__file__).resolve().parent
    ),
)
try:
    from cycle_method import cycle_json, cycle_print
except ImportError:
    cycle_json = lambda obj, **kw: print(json.dumps(obj, default=str))
    cycle_print = print

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)

# ── Canon mapping for the Michigan Code of Judicial Conduct ──────────
CANON_MAP: Dict[str, str] = {
    "Canon 1": "A judge should uphold the integrity and independence of the judiciary.",
    "Canon 2": "A judge should avoid impropriety and the appearance of impropriety in all activities.",
    "Canon 2A": "A judge should respect and comply with the law and should act at all times in a manner that promotes public confidence in the integrity and impartiality of the judiciary.",
    "Canon 3": "A judge should perform the duties of the office impartially and diligently.",
    "Canon 3(A)(4)": "A judge should be patient, dignified, and courteous to litigants, jurors, witnesses, lawyers, and others.",
    "Canon 3(A)(5)": "A judge should dispose of all judicial matters promptly and should not engage in ex parte communications.",
    "Canon 3(B)(2)": "A judge shall not allow family, social, political, or other relationships to influence judicial conduct or judgment, nor convey or permit others to convey the impression that they are in a special position to influence the judge.",
    "Canon 3(B)(5)": "A judge shall require lawyers in proceedings before the judge to refrain from manifesting bias or prejudice.",
    "Canon 3(B)(7)": "A judge shall not initiate, permit, or consider ex parte communications, or consider other communications made to the judge outside the presence of the parties.",
    "Canon 4": "A judge should so conduct extra-judicial activities as to minimize the risk of conflict with judicial obligations.",
}

# Keywords for canon auto-classification
_CANON_KEYWORDS: Dict[str, List[str]] = {
    "Canon 1": ["integrity", "independence", "judicial independence"],
    "Canon 2": ["impropriety", "appearance", "public confidence"],
    "Canon 2A": ["comply with law", "promote confidence", "impartiality"],
    "Canon 3": ["impartial", "diligent", "duties of office"],
    "Canon 3(A)(4)": ["patient", "dignified", "courteous", "demeanor"],
    "Canon 3(A)(5)": ["ex parte", "exparte", "without notice"],
    "Canon 3(B)(2)": ["bias", "prejudice", "relationship", "influence"],
    "Canon 3(B)(5)": ["require lawyers", "refrain from bias"],
    "Canon 3(B)(7)": ["ex parte communication", "outside the presence", "ex parte order"],
    "Canon 4": ["extra-judicial", "conflict of interest"],
}

# Map DB canon_number patterns to standard canons
_DB_CANON_PATTERNS: Dict[str, str] = {
    "EX_PARTE": "Canon 3(B)(7)",
    "ex_parte": "Canon 3(B)(7)",
    "PROCEDURAL_MISCONDUCT": "Canon 3",
    "CREDIBILITY_FAILURE": "Canon 3",
    "DUE_PROCESS_VIOLATION": "Canon 2A",
    "PPO_WEAPONIZATION": "Canon 2",
    "MCJC_CANON_VIOLATION": "Canon 2",
    "Disqualification": "Canon 3(B)(2)",
    "Canon 2": "Canon 2",
    "Canon 3": "Canon 3",
}


def _get_db(db_path: str = DB_PATH) -> Optional[sqlite3.Connection]:
    """Get read-only DB connection."""
    try:
        conn = sqlite3.connect(db_path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA query_only=ON")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        return None


def _row_to_dict(row: sqlite3.Row) -> Dict:
    """Convert a sqlite3.Row to a plain dict, replacing None with empty string."""
    return {k: (v if v is not None else "") for k, v in dict(row).items()}


def _safe_query(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> List[Dict]:
    """Execute a query safely, returning list of dicts or empty list on error."""
    try:
        rows = conn.execute(sql, params).fetchall()
        return [_row_to_dict(r) for r in rows]
    except Exception:
        return []


class JTCComplaintGenerator:
    """Generates JTC complaints from database evidence."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    # ── Data Gathering ────────────────────────────────────────────────

    def gather_violations(
        self,
        judge_name: str = "McNeill",
        severity_filter: Optional[str] = None,
        limit: int = 500,
    ) -> List[Dict]:
        """
        Query all violation tables for misconduct by the specified judge.

        Sources:
          - judicial_violations
          - benchbook_violation_findings
          - auth_benchbook_violations
          - chronological_misconduct
          - forensic_judicial_analysis
        """
        conn = _get_db(self.db_path)
        if not conn:
            return []

        all_violations: List[Dict] = []
        like_judge = f"%{judge_name}%"

        # 1. judicial_violations (primary table)
        sql = (
            "SELECT violation_id, judge_name, canon_number, canon_text, "
            "violation_description, evidence_refs, severity, jtc_exhibit_id, created_at "
            "FROM judicial_violations WHERE judge_name LIKE ?"
        )
        params: list = [like_judge]
        if severity_filter:
            sql += " AND severity = ?"
            params.append(severity_filter)
        sql += (
            " ORDER BY CASE severity "
            "WHEN 'critical' THEN 1 WHEN 'high' THEN 2 "
            "WHEN 'medium' THEN 3 ELSE 4 END LIMIT ?"
        )
        params.append(limit)
        for row in _safe_query(conn, sql, tuple(params)):
            row["source_table"] = "judicial_violations"
            all_violations.append(row)

        # 2. benchbook_violation_findings
        sql = "SELECT rowid as id, rule, explanation, matching_text FROM benchbook_violation_findings LIMIT ?"
        for row in _safe_query(conn, sql, (limit,)):
            row["source_table"] = "benchbook_violation_findings"
            row["severity"] = "high"
            all_violations.append(row)

        # 3. auth_benchbook_violations
        sql = (
            "SELECT id, rule, explanation, matching_text, judge, severity, source_file "
            "FROM auth_benchbook_violations WHERE judge LIKE ? LIMIT ?"
        )
        for row in _safe_query(conn, sql, (like_judge, limit)):
            row["source_table"] = "auth_benchbook_violations"
            # severity is numeric in this table; normalize
            try:
                sev_val = float(row.get("severity", 0))
                if sev_val >= 0.8:
                    row["severity"] = "critical"
                elif sev_val >= 0.6:
                    row["severity"] = "high"
                elif sev_val >= 0.4:
                    row["severity"] = "medium"
                else:
                    row["severity"] = "low"
            except (ValueError, TypeError):
                row["severity"] = "medium"
            all_violations.append(row)

        # 4. chronological_misconduct
        sql = "SELECT rowid as id, issue, date FROM chronological_misconduct ORDER BY date LIMIT ?"
        for row in _safe_query(conn, sql, (limit,)):
            row["source_table"] = "chronological_misconduct"
            row["severity"] = "high"
            all_violations.append(row)

        # 5. forensic_judicial_analysis
        sql = (
            "SELECT finding_id, category, severity, description, "
            "evidence_citations, mcr_violations, date_iso, source_table "
            "FROM forensic_judicial_analysis "
            "ORDER BY CASE severity "
            "WHEN 'critical' THEN 1 WHEN 'high' THEN 2 "
            "WHEN 'medium' THEN 3 ELSE 4 END LIMIT ?"
        )
        for row in _safe_query(conn, sql, (limit,)):
            row["source_table"] = "forensic_judicial_analysis"
            all_violations.append(row)

        conn.close()
        return all_violations

    # ── Canon Mapping ─────────────────────────────────────────────────

    def map_to_canons(self, violations: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Map violations to Code of Judicial Conduct canons.

        Returns dict: canon_key -> list of supporting violations.
        """
        canon_buckets: Dict[str, List[Dict]] = {k: [] for k in CANON_MAP}

        for v in violations:
            assigned = False
            # Try DB canon_number first
            canon_num = str(v.get("canon_number", ""))
            for pattern, canon_key in _DB_CANON_PATTERNS.items():
                if pattern in canon_num:
                    if canon_key in canon_buckets:
                        canon_buckets[canon_key].append(v)
                        assigned = True
                        break

            if assigned:
                continue

            # Keyword-based classification from description / matching_text
            text_blob = " ".join(
                str(v.get(f, ""))
                for f in (
                    "violation_description",
                    "description",
                    "explanation",
                    "matching_text",
                    "issue",
                    "category",
                    "mcr_violations",
                )
            ).lower()

            best_canon = None
            best_hits = 0
            for canon_key, keywords in _CANON_KEYWORDS.items():
                hits = sum(1 for kw in keywords if kw in text_blob)
                if hits > best_hits:
                    best_hits = hits
                    best_canon = canon_key

            if best_canon and best_hits > 0:
                canon_buckets[best_canon].append(v)
            else:
                # Default: Canon 3 (impartiality/diligence) as catch-all
                canon_buckets["Canon 3"].append(v)

        return canon_buckets

    # ── Evidence Retrieval ────────────────────────────────────────────

    def get_evidence_for_violation(
        self, violation_id: int, limit: int = 5
    ) -> List[Dict]:
        """
        Get supporting evidence quotes for a specific violation.
        Searches evidence_quotes_fts for related text.
        """
        conn = _get_db(self.db_path)
        if not conn:
            return []

        results: List[Dict] = []

        # First, get the violation text to use as search terms
        violation_text = ""
        for table, id_col in [
            ("judicial_violations", "violation_id"),
            ("forensic_judicial_analysis", "finding_id"),
        ]:
            rows = _safe_query(
                conn,
                f"SELECT * FROM {table} WHERE {id_col} = ? LIMIT 1",
                (str(violation_id),),
            )
            if rows:
                violation_text = str(
                    rows[0].get("violation_description", "")
                    or rows[0].get("description", "")
                )
                break

        if not violation_text:
            # Try by rowid across tables
            for table in ["benchbook_violation_findings", "auth_benchbook_violations"]:
                rows = _safe_query(
                    conn,
                    f"SELECT * FROM {table} WHERE rowid = ? OR id = ? LIMIT 1",
                    (violation_id, violation_id),
                )
                if rows:
                    violation_text = str(
                        rows[0].get("explanation", "")
                        or rows[0].get("matching_text", "")
                    )
                    break

        if violation_text:
            # Extract key terms for FTS search (first 5 significant words)
            words = [
                w
                for w in violation_text.split()
                if len(w) > 3 and w.isalpha()
            ][:5]
            if words:
                fts_query = " OR ".join(words)
                results = _safe_query(
                    conn,
                    "SELECT id, quote_text, speaker, legal_significance, evidence_category "
                    "FROM evidence_quotes WHERE rowid IN "
                    "(SELECT rowid FROM evidence_quotes_fts WHERE evidence_quotes_fts MATCH ?) "
                    "LIMIT ?",
                    (fts_query, limit),
                )

        # Fallback: also check impeachment_items
        if len(results) < limit:
            remaining = limit - len(results)
            like_pat = f"%{violation_text[:80]}%" if violation_text else "%McNeill%"
            impeach = _safe_query(
                conn,
                "SELECT id, speaker, statement, contradicting_text, legal_hook "
                "FROM impeachment_items "
                "WHERE statement LIKE ? OR contradicting_text LIKE ? "
                "LIMIT ?",
                (like_pat, like_pat, remaining),
            )
            for item in impeach:
                item["source"] = "impeachment_items"
                results.append(item)

        conn.close()
        return results

    # ── Complaint Narrative (structured) ──────────────────────────────

    def generate_complaint_narrative(
        self, judge_name: str = "McNeill"
    ) -> Dict:
        """
        Generate full JTC complaint structure:
          - complaint_header
          - executive_summary
          - canon_sections (per-canon violations with evidence)
          - chronological_timeline
          - pattern_analysis
          - relief_requested
          - total_violations, total_evidence_items, severity_breakdown
        """
        violations = self.gather_violations(judge_name=judge_name)
        canon_sections = self.map_to_canons(violations)
        stats = self.get_statistics(judge_name=judge_name)

        # Chronological timeline from chronological_misconduct
        conn = _get_db(self.db_path)
        timeline: List[Dict] = []
        pattern_analysis: List[Dict] = []
        if conn:
            timeline = _safe_query(
                conn,
                "SELECT rowid as id, issue, date FROM chronological_misconduct "
                "ORDER BY date LIMIT 500",
            )
            pattern_analysis = _safe_query(
                conn,
                "SELECT finding_id, category, severity, description, "
                "evidence_citations, mcr_violations, date_iso "
                "FROM forensic_judicial_analysis "
                "ORDER BY CASE severity "
                "WHEN 'critical' THEN 1 WHEN 'high' THEN 2 "
                "WHEN 'medium' THEN 3 ELSE 4 END LIMIT 200",
            )
            conn.close()

        # Build canon sections with counts
        canon_output: Dict[str, Dict] = {}
        total_evidence = 0
        for canon_key, canon_desc in CANON_MAP.items():
            items = canon_sections.get(canon_key, [])
            canon_output[canon_key] = {
                "canon_text": canon_desc,
                "violation_count": len(items),
                "violations": items[:50],  # cap per-canon for output size
            }
            total_evidence += len(items)

        severity_breakdown = stats.get("by_severity", {})

        narrative = {
            "complaint_header": {
                "tribunal": "Michigan Judicial Tenure Commission",
                "authority": "Const 1963 art 6 § 30; MCR 9.200-9.252",
                "complainant": "Andrew Pigors (pro se)",
                "complainant_role": "Plaintiff/Appellant in Pigors v. Watson",
                "respondent": "Hon. Jenny L. McNeill",
                "respondent_court": "14th Circuit Court, Muskegon County, Michigan",
                "case_numbers": [
                    "2024-001507-DC (custody)",
                    "2023-5907-PP (PPO)",
                ],
                "generated_date": datetime.now().strftime("%B %d, %Y"),
                "status": "DRAFT — NOT YET FILED",
            },
            "executive_summary": (
                f"This complaint documents {stats.get('total_violations', 0)} instances of "
                f"judicial misconduct by {stats.get('respondent', 'Hon. Jenny L. McNeill')} "
                f"across multiple categories, including {severity_breakdown.get('critical', 0)} "
                f"critical violations, {severity_breakdown.get('high', 0)} high-severity "
                f"violations, and {severity_breakdown.get('medium', 0)} medium-severity "
                f"violations. The misconduct spans ex parte communications, procedural "
                f"irregularities, bias, due process violations, and failure to follow "
                f"mandatory court rules, resulting in over 329 days of parent-child "
                f"separation without lawful justification."
            ),
            "canon_sections": canon_output,
            "chronological_timeline": timeline[:100],
            "pattern_analysis": pattern_analysis[:100],
            "relief_requested": {
                "primary": "Public censure and/or removal from the bench pursuant to Const 1963 art 6 § 30",
                "secondary": [
                    "Referral for further investigation under MCR 9.220",
                    "Interim suspension pending investigation under MCR 9.220(B)",
                    "Order requiring recusal from all Pigors v. Watson proceedings",
                    "Such other discipline as the Commission deems appropriate",
                ],
            },
            "total_violations": stats.get("total_violations", 0),
            "total_evidence_items": total_evidence,
            "severity_breakdown": severity_breakdown,
        }

        return narrative

    # ── Complaint Text (formatted document) ───────────────────────────

    def generate_complaint_text(self, judge_name: str = "McNeill") -> str:
        """
        Generate the JTC complaint as formatted text ready for filing.
        """
        narrative = self.generate_complaint_narrative(judge_name=judge_name)
        hdr = narrative["complaint_header"]
        stats = narrative["severity_breakdown"]

        lines: List[str] = []

        def _add(text: str = "") -> None:
            lines.append(text)

        def _blank(n: int = 1) -> None:
            for _ in range(n):
                lines.append("")

        # ── Header ────────────────────────────────────────────────
        _add("STATE OF MICHIGAN")
        _add("JUDICIAL TENURE COMMISSION")
        _blank(2)
        _add("=" * 60)
        _add("COMPLAINT")
        _add("=" * 60)
        _blank()
        _add(f"Complainant:   {hdr['complainant']}")
        _add(f"               Plaintiff/Appellant in Pigors v. Watson")
        _blank()
        _add(f"Respondent:    {hdr['respondent']}")
        _add(f"               {hdr['respondent_court']}")
        _blank()
        _add(f"Case Numbers:  {hdr['case_numbers'][0]}")
        _add(f"               {hdr['case_numbers'][1]}")
        _blank()
        _add(f"Date:          {hdr['generated_date']}")
        _add(f"Status:        {hdr['status']}")
        _blank()
        _add("-" * 60)
        _blank()

        # ── Jurisdictional Statement ──────────────────────────────
        _add("I. JURISDICTIONAL STATEMENT")
        _blank()
        para = 1
        _add(
            f"    {para}. The Judicial Tenure Commission has jurisdiction over this "
            f"complaint pursuant to Const 1963 art 6, § 30 and MCR 9.200 et seq."
        )
        para += 1
        _blank()
        _add(
            f"    {para}. The Respondent, Hon. Jenny L. McNeill, is a judge of the "
            f"14th Circuit Court, Muskegon County, Michigan, and is therefore subject "
            f"to the jurisdiction of this Commission."
        )
        para += 1
        _blank()
        _add(
            f"    {para}. MCR 9.202 provides that any person may file a complaint "
            f"with the Commission alleging that a judge has engaged in misconduct "
            f"in office, or conduct that is clearly prejudicial to the administration "
            f"of justice."
        )
        para += 1
        _blank()

        # ── Parties ───────────────────────────────────────────────
        _add("II. PARTIES")
        _blank()
        _add(
            f"    {para}. Complainant Andrew Pigors is a pro se litigant and the "
            f"father of a minor child who is the subject of custody proceedings "
            f"in Case No. 2024-001507-DC before the Respondent judge."
        )
        para += 1
        _blank()
        _add(
            f"    {para}. Respondent Hon. Jenny L. McNeill presides over the above-"
            f"captioned cases in the 14th Circuit Court, Muskegon County, Michigan."
        )
        para += 1
        _blank()

        # ── Executive Summary ─────────────────────────────────────
        _add("III. EXECUTIVE SUMMARY OF MISCONDUCT")
        _blank()
        _add(f"    {para}. {narrative['executive_summary']}")
        para += 1
        _blank()
        _add(
            f"    {para}. The misconduct documented herein is not the product of "
            f"isolated errors but reflects a sustained pattern of judicial conduct "
            f"that is clearly prejudicial to the administration of justice, in "
            f"violation of the Michigan Code of Judicial Conduct and the Michigan "
            f"Court Rules."
        )
        para += 1
        _blank()

        # ── Canon-by-Canon Violations ─────────────────────────────
        section_num = 4
        for canon_key, canon_desc in CANON_MAP.items():
            section_data = narrative["canon_sections"].get(canon_key, {})
            violation_count = section_data.get("violation_count", 0)
            if violation_count == 0:
                continue

            _add(f"{'=' * 60}")
            _add(f"{_roman(section_num)}. VIOLATIONS OF {canon_key.upper()}")
            _add(f"    \"{canon_desc}\"")
            _add(f"    ({violation_count} documented violations)")
            _add(f"{'=' * 60}")
            _blank()

            violation_items = section_data.get("violations", [])
            for i, v in enumerate(violation_items[:25], 1):
                desc = (
                    v.get("violation_description", "")
                    or v.get("description", "")
                    or v.get("explanation", "")
                    or v.get("issue", "")
                    or v.get("matching_text", "")
                )
                desc = " ".join(str(desc).split())[:500]
                severity = v.get("severity", "")
                evidence = v.get("evidence_refs", "") or v.get("evidence_citations", "") or v.get("mcr_violations", "")
                source = v.get("source_table", "")

                _add(f"    {para}. [{severity.upper() if severity else 'NOTED'}] {desc}")
                if evidence:
                    _add(f"        Authority: {evidence}")
                if source:
                    _add(f"        Source: {source}")
                para += 1
                _blank()

            section_num += 1

        # ── Chronological Timeline ────────────────────────────────
        _add(f"{'=' * 60}")
        _add(f"{_roman(section_num)}. CHRONOLOGICAL TIMELINE OF MISCONDUCT")
        _add(f"{'=' * 60}")
        _blank()

        timeline = narrative.get("chronological_timeline", [])
        if timeline:
            _add(
                f"    {para}. The following chronological timeline documents the "
                f"pattern and progression of judicial misconduct in these proceedings:"
            )
            para += 1
            _blank()

            for entry in timeline[:50]:
                date_str = entry.get("date", "Unknown")
                issue = " ".join(str(entry.get("issue", "")).split())[:300]
                _add(f"    {para}. [{date_str}] {issue}")
                para += 1
            _blank()
        section_num += 1

        # ── Pattern Analysis ──────────────────────────────────────
        _add(f"{'=' * 60}")
        _add(f"{_roman(section_num)}. FORENSIC PATTERN ANALYSIS")
        _add(f"{'=' * 60}")
        _blank()

        patterns = narrative.get("pattern_analysis", [])
        if patterns:
            # Summarize by category
            cat_counts: Dict[str, int] = defaultdict(int)
            for p in patterns:
                cat = p.get("category", "Uncategorized")
                cat_counts[cat] += 1

            _add(
                f"    {para}. Forensic analysis of the judicial record reveals "
                f"{len(patterns)} distinct findings across the following categories:"
            )
            para += 1
            _blank()
            for cat, cnt in sorted(cat_counts.items(), key=lambda x: -x[1]):
                _add(f"        - {cat}: {cnt} findings")
            _blank()

            # Top critical/high findings
            critical_findings = [
                p for p in patterns if p.get("severity") in ("critical", "high")
            ][:20]
            if critical_findings:
                _add(
                    f"    {para}. The most severe forensic findings include:"
                )
                para += 1
                _blank()
                for f in critical_findings:
                    desc = " ".join(str(f.get("description", "")).split())[:400]
                    sev = f.get("severity", "")
                    _add(f"    {para}. [{sev.upper()}] {desc}")
                    mcr = f.get("mcr_violations", "")
                    if mcr:
                        _add(f"        MCR Violations: {mcr}")
                    para += 1
                _blank()
        section_num += 1

        # ── Relief Requested ──────────────────────────────────────
        _add(f"{'=' * 60}")
        _add(f"{_roman(section_num)}. RELIEF REQUESTED")
        _add(f"{'=' * 60}")
        _blank()

        relief = narrative.get("relief_requested", {})
        _add(
            f"    {para}. WHEREFORE, Complainant respectfully requests that the "
            f"Judicial Tenure Commission:"
        )
        para += 1
        _blank()
        _add(f"    a. {relief.get('primary', '')};")
        _blank()
        for i, item in enumerate(relief.get("secondary", []), ord("b")):
            _add(f"    {chr(i)}. {item};")
        _blank()

        _add(
            f"    {para}. This complaint is submitted in good faith, based upon "
            f"personal knowledge and documentary evidence contained in the court "
            f"record of the above-captioned cases."
        )
        para += 1
        _blank(2)

        # ── Verification ──────────────────────────────────────────
        _add("VERIFICATION")
        _blank()
        _add(
            "    I, Andrew Pigors, declare under penalty of perjury that the "
            "statements made in this complaint are true and correct to the best "
            "of my knowledge, information, and belief."
        )
        _blank(2)
        _add("Dated: _________________________")
        _blank(2)
        _add("_________________________________")
        _add("Andrew Pigors")
        _add("Complainant (Pro Se)")
        _add("[Address]")
        _add("[Phone]")
        _add("[Email]")
        _blank(2)

        # ── Certificate of Service ────────────────────────────────
        _add("-" * 60)
        _add("CERTIFICATE OF SERVICE")
        _blank()
        _add(
            "    I hereby certify that on ______________, I served a true and "
            "correct copy of this Complaint upon the Judicial Tenure Commission "
            "by [first-class mail / personal delivery / electronic filing] at:"
        )
        _blank()
        _add("    Michigan Judicial Tenure Commission")
        _add("    3034 W. Grand Blvd., Suite 8-450")
        _add("    Detroit, Michigan 48202")
        _blank(2)
        _add("_________________________________")
        _add("Andrew Pigors")
        _blank()

        return "\n".join(lines)

    # ── Statistics ────────────────────────────────────────────────────

    def get_statistics(self, judge_name: str = "McNeill") -> Dict:
        """
        Summary statistics: total violations, by severity, by canon,
        top violation categories, evidence coverage.
        """
        conn = _get_db(self.db_path)
        if not conn:
            return {"error": "DB connection failed"}

        like_judge = f"%{judge_name}%"
        result: Dict = {
            "respondent": f"Hon. Jenny L. {judge_name}",
            "total_violations": 0,
            "by_severity": {},
            "by_canon": {},
            "by_source_table": {},
            "top_categories": [],
            "evidence_coverage": 0,
        }

        # Total from judicial_violations
        rows = _safe_query(
            conn,
            "SELECT COUNT(*) as cnt FROM judicial_violations WHERE judge_name LIKE ?",
            (like_judge,),
        )
        jv_count = rows[0]["cnt"] if rows else 0

        # By severity
        sev_rows = _safe_query(
            conn,
            "SELECT severity, COUNT(*) as cnt FROM judicial_violations "
            "WHERE judge_name LIKE ? GROUP BY severity ORDER BY cnt DESC",
            (like_judge,),
        )
        result["by_severity"] = {r["severity"]: r["cnt"] for r in sev_rows if r["severity"]}

        # By canon
        canon_rows = _safe_query(
            conn,
            "SELECT canon_number, COUNT(*) as cnt FROM judicial_violations "
            "WHERE judge_name LIKE ? GROUP BY canon_number ORDER BY cnt DESC",
            (like_judge,),
        )
        result["by_canon"] = {r["canon_number"]: r["cnt"] for r in canon_rows if r["canon_number"]}

        # Supplementary table counts
        supp_tables = {
            "benchbook_violation_findings": "SELECT COUNT(*) as cnt FROM benchbook_violation_findings",
            "auth_benchbook_violations": f"SELECT COUNT(*) as cnt FROM auth_benchbook_violations WHERE judge LIKE '{like_judge}'",
            "chronological_misconduct": "SELECT COUNT(*) as cnt FROM chronological_misconduct",
            "forensic_judicial_analysis": "SELECT COUNT(*) as cnt FROM forensic_judicial_analysis",
        }
        total = jv_count
        result["by_source_table"]["judicial_violations"] = jv_count
        for table, sql in supp_tables.items():
            rows = _safe_query(conn, sql)
            cnt = rows[0]["cnt"] if rows else 0
            result["by_source_table"][table] = cnt
            total += cnt
        result["total_violations"] = total

        # Top categories from forensic_judicial_analysis
        cat_rows = _safe_query(
            conn,
            "SELECT category, COUNT(*) as cnt FROM forensic_judicial_analysis "
            "GROUP BY category ORDER BY cnt DESC LIMIT 10",
        )
        result["top_categories"] = [
            {"category": r["category"], "count": r["cnt"]} for r in cat_rows
        ]

        # Evidence coverage: how many evidence_quotes exist
        ev_rows = _safe_query(conn, "SELECT COUNT(*) as cnt FROM evidence_quotes")
        result["evidence_coverage"] = ev_rows[0]["cnt"] if ev_rows else 0

        conn.close()
        return result


# ── Helpers ───────────────────────────────────────────────────────────

def _roman(num: int) -> str:
    """Convert integer to Roman numeral string."""
    val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syms = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
    result = ""
    for i, v in enumerate(val):
        while num >= v:
            result += syms[i]
            num -= v
    return result


# ── Self-Test ─────────────────────────────────────────────────────────

def self_test() -> Dict:
    """Self-test: verify DB connectivity and basic query capability."""
    results: Dict = {
        "db_connected": False,
        "tables_found": {},
        "sample_counts": {},
        "errors": [],
    }

    try:
        conn = _get_db()
        if not conn:
            results["errors"].append("Failed to connect to database")
            return results
        results["db_connected"] = True

        required_tables = [
            "judicial_violations",
            "benchbook_violation_findings",
            "auth_benchbook_violations",
            "chronological_misconduct",
            "forensic_judicial_analysis",
            "evidence_quotes",
            "impeachment_items",
        ]

        for table in required_tables:
            try:
                row = conn.execute(f"SELECT COUNT(*) as cnt FROM {table}").fetchone()
                results["tables_found"][table] = True
                results["sample_counts"][table] = row["cnt"] if row else 0
            except Exception as e:
                results["tables_found"][table] = False
                results["errors"].append(f"{table}: {e}")

        conn.close()
    except Exception as e:
        results["errors"].append(str(e))

    results["status"] = "PASS" if results["db_connected"] and not results["errors"] else "FAIL"
    return results


# ── CLI ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="JTC Complaint Generator — MBP LitigationOS Skill"
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="stats",
        choices=["stats", "violations", "canons", "narrative", "text", "self-test"],
        help="Command to run (default: stats)",
    )
    parser.add_argument("--judge", default="McNeill", help="Judge name filter")
    parser.add_argument("--severity", default=None, help="Severity filter")
    parser.add_argument("--limit", type=int, default=500, help="Row limit")
    parser.add_argument("--output", default=None, help="Output file path")

    args = parser.parse_args()

    gen = JTCComplaintGenerator()

    if args.command == "self-test":
        result = self_test()
    elif args.command == "stats":
        result = gen.get_statistics(judge_name=args.judge)
    elif args.command == "violations":
        result = gen.gather_violations(
            judge_name=args.judge,
            severity_filter=args.severity,
            limit=args.limit,
        )
    elif args.command == "canons":
        violations = gen.gather_violations(judge_name=args.judge, limit=args.limit)
        result = {
            k: {"canon_text": CANON_MAP[k], "count": len(v)}
            for k, v in gen.map_to_canons(violations).items()
        }
    elif args.command == "narrative":
        result = gen.generate_complaint_narrative(judge_name=args.judge)
    elif args.command == "text":
        text = gen.generate_complaint_text(judge_name=args.judge)
        if args.output:
            Path(args.output).write_text(text, encoding="utf-8")
            print(f"Complaint written to {args.output}", file=sys.stderr)
            sys.exit(0)
        else:
            sys.stdout.buffer.write(text.encode("utf-8", errors="replace"))
            sys.stdout.buffer.write(b"\n")
            sys.exit(0)
    else:
        result = {"error": f"Unknown command: {args.command}"}

    cycle_json(result)
