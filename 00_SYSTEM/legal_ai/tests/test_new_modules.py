"""
Comprehensive unit tests for 6 LitigationOS legal_ai modules:
  1. OpinionParser       (opinion_parser.py)
  2. BrainEvolver        (brain_evolver.py)
  3. CrossBrainOptimizer (cross_brain_optimizer.py)
  4. LegalRAGEngine      (rag_engine.py)
  5. LegalReranker       (reranker.py)
  6. RAGEvaluator        (rag_evaluation.py)

All tests are pure unit tests — no DB connections or external dependencies.
Run with:
    cd C:\\Users\\andre\\LitigationOS\\00_SYSTEM\\legal_ai
    python -m pytest tests/test_new_modules.py -v
"""

from __future__ import annotations

import math
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# ---------------------------------------------------------------------------
# Ensure legal_ai package is importable
# ---------------------------------------------------------------------------
_LEGAL_AI_DIR = Path(__file__).resolve().parent.parent
if str(_LEGAL_AI_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_LEGAL_AI_DIR.parent))

# Persistently patch BrainManager so lazy imports never load heavy DB code.
# This stays in sys.modules for the whole test session (constructors also
# use lazy imports, so a context-manager patch is not sufficient).
_mock_brains = MagicMock()
sys.modules["brains"] = _mock_brains
sys.modules["brains.brain_manager"] = _mock_brains.brain_manager

# Pre-mock heavy ML libraries to prevent slow imports (torch/CUDA init).
# sentence_transformers is an empty package shell — `from sentence_transformers
# import CrossEncoder` raises ImportError, which is the graceful-degradation
# path that reranker.py already handles.
# Force-set (not setdefault) so mocks always win, even if the real package
# is installed and was somehow imported by a pytest plugin.
import types as _types
_fake_st = _types.ModuleType("sentence_transformers")
_fake_st.__path__ = []
sys.modules["sentence_transformers"] = _fake_st
# Also block torch if someone tries to import it transitively
_fake_torch = _types.ModuleType("torch")
_fake_torch.__path__ = []
sys.modules["torch"] = _fake_torch

if True:  # block keeps the original indentation for the imports
    from legal_ai.opinion_parser import (
        OpinionParser,
        ParsedOpinion,
        OrderSection,
        ProceduralDefect,
        DEFECT_PATTERNS,
    )
    from legal_ai.brain_evolver import (
        BrainEvolver,
        BrainHealthScore,
        DuplicateGroup,
        EvolutionAction,
        EvolutionReport,
        BRAIN_NAMES,
        _tokenize as be_tokenize,
        _jaccard,
    )
    from legal_ai.cross_brain_optimizer import (
        CrossBrainOptimizer,
        QueryPlan,
        CrossBrainResult,
        CrossBrainSearchResult,
        QUERY_BRAIN_MAP,
        QUERY_CLASSIFIERS,
        BRAIN_FTS_TABLES,
    )
    from legal_ai.rag_engine import (
        LegalRAGEngine,
        RetrievedEvidence,
        GroundedClaim,
        RAGResponse,
        EVIDENCE_WEIGHTS,
        EVIDENCE_STRENGTH_MAP,
        LANE_PATTERNS,
        LEGAL_THESAURUS,
    )
    from legal_ai.reranker import (
        LegalReranker,
        RerankResult,
        RerankReport,
        STRENGTH_BONUS,
        LANE_RELEVANCE_BONUS,
    )
    from legal_ai.rag_evaluation import (
        RAGEvaluator,
        TestCase,
        EvalMetrics,
        EvalReport,
        PASS_THRESHOLDS,
    )


# ===========================================================================
# 1. OpinionParser Tests
# ===========================================================================


