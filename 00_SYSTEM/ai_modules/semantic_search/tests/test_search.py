"""Tests for SemanticSearchEngine — end-to-end integration."""
from __future__ import annotations

import pytest

from semantic_search.search_engine import SemanticSearchEngine


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

DOCS = [
    {
        "file_path": "/evidence/custody_report.pdf",
        "text": (
            "The custody evaluation report recommends joint legal custody "
            "with primary physical custody to the mother. The evaluator "
            "noted concerns about the father's inconsistent visitation "
            "schedule and lack of stable housing."
        ),
        "lane": "A",
        "case_number": "2024-001507-DC",
        "page_number": 1,
    },
    {
        "file_path": "/evidence/housing_complaint.pdf",
        "text": (
            "Shady Oaks management failed to address black mould in unit "
            "twelve for over six months despite repeated written complaints. "
            "The tenant submitted maintenance requests on January third, "
            "February fifteenth, and April ninth of two thousand twenty five."
        ),
        "lane": "B",
        "case_number": "2025-002760-CZ",
        "page_number": 1,
    },
    {
        "file_path": "/evidence/judicial_misconduct.pdf",
        "text": (
            "Judge McNeill demonstrated bias by refusing to allow the "
            "defendant to present exculpatory evidence during the hearing "
            "on October seventh. The transcript shows the judge interrupted "
            "counsel seventeen times and made prejudicial comments about "
            "the defendant's character."
        ),
        "lane": "E",
        "case_number": "2024-001507-DC",
        "page_number": 1,
    },
    {
        "file_path": "/evidence/financial_records.pdf",
        "text": (
            "Bank statements from two thousand twenty three show regular "
            "deposits consistent with employment income and child support "
            "payments made on the first of each month without exception."
        ),
        "lane": "A",
        "case_number": "2024-001507-DC",
        "page_number": 5,
    },
]


@pytest.fixture()
def engine() -> SemanticSearchEngine:
    """Pre-loaded engine with test documents."""
    eng = SemanticSearchEngine(force_tfidf=True, chunk_size=100, chunk_overlap=20)
    eng.bulk_ingest(DOCS)
    return eng


@pytest.fixture()
def empty_engine() -> SemanticSearchEngine:
    return SemanticSearchEngine(force_tfidf=True)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSemanticSearchEngine:
    """Integration tests for the search engine."""

    def test_search_returns_results(self, engine: SemanticSearchEngine) -> None:
        results = engine.search("custody evaluation report")
        assert len(results) > 0
        assert all("score" in r for r in results)
        assert all("chunk_text" in r for r in results)

    def test_search_relevance(self, engine: SemanticSearchEngine) -> None:
        # Use lower threshold for TF-IDF on small corpus
        results = engine.search("mould maintenance complaints", min_score=0.01)
        assert len(results) > 0
        # At least one result should relate to housing / mould
        texts = " ".join(r["chunk_text"].lower() for r in results)
        assert any(
            kw in texts for kw in ("mould", "housing", "shady", "maintenance", "complaints")
        )

    def test_lane_filtering(self, engine: SemanticSearchEngine) -> None:
        results = engine.search("evidence", lane="B")
        for r in results:
            assert r["lane"] == "B", f"Expected lane B, got {r['lane']}"

    def test_lane_filter_excludes_other_lanes(self, engine: SemanticSearchEngine) -> None:
        results_all = engine.search("evidence", top_k=20)
        results_e = engine.search("evidence", lane="E", top_k=20)
        assert len(results_e) <= len(results_all)

    def test_min_score_filtering(self, engine: SemanticSearchEngine) -> None:
        results_low = engine.search("evidence", min_score=0.0, top_k=50)
        results_high = engine.search("evidence", min_score=0.9, top_k=50)
        assert len(results_high) <= len(results_low)

    def test_empty_index_returns_empty(self, empty_engine: SemanticSearchEngine) -> None:
        results = empty_engine.search("anything")
        assert results == []

    def test_ingest_document(self, empty_engine: SemanticSearchEngine) -> None:
        count = empty_engine.ingest_document(
            "test.txt",
            "This is a test document about custody and child welfare.",
            {"lane": "A"},
        )
        assert count > 0
        results = empty_engine.search("custody")
        assert len(results) > 0

    def test_get_stats(self, engine: SemanticSearchEngine) -> None:
        stats = engine.get_stats()
        assert stats["index_size"] > 0
        assert stats["embedder_backend"] == "tfidf"
        assert "chunk_count" in stats

    def test_top_k_limits_results(self, engine: SemanticSearchEngine) -> None:
        results = engine.search("evidence", top_k=2)
        assert len(results) <= 2

    def test_bulk_ingest_returns_count(self) -> None:
        eng = SemanticSearchEngine(force_tfidf=True, chunk_size=50, chunk_overlap=10)
        count = eng.bulk_ingest(DOCS)
        assert count > 0

    def test_results_contain_metadata(self, engine: SemanticSearchEngine) -> None:
        results = engine.search("custody")
        for r in results:
            assert "file_path" in r
            assert "score" in r
            assert isinstance(r["score"], float)
