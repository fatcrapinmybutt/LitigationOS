"""
NOVEL Engine — Invention Genome
The DNA of an invention: what it solves, how it works, what it produces,
and how it evolves. Every invention starts as a genome that can mutate,
crossbreed, and spawn into a fully operational system component.
"""

import os
import sys
import json
import sqlite3
import hashlib
import random
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional

os.environ["PYTHONUTF8"] = "1"

DB_PATH = Path(__file__).parent / "novel.db"
REPO_ROOT = Path(r"C:\Users\andre\LitigationOS")

# ─── What NOVEL can invent ────────────────────────────────────────────────
INVENTION_TYPES = {
    "agent":    {"ext": ".agent.md", "dir": REPO_ROOT / ".agents" / "agents", "desc": "Autonomous agent definition"},
    "skill":    {"ext": "SKILL.md",  "dir": REPO_ROOT / ".agents" / "skills", "desc": "Reusable skill module"},
    "tool":     {"ext": ".py",       "dir": REPO_ROOT / "00_SYSTEM" / "tools", "desc": "Python CLI tool"},
    "workflow": {"ext": ".py",       "dir": REPO_ROOT / "00_SYSTEM" / "pipeline", "desc": "Multi-step pipeline workflow"},
    "template": {"ext": ".md",       "dir": REPO_ROOT / "01_FILINGS" / "TEMPLATES", "desc": "Court filing template"},
    "engine":   {"ext": ".py",       "dir": REPO_ROOT / "00_SYSTEM", "desc": "Core system engine"},
    "mcp_tool": {"ext": ".py",       "dir": REPO_ROOT / "00_SYSTEM" / "mcp_server", "desc": "MCP server tool"},
    "analysis": {"ext": ".py",       "dir": REPO_ROOT / "00_SYSTEM" / "tools", "desc": "Analysis/intelligence module"},
    "db_schema":{"ext": ".sql",      "dir": REPO_ROOT / "databases", "desc": "Database schema or migration"},
    "integration": {"ext": ".py",    "dir": REPO_ROOT / "00_SYSTEM" / "tools", "desc": "Cross-system integration"},
}

# ─── Problem domains NOVEL understands ────────────────────────────────────
PROBLEM_DOMAINS = [
    "evidence_processing", "filing_generation", "legal_research",
    "judicial_analysis", "deadline_management", "document_conversion",
    "deduplication", "organization", "search_retrieval", "ocr_extraction",
    "contradiction_detection", "authority_validation", "citation_verification",
    "narrative_construction", "chronology_building", "exhibit_management",
    "service_tracking", "compliance_auditing", "adversarial_analysis",
    "pattern_recognition", "gap_detection", "quality_assurance",
    "cross_lane_convergence", "court_form_intelligence", "workflow_automation",
    "agent_orchestration", "memory_management", "system_health",
    "performance_optimization", "security_hardening",
]

# ─── Technique library (building blocks for inventions) ───────────────────
TECHNIQUE_LIBRARY = {
    "nlp": ["tfidf", "bm25", "regex_patterns", "keyword_extraction", "entity_recognition", "sentiment_analysis"],
    "ml": ["naive_bayes", "decision_tree", "clustering", "anomaly_detection", "similarity_scoring"],
    "search": ["fts5", "trigram", "fuzzy_match", "semantic_search", "graph_traversal", "bfs_dfs"],
    "data": ["sqlite_wal", "json_streaming", "csv_batch", "pandas_transform", "schema_migration"],
    "document": ["pdf_extraction", "docx_generation", "markdown_parse", "ocr_pipeline", "bates_stamping"],
    "graph": ["neo4j_export", "networkx", "adjacency_list", "topological_sort", "centrality_analysis"],
    "automation": ["queue_processing", "event_driven", "cron_scheduling", "watchdog_monitoring", "webhook"],
    "quality": ["checksum_verify", "schema_validate", "hallucination_detect", "regression_test", "fuzzing"],
    "evolution": ["genetic_algorithm", "simulated_annealing", "hill_climbing", "particle_swarm", "differential_evolution"],
}


