"""
DELTA 6 — Predictive Filing Optimizer
======================================
Monte Carlo simulation of filing outcomes using evidence strength,
authority PageRank, and adversary attack patterns.

Usage:
    python filing_optimizer.py test
    python filing_optimizer.py score <filing_type>
    python filing_optimizer.py simulate <filing_type> [n_simulations]
    python filing_optimizer.py compare <type1> <type2> ...
    python filing_optimizer.py order <type1> <type2> ...
    python filing_optimizer.py weakest <filing_type>
    python filing_optimizer.py report [type1 type2 ...]
"""

import json
import logging
import os
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)

# Default filing types for comprehensive reports
DEFAULT_FILINGS = [
    "MSC_ORIGINAL_ACTION",
    "COA_APPELLATE_BRIEF",
    "EMERGENCY_MOTION_RESTORE_PT",
    "JUDICIAL_DISQUALIFICATION",
    "JTC_COMPLAINT",
]

# Map user-friendly names to DB vehicle_name / filing_vehicle patterns
FILING_ALIASES = {
    "MSC_ORIGINAL_ACTION": ["MSC", "ORIGINAL_ACTION", "MSC_ORIGINAL"],
    "COA_APPELLATE_BRIEF": ["COA", "APPELLATE_BRIEF", "COA_APPLICATION_LEAVE_APPEAL", "COA_BRIEF"],
    "EMERGENCY_MOTION_RESTORE_PT": ["EMERGENCY", "RESTORE_PT", "EMERGENCY_MOTION_RESTORE_PT", "PARENTING_TIME"],
    "JUDICIAL_DISQUALIFICATION": ["DISQUALIFICATION", "JUDICIAL_DISQUALIFICATION", "DISQ"],
    "JTC_COMPLAINT": ["JTC", "JTC_COMPLAINT", "JUDICIAL_TENURE"],
    "MOTION_CHANGE_CUSTODY": ["CUSTODY", "CHANGE_CUSTODY", "MOTION_CHANGE_CUSTODY"],
    "MOTION_COMPEL_DISCOVERY": ["COMPEL", "DISCOVERY", "MOTION_COMPEL_DISCOVERY"],
    "PPO_TERMINATION": ["PPO", "PPO_TERMINATION"],
    "CONTEMPT_MOTION": ["CONTEMPT", "CONTEMPT_MOTION"],
    "SUPERINTENDING_CONTROL": ["SUPERINTENDING", "SUPERINTENDING_CONTROL"],
}


def _get_db() -> sqlite3.Connection:
    """Get read-only DB connection."""
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA query_only=ON")
    conn.execute("PRAGMA cache_size=-65536")
    conn.row_factory = sqlite3.Row
    return conn


def _safe_float(val: Any, default: float = 0.0) -> float:
    """Safely convert a value to float."""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


