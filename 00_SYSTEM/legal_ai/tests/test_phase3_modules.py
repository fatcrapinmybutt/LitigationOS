# -*- coding: utf-8 -*-
"""
Comprehensive tests for LitigationOS Phase 3 legal_ai modules:
  - completeness_scorer.py (CompletenessScorer)
  - chatgpt_parser.py      (ChatGPTParser)
  - deadline_integration.py (DeadlineSentinelIntegration)
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

# ── Path setup so imports resolve from the legal_ai package ──
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from completeness_scorer import (
    CompletenessReport,
    CompletenessScorer,
    DimensionScore,
    ScoringError,
)
from chatgpt_parser import (
    ChatGPTParser,
    ChatMessage,
    CodeBlock,
    LegalExtract,
    ParsedConversation,
)
from deadline_integration import (
    AlertThreshold,
    DeadlineAlert,
    DeadlineSentinelIntegration,
    DeadlineStatus,
)


# ═══════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════

def _well_formed_motion() -> str:
    """A realistic Michigan court motion with most elements present."""
    return """\
STATE OF MICHIGAN
IN THE 14TH CIRCUIT COURT FOR THE COUNTY OF MUSKEGON

ANDREW PIGORS,
    Petitioner,
                                    Case No. 2024-001507-DC
v.                                  Hon. Annette Smedley

EMILY WATSON,
    Respondent.
______________________________________________/

MOTION FOR RECONSIDERATION

I.  INTRODUCTION

    Petitioner Andrew Pigors, appearing pro se, respectfully moves this
    Honorable Court to reconsider its Order dated January 15, 2025 on the
    grounds set forth below.

II.  STATEMENT OF FACTS

    On January 10, 2025, Petitioner filed a Motion to Modify Parenting
    Time.  The Court entered an Order on January 15, 2025, denying said
    motion without hearing.  (See Exhibit A.)  Petitioner testified on
    the record at the October 3, 2024 hearing.  (Tr. at 45-47.)

III.  LEGAL STANDARD

    A motion for reconsideration is governed by MCR 2.119(F).  The movant
    must demonstrate a palpable error by which the court was misled.
    MCL 722.27(1)(c) governs modification of custody orders.  See also
    Vodvarka v Grasmeyer, 259 Mich App 499; 675 NW2d 847 (2003).
    The burden of proof rests on the moving party under 42 USC 1983.

IV.  ARGUMENT

    A.  Relief Requested

    Petitioner requests the Court vacate its January 15, 2025 Order.

    B.  Grounds

    The Court's Order failed to consider the child's best interests under
    MCL 722.23 and overlooked Exhibit B — the GAL report recommending
    expanded parenting time.

V.  CONCLUSION

    For the foregoing reasons, Petitioner respectfully requests this Court
    grant this Motion for Reconsideration.

Respectfully submitted,

Date: February 1, 2025

/s/ Andrew Pigors
Andrew Pigors, Pro Se Petitioner
1234 Main St, Muskegon, MI 49441
(231) 555-0199

CERTIFICATE OF SERVICE

    I hereby certify that on February 1, 2025, I served a copy of this
    Motion on Respondent by first-class mail at:

    Emily Watson
    5678 Oak Ave, Muskegon, MI 49442

