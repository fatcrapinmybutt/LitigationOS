#!/usr/bin/env python3
"""
LitigationOS Phase 10 CONVERGE — Integration Test Script
Tests DB connectivity, OMEGA scoring, critical file existence, and website build.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import os
import json
import sqlite3
import subprocess
import time
from pathlib import Path
from datetime import datetime

# ── Paths ──────────────────────────────────────────────────────────────
BASE_DIR = Path(r"C:\Users\andre\LitigationOS")
SYSTEM_DIR = BASE_DIR / "00_SYSTEM"
DB_PATH = Path(r"C:\Users\andre\litigation_context.db")
WEBSITE_DIR = SYSTEM_DIR / "apps" / "website"

# ── Test Framework ─────────────────────────────────────────────────────
class TestRunner:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
        self.skipped = 0

    def record(self, name, passed, detail=""):
        status = "PASS" if passed else "FAIL"
        self.results.append({"name": name, "status": status, "detail": detail})
        if passed:
            self.passed += 1
        else:
            self.failed += 1
        icon = "✅" if passed else "❌"
        print(f"  {icon} {name}")
        if detail and not passed:
            print(f"     └─ {detail[:120]}")

    def skip(self, name, reason=""):
        self.results.append({"name": name, "status": "SKIP", "detail": reason})
        self.skipped += 1
        print(f"  ⏭️  {name}  (skipped: {reason})")

    def summary(self):
        total = self.passed + self.failed + self.skipped
        print(f"\n{'=' * 60}")
        print(f"  Test Results: {self.passed} passed, {self.failed} failed, {self.skipped} skipped  ({total} total)")
        if self.failed == 0:
            print("  🎉 ALL TESTS PASSED")
        else:
            print("  ⚠️  SOME TESTS FAILED — review above")
        print(f"{'=' * 60}")
        return self.failed == 0


runner = TestRunner()


# ══════════════════════════════════════════════════════════════════════
#  TEST 1: Database Connectivity & Key Tables
# ══════════════════════════════════════════════════════════════════════
def test_db_connectivity():
    print("\n── Test Suite: Database ──────────────────────────────────")

    # 1a. DB file exists
    runner.record("DB file exists", DB_PATH.exists(), f"Expected at {DB_PATH}")
    if not DB_PATH.exists():
        runner.skip("DB connection", "DB file missing")
        runner.skip("Key tables exist", "DB file missing")
        return

    # 1b. Can connect
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        conn.execute("SELECT 1")
        runner.record("DB connection", True)
    except Exception as e:
        runner.record("DB connection", False, str(e))
        return

    # 1c. Key tables
    key_tables = [
        "omega_evolution_config",
        "omega_evolution_log",
        "omega_anomaly_log",
        "omega_alerts",
    ]
    all_tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    total_tables = len(all_tables)

    for t in key_tables:
        runner.record(f"Table exists: {t}", t in all_tables)

    runner.record(f"Total tables >= 4", total_tables >= 4, f"Found {total_tables} tables")
    conn.close()


# ══════════════════════════════════════════════════════════════════════
#  TEST 2: OMEGA Scoring Engine
# ══════════════════════════════════════════════════════════════════════
def test_omega_scoring():
    print("\n── Test Suite: OMEGA Scoring ─────────────────────────────")

    score_engine = SYSTEM_DIR / "omega" / "omega_score_engine.py"
    runner.record("omega_score_engine.py exists", score_engine.exists())

    if not score_engine.exists():
        runner.skip("OMEGA scoring produces output", "Script missing")
        return

    try:
        result = subprocess.run(
            [sys.executable, str(score_engine)],
            capture_output=True, text=True, timeout=60,
            cwd=str(SYSTEM_DIR), errors='replace'
        )
        has_output = len(result.stdout.strip()) > 0 or len(result.stderr.strip()) > 0
        runner.record(
            "OMEGA scoring produces output",
            has_output,
            f"exit={result.returncode}, stdout={len(result.stdout)}B, stderr={len(result.stderr)}B"
        )
        runner.record(
            "OMEGA scoring exits cleanly",
            result.returncode == 0,
            f"Return code: {result.returncode}" + (f" — {result.stderr[:100]}" if result.returncode != 0 else "")
        )
    except subprocess.TimeoutExpired:
        runner.record("OMEGA scoring produces output", False, "Timed out after 60s")
    except Exception as e:
        runner.record("OMEGA scoring produces output", False, str(e))


# ══════════════════════════════════════════════════════════════════════
#  TEST 3: Critical File Existence
# ══════════════════════════════════════════════════════════════════════
def test_critical_files():
    print("\n── Test Suite: Critical Files ────────────────────────────")

    critical_files = [
        # Phase 10 CONVERGE files
        SYSTEM_DIR / "omega" / "self_evolution.py",
        SYSTEM_DIR / "omega" / "observability.py",
        SYSTEM_DIR / "omega" / "autonomous_ops.json",
        SYSTEM_DIR / "tests" / "integration_test.py",
        # Core omega components
        SYSTEM_DIR / "omega" / "omega_score_engine.py",
        SYSTEM_DIR / "omega" / "filing_executor.py",
        SYSTEM_DIR / "omega" / "evidence_miner.py",
        SYSTEM_DIR / "omega" / "judicial_analysis.py",
        SYSTEM_DIR / "omega" / "predictive_model.py",
        SYSTEM_DIR / "omega" / "accountability.py",
        SYSTEM_DIR / "omega" / "emergency_protocol.py",
        # Website
        WEBSITE_DIR / "package.json",
        WEBSITE_DIR / "next.config.js",
    ]

    for f in critical_files:
        rel = f.relative_to(BASE_DIR)
        runner.record(f"Exists: {rel}", f.exists())

    # Check directories
    critical_dirs = [
        SYSTEM_DIR / "omega",
        SYSTEM_DIR / "agents",
        SYSTEM_DIR / "pipeline",
        SYSTEM_DIR / "apps" / "website",
        SYSTEM_DIR / "neo4j",
        SYSTEM_DIR / "engines",
    ]
    for d in critical_dirs:
        rel = d.relative_to(BASE_DIR)
        runner.record(f"Dir exists: {rel}", d.exists())


# ══════════════════════════════════════════════════════════════════════
#  TEST 4: Website Build
# ══════════════════════════════════════════════════════════════════════
def test_website_build():
    print("\n── Test Suite: Website Build ─────────────────────────────")

    pkg_json = WEBSITE_DIR / "package.json"
    if not pkg_json.exists():
        runner.skip("Website build", "package.json not found")
        return

    node_modules = WEBSITE_DIR / "node_modules"
    if not node_modules.exists():
        runner.skip("Website build", "node_modules missing — run npm install first")
        return

    try:
        print("  ⏳ Running next build (this may take a minute)…")
        result = subprocess.run(
            ["npx", "next", "build"],
            capture_output=True, text=True, timeout=180,
            cwd=str(WEBSITE_DIR), shell=True, errors='replace'
        )
        success = result.returncode == 0
        runner.record(
            "Website next build",
            success,
            "" if success else (result.stderr or result.stdout)[-200:]
        )
    except subprocess.TimeoutExpired:
        runner.record("Website next build", False, "Timed out after 180s")
    except Exception as e:
        runner.record("Website next build", False, str(e))


# ══════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════
def main():
    print("=" * 60)
    print("  🧪 LitigationOS — Integration Test Suite  (Phase 10)")
    print(f"  Run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    test_db_connectivity()
    test_omega_scoring()
    test_critical_files()
    test_website_build()

    all_passed = runner.summary()
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
