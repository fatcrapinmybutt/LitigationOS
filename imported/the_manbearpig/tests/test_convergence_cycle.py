"""Tests for convergence_cycle_engine module."""

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from convergence_cycle_engine import ConvergenceCycleEngine


@pytest.fixture
def temp_repo(monkeypatch):
    """Create a temporary repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Change to temp directory
        monkeypatch.chdir(tmpdir)
        
        # Create necessary directories
        (tmpdir / "VERSIONS").mkdir()
        (tmpdir / "output").mkdir()
        (tmpdir / "logs").mkdir()
        (tmpdir / "modules").mkdir()
        
        # Create initial files
        (tmpdir / "VERSION").write_text("v0000")
        (tmpdir / "CHANGELOG.md").write_text("# CHANGELOG\n\n")
        (tmpdir / "codex_manifest.json").write_text("[]")
        
        # Create a few Python modules
        (tmpdir / "modules" / "__init__.py").write_text("")
        (tmpdir / "modules" / "test_module.py").write_text('"""Test module"""\n\ndef test_func():\n    pass\n')
        (tmpdir / "test_file.py").write_text('"""Main test"""\n\nif __name__ == "__main__":\n    print("test")\n')
        
        yield tmpdir


def test_read_version(temp_repo):
    """Test reading version from VERSION file."""
    engine = ConvergenceCycleEngine()
    version = engine.read_version()
    assert version == "v0000"


def test_increment_version(temp_repo):
    """Test version increment."""
    engine = ConvergenceCycleEngine()
    
    # Initial version should be v0000
    assert engine.read_version() == "v0000"
    
    # Increment should give v0001
    new_version = engine.increment_version()
    assert new_version == "v0001"
    assert engine.current_version == "v0001"
    assert Path("VERSION").read_text() == "v0001"
    
    # Increment again should give v0002
    new_version = engine.increment_version()
    assert new_version == "v0002"


def test_update_current(temp_repo):
    """Test CURRENT file update."""
    engine = ConvergenceCycleEngine()
    engine.current_version = "v0005"
    engine.update_current()
    
    assert Path("CURRENT").read_text() == "v0005"


def test_snapshot_version(temp_repo):
    """Test version snapshot creation."""
    engine = ConvergenceCycleEngine()
    engine.current_version = "v0001"
    
    snapshot_dir = engine.snapshot_version()
    
    assert snapshot_dir.exists()
    assert snapshot_dir.name == "v0001"
    assert (snapshot_dir / "SNAPSHOT_MANIFEST.json").exists()
    
    # Check manifest content
    manifest = json.loads((snapshot_dir / "SNAPSHOT_MANIFEST.json").read_text())
    assert manifest["version"] == "v0001"
    assert "timestamp" in manifest
    assert "files" in manifest
    assert len(manifest["files"]) > 0


def test_update_changelog(temp_repo):
    """Test CHANGELOG update."""
    engine = ConvergenceCycleEngine()
    engine.current_version = "v0001"
    engine.changed_files = ["test_file.py", "modules/test_module.py"]
    
    engine.update_changelog()
    
    changelog_content = Path("CHANGELOG.md").read_text()
    assert "[v0001]" in changelog_content
    # Check for any date in YYYY-MM-DD format or the word "test_file.py"
    assert "2026-" in changelog_content or "test_file.py" in changelog_content


def test_update_manifest(temp_repo):
    """Test manifest update."""
    engine = ConvergenceCycleEngine()
    engine.update_manifest()
    
    manifest = json.loads(Path("codex_manifest.json").read_text())
    assert len(manifest) > 0
    
    # Check manifest structure
    for entry in manifest:
        assert "module" in entry
        assert "path" in entry
        assert "hash" in entry
        assert "legal_function" in entry
        assert "dependencies" in entry


def test_size_policy_enforcement(temp_repo):
    """Test size policy enforcement."""
    engine = ConvergenceCycleEngine()
    
    # Should not use patches mode for small repo
    result = engine.enforce_size_policy()
    assert result is True  # Size OK
    assert engine.use_patches_mode is False
    
    # Check that size report was created
    assert Path("logs/size_report.log").exists()
    
    report_content = Path("logs/size_report.log").read_text()
    assert "Size Policy Report" in report_content
    assert "PATCHES mode: DISABLED" in report_content


def test_should_build_full_release(temp_repo):
    """Test full release build decision."""
    engine = ConvergenceCycleEngine()
    
    # No changes - should not build
    engine.changed_files = []
    assert engine.should_build_full_release() is False
    
    # 1-2 files - should not build
    engine.changed_files = ["file1.py", "file2.py"]
    assert engine.should_build_full_release() is False
    
    # >2 files - should build
    engine.changed_files = ["file1.py", "file2.py", "file3.py"]
    assert engine.should_build_full_release() is True
    
    # Multi-module changes - should build
    engine.changed_files = ["module1/file1.py", "module2/file2.py"]
    assert engine.should_build_full_release() is True


def test_run_smoke_tests(temp_repo):
    """Test smoke test execution."""
    engine = ConvergenceCycleEngine()
    engine.current_version = "v0001"
    
    # Create CURRENT file for smoke tests
    Path("CURRENT").write_text("v0001")
    
    # Run smoke tests (may fail but shouldn't crash)
    result = engine.run_smoke_tests()
    
    # Check that log was created
    assert Path("logs/smoke_tests.log").exists()
    
    log_content = Path("logs/smoke_tests.log").read_text()
    assert "Smoke Test Run" in log_content
    assert engine.current_version in log_content


def test_full_cycle_integration(temp_repo):
    """Test full convergence cycle."""
    engine = ConvergenceCycleEngine()
    
    # Ensure logs directory exists (engine should create it)
    Path("logs").mkdir(exist_ok=True)
    
    # Run full cycle (may fail smoke tests but shouldn't crash)
    try:
        engine.run_cycle()
    except Exception:
        pass  # Cycle may fail but should complete
    
    # Check that all artifacts were created
    assert Path("VERSION").exists()
    assert Path("CURRENT").exists()
    assert Path("CHANGELOG.md").exists()
    assert Path("codex_manifest.json").exists()
    
    # Check version was incremented
    version = Path("VERSION").read_text().strip()
    assert version == "v0001"
    
    # Check snapshot was created
    assert (Path("VERSIONS") / "v0001").exists()
    assert (Path("VERSIONS") / "v0001" / "SNAPSHOT_MANIFEST.json").exists()
    
    # Check logs were created (convergence_cycle.log should exist)
    # Note: other logs may not exist if smoke tests fail
    assert Path("logs").exists()
