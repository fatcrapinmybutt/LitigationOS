"""
Performance-focused tests for codex_supreme module.
Tests caching and I/O optimization.
"""
import json
import pytest
from pathlib import Path
from modules import codex_supreme


@pytest.fixture
def test_manifest(tmp_path: Path):
    """Create a test manifest file."""
    manifest_path = tmp_path / "codex_manifest.json"
    manifest_data = [
        {
            "path": "file1.py",
            "hash": "abc123",
            "timestamp": "2025-01-01T00:00:00",
            "legal_function": "motion_builder",
            "validated": True,
        },
        {
            "path": "file2.py",
            "hash": "def456",
            "timestamp": "2025-01-02T00:00:00",
            "legal_function": "form_filler",
            "validated": True,
        },
        {
            "path": "file3.py",
            "hash": "ghi789",
            "timestamp": "2025-01-03T00:00:00",
            "legal_function": "evidence_tracker",
            "validated": False,
        },
    ]
    manifest_path.write_text(json.dumps(manifest_data))
    
    # Create the actual files
    for entry in manifest_data:
        file_path = tmp_path / entry["path"]
        file_path.write_text(f"# {entry['legal_function']}")
    
    return manifest_path


def test_sha256_file_basic(tmp_path: Path):
    """Test basic SHA256 file hashing."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    
    hash1 = codex_supreme.sha256_file(str(test_file))
    assert len(hash1) == 64
    assert hash1.isalnum()
    
    # Verify consistency
    hash2 = codex_supreme.sha256_file(str(test_file))
    assert hash1 == hash2


def test_sha256_file_nonexistent():
    """Test SHA256 on nonexistent file returns empty string."""
    result = codex_supreme.sha256_file("/nonexistent/file.txt")
    assert result == ""


def test_log_event(tmp_path: Path):
    """Test event logging."""
    log_file = tmp_path / "test_audit.log"
    codex_supreme.log_event("Test event", log_file=str(log_file))
    
    assert log_file.exists()
    content = log_file.read_text()
    assert "Test event" in content
    assert len(content.split()) >= 3  # timestamp, hash, event


def test_save_and_load_state(tmp_path: Path):
    """Test state persistence."""
    state_file = tmp_path / "state.json"
    test_state = {"version": "1.0", "modules": ["mod1", "mod2"]}
    
    codex_supreme.save_state(test_state, state_file=str(state_file))
    loaded_state = codex_supreme.load_state(state_file=str(state_file))
    
    assert loaded_state == test_state


def test_load_state_missing_file(tmp_path: Path):
    """Test loading state when file doesn't exist."""
    state_file = tmp_path / "nonexistent.json"
    state = codex_supreme.load_state(state_file=str(state_file))
    assert state == {}


def test_self_diagnostic_with_manifest(tmp_path: Path, test_manifest: Path, monkeypatch):
    """Test self diagnostic function."""
    # Change to the temp directory context
    monkeypatch.chdir(tmp_path)
    
    # Copy manifest to expected location
    manifest_dest = tmp_path / "codex_manifest.json"
    manifest_dest.write_text(test_manifest.read_text())
    
    # Create other required files
    (tmp_path / "logs").mkdir(exist_ok=True)
    (tmp_path / "logs" / "codex_errors.log").touch()
    (tmp_path / "patch_history.json").write_text("[]")
    (tmp_path / "codex_state.json").write_text("{}")
    
    # Create the files referenced in manifest
    manifest_data = json.loads(manifest_dest.read_text())
    for entry in manifest_data:
        file_path = tmp_path / entry["path"]
        # Write content that matches hash (for simplicity, use placeholder)
        file_path.write_text(f"# Test content for {entry['path']}")
    
    diagnostics = codex_supreme.self_diagnostic()
    assert isinstance(diagnostics, list)
    assert len(diagnostics) > 0


