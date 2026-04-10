"""
Engine Architecture Diagnostic — Systematic Debug
Tests every import, checks shared integration, finds dead code.
"""
import sys
import os
import importlib
import traceback
from pathlib import Path

# Avoid shadow modules in repo root
REPO = Path(r"C:\Users\andre\LitigationOS")
ENGINE_ROOT = REPO / "00_SYSTEM" / "engines"
SHARED_ROOT = REPO / "00_SYSTEM" / "shared"

# Add the 00_SYSTEM dir to path so 'from shared import ...' works
sys.path.insert(0, str(REPO / "00_SYSTEM"))
# Add engines parent so 'from engines import ...' works
sys.path.insert(0, str(ENGINE_ROOT.parent))

results = {
    "import_success": [],
    "import_fail": [],
    "shared_integration": [],
    "hardcoded_paths": [],
    "missing_tests": [],
    "non_canonical": [],
    "standalone_scripts": [],
    "dead_exports": [],
}

# ── 1. Test shared module ──────────────────────────────────────────
print("=" * 70)
print("1. SHARED MODULE HEALTH")
print("=" * 70)

try:
    from shared import get_db, get_db_path, sanitize_fts5, get_root, DB_REGISTRY
    print(f"  ✓ shared module imports OK")
    print(f"  ✓ get_root() = {get_root()}")
    print(f"  ✓ get_db_path() = {get_db_path()}")
    print(f"  ✓ DB_REGISTRY has {len(DB_REGISTRY)} entries")
    for k, v in sorted(DB_REGISTRY.items()):
        exists = Path(v).exists() if os.path.isabs(str(v)) else (get_root() / v).exists()
        status = "✓" if exists else "✗ MISSING"
        print(f"      {status} {k}: {v}")
except Exception as e:
    print(f"  ✗ SHARED MODULE FAILED: {e}")
    traceback.print_exc()

# ── 2. Test lazy engine accessors ──────────────────────────────────
print("\n" + "=" * 70)
print("2. LAZY ENGINE ACCESSORS")
print("=" * 70)

accessor_names = [
    "get_analytics_engine",
    "get_semantic_engine",
    "get_search_engine",
    "get_typst_engine",
    "get_perception_engine",
]

for name in accessor_names:
    try:
        from shared import __init__ as sh
        fn = getattr(sh, name, None)
        if fn is None:
            # Try importing directly
            import shared as sh2
            fn = getattr(sh2, name, None)
        if fn:
            print(f"  ✓ {name} defined in shared")
        else:
            print(f"  ✗ {name} NOT FOUND in shared")
    except Exception as e:
        print(f"  ✗ {name} error: {e}")

# ── 3. Test each canonical engine import ───────────────────────────
print("\n" + "=" * 70)
print("3. ENGINE IMPORT TESTS (via engines.__init__._ENGINE_MAP)")
print("=" * 70)

try:
    import engines
    engine_map = getattr(engines, '_ENGINE_MAP', {})
    print(f"  Total registered engines: {len(engine_map)}")
    print()

    for name, cls in sorted(engine_map.items()):
        if cls is not None:
            print(f"  ✓ {name:20s} → {cls.__module__}.{cls.__name__}")
            results["import_success"].append(name)
        else:
            print(f"  ✗ {name:20s} → None (import failed)")
            results["import_fail"].append(name)

    # Check what FAILED silently (set to None in __init__.py)
    print("\n  --- Failed imports (set to None) ---")
    for attr_name in engines.__all__:
        val = getattr(engines, attr_name, "MISSING")
        if val is None:
            print(f"  ✗ engines.{attr_name} = None (silently failed)")
            results["import_fail"].append(attr_name)

except Exception as e:
    print(f"  ✗ engines package import FAILED: {e}")
    traceback.print_exc()

# ── 4. Test individual engine instantiation ────────────────────────
print("\n" + "=" * 70)
print("4. ENGINE INSTANTIATION TESTS")
print("=" * 70)

for name in sorted(engine_map.keys()):
    cls = engine_map[name]
    if cls is None:
        print(f"  SKIP {name:20s} — class is None")
        continue
    try:
        # Check constructor signature
        import inspect
        sig = inspect.signature(cls.__init__)
        params = list(sig.parameters.keys())
        params = [p for p in params if p != 'self']

        if not params:
            obj = cls()
            print(f"  ✓ {name:20s} — no-arg constructor works")
        elif len(params) == 1 and 'db_path' in params[0].lower() or 'path' in str(params):
            # Try with db_path
            db_path = str(REPO / "litigation_context.db")
            obj = cls(db_path)
            print(f"  ✓ {name:20s} — constructor(db_path) works")
        else:
            print(f"  ? {name:20s} — constructor needs: {params} (skipped)")
    except Exception as e:
        err = str(e)[:80]
        print(f"  ✗ {name:20s} — INSTANTIATION FAILED: {err}")

