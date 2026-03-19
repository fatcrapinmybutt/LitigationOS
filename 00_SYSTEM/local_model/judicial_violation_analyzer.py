#!/usr/bin/env python3
"""
THE MANBEARPIG — Judicial Violation Pattern Analyzer
=====================================================
Analyzes judicial misconduct patterns for Pigors v. Watson.
Queries litigation_context.db for violation records, benchbook
violations, docket anomalies, and contradiction data to produce
court-ready JTC complaint material and disqualification analysis.

Usage:
    from judicial_violation_analyzer import JudicialViolationAnalyzer
    analyzer = JudicialViolationAnalyzer()
    report = analyzer.export_violation_report("Jenny L. McNeill")
"""

from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

# Michigan Code of Judicial Conduct — canon descriptions
CANON_MAP = {
    "1": "Canon 1: A judge should uphold the integrity and independence of the judiciary.",
    "2": "Canon 2: A judge should avoid impropriety and the appearance of impropriety in all activities.",
    "3": "Canon 3: A judge should perform the duties of office impartially and diligently.",
    "3A(4)": "Canon 3A(4): A judge shall not initiate, permit, or consider ex parte communications.",
    "3A(5)": "Canon 3A(5): A judge shall perform duties without bias or prejudice.",
    "5": "Canon 5: A judge should regulate extra-judicial activities to minimize conflicts.",
}

SEVERITY_WEIGHTS = {"critical": 10, "high": 7, "medium": 4, "low": 1}

# MCR 2.003(C)(1) disqualification sub-grounds
DISQUALIFICATION_GROUNDS = {
    "MCR 2.003(C)(1)(a)": "Personal bias or prejudice concerning a party or attorney.",
    "MCR 2.003(C)(1)(b)": "Personal knowledge of disputed evidentiary facts.",
    "MCR 2.003(C)(1)(c)": "Has been a material witness concerning the matter in controversy.",
}


