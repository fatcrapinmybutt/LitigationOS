# FORGE — Filing Operations & Readiness Generation Engine
"""Filing packet assembly, exhibit management, and readiness checklists."""

try:
    from .forge_engine import ForgeEngine
except ImportError as e:
    ForgeEngine = None
    _import_error = str(e)

__all__ = ["ForgeEngine"]
