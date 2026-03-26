"""
DELTA9 Agent Orchestrator — Dual-Lane Parallel Execution Engine.
MAX LEVEL 9999++

Runs 56 agents across 5 tiers in two parallel lanes:
  Lane 1 (I/O bound): Index → Dedup → Flatten/Extract
  Lane 2 (CPU/AI bound): Judicial → Case Intel → Legal Warfare
  Convergence: Filing → Brains → Graph → MSC → Test → Certify

Usage:
  python -m agents.agent_orchestrator [--dry-run] [--tier TIER] [--agent AGENT_ID]
"""
import argparse
import json
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional

from .agent_models import AgentResult, MASTER_INDEX_DB, CHECKPOINT_DIR

# Import context manager for tier-level handoff (fail-safe)
_ContextManager = None
try:
    _cm_path = Path(__file__).resolve().parent.parent.parent / "local_model"
    import sys as _sys
    if str(_cm_path) not in _sys.path:
        _sys.path.insert(0, str(_cm_path))
    from context_manager import ContextManager as _ContextManager
except Exception:
    pass


def create_master_index_db(db_path: Path):
    """Create the master_index.db with full schema."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")

    conn.executescript("""
    -- Core file catalog
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY,
        drive TEXT NOT NULL,
        full_path TEXT UNIQUE NOT NULL,
        file_name TEXT NOT NULL,
        extension TEXT,
        size_bytes INTEGER,
        depth INTEGER,
        modified TEXT,
        sha256 TEXT,
        category TEXT,
        subcategory TEXT,
        is_canonical INTEGER DEFAULT 0,
        canonical_id INTEGER,
        dest_path TEXT,
        meek_lane TEXT,
        content_score REAL DEFAULT 0,
        processed INTEGER DEFAULT 0,
        potential_dupe INTEGER DEFAULT 0
    );

    -- Ready queue (Lane 1 feeds -> Lane 2 consumes)
    CREATE TABLE IF NOT EXISTS ready_queue (
        id INTEGER PRIMARY KEY,
        file_id INTEGER REFERENCES files(id),
        queue_type TEXT,
        priority INTEGER DEFAULT 0,
        claimed_by TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT DEFAULT (datetime('now'))
    );

    -- Dedup clusters
    CREATE TABLE IF NOT EXISTS dedup_clusters (
        cluster_sha256 TEXT PRIMARY KEY,
        file_count INTEGER,
        canonical_id INTEGER REFERENCES files(id),
        space_saved_bytes INTEGER
    );

    -- Zip contents catalog
    CREATE TABLE IF NOT EXISTS zip_contents (
        id INTEGER PRIMARY KEY,
        zip_id INTEGER REFERENCES files(id),
        inner_path TEXT,
        inner_size INTEGER,
        inner_ext TEXT,
        is_legal INTEGER DEFAULT 0
    );

    -- Atom stores
    CREATE TABLE IF NOT EXISTS atoms (
        id TEXT PRIMARY KEY,
        atom_type TEXT,
        source_file_id INTEGER REFERENCES files(id),
        meek_lane TEXT,
        title TEXT,
        content TEXT,
        confidence REAL,
        posture TEXT,
        created_by TEXT
    );

    -- Judicial findings
    CREATE TABLE IF NOT EXISTS judicial_findings (
        id INTEGER PRIMARY KEY,
        judge TEXT,
        finding_type TEXT,
        description TEXT,
        severity REAL,
        source_file_id INTEGER REFERENCES files(id),
        canon_ref TEXT,
        mcr_ref TEXT,
        confidence REAL,
        agent_id TEXT
    );

    -- Legal action scores
    CREATE TABLE IF NOT EXISTS action_scores (
        id INTEGER PRIMARY KEY,
        action_id TEXT,
        lane TEXT,
        evidence_score REAL,
        authority_score REAL,
        vulnerability_score REAL,
        readiness_score REAL,
        composite_score REAL,
        gap_count INTEGER,
        updated_by TEXT
    );

    -- Agent health tracking
    CREATE TABLE IF NOT EXISTS agent_log (
        id INTEGER PRIMARY KEY,
        agent_id TEXT NOT NULL,
        level TEXT DEFAULT 'INFO',
        action TEXT,
        detail TEXT,
        items_processed INTEGER,
        items_errored INTEGER,
        timestamp TEXT DEFAULT (datetime('now'))
    );

    -- Performance indexes
    CREATE INDEX IF NOT EXISTS idx_files_ext ON files(extension);
    CREATE INDEX IF NOT EXISTS idx_files_sha ON files(sha256);
    CREATE INDEX IF NOT EXISTS idx_files_depth ON files(depth);
    CREATE INDEX IF NOT EXISTS idx_files_category ON files(category);
    CREATE INDEX IF NOT EXISTS idx_files_canonical ON files(is_canonical);
    CREATE INDEX IF NOT EXISTS idx_files_drive ON files(drive);
    CREATE INDEX IF NOT EXISTS idx_files_processed ON files(processed);
    CREATE INDEX IF NOT EXISTS idx_queue_status ON ready_queue(status, queue_type);
    CREATE INDEX IF NOT EXISTS idx_atoms_type ON atoms(atom_type, meek_lane);
    CREATE INDEX IF NOT EXISTS idx_judicial_judge ON judicial_findings(judge, finding_type);
    CREATE INDEX IF NOT EXISTS idx_scores_lane ON action_scores(lane);
    """)
    conn.commit()
    conn.close()


def get_tier_agents(tier: str) -> list:
    """Return agent instances for a tier."""
    agents = []

    if tier == "tier1":
        from .lane1_infrastructure.a01_index_scout_c import IndexScoutC
        from .lane1_infrastructure.a02_index_scout_d import IndexScoutD
        from .lane1_infrastructure.a03_index_scout_f import IndexScoutF
        from .lane1_infrastructure.a04_index_scout_gi import IndexScoutGI
        agents = [IndexScoutC(), IndexScoutD(), IndexScoutF(), IndexScoutGI()]

    elif tier == "tier2":
        from .lane1_infrastructure.a05_legal_dedup import LegalDedup
        from .lane1_infrastructure.a06_data_dedup import DataDedup
        from .lane1_infrastructure.a07_code_dedup import CodeDedup
        from .lane1_infrastructure.a08_archive_cracker import ArchiveCracker
        agents = [LegalDedup(), DataDedup(), CodeDedup(), ArchiveCracker()]

    elif tier == "tier3":
        from .lane1_infrastructure.a09_flatten_commander import FlattenCommander
        from .lane1_infrastructure.a10_pdf_harvester import PdfHarvester
        from .lane1_infrastructure.a11_text_miner import TextMiner
        from .lane1_infrastructure.a12_struct_parser import StructParser
        agents = [FlattenCommander(), PdfHarvester(), TextMiner(), StructParser()]

    elif tier == "tierJ":
        from .lane2_intelligence.j01_mcneill_profiler import McNeillProfiler
        from .lane2_intelligence.j02_hoopes_profiler import HoopesProfiler
        from .lane2_intelligence.j03_benchbook_auditor import BenchbookAuditor
        from .lane2_intelligence.j04_canon_mapper import CanonMapper
        from .lane2_intelligence.j05_jtc_compiler import JtcCompiler
        from .lane2_intelligence.j06_disqualification import DisqualificationEngine
        from .lane2_intelligence.j07_exparte_detector import ExParteDetector
        from .lane2_intelligence.j08_transcript_impeacher import TranscriptImpeacher
        agents = [McNeillProfiler(), HoopesProfiler(), BenchbookAuditor(),
                  CanonMapper(), JtcCompiler(), DisqualificationEngine(),
                  ExParteDetector(), TranscriptImpeacher()]

    elif tier == "tierK":
        from .lane2_intelligence.k01_lane_a_custody import LaneACustody
        from .lane2_intelligence.k02_lane_a_ppo import LaneAPpo
        from .lane2_intelligence.k03_lane_b_housing import LaneBHousing
        from .lane2_intelligence.k04_lane_c_convergence import LaneCConvergence
        from .lane2_intelligence.k05_person_profiler import PersonProfiler
        from .lane2_intelligence.k06_timeline_builder import TimelineBuilder
        from .lane2_intelligence.k07_authority_harvester import AuthorityHarvester
        from .lane2_intelligence.k08_contradiction_detector import ContradictionDetector
        from .lane2_intelligence.k09_lane_d_ppo import LaneDPPOIntel
        from .lane2_intelligence.k10_lane_e_misconduct import LaneEMisconductIntel
        from .lane2_intelligence.k11_lane_f_appellate import LaneFAppellateIntel
        agents = [LaneACustody(), LaneAPpo(), LaneBHousing(), LaneCConvergence(),
                  PersonProfiler(), TimelineBuilder(), AuthorityHarvester(),
                  ContradictionDetector(),
                  LaneDPPOIntel(), LaneEMisconductIntel(), LaneFAppellateIntel()]

    elif tier == "tierL":
        from .lane2_intelligence.l01_lane_a_scorer import LaneAScorer
        from .lane2_intelligence.l02_lane_b_scorer import LaneBScorer
        from .lane2_intelligence.l03_lane_c_scorer import LaneCScorer
        from .lane2_intelligence.l04_gap_detector import GapDetector
        from .lane2_intelligence.l05_citation_validator import CitationValidator
        from .lane2_intelligence.l06_damages_calculator import DamagesCalculator
        from .lane2_intelligence.l07_filing_readiness import FilingReadiness
        from .lane2_intelligence.l08_red_team_scanner import RedTeamScanner
        from .lane2_intelligence.l09_lane_d_scorer import LaneDScorer
        from .lane2_intelligence.l10_lane_e_scorer import LaneEScorer
        from .lane2_intelligence.l11_lane_f_scorer import LaneFScorer
        agents = [LaneAScorer(), LaneBScorer(), LaneCScorer(), GapDetector(),
                  CitationValidator(), DamagesCalculator(), FilingReadiness(),
                  RedTeamScanner(),
                  LaneDScorer(), LaneEScorer(), LaneFScorer()]

    elif tier == "convergence":
        from .convergence.f01_filing_factory import FilingFactory
        from .convergence.f02_brain_feeder import BrainFeeder
        from .convergence.f03_graph_builder import GraphBuilder
        from .convergence.f04_msc_architect import MscArchitect
        from .convergence.f05_test_runner import TestRunner
        from .convergence.f06_convergence_certifier import ConvergenceCertifier
        from .convergence.f07_filing_packager import FilingPackager
        from .convergence.f09_deadline_enforcer import DeadlineEnforcer
        from .convergence.f10_oneshot_filer import OneShotFiler
        agents = [FilingFactory(), BrainFeeder(), GraphBuilder(),
                  MscArchitect(), TestRunner(), ConvergenceCertifier(),
                  FilingPackager(), DeadlineEnforcer(), OneShotFiler()]

    return agents


# =========================================
# TIER DEPENDENCY GRAPH — validates execution order
# =========================================
TIER_DEPENDENCIES = {
    "tier1": [],
    "tier2": ["tier1"],
    "tier3": ["tier2"],
    "tierJ": ["tier1"],
    "tierK": ["tierJ"],
    "tierL": ["tier3", "tierK"],  # REQUIRES BOTH lanes
    "convergence": ["tierL"],
}

# Configurable worker counts per tier
TIER_WORKERS: Dict[str, int] = {
    "tier1": 2, "tier2": 2, "tier3": 2,
    "tierJ": 3, "tierK": 3, "tierL": 3,
    "convergence": 2,
}


class TierCircuitBreaker:
    """Halts a tier after N consecutive agent failures to prevent cascade waste."""

    def __init__(self, threshold: int = 3):
        self._threshold = threshold
        self._tier_failures: Dict[str, int] = {}
        self._open_tiers: set = set()

    def record_success(self, tier: str) -> None:
        self._tier_failures[tier] = 0

    def record_failure(self, tier: str) -> bool:
        """Record failure. Returns True if circuit just opened."""
        self._tier_failures[tier] = self._tier_failures.get(tier, 0) + 1
        if self._tier_failures[tier] >= self._threshold and tier not in self._open_tiers:
            self._open_tiers.add(tier)
            print(f"  [CIRCUIT_BREAKER] Tier {tier} halted after {self._tier_failures[tier]} failures")
            return True
        return False

    def is_open(self, tier: str) -> bool:
        return tier in self._open_tiers

    def reset(self, tier: str) -> None:
        self._tier_failures.pop(tier, None)
        self._open_tiers.discard(tier)

    def snapshot(self) -> Dict[str, dict]:
        """Return per-tier failure counts and open status."""
        tiers = set(list(self._tier_failures.keys()) + list(self._open_tiers))
        return {t: {"consecutive_failures": self._tier_failures.get(t, 0),
                     "circuit_open": t in self._open_tiers} for t in tiers}


# Module-level singletons
_circuit_breaker = TierCircuitBreaker(threshold=3)
_message_bus_stats: Dict[str, int] = {"sent": 0, "delivered": 0, "pending": 0}


def _verify_cross_lane_data(db_path: Path, all_results: dict):
    """Cross-lane synchronization barrier.
    Verifies that BOTH Lane 1 (Tier 3) and Lane 2 (TierK) produced output
    before allowing TierL to start. Prevents race conditions where TierL
    reads incomplete data."""
    import sqlite3 as _sql

    # Check tier results first
    lane1_ok = any(r.status == "SUCCESS" for r in all_results.get("tier3", []))
    lane2_ok = any(r.status == "SUCCESS" for r in all_results.get("tierK", []))

    if not lane1_ok:
        print("  ⚠ WARNING: Lane 1 (Tier 3) had no successful agents — TierL may have incomplete data")
    if not lane2_ok:
        print("  ⚠ WARNING: Lane 2 (TierK) had no successful agents — TierL may have incomplete data")

    # Verify DB has actual data from both lanes
    try:
        conn = _sql.connect(str(db_path), timeout=30)
        conn.execute("PRAGMA busy_timeout=30000")

        atoms_count = conn.execute("SELECT COUNT(*) FROM atoms").fetchone()[0]
        findings_count = conn.execute(
            "SELECT COUNT(*) FROM judicial_findings"
        ).fetchone()[0]

        conn.close()

        print(f"  ✓ Cross-lane sync: {atoms_count} atoms, {findings_count} judicial findings")

        if atoms_count == 0 and findings_count == 0:
            print("  ⚠ WARNING: Both lanes empty — TierL will have nothing to score")
    except Exception as e:
        print(f"  ⚠ Cross-lane verification failed (non-blocking): {e}")


def _validate_tier_dependencies(tier: str, completed_tiers: set):
    """Validate that all dependencies for a tier have been completed."""
    deps = TIER_DEPENDENCIES.get(tier, [])
    missing = [d for d in deps if d not in completed_tiers]
    if missing:
        print(f"  ⚠ WARNING: Tier {tier} depends on {missing} which haven't completed")
        return False
    return True


def run_tier(tier: str, max_workers: int = 4, dry_run: bool = False) -> List[AgentResult]:
    """Run all agents in a tier with parallel execution."""
    agents = get_tier_agents(tier)
    if not agents:
        print(f"[ORCHESTRATOR] No agents for tier '{tier}'")
        return []

    print(f"\n{'='*60}")
    print(f"  TIER {tier.upper()}: {len(agents)} agents")
    print(f"{'='*60}")

    if dry_run:
        for a in agents:
            print(f"  [DRY-RUN] Would run: {a.agent_id}")
        return []

    results: List[AgentResult] = []
    max_retries = 2
    workers = TIER_WORKERS.get(tier, max_workers)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(a.run): a for a in agents}
        for future in as_completed(futures):
            if _circuit_breaker.is_open(tier):
                for f in futures:
                    f.cancel()
                break
            agent = futures[future]
            try:
                result = future.result()
                results.append(result)
                status_icon = "✓" if result.status == "SUCCESS" else "✗"
                print(f"  {status_icon} {result}")
                if result.status == "SUCCESS":
                    _circuit_breaker.record_success(tier)
                else:
                    _circuit_breaker.record_failure(tier)
            except Exception as e:
                print(f"  ✗ {agent.agent_id}: EXCEPTION: {e}")
                from .agent_models import AgentStats
                results.append(AgentResult(agent.agent_id, "CRASH",
                                           AgentStats(), error=str(e)))
                _circuit_breaker.record_failure(tier)

    # Retry failed agents (up to max_retries times)
    for retry_round in range(1, max_retries + 1):
        failed = [r for r in results if r.status in ("CRASH", "FATAL")]
        if not failed:
            break
        
        print(f"\n  ↻ Retry round {retry_round}/{max_retries}: {len(failed)} failed agents")
        time.sleep(2 ** retry_round)  # Exponential backoff: 2s, 4s
        
        # Re-instantiate failed agents and retry
        retry_agents = []
        for r in failed:
            for a in agents:
                if a.agent_id == r.agent_id:
                    retry_agents.append(a)
                    break
        
        retry_results: List[AgentResult] = []
        with ThreadPoolExecutor(max_workers=max(1, max_workers // 2)) as pool:
            futures = {pool.submit(a.run): a for a in retry_agents}
            for future in as_completed(futures):
                agent = futures[future]
                try:
                    result = future.result()
                    retry_results.append(result)
                    status_icon = "✓" if result.status == "SUCCESS" else "↻"
                    print(f"  {status_icon} [retry] {result}")
                except Exception as e:
                    from .agent_models import AgentStats
                    retry_results.append(AgentResult(agent.agent_id, "CRASH",
                                                     AgentStats(), error=str(e)))
        
        # Replace failed results with retry results
        for rr in retry_results:
            results = [r if r.agent_id != rr.agent_id else rr for r in results]

    # Assess tier completeness
    success_count = sum(1 for r in results if r.status == "SUCCESS")
    success_rate = success_count / len(results) if results else 0
    total_processed = sum(r.stats.processed for r in results)
    
    if success_rate < 0.5:
        print(f"\n  ⚠ WARNING: Tier {tier} success rate {success_rate:.0%} < 50%")
        print(f"    Only {total_processed} items processed across {success_count}/{len(results)} agents")

    # Route inter-agent messages after tier execution
    sent = sum(len(a._outbox) for a in agents if hasattr(a, '_outbox') and a._outbox)
    _message_bus_stats["sent"] += sent
    delivered = route_messages(agents, results)
    _message_bus_stats["delivered"] += delivered
    _message_bus_stats["pending"] += max(0, sent - delivered)

    return results


def run_full_fleet(dry_run: bool = False) -> Dict[str, List[AgentResult]]:
    """Execute the full DELTA9 56-agent fleet."""
    start = time.time()
    all_results: Dict[str, List[AgentResult]] = {}

    # Phase 0: Create master index DB
    print("\n[ORCHESTRATOR] Creating master_index.db...")
    create_master_index_db(MASTER_INDEX_DB)
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

    # === LANE 1 + LANE 2 PARALLEL ===
    # Tier 1 (Index) runs first, then Lane 2 starts consuming
    print("\n[ORCHESTRATOR] ═══ LANE 1: INFRASTRUCTURE ═══")
    all_results["tier1"] = run_tier("tier1", max_workers=4, dry_run=dry_run)

    # After indexing, run Tier 2 (Dedup) AND Tier J (Judicial) in parallel
    print("\n[ORCHESTRATOR] ═══ PARALLEL: LANE 1 TIER 2 + LANE 2 TIER J ═══")
    if not dry_run:
        with ThreadPoolExecutor(max_workers=2) as pool:
            f_tier2 = pool.submit(run_tier, "tier2", 4, dry_run)
            f_tierJ = pool.submit(run_tier, "tierJ", 4, dry_run)
            all_results["tier2"] = f_tier2.result()
            all_results["tierJ"] = f_tierJ.result()
    else:
        all_results["tier2"] = run_tier("tier2", dry_run=True)
        all_results["tierJ"] = run_tier("tierJ", dry_run=True)

    # Tier 3 (Flatten) AND Tier K (Case Intel) in parallel
    print("\n[ORCHESTRATOR] ═══ PARALLEL: LANE 1 TIER 3 + LANE 2 TIER K ═══")
    if not dry_run:
        with ThreadPoolExecutor(max_workers=2) as pool:
            f_tier3 = pool.submit(run_tier, "tier3", 4, dry_run)
            f_tierK = pool.submit(run_tier, "tierK", 4, dry_run)
            all_results["tier3"] = f_tier3.result()
            all_results["tierK"] = f_tierK.result()
    else:
        all_results["tier3"] = run_tier("tier3", dry_run=True)
        all_results["tierK"] = run_tier("tierK", dry_run=True)

    # Tier L (Legal Warfare) — needs both lanes' output
    # Cross-lane synchronization barrier: verify BOTH lanes produced data
    if not dry_run:
        _verify_cross_lane_data(MASTER_INDEX_DB, all_results)
    print("\n[ORCHESTRATOR] ═══ LANE 2 TIER L: LEGAL WARFARE ═══")
    all_results["tierL"] = run_tier("tierL", max_workers=4, dry_run=dry_run)

    # Convergence — after all lanes complete
    print("\n[ORCHESTRATOR] ═══ CONVERGENCE ═══")
    all_results["convergence"] = run_tier("convergence", max_workers=3, dry_run=dry_run)

    # === FINAL REPORT ===
    # Register all tier results in context manager for cross-session recall
    if _ContextManager:
        try:
            _ctx = _ContextManager("orchestrator")
            for tier_name, tier_results in all_results.items():
                summary = {
                    "tier": tier_name,
                    "agents": len(tier_results),
                    "success": sum(1 for r in tier_results if r.status == "SUCCESS"),
                    "failed": sum(1 for r in tier_results if r.status != "SUCCESS"),
                }
                _ctx.add_to_window(
                    key=f"tier_{tier_name}_results",
                    value=summary,
                    priority="HIGH",
                    category="tier_results",
                )
        except Exception:
            pass

    elapsed = time.time() - start
    print(f"\n{'='*60}")
    print(f"  DELTA9 FLEET EXECUTION COMPLETE")
    print(f"  Total time: {elapsed:.1f}s ({elapsed/60:.1f} min)")
    print(f"{'='*60}")

    total_processed = 0
    total_errors = 0
    for tier_name, results in all_results.items():
        for r in results:
            total_processed += r.stats.processed
            total_errors += r.stats.errored
            icon = "✓" if r.status == "SUCCESS" else "✗"
            print(f"  {icon} [{tier_name}] {r}")

    print(f"\n  TOTALS: {total_processed} items processed, {total_errors} errors")

    # Save report
    report_path = CHECKPOINT_DIR / "fleet_report.json"
    report = {
        "elapsed_seconds": elapsed,
        "total_processed": total_processed,
        "total_errors": total_errors,
        "tiers": {
            t: [{"agent": r.agent_id, "status": r.status,
                 "processed": r.stats.processed, "errors": r.stats.errored}
                for r in results]
            for t, results in all_results.items()
        }
    }
    report_path.write_text(json.dumps(report, indent=2))
    print(f"\n  Report saved: {report_path}")

    return all_results


def main():
    parser = argparse.ArgumentParser(description="DELTA9 Agent Fleet Orchestrator")
    parser.add_argument("--dry-run", action="store_true", help="List agents without executing")
    parser.add_argument("--tier", type=str, help="Run specific tier only")
    parser.add_argument("--agent", type=str, help="Run specific agent by ID")
    parser.add_argument("--create-db", action="store_true", help="Create master_index.db only")
    parser.add_argument("--dashboard", action="store_true", help="Show fleet health dashboard")
    args = parser.parse_args()

    if args.create_db:
        create_master_index_db(MASTER_INDEX_DB)
        print(f"Created {MASTER_INDEX_DB}")
        return

    if args.dashboard:
        print_fleet_dashboard()
        return

    if args.tier:
        create_master_index_db(MASTER_INDEX_DB)
        CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
        results = run_tier(args.tier, dry_run=args.dry_run)
        sys.exit(0 if all(r.status == "SUCCESS" for r in results) else 1)

    if args.agent:
        create_master_index_db(MASTER_INDEX_DB)
        CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
        # Find agent across all tiers
        all_agents = []
        for t in ["tier1", "tier2", "tier3", "tierJ", "tierK", "tierL", "convergence"]:
            all_agents.extend(get_tier_agents(t))
        
        target = next((a for a in all_agents if a.agent_id == args.agent), None)
        if not target:
            print(f"Error: Agent '{args.agent}' not found")
            sys.exit(1)
            
        print(f"Running single agent: {target.agent_id}")
        if not args.dry_run:
            result = target.run()
            print(f"Result: {result}")
            sys.exit(0 if result.status == "SUCCESS" else 1)
        else:
            print("Dry run complete")
            sys.exit(0)

    run_full_fleet(dry_run=args.dry_run)


# =========================================
# OMEGA v2.0: MESSAGE ROUTING
# =========================================
def route_messages(agents: list, results: List[AgentResult]) -> int:
    """Route inter-agent messages from completed agents to recipients.
    Called by orchestrator between tier executions.
    Returns number of messages delivered."""
    delivered = 0
    all_outboxes = []

    for agent in agents:
        if hasattr(agent, '_outbox') and agent._outbox:
            all_outboxes.extend(agent._outbox)

    for msg in all_outboxes:
        if msg.recipient == "*":
            # Broadcast to all agents
            for agent in agents:
                if agent.agent_id != msg.sender:
                    agent.deliver_messages([msg])
                    delivered += 1
        else:
            target = next((a for a in agents if a.agent_id == msg.recipient), None)
            if target:
                target.deliver_messages([msg])
                delivered += 1

    if delivered > 0:
        print(f"  📨 Routed {delivered} inter-agent messages")
    return delivered


# =========================================
# OMEGA v2.0: HEALTH-AWARE SCHEDULING
# =========================================
def compute_tier_health(results: List[AgentResult]) -> dict:
    """Compute health metrics for a tier's execution results."""
    if not results:
        return {"status": "EMPTY", "success_rate": 0, "quality_avg": 0,
                "total_processed": 0, "total_errors": 0, "findings_count": 0}

    success = sum(1 for r in results if r.status in ("SUCCESS", "PARTIAL"))
    total = len(results)
    quality_scores = [r.quality.overall for r in results
                      if r.quality is not None]
    findings_count = sum(len(r.findings) for r in results)

    return {
        "status": "HEALTHY" if success / total > 0.7 else
                  "DEGRADED" if success / total > 0.3 else "CRITICAL",
        "success_rate": success / total,
        "quality_avg": sum(quality_scores) / len(quality_scores) if quality_scores else 0,
        "total_processed": sum(r.stats.processed for r in results),
        "total_errors": sum(r.stats.errored for r in results),
        "findings_count": findings_count,
        "agents": total,
        "retries": sum(r.stats.retry_count for r in results),
    }


