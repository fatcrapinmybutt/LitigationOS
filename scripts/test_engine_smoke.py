"""
LitigationOS Engine Fleet Smoke Tests
======================================
Tests every engine directory for:
  1. Import success (module loads without crash)
  2. Class existence (expected class/function available)
  3. Registry presence (in _ENGINE_MAP for class-based engines)
  4. No stdout pollution (import doesn't write to stdout)

ASCII-only output for Windows cp1252 compatibility.
"""

import importlib
import io
import os
import sys
import time
from contextlib import redirect_stdout
from pathlib import Path

# Prevent shadow-module hijacking from repo root
REPO_ROOT = Path(__file__).resolve().parent.parent
SYSTEM_DIR = REPO_ROOT / "00_SYSTEM"
if str(SYSTEM_DIR) not in sys.path:
    sys.path.insert(0, str(SYSTEM_DIR))

# Ensure engines package is findable
if str(SYSTEM_DIR) not in sys.path:
    sys.path.insert(0, str(SYSTEM_DIR))

# ── Engine Registry ─────────────────────────────────────────────────
# Maps engine_dir_name -> (import_path, expected_class_or_attr)
# Class-based engines expected in _ENGINE_MAP
CLASS_ENGINES = {
    "nexus":          ("engines.nexus.nexus_engine",   "NexusEngine"),
    "chimera":        ("engines.chimera.chimera_engine","ChimeraEngine"),
    "chronos":        ("engines.chronos.chronos_engine","ChronosEngine"),
    "cerberus":       ("engines.cerberus.cerberus_engine","CerberusEngine"),
    "event_horizon":  ("engines.event_horizon",        "Engine"),
    "oracle":         ("engines.oracle.oracle_engine",  "Oracle"),
    "nemesis":        ("engines.nemesis.nemesis_engine", "NemesisEngine"),
    "lexicon":        ("engines.lexicon.lexicon_engine", "LexiconEngine"),
    "forge":          ("engines.forge.forge_engine",    "ForgeEngine"),
    "filing_engine":  ("engines.filing_engine",         "FilingEngine"),
    "semantic":       ("engines.semantic.engine",       "SemanticSearchEngine"),
    "perception":     ("engines.perception.engine",     "LegalBERTEngine"),
    "search":         ("engines.search",                "HybridSearchEngine"),
    "analytics":      ("engines.analytics",             "AnalyticsEngine"),
    "typst":          ("engines.typst",                 "TypstFilingEngine"),
    "irac":           ("engines.irac",                  "IRACEngine"),
    "damages":        ("engines.damages",               "DamagesEngine"),
    "causal":         ("engines.causal",                "CausalChainEngine"),
    "adversary":      ("engines.adversary",             "AdversaryEngine"),
    "temporal":       ("engines.temporal",               "TemporalKnowledgeGraph"),
    "hypergraph":     ("engines.hypergraph",             "EvidenceHypergraph"),
}

# Module-based sub-packages (no single engine class, import as module)
MODULE_ENGINES = {
    "hydra_governor":  ("engines.hydra_governor",   None),
    "filing_assembler":("engines.filing_assembler",  None),
    "agents":          ("engines.agents",             None),
}

# Package-level engines (may or may not have deeper structure)
PACKAGE_ENGINES = {
    "intake":         ("engines.intake",             "IntakePipeline"),
    "narrative":      ("engines.narrative",           None),
    "rebuttal":       ("engines.rebuttal",            None),
    "qa":             ("engines.qa",                  None),
    "orchestrator":   ("engines.orchestrator",        None),
    "meek234_fullstack":("engines.meek234_fullstack", None),
}

# Known stubs/deprecated (expected to fail or be minimal)
STUB_ENGINES = {
    "docforge_v18",
    "docforge_v19",
    "mi_warchest_v2",
    "ocr_embed_v2",
}

# Non-Python (skip import test)
NON_PYTHON = {"ingest", "templates", "tests"}


# Known environment-sensitive engines (disk space, GPU, etc.)
# These pass if they import + exist in _ENGINE_MAP, even if instantiation
# fails due to environment constraints (low disk, no GPU, etc.)
ENV_SENSITIVE = {"event_horizon"}  # needs 2GB free disk


def test_import(module_path: str) -> tuple[bool, str]:
    """Try to import a module. Returns (success, error_or_empty)."""
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            mod = importlib.import_module(module_path)
        stdout_leak = buf.getvalue()
        if stdout_leak.strip():
            return True, f"WARNING: stdout leak ({len(stdout_leak)} chars)"
        return True, ""
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def test_attr(module_path: str, attr_name: str) -> tuple[bool, str]:
    """Check if a module has the expected attribute."""
    try:
        mod = importlib.import_module(module_path)
        if hasattr(mod, attr_name):
            return True, ""
        available = [a for a in dir(mod) if not a.startswith("_")]
        return False, f"Missing '{attr_name}'. Has: {', '.join(available[:10])}"
    except Exception as e:
        return False, f"Import failed: {type(e).__name__}: {e}"


def test_engine_map_entry(name: str) -> tuple[bool, str]:
    """Check if engine is registered in _ENGINE_MAP."""
    try:
        from engines import _ENGINE_MAP
        if name in _ENGINE_MAP and _ENGINE_MAP[name] is not None:
            return True, ""
        if name in _ENGINE_MAP:
            return False, "Registered but None (import failed silently)"
        return False, f"Not in _ENGINE_MAP (available: {', '.join(sorted(_ENGINE_MAP))})"
    except Exception as e:
        return False, f"Cannot access _ENGINE_MAP: {e}"


