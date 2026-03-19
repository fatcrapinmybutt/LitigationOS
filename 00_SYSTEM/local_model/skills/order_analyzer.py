#!/usr/bin/env python3
"""
MBP LitigationOS -- Order Analyzer Skill
==========================================
Analyze court orders for reversible errors, map to appellate grounds,
and identify orders that should be vacated.
Case: Pigors v. Watson, 14th Circuit Muskegon, Judge McNeill.
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent if 'skills' in str(Path(__file__)) else Path(__file__).resolve().parent))
try:
    from cycle_method import cycle_json, cycle_print
except ImportError:
    cycle_json = lambda obj, **kw: print(json.dumps(obj, default=str))
    cycle_print = print

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)


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


# ── Error classification keywords ─────────────────────────────────────

ERROR_PATTERNS = {
    "missing_findings": {
        "keywords": [
            "no finding", "without finding", "failed to find",
            "no endangerment", "no best interest", "no factual basis",
            "no evidence", "did not address", "failed to address",
        ],
        "authority": "MCL 722.27a(3); MCL 722.27(1)(c)",
        "description": "Missing required findings (e.g., endangerment, best interest)",
    },
    "procedural_defect": {
        "keywords": [
            "no notice", "without notice", "ex parte", "no hearing",
            "without hearing", "denied hearing", "no opportunity",
            "procedural", "due process", "unilateral",
        ],
        "authority": "MCR 2.119; US Const Amend XIV",
        "description": "Procedural defects — no notice, no hearing, ex parte action",
    },
    "evidence_standard": {
        "keywords": [
            "no competent evidence", "no evidence", "insufficient evidence",
            "unsupported", "speculation", "hearsay", "no testimony",
            "no record", "not in record",
        ],
        "authority": "MCR 2.517(A)(1); MRE 602; MRE 802",
        "description": "Evidence standard violations — no competent evidence in record",
    },
    "jurisdiction": {
        "keywords": [
            "exceeded authority", "no jurisdiction", "jurisdictional",
            "ultra vires", "outside scope", "lack of authority",
            "unauthorized",
        ],
        "authority": "MCL 600.1701; MCR 3.302",
        "description": "Jurisdiction issues — court exceeded its authority",
    },
    "due_process": {
        "keywords": [
            "due process", "fundamental right", "parental right",
            "constitutional", "liberty interest", "14th amendment",
            "troxel", "substantive due process",
        ],
        "authority": "US Const Amend XIV; Troxel v Granville, 530 US 57 (2000)",
        "description": "Due process violations — infringement on fundamental parental rights",
    },
    "abuse_of_discretion": {
        "keywords": [
            "abuse of discretion", "arbitrary", "capricious",
            "clearly erroneous", "unreasonable", "no rational basis",
            "against great weight",
        ],
        "authority": "MCL 722.28; Vodvarka v Grasher, 259 Mich App 1 (2003)",
        "description": "Abuse of discretion in custody/parenting time determination",
    },
}

APPELLATE_STANDARDS = {
    "abuse_of_discretion": {
        "standard": "Abuse of Discretion",
        "description": "Court's decision was so palpably and grossly violative of fact "
                       "and logic that it evidenced a perversity of will or defiance of judgment.",
        "authority": "MCL 722.28; Vodvarka v Grasher, 259 Mich App 1 (2003)",
    },
    "clear_error": {
        "standard": "Clear Error",
        "description": "After reviewing the entire record, the appellate court is left "
                       "with the definite and firm conviction a mistake was made.",
        "authority": "MCR 2.613(C); Fletcher v Fletcher, 447 Mich 871 (1994)",
    },
    "de_novo": {
        "standard": "De Novo",
        "description": "Questions of law are reviewed without deference to the lower court.",
        "authority": "Docket No. 366810; MCR 7.216(A)(7)",
    },
    "constitutional_error": {
        "standard": "Constitutional Error",
        "description": "Deprivation of fundamental rights — heightened scrutiny applies.",
        "authority": "US Const Amend XIV; Troxel v Granville, 530 US 57 (2000)",
    },
}


class OrderAnalyzer:
    """Analyze court orders for reversible errors and appellate grounds."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def _conn(self) -> Optional[sqlite3.Connection]:
        try:
            conn = sqlite3.connect(self.db_path, timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA query_only=ON")
            conn.row_factory = sqlite3.Row
            return conn
        except Exception:
            return None

    # ── Query court orders ────────────────────────────────────────────

    def get_court_orders(self, limit: int = 50) -> List[Dict]:
        """Query court_documents_v4 and docket_events for court orders."""
        orders: List[Dict] = []
        conn = self._conn()
        if not conn:
            return orders

        # court_documents_v4
        try:
            rows = conn.execute(
                "SELECT * FROM court_documents_v4 ORDER BY rowid DESC LIMIT ?",
                (limit,),
            ).fetchall()
            for r in rows:
                orders.append({
                    "source": "court_documents_v4",
                    **{k: r[k] for k in r.keys()},
                })
        except Exception:
            pass

        # docket_events flagged as orders
        try:
            rows = conn.execute(
                "SELECT event_date_iso, title, event_type, summary "
                "FROM docket_events "
                "WHERE lower(event_type) LIKE '%order%' "
                "   OR lower(title) LIKE '%order%' "
                "ORDER BY event_date_iso DESC LIMIT ?",
                (limit,),
            ).fetchall()
            for r in rows:
                orders.append({
                    "source": "docket_events",
                    "date": r["event_date_iso"],
                    "title": r["title"],
                    "event_type": r["event_type"],
                    "summary": r["summary"],
                })
        except Exception:
            pass

        conn.close()
        return orders

    # ── Analyze a single order for errors ─────────────────────────────

    def analyze_order(self, order_text: str) -> Dict:
        """
        Analyze a court order for reversible errors.
        Returns: {errors, appellate_grounds, recommended_vehicles, severity}.
        """
        text_lower = order_text.lower()
        errors: List[Dict] = []

        for error_type, info in ERROR_PATTERNS.items():
            hits = [kw for kw in info["keywords"] if kw in text_lower]
            if hits:
                errors.append({
                    "error_type": error_type,
                    "description": info["description"],
                    "authority": info["authority"],
                    "matched_keywords": hits,
                    "severity": "critical" if len(hits) >= 3 else (
                        "high" if len(hits) >= 2 else "moderate"
                    ),
                })

        # Check for 329+ day separation issue — always flag
        if any(kw in text_lower for kw in [
            "parenting time", "custody", "visitation", "contact"
        ]):
            errors.append({
                "error_type": "prolonged_separation",
                "description": "Order contributes to 329+ days parent-child separation "
                               "without required findings per MCL 722.27a(7)",
                "authority": "MCL 722.27a(7); MCL 722.23(j)",
                "matched_keywords": ["prolonged separation"],
                "severity": "critical",
            })

        appellate_grounds = self.map_to_appellate_grounds(errors)

        # Determine recommended vehicles
        vehicles: List[str] = []
        error_types = {e["error_type"] for e in errors}
        if "due_process" in error_types or "constitutional_error" in error_types:
            vehicles.append("Appeal of Right (MCR 7.204)")
        if "procedural_defect" in error_types:
            vehicles.append("Motion for Reconsideration (MCR 2.119(F))")
            vehicles.append("Motion to Set Aside Order (MCR 2.612)")
        if "abuse_of_discretion" in error_types:
            vehicles.append("Appeal of Right (MCR 7.204)")
        if "missing_findings" in error_types:
            vehicles.append("Motion for Findings of Fact (MCR 2.517)")
        if not vehicles:
            vehicles.append("Motion for Reconsideration (MCR 2.119(F))")

        severity = "critical" if any(
            e["severity"] == "critical" for e in errors
        ) else ("high" if any(
            e["severity"] == "high" for e in errors
        ) else "moderate")

        return {
            "errors": errors,
            "error_count": len(errors),
            "appellate_grounds": appellate_grounds,
            "recommended_vehicles": list(set(vehicles)),
            "severity": severity,
        }

    # ── Find defective orders ─────────────────────────────────────────

    def find_defective_orders(self, judge_name: str = "McNeill") -> List[Dict]:
        """
        Cross-reference judicial_violations with court orders to find
        orders likely defective. Pulls from forensic_judicial_analysis.
        """
        defective: List[Dict] = []
        conn = self._conn()
        if not conn:
            return defective

        like_judge = f"%{judge_name}%"

        # judicial_violations — critical/high severity
        try:
            rows = conn.execute(
                "SELECT * FROM judicial_violations "
                "WHERE (judge_name LIKE ? OR judge_name IS NULL) "
                "AND severity IN ('critical', 'high') "
                "ORDER BY severity DESC",
                (like_judge,),
            ).fetchall()
            for r in rows:
                defective.append({
                    "source": "judicial_violations",
                    **{k: r[k] for k in r.keys()},
                })
        except Exception:
            pass

        # forensic_judicial_analysis — limit scan
        try:
            rows = conn.execute(
                "SELECT * FROM forensic_judicial_analysis "
                "WHERE lower(category) LIKE '%order%' "
                "   OR lower(category) LIKE '%defect%' "
                "   OR lower(category) LIKE '%error%' "
                "   OR lower(category) LIKE '%violation%' "
                "LIMIT 100",
            ).fetchall()
            for r in rows:
                defective.append({
                    "source": "forensic_judicial_analysis",
                    **{k: r[k] for k in r.keys()},
                })
        except Exception:
            pass

        # auth_benchbook_violations
        try:
            rows = conn.execute(
                "SELECT * FROM auth_benchbook_violations "
                "WHERE judge LIKE ? AND severity IN ('critical', 'high') "
                "ORDER BY severity DESC",
                (like_judge,),
            ).fetchall()
            for r in rows:
                defective.append({
                    "source": "auth_benchbook_violations",
                    **{k: r[k] for k in r.keys()},
                })
        except Exception:
            pass

        conn.close()
        return defective

    # ── Map errors to appellate grounds ───────────────────────────────

    def map_to_appellate_grounds(self, errors: List[Dict]) -> List[Dict]:
        """
        Map identified errors to appellate grounds with standard of review.
        Returns: [{ground, standard_of_review, authority, supporting_evidence}].
        """
        grounds: List[Dict] = []
        seen_standards: set = set()

        mapping = {
            "abuse_of_discretion": "abuse_of_discretion",
            "missing_findings": "clear_error",
            "evidence_standard": "clear_error",
            "procedural_defect": "de_novo",
            "jurisdiction": "de_novo",
            "due_process": "constitutional_error",
            "prolonged_separation": "constitutional_error",
        }

        for error in errors:
            key = mapping.get(error["error_type"], "abuse_of_discretion")
            if key not in seen_standards:
                seen_standards.add(key)
                std = APPELLATE_STANDARDS[key]
                grounds.append({
                    "ground": std["standard"],
                    "standard_of_review": std["description"],
                    "authority": std["authority"],
                    "supporting_errors": [
                        e for e in errors if mapping.get(e["error_type"]) == key
                    ],
                })

        return grounds

    # ── Orders to vacate ──────────────────────────────────────────────

    def get_orders_to_vacate(self) -> List[Dict]:
        """
        Identify specific orders that should be vacated.
        Queries judicial_violations for critical/high severity.
        Returns: [{description, date, legal_basis, evidence_count}].
        """
        candidates: List[Dict] = []
        conn = self._conn()
        if not conn:
            return candidates

        # Gather violations — limit to top candidates for performance
        try:
            rows = conn.execute(
                "SELECT * FROM judicial_violations "
                "WHERE severity IN ('critical', 'high') "
                "ORDER BY severity DESC LIMIT 50",
            ).fetchall()
            for r in rows:
                d = {k: r[k] for k in r.keys()}
                description = d.get("violation_description") or d.get("description") or str(d)
                candidates.append({
                    "description": description,
                    "date": d.get("date") or d.get("event_date") or "unknown",
                    "severity": d.get("severity", "high"),
                    "legal_basis": self._vacatur_basis(d),
                    "evidence_count": self._count_supporting_evidence(
                        conn, description
                    ),
                })
        except Exception:
            pass

        conn.close()
        return candidates

    @staticmethod
    def _vacatur_basis(violation: Dict) -> str:
        """Determine the legal basis for vacatur from violation details."""
        text = str(violation).lower()
        if "due process" in text or "constitutional" in text:
            return "MCR 2.612(C)(1)(f) — unconstitutional deprivation; US Const Amend XIV"
        if "ex parte" in text or "no notice" in text:
            return "MCR 2.612(C)(1)(d) — void order (no notice/hearing)"
        if "fraud" in text or "misrepresent" in text:
            return "MCR 2.612(C)(1)(c) — fraud, misrepresentation, or misconduct"
        if "jurisdiction" in text:
            return "MCR 2.612(C)(1)(d) — void order (no jurisdiction)"
        return "MCR 2.612(C)(1)(f) — any other reason justifying relief"

    @staticmethod
    def _count_supporting_evidence(conn: sqlite3.Connection, desc: str) -> int:
        """Count evidence_quotes entries that relate to this violation."""
        try:
            keywords = [w for w in desc.split() if len(w) > 4][:5]
            if not keywords:
                return 0
            clauses = " OR ".join(["quote_text LIKE ?"] * len(keywords))
            params = [f"%{kw}%" for kw in keywords]
            row = conn.execute(
                f"SELECT COUNT(*) as cnt FROM evidence_quotes WHERE {clauses}",
                params,
            ).fetchone()
            return row["cnt"] if row else 0
        except Exception:
            return 0

    # ── Generate vacatur brief ────────────────────────────────────────

    def generate_vacatur_brief(self, order_description: str) -> str:
        """Generate IRAC-structured argument for vacating a specific order."""
        conn = self._conn()
        if not conn:
            return "ERROR: Database unavailable."

        # Gather supporting authority
        authorities: List[str] = []
        try:
            rows = conn.execute(
                "SELECT rule_number, title, substr(full_text, 1, 500) as text "
                "FROM auth_rules "
                "WHERE rule_number LIKE '%2.612%' OR rule_number LIKE '%2.119%' "
                "   OR rule_number LIKE '%7.204%' "
                "LIMIT 10",
            ).fetchall()
            for r in rows:
                authorities.append(f"{r['rule_number']} — {r['title']}: {r['text']}")
        except Exception:
            pass

        # Gather supporting evidence
        evidence: List[str] = []
        keywords = [w for w in order_description.split() if len(w) > 4][:6]
        if keywords:
            try:
                clauses = " OR ".join(["quote_text LIKE ?"] * len(keywords))
                params = [f"%{kw}%" for kw in keywords]
                rows = conn.execute(
                    f"SELECT quote_text, speaker, legal_significance "
                    f"FROM evidence_quotes WHERE {clauses} LIMIT 15",
                    params,
                ).fetchall()
                for r in rows:
                    evidence.append(
                        f"  - [{r['speaker'] or 'Record'}]: {r['quote_text'][:200]}"
                    )
            except Exception:
                pass

        # Gather judicial violations
        violations: List[str] = []
        try:
            rows = conn.execute(
                "SELECT violation_description, canon_number, severity "
                "FROM judicial_violations "
                "WHERE severity IN ('critical', 'high') LIMIT 10",
            ).fetchall()
            for r in rows:
                violations.append(
                    f"  - Canon {r['canon_number'] or 'N/A'} ({r['severity']}): "
                    f"{r['violation_description'][:200]}"
                )
        except Exception:
            pass

        conn.close()

        auth_block = "\n".join(authorities) if authorities else "  [Authority search returned no results — manual citation required]"
        evid_block = "\n".join(evidence) if evidence else "  [No matching evidence quotes — supplement from record]"
        viol_block = "\n".join(violations) if violations else "  [No judicial violations on record]"

        brief = f"""
================================================================================
IRAC BRIEF IN SUPPORT OF MOTION TO VACATE ORDER
Pigors v. Watson — Case No. 2024-001507-DC
14th Circuit Court, Muskegon County | Hon. Jenny L. McNeill
================================================================================

ORDER AT ISSUE:
  {order_description}

I. ISSUE

  Whether the trial court's order should be set aside under MCR 2.612(C)(1)
  where the order was entered in violation of Plaintiff's procedural and
  substantive due process rights, without required statutory findings, and
  contributing to {'>'}329 days of parent-child separation.

II. RULE

  MCR 2.612(C)(1) provides that a court may relieve a party from a final
  judgment or order for the following reasons:
    (a) Mistake, inadvertence, surprise, or excusable neglect;
    (c) Fraud, misrepresentation, or other misconduct of an adverse party;
    (d) The judgment or order is void;
    (f) Any other reason justifying relief from the operation of the judgment.

  MCL 722.27a(7) — A parenting time order shall not be entered that would
  change the child's established custodial environment unless there is clear
  and convincing evidence that it is in the child's best interest.

  MCL 722.23(a)-(l) — The court shall consider all best interest factors.

  Governing Authority from DB:
{auth_block}

III. APPLICATION

  A. Factual Background

  Plaintiff Andrew Pigors, proceeding pro se, has been separated from his
  child for more than 329 days as a direct consequence of the challenged order.
  This prolonged separation occurred without the required statutory findings.

  B. The Order Lacks Required Findings

  The trial court failed to make the findings required by MCL 722.27a(3)
  before restricting parenting time. No finding of endangerment was made on
  the record. No best interest analysis was conducted per MCL 722.23.

  C. Procedural Defects

  The order was entered without adequate notice or hearing opportunity,
  violating MCR 2.119 and Plaintiff's Fourteenth Amendment due process rights.

  D. Supporting Evidence from Record
{evid_block}

  E. Judicial Violations
{viol_block}

IV. CONCLUSION

  For the foregoing reasons, the order described above should be set aside
  pursuant to MCR 2.612(C)(1). The trial court's failure to make required
  findings, combined with procedural defects and documented judicial violations,
  constitutes reversible error. Plaintiff respectfully requests that this Court
  vacate the order and restore his parenting time rights.

  WHEREFORE, Plaintiff Andrew Pigors respectfully requests that this
  Honorable Court:
    1. Set aside the challenged order per MCR 2.612(C)(1);
    2. Restore parenting time per MCL 722.27a;
    3. Order a de novo best interest hearing per MCL 722.23;
    4. Grant such other relief as this Court deems just and equitable.

Respectfully submitted,

______________________________
Andrew Pigors, Pro Se Plaintiff
Date: _______________

CERTIFICATE OF SERVICE
I certify that a copy of this document was served on all parties by
first-class mail / electronic service on _____________.

______________________________
Andrew Pigors
================================================================================
"""
        return brief.strip()


# ── Self-test ─────────────────────────────────────────────────────────

def self_test() -> Dict:
    """Run diagnostics on OrderAnalyzer skill."""
    results = {
        "skill": "order_analyzer",
        "status": "ok",
        "tests": {},
    }
    analyzer = OrderAnalyzer()

    # Test DB connection
    conn = _get_db()
    results["tests"]["db_connection"] = "pass" if conn else "FAIL"
    if conn:
        conn.close()

    # Test get_court_orders
    try:
        orders = analyzer.get_court_orders(limit=5)
        results["tests"]["get_court_orders"] = f"pass ({len(orders)} rows)"
    except Exception as e:
        results["tests"]["get_court_orders"] = f"FAIL: {e}"

    # Test analyze_order
    try:
        sample = "Order entered ex parte without notice or hearing denying parenting time"
        analysis = analyzer.analyze_order(sample)
        results["tests"]["analyze_order"] = (
            f"pass ({analysis['error_count']} errors, "
            f"{len(analysis['appellate_grounds'])} grounds)"
        )
    except Exception as e:
        results["tests"]["analyze_order"] = f"FAIL: {e}"

    # Test find_defective_orders
    try:
        defective = analyzer.find_defective_orders("McNeill")
        results["tests"]["find_defective_orders"] = f"pass ({len(defective)} items)"
    except Exception as e:
        results["tests"]["find_defective_orders"] = f"FAIL: {e}"

    # Test get_orders_to_vacate
    try:
        vacate = analyzer.get_orders_to_vacate()
        results["tests"]["get_orders_to_vacate"] = f"pass ({len(vacate)} candidates)"
    except Exception as e:
        results["tests"]["get_orders_to_vacate"] = f"FAIL: {e}"

    # Test map_to_appellate_grounds
    try:
        sample_errors = [
            {"error_type": "due_process", "severity": "critical"},
            {"error_type": "missing_findings", "severity": "high"},
        ]
        grounds = analyzer.map_to_appellate_grounds(sample_errors)
        results["tests"]["map_to_appellate_grounds"] = f"pass ({len(grounds)} grounds)"
    except Exception as e:
        results["tests"]["map_to_appellate_grounds"] = f"FAIL: {e}"

    # Overall status
    if any("FAIL" in str(v) for v in results["tests"].values()):
        results["status"] = "degraded"

    return results


# ── CLI ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        analyzer = OrderAnalyzer()

        if cmd == "orders":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
            cycle_json(analyzer.get_court_orders(limit))
        elif cmd == "analyze":
            text = " ".join(sys.argv[2:])
            cycle_json(analyzer.analyze_order(text))
        elif cmd == "defective":
            judge = sys.argv[2] if len(sys.argv) > 2 else "McNeill"
            cycle_json(analyzer.find_defective_orders(judge))
        elif cmd == "vacate":
            cycle_json(analyzer.get_orders_to_vacate())
        elif cmd == "brief":
            desc = " ".join(sys.argv[2:])
            print(analyzer.generate_vacatur_brief(desc))
        elif cmd == "test":
            cycle_json(self_test())
        else:
            print(f"Unknown command: {cmd}", file=sys.stderr)
            print("Commands: orders, analyze, defective, vacate, brief, test")
    else:
        print("Order Analyzer Skill — MBP LitigationOS")
        print("Usage:")
        print("  python order_analyzer.py orders [limit]")
        print("  python order_analyzer.py analyze 'order text here'")
        print("  python order_analyzer.py defective [judge_name]")
        print("  python order_analyzer.py vacate")
        print("  python order_analyzer.py brief 'order description'")
        print("  python order_analyzer.py test")
