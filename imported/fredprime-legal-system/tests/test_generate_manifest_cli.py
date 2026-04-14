import json
import subprocess
import sys


def test_cli_generates_manifest(tmp_path):
    output = tmp_path / "manifest.json"
    result = subprocess.run(
        [
            sys.executable,
            "cli/generate_manifest.py",
            "-o",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert output.exists()
    # Check that the output message contains the path
    assert str(output) in result.stdout
    # Verify the manifest was created with the new format
    data = json.loads(output.read_text())
    # New format is a dict with relative paths as keys
    assert isinstance(data, dict)
    # Should have some files indexed
    assert len(data) > 0