class TestOpinionParser:
    """Tests for legal_ai.opinion_parser.OpinionParser."""

    @pytest.fixture
    def parser(self) -> OpinionParser:
        return OpinionParser(
            brain_manager=None,
            use_citation_extractor=False,
            use_entity_extractor=False,
        )

    # -- Happy paths --------------------------------------------------------

    def test_parse_empty_text_returns_warning(self, parser: OpinionParser):
        result = parser.parse("")
        assert isinstance(result, ParsedOpinion)
        assert any("empty" in w.lower() for w in result.warnings)

    def test_parse_basic_order_returns_sections(self, parser: OpinionParser):
        text = (
            "STATE OF MICHIGAN\n"
            "IN THE CIRCUIT COURT\n\n"
            "FINDINGS OF FACT\n"
            "The Court finds that the respondent failed to appear.\n\n"
            "CONCLUSIONS OF LAW\n"
            "MCR 2.003 governs judicial disqualification.\n\n"
            "IT IS HEREBY ORDERED that the motion is granted."
        )
        result = parser.parse(text)
        assert isinstance(result, ParsedOpinion)
        assert len(result.sections) >= 3
        section_types = {s.section_type for s in result.sections}
        assert "caption" in section_types or "finding_of_fact" in section_types

    def test_classify_order_type_ex_parte(self, parser: OpinionParser):
        text = "This ex parte order is entered without notice to the opposing party."
        assert parser.classify_order_type(text) == "ex_parte"

    def test_classify_order_type_stipulated(self, parser: OpinionParser):
        text = "Based on the stipulation of the parties, it is ordered that..."
        assert parser.classify_order_type(text) == "stipulated"

    def test_classify_order_type_default_is_contested(self, parser: OpinionParser):
        text = "This is a plain court order with no special indicators."
        assert parser.classify_order_type(text) == "contested"

    def test_classify_order_type_emergency(self, parser: OpinionParser):
        text = "Emergency temporary restraining order is issued."
        assert parser.classify_order_type(text) == "emergency"

    def test_detect_defects_ex_parte(self, parser: OpinionParser):
        text = "This order was entered ex parte without notice to the respondent."
        defects = parser.detect_defects(text)
        assert len(defects) >= 1
        assert defects[0].defect_type == "ex_parte"
        assert defects[0].severity == "critical"
        assert defects[0].confidence > 0.5

    def test_detect_defects_missing_notice(self, parser: OpinionParser):
        text = "No proof of service was filed in this matter."
        defects = parser.detect_defects(text)
        types = [d.defect_type for d in defects]
        assert "missing_notice" in types

    def test_detect_defects_missing_findings_custody(self, parser: OpinionParser):
        text = "The court modifies custody and parenting time without any specific analysis."
        defects = parser.detect_defects(text)
        types = [d.defect_type for d in defects]
        assert "missing_findings" in types

    def test_detect_defects_no_defects_clean_order(self, parser: OpinionParser):
        text = "After hearing with all parties present, the Court orders that the motion is granted."
        defects = parser.detect_defects(text)
        assert len(defects) == 0

    def test_parse_extracts_date(self, parser: OpinionParser):
        text = "Dated: January 15, 2025\nIT IS HEREBY ORDERED that the motion is granted."
        result = parser.parse(text)
        assert "January 15, 2025" in result.order_date

    def test_parse_extracts_judge(self, parser: OpinionParser):
        text = "Honorable Judge McNeill presiding.\nIT IS HEREBY ORDERED that..."
        result = parser.parse(text)
        assert "McNeill" in result.judge

    def test_parse_extracts_case_number(self, parser: OpinionParser):
        text = "Case No. 2024-001507-DC\nIT IS HEREBY ORDERED that..."
        result = parser.parse(text)
        assert "001507" in result.case_number

    def test_parse_sets_is_ex_parte_flag(self, parser: OpinionParser):
        text = "This ex parte order entered without hearing."
        result = parser.parse(text)
        assert result.is_ex_parte is True

    def test_parse_detects_best_interest(self, parser: OpinionParser):
        text = "The Court considers the best interest of the children under MCL 722.23."
        result = parser.parse(text)
        assert result.has_best_interest_analysis is True

    def test_parse_batch(self, parser: OpinionParser):
        texts = [
            "IT IS HEREBY ORDERED that motion granted.",
            "Ex parte order without notice.",
            "",
        ]
        results = parser.parse_batch(texts)
        assert len(results) == 3
        assert all(isinstance(r, ParsedOpinion) for r in results)

    def test_get_stats(self, parser: OpinionParser):
        parser.parse("IT IS HEREBY ORDERED that the motion is granted.")
        stats = parser.get_stats()
        assert stats["orders_parsed"] >= 1
        assert stats["version"] == "1.0.0"
        assert "defect_patterns" in stats

    def test_parse_time_is_recorded(self, parser: OpinionParser):
        result = parser.parse("IT IS HEREBY ORDERED that motion granted.")
        assert result.parse_time_ms >= 0.0

    # -- Edge / error cases -------------------------------------------------

    def test_parse_whitespace_only_returns_warning(self, parser: OpinionParser):
        result = parser.parse("   \n\t  ")
        assert any("empty" in w.lower() for w in result.warnings)

    def test_detect_defects_missing_signature(self, parser: OpinionParser):
        text = "This order is unsigned and has no judicial signature."
        defects = parser.detect_defects(text)
        types = [d.defect_type for d in defects]
        assert "missing_signature" in types

    def test_ex_parte_suppressed_when_parties_present(self, parser: OpinionParser):
        text = "Ex parte filing noted, but after hearing with parties present."
        order_type = parser.classify_order_type(text)
        assert order_type == "contested"


# ===========================================================================
# 2. BrainEvolver Tests
# ===========================================================================


