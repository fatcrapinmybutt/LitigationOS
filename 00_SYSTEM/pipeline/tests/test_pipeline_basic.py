"""Unit tests for the pipeline configuration module (00_SYSTEM/pipeline/config.py).

Validates that the pipeline config is correctly defined: PHASES list,
MEEK_SIGNALS dict, drive detection, and utility functions.
"""

import os
import re
import sys
import unittest

# UTF-8 stdout for Windows — only when running standalone (not under pytest)
if "pytest" not in sys.modules:
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")

# Add the pipeline directory to sys.path
# Parent dir is the pipeline directory
PIPELINE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, PIPELINE_DIR)


class TestPipelineImport(unittest.TestCase):
    """Verify the config module can be imported without crashing."""

    def test_import_config(self):
        import config
        self.assertTrue(hasattr(config, "PHASES"))
        self.assertTrue(hasattr(config, "MEEK_SIGNALS"))
        self.assertTrue(hasattr(config, "LITIGOS_ROOT"))

    def test_litigos_root_is_path(self):
        from pathlib import Path
        import config
        self.assertIsInstance(config.LITIGOS_ROOT, Path)

    def test_long_path_function_exists(self):
        import config
        self.assertTrue(callable(config.long_path))


class TestPhases(unittest.TestCase):
    """Validate the PHASES registry."""

    def test_phases_is_list(self):
        import config
        self.assertIsInstance(config.PHASES, list)

    def test_phases_not_empty(self):
        import config
        self.assertGreater(len(config.PHASES), 10,
                           "Expected at least 10 pipeline phases")

    def test_phases_has_24_entries(self):
        import config
        self.assertEqual(len(config.PHASES), 24,
                         f"Expected 24 phases, got {len(config.PHASES)}")

    def test_phase_tuple_structure(self):
        """Each phase entry should be a 3-tuple: (id, module, description)."""
        import config
        for phase in config.PHASES:
            self.assertIsInstance(phase, tuple, f"Phase entry is not a tuple: {phase}")
            self.assertEqual(len(phase), 3,
                             f"Phase tuple should have 3 elements: {phase}")
            phase_id, module_name, description = phase
            self.assertIsInstance(phase_id, str)
            self.assertIsInstance(module_name, str)
            self.assertIsInstance(description, str)

    def test_known_phases_present(self):
        """Verify critical phases exist by ID."""
        import config
        phase_ids = {p[0] for p in config.PHASES}
        for expected_id in ["0", "1", "2", "3", "4a", "5", "6", "7a", "8", "9", "16"]:
            self.assertIn(expected_id, phase_ids,
                          f"Phase {expected_id} not found in PHASES")

    def test_phase_ids_unique(self):
        import config
        phase_ids = [p[0] for p in config.PHASES]
        self.assertEqual(len(phase_ids), len(set(phase_ids)),
                         "Duplicate phase IDs found")

    def test_phase_modules_unique(self):
        import config
        modules = [p[1] for p in config.PHASES]
        self.assertEqual(len(modules), len(set(modules)),
                         "Duplicate module names found")