class FilingOptimizer:
    """Predictive filing optimizer using Monte Carlo simulation."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        self._conn: Optional[sqlite3.Connection] = None
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._cache_ttl = 300  # 5 minutes
        self._error_log: List[str] = []

    def _get_db(self) -> Optional[sqlite3.Connection]:
        """Get DB connection with reuse + reconnect."""
        if self._conn is not None:
            try:
                self._conn.execute("SELECT 1")
                return self._conn
            except Exception:
                self._conn = None

        for attempt in range(3):
            try:
                self._conn = sqlite3.connect(self.db_path, timeout=30)
                self._conn.execute("PRAGMA journal_mode=WAL")
                self._conn.execute("PRAGMA query_only=ON")
                self._conn.execute("PRAGMA cache_size=-65536")
                self._conn.row_factory = sqlite3.Row
                return self._conn
            except Exception as e:
                wait = 2 ** attempt
                logger.warning(f"DB connect attempt {attempt + 1} failed: {e}, retry in {wait}s")
                self._error_log.append(f"DB connect fail #{attempt + 1}: {e}")
                time.sleep(wait)
        return None

    def _cached(self, key: str) -> Optional[Any]:
        """Check cache for a key."""
        if key in self._cache:
            ts, val = self._cache[key]
            if time.time() - ts < self._cache_ttl:
                return val
            del self._cache[key]
        return None

    def _set_cache(self, key: str, val: Any) -> None:
        """Store in cache with LRU eviction."""
        if len(self._cache) >= 1000:
            oldest_key = min(self._cache, key=lambda k: self._cache[k][0])
            del self._cache[oldest_key]
        self._cache[key] = (time.time(), val)

    def _resolve_filing(self, filing_type: str) -> str:
        """Normalize a filing type string to canonical form."""
        up = filing_type.upper().replace(" ", "_").replace("-", "_")
        for canonical, aliases in FILING_ALIASES.items():
            if up == canonical or up in aliases:
                return canonical
        return up

    def _match_patterns(self, filing_type: str) -> List[str]:
        """Return SQL LIKE patterns for matching a filing type across tables."""
        canonical = self._resolve_filing(filing_type)
        patterns = [f"%{canonical}%"]
        aliases = FILING_ALIASES.get(canonical, [])
        for a in aliases:
            patterns.append(f"%{a}%")
        # Add the raw input too
        raw = filing_type.upper().replace(" ", "_").replace("-", "_")
        if f"%{raw}%" not in patterns:
            patterns.append(f"%{raw}%")
        return patterns

    # ------------------------------------------------------------------
    # Data gathering helpers
    # ------------------------------------------------------------------

    def _query_evidence_strength(self, filing_type: str) -> Dict[str, Any]:
        """Query evidence_quotes for evidence supporting this filing type."""
        conn = self._get_db()
        if not conn:
            return {"count": 0, "score": 0.0, "error": "no_db"}

        try:
            patterns = self._match_patterns(filing_type)
            total = 0
            high_significance = 0

            # FTS search on evidence_quotes_fts
            fts_terms = []
            canonical = self._resolve_filing(filing_type)
            for alias in FILING_ALIASES.get(canonical, [canonical]):
                # Split underscores into words for FTS
                words = alias.lower().replace("_", " ").split()
                fts_terms.extend(words)
            fts_terms = list(set(fts_terms))

            if fts_terms:
                fts_query = " OR ".join(fts_terms[:8])
                try:
                    row = conn.execute(
                        "SELECT COUNT(*) as cnt FROM evidence_quotes_fts WHERE evidence_quotes_fts MATCH ?",
                        (fts_query,),
                    ).fetchone()
                    total = row["cnt"] if row else 0
                except Exception:
                    # Fallback: LIKE on evidence_category
                    for p in patterns[:3]:
                        row = conn.execute(
                            "SELECT COUNT(*) as cnt FROM evidence_quotes WHERE evidence_category LIKE ?",
                            (p,),
                        ).fetchone()
                        total += row["cnt"] if row else 0

            # Check high-significance evidence
            try:
                row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM evidence_quotes WHERE legal_significance IS NOT NULL AND legal_significance != ''"
                ).fetchone()
                high_significance = row["cnt"] if row else 0
            except Exception:
                pass

            # Normalize: 0 evidence = 0, 100+ = 80, 500+ = 95, 1000+ = 100
            if total >= 1000:
                score = 100.0
            elif total >= 500:
                score = 95.0
            elif total >= 100:
                score = 80.0 + (total - 100) * 0.0375
            elif total >= 10:
                score = 40.0 + (total - 10) * (40.0 / 90.0)
            elif total > 0:
                score = total * 4.0
            else:
                score = 0.0

            return {"count": total, "high_significance": high_significance, "score": min(score, 100.0)}
        except Exception as e:
            self._error_log.append(f"evidence query error: {e}")
            return {"count": 0, "score": 0.0, "error": str(e)}

    def _query_authority_strength(self, filing_type: str) -> Dict[str, Any]:
        """Query auth_rules for authority supporting this filing type."""
        conn = self._get_db()
        if not conn:
            return {"count": 0, "score": 0.0, "error": "no_db"}

        try:
            canonical = self._resolve_filing(filing_type)
            fts_terms = []
            for alias in FILING_ALIASES.get(canonical, [canonical]):
                words = alias.lower().replace("_", " ").split()
                fts_terms.extend(words)
            fts_terms = list(set(fts_terms))

            count = 0
            if fts_terms:
                fts_query = " OR ".join(fts_terms[:8])
                try:
                    row = conn.execute(
                        "SELECT COUNT(*) as cnt FROM auth_rules_fts WHERE auth_rules_fts MATCH ?",
                        (fts_query,),
                    ).fetchone()
                    count = row["cnt"] if row else 0
                except Exception:
                    pass

            # Also count master_citations matches
            citation_count = 0
            try:
                patterns = self._match_patterns(filing_type)
                for p in patterns[:2]:
                    row = conn.execute(
                        "SELECT COUNT(*) as cnt FROM master_citations WHERE context LIKE ?",
                        (p,),
                    ).fetchone()
                    citation_count += row["cnt"] if row else 0
            except Exception:
                pass

            total = count + citation_count
            # Normalize: 0 = 0, 10+ = 60, 50+ = 85, 100+ = 95, 200+ = 100
            if total >= 200:
                score = 100.0
            elif total >= 100:
                score = 95.0
            elif total >= 50:
                score = 85.0 + (total - 50) * 0.2
            elif total >= 10:
                score = 60.0 + (total - 10) * (25.0 / 40.0)
            elif total > 0:
                score = total * 6.0
            else:
                score = 0.0

            return {"rule_count": count, "citation_count": citation_count, "total": total, "score": min(score, 100.0)}
        except Exception as e:
            self._error_log.append(f"authority query error: {e}")
            return {"count": 0, "score": 0.0, "error": str(e)}

    def _query_adversary_risk(self, filing_type: str) -> Dict[str, Any]:
        """Query adversary_models for known attack patterns."""
        conn = self._get_db()
        if not conn:
            return {"attacks": 0, "high_risk": 0, "risk_score": 50.0, "error": "no_db"}

        try:
            patterns = self._match_patterns(filing_type)
            attacks = []
            for p in patterns:
                rows = conn.execute(
                    "SELECT attack_type, risk_level, rebuttal_strategy FROM adversary_models WHERE UPPER(filing_vehicle) LIKE ?",
                    (p,),
                ).fetchall()
                attacks.extend([dict(r) for r in rows])

            # Deduplicate by attack_type
            seen = set()
            unique = []
            for a in attacks:
                key = a.get("attack_type", "")
                if key not in seen:
                    seen.add(key)
                    unique.append(a)

            total = len(unique)
            high_risk = sum(1 for a in unique if a.get("risk_level", "").upper() == "HIGH")
            medium_risk = sum(1 for a in unique if a.get("risk_level", "").upper() == "MEDIUM")
            has_rebuttal = sum(1 for a in unique if a.get("rebuttal_strategy"))

            # Risk score: more HIGH attacks = higher risk; rebuttals reduce risk
            base_risk = high_risk * 15 + medium_risk * 8 + (total - high_risk - medium_risk) * 3
            rebuttal_mitigation = has_rebuttal * 5
            risk_score = min(max(base_risk - rebuttal_mitigation, 0), 100)

            return {
                "total_attacks": total,
                "high_risk": high_risk,
                "medium_risk": medium_risk,
                "rebuttals_available": has_rebuttal,
                "risk_score": float(risk_score),
                "attacks": unique[:10],
            }
        except Exception as e:
            self._error_log.append(f"adversary query error: {e}")
            return {"attacks": 0, "risk_score": 50.0, "error": str(e)}

    def _query_filing_readiness(self, filing_type: str) -> Dict[str, Any]:
        """Query filing_readiness table."""
        conn = self._get_db()
        if not conn:
            return {"found": False, "total_score": 0, "error": "no_db"}

        try:
            patterns = self._match_patterns(filing_type)
            for p in patterns:
                row = conn.execute(
                    "SELECT * FROM filing_readiness WHERE UPPER(vehicle_name) LIKE ?",
                    (p,),
                ).fetchone()
                if row:
                    d = dict(row)
                    return {
                        "found": True,
                        "vehicle_name": d.get("vehicle_name"),
                        "authority_score": _safe_float(d.get("authority_score")),
                        "evidence_score": _safe_float(d.get("evidence_score")),
                        "compliance_score": _safe_float(d.get("compliance_score")),
                        "impeachment_score": _safe_float(d.get("impeachment_score")),
                        "total_score": _safe_float(d.get("total_score")),
                        "gaps": d.get("gaps", ""),
                        "strengths": d.get("strengths", ""),
                        "status": d.get("status", "UNKNOWN"),
                        "attack_vectors": int(d.get("attack_vectors", 0)),
                        "rebuttals_ready": int(d.get("rebuttals_ready", 0)),
                    }

            # Fallback: check legal_action_scores
            for p in patterns:
                row = conn.execute(
                    "SELECT * FROM legal_action_scores WHERE UPPER(action_name) LIKE ?",
                    (p,),
                ).fetchone()
                if row:
                    d = dict(row)
                    return {
                        "found": True,
                        "vehicle_name": d.get("action_name"),
                        "authority_score": _safe_float(d.get("authority_score")),
                        "evidence_score": _safe_float(d.get("evidence_score")),
                        "compliance_score": _safe_float(d.get("compliance_score")),
                        "total_score": _safe_float(d.get("overall_score")),
                        "gaps": d.get("gaps", ""),
                        "status": "FROM_ACTION_SCORES",
                    }

            return {"found": False, "total_score": 0}
        except Exception as e:
            self._error_log.append(f"readiness query error: {e}")
            return {"found": False, "total_score": 0, "error": str(e)}

    def _query_gaps(self, filing_type: str) -> Dict[str, Any]:
        """Query gap_tickets for unresolved gaps."""
        conn = self._get_db()
        if not conn:
            return {"total": 0, "unresolved": 0, "critical": 0, "error": "no_db"}

        try:
            patterns = self._match_patterns(filing_type)
            gaps = []
            for p in patterns:
                rows = conn.execute(
                    "SELECT * FROM gap_tickets WHERE UPPER(filing_name) LIKE ? OR UPPER(description) LIKE ?",
                    (p, p),
                ).fetchall()
                gaps.extend([dict(r) for r in rows])

            # Also get SYSTEM-level unresolved gaps
            sys_rows = conn.execute(
                "SELECT * FROM gap_tickets WHERE resolution_status != 'resolved'"
            ).fetchall()
            unresolved_system = [dict(r) for r in sys_rows]

            # Deduplicate
            seen = set()
            unique = []
            for g in gaps:
                tid = g.get("ticket_id", "")
                if tid not in seen:
                    seen.add(tid)
                    unique.append(g)

            total = len(unique)
            unresolved = sum(1 for g in unique if g.get("resolution_status") != "resolved")
            critical = sum(1 for g in unique if g.get("severity", "").lower() == "critical" and g.get("resolution_status") != "resolved")

            # Also count total unresolved across system
            total_unresolved_system = sum(1 for g in unresolved_system if g.get("resolution_status") != "resolved")

            return {
                "filing_gaps": total,
                "unresolved": unresolved,
                "critical_unresolved": critical,
                "system_unresolved": total_unresolved_system,
                "gap_details": [
                    {"id": g.get("ticket_id"), "type": g.get("gap_type"), "severity": g.get("severity"),
                     "description": g.get("description", "")[:200], "status": g.get("resolution_status")}
                    for g in unique[:10]
                ],
            }
        except Exception as e:
            self._error_log.append(f"gaps query error: {e}")
            return {"total": 0, "unresolved": 0, "critical": 0, "error": str(e)}

    def _query_judicial_bias_factor(self) -> float:
        """Compute judicial bias factor from judicial_violations count."""
        cached = self._cached("judicial_bias")
        if cached is not None:
            return cached

        conn = self._get_db()
        if not conn:
            return 0.3  # default high bias assumption

        try:
            row = conn.execute("SELECT COUNT(*) as cnt FROM judicial_violations").fetchone()
            count = row["cnt"] if row else 0

            # 1127 violations = very high bias risk
            # Scale: 0 violations = 0.0 bias, 100 = 0.15, 500 = 0.25, 1000+ = 0.35
            if count >= 1000:
                factor = 0.35
            elif count >= 500:
                factor = 0.25 + (count - 500) * (0.10 / 500.0)
            elif count >= 100:
                factor = 0.15 + (count - 100) * (0.10 / 400.0)
            else:
                factor = count * 0.0015

            self._set_cache("judicial_bias", factor)
            return factor
        except Exception as e:
            self._error_log.append(f"judicial bias query error: {e}")
            return 0.3

    def _query_deadlines(self, filing_type: str) -> Dict[str, Any]:
        """Query deadlines for urgency."""
        conn = self._get_db()
        if not conn:
            return {"has_deadline": False, "error": "no_db"}

        try:
            patterns = self._match_patterns(filing_type)
            for p in patterns:
                rows = conn.execute(
                    "SELECT * FROM deadlines WHERE UPPER(title) LIKE ? AND status != 'satisfied' ORDER BY due_date_iso ASC",
                    (p,),
                ).fetchall()
                if rows:
                    d = dict(rows[0])
                    due = d.get("due_date_iso", "")
                    days_left = None
                    if due:
                        try:
                            due_dt = datetime.strptime(due[:10], "%Y-%m-%d")
                            days_left = (due_dt - datetime.now()).days
                        except Exception:
                            pass
                    return {
                        "has_deadline": True,
                        "title": d.get("title"),
                        "due_date": due,
                        "days_remaining": days_left,
                        "basis_authority": d.get("basis_authority"),
                        "risk_if_missed": d.get("risk_if_missed"),
                        "urgency": "CRITICAL" if days_left is not None and days_left <= 14 else
                                   "HIGH" if days_left is not None and days_left <= 30 else
                                   "MODERATE" if days_left is not None and days_left <= 60 else "LOW",
                    }

            # Check all upcoming deadlines
            rows = conn.execute(
                "SELECT * FROM deadlines WHERE status NOT IN ('satisfied','expired') ORDER BY due_date_iso ASC LIMIT 5"
            ).fetchall()
            upcoming = []
            for r in rows:
                d = dict(r)
                due = d.get("due_date_iso", "")
                days_left = None
                if due:
                    try:
                        due_dt = datetime.strptime(due[:10], "%Y-%m-%d")
                        days_left = (due_dt - datetime.now()).days
                    except Exception:
                        pass
                upcoming.append({
                    "title": d.get("title"),
                    "due_date": due,
                    "days_remaining": days_left,
                })

            return {"has_deadline": False, "upcoming_deadlines": upcoming}
        except Exception as e:
            self._error_log.append(f"deadlines query error: {e}")
            return {"has_deadline": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Core methods
    # ------------------------------------------------------------------

    def score_filing(self, filing_type: str) -> Dict[str, Any]:
        """Score a filing's probability of success (0-100)."""
        cache_key = f"score:{filing_type}"
        cached = self._cached(cache_key)
        if cached is not None:
            return cached

        canonical = self._resolve_filing(filing_type)

        evidence = self._query_evidence_strength(filing_type)
        authority = self._query_authority_strength(filing_type)
        adversary = self._query_adversary_risk(filing_type)
        readiness = self._query_filing_readiness(filing_type)
        gaps = self._query_gaps(filing_type)
        bias_factor = self._query_judicial_bias_factor()

        evidence_score = evidence.get("score", 0.0)
        authority_score = authority.get("score", 0.0)
        risk_score = adversary.get("risk_score", 50.0)

        # Incorporate filing_readiness total_score if available
        readiness_score = _safe_float(readiness.get("total_score", 0))

        # Gap penalty: each unresolved critical gap = -5, each unresolved = -2
        gap_penalty = gaps.get("critical_unresolved", 0) * 5 + gaps.get("unresolved", 0) * 2

        # Composite score: weighted combination
        # Evidence: 30%, Authority: 25%, Readiness: 25%, Risk mitigation: 20%
        risk_mitigation = max(100.0 - risk_score, 0)

        raw_score = (
            evidence_score * 0.30
            + authority_score * 0.25
            + readiness_score * 0.25
            + risk_mitigation * 0.20
        )

        # Apply gap penalty and bias factor
        adjusted = raw_score - gap_penalty - (bias_factor * 15)
        overall = max(min(adjusted, 100.0), 0.0)

        # Recommendation
        if overall >= 80:
            recommendation = "STRONG — File with confidence. High probability of success."
        elif overall >= 60:
            recommendation = "VIABLE — File with preparation. Address identified gaps first."
        elif overall >= 40:
            recommendation = "MARGINAL — Significant weaknesses exist. Cure gaps before filing."
        elif overall >= 20:
            recommendation = "WEAK — Major deficiencies. Consider alternative strategies."
        else:
            recommendation = "NOT READY — Insufficient evidence/authority. Do not file."

        result = {
            "filing_type": canonical,
            "overall_score": round(overall, 1),
            "evidence_score": round(evidence_score, 1),
            "authority_score": round(authority_score, 1),
            "risk_score": round(risk_score, 1),
            "readiness_score": round(readiness_score, 1),
            "judicial_bias_factor": round(bias_factor, 3),
            "gap_penalty": gap_penalty,
            "gaps": {
                "unresolved": gaps.get("unresolved", 0),
                "critical": gaps.get("critical_unresolved", 0),
                "details": gaps.get("gap_details", []),
            },
            "adversary_attacks": {
                "total": adversary.get("total_attacks", 0),
                "high_risk": adversary.get("high_risk", 0),
                "rebuttals": adversary.get("rebuttals_available", 0),
            },
            "readiness_status": readiness.get("status", "UNKNOWN"),
            "recommendation": recommendation,
        }

        self._set_cache(cache_key, result)
        return result

    def simulate_outcomes(self, filing_type: str, n_simulations: int = 1000) -> Dict[str, Any]:
        """Monte Carlo simulation of filing outcomes."""
        score_data = self.score_filing(filing_type)
        evidence_score = score_data["evidence_score"] / 100.0
        authority_score = score_data["authority_score"] / 100.0
        risk_score = score_data["risk_score"] / 100.0
        readiness_score = score_data["readiness_score"] / 100.0
        bias_factor = score_data["judicial_bias_factor"]

        rng = np.random.default_rng(seed=42)
        outcomes = np.zeros(n_simulations)

        for i in range(n_simulations):
            # Sample evidence contribution from beta distribution
            # Shape params derived from score: high score = right-skewed toward 1
            ev_alpha = max(evidence_score * 10, 0.5)
            ev_beta = max((1 - evidence_score) * 10, 0.5)
            ev_sample = rng.beta(ev_alpha, ev_beta)

            # Sample authority contribution
            auth_alpha = max(authority_score * 8, 0.5)
            auth_beta = max((1 - authority_score) * 8, 0.5)
            auth_sample = rng.beta(auth_alpha, auth_beta)

            # Readiness as a bounded factor
            ready_alpha = max(readiness_score * 6, 0.5)
            ready_beta = max((1 - readiness_score) * 6, 0.5)
            ready_sample = rng.beta(ready_alpha, ready_beta)

            # Risk reduction: adversary attacks pull down outcome
            risk_drag = rng.beta(max(risk_score * 5, 0.5), max((1 - risk_score) * 5, 0.5))

            # Judicial bias: random perturbation from bias factor
            # Higher bias = more random negative outcomes
            bias_noise = rng.normal(0, bias_factor)

            # Composite: weighted sum + noise
            raw = (
                ev_sample * 0.30
                + auth_sample * 0.25
                + ready_sample * 0.25
                + (1.0 - risk_drag) * 0.20
            )

            # Apply bias noise
            outcome = raw + bias_noise

            # Random judicial unpredictability (±5%)
            outcome += rng.normal(0, 0.05)

            outcomes[i] = max(min(outcome, 1.0), 0.0)

        # Compute statistics
        outcomes_pct = outcomes * 100

        mean = float(np.mean(outcomes_pct))
        median = float(np.median(outcomes_pct))
        std = float(np.std(outcomes_pct))
        p5 = float(np.percentile(outcomes_pct, 5))
        p95 = float(np.percentile(outcomes_pct, 95))
        best = float(np.max(outcomes_pct))
        worst = float(np.min(outcomes_pct))

        # Success probability: outcome >= 50 considered "success"
        success_prob = float(np.mean(outcomes >= 0.50)) * 100

        # Histogram: 10 bins
        hist_counts, hist_edges = np.histogram(outcomes_pct, bins=10, range=(0, 100))
        histogram = [
            {"range": f"{hist_edges[j]:.0f}-{hist_edges[j+1]:.0f}", "count": int(hist_counts[j])}
            for j in range(len(hist_counts))
        ]

        return {
            "filing_type": self._resolve_filing(filing_type),
            "n_simulations": n_simulations,
            "success_probability": round(success_prob, 1),
            "mean_outcome": round(mean, 1),
            "median_outcome": round(median, 1),
            "std_deviation": round(std, 1),
            "confidence_interval_95": [round(p5, 1), round(p95, 1)],
            "best_case": round(best, 1),
            "worst_case": round(worst, 1),
            "histogram": histogram,
        }

    def compare_filings(self, filing_types: List[str]) -> Dict[str, Any]:
        """Compare multiple filings side by side."""
        results = []
        for ft in filing_types:
            score = self.score_filing(ft)
            sim = self.simulate_outcomes(ft, n_simulations=500)
            results.append({
                "filing_type": score["filing_type"],
                "overall_score": score["overall_score"],
                "success_probability": sim["success_probability"],
                "confidence_interval_95": sim["confidence_interval_95"],
                "evidence_score": score["evidence_score"],
                "authority_score": score["authority_score"],
                "risk_score": score["risk_score"],
                "readiness_status": score["readiness_status"],
                "recommendation": score["recommendation"],
            })

        # Rank by overall score
        ranked = sorted(results, key=lambda x: x["overall_score"], reverse=True)
        for i, r in enumerate(ranked):
            r["rank"] = i + 1

        best = ranked[0] if ranked else None
        return {
            "comparison": ranked,
            "strongest_option": best["filing_type"] if best else None,
            "strongest_score": best["overall_score"] if best else 0,
            "strategic_note": (
                f"{best['filing_type']} is the strongest filing with {best['overall_score']}/100 "
                f"and {best['success_probability']}% simulated success rate."
            ) if best else "No filings to compare.",
        }

    def optimize_filing_order(self, filing_types: List[str]) -> List[Dict[str, Any]]:
        """Determine optimal order of filings considering dependencies and deadlines."""
        scored = []
        for ft in filing_types:
            score = self.score_filing(ft)
            deadline = self._query_deadlines(ft)
            canonical = self._resolve_filing(ft)

            days_remaining = None
            urgency_weight = 0
            if deadline.get("has_deadline") and deadline.get("days_remaining") is not None:
                days_remaining = deadline["days_remaining"]
                if days_remaining <= 7:
                    urgency_weight = 100
                elif days_remaining <= 14:
                    urgency_weight = 80
                elif days_remaining <= 30:
                    urgency_weight = 50
                elif days_remaining <= 60:
                    urgency_weight = 25
                else:
                    urgency_weight = 10

            # Strength multiplier: filings that strengthen later filings get a boost
            # Emergency PT + Disqualification strengthen appellate arguments
            strength_boost = 0
            if canonical in ("EMERGENCY_MOTION_RESTORE_PT", "JUDICIAL_DISQUALIFICATION"):
                strength_boost = 15  # These create appellate record
            elif canonical == "JTC_COMPLAINT":
                strength_boost = 5  # External pressure

            # Priority = urgency + score + strength_boost
            priority = urgency_weight + score["overall_score"] * 0.5 + strength_boost

            scored.append({
                "filing_type": canonical,
                "overall_score": score["overall_score"],
                "days_remaining": days_remaining,
                "urgency": deadline.get("urgency", "N/A") if deadline.get("has_deadline") else "NO_DEADLINE",
                "urgency_weight": urgency_weight,
                "strength_boost": strength_boost,
                "priority_score": round(priority, 1),
                "recommendation": score["recommendation"],
            })

        # Sort by priority descending
        ordered = sorted(scored, key=lambda x: x["priority_score"], reverse=True)
        for i, item in enumerate(ordered):
            item["order"] = i + 1

        return ordered

    def identify_weakest_link(self, filing_type: str) -> Dict[str, Any]:
        """Find the single weakest aspect of a filing."""
        score = self.score_filing(filing_type)

        dimensions = {
            "evidence": {
                "score": score["evidence_score"],
                "cure_suggestion": "Gather additional evidence quotes; run FTS search for supporting testimony; review transcripts for overlooked statements.",
                "impact_if_fixed": "Evidence is 30% of composite score — improving from low to high adds ~25 points.",
            },
            "authority": {
                "score": score["authority_score"],
                "cure_suggestion": "Research additional Michigan court rules and case law; check auth_rules_fts for related authority; verify all citations in master_citations.",
                "impact_if_fixed": "Authority is 25% of composite — strong citations dramatically improve credibility.",
            },
            "risk_exposure": {
                "score": score["risk_score"],  # Higher = worse
                "cure_suggestion": "Review adversary_models for unaddressed attack vectors; prepare rebuttals for HIGH-risk attacks; pre-empt arguments in filing.",
                "impact_if_fixed": "Reducing risk exposure from HIGH to LOW adds ~15-20 points to overall score.",
            },
            "readiness": {
                "score": score["readiness_score"],
                "cure_suggestion": "Complete filing checklist; ensure MCR 2.113 compliance; verify certificate of service; fill template gaps.",
                "impact_if_fixed": "Readiness is 25% of composite — a complete, compliant filing is prerequisite to success.",
            },
            "gaps": {
                "score": max(100.0 - score["gap_penalty"] * 5, 0),
                "cure_suggestion": "Resolve gap_tickets marked 'critical'; prioritize authority gaps over formatting gaps.",
                "impact_if_fixed": "Each resolved critical gap removes 5-point penalty from overall score.",
            },
        }

        # Find weakest (lowest score, except risk where highest = worst)
        weakest_name = None
        weakest_score = 101
        for name, dim in dimensions.items():
            effective_score = dim["score"]
            if name == "risk_exposure":
                effective_score = 100.0 - dim["score"]  # Invert: high risk = low effective
            if effective_score < weakest_score:
                weakest_score = effective_score
                weakest_name = name

        weakest = dimensions[weakest_name]
        return {
            "filing_type": self._resolve_filing(filing_type),
            "weakness": weakest_name,
            "category": weakest_name.replace("_", " ").title(),
            "current_score": round(weakest["score"], 1),
            "cure_suggestion": weakest["cure_suggestion"],
            "impact_if_fixed": weakest["impact_if_fixed"],
            "all_dimensions": {
                name: round(dim["score"], 1)
                for name, dim in dimensions.items()
            },
        }

    def generate_optimization_report(self, filing_types: List[str] = None) -> Dict[str, Any]:
        """Comprehensive optimization report across all filing types."""
        if not filing_types:
            filing_types = DEFAULT_FILINGS

        # Score all
        scores = {}
        for ft in filing_types:
            scores[ft] = self.score_filing(ft)

        # Simulate all
        simulations = {}
        for ft in filing_types:
            simulations[ft] = self.simulate_outcomes(ft, n_simulations=1000)

        # Compare
        comparison = self.compare_filings(filing_types)

        # Optimal order
        order = self.optimize_filing_order(filing_types)

        # Weakest links
        weakest_links = {}
        for ft in filing_types:
            weakest_links[ft] = self.identify_weakest_link(ft)

        # Judicial bias context
        bias_factor = self._query_judicial_bias_factor()

        # Build summary
        strongest = comparison["strongest_option"]
        strongest_score = comparison["strongest_score"]

        # Overall case readiness
        avg_score = np.mean([s["overall_score"] for s in scores.values()])
        avg_success = np.mean([s["success_probability"] for s in simulations.values()])

        if avg_score >= 70:
            overall_assessment = "STRONG POSITION — Multiple viable filing options with high success probability."
        elif avg_score >= 50:
            overall_assessment = "MODERATE POSITION — Several filings viable but gaps remain. Prioritize cures."
        elif avg_score >= 30:
            overall_assessment = "DEVELOPING — Foundation exists but significant work needed before filing."
        else:
            overall_assessment = "EARLY STAGE — Build evidence and authority base before committing to filings."

        return {
            "report_title": "DELTA 6 — Predictive Filing Optimization Report",
            "generated_at": datetime.now().isoformat(),
            "case": "Pigors v. Watson — Consolidated",
            "parent_child_separation_days": "329+",
            "overall_assessment": overall_assessment,
            "average_score": round(float(avg_score), 1),
            "average_success_probability": round(float(avg_success), 1),
            "judicial_bias_factor": round(bias_factor, 3),
            "judicial_violations_count": 1127,
            "strongest_filing": strongest,
            "strongest_score": strongest_score,
            "recommended_filing_order": order,
            "individual_scores": scores,
            "simulations": simulations,
            "comparison": comparison,
            "weakest_links": weakest_links,
            "strategic_recommendations": [
                f"1. FILE FIRST: {order[0]['filing_type']} (priority {order[0]['priority_score']})" if order else "",
                f"2. STRONGEST OPTION: {strongest} at {strongest_score}/100",
                f"3. AVERAGE SUCCESS RATE: {round(float(avg_success), 1)}% across {len(filing_types)} filings",
                f"4. JUDICIAL BIAS: {round(bias_factor * 100, 1)}% bias factor from {1127} documented violations — factor into expectations",
                "5. CURE GAPS: Address weakest links before filing to maximize success probability",
            ],
        }

    def close(self):
        """Close DB connection."""
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None