class TestBrainEvolver:
    """Tests for legal_ai.brain_evolver.BrainEvolver."""

    @pytest.fixture
    def evolver(self, tmp_path: Path) -> BrainEvolver:
        """Create a BrainEvolver with a temp brain directory."""
        brain_dir = tmp_path / "brains"
        brain_dir.mkdir()
        # Create a cross_brain_index.db with evolution log
        db_path = brain_dir / "cross_brain_index.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS brain_evolution_log ("
            "log_id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "cycle_id TEXT, action_type TEXT, brain_name TEXT,"
            "table_name TEXT, description TEXT, records_affected INTEGER,"
            "status TEXT, rollback_sql TEXT, executed_at TEXT)"
        )
        conn.commit()
        conn.close()
        # Pass a MagicMock brain_manager to skip lazy BrainManager import,
        # then set to None so tests exercise the no-brain-manager paths.
        ev = BrainEvolver.__new__(BrainEvolver)
        ev._brain_manager = None
        ev._auto_execute = False
        ev._brain_dir = brain_dir
        ev._evolution_count = 0
        ev._total_actions = 0
        return ev

    def _create_brain_db(self, brain_dir: Path, brain_name: str, tables: dict):
        """Helper to create a brain DB with tables and data."""
        db_path = brain_dir / f"{brain_name}.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA journal_mode = WAL")
        for table_name, rows in tables.items():
            if rows:
                cols = list(rows[0].keys())
                col_defs = ", ".join(f"{c} TEXT" for c in cols)
                conn.execute(f"CREATE TABLE IF NOT EXISTS [{table_name}] ({col_defs})")
                for row in rows:
                    placeholders = ", ".join("?" * len(cols))
                    conn.execute(
                        f"INSERT INTO [{table_name}] ({', '.join(cols)}) VALUES ({placeholders})",
                        tuple(row.values()),
                    )
            else:
                conn.execute(f"CREATE TABLE IF NOT EXISTS [{table_name}] (id TEXT, content TEXT)")
        conn.commit()
        conn.close()

    # -- Happy paths --------------------------------------------------------

    def test_assess_health_missing_brain(self, evolver: BrainEvolver):
        scores = evolver.assess_health("nonexistent_brain")
        assert len(scores) == 1
        assert scores[0].health_score == 0.0
        assert any("not found" in i for i in scores[0].issues)

    def test_assess_health_existing_brain(self, evolver: BrainEvolver):
        self._create_brain_db(
            evolver._brain_dir, "authority_brain",
            {"rules": [{"id": "1", "content": "MCR 2.003"}]}
        )
        scores = evolver.assess_health("authority_brain")
        assert len(scores) == 1
        assert scores[0].brain_name == "authority_brain"
        assert scores[0].total_rows >= 1
        assert scores[0].health_score > 0.0

    def test_find_duplicates_empty_table(self, evolver: BrainEvolver):
        self._create_brain_db(
            evolver._brain_dir, "test_brain", {"data": []}
        )
        dupes = evolver.find_duplicates("test_brain", "data", "content")
        assert dupes == []

    def test_find_duplicates_detects_similar_records(self, evolver: BrainEvolver):
        self._create_brain_db(
            evolver._brain_dir, "test_brain",
            {"data": [
                {"id": "1", "content": "MCR 2.003 governs judicial disqualification for bias"},
                {"id": "2", "content": "MCR 2.003 governs judicial disqualification for bias and prejudice"},
                {"id": "3", "content": "Something completely different about eviction law"},
            ]}
        )
        dupes = evolver.find_duplicates("test_brain", "data", "content", threshold=0.6)
        assert len(dupes) >= 1
        assert "1" in dupes[0].record_ids or "2" in dupes[0].record_ids

    def test_find_duplicates_nonexistent_brain(self, evolver: BrainEvolver):
        result = evolver.find_duplicates("no_brain", "data", "content")
        assert result == []

    def test_merge_duplicates_proposed_not_executed(self, evolver: BrainEvolver):
        group = DuplicateGroup(
            brain_name="test",
            table_name="data",
            record_ids=["1", "2", "3"],
            similarity_score=0.92,
        )
        action = evolver.merge_duplicates(group)
        assert action.status == "proposed"
        assert action.action_type == "dedup"

    def test_check_fts_sync_no_brain(self, evolver: BrainEvolver):
        result = evolver.check_fts_sync("nonexistent_brain")
        assert result == {}

    def test_rebuild_fts_proposed(self, evolver: BrainEvolver):
        action = evolver.rebuild_fts("authority_brain", "court_rules_fts")
        assert action.status == "proposed"
        assert action.action_type == "fts_rebuild"

    def test_evolve_dry_run(self, evolver: BrainEvolver):
        report = evolver.evolve(dry_run=True)
        assert isinstance(report, EvolutionReport)
        assert report.cycle_id.startswith("evo_")
        assert report.started_at != ""

    def test_get_stats(self, evolver: BrainEvolver):
        stats = evolver.get_stats()
        assert stats["version"] == "1.0.0"
        assert "known_brains" in stats
        assert "auto_execute" in stats
        assert stats["auto_execute"] is False

    def test_get_evolution_history(self, evolver: BrainEvolver):
        history = evolver.get_evolution_history(limit=10)
        assert isinstance(history, list)

    # -- Edge / error cases -------------------------------------------------

    def test_tokenize_helper(self):
        tokens = be_tokenize("Hello World hello")
        assert "hello" in tokens
        assert "world" in tokens
        assert len(tokens) == 2  # deduped + lowered

    def test_jaccard_identical(self):
        assert _jaccard({"a", "b", "c"}, {"a", "b", "c"}) == 1.0

    def test_jaccard_disjoint(self):
        assert _jaccard({"a", "b"}, {"c", "d"}) == 0.0

    def test_jaccard_both_empty(self):
        assert _jaccard(set(), set()) == 1.0

    def test_jaccard_partial_overlap(self):
        sim = _jaccard({"a", "b", "c"}, {"b", "c", "d"})
        assert abs(sim - 0.5) < 0.01  # 2 common / 4 union

    def test_brain_exists_false(self, evolver: BrainEvolver):
        assert evolver._brain_exists("nonexistent_brain") is False

    def test_brain_exists_true(self, evolver: BrainEvolver):
        self._create_brain_db(evolver._brain_dir, "test_brain", {"t": []})
        assert evolver._brain_exists("test_brain") is True


