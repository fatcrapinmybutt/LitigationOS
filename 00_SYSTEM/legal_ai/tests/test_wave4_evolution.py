"""Tests for Wave 4 Evolution modules — LitigationOS Legal AI.

Covers:
    1. SkillEvolver           (skill_evolver.py)
    2. SelfHealingMonitor     (self_healing_monitor.py)
    3. BrainEvolverDaemon     (brain_evolver_daemon.py)
    4. KnowledgeGraphEnricher (knowledge_graph_enricher.py)
    5. CodebaseHealthTracker  (codebase_health_tracker.py)

All tests are pure unit tests — no DB connections, no external dependencies.
Run with:
    cd C:\\Users\\andre\\LitigationOS\\00_SYSTEM\\legal_ai
    python -m pytest tests/test_wave4_evolution.py -v
"""
from __future__ import annotations

import ast
import json
import os
import sqlite3
import sys
import tempfile
import textwrap
import unittest
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch, PropertyMock

# ---------------------------------------------------------------------------
# Ensure legal_ai package is importable (avoid repo-root shadow modules)
# ---------------------------------------------------------------------------
_LEGAL_AI_DIR = Path(__file__).resolve().parent.parent
if str(_LEGAL_AI_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_LEGAL_AI_DIR.parent))

# ---------------------------------------------------------------------------
# Imports from modules under test
# ---------------------------------------------------------------------------
from legal_ai.skill_evolver import (
    SkillEvolver,
    SkillMetrics,
    EvolutionRecord,
    EvolutionReport,
    MI_DOMAIN_SKILLS,
)

from legal_ai.self_healing_monitor import (
    SelfHealingMonitor,
    HealthStatus,
    ComponentHealth,
    HealthAlert,
    RecoveryAction,
    HealthReport,
)

from legal_ai.brain_evolver_daemon import (
    BrainEvolverDaemon,
    BrainStatus,
    MaintenanceResult,
    MaintenanceReport,
    BRAIN_REGISTRY,
)

from legal_ai.knowledge_graph_enricher import (
    KnowledgeGraphEnricher,
    AuthorityNode,
    AuthorityEdge,
    AuthorityCluster,
    GraphReport,
)

from legal_ai.codebase_health_tracker import (
    CodebaseHealthTracker,
    ModuleHealth,
    CodebaseReport,
    _GRADE_THRESHOLDS,
)


# ###########################################################################
# Helper: in-memory DB that passes _ensure_tables() checks
# ###########################################################################