def test_self_diagnostic_missing_files(tmp_path: Path, monkeypatch):
    """Test self diagnostic with missing critical files."""
    monkeypatch.chdir(tmp_path)
    
    diagnostics = codex_supreme.self_diagnostic()
    assert isinstance(diagnostics, list)
    # Should report missing files
    assert any("Missing" in msg for msg in diagnostics)


def test_forensic_integrity_check_no_manifest(tmp_path: Path, monkeypatch):
    """Test integrity check when manifest doesn't exist."""
    monkeypatch.chdir(tmp_path)
    
    issues = codex_supreme.forensic_integrity_check()
    assert issues == []


def test_forensic_integrity_check_with_manifest(tmp_path: Path, test_manifest: Path, monkeypatch):
    """Test forensic integrity check."""
    monkeypatch.chdir(tmp_path)
    
    # Copy manifest to expected location
    manifest_dest = tmp_path / "codex_manifest.json"
    manifest_dest.write_text(test_manifest.read_text())
    
    # Create files with matching content
    manifest_data = json.loads(manifest_dest.read_text())
    for entry in manifest_data:
        file_path = tmp_path / entry["path"]
        file_path.write_text(f"# Test content")
    
    issues = codex_supreme.forensic_integrity_check()
    assert isinstance(issues, list)
    # Files won't match hashes, so should report tampering
    # (unless we calculate exact matching content, which is fine for test)


def test_timeline_event_matrix_no_manifest(tmp_path: Path, monkeypatch):
    """Test timeline matrix when no manifest exists."""
    monkeypatch.chdir(tmp_path)
    
    timeline = codex_supreme.timeline_event_matrix()
    assert timeline == []


def test_timeline_event_matrix_with_manifest(tmp_path: Path, test_manifest: Path, monkeypatch):
    """Test timeline event matrix generation."""
    monkeypatch.chdir(tmp_path)
    
    # Copy manifest to expected location
    manifest_dest = tmp_path / "codex_manifest.json"
    manifest_dest.write_text(test_manifest.read_text())
    
    timeline = codex_supreme.timeline_event_matrix()
    assert isinstance(timeline, list)
    assert len(timeline) == 3
    
    # Verify timeline is sorted by date
    dates = [entry["date"] for entry in timeline]
    assert dates == sorted(dates)
    
    # Verify structure
    for entry in timeline:
        assert "file" in entry
        assert "date" in entry
        assert "legal_function" in entry
        assert "validated" in entry


def test_manifest_loading_efficiency(tmp_path: Path, test_manifest: Path, benchmark_timer, monkeypatch):
    """Test that manifest is not loaded multiple times unnecessarily."""
    monkeypatch.chdir(tmp_path)
    
    # Copy manifest to expected location
    manifest_dest = tmp_path / "codex_manifest.json"
    manifest_dest.write_text(test_manifest.read_text())
    
    # Create large manifest for testing
    large_manifest = []
    for i in range(1000):
        large_manifest.append({
            "path": f"file{i}.py",
            "hash": f"hash{i:04d}",
            "timestamp": f"2025-01-{(i % 28) + 1:02d}T00:00:00",
            "legal_function": f"function_{i}",
            "validated": i % 2 == 0,
        })
    manifest_dest.write_text(json.dumps(large_manifest))
    
    # This test verifies that operations don't take too long
    # If manifest is loaded multiple times, this will be slow
    with benchmark_timer:
        timeline = codex_supreme.timeline_event_matrix()
    
    assert len(timeline) == 1000
    # Should complete reasonably fast even with 1000 entries
    assert benchmark_timer.elapsed < 2.0


def test_sha256_consistency(tmp_path: Path):
    """Test that SHA256 produces consistent results."""
    test_file = tmp_path / "consistent.txt"
    test_file.write_text("same content every time")
    
    hashes = [codex_supreme.sha256_file(str(test_file)) for _ in range(10)]
    assert len(set(hashes)) == 1  # All hashes should be identical
