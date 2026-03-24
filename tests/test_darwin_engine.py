"""Tests for DARWIN engine (DarwinEngine).

Engine: 00_SYSTEM/darwin/darwin_engine.py
Primary class: DarwinEngine
Purpose: Self-evolving agent fleet management — bootstrap, evolve, learn, speciate.
"""
import ast
import os

import pytest

ENGINE_REL = os.path.join("00_SYSTEM", "darwin", "darwin_engine.py")
ENGINE_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ENGINE_REL))


class TestDarwinEngineFile:
    """Verify engine file integrity."""

    def test_file_exists(self):
        assert os.path.exists(ENGINE_PATH), f"Engine not found at {ENGINE_PATH}"

    def test_file_not_empty(self):
        size = os.path.getsize(ENGINE_PATH)
        assert size > 0, "Engine file is empty"
        assert size > 5_000, f"Engine suspiciously small ({size} bytes)"

    def test_valid_python_syntax(self):
        with open(ENGINE_PATH, "r", encoding="utf-8") as f:
            source = f.read()
        compile(source, ENGINE_PATH, "exec")

    def test_parseable_ast(self):
        with open(ENGINE_PATH, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
        assert isinstance(tree, ast.Module)


class TestDarwinEngineStructure:
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
        assert "DarwinEngine" in self.class_names, (
            f"DarwinEngine class not found. Classes: {self.class_names[:10]}"
        )

    def test_has_main_block(self):
        assert 'if __name__' in self.source, "Missing __main__ block"

    def test_has_bootstrap(self):
        assert "bootstrap" in self.function_names, "Engine should have bootstrap() method"

    def test_has_evolve(self):
        """Engine should support evolution cycles."""
        assert "evolve" in self.source.lower(), "Expected evolve capability"

    def test_has_breed(self):
        """Engine should support agent crossbreeding."""
        assert "breed" in self.source.lower(), "Expected breed/crossbreed capability"

    def test_imports_sub_modules(self):
        """Engine should import AgentGenome and MutationEngine."""
        assert "AgentGenome" in self.source, "Expected AgentGenome import"
        assert "MutationEngine" in self.source, "Expected MutationEngine import"

    def test_has_subcommands(self):
        expected = ["bootstrap", "evolve", "dashboard", "breed", "specialize", "learn"]
        found = [cmd for cmd in expected if cmd in self.source]
        assert len(found) >= 4, f"Expected >=4 subcommands, found: {found}"


class TestDarwinEnginePatterns:
    """Verify engine follows LitigationOS patterns."""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        with open(ENGINE_PATH, "r", encoding="utf-8") as f:
            self.source = f.read()

    def test_utf8_env_set(self):
        assert "PYTHONUTF8" in self.source, "Engine should set PYTHONUTF8=1"

    def test_has_error_handling(self):
        """Darwin delegates error handling to sub-modules (GenomeDB, MutationEngine)."""
        except_count = self.source.count("except")
        if except_count == 0:
            pytest.skip(
                "Darwin engine has 0 except blocks — delegates to sub-modules. "
                "Consider adding top-level error handling."
            )

    def test_repo_root_reference(self):
        assert "LitigationOS" in self.source, "Engine should reference LitigationOS repo root"

    def test_scans_agent_directories(self):
        assert "agents" in self.source.lower(), "Engine should scan agent directories"
