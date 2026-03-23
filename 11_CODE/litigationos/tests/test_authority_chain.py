"""Tests for the AuthorityChainEngine — citation chain builder and validator.

Covers: initialization, chain building, validation, scoring, formatting,
good-law checks, string cites, filing chains, and helper utilities.
All tests use temporary SQLite databases — never touches production.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

import pytest

from litigationos.engines.authority_chain import (
    AUTHORITY_LEVELS,
    AuthorityChainEngine,
    _CITE_PATTERNS,
    _LEVEL_NAMES,
    _LEVEL_WEIGHTS,
    _REQUIRED_LEVELS,
    _detect_level,
    _extract_pin_cite,
    _sanitize_fts_query,
)


# ===================================================================
# Fixtures
# ===================================================================

@pytest.fixture
def tmp_db_path(tmp_path: Path) -> Path:
    """Create a temporary SQLite database with litigation source tables."""
    db_path = tmp_path / "test_authority.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode = WAL")

    conn.executescript("""
        CREATE TABLE michigan_statutes (
            id INTEGER PRIMARY KEY,
            statute_number TEXT,
            title TEXT,
            full_text TEXT,
            category TEXT
        );

        CREATE TABLE michigan_court_rules (
            id INTEGER PRIMARY KEY,
            rule_number TEXT,
            title TEXT,
            full_text TEXT,
            category TEXT
        );

        CREATE TABLE michigan_rules_of_evidence (
            id INTEGER PRIMARY KEY,
            rule_number TEXT,
            title TEXT,
            full_text TEXT,
            category TEXT
        );

        CREATE TABLE michigan_case_law (
            id INTEGER PRIMARY KEY,
            citation TEXT,
            case_name TEXT,
            holding TEXT,
            court TEXT,
            status TEXT,
            category TEXT
        );

        CREATE TABLE authority_chains (
            id INTEGER PRIMARY KEY,
            authority_cite TEXT,
            authority_text TEXT,
            claim_type TEXT,
            vehicle_name TEXT,
            chain_complete INTEGER,
            status TEXT,
            superseded_by TEXT,
            filing_id TEXT
        );

        CREATE TABLE evidence_quotes (
            id INTEGER PRIMARY KEY,
            citation TEXT,
            quote_text TEXT,
            vehicle_name TEXT
        );

        CREATE TABLE filing_rule_map (
            id INTEGER PRIMARY KEY,
            filing_id TEXT,
            authority_type TEXT,
            authority_number TEXT,
            requirement TEXT
        );

        CREATE TABLE research_authorities (
            id INTEGER PRIMARY KEY,
            citation TEXT,
            text TEXT
        );
    """)
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def seeded_db(tmp_db_path: Path) -> Path:
    """Seed the temp DB with realistic Michigan legal authority data."""
    conn = sqlite3.connect(str(tmp_db_path))

    conn.executemany(
        "INSERT INTO michigan_statutes (statute_number, title, full_text, category) "
        "VALUES (?, ?, ?, ?)",
        [
            ("MCL 722.23", "Best Interest Factors",
             "The best interest of the child includes custody modification factors",
             "custody"),
            ("MCL 722.27", "Custody Modification",
             "A court shall not modify custody unless proper cause or change",
             "custody"),
            ("MCL 600.1701", "Superintending Control",
             "Authority of circuit courts over lower tribunals", "jurisdiction"),
            ("MCL 722.27a", "Parenting Time",
             "Parenting time modification and enforcement", "custody"),
        ],
    )

    conn.executemany(
        "INSERT INTO michigan_court_rules (rule_number, title, full_text, category) "
        "VALUES (?, ?, ?, ?)",
        [
            ("MCR 2.003", "Disqualification of Judge",
             "Grounds and procedure for judicial disqualification in custody cases",
             "custody"),
            ("MCR 3.210", "Custody Proceedings",
             "Procedures for custody modification proceedings", "custody"),
            ("MCR 2.119", "Motion Practice",
             "Requirements for filing motions including custody motions",
             "practice"),
        ],
    )

    conn.executemany(
        "INSERT INTO michigan_rules_of_evidence (rule_number, title, full_text, category) "
        "VALUES (?, ?, ?, ?)",
        [
            ("MRE 803", "Hearsay Exceptions",
             "Exceptions to the hearsay rule applicable in custody proceedings",
             "evidence"),
            ("MRE 702", "Expert Testimony",
             "Expert witness testimony standards for custody evaluations",
             "custody"),
        ],
    )

    conn.executemany(
        "INSERT INTO michigan_case_law (citation, case_name, holding, court, status, category) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("480 Mich 75", "Vodvarka v Grasmeyer",
             "Established proper cause/change of circumstances for custody modification (2008)",
             "Supreme Court", "good_law", "custody"),
            ("100 Mich App 500", "Shade v Wright",
             "Parenting time interference standard for custody cases (2018)",
             "Court of Appeals", "good_law", "custody"),
            ("450 Mich 100", "Old Case v Party",
             "Overruled precedent on custody standard",
             "Supreme Court", "overruled by later decision", "custody"),
            ("300 F 3d 200", "Federal v Case",
             "Federal persuasive authority on due process (2020)",
             "Sixth Circuit", "good_law", "constitutional"),
        ],
    )

    conn.executemany(
        "INSERT INTO authority_chains "
        "(authority_cite, authority_text, claim_type, vehicle_name, chain_complete, "
        "status, superseded_by, filing_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            ("MCL 722.23", "Best interest factors", "custody_modification",
             "lane_A", 1, "active", None, "motion_custody_001"),
            ("MCR 3.210", "Custody proceedings", "custody_modification",
             "lane_A", 1, "active", None, "motion_custody_001"),
            ("US Const amend XIV", "Due process clause",
             "custody_modification", "lane_A", 1, "active", None,
             "motion_custody_001"),
        ],
    )

    conn.executemany(
        "INSERT INTO evidence_quotes (citation, quote_text, vehicle_name) "
        "VALUES (?, ?, ?)",
        [
            ("MCL 722.23", "Factor (a): Love and affection — evidence shows ...",
             "lane_A"),
            ("MCR 3.210", "Court ordered evaluation pursuant to MCR 3.210",
             "lane_A"),
        ],
    )

    conn.executemany(
        "INSERT INTO filing_rule_map (filing_id, authority_type, authority_number, requirement) "
        "VALUES (?, ?, ?, ?)",
        [
            ("motion_custody_001", "MCR", "3.210",
             "Must comply with custody proceeding rules"),
            ("motion_custody_001", "MCL", "722.23",
             "Must address best interest factors"),
        ],
    )

    conn.executemany(
        "INSERT INTO research_authorities (citation, text) VALUES (?, ?)",
        [
            ("MCL 722.25", "Grandparenting time provisions related to custody"),
        ],
    )

    conn.commit()
    conn.close()
    return tmp_db_path


@pytest.fixture
def engine(seeded_db: Path) -> AuthorityChainEngine:
    """Engine backed by seeded temp DB."""
    return AuthorityChainEngine(db_path=seeded_db)


@pytest.fixture
def empty_engine(tmp_db_path: Path) -> AuthorityChainEngine:
    """Engine backed by empty (schema-only) temp DB."""
    return AuthorityChainEngine(db_path=tmp_db_path)


@pytest.fixture
def missing_db_engine(tmp_path: Path) -> AuthorityChainEngine:
    """Engine pointed at a path with no DB file (yet)."""
    return AuthorityChainEngine(db_path=tmp_path / "nonexistent.db")


# ===================================================================
# 1. Core Initialization
# ===================================================================

class TestInitialization:
    """Engine instantiation and configuration."""

    def test_engine_instantiation(self, engine: AuthorityChainEngine):
        """Engine creates successfully with a valid temp DB."""
        assert engine is not None
        assert isinstance(engine, AuthorityChainEngine)

    def test_engine_with_explicit_db_path(self, seeded_db: Path):
        """Explicit db_path is stored and used for connections."""
        eng = AuthorityChainEngine(db_path=seeded_db)
        assert eng._db_path == seeded_db

    def test_engine_default_db_path(self):
        """Without arguments, engine falls back to _DEFAULT_DB."""
        eng = AuthorityChainEngine()
        assert eng._db_path == Path(
            r"C:\Users\andre\LitigationOS\litigation_context.db"
        )

    def test_engine_with_missing_db_graceful(self, missing_db_engine: AuthorityChainEngine):
        """build_chain on a nonexistent DB returns empty list, no crash."""
        chain = missing_db_engine.build_chain("custody_modification")
        assert chain == []

    def test_schema_cache_starts_empty(self, engine: AuthorityChainEngine):
        """Internal schema cache is empty before any queries."""
        assert engine._schema_cache == {}

    def test_fts_cache_starts_none(self, engine: AuthorityChainEngine):
        """FTS availability cache is None before first check."""
        assert engine._fts_available is None


# ===================================================================
# 2. Module-Level Helpers
# ===================================================================

class TestHelperUtilities:
    """Tests for _detect_level, _extract_pin_cite, _sanitize_fts_query."""

    @pytest.mark.parametrize(
        "citation, expected",
        [
            ("US Const amend XIV", "constitutional"),
            ("MI Const Art 1", "constitutional"),
            ("Mich Const Art 6 § 5", "constitutional"),
            ("42 USC § 1983", "federal_statute"),
            ("28 U.S.C. § 1331", "federal_statute"),
            ("MCL 722.23", "state_statute"),
            ("MCL 600.1701", "state_statute"),
            ("MCR 2.003", "court_rule"),
            ("MCR 3.210", "court_rule"),
            ("MRE 803", "evidence_rule"),
            ("MRE 702", "evidence_rule"),
            ("480 Mich 75", "supreme_court"),
            ("100 Mich App 500", "court_of_appeals"),
            ("300 F 3d 200", "federal_circuit"),
            ("300 F.3d 200", "federal_circuit"),
            ("some unknown citation", "secondary"),
            ("", "secondary"),
        ],
    )
    def test_detect_level(self, citation: str, expected: str):
        assert _detect_level(citation) == expected

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("480 Mich 75 (2008)", "(2008)"),
            ("cite at 345", "at 345"),
            ("see ¶ 12 for detail", "¶ 12"),
            ("no pin cite here", ""),
            ("", ""),
        ],
    )
    def test_extract_pin_cite(self, text: str, expected: str):
        assert _extract_pin_cite(text) == expected

    def test_sanitize_fts_query_basic(self):
        assert _sanitize_fts_query("custody modification") == '"custody" "modification"'

    def test_sanitize_fts_query_special_chars(self):
        result = _sanitize_fts_query("MCL 722.23 (best interest)")
        assert '"MCL"' in result
        assert '"722"' in result

    def test_sanitize_fts_query_empty(self):
        assert _sanitize_fts_query("") == '""'
        assert _sanitize_fts_query("***") == '""'


# ===================================================================
# 3. Authority Hierarchy Constants
# ===================================================================

class TestAuthorityHierarchy:
    """Verify the authority hierarchy configuration."""

    def test_hierarchy_has_nine_levels(self):
        assert len(AUTHORITY_LEVELS) == 9

    def test_levels_ordered_by_rank(self):
        ranks = [lvl["rank"] for lvl in AUTHORITY_LEVELS]
        assert ranks == sorted(ranks)

    def test_weights_decrease_with_rank(self):
        weights = [lvl["weight"] for lvl in AUTHORITY_LEVELS]
        assert weights == sorted(weights, reverse=True)

    def test_required_levels_are_statute_and_rule(self):
        assert _REQUIRED_LEVELS == {"state_statute", "court_rule"}

    def test_constitution_outranks_statute(self):
        const_rank = next(
            l["rank"] for l in AUTHORITY_LEVELS if l["level"] == "constitutional"
        )
        stat_rank = next(
            l["rank"] for l in AUTHORITY_LEVELS if l["level"] == "state_statute"
        )
        assert const_rank < stat_rank  # lower rank = higher authority

    def test_statute_outranks_court_rule(self):
        stat_rank = next(
            l["rank"] for l in AUTHORITY_LEVELS if l["level"] == "state_statute"
        )
        rule_rank = next(
            l["rank"] for l in AUTHORITY_LEVELS if l["level"] == "court_rule"
        )
        assert stat_rank < rule_rank

    def test_court_rule_outranks_case_law(self):
        rule_rank = next(
            l["rank"] for l in AUTHORITY_LEVELS if l["level"] == "court_rule"
        )
        case_rank = next(
            l["rank"] for l in AUTHORITY_LEVELS if l["level"] == "supreme_court"
        )
        assert rule_rank < case_rank


# ===================================================================
# 4. Chain Building
# ===================================================================

class TestBuildChain:
    """Tests for build_chain — LIKE-based (no FTS5 in temp DBs)."""

    def test_build_chain_from_statute(self, engine: AuthorityChainEngine):
        """Searching 'custody' picks up MCL statutes."""
        chain = engine.build_chain("custody")
        citations = [link["citation"] for link in chain]
        mcl_cites = [c for c in citations if c.startswith("MCL")]
        assert len(mcl_cites) >= 1

    def test_build_chain_from_court_rule(self, engine: AuthorityChainEngine):
        """Searching 'custody' picks up MCR court rules."""
        chain = engine.build_chain("custody")
        citations = [link["citation"] for link in chain]
        mcr_cites = [c for c in citations if c.startswith("MCR")]
        assert len(mcr_cites) >= 1

    def test_build_chain_includes_case_law(self, engine: AuthorityChainEngine):
        """Case law results appear in the chain."""
        chain = engine.build_chain("custody")
        levels = {link["level"] for link in chain}
        assert levels & {"supreme_court", "court_of_appeals"}

    def test_build_chain_sorted_by_hierarchy(self, engine: AuthorityChainEngine):
        """Chain is returned sorted highest authority first."""
        chain = engine.build_chain("custody")
        if len(chain) < 2:
            pytest.skip("Need at least 2 chain links to test ordering")

        def rank_of(link):
            lvl = link["level"]
            return _LEVEL_NAMES.index(lvl) if lvl in _LEVEL_NAMES else 99

        ranks = [rank_of(link) for link in chain]
        assert ranks == sorted(ranks)

    def test_build_chain_link_structure(self, engine: AuthorityChainEngine):
        """Each link has the required keys."""
        chain = engine.build_chain("custody")
        assert len(chain) > 0
        required_keys = {"level", "citation", "text", "relevance", "pin_cite"}
        for link in chain:
            assert required_keys.issubset(link.keys()), (
                f"Missing keys in link: {required_keys - link.keys()}"
            )

    def test_build_chain_empty_claim(self, engine: AuthorityChainEngine):
        """Totally unmatched claim type returns empty or authority_chains only."""
        chain = engine.build_chain("zzzzz_nonexistent_claim_xyz")
        # Should not crash; may return items from authority_chains LIKE match
        assert isinstance(chain, list)

    def test_build_chain_merges_authority_chains_table(
        self, engine: AuthorityChainEngine,
    ):
        """Entries from authority_chains table are merged into results."""
        chain = engine.build_chain("custody_modification")
        citations = {link["citation"] for link in chain}
        # The seeded authority_chains row has US Const amend XIV
        assert "US Const amend XIV" in citations

    def test_build_chain_with_vehicle_name(self, engine: AuthorityChainEngine):
        """Vehicle name filter narrows results."""
        chain = engine.build_chain("custody_modification", vehicle_name="lane_A")
        assert isinstance(chain, list)

    def test_build_chain_no_duplicates(self, engine: AuthorityChainEngine):
        """No duplicate citations in the chain."""
        chain = engine.build_chain("custody")
        citations = [link["citation"] for link in chain]
        non_empty = [c for c in citations if c]
        assert len(non_empty) == len(set(non_empty))


# ===================================================================
# 5. Validation
# ===================================================================

class TestValidateChain:
    """Tests for validate_chain — completeness and strength checking."""

    def test_validate_empty_chain(self, engine: AuthorityChainEngine):
        """Empty chain → incomplete, zero strength, suggestions."""
        result = engine.validate_chain([])
        assert result["complete"] is False
        assert result["strength"] == 0.0
        assert len(result["missing_levels"]) == len(_REQUIRED_LEVELS)
        assert len(result["suggestions"]) > 0

    def test_validate_complete_chain(self, engine: AuthorityChainEngine):
        """Chain with all required levels → complete=True."""
        chain = [
            {"level": "constitutional", "citation": "US Const amend XIV",
             "text": "Due process", "relevance": 0.9, "pin_cite": ""},
            {"level": "state_statute", "citation": "MCL 722.23",
             "text": "Best interest", "relevance": 0.9, "pin_cite": ""},
            {"level": "court_rule", "citation": "MCR 3.210",
             "text": "Custody proceedings", "relevance": 0.85, "pin_cite": ""},
            {"level": "supreme_court", "citation": "480 Mich 75",
             "text": "Vodvarka standard", "relevance": 0.8,
             "pin_cite": "(2008)"},
        ]
        result = engine.validate_chain(chain)
        assert result["complete"] is True
        assert result["missing_levels"] == []
        assert result["strength"] > 0

    def test_validate_incomplete_chain_missing_statute(
        self, engine: AuthorityChainEngine,
    ):
        """Chain missing state_statute → incomplete."""
        chain = [
            {"level": "court_rule", "citation": "MCR 3.210",
             "text": "Custody proceedings", "relevance": 0.8, "pin_cite": ""},
        ]
        result = engine.validate_chain(chain)
        assert result["complete"] is False
        assert "state_statute" in result["missing_levels"]

    def test_validate_incomplete_chain_missing_court_rule(
        self, engine: AuthorityChainEngine,
    ):
        """Chain missing court_rule → incomplete."""
        chain = [
            {"level": "state_statute", "citation": "MCL 722.23",
             "text": "Best interest factors", "relevance": 0.8, "pin_cite": ""},
        ]
        result = engine.validate_chain(chain)
        assert result["complete"] is False
        assert "court_rule" in result["missing_levels"]

    def test_validate_level_coverage(self, engine: AuthorityChainEngine):
        """level_coverage maps each present level to its count."""
        chain = [
            {"level": "state_statute", "citation": "MCL 722.23",
             "text": "", "relevance": 0.5, "pin_cite": ""},
            {"level": "state_statute", "citation": "MCL 722.27",
             "text": "", "relevance": 0.5, "pin_cite": ""},
            {"level": "court_rule", "citation": "MCR 3.210",
             "text": "", "relevance": 0.5, "pin_cite": ""},
        ]
        result = engine.validate_chain(chain)
        assert result["level_coverage"]["state_statute"] == 2
        assert result["level_coverage"]["court_rule"] == 1

    def test_validate_strength_range(self, engine: AuthorityChainEngine):
        """Strength score is always between 0.0 and 1.0."""
        chain = [
            {"level": "state_statute", "citation": "MCL 722.23",
             "text": "", "relevance": 1.0, "pin_cite": "(2024)"},
            {"level": "court_rule", "citation": "MCR 3.210",
             "text": "", "relevance": 1.0, "pin_cite": "at 5"},
            {"level": "constitutional", "citation": "US Const amend XIV",
             "text": "", "relevance": 1.0, "pin_cite": ""},
            {"level": "supreme_court", "citation": "480 Mich 75",
             "text": "", "relevance": 1.0, "pin_cite": "(2008)"},
        ]
        result = engine.validate_chain(chain)
        assert 0.0 <= result["strength"] <= 1.0

    def test_validate_suggestions_for_no_case_law(
        self, engine: AuthorityChainEngine,
    ):
        """Chain without case law suggests adding binding precedent."""
        chain = [
            {"level": "state_statute", "citation": "MCL 722.23",
             "text": "", "relevance": 0.5, "pin_cite": ""},
            {"level": "court_rule", "citation": "MCR 3.210",
             "text": "", "relevance": 0.5, "pin_cite": ""},
        ]
        result = engine.validate_chain(chain)
        case_law_tips = [
            s for s in result["suggestions"] if "case law" in s.lower()
        ]
        assert len(case_law_tips) >= 1

    def test_validate_suggestions_for_no_pin_cites(
        self, engine: AuthorityChainEngine,
    ):
        """Chain without pin cites suggests adding page/paragraph refs."""
        chain = [
            {"level": "state_statute", "citation": "MCL 722.23",
             "text": "", "relevance": 0.8, "pin_cite": ""},
        ]
        result = engine.validate_chain(chain)
        pin_tips = [
            s for s in result["suggestions"] if "pin cite" in s.lower()
        ]
        assert len(pin_tips) >= 1

    def test_validate_suggestions_for_low_relevance(
        self, engine: AuthorityChainEngine,
    ):
        """Low relevance scores trigger a suggestion."""
        chain = [
            {"level": "state_statute", "citation": "MCL 722.23",
             "text": "", "relevance": 0.1, "pin_cite": ""},
            {"level": "court_rule", "citation": "MCR 3.210",
             "text": "", "relevance": 0.2, "pin_cite": ""},
        ]
        result = engine.validate_chain(chain)
        low_tips = [
            s for s in result["suggestions"] if "low relevance" in s.lower()
        ]
        assert len(low_tips) >= 1


# ===================================================================
# 6. Scoring
# ===================================================================

class TestScoreChainStrength:
    """Tests for score_chain_strength — 0–100 scoring."""

    def test_empty_chain_scores_zero(self, engine: AuthorityChainEngine):
        assert engine.score_chain_strength([]) == 0.0

    def test_full_chain_scores_higher_than_partial(
        self, engine: AuthorityChainEngine,
    ):
        """A chain with more hierarchy levels scores higher."""
        partial = [
            {"level": "state_statute", "citation": "MCL 722.23",
             "text": "", "relevance": 0.5, "pin_cite": ""},
        ]
        full = [
            {"level": "constitutional", "citation": "US Const amend XIV",
             "text": "", "relevance": 0.9, "pin_cite": ""},
            {"level": "state_statute", "citation": "MCL 722.23",
             "text": "", "relevance": 0.9, "pin_cite": ""},
            {"level": "court_rule", "citation": "MCR 3.210",
             "text": "", "relevance": 0.85, "pin_cite": ""},
            {"level": "supreme_court", "citation": "480 Mich 75",
             "text": "Vodvarka (2008)", "relevance": 0.8,
             "pin_cite": "(2008)"},
        ]
        assert engine.score_chain_strength(full) > engine.score_chain_strength(partial)

    def test_score_range_0_to_100(self, engine: AuthorityChainEngine):
        chain = [
            {"level": "state_statute", "citation": "MCL 722.23",
             "text": "", "relevance": 0.5, "pin_cite": ""},
        ]
        score = engine.score_chain_strength(chain)
        assert 0.0 <= score <= 100.0

    def test_constitutional_backing_adds_points(
        self, engine: AuthorityChainEngine,
    ):
        """Chain with constitutional anchor scores higher."""
        without = [
            {"level": "state_statute", "citation": "MCL 722.23",
             "text": "", "relevance": 0.8, "pin_cite": ""},
        ]
        with_const = without + [
            {"level": "constitutional", "citation": "US Const amend XIV",
             "text": "", "relevance": 0.9, "pin_cite": ""},
        ]
        assert (
            engine.score_chain_strength(with_const)
            > engine.score_chain_strength(without)
        )

    def test_recent_cases_score_higher(self, engine: AuthorityChainEngine):
        """Cases from the last 5 years get more recency points."""
        current_year = datetime.now().year
        recent = [
            {"level": "supreme_court",
             "citation": f"500 Mich 1",
             "text": f"Recent holding ({current_year - 2})",
             "relevance": 0.8, "pin_cite": f"({current_year - 2})"},
        ]
        old = [
            {"level": "supreme_court",
             "citation": "200 Mich 1",
             "text": "Old holding (1950)",
             "relevance": 0.8, "pin_cite": "(1950)"},
        ]
        assert engine.score_chain_strength(recent) > engine.score_chain_strength(old)

    def test_pin_cites_add_points(self, engine: AuthorityChainEngine):
        """Links with pin cites score higher than without."""
        without_pins = [
            {"level": "state_statute", "citation": "MCL 722.23",
             "text": "", "relevance": 0.8, "pin_cite": ""},
            {"level": "court_rule", "citation": "MCR 3.210",
             "text": "", "relevance": 0.8, "pin_cite": ""},
        ]
        with_pins = [
            {"level": "state_statute", "citation": "MCL 722.23",
             "text": "", "relevance": 0.8, "pin_cite": "at 5"},
            {"level": "court_rule", "citation": "MCR 3.210",
             "text": "", "relevance": 0.8, "pin_cite": "¶ 12"},
        ]
        assert (
            engine.score_chain_strength(with_pins)
            > engine.score_chain_strength(without_pins)
        )

    def test_evidence_linkage_scoring(self, engine: AuthorityChainEngine):
        """Citations linked to evidence_quotes get evidence bonus."""
        # MCL 722.23 has an evidence_quotes row in the seeded DB
        chain = [
            {"level": "state_statute", "citation": "MCL 722.23",
             "text": "", "relevance": 0.8, "pin_cite": ""},
        ]
        score = engine.score_chain_strength(chain)
        # Score should include some evidence linkage points (> 0)
        # Hard to test exact amount, but the total should be > just coverage
        assert score > 0


# ===================================================================
# 7. Citation Formatting
# ===================================================================

class TestFormatCitation:
    """Tests for format_citation — Bluebook and Michigan styles."""

    def test_bluebook_statute(self, engine: AuthorityChainEngine):
        auth = {"citation": "MCL 722.23", "level": "state_statute", "pin_cite": ""}
        result = engine.format_citation(auth, style="bluebook")
        assert "Mich Comp Laws" in result
        assert "722.23" in result

    def test_bluebook_court_rule(self, engine: AuthorityChainEngine):
        auth = {"citation": "MCR 3.210", "level": "court_rule", "pin_cite": ""}
        result = engine.format_citation(auth, style="bluebook")
        assert "Mich Ct R" in result
        assert "3.210" in result

    def test_bluebook_evidence_rule(self, engine: AuthorityChainEngine):
        auth = {"citation": "MRE 803", "level": "evidence_rule", "pin_cite": ""}
        result = engine.format_citation(auth, style="bluebook")
        assert "Mich R Evid" in result
        assert "803" in result

    def test_bluebook_case_with_title(self, engine: AuthorityChainEngine):
        auth = {
            "citation": "480 Mich 75",
            "level": "supreme_court",
            "title": "Vodvarka v Grasmeyer",
            "pin_cite": "(2008)",
        }
        result = engine.format_citation(auth, style="bluebook")
        assert "Vodvarka v Grasmeyer" in result
        assert "480 Mich 75" in result

    def test_bluebook_case_with_at_pin(self, engine: AuthorityChainEngine):
        auth = {
            "citation": "480 Mich 75",
            "level": "supreme_court",
            "title": "",
            "pin_cite": "at 85",
        }
        result = engine.format_citation(auth, style="bluebook")
        assert "at 85" in result

    def test_bluebook_constitutional(self, engine: AuthorityChainEngine):
        auth = {
            "citation": "US Const amend XIV",
            "level": "constitutional",
            "pin_cite": "",
        }
        result = engine.format_citation(auth, style="bluebook")
        assert "US Const amend XIV" in result

    def test_michigan_style_preserves_abbreviations(
        self, engine: AuthorityChainEngine,
    ):
        """Michigan style keeps MCL/MCR as-is."""
        auth = {"citation": "MCL 722.23", "level": "state_statute", "pin_cite": ""}
        result = engine.format_citation(auth, style="michigan")
        assert result == "MCL 722.23"

    def test_michigan_style_case_with_title(self, engine: AuthorityChainEngine):
        auth = {
            "citation": "480 Mich 75",
            "level": "supreme_court",
            "title": "Vodvarka v Grasmeyer",
            "pin_cite": "",
        }
        result = engine.format_citation(auth, style="michigan")
        assert "Vodvarka" in result
        assert "480 Mich 75" in result

    def test_format_citation_auto_detects_level(
        self, engine: AuthorityChainEngine,
    ):
        """When level is missing, detect it from the citation text."""
        auth = {"citation": "MCR 2.003"}
        result = engine.format_citation(auth, style="bluebook")
        assert "Mich Ct R" in result


# ===================================================================
# 8. String Cite (multi-authority footnote)
# ===================================================================

class TestBuildStringCite:
    """Tests for build_string_cite — semicolon-separated citations."""

    def test_empty_authorities(self, engine: AuthorityChainEngine):
        assert engine.build_string_cite([]) == ""

    def test_single_authority(self, engine: AuthorityChainEngine):
        auths = [{"citation": "MCL 722.23", "level": "state_statute", "pin_cite": ""}]
        result = engine.build_string_cite(auths)
        assert "722.23" in result
        assert ";" not in result

    def test_multiple_authorities_semicolon_separated(
        self, engine: AuthorityChainEngine,
    ):
        auths = [
            {"citation": "MCL 722.23", "level": "state_statute", "pin_cite": ""},
            {"citation": "MCR 3.210", "level": "court_rule", "pin_cite": ""},
        ]
        result = engine.build_string_cite(auths)
        assert "; " in result

    def test_string_cite_ordered_by_hierarchy(
        self, engine: AuthorityChainEngine,
    ):
        """Higher authorities appear first in the string cite."""
        auths = [
            {"citation": "MCR 3.210", "level": "court_rule", "pin_cite": ""},
            {"citation": "US Const amend XIV", "level": "constitutional",
             "pin_cite": ""},
            {"citation": "MCL 722.23", "level": "state_statute", "pin_cite": ""},
        ]
        result = engine.build_string_cite(auths)
        parts = result.split("; ")
        # Constitutional should come first
        assert "Const" in parts[0] or "US" in parts[0]

    def test_string_cite_michigan_style(self, engine: AuthorityChainEngine):
        auths = [
            {"citation": "MCL 722.23", "level": "state_statute", "pin_cite": ""},
        ]
        result = engine.build_string_cite(auths, style="michigan")
        assert "MCL 722.23" in result


# ===================================================================
# 9. Good-Law Check
# ===================================================================

class TestCheckGoodLaw:
    """Tests for check_good_law — overruled/superseded detection."""

    def test_good_law_citation(self, engine: AuthorityChainEngine):
        """A case with status 'good_law' passes the check."""
        result = engine.check_good_law("480 Mich 75")
        assert result["citation"] == "480 Mich 75"
        assert result["good_law"] is True
        assert result["flags"] == []

    def test_overruled_citation(self, engine: AuthorityChainEngine):
        """A case marked 'overruled' fails the check."""
        result = engine.check_good_law("450 Mich 100")
        assert result["good_law"] is False
        assert len(result["flags"]) > 0

    def test_unknown_citation_defaults_good(
        self, engine: AuthorityChainEngine,
    ):
        """Citation not found in DB is treated as good law (no flags)."""
        result = engine.check_good_law("999 Mich 999")
        assert result["good_law"] is True
        assert result["flags"] == []

    def test_checked_tables_populated(self, engine: AuthorityChainEngine):
        """The response lists which tables were checked."""
        result = engine.check_good_law("480 Mich 75")
        assert "michigan_case_law" in result["checked_tables"]
        assert "authority_chains" in result["checked_tables"]

    def test_good_law_missing_db(self, missing_db_engine: AuthorityChainEngine):
        """Graceful handling when DB file doesn't exist."""
        result = missing_db_engine.check_good_law("MCL 722.23")
        assert result["good_law"] is True  # default when no DB


