#!/usr/bin/env python3
"""
MBP LitigationOS -- Pro Se Trap Detector Skill
================================================
Detect procedural traps that pro se litigants commonly fall into.
Cross-references deadlines, filings, objections, and judicial conduct
against known trap patterns to surface risks before they become fatal.

Case: Andrew Pigors v. Tiffany Watson
Court: 14th Circuit Court, Muskegon County
Judge: Hon. Jenny L. McNeill
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
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


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    """Check if a table exists in the database."""
    try:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM sqlite_master "
            "WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
        return bool(row and row["cnt"] > 0)
    except Exception:
        return False


def _safe_count(conn: sqlite3.Connection, query: str, params: tuple = ()) -> int:
    """Execute a COUNT query safely, returning 0 on error."""
    try:
        row = conn.execute(query, params).fetchone()
        return row[0] if row else 0
    except Exception:
        return 0


def _safe_fetchall(conn: sqlite3.Connection, query: str, params: tuple = ()) -> List[dict]:
    """Execute a query safely, returning list of dicts."""
    try:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []


class ProSeTrapDetector:
    """Detect procedural traps that pro se litigants commonly face."""

    KNOWN_TRAPS = {
        "waiver_by_silence": {
            "description": "Failing to object preserves nothing for appeal",
            "authority": "MCR 2.517; Walters v Nadell",
            "detection": "Check if objections were filed to every adverse ruling",
            "severity": "critical",
            "counter_filing": "Motion for Reconsideration (MCR 2.119(F)) or timely objection",
        },
        "improper_service": {
            "description": "Service defects can void entire filing",
            "authority": "MCR 2.105; MCR 2.107",
            "detection": "Verify certificate of service on every filing",
            "severity": "critical",
            "counter_filing": "Motion to Quash Service / Re-serve with proper proof",
        },
        "missed_deadline": {
            "description": "Missing filing deadlines = dismissal or default",
            "authority": "MCR 7.204(A) (21 days for appeal); MCR 2.119(F)(1) (21 days reconsideration)",
            "detection": "Cross-check deadlines table against docket_events",
            "severity": "critical",
            "counter_filing": "Motion for Relief from Judgment (MCR 2.612) or Late Application (MCR 7.205(F))",
        },
        "failure_to_preserve": {
            "description": "Issues not raised below are waived on appeal",
            "authority": "MCR 2.517(A)(7); Peterman v DNR",
            "detection": "Compare appellate issues to trial court objections",
            "severity": "critical",
            "counter_filing": "Supplemental objections or Motion to Amend",
        },
        "ex_parte_trap": {
            "description": "Judge communicating with one side without notice",
            "authority": "MCR 2.003; Canon 3(B)(7)",
            "detection": "Search for ex parte patterns in forensic_judicial_analysis",
            "severity": "critical",
            "counter_filing": "Motion for Disqualification (MCR 2.003) / JTC Complaint",
        },
        "burden_shifting": {
            "description": "Court improperly shifting burden of proof to father",
            "authority": "MCL 722.27(1)(c); Foskett v Foskett",
            "detection": "Check if court required father to prove fitness vs mother proving change",
            "severity": "high",
            "counter_filing": "Motion for Reconsideration citing burden standard",
        },
        "no_findings_of_fact": {
            "description": "Court must make findings on each best interest factor",
            "authority": "MCL 722.23; Bowers v Bowers",
            "detection": "Check court orders for required best interest findings",
            "severity": "high",
            "counter_filing": "Motion for Findings of Fact (MCR 2.517) or Appeal (MCR 7.204)",
        },
        "ppo_as_custody_tool": {
            "description": "PPO used to gain custody advantage instead of protection",
            "authority": "MCL 600.2950; Thompson v Thompson",
            "detection": "Cross-reference PPO timeline with custody proceedings",
            "severity": "high",
            "counter_filing": "Motion to Terminate PPO / Motion to Modify Custody",
        },
        "foc_rubber_stamp": {
            "description": "Court adopting FOC recommendation without independent analysis",
            "authority": "MCL 552.505; Harvey v Harvey",
            "detection": "Compare court order to FOC recommendation for verbatim adoption",
            "severity": "high",
            "counter_filing": "Objection to FOC Recommendation (MCL 552.507) with independent analysis demand",
        },
        "motion_to_adjourn_trap": {
            "description": "Denying adjournment to deprive party of preparation time",
            "authority": "MCR 2.503; Soumis v Soumis",
            "detection": "Check for denied adjournment requests near hearing dates",
            "severity": "medium",
            "counter_filing": "Emergency Motion for Adjournment with prejudice showing",
        },
        "discovery_stonewalling": {
            "description": "Opposing party refusing discovery without consequences",
            "authority": "MCR 2.313; MCR 2.310",
            "detection": "Check for unanswered discovery requests",
            "severity": "high",
            "counter_filing": "Motion to Compel (MCR 2.313) with sanctions request",
        },
        "gal_bias_trap": {
            "description": "GAL conducting biased investigation",
            "authority": "MCR 3.917; MCL 722.24",
            "detection": "Analyze GAL report for balance of investigation",
            "severity": "medium",
            "counter_filing": "Motion to Remove GAL / Objection to GAL Report",
        },
    }

    SEVERITY_ORDER = {"critical": 1, "high": 2, "medium": 3, "low": 4}

    def __init__(self, db_path: str = DB_PATH) -> None:
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def _conn_get(self) -> Optional[sqlite3.Connection]:
        if self._conn is None:
            try:
                self._conn = sqlite3.connect(self.db_path, timeout=30)
                self._conn.execute("PRAGMA journal_mode=WAL")
                self._conn.execute("PRAGMA query_only=ON")
                self._conn.row_factory = sqlite3.Row
            except Exception:
                self._conn = None
        return self._conn

    def close(self) -> None:
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    # ── Individual Trap Checks ────────────────────────────────────────

    def check_deadline_traps(self) -> List[Dict]:
        """Check deadlines table for approaching or missed deadlines."""
        results: List[Dict] = []
        conn = self._conn_get()
        if not conn or not _table_exists(conn, "deadlines"):
            return results

        now_iso = datetime.now().strftime("%Y-%m-%d")

        # Missed deadlines
        missed = _safe_fetchall(
            conn,
            "SELECT title, due_date_iso, basis_authority, status "
            "FROM deadlines "
            "WHERE status NOT IN ('completed', 'done') "
            "AND due_date_iso < ? "
            "ORDER BY due_date_iso ASC LIMIT 50",
            (now_iso,),
        )
        for row in missed:
            results.append({
                "trap_name": "missed_deadline",
                "triggered": True,
                "severity": "critical",
                "detail": f"MISSED: {row.get('title', '?')} due {row.get('due_date_iso', '?')}",
                "authority": row.get("basis_authority", ""),
                "source_table": "deadlines",
            })

        # Approaching deadlines (within 14 days)
        upcoming = _safe_fetchall(
            conn,
            "SELECT title, due_date_iso, basis_authority, status "
            "FROM deadlines "
            "WHERE status NOT IN ('completed', 'done') "
            "AND due_date_iso >= ? "
            "AND due_date_iso <= date(?, '+14 days') "
            "ORDER BY due_date_iso ASC LIMIT 50",
            (now_iso, now_iso),
        )
        for row in upcoming:
            results.append({
                "trap_name": "missed_deadline",
                "triggered": False,
                "severity": "high",
                "detail": f"APPROACHING: {row.get('title', '?')} due {row.get('due_date_iso', '?')}",
                "authority": row.get("basis_authority", ""),
                "source_table": "deadlines",
            })

        return results

    def check_preservation_traps(self) -> List[Dict]:
        """Check if appellate issues are properly preserved at trial level."""
        results: List[Dict] = []
        conn = self._conn_get()
        if not conn or not _table_exists(conn, "claims"):
            return results

        # Look for appellate claims without preservation evidence
        appellate_claims = _safe_fetchall(
            conn,
            "SELECT id, classification, proposition, status "
            "FROM claims "
            "WHERE (classification LIKE '%appell%' OR classification LIKE '%appeal%') "
            "LIMIT 100",
        )

        for claim in appellate_claims:
            prop = claim.get("proposition", "") or ""
            # Search evidence_quotes for objections supporting this claim
            objection_count = 0
            if _table_exists(conn, "evidence_quotes"):
                objection_count = _safe_count(
                    conn,
                    "SELECT COUNT(*) FROM evidence_quotes "
                    "WHERE (evidence_category LIKE '%objection%' "
                    "OR quote_text LIKE '%object%') "
                    "AND quote_text LIKE ?",
                    (f"%{prop[:60]}%",) if len(prop) > 10 else ("%",),
                )

            if objection_count == 0 and prop:
                results.append({
                    "trap_name": "failure_to_preserve",
                    "triggered": True,
                    "severity": "critical",
                    "detail": f"Appellate claim may lack preservation: {prop[:120]}",
                    "authority": "MCR 2.517(A)(7); Peterman v DNR",
                    "source_table": "claims",
                })

        return results

    def check_service_traps(self) -> List[Dict]:
        """Check filings for missing certificates of service."""
        results: List[Dict] = []
        conn = self._conn_get()
        if not conn:
            return results

        # Try filing_inventory first, fall back to documents
        table = None
        for candidate in ("filing_inventory", "documents", "docket_events"):
            if _table_exists(conn, candidate):
                table = candidate
                break

        if not table:
            return results

        if table == "docket_events":
            # Check docket events that are filings but may lack service proof
            filings = _safe_fetchall(
                conn,
                "SELECT id, title, event_date_iso, event_type "
                "FROM docket_events "
                "WHERE event_type LIKE '%fil%' OR event_type LIKE '%motion%' "
                "ORDER BY event_date_iso DESC LIMIT 50",
            )
            for row in filings:
                title = (row.get("title", "") or "").lower()
                if "certificate of service" not in title and "proof of service" not in title:
                    results.append({
                        "trap_name": "improper_service",
                        "triggered": True,
                        "severity": "high",
                        "detail": f"Filing may lack service proof: {row.get('title', '?')} ({row.get('event_date_iso', '')})",
                        "authority": "MCR 2.105; MCR 2.107",
                        "source_table": table,
                    })
        else:
            total = _safe_count(conn, f"SELECT COUNT(*) FROM {table}")
            results.append({
                "trap_name": "improper_service",
                "triggered": False,
                "severity": "medium",
                "detail": f"Found {total} records in {table} — manual service verification recommended",
                "authority": "MCR 2.105; MCR 2.107",
                "source_table": table,
            })

        return results

    def check_ex_parte_traps(self) -> List[Dict]:
        """Search for ex parte communication patterns."""
        results: List[Dict] = []
        conn = self._conn_get()
        if not conn:
            return results

        # Check judicial_violations
        if _table_exists(conn, "judicial_violations"):
            ex_parte = _safe_fetchall(
                conn,
                "SELECT id, judge_name, canon_number, violation_description, severity "
                "FROM judicial_violations "
                "WHERE violation_description LIKE '%ex parte%' "
                "OR violation_description LIKE '%one side%' "
                "OR violation_description LIKE '%without notice%' "
                "OR canon_number LIKE '%3(B)(7)%' "
                "LIMIT 50",
            )
            for row in ex_parte:
                results.append({
                    "trap_name": "ex_parte_trap",
                    "triggered": True,
                    "severity": "critical",
                    "detail": f"Ex parte violation: {(row.get('violation_description', '') or '')[:150]}",
                    "authority": "MCR 2.003; Canon 3(B)(7)",
                    "source_table": "judicial_violations",
                })

        # Check evidence_quotes for ex parte references
        if _table_exists(conn, "evidence_quotes"):
            ex_parte_ev = _safe_fetchall(
                conn,
                "SELECT id, quote_text, speaker, legal_significance "
                "FROM evidence_quotes "
                "WHERE quote_text LIKE '%ex parte%' "
                "LIMIT 20",
            )
            for row in ex_parte_ev:
                results.append({
                    "trap_name": "ex_parte_trap",
                    "triggered": True,
                    "severity": "high",
                    "detail": f"Ex parte evidence: {(row.get('quote_text', '') or '')[:150]}",
                    "authority": "MCR 2.003; Canon 3(B)(7)",
                    "source_table": "evidence_quotes",
                })

        return results

    def check_burden_traps(self) -> List[Dict]:
        """Search for improper burden shifting patterns."""
        results: List[Dict] = []
        conn = self._conn_get()
        if not conn:
            return results

        burden_terms = [
            "%burden%shift%", "%father%prove%", "%father%must show%",
            "%must demonstrate%fitness%", "%presumption against%father%",
        ]

        for table, text_col in [
            ("evidence_quotes", "quote_text"),
            ("judicial_violations", "violation_description"),
        ]:
            if not _table_exists(conn, table):
                continue
            for term in burden_terms:
                rows = _safe_fetchall(
                    conn,
                    f"SELECT * FROM {table} WHERE {text_col} LIKE ? LIMIT 10",
                    (term,),
                )
                for row in rows:
                    results.append({
                        "trap_name": "burden_shifting",
                        "triggered": True,
                        "severity": "high",
                        "detail": f"Burden shifting pattern: {(dict(row).get(text_col, '') or '')[:150]}",
                        "authority": "MCL 722.27(1)(c); Foskett v Foskett",
                        "source_table": table,
                    })

        return results

    # ── Main Scan ─────────────────────────────────────────────────────

    def scan_for_traps(self) -> List[Dict]:
        """Run all trap detections against the database."""
        all_traps: List[Dict] = []

        checks = [
            self.check_deadline_traps,
            self.check_preservation_traps,
            self.check_service_traps,
            self.check_ex_parte_traps,
            self.check_burden_traps,
        ]

        for check_fn in checks:
            try:
                all_traps.extend(check_fn())
            except Exception:
                pass

        # Sort by severity
        all_traps.sort(key=lambda t: self.SEVERITY_ORDER.get(t.get("severity", "low"), 4))

        return all_traps

    # ── Report Generation ─────────────────────────────────────────────

    def generate_trap_report(self) -> Dict:
        """Generate comprehensive trap report."""
        detected = self.scan_for_traps()

        triggered = [t for t in detected if t.get("triggered")]
        warnings = [t for t in detected if not t.get("triggered")]

        by_severity: Dict[str, int] = {}
        for t in triggered:
            sev = t.get("severity", "unknown")
            by_severity[sev] = by_severity.get(sev, 0) + 1

        by_trap: Dict[str, int] = {}
        for t in triggered:
            name = t.get("trap_name", "unknown")
            by_trap[name] = by_trap.get(name, 0) + 1

        counter_measures = []
        for trap_name in by_trap:
            cm = self.get_counter_measures(trap_name)
            if cm:
                counter_measures.append(cm)

        return {
            "report_date": datetime.now().isoformat(),
            "case": "Pigors v. Watson, 14th Circuit Muskegon County",
            "total_known_traps": len(self.KNOWN_TRAPS),
            "total_triggered": len(triggered),
            "total_warnings": len(warnings),
            "by_severity": by_severity,
            "by_trap_type": by_trap,
            "triggered_traps": triggered,
            "warnings": warnings,
            "counter_measures": counter_measures,
        }

    def get_counter_measures(self, trap_name: str) -> Dict:
        """Get specific counter-measures for a detected trap."""
        trap = self.KNOWN_TRAPS.get(trap_name)
        if not trap:
            return {}

        return {
            "trap_name": trap_name,
            "description": trap["description"],
            "authority": trap["authority"],
            "recommended_filing": trap.get("counter_filing", ""),
            "severity": trap.get("severity", "unknown"),
            "detection_method": trap["detection"],
        }

    def get_statistics(self) -> Dict:
        """Summary of all traps: total known, total detected, by severity."""
        detected = self.scan_for_traps()
        triggered = [t for t in detected if t.get("triggered")]

        sev_counts: Dict[str, int] = {}
        for t in triggered:
            sev = t.get("severity", "unknown")
            sev_counts[sev] = sev_counts.get(sev, 0) + 1

        trap_counts: Dict[str, int] = {}
        for t in triggered:
            name = t.get("trap_name", "unknown")
            trap_counts[name] = trap_counts.get(name, 0) + 1

        return {
            "total_known_traps": len(self.KNOWN_TRAPS),
            "total_detected": len(triggered),
            "total_scanned": len(detected),
            "by_severity": sev_counts,
            "by_trap_type": trap_counts,
            "db_path": self.db_path,
        }


# ── Self-Test ─────────────────────────────────────────────────────────

def self_test() -> Dict:
    """Validate that the skill loads, connects to DB, and runs without error."""
    results: Dict = {
        "skill": "pro_se_trap_detector",
        "status": "pass",
        "checks": {},
        "errors": [],
    }

    # Check 1: class instantiates
    try:
        detector = ProSeTrapDetector()
        results["checks"]["instantiation"] = "pass"
    except Exception as exc:
        results["checks"]["instantiation"] = "fail"
        results["errors"].append(f"Instantiation failed: {exc}")
        results["status"] = "fail"
        return results

    # Check 2: DB connection
    try:
        conn = detector._conn_get()
        if conn:
            results["checks"]["db_connection"] = "pass"
        else:
            results["checks"]["db_connection"] = "skip (DB not available)"
    except Exception as exc:
        results["checks"]["db_connection"] = f"fail: {exc}"
        results["errors"].append(str(exc))

    # Check 3: KNOWN_TRAPS populated
    trap_count = len(ProSeTrapDetector.KNOWN_TRAPS)
    results["checks"]["known_traps_count"] = trap_count
    results["checks"]["known_traps"] = "pass" if trap_count >= 10 else "fail"

    # Check 4: scan_for_traps runs
    try:
        traps = detector.scan_for_traps()
        results["checks"]["scan_for_traps"] = f"pass ({len(traps)} findings)"
    except Exception as exc:
        results["checks"]["scan_for_traps"] = f"fail: {exc}"
        results["errors"].append(str(exc))

    # Check 5: generate_trap_report runs
    try:
        report = detector.generate_trap_report()
        results["checks"]["generate_trap_report"] = f"pass (triggered={report.get('total_triggered', 0)})"
    except Exception as exc:
        results["checks"]["generate_trap_report"] = f"fail: {exc}"
        results["errors"].append(str(exc))

    # Check 6: get_counter_measures runs for each trap
    try:
        cm_count = 0
        for trap_name in ProSeTrapDetector.KNOWN_TRAPS:
            cm = detector.get_counter_measures(trap_name)
            if cm:
                cm_count += 1
        results["checks"]["counter_measures"] = f"pass ({cm_count}/{trap_count})"
    except Exception as exc:
        results["checks"]["counter_measures"] = f"fail: {exc}"
        results["errors"].append(str(exc))

    # Check 7: get_statistics runs
    try:
        stats = detector.get_statistics()
        results["checks"]["get_statistics"] = f"pass (detected={stats.get('total_detected', 0)})"
    except Exception as exc:
        results["checks"]["get_statistics"] = f"fail: {exc}"
        results["errors"].append(str(exc))

    if results["errors"]:
        results["status"] = "fail"

    detector.close()
    return results


# ── CLI ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "--self-test":
            result = self_test()
        elif cmd == "--report":
            d = ProSeTrapDetector()
            result = d.generate_trap_report()
            d.close()
        elif cmd == "--stats":
            d = ProSeTrapDetector()
            result = d.get_statistics()
            d.close()
        elif cmd == "--deadlines":
            d = ProSeTrapDetector()
            result = d.check_deadline_traps()
            d.close()
        elif cmd == "--preservation":
            d = ProSeTrapDetector()
            result = d.check_preservation_traps()
            d.close()
        elif cmd == "--ex-parte":
            d = ProSeTrapDetector()
            result = d.check_ex_parte_traps()
            d.close()
        elif cmd == "--burden":
            d = ProSeTrapDetector()
            result = d.check_burden_traps()
            d.close()
        elif cmd == "--service":
            d = ProSeTrapDetector()
            result = d.check_service_traps()
            d.close()
        elif cmd == "--counter":
            trap_name = sys.argv[2] if len(sys.argv) > 2 else ""
            d = ProSeTrapDetector()
            result = d.get_counter_measures(trap_name)
            d.close()
        else:
            d = ProSeTrapDetector()
            result = d.scan_for_traps()
            d.close()
    else:
        result = self_test()

    cycle_json(result)