# ===========================================================================
# 3. CrossBrainOptimizer Tests
# ===========================================================================


class TestCrossBrainOptimizer:
    """Tests for legal_ai.cross_brain_optimizer.CrossBrainOptimizer."""

    @pytest.fixture
    def optimizer(self) -> CrossBrainOptimizer:
        # Bypass __init__ lazy BrainManager loading via __new__
        opt = CrossBrainOptimizer.__new__(CrossBrainOptimizer)
        opt._bm = None
        opt._cache_size = 10
        opt._cache_ttl = 60
        from collections import OrderedDict
        opt._cache = OrderedDict()
        opt._latencies = []
        opt._brain_latencies = {}
        opt._table_latencies = {}
        opt._total_queries = 0
        opt._cache_hits = 0
        return opt

    # -- Query planning -----------------------------------------------------

    def test_plan_query_legal_authority(self, optimizer: CrossBrainOptimizer):
        plan = optimizer.plan_query("MCR 2.003 disqualification")
        assert isinstance(plan, QueryPlan)
        assert plan.query_type == "legal_authority"
        assert "authority_brain" in plan.target_brains

    def test_plan_query_factual_narrative(self, optimizer: CrossBrainOptimizer):
        plan = optimizer.plan_query("What happened at the hearing on June 15?")
        assert plan.query_type == "factual_narrative"
        assert "narrative_brain" in plan.target_brains

    def test_plan_query_entity_lookup(self, optimizer: CrossBrainOptimizer):
        plan = optimizer.plan_query("Who is Judge McNeill?")
        assert plan.query_type == "entity_lookup"
        assert "entity_brain" in plan.target_brains

    def test_plan_query_claim_analysis(self, optimizer: CrossBrainOptimizer):
        plan = optimizer.plan_query("What are the elements of the damages claim?")
        assert plan.query_type == "claim_analysis"
        assert "claims_brain" in plan.target_brains

    def test_plan_query_strategic(self, optimizer: CrossBrainOptimizer):
        plan = optimizer.plan_query("What is the strength of the argument?")
        assert plan.query_type == "strategic"

    def test_plan_query_universal_fallback(self, optimizer: CrossBrainOptimizer):
        plan = optimizer.plan_query("something very generic")
        assert plan.query_type == "universal"
        assert len(plan.target_brains) == len(QUERY_BRAIN_MAP["universal"])

    def test_plan_query_with_hint_brains(self, optimizer: CrossBrainOptimizer):
        plan = optimizer.plan_query("MCR 2.003", hint_brains=["authority_brain"])
        assert plan.target_brains == ["authority_brain"]

    def test_plan_query_has_fts_queries(self, optimizer: CrossBrainOptimizer):
        plan = optimizer.plan_query("MCR 2.003 judicial disqualification")
        assert len(plan.fts_queries) > 0
        assert plan.estimated_cost_ms > 0.0

    # -- Search (no brain manager) ------------------------------------------

    def test_search_without_brain_manager(self, optimizer: CrossBrainOptimizer):
        result = optimizer.search("MCR 2.003")
        assert isinstance(result, CrossBrainSearchResult)
        assert any("unavailable" in w.lower() for w in result.warnings)
        assert result.results == []

    def test_search_brain_without_brain_manager(self, optimizer: CrossBrainOptimizer):
        results = optimizer.search_brain("authority_brain", "MCR 2.003")
        assert results == []

    # -- Cache management ---------------------------------------------------

    def test_invalidate_cache_all(self, optimizer: CrossBrainOptimizer):
        # Force a cache entry by manually inserting
        from legal_ai.cross_brain_optimizer import _CacheEntry
        key = ("test", frozenset())
        optimizer._cache[key] = _CacheEntry(
            result=CrossBrainSearchResult(), timestamp=time.time()
        )
        assert len(optimizer._cache) == 1
        removed = optimizer.invalidate_cache()
        assert removed == 1
        assert len(optimizer._cache) == 0

    def test_invalidate_cache_by_brain(self, optimizer: CrossBrainOptimizer):
        from legal_ai.cross_brain_optimizer import _CacheEntry
        result_a = CrossBrainSearchResult(brains_searched=["authority_brain"])
        result_b = CrossBrainSearchResult(brains_searched=["narrative_brain"])
        optimizer._cache[("a", frozenset())] = _CacheEntry(result=result_a, timestamp=time.time())
        optimizer._cache[("b", frozenset())] = _CacheEntry(result=result_b, timestamp=time.time())
        removed = optimizer.invalidate_cache("authority_brain")
        assert removed == 1
        assert len(optimizer._cache) == 1

    # -- Latency report -----------------------------------------------------

    def test_get_latency_report_empty(self, optimizer: CrossBrainOptimizer):
        report = optimizer.get_latency_report()
        assert report.total_queries == 0
        assert report.avg_latency_ms == 0.0

    def test_get_latency_report_with_data(self, optimizer: CrossBrainOptimizer):
        optimizer._latencies = [10.0, 20.0, 30.0]
        optimizer._total_queries = 3
        optimizer._cache_hits = 1
        report = optimizer.get_latency_report()
        assert report.total_queries == 3
        assert report.avg_latency_ms == 20.0
        assert report.cache_hit_rate > 0.0

    # -- Stats and FTS term building ----------------------------------------

    def test_get_stats(self, optimizer: CrossBrainOptimizer):
        stats = optimizer.get_stats()
        assert stats["version"] == "1.0.0"
        assert "known_brains" in stats
        assert "total_fts_tables" in stats

    def test_build_fts_term_multi_word(self, optimizer: CrossBrainOptimizer):
        fts = optimizer._build_fts_term("MCR 2.003 disqualification")
        assert "OR" in fts

    def test_build_fts_term_single_word(self, optimizer: CrossBrainOptimizer):
        fts = optimizer._build_fts_term("disqualification")
        assert fts == "disqualification"

    def test_classify_query_types(self, optimizer: CrossBrainOptimizer):
        assert optimizer._classify_query("MCR 2.003") == "legal_authority"
        assert optimizer._classify_query("who is the judge") == "entity_lookup"
        assert optimizer._classify_query("claim for damages breach") == "claim_analysis"


