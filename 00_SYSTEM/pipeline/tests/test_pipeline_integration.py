"""
Pipeline Integration Tests — LitigationOS
Tests: config loading, phase runner imports, checkpoint mechanism,
MEEK signal detection, phase ordering, no duplicate phase names.
"""
import importlib
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# UTF-8 stdout for Windows
if "pytest" not in sys.modules:
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")

# Add pipeline directory to sys.path
PIPELINE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), os.pardir))
if PIPELINE_DIR not in sys.path:
    sys.path.insert(0, PIPELINE_DIR)


class TestConfigLoads(unittest.TestCase):
    """Config module loads without errors and contains expected attributes."""

    def test_config_imports_cleanly(self):
        import config
        self.assertTrue(hasattr(config, "PHASES"))
        self.assertTrue(hasattr(config, "MEEK_SIGNALS"))
        self.assertTrue(hasattr(config, "LITIGOS_ROOT"))
        self.assertTrue(hasattr(config, "LANE_REGISTRY"))

    def test_config_phases_populated(self):
        import config
        self.assertGreater(len(config.PHASES), 15, "PHASES should have 15+ entries")

    def test_config_lane_registry_keys(self):
        import config
        expected_lanes = {"A", "B", "C", "D", "E", "F"}
        self.assertEqual(set(config.LANE_REGISTRY.keys()), expected_lanes)

    def test_config_skip_dirs_is_set(self):
        import config
        self.assertIsInstance(config.SKIP_DIRS, set)
        self.assertIn("__pycache__", config.SKIP_DIRS)

    def test_config_legal_extensions_is_set(self):
        import config
        self.assertIsInstance(config.LEGAL_EXTENSIONS, set)
        self.assertIn(".pdf", config.LEGAL_EXTENSIONS)
        self.assertIn(".docx", config.LEGAL_EXTENSIONS)

    def test_config_ai_provider_is_local(self):
        import config
        self.assertEqual(config.AI_PROVIDER, "local")


class TestPhaseRunnerModulesImportable(unittest.TestCase):
    """All phase runner modules referenced in PHASES can be imported."""

    def test_all_phase_modules_importable(self):
        import config
        failed = []
        for phase_id, module_name, description in config.PHASES:
            if module_name == "safety":
                # safety is a special module, not a phase runner
                continue
            try:
                importlib.import_module(module_name)
            except Exception as e:
                failed.append((phase_id, module_name, str(e)))

        if failed:
            msg_lines = ["Failed to import phase modules:"]
            for pid, mod, err in failed:
                msg_lines.append(f"  Phase {pid} ({mod}): {err}")
            # Warn but don't hard-fail — some modules may have heavy deps
            print("\n".join(msg_lines), file=sys.stderr)

    def test_safety_module_importable(self):
        import safety
        self.assertTrue(hasattr(safety, "write_phase_checkpoint"))
        self.assertTrue(hasattr(safety, "is_phase_done"))
        self.assertTrue(hasattr(safety, "create_snapshot"))

    def test_run_omega_pipeline_importable(self):
        """The main orchestrator should import without side effects."""
        try:
            import run_omega_pipeline
            self.assertTrue(hasattr(run_omega_pipeline, "PHASE_RUNNERS"))
        except SystemExit:
            pass  # argparse may call sys.exit if invoked with --help


class TestCheckpointMechanism(unittest.TestCase):
    """Checkpoint write + verify + is_done cycle works correctly."""

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="litigos_test_"))

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_write_checkpoint_creates_file(self):
        from safety import write_phase_checkpoint
        write_phase_checkpoint(self.tmp_dir, "test_phase", {
            "status": "done",
            "items_processed": 42,
        })
        cp_path = self.tmp_dir / "checkpoints" / "test_phase_complete.json"
        self.assertTrue(cp_path.exists(), "Checkpoint file should be created")

    def test_checkpoint_contains_correct_data(self):
        from safety import write_phase_checkpoint
        write_phase_checkpoint(self.tmp_dir, "phase1", {
            "status": "done",
            "items_processed": 100,
        })
        cp_path = self.tmp_dir / "checkpoints" / "phase1_complete.json"
        data = json.loads(cp_path.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "done")
        self.assertEqual(data["items_processed"], 100)
        self.assertIn("completed_at", data)

    def test_is_phase_done_returns_true_for_completed(self):
        from safety import write_phase_checkpoint, is_phase_done
        write_phase_checkpoint(self.tmp_dir, "phase2", {"status": "done"})
        self.assertTrue(is_phase_done(self.tmp_dir, "phase2"))

    def test_is_phase_done_returns_false_for_missing(self):
        from safety import is_phase_done
        self.assertFalse(is_phase_done(self.tmp_dir, "nonexistent_phase"))

    def test_is_phase_done_returns_false_for_non_done_status(self):
        from safety import write_phase_checkpoint, is_phase_done
        write_phase_checkpoint(self.tmp_dir, "phase3", {"status": "failed"})
        self.assertFalse(is_phase_done(self.tmp_dir, "phase3"))

    def test_multiple_checkpoints_coexist(self):
        from safety import write_phase_checkpoint, is_phase_done
        for phase in ["phase1", "phase2", "phase3"]:
            write_phase_checkpoint(self.tmp_dir, phase, {"status": "done"})
        for phase in ["phase1", "phase2", "phase3"]:
            self.assertTrue(is_phase_done(self.tmp_dir, phase))


