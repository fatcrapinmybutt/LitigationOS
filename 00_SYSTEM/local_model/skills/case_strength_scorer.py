#!/usr/bin/env python3
"""
MBP LitigationOS -- Case Strength Scorer Skill
================================================
Per-lane, per-vehicle, per-ground strength scoring with gap analysis
and prioritized recommendations for Pigors v. Watson.

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

LANE_MAP = {
    "A": "Watson Custody (2024-001507-DC)",
    "B": "Shady Oaks Housing",
    "C": "Convergence (Multi-Lane)",
    "D": "PPO (2023-5907-PP)",
    "E": "Judicial Misconduct (JTC/MSC)",
    "F": "Appellate (COA 366810)",
}


def _get_db() -> Optional[sqlite3.Connection]:
    """Get read-only DB connection with WAL mode."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA query_only=ON")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        return None


def _grade(score: float) -> str:
    """Convert numeric score to letter grade."""
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


class CaseStrengthScorer:
    """Case strength scoring and gap analysis engine."""

    def __init__(self):
        self._cache: Dict = {}

    # ── Data Access ───────────────────────────────────────────────────

    def get_lane_scores(self) -> List[Dict]:
        """Query legal_action_scores (12 rows) for per-lane assessment."""
        conn = _get_db()
        if not conn:
            return []

        try:
            rows = conn.execute(
                "SELECT id, action_name, lane, evidence_score, "
                "authority_score, compliance_score, overall_score, "
                "gaps, supporting_atoms, updated_at "
                "FROM legal_action_scores ORDER BY overall_score DESC"
            ).fetchall()
            result = [dict(r) for r in rows]
            conn.close()
            return result
        except Exception:
            conn.close()
            return []

    def get_filing_readiness(self) -> List[Dict]:
        """Query filing_readiness (10 rows)."""
        conn = _get_db()
        if not conn:
            return []

        try:
            rows = conn.execute(
                "SELECT id, vehicle_name, best_source, authority_score, "
                "evidence_score, compliance_score, impeachment_score, "
                "total_score, gaps, strengths, attack_vectors, "
                "rebuttals_ready, status "
                "FROM filing_readiness ORDER BY total_score DESC"
            ).fetchall()
            result = [dict(r) for r in rows]
            conn.close()
            return result
        except Exception:
            conn.close()
            return []

    def get_claims_analysis(self) -> Dict:
        """Query claims (57 rows) + claims_matrix (57 rows)."""
        conn = _get_db()
        if not conn:
            return {"claims": [], "matrix": []}

        try:
            claims = [
                dict(r) for r in conn.execute(
                    "SELECT claim_id, issue_id, classification, actor, "
                    "substr(proposition, 1, 400) as proposition, "
                    "substr(affirmative_counter_proposition, 1, 400) as counter, "
                    "evidence_targets, status "
                    "FROM claims ORDER BY claim_id"
                ).fetchall()
            ]

            matrix = [
                dict(r) for r in conn.execute(
                    "SELECT claim_id, issue_id, classification, actor, "
                    "status, substr(proposition, 1, 400) as proposition "
                    "FROM claims_matrix ORDER BY claim_id"
                ).fetchall()
            ]

            conn.close()

            # Classification breakdown
            class_counts = {}
            for c in claims:
                cls = c.get("classification", "unknown")
                class_counts[cls] = class_counts.get(cls, 0) + 1

            return {
                "claims_count": len(claims),
                "matrix_count": len(matrix),
                "classification_breakdown": class_counts,
                "claims": claims,
                "matrix": matrix,
            }
        except Exception:
            conn.close()
            return {"claims": [], "matrix": []}

    def get_case_strength(self) -> List[Dict]:
        """Query case_strength_scores (5 rows)."""
        conn = _get_db()
        if not conn:
            return []

        try:
            rows = conn.execute(
                "SELECT id, lane, lane_name, authority_score, evidence_score, "
                "impeachment_score, timeline_score, total_score, grade, "
                "authority_count, evidence_count, impeachment_count, "
                "contradiction_count, timeline_count, testimony_count, "
                "filing_bundle_count, strengths, weaknesses, "
                "critical_gaps, next_action, scored_at "
                "FROM case_strength_scores ORDER BY total_score DESC"
            ).fetchall()
            result = [dict(r) for r in rows]
            conn.close()
            return result
        except Exception:
            conn.close()
            return []

    # ── Scoring ───────────────────────────────────────────────────────

    def score_vehicle(self, vehicle_name: str) -> Dict:
        """Comprehensive readiness score for a specific filing vehicle."""
        readiness = self.get_filing_readiness()
        match = None
        for r in readiness:
            if vehicle_name.lower() in (r.get("vehicle_name", "") or "").lower():
                match = r
                break

        if not match:
            return {
                "vehicle": vehicle_name,
                "status": "NOT_FOUND",
                "message": f"No filing readiness data found for '{vehicle_name}'",
                "available_vehicles": [
                    r.get("vehicle_name") for r in readiness
                ],
            }

        # Parse scores
        auth = match.get("authority_score", 0) or 0
        evid = match.get("evidence_score", 0) or 0
        comp = match.get("compliance_score", 0) or 0
        imp = match.get("impeachment_score", 0) or 0
        total = match.get("total_score", 0) or 0

        return {
            "vehicle": match.get("vehicle_name"),
            "status": match.get("status"),
            "scores": {
                "authority": auth,
                "evidence": evid,
                "compliance": comp,
                "impeachment": imp,
                "total": total,
                "grade": _grade(total) if isinstance(total, (int, float)) else "N/A",
            },
            "strengths": match.get("strengths"),
            "gaps": match.get("gaps"),
            "attack_vectors": match.get("attack_vectors"),
            "rebuttals_ready": match.get("rebuttals_ready"),
            "filing_ready": total >= 70 if isinstance(total, (int, float)) else False,
        }

    def score_ground(self, ground_name: str) -> Dict:
        """Evidence sufficiency score for a specific legal ground."""
        conn = _get_db()
        if not conn:
            return {"error": "DB connection failed"}

        try:
            # Search evidence_quotes for this ground
            like_pat = f"%{ground_name}%"
            ground_clean = ground_name.replace("_", " ")
            like_pat2 = f"%{ground_clean}%"

            evidence_count = conn.execute(
                "SELECT COUNT(*) FROM evidence_quotes "
                "WHERE quote_text LIKE ? OR quote_text LIKE ? "
                "OR legal_significance LIKE ? OR evidence_category LIKE ?",
                (like_pat, like_pat2, like_pat2, like_pat2),
            ).fetchone()[0]

            # Search claims for this ground
            claims_count = conn.execute(
                "SELECT COUNT(*) FROM claims "
                "WHERE proposition LIKE ? OR classification LIKE ?",
                (like_pat2, like_pat2),
            ).fetchone()[0]

            # Search authority
            authority_count = 0
            try:
                authority_count = conn.execute(
                    "SELECT COUNT(*) FROM auth_rules "
                    "WHERE title LIKE ? OR full_text LIKE ?",
                    (like_pat2, like_pat2),
                ).fetchone()[0]
            except Exception:
                pass

            conn.close()

            # Score calculation
            evidence_score = min(evidence_count / 10.0, 10.0) * 10
            claims_score = min(claims_count / 3.0, 10.0) * 10
            authority_score_val = min(authority_count / 2.0, 10.0) * 10
            total = round(
                evidence_score * 0.5 + claims_score * 0.2 + authority_score_val * 0.3,
                2,
            )

            return {
                "ground": ground_name,
                "evidence_count": evidence_count,
                "claims_count": claims_count,
                "authority_count": authority_count,
                "scores": {
                    "evidence": round(evidence_score, 2),
                    "claims": round(claims_score, 2),
                    "authority": round(authority_score_val, 2),
                    "total": total,
                    "grade": _grade(total),
                },
                "sufficiency": (
                    "STRONG" if total >= 80 else
                    "ADEQUATE" if total >= 60 else
                    "WEAK" if total >= 40 else
                    "INSUFFICIENT"
                ),
            }
        except Exception as e:
            return {"error": str(e)}

    # ── Gap Analysis ──────────────────────────────────────────────────

    def identify_gaps(self) -> List[Dict]:
        """Query gap_tickets (15 rows) for unresolved gaps."""
        conn = _get_db()
        if not conn:
            return []

        try:
            rows = conn.execute(
                "SELECT ticket_id, filing_name, gap_type, "
                "description, severity, resolution_status, "
                "resolution_notes, created_at, resolved_at "
                "FROM gap_tickets ORDER BY severity DESC"
            ).fetchall()
            result = [dict(r) for r in rows]
            conn.close()
            return result
        except Exception:
            conn.close()
            return []

    # ── Scorecard & Recommendations ───────────────────────────────────

    def generate_scorecard(self) -> Dict:
        """Overall case scorecard with per-lane, per-vehicle, per-ground scores."""
        lane_scores = self.get_lane_scores()
        readiness = self.get_filing_readiness()
        strength = self.get_case_strength()
        gaps = self.identify_gaps()

        # Per-lane summary
        lane_summary = {}
        for ls in lane_scores:
            lane = ls.get("lane", "?")
            lane_summary[lane] = {
                "action": ls.get("action_name"),
                "overall_score": ls.get("overall_score"),
                "evidence": ls.get("evidence_score"),
                "authority": ls.get("authority_score"),
                "compliance": ls.get("compliance_score"),
                "gaps": ls.get("gaps"),
            }

        # Per-vehicle summary
        vehicle_summary = {}
        for fr in readiness:
            name = fr.get("vehicle_name", "?")
            total = fr.get("total_score", 0) or 0
            vehicle_summary[name] = {
                "total_score": total,
                "grade": _grade(total) if isinstance(total, (int, float)) else "N/A",
                "status": fr.get("status"),
                "gaps": fr.get("gaps"),
            }

        # Case strength summary
        strength_summary = {}
        for cs in strength:
            lane = cs.get("lane", "?")
            strength_summary[lane] = {
                "lane_name": cs.get("lane_name"),
                "total_score": cs.get("total_score"),
                "grade": cs.get("grade"),
                "strengths": cs.get("strengths"),
                "weaknesses": cs.get("weaknesses"),
                "critical_gaps": cs.get("critical_gaps"),
                "next_action": cs.get("next_action"),
            }

        # Gap summary
        open_gaps = [g for g in gaps if g.get("resolution_status") != "resolved"]

        return {
            "scorecard_title": "Pigors v. Watson — Case Strength Scorecard",
            "generated": datetime.now().isoformat(),
            "lanes": lane_summary,
            "vehicles": vehicle_summary,
            "case_strength": strength_summary,
            "gap_analysis": {
                "total_gaps": len(gaps),
                "open_gaps": len(open_gaps),
                "gaps": open_gaps,
            },
            "overall_assessment": self._compute_overall(lane_scores, strength),
        }

    def _compute_overall(
        self, lane_scores: List[Dict], strength: List[Dict]
    ) -> Dict:
        """Compute aggregate overall assessment."""
        lane_totals = [
            ls.get("overall_score", 0) or 0 for ls in lane_scores
            if isinstance(ls.get("overall_score"), (int, float))
        ]
        strength_totals = [
            cs.get("total_score", 0) or 0 for cs in strength
            if isinstance(cs.get("total_score"), (int, float))
        ]

        all_scores = lane_totals + strength_totals
        avg = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0

        return {
            "average_score": avg,
            "grade": _grade(avg),
            "lanes_scored": len(lane_totals),
            "strength_lanes": len(strength_totals),
            "assessment": (
                "STRONG — ready for aggressive filing posture"
                if avg >= 80 else
                "GOOD — most vehicles filing-ready with minor gaps"
                if avg >= 65 else
                "FAIR — significant gaps require attention before filing"
                if avg >= 50 else
                "WEAK — critical gaps must be resolved"
            ),
        }

    def get_recommendations(self) -> List[Dict]:
        """Prioritized list of actions to improve case strength."""
        gaps = self.identify_gaps()
        strength = self.get_case_strength()
        readiness = self.get_filing_readiness()

        recommendations = []
        priority = 1

        # Critical gaps first
        for g in gaps:
            if g.get("resolution_status") == "resolved":
                continue
            sev = g.get("severity", "")
            if sev and str(sev).lower() in ("critical", "high"):
                recommendations.append({
                    "priority": priority,
                    "type": "gap_resolution",
                    "action": f"Resolve {g.get('gap_type', 'gap')}: {g.get('description', '')}",
                    "filing": g.get("filing_name"),
                    "severity": sev,
                })
                priority += 1

        # Weakest lanes
        for cs in strength:
            total = cs.get("total_score", 0) or 0
            if isinstance(total, (int, float)) and total < 60:
                recommendations.append({
                    "priority": priority,
                    "type": "lane_improvement",
                    "action": f"Strengthen Lane {cs.get('lane', '?')} "
                              f"({cs.get('lane_name', '')}): {cs.get('next_action', '')}",
                    "current_score": total,
                    "weaknesses": cs.get("weaknesses"),
                })
                priority += 1

        # Vehicles not filing-ready
        for fr in readiness:
            total = fr.get("total_score", 0) or 0
            if isinstance(total, (int, float)) and total < 70:
                recommendations.append({
                    "priority": priority,
                    "type": "vehicle_preparation",
                    "action": f"Prepare {fr.get('vehicle_name', '?')} for filing",
                    "current_score": total,
                    "gaps": fr.get("gaps"),
                })
                priority += 1

        # Remaining non-critical gaps
        for g in gaps:
            if g.get("resolution_status") == "resolved":
                continue
            sev = str(g.get("severity", "")).lower()
            if sev not in ("critical", "high"):
                recommendations.append({
                    "priority": priority,
                    "type": "gap_resolution",
                    "action": f"Resolve {g.get('gap_type', 'gap')}: {g.get('description', '')}",
                    "filing": g.get("filing_name"),
                    "severity": g.get("severity"),
                })
                priority += 1

        return recommendations


