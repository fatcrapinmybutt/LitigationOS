"""
NEMESIS — Neutralizing Enemy Maneuvers via Evidence-backed Strategic Intelligence System
═══════════════════════════════════════════════════════════════════════════════════════════

Analyzes adversary behavior patterns, predicts likely moves, pre-builds counter-strategies,
and identifies exploitable vulnerabilities. Part of the PANTHEON Engine Suite.
"""

import sys
import os
import json
import sqlite3
import hashlib
import re
import logging
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)

DB_PATH= str(Path(__file__).resolve().parents[3] / "litigation_context.db")

# Verified party identity — NEVER fabricate
ADVERSARIES = {
    "emily_watson": {
        "name": "Emily A. Watson",
        "role": "defendant",
        "address": "2160 Garland Drive, Norton Shores, MI 49441",
        "known_associates": ["Ronald Berry", "Albert Watson", "Lori Watson", "Jennifer Barnes (P55406)"],
    },
    "jennifer_barnes": {
        "name": "Jennifer Barnes (P55406)",
        "role": "defendant_attorney",
        "status": "WITHDREW",
        "firm": "Barnes Law Firm PLLC, 880 Jefferson St Ste B, Muskegon, MI 49440",
    },
    "jenny_mcneill": {
        "name": "Hon. Jenny L. McNeill",
        "role": "judge_family",
        "court": "14th Circuit Court, Family Division",
        "former_firm": "Ladas, Hoopes & McNeill, 435 Whitehall Rd",
        "conflict": "Former partner with Kenneth Hoopes (Chief Judge) and Maria Ladas-Hoopes (60th District)",
    },
    "ronald_berry": {
        "name": "Ronald Berry",
        "role": "non_attorney_associate",
        "relationship": "Emily's boyfriend/domestic partner",
        "address": "2160 Garland Drive, Norton Shores, MI 49441",
        "notes": "NO bar number. NO Esq. NEVER was Emily's attorney.",
    },
}

# Known adversary behavioral patterns (from evidence analysis)
KNOWN_PATTERNS = {
    "accusation_before_filing": {
        "description": "Emily makes accusations shortly before court filings/hearings",
        "evidence": "PPO petition filed 2 days after recanting 'nothing was physical'",
    },
    "police_weaponization": {
        "description": "Using police reports as leverage for court orders",
        "evidence": "Albert: 'they want this documented so Emily can get an Ex Parte order'",
    },
    "false_victim_narrative": {
        "description": "Andrew documented as VICTIM, but Emily claims she is victim",
        "evidence": "Police reports: Andrew=victim, Cody Watson=offender",
    },
    "judicial_cartel": {
        "description": "Three judges from same law firm handling interrelated cases",
        "evidence": "McNeill + Hoopes + Ladas-Hoopes all from Ladas, Hoopes & McNeill",
    },
}

# Adversary move types
MOVE_TYPES = [
    "motion_to_dismiss", "motion_for_sanctions", "ppo_extension", "custody_modification",
    "contempt_motion", "emergency_ex_parte", "motion_to_strike", "objection_to_evidence",
    "motion_for_continuance", "motion_in_limine", "discovery_request", "subpoena",
    "counter_complaint", "motion_for_default", "appeal", "jtc_interference",
]


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    return conn