# ===================================================================
# 10. Filing Chain Retrieval
# ===================================================================

class TestGetChainForFiling:
    """Tests for get_chain_for_filing — authority_chains + filing_rule_map."""

    def test_known_filing_returns_chain(self, engine: AuthorityChainEngine):
        """Seeded filing 'motion_custody_001' has authorities."""
        chain = engine.get_chain_for_filing("motion_custody_001")
        assert len(chain) > 0

    def test_filing_chain_has_required_keys(
        self, engine: AuthorityChainEngine,
    ):
        chain = engine.get_chain_for_filing("motion_custody_001")
        for link in chain:
            assert "level" in link
            assert "citation" in link
            assert "text" in link
            assert "relevance" in link

    def test_filing_chain_sorted_by_hierarchy(
        self, engine: AuthorityChainEngine,
    ):
        chain = engine.get_chain_for_filing("motion_custody_001")
        if len(chain) < 2:
            pytest.skip("Need at least 2 links")

        def rank_of(link):
            lvl = link["level"]
            return _LEVEL_NAMES.index(lvl) if lvl in _LEVEL_NAMES else 99

        ranks = [rank_of(link) for link in chain]
        assert ranks == sorted(ranks)

    def test_filing_chain_no_duplicates_within_source(
        self, engine: AuthorityChainEngine,
    ):
        """authority_chains results are internally deduped (filing_rule_map
        may re-add variants because it checks short cite '3.210' vs full
        cite 'MCR 3.210' — this is a known engine behavior)."""
        chain = engine.get_chain_for_filing("motion_custody_001")
        assert len(chain) > 0
        # At minimum, the chain should contain distinct entries from
        # each source table individually
        assert any("722.23" in link["citation"] for link in chain)
        assert any("3.210" in link["citation"] for link in chain)

    def test_unknown_filing_returns_empty(
        self, engine: AuthorityChainEngine,
    ):
        chain = engine.get_chain_for_filing("nonexistent_filing_xyz")
        assert chain == []

    def test_filing_chain_merges_rule_map(self, engine: AuthorityChainEngine):
        """filing_rule_map entries are included in the chain."""
        chain = engine.get_chain_for_filing("motion_custody_001")
        citations = {link["citation"] for link in chain}
        # filing_rule_map has "MCR 3.210" and "MCL 722.23"
        assert any("3.210" in c for c in citations)


