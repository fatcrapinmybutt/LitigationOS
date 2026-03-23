"""
DARWIN Engine — Agent Genome
Each agent has a "genome" that encodes its capabilities, prompt patterns,
and learned behaviors. Genomes evolve through mutation and crossbreeding.
"""

import sys
import os
import json
import hashlib
import sqlite3
import random
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional

os.environ["PYTHONUTF8"] = "1"

DB_PATH = Path(__file__).parent / "darwin.db"


@dataclass
class AgentGenome:
    """The DNA of an agent — everything that defines its behavior."""
    agent_id: str
    name: str
    generation: int = 0
    parent_ids: list = field(default_factory=list)

    # Core behavioral genes
    system_prompt: str = ""
    role_description: str = ""
    expertise_domains: list = field(default_factory=list)
    omega_skills: list = field(default_factory=list)

    # Capability genes (0.0 to 1.0 weights)
    evidence_weight: float = 0.5
    filing_weight: float = 0.5
    research_weight: float = 0.5
    investigation_weight: float = 0.5
    qa_weight: float = 0.5
    strategy_weight: float = 0.5

    # Anti-hallucination genes (learned constraints)
    forbidden_patterns: list = field(default_factory=list)
    required_verifications: list = field(default_factory=list)
    citation_strictness: float = 0.8

    # Court-specific genes
    court_formats: list = field(default_factory=list)
    mcr_rules_known: list = field(default_factory=list)
    jurisdiction: str = "Michigan"

    # Performance metrics (updated after each task)
    fitness_score: float = 0.0
    tasks_completed: int = 0
    tasks_failed: int = 0
    avg_quality: float = 0.0
    avg_completeness: float = 0.0
    avg_accuracy: float = 0.0
    hallucination_count: int = 0

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_evolved: str = field(default_factory=lambda: datetime.now().isoformat())
    genome_hash: str = ""

    def compute_hash(self) -> str:
        """Deterministic hash of behavioral genes (not performance metrics)."""
        behavioral = {
            "system_prompt": self.system_prompt,
            "role_description": self.role_description,
            "expertise_domains": sorted(self.expertise_domains),
            "omega_skills": sorted(self.omega_skills),
            "evidence_weight": self.evidence_weight,
            "filing_weight": self.filing_weight,
            "research_weight": self.research_weight,
            "investigation_weight": self.investigation_weight,
            "qa_weight": self.qa_weight,
            "strategy_weight": self.strategy_weight,
            "forbidden_patterns": sorted(self.forbidden_patterns),
            "citation_strictness": self.citation_strictness,
        }
        raw = json.dumps(behavioral, sort_keys=True)
        self.genome_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return self.genome_hash

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> "AgentGenome":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    @classmethod
    def from_json(cls, raw: str) -> "AgentGenome":
        return cls.from_dict(json.loads(raw))

    @classmethod
    def from_agent_md(cls, agent_id: str, md_path: Path) -> "AgentGenome":
        """Bootstrap a genome from an existing agent markdown definition."""
        content = md_path.read_text(encoding="utf-8", errors="replace")
        genome = cls(
            agent_id=agent_id,
            name=agent_id.replace("-", " ").title(),
            system_prompt=content[:2000],
            role_description=content[:500],
        )

        # Extract domains from content keywords
        domain_keywords = {
            "evidence": ["evidence", "exhibit", "authentication", "bates"],
            "filing": ["motion", "brief", "filing", "complaint", "petition"],
            "research": ["research", "case law", "MCL", "MCR", "precedent"],
            "investigation": ["investigation", "pattern", "conspiracy", "surveillance"],
            "custody": ["custody", "parenting", "child", "best interest"],
            "judicial": ["judge", "judicial", "misconduct", "recusal", "JTC"],
        }

        content_lower = content.lower()
        for domain, keywords in domain_keywords.items():
            if any(kw in content_lower for kw in keywords):
                genome.expertise_domains.append(domain)

        # Adjust weights based on detected domains
        if "evidence" in genome.expertise_domains:
            genome.evidence_weight = 0.8
        if "filing" in genome.expertise_domains:
            genome.filing_weight = 0.8
        if "research" in genome.expertise_domains:
            genome.research_weight = 0.8
        if "investigation" in genome.expertise_domains:
            genome.investigation_weight = 0.8

        # Default anti-hallucination genes
        genome.forbidden_patterns = [
            "Jane Berry", "Patricia Berry", "91% alienation",
            "Tiffany Watson", "Lincoln David Watson", "Ron Berry Esq",
        ]
        genome.required_verifications = [
            "party_names", "case_numbers", "bar_numbers", "statistics",
        ]

        genome.compute_hash()
        return genome


