"""
Configuration manager for LitigationOS Daemon.
Loads YAML config, validates with Pydantic, supports hot-reload.
"""
import os
import sys
from pathlib import Path
from typing import Optional

import yaml

from .models import DaemonConfig

DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "daemon_config.yaml"
)


def generate_default_config(path: str = None) -> str:
    """Generate default config YAML. Returns the path written."""
    path = path or DEFAULT_CONFIG_PATH
    config = DaemonConfig()
    data = config.model_dump(mode="json")
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    return path


def load_config(path: str = None) -> DaemonConfig:
    """Load config from YAML. Creates default if missing."""
    path = path or DEFAULT_CONFIG_PATH
    if not os.path.exists(path):
        generate_default_config(path)

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if raw is None:
        raw = {}

    return DaemonConfig(**raw)


def validate_config(path: str = None) -> tuple[bool, list[str]]:
    """Validate config file. Returns (valid, errors)."""
    errors = []
    try:
        config = load_config(path)
    except Exception as e:
        return False, [str(e)]

    # Check drive paths exist
    for drive in config.drives:
        if not os.path.exists(drive.path + "\\"):
            errors.append(f"Drive {drive.path} not found")

    # Check brain dir
    if not os.path.isdir(config.brain_dir):
        errors.append(f"Brain directory not found: {config.brain_dir}")

    # Check log dir parent
    log_parent = os.path.dirname(config.logging.log_dir)
    if not os.path.isdir(log_parent):
        errors.append(f"Log dir parent not found: {log_parent}")

    return len(errors) == 0, errors


class ConfigManager:
    """Manages daemon configuration with hot-reload support."""

    def __init__(self, config_path: str = None):
        self._path = config_path or DEFAULT_CONFIG_PATH
        self._config: Optional[DaemonConfig] = None
        self._mtime: float = 0.0

    @property
    def config(self) -> DaemonConfig:
        if self._config is None:
            self.reload()
        return self._config

    def reload(self) -> DaemonConfig:
        """Reload config from disk."""
        self._config = load_config(self._path)
        if os.path.exists(self._path):
            self._mtime = os.path.getmtime(self._path)
        return self._config

    def has_changed(self) -> bool:
        """Check if config file has been modified since last load."""
        if not os.path.exists(self._path):
            return False
        return os.path.getmtime(self._path) > self._mtime

    def check_and_reload(self) -> bool:
        """Reload if changed. Returns True if reloaded."""
        if self.has_changed():
            self.reload()
            return True
        return False

    def save(self, config: DaemonConfig = None):
        """Save current config to disk."""
        config = config or self._config
        if config is None:
            return
        data = config.model_dump(mode="json")
        with open(self._path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        self._mtime = os.path.getmtime(self._path)
