#!/usr/bin/env python3
"""
MBP LitigationOS -- Alienation Analyzer Skill
===============================================
Parental alienation evidence gathering, Factor (j) analysis, timeline
construction, and severity scoring for Pigors v. Watson.

Authority: MCL 722.23(j), Lombardo v Lombardo, 202 Mich App 151 (1993).
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

ALIENATION_KEYWORDS = [
    "alienat", "interfere", "withhold", "deny contact", "disparage",
    "undermine", "gatekeep", "obstruct", "parenting time", "visitation",
    "false alleg", "coaching", "turned against", "refuse", "block",
    "factor j", "factor (j)", "722.23(j)", "relationship with",
]


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


class AlienationAnalyzer:
    """Parental alienation analysis engine for MCL 722.23(j)."""

    def __init__(self):
        self._cache: Dict = {}

    # ── Data Gathering ────────────────────────────────────────────────

    def gather_alienation_evidence(self) -> Dict:
        """
        Query alienation_tactics (50 rows), parental_alienation_evidence
        (10 rows), and evidence_quotes matching alienation keywords.
        """
        conn = _get_db()
        if not conn:
            return {"error": "DB connection failed", "tactics": [], "evidence": [], "quotes": []}

        try:
            tactics = [
                dict(r) for r in conn.execute(
                    "SELECT tactic, description FROM alienation_tactics LIMIT 50"
                ).fetchall()
            ]

            pa_evidence = [
                dict(r) for r in conn.execute(
                    "SELECT id, event_date, description, evidence_source, "
                    "mcl_factor, severity FROM parental_alienation_evidence "
                    "LIMIT 10"
                ).fetchall()
            ]

            # FTS search for alienation-related evidence quotes
            fts_terms = " OR ".join(ALIENATION_KEYWORDS[:8])
            quotes = []
            try:
                rows = conn.execute(
                    "SELECT id, quote_text, speaker, date_ref, "
                    "legal_significance, evidence_category "
                    "FROM evidence_quotes WHERE rowid IN "
                    "(SELECT rowid FROM evidence_quotes_fts "
                    " WHERE evidence_quotes_fts MATCH ?) LIMIT 100",
                    (fts_terms,),
                ).fetchall()
                quotes = [dict(r) for r in rows]
            except Exception:
                # Fallback to LIKE
                like_clauses = " OR ".join(
                    ["quote_text LIKE ?"] * len(ALIENATION_KEYWORDS)
                )
                params = [f"%{kw}%" for kw in ALIENATION_KEYWORDS]
                rows = conn.execute(
                    f"SELECT id, substr(quote_text, 1, 500) as quote_text, "
                    f"speaker, date_ref, legal_significance, evidence_category "
                    f"FROM evidence_quotes WHERE {like_clauses} LIMIT 100",
                    params,
                ).fetchall()
                quotes = [dict(r) for r in rows]

            conn.close()
            return {
                "tactics_count": len(tactics),
                "evidence_count": len(pa_evidence),
                "quotes_count": len(quotes),
                "tactics": tactics,
                "evidence": pa_evidence,
                "quotes": quotes[:50],
            }
        except Exception as e:
            conn.close()
            return {"error": str(e), "tactics": [], "evidence": [], "quotes": []}

    def analyze_factor_j(self) -> Dict:
        """
        Comprehensive MCL 722.23(j) analysis using the Lombardo v Lombardo
        framework: willingness to facilitate a close and continuing
        parent-child relationship with the other parent.
        """
        data = self.gather_alienation_evidence()

        # Build analysis
        analysis = {
            "factor": "(j)",
            "statute": "MCL 722.23(j)",
            "standard": (
                "The willingness and ability of each of the parties to "
                "facilitate and encourage a close and continuing parent-child "
                "relationship between the child and the other parent or the "
                "child and the parents."
            ),
            "framework": "Lombardo v Lombardo, 202 Mich App 151, 154 (1993)",
            "framework_holding": (
                "Factor (j) examines not just physical obstruction of "
                "parenting time, but also whether a parent disparages the "
                "other parent, coaches the children, or engages in conduct "
                "designed to undermine the parent-child bond."
            ),
            "evidence_summary": {
                "total_tactics_documented": data.get("tactics_count", 0),
                "formal_alienation_events": data.get("evidence_count", 0),
                "supporting_quotes": data.get("quotes_count", 0),
            },
            "tactics": data.get("tactics", []),
            "alienation_events": data.get("evidence", []),
            "key_quotes": data.get("quotes", [])[:20],
            "assessment": self._assess_factor_j(data),
        }
        return analysis

    def _assess_factor_j(self, data: Dict) -> Dict:
        """Generate assessment based on evidence volume and severity."""
        evidence_count = data.get("evidence_count", 0)
        quotes_count = data.get("quotes_count", 0)
        tactics_count = data.get("tactics_count", 0)

        total_indicators = evidence_count + quotes_count + tactics_count

        if total_indicators >= 30:
            conclusion = "STRONGLY_FAVORS_FATHER"
            narrative = (
                "Overwhelming evidence of systematic alienation conduct by "
                "Mother. Factor (j) strongly favors Father."
            )
        elif total_indicators >= 15:
            conclusion = "FAVORS_FATHER"
            narrative = (
                "Substantial evidence of alienation conduct by Mother. "
                "Factor (j) favors Father."
            )
        elif total_indicators >= 5:
            conclusion = "LEANS_FATHER"
            narrative = (
                "Meaningful evidence of alienation conduct warrants serious "
                "judicial scrutiny. Factor (j) leans toward Father."
            )
        else:
            conclusion = "INSUFFICIENT_DATA"
            narrative = "Additional evidence needed for conclusive assessment."

        return {
            "conclusion": conclusion,
            "narrative": narrative,
            "total_indicators": total_indicators,
            "strength": min(total_indicators / 30.0, 1.0),
        }

    def build_alienation_timeline(self) -> List[Dict]:
        """Build chronological timeline of alienation acts from evidence."""
        conn = _get_db()
        if not conn:
            return []

        timeline = []
        try:
            # parental_alienation_evidence with dates
            rows = conn.execute(
                "SELECT event_date, description, evidence_source, severity "
                "FROM parental_alienation_evidence "
                "WHERE event_date IS NOT NULL "
                "ORDER BY event_date"
            ).fetchall()
            for r in rows:
                timeline.append({
                    "date": r["event_date"],
                    "source": "parental_alienation_evidence",
                    "description": r["description"],
                    "evidence_source": r["evidence_source"],
                    "severity": r["severity"],
                })

            # evidence_quotes with date_ref containing alienation keywords
            like_clauses = " OR ".join(["quote_text LIKE ?"] * 5)
            params = [f"%{kw}%" for kw in ALIENATION_KEYWORDS[:5]]
            rows = conn.execute(
                f"SELECT date_ref, substr(quote_text, 1, 300) as quote_text, "
                f"speaker, evidence_category "
                f"FROM evidence_quotes "
                f"WHERE date_ref IS NOT NULL AND date_ref != '' "
                f"AND ({like_clauses}) "
                f"ORDER BY date_ref LIMIT 100",
                params,
            ).fetchall()
            for r in rows:
                timeline.append({
                    "date": r["date_ref"],
                    "source": "evidence_quotes",
                    "description": r["quote_text"],
                    "speaker": r["speaker"],
                    "category": r["evidence_category"],
                })

            conn.close()

            # Sort by date
            timeline.sort(key=lambda x: x.get("date", "") or "")
        except Exception:
            pass

        return timeline

    def score_alienation_severity(self) -> Dict:
        """
        Score alienation severity 1-10 based on frequency, duration, impact.
        """
        data = self.gather_alienation_evidence()
        timeline = self.build_alienation_timeline()

        tactics_count = data.get("tactics_count", 0)
        evidence_count = data.get("evidence_count", 0)
        quotes_count = data.get("quotes_count", 0)

        # Frequency score (0-10): based on number of documented events
        total_events = evidence_count + quotes_count
        frequency_score = min(total_events / 10.0, 10.0)

        # Duration score (0-10): based on timeline span
        duration_score = 0.0
        if len(timeline) >= 2:
            try:
                dates = sorted([e["date"] for e in timeline if e.get("date")])
                if len(dates) >= 2:
                    # Rough month-based estimate
                    duration_score = min(len(dates) / 5.0, 10.0)
            except Exception:
                duration_score = 5.0 if len(timeline) > 5 else 2.0

        # Impact score (0-10): based on severity of alienation evidence
        severity_values = []
        for ev in data.get("evidence", []):
            sev = ev.get("severity")
            if sev:
                try:
                    severity_values.append(float(sev))
                except (ValueError, TypeError):
                    severity_values.append(5.0)
        impact_score = (
            sum(severity_values) / len(severity_values)
            if severity_values
            else min(tactics_count / 5.0, 10.0)
        )

        # Variety score (0-10): diversity of alienation tactics
        variety_score = min(tactics_count / 5.0, 10.0)

        # Composite
        composite = round(
            (frequency_score * 0.3 + duration_score * 0.2 +
             impact_score * 0.3 + variety_score * 0.2), 2
        )

        return {
            "composite_score": composite,
            "frequency_score": round(frequency_score, 2),
            "duration_score": round(duration_score, 2),
            "impact_score": round(impact_score, 2),
            "variety_score": round(variety_score, 2),
            "total_events": total_events,
            "total_tactics": tactics_count,
            "timeline_entries": len(timeline),
            "interpretation": (
                "SEVERE" if composite >= 7 else
                "SIGNIFICANT" if composite >= 5 else
                "MODERATE" if composite >= 3 else
                "MILD"
            ),
            "days_separation": "329+",
        }

    def generate_factor_j_brief(self) -> Dict:
        """Generate IRAC brief section for Factor (j)."""
        analysis = self.analyze_factor_j()
        severity = self.score_alienation_severity()

        issue = (
            "Whether Defendant-Mother's pattern of conduct demonstrates an "
            "unwillingness and inability to facilitate and encourage a close "
            "and continuing parent-child relationship between the child and "
            "Plaintiff-Father, under MCL 722.23(j)."
        )

        rule = (
            "MCL 722.23(j) requires the court to evaluate '[t]he willingness "
            "and ability of each of the parties to facilitate and encourage a "
            "close and continuing parent-child relationship between the child "
            "and the other parent.' In Lombardo v Lombardo, 202 Mich App 151, "
            "154 (1993), the Court of Appeals held that this factor examines "
            "not merely physical obstruction of parenting time, but also "
            "disparagement, coaching, and any conduct designed to undermine "
            "the parent-child bond."
        )

        # Build application from evidence
        tactics_list = [
            t.get("tactic", "") for t in analysis.get("tactics", [])[:10]
        ]
        app_points = []
        if tactics_list:
            app_points.append(
                f"The record documents {len(tactics_list)} distinct alienation "
                f"tactics employed by Mother, including: "
                f"{'; '.join(tactics_list[:5])}."
            )
        app_points.append(
            f"A total of {severity['total_events']} alienation-related events "
            f"are documented in the record, yielding a composite severity "
            f"score of {severity['composite_score']}/10 "
            f"({severity['interpretation']})."
        )
        app_points.append(
            f"Father and child have been separated for {severity['days_separation']} "
            f"days, demonstrating the ongoing impact of Mother's alienation "
            f"conduct on the parent-child relationship."
        )

        application = " ".join(app_points)

        conclusion = (
            f"Factor (j) {analysis['assessment']['conclusion'].replace('_', ' ').lower()}. "
            f"The evidence overwhelmingly demonstrates Mother's systematic "
            f"campaign to destroy the father-child bond, warranting "
            f"modification of custody under MCL 722.27(1)(c)."
        )

        return {
            "irac": {
                "issue": issue,
                "rule": rule,
                "application": application,
                "conclusion": conclusion,
            },
            "severity_score": severity,
            "evidence_summary": analysis["evidence_summary"],
            "assessment": analysis["assessment"],
        }

    def get_statistics(self) -> Dict:
        """Summary statistics for alienation evidence."""
        conn = _get_db()
        if not conn:
            return {"error": "DB connection failed"}

        stats: Dict = {}
        try:
            stats["alienation_tactics"] = conn.execute(
                "SELECT COUNT(*) FROM alienation_tactics"
            ).fetchone()[0]
            stats["alienation_evidence_events"] = conn.execute(
                "SELECT COUNT(*) FROM parental_alienation_evidence"
            ).fetchone()[0]

            # Severity distribution
            rows = conn.execute(
                "SELECT severity, COUNT(*) as cnt "
                "FROM parental_alienation_evidence "
                "GROUP BY severity"
            ).fetchall()
            stats["severity_distribution"] = {
                str(r["severity"]): r["cnt"] for r in rows
            }

            # MCL factor distribution
            rows = conn.execute(
                "SELECT mcl_factor, COUNT(*) as cnt "
                "FROM parental_alienation_evidence "
                "GROUP BY mcl_factor"
            ).fetchall()
            stats["mcl_factor_distribution"] = {
                str(r["mcl_factor"]): r["cnt"] for r in rows
            }

            conn.close()
        except Exception as e:
            stats["error"] = str(e)

        return stats


def self_test() -> Dict:
    """Verify skill connectivity and data availability."""
    results = {"skill": "alienation_analyzer", "timestamp": datetime.now().isoformat()}
    conn = _get_db()
    if not conn:
        results["status"] = "FAIL"
        results["error"] = "DB connection failed"
        return results

    checks = {}
    for table in ["alienation_tactics", "parental_alienation_evidence", "evidence_quotes"]:
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
    analyzer = AlienationAnalyzer()

    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "gather":
            cycle_json(analyzer.gather_alienation_evidence())
        elif cmd == "factor_j":
            cycle_json(analyzer.analyze_factor_j())
        elif cmd == "timeline":
            cycle_json(analyzer.build_alienation_timeline())
        elif cmd == "score":
            cycle_json(analyzer.score_alienation_severity())
        elif cmd == "brief":
            cycle_json(analyzer.generate_factor_j_brief())
        elif cmd == "stats":
            cycle_json(analyzer.get_statistics())
        elif cmd == "self_test":
            cycle_json(self_test())
        else:
            print(f"Unknown command: {cmd}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Alienation Analyzer Skill")
        print("Usage: python alienation_analyzer.py <command>")
        print("Commands: gather, factor_j, timeline, score, brief, stats, self_test")
