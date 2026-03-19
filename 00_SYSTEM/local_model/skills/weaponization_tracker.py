#!/usr/bin/env python3
"""
MBP LitigationOS -- Weaponization Tracker Skill
=================================================
Track and analyze weaponization of court processes, PPOs, contempt,
and procedural mechanisms against Plaintiff in Pigors v. Watson.

Case: Andrew Pigors v. Tiffany Watson
Court: 14th Circuit Court, Muskegon County
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

WEAPONIZATION_CATEGORIES = {
    "ppo": ["ppo", "protection order", "personal protection", "2950", "restraining"],
    "contempt": ["contempt", "sanction", "punish", "jail", "incarcerat"],
    "process": ["process", "procedur", "deny", "due process", "hearing", "notice"],
    "custody": ["custody", "parenting time", "visitation", "withhold", "deny access"],
    "financial": ["financ", "support", "garnish", "arrearage", "income"],
    "false_allegations": ["false", "fabricat", "alleg", "accus", "lie", "perjur"],
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


class WeaponizationTracker:
    """Court process weaponization tracking and analysis."""

    def __init__(self):
        self._cache: Dict = {}

    # ── Data Access ───────────────────────────────────────────────────

    def get_weaponization_events(
        self, category: Optional[str] = None, limit: int = 100
    ) -> List[Dict]:
        """Query global_weaponization (7,131 rows)."""
        conn = _get_db()
        if not conn:
            return []

        try:
            if category:
                rows = conn.execute(
                    "SELECT category, substr(fact240, 1, 400) as fact240, "
                    "authoritieshitsuggested, relief_lever, sourcefile, ts_local "
                    "FROM global_weaponization "
                    "WHERE category LIKE ? "
                    "ORDER BY ts_local DESC LIMIT ?",
                    (f"%{category}%", limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT category, substr(fact240, 1, 400) as fact240, "
                    "authoritieshitsuggested, relief_lever, sourcefile, ts_local "
                    "FROM global_weaponization "
                    "ORDER BY ts_local DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            result = [dict(r) for r in rows]
            conn.close()
            return result
        except Exception:
            conn.close()
            return []

    def get_harms_violations(self, limit: int = 100) -> List[Dict]:
        """Query global_harms_violations (325 rows)."""
        conn = _get_db()
        if not conn:
            return []

        try:
            rows = conn.execute(
                "SELECT substr(harmsviolations_text, 1, 500) as text, "
                "sourcefile, msgid, ts_local "
                "FROM global_harms_violations "
                "ORDER BY ts_local DESC LIMIT ?",
                (limit,),
            ).fetchall()
            result = [dict(r) for r in rows]
            conn.close()
            return result
        except Exception:
            conn.close()
            return []

    # ── Specialized Tracking ──────────────────────────────────────────

    def track_ppo_weaponization(self) -> Dict:
        """Evidence of PPO being used as a weapon to deny parental rights."""
        events = self.get_weaponization_events(category="ppo", limit=200)

        # Also search for PPO-related harms
        conn = _get_db()
        harms = []
        if conn:
            try:
                rows = conn.execute(
                    "SELECT substr(harmsviolations_text, 1, 400) as text, "
                    "sourcefile, ts_local "
                    "FROM global_harms_violations "
                    "WHERE harmsviolations_text LIKE '%ppo%' "
                    "OR harmsviolations_text LIKE '%protection order%' "
                    "OR harmsviolations_text LIKE '%2950%' "
                    "LIMIT 50"
                ).fetchall()
                harms = [dict(r) for r in rows]
                conn.close()
            except Exception:
                conn.close()

        # If category filter returned few results, broaden search
        if len(events) < 5:
            all_events = self.get_weaponization_events(limit=500)
            ppo_keywords = WEAPONIZATION_CATEGORIES["ppo"]
            events = [
                e for e in all_events
                if any(
                    kw in (e.get("fact240", "") or "").lower()
                    or kw in (e.get("category", "") or "").lower()
                    for kw in ppo_keywords
                )
            ]

        return {
            "type": "PPO Weaponization",
            "authority": "MCL 600.2950 — Personal Protection Orders",
            "events_count": len(events),
            "harms_count": len(harms),
            "events": events[:50],
            "harms": harms[:20],
            "legal_hooks": [
                "MCL 600.2950 — PPO misuse as tactical litigation weapon",
                "MCL 722.23(j) — Obstruction of parent-child relationship via PPO",
                "US Const Amend XIV — Due process violation through weaponized PPO",
            ],
        }

    def track_contempt_weaponization(self) -> Dict:
        """Contempt proceedings used to harass or punish."""
        events = self.get_weaponization_events(category="contempt", limit=200)

        if len(events) < 5:
            all_events = self.get_weaponization_events(limit=500)
            keywords = WEAPONIZATION_CATEGORIES["contempt"]
            events = [
                e for e in all_events
                if any(
                    kw in (e.get("fact240", "") or "").lower()
                    or kw in (e.get("category", "") or "").lower()
                    for kw in keywords
                )
            ]

        return {
            "type": "Contempt Weaponization",
            "authority": "MCL 600.1701, MCR 3.606 — Contempt of Court",
            "events_count": len(events),
            "events": events[:50],
            "legal_hooks": [
                "MCL 600.1701 — Contempt used as harassment tool",
                "MCR 3.606 — Improper contempt procedure",
                "Sword v Sword, 399 Mich 367 (1976) — Contempt standards",
            ],
        }

    def track_process_weaponization(self) -> Dict:
        """Court process used to deny rights."""
        events = self.get_weaponization_events(category="process", limit=200)

        if len(events) < 5:
            all_events = self.get_weaponization_events(limit=500)
            keywords = WEAPONIZATION_CATEGORIES["process"]
            events = [
                e for e in all_events
                if any(
                    kw in (e.get("fact240", "") or "").lower()
                    or kw in (e.get("category", "") or "").lower()
                    for kw in keywords
                )
            ]

        return {
            "type": "Process Weaponization",
            "authority": "US Const Amend XIV — Due Process",
            "events_count": len(events),
            "events": events[:50],
            "legal_hooks": [
                "US Const Amend XIV — Fundamental right to parent",
                "Troxel v Granville, 530 US 57 (2000) — Parental rights",
                "MCR 2.003 — Judicial disqualification for process abuse",
                "MCR 3.210 — Custody procedure requirements",
            ],
        }

    # ── Timeline & Scoring ────────────────────────────────────────────

    def build_weaponization_timeline(self) -> List[Dict]:
        """Chronological weaponization events."""
        conn = _get_db()
        if not conn:
            return []

        try:
            rows = conn.execute(
                "SELECT category, substr(fact240, 1, 300) as fact240, "
                "authoritieshitsuggested, relief_lever, ts_local "
                "FROM global_weaponization "
                "WHERE ts_local IS NOT NULL AND ts_local != '' "
                "ORDER BY ts_local ASC LIMIT 500"
            ).fetchall()
            timeline = [dict(r) for r in rows]
            conn.close()
            return timeline
        except Exception:
            conn.close()
            return []

    def calculate_harm_score(self) -> Dict:
        """Quantified harm assessment based on weaponization data."""
        conn = _get_db()
        if not conn:
            return {"error": "DB connection failed"}

        try:
            weapon_count = conn.execute(
                "SELECT COUNT(*) FROM global_weaponization"
            ).fetchone()[0]
            harms_count = conn.execute(
                "SELECT COUNT(*) FROM global_harms_violations"
            ).fetchone()[0]

            # Category breakdown
            rows = conn.execute(
                "SELECT category, COUNT(*) as cnt "
                "FROM global_weaponization "
                "GROUP BY category ORDER BY cnt DESC"
            ).fetchall()
            categories = {r["category"]: r["cnt"] for r in rows}

            conn.close()

            # Score components (each 0-10)
            frequency_score = min(weapon_count / 500.0, 10.0)
            harm_severity = min(harms_count / 30.0, 10.0)
            diversity = min(len(categories) / 5.0, 10.0)

            composite = round(
                frequency_score * 0.4 + harm_severity * 0.35 + diversity * 0.25,
                2,
            )

            return {
                "composite_harm_score": composite,
                "frequency_score": round(frequency_score, 2),
                "harm_severity_score": round(harm_severity, 2),
                "diversity_score": round(diversity, 2),
                "total_weaponization_events": weapon_count,
                "total_harms_violations": harms_count,
                "category_breakdown": categories,
                "interpretation": (
                    "EXTREME" if composite >= 8 else
                    "SEVERE" if composite >= 6 else
                    "SIGNIFICANT" if composite >= 4 else
                    "MODERATE" if composite >= 2 else
                    "LOW"
                ),
                "days_separation": "329+",
            }
        except Exception as e:
            return {"error": str(e)}

    def generate_weaponization_report(self) -> Dict:
        """Formatted report for court filing."""
        harm = self.calculate_harm_score()
        ppo = self.track_ppo_weaponization()
        contempt = self.track_contempt_weaponization()
        process = self.track_process_weaponization()

        return {
            "report_title": "Weaponization of Court Processes — Analytical Report",
            "case": "Pigors v. Watson, No. 2024-001507-DC",
            "court": "14th Circuit Court, Muskegon County",
            "generated": datetime.now().isoformat(),
            "harm_assessment": harm,
            "ppo_weaponization": {
                "events": ppo["events_count"],
                "harms": ppo["harms_count"],
                "legal_hooks": ppo["legal_hooks"],
            },
            "contempt_weaponization": {
                "events": contempt["events_count"],
                "legal_hooks": contempt["legal_hooks"],
            },
            "process_weaponization": {
                "events": process["events_count"],
                "legal_hooks": process["legal_hooks"],
            },
            "recommendations": [
                "Assert due process violations in pending appeal (COA 366810)",
                "Include weaponization evidence in MSC complaint",
                "File motion documenting systematic abuse of court process",
                "Preserve record for federal civil rights action (42 USC § 1983)",
            ],
        }

    def get_statistics(self) -> Dict:
        """Summary statistics."""
        conn = _get_db()
        if not conn:
            return {"error": "DB connection failed"}

        stats: Dict = {}
        try:
            stats["global_weaponization_total"] = conn.execute(
                "SELECT COUNT(*) FROM global_weaponization"
            ).fetchone()[0]
            stats["global_harms_violations_total"] = conn.execute(
                "SELECT COUNT(*) FROM global_harms_violations"
            ).fetchone()[0]

            rows = conn.execute(
                "SELECT category, COUNT(*) as cnt "
                "FROM global_weaponization "
                "GROUP BY category ORDER BY cnt DESC LIMIT 20"
            ).fetchall()
            stats["weaponization_by_category"] = {
                str(r["category"]): r["cnt"] for r in rows
            }

            conn.close()
        except Exception as e:
            stats["error"] = str(e)

        return stats


def self_test() -> Dict:
    """Verify skill connectivity and data availability."""
    results = {"skill": "weaponization_tracker", "timestamp": datetime.now().isoformat()}
    conn = _get_db()
    if not conn:
        results["status"] = "FAIL"
        results["error"] = "DB connection failed"
        return results

    checks = {}
    for table in ["global_weaponization", "global_harms_violations"]:
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
    tracker = WeaponizationTracker()

    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "events":
            category = sys.argv[2] if len(sys.argv) > 2 else None
            cycle_json(tracker.get_weaponization_events(category=category))
        elif cmd == "harms":
            cycle_json(tracker.get_harms_violations())
        elif cmd == "ppo":
            cycle_json(tracker.track_ppo_weaponization())
        elif cmd == "contempt":
            cycle_json(tracker.track_contempt_weaponization())
        elif cmd == "process":
            cycle_json(tracker.track_process_weaponization())
        elif cmd == "timeline":
            cycle_json(tracker.build_weaponization_timeline())
        elif cmd == "harm_score":
            cycle_json(tracker.calculate_harm_score())
        elif cmd == "report":
            cycle_json(tracker.generate_weaponization_report())
        elif cmd == "stats":
            cycle_json(tracker.get_statistics())
        elif cmd == "self_test":
            cycle_json(self_test())
        else:
            print(f"Unknown command: {cmd}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Weaponization Tracker Skill")
        print("Usage: python weaponization_tracker.py <command> [category]")
        print("Commands: events, harms, ppo, contempt, process, timeline, harm_score, report, stats, self_test")
