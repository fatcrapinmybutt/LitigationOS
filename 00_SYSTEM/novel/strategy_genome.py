"""
NOVEL Engine — Strategy Genome
Each legal strategy has DNA encoding its arguments, authorities, evidence links,
risk factors, and Michigan-specific procedural requirements. Strategies evolve
through adversarial pressure, judicial outcome feedback, and cross-breeding.
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
LITIGATION_DB = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")

# ─── Michigan Court Hierarchy ─────────────────────────────────────────────
MICHIGAN_COURTS = {
    "60th_district": {"level": 1, "name": "60th District Court", "judge": "Kostrzewa, Raymond J., Jr."},
    "14th_circuit_family": {"level": 2, "name": "14th Circuit Court, Family Division", "judge": "Hon. Jenny L. McNeill"},
    "14th_circuit_civil": {"level": 2, "name": "14th Circuit Court, Civil Division", "judge": "Hon. Kenneth Hoopes"},
    "michigan_coa": {"level": 3, "name": "Michigan Court of Appeals", "judge": None},
    "michigan_msc": {"level": 4, "name": "Michigan Supreme Court", "judge": None},
    "usdc_wdmi": {"level": 5, "name": "US District Court, Western District of Michigan", "judge": None},
    "jtc": {"level": 0, "name": "Judicial Tenure Commission", "judge": None},
}

# ─── Case Lanes ───────────────────────────────────────────────────────────
CASE_LANES = {
    "A": {"name": "Watson Custody", "case": "2024-001507-DC", "court": "14th_circuit_family", "meek": "MEEK2"},
    "B": {"name": "Shady Oaks Housing", "case": "2025-002760-CZ", "court": "14th_circuit_civil", "meek": "MEEK1"},
    "C": {"name": "Convergence", "case": "multi-lane", "court": "multiple", "meek": None},
    "D": {"name": "PPO/Protection", "case": "2023-5907-PP", "court": "14th_circuit_family", "meek": "MEEK3"},
    "E": {"name": "Judicial Misconduct", "case": "2024-001507-DC", "court": "jtc", "meek": "MEEK4"},
    "F": {"name": "Appellate", "case": "COA 366810", "court": "michigan_coa", "meek": "MEEK5"},
}

# ─── Legal Argument Archetypes ────────────────────────────────────────────
ARGUMENT_ARCHETYPES = [
    "due_process_violation", "equal_protection", "best_interest_child",
    "parental_fitness", "change_of_circumstances", "judicial_bias",
    "procedural_irregularity", "fraud_on_court", "ineffective_counsel",
    "self_defense", "brady_violation", "nonservice",
    "ex_parte_communication", "conflict_of_interest", "contempt",
    "parenting_time_interference", "relocation", "child_support_mod",
    "property_division", "housing_code_violation", "title_fraud",
    "retaliatory_prosecution", "malicious_prosecution", "abuse_of_process",
    "section_1983", "section_1985_conspiracy", "rooker_feldman_exception",
    "extraordinary_writ", "superintending_control", "mandamus",
]

# ─── Michigan Authority Categories ────────────────────────────────────────
AUTHORITY_TYPES = [
    "mcl_statute", "mcr_court_rule", "michigan_coa_case",
    "michigan_msc_case", "federal_statute", "federal_case",
    "constitution_michigan", "constitution_federal", "secondary_authority",
]

# ─── Forbidden Hallucination Patterns ─────────────────────────────────────
FORBIDDEN_PATTERNS = [
    "Jane Berry", "Patricia Berry", "91% alienation", "Tiffany Watson",
    "Lincoln David Watson", "Ron Berry Esq", "Amy McNeill",
    "Emily Ann", "Emily M.", "P35878",
]


@dataclass
class StrategyGenome:
    """The DNA of a legal strategy — everything that defines an argument."""

    # ── Identity ──
    strategy_id: str = ""
    name: str = ""
    description: str = ""
    lane: str = "A"
    court: str = "14th_circuit_family"
    filing_type: str = "motion"

    # ── Argument Core ──
    primary_argument: str = ""
    secondary_arguments: list = field(default_factory=list)
    archetypes: list = field(default_factory=list)
    legal_standard: str = ""
    burden_of_proof: str = "preponderance"

    # ── Authority Chain ──
    primary_authorities: list = field(default_factory=list)
    supporting_authorities: list = field(default_factory=list)
    distinguishing_authorities: list = field(default_factory=list)
    mcr_rules: list = field(default_factory=list)
    mcl_statutes: list = field(default_factory=list)

    # ── Evidence Bindings ──
    evidence_atoms: list = field(default_factory=list)
    exhibit_refs: list = field(default_factory=list)
    affidavit_paragraphs: list = field(default_factory=list)
    chronology_anchors: list = field(default_factory=list)

    # ── Risk Assessment ──
    strength_score: float = 0.5
    risk_score: float = 0.5
    novelty_score: float = 0.5
    judicial_reception: float = 0.5
    opposing_vulnerability: float = 0.5

    # ── Adversarial Intelligence ──
    anticipated_objections: list = field(default_factory=list)
    counter_arguments: list = field(default_factory=list)
    opposing_authorities: list = field(default_factory=list)
    worst_case_scenario: str = ""
    adversary_weakness: str = ""

    # ── Procedural Requirements ──
    required_forms: list = field(default_factory=list)
    service_requirements: list = field(default_factory=list)
    filing_deadlines: list = field(default_factory=list)
    prerequisites: list = field(default_factory=list)
    proposed_order_needed: bool = True

    # ── Michigan-Specific ──
    best_interest_factors: list = field(default_factory=list)
    custody_factors_impacted: list = field(default_factory=list)
    mcl_722_23_factors: dict = field(default_factory=dict)
    friend_of_court_role: str = ""

    # ── Evolution Metadata ──
    generation: int = 0
    parent_ids: list = field(default_factory=list)
    mutation_history: list = field(default_factory=list)
    fitness_score: float = 0.5
    win_count: int = 0
    loss_count: int = 0
    total_deployments: int = 0
    created_at: str = ""
    evolved_at: str = ""
    status: str = "active"

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.evolved_at:
            self.evolved_at = self.created_at

    @property
    def win_rate(self) -> float:
        total = self.win_count + self.loss_count
        return self.win_count / total if total > 0 else 0.5

    @property
    def composite_fitness(self) -> float:
        """Multi-factor fitness: strength, evidence support, authority depth, win record."""
        weights = {
            "strength": 0.20,
            "evidence": 0.20,
            "authority": 0.20,
            "win_rate": 0.25,
            "risk_inv": 0.15,
        }
        evidence_depth = min(len(self.evidence_atoms) / 10.0, 1.0)
        authority_depth = min(len(self.primary_authorities) / 5.0, 1.0)
        risk_inverse = 1.0 - self.risk_score

        return (
            weights["strength"] * self.strength_score
            + weights["evidence"] * evidence_depth
            + weights["authority"] * authority_depth
            + weights["win_rate"] * self.win_rate
            + weights["risk_inv"] * risk_inverse
        )

    @property
    def genome_hash(self) -> str:
        core = f"{self.primary_argument}|{'|'.join(sorted(self.archetypes))}|{'|'.join(sorted(self.mcr_rules))}"
        return hashlib.sha256(core.encode()).hexdigest()[:12]

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "StrategyGenome":
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in d.items() if k in valid_fields}
        return cls(**filtered)

    def validate(self) -> list:
        """Check genome for hallucinations and missing requirements."""
        issues = []
        full_text = json.dumps(self.to_dict()).lower()
        for pattern in FORBIDDEN_PATTERNS:
            if pattern.lower() in full_text:
                issues.append(f"HALLUCINATION: '{pattern}' found in strategy")

        if not self.primary_authorities:
            issues.append("NO_AUTHORITY: No primary authorities cited")
        if not self.evidence_atoms:
            issues.append("NO_EVIDENCE: No evidence atoms linked")
        if self.lane not in CASE_LANES:
            issues.append(f"INVALID_LANE: Lane '{self.lane}' not in valid lanes")
        if self.court not in MICHIGAN_COURTS:
            issues.append(f"INVALID_COURT: Court '{self.court}' not recognized")
        if not self.primary_argument:
            issues.append("NO_ARGUMENT: Primary argument is empty")
        if self.filing_type == "motion" and not self.mcr_rules:
            issues.append("NO_MCR: Motion filed without MCR rule citation")
        return issues


@dataclass
class AdversaryProfile:
    """Model of opposing party's likely strategy and behavior patterns."""

    adversary_id: str = "emily_watson"
    name: str = "Emily A. Watson"
    attorney: str = "Pro Se (Jennifer Barnes P55406 WITHDREW)"
    known_tactics: list = field(default_factory=lambda: [
        "false_allegations_abuse",
        "parenting_time_withholding",
        "ppo_weaponization",
        "court_system_manipulation",
        "third_party_proxy_litigation",
    ])
    historical_arguments: list = field(default_factory=list)
    weakness_profile: dict = field(default_factory=lambda: {
        "credibility": 0.3,
        "procedural_compliance": 0.4,
        "evidence_strength": 0.3,
        "consistency": 0.2,
    })
    ally_network: list = field(default_factory=lambda: [
        {"name": "Ronald Berry", "role": "domestic_partner", "bar_number": None},
        {"name": "Albert Watson", "role": "father", "address": "1143 E Norton Ave"},
        {"name": "Lori Watson", "role": "mother", "address": "1143 E Norton Ave"},
    ])
    judicial_advantage: dict = field(default_factory=lambda: {
        "mcneill_conflict": True,
        "berry_connection": True,
        "hoopes_conflict": True,
    })


