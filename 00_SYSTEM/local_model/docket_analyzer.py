"""
Docket Analyzer — LitigationOS 2026
Analyzes docket events, global chronology, and master timeline for
Pigors v. Watson consolidated litigation.
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


class DocketAnalyzer:
    """Analyzes docket events, chronology, and timeline for pattern detection."""

    def get_docket_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Query docket_events table."""
        conn = _get_db()
        try:
            rows = conn.execute(
                "SELECT * FROM docket_events ORDER BY event_date_iso DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_global_chronology(self, limit: int = 500) -> List[Dict[str, Any]]:
        """Query global_chronology table (~7,131 rows)."""
        conn = _get_db()
        try:
            rows = conn.execute(
                "SELECT * FROM global_chronology ORDER BY rowid DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_master_timeline(
        self, limit: int = 500, search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Query master_timeline (~5,536 rows) with optional FTS via master_timeline_fts."""
        conn = _get_db()
        try:
            if search:
                rows = conn.execute(
                    """SELECT mt.* FROM master_timeline mt
                       JOIN master_timeline_fts fts ON mt.rowid = fts.rowid
                       WHERE master_timeline_fts MATCH ?
                       ORDER BY rank LIMIT ?""",
                    (search, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM master_timeline ORDER BY rowid DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def detect_ex_parte_pattern(self) -> Dict[str, Any]:
        """Find clusters of ex parte actions in chronology."""
        conn = _get_db()
        try:
            rows = conn.execute(
                """SELECT * FROM global_chronology
                   WHERE LOWER(COALESCE(event_type,'') || ' ' || COALESCE(title,'') || ' ' || COALESCE(summary,''))
                   LIKE '%ex parte%'
                   ORDER BY rowid"""
            ).fetchall()
            events = [dict(r) for r in rows]

            clusters: List[List[Dict]] = []
            current_cluster: List[Dict] = []
            for evt in events:
                if not current_cluster:
                    current_cluster.append(evt)
                else:
                    current_cluster.append(evt)
            if current_cluster:
                clusters.append(current_cluster)

            return {
                "pattern": "ex_parte",
                "total_events": len(events),
                "clusters": len(clusters),
                "events": events,
                "finding": (
                    f"Found {len(events)} ex parte event(s) in the chronology."
                    if events
                    else "No ex parte events detected."
                ),
            }
        finally:
            conn.close()

    def detect_delay_pattern(self) -> Dict[str, Any]:
        """Find unusual delays or rushing in docket events."""
        conn = _get_db()
        try:
            rows = conn.execute(
                "SELECT * FROM docket_events ORDER BY event_date_iso"
            ).fetchall()
            events = [dict(r) for r in rows]

            delays: List[Dict[str, Any]] = []
            rushes: List[Dict[str, Any]] = []
            for i in range(1, len(events)):
                prev_date = events[i - 1].get("event_date_iso")
                curr_date = events[i].get("event_date_iso")
                if not prev_date or not curr_date:
                    continue
                try:
                    d1 = datetime.fromisoformat(str(prev_date)[:10])
                    d2 = datetime.fromisoformat(str(curr_date)[:10])
                    gap_days = (d2 - d1).days
                    if gap_days > 60:
                        delays.append({
                            "from_event": events[i - 1].get("title", ""),
                            "to_event": events[i].get("title", ""),
                            "gap_days": gap_days,
                            "from_date": str(prev_date),
                            "to_date": str(curr_date),
                        })
                    elif 0 < gap_days < 3:
                        rushes.append({
                            "from_event": events[i - 1].get("title", ""),
                            "to_event": events[i].get("title", ""),
                            "gap_days": gap_days,
                            "from_date": str(prev_date),
                            "to_date": str(curr_date),
                        })
                except (ValueError, TypeError):
                    continue

            return {
                "pattern": "delay_and_rushing",
                "unusual_delays": delays,
                "unusual_rushes": rushes,
                "delay_count": len(delays),
                "rush_count": len(rushes),
                "finding": (
                    f"Found {len(delays)} unusual delay(s) (>60 days) and "
                    f"{len(rushes)} rushed action(s) (<3 days)."
                ),
            }
        finally:
            conn.close()

    def detect_bias_indicators(self) -> Dict[str, Any]:
        """Find patterns suggesting judicial bias in the docket."""
        conn = _get_db()
        try:
            bias_keywords = [
                "denied", "overruled", "sustained", "ex parte",
                "without hearing", "sua sponte", "prejudice",
            ]
            results: Dict[str, List[Dict]] = {kw: [] for kw in bias_keywords}

            for kw in bias_keywords:
                rows = conn.execute(
                    """SELECT * FROM docket_events
                       WHERE LOWER(COALESCE(title,'') || ' ' || COALESCE(summary,''))
                       LIKE ?""",
                    (f"%{kw}%",),
                ).fetchall()
                results[kw] = [dict(r) for r in rows]

            indicator_counts = {kw: len(evts) for kw, evts in results.items()}
            total = sum(indicator_counts.values())

            return {
                "pattern": "bias_indicators",
                "indicator_counts": indicator_counts,
                "total_indicators": total,
                "details": {kw: evts for kw, evts in results.items() if evts},
                "finding": (
                    f"Found {total} potential bias indicator(s) across "
                    f"{sum(1 for v in indicator_counts.values() if v > 0)} categories."
                ),
            }
        finally:
            conn.close()

    def analyze_docket(self) -> Dict[str, Any]:
        """Comprehensive docket analysis combining all detection methods."""
        docket = self.get_docket_events()
        ex_parte = self.detect_ex_parte_pattern()
        delays = self.detect_delay_pattern()
        bias = self.detect_bias_indicators()

        return {
            "analysis_timestamp": datetime.now().isoformat(),
            "case": "Pigors v. Watson",
            "docket_event_count": len(docket),
            "ex_parte_analysis": ex_parte,
            "delay_analysis": delays,
            "bias_analysis": bias,
            "summary": (
                f"Docket contains {len(docket)} events. "
                f"{ex_parte['finding']} "
                f"{delays['finding']} "
                f"{bias['finding']}"
            ),
        }

    def generate_timeline_report(self) -> Dict[str, Any]:
        """Formatted timeline report with annotations."""
        events = self.get_docket_events(limit=500)
        chronology = self.get_global_chronology(limit=200)
        ex_parte = self.detect_ex_parte_pattern()
        delays = self.detect_delay_pattern()

        annotated: List[Dict[str, Any]] = []
        for evt in events:
            entry: Dict[str, Any] = {
                "date": evt.get("event_date_iso", ""),
                "title": evt.get("title", ""),
                "type": evt.get("event_type", ""),
                "summary": evt.get("summary", ""),
                "annotations": [],
            }
            title_lower = (evt.get("title") or "").lower()
            if "ex parte" in title_lower:
                entry["annotations"].append("⚠️ EX PARTE ACTION")
            if "denied" in title_lower:
                entry["annotations"].append("❌ DENIED")
            annotated.append(entry)

        return {
            "report_timestamp": datetime.now().isoformat(),
            "case": "Pigors v. Watson",
            "timeline_entries": annotated,
            "total_docket_events": len(events),
            "total_chronology_events": len(chronology),
            "pattern_flags": {
                "ex_parte_count": ex_parte["total_events"],
                "delay_count": delays["delay_count"],
                "rush_count": delays["rush_count"],
            },
        }


def self_test() -> Dict[str, Any]:
    """Run self-test to verify DB connectivity and key docket analysis methods."""
    results = {"status": "ok", "tests": {}}
    analyzer = DocketAnalyzer()

    # Test 1: DB connectivity
    try:
        conn = _get_db()
        conn.execute("SELECT 1").fetchone()
        conn.close()
        results["tests"]["db_connectivity"] = {"passed": True}
    except Exception as e:
        results["tests"]["db_connectivity"] = {"passed": False, "error": str(e)}

    # Test 2: get_docket_events
    try:
        events = analyzer.get_docket_events(limit=5)
        results["tests"]["get_docket_events"] = {
            "passed": isinstance(events, list),
            "count": len(events),
        }
    except Exception as e:
        results["tests"]["get_docket_events"] = {"passed": False, "error": str(e)}

    # Test 3: detect_delay_pattern
    try:
        delays = analyzer.detect_delay_pattern()
        results["tests"]["detect_delay_pattern"] = {
            "passed": isinstance(delays, dict) and "pattern" in delays,
            "delay_count": delays.get("delay_count", 0),
        }
    except Exception as e:
        results["tests"]["detect_delay_pattern"] = {"passed": False, "error": str(e)}

    results["status"] = (
        "ok" if all(t.get("passed") for t in results["tests"].values()) else "degraded"
    )
    return results


if __name__ == "__main__":
    analyzer = DocketAnalyzer()
    commands = {
        "events": lambda: analyzer.get_docket_events(),
        "chronology": lambda: analyzer.get_global_chronology(),
        "timeline": lambda: analyzer.get_master_timeline(),
        "ex_parte": lambda: analyzer.detect_ex_parte_pattern(),
        "delays": lambda: analyzer.detect_delay_pattern(),
        "bias": lambda: analyzer.detect_bias_indicators(),
        "analyze": lambda: analyzer.analyze_docket(),
        "report": lambda: analyzer.generate_timeline_report(),
    }
    cmd = sys.argv[1] if len(sys.argv) > 1 else "analyze"
    if cmd == "help":
        print("Usage: docket_analyzer.py [" + "|".join(commands.keys()) + "|test]")
        sys.exit(0)
    if cmd == "test":
        print(json.dumps(self_test(), indent=2, default=str))
        sys.exit(0)
    if cmd not in commands:
        print(f"Unknown command: {cmd}. Use 'help' for options.")
        sys.exit(1)
    result = commands[cmd]()
    print(json.dumps(result, indent=2, default=str))