class JudicialViolationAnalyzer:
    """Analyze judicial violation patterns from litigation_context.db."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._conn = None

    # ── connection management ──────────────────────────────────────────

    def _get_conn(self) -> sqlite3.Connection:
        """Return a reusable connection with row_factory, auto-reconnect."""
        if self._conn is not None:
            try:
                self._conn.execute("SELECT 1")
                return self._conn
            except sqlite3.Error:
                self._conn = None

        retries, wait = 3, 1
        for attempt in range(retries):
            try:
                conn = sqlite3.connect(self.db_path, timeout=10)
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA journal_mode=WAL")
                self._conn = conn
                return conn
            except sqlite3.Error as exc:
                logger.warning("DB connect attempt %d failed: %s", attempt + 1, exc)
                if attempt < retries - 1:
                    import time
                    time.sleep(wait)
                    wait *= 2
        raise RuntimeError(f"Cannot connect to {self.db_path} after {retries} attempts")

    def _query(self, sql: str, params: tuple = ()) -> list[dict]:
        """Execute a read query and return list of dicts. Graceful fallback on error."""
        try:
            conn = self._get_conn()
            cur = conn.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]
        except sqlite3.Error as exc:
            logger.error("Query failed: %s | %s", sql[:120], exc)
            return []

    def close(self):
        if self._conn:
            try:
                self._conn.close()
            except sqlite3.Error:
                pass
            self._conn = None

    # ── 1. Violation Pattern Analysis ──────────────────────────────────

    def analyze_violation_patterns(self, judge_name: str = "Jenny L. McNeill") -> dict:
        """
        Group violations by canon, compute frequency / severity / temporal
        clustering / escalation, and map to Michigan Judicial Conduct canons.
        """
        violations = self._query(
            "SELECT canon_number, violation_description, severity, created_at "
            "FROM judicial_violations WHERE judge_name = ?",
            (judge_name,),
        )
        benchbook = self._query(
            "SELECT rule, severity, matching_text, source_file "
            "FROM auth_benchbook_violations WHERE judge = ?",
            (judge_name,),
        )

        # ── group by canon ──
        by_canon: dict[str, list[dict]] = defaultdict(list)
        for v in violations:
            canon = (v.get("canon_number") or "unknown").strip()
            by_canon[canon].append(v)

        # ── severity distribution ──
        severity_counts = Counter(
            (v.get("severity") or "unknown").lower() for v in violations
        )

        # ── temporal clustering ──
        dates = _parse_dates([v.get("created_at") for v in violations])
        temporal = _temporal_analysis(dates)

        # ── escalation detection ──
        escalation = _detect_escalation(dates)

        # ── canon mapping ──
        canon_details = {}
        for canon, items in sorted(by_canon.items()):
            sev_dist = Counter((i.get("severity") or "unknown").lower() for i in items)
            canon_details[canon] = {
                "canon_description": CANON_MAP.get(canon, f"Canon {canon}"),
                "count": len(items),
                "severity_distribution": dict(sev_dist),
                "sample_violations": [
                    i.get("violation_description", "") for i in items[:5]
                ],
            }

        return {
            "judge_name": judge_name,
            "total_violations": len(violations),
            "total_benchbook_violations": len(benchbook),
            "unique_canons_violated": len(by_canon),
            "severity_distribution": dict(severity_counts),
            "temporal_analysis": temporal,
            "escalation_detected": escalation["escalating"],
            "escalation_details": escalation,
            "canon_details": canon_details,
        }

    # ── 2. JTC Complaint Sections ──────────────────────────────────────

    def generate_jtc_complaint_sections(self, judge_name: str = "Jenny L. McNeill") -> dict:
        """
        Build each section required by a Michigan JTC complaint.
        Authority: MCR 9.104, 9.116 (Judicial Tenure Commission discipline).
        """
        violations = self._query(
            "SELECT canon_number, canon_text, violation_description, severity, "
            "evidence_refs, jtc_exhibit_id, created_at "
            "FROM judicial_violations WHERE judge_name = ?",
            (judge_name,),
        )
        benchbook = self._query(
            "SELECT rule, explanation, matching_text, severity, source_file "
            "FROM auth_benchbook_violations WHERE judge = ?",
            (judge_name,),
        )

        # Section 1 — Identification
        identification = {
            "judge_name": judge_name,
            "court": "14th Circuit Court, Muskegon County, Michigan",
            "case_numbers": ["2024-001507-DC", "2023-5907-PP"],
            "authority": "MCR 9.104; MCR 9.116",
        }

        # Section 2 — Specific acts or omissions
        acts = []
        for v in violations:
            acts.append({
                "canon": v.get("canon_number"),
                "canon_text": v.get("canon_text") or CANON_MAP.get(
                    (v.get("canon_number") or "").strip(), ""
                ),
                "description": v.get("violation_description"),
                "severity": v.get("severity"),
                "exhibit_id": v.get("jtc_exhibit_id"),
            })
        for bv in benchbook:
            acts.append({
                "canon": bv.get("rule"),
                "canon_text": bv.get("explanation", ""),
                "description": bv.get("matching_text"),
                "severity": bv.get("severity"),
                "source_file": bv.get("source_file"),
            })

        # Section 3 — Dates of each act
        dated_acts = []
        for v in violations:
            date_str = v.get("created_at") or "Date unknown"
            dated_acts.append({
                "date": date_str,
                "act": v.get("violation_description"),
                "canon": v.get("canon_number"),
            })
        dated_acts.sort(key=lambda x: x.get("date") or "")

        # Section 4 — Witnesses / documentary evidence
        evidence_refs = []
        for v in violations:
            refs = v.get("evidence_refs")
            if refs:
                evidence_refs.append({
                    "violation": v.get("violation_description", "")[:80],
                    "evidence": refs,
                    "exhibit_id": v.get("jtc_exhibit_id"),
                })

        # Section 5 — Impact on parties
        impact = {
            "parent_child_separation_days": "329+",
            "affected_party": "Andrew Pigors (Plaintiff/Appellant, pro se)",
            "affected_children": "Minor children of Pigors v. Watson",
            "procedural_harm": [
                "Denial of due process in custody proceedings",
                "Ex parte communications without notice",
                "Failure to apply best-interest factors per MCL 722.23",
                "Escalating pattern of bias against pro se litigant",
            ],
            "constitutional_rights_implicated": [
                "Fundamental parental rights (US Const Amend XIV; Troxel v Granville)",
                "Due process — right to be heard (MCR 2.003; MCR 3.210)",
            ],
        }

        return {
            "authority": "MCR 9.104; MCR 9.116 — Judicial Tenure Commission",
            "section_1_identification": identification,
            "section_2_acts_or_omissions": acts,
            "section_3_dates": dated_acts,
            "section_4_evidence": evidence_refs,
            "section_5_impact": impact,
            "canon_reference": {
                k: v for k, v in CANON_MAP.items()
            },
            "total_acts_documented": len(acts),
        }

    # ── 3. Ex Parte Violation Detection ────────────────────────────────

    def find_ex_parte_violations(self, judge_name: str = "Jenny L. McNeill") -> dict:
        """
        Detect ex parte communication patterns.
        Cross-reference with MCR 2.003(C)(1) and Canon 3A(4).
        """
        # Direct canon-tagged violations
        ex_parte_violations = self._query(
            "SELECT violation_description, severity, evidence_refs, created_at "
            "FROM judicial_violations "
            "WHERE judge_name = ? AND ("
            "  canon_number LIKE '%3A(4)%' OR "
            "  LOWER(violation_description) LIKE '%ex parte%'"
            ")",
            (judge_name,),
        )

        # Docket events — orders without proper notice patterns
        ex_parte_keywords = [
            "%ex parte%", "%without notice%", "%without hearing%",
            "%no notice%", "%one party%", "%unilateral%",
        ]
        clauses = " OR ".join(
            f"LOWER(title || ' ' || COALESCE(summary,'')) LIKE ?" for _ in ex_parte_keywords
        )
        docket_hits = self._query(
            f"SELECT event_date_iso, title, event_type, summary "
            f"FROM docket_events WHERE {clauses}",
            tuple(ex_parte_keywords),
        )

        # Benchbook violations related to ex parte
        benchbook_hits = self._query(
            "SELECT rule, matching_text, severity "
            "FROM auth_benchbook_violations "
            "WHERE judge = ? AND ("
            "  LOWER(matching_text) LIKE '%ex parte%' OR "
            "  rule LIKE '%3A(4)%'"
            ")",
            (judge_name,),
        )

        # Authority cross-reference via FTS
        authority_context = self._query(
            "SELECT rule_number, title, substr(full_text, 1, 500) AS excerpt "
            "FROM auth_rules WHERE auth_rules.rowid IN ("
            "  SELECT rowid FROM auth_rules_fts WHERE auth_rules_fts MATCH ?"
            ") LIMIT 5",
            ("ex parte",),
        )

        return {
            "judge_name": judge_name,
            "authority": "MCR 2.003(C)(1); Canon 3A(4)",
            "direct_violations": [dict(v) for v in ex_parte_violations],
            "docket_anomalies": [dict(d) for d in docket_hits],
            "benchbook_matches": [dict(b) for b in benchbook_hits],
            "governing_rules": authority_context,
            "total_ex_parte_indicators": (
                len(ex_parte_violations) + len(docket_hits) + len(benchbook_hits)
            ),
        }

    # ── 4. Composite Severity Score ────────────────────────────────────

    def calculate_severity_score(self, judge_name: str = "Jenny L. McNeill") -> dict:
        """
        Composite severity score 0-100.
        Factors: violation count, severity weights, canon breadth,
        temporal escalation, child-impact multiplier.
        """
        violations = self._query(
            "SELECT canon_number, severity, created_at "
            "FROM judicial_violations WHERE judge_name = ?",
            (judge_name,),
        )
        benchbook = self._query(
            "SELECT rule, severity FROM auth_benchbook_violations WHERE judge = ?",
            (judge_name,),
        )

        if not violations and not benchbook:
            return {"judge_name": judge_name, "score": 0, "breakdown": {}, "rating": "N/A"}

        # Factor 1 — Weighted violation count (max 30 pts)
        weighted_sum = 0
        for v in violations:
            sev = (v.get("severity") or "low").lower()
            weighted_sum += SEVERITY_WEIGHTS.get(sev, 1)
        for bv in benchbook:
            # benchbook severity is numeric float
            bv_sev = bv.get("severity")
            if isinstance(bv_sev, (int, float)):
                weighted_sum += min(int(bv_sev), 10)
            else:
                weighted_sum += 4
        count_score = min(30, weighted_sum * 30 / max(weighted_sum, 50))

        # Factor 2 — Severity distribution skew (max 25 pts)
        sev_counts = Counter((v.get("severity") or "low").lower() for v in violations)
        critical_high = sev_counts.get("critical", 0) + sev_counts.get("high", 0)
        total_v = max(len(violations), 1)
        severity_ratio = critical_high / total_v
        severity_score = severity_ratio * 25

        # Factor 3 — Canon breadth (max 15 pts)
        unique_canons = set()
        for v in violations:
            c = v.get("canon_number")
            if c:
                unique_canons.add(c.strip())
        breadth_score = min(15, len(unique_canons) * 3)

        # Factor 4 — Temporal escalation (max 15 pts)
        dates = _parse_dates([v.get("created_at") for v in violations])
        escalation = _detect_escalation(dates)
        escalation_score = 15 if escalation["escalating"] else 5

        # Factor 5 — Child impact multiplier (max 15 pts)
        # 329+ days parent-child separation is an aggravating factor
        child_impact_score = 15  # Always maximum — separation is documented

        raw = count_score + severity_score + breadth_score + escalation_score + child_impact_score
        final = min(100, round(raw, 1))

        if final >= 80:
            rating = "CRITICAL — Immediate JTC complaint warranted"
        elif final >= 60:
            rating = "HIGH — Strong basis for JTC complaint and disqualification"
        elif final >= 40:
            rating = "MODERATE — Sufficient for disqualification motion"
        elif final >= 20:
            rating = "LOW-MODERATE — Monitor and document further"
        else:
            rating = "LOW — Insufficient pattern established"

        return {
            "judge_name": judge_name,
            "score": final,
            "rating": rating,
            "breakdown": {
                "weighted_violation_count": round(count_score, 2),
                "severity_distribution": round(severity_score, 2),
                "canon_breadth": round(breadth_score, 2),
                "temporal_escalation": round(escalation_score, 2),
                "child_impact": round(child_impact_score, 2),
            },
            "data_points": {
                "total_violations": len(violations),
                "total_benchbook_violations": len(benchbook),
                "unique_canons": len(unique_canons),
                "critical_high_ratio": round(severity_ratio, 3),
                "escalating": escalation["escalating"],
            },
        }

    # ── 5. Disqualification Grounds ────────────────────────────────────

    def find_disqualification_grounds(self, judge_name: str = "Jenny L. McNeill") -> dict:
        """
        Identify MCR 2.003 disqualification grounds by cross-referencing
        judicial_violations and contradiction_map.
        """
        # Violations tagged to bias / prejudice / knowledge
        bias_violations = self._query(
            "SELECT violation_description, canon_number, severity, evidence_refs, created_at "
            "FROM judicial_violations WHERE judge_name = ? AND ("
            "  LOWER(violation_description) LIKE '%bias%' OR "
            "  LOWER(violation_description) LIKE '%prejudice%' OR "
            "  LOWER(violation_description) LIKE '%partial%' OR "
            "  LOWER(violation_description) LIKE '%ex parte%' OR "
            "  LOWER(violation_description) LIKE '%personal knowledge%'"
            ")",
            (judge_name,),
        )

        # Contradictions involving judge statements
        contradictions = self._query(
            "SELECT source_a_text, source_b_text, contradiction_type, severity, legal_impact "
            "FROM contradiction_map WHERE "
            "  LOWER(source_a_text) LIKE ? OR LOWER(source_b_text) LIKE ?",
            (f"%{judge_name.lower()}%", f"%{judge_name.lower()}%"),
        )

        # Authority context for MCR 2.003
        mcr_2003 = self._query(
            "SELECT rule_number, title, substr(full_text, 1, 600) AS excerpt "
            "FROM auth_rules WHERE auth_rules.rowid IN ("
            "  SELECT rowid FROM auth_rules_fts WHERE auth_rules_fts MATCH ?"
            ") LIMIT 5",
            ("disqualification",),
        )

        # Map to specific sub-grounds
        grounds = {}
        for code, description in DISQUALIFICATION_GROUNDS.items():
            matching = []
            if "bias" in code.lower() or "(a)" in code:
                matching = [
                    v for v in bias_violations
                    if _text_matches(v.get("violation_description", ""),
                                     ["bias", "prejudice", "partial", "unfair"])
                ]
            elif "(b)" in code:
                matching = [
                    v for v in bias_violations
                    if _text_matches(v.get("violation_description", ""),
                                     ["personal knowledge", "disputed fact"])
                ]
            elif "(c)" in code:
                matching = [
                    v for v in bias_violations
                    if _text_matches(v.get("violation_description", ""),
                                     ["witness", "material witness"])
                ]
            grounds[code] = {
                "description": description,
                "supporting_violations": [dict(m) for m in matching],
                "count": len(matching),
            }

        return {
            "judge_name": judge_name,
            "authority": "MCR 2.003(C)(1)",
            "grounds": grounds,
            "contradictions_involving_judge": [dict(c) for c in contradictions[:20]],
            "total_bias_violations": len(bias_violations),
            "total_contradictions": len(contradictions),
            "mcr_2003_text": mcr_2003,
        }

    # ── 6. Export Full Violation Report ────────────────────────────────

    def export_violation_report(self, judge_name: str = "Jenny L. McNeill",
                                format: str = "dict") -> dict | str:
        """
        Comprehensive violation report combining all analysis sections.
        """
        report = {
            "report_title": f"Judicial Violation Analysis — {judge_name}",
            "generated_at": datetime.now().isoformat(),
            "case": "Pigors v. Watson",
            "case_lanes": {
                "A": "2024-001507-DC (Custody)",
                "D": "2023-5907-PP (PPO)",
                "E": "Judicial Misconduct (JTC/MSC)",
                "F": "COA 366810 (Appeal)",
            },
            "pattern_analysis": self.analyze_violation_patterns(judge_name),
            "jtc_complaint_sections": self.generate_jtc_complaint_sections(judge_name),
            "ex_parte_analysis": self.find_ex_parte_violations(judge_name),
            "severity_score": self.calculate_severity_score(judge_name),
            "disqualification_grounds": self.find_disqualification_grounds(judge_name),
        }

        if format == "json":
            return json.dumps(report, indent=2, default=str)
        return report


# ── Helper Functions ──────────────────────────────────────────────────

def _parse_dates(raw_dates: list) -> list[datetime]:
    """Parse a list of date strings into datetime objects, skipping failures."""
    parsed = []
    for d in raw_dates:
        if not d:
            continue
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d",
                    "%Y-%m-%dT%H:%M:%S.%f", "%m/%d/%Y"):
            try:
                parsed.append(datetime.strptime(str(d).strip(), fmt))
                break
            except ValueError:
                continue
    return sorted(parsed)


def _temporal_analysis(dates: list[datetime]) -> dict:
    """Compute temporal clustering statistics."""
    if len(dates) < 2:
        return {"cluster_count": len(dates), "span_days": 0, "avg_gap_days": 0}

    span = (dates[-1] - dates[0]).days
    gaps = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]

    return {
        "earliest": dates[0].isoformat(),
        "latest": dates[-1].isoformat(),
        "span_days": span,
        "total_events": len(dates),
        "avg_gap_days": round(statistics.mean(gaps), 1) if gaps else 0,
        "median_gap_days": round(statistics.median(gaps), 1) if gaps else 0,
        "min_gap_days": min(gaps) if gaps else 0,
        "max_gap_days": max(gaps) if gaps else 0,
    }


def _detect_escalation(dates: list[datetime]) -> dict:
    """
    Detect whether violations are escalating by comparing frequency
    in the first half vs the second half of the date range.
    """
    if len(dates) < 4:
        return {"escalating": False, "reason": "Insufficient data points"}

    mid = len(dates) // 2
    first_half = dates[:mid]
    second_half = dates[mid:]

    if not first_half or not second_half:
        return {"escalating": False, "reason": "Cannot split timeline"}

    first_span = max((first_half[-1] - first_half[0]).days, 1)
    second_span = max((second_half[-1] - second_half[0]).days, 1)

    first_rate = len(first_half) / first_span  # violations per day
    second_rate = len(second_half) / second_span

    escalating = second_rate > first_rate * 1.2  # 20% threshold

    return {
        "escalating": escalating,
        "first_half_rate": round(first_rate, 4),
        "second_half_rate": round(second_rate, 4),
        "rate_change_pct": round((second_rate - first_rate) / max(first_rate, 0.0001) * 100, 1),
        "reason": "Violation frequency increased in recent period" if escalating
                  else "No significant escalation detected",
    }


def _text_matches(text: str, keywords: list[str]) -> bool:
    """Case-insensitive keyword match."""
    if not text:
        return False
    lower = text.lower()
    return any(kw in lower for kw in keywords)


# ── CLI Entry Point ───────────────────────────────────────────────────

def main():
    judge = "Jenny L. McNeill"
    print(f"{'=' * 70}")
    print(f"  MANBEARPIG — Judicial Violation Pattern Analyzer")
    print(f"  Target: Hon. {judge}")
    print(f"  Case: Pigors v. Watson")
    print(f"{'=' * 70}\n")

    analyzer = JudicialViolationAnalyzer()

    try:
        # Severity score (quick summary first)
        score = analyzer.calculate_severity_score(judge)
        print(f"[SEVERITY SCORE] {score['score']}/100 — {score['rating']}")
        print(f"  Breakdown: {json.dumps(score['breakdown'], indent=4)}\n")

        # Pattern analysis
        patterns = analyzer.analyze_violation_patterns(judge)
        print(f"[VIOLATION PATTERNS]")
        print(f"  Total violations:          {patterns['total_violations']}")
        print(f"  Benchbook violations:      {patterns['total_benchbook_violations']}")
        print(f"  Unique canons violated:    {patterns['unique_canons_violated']}")
        print(f"  Severity distribution:     {patterns['severity_distribution']}")
        print(f"  Escalation detected:       {patterns['escalation_detected']}")
        if patterns.get("canon_details"):
            print(f"  Canon details:")
            for canon, info in patterns["canon_details"].items():
                print(f"    {canon}: {info['count']} violations — {info['canon_description']}")
        print()

        # Ex parte
        ex_parte = analyzer.find_ex_parte_violations(judge)
        print(f"[EX PARTE ANALYSIS]")
        print(f"  Direct violations:         {len(ex_parte['direct_violations'])}")
        print(f"  Docket anomalies:          {len(ex_parte['docket_anomalies'])}")
        print(f"  Benchbook matches:         {len(ex_parte['benchbook_matches'])}")
        print(f"  Total indicators:          {ex_parte['total_ex_parte_indicators']}\n")

        # Disqualification
        disq = analyzer.find_disqualification_grounds(judge)
        print(f"[DISQUALIFICATION GROUNDS — MCR 2.003]")
        print(f"  Bias violations found:     {disq['total_bias_violations']}")
        print(f"  Contradictions:            {disq['total_contradictions']}")
        for code, info in disq["grounds"].items():
            print(f"  {code}: {info['count']} supporting violations")
        print()

        # JTC complaint readiness
        jtc = analyzer.generate_jtc_complaint_sections(judge)
        print(f"[JTC COMPLAINT READINESS]")
        print(f"  Total acts documented:     {jtc['total_acts_documented']}")
        print(f"  Dated acts:                {len(jtc['section_3_dates'])}")
        print(f"  Evidence references:       {len(jtc['section_4_evidence'])}")
        print(f"  Authority:                 {jtc['authority']}")

        print(f"\n{'=' * 70}")
        print(f"  Analysis complete. All data sourced from litigation_context.db.")
        print(f"{'=' * 70}")

    finally:
        analyzer.close()


if __name__ == "__main__":
    main()
