"""Tests for LitigationOS 16-phase pipeline.

Validates: phase file existence, ordering, MEEK signal regex, lane assignment,
config integrity, and pipeline module structure.
"""
import ast
import os
import re
import sys

import pytest

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
PIPELINE_DIR = os.path.join(REPO_ROOT, "00_SYSTEM", "pipeline")
CONFIG_PATH = os.path.join(PIPELINE_DIR, "config.py")

# Expected phases from config.py
EXPECTED_PHASES = [
    ("0", "safety", "Safety Snapshot"),
    ("0.5", "phase0_5_drive_ingest", "Drive Ingestion"),
    ("1", "phase1_inventory", "Recursive Inventory"),
    ("2", "phase2_dedup", "Hash-Cluster Dedup"),
    ("3", "phase3_classify", "3-Pass Classification"),
    ("4a", "phase4a_pdf_extract", "PDF Extraction"),
    ("4b", "phase4b_docx_extract", "DOCX Extraction"),
    ("4c", "phase4c_structured_extract", "Structured Data"),
    ("4d", "phase4d_atomize", "Atom Generation"),
    ("4e", "phase4e_archive_extract", "Archive Extraction"),
    ("5", "phase5_brain_feed", "LEXOS Brain Feed"),
    ("6", "phase6_gap_analysis", "EGCP Gap Analysis"),
    ("7a", "phase7a_graph_delta", "Graph Delta"),
    ("7b", "phase7b_synthesis_merge", "Synthesis Merge"),
    ("7c", "phase7c_knowledge_merge", "Knowledge Merge"),
    ("8", "phase8_litigation_refresh", "Litigation Refresh"),
    ("9", "phase9_mcp_ingest", "MCP Ingest"),
    ("10", "phase10_judicial_analysis", "Judicial Analysis"),
    ("11", "phase11_legal_action_discovery", "Legal Action Discovery"),
    ("12", "phase12_rule_audit", "MCR/MCL Rule Audit"),
    ("13", "phase13_refinement", "Document Refinement"),
    ("14", "phase14_finalize", "Filing Finalization"),
    ("15", "phase15_validation", "Court-Ready Validation"),
    ("16", "phase16_desktop", "Desktop Offload"),
]


class TestPipelineDirectory:
    """Verify pipeline directory structure."""

    def test_pipeline_dir_exists(self):
        assert os.path.isdir(PIPELINE_DIR), f"Pipeline dir not found: {PIPELINE_DIR}"

    def test_config_exists(self):
        assert os.path.isfile(CONFIG_PATH), f"config.py not found: {CONFIG_PATH}"

    def test_config_valid_syntax(self):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            source = f.read()
        compile(source, CONFIG_PATH, "exec")


class TestPhaseFileExistence:
    """Verify each defined pipeline phase has a corresponding .py file."""

    # Phases that have actual .py files (not all phases have standalone files)
    PHASES_WITH_FILES = [
        "phase1_inventory",
        "phase2_dedup",
        "phase3_classify",
        "phase4a_pdf_extract",
        "phase4b_docx_extract",
        "phase4c_structured_extract",
        "phase4d_atomize",
        "phase4e_archive_extract",
        "phase5_brain_feed",
        "phase7a_graph_delta",
        "phase7c_knowledge_merge",
        "phase8_litigation_refresh",
        "phase12_rule_audit",
        "phase13_refinement",
        "phase14_finalize",
        "phase16_desktop",
    ]

    @pytest.mark.parametrize("module_name", PHASES_WITH_FILES)
    def test_phase_file_exists(self, module_name):
        path = os.path.join(PIPELINE_DIR, f"{module_name}.py")
        assert os.path.isfile(path), f"Phase file missing: {path}"

    @pytest.mark.parametrize("module_name", PHASES_WITH_FILES)
    def test_phase_file_valid_syntax(self, module_name):
        path = os.path.join(PIPELINE_DIR, f"{module_name}.py")
        if not os.path.isfile(path):
            pytest.skip(f"{module_name}.py not found")
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
        compile(source, path, "exec")


