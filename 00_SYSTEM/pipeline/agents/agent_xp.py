"""
AGENT XP SYSTEM — Experience Points, Leveling, and Auto-Improvement

Every agent gains XP after completing a task based on:
  - Items processed (base XP)
  - Quality score (multiplier)
  - Accuracy bonus
  - Findings discovered
  - Inter-agent collaboration
  - Speed bonus (above-average throughput)

Levels follow exponential progression: xp_per_level = 100 * (level ^ 1.5)

Integration:
  - Called from agent_orchestrator.py after each agent completes
  - Reads AgentResult to compute XP
  - Stores in litigation_context.db (agent_xp + agent_xp_history tables)
  - Agents can query their own level to unlock advanced behaviors

Usage:
  xp = AgentXP()
  xp.grant_xp(agent_result)
  level = xp.get_level("A01")
  leaderboard = xp.get_leaderboard()
"""
import math
import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .agent_models import AgentResult, QualityScore

LITIGATION_DB = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")


def _connect(db_path: Path = LITIGATION_DB) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), timeout=60)
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.row_factory = sqlite3.Row
    return conn


class AgentXP:
    """Manages agent experience points, leveling, and auto-improvement triggers."""

    # Level thresholds: level N requires 100 * N^1.5 cumulative XP
    XP_BASE_PER_ITEM = 10
    ACCURACY_BONUS_BASE = 10
    ACCURACY_BONUS_MAX = 40
    FINDING_XP_PER_RELEVANCE = 20
    COLLAB_XP_PER_MSG = 2
    SPEED_BONUS_THRESHOLD = 1.0  # throughput > 1.0 earns speed bonus

    # Level milestones unlock capabilities
    LEVEL_UNLOCKS = {
        1: "basic",           # Default — all agents start here
        3: "parallel",        # Can use parallel workers
        5: "sub_agent",       # Can spawn sub-agents
        7: "plan_execute",    # Can use plan-and-execute pattern
        10: "react_loop",     # Can use ReAct reasoning loop
        15: "self_evolve",    # Can modify own prompts/strategies
        20: "fleet_command",  # Can orchestrate other agents
        25: "omega",          # Full autonomy
    }

    def __init__(self, db_path: Path = LITIGATION_DB):
        self.db_path = db_path
        self._ensure_tables()

    def _ensure_tables(self):
        """Create XP tables if they don't exist."""
        conn = _connect(self.db_path)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS agent_xp (
                    agent_id TEXT PRIMARY KEY,
                    total_xp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    current_xp_in_level INTEGER DEFAULT 0,
                    next_level_xp INTEGER DEFAULT 100,
                    runs_completed INTEGER DEFAULT 0,
                    runs_success INTEGER DEFAULT 0,
                    runs_partial INTEGER DEFAULT 0,
                    runs_fatal INTEGER DEFAULT 0,
                    best_quality REAL DEFAULT 0.0,
                    avg_quality REAL DEFAULT 0.0,
                    total_findings INTEGER DEFAULT 0,
                    total_messages INTEGER DEFAULT 0,
                    unlocked_capabilities TEXT DEFAULT 'basic',
                    last_run_at TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS agent_xp_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    run_id TEXT,
                    xp_gained INTEGER DEFAULT 0,
                    xp_breakdown TEXT,
                    quality_score REAL DEFAULT 0.0,
                    items_processed INTEGER DEFAULT 0,
                    items_total INTEGER DEFAULT 0,
                    findings_count INTEGER DEFAULT 0,
                    messages_sent INTEGER DEFAULT 0,
                    status TEXT,
                    level_before INTEGER DEFAULT 1,
                    level_after INTEGER DEFAULT 1,
                    leveled_up INTEGER DEFAULT 0,
                    timestamp TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (agent_id) REFERENCES agent_xp(agent_id)
                );

                CREATE INDEX IF NOT EXISTS idx_xp_history_agent
                    ON agent_xp_history(agent_id);
                CREATE INDEX IF NOT EXISTS idx_xp_history_time
                    ON agent_xp_history(timestamp);
            """)
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def xp_for_level(level: int) -> int:
        """Calculate total XP needed to reach a given level."""
        if level <= 1:
            return 0
        return int(100 * math.pow(level, 1.5))

    @staticmethod
    def level_from_xp(total_xp: int) -> Tuple[int, int, int]:
        """Given total XP, return (level, xp_in_current_level, xp_needed_for_next).
        
        Returns:
            (level, current_xp_in_level, next_level_xp)
        """
        level = 1
        while True:
            next_threshold = int(100 * math.pow(level + 1, 1.5))
            if total_xp < next_threshold:
                prev_threshold = int(100 * math.pow(level, 1.5)) if level > 1 else 0
                return (level, total_xp - prev_threshold, next_threshold - prev_threshold)
            level += 1

    def calculate_xp(self, result: AgentResult) -> Dict[str, int]:
        """Calculate XP earned from an AgentResult.
        
        Returns breakdown dict with component XP values.
        """
        stats = result.stats
        quality = result.quality or QualityScore()

        # Base XP: items processed * base rate
        base_xp = stats.processed * self.XP_BASE_PER_ITEM

        # Quality multiplier (0.0 - 1.0 scales the base)
        quality_xp = int(base_xp * quality.overall)

        # Accuracy bonus: scales with accuracy dimension
        accuracy_bonus = int(self.ACCURACY_BONUS_BASE +
                             (quality.accuracy * self.ACCURACY_BONUS_MAX))

        # Finding bonus: each finding weighted by relevance
        finding_bonus = 0
        for f in result.findings:
            relevance = f.get("relevance", 0.5)
            finding_bonus += int(relevance * self.FINDING_XP_PER_RELEVANCE)

        # Collaboration bonus
        collab_bonus = result.messages_sent * self.COLLAB_XP_PER_MSG

        # Speed bonus (only if throughput > threshold)
        speed_bonus = 0
        if quality.throughput > self.SPEED_BONUS_THRESHOLD:
            speed_bonus = int((quality.throughput - self.SPEED_BONUS_THRESHOLD) * 100)

        # Status penalty: FATAL/CRASH get reduced XP
        status_multiplier = {
            "SUCCESS": 1.0,
            "PARTIAL": 0.6,
            "FATAL": 0.1,
            "CRASH": 0.05,
        }.get(result.status, 0.5)

        total = int((quality_xp + accuracy_bonus + finding_bonus +
                     collab_bonus + speed_bonus) * status_multiplier)

        # Minimum 1 XP for any completed run (even failures teach something)
        total = max(1, total)

        return {
            "base_xp": base_xp,
            "quality_xp": quality_xp,
            "accuracy_bonus": accuracy_bonus,
            "finding_bonus": finding_bonus,
            "collab_bonus": collab_bonus,
            "speed_bonus": speed_bonus,
            "status_multiplier": status_multiplier,
            "total": total,
        }

    def grant_xp(self, result: AgentResult, run_id: str = None) -> Dict:
        """Grant XP to an agent based on their run result.
        
        Returns dict with: agent_id, xp_gained, level_before, level_after, 
                          leveled_up, unlocked_capabilities
        """
        breakdown = self.calculate_xp(result)
        xp_gained = breakdown["total"]
        agent_id = result.agent_id

        conn = _connect(self.db_path)
        try:
            # Get or create agent record
            row = conn.execute(
                "SELECT total_xp, level, runs_completed, runs_success, "
                "runs_partial, runs_fatal, best_quality, avg_quality, "
                "total_findings, total_messages FROM agent_xp WHERE agent_id = ?",
                (agent_id,)
            ).fetchone()

            if row is None:
                # First run — create record
                conn.execute(
                    "INSERT INTO agent_xp (agent_id, total_xp, level) VALUES (?, 0, 1)",
                    (agent_id,)
                )
                old_xp = 0
                old_level = 1
                runs = 0
                successes = 0
                partials = 0
                fatals = 0
                best_q = 0.0
                avg_q = 0.0
                total_findings = 0
                total_msgs = 0
            else:
                old_xp = row["total_xp"]
                old_level = row["level"]
                runs = row["runs_completed"]
                successes = row["runs_success"]
                partials = row["runs_partial"]
                fatals = row["runs_fatal"]
                best_q = row["best_quality"]
                avg_q = row["avg_quality"]
                total_findings = row["total_findings"]
                total_msgs = row["total_messages"]

            # Calculate new totals
            new_xp = old_xp + xp_gained
            new_level, current_in_level, next_level_xp = self.level_from_xp(new_xp)
            leveled_up = new_level > old_level

            quality_score = (result.quality.overall if result.quality else 0.0)
            new_best = max(best_q, quality_score)
            new_avg = ((avg_q * runs) + quality_score) / (runs + 1)

            # Status counters
            new_runs = runs + 1
            new_success = successes + (1 if result.status == "SUCCESS" else 0)
            new_partial = partials + (1 if result.status == "PARTIAL" else 0)
            new_fatal = fatals + (1 if result.status in ("FATAL", "CRASH") else 0)
            new_findings = total_findings + len(result.findings)
            new_msgs = total_msgs + result.messages_sent

            # Determine unlocked capabilities
            unlocked = []
            for lvl, cap in sorted(self.LEVEL_UNLOCKS.items()):
                if new_level >= lvl:
                    unlocked.append(cap)
            unlocked_str = ",".join(unlocked)

            # Update agent record
            conn.execute("""
                UPDATE agent_xp SET
                    total_xp = ?,
                    level = ?,
                    current_xp_in_level = ?,
                    next_level_xp = ?,
                    runs_completed = ?,
                    runs_success = ?,
                    runs_partial = ?,
                    runs_fatal = ?,
                    best_quality = ?,
                    avg_quality = ?,
                    total_findings = ?,
                    total_messages = ?,
                    unlocked_capabilities = ?,
                    last_run_at = datetime('now'),
                    updated_at = datetime('now')
                WHERE agent_id = ?
            """, (new_xp, new_level, current_in_level, next_level_xp,
                  new_runs, new_success, new_partial, new_fatal,
                  new_best, round(new_avg, 4), new_findings, new_msgs,
                  unlocked_str, agent_id))

            # Record history
            import json
            conn.execute("""
                INSERT INTO agent_xp_history
                    (agent_id, run_id, xp_gained, xp_breakdown, quality_score,
                     items_processed, items_total, findings_count, messages_sent,
                     status, level_before, level_after, leveled_up)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (agent_id, run_id or f"run_{int(time.time())}",
                  xp_gained, json.dumps(breakdown), quality_score,
                  result.stats.processed, result.stats.total,
                  len(result.findings), result.messages_sent,
                  result.status, old_level, new_level, int(leveled_up)))

            conn.commit()

            return {
                "agent_id": agent_id,
                "xp_gained": xp_gained,
                "total_xp": new_xp,
                "level_before": old_level,
                "level_after": new_level,
                "leveled_up": leveled_up,
                "unlocked_capabilities": unlocked_str,
                "breakdown": breakdown,
            }

        finally:
            conn.close()

    def get_level(self, agent_id: str) -> Dict:
        """Get an agent's current level and capabilities."""
        conn = _connect(self.db_path)
        try:
            row = conn.execute(
                "SELECT * FROM agent_xp WHERE agent_id = ?",
                (agent_id,)
            ).fetchone()
            if row is None:
                return {
                    "agent_id": agent_id,
                    "level": 1, "total_xp": 0,
                    "unlocked_capabilities": "basic",
                    "runs_completed": 0,
                }
            return dict(row)
        finally:
            conn.close()

    def get_leaderboard(self, limit: int = 20) -> List[Dict]:
        """Get top agents by XP."""
        conn = _connect(self.db_path)
        try:
            rows = conn.execute("""
                SELECT agent_id, total_xp, level, runs_completed,
                       runs_success, best_quality, avg_quality,
                       unlocked_capabilities
                FROM agent_xp
                ORDER BY total_xp DESC
                LIMIT ?
            """, (limit,)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_history(self, agent_id: str, limit: int = 10) -> List[Dict]:
        """Get recent XP history for an agent."""
        conn = _connect(self.db_path)
        try:
            rows = conn.execute("""
                SELECT * FROM agent_xp_history
                WHERE agent_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (agent_id, limit)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def has_capability(self, agent_id: str, capability: str) -> bool:
        """Check if an agent has unlocked a specific capability."""
        info = self.get_level(agent_id)
        caps = info.get("unlocked_capabilities", "basic").split(",")
        return capability in caps

    def get_fleet_stats(self) -> Dict:
        """Get fleet-wide XP statistics."""
        conn = _connect(self.db_path)
        try:
            row = conn.execute("""
                SELECT
                    COUNT(*) as total_agents,
                    SUM(total_xp) as fleet_xp,
                    AVG(level) as avg_level,
                    MAX(level) as max_level,
                    SUM(runs_completed) as total_runs,
                    SUM(runs_success) as total_successes,
                    AVG(avg_quality) as fleet_avg_quality,
                    MAX(best_quality) as fleet_best_quality,
                    SUM(total_findings) as fleet_findings
                FROM agent_xp
            """).fetchone()
            return dict(row) if row else {}
        finally:
            conn.close()

    def print_leaderboard(self, limit: int = 20) -> str:
        """Format a text leaderboard."""
        board = self.get_leaderboard(limit)
        if not board:
            return "No agents have earned XP yet."

        lines = ["╔══════════════════════════════════════════════════════════════╗"]
        lines.append("║           AGENT FLEET LEADERBOARD — XP RANKINGS            ║")
        lines.append("╠══════════════════════════════════════════════════════════════╣")
        lines.append("║ Rank │ Agent ID        │ Level │ XP      │ Runs │ Quality  ║")
        lines.append("╠══════════════════════════════════════════════════════════════╣")

        for i, agent in enumerate(board, 1):
            rank = f"{i:>4}"
            aid = f"{agent['agent_id']:<15}"[:15]
            lvl = f"{agent['level']:>5}"
            xp = f"{agent['total_xp']:>7}"
            runs = f"{agent['runs_completed']:>4}"
            qual = f"{agent['avg_quality']:>7.2f}" if agent['avg_quality'] else "   N/A"
            lines.append(f"║ {rank} │ {aid} │ {lvl} │ {xp} │ {runs} │ {qual}  ║")

        lines.append("╚══════════════════════════════════════════════════════════════╝")

        stats = self.get_fleet_stats()
        if stats.get("total_agents"):
            lines.append(f"\nFleet: {stats['total_agents']} agents │ "
                         f"{stats['fleet_xp'] or 0} total XP │ "
                         f"Avg Level {stats['avg_level']:.1f} │ "
                         f"Max Level {stats['max_level']} │ "
                         f"{stats['total_runs'] or 0} runs")

        return "\n".join(lines)


# Convenience function for orchestrator integration
def grant_xp_for_result(result: AgentResult, run_id: str = None) -> Dict:
    """One-liner XP grant — call from orchestrator after any agent completes."""
    xp = AgentXP()
    return xp.grant_xp(result, run_id)
