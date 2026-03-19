"""
DELTA99 Ω∞ — Adversary Counter-Intelligence Engine
====================================================
Predicts adversary next moves based on behavioral patterns and temporal analysis.
Generates counter-strategies and pre-drafted response filings.

Depends on: d99-temporal-anomaly, d99-watson-pattern
Uses: adversary_models(114), omega_predictions(19), extracted_harms(26K),
      docket_events, master_chronological_timeline
"""
import sys
import sqlite3
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict

_shared = Path(__file__).parent.parent / "shared"
if str(_shared) not in sys.path:
    sys.path.insert(0, str(_shared))

from autonomos_config import CENTRAL_DB

COUNTER_DB = Path(__file__).parent / "counter_intel.db"

# ── Known Adversary Playbook Patterns ──────────────────────────────
WATSON_PLAYBOOK = [
    {"pattern": "emergency_motion", "trigger": "Father files any motion",
     "response": "Watson files emergency motion within 48hrs",
     "counter": "Pre-file response brief anticipating emergency claims"},
    {"pattern": "ppo_weaponization", "trigger": "Approaching exchange date",
     "response": "Watson alleges PPO violation to cancel parenting time",
     "counter": "Document all exchanges with witnesses + video + GPS timestamps"},
    {"pattern": "false_allegations", "trigger": "Custody hearing approaching",
     "response": "Watson files new allegations 7-14 days before hearing",
     "counter": "Prepare sworn affidavit rebutting common false claims"},
    {"pattern": "ex_parte_rush", "trigger": "Watson dissatisfied with ruling",
     "response": "Ex parte motion to McNeill for immediate modification",
     "counter": "File motion for disqualification + MSC superintending control"},
    {"pattern": "foc_manipulation", "trigger": "FOC review period",
     "response": "Watson provides false information to Rusco",
     "counter": "Submit counter-documentation to FOC within 21-day window"},
    {"pattern": "family_escalation", "trigger": "Court date approaching",
     "response": "Albert/Cody Watson increase harassment at exchanges",
     "counter": "File supplemental affidavit + request supervised exchange location"},
]

MCNEILL_PLAYBOOK = [
    {"pattern": "same_day_ruling", "trigger": "Watson files motion",
     "response": "Order entered same day without hearing",
     "counter": "Immediate objection + preserve for appeal + JTC documentation"},
    {"pattern": "deny_hearing", "trigger": "Father requests oral argument",
     "response": "Motion denied without hearing",
     "counter": "File MCR 2.119(E) request + preserve under Carines"},
    {"pattern": "ex_parte_order", "trigger": "Watson ex parte request",
     "response": "Signed without notice to Father",
     "counter": "Motion to vacate void order + due process argument"},
]


def _init_db() -> sqlite3.Connection:
    COUNTER_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(COUNTER_DB), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS threat_assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            adversary TEXT NOT NULL,
            predicted_action TEXT NOT NULL,
            trigger_event TEXT DEFAULT '',
            probability REAL DEFAULT 0.5,
            time_horizon_days INTEGER DEFAULT 14,
            counter_strategy TEXT DEFAULT '',
            pre_drafted_response TEXT DEFAULT '',
            assessed_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS counter_strategies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            threat_id INTEGER,
            strategy_name TEXT NOT NULL,
            description TEXT DEFAULT '',
            required_filings TEXT DEFAULT '[]',
            required_evidence TEXT DEFAULT '[]',
            priority TEXT DEFAULT 'MEDIUM'
        );
        CREATE TABLE IF NOT EXISTS adversary_behavior_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            adversary TEXT NOT NULL,
            action TEXT NOT NULL,
            date TEXT DEFAULT '',
            details TEXT DEFAULT '',
            matches_pattern TEXT DEFAULT '',
            logged_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS analysis_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            adversaries_analyzed INTEGER DEFAULT 0,
            threats_identified INTEGER DEFAULT 0,
            counters_generated INTEGER DEFAULT 0,
            duration_s REAL DEFAULT 0.0,
            run_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    return conn


def _analyze_recent_behavior(central: sqlite3.Connection,
                             adversary: str, days: int = 90) -> list[dict]:
    """Analyze recent adversary behavior from timeline and docket."""
    behaviors = []
    terms = adversary.lower().split()

    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    # Check docket_events
    for term in terms[:2]:
        try:
            rows = central.execute("""
                SELECT event_date, event_description, event_type
                FROM docket_events
                WHERE event_description LIKE ? AND event_date >= ?
                ORDER BY event_date DESC LIMIT 50
            """, (f"%{term}%", cutoff)).fetchall()
            for r in rows:
                behaviors.append({
                    "date": str(r[0] or ""),
                    "action": str(r[1] or "")[:300],
                    "type": str(r[2] or ""),
                    "source": "docket_events",
                })
        except sqlite3.Error:
            pass

    # Check master_chronological_timeline
    for term in terms[:2]:
        try:
            rows = central.execute("""
                SELECT event_date, event_description, category
                FROM master_chronological_timeline
                WHERE event_description LIKE ? AND event_date >= ?
                ORDER BY event_date DESC LIMIT 50
            """, (f"%{term}%", cutoff)).fetchall()
            for r in rows:
                behaviors.append({
                    "date": str(r[0] or ""),
                    "action": str(r[1] or "")[:300],
                    "type": str(r[2] or ""),
                    "source": "timeline",
                })
        except sqlite3.Error:
            pass

    return behaviors


