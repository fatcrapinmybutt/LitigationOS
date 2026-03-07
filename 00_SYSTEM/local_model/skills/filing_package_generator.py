#!/usr/bin/env python3
"""
MBP LitigationOS -- Filing Package Generator Skill
====================================================
Auto-generate complete court filing packages for all litigation lanes.
Produces MCR-compliant captions, certificates of service, motion packages,
appellate briefs, MSC original actions, federal § 1983 complaints, and
JTC complaints — all grounded in litigation_context.db.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
import textwrap
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

# ── Case Constants ────────────────────────────────────────────────────
PLAINTIFF = "Andrew Pigors"
PLAINTIFF_ADDRESS = "Muskegon, Michigan"
DEFENDANT = "Tiffany Watson (fka Pigors)"
JUDGE = "Hon. Jenny L. McNeill"

CASES = {
    "custody": {"number": "2024-001507-DC", "court": "14th Circuit", "lane": "A"},
    "ppo": {"number": "2023-5907-PP", "court": "14th Circuit", "lane": "D"},
    "coa": {"number": "366810", "court": "COA", "lane": "F"},
}

COURT_INFO = {
    "14th Circuit": {
        "full_name": "14TH CIRCUIT COURT FOR THE COUNTY OF MUSKEGON",
        "state": "STATE OF MICHIGAN",
        "judge": JUDGE,
    },
    "COA": {
        "full_name": "MICHIGAN COURT OF APPEALS",
        "state": "STATE OF MICHIGAN",
        "judge": "Panel TBD",
    },
    "MSC": {
        "full_name": "MICHIGAN SUPREME COURT",
        "state": "STATE OF MICHIGAN",
        "judge": "",
    },
    "USDC_WD_MI": {
        "full_name": "UNITED STATES DISTRICT COURT\nWESTERN DISTRICT OF MICHIGAN",
        "state": "",
        "judge": "",
    },
    "JTC": {
        "full_name": "JUDICIAL TENURE COMMISSION",
        "state": "STATE OF MICHIGAN",
        "judge": "",
    },
}

# Page/word limits per court
PAGE_LIMITS = {
    "COA_brief": {"pages": 50, "words": 16000, "rule": "MCR 7.212(B)"},
    "circuit_motion": {"pages": 20, "words": 8000, "rule": "MCR 2.119(A)(2)"},
    "MSC_brief": {"pages": 50, "words": 16000, "rule": "MCR 7.312(B)"},
}


# ── DB Helper ─────────────────────────────────────────────────────────
def _get_db() -> Optional[sqlite3.Connection]:
    """Get read-only DB connection with mmap zero-syscall I/O for filing assembly."""
    try:
        # Use connection multiplexer for mmap=12GB + 128MB cache + optimal PRAGMAs
        try:
            import sys as _sys
            _sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "00_SYSTEM" / "pipeline"))
            from connection_multiplexer import get_connection
            return get_connection(readonly=True)
        except ImportError:
            pass
        # Fallback: direct connection with full PRAGMA tuning
        conn = sqlite3.connect(DB_PATH, timeout=180)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=180000")
        conn.execute("PRAGMA query_only=ON")
        conn.execute("PRAGMA cache_size=-131072")  # 128MB page cache
        conn.execute("PRAGMA mmap_size=12884901888")  # 12GB mmap
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        return None


def _rows_to_dicts(rows) -> List[Dict]:
    """Convert sqlite3.Row list to list of plain dicts."""
    return [dict(r) for r in rows] if rows else []


def _safe_query(conn, sql: str, params: tuple = ()) -> List[Dict]:
    """Execute query, return list of dicts. Empty list on failure."""
    try:
        return _rows_to_dicts(conn.execute(sql, params).fetchall())
    except Exception:
        return []


# ── Filing Package Generator ─────────────────────────────────────────
class FilingPackageGenerator:
    """Auto-generate complete court filing packages for all lanes."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    @property
    def conn(self) -> Optional[sqlite3.Connection]:
        if self._conn is None:
            self._conn = _get_db()
        return self._conn

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    # ── Inventory & Readiness ─────────────────────────────────────────

    def get_filing_inventory(
        self, lane: Optional[str] = None, status: Optional[str] = None
    ) -> List[Dict]:
        """Query filing_inventory and filing_packages tables.
        Optional filter by case lane or status."""
        if not self.conn:
            return []

        results = []

        # filing_inventory
        sql = "SELECT * FROM filing_inventory WHERE 1=1"
        params: list = []
        if lane:
            sql += " AND case_lane = ?"
            params.append(lane)
        if status:
            sql += " AND status = ?"
            params.append(status)
        sql += " ORDER BY rowid"
        results.extend(_safe_query(self.conn, sql, tuple(params)))

        # filing_packages
        pkg_sql = "SELECT * FROM filing_packages WHERE 1=1"
        pkg_params: list = []
        if lane:
            pkg_sql += " AND case_lane = ?"
            pkg_params.append(lane)
        if status:
            pkg_sql += " AND status = ?"
            pkg_params.append(status)
        pkg_sql += " ORDER BY rowid"
        pkgs = _safe_query(self.conn, pkg_sql, tuple(pkg_params))
        for p in pkgs:
            p["_source"] = "filing_packages"
        results.extend(pkgs)

        return results

    def get_filing_readiness(
        self, vehicle_name: Optional[str] = None
    ) -> List[Dict]:
        """Query filing_readiness: vehicle_name, authority_score,
        evidence_score, compliance_score, impeachment_score,
        total_score, gaps, strengths."""
        if not self.conn:
            return []

        if vehicle_name:
            return _safe_query(
                self.conn,
                "SELECT * FROM filing_readiness WHERE vehicle_name LIKE ?",
                (f"%{vehicle_name}%",),
            )
        return _safe_query(self.conn, "SELECT * FROM filing_readiness")

    # ── Caption Generation ────────────────────────────────────────────

    def generate_caption(self, court: str, case_number: str) -> str:
        """Generate MCR 2.113 compliant caption block.
        Courts: '14th Circuit', 'COA', 'MSC', 'USDC_WD_MI', 'JTC'"""
        info = COURT_INFO.get(court, COURT_INFO["14th Circuit"])
        today = datetime.now().strftime("%B %d, %Y")

        lines = []
        if info["state"]:
            lines.append(info["state"])
        lines.append(info["full_name"])
        lines.append("")

        if court in ("14th Circuit", "COA"):
            lines.append(f"{'ANDREW PIGORS,':<40}")
            lines.append(f"{'    Plaintiff/Appellant,':<40}Case No. {case_number}")
            if info.get("judge"):
                lines.append(f"{'':40}{info['judge']}")
            lines.append(f"{'  v.':<40}")
            lines.append(f"{'TIFFANY WATSON (fka PIGORS),':<40}")
            lines.append(f"{'    Defendant/Appellee.':<40}")
        elif court == "MSC":
            lines.append(f"{'ANDREW PIGORS,':<40}")
            lines.append(f"{'    Plaintiff/Petitioner,':<40}Case No. {case_number}")
            lines.append(f"{'  v.':<40}")
            lines.append(f"{'TIFFANY WATSON (fka PIGORS),':<40}")
            lines.append(f"{'    Defendant/Respondent.':<40}")
        elif court == "USDC_WD_MI":
            lines.append(f"{'ANDREW PIGORS,':<40}")
            lines.append(f"{'    Plaintiff,':<40}Case No. {case_number}")
            lines.append(f"{'  v.':<40}")
            lines.append(
                f"{'TIFFANY WATSON (fka PIGORS), et al.,':<40}"
            )
            lines.append(f"{'    Defendants.':<40}")
        elif court == "JTC":
            lines.append("IN THE MATTER OF:")
            lines.append(f"{'HON. JENNY L. McNEILL,':<40}Complaint No. {case_number}")
            lines.append(f"{'    14th Circuit Court Judge.':<40}")
        else:
            lines.append(f"{'ANDREW PIGORS,':<40}")
            lines.append(f"{'    Plaintiff,':<40}Case No. {case_number}")
            lines.append(f"{'  v.':<40}")
            lines.append(f"{'TIFFANY WATSON (fka PIGORS),':<40}")
            lines.append(f"{'    Defendant.':<40}")

        lines.append("_" * 60)
        return "\n".join(lines)

    # ── Certificate of Service ────────────────────────────────────────

    def generate_certificate_of_service(
        self,
        method: str = "first-class mail",
        recipient: str = "Tiffany Watson",
    ) -> str:
        """Generate certificate of service per MCR 2.107."""
        today = datetime.now().strftime("%B %d, %Y")
        return textwrap.dedent(f"""\
            CERTIFICATE OF SERVICE

            I, Andrew Pigors, hereby certify that on {today}, I served
            a true and correct copy of the foregoing document upon:

                {recipient}
                [Address on file with the Court]

            by {method}, postage prepaid, in accordance with MCR 2.107.

                                    ___________________________
                                    Andrew Pigors, Pro Se
                                    Muskegon, Michigan
                                    Date: {today}
        """)

    # ── Authority & Evidence Helpers ──────────────────────────────────

    def _query_authority(self, topic: str, limit: int = 10) -> List[Dict]:
        """Search auth_rules for governing authority on a topic.

        Uses a single UNION query combining LIKE + FTS for efficiency.
        """
        if not self.conn:
            return []
        results = _safe_query(
            self.conn,
            "SELECT rule_number, title, substr(full_text, 1, 800) as text "
            "FROM auth_rules WHERE rule_number LIKE ? OR title LIKE ? "
            "UNION "
            "SELECT rule_number, title, substr(full_text, 1, 800) as text "
            "FROM auth_rules WHERE rowid IN "
            "(SELECT rowid FROM auth_rules_fts WHERE auth_rules_fts MATCH ?) "
            "LIMIT ?",
            (f"%{topic}%", f"%{topic}%", topic, limit),
        )
        return results

    def _query_evidence(self, topic: str, limit: int = 10) -> List[Dict]:
        """Search evidence_quotes for supporting facts.

        Uses a single UNION query combining LIKE + FTS for efficiency.
        """
        if not self.conn:
            return []
        results = _safe_query(
            self.conn,
            "SELECT quote_text, speaker, legal_significance, evidence_category "
            "FROM evidence_quotes WHERE quote_text LIKE ? "
            "OR legal_significance LIKE ? "
            "UNION "
            "SELECT quote_text, speaker, legal_significance, evidence_category "
            "FROM evidence_quotes WHERE rowid IN "
            "(SELECT rowid FROM evidence_quotes_fts "
            "WHERE evidence_quotes_fts MATCH ?) LIMIT ?",
            (f"%{topic}%", f"%{topic}%", topic, limit),
        )
        return results

    def _query_judicial_violations(self, limit: int = 20) -> List[Dict]:
        """Retrieve judicial violation findings."""
        if not self.conn:
            return []
        return _safe_query(
            self.conn,
            "SELECT * FROM judicial_violations ORDER BY severity DESC LIMIT ?",
            (limit,),
        )

    def _query_vehicles(self, lane: Optional[str] = None) -> List[Dict]:
        """Retrieve procedural vehicles."""
        if not self.conn:
            return []
        if lane:
            return _safe_query(
                self.conn,
                "SELECT * FROM vehicles WHERE case_lane = ?",
                (lane,),
            )
        return _safe_query(self.conn, "SELECT * FROM vehicles")

    # ── Citation Verification ────────────────────────────────────────

    def verify_all_citations(self, text: str) -> Dict:
        """Extract all MCR/MCL/MRE citations from text and verify each
        against auth_rules and rules_text DB tables.
        Returns: {verified: [...], unverified: [...], total: int}.

        Uses batch pre-loading for efficiency instead of per-citation COUNT queries.
        """
        cite_re = re.compile(
            r'(MCR|MCL|MRE)\s+(\d+(?:\.\d+)+(?:\([A-Za-z0-9]+\))*)'
        )
        citations = cite_re.findall(text)
        verified, unverified = [], []

        if not self.conn:
            return {"verified": [], "unverified": [f"{t} {n}" for t, n in citations],
                    "total": len(citations)}

        # Batch pre-load: fetch all rule_numbers from auth_rules and rules_text once
        auth_numbers = set()
        rules_numbers = set()
        try:
            for row in _safe_query(self.conn, "SELECT rule_number FROM auth_rules", ()):
                auth_numbers.add(str(row.get("rule_number", "")))
        except Exception:
            pass
        try:
            for row in _safe_query(self.conn, "SELECT rule FROM rules_text", ()):
                rules_numbers.add(str(row.get("rule", "")))
        except Exception:
            pass

        for cite_type, cite_num in citations:
            base_num = cite_num.split("(")[0]
            full_cite = f"{cite_type} {cite_num}"
            found = any(base_num in rn for rn in auth_numbers) or \
                    any(base_num in rn for rn in rules_numbers)
            (verified if found else unverified).append(full_cite)

        return {
            "verified": list(set(verified)),
            "unverified": list(set(unverified)),
            "total": len(citations),
        }

    # ── Post-Generation Validation ────────────────────────────────────

    def _post_generation_validate(self, text: str) -> Dict:
        """Run full validation on generated filing text: placeholders,
        citations, Certificate of Service, and signature block.
        Returns: {score: int, issues: [str], citation_audit: dict}."""
        issues: List[str] = []
        score = 100

        # 1. Placeholder detection
        placeholder_re = re.compile(
            r'\[(?:DATE|NAME|CASE NUMBER|ADDRESS|PHONE|EMAIL|CITY|STATE|ZIP'
            r'|COURT|JUDGE|SPECIFY[^\]]*|STATE FACTS|ISSUE \d+'
            r'|SWORN STATEMENT[^\]]*|APPLICATION OF LAW TO FACTS'
            r'|QUESTION PRESENTED[^\]]*|DOCUMENT BEING RESPONDED TO'
            r'|FOC RECOMMENDATION[^\]]*|ORDER PROVISION[^\]]*'
            r'|MATTER TO BE HEARD|FIRST ARGUMENT HEADING'
            r'|Cases will be auto-populated[^\]]*'
            r'|MCR references will be auto-populated[^\]]*'
            r'|MCL references will be auto-populated[^\]]*'
            r'|Detailed factual recitation[^\]]*'
            r'|IRAC[^\]]*|Apply IRAC[^\]]*'
            r'|Address on file|City, State ZIP)\]', re.IGNORECASE
        )
        placeholders = placeholder_re.findall(text)
        if placeholders:
            issues.append(f"Found {len(placeholders)} placeholder(s)")
            score -= len(placeholders) * 5

        # 2. Certificate of Service (MCR 2.107) — mandatory
        if "CERTIFICATE OF SERVICE" not in text:
            if "ORDER" not in text.upper()[:200]:
                issues.append("MISSING Certificate of Service (MCR 2.107 requires it)")
                score -= 20

        # 3. Signature block
        if "Respectfully submitted" not in text and "IT IS SO ORDERED" not in text:
            issues.append("Missing signature block")
            score -= 10

        # 4. Citation audit
        citation_audit = self.verify_all_citations(text)
        if citation_audit["unverified"]:
            issues.append(
                f"{len(citation_audit['unverified'])} unverified citation(s): "
                f"{', '.join(citation_audit['unverified'][:5])}"
            )
            score -= len(citation_audit["unverified"]) * 3

        return {
            "score": max(0, min(100, score)),
            "issues": issues,
            "citation_audit": citation_audit,
        }

    # ── MSC Package ───────────────────────────────────────────────────

    def generate_msc_package(self) -> Dict:
        """Generate complete MSC original action filing package:
        complaint, supporting brief, appendix, emergency application,
        certificate of service, proposed order."""
        caption = self.generate_caption("MSC", "______")
        cert = self.generate_certificate_of_service()
        today = datetime.now().strftime("%B %d, %Y")

        # Pull authority
        mcr_7306 = self._query_authority("7.306", limit=5)
        mcr_7312 = self._query_authority("7.312", limit=3)
        mcr_7315 = self._query_authority("7.315", limit=3)
        mcr_3302 = self._query_authority("3.302", limit=3)

        # Pull judicial violations for evidence
        violations = self._query_judicial_violations(limit=20)
        violation_summary = []
        for v in violations:
            violation_summary.append({
                "judge": v.get("judge_name", ""),
                "canon": v.get("canon_number", ""),
                "description": v.get("violation_description", ""),
                "severity": v.get("severity", ""),
            })

        # Pull supporting evidence
        evidence = self._query_evidence("due process custody parenting", limit=10)

        complaint = textwrap.dedent(f"""\
            {caption}

            COMPLAINT FOR SUPERINTENDING CONTROL AND MANDAMUS

            COMES NOW Plaintiff Andrew Pigors, pro se, and respectfully files
            this Complaint for Superintending Control and/or Mandamus pursuant to
            MCR 7.306 and MCL 600.1701, and states as follows:

            JURISDICTION AND AUTHORITY

            1.  This Court has original jurisdiction pursuant to Const 1963,
                art 6, § 4 and MCR 7.306.

            2.  Superintending control is warranted where a lower court has
                failed to perform a clear legal duty. MCR 3.302; MCL 600.1701.

            STATEMENT OF FACTS

            3.  Plaintiff is the natural father of the minor child(ren) at issue
                in Case No. 2024-001507-DC, 14th Circuit Court, Muskegon County.

            4.  The Honorable Jenny L. McNeill has presided over this matter and
                has committed multiple procedural and substantive violations of
                Michigan Court Rules, due process, and judicial conduct canons.

            5.  Parent-child separation has persisted for 329+ days without
                constitutionally adequate process.

            VIOLATIONS SUMMARY

            {self._format_violations_section(violation_summary)}

            PRAYER FOR RELIEF

            WHEREFORE, Plaintiff respectfully requests that this Court:

            a.  Issue an order of superintending control directing the 14th
                Circuit Court to comply with Michigan Court Rules;
            b.  Issue a writ of mandamus directing immediate restoration of
                parenting time pending proper adjudication;
            c.  Grant such other relief as this Court deems just and proper.

                                        Respectfully submitted,

                                        ___________________________
                                        Andrew Pigors, Pro Se
                                        Muskegon, Michigan
                                        Date: {today}
        """)

        brief = textwrap.dedent(f"""\
            {caption}

            BRIEF IN SUPPORT OF COMPLAINT FOR
            SUPERINTENDING CONTROL AND MANDAMUS
            (MCR 7.312)

            STATEMENT OF QUESTIONS PRESENTED

            I.   Whether the 14th Circuit Court committed clear error requiring
                 superintending control when it failed to comply with mandatory
                 procedural requirements of the Michigan Court Rules.

            II.  Whether mandamus is warranted where a lower court judge has
                 failed to perform a clear legal duty.

            STATEMENT OF FACTS

            [Facts supported by record citations — see appendix]

            ARGUMENT

            I.   SUPERINTENDING CONTROL IS WARRANTED

                 Superintending control is an extraordinary remedy available when
                 a lower court has failed to perform a clear legal duty.
                 MCR 3.302; MCL 600.1701.

            II.  MANDAMUS SHOULD ISSUE

                 A writ of mandamus will issue where: (1) the party seeking the
                 writ has a clear legal right to performance of the duty sought;
                 (2) the defendant has a clear legal duty to perform; and (3)
                 the act is ministerial. Toan v Fluor, 2019.

            CONCLUSION

            For the foregoing reasons, Plaintiff respectfully requests that this
            Court grant the relief sought in the Complaint.

                                        Respectfully submitted,

                                        ___________________________
                                        Andrew Pigors, Pro Se
                                        Date: {today}
        """)

        emergency = textwrap.dedent(f"""\
            {caption}

            EMERGENCY APPLICATION FOR IMMEDIATE CONSIDERATION
            (MCR 7.315(C))

            Plaintiff Andrew Pigors respectfully moves this Court for immediate
            consideration of the accompanying Complaint for Superintending
            Control and Mandamus on an emergency basis pursuant to MCR 7.315(C).

            GROUNDS FOR EMERGENCY

            1.  Parent-child separation has persisted for 329+ days.
            2.  Irreparable harm to the parent-child bond is ongoing.
            3.  Constitutional due process rights are being violated daily.
            4.  No adequate remedy at law exists given the lower court's conduct.

                                        Respectfully submitted,

                                        ___________________________
                                        Andrew Pigors, Pro Se
                                        Date: {today}
        """)

        proposed_order = textwrap.dedent(f"""\
            {self.generate_caption("MSC", "______")}

            ORDER

            At a session of the Michigan Supreme Court, held at Lansing,
            Michigan, on _______________, 20___.

            PRESENT: [Justices]

            Having considered the Complaint for Superintending Control and
            Mandamus filed by Plaintiff Andrew Pigors, and being otherwise
            advised in the premises,

            IT IS HEREBY ORDERED that:

            1.  Superintending control is GRANTED;
            2.  The 14th Circuit Court for the County of Muskegon is directed
                to [specific relief];
            3.  [Additional provisions].

                                        ___________________________
                                        Chief Justice
        """)

        result = {
            "package_type": "MSC_original_action",
            "court": "MSC",
            "generated": datetime.now().isoformat(),
            "documents": {
                "complaint": complaint,
                "supporting_brief": brief,
                "emergency_application": emergency,
                "proposed_order": proposed_order,
                "certificate_of_service": cert,
            },
            "appendix_items": {
                "judicial_violations": violation_summary,
                "supporting_evidence": evidence,
            },
            "authority_cited": {
                "MCR_7.306": mcr_7306,
                "MCR_7.312": mcr_7312,
                "MCR_7.315": mcr_7315,
                "MCR_3.302": mcr_3302,
            },
            "document_count": 5,
        }
        # Post-generation validation on all documents
        all_text = "\n".join(str(v) for v in result["documents"].values())
        result["validation"] = self._post_generation_validate(all_text)
        return result

    def _format_violations_section(self, violations: List[Dict]) -> str:
        """Format violations into numbered paragraphs."""
        if not violations:
            return "    [No judicial violations found in database — verify data.]"
        lines = []
        for i, v in enumerate(violations[:10], start=6):
            desc = v.get("description", "N/A")
            canon = v.get("canon", "N/A")
            severity = v.get("severity", "N/A")
            lines.append(
                f"    {i}.  {desc}\n"
                f"        (Canon/Rule: {canon} | Severity: {severity})"
            )
        return "\n\n".join(lines)

    # ── Circuit Court Motion Package ──────────────────────────────────

    def generate_circuit_motion_package(self, motion_type: str) -> Dict:
        """Generate circuit court motion package.
        Types: 'emergency_restore_pt', 'disqualify', 'contempt',
               'compel_discovery'"""
        type_config = {
            "emergency_restore_pt": {
                "title": "EMERGENCY MOTION TO RESTORE PARENTING TIME",
                "rules": ["MCL 722.27a", "MCR 2.119"],
                "basis": "parenting time restoration",
            },
            "disqualify": {
                "title": "MOTION TO DISQUALIFY JUDGE",
                "rules": ["MCR 2.003(C)(1)", "MCJC Canon 2"],
                "basis": "judicial disqualification bias",
            },
            "contempt": {
                "title": "MOTION FOR CONTEMPT OF COURT",
                "rules": ["MCL 600.1701", "MCR 3.606"],
                "basis": "contempt violation court order",
            },
            "compel_discovery": {
                "title": "MOTION TO COMPEL DISCOVERY",
                "rules": ["MCR 2.313", "MCR 2.310"],
                "basis": "discovery compel production",
            },
        }

        config = type_config.get(motion_type)
        if not config:
            return {
                "error": f"Unknown motion type: {motion_type}",
                "valid_types": list(type_config.keys()),
            }

        case = CASES["custody"]
        caption = self.generate_caption("14th Circuit", case["number"])
        cert = self.generate_certificate_of_service()
        today = datetime.now().strftime("%B %d, %Y")

        # Pull authority for this motion type
        authority = []
        for rule in config["rules"]:
            authority.extend(self._query_authority(rule, limit=3))

        # Pull relevant evidence
        evidence = self._query_evidence(config["basis"], limit=8)

        motion = textwrap.dedent(f"""\
            {caption}

            {config['title']}

            COMES NOW Plaintiff Andrew Pigors, pro se, and respectfully moves
            this Honorable Court for an order granting the relief described
            herein, and in support thereof states:

            STATEMENT OF FACTS

            1.  This matter involves custody and parenting time for the minor
                child(ren) in Case No. {case['number']}.

            2.  Parent-child separation has persisted for 329+ days.

            3.  [Specific facts supporting this motion — to be completed
                 from evidence record]

            LEGAL AUTHORITY

            4.  [Authority section — rules: {', '.join(config['rules'])}]

            ARGUMENT

            5.  [IRAC analysis to be completed for each issue]

            RELIEF REQUESTED

            WHEREFORE, Plaintiff respectfully requests that this Court:

            a.  Grant Plaintiff's {config['title']};
            b.  Grant such other relief as this Court deems just and proper.

                                        Respectfully submitted,

                                        ___________________________
                                        Andrew Pigors, Pro Se
                                        Muskegon, Michigan
                                        Date: {today}
        """)

        brief_in_support = textwrap.dedent(f"""\
            {caption}

            BRIEF IN SUPPORT OF
            {config['title']}

            STATEMENT OF ISSUES

            I.   Whether Plaintiff is entitled to the relief sought in the
                 accompanying motion.

            STATEMENT OF FACTS

            [Facts with record citations]

            ARGUMENT

            [IRAC structure for each issue — cite {', '.join(config['rules'])}]

            CONCLUSION

            For the foregoing reasons, Plaintiff respectfully requests that this
            Court grant the accompanying motion.

                                        Respectfully submitted,

                                        ___________________________
                                        Andrew Pigors, Pro Se
                                        Date: {today}
        """)

        proposed_order = textwrap.dedent(f"""\
            {caption}

            ORDER GRANTING {config['title']}

            This matter having come before the Court on Plaintiff's
            {config['title']}, and the Court being otherwise advised,

            IT IS HEREBY ORDERED that Plaintiff's motion is GRANTED.

            [Specific provisions]

            IT IS SO ORDERED.

                                        ___________________________
                                        {JUDGE}
                                        Date: _______________
        """)

        result = {
            "package_type": f"circuit_motion_{motion_type}",
            "court": "14th Circuit",
            "case_number": case["number"],
            "motion_type": motion_type,
            "generated": datetime.now().isoformat(),
            "documents": {
                "motion": motion,
                "brief_in_support": brief_in_support,
                "proposed_order": proposed_order,
                "certificate_of_service": cert,
            },
            "authority_cited": authority,
            "supporting_evidence": evidence,
            "document_count": 4,
        }
        # Post-generation validation on all documents
        all_text = "\n".join(str(v) for v in result["documents"].values())
        result["validation"] = self._post_generation_validate(all_text)
        return result

    # ── COA Brief Package ─────────────────────────────────────────────

    def generate_coa_brief_package(self) -> Dict:
        """Generate COA appellant brief package per MCR 7.212.
        Case: COA 366810."""
        case_no = CASES["coa"]["number"]
        caption = self.generate_caption("COA", case_no)
        cert = self.generate_certificate_of_service()
        today = datetime.now().strftime("%B %d, %Y")

        # Pull MCR 7.212 requirements
        mcr_7212 = self._query_authority("7.212", limit=5)

        # Pull evidence for appeal issues
        evidence = self._query_evidence("appeal error custody", limit=10)

        # Pull judicial violations for issues on appeal
        violations = self._query_judicial_violations(limit=15)

        brief = textwrap.dedent(f"""\
            {caption}

            APPELLANT'S BRIEF ON APPEAL
            (MCR 7.212)

            STATEMENT OF JURISDICTION

            The Court of Appeals has jurisdiction pursuant to MCR 7.203(A).
            The order being appealed was entered on [date]. This claim of appeal
            was timely filed within 21 days per MCR 7.204(A)(1).

            STATEMENT OF QUESTIONS PRESENTED

            I.   Whether the trial court committed clear error when it
                 [issue 1].

            II.  Whether the trial court abused its discretion when it
                 [issue 2].

            III. Whether Plaintiff's due process rights were violated when
                 [issue 3].

            STATEMENT OF FACTS

            [Comprehensive factual narrative with record citations]

            STANDARD OF REVIEW

            Custody decisions are reviewed for an abuse of discretion. Findings
            of fact are reviewed for clear error. Questions of law are reviewed
            de novo. MCL 722.28; Berger v Berger, 277 Mich App 700, 705 (2008).

            ARGUMENT

            I.   [IRAC for Issue I]

            II.  [IRAC for Issue II]

            III. [IRAC for Issue III]

            RELIEF REQUESTED

            For the foregoing reasons, Appellant respectfully requests that this
            Court reverse the trial court's order(s) and remand for proceedings
            consistent with this Court's opinion.

                                        Respectfully submitted,

                                        ___________________________
                                        Andrew Pigors, Pro Se
                                        Appellant
                                        Muskegon, Michigan
                                        Date: {today}

            WORD COUNT CERTIFICATION

            I certify that this brief contains fewer than 16,000 words,
            excluding the table of contents, table of authorities, caption
            page, and signature block, in compliance with MCR 7.212(B).

                                        ___________________________
                                        Andrew Pigors
        """)

        appendix_items = {
            "lower_court_orders": "[Orders appealed from — to be attached]",
            "relevant_docket_entries": "[Docket entries — to be attached]",
            "key_transcript_excerpts": "[Transcript excerpts — to be attached]",
            "judicial_violations": [dict(v) for v in violations[:10]]
            if violations
            else [],
        }

        proof_of_service = textwrap.dedent(f"""\
            PROOF OF SERVICE

            STATE OF MICHIGAN  )
                                ) ss.
            COUNTY OF MUSKEGON )

            Andrew Pigors, being duly sworn, deposes and says that on
            {today}, he served a true copy of the Appellant's Brief on Appeal,
            Appendix, and this Proof of Service upon:

                {DEFENDANT}
                [Address on file with the Court]

            by first-class mail, postage prepaid.

                                        ___________________________
                                        Andrew Pigors

            Subscribed and sworn to before me this ____ day of
            _______________, 20___.

                                        ___________________________
                                        Notary Public
                                        My commission expires: ____________
        """)

        result = {
            "package_type": "COA_appellant_brief",
            "court": "COA",
            "case_number": case_no,
            "generated": datetime.now().isoformat(),
            "documents": {
                "appellant_brief": brief,
                "proof_of_service": proof_of_service,
            },
            "appendix": appendix_items,
            "authority_cited": mcr_7212,
            "supporting_evidence": evidence,
            "limits": PAGE_LIMITS["COA_brief"],
            "document_count": 3,
        }
        # Post-generation validation
        all_text = "\n".join(str(v) for v in result["documents"].values())
        result["validation"] = self._post_generation_validate(all_text)
        return result

    # ── Federal § 1983 Complaint Package ──────────────────────────────

    def generate_federal_complaint_package(self) -> Dict:
        """Generate 42 USC § 1983 complaint package for USDC WD MI."""
        caption = self.generate_caption("USDC_WD_MI", "1:____-cv-_____")
        cert = self.generate_certificate_of_service(
            method="CM/ECF electronic filing"
        )
        today = datetime.now().strftime("%B %d, %Y")

        # Pull due process authority
        due_process = self._query_authority("due process", limit=5)
        evidence = self._query_evidence("due process rights constitutional", limit=8)

        complaint = textwrap.dedent(f"""\
            {caption}

            COMPLAINT UNDER 42 U.S.C. § 1983

            Plaintiff Andrew Pigors, pro se, brings this action pursuant to
            42 U.S.C. § 1983 for deprivation of rights under color of state
            law, and alleges as follows:

            PARTIES

            1.  Plaintiff Andrew Pigors is a citizen and resident of Muskegon
                County, Michigan.

            2.  Defendant Tiffany Watson (fka Pigors) is a citizen and resident
                of Muskegon County, Michigan.

            3.  [Additional defendants as applicable — state actors]

            JURISDICTION AND VENUE

            4.  This Court has federal question jurisdiction under 28 U.S.C.
                § 1331 and 42 U.S.C. § 1983.

            5.  Venue is proper in the Western District of Michigan under
                28 U.S.C. § 1391(b) because the events giving rise to this
                claim occurred in Muskegon County, Michigan.

            STATEMENT OF FACTS

            6.  [Factual narrative with specificity per FRCP 8]

            7.  Parent-child separation has persisted for 329+ days without
                constitutionally adequate process.

            CLAIMS FOR RELIEF

            COUNT I — DEPRIVATION OF DUE PROCESS (14TH AMENDMENT)

            8.  Plaintiff has a fundamental liberty interest in the care,
                custody, and control of his child(ren). Troxel v Granville,
                530 U.S. 57 (2000).

            9.  Defendants, acting under color of state law, deprived Plaintiff
                of this fundamental right without due process of law.

            PRAYER FOR RELIEF

            WHEREFORE, Plaintiff respectfully requests:

            a.  A declaratory judgment that Defendants violated Plaintiff's
                constitutional rights;
            b.  Injunctive relief restoring Plaintiff's parental rights;
            c.  Compensatory damages;
            d.  Costs and such further relief as this Court deems just.

                                        Respectfully submitted,

                                        ___________________________
                                        Andrew Pigors, Pro Se
                                        Muskegon, Michigan
                                        Date: {today}
        """)

        civil_cover_sheet = textwrap.dedent(f"""\
            CIVIL COVER SHEET (JS-44)

            Plaintiff: Andrew Pigors
            Defendant: Tiffany Watson (fka Pigors), et al.
            Attorneys: Pro Se
            County of Residence — Plaintiff: Muskegon County, MI
            Basis of Jurisdiction: Federal Question (28 U.S.C. § 1331)
            Nature of Suit: 440 — Other Civil Rights
            Cause of Action: 42 U.S.C. § 1983
            Requested in Complaint: Declaratory, Injunctive, Damages
        """)

        ifp_motion = textwrap.dedent(f"""\
            {caption}

            MOTION TO PROCEED IN FORMA PAUPERIS
            (28 U.S.C. § 1915)

            Plaintiff Andrew Pigors respectfully moves this Court for leave to
            proceed in forma pauperis without prepayment of fees and costs,
            pursuant to 28 U.S.C. § 1915(a).

            In support thereof, Plaintiff states:

            1.  Plaintiff is unable to pay the costs of these proceedings.
            2.  Plaintiff's financial affidavit is attached hereto.

            WHEREFORE, Plaintiff requests that this Court grant leave to
            proceed in forma pauperis.

                                        Respectfully submitted,

                                        ___________________________
                                        Andrew Pigors, Pro Se
                                        Date: {today}
        """)

        summons = textwrap.dedent(f"""\
            UNITED STATES DISTRICT COURT
            WESTERN DISTRICT OF MICHIGAN

            SUMMONS IN A CIVIL ACTION

            Case Number: 1:____-cv-_____

            TO: Tiffany Watson (fka Pigors)
                [Address]

            A lawsuit has been filed against you. You must respond within
            21 days after service (60 days if served outside the judicial
            district), or a default judgment may be entered against you.

            Clerk of Court: ___________________________
            Date: _______________
        """)

        result = {
            "package_type": "federal_1983_complaint",
            "court": "USDC_WD_MI",
            "generated": datetime.now().isoformat(),
            "documents": {
                "complaint": complaint,
                "civil_cover_sheet": civil_cover_sheet,
                "ifp_motion": ifp_motion,
                "summons": summons,
                "certificate_of_service": cert,
            },
            "authority_cited": due_process,
            "supporting_evidence": evidence,
            "document_count": 5,
        }
        # Post-generation validation on all documents
        all_text = "\n".join(str(v) for v in result["documents"].values())
        result["validation"] = self._post_generation_validate(all_text)
        return result

    # ── JTC Complaint Package ─────────────────────────────────────────

    def generate_jtc_complaint_package(self) -> Dict:
        """Generate JTC complaint package per MCR 9.211."""
        caption = self.generate_caption("JTC", "______")
        today = datetime.now().strftime("%B %d, %Y")

        # Pull MCR 9.211 and MCJC canons
        mcr_9211 = self._query_authority("9.211", limit=5)
        mcjc = self._query_authority("canon", limit=5)

        # Pull judicial violations
        violations = self._query_judicial_violations(limit=25)
        violation_entries = []
        for v in violations:
            violation_entries.append({
                "judge": v.get("judge_name", ""),
                "canon": v.get("canon_number", ""),
                "description": v.get("violation_description", ""),
                "severity": v.get("severity", ""),
            })

        # Pull supporting evidence
        evidence = self._query_evidence("judicial misconduct bias", limit=10)

        complaint = textwrap.dedent(f"""\
            {caption}

            FORMAL COMPLAINT AGAINST
            HON. JENNY L. McNEILL
            (MCR 9.211)

            Complainant Andrew Pigors respectfully submits this formal
            complaint against the Honorable Jenny L. McNeill, Judge of the
            14th Circuit Court for the County of Muskegon, and states:

            COMPLAINANT INFORMATION

            Name:    Andrew Pigors
            Address: Muskegon, Michigan
            Phone:   [On file]

            RESPONDENT JUDGE

            Name:    Hon. Jenny L. McNeill
            Court:   14th Circuit Court, Muskegon County
            Cases:   2024-001507-DC; 2023-5907-PP

            SPECIFIC ALLEGATIONS

            {self._format_jtc_allegations(violation_entries)}

            SUPPORTING DOCUMENTATION

            See attached Evidence Index and Exhibits.

            PRAYER FOR RELIEF

            Complainant respectfully requests the Judicial Tenure Commission
            investigate the conduct described herein and take appropriate
            disciplinary action pursuant to MCR 9.220 et seq.

                                        Respectfully submitted,

                                        ___________________________
                                        Andrew Pigors
                                        Muskegon, Michigan
                                        Date: {today}
        """)

        evidence_index = self._build_evidence_index(evidence, violations)

        return {
            "package_type": "JTC_complaint",
            "court": "JTC",
            "target_judge": JUDGE,
            "generated": datetime.now().isoformat(),
            "documents": {
                "formal_complaint": complaint,
                "evidence_index": evidence_index,
            },
            "violations_cited": violation_entries,
            "authority_cited": {
                "MCR_9.211": mcr_9211,
                "MCJC_canons": mcjc,
            },
            "supporting_evidence": evidence,
            "document_count": 2,
        }

    def _format_jtc_allegations(self, violations: List[Dict]) -> str:
        """Format violations into JTC allegation paragraphs."""
        if not violations:
            return "    [No judicial violations found in database — verify data.]"
        lines = []
        for i, v in enumerate(violations[:15], start=1):
            desc = v.get("description", "N/A")
            canon = v.get("canon", "N/A")
            severity = v.get("severity", "N/A")
            lines.append(
                f"    {i}.  {desc}\n"
                f"        Applicable standard: {canon}\n"
                f"        Severity: {severity}"
            )
        return "\n\n".join(lines)

    def _build_evidence_index(
        self, evidence: List[Dict], violations: List[Dict]
    ) -> str:
        """Build an evidence index for supporting exhibits."""
        lines = ["EVIDENCE INDEX", "=" * 60, ""]
        lines.append("EXHIBIT  |  DESCRIPTION")
        lines.append("-" * 60)
        idx = 1
        for v in violations[:15]:
            desc = v.get("violation_description", v.get("description", "N/A"))
            lines.append(f"  {idx:3d}    |  Judicial Violation: {str(desc)[:60]}")
            idx += 1
        for e in evidence[:10]:
            qt = str(e.get("quote_text", "N/A"))[:60]
            lines.append(f"  {idx:3d}    |  Evidence: {qt}")
            idx += 1
        lines.append("-" * 60)
        lines.append(f"Total exhibits: {idx - 1}")
        return "\n".join(lines)

    # ── Compliance Checker ────────────────────────────────────────────

    def check_compliance(self, document_text: str, court: str) -> Dict:
        """Check a document for MCR compliance.
        Returns: score (0-100), issues list, suggestions."""
        issues = []
        suggestions = []
        score = 100

        text = document_text or ""

        # 1. Check for certificate of service
        if "certificate of service" not in text.lower():
            issues.append("Missing Certificate of Service (MCR 2.107)")
            suggestions.append("Add Certificate of Service at the end of the document.")
            score -= 15

        # 2. Check for case caption
        if "case no" not in text.lower() and "case number" not in text.lower():
            issues.append("Missing case number in caption (MCR 2.113)")
            suggestions.append("Ensure caption includes Case No.")
            score -= 10

        # 3. Check for signature block
        if "respectfully submitted" not in text.lower():
            issues.append("Missing signature block")
            suggestions.append("Add signature block with name, address, date.")
            score -= 10

        # 4. Check for date
        date_pattern = re.compile(
            r"\b(?:January|February|March|April|May|June|July|August|"
            r"September|October|November|December)\s+\d{1,2},?\s+\d{4}\b"
        )
        if not date_pattern.search(text):
            issues.append("No date found in document")
            suggestions.append("Include the filing date.")
            score -= 5

        # 5. Word count check
        word_count = len(text.split())
        limits = PAGE_LIMITS.get(f"{court}_brief", PAGE_LIMITS.get("circuit_motion"))
        if limits and word_count > limits["words"]:
            issues.append(
                f"Word count ({word_count}) exceeds limit "
                f"({limits['words']}) per {limits['rule']}"
            )
            suggestions.append("Reduce document length to comply with word limits.")
            score -= 15

        # 6. Check for legal citations
        mcr_cites = re.findall(r"MCR\s+\d+\.\d+", text, re.I)
        mcl_cites = re.findall(r"MCL\s+\d+\.\d+", text, re.I)
        if not mcr_cites and not mcl_cites:
            issues.append("No MCR or MCL citations found")
            suggestions.append(
                "Add legal authority citations to support every assertion."
            )
            score -= 20

        # 7. Check for IRAC structure indicators
        irac_keywords = ["issue", "rule", "application", "conclusion", "argument"]
        found_irac = sum(1 for kw in irac_keywords if kw in text.lower())
        if found_irac < 2:
            issues.append("Document may lack IRAC structure")
            suggestions.append(
                "Structure arguments using Issue, Rule, Application, Conclusion."
            )
            score -= 10

        # 8. Check for prayer for relief
        if (
            "prayer for relief" not in text.lower()
            and "relief requested" not in text.lower()
            and "wherefore" not in text.lower()
        ):
            issues.append("Missing Prayer for Relief / WHEREFORE clause")
            suggestions.append("Add a specific relief request.")
            score -= 10

        # 9. Court-specific checks
        if court == "COA" and "standard of review" not in text.lower():
            issues.append("COA brief missing Standard of Review section (MCR 7.212)")
            suggestions.append("Add Standard of Review section.")
            score -= 10

        if court == "COA" and "jurisdiction" not in text.lower():
            issues.append("COA brief missing jurisdictional statement (MCR 7.212)")
            suggestions.append("Add Statement of Jurisdiction.")
            score -= 5

        score = max(0, score)

        return {
            "score": score,
            "court": court,
            "word_count": word_count,
            "citation_count": len(mcr_cites) + len(mcl_cites),
            "issues": issues,
            "suggestions": suggestions,
            "compliant": score >= 70,
        }

    # ── Package Status ────────────────────────────────────────────────

    def get_package_status(self) -> Dict:
        """Summary of all filing packages: ready, gaps, scores."""
        readiness = self.get_filing_readiness()
        packages = self.get_filing_inventory()

        ready = [r for r in readiness if r.get("total_score", 0) >= 70]
        needs_work = [r for r in readiness if r.get("total_score", 0) < 70]

        return {
            "total_readiness_entries": len(readiness),
            "total_inventory_entries": len(packages),
            "ready_to_file": [
                {
                    "vehicle": r.get("vehicle_name", ""),
                    "score": r.get("total_score", 0),
                    "strengths": r.get("strengths", ""),
                }
                for r in ready
            ],
            "needs_work": [
                {
                    "vehicle": r.get("vehicle_name", ""),
                    "score": r.get("total_score", 0),
                    "gaps": r.get("gaps", ""),
                }
                for r in needs_work
            ],
            "summary": (
                f"{len(ready)} packages ready to file, "
                f"{len(needs_work)} need additional work"
            ),
        }


