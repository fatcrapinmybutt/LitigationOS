r"""
Self-contained test runner that writes all output to a file.
No stdout/stderr needed — fully pipe-independent.

Run: python C:\Users\andre\LitigationOS\00_SYSTEM\legal_ai\tests\_runner.py
Results: C:\Users\andre\LitigationOS\00_SYSTEM\legal_ai\tests\_results.txt
"""
import sys, os

# -- STEP 0: Environment lockdown BEFORE any other imports --
os.environ["PYTHONUTF8"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Ensure CWD is legal_ai (not repo root — shadow module protection)
LEGAL_AI = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
LEGAL_AI = os.path.normpath(LEGAL_AI)
os.chdir(LEGAL_AI)

# Ensure 00_SYSTEM is on sys.path for legal_ai imports
SYSTEM_DIR = os.path.dirname(LEGAL_AI)
if SYSTEM_DIR not in sys.path:
    sys.path.insert(0, SYSTEM_DIR)

# Remove repo root from sys.path (shadow modules: json.py, typing.py, numpy.py, etc.)
REPO_ROOT = os.path.normcase(os.path.normpath(os.path.dirname(SYSTEM_DIR)))
sys.path = [p for p in sys.path if os.path.normcase(os.path.normpath(p)) != REPO_ROOT]

# -- STEP 1: Pre-mock heavy/slow dependencies --
from unittest.mock import MagicMock

# Mock brains.brain_manager (opens 6 SQLite DBs on import)
_mb = MagicMock()
sys.modules["brains"] = _mb
sys.modules["brains.brain_manager"] = _mb.brain_manager

# Mock sentence_transformers (imports torch, CUDA — very slow)
# Empty module with no CrossEncoder/SentenceTransformer attrs →
# `from sentence_transformers import CrossEncoder` raises ImportError
import types as _types
_fake_st = _types.ModuleType("sentence_transformers")
_fake_st.__path__ = []  # looks like a package
sys.modules["sentence_transformers"] = _fake_st

# Block torch as well (it pulls in CUDA, can take 30+ seconds)
_fake_torch = _types.ModuleType("torch")
_fake_torch.__path__ = []
sys.modules["torch"] = _fake_torch

# Don't mock numpy — let it import naturally (it's fast if installed, ImportError if not)

# -- STEP 2: Open results file --
RESULTS = os.path.join(LEGAL_AI, "tests", "_results.txt")

with open(RESULTS, "w", encoding="utf-8", errors="replace") as f:
    f.write("=" * 70 + "\n")
    f.write("TEST RUNNER RESULTS\n")
    f.write("=" * 70 + "\n")
    f.write(f"Python: {sys.version}\n")
    f.write(f"CWD: {os.getcwd()}\n")
    f.write(f"sys.path[0:3]: {sys.path[:3]}\n\n")

    try:
        import pytest
        f.write(f"pytest {pytest.__version__}\n\n")
        f.write("-" * 70 + "\n")

        # Redirect all output to file
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout = f
        sys.stderr = f

        try:
            code = pytest.main([
                "tests/test_new_modules.py",
                "-v",
                "--tb=short",
                "-x",
                "--no-header",
            ])
        finally:
            sys.stdout = old_out
            sys.stderr = old_err

        f.write(f"\n{'=' * 70}\n")
        f.write(f"EXIT CODE: {code}\n")

    except Exception as ex:
        import traceback
        f.write(f"FATAL: {ex}\n")
        f.write(traceback.format_exc())

os._exit(0)  # Hard exit — no cleanup that might hang
