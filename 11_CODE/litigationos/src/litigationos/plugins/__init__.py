"""Plugins package — jurisdiction-extensible rule/form/court plugins.

Plugins are auto-discovered at startup by scanning subdirectories for
modules that export a JurisdictionPlugin subclass.
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from litigationos.plugins.base import JurisdictionPlugin


def discover_plugins() -> dict[str, "JurisdictionPlugin"]:
    """Scan plugins/ subdirectories and return {jurisdiction_id: PluginInstance}."""
    plugins: dict[str, JurisdictionPlugin] = {}
    for importer, modname, ispkg in pkgutil.iter_modules(__path__):
        if ispkg:
            mod = importlib.import_module(f".{modname}", __package__)
            if hasattr(mod, "Plugin"):
                p = mod.Plugin()
                plugins[p.jurisdiction_id] = p
    return plugins


__all__ = ["discover_plugins"]
