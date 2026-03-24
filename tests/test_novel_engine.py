"""Tests for NOVEL engine (NovelEngine).

Engine: 00_SYSTEM/novel/novel_engine.py
Primary class: NovelEngine
Purpose: Invention engine — perceive gaps, brainstorm, forge prototypes, validate, evolve.
"""
import ast
import os

import pytest

ENGINE_REL = os.path.join("00_SYSTEM", "novel", "novel_engine.py")
ENGINE_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ENGINE_REL))


class TestNovelEngineFile:
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


class TestNovelEngineStructure:
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
        assert "NovelEngine" in self.class_names, (
            f"NovelEngine class not found. Classes: {self.class_names[:10]}"
        )

    def test_has_main_block(self):
        assert 'if __name__' in self.source, "Missing __main__ block"

    def test_has_subcommands(self):
        """Engine supports CLI subcommands (perceive, scan, brainstorm, etc.)."""
        expected = ["perceive", "scan", "brainstorm", "invent", "forge", "validate"]
        found = [cmd for cmd in expected if cmd in self.source]
        assert len(found) >= 4, f"Expected >=4 subcommands, found: {found}"

    def test_imports_sub_modules(self):
        """Engine should import from novel sub-package (genome, creativity, perception, etc.)."""
        sub_modules = ["invention_genome", "creativity_engine", "perception", "validator", "composer"]
        found = [m for m in sub_modules if m in self.source]
        assert len(found) >= 3, f"Expected >=3 sub-module imports, found: {found}"

    def test_has_evolution_lifecycle(self):
        """v2 lifecycle: Perceive → Scan → Imagine → Forge → Validate → Compose → Evolve → Spawn."""
        lifecycle = ["perceive", "validate", "compose", "evolve"]
        found = [step for step in lifecycle if step in self.source.lower()]
        assert len(found) >= 3, f"Expected >=3 lifecycle steps, found: {found}"


class TestNovelEnginePatterns:
    """Verify engine follows LitigationOS patterns."""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        with open(ENGINE_PATH, "r", encoding="utf-8") as f:
            self.source = f.read()

    def test_utf8_env_set(self):
        assert "PYTHONUTF8" in self.source, "Engine should set PYTHONUTF8=1"

    def test_has_error_handling(self):
        assert self.source.count("except") > 2, "Engine should have error handling"

    def test_invention_db_integration(self):
        assert "InventionDB" in self.source, "Engine should use InventionDB for persistence"
