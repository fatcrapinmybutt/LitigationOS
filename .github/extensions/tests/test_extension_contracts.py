"""Contract tests for MCP extension Python bridges.

Tests the PUBLIC contract of:
  - litigation-db/query_helper.py  (handle_query, handle_fts_search, handle_stats)
  - lexos/lexos_bridge.py          (fts_escape, get_db, search helpers, DB-only actions)

These are greybox tests: they verify inputs → outputs at the module boundary
without testing Ollama/LLM integration (which requires a running server).
"""
import sqlite3
import sys
import types
from pathlib import Path
from unittest.mock import patch

import pytest

# ── Bootstrap imports ─────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[3]  # LitigationOS root
DB_PATH = ROOT / "litigation_context.db"

# Import query_helper as module
QUERY_HELPER_DIR = ROOT / ".github" / "extensions" / "litigation-db"
sys.path.insert(0, str(QUERY_HELPER_DIR))
import query_helper  # noqa: E402

sys.path.pop(0)

# Import lexos_bridge as module
LEXOS_DIR = ROOT / ".github" / "extensions" / "lexos"
sys.path.insert(0, str(LEXOS_DIR))
import lexos_bridge  # noqa: E402

sys.path.pop(0)

# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def db():
    """Shared read-only connection for the test module."""
    if not DB_PATH.exists():
        pytest.skip("litigation_context.db not found")
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON")
    yield conn
    conn.close()


# ═══════════════════════════════════════════════════════════════════════════
# litigation-db / query_helper.py contracts
# ═══════════════════════════════════════════════════════════════════════════

class TestQueryHelperQuery:
    """handle_query: parameterized SQL execution."""

    def test_returns_columns_rows_count(self, db):
        req = {"sql": "SELECT 1 AS val, 'hello' AS msg", "params": []}
        result = query_helper.handle_query(db, req, max_rows=50)
        assert "columns" in result
        assert "rows" in result
        assert "count" in result
        assert result["count"] == 1
        assert result["rows"][0]["val"] == 1
        assert result["rows"][0]["msg"] == "hello"

    def test_respects_max_rows(self, db):
        req = {"sql": "SELECT id FROM evidence_quotes LIMIT 100", "params": []}
        result = query_helper.handle_query(db, req, max_rows=5)
        assert result["count"] == 5
        assert "truncated" in result  # more rows available

    def test_parameterized_query(self, db):
        req = {
            "sql": "SELECT COUNT(*) AS cnt FROM evidence_quotes WHERE lane = ?",
            "params": ["F7"],
        }
        result = query_helper.handle_query(db, req, max_rows=50)
        assert result["count"] == 1
        assert result["rows"][0]["cnt"] >= 0

    def test_empty_result(self, db):
        req = {
            "sql": "SELECT * FROM evidence_quotes WHERE id = ?",
            "params": [-999999],
        }
        result = query_helper.handle_query(db, req, max_rows=50)
        assert result["count"] == 0
        assert result["rows"] == []


class TestQueryHelperFTS:
    """handle_fts_search: FTS5 and LIKE-fallback search."""

    def test_fts_evidence_returns_results(self, db):
        req = {"table": "evidence_fts", "query": "custody"}
        result = query_helper.handle_fts_search(db, req, max_rows=10)
        assert "columns" in result
        assert "rows" in result
        assert result["count"] >= 1
        # FTS results include excerpt
        assert any("excerpt" in r for r in result["rows"])

    def test_fts_timeline_returns_results(self, db):
        req = {"table": "timeline_fts", "query": "custody"}
        result = query_helper.handle_fts_search(db, req, max_rows=10)
        assert result["count"] >= 1

    def test_like_fallback_police_reports(self, db):
        req = {"table": "police_reports", "query": "report"}
        result = query_helper.handle_fts_search(db, req, max_rows=10)
        assert "rows" in result
        # LIKE search may or may not find results, but should not error

    def test_disallowed_table_returns_error(self, db):
        req = {"table": "sqlite_master", "query": "anything"}
        result = query_helper.handle_fts_search(db, req, max_rows=10)
        assert "error" in result
        assert "allowlist" in result["error"].lower()

    def test_empty_like_query(self, db):
        req = {"table": "police_reports", "query": "x"}  # single char, < 2
        result = query_helper.handle_fts_search(db, req, max_rows=10)
        assert result["count"] == 0


class TestQueryHelperStats:
    """handle_stats: table row counts."""

    def test_returns_stats_dict(self, db):
        result = query_helper.handle_stats(db)
        assert "stats" in result
        stats = result["stats"]
        assert isinstance(stats, dict)

    def test_evidence_quotes_count(self, db):
        result = query_helper.handle_stats(db)
        eq_count = result["stats"].get("evidence_quotes", 0)
        assert eq_count > 50000  # we know there are 92K+

    def test_all_stats_tables_present(self, db):
        result = query_helper.handle_stats(db)
        for tbl in query_helper.STATS_TABLES:
            assert tbl in result["stats"], f"Missing stats for {tbl}"