class TestMeekSignals(unittest.TestCase):
    """Validate the MEEK_SIGNALS lane detection dict."""

    def test_meek_signals_is_dict(self):
        import config
        self.assertIsInstance(config.MEEK_SIGNALS, dict)

    def test_meek_signals_has_5_lanes(self):
        import config
        self.assertEqual(len(config.MEEK_SIGNALS), 5,
                         f"Expected 5 MEEK lanes, got {len(config.MEEK_SIGNALS)}")

    def test_meek_signal_keys(self):
        import config
        expected = {"MEEK1", "MEEK2", "MEEK3", "MEEK4", "MEEK5"}
        self.assertEqual(set(config.MEEK_SIGNALS.keys()), expected)

    def test_meek_signals_are_compiled_regex(self):
        import config
        for key, pattern in config.MEEK_SIGNALS.items():
            self.assertIsInstance(pattern, re.Pattern,
                                 f"{key} is not a compiled regex: {type(pattern)}")

    def test_meek1_matches_housing(self):
        """MEEK1 = Shady Oaks Housing lane."""
        import config
        pattern = config.MEEK_SIGNALS["MEEK1"]
        self.assertIsNotNone(pattern.search("shady oaks"))
        self.assertIsNotNone(pattern.search("landlord tenant dispute"))
        self.assertIsNotNone(pattern.search("MCL 554"))

    def test_meek2_matches_custody(self):
        """MEEK2 = Watson Custody lane."""
        import config
        pattern = config.MEEK_SIGNALS["MEEK2"]
        self.assertIsNotNone(pattern.search("custody agreement"))
        self.assertIsNotNone(pattern.search("parenting time"))
        self.assertIsNotNone(pattern.search("MCR 3.206"))

    def test_meek3_matches_ppo(self):
        """MEEK3 = PPO / Protection Orders lane."""
        import config
        pattern = config.MEEK_SIGNALS["MEEK3"]
        self.assertIsNotNone(pattern.search("PPO"))
        self.assertIsNotNone(pattern.search("protection order"))
        self.assertIsNotNone(pattern.search("MCL 600.2950"))

    def test_meek4_matches_misconduct(self):
        """MEEK4 = Judicial Misconduct lane."""
        import config
        pattern = config.MEEK_SIGNALS["MEEK4"]
        self.assertIsNotNone(pattern.search("judicial misconduct"))
        self.assertIsNotNone(pattern.search("MCR 2.003"))
        self.assertIsNotNone(pattern.search("disqualification"))

    def test_meek5_matches_appellate(self):
        """MEEK5 = Appellate lane."""
        import config
        pattern = config.MEEK_SIGNALS["MEEK5"]
        self.assertIsNotNone(pattern.search("appellate"))
        self.assertIsNotNone(pattern.search("COA"))
        self.assertIsNotNone(pattern.search("MCR 7.212"))

    def test_meek_no_false_positives(self):
        """Generic text should not match any MEEK signal."""
        import config
        generic = "Today is a sunny day in Michigan."
        for key, pattern in config.MEEK_SIGNALS.items():
            self.assertIsNone(pattern.search(generic),
                              f"{key} false-positive on generic text")


class TestLongPath(unittest.TestCase):
    """Test the Windows long path helper."""

    def test_long_path_adds_prefix(self):
        import config
        result = config.long_path(r"C:\Users\test\file.txt")
        self.assertTrue(result.startswith("\\\\?\\"))

    def test_long_path_no_double_prefix(self):
        import config
        already = "\\\\?\\C:\\Users\\test\\file.txt"
        result = config.long_path(already)
        self.assertFalse(result.startswith("\\\\?\\\\\\?\\"))

    def test_long_path_accepts_pathlib(self):
        from pathlib import Path
        import config
        result = config.long_path(Path(r"C:\test"))
        self.assertIsInstance(result, str)


class TestPipelineLogger(unittest.TestCase):
    """Test the PipelineLogger class."""

    def test_pipeline_logger_creation(self):
        import config
        logger = config.PipelineLogger("test_phase")
        self.assertIsNotNone(logger)

    def test_pipeline_logger_with_cycle_dir(self):
        import config
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            logger = config.PipelineLogger("test_phase", cycle_dir=config.Path(td))
            logger.info("test message")
            log_path = config.Path(td) / "pipeline.log.jsonl"
            self.assertTrue(log_path.exists())


class TestMasterModifiable(unittest.TestCase):
    """Validate MASTER_MODIFIABLE list."""

    def test_master_modifiable_is_list(self):
        import config
        self.assertIsInstance(config.MASTER_MODIFIABLE, list)

    def test_master_modifiable_not_empty(self):
        import config
        self.assertGreater(len(config.MASTER_MODIFIABLE), 0)

    def test_master_modifiable_entries_are_strings(self):
        import config
        for entry in config.MASTER_MODIFIABLE:
            self.assertIsInstance(entry, str)


if __name__ == "__main__":
    unittest.main(verbosity=2)
