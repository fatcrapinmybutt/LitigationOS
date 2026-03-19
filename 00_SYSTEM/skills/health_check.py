#!/usr/bin/env python3
"""
LitigationOS Skills — Health Check & Diagnostics

Run:  python health_check.py
From: C:\\Users\\andre\\LitigationOS\\00_SYSTEM\\skills\\

Reports:
  - Database connectivity and table count
  - Per-skill import status
  - Self-test availability and results (optional)
"""

import sys
import os
import time
import sqlite3
import argparse

# Ensure the skills package is importable
_skills_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_skills_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from skills import (
    SKILL_REGISTRY,
    DB_PATH,
    list_skills,
    load_skill,
    check_db_connectivity,
    run_skill_selftest,
)

# ── Formatting helpers ───────────────────────────────────────────────────────
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def _ok(text: str) -> str:
    return f"{GREEN}{text}{RESET}"


def _err(text: str) -> str:
    return f"{RED}{text}{RESET}"


def _warn(text: str) -> str:
    return f"{YELLOW}{text}{RESET}"


def _header(text: str) -> str:
    return f"\n{BOLD}{CYAN}{'═' * 60}\n  {text}\n{'═' * 60}{RESET}"


# ── Health checks ────────────────────────────────────────────────────────────
def check_database() -> bool:
    """Test database connectivity and report stats."""
    print(_header("DATABASE CONNECTIVITY"))
    info = check_db_connectivity()

    print(f"  Path:       {info['path']}")
    print(f"  Exists:     {_ok('YES') if info['exists'] else _err('NO')}")
    print(f"  Accessible: {_ok('YES') if info['accessible'] else _err('NO')}")
    print(f"  Tables:     {info['table_count']}")

    if info["error"]:
        print(f"  Error:      {_err(info['error'])}")
        return False

    # Extra: check key tables used by skills
    key_tables = [
        "auth_rules", "evidence_quotes", "master_citations",
        "documents", "deadlines", "claims", "docket_events",
    ]
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        existing = {row[0] for row in cursor.fetchall()}
        conn.close()

        print(f"\n  {'Key Table':<28} {'Status':<10}")
        print(f"  {'─' * 28} {'─' * 10}")
        all_ok = True
        for table in key_tables:
            if table in existing:
                print(f"  {table:<28} {_ok('FOUND')}")
            else:
                print(f"  {table:<28} {_warn('MISSING')}")
                all_ok = False
        return all_ok
    except Exception as exc:
        print(f"  Table check error: {_err(str(exc))}")
        return False


def check_skills() -> int:
    """Load each skill and report status. Returns count of failures."""
    print(_header("SKILL IMPORT STATUS"))

    skills = list_skills()
    print(f"  Registered skills: {len(skills)}\n")
    print(f"  {'Skill':<28} {'Module':<35} {'Status':<10} {'Time'}")
    print(f"  {'─' * 28} {'─' * 35} {'─' * 10} {'─' * 8}")

    failures = 0
    for name in skills:
        module_name = SKILL_REGISTRY[name]
        t0 = time.perf_counter()
        try:
            load_skill(name)
            elapsed = time.perf_counter() - t0
            print(f"  {name:<28} {module_name:<35} {_ok('OK'):<20} {elapsed:.3f}s")
        except Exception as exc:
            elapsed = time.perf_counter() - t0
            failures += 1
            err_msg = str(exc)[:40]
            print(f"  {name:<28} {module_name:<35} {_err('FAIL'):<20} {elapsed:.3f}s")
            print(f"  {'':>28} └─ {_err(err_msg)}")

    return failures


def check_db_usage() -> None:
    """For each loaded skill, verify it can reach the DB."""
    print(_header("SKILL → DATABASE CONNECTIVITY"))

    skills = list_skills()
    print(f"\n  {'Skill':<28} {'Has DB_PATH':<14} {'DB Query':<10}")
    print(f"  {'─' * 28} {'─' * 14} {'─' * 10}")

    for name in skills:
        try:
            module = load_skill(name)
        except Exception:
            print(f"  {name:<28} {_err('IMPORT FAIL'):<24}")
            continue

        has_db = hasattr(module, "DB_PATH")
        db_path_val = getattr(module, "DB_PATH", None)

        # Try a lightweight query if the module has a DB path
        query_ok = False
        if db_path_val and os.path.isfile(db_path_val):
            try:
                conn = sqlite3.connect(db_path_val, timeout=3)
                conn.execute("SELECT 1")
                conn.close()
                query_ok = True
            except Exception:
                pass

        db_col = _ok("YES") if has_db else _warn("NO")
        q_col = _ok("OK") if query_ok else (_err("FAIL") if has_db else _warn("N/A"))
        print(f"  {name:<28} {db_col:<24} {q_col}")


def check_selftests(run_tests: bool = False) -> None:
    """Report self-test availability and optionally run them."""
    print(_header("SELF-TEST AVAILABILITY"))

    skills = list_skills()
    print(f"\n  {'Skill':<28} {'self_test()':<14} {'Result'}")
    print(f"  {'─' * 28} {'─' * 14} {'─' * 30}")

    for name in skills:
        try:
            module = load_skill(name)
        except Exception:
            print(f"  {name:<28} {_err('IMPORT FAIL'):<24}")
            continue

        has_fn = hasattr(module, "self_test") and callable(getattr(module, "self_test"))

        if not has_fn:
            print(f"  {name:<28} {_warn('NO'):<24} {'─'}")
            continue

        if not run_tests:
            print(f"  {name:<28} {_ok('YES'):<24} {'(use --run-selftests to execute)'}")
        else:
            result = run_skill_selftest(name)
            if result["error"]:
                print(f"  {name:<28} {_ok('YES'):<24} {_err(result['error'][:40])}")
            else:
                outcome = str(result["result"])[:40]
                print(f"  {name:<28} {_ok('YES'):<24} {_ok(outcome)}")


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="LitigationOS Skills Health Check"
    )
    parser.add_argument(
        "--run-selftests", action="store_true",
        help="Actually execute self_test() for skills that define one"
    )
    args = parser.parse_args()

    print(f"\n{BOLD}LitigationOS Skills — Health Check{RESET}")
    print(f"{'─' * 50}")

    db_ok = check_database()
    failures = check_skills()
    check_db_usage()
    check_selftests(run_tests=args.run_selftests)

    # ── Summary ──────────────────────────────────────────────────────────
    print(_header("SUMMARY"))
    total = len(SKILL_REGISTRY)
    passed = total - failures
    print(f"  Skills:   {passed}/{total} loaded successfully")
    print(f"  Database: {_ok('CONNECTED') if db_ok else _err('ISSUES DETECTED')}")

    if failures == 0 and db_ok:
        print(f"\n  {_ok('✓ ALL SYSTEMS OPERATIONAL')}\n")
        return 0
    else:
        print(f"\n  {_err(f'✗ {failures} skill(s) failed to load')}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