class TestQueryHelperConstants:
    """Verify allowlist and configuration constants."""

    def test_allowed_fts_tables(self):
        assert "evidence_fts" in query_helper.ALLOWED_FTS
        assert "timeline_fts" in query_helper.ALLOWED_FTS

    def test_allowed_like_tables(self):
        assert "police_reports" in query_helper.ALLOWED_LIKE
        assert "michigan_rules_extracted" in query_helper.ALLOWED_LIKE

    def test_stats_includes_key_tables(self):
        key_tables = ["evidence_quotes", "timeline_events", "impeachment_matrix"]
        for t in key_tables:
            assert t in query_helper.STATS_TABLES


# ═══════════════════════════════════════════════════════════════════════════
# lexos / lexos_bridge.py contracts
# ═══════════════════════════════════════════════════════════════════════════

class TestFtsEscape:
    """fts_escape: FTS5 query sanitization."""

    def test_strips_parentheses(self):
        result = lexos_bridge.fts_escape("MCL 722.23(j)")
        assert "(" not in result
        assert ")" not in result

    def test_strips_periods(self):
        result = lexos_bridge.fts_escape("MCR 2.003")
        assert "." not in result

    def test_empty_returns_empty_quotes(self):
        assert lexos_bridge.fts_escape("") == '""'
        assert lexos_bridge.fts_escape(None) == '""'

    def test_preserves_alphanumeric(self):
        result = lexos_bridge.fts_escape("custody alienation")
        assert "custody" in result
        assert "alienation" in result

    def test_quotes_each_word(self):
        result = lexos_bridge.fts_escape("custody")
        assert result == '"custody"'

    def test_limits_token_count(self):
        long_query = " ".join(f"word{i}" for i in range(20))
        result = lexos_bridge.fts_escape(long_query)
        # Max 12 tokens
        assert result.count('"') <= 24  # 12 words * 2 quotes each


class TestLexosConstants:
    """Verify lexos_bridge configuration constants."""

    def test_all_actions_list(self):
        assert len(lexos_bridge.ALL_ACTIONS) == 15
        assert "analyze" in lexos_bridge.ALL_ACTIONS
        assert "readiness" in lexos_bridge.ALL_ACTIONS
        assert "status" in lexos_bridge.ALL_ACTIONS

    def test_system_prompt_mentions_pigors(self):
        assert "Pigors" in lexos_bridge.SYSTEM_PROMPT

    def test_model_name_set(self):
        assert lexos_bridge.MODEL_NAME  # non-empty


class TestLexosHelpers:
    """safe_rows and safe_int utility contracts."""

    def test_safe_rows_empty(self):
        assert lexos_bridge.safe_rows([]) == []
        assert lexos_bridge.safe_rows(None) == []

    def test_safe_int_none(self):
        assert lexos_bridge.safe_int(None) == 0
        assert lexos_bridge.safe_int(None, 42) == 42

    def test_safe_int_string(self):
        assert lexos_bridge.safe_int("bad") == 0

    def test_safe_int_valid(self):
        assert lexos_bridge.safe_int("123") == 123
        assert lexos_bridge.safe_int(456) == 456


class TestLexosGetDb:
    """get_db: connection factory with PRAGMAs."""

    def test_returns_connection(self):
        conn = lexos_bridge.get_db()
        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_row_factory_set(self):
        conn = lexos_bridge.get_db()
        assert conn.row_factory == sqlite3.Row
        conn.close()

    def test_cache_size_set(self):
        conn = lexos_bridge.get_db()
        val = conn.execute("PRAGMA cache_size").fetchone()[0]
        assert val == -32000
        conn.close()


class TestLexosSearchEvidence:
    """search_evidence: FTS5 search with LIKE fallback."""

    def test_returns_list(self):
        conn = lexos_bridge.get_db()
        try:
            results = lexos_bridge.search_evidence(conn, "custody", limit=5)
            assert isinstance(results, list)
            if results:
                assert "quote_text" in results[0] or "id" in results[0]
        finally:
            conn.close()

    def test_lane_filter(self):
        conn = lexos_bridge.get_db()
        try:
            results = lexos_bridge.search_evidence(
                conn, "custody", limit=5, lane="F7"
            )
            assert isinstance(results, list)
        finally:
            conn.close()

    def test_empty_query(self):
        conn = lexos_bridge.get_db()
        try:
            results = lexos_bridge.search_evidence(conn, "", limit=5)
            assert isinstance(results, list)
        finally:
            conn.close()
