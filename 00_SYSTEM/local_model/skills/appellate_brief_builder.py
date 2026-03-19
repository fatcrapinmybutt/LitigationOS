#!/usr/bin/env python3
"""
MBP LitigationOS -- Appellate Brief Builder Skill
===================================================
Generate MCR 7.212-compliant appellate brief sections for
Pigors v. Watson, COA 366810 (appeal from 14th Circuit Court,
Muskegon County, Hon. Jenny L. McNeill).
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
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

WORD_LIMIT = 16_000  # MCR 7.212(B)


def _get_db() -> Optional[sqlite3.Connection]:
    """Get read-only DB connection."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA query_only=ON")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        return None


class AppellateBriefBuilder:
    """Generate appellate brief sections per MCR 7.212 for COA 366810."""

    CASE_CAPTION = "Pigors v. Watson"
    COA_DOCKET = "366810"
    LOWER_COURT = "14th Circuit Court, Muskegon County"
    LOWER_CASE = "2024-001507-DC"
    JUDGE = "Hon. Jenny L. McNeill"
    APPELLANT = "Andrew Pigors"
    APPELLEE = "Tiffany Watson"

    # MCR 7.212(C)(1) — Jurisdiction ──────────────────────────────────

    def generate_jurisdiction_statement(self) -> Dict:
        """Generate MCR 7.212(C)(1) jurisdiction statement."""
        conn = _get_db()
        if not conn:
            return {"error": "DB unavailable"}
        try:
            # Find jurisdiction authority
            auth_rows = []
            try:
                rows = conn.execute(
                    "SELECT rule_number, title, substr(full_text, 1, 500) as text "
                    "FROM auth_rules WHERE rule_number LIKE '%7.203%' "
                    "OR rule_number LIKE '%7.204%' LIMIT 5"
                ).fetchall()
                auth_rows = [dict(r) for r in rows]
            except Exception:
                pass

            return {
                "section": "JURISDICTIONAL STATEMENT",
                "mcr_ref": "MCR 7.212(C)(1)",
                "content": {
                    "court": "Michigan Court of Appeals",
                    "docket": self.COA_DOCKET,
                    "appeal_type": "Appeal of Right",
                    "basis": "MCR 7.203(A) — Appeal of right from final order of circuit court",
                    "lower_court": self.LOWER_COURT,
                    "lower_case": self.LOWER_CASE,
                    "judge": self.JUDGE,
                    "subject": "Custody / Parenting Time / Domestic Relations",
                },
                "authority": auth_rows,
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()

    # MCR 7.212(C)(4) — Issues Presented ──────────────────────────────

    def generate_issues_presented(
        self, issues: Optional[List[str]] = None
    ) -> Dict:
        """Generate MCR 7.212(C)(4) issues presented for review."""
        conn = _get_db()
        if not conn:
            return {"error": "DB unavailable"}
        try:
            # Pull claims / issues from DB
            db_claims = []
            try:
                rows = conn.execute(
                    "SELECT * FROM claims ORDER BY rowid LIMIT 50"
                ).fetchall()
                db_claims = [dict(r) for r in rows]
            except Exception:
                pass

            # Default issues if none provided
            if not issues:
                issues = [
                    "Whether the trial court abused its discretion in custody "
                    "determination by failing to properly weigh the best-interest "
                    "factors under MCL 722.23",
                    "Whether the trial court violated Plaintiff's due process "
                    "rights through ex parte communications and proceedings",
                    "Whether the trial court erred in its parenting time "
                    "determination under MCL 722.27a",
                    "Whether the trial court demonstrated bias requiring "
                    "disqualification under MCR 2.003",
                ]

            formatted = []
            for i, issue in enumerate(issues, 1):
                formatted.append({
                    "number": i,
                    "issue": issue,
                    "answer_below": "No",
                    "appellant_answer": "Yes",
                })

            return {
                "section": "ISSUES PRESENTED",
                "mcr_ref": "MCR 7.212(C)(4)",
                "issues": formatted,
                "db_claims": db_claims,
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()

    # MCR 7.212(C)(6) — Statement of Facts ────────────────────────────

    def generate_statement_of_facts(self) -> Dict:
        """Generate MCR 7.212(C)(6) chronological statement of facts."""
        conn = _get_db()
        if not conn:
            return {"error": "DB unavailable"}
        try:
            # Timeline events
            timeline = []
            try:
                rows = conn.execute(
                    "SELECT * FROM master_timeline ORDER BY rowid LIMIT 300"
                ).fetchall()
                timeline = [dict(r) for r in rows]
            except Exception:
                pass

            # Evidence quotes
            evidence = []
            try:
                rows = conn.execute(
                    "SELECT quote_text, speaker, legal_significance, "
                    "evidence_category, date_ref "
                    "FROM evidence_quotes "
                    "WHERE legal_significance IS NOT NULL "
                    "AND legal_significance != '' "
                    "ORDER BY rowid LIMIT 100"
                ).fetchall()
                evidence = [dict(r) for r in rows]
            except Exception:
                pass

            # Docket events
            docket = []
            try:
                rows = conn.execute(
                    "SELECT * FROM docket_events ORDER BY event_date_iso"
                ).fetchall()
                docket = [dict(r) for r in rows]
            except Exception:
                pass

            return {
                "section": "STATEMENT OF FACTS",
                "mcr_ref": "MCR 7.212(C)(6)",
                "note": "Facts must cite to lower court record with page references",
                "timeline_events": len(timeline),
                "evidence_items": len(evidence),
                "docket_events": len(docket),
                "timeline": timeline,
                "evidence": evidence,
                "docket": docket,
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()

    # MCR 7.212(C)(7) — Argument (IRAC) ───────────────────────────────

    def generate_argument_section(self, issue: str) -> Dict:
        """Generate MCR 7.212(C)(7) IRAC argument for one issue."""
        conn = _get_db()
        if not conn:
            return {"error": "DB unavailable"}
        try:
            # Find authority for this issue
            authority = []
            try:
                rows = conn.execute(
                    "SELECT rule_number, title, substr(full_text, 1, 500) as text "
                    "FROM auth_rules WHERE rowid IN "
                    "(SELECT rowid FROM auth_rules_fts "
                    " WHERE auth_rules_fts MATCH ?) LIMIT 15",
                    (issue,),
                ).fetchall()
                authority = [dict(r) for r in rows]
            except Exception:
                pass

            # Citations
            citations = []
            try:
                rows = conn.execute(
                    "SELECT citation, cite_type, substr(context, 1, 300) as ctx "
                    "FROM master_citations WHERE citation LIKE ? "
                    "OR context LIKE ? LIMIT 20",
                    (f"%{issue[:30]}%", f"%{issue[:30]}%"),
                ).fetchall()
                citations = [dict(r) for r in rows]
            except Exception:
                pass

            # Evidence
            evidence = []
            try:
                rows = conn.execute(
                    "SELECT rowid, quote_text, speaker, legal_significance "
                    "FROM evidence_quotes WHERE rowid IN "
                    "(SELECT rowid FROM evidence_quotes_fts "
                    " WHERE evidence_quotes_fts MATCH ?) LIMIT 20",
                    (issue,),
                ).fetchall()
                evidence = [dict(r) for r in rows]
            except Exception:
                pass

            return {
                "section": "ARGUMENT",
                "mcr_ref": "MCR 7.212(C)(7)",
                "issue": issue,
                "irac": {
                    "issue": f"Whether {issue}",
                    "rule": authority,
                    "application": evidence,
                    "conclusion": (
                        "The trial court's action constitutes reversible error "
                        "requiring remand with corrective instructions."
                    ),
                },
                "supporting_citations": citations,
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()

    # Standard of Review ───────────────────────────────────────────────

    def generate_standard_of_review(self, issue: str) -> Dict:
        """Identify the correct standard of review for an issue."""
        issue_lower = issue.lower()

        # Map issues to standards
        if any(kw in issue_lower for kw in ["custody", "parenting", "best interest"]):
            standard = "Abuse of Discretion"
            explanation = (
                "Custody decisions are reviewed for abuse of discretion. "
                "Findings of fact are reviewed for clear error. "
                "MCL 722.28; Berger v Berger, 277 Mich App 700, 705 (2008)."
            )
        elif any(kw in issue_lower for kw in ["due process", "constitutional"]):
            standard = "De Novo"
            explanation = (
                "Constitutional questions including due process are reviewed "
                "de novo. In re Contempt of Henry, 282 Mich App 656, 668 (2009)."
            )
        elif any(kw in issue_lower for kw in ["bias", "disqualification", "recusal"]):
            standard = "Abuse of Discretion"
            explanation = (
                "A trial court's decision on a motion for disqualification is "
                "reviewed for abuse of discretion. MCR 2.003(D); "
                "Cain v Dep't of Corrections, 451 Mich 470, 497 (1996)."
            )
        elif any(kw in issue_lower for kw in ["evidence", "admissibility", "hearsay"]):
            standard = "Abuse of Discretion"
            explanation = (
                "Evidentiary rulings are reviewed for abuse of discretion. "
                "Craig v Oakwood Hosp, 471 Mich 67, 76 (2004)."
            )
        elif any(kw in issue_lower for kw in ["fact", "finding", "credibility"]):
            standard = "Clear Error"
            explanation = (
                "Findings of fact are reviewed for clear error. A finding is "
                "clearly erroneous when the reviewing court is left with a "
                "definite and firm conviction that a mistake was made. "
                "MCR 2.613(C); In re Mason, 486 Mich 142, 152 (2010)."
            )
        else:
            standard = "De Novo / Abuse of Discretion"
            explanation = (
                "Questions of law are reviewed de novo; discretionary decisions "
                "for abuse of discretion; factual findings for clear error."
            )

        return {
            "issue": issue,
            "standard_of_review": standard,
            "explanation": explanation,
        }

    # MCR 7.212(C)(8) — Relief Requested ──────────────────────────────

    def generate_relief_requested(self) -> Dict:
        """Generate MCR 7.212(C)(8) specific relief requested."""
        return {
            "section": "RELIEF REQUESTED",
            "mcr_ref": "MCR 7.212(C)(8)",
            "relief": [
                {
                    "number": 1,
                    "request": (
                        "Reverse the trial court's custody and parenting time "
                        "orders entered in Case No. 2024-001507-DC"
                    ),
                },
                {
                    "number": 2,
                    "request": (
                        "Remand to a different judge pursuant to MCR 2.003 "
                        "due to demonstrated bias and procedural violations"
                    ),
                },
                {
                    "number": 3,
                    "request": (
                        "Order immediate restoration of Plaintiff-Appellant's "
                        "parenting time pending further proceedings"
                    ),
                },
                {
                    "number": 4,
                    "request": (
                        "Order a de novo best-interest hearing with proper "
                        "application of MCL 722.23 factors (a)-(l)"
                    ),
                },
                {
                    "number": 5,
                    "request": "Any further relief this Court deems just and equitable",
                },
            ],
        }

    # Full brief generation ────────────────────────────────────────────

    def generate_full_brief(self, issues: Optional[List[str]] = None) -> Dict:
        """Generate a complete appellant brief with all MCR 7.212 sections."""
        jurisdiction = self.generate_jurisdiction_statement()
        issues_presented = self.generate_issues_presented(issues)
        facts = self.generate_statement_of_facts()
        relief = self.generate_relief_requested()

        # Generate argument + standard of review for each issue
        issue_list = [
            i["issue"] for i in issues_presented.get("issues", [])
        ]
        arguments = []
        for iss in issue_list:
            arguments.append({
                "standard_of_review": self.generate_standard_of_review(iss),
                "argument": self.generate_argument_section(iss),
            })

        return {
            "caption": {
                "court": "STATE OF MICHIGAN COURT OF APPEALS",
                "docket": f"No. {self.COA_DOCKET}",
                "lower_court": self.LOWER_COURT,
                "lower_case": self.LOWER_CASE,
                "appellant": self.APPELLANT,
                "appellee": self.APPELLEE,
            },
            "sections": {
                "table_of_contents": "[ Generated from sections below ]",
                "index_of_authorities": "[ Generated from citations below ]",
                "jurisdiction": jurisdiction,
                "issues_presented": issues_presented,
                "statement_of_facts": facts,
                "arguments": arguments,
                "relief_requested": relief,
            },
            "mcr_compliance": {
                "rule": "MCR 7.212",
                "word_limit": WORD_LIMIT,
                "format": "12pt Times New Roman, double-spaced, 1-inch margins",
            },
        }

    # Utilities ─────────────────────────────────────────────────────────

    def check_word_count(self, text: str) -> Dict:
        """Verify text is within the 16,000 word limit per MCR 7.212(B)."""
        words = len(text.split())
        return {
            "word_count": words,
            "limit": WORD_LIMIT,
            "within_limit": words <= WORD_LIMIT,
            "remaining": max(0, WORD_LIMIT - words),
            "over_by": max(0, words - WORD_LIMIT),
        }

    def get_lower_court_record(self) -> Dict:
        """Retrieve relevant lower court proceedings from DB."""
        conn = _get_db()
        if not conn:
            return {"error": "DB unavailable"}
        try:
            docket = []
            try:
                rows = conn.execute(
                    "SELECT * FROM docket_events ORDER BY event_date_iso"
                ).fetchall()
                docket = [dict(r) for r in rows]
            except Exception:
                pass

            court_docs = []
            try:
                rows = conn.execute(
                    "SELECT * FROM court_documents_v4 ORDER BY rowid LIMIT 200"
                ).fetchall()
                court_docs = [dict(r) for r in rows]
            except Exception:
                pass

            vehicles = []
            try:
                rows = conn.execute(
                    "SELECT * FROM vehicles WHERE case_lane IN ('A', 'F') "
                    "ORDER BY rowid LIMIT 100"
                ).fetchall()
                vehicles = [dict(r) for r in rows]
            except Exception:
                pass

            return {
                "lower_court": self.LOWER_COURT,
                "case_number": self.LOWER_CASE,
                "judge": self.JUDGE,
                "docket_events": docket,
                "court_documents": court_docs,
                "vehicles": vehicles,
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()


# ── CLI ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    abb = AppellateBriefBuilder()
    usage = (
        "Appellate Brief Builder Skill\n"
        "Usage:\n"
        "  python appellate_brief_builder.py jurisdiction\n"
        "  python appellate_brief_builder.py issues [ISSUE1] [ISSUE2] ...\n"
        "  python appellate_brief_builder.py facts\n"
        "  python appellate_brief_builder.py argument <ISSUE>\n"
        "  python appellate_brief_builder.py standard <ISSUE>\n"
        "  python appellate_brief_builder.py relief\n"
        "  python appellate_brief_builder.py full\n"
        "  python appellate_brief_builder.py wordcount <TEXT>\n"
        "  python appellate_brief_builder.py record\n"
    )

    if len(sys.argv) < 2:
        print(usage)
        sys.exit(0)

    cmd = sys.argv[1].lower()

    if cmd == "jurisdiction":
        cycle_json(abb.generate_jurisdiction_statement())
    elif cmd == "issues":
        issues = sys.argv[2:] if len(sys.argv) > 2 else None
        cycle_json(abb.generate_issues_presented(issues))
    elif cmd == "facts":
        cycle_json(abb.generate_statement_of_facts())
    elif cmd == "argument":
        if len(sys.argv) < 3:
            print("Error: issue text required", file=sys.stderr)
            sys.exit(1)
        cycle_json(abb.generate_argument_section(" ".join(sys.argv[2:])))
    elif cmd == "standard":
        if len(sys.argv) < 3:
            print("Error: issue text required", file=sys.stderr)
            sys.exit(1)
        cycle_json(abb.generate_standard_of_review(" ".join(sys.argv[2:])))
    elif cmd == "relief":
        cycle_json(abb.generate_relief_requested())
    elif cmd == "full":
        cycle_json(abb.generate_full_brief())
    elif cmd == "wordcount":
        if len(sys.argv) < 3:
            print("Error: text required", file=sys.stderr)
            sys.exit(1)
        cycle_json(abb.check_word_count(" ".join(sys.argv[2:])))
    elif cmd == "record":
        cycle_json(abb.get_lower_court_record())
    else:
        print(usage)