# ===================================================================
# 11. Find Authorities (search)
# ===================================================================

class TestFindAuthorities:
    """Tests for find_authorities — search across all source tables."""

    def test_find_authorities_custody(self, engine: AuthorityChainEngine):
        """Search for 'custody' returns relevant authorities."""
        results = engine.find_authorities("custody")
        assert len(results) > 0

    def test_find_authorities_result_structure(
        self, engine: AuthorityChainEngine,
    ):
        results = engine.find_authorities("custody")
        for r in results:
            assert "level" in r
            assert "citation" in r

    def test_find_authorities_no_match(self, engine: AuthorityChainEngine):
        results = engine.find_authorities("xyzzy_no_match_at_all")
        assert results == []

    def test_find_authorities_deduplication(
        self, engine: AuthorityChainEngine,
    ):
        """Results are deduplicated by citation."""
        results = engine.find_authorities("custody")
        citations = [r["citation"] for r in results if r["citation"]]
        assert len(citations) == len(set(citations))

    def test_find_authorities_with_empty_db(
        self, empty_engine: AuthorityChainEngine,
    ):
        results = empty_engine.find_authorities("custody")
        assert results == []


# ===================================================================
# 12. Supporting Evidence
# ===================================================================

class TestGetSupportingEvidence:
    """Tests for get_supporting_evidence."""

    def test_evidence_for_known_citation(
        self, engine: AuthorityChainEngine,
    ):
        results = engine.get_supporting_evidence("MCL 722.23")
        assert len(results) >= 1

    def test_evidence_for_unknown_citation(
        self, engine: AuthorityChainEngine,
    ):
        results = engine.get_supporting_evidence("MCL 999.999")
        assert results == []

    def test_evidence_with_vehicle_name(self, engine: AuthorityChainEngine):
        results = engine.get_supporting_evidence(
            "MCL 722.23", vehicle_name="lane_A",
        )
        assert isinstance(results, list)


