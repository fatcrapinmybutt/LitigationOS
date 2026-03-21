"""
DELTA9 Agent Models — Data classes, error types, and shared state.
MAX LEVEL 9999++ OMEGA — Every agent uses these.

v2.0 OMEGA Upgrades:
  - QualityScore: per-agent output quality assessment
  - PlanStep: Plan-and-Execute pattern support
  - AgentMessage: inter-agent communication bus
  - Enhanced AgentResult with quality scoring + plan history
  - RetryableError for transient failures with backoff hints

v3.0 OMEGA Upgrades:
  - HealthReport: structured fleet-readable health status
  - ProvenanceEntry: immutable provenance chain record
  - EvidenceScore: multi-dimensional evidence scoring
  - LaneDetection: lane classification result with confidence
  - FleetStatus: aggregated fleet health snapshot
  - ValidationResult: output validation with issues list
"""
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


class SkipItemError(Exception):
    """Raised when an item should be skipped (not fatal)."""
    pass


class FatalAgentError(Exception):
    """Raised when agent must abort entirely."""
    pass


class LaneCrossContaminationError(SkipItemError):
    """Raised when evidence from wrong case lane detected — skip item, not fatal."""
    pass


class RetryableError(Exception):
    """Raised for transient failures that should be retried with backoff.
    Includes retry hints so the caller can make intelligent decisions."""
    def __init__(self, message: str, suggested_wait: float = 2.0,
                 max_retries: int = 3):
        super().__init__(message)
        self.suggested_wait = suggested_wait
        self.max_retries = max_retries


@dataclass
class QualityScore:
    """Per-agent output quality assessment — enables self-evaluation.
    Each dimension is 0.0-1.0. Overall is the weighted mean."""
    completeness: float = 0.0   # Did the agent process all items?
    accuracy: float = 0.0       # Error rate inverse (1.0 = zero errors)
    throughput: float = 0.0     # Items/sec relative to agent's historical avg
    coverage: float = 0.0       # How much of the input domain was touched?

    @property
    def overall(self) -> float:
        weights = {'completeness': 0.35, 'accuracy': 0.35,
                   'throughput': 0.15, 'coverage': 0.15}
        return (self.completeness * weights['completeness'] +
                self.accuracy * weights['accuracy'] +
                self.throughput * weights['throughput'] +
                self.coverage * weights['coverage'])

    def __str__(self) -> str:
        return (f"Q={self.overall:.2f} "
                f"[comp={self.completeness:.2f} acc={self.accuracy:.2f} "
                f"thr={self.throughput:.2f} cov={self.coverage:.2f}]")


@dataclass
class PlanStep:
    """Single step in a Plan-and-Execute strategy.
    Agents can decompose complex tasks into ordered steps,
    execute them, and replan based on results."""
    step_id: str
    description: str
    status: str = "pending"     # pending, running, done, failed, skipped
    tool_name: str = ""         # Which tool to invoke
    tool_args: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    error: Optional[str] = None
    depends_on: List[str] = field(default_factory=list)
    elapsed: float = 0.0

    @property
    def is_ready(self) -> bool:
        return self.status == "pending" and not self.depends_on

    def __str__(self) -> str:
        return f"[{self.status}] {self.step_id}: {self.description[:60]}"


@dataclass
class AgentMessage:
    """Inter-agent communication message for the message bus.
    Enables agents to share findings, request work, or signal events."""
    sender: str
    recipient: str           # Agent ID or "*" for broadcast
    msg_type: str            # "finding", "request", "signal", "handoff"
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: int = 5        # 1 (highest) to 10 (lowest)
    timestamp: float = field(default_factory=time.time)

    def __str__(self) -> str:
        return f"[{self.msg_type}] {self.sender}→{self.recipient}: {str(self.payload)[:80]}"


@dataclass
class AgentStats:
    total: int = 0
    processed: int = 0
    skipped: int = 0
    errored: int = 0
    start_time: float = field(default_factory=time.time)
    peak_memory_mb: float = 0.0
    retry_count: int = 0

    @property
    def elapsed(self) -> float:
        return time.time() - self.start_time

    @property
    def rate(self) -> float:
        return self.processed / max(self.elapsed, 0.001)

    @property
    def error_rate(self) -> float:
        done = self.processed + self.skipped + self.errored
        return self.errored / max(done, 1)

    @property
    def success_rate(self) -> float:
        done = self.processed + self.skipped + self.errored
        return self.processed / max(done, 1)

    def __str__(self) -> str:
        return (f"[{self.processed}/{self.total} done, {self.skipped} skip, "
                f"{self.errored} err, {self.elapsed:.1f}s]")


