import json
import re
import subprocess
from pathlib import Path
from typing import Iterable

from src.utils.hashing import hash_file

MANIFEST_FILE = "codex_manifest.json"
BANNED_KEYWORDS = ["TODO", "WIP", "temp_var", "placeholder"]
MANIFEST_REQUIRED_KEYS = {"path", "hash"}


def _run_git_command(args: list[str]) -> str:
    try:
        result = subprocess.run(args, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() if exc.stderr else "no stderr output"
        raise RuntimeError(f"Git command failed: {' '.join(args)} ({stderr})") from exc
    return result.stdout.strip()


def get_current_branch() -> str:
    return _run_git_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])


def get_last_commit_message() -> str:
    return _run_git_command(["git", "log", "-1", "--pretty=%B"])


def load_manifest() -> list[dict]:
    if not Path(MANIFEST_FILE).exists():
        return []
    try:
        payload = json.loads(Path(MANIFEST_FILE).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Manifest JSON invalid: {MANIFEST_FILE}") from exc
    if not isinstance(payload, list):
        raise TypeError("Manifest JSON must be a list of entries")
    return payload


def _contains_banned_keywords(msg: str, keywords: Iterable[str]) -> bool:
    return any(keyword in msg for keyword in keywords)


def verify_commit_message(msg: str) -> None:
    if _contains_banned_keywords(msg, BANNED_KEYWORDS):
        raise ValueError("Commit message contains banned keyword")
    if not re.match(r"^\[(core|hotfix|docs|merge|patch|engine|matrix|echelon)\] ", msg):
        raise ValueError("Commit message format invalid")


def verify_branch_name(branch: str) -> bool:
    if not branch.startswith("codex/"):
        raise ValueError("Branch name must start with 'codex/'")
    triggers = {
        "core",
        "engine",
        "matrix",
        "protocol",
        "epoch",
        "echelon",
        "hotfix",
        "merge",
    }
    if not any(trigger in branch for trigger in triggers):
        raise ValueError("Branch name missing required trigger tag")
    return True


def _validate_manifest_entry(entry: dict, index: int) -> tuple[Path, str]:
    if not isinstance(entry, dict):
        raise TypeError(f"Manifest entry {index} must be a dict")
    missing = MANIFEST_REQUIRED_KEYS.difference(entry.keys())
    if missing:
        raise ValueError(f"Manifest entry {index} missing keys: {sorted(missing)}")
    path_value = entry["path"]
    if not isinstance(path_value, str):
        raise TypeError(f"Manifest entry {index} path must be a string")
    hash_value = entry["hash"]
    if not isinstance(hash_value, str):
        raise TypeError(f"Manifest entry {index} hash must be a string")
    return Path(path_value), hash_value


def verify_manifest_hashes() -> None:
    manifest = load_manifest()
    for index, entry in enumerate(manifest):
        path, expected_hash = _validate_manifest_entry(entry, index)
        if not path.exists():
            raise FileNotFoundError(f"Missing file: {path}")
        if hash_file(path) != expected_hash:
            raise ValueError(f"Hash mismatch for {path}")


def run_guardian() -> None:
    branch = get_current_branch()
    msg = get_last_commit_message()
    msg_lines = msg.splitlines()
    if not msg_lines or not msg_lines[0].strip():
        raise ValueError("Commit message is empty")
    msg = msg_lines[0]
    verify_branch_name(branch)
    verify_commit_message(msg)
    if Path(MANIFEST_FILE).exists():
        verify_manifest_hashes()