# ── Self Test ─────────────────────────────────────────────────────────
def self_test() -> Dict:
    """Run self-test to verify skill functionality."""
    results = {
        "skill": "filing_package_generator",
        "timestamp": datetime.now().isoformat(),
        "tests": {},
        "passed": 0,
        "failed": 0,
    }

    gen = FilingPackageGenerator()

    # Test 1: DB connection
    try:
        connected = gen.conn is not None
        results["tests"]["db_connection"] = {
            "passed": connected,
            "detail": "Connected" if connected else "Failed",
        }
        results["passed" if connected else "failed"] += 1
    except Exception as e:
        results["tests"]["db_connection"] = {"passed": False, "detail": str(e)}
        results["failed"] += 1

    # Test 2: Caption generation
    try:
        caption = gen.generate_caption("14th Circuit", "2024-001507-DC")
        ok = "ANDREW PIGORS" in caption and "2024-001507-DC" in caption
        results["tests"]["caption_generation"] = {
            "passed": ok,
            "detail": f"Length: {len(caption)} chars",
        }
        results["passed" if ok else "failed"] += 1
    except Exception as e:
        results["tests"]["caption_generation"] = {"passed": False, "detail": str(e)}
        results["failed"] += 1

    # Test 3: Caption for each court
    for court in COURT_INFO:
        try:
            c = gen.generate_caption(court, "TEST-001")
            ok = len(c) > 50
            results["tests"][f"caption_{court}"] = {
                "passed": ok,
                "detail": f"{court}: {len(c)} chars",
            }
            results["passed" if ok else "failed"] += 1
        except Exception as e:
            results["tests"][f"caption_{court}"] = {"passed": False, "detail": str(e)}
            results["failed"] += 1

    # Test 4: Certificate of service
    try:
        cert = gen.generate_certificate_of_service()
        ok = "MCR 2.107" in cert and "Andrew Pigors" in cert
        results["tests"]["certificate_of_service"] = {
            "passed": ok,
            "detail": f"Length: {len(cert)} chars",
        }
        results["passed" if ok else "failed"] += 1
    except Exception as e:
        results["tests"]["certificate_of_service"] = {
            "passed": False,
            "detail": str(e),
        }
        results["failed"] += 1

    # Test 5: Filing readiness query
    try:
        readiness = gen.get_filing_readiness()
        ok = isinstance(readiness, list)
        results["tests"]["filing_readiness"] = {
            "passed": ok,
            "detail": f"Rows: {len(readiness)}",
        }
        results["passed" if ok else "failed"] += 1
    except Exception as e:
        results["tests"]["filing_readiness"] = {"passed": False, "detail": str(e)}
        results["failed"] += 1

    # Test 6: Filing inventory query
    try:
        inv = gen.get_filing_inventory()
        ok = isinstance(inv, list)
        results["tests"]["filing_inventory"] = {
            "passed": ok,
            "detail": f"Rows: {len(inv)}",
        }
        results["passed" if ok else "failed"] += 1
    except Exception as e:
        results["tests"]["filing_inventory"] = {"passed": False, "detail": str(e)}
        results["failed"] += 1

    # Test 7: Compliance checker
    try:
        sample = (
            "Case No. 2024-001507-DC\n"
            "MCR 2.119 motion\n"
            "Respectfully submitted\n"
            "Certificate of Service\n"
            "MCR 2.107\n"
            "WHEREFORE\n"
            f"{datetime.now().strftime('%B %d, %Y')}\n"
        )
        check = gen.check_compliance(sample, "14th Circuit")
        ok = isinstance(check, dict) and "score" in check
        results["tests"]["compliance_checker"] = {
            "passed": ok,
            "detail": f"Score: {check.get('score', 'N/A')}",
        }
        results["passed" if ok else "failed"] += 1
    except Exception as e:
        results["tests"]["compliance_checker"] = {"passed": False, "detail": str(e)}
        results["failed"] += 1

    # Test 8: Package status
    try:
        status = gen.get_package_status()
        ok = isinstance(status, dict) and "summary" in status
        results["tests"]["package_status"] = {
            "passed": ok,
            "detail": status.get("summary", "N/A"),
        }
        results["passed" if ok else "failed"] += 1
    except Exception as e:
        results["tests"]["package_status"] = {"passed": False, "detail": str(e)}
        results["failed"] += 1

    gen.close()

    total = results["passed"] + results["failed"]
    results["total"] = total
    results["success_rate"] = (
        f"{results['passed']}/{total} ({results['passed']*100//total}%)"
        if total
        else "0/0"
    )

    return results


