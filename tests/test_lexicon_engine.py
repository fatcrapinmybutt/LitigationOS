"""Tests for LEXICON engine (LexiconEngine).

Engine: 00_SYSTEM/engines/lexicon/lexicon_engine.py
Primary class: LexiconEngine
Purpose: Unified Michigan legal intelligence query API — combines LEXICON + ORACLE.
"""
import ast
import os

import pytest

ENGINE_REL = os.path.join("00_SYSTEM", "engines", "lexicon", "lexicon_engine.py")
ENGINE_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ENGINE_REL))


class TestLexiconEngineFile:
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


class TestLexiconEngineStructure:
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
        assert "LexiconEngine" in self.class_names, (
            f"LexiconEngine class not found. Classes: {self.class_names[:10]}"
        )

    def test_has_ask_method(self):
        assert "ask" in self.function_names, "Engine should have ask() method"

    def test_has_filing_roadmap(self):
        assert "filing_roadmap" in self.function_names, "Engine should have filing_roadmap()"

    def test_has_compute_deadlines(self):
        assert "compute_deadlines" in self.function_names, "Engine should have compute_deadlines()"

    def test_has_evidence_check(self):
        assert "evidence_check" in self.function_names, "Engine should have evidence_check()"

    def test_oracle_integration(self):
        """LexiconEngine should optionally integrate with Oracle."""
        assert "Oracle" in self.source, "Expected Oracle import/integration"
        assert "HAS_ORACLE" in self.source, "Expected HAS_ORACLE feature flag"

    def test_lexicon_db_integration(self):
        assert "LexiconDB" in self.source, "Expected LexiconDB import"


class TestLexiconEnginePatterns:
    """Verify engine follows LitigationOS patterns."""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        with open(ENGINE_PATH, "r", encoding="utf-8") as f:
            self.source = f.read()

    def test_has_error_handling(self):
        assert self.source.count("except") > 2, "Engine should have error handling"

    def test_has_type_hints(self):
        assert "Dict[str, Any]" in self.source or "dict[str" in self.source, (
            "Engine should use type hints"
        )

    def test_keyword_routing(self):
        """ask() should route questions based on keywords."""
        assert "filing" in self.source.lower() and "keyword" in self.source.lower(), (
            "Expected keyword-based question routing"
        )