def self_test() -> Dict:
    """Verify skill connectivity and data availability."""
    results = {"skill": "case_strength_scorer", "timestamp": datetime.now().isoformat()}
    conn = _get_db()
    if not conn:
        results["status"] = "FAIL"
        results["error"] = "DB connection failed"
        return results

    checks = {}
    for table in [
        "legal_action_scores", "filing_readiness", "claims",
        "claims_matrix", "case_strength_scores", "gap_tickets",
    ]:
        try:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            checks[table] = {"status": "OK", "rows": count}
        except Exception as e:
            checks[table] = {"status": "FAIL", "error": str(e)}

    conn.close()
    results["checks"] = checks
    results["status"] = (
        "OK" if all(c["status"] == "OK" for c in checks.values()) else "DEGRADED"
    )
    return results


# ── CLI ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    scorer = CaseStrengthScorer()

    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "lanes":
            cycle_json(scorer.get_lane_scores())
        elif cmd == "readiness":
            cycle_json(scorer.get_filing_readiness())
        elif cmd == "claims":
            cycle_json(scorer.get_claims_analysis())
        elif cmd == "strength":
            cycle_json(scorer.get_case_strength())
        elif cmd == "vehicle":
            name = sys.argv[2] if len(sys.argv) > 2 else "appeal"
            cycle_json(scorer.score_vehicle(name))
        elif cmd == "ground":
            name = sys.argv[2] if len(sys.argv) > 2 else "judicial_bias"
            cycle_json(scorer.score_ground(name))
        elif cmd == "gaps":
            cycle_json(scorer.identify_gaps())
        elif cmd == "scorecard":
            cycle_json(scorer.generate_scorecard())
        elif cmd == "recommendations":
            cycle_json(scorer.get_recommendations())
        elif cmd == "stats":
            cycle_json(self_test())
        elif cmd == "self_test":
            cycle_json(self_test())
        else:
            print(f"Unknown command: {cmd}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Case Strength Scorer Skill")
        print("Usage: python case_strength_scorer.py <command> [args]")
        print("Commands: lanes, readiness, claims, strength, vehicle, ground, gaps, scorecard, recommendations, self_test")
