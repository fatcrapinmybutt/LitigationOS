"""Shared test configuration for LitigationOS engine tests.

Handles shadow module protection — repo root contains json.py, typing.py,
tokenize.py, numpy.py, pandas.py that shadow stdlib/third-party modules.
"""
import sys
import os

# Compute paths once
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYSTEM_DIR = os.path.join(REPO_ROOT, "00_SYSTEM")

# Remove repo root from sys.path to avoid shadow modules
sys.path = [p for p in sys.path if os.path.abspath(p) != REPO_ROOT]

# Add specific directories we need (order matters — most specific first)
_dirs_to_add = [
    os.path.join(SYSTEM_DIR, "pipeline"),
    os.path.join(SYSTEM_DIR, "local_model"),
    os.path.join(SYSTEM_DIR, "engines"),
    os.path.join(SYSTEM_DIR, "novel"),
    os.path.join(SYSTEM_DIR, "darwin"),
    os.path.join(SYSTEM_DIR, "brains"),
    os.path.join(SYSTEM_DIR, "legal_ai"),
    SYSTEM_DIR,
]
for d in reversed(_dirs_to_add):
    if os.path.isdir(d) and d not in sys.path:
        sys.path.insert(0, d)