@dataclass
class AgentResult:
    agent_id: str
    status: str  # SUCCESS, FATAL, CRASH, PARTIAL
    stats: AgentStats
    error: Optional[str] = None
    quality: Optional[QualityScore] = None
    plan_history: List[PlanStep] = field(default_factory=list)
    findings: List[Dict[str, Any]] = field(default_factory=list)
    messages_sent: int = 0

    def __str__(self) -> str:
        q = f" {self.quality}" if self.quality else ""
        return f"{self.agent_id}: {self.status} {self.stats}{q}"


# ═══════════════════════════════════════════
# v3.0 OMEGA DATA CLASSES
# ═══════════════════════════════════════════

@dataclass
class HealthReport:
    """Structured health report for fleet monitoring.
    Every agent can report its health in a fleet-readable format."""
    agent_id: str
    status: str              # healthy, degraded, failing, dead
    uptime_seconds: float = 0.0
    items_processed: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    memory_mb: float = 0.0
    db_connected: bool = False
    lane: str = "U"          # Which case lane (A-F or U=unclassified)
    capabilities: List[str] = field(default_factory=list)

    @property
    def health_score(self) -> float:
        """0.0 to 1.0 health score based on error rate and connectivity."""
        if self.status == "dead":
            return 0.0
        total = self.items_processed + self.error_count
        error_penalty = (self.error_count / max(total, 1)) * 0.5
        db_penalty = 0.0 if self.db_connected else 0.2
        base = {"healthy": 1.0, "degraded": 0.7, "failing": 0.3}.get(self.status, 0.5)
        return max(0.0, base - error_penalty - db_penalty)

    def __str__(self) -> str:
        return f"{self.agent_id}: {self.status} (score={self.health_score:.2f}, items={self.items_processed})"


@dataclass
class ProvenanceEntry:
    """Immutable provenance chain record — links outputs to their source inputs.
    Every generated artifact (filing, analysis, score) MUST have provenance."""
    output_type: str         # filing, analysis, score, classification, timeline
    output_id: str           # Unique identifier for the output
    inputs: List[Dict[str, str]] = field(default_factory=list)  # [{type, id, path}]
    agent_id: str = ""
    timestamp: float = field(default_factory=time.time)

    def __str__(self) -> str:
        return f"[{self.output_type}] {self.output_id} ← {len(self.inputs)} inputs"


@dataclass
class EvidenceScore:
    """Multi-dimensional evidence scoring result.
    Rates evidence on relevance, admissibility, and impact."""
    relevance: float = 0.0      # 0-1: How relevant to the claim?
    admissibility: float = 0.0  # 0-1: Will court admit it? (MRE compliance)
    impact: float = 0.0         # 0-1: How much does it help the case?
    evidence_type: str = ""     # document, testimony, photo, record, digital
    claim_type: str = ""        # custody, misconduct, housing, ppo, appeal, civil_rights
    mre_issues: List[str] = field(default_factory=list)  # MRE rules that may exclude
    notes: str = ""

    @property
    def composite(self) -> float:
        """Weighted composite score. Admissibility gates everything."""
        if self.admissibility < 0.3:
            return self.admissibility * 0.5  # Inadmissible = near-zero value
        return (self.relevance * 0.35 + self.admissibility * 0.35 + self.impact * 0.30)

    def __str__(self) -> str:
        return (f"Evidence[{self.evidence_type}→{self.claim_type}]: "
                f"composite={self.composite:.2f} (rel={self.relevance:.2f} "
                f"adm={self.admissibility:.2f} imp={self.impact:.2f})")


@dataclass
class LaneDetection:
    """Lane classification result with confidence scoring.
    Maps evidence/documents to one of 6 case lanes."""
    lane: str = "U"           # A, B, C, D, E, F, or U (unclassified)
    confidence: float = 0.0   # 0-1: How confident in the classification?
    signals_found: List[str] = field(default_factory=list)
    signal_counts: Dict[str, int] = field(default_factory=dict)  # {lane: count}

    @property
    def is_confident(self) -> bool:
        return self.confidence >= 0.6

    def __str__(self) -> str:
        return f"Lane={self.lane} (conf={self.confidence:.2f}, signals={len(self.signals_found)})"


@dataclass
class FleetStatus:
    """Aggregated fleet health snapshot for orchestrator monitoring."""
    total_agents: int = 0
    healthy: int = 0
    degraded: int = 0
    failing: int = 0
    dead: int = 0
    total_items_processed: int = 0
    total_errors: int = 0
    reports: List[HealthReport] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    @property
    def fleet_health(self) -> float:
        if self.total_agents == 0:
            return 0.0
        return sum(r.health_score for r in self.reports) / self.total_agents

    def __str__(self) -> str:
        return (f"Fleet: {self.total_agents} agents, health={self.fleet_health:.2f} "
                f"({self.healthy}✓ {self.degraded}~ {self.failing}! {self.dead}✗)")