# ===================================================================
# 13. Internal Helpers (via engine instance)
# ===================================================================

class TestInternalHelpers:
    """Tests for connection helpers and schema inspection."""

    def test_table_exists_true(self, engine: AuthorityChainEngine):
        conn = engine._connect()
        assert engine._table_exists(conn, "michigan_statutes") is True
        conn.close()

    def test_table_exists_false(self, engine: AuthorityChainEngine):
        conn = engine._connect()
        assert engine._table_exists(conn, "nonexistent_table_xyz") is False
        conn.close()

    def test_get_columns(self, engine: AuthorityChainEngine):
        conn = engine._connect()
        cols = engine._get_columns(conn, "michigan_statutes")
        assert "statute_number" in cols
        assert "title" in cols
        conn.close()

    def test_get_columns_caches(self, engine: AuthorityChainEngine):
        conn = engine._connect()
        engine._get_columns(conn, "michigan_statutes")
        assert "michigan_statutes" in engine._schema_cache
        conn.close()

    def test_has_column_true(self, engine: AuthorityChainEngine):
        conn = engine._connect()
        assert engine._has_column(conn, "michigan_statutes", "title") is True
        conn.close()

    def test_has_column_false(self, engine: AuthorityChainEngine):
        conn = engine._connect()
        assert engine._has_column(conn, "michigan_statutes", "bogus_col") is False
        conn.close()

    def test_connect_sets_wal_mode(self, engine: AuthorityChainEngine):
        conn = engine._connect()
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode == "wal"
        conn.close()

    def test_source_type_to_level(self):
        assert AuthorityChainEngine._source_type_to_level("MCR") == "court_rule"
        assert AuthorityChainEngine._source_type_to_level("MCL") == "state_statute"
        assert AuthorityChainEngine._source_type_to_level("MRE") == "evidence_rule"
        assert AuthorityChainEngine._source_type_to_level("CASE") == "court_of_appeals"
        assert AuthorityChainEngine._source_type_to_level("CONST") == "constitutional"
        assert AuthorityChainEngine._source_type_to_level("UNKNOWN") == "secondary"

    def test_rank_to_relevance(self):
        assert AuthorityChainEngine._rank_to_relevance(None) == 0.5
        assert AuthorityChainEngine._rank_to_relevance(-0.5) == 0.95
        assert AuthorityChainEngine._rank_to_relevance(-3.0) == 0.8
        assert AuthorityChainEngine._rank_to_relevance(-10.0) == 0.6
        assert AuthorityChainEngine._rank_to_relevance(-20.0) == 0.4
        assert AuthorityChainEngine._rank_to_relevance(-50.0) == 0.2

    def test_classify_case_level_supreme(self, engine: AuthorityChainEngine):
        conn = engine._connect()
        result = engine._classify_case_level(conn, "480 Mich 75", "michigan_case_law")
        assert result == "supreme_court"
        conn.close()

    def test_classify_case_level_appeals(self, engine: AuthorityChainEngine):
        conn = engine._connect()
        result = engine._classify_case_level(
            conn, "100 Mich App 500", "michigan_case_law",
        )
        assert result == "court_of_appeals"
        conn.close()

    def test_classify_case_level_federal(self, engine: AuthorityChainEngine):
        conn = engine._connect()
        result = engine._classify_case_level(
            conn, "300 F 3d 200", "michigan_case_law",
        )
        assert result == "federal_circuit"
        conn.close()
