#!/usr/bin/env python3
"""
MBP LitigationOS — Adversary Wargame v2 Skill (m47)
=====================================================
Advanced wargaming that predicts adversary moves by analyzing
adversary_models, conspiracy_timeline, and judicial_violations.

Capabilities:
    - Scenario wargaming (predict Berry/Watson response + McNeill ruling)
    - Decision tree generation for filing options
    - Risk assessment with probability scoring
    - Berry appellate strategy prediction
    - Watson/Berry/McNeill coordination detection

Tables used:
    adversary_models (114 rows)
    conspiracy_timeline (2,512 rows)
    judicial_violations (1,127 rows)
    docket_events (221 rows)
    extracted_harms (26,459 rows)

Usage:
    from skills.adversary_wargame_v2 import AdversaryWargameV2
    wg = AdversaryWargameV2()
    scenario = wg.wargame_scenario("Emergency Motion to Restore PT", "14th Circuit")
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent
    if "skills" in str(Path(__file__)) else Path(__file__).resolve().parent))
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
    try:
        conn = sqlite3.connect(DB_PATH, timeout=60)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("PRAGMA query_only=ON")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        return None


# Known adversary patterns
BERRY_PATTERNS = {
    "delay_tactics": "Berry files procedural motions to consume deadlines",
    "appellate_bar": "Berry's appellate bar connections compromise COA proceedings",
    "coordination": "Watson files → McNeill rules same day → Berry files within 48 hrs",
    "form_over_substance": "Attack pro se formatting, miss deadlines, procedural traps",
}

MCNEILL_PATTERNS = {
    "ex_parte_bias": "24/55 orders (43.6%) entered ex parte — all without notice",
    "same_day_ruling": "Rules on Watson filings same day without hearing Father",
    "evidence_refusal": "Refuses to view exculpatory evidence presented by Father",
    "muting": "Mutes/silences Plaintiff at hearings",
    "disparate_treatment": "Zero sanctions on Emily despite violations",
}


class AdversaryWargameV2:
    """Advanced adversary wargaming with DB-grounded predictions."""

    def wargame_scenario(
        self,
        our_filing: str,
        court: str,
    ) -> Dict[str, Any]:
        """Predict Berry/Watson response, McNeill ruling, and our counter.

        Args:
            our_filing: Description or title of our planned filing
            court: Target court (e.g., '14th Circuit', 'COA', 'MSC')
        """
        conn = _get_db()
        if not conn:
            return {"error": "DB unavailable"}

        try:
            # Find relevant adversary models
            models = conn.execute(
                "SELECT filing_vehicle, attack_type, attack_description, "
                "weakness_exploited, rebuttal_strategy, rebuttal_authority, "
                "risk_level "
                "FROM adversary_models "
                "WHERE filing_vehicle LIKE ? OR attack_description LIKE ? "
                "ORDER BY risk_level DESC LIMIT 10",
                (f"%{our_filing[:30]}%", f"%{our_filing[:30]}%"),
            ).fetchall()

            # If no specific match, get general high-risk models
            if not models:
                models = conn.execute(
                    "SELECT filing_vehicle, attack_type, attack_description, "
                    "weakness_exploited, rebuttal_strategy, rebuttal_authority, "
                    "risk_level "
                    "FROM adversary_models "
                    "WHERE risk_level = 'HIGH' OR risk_level = 'CRITICAL' "
                    "ORDER BY risk_level DESC LIMIT 10",
                ).fetchall()

            # Get relevant judicial violations for McNeill prediction
            violations = conn.execute(
                "SELECT violation_type, count(*) as cnt "
                "FROM judicial_violations "
                "GROUP BY violation_type ORDER BY cnt DESC LIMIT 10",
            ).fetchall()

            # Get conspiracy patterns
            conspiracies = conn.execute(
                "SELECT conspiracy_type, count(*) as cnt, "
                "max(date) as latest "
                "FROM conspiracy_timeline "
                "GROUP BY conspiracy_type ORDER BY cnt DESC LIMIT 10",
            ).fetchall()

        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()

        # Build predictions
        watson_responses = []
        berry_responses = []
        mcneill_predictions = []

        for m in models:
            m_dict = dict(m)
            if "watson" in (m_dict.get("attack_description") or "").lower():
                watson_responses.append(m_dict)
            elif "berry" in (m_dict.get("attack_description") or "").lower():
                berry_responses.append(m_dict)
            else:
                watson_responses.append(m_dict)

        # McNeill prediction based on violation patterns
        for v in violations:
            mcneill_predictions.append({
                "pattern": v["violation_type"],
                "frequency": v["cnt"],
                "prediction": f"Likely to repeat: {v['violation_type']}",
            })

        return {
            "our_filing": our_filing,
            "court": court,
            "watson_predicted_response": {
                "count": len(watson_responses),
                "responses": [dict(m) for m in watson_responses[:5]],
                "likely_tactic": "File opposing motion with unverified allegations",
            },
            "berry_predicted_response": {
                "count": len(berry_responses),
                "responses": [dict(m) for m in berry_responses[:5]],
                "likely_tactic": BERRY_PATTERNS.get("form_over_substance"),
            },
            "mcneill_predicted_ruling": {
                "patterns": mcneill_predictions[:5],
                "likely_outcome": (
                    "If 14th Circuit: high probability of adverse ruling based on "
                    f"43.6% ex parte rate. Recommend filing in {court} with MSC backup."
                ),
            },
            "our_counter_strategy": {
                "preserve_record": "Object on record to every procedural defect",
                "document_pattern": "Cite 24 ex parte orders as pattern evidence",
                "multi_forum": "Simultaneous MSC superintending control if denied",
                "rebuttals": [dict(m) for m in models[:3]],
            },
            "conspiracy_context": [dict(c) for c in conspiracies],
        }

    def generate_decision_tree(
        self,
        filing_options: List[str],
    ) -> Dict[str, Any]:
        """Generate decision tree of possible outcomes for each filing option."""
        conn = _get_db()
        if not conn:
            return {"error": "DB unavailable"}

        tree = []
        try:
            # Get overall adversary risk profile
            risk_dist = conn.execute(
                "SELECT risk_level, count(*) as cnt "
                "FROM adversary_models GROUP BY risk_level",
            ).fetchall()
            risk_profile = {r["risk_level"]: r["cnt"] for r in risk_dist}

            for option in filing_options:
                # Check if any adversary models match
                matches = conn.execute(
                    "SELECT attack_type, attack_description, risk_level, "
                    "rebuttal_strategy "
                    "FROM adversary_models "
                    "WHERE filing_vehicle LIKE ? OR attack_description LIKE ? "
                    "LIMIT 5",
                    (f"%{option[:25]}%", f"%{option[:25]}%"),
                ).fetchall()

                outcomes = {
                    "favorable": {
                        "probability": 0.25 if "14th" in option else 0.55,
                        "description": "Court grants relief as requested",
                        "next_step": "Enforce order immediately",
                    },
                    "partial": {
                        "probability": 0.20,
                        "description": "Court grants limited relief",
                        "next_step": "Supplement with additional evidence/authority",
                    },
                    "denied": {
                        "probability": 0.40 if "14th" in option else 0.20,
                        "description": "Court denies — McNeill pattern",
                        "next_step": "Immediate appeal or MSC superintending control",
                    },
                    "procedural_trap": {
                        "probability": 0.15 if matches else 0.05,
                        "description": "Opposing counsel exploits procedural defect",
                        "next_step": "Pre-filing validator + pro se trap detector",
                    },
                }

                tree.append({
                    "filing_option": option,
                    "adversary_models_matched": len(matches),
                    "known_attacks": [dict(m) for m in matches],
                    "outcomes": outcomes,
                    "recommended": (
                        "PROCEED" if outcomes["favorable"]["probability"] >= 0.4
                        else "PROCEED WITH CAUTION"
                    ),
                })
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()

        return {
            "filing_options": filing_options,
            "risk_profile": risk_profile,
            "decision_tree": tree,
        }

    def risk_assess(self, filing: str) -> Dict[str, Any]:
        """Probability of success, risk factors, and mitigation for a filing."""
        conn = _get_db()
        if not conn:
            return {"error": "DB unavailable"}
        try:
            # Count relevant adversary attacks
            attacks = conn.execute(
                "SELECT count(*) FROM adversary_models "
                "WHERE filing_vehicle LIKE ? OR attack_description LIKE ?",
                (f"%{filing[:25]}%", f"%{filing[:25]}%"),
            ).fetchone()[0]

            # Count relevant violations
            violation_count = conn.execute(
                "SELECT count(*) FROM judicial_violations",
            ).fetchone()[0]

            # Recent conspiracy events
            recent = conn.execute(
                "SELECT count(*) FROM conspiracy_timeline "
                "WHERE date >= date('now', '-90 days')",
            ).fetchone()[0]

            # Risk factors
            risk_factors = []
            if attacks > 3:
                risk_factors.append({
                    "factor": "Multiple adversary attack models exist",
                    "severity": "HIGH",
                    "mitigation": "Pre-emptively address in filing",
                })
            if violation_count > 100:
                risk_factors.append({
                    "factor": f"{violation_count} judicial violations documented",
                    "severity": "HIGH",
                    "mitigation": "Include in disqualification argument",
                })
            if recent > 50:
                risk_factors.append({
                    "factor": f"{recent} conspiracy events in last 90 days",
                    "severity": "MEDIUM",
                    "mitigation": "Document coordination pattern",
                })

            # Pro se traps
            risk_factors.append({
                "factor": "Failure to preserve issues for appeal",
                "severity": "CRITICAL",
                "mitigation": "MCR 2.517 objection on record for every issue",
            })
            risk_factors.append({
                "factor": "Insufficient service time (MCR 2.119)",
                "severity": "HIGH",
                "mitigation": "9 days + 3 if mailed = 12 days minimum",
            })

            # Calculate probability
            base_prob = 0.50
            if "MSC" in filing.upper() or "supreme" in filing.lower():
                base_prob = 0.60  # MSC more favorable
            elif "14th" in filing or "circuit" in filing.lower():
                base_prob = 0.25  # McNeill hostile
            elif "COA" in filing.upper() or "appeal" in filing.lower():
                base_prob = 0.55  # COA moderate
            elif "federal" in filing.lower() or "1983" in filing:
                base_prob = 0.65  # Federal favorable

            # Adjust for risks
            adj = base_prob - (0.02 * len(risk_factors))
            prob = max(0.10, min(0.90, adj))

        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()

        return {
            "filing": filing,
            "success_probability": round(prob, 2),
            "risk_level": (
                "LOW" if prob >= 0.60 else
                "MEDIUM" if prob >= 0.40 else
                "HIGH"
            ),
            "risk_factors": risk_factors,
            "recommendation": (
                "PROCEED — favorable odds" if prob >= 0.50 else
                "PROCEED WITH CAUTION — address risk factors" if prob >= 0.30 else
                "RECONSIDER — high risk of adverse outcome"
            ),
            "adversary_attacks_known": attacks,
            "judicial_violations_total": violation_count,
        }

    def berry_strategy_predict(self) -> Dict[str, Any]:
        """Predict Berry's appellate strategy based on adversary_models patterns."""
        conn = _get_db()
        if not conn:
            return {"error": "DB unavailable"}
        try:
            # Get all Berry-related models
            models = conn.execute(
                "SELECT filing_vehicle, attack_type, attack_description, "
                "weakness_exploited, rebuttal_strategy, rebuttal_authority, "
                "risk_level "
                "FROM adversary_models "
                "WHERE attack_description LIKE '%Berry%' "
                "OR attack_description LIKE '%appellate%' "
                "OR attack_description LIKE '%appeal%' "
                "ORDER BY risk_level DESC",
            ).fetchall()

            # Berry coordination events
            coord = conn.execute(
                "SELECT date, action, coordinated_with, conspiracy_type "
                "FROM conspiracy_timeline "
                "WHERE actor LIKE '%Berry%' "
                "OR coordinated_with LIKE '%Berry%' "
                "ORDER BY date DESC LIMIT 20",
            ).fetchall()

            # Attack type distribution
            attack_types = Counter()
            for m in models:
                if m["attack_type"]:
                    attack_types[m["attack_type"]] += 1

        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()

        return {
            "adversary": "Ron Berry (Appellate Attorney)",
            "total_models": len(models),
            "known_patterns": BERRY_PATTERNS,
            "attack_distribution": dict(attack_types),
            "models": [dict(m) for m in models[:10]],
            "coordination_events": [dict(c) for c in coord],
            "predicted_strategy": {
                "primary": "Challenge pro se procedural compliance",
                "secondary": "Leverage appellate bar connections at COA",
                "tertiary": "Delay tactics to run out deadlines",
                "counter": (
                    "MSC is primary vehicle to bypass Berry's COA advantage. "
                    "Pre-filing validator catches procedural traps. "
                    "Document coordination for conspiracy claim."
                ),
            },
        }

    def watson_coordination_detect(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Flag coordination patterns between Watson/Berry/McNeill."""
        conn = _get_db()
        if not conn:
            return {"error": "DB unavailable"}

        start_date = start_date or "2023-01-01"
        end_date = end_date or date.today().isoformat()

        try:
            # All conspiracy events in range
            events = conn.execute(
                "SELECT id, date, actor, action, coordinated_with, "
                "conspiracy_type, severity "
                "FROM conspiracy_timeline "
                "WHERE date BETWEEN ? AND ? "
                "ORDER BY date",
                (start_date, end_date),
            ).fetchall()

            # Group by coordination pairs
            pairs = Counter()
            for evt in events:
                actor = evt["actor"] or ""
                coord = evt["coordinated_with"] or ""
                if coord:
                    pair = tuple(sorted([actor, coord]))
                    pairs[pair] += 1

            # Same-day filing/ruling patterns
            same_day = conn.execute(
                "SELECT d1.event_date_iso, d1.title as event1, d2.title as event2, "
                "d1.case_id "
                "FROM docket_events d1 "
                "JOIN docket_events d2 "
                "ON d1.event_date_iso = d2.event_date_iso "
                "AND d1.event_id != d2.event_id "
                "WHERE d1.event_date_iso BETWEEN ? AND ? "
                "ORDER BY d1.event_date_iso",
                (start_date, end_date),
            ).fetchall()

            # Severity distribution
            severity_dist = Counter()
            for evt in events:
                if evt["severity"]:
                    severity_dist[evt["severity"]] += 1

        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()

        return {
            "date_range": {"start": start_date, "end": end_date},
            "total_conspiracy_events": len(events),
            "coordination_pairs": {
                f"{p[0]} ↔ {p[1]}": cnt
                for p, cnt in pairs.most_common(10)
            },
            "same_day_events": [dict(r) for r in same_day[:20]],
            "severity_distribution": dict(severity_dist),
            "key_pattern": (
                "Watson files → McNeill rules same day → Berry files within 48 hrs. "
                "Documented across multiple months. "
                f"Total coordination events: {len(events)}."
            ),
            "events": [dict(e) for e in events[:30]],
        }


# ── JSON-RPC dispatch ─────────────────────────────────────────────────

def handle_rpc(method: str, params: Dict[str, Any] = None) -> Dict:
    params = params or {}
    wg = AdversaryWargameV2()
    dispatch = {
        "wargame_scenario": wg.wargame_scenario,
        "generate_decision_tree": wg.generate_decision_tree,
        "risk_assess": wg.risk_assess,
        "berry_strategy_predict": wg.berry_strategy_predict,
        "watson_coordination_detect": wg.watson_coordination_detect,
    }
    fn = dispatch.get(method)
    if not fn:
        return {"error": f"Unknown method: {method}", "available": list(dispatch.keys())}
    try:
        result = fn(**params)
        return {"result": result, "method": method, "status": "ok"}
    except Exception as e:
        return {"error": str(e), "method": method}


if __name__ == "__main__":
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    wg = AdversaryWargameV2()
    print("=== Adversary Wargame v2 Skill (m47) ===\n")

    # Risk assessment
    risk = wg.risk_assess("Emergency Motion to Restore Parenting Time (14th Circuit)")
    print(f"Risk assess: P(success)={risk['success_probability']}, "
          f"level={risk['risk_level']}")

    # Berry prediction
    berry = wg.berry_strategy_predict()
    print(f"Berry models: {berry['total_models']}, "
          f"coordination events: {len(berry['coordination_events'])}")

    # Coordination detection
    coord = wg.watson_coordination_detect()
    print(f"Conspiracy events: {coord['total_conspiracy_events']}")
    print(f"Coordination pairs: {coord['coordination_pairs']}")

    print("\n[OK] Adversary Wargame v2 operational")