# ===========================================================================
# 4. LegalRAGEngine Tests
# ===========================================================================


class TestLegalRAGEngine:
    """Tests for legal_ai.rag_engine.LegalRAGEngine."""

    @pytest.fixture
    def rag(self) -> LegalRAGEngine:
        # Bypass __init__ lazy BrainManager / CrossBrainOptimizer loading
        engine = LegalRAGEngine.__new__(LegalRAGEngine)
        engine._bm = None
        engine._optimizer = None
        engine._max_corrections = 2
        engine._min_confidence = 0.4
        engine._total_queries = 0
        engine._total_retrievals = 0
        engine._total_corrections = 0
        engine._total_grounding_sum = 0.0
        return engine

    # -- Lane detection -----------------------------------------------------

    def test_detect_lane_custody(self, rag: LegalRAGEngine):
        assert rag.detect_lane("custody and parenting time") == "A"

    def test_detect_lane_housing(self, rag: LegalRAGEngine):
        assert rag.detect_lane("eviction from mobile home park") == "B"

    def test_detect_lane_ppo(self, rag: LegalRAGEngine):
        assert rag.detect_lane("PPO protection order stalking") == "D"

    def test_detect_lane_misconduct(self, rag: LegalRAGEngine):
        assert rag.detect_lane("judicial misconduct disqualification bias") == "E"

    def test_detect_lane_appellate(self, rag: LegalRAGEngine):
        assert rag.detect_lane("COA appellate brief standard of review") == "F"

    def test_detect_lane_convergence(self, rag: LegalRAGEngine):
        assert rag.detect_lane("convergence cross-lane pattern") == "C"

    def test_detect_lane_unknown(self, rag: LegalRAGEngine):
        assert rag.detect_lane("generic question") == ""

    def test_detect_lane_priority_e_over_a(self, rag: LegalRAGEngine):
        # E (misconduct) should win over A (custody) due to priority
        assert rag.detect_lane("judicial misconduct in custody case") == "E"

    # -- Evidence weighting -------------------------------------------------

    def test_weight_by_evidence_strength(self, rag: LegalRAGEngine):
        evidence = [
            RetrievedEvidence(text="strong fact", source="s1", score=1.0, evidence_strength="RECORD_FACT"),
            RetrievedEvidence(text="weak claim", source="s2", score=1.0, evidence_strength="ALLEGATION"),
        ]
        weighted = rag.weight_by_evidence_strength(evidence)
        assert weighted[0].score > weighted[1].score

    # -- Generation (extractive) --------------------------------------------

    def test_generate_no_evidence(self, rag: LegalRAGEngine):
        answer = rag.generate("test query", [])
        assert "no evidence" in answer.lower()

    def test_generate_with_evidence(self, rag: LegalRAGEngine):
        evidence = [
            RetrievedEvidence(
                text="MCR 2.003 governs judicial disqualification in Michigan courts. It requires a motion showing bias.",
                source="mcr_rules",
                score=0.9,
            ),
            RetrievedEvidence(
                text="The standard for disqualification is actual bias or appearance of impropriety.",
                source="case_law",
                score=0.7,
            ),
        ]
        answer = rag.generate("What MCR governs disqualification?", evidence)
        assert len(answer) > 0
        assert "Per" in answer  # Source attribution format

    # -- Grounding verification ---------------------------------------------

    def test_verify_grounding_empty(self, rag: LegalRAGEngine):
        conf, claims = rag.verify_grounding("", [])
        assert conf == 0.0
        assert claims == []

    def test_verify_grounding_grounded(self, rag: LegalRAGEngine):
        evidence = [
            RetrievedEvidence(
                text="MCR 2.003 governs judicial disqualification for bias and prejudice in Michigan courts.",
                source="rules",
            ),
        ]
        answer = "MCR 2.003 governs judicial disqualification for bias in Michigan courts."
        conf, claims = rag.verify_grounding(answer, evidence)
        assert conf > 0.0
        assert len(claims) >= 1

    def test_verify_grounding_ungrounded(self, rag: LegalRAGEngine):
        evidence = [
            RetrievedEvidence(text="The sky is blue.", source="weather"),
        ]
        answer = "MCR 2.003 governs judicial disqualification for bias."
        conf, claims = rag.verify_grounding(answer, evidence)
        # Most tokens won't overlap, so grounding should be low
        for claim in claims:
            assert claim.confidence < 0.5

    # -- Query pipeline (no external deps) ----------------------------------

    def test_query_returns_empty_when_no_evidence(self, rag: LegalRAGEngine):
        response = rag.query("MCR 2.003 disqualification")
        assert isinstance(response, RAGResponse)
        assert response.retrieval_count == 0
        assert "no" in response.answer.lower() or "no evidence" in response.answer.lower()

    # -- Expand query -------------------------------------------------------

    def test_expand_query_with_thesaurus(self, rag: LegalRAGEngine):
        expanded = rag._expand_query("custody abuse bias")
        assert len(expanded) > len("custody abuse bias")
        # Should add synonyms
        assert "parenting" in expanded.lower() or "domestic violence" in expanded.lower()

    def test_expand_query_no_expansion(self, rag: LegalRAGEngine):
        original = "xyznotaword"
        expanded = rag._expand_query(original)
        assert expanded == original

    # -- Stats and utility --------------------------------------------------

    def test_get_stats(self, rag: LegalRAGEngine):
        stats = rag.get_stats()
        assert stats["version"] == "1.0.0"
        assert "max_corrections" in stats
        assert stats["brain_manager_available"] is False

    def test_infer_strength(self, rag: LegalRAGEngine):
        assert rag._infer_strength("court_rules_fts") == "strong"
        assert rag._infer_strength("orders_fts") == "moderate"
        assert rag._infer_strength("drafts_fts") == "weak"
        assert rag._infer_strength("unknown_table") == "unknown"

    def test_extract_citations(self, rag: LegalRAGEngine):
        text = "Under MCR 2.003(C)(1) and MCL 722.23, the court must..."
        cites = rag._extract_citations(text)
        assert len(cites) >= 1
        assert any("MCR" in c for c in cites)