def _match_playbook_patterns(behaviors: list[dict],
                             playbook: list[dict]) -> list[dict]:
    """Match observed behaviors against known playbook patterns."""
    matches = []
    for behavior in behaviors:
        action_lower = behavior["action"].lower()
        for pattern in playbook:
            trigger = pattern["trigger"].lower()
            response = pattern["response"].lower()
            # Check if behavior matches a known pattern trigger or response
            trigger_words = trigger.split()
            match_score = sum(1 for w in trigger_words if w in action_lower)
            if match_score >= len(trigger_words) * 0.4:
                matches.append({
                    "behavior": behavior["action"][:200],
                    "behavior_date": behavior["date"],
                    "matched_pattern": pattern["pattern"],
                    "predicted_response": pattern["response"],
                    "counter_strategy": pattern["counter"],
                    "match_confidence": min(match_score / len(trigger_words), 1.0),
                })
    return matches


def _generate_threat_assessment(adversary: str, behaviors: list[dict],
                                pattern_matches: list[dict]) -> list[dict]:
    """Generate threat predictions."""
    threats = []

    # Based on pattern matches
    for match in pattern_matches:
        threats.append({
            "adversary": adversary,
            "predicted_action": match["predicted_response"],
            "trigger": match["behavior"][:200],
            "probability": round(match["match_confidence"] * 0.8, 2),
            "horizon_days": 14,
            "counter": match["counter_strategy"],
        })

    # Based on behavior frequency
    action_freq = defaultdict(int)
    for b in behaviors:
        action_type = b.get("type", "unknown")
        action_freq[action_type] += 1

    for action_type, count in action_freq.items():
        if count >= 3:  # Repeated behavior = likely to recur
            threats.append({
                "adversary": adversary,
                "predicted_action": f"Repeat of {action_type} behavior (seen {count}x)",
                "trigger": "Recurring pattern",
                "probability": min(count * 0.15, 0.9),
                "horizon_days": 30,
                "counter": f"Prepare preemptive response for {action_type}",
            })

    return threats


def run_full_analysis() -> dict:
    """Run complete counter-intelligence analysis."""
    start = time.time()
    cdb = _init_db()
    central = sqlite3.connect(str(CENTRAL_DB), timeout=30)
    central.execute("PRAGMA busy_timeout=120000")

    all_threats = []
    all_counters = []
    adversary_results = {}

    adversaries_to_analyze = {
        "Emily Watson": WATSON_PLAYBOOK,
        "Judge McNeill": MCNEILL_PLAYBOOK,
        "Ron Berry": WATSON_PLAYBOOK[:3],
        "Pamela Rusco": [],
    }

    for adversary, playbook in adversaries_to_analyze.items():
        behaviors = _analyze_recent_behavior(central, adversary)
        pattern_matches = _match_playbook_patterns(behaviors, playbook) if playbook else []
        threats = _generate_threat_assessment(adversary, behaviors, pattern_matches)

        all_threats.extend(threats)

        # Persist
        for t in threats:
            tid = cdb.execute("""
                INSERT INTO threat_assessments
                (adversary, predicted_action, trigger_event, probability,
                 time_horizon_days, counter_strategy)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (t["adversary"], t["predicted_action"], t["trigger"],
                  t["probability"], t["horizon_days"], t["counter"])).lastrowid

            cdb.execute("""
                INSERT INTO counter_strategies
                (threat_id, strategy_name, description, priority)
                VALUES (?, ?, ?, ?)
            """, (tid, f"Counter {t['adversary']}", t["counter"],
                  "HIGH" if t["probability"] > 0.6 else "MEDIUM"))

        for b in behaviors:
            cdb.execute("""
                INSERT INTO adversary_behavior_log
                (adversary, action, date, details)
                VALUES (?, ?, ?, ?)
            """, (adversary, b["action"][:300], b["date"], b.get("source", "")))

        adversary_results[adversary] = {
            "recent_behaviors": len(behaviors),
            "pattern_matches": len(pattern_matches),
            "threats_predicted": len(threats),
            "top_threat": threats[0]["predicted_action"][:150] if threats else "None",
        }

    duration = round(time.time() - start, 2)
    cdb.execute("""
        INSERT INTO analysis_runs
        (adversaries_analyzed, threats_identified, counters_generated, duration_s)
        VALUES (?, ?, ?, ?)
    """, (len(adversaries_to_analyze), len(all_threats), len(all_threats), duration))
    cdb.commit()
    central.close()
    cdb.close()

    return {
        "adversaries_analyzed": len(adversaries_to_analyze),
        "total_threats": len(all_threats),
        "adversary_details": adversary_results,
        "top_threats": [
            {"adversary": t["adversary"], "action": t["predicted_action"][:150],
             "probability": t["probability"], "counter": t["counter"][:150]}
            for t in sorted(all_threats, key=lambda x: -x["probability"])[:10]
        ],
        "duration_s": duration,
    }


if __name__ == "__main__":
    result = run_full_analysis()
    print(json.dumps(result, indent=2, default=str))
