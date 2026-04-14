"""Centralised drive-configuration loader for LitigationOS.

Config file resolution order
-----------------------------
1. The path in the ``FRED_DRIVES_CONFIG`` environment variable (if set).
2. ``CONFIG/drives.toml`` relative to the project root (i.e. the directory
   that contains this package's top-level ``litigationos/`` folder).
3. If neither exists, all functions return safe empty/permissive defaults
   and emit a one-time ``warnings.warn`` message.

Example ``CONFIG/drives.toml``
-------------------------------
See ``CONFIG/drives.toml.example`` in the repository root.
"""

from __future__ import annotations

import os
import warnings
from pathlib import Path, PureWindowsPath
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# tomllib / tomli compatibility (stdlib in 3.11+, external on 3.10)
# ---------------------------------------------------------------------------
try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:
        tomllib = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_CONFIG_PATH = _PROJECT_ROOT / "CONFIG" / "drives.toml"

_WARN_MISSING = (
    "LitigationOS drive config not found at {path!r}. "
    "Falling back to empty drive list. "
    "Copy CONFIG/drives.toml.example to CONFIG/drives.toml and edit it."
)
_WARN_NO_TOMLLIB = (
    "Neither tomllib (stdlib >=3.11) nor tomli (pip install tomli) is "
    "available. Drive config cannot be loaded; falling back to defaults."
)


def _resolve_config_path() -> Path:
    """Return the effective config path, honouring the env-var override."""
    env_override = os.environ.get("FRED_DRIVES_CONFIG", "").strip()
    if env_override:
        return Path(env_override)
    return _DEFAULT_CONFIG_PATH


def _parse_toml(config_path: Path) -> dict:
    """Parse a TOML file and return the raw dict, or {} on failure."""
    if tomllib is None:
        warnings.warn(_WARN_NO_TOMLLIB, RuntimeWarning, stacklevel=3)
        return {}
    if not config_path.is_file():
        warnings.warn(_WARN_MISSING.format(path=str(config_path)), RuntimeWarning, stacklevel=3)
        return {}
    with open(config_path, "rb") as fh:
        return tomllib.load(fh)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_drives(config_path: Optional[Path] = None) -> Dict[str, dict]:
    """Return a dict of *active* drive entries from the config file.

    Active means ``enabled = true`` **and** the path currently exists on the
    file-system.  Keys are the drive names from the ``[drives.*]`` section
    (e.g. ``"evidence_primary"``).  Values are the raw TOML sub-tables.

    Parameters
    ----------
    config_path:
        Override the config file path.  When *None*, the default resolution
        order (env-var -> ``CONFIG/drives.toml``) is used.
    """
    path = config_path if config_path is not None else _resolve_config_path()
    data = _parse_toml(path)
    drives_section: dict = data.get("drives", {})

    active: Dict[str, dict] = {}
    for name, entry in drives_section.items():
        if not isinstance(entry, dict):
            continue
        if not entry.get("enabled", False):
            continue
        drive_path = entry.get("path", "")
        if drive_path and Path(drive_path).exists():
            active[name] = entry
    return active


def get_drive_paths(
    role: Optional[str] = None,
    config_path: Optional[Path] = None,
) -> List[Path]:
    """Return a list of ``Path`` objects for active drives, optionally filtered by *role*.

    Parameters
    ----------
    role:
        When provided (e.g. ``"evidence"``, ``"code"``, ``"cloud_mirror"``),
        only drives whose ``role`` field matches are returned.  When *None*,
        all active drives are returned.
    config_path:
        Override the config file path.
    """
    active = load_drives(config_path)
    paths: List[Path] = []
    for entry in active.values():
        if role is not None and entry.get("role") != role:
            continue
        drive_path = entry.get("path", "")
        if drive_path:
            paths.append(Path(drive_path))
    return paths


def validate_drive_policy(
    path: "str | Path",
    config_path: Optional[Path] = None,
) -> Tuple[bool, str]:
    """Check whether *path* is allowed under the ``[policy]`` section.

    Returns
    -------
    (True, "")
        The path is allowed.
    (False, reason_string)
        The path is denied; ``reason_string`` explains why.
    """
    path = Path(path)
    raw = _parse_toml(config_path if config_path is not None else _resolve_config_path())
    policy: dict = raw.get("policy", {})

    deny_drives: List[str] = [d.upper() for d in policy.get("deny_drives", [])]

    # Use PureWindowsPath to reliably extract Windows-style drive letters (e.g.
    # "C:" from "C:/foo") regardless of the OS this code is running on.
    win_drive = PureWindowsPath(str(path)).drive  # e.g. "C:" or ""
    drive_letter = win_drive.rstrip(":").upper() if win_drive else ""

    if drive_letter and drive_letter in deny_drives:
        return False, f"Drive {drive_letter}: is in the deny list {deny_drives}"

    return True, ""


def check_required_drives(
    config_path: Optional[Path] = None,
) -> Tuple[bool, List[str]]:
    """Check whether the ``require_any`` policy is satisfied.

    Returns
    -------
    (True, [])
        At least one of the required drives is present and active.
    (False, missing_drives)
        None of the required drives are active; ``missing_drives`` lists them.
    """
    resolved = config_path if config_path is not None else _resolve_config_path()
    raw = _parse_toml(resolved)
    policy: dict = raw.get("policy", {})
    require_any: List[str] = [d.upper() for d in policy.get("require_any", [])]

    if not require_any:
        return True, []

    active = load_drives(resolved)
    active_drive_letters = set()
    for entry in active.values():
        drive_path_str = entry.get("path", "")
        win_drive = PureWindowsPath(drive_path_str).drive  # e.g. "F:" or ""
        letter = win_drive.rstrip(":").upper() if win_drive else ""
        if letter:
            active_drive_letters.add(letter)

    satisfied = [r for r in require_any if r in active_drive_letters]
    if satisfied:
        return True, []

    return False, require_any
