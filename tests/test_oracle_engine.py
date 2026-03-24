"""Tests for ORACLE engine (Oracle).

Engine: 00_SYSTEM/engines/oracle/oracle_engine.py
Primary class: Oracle
Purpose: Michigan rule reasoning — filing checklists, computed deadlines, required forms.
"""
import ast
import os

import pytest

ENGINE_REL = os.path.join("00_SYSTEM", "engines", "oracle", "oracle_engine.py")
ENGINE_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ENGINE_REL))


class TestOracleEngineFile:
    """Verify engine file integrity."""

    def test_file_exists(self):
        assert os.path.exists(ENGINE_PATH), f"Engine not found at {ENGINE_PATH}"

    def test_file_not_empty(self):
        size = os.path.getsize(ENGINE_PATH)
        assert size > 0, "Engine file is empty"
        assert size > 10_000, f"Engine suspiciously small ({size} bytes)"

    def test_valid_python_syntax(self):
        with open(ENGINE_PATH, "r", encoding="utf-8") as f:
            source = f.read()
        compile(source, ENGINE_PATH, "exec")

    def test_parseable_ast(self):
        with open(ENGINE_PATH, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
        assert isinstance(tree, ast.Module)


class TestOracleEngineStructure:
    """Verify engine defines expected classes and methods."""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        with open(ENGINE_PATH, "r", encoding="utf-8") as f:
            self.source = f.read()
        self.tree = ast.parse(self.source)
        self.class_names = [
            node.name for node in ast.walk(self.tree) if isinstance(node, ast.ClassDef)
        ]
        self.function_names = [
            node.name for node in ast.walk(self.tree) if isinstance(node, ast.FunctionDef)
        ]

    def test_has_main_class(self):
        assert "Oracle" in self.class_names, (
            f"Oracle class not found. Classes: {self.class_names[:10]}"
        )

    def test_has_main_block(self):
        assert 'if __name__' in self.source, "Missing __main__ block"

    def test_has_get_roadmap(self):
        assert "get_roadmap" in self.function_names, "Oracle should have get_roadmap()"

    def test_has_compute_deadlines(self):
        assert "compute_deadlines" in self.function_names, "Oracle should have compute_deadlines()"

    def test_has_get_checklist(self):
        assert "get_checklist" in self.function_names, "Oracle should have get_checklist()"

    def test_has_cli_subcommands(self):
        expected = ["roadmap", "deadlines", "checklist", "forms", "service", "risks"]
        found = [cmd for cmd in expected if cmd in self.source]
        assert len(found) >= 4, f"Expected >=4 CLI subcommands, found: {found}"

    def test_lane_data_integrity(self):
        """Oracle must have verified lane data — no fabricated info."""
        assert "2024-001507-DC" in self.source, "Lane A case number missing"
        assert "Emily A. Watson" in self.source, "Lane A opposing party missing"
        assert "Jenny L. McNeill" in self.source, "Judge name missing or wrong"

    def test_no_fabricated_parties(self):
        """Ensure no hallucinated party names exist."""
        assert "Jane Berry" not in self.source, "Hallucinated party: Jane Berry"
        assert "Patricia Berry" not in self.source, "Hallucinated party: Patricia Berry"


class TestOracleEnginePatterns:
    """Verify engine follows LitigationOS patterns."""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        with open(ENGINE_PATH, "r", encoding="utf-8") as f:
            self.source = f.read()

    def test_has_error_handling(self):
        assert self.source.count("except") > 2, "Engine should have error handling"

    def test_uses_sqlite(self):
        assert "sqlite3" in self.source, "Oracle should use SQLite for rule storage"

    def test_deadline_calculator_integration(self):
        assert "DeadlineCalculator" in self.source, "Expected DeadlineCalculator integration"

    def test_michigan_calendar_integration(self):
        assert "MichiganCalendar" in self.source, "Expected MichiganCalendar integration"

    def test_has_type_hints(self):
        assert "Dict[str, Any]" in self.source or "dict[str" in self.source