def init_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS nemesis_profiles (
            profile_id TEXT PRIMARY KEY,
            adversary_key TEXT NOT NULL,
            name TEXT NOT NULL,
            behavior_summary TEXT,
            threat_level INTEGER DEFAULT 5,
            patterns_json TEXT,
            weaknesses_json TEXT,
            updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS nemesis_predictions (
            prediction_id TEXT PRIMARY KEY,
            adversary_key TEXT NOT NULL,
            move_type TEXT NOT NULL,
            probability REAL DEFAULT 0.5,
            timing_estimate TEXT,
            trigger_event TEXT,
            reasoning TEXT,
            counter_strategy_id TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS nemesis_counters (
            counter_id TEXT PRIMARY KEY,
            prediction_id TEXT,
            adversary_key TEXT,
            move_type TEXT NOT NULL,
            counter_type TEXT NOT NULL,
            title TEXT NOT NULL,
            strategy TEXT NOT NULL,
            authority TEXT,
            evidence_needed TEXT,
            filing_lane TEXT,
            pre_built INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS nemesis_vulnerabilities (
            vuln_id TEXT PRIMARY KEY,
            adversary_key TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            severity INTEGER DEFAULT 5,
            evidence_refs TEXT,
            exploitation_strategy TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_nemesis_pred_adv ON nemesis_predictions(adversary_key);
        CREATE INDEX IF NOT EXISTS idx_nemesis_vuln_adv ON nemesis_vulnerabilities(adversary_key);
    """)


class NemesisEngine:
    """Adversary intelligence and counter-strategy engine."""

    def __init__(self):
        self.conn = get_db()
        init_tables(self.conn)

    def build_profile(self, adversary_key: str) -> dict:
        """Build or update adversary behavioral profile."""
        if adversary_key not in ADVERSARIES:
            return {"error": f"Unknown adversary: {adversary_key}"}

        adv = ADVERSARIES[adversary_key]
        patterns = self._analyze_patterns(adversary_key)
        weaknesses = self._identify_weaknesses(adversary_key)

        profile_id = f"profile-{adversary_key}"
        threat_level = self._calculate_threat_level(adversary_key, patterns)

        self.conn.execute(
            "INSERT OR REPLACE INTO nemesis_profiles "
            "(profile_id, adversary_key, name, behavior_summary, threat_level, patterns_json, weaknesses_json, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))",
            (profile_id, adversary_key, adv["name"],
             self._generate_behavior_summary(adversary_key, patterns),
             threat_level, json.dumps(patterns), json.dumps(weaknesses))
        )
        self.conn.commit()

        return {
            "profile_id": profile_id,
            "name": adv["name"],
            "threat_level": threat_level,
            "patterns": len(patterns),
            "weaknesses": len(weaknesses),
        }

    def _analyze_patterns(self, adversary_key: str) -> list:
        """Analyze behavioral patterns from DB evidence."""
        patterns = []

        # Check for known patterns
        for pat_key, pat_data in KNOWN_PATTERNS.items():
            if adversary_key in ["emily_watson", "jenny_mcneill", "ronald_berry"]:
                patterns.append({
                    "type": pat_key,
                    "description": pat_data["description"],
                    "evidence": pat_data["evidence"],
                    "confidence": 0.8,
                })

        # Query DB for additional pattern data
        try:
            # Check chimera_contradictions if exists
            tables = [r[0] for r in self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'chimera%'"
            ).fetchall()]

            if "chimera_contradictions" in tables:
                contras = self.conn.execute(
                    "SELECT COUNT(*) FROM chimera_contradictions WHERE statement_id_a LIKE ? OR statement_id_b LIKE ?",
                    (f"%{adversary_key}%", f"%{adversary_key}%")
                ).fetchone()[0]
                if contras > 0:
                    patterns.append({
                        "type": "serial_contradiction",
                        "description": f"{contras} contradictory statements detected",
                        "confidence": 0.9,
                    })

            # Check evidence_quotes for adversary mentions
            if self._table_exists("evidence_quotes"):
                quotes = self.conn.execute(
                    "SELECT COUNT(*) FROM evidence_quotes WHERE content LIKE ?",
                    (f"%{ADVERSARIES[adversary_key]['name'].split()[0]}%",)
                ).fetchone()[0]
                if quotes > 0:
                    patterns.append({
                        "type": "documented_behavior",
                        "description": f"{quotes} evidence quotes referencing this adversary",
                        "confidence": 0.7,
                    })
        except Exception as e:
            logger.warning("[_analyze_patterns] DB pattern query failed for %s: %s", adversary_key, e, exc_info=True)

        return patterns

    def _identify_weaknesses(self, adversary_key: str) -> list:
        """Identify exploitable vulnerabilities."""
        weaknesses = []

        if adversary_key == "emily_watson":
            weaknesses = [
                {"category": "credibility", "description": "Recanted 'nothing was physical' then filed PPO claiming violence", "severity": 9},
                {"category": "credibility", "description": "Police reports document Andrew as VICTIM, not offender", "severity": 9},
                {"category": "motive", "description": "Albert admitted weaponizing police reports for Ex Parte order", "severity": 10},
                {"category": "credibility", "description": "0 arrests, 0 charges against Andrew across all police contacts", "severity": 8},
                {"category": "pattern", "description": "Accusations precede court dates — suggests strategic timing", "severity": 7},
                {"category": "associate", "description": "Ronald Berry (non-attorney) potentially practicing law", "severity": 6},
            ]
        elif adversary_key == "jenny_mcneill":
            weaknesses = [
                {"category": "conflict", "description": "Former partner at Ladas, Hoopes & McNeill with Chief Judge Hoopes", "severity": 10},
                {"category": "bias", "description": "Three judges from same firm handling interrelated cases", "severity": 10},
                {"category": "due_process", "description": "Ex parte communications alleged", "severity": 8},
                {"category": "procedure", "description": "Potential MCR 2.003 disqualification grounds", "severity": 9},
                {"category": "conflict", "description": "Cannot be impartially reassigned — Hoopes is Chief Judge", "severity": 9},
            ]
        elif adversary_key == "jennifer_barnes":
            weaknesses = [
                {"category": "withdrawal", "description": "Withdrew from case — may indicate knowledge of weak position", "severity": 5},
                {"category": "ethics", "description": "Potential knowledge of client's false statements", "severity": 6},
            ]
        elif adversary_key == "ronald_berry":
            weaknesses = [
                {"category": "standing", "description": "Non-attorney with no legal standing in custody proceedings", "severity": 7},
                {"category": "credibility", "description": "Lives with defendant — bias as witness", "severity": 6},
                {"category": "interference", "description": "Potential unauthorized practice of law", "severity": 7},
            ]

        # Store vulnerabilities
        for w in weaknesses:
            vid = hashlib.md5(f"{adversary_key}:{w['description'][:50]}".encode()).hexdigest()[:12]
            self.conn.execute(
                "INSERT OR REPLACE INTO nemesis_vulnerabilities "
                "(vuln_id, adversary_key, category, description, severity, exploitation_strategy) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (vid, adversary_key, w["category"], w["description"], w["severity"],
                 self._suggest_exploitation(w))
            )
        self.conn.commit()
        return weaknesses

    def _suggest_exploitation(self, weakness: dict) -> str:
        """Suggest how to exploit a weakness legally and ethically."""
        category = weakness.get("category", "")
        if category == "credibility":
            return "Cross-examine with contradictory documents. Impeach per MRE 613."
        elif category == "conflict":
            return "File MCR 2.003 disqualification motion. Request MSC original jurisdiction if entire circuit compromised."
        elif category == "motive":
            return "Present admission in motion/trial. Argue bad faith per MCL 722.27a."
        elif category == "due_process":
            return "Document violations. Include in appellate record. Cite Mathews v. Eldridge."
        elif category == "pattern":
            return "Build timeline overlay showing accusation-filing correlation. Present as impeachment exhibit."
        elif category == "bias":
            return "JTC complaint with documented pattern. COA appeal citing structural bias."
        return "Document thoroughly. Include in appropriate filing."

    def _calculate_threat_level(self, adversary_key: str, patterns: list) -> int:
        """Calculate threat level 1-10."""
        base = 5
        if adversary_key == "emily_watson":
            base = 7  # Primary adversary
        elif adversary_key == "jenny_mcneill":
            base = 9  # Judge with power + conflict
        elif adversary_key == "jennifer_barnes":
            base = 3  # Withdrew
        elif adversary_key == "ronald_berry":
            base = 4  # No legal standing
        return min(10, base + len(patterns) // 3)

    def _generate_behavior_summary(self, adversary_key: str, patterns: list) -> str:
        """Generate narrative behavior summary."""
        adv = ADVERSARIES[adversary_key]
        pat_descriptions = [p["description"] for p in patterns[:5]]
        return f"{adv['name']}: {'; '.join(pat_descriptions)}" if pat_descriptions else f"{adv['name']}: No patterns detected yet."

    def predict(self, adversary_key: str, context: str = "") -> list:
        """Predict likely adversary moves based on patterns and context."""
        predictions = []

        if adversary_key == "emily_watson":
            predictions = [
                {"move": "ppo_extension", "probability": 0.7,
                 "reasoning": "History of using PPO as leverage; likely to seek extension before expiration",
                 "timing": "Before PPO expiration date",
                 "trigger": "Andrew files any motion asserting rights"},
                {"move": "contempt_motion", "probability": 0.6,
                 "reasoning": "Pattern of retaliatory filings when Andrew asserts parenting rights",
                 "timing": "Within 14 days of Andrew's next filing",
                 "trigger": "Andrew files custody motion or requests parenting time"},
                {"move": "emergency_ex_parte", "probability": 0.5,
                 "reasoning": "Albert admitted strategy of using police reports for Ex Parte orders",
                 "timing": "Before next scheduled hearing",
                 "trigger": "Any confrontation or police contact"},
                {"move": "motion_for_sanctions", "probability": 0.4,
                 "reasoning": "Common defense tactic against pro se litigants",
                 "timing": "After Andrew files multiple motions",
                 "trigger": "Andrew files 3+ motions in short period"},
                {"move": "custody_modification", "probability": 0.3,
                 "reasoning": "May seek to formalize current custody arrangement",
                 "timing": "If parenting time withholding is challenged",
                 "trigger": "Andrew successfully argues for parenting time restoration"},
            ]
        elif adversary_key == "jenny_mcneill":
            predictions = [
                {"move": "motion_to_dismiss", "probability": 0.6,
                 "reasoning": "May dismiss disqualification motion without hearing",
                 "timing": "Within 14 days of filing",
                 "trigger": "Andrew files MCR 2.003 disqualification"},
                {"move": "motion_for_sanctions", "probability": 0.5,
                 "reasoning": "Judges sometimes sanction pro se litigants for disqualification motions",
                 "timing": "At hearing on disqualification",
                 "trigger": "Disqualification motion filed"},
                {"move": "jtc_interference", "probability": 0.3,
                 "reasoning": "May attempt to influence proceedings if JTC complaint filed",
                 "timing": "After JTC complaint becomes known",
                 "trigger": "JTC complaint filed"},
            ]

        # Store predictions
        for pred in predictions:
            pid = hashlib.md5(f"{adversary_key}:{pred['move']}:{datetime.now().isoformat()}".encode()).hexdigest()[:12]
            counter = self._build_counter(adversary_key, pred)
            self.conn.execute(
                "INSERT OR REPLACE INTO nemesis_predictions "
                "(prediction_id, adversary_key, move_type, probability, timing_estimate, trigger_event, reasoning, counter_strategy_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (pid, adversary_key, pred["move"], pred["probability"],
                 pred.get("timing", ""), pred.get("trigger", ""), pred["reasoning"],
                 counter.get("counter_id", ""))
            )
        self.conn.commit()
        return predictions

    def _build_counter(self, adversary_key: str, prediction: dict) -> dict:
        """Build a counter-strategy for a predicted move."""
        move = prediction["move"]
        counters = {
            "ppo_extension": {
                "counter_type": "responsive_motion",
                "title": "Response to PPO Extension + Motion to Dismiss PPO",
                "strategy": "Present recantation evidence ('nothing was physical'), Albert's admission of weaponization, "
                           "police reports showing Andrew as victim. Argue PPO was obtained by fraud. MCL 600.2950.",
                "authority": "MCL 600.2950; MCR 3.706(H); Pickering v Pickering",
                "evidence_needed": "Police reports, Emily's recantation, Albert's admission recording",
                "lane": "D",
            },
            "contempt_motion": {
                "counter_type": "responsive_motion",
                "title": "Response to Contempt + Counter-Motion for Contempt",
                "strategy": "Deny alleged violation. Counter with Emily's contempt (withholding parenting time). "
                           "Show pattern of retaliatory filings. Request sanctions for frivolous contempt motion.",
                "authority": "MCL 600.1701; MCR 3.606; In re Contempt of Dougherty",
                "evidence_needed": "Parenting time log, communication records, filing timeline",
                "lane": "A",
            },
            "emergency_ex_parte": {
                "counter_type": "motion_to_vacate",
                "title": "Emergency Motion to Vacate Ex Parte Order",
                "strategy": "Challenge ex parte order within 14 days. Show no genuine emergency. "
                           "Present evidence of strategic abuse of ex parte process. Request hearing.",
                "authority": "MCR 2.119(B); MCR 3.207(B); Kernen v Homestead Development",
                "evidence_needed": "Timeline of prior ex parte abuse, Albert's admission, lack of genuine emergency",
                "lane": "A",
            },
            "motion_for_sanctions": {
                "counter_type": "responsive_brief",
                "title": "Response to Motion for Sanctions",
                "strategy": "Show filings are well-grounded in fact and law. Pro se litigant held to less strict standard. "
                           "Counter-argue that sanctions motion is itself frivolous attempt to chill access to courts.",
                "authority": "MCR 2.114(E); Louya v William Beaumont Hosp; Diehl v Danuloff",
                "evidence_needed": "All filing authorities verified, evidence supporting each claim",
                "lane": "A",
            },
            "motion_to_dismiss": {
                "counter_type": "responsive_brief",
                "title": "Response to Motion to Dismiss",
                "strategy": "Argue factual and legal sufficiency. Show all elements met. "
                           "If disqualification: argue mandatory duty under MCR 2.003. Cannot dismiss without hearing.",
                "authority": "MCR 2.116(C)(8); MCR 2.003(D); Kern v Kern-Koskela",
                "evidence_needed": "Verified factual basis for each claim, authority chain",
                "lane": "A",
            },
            "custody_modification": {
                "counter_type": "counter_motion",
                "title": "Counter-Motion for Custody Modification + Parenting Time Restoration",
                "strategy": "Show proper cause/change in circumstances (withholding). Best interest factors favor Andrew. "
                           "Present full evidence of Emily's alienation pattern and parenting time denial.",
                "authority": "MCL 722.27; MCL 722.23 (best interest factors); Vodvarka v Grasmeyer",
                "evidence_needed": "Withholding timeline, child welfare evidence, stability comparison",
                "lane": "A",
            },
            "jtc_interference": {
                "counter_type": "supplemental_complaint",
                "title": "Supplemental JTC Complaint — Retaliation",
                "strategy": "Document any retaliatory action after JTC complaint. File supplemental complaint "
                           "with JTC showing pattern of retaliation confirms original complaint.",
                "authority": "MCR 9.220; Const 1963, art 6, § 30",
                "evidence_needed": "JTC complaint, timeline of retaliation, retaliatory orders",
                "lane": "E",
            },
        }

        counter_data = counters.get(move, {
            "counter_type": "responsive_motion",
            "title": f"Response to {move.replace('_', ' ').title()}",
            "strategy": "Respond within deadline. Present evidence. Argue on merits.",
            "authority": "MCR 2.119",
            "evidence_needed": "Relevant evidence for this claim",
            "lane": "A",
        })

        counter_id = hashlib.md5(f"counter:{adversary_key}:{move}".encode()).hexdigest()[:12]
        self.conn.execute(
            "INSERT OR REPLACE INTO nemesis_counters "
            "(counter_id, adversary_key, move_type, counter_type, title, strategy, authority, evidence_needed, filing_lane) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (counter_id, adversary_key, move, counter_data["counter_type"],
             counter_data["title"], counter_data["strategy"],
             counter_data.get("authority", ""), counter_data.get("evidence_needed", ""),
             counter_data.get("lane", "A"))
        )
        self.conn.commit()
        return {"counter_id": counter_id, **counter_data}

    def _table_exists(self, table_name: str) -> bool:
        r = self.conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
        ).fetchone()
        return r[0] > 0

    def vulnerability_report(self, adversary_key: str = None) -> list:
        """Get vulnerability report."""
        query = "SELECT * FROM nemesis_vulnerabilities"
        params = ()
        if adversary_key:
            query += " WHERE adversary_key = ?"
            params = (adversary_key,)
        query += " ORDER BY severity DESC"
        return [dict(r) for r in self.conn.execute(query, params).fetchall()]

    def status(self) -> dict:
        row = self.conn.execute("""
            SELECT
                (SELECT COUNT(*) FROM nemesis_profiles) as profiles,
                (SELECT COUNT(*) FROM nemesis_predictions) as predictions,
                (SELECT COUNT(*) FROM nemesis_counters) as counters,
                (SELECT COUNT(*) FROM nemesis_vulnerabilities) as vulnerabilities
        """).fetchone()
        return dict(row)

    def close(self):
        self.conn.close()


def main():
    if len(sys.argv) < 2:
        print("""
╔═══════════════════════════════════════════════════════════════╗
║          NEMESIS ⚔️  — Adversary Intelligence Engine           ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  Commands:                                                    ║
║    profile <adversary>    — Build/update adversary profile     ║
║    predict <adversary>    — Predict likely moves               ║
║    counter <adversary> <move_type> — Get counter-strategy      ║
║    vulns [adversary]      — Vulnerability report               ║
║    all                    — Full analysis of all adversaries    ║
║    status                 — Dashboard                          ║
║                                                               ║
║  Adversaries: emily_watson, jenny_mcneill, jennifer_barnes,   ║
║               ronald_berry                                     ║
║                                                               ║
║  Move types: ppo_extension, contempt_motion, emergency,       ║
║              motion_for_sanctions, motion_to_dismiss,          ║
║              custody_modification, jtc_interference            ║
╚═══════════════════════════════════════════════════════════════╝""")
        return

    cmd = sys.argv[1]
    engine = NemesisEngine()

    try:
        if cmd == "profile" and len(sys.argv) >= 3:
            result = engine.build_profile(sys.argv[2])
            print(json.dumps(result, indent=2))

        elif cmd == "predict" and len(sys.argv) >= 3:
            preds = engine.predict(sys.argv[2])
            for p in preds:
                prob_bar = "█" * int(p["probability"] * 10) + "░" * (10 - int(p["probability"] * 10))
                print(f"  [{prob_bar}] {p['probability']:.0%} — {p['move'].replace('_', ' ').title()}")
                print(f"    Trigger: {p.get('trigger', 'N/A')}")
                print(f"    Timing:  {p.get('timing', 'N/A')}")
                print()

        elif cmd == "vulns":
            adv_key = sys.argv[2] if len(sys.argv) >= 3 else None
            vulns = engine.vulnerability_report(adv_key)
            for v in vulns:
                severity_bar = "🔴" * (v["severity"] // 3) + "🟡" * ((v["severity"] % 3) > 0)
                print(f"  [{v['severity']}/10] {v['category'].upper()}: {v['description']}")

        elif cmd == "all":
            print("═" * 60)
            print("  NEMESIS — Full Adversary Analysis")
            print("═" * 60)
            for adv_key in ADVERSARIES:
                print(f"\n▶ {ADVERSARIES[adv_key]['name']}")
                profile = engine.build_profile(adv_key)
                print(f"  Threat Level: {'🔴' * (profile['threat_level'] // 2)}  ({profile['threat_level']}/10)")
                print(f"  Patterns: {profile['patterns']}  |  Weaknesses: {profile['weaknesses']}")
                preds = engine.predict(adv_key)
                if preds:
                    top = max(preds, key=lambda p: p["probability"])
                    print(f"  Most Likely Move: {top['move'].replace('_', ' ').title()} ({top['probability']:.0%})")
            s = engine.status()
            print(f"\n  Total: {s['profiles']} profiles, {s['predictions']} predictions, "
                  f"{s['counters']} counters, {s['vulnerabilities']} vulnerabilities")

        elif cmd == "status":
            s = engine.status()
            print(f"""
╔═══════════════════════════════════════╗
║       NEMESIS STATUS DASHBOARD        ║
╠═══════════════════════════════════════╣
║  Profiles:        {s['profiles']:>4}                ║
║  Predictions:     {s['predictions']:>4}                ║
║  Counter-Strats:  {s['counters']:>4}                ║
║  Vulnerabilities: {s['vulnerabilities']:>4}                ║
╚═══════════════════════════════════════╝""")
        else:
            print(f"Unknown command: {cmd}")
    finally:
        engine.close()


if __name__ == "__main__":
    main()
