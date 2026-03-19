#!/usr/bin/env python3
"""
MBP LitigationOS -- Adversary War Room Skill
==============================================
Predictive attack/rebuttal modeling for litigation.
Mines adversary_models (43 rows) and risk_events (21 rows) to simulate
opponent behavior, build rebuttal packets, and war-game filing scenarios.

Case: Andrew Pigors (Plaintiff/Appellant) v. Tiffany Watson (Defendant/Appellee)
Court: 14th Circuit Court, Muskegon County — Hon. Jenny L. McNeill
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

# Severity-integer-to-label mapping (risk_events.severity is 0-100 int)
_SEV_LABELS = {range(90, 101): "critical", range(75, 90): "high",
               range(50, 75): "medium", range(0, 50): "low"}

# Risk-level weight for scoring (adversary_models.risk_level is text)
_RISK_WEIGHTS = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}


def _sev_label(val: int) -> str:
    for rng, label in _SEV_LABELS.items():
        if val in rng:
            return label
    return "unknown"


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


def _row_to_dict(row: sqlite3.Row) -> Dict:
    return {k: row[k] for k in row.keys()}


def _safe_json(text: Optional[str]):
    """Parse JSON column or return raw string."""
    if not text:
        return None
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return text


class AdversaryWarRoom:
    """Predictive attack/rebuttal modeling engine."""

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

    # ── Core Queries ──────────────────────────────────────────────────

    def get_known_attacks(
        self, filing_vehicle: Optional[str] = None, limit: int = 50
    ) -> List[Dict]:
        """Query adversary_models for known attack patterns."""
        results: List[Dict] = []
        try:
            conn = self._conn()
            if not conn:
                return results

            if filing_vehicle:
                rows = conn.execute(
                    "SELECT id, filing_vehicle, attack_type, attack_description, "
                    "weakness_exploited, our_evidence_strength, rebuttal_strategy, "
                    "rebuttal_authority, rebuttal_evidence, risk_level "
                    "FROM adversary_models "
                    "WHERE filing_vehicle = ? "
                    "ORDER BY CASE risk_level "
                    "  WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 "
                    "  WHEN 'MEDIUM' THEN 3 ELSE 4 END "
                    "LIMIT ?",
                    (filing_vehicle, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, filing_vehicle, attack_type, attack_description, "
                    "weakness_exploited, our_evidence_strength, rebuttal_strategy, "
                    "rebuttal_authority, rebuttal_evidence, risk_level "
                    "FROM adversary_models "
                    "ORDER BY CASE risk_level "
                    "  WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 "
                    "  WHEN 'MEDIUM' THEN 3 ELSE 4 END "
                    "LIMIT ?",
                    (limit,),
                ).fetchall()

            results = [_row_to_dict(r) for r in rows]
            conn.close()
        except Exception:
            pass
        return results

    def get_risk_events(
        self, severity_filter: Optional[str] = None, limit: int = 30
    ) -> List[Dict]:
        """Query risk_events for active litigation risks.
        severity_filter: 'critical', 'high', 'medium', 'low' or None for all.
        """
        results: List[Dict] = []
        sev_ranges = {
            "critical": (90, 100), "high": (75, 89),
            "medium": (50, 74), "low": (0, 49),
        }
        try:
            conn = self._conn()
            if not conn:
                return results

            if severity_filter and severity_filter.lower() in sev_ranges:
                lo, hi = sev_ranges[severity_filter.lower()]
                rows = conn.execute(
                    "SELECT risk_type_id, track, forum, risk_class, severity, "
                    "title, trigger_json, cure_cost, cure_deadline_clock, "
                    "cure_packet_json, authority_refs_json "
                    "FROM risk_events "
                    "WHERE severity BETWEEN ? AND ? "
                    "ORDER BY severity DESC LIMIT ?",
                    (lo, hi, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT risk_type_id, track, forum, risk_class, severity, "
                    "title, trigger_json, cure_cost, cure_deadline_clock, "
                    "cure_packet_json, authority_refs_json "
                    "FROM risk_events "
                    "ORDER BY severity DESC LIMIT ?",
                    (limit,),
                ).fetchall()

            for row in rows:
                d = _row_to_dict(row)
                d["severity_label"] = _sev_label(d.get("severity", 0) or 0)
                d["trigger_json"] = _safe_json(d.get("trigger_json"))
                d["cure_packet_json"] = _safe_json(d.get("cure_packet_json"))
                d["authority_refs_json"] = _safe_json(d.get("authority_refs_json"))
                results.append(d)

            conn.close()
        except Exception:
            pass
        return results

    # ── Predictive Methods ────────────────────────────────────────────

    def predict_attacks(self, filing_type: str) -> List[Dict]:
        """Predict likely opposing attacks for a filing type.
        Matches filing_type against adversary_models.filing_vehicle using
        exact match first, then LIKE fallback, plus ALL_FILINGS catch-all.
        Returns ranked list with probability estimate based on risk_level.
        """
        results: List[Dict] = []
        try:
            conn = self._conn()
            if not conn:
                return results

            # Exact match + ALL_FILINGS generic attacks
            rows = conn.execute(
                "SELECT id, filing_vehicle, attack_type, attack_description, "
                "weakness_exploited, our_evidence_strength, rebuttal_strategy, "
                "rebuttal_authority, rebuttal_evidence, risk_level "
                "FROM adversary_models "
                "WHERE filing_vehicle = ? OR filing_vehicle = 'ALL_FILINGS' "
                "ORDER BY CASE risk_level "
                "  WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 "
                "  WHEN 'MEDIUM' THEN 3 ELSE 4 END",
                (filing_type,),
            ).fetchall()

            # LIKE fallback if no exact match (beyond ALL_FILINGS)
            exact_ids = {r["id"] for r in rows}
            like_pat = f"%{filing_type}%"
            fallback = conn.execute(
                "SELECT id, filing_vehicle, attack_type, attack_description, "
                "weakness_exploited, our_evidence_strength, rebuttal_strategy, "
                "rebuttal_authority, rebuttal_evidence, risk_level "
                "FROM adversary_models "
                "WHERE filing_vehicle LIKE ? AND filing_vehicle != 'ALL_FILINGS' "
                "ORDER BY CASE risk_level "
                "  WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 "
                "  WHEN 'MEDIUM' THEN 3 ELSE 4 END",
                (like_pat,),
            ).fetchall()

            all_rows = list(rows) + [r for r in fallback if r["id"] not in exact_ids]

            # Probability estimate: CRITICAL=0.9, HIGH=0.7, MEDIUM=0.5, LOW=0.3
            prob_map = {"CRITICAL": 0.9, "HIGH": 0.7, "MEDIUM": 0.5, "LOW": 0.3}
            for row in all_rows:
                rl = (row["risk_level"] or "MEDIUM").upper()
                results.append({
                    "attack_type": row["attack_type"] or "",
                    "attack_description": row["attack_description"] or "",
                    "probability": prob_map.get(rl, 0.5),
                    "risk_level": rl,
                    "weakness_exploited": row["weakness_exploited"] or "",
                    "rebuttal_strategy": row["rebuttal_strategy"] or "",
                    "rebuttal_authority": row["rebuttal_authority"] or "",
                    "filing_vehicle": row["filing_vehicle"] or "",
                })

            results.sort(key=lambda x: x["probability"], reverse=True)
            conn.close()
        except Exception:
            pass
        return results

    def build_rebuttal_packet(self, attack_type: str) -> Dict:
        """Build comprehensive rebuttal packet for a specific attack type.
        Pulls from adversary_models, auth_rules, evidence_quotes, impeachment_items.
        """
        packet: Dict = {
            "attack_type": attack_type,
            "attacks": [],
            "authority": [],
            "evidence": [],
            "impeachment": [],
            "summary": "",
        }
        try:
            conn = self._conn()
            if not conn:
                return packet

            like_pat = f"%{attack_type}%"

            # 1. adversary_models entries for this attack
            rows = conn.execute(
                "SELECT filing_vehicle, attack_type, attack_description, "
                "weakness_exploited, our_evidence_strength, rebuttal_strategy, "
                "rebuttal_authority, rebuttal_evidence, risk_level "
                "FROM adversary_models "
                "WHERE attack_type LIKE ? "
                "ORDER BY CASE risk_level "
                "  WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 "
                "  WHEN 'MEDIUM' THEN 3 ELSE 4 END",
                (like_pat,),
            ).fetchall()
            packet["attacks"] = [_row_to_dict(r) for r in rows]

            # Collect authority citations from rebuttal_authority fields
            auth_cites = set()
            for atk in packet["attacks"]:
                ra = atk.get("rebuttal_authority", "")
                if ra:
                    auth_cites.update(
                        c.strip() for c in ra.replace(";", ",").split(",") if c.strip()
                    )

            # 2. Look up cited authorities in auth_rules
            for cite in list(auth_cites)[:20]:
                try:
                    row = conn.execute(
                        "SELECT rule_number, title, substr(full_text, 1, 500) as text "
                        "FROM auth_rules "
                        "WHERE rule_number LIKE ? LIMIT 1",
                        (f"%{cite}%",),
                    ).fetchone()
                    if row:
                        packet["authority"].append({
                            "rule": row["rule_number"] or "",
                            "title": row["title"] or "",
                            "text": row["text"] or "",
                        })
                except Exception:
                    pass

            # 3. Supporting evidence from evidence_quotes
            try:
                rows = conn.execute(
                    "SELECT quote_text, speaker, legal_significance, "
                    "evidence_category "
                    "FROM evidence_quotes "
                    "WHERE quote_text LIKE ? OR legal_significance LIKE ? "
                    "LIMIT 10",
                    (like_pat, like_pat),
                ).fetchall()
                packet["evidence"] = [_row_to_dict(r) for r in rows]
            except Exception:
                pass

            # 4. Counter-attack via impeachment_items
            try:
                rows = conn.execute(
                    "SELECT speaker, statement, contradicting_text, "
                    "legal_hook, severity "
                    "FROM impeachment_items "
                    "WHERE statement LIKE ? OR legal_hook LIKE ? "
                    "ORDER BY CASE severity "
                    "  WHEN 'critical' THEN 1 WHEN 'high' THEN 2 "
                    "  WHEN 'medium' THEN 3 ELSE 4 END "
                    "LIMIT 10",
                    (like_pat, like_pat),
                ).fetchall()
                packet["impeachment"] = [_row_to_dict(r) for r in rows]
            except Exception:
                pass

            n_atk = len(packet["attacks"])
            n_auth = len(packet["authority"])
            n_ev = len(packet["evidence"])
            n_imp = len(packet["impeachment"])
            packet["summary"] = (
                f"Rebuttal packet for '{attack_type}': "
                f"{n_atk} attack model(s), {n_auth} authority cite(s), "
                f"{n_ev} evidence item(s), {n_imp} impeachment item(s)."
            )

            conn.close()
        except Exception:
            pass
        return packet

    def war_game_scenario(
        self, our_filing: str, opponent_response: Optional[str] = None
    ) -> Dict:
        """Simulate a full attack-defense cycle for a filing type.
        1. Our filing → predicted opponent attacks
        2. Each attack → our prepared rebuttal
        3. Each rebuttal → predicted counter-attack (round 2)
        4. Overall risk assessment
        """
        scenario: Dict = {
            "our_filing": our_filing,
            "opponent_response": opponent_response,
            "rounds": [],
            "overall_risk": 0.0,
            "risk_label": "",
            "recommendation": "",
        }
        try:
            # Round 1: Predict attacks against our filing
            attacks = self.predict_attacks(our_filing)

            # If caller specified an expected opponent response, filter/boost
            if opponent_response:
                boosted = []
                other = []
                opp_lower = opponent_response.lower()
                for a in attacks:
                    if opp_lower in (a.get("attack_type", "") or "").lower() or \
                       opp_lower in (a.get("attack_description", "") or "").lower():
                        a["probability"] = min(a["probability"] + 0.2, 1.0)
                        boosted.append(a)
                    else:
                        other.append(a)
                attacks = boosted + other

            # Round 2: For each attack, build rebuttal and check for counter
            total_risk = 0.0
            for atk in attacks:
                move: Dict = {
                    "round": 1,
                    "attack": atk,
                    "rebuttal": None,
                    "counter_attack": None,
                }

                # Build rebuttal
                rebuttal = self.build_rebuttal_packet(atk.get("attack_type", ""))
                move["rebuttal"] = {
                    "strategy": atk.get("rebuttal_strategy", ""),
                    "authority": atk.get("rebuttal_authority", ""),
                    "evidence_count": len(rebuttal.get("evidence", [])),
                    "impeachment_count": len(rebuttal.get("impeachment", [])),
                }

                # Round 3: Predict counter-attack on our rebuttal
                weakness = atk.get("weakness_exploited", "")
                if weakness:
                    counters = self.predict_attacks(our_filing)
                    related = [
                        c for c in counters
                        if weakness.lower() in (c.get("attack_description", "") or "").lower()
                        and c.get("attack_type") != atk.get("attack_type")
                    ]
                    if related:
                        move["counter_attack"] = related[0]
                        move["round"] = 2

                total_risk += atk.get("probability", 0.5)
                scenario["rounds"].append(move)

            n = len(attacks) or 1
            avg_risk = total_risk / n
            scenario["overall_risk"] = round(avg_risk, 2)
            if avg_risk >= 0.75:
                scenario["risk_label"] = "HIGH"
                scenario["recommendation"] = (
                    "High-risk filing. Strengthen rebuttals before filing. "
                    "Consider pre-emptive motions to neutralize top attacks."
                )
            elif avg_risk >= 0.5:
                scenario["risk_label"] = "MEDIUM"
                scenario["recommendation"] = (
                    "Moderate risk. Prepare rebuttal packets for top 3 attacks. "
                    "Filing is viable with preparation."
                )
            else:
                scenario["risk_label"] = "LOW"
                scenario["recommendation"] = (
                    "Low-risk filing. Opponent has limited attack vectors. "
                    "Proceed with standard rebuttal preparation."
                )
        except Exception:
            pass
        return scenario

    # ── Risk Analysis ─────────────────────────────────────────────────

    def get_risk_matrix(self) -> Dict:
        """Build complete risk matrix from risk_events.
        Grouped by severity and forum with cure packets and deadlines.
        """
        matrix: Dict = {
            "total_risks": 0,
            "by_severity": {"critical": [], "high": [], "medium": [], "low": []},
            "by_forum": {},
            "unmitigated": [],
            "cure_deadlines": [],
        }
        try:
            conn = self._conn()
            if not conn:
                return matrix

            rows = conn.execute(
                "SELECT risk_type_id, track, forum, risk_class, severity, "
                "title, trigger_json, cure_cost, cure_deadline_clock, "
                "cure_packet_json, authority_refs_json "
                "FROM risk_events ORDER BY severity DESC"
            ).fetchall()

            matrix["total_risks"] = len(rows)

            for row in rows:
                d = _row_to_dict(row)
                d["severity_label"] = _sev_label(d.get("severity", 0) or 0)
                d["trigger_json"] = _safe_json(d.get("trigger_json"))
                d["cure_packet_json"] = _safe_json(d.get("cure_packet_json"))
                d["authority_refs_json"] = _safe_json(d.get("authority_refs_json"))

                # By severity
                label = d["severity_label"]
                if label in matrix["by_severity"]:
                    matrix["by_severity"][label].append(d)

                # By forum
                forum = d.get("forum", "*") or "*"
                matrix["by_forum"].setdefault(forum, []).append(d)

                # Unmitigated: no cure packet
                cure = d.get("cure_packet_json")
                if not cure or cure == "null":
                    matrix["unmitigated"].append(d)

                # Cure deadlines
                deadline = d.get("cure_deadline_clock")
                if deadline:
                    matrix["cure_deadlines"].append({
                        "risk_id": d["risk_type_id"],
                        "title": d["title"],
                        "severity": d["severity"],
                        "severity_label": label,
                        "deadline": deadline,
                        "forum": forum,
                    })

            # Sort deadlines by severity descending
            matrix["cure_deadlines"].sort(
                key=lambda x: x.get("severity", 0) or 0, reverse=True
            )

            conn.close()
        except Exception:
            pass
        return matrix

    # ── Opponent Weakness Analysis ────────────────────────────────────

    def find_opponent_weaknesses(self) -> List[Dict]:
        """Search for opponent (Watson) weaknesses across evidence tables.
        Scans contradiction_map, impeachment_items, and evidence_quotes.
        """
        weaknesses: List[Dict] = []
        try:
            conn = self._conn()
            if not conn:
                return weaknesses

            # 1. Contradictions involving Watson
            try:
                rows = conn.execute(
                    "SELECT id, source_a_text, source_b_text, "
                    "contradiction_type, severity, legal_impact "
                    "FROM contradiction_map "
                    "WHERE source_a_text LIKE '%Watson%' "
                    "   OR source_b_text LIKE '%Watson%' "
                    "   OR source_a_text LIKE '%Tiffany%' "
                    "   OR source_b_text LIKE '%Tiffany%' "
                    "ORDER BY CASE severity "
                    "  WHEN 'critical' THEN 1 WHEN 'high' THEN 2 "
                    "  WHEN 'medium' THEN 3 ELSE 4 END "
                    "LIMIT 20"
                ).fetchall()
                for row in rows:
                    weaknesses.append({
                        "source": "contradiction_map",
                        "type": "contradiction",
                        "severity": row["severity"] or "",
                        "description": row["contradiction_type"] or "",
                        "detail_a": row["source_a_text"] or "",
                        "detail_b": row["source_b_text"] or "",
                        "legal_impact": row["legal_impact"] or "",
                        "exploitation": "Impeach with contradicting statements; "
                                        "cite MRE 613 prior inconsistent statements.",
                    })
            except Exception:
                pass

            # 2. Impeachment items where speaker is Watson
            try:
                rows = conn.execute(
                    "SELECT id, speaker, statement, contradicting_text, "
                    "legal_hook, severity "
                    "FROM impeachment_items "
                    "WHERE speaker LIKE '%Watson%' OR speaker LIKE '%Tiffany%' "
                    "ORDER BY CASE severity "
                    "  WHEN 'critical' THEN 1 WHEN 'high' THEN 2 "
                    "  WHEN 'medium' THEN 3 ELSE 4 END "
                    "LIMIT 20"
                ).fetchall()
                for row in rows:
                    weaknesses.append({
                        "source": "impeachment_items",
                        "type": "impeachment",
                        "severity": row["severity"] or "",
                        "description": f"Speaker: {row['speaker'] or ''}",
                        "detail_a": row["statement"] or "",
                        "detail_b": row["contradicting_text"] or "",
                        "legal_impact": row["legal_hook"] or "",
                        "exploitation": "Use at deposition/cross-exam; "
                                        "confront with contradicting evidence per MRE 613.",
                    })
            except Exception:
                pass

            # 3. Evidence quotes indicating credibility issues
            try:
                rows = conn.execute(
                    "SELECT quote_text, speaker, legal_significance, "
                    "evidence_category "
                    "FROM evidence_quotes "
                    "WHERE (speaker LIKE '%Watson%' OR speaker LIKE '%Tiffany%') "
                    "  AND (legal_significance LIKE '%credib%' "
                    "       OR legal_significance LIKE '%false%' "
                    "       OR legal_significance LIKE '%inconsist%' "
                    "       OR legal_significance LIKE '%contradict%' "
                    "       OR evidence_category LIKE '%credib%') "
                    "LIMIT 15"
                ).fetchall()
                for row in rows:
                    weaknesses.append({
                        "source": "evidence_quotes",
                        "type": "credibility",
                        "severity": "high",
                        "description": row["evidence_category"] or "",
                        "detail_a": row["quote_text"] or "",
                        "detail_b": row["legal_significance"] or "",
                        "legal_impact": "Credibility challenge under MRE 608/609.",
                        "exploitation": "Establish pattern of dishonesty; "
                                        "undermine testimony credibility at trial.",
                    })
            except Exception:
                pass

            # Sort: critical > high > medium > low
            sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            weaknesses.sort(
                key=lambda x: sev_order.get(
                    (x.get("severity") or "medium").lower(), 3
                )
            )

            conn.close()
        except Exception:
            pass
        return weaknesses

    # ── Filing Risk Score ─────────────────────────────────────────────

    def get_filing_risk_score(self, filing_type: str) -> Dict:
        """Assess risk score (1-10) for a specific filing type.
        Combines attack count, risk levels, and evidence strength.
        """
        score_result: Dict = {
            "filing_type": filing_type,
            "attacks_found": 0,
            "risk_score": 0,
            "risk_label": "",
            "attack_breakdown": [],
            "weakest_rebuttal": None,
            "mitigations": [],
        }
        try:
            attacks = self.get_known_attacks(filing_vehicle=filing_type)

            # Also include ALL_FILINGS generic attacks
            generic = self.get_known_attacks(filing_vehicle="ALL_FILINGS")
            seen_ids = {a.get("id") for a in attacks}
            for g in generic:
                if g.get("id") not in seen_ids:
                    attacks.append(g)

            score_result["attacks_found"] = len(attacks)

            if not attacks:
                score_result["risk_score"] = 1
                score_result["risk_label"] = "VERY LOW"
                score_result["mitigations"] = [
                    "No known attack patterns. Proceed with standard preparation."
                ]
                return score_result

            # Compute weighted score
            total_weight = 0
            weakest = None
            weakest_strength = "strong"
            strength_order = {"weak": 3, "moderate": 2, "strong": 1}

            for atk in attacks:
                rl = (atk.get("risk_level") or "MEDIUM").upper()
                w = _RISK_WEIGHTS.get(rl, 2)
                total_weight += w

                ev_str = (atk.get("our_evidence_strength") or "moderate").lower()
                score_result["attack_breakdown"].append({
                    "attack_type": atk.get("attack_type", ""),
                    "risk_level": rl,
                    "evidence_strength": ev_str,
                    "rebuttal_ready": bool(atk.get("rebuttal_strategy")),
                })

                # Track weakest rebuttal
                if strength_order.get(ev_str, 2) > strength_order.get(weakest_strength, 1):
                    weakest_strength = ev_str
                    weakest = atk

            # Scale to 1-10: max possible is 4 * attack_count
            max_possible = 4 * len(attacks)
            raw = (total_weight / max_possible) * 10 if max_possible else 1
            score_result["risk_score"] = round(min(max(raw, 1), 10), 1)

            if score_result["risk_score"] >= 8:
                score_result["risk_label"] = "CRITICAL"
            elif score_result["risk_score"] >= 6:
                score_result["risk_label"] = "HIGH"
            elif score_result["risk_score"] >= 4:
                score_result["risk_label"] = "MEDIUM"
            else:
                score_result["risk_label"] = "LOW"

            if weakest:
                score_result["weakest_rebuttal"] = {
                    "attack_type": weakest.get("attack_type", ""),
                    "evidence_strength": weakest_strength,
                    "rebuttal_strategy": weakest.get("rebuttal_strategy", ""),
                }

            # Mitigations
            if score_result["risk_score"] >= 7:
                score_result["mitigations"].append(
                    "Strengthen weak rebuttals before filing."
                )
                score_result["mitigations"].append(
                    "Consider pre-emptive motion to address anticipated attacks."
                )
            if weakest_strength == "weak":
                score_result["mitigations"].append(
                    f"Priority: shore up evidence for "
                    f"'{weakest.get('attack_type', '')}' rebuttal."
                )
            crit = [
                a for a in attacks
                if (a.get("risk_level") or "").upper() == "CRITICAL"
            ]
            if crit:
                score_result["mitigations"].append(
                    f"{len(crit)} CRITICAL attack(s) identified — "
                    f"prepare dedicated rebuttal packets."
                )

        except Exception:
            pass
        return score_result


# ── Self-Test ─────────────────────────────────────────────────────────


def self_test() -> Dict:
    """Run diagnostic checks on all AdversaryWarRoom methods."""
    results: Dict = {
        "skill": "adversary_war_room",
        "tests": {},
        "passed": 0,
        "failed": 0,
        "status": "UNKNOWN",
    }
    wr = AdversaryWarRoom()

    # Test 1: get_known_attacks
    try:
        attacks = wr.get_known_attacks(limit=5)
        ok = isinstance(attacks, list) and len(attacks) > 0
        results["tests"]["get_known_attacks"] = {
            "passed": ok, "count": len(attacks),
        }
        results["passed" if ok else "failed"] += 1
    except Exception as e:
        results["tests"]["get_known_attacks"] = {"passed": False, "error": str(e)}
        results["failed"] += 1

    # Test 2: get_risk_events
    try:
        risks = wr.get_risk_events(limit=5)
        ok = isinstance(risks, list) and len(risks) > 0
        results["tests"]["get_risk_events"] = {
            "passed": ok, "count": len(risks),
        }
        results["passed" if ok else "failed"] += 1
    except Exception as e:
        results["tests"]["get_risk_events"] = {"passed": False, "error": str(e)}
        results["failed"] += 1

    # Test 3: predict_attacks
    try:
        preds = wr.predict_attacks("COA_APPEAL")
        ok = isinstance(preds, list) and len(preds) > 0
        results["tests"]["predict_attacks"] = {
            "passed": ok, "count": len(preds),
        }
        results["passed" if ok else "failed"] += 1
    except Exception as e:
        results["tests"]["predict_attacks"] = {"passed": False, "error": str(e)}
        results["failed"] += 1

    # Test 4: build_rebuttal_packet
    try:
        packet = wr.build_rebuttal_packet("standing")
        ok = isinstance(packet, dict) and "attacks" in packet
        results["tests"]["build_rebuttal_packet"] = {
            "passed": ok, "summary": packet.get("summary", ""),
        }
        results["passed" if ok else "failed"] += 1
    except Exception as e:
        results["tests"]["build_rebuttal_packet"] = {"passed": False, "error": str(e)}
        results["failed"] += 1

    # Test 5: war_game_scenario
    try:
        scenario = wr.war_game_scenario("COA_APPEAL")
        ok = isinstance(scenario, dict) and "rounds" in scenario
        results["tests"]["war_game_scenario"] = {
            "passed": ok,
            "rounds": len(scenario.get("rounds", [])),
            "risk_label": scenario.get("risk_label", ""),
        }
        results["passed" if ok else "failed"] += 1
    except Exception as e:
        results["tests"]["war_game_scenario"] = {"passed": False, "error": str(e)}
        results["failed"] += 1

    # Test 6: get_risk_matrix
    try:
        mx = wr.get_risk_matrix()
        ok = isinstance(mx, dict) and mx.get("total_risks", 0) > 0
        results["tests"]["get_risk_matrix"] = {
            "passed": ok, "total_risks": mx.get("total_risks", 0),
        }
        results["passed" if ok else "failed"] += 1
    except Exception as e:
        results["tests"]["get_risk_matrix"] = {"passed": False, "error": str(e)}
        results["failed"] += 1

    # Test 7: find_opponent_weaknesses
    try:
        weak = wr.find_opponent_weaknesses()
        ok = isinstance(weak, list)
        results["tests"]["find_opponent_weaknesses"] = {
            "passed": ok, "count": len(weak),
        }
        results["passed" if ok else "failed"] += 1
    except Exception as e:
        results["tests"]["find_opponent_weaknesses"] = {"passed": False, "error": str(e)}
        results["failed"] += 1

    # Test 8: get_filing_risk_score
    try:
        score = wr.get_filing_risk_score("COA_APPEAL")
        ok = isinstance(score, dict) and "risk_score" in score
        results["tests"]["get_filing_risk_score"] = {
            "passed": ok,
            "risk_score": score.get("risk_score"),
            "risk_label": score.get("risk_label", ""),
        }
        results["passed" if ok else "failed"] += 1
    except Exception as e:
        results["tests"]["get_filing_risk_score"] = {"passed": False, "error": str(e)}
        results["failed"] += 1

    results["status"] = "PASS" if results["failed"] == 0 else "PARTIAL"
    return results


# ── CLI ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    usage = (
        "Adversary War Room Skill\n"
        "Usage:\n"
        "  python adversary_war_room.py --attacks [FILING_VEHICLE]\n"
        "  python adversary_war_room.py --risks [critical|high|medium|low]\n"
        "  python adversary_war_room.py --predict FILING_TYPE\n"
        "  python adversary_war_room.py --rebuttal ATTACK_TYPE\n"
        "  python adversary_war_room.py --wargame FILING_TYPE [OPPONENT_RESPONSE]\n"
        "  python adversary_war_room.py --matrix\n"
        "  python adversary_war_room.py --weaknesses\n"
        "  python adversary_war_room.py --score FILING_TYPE\n"
        "  python adversary_war_room.py --self-test\n"
    )

    if len(sys.argv) < 2:
        print(usage)
        sys.exit(0)

    cmd = sys.argv[1]
    wr = AdversaryWarRoom()

    if cmd == "--attacks":
        fv = sys.argv[2] if len(sys.argv) > 2 else None
        cycle_json(wr.get_known_attacks(filing_vehicle=fv))
    elif cmd == "--risks":
        sf = sys.argv[2] if len(sys.argv) > 2 else None
        cycle_json(wr.get_risk_events(severity_filter=sf))
    elif cmd == "--predict":
        ft = sys.argv[2] if len(sys.argv) > 2 else "COA_APPEAL"
        cycle_json(wr.predict_attacks(ft))
    elif cmd == "--rebuttal":
        at = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "standing"
        cycle_json(wr.build_rebuttal_packet(at))
    elif cmd == "--wargame":
        ft = sys.argv[2] if len(sys.argv) > 2 else "COA_APPEAL"
        opp = sys.argv[3] if len(sys.argv) > 3 else None
        cycle_json(wr.war_game_scenario(ft, opp))
    elif cmd == "--matrix":
        cycle_json(wr.get_risk_matrix())
    elif cmd == "--weaknesses":
        cycle_json(wr.find_opponent_weaknesses())
    elif cmd == "--score":
        ft = sys.argv[2] if len(sys.argv) > 2 else "COA_APPEAL"
        cycle_json(wr.get_filing_risk_score(ft))
    elif cmd == "--self-test":
        cycle_json(self_test())
    else:
        print(usage)
