"""PatchManager — Hot-reload patch system for THEMANBEARPIG.

Allows graph data updates (adversary nodes, evidence links, config changes)
without rebuilding the PyInstaller EXE.  Patches live in ``patches/`` outside
the frozen bundle so they persist across rebuilds.
"""

__version__ = "1.0.0"

from .manager import PatchManager  # noqa: F401 — lazy, no side effects