@dataclass
class ValidationResult:
    """Output validation result with detailed issue tracking.
    Used by guard_output() and validate_output() in Agent9999 v3.0."""
    is_valid: bool = True
    issues: List[str] = field(default_factory=list)
    corrections_made: int = 0
    hallucinations_caught: int = 0
    original_text: str = ""
    corrected_text: str = ""

    def __str__(self) -> str:
        status = "VALID" if self.is_valid else f"INVALID ({len(self.issues)} issues)"
        return f"Validation: {status}, {self.corrections_made} corrections, {self.hallucinations_caught} hallucinations caught"


# Lane definitions (IRON LAW — never mix)
LANE_A_SIGNALS = {
    'custody', 'parenting', 'foc', 'child', 'mcl 722', 'mcr 3.206',
    'mcr 3.207', 'mcr 3.210', 'best interest', 'watson', 'mcneill',
    'rusco', 'ppo', 'contempt', 'mcl 600.2950', 'mcr 3.606',
    'mcr 3.707', 'mcr 3.708', '2024-001507', '2023-5907'
}

LANE_B_SIGNALS = {
    'shady oaks', 'homes of america', 'alden', 'habitability',
    'mcl 554', 'landlord', 'tenant', 'mobile home park',
    'mcl 445.903', 'consumer protection', 'warranty of habitability',
    'hoopes', '2025-002760', 'security deposit', 'mcl 600.5720'
}

LANE_C_SIGNALS = {
    'muskegon county', '14th circuit', 'judicial misconduct',
    'jtc', 'canon', 'disqualification', 'mcr 2.003', 'mcr 9.200',
    '42 usc', '1983', '1985', 'monell', 'civil rights', 'bias',
    'ex parte', 'pattern', 'systemic'
}

LANE_D_SIGNALS = {
    'ppo', 'protection order', 'personal protection', 'contempt',
    'bond violation', 'no contact', 'stalking', 'harassment order',
    'mcl 600.2950', 'mcr 3.706', 'mcr 3.707', 'mcr 3.708',
    'restrain', 'enforce order', 'modify ppo', 'violate order',
    'domestic violence', 'threat', 'intimidation',
}

LANE_E_SIGNALS = {
    'bias', 'prejudice', 'impartial', 'recusal', 'disqualification',
    'jtc', 'judicial tenure', 'judicial misconduct', 'canon',
    'mcr 2.003', 'mcr 9.200', 'ex parte', 'improper communication',
    'mcneill bias', 'mcneill misconduct', 'mcneill violation',
    'code of conduct', 'appearance of impropriety', 'unilateral',
    'pattern of bias', 'systemic misconduct',
}

LANE_F_SIGNALS = {
    'appeal', 'leave to appeal', 'interlocutory', 'appellate',
    'court of appeals', 'coa', 'supreme court', 'msc',
    'mcr 7.201', 'mcr 7.203', 'mcr 7.205', 'mcr 7.301',
    'mcr 7.303', 'mcr 7.305', 'standard of review',
    'de novo', 'abuse of discretion', 'clearly erroneous',
    'peremptory', 'superintending control', 'original action',
    'brief on appeal', 'appendix', 'claim of appeal',
}

# File categories
LEGAL_EXTENSIONS = {'.pdf', '.md', '.txt', '.docx', '.doc', '.rtf'}
DATA_EXTENSIONS = {'.json', '.jsonl', '.csv', '.xlsx', '.tsv'}
CODE_EXTENSIONS = {'.py', '.js', '.ts', '.html', '.css', '.ps1', '.bat', '.sh'}
ARCHIVE_EXTENSIONS = {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'}
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.tiff', '.bmp', '.webp'}

SKIP_DIRS = {
    '__pycache__', '.git', 'node_modules', '.vscode', '.idea',
    'java-1.8.0-openjdk-1.8.0.302-1.b08.redhat.windows.x86_64',
    'tesseract-main', 'czkawka-master', '.tox', '.mypy_cache',
    'venv', '.env', 'dist', 'build'
}

SKIP_EXTENSIONS = {'.pyc', '.pyo', '.class', '.dll', '.exe', '.obj', '.o',
                   '.so', '.dylib', '.h', '.qml', '.typed', '.lombok'}

# Canonical priority (higher = preferred)
CANONICAL_PRIORITY = {
    'LitigationOS': 100,
    'COURT_FILINGS_FINAL': 95,
    'COURT_PACKETS': 90,
    '01_CASE_FILES': 85,
    '02_EVIDENCE': 80,
    '03_LEGAL_AUTHORITIES': 75,
    'SCANNED_EVIDENCE': 70,
    'PIGORS_CASE_MASTER': 65,
    'extracts_full': 60,
    'discovery': 50,
    'CAPSTONE': 45,
    'ALL_PC_EVIDENCE_EXTRACTED': 40,
    'Documents': 35,
    'CANONICAL_ROOT_H': 30,
}

# Master index DB path
MASTER_INDEX_DB = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\agents\master_index.db")
CHECKPOINT_DIR = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\agents\checkpoints")
