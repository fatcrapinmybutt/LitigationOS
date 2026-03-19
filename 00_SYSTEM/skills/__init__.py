"""
LitigationOS Skill Registry — Auto-discovery, lazy loading, and health monitoring.

MBP LitigationOS 2026 v1.0
Skills: 33 Michigan-first litigation intelligence modules
  - 9 system skills (this package)
  - 16 local_model skills (local_model/skills/)
  - 8 core modules (local_model/)
Database: litigation_context.db (Pure SQLite, no external APIs)

Usage:
    from skills import list_skills, load_skill, get_skill_status

    # List available skills
    print(list_skills())

    # Load and use a skill
    timeline = load_skill('timeline_builder')

    # Check system health
    status = get_skill_status()
"""

import importlib
import logging
import sqlite3
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Canonical database path (shared by all skills) ──────────────────────────
DB_PATH = r"C:\Users\andre\litigation_context.db"

# ── Skill Registry: name → module filename (without .py) ────────────────────
# Prefixes: (none) = this package, @lm: = local_model/skills/, @lmroot: = local_model/
SKILL_REGISTRY: Dict[str, str] = {
    # ── System skills (this package) ────────────────────────────────────────
    "convergence_engine":        "skill_convergence_engine",
    "chess_mode":                "skill_chess_mode",
    "timeline_builder":          "skill_timeline_builder",
    "rose_glass_coherence":      "skill_rose_glass_coherence",
    "business_corporate":        "skill_business_corporate",
    "defenses_setoffs":          "skill_defenses_setoffs",
    "landlord_tenant":           "skill_landlord_tenant",
    "michigan_tort_lawsuit":     "skill_michigan_tort_lawsuit",
    "torts_claims":              "skill_torts_claims",
    # ── Local model skills (local_model/skills/) ────────────────────────────
    "jtc_complaint_generator":   "@lm:jtc_complaint_generator",
    "filing_package_generator":  "@lm:filing_package_generator",
    "adversary_war_room":        "@lm:adversary_war_room",
    "motion_generator":          "@lm:motion_generator",
    "order_analyzer":            "@lm:order_analyzer",
    "alienation_analyzer":       "@lm:alienation_analyzer",
    "forensic_analyzer":         "@lm:forensic_analyzer",
    "weaponization_tracker":     "@lm:weaponization_tracker",
    "evidence_clusterer":        "@lm:evidence_clusterer",
    "case_strength_scorer":      "@lm:case_strength_scorer",
    "narrative_builder":         "@lm:narrative_builder",
    "appellate_brief_builder":   "@lm:appellate_brief_builder",
    "authority_graph_navigator": "@lm:authority_graph_navigator",
    "citation_network":          "@lm:citation_network",
    "chronology_engine":         "@lm:chronology_engine",
    "discovery_engine":          "@lm:discovery_engine",
    "authority_search":          "@lm:authority_search",
    "cite_check":                "@lm:cite_check",
    "contradiction_finder":      "@lm:contradiction_finder",
    "deadline_calculator":       "@lm:deadline_calculator",
    "factor_analysis":           "@lm:factor_analysis",
    "impeachment_engine":        "@lm:impeachment_engine",
    "precedent_matcher":         "@lm:precedent_matcher",
    "lm_timeline_builder":       "@lm:timeline_builder",
    # ── Core modules (local_model/) ─────────────────────────────────────────
    "docket_analyzer":           "@lmroot:docket_analyzer",
    "compliance_checker":        "@lmroot:compliance_checker",
    "risk_assessor":             "@lmroot:risk_assessor",
    "witness_prep":              "@lmroot:witness_prep",
    "gap_resolver":              "@lmroot:gap_resolver",
    "message_intelligence":      "@lmroot:message_intelligence",
    "cross_reference_engine":    "@lmroot:cross_reference_engine",
    "harms_calculator":          "@lmroot:harms_calculator",
}

# Skills that define a `def self_test()` function
_SKILLS_WITH_SELFTEST = frozenset({
    "convergence_engine",
    "timeline_builder",
    "rose_glass_coherence",
    "michigan_tort_lawsuit",
})

# ── Cross-package import paths ───────────────────────────────────────────────
_SYSTEM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LM_SKILLS_DIR = os.path.join(_SYSTEM_DIR, "local_model", "skills")
_LM_ROOT_DIR = os.path.join(_SYSTEM_DIR, "local_model")

# ── Lazy-load cache ─────────────────────────────────────────────────────────
_loaded: Dict[str, Any] = {}