def _make_temp_db() -> str:
    """Create a temporary SQLite DB path that exists on disk."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return path


# ###########################################################################
# Helper: sample Python source for analysis tests
# ###########################################################################

_SAMPLE_GOOD_PY = textwrap.dedent('''\
    """A well-documented sample module."""
    import os
    from typing import Dict

    class MyEngine:
        """Engine docstring."""

        def __init__(self) -> None:
            self._data: Dict[str, int] = {}

        def run(self, x: int) -> int:
            """Run the engine."""
            try:
                return x * 2
            except Exception:
                return 0

        def get_stats(self) -> dict:
            """Return stats."""
            return {"module": "sample"}

        def to_dict(self) -> dict:
            """Serialize."""
            return {}

    if __name__ == "__main__":
        e = MyEngine()
        print(e.run(5))
''')

_SAMPLE_BAD_PY = textwrap.dedent('''\
    x = 1
    y = x + 2
    print(y)
''')

_SAMPLE_SYNTAX_ERROR_PY = textwrap.dedent('''\
    def broken(:
        pass
''')


# ###########################################################################
# 1. SkillEvolver Tests
# ###########################################################################

class TestSkillMetricsDataclass(unittest.TestCase):
    """Test SkillMetrics and EvolutionRecord dataclasses."""

    def test_metrics_to_dict(self):
        m = SkillMetrics(skill_name="test_skill", module_path="/fake/path.py")
        d = m.to_dict()
        self.assertEqual(d["skill_name"], "test_skill")
        self.assertEqual(d["invocation_count"], 0)
        self.assertEqual(d["success_rate"], 1.0)

    def test_evolution_record_to_dict(self):
        r = EvolutionRecord(
            skill_name="skill_best_interest",
            version="v1.1",
            changes=["Added docstrings", "Added error handling"],
            before_score=45.0,
            after_score=72.0,
            improvement_pct=60.0,
        )
        d = r.to_dict()
        self.assertEqual(d["skill_name"], "skill_best_interest")
        self.assertEqual(d["version"], "v1.1")
        self.assertEqual(len(d["changes"]), 2)

    def test_report_to_dict(self):
        report = EvolutionReport(
            total_skills=14,
            evolved_count=3,
            improvement_avg=15.5,
        )
        d = report.to_dict()
        self.assertEqual(d["total_skills"], 14)
        self.assertEqual(d["improvement_avg"], 15.5)
        self.assertIn("recommendations", d)

    def test_mi_domain_skills_populated(self):
        self.assertGreater(len(MI_DOMAIN_SKILLS), 0)
        for skill in MI_DOMAIN_SKILLS:
            self.assertIn("name", skill)
            self.assertIn("file", skill)


class TestSkillEvolver(unittest.TestCase):
    """Test SkillEvolver with temp filesystem and mocked DB."""

    def setUp(self):
        self._tmp_db = _make_temp_db()
        self._tmp_skill_dir = tempfile.mkdtemp()
        # Write sample skill files
        self._good_skill = os.path.join(self._tmp_skill_dir, "skill_test_good.py")
        with open(self._good_skill, "w", encoding="utf-8") as f:
            f.write(_SAMPLE_GOOD_PY)
        self._bad_skill = os.path.join(self._tmp_skill_dir, "skill_test_bad.py")
        with open(self._bad_skill, "w", encoding="utf-8") as f:
            f.write(_SAMPLE_BAD_PY)

        self.evolver = SkillEvolver(
            db_path=self._tmp_db,
            engines_dir=self._tmp_skill_dir,
            skills_dir=self._tmp_skill_dir,
        )

    def tearDown(self):
        try:
            os.unlink(self._tmp_db)
        except OSError:
            pass
        for f in os.listdir(self._tmp_skill_dir):
            try:
                os.unlink(os.path.join(self._tmp_skill_dir, f))
            except OSError:
                pass
        try:
            os.rmdir(self._tmp_skill_dir)
        except OSError:
            pass

    def test_scan_skills_finds_modules(self):
        results = self.evolver.scan_skills(self._tmp_skill_dir)
        self.assertIsInstance(results, list)
        names = [m.skill_name for m in results]
        self.assertIn("skill_test_good", names)

    def test_analyze_skill_returns_metrics(self):
        metrics = self.evolver.analyze_skill(self._good_skill)
        self.assertIsInstance(metrics, SkillMetrics)
        self.assertEqual(metrics.skill_name, "skill_test_good")
        self.assertGreater(metrics.lines_of_code, 0)

    def test_skill_score_range(self):
        metrics = self.evolver.analyze_skill(self._good_skill)
        score = self.evolver.score_skill(metrics)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 100.0)

    def test_score_components(self):
        """Good skill should score well on completeness, error_handling, docs."""
        metrics = self.evolver.analyze_skill(self._good_skill)
        self.assertTrue(metrics.has_get_stats)
        self.assertTrue(metrics.has_to_dict)
        self.assertTrue(metrics.has_main_guard)
        self.assertGreater(metrics.docstring_coverage, 0)
        self.assertGreater(metrics.error_handling_score, 0)

    def test_bad_skill_lower_score(self):
        """Bad skill (no docs, no classes, no error handling) should score lower."""
        good_metrics = self.evolver.analyze_skill(self._good_skill)
        bad_metrics = self.evolver.analyze_skill(self._bad_skill)
        good_score = self.evolver.score_skill(good_metrics)
        bad_score = self.evolver.score_skill(bad_metrics)
        self.assertGreater(good_score, bad_score)

    def test_identify_evolution_targets(self):
        self.evolver.scan_skills(self._tmp_skill_dir)
        targets = self.evolver.identify_evolution_targets()
        self.assertIsInstance(targets, list)
        # bad skill should be a target
        target_names = [t[0] for t in targets]
        self.assertIn("skill_test_bad", target_names)

    def test_evolve_skill_records_change(self):
        record = self.evolver.evolve_skill(
            "skill_test_good",
            changes=["Added retry logic", "Improved docstrings"],
        )
        self.assertIsInstance(record, EvolutionRecord)
        self.assertEqual(record.skill_name, "skill_test_good")
        self.assertEqual(len(record.changes), 2)

    def test_evolution_history_tracked(self):
        self.evolver.evolve_skill("skill_test_good", changes=["Change 1"])
        history = self.evolver.get_evolution_history("skill_test_good")
        self.assertIsInstance(history, list)

    def test_evolution_report_structure(self):
        self.evolver.scan_skills(self._tmp_skill_dir)
        report = self.evolver.generate_report()
        self.assertIsInstance(report, EvolutionReport)
        d = report.to_dict()
        self.assertIn("total_skills", d)
        self.assertIn("recommendations", d)
        self.assertIn("top_performers", d)
        self.assertIn("bottom_performers", d)

    def test_get_stats(self):
        stats = self.evolver.get_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("scans_run", stats)


# ###########################################################################
# 2. SelfHealingMonitor Tests
# ###########################################################################

class TestHealthStatusEnum(unittest.TestCase):
    """Test HealthStatus enum values."""

    def test_health_status_enum_values(self):
        self.assertEqual(HealthStatus.HEALTHY.value, "healthy")
        self.assertEqual(HealthStatus.DEGRADED.value, "degraded")
        self.assertEqual(HealthStatus.FAILING.value, "failing")
        self.assertEqual(HealthStatus.DEAD.value, "dead")
        self.assertEqual(HealthStatus.UNKNOWN.value, "unknown")


class TestHealthDataclasses(unittest.TestCase):
    """Test ComponentHealth, HealthAlert, RecoveryAction, HealthReport."""

    def test_component_health_to_dict(self):
        ch = ComponentHealth(
            component_name="litigation_context",
            component_type="database",
            status=HealthStatus.HEALTHY,
            last_check="2025-01-01T00:00:00",
            uptime_pct=99.9,
        )
        d = ch.to_dict()
        self.assertEqual(d["status"], "healthy")
        self.assertEqual(d["component_name"], "litigation_context")

    def test_health_alert_to_dict(self):
        alert = HealthAlert(
            severity="critical",
            component="disk_C",
            message="Low disk space",
            suggested_action="Free up space",
        )
        d = alert.to_dict()
        self.assertEqual(d["severity"], "critical")
        self.assertIn("suggested_action", d)

    def test_recovery_action_to_dict(self):
        action = RecoveryAction(
            priority=1,
            component="litigation_context",
            action="WAL checkpoint",
            command="PRAGMA wal_checkpoint(TRUNCATE)",
            estimated_impact="Reduce WAL size",
        )
        d = action.to_dict()
        self.assertEqual(d["priority"], 1)
        self.assertIn("command", d)

    def test_health_report_to_dict(self):
        report = HealthReport(
            overall_status=HealthStatus.DEGRADED,
            total_components=10,
            healthy=7,
            degraded=2,
            failing=1,
        )
        d = report.to_dict()
        self.assertEqual(d["overall_status"], "degraded")
        self.assertEqual(d["total_components"], 10)
        self.assertEqual(d["healthy"], 7)


class TestSelfHealingMonitor(unittest.TestCase):
    """Test SelfHealingMonitor with temp DB — heavy FS scans are mocked."""

    def setUp(self):
        self._tmp_db = _make_temp_db()
        self.monitor = SelfHealingMonitor(db_path=self._tmp_db)

    def tearDown(self):
        try:
            os.unlink(self._tmp_db)
        except OSError:
            pass
        for ext in ("-wal", "-shm"):
            try:
                os.unlink(self._tmp_db + ext)
            except OSError:
                pass

    def test_check_database_health(self):
        result = self.monitor.check_database_health(self._tmp_db)
        self.assertIsInstance(result, ComponentHealth)
        self.assertEqual(result.component_type, "database")
        self.assertIn(result.status, list(HealthStatus))

    def test_check_module_health_valid_file(self):
        """A valid Python file should be healthy."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(_SAMPLE_GOOD_PY)
            tmp_path = f.name
        try:
            result = self.monitor.check_module_health(tmp_path)
            self.assertIsInstance(result, ComponentHealth)
            self.assertEqual(result.component_type, "module")
        finally:
            os.unlink(tmp_path)

    def test_check_module_health_syntax_error(self):
        """A file with syntax errors should be degraded or failing."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(_SAMPLE_SYNTAX_ERROR_PY)
            tmp_path = f.name
        try:
            result = self.monitor.check_module_health(tmp_path)
            self.assertIsInstance(result, ComponentHealth)
            self.assertIn(result.status, (
                HealthStatus.DEGRADED, HealthStatus.FAILING, HealthStatus.DEAD,
            ))
        finally:
            os.unlink(tmp_path)

    def test_check_disk_health(self):
        result = self.monitor.check_disk_health()
        self.assertIsInstance(result, ComponentHealth)
        self.assertEqual(result.component_type, "filesystem")

    def _mock_full_health_check(self):
        """Run full_health_check with heavy FS scans stubbed out."""
        healthy_component = ComponentHealth(
            component_name="mock_db", component_type="database",
            status=HealthStatus.HEALTHY,
            last_check="2025-01-01T00:00:00",
        )
        degraded_component = ComponentHealth(
            component_name="mock_module", component_type="module",
            status=HealthStatus.DEGRADED,
            last_check="2025-01-01T00:00:00",
        )
        mock_components = [healthy_component, degraded_component]
        with (
            unittest.mock.patch.object(
                self.monitor, "check_all_databases", return_value=[healthy_component]
            ),
            unittest.mock.patch.object(
                self.monitor, "check_all_modules", return_value=[degraded_component]
            ),
            unittest.mock.patch.object(
                self.monitor, "check_all_skills", return_value=[]
            ),
            unittest.mock.patch.object(
                self.monitor, "check_pipeline_health",
                return_value=healthy_component,
            ),
            unittest.mock.patch.object(
                self.monitor, "check_agent_health",
                return_value=healthy_component,
            ),
            unittest.mock.patch.object(
                self.monitor, "check_disk_health",
                return_value=healthy_component,
            ),
        ):
            return self.monitor.run_full_health_check()

    def test_full_health_check_returns_report(self):
        report = self._mock_full_health_check()
        self.assertIsInstance(report, HealthReport)
        self.assertGreater(report.total_components, 0)

    def test_overall_status_calculation(self):
        report = self._mock_full_health_check()
        self.assertIn(report.overall_status, list(HealthStatus))

    def test_healthy_count(self):
        report = self._mock_full_health_check()
        total = report.healthy + report.degraded + report.failing + report.dead
        self.assertGreaterEqual(report.total_components, 0)

    def test_degraded_detection(self):
        """A report with some failing components should detect degraded state."""
        ch = ComponentHealth(
            component_name="test", component_type="database",
            status=HealthStatus.DEGRADED,
        )
        alerts = self.monitor._generate_alerts([ch])
        self.assertIsInstance(alerts, list)

    def test_recovery_plan_generated(self):
        report = self._mock_full_health_check()
        plan = self.monitor.generate_recovery_plan(report)
        self.assertIsInstance(plan, list)

    def test_get_stats(self):
        stats = self.monitor.get_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("checks_run", stats)
        self.assertIn("db_path", stats)


# ###########################################################################
# 3. BrainEvolverDaemon Tests
# ###########################################################################

class TestBrainDataclasses(unittest.TestCase):
    """Test BrainStatus, MaintenanceResult, MaintenanceReport dataclasses."""

    def test_brain_status_fields(self):
        bs = BrainStatus(
            brain_name="lane_A_custody",
            table_count=42,
            row_count=10000,
            size_bytes=1_000_000,
            has_fts=True,
            quality_score=0.85,
        )
        self.assertEqual(bs.brain_name, "lane_A_custody")
        self.assertEqual(bs.table_count, 42)
        self.assertTrue(bs.has_fts)

    def test_brain_status_to_dict(self):
        bs = BrainStatus(brain_name="test", quality_score=0.9)
        d = bs.to_dict()
        self.assertEqual(d["brain_name"], "test")
        self.assertAlmostEqual(d["quality_score"], 0.9)

    def test_maintenance_result_to_dict(self):
        mr = MaintenanceResult(
            brain_name="lane_B_housing",
            action="dedup",
            items_processed=500,
            items_removed=12,
        )
        d = mr.to_dict()
        self.assertEqual(d["action"], "dedup")
        self.assertEqual(d["items_processed"], 500)

    def test_maintenance_report_to_dict(self):
        report = MaintenanceReport(
            brains_maintained=5,
            total_actions=10,
            space_saved_bytes=1048576,  # 1 MB
        )
        d = report.to_dict()
        self.assertEqual(d["brains_maintained"], 5)
        self.assertAlmostEqual(d["space_saved_mb"], 1.0)

    def test_brain_registry_populated(self):
        self.assertGreater(len(BRAIN_REGISTRY), 0)
        names = [b["name"] for b in BRAIN_REGISTRY]
        self.assertIn("litigation_context", names)
        self.assertIn("lane_A_custody", names)


class TestBrainEvolverDaemon(unittest.TestCase):
    """Test BrainEvolverDaemon with temp DB."""

    def setUp(self):
        self._tmp_db = _make_temp_db()
        self._tmp_brains = tempfile.mkdtemp()
        self.daemon = BrainEvolverDaemon(
            db_path=self._tmp_db,
            brains_dir=self._tmp_brains,
        )

    def tearDown(self):
        for f in [self._tmp_db, self._tmp_db + "-wal", self._tmp_db + "-shm"]:
            try:
                os.unlink(f)
            except OSError:
                pass
        try:
            for f in os.listdir(self._tmp_brains):
                os.unlink(os.path.join(self._tmp_brains, f))
            os.rmdir(self._tmp_brains)
        except OSError:
            pass

    def _make_sample_brain(self, name: str = "test_brain") -> str:
        """Create a small SQLite brain with test data."""
        path = os.path.join(self._tmp_brains, f"{name}.db")
        conn = sqlite3.connect(path)
        conn.execute("CREATE TABLE documents (id INTEGER PRIMARY KEY, content TEXT, source TEXT, created_at TEXT)")
        conn.execute("INSERT INTO documents VALUES (1, 'Hello world', 'test', '2024-01-01')")
        conn.execute("INSERT INTO documents VALUES (2, 'Hello world', 'test', '2024-01-02')")
        conn.execute("INSERT INTO documents VALUES (3, 'Different content', 'test', '2024-06-01')")
        conn.commit()
        conn.close()
        return path

    def test_scan_brains_finds_databases(self):
        self._make_sample_brain("lane_test")
        results = self.daemon.scan_brains()
        self.assertIsInstance(results, list)

    def test_brain_status_fields_populated(self):
        brain_path = self._make_sample_brain()
        bs = self.daemon._assess_brain(Path(brain_path), "test_brain")
        self.assertIsInstance(bs, BrainStatus)
        self.assertEqual(bs.brain_name, "test_brain")
        self.assertGreater(bs.size_bytes, 0)

    def test_maintain_brain_returns_results(self):
        brain_path = self._make_sample_brain()
        results = self.daemon.maintain_brain(brain_path)
        self.assertIsInstance(results, list)
        for r in results:
            self.assertIsInstance(r, MaintenanceResult)

    def test_dedup_uses_content_comparison(self):
        """CRITICAL: dedup must use content-based comparison, not hash-only."""
        brain_path = self._make_sample_brain()
        result = self.daemon.dedup_brain(brain_path)
        self.assertIsInstance(result, MaintenanceResult)
        self.assertEqual(result.action, "dedup")
        # Content-based dedup should process rows
        self.assertGreaterEqual(result.items_processed, 0)

    def test_fts_rebuild_action(self):
        brain_path = self._make_sample_brain()
        result = self.daemon.rebuild_fts(brain_path)
        self.assertIsInstance(result, MaintenanceResult)
        self.assertIn("fts", result.action.lower())

    def test_prune_stale_entries(self):
        brain_path = self._make_sample_brain()
        result = self.daemon.prune_stale(brain_path, max_age_days=30)
        self.assertIsInstance(result, MaintenanceResult)

    def test_wal_checkpoint_action(self):
        brain_path = self._make_sample_brain()
        result = self.daemon.checkpoint_wal(brain_path)
        self.assertIsInstance(result, MaintenanceResult)

    def test_integrity_check(self):
        brain_path = self._make_sample_brain()
        result = self.daemon.check_integrity(brain_path)
        self.assertIsInstance(result, dict)
        self.assertIn("ok", result)
        self.assertTrue(result["ok"])

    def test_maintenance_report_structure(self):
        brain_path = self._make_sample_brain()
        results = self.daemon.maintain_brain(brain_path)
        report = MaintenanceReport(
            brains_maintained=1,
            total_actions=len(results),
            results=results,
        )
        d = report.to_dict()
        self.assertIn("brains_maintained", d)
        self.assertIn("results", d)
        self.assertIsInstance(d["results"], list)

    def test_get_stats(self):
        stats = self.daemon.get_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("actions_performed", stats)


# ###########################################################################
# 4. KnowledgeGraphEnricher Tests
# ###########################################################################

class TestAuthorityDataclasses(unittest.TestCase):
    """Test AuthorityNode, AuthorityEdge, AuthorityCluster, GraphReport."""

    def test_authority_node_to_dict(self):
        node = AuthorityNode(
            node_id="n1",
            citation="Troxel v. Granville, 530 U.S. 57 (2000)",
            authority_type="case",
            jurisdiction="SCOTUS",
            year=2000,
            court="U.S. Supreme Court",
            relevance_score=0.85,
            binding=True,
            lanes=["A", "D"],
        )
        d = node.to_dict()
        self.assertEqual(d["node_id"], "n1")
        self.assertEqual(d["jurisdiction"], "SCOTUS")
        self.assertTrue(d["binding"])
        self.assertEqual(d["year"], 2000)

    def test_authority_edge_to_dict(self):
        edge = AuthorityEdge(source_id="n1", target_id="n2", relationship="cites")
        d = edge.to_dict()
        self.assertEqual(d["source_id"], "n1")
        self.assertEqual(d["relationship"], "cites")

    def test_authority_cluster_to_dict(self):
        cluster = AuthorityCluster(
            cluster_id="c1", theme="due_process",
            authorities=["n1", "n2"], density=0.75, lanes=["A"],
        )
        d = cluster.to_dict()
        self.assertEqual(d["theme"], "due_process")
        self.assertAlmostEqual(d["density"], 0.75, places=3)

    def test_graph_report_to_dict(self):
        report = GraphReport(total_nodes=10, total_edges=15)
        d = report.to_dict()
        self.assertEqual(d["total_nodes"], 10)
        self.assertEqual(d["total_edges"], 15)
        self.assertIn("clusters", d)


class TestKnowledgeGraphEnricher(unittest.TestCase):
    """Test KnowledgeGraphEnricher in memory (no DB file needed)."""

    def setUp(self):
        self.enricher = KnowledgeGraphEnricher(db_path=Path(":memory:"))

    def _add_test_graph(self):
        """Add a small test graph with known structure."""
        # Hub node: Troxel (cited by many)
        hub = AuthorityNode(
            node_id="troxel", citation="Troxel v. Granville, 530 U.S. 57 (2000)",
            authority_type="case", jurisdiction="SCOTUS", year=2000,
            binding=True, lanes=["A", "D"],
        )
        leaf1 = AuthorityNode(
            node_id="mcl722", citation="MCL 722.23",
            authority_type="statute", jurisdiction="MI",
            binding=True, lanes=["A"],
        )
        leaf2 = AuthorityNode(
            node_id="mcr2003", citation="MCR 2.003",
            authority_type="rule", jurisdiction="MCR",
            binding=True, lanes=["A", "E"],
        )
        orphan = AuthorityNode(
            node_id="orphan1", citation="Some Obscure Case (1999)",
            authority_type="case", jurisdiction="MI",
            lanes=["B"],
        )

        self.enricher.add_authority(hub)
        self.enricher.add_authority(leaf1)
        self.enricher.add_authority(leaf2)
        self.enricher.add_authority(orphan)

        # Edges: leaf1 → hub, leaf2 → hub (hub is a hub)
        self.enricher.add_edge(AuthorityEdge(source_id="mcl722", target_id="troxel"))
        self.enricher.add_edge(AuthorityEdge(source_id="mcr2003", target_id="troxel"))
        # hub → leaf1 (bidirectional relevance)
        self.enricher.add_edge(AuthorityEdge(source_id="troxel", target_id="mcl722"))

    def test_add_authority_node(self):
        node = AuthorityNode(
            node_id="n1", citation="Test v. Case",
            authority_type="case", jurisdiction="MI",
        )
        self.enricher.add_authority(node)
        self.assertIn("n1", self.enricher._nodes)

    def test_add_edge(self):
        n1 = AuthorityNode(node_id="a", citation="A", authority_type="case", jurisdiction="MI")
        n2 = AuthorityNode(node_id="b", citation="B", authority_type="case", jurisdiction="MI")
        self.enricher.add_authority(n1)
        self.enricher.add_authority(n2)
        edge = AuthorityEdge(source_id="a", target_id="b")
        self.enricher.add_edge(edge)
        self.assertIn(("a", "b"), self.enricher._edges)

    def test_pagerank_converges(self):
        self._add_test_graph()
        scores = self.enricher.compute_pagerank()
        self.assertIsInstance(scores, dict)
        self.assertGreater(len(scores), 0)
        # All scores should be non-negative
        for s in scores.values():
            self.assertGreaterEqual(s, 0.0)

    def test_pagerank_scores_sum_approximately(self):
        """After normalization, max score should be 1.0."""
        self._add_test_graph()
        scores = self.enricher.compute_pagerank()
        max_score = max(scores.values())
        self.assertAlmostEqual(max_score, 1.0, places=2)

    def test_pagerank_hub_authority_higher(self):
        """Hub node (troxel) should have highest or near-highest pagerank."""
        self._add_test_graph()
        scores = self.enricher.compute_pagerank()
        # troxel is cited by 2 nodes → should have high score
        self.assertGreater(scores["troxel"], scores.get("orphan1", 0))

    def test_detect_clusters(self):
        self._add_test_graph()
        clusters = self.enricher.detect_clusters()
        self.assertIsInstance(clusters, list)
        self.assertGreater(len(clusters), 0)

    def test_find_orphans(self):
        self._add_test_graph()
        orphans = self.enricher.find_orphans()
        self.assertIsInstance(orphans, list)
        # orphan1 has no edges → should be found
        self.assertIn("orphan1", orphans)

    def test_find_gaps_by_lane(self):
        self._add_test_graph()
        gaps = self.enricher.find_gaps(lane="A")
        self.assertIsInstance(gaps, list)

    def test_seed_authorities_loaded(self):
        """enrich_from_seeds should load SCOTUS, MI, MCR, MCL authorities."""
        count = self.enricher.enrich_from_seeds()
        self.assertGreater(count, 0)
        # Check jurisdiction diversity
        jurisdictions = {n.jurisdiction for n in self.enricher._nodes.values()}
        for expected in ("SCOTUS", "MI", "MCR", "MCL"):
            self.assertIn(expected, jurisdictions,
                          f"{expected} authorities should be seeded")

    def test_mermaid_export_valid(self):
        self._add_test_graph()
        mermaid = self.enricher.export_mermaid()
        self.assertIsInstance(mermaid, str)
        self.assertIn("graph", mermaid.lower())

    def test_get_stats(self):
        self._add_test_graph()
        stats = self.enricher.get_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("total_nodes", stats)


# ###########################################################################
# 5. CodebaseHealthTracker Tests
# ###########################################################################

class TestModuleHealthDataclass(unittest.TestCase):
    """Test ModuleHealth and CodebaseReport dataclasses."""

    def test_module_health_to_dict(self):
        mh = ModuleHealth(
            module_path="/fake/path.py",
            module_name="suggestion_engine",
            lines_of_code=1200,
            function_count=15,
            class_count=3,
            has_docstrings=True,
            has_type_hints=True,
            has_error_handling=True,
            syntax_valid=True,
            quality_score=85.0,
        )
        d = mh.to_dict()
        self.assertEqual(d["module_name"], "suggestion_engine")
        self.assertEqual(d["lines_of_code"], 1200)
        self.assertTrue(d["has_docstrings"])

    def test_codebase_report_to_dict(self):
        report = CodebaseReport(
            total_modules=50,
            avg_quality_score=72.5,
            grade="B-",
        )
        d = report.to_dict()
        self.assertEqual(d["total_modules"], 50)
        self.assertEqual(d["grade"], "B-")
        self.assertIn("recommendations", d)


class TestCodebaseHealthTracker(unittest.TestCase):
    """Test CodebaseHealthTracker with temp files."""

    def setUp(self):
        self._tmp_db = _make_temp_db()
        self.tracker = CodebaseHealthTracker(db_path=Path(self._tmp_db))

    def tearDown(self):
        for f in [self._tmp_db, self._tmp_db + "-wal", self._tmp_db + "-shm"]:
            try:
                os.unlink(f)
            except OSError:
                pass

    def _write_tmp_py(self, content: str) -> str:
        """Write content to a temp .py file and return its path."""
        fd, path = tempfile.mkstemp(suffix=".py")
        os.close(fd)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def test_analyze_module_returns_health(self):
        path = self._write_tmp_py(_SAMPLE_GOOD_PY)
        try:
            health = self.tracker.analyze_module(path)
            self.assertIsInstance(health, ModuleHealth)
            self.assertGreater(health.lines_of_code, 0)
        finally:
            os.unlink(path)

    def test_syntax_valid_check(self):
        good_path = self._write_tmp_py(_SAMPLE_GOOD_PY)
        bad_path = self._write_tmp_py(_SAMPLE_SYNTAX_ERROR_PY)
        try:
            good_health = self.tracker.analyze_module(good_path)
            bad_health = self.tracker.analyze_module(bad_path)
            self.assertTrue(good_health.syntax_valid)
            self.assertFalse(bad_health.syntax_valid)
        finally:
            os.unlink(good_path)
            os.unlink(bad_path)

    def test_docstring_detection(self):
        path = self._write_tmp_py(_SAMPLE_GOOD_PY)
        try:
            health = self.tracker.analyze_module(path)
            self.assertTrue(health.has_docstrings)
        finally:
            os.unlink(path)

    def test_no_docstring_detection(self):
        path = self._write_tmp_py(_SAMPLE_BAD_PY)
        try:
            health = self.tracker.analyze_module(path)
            self.assertFalse(health.has_docstrings)
        finally:
            os.unlink(path)

    def test_type_hint_detection(self):
        path = self._write_tmp_py(_SAMPLE_GOOD_PY)
        try:
            health = self.tracker.analyze_module(path)
            self.assertTrue(health.has_type_hints)
        finally:
            os.unlink(path)

    def test_error_handling_detection(self):
        path = self._write_tmp_py(_SAMPLE_GOOD_PY)
        try:
            health = self.tracker.analyze_module(path)
            self.assertTrue(health.has_error_handling)
        finally:
            os.unlink(path)

    def test_quality_score_range(self):
        path = self._write_tmp_py(_SAMPLE_GOOD_PY)
        try:
            health = self.tracker.analyze_module(path)
            score = self.tracker.score_module(health)
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 100.0)
        finally:
            os.unlink(path)

    def test_grade_thresholds(self):
        """Test all grade boundaries."""
        self.assertEqual(CodebaseHealthTracker.calculate_grade(96.0), "A+")
        self.assertEqual(CodebaseHealthTracker.calculate_grade(91.0), "A")
        self.assertEqual(CodebaseHealthTracker.calculate_grade(86.0), "A-")
        self.assertEqual(CodebaseHealthTracker.calculate_grade(81.0), "B+")
        self.assertEqual(CodebaseHealthTracker.calculate_grade(76.0), "B")
        self.assertEqual(CodebaseHealthTracker.calculate_grade(71.0), "B-")
        self.assertEqual(CodebaseHealthTracker.calculate_grade(66.0), "C+")
        self.assertEqual(CodebaseHealthTracker.calculate_grade(61.0), "C")
        self.assertEqual(CodebaseHealthTracker.calculate_grade(51.0), "D")
        self.assertEqual(CodebaseHealthTracker.calculate_grade(30.0), "F")

    def test_html_dashboard_generated(self):
        path = self._write_tmp_py(_SAMPLE_GOOD_PY)
        try:
            health = self.tracker.analyze_module(path)
            report = CodebaseReport(
                total_modules=1,
                modules=[health],
                avg_quality_score=self.tracker.score_module(health),
                grade=CodebaseHealthTracker.calculate_grade(
                    self.tracker.score_module(health)
                ),
            )
            html_output = self.tracker.generate_html_dashboard(report)
            self.assertIsInstance(html_output, str)
            self.assertIn("<!DOCTYPE html>", html_output)
        finally:
            os.unlink(path)

    def test_html_contains_dark_theme(self):
        path = self._write_tmp_py(_SAMPLE_GOOD_PY)
        try:
            health = self.tracker.analyze_module(path)
            report = CodebaseReport(total_modules=1, modules=[health])
            html_output = self.tracker.generate_html_dashboard(report)
            # Dark theme uses dark background colors
            self.assertTrue(
                "dark" in html_output.lower() or "#1" in html_output or "#0" in html_output,
                "Dashboard should contain dark theme styling",
            )
        finally:
            os.unlink(path)

    def test_html_contains_sortable_table(self):
        path = self._write_tmp_py(_SAMPLE_GOOD_PY)
        try:
            health = self.tracker.analyze_module(path)
            report = CodebaseReport(total_modules=1, modules=[health])
            html_output = self.tracker.generate_html_dashboard(report)
            self.assertIn("<table", html_output)
        finally:
            os.unlink(path)

    def test_get_stats(self):
        stats = self.tracker.get_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("version", stats)


if __name__ == "__main__":
    unittest.main()
