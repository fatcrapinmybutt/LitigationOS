"""Pytest configuration — ensure semantic_search is importable."""
from __future__ import annotations

import sys
from pathlib import Path

# Add ai_modules to sys.path so `import semantic_search` works in tests
_ai_modules = str(Path(__file__).resolve().parent.parent)
if _ai_modules not in sys.path:
    sys.path.insert(0, _ai_modules)
