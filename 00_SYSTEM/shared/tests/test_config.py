"""
Contract tests for shared.internal.config — Path resolution.

These tests lock the behavior of get_root(), get_brain_dir(), etc.
"""

import os
import sys
from pathlib import Path

import pytest

# Add 00_SYSTEM to path
_system_dir = str(Path(__file__).resolve().parent.parent.parent)
if _system_dir not in sys.path:
    sys.path.insert(0, _system_dir)

from shared import get_root, get_brain_dir, get_engine_dir, get_tools_dir, DB_REGISTRY


class TestGetRoot:
    """Contract: get_root() returns the LitigationOS root directory."""

    def test_returns_path(self):
        """Always returns a Path object."""
        assert isinstance(get_root(), Path)

    def test_root_exists(self):
        """The resolved root directory exists."""
        assert get_root().exists()

    def test_root_is_directory(self):
        """Root is a directory, not a file."""
        assert get_root().is_dir()

    def test_root_contains_canon(self):
        """Root contains _CANON.md (the filesystem law)."""
        assert (get_root() / "_CANON.md").exists()

    def test_env_override(self, tmp_path, monkeypatch):
        """LITIGOS_ROOT env var overrides default."""
        # Create a minimal fake root with _CANON.md so it "looks" valid
        monkeypatch.setenv("LITIGOS_ROOT", str(tmp_path))
        get_root.cache_clear()  # Clear lru_cache so env var takes effect
        try:
            root = get_root()
            assert root == tmp_path
        finally:
            get_root.cache_clear()  # Reset for subsequent tests


class TestDirectoryHelpers:
    """Contract: directory helpers resolve correctly."""

    def test_brain_dir_exists(self):
        brain_dir = get_brain_dir()
        assert brain_dir.exists()
        assert brain_dir.name == "brains"

    def test_engine_dir_exists(self):
        engine_dir = get_engine_dir()
        assert engine_dir.exists()
        assert engine_dir.name == "engines"

    def test_tools_dir_exists(self):
        tools_dir = get_tools_dir()
        assert tools_dir.exists()
        assert tools_dir.name == "tools"


class TestDbRegistry:
    """Contract: DB_REGISTRY maps known databases."""

    def test_has_litigation(self):
        assert "litigation" in DB_REGISTRY

    def test_has_brain_databases(self):
        brains = [k for k in DB_REGISTRY if "brain" in k]
        assert len(brains) >= 5

    def test_litigation_is_context_db(self):
        assert DB_REGISTRY["litigation"] == "litigation_context.db"

    def test_all_values_are_strings(self):
        for name, path in DB_REGISTRY.items():
            assert isinstance(path, str), f"{name} path is not a string"
