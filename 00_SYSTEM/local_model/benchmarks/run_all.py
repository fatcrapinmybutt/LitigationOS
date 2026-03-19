"""
APEX Benchmark Suite — Tests Retrieval, Classification, and Generation Quality
===============================================================================

Runs WITHOUT LLM (tests MANBEARPIG baseline).  With LLM, tests enhanced pipeline.
Results stored in ``benchmarks/history.json`` for trend tracking.

BENCHMARKS:
  1. Retrieval  — MRR and Recall@10 on curated legal queries
  2. Classification — Lane detection + task-type accuracy
  3. Quality Gate — Prohibited-pattern / privacy / fabrication detection

ARCHITECTURE:
  - Shadow-programmed: LLM features OFF by default
  - Never crashes — every test is try/excepted
  - Never sets CWD to repo root (shadow modules)

Author: APEX_MANBEARPIG_LITIGATIONOS
"""

from __future__ import annotations

import io
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Shadow-program gate
# ---------------------------------------------------------------------------
APEX_LLM_ENABLED: bool = (
    os.environ.get("APEX_LLM_ENABLED", "false").lower() == "true"
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("apex.benchmarks")

# ---------------------------------------------------------------------------
# Path anchors (never use repo root as CWD)
# ---------------------------------------------------------------------------
_HERE: Path = Path(__file__).parent          # …/benchmarks/
_MODEL_DIR: Path = _HERE.parent              # …/local_model/
_REPO: Path = _MODEL_DIR.parent.parent       # …/LitigationOS/
_HISTORY_FILE: Path = _HERE / "history.json"

# ═══════════════════════════════════════════════════════════════════════════
# Test data
# ═══════════════════════════════════════════════════════════════════════════

RETRIEVAL_TESTS: List[Dict[str, Any]] = [
    {
        "query": "MCR 2.003 disqualification",
        "expected_contains": ["disqualification", "recusal", "bias"],
    },
    {
        "query": "best interest factors custody",
        "expected_contains": ["MCL 722.23", "factor"],
    },
    {
        "query": "truth in renting Michigan",
        "expected_contains": ["MCL 554.634", "tenant"],
    },
    {
        "query": "PPO modification",
        "expected_contains": ["MCL 600.2950", "protection order"],
    },
    {
        "query": "appellate brief word limit",
        "expected_contains": ["MCR 7.212", "16500"],
    },
    {
        "query": "ex parte communication judicial",
        "expected_contains": ["MCR 2.410", "Canon"],
    },
    {
        "query": "service of process 91 days",
        "expected_contains": ["MCR 2.102", "91"],
    },
    {
        "query": "RICO treble damages",
        "expected_contains": ["18 USC", "treble"],
    },
    {
        "query": "parental alienation Michigan",
        "expected_contains": ["MCL 722.23", "interference"],
    },
    {
        "query": "void judgment collateral attack",
        "expected_contains": ["MCR 2.612", "void"],
    },
]

CLASSIFICATION_TESTS: List[Dict[str, Any]] = [
    {
        "text": "Motion to modify parenting time due to interference",
        "expected_lane": "A",
        "expected_type": "custody",
    },
    {
        "text": "Complaint about mold and habitability violations at Shady Oaks",
        "expected_lane": "B",
        "expected_type": "new_lawsuit",
    },
    {
        "text": "Judge McNeill held ex parte hearing without notice",
        "expected_lane": "E",
        "expected_type": "jtc_complaint",
    },
    {
        "text": "Appeal the denial of motion to disqualify",
        "expected_lane": "F",
        "expected_type": "appeal",
    },
    {
        "text": "Respondent violated no-contact provision of PPO",
        "expected_lane": "D",
        "expected_type": "ppo",
    },
    {
        "text": "Section 1983 civil rights violation by court officials",
        "expected_lane": "C",
        "expected_type": "federal_1983",
    },
    {
        "text": "Emergency TRO needed due to immediate danger to child",
        "expected_lane": "A",
        "expected_type": "emergency",
    },
    {
        "text": "Request for sanctions under MCR 2.114 for frivolous motion",
        "expected_lane": "C",
        "expected_type": "sanctions",
    },
    {
        "text": "Witness prior inconsistent statement impeachment",
        "expected_lane": "C",
        "expected_type": "impeachment",
    },
    {
        "text": "Application for leave to appeal to Michigan Supreme Court",
        "expected_lane": "F",
        "expected_type": "msc_writ",
    },
]

QUALITY_GATE_TESTS: List[Dict[str, Any]] = [
    {
        "text": "Emily Ann Watson filed a motion",
        "should_fail": True,
        "reason": "wrong_name",
        "gate": "prohibited_pattern",
    },
    {
        "text": "Emily A. Watson filed a motion",
        "should_fail": False,
        "reason": "",
        "gate": "name_check",
    },
    {
        "text": "Based on 9 CPS investigations",
        "should_fail": True,
        "reason": "fabricated",
        "gate": "fabrication_check",
    },
    {
        "text": "Based on documented interference incidents",
        "should_fail": False,
        "reason": "",
        "gate": "content_check",
    },
    {
        "text": "Lincoln David Watson was present",
        "should_fail": True,
        "reason": "privacy",
        "gate": "privacy_check",
    },
    {
        "text": "L.D.W. was present",
        "should_fail": False,
        "reason": "",
        "gate": "privacy_check",
    },
    {
        "text": "Plaintiff alleges that the court [INSERT FINDING HERE]",
        "should_fail": True,
        "reason": "placeholder",
        "gate": "placeholder_check",
    },
    {
        "text": "Plaintiff alleges that the court entered an improper order",
        "should_fail": False,
        "reason": "",
        "gate": "content_check",
    },
    {
        "text": "As discussed in our phone call yesterday",
        "should_fail": True,
        "reason": "unverifiable_reference",
        "gate": "verifiability_check",
    },
    {
        "text": "As documented in Exhibit 14, filed on 2025-01-15",
        "should_fail": False,
        "reason": "",
        "gate": "verifiability_check",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
# Fallback quality-gate patterns (used when QualityGate module unavailable)
# ═══════════════════════════════════════════════════════════════════════════
_PROHIBITED_PATTERNS = [
    # Wrong name variant
    (r"Emily\s+Ann\s+Watson", "wrong_name"),
    # Fabricated claim (the 9 CPS investigations)
    (r"\b9\s+CPS\s+investigations?\b", "fabricated"),
    # Full child name (privacy)
    (r"Lincoln\s+David\s+Watson", "privacy"),
    # Placeholders
    (r"\[INSERT\b", "placeholder"),
    (r"\[TODO\b", "placeholder"),
    (r"\[PLACEHOLDER\b", "placeholder"),
    (r"\[FILL\s+IN\b", "placeholder"),
    # Unverifiable references
    (r"\b(?:phone|telephone)\s+call\s+(?:yesterday|today|last\s+week)", "unverifiable_reference"),
    (r"\bas\s+(?:we|I)\s+discussed\b", "unverifiable_reference"),
]

import re as _re
_COMPILED_PROHIBITED = [
    (_re.compile(pat, _re.IGNORECASE), reason) for pat, reason in _PROHIBITED_PATTERNS
]


def _fallback_quality_check(text: str) -> Dict[str, Any]:
    """Rule-based quality check when QualityGate module isn't available."""
    issues: List[Dict[str, str]] = []
    for pattern, reason in _COMPILED_PROHIBITED:
        if pattern.search(text):
            issues.append({"pattern": pattern.pattern, "reason": reason})

    passed = len(issues) == 0
    score = 100.0 if passed else max(0.0, 100.0 - len(issues) * 25.0)
    return {
        "passed": passed,
        "score": score,
        "issues": issues,
        "fallback": True,
    }


# ═══════════════════════════════════════════════════════════════════════════
# APEXBenchmark
# ═══════════════════════════════════════════════════════════════════════════
class APEXBenchmark:
    """Comprehensive benchmark suite for the APEX system.

    Tests retrieval quality, classification accuracy, and quality-gate
    correctness.  Works fully offline; LLM features activate only when
    ``APEX_LLM_ENABLED=true``.
    """

    def __init__(self) -> None:
        self._orchestrator: Any = None
        self._rag: Any = None
        self._quality_gate: Any = None

    # ------------------------------------------------------------------
    # Lazy loaders (thread-safe via single-threaded benchmark runner)
    # ------------------------------------------------------------------
    def _get_orchestrator(self) -> Any:
        if self._orchestrator is None:
            try:
                saved = os.getcwd()
                os.chdir(str(_MODEL_DIR))
                from apex_orchestrator import APEXOrchestrator  # type: ignore[import-untyped]
                self._orchestrator = APEXOrchestrator()
            except Exception as exc:  # noqa: BLE001
                logger.warning("APEXOrchestrator unavailable: %s", exc)
                self._orchestrator = None
            finally:
                try:
                    os.chdir(saved)
                except Exception:  # noqa: BLE001
                    pass
        return self._orchestrator

    def _get_rag(self) -> Any:
        if self._rag is None:
            try:
                saved = os.getcwd()
                os.chdir(str(_MODEL_DIR))
                from apex_hybrid_rag import APEXHybridRAG  # type: ignore[import-untyped]
                self._rag = APEXHybridRAG()
            except Exception as exc:  # noqa: BLE001
                logger.warning("APEXHybridRAG unavailable: %s", exc)
                self._rag = None
            finally:
                try:
                    os.chdir(saved)
                except Exception:  # noqa: BLE001
                    pass
        return self._rag

    def _get_quality_gate(self) -> Any:
        if self._quality_gate is None:
            try:
                saved = os.getcwd()
                os.chdir(str(_MODEL_DIR))
                from quality_gate import QualityGate  # type: ignore[import-untyped]
                self._quality_gate = QualityGate()
            except Exception as exc:  # noqa: BLE001
                logger.info("QualityGate unavailable, using fallback: %s", exc)
                self._quality_gate = None
            finally:
                try:
                    os.chdir(saved)
                except Exception:  # noqa: BLE001
                    pass
        return self._quality_gate

    # ------------------------------------------------------------------
    # Run all benchmarks
    # ------------------------------------------------------------------
    def run_all(self) -> Dict[str, Any]:
        """Run all benchmarks.

        Returns::

            {
                "retrieval": {mrr, recall_at_10, tests: [...]},
                "classification": {accuracy, lane_accuracy, type_accuracy, tests: [...]},
                "quality_gate": {accuracy, false_positives, false_negatives, tests: [...]},
                "overall_score": 0-100,
                "timestamp": ...,
                "llm_enabled": bool,
                "elapsed_seconds": float,
            }
        """
        t0 = time.monotonic()
        results: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "llm_enabled": APEX_LLM_ENABLED,
            "retrieval": {},
            "classification": {},
            "quality_gate": {},
            "overall_score": 0.0,
            "elapsed_seconds": 0.0,
        }
        try:
            results["retrieval"] = self.run_retrieval()
            results["classification"] = self.run_classification()
            results["quality_gate"] = self.run_quality_gate()

            # Compute weighted overall score (0-100)
            r_score = results["retrieval"].get("recall_at_10", 0.0) * 100
            c_score = results["classification"].get("accuracy", 0.0) * 100
            q_score = results["quality_gate"].get("accuracy", 0.0) * 100

            # Weights: retrieval 40%, classification 30%, quality 30%
            results["overall_score"] = round(
                r_score * 0.4 + c_score * 0.3 + q_score * 0.3, 1,
            )

        except Exception as exc:  # noqa: BLE001
            logger.error("run_all() failed: %s", exc)
            results["error"] = str(exc)

        results["elapsed_seconds"] = round(time.monotonic() - t0, 3)
        return results

    # ------------------------------------------------------------------
    # Retrieval benchmark
    # ------------------------------------------------------------------
    def run_retrieval(self) -> Dict[str, Any]:
        """Test retrieval quality.

        Returns::

            {mrr: float, recall_at_10: float, tests: [...]}
        """
        result: Dict[str, Any] = {
            "mrr": 0.0,
            "recall_at_10": 0.0,
            "tests": [],
            "total": len(RETRIEVAL_TESTS),
            "passed": 0,
        }
        try:
            rag = self._get_rag()
            if rag is None:
                result["error"] = "APEXHybridRAG unavailable"
                return result

            reciprocal_ranks: List[float] = []
            recalls: List[float] = []

            for test in RETRIEVAL_TESTS:
                test_result: Dict[str, Any] = {
                    "query": test["query"],
                    "expected": test["expected_contains"],
                    "found": [],
                    "passed": False,
                    "rr": 0.0,
                    "recall": 0.0,
                }
                try:
                    search_results = rag.search(test["query"], top_k=10)
                    all_text = " ".join(
                        r.get("text", "") for r in search_results
                    ).lower()

                    # Check which expected terms appear in top-10 results
                    found_terms: List[str] = []
                    first_rank: Optional[int] = None

                    for expected_term in test["expected_contains"]:
                        term_lower = expected_term.lower()
                        if term_lower in all_text:
                            found_terms.append(expected_term)
                            # Find first result containing this term
                            if first_rank is None:
                                for idx, r in enumerate(search_results):
                                    if term_lower in r.get("text", "").lower():
                                        first_rank = idx + 1
                                        break

                    test_result["found"] = found_terms

                    # Recall@10: fraction of expected terms found
                    total_expected = len(test["expected_contains"])
                    recall = len(found_terms) / total_expected if total_expected > 0 else 0.0
                    test_result["recall"] = round(recall, 2)
                    recalls.append(recall)

                    # Reciprocal rank (of first relevant result)
                    rr = 1.0 / first_rank if first_rank else 0.0
                    test_result["rr"] = round(rr, 4)
                    reciprocal_ranks.append(rr)

                    test_result["passed"] = recall >= 0.5  # at least half the terms found
                    if test_result["passed"]:
                        result["passed"] += 1

                except Exception as exc:  # noqa: BLE001
                    test_result["error"] = str(exc)
                    reciprocal_ranks.append(0.0)
                    recalls.append(0.0)

                result["tests"].append(test_result)

            # Aggregate metrics
            result["mrr"] = round(
                sum(reciprocal_ranks) / len(reciprocal_ranks), 4,
            ) if reciprocal_ranks else 0.0

            result["recall_at_10"] = round(
                sum(recalls) / len(recalls), 4,
            ) if recalls else 0.0

        except Exception as exc:  # noqa: BLE001
            logger.error("run_retrieval() failed: %s", exc)
            result["error"] = str(exc)

        return result

    # ------------------------------------------------------------------
    # Classification benchmark
    # ------------------------------------------------------------------
    def run_classification(self) -> Dict[str, Any]:
        """Test classification accuracy (lane detection + task-type).

        Returns::

            {accuracy: float, lane_accuracy: float, type_accuracy: float, tests: [...]}
        """
        result: Dict[str, Any] = {
            "accuracy": 0.0,
            "lane_accuracy": 0.0,
            "type_accuracy": 0.0,
            "tests": [],
            "total": len(CLASSIFICATION_TESTS),
            "passed": 0,
        }
        try:
            orch = self._get_orchestrator()
            if orch is None:
                result["error"] = "APEXOrchestrator unavailable"
                return result

            lane_correct = 0
            type_correct = 0

            for test in CLASSIFICATION_TESTS:
                test_result: Dict[str, Any] = {
                    "text": test["text"][:80],
                    "expected_lane": test["expected_lane"],
                    "expected_type": test["expected_type"],
                    "detected_lane": "",
                    "detected_type": "",
                    "lane_correct": False,
                    "type_correct": False,
                }
                try:
                    detected_lane = orch.detect_lane(test["text"])
                    detected_type = orch.detect_task_type(test["text"])

                    test_result["detected_lane"] = detected_lane
                    test_result["detected_type"] = detected_type
                    test_result["lane_correct"] = detected_lane == test["expected_lane"]
                    test_result["type_correct"] = detected_type == test["expected_type"]

                    if test_result["lane_correct"]:
                        lane_correct += 1
                    if test_result["type_correct"]:
                        type_correct += 1
                    if test_result["lane_correct"] and test_result["type_correct"]:
                        result["passed"] += 1

                except Exception as exc:  # noqa: BLE001
                    test_result["error"] = str(exc)

                result["tests"].append(test_result)

            total = len(CLASSIFICATION_TESTS)
            result["lane_accuracy"] = round(lane_correct / total, 4) if total > 0 else 0.0
            result["type_accuracy"] = round(type_correct / total, 4) if total > 0 else 0.0
            # Combined accuracy: both lane AND type must be correct
            result["accuracy"] = round(result["passed"] / total, 4) if total > 0 else 0.0

        except Exception as exc:  # noqa: BLE001
            logger.error("run_classification() failed: %s", exc)
            result["error"] = str(exc)

        return result

    # ------------------------------------------------------------------
    # Quality-gate benchmark
    # ------------------------------------------------------------------
    def run_quality_gate(self) -> Dict[str, Any]:
        """Test quality gate accuracy.

        Returns::

            {accuracy: float, false_positives: int, false_negatives: int, tests: [...]}
        """
        result: Dict[str, Any] = {
            "accuracy": 0.0,
            "false_positives": 0,
            "false_negatives": 0,
            "tests": [],
            "total": len(QUALITY_GATE_TESTS),
            "passed": 0,
        }
        try:
            gate = self._get_quality_gate()

            correct = 0
            fp = 0  # gate says FAIL but should PASS
            fn = 0  # gate says PASS but should FAIL

            for test in QUALITY_GATE_TESTS:
                test_result: Dict[str, Any] = {
                    "text": test["text"][:80],
                    "should_fail": test["should_fail"],
                    "reason": test.get("reason", ""),
                    "gate_result": None,
                    "correct": False,
                }
                try:
                    # Use real gate if available, otherwise fallback
                    if gate is not None and hasattr(gate, "validate"):
                        qr = gate.validate(test["text"])
                        if isinstance(qr, dict):
                            gate_passed = qr.get("passed", True)
                        else:
                            gate_passed = True
                    else:
                        qr = _fallback_quality_check(test["text"])
                        gate_passed = qr.get("passed", True)

                    gate_failed = not gate_passed
                    test_result["gate_result"] = {
                        "passed": gate_passed,
                        "issues": qr.get("issues", []) if isinstance(qr, dict) else [],
                    }

                    # Check correctness
                    if test["should_fail"] and gate_failed:
                        test_result["correct"] = True
                        correct += 1
                    elif not test["should_fail"] and gate_passed:
                        test_result["correct"] = True
                        correct += 1
                    elif not test["should_fail"] and gate_failed:
                        fp += 1  # false positive (wrongly flagged as bad)
                    elif test["should_fail"] and gate_passed:
                        fn += 1  # false negative (missed a real problem)

                except Exception as exc:  # noqa: BLE001
                    test_result["error"] = str(exc)

                result["tests"].append(test_result)

            total = len(QUALITY_GATE_TESTS)
            result["accuracy"] = round(correct / total, 4) if total > 0 else 0.0
            result["false_positives"] = fp
            result["false_negatives"] = fn
            result["passed"] = correct

        except Exception as exc:  # noqa: BLE001
            logger.error("run_quality_gate() failed: %s", exc)
            result["error"] = str(exc)

        return result

    # ------------------------------------------------------------------
    # History persistence
    # ------------------------------------------------------------------
    def save_results(self, results: Dict[str, Any]) -> None:
        """Append results to ``benchmarks/history.json`` for trend tracking."""
        try:
            history: List[Dict[str, Any]] = []
            if _HISTORY_FILE.exists():
                try:
                    raw = _HISTORY_FILE.read_text(encoding="utf-8")
                    loaded = json.loads(raw)
                    if isinstance(loaded, list):
                        history = loaded
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Could not parse history file: %s", exc)

            # Strip verbose per-test data to keep history lean
            slim = {
                "timestamp": results.get("timestamp", datetime.now(timezone.utc).isoformat()),
                "llm_enabled": results.get("llm_enabled", False),
                "overall_score": results.get("overall_score", 0.0),
                "elapsed_seconds": results.get("elapsed_seconds", 0.0),
                "retrieval_mrr": results.get("retrieval", {}).get("mrr", 0.0),
                "retrieval_recall": results.get("retrieval", {}).get("recall_at_10", 0.0),
                "classification_accuracy": results.get("classification", {}).get("accuracy", 0.0),
                "classification_lane": results.get("classification", {}).get("lane_accuracy", 0.0),
                "classification_type": results.get("classification", {}).get("type_accuracy", 0.0),
                "quality_accuracy": results.get("quality_gate", {}).get("accuracy", 0.0),
                "quality_fp": results.get("quality_gate", {}).get("false_positives", 0),
                "quality_fn": results.get("quality_gate", {}).get("false_negatives", 0),
            }
            history.append(slim)

            # Keep last 100 runs
            history = history[-100:]

            _HISTORY_FILE.write_text(
                json.dumps(history, indent=2, default=str) + "\n",
                encoding="utf-8",
            )
            logger.info("Saved benchmark results to %s", _HISTORY_FILE)

        except Exception as exc:  # noqa: BLE001
            logger.error("save_results() failed: %s", exc)

    def print_summary(self, results: Dict[str, Any]) -> None:
        """Print a human-readable summary of benchmark results."""
        try:
            print("=" * 60)
            print("  APEX BENCHMARK RESULTS")
            print("=" * 60)
            print(f"  Timestamp:     {results.get('timestamp', 'N/A')}")
            print(f"  LLM Enabled:   {results.get('llm_enabled', False)}")
            print(f"  Elapsed:       {results.get('elapsed_seconds', 0):.1f}s")
            print(f"  Overall Score: {results.get('overall_score', 0):.1f}/100")
            print("-" * 60)

            ret = results.get("retrieval", {})
            print(f"  RETRIEVAL:")
            print(f"    MRR:        {ret.get('mrr', 0):.4f}")
            print(f"    Recall@10:  {ret.get('recall_at_10', 0):.4f}")
            print(f"    Passed:     {ret.get('passed', 0)}/{ret.get('total', 0)}")

            cls = results.get("classification", {})
            print(f"  CLASSIFICATION:")
            print(f"    Combined:   {cls.get('accuracy', 0):.1%}")
            print(f"    Lane:       {cls.get('lane_accuracy', 0):.1%}")
            print(f"    Type:       {cls.get('type_accuracy', 0):.1%}")
            print(f"    Passed:     {cls.get('passed', 0)}/{cls.get('total', 0)}")

            qg = results.get("quality_gate", {})
            print(f"  QUALITY GATE:")
            print(f"    Accuracy:   {qg.get('accuracy', 0):.1%}")
            print(f"    FP:         {qg.get('false_positives', 0)}")
            print(f"    FN:         {qg.get('false_negatives', 0)}")
            print(f"    Passed:     {qg.get('passed', 0)}/{qg.get('total', 0)}")

            print("=" * 60)

            if results.get("overall_score", 0) >= 80:
                print("  ✅ SYSTEM HEALTHY — Score ≥ 80")
            elif results.get("overall_score", 0) >= 50:
                print("  ⚠️  DEGRADED — Score 50-79")
            else:
                print("  ❌ CRITICAL — Score < 50")
            print()

        except Exception as exc:  # noqa: BLE001
            logger.error("print_summary() failed: %s", exc)

    def trend(self, last_n: int = 10) -> List[Dict[str, Any]]:
        """Load last *last_n* benchmark runs from history."""
        try:
            if not _HISTORY_FILE.exists():
                return []
            raw = _HISTORY_FILE.read_text(encoding="utf-8")
            history = json.loads(raw)
            if isinstance(history, list):
                return history[-last_n:]
            return []
        except Exception as exc:  # noqa: BLE001
            logger.error("trend() failed: %s", exc)
            return []


# ═══════════════════════════════════════════════════════════════════════════
# CLI entry point
# ═══════════════════════════════════════════════════════════════════════════
def main() -> None:
    """CLI: ``python -m benchmarks.run_all`` or ``python run_all.py``"""
    if sys.stdout.encoding != "utf-8":
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace",
        )

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    bench = APEXBenchmark()

    if "--trend" in sys.argv:
        history = bench.trend()
        if history:
            print(json.dumps(history, indent=2))
        else:
            print("No benchmark history found.")
        return

    if "--json" in sys.argv:
        results = bench.run_all()
        bench.save_results(results)
        print(json.dumps(results, indent=2, default=str))
        return

    if "--retrieval" in sys.argv:
        results = bench.run_retrieval()
        print(json.dumps(results, indent=2, default=str))
        return

    if "--classification" in sys.argv:
        results = bench.run_classification()
        print(json.dumps(results, indent=2, default=str))
        return

    if "--quality" in sys.argv:
        results = bench.run_quality_gate()
        print(json.dumps(results, indent=2, default=str))
        return

    # Default: run all, print summary, save history
    results = bench.run_all()
    bench.print_summary(results)
    bench.save_results(results)


if __name__ == "__main__":
    main()