# ── CLI ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Filing Package Generator Skill")
        print("Usage:")
        print("  python filing_package_generator.py self_test")
        print("  python filing_package_generator.py status")
        print("  python filing_package_generator.py readiness [vehicle]")
        print("  python filing_package_generator.py inventory [lane] [status]")
        print("  python filing_package_generator.py caption <court> <case_no>")
        print("  python filing_package_generator.py cert")
        print("  python filing_package_generator.py msc")
        print("  python filing_package_generator.py circuit <motion_type>")
        print("  python filing_package_generator.py coa")
        print("  python filing_package_generator.py federal")
        print("  python filing_package_generator.py jtc")
        print("  python filing_package_generator.py compliance <court> <file>")
        sys.exit(0)

    cmd = sys.argv[1].lower()
    gen = FilingPackageGenerator()

    try:
        if cmd == "self_test":
            cycle_json(self_test())

        elif cmd == "status":
            cycle_json(gen.get_package_status())

        elif cmd == "readiness":
            vehicle = sys.argv[2] if len(sys.argv) > 2 else None
            cycle_json(gen.get_filing_readiness(vehicle))

        elif cmd == "inventory":
            lane = sys.argv[2] if len(sys.argv) > 2 else None
            status = sys.argv[3] if len(sys.argv) > 3 else None
            cycle_json(gen.get_filing_inventory(lane, status))

        elif cmd == "caption":
            court = sys.argv[2] if len(sys.argv) > 2 else "14th Circuit"
            case_no = sys.argv[3] if len(sys.argv) > 3 else "2024-001507-DC"
            print(gen.generate_caption(court, case_no))

        elif cmd == "cert":
            print(gen.generate_certificate_of_service())

        elif cmd == "msc":
            cycle_json(gen.generate_msc_package())

        elif cmd == "circuit":
            mtype = sys.argv[2] if len(sys.argv) > 2 else "emergency_restore_pt"
            cycle_json(gen.generate_circuit_motion_package(mtype))

        elif cmd == "coa":
            cycle_json(gen.generate_coa_brief_package())

        elif cmd == "federal":
            cycle_json(gen.generate_federal_complaint_package())

        elif cmd == "jtc":
            cycle_json(gen.generate_jtc_complaint_package())

        elif cmd == "compliance":
            court = sys.argv[2] if len(sys.argv) > 2 else "14th Circuit"
            fpath = sys.argv[3] if len(sys.argv) > 3 else None
            if fpath and Path(fpath).exists():
                text = Path(fpath).read_text(encoding="utf-8", errors="replace")
            else:
                text = sys.stdin.read() if not sys.stdin.isatty() else ""
            cycle_json(gen.check_compliance(text, court))

        else:
            print(f"Unknown command: {cmd}", file=sys.stderr)
            sys.exit(1)

    finally:
        gen.close()
