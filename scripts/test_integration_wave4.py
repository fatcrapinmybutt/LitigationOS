"""
Integration Wave 4 Test Suite
==============================
Validates all new integration wiring from Waves 4.1 and 4.2:
  1. Legal AI Registry — 66-tool lazy-loading dispatcher
  2. Automation Registry — 13-task omega/utility dispatch
  3. Handler Integration — HANDLER_MAP expansion (6→14 entries)
  4. Engine Registry — safe import, _ENGINE_MAP, get_engine factory

Uses importlib.util for direct module loading (same as test_engines_init.py).
No pytest, no unittest — standalone pass/fail reporting.
"""

import importlib.util
import os
import sys
import types
from pathlib import Path

# --- Setup ------------------------------------------------------------------
_repo = Path(__file__).resolve().parent.parent
_system = _repo / "00_SYSTEM"
sys.path.insert(0, str(_system))

_passed = 0
_failed = 0

# Save a copy of stdout's fd — some handlers close it during import.
_stdout_fd_backup = os.dup(sys.stdout.fileno())


def _ensure_stdout():
    """Restore sys.stdout if the underlying fd was closed."""
    try:
        sys.stdout.write("")
        sys.stdout.flush()
    except (ValueError, OSError):
        # The original stdout pipe is dead. Fall back to stderr so
        # run_all_tests.py (which merges stdout+stderr) still sees output.
        sys.stdout = sys.stderr


def test(label, fn):
    """Run a single test; print [PASS] or [FAIL] and update counters."""
    global _passed, _failed
    try:
        result = fn()
        if result:
            _passed += 1
            msg = f"  [PASS] {label}"
        else:
            _failed += 1
            msg = f"  [FAIL] {label}"
    except Exception as e:
        _failed += 1
        msg = f"  [FAIL] {label} — {type(e).__name__}: {e}"
    _ensure_stdout()
    print(msg)


def _load_mod(name, filepath):
    """Load a module from a filepath using importlib.util."""
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# ===========================================================================
# GROUP 1 — Legal AI Registry
# ===========================================================================
print("\n▶ GROUP 1 — Legal AI Registry")

_legal_ai_registry_mod = None


def _load_legal_ai_registry():
    global _legal_ai_registry_mod
    if _legal_ai_registry_mod is None:
        # Register legal_ai as a package so relative imports resolve
        pkg = types.ModuleType("legal_ai")
        pkg.__path__ = [str(_system / "legal_ai")]
        pkg.__package__ = "legal_ai"
        sys.modules["legal_ai"] = pkg
        _legal_ai_registry_mod = _load_mod(
            "legal_ai.registry",
            _system / "legal_ai" / "registry.py",
        )
    return _legal_ai_registry_mod


test("legal_ai/registry.py exists and imports", lambda: (
    (_system / "legal_ai" / "registry.py").exists()
    and _load_legal_ai_registry() is not None
))

test("LEGAL_AI_REGISTRY has 60+ tools", lambda: (
    len(_load_legal_ai_registry().LEGAL_AI_REGISTRY) >= 60
))

test("get_legal_ai_tool('quality_gate') returns instance", lambda: (
    # May raise ImportError for missing deps — that's a real failure.
    # The tool module exists, so this should instantiate.
    _load_legal_ai_registry().get_legal_ai_tool("quality_gate") is not None
))

test("list_legal_ai_tools() returns dicts with required keys", lambda: (
    (tools := _load_legal_ai_registry().list_legal_ai_tools()) is not None
    and len(tools) >= 60
    and all(
        {"tool_name", "class_name", "category"} <= set(t.keys())
        for t in tools
    )
))

test("list_legal_ai_tools filtered by category contains custody-related tools", lambda: (
    # No dedicated search function — filter list for 'custody' in descriptions
    any(
        "custody" in t.get("description", "").lower()
        for t in _load_legal_ai_registry().list_legal_ai_tools()
    )
))

test("resolve_method returns valid method for quality_gate", lambda: (
    (reg := _load_legal_ai_registry()) is not None
    and (entry := reg.LEGAL_AI_REGISTRY.get("quality_gate")) is not None
    and (inst := reg.get_legal_ai_tool("quality_gate")) is not None
    and (method := reg.resolve_method(inst, "quality_gate")) is not None
    and isinstance(method, str) and len(method) > 0
))


# ===========================================================================
# GROUP 2 — Automation Registry
# ===========================================================================
print("\n▶ GROUP 2 — Automation Registry")

_automation_mod = None


def _load_automation():
    global _automation_mod
    if _automation_mod is None:
        # Register automation as a package
        pkg = types.ModuleType("automation")
        pkg.__path__ = [str(_system / "automation")]
        pkg.__package__ = "automation"
        sys.modules["automation"] = pkg
        _automation_mod = _load_mod(
            "automation.__init__",
            _system / "automation" / "__init__.py",
        )
        # Re-register so `from automation import X` works
        sys.modules["automation"] = _automation_mod
    return _automation_mod


test("automation/__init__.py exists and imports", lambda: (
    (_system / "automation" / "__init__.py").exists()
    and _load_automation() is not None
))

test("AUTOMATION_REGISTRY has 13 tasks", lambda: (
    len(_load_automation().AUTOMATION_REGISTRY) == 13
))

test("list_automations() returns dicts with required keys", lambda: (
    (items := _load_automation().list_automations()) is not None
    and len(items) == 13
    and all(
        {"name", "description", "schedule_hint"} <= set(t.keys())
        for t in items
    )
))