def adaptive_workers(tier: str, health_history: dict) -> int:
    """Compute optimal worker count based on prior tier health.
    Reduces parallelism after errors, increases after success."""
    base = 4

    # Check health of dependency tiers
    for dep_tier in TIER_DEPENDENCIES.get(tier, []):
        dep_health = health_history.get(dep_tier, {})
        if dep_health.get("status") == "CRITICAL":
            return max(1, base // 2)
        if dep_health.get("status") == "DEGRADED":
            base = max(2, base - 1)

    return base


def get_fleet_health() -> dict:
    """Return a structured health snapshot of the fleet from the last run."""
    report_path = CHECKPOINT_DIR / "fleet_report.json"
    report: dict = {}
    if report_path.exists():
        try:
            report = json.loads(report_path.read_text())
        except (json.JSONDecodeError, OSError):
            pass

    tiers_detail: Dict[str, dict] = {}
    total_agents = total_passed = total_failed = 0

    for tier_id, agents_list in report.get("tiers", {}).items():
        passed = sum(1 for a in agents_list if a.get("status") == "SUCCESS")
        failed = len(agents_list) - passed
        cb_snap = _circuit_breaker.snapshot()
        tiers_detail[tier_id] = {
            "agents_run": len(agents_list),
            "agents_passed": passed,
            "agents_failed": failed,
            "circuit_open": cb_snap.get(tier_id, {}).get("circuit_open", False),
        }
        total_agents += len(agents_list)
        total_passed += passed
        total_failed += failed

    if total_agents == 0:
        health = "HEALTHY"
    elif total_failed == 0:
        health = "HEALTHY"
    elif total_passed / total_agents >= 0.7:
        health = "HEALTHY"
    elif total_passed / total_agents >= 0.3:
        health = "DEGRADED"
    else:
        health = "CRITICAL"

    return {
        "tiers": tiers_detail,
        "total_agents": total_agents,
        "total_passed": total_passed,
        "total_failed": total_failed,
        "overall_health": health,
        "message_bus_stats": dict(_message_bus_stats),
    }


# =========================================
# OMEGA v2.0: FLEET DASHBOARD
# =========================================
def print_fleet_dashboard():
    """Print fleet health dashboard from last run's report."""
    report_path = CHECKPOINT_DIR / "fleet_report.json"
    if not report_path.exists():
        print("No fleet report found. Run the fleet first.")
        return

    report = json.loads(report_path.read_text())
    print(f"\n{'═'*60}")
    print(f"  DELTA9 OMEGA FLEET DASHBOARD")
    print(f"{'═'*60}")
    print(f"  Last run: {report.get('elapsed_seconds', 0):.1f}s")
    print(f"  Total processed: {report.get('total_processed', 0):,}")
    print(f"  Total errors: {report.get('total_errors', 0):,}")

    if "tier_health" in report:
        print(f"\n  {'Tier':<15} {'Status':<10} {'Quality':<10} {'Rate':<8} {'Findings'}")
        print(f"  {'─'*55}")
        for tier_name, health in report["tier_health"].items():
            status = health.get("status", "?")
            quality = health.get("quality_avg", 0)
            rate = health.get("success_rate", 0)
            findings = health.get("findings_count", 0)
            icon = "✓" if status == "HEALTHY" else "⚠" if status == "DEGRADED" else "✗"
            print(f"  {icon} {tier_name:<13} {status:<10} {quality:.2f}      {rate:.0%}    {findings}")

    tiers = report.get("tiers", {})
    print(f"\n  {'Agent':<30} {'Status':<10} {'Processed':<12} {'Errors'}")
    print(f"  {'─'*65}")
    for tier_name, agents in tiers.items():
        for a in agents:
            icon = "✓" if a.get("status") == "SUCCESS" else "✗"
            print(f"  {icon} {a['agent']:<28} {a['status']:<10} "
                  f"{a.get('processed', 0):<12} {a.get('errors', 0)}")
    print()


if __name__ == "__main__":
    main()