# ===========================================================================
# 5. LegalReranker Tests
# ===========================================================================


class TestLegalReranker:
    """Tests for legal_ai.reranker.LegalReranker."""

    @pytest.fixture
    def reranker(self) -> LegalReranker:
        # No ML models — passthrough mode
        return LegalReranker(use_cross_encoder=False)

    # -- Rerank (passthrough mode) ------------------------------------------

    def test_rerank_empty_candidates(self, reranker: LegalReranker):
        results, report = reranker.rerank("test", [])
        assert results == []
        assert report.method == "passthrough"
        assert report.candidates_in == 0

    def test_rerank_passthrough_returns_sorted(self, reranker: LegalReranker):
        candidates = [
            {"text": "low", "score": 0.3},
            {"text": "high", "score": 0.9},
            {"text": "mid", "score": 0.6},
        ]
        results, report = reranker.rerank("test", candidates, top_k=3)
        assert len(results) == 3
        assert results[0].combined_score >= results[1].combined_score
        assert results[1].combined_score >= results[2].combined_score

    def test_rerank_top_k_limits_output(self, reranker: LegalReranker):
        candidates = [{"text": f"doc{i}", "score": i * 0.1} for i in range(20)]
        results, report = reranker.rerank("test", candidates, top_k=5)
        assert len(results) == 5
        assert report.candidates_in == 20
        assert report.results_out == 5

    def test_rerank_evidence_strength_bonus(self, reranker: LegalReranker):
        candidates = [
            {"text": "strong evidence", "score": 0.5, "evidence_strength": "strong"},
            {"text": "weak evidence", "score": 0.5, "evidence_strength": "weak"},
        ]
        results, _ = reranker.rerank("test", candidates, top_k=2)
        strong = [r for r in results if "strong" in r.text][0]
        weak = [r for r in results if "weak" in r.text][0]
        assert strong.combined_score > weak.combined_score

    def test_rerank_lane_relevance_bonus(self, reranker: LegalReranker):
        candidates = [
            {"text": "lane A doc", "score": 0.5, "lane": "A"},
            {"text": "lane B doc", "score": 0.5, "lane": "B"},
        ]
        results, _ = reranker.rerank("test", candidates, top_k=2, lane="A")
        lane_a = [r for r in results if "lane A" in r.text][0]
        lane_b = [r for r in results if "lane B" in r.text][0]
        assert lane_a.combined_score > lane_b.combined_score

    def test_rerank_report_has_timing(self, reranker: LegalReranker):
        candidates = [{"text": "doc", "score": 0.5}]
        _, report = reranker.rerank("test", candidates)
        assert report.time_ms >= 0.0
        assert report.query == "test"

    def test_rerank_assigns_ranks(self, reranker: LegalReranker):
        candidates = [
            {"text": "a", "score": 0.1},
            {"text": "b", "score": 0.9},
        ]
        results, _ = reranker.rerank("test", candidates, top_k=2)
        assert results[0].rank == 1
        assert results[1].rank == 2

    # -- MMR (fallback mode — no numpy or embedder) -------------------------

    def test_mmr_fallback_no_numpy(self, reranker: LegalReranker):
        candidates = [
            {"text": "doc1", "score": 0.9},
            {"text": "doc2", "score": 0.3},
        ]
        results, report = reranker.mmr_select("test", candidates, top_k=2)
        assert len(results) <= 2
        # Falls back to score passthrough or rerank

    # -- Stats --------------------------------------------------------------

    def test_get_stats(self, reranker: LegalReranker):
        reranker.rerank("test", [{"text": "doc", "score": 0.5}])
        stats = reranker.get_stats()
        assert stats["method"] == "passthrough"
        assert stats["total_reranks"] >= 1
        assert stats["total_time_ms"] >= 0.0

    # -- Sigmoid ------------------------------------------------------------

    def test_sigmoid_normal(self):
        val = LegalReranker._sigmoid(0.0)
        assert abs(val - 0.5) < 0.01

    def test_sigmoid_large_positive(self):
        val = LegalReranker._sigmoid(100.0)
        assert val > 0.99

    def test_sigmoid_large_negative(self):
        val = LegalReranker._sigmoid(-100.0)
        assert val < 0.01

    # -- Position changes ---------------------------------------------------

    def test_count_position_changes(self, reranker: LegalReranker):
        original = [{"text": "first"}, {"text": "second"}, {"text": "third"}]
        reranked = [
            RerankResult(text="third", rank=1),
            RerankResult(text="first", rank=2),
            RerankResult(text="second", rank=3),
        ]
        changes = reranker._count_position_changes(original, reranked)
        assert changes >= 2