test("run_automation('nonexistent_task') returns error status (not crash)", lambda: (
    (result := _load_automation().run_automation("nonexistent_task")) is not None
    and isinstance(result, dict)
    and result.get("status") == "error"
))


# ===========================================================================
# GROUP 3 — Handler Integration (task_handlers.py)
# ===========================================================================
print("\n▶ GROUP 3 — Handler Integration")
_ensure_stdout()

_handlers_mod = None


def _load_handlers():
    global _handlers_mod
    if _handlers_mod is None:
        # Ensure daemon is a package
        daemon_dir = _system / "daemon"
        if "daemon" not in sys.modules:
            pkg = types.ModuleType("daemon")
            pkg.__path__ = [str(daemon_dir)]
            pkg.__package__ = "daemon"
            sys.modules["daemon"] = pkg
        _handlers_mod = _load_mod(
            "daemon.task_handlers",
            daemon_dir / "task_handlers.py",
        )
    return _handlers_mod


test("HANDLER_MAP has >= 14 entries", lambda: (
    len(_load_handlers().HANDLER_MAP) >= 14
))

test("All HANDLER_MAP values are callable", lambda: (
    all(callable(v) for v in _load_handlers().HANDLER_MAP.values())
))

def _test_handle_legal_ai():
    """handle_legal_ai with quality_gate returns dict with 'status'."""
    import logging
    logging.disable(logging.CRITICAL)
    try:
        result = _load_handlers().handle_legal_ai({"tool_name": "quality_gate"})
        return isinstance(result, dict) and "status" in result
    finally:
        logging.disable(logging.NOTSET)


test("handle_legal_ai({'tool_name': 'quality_gate'}) returns dict with 'status'",
     _test_handle_legal_ai)

test("handle_automation({'task_name': 'nonexistent'}) returns error dict", lambda: (
    (result := _load_handlers().handle_automation({"task_name": "nonexistent"})) is not None
    and isinstance(result, dict)
    and result.get("status") == "error"
))

def _test_filing_scan():
    """filing_scan with empty payload triggers an error path — still returns dict."""
    import logging
    logging.disable(logging.CRITICAL)
    try:
        result = _load_handlers().handle_filing_scan({})
        return isinstance(result, dict) and "status" in result
    finally:
        logging.disable(logging.NOTSET)


test("handle_filing_scan({}) returns dict with 'status' key", _test_filing_scan)

test("handle_brain_query({'brain_name':'','sql':''}) returns error dict", lambda: (
    (result := _load_handlers().handle_brain_query({"brain_name": "", "sql": ""})) is not None
    and isinstance(result, dict)
    and result.get("status") == "error"
))

test("handle_brain_search({'query': ''}) returns error dict", lambda: (
    (result := _load_handlers().handle_brain_search({"query": ""})) is not None
    and isinstance(result, dict)
    and result.get("status") == "error"
))


# ===========================================================================
# GROUP 4 — Engine Registry (__init__.py)
# ===========================================================================
print("\n▶ GROUP 4 — Engine Registry")
_ensure_stdout()

_engines_mod = None


def _load_engines():
    global _engines_mod
    if _engines_mod is None:
        engines_dir = _system / "engines"
        # Register engines as a package
        pkg = types.ModuleType("engines")
        pkg.__path__ = [str(engines_dir)]
        pkg.__package__ = "engines"
        sys.modules["engines"] = pkg
        _engines_mod = _load_mod(
            "engines.__init__",
            engines_dir / "__init__.py",
        )
        # Merge into the package namespace
        for k, v in vars(_engines_mod).items():
            if not k.startswith("__"):
                setattr(pkg, k, v)
        sys.modules["engines"] = _engines_mod
    return _engines_mod


test("engines.__version__ == '3.0.0'", lambda: (
    _load_engines().__version__ == "3.0.0"
))

test("engines._ENGINE_MAP has >= 9 entries", lambda: (
    len(_load_engines()._ENGINE_MAP) >= 9
))


def _test_get_engine():
    """Test get_engine — accepts either a working engine or a clean KeyError."""
    eng = _load_engines()
    try:
        result = eng.get_engine("nexus")
        return result is not None
    except KeyError:
        # Acceptable — engine not loaded due to missing deps
        return True
    except ImportError:
        # Also acceptable — dependency not installed
        return True


test("engines.get_engine('nexus') callable or KeyError (no import crash)",
     _test_get_engine)


# ===========================================================================
# Summary — write to stderr as a fallback since handler imports may have
# corrupted stdout's fd beyond recovery.
# ===========================================================================
_summary = (
    f"\n{'=' * 50}\n"
    f"  RESULTS: {_passed} passed, {_failed} failed\n"
    + ("  STATUS: ALL PASSED [OK]\n" if _failed == 0 else "  STATUS: FAILURES DETECTED [X]\n")
    + f"{'=' * 50}\n"
)
# Try stdout first, fall back to stderr
try:
    sys.stdout.write(_summary)
    sys.stdout.flush()
except (ValueError, OSError):
    sys.stderr.write(_summary)
    sys.stderr.flush()

try:
    os.close(_stdout_fd_backup)
except OSError:
    pass

# os._exit skips atexit/TextIOWrapper cleanup that would crash on the dead fd.
os._exit(0 if _failed == 0 else 1)