# ------------------------------------------------------------------
# Self-test
# ------------------------------------------------------------------

def self_test() -> Dict[str, Any]:
    """Run self-test to verify DB connectivity and core methods."""
    results = {"status": "ok", "tests": {}}
    optimizer = FilingOptimizer()

    # Test 1: DB connectivity
    try:
        conn = _get_db()
        conn.execute("SELECT 1").fetchone()
        conn.close()
        results["tests"]["db_connectivity"] = {"passed": True}
    except Exception as e:
        results["tests"]["db_connectivity"] = {"passed": False, "error": str(e)}

    # Test 2: score_filing
    try:
        score = optimizer.score_filing("EMERGENCY_MOTION_RESTORE_PT")
        passed = (
            isinstance(score, dict)
            and "overall_score" in score
            and 0 <= score["overall_score"] <= 100
            and "evidence_score" in score
            and "recommendation" in score
        )
        results["tests"]["score_filing"] = {
            "passed": passed,
            "filing_type": score.get("filing_type"),
            "overall_score": score.get("overall_score"),
            "recommendation": score.get("recommendation", "")[:80],
        }
    except Exception as e:
        results["tests"]["score_filing"] = {"passed": False, "error": str(e)}

    # Test 3: simulate_outcomes
    try:
        sim = optimizer.simulate_outcomes("JUDICIAL_DISQUALIFICATION", n_simulations=100)
        passed = (
            isinstance(sim, dict)
            and "success_probability" in sim
            and "confidence_interval_95" in sim
            and "histogram" in sim
            and len(sim["histogram"]) == 10
        )
        results["tests"]["simulate_outcomes"] = {
            "passed": passed,
            "success_probability": sim.get("success_probability"),
            "confidence_interval": sim.get("confidence_interval_95"),
            "n_simulations": sim.get("n_simulations"),
        }
    except Exception as e:
        results["tests"]["simulate_outcomes"] = {"passed": False, "error": str(e)}

    # Test 4: compare_filings
    try:
        comp = optimizer.compare_filings(["EMERGENCY_MOTION_RESTORE_PT", "JUDICIAL_DISQUALIFICATION"])
        passed = (
            isinstance(comp, dict)
            and "comparison" in comp
            and len(comp["comparison"]) == 2
            and "strongest_option" in comp
        )
        results["tests"]["compare_filings"] = {
            "passed": passed,
            "strongest": comp.get("strongest_option"),
        }
    except Exception as e:
        results["tests"]["compare_filings"] = {"passed": False, "error": str(e)}

    # Test 5: identify_weakest_link
    try:
        weak = optimizer.identify_weakest_link("COA_APPELLATE_BRIEF")
        passed = (
            isinstance(weak, dict)
            and "weakness" in weak
            and "cure_suggestion" in weak
            and "impact_if_fixed" in weak
        )
        results["tests"]["identify_weakest_link"] = {
            "passed": passed,
            "weakest": weak.get("weakness"),
            "category": weak.get("category"),
        }
    except Exception as e:
        results["tests"]["identify_weakest_link"] = {"passed": False, "error": str(e)}

    # Test 6: optimize_filing_order
    try:
        order = optimizer.optimize_filing_order(DEFAULT_FILINGS[:3])
        passed = isinstance(order, list) and len(order) == 3 and all("order" in o for o in order)
        results["tests"]["optimize_filing_order"] = {
            "passed": passed,
            "first_to_file": order[0]["filing_type"] if order else None,
        }
    except Exception as e:
        results["tests"]["optimize_filing_order"] = {"passed": False, "error": str(e)}

    results["status"] = (
        "ok" if all(t.get("passed") for t in results["tests"].values()) else "degraded"
    )
    optimizer.close()
    return results


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    optimizer = FilingOptimizer()

    if len(sys.argv) < 2:
        print("DELTA 6 — Predictive Filing Optimizer")
        print("Usage:")
        print("  filing_optimizer.py test")
        print("  filing_optimizer.py score <filing_type>")
        print("  filing_optimizer.py simulate <filing_type> [n]")
        print("  filing_optimizer.py compare <type1> <type2> ...")
        print("  filing_optimizer.py order <type1> <type2> ...")
        print("  filing_optimizer.py weakest <filing_type>")
        print("  filing_optimizer.py report [type1 type2 ...]")
        sys.exit(0)

    cmd = sys.argv[1].lower()

    try:
        if cmd == "test":
            print(json.dumps(self_test(), indent=2, default=str))

        elif cmd == "score" and len(sys.argv) >= 3:
            result = optimizer.score_filing(sys.argv[2])
            print(json.dumps(result, indent=2, default=str))

        elif cmd == "simulate" and len(sys.argv) >= 3:
            n = int(sys.argv[3]) if len(sys.argv) > 3 else 1000
            result = optimizer.simulate_outcomes(sys.argv[2], n)
            print(json.dumps(result, indent=2, default=str))

        elif cmd == "compare" and len(sys.argv) >= 4:
            result = optimizer.compare_filings(sys.argv[2:])
            print(json.dumps(result, indent=2, default=str))

        elif cmd == "order" and len(sys.argv) >= 4:
            result = optimizer.optimize_filing_order(sys.argv[2:])
            print(json.dumps(result, indent=2, default=str))

        elif cmd == "weakest" and len(sys.argv) >= 3:
            result = optimizer.identify_weakest_link(sys.argv[2])
            print(json.dumps(result, indent=2, default=str))

        elif cmd == "report":
            types = sys.argv[2:] if len(sys.argv) > 2 else None
            result = optimizer.generate_optimization_report(types)
            print(json.dumps(result, indent=2, default=str))

        else:
            print(f"Unknown command: {cmd}")
            sys.exit(1)
    finally:
        optimizer.close()
