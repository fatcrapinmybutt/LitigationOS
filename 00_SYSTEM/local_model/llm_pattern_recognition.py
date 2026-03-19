#!/usr/bin/env python3
"""
MBP LitigationOS — Judicial Pattern Recognition Engine
=======================================================
Analyzes judicial behavior patterns by querying judicial_violations,
auth_benchbook_violations, docket_events, contradiction_map, and
impeachment_items for Judge McNeill.

Outputs structured pattern reports with severity scores and Mermaid diagrams.

Case: Andrew Pigors v. Tiffany Watson
Judge: Hon. Jenny L. McNeill

Usage:
    # Python API
    from llm_pattern_recognition import PatternRecognition
    pr = PatternRecognition()
    report = pr.analyze_judicial_patterns()

    # CLI
    python llm_pattern_recognition.py analyze
    python llm_pattern_recognition.py report
    python llm_pattern_recognition.py mermaid

    # JSON-RPC pipe mode (for Electron integration)
    python llm_pattern_recognition.py --pipe
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── Cycle Method I/O ───────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    from cycle_method import cycle_json, cycle_print
except ImportError:
    cycle_json = lambda o, **k: print(json.dumps(o, default=str))
    cycle_print = print

# ── Constants ──────────────────────────────────────────────────────────
DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)

DEFAULT_JUDGE = "McNeill"

# Severity weights for composite scoring
SEVERITY_WEIGHTS = {
    "critical": 10,
    "high": 7,
    "medium": 4,
    "low": 2,
    "info": 1,
}

# Pattern categories for classification
PATTERN_CATEGORIES = {
    "hearing_denial": "Systematic denial of hearings or continuances",
    "ex_parte": "Indicators of ex parte communication",
    "bias_statistical": "Statistical imbalance in rulings favoring one party",
    "benchbook_deviation": "Deviations from Michigan Judicial Benchbook standards",
    "procedural_violation": "Violations of Michigan Court Rules",
    "due_process": "Due process violations (14th Amendment, Mathews v Eldridge)",
    "alienation_facilitation": "Failure to address parental alienation under MCL 722.23(j)",
}


class PatternRecognition:
    """
    Judicial pattern recognition engine.
    Queries litigation_context.db for judicial behavior patterns,
    benchbook violations, docket events, and contradictions.
    """

    def __init__(self, judge_name: str = DEFAULT_JUDGE):
        self.judge_name = judge_name
        self._db: Optional[sqlite3.Connection] = None
        self._error_log: List[Dict[str, Any]] = []

    # ── Database ───────────────────────────────────────────────────────

    def _get_db(self) -> Optional[sqlite3.Connection]:
        """Get DB connection with self-healing reconnect."""
        if self._db:
            try:
                self._db.execute("SELECT 1")
                return self._db
            except Exception:
                self._db = None

        for attempt in range(3):
            try:
                self._db = sqlite3.connect(DB_PATH, timeout=60)
                self._db.execute("PRAGMA journal_mode=WAL")
                self._db.execute("PRAGMA cache_size=-65536")
                self._db.execute("PRAGMA query_only=ON")
                self._db.execute("PRAGMA temp_store=MEMORY")
                self._db.row_factory = sqlite3.Row
                return self._db
            except Exception as e:
                self._log_error("db_connect", f"Attempt {attempt+1}: {e}")
                time.sleep(0.5 * (attempt + 1))
                self._db = None
        return None

    def _log_error(self, component: str, msg: str):
        entry = {"ts": time.time(), "component": component, "msg": str(msg)[:300]}
        self._error_log.append(entry)
        if len(self._error_log) > 500:
            self._error_log = self._error_log[-250:]

    # ── Data Queries ───────────────────────────────────────────────────

    def _get_benchbook_violations(self) -> List[Dict]:
        """Retrieve benchbook violations for this judge (includes untagged rows)."""
        conn = self._get_db()
        if not conn:
            return []
        try:
            rows = conn.execute(
                "SELECT id, rule, explanation, matching_text, judge, severity, source_file "
                "FROM auth_benchbook_violations "
                "WHERE judge LIKE ? OR judge IS NULL ORDER BY severity DESC",
                (f"%{self.judge_name}%",),
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            self._log_error("benchbook_violations", str(e))
            return []

    def _get_judicial_violations(self) -> List[Dict]:
        """Retrieve judicial violations (may be empty if not yet populated)."""
        conn = self._get_db()
        if not conn:
            return []
        try:
            rows = conn.execute(
                "SELECT * FROM judicial_violations WHERE judge_name LIKE ?",
                (f"%{self.judge_name}%",),
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            self._log_error("judicial_violations", str(e))
            return []

    def _get_docket_events(self) -> List[Dict]:
        """Retrieve docket events for timeline analysis."""
        conn = self._get_db()
        if not conn:
            return []
        try:
            rows = conn.execute(
                "SELECT event_id, case_id, event_date_iso, title, event_type, "
                "summary, truth_tag FROM docket_events ORDER BY event_date_iso",
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            self._log_error("docket_events", str(e))
            return []

    def _get_contradictions(self) -> List[Dict]:
        """Retrieve contradiction map entries."""
        conn = self._get_db()
        if not conn:
            return []
        try:
            rows = conn.execute(
                "SELECT id, source_a_text, source_b_text, contradiction_type, "
                "severity, legal_impact FROM contradiction_map "
                "ORDER BY severity DESC LIMIT 100",
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            self._log_error("contradictions", str(e))
            return []

    def _get_impeachment_items(self) -> List[Dict]:
        """Retrieve impeachment material."""
        conn = self._get_db()
        if not conn:
            return []
        try:
            rows = conn.execute(
                "SELECT id, item_type, speaker, statement, contradicting_text, "
                "legal_hook, severity FROM impeachment_items "
                "ORDER BY severity DESC LIMIT 50",
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            self._log_error("impeachment_items", str(e))
            return []

    # ── Pattern Analysis ───────────────────────────────────────────────

    def analyze_judicial_patterns(
        self, judge_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Comprehensive judicial pattern analysis.
        Returns structured report with categorized patterns and severity scores.
        """
        if judge_name:
            self.judge_name = judge_name

        try:
            violations = self._get_benchbook_violations()
            jv = self._get_judicial_violations()
            docket = self._get_docket_events()
            contradictions = self._get_contradictions()
            impeachment = self._get_impeachment_items()

            # Categorize violations by rule
            rule_counts: Counter = Counter()
            severity_counts: Counter = Counter()
            violation_categories: Dict[str, List] = defaultdict(list)

            for v in violations:
                rule = v.get("rule", "unknown")
                sev = (v.get("severity") or "medium").lower()
                rule_counts[rule] += 1
                severity_counts[sev] += 1
                violation_categories[rule].append({
                    "explanation": (v.get("explanation") or "")[:200],
                    "severity": sev,
                    "source": v.get("source_file", ""),
                })

            # Compute composite severity score (0-100)
            total_weighted = sum(
                SEVERITY_WEIGHTS.get(sev, 1) * count
                for sev, count in severity_counts.items()
            )
            max_possible = max(len(violations) * 10, 1)
            composite_score = min(round((total_weighted / max_possible) * 100), 100)

            # Docket timeline analysis
            timeline = self._analyze_timeline(docket)

            # Contradiction cross-reference
            judicial_contradictions = [
                c for c in contradictions
                if self.judge_name.lower() in (
                    (c.get("source_a_text") or "") + (c.get("source_b_text") or "")
                ).lower()
            ]

            return {
                "ok": True,
                "judge": self.judge_name,
                "analysis_timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "summary": {
                    "total_benchbook_violations": len(violations),
                    "total_judicial_violations": len(jv),
                    "total_docket_events": len(docket),
                    "total_contradictions": len(contradictions),
                    "judicial_contradictions": len(judicial_contradictions),
                    "total_impeachment_items": len(impeachment),
                    "composite_severity_score": composite_score,
                },
                "violation_breakdown": {
                    "by_rule": dict(rule_counts.most_common(20)),
                    "by_severity": dict(severity_counts),
                    "top_violations": [
                        {
                            "rule": rule,
                            "count": count,
                            "samples": violation_categories[rule][:3],
                        }
                        for rule, count in rule_counts.most_common(10)
                    ],
                },
                "timeline": timeline,
                "contradictions_involving_judge": judicial_contradictions[:10],
                "pattern_indicators": self._classify_patterns(
                    violations, docket, contradictions, impeachment,
                ),
                "errors": [e["msg"] for e in self._error_log[-5:]],
            }

        except Exception as e:
            self._log_error("analyze_judicial_patterns", str(e))
            return {"ok": False, "error": str(e)}

    def _analyze_timeline(self, docket: List[Dict]) -> Dict[str, Any]:
        """Analyze docket event timeline for patterns."""
        if not docket:
            return {"events": [], "gaps": [], "clusters": []}

        # Group events by type
        by_type: Dict[str, int] = Counter()
        dates = []
        for evt in docket:
            by_type[evt.get("event_type", "unknown")] += 1
            if evt.get("event_date_iso"):
                dates.append(evt["event_date_iso"])

        # Detect gaps (>30 day gaps between events)
        dates_sorted = sorted(set(dates))
        gaps = []
        for i in range(1, len(dates_sorted)):
            try:
                d1 = time.strptime(dates_sorted[i-1][:10], "%Y-%m-%d")
                d2 = time.strptime(dates_sorted[i][:10], "%Y-%m-%d")
                delta_days = (time.mktime(d2) - time.mktime(d1)) / 86400
                if delta_days > 30:
                    gaps.append({
                        "from": dates_sorted[i-1],
                        "to": dates_sorted[i],
                        "days": int(delta_days),
                    })
            except Exception:
                continue

        return {
            "event_count": len(docket),
            "date_range": {
                "first": dates_sorted[0] if dates_sorted else None,
                "last": dates_sorted[-1] if dates_sorted else None,
            },
            "by_type": dict(by_type),
            "gaps_over_30_days": gaps,
            "events": [
                {
                    "date": e.get("event_date_iso"),
                    "title": e.get("title"),
                    "type": e.get("event_type"),
                    "summary": (e.get("summary") or "")[:200],
                }
                for e in docket
            ],
        }

    def _classify_patterns(
        self,
        violations: List[Dict],
        docket: List[Dict],
        contradictions: List[Dict],
        impeachment: List[Dict],
    ) -> List[Dict]:
        """Classify detected patterns into categories with confidence scores."""
        patterns = []

        # Benchbook deviation pattern
        if violations:
            severity_dist = Counter(
                (v.get("severity") or "medium").lower() for v in violations
            )
            critical_high = severity_dist.get("critical", 0) + severity_dist.get("high", 0)
            confidence = min(critical_high / max(len(violations), 1) * 100, 100)
            patterns.append({
                "category": "benchbook_deviation",
                "description": PATTERN_CATEGORIES["benchbook_deviation"],
                "indicator_count": len(violations),
                "confidence": round(confidence, 1),
                "severity": "high" if critical_high > 5 else "medium",
                "evidence_summary": (
                    f"{len(violations)} benchbook violations detected, "
                    f"{critical_high} rated critical/high severity"
                ),
            })

        # Procedural violation pattern (from violation rules containing MCR)
        mcr_violations = [
            v for v in violations
            if "MCR" in (v.get("rule") or "").upper()
        ]
        if mcr_violations:
            patterns.append({
                "category": "procedural_violation",
                "description": PATTERN_CATEGORIES["procedural_violation"],
                "indicator_count": len(mcr_violations),
                "confidence": min(len(mcr_violations) * 10, 100),
                "severity": "high" if len(mcr_violations) > 10 else "medium",
                "evidence_summary": (
                    f"{len(mcr_violations)} MCR-related violations in benchbook analysis"
                ),
            })

        # Contradiction pattern
        if contradictions:
            high_sev = [
                c for c in contradictions
                if (c.get("severity") or "").lower() in ("critical", "high")
            ]
            patterns.append({
                "category": "bias_statistical",
                "description": PATTERN_CATEGORIES["bias_statistical"],
                "indicator_count": len(contradictions),
                "confidence": min(len(high_sev) * 5, 100),
                "severity": "high" if len(high_sev) > 10 else "medium",
                "evidence_summary": (
                    f"{len(contradictions)} contradictions found, "
                    f"{len(high_sev)} rated critical/high"
                ),
            })

        # Impeachment material pattern
        if impeachment:
            patterns.append({
                "category": "due_process",
                "description": PATTERN_CATEGORIES["due_process"],
                "indicator_count": len(impeachment),
                "confidence": min(len(impeachment) * 8, 100),
                "severity": "high" if len(impeachment) > 5 else "medium",
                "evidence_summary": (
                    f"{len(impeachment)} impeachment items available for cross-examination"
                ),
            })

        # Sort by confidence descending
        patterns.sort(key=lambda p: p["confidence"], reverse=True)
        return patterns

    # ── Public API Methods ─────────────────────────────────────────────

    def detect_bias_indicators(self) -> Dict[str, Any]:
        """
        Detect statistical bias indicators from benchbook violations
        and docket events.
        """
        try:
            violations = self._get_benchbook_violations()
            docket = self._get_docket_events()
            contradictions = self._get_contradictions()

            # Analyze violation severity distribution
            severity_dist = Counter(
                (v.get("severity") or "medium").lower() for v in violations
            )

            # Analyze rule distribution
            rule_dist = Counter(v.get("rule", "unknown") for v in violations)

            # Check for patterns indicating bias
            bias_indicators = []

            # High concentration of violations = potential bias
            if len(violations) > 50:
                bias_indicators.append({
                    "indicator": "High violation density",
                    "description": (
                        f"{len(violations)} benchbook violations detected — "
                        f"significantly above normal judicial conduct baseline"
                    ),
                    "severity": "high",
                    "authority": "Canon 2, Michigan Code of Judicial Conduct",
                })

            # Critical severity violations
            critical_count = severity_dist.get("critical", 0)
            if critical_count > 0:
                bias_indicators.append({
                    "indicator": "Critical-severity violations present",
                    "description": (
                        f"{critical_count} critical-severity benchbook violations"
                    ),
                    "severity": "critical",
                    "authority": "MCR 2.003(C)(1) — Disqualification for bias",
                })

            # Repeated violations of same rule
            for rule, count in rule_dist.most_common(5):
                if count > 10:
                    bias_indicators.append({
                        "indicator": f"Repeated violation of {rule}",
                        "description": (
                            f"Rule {rule} violated {count} times — "
                            f"pattern suggests systematic non-compliance"
                        ),
                        "severity": "high",
                        "authority": "MCR 2.003(C)(1)(b) — Personal bias or prejudice",
                    })

            # Contradiction density as bias proxy
            high_contradictions = [
                c for c in contradictions
                if (c.get("severity") or "").lower() in ("critical", "high")
            ]
            if len(high_contradictions) > 20:
                bias_indicators.append({
                    "indicator": "High contradiction density",
                    "description": (
                        f"{len(high_contradictions)} high-severity contradictions "
                        f"in judicial record — indicates inconsistent application of law"
                    ),
                    "severity": "high",
                    "authority": "US Const Amend XIV — Due Process",
                })

            return {
                "ok": True,
                "judge": self.judge_name,
                "bias_indicators": bias_indicators,
                "severity_distribution": dict(severity_dist),
                "rule_distribution": dict(rule_dist.most_common(15)),
                "total_violations": len(violations),
                "total_contradictions": len(contradictions),
                "high_contradictions": len(high_contradictions),
                "assessment": (
                    "SIGNIFICANT BIAS INDICATORS DETECTED"
                    if len(bias_indicators) >= 3
                    else "MODERATE BIAS INDICATORS"
                    if len(bias_indicators) >= 1
                    else "INSUFFICIENT DATA FOR BIAS DETERMINATION"
                ),
            }

        except Exception as e:
            self._log_error("detect_bias_indicators", str(e))
            return {"ok": False, "error": str(e)}

    def get_ruling_statistics(self) -> Dict[str, Any]:
        """
        Compute ruling statistics from docket events and violations.
        """
        try:
            docket = self._get_docket_events()
            violations = self._get_benchbook_violations()

            # Categorize docket events
            event_types = Counter(e.get("event_type", "unknown") for e in docket)

            # Analyze truth tags from docket
            truth_tags = Counter(
                e.get("truth_tag", "untagged") for e in docket
                if e.get("truth_tag")
            )

            # Violation severity breakdown
            violation_severity = Counter(
                (v.get("severity") or "medium").lower() for v in violations
            )

            # Source file distribution (which documents have most violations)
            source_dist = Counter(
                v.get("source_file", "unknown") for v in violations
            )

            return {
                "ok": True,
                "judge": self.judge_name,
                "docket_statistics": {
                    "total_events": len(docket),
                    "by_event_type": dict(event_types),
                    "truth_tags": dict(truth_tags),
                },
                "violation_statistics": {
                    "total_violations": len(violations),
                    "by_severity": dict(violation_severity),
                    "by_source": dict(source_dist.most_common(10)),
                    "unique_rules_violated": len(set(
                        v.get("rule", "") for v in violations
                    )),
                },
                "composite_metrics": {
                    "violations_per_event": (
                        round(len(violations) / max(len(docket), 1), 2)
                    ),
                    "critical_ratio": round(
                        violation_severity.get("critical", 0) /
                        max(len(violations), 1) * 100, 1
                    ),
                    "high_ratio": round(
                        violation_severity.get("high", 0) /
                        max(len(violations), 1) * 100, 1
                    ),
                },
            }

        except Exception as e:
            self._log_error("get_ruling_statistics", str(e))
            return {"ok": False, "error": str(e)}

    def generate_pattern_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive pattern report combining all analyses.
        Returns structured report with executive summary, findings, and recommendations.
        """
        try:
            patterns = self.analyze_judicial_patterns()
            if not patterns.get("ok"):
                return patterns

            bias = self.detect_bias_indicators()
            stats = self.get_ruling_statistics()

            # Executive summary
            summary = patterns.get("summary", {})
            total_issues = (
                summary.get("total_benchbook_violations", 0) +
                summary.get("total_judicial_violations", 0) +
                summary.get("judicial_contradictions", 0)
            )

            severity_score = summary.get("composite_severity_score", 0)
            if severity_score >= 70:
                risk_level = "CRITICAL"
            elif severity_score >= 40:
                risk_level = "HIGH"
            elif severity_score >= 20:
                risk_level = "MODERATE"
            else:
                risk_level = "LOW"

            # Build recommendations
            recommendations = []
            if severity_score >= 50:
                recommendations.append({
                    "action": "File Motion for Disqualification under MCR 2.003(C)(1)",
                    "priority": "HIGH",
                    "authority": "MCR 2.003(C)(1)(b) — personal bias or prejudice",
                })
            if summary.get("total_benchbook_violations", 0) > 100:
                recommendations.append({
                    "action": "File Judicial Tenure Commission Complaint",
                    "priority": "HIGH",
                    "authority": "MCR 9.104 — Grounds for discipline",
                })
            if summary.get("judicial_contradictions", 0) > 5:
                recommendations.append({
                    "action": "Document contradictions in appellate brief",
                    "priority": "MEDIUM",
                    "authority": "MCR 7.212(C)(7) — Argument section of brief",
                })
            recommendations.append({
                "action": "Preserve all pattern evidence for appeal record",
                "priority": "HIGH",
                "authority": "MCR 7.210(A) — Record on appeal",
            })

            report = {
                "ok": True,
                "report_type": "judicial_pattern_analysis",
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "judge": self.judge_name,
                "executive_summary": {
                    "risk_level": risk_level,
                    "composite_severity_score": severity_score,
                    "total_issues_found": total_issues,
                    "assessment": bias.get("assessment", "UNKNOWN"),
                    "key_finding": (
                        f"{summary.get('total_benchbook_violations', 0)} benchbook violations, "
                        f"{summary.get('judicial_contradictions', 0)} judicial contradictions, "
                        f"severity score {severity_score}/100"
                    ),
                },
                "detailed_findings": {
                    "patterns": patterns,
                    "bias_analysis": bias,
                    "statistics": stats,
                },
                "recommendations": recommendations,
                "mermaid_diagram": self._generate_mermaid(patterns, bias),
            }

            return report

        except Exception as e:
            self._log_error("generate_pattern_report", str(e))
            return {"ok": False, "error": str(e)}

    # ── Mermaid Diagram Generation ─────────────────────────────────────

    def _generate_mermaid(
        self, patterns: Dict, bias: Dict,
    ) -> str:
        """Generate Mermaid diagram of bias patterns."""
        try:
            lines = ["graph TD"]

            # Judge node
            lines.append(f'    JUDGE[("Judge {self.judge_name}")]')
            lines.append('    style JUDGE fill:#ff6b6b,stroke:#333,stroke-width:3px')

            # Summary metrics
            summary = patterns.get("summary", {})
            lines.append(
                f'    SCORE["Severity Score: '
                f'{summary.get("composite_severity_score", 0)}/100"]'
            )
            lines.append('    JUDGE --> SCORE')

            # Violation categories
            violation_data = patterns.get("violation_breakdown", {})
            top_violations = violation_data.get("top_violations", [])

            for i, tv in enumerate(top_violations[:6]):
                node_id = f"V{i}"
                rule = tv.get("rule", "unknown")[:30]
                count = tv.get("count", 0)
                lines.append(f'    {node_id}["{rule}\\n({count} violations)"]')
                lines.append(f'    JUDGE --> {node_id}')

                # Color by count severity
                if count > 50:
                    lines.append(f'    style {node_id} fill:#ff4444,stroke:#333')
                elif count > 20:
                    lines.append(f'    style {node_id} fill:#ff8844,stroke:#333')
                else:
                    lines.append(f'    style {node_id} fill:#ffbb44,stroke:#333')

            # Bias indicators
            indicators = bias.get("bias_indicators", [])
            for i, ind in enumerate(indicators[:4]):
                node_id = f"B{i}"
                label = ind.get("indicator", "")[:40]
                lines.append(f'    {node_id}{{"Bias: {label}"}}')
                lines.append(f'    JUDGE --> {node_id}')
                lines.append(f'    style {node_id} fill:#cc44ff,stroke:#333')

            # Pattern indicators
            pattern_indicators = patterns.get("pattern_indicators", [])
            for i, pi in enumerate(pattern_indicators[:4]):
                node_id = f"P{i}"
                cat = pi.get("category", "unknown")
                conf = pi.get("confidence", 0)
                lines.append(f'    {node_id}(("{cat}\\nConfidence: {conf}%"))')
                lines.append(f'    JUDGE --> {node_id}')
                if conf > 70:
                    lines.append(f'    style {node_id} fill:#ff4444,stroke:#333')
                elif conf > 40:
                    lines.append(f'    style {node_id} fill:#ff8844,stroke:#333')

            # Recommendations
            report_summary = patterns.get("summary", {})
            if report_summary.get("composite_severity_score", 0) >= 50:
                lines.append('    REC["⚠️ RECOMMEND: MCR 2.003 Disqualification"]')
                lines.append('    SCORE --> REC')
                lines.append('    style REC fill:#ff0000,color:#fff,stroke:#333,stroke-width:2px')

            return "\n".join(lines)

        except Exception as e:
            self._log_error("generate_mermaid", str(e))
            return f"graph TD\n    ERR[\"Mermaid generation error: {str(e)[:80]}\"]"

    # ── Status ─────────────────────────────────────────────────────────

    def status(self) -> Dict[str, Any]:
        """System health check."""
        db_ok = False
        table_counts = {}
        try:
            conn = self._get_db()
            if conn:
                conn.execute("SELECT 1")
                db_ok = True
                for table in [
                    "auth_benchbook_violations", "judicial_violations",
                    "docket_events", "contradiction_map", "impeachment_items",
                ]:
                    try:
                        row = conn.execute(f"SELECT count(*) FROM {table}").fetchone()
                        table_counts[table] = row[0] if row else 0
                    except Exception:
                        table_counts[table] = -1
        except Exception:
            pass

        return {
            "ok": True,
            "db_connected": db_ok,
            "db_path": DB_PATH,
            "judge": self.judge_name,
            "table_counts": table_counts,
            "pattern_categories": list(PATTERN_CATEGORIES.keys()),
            "error_count": len(self._error_log),
            "recent_errors": [e["msg"] for e in self._error_log[-3:]],
        }


# ── JSON-RPC Pipe Mode ────────────────────────────────────────────────

def _handle_rpc(pr: PatternRecognition, request: Dict) -> Dict:
    """Handle a single JSON-RPC request."""
    method = request.get("method", "")
    params = request.get("params", {})
    req_id = request.get("id", None)

    dispatch = {
        "analyze_judicial_patterns": lambda p: pr.analyze_judicial_patterns(
            judge_name=p.get("judge_name"),
        ),
        "detect_bias_indicators": lambda p: pr.detect_bias_indicators(),
        "generate_pattern_report": lambda p: pr.generate_pattern_report(),
        "get_ruling_statistics": lambda p: pr.get_ruling_statistics(),
        "status": lambda p: pr.status(),
    }

    handler = dispatch.get(method)
    if not handler:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Unknown method: {method}"},
        }

    try:
        result = handler(params)
        return {"jsonrpc": "2.0", "id": req_id, "result": result}
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32000, "message": str(e)[:500]},
        }


def _run_pipe(pr: PatternRecognition):
    """Run JSON-RPC pipe mode — reads JSON from stdin, writes to stdout."""
    cycle_print("[PatternRec] JSON-RPC pipe mode ready. Send JSON requests on stdin.")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = _handle_rpc(pr, request)
            cycle_json(response)
        except json.JSONDecodeError as e:
            cycle_json({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {e}"},
            })
        except Exception as e:
            cycle_json({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32000, "message": str(e)[:500]},
            })


# ── CLI ────────────────────────────────────────────────────────────────

def _cli():
    """Command-line interface."""
    import argparse

    parser = argparse.ArgumentParser(
        description="MBP LitigationOS — Judicial Pattern Recognition"
    )
    parser.add_argument("--pipe", action="store_true",
                        help="JSON-RPC pipe mode for Electron integration")
    parser.add_argument("command", nargs="?", default="status",
                        choices=["analyze", "bias", "stats", "report",
                                 "mermaid", "status", "selftest"],
                        help="Analysis command")
    parser.add_argument("--judge", default=DEFAULT_JUDGE,
                        help="Judge name to analyze")

    args = parser.parse_args()
    pr = PatternRecognition(judge_name=args.judge)

    if args.pipe:
        _run_pipe(pr)
        return

    if args.command == "status":
        cycle_json(pr.status(), pretty=True)
    elif args.command == "analyze":
        cycle_json(pr.analyze_judicial_patterns(), pretty=True)
    elif args.command == "bias":
        cycle_json(pr.detect_bias_indicators(), pretty=True)
    elif args.command == "stats":
        cycle_json(pr.get_ruling_statistics(), pretty=True)
    elif args.command == "report":
        cycle_json(pr.generate_pattern_report(), pretty=True)
    elif args.command == "mermaid":
        report = pr.generate_pattern_report()
        if report.get("ok"):
            cycle_print(report.get("mermaid_diagram", ""))
        else:
            cycle_json(report, pretty=True)
    elif args.command == "selftest":
        _selftest(pr)


def _selftest(pr: PatternRecognition):
    """Self-test: exercise all analysis functions."""
    cycle_print("[PatternRec] Self-test starting...")
    tests_passed = 0
    tests_failed = 0

    # Test 1: Status
    try:
        result = pr.status()
        assert result["ok"], "Status check failed"
        cycle_print(f"  [PASS] status — db_connected={result['db_connected']}, "
                    f"tables={result['table_counts']}")
        tests_passed += 1
    except Exception as e:
        cycle_print(f"  [FAIL] status — {e}")
        tests_failed += 1

    # Test 2: Analyze judicial patterns
    try:
        result = pr.analyze_judicial_patterns()
        assert result["ok"], f"analyze failed: {result.get('error')}"
        s = result["summary"]
        cycle_print(f"  [PASS] analyze_judicial_patterns — "
                    f"violations={s['total_benchbook_violations']}, "
                    f"score={s['composite_severity_score']}")
        tests_passed += 1
    except Exception as e:
        cycle_print(f"  [FAIL] analyze_judicial_patterns — {e}")
        tests_failed += 1

    # Test 3: Detect bias indicators
    try:
        result = pr.detect_bias_indicators()
        assert result["ok"], f"bias failed: {result.get('error')}"
        cycle_print(f"  [PASS] detect_bias_indicators — "
                    f"indicators={len(result.get('bias_indicators', []))}, "
                    f"assessment={result.get('assessment')}")
        tests_passed += 1
    except Exception as e:
        cycle_print(f"  [FAIL] detect_bias_indicators — {e}")
        tests_failed += 1

    # Test 4: Get ruling statistics
    try:
        result = pr.get_ruling_statistics()
        assert result["ok"], f"stats failed: {result.get('error')}"
        cycle_print(f"  [PASS] get_ruling_statistics — "
                    f"events={result['docket_statistics']['total_events']}, "
                    f"violations={result['violation_statistics']['total_violations']}")
        tests_passed += 1
    except Exception as e:
        cycle_print(f"  [FAIL] get_ruling_statistics — {e}")
        tests_failed += 1

    # Test 5: Generate pattern report
    try:
        result = pr.generate_pattern_report()
        assert result["ok"], f"report failed: {result.get('error')}"
        es = result["executive_summary"]
        cycle_print(f"  [PASS] generate_pattern_report — "
                    f"risk={es['risk_level']}, score={es['composite_severity_score']}, "
                    f"recommendations={len(result.get('recommendations', []))}")
        tests_passed += 1
    except Exception as e:
        cycle_print(f"  [FAIL] generate_pattern_report — {e}")
        tests_failed += 1

    # Test 6: Mermaid diagram
    try:
        report = pr.generate_pattern_report()
        assert report["ok"]
        mermaid = report.get("mermaid_diagram", "")
        assert "graph TD" in mermaid, "Mermaid diagram missing graph declaration"
        assert "JUDGE" in mermaid, "Mermaid diagram missing JUDGE node"
        cycle_print(f"  [PASS] mermaid_diagram — {len(mermaid)} chars")
        tests_passed += 1
    except Exception as e:
        cycle_print(f"  [FAIL] mermaid_diagram — {e}")
        tests_failed += 1

    # Test 7: JSON output format
    try:
        result = pr.analyze_judicial_patterns()
        json_str = json.dumps(result, default=str)
        parsed = json.loads(json_str)
        assert parsed["ok"], "JSON roundtrip failed"
        cycle_print(f"  [PASS] json_serialization — {len(json_str)} bytes")
        tests_passed += 1
    except Exception as e:
        cycle_print(f"  [FAIL] json_serialization — {e}")
        tests_failed += 1

    cycle_print(f"\n[PatternRec] Self-test complete: {tests_passed} passed, {tests_failed} failed")


# ── Entry Point ────────────────────────────────────────────────────────

if __name__ == "__main__":
    _cli()
