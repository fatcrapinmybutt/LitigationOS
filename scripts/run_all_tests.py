"""
LitigationOS Unified Test Runner
=================================
Runs all test suites and produces a consolidated pass/fail report.

Usage:
    python scripts/run_all_tests.py
"""

import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

TEST_SUITES: list[dict[str, str]] = [
    {"name": "Engine Smoke Tests", "script": "scripts/test_engine_smoke.py"},
    {"name": "Engine Convergence", "script": "scripts/test_engines_init.py"},
    {"name": "Filing Engine", "script": "scripts/test_filing_engine.py"},
    {"name": "Intake Engine", "script": "scripts/test_intake_engine.py"},
    {"name": "Error Paths", "script": "scripts/test_error_paths.py"},
    {"name": "Validator Accuracy", "script": "scripts/test_validator_accuracy.py"},
    {"name": "Integration Wave 4", "script": "scripts/test_integration_wave4.py"},
]


@dataclass
class SuiteResult:
    """Result of a single test suite run."""
    name: str
    passed: int = 0
    failed: int = 0
    duration_sec: float = 0.0
    output: str = ""
    returncode: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.passed + self.failed

    @property
    def ok(self) -> bool:
        return self.failed == 0 and self.returncode == 0


def _count_results(output: str) -> tuple[int, int]:
    """Parse PASS/FAIL counts from test script stdout.

    Recognizes ✅/❌ (existing suites) and ✓/✗ (Wave 3+ suites).
    Also parses 'N passed, M failed' summary lines as fallback.
    """
    passed = failed = 0
    for line in output.splitlines():
        stripped = line.strip()
        # ASCII markers (primary) + Unicode fallback
        if stripped.startswith("[PASS]") or stripped.startswith("PASS:") or stripped.startswith("[OK]"):
            passed += 1
        elif stripped.startswith("[FAIL]") or stripped.startswith("FAIL:"):
            failed += 1
        # Legacy unicode markers (kept for backward compat)
        elif any(stripped.startswith(c) for c in ("\u2705", "\u2713")):
            passed += 1
        elif any(stripped.startswith(c) for c in ("\u274c", "\u2717")):
            failed += 1
    # Fallback: parse summary line like "RESULTS: 14 passed, 0 failed"
    if passed == 0 and failed == 0:
        import re
        m = re.search(r'(\d+)\s+passed,\s+(\d+)\s+failed', output)
        if m:
            passed, failed = int(m.group(1)), int(m.group(2))
    return passed, failed


def run_suite(suite: dict[str, str]) -> SuiteResult:
    """Execute a single test suite and capture results."""
    name = suite["name"]
    script = REPO_ROOT / suite["script"]
    result = SuiteResult(name=name)

    if not script.exists():
        result.failed = 1
        result.errors.append(f"Script not found: {script}")
        result.returncode = 1
        return result

    start = time.perf_counter()
    try:
        proc = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(REPO_ROOT),
        )
        result.output = proc.stdout + proc.stderr
        result.returncode = proc.returncode
    except subprocess.TimeoutExpired:
        result.output = "(timed out after 300s)"
        result.returncode = 1
        result.errors.append("Timeout")
    except Exception as exc:
        result.output = str(exc)
        result.returncode = 1
        result.errors.append(str(exc))

    result.duration_sec = round(time.perf_counter() - start, 2)
    result.passed, result.failed = _count_results(result.output)

    # If subprocess failed but we counted 0 failures, mark at least 1
    if result.returncode != 0 and result.failed == 0:
        result.failed = 1

    return result


def main() -> int:
    """Run all suites and print consolidated report."""
    print("=" * 60)
    print("  LitigationOS Unified Test Runner")
    print("=" * 60)
    print()

    total_start = time.perf_counter()
    results: list[SuiteResult] = []

    for suite in TEST_SUITES:
        print(f"> Running: {suite['name']} ...")
        sr = run_suite(suite)
        results.append(sr)

        status = "[PASS]" if sr.ok else "[FAIL]"
        print(f"  {status}  ({sr.passed} passed, {sr.failed} failed, {sr.duration_sec}s)")
        if not sr.ok:
            # Show last 20 lines of output on failure
            tail = "\n".join(sr.output.strip().splitlines()[-20:])
            if tail:
                print(f"  --- output tail ---\n{tail}\n  ---")
        print()

    total_time = round(time.perf_counter() - total_start, 2)

    # Consolidated summary
    total_passed = sum(r.passed for r in results)
    total_failed = sum(r.failed for r in results)
    all_ok = all(r.ok for r in results)

    print("=" * 60)
    print("  CONSOLIDATED RESULTS")
    print("=" * 60)
    for r in results:
        tag = "PASS" if r.ok else "FAIL"
        print(f"  [{tag:4s}] {r.name:<25s}  {r.passed:>3d} passed  {r.failed:>3d} failed  {r.duration_sec:>6.2f}s")
    print("-" * 60)
    print(f"  TOTAL: {total_passed} passed, {total_failed} failed, {total_time}s")
    print(f"  STATUS: {'ALL PASSED' if all_ok else 'FAILURES DETECTED'}")
    print("=" * 60)

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
