"""
RAG Evaluation — LitigationOS Legal AI
=======================================
Retrieval and generation quality measurement for the legal RAG pipeline.

Implements the RAG evaluation framework from rag-engineer + rag-implementation
skills, adapted for local-first (zero-LLM) evaluation:

  1. Retrieval precision / recall (when ground truth exists)
  2. Faithfulness — answer grounded in retrieved context
  3. Context relevance — retrieved docs relevant to query
  4. Answer coverage — query aspects addressed
  5. Citation accuracy — cited sources actually support claims
  6. Lane accuracy — evidence from correct case lane

All metrics computed via heuristic/statistical methods (no LLM-as-judge).
Designed for batch evaluation over test suites and continuous monitoring.

Usage:
    from legal_ai.rag_evaluation import RAGEvaluator, TestCase
    evaluator = RAGEvaluator()
    result = evaluator.evaluate_single(
        query="What MCR governs disqualification?",
        answer="MCR 2.003 governs judicial disqualification.",
        retrieved=[{"text": "MCR 2.003(C)(1)...", "source": "mcr_rules"}],
        expected_answer="MCR 2.003",
    )
    print(result.faithfulness, result.answer_coverage)
"""

from __future__ import annotations

import logging
import re
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

logger = logging.getLogger("legal_ai.rag_evaluation")


# ── Data Models (agent-tool-builder: clear schemas) ──────────────

@dataclass
class TestCase:
    """A single RAG evaluation test case.

    Tool Schema (for agent integration):
        query: str — The test query
        expected_answer: str — Ground truth answer (optional)
        relevant_doc_ids: list[str] — IDs of known-relevant documents
        expected_lane: str — Expected case lane (A-F)
        expected_citations: list[str] — Expected legal citations
        tags: list[str] — Category tags for filtering
    """
    query: str
    expected_answer: str = ""
    relevant_doc_ids: List[str] = field(default_factory=list)
    expected_lane: str = ""
    expected_citations: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class EvalMetrics:
    """Evaluation metrics for a single query.

    All scores are 0.0–1.0 where 1.0 is perfect.
    """
    # Retrieval quality
    retrieval_precision: float = 0.0
    retrieval_recall: float = 0.0
    retrieval_f1: float = 0.0

    # Generation quality
    faithfulness: float = 0.0
    answer_coverage: float = 0.0
    citation_accuracy: float = 0.0

    # Context quality
    context_relevance: float = 0.0

    # Domain-specific
    lane_accuracy: float = 0.0
    legal_citation_count: int = 0

    # Metadata
    query: str = ""
    time_ms: float = 0.0
    evidence_count: int = 0
    warnings: List[str] = field(default_factory=list)


@dataclass
class EvalReport:
    """Aggregate evaluation report across a test suite.

    Tool Schema:
        name: rag_eval_report
        description: Aggregate RAG evaluation metrics across test suite.
        returns: EvalReport with per-metric averages and failure analysis.
    """
    total_cases: int = 0
    passed: int = 0
    failed: int = 0

    avg_retrieval_precision: float = 0.0
    avg_retrieval_recall: float = 0.0
    avg_retrieval_f1: float = 0.0
    avg_faithfulness: float = 0.0
    avg_answer_coverage: float = 0.0
    avg_citation_accuracy: float = 0.0
    avg_context_relevance: float = 0.0
    avg_lane_accuracy: float = 0.0

    total_time_ms: float = 0.0
    per_case_results: List[EvalMetrics] = field(default_factory=list)
    failure_analysis: Dict[str, int] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


# ── Legal citation pattern ───────────────────────────────────────

_CITATION_PATTERN = re.compile(
    r"(?:MCL|MCR|MRE)\s+\d+[\.\d]*"
    r"|(?:\d+\s+(?:Mich(?:\s+App)?|U\.?S\.?|F\.?\d*d?|S\.?\s*Ct\.?)\s+\d+)"
    r"|(?:\d+\s+USC\s+§?\s*\d+)",
    re.IGNORECASE,
)

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")