@dataclass
class InventionGenome:
    """The DNA of an invention — a blueprint that can be prototyped, tested, and evolved."""

    # ── Identity ──
    invention_id: str = ""
    name: str = ""
    codename: str = ""
    invention_type: str = "tool"
    version: str = "0.1.0"

    # ── Problem Definition ──
    problem_statement: str = ""
    domains: list = field(default_factory=list)
    gap_source: str = ""
    urgency: float = 0.5
    impact: float = 0.5

    # ── Solution Design ──
    approach: str = ""
    techniques: list = field(default_factory=list)
    inputs: list = field(default_factory=list)
    outputs: list = field(default_factory=list)
    dependencies: list = field(default_factory=list)
    architecture: str = ""

    # ── Code Blueprint ──
    entry_point: str = ""
    classes: list = field(default_factory=list)
    functions: list = field(default_factory=list)
    cli_commands: list = field(default_factory=list)
    db_tables: list = field(default_factory=list)
    config_params: dict = field(default_factory=dict)

    # ── Quality Gates ──
    acceptance_criteria: list = field(default_factory=list)
    test_cases: list = field(default_factory=list)
    anti_patterns: list = field(default_factory=list)
    security_constraints: list = field(default_factory=list)

    # ── Lineage ──
    inspiration_sources: list = field(default_factory=list)
    parent_ids: list = field(default_factory=list)
    generation: int = 0
    mutation_log: list = field(default_factory=list)

    # ── Fitness ──
    fitness_score: float = 0.0
    novelty_score: float = 0.5
    utility_score: float = 0.5
    elegance_score: float = 0.5
    reliability_score: float = 0.0
    test_pass_rate: float = 0.0
    deployments: int = 0
    failures: int = 0
    validation_score: float = 0.0
    validation_errors: int = 0

    # ── Status ──
    status: str = "concept"  # concept → designed → prototyped → tested → deployed → evolved → archived
    prototype_path: str = ""
    created_at: str = ""
    evolved_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.evolved_at:
            self.evolved_at = self.created_at
        if not self.invention_id:
            self.invention_id = self._generate_id()

    def _generate_id(self) -> str:
        seed = f"{self.name}|{self.invention_type}|{datetime.now().isoformat()}"
        return hashlib.sha256(seed.encode()).hexdigest()[:12]

    @property
    def composite_fitness(self) -> float:
        """Weighted fitness across all dimensions."""
        if self.status == "concept":
            return (self.novelty_score * 0.4 + self.utility_score * 0.4 + self.urgency * 0.2)
        return (
            self.utility_score * 0.25
            + self.reliability_score * 0.25
            + self.novelty_score * 0.15
            + self.elegance_score * 0.10
            + self.test_pass_rate * 0.15
            + (1.0 - (self.failures / max(self.deployments, 1))) * 0.10
        )

    @property
    def readiness(self) -> str:
        """How close to deployment."""
        if not self.problem_statement:
            return "needs_problem"
        if not self.approach:
            return "needs_design"
        if not self.functions and not self.classes:
            return "needs_blueprint"
        if not self.prototype_path:
            return "needs_prototype"
        if self.test_pass_rate < 0.5:
            return "needs_testing"
        return "deploy_ready"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "InventionGenome":
        valid = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in d.items() if k in valid})

    def mutate(self, mutation_type: str = "random") -> "InventionGenome":
        """Create a mutated copy of this invention."""
        import copy
        child = copy.deepcopy(self)
        child.generation += 1
        child.parent_ids = [self.invention_id]
        child.status = "concept"
        child.invention_id = child._generate_id()
        child.created_at = datetime.now().isoformat()
        child.evolved_at = child.created_at
        child.deployments = 0
        child.failures = 0

        if mutation_type == "technique_swap":
            if child.techniques and TECHNIQUE_LIBRARY:
                category = random.choice(list(TECHNIQUE_LIBRARY.keys()))
                new_tech = random.choice(TECHNIQUE_LIBRARY[category])
                if new_tech not in child.techniques:
                    old = random.choice(child.techniques) if child.techniques else None
                    if old:
                        child.techniques.remove(old)
                    child.techniques.append(new_tech)
                    child.mutation_log.append(f"technique_swap: {old} → {new_tech}")

        elif mutation_type == "domain_expand":
            available = [d for d in PROBLEM_DOMAINS if d not in child.domains]
            if available:
                new_domain = random.choice(available)
                child.domains.append(new_domain)
                child.mutation_log.append(f"domain_expand: +{new_domain}")

        elif mutation_type == "architecture_shift":
            shifts = ["add_caching", "add_parallelism", "add_streaming", "add_retry_logic",
                       "add_checkpoint", "add_validation_layer", "switch_to_async"]
            shift = random.choice(shifts)
            child.architecture += f" | MUTATION: {shift}"
            child.mutation_log.append(f"architecture_shift: {shift}")

        elif mutation_type == "random":
            mutations = ["technique_swap", "domain_expand", "architecture_shift"]
            return self.mutate(random.choice(mutations))

        return child

    @staticmethod
    def crossbreed(parent_a: "InventionGenome", parent_b: "InventionGenome") -> "InventionGenome":
        """Combine two inventions into a hybrid offspring."""
        child = InventionGenome(
            name=f"{parent_a.name.split()[0]}-{parent_b.name.split()[-1]}-Hybrid",
            codename=f"HYBRID-{parent_a.invention_id[:4]}-{parent_b.invention_id[:4]}",
            invention_type=parent_a.invention_type if parent_a.composite_fitness >= parent_b.composite_fitness else parent_b.invention_type,
            problem_statement=f"Hybrid: {parent_a.problem_statement} + {parent_b.problem_statement}",
            domains=list(set(parent_a.domains + parent_b.domains)),
            approach=f"Combined approach: [{parent_a.approach}] ∪ [{parent_b.approach}]",
            techniques=list(set(parent_a.techniques + parent_b.techniques)),
            inputs=list(set(parent_a.inputs + parent_b.inputs)),
            outputs=list(set(parent_a.outputs + parent_b.outputs)),
            dependencies=list(set(parent_a.dependencies + parent_b.dependencies)),
            classes=parent_a.classes + parent_b.classes,
            functions=list(set(parent_a.functions + parent_b.functions)),
            acceptance_criteria=list(set(parent_a.acceptance_criteria + parent_b.acceptance_criteria)),
            inspiration_sources=[parent_a.invention_id, parent_b.invention_id],
            parent_ids=[parent_a.invention_id, parent_b.invention_id],
            generation=max(parent_a.generation, parent_b.generation) + 1,
            novelty_score=(parent_a.novelty_score + parent_b.novelty_score) / 2 + 0.1,
            utility_score=max(parent_a.utility_score, parent_b.utility_score),
            urgency=max(parent_a.urgency, parent_b.urgency),
            impact=max(parent_a.impact, parent_b.impact),
        )
        child.mutation_log.append(f"crossbreed: {parent_a.invention_id} × {parent_b.invention_id}")
        return child