def list_skills() -> List[str]:
    """Return sorted list of registered skill names."""
    return sorted(SKILL_REGISTRY.keys())


def load_skill(name: str) -> Any:
    """Dynamically import and return a skill module by registry name.

    Supports three module path prefixes:
      - (none): relative import in this package (system skills)
      - @lm:   import from local_model/skills/
      - @lmroot: import from local_model/

    Raises KeyError if the skill name is unknown.
    Raises ImportError if the module cannot be loaded.
    """
    if name not in SKILL_REGISTRY:
        raise KeyError(
            f"Unknown skill: '{name}'. Available: {list_skills()}"
        )
    if name not in _loaded:
        module_path = SKILL_REGISTRY[name]
        try:
            if module_path.startswith("@lm:"):
                # Local model skill — import from local_model/skills/
                actual_name = module_path[4:]
                file_path = os.path.join(_LM_SKILLS_DIR, f"{actual_name}.py")
                module = _import_from_file(f"lm_skills.{actual_name}", file_path)
            elif module_path.startswith("@lmroot:"):
                # Core module — import from local_model/
                actual_name = module_path[8:]
                file_path = os.path.join(_LM_ROOT_DIR, f"{actual_name}.py")
                module = _import_from_file(f"lm_core.{actual_name}", file_path)
            else:
                # System skill — relative import in this package
                module = importlib.import_module(f".{module_path}", package=__name__)
            _loaded[name] = module
            logger.info("Loaded skill: %s (module: %s)", name, module_path)
        except Exception as exc:
            logger.error("Failed to load skill '%s': %s", name, exc)
            raise
    return _loaded[name]


def _import_from_file(module_name: str, file_path: str) -> Any:
    """Import a module directly from a file path (cross-package import)."""
    import importlib.util
    if not os.path.isfile(file_path):
        raise ImportError(f"Module file not found: {file_path}")
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot create module spec for: {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def unload_skill(name: str) -> bool:
    """Remove a skill from the cache, forcing re-import on next load."""
    if name in _loaded:
        del _loaded[name]
        logger.info("Unloaded skill: %s", name)
        return True
    return False


def run_skill_selftest(name: str) -> Dict[str, Any]:
    """Run a skill's self_test() if it defines one.

    Returns dict with keys: skill, has_selftest, result, error
    """
    result = {"skill": name, "has_selftest": False, "result": None, "error": None}

    try:
        module = load_skill(name)
    except Exception as exc:
        result["error"] = f"Import failed: {exc}"
        return result

    selftest_fn = getattr(module, "self_test", None)
    if selftest_fn is None or not callable(selftest_fn):
        result["has_selftest"] = False
        result["result"] = "No self_test() defined"
        return result

    result["has_selftest"] = True
    try:
        outcome = selftest_fn()
        result["result"] = outcome if outcome is not None else "Completed (no return value)"
        logger.info("Selftest passed for skill: %s", name)
    except Exception as exc:
        result["error"] = f"Selftest raised: {exc}"
        logger.error("Selftest failed for skill '%s': %s", name, exc)

    return result


def get_skill_status() -> Dict[str, str]:
    """Check which skills can be loaded successfully.

    Returns dict mapping skill name → 'OK' or 'ERROR: <message>'.
    """
    results: Dict[str, str] = {}
    for name in sorted(SKILL_REGISTRY.keys()):
        try:
            load_skill(name)
            results[name] = "OK"
        except Exception as exc:
            results[name] = f"ERROR: {exc}"
    return results


def check_db_connectivity() -> Dict[str, Any]:
    """Test database connectivity (shared by all skills).

    Returns dict with: path, exists, accessible, table_count, error
    """
    info: Dict[str, Any] = {
        "path": DB_PATH,
        "exists": os.path.isfile(DB_PATH),
        "accessible": False,
        "table_count": 0,
        "error": None,
    }
    if not info["exists"]:
        info["error"] = "Database file not found"
        return info

    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cursor = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
        )
        info["table_count"] = cursor.fetchone()[0]
        info["accessible"] = True
        conn.close()
    except Exception as exc:
        info["error"] = str(exc)

    return info


def get_full_health() -> Dict[str, Any]:
    """Comprehensive health report: DB + all skills + selftest availability."""
    return {
        "database": check_db_connectivity(),
        "skill_count": len(SKILL_REGISTRY),
        "skill_status": get_skill_status(),
        "selftest_available": sorted(_SKILLS_WITH_SELFTEST),
    }