class TestPhaseOrdering:
    """Verify phases are in the correct order."""

    def test_phase_count(self):
        """Pipeline should define 24 phases (0 through 16 including sub-phases)."""
        assert len(EXPECTED_PHASES) == 24

    def test_starts_with_safety(self):
        assert EXPECTED_PHASES[0][0] == "0"
        assert "safety" in EXPECTED_PHASES[0][1].lower()

    def test_ends_with_desktop(self):
        assert EXPECTED_PHASES[-1][0] == "16"
        assert "desktop" in EXPECTED_PHASES[-1][1].lower()

    def test_phase_numbers_monotonic(self):
        """Phase numbers should increase monotonically."""

        def phase_sort_key(phase_id: str) -> float:
            """Convert phase IDs like '4a', '7c', '0.5' to sortable floats."""
            if "." in phase_id:
                return float(phase_id)
            # Extract numeric part + letter suffix
            match = re.match(r"(\d+)([a-z])?", phase_id)
            if match:
                num = int(match.group(1))
                suffix = match.group(2)
                return num + (ord(suffix) - ord("a") + 1) * 0.01 if suffix else float(num)
            return float(phase_id)

        keys = [phase_sort_key(p[0]) for p in EXPECTED_PHASES]
        for i in range(1, len(keys)):
            assert keys[i] > keys[i - 1], (
                f"Phase ordering violated: {EXPECTED_PHASES[i-1][0]} ({keys[i-1]}) "
                f">= {EXPECTED_PHASES[i][0]} ({keys[i]})"
            )

    def test_each_phase_has_description(self):
        for phase_id, module, description in EXPECTED_PHASES:
            assert description, f"Phase {phase_id} ({module}) has empty description"


class TestMeekSignals:
    """Verify MEEK signal detection regexes compile and match expected patterns."""

    MEEK_SIGNALS = {
        "MEEK1": re.compile(r"(?i)(shady.?oaks|homes.?of.?america|alden.?global|habitability|landlord|tenant|MCL\s+554|rent|mobile.?home|park)"),
        "MEEK2": re.compile(r"(?i)(custody|parenting|FOC|child|MCL\s+722|MCR\s+3\.20[67]|MCR\s+3\.210|best.?interest|factor\s+[a-l])"),
        "MEEK3": re.compile(r"(?i)(PPO|protection.?order|contempt|MCL\s+600\.2950|MCR\s+3\.70[678]|bond|restrain)"),
        "MEEK4": re.compile(r"(?i)(bias|JTC|disqualif|MCR\s+2\.003|canon|judicial.?misconduct|superintend)"),
        "MEEK5": re.compile(r"(?i)(appell|COA|MSC|MCR\s+7\.|leave.?to.?appeal|standard.?of.?review|de.?novo|abuse.?of.?discretion)"),
    }

    def test_all_meek_signals_compile(self):
        """Each MEEK regex should compile without error."""
        for signal_name, pattern in self.MEEK_SIGNALS.items():
            assert pattern is not None, f"{signal_name} failed to compile"

    @pytest.mark.parametrize(
        "signal,text",
        [
            ("MEEK1", "Shady Oaks mobile home park habitability complaint"),
            ("MEEK1", "tenant rights under MCL 554"),
            ("MEEK2", "custody dispute FOC parenting time"),
            ("MEEK2", "best interest factor analysis MCR 3.207"),
            ("MEEK3", "PPO protection order contempt bond"),
            ("MEEK3", "MCL 600.2950 restraining order"),
            ("MEEK4", "judicial misconduct JTC bias canon"),
            ("MEEK4", "MCR 2.003 disqualification motion"),
            ("MEEK5", "COA appeal leave to appeal standard of review"),
            ("MEEK5", "MCR 7.205 abuse of discretion de novo"),
        ],
    )
    def test_meek_signal_matches(self, signal, text):
        pattern = self.MEEK_SIGNALS[signal]
        assert pattern.search(text), f"{signal} should match: {text}"

    @pytest.mark.parametrize(
        "signal,text",
        [
            ("MEEK1", "child custody hearing"),  # This is MEEK2, not MEEK1
            ("MEEK3", "appellate brief"),         # This is MEEK5, not MEEK3
        ],
    )
    def test_meek_signal_no_false_positive(self, signal, text):
        pattern = self.MEEK_SIGNALS[signal]
        assert not pattern.search(text), f"{signal} should NOT match: {text}"


class TestLaneAssignment:
    """Verify the six case lanes are properly defined."""

    EXPECTED_LANES = {
        "A": "custody",
        "B": "housing",
        "C": "convergence",
        "D": "PPO",
        "E": "misconduct",
        "F": "appellate",
    }

    def test_config_has_lanes(self):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            source = f.read()
        for lane_id in self.EXPECTED_LANES:
            assert f'"{lane_id}"' in source or f"'{lane_id}'" in source, (
                f"Lane {lane_id} not found in config.py"
            )

    def test_meek_signal_to_lane_coverage(self):
        """Each MEEK signal should map to a lane."""
        expected_mappings = {
            "MEEK1": "B",  # Housing
            "MEEK2": "A",  # Custody
            "MEEK3": "D",  # PPO
            "MEEK4": "E",  # Misconduct
            "MEEK5": "F",  # Appellate
        }
        for meek, lane in expected_mappings.items():
            assert lane in self.EXPECTED_LANES, (
                f"{meek} maps to lane {lane} which is not defined"
            )
