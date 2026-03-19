#!/usr/bin/env python3
"""
MBP LitigationOS -- Forensic Analyzer Skill
=============================================
Judicial conduct forensic analysis, benchbook violation tracking, and
pattern detection for Pigors v. Watson.

Case: Andrew Pigors v. Tiffany Watson
Judge: Hon. Jenny L. McNeill, 14th Circuit Court, Muskegon County
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from collections import Counter
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
    """Get read-only DB connection with WAL mode."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA query_only=ON")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        return None


class ForensicAnalyzer:
    """Judicial forensic analysis engine."""

    def __init__(self):
        self._cache: Dict = {}

    # ── Data Access ───────────────────────────────────────────────────

    def get_forensic_findings(
        self, category: Optional[str] = None, limit: int = 100
    ) -> List[Dict]:
        """Query forensic_findings (16,974 rows)."""
        conn = _get_db()
        if not conn:
            return []

        try:
            if category:
                rows = conn.execute(
                    "SELECT id, source, finding_type, severity, actor, "
                    "substr(description, 1, 500) as description, "
                    "substr(evidence_text, 1, 300) as evidence_text, "
                    "legal_hook, event_date "
                    "FROM forensic_findings "
                    "WHERE finding_type = ? OR severity = ? "
                    "ORDER BY event_date DESC LIMIT ?",
                    (category, category, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, source, finding_type, severity, actor, "
                    "substr(description, 1, 500) as description, "
                    "substr(evidence_text, 1, 300) as evidence_text, "
                    "legal_hook, event_date "
                    "FROM forensic_findings "
                    "ORDER BY event_date DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            result = [dict(r) for r in rows]
            conn.close()
            return result
        except Exception:
            conn.close()
            return []

    def get_judicial_forensics(
        self, judge: str = "McNeill", limit: int = 100
    ) -> List[Dict]:
        """Query forensic_judicial_analysis (3,003 rows)."""
        conn = _get_db()
        if not conn:
            return []

        try:
            rows = conn.execute(
                "SELECT finding_id, category, severity, "
                "substr(description, 1, 500) as description, "
                "evidence_citations, mcr_violations, date_iso, source_table "
                "FROM forensic_judicial_analysis "
                "WHERE description LIKE ? "
                "ORDER BY date_iso DESC LIMIT ?",
                (f"%{judge}%", limit),
            ).fetchall()
            # If judge filter yields few results, get all
            result = [dict(r) for r in rows]
            if len(result) < 5:
                rows = conn.execute(
                    "SELECT finding_id, category, severity, "
                    "substr(description, 1, 500) as description, "
                    "evidence_citations, mcr_violations, date_iso, source_table "
                    "FROM forensic_judicial_analysis "
                    "ORDER BY date_iso DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                result = [dict(r) for r in rows]
            conn.close()
            return result
        except Exception:
            conn.close()
            return []

    def get_benchbook_violations(self, judge: str = "McNeill") -> Dict:
        """
        Query benchbook_violation_findings (540 rows) and
        auth_benchbook_violations (504 rows).
        """
        conn = _get_db()
        if not conn:
            return {"violation_findings": [], "auth_violations": []}

        try:
            findings = [
                dict(r) for r in conn.execute(
                    "SELECT [index], rule, explanation, "
                    "substr(matching_text, 1, 400) as matching_text "
                    "FROM benchbook_violation_findings LIMIT 540"
                ).fetchall()
            ]

            auth_violations = [
                dict(r) for r in conn.execute(
                    "SELECT id, rule, explanation, "
                    "substr(matching_text, 1, 400) as matching_text, "
                    "judge, severity, source_file "
                    "FROM auth_benchbook_violations "
                    "WHERE judge LIKE ? OR judge IS NULL "
                    "ORDER BY severity DESC",
                    (f"%{judge}%",),
                ).fetchall()
            ]
            # If judge filter yields nothing, get all
            if len(auth_violations) < 5:
                auth_violations = [
                    dict(r) for r in conn.execute(
                        "SELECT id, rule, explanation, "
                        "substr(matching_text, 1, 400) as matching_text, "
                        "judge, severity, source_file "
                        "FROM auth_benchbook_violations "
                        "ORDER BY severity DESC LIMIT 504"
                    ).fetchall()
                ]

            conn.close()
            return {
                "violation_findings": findings,
                "violation_findings_count": len(findings),
                "auth_violations": auth_violations,
                "auth_violations_count": len(auth_violations),
            }
        except Exception:
            conn.close()
            return {"violation_findings": [], "auth_violations": []}

    # ── Analysis ──────────────────────────────────────────────────────

    def analyze_judicial_conduct(self, judge: str = "McNeill") -> Dict:
        """Comprehensive judicial conduct analysis combining all forensic tables."""
        judicial = self.get_judicial_forensics(judge)
        benchbook = self.get_benchbook_violations(judge)
        findings = self.get_forensic_findings(limit=200)

        # Category breakdown
        categories = Counter(r.get("category", "unknown") for r in judicial)
        severities = Counter(r.get("severity", "unknown") for r in judicial)

        # MCR violations referenced
        mcr_violations = []
        for r in judicial:
            mcr = r.get("mcr_violations", "")
            if mcr:
                mcr_violations.append(mcr)

        # Benchbook rule violations
        bb_rules = Counter(
            r.get("rule", "unknown")
            for r in benchbook.get("auth_violations", [])
        )

        # Judge-specific forensic findings
        judge_findings = [
            f for f in findings
            if judge.lower() in (f.get("actor", "") or "").lower()
            or judge.lower() in (f.get("description", "") or "").lower()
        ]

        return {
            "judge": judge,
            "judicial_forensics_count": len(judicial),
            "benchbook_violation_findings_count": benchbook.get("violation_findings_count", 0),
            "auth_benchbook_violations_count": benchbook.get("auth_violations_count", 0),
            "judge_specific_findings": len(judge_findings),
            "category_breakdown": dict(categories.most_common(20)),
            "severity_breakdown": dict(severities.most_common(10)),
            "mcr_violations_cited": mcr_violations[:20],
            "benchbook_rules_violated": dict(bb_rules.most_common(20)),
            "top_findings": judicial[:10],
            "top_benchbook_violations": benchbook.get("auth_violations", [])[:10],
        }

    def identify_patterns(self) -> Dict:
        """Pattern detection across forensic data (ex parte, bias, procedural)."""
        conn = _get_db()
        if not conn:
            return {"error": "DB connection failed"}

        patterns = {
            "ex_parte": [],
            "bias": [],
            "procedural_violations": [],
            "due_process": [],
            "other": [],
        }
        pattern_keywords = {
            "ex_parte": ["ex parte", "one-sided", "without notice", "unilateral"],
            "bias": ["bias", "prejudice", "partial", "favorit", "one-sided"],
            "procedural_violations": ["MCR", "procedur", "rule", "violat", "fail to"],
            "due_process": ["due process", "notice", "hearing", "opportunity", "right to"],
        }

        try:
            # Scan forensic_judicial_analysis for patterns
            rows = conn.execute(
                "SELECT finding_id, category, severity, "
                "substr(description, 1, 300) as description, mcr_violations "
                "FROM forensic_judicial_analysis LIMIT 500"
            ).fetchall()

            for r in rows:
                desc = (r["description"] or "").lower()
                cat = (r["category"] or "").lower()
                classified = False
                for pattern_name, keywords in pattern_keywords.items():
                    if any(kw in desc or kw in cat for kw in keywords):
                        patterns[pattern_name].append(dict(r))
                        classified = True
                        break
                if not classified:
                    patterns["other"].append(dict(r))

            conn.close()
        except Exception:
            pass

        summary = {k: len(v) for k, v in patterns.items()}
        return {
            "pattern_counts": summary,
            "total_patterns": sum(summary.values()),
            "patterns": {k: v[:20] for k, v in patterns.items()},
        }

    def generate_forensic_report(self, judge: str = "McNeill") -> Dict:
        """Formatted forensic report with findings, patterns, recommendations."""
        conduct = self.analyze_judicial_conduct(judge)
        patterns = self.identify_patterns()

        recommendations = []
        if patterns["pattern_counts"].get("ex_parte", 0) > 0:
            recommendations.append(
                "File Motion for Disqualification under MCR 2.003(C)(1)(b) "
                "citing documented ex parte contacts."
            )
        if patterns["pattern_counts"].get("bias", 0) > 0:
            recommendations.append(
                "File Complaint with Judicial Tenure Commission citing "
                "documented bias patterns."
            )
        if patterns["pattern_counts"].get("procedural_violations", 0) > 0:
            recommendations.append(
                "Preserve procedural violation record for appeal under "
                "MCR 7.204 — claim of appeal."
            )
        if patterns["pattern_counts"].get("due_process", 0) > 0:
            recommendations.append(
                "Assert Fourteenth Amendment due process violation — "
                "fundamental parental rights (Troxel v Granville)."
            )

        return {
            "report_title": f"Forensic Judicial Conduct Report — Hon. {judge}",
            "case": "Pigors v. Watson, No. 2024-001507-DC",
            "court": "14th Circuit Court, Muskegon County",
            "generated": datetime.now().isoformat(),
            "conduct_analysis": conduct,
            "pattern_analysis": patterns["pattern_counts"],
            "recommendations": recommendations,
            "authority": [
                "MCR 2.003 — Disqualification of Judge",
                "MCR 2.003(C)(1)(b) — Personal bias or prejudice",
                "Const 1963, art 6, § 1 — Judicial accountability",
                "Code of Judicial Conduct, Canons 1-7",
            ],
        }

    def get_statistics(self) -> Dict:
        """Summary counts by category, severity, pattern."""
        conn = _get_db()
        if not conn:
            return {"error": "DB connection failed"}

        stats: Dict = {}
        try:
            stats["forensic_findings_total"] = conn.execute(
                "SELECT COUNT(*) FROM forensic_findings"
            ).fetchone()[0]

            stats["judicial_analysis_total"] = conn.execute(
                "SELECT COUNT(*) FROM forensic_judicial_analysis"
            ).fetchone()[0]

            stats["benchbook_violation_findings"] = conn.execute(
                "SELECT COUNT(*) FROM benchbook_violation_findings"
            ).fetchone()[0]

            stats["auth_benchbook_violations"] = conn.execute(
                "SELECT COUNT(*) FROM auth_benchbook_violations"
            ).fetchone()[0]

            # Category distribution from judicial analysis
            rows = conn.execute(
                "SELECT category, COUNT(*) as cnt "
                "FROM forensic_judicial_analysis "
                "GROUP BY category ORDER BY cnt DESC LIMIT 20"
            ).fetchall()
            stats["judicial_categories"] = {r["category"]: r["cnt"] for r in rows}

            # Severity distribution from forensic findings
            rows = conn.execute(
                "SELECT severity, COUNT(*) as cnt "
                "FROM forensic_findings "
                "GROUP BY severity ORDER BY cnt DESC LIMIT 10"
            ).fetchall()
            stats["severity_distribution"] = {
                str(r["severity"]): r["cnt"] for r in rows
            }

            conn.close()
        except Exception as e:
            stats["error"] = str(e)

        return stats


def self_test() -> Dict:
    """Verify skill connectivity and data availability."""
    results = {"skill": "forensic_analyzer", "timestamp": datetime.now().isoformat()}
    conn = _get_db()
    if not conn:
        results["status"] = "FAIL"
        results["error"] = "DB connection failed"
        return results

    checks = {}
    for table in [
        "forensic_findings", "forensic_judicial_analysis",
        "benchbook_violation_findings", "auth_benchbook_violations",
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
    analyzer = ForensicAnalyzer()

    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        judge = sys.argv[2] if len(sys.argv) > 2 else "McNeill"
        if cmd == "findings":
            category = sys.argv[2] if len(sys.argv) > 2 else None
            cycle_json(analyzer.get_forensic_findings(category=category))
        elif cmd == "judicial":
            cycle_json(analyzer.get_judicial_forensics(judge=judge))
        elif cmd == "benchbook":
            cycle_json(analyzer.get_benchbook_violations(judge=judge))
        elif cmd == "conduct":
            cycle_json(analyzer.analyze_judicial_conduct(judge=judge))
        elif cmd == "patterns":
            cycle_json(analyzer.identify_patterns())
        elif cmd == "report":
            cycle_json(analyzer.generate_forensic_report(judge=judge))
        elif cmd == "stats":
            cycle_json(analyzer.get_statistics())
        elif cmd == "self_test":
            cycle_json(self_test())
        else:
            print(f"Unknown command: {cmd}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Forensic Analyzer Skill")
        print("Usage: python forensic_analyzer.py <command> [judge]")
        print("Commands: findings, judicial, benchbook, conduct, patterns, report, stats, self_test")
