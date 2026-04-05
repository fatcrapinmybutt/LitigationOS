# ORACLE — Michigan Rule Reasoning Engine
"""Given filing type + court + lane → complete procedural roadmap."""

try:
    from .oracle_engine import Oracle
except ImportError as e:
    Oracle = None
    _import_error = str(e)

__all__ = ["Oracle"]