@dataclass
class JudicialProfile:
    """Model of judge's tendencies, biases, and decision patterns."""

    judge_id: str = ""
    name: str = ""
    court: str = ""
    known_biases: list = field(default_factory=list)
    ruling_patterns: dict = field(default_factory=dict)
    receptive_arguments: list = field(default_factory=list)
    hostile_to: list = field(default_factory=list)
    disqualification_grounds: list = field(default_factory=list)
    conflict_score: float = 0.0

    @classmethod
    def mcneill(cls) -> "JudicialProfile":
        return cls(
            judge_id="mcneill",
            name="Hon. Jenny L. McNeill",
            court="14th_circuit_family",
            known_biases=["pro_respondent", "anti_pro_se", "berry_connection"],
            ruling_patterns={
                "custody_modifications": "rarely_grants_to_father",
                "parenting_time": "restrictive",
                "contempt": "selective_enforcement",
                "evidentiary_hearings": "frequently_denied",
            },
            receptive_arguments=["procedural_compliance", "foc_recommendation"],
            hostile_to=["judicial_bias_claims", "pro_se_motions", "recusal_requests"],
            disqualification_grounds=[
                "MCR 2.003(C)(1)(b) — personal bias or prejudice",
                "Berry domestic partner connection to judicial family",
                "Partner at Ladas, Hoopes & McNeill law firm",
                "Pattern of one-sided rulings against father",
            ],
            conflict_score=0.95,
        )

    @classmethod
    def hoopes(cls) -> "JudicialProfile":
        return cls(
            judge_id="hoopes",
            name="Hon. Kenneth Hoopes",
            court="14th_circuit_civil",
            known_biases=["same_firm_as_mcneill"],
            ruling_patterns={"dismissals": "granted_without_hearing"},
            disqualification_grounds=[
                "Chief Judge from same Ladas, Hoopes & McNeill firm",
                "Cannot impartially reassign after McNeill disqualification",
                "Entire 14th Circuit compromised",
            ],
            conflict_score=0.90,
        )

    @classmethod
    def ladas_hoopes(cls) -> "JudicialProfile":
        return cls(
            judge_id="ladas_hoopes",
            name="Hon. Maria Ladas-Hoopes",
            court="60th_district",
            known_biases=["married_to_chief_judge"],
            ruling_patterns={"evictions": "granted_ignoring_evidence"},
            disqualification_grounds=[
                "Wife of Chief Judge Kenneth Hoopes",
                "Same Ladas, Hoopes & McNeill firm origin",
                "Evicted plaintiff while ignoring housing violation evidence",
            ],
            conflict_score=0.90,
        )