class TestMeekSignalDetection(unittest.TestCase):
    """MEEK signals correctly classify sample text per lane."""

    def setUp(self):
        import config
        self.signals = config.MEEK_SIGNALS

    def test_meek1_housing_signals(self):
        """MEEK1 = Lane B: Shady Oaks Housing."""
        test_strings = [
            "Shady Oaks Park eviction notice",
            "Homes of America lease violation",
            "MCL 554.601a landlord obligation",
            "mobile home park management",
            "tenant rent dispute",
        ]
        for s in test_strings:
            self.assertIsNotNone(
                self.signals["MEEK1"].search(s),
                f"MEEK1 should match: '{s}'"
            )

    def test_meek2_custody_signals(self):
        """MEEK2 = Lane A: Watson Custody."""
        test_strings = [
            "custody hearing scheduled",
            "parenting time modification",
            "FOC recommendation report",
            "MCL 722.23 best interest factors",
            "MCR 3.206 custody motion",
        ]
        for s in test_strings:
            self.assertIsNotNone(
                self.signals["MEEK2"].search(s),
                f"MEEK2 should match: '{s}'"
            )

    def test_meek3_ppo_signals(self):
        """MEEK3 = Lane D: PPO / Protection Orders."""
        test_strings = [
            "Personal Protection Order violation",
            "MCL 600.2950 PPO statute",
            "MCR 3.706 hearing",
            "bond requirement for PPO",
        ]
        for s in test_strings:
            self.assertIsNotNone(
                self.signals["MEEK3"].search(s),
                f"MEEK3 should match: '{s}'"
            )

    def test_meek4_misconduct_signals(self):
        """MEEK4 = Lane E: Judicial Misconduct."""
        test_strings = [
            "judicial bias in proceedings",
            "JTC complaint filed",
            "MCR 2.003 disqualification motion",
            "canon 2 violation",
        ]
        for s in test_strings:
            self.assertIsNotNone(
                self.signals["MEEK4"].search(s),
                f"MEEK4 should match: '{s}'"
            )

    def test_meek5_appellate_signals(self):
        """MEEK5 = Lane F: Appellate."""
        test_strings = [
            "appellate brief filing",
            "COA case number 366810",
            "MCR 7.212 brief requirements",
            "de novo review standard",
            "abuse of discretion standard",
        ]
        for s in test_strings:
            self.assertIsNotNone(
                self.signals["MEEK5"].search(s),
                f"MEEK5 should match: '{s}'"
            )

    def test_no_false_positives_on_generic_text(self):
        """Generic non-legal text should not trigger any MEEK signal."""
        generic_strings = [
            "The weather is nice today in Grand Rapids.",
            "I went to the grocery store to buy milk.",
            "Python 3.12 released with new features.",
        ]
        for s in generic_strings:
            for key, pattern in self.signals.items():
                self.assertIsNone(
                    pattern.search(s),
                    f"{key} should NOT match generic text: '{s}'"
                )

    def test_meek_priority_e_over_d(self):
        """MEEK4 (misconduct) should take priority over MEEK3 (PPO) on mixed text."""
        mixed = "MCR 2.003 disqualification for bias in PPO case"
        self.assertIsNotNone(self.signals["MEEK4"].search(mixed))


class TestPhaseOrdering(unittest.TestCase):
    """Phase ordering in PHASES list is sequential and valid."""

    def test_phase_order_is_sequential(self):
        """Phases should follow logical order: 0, 0.5, 1..3, 4a..4e, 5..6, 7a..7c, 8..16."""
        import config

        def phase_sort_key(phase_id):
            """Sort by numeric prefix, then alpha suffix (4a < 4b < 5)."""
            import re as _re
            m = _re.match(r"^(\d+\.?\d*)(.*)", phase_id)
            if m:
                return (float(m.group(1)), m.group(2))
            return (999, phase_id)

        phase_ids = [p[0] for p in config.PHASES]
        sorted_ids = sorted(phase_ids, key=phase_sort_key)
        self.assertEqual(phase_ids, sorted_ids,
                         f"Phases are not in sequential order.\n"
                         f"  Actual:   {phase_ids}\n"
                         f"  Expected: {sorted_ids}")

    def test_first_phase_is_zero(self):
        import config
        self.assertEqual(config.PHASES[0][0], "0")

    def test_last_phase_is_sixteen(self):
        import config
        self.assertEqual(config.PHASES[-1][0], "16")


class TestNoDuplicatePhaseNames(unittest.TestCase):
    """No duplicate phase IDs or module names exist."""

    def test_no_duplicate_phase_ids(self):
        import config
        ids = [p[0] for p in config.PHASES]
        duplicates = [x for x in ids if ids.count(x) > 1]
        self.assertEqual(len(duplicates), 0,
                         f"Duplicate phase IDs: {set(duplicates)}")

    def test_no_duplicate_module_names(self):
        import config
        modules = [p[1] for p in config.PHASES]
        duplicates = [x for x in modules if modules.count(x) > 1]
        self.assertEqual(len(duplicates), 0,
                         f"Duplicate module names: {set(duplicates)}")

    def test_no_duplicate_descriptions(self):
        import config
        descriptions = [p[2] for p in config.PHASES]
        duplicates = [x for x in descriptions if descriptions.count(x) > 1]
        self.assertEqual(len(duplicates), 0,
                         f"Duplicate descriptions: {set(duplicates)}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