Page 1 of 3
"""


def _build_deadline_db(db_path: str) -> None:
    """Create a litigation_deadlines table with varied test data."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE litigation_deadlines (
            deadline_id TEXT PRIMARY KEY,
            case_name TEXT,
            court TEXT,
            filing_type TEXT,
            due_date TEXT,
            days_remaining INTEGER,
            priority TEXT DEFAULT 'MEDIUM',
            status TEXT DEFAULT 'upcoming',
            basis TEXT,
            authority TEXT,
            notes TEXT
        )
    """)

    today = date.today()
    rows = [
        ("DL-001", "Pigors v Watson", "14th Circuit", "Motion",
         (today - timedelta(days=10)).isoformat(), -10, "CRITICAL", "upcoming",
         "MCR 2.119", "MCR 2.119(F)", "Overdue motion"),
        ("DL-002", "Pigors v Watson", "14th Circuit", "Response",
         (today + timedelta(days=1)).isoformat(), 1, "CRITICAL", "upcoming",
         "MCR 2.108", "MCR 2.108(A)", "Due tomorrow"),
        ("DL-003", "Pigors v Watson", "14th Circuit", "Brief",
         (today + timedelta(days=5)).isoformat(), 5, "HIGH", "upcoming",
         "MCR 7.212", "MCR 7.212(A)", "Within 7 days"),
        ("DL-004", "Pigors v Watson", "COA", "Application",
         (today + timedelta(days=12)).isoformat(), 12, "HIGH", "upcoming",
         "MCR 7.205", "MCR 7.205(A)", "Within 14 days"),
        ("DL-005", "Shady Oaks", "District", "Complaint",
         (today + timedelta(days=25)).isoformat(), 25, "MEDIUM", "upcoming",
         "MCR 2.110", "MCR 2.110", "Within 30 days"),
        ("DL-006", "Pigors v Watson", "14th Circuit", "Notice",
         (today + timedelta(days=60)).isoformat(), 60, "LOW", "upcoming",
         "MCR 2.107", "MCR 2.107", "Far out"),
        ("DL-007", "Old Case", "14th Circuit", "Proof",
         "2024-01-15", -200, "LOW", "filed",
         "", "", "Already filed"),
        ("DL-008", "Waived Case", "14th Circuit", "Motion",
         "2024-06-15", -100, "LOW", "waived",
         "", "", "Waived deadline"),
    ]
    conn.executemany(
        """INSERT INTO litigation_deadlines
           (deadline_id, case_name, court, filing_type, due_date,
            days_remaining, priority, status, basis, authority, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    conn.commit()
    conn.close()


def _make_chatgpt_export(tmp_path: Path, conversations: list) -> str:
    """Write a conversations.json file and return its path."""
    p = tmp_path / "conversations.json"
    p.write_text(json.dumps(conversations), encoding="utf-8")
    return str(p)


def _simple_conversation(cid: str = "conv-1", title: str = "Legal Q&A") -> dict:
    """A minimal ChatGPT export conversation dict with mapping format."""
    return {
        "id": cid,
        "title": title,
        "create_time": 1700000000.0,
        "mapping": {
            "node-root": {
                "id": "node-root",
                "parent": None,
                "message": None,
            },
            "node-user": {
                "id": "node-user",
                "parent": "node-root",
                "message": {
                    "id": "msg-user-1",
                    "author": {"role": "user"},
                    "content": {
                        "parts": [
                            "What is MCL 722.27 about? Also see MCR 2.119(F). "
                            "Refer to Vodvarka v Grasmeyer, 259 Mich App 499."
                        ]
                    },
                    "create_time": 1700000001.0,
                },
            },
            "node-assistant": {
                "id": "node-assistant",
                "parent": "node-user",
                "message": {
                    "id": "msg-asst-1",
                    "author": {"role": "assistant"},
                    "content": {
                        "parts": [
                            "MCL 722.27 governs modification of custody. "
                            "Under 42 USC 1983 you can bring federal claims. "
                            "```python\nprint('hello')\n```\n"
                            "Legal analysis: the standard of review is de novo."
                        ]
                    },
                    "create_time": 1700000010.0,
                },
            },
        },
    }


# ═══════════════════════════════════════════════════════════════════
#  CompletenessScorer Tests
# ═══════════════════════════════════════════════════════════════════


class TestCompletenessScorer:
    """Tests for completeness_scorer.CompletenessScorer."""

    def _scorer(self, tmp_path: Path) -> CompletenessScorer:
        """Return a scorer pointing at a non-existent DB (no DB checks)."""
        return CompletenessScorer(db_path=str(tmp_path / "nonexistent.db"))

    # ── Core scoring ──

    def test_score_well_formed_motion(self, tmp_path):
        scorer = self._scorer(tmp_path)
        report = scorer.score_filing(_well_formed_motion(), filing_type="motion")
        assert report.overall_score > 60
        assert report.grade in ("A", "B", "C")

    def test_score_empty_text_raises(self, tmp_path):
        scorer = self._scorer(tmp_path)
        with pytest.raises(ScoringError):
            scorer.score_filing("")

    def test_score_whitespace_only_raises(self, tmp_path):
        scorer = self._scorer(tmp_path)
        with pytest.raises(ScoringError):
            scorer.score_filing("   \n\t  ")

    def test_score_none_text_raises(self, tmp_path):
        scorer = self._scorer(tmp_path)
        with pytest.raises((ScoringError, TypeError, AttributeError)):
            scorer.score_filing(None)

    # ── Placeholder detection ──

    def test_score_placeholder_detection(self, tmp_path):
        scorer = self._scorer(tmp_path)
        text = _well_formed_motion().replace(
            "MCR 2.119(F)", "[CITATION_NEEDED] TODO FIXME [PLACEHOLDER]"
        )
        report = scorer.score_filing(text, filing_type="motion")
        # Placeholders should drag the score down
        placeholder_dim = [
            d for d in report.dimensions if "Placeholder" in d.dimension_name
        ]
        assert len(placeholder_dim) == 1
        assert placeholder_dim[0].score < 100.0

    def test_score_no_placeholders_full_score(self, tmp_path):
        scorer = self._scorer(tmp_path)
        # Use motion text without underscore separator (it triggers _{3,} pattern)
        clean_text = _well_formed_motion().replace("______________________________________________", "---")
        report = scorer.score_filing(clean_text, filing_type="motion")
        placeholder_dim = [
            d for d in report.dimensions if "Placeholder" in d.dimension_name
        ]
        assert placeholder_dim[0].score == 100.0

    # ── Citation detection ──

    def test_score_citation_detection(self, tmp_path):
        scorer = self._scorer(tmp_path)
        report = scorer.score_filing(_well_formed_motion(), filing_type="motion")
        citation_dim = [
            d for d in report.dimensions if "Citation" in d.dimension_name
        ]
        assert len(citation_dim) == 1
        assert citation_dim[0].score > 0

    def test_score_no_citations(self, tmp_path):
        scorer = self._scorer(tmp_path)
        text = "This is a motion with no legal references at all.\n" * 40
        report = scorer.score_filing(text, filing_type="motion")
        citation_dim = [
            d for d in report.dimensions if "Citation" in d.dimension_name
        ]
        assert citation_dim[0].score == 0.0

    # ── Signature detection ──

    def test_score_signature_detection(self, tmp_path):
        scorer = self._scorer(tmp_path)
        report = scorer.score_filing(_well_formed_motion(), filing_type="motion")
        sig_dim = [
            d for d in report.dimensions if "Signature" in d.dimension_name
        ]
        assert len(sig_dim) == 1
        assert sig_dim[0].score > 50

    def test_score_no_signature(self, tmp_path):
        scorer = self._scorer(tmp_path)
        text = "MOTION FOR SOMETHING\nArgument text.\n" * 20
        report = scorer.score_filing(text, filing_type="motion")
        sig_dim = [
            d for d in report.dimensions if "Signature" in d.dimension_name
        ]
        assert sig_dim[0].score < 50

    # ── Service detection ──

    def test_score_service_detection(self, tmp_path):
        scorer = self._scorer(tmp_path)
        report = scorer.score_filing(_well_formed_motion(), filing_type="motion")
        svc_dim = [
            d for d in report.dimensions if "Service" in d.dimension_name
        ]
        assert len(svc_dim) == 1
        assert svc_dim[0].score > 0

    def test_score_no_service(self, tmp_path):
        scorer = self._scorer(tmp_path)
        text = "MOTION\nArgument paragraph.\n" * 20
        report = scorer.score_filing(text, filing_type="motion")
        svc_dim = [
            d for d in report.dimensions if "Service" in d.dimension_name
        ]
        assert svc_dim[0].score == 0.0

    # ── Case number format ──

    def test_score_case_number_format(self, tmp_path):
        scorer = self._scorer(tmp_path)
        report = scorer.score_filing(_well_formed_motion(), filing_type="motion")
        scao_dim = [
            d for d in report.dimensions if "SCAO" in d.dimension_name
        ]
        assert len(scao_dim) == 1
        # Should find 2024-001507-DC
        has_case_number_issue = any(
            "case number" in i.lower() for i in scao_dim[0].issues
        )
        assert not has_case_number_issue

    def test_score_missing_case_number(self, tmp_path):
        scorer = self._scorer(tmp_path)
        text = "MOTION\n" + "argument " * 100
        report = scorer.score_filing(text, filing_type="motion")
        scao_dim = [
            d for d in report.dimensions if "SCAO" in d.dimension_name
        ]
        has_case_number_issue = any(
            "case number" in i.lower() for i in scao_dim[0].issues
        )
        assert has_case_number_issue

    # ── Batch scoring ──

    def test_score_batch(self, tmp_path):
        scorer = self._scorer(tmp_path)
        f1 = tmp_path / "motion1.txt"
        f2 = tmp_path / "motion2.txt"
        f1.write_text(_well_formed_motion(), encoding="utf-8")
        f2.write_text("Short filing.\n", encoding="utf-8")
        reports = scorer.score_batch([str(f1), str(f2)])
        assert len(reports) == 2
        assert reports[0].overall_score > reports[1].overall_score

    def test_score_batch_missing_file(self, tmp_path):
        scorer = self._scorer(tmp_path)
        reports = scorer.score_batch([str(tmp_path / "nonexistent.txt")])
        assert len(reports) == 1
        assert reports[0].overall_score == 0.0
        assert reports[0].grade == "F"

    # ── Dimension scores ──

    def test_dimension_scores_range(self, tmp_path):
        scorer = self._scorer(tmp_path)
        report = scorer.score_filing(_well_formed_motion(), filing_type="motion")
        assert len(report.dimensions) == 8
        for dim in report.dimensions:
            assert 0 <= dim.score <= 100
            assert dim.max_points > 0

    def test_weighted_score_property(self, tmp_path):
        dim = DimensionScore(
            dimension_name="Test", score=80.0, max_points=15.0
        )
        assert dim.weighted_score == pytest.approx(12.0, abs=0.01)

    # ── Grade assignment ──

    def test_grade_assignment_A(self, tmp_path):
        scorer = self._scorer(tmp_path)
        report = scorer.score_filing(_well_formed_motion(), filing_type="motion")
        # The well-formed motion should get at least a C
        assert report.grade in ("A", "B", "C")

    def test_grade_F_for_minimal_text(self, tmp_path):
        scorer = self._scorer(tmp_path)
        report = scorer.score_filing("Just some text.", filing_type="motion")
        assert report.grade in ("D", "F")

    # ── Filing readiness ──

    def test_filing_ready_flag_true(self, tmp_path):
        scorer = self._scorer(tmp_path)
        report = scorer.score_filing(_well_formed_motion(), filing_type="motion")
        if report.grade in ("A", "B", "C") and not report.critical_issues:
            assert report.filing_ready is True

    def test_filing_ready_flag_false_for_low_score(self, tmp_path):
        scorer = self._scorer(tmp_path)
        report = scorer.score_filing("nothing useful.", filing_type="motion")
        assert report.filing_ready is False

    # ── Serialisation ──

    def test_to_dict(self, tmp_path):
        scorer = self._scorer(tmp_path)
        report = scorer.score_filing(_well_formed_motion(), filing_type="motion")
        d = report.to_dict()
        assert "overall_score" in d
        assert "grade" in d
        assert "filing_ready" in d
        assert "dimensions" in d
        assert isinstance(d["dimensions"], list)
        assert "scored_at" in d

    def test_to_dict_dimensions_structure(self, tmp_path):
        scorer = self._scorer(tmp_path)
        report = scorer.score_filing(_well_formed_motion(), filing_type="motion")
        d = report.to_dict()
        for dim in d["dimensions"]:
            assert "name" in dim
            assert "score" in dim
            assert "weighted" in dim
            assert "issues" in dim

    # ── Stats ──

    def test_get_stats(self, tmp_path):
        scorer = self._scorer(tmp_path)
        scorer.score_filing(_well_formed_motion())
        stats = scorer.get_stats()
        assert stats["scores_computed"] >= 1
        assert "db_path" in stats
        assert "dimensions" in stats
        assert "weights" in stats

    # ── File scoring ──

    def test_score_file(self, tmp_path):
        scorer = self._scorer(tmp_path)
        f = tmp_path / "motion.txt"
        f.write_text(_well_formed_motion(), encoding="utf-8")
        report = scorer.score_file(str(f))
        assert report.filing_path != ""
        assert report.overall_score > 0

    def test_score_file_not_found(self, tmp_path):
        scorer = self._scorer(tmp_path)
        with pytest.raises(ScoringError):
            scorer.score_file(str(tmp_path / "nope.txt"))


# ═══════════════════════════════════════════════════════════════════
#  ChatGPTParser Tests
# ═══════════════════════════════════════════════════════════════════


class TestChatGPTParser:
    """Tests for chatgpt_parser.ChatGPTParser."""

    # ── Single conversation ──

    def test_parse_single_conversation(self):
        parser = ChatGPTParser()
        conv = parser.parse_single(_simple_conversation())
        assert isinstance(conv, ParsedConversation)
        assert conv.conversation_id == "conv-1"
        assert conv.title == "Legal Q&A"
        assert conv.message_count >= 2
        assert conv.word_count > 0

    def test_parse_single_empty_mapping(self):
        parser = ChatGPTParser()
        conv = parser.parse_single({"id": "empty", "title": "Empty", "mapping": {}})
        assert conv.message_count == 0

    def test_parse_single_flat_messages(self):
        parser = ChatGPTParser()
        raw = {
            "id": "flat-1",
            "title": "Flat",
            "messages": [
                {"role": "user", "content": "Hello world"},
                {"role": "assistant", "content": "Hi there MCL 722.27"},
            ],
        }
        conv = parser.parse_single(raw)
        assert conv.message_count == 2

    # ── Export parsing ──

    def test_parse_export_file(self, tmp_path):
        parser = ChatGPTParser()
        path = _make_chatgpt_export(tmp_path, [_simple_conversation()])
        results = parser.parse_export(path)
        assert len(results) == 1

    def test_parse_empty_export(self, tmp_path):
        parser = ChatGPTParser()
        path = _make_chatgpt_export(tmp_path, [])
        results = parser.parse_export(path)
        assert results == []

    def test_parse_malformed_json(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("{{{not valid json", encoding="utf-8")
        parser = ChatGPTParser()
        with pytest.raises((ValueError, json.JSONDecodeError)):
            parser.parse_export(str(f))

    def test_parse_missing_file(self):
        parser = ChatGPTParser()
        with pytest.raises(FileNotFoundError):
            parser.parse_export("/nonexistent/path.json")

    def test_parse_dict_wrapper(self, tmp_path):
        """Export wrapped as {"conversations": [...]}."""
        parser = ChatGPTParser()
        wrapped = {"conversations": [_simple_conversation()]}
        path = _make_chatgpt_export(tmp_path, wrapped)
        # parse_export reads the file and handles dict wrapper
        results = parser.parse_export(path)
        assert len(results) == 1

    # ── Legal content extraction ──

    def test_extract_legal_content_mcl(self):
        parser = ChatGPTParser()
        extracts = parser.extract_legal_content("See MCL 722.27 for details.")
        types = [e.extract_type for e in extracts]
        assert "statute" in types

    def test_extract_legal_content_mcr(self):
        parser = ChatGPTParser()
        extracts = parser.extract_legal_content("Under MCR 2.119(F) the movant must show error.")
        statutes = [e for e in extracts if e.extract_type == "statute"]
        assert len(statutes) >= 1

    def test_extract_federal_citations(self):
        parser = ChatGPTParser()
        extracts = parser.extract_legal_content(
            "Pursuant to 42 USC 1983, plaintiff alleges. Also 28 USC 1331."
        )
        statutes = [e for e in extracts if e.extract_type == "statute"]
        assert len(statutes) >= 1
        texts = [s.text for s in statutes]
        assert any("1983" in t for t in texts)

    def test_extract_case_ref(self):
        parser = ChatGPTParser()
        extracts = parser.extract_legal_content(
            "In Vodvarka v Grasmeyer, the court held that..."
        )
        case_refs = [e for e in extracts if e.extract_type == "case_ref"]
        assert len(case_refs) >= 1

    def test_extract_legal_content_empty(self):
        parser = ChatGPTParser()
        assert parser.extract_legal_content("") == []
        assert parser.extract_legal_content(None) == []

    # ── Code block extraction ──

    def test_extract_code_blocks(self):
        parser = ChatGPTParser()
        text = "Here:\n```python\nprint('hello')\n```\nEnd."
        blocks = parser.extract_code_blocks(text)
        assert len(blocks) == 1
        assert blocks[0].language == "python"
        assert "print" in blocks[0].code

    def test_extract_code_blocks_no_lang(self):
        parser = ChatGPTParser()
        text = "```\nsome code\n```"
        blocks = parser.extract_code_blocks(text)
        assert len(blocks) == 1
        assert blocks[0].language == "text"

    def test_extract_code_blocks_empty(self):
        parser = ChatGPTParser()
        assert parser.extract_code_blocks("") == []
        assert parser.extract_code_blocks(None) == []

    # ── Search ──

    def test_search_conversations(self):
        parser = ChatGPTParser()
        conv = parser.parse_single(_simple_conversation())
        results = parser.search_conversations([conv], "MCL")
        assert len(results) == 1

    def test_search_conversations_no_match(self):
        parser = ChatGPTParser()
        conv = parser.parse_single(_simple_conversation())
        results = parser.search_conversations([conv], "zzznonexistent999")
        assert len(results) == 0

    def test_search_empty_query_returns_all(self):
        parser = ChatGPTParser()
        conv = parser.parse_single(_simple_conversation())
        results = parser.search_conversations([conv], "")
        assert len(results) == 1

    # ── DB export ──

    def test_export_to_db(self, tmp_path):
        parser = ChatGPTParser()
        conv = parser.parse_single(_simple_conversation())
        db_path = str(tmp_path / "export.db")
        parser.export_to_db([conv], db_path)

        conn = sqlite3.connect(db_path)
        count = conn.execute(
            "SELECT COUNT(*) FROM chatgpt_conversations"
        ).fetchone()[0]
        conn.close()
        assert count == 1

    def test_export_to_db_empty_list(self, tmp_path):
        parser = ChatGPTParser()
        db_path = str(tmp_path / "empty_export.db")
        parser.export_to_db([], db_path)

        conn = sqlite3.connect(db_path)
        count = conn.execute(
            "SELECT COUNT(*) FROM chatgpt_conversations"
        ).fetchone()[0]
        conn.close()
        assert count == 0

    def test_export_to_db_legal_extracts(self, tmp_path):
        parser = ChatGPTParser()
        conv = parser.parse_single(_simple_conversation())
        db_path = str(tmp_path / "extracts.db")
        parser.export_to_db([conv], db_path)

        conn = sqlite3.connect(db_path)
        count = conn.execute(
            "SELECT COUNT(*) FROM chatgpt_legal_extracts"
        ).fetchone()[0]
        conn.close()
        assert count > 0

    # ── Dataclass tests ──

    def test_chatmessage_dataclass(self):
        msg = ChatMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.message_id  # auto-generated UUID

    def test_chatmessage_custom_id(self):
        msg = ChatMessage(role="assistant", content="Hi", message_id="custom-123")
        assert msg.message_id == "custom-123"

    def test_legal_extract_types(self):
        le = LegalExtract(extract_type="citation", text="259 Mich App 499", confidence=0.9)
        assert le.extract_type == "citation"
        assert le.confidence == 0.9

    def test_code_block_dataclass(self):
        cb = CodeBlock(language="sql", code="SELECT 1", context="example")
        assert cb.language == "sql"
        assert cb.code == "SELECT 1"

    def test_parsed_conversation_defaults(self):
        pc = ParsedConversation(conversation_id="test", title="T")
        assert pc.messages == []
        assert pc.code_blocks == []
        assert pc.legal_extracts == []
        assert pc.word_count == 0

    # ── Stats ──

    def test_stats(self):
        parser = ChatGPTParser()
        parser.parse_single(_simple_conversation())
        stats = parser.get_stats()
        assert "conversations_parsed" in stats
        assert stats["conversations_parsed"] >= 1
        assert "messages_extracted" in stats

    # ── Edge cases ──

    def test_unicode_handling(self):
        parser = ChatGPTParser()
        text = "\u00a71983 \u2014 The court\u2019s \u201cholding\u201d under MCL 722.27"
        extracts = parser.extract_legal_content(text)
        statutes = [e for e in extracts if e.extract_type == "statute"]
        assert len(statutes) >= 1

    def test_html_entities(self):
        parser = ChatGPTParser()
        text = "MCL 722.27 &amp; MCR 2.119 are relevant &mdash; see analysis."
        extracts = parser.extract_legal_content(text)
        statutes = [e for e in extracts if e.extract_type == "statute"]
        assert len(statutes) >= 1

    def test_null_content(self):
        parser = ChatGPTParser()
        raw = {
            "id": "null-content",
            "title": "Null",
            "messages": [
                {"role": "user", "content": None},
                {"role": "assistant"},
            ],
        }
        conv = parser.parse_single(raw)
        # Should not crash — messages with no content are skipped
        assert isinstance(conv, ParsedConversation)


# ═══════════════════════════════════════════════════════════════════
#  DeadlineSentinelIntegration Tests
# ═══════════════════════════════════════════════════════════════════


class TestDeadlineSentinelIntegration:
    """Tests for deadline_integration.DeadlineSentinelIntegration."""

    # ── Scan ──

    def test_scan_empty_db(self, tmp_path):
        db = str(tmp_path / "empty.db")
        # Create empty DB with just the alert tables (no deadlines)
        sqlite3.connect(db).close()
        sentinel = DeadlineSentinelIntegration(db_path=db)
        status = sentinel.scan()
        assert isinstance(status, DeadlineStatus)
        assert status.total_deadlines == 0

    def test_scan_with_deadlines(self, tmp_path):
        db = str(tmp_path / "dl.db")
        _build_deadline_db(db)
        sentinel = DeadlineSentinelIntegration(db_path=db)
        status = sentinel.scan()
        assert status.total_deadlines > 0

    # ── Urgency tiers ──

    def test_overdue_detection(self, tmp_path):
        db = str(tmp_path / "dl.db")
        _build_deadline_db(db)
        sentinel = DeadlineSentinelIntegration(db_path=db)
        status = sentinel.scan()
        assert status.overdue >= 1  # DL-001 is 10 days overdue

    def test_critical_threshold(self, tmp_path):
        db = str(tmp_path / "dl.db")
        _build_deadline_db(db)
        sentinel = DeadlineSentinelIntegration(db_path=db)
        status = sentinel.scan()
        assert status.critical_7d >= 1  # DL-002 (1 day), DL-003 (5 days)

    def test_high_threshold(self, tmp_path):
        db = str(tmp_path / "dl.db")
        _build_deadline_db(db)
        sentinel = DeadlineSentinelIntegration(db_path=db)
        status = sentinel.scan()
        assert status.high_14d >= 1  # DL-004 (12 days)

    def test_medium_threshold(self, tmp_path):
        db = str(tmp_path / "dl.db")
        _build_deadline_db(db)
        sentinel = DeadlineSentinelIntegration(db_path=db)
        status = sentinel.scan()
        assert status.medium_30d >= 1  # DL-005 (25 days)

    # ── Health score ──

    def test_health_score_perfect(self, tmp_path):
        db = str(tmp_path / "perfect.db")
        # DB with only far-future deadlines
        conn = sqlite3.connect(db)
        conn.execute("""
            CREATE TABLE litigation_deadlines (
                deadline_id TEXT PRIMARY KEY,
                case_name TEXT,
                court TEXT,
                filing_type TEXT,
                due_date TEXT,
                status TEXT DEFAULT 'upcoming',
                authority TEXT
            )
        """)
        future = (date.today() + timedelta(days=90)).isoformat()
        conn.execute(
            "INSERT INTO litigation_deadlines VALUES (?,?,?,?,?,?,?)",
            ("DL-X", "Case", "Court", "Motion", future, "upcoming", ""),
        )
        conn.commit()
        conn.close()

        sentinel = DeadlineSentinelIntegration(db_path=db)
        status = sentinel.scan()
        assert status.health_score == 100.0

    def test_health_score_degraded(self, tmp_path):
        db = str(tmp_path / "dl.db")
        _build_deadline_db(db)
        sentinel = DeadlineSentinelIntegration(db_path=db)
        status = sentinel.scan()
        # Overdue + critical items should reduce score below 100
        assert status.health_score < 100.0

    def test_health_score_empty_db(self, tmp_path):
        db = str(tmp_path / "empty2.db")
        sqlite3.connect(db).close()
        sentinel = DeadlineSentinelIntegration(db_path=db)
        status = sentinel.scan()
        assert status.health_score == 100.0

    # ── Dashboard ──

    def test_dashboard_text(self, tmp_path):
        db = str(tmp_path / "dl.db")
        _build_deadline_db(db)
        sentinel = DeadlineSentinelIntegration(db_path=db)
        text = sentinel.get_dashboard(format="text")
        assert "DEADLINE SENTINEL" in text.upper()
        assert "Health Score" in text

    def test_dashboard_json(self, tmp_path):
        db = str(tmp_path / "dl.db")
        _build_deadline_db(db)
        sentinel = DeadlineSentinelIntegration(db_path=db)
        raw = sentinel.get_dashboard(format="json")
        data = json.loads(raw)
        assert "total_deadlines" in data
        assert "health_score" in data

    def test_dashboard_html(self, tmp_path):
        db = str(tmp_path / "dl.db")
        _build_deadline_db(db)
        sentinel = DeadlineSentinelIntegration(db_path=db)
        html = sentinel.get_dashboard(format="html")
        assert "<html>" in html.lower()
        assert "Deadline Sentinel" in html

    # ── Overdue / upcoming ──

    def test_get_overdue(self, tmp_path):
        db = str(tmp_path / "dl.db")
        _build_deadline_db(db)
        sentinel = DeadlineSentinelIntegration(db_path=db)
        overdue = sentinel.get_overdue()
        assert isinstance(overdue, list)
        for a in overdue:
            assert a.alert_level == "OVERDUE"

    def test_get_upcoming(self, tmp_path):
        db = str(tmp_path / "dl.db")
        _build_deadline_db(db)
        sentinel = DeadlineSentinelIntegration(db_path=db)
        upcoming = sentinel.get_upcoming(days=30)
        assert isinstance(upcoming, list)
        for item in upcoming:
            assert item.get("days_remaining", 999) <= 30

    # ── Alert lifecycle ──

    def test_acknowledge_alert(self, tmp_path):
        db = str(tmp_path / "dl.db")
        _build_deadline_db(db)
        sentinel = DeadlineSentinelIntegration(db_path=db)
        status = sentinel.scan()
        if status.alerts:
            aid = status.alerts[0].alert_id
            result = sentinel.acknowledge_alert(aid)
            assert result is True
            # Verify in DB
            conn = sqlite3.connect(db)
            row = conn.execute(
                "SELECT acknowledged FROM deadline_alerts WHERE alert_id=?",
                (aid,),
            ).fetchone()
            conn.close()
            if row:
                assert row[0] == 1

    def test_acknowledge_nonexistent_alert(self, tmp_path):
        db = str(tmp_path / "dl.db")
        _build_deadline_db(db)
        sentinel = DeadlineSentinelIntegration(db_path=db)
        # Should succeed (SQL updates 0 rows but no error)
        result = sentinel.acknowledge_alert("nonexistent-alert-id")
        assert result is True

    # ── Alert history ──

    def test_alert_history(self, tmp_path):
        db = str(tmp_path / "dl.db")
        _build_deadline_db(db)
        sentinel = DeadlineSentinelIntegration(db_path=db)
        sentinel.scan()  # Populate alerts
        history = sentinel.get_alert_history(limit=50)
        assert isinstance(history, list)
        assert len(history) > 0

    def test_alert_dedup(self, tmp_path):
        db = str(tmp_path / "dl.db")
        _build_deadline_db(db)
        sentinel = DeadlineSentinelIntegration(db_path=db)
        sentinel.scan()
        sentinel.scan()  # Second scan — same alerts
        history = sentinel.get_alert_history(limit=100)
        ids = [h["alert_id"] for h in history]
        assert len(ids) == len(set(ids)), "Duplicate alerts found in history"

    # ── Stats ──

    def test_stats(self, tmp_path):
        db = str(tmp_path / "dl.db")
        _build_deadline_db(db)
        sentinel = DeadlineSentinelIntegration(db_path=db)
        sentinel.scan()
        stats = sentinel.get_stats()
        assert "scans_run" in stats
        assert stats["scans_run"] >= 1
        assert "thresholds" in stats
        assert "db_path" in stats

    # ── DeadlineStatus serialisation ──

    def test_deadline_status_to_dict(self, tmp_path):
        db = str(tmp_path / "dl.db")
        _build_deadline_db(db)
        sentinel = DeadlineSentinelIntegration(db_path=db)
        status = sentinel.scan()
        d = status.to_dict()
        assert "total_deadlines" in d
        assert "overdue" in d
        assert "health_score" in d
        assert "alert_count" in d
        assert "scan_time" in d
        assert isinstance(d["health_score"], float)

    def test_deadline_status_defaults(self):
        status = DeadlineStatus()
        assert status.total_deadlines == 0
        assert status.health_score == 100.0
        d = status.to_dict()
        assert d["alert_count"] == 0

    # ── DeadlineAlert serialisation ──

    def test_deadline_alert_to_dict(self):
        alert = DeadlineAlert(
            alert_id="test-123",
            deadline_id="DL-001",
            case_name="Test Case",
            filing_type="Motion",
            due_date="2025-03-01",
            days_remaining=5,
            alert_level="HIGH",
            alert_message="Due in 5 days",
        )
        d = alert.to_dict()
        assert d["alert_id"] == "test-123"
        assert d["days_remaining"] == 5

    # ── AlertThreshold ──

    def test_alert_threshold_matches(self):
        t = AlertThreshold(days=7, level="HIGH", label="7d", color="#FF0000")
        assert t.matches(5) is True
        assert t.matches(7) is True
        assert t.matches(8) is False

    def test_alert_threshold_overdue(self):
        t = AlertThreshold(days=0, level="OVERDUE", label="overdue")
        assert t.matches(-5) is True
        assert t.matches(0) is True
        assert t.matches(1) is False

    # ── Filed/waived skip ──

    def test_filed_and_waived_counted(self, tmp_path):
        db = str(tmp_path / "dl.db")
        _build_deadline_db(db)
        sentinel = DeadlineSentinelIntegration(db_path=db)
        status = sentinel.scan()
        assert status.filed >= 1   # DL-007 is filed
        assert status.waived >= 1  # DL-008 is waived