# ── 5. Find hardcoded DB paths ─────────────────────────────────────
print("\n" + "=" * 70)
print("5. HARDCODED DATABASE PATHS")
print("=" * 70)

import re
hardcode_pattern = re.compile(
    r'(?:DB_PATH|db_path|database_path)\s*=.*(?:litigation_context|\.db)',
    re.IGNORECASE
)
path_resolve_pattern = re.compile(
    r'Path\(__file__\).*parents?\[\d+\].*(?:\.db|litigation)',
    re.IGNORECASE
)

for py_file in ENGINE_ROOT.rglob("*.py"):
    try:
        content = py_file.read_text(encoding="utf-8", errors="ignore")
        for i, line in enumerate(content.split("\n"), 1):
            if hardcode_pattern.search(line) or path_resolve_pattern.search(line):
                rel = py_file.relative_to(ENGINE_ROOT)
                print(f"  ⚠ {rel}:{i}")
                print(f"    {line.strip()[:100]}")
                results["hardcoded_paths"].append((str(rel), i, line.strip()[:100]))
    except Exception:
        pass

# ── 6. Identify non-canonical directories ──────────────────────────
print("\n" + "=" * 70)
print("6. NON-CANONICAL DIRECTORIES")
print("=" * 70)

CANONICAL = {
    "nexus", "chimera", "chronos", "cerberus", "filing_engine",
    "intake", "rebuttal", "narrative", "agents", "analytics",
    "semantic", "search", "typst", "ingest",
    # Extended (registered in __init__.py)
    "event_horizon", "oracle", "nemesis", "lexicon", "forge",
    "hydra_governor", "filing_assembler", "perception",
    # Analysis engines
    "irac", "damages", "causal", "adversary", "temporal", "hypergraph",
    # Infrastructure
    "__pycache__", "templates", "tests",
}

for d in sorted(ENGINE_ROOT.iterdir()):
    if d.is_dir() and d.name not in CANONICAL:
        # Check if it's registered in _ENGINE_MAP
        registered = d.name in engine_map
        has_init = (d / "__init__.py").exists()
        py_count = len(list(d.glob("*.py")))
        status = "REGISTERED" if registered else "ORPHAN"
        print(f"  {'✓' if registered else '?'} {d.name:30s} [{status}] init={has_init} files={py_count}")
        results["non_canonical"].append(d.name)

# ── 7. Standalone scripts in engines root ──────────────────────────
print("\n" + "=" * 70)
print("7. STANDALONE SCRIPTS (engines root)")
print("=" * 70)

for f in sorted(ENGINE_ROOT.glob("*.py")):
    if f.name == "__init__.py":
        continue
    size = f.stat().st_size
    print(f"  {f.name:45s} ({size:>8,} bytes)")
    results["standalone_scripts"].append(f.name)

# ── 8. Missing test files ──────────────────────────────────────────
print("\n" + "=" * 70)
print("8. TEST COVERAGE")
print("=" * 70)

for d in sorted(ENGINE_ROOT.iterdir()):
    if not d.is_dir() or d.name.startswith("_") or d.name == "tests":
        continue
    tests = list(d.glob("test_*.py")) + list(d.glob("*_test.py"))
    if tests:
        print(f"  ✓ {d.name:25s} has {len(tests)} test file(s)")
    else:
        print(f"  ✗ {d.name:25s} NO TESTS")
        results["missing_tests"].append(d.name)

# ── 9. Summary ─────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"  Engines import OK:    {len(results['import_success'])}")
print(f"  Engines import FAIL:  {len(results['import_fail'])}")
print(f"  Hardcoded DB paths:   {len(results['hardcoded_paths'])}")
print(f"  Non-canonical dirs:   {len(results['non_canonical'])}")
print(f"  Standalone scripts:   {len(results['standalone_scripts'])}")
print(f"  Engines without tests:{len(results['missing_tests'])}")

if results["import_fail"]:
    print(f"\n  FAILED IMPORTS: {', '.join(set(results['import_fail']))}")