# ===========================================================================
# 6. RAGEvaluator Tests
# ===========================================================================


class TestRAGEvaluator:
    """Tests for legal_ai.rag_evaluation.RAGEvaluator."""

    @pytest.fixture
    def evaluator(self) -> RAGEvaluator:
        return RAGEvaluator()

    # -- Single evaluation --------------------------------------------------

    def test_evaluate_single_basic(self, evaluator: RAGEvaluator):
        metrics = evaluator.evaluate_single(
            query="What MCR governs disqualification?",
            answer="MCR 2.003 governs judicial disqualification in Michigan.",
            retrieved=[
                {"text": "MCR 2.003 governs disqualification of judges.", "source": "mcr_rules"},
            ],
        )
        assert isinstance(metrics, EvalMetrics)
        assert metrics.faithfulness > 0.0
        assert metrics.time_ms >= 0.0

    def test_evaluate_single_with_expected_answer(self, evaluator: RAGEvaluator):
        metrics = evaluator.evaluate_single(
            query="What MCR governs disqualification?",
            answer="MCR 2.003 governs judicial disqualification.",
            retrieved=[{"text": "MCR 2.003...", "source": "rules"}],
            expected_answer="MCR 2.003 governs disqualification of judges.",
        )
        assert metrics.answer_coverage > 0.0

    def test_evaluate_single_retrieval_precision_recall(self, evaluator: RAGEvaluator):
        metrics = evaluator.evaluate_single(
            query="test",
            answer="answer",
            retrieved=[
                {"text": "doc1", "source": "a"},
                {"text": "doc2", "source": "b"},
                {"text": "doc3", "source": "c"},
            ],
            relevant_doc_ids=["a", "b", "d"],
        )
        assert metrics.retrieval_precision > 0.0
        assert metrics.retrieval_recall > 0.0
        assert metrics.retrieval_f1 > 0.0

    def test_evaluate_single_citation_accuracy(self, evaluator: RAGEvaluator):
        metrics = evaluator.evaluate_single(
            query="test",
            answer="Under MCR 2.003, the court must disqualify.",
            retrieved=[{"text": "MCR 2.003 text", "source": "rules"}],
            expected_citations=["MCR 2.003"],
        )
        assert metrics.citation_accuracy > 0.0
        assert metrics.legal_citation_count >= 1

    def test_evaluate_single_lane_accuracy(self, evaluator: RAGEvaluator):
        metrics = evaluator.evaluate_single(
            query="test",
            answer="answer",
            retrieved=[
                {"text": "doc", "source": "s1", "lane": "E"},
            ],
            expected_lane="E",
        )
        assert metrics.lane_accuracy == 1.0

    def test_evaluate_single_lane_mismatch(self, evaluator: RAGEvaluator):
        metrics = evaluator.evaluate_single(
            query="test",
            answer="answer",
            retrieved=[
                {"text": "doc", "source": "s1", "lane": "A"},
            ],
            expected_lane="E",
        )
        assert metrics.lane_accuracy == 0.0

    def test_evaluate_single_empty_answer(self, evaluator: RAGEvaluator):
        metrics = evaluator.evaluate_single(
            query="test", answer="", retrieved=[],
        )
        assert metrics.faithfulness == 0.0
        assert metrics.answer_coverage == 0.0

    # -- Suite evaluation ---------------------------------------------------

    def test_evaluate_suite(self, evaluator: RAGEvaluator):
        test_cases = [
            TestCase(
                query="What MCR governs disqualification?",
                expected_answer="MCR 2.003",
                expected_citations=["MCR 2.003"],
            ),
            TestCase(
                query="Best interest factors?",
                expected_answer="MCL 722.23",
            ),
        ]

        def mock_rag(query: str) -> dict:
            return {
                "answer": f"The answer involves {query}",
                "retrieved": [{"text": query, "source": "test"}],
            }

        report = evaluator.evaluate_suite(test_cases, mock_rag)
        assert isinstance(report, EvalReport)
        assert report.total_cases == 2
        assert report.passed + report.failed == 2
        assert len(report.per_case_results) == 2

    def test_evaluate_suite_handles_exception(self, evaluator: RAGEvaluator):
        test_cases = [TestCase(query="test")]

        def failing_rag(query: str) -> dict:
            raise RuntimeError("RAG failed")

        report = evaluator.evaluate_suite(test_cases, failing_rag)
        assert report.failed == 1

    # -- Recommendations ----------------------------------------------------

    def test_recommendations_low_faithfulness(self, evaluator: RAGEvaluator):
        report = EvalReport(
            avg_faithfulness=0.2,
            avg_retrieval_precision=0.8,
            avg_retrieval_recall=0.8,
            avg_context_relevance=0.8,
            avg_citation_accuracy=0.8,
            avg_lane_accuracy=0.9,
        )
        recs = evaluator._generate_recommendations(report)
        assert any("faithfulness" in r.lower() for r in recs)

    def test_recommendations_all_passing(self, evaluator: RAGEvaluator):
        report = EvalReport(
            avg_faithfulness=0.9,
            avg_retrieval_precision=0.9,
            avg_retrieval_recall=0.9,
            avg_context_relevance=0.9,
            avg_citation_accuracy=0.9,
            avg_lane_accuracy=0.9,
        )
        recs = evaluator._generate_recommendations(report)
        assert any("passing" in r.lower() for r in recs)

    # -- Stats --------------------------------------------------------------

    def test_get_stats(self, evaluator: RAGEvaluator):
        evaluator.evaluate_single("q", "a", [{"text": "t", "source": "s"}])
        stats = evaluator.get_stats()
        assert stats["total_evaluations"] >= 1
        assert "thresholds" in stats

    # -- Tokenizer ----------------------------------------------------------

    def test_tokenizer(self):
        tokens = RAGEvaluator._tokenize("Hello, World! Testing 123.")
        assert "Hello" in tokens
        assert "World" in tokens
        assert "123" in tokens

    # -- Context relevance --------------------------------------------------

    def test_context_relevance_high(self, evaluator: RAGEvaluator):
        score = evaluator._compute_context_relevance(
            "MCR 2.003 disqualification",
            [{"text": "MCR 2.003 governs judicial disqualification for bias."}],
        )
        assert score > 0.3

    def test_context_relevance_low(self, evaluator: RAGEvaluator):
        score = evaluator._compute_context_relevance(
            "MCR 2.003 disqualification",
            [{"text": "The weather is nice today."}],
        )
        assert score < 0.3


# ===========================================================================
# Run all tests
# ===========================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
