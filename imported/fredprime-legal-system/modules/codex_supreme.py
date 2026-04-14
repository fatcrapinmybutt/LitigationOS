import datetime
import hashlib
import json
import os
from pathlib import Path
from functools import lru_cache

PERSISTENT_STATE_FILE = "codex_state.json"
AUDIT_LOG = "audit_chain.log"
MANIFEST_FILE = "codex_manifest.json"
ERROR_LOG = "logs/codex_errors.log"
PATCH_HISTORY = "patch_history.json"

# Global cache for manifest to avoid repeated file I/O
_manifest_cache = None
_manifest_mtime = None


def sha256_file(fpath: str) -> str:
    try:
        return hashlib.sha256(Path(fpath).read_bytes()).hexdigest()
    except Exception:
        return ""


def load_manifest() -> list:
    """Load manifest with caching to avoid repeated file I/O."""
    global _manifest_cache, _manifest_mtime
    
    if not os.path.exists(MANIFEST_FILE):
        return []
    
    # Check if cache is valid by comparing modification time
    current_mtime = os.path.getmtime(MANIFEST_FILE)
    if _manifest_cache is not None and _manifest_mtime == current_mtime:
        return _manifest_cache
    
    # Load and cache manifest
    try:
        _manifest_cache = json.loads(Path(MANIFEST_FILE).read_text())
        _manifest_mtime = current_mtime
        return _manifest_cache
    except Exception:
        return []


def clear_manifest_cache() -> None:
    """Clear the manifest cache. Useful for testing or forced reload."""
    global _manifest_cache, _manifest_mtime
    _manifest_cache = None
    _manifest_mtime = None


def log_event(event: str, log_file: str = AUDIT_LOG) -> None:
    ts = datetime.datetime.now().isoformat()
    hval = hashlib.sha256(event.encode()).hexdigest()
    with open(log_file, "a") as f:
        f.write(f"{ts} {hval} {event}\n")


def save_state(state: dict, state_file: str = PERSISTENT_STATE_FILE) -> None:
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)


def load_state(state_file: str = PERSISTENT_STATE_FILE) -> dict:
    if os.path.exists(state_file):
        with open(state_file) as f:
            return json.load(f)
    return {}


def self_diagnostic() -> list[str]:
    diagnostics = []
    for path in [MANIFEST_FILE, ERROR_LOG, PATCH_HISTORY, PERSISTENT_STATE_FILE]:
        if not os.path.exists(path):
            diagnostics.append(f"Missing critical file: {path}")
        else:
            diagnostics.append(f"OK: {path}")
    
    manifest = load_manifest()
    # Build a hash cache to avoid redundant calculations
    hash_cache = {}
    for entry in manifest:
        p = Path(entry["path"])
        if p.exists():
            # Use cache to avoid re-hashing same file
            if str(p) not in hash_cache:
                hash_cache[str(p)] = sha256_file(p)
            if hash_cache[str(p)] != entry.get("hash"):
                diagnostics.append(f"File hash mismatch: {p}")
    
    save_state({"last_diagnostic": diagnostics})
    return diagnostics


def forensic_integrity_check() -> list[str]:
    issues = []
    manifest = load_manifest()
    if not manifest:
        return issues
    
    # Build a hash cache to avoid redundant calculations
    hash_cache = {}
    for entry in manifest:
        path = Path(entry["path"])
        if path.exists():
            # Use cache to avoid re-hashing same file
            if str(path) not in hash_cache:
                hash_cache[str(path)] = sha256_file(path)
            if hash_cache[str(path)] != entry.get("hash"):
                issues.append(f"Tampered: {path}")
    
    save_state({"last_integrity_check": issues})
    return issues


def timeline_event_matrix() -> list[dict]:
    timeline = []
    manifest = load_manifest()
    for entry in manifest:
        timeline.append(
            {
                "file": entry.get("path"),
                "date": entry.get("timestamp"),
                "legal_function": entry.get("legal_function"),
                "validated": entry.get("validated"),
            }
        )
    timeline.sort(key=lambda x: x.get("date") or "")
    save_state({"timeline_matrix": timeline})
    return timeline