class StrategyDB:
    """SQLite persistence for strategy genomes and evolution tracking."""

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
                CREATE TABLE IF NOT EXISTS strategies (
                    strategy_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    lane TEXT DEFAULT 'A',
                    court TEXT DEFAULT '14th_circuit_family',
                    filing_type TEXT DEFAULT 'motion',
                    generation INTEGER DEFAULT 0,
                    fitness_score REAL DEFAULT 0.5,
                    status TEXT DEFAULT 'active',
                    genome_json TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now')),
                    evolved_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS strategy_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    description TEXT,
                    old_fitness REAL,
                    new_fitness REAL,
                    genome_snapshot TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS battle_outcomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_id TEXT NOT NULL,
                    battle_type TEXT NOT NULL,
                    opponent_id TEXT,
                    outcome TEXT NOT NULL,
                    score_delta REAL DEFAULT 0.0,
                    notes TEXT,
                    court TEXT,
                    judge_id TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS authority_chains (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chain_id TEXT UNIQUE NOT NULL,
                    strategy_id TEXT,
                    authorities TEXT NOT NULL,
                    chain_type TEXT DEFAULT 'supporting',
                    strength REAL DEFAULT 0.5,
                    validated INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS adversary_intel (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    adversary_id TEXT NOT NULL,
                    intel_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT,
                    confidence REAL DEFAULT 0.5,
                    lane TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS evolution_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cycle_number INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    details TEXT,
                    strategies_evolved INTEGER DEFAULT 0,
                    strategies_spawned INTEGER DEFAULT 0,
                    strategies_culled INTEGER DEFAULT 0,
                    best_fitness REAL DEFAULT 0.0,
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS judicial_profiles (
                    judge_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    court TEXT,
                    profile_json TEXT NOT NULL,
                    conflict_score REAL DEFAULT 0.0,
                    updated_at TEXT DEFAULT (datetime('now'))
                );

                CREATE INDEX IF NOT EXISTS idx_strategies_lane ON strategies(lane);
                CREATE INDEX IF NOT EXISTS idx_strategies_fitness ON strategies(fitness_score DESC);
                CREATE INDEX IF NOT EXISTS idx_strategies_status ON strategies(status);
                CREATE INDEX IF NOT EXISTS idx_battles_strategy ON battle_outcomes(strategy_id);
                CREATE INDEX IF NOT EXISTS idx_authority_strategy ON authority_chains(strategy_id);
            """)

    def save_strategy(self, genome: StrategyGenome):
        with self._conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO strategies
                (strategy_id, name, lane, court, filing_type, generation,
                 fitness_score, status, genome_json, created_at, evolved_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                genome.strategy_id, genome.name, genome.lane, genome.court,
                genome.filing_type, genome.generation, genome.composite_fitness,
                genome.status, json.dumps(genome.to_dict()), genome.created_at,
                genome.evolved_at,
            ))

    def load_strategy(self, strategy_id: str) -> Optional[StrategyGenome]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT genome_json FROM strategies WHERE strategy_id = ?",
                (strategy_id,)
            ).fetchone()
            if row:
                return StrategyGenome.from_dict(json.loads(row["genome_json"]))
        return None

    def get_all_strategies(self, lane: str = None, status: str = "active") -> list:
        with self._conn() as conn:
            if lane:
                rows = conn.execute(
                    "SELECT genome_json FROM strategies WHERE lane = ? AND status = ? ORDER BY fitness_score DESC",
                    (lane, status)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT genome_json FROM strategies WHERE status = ? ORDER BY fitness_score DESC",
                    (status,)
                ).fetchall()
            return [StrategyGenome.from_dict(json.loads(r["genome_json"])) for r in rows]

    def get_top_strategies(self, n: int = 10) -> list:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT genome_json FROM strategies WHERE status = 'active' ORDER BY fitness_score DESC LIMIT ?",
                (n,)
            ).fetchall()
            return [StrategyGenome.from_dict(json.loads(r["genome_json"])) for r in rows]

    def record_battle(self, strategy_id: str, battle_type: str, outcome: str,
                      opponent_id: str = None, score_delta: float = 0.0,
                      notes: str = "", court: str = "", judge_id: str = ""):
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO battle_outcomes
                (strategy_id, battle_type, opponent_id, outcome, score_delta, notes, court, judge_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (strategy_id, battle_type, opponent_id, outcome, score_delta, notes, court, judge_id))

    def record_evolution(self, cycle: int, event_type: str, details: str = "",
                         evolved: int = 0, spawned: int = 0, culled: int = 0, best: float = 0.0):
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO evolution_log
                (cycle_number, event_type, details, strategies_evolved, strategies_spawned, strategies_culled, best_fitness)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (cycle, event_type, details, evolved, spawned, culled, best))

    def save_judicial_profile(self, profile: JudicialProfile):
        with self._conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO judicial_profiles (judge_id, name, court, profile_json, conflict_score, updated_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (profile.judge_id, profile.name, profile.court,
                  json.dumps(asdict(profile)), profile.conflict_score))

    def save_adversary_intel(self, adversary_id: str, intel_type: str,
                             content: str, source: str = "", confidence: float = 0.5, lane: str = ""):
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO adversary_intel (adversary_id, intel_type, content, source, confidence, lane)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (adversary_id, intel_type, content, source, confidence, lane))

    def get_stats(self) -> dict:
        with self._conn() as conn:
            row = conn.execute("""
                SELECT
                    (SELECT COUNT(*) FROM strategies WHERE status='active') as active_strategies,
                    (SELECT COUNT(*) FROM strategies) as total_strategies,
                    (SELECT MAX(generation) FROM strategies) as max_generation,
                    (SELECT AVG(fitness_score) FROM strategies WHERE status='active') as avg_fitness,
                    (SELECT MAX(fitness_score) FROM strategies) as max_fitness,
                    (SELECT COUNT(*) FROM battle_outcomes) as total_battles,
                    (SELECT COUNT(*) FROM authority_chains) as total_chains,
                    (SELECT COUNT(*) FROM adversary_intel) as total_intel,
                    (SELECT COUNT(*) FROM evolution_log) as total_evolutions,
                    (SELECT COUNT(*) FROM judicial_profiles) as total_profiles
            """).fetchone()
            return dict(row)


def build_seed_strategies() -> list:
    """Generate the initial strategy population from Michigan litigation knowledge."""
    seeds = []

    # ── Lane A: Custody Restoration ──
    seeds.append(StrategyGenome(
        strategy_id="custody-pt-restoration",
        name="Emergency Parenting Time Restoration",
        description="Restore parenting time after 363+ day wrongful suspension",
        lane="A", court="14th_circuit_family", filing_type="motion",
        primary_argument="Child's best interest requires immediate restoration of parenting time after 363+ days of wrongful suspension without evidentiary hearing",
        secondary_arguments=[
            "No finding of unfitness under MCL 722.25",
            "Due process violation — no hearing before suspension",
            "Established custodial environment disrupted without clear and convincing evidence",
        ],
        archetypes=["best_interest_child", "due_process_violation", "parenting_time_interference"],
        legal_standard="Best interest of the child — MCL 722.23",
        burden_of_proof="preponderance",
        mcr_rules=["MCR 3.206", "MCR 3.210", "MCR 2.119"],
        mcl_statutes=["MCL 722.23", "MCL 722.25", "MCL 722.27", "MCL 722.27a"],
        primary_authorities=["Shade v Wright 291 Mich App 17 (2010)", "Vodvarka v Grasmeyer 259 Mich App 499 (2003)"],
        best_interest_factors=["a", "b", "c", "d", "f", "j", "k", "l"],
        strength_score=0.8, risk_score=0.3,
    ))

    # ── Lane A: MCR 2.003 Disqualification ──
    seeds.append(StrategyGenome(
        strategy_id="mcr-2003-disqualification",
        name="Judicial Disqualification — Berry-McNeill Conflict",
        description="Disqualify Judge McNeill under MCR 2.003 based on Berry connection",
        lane="A", court="14th_circuit_family", filing_type="motion",
        primary_argument="Judge McNeill must be disqualified under MCR 2.003(C)(1)(b) due to undisclosed personal relationship between Ronald Berry (defendant's domestic partner) and McNeill's professional network from Ladas, Hoopes & McNeill law firm",
        secondary_arguments=[
            "Appearance of impropriety under Canon 2",
            "Pattern of one-sided rulings demonstrating actual bias",
            "Failure to disclose conflict sua sponte",
        ],
        archetypes=["judicial_bias", "conflict_of_interest", "due_process_violation"],
        legal_standard="MCR 2.003(C)(1) — disqualification for cause",
        mcr_rules=["MCR 2.003"],
        mcl_statutes=["MCL 600.1401"],
        primary_authorities=[
            "Cain v Michigan Dept of Corrections 451 Mich 470 (1996)",
            "Caperton v AT Massey Coal 556 US 868 (2009)",
        ],
        strength_score=0.85, risk_score=0.4,
        anticipated_objections=["Untimely filing", "Insufficient evidence of actual bias", "Mere disagreement with rulings"],
        counter_arguments=[
            "Bias discovered through Berry connection — not mere disagreement",
            "Structural conflict from shared law firm origin cannot be waived",
            "Due process requires disqualification when objective observer would question impartiality",
        ],
    ))

    # ── Lane B: Shady Oaks Complaint ──
    seeds.append(StrategyGenome(
        strategy_id="shady-oaks-complaint",
        name="Shady Oaks Housing Complaint",
        description="Civil complaint for housing code violations, illegal lockout, title fraud",
        lane="B", court="14th_circuit_civil", filing_type="complaint",
        primary_argument="Defendants violated Michigan Housing Law through illegal lockout, habitability failures, water shutoff, and title manipulation at mobile home park",
        archetypes=["housing_code_violation", "title_fraud", "fraud_on_court"],
        mcl_statutes=["MCL 600.2918", "MCL 125.534", "MCL 554.139"],
        strength_score=0.75, risk_score=0.35,
    ))

    # ── Lane D: PPO Vacatur ──
    seeds.append(StrategyGenome(
        strategy_id="ppo-vacatur",
        name="PPO Vacatur — Weaponized Protection Order",
        description="Vacate PPO obtained through fraud and used as custody weapon",
        lane="D", court="14th_circuit_family", filing_type="motion",
        primary_argument="PPO was obtained through misrepresentation and has been weaponized to deny father all parenting time — constituting abuse of process",
        archetypes=["abuse_of_process", "fraud_on_court", "due_process_violation"],
        mcr_rules=["MCR 3.707", "MCR 3.708"],
        mcl_statutes=["MCL 600.2950", "MCL 600.2950a"],
        strength_score=0.70, risk_score=0.45,
    ))

    # ── Lane E: JTC Complaint ──
    seeds.append(StrategyGenome(
        strategy_id="jtc-complaint-mcneill",
        name="JTC Complaint — McNeill Misconduct",
        description="Judicial Tenure Commission complaint for McNeill's pattern of misconduct",
        lane="E", court="jtc", filing_type="complaint",
        primary_argument="Judge McNeill has engaged in a pattern of judicial misconduct including undisclosed conflicts, ex parte communications, denial of due process, and biased rulings that warrant investigation by the Judicial Tenure Commission",
        archetypes=["judicial_bias", "conflict_of_interest", "ex_parte_communication"],
        primary_authorities=["Const 1963 Art 6 Sec 30", "MCR 9.104", "MCR 9.116"],
        strength_score=0.70, risk_score=0.50,
    ))

    # ── Lane F: COA Appeal ──
    seeds.append(StrategyGenome(
        strategy_id="coa-appeal-366810",
        name="COA Appeal — Custody Order",
        description="Appeal custody order to Michigan Court of Appeals",
        lane="F", court="michigan_coa", filing_type="brief",
        primary_argument="Trial court abused its discretion by modifying custody without proper evidentiary hearing, applying incorrect legal standard, and failing to consider all best interest factors",
        archetypes=["due_process_violation", "best_interest_child", "procedural_irregularity"],
        mcr_rules=["MCR 7.212", "MCR 7.215"],
        primary_authorities=["Pierron v Pierron 486 Mich 81 (2010)", "Dailey v Kloenhamer 291 Mich App 660 (2011)"],
        strength_score=0.65, risk_score=0.55,
    ))

    # ── Lane C: Federal §1983 ──
    seeds.append(StrategyGenome(
        strategy_id="federal-1983",
        name="Federal §1983 — Due Process Violation",
        description="Federal civil rights complaint for systematic due process violations",
        lane="C", court="usdc_wdmi", filing_type="complaint",
        primary_argument="State actors systematically deprived plaintiff of constitutionally protected parental rights without due process of law, constituting a §1983 violation",
        archetypes=["section_1983", "due_process_violation", "equal_protection"],
        mcl_statutes=["42 USC 1983", "42 USC 1985"],
        primary_authorities=[
            "Troxel v Granville 530 US 57 (2000)",
            "Santosky v Kramer 455 US 745 (1982)",
        ],
        strength_score=0.55, risk_score=0.65,
        anticipated_objections=["Rooker-Feldman doctrine", "Judicial immunity", "Younger abstention"],
    ))

    # ── Lane A: Contempt for PT Denial ──
    seeds.append(StrategyGenome(
        strategy_id="contempt-pt-denial",
        name="Contempt — Parenting Time Denial",
        description="Show cause for contempt based on systematic parenting time denial",
        lane="A", court="14th_circuit_family", filing_type="motion",
        primary_argument="Defendant is in contempt of court orders by systematically denying all parenting time for 363+ consecutive days without court authorization",
        archetypes=["contempt", "parenting_time_interference"],
        mcr_rules=["MCR 3.606"],
        mcl_statutes=["MCL 722.27a", "MCL 600.1701"],
        strength_score=0.80, risk_score=0.25,
    ))

    return seeds