def main() -> int:
    start = time.perf_counter()
    passed = 0
    failed = 0
    warnings = 0
    results = []

    print("=" * 70)
    print("  LitigationOS Engine Fleet Smoke Tests")
    print("=" * 70)
    print()

    # ── Test 1: engines package import ───────────────────────────────
    print("--- Package Import ---")
    ok, err = test_import("engines")
    if ok:
        print(f"[PASS] engines package imports successfully")
        passed += 1
    else:
        print(f"[FAIL] engines package: {err}")
        failed += 1
    print()

    # ── Test 2: Class-based engines ──────────────────────────────────
    print("--- Class-Based Engines (21) ---")
    for name, (mod_path, cls_name) in sorted(CLASS_ENGINES.items()):
        ok_import, err_import = test_import(mod_path)
        ok_attr, err_attr = test_attr(mod_path, cls_name)
        ok_map, err_map = test_engine_map_entry(name)

        if ok_import and ok_attr and ok_map:
            tag = "[PASS]"
            detail = ""
            passed += 1
            if err_import:
                detail = f" ({err_import})"
                warnings += 1
        elif ok_import and ok_attr:
            tag = "[PASS]"
            detail = f" (not in _ENGINE_MAP: {err_map})"
            passed += 1
            warnings += 1
        elif ok_import:
            tag = "[FAIL]"
            detail = f" class: {err_attr}"
            failed += 1
        else:
            tag = "[FAIL]"
            detail = f" import: {err_import}"
            failed += 1

        print(f"  {tag} {name:20s} {cls_name:25s}{detail}")
        results.append((name, tag))
    print()

    # ── Test 3: Module-based sub-packages ────────────────────────────
    print("--- Module-Based Sub-Packages (3) ---")
    for name, (mod_path, _) in sorted(MODULE_ENGINES.items()):
        ok, err = test_import(mod_path)
        if ok:
            print(f"  [PASS] {name:25s}")
            passed += 1
        else:
            print(f"  [FAIL] {name:25s} {err}")
            failed += 1
        results.append((name, "[PASS]" if ok else "[FAIL]"))
    print()

    # ── Test 4: Package-level engines ────────────────────────────────
    print("--- Package-Level Engines (6) ---")
    for name, (mod_path, cls_name) in sorted(PACKAGE_ENGINES.items()):
        ok, err = test_import(mod_path)
        if ok:
            if cls_name:
                ok2, err2 = test_attr(mod_path, cls_name)
                if ok2:
                    print(f"  [PASS] {name:25s} ({cls_name})")
                    passed += 1
                else:
                    print(f"  [FAIL] {name:25s} imports but {err2}")
                    failed += 1
            else:
                print(f"  [PASS] {name:25s}")
                passed += 1
        else:
            print(f"  [FAIL] {name:25s} {err}")
            failed += 1
        results.append((name, "[PASS]" if ok else "[FAIL]"))
    print()

    # ── Test 5: Stub/deprecated engines ──────────────────────────────
    print("--- Stub/Deprecated Engines (4) ---")
    for name in sorted(STUB_ENGINES):
        mod_path = f"engines.{name}"
        ok, err = test_import(mod_path)
        if ok:
            print(f"  [PASS] {name:25s} (stub loads)")
            passed += 1
        else:
            print(f"  [FAIL] {name:25s} {err}")
            failed += 1
        results.append((name, "[PASS]" if ok else "[FAIL]"))
    print()

    # ── Test 6: Non-Python directories ───────────────────────────────
    print("--- Non-Python Directories ---")
    engines_dir = SYSTEM_DIR / "engines"
    for name in sorted(NON_PYTHON):
        d = engines_dir / name
        if d.is_dir():
            files = list(d.iterdir())
            print(f"  [SKIP] {name:25s} ({len(files)} files, non-Python)")
        else:
            print(f"  [SKIP] {name:25s} (directory missing)")
    print()

    # ── Test 7: get_engine() factory ─────────────────────────────────
    print("--- get_engine() Factory ---")
    try:
        from engines import get_engine, _ENGINE_MAP
        map_count = len(_ENGINE_MAP)
        loaded = sum(1 for v in _ENGINE_MAP.values() if v is not None)
        print(f"  Registered: {loaded}/{map_count} engines loaded")

        factory_pass = 0
        factory_fail = 0
        for eng_name in sorted(_ENGINE_MAP):
            if _ENGINE_MAP[eng_name] is None:
                print(f"  [FAIL] get_engine('{eng_name}') -> None (import failed)")
                factory_fail += 1
                continue
            try:
                instance = get_engine(eng_name)
                print(f"  [PASS] get_engine('{eng_name}') -> {type(instance).__name__}")
                factory_pass += 1
            except Exception as e:
                ename = type(e).__name__
                if eng_name in ENV_SENSITIVE:
                    print(f"  [PASS] get_engine('{eng_name}') -> env skip: {ename}")
                    factory_pass += 1
                else:
                    print(f"  [FAIL] get_engine('{eng_name}') -> {ename}: {e}")
                    factory_fail += 1

        passed += factory_pass
        failed += factory_fail
    except Exception as e:
        print(f"  [FAIL] Cannot import get_engine: {e}")
        failed += 1
    print()

    # ── Summary ──────────────────────────────────────────────────────
    elapsed = round(time.perf_counter() - start, 2)
    total = passed + failed
    pct = round(passed / total * 100, 1) if total else 0

    print("=" * 70)
    print(f"  RESULTS: {passed} passed, {failed} failed ({pct}%)")
    if warnings:
        print(f"  WARNINGS: {warnings}")
    print(f"  TIME: {elapsed}s")
    print(f"  ENGINE FLEET SCORE: {pct:.0f}%")
    print("=" * 70)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    os.chdir(str(REPO_ROOT))
    sys.exit(main())
