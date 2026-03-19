"""
Risk Assessor — LitigationOS 2026
Evaluates litigation risks: deadlines, waivers, appeal preservation,
strategic risk, and cure packets for Pigors v. Watson.
"""

import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

DB_PATH = os.environ.get("LITIGATION_DB_PATH", r"C:\Users\andre\LitigationOS\litigation_context.db")


def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA query_only=ON")
    conn.row_factory = sqlite3.Row
    return conn


class RiskAssessor:
    """Assesses litigation risks across deadlines, waivers, and strategy."""

    SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

    def get_risk_events(self, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query risk_events table (~21 rows), optionally filtered by severity."""
        conn = _get_db()
        try:
            if severity:
                rows = conn.execute(
                    "SELECT * FROM risk_events WHERE LOWER(severity) = ? ORDER BY rowid",
                    (severity.lower(),),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM risk_events ORDER BY rowid"
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_deadlines(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query deadlines table (~15 rows), optionally filtered by status."""
        conn = _get_db()
        try:
            if status:
                rows = conn.execute(
                    "SELECT * FROM deadlines WHERE LOWER(status) = ? ORDER BY due_date_iso",
                    (status.lower(),),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM deadlines ORDER BY due_date_iso"
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def assess_deadline_risk(self) -> Dict[str, Any]:
        """Identify approaching or missed deadlines with severity."""
        deadlines = self.get_deadlines()
        now = datetime.now()

        missed: List[Dict] = []
        critical: List[Dict] = []  # within 7 days
        warning: List[Dict] = []   # within 30 days
        upcoming: List[Dict] = []  # within 90 days

        for dl in deadlines:
            due = dl.get("due_date_iso")
            if not due:
                continue
            try:
                due_dt = datetime.fromisoformat(str(due)[:10])
            except (ValueError, TypeError):
                continue

            days_until = (due_dt - now).days
            entry = {**dl, "days_until_due": days_until}

            if days_until < 0:
                entry["risk_level"] = "MISSED"
                missed.append(entry)
            elif days_until <= 7:
                entry["risk_level"] = "CRITICAL"
                critical.append(entry)
            elif days_until <= 30:
                entry["risk_level"] = "WARNING"
                warning.append(entry)
            elif days_until <= 90:
                entry["risk_level"] = "UPCOMING"
                upcoming.append(entry)

        return {
            "assessment": "deadline_risk",
            "timestamp": now.isoformat(),
            "missed": missed,
            "critical": critical,
            "warning": warning,
            "upcoming": upcoming,
            "summary": (
                f"Deadlines: {len(missed)} MISSED, {len(critical)} CRITICAL (<7d), "
                f"{len(warning)} WARNING (<30d), {len(upcoming)} upcoming (<90d)."
            ),
        }

    def assess_waiver_risk(self) -> Dict[str, Any]:
        """Identify rights that may be waived if not preserved."""
        conn = _get_db()
        try:
            risk_events = conn.execute(
                """SELECT * FROM risk_events
                   WHERE LOWER(COALESCE(risk_class,'') || ' ' || COALESCE(title,''))
                   LIKE '%waiv%'
                   ORDER BY rowid"""
            ).fetchall()
            waiver_risks = [dict(r) for r in risk_events]

            deadlines = conn.execute(
                """SELECT * FROM deadlines
                   WHERE LOWER(COALESCE(basis_authority,'') || ' ' || COALESCE(title,''))
                   LIKE '%preserv%' OR LOWER(COALESCE(title,'')) LIKE '%waiv%'
                   ORDER BY due_date_iso"""
            ).fetchall()
            preservation_deadlines = [dict(r) for r in deadlines]

            return {
                "assessment": "waiver_risk",
                "waiver_risks": waiver_risks,
                "preservation_deadlines": preservation_deadlines,
                "total_risks": len(waiver_risks),
                "finding": (
                    f"Found {len(waiver_risks)} waiver risk(s) and "
                    f"{len(preservation_deadlines)} preservation deadline(s)."
                ),
            }
        finally:
            conn.close()

    def assess_appeal_preservation(self) -> Dict[str, Any]:
        """Check if appellate issues are properly preserved."""
        conn = _get_db()
        try:
            # Check for objections and preservation in evidence/docket
            objections = conn.execute(
                """SELECT * FROM docket_events
                   WHERE LOWER(COALESCE(title,'') || ' ' || COALESCE(summary,''))
                   LIKE '%objection%' OR LOWER(COALESCE(title,'') || ' ' || COALESCE(summary,''))
                   LIKE '%preserv%'
                   ORDER BY event_date_iso"""
            ).fetchall()
            objection_events = [dict(r) for r in objections]

            # Check risk_events for appeal-related risks
            appeal_risks = conn.execute(
                """SELECT * FROM risk_events
                   WHERE LOWER(COALESCE(risk_class,'') || ' ' || COALESCE(title,''))
                   LIKE '%appeal%' OR LOWER(COALESCE(risk_class,'') || ' ' || COALESCE(title,''))
                   LIKE '%preserv%'
                   ORDER BY rowid"""
            ).fetchall()
            appeal_risk_list = [dict(r) for r in appeal_risks]

            return {
                "assessment": "appeal_preservation",
                "objections_on_record": objection_events,
                "appeal_risks": appeal_risk_list,
                "objection_count": len(objection_events),
                "finding": (
                    f"Found {len(objection_events)} objection/preservation event(s) "
                    f"and {len(appeal_risk_list)} appeal-related risk(s). "
                    "Review each to confirm issues are preserved per MCR 2.517 and MCR 7.205."
                ),
            }
        finally:
            conn.close()

    def assess_strategic_risk(self, proposed_action: str) -> Dict[str, Any]:
        """Assess risk score for a proposed litigation action."""
        conn = _get_db()
        try:
            # Check adversary models for counter-attacks
            adversary = conn.execute(
                """SELECT * FROM adversary_models
                   WHERE LOWER(COALESCE(attack_type,'') || ' ' || COALESCE(rebuttal_strategy,''))
                   LIKE ?
                   LIMIT 10""",
                (f"%{proposed_action.lower()}%",),
            ).fetchall()
            adversary_threats = [dict(r) for r in adversary]

            # Check risk_events for related risks
            related_risks = conn.execute(
                """SELECT * FROM risk_events
                   WHERE LOWER(COALESCE(title,'') || ' ' || COALESCE(risk_class,''))
                   LIKE ?
                   LIMIT 10""",
                (f"%{proposed_action.lower()}%",),
            ).fetchall()
            risk_list = [dict(r) for r in related_risks]

            threat_count = len(adversary_threats) + len(risk_list)
            if threat_count == 0:
                risk_score = 20
                risk_level = "LOW"
            elif threat_count <= 2:
                risk_score = 45
                risk_level = "MODERATE"
            elif threat_count <= 5:
                risk_score = 70
                risk_level = "HIGH"
            else:
                risk_score = 90
                risk_level = "CRITICAL"

            return {
                "assessment": "strategic_risk",
                "proposed_action": proposed_action,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "adversary_threats": adversary_threats,
                "related_risks": risk_list,
                "recommendation": (
                    f"Risk level {risk_level} (score {risk_score}/100). "
                    f"Found {len(adversary_threats)} anticipated adversary response(s) "
                    f"and {len(risk_list)} related risk event(s)."
                ),
            }
        finally:
            conn.close()

    def get_cure_packets(self) -> List[Dict[str, Any]]:
        """Extract cure_packet_json from risk_events for actionable mitigations."""
        conn = _get_db()
        try:
            rows = conn.execute(
                """SELECT * FROM risk_events
                   WHERE cure_packet_json IS NOT NULL AND cure_packet_json != ''
                   ORDER BY rowid"""
            ).fetchall()
            results: List[Dict[str, Any]] = []
            for r in rows:
                entry = dict(r)
                raw = entry.get("cure_packet_json", "")
                try:
                    entry["cure_packet_parsed"] = json.loads(raw) if raw else None
                except (json.JSONDecodeError, TypeError):
                    entry["cure_packet_parsed"] = None
                results.append(entry)
            return results
        finally:
            conn.close()

    def generate_risk_dashboard(self) -> Dict[str, Any]:
        """Comprehensive risk overview with all categories."""
        deadline_risk = self.assess_deadline_risk()
        waiver_risk = self.assess_waiver_risk()
        appeal_risk = self.assess_appeal_preservation()
        risk_events = self.get_risk_events()
        cure_packets = self.get_cure_packets()

        # Severity distribution
        severity_dist: Dict[str, int] = {}
        for evt in risk_events:
            sev = (evt.get("severity") or "unknown").lower()
            severity_dist[sev] = severity_dist.get(sev, 0) + 1

        # Overall risk level
        missed = len(deadline_risk["missed"])
        critical = len(deadline_risk["critical"])
        if missed > 0:
            overall = "CRITICAL"
        elif critical > 0:
            overall = "HIGH"
        elif len(deadline_risk["warning"]) > 0:
            overall = "ELEVATED"
        else:
            overall = "MANAGEABLE"

        return {
            "dashboard_timestamp": datetime.now().isoformat(),
            "case": "Pigors v. Watson",
            "overall_risk_level": overall,
            "total_risk_events": len(risk_events),
            "severity_distribution": severity_dist,
            "deadline_assessment": deadline_risk,
            "waiver_assessment": waiver_risk,
            "appeal_preservation": appeal_risk,
            "cure_packets_available": len(cure_packets),
            "summary": (
                f"Overall risk: {overall}. "
                f"{deadline_risk['summary']} "
                f"{waiver_risk['finding']} "
                f"{appeal_risk['finding']}"
            ),
        }


def self_test() -> Dict[str, Any]:
    """Run self-test to verify DB connectivity and key risk assessment methods."""
    results = {"status": "ok", "tests": {}}
    assessor = RiskAssessor()

    # Test 1: DB connectivity
    try:
        conn = _get_db()
        conn.execute("SELECT 1").fetchone()
        conn.close()
        results["tests"]["db_connectivity"] = {"passed": True}
    except Exception as e:
        results["tests"]["db_connectivity"] = {"passed": False, "error": str(e)}

    # Test 2: get_risk_events
    try:
        events = assessor.get_risk_events()
        results["tests"]["get_risk_events"] = {
            "passed": isinstance(events, list),
            "count": len(events),
        }
    except Exception as e:
        results["tests"]["get_risk_events"] = {"passed": False, "error": str(e)}

    # Test 3: assess_deadline_risk
    try:
        dr = assessor.assess_deadline_risk()
        results["tests"]["assess_deadline_risk"] = {
            "passed": isinstance(dr, dict) and "assessment" in dr,
            "summary": dr.get("summary", ""),
        }
    except Exception as e:
        results["tests"]["assess_deadline_risk"] = {"passed": False, "error": str(e)}

    results["status"] = (
        "ok" if all(t.get("passed") for t in results["tests"].values()) else "degraded"
    )
    return results


if __name__ == "__main__":
    assessor = RiskAssessor()
    commands = {
        "events": lambda: assessor.get_risk_events(),
        "deadlines": lambda: assessor.get_deadlines(),
        "deadline-risk": lambda: assessor.assess_deadline_risk(),
        "waiver-risk": lambda: assessor.assess_waiver_risk(),
        "appeal": lambda: assessor.assess_appeal_preservation(),
        "cure": lambda: assessor.get_cure_packets(),
        "dashboard": lambda: assessor.generate_risk_dashboard(),
    }

    if len(sys.argv) < 2:
        print("Usage: risk_assessor.py [" + "|".join(commands.keys()) + "|strategic <action>|test]")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "test":
        result = self_test()
    elif cmd == "strategic" and len(sys.argv) >= 3:
        action = " ".join(sys.argv[2:])
        result = assessor.assess_strategic_risk(action)
    elif cmd in commands:
        result = commands[cmd]()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

    print(json.dumps(result, indent=2, default=str))