class GenomeDB:
    """Persistent storage for agent genomes using SQLite."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=60000")
            conn.execute("PRAGMA cache_size=-32000")
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS genomes (
                    agent_id TEXT PRIMARY KEY,
                    generation INTEGER DEFAULT 0,
                    genome_json TEXT NOT NULL,
                    fitness_score REAL DEFAULT 0.0,
                    tasks_completed INTEGER DEFAULT 0,
                    tasks_failed INTEGER DEFAULT 0,
                    avg_quality REAL DEFAULT 0.0,
                    hallucination_count INTEGER DEFAULT 0,
                    genome_hash TEXT,
                    created_at TEXT,
                    last_evolved TEXT,
                    is_active INTEGER DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS genome_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    generation INTEGER,
                    genome_json TEXT NOT NULL,
                    fitness_score REAL,
                    event_type TEXT,
                    event_detail TEXT,
                    timestamp TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS task_outcomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    task_id TEXT,
                    task_type TEXT,
                    quality_score REAL,
                    completeness_score REAL,
                    accuracy_score REAL,
                    hallucination_detected INTEGER DEFAULT 0,
                    placeholder_count INTEGER DEFAULT 0,
                    citation_accuracy REAL,
                    output_length INTEGER,
                    execution_time_s REAL,
                    outcome TEXT,
                    notes TEXT,
                    timestamp TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS evolution_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT,
                    parent_ids TEXT,
                    child_id TEXT,
                    mutation_type TEXT,
                    detail TEXT,
                    timestamp TEXT DEFAULT (datetime('now'))
                );

                CREATE INDEX IF NOT EXISTS idx_outcomes_agent
                    ON task_outcomes(agent_id);
                CREATE INDEX IF NOT EXISTS idx_outcomes_quality
                    ON task_outcomes(quality_score);
                CREATE INDEX IF NOT EXISTS idx_history_agent
                    ON genome_history(agent_id, generation);
            """)

    def save_genome(self, genome: AgentGenome):
        genome.compute_hash()
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("PRAGMA busy_timeout=60000")
            conn.execute("""
                INSERT OR REPLACE INTO genomes
                (agent_id, generation, genome_json, fitness_score, tasks_completed,
                 tasks_failed, avg_quality, hallucination_count, genome_hash,
                 created_at, last_evolved, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                genome.agent_id, genome.generation, genome.to_json(),
                genome.fitness_score, genome.tasks_completed, genome.tasks_failed,
                genome.avg_quality, genome.hallucination_count, genome.genome_hash,
                genome.created_at, genome.last_evolved,
            ))
            # Archive to history
            conn.execute("""
                INSERT INTO genome_history
                (agent_id, generation, genome_json, fitness_score, event_type)
                VALUES (?, ?, ?, ?, 'save')
            """, (genome.agent_id, genome.generation, genome.to_json(), genome.fitness_score))

    def load_genome(self, agent_id: str) -> Optional[AgentGenome]:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("PRAGMA busy_timeout=60000")
            row = conn.execute(
                "SELECT genome_json FROM genomes WHERE agent_id = ? AND is_active = 1",
                (agent_id,)
            ).fetchone()
            if row:
                return AgentGenome.from_json(row[0])
        return None

    def get_top_performers(self, n: int = 10, domain: str = None) -> list:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("PRAGMA busy_timeout=60000")
            if domain:
                rows = conn.execute("""
                    SELECT genome_json FROM genomes
                    WHERE is_active = 1 AND genome_json LIKE ?
                    ORDER BY fitness_score DESC LIMIT ?
                """, (f'%"{domain}"%', n)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT genome_json FROM genomes
                    WHERE is_active = 1
                    ORDER BY fitness_score DESC LIMIT ?
                """, (n,)).fetchall()
            return [AgentGenome.from_json(r[0]) for r in rows]

    def get_all_active(self) -> list:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("PRAGMA busy_timeout=60000")
            rows = conn.execute(
                "SELECT genome_json FROM genomes WHERE is_active = 1"
            ).fetchall()
            return [AgentGenome.from_json(r[0]) for r in rows]

    def record_outcome(self, agent_id: str, task_id: str, task_type: str,
                       quality: float, completeness: float, accuracy: float,
                       hallucination: bool = False, placeholders: int = 0,
                       citation_accuracy: float = 1.0, output_length: int = 0,
                       execution_time: float = 0.0, notes: str = ""):
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("PRAGMA busy_timeout=60000")
            conn.execute("""
                INSERT INTO task_outcomes
                (agent_id, task_id, task_type, quality_score, completeness_score,
                 accuracy_score, hallucination_detected, placeholder_count,
                 citation_accuracy, output_length, execution_time_s, outcome, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                agent_id, task_id, task_type, quality, completeness, accuracy,
                1 if hallucination else 0, placeholders, citation_accuracy,
                output_length, execution_time,
                "success" if quality >= 0.7 else "needs_improvement", notes,
            ))

    def get_agent_stats(self, agent_id: str) -> dict:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("PRAGMA busy_timeout=60000")
            row = conn.execute("""
                SELECT
                    COUNT(*) as total_tasks,
                    AVG(quality_score) as avg_quality,
                    AVG(completeness_score) as avg_completeness,
                    AVG(accuracy_score) as avg_accuracy,
                    SUM(hallucination_detected) as total_hallucinations,
                    AVG(placeholder_count) as avg_placeholders,
                    AVG(citation_accuracy) as avg_citation_accuracy,
                    AVG(execution_time_s) as avg_execution_time
                FROM task_outcomes WHERE agent_id = ?
            """, (agent_id,)).fetchone()
            if row and row[0] > 0:
                return {
                    "total_tasks": row[0],
                    "avg_quality": round(row[1] or 0, 3),
                    "avg_completeness": round(row[2] or 0, 3),
                    "avg_accuracy": round(row[3] or 0, 3),
                    "total_hallucinations": row[4] or 0,
                    "avg_placeholders": round(row[5] or 0, 1),
                    "avg_citation_accuracy": round(row[6] or 0, 3),
                    "avg_execution_time": round(row[7] or 0, 1),
                }
            return {"total_tasks": 0}

    def fleet_dashboard(self) -> str:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("PRAGMA busy_timeout=60000")
            rows = conn.execute("""
                SELECT agent_id, generation, fitness_score, tasks_completed,
                       tasks_failed, avg_quality, hallucination_count
                FROM genomes WHERE is_active = 1
                ORDER BY fitness_score DESC
            """).fetchall()

        lines = [
            "╔══════════════════════════════════════════════════════════════╗",
            "║              DARWIN FLEET FITNESS DASHBOARD                  ║",
            "╠══════════════════════════════════════════════════════════════╣",
            f"║  Total Active Agents: {len(rows):<38}║",
            "╠══════════════════════════════════════════════════════════════╣",
            "║  Agent ID              │ Gen │ Fitness │ Tasks │ Quality    ║",
            "╠════════════════════════╪═════╪═════════╪═══════╪════════════╣",
        ]

        for row in rows[:20]:
            aid = row[0][:22].ljust(22)
            gen = str(row[1]).center(3)
            fit = f"{row[2]:.2f}".center(7)
            tasks = str(row[3]).center(5)
            qual = f"{row[5]:.2f}".center(10) if row[5] else "  N/A   "
            lines.append(f"║  {aid} │ {gen} │ {fit} │ {tasks} │ {qual} ║")

        lines.append("╚══════════════════════════════════════════════════════════════╝")
        return "\n".join(lines)


if __name__ == "__main__":
    db = GenomeDB()
    print("DARWIN GenomeDB initialized at:", DB_PATH)
    print("Tables created. Ready for genome registration.")
