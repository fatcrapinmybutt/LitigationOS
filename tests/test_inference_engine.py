"""Tests for MANBEARPIG inference engine (MichiganLegalModel).

Engine: 00_SYSTEM/local_model/inference_engine.py
Primary class: MichiganLegalModel
Purpose: 100% local Michigan legal LLM — TF-IDF + Naive Bayes + BM25
"""
import ast
import os
import re
import sys

import pytest

ENGINE_REL = os.path.join("00_SYSTEM", "local_model", "inference_engine.py")
ENGINE_PATH = os.path.join(os.path.dirname(__file__), "..", ENGINE_REL)
ENGINE_PATH = os.path.normpath(ENGINE_PATH)


class TestInferenceEngineFile:
    """Verify engine file integrity."""

    def test_file_exists(self):
        assert os.path.exists(ENGINE_PATH), f"Engine not found at {ENGINE_PATH}"

    def test_file_not_empty(self):
        size = os.path.getsize(ENGINE_PATH)
        assert size > 0, "Engine file is empty"
        assert size > 10_000, f"Engine suspiciously small ({size} bytes) — expected >10KB"

    def test_valid_python_syntax(self):
        with open(ENGINE_PATH, "r", encoding="utf-8") as f:
            source = f.read()
        compile(source, ENGINE_PATH, "exec")

    def test_parseable_ast(self):
        with open(ENGINE_PATH, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
        assert isinstance(tree, ast.Module)


class TestInferenceEngineStructure:
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
        assert "MichiganLegalModel" in self.class_names, (
            f"MichiganLegalModel class not found. Classes: {self.class_names[:10]}"
        )

    def test_has_query_method(self):
        assert "query" in self.function_names, "query() method not found"

    def test_has_main_block(self):
        assert 'if __name__' in self.source, "Missing if __name__ == '__main__' block"

    def test_no_remote_providers(self):
        """Engine must be 100% local — no remote API calls."""
        dangerous = ["openai", "anthropic", "requests.post", "httpx"]
        for pattern in dangerous:
            # Allow in comments/strings but not as actual imports
            imports = [
                node for node in ast.walk(self.tree)
                if isinstance(node, (ast.Import, ast.ImportFrom))
            ]
            for imp in imports:
                if isinstance(imp, ast.Import):
                    for alias in imp.names:
                        assert pattern not in alias.name.lower(), (
                            f"Remote provider import detected: {alias.name}"
                        )
                elif isinstance(imp, ast.ImportFrom) and imp.module:
                    assert pattern not in imp.module.lower(), (
                        f"Remote provider import detected: {imp.module}"
                    )

    def test_uses_local_model_dir(self):
        assert "MODEL_DIR" in self.source or "model_data" in self.source, (
            "Engine should reference local model directory"
        )

    def test_has_cycle_method_integration(self):
        """Engine should use cycle_method for safe stdout output."""
        assert "cycle_" in self.source, "Expected cycle_method integration (cycle_json/cycle_print)"


class TestInferenceEnginePatterns:
    """Verify engine follows LitigationOS patterns."""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        with open(ENGINE_PATH, "r", encoding="utf-8") as f:
            self.source = f.read()

    def test_utf8_stdout_safety(self):
        """Engine should set UTF-8 stdout in __main__ block."""
        assert "encoding='utf-8'" in self.source or 'encoding="utf-8"' in self.source

    def test_has_error_handling(self):
        assert self.source.count("except") > 5, "Engine should have robust error handling"

    def test_has_logging(self):
        assert "logging" in self.source, "Engine should use logging module"

    def test_has_db_path(self):
        assert "litigation_context.db" in self.source, "Engine should reference central DB"

    def test_skill_count_documented(self):
        """Docstring claims 30+ skills — verify some are defined."""
        skill_indicators = re.findall(r'(?:skill|SKILL|method_map|RPC_METHODS)', self.source)
        assert len(skill_indicators) > 0, "Expected skill/method registry in engine"