# ── Thresholds ───────────────────────────────────────────────────

PASS_THRESHOLDS = {
    "faithfulness": 0.5,
    "answer_coverage": 0.3,
    "context_relevance": 0.3,
    "citation_accuracy": 0.5,
}


# ── Main Evaluator ───────────────────────────────────────────────

class RAGEvaluator:
    """
    Heuristic-based RAG evaluation engine.

    Measures retrieval and generation quality WITHOUT requiring
    an external LLM.  Uses token overlap, citation matching,
    and structural heuristics.

    Follows autonomous-agent-patterns: clear tool schemas,
    explicit error handling, progress reporting.
    """

    def __init__(self, pass_thresholds: Optional[Dict[str, float]] = None):
        self._thresholds = pass_thresholds or dict(PASS_THRESHOLDS)
        self._total_evals: int = 0
        self._total_time_ms: float = 0.0

    # ── Single Evaluation ────────────────────────────────────────

    def evaluate_single(
        self,
        query: str,
        answer: str,
        retrieved: Sequence[Dict[str, Any]],
        expected_answer: str = "",
        relevant_doc_ids: Optional[Sequence[str]] = None,
        expected_lane: str = "",
        expected_citations: Optional[Sequence[str]] = None,
    ) -> EvalMetrics:
        """
        Evaluate a single RAG query-answer pair.

        Args:
            query:             The user query.
            answer:            The generated answer.
            retrieved:         List of retrieved evidence dicts (text, source, lane).
            expected_answer:   Ground truth (for coverage scoring).
            relevant_doc_ids:  Known-relevant document IDs (for precision/recall).
            expected_lane:     Expected case lane A-F (for lane accuracy).
            expected_citations: Expected legal citations (for citation accuracy).

        Returns:
            EvalMetrics with all computed scores.
        """
        t0 = time.perf_counter()
        self._total_evals += 1
        warnings: List[str] = []

        metrics = EvalMetrics(query=query, evidence_count=len(retrieved))

        # ── Retrieval precision / recall ─────────────────────────
        if relevant_doc_ids:
            retrieved_ids = {
                r.get("source", r.get("id", "")) for r in retrieved
            }
            relevant_set = set(relevant_doc_ids)

            if retrieved_ids:
                tp = len(retrieved_ids & relevant_set)
                metrics.retrieval_precision = tp / len(retrieved_ids) if retrieved_ids else 0.0
                metrics.retrieval_recall = tp / len(relevant_set) if relevant_set else 0.0
                if metrics.retrieval_precision + metrics.retrieval_recall > 0:
                    metrics.retrieval_f1 = (
                        2 * metrics.retrieval_precision * metrics.retrieval_recall
                        / (metrics.retrieval_precision + metrics.retrieval_recall)
                    )

        # ── Faithfulness (answer grounded in context) ────────────
        metrics.faithfulness = self._compute_faithfulness(answer, retrieved)

        # ── Answer coverage (addresses the query) ────────────────
        metrics.answer_coverage = self._compute_coverage(
            query, answer, expected_answer
        )

        # ── Context relevance (retrieved docs relevant to query) ─
        metrics.context_relevance = self._compute_context_relevance(
            query, retrieved
        )

        # ── Citation accuracy ────────────────────────────────────
        answer_citations = _CITATION_PATTERN.findall(answer)
        metrics.legal_citation_count = len(answer_citations)

        if expected_citations:
            metrics.citation_accuracy = self._compute_citation_accuracy(
                answer_citations, list(expected_citations)
            )
        elif answer_citations:
            # Check citations appear in retrieved context
            context_text = " ".join(r.get("text", "") for r in retrieved)
            found = sum(
                1 for c in answer_citations
                if c.lower() in context_text.lower()
            )
            metrics.citation_accuracy = found / len(answer_citations) if answer_citations else 0.0

        # ── Lane accuracy ────────────────────────────────────────
        if expected_lane:
            detected_lanes = {r.get("lane", "") for r in retrieved if r.get("lane")}
            if detected_lanes:
                metrics.lane_accuracy = 1.0 if expected_lane.upper() in {
                    l.upper() for l in detected_lanes
                } else 0.0
            else:
                warnings.append("No lane info in retrieved evidence")

        metrics.warnings = warnings
        elapsed = (time.perf_counter() - t0) * 1000
        metrics.time_ms = round(elapsed, 2)
        self._total_time_ms += elapsed

        return metrics

    # ── Batch Evaluation ─────────────────────────────────────────

    def evaluate_suite(
        self,
        test_cases: Sequence[TestCase],
        rag_fn: Any,
    ) -> EvalReport:
        """
        Evaluate a full test suite.

        Args:
            test_cases: List of TestCase objects.
            rag_fn:     Callable(query: str) -> dict with keys:
                        'answer', 'retrieved' (list of evidence dicts).

        Returns:
            EvalReport with aggregate metrics and failure analysis.
        """
        report = EvalReport(total_cases=len(test_cases))
        failure_reasons: Dict[str, int] = {}

        for tc in test_cases:
            try:
                result = rag_fn(tc.query)
                answer = result.get("answer", "")
                retrieved = result.get("retrieved", [])

                metrics = self.evaluate_single(
                    query=tc.query,
                    answer=answer,
                    retrieved=retrieved,
                    expected_answer=tc.expected_answer,
                    relevant_doc_ids=tc.relevant_doc_ids,
                    expected_lane=tc.expected_lane,
                    expected_citations=tc.expected_citations,
                )

                report.per_case_results.append(metrics)

                # Check pass/fail
                passed = True
                for metric_name, threshold in self._thresholds.items():
                    score = getattr(metrics, metric_name, 0.0)
                    if score < threshold:
                        passed = False
                        failure_reasons[metric_name] = (
                            failure_reasons.get(metric_name, 0) + 1
                        )

                if passed:
                    report.passed += 1
                else:
                    report.failed += 1

            except Exception as exc:
                logger.warning("Test case failed: %s — %s", tc.query[:50], exc)
                report.failed += 1
                failure_reasons["exception"] = (
                    failure_reasons.get("exception", 0) + 1
                )

        # Aggregate metrics
        n = len(report.per_case_results)
        if n > 0:
            report.avg_retrieval_precision = round(
                sum(m.retrieval_precision for m in report.per_case_results) / n, 4
            )
            report.avg_retrieval_recall = round(
                sum(m.retrieval_recall for m in report.per_case_results) / n, 4
            )
            report.avg_retrieval_f1 = round(
                sum(m.retrieval_f1 for m in report.per_case_results) / n, 4
            )
            report.avg_faithfulness = round(
                sum(m.faithfulness for m in report.per_case_results) / n, 4
            )
            report.avg_answer_coverage = round(
                sum(m.answer_coverage for m in report.per_case_results) / n, 4
            )
            report.avg_citation_accuracy = round(
                sum(m.citation_accuracy for m in report.per_case_results) / n, 4
            )
            report.avg_context_relevance = round(
                sum(m.context_relevance for m in report.per_case_results) / n, 4
            )
            report.avg_lane_accuracy = round(
                sum(m.lane_accuracy for m in report.per_case_results) / n, 4
            )
            report.total_time_ms = round(
                sum(m.time_ms for m in report.per_case_results), 2
            )

        report.failure_analysis = failure_reasons
        report.recommendations = self._generate_recommendations(report)

        return report

    # ── Metric Computation ───────────────────────────────────────

    def _compute_faithfulness(
        self,
        answer: str,
        retrieved: Sequence[Dict[str, Any]],
    ) -> float:
        """
        Measure how much of the answer is grounded in retrieved context.

        Splits answer into sentences, checks each against context via
        token overlap. Returns fraction of grounded sentences.
        """
        if not answer or not retrieved:
            return 0.0

        context_text = " ".join(r.get("text", "") for r in retrieved).lower()
        context_tokens = set(self._tokenize(context_text))

        if not context_tokens:
            return 0.0

        sentences = _SENTENCE_SPLIT.split(answer)
        if not sentences:
            return 0.0

        grounded_count = 0
        for sent in sentences:
            sent_tokens = set(self._tokenize(sent.lower()))
            if not sent_tokens:
                continue
            overlap = len(sent_tokens & context_tokens) / len(sent_tokens)
            if overlap >= 0.4:  # 40% token overlap = grounded
                grounded_count += 1

        return grounded_count / len(sentences) if sentences else 0.0

    def _compute_coverage(
        self,
        query: str,
        answer: str,
        expected: str = "",
    ) -> float:
        """
        Measure how well the answer covers the query's information need.

        If expected answer provided: token overlap with expected.
        Otherwise: token overlap between query keywords and answer.
        """
        if not answer:
            return 0.0

        answer_lower = answer.lower()
        answer_tokens = set(self._tokenize(answer_lower))

        if expected:
            expected_tokens = set(self._tokenize(expected.lower()))
            if not expected_tokens:
                return 0.0
            return len(answer_tokens & expected_tokens) / len(expected_tokens)

        # No expected answer — check query keyword coverage
        query_tokens = set(self._tokenize(query.lower())) - _STOP_WORDS
        if not query_tokens:
            return 0.5  # Can't measure, assume partial

        covered = len(query_tokens & answer_tokens)
        return covered / len(query_tokens)

    def _compute_context_relevance(
        self,
        query: str,
        retrieved: Sequence[Dict[str, Any]],
    ) -> float:
        """
        Measure how relevant the retrieved documents are to the query.

        Uses token overlap between query and each document.
        Returns average relevance across retrieved docs.
        """
        if not retrieved:
            return 0.0

        query_tokens = set(self._tokenize(query.lower())) - _STOP_WORDS
        if not query_tokens:
            return 0.5

        relevance_scores = []
        for doc in retrieved:
            doc_text = doc.get("text", "").lower()
            doc_tokens = set(self._tokenize(doc_text))
            if doc_tokens:
                overlap = len(query_tokens & doc_tokens) / len(query_tokens)
                relevance_scores.append(min(overlap, 1.0))

        return sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0

    def _compute_citation_accuracy(
        self,
        found_citations: List[str],
        expected_citations: List[str],
    ) -> float:
        """Check how many expected citations appear in the answer."""
        if not expected_citations:
            return 1.0 if not found_citations else 0.5

        found_norm = {c.lower().strip() for c in found_citations}
        expected_norm = {c.lower().strip() for c in expected_citations}

        if not expected_norm:
            return 1.0

        matched = sum(
            1 for exp in expected_norm
            if any(exp in f or f in exp for f in found_norm)
        )
        return matched / len(expected_norm)

    # ── Recommendations Engine ───────────────────────────────────

    def _generate_recommendations(self, report: EvalReport) -> List[str]:
        """Generate actionable recommendations from evaluation results."""
        recs: List[str] = []

        if report.avg_faithfulness < 0.5:
            recs.append(
                "LOW FAITHFULNESS: Answers not well-grounded in evidence. "
                "Consider: (1) increase top_k retrieval, (2) add reranking step, "
                "(3) strengthen corrective RAG loop threshold."
            )

        if report.avg_retrieval_precision < 0.3:
            recs.append(
                "LOW RETRIEVAL PRECISION: Too many irrelevant documents retrieved. "
                "Consider: (1) add metadata filtering by lane, (2) use cross-encoder "
                "reranking, (3) tune FTS5 query syntax."
            )

        if report.avg_retrieval_recall < 0.3:
            recs.append(
                "LOW RETRIEVAL RECALL: Missing relevant documents. "
                "Consider: (1) expand query with legal thesaurus, (2) search "
                "more brain databases, (3) increase fetch_k for broader search."
            )

        if report.avg_context_relevance < 0.3:
            recs.append(
                "LOW CONTEXT RELEVANCE: Retrieved docs don't match queries well. "
                "Consider: (1) improve chunking boundaries, (2) add hybrid search "
                "(BM25 + semantic), (3) use MMR for diversity."
            )

        if report.avg_citation_accuracy < 0.5:
            recs.append(
                "LOW CITATION ACCURACY: Citations in answers don't match expected. "
                "Consider: (1) run citation_extractor validation, (2) cross-ref "
                "against mcr_rules.db, (3) flag hallucinated citations."
            )

        if report.avg_lane_accuracy < 0.7:
            recs.append(
                "LOW LANE ACCURACY: Evidence from wrong case lanes. "
                "Consider: (1) add lane pre-filter to retrieval, (2) strengthen "
                "MEEK signal detection, (3) add lane metadata to FTS5 index."
            )

        if not recs:
            recs.append("ALL METRICS PASSING — RAG pipeline performing well.")

        return recs

    # ── Utilities ────────────────────────────────────────────────

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Simple whitespace + punctuation tokenizer."""
        return re.findall(r"\b\w+\b", text)

    def get_stats(self) -> Dict[str, Any]:
        """Return evaluator statistics."""
        return {
            "total_evaluations": self._total_evals,
            "total_time_ms": round(self._total_time_ms, 2),
            "avg_time_ms": round(
                self._total_time_ms / self._total_evals, 2
            ) if self._total_evals > 0 else 0.0,
            "thresholds": dict(self._thresholds),
        }


# ── Stop Words (for query keyword extraction) ───────────────────

_STOP_WORDS: Set[str] = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "as", "into", "through", "during", "before", "after", "above", "below",
    "between", "out", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "both",
    "each", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "just",
    "because", "but", "and", "or", "if", "while", "about", "what", "which",
    "who", "whom", "this", "that", "these", "those", "am", "it", "its",
}


# ── Built-in Test Suite (Michigan Litigation) ────────────────────

LITIGATION_TEST_SUITE: List[TestCase] = [
    TestCase(
        query="What MCR governs judicial disqualification?",
        expected_answer="MCR 2.003 governs disqualification of judges.",
        expected_citations=["MCR 2.003"],
        expected_lane="E",
        tags=["misconduct", "mcr"],
    ),
    TestCase(
        query="What are the best interest factors under Michigan law?",
        expected_answer="MCL 722.23 lists 12 best interest factors for child custody.",
        expected_citations=["MCL 722.23"],
        expected_lane="A",
        tags=["custody", "mcl"],
    ),
    TestCase(
        query="What statute governs Michigan RICO?",
        expected_answer="MCL 750.159i governs civil RICO in Michigan.",
        expected_citations=["MCL 750.159i"],
        expected_lane="B",
        tags=["housing", "rico", "mcl"],
    ),
    TestCase(
        query="What MCR governs motion practice timing?",
        expected_answer="MCR 2.119 governs motion practice including timing requirements.",
        expected_citations=["MCR 2.119"],
        tags=["procedure", "mcr"],
    ),
    TestCase(
        query="What is the standard for PPO modification?",
        expected_answer="MCL 600.2950 governs PPO issuance and modification.",
        expected_citations=["MCL 600.2950"],
        expected_lane="D",
        tags=["ppo", "mcl"],
    ),
    TestCase(
        query="What federal statute protects parental liberty?",
        expected_answer="The 14th Amendment Due Process Clause protects parental liberty.",
        expected_citations=["42 USC 1983"],
        expected_lane="E",
        tags=["federal", "constitutional"],
    ),
    TestCase(
        query="What is the standard of review for custody on appeal?",
        expected_answer="Custody decisions reviewed for abuse of discretion; findings of fact for clear error.",
        expected_lane="F",
        tags=["appellate", "custody"],
    ),
    TestCase(
        query="What Michigan law governs mobile home parks?",
        expected_answer="MCL 125.2301 et seq. is the Mobile Home Commission Act.",
        expected_citations=["MCL 125.2301"],
        expected_lane="B",
        tags=["housing", "mcl"],
    ),
]