class InventionDB:
    """Persistence layer for the invention ecosystem."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=60)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("PRAGMA cache_size=-32000")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS inventions (
                    invention_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    codename TEXT,
                    invention_type TEXT NOT NULL,
                    status TEXT DEFAULT 'concept',
                    generation INTEGER DEFAULT 0,
                    fitness_score REAL DEFAULT 0.0,
                    novelty_score REAL DEFAULT 0.5,
                    utility_score REAL DEFAULT 0.5,
                    domains TEXT,
                    prototype_path TEXT,
                    genome_json TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now')),
                    evolved_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS invention_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invention_id TEXT NOT NULL,
                    event TEXT NOT NULL,
                    details TEXT,
                    old_status TEXT,
                    new_status TEXT,
                    fitness_delta REAL DEFAULT 0.0,
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS gap_registry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    gap_id TEXT UNIQUE NOT NULL,
                    domain TEXT NOT NULL,
                    description TEXT NOT NULL,
                    severity REAL DEFAULT 0.5,
                    detected_by TEXT,
                    addressed_by TEXT,
                    status TEXT DEFAULT 'open',
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS technique_outcomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    technique TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    invention_id TEXT,
                    outcome TEXT NOT NULL,
                    effectiveness REAL DEFAULT 0.5,
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS spawn_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    parent_id TEXT,
                    child_id TEXT NOT NULL,
                    spawn_type TEXT NOT NULL,
                    spawn_method TEXT,
                    output_path TEXT,
                    success INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS evolution_cycles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cycle_number INTEGER NOT NULL,
                    inventions_scanned INTEGER DEFAULT 0,
                    gaps_found INTEGER DEFAULT 0,
                    ideas_generated INTEGER DEFAULT 0,
                    prototypes_built INTEGER DEFAULT 0,
                    mutations INTEGER DEFAULT 0,
                    crossbreeds INTEGER DEFAULT 0,
                    promotions INTEGER DEFAULT 0,
                    culled INTEGER DEFAULT 0,
                    best_fitness REAL DEFAULT 0.0,
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE INDEX IF NOT EXISTS idx_inv_type ON inventions(invention_type);
                CREATE INDEX IF NOT EXISTS idx_inv_status ON inventions(status);
                CREATE INDEX IF NOT EXISTS idx_inv_fitness ON inventions(fitness_score DESC);
                CREATE INDEX IF NOT EXISTS idx_gaps_status ON gap_registry(status);
                CREATE INDEX IF NOT EXISTS idx_gaps_domain ON gap_registry(domain);
                CREATE INDEX IF NOT EXISTS idx_spawn_parent ON spawn_log(parent_id);
            """)

    def save(self, genome: InventionGenome):
        with self._conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO inventions
                (invention_id, name, codename, invention_type, status, generation,
                 fitness_score, novelty_score, utility_score, domains,
                 prototype_path, genome_json, created_at, evolved_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                genome.invention_id, genome.name, genome.codename,
                genome.invention_type, genome.status, genome.generation,
                genome.composite_fitness, genome.novelty_score, genome.utility_score,
                json.dumps(genome.domains), genome.prototype_path,
                json.dumps(genome.to_dict()), genome.created_at, genome.evolved_at,
            ))

    def load(self, invention_id: str) -> Optional[InventionGenome]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT genome_json FROM inventions WHERE invention_id = ?", (invention_id,)
            ).fetchone()
            if row:
                return InventionGenome.from_dict(json.loads(row["genome_json"]))
        return None

    def get_all(self, status: str = None, inv_type: str = None) -> list:
        with self._conn() as conn:
            query = "SELECT genome_json FROM inventions WHERE 1=1"
            params = []
            if status:
                query += " AND status = ?"
                params.append(status)
            if inv_type:
                query += " AND invention_type = ?"
                params.append(inv_type)
            query += " ORDER BY fitness_score DESC"
            rows = conn.execute(query, params).fetchall()
            return [InventionGenome.from_dict(json.loads(r["genome_json"])) for r in rows]

    def register_gap(self, gap_id: str, domain: str, description: str,
                     severity: float = 0.5, detected_by: str = "novel_scan"):
        with self._conn() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO gap_registry (gap_id, domain, description, severity, detected_by)
                VALUES (?, ?, ?, ?, ?)
            """, (gap_id, domain, description, severity, detected_by))

    def get_open_gaps(self, domain: str = None) -> list:
        with self._conn() as conn:
            if domain:
                rows = conn.execute(
                    "SELECT * FROM gap_registry WHERE status = 'open' AND domain = ? ORDER BY severity DESC",
                    (domain,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM gap_registry WHERE status = 'open' ORDER BY severity DESC"
                ).fetchall()
            return [dict(r) for r in rows]

    def record_spawn(self, parent_id: str, child_id: str, spawn_type: str,
                     method: str = "", output_path: str = "", success: bool = True):
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO spawn_log (parent_id, child_id, spawn_type, spawn_method, output_path, success)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (parent_id, child_id, spawn_type, method, output_path, int(success)))

    def record_technique(self, technique: str, domain: str, invention_id: str,
                         outcome: str, effectiveness: float = 0.5):
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO technique_outcomes (technique, domain, invention_id, outcome, effectiveness)
                VALUES (?, ?, ?, ?, ?)
            """, (technique, domain, invention_id, outcome, effectiveness))

    def get_best_techniques(self, domain: str, limit: int = 5) -> list:
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT technique, AVG(effectiveness) as avg_eff, COUNT(*) as uses
                FROM technique_outcomes WHERE domain = ?
                GROUP BY technique ORDER BY avg_eff DESC LIMIT ?
            """, (domain, limit)).fetchall()
            return [dict(r) for r in rows]

    def record_cycle(self, cycle: int, scanned: int = 0, gaps: int = 0,
                     ideas: int = 0, prototypes: int = 0, mutations: int = 0,
                     crossbreeds: int = 0, promotions: int = 0, culled: int = 0,
                     best_fitness: float = 0.0):
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO evolution_cycles
                (cycle_number, inventions_scanned, gaps_found, ideas_generated,
                 prototypes_built, mutations, crossbreeds, promotions, culled, best_fitness)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (cycle, scanned, gaps, ideas, prototypes, mutations, crossbreeds, promotions, culled, best_fitness))

    def get_stats(self) -> dict:
        with self._conn() as conn:
            row = conn.execute("""
                SELECT
                    (SELECT COUNT(*) FROM inventions) as total_inventions,
                    (SELECT COUNT(*) FROM inventions WHERE status='concept') as concepts,
                    (SELECT COUNT(*) FROM inventions WHERE status='designed') as designed,
                    (SELECT COUNT(*) FROM inventions WHERE status='prototyped') as prototyped,
                    (SELECT COUNT(*) FROM inventions WHERE status='tested') as tested,
                    (SELECT COUNT(*) FROM inventions WHERE status='deployed') as deployed,
                    (SELECT COUNT(*) FROM inventions WHERE status='evolved') as evolved,
                    (SELECT MAX(generation) FROM inventions) as max_generation,
                    (SELECT AVG(fitness_score) FROM inventions) as avg_fitness,
                    (SELECT MAX(fitness_score) FROM inventions) as best_fitness,
                    (SELECT COUNT(*) FROM gap_registry WHERE status='open') as open_gaps,
                    (SELECT COUNT(*) FROM gap_registry) as total_gaps,
                    (SELECT COUNT(*) FROM spawn_log) as total_spawns,
                    (SELECT COUNT(*) FROM spawn_log WHERE success=1) as successful_spawns,
                    (SELECT COUNT(*) FROM technique_outcomes) as technique_trials,
                    (SELECT COUNT(*) FROM evolution_cycles) as evolution_cycles
            """).fetchone()
            return dict(row)
