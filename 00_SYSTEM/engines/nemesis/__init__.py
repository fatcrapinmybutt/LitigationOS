# NEMESIS — Adversary Intelligence Engine
"""Adversary prediction, counter-strategy generation, and vulnerability analysis."""

try:
    from .nemesis_engine import NemesisEngine
except ImportError as e:
    NemesisEngine = None
    _import_error = str(e)

__all__ = ["NemesisEngine"]
